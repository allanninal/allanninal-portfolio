#!/usr/bin/env python3
"""/slack/ field notes, batch H — the writing.

Four notes about access that used to exist. The first two are about a change
somebody made to a channel while your integration was already using it: a
public channel converted to private, where the ID never moves and the governing
scope does, and a bot quietly removed from a room it had been posting to for a
year. Neither is a state you configured wrong; both are transitions, and both
are evidenced against something you recorded earlier rather than against the
channel alone.

The last two are both DM failures and they fail from opposite ends. One is your
side: there is no D conversation to address, because nobody ever opened one.
One is theirs: the conversation exists, the account behind it was deactivated
in October, and every send since has returned ok: true into a room with nobody
in it.

Read-only throughout. GET requests to read methods: nothing here posts, joins,
invites, opens a DM or converts anything. conversations.open creates a DM, so
it is not called even to test for one; the IM inventory is read instead. Every
script reports what it found and prints the repair for a human to run.
"""

CITE_CONV_INFO = ("conversations.info method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.info")
CITE_CONV_LIST = ("conversations.list method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.list")
CITE_CONV_OPEN = ("conversations.open method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/conversations.open")
CITE_USERS_CONV = ("users.conversations method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.conversations")
CITE_USERS_LIST = ("users.list method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.list")
CITE_USERS_INFO = ("users.info method reference — Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.info")
CITE_MEMBER_LEFT = ("member_left_channel event reference — Slack Docs",
                    "https://docs.slack.dev/reference/events/member_left_channel")
CITE_USER_CHANGE = ("user_change event reference — Slack Docs",
                    "https://docs.slack.dev/reference/events/user_change")
CITE_SCOPES = ("Permission scopes — Slack Docs",
               "https://docs.slack.dev/reference/scopes/")
CITE_AUTH_TEST = ("auth.test method reference — Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_CONV_API = ("Using the Conversations API — Slack Docs",
                 "https://docs.slack.dev/apis/web-api/using-the-conversations-api")
CITE_PAGINATION = ("Pagination in the Web API — Slack Docs",
                   "https://docs.slack.dev/apis/web-api/pagination")

GUIDES = [

{
"slug": "channel-converted-to-private",
"title": "is_private: the public channel you read was converted",
"description": "An admin converted a public channel to private. The ID never changed, so nothing looks stale, and the scope that governed your reads is now the wrong one.",
"h1": "is_private: the public channel you read was converted",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack channel converted to private", "slack is_private true",
             "slack groups:read after conversion", "slack chat:write.public stopped working",
             "slack public channel now private bot"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a baseline file recording what each channel was",
"lead": "The reader has been pulling history out of <code>#incidents</code> for a year. This morning it returns <code>channel_not_found</code>, and the day before it returned messages. Nothing was deployed, the ID in the config is the ID it has always been, and the channel is still there. Somebody converted it to private on Tuesday, which moved it across a scope boundary without moving its identifier.",
"short_answer": """<p>Conversion preserves the channel ID and everything in it. What it changes is which scope pair governs access: reads that <code>channels:read</code> and <code>channels:history</code> authorised now need <code>groups:read</code> and <code>groups:history</code>. If the token holds the new pair, <code>conversations.info</code> keeps working and <code>channel.is_private</code> is simply <code>true</code>. If it does not, the same ID that answered yesterday answers <code>channel_not_found</code> today.</p>
<p>That means the finding is a comparison, not a field read. The script below takes a baseline &mdash; the visibility your configuration recorded for each channel, and when &mdash; and compares it against what <code>conversations.info</code> says now. It also compares <code>channel.created</code> against the recorded one, because a conversion keeps that timestamp and a recycled name does not, which is how you tell "this channel changed" from "this is a different channel".</p>""",
"problem": """<p>Every other channel fault leaves a mark on the reference. A rename releases the name, an archive sets a boolean you can read, a wrong ID never resolved in the first place. Conversion leaves nothing: the same ID, the same name, the same members, the same history, the same position in the sidebar. The only thing that moved is invisible from the configuration file, and it moved because somebody in the channel decided its conversation had become sensitive.</p>
<p>The way it presents depends entirely on what the token already holds, which is why two teams hit this and describe two different bugs. An app with <code>groups:read</code> granted for some other reason sees nothing at all until it tries to read history, then gets <code>not_in_channel</code> if the bot is not a member. An app with only the <code>channels:*</code> pair loses the channel completely: it vanishes from <code>conversations.list</code> and <code>conversations.info</code> starts denying it exists. One team is debugging membership, the other is debugging a missing channel, and both are looking at the same Tuesday afternoon.</p>
<p>The cruellest variant is an app that never joined anything. <code>chat:write.public</code> lets an app post into public channels it is not a member of, and a great many notification integrations are built entirely on that convenience. It applies to public channels and only public channels. The moment the channel converts, that route closes, and the repair is not a scope: it is a person in the room running <code>/invite</code>.</p>""",
"why": """<p><strong>The ID is a red herring, so stop checking it.</strong> Conversion is deliberately identity-preserving: permalinks keep working, references in old messages keep working, and your configuration keeps pointing at exactly the right conversation. Everything a developer instinctively verifies is correct, which is why this one eats an afternoon before anybody says the word "private".</p>
<p><strong>Scopes are typed by conversation, not by channel.</strong> Slack governs public channels with <code>channels:*</code> and private ones with <code>groups:*</code>, and a channel can move between those categories while your grant cannot. No scope covers both. That is why a conversion is a permission event even though nobody touched permissions.</p>
<p><strong>The transition needs a baseline, because the current state is not a fault.</strong> <code>is_private: true</code> is an ordinary property of an ordinary channel. It is only a finding when your configuration recorded the channel as public, so the script has to be given something to compare against. A file that records visibility, <code>created</code>, and the date it was captured is enough, and it is the same file that dates the change.</p>
<p><strong><code>created</code> distinguishes conversion from recycling.</strong> A converted channel keeps its creation timestamp along with its ID. If the ID resolves to a channel created three weeks ago, you are not looking at a conversion &mdash; you are looking at a different conversation, and that is a different note. One integer comparison keeps the two apart.</p>
<p><strong>The conversion is one-way in the product.</strong> Slack's UI converts public to private and does not offer the reverse to ordinary admins, so "wait for it to be converted back" is not a plan. Adding the scope pair and getting the bot invited is the whole repair, and the second half needs a human inside the room.</p>""",
"steps": [
 {"h": "Record what each channel was, once",
  "body": """<p>The baseline is a small JSON object per channel ID: <code>visibility</code>, the <code>created</code> timestamp <code>conversations.info</code> returned, and the date you captured it. Without it there is no finding here at all, only a description of the present. Generate it on a day everything works and commit it beside the configuration it describes.</p>"""},
 {"h": "Read the grant off the header first",
  "body": """<p>One <code>auth.test</code>, and take <code>X-OAuth-Scopes</code> from the response. The grant decides how the conversion will present: with <code>groups:read</code> you will see the converted channel and its new flag, without it you will see an ID that has stopped existing. Interpreting the second case without knowing the grant is guesswork.</p>"""},
 {"h": "Compare visibility against the baseline, not against expectations",
  "body": """<p><code>conversations.info</code> per target, then <code>channel.is_private</code> against the recorded value. A channel recorded private and still private is not a finding no matter how surprising anybody finds it, and a channel recorded public and now private is the headline whether or not anything has failed yet.</p>"""},
 {"h": "Treat a not-found on a recorded channel as a candidate conversion",
  "body": """<p>An ID that used to answer and now says <code>channel_not_found</code>, on a token with no <code>groups:read</code>, is most likely a conversion. It could also be a deletion, and no read-only token separates those, so the script reports it as the candidate it is and names the scope that would settle it.</p>"""},
 {"h": "Check the creation timestamp before you believe any of it",
  "body": """<p>If <code>channel.created</code> does not match the baseline, the ID is answering for a channel that did not exist when you recorded it. That is not a conversion and the repair is completely different. One comparison, and it prevents the most confident kind of wrong report.</p>"""},
 {"h": "Add the scope pair, reinstall, then get the bot invited",
  "body": """<p><code>groups:read</code> and <code>groups:history</code> in Bot Token Scopes, then a reinstall, then a member of the channel running <code>/invite @YourApp</code>. If the integration was living on <code>chat:write.public</code> it has never been a member of anything, so the invite is not a formality &mdash; it is now the only way in.</p>"""},
],
"verify": """<p>Once the scopes are granted and the bot has been invited, re-run against the same baseline and refresh it. Every channel should agree with what it records.</p>
<pre><code class="language-bash">python3 slack_visibility_change.py --baseline channels.json
# grant: channels:read=yes groups:read=yes groups:history=yes
# unchanged   C01ABCDE9  private, and the baseline already recorded it private
# unchanged   C02XYZ123  public, and the baseline already recorded it public
# 2 channel(s) checked, 0 converted since the baseline</code></pre>""",
"code_intro": "The three pure functions are the whole argument. <code>conversion_verdict</code> compares a recorded visibility against a live <code>conversations.info</code> response and treats a not-found as a candidate rather than an answer, <code>same_channel</code> uses the creation timestamp to rule out the case where the ID is answering for something else entirely, and <code>access_route</code> says what way in the app still has now &mdash; including the one that has closed for good.",
"py_file": "slack_visibility_change.py",
"py": '''"""Find the Slack channels that were converted to private under an integration.

Read only. One auth.test for the granted-scope header, then one
conversations.info per channel, each compared against a baseline that records
what the channel used to be. Nothing is converted, joined or invited: the
script names the channels whose visibility moved and prints the repair.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_visibility_change")

API = "https://slack.com/api/"

# Conversion moves a channel from one scope pair to the other without moving its
# ID. That is the entire mechanism, and the reason nothing in a config file looks
# stale afterwards.
PUBLIC_PAIR = ("channels:read", "channels:history")
PRIVATE_PAIR = ("groups:read", "groups:history")


def granted_scopes(header):
    """The scopes the token actually holds, off X-OAuth-Scopes. Pure."""
    return {part.strip() for part in str(header or "").split(",") if part.strip()}


def conversion_verdict(record, body, scopes):
    """Compare a recorded visibility against a live conversations.info response.

    Pure. Returns (state, detail). A not-found on a channel the baseline records
    is deliberately reported as a candidate rather than a conclusion: conversion
    and deletion are indistinguishable to a token that cannot see private
    channels, and claiming the first would be a guess dressed as a finding.
    """
    was = str((record or {}).get("visibility") or "unrecorded").lower()

    if body.get("ok") is not True:
        error = body.get("error") or "<no error field>"
        if error != "channel_not_found":
            return ("unreadable",
                    "conversations.info answered 200 with ok: false, error=%s. "
                    "Visibility cannot be compared until that is resolved." % error)
        if was != "public":
            return ("not-visible",
                    "channel_not_found, and the baseline does not record this "
                    "channel as public, so there is nothing here to compare.")
        if PRIVATE_PAIR[0] not in scopes:
            return ("candidate-conversion",
                    "the baseline recorded this channel as public and the ID now "
                    "answers channel_not_found on a token without %s. Conversion "
                    "is the likeliest cause; deletion is the other one, and this "
                    "token cannot tell them apart." % PRIVATE_PAIR[0])
        return ("gone",
                "the baseline recorded this channel as public and it is now "
                "invisible even with %s granted, so a conversion would still have "
                "been readable. Something removed it." % PRIVATE_PAIR[0])

    channel = body.get("channel") or {}
    now = "private" if channel.get("is_private") else "public"
    if was == "unrecorded":
        return ("unrecorded",
                "no baseline visibility for this channel, so today's %s is a fact "
                "rather than a finding. Record it and re-run." % now)
    if was == now:
        return ("unchanged",
                "%s, and the baseline already recorded it %s" % (now, was))
    if was == "public":
        return ("converted-to-private",
                "recorded public, is_private is now true. Same ID, same history, "
                "and reads are governed by %s from here on." % PRIVATE_PAIR[0])
    return ("converted-to-public",
            "recorded private and now public. Rare, because the product converts "
            "one way, but it widens who can read what your app writes here.")


def same_channel(record, channel):
    """Is this the conversation the baseline recorded, or a different one?

    Pure. A conversion preserves both the ID and channel.created; a name released
    by a rename and claimed by a new channel preserves neither. One integer
    comparison keeps a conversion report from being filed against a channel that
    did not exist when the baseline was written.
    """
    was = (record or {}).get("created")
    now = (channel or {}).get("created")
    if was is None or now is None:
        return ("undatable",
                "no creation timestamp on one side, so the identity of this "
                "channel cannot be confirmed. Re-record the baseline.")
    if int(was) == int(now):
        return ("same-channel",
                "created is unchanged, so this is the same conversation and "
                "whatever changed about it changed in place")
    return ("different-channel",
            "created moved from %s to %s. This ID is answering for a channel that "
            "did not exist when the baseline was recorded, so nothing here is a "
            "conversion." % (was, now))


def access_route(channel, scopes):
    """What way into this channel the app still has. Pure.

    The route that matters is the one that closes: chat:write.public posts into
    public channels without membership and has no private equivalent, so an
    integration that never joined anything has no route left the moment the
    channel converts.
    """
    if not (channel or {}).get("is_private"):
        return ("public",
                "public, so chat:write.public still reaches it without membership")
    missing = [s for s in PRIVATE_PAIR if s not in scopes]
    if missing:
        return ("no-scope",
                "private and the token is missing %s. Add them to Bot Token "
                "Scopes and reinstall." % ", ".join(missing))
    if channel.get("is_member"):
        return ("member",
                "private, and the bot is a member, so the scopes are the only "
                "thing that had to change")
    return ("needs-invite",
            "private, scopes granted, and the bot is not a member. No API call "
            "fixes this: a private channel cannot be self-joined.")


def get(session, method, **params):
    """One GET against a read method. Returns (body, headers)."""
    res = session.get(API + method, params=params, timeout=30)
    return res.json(), res.headers


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True,
                    help="JSON object mapping channel ID to {visibility, created, recorded}")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:read, and groups:read to see the other side)",
                  args.token_env)
        return 2

    baseline = json.loads(open(args.baseline, encoding="utf-8").read())
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    body, headers = get(session, "auth.test")
    if body.get("ok") is not True:
        log.error("auth.test failed: %s", body.get("error"))
        return 2
    scopes = granted_scopes(headers.get("X-OAuth-Scopes"))
    log.info("grant: %s", " ".join(
        "%s=%s" % (s, "yes" if s in scopes else "no")
        for s in (PUBLIC_PAIR[0],) + PRIVATE_PAIR))

    changed = 0
    for channel_id in sorted(baseline):
        record = baseline[channel_id]
        info, _ = get(session, "conversations.info", channel=channel_id)
        state, detail = conversion_verdict(record, info, scopes)

        if state in ("unchanged", "not-visible"):
            log.info("%-22s %-12s %s", state, channel_id, detail)
            continue

        changed += 1
        log.warning("%-22s %-12s %s", state, channel_id, detail)
        log.warning("  recorded on %s", record.get("recorded") or "an unknown date")

        if info.get("ok") is True:
            identity, why = same_channel(record, info.get("channel") or {})
            log.warning("  identity: %s -- %s", identity, why)
            if identity == "different-channel":
                log.warning("  repair: this is a recycled ID, not a conversion. "
                            "Re-resolve the channel before changing any scopes.")
                continue
            route, how = access_route(info.get("channel") or {}, scopes)
            log.warning("  access: %s -- %s", route, how)
            if route == "needs-invite":
                log.warning("  repair: ask a member of %s to run /invite @YourApp",
                            channel_id)
            elif route == "no-scope":
                log.warning("  repair: add %s to Bot Token Scopes, reinstall, then "
                            "get the bot invited", ", ".join(PRIVATE_PAIR))
        else:
            log.warning("  repair: add %s to Bot Token Scopes and reinstall, then "
                        "re-run. If the channel reappears it was converted; if it "
                        "does not, it was deleted.", ", ".join(PRIVATE_PAIR))

    log.info("%d channel(s) checked, %d changed since the baseline",
             len(baseline), changed)
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-visibility-change.mjs",
"js": '''/**
 * Find the Slack channels that were converted to private under an integration.
 *
 * Read only. One auth.test for the granted-scope header, then one
 * conversations.info per channel, each compared against a baseline that records
 * what the channel used to be. Nothing is converted, joined or invited.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Conversion moves a channel from one scope pair to the other without moving its
// ID. That is the entire mechanism, and the reason nothing in a config file
// looks stale afterwards.
const PUBLIC_PAIR = ['channels:read', 'channels:history'];
const PRIVATE_PAIR = ['groups:read', 'groups:history'];

/** The scopes the token actually holds, off X-OAuth-Scopes. Pure. */
export function grantedScopes(header) {
  return new Set(String(header ?? '').split(',').map((s) => s.trim()).filter(Boolean));
}

/**
 * Compare a recorded visibility against a live conversations.info response.
 * Pure. A not-found on a recorded channel is reported as a candidate rather
 * than a conclusion: conversion and deletion look identical to a token that
 * cannot see private channels.
 */
export function conversionVerdict(record, body, scopes) {
  const was = String(record?.visibility ?? 'unrecorded').toLowerCase();

  if (body.ok !== true) {
    const error = body.error ?? '<no error field>';
    if (error !== 'channel_not_found') {
      return ['unreadable',
        `conversations.info answered 200 with ok: false, error=${error}. ` +
        'Visibility cannot be compared until that is resolved.'];
    }
    if (was !== 'public') {
      return ['not-visible',
        'channel_not_found, and the baseline does not record this channel as ' +
        'public, so there is nothing here to compare.'];
    }
    if (!scopes.has(PRIVATE_PAIR[0])) {
      return ['candidate-conversion',
        'the baseline recorded this channel as public and the ID now answers ' +
        `channel_not_found on a token without ${PRIVATE_PAIR[0]}. Conversion is ` +
        'the likeliest cause; deletion is the other one, and this token cannot ' +
        'tell them apart.'];
    }
    return ['gone',
      'the baseline recorded this channel as public and it is now invisible even ' +
      `with ${PRIVATE_PAIR[0]} granted, so a conversion would still have been ` +
      'readable. Something removed it.'];
  }

  const channel = body.channel ?? {};
  const now = channel.is_private ? 'private' : 'public';
  if (was === 'unrecorded') {
    return ['unrecorded',
      `no baseline visibility for this channel, so today's ${now} is a fact ` +
      'rather than a finding. Record it and re-run.'];
  }
  if (was === now) return ['unchanged', `${now}, and the baseline already recorded it ${was}`];
  if (was === 'public') {
    return ['converted-to-private',
      'recorded public, is_private is now true. Same ID, same history, and reads ' +
      `are governed by ${PRIVATE_PAIR[0]} from here on.`];
  }
  return ['converted-to-public',
    'recorded private and now public. Rare, because the product converts one ' +
    'way, but it widens who can read what your app writes here.'];
}

/**
 * Is this the conversation the baseline recorded, or a different one? Pure.
 * A conversion preserves both the ID and channel.created; a recycled name
 * preserves neither.
 */
export function sameChannel(record, channel) {
  const was = record?.created;
  const now = channel?.created;
  if (was === undefined || was === null || now === undefined || now === null) {
    return ['undatable',
      'no creation timestamp on one side, so the identity of this channel cannot ' +
      'be confirmed. Re-record the baseline.'];
  }
  if (Number(was) === Number(now)) {
    return ['same-channel',
      'created is unchanged, so this is the same conversation and whatever ' +
      'changed about it changed in place'];
  }
  return ['different-channel',
    `created moved from ${was} to ${now}. This ID is answering for a channel ` +
    'that did not exist when the baseline was recorded, so nothing here is a ' +
    'conversion.'];
}

/**
 * What way into this channel the app still has. Pure.
 * chat:write.public posts into public channels without membership and has no
 * private equivalent, so it is the route that closes.
 */
export function accessRoute(channel, scopes) {
  if (!channel?.is_private) {
    return ['public', 'public, so chat:write.public still reaches it without membership'];
  }
  const missing = PRIVATE_PAIR.filter((s) => !scopes.has(s));
  if (missing.length) {
    return ['no-scope',
      `private and the token is missing ${missing.join(', ')}. Add them to Bot ` +
      'Token Scopes and reinstall.'];
  }
  if (channel.is_member) {
    return ['member',
      'private, and the bot is a member, so the scopes are the only thing that ' +
      'had to change'];
  }
  return ['needs-invite',
    'private, scopes granted, and the bot is not a member. No API call fixes ' +
    'this: a private channel cannot be self-joined.'];
}

async function get(token, method, params) {
  const query = new URLSearchParams(params ?? {});
  const res = await fetch(`${API}${method}?${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return [await res.json(), res.headers];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function main() {
  const args = process.argv.slice(2);
  const baselinePath = arg(args, '--baseline');
  if (!baselinePath) {
    console.error('usage: --baseline channels.json [--token-env SLACK_BOT_TOKEN]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:read, and groups:read to see the other side)`);
    process.exitCode = 2;
    return;
  }

  const baseline = JSON.parse(await readFile(baselinePath, 'utf8'));
  const [auth, headers] = await get(token, 'auth.test');
  if (auth.ok !== true) {
    console.error(`auth.test failed: ${auth.error}`);
    process.exitCode = 2;
    return;
  }
  const scopes = grantedScopes(headers.get('x-oauth-scopes'));
  console.log('grant: ' + [PUBLIC_PAIR[0], ...PRIVATE_PAIR]
    .map((s) => `${s}=${scopes.has(s) ? 'yes' : 'no'}`).join(' '));

  let changed = 0;
  for (const channelId of Object.keys(baseline).sort()) {
    const record = baseline[channelId];
    const [info] = await get(token, 'conversations.info', { channel: channelId });
    const [state, detail] = conversionVerdict(record, info, scopes);

    if (state === 'unchanged' || state === 'not-visible') {
      console.log(`${state.padEnd(22)} ${channelId.padEnd(12)} ${detail}`);
      continue;
    }

    changed += 1;
    console.warn(`${state.padEnd(22)} ${channelId.padEnd(12)} ${detail}`);
    console.warn(`  recorded on ${record.recorded ?? 'an unknown date'}`);

    if (info.ok === true) {
      const [identity, why] = sameChannel(record, info.channel ?? {});
      console.warn(`  identity: ${identity} -- ${why}`);
      if (identity === 'different-channel') {
        console.warn('  repair: this is a recycled ID, not a conversion. ' +
                     'Re-resolve the channel before changing any scopes.');
        continue;
      }
      const [route, how] = accessRoute(info.channel ?? {}, scopes);
      console.warn(`  access: ${route} -- ${how}`);
      if (route === 'needs-invite') {
        console.warn(`  repair: ask a member of ${channelId} to run /invite @YourApp`);
      } else if (route === 'no-scope') {
        console.warn(`  repair: add ${PRIVATE_PAIR.join(', ')} to Bot Token Scopes, ` +
                     'reinstall, then get the bot invited');
      }
    } else {
      console.warn(`  repair: add ${PRIVATE_PAIR.join(', ')} to Bot Token Scopes and ` +
                   'reinstall, then re-run. If the channel reappears it was ' +
                   'converted; if it does not, it was deleted.');
    }
  }

  console.log(`${Object.keys(baseline).length} channel(s) checked, ${changed} changed ` +
              'since the baseline');
  process.exitCode = changed ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing baseline.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests pin the two places this could overclaim. A <code>channel_not_found</code> on a recorded public channel has to come back as <code>candidate-conversion</code> and never as a conversion, because a deletion produces exactly the same response; and a channel whose <code>created</code> timestamp has moved has to be rejected as a different conversation before any verdict about visibility is believed. The rest checks that an unchanged private channel stays boring.",
"test_py_file": "test_slack_visibility_change.py",
"test_py": '''from slack_visibility_change import (access_route, conversion_verdict,
                                      granted_scopes, same_channel)

PUBLIC_ONLY = granted_scopes("channels:read,channels:history,chat:write.public")
BOTH = granted_scopes("channels:read,groups:read,groups:history")
WAS_PUBLIC = {"visibility": "public", "created": 1451648400, "recorded": "2026-01-04"}


def ok(**channel):
    return {"ok": True, "channel": dict({"id": "C01ABCDE9", "created": 1451648400},
                                        **channel)}


def test_a_channel_that_matches_its_baseline_is_not_a_finding():
    state, _ = conversion_verdict({"visibility": "private"},
                                  ok(is_private=True), BOTH)
    assert state == "unchanged"


def test_recorded_public_and_now_private_is_the_headline():
    state, detail = conversion_verdict(WAS_PUBLIC, ok(is_private=True), BOTH)
    assert state == "converted-to-private"
    assert "Same ID" in detail


def test_not_found_without_groups_read_is_a_candidate_not_a_conclusion():
    state, detail = conversion_verdict(
        WAS_PUBLIC, {"ok": False, "error": "channel_not_found"}, PUBLIC_ONLY)
    assert state == "candidate-conversion"
    assert "deletion" in detail


def test_not_found_with_groups_read_rules_conversion_out():
    state, _ = conversion_verdict(
        WAS_PUBLIC, {"ok": False, "error": "channel_not_found"}, BOTH)
    assert state == "gone"


def test_another_error_is_not_a_visibility_answer_at_all():
    state, _ = conversion_verdict(
        WAS_PUBLIC, {"ok": False, "error": "ratelimited"}, BOTH)
    assert state == "unreadable"


def test_a_channel_with_no_recorded_visibility_produces_a_fact_not_a_finding():
    state, _ = conversion_verdict({}, ok(is_private=True), BOTH)
    assert state == "unrecorded"


def test_a_moved_creation_timestamp_means_this_is_not_the_same_channel():
    identity, detail = same_channel(WAS_PUBLIC, {"created": 1770000000})
    assert identity == "different-channel"
    assert "did not exist when the baseline" in detail


def test_an_unchanged_creation_timestamp_confirms_an_in_place_change():
    assert same_channel(WAS_PUBLIC, {"created": 1451648400})[0] == "same-channel"


def test_identity_is_undatable_when_the_baseline_never_recorded_created():
    assert same_channel({"visibility": "public"}, {"created": 1451648400})[0] == "undatable"


def test_a_private_channel_without_the_scope_pair_names_what_is_missing():
    route, detail = access_route({"is_private": True}, PUBLIC_ONLY)
    assert route == "no-scope"
    assert "groups:history" in detail


def test_scopes_granted_and_no_membership_needs_a_person():
    route, detail = access_route({"is_private": True, "is_member": False}, BOTH)
    assert route == "needs-invite"
    assert "cannot be self-joined" in detail


def test_a_still_public_channel_keeps_the_write_public_route():
    route, detail = access_route({"is_private": False}, PUBLIC_ONLY)
    assert route == "public"
    assert "chat:write.public" in detail
''',
"test_js_file": "slack-visibility-change.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { accessRoute, conversionVerdict, grantedScopes, sameChannel }
  from './slack-visibility-change.mjs';

const PUBLIC_ONLY = grantedScopes('channels:read,channels:history,chat:write.public');
const BOTH = grantedScopes('channels:read,groups:read,groups:history');
const WAS_PUBLIC = { visibility: 'public', created: 1451648400, recorded: '2026-01-04' };

const ok = (channel) => ({
  ok: true,
  channel: { id: 'C01ABCDE9', created: 1451648400, ...channel },
});

test('a channel that matches its baseline is not a finding', () => {
  const [state] = conversionVerdict({ visibility: 'private' }, ok({ is_private: true }), BOTH);
  assert.equal(state, 'unchanged');
});

test('recorded public and now private is the headline', () => {
  const [state, detail] = conversionVerdict(WAS_PUBLIC, ok({ is_private: true }), BOTH);
  assert.equal(state, 'converted-to-private');
  assert.match(detail, /Same ID/);
});

test('not found without groups read is a candidate not a conclusion', () => {
  const [state, detail] = conversionVerdict(
    WAS_PUBLIC, { ok: false, error: 'channel_not_found' }, PUBLIC_ONLY);
  assert.equal(state, 'candidate-conversion');
  assert.match(detail, /deletion/);
});

test('not found with groups read rules conversion out', () => {
  const [state] = conversionVerdict(
    WAS_PUBLIC, { ok: false, error: 'channel_not_found' }, BOTH);
  assert.equal(state, 'gone');
});

test('another error is not a visibility answer at all', () => {
  const [state] = conversionVerdict(WAS_PUBLIC, { ok: false, error: 'ratelimited' }, BOTH);
  assert.equal(state, 'unreadable');
});

test('a channel with no recorded visibility produces a fact not a finding', () => {
  const [state] = conversionVerdict({}, ok({ is_private: true }), BOTH);
  assert.equal(state, 'unrecorded');
});

test('a moved creation timestamp means this is not the same channel', () => {
  const [identity, detail] = sameChannel(WAS_PUBLIC, { created: 1770000000 });
  assert.equal(identity, 'different-channel');
  assert.match(detail, /did not exist when the baseline/);
});

test('an unchanged creation timestamp confirms an in place change', () => {
  assert.equal(sameChannel(WAS_PUBLIC, { created: 1451648400 })[0], 'same-channel');
});

test('identity is undatable when the baseline never recorded created', () => {
  assert.equal(sameChannel({ visibility: 'public' }, { created: 1451648400 })[0], 'undatable');
});

test('a private channel without the scope pair names what is missing', () => {
  const [route, detail] = accessRoute({ is_private: true }, PUBLIC_ONLY);
  assert.equal(route, 'no-scope');
  assert.match(detail, /groups:history/);
});

test('scopes granted and no membership needs a person', () => {
  const [route, detail] = accessRoute({ is_private: true, is_member: false }, BOTH);
  assert.equal(route, 'needs-invite');
  assert.match(detail, /cannot be self-joined/);
});

test('a still public channel keeps the write public route', () => {
  const [route, detail] = accessRoute({ is_private: false }, PUBLIC_ONLY);
  assert.equal(route, 'public');
  assert.match(detail, /chat:write\\.public/);
});
''',
"faq": [
 ("How do I tell a conversion from a channel that was simply deleted?",
  "With groups:read granted you can tell immediately: a converted channel is still readable and reports is_private true, so if it is invisible even with the scope, it is not a conversion. Without that scope the two are genuinely identical, both arriving as channel_not_found, and no read-only token separates them. The honest sequence is to add the scope, reinstall, and re-run: if the channel reappears it was converted."),
 ("Does the channel ID change when a channel is converted to private?",
  "No. The ID, the history, the members, the pins and the permalinks all survive, which is exactly why this is hard to spot. Older documentation and some client libraries talk about private channels having G-prefixed IDs, but a converted channel keeps the C-prefixed ID it was created with, so prefix-sniffing is not a reliable test of visibility."),
 ("Our app posts with chat:write.public and never joins channels. What changes?",
  "That route disappears. chat:write.public is defined for public channels, and there is no private equivalent, so after a conversion the app has no way to post until a member invites it. This is the case worth checking first, because an app built that way has never been a member of anything and the invite step has never been in anybody's runbook."),
 ("Can the bot convert the channel back, or join itself?",
  "Neither. Conversion back to public is not offered to ordinary admins in the product, and conversations.join works on public channels only, so a private channel is only ever entered by invitation from someone already inside it. Both halves of the repair are human actions, which is why the script prints them rather than pretending it can do them."),
 ("Where does the baseline come from if we never recorded one?",
  "Generate it on a day the integration is working: for each configured channel, store the is_private flag and the created timestamp that conversations.info returns, plus today's date. Commit it beside the configuration. It is worth doing even though it feels redundant, because without a recorded past there is no way to distinguish a channel that changed from a channel that was always like this."),
],
"related": [
 ("/slack/private-channel-invisible/", "a private channel the token never could see"),
 ("/slack/bot-not-in-channel/", "visible, and still not a member"),
 ("/slack/missing-scope-on-read/", "when Slack does name what was needed"),
],
"citations": [CITE_CONV_INFO, CITE_SCOPES, CITE_AUTH_TEST, CITE_CONV_API],
},

{
"slug": "membership-lost-silently",
"title": "Membership lost: the bot was removed and nothing said so",
"description": "Any channel member can remove your app and nobody is told. Diff the bot's conversation set against last run's snapshot instead of waiting for a send to fail.",
"h1": "Membership lost: the bot was removed and nothing said so",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack bot removed from channel", "slack member_left_channel event",
             "slack users.conversations membership audit", "slack bot kicked no notification",
             "slack digest stopped posting"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a snapshot from the previous run",
"lead": "The Monday digest ran for eleven months. Somebody tidied up the channel membership list three weeks ago, the app was in it, and out it went. No email, no error, no ticket. The job still runs, still exits 0, and the only trace is a <code>not_in_channel</code> in a response body nobody reads. The state is easy to check. Nobody checked, because nothing asked them to.",
"short_answer": """<p>Removal is not an event your app finds out about unless it asked to. Any member can remove an app with <code>/kick</code> or from the channel's integrations panel; Slack emits <code>member_left_channel</code>, but only to apps subscribed to it and only while their event delivery is healthy. Nothing is sent to the app owner, nothing appears in the app configuration, and the next send returns <code>ok: false</code> inside an HTTP 200.</p>
<p>So the check has to be a scheduled diff rather than an error handler. One paginated <code>users.conversations</code> for the bot user returns the authoritative set of conversations it currently belongs to. Compare that against the set the previous run stored and the finding is a transition with a window attached: these channels were held last Tuesday and are not held now. The script below does that, and separates it firmly from channels the bot never had.</p>""",
"problem": """<p>The permission model is the source of this. Adding an app to a channel is an ordinary member action, and so is removing it &mdash; there is no admin gate, no confirmation naming what depends on it, and no audit trail visible to the app. Someone spring-cleaning a channel's member list sees a list of names, one of which is a robot, and the robot does not look like it is doing anything. It is doing something once a day at 09:00.</p>
<p>What turns a small mistake into a long outage is that the loss is undetectable from every direction at once. The send fails inside a 200 so the process exits clean. The absence of a daily message is not something anybody alerts on, because alerting on absence requires having decided in advance what should be present. And the humans in the channel do not report it, because a message that stops arriving reads as a message that was never scheduled.</p>
<p>Then the discovery is accidental and late. Someone asks why they have not seen the digest, somebody else says they thought it had been turned off, and the reconstruction begins with three weeks of missing history and no idea which of the fifty channels the app targets also lost it. That last part is the real cost: without a set diff, finding out means checking every channel by hand.</p>""",
"why": """<p><strong>A state check answers the wrong question.</strong> "Is the bot in this channel today" is worth knowing, but it does not tell you whether something changed, when, or whether it was ever true. Reading <code>is_member</code> on a channel the bot was never invited to and reading it on a channel it was removed from yesterday produce the same false, and those two findings go to different people.</p>
<p><strong>The snapshot is the only clock you have.</strong> The Web API does not report when membership changed &mdash; there is no per-channel joined-at field on a bot's conversation list. Storing the previous run's set turns the finding into a window: it happened between the snapshot and now. That window is as tight as your schedule, which is the argument for running this hourly rather than when somebody complains.</p>
<p><strong><code>users.conversations</code> beats a loop over targets.</strong> One paginated call for the bot user returns every conversation it belongs to across public channels, private channels, DMs and group DMs. Per-channel <code>conversations.info</code> costs a call each and misses everything not on the list, which is exactly the case where the bot is in channels nobody knows about.</p>
<p><strong>The events that would have told you have to be subscribed in advance.</strong> <code>member_left_channel</code> fires on removal and <code>channel_left</code> fires for the bot itself, and neither is on by default. A bot token cannot read which events your app subscribes to &mdash; that lives in app configuration behind a different credential &mdash; so the script takes the list from your manifest and tells you what is missing rather than pretending to discover it.</p>
<p><strong>Removal and never-joined need separating in the report, not in the reader's head.</strong> A channel that was never held is a configuration gap and its repair is an initial invite. A channel that was held and is now lost is an incident with a date, and its repair includes finding out who removed it and why, because the second removal usually follows the first.</p>""",
"steps": [
 {"h": "Get the bot user ID from the token in hand",
  "body": """<p><code>auth.test</code> needs no scopes and returns <code>user_id</code>, which for a bot token is the bot user. Everything else keys off that ID, and it also confirms which workspace this credential actually points at.</p>"""},
 {"h": "Take the authoritative set in one paginated pass",
  "body": """<p><code>users.conversations?user=&lt;bot&gt;&amp;types=public_channel,private_channel&amp;limit=1000</code>, following <code>next_cursor</code> to the end. Private channels only appear with <code>groups:read</code> granted, so a run without it reports a set that is missing exactly the channels people are most careful about.</p>"""},
 {"h": "Diff against the previous run, not against the config",
  "body": """<p>Three sets go in: what you expect, what you had last time, and what you have now. Four findings come out. Lost is the incident. Never-held is a configuration gap. Regained means somebody already fixed it. Undeclared means the bot is in channels your configuration does not mention, which is information rather than a fault.</p>"""},
 {"h": "Say how wide the window is, and admit when it is useless",
  "body": """<p>A snapshot from six hours ago dates the removal to within six hours. One from four months ago dates it to within four months, which is not a date. The script grades its own snapshot and says plainly when the answer it can give is too vague to act on.</p>"""},
 {"h": "Check the events that should have raised this in real time",
  "body": """<p>Pass the event list from your app manifest. If <code>member_left_channel</code> is missing, this run is the only thing that will ever notice a removal, and its resolution is your cron schedule. Subscribing turns a scheduled diff into an alert.</p>"""},
 {"h": "Print the new snapshot and store it",
  "body": """<p>The script writes nothing, so the closing line is the snapshot itself, ready to redirect into the file the next run will read. Keeping every snapshot rather than overwriting turns the audit into a history of who your app lost access to and when.</p>"""},
],
"verify": """<p>After the re-invite, run it once to fix the drift and once more to confirm the set is stable.</p>
<pre><code class="language-bash">python3 slack_membership_drift.py --expected targets.json --snapshot last.json
# bot user U07BOTAPP1, 24 conversation(s) currently held
# window: tight -- the previous snapshot is 1 day old
# held        C01ABCDE9  membership unchanged since the snapshot
# 3 expected, 0 lost, 0 never held</code></pre>""",
"code_intro": "Everything interesting is a set operation. <code>diff_membership</code> sorts the expected channels into lost, never-held, regained and held, which is the distinction the whole note turns on. <code>snapshot_window</code> grades how much the previous snapshot is actually worth and refuses to imply precision it does not have. <code>alerting_gap</code> takes the event list from your manifest, because a bot token cannot read your app's subscriptions and inventing that answer would be worse than asking for it.",
"py_file": "slack_membership_drift.py",
"py": '''"""Report Slack channels the bot has lost membership of since the last run.

Read only. One auth.test and one paginated users.conversations, diffed against
the snapshot the previous run printed. Nothing is joined and nobody is invited:
the script names what was lost, dates it as tightly as the snapshot allows, and
prints the new snapshot for you to store.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_membership_drift")

API = "https://slack.com/api/"

# Neither of these is subscribed by default, and a bot token cannot read which
# events an app subscribes to: that lives in app configuration behind an app
# configuration token. So the list is supplied, not discovered.
WATCHERS = {
    "member_left_channel": "fires when any member, your app included, leaves a channel",
    "channel_left": "fires when the app itself is removed from a public channel",
    "group_left": "the private channel equivalent of channel_left",
}


def diff_membership(expected, previous, current):
    """Sort the expected channels by what happened to membership. Pure.

    Returns a dict of sorted lists. The distinction that matters is lost against
    never-held: both are "the bot is not in this channel today" and they are a
    different incident with a different repair and a different owner.
    """
    expected, previous, current = set(expected), set(previous), set(current)
    return {
        "lost": sorted((expected & previous) - current),
        "never": sorted(expected - previous - current),
        "regained": sorted((expected & current) - previous),
        "held": sorted(expected & current & previous),
        "undeclared": sorted(current - expected),
    }


def snapshot_window(recorded_at, now):
    """How much the previous snapshot is worth as a clock. Pure.

    Returns (quality, detail). A removal can only be dated to the gap between the
    snapshot and this run, so a stale snapshot does not produce a vague date, it
    produces no date at all, and the script says so rather than implying one.
    """
    if recorded_at is None:
        return ("none",
                "no previous snapshot, so nothing this run reports is a change. "
                "Store the snapshot below and the next run can date things.")
    days = (now - recorded_at).days
    if days < 0:
        return ("future",
                "the snapshot is dated after this run. Something is wrong with a "
                "clock and no window can be derived from it.")
    if days <= 2:
        return ("tight", "the previous snapshot is %d day(s) old" % days)
    if days <= 30:
        return ("wide",
                "the previous snapshot is %d days old, so a removal can only be "
                "placed inside that month" % days)
    return ("useless",
            "the previous snapshot is %d days old. That is a window, not a date. "
            "Run this on a schedule and the window becomes the schedule." % days)


def alerting_gap(subscribed):
    """Which of the events that would have raised this in real time are missing.

    Pure, and deliberately fed rather than fetched: the subscription list is app
    configuration and a runtime bot token has no read access to it. Returns
    (state, rows) with rows as [(event, why it matters), ...].
    """
    have = {str(e).strip() for e in (subscribed or []) if str(e).strip()}
    missing = [(name, why) for name, why in sorted(WATCHERS.items()) if name not in have]
    if not missing:
        return ("covered", [])
    if "member_left_channel" in {name for name, _ in missing}:
        return ("blind", missing)
    return ("partial", missing)


def get(session, method, **params):
    body = session.get(API + method, params=params, timeout=30).json()
    if body.get("ok") is not True:
        raise SystemExit("%s answered 200 with ok: false, error=%s"
                         % (method, body.get("error")))
    return body


def bot_conversations(session, user_id):
    """Every conversation the bot currently belongs to. GET, paginated."""
    out, cursor = [], ""
    while True:
        params = {"user": user_id, "types": "public_channel,private_channel",
                  "limit": 1000, "exclude_archived": "false"}
        if cursor:
            params["cursor"] = cursor
        body = get(session, "users.conversations", **params)
        out.extend(c.get("id") for c in (body.get("channels") or []))
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expected", required=True,
                    help="JSON list of channel IDs the integration targets")
    ap.add_argument("--snapshot", help="JSON snapshot printed by the previous run")
    ap.add_argument("--events", help="JSON list of the events your app manifest subscribes to")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:read and groups:read)", args.token_env)
        return 2

    expected = json.loads(open(args.expected, encoding="utf-8").read())
    previous, recorded_at = [], None
    if args.snapshot:
        snap = json.loads(open(args.snapshot, encoding="utf-8").read())
        previous = snap.get("channels") or []
        stamp = snap.get("recorded")
        if stamp:
            recorded_at = datetime.fromisoformat(stamp)
    subscribed = []
    if args.events:
        subscribed = json.loads(open(args.events, encoding="utf-8").read())

    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})
    me = get(session, "auth.test")
    current = bot_conversations(session, me.get("user_id"))
    log.info("bot user %s, %d conversation(s) currently held",
             me.get("user_id"), len(current))

    now = datetime.now(timezone.utc)
    quality, detail = snapshot_window(recorded_at, now)
    log.info("window: %s -- %s", quality, detail)

    groups = diff_membership(expected, previous, current)
    for channel_id in groups["lost"]:
        log.warning("lost        %-12s held at the snapshot, not held now. Somebody "
                    "removed the app.", channel_id)
        log.warning("  repair: ask a member to run /invite @YourApp in %s, then find "
                    "out who removed it", channel_id)
    for channel_id in groups["never"]:
        log.warning("never-held  %-12s not held at the snapshot either, so this was "
                    "never set up rather than lost", channel_id)
    for channel_id in groups["regained"]:
        log.info("regained    %-12s not held at the snapshot, held now", channel_id)
    for channel_id in groups["held"]:
        log.info("held        %-12s membership unchanged since the snapshot", channel_id)
    if groups["undeclared"]:
        log.info("the bot is also in %d conversation(s) your target list does not "
                 "mention", len(groups["undeclared"]))

    state, missing = alerting_gap(subscribed)
    if state != "covered":
        log.warning("alerting: %s -- this run is the only thing that notices", state)
        for name, why in missing:
            log.warning("  subscribe to %-22s %s", name, why)

    print(json.dumps({"recorded": now.isoformat(), "channels": sorted(current)},
                     indent=2))
    log.info("%d expected, %d lost, %d never held",
             len(expected), len(groups["lost"]), len(groups["never"]))
    return 1 if groups["lost"] or groups["never"] else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-membership-drift.mjs",
"js": '''/**
 * Report Slack channels the bot has lost membership of since the last run.
 *
 * Read only. One auth.test and one paginated users.conversations, diffed
 * against the snapshot the previous run printed. Nothing is joined and nobody
 * is invited: the script names what was lost and prints the new snapshot.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Neither of these is subscribed by default, and a bot token cannot read which
// events an app subscribes to: that lives in app configuration behind an app
// configuration token. So the list is supplied, not discovered.
const WATCHERS = {
  channel_left: 'fires when the app itself is removed from a public channel',
  group_left: 'the private channel equivalent of channel_left',
  member_left_channel: 'fires when any member, your app included, leaves a channel',
};

/**
 * Sort the expected channels by what happened to membership. Pure.
 * lost against never-held is the distinction that matters: both are "not in
 * this channel today" and they are different incidents with different owners.
 */
export function diffMembership(expected, previous, current) {
  const exp = new Set(expected);
  const prev = new Set(previous);
  const cur = new Set(current);
  const sort = (xs) => [...xs].sort();
  return {
    lost: sort([...exp].filter((c) => prev.has(c) && !cur.has(c))),
    never: sort([...exp].filter((c) => !prev.has(c) && !cur.has(c))),
    regained: sort([...exp].filter((c) => cur.has(c) && !prev.has(c))),
    held: sort([...exp].filter((c) => cur.has(c) && prev.has(c))),
    undeclared: sort([...cur].filter((c) => !exp.has(c))),
  };
}

/**
 * How much the previous snapshot is worth as a clock. Pure.
 * A stale snapshot does not produce a vague date, it produces no date at all.
 */
export function snapshotWindow(recordedAt, now) {
  if (recordedAt === null || recordedAt === undefined) {
    return ['none',
      'no previous snapshot, so nothing this run reports is a change. Store the ' +
      'snapshot below and the next run can date things.'];
  }
  const days = Math.floor((now - recordedAt) / 86400000);
  if (days < 0) {
    return ['future',
      'the snapshot is dated after this run. Something is wrong with a clock and ' +
      'no window can be derived from it.'];
  }
  if (days <= 2) return ['tight', `the previous snapshot is ${days} day(s) old`];
  if (days <= 30) {
    return ['wide',
      `the previous snapshot is ${days} days old, so a removal can only be placed ` +
      'inside that month'];
  }
  return ['useless',
    `the previous snapshot is ${days} days old. That is a window, not a date. Run ` +
    'this on a schedule and the window becomes the schedule.'];
}

/**
 * Which of the events that would have raised this in real time are missing.
 * Pure, and deliberately fed rather than fetched: the subscription list is app
 * configuration and a runtime bot token has no read access to it.
 */
export function alertingGap(subscribed) {
  const have = new Set((subscribed ?? []).map((e) => String(e).trim()).filter(Boolean));
  const missing = Object.entries(WATCHERS)
    .filter(([name]) => !have.has(name))
    .sort(([a], [b]) => a.localeCompare(b));
  if (missing.length === 0) return ['covered', []];
  if (missing.some(([name]) => name === 'member_left_channel')) return ['blind', missing];
  return ['partial', missing];
}

async function get(token, method, params) {
  const query = new URLSearchParams(params ?? {});
  const res = await fetch(`${API}${method}?${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const body = await res.json();
  if (body.ok !== true) {
    throw new Error(`${method} answered 200 with ok: false, error=${body.error}`);
  }
  return body;
}

async function botConversations(token, userId) {
  const out = [];
  let cursor = '';
  for (;;) {
    const params = {
      user: userId,
      types: 'public_channel,private_channel',
      limit: '1000',
      exclude_archived: 'false',
    };
    if (cursor) params.cursor = cursor;
    const body = await get(token, 'users.conversations', params);
    out.push(...(body.channels ?? []).map((c) => c.id));
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
  const expectedPath = arg(args, '--expected');
  if (!expectedPath) {
    console.error('usage: --expected targets.json [--snapshot last.json] [--events events.json]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:read and groups:read)`);
    process.exitCode = 2;
    return;
  }

  const expected = JSON.parse(await readFile(expectedPath, 'utf8'));
  let previous = [];
  let recordedAt = null;
  const snapshotPath = arg(args, '--snapshot');
  if (snapshotPath) {
    const snap = JSON.parse(await readFile(snapshotPath, 'utf8'));
    previous = snap.channels ?? [];
    if (snap.recorded) recordedAt = new Date(snap.recorded);
  }
  const eventsPath = arg(args, '--events');
  const subscribed = eventsPath ? JSON.parse(await readFile(eventsPath, 'utf8')) : [];

  const me = await get(token, 'auth.test');
  const current = await botConversations(token, me.user_id);
  console.log(`bot user ${me.user_id}, ${current.length} conversation(s) currently held`);

  const now = new Date();
  const [quality, detail] = snapshotWindow(recordedAt, now);
  console.log(`window: ${quality} -- ${detail}`);

  const groups = diffMembership(expected, previous, current);
  for (const channelId of groups.lost) {
    console.warn(`lost        ${channelId.padEnd(12)} held at the snapshot, not held ` +
                 'now. Somebody removed the app.');
    console.warn(`  repair: ask a member to run /invite @YourApp in ${channelId}, then ` +
                 'find out who removed it');
  }
  for (const channelId of groups.never) {
    console.warn(`never-held  ${channelId.padEnd(12)} not held at the snapshot either, ` +
                 'so this was never set up rather than lost');
  }
  for (const channelId of groups.regained) {
    console.log(`regained    ${channelId.padEnd(12)} not held at the snapshot, held now`);
  }
  for (const channelId of groups.held) {
    console.log(`held        ${channelId.padEnd(12)} membership unchanged since the snapshot`);
  }
  if (groups.undeclared.length) {
    console.log(`the bot is also in ${groups.undeclared.length} conversation(s) your ` +
                'target list does not mention');
  }

  const [state, missing] = alertingGap(subscribed);
  if (state !== 'covered') {
    console.warn(`alerting: ${state} -- this run is the only thing that notices`);
    for (const [name, why] of missing) {
      console.warn(`  subscribe to ${name.padEnd(22)} ${why}`);
    }
  }

  console.log(JSON.stringify(
    { recorded: now.toISOString(), channels: [...current].sort() }, null, 2));
  console.log(`${expected.length} expected, ${groups.lost.length} lost, ` +
              `${groups.never.length} never held`);
  process.exitCode = groups.lost.length || groups.never.length ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing target list.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The diff is four buckets and the tests exist to keep two of them apart: a channel held at the snapshot and missing now is <code>lost</code>, and a channel missing from both is <code>never</code>. Collapsing those is the failure mode this whole note argues against. The window tests pin that a snapshot old enough to be meaningless is labelled as such rather than reported as a date, and the alerting tests pin that a missing <code>member_left_channel</code> is the difference between partial cover and none.",
"test_py_file": "test_slack_membership_drift.py",
"test_py": '''from datetime import datetime, timedelta, timezone

from slack_membership_drift import alerting_gap, diff_membership, snapshot_window

NOW = datetime(2026, 8, 30, tzinfo=timezone.utc)
EXPECTED = ["C01ALERTS1", "C02DIGEST2", "C03NEVER33"]


def test_a_channel_held_before_and_missing_now_is_a_loss():
    groups = diff_membership(EXPECTED, ["C01ALERTS1", "C02DIGEST2"], ["C02DIGEST2"])
    assert groups["lost"] == ["C01ALERTS1"]


def test_a_channel_missing_from_both_sets_was_never_held():
    groups = diff_membership(EXPECTED, ["C01ALERTS1", "C02DIGEST2"], ["C02DIGEST2"])
    assert groups["never"] == ["C03NEVER33"]
    assert "C03NEVER33" not in groups["lost"]


def test_a_channel_gained_since_the_snapshot_is_not_a_finding():
    groups = diff_membership(EXPECTED, [], ["C01ALERTS1"])
    assert groups["regained"] == ["C01ALERTS1"]
    assert groups["lost"] == []


def test_conversations_outside_the_target_list_are_reported_separately():
    groups = diff_membership(["C01ALERTS1"], ["C01ALERTS1"],
                             ["C01ALERTS1", "C09RANDOM9"])
    assert groups["undeclared"] == ["C09RANDOM9"]
    assert groups["held"] == ["C01ALERTS1"]


def test_with_no_snapshot_nothing_can_be_called_a_loss():
    groups = diff_membership(EXPECTED, [], [])
    assert groups["lost"] == []
    assert len(groups["never"]) == 3


def test_a_recent_snapshot_dates_the_removal_tightly():
    quality, _ = snapshot_window(NOW - timedelta(days=1), NOW)
    assert quality == "tight"


def test_a_month_old_snapshot_is_a_window_not_a_date():
    assert snapshot_window(NOW - timedelta(days=20), NOW)[0] == "wide"


def test_an_ancient_snapshot_says_so_rather_than_implying_precision():
    quality, detail = snapshot_window(NOW - timedelta(days=200), NOW)
    assert quality == "useless"
    assert "not a date" in detail


def test_a_missing_snapshot_is_its_own_state():
    quality, detail = snapshot_window(None, NOW)
    assert quality == "none"
    assert "nothing this run reports is a change" in detail


def test_a_snapshot_from_the_future_is_a_clock_problem():
    assert snapshot_window(NOW + timedelta(days=3), NOW)[0] == "future"


def test_without_member_left_channel_nothing_raises_in_real_time():
    state, missing = alerting_gap(["app_mention"])
    assert state == "blind"
    assert "member_left_channel" in dict(missing)


def test_the_key_event_alone_is_partial_cover_rather_than_none():
    state, missing = alerting_gap(["member_left_channel"])
    assert state == "partial"
    assert "member_left_channel" not in dict(missing)


def test_all_three_events_subscribed_needs_no_warning():
    state, missing = alerting_gap(
        ["member_left_channel", "channel_left", "group_left"])
    assert state == "covered"
    assert missing == []
''',
"test_js_file": "slack-membership-drift.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { alertingGap, diffMembership, snapshotWindow }
  from './slack-membership-drift.mjs';

const NOW = new Date('2026-08-30T00:00:00Z');
const EXPECTED = ['C01ALERTS1', 'C02DIGEST2', 'C03NEVER33'];
const daysBefore = (n) => new Date(NOW.getTime() - n * 86400000);

test('a channel held before and missing now is a loss', () => {
  const groups = diffMembership(EXPECTED, ['C01ALERTS1', 'C02DIGEST2'], ['C02DIGEST2']);
  assert.deepEqual(groups.lost, ['C01ALERTS1']);
});

test('a channel missing from both sets was never held', () => {
  const groups = diffMembership(EXPECTED, ['C01ALERTS1', 'C02DIGEST2'], ['C02DIGEST2']);
  assert.deepEqual(groups.never, ['C03NEVER33']);
  assert.ok(!groups.lost.includes('C03NEVER33'));
});

test('a channel gained since the snapshot is not a finding', () => {
  const groups = diffMembership(EXPECTED, [], ['C01ALERTS1']);
  assert.deepEqual(groups.regained, ['C01ALERTS1']);
  assert.deepEqual(groups.lost, []);
});

test('conversations outside the target list are reported separately', () => {
  const groups = diffMembership(['C01ALERTS1'], ['C01ALERTS1'],
    ['C01ALERTS1', 'C09RANDOM9']);
  assert.deepEqual(groups.undeclared, ['C09RANDOM9']);
  assert.deepEqual(groups.held, ['C01ALERTS1']);
});

test('with no snapshot nothing can be called a loss', () => {
  const groups = diffMembership(EXPECTED, [], []);
  assert.deepEqual(groups.lost, []);
  assert.equal(groups.never.length, 3);
});

test('a recent snapshot dates the removal tightly', () => {
  assert.equal(snapshotWindow(daysBefore(1), NOW)[0], 'tight');
});

test('a month old snapshot is a window not a date', () => {
  assert.equal(snapshotWindow(daysBefore(20), NOW)[0], 'wide');
});

test('an ancient snapshot says so rather than implying precision', () => {
  const [quality, detail] = snapshotWindow(daysBefore(200), NOW);
  assert.equal(quality, 'useless');
  assert.match(detail, /not a date/);
});

test('a missing snapshot is its own state', () => {
  const [quality, detail] = snapshotWindow(null, NOW);
  assert.equal(quality, 'none');
  assert.match(detail, /nothing this run reports is a change/);
});

test('a snapshot from the future is a clock problem', () => {
  assert.equal(snapshotWindow(daysBefore(-3), NOW)[0], 'future');
});

test('without member left channel nothing raises in real time', () => {
  const [state, missing] = alertingGap(['app_mention']);
  assert.equal(state, 'blind');
  assert.ok(Object.fromEntries(missing).member_left_channel);
});

test('the key event alone is partial cover rather than none', () => {
  const [state, missing] = alertingGap(['member_left_channel']);
  assert.equal(state, 'partial');
  assert.ok(!Object.fromEntries(missing).member_left_channel);
});

test('all three events subscribed needs no warning', () => {
  const [state, missing] = alertingGap(
    ['member_left_channel', 'channel_left', 'group_left']);
  assert.equal(state, 'covered');
  assert.deepEqual(missing, []);
});
''',
"faq": [
 ("Who is allowed to remove an app from a channel?",
  "Any member of the channel, using /kick @YourApp or the integrations tab in the channel details. It is not an admin action and there is no confirmation step that names what depends on the app. That is why this is worth auditing on a schedule rather than treating as an unlikely event: the barrier to it happening is one person tidying a member list."),
 ("Does Slack notify the app or its owner when this happens?",
  "Not out of band. There is no email, nothing in the app configuration screen, and nothing in the install record. Slack does emit member_left_channel to apps subscribed to it, which is the real-time answer, but that subscription has to have been added in advance and event delivery has to be healthy for it to arrive."),
 ("Why diff a snapshot instead of just reading is_member on each channel?",
  "Because is_member answers what is true now and this note is about what changed. A false on a channel the bot was never invited to and a false on a channel it was removed from yesterday are the same value and completely different findings. The snapshot is also the only clock available: nothing in the API reports when a bot joined or left a conversation."),
 ("How often should this run?",
  "As often as you want the window to be. The script can only place a removal between the previous snapshot and this run, so an hourly job dates it to the hour and a quarterly one dates it to the quarter. Hourly is cheap here: users.conversations is one paginated call regardless of how many channels you target."),
 ("Can the script re-invite the bot itself?",
  "No, and it would need a write scope to try. conversations.join covers public channels only and would still be a write, and private channels can never be self-joined at all. The script prints the invite for a human, which is also the right shape socially: somebody removed the app on purpose often enough that walking back in unannounced is the wrong move."),
],
"related": [
 ("/slack/bot-not-in-channel/", "the state, rather than the transition"),
 ("/slack/http-200-ok-false/", "why the failed send exited zero"),
 ("/slack/event-subscriptions-auto-disabled/", "when the events stop arriving too"),
],
"citations": [CITE_USERS_CONV, CITE_MEMBER_LEFT, CITE_AUTH_TEST, CITE_PAGINATION],
},

{
"slug": "dm-never-opened",
"title": "channel_not_found: the DM conversation was never opened",
"description": "A user ID is not a DM. Slack opens the conversation implicitly for some recipients and not others, so audit which of yours already have a D channel.",
"h1": "channel_not_found: the DM conversation was never opened",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack dm channel_not_found", "slack conversations.open users",
             "slack send dm to user id", "slack im:write scope", "slack D channel id"],
"deps": "Python 3.9+ with requests, or Node.js 18+; im:read to see the IM inventory",
"lead": "The onboarding bot DMs every new hire. It works for the twelve people who tried it during the pilot and fails for everybody since with <code>channel_not_found</code>, for a user ID copied straight out of the profile panel. Nothing is wrong with the ID. There is no conversation for it to be delivered into, because a direct message is a channel and nobody has ever opened this one.",
"short_answer": """<p>A DM is a conversation with its own <code>D</code>-prefixed ID. A user ID identifies a person, not a place to put a message. <code>chat.postMessage</code> will accept a <code>U</code> value and open the IM implicitly a lot of the time, which is why this works for the people who have already interacted with the app and fails for everyone else; the <code>files.*</code> family and the read methods never do it at all.</p>
<p>The supported sequence is <code>conversations.open?users=&lt;U...&gt;</code>, take <code>channel.id</code>, and post to that. <code>conversations.open</code> creates a conversation, so it is a write and this script will not call it &mdash; not even to probe. Instead it reads the IM inventory with <code>conversations.list?types=im</code>, which lists the DMs that already exist, and sorts your configured recipients into the ones that will deliver today and the ones nothing has ever been opened for.</p>""",
"problem": """<p>The reason this survives testing is that testing is done by people who have already used the app. A developer DMs themselves, it works. QA installs the app, clicks the shortcut, gets a reply, and the DM works for them from then on, because that interaction opened the conversation. Every one of those people has a <code>D</code> channel with the app and every new user does not, so the feature passes every check made by anyone who has ever touched it.</p>
<p>The inconsistency across methods finishes the job. <code>chat.postMessage</code> with a user ID is tolerant enough that a whole codebase gets written on the assumption that a user ID is an address. Then a feature is added that uploads a file to the same recipient, and <code>files.completeUploadExternal</code> demands a real channel ID and refuses the <code>U</code>. That reads as a bug in the new feature rather than as a wrong assumption in the old one.</p>
<p>The audit is awkward for an honest reason: the natural way to answer "does a DM exist with this person" is to call <code>conversations.open</code>, which answers by creating one. A read-only check cannot use it, and neither should a health check, because a probe that opens a hundred DMs is a probe that has just written to a hundred conversations. Reading the IM list instead is the version of this question that leaves no trace.</p>""",
"why": """<p><strong>Conversations are addressed, people are not.</strong> Every Slack method that takes a <code>channel</code> parameter wants a conversation ID, and a DM has one like any other conversation. The tolerance in <code>chat.postMessage</code> is a convenience layered on top, not a second addressing scheme, and it is the only place that convenience exists.</p>
<p><strong>The implicit open is not documented as a guarantee.</strong> It works often enough to look like a rule and fails for users who have never interacted with the app, for other bots, and for anything outside the messaging family. Depending on it means depending on a behaviour that varies by recipient, which is the hardest kind of bug to reproduce because it is a property of who you tested with.</p>
<p><strong>The D ID is stable, so cache it.</strong> Once a DM exists between the app and a user, its ID does not change. Storing it per user at the point the conversation is opened turns every later send into a plain channel post and removes the whole class of problem. Opening it on every send instead adds a call, and a write, to every message you send.</p>
<p><strong>Reading the IM inventory needs its own scope.</strong> <code>im:read</code> lets the token enumerate its DM conversations, <code>im:write</code> lets it open one, and <code>im:history</code> lets it read the messages. An audit run without <code>im:read</code> sees an empty inventory and would report every recipient as unopened, which is a wrong answer rather than a missing one, so the script checks the grant before it believes its own findings.</p>
<p><strong>Group DMs are a separate family.</strong> A conversation with several people is an mpim, opened by passing a comma-separated <code>users</code> list, governed by <code>mpim:read</code> and <code>mpim:write</code>. The scopes are separate from the one-to-one ones, so an app that DMs individuals fine can fail entirely on group DMs with nothing in common but the word "message".</p>""",
"steps": [
 {"h": "Read the grant before you read anything else",
  "body": """<p><code>auth.test</code>, then <code>X-OAuth-Scopes</code> off the response. Without <code>im:read</code> the inventory comes back empty and every recipient looks unopened, so the script reports that the audit itself is blind rather than producing a hundred confident false findings.</p>"""},
 {"h": "List the DM conversations that already exist",
  "body": """<p><code>conversations.list?types=im&amp;limit=1000</code>, paginated. Each entry carries the <code>D</code> ID and the <code>user</code> it belongs to, which is exactly the mapping the application should have cached and did not.</p>"""},
 {"h": "Never probe with conversations.open",
  "body": """<p>It answers the question by creating the conversation, so it is a write, and a scheduled audit built on it opens a DM with every recipient it checks. The IM listing answers the same question and changes nothing.</p>"""},
 {"h": "Sort each configured recipient against that inventory",
  "body": """<p>A stored <code>D</code> that appears in the listing is correct. A stored <code>U</code> whose IM exists is working by luck and should be replaced with the ID. A stored <code>U</code> with no IM is the failure, and a stored <code>D</code> that is not in the listing is a conversation this token cannot see at all.</p>"""},
 {"h": "Print the open call rather than making it",
  "body": """<p>For every recipient with no conversation, the script prints the exact <code>conversations.open</code> invocation with the user ID filled in. Running it is a decision about writing into somebody's workspace, and that decision stays with the person reading the report.</p>"""},
 {"h": "Cache the D per user once it exists",
  "body": """<p>Store the returned <code>channel.id</code> against the user in whatever holds your recipient list. The mapping does not expire. After that the send path is an ordinary post to a channel ID, and none of the method-by-method inconsistency applies to it any more.</p>"""},
],
"verify": """<p>Once the conversations exist and the IDs are cached, every recipient should classify as addressed and the run should need no repairs.</p>
<pre><code class="language-bash">python3 slack_dm_targets.py --targets recipients.json
# grant: im:read=yes im:write=yes
# inventory: 214 IM conversation(s) visible to this token
# addressed  ONCALL_PRIMARY  D01ALICE99  a DM conversation ID, and the IM exists
# addressed  ONCALL_BACKUP   D02BOBBB88  a DM conversation ID, and the IM exists
# 2 target(s) checked, 0 with no conversation to deliver into</code></pre>""",
"code_intro": "<code>im_index</code> turns the IM listing into the user-to-conversation map your application should have been keeping. <code>target_route</code> sorts one configured recipient against it, and the interesting row is the one where a user ID happens to work: an existing conversation makes the wrong value behave correctly, which is why the bug survives so long. <code>open_capability</code> checks the grant first, because an audit without <code>im:read</code> would report every recipient as broken.",
"py_file": "slack_dm_targets.py",
"py": '''"""Report the Slack DM recipients that have no conversation to deliver into.

Read only, and pointedly so: conversations.open answers this question by
creating a DM, which makes it a write, so the IM inventory is listed instead.
Nothing is opened. For every recipient without a conversation the script prints
the open call for you to run.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_dm_targets")

API = "https://slack.com/api/"

# im:read enumerates the DMs the token already has, im:write opens a new one.
# The audit needs the first; the repair needs the second, and the repair is not
# performed here.
AUDIT_SCOPE = "im:read"
OPEN_SCOPE = "im:write"


def im_index(conversations):
    """Map user ID to the IM conversation that exists with them. Pure.

    This is the mapping the application should have cached when it first opened
    each DM, rebuilt from conversations.list?types=im. Entries without a user are
    dropped: group DMs come back in the same family and belong to mpim scopes,
    not to this one.
    """
    index = {}
    for conversation in conversations or []:
        user = conversation.get("user")
        if user and conversation.get("is_im"):
            index[user] = conversation
    return index


def target_route(value, index):
    """Sort one configured recipient against the DM conversations that exist.

    Pure. Returns (state, dm_id, detail). The row that explains the whole bug is
    user-id-open: a user ID in a channel slot, and an existing conversation
    quietly making the wrong value behave like the right one.
    """
    text = str(value or "").strip()
    if not text:
        return ("empty", None,
                "no recipient at all. Something upstream resolved to an empty "
                "string and every method will refuse it.")

    if text.startswith("D"):
        for user, conversation in index.items():
            if conversation.get("id") == text:
                return ("addressed", text,
                        "a DM conversation ID, and the IM exists with %s" % user)
        return ("dm-id-unknown", None,
                "a DM conversation ID that is not in this token's IM list. Either "
                "it belongs to a different installation, or im:read is not "
                "granted and the inventory is incomplete.")

    if text[:1] in ("U", "W"):
        existing = index.get(text)
        if existing is not None:
            return ("user-id-open", existing.get("id"),
                    "a user ID, and a conversation already exists, so "
                    "chat.postMessage delivers and the file methods still refuse "
                    "it. Store %s instead." % existing.get("id"))
        return ("user-id-unopened", None,
                "a user ID with no conversation behind it. This is the recipient "
                "the feature fails for, and it fails only for people who have "
                "never interacted with the app.")

    return ("not-a-recipient", None,
            "neither a user ID nor a DM conversation ID. A channel ID here would "
            "post in public; anything else fails outright.")


def open_capability(scopes):
    """Whether this audit can see DMs, and whether the app could open one. Pure.

    Returns (state, missing, detail). The blind case matters most: without
    im:read the inventory is empty and every recipient classifies as unopened,
    which is a wrong answer rather than a missing one.
    """
    have = {s.strip() for s in str(scopes or "").split(",") if s.strip()}
    can_audit = AUDIT_SCOPE in have
    can_open = OPEN_SCOPE in have
    if not can_audit and not can_open:
        return ("unequipped", [AUDIT_SCOPE, OPEN_SCOPE],
                "neither scope is granted. This token cannot list DMs and the app "
                "cannot open them, so nothing about DMs works today.")
    if not can_audit:
        return ("blind", [AUDIT_SCOPE],
                "the app can open DMs but this token cannot list them, so the "
                "inventory below is empty for a reason that has nothing to do "
                "with your recipients. Do not act on it.")
    if not can_open:
        return ("cannot-open", [OPEN_SCOPE],
                "DMs can be listed but not opened. Every unopened recipient is "
                "unfixable until im:write is granted and the app reinstalled.")
    return ("ready", [], "both scopes granted")


def repair_command(user_id):
    """The one write call this script will not make, printed for you. Pure."""
    return ('curl -sS -H "Authorization: Bearer $SLACK_BOT_TOKEN" '
            "-d users=%s https://slack.com/api/conversations.open" % user_id)


def list_ims(session):
    """Every DM conversation the token can see. GET, paginated."""
    out, cursor = [], ""
    while True:
        params = {"types": "im", "limit": 1000}
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
    ap.add_argument("--targets", required=True,
                    help="JSON object mapping a config key to its DM recipient value")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (im:read is what this audit needs)", args.token_env)
        return 2

    targets = json.loads(open(args.targets, encoding="utf-8").read())
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    res = session.get(API + "auth.test", timeout=30)
    if res.json().get("ok") is not True:
        log.error("auth.test failed: %s", res.json().get("error"))
        return 2
    state, missing, detail = open_capability(res.headers.get("X-OAuth-Scopes"))
    log.info("grant: %s=%s %s=%s", AUDIT_SCOPE,
             "no" if AUDIT_SCOPE in missing else "yes", OPEN_SCOPE,
             "no" if OPEN_SCOPE in missing else "yes")
    if state in ("blind", "unequipped"):
        log.error("%s -- %s", state, detail)
        log.error("repair: add %s to Bot Token Scopes and reinstall, then re-run",
                  ", ".join(missing))
        return 2
    if state == "cannot-open":
        log.warning("%s -- %s", state, detail)

    index = im_index(list_ims(session))
    log.info("inventory: %d IM conversation(s) visible to this token", len(index))

    bad = 0
    for key in sorted(targets):
        route, dm_id, why = target_route(targets[key], index)
        if route == "addressed":
            log.info("%-16s %-16s %-12s %s", route, key, dm_id, why)
            continue

        bad += 1
        log.warning("%-16s %-16s %-12s %s", route, key, targets[key], why)
        if route == "user-id-open":
            log.warning("  repair: %s=%s", key, dm_id)
        elif route == "user-id-unopened":
            log.warning("  repair: %s", repair_command(targets[key]))
            log.warning("  then store the returned channel.id in %s", key)
        else:
            log.warning("  repair: put a D conversation ID in %s, or the user ID "
                        "you want a DM opened for", key)

    log.info("%d target(s) checked, %d with no conversation to deliver into",
             len(targets), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-dm-targets.mjs",
"js": '''/**
 * Report the Slack DM recipients that have no conversation to deliver into.
 *
 * Read only, and pointedly so: conversations.open answers this question by
 * creating a DM, which makes it a write, so the IM inventory is listed instead.
 * Nothing is opened; the open call is printed for you to run.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// im:read enumerates the DMs the token already has, im:write opens a new one.
// The audit needs the first; the repair needs the second, and the repair is not
// performed here.
const AUDIT_SCOPE = 'im:read';
const OPEN_SCOPE = 'im:write';

/**
 * Map user ID to the IM conversation that exists with them. Pure.
 * This is the mapping the application should have cached when it first opened
 * each DM. Entries without a user belong to the mpim family, not this one.
 */
export function imIndex(conversations) {
  const index = new Map();
  for (const conversation of conversations ?? []) {
    if (conversation.user && conversation.is_im) index.set(conversation.user, conversation);
  }
  return index;
}

/**
 * Sort one configured recipient against the DM conversations that exist. Pure.
 * user-id-open is the row that explains the bug: an existing conversation
 * quietly makes the wrong value behave like the right one.
 */
export function targetRoute(value, index) {
  const text = String(value ?? '').trim();
  if (!text) {
    return ['empty', null,
      'no recipient at all. Something upstream resolved to an empty string and ' +
      'every method will refuse it.'];
  }

  if (text.startsWith('D')) {
    for (const [user, conversation] of index) {
      if (conversation.id === text) {
        return ['addressed', text, `a DM conversation ID, and the IM exists with ${user}`];
      }
    }
    return ['dm-id-unknown', null,
      "a DM conversation ID that is not in this token's IM list. Either it " +
      'belongs to a different installation, or im:read is not granted and the ' +
      'inventory is incomplete.'];
  }

  if (text[0] === 'U' || text[0] === 'W') {
    const existing = index.get(text);
    if (existing) {
      return ['user-id-open', existing.id,
        'a user ID, and a conversation already exists, so chat.postMessage ' +
        `delivers and the file methods still refuse it. Store ${existing.id} instead.`];
    }
    return ['user-id-unopened', null,
      'a user ID with no conversation behind it. This is the recipient the ' +
      'feature fails for, and it fails only for people who have never ' +
      'interacted with the app.'];
  }

  return ['not-a-recipient', null,
    'neither a user ID nor a DM conversation ID. A channel ID here would post in ' +
    'public; anything else fails outright.'];
}

/**
 * Whether this audit can see DMs, and whether the app could open one. Pure.
 * Without im:read the inventory is empty and every recipient classifies as
 * unopened, which is a wrong answer rather than a missing one.
 */
export function openCapability(scopes) {
  const have = new Set(String(scopes ?? '').split(',').map((s) => s.trim()).filter(Boolean));
  const canAudit = have.has(AUDIT_SCOPE);
  const canOpen = have.has(OPEN_SCOPE);
  if (!canAudit && !canOpen) {
    return ['unequipped', [AUDIT_SCOPE, OPEN_SCOPE],
      'neither scope is granted. This token cannot list DMs and the app cannot ' +
      'open them, so nothing about DMs works today.'];
  }
  if (!canAudit) {
    return ['blind', [AUDIT_SCOPE],
      'the app can open DMs but this token cannot list them, so the inventory ' +
      'below is empty for a reason that has nothing to do with your recipients. ' +
      'Do not act on it.'];
  }
  if (!canOpen) {
    return ['cannot-open', [OPEN_SCOPE],
      'DMs can be listed but not opened. Every unopened recipient is unfixable ' +
      'until im:write is granted and the app reinstalled.'];
  }
  return ['ready', [], 'both scopes granted'];
}

/** The one write call this script will not make, printed for you. Pure. */
export function repairCommand(userId) {
  return 'curl -sS -H "Authorization: Bearer $SLACK_BOT_TOKEN" ' +
    `-d users=${userId} https://slack.com/api/conversations.open`;
}

async function listIms(token) {
  const out = [];
  let cursor = '';
  for (;;) {
    const params = new URLSearchParams({ types: 'im', limit: '1000' });
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
  const targetsPath = arg(args, '--targets');
  if (!targetsPath) {
    console.error('usage: --targets recipients.json [--token-env SLACK_BOT_TOKEN]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (im:read is what this audit needs)`);
    process.exitCode = 2;
    return;
  }

  const targets = JSON.parse(await readFile(targetsPath, 'utf8'));
  const authRes = await fetch(`${API}auth.test`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const auth = await authRes.json();
  if (auth.ok !== true) {
    console.error(`auth.test failed: ${auth.error}`);
    process.exitCode = 2;
    return;
  }
  const [state, missing, detail] = openCapability(authRes.headers.get('x-oauth-scopes'));
  console.log(`grant: ${AUDIT_SCOPE}=${missing.includes(AUDIT_SCOPE) ? 'no' : 'yes'} ` +
              `${OPEN_SCOPE}=${missing.includes(OPEN_SCOPE) ? 'no' : 'yes'}`);
  if (state === 'blind' || state === 'unequipped') {
    console.error(`${state} -- ${detail}`);
    console.error(`repair: add ${missing.join(', ')} to Bot Token Scopes and ` +
                  'reinstall, then re-run');
    process.exitCode = 2;
    return;
  }
  if (state === 'cannot-open') console.warn(`${state} -- ${detail}`);

  const index = imIndex(await listIms(token));
  console.log(`inventory: ${index.size} IM conversation(s) visible to this token`);

  let bad = 0;
  for (const key of Object.keys(targets).sort()) {
    const [route, dmId, why] = targetRoute(targets[key], index);
    if (route === 'addressed') {
      console.log(`${route.padEnd(16)} ${key.padEnd(16)} ${String(dmId).padEnd(12)} ${why}`);
      continue;
    }

    bad += 1;
    console.warn(`${route.padEnd(16)} ${key.padEnd(16)} ` +
                 `${String(targets[key]).padEnd(12)} ${why}`);
    if (route === 'user-id-open') {
      console.warn(`  repair: ${key}=${dmId}`);
    } else if (route === 'user-id-unopened') {
      console.warn(`  repair: ${repairCommand(targets[key])}`);
      console.warn(`  then store the returned channel.id in ${key}`);
    } else {
      console.warn(`  repair: put a D conversation ID in ${key}, or the user ID you ` +
                   'want a DM opened for');
    }
  }

  console.log(`${Object.keys(targets).length} target(s) checked, ${bad} with no ` +
              'conversation to deliver into');
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing target list.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two assertions carry the note. A user ID with a conversation behind it has to classify as <code>user-id-open</code> and not as correct, because it works today by accident and will still be refused by the file methods; and a user ID with no conversation has to be the failure rather than a variant of the same row. The capability tests pin that a token without <code>im:read</code> reports itself blind instead of reporting every recipient as broken.",
"test_py_file": "test_slack_dm_targets.py",
"test_py": '''from slack_dm_targets import (im_index, open_capability, repair_command,
                              target_route)

IMS = [
    {"id": "D01ALICE99", "user": "U01ALICE99", "is_im": True},
    {"id": "D02BOBBB88", "user": "U02BOBBB88", "is_im": True},
    {"id": "G03GROUP77", "is_im": False},
]
INDEX = im_index(IMS)


def test_the_index_maps_users_to_their_conversations():
    assert set(INDEX) == {"U01ALICE99", "U02BOBBB88"}
    assert INDEX["U01ALICE99"]["id"] == "D01ALICE99"


def test_a_group_conversation_is_not_in_the_one_to_one_index():
    assert all(c.get("is_im") for c in INDEX.values())


def test_a_known_dm_id_is_the_only_addressed_state():
    route, dm_id, _ = target_route("D01ALICE99", INDEX)
    assert route == "addressed"
    assert dm_id == "D01ALICE99"


def test_a_user_id_with_a_conversation_still_needs_replacing():
    route, dm_id, detail = target_route("U01ALICE99", INDEX)
    assert route == "user-id-open"
    assert dm_id == "D01ALICE99"
    assert "file methods still refuse" in detail


def test_a_user_id_with_no_conversation_is_the_failure():
    route, dm_id, detail = target_route("U09NEWHIRE", INDEX)
    assert route == "user-id-unopened"
    assert dm_id is None
    assert "never interacted" in detail


def test_a_dm_id_outside_the_inventory_is_not_reported_as_working():
    route, _, _ = target_route("D99ELSEWHR", INDEX)
    assert route == "dm-id-unknown"


def test_an_empty_recipient_is_its_own_state():
    assert target_route("", INDEX)[0] == "empty"
    assert target_route(None, INDEX)[0] == "empty"


def test_a_channel_id_is_not_a_dm_recipient():
    assert target_route("C01ABCDE9", INDEX)[0] == "not-a-recipient"


def test_without_im_read_the_audit_calls_itself_blind():
    state, missing, detail = open_capability("chat:write,im:write")
    assert state == "blind"
    assert missing == ["im:read"]
    assert "Do not act on it" in detail


def test_without_im_write_the_findings_are_real_but_unfixable():
    state, missing, _ = open_capability("im:read,chat:write")
    assert state == "cannot-open"
    assert missing == ["im:write"]


def test_neither_scope_is_its_own_verdict():
    assert open_capability("chat:write")[0] == "unequipped"
    assert open_capability("")[0] == "unequipped"


def test_both_scopes_granted_is_ready():
    assert open_capability("im:read,im:write,chat:write")[0] == "ready"


def test_the_repair_reads_the_token_from_the_environment():
    line = repair_command("U09NEWHIRE")
    assert "conversations.open" in line
    assert "$SLACK_BOT_TOKEN" in line
    assert "users=U09NEWHIRE" in line
''',
"test_js_file": "slack-dm-targets.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { imIndex, openCapability, repairCommand, targetRoute }
  from './slack-dm-targets.mjs';

const IMS = [
  { id: 'D01ALICE99', user: 'U01ALICE99', is_im: true },
  { id: 'D02BOBBB88', user: 'U02BOBBB88', is_im: true },
  { id: 'G03GROUP77', is_im: false },
];
const INDEX = imIndex(IMS);

test('the index maps users to their conversations', () => {
  assert.deepEqual([...INDEX.keys()].sort(), ['U01ALICE99', 'U02BOBBB88']);
  assert.equal(INDEX.get('U01ALICE99').id, 'D01ALICE99');
});

test('a group conversation is not in the one to one index', () => {
  assert.ok([...INDEX.values()].every((c) => c.is_im));
});

test('a known dm id is the only addressed state', () => {
  const [route, dmId] = targetRoute('D01ALICE99', INDEX);
  assert.equal(route, 'addressed');
  assert.equal(dmId, 'D01ALICE99');
});

test('a user id with a conversation still needs replacing', () => {
  const [route, dmId, detail] = targetRoute('U01ALICE99', INDEX);
  assert.equal(route, 'user-id-open');
  assert.equal(dmId, 'D01ALICE99');
  assert.match(detail, /file methods still refuse/);
});

test('a user id with no conversation is the failure', () => {
  const [route, dmId, detail] = targetRoute('U09NEWHIRE', INDEX);
  assert.equal(route, 'user-id-unopened');
  assert.equal(dmId, null);
  assert.match(detail, /never interacted/);
});

test('a dm id outside the inventory is not reported as working', () => {
  assert.equal(targetRoute('D99ELSEWHR', INDEX)[0], 'dm-id-unknown');
});

test('an empty recipient is its own state', () => {
  assert.equal(targetRoute('', INDEX)[0], 'empty');
  assert.equal(targetRoute(null, INDEX)[0], 'empty');
});

test('a channel id is not a dm recipient', () => {
  assert.equal(targetRoute('C01ABCDE9', INDEX)[0], 'not-a-recipient');
});

test('without im read the audit calls itself blind', () => {
  const [state, missing, detail] = openCapability('chat:write,im:write');
  assert.equal(state, 'blind');
  assert.deepEqual(missing, ['im:read']);
  assert.match(detail, /Do not act on it/);
});

test('without im write the findings are real but unfixable', () => {
  const [state, missing] = openCapability('im:read,chat:write');
  assert.equal(state, 'cannot-open');
  assert.deepEqual(missing, ['im:write']);
});

test('neither scope is its own verdict', () => {
  assert.equal(openCapability('chat:write')[0], 'unequipped');
  assert.equal(openCapability('')[0], 'unequipped');
});

test('both scopes granted is ready', () => {
  assert.equal(openCapability('im:read,im:write,chat:write')[0], 'ready');
});

test('the repair reads the token from the environment', () => {
  const line = repairCommand('U09NEWHIRE');
  assert.match(line, /conversations\\.open/);
  assert.match(line, /\\$SLACK_BOT_TOKEN/);
  assert.match(line, /users=U09NEWHIRE/);
});
''',
"faq": [
 ("Why does DMing a user ID work for some people and not others?",
  "Because it depends on whether a conversation already exists with that person. chat.postMessage will open the IM implicitly in many cases and reliably will not for users who have never interacted with the app, which maps almost exactly onto the difference between the people who tested the feature and the people who are now using it."),
 ("Can a read-only script check whether a DM exists without creating one?",
  "Yes, by listing rather than opening. conversations.list with types=im returns the DM conversations the token can see, each with the user it belongs to. conversations.open would answer the same question by creating the conversation, so an audit built on it writes into every recipient's workspace as a side effect of checking."),
 ("Which scopes does this need?",
  "im:read to enumerate DM conversations, im:write to open one, im:history to read the messages in them. Group DMs use the mpim: equivalents and are a separate grant, so an app can be perfectly configured for one-to-one DMs and unable to open a conversation with three people."),
 ("Should the D channel ID be cached, or resolved on every send?",
  "Cached. The mapping between a user and their DM conversation with your app is stable, so opening it repeatedly adds a write and a round trip to every message for no benefit. Store the returned channel.id against the user the first time and the send path becomes an ordinary post to a channel ID."),
 ("What if the recipient is another app rather than a person?",
  "Then no DM can be opened at all: apps cannot DM other apps, and the attempt returns cannot_dm_bot. That is a property of the recipient rather than of the conversation, so it belongs with the other recipient-side faults, along with accounts that have been deactivated since the ID was stored."),
],
"related": [
 ("/slack/channel-name-instead-of-id/", "the other identifier in the wrong slot"),
 ("/slack/missing-scope-on-read/", "reading needed against provided"),
 ("/slack/http-200-ok-false/", "why the failure never raised"),
],
"citations": [CITE_CONV_OPEN, CITE_CONV_LIST, CITE_SCOPES, CITE_CONV_API],
},

{
"slug": "dm-to-deactivated-user",
"title": "DMs delivered into deactivated accounts, with ok: true",
"description": "Slack keeps the user and the DM after offboarding, so sends still succeed. Join your recipient list against users.list and find the addresses nobody reads.",
"h1": "DMs delivered into deactivated accounts, with ok: true",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack deactivated user dm", "slack users.list deleted true",
             "slack cannot_dm_bot", "slack user_change event deactivation",
             "slack notification to former employee"],
"deps": "Python 3.9+ with requests, or Node.js 18+; users:read to page the directory",
"lead": "The approval bot has a 96% delivery rate and a 41% response rate, and nobody can explain the gap. Every send returns <code>ok: true</code>. The messages are arriving, in DMs, with people who left the company: the account is deactivated, the conversation still exists, and Slack is faithfully writing into a room that nobody will ever open again.",
"short_answer": """<p>Deactivation does not delete anything. The user record stays, with <code>deleted: true</code> on it, and the DM conversation your app opened at signup stays with it. Posting into that existing <code>D</code> channel still returns <code>ok: true</code>. There is no error, no bounce, and no signal of any kind that the recipient stopped existing eight months ago.</p>
<p>So the check is a join, not a send. Page <code>users.list</code>, build the directory, and put your recipient table beside it. The script below sorts each recipient into what a send would actually do: silently accepted for a deactivated account, refused loudly for another app with <code>cannot_dm_bot</code>, delivered but possibly useless for a single-channel guest, or genuinely delivered. Loud failures are already visible in your logs. The silent one is the reason the numbers do not add up.</p>""",
"problem": """<p>The recipient list is built once and never revisited. Someone signs up, the app opens a DM, the <code>D</code> ID goes into a table, and that row is now permanent. People leave, and their leaving is handled thoroughly everywhere else &mdash; SSO, the HR system, the badge &mdash; and not in your table, because nothing in the offboarding checklist knows your table exists.</p>
<p>What makes this specifically a Slack problem is the direction the failure points. A dead email address bounces. A disconnected number errors. A deactivated Slack account accepts, because the conversation is a real conversation and the write into it is a legitimate write. From the API's point of view nothing has gone wrong, and it is right: the message was stored. It is only wrong from yours.</p>
<p>The result is a slow accumulation with no threshold. Six months in, a percent of the sends go nowhere. Two years in it is a fifth, and the delivery metric still reads 100% because the metric is counting <code>ok: true</code>. The first person to notice is usually not an engineer but someone in operations asking why approvals from one team never come back.</p>""",
"why": """<p><strong>The user record outlives the user.</strong> Slack keeps deactivated accounts so that old messages still render with a name and an avatar, so <code>users.info</code> keeps answering and the ID keeps resolving forever. Any check that only asks "is this a real user ID" passes for every person who has ever left.</p>
<p><strong>The silent case is the expensive one.</strong> <code>cannot_dm_bot</code> and <code>user_not_found</code> are loud: they turn up in logs, they fail a run, somebody eventually greps for them. A deactivated recipient produces no artefact at all, which is why the script sorts by how a send fails rather than by what the recipient is &mdash; the grouping that matters operationally is silent against loud.</p>
<p><strong>Deactivation is the state you can read; timing is approximate.</strong> The user object carries an <code>updated</code> timestamp, which for a deactivated account is usually when the deactivation happened, because it is the last thing that changed about them. It is close enough to size the problem and not an audit record, and the script says which of those it is offering.</p>
<p><strong>Bots and guests fail differently and belong in the report anyway.</strong> An app cannot DM another app: that attempt fails outright. A single-channel guest can be DM'd, but a message full of links to channels they cannot open is delivered and useless. Neither is the headline, and both are in your recipient list for the same reason the deactivated accounts are &mdash; nobody has looked at it since it was built.</p>
<p><strong>The fix is a schedule plus an event.</strong> Joining against <code>users.list</code> weekly catches everything eventually; subscribing to <code>user_change</code>, which fires with <code>deleted: true</code> on deactivation, catches it the same day. The two together mean the list is correct in near real time and self-heals if the events are ever missed.</p>""",
"steps": [
 {"h": "Page the whole directory once",
  "body": """<p><code>users.list?limit=200</code>, following <code>next_cursor</code> to the end. It is a Tier 2 method and a large workspace is many pages, so do this once per run and index it by ID rather than calling <code>users.info</code> per recipient, which is a call each and rate-limits at scale.</p>"""},
 {"h": "Sort recipients by what the account is",
  "body": """<p><code>deleted</code> first, because it outranks everything else about a recipient. Then <code>is_bot</code> and <code>is_app_user</code>, then the guest flags. The order is the point: a deactivated bot is a deactivated recipient, and reporting it as a bot sends the reader to the wrong repair.</p>"""},
 {"h": "Translate that into what a send would do",
  "body": """<p>This is the step that makes the report actionable. Deactivated is silent acceptance. A bot recipient is a loud refusal you can already see in your logs. A restricted guest is delivery into an account that may not be able to open half of what the message references. Sorting by loudness puts the invisible failures at the top where they belong.</p>"""},
 {"h": "Date the silence from the user record",
  "body": """<p>The <code>updated</code> field on a deactivated account is usually the deactivation, which turns "this recipient is dead" into "this recipient has been dead since October" and lets you multiply out how many messages went nowhere. Report it as an approximation, because that is what it is.</p>"""},
 {"h": "Report the recipients that are not in the directory at all",
  "body": """<p>An ID in your table with no matching user is not a deactivated account; it is an ID from another workspace, a Grid org this token cannot see, or a corrupted row. It needs a different investigation and it must not be counted as offboarded.</p>"""},
 {"h": "Subscribe to user_change and re-run the join on a schedule",
  "body": """<p><code>user_change</code> fires with <code>deleted: true</code> when somebody is deactivated, which makes the cleanup event-driven and same-day. Keep the scheduled join anyway as the backstop: events can be missed while a Request URL is unhealthy, and the join does not care why a row went stale.</p>"""},
],
"verify": """<p>After the join has been applied and the dead rows marked inactive, every remaining recipient should be an active human.</p>
<pre><code class="language-bash">python3 slack_dm_recipient_audit.py --recipients recipients.json
# directory: 1842 user record(s), 311 deactivated
# active     U01ALICE99  delivered, and somebody is there to read it
# active     U02BOBBB88  delivered, and somebody is there to read it
# 2 recipient(s) checked, 0 silent, 0 loud</code></pre>""",
"code_intro": "<code>recipient_class</code> reads one <code>users.list</code> record in a fixed order, because a deactivated bot has to be reported as deactivated rather than as a bot. <code>delivery_outcome</code> is the function worth stealing: it turns that class into what a send actually does, which sorts the findings into the ones already visible in your logs and the one that never will be. <code>dormant_since</code> dates the silence and is careful to describe itself as an approximation.",
"py_file": "slack_dm_recipient_audit.py",
"py": '''"""Find the DM recipients that no longer read anything.

Read only. One paginated users.list, joined against the recipient table your
application keeps. Nothing is sent and no row is rewritten: the script names
the recipients whose sends succeed into a void, dates them where the directory
allows, and prints the repair.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_dm_recipient_audit")

API = "https://slack.com/api/"

# Sorted by how a send fails rather than by what the recipient is. Loud failures
# are already in your logs; the silent one is the reason a delivery metric can
# read 100% while a fifth of the messages go nowhere.
OUTCOMES = {
    "deactivated": ("silent",
                    "the DM conversation still exists, so the send returns ok: "
                    "true and the message is stored where nobody will read it"),
    "bot": ("loud",
            "apps cannot DM other apps; the attempt fails with cannot_dm_bot and "
            "is already visible in your logs"),
    "single-channel-guest": ("partial",
                             "delivered, but this account can reach one channel, "
                             "so anything the message links to is probably closed "
                             "to them"),
    "guest": ("partial",
              "delivered, though a multi-channel guest may not be able to open "
              "every channel the message references"),
    "active": ("delivered", "delivered, and somebody is there to read it"),
    "unknown": ("loud",
                "no user record in this workspace. A send returns user_not_found "
                "rather than succeeding, so this is a broken row and not an "
                "offboarded person."),
}


def recipient_class(user):
    """Sort one users.list record by what it means for a DM. Pure.

    Order matters and deactivation comes first: a deactivated bot is a
    deactivated recipient, and reporting it as a bot sends the reader to the
    wrong repair.
    """
    if user is None:
        return ("unknown", "no matching record in the directory")
    if user.get("deleted"):
        return ("deactivated", "deleted is true; the account was deactivated")
    if user.get("is_bot") or user.get("is_app_user"):
        return ("bot", "this recipient is an app, not a person")
    if user.get("is_ultra_restricted"):
        return ("single-channel-guest", "a single-channel guest account")
    if user.get("is_restricted"):
        return ("guest", "a multi-channel guest account")
    return ("active", "an active member of the workspace")


def delivery_outcome(kind):
    """What a send to this recipient actually does. Pure.

    Returns (loudness, detail). The split that matters is silent against loud:
    one of these is already in your logs and one has never appeared anywhere.
    """
    return OUTCOMES.get(kind, OUTCOMES["unknown"])


def dormant_since(user):
    """Date the silence from the user record. Pure.

    users.list returns `updated`, the last time the record changed, which for a
    deactivated account is usually the deactivation itself. That is close enough
    to size the problem and is not an audit record, so it is reported as the
    approximation it is.
    """
    stamp = (user or {}).get("updated")
    if not stamp:
        return ("undatable",
                "the directory record carries no updated timestamp, so how long "
                "this has been true cannot be recovered here")
    when = datetime.fromtimestamp(int(stamp), tz=timezone.utc)
    return ("approximate",
            "the record last changed on %s, which for a deactivated account is "
            "usually the deactivation" % when.date().isoformat())


def roster_diff(recipients, directory):
    """Split the recipient list by whether the directory knows the ID. Pure."""
    known = sorted(r for r in recipients if r in directory)
    unknown = sorted(r for r in recipients if r not in directory)
    return {"known": known, "unknown": unknown}


def list_users(session):
    """The whole user directory. GET, paginated, Tier 2, so once per run."""
    out, cursor = [], ""
    while True:
        params = {"limit": 200}
        if cursor:
            params["cursor"] = cursor
        body = session.get(API + "users.list", params=params, timeout=30).json()
        if body.get("ok") is not True:
            raise SystemExit("users.list answered 200 with ok: false, error=%s"
                             % body.get("error"))
        out.extend(body.get("members") or [])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--recipients", required=True,
                    help="JSON list of the user IDs your application DMs")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (users:read is enough)", args.token_env)
        return 2

    recipients = json.loads(open(args.recipients, encoding="utf-8").read())
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    members = list_users(session)
    directory = {m.get("id"): m for m in members if m.get("id")}
    log.info("directory: %d user record(s), %d deactivated", len(directory),
             sum(1 for m in directory.values() if m.get("deleted")))

    split = roster_diff(recipients, directory)
    silent = loud = 0
    for user_id in split["known"] + split["unknown"]:
        kind, why = recipient_class(directory.get(user_id))
        loudness, outcome = delivery_outcome(kind)

        if loudness == "delivered":
            log.info("%-22s %-12s %s", kind, user_id, outcome)
            continue

        if loudness == "silent":
            silent += 1
        elif loudness == "loud":
            loud += 1

        log.warning("%-22s %-12s %s", kind, user_id, outcome)
        log.warning("  why: %s", why)
        if kind == "deactivated":
            _, dated = dormant_since(directory.get(user_id))
            log.warning("  since: %s", dated)
            log.warning("  repair: mark %s inactive in your recipient table", user_id)
        elif kind == "bot":
            log.warning("  repair: filter is_bot and is_app_user out of the "
                        "recipient set before it is stored")
        elif kind == "unknown":
            log.warning("  repair: this ID belongs to another workspace or is a "
                        "corrupted row; investigate it separately from offboarding")
        else:
            log.warning("  repair: check that the channels this message links to "
                        "are reachable by a guest, or route around them")

    log.info("%d recipient(s) checked, %d silent, %d loud",
             len(recipients), silent, loud)
    return 1 if silent or loud else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-dm-recipient-audit.mjs",
"js": '''/**
 * Find the DM recipients that no longer read anything.
 *
 * Read only. One paginated users.list, joined against the recipient table your
 * application keeps. Nothing is sent and no row is rewritten: the script names
 * the recipients whose sends succeed into a void and prints the repair.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Sorted by how a send fails rather than by what the recipient is. Loud failures
// are already in your logs; the silent one is the reason a delivery metric can
// read 100% while a fifth of the messages go nowhere.
const OUTCOMES = {
  deactivated: ['silent',
    'the DM conversation still exists, so the send returns ok: true and the ' +
    'message is stored where nobody will read it'],
  bot: ['loud',
    'apps cannot DM other apps; the attempt fails with cannot_dm_bot and is ' +
    'already visible in your logs'],
  'single-channel-guest': ['partial',
    'delivered, but this account can reach one channel, so anything the message ' +
    'links to is probably closed to them'],
  guest: ['partial',
    'delivered, though a multi-channel guest may not be able to open every ' +
    'channel the message references'],
  active: ['delivered', 'delivered, and somebody is there to read it'],
  unknown: ['loud',
    'no user record in this workspace. A send returns user_not_found rather than ' +
    'succeeding, so this is a broken row and not an offboarded person.'],
};

/**
 * Sort one users.list record by what it means for a DM. Pure.
 * Deactivation comes first: a deactivated bot is a deactivated recipient, and
 * reporting it as a bot sends the reader to the wrong repair.
 */
export function recipientClass(user) {
  if (user === null || user === undefined) {
    return ['unknown', 'no matching record in the directory'];
  }
  if (user.deleted) return ['deactivated', 'deleted is true; the account was deactivated'];
  if (user.is_bot || user.is_app_user) return ['bot', 'this recipient is an app, not a person'];
  if (user.is_ultra_restricted) return ['single-channel-guest', 'a single-channel guest account'];
  if (user.is_restricted) return ['guest', 'a multi-channel guest account'];
  return ['active', 'an active member of the workspace'];
}

/**
 * What a send to this recipient actually does. Pure.
 * The split that matters is silent against loud: one of these is already in
 * your logs and one has never appeared anywhere.
 */
export function deliveryOutcome(kind) {
  return OUTCOMES[kind] ?? OUTCOMES.unknown;
}

/**
 * Date the silence from the user record. Pure.
 * `updated` is the last time the record changed, which for a deactivated
 * account is usually the deactivation itself. An approximation, reported as one.
 */
export function dormantSince(user) {
  const stamp = user?.updated;
  if (!stamp) {
    return ['undatable',
      'the directory record carries no updated timestamp, so how long this has ' +
      'been true cannot be recovered here'];
  }
  const when = new Date(Number(stamp) * 1000).toISOString().slice(0, 10);
  return ['approximate',
    `the record last changed on ${when}, which for a deactivated account is ` +
    'usually the deactivation'];
}

/** Split the recipient list by whether the directory knows the ID. Pure. */
export function rosterDiff(recipients, directory) {
  const has = (r) => Object.prototype.hasOwnProperty.call(directory, r);
  return {
    known: recipients.filter(has).sort(),
    unknown: recipients.filter((r) => !has(r)).sort(),
  };
}

async function listUsers(token) {
  const out = [];
  let cursor = '';
  for (;;) {
    const params = new URLSearchParams({ limit: '200' });
    if (cursor) params.set('cursor', cursor);
    const res = await fetch(`${API}users.list?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const body = await res.json();
    if (body.ok !== true) {
      throw new Error(`users.list answered 200 with ok: false, error=${body.error}`);
    }
    out.push(...(body.members ?? []));
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
  const recipientsPath = arg(args, '--recipients');
  if (!recipientsPath) {
    console.error('usage: --recipients recipients.json [--token-env SLACK_BOT_TOKEN]');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (users:read is enough)`);
    process.exitCode = 2;
    return;
  }

  const recipients = JSON.parse(await readFile(recipientsPath, 'utf8'));
  const members = await listUsers(token);
  const directory = Object.fromEntries(members.filter((m) => m.id).map((m) => [m.id, m]));
  const dead = Object.values(directory).filter((m) => m.deleted).length;
  console.log(`directory: ${Object.keys(directory).length} user record(s), ${dead} deactivated`);

  const split = rosterDiff(recipients, directory);
  let silent = 0;
  let loud = 0;
  for (const userId of [...split.known, ...split.unknown]) {
    const [kind, why] = recipientClass(directory[userId]);
    const [loudness, outcome] = deliveryOutcome(kind);

    if (loudness === 'delivered') {
      console.log(`${kind.padEnd(22)} ${userId.padEnd(12)} ${outcome}`);
      continue;
    }

    if (loudness === 'silent') silent += 1;
    else if (loudness === 'loud') loud += 1;

    console.warn(`${kind.padEnd(22)} ${userId.padEnd(12)} ${outcome}`);
    console.warn(`  why: ${why}`);
    if (kind === 'deactivated') {
      const [, dated] = dormantSince(directory[userId]);
      console.warn(`  since: ${dated}`);
      console.warn(`  repair: mark ${userId} inactive in your recipient table`);
    } else if (kind === 'bot') {
      console.warn('  repair: filter is_bot and is_app_user out of the recipient ' +
                   'set before it is stored');
    } else if (kind === 'unknown') {
      console.warn('  repair: this ID belongs to another workspace or is a corrupted ' +
                   'row; investigate it separately from offboarding');
    } else {
      console.warn('  repair: check that the channels this message links to are ' +
                   'reachable by a guest, or route around them');
    }
  }

  console.log(`${recipients.length} recipient(s) checked, ${silent} silent, ${loud} loud`);
  process.exitCode = silent || loud ? 1 : 0;
}

// Only run when invoked directly, so importing this module in the tests does not
// execute main() and fail the file on a missing recipient list.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The ordering inside <code>recipient_class</code> is load-bearing, so a record that is both a bot and deactivated is asserted to come back deactivated: it is the repair that differs, not the trivia. The outcome tests pin that exactly one class is <code>silent</code>, since that is the finding the whole note exists for, and that an ID missing from the directory is treated as a broken row rather than folded in with the people who left.",
"test_py_file": "test_slack_dm_recipient_audit.py",
"test_py": '''from slack_dm_recipient_audit import (delivery_outcome, dormant_since,
                                       recipient_class, roster_diff)

ALICE = {"id": "U01ALICE99", "updated": 1725000000}
GONE = {"id": "U02GONE888", "deleted": True, "updated": 1760000000}
APP = {"id": "U03BOTBOT7", "is_bot": True}
GUEST = {"id": "U04GUEST66", "is_restricted": True}
SINGLE = {"id": "U05ONECH55", "is_restricted": True, "is_ultra_restricted": True}
DIRECTORY = {u["id"]: u for u in (ALICE, GONE, APP, GUEST, SINGLE)}


def test_an_ordinary_member_is_active():
    assert recipient_class(ALICE)[0] == "active"


def test_a_deactivated_account_is_the_headline_class():
    kind, why = recipient_class(GONE)
    assert kind == "deactivated"
    assert "deactivated" in why


def test_deactivation_outranks_being_a_bot():
    assert recipient_class(dict(APP, deleted=True))[0] == "deactivated"


def test_an_app_user_counts_as_a_bot_recipient():
    assert recipient_class({"is_app_user": True})[0] == "bot"


def test_a_single_channel_guest_is_not_folded_in_with_other_guests():
    assert recipient_class(SINGLE)[0] == "single-channel-guest"
    assert recipient_class(GUEST)[0] == "guest"


def test_a_missing_record_is_unknown_rather_than_deactivated():
    assert recipient_class(None)[0] == "unknown"


def test_only_the_deactivated_case_is_silent():
    assert delivery_outcome("deactivated")[0] == "silent"
    for kind in ("bot", "unknown"):
        assert delivery_outcome(kind)[0] == "loud"
    assert delivery_outcome("active")[0] == "delivered"


def test_the_silent_outcome_says_the_send_succeeds():
    _, detail = delivery_outcome("deactivated")
    assert "ok: true" in detail


def test_an_unrecognised_class_falls_back_to_the_loud_row():
    assert delivery_outcome("something-new") == delivery_outcome("unknown")


def test_the_updated_timestamp_dates_the_silence_as_an_approximation():
    state, detail = dormant_since(GONE)
    assert state == "approximate"
    assert "2025-10" in detail


def test_a_record_without_a_timestamp_is_not_given_a_date():
    assert dormant_since({"deleted": True})[0] == "undatable"
    assert dormant_since(None)[0] == "undatable"


def test_recipients_outside_the_directory_are_kept_separate():
    split = roster_diff(["U01ALICE99", "U99OTHERWS"], DIRECTORY)
    assert split["known"] == ["U01ALICE99"]
    assert split["unknown"] == ["U99OTHERWS"]
''',
"test_js_file": "slack-dm-recipient-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { deliveryOutcome, dormantSince, recipientClass, rosterDiff }
  from './slack-dm-recipient-audit.mjs';

const ALICE = { id: 'U01ALICE99', updated: 1725000000 };
const GONE = { id: 'U02GONE888', deleted: true, updated: 1760000000 };
const APP = { id: 'U03BOTBOT7', is_bot: true };
const GUEST = { id: 'U04GUEST66', is_restricted: true };
const SINGLE = { id: 'U05ONECH55', is_restricted: true, is_ultra_restricted: true };
const DIRECTORY = Object.fromEntries(
  [ALICE, GONE, APP, GUEST, SINGLE].map((u) => [u.id, u]));

test('an ordinary member is active', () => {
  assert.equal(recipientClass(ALICE)[0], 'active');
});

test('a deactivated account is the headline class', () => {
  const [kind, why] = recipientClass(GONE);
  assert.equal(kind, 'deactivated');
  assert.match(why, /deactivated/);
});

test('deactivation outranks being a bot', () => {
  assert.equal(recipientClass({ ...APP, deleted: true })[0], 'deactivated');
});

test('an app user counts as a bot recipient', () => {
  assert.equal(recipientClass({ is_app_user: true })[0], 'bot');
});

test('a single channel guest is not folded in with other guests', () => {
  assert.equal(recipientClass(SINGLE)[0], 'single-channel-guest');
  assert.equal(recipientClass(GUEST)[0], 'guest');
});

test('a missing record is unknown rather than deactivated', () => {
  assert.equal(recipientClass(null)[0], 'unknown');
  assert.equal(recipientClass(undefined)[0], 'unknown');
});

test('only the deactivated case is silent', () => {
  assert.equal(deliveryOutcome('deactivated')[0], 'silent');
  assert.equal(deliveryOutcome('bot')[0], 'loud');
  assert.equal(deliveryOutcome('unknown')[0], 'loud');
  assert.equal(deliveryOutcome('active')[0], 'delivered');
});

test('the silent outcome says the send succeeds', () => {
  assert.match(deliveryOutcome('deactivated')[1], /ok: true/);
});

test('an unrecognised class falls back to the loud row', () => {
  assert.deepEqual(deliveryOutcome('something-new'), deliveryOutcome('unknown'));
});

test('the updated timestamp dates the silence as an approximation', () => {
  const [state, detail] = dormantSince(GONE);
  assert.equal(state, 'approximate');
  assert.match(detail, /2025-10/);
});

test('a record without a timestamp is not given a date', () => {
  assert.equal(dormantSince({ deleted: true })[0], 'undatable');
  assert.equal(dormantSince(null)[0], 'undatable');
});

test('recipients outside the directory are kept separate', () => {
  const split = rosterDiff(['U01ALICE99', 'U99OTHERWS'], DIRECTORY);
  assert.deepEqual(split.known, ['U01ALICE99']);
  assert.deepEqual(split.unknown, ['U99OTHERWS']);
});
''',
"faq": [
 ("Why does posting to a deactivated user's DM return ok: true?",
  "Because the conversation is real and the write is legitimate. Deactivation removes the person's ability to sign in; it does not delete their account, their history, or the DM conversation your app opened with them. Slack stores the message exactly as asked. Nothing has failed from the API's point of view, which is why nothing is reported."),
 ("Is users.list the only way to find deactivated recipients?",
  "It is the efficient way. users.info per recipient gives the same deleted flag but costs a call each, and at a few thousand recipients that rate-limits long before it finishes. Page the directory once, index it by ID, and join in memory. On a large Enterprise Grid workspace consider the cursor pages carefully: users.list is Tier 2."),
 ("What does the updated field actually tell me?",
  "The last time the user record changed. For an account that was deactivated and never touched again, that is effectively the deactivation date, which is enough to estimate how long the messages have been going nowhere. It is not an audit log: a profile edit before deactivation, or an admin change after it, will move the timestamp."),
 ("Should deactivated recipients be deleted from our table or just marked?",
  "Marked. Deactivated accounts are sometimes reactivated when someone returns or when an offboarding was reversed, and the DM conversation ID stays valid throughout, so a row you kept is a row you do not have to rebuild. Marking also preserves the history of who was on a notification list, which is often the thing an audit asks for."),
 ("How do we stop the list going stale again?",
  "Subscribe to user_change, which fires with deleted true when an account is deactivated, and update the row when it arrives. Keep the scheduled join as a backstop: events can be missed while a Request URL is unhealthy or a subscription is disabled, and the join notices a stale row regardless of why it went stale."),
],
"related": [
 ("/slack/users-read-email-missing/", "the other half of the user directory"),
 ("/slack/account-inactive/", "when the deactivated user is yours"),
 ("/slack/pagination-not-followed/", "the directory pages you never read"),
],
"citations": [CITE_USERS_LIST, CITE_USERS_INFO, CITE_USER_CHANGE, CITE_PAGINATION],
},

]
