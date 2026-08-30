#!/usr/bin/env python3
"""/slack/ field notes, batch I — the writing.

Four notes that all end with "the message did not land", and none of which is
the same note. One is about a channel whose posting rules belong to the
workspace rather than to the channel, and which is not reliably called what you
think it is called. One is about a channel where posting is a permission held
by a named few, and where the flag that would say so is absent on most plans,
so the answer has to be inferred from who has actually spoken. One is not about
permission at all: the post is allowed, in the other position, and the channel's
threading convention is the thing the code assumed. And one is about a channel
where every send succeeds and the audience includes another organisation.

Read-only throughout, and pointedly so: whether an app may post into a channel
is the one question in this section it would be easiest to answer by posting.
None of these do. Every check is an inference from readable state, every repair
is printed for a human to run, and no script here posts, joins, invites or
changes a channel setting.
"""

CITE_CONV_INFO = ("conversations.info method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.info")
CITE_CONV_LIST = ("conversations.list method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.list")
CITE_CONV_HISTORY = ("conversations.history method reference — Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_CONV_REPLIES = ("conversations.replies method reference — Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.replies")
CITE_CONV_MEMBERS = ("conversations.members method reference — Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.members")
CITE_POSTMESSAGE = ("chat.postMessage method reference — Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_WEBHOOKS = ("Sending messages using incoming webhooks — Slack Docs",
                 "https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks")
CITE_RETRIEVING = ("Retrieving messages — Slack Docs",
                   "https://docs.slack.dev/messaging/retrieving-messages")
CITE_USERS_INFO = ("users.info method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.info")
CITE_AUTH_TEST = ("auth.test method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_SCOPES = ("Permission scopes — Slack Docs",
               "https://docs.slack.dev/reference/scopes/")
CITE_GRID = ("Enterprise Grid — Slack Docs",
             "https://docs.slack.dev/enterprise-grid/")

GUIDES = [

{
"slug": "general-channel-restricted",
"title": "posting_to_general_channel_denied: the default channel",
"description": "Only one channel refuses you, and it may not be called general. Find the channel carrying is_general before an integration quietly defaults into it.",
"h1": "posting_to_general_channel_denied: the default channel",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["posting_to_general_channel_denied", "slack restricted_action general",
             "slack is_general channel", "slack webhook 403 general",
             "slack cannot post to general"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Every other channel takes the message. The one that does not is the channel the integration was pointed at on the afternoon somebody wired it up, because it was the channel that already existed and already had everyone in it. The webhook comes back <code>HTTP 403</code> with three words of plain text. <code>chat.postMessage</code> comes back <code>restricted_action</code>. No scope you add will move either of them.</p><p>Neither will renaming anything, and that is the part worth knowing before you start: the channel this is about is not necessarily called <code>#general</code>.",
"short_answer": """<p>A workspace has exactly one default channel, and it is the only channel in Slack whose posting rules live in <strong>workspace</strong> settings rather than in the channel. An admin sets them under Settings &amp; administration, Workspace settings, Permissions, Messaging, and apps are routinely left off the list. A bot token cannot read that preference at all &mdash; there is no method for it, and there is not going to be one.</p>
<p>What a bot token <em>can</em> read is which channel it is. <code>conversations.info</code> and <code>conversations.list</code> both return <code>is_general</code>, and that boolean is the whole detection. It survives the rename that the name does not: the default channel can be called <code>#team-hq</code>, and an ordinary channel can be sitting next to it called <code>#general</code>. The script below finds the channel carrying the flag, reports any configured target that lands on it, and attributes an error you already have in your logs to that policy or to something else entirely.</p>""",
"problem": """<p>Integrations default to the default channel because it is the one room that is guaranteed to exist and guaranteed to contain the audience. A quickstart posts to <code>#general</code>. A Terraform module has it as the fallback. A colleague sets up an alert at four on a Friday and picks the channel everyone is in. None of that is unreasonable, and all of it ages badly: a workspace that grows past a couple of hundred people gets its default channel locked down, which is the correct thing for an admin to do, and the integration nobody remembers is the one that stops.</p>
<p>The refusal then looks different depending on which surface sent the message. <code>chat.postMessage</code> returns the usual <code>HTTP 200</code> with <code>restricted_action</code> in the body &mdash; an error string it shares with per-channel posting restrictions, so it does not identify the cause. An incoming webhook returns a genuine <code>HTTP 403</code> whose body is the plain string <code>posting_to_general_channel_denied</code>, not JSON at all. A client that calls <code>.json()</code> on every response throws a parse error there and the incident report says "malformed response from Slack", which is how a permissions problem gets triaged as a network one.</p>
<p>And then the name. The default channel can be renamed, which releases the string <code>general</code> for anyone to claim, so a workspace can perfectly well have a default channel called <code>#team-hq</code> and an ordinary, entirely unrestricted channel called <code>#general</code>. A configuration audit that greps for the word gets that backwards in both directions at once: it flags the harmless channel and misses the restricted one.</p>""",
"why": """<p><strong>The policy is not in the API, and the channel is.</strong> No read method returns "who may post in the default channel", so no script can tell you whether this app is on the list. What every script can tell you is that a target carries <code>is_general</code>, which is a warning worth raising on its own, because the restriction is the normal end state for that channel rather than an unusual one.</p>
<p><strong><code>is_general</code> is the stable handle; the name is not.</strong> The flag is set at workspace creation and follows the channel through renames. Anything that identifies the default channel by its name is identifying a label that a workspace admin can move in ten seconds and that a different channel can then adopt.</p>
<p><strong>There can be more than one.</strong> <code>is_general</code> is a per-workspace property. An org-wide token on Enterprise Grid enumerates channels across several workspaces, so the honest answer to "which one is the default" is a list, and a script that takes the first match is right only until the second workspace is added.</p>
<p><strong>The audience is the reason it is locked, so asking for an exception rarely works.</strong> The default channel contains every member of the workspace and cannot be narrowed. A restriction on it is an audience decision, not a security one, and the argument "our bot is fine" does not engage with it. Moving the integration to a purpose-built channel is both the faster repair and the better one.</p>
<p><strong>Bare <code>restricted_action</code> is ambiguous, and <code>is_general</code> disambiguates it.</strong> The same string comes back from a per-channel posting restriction, which is a different admin screen and a different note. Attributing it correctly is the difference between emailing a workspace admin and asking a channel owner.</p>""",
"steps": [
 {"h": "Find the default channel instead of assuming its name",
  "body": """<p>One paginated <code>conversations.list</code>, then filter on <code>is_general</code>. This is the only step that has to happen before anything else, because every later verdict is measured against the answer. Keep the result as a list: an org-wide Grid token will return one per workspace.</p>"""},
 {"h": "Resolve targets by ID first, then by name",
  "body": """<p>Configuration holds both, and the check has to work on either or it will not get run. Resolving by ID is exact; resolving by name is what surfaces the interesting case, where the string in the config and the channel carrying the flag are two different rooms.</p>"""},
 {"h": "Count the audience you would have been posting to",
  "body": """<p><code>conversations.info</code> with <code>include_num_members=true</code>. It costs one call and it changes the conversation: "this posts to all 812 people in the workspace" is an argument a reader acts on, where "this targets the default channel" is a line in a report.</p>"""},
 {"h": "Attribute the refusal you already recorded, offline",
  "body": """<p>The script takes the error your integration logged and says what it means. It does not send a message to find out, and neither should you: discovering whether you may post by posting is the one experiment in this section that puts a message in front of a few hundred people to answer a question a boolean already answered.</p>"""},
 {"h": "Move the integration rather than the policy",
  "body": """<p>The script prints both repairs and puts them in that order deliberately. A purpose-built channel is a change you can make today and it improves the alerting regardless. Relaxing the workspace restriction needs an admin, needs a reason, and widens who may post in the room that reaches everybody.</p>"""},
 {"h": "Assert the flag at boot",
  "body": """<p>Add <code>is_general</code> to the same startup check that already validates the token, and refuse to start when a send target carries it. That turns a class of misconfiguration into a deploy-time failure, which is the only time anybody is looking.</p>"""},
],
"verify": """<p>Re-run against the repointed configuration. Every target should come back ordinary, with a member count that is visibly smaller than the workspace.</p>
<pre><code class="language-bash">python3 slack_general_channel_target.py C0ALERTS99 C0DEPLOY11
# default channel  C0TEAMHQ11  #team-hq  812 member(s)
# ordinary         C0ALERTS99  #alerts is not the workspace default, 34 member(s)
# ordinary         C0DEPLOY11  #deploys is not the workspace default, 12 member(s)
# 2 target(s) checked, 0 on or confusable with the workspace default</code></pre>""",
"code_intro": "Three pure functions and two GET methods. <code>default_channels</code> returns a list rather than a channel, because the flag is per workspace and a Grid token sees several. <code>target_verdict</code> sorts one configured target against that list and keeps the <code>#general</code>-that-is-not-the-default case in a bucket of its own. <code>attribute_refusal</code> is completely offline: it reads an error you already have, which is how this script answers a question about posting without posting.",
"py_file": "slack_general_channel_target.py",
"py": '''"""Find the integration targets that point at the workspace default channel.

Read only. One paginated conversations.list finds the channel carrying
is_general, one conversations.info per target adds the size of the audience.
Nothing is sent: who may post in the default channel is a workspace preference
no bot token can read, so this reports which target lands on that channel and
prints the admin path that would have to change if it stays there.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_general_channel_target")

API = "https://slack.com/api/"

# Refusals an integration writes to its log. Only the first belongs exclusively
# to the default channel policy. The restricted_action family is a per-channel
# posting permission wearing nearly the same words, and the rest are not posting
# policy at all.
REFUSALS = {
    "posting_to_general_channel_denied": (
        "default-channel-policy",
        "the workspace restricts who may post in its default channel and this app "
        "is not on the list. Incoming webhooks return it as a real HTTP 403 with a "
        "plain-text body rather than JSON, so a client that parses every response "
        "will report it as a transport failure."),
    "restricted_action": (
        "ambiguous-policy",
        "returned both by the default-channel restriction and by a per-channel "
        "posting restriction. Whether the target carries is_general is what "
        "decides which admin screen this is about."),
    "restricted_action_read_only_channel": (
        "channel-policy",
        "a per-channel posting restriction, not the default-channel one. The "
        "repair is a channel setting and a channel owner."),
    "restricted_action_thread_only_channel": (
        "channel-policy",
        "the channel accepts replies and refuses top-level posts. Nothing to do "
        "with the default channel, and nothing to do with scopes either."),
    "restricted_action_non_threadable_channel": (
        "channel-policy",
        "the channel refuses threaded replies. A posting-mode mismatch rather "
        "than a permission."),
    "restricted_action_thread_locked": (
        "channel-policy",
        "one thread was locked. The channel itself is still writable."),
    "not_in_channel": (
        "membership",
        "the app is not a member. That is a membership finding and it applies to "
        "any channel, default or not."),
    "is_archived": (
        "channel-state",
        "the channel is frozen. It refuses everyone, including workspace owners."),
    "channel_not_found": (
        "visibility",
        "the ID did not resolve for this token. Slack will not say whether that "
        "is a wrong ID or a channel the token may not know about."),
    "missing_scope": (
        "scopes",
        "a grant problem, and the only one on this list a reinstall fixes."),
}

REPAIR_MOVE = ("point the integration at a purpose-built channel; the default "
               "channel is every person in the workspace and cannot be narrowed")
REPAIR_POLICY = ("if it has to stay, an admin opens Settings and administration, "
                 "Workspace settings, Permissions, Messaging, and adds apps to the "
                 "people who may post in the default channel")


def default_channels(channels):
    """Every channel carrying is_general. Pure, and a list on purpose.

    is_general is a per-workspace property. An org-wide Enterprise Grid token
    enumerates several workspaces in one sweep, so there is genuinely more than
    one answer, and none of them has to be named "general": the default channel
    can be renamed, after which any channel may claim the name it released.
    """
    return [c for c in channels if c.get("is_general") is True]


def target_verdict(target, channels):
    """Sort one configured target against the workspace default. Pure.

    Accepts an ID or a name because configuration holds both, and because the
    name is exactly the thing that cannot be trusted here. Returns
    (verdict, channel, detail).
    """
    wanted = str(target or "").strip()
    if not wanted:
        return ("unresolved", None,
                "an empty target. Something upstream resolved to nothing and the "
                "send will fail before any policy is consulted.")

    key = wanted.lstrip("#").lower()
    hit = next((c for c in channels if str(c.get("id") or "") == wanted), None)
    if hit is None:
        hit = next((c for c in channels
                    if str(c.get("name") or "").lower() == key), None)
    if hit is None:
        return ("unresolved", None,
                "nothing in the sweep answers to %s, so this check cannot say "
                "whether it is the default channel. Resolve the reference first."
                % wanted)

    name = str(hit.get("name") or "?")
    if hit.get("is_general") is True:
        return ("default-channel", hit,
                "#%s carries is_general. It is the workspace default channel, it "
                "holds every member of the workspace, and who may post in it is a "
                "workspace preference this token cannot read." % name)

    if key == "general" or name.lower() == "general":
        others = default_channels(channels)
        instead = ("#" + str(others[0].get("name"))) if others else "a channel this token cannot see"
        return ("general-by-name-only", hit,
                "#general here is an ordinary channel: the workspace default is "
                "%s. The default-channel restriction does not apply to this one, "
                "and an audit that greps configuration for the word general gets "
                "both channels backwards at once." % instead)

    return ("ordinary", hit, "#%s is not the workspace default" % name)


def attribute_refusal(error, status=None):
    """Attribute a refusal the integration already recorded. Pure and offline.

    This script never sends a message, so it cannot produce one of these itself.
    Finding out whether you may post by posting is the experiment that puts a
    test message in front of everybody in the workspace to learn what one boolean
    already told you.
    """
    text = str(error or "").strip()
    if status == 403 and "general" in text.lower():
        text = "posting_to_general_channel_denied"

    known = REFUSALS.get(text)
    if known is not None:
        return known
    if text.startswith("restricted_action"):
        return ("channel-policy",
                "an unfamiliar restricted_action variant. Every member of that "
                "family is a posting policy rather than a grant, so no scope "
                "change and no reinstall will move it.")
    if not text:
        return ("none-recorded",
                "no error was supplied, so nothing was attributed. The structural "
                "finding above stands on its own.")
    return ("unattributed",
            "%s is not a posting restriction. Whatever stopped the message, the "
            "default channel policy is not it." % text)


def sweep(session):
    """Every channel the token can enumerate. GET only, cursor paginated."""
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


def member_count(session, cid):
    """How many people the message would reach. GET only, best effort."""
    body = session.get(API + "conversations.info",
                       params={"channel": cid, "include_num_members": "true"},
                       timeout=30).json()
    if body.get("ok") is not True:
        return "?"
    return (body.get("channel") or {}).get("num_members", "?")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("targets", nargs="+",
                    help="channel IDs or names the integration posts to")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--observed-error", default="",
                    help="an error the integration already logged, attributed offline")
    ap.add_argument("--observed-status", type=int, default=0,
                    help="the HTTP status that came with it, if a webhook sent it")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:read and groups:read are enough)", args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    channels = sweep(s)
    defaults = default_channels(channels)
    if not defaults:
        log.warning("no channel in the sweep carries is_general, so this token "
                    "cannot see the workspace default. Every verdict below is "
                    "limited to the channels it can enumerate")
    for d in defaults:
        log.info("default channel  %-12s #%-18s %s member(s)", d.get("id"),
                 d.get("name"), member_count(s, d.get("id")))

    hits = 0
    for target in args.targets:
        verdict, channel, detail = target_verdict(target, channels)
        if verdict == "ordinary":
            log.info("%-20s %-12s %s, %s member(s)", verdict, channel.get("id"),
                     detail, member_count(s, channel.get("id")))
            continue

        hits += 1
        cid = (channel or {}).get("id") or target
        log.warning("%-20s %-12s %s", verdict, cid, detail)
        if verdict == "default-channel":
            log.warning("  reaches: %s member(s), which is the whole workspace",
                        member_count(s, cid))
            log.warning("  repair: %s", REPAIR_MOVE)
            log.warning("  repair: %s", REPAIR_POLICY)
        elif verdict == "general-by-name-only":
            log.warning("  repair: store %s as the ID and stop matching on the "
                        "name; the two questions have drifted apart in this "
                        "workspace", cid)
        else:
            log.warning("  repair: resolve the reference to a channel ID first, "
                        "then re-run this check")

    if args.observed_error or args.observed_status:
        source, why = attribute_refusal(args.observed_error,
                                        args.observed_status or None)
        log.warning("recorded refusal  %-22s %s", source, why)

    log.info("%d target(s) checked, %d on or confusable with the workspace default",
             len(args.targets), hits)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-general-channel-target.mjs",
"js": '''/**
 * Find the integration targets that point at the workspace default channel.
 *
 * Read only. One paginated conversations.list finds the channel carrying
 * is_general, one conversations.info per target adds the size of the audience.
 * Nothing is sent: who may post in the default channel is a workspace
 * preference no bot token can read, so this reports which target lands on that
 * channel and prints the admin path that would have to change.
 */

const API = 'https://slack.com/api/';

// Refusals an integration writes to its log. Only the first belongs exclusively
// to the default channel policy. The restricted_action family is a per-channel
// posting permission wearing nearly the same words.
const REFUSALS = new Map([
  ['posting_to_general_channel_denied', ['default-channel-policy',
    'the workspace restricts who may post in its default channel and this app is ' +
    'not on the list. Incoming webhooks return it as a real HTTP 403 with a ' +
    'plain-text body rather than JSON, so a client that parses every response ' +
    'will report it as a transport failure.']],
  ['restricted_action', ['ambiguous-policy',
    'returned both by the default-channel restriction and by a per-channel ' +
    'posting restriction. Whether the target carries is_general is what decides ' +
    'which admin screen this is about.']],
  ['restricted_action_read_only_channel', ['channel-policy',
    'a per-channel posting restriction, not the default-channel one. The repair ' +
    'is a channel setting and a channel owner.']],
  ['restricted_action_thread_only_channel', ['channel-policy',
    'the channel accepts replies and refuses top-level posts. Nothing to do with ' +
    'the default channel, and nothing to do with scopes either.']],
  ['restricted_action_non_threadable_channel', ['channel-policy',
    'the channel refuses threaded replies. A posting-mode mismatch rather than a ' +
    'permission.']],
  ['restricted_action_thread_locked', ['channel-policy',
    'one thread was locked. The channel itself is still writable.']],
  ['not_in_channel', ['membership',
    'the app is not a member. That is a membership finding and it applies to any ' +
    'channel, default or not.']],
  ['is_archived', ['channel-state',
    'the channel is frozen. It refuses everyone, including workspace owners.']],
  ['channel_not_found', ['visibility',
    'the ID did not resolve for this token. Slack will not say whether that is a ' +
    'wrong ID or a channel the token may not know about.']],
  ['missing_scope', ['scopes',
    'a grant problem, and the only one on this list a reinstall fixes.']],
]);

const REPAIR_MOVE = 'point the integration at a purpose-built channel; the ' +
  'default channel is every person in the workspace and cannot be narrowed';
const REPAIR_POLICY = 'if it has to stay, an admin opens Settings and ' +
  'administration, Workspace settings, Permissions, Messaging, and adds apps to ' +
  'the people who may post in the default channel';

/**
 * Every channel carrying is_general. Pure, and a list on purpose: the flag is
 * per workspace and an org-wide Grid token enumerates several at once.
 */
export function defaultChannels(channels) {
  return channels.filter((c) => c.is_general === true);
}

/**
 * Sort one configured target against the workspace default. Pure.
 * Accepts an ID or a name, because the name is exactly the thing that cannot be
 * trusted here.
 */
export function targetVerdict(target, channels) {
  const wanted = String(target ?? '').trim();
  if (!wanted) {
    return ['unresolved', null,
      'an empty target. Something upstream resolved to nothing and the send will ' +
      'fail before any policy is consulted.'];
  }

  const key = wanted.replace(/^#+/, '').toLowerCase();
  let hit = channels.find((c) => String(c.id ?? '') === wanted) ?? null;
  if (hit === null) {
    hit = channels.find((c) => String(c.name ?? '').toLowerCase() === key) ?? null;
  }
  if (hit === null) {
    return ['unresolved', null,
      `nothing in the sweep answers to ${wanted}, so this check cannot say whether ` +
      'it is the default channel. Resolve the reference first.'];
  }

  const name = String(hit.name ?? '?');
  if (hit.is_general === true) {
    return ['default-channel', hit,
      `#${name} carries is_general. It is the workspace default channel, it holds ` +
      'every member of the workspace, and who may post in it is a workspace ' +
      'preference this token cannot read.'];
  }

  if (key === 'general' || name.toLowerCase() === 'general') {
    const others = defaultChannels(channels);
    const instead = others.length > 0
      ? `#${others[0].name}` : 'a channel this token cannot see';
    return ['general-by-name-only', hit,
      `#general here is an ordinary channel: the workspace default is ${instead}. ` +
      'The default-channel restriction does not apply to this one, and an audit ' +
      'that greps configuration for the word general gets both channels backwards ' +
      'at once.'];
  }

  return ['ordinary', hit, `#${name} is not the workspace default`];
}

/**
 * Attribute a refusal the integration already recorded. Pure and offline.
 * This script never sends a message, so it cannot produce one of these itself.
 */
export function attributeRefusal(error, status = null) {
  let text = String(error ?? '').trim();
  if (status === 403 && text.toLowerCase().includes('general')) {
    text = 'posting_to_general_channel_denied';
  }

  const known = REFUSALS.get(text);
  if (known !== undefined) return known;
  if (text.startsWith('restricted_action')) {
    return ['channel-policy',
      'an unfamiliar restricted_action variant. Every member of that family is a ' +
      'posting policy rather than a grant, so no scope change and no reinstall ' +
      'will move it.'];
  }
  if (!text) {
    return ['none-recorded',
      'no error was supplied, so nothing was attributed. The structural finding ' +
      'above stands on its own.'];
  }
  return ['unattributed',
    `${text} is not a posting restriction. Whatever stopped the message, the ` +
    'default channel policy is not it.'];
}

async function sweep(token) {
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

async function memberCount(token, cid) {
  const params = new URLSearchParams({ channel: cid, include_num_members: 'true' });
  const res = await fetch(`${API}conversations.info?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  if (body.ok !== true) return '?';
  return body.channel?.num_members ?? '?';
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

/** Everything that is not a flag and not the value of one. */
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
  const targets = positionals(args);
  if (targets.length === 0) {
    console.error('usage: <channel id or name>... [--token-env SLACK_BOT_TOKEN] ' +
      '[--observed-error restricted_action] [--observed-status 403]');
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

  const channels = await sweep(token);
  const defaults = defaultChannels(channels);
  if (defaults.length === 0) {
    console.warn('no channel in the sweep carries is_general, so this token cannot ' +
      'see the workspace default. Every verdict below is limited to the channels ' +
      'it can enumerate');
  }
  for (const d of defaults) {
    console.log(`default channel  ${String(d.id).padEnd(12)} ` +
      `#${String(d.name).padEnd(18)} ${await memberCount(token, d.id)} member(s)`);
  }

  let hits = 0;
  for (const target of targets) {
    const [verdict, channel, detail] = targetVerdict(target, channels);
    if (verdict === 'ordinary') {
      console.log(`${verdict.padEnd(20)} ${String(channel.id).padEnd(12)} ${detail}, ` +
        `${await memberCount(token, channel.id)} member(s)`);
      continue;
    }

    hits += 1;
    const cid = channel?.id ?? target;
    console.warn(`${verdict.padEnd(20)} ${String(cid).padEnd(12)} ${detail}`);
    if (verdict === 'default-channel') {
      console.warn(`  reaches: ${await memberCount(token, cid)} member(s), which is ` +
        'the whole workspace');
      console.warn(`  repair: ${REPAIR_MOVE}`);
      console.warn(`  repair: ${REPAIR_POLICY}`);
    } else if (verdict === 'general-by-name-only') {
      console.warn(`  repair: store ${cid} as the ID and stop matching on the name; ` +
        'the two questions have drifted apart in this workspace');
    } else {
      console.warn('  repair: resolve the reference to a channel ID first, then ' +
        're-run this check');
    }
  }

  const observedError = arg(args, '--observed-error', '');
  const observedStatus = Number(arg(args, '--observed-status', 0));
  if (observedError || observedStatus) {
    const [source, why] = attributeRefusal(observedError, observedStatus || null);
    console.warn(`recorded refusal  ${source.padEnd(22)} ${why}`);
  }

  console.log(`${targets.length} target(s) checked, ${hits} on or confusable with ` +
    'the workspace default');
  process.exitCode = hits ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two fixtures carry the whole point: a default channel named <code>#team-hq</code> and an ordinary channel named <code>#general</code>, in the same workspace, which is the arrangement every name-based check gets wrong. The tests pin that <code>target_verdict</code> flags the first and explicitly clears the second, that <code>default_channels</code> returns both entries when a Grid sweep contains two workspaces, and that a bare <code>restricted_action</code> is reported as ambiguous rather than confidently attributed to the default channel.",
"test_py_file": "test_slack_general_channel_target.py",
"test_py": '''from slack_general_channel_target import (attribute_refusal, default_channels,
                                            target_verdict)

# The arrangement that defeats every name-based check: the default channel was
# renamed and an ordinary channel picked up the name it released.
DEFAULT = {"id": "C0TEAMHQ11", "name": "team-hq", "is_general": True}
DECOY = {"id": "C0GENERAL1", "name": "general", "is_general": False}
ALERTS = {"id": "C0ALERTS99", "name": "alerts", "is_general": False}
WORKSPACE = [DEFAULT, DECOY, ALERTS]


def test_the_default_channel_is_found_by_its_flag_not_its_name():
    assert default_channels(WORKSPACE) == [DEFAULT]


def test_a_grid_sweep_can_hold_more_than_one_default_channel():
    other = {"id": "C0SECOND11", "name": "general", "is_general": True}
    assert default_channels(WORKSPACE + [other]) == [DEFAULT, other]


def test_targeting_the_default_channel_by_id_is_the_headline_finding():
    verdict, channel, detail = target_verdict("C0TEAMHQ11", WORKSPACE)
    assert verdict == "default-channel"
    assert channel["id"] == "C0TEAMHQ11"
    assert "is_general" in detail


def test_targeting_the_default_channel_by_name_reaches_the_same_verdict():
    assert target_verdict("#team-hq", WORKSPACE)[0] == "default-channel"


def test_a_channel_called_general_that_is_not_the_default_is_cleared():
    verdict, channel, detail = target_verdict("#general", WORKSPACE)
    assert verdict == "general-by-name-only"
    assert channel["id"] == "C0GENERAL1"
    assert "#team-hq" in detail


def test_an_ordinary_channel_is_ordinary():
    verdict, channel, _ = target_verdict("C0ALERTS99", WORKSPACE)
    assert verdict == "ordinary"
    assert channel["name"] == "alerts"


def test_a_target_that_does_not_resolve_is_not_guessed_at():
    verdict, channel, _ = target_verdict("C0NOTHERE1", WORKSPACE)
    assert verdict == "unresolved"
    assert channel is None
    assert target_verdict("", WORKSPACE)[0] == "unresolved"


def test_the_webhook_403_is_attributed_to_the_default_channel_policy():
    source, why = attribute_refusal("posting_to_general_channel_denied", 403)
    assert source == "default-channel-policy"
    assert "403" in why


def test_a_plain_text_403_body_is_recognised_even_when_it_is_not_the_error_name():
    source, _ = attribute_refusal("posting to general channel denied", 403)
    assert source == "default-channel-policy"


def test_bare_restricted_action_is_reported_as_ambiguous():
    source, why = attribute_refusal("restricted_action")
    assert source == "ambiguous-policy"
    assert "is_general" in why


def test_the_read_only_variant_belongs_to_a_different_note():
    assert attribute_refusal("restricted_action_read_only_channel")[0] == "channel-policy"
    assert attribute_refusal("restricted_action_invented_variant")[0] == "channel-policy"


def test_a_membership_error_is_never_dressed_up_as_a_policy():
    assert attribute_refusal("not_in_channel")[0] == "membership"
    assert attribute_refusal("missing_scope")[0] == "scopes"
    assert attribute_refusal("timeout")[0] == "unattributed"
    assert attribute_refusal("")[0] == "none-recorded"
''',
"test_js_file": "slack-general-channel-target.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { attributeRefusal, defaultChannels, targetVerdict }
  from './slack-general-channel-target.mjs';

// The arrangement that defeats every name-based check: the default channel was
// renamed and an ordinary channel picked up the name it released.
const DEFAULT = { id: 'C0TEAMHQ11', name: 'team-hq', is_general: true };
const DECOY = { id: 'C0GENERAL1', name: 'general', is_general: false };
const ALERTS = { id: 'C0ALERTS99', name: 'alerts', is_general: false };
const WORKSPACE = [DEFAULT, DECOY, ALERTS];

test('the default channel is found by its flag not its name', () => {
  assert.deepEqual(defaultChannels(WORKSPACE), [DEFAULT]);
});

test('a grid sweep can hold more than one default channel', () => {
  const other = { id: 'C0SECOND11', name: 'general', is_general: true };
  assert.deepEqual(defaultChannels([...WORKSPACE, other]), [DEFAULT, other]);
});

test('targeting the default channel by id is the headline finding', () => {
  const [verdict, channel, detail] = targetVerdict('C0TEAMHQ11', WORKSPACE);
  assert.equal(verdict, 'default-channel');
  assert.equal(channel.id, 'C0TEAMHQ11');
  assert.match(detail, /is_general/);
});

test('targeting the default channel by name reaches the same verdict', () => {
  assert.equal(targetVerdict('#team-hq', WORKSPACE)[0], 'default-channel');
});

test('a channel called general that is not the default is cleared', () => {
  const [verdict, channel, detail] = targetVerdict('#general', WORKSPACE);
  assert.equal(verdict, 'general-by-name-only');
  assert.equal(channel.id, 'C0GENERAL1');
  assert.match(detail, /#team-hq/);
});

test('an ordinary channel is ordinary', () => {
  const [verdict, channel] = targetVerdict('C0ALERTS99', WORKSPACE);
  assert.equal(verdict, 'ordinary');
  assert.equal(channel.name, 'alerts');
});

test('a target that does not resolve is not guessed at', () => {
  const [verdict, channel] = targetVerdict('C0NOTHERE1', WORKSPACE);
  assert.equal(verdict, 'unresolved');
  assert.equal(channel, null);
  assert.equal(targetVerdict('', WORKSPACE)[0], 'unresolved');
});

test('the webhook 403 is attributed to the default channel policy', () => {
  const [source, why] = attributeRefusal('posting_to_general_channel_denied', 403);
  assert.equal(source, 'default-channel-policy');
  assert.match(why, /403/);
});

test('a plain text 403 body is recognised even when it is not the error name', () => {
  assert.equal(attributeRefusal('posting to general channel denied', 403)[0],
    'default-channel-policy');
});

test('bare restricted_action is reported as ambiguous', () => {
  const [source, why] = attributeRefusal('restricted_action');
  assert.equal(source, 'ambiguous-policy');
  assert.match(why, /is_general/);
});

test('the read only variant belongs to a different note', () => {
  assert.equal(attributeRefusal('restricted_action_read_only_channel')[0],
    'channel-policy');
  assert.equal(attributeRefusal('restricted_action_invented_variant')[0],
    'channel-policy');
});

test('a membership error is never dressed up as a policy', () => {
  assert.equal(attributeRefusal('not_in_channel')[0], 'membership');
  assert.equal(attributeRefusal('missing_scope')[0], 'scopes');
  assert.equal(attributeRefusal('timeout')[0], 'unattributed');
  assert.equal(attributeRefusal('')[0], 'none-recorded');
});
''',
"faq": [
 ("Can a bot token read who is allowed to post in the default channel?",
  "No. It is a workspace preference, it lives in the admin console, and there is no read method that returns it. That is why this check is structural rather than conclusive: it tells you a target carries is_general, which is the channel most likely to be restricted and the channel with the largest possible audience, and it leaves the certainty to the error your integration already recorded."),
 ("Why does the webhook return 403 when chat.postMessage returns 200?",
  "Incoming webhooks are one of the few Slack surfaces that use real HTTP status codes, and they return a plain-text body rather than JSON. So the same restriction produces a 403 with the string posting_to_general_channel_denied through a webhook and an HTTP 200 carrying restricted_action through the Web API. Clients that assume JSON on every response tend to misreport the webhook case as a transport error."),
 ("Our default channel is not called #general. Does any of this still apply?",
  "All of it, and more so. The restriction follows the is_general flag, not the name, so a renamed default channel is restricted exactly as before while every name-based check in your codebase stops finding it. The reverse case is just as common: a new channel claims the released name #general and gets flagged by audits that it has nothing to do with."),
 ("Should the script just try posting to find out?",
  "No, and it is worth being explicit about why. A test post to the default channel is a message delivered to every person in the workspace, and it answers a question that conversations.info answers for free. Every script in this section holds a token that could post and none of them do; this is the note where that rule earns itself."),
 ("What should an integration post to instead?",
  "A channel created for it, with the people who care about the alerts in it. That is a better outcome than an exception in the workspace posting policy even when the exception is easy to get: the default channel cannot be narrowed, so anything sent there is sent to everybody, and alert fatigue in the channel that reaches the whole company is its own incident."),
],
"related": [
 ("/slack/read-only-channel/", "the same words, a per-channel restriction"),
 ("/slack/archived-channel-target/", "another channel that resolves and refuses"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
],
"citations": [CITE_CONV_INFO, CITE_CONV_LIST, CITE_POSTMESSAGE, CITE_WEBHOOKS],
},

{
"slug": "read-only-channel",
"title": "restricted_action_read_only_channel: the channel is locked",
"description": "A member with chat:write, refused anyway. is_read_only is absent on most plans, so read who has actually posted instead of trusting a missing flag.",
"h1": "restricted_action_read_only_channel: the channel is locked",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["restricted_action_read_only_channel", "slack read only channel bot",
             "slack posting permissions channel", "slack is_read_only",
             "slack announcement channel app"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the inference needs channels:history",
"lead": "The bot is a member: <code>is_member</code> is true and you have checked it twice. The token holds <code>chat:write</code> and the grant screen agrees. The channel is not archived, not private, not the workspace default. The message is still refused, and the error names something that is not in the OAuth screen at all.</p><p>Nothing about this app is wrong. Somebody decided who may speak in that room, and the app was not on the list.",
"short_answer": """<p><code>restricted_action_read_only_channel</code> means the channel has a posting permission and this app does not satisfy it. Paid workspaces and Enterprise Grid let a channel manager restrict posting to a named set of members &mdash; the announcement-channel arrangement, where everyone reads and three people write. Membership and scopes are both irrelevant to it, which is why every scope-shaped investigation of this error ends in confusion.</p>
<p>The awkward part is detection. <code>conversations.info</code> returns <code>is_read_only</code> only on the plans that expose it, so the field is usually <em>absent</em>, and absent is not <code>false</code>. The script below reports the presence of the flag separately from its value, then infers the rest from readable history: how many distinct people have actually posted, against how many members the channel has, and whether this app's own user ID is among the authors. That last one is the strongest evidence a read-only check can produce &mdash; it posted here once, so it was permitted to.</p>""",
"problem": """<p>This error arrives in an investigation that has already ruled out everything it knows how to rule out. Membership: checked. Scopes: checked, and the app has <code>chat:write</code>, which is the scope whose name promises exactly this. Channel state: not archived. So the next move is usually to add scopes, then to reinstall, then to create a second app, and none of those does anything, because a posting permission is not a grant. It is a property of the channel, set by a person, in a menu no OAuth screen mentions.</p>
<p>The variants make it worse rather than better. <code>restricted_action_read_only_channel</code> is explicit. Bare <code>restricted_action</code> is not, and is shared with the workspace default-channel policy. <code>restricted_action_thread_locked</code> means one thread was closed while the channel is perfectly writable. An integration that logs the error string and nothing else has already lost the distinction that decides who you go and talk to.</p>
<p>And the flag that ought to settle it usually is not there. On the plans where <code>is_read_only</code> is returned, it covers the whole-channel lock. On the plans where it is not returned, the very common Python line <code>channel.get("is_read_only")</code> yields <code>None</code>, which is falsey, which means the check reports "writable" for every locked channel in the workspace with total confidence. The one thing a detector must not do here is treat a missing field as a negative answer.</p>""",
"why": """<p><strong>Posting permission is not a scope, so no reinstall touches it.</strong> <code>chat:write</code> authorises the app to use <code>chat.postMessage</code>. Whether a particular channel accepts the resulting message is decided after that, by channel settings. The two questions look like one question in the error message and they are answered by two different people.</p>
<p><strong>Absent is not false.</strong> The single most important line of code in this note is the one that asks whether <code>is_read_only</code> is <em>present</em> before asking what it says. Reporting "the flag was not returned by this plan" is a useful, honest finding. Reporting "writable" on the strength of a missing key is a confident wrong answer, which is worse than no answer.</p>
<p><strong>A restriction on some members is invisible even where the flag exists.</strong> <code>is_read_only</code> describes a channel nobody may post in. The far more common arrangement &mdash; posting allowed for a named group &mdash; sets no field a bot token can read. So the honest detection is an inference from behaviour, and it has to be labelled as an inference.</p>
<p><strong>Who has spoken is readable, and it is the best proxy there is.</strong> A channel with 900 members where four accounts have posted the last hundred messages is shaped like a restricted channel. It is also shaped like a channel nobody uses, and the script says so rather than pretending the two are distinguishable from here.</p>
<p><strong>Your own past message is the closest thing to proof.</strong> If this app's user ID appears among the authors of the readable history, it was allowed to post here at least once, without anybody having to send a test message to find out. It is evidence about the past: a permission changed this morning shows up in the next failed send, not in the history.</p>""",
"steps": [
 {"h": "Establish who you are before asking what you may do",
  "body": """<p>One <code>auth.test</code> gives the bot's own user ID. Everything downstream needs it, and it is the call that turns "somebody posted" into "we posted", which is the difference between a shape and a fact.</p>"""},
 {"h": "Ask whether the flag exists, then what it says",
  "body": """<p>Two questions, in that order, and reported as two lines. <code>not-exposed</code>, <code>declared-read-only</code> and <code>declared-writable</code> are three different states and only one of them is a clean bill of health.</p>"""},
 {"h": "Read the history and throw away everything that is not a post",
  "body": """<p>Joins, leaves, topic changes and pinned items are written by the system on behalf of people who may have no posting rights at all. Counting them is how a locked channel measures as a busy one. Filter on subtype first, count authors second.</p>"""},
 {"h": "Compare distinct authors against the member count",
  "body": """<p><code>conversations.info</code> with <code>include_num_members=true</code> supplies the denominator. Three authors in a channel of nine is a small team. Three authors in a channel of nine hundred is an announcement channel, and worth saying out loud before somebody spends an afternoon on scopes.</p>"""},
 {"h": "Look for yourself in the author list",
  "body": """<p>If the app's own user ID is there, posting was permitted at some point, and the investigation moves from "are we allowed" to "what changed". If it is not there, that is not evidence of a restriction either &mdash; a new integration has never posted anywhere.</p>"""},
 {"h": "Send the finding to a channel manager, not to the OAuth screen",
  "body": """<p>The printed repair names the screen: the channel's own settings, Permissions, Posting permissions. It also prints the alternative, which is usually faster: point the integration at a channel that does not have the restriction, because an announcement channel has that restriction for a reason and a bot is not usually the exception people want to make.</p>"""},
],
"verify": """<p>After a channel manager adds the app, or after the integration is repointed, the run should find your own posts in the history and say so.</p>
<pre><code class="language-bash">python3 slack_channel_posting_policy.py C0DEPLOYS1
# identity  U0APPBOT11 in acme
# C0DEPLOYS1  flag     declared-writable   is_read_only came back false
# C0DEPLOYS1  history  41 post(s) by 11 author(s), channel has 34 member(s)
# C0DEPLOYS1  posting  app-has-posted      this app is among the authors
# 1 channel(s) checked, 0 where posting looks restricted</code></pre>""",
"code_intro": "Three pure functions and three GET methods. <code>read_only_state</code> exists to keep one distinction alive that a single <code>.get()</code> would destroy: the difference between a flag that says no and a flag that was never returned. <code>authorship</code> filters the system traffic out of the history before counting anybody. <code>posting_verdict</code> combines the two and is careful about its own confidence &mdash; <code>locked</code> is a fact, <code>announcement-shaped</code> is an inference, and they are never printed in the same voice.",
"py_file": "slack_channel_posting_policy.py",
"py": '''"""Work out whether a Slack channel will accept a message from this app.

Read only, and inferential on purpose: whether an app may post is the one thing
here that could be settled by posting, and posting is exactly what this section
does not do. The check reads the flag if the plan returns it, reads who has
actually spoken if it does not, and looks for this app among the authors.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_channel_posting_policy")

API = "https://slack.com/api/"

# Message subtypes anybody can generate, including in a channel nobody may post
# in. Joining a locked channel still writes a channel_join message, so counting
# these turns a silent room into a busy one and hides the finding.
NOT_A_POST = frozenset({
    "channel_join", "channel_leave", "channel_topic", "channel_purpose",
    "channel_name", "channel_archive", "channel_unarchive", "pinned_item",
    "unpinned_item", "bot_add", "bot_remove", "reminder_add", "tombstone",
    "channel_convert_to_private", "channel_convert_to_public",
})

# A channel with more members than this, and no more authors than that, is the
# shape of an announcement channel. Both numbers are judgement calls and both
# are meant to be edited for your workspace.
CROWD = 25
NARROW_AUTHORS = 3
MIN_SAMPLE = 8

REPAIR_ASK = ("ask a channel manager to open the channel, then Settings, "
              "Permissions, Posting permissions, and add this app to the members "
              "who may post")
REPAIR_MOVE = ("or point the integration at a channel without the restriction. An "
               "announcement channel is restricted deliberately and an app is not "
               "usually the exception people want to make")
REPAIR_NOT_SCOPES = ("do not add scopes for this. A posting permission is a "
                     "channel setting, and chat:write is already the whole grant "
                     "Slack has to offer")


def read_only_state(channel):
    """Report the flag and whether the flag was there at all. Pure.

    The distinction this function exists to preserve: channel.get("is_read_only")
    returns None on every plan that does not expose the field, None is falsey, and
    a check written that way reports every locked channel in the workspace as
    writable with complete confidence.
    """
    fields = channel or {}
    if "is_read_only" not in fields:
        return ("not-exposed",
                "conversations.info did not return is_read_only at all. Absent is "
                "not false: the field is only present on the plans that expose it, "
                "so this says nothing either way and the history below is the only "
                "evidence available.")
    if fields.get("is_read_only") is True:
        return ("declared-read-only",
                "conversations.info returns is_read_only: true. Nobody posts here, "
                "the app included, and no scope change alters that.")
    return ("declared-writable",
            "is_read_only came back false. That covers the whole-channel lock and "
            "says nothing about posting being restricted to a named group of "
            "members, which is the more common arrangement and sets no readable "
            "field.")


def authorship(messages, bot_user_id=None):
    """Who has actually posted in the readable history. Pure.

    Returns a stats dict. System subtypes are dropped before anybody is counted,
    because they are written on behalf of people who may hold no posting rights
    at all.
    """
    stats = {"sample": len(messages or []), "posts": 0, "apps": 0,
             "authors": [], "self_posted": False}
    for message in messages or []:
        subtype = message.get("subtype")
        if subtype in NOT_A_POST:
            continue
        author = (message.get("user") or message.get("bot_id")
                  or (message.get("bot_profile") or {}).get("id"))
        if not author:
            continue
        stats["posts"] += 1
        if subtype == "bot_message" or message.get("bot_id"):
            stats["apps"] += 1
        if bot_user_id and author == bot_user_id:
            stats["self_posted"] = True
        if author not in stats["authors"]:
            stats["authors"].append(author)
    return stats


def posting_verdict(state, stats, member_count):
    """Combine the flag, the authorship and the size of the room. Pure.

    Returns (verdict, detail). Only `locked` is a fact. `announcement-shaped` is
    an inference and says so in its own text, because the alternative explanation
    for three authors and nine hundred members is a channel nobody uses.
    """
    if state == "declared-read-only":
        return ("locked",
                "the channel declares itself read only. This is the one certain "
                "answer available to a read-only token, and it is an admin action "
                "to change.")

    posts = int(stats.get("posts") or 0)
    authors = list(stats.get("authors") or [])
    members = int(member_count or 0)

    if posts < MIN_SAMPLE:
        return ("undetermined",
                "only %d readable post(s) in the sample. Too little to infer "
                "anything from, and a small sample is itself worth knowing: a "
                "non-Marketplace app is clamped to 15 objects per "
                "conversations.history call." % posts)
    if stats.get("self_posted"):
        return ("app-has-posted",
                "this app is among the authors of the readable history, so it was "
                "permitted to post here at least once without anybody sending a "
                "test message to find out. Evidence about the past: a permission "
                "changed this morning appears in the next failed send, not here.")
    if len(authors) <= NARROW_AUTHORS and members >= CROWD:
        return ("announcement-shaped",
                "%d member(s) and %d distinct author(s) across %d readable "
                "post(s). That is the shape of a channel where posting is held by "
                "a few people. It is also the shape of a channel nobody talks in, "
                "so treat this as a question for a channel manager rather than as "
                "a finding." % (members, len(authors), posts))
    return ("open",
            "%d distinct author(s) across %d readable post(s) in a channel of %d. "
            "Nothing here looks like a posting restriction, and the app has simply "
            "not posted yet." % (len(authors), posts, members))


def whoami(session):
    """The bot's own user ID. GET only."""
    body = session.get(API + "auth.test", timeout=30).json()
    if body.get("ok") is not True:
        raise SystemExit("auth.test answered 200 with ok: false, error=%s"
                         % body.get("error"))
    return body.get("user_id"), body.get("team")


def channel_info(session, cid):
    """One channel object with its member count. GET only."""
    body = session.get(API + "conversations.info",
                       params={"channel": cid, "include_num_members": "true"},
                       timeout=30).json()
    if body.get("ok") is not True:
        raise SystemExit("conversations.info on %s answered ok: false, error=%s"
                         % (cid, body.get("error")))
    return body.get("channel") or {}


def recent_messages(session, cid, limit):
    """The readable history, or an honest empty list. GET only."""
    body = session.get(API + "conversations.history",
                       params={"channel": cid, "limit": limit}, timeout=30).json()
    if body.get("ok") is not True:
        log.warning("conversations.history on %s answered ok: false, error=%s. "
                    "The inference below has nothing to work from.",
                    cid, body.get("error"))
        return []
    return body.get("messages") or []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("channels", nargs="+", help="channel IDs the integration posts to")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--sample", type=int, default=100,
                    help="how many messages of history to read per channel")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:read and channels:history are enough)",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    me, team = whoami(s)
    log.info("identity  %s in %s", me, team)

    restricted = 0
    for cid in args.channels:
        channel = channel_info(s, cid)
        state, why = read_only_state(channel)
        members = channel.get("num_members") or 0
        stats = authorship(recent_messages(s, cid, args.sample), me)
        verdict, detail = posting_verdict(state, stats, members)

        log.info("%-12s flag     %-18s %s", cid, state, why)
        log.info("%-12s history  %d post(s) by %d author(s), channel has %s member(s)",
                 cid, stats["posts"], len(stats["authors"]), members)

        if verdict in ("app-has-posted", "open"):
            log.info("%-12s posting  %-18s %s", cid, verdict, detail)
            continue

        restricted += 1
        log.warning("%-12s posting  %-18s %s", cid, verdict, detail)
        log.warning("  repair: %s", REPAIR_ASK)
        log.warning("  repair: %s", REPAIR_MOVE)
        log.warning("  note:   %s", REPAIR_NOT_SCOPES)

    log.info("%d channel(s) checked, %d where posting looks restricted",
             len(args.channels), restricted)
    return 1 if restricted else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-channel-posting-policy.mjs",
"js": '''/**
 * Work out whether a Slack channel will accept a message from this app.
 *
 * Read only, and inferential on purpose: whether an app may post is the one
 * thing here that could be settled by posting, and posting is exactly what this
 * section does not do. The check reads the flag if the plan returns it, reads
 * who has actually spoken if it does not, and looks for this app among the
 * authors.
 */

const API = 'https://slack.com/api/';

// Message subtypes anybody can generate, including in a channel nobody may post
// in. Joining a locked channel still writes a channel_join message, so counting
// these turns a silent room into a busy one and hides the finding.
const NOT_A_POST = new Set([
  'channel_join', 'channel_leave', 'channel_topic', 'channel_purpose',
  'channel_name', 'channel_archive', 'channel_unarchive', 'pinned_item',
  'unpinned_item', 'bot_add', 'bot_remove', 'reminder_add', 'tombstone',
  'channel_convert_to_private', 'channel_convert_to_public',
]);

// Both numbers are judgement calls and both are meant to be edited.
const CROWD = 25;
const NARROW_AUTHORS = 3;
const MIN_SAMPLE = 8;

const REPAIR_ASK = 'ask a channel manager to open the channel, then Settings, ' +
  'Permissions, Posting permissions, and add this app to the members who may post';
const REPAIR_MOVE = 'or point the integration at a channel without the ' +
  'restriction. An announcement channel is restricted deliberately and an app is ' +
  'not usually the exception people want to make';
const REPAIR_NOT_SCOPES = 'do not add scopes for this. A posting permission is a ' +
  'channel setting, and chat:write is already the whole grant Slack has to offer';

/**
 * Report the flag and whether the flag was there at all. Pure.
 * channel.is_read_only is undefined on every plan that does not expose it, and
 * undefined is falsey, so a check written the obvious way reports every locked
 * channel as writable.
 */
export function readOnlyState(channel) {
  const fields = channel ?? {};
  if (!Object.prototype.hasOwnProperty.call(fields, 'is_read_only')) {
    return ['not-exposed',
      'conversations.info did not return is_read_only at all. Absent is not ' +
      'false: the field is only present on the plans that expose it, so this says ' +
      'nothing either way and the history below is the only evidence available.'];
  }
  if (fields.is_read_only === true) {
    return ['declared-read-only',
      'conversations.info returns is_read_only: true. Nobody posts here, the app ' +
      'included, and no scope change alters that.'];
  }
  return ['declared-writable',
    'is_read_only came back false. That covers the whole-channel lock and says ' +
    'nothing about posting being restricted to a named group of members, which is ' +
    'the more common arrangement and sets no readable field.'];
}

/**
 * Who has actually posted in the readable history. Pure.
 * System subtypes are dropped before anybody is counted.
 */
export function authorship(messages, botUserId = null) {
  const stats = {
    sample: (messages ?? []).length, posts: 0, apps: 0,
    authors: [], self_posted: false,
  };
  for (const message of messages ?? []) {
    const subtype = message.subtype;
    if (NOT_A_POST.has(subtype)) continue;
    const author = message.user ?? message.bot_id ?? message.bot_profile?.id ?? null;
    if (!author) continue;
    stats.posts += 1;
    if (subtype === 'bot_message' || message.bot_id) stats.apps += 1;
    if (botUserId && author === botUserId) stats.self_posted = true;
    if (!stats.authors.includes(author)) stats.authors.push(author);
  }
  return stats;
}

/**
 * Combine the flag, the authorship and the size of the room. Pure.
 * Only `locked` is a fact. `announcement-shaped` is an inference and says so.
 */
export function postingVerdict(state, stats, memberCount) {
  if (state === 'declared-read-only') {
    return ['locked',
      'the channel declares itself read only. This is the one certain answer ' +
      'available to a read-only token, and it is an admin action to change.'];
  }

  const posts = Number(stats?.posts ?? 0);
  const authors = stats?.authors ?? [];
  const members = Number(memberCount ?? 0);

  if (posts < MIN_SAMPLE) {
    return ['undetermined',
      `only ${posts} readable post(s) in the sample. Too little to infer anything ` +
      'from, and a small sample is itself worth knowing: a non-Marketplace app is ' +
      'clamped to 15 objects per conversations.history call.'];
  }
  if (stats.self_posted) {
    return ['app-has-posted',
      'this app is among the authors of the readable history, so it was permitted ' +
      'to post here at least once without anybody sending a test message to find ' +
      'out. Evidence about the past: a permission changed this morning appears in ' +
      'the next failed send, not here.'];
  }
  if (authors.length <= NARROW_AUTHORS && members >= CROWD) {
    return ['announcement-shaped',
      `${members} member(s) and ${authors.length} distinct author(s) across ` +
      `${posts} readable post(s). That is the shape of a channel where posting is ` +
      'held by a few people. It is also the shape of a channel nobody talks in, so ' +
      'treat this as a question for a channel manager rather than as a finding.'];
  }
  return ['open',
    `${authors.length} distinct author(s) across ${posts} readable post(s) in a ` +
    `channel of ${members}. Nothing here looks like a posting restriction, and the ` +
    'app has simply not posted yet.'];
}

async function get(token, method, params) {
  const res = await fetch(`${API}${method}?${new URLSearchParams(params)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
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
    console.error('usage: <channel id>... [--token-env SLACK_BOT_TOKEN] [--sample 100]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:read and channels:history are enough)`);
    process.exitCode = 2;
    return;
  }
  const sample = Number(arg(args, '--sample', 100));

  const auth = await get(token, 'auth.test', {});
  if (auth.ok !== true) {
    throw new Error(`auth.test answered 200 with ok: false, error=${auth.error}`);
  }
  console.log(`identity  ${auth.user_id} in ${auth.team}`);

  let restricted = 0;
  for (const cid of channels) {
    const info = await get(token, 'conversations.info',
      { channel: cid, include_num_members: 'true' });
    if (info.ok !== true) {
      throw new Error(`conversations.info on ${cid} answered ok: false, error=${info.error}`);
    }
    const channel = info.channel ?? {};
    const [state, why] = readOnlyState(channel);
    const members = channel.num_members ?? 0;

    const history = await get(token, 'conversations.history',
      { channel: cid, limit: String(sample) });
    if (history.ok !== true) {
      console.warn(`conversations.history on ${cid} answered ok: false, error=` +
        `${history.error}. The inference below has nothing to work from.`);
    }
    const stats = authorship(history.messages ?? [], auth.user_id);
    const [verdict, detail] = postingVerdict(state, stats, members);

    console.log(`${cid.padEnd(12)} flag     ${state.padEnd(18)} ${why}`);
    console.log(`${cid.padEnd(12)} history  ${stats.posts} post(s) by ` +
      `${stats.authors.length} author(s), channel has ${members} member(s)`);

    if (verdict === 'app-has-posted' || verdict === 'open') {
      console.log(`${cid.padEnd(12)} posting  ${verdict.padEnd(18)} ${detail}`);
      continue;
    }

    restricted += 1;
    console.warn(`${cid.padEnd(12)} posting  ${verdict.padEnd(18)} ${detail}`);
    console.warn(`  repair: ${REPAIR_ASK}`);
    console.warn(`  repair: ${REPAIR_MOVE}`);
    console.warn(`  note:   ${REPAIR_NOT_SCOPES}`);
  }

  console.log(`${channels.length} channel(s) checked, ${restricted} where posting ` +
    'looks restricted');
  process.exitCode = restricted ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that matters most is the one asserting that a channel object <em>without</em> an <code>is_read_only</code> key comes back as <code>not-exposed</code> rather than as writable, because that single behaviour is the difference between this check and the version of it everybody writes first. After that: a history made entirely of <code>channel_join</code> events has to count as zero posts, and the announcement shape must not be claimed in a channel of nine people.",
"test_py_file": "test_slack_channel_posting_policy.py",
"test_py": '''from slack_channel_posting_policy import (authorship, posting_verdict,
                                           read_only_state)

APP = "U0APPBOT11"


def crowd(authors, count):
    """A readable history with `count` posts spread over `authors`."""
    return [{"user": authors[i % len(authors)], "ts": "170000000%d.0001" % i}
            for i in range(count)]


def test_a_missing_flag_is_not_a_writable_channel():
    state, why = read_only_state({"id": "C0LOCKED11", "name": "announce"})
    assert state == "not-exposed"
    assert "Absent is not false" in why


def test_the_flag_is_reported_when_the_plan_returns_it():
    assert read_only_state({"is_read_only": True})[0] == "declared-read-only"
    assert read_only_state({"is_read_only": False})[0] == "declared-writable"


def test_a_declared_read_only_channel_is_the_one_certain_verdict():
    verdict, detail = posting_verdict("declared-read-only", {"posts": 0}, 900)
    assert verdict == "locked"
    assert "admin action" in detail


def test_joins_and_topic_changes_are_not_posts():
    messages = [{"user": "U0AAA", "subtype": "channel_join"},
                {"user": "U0BBB", "subtype": "channel_topic"},
                {"user": "U0CCC", "subtype": "pinned_item"}]
    stats = authorship(messages, APP)
    assert stats["sample"] == 3
    assert stats["posts"] == 0
    assert stats["authors"] == []


def test_authors_are_counted_once_each():
    stats = authorship(crowd(["U0AAA", "U0BBB"], 10), APP)
    assert stats["posts"] == 10
    assert stats["authors"] == ["U0AAA", "U0BBB"]
    assert stats["self_posted"] is False


def test_the_app_finds_itself_in_the_history():
    messages = crowd(["U0AAA"], 9) + [{"user": APP, "bot_id": "B0APP1",
                                       "subtype": "bot_message"}]
    stats = authorship(messages, APP)
    assert stats["self_posted"] is True
    assert stats["apps"] == 1
    verdict, detail = posting_verdict("not-exposed", stats, 900)
    assert verdict == "app-has-posted"
    assert "past" in detail


def test_an_app_message_without_a_user_field_still_has_an_author():
    stats = authorship([{"bot_id": "B0OTHER1", "subtype": "bot_message"}], APP)
    assert stats["posts"] == 1
    assert stats["authors"] == ["B0OTHER1"]
    assert stats["self_posted"] is False


def test_a_crowd_with_three_voices_is_announcement_shaped():
    stats = authorship(crowd(["U0AAA", "U0BBB", "U0CCC"], 60), APP)
    verdict, detail = posting_verdict("not-exposed", stats, 900)
    assert verdict == "announcement-shaped"
    assert "channel manager" in detail


def test_three_voices_in_a_small_room_are_just_a_small_team():
    stats = authorship(crowd(["U0AAA", "U0BBB", "U0CCC"], 60), APP)
    assert posting_verdict("not-exposed", stats, 9)[0] == "open"


def test_a_thin_sample_produces_no_verdict_at_all():
    stats = authorship(crowd(["U0AAA"], 4), APP)
    verdict, detail = posting_verdict("declared-writable", stats, 900)
    assert verdict == "undetermined"
    assert "15 objects" in detail


def test_the_flag_outranks_the_inference():
    stats = authorship(crowd(["U0AAA", "U0BBB", "U0CCC", "U0DDD"], 40), APP)
    assert posting_verdict("declared-read-only", stats, 40)[0] == "locked"
''',
"test_js_file": "slack-channel-posting-policy.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { authorship, postingVerdict, readOnlyState }
  from './slack-channel-posting-policy.mjs';

const APP = 'U0APPBOT11';

/** A readable history with `count` posts spread over `authors`. */
function crowd(authors, count) {
  return Array.from({ length: count }, (_, i) => ({
    user: authors[i % authors.length], ts: `170000000${i}.0001`,
  }));
}

test('a missing flag is not a writable channel', () => {
  const [state, why] = readOnlyState({ id: 'C0LOCKED11', name: 'announce' });
  assert.equal(state, 'not-exposed');
  assert.match(why, /Absent is not false/);
});

test('the flag is reported when the plan returns it', () => {
  assert.equal(readOnlyState({ is_read_only: true })[0], 'declared-read-only');
  assert.equal(readOnlyState({ is_read_only: false })[0], 'declared-writable');
});

test('a declared read only channel is the one certain verdict', () => {
  const [verdict, detail] = postingVerdict('declared-read-only', { posts: 0 }, 900);
  assert.equal(verdict, 'locked');
  assert.match(detail, /admin action/);
});

test('joins and topic changes are not posts', () => {
  const stats = authorship([
    { user: 'U0AAA', subtype: 'channel_join' },
    { user: 'U0BBB', subtype: 'channel_topic' },
    { user: 'U0CCC', subtype: 'pinned_item' },
  ], APP);
  assert.equal(stats.sample, 3);
  assert.equal(stats.posts, 0);
  assert.deepEqual(stats.authors, []);
});

test('authors are counted once each', () => {
  const stats = authorship(crowd(['U0AAA', 'U0BBB'], 10), APP);
  assert.equal(stats.posts, 10);
  assert.deepEqual(stats.authors, ['U0AAA', 'U0BBB']);
  assert.equal(stats.self_posted, false);
});

test('the app finds itself in the history', () => {
  const messages = [...crowd(['U0AAA'], 9),
    { user: APP, bot_id: 'B0APP1', subtype: 'bot_message' }];
  const stats = authorship(messages, APP);
  assert.equal(stats.self_posted, true);
  assert.equal(stats.apps, 1);
  const [verdict, detail] = postingVerdict('not-exposed', stats, 900);
  assert.equal(verdict, 'app-has-posted');
  assert.match(detail, /past/);
});

test('an app message without a user field still has an author', () => {
  const stats = authorship([{ bot_id: 'B0OTHER1', subtype: 'bot_message' }], APP);
  assert.equal(stats.posts, 1);
  assert.deepEqual(stats.authors, ['B0OTHER1']);
  assert.equal(stats.self_posted, false);
});

test('a crowd with three voices is announcement shaped', () => {
  const stats = authorship(crowd(['U0AAA', 'U0BBB', 'U0CCC'], 60), APP);
  const [verdict, detail] = postingVerdict('not-exposed', stats, 900);
  assert.equal(verdict, 'announcement-shaped');
  assert.match(detail, /channel manager/);
});

test('three voices in a small room are just a small team', () => {
  const stats = authorship(crowd(['U0AAA', 'U0BBB', 'U0CCC'], 60), APP);
  assert.equal(postingVerdict('not-exposed', stats, 9)[0], 'open');
});

test('a thin sample produces no verdict at all', () => {
  const stats = authorship(crowd(['U0AAA'], 4), APP);
  const [verdict, detail] = postingVerdict('declared-writable', stats, 900);
  assert.equal(verdict, 'undetermined');
  assert.match(detail, /15 objects/);
});

test('the flag outranks the inference', () => {
  const stats = authorship(crowd(['U0AAA', 'U0BBB', 'U0CCC', 'U0DDD'], 40), APP);
  assert.equal(postingVerdict('declared-read-only', stats, 40)[0], 'locked');
});
''',
"faq": [
 ("Why not just try posting a test message and see what happens?",
  "Because the channel you are testing is usually an announcement channel with several hundred people in it, and a test message there is a small incident of its own. Every script in this section holds a token that could post and none of them do. The history already contains the answer for the case that matters most: if the app has posted here before, it was allowed to."),
 ("Is is_read_only reliable?",
  "It is reliable when it is there, and it is usually not there. The field is returned on the plans that expose it and omitted otherwise, so the correct handling is three states rather than two: present and true, present and false, and absent. Treating absent as false is the specific mistake this script is written to avoid, and it is the default behaviour of the obvious one-line check in both languages."),
 ("What is the difference between this and posting_to_general_channel_denied?",
  "The screen and the person. A read-only or restricted channel is a channel setting, changed by a channel manager, and it can apply to any channel. The general-channel restriction is a workspace preference, changed by a workspace admin, and it applies only to the channel carrying is_general. Bare restricted_action is returned by both, which is why the other note attributes it using that flag."),
 ("Could the app be missing chat:write instead?",
  "That produces missing_scope, with needed and provided both named in the response body, and it is a completely different error string. If you are seeing any member of the restricted_action family, the grant is not the problem: Slack got as far as evaluating the channel's posting policy, which it only does once the token has cleared."),
 ("The channel has 900 members and four authors. Is it definitely restricted?",
  "No, and the script deliberately calls that verdict announcement-shaped rather than restricted. A channel where a few people post to a large audience is the signature of a posting restriction and also the signature of an ordinary channel nobody uses much. It is a good question to put to a channel manager and a bad thing to assert in a report."),
],
"related": [
 ("/slack/general-channel-restricted/", "the same error string, a workspace policy"),
 ("/slack/bot-not-in-channel/", "the membership question this note assumes away"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
],
"citations": [CITE_POSTMESSAGE, CITE_CONV_INFO, CITE_CONV_HISTORY, CITE_SCOPES],
},

{
"slug": "thread-only-or-non-threadable",
"title": "Thread-only and non-threadable channels refuse your post",
"description": "restricted_action_thread_only_channel, or cannot_reply_to_message. Read the channel's threading convention and match your posting mode to it first.",
"h1": "Thread-only and non-threadable channels refuse your post",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["restricted_action_thread_only_channel", "cannot_reply_to_message slack",
             "restricted_action_non_threadable_channel", "slack thread_ts reply failed",
             "slack thread only channel bot"],
"deps": "Python 3.9+ with requests, or Node.js 18+; reading the convention needs channels:history",
"lead": "This one is not a permission. The app is a member, the token is fine, the channel accepts messages from it all day &mdash; just not that message, in that position. A top-level post comes back <code>restricted_action_thread_only_channel</code>. A reply comes back <code>restricted_action_non_threadable_channel</code>, or <code>cannot_reply_to_message</code>, which is a different failure again.</p><p>The code has one posting mode and the channels have several conventions, and the mismatch only shows up in whichever channel somebody added last.",
"short_answer": """<p>Slack channels can be configured so that all conversation happens in threads, in which case a top-level post is refused; and there are channels and messages where threading does not apply, in which case a reply is refused. An integration that always posts top-level, or that always replies under a stored <code>thread_ts</code>, works everywhere until it meets the channel that wants the other one.</p>
<p>There is no <code>is_thread_only</code> field to read, so the check is a convention check rather than a policy check, and the script is careful to say which it is doing. <code>conversations.history</code> shows how the channel actually behaves: how many top-level posts there are, how many of them carry <code>reply_count</code>, and how much of the traffic lives under a handful of parents. That shape is compared against the posting mode your integration is configured for. Separately, <code>conversations.replies</code> tells you whether a stored <code>thread_ts</code> still anchors a live parent, which is the other half of <code>cannot_reply_to_message</code> and has nothing to do with channel policy at all.</p>""",
"problem": """<p>An integration picks its posting mode once, early, for reasons that had nothing to do with any channel. A digest posts top-level because that is what a digest is. An incident bot replies under a stored <code>thread_ts</code> because it wants the updates to stay together. A deploy notifier posts a parent and then threads its own updates under it. Each of those is a sensible default, and each is a global setting in a codebase whose channel list grows one row at a time.</p>
<p>Then somebody adds the incident channel that a team runs entirely in threads, and top-level posts stop being accepted. Or the alert stream is pointed at a channel where the stored parent has aged out of retention, and every reply comes back <code>cannot_reply_to_message</code> while nothing about the channel has changed. Both look like the channel rejecting the app, and neither is: the message is allowed, in the other position.</p>
<p>The two halves of the failure also want different repairs and get conflated constantly. A channel-level refusal is fixed by changing the mode you post in. A dead <code>thread_ts</code> is fixed by not storing a thread anchor forever &mdash; a parent can be deleted, and it can simply fall off the end of a workspace's retention window, after which the ID you cached refers to nothing. One of those is a configuration change and the other is a data-lifetime bug.</p>""",
"why": """<p><strong>This is a position error, not a permission error.</strong> It shares the <code>restricted_action</code> prefix with the channel-lock family, which sends people to the permissions screen, where there is nothing to find. The app may post. It may not post <em>there</em>, in that arrangement.</p>
<p><strong>No field describes the convention, so the history has to.</strong> <code>conversations.info</code> does not return a threading policy. What is readable is behaviour: a channel where nearly every message lives under three parents is being run as a thread-only channel whether or not a setting says so, and an integration that posts top-level into it is going to look wrong even in the cases where it is not refused.</p>
<p><strong>The sample is smaller than you think.</strong> A non-Marketplace app installed after May 2025 is clamped to fifteen objects per <code>conversations.history</code> call and one call a minute. Fifteen messages is a thin basis for a claim about a convention, so the script prints the sample size beside the verdict and refuses to classify below a floor.</p>
<p><strong><code>cannot_reply_to_message</code> is a message-lifetime problem wearing channel clothes.</strong> The parent can be deleted, leaving a tombstone; it can age past the retention window; it can belong to a channel the token has since lost access to. None of those is a channel policy, and <code>conversations.replies</code> distinguishes them for the cost of one call.</p>
<p><strong>The posting mode belongs to the target, not to the app.</strong> The durable repair is a per-channel setting rather than a global one, because the next channel somebody adds will have its own convention and the code will meet it in production.</p>""",
"steps": [
 {"h": "Write down the mode the integration actually uses",
  "body": """<p>Three of them cover almost everything: <code>top-level</code>, <code>reply</code> under a stored anchor, and <code>parent-then-replies</code> where the app posts its own parent and threads beneath it. The script takes the mode as an argument because it is a fact about your code, not about Slack, and nothing in the API will tell it to you.</p>"""},
 {"h": "Read the channel's history and count the shape, not the messages",
  "body": """<p><code>conversations.history</code> returns top-level messages, each carrying <code>reply_count</code> for the thread hanging off it. The three numbers that matter are the top-level count, how many of those have replies, and how many replies in total.</p>"""},
 {"h": "Refuse to classify a thin sample",
  "body": """<p>Below a floor of readable posts the answer is <code>undetermined</code> and the script says so. This is the note where a rate-limit clamp is not a footnote: fifteen messages can make an ordinary channel look thread-only or look never-threaded depending on the hour you ran it.</p>"""},
 {"h": "Compare the convention against your mode",
  "body": """<p>A thread-heavy channel plus a top-level poster predicts <code>restricted_action_thread_only_channel</code>. A never-threaded channel plus a replier predicts <code>restricted_action_non_threadable_channel</code>. The script names the error you would get, which is what makes the finding recognisable to whoever has that string in their logs.</p>"""},
 {"h": "Check every stored thread anchor separately",
  "body": """<p>One <code>conversations.replies</code> with <code>limit=1</code> per anchor. <code>thread_not_found</code>, a tombstone parent, and a live parent with replies are three different states, and only the third is a working anchor. This check has nothing to do with the channel's convention and everything to do with <code>cannot_reply_to_message</code>.</p>"""},
 {"h": "Make the mode a property of the target",
  "body": """<p>Move the posting mode out of the global config and into the row that holds the channel ID. The script prints the line to add. Then stop storing thread anchors indefinitely: give them an expiry shorter than the workspace retention and fall back to a fresh parent when the anchor is gone.</p>"""},
],
"verify": """<p>Run it against the channel that was refusing the message, with the mode the integration is configured for.</p>
<pre><code class="language-bash">python3 slack_thread_mode_match.py --channel C0INCIDENT --mode reply --anchor 1735689600.000100
# C0INCIDENT  shape    thread-heavy    18 top-level post(s), 14 with replies, 212 replies
# C0INCIDENT  mode     compatible      reply matches how this channel is used
# C0INCIDENT  anchor   anchored        1735689600.000100 still has a live parent
# 1 channel(s) checked, 0 mismatch(es), 0 dead anchor(s)</code></pre>""",
"code_intro": "Three pure functions and two GET methods, and the split between them is the point of the note. <code>threading_shape</code> reads a convention out of history and is deliberately unwilling to call one below a sample floor. <code>mode_mismatch</code> turns the convention plus your posting mode into the error string you would see, which is what makes the finding searchable. <code>anchor_state</code> answers an unrelated question that produces a similar-looking failure: whether a stored <code>thread_ts</code> still points at anything.",
"py_file": "slack_thread_mode_match.py",
"py": '''"""Match an integration's Slack posting mode against how a channel is actually used.

Read only. One conversations.history per channel reads the threading convention,
one conversations.replies per stored anchor checks that it still anchors
something. Nothing is sent: the script names the error the current mode would
produce and prints the configuration line that stops producing it.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_thread_mode_match")

API = "https://slack.com/api/"

# System traffic. Nobody chose to post it and it says nothing about how the
# channel is used, so it is dropped before any shape is counted.
NOT_A_POST = frozenset({
    "channel_join", "channel_leave", "channel_topic", "channel_purpose",
    "channel_name", "channel_archive", "channel_unarchive", "pinned_item",
    "unpinned_item", "bot_add", "bot_remove", "reminder_add",
})

MODES = ("top-level", "reply", "parent-then-replies")

# Below this many readable posts nothing is claimed. A non-Marketplace app is
# clamped to 15 objects per conversations.history call, which is thin enough to
# make an ordinary channel look like either extreme.
MIN_SAMPLE = 8
THREAD_HEAVY = 0.8
MIN_PARENTS = 3


def threading_shape(messages):
    """Read a channel's threading convention out of its history. Pure.

    Returns (shape, stats). conversations.history returns top-level messages,
    each carrying reply_count for the thread hanging off it, so the three numbers
    worth having are the top-level count, how many of those were replied to, and
    how many replies exist in total.

    The shapes are named after behaviour rather than policy. Slack exposes no
    threading setting, so "thread-heavy" is the strongest honest claim: this is
    how the channel is used, which is what your message will be judged against.
    """
    posts = parents = replies = broadcasts = 0
    for message in messages or []:
        if message.get("subtype") in NOT_A_POST:
            continue
        posts += 1
        count = int(message.get("reply_count") or 0)
        if count:
            parents += 1
            replies += count
        if message.get("subtype") == "thread_broadcast":
            broadcasts += 1

    stats = {"sample": len(messages or []), "posts": posts, "parents": parents,
             "replies": replies, "broadcasts": broadcasts}
    if posts < MIN_SAMPLE:
        return ("undetermined", stats)

    share = replies / float(replies + posts) if (replies + posts) else 0.0
    if share >= THREAD_HEAVY and parents >= MIN_PARENTS:
        return ("thread-heavy", stats)
    if replies == 0:
        return ("never-threaded", stats)
    return ("mixed", stats)


def mode_mismatch(shape, mode):
    """Compare the channel's convention against the mode the integration uses. Pure.

    Returns (verdict, likely_error, detail). The error string is the useful half:
    it is what somebody already has in their logs, and naming it is what turns a
    shape into a recognisable finding.
    """
    if mode not in MODES:
        return ("unknown-mode", "",
                "%r is not one of %s. The mode is a fact about your code and "
                "nothing in the API will supply it." % (mode, ", ".join(MODES)))
    if shape == "undetermined":
        return ("undetermined", "",
                "too little readable history to describe how this channel is used. "
                "Re-run with a larger sample, or accept that this channel cannot be "
                "assessed from here.")

    if shape == "thread-heavy" and mode == "top-level":
        return ("likely-blocked", "restricted_action_thread_only_channel",
                "almost everything said here is said inside a thread, and this "
                "integration posts at the top level. Where the channel enforces "
                "that convention the post is refused; where it does not, the post "
                "lands somewhere nobody is reading.")
    if shape == "never-threaded" and mode in ("reply", "parent-then-replies"):
        return ("likely-blocked", "restricted_action_non_threadable_channel",
                "nothing in the readable history has ever been replied to, and "
                "this integration threads. Either the channel does not support "
                "threading or nobody uses it, and the first of those refuses the "
                "message outright.")
    if shape == "mixed":
        return ("compatible", "",
                "the channel is used both ways, so neither mode is refused by "
                "convention. Any failure here is a permission or an anchor rather "
                "than a position.")
    return ("compatible", "", "%s matches how this channel is used" % mode)


def anchor_state(body):
    """Whether a stored thread_ts still anchors a live parent. Pure.

    Nothing here is about channel policy. cannot_reply_to_message is usually a
    message-lifetime problem: parents get deleted, and they fall off the end of a
    workspace's retention window, after which a cached anchor refers to nothing.
    """
    if body.get("ok") is not True:
        error = body.get("error") or "<no error field>"
        if error == "thread_not_found":
            return ("missing-parent",
                    "conversations.replies says thread_not_found. The stored ts "
                    "anchors nothing: the parent was deleted or has aged past the "
                    "workspace retention window. A reply under it returns "
                    "cannot_reply_to_message.")
        if error in ("not_in_channel", "channel_not_found", "missing_scope"):
            return ("unreadable",
                    "conversations.replies says %s, which is a membership or scope "
                    "question rather than an answer about the thread." % error)
        return ("unreadable",
                "conversations.replies answered 200 with ok: false, error=%s" % error)

    messages = body.get("messages") or []
    if not messages:
        return ("missing-parent",
                "ok: true with an empty messages array. The thread is gone and "
                "Slack did not consider that an error.")

    parent = messages[0]
    if parent.get("subtype") == "tombstone":
        return ("deleted-parent",
                "the parent is a tombstone: it was deleted while its replies "
                "survived. Slack keeps the thread visible and refuses new replies "
                "to it.")
    count = int(parent.get("reply_count") or 0)
    if count == 0:
        return ("childless-parent",
                "the ts resolves to a message with no replies yet. That is a "
                "perfectly good anchor, and it is indistinguishable from a message "
                "nobody has threaded under.")
    return ("anchored", "the parent is there with %d repl(ies) under it" % count)


def get(session, method, params):
    """One read call. GET only, and the body is returned as Slack sent it."""
    return session.get(API + method, params=params, timeout=30).json()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--channel", required=True, action="append",
                    help="a channel ID the integration posts to; repeatable")
    ap.add_argument("--mode", required=True, choices=list(MODES),
                    help="how this integration posts today")
    ap.add_argument("--anchor", action="append", default=[],
                    help="a stored thread_ts to validate; repeatable")
    ap.add_argument("--sample", type=int, default=100,
                    help="how many messages of history to read per channel")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:read and channels:history are enough)",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    mismatches = dead = 0
    for cid in args.channel:
        history = get(s, "conversations.history",
                      {"channel": cid, "limit": args.sample})
        if history.get("ok") is not True:
            log.warning("%-12s history  unreadable, error=%s", cid,
                        history.get("error"))
            continue

        shape, stats = threading_shape(history.get("messages") or [])
        verdict, likely, detail = mode_mismatch(shape, args.mode)
        log.info("%-12s shape    %-15s %d top-level post(s), %d with replies, "
                 "%d replies", cid, shape, stats["posts"], stats["parents"],
                 stats["replies"])

        if verdict == "compatible":
            log.info("%-12s mode     %-15s %s", cid, verdict, detail)
        else:
            mismatches += 1
            log.warning("%-12s mode     %-15s %s", cid, verdict, detail)
            if likely:
                log.warning("  expect: %s on the next send", likely)
            log.warning("  repair: set the posting mode on this target rather than "
                        "globally, for example  %s: mode=%s", cid,
                        "reply" if args.mode == "top-level" else "top-level")

        for anchor in args.anchor:
            replies = get(s, "conversations.replies",
                          {"channel": cid, "ts": anchor, "limit": 1})
            state, why = anchor_state(replies)
            if state == "anchored" or state == "childless-parent":
                log.info("%-12s anchor   %-15s %s", cid, state, why)
                continue
            dead += 1
            log.warning("%-12s anchor   %-15s %s", cid, state, why)
            log.warning("  repair: expire stored thread anchors well inside the "
                        "workspace retention window and fall back to a fresh "
                        "parent when the anchor is gone")

    log.info("%d channel(s) checked, %d mismatch(es), %d dead anchor(s)",
             len(args.channel), mismatches, dead)
    return 1 if (mismatches or dead) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-thread-mode-match.mjs",
"js": '''/**
 * Match an integration's Slack posting mode against how a channel is used.
 *
 * Read only. One conversations.history per channel reads the threading
 * convention, one conversations.replies per stored anchor checks that it still
 * anchors something. Nothing is sent: the script names the error the current
 * mode would produce and prints the configuration line that stops it.
 */

const API = 'https://slack.com/api/';

// System traffic. Nobody chose to post it and it says nothing about how the
// channel is used, so it is dropped before any shape is counted.
const NOT_A_POST = new Set([
  'channel_join', 'channel_leave', 'channel_topic', 'channel_purpose',
  'channel_name', 'channel_archive', 'channel_unarchive', 'pinned_item',
  'unpinned_item', 'bot_add', 'bot_remove', 'reminder_add',
]);

export const MODES = ['top-level', 'reply', 'parent-then-replies'];

const MIN_SAMPLE = 8;
const THREAD_HEAVY = 0.8;
const MIN_PARENTS = 3;

/**
 * Read a channel's threading convention out of its history. Pure.
 * The shapes are named after behaviour rather than policy: Slack exposes no
 * threading setting, so `thread-heavy` is the strongest honest claim.
 */
export function threadingShape(messages) {
  let posts = 0; let parents = 0; let replies = 0; let broadcasts = 0;
  for (const message of messages ?? []) {
    if (NOT_A_POST.has(message.subtype)) continue;
    posts += 1;
    const count = Number(message.reply_count ?? 0);
    if (count) { parents += 1; replies += count; }
    if (message.subtype === 'thread_broadcast') broadcasts += 1;
  }

  const stats = { sample: (messages ?? []).length, posts, parents, replies, broadcasts };
  if (posts < MIN_SAMPLE) return ['undetermined', stats];

  const share = (replies + posts) ? replies / (replies + posts) : 0;
  if (share >= THREAD_HEAVY && parents >= MIN_PARENTS) return ['thread-heavy', stats];
  if (replies === 0) return ['never-threaded', stats];
  return ['mixed', stats];
}

/**
 * Compare the channel's convention against the mode the integration uses. Pure.
 * Returns [verdict, likelyError, detail]; the error string is the half somebody
 * already has in their logs.
 */
export function modeMismatch(shape, mode) {
  if (!MODES.includes(mode)) {
    return ['unknown-mode', '',
      `${mode} is not one of ${MODES.join(', ')}. The mode is a fact about your ` +
      'code and nothing in the API will supply it.'];
  }
  if (shape === 'undetermined') {
    return ['undetermined', '',
      'too little readable history to describe how this channel is used. Re-run ' +
      'with a larger sample, or accept that this channel cannot be assessed from here.'];
  }

  if (shape === 'thread-heavy' && mode === 'top-level') {
    return ['likely-blocked', 'restricted_action_thread_only_channel',
      'almost everything said here is said inside a thread, and this integration ' +
      'posts at the top level. Where the channel enforces that convention the post ' +
      'is refused; where it does not, the post lands somewhere nobody is reading.'];
  }
  if (shape === 'never-threaded' && (mode === 'reply' || mode === 'parent-then-replies')) {
    return ['likely-blocked', 'restricted_action_non_threadable_channel',
      'nothing in the readable history has ever been replied to, and this ' +
      'integration threads. Either the channel does not support threading or ' +
      'nobody uses it, and the first of those refuses the message outright.'];
  }
  if (shape === 'mixed') {
    return ['compatible', '',
      'the channel is used both ways, so neither mode is refused by convention. ' +
      'Any failure here is a permission or an anchor rather than a position.'];
  }
  return ['compatible', '', `${mode} matches how this channel is used`];
}

/**
 * Whether a stored thread_ts still anchors a live parent. Pure.
 * Nothing here is about channel policy: cannot_reply_to_message is usually a
 * message-lifetime problem.
 */
export function anchorState(body) {
  if (body.ok !== true) {
    const error = body.error ?? '<no error field>';
    if (error === 'thread_not_found') {
      return ['missing-parent',
        'conversations.replies says thread_not_found. The stored ts anchors ' +
        'nothing: the parent was deleted or has aged past the workspace retention ' +
        'window. A reply under it returns cannot_reply_to_message.'];
    }
    if (['not_in_channel', 'channel_not_found', 'missing_scope'].includes(error)) {
      return ['unreadable',
        `conversations.replies says ${error}, which is a membership or scope ` +
        'question rather than an answer about the thread.'];
    }
    return ['unreadable',
      `conversations.replies answered 200 with ok: false, error=${error}`];
  }

  const messages = body.messages ?? [];
  if (messages.length === 0) {
    return ['missing-parent',
      'ok: true with an empty messages array. The thread is gone and Slack did ' +
      'not consider that an error.'];
  }

  const parent = messages[0];
  if (parent.subtype === 'tombstone') {
    return ['deleted-parent',
      'the parent is a tombstone: it was deleted while its replies survived. ' +
      'Slack keeps the thread visible and refuses new replies to it.'];
  }
  const count = Number(parent.reply_count ?? 0);
  if (count === 0) {
    return ['childless-parent',
      'the ts resolves to a message with no replies yet. That is a perfectly good ' +
      'anchor, and it is indistinguishable from a message nobody has threaded under.'];
  }
  return ['anchored', `the parent is there with ${count} repl(ies) under it`];
}

async function get(token, method, params) {
  const res = await fetch(`${API}${method}?${new URLSearchParams(params)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

function all(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) if (args[i] === name) out.push(args[i + 1]);
  return out;
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const channels = all(args, '--channel');
  const mode = arg(args, '--mode', '');
  if (channels.length === 0 || !MODES.includes(mode)) {
    console.error(`usage: --channel C0... [--channel C1...] --mode ${MODES.join('|')} ` +
      '[--anchor 1735689600.000100] [--sample 100] [--token-env SLACK_BOT_TOKEN]');
    process.exitCode = 2;
    return;
  }
  const anchors = all(args, '--anchor');
  const sample = arg(args, '--sample', '100');
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:read and channels:history are enough)`);
    process.exitCode = 2;
    return;
  }

  let mismatches = 0;
  let dead = 0;
  for (const cid of channels) {
    const history = await get(token, 'conversations.history',
      { channel: cid, limit: String(sample) });
    if (history.ok !== true) {
      console.warn(`${cid.padEnd(12)} history  unreadable, error=${history.error}`);
      continue;
    }

    const [shape, stats] = threadingShape(history.messages ?? []);
    const [verdict, likely, detail] = modeMismatch(shape, mode);
    console.log(`${cid.padEnd(12)} shape    ${shape.padEnd(15)} ${stats.posts} ` +
      `top-level post(s), ${stats.parents} with replies, ${stats.replies} replies`);

    if (verdict === 'compatible') {
      console.log(`${cid.padEnd(12)} mode     ${verdict.padEnd(15)} ${detail}`);
    } else {
      mismatches += 1;
      console.warn(`${cid.padEnd(12)} mode     ${verdict.padEnd(15)} ${detail}`);
      if (likely) console.warn(`  expect: ${likely} on the next send`);
      console.warn('  repair: set the posting mode on this target rather than ' +
        `globally, for example  ${cid}: mode=` +
        `${mode === 'top-level' ? 'reply' : 'top-level'}`);
    }

    for (const anchor of anchors) {
      const replies = await get(token, 'conversations.replies',
        { channel: cid, ts: anchor, limit: '1' });
      const [state, why] = anchorState(replies);
      if (state === 'anchored' || state === 'childless-parent') {
        console.log(`${cid.padEnd(12)} anchor   ${state.padEnd(15)} ${why}`);
        continue;
      }
      dead += 1;
      console.warn(`${cid.padEnd(12)} anchor   ${state.padEnd(15)} ${why}`);
      console.warn('  repair: expire stored thread anchors well inside the ' +
        'workspace retention window and fall back to a fresh parent when the ' +
        'anchor is gone');
    }
  }

  console.log(`${channels.length} channel(s) checked, ${mismatches} mismatch(es), ` +
    `${dead} dead anchor(s)`);
  process.exitCode = (mismatches || dead) ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The shape functions are pinned from both ends: a channel that is nothing but threads, and a channel where no message has ever been replied to, with the sample floor between them so that neither can be claimed from a handful of messages. The anchor tests separate the three ways a stored <code>thread_ts</code> can be dead &mdash; a <code>thread_not_found</code> error, an <code>ok: true</code> response with no messages in it, and a tombstoned parent &mdash; because only the first of those looks like a failure.",
"test_py_file": "test_slack_thread_mode_match.py",
"test_py": '''from slack_thread_mode_match import anchor_state, mode_mismatch, threading_shape


def threads(parents, replies_each):
    """Top-level messages that each carry a busy thread."""
    return [{"user": "U0AAA", "ts": "17000000%02d.0001" % i,
             "reply_count": replies_each} for i in range(parents)]


def flat(count):
    """Top-level messages nobody has ever replied to."""
    return [{"user": "U0AAA", "ts": "17000000%02d.0001" % i} for i in range(count)]


def test_a_channel_run_in_threads_reads_as_thread_heavy():
    shape, stats = threading_shape(threads(10, 20))
    assert shape == "thread-heavy"
    assert stats["parents"] == 10
    assert stats["replies"] == 200


def test_a_channel_nobody_threads_in_reads_as_never_threaded():
    shape, stats = threading_shape(flat(20))
    assert shape == "never-threaded"
    assert stats["replies"] == 0


def test_a_channel_used_both_ways_is_mixed():
    assert threading_shape(threads(3, 2) + flat(20))[0] == "mixed"


def test_system_traffic_is_not_a_post():
    messages = flat(3) + [{"user": "U0BBB", "subtype": "channel_join"}] * 30
    shape, stats = threading_shape(messages)
    assert stats["posts"] == 3
    assert shape == "undetermined"


def test_a_thin_sample_is_never_classified():
    assert threading_shape(threads(2, 40))[0] == "undetermined"
    assert threading_shape([])[0] == "undetermined"


def test_top_level_posting_into_a_thread_run_channel_names_its_error():
    verdict, likely, detail = mode_mismatch("thread-heavy", "top-level")
    assert verdict == "likely-blocked"
    assert likely == "restricted_action_thread_only_channel"
    assert "nobody is reading" in detail


def test_threading_into_a_channel_that_never_threads_names_the_other_error():
    for mode in ("reply", "parent-then-replies"):
        verdict, likely, _ = mode_mismatch("never-threaded", mode)
        assert verdict == "likely-blocked"
        assert likely == "restricted_action_non_threadable_channel"


def test_the_matching_pairs_are_compatible():
    assert mode_mismatch("thread-heavy", "reply")[0] == "compatible"
    assert mode_mismatch("never-threaded", "top-level")[0] == "compatible"
    assert mode_mismatch("mixed", "top-level")[0] == "compatible"


def test_an_unassessable_channel_produces_no_prediction():
    verdict, likely, _ = mode_mismatch("undetermined", "top-level")
    assert verdict == "undetermined"
    assert likely == ""


def test_a_mode_the_script_does_not_know_is_rejected_rather_than_guessed():
    assert mode_mismatch("thread-heavy", "broadcast")[0] == "unknown-mode"


def test_thread_not_found_is_a_dead_anchor_and_says_which_error_follows():
    state, why = anchor_state({"ok": False, "error": "thread_not_found"})
    assert state == "missing-parent"
    assert "cannot_reply_to_message" in why


def test_an_ok_response_with_no_messages_is_also_a_dead_anchor():
    state, why = anchor_state({"ok": True, "messages": []})
    assert state == "missing-parent"
    assert "not consider that an error" in why


def test_a_tombstoned_parent_is_its_own_state():
    body = {"ok": True, "messages": [{"subtype": "tombstone", "reply_count": 4}]}
    assert anchor_state(body)[0] == "deleted-parent"


def test_a_live_parent_is_anchored():
    body = {"ok": True, "messages": [{"ts": "1735689600.000100", "reply_count": 4}]}
    state, why = anchor_state(body)
    assert state == "anchored"
    assert "4 repl" in why


def test_a_parent_with_no_replies_yet_is_still_a_good_anchor():
    body = {"ok": True, "messages": [{"ts": "1735689600.000100"}]}
    assert anchor_state(body)[0] == "childless-parent"


def test_a_scope_error_is_not_reported_as_a_dead_thread():
    assert anchor_state({"ok": False, "error": "missing_scope"})[0] == "unreadable"
    assert anchor_state({"ok": False, "error": "not_in_channel"})[0] == "unreadable"
''',
"test_js_file": "slack-thread-mode-match.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { anchorState, modeMismatch, threadingShape }
  from './slack-thread-mode-match.mjs';

/** Top-level messages that each carry a busy thread. */
function threads(parents, repliesEach) {
  return Array.from({ length: parents }, (_, i) => ({
    user: 'U0AAA', ts: `17000000${String(i).padStart(2, '0')}.0001`,
    reply_count: repliesEach,
  }));
}

/** Top-level messages nobody has ever replied to. */
function flat(count) {
  return Array.from({ length: count }, (_, i) => ({
    user: 'U0AAA', ts: `17000000${String(i).padStart(2, '0')}.0001`,
  }));
}

test('a channel run in threads reads as thread heavy', () => {
  const [shape, stats] = threadingShape(threads(10, 20));
  assert.equal(shape, 'thread-heavy');
  assert.equal(stats.parents, 10);
  assert.equal(stats.replies, 200);
});

test('a channel nobody threads in reads as never threaded', () => {
  const [shape, stats] = threadingShape(flat(20));
  assert.equal(shape, 'never-threaded');
  assert.equal(stats.replies, 0);
});

test('a channel used both ways is mixed', () => {
  assert.equal(threadingShape([...threads(3, 2), ...flat(20)])[0], 'mixed');
});

test('system traffic is not a post', () => {
  const joins = Array.from({ length: 30 },
    () => ({ user: 'U0BBB', subtype: 'channel_join' }));
  const [shape, stats] = threadingShape([...flat(3), ...joins]);
  assert.equal(stats.posts, 3);
  assert.equal(shape, 'undetermined');
});

test('a thin sample is never classified', () => {
  assert.equal(threadingShape(threads(2, 40))[0], 'undetermined');
  assert.equal(threadingShape([])[0], 'undetermined');
});

test('top level posting into a thread run channel names its error', () => {
  const [verdict, likely, detail] = modeMismatch('thread-heavy', 'top-level');
  assert.equal(verdict, 'likely-blocked');
  assert.equal(likely, 'restricted_action_thread_only_channel');
  assert.match(detail, /nobody is reading/);
});

test('threading into a channel that never threads names the other error', () => {
  for (const mode of ['reply', 'parent-then-replies']) {
    const [verdict, likely] = modeMismatch('never-threaded', mode);
    assert.equal(verdict, 'likely-blocked');
    assert.equal(likely, 'restricted_action_non_threadable_channel');
  }
});

test('the matching pairs are compatible', () => {
  assert.equal(modeMismatch('thread-heavy', 'reply')[0], 'compatible');
  assert.equal(modeMismatch('never-threaded', 'top-level')[0], 'compatible');
  assert.equal(modeMismatch('mixed', 'top-level')[0], 'compatible');
});

test('an unassessable channel produces no prediction', () => {
  const [verdict, likely] = modeMismatch('undetermined', 'top-level');
  assert.equal(verdict, 'undetermined');
  assert.equal(likely, '');
});

test('a mode the script does not know is rejected rather than guessed', () => {
  assert.equal(modeMismatch('thread-heavy', 'broadcast')[0], 'unknown-mode');
});

test('thread_not_found is a dead anchor and says which error follows', () => {
  const [state, why] = anchorState({ ok: false, error: 'thread_not_found' });
  assert.equal(state, 'missing-parent');
  assert.match(why, /cannot_reply_to_message/);
});

test('an ok response with no messages is also a dead anchor', () => {
  const [state, why] = anchorState({ ok: true, messages: [] });
  assert.equal(state, 'missing-parent');
  assert.match(why, /not consider that an error/);
});

test('a tombstoned parent is its own state', () => {
  const body = { ok: true, messages: [{ subtype: 'tombstone', reply_count: 4 }] };
  assert.equal(anchorState(body)[0], 'deleted-parent');
});

test('a live parent is anchored', () => {
  const body = { ok: true, messages: [{ ts: '1735689600.000100', reply_count: 4 }] };
  const [state, why] = anchorState(body);
  assert.equal(state, 'anchored');
  assert.match(why, /4 repl/);
});

test('a parent with no replies yet is still a good anchor', () => {
  const body = { ok: true, messages: [{ ts: '1735689600.000100' }] };
  assert.equal(anchorState(body)[0], 'childless-parent');
});

test('a scope error is not reported as a dead thread', () => {
  assert.equal(anchorState({ ok: false, error: 'missing_scope' })[0], 'unreadable');
  assert.equal(anchorState({ ok: false, error: 'not_in_channel' })[0], 'unreadable');
});
''',
"faq": [
 ("Is there a field that says a channel is thread-only?",
  "No. conversations.info returns no threading policy, which is why this check reads behaviour instead. That is a real limitation and the script names its shapes accordingly: thread-heavy describes how a channel is used, not what a setting says. It happens to be the more useful claim anyway, since a top-level post into a channel that runs on threads is a bad post even where it is technically allowed."),
 ("What is the difference between restricted_action_thread_only_channel and cannot_reply_to_message?",
  "The first is the channel refusing a top-level post. The second is a specific thread refusing a reply, almost always because the parent no longer exists: it was deleted, or it aged out of the workspace retention window. One is fixed by changing where in the channel you post; the other is fixed by not caching a thread anchor for longer than the message it points at will live."),
 ("How large a history sample do I need?",
  "The script floors at eight readable posts and prints the sample size beside every verdict. If your app is not Marketplace-listed and was installed after May 2025, conversations.history returns at most fifteen objects per call and you get one call a minute, so raising the limit does not help and you may need several runs. Below the floor the honest answer is undetermined."),
 ("Can I just always post in a thread to be safe?",
  "No, because the mirror-image failure exists: a channel or message where threading does not apply refuses the reply with restricted_action_non_threadable_channel. There is no globally safe mode, which is the actual finding of this note. The mode has to be a property of the target channel, stored beside its ID."),
 ("Why does the check need me to tell it the posting mode?",
  "Because nothing in the Slack API knows how your code sends. The convention is readable and the mode is not, so the comparison needs one fact from each side. Passing it in also makes the check honest about what it is doing: it is comparing a decision you made against a habit the channel has, not evaluating a permission."),
],
"related": [
 ("/slack/read-only-channel/", "when it is a permission rather than a position"),
 ("/slack/non-marketplace-history-clamp/", "why the history sample is fifteen objects"),
 ("/slack/http-200-ok-false/", "every failure arrives as HTTP 200"),
],
"citations": [CITE_POSTMESSAGE, CITE_CONV_REPLIES, CITE_CONV_HISTORY, CITE_RETRIEVING],
},

{
"slug": "slack-connect-external-channel",
"title": "is_ext_shared: the channel is shared with another org",
"description": "Nothing errors, and that is the finding. Check is_ext_shared and every member's team_id before an internal bot posts stack traces to a vendor.",
"h1": "is_ext_shared: the channel is shared with another org",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack connect is_ext_shared", "slack external shared channel bot",
             "slack is_org_shared", "slack connect data leak",
             "slack conversations.info is_shared"],
"deps": "Python 3.9+ with requests, or Node.js 18+; resolving members needs users:read",
"lead": "Every other note in this batch is about a message that did not arrive. This one is about a message that arrived perfectly, for eight months, in a room that has a vendor in it.</p><p>Nothing failed. There is no error string to search for, no exit code, no retry, no alert. <code>chat.postMessage</code> returned <code>ok: true</code> every single time, because from the app's side nothing about the channel changed: same ID, same membership, same call. Somebody shared it with another organisation, and the deploy failures with customer names in them have been going out of the building ever since.",
"short_answer": """<p>Slack Connect shares a channel with an external organisation while keeping the channel ID identical. Nothing in your configuration moves, nothing in your code notices, and messages continue to flow. <code>conversations.info</code> is where it becomes visible: <code>is_ext_shared</code> for a channel shared outside your org, <code>is_pending_ext_shared</code> for an invitation not yet accepted, <code>is_org_shared</code> for a channel spanning workspaces inside one Enterprise Grid org, and the vaguer <code>is_shared</code> underneath both.</p>
<p>Those flags change more than the audience. In an externally shared channel a member's <code>team_id</code> is not yours, <code>users.info</code> can answer <code>user_not_found</code> for a perfectly real person, <code>profile.email</code> is absent whatever scopes you hold, and mentions of internal users and links to internal channels do not resolve for half the room. The script below reads the flags, resolves the membership against your own <code>team_id</code> from <code>auth.test</code>, and prints the list of assumptions your send path is quietly still making.</p>""",
"problem": """<p>The absence of an error is the whole problem. Every other failure in this section announces itself somewhere, even if only as <code>ok: false</code> in a body nobody reads. This one produces a clean log, a green dashboard and a successful delivery, and the only symptom is that people outside the company can read your stack traces. Detection cannot be an error handler here, because there is no error. It has to be a scheduled assertion about state.</p>
<p>It usually arrives from the side. A team starts working with a vendor and shares the channel that the conversation is already happening in, which is the sensible thing to do and takes four clicks. Nobody involved in that decision knows that the channel has an alerting integration in it, because the integration was added by a different team eighteen months earlier and is a quiet member that never speaks except when something breaks. The <code>is_ext_shared</code> flag flips and no notification reaches anybody who would recognise what it means.</p>
<p>Then the assumptions break, mostly silently. Code that resolves a member through <code>users.info</code> before deciding what to include gets <code>user_not_found</code> for external members and either crashes or, far more often, falls through to a default that includes everything. Code that looks up an email to match a Slack user against an internal directory gets nothing back and treats the person as unknown. An <code>@here</code> reaches the vendor. A link to an internal channel renders as a dead reference for half the room, which is the one harmless case on this list.</p>""",
"why": """<p><strong>The channel ID does not change, so nothing in your configuration can catch it.</strong> No environment variable moves, no name changes, no deploy happens. Everything a code review looks at is identical before and after. The only thing that changed is a boolean on the far side of an API call nobody makes.</p>
<p><strong><code>is_shared</code> alone does not mean external.</strong> On Enterprise Grid a channel shared between two of your own workspaces sets <code>is_shared</code> and <code>is_org_shared</code> and is entirely internal. Treating those as the same finding produces a report full of false alarms, and a report full of false alarms is a report nobody reads the real finding in. The script keeps <code>external</code>, <code>pending-external</code> and <code>org-shared</code> as three verdicts.</p>
<p><strong><code>team_id</code> is the assumption that quietly stops holding.</strong> Almost every app is written as though every member of every channel belongs to the workspace the token was installed in. In a Connect channel that is false, and it is false in a way that produces no error: <code>conversations.members</code> returns the IDs happily and <code>users.info</code> is the call that refuses.</p>
<p><strong><code>user_not_found</code> is a correct answer here, not a bug.</strong> A member of the other organisation is not in your workspace's user table and your token is not entitled to resolve them. Any code that looks a member up before deciding what to send needs a deliberate branch for that, and the safe branch is to send less rather than to fall through.</p>
<p><strong>Pending is worth reporting as loudly as shared.</strong> <code>is_pending_ext_shared</code> means the invitation is out. When it is accepted nothing on your side is asked to change, so the moment to move an integration is while the answer is still no.</p>""",
"steps": [
 {"h": "Establish your own team_id first",
  "body": """<p>One <code>auth.test</code>. Every membership verdict below is a comparison against it, and hardcoding a workspace ID in a script that audits workspace boundaries is its own small joke.</p>"""},
 {"h": "Read the four sharing flags, not one of them",
  "body": """<p><code>is_ext_shared</code>, <code>is_pending_ext_shared</code>, <code>is_org_shared</code> and <code>is_shared</code>, in that order of precedence. They answer different questions and only the first is a data-egress finding. Report the other two rather than folding them in, because the difference between "outside the company" and "another one of our workspaces" is the difference between an incident and a note.</p>"""},
 {"h": "Enumerate the membership and resolve it",
  "body": """<p><code>conversations.members</code> is cursor-paginated and returns IDs only. Resolving each through <code>users.info</code> is what turns a list of IDs into an audience. Cap it, cache it, and expect a share of the calls to refuse: <code>users.info</code> is a Tier 4 method but a hundred members is still a hundred calls.</p>"""},
 {"h": "Treat an unresolvable member as a finding, not as an error",
  "body": """<p>This is the step most audits get wrong. <code>user_not_found</code> for a member of a Connect channel is Slack telling you the person is outside your organisation. Counting those as failures loses the signal; counting them as external members is the signal.</p>"""},
 {"h": "Print the assumptions rather than only the verdict",
  "body": """<p>The verdict is one line and it is not the useful part. The useful part is the list of things your send path still believes: that members resolve, that emails are readable, that a mention renders for everybody, that a file link is as private as the channel. The script prints that list for the state it found, and it prints nothing for an internal channel.</p>"""},
 {"h": "Put the assertion in the send path, not in a quarterly review",
  "body": """<p>The durable repair is three lines in the code that sends: read <code>conversations.info</code> for the target, refuse when <code>is_ext_shared</code> is true unless that target is explicitly marked as external, and cache the answer for an hour. Where external posting is intended, redact for that target specifically rather than trusting the message body to be safe.</p>"""},
],
"verify": """<p>After the sensitive integration has been moved, re-run over both channels. The internal one should come back with no assumptions listed at all, which is the only clean output this script produces.</p>
<pre><code class="language-bash">python3 slack_external_channel_audit.py C0VENDOR11 C0INTERNAL
# identity   T0ACME1111 as U0APPBOT11
# C0VENDOR11  sharing  external        2 connected team(s) beyond your own
# C0VENDOR11  members  14 resolved, 5 external-org, 2 unresolvable
# C0INTERNAL  sharing  internal        no sharing flags are set
# C0INTERNAL  members  34 resolved, 0 external-org, 0 unresolvable
# 2 channel(s) checked, 1 reaching outside the organisation</code></pre>""",
"code_intro": "Three pure functions and three GET methods. <code>sharing_state</code> keeps external, pending and org-shared apart, because collapsing them is what makes this report unreadable on Enterprise Grid. <code>member_origin</code> places one resolved member against your own <code>team_id</code> and treats an unresolvable member as evidence rather than as a failed call. <code>assumptions_broken</code> is the function worth stealing even if you never run the rest: it returns what your send path still believes, and it returns an empty list for an internal channel.",
"py_file": "slack_external_channel_audit.py",
"py": '''"""Find the Slack channels an integration posts to that reach outside your org.

Read only, and the only note in this section where nothing is failing. Slack
Connect keeps the channel ID identical when a channel is shared externally, so
conversations.info and the membership are the only places the change is visible.
Nothing is sent; the assertion to add to your send path is printed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_external_channel_audit")

API = "https://slack.com/api/"

# What your send path still believes, per sharing state. The verdict is one line
# and this is the part somebody acts on.
ASSUMPTIONS = {
    "external": [
        ("every member resolves through users.info",
         "members of the other organisation are not in your user table and answer "
         "user_not_found. Code that resolves before deciding what to send needs a "
         "branch, and the safe branch sends less"),
        ("users:read.email gives me an address",
         "profile.email is absent for external members whatever scope you hold, so "
         "directory matching silently classifies them as unknown"),
        ("a mention reaches the people I mean",
         "internal user IDs and internal channel links do not resolve for the other "
         "organisation, and an @here reaches all of them"),
        ("the channel ID tells me who the audience is",
         "the ID did not change when the channel was shared. Nothing in your "
         "configuration moved and nothing in a code review would show it"),
        ("a file link is as private as the channel",
         "file, canvas and list sharing across Connect is separately governed. "
         "Blocked, it answers slack_connect_file_link_sharing_blocked. Not blocked, "
         "the file is outside the company"),
    ],
    "pending-external": [
        ("this is not shared yet, so there is time",
         "there is, and that is the point. When the invitation is accepted nothing "
         "on your side is asked to change: same ID, same members call, wider room"),
        ("somebody will tell us when it is accepted",
         "no notification reaches an app owner. The flag flips and the next send "
         "succeeds exactly as before"),
    ],
    "org-shared": [
        ("every member shares my team_id",
         "an org-shared channel spans workspaces inside one Enterprise Grid org, so "
         "members carry other team IDs while being entirely internal"),
        ("auth.test team_id describes the audience",
         "it describes the workspace the token was installed in, which is a subset "
         "of who is in this channel"),
    ],
    "shared-unclassified": [
        ("is_shared on its own tells me something actionable",
         "it does not. Read this channel with a token that can see the org before "
         "deciding whether it is external, and treat it as external until then"),
    ],
    "internal": [],
}

REPAIR_ASSERT = ("assert it in the send path: read conversations.info for the "
                 "target, refuse when is_ext_shared is true unless that target is "
                 "explicitly marked external, cache the answer for an hour")
REPAIR_MOVE = ("move the sensitive integration to an internal-only channel. Where "
               "external posting is intended, redact for that target specifically "
               "rather than trusting the message body")


def sharing_state(channel):
    """Who this channel reaches, from conversations.info. Pure.

    Four flags, in precedence order, kept as separate verdicts. Collapsing
    org-shared into external produces a report full of false alarms on Enterprise
    Grid, and a report full of false alarms is a report the real finding gets
    ignored in.
    """
    fields = channel or {}
    connected = [t for t in (fields.get("connected_team_ids") or []) if t]
    shared = [t for t in (fields.get("shared_team_ids") or []) if t]

    if fields.get("is_ext_shared") is True:
        return ("external",
                "is_ext_shared is set: this channel is shared with at least one "
                "organisation that is not yours (%d connected team id(s), %d shared). "
                "Every message sent here leaves the company and nothing errors."
                % (len(connected), len(shared)))
    if fields.get("is_pending_ext_shared") is True:
        return ("pending-external",
                "is_pending_ext_shared is set: an invitation to another organisation "
                "is outstanding. When it is accepted the channel ID stays the same "
                "and your integration is not asked anything.")
    if fields.get("is_org_shared") is True:
        return ("org-shared",
                "is_org_shared is set: shared across workspaces inside one Enterprise "
                "Grid organisation. Internal, and it still breaks the assumption that "
                "every member carries your team_id.")
    if fields.get("is_shared") is True:
        return ("shared-unclassified",
                "is_shared is set and neither is_ext_shared nor is_org_shared is. "
                "This token cannot tell which kind of sharing it is; treat it as "
                "external until a token that can see the org says otherwise.")
    return ("internal", "no sharing flags are set on this channel")


def member_origin(user, home_team_id):
    """Place one resolved member against your own workspace. Pure.

    `user` is the users.info profile, or None when the call refused. None is the
    interesting case and it is not an error: a member of the other organisation is
    not in your workspace's user table and your token is not entitled to resolve
    them, so Slack answers user_not_found about a real person.
    """
    if not user:
        return ("unresolvable",
                "users.info returned no profile. In a Connect channel that is the "
                "answer rather than a failure: this person belongs to another "
                "organisation and your token may not read them.")
    if user.get("is_stranger") is True:
        return ("external-org",
                "is_stranger is set, which is Slack saying plainly that this member "
                "is outside your organisation.")

    team = str(user.get("team_id") or "")
    home = str(home_team_id or "")
    if team and home and team != home:
        return ("other-team",
                "team_id %s is not %s. In an externally shared channel that is "
                "another organisation; in an org-shared channel it is another "
                "workspace in your own. The channel flags decide which, and this "
                "record does not." % (team, home))
    if user.get("is_ultra_restricted") is True or user.get("is_restricted") is True:
        return ("guest",
                "a guest account in your own workspace. Inside the company, and "
                "usually without access to the channels your message links to.")
    if user.get("is_bot") is True:
        return ("app", "another app in the room, which reads everything you send")
    return ("home", "a member of your own workspace")


def assumptions_broken(state):
    """What the send path still believes, for this sharing state. Pure.

    Empty for an internal channel, which is the only clean output this script
    produces.
    """
    return list(ASSUMPTIONS.get(state, ASSUMPTIONS["shared-unclassified"]))


def get(session, method, params):
    """One read call. GET only."""
    return session.get(API + method, params=params, timeout=30).json()


def all_members(session, cid, cap):
    """Member IDs, cursor paginated, stopped at a cap. GET only."""
    out, cursor = [], ""
    while len(out) < cap:
        params = {"channel": cid, "limit": 200}
        if cursor:
            params["cursor"] = cursor
        body = get(session, "conversations.members", params)
        if body.get("ok") is not True:
            log.warning("conversations.members on %s answered ok: false, error=%s",
                        cid, body.get("error"))
            return out
        out.extend(body.get("members") or [])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            break
    return out[:cap]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("channels", nargs="+", help="channel IDs the integration posts to")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--max-members", type=int, default=200,
                    help="stop resolving members past this many; users.info is one "
                         "call each")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:read, groups:read and users:read are enough)",
                  args.token_env)
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})

    auth = get(s, "auth.test", {})
    if auth.get("ok") is not True:
        raise SystemExit("auth.test answered 200 with ok: false, error=%s"
                         % auth.get("error"))
    home = auth.get("team_id")
    log.info("identity   %s as %s", home, auth.get("user_id"))

    outside = 0
    for cid in args.channels:
        info = get(s, "conversations.info", {"channel": cid})
        if info.get("ok") is not True:
            log.warning("%-12s sharing  unreadable, error=%s", cid, info.get("error"))
            continue

        state, detail = sharing_state(info.get("channel") or {})
        counts = {}
        for uid in all_members(s, cid, args.max_members):
            profile = get(s, "users.info", {"user": uid}).get("user")
            origin, _ = member_origin(profile, home)
            counts[origin] = counts.get(origin, 0) + 1

        external_members = counts.get("external-org", 0) + counts.get("unresolvable", 0)
        summary = ", ".join("%d %s" % (n, k) for k, n in sorted(counts.items()))

        if state == "internal" and not external_members:
            log.info("%-12s sharing  %-20s %s", cid, state, detail)
            log.info("%-12s members  %s", cid, summary or "none resolved")
            continue

        outside += 1
        log.warning("%-12s sharing  %-20s %s", cid, state, detail)
        log.warning("%-12s members  %s", cid, summary or "none resolved")
        for assumption, reality in assumptions_broken(state):
            log.warning("  assumes: %s", assumption)
            log.warning("  actually: %s", reality)
        log.warning("  repair: %s", REPAIR_ASSERT)
        log.warning("  repair: %s", REPAIR_MOVE)

    log.info("%d channel(s) checked, %d reaching outside the organisation",
             len(args.channels), outside)
    return 1 if outside else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-external-channel-audit.mjs",
"js": '''/**
 * Find the Slack channels an integration posts to that reach outside your org.
 *
 * Read only, and the only note in this section where nothing is failing. Slack
 * Connect keeps the channel ID identical when a channel is shared externally,
 * so conversations.info and the membership are the only places the change is
 * visible. Nothing is sent; the assertion to add to your send path is printed.
 */

const API = 'https://slack.com/api/';

// What your send path still believes, per sharing state. The verdict is one line
// and this is the part somebody acts on.
const ASSUMPTIONS = new Map([
  ['external', [
    ['every member resolves through users.info',
      'members of the other organisation are not in your user table and answer ' +
      'user_not_found. Code that resolves before deciding what to send needs a ' +
      'branch, and the safe branch sends less'],
    ['users:read.email gives me an address',
      'profile.email is absent for external members whatever scope you hold, so ' +
      'directory matching silently classifies them as unknown'],
    ['a mention reaches the people I mean',
      'internal user IDs and internal channel links do not resolve for the other ' +
      'organisation, and an @here reaches all of them'],
    ['the channel ID tells me who the audience is',
      'the ID did not change when the channel was shared. Nothing in your ' +
      'configuration moved and nothing in a code review would show it'],
    ['a file link is as private as the channel',
      'file, canvas and list sharing across Connect is separately governed. ' +
      'Blocked, it answers slack_connect_file_link_sharing_blocked. Not blocked, ' +
      'the file is outside the company'],
  ]],
  ['pending-external', [
    ['this is not shared yet, so there is time',
      'there is, and that is the point. When the invitation is accepted nothing on ' +
      'your side is asked to change: same ID, same members call, wider room'],
    ['somebody will tell us when it is accepted',
      'no notification reaches an app owner. The flag flips and the next send ' +
      'succeeds exactly as before'],
  ]],
  ['org-shared', [
    ['every member shares my team_id',
      'an org-shared channel spans workspaces inside one Enterprise Grid org, so ' +
      'members carry other team IDs while being entirely internal'],
    ['auth.test team_id describes the audience',
      'it describes the workspace the token was installed in, which is a subset of ' +
      'who is in this channel'],
  ]],
  ['shared-unclassified', [
    ['is_shared on its own tells me something actionable',
      'it does not. Read this channel with a token that can see the org before ' +
      'deciding whether it is external, and treat it as external until then'],
  ]],
  ['internal', []],
]);

const REPAIR_ASSERT = 'assert it in the send path: read conversations.info for ' +
  'the target, refuse when is_ext_shared is true unless that target is explicitly ' +
  'marked external, cache the answer for an hour';
const REPAIR_MOVE = 'move the sensitive integration to an internal-only channel. ' +
  'Where external posting is intended, redact for that target specifically rather ' +
  'than trusting the message body';

/**
 * Who this channel reaches, from conversations.info. Pure.
 * Four flags in precedence order, kept as separate verdicts: collapsing
 * org-shared into external fills the report with false alarms on Grid.
 */
export function sharingState(channel) {
  const fields = channel ?? {};
  const connected = (fields.connected_team_ids ?? []).filter(Boolean);
  const shared = (fields.shared_team_ids ?? []).filter(Boolean);

  if (fields.is_ext_shared === true) {
    return ['external',
      'is_ext_shared is set: this channel is shared with at least one organisation ' +
      `that is not yours (${connected.length} connected team id(s), ${shared.length} ` +
      'shared). Every message sent here leaves the company and nothing errors.'];
  }
  if (fields.is_pending_ext_shared === true) {
    return ['pending-external',
      'is_pending_ext_shared is set: an invitation to another organisation is ' +
      'outstanding. When it is accepted the channel ID stays the same and your ' +
      'integration is not asked anything.'];
  }
  if (fields.is_org_shared === true) {
    return ['org-shared',
      'is_org_shared is set: shared across workspaces inside one Enterprise Grid ' +
      'organisation. Internal, and it still breaks the assumption that every member ' +
      'carries your team_id.'];
  }
  if (fields.is_shared === true) {
    return ['shared-unclassified',
      'is_shared is set and neither is_ext_shared nor is_org_shared is. This token ' +
      'cannot tell which kind of sharing it is; treat it as external until a token ' +
      'that can see the org says otherwise.'];
  }
  return ['internal', 'no sharing flags are set on this channel'];
}

/**
 * Place one resolved member against your own workspace. Pure.
 * `user` is the users.info profile, or null when the call refused, and null is
 * the interesting case rather than an error.
 */
export function memberOrigin(user, homeTeamId) {
  if (!user) {
    return ['unresolvable',
      'users.info returned no profile. In a Connect channel that is the answer ' +
      'rather than a failure: this person belongs to another organisation and your ' +
      'token may not read them.'];
  }
  if (user.is_stranger === true) {
    return ['external-org',
      'is_stranger is set, which is Slack saying plainly that this member is ' +
      'outside your organisation.'];
  }

  const team = String(user.team_id ?? '');
  const home = String(homeTeamId ?? '');
  if (team && home && team !== home) {
    return ['other-team',
      `team_id ${team} is not ${home}. In an externally shared channel that is ` +
      'another organisation; in an org-shared channel it is another workspace in ' +
      'your own. The channel flags decide which, and this record does not.'];
  }
  if (user.is_ultra_restricted === true || user.is_restricted === true) {
    return ['guest',
      'a guest account in your own workspace. Inside the company, and usually ' +
      'without access to the channels your message links to.'];
  }
  if (user.is_bot === true) {
    return ['app', 'another app in the room, which reads everything you send'];
  }
  return ['home', 'a member of your own workspace'];
}

/**
 * What the send path still believes, for this sharing state. Pure.
 * Empty for an internal channel, which is the only clean output here.
 */
export function assumptionsBroken(state) {
  return [...(ASSUMPTIONS.get(state) ?? ASSUMPTIONS.get('shared-unclassified'))];
}

async function get(token, method, params) {
  const res = await fetch(`${API}${method}?${new URLSearchParams(params)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}

async function allMembers(token, cid, cap) {
  const out = [];
  let cursor = '';
  while (out.length < cap) {
    const params = { channel: cid, limit: '200' };
    if (cursor) params.cursor = cursor;
    const body = await get(token, 'conversations.members', params);
    if (body.ok !== true) {
      console.warn(`conversations.members on ${cid} answered ok: false, error=${body.error}`);
      return out;
    }
    out.push(...(body.members ?? []));
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) break;
  }
  return out.slice(0, cap);
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
      '[--max-members 200]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:read, groups:read and users:read are enough)`);
    process.exitCode = 2;
    return;
  }
  const cap = Number(arg(args, '--max-members', 200));

  const auth = await get(token, 'auth.test', {});
  if (auth.ok !== true) {
    throw new Error(`auth.test answered 200 with ok: false, error=${auth.error}`);
  }
  const home = auth.team_id;
  console.log(`identity   ${home} as ${auth.user_id}`);

  let outside = 0;
  for (const cid of channels) {
    const info = await get(token, 'conversations.info', { channel: cid });
    if (info.ok !== true) {
      console.warn(`${cid.padEnd(12)} sharing  unreadable, error=${info.error}`);
      continue;
    }

    const [state, detail] = sharingState(info.channel ?? {});
    const counts = new Map();
    for (const uid of await allMembers(token, cid, cap)) {
      const profile = (await get(token, 'users.info', { user: uid })).user ?? null;
      const [origin] = memberOrigin(profile, home);
      counts.set(origin, (counts.get(origin) ?? 0) + 1);
    }

    const externalMembers = (counts.get('external-org') ?? 0) + (counts.get('unresolvable') ?? 0);
    const summary = [...counts.entries()].sort()
      .map(([k, n]) => `${n} ${k}`).join(', ');

    if (state === 'internal' && !externalMembers) {
      console.log(`${cid.padEnd(12)} sharing  ${state.padEnd(20)} ${detail}`);
      console.log(`${cid.padEnd(12)} members  ${summary || 'none resolved'}`);
      continue;
    }

    outside += 1;
    console.warn(`${cid.padEnd(12)} sharing  ${state.padEnd(20)} ${detail}`);
    console.warn(`${cid.padEnd(12)} members  ${summary || 'none resolved'}`);
    for (const [assumption, reality] of assumptionsBroken(state)) {
      console.warn(`  assumes: ${assumption}`);
      console.warn(`  actually: ${reality}`);
    }
    console.warn(`  repair: ${REPAIR_ASSERT}`);
    console.warn(`  repair: ${REPAIR_MOVE}`);
  }

  console.log(`${channels.length} channel(s) checked, ${outside} reaching outside ` +
    'the organisation');
  process.exitCode = outside ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two behaviours carry this note and both are pinned hard. An org-shared channel must not be reported as external, because a Grid workspace has plenty of them and one false alarm per channel is how a report becomes wallpaper. And a member who fails to resolve must come back as <code>unresolvable</code> with an explanation, not as an exception: <code>user_not_found</code> for a member of a Connect channel is the answer to the question, not a failed call.",
"test_py_file": "test_slack_external_channel_audit.py",
"test_py": '''from slack_external_channel_audit import (assumptions_broken, member_origin,
                                          sharing_state)

HOME = "T0ACME1111"
AWAY = "T0VENDOR22"


def test_an_externally_shared_channel_is_the_headline_finding():
    state, detail = sharing_state({"is_shared": True, "is_ext_shared": True,
                                   "connected_team_ids": [AWAY]})
    assert state == "external"
    assert "leaves the company" in detail


def test_a_pending_invitation_is_reported_before_it_is_accepted():
    state, detail = sharing_state({"is_pending_ext_shared": True})
    assert state == "pending-external"
    assert "not asked anything" in detail


def test_an_org_shared_channel_is_internal_and_not_an_alarm():
    state, detail = sharing_state({"is_shared": True, "is_org_shared": True})
    assert state == "org-shared"
    assert "Internal" in detail


def test_external_beats_org_shared_when_both_flags_are_set():
    assert sharing_state({"is_ext_shared": True, "is_org_shared": True})[0] == "external"


def test_bare_is_shared_is_not_classified_as_safe():
    state, _ = sharing_state({"is_shared": True})
    assert state == "shared-unclassified"
    assert assumptions_broken(state)


def test_a_channel_with_no_flags_is_internal_and_lists_nothing():
    state, _ = sharing_state({"id": "C0INTERNAL", "name": "deploys"})
    assert state == "internal"
    assert assumptions_broken(state) == []


def test_a_member_who_does_not_resolve_is_evidence_not_an_error():
    origin, why = member_origin(None, HOME)
    assert origin == "unresolvable"
    assert "rather than a failure" in why


def test_is_stranger_is_taken_at_face_value():
    origin, _ = member_origin({"id": "U0THEM111", "is_stranger": True}, HOME)
    assert origin == "external-org"


def test_a_foreign_team_id_is_reported_without_deciding_what_it_means():
    origin, why = member_origin({"id": "U0THEM111", "team_id": AWAY}, HOME)
    assert origin == "other-team"
    assert AWAY in why and HOME in why
    assert "channel flags decide" in why


def test_a_guest_in_your_own_workspace_is_not_external():
    origin, _ = member_origin({"id": "U0GUEST11", "team_id": HOME,
                               "is_restricted": True}, HOME)
    assert origin == "guest"


def test_another_app_in_the_room_is_named_as_one():
    origin, _ = member_origin({"id": "U0OTHERAP", "team_id": HOME,
                               "is_bot": True}, HOME)
    assert origin == "app"


def test_an_ordinary_colleague_is_home():
    assert member_origin({"id": "U0USER111", "team_id": HOME}, HOME)[0] == "home"


def test_the_external_assumption_list_names_the_email_and_the_mention():
    listed = " ".join(a for a, _ in assumptions_broken("external"))
    assert "users.info" in listed
    assert "email" in listed
    assert "mention" in listed


def test_an_unknown_state_is_treated_as_shared_rather_than_as_safe():
    assert assumptions_broken("something-new") == assumptions_broken("shared-unclassified")
''',
"test_js_file": "slack-external-channel-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { assumptionsBroken, memberOrigin, sharingState }
  from './slack-external-channel-audit.mjs';

const HOME = 'T0ACME1111';
const AWAY = 'T0VENDOR22';

test('an externally shared channel is the headline finding', () => {
  const [state, detail] = sharingState({
    is_shared: true, is_ext_shared: true, connected_team_ids: [AWAY],
  });
  assert.equal(state, 'external');
  assert.match(detail, /leaves the company/);
});

test('a pending invitation is reported before it is accepted', () => {
  const [state, detail] = sharingState({ is_pending_ext_shared: true });
  assert.equal(state, 'pending-external');
  assert.match(detail, /not asked anything/);
});

test('an org shared channel is internal and not an alarm', () => {
  const [state, detail] = sharingState({ is_shared: true, is_org_shared: true });
  assert.equal(state, 'org-shared');
  assert.match(detail, /Internal/);
});

test('external beats org shared when both flags are set', () => {
  assert.equal(sharingState({ is_ext_shared: true, is_org_shared: true })[0], 'external');
});

test('bare is_shared is not classified as safe', () => {
  const [state] = sharingState({ is_shared: true });
  assert.equal(state, 'shared-unclassified');
  assert.ok(assumptionsBroken(state).length > 0);
});

test('a channel with no flags is internal and lists nothing', () => {
  const [state] = sharingState({ id: 'C0INTERNAL', name: 'deploys' });
  assert.equal(state, 'internal');
  assert.deepEqual(assumptionsBroken(state), []);
});

test('a member who does not resolve is evidence not an error', () => {
  const [origin, why] = memberOrigin(null, HOME);
  assert.equal(origin, 'unresolvable');
  assert.match(why, /rather than a failure/);
});

test('is_stranger is taken at face value', () => {
  assert.equal(memberOrigin({ id: 'U0THEM111', is_stranger: true }, HOME)[0],
    'external-org');
});

test('a foreign team id is reported without deciding what it means', () => {
  const [origin, why] = memberOrigin({ id: 'U0THEM111', team_id: AWAY }, HOME);
  assert.equal(origin, 'other-team');
  assert.match(why, new RegExp(AWAY));
  assert.match(why, new RegExp(HOME));
  assert.match(why, /channel flags decide/);
});

test('a guest in your own workspace is not external', () => {
  assert.equal(memberOrigin({ id: 'U0GUEST11', team_id: HOME, is_restricted: true },
    HOME)[0], 'guest');
});

test('another app in the room is named as one', () => {
  assert.equal(memberOrigin({ id: 'U0OTHERAP', team_id: HOME, is_bot: true },
    HOME)[0], 'app');
});

test('an ordinary colleague is home', () => {
  assert.equal(memberOrigin({ id: 'U0USER111', team_id: HOME }, HOME)[0], 'home');
});

test('the external assumption list names the email and the mention', () => {
  const listed = assumptionsBroken('external').map(([a]) => a).join(' ');
  assert.match(listed, /users.info/);
  assert.match(listed, /email/);
  assert.match(listed, /mention/);
});

test('an unknown state is treated as shared rather than as safe', () => {
  assert.deepEqual(assumptionsBroken('something-new'),
    assumptionsBroken('shared-unclassified'));
});
''',
"faq": [
 ("How do I tell an externally shared channel from one shared between our own workspaces?",
  "is_ext_shared means outside your organisation; is_org_shared means across workspaces inside one Enterprise Grid org. Both set is_shared, which is why is_shared alone is not a finding. The script keeps them apart deliberately: a Grid workspace has many org-shared channels, and an audit that flags all of them is an audit whose real finding gets scrolled past."),
 ("Why does users.info fail for some members of the channel?",
  "Because they are not your users. A member from the other organisation is not in your workspace's user table, and your token has no entitlement to read them, so Slack answers user_not_found about a person who visibly exists. Treat that as the classification rather than as an error, and give the send path a branch for members it cannot resolve."),
 ("Can an app be notified when a channel becomes externally shared?",
  "There are shared-channel events, but they require the subscription to have been set up in advance and the app's event delivery to be healthy, which is exactly the combination this note assumes you do not have. A scheduled read of conversations.info for every configured target does not depend on any of that and takes one call per channel."),
 ("Is posting to a Slack Connect channel always wrong?",
  "No. Plenty of integrations exist to talk to a partner and belong there. The finding is the mismatch: an internal alerting bot, configured for an internal channel, still posting after the channel was shared. That is why the durable repair is an explicit per-target flag, so an intentionally external target passes the assertion and everything else fails it."),
 ("Nothing has ever errored. What is the actual harm?",
  "Whatever your alerts contain. Deploy failures carry stack traces, stack traces carry file paths and query fragments, and monitoring messages carry customer names and IDs. None of that was written with an external reader in mind, because when it was written there was not one. The absence of an error is what let it run for months."),
],
"related": [
 ("/slack/public-file-links-exposed/", "the other note about data leaving the room"),
 ("/slack/enterprise-id-not-stored/", "identity that spans more than one workspace"),
 ("/slack/private-channel-invisible/", "when the token cannot see the channel at all"),
],
"citations": [CITE_CONV_INFO, CITE_CONV_MEMBERS, CITE_USERS_INFO, CITE_GRID],
},

]
