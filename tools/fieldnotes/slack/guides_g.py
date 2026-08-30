#!/usr/bin/env python3
"""/slack/ field notes, batch G — the writing.

Four notes that all point at a channel and none of which is about the same
thing going wrong. One is about the *form* of the reference: a name in a slot
that wants an ID, which works on the send path and fails on the read path. One
is about a target that resolves perfectly and is frozen, where the repair is a
different channel rather than a different string. One is about a target the
token is not permitted to know exists, where the honest finding is which
question is still open rather than an answer. And one is about time: a name
that was right for two years, and the day it either stops resolving or, far
worse, starts resolving somewhere else.

Read-only throughout. Web API methods that read, GET requests only: nothing
here posts, joins, invites, archives or renames. Every script reports what it
found and prints the repair for a human to run.
"""

CITE_CONV_LIST = ("conversations.list method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.list")
CITE_CONV_INFO = ("conversations.info method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.info")
CITE_CONV_HISTORY = ("conversations.history method reference — Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_POSTMESSAGE = ("chat.postMessage method reference — Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_CONV_API = ("Using the Conversations API — Slack Docs",
                 "https://docs.slack.dev/apis/web-api/using-the-conversations-api")
CITE_WEBHOOKS = ("Sending messages using incoming webhooks — Slack Docs",
                 "https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks")
CITE_SCOPES = ("Permission scopes — Slack Docs",
               "https://docs.slack.dev/reference/scopes/")
CITE_AUTH_TEST = ("auth.test method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_PAGINATION = ("Pagination in the Web API — Slack Docs",
                   "https://docs.slack.dev/apis/web-api/pagination")

GUIDES = [

{
"slug": "channel-name-instead-of-id",
"title": "channel_not_found: a channel name where an ID belongs",
"description": "chat.postMessage accepts #alerts and conversations.history refuses it. Check the form of every configured channel reference before either one runs.",
"h1": "channel_not_found: a channel name where an ID belongs",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack channel_not_found", "slack channel name vs id",
             "slack conversations.info channel_not_found", "slack channel id lookup",
             "slack chat.postMessage channel name"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "<code>{\"ok\": false, \"error\": \"channel_not_found\"}</code> for a channel that is open on the other monitor. The name in the config is spelled right, the bot is in the room, the token is fine. And the daily digest that posts to that same string has been working for a year. The difference is not the channel. It is which method you handed the string to.",
"short_answer": """<p>Slack's canonical channel identifier is the <code>C</code>-prefixed ID. <code>chat.postMessage</code> kept legacy name resolution, so <code>#alerts</code> works there; <code>conversations.info</code>, <code>conversations.history</code>, <code>conversations.members</code> and the <code>files.*</code> family never accepted a name and answer <code>channel_not_found</code>. One string, two behaviours, and no error message anywhere that mentions the word "name".</p>
<p>So the check is a grammar check, and it needs no network: does every configured channel value match <code>^[CG][A-Z0-9]{7,}$</code>? The script below classifies each reference by shape &mdash; ID, <code>#name</code>, bare name, a <code>U</code> user ID somebody pasted, a permalink &mdash; then prints which method families accept that shape and which refuse it. Only then does it paginate <code>conversations.list</code> once to hand you the ID to paste in.</p>""",
"problem": """<p>There is deliberately <strong>no</strong> name-to-ID lookup method in the Web API. That single fact explains why this bug is thirteen years old and still arriving. A developer who wants to send to <code>#alerts</code> reaches for the obvious thing, discovers that <code>chat.postMessage</code> accepts it, and reasonably concludes that names are how you address a channel. Everything built on that assumption works until the first read call.</p>
<p>Then the failure is split by code path rather than by configuration. The alert sender works. The thread-reply feature, which has to call <code>conversations.replies</code> first, does not. The file upload, which finishes with <code>files.completeUploadExternal</code>, does not. Three features share one config value and only one of them is broken, which is exactly the shape that sends people looking at the broken feature's code instead of at the string all three of them read.</p>
<p>The neighbouring mistakes are the same mistake wearing a different hat. A <code>U</code>-prefixed user ID in the channel slot does not error at all on <code>chat.postMessage</code> &mdash; Slack opens a DM and delivers the message to one person, which is a far worse outcome than a failure. A permalink pasted out of the browser carries the real ID inside it and matches nothing as a whole string. And on Enterprise Grid a name handed to an org-wide token comes back <code>team_not_found</code>, because the same name can exist in several workspaces and Slack will not guess.</p>""",
"why": """<p><strong>IDs are stable, names are not.</strong> A channel ID is assigned once and never changes, survives renames, and survives a conversion from public to private. A name is a display label that any member with permission can change, and that is released for reuse when they do. Configuration that stores the label is storing the one field that is designed to move.</p>
<p><strong>The tolerance is legacy, not policy.</strong> <code>chat.postMessage</code> resolves names because it predates the <code>conversations.*</code> family and Slack did not break it. Nothing in the documentation promises it will keep doing so, and no new method has been given the behaviour. Building on it means building on the one exception.</p>
<p><strong>The grammar is checkable offline.</strong> Channel IDs match <code>^[CG][A-Z0-9]{7,}$</code>, DMs start <code>D</code>, users start <code>U</code> or <code>W</code>. A regular expression over your configuration finds every one of these before a request is sent, which means the check belongs in the startup assertion rather than in the incident.</p>
<p><strong>Resolving per message is its own bug.</strong> The tempting fix &mdash; keep names in config, look them up when sending &mdash; means paginating <code>conversations.list</code> on every send. That is a Tier 2 method over a workspace with thousands of channels, so the fix trades <code>channel_not_found</code> for <code>ratelimited</code>. Resolve once at startup, cache the ID, and treat the name as a comment.</p>
<p><strong>A user ID in the channel slot succeeds.</strong> That is the case worth the extra branch in the classifier. There is no error to grep for, no failed run, no alert: the message is delivered, to one person, in a DM, and the channel it was meant for stays silent.</p>""",
"steps": [
 {"h": "Collect every place a channel is named",
  "body": """<p>Environment variables, YAML, Terraform, database rows, the hardcoded string in the one script nobody owns. The script takes a JSON object mapping a config key to its value, because the finding has to be reported against the key a human can go and edit, not against an anonymous string.</p>"""},
 {"h": "Classify by shape before you classify by result",
  "body": """<p><code>reference_form</code> is pure and answers offline. An ID passes. A <code>#name</code> or a bare name is the headline case. A <code>D</code> is a DM conversation, a <code>U</code> or <code>W</code> is a person, and a permalink is an ID wrapped in a URL that no method will unwrap for you.</p>"""},
 {"h": "Print which methods accept that shape",
  "body": """<p>This is the step that ends the argument about whether the value is wrong, because the same value is genuinely right for one method and wrong for another. Showing <code>chat.postMessage: accepts</code> beside <code>conversations.history: refuses</code> explains the intermittent failure in one line.</p>"""},
 {"h": "Resolve the names once, with one paginated sweep",
  "body": """<p><code>conversations.list</code> with <code>exclude_archived=false</code>, following <code>next_cursor</code> to the end. Include archived channels deliberately: a name that resolves only to an archived channel is a different finding from a name that resolves to nothing, and hiding the archive turns the first into the second.</p>"""},
 {"h": "Refuse to guess when two channels share a name",
  "body": """<p>Names are unique among live channels, but an archived channel releases its name for reuse, so a sweep that includes archives can return two rows for one string. Report both and let a human choose. A script that silently picks the live one is a script that quietly rewrites where your alerts go.</p>"""},
 {"h": "Paste the IDs and keep the name as a comment",
  "body": """<p>The script prints a ready config line: the ID as the value, the old name after a <code>#</code> so the file still reads like something a person wrote. Add a startup assertion on the ID grammar, and the next person who types a name gets a boot failure instead of a mystery.</p>"""},
],
"verify": """<p>Re-run over the edited configuration. Every reference should classify as an ID and no lookup should be needed at all, which is visible in the run taking no network calls.</p>
<pre><code class="language-bash">python3 slack_channel_reference_form.py --config channels.json
# canonical      ALERTS_CHANNEL   C01ABCDE9  accepted by every method family
# canonical      DIGEST_CHANNEL   C02XYZ123  accepted by every method family
# 2 reference(s) checked, 0 that are not channel IDs</code></pre>""",
"code_intro": "Two of the three functions never touch the network. <code>reference_form</code> names the shape of a configured string, <code>path_outcomes</code> turns that shape into the per-method truth table that explains why one feature works and another does not, and <code>resolve_name</code> matches a name against the workspace inventory without picking a winner when there are two. The only I/O is one paginated <code>conversations.list</code>, and it runs only if something needs resolving.",
"py_file": "slack_channel_reference_form.py",
"py": '''"""Check that every Slack channel reference in your configuration is an ID.

Read only, and mostly offline: the shape of a reference settles most of the
finding before a request is sent. One paginated conversations.list resolves the
names that are left. Nothing is written; the replacement config line is printed
for you to paste.
"""
import argparse
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_channel_reference_form")

API = "https://slack.com/api/"

ID_RE = re.compile(r"^[CG][A-Z0-9]{7,}$")
DM_RE = re.compile(r"^D[A-Z0-9]{7,}$")
USER_RE = re.compile(r"^[UW][A-Z0-9]{7,}$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
LINK_RE = re.compile(r"/archives/([CGD][A-Z0-9]{7,})")

# chat.postMessage kept legacy name resolution from before the conversations.*
# family existed. Nothing else did. That split is the whole reason this survives
# code review: the send path works and the read path does not.
TOLERANT = ("chat.postMessage",)
STRICT = ("conversations.info", "conversations.history", "conversations.members",
          "files.completeUploadExternal")
FAMILIES = TOLERANT + STRICT

NEEDS_LOOKUP = ("hash-name", "bare-name")


def reference_form(value):
    """Name the shape of one configured channel reference. Pure, so it is offline.

    Returns (form, detail). Order matters: a permalink contains a valid ID and
    would otherwise fall through to the malformed bucket, and a bare name is only
    a name once every ID pattern has been ruled out.
    """
    text = ("" if value is None else str(value)).strip()
    if not text:
        return ("empty", "no value at all. Something upstream resolved to an empty "
                         "string and the call will fail on every method.")

    link = LINK_RE.search(text)
    if link and not ID_RE.match(text):
        return ("permalink",
                "a channel permalink. The ID is inside it (%s) but no method will "
                "unwrap a URL for you." % link.group(1))
    if ID_RE.match(text):
        return ("channel-id", "a channel ID, which is what every method wants")
    if DM_RE.match(text):
        return ("dm-id",
                "a DM conversation ID. Every method accepts it and none of them "
                "will tell you it reaches one person rather than a channel.")
    if USER_RE.match(text):
        return ("user-id",
                "a user ID in the channel slot. chat.postMessage opens a DM and "
                "delivers to that person, so there is no error to find.")
    if text.startswith("#"):
        body = text[1:]
        if NAME_RE.match(body):
            return ("hash-name",
                    "a channel name with the display hash. The hash is UI syntax; "
                    "no method has ever treated it as part of an identifier.")
        return ("malformed", "starts with # but the rest is not a legal channel name")
    if NAME_RE.match(text):
        return ("bare-name",
                "a channel name. Names are display labels: mutable, reusable, and "
                "accepted by exactly one method family.")
    return ("malformed",
            "not an ID, not a legal channel name, and not a permalink. Whatever "
            "built this string built it wrong.")


def path_outcomes(form):
    """Turn a reference shape into the per-method truth table. Pure.

    Returns (verdict, rows) with rows as [(method, outcome), ...]. The verdict is
    the half worth reading: `split-brain` means this exact string is correct for
    one method family and wrong for another, which is why the failure looks
    intermittent rather than configured.
    """
    if form == "channel-id":
        return ("canonical", [(m, "accepts") for m in FAMILIES])
    if form in NEEDS_LOOKUP:
        return ("split-brain",
                [(m, "accepts") for m in TOLERANT] + [(m, "refuses") for m in STRICT])
    if form == "user-id":
        return ("wrong-entity",
                [(m, "delivers elsewhere") for m in TOLERANT]
                + [(m, "refuses") for m in STRICT])
    if form == "dm-id":
        return ("not-a-channel", [(m, "accepts") for m in FAMILIES])
    if form == "permalink":
        return ("recoverable", [(m, "refuses") for m in FAMILIES])
    return ("unusable", [(m, "refuses") for m in FAMILIES])


def resolve_name(value, channels):
    """Match a configured name against the workspace inventory. Pure.

    Names are unique among live channels, but archiving releases a name for
    reuse, so a sweep that includes archives can return two rows for one string.
    Returns (state, channel, detail) and never picks a winner when the answer is
    genuinely two channels.
    """
    wanted = str(value).lstrip("#").strip().lower()
    hits = [c for c in channels if str(c.get("name") or "").lower() == wanted]
    live = [c for c in hits if not c.get("is_archived")]

    if not hits:
        return ("unresolved", None,
                "no channel in the workspace carries this name. It was renamed, "
                "deleted, or belongs to a workspace this token cannot see.")
    if not live:
        return ("archived-only", hits[0],
                "the only match is archived (%s). The ID resolves and the channel "
                "accepts nothing." % hits[0].get("id"))
    if len(live) > 1:
        return ("ambiguous", None,
                "%d live channels answer to this name, which happens across an "
                "Enterprise Grid org. A name cannot address one of them."
                % len(live))
    if len(hits) > 1:
        return ("resolved-with-archived-twin", live[0],
                "resolves to %s, and an archived channel holds the same name. The "
                "name is already contested." % live[0].get("id"))
    return ("resolved", live[0], "resolves to %s" % live[0].get("id"))


def config_line(key, channel, original):
    """The replacement line, with the old name kept as a comment. Pure."""
    return "%s=%s  # was %s, now #%s" % (key, channel.get("id"), original,
                                         channel.get("name"))


def list_channels(session):
    """Every channel the token can enumerate, archives included. GET only."""
    out, cursor = [], ""
    while True:
        params = {"types": "public_channel,private_channel",
                  "exclude_archived": "false", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.list", params=params, timeout=30).json()
        if body.get("ok") is not True:
            raise SystemExit("conversations.list answered 200 with ok: false, "
                             "error=%s" % body.get("error"))
        out.extend(body.get("channels") or [])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True,
                    help="JSON object mapping a config key to its channel reference")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    args = ap.parse_args()

    entries = json.loads(open(args.config, encoding="utf-8").read())
    forms = {k: reference_form(v) for k, v in entries.items()}

    channels = []
    if any(f[0] in NEEDS_LOOKUP for f in forms.values()):
        token = os.environ.get(args.token_env)
        if not token:
            log.error("set %s (channels:read and groups:read are enough)", args.token_env)
            return 2
        s = requests.Session()
        s.headers.update({"Authorization": "Bearer " + token})
        channels = list_channels(s)
        log.info("inventory: %d channel(s) the token can enumerate", len(channels))

    bad = 0
    for key in sorted(entries):
        value = entries[key]
        form, detail = forms[key]
        verdict, rows = path_outcomes(form)
        if verdict == "canonical":
            log.info("%-14s %-16s %-12s accepted by every method family",
                     verdict, key, value)
            continue

        bad += 1
        log.warning("%-14s %-16s %-12s %s", verdict, key, value, detail)
        for method, outcome in rows:
            if outcome != "accepts":
                log.warning("  %-30s %s", method, outcome)

        if form == "permalink":
            log.warning("  repair: %s=%s", key, LINK_RE.search(str(value)).group(1))
            continue
        if form not in NEEDS_LOOKUP:
            log.warning("  repair: put a channel ID in %s; copy it from the channel "
                        "details panel in Slack", key)
            continue

        state, channel, why = resolve_name(value, channels)
        log.warning("  lookup: %s -- %s", state, why)
        if channel is not None and state != "archived-only":
            log.warning("  repair: %s", config_line(key, channel, value))
        elif state == "archived-only":
            log.warning("  repair: this name only exists on an archived channel; "
                        "point %s at a live one", key)
        else:
            log.warning("  repair: find the channel in Slack, copy its ID from the "
                        "details panel, and store that in %s", key)

    log.info("%d reference(s) checked, %d that are not channel IDs", len(entries), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-channel-reference-form.mjs",
"js": '''/**
 * Check that every Slack channel reference in your configuration is an ID.
 *
 * Read only, and mostly offline: the shape of a reference settles most of the
 * finding before a request is sent. One paginated conversations.list resolves
 * the names that are left. Nothing is written; the replacement config line is
 * printed for you to paste.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

const ID_RE = /^[CG][A-Z0-9]{7,}$/;
const DM_RE = /^D[A-Z0-9]{7,}$/;
const USER_RE = /^[UW][A-Z0-9]{7,}$/;
const NAME_RE = /^[a-z0-9][a-z0-9._-]{0,79}$/;
const LINK_RE = /\\/archives\\/([CGD][A-Z0-9]{7,})/;

// chat.postMessage kept legacy name resolution from before the conversations.*
// family existed. Nothing else did. That split is the whole reason this survives
// code review: the send path works and the read path does not.
const TOLERANT = ['chat.postMessage'];
const STRICT = ['conversations.info', 'conversations.history',
  'conversations.members', 'files.completeUploadExternal'];
const FAMILIES = [...TOLERANT, ...STRICT];

const NEEDS_LOOKUP = new Set(['hash-name', 'bare-name']);

/**
 * Name the shape of one configured channel reference. Pure, so it is offline.
 * Order matters: a permalink contains a valid ID and would otherwise fall through
 * to the malformed bucket.
 */
export function referenceForm(value) {
  const text = (value === null || value === undefined ? '' : String(value)).trim();
  if (!text) {
    return ['empty', 'no value at all. Something upstream resolved to an empty ' +
      'string and the call will fail on every method.'];
  }

  const link = LINK_RE.exec(text);
  if (link && !ID_RE.test(text)) {
    return ['permalink',
      `a channel permalink. The ID is inside it (${link[1]}) but no method will ` +
      'unwrap a URL for you.'];
  }
  if (ID_RE.test(text)) return ['channel-id', 'a channel ID, which is what every method wants'];
  if (DM_RE.test(text)) {
    return ['dm-id',
      'a DM conversation ID. Every method accepts it and none of them will tell ' +
      'you it reaches one person rather than a channel.'];
  }
  if (USER_RE.test(text)) {
    return ['user-id',
      'a user ID in the channel slot. chat.postMessage opens a DM and delivers to ' +
      'that person, so there is no error to find.'];
  }
  if (text.startsWith('#')) {
    const body = text.slice(1);
    if (NAME_RE.test(body)) {
      return ['hash-name',
        'a channel name with the display hash. The hash is UI syntax; no method ' +
        'has ever treated it as part of an identifier.'];
    }
    return ['malformed', 'starts with # but the rest is not a legal channel name'];
  }
  if (NAME_RE.test(text)) {
    return ['bare-name',
      'a channel name. Names are display labels: mutable, reusable, and accepted ' +
      'by exactly one method family.'];
  }
  return ['malformed',
    'not an ID, not a legal channel name, and not a permalink. Whatever built ' +
    'this string built it wrong.'];
}

/**
 * Turn a reference shape into the per-method truth table. Pure.
 * `split-brain` means this exact string is correct for one method family and
 * wrong for another, which is why the failure looks intermittent.
 */
export function pathOutcomes(form) {
  if (form === 'channel-id') return ['canonical', FAMILIES.map((m) => [m, 'accepts'])];
  if (NEEDS_LOOKUP.has(form)) {
    return ['split-brain', [
      ...TOLERANT.map((m) => [m, 'accepts']),
      ...STRICT.map((m) => [m, 'refuses']),
    ]];
  }
  if (form === 'user-id') {
    return ['wrong-entity', [
      ...TOLERANT.map((m) => [m, 'delivers elsewhere']),
      ...STRICT.map((m) => [m, 'refuses']),
    ]];
  }
  if (form === 'dm-id') return ['not-a-channel', FAMILIES.map((m) => [m, 'accepts'])];
  if (form === 'permalink') return ['recoverable', FAMILIES.map((m) => [m, 'refuses'])];
  return ['unusable', FAMILIES.map((m) => [m, 'refuses'])];
}

/**
 * Match a configured name against the workspace inventory. Pure.
 * Never picks a winner when the answer is genuinely two channels.
 */
export function resolveName(value, channels) {
  const wanted = String(value).replace(/^#+/, '').trim().toLowerCase();
  const hits = channels.filter((c) => String(c.name ?? '').toLowerCase() === wanted);
  const live = hits.filter((c) => !c.is_archived);

  if (hits.length === 0) {
    return ['unresolved', null,
      'no channel in the workspace carries this name. It was renamed, deleted, or ' +
      'belongs to a workspace this token cannot see.'];
  }
  if (live.length === 0) {
    return ['archived-only', hits[0],
      `the only match is archived (${hits[0].id}). The ID resolves and the channel ` +
      'accepts nothing.'];
  }
  if (live.length > 1) {
    return ['ambiguous', null,
      `${live.length} live channels answer to this name, which happens across an ` +
      'Enterprise Grid org. A name cannot address one of them.'];
  }
  if (hits.length > 1) {
    return ['resolved-with-archived-twin', live[0],
      `resolves to ${live[0].id}, and an archived channel holds the same name. The ` +
      'name is already contested.'];
  }
  return ['resolved', live[0], `resolves to ${live[0].id}`];
}

/** The replacement line, with the old name kept as a comment. Pure. */
export function configLine(key, channel, original) {
  return `${key}=${channel.id}  # was ${original}, now #${channel.name}`;
}

async function listChannels(token) {
  const out = [];
  let cursor = '';
  for (;;) {
    const params = new URLSearchParams({
      types: 'public_channel,private_channel',
      exclude_archived: 'false',
      limit: '1000',
    });
    if (cursor) params.set('cursor', cursor);
    const res = await fetch(`${API}conversations.list?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = await res.json();
    if (body.ok !== true) {
      throw new Error(`conversations.list answered 200 with ok: false, error=${body.error}`);
    }
    out.push(...(body.channels ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) return out;
  }
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const configPath = arg(args, '--config');
  if (!configPath) {
    console.error('usage: --config channels.json [--token-env SLACK_BOT_TOKEN]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const entries = JSON.parse(await readFile(configPath, 'utf8'));
  const forms = new Map(Object.entries(entries).map(([k, v]) => [k, referenceForm(v)]));

  let channels = [];
  if ([...forms.values()].some(([f]) => NEEDS_LOOKUP.has(f))) {
    const token = process.env[tokenEnv];
    if (!token) {
      console.error(`set ${tokenEnv} (channels:read and groups:read are enough)`);
      process.exitCode = 2;
      return;
    }
    channels = await listChannels(token);
    console.log(`inventory: ${channels.length} channel(s) the token can enumerate`);
  }

  let bad = 0;
  for (const key of Object.keys(entries).sort()) {
    const value = entries[key];
    const [form, detail] = forms.get(key);
    const [verdict, rows] = pathOutcomes(form);
    if (verdict === 'canonical') {
      console.log(`${verdict.padEnd(14)} ${key.padEnd(16)} ${String(value).padEnd(12)} ` +
                  'accepted by every method family');
      continue;
    }

    bad += 1;
    console.warn(`${verdict.padEnd(14)} ${key.padEnd(16)} ${String(value).padEnd(12)} ${detail}`);
    for (const [method, outcome] of rows) {
      if (outcome !== 'accepts') console.warn(`  ${method.padEnd(30)} ${outcome}`);
    }

    if (form === 'permalink') {
      console.warn(`  repair: ${key}=${LINK_RE.exec(String(value))[1]}`);
      continue;
    }
    if (!NEEDS_LOOKUP.has(form)) {
      console.warn(`  repair: put a channel ID in ${key}; copy it from the channel ` +
                   'details panel in Slack');
      continue;
    }

    const [state, channel, why] = resolveName(value, channels);
    console.warn(`  lookup: ${state} -- ${why}`);
    if (channel !== null && state !== 'archived-only') {
      console.warn(`  repair: ${configLine(key, channel, value)}`);
    } else if (state === 'archived-only') {
      console.warn('  repair: this name only exists on an archived channel; point ' +
                   `${key} at a live one`);
    } else {
      console.warn('  repair: find the channel in Slack, copy its ID from the details ' +
                   `panel, and store that in ${key}`);
    }
  }

  console.log(`${Object.keys(entries).length} reference(s) checked, ${bad} that are ` +
              'not channel IDs');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing config.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case worth pinning hardest is the user ID, because it is the only shape here that produces no error anywhere: <code>chat.postMessage</code> takes a <code>U</code> value and delivers a DM. The tests assert that it classifies as <code>wrong-entity</code> rather than joining the names in the split-brain bucket, and that a name matching both a live and an archived channel is reported as contested instead of quietly resolved.",
"test_py_file": "test_slack_channel_reference_form.py",
"test_py": '''from slack_channel_reference_form import (config_line, path_outcomes,
                                           reference_form, resolve_name)

LIVE = {"id": "C01ABCDE9", "name": "alerts", "is_archived": False}
DEAD = {"id": "C09OLDONE", "name": "alerts", "is_archived": True}


def test_a_channel_id_is_the_canonical_form():
    form, _ = reference_form("C01ABCDE9")
    assert form == "channel-id"
    assert path_outcomes(form)[0] == "canonical"


def test_a_hash_name_is_accepted_by_one_family_and_refused_by_the_rest():
    form, _ = reference_form("#alerts")
    assert form == "hash-name"
    verdict, rows = path_outcomes(form)
    assert verdict == "split-brain"
    assert dict(rows)["chat.postMessage"] == "accepts"
    assert dict(rows)["conversations.history"] == "refuses"


def test_a_bare_name_lands_in_the_same_bucket_as_a_hash_name():
    assert reference_form("alerts")[0] == "bare-name"
    assert path_outcomes("bare-name")[0] == "split-brain"


def test_a_user_id_is_not_a_name_problem_because_nothing_errors():
    form, detail = reference_form("U024BE7LH")
    assert form == "user-id"
    assert "DM" in detail
    verdict, rows = path_outcomes(form)
    assert verdict == "wrong-entity"
    assert dict(rows)["chat.postMessage"] == "delivers elsewhere"


def test_a_permalink_carries_the_id_it_needs():
    form, detail = reference_form("https://acme.slack.com/archives/C01ABCDE9")
    assert form == "permalink"
    assert "C01ABCDE9" in detail


def test_an_empty_string_is_reported_as_its_own_shape():
    assert reference_form("")[0] == "empty"
    assert reference_form(None)[0] == "empty"
    assert path_outcomes("empty")[0] == "unusable"


def test_a_name_resolves_to_the_live_channel():
    state, channel, _ = resolve_name("#alerts", [LIVE])
    assert state == "resolved"
    assert channel["id"] == "C01ABCDE9"


def test_a_name_held_by_a_live_and_an_archived_channel_is_reported_as_contested():
    state, channel, detail = resolve_name("alerts", [DEAD, LIVE])
    assert state == "resolved-with-archived-twin"
    assert channel["id"] == "C01ABCDE9"
    assert "contested" in detail


def test_a_name_that_only_matches_an_archive_is_not_a_resolution():
    state, _, _ = resolve_name("alerts", [DEAD])
    assert state == "archived-only"


def test_two_live_channels_with_one_name_are_never_silently_picked():
    twin = dict(LIVE, id="C07OTHER1")
    state, channel, _ = resolve_name("alerts", [LIVE, twin])
    assert state == "ambiguous"
    assert channel is None


def test_the_repair_line_keeps_the_old_name_as_a_comment():
    line = config_line("ALERTS_CHANNEL", LIVE, "#alerts")
    assert line.startswith("ALERTS_CHANNEL=C01ABCDE9")
    assert "#alerts" in line
''',
"test_js_file": "slack-channel-reference-form.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { configLine, pathOutcomes, referenceForm, resolveName }
  from './slack-channel-reference-form.mjs';

const LIVE = { id: 'C01ABCDE9', name: 'alerts', is_archived: false };
const DEAD = { id: 'C09OLDONE', name: 'alerts', is_archived: true };

test('a channel id is the canonical form', () => {
  const [form] = referenceForm('C01ABCDE9');
  assert.equal(form, 'channel-id');
  assert.equal(pathOutcomes(form)[0], 'canonical');
});

test('a hash name is accepted by one family and refused by the rest', () => {
  const [form] = referenceForm('#alerts');
  assert.equal(form, 'hash-name');
  const [verdict, rows] = pathOutcomes(form);
  assert.equal(verdict, 'split-brain');
  const table = Object.fromEntries(rows);
  assert.equal(table['chat.postMessage'], 'accepts');
  assert.equal(table['conversations.history'], 'refuses');
});

test('a bare name lands in the same bucket as a hash name', () => {
  assert.equal(referenceForm('alerts')[0], 'bare-name');
  assert.equal(pathOutcomes('bare-name')[0], 'split-brain');
});

test('a user id is not a name problem because nothing errors', () => {
  const [form, detail] = referenceForm('U024BE7LH');
  assert.equal(form, 'user-id');
  assert.match(detail, /DM/);
  const [verdict, rows] = pathOutcomes(form);
  assert.equal(verdict, 'wrong-entity');
  assert.equal(Object.fromEntries(rows)['chat.postMessage'], 'delivers elsewhere');
});

test('a permalink carries the id it needs', () => {
  const [form, detail] = referenceForm('https://acme.slack.com/archives/C01ABCDE9');
  assert.equal(form, 'permalink');
  assert.match(detail, /C01ABCDE9/);
});

test('an empty string is reported as its own shape', () => {
  assert.equal(referenceForm('')[0], 'empty');
  assert.equal(referenceForm(null)[0], 'empty');
  assert.equal(pathOutcomes('empty')[0], 'unusable');
});

test('a name resolves to the live channel', () => {
  const [state, channel] = resolveName('#alerts', [LIVE]);
  assert.equal(state, 'resolved');
  assert.equal(channel.id, 'C01ABCDE9');
});

test('a name held by a live and an archived channel is reported as contested', () => {
  const [state, channel, detail] = resolveName('alerts', [DEAD, LIVE]);
  assert.equal(state, 'resolved-with-archived-twin');
  assert.equal(channel.id, 'C01ABCDE9');
  assert.match(detail, /contested/);
});

test('a name that only matches an archive is not a resolution', () => {
  assert.equal(resolveName('alerts', [DEAD])[0], 'archived-only');
});

test('two live channels with one name are never silently picked', () => {
  const twin = { ...LIVE, id: 'C07OTHER1' };
  const [state, channel] = resolveName('alerts', [LIVE, twin]);
  assert.equal(state, 'ambiguous');
  assert.equal(channel, null);
});

test('the repair line keeps the old name as a comment', () => {
  const line = configLine('ALERTS_CHANNEL', LIVE, '#alerts');
  assert.ok(line.startsWith('ALERTS_CHANNEL=C01ABCDE9'));
  assert.match(line, /#alerts/);
});
''',
"faq": [
 ("Why does chat.postMessage accept #alerts when conversations.info does not?",
  "Because chat.postMessage predates the conversations.* family and Slack kept its legacy name resolution for compatibility. The newer methods were never given the behaviour, and nothing in the documentation promises the old one keeps it. Treating that single exception as the rule is what produces a configuration that works on the send path and fails on every read."),
 ("Is there a method that converts a channel name into an ID?",
  "No, and that absence is deliberate rather than an oversight. The supported way is to paginate conversations.list and match on the name field yourself. Do it once at startup and cache the ID: doing it per message means a Tier 2 call over every channel in the workspace on every send, which trades channel_not_found for ratelimited."),
 ("Where do I find a channel ID without writing code?",
  "Open the channel in Slack, click the channel name to open its details, and the ID is at the bottom of that panel with a copy button. The web client also puts it in the URL after /archives/, which is why permalinks turn up in configuration files: the ID a developer needed was visible in the address bar."),
 ("Could channel_not_found mean something other than a name in an ID slot?",
  "Yes, and the script does not claim otherwise. The same error covers a private channel the token has no scope to see, a channel in a different workspace on Enterprise Grid, and a deleted channel. Ruling out the reference form first is worthwhile because it is the only one of those you can settle offline, in a regular expression, before making any request."),
 ("What happens if I put a user ID in the channel field?",
  "chat.postMessage opens a DM with that person and delivers the message, and returns ok: true. There is no error, no failed run and no alert. Meanwhile the channel that was supposed to receive it stays silent. It is the only shape in this note that is more dangerous than an outright failure, which is why the classifier gives it a verdict of its own."),
],
"related": [
 ("/slack/bot-not-in-channel/", "the ID is right and the bot is not a member"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
 ("/slack/pagination-not-followed/", "next_cursor and the channels you never saw"),
],
"citations": [CITE_CONV_LIST, CITE_CONV_INFO, CITE_POSTMESSAGE, CITE_CONV_API],
},

{
"slug": "archived-channel-target",
"title": "is_archived: the target channel was archived months ago",
"description": "The ID still resolves and conversations.info still answers ok. The channel is frozen, the alerts stopped, and nothing on the sending side ever raised.",
"h1": "is_archived: the target channel was archived months ago",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack is_archived error", "slack channel_is_archived webhook 410",
             "slack archived channel post failed", "slack conversations.list exclude_archived",
             "slack alerts stopped posting"],
"deps": "Python 3.9+ with requests, or Node.js 18+; dating the silence also needs channels:history",
"lead": "Nobody filed a ticket, because nothing looks broken. The channel is still there if you search for it, the ID in the config still resolves, and <code>conversations.info</code> still answers <code>ok: true</code>. What changed is one boolean inside that response, set during a reorganisation in March, and every alert since has been refused on the way in.",
"short_answer": """<p>Archiving does not delete a channel. The ID keeps resolving, <code>conversations.info</code> keeps succeeding, and the only difference is <code>channel.is_archived: true</code> &mdash; after which the channel accepts nothing from anyone, forever, until a human unarchives it. Sends fail with <code>is_archived</code>, and if the sender is an incoming webhook they fail with a real <code>HTTP 410 Gone</code>, which is one of the few places Slack breaks its own 200 habit.</p>
<p>The script below does not check your targets one at a time. It takes one paginated <code>conversations.list</code> sweep with <code>exclude_archived=false</code>, intersects the archived set with the channels your integration points at, dates the silence from the last message in each, and then looks for the live channel the traffic should have moved to. The answer here is not a corrected string; it is a different room.</p>""",
"problem": """<p>Archiving is a tidying action. Somebody closes out a project, a team reorganises, a quarter ends, and a dozen channels get archived in an afternoon by a person who has never seen your integration's configuration. Slack asks them to confirm; it does not tell them that a build pipeline, a PagerDuty bridge and a nightly digest are all addressed to one of the channels in the list.</p>
<p>From the integration's side there is nothing to notice. The failure is on the sending side, and the sending side is the half nobody watches: a cron job that exits 0, a webhook call whose response is discarded, a library that returns a result object nobody inspects. Alerts do not error, they simply stop arriving, and the absence of a message is the hardest event in the world to alert on.</p>
<p>What makes it worse is that the obvious health check passes. A startup assertion that calls <code>conversations.info</code> and checks for <code>ok: true</code> is satisfied by an archived channel. So is one that checks the ID resolves, and so is one that checks the bot is a member &mdash; membership is preserved through archiving. Every reasonable check short of reading the one boolean returns a clean bill of health for a channel that has been refusing messages since March.</p>""",
"why": """<p><strong>Archived is a state, not an absence.</strong> The channel object is intact: name, members, history, ID. Detection therefore cannot be an error-handling branch, because there is no error on the read path at all. It has to be a field assertion, which means somebody has to have decided in advance that the field is worth asserting on.</p>
<p><strong>The sweep is cheaper than the per-channel check.</strong> <code>conversations.info</code> per target is one Tier 3 call per channel; one paginated <code>conversations.list</code> is a handful of calls for the entire workspace and gives you the inventory you need for the successor search anyway. For anything beyond three or four targets the sweep wins, and it keeps working when the target list grows.</p>
<p><strong>You have to ask for archives explicitly.</strong> <code>conversations.list</code> defaults to <code>exclude_archived</code> being false in the reference, but plenty of client wrappers and plenty of existing code set it true because that is what a channel picker wants. A sweep built on that default cannot see the thing it is looking for: an archived target simply vanishes from the inventory and gets misreported as an unknown ID.</p>
<p><strong>The last message dates the outage.</strong> Reading one message with <code>conversations.history?limit=1</code> turns "this is archived" into "this went quiet on 4 January", which is the difference between a finding and an incident timeline. It needs <code>channels:history</code> and it needs the bot to have been a member before the archive, and where it is not available the script says so rather than inventing a date.</p>
<p><strong>Webhooks are the exception that proves the rule.</strong> An incoming webhook aimed at an archived channel returns <code>410 Gone</code> with a plain-text <code>channel_is_archived</code> body. Any HTTP client on earth surfaces that, which is why webhook-based integrations tend to discover this in days and Web API integrations tend to discover it in months.</p>""",
"steps": [
 {"h": "Sweep the workspace once, archives included",
  "body": """<p><code>conversations.list</code> with <code>types=public_channel,private_channel</code>, <code>exclude_archived=false</code> and <code>limit=1000</code>, following <code>next_cursor</code> to the end. Build a dictionary keyed by ID. Everything after this is a lookup rather than a call.</p>"""},
 {"h": "Intersect the archive with what you actually target",
  "body": """<p>A workspace of any age has hundreds of archived channels and none of them matter except the ones in your configuration. Feed the script the IDs your integration sends to, and the report is short enough that somebody will read it.</p>"""},
 {"h": "Separate archived from invisible",
  "body": """<p>A target that is not in the sweep at all is not archived; it is an ID this token cannot enumerate, which is a private-channel scope question and a different repair. Keeping the two verdicts apart matters, because "archived" sends you to the Slack admin UI and "invisible" sends you to the OAuth screen.</p>"""},
 {"h": "Date the silence from the last message",
  "body": """<p>One <code>conversations.history</code> call with <code>limit=1</code> per archived target. The <code>ts</code> of the newest message is when the room stopped, which is very close to when your alerts stopped. If the call is refused because the bot was never a member, report it as undatable: an archived channel cannot be joined, so that date is genuinely unrecoverable.</p>"""},
 {"h": "Find where the traffic went instead",
  "body": """<p>Teams rename rather than relocate. An archived <code>#ops-alerts</code> almost always sits beside a live <code>#ops-alerts-v2</code>, and an archived <code>#ops-alerts-old</code> beside a live <code>#ops-alerts</code>. The successor search matches on that stem and offers the shortest live candidate, as a suggestion with an ID attached rather than as an instruction.</p>"""},
 {"h": "Assert on the boolean at boot",
  "body": """<p>Add <code>is_archived</code> to the startup health check that already validates the token. An archive then shows up as a loud boot failure on the next deploy instead of as a silence somebody notices a quarter later. Unarchiving is a Slack UI action; there is no bot-callable unarchive for private channels.</p>"""},
],
"verify": """<p>After the configuration points at live channels, the sweep should report every target as live and exit 0.</p>
<pre><code class="language-bash">python3 slack_archived_target_sweep.py C01ABCDE9 C02XYZ123
# inventory: 1184 channel(s), 407 archived
# live      C01ABCDE9  #ops-alerts-v2   accepts messages
# live      C02XYZ123  #build-digest    accepts messages
# 2 target(s) checked, 0 archived, 0 invisible</code></pre>""",
"code_intro": "Three pure functions and two GET methods. <code>target_state</code> sorts a target against the swept inventory, <code>silence_since</code> turns one <code>conversations.history</code> response into a date or an honest refusal to give one, and <code>successor</code> is the only function in this section that offers a suggestion rather than a verdict &mdash; so it is deliberately conservative and returns nothing at all rather than a plausible wrong room.",
"py_file": "slack_archived_target_sweep.py",
"py": '''"""Find the integration targets that are pointing at archived Slack channels.

Read only. One paginated conversations.list, plus one conversations.history per
archived target to date the silence. Nothing is unarchived and nothing is
posted: the script names the frozen channel, says when it went quiet, and
suggests the live channel the traffic probably belongs in.
"""
import argparse
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_archived_target_sweep")

API = "https://slack.com/api/"

# Suffixes a team adds when it retires a channel rather than renaming the new
# one. Stripping them is how #ops-alerts-old finds its way back to #ops-alerts.
RETIRED_SUFFIXES = ("-old", "-archive", "-archived", "-deprecated", "-legacy",
                    "-retired", "-v1", "-tmp", "-temp")


def target_state(cid, inventory):
    """Sort one configured target against the swept inventory. Pure.

    Returns (state, channel, detail). `invisible` is deliberately not folded into
    an error bucket: a target missing from the sweep is a scope question, and it
    sends a reader to a different screen than an archived one does.
    """
    channel = inventory.get(cid)
    if channel is None:
        return ("invisible", None,
                "not in the sweep at all. Either the ID is wrong, or it is a "
                "private channel this token has no scope to enumerate. Slack will "
                "not say which.")
    name = channel.get("name") or "?"
    if channel.get("is_archived"):
        return ("archived", channel,
                "#%s is archived. The ID still resolves and conversations.info "
                "still answers ok; the channel accepts nothing from anyone." % name)
    if channel.get("is_general"):
        return ("live", channel,
                "#%s accepts messages, and it is the workspace default channel, "
                "which carries its own posting restrictions." % name)
    return ("live", channel, "#%s accepts messages" % name)


def silence_since(body):
    """Date the last message in a channel, or say why it cannot be dated. Pure.

    An archived channel cannot be joined, so a bot that was never a member before
    the archive can never read its history. That is a real limit and the script
    reports it rather than guessing at a date.
    """
    if body.get("ok") is not True:
        error = body.get("error") or "<no error field>"
        if error in ("not_in_channel", "channel_not_found"):
            return ("undatable",
                    "conversations.history says %s. An archived channel cannot be "
                    "joined, so if the bot was not already a member the date is "
                    "unrecoverable from here." % error)
        if error == "missing_scope":
            return ("undatable",
                    "missing_scope: needed=%s. The archive is readable with the "
                    "right scope, but not with this token."
                    % (body.get("needed") or "channels:history"))
        return ("undatable", "conversations.history answered ok: false, error=%s" % error)

    messages = body.get("messages") or []
    if not messages:
        return ("empty",
                "readable and holding no messages at all, which usually means the "
                "channel was archived before anything was ever sent to it")
    try:
        when = datetime.fromtimestamp(float(messages[0].get("ts")), timezone.utc)
    except (TypeError, ValueError):
        return ("undatable", "the newest message carries no readable ts")
    return ("dated", "last message %s, which is close enough to when the alerts "
                     "stopped arriving" % when.date().isoformat())


def successor(name, inventory):
    """Guess the live channel that replaced an archived one. Pure.

    Conservative on purpose. It matches only on an obvious shared stem and
    returns None rather than the nearest plausible room, because this is the one
    output here that a reader might act on without checking.
    """
    wanted = str(name or "").lower()
    if not wanted:
        return None

    stem = wanted
    for suffix in RETIRED_SUFFIXES:
        if stem.endswith(suffix) and len(stem) > len(suffix):
            stem = stem[: -len(suffix)]
            break

    candidates = []
    for channel in inventory:
        if channel.get("is_archived"):
            continue
        other = str(channel.get("name") or "").lower()
        if not other:
            continue
        if (other == stem or other.startswith(wanted + "-")
                or other.startswith(stem + "-")):
            candidates.append(channel)
    if not candidates:
        return None
    candidates.sort(key=lambda c: (len(str(c.get("name") or "")), str(c.get("name") or "")))
    return candidates[0]


def sweep(session):
    """Every channel the token can enumerate, archives deliberately included."""
    out, cursor = [], ""
    while True:
        params = {"types": "public_channel,private_channel",
                  "exclude_archived": "false", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.list", params=params, timeout=30).json()
        if body.get("ok") is not True:
            raise SystemExit("conversations.list answered 200 with ok: false, "
                             "error=%s" % body.get("error"))
        out.extend(body.get("channels") or [])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("targets", nargs="+", help="channel IDs the integration sends to")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:read and groups:read are enough for the sweep)",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    channels = sweep(s)
    inventory = {c.get("id"): c for c in channels}
    log.info("inventory: %d channel(s), %d archived", len(channels),
             sum(1 for c in channels if c.get("is_archived")))

    archived = invisible = 0
    for cid in args.targets:
        state, channel, detail = target_state(cid, inventory)
        if state == "live":
            log.info("%-9s %-12s %s", state, cid, detail)
            continue
        if state == "invisible":
            invisible += 1
            log.warning("%-9s %-12s %s", state, cid, detail)
            log.warning("  repair: check the ID, then add groups:read and reinstall "
                        "if the channel is private")
            continue

        archived += 1
        log.warning("%-9s %-12s %s", state, cid, detail)
        history = s.get(API + "conversations.history",
                        params={"channel": cid, "limit": 1}, timeout=30).json()
        dated, when = silence_since(history)
        log.warning("  %-9s %s", dated, when)
        moved = successor(channel.get("name"), channels)
        if moved is not None:
            log.warning("  repair: the traffic probably belongs in #%s (%s); confirm "
                        "with the team before you repoint it",
                        moved.get("name"), moved.get("id"))
        log.warning("  repair: unarchive in the Slack UI, or point the integration "
                    "at a live channel, then assert is_archived at boot")

    log.info("%d target(s) checked, %d archived, %d invisible",
             len(args.targets), archived, invisible)
    return 1 if (archived or invisible) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-archived-target-sweep.mjs",
"js": '''/**
 * Find the integration targets that are pointing at archived Slack channels.
 *
 * Read only. One paginated conversations.list, plus one conversations.history
 * per archived target to date the silence. Nothing is unarchived and nothing is
 * posted: the script names the frozen channel, says when it went quiet, and
 * suggests the live channel the traffic probably belongs in.
 */
const API = 'https://slack.com/api/';

// Suffixes a team adds when it retires a channel rather than renaming the new
// one. Stripping them is how #ops-alerts-old finds its way back to #ops-alerts.
const RETIRED_SUFFIXES = ['-old', '-archive', '-archived', '-deprecated', '-legacy',
  '-retired', '-v1', '-tmp', '-temp'];

/**
 * Sort one configured target against the swept inventory. Pure.
 * `invisible` is deliberately not folded into an error bucket: it is a scope
 * question, and it sends a reader to a different screen than an archive does.
 */
export function targetState(cid, inventory) {
  const channel = inventory.get(cid);
  if (!channel) {
    return ['invisible', null,
      'not in the sweep at all. Either the ID is wrong, or it is a private ' +
      'channel this token has no scope to enumerate. Slack will not say which.'];
  }
  const name = channel.name ?? '?';
  if (channel.is_archived) {
    return ['archived', channel,
      `#${name} is archived. The ID still resolves and conversations.info still ` +
      'answers ok; the channel accepts nothing from anyone.'];
  }
  if (channel.is_general) {
    return ['live', channel,
      `#${name} accepts messages, and it is the workspace default channel, which ` +
      'carries its own posting restrictions.'];
  }
  return ['live', channel, `#${name} accepts messages`];
}

/**
 * Date the last message in a channel, or say why it cannot be dated. Pure.
 * An archived channel cannot be joined, so a bot that was never a member before
 * the archive can never read its history.
 */
export function silenceSince(body) {
  if (body?.ok !== true) {
    const error = body?.error ?? '<no error field>';
    if (error === 'not_in_channel' || error === 'channel_not_found') {
      return ['undatable',
        `conversations.history says ${error}. An archived channel cannot be ` +
        'joined, so if the bot was not already a member the date is unrecoverable ' +
        'from here.'];
    }
    if (error === 'missing_scope') {
      return ['undatable',
        `missing_scope: needed=${body?.needed ?? 'channels:history'}. The archive ` +
        'is readable with the right scope, but not with this token.'];
    }
    return ['undatable', `conversations.history answered ok: false, error=${error}`];
  }

  const messages = body.messages ?? [];
  if (messages.length === 0) {
    return ['empty',
      'readable and holding no messages at all, which usually means the channel ' +
      'was archived before anything was ever sent to it'];
  }
  const seconds = Number(messages[0]?.ts);
  if (!Number.isFinite(seconds)) {
    return ['undatable', 'the newest message carries no readable ts'];
  }
  const when = new Date(seconds * 1000).toISOString().slice(0, 10);
  return ['dated',
    `last message ${when}, which is close enough to when the alerts stopped arriving`];
}

/**
 * Guess the live channel that replaced an archived one. Pure.
 * Conservative on purpose: it returns null rather than the nearest plausible
 * room, because this is the one output here a reader might act on unchecked.
 */
export function successor(name, inventory) {
  const wanted = String(name ?? '').toLowerCase();
  if (!wanted) return null;

  let stem = wanted;
  for (const suffix of RETIRED_SUFFIXES) {
    if (stem.endsWith(suffix) && stem.length > suffix.length) {
      stem = stem.slice(0, -suffix.length);
      break;
    }
  }

  const candidates = inventory.filter((channel) => {
    if (channel.is_archived) return false;
    const other = String(channel.name ?? '').toLowerCase();
    if (!other) return false;
    return other === stem || other.startsWith(`${wanted}-`) || other.startsWith(`${stem}-`);
  });
  if (candidates.length === 0) return null;
  candidates.sort((a, b) => String(a.name).length - String(b.name).length
    || String(a.name).localeCompare(String(b.name)));
  return candidates[0];
}

async function get(token, method, params) {
  const res = await fetch(`${API}${method}?${new URLSearchParams(params)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

async function sweep(token) {
  const out = [];
  let cursor = '';
  for (;;) {
    const params = {
      types: 'public_channel,private_channel',
      exclude_archived: 'false',
      limit: '1000',
    };
    if (cursor) params.cursor = cursor;
    const body = await get(token, 'conversations.list', params);
    if (body.ok !== true) {
      throw new Error(`conversations.list answered 200 with ok: false, error=${body.error}`);
    }
    out.push(...(body.channels ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) return out;
  }
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const targets = args.filter((a) => !a.startsWith('--') && a !== tokenEnv);
  if (targets.length === 0) {
    console.error('usage: slack-archived-target-sweep.mjs C01ABCDE9 [C02XYZ123 ...]');
    process.exitCode = 2;
    return;
  }
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:read and groups:read are enough for the sweep)`);
    process.exitCode = 2;
    return;
  }

  const channels = await sweep(token);
  const inventory = new Map(channels.map((c) => [c.id, c]));
  const archivedCount = channels.filter((c) => c.is_archived).length;
  console.log(`inventory: ${channels.length} channel(s), ${archivedCount} archived`);

  let archived = 0;
  let invisible = 0;
  for (const cid of targets) {
    const [state, channel, detail] = targetState(cid, inventory);
    if (state === 'live') {
      console.log(`${state.padEnd(9)} ${cid.padEnd(12)} ${detail}`);
      continue;
    }
    if (state === 'invisible') {
      invisible += 1;
      console.warn(`${state.padEnd(9)} ${cid.padEnd(12)} ${detail}`);
      console.warn('  repair: check the ID, then add groups:read and reinstall if ' +
                   'the channel is private');
      continue;
    }

    archived += 1;
    console.warn(`${state.padEnd(9)} ${cid.padEnd(12)} ${detail}`);
    const history = await get(token, 'conversations.history', { channel: cid, limit: '1' });
    const [dated, when] = silenceSince(history);
    console.warn(`  ${dated.padEnd(9)} ${when}`);
    const moved = successor(channel.name, channels);
    if (moved) {
      console.warn(`  repair: the traffic probably belongs in #${moved.name} ` +
                   `(${moved.id}); confirm with the team before you repoint it`);
    }
    console.warn('  repair: unarchive in the Slack UI, or point the integration at a ' +
                 'live channel, then assert is_archived at boot');
  }

  console.log(`${targets.length} target(s) checked, ${archived} archived, ` +
              `${invisible} invisible`);
  process.exitCode = archived || invisible ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "<code>successor</code> gets the most attention, because it is the only function here whose output is a suggestion and the only one that could plausibly send somebody to repoint an alert stream at the wrong room. The tests pin both naming conventions teams actually use, and pin the negative case hardest: an archived channel with no obvious replacement has to return nothing rather than the closest thing in the workspace.",
"test_py_file": "test_slack_archived_target_sweep.py",
"test_py": '''from slack_archived_target_sweep import silence_since, successor, target_state

LIVE = {"id": "C01LIVE00", "name": "ops-alerts-v2", "is_archived": False}
DEAD = {"id": "C02DEAD00", "name": "ops-alerts", "is_archived": True}
GENERAL = {"id": "C03GEN000", "name": "general", "is_archived": False, "is_general": True}


def test_an_archived_target_is_a_finding_even_though_the_id_resolves():
    state, channel, detail = target_state("C02DEAD00", {"C02DEAD00": DEAD})
    assert state == "archived"
    assert channel["id"] == "C02DEAD00"
    assert "conversations.info still answers ok" in detail


def test_a_live_target_passes():
    assert target_state("C01LIVE00", {"C01LIVE00": LIVE})[0] == "live"


def test_a_target_missing_from_the_sweep_is_invisible_not_archived():
    state, channel, detail = target_state("C09GHOST0", {"C01LIVE00": LIVE})
    assert state == "invisible"
    assert channel is None
    assert "not say which" in detail


def test_the_default_channel_is_still_live_but_says_so():
    state, _, detail = target_state("C03GEN000", {"C03GEN000": GENERAL})
    assert state == "live"
    assert "default channel" in detail


def test_the_last_message_dates_the_silence():
    state, detail = silence_since({"ok": True, "messages": [{"ts": "1735981953.000100"}]})
    assert state == "dated"
    assert "2025-01-04" in detail


def test_history_refused_to_a_non_member_is_undatable_not_wrong():
    state, detail = silence_since({"ok": False, "error": "not_in_channel"})
    assert state == "undatable"
    assert "cannot be joined" in detail


def test_a_readable_but_empty_archive_is_its_own_answer():
    assert silence_since({"ok": True, "messages": []})[0] == "empty"


def test_a_versioned_replacement_is_offered():
    moved = successor("ops-alerts", [DEAD, LIVE])
    assert moved["name"] == "ops-alerts-v2"


def test_a_retired_suffix_finds_its_way_back_to_the_stem():
    old = {"id": "C04OLD000", "name": "ops-alerts-old", "is_archived": True}
    live = {"id": "C05NEW000", "name": "ops-alerts", "is_archived": False}
    assert successor("ops-alerts-old", [old, live])["name"] == "ops-alerts"


def test_the_shortest_candidate_wins():
    inventory = [DEAD, LIVE, {"id": "C06LONG00", "name": "ops-alerts-v2-testing",
                              "is_archived": False}]
    assert successor("ops-alerts", inventory)["name"] == "ops-alerts-v2"


def test_no_obvious_replacement_returns_nothing_at_all():
    inventory = [DEAD, {"id": "C07RAND00", "name": "random", "is_archived": False}]
    assert successor("ops-alerts", inventory) is None


def test_an_archived_lookalike_is_never_offered_as_a_successor():
    twin = {"id": "C08DEAD00", "name": "ops-alerts-v2", "is_archived": True}
    assert successor("ops-alerts", [DEAD, twin]) is None
''',
"test_js_file": "slack-archived-target-sweep.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { silenceSince, successor, targetState }
  from './slack-archived-target-sweep.mjs';

const LIVE = { id: 'C01LIVE00', name: 'ops-alerts-v2', is_archived: false };
const DEAD = { id: 'C02DEAD00', name: 'ops-alerts', is_archived: true };
const GENERAL = { id: 'C03GEN000', name: 'general', is_archived: false, is_general: true };

test('an archived target is a finding even though the id resolves', () => {
  const [state, channel, detail] = targetState('C02DEAD00', new Map([['C02DEAD00', DEAD]]));
  assert.equal(state, 'archived');
  assert.equal(channel.id, 'C02DEAD00');
  assert.match(detail, /conversations\\.info still answers ok/);
});

test('a live target passes', () => {
  assert.equal(targetState('C01LIVE00', new Map([['C01LIVE00', LIVE]]))[0], 'live');
});

test('a target missing from the sweep is invisible not archived', () => {
  const [state, channel, detail] = targetState('C09GHOST0', new Map([['C01LIVE00', LIVE]]));
  assert.equal(state, 'invisible');
  assert.equal(channel, null);
  assert.match(detail, /not say which/);
});

test('the default channel is still live but says so', () => {
  const [state, , detail] = targetState('C03GEN000', new Map([['C03GEN000', GENERAL]]));
  assert.equal(state, 'live');
  assert.match(detail, /default channel/);
});

test('the last message dates the silence', () => {
  const [state, detail] = silenceSince({ ok: true, messages: [{ ts: '1735981953.000100' }] });
  assert.equal(state, 'dated');
  assert.match(detail, /2025-01-04/);
});

test('history refused to a non member is undatable not wrong', () => {
  const [state, detail] = silenceSince({ ok: false, error: 'not_in_channel' });
  assert.equal(state, 'undatable');
  assert.match(detail, /cannot be joined/);
});

test('a readable but empty archive is its own answer', () => {
  assert.equal(silenceSince({ ok: true, messages: [] })[0], 'empty');
});

test('a versioned replacement is offered', () => {
  assert.equal(successor('ops-alerts', [DEAD, LIVE]).name, 'ops-alerts-v2');
});

test('a retired suffix finds its way back to the stem', () => {
  const old = { id: 'C04OLD000', name: 'ops-alerts-old', is_archived: true };
  const live = { id: 'C05NEW000', name: 'ops-alerts', is_archived: false };
  assert.equal(successor('ops-alerts-old', [old, live]).name, 'ops-alerts');
});

test('the shortest candidate wins', () => {
  const inventory = [DEAD, LIVE,
    { id: 'C06LONG00', name: 'ops-alerts-v2-testing', is_archived: false }];
  assert.equal(successor('ops-alerts', inventory).name, 'ops-alerts-v2');
});

test('no obvious replacement returns nothing at all', () => {
  const inventory = [DEAD, { id: 'C07RAND00', name: 'random', is_archived: false }];
  assert.equal(successor('ops-alerts', inventory), null);
});

test('an archived lookalike is never offered as a successor', () => {
  const twin = { id: 'C08DEAD00', name: 'ops-alerts-v2', is_archived: true };
  assert.equal(successor('ops-alerts', [DEAD, twin]), null);
});
''',
"faq": [
 ("Can a bot unarchive a channel?",
  "Not usefully. conversations.unarchive exists for public channels and needs a write scope this section's scripts deliberately do not hold, and there is no unarchive for private channels at all. In practice a workspace admin unarchives from the Slack UI. That is why the script prints the repair rather than performing it: the useful automation here is the detection, not the action."),
 ("Why does my webhook get a 410 when the Web API returns 200?",
  "Incoming webhooks are one of the few Slack surfaces that answer with real HTTP status codes and a plain-text body, so an archived channel comes back as 410 Gone with channel_is_archived. The Web API keeps its usual habit and returns 200 with ok: false and error: is_archived. The same fault, two completely different shapes, which is why webhook integrations tend to find this in days."),
 ("Does the bot stay a member of an archived channel?",
  "Yes. Membership, history and the channel ID all survive archiving, which is exactly why membership checks pass while sends fail. If your health check asks is_member and stops there, an archived channel reports as healthy. Both booleans have to be read, and is_archived has to be read first because it outranks membership entirely."),
 ("How far back can conversations.history date the silence?",
  "As far as the workspace retention policy allows. On a free plan, history beyond the visible window is not returned at all, so a channel archived a year ago may come back empty and the script reports it as empty rather than dated. Treat the date as corroboration when you get it and do not build the report around always having one."),
 ("Should the script pick the successor channel automatically?",
  "No, and the successor function is written to under-reach for exactly that reason. Matching #ops-alerts to #ops-alerts-v2 is a naming convention, not a fact Slack asserts, and repointing an alert stream at the wrong room is a worse outcome than the alerts staying stopped for another hour. It prints a candidate with its ID and asks a human to confirm."),
],
"related": [
 ("/slack/bot-not-in-channel/", "membership passes while the send still fails"),
 ("/slack/non-marketplace-history-clamp/", "conversations.history clamped to one call a minute"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
],
"citations": [CITE_CONV_INFO, CITE_CONV_LIST, CITE_CONV_HISTORY, CITE_WEBHOOKS],
},

{
"slug": "private-channel-invisible",
"title": "channel_not_found: private, and the token cannot see it",
"description": "A private channel without groups:read is not missing, it is invisible. Slack says channel_not_found either way, so read the grant instead of the error.",
"h1": "channel_not_found: private, and the token cannot see it",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack groups:read missing", "slack private channel channel_not_found",
             "slack conversations.list private_channel empty", "slack bot cannot see private channel",
             "slack groups:history scope"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You are looking at the channel. It is on the screen, the ID is copied from its details panel, other people are talking in it. <code>conversations.info</code> says <code>channel_not_found</code>, and <code>conversations.list</code> returns four hundred channels without it. Nothing is wrong with the ID. The token has not been told that private channels exist.",
"short_answer": """<p>Slack splits conversation access by type. <code>channels:read</code> covers public channels, <code>groups:read</code> covers private ones, <code>im:*</code> covers DMs and <code>mpim:*</code> covers group DMs. A token holding only the <code>channels:*</code> pair cannot see private conversations at all &mdash; they are absent from <code>conversations.list</code>, and <code>conversations.info</code> on one answers <code>channel_not_found</code> rather than a permission error. That is intentional: Slack will not confirm a private channel exists to a token that is not allowed to know.</p>
<p>So do not read the error, read the grant. The script below takes <code>X-OAuth-Scopes</code> off the response header and uses it to decide which of three situations you are in: no <code>groups:read</code> at all, the scope granted but the bot in no private channel, or the scope granted and this particular ID outside the visible set. The third one is genuinely undecidable from a read-only token, and the script says so instead of guessing.</p>""",
"problem": """<p>The install screen makes this easy to get wrong. Bot Token Scopes is a long searchable list, <code>channels:read</code> sounds like it means "channels", and nothing on the page suggests that private channels are governed by a scope with a completely different name. The word "groups" is a survival from Slack's pre-2018 API, where private channels were a separate object type called groups, and the scope names never caught up with the vocabulary the product uses today.</p>
<p>Then the error hides the mistake. If Slack answered <code>missing_scope</code> here, this note would not need to exist &mdash; that error names what was <code>needed</code> and what was <code>provided</code>, and the repair reads itself. Instead <code>conversations.info</code> on a private channel answers <code>channel_not_found</code>, which is a statement about the ID rather than about the permission. A developer who trusts the error spends the afternoon checking that the ID is right, and the ID is right.</p>
<p>The second half of the trap arrives after the scope is added. <code>groups:read</code> grants the ability to see private channels <em>the bot belongs to</em>, not visibility into every private channel in the workspace. So the reinstall completes, <code>conversations.list?types=private_channel</code> comes back <code>ok: true</code> with an empty array, and it looks like the scope did not take. It took. Nobody has invited the bot yet, and no API call can invite it &mdash; a private channel cannot be self-joined.</p>""",
"why": """<p><strong>The ambiguity is a security property.</strong> If a token without <code>groups:read</code> got <code>missing_scope</code> for one ID and <code>channel_not_found</code> for another, that difference would be an oracle: anyone with a bot token could enumerate which private channel IDs exist. Slack collapses both into <code>channel_not_found</code> on purpose, and no amount of cleverness in your script recovers the distinction.</p>
<p><strong>The header is the honest source.</strong> Every Web API response carries <code>X-OAuth-Scopes</code> listing what the token actually holds. That is a direct read of the grant rather than an inference from a failure, it costs nothing on top of a call you are already making, and it answers the question the error refuses to.</p>
<p><strong>Read and history are separate grants.</strong> <code>groups:read</code> lets the bot enumerate and inspect a private channel. Reading its messages needs <code>groups:history</code> as well. An app that adds only the first will list the channel happily and then fail on the call that actually matters, which reads as a second, unrelated bug.</p>
<p><strong>Empty is a result, not a failure.</strong> <code>ok: true</code> with zero channels is the workspace telling you the bot is a member of no private conversations. Treating that as an error sends people back to the scopes screen they just fixed; treating it as a membership finding sends them to a human who can run <code>/invite</code>.</p>
<p><strong>Conversion moves a channel across the boundary.</strong> A public channel converted to private keeps its ID, so a call that worked last week starts answering <code>channel_not_found</code> with no deploy on your side. The scope check is the same, but the story is different, and it is worth naming when the ID used to work.</p>""",
"steps": [
 {"h": "Take the grant off the header of a call you are already making",
  "body": """<p>One <code>auth.test</code>, which needs no scopes, and read <code>X-OAuth-Scopes</code> from the response headers. That string is the authoritative list of what the token holds. Everything after this is interpretation of a fact rather than inference from a symptom.</p>"""},
 {"h": "Split the grant by conversation type",
  "body": """<p>Four pairs: public, private, DM, group DM, each with a read scope and a history scope. Printing the grid makes the shape of the gap obvious, and it catches the app that has <code>groups:read</code> without <code>groups:history</code> before that turns into a second incident.</p>"""},
 {"h": "Ask for the private list explicitly",
  "body": """<p><code>conversations.list?types=private_channel</code>, paginated. With the scope missing this returns <code>missing_scope</code> and <code>needed: groups:read</code>, which corroborates the header. With the scope present it returns exactly the private channels the bot belongs to.</p>"""},
 {"h": "Distinguish no scope from no membership",
  "body": """<p>These are the two states that both look like "I cannot see it" and they need opposite repairs. Missing scope is an OAuth screen and a reinstall. Empty list with the scope present is a person running <code>/invite @YourApp</code> inside the room. Reporting them as one finding sends half your readers to the wrong place.</p>"""},
 {"h": "Refuse to answer the third question",
  "body": """<p>If the scope is granted, the visible set is non-empty, and your ID is not in it, then it is either a private channel the bot was never invited to or an ID that does not exist &mdash; and a read-only token cannot tell those apart, by design. The script prints that plainly. An audit that guesses here is worse than one that admits the limit.</p>"""},
 {"h": "Add the scope, reinstall, then get the bot invited",
  "body": """<p>Both steps, in that order. Add <code>groups:read</code> and <code>groups:history</code> to Bot Token Scopes and reinstall the app, then have a member of each private channel invite it. Neither half works alone, and the reinstall is what people forget: adding a scope in the app configuration does nothing to the token already in your environment.</p>"""},
],
"verify": """<p>Once the scope is granted and the bot has been invited, the probe should place every target in the visible set.</p>
<pre><code class="language-bash">python3 slack_private_visibility_probe.py G01SECRET1
# grant: private_channel read=yes history=yes
# visible   G01SECRET1  the token is in this private channel and can read its metadata
# 1 target(s) checked, 0 that this token cannot account for</code></pre>""",
"code_intro": "The interesting decision is what the script refuses to conclude. <code>scope_posture</code> parses the granted-scope header into the four conversation families, <code>visibility_verdict</code> combines that with the private listing to reach one of five states &mdash; one of which is an explicit &ldquo;no read-only token can answer this&rdquo; &mdash; and <code>repair_for</code> maps each state to the repair, so the wrong screen is never suggested for the right finding.",
"py_file": "slack_private_visibility_probe.py",
"py": '''"""Say why a Slack private channel is invisible: no scope, or no invitation.

Read only. One auth.test for the granted-scope header and one paginated
conversations.list for the private set. The script reaches a verdict about the
token's grant, prints the repair, and declines to answer the one question a
read-only token genuinely cannot.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_private_visibility_probe")

API = "https://slack.com/api/"

# "groups" is a survival from the pre-2018 API where private channels were a
# separate object type. The product stopped using the word; the scopes did not.
CONVERSATION_SCOPES = (
    ("public_channel", "channels:read", "channels:history"),
    ("private_channel", "groups:read", "groups:history"),
    ("im", "im:read", "im:history"),
    ("mpim", "mpim:read", "mpim:history"),
)


def scope_posture(header):
    """Read the granted-scope header into a per-conversation-type grid. Pure.

    Returns (state, rows) with rows as [(kind, can_list, can_read_history), ...].
    The header is a direct statement of the grant, which is the whole point: the
    error a private channel produces is not.
    """
    granted = {s.strip() for s in str(header or "").split(",") if s.strip()}
    if not granted:
        return ("unknown", [])

    rows = [(kind, read in granted, history in granted)
            for kind, read, history in CONVERSATION_SCOPES]
    private = {kind: (can_list, can_read) for kind, can_list, can_read in rows}
    can_list, can_read = private["private_channel"]
    if not can_list:
        return ("no-private-read", rows)
    if not can_read:
        return ("private-list-only", rows)
    return ("private-readable", rows)


def visibility_verdict(posture, listing, target_id=None):
    """Decide what a channel_not_found on a private channel actually means. Pure.

    This function is allowed to answer "I cannot tell", and does. The ambiguity is
    deliberate on Slack's side: a token that may not see private channels is not
    told that one exists, because that difference would be an enumeration oracle.
    """
    ok = listing.get("ok") is True
    error = listing.get("error") or "<no error field>"

    if posture == "unknown":
        return ("unknown-grant",
                "no X-OAuth-Scopes header came back, so the grant could not be "
                "read. Nothing below follows from an empty channel list alone.")

    if posture == "no-private-read":
        answered = "ok: true with an empty list" if ok else "error=" + error
        return ("invisible-by-scope",
                "the grant has no groups:read, so private channels are not empty "
                "for this token, they are absent. conversations.list answered %s. "
                "Every private ID returns channel_not_found, which is Slack "
                "declining to confirm the channel exists." % answered)

    if not ok:
        if error == "missing_scope":
            return ("invisible-by-scope",
                    "missing_scope: needed=%s, provided=%s. The header and the "
                    "error agree." % (listing.get("needed") or "groups:read",
                                      listing.get("provided") or "?"))
        return ("inconclusive",
                "conversations.list answered ok: false, error=%s. Resolve that "
                "before reading anything into visibility." % error)

    channels = listing.get("channels") or []
    if not channels:
        return ("scope-without-membership",
                "groups:read is granted and the token belongs to no private "
                "channel at all. The scope is the ability to see private channels "
                "the bot is in, not blanket visibility into the workspace.")

    if target_id is None:
        return ("visible-set",
                "%d private channel(s) visible to this token" % len(channels))
    if target_id in {c.get("id") for c in channels}:
        return ("visible",
                "the token is in this private channel and can read its metadata")
    return ("outside-the-visible-set",
            "groups:read is granted, %d private channel(s) are visible, and this "
            "ID is not one of them. That is genuinely two possibilities -- a "
            "private channel the bot was never invited to, or an ID that does not "
            "exist -- and no read-only token separates them." % len(channels))


def repair_for(state):
    """The repair each verdict actually calls for. Pure, and printed, never run."""
    if state == "invisible-by-scope":
        return ("add groups:read (and groups:history if the app reads messages) to "
                "Bot Token Scopes",
                "reinstall the app: a scope added in the configuration does nothing "
                "to the token already in your environment")
    if state == "private-list-only":
        return ("add groups:history as well; groups:read lists the channel and does "
                "not read a word of it",)
    if state == "scope-without-membership":
        return ("a member of the private channel runs /invite @YourApp; no API call "
                "joins a private channel",)
    if state == "outside-the-visible-set":
        return ("ask somebody who is in the channel whether the bot is a member and "
                "whether the ID is right; the API will not say",)
    if state == "unknown-grant":
        return ("check that the response really came from slack.com; a proxy that "
                "strips headers takes the grant with it",)
    return ()


def private_listing(session):
    """Every private channel the token can enumerate, as one listing-shaped dict."""
    channels, cursor = [], ""
    while True:
        params = {"types": "private_channel", "exclude_archived": "false", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.list", params=params, timeout=30).json()
        if body.get("ok") is not True:
            return body
        channels.extend(body.get("channels") or [])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return {"ok": True, "channels": channels}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("targets", nargs="*",
                    help="private channel IDs the integration expects to see")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (auth.test needs no scopes; the listing needs groups:read)",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    probe = s.get(API + "auth.test", timeout=30)
    identity = probe.json()
    if identity.get("ok") is not True:
        log.error("auth.test answered 200 with ok: false, error=%s", identity.get("error"))
        return 2
    log.info("token acts as %s (%s) in %s", identity.get("user"),
             identity.get("user_id"), identity.get("team"))

    posture, rows = scope_posture(probe.headers.get("x-oauth-scopes"))
    for kind, can_list, can_read in rows:
        log.info("grant: %-16s read=%-3s history=%s", kind,
                 "yes" if can_list else "no", "yes" if can_read else "no")

    listing = private_listing(s)
    bad = 0

    if posture == "private-list-only":
        log.warning("%-24s %s", "private-list-only",
                    "groups:read without groups:history: the channel will list and "
                    "its messages will not read")
        for line in repair_for("private-list-only"):
            log.warning("  repair: %s", line)
        bad += 1

    for target in (args.targets or [None]):
        state, detail = visibility_verdict(posture, listing, target)
        label = target or "<no target given>"
        if state in ("visible", "visible-set"):
            log.info("%-24s %-12s %s", state, label, detail)
            continue
        bad += 1
        log.warning("%-24s %-12s %s", state, label, detail)
        for line in repair_for(state):
            log.warning("  repair: %s", line)

    log.info("%d target(s) checked, %d that this token cannot account for",
             len(args.targets), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-private-visibility-probe.mjs",
"js": '''/**
 * Say why a Slack private channel is invisible: no scope, or no invitation.
 *
 * Read only. One auth.test for the granted-scope header and one paginated
 * conversations.list for the private set. The script reaches a verdict about the
 * token's grant, prints the repair, and declines to answer the one question a
 * read-only token genuinely cannot.
 */
const API = 'https://slack.com/api/';

// "groups" is a survival from the pre-2018 API where private channels were a
// separate object type. The product stopped using the word; the scopes did not.
const CONVERSATION_SCOPES = [
  ['public_channel', 'channels:read', 'channels:history'],
  ['private_channel', 'groups:read', 'groups:history'],
  ['im', 'im:read', 'im:history'],
  ['mpim', 'mpim:read', 'mpim:history'],
];

/**
 * Read the granted-scope header into a per-conversation-type grid. Pure.
 * The header is a direct statement of the grant, which is the whole point: the
 * error a private channel produces is not.
 */
export function scopePosture(header) {
  const granted = new Set(String(header ?? '').split(',').map((s) => s.trim()).filter(Boolean));
  if (granted.size === 0) return ['unknown', []];

  const rows = CONVERSATION_SCOPES.map(([kind, read, history]) =>
    [kind, granted.has(read), granted.has(history)]);
  const [, canList, canRead] = rows.find(([kind]) => kind === 'private_channel');
  if (!canList) return ['no-private-read', rows];
  if (!canRead) return ['private-list-only', rows];
  return ['private-readable', rows];
}

/**
 * Decide what a channel_not_found on a private channel actually means. Pure.
 * This function is allowed to answer "I cannot tell", and does: the ambiguity is
 * deliberate on Slack's side, because the difference would be an enumeration oracle.
 */
export function visibilityVerdict(posture, listing, targetId = null) {
  const ok = listing?.ok === true;
  const error = listing?.error ?? '<no error field>';

  if (posture === 'unknown') {
    return ['unknown-grant',
      'no X-OAuth-Scopes header came back, so the grant could not be read. ' +
      'Nothing below follows from an empty channel list alone.'];
  }

  if (posture === 'no-private-read') {
    const answered = ok ? 'ok: true with an empty list' : `error=${error}`;
    return ['invisible-by-scope',
      'the grant has no groups:read, so private channels are not empty for this ' +
      `token, they are absent. conversations.list answered ${answered}. Every ` +
      'private ID returns channel_not_found, which is Slack declining to confirm ' +
      'the channel exists.'];
  }

  if (!ok) {
    if (error === 'missing_scope') {
      return ['invisible-by-scope',
        `missing_scope: needed=${listing?.needed ?? 'groups:read'}, ` +
        `provided=${listing?.provided ?? '?'}. The header and the error agree.`];
    }
    return ['inconclusive',
      `conversations.list answered ok: false, error=${error}. Resolve that before ` +
      'reading anything into visibility.'];
  }

  const channels = listing.channels ?? [];
  if (channels.length === 0) {
    return ['scope-without-membership',
      'groups:read is granted and the token belongs to no private channel at all. ' +
      'The scope is the ability to see private channels the bot is in, not blanket ' +
      'visibility into the workspace.'];
  }

  if (targetId === null) {
    return ['visible-set', `${channels.length} private channel(s) visible to this token`];
  }
  if (channels.some((c) => c.id === targetId)) {
    return ['visible', 'the token is in this private channel and can read its metadata'];
  }
  return ['outside-the-visible-set',
    `groups:read is granted, ${channels.length} private channel(s) are visible, and ` +
    'this ID is not one of them. That is genuinely two possibilities -- a private ' +
    'channel the bot was never invited to, or an ID that does not exist -- and no ' +
    'read-only token separates them.'];
}

/** The repair each verdict actually calls for. Pure, and printed, never run. */
export function repairFor(state) {
  if (state === 'invisible-by-scope') {
    return ['add groups:read (and groups:history if the app reads messages) to Bot ' +
      'Token Scopes',
    'reinstall the app: a scope added in the configuration does nothing to the ' +
      'token already in your environment'];
  }
  if (state === 'private-list-only') {
    return ['add groups:history as well; groups:read lists the channel and does not ' +
      'read a word of it'];
  }
  if (state === 'scope-without-membership') {
    return ['a member of the private channel runs /invite @YourApp; no API call joins ' +
      'a private channel'];
  }
  if (state === 'outside-the-visible-set') {
    return ['ask somebody who is in the channel whether the bot is a member and ' +
      'whether the ID is right; the API will not say'];
  }
  if (state === 'unknown-grant') {
    return ['check that the response really came from slack.com; a proxy that strips ' +
      'headers takes the grant with it'];
  }
  return [];
}

async function privateListing(token) {
  const channels = [];
  let cursor = '';
  for (;;) {
    const params = new URLSearchParams({
      types: 'private_channel', exclude_archived: 'false', limit: '1000',
    });
    if (cursor) params.set('cursor', cursor);
    const res = await fetch(`${API}conversations.list?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = await res.json();
    if (body.ok !== true) return body;
    channels.push(...(body.channels ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) return { ok: true, channels };
  }
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const targets = args.filter((a) => !a.startsWith('--') && a !== tokenEnv);
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (auth.test needs no scopes; the listing needs groups:read)`);
    process.exitCode = 2;
    return;
  }

  const probe = await fetch(`${API}auth.test`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const identity = await probe.json();
  if (identity.ok !== true) {
    console.error(`auth.test answered 200 with ok: false, error=${identity.error}`);
    process.exitCode = 2;
    return;
  }
  console.log(`token acts as ${identity.user} (${identity.user_id}) in ${identity.team}`);

  const [posture, rows] = scopePosture(probe.headers.get('x-oauth-scopes'));
  for (const [kind, canList, canRead] of rows) {
    console.log(`grant: ${kind.padEnd(16)} read=${(canList ? 'yes' : 'no').padEnd(3)} ` +
                `history=${canRead ? 'yes' : 'no'}`);
  }

  const listing = await privateListing(token);
  let bad = 0;

  if (posture === 'private-list-only') {
    console.warn(`${'private-list-only'.padEnd(24)} groups:read without ` +
                 'groups:history: the channel will list and its messages will not read');
    for (const line of repairFor('private-list-only')) console.warn(`  repair: ${line}`);
    bad += 1;
  }

  for (const target of targets.length ? targets : [null]) {
    const [state, detail] = visibilityVerdict(posture, listing, target);
    const label = target ?? '<no target given>';
    if (state === 'visible' || state === 'visible-set') {
      console.log(`${state.padEnd(24)} ${label.padEnd(12)} ${detail}`);
      continue;
    }
    bad += 1;
    console.warn(`${state.padEnd(24)} ${label.padEnd(12)} ${detail}`);
    for (const line of repairFor(state)) console.warn(`  repair: ${line}`);
  }

  console.log(`${targets.length} target(s) checked, ${bad} that this token cannot account for`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertion that matters most is a negative one: given a granted scope, a non-empty visible set and an ID outside it, the verdict has to be <code>outside-the-visible-set</code> and the repair has to be &ldquo;ask a person&rdquo;, not a confident claim that the channel does not exist. The rest of the suite pins the two states that look identical from the outside &mdash; no scope, and no invitation &mdash; onto their two different repairs.",
"test_py_file": "test_slack_private_visibility_probe.py",
"test_py": '''from slack_private_visibility_probe import (repair_for, scope_posture,
                                            visibility_verdict)

FULL = "channels:read,channels:history,groups:read,groups:history,chat:write"
PUBLIC_ONLY = "channels:read,channels:history,chat:write"
LIST_ONLY = "channels:read,groups:read,chat:write"
PRIVATE = {"id": "G01SECRET1", "name": "leadership"}


def test_the_header_is_read_into_a_per_type_grid():
    state, rows = scope_posture(FULL)
    assert state == "private-readable"
    assert dict((kind, (a, b)) for kind, a, b in rows)["private_channel"] == (True, True)
    assert dict((kind, (a, b)) for kind, a, b in rows)["im"] == (False, False)


def test_a_public_only_grant_cannot_see_private_channels():
    assert scope_posture(PUBLIC_ONLY)[0] == "no-private-read"


def test_read_without_history_is_its_own_posture():
    assert scope_posture(LIST_ONLY)[0] == "private-list-only"


def test_a_missing_header_is_not_read_as_a_missing_scope():
    assert scope_posture("")[0] == "unknown"
    assert visibility_verdict("unknown", {"ok": True, "channels": []})[0] == "unknown-grant"


def test_no_scope_makes_the_channel_absent_rather_than_empty():
    state, detail = visibility_verdict(
        "no-private-read", {"ok": False, "error": "missing_scope"}, "G01SECRET1")
    assert state == "invisible-by-scope"
    assert "declining to confirm" in detail


def test_the_scope_granted_with_no_membership_is_a_different_finding():
    state, detail = visibility_verdict(
        "private-readable", {"ok": True, "channels": []}, "G01SECRET1")
    assert state == "scope-without-membership"
    assert "not blanket visibility" in detail


def test_a_visible_private_channel_passes():
    state, _ = visibility_verdict(
        "private-readable", {"ok": True, "channels": [PRIVATE]}, "G01SECRET1")
    assert state == "visible"


def test_an_id_outside_the_visible_set_is_never_declared_nonexistent():
    state, detail = visibility_verdict(
        "private-readable", {"ok": True, "channels": [PRIVATE]}, "G09OTHER99")
    assert state == "outside-the-visible-set"
    assert "two possibilities" in detail
    assert "no read-only token separates them" in detail


def test_an_unrelated_error_is_inconclusive_not_a_visibility_answer():
    state, _ = visibility_verdict(
        "private-readable", {"ok": False, "error": "ratelimited"}, "G01SECRET1")
    assert state == "inconclusive"


def test_the_two_lookalike_states_get_different_repairs():
    scope_fix = " ".join(repair_for("invisible-by-scope"))
    invite_fix = " ".join(repair_for("scope-without-membership"))
    assert "reinstall" in scope_fix
    assert "/invite" in invite_fix
    assert "reinstall" not in invite_fix


def test_the_undecidable_state_asks_a_human_rather_than_guessing():
    assert "will not say" in " ".join(repair_for("outside-the-visible-set"))
''',
"test_js_file": "slack-private-visibility-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { repairFor, scopePosture, visibilityVerdict }
  from './slack-private-visibility-probe.mjs';

const FULL = 'channels:read,channels:history,groups:read,groups:history,chat:write';
const PUBLIC_ONLY = 'channels:read,channels:history,chat:write';
const LIST_ONLY = 'channels:read,groups:read,chat:write';
const PRIVATE = { id: 'G01SECRET1', name: 'leadership' };

test('the header is read into a per type grid', () => {
  const [state, rows] = scopePosture(FULL);
  assert.equal(state, 'private-readable');
  const grid = Object.fromEntries(rows.map(([kind, a, b]) => [kind, [a, b]]));
  assert.deepEqual(grid.private_channel, [true, true]);
  assert.deepEqual(grid.im, [false, false]);
});

test('a public only grant cannot see private channels', () => {
  assert.equal(scopePosture(PUBLIC_ONLY)[0], 'no-private-read');
});

test('read without history is its own posture', () => {
  assert.equal(scopePosture(LIST_ONLY)[0], 'private-list-only');
});

test('a missing header is not read as a missing scope', () => {
  assert.equal(scopePosture('')[0], 'unknown');
  assert.equal(visibilityVerdict('unknown', { ok: true, channels: [] })[0], 'unknown-grant');
});

test('no scope makes the channel absent rather than empty', () => {
  const [state, detail] = visibilityVerdict(
    'no-private-read', { ok: false, error: 'missing_scope' }, 'G01SECRET1');
  assert.equal(state, 'invisible-by-scope');
  assert.match(detail, /declining to confirm/);
});

test('the scope granted with no membership is a different finding', () => {
  const [state, detail] = visibilityVerdict(
    'private-readable', { ok: true, channels: [] }, 'G01SECRET1');
  assert.equal(state, 'scope-without-membership');
  assert.match(detail, /not blanket visibility/);
});

test('a visible private channel passes', () => {
  const [state] = visibilityVerdict(
    'private-readable', { ok: true, channels: [PRIVATE] }, 'G01SECRET1');
  assert.equal(state, 'visible');
});

test('an id outside the visible set is never declared nonexistent', () => {
  const [state, detail] = visibilityVerdict(
    'private-readable', { ok: true, channels: [PRIVATE] }, 'G09OTHER99');
  assert.equal(state, 'outside-the-visible-set');
  assert.match(detail, /two possibilities/);
  assert.match(detail, /no read-only token separates them/);
});

test('an unrelated error is inconclusive not a visibility answer', () => {
  const [state] = visibilityVerdict(
    'private-readable', { ok: false, error: 'ratelimited' }, 'G01SECRET1');
  assert.equal(state, 'inconclusive');
});

test('the two lookalike states get different repairs', () => {
  const scopeFix = repairFor('invisible-by-scope').join(' ');
  const inviteFix = repairFor('scope-without-membership').join(' ');
  assert.match(scopeFix, /reinstall/);
  assert.match(inviteFix, /\\/invite/);
  assert.doesNotMatch(inviteFix, /reinstall/);
});

test('the undecidable state asks a human rather than guessing', () => {
  assert.match(repairFor('outside-the-visible-set').join(' '), /will not say/);
});
''',
"faq": [
 ("Why is the scope called groups:read and not private_channels:read?",
  "Because private channels used to be a separate object type called a group, before the conversations.* family unified them in 2018. The methods were renamed and the scopes were not, so the API you read today talks about private channels while the permission you have to grant talks about groups. Searching the scope list for the word private finds nothing useful, which is most of why this is missed."),
 ("Can I tell whether a private channel ID exists at all?",
  "Not from a read-only token, and not from any token that is not in the channel. Slack returns channel_not_found for a private channel you are not permitted to see, which is the same answer it returns for an ID that never existed. The collapse is deliberate, since a difference between the two would let anyone enumerate private channel IDs. Ask a member instead."),
 ("I added groups:read and conversations.list still returns nothing.",
  "Two things to check, in order. First, did you reinstall? A scope added on the app configuration page does not change the token sitting in your environment until the app is reinstalled and you take the new value. Second, has anybody invited the bot? The scope grants the ability to see private channels the bot belongs to, so with no invitations the correct answer really is an empty list."),
 ("Can the bot invite itself to a private channel?",
  "No. conversations.join works for public channels only, and there is no self-invite path for a private one. A human member has to run /invite @YourApp, or a user token belonging to a member has to call conversations.invite. This is the reason the empty-list finding is worth separating from the missing-scope finding: only one of them is fixed by an engineer."),
 ("A channel that used to work now returns channel_not_found. Same ID.",
  "That is the usual signature of a public channel being converted to private. The ID survives conversion, but the scope that governs it changes from channels:read to groups:read, so a token holding only the public pair loses it from one day to the next with no deploy on your side. The grant check reads the same in both cases; what changed is which side of the boundary the channel is on."),
],
"related": [
 ("/slack/missing-scope-on-read/", "when Slack does name the scope you need"),
 ("/slack/bot-not-in-channel/", "visible, and still not a member"),
 ("/slack/bot-vs-user-scope-mixup/", "the scope landed on the other token"),
],
"citations": [CITE_SCOPES, CITE_CONV_LIST, CITE_CONV_INFO, CITE_AUTH_TEST],
},

{
"slug": "channel-renamed-hardcoded",
"title": "channel_not_found after a rename, or worse, the wrong room",
"description": "Slack channel names are mutable and reusable. A hardcoded name either stops resolving on rename day or starts resolving to a channel nobody chose.",
"h1": "channel_not_found after a rename, or worse, the wrong room",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack channel renamed integration broke", "slack previous_names",
             "slack channel name reused", "slack hardcoded channel name",
             "slack channel_not_found after rename"],
"deps": "Python 3.9+ with requests, or Node.js 18+; previous_names is returned by conversations.info on some plans",
"lead": "An integration that has run untouched for two years stops on a Tuesday. Nothing was deployed, no token expired, no scope changed. What happened is that a team tidied up and renamed <code>#ops-alerts</code> to <code>#platform-alerts</code>. If you are lucky, you get <code>channel_not_found</code> and a page. If you are not, somebody created a new <code>#ops-alerts</code> the following week and your alerts are still being delivered, to strangers.",
"short_answer": """<p>A Slack channel name is a display label. It can be changed by anyone with permission, and when it changes the old name is released and can be claimed by a different channel. The ID never moves. Any configuration that stores the name has stored the field that is designed to change, and the failure arrives on a day nobody deployed anything.</p>
<p>The script below is a drift check rather than a lookup. For each configured entry it resolves the stored value, then asks two questions of the answer: is the channel it resolves to <em>older</em> than this configuration, and has this channel been renamed before? A resolved name pointing at a channel created after your config line was written is the dangerous finding, because nothing is failing &mdash; the messages are landing in a room that happens to be wearing the right name.</p>""",
"problem": """<p>Renames are cheap and social. A team finishes a migration and drops the project prefix, a company rebrands, two channels merge, somebody fixes a typo that has annoyed them for a year. None of these people are thinking about integrations, and Slack gives them no reason to: the rename dialog does not list what points at the channel, because nothing knows.</p>
<p>The visible outcome is the kind one. The name stops resolving, every call returns <code>channel_not_found</code>, alerts stop, and eventually somebody notices and greps for the string. Annoying, findable, over in an hour.</p>
<p>The invisible outcome is the one worth writing a script for. Slack releases a name when it stops being used, so a week or a month later a different team can create a channel with exactly the string in your config. Now the old integration resolves again, returns <code>ok: true</code>, and posts production alerts into a room full of people who have no idea what they are looking at. There is no error anywhere in the system. The only signal that anything is wrong is that the channel your alerts were supposed to reach has been quiet for a month, and quiet channels do not page anybody.</p>
<p>The same drift runs the other way too, more harmlessly. Configuration that stores the ID with a human label beside it &mdash; <code>C01ABCDE9  # #ops-alerts</code> &mdash; keeps delivering correctly forever while the comment slowly becomes fiction, until an on-call engineer follows the runbook to a channel that has not existed under that name in two years.</p>""",
"why": """<p><strong>Names are not unique over time.</strong> They are unique among live channels at any instant, which is a much weaker guarantee than it looks. Storing a name is storing a claim that was true when you wrote it, and nothing in Slack renews that claim on your behalf.</p>
<p><strong>The creation timestamp is the tell.</strong> If the channel a name resolves to was created after the configuration that names it, the name has been recycled onto something new. That comparison needs one field from Slack, <code>channel.created</code>, and one fact you already have &mdash; when that config line was written. It is the only way a read-only script can tell a stable name from a name that quietly moved house.</p>
<p><strong>previous_names is a direct confirmation.</strong> <code>conversations.info</code> returns <code>previous_names</code> on some plans, listing what the channel has been called before. A non-empty list is proof that this channel is a renaming sort of channel, which turns a "correct today" into a "correct today, and it has moved twice already".</p>
<p><strong>Nothing fails, so nothing alerts.</strong> This is the note in the batch where the API is entirely happy. Every other channel problem here produces at least an <code>ok: false</code> somewhere. A recycled name produces a successful send to the wrong audience, which is why the detection has to be scheduled rather than triggered, and why a script has to go looking for it deliberately.</p>
<p><strong>The repair is a data-model change, not a fix.</strong> Editing the config to the new name buys you until the next rename. Storing the ID ends the class of bug: IDs survive renames, survive public-to-private conversion, and are the only channel field Slack promises is stable.</p>""",
"steps": [
 {"h": "Write down when each config line was written",
  "body": """<p>The script wants three fields per entry: the config key, the stored value, and a <code>since</code> timestamp for when that value was set &mdash; the commit date of the line is close enough. Without <code>since</code> the recycled-name check cannot run at all, because the whole comparison is against the age of your own configuration.</p>"""},
 {"h": "Resolve every stored value, IDs included",
  "body": """<p>One paginated <code>conversations.list</code> gives you both indexes: by name for the entries that store a name, by ID for the entries that store an ID with a label. Both halves drift, in opposite directions, and a check that only handles names misses the stale-runbook case entirely.</p>"""},
 {"h": "Compare the creation date against your configuration",
  "body": """<p>A name that resolves to a channel created after your config line is the finding this whole note exists for. Report it first and loudest: it is the only state here where messages are being delivered successfully to the wrong people, and it will not appear in any error budget.</p>"""},
 {"h": "Ask conversations.info what this channel used to be called",
  "body": """<p><code>previous_names</code> turns a suspicion into evidence. A channel with a rename history is one that will be renamed again, and a stored name pointing at it should be replaced now rather than after the next incident. Where the field is absent, say the check was unavailable rather than reporting a clean result.</p>"""},
 {"h": "Rank by silence, not by severity of the error",
  "body": """<p>An outage is loud and already known by the time you run this. A silent misdelivery is neither, so it sorts above the outage in the report. The exit code treats both as failures, but the ordering in the output is what decides which one a person reads first.</p>"""},
 {"h": "Store IDs and let the label drift",
  "body": """<p>Replace every stored name with its ID and keep the name as a comment. Then add a soft assertion at startup: if the current name of the stored ID differs from the label, warn and carry on. A drifted label is a documentation bug and must never take a deploy down &mdash; the traffic was always going to the right room.</p>"""},
],
"verify": """<p>After the configuration stores IDs, every entry should come back pinned, and the one that warns should warn about a comment rather than about delivery.</p>
<pre><code class="language-bash">python3 slack_channel_name_drift.py --config channels.json
# ok        pinned         ALERTS_CHANNEL  an ID with a label that still matches #platform-alerts
# ok        pinned         DIGEST_CHANNEL  an ID with a label that still matches #build-digest
# 2 entry(ies) checked, 0 drifting</code></pre>""",
"code_intro": "The comparison at the heart of this is between a Slack timestamp and a date from your own repository, so <code>drift_verdict</code> takes both and stays pure. <code>severity</code> is the other half of the argument: it ranks a recycled name above an outright outage, because one of them is already known to everybody and the other is not known to anybody. <code>config_line</code> prints the replacement.",
"py_file": "slack_channel_name_drift.py",
"py": '''"""Find Slack channel references that have drifted since they were configured.

Read only. One paginated conversations.list plus one conversations.info per
resolved entry, GET only. Nothing is renamed and nothing is posted: the script
reports the drift and prints the config line that ends it.
"""
import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_channel_name_drift")

API = "https://slack.com/api/"

ID_RE = re.compile(r"^[CG][A-Z0-9]{7,}$")

# A recycled name delivers successfully to the wrong audience, so it outranks an
# outage: the outage is already known to everyone whose alerts stopped, and this
# is known to nobody.
SEVERITY = {
    "name-recycled": "silent-misdelivery",
    "name-gone": "outage",
    "id-unresolved": "outage",
    "rename-prone": "warning",
    "name-unpinned": "warning",
    "label-drifted": "warning",
    "pinned": "ok",
}
RANK = ("silent-misdelivery", "outage", "warning", "ok")


def severity(state):
    """How loudly one drift state deserves to be read. Pure."""
    return SEVERITY.get(state, "warning")


def _epoch(value):
    """ISO-8601 to a Unix timestamp, or None. Pure and tolerant of a trailing Z."""
    if value in (None, ""):
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        stamp = datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.timestamp()


def _day(epoch):
    return datetime.fromtimestamp(float(epoch), timezone.utc).date().isoformat()


def drift_verdict(entry, channel):
    """Compare one configured reference against what it resolves to today. Pure.

    `entry` is {"key", "value", "since", "label"}: the value as stored, and when
    it was stored. `channel` is what it resolves to now, or None. The comparison
    that matters is between Slack's channel.created and the age of your own
    configuration, because a name younger than the config line is a name that was
    released by a rename and claimed by somebody else.
    """
    value = str(entry.get("value") or "").strip()
    label = str(entry.get("label") or "").lstrip("#").strip().lower()
    since = _epoch(entry.get("since"))

    if ID_RE.match(value):
        if channel is None:
            return ("id-unresolved",
                    "the stored ID resolves to nothing this token can see. The "
                    "channel was deleted, or converted to private and the scope "
                    "for it is missing. IDs do not change, so this is not a rename.")
        current = str(channel.get("name") or "").lower()
        if not label:
            return ("pinned",
                    "an ID with no label beside it. Nothing can drift, and nothing "
                    "tells the next reader which room this is either.")
        if label != current:
            return ("label-drifted",
                    "the ID still points at the right room and the label beside it "
                    "says #%s while Slack says #%s. Warn, never fail: the traffic "
                    "is fine and the runbook is wrong." % (label, current))
        return ("pinned", "an ID with a label that still matches #%s" % current)

    if channel is None:
        return ("name-gone",
                "no channel answers to %s any more. It was renamed or deleted, and "
                "every call using this value has failed since the day that "
                "happened." % value)

    created = channel.get("created")
    created = float(created) if isinstance(created, (int, float, str)) and str(created).strip() else None
    if since and created and created > since:
        return ("name-recycled",
                "%s resolves to %s, created %s, which is after this configuration "
                "was written. The name was released by a rename and claimed by a "
                "different channel. Nothing errors: the messages are being "
                "delivered, into a room nobody chose."
                % (value, channel.get("id"), _day(created)))

    previous = [str(n) for n in (channel.get("previous_names") or []) if n]
    if previous:
        return ("rename-prone",
                "%s resolves today, and this channel has already answered to %s. "
                "The name is a moving target that has simply not moved again yet."
                % (value, ", ".join("#" + n for n in previous[:3])))

    return ("name-unpinned",
            "%s resolves to %s and has no recorded rename. Correct today, and one "
            "rename away from either of the findings above."
            % (value, channel.get("id")))


def config_line(entry, channel):
    """The replacement line: ID as the value, name demoted to a comment. Pure."""
    return "%s=%s  # #%s -- store the ID, the name is a label" % (
        entry.get("key"), channel.get("id"), channel.get("name"))


def list_channels(session):
    """Every channel the token can enumerate, archives included. GET only."""
    out, cursor = [], ""
    while True:
        params = {"types": "public_channel,private_channel",
                  "exclude_archived": "false", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "conversations.list", params=params, timeout=30).json()
        if body.get("ok") is not True:
            raise SystemExit("conversations.list answered 200 with ok: false, "
                             "error=%s" % body.get("error"))
        out.extend(body.get("channels") or [])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return out


def with_previous_names(session, channel):
    """conversations.info for previous_names, which the listing does not carry."""
    body = session.get(API + "conversations.info",
                       params={"channel": channel.get("id")}, timeout=30).json()
    if body.get("ok") is not True:
        return channel
    merged = dict(channel)
    merged.update(body.get("channel") or {})
    return merged


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True,
                    help="JSON array of {key, value, since, label} configuration entries")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    args = ap.parse_args()

    entries = json.loads(open(args.config, encoding="utf-8").read())
    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:read and groups:read are enough)", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    channels = list_channels(s)
    by_id = {c.get("id"): c for c in channels}
    by_name = {}
    for c in channels:
        if not c.get("is_archived"):
            by_name.setdefault(str(c.get("name") or "").lower(), c)
    log.info("inventory: %d channel(s) the token can enumerate", len(channels))

    rows = []
    for entry in entries:
        value = str(entry.get("value") or "").strip()
        channel = by_id.get(value) or by_name.get(value.lstrip("#").lower())
        if channel is not None:
            channel = with_previous_names(s, channel)
        state, detail = drift_verdict(entry, channel)
        rows.append((severity(state), state, entry, channel, detail))

    rows.sort(key=lambda r: (RANK.index(r[0]), str(r[2].get("key"))))

    bad = 0
    for level, state, entry, channel, detail in rows:
        line = "%-19s %-15s %-15s %s" % (level, state, entry.get("key"), detail)
        if level == "ok":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if channel is not None:
            log.warning("  repair: %s", config_line(entry, channel))
        else:
            log.warning("  repair: find the channel in Slack, copy its ID from the "
                        "details panel, and store that in %s", entry.get("key"))
        if state == "name-recycled":
            log.warning("  repair: check what has been posted into %s since %s "
                        "before you repoint anything",
                        channel.get("id"), _day(channel.get("created")))

    log.info("%d entry(ies) checked, %d drifting", len(entries), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-channel-name-drift.mjs",
"js": '''/**
 * Find Slack channel references that have drifted since they were configured.
 *
 * Read only. One paginated conversations.list plus one conversations.info per
 * resolved entry, GET only. Nothing is renamed and nothing is posted: the script
 * reports the drift and prints the config line that ends it.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

const ID_RE = /^[CG][A-Z0-9]{7,}$/;

// A recycled name delivers successfully to the wrong audience, so it outranks an
// outage: the outage is already known to everyone whose alerts stopped, and this
// is known to nobody.
const SEVERITY = {
  'name-recycled': 'silent-misdelivery',
  'name-gone': 'outage',
  'id-unresolved': 'outage',
  'rename-prone': 'warning',
  'name-unpinned': 'warning',
  'label-drifted': 'warning',
  pinned: 'ok',
};
const RANK = ['silent-misdelivery', 'outage', 'warning', 'ok'];

/** How loudly one drift state deserves to be read. Pure. */
export function severity(state) {
  return SEVERITY[state] ?? 'warning';
}

function epoch(value) {
  if (value === null || value === undefined || value === '') return null;
  const stamp = Date.parse(String(value));
  return Number.isNaN(stamp) ? null : stamp / 1000;
}

function day(seconds) {
  return new Date(Number(seconds) * 1000).toISOString().slice(0, 10);
}

/**
 * Compare one configured reference against what it resolves to today. Pure.
 * The comparison that matters is between Slack's channel.created and the age of
 * your own configuration: a name younger than the config line is a name that was
 * released by a rename and claimed by somebody else.
 */
export function driftVerdict(entry, channel) {
  const value = String(entry.value ?? '').trim();
  const label = String(entry.label ?? '').replace(/^#+/, '').trim().toLowerCase();
  const since = epoch(entry.since);

  if (ID_RE.test(value)) {
    if (!channel) {
      return ['id-unresolved',
        'the stored ID resolves to nothing this token can see. The channel was ' +
        'deleted, or converted to private and the scope for it is missing. IDs do ' +
        'not change, so this is not a rename.'];
    }
    const current = String(channel.name ?? '').toLowerCase();
    if (!label) {
      return ['pinned',
        'an ID with no label beside it. Nothing can drift, and nothing tells the ' +
        'next reader which room this is either.'];
    }
    if (label !== current) {
      return ['label-drifted',
        `the ID still points at the right room and the label beside it says #${label} ` +
        `while Slack says #${current}. Warn, never fail: the traffic is fine and the ` +
        'runbook is wrong.'];
    }
    return ['pinned', `an ID with a label that still matches #${current}`];
  }

  if (!channel) {
    return ['name-gone',
      `no channel answers to ${value} any more. It was renamed or deleted, and every ` +
      'call using this value has failed since the day that happened.'];
  }

  const created = Number(channel.created);
  if (since && Number.isFinite(created) && created > since) {
    return ['name-recycled',
      `${value} resolves to ${channel.id}, created ${day(created)}, which is after ` +
      'this configuration was written. The name was released by a rename and claimed ' +
      'by a different channel. Nothing errors: the messages are being delivered, into ' +
      'a room nobody chose.'];
  }

  const previous = (channel.previous_names ?? []).filter(Boolean).map(String);
  if (previous.length > 0) {
    return ['rename-prone',
      `${value} resolves today, and this channel has already answered to ` +
      `${previous.slice(0, 3).map((n) => `#${n}`).join(', ')}. The name is a moving ` +
      'target that has simply not moved again yet.'];
  }

  return ['name-unpinned',
    `${value} resolves to ${channel.id} and has no recorded rename. Correct today, ` +
    'and one rename away from either of the findings above.'];
}

/** The replacement line: ID as the value, name demoted to a comment. Pure. */
export function configLine(entry, channel) {
  return `${entry.key}=${channel.id}  # #${channel.name} -- store the ID, the name is a label`;
}

async function get(token, method, params) {
  const res = await fetch(`${API}${method}?${new URLSearchParams(params)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

async function listChannels(token) {
  const out = [];
  let cursor = '';
  for (;;) {
    const params = {
      types: 'public_channel,private_channel',
      exclude_archived: 'false',
      limit: '1000',
    };
    if (cursor) params.cursor = cursor;
    const body = await get(token, 'conversations.list', params);
    if (body.ok !== true) {
      throw new Error(`conversations.list answered 200 with ok: false, error=${body.error}`);
    }
    out.push(...(body.channels ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) return out;
  }
}

async function withPreviousNames(token, channel) {
  const body = await get(token, 'conversations.info', { channel: channel.id });
  if (body.ok !== true) return channel;
  return { ...channel, ...(body.channel ?? {}) };
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const configPath = arg(args, '--config');
  if (!configPath) {
    console.error('usage: --config channels.json [--token-env SLACK_BOT_TOKEN]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:read and groups:read are enough)`);
    process.exitCode = 2;
    return;
  }

  const entries = JSON.parse(await readFile(configPath, 'utf8'));
  const channels = await listChannels(token);
  const byId = new Map(channels.map((c) => [c.id, c]));
  const byName = new Map();
  for (const c of channels) {
    const key = String(c.name ?? '').toLowerCase();
    if (!c.is_archived && !byName.has(key)) byName.set(key, c);
  }
  console.log(`inventory: ${channels.length} channel(s) the token can enumerate`);

  const rows = [];
  for (const entry of entries) {
    const value = String(entry.value ?? '').trim();
    let channel = byId.get(value) ?? byName.get(value.replace(/^#+/, '').toLowerCase()) ?? null;
    if (channel) channel = await withPreviousNames(token, channel);
    const [state, detail] = driftVerdict(entry, channel);
    rows.push([severity(state), state, entry, channel, detail]);
  }

  rows.sort((a, b) => RANK.indexOf(a[0]) - RANK.indexOf(b[0])
    || String(a[2].key).localeCompare(String(b[2].key)));

  let bad = 0;
  for (const [level, state, entry, channel, detail] of rows) {
    const line = `${level.padEnd(19)} ${state.padEnd(15)} ` +
                 `${String(entry.key).padEnd(15)} ${detail}`;
    if (level === 'ok') {
      console.log(line);
      continue;
    }
    bad += 1;
    console.warn(line);
    if (channel) {
      console.warn(`  repair: ${configLine(entry, channel)}`);
    } else {
      console.warn('  repair: find the channel in Slack, copy its ID from the details ' +
                   `panel, and store that in ${entry.key}`);
    }
    if (state === 'name-recycled') {
      console.warn(`  repair: check what has been posted into ${channel.id} since ` +
                   `${day(channel.created)} before you repoint anything`);
    }
  }

  console.log(`${entries.length} entry(ies) checked, ${bad} drifting`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing config.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two entries with identical stored values and identical resolutions have to reach opposite verdicts depending on one number: whether the channel is older or younger than the configuration that names it. That pair is the suite's centre of gravity. The other assertion worth having is on <code>severity</code>, which has to rank the silent misdelivery above the outage &mdash; get that backwards and the report buries the only finding nobody already knows about.",
"test_py_file": "test_slack_channel_name_drift.py",
"test_py": '''from slack_channel_name_drift import config_line, drift_verdict, severity

OLD = {"id": "C01ABCDE9", "name": "ops-alerts", "created": 1600000000}
NEW = {"id": "C07FRESH1", "name": "ops-alerts", "created": 1767225600}
SINCE = "2024-03-01T00:00:00Z"


def test_a_name_that_resolves_to_nothing_is_the_loud_failure():
    state, detail = drift_verdict(
        {"key": "ALERTS", "value": "#ops-alerts", "since": SINCE}, None)
    assert state == "name-gone"
    assert "renamed or deleted" in detail


def test_a_name_on_a_channel_younger_than_the_config_is_the_quiet_one():
    state, detail = drift_verdict(
        {"key": "ALERTS", "value": "#ops-alerts", "since": SINCE}, NEW)
    assert state == "name-recycled"
    assert "2026-01-01" in detail
    assert "nobody chose" in detail


def test_the_same_name_on_an_older_channel_is_not_a_recycling():
    state, _ = drift_verdict(
        {"key": "ALERTS", "value": "#ops-alerts", "since": SINCE}, OLD)
    assert state == "name-unpinned"


def test_a_rename_history_is_reported_even_when_the_name_resolves():
    channel = dict(OLD, previous_names=["ops-alerts-legacy"])
    state, detail = drift_verdict(
        {"key": "ALERTS", "value": "#ops-alerts", "since": SINCE}, channel)
    assert state == "rename-prone"
    assert "#ops-alerts-legacy" in detail


def test_a_missing_since_cannot_produce_a_recycling_verdict():
    state, _ = drift_verdict({"key": "ALERTS", "value": "#ops-alerts"}, NEW)
    assert state == "name-unpinned"


def test_a_stored_id_with_a_stale_label_is_a_warning_not_a_failure():
    entry = {"key": "ALERTS", "value": "C01ABCDE9", "label": "#platform-alerts"}
    state, detail = drift_verdict(entry, OLD)
    assert state == "label-drifted"
    assert "runbook is wrong" in detail
    assert severity(state) == "warning"


def test_a_stored_id_with_a_current_label_is_pinned():
    entry = {"key": "ALERTS", "value": "C01ABCDE9", "label": "ops-alerts"}
    assert drift_verdict(entry, OLD)[0] == "pinned"
    assert severity("pinned") == "ok"


def test_an_id_that_resolves_to_nothing_is_not_called_a_rename():
    entry = {"key": "ALERTS", "value": "C01ABCDE9", "label": "ops-alerts"}
    state, detail = drift_verdict(entry, None)
    assert state == "id-unresolved"
    assert "not a rename" in detail


def test_the_silent_misdelivery_outranks_the_outage():
    assert severity("name-recycled") == "silent-misdelivery"
    assert severity("name-gone") == "outage"


def test_an_unknown_state_is_never_silently_treated_as_healthy():
    assert severity("something-new") == "warning"


def test_the_repair_line_stores_the_id_and_demotes_the_name():
    line = config_line({"key": "ALERTS"}, OLD)
    assert line.startswith("ALERTS=C01ABCDE9")
    assert "#ops-alerts" in line
''',
"test_js_file": "slack-channel-name-drift.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { configLine, driftVerdict, severity } from './slack-channel-name-drift.mjs';

const OLD = { id: 'C01ABCDE9', name: 'ops-alerts', created: 1600000000 };
const NEW = { id: 'C07FRESH1', name: 'ops-alerts', created: 1767225600 };
const SINCE = '2024-03-01T00:00:00Z';

test('a name that resolves to nothing is the loud failure', () => {
  const [state, detail] = driftVerdict(
    { key: 'ALERTS', value: '#ops-alerts', since: SINCE }, null);
  assert.equal(state, 'name-gone');
  assert.match(detail, /renamed or deleted/);
});

test('a name on a channel younger than the config is the quiet one', () => {
  const [state, detail] = driftVerdict(
    { key: 'ALERTS', value: '#ops-alerts', since: SINCE }, NEW);
  assert.equal(state, 'name-recycled');
  assert.match(detail, /2026-01-01/);
  assert.match(detail, /nobody chose/);
});

test('the same name on an older channel is not a recycling', () => {
  const [state] = driftVerdict(
    { key: 'ALERTS', value: '#ops-alerts', since: SINCE }, OLD);
  assert.equal(state, 'name-unpinned');
});

test('a rename history is reported even when the name resolves', () => {
  const channel = { ...OLD, previous_names: ['ops-alerts-legacy'] };
  const [state, detail] = driftVerdict(
    { key: 'ALERTS', value: '#ops-alerts', since: SINCE }, channel);
  assert.equal(state, 'rename-prone');
  assert.match(detail, /#ops-alerts-legacy/);
});

test('a missing since cannot produce a recycling verdict', () => {
  const [state] = driftVerdict({ key: 'ALERTS', value: '#ops-alerts' }, NEW);
  assert.equal(state, 'name-unpinned');
});

test('a stored id with a stale label is a warning not a failure', () => {
  const entry = { key: 'ALERTS', value: 'C01ABCDE9', label: '#platform-alerts' };
  const [state, detail] = driftVerdict(entry, OLD);
  assert.equal(state, 'label-drifted');
  assert.match(detail, /runbook is wrong/);
  assert.equal(severity(state), 'warning');
});

test('a stored id with a current label is pinned', () => {
  const entry = { key: 'ALERTS', value: 'C01ABCDE9', label: 'ops-alerts' };
  assert.equal(driftVerdict(entry, OLD)[0], 'pinned');
  assert.equal(severity('pinned'), 'ok');
});

test('an id that resolves to nothing is not called a rename', () => {
  const entry = { key: 'ALERTS', value: 'C01ABCDE9', label: 'ops-alerts' };
  const [state, detail] = driftVerdict(entry, null);
  assert.equal(state, 'id-unresolved');
  assert.match(detail, /not a rename/);
});

test('the silent misdelivery outranks the outage', () => {
  assert.equal(severity('name-recycled'), 'silent-misdelivery');
  assert.equal(severity('name-gone'), 'outage');
});

test('an unknown state is never silently treated as healthy', () => {
  assert.equal(severity('something-new'), 'warning');
});

test('the repair line stores the id and demotes the name', () => {
  const line = configLine({ key: 'ALERTS' }, OLD);
  assert.ok(line.startsWith('ALERTS=C01ABCDE9'));
  assert.match(line, /#ops-alerts/);
});
''',
"faq": [
 ("How do I know when my config line was written?",
  "git log -1 on the line is close enough, and a single date for the whole file is usually close enough too. The check only needs to distinguish a channel created years before your integration from one created last month, so an approximate since value works. If you genuinely have no date, use the day the service was first deployed and the check stays useful."),
 ("Is previous_names always returned?",
  "It comes back from conversations.info on some plans and not on others, so it is not something to build the only detection on. That is why the script treats it as corroboration rather than as the primary signal: the creation timestamp comparison works everywhere, and previous_names upgrades a suspicion into a confirmed rename history when the field is there."),
 ("Does renaming a channel change its ID?",
  "No. The ID is assigned at creation and never changes, through renames, through a conversion from public to private, and through archiving. That single property is what makes storing the ID the actual fix rather than a workaround. The name is a label attached to the ID, and Slack has never promised it stays put."),
 ("Can somebody really create a new channel with my old channel's name?",
  "Yes, once the original has been renamed or archived and the name is released. It is not a rare edge case either: names are released precisely because they describe something a team wants to keep talking about, so the same string tends to get claimed again. That is the whole mechanism behind the silent misdelivery this note ranks first."),
 ("Should the startup check fail the deploy when a name has drifted?",
  "Only for the states where delivery is affected. A stored ID whose human label is stale is a documentation bug and should warn, because the traffic is going exactly where it should. A stored name that no longer resolves, or that resolves to a channel younger than your configuration, should fail loudly at boot rather than at 3am on the first alert of the incident."),
],
"related": [
 ("/slack/enterprise-id-not-stored/", "storing the identifier that does not move"),
 ("/slack/pagination-not-followed/", "next_cursor and the channels you never saw"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
],
"citations": [CITE_CONV_INFO, CITE_CONV_LIST, CITE_CONV_API, CITE_PAGINATION],
},

]
