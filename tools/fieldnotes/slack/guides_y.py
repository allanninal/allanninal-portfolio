#!/usr/bin/env python3
"""/slack/ field notes, batch Y - the writing.

Four notes separated by where the evidence lives, which is the only axis that
keeps them apart from the notes already published beside them.

The first is a sweep across the method surface. Slack replaced the per-type
channels.*, groups.*, im.* and mpim.* families with conversations.*, and the
interesting reading is not the method that already died - it is the one that
still answers ok: true while carrying a warning, because that warning is a
dated outage nobody has read. The retirement of files.upload has its own note
and this one hands it over by name; so does the retired RTM transport. The
rule that shapes the script is that a deprecated write is named and never
issued, because "does it still work?" cannot be asked of a write without
performing it.

The second is the App Home Home tab, which is a different switch from the
Messages tab in the batch before it, with a different symptom. The Messages
tab governs whether a person may type at your app, and refuses with
messages_tab_disabled. The Home tab governs whether a view you published is
reachable at all, and refuses with nothing whatsoever: views.publish answers
ok: true for a surface that does not exist. The second half of the reading is
therefore not DM traffic but coverage - which members have ever had a view
published for them, and how old it is - because the view is per user and per
installation and publishing once at startup leaves everybody else with an
empty tab.

The third is a row in your own database rather than an error from Slack. A
revoked token and a deactivated account each have their own note, and each of
those is about one dead credential. This one is about the population: what
fraction of the installation store is dead, whether that fraction is growing
between audits, and what else the uninstall left behind. A dead fraction that
holds steady across two audits is the proof that nothing is cleaning up.

The fourth is the reach of a single token. On Enterprise Grid an install is
either org-wide or bound to one workspace, and a workspace-bound token meets
team_access_not_granted the moment it is pointed at a sibling. Keying the
installation store on (enterprise_id, team_id) is a different note; this one
is about what one token can see and about the team_id parameter that org-wide
code has to start supplying.

Read only throughout. Two of the four make one GET each to
apps.manifest.export, which needs an app configuration token rather than a bot
token, and both degrade to the half that does not need it. No token, client
secret or signing secret is read, printed or transmitted by anything here.
"""

CITE_METHODS = ("Web API method reference - Slack Docs",
                "https://docs.slack.dev/reference/methods/")
CITE_CONVERSATIONS_LIST = ("conversations.list method reference - Slack Docs",
                           "https://docs.slack.dev/reference/methods/conversations.list")
CITE_CHANGELOG_2024 = ("Changelog: retiring older methods and files.upload - Slack Docs",
                       "https://docs.slack.dev/changelog/2024/05/16/apps/")
CITE_CONVERSATIONS_API = ("The Conversations API - Slack Docs",
                          "https://docs.slack.dev/apis/web-api/")
CITE_APP_HOME = ("App Home surfaces - Slack Docs",
                 "https://docs.slack.dev/surfaces/app-home")
CITE_VIEWS_PUBLISH = ("views.publish method reference - Slack Docs",
                      "https://docs.slack.dev/reference/methods/views.publish")
CITE_APP_HOME_OPENED = ("app_home_opened event reference - Slack Docs",
                        "https://docs.slack.dev/reference/events/app_home_opened")
CITE_MANIFEST_REF = ("App manifest reference - Slack Docs",
                     "https://docs.slack.dev/reference/manifests")
CITE_MANIFEST_EXPORT = ("apps.manifest.export method reference - Slack Docs",
                        "https://docs.slack.dev/reference/methods/apps.manifest.export")
CITE_TOKENS_REVOKED = ("tokens_revoked event reference - Slack Docs",
                       "https://docs.slack.dev/reference/events/tokens_revoked")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_BOLT_1203 = ("bolt-js #1203: the installation store never deletes a record "
                  "when the app is uninstalled",
                  "https://github.com/slackapi/bolt-js/issues/1203")
CITE_BOLT_673 = ("bolt-js #673: handling app_uninstalled and tokens_revoked",
                 "https://github.com/slackapi/bolt-js/issues/673")
CITE_GRID = ("Enterprise Grid for app developers - Slack Docs",
             "https://docs.slack.dev/enterprise-grid/")
CITE_BOLT_1778 = ("bolt-js #1778: a workspace-scoped token on Grid and "
                  "team_access_not_granted",
                  "https://github.com/slackapi/bolt-js/issues/1778")

GUIDES = []

GUIDES.append({
"slug": "deprecated-method-in-use",
"title": "method_deprecated: still on channels.*, groups.* and im.*",
"description": "The finding worth having is the method that still works and carries a warning. Sweep the legacy families for it without ever issuing a deprecated write.",
"h1": "method_deprecated: still on channels.*, groups.* and im.*",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack method_deprecated error",
             "slack channels.list conversations.list migration",
             "slack deprecated_endpoint groups.history",
             "slack response_metadata warnings deprecation",
             "slack conversations api migration checklist"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with channels:read, groups:read, im:read and mpim:read, plus channels:history if you want the history methods probed too",
"lead": "Nothing broke. That is the whole difficulty. The integration was written in 2019 against a tutorial that was already a year old, it calls <code>channels.list</code> and <code>channels.history</code>, and it has run every fifteen minutes for six years without a single error. Then one morning it returns nothing at all, and the body says <code>{\"ok\": false, \"error\": \"method_deprecated\"}</code>.</p><p>The notice was there. It had been there for months, on responses that said <code>ok: true</code> and returned exactly the data they always returned, in a field nobody logs: <code>warning</code>. Slack tells you a method is going away by attaching a string to a successful response, and the entire industry standard for handling a successful response is to read the payload and throw the envelope away.",
"short_answer": """<p>Slack replaced the per-type method families with one unified family. <code>channels.*</code>, <code>groups.*</code>, <code>im.*</code> and <code>mpim.*</code> all became <code>conversations.*</code>, distinguished by a <code>types</code> parameter rather than by the method name. <code>rtm.start</code> gave way to <code>rtm.connect</code> and then to Socket Mode. <code>files.upload</code> was replaced by a three-call external-upload sequence. Code written from an old tutorial starts on the retired path and stays there.</p>
<p>There are three states, and only one of them is an error. A method that has been <strong>removed</strong> answers <code>unknown_method</code>. A method that is <strong>dead</strong> answers <code>method_deprecated</code> or <code>deprecated_endpoint</code>. A method that is <strong>scheduled</strong> answers <code>ok: true</code> with a <code>warning</code> field or entries in <code>response_metadata.warnings[]</code> &mdash; and that third state is the only one you can act on before an outage rather than during one.</p>
<p>Two cautions shape the script below. Not every <code>warning</code> is a deprecation: <code>missing_charset</code> and <code>superfluous_charset</code> are about the <code>Content-Type</code> header you sent and say nothing about the method's future, so a sweep that counts them reports that everything is dying. And <strong>a deprecated write is never issued to find out whether it still works</strong>. <code>files.upload</code>, <code>im.open</code>, <code>channels.create</code> and <code>rtm.start</code> are named here, mapped to their replacements, and left alone.</p>""",
"problem": """<p>The reason this is a whole-surface problem rather than a single-method one is that the migration was a family migration. If your code calls <code>channels.list</code> it almost certainly also calls <code>channels.info</code>, <code>channels.history</code> and probably <code>groups.list</code> for the private ones, because that is how the old API forced you to write it: one method per conversation type, four times over, with a branch to pick between them. The replacement collapses all of that into <code>conversations.list</code> with <code>types=public_channel,private_channel,im,mpim</code>. Finding one legacy call almost always means finding six.</p>
<p>The staged retirement is what turns this into a surprise. A method does not usually flip from working to dead. It works, then it works and warns, then it warns more loudly, then it fails &mdash; and the middle two stages are invisible to any client that treats HTTP 200 as done. The advance notice is delivered on the successful response, which is the one place production code is guaranteed not to look, because the successful response is the one where nothing needs investigating.</p>
<p>The families also diverge in behaviour before they diverge in availability, which produces bugs that look nothing like a deprecation. <code>conversations.list</code> paginates by cursor and defaults to public channels only; <code>channels.list</code> returned a big array. An app that migrates the method name and not the pagination gets the first hundred channels and silently stops. An app that migrates <code>channels.list</code> and forgets <code>groups.list</code> stops seeing private channels entirely, with no error, because the replacement simply was not asked for that type.</p>
<p>And there is a category boundary that catches teams mid-migration. Some of these methods are reads and can be checked by asking. Others are writes: <code>im.open</code> opens a conversation, <code>channels.create</code> creates a channel, <code>files.upload</code> uploads a file, <code>rtm.start</code> and <code>rtm.connect</code> mint a session. There is no read-only way to ask a write method whether it still works, because the only way to ask is to do it. Every audit script that "just tries them all" is quietly writing to the workspace it was hired to inspect.</p>""",
"why": """<p><strong>The scheduled state is the finding; the dead state is the incident.</strong> By the time <code>method_deprecated</code> comes back, the outage has already happened and you do not need a script to find it. What a sweep is for is the response that succeeded and warned. So this check treats <code>ok: true</code> plus a deprecation warning as a finding of equal weight to an outright failure, and prints the migration for it in exactly the same words.</p>
<p><strong>A warning is not automatically a deprecation, and conflating them makes the check useless.</strong> <code>missing_charset</code> and <code>superfluous_charset</code> arrive constantly on perfectly healthy calls and are about the request's <code>Content-Type</code>. A sweep that reports them as scheduled outages produces a list on which everything is on fire, which is the same information as a list on which nothing is. The filter is small, explicit, and the reason the output can be trusted.</p>
<p><strong>Both warning channels are read, because Slack uses both.</strong> <code>body.warning</code> is a single string; <code>body.response_metadata.warnings[]</code> is an array, and structured deprecation messages arrive there. Reading only the first is how a sweep comes back clean on an app with a dated retirement notice sitting in the array.</p>
<p><strong>Deprecated writes are named and never called, and that is not squeamishness.</strong> Calling <code>im.open</code> to see whether it still exists opens a DM. Calling <code>channels.create</code> creates a channel with whatever name the probe made up. Calling <code>rtm.connect</code> mints a session against your connection budget. The map in this script records, for every legacy method, both its replacement and whether issuing it is a read, and only the reads are issued. The rest are reported from the map.</p>
<p><strong>Two of these methods have notes of their own and are handed over rather than duplicated.</strong> <code>files.upload</code> was sunset on its own timetable and its replacement is a three-call sequence with its own failure modes; the RTM transport requires a classic scope a modern app cannot request. Both are printed here with a pointer, because a sweep should tell you they are in your code, and neither is explained here, because a pointer is more useful than a summary.</p>
<p><strong>The replacement is printed as a mapping, not as advice.</strong> &ldquo;Migrate to the Conversations API&rdquo; is not actionable at four in the afternoon. <code>channels.history -&gt; conversations.history</code> is. Every row the script prints carries the exact method that replaces it and, where the parameters changed, the parameter that has to come with it.</p>""",
"steps": [
 {"h": "Take the method list from your own code, not from a guess",
  "body": """<p>Pass <code>--methods</code> with the legacy names your source actually contains, from a grep for <code>slack.com/api/</code> or for your SDK's call sites. With no argument the script sweeps the whole known map, which is a fine first pass and will report methods you never call as <code>live</code>.</p>"""},
 {"h": "Decide, per method, whether the sweep is allowed to issue it",
  "body": """<p><code>probe_safety</code> answers <code>probe</code>, <code>report-only</code> or <code>needs-argument</code>. A deprecated write is always <code>report-only</code>: named, mapped, never called. A read that needs a channel id is <code>needs-argument</code> until you pass <code>--channel</code>, because a probe without one returns <code>channel_not_found</code> and tells you nothing about the method.</p>"""},
 {"h": "Read three fields on every response, two of which are on successes",
  "body": """<p><code>classify</code> returns <code>removed</code>, <code>dead</code>, <code>scheduled</code>, <code>live</code>, <code>not-assessed</code> or <code>failed</code>. <code>scheduled</code> is the one to act on: the call worked, the data came back, and a warning says it will not next quarter.</p>"""},
 {"h": "Filter the charset noise out of the warnings",
  "body": """<p><code>deprecation_warnings</code> reads <code>body.warning</code> and <code>body.response_metadata.warnings[]</code> together and drops <code>missing_charset</code> and <code>superfluous_charset</code>. Those two are about the header you sent. Leaving them in turns a sweep of twenty methods into twenty findings.</p>"""},
 {"h": "Migrate the family, not the method",
  "body": """<p><code>migration_for</code> prints the replacement and the parameter that has to come with it: <code>conversations.list</code> needs <code>types</code>, and the four legacy list methods collapse into one call with four values. Migrating <code>channels.list</code> alone and leaving <code>groups.list</code> behind loses every private channel silently.</p>"""},
 {"h": "Log the warning field permanently, at WARN",
  "body": """<p>The repair that stops this recurring is one line in your HTTP client: if <code>body.warning</code> or <code>body.response_metadata.warnings</code> is non-empty, log it. That is the only channel Slack has for telling you about the next retirement, and it costs nothing to keep open.</p>"""},
],
"verify": """<p>Migrate, deploy, and run the sweep again with the same <code>--methods</code> list. Every row should read <code>live</code>, and the verdict line should be <code>clean</code>.</p>
<pre><code class="language-bash">python3 slack_deprecated_methods.py \\
  --methods channels.list,groups.list,channels.history,im.open,files.upload
# method     channels.list    dead        method_deprecated
#            migrate to       conversations.list, with types=public_channel
# method     groups.list      scheduled   ok true, and warning: method_deprecated
#            migrate to       conversations.list, with types=private_channel
# method     channels.history needs-argument
#            note             pass --channel C... to probe the history methods
# method     im.open          report-only this method writes; it opens a conversation,
#                             so the sweep names it and does not call it
#            migrate to       conversations.open
# method     files.upload     report-only this method writes; the sweep names it and
#                             does not call it
#            see also         /slack/files-upload-retired/
# verdict    2 finding(s)     1 dead, 1 scheduled, 2 named but not probed
#   repair: migrate the whole family at once; the four legacy list methods are one
#           conversations.list call with types=public_channel,private_channel,im,mpim
#   repair: log body.warning and body.response_metadata.warnings at WARN, permanently
#   note:   no deprecated write was issued to establish any of this</code></pre>""",
"code_intro": "The map is the script. <code>replacement_for</code> holds every legacy method against what replaced it and against whether issuing it is a read, and <code>probe_safety</code> is the guard that reads the second half of that pair: a deprecated write is named and never called. <code>deprecation_warnings</code> pulls both warning channels together and drops the two charset warnings that mean nothing here. <code>classify</code> turns one response into one of six states, of which <code>scheduled</code> is the valuable one, and <code>sweep_verdict</code> refuses to report clean on a sweep where most rows were never assessed.",
"py_file": "slack_deprecated_methods.py",
"py": '''"""Find the deprecated Slack methods your app still calls.

Read only, and deliberately stricter than the question requires. The map below
records, for every legacy method, both its replacement and whether issuing it
is a read. Only the reads are ever issued. files.upload, im.open,
channels.create, mpim.open and the RTM session methods are deprecated writes:
they are named here, mapped to their replacements, and never called, because
"does it still work?" cannot be asked of a write method without performing it.

Three fields carry the answer and two of them ride on responses that
succeeded. body.error holds method_deprecated once a method is dead;
body.warning and body.response_metadata.warnings[] hold the notice while it
still works. The second pair is the whole point of running this: it is the only
form of this finding that arrives before the outage rather than during it.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_deprecated_methods")

API = "https://slack.com/api/"

# Legacy method -> (replacement, kind). The kind is the safety half of the map
# and the reason this script can promise it never writes: "write" methods are
# reported from the map and never issued.
REPLACEMENTS = {
    "channels.list": ("conversations.list, with types=public_channel", "read"),
    "channels.info": ("conversations.info", "read"),
    "channels.history": ("conversations.history", "read"),
    "channels.replies": ("conversations.replies", "read"),
    "channels.create": ("conversations.create", "write"),
    "channels.invite": ("conversations.invite", "write"),
    "channels.join": ("conversations.join", "write"),
    "channels.archive": ("conversations.archive", "write"),
    "groups.list": ("conversations.list, with types=private_channel", "read"),
    "groups.info": ("conversations.info", "read"),
    "groups.history": ("conversations.history", "read"),
    "groups.replies": ("conversations.replies", "read"),
    "groups.create": ("conversations.create, with is_private=true", "write"),
    "im.list": ("conversations.list, with types=im", "read"),
    "im.history": ("conversations.history", "read"),
    "im.replies": ("conversations.replies", "read"),
    "im.open": ("conversations.open", "write"),
    "im.close": ("conversations.close", "write"),
    "mpim.list": ("conversations.list, with types=mpim", "read"),
    "mpim.history": ("conversations.history", "read"),
    "mpim.open": ("conversations.open, with a comma separated users list", "write"),
    "files.upload": ("files.getUploadURLExternal, then a plain upload, then "
                     "files.completeUploadExternal", "write"),
    "rtm.start": ("Socket Mode", "write"),
    "rtm.connect": ("Socket Mode", "write"),
}

# The methods that answer with no arguments at all. Everything else in the read
# half of the map needs a channel id, and probing it without one returns
# channel_not_found, which says nothing whatever about the method.
ARG_FREE = ("channels.list", "groups.list", "im.list", "mpim.list")

# Two methods here are large enough to have their own note. A sweep should tell
# you they are in your code; it should not try to explain them in a column.
OWNED_ELSEWHERE = {
    "files.upload": "/slack/files-upload-retired/",
    "rtm.start": "/slack/rtm-legacy-still-used/",
    "rtm.connect": "/slack/rtm-legacy-still-used/",
}

# A warning field is not automatically a deprecation notice. These two are
# about the Content-Type header on the request you sent and say nothing about
# the method's future. Counting them produces a sweep on which every method is
# dying, which carries the same information as one on which none of them is.
NOISE_WARNINGS = ("missing_charset", "superfluous_charset")

DEAD_ERRORS = ("method_deprecated", "deprecated_endpoint")
UNASSESSABLE = ("missing_scope", "not_allowed_token_type", "invalid_auth",
                "ratelimited", "token_revoked", "account_inactive")


def replacement_for(method):
    """What replaced this method, and whether issuing it is a read. Pure.

    Returns (replacement, kind); kind is "read", "write" or "unknown". An
    unknown method is not assumed safe: it is reported and not issued.
    """
    entry = REPLACEMENTS.get(str(method or "").strip())
    if not entry:
        return (None, "unknown")
    return entry


def probe_safety(method, channel_available=False):
    """May this sweep issue this method itself? Pure.

    Returns (action, why); action is "probe", "report-only" or
    "needs-argument". This is the guard the read-only promise rests on, so it
    is a function with tests rather than a comment in the request loop.
    """
    name = str(method or "").strip()
    _replacement, kind = replacement_for(name)
    if kind == "write":
        return ("report-only", "this method writes; the sweep names it and does "
                               "not call it")
    if kind == "unknown":
        return ("report-only", "this method is not in the map, so the sweep will "
                               "not issue it on the chance that it is a read")
    if name in ARG_FREE:
        return ("probe", "a read that answers with no arguments")
    if channel_available:
        return ("probe", "a read, probed against the channel you passed")
    return ("needs-argument", "pass --channel C... to probe the info and history "
                              "methods; without one the answer is channel_not_found "
                              "and says nothing about the method")


def deprecation_warnings(body):
    """The warnings in a response that are actually about deprecation. Pure.

    Reads both channels, because Slack uses both: body.warning is one string
    and body.response_metadata.warnings is an array carrying the structured
    notices. Drops the two charset warnings, which are about the request header
    and arrive constantly on healthy calls.
    """
    doc = body or {}
    raw = [doc.get("warning")]
    raw.extend((doc.get("response_metadata") or {}).get("warnings") or [])
    out = []
    for item in raw:
        text = str(item or "").strip()
        if text and text not in NOISE_WARNINGS:
            out.append(text)
    return list(dict.fromkeys(out))


def classify(body):
    """Read one response body as a deprecation state. Pure.

    Returns (state, detail). Six states, and the third is the one worth having:

      removed       unknown_method; the name is gone from the API entirely.
      dead          method_deprecated or deprecated_endpoint.
      scheduled     ok true, and a deprecation warning rides along with it.
      live          ok true and nothing said.
      not-assessed  the call was refused for a reason unrelated to deprecation,
                    so this method's state is simply not known.
      failed        any other ok false, which is a different note.
    """
    doc = body or {}
    error = str(doc.get("error") or "")
    if doc.get("ok") is True:
        warnings = deprecation_warnings(doc)
        if warnings:
            return ("scheduled", "ok true, and warning: %s" % ", ".join(warnings))
        return ("live", "ok true, and no deprecation warning")
    if error == "unknown_method":
        return ("removed", "unknown_method: the name is gone from the API")
    if error in DEAD_ERRORS:
        return ("dead", error)
    if error in UNASSESSABLE:
        return ("not-assessed", "%s, which is about the token rather than the "
                                "method" % error)
    if not error:
        return ("not-assessed", "no ok field and no error, so nothing can be read "
                                "from this response")
    return ("failed", "%s, which is a different problem" % error)


def migration_for(method):
    """The exact replacement line to print for one method. Pure."""
    replacement, _kind = replacement_for(method)
    return replacement


def sweep_verdict(rows):
    """rows: [(method, state), ...]. Returns (state, detail). Pure.

    Refuses to report clean on a sweep in which nothing was actually assessed,
    which is the failure mode of every audit tool: a token that cannot read
    anything produces a spotless report.
    """
    seen = [(str(m), str(st)) for m, st in (rows or [])]
    if not seen:
        return ("no-methods", "no method was checked, so there is nothing to say")
    dead = [m for m, st in seen if st in ("dead", "removed")]
    scheduled = [m for m, st in seen if st == "scheduled"]
    named = [m for m, st in seen if st == "report-only"]
    assessed = [m for m, st in seen if st in ("dead", "removed", "scheduled", "live")]
    if dead and scheduled:
        return ("dead", "%d method(s) already refused and %d more are warning"
                % (len(dead), len(scheduled)))
    if dead:
        return ("dead", "%d method(s) already refused: %s"
                % (len(dead), ", ".join(sorted(dead))))
    if scheduled:
        return ("scheduled", "%d method(s) still work and are warning: %s"
                % (len(scheduled), ", ".join(sorted(scheduled))))
    if not assessed:
        return ("not-assessed", "nothing was assessed; %d method(s) were named from "
                                "the map and none was probed" % len(named))
    return ("clean", "%d method(s) probed and none is deprecated" % len(assessed))


def get(session, method, params=None):
    """One GET against the Web API. Returns the parsed body."""
    r = session.get(API + method, params=params or {}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a read scoped bot token")
    ap.add_argument("--methods", default="",
                    help="comma separated legacy method names from your own source; "
                         "the whole known map is swept when this is omitted")
    ap.add_argument("--channel", default="",
                    help="a channel id, so the info and history methods can be probed")
    args = ap.parse_args()

    wanted = [m.strip() for m in args.methods.split(",") if m.strip()]
    if not wanted:
        wanted = sorted(REPLACEMENTS)

    token = os.environ.get(args.token_env)
    session = requests.Session()
    if token:
        session.headers.update({"Authorization": "Bearer " + token})
    else:
        log.warning("token      missing        set %s; every read becomes report-only",
                    args.token_env)

    rows = []
    for name in wanted:
        action, why = probe_safety(name, channel_available=bool(args.channel))
        if action != "probe" or not token:
            state = "report-only" if action != "needs-argument" else "needs-argument"
            log.warning("method     %-16s %-11s %s", name, state, why)
            rows.append((name, state))
        else:
            params = {} if name in ARG_FREE else {"channel": args.channel}
            state, detail = classify(get(session, name, params))
            level = log.info if state == "live" else log.warning
            level("method     %-16s %-11s %s", name, state, detail)
            rows.append((name, state))
        line = migration_for(name)
        if line:
            log.info("           migrate to       %s", line)
        if name in OWNED_ELSEWHERE:
            log.info("           see also         %s", OWNED_ELSEWHERE[name])

    state, detail = sweep_verdict(rows)
    if state == "clean":
        log.info("verdict    clean          %s", detail)
        return 0
    log.warning("verdict    %-14s %s", state, detail)
    log.warning("  repair: migrate the whole family at once; the four legacy list "
                "methods are one conversations.list call with "
                "types=public_channel,private_channel,im,mpim")
    log.warning("  repair: log body.warning and body.response_metadata.warnings at "
                "WARN, permanently; that is the only channel Slack has for the next "
                "retirement")
    log.warning("  note:   no deprecated write was issued to establish any of this")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-deprecated-methods.mjs",
"js": '''/**
 * Find the deprecated Slack methods your app still calls.
 *
 * Read only, and deliberately stricter than the question requires. The map
 * below records, for every legacy method, both its replacement and whether
 * issuing it is a read. Only the reads are ever issued. files.upload, im.open,
 * channels.create, mpim.open and the RTM session methods are deprecated
 * writes: they are named, mapped, and never called, because "does it still
 * work?" cannot be asked of a write without performing it.
 *
 * Three fields carry the answer and two of them ride on responses that
 * succeeded: body.warning and body.response_metadata.warnings[] are the only
 * form of this finding that arrives before the outage.
 */

const API = 'https://slack.com/api/';

// Legacy method -> [replacement, kind]. The kind is the safety half of the map.
export const REPLACEMENTS = {
  'channels.list': ['conversations.list, with types=public_channel', 'read'],
  'channels.info': ['conversations.info', 'read'],
  'channels.history': ['conversations.history', 'read'],
  'channels.replies': ['conversations.replies', 'read'],
  'channels.create': ['conversations.create', 'write'],
  'channels.invite': ['conversations.invite', 'write'],
  'channels.join': ['conversations.join', 'write'],
  'channels.archive': ['conversations.archive', 'write'],
  'groups.list': ['conversations.list, with types=private_channel', 'read'],
  'groups.info': ['conversations.info', 'read'],
  'groups.history': ['conversations.history', 'read'],
  'groups.replies': ['conversations.replies', 'read'],
  'groups.create': ['conversations.create, with is_private=true', 'write'],
  'im.list': ['conversations.list, with types=im', 'read'],
  'im.history': ['conversations.history', 'read'],
  'im.replies': ['conversations.replies', 'read'],
  'im.open': ['conversations.open', 'write'],
  'im.close': ['conversations.close', 'write'],
  'mpim.list': ['conversations.list, with types=mpim', 'read'],
  'mpim.history': ['conversations.history', 'read'],
  'mpim.open': ['conversations.open, with a comma separated users list', 'write'],
  'files.upload': ['files.getUploadURLExternal, then a plain upload, then '
    + 'files.completeUploadExternal', 'write'],
  'rtm.start': ['Socket Mode', 'write'],
  'rtm.connect': ['Socket Mode', 'write'],
};

// The methods that answer with no arguments at all.
export const ARG_FREE = ['channels.list', 'groups.list', 'im.list', 'mpim.list'];

// Two methods here are large enough to have their own note.
export const OWNED_ELSEWHERE = {
  'files.upload': '/slack/files-upload-retired/',
  'rtm.start': '/slack/rtm-legacy-still-used/',
  'rtm.connect': '/slack/rtm-legacy-still-used/',
};

// About the Content-Type header you sent, not about the method's future.
export const NOISE_WARNINGS = ['missing_charset', 'superfluous_charset'];

export const DEAD_ERRORS = ['method_deprecated', 'deprecated_endpoint'];
export const UNASSESSABLE = ['missing_scope', 'not_allowed_token_type',
  'invalid_auth', 'ratelimited', 'token_revoked', 'account_inactive'];

/** What replaced this method, and whether issuing it is a read. Pure. */
export function replacementFor(method) {
  const entry = REPLACEMENTS[String(method ?? '').trim()];
  if (!entry) return [null, 'unknown'];
  return entry;
}

/**
 * May this sweep issue this method itself? Pure.
 * Returns [action, why]; probe, report-only or needs-argument.
 */
export function probeSafety(method, channelAvailable = false) {
  const name = String(method ?? '').trim();
  const [, kind] = replacementFor(name);
  if (kind === 'write') {
    return ['report-only', 'this method writes; the sweep names it and does not '
      + 'call it'];
  }
  if (kind === 'unknown') {
    return ['report-only', 'this method is not in the map, so the sweep will not '
      + 'issue it on the chance that it is a read'];
  }
  if (ARG_FREE.includes(name)) {
    return ['probe', 'a read that answers with no arguments'];
  }
  if (channelAvailable) {
    return ['probe', 'a read, probed against the channel you passed'];
  }
  return ['needs-argument', 'pass --channel C... to probe the info and history '
    + 'methods; without one the answer is channel_not_found and says nothing '
    + 'about the method'];
}

/** The warnings in a response that are actually about deprecation. Pure. */
export function deprecationWarnings(body) {
  const doc = body ?? {};
  const raw = [doc.warning, ...((doc.response_metadata ?? {}).warnings ?? [])];
  const out = [];
  for (const item of raw) {
    const text = String(item ?? '').trim();
    if (text && !NOISE_WARNINGS.includes(text)) out.push(text);
  }
  return [...new Set(out)];
}

/**
 * Read one response body as a deprecation state. Pure.
 * Returns [state, detail]; removed, dead, scheduled, live, not-assessed, failed.
 */
export function classify(body) {
  const doc = body ?? {};
  const error = String(doc.error ?? '');
  if (doc.ok === true) {
    const warnings = deprecationWarnings(doc);
    if (warnings.length) {
      return ['scheduled', `ok true, and warning: ${warnings.join(', ')}`];
    }
    return ['live', 'ok true, and no deprecation warning'];
  }
  if (error === 'unknown_method') {
    return ['removed', 'unknown_method: the name is gone from the API'];
  }
  if (DEAD_ERRORS.includes(error)) return ['dead', error];
  if (UNASSESSABLE.includes(error)) {
    return ['not-assessed', `${error}, which is about the token rather than the method`];
  }
  if (!error) {
    return ['not-assessed', 'no ok field and no error, so nothing can be read from '
      + 'this response'];
  }
  return ['failed', `${error}, which is a different problem`];
}

/** The exact replacement line to print for one method. Pure. */
export function migrationFor(method) {
  const [replacement] = replacementFor(method);
  return replacement ?? null;
}

/** rows: [[method, state], ...]. Returns [state, detail]. Pure. */
export function sweepVerdict(rows) {
  const seen = (rows ?? []).map(([m, st]) => [String(m), String(st)]);
  if (!seen.length) {
    return ['no-methods', 'no method was checked, so there is nothing to say'];
  }
  const pick = (...states) => seen.filter(([, st]) => states.includes(st))
    .map(([m]) => m);
  const dead = pick('dead', 'removed');
  const scheduled = pick('scheduled');
  const named = pick('report-only');
  const assessed = pick('dead', 'removed', 'scheduled', 'live');
  if (dead.length && scheduled.length) {
    return ['dead', `${dead.length} method(s) already refused and ${scheduled.length} `
      + 'more are warning'];
  }
  if (dead.length) {
    return ['dead', `${dead.length} method(s) already refused: `
      + `${[...dead].sort().join(', ')}`];
  }
  if (scheduled.length) {
    return ['scheduled', `${scheduled.length} method(s) still work and are warning: `
      + `${[...scheduled].sort().join(', ')}`];
  }
  if (!assessed.length) {
    return ['not-assessed', `nothing was assessed; ${named.length} method(s) were `
      + 'named from the map and none was probed'];
  }
  return ['clean', `${assessed.length} method(s) probed and none is deprecated`];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function read(token, method, params) {
  const qs = new URLSearchParams(params ?? {}).toString();
  const url = `${API}${method}${qs ? `?${qs}` : ''}`;
  const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const channel = arg(args, '--channel');
  let wanted = arg(args, '--methods').split(',').map((m) => m.trim()).filter(Boolean);
  if (!wanted.length) wanted = Object.keys(REPLACEMENTS).sort();

  const token = process.env[tokenEnv];
  if (!token) {
    console.warn(`token      missing        set ${tokenEnv}; every read becomes `
      + 'report-only');
  }

  const rows = [];
  for (const name of wanted) {
    const [action, why] = probeSafety(name, Boolean(channel));
    const pad = name.padEnd(16);
    if (action !== 'probe' || !token) {
      const state = action === 'needs-argument' ? 'needs-argument' : 'report-only';
      console.warn(`method     ${pad} ${state.padEnd(11)} ${why}`);
      rows.push([name, state]);
    } else {
      const params = ARG_FREE.includes(name) ? {} : { channel };
      // eslint-disable-next-line no-await-in-loop
      const [state, detail] = classify(await read(token, name, params));
      const line = `method     ${pad} ${state.padEnd(11)} ${detail}`;
      if (state === 'live') console.log(line);
      else console.warn(line);
      rows.push([name, state]);
    }
    const line = migrationFor(name);
    if (line) console.log(`           migrate to       ${line}`);
    if (OWNED_ELSEWHERE[name]) {
      console.log(`           see also         ${OWNED_ELSEWHERE[name]}`);
    }
  }

  const [state, detail] = sweepVerdict(rows);
  if (state === 'clean') {
    console.log(`verdict    clean          ${detail}`);
    return;
  }
  console.warn(`verdict    ${state.padEnd(14)} ${detail}`);
  console.warn('  repair: migrate the whole family at once; the four legacy list '
    + 'methods are one conversations.list call with '
    + 'types=public_channel,private_channel,im,mpim');
  console.warn('  repair: log body.warning and body.response_metadata.warnings at '
    + 'WARN, permanently');
  console.warn('  note:   no deprecated write was issued to establish any of this');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions that carry the weight are the ones about restraint. Every deprecated write in the map has to come back <code>report-only</code>, and a method the map has never heard of has to come back <code>report-only</code> too rather than being assumed harmless. After that it is the warning filter: a response carrying only <code>missing_charset</code> is <code>live</code>, the same response carrying a real notice is <code>scheduled</code>, and a sweep in which nothing was probed refuses to say <code>clean</code>.",
"test_py_file": "test_slack_deprecated_methods.py",
"test_py": '''from slack_deprecated_methods import (
    REPLACEMENTS, classify, deprecation_warnings, migration_for, probe_safety,
    replacement_for, sweep_verdict,
)


def test_every_legacy_list_method_maps_to_the_one_replacement():
    for name in ("channels.list", "groups.list", "im.list", "mpim.list"):
        replacement, kind = replacement_for(name)
        assert replacement.startswith("conversations.list")
        assert kind == "read"


def test_an_unknown_method_is_not_assumed_to_be_a_read():
    assert replacement_for("chat.postMessage") == (None, "unknown")
    assert probe_safety("chat.postMessage")[0] == "report-only"


def test_every_deprecated_write_in_the_map_is_named_and_never_probed():
    writes = [m for m, (_r, kind) in REPLACEMENTS.items() if kind == "write"]
    assert "files.upload" in writes
    assert "im.open" in writes
    assert "rtm.connect" in writes
    for name in writes:
        action, why = probe_safety(name, channel_available=True)
        assert action == "report-only"
        assert "writes" in why


def test_the_argument_free_reads_are_probed_without_a_channel():
    assert probe_safety("channels.list")[0] == "probe"
    assert probe_safety("mpim.list")[0] == "probe"


def test_a_read_that_needs_a_channel_says_so_until_one_is_given():
    assert probe_safety("channels.history")[0] == "needs-argument"
    assert probe_safety("channels.history", channel_available=True)[0] == "probe"


def test_the_charset_warnings_are_not_deprecation_notices():
    assert deprecation_warnings({"ok": True, "warning": "missing_charset"}) == []
    assert deprecation_warnings(
        {"ok": True, "response_metadata": {"warnings": ["superfluous_charset"]}}) == []


def test_both_warning_channels_are_read_and_deduplicated():
    body = {"ok": True, "warning": "method_deprecated",
            "response_metadata": {"warnings": ["method_deprecated", "use_conversations"]}}
    assert deprecation_warnings(body) == ["method_deprecated", "use_conversations"]


def test_a_success_carrying_a_real_notice_is_the_finding_worth_having():
    state, detail = classify({"ok": True, "warning": "method_deprecated"})
    assert state == "scheduled"
    assert "method_deprecated" in detail


def test_a_success_carrying_only_charset_noise_is_simply_live():
    assert classify({"ok": True, "warning": "superfluous_charset"})[0] == "live"


def test_the_two_dead_errors_are_both_recognised():
    assert classify({"ok": False, "error": "method_deprecated"})[0] == "dead"
    assert classify({"ok": False, "error": "deprecated_endpoint"})[0] == "dead"


def test_unknown_method_is_removed_rather_than_merely_deprecated():
    state, detail = classify({"ok": False, "error": "unknown_method"})
    assert state == "removed"
    assert "gone" in detail


def test_a_token_problem_is_not_assessed_rather_than_counted_as_healthy():
    assert classify({"ok": False, "error": "missing_scope"})[0] == "not-assessed"
    assert classify({"ok": False, "error": "ratelimited"})[0] == "not-assessed"


def test_an_unrelated_error_is_handed_on_rather_than_absorbed():
    state, detail = classify({"ok": False, "error": "channel_not_found"})
    assert state == "failed"
    assert "different problem" in detail


def test_a_body_with_neither_ok_nor_error_is_not_assessed():
    assert classify({})[0] == "not-assessed"


def test_the_migration_line_names_the_parameter_that_has_to_come_with_it():
    assert "types=private_channel" in migration_for("groups.list")
    assert migration_for("nope.nope") is None


def test_a_dead_method_outranks_a_scheduled_one_in_the_verdict():
    state, detail = sweep_verdict([("channels.list", "dead"),
                                   ("groups.list", "scheduled")])
    assert state == "dead"
    assert "warning" in detail


def test_a_scheduled_method_is_a_finding_on_its_own():
    state, detail = sweep_verdict([("groups.list", "scheduled"),
                                   ("im.list", "live")])
    assert state == "scheduled"
    assert "groups.list" in detail


def test_a_sweep_that_probed_nothing_refuses_to_report_clean():
    state, detail = sweep_verdict([("files.upload", "report-only"),
                                   ("im.open", "report-only")])
    assert state == "not-assessed"
    assert "none was probed" in detail


def test_an_empty_sweep_says_so_instead_of_passing():
    assert sweep_verdict([])[0] == "no-methods"


def test_all_reads_probed_and_healthy_is_the_only_clean_verdict():
    state, detail = sweep_verdict([("channels.list", "live"), ("im.list", "live")])
    assert state == "clean"
    assert "2 method(s)" in detail
''',
"test_js_file": "slack-deprecated-methods.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  REPLACEMENTS, classify, deprecationWarnings, migrationFor, probeSafety,
  replacementFor, sweepVerdict,
} from './slack-deprecated-methods.mjs';

test('every legacy list method maps to the one replacement', () => {
  for (const name of ['channels.list', 'groups.list', 'im.list', 'mpim.list']) {
    const [replacement, kind] = replacementFor(name);
    assert.equal(replacement.startsWith('conversations.list'), true);
    assert.equal(kind, 'read');
  }
});

test('an unknown method is not assumed to be a read', () => {
  assert.deepEqual(replacementFor('chat.postMessage'), [null, 'unknown']);
  assert.equal(probeSafety('chat.postMessage')[0], 'report-only');
});

test('every deprecated write in the map is named and never probed', () => {
  const writes = Object.entries(REPLACEMENTS)
    .filter(([, [, kind]]) => kind === 'write').map(([m]) => m);
  assert.equal(writes.includes('files.upload'), true);
  assert.equal(writes.includes('im.open'), true);
  assert.equal(writes.includes('rtm.connect'), true);
  for (const name of writes) {
    const [action, why] = probeSafety(name, true);
    assert.equal(action, 'report-only');
    assert.match(why, /writes/);
  }
});

test('the argument free reads are probed without a channel', () => {
  assert.equal(probeSafety('channels.list')[0], 'probe');
  assert.equal(probeSafety('mpim.list')[0], 'probe');
});

test('a read that needs a channel says so until one is given', () => {
  assert.equal(probeSafety('channels.history')[0], 'needs-argument');
  assert.equal(probeSafety('channels.history', true)[0], 'probe');
});

test('the charset warnings are not deprecation notices', () => {
  assert.deepEqual(deprecationWarnings({ ok: true, warning: 'missing_charset' }), []);
  assert.deepEqual(deprecationWarnings(
    { ok: true, response_metadata: { warnings: ['superfluous_charset'] } }), []);
});

test('both warning channels are read and deduplicated', () => {
  const body = {
    ok: true,
    warning: 'method_deprecated',
    response_metadata: { warnings: ['method_deprecated', 'use_conversations'] },
  };
  assert.deepEqual(deprecationWarnings(body),
    ['method_deprecated', 'use_conversations']);
});

test('a success carrying a real notice is the finding worth having', () => {
  const [state, detail] = classify({ ok: true, warning: 'method_deprecated' });
  assert.equal(state, 'scheduled');
  assert.match(detail, /method_deprecated/);
});

test('a success carrying only charset noise is simply live', () => {
  assert.equal(classify({ ok: true, warning: 'superfluous_charset' })[0], 'live');
});

test('the two dead errors are both recognised', () => {
  assert.equal(classify({ ok: false, error: 'method_deprecated' })[0], 'dead');
  assert.equal(classify({ ok: false, error: 'deprecated_endpoint' })[0], 'dead');
});

test('unknown_method is removed rather than merely deprecated', () => {
  const [state, detail] = classify({ ok: false, error: 'unknown_method' });
  assert.equal(state, 'removed');
  assert.match(detail, /gone/);
});

test('a token problem is not assessed rather than counted as healthy', () => {
  assert.equal(classify({ ok: false, error: 'missing_scope' })[0], 'not-assessed');
  assert.equal(classify({ ok: false, error: 'ratelimited' })[0], 'not-assessed');
});

test('an unrelated error is handed on rather than absorbed', () => {
  const [state, detail] = classify({ ok: false, error: 'channel_not_found' });
  assert.equal(state, 'failed');
  assert.match(detail, /different problem/);
});

test('a body with neither ok nor error is not assessed', () => {
  assert.equal(classify({})[0], 'not-assessed');
});

test('the migration line names the parameter that has to come with it', () => {
  assert.match(migrationFor('groups.list'), /types=private_channel/);
  assert.equal(migrationFor('nope.nope'), null);
});

test('a dead method outranks a scheduled one in the verdict', () => {
  const [state, detail] = sweepVerdict([['channels.list', 'dead'],
    ['groups.list', 'scheduled']]);
  assert.equal(state, 'dead');
  assert.match(detail, /warning/);
});

test('a scheduled method is a finding on its own', () => {
  const [state, detail] = sweepVerdict([['groups.list', 'scheduled'],
    ['im.list', 'live']]);
  assert.equal(state, 'scheduled');
  assert.match(detail, /groups\\.list/);
});

test('a sweep that probed nothing refuses to report clean', () => {
  const [state, detail] = sweepVerdict([['files.upload', 'report-only'],
    ['im.open', 'report-only']]);
  assert.equal(state, 'not-assessed');
  assert.match(detail, /none was probed/);
});

test('an empty sweep says so instead of passing', () => {
  assert.equal(sweepVerdict([])[0], 'no-methods');
});

test('all reads probed and healthy is the only clean verdict', () => {
  const [state, detail] = sweepVerdict([['channels.list', 'live'],
    ['im.list', 'live']]);
  assert.equal(state, 'clean');
  assert.match(detail, /2 method\\(s\\)/);
});
''',
"faq": [
 ("Why does the script refuse to call files.upload or im.open when the whole point is to find out whether they still work?",
  "Because there is no read-only way to ask a write method that question. The only way to find out whether im.open still works is to open a conversation; the only way to find out whether channels.create still works is to create a channel with whatever name the probe invented. A diagnostic that does either has written to the workspace it was hired to inspect, and it will do so every time it runs. The map in this script records whether each legacy method is a read or a write, and the write half is reported from the map: the name, the replacement, and nothing sent."),
 ("My sweep says everything is live. Am I safe?",
  "Only for the methods it actually probed. Look at the verdict line rather than the rows: a sweep in which every row was report-only or needs-argument reports not-assessed, not clean, precisely because a token that can read nothing produces a spotless report. Pass --channel so the info and history methods can be probed, and pass --methods with the names your source really contains rather than sweeping the whole map, because a clean result on methods you never call is not evidence about the ones you do."),
 ("What is the difference between a warning and an error here?",
  "Timing, and it is the whole value of the check. An error means the method is already refusing you and the outage has happened. A warning arrives on a response that succeeded, returned its data and did everything you asked, and it is Slack telling you the method has a date on it. That notice is the only advance warning the API gives, and it is delivered in the one place production code never looks, because nothing needs investigating when the call worked."),
 ("Is files.upload covered by this note?",
  "It is named and handed over. files.upload was sunset on its own timetable and its replacement is a three-call sequence with failure modes of its own, so the sweep prints the method, the migration and a pointer, and the note linked below explains it properly. The same is true of the RTM transport: rtm.start and rtm.connect appear in the map because they belong in a sweep of your call sites, and the reason a modern app cannot use them at all is a different note about a scope that no longer exists."),
 ("I renamed channels.list to conversations.list and private channels disappeared. Why?",
  "Because the replacement is one method with a types parameter, and its default is public channels only. The old API forced you to write four calls, one per conversation type; the new one is a single call that has to be told which types you want. Migrating the method names one at a time and leaving the parameters alone loses private channels, DMs and group DMs silently, with no error anywhere, which is why the script prints the parameter alongside the replacement rather than just the new name."),
],
"related": [
 ("/slack/files-upload-retired/", "the one method in the map with its own timetable"),
 ("/slack/rtm-legacy-still-used/", "the retired transport, and the scope it needs"),
 ("/slack/http-200-ok-false/", "why a warning on a successful response goes unread"),
],
"citations": [CITE_METHODS, CITE_CONVERSATIONS_LIST, CITE_CHANGELOG_2024,
              CITE_CONVERSATIONS_API],
})
GUIDES.append({
"slug": "app-home-tab-disabled",
"title": "views.publish succeeds and the Home tab is switched off",
"description": "Publishing to a surface nobody can reach returns ok: true. Read the switch, the app_home_opened subscription, and which members have ever been published to.",
"h1": "views.publish succeeds and the Home tab is switched off",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack home tab not showing",
             "slack views.publish ok true nothing happens",
             "home_tab_enabled manifest slack",
             "slack app_home_opened not firing",
             "slack app home empty for some users"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token with app_configurations:read for the manifest, a bot token with users:read for the member list, and your own views.publish log as JSON",
"lead": "The dashboard is finished. Four sections, a refresh button, a chart that took a fortnight, and <code>views.publish</code> returns <code>{\"ok\": true}</code> with a <code>view</code> object and a real view id every single time it runs. You open the app in Slack to admire it and there is no Home tab on the profile at all &mdash; just About, and a Messages tab you never asked for.</p><p>Nothing failed. Nothing will fail. <code>views.publish</code> will keep answering <code>ok: true</code> for as long as you keep calling it, because the method's job is to store a view for a user, and it does that faithfully whether or not there is a tab through which anybody can see it.",
"short_answer": """<p>The Home tab is a switch in app configuration, under <strong>App Home &rarr; Show Tabs &rarr; Home Tab</strong>, and in the manifest it is <code>features.app_home.home_tab_enabled</code>. With it off, <code>views.publish</code> still succeeds &mdash; the view is stored against the user &mdash; and the surface it was stored for is not rendered. There is no error, no warning and no field on the response that says so.</p>
<p>The second half is a subscription. The published view is <strong>per user and per installation</strong>, so there is no such thing as publishing the Home tab once. Slack sends <code>app_home_opened</code> when a person opens the tab, and that event is the cue to publish for <em>that</em> person. An app that publishes at startup for the users it happens to know about leaves everybody who joined afterwards looking at an empty tab, forever, with no error on either side.</p>
<p>This is a different switch from the Messages tab, and the difference is worth stating plainly because they sit next to each other in the same settings panel. The Messages tab governs whether a person may type at your app, and refusing it produces an actual error string, <code>messages_tab_disabled</code>. The Home tab governs whether a view you published is reachable, and refusing it produces nothing at all. One fails loudly on the way in; the other succeeds quietly on the way out.</p>""",
"problem": """<p>Every signal available to your code says the feature works. The call returns <code>ok: true</code>. The response carries a <code>view</code> object with an id, a hash and the blocks you sent, echoed back. Your integration tests assert on that response and pass. Your metrics show a healthy publish rate. The only place the failure exists is on a profile page in a Slack client, and there is no API that will tell you what that page looks like.</p>
<p>The switch is off by default on a new app, which means this is not something that broke. It is something that was never on, so there is no change to bisect, no deploy to roll back, and no correlation with anything. Teams reach for the blocks first, because a Home tab that renders empty and a Home tab that does not exist look identical from the outside, and they spend an afternoon simplifying a view that was never going to be shown.</p>
<p>The staleness shape is worse, because it works for the person testing it. The developer opens the app, the handler fires, a view is published for them, the tab looks perfect. Every other member of the workspace has never triggered a publish, so they open the same app and see the empty state. The bug report reads &ldquo;it works for you and not for me&rdquo;, which is the least tractable sentence in software, and the cause is that the view is stored per user and nobody thought to ask what happens for a user who has never been stored against.</p>
<p>Then there is drift, which is the version of this that arrives months later. A view published in March against a user who has not opened the app since is still sitting there in March's state, showing March's numbers, with a button wired to a March action id your handler no longer recognises. Nothing expires it. The Home tab has no notion of a stale view, so a publish-once app degrades into a museum, and the only clue is that the numbers on it are wrong rather than absent.</p>""",
"why": """<p><strong>The failure has no error, so it has to be read from configuration and from coverage.</strong> There is no call that returns &ldquo;this user cannot see a Home tab&rdquo;, and <code>views.publish</code> is a write, so a diagnostic cannot even reproduce the symptom without publishing. Everything here is read: the manifest for the switch and the subscription, <code>users.list</code> for who exists, and your own publish log for who has been served.</p>
<p><strong>Coverage is the measurement, because the surface is per user.</strong> A publish rate is not evidence; forty thousand publishes for the same eleven people is a broken feature with excellent metrics. What settles it is the set difference between the members of the workspace and the users who have ever appeared in a publish record, and that number is usually startling the first time somebody looks at it.</p>
<p><strong>The cadence is a separate finding from the coverage, and both are separate from the switch.</strong> An app can have the tab enabled, the subscription in place, and still publish only at boot because the handler was written before the event was wired up. So the script reports the switch, the trigger mix and the coverage independently, and only then combines them, because each one has a different repair and fixing the wrong one costs a week.</p>
<p><strong>Staleness is measured per user, not per app.</strong> The question is not when the app last published anything; it is how long ago each individual user's view was written, because that is the state they are looking at right now. A single recent publish for one active user makes an app look healthy while four hundred people stare at last quarter.</p>
<p><strong>This is not the Messages tab note, and the script says so out loud.</strong> If the manifest shows the Home tab off and the Messages tab on, that is an app with a DM surface and no dashboard, and the two have different switches, different symptoms and different repairs. The check prints the pointer rather than quietly folding them together, because &ldquo;the App Home is disabled&rdquo; is a sentence that has sent a great many people to flip the wrong checkbox.</p>
<p><strong>The repair is printed as manifest keys.</strong> A checkbox in a web console exists in one place and is invisible to review, which is exactly how an app ships with the switch off in the first place. <code>features.app_home.home_tab_enabled: true</code> in a manifest that lives in your repository is a switch that stays on for the next app too.</p>""",
"steps": [
 {"h": "Read the switch and the subscription from the manifest",
  "body": """<p><code>apps.manifest.export</code> returns <code>features.app_home</code> and <code>settings.event_subscriptions</code>. It needs an app configuration token, which is a different credential class from the bot token your app runs on; without one the script skips to the coverage half, which needs only <code>users:read</code> and your own log.</p>"""},
 {"h": "Take every finding at once, not the first one",
  "body": """<p><code>home_tab_findings</code> returns <code>home-tab-off</code>, <code>no-app-home-opened-subscription</code> and <code>messages-tab-only</code> as a list. The last of those is a pointer rather than a fault: it fires when the Home tab is off and the Messages tab is on, which means you are looking at the other note.</p>"""},
 {"h": "Classify what triggers your publishes",
  "body": """<p><code>publish_cadence</code> reads the <code>trigger</code> field on your own publish records and answers <code>on-open</code>, <code>startup-only</code>, <code>mixed</code> or <code>no-records</code>. <code>startup-only</code> is the finding that explains &ldquo;it works for you and not for me&rdquo;, because the set of users published to at boot is the set of users you already knew about.</p>"""},
 {"h": "Measure coverage against the actual member list",
  "body": """<p><code>publish_coverage</code> holds <code>users.list</code>, with bots and deactivated accounts removed, against the user ids in your publish log. It answers <code>covered</code>, <code>partial</code>, <code>none-published</code> or <code>no-members</code>, and the count of people who have never had a view stored for them is the number to put in the ticket.</p>"""},
 {"h": "Ask how old each user's view is",
  "body": """<p><code>staleness</code> takes the most recent publish per user rather than the most recent publish overall, because the second number is always reassuring and never relevant. A user whose view was written four months ago is looking at four-month-old blocks with four-month-old action ids in them.</p>"""},
 {"h": "Publish in the app_home_opened handler and nowhere else",
  "body": """<p>The repair is a shape rather than a setting. Subscribe to <code>app_home_opened</code>, publish the view inside that handler for <code>event.user</code>, and let every open refresh it. Startup publishing then becomes unnecessary, staleness stops being possible, and coverage takes care of itself.</p>"""},
],
"verify": """<p>Turn the switch on, move the publish into the event handler, and re-run after a day of real use. Coverage climbs on its own as people open the app, and <code>cadence</code> should read <code>on-open</code>.</p>
<pre><code class="language-bash">python3 slack_home_tab.py --app-id A05NW7XQ1 --publishes publishes.json
# manifest   ok                     features.app_home read for A05NW7XQ1
# config     home-tab-off           the Home tab is off, so views.publish stores a
#                                   view for a surface that is not rendered
# config     no-app-home-opened-subscription
#                                   app_home_opened is not subscribed, so nothing
#                                   tells the app when to publish for a user
# members    412 member(s)          bots and deactivated accounts removed
# cadence    startup-only           97 record(s), all triggered at startup; a user
#                                   who joined since the last restart has no view
# coverage   partial                11 of 412 member(s) have ever been published to;
#                                   401 have never had a view stored
# stale      stale                  9 of 11 user(s) were last published to more than
#                                   30 days ago
# verdict    tab-off                the switch, the subscription and the coverage all
#                                   point the same way
# repair: features.app_home.home_tab_enabled: true
# repair: settings.event_subscriptions.bot_events: add app_home_opened
# repair: publish inside the app_home_opened handler, for event.user, on every open</code></pre>""",
"code_intro": "Two halves that do not need each other. <code>home_tab_findings</code> reads the manifest and returns a list, because the switch and the subscription are separate settings that fail together and get fixed one at a time. The other half needs no configuration credential at all: <code>publish_cadence</code> reads what triggers your publishes, <code>publish_coverage</code> is a set difference between the workspace's members and the users you have ever published for, and <code>staleness</code> asks the per-user question rather than the flattering per-app one. <code>home_verdict</code> combines them and is allowed to say that the switch is fine and the loop is not.",
"py_file": "slack_home_tab.py",
"py": '''"""Decide whether your App Home Home tab is reachable, and by whom.

Read only. Two GET methods are used: apps.manifest.export with an app
configuration token for the switch and the subscription, and users.list with a
bot token for the member list. views.publish is never called - it is a write,
it stores a view against a user, and a diagnostic that runs it changes what the
user sees in order to find out what the user sees.

The third input is your own publish log, as JSON: a list of records carrying at
least user, trigger and ts. That is the only place the per-user history of this
surface exists, because Slack offers no method that reports which users have a
published view.

Either half runs without the other. Most readers have a bot token and no app
configuration token, and the coverage half is the one that does not need it.
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_home_tab")

API = "https://slack.com/api/"

# The event that tells the app a particular person is looking at the tab right
# now. Without it there is no cue to publish for anyone in particular, which is
# the whole reason a publish-once app leaves most of a workspace with an empty
# surface.
OPEN_EVENT = "app_home_opened"

# The triggers that mean "we published for the users we already knew about",
# as opposed to publishing for the person who just opened the tab.
STARTUP_TRIGGERS = ("startup", "boot", "deploy", "cron", "schedule")

REPAIRS = {
    "home-tab-off": "features.app_home.home_tab_enabled: true",
    "no-app-home-opened-subscription":
        "settings.event_subscriptions.bot_events: add app_home_opened",
}

DAY = 86400.0


def home_tab_findings(manifest):
    """Every App Home setting relevant to the Home tab, as a list. Pure.

    Returns a list of (code, detail). A list rather than a verdict because the
    switch and the subscription are two settings that fail together and get
    fixed one at a time, and a check that reported only the first would be
    answered with "I turned it on and it is still empty" a week later.

    messages-tab-only is a pointer rather than a fault: the Messages tab is a
    different switch with a different symptom, and conflating the two is how
    somebody ends up flipping the wrong checkbox.
    """
    if not manifest:
        return [("no-manifest", "no manifest was read, so the switch itself could "
                                "not be inspected; the coverage below needs no "
                                "configuration token")]
    body = manifest.get("manifest") or manifest
    features = (body.get("features") or {}).get("app_home") or {}
    events = (body.get("settings") or {}).get("event_subscriptions") or {}
    bot_events = set(events.get("bot_events") or [])
    out = []
    if not features.get("home_tab_enabled"):
        out.append(("home-tab-off", "the Home tab is off, so views.publish stores a "
                                    "view for a surface that is not rendered and "
                                    "still answers ok true"))
        if features.get("messages_tab_enabled"):
            out.append(("messages-tab-only", "the Messages tab is on and the Home tab "
                                             "is off; those are different switches "
                                             "with different symptoms"))
    if OPEN_EVENT not in bot_events:
        out.append(("no-app-home-opened-subscription", "app_home_opened is not "
                                                       "subscribed, so nothing tells "
                                                       "the app when to publish for a "
                                                       "particular user"))
    return out


def publish_cadence(records):
    """What triggers your publishes? Pure.

    records: [{"user": "U...", "trigger": "app_home_opened", "ts": 1.7e9}, ...]

    Returns (state, counts).

      no-records    nothing to read.
      on-open       every publish was triggered by app_home_opened. Correct.
      startup-only  every publish happened at boot, for the users the process
                    already knew about. This is the shape that produces "it
                    works for you and not for me".
      mixed         both, which is usually a migration in progress.
      unknown-trigger  the records carry no trigger the script recognises.
    """
    rows = [r for r in (records or []) if isinstance(r, dict)]
    counts = {"records": len(rows), "on_open": 0, "startup": 0, "other": 0}
    if not rows:
        return ("no-records", counts)
    for row in rows:
        trigger = str(row.get("trigger") or "").strip().lower()
        if trigger == OPEN_EVENT:
            counts["on_open"] += 1
        elif trigger in STARTUP_TRIGGERS:
            counts["startup"] += 1
        else:
            counts["other"] += 1
    if counts["on_open"] and counts["startup"]:
        return ("mixed", counts)
    if counts["on_open"]:
        return ("on-open", counts)
    if counts["startup"]:
        return ("startup-only", counts)
    return ("unknown-trigger", counts)


def publish_coverage(members, records):
    """How much of the workspace has ever had a view stored for it? Pure.

    members: user ids from users.list, already filtered.
    records: your publish log.

    Returns (state, counts). A publish rate is not evidence: forty thousand
    publishes for the same eleven people is a broken feature with excellent
    metrics. The set difference is the measurement.
    """
    people = [str(m) for m in (members or []) if str(m or "")]
    served = {str((r or {}).get("user") or "") for r in (records or [])
              if isinstance(r, dict)}
    served.discard("")
    covered = [m for m in people if m in served]
    counts = {"members": len(people), "covered": len(covered),
              "never": len(people) - len(covered)}
    if not people:
        return ("no-members", counts)
    if not covered:
        return ("none-published", counts)
    if counts["never"]:
        return ("partial", counts)
    return ("covered", counts)


def staleness(records, now=None, max_age_days=30):
    """How old is each user's view? Pure.

    Takes the most recent publish per user rather than the most recent publish
    overall, because the second number is always reassuring and never relevant:
    one active user refreshed this morning tells you nothing about the four
    hundred people looking at last quarter.

    Returns (state, counts).
    """
    now = float(now if now is not None else time.time())
    latest = {}
    for row in (records or []):
        if not isinstance(row, dict):
            continue
        user = str(row.get("user") or "")
        try:
            ts = float(row.get("ts") or 0)
        except (TypeError, ValueError):
            ts = 0.0
        if not user or not ts:
            continue
        latest[user] = max(latest.get(user, 0.0), ts)
    counts = {"users": len(latest), "stale": 0, "fresh": 0}
    if not latest:
        return ("no-records", counts)
    cutoff = now - float(max_age_days) * DAY
    for ts in latest.values():
        if ts < cutoff:
            counts["stale"] += 1
        else:
            counts["fresh"] += 1
    return (("stale", counts) if counts["stale"] else ("fresh", counts))


def home_verdict(codes, cadence, coverage):
    """Hold the switch, the cadence and the coverage against each other. Pure.

    Returns (verdict, detail). Allowed to contradict any of the three, and its
    most useful answer is publish-loop: every switch is correct, the
    subscription is in place, and most of the workspace has still never had a
    view stored, which puts the fault in your handler rather than in a setting.
    """
    found = set(codes or [])
    if "home-tab-off" in found:
        return ("tab-off", "the Home tab is off, so nothing published for anybody is "
                           "reachable; fix this before reading the coverage")
    if "no-app-home-opened-subscription" in found:
        return ("no-subscription", "the tab is on and nothing tells the app when to "
                                   "fill it, so only the users it publishes to by "
                                   "some other route have a view")
    if "no-manifest" in found:
        return ("coverage-only", "the switch was not readable, so this verdict rests "
                                 "on the publish log and the member list alone")
    if cadence == "startup-only":
        return ("publish-once", "every publish happened at startup, so anybody who "
                                "joined since the last restart has an empty tab")
    if coverage in ("none-published", "partial"):
        return ("under-published", "the configuration is correct and most of the "
                                   "workspace has still never had a view stored")
    if cadence == "no-records":
        return ("no-evidence", "no publish records were given, so there is nothing to "
                               "conclude about coverage")
    return ("consistent", "the tab is on, the event is subscribed, and every member "
                          "has a published view")


def repair_manifest(codes):
    """Turn findings into the exact manifest lines that fix them. Pure."""
    return [REPAIRS[code] for code in codes if code in REPAIRS]


def get(session, method, params=None, token=None):
    """One GET against the Web API. Returns the parsed body."""
    headers = {"Authorization": "Bearer " + token} if token else None
    r = session.get(API + method, params=params or {}, headers=headers, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def real_members(session, limit):
    """users.list with bots and deactivated accounts removed. A read."""
    body = get(session, "users.list", {"limit": str(limit)})
    if body.get("ok") is not True:
        log.warning("members    unavailable            %s", body.get("error"))
        return []
    out = []
    for user in body.get("members") or []:
        if (user or {}).get("is_bot") or (user or {}).get("deleted"):
            continue
        if (user or {}).get("id") == "USLACKBOT":
            continue
        out.append((user or {}).get("id"))
    return [u for u in out if u]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app-id", default="", help="the app id to export, A...")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_ACCESS_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a bot token with users:read")
    ap.add_argument("--publishes", default="",
                    help="your own views.publish log as JSON: a list of records "
                         "carrying user, trigger and ts")
    ap.add_argument("--max-age-days", type=int, default=30)
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()

    session = requests.Session()
    manifest = {}
    config_token = os.environ.get(args.config_token_env)
    if args.app_id and config_token:
        body = get(session, "apps.manifest.export", {"app_id": args.app_id},
                   token=config_token)
        if body.get("ok") is not True:
            log.warning("manifest   unavailable            apps.manifest.export "
                        "answered ok: false, error=%s", body.get("error"))
        else:
            manifest = body
            log.info("manifest   ok                     features.app_home read for %s",
                     args.app_id)
    else:
        log.info("manifest   skipped                set %s and --app-id to read the "
                 "switch itself", args.config_token_env)

    findings = home_tab_findings(manifest)
    for code, detail in findings:
        (log.info if code in ("no-manifest", "messages-tab-only") else log.warning)(
            "config     %-22s %s", code, detail)
    if any(code == "messages-tab-only" for code, _d in findings):
        log.info("           see also               /slack/messages-tab-disabled/")

    records = []
    if args.publishes:
        with open(args.publishes, encoding="utf-8") as handle:
            records = json.load(handle) or []
        log.info("publishes  %d record(s)", len(records))

    members = []
    token = os.environ.get(args.token_env)
    if token:
        session.headers.update({"Authorization": "Bearer " + token})
        members = real_members(session, args.limit)
        log.info("members    %d member(s)             bots and deactivated accounts "
                 "removed", len(members))
    else:
        log.info("members    skipped                set %s to a bot token with "
                 "users:read", args.token_env)

    cadence, cadence_counts = publish_cadence(records)
    (log.info if cadence == "on-open" else log.warning)(
        "cadence    %-22s %s", cadence, cadence_counts)
    coverage, coverage_counts = publish_coverage(members, records)
    (log.info if coverage in ("covered", "no-members") else log.warning)(
        "coverage   %-22s %s", coverage, coverage_counts)
    stale, stale_counts = staleness(records, max_age_days=args.max_age_days)
    (log.info if stale != "stale" else log.warning)(
        "stale      %-22s %s", stale, stale_counts)

    codes = [c for c, _d in findings]
    verdict, detail = home_verdict(codes, cadence, coverage)
    (log.info if verdict in ("consistent", "no-evidence") else log.warning)(
        "verdict    %-22s %s", verdict, detail)
    for line in repair_manifest(codes):
        log.warning("repair: %s", line)
    if verdict != "consistent":
        log.warning("repair: publish inside the app_home_opened handler, for "
                    "event.user, on every open")
    return 0 if verdict in ("consistent", "no-evidence") else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-home-tab.mjs",
"js": '''/**
 * Decide whether your App Home Home tab is reachable, and by whom.
 *
 * Read only. Two GET methods are used: apps.manifest.export with an app
 * configuration token for the switch and the subscription, and users.list with
 * a bot token for the member list. views.publish is never called - it is a
 * write, and a diagnostic that runs it changes what the user sees in order to
 * find out what the user sees.
 *
 * The third input is your own publish log, as JSON. That is the only place the
 * per-user history of this surface exists.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// The event that tells the app a particular person is looking at the tab now.
export const OPEN_EVENT = 'app_home_opened';

// Triggers that mean "we published for the users we already knew about".
export const STARTUP_TRIGGERS = ['startup', 'boot', 'deploy', 'cron', 'schedule'];

export const REPAIRS = {
  'home-tab-off': 'features.app_home.home_tab_enabled: true',
  'no-app-home-opened-subscription':
    'settings.event_subscriptions.bot_events: add app_home_opened',
};

const DAY = 86400;

/** Every App Home setting relevant to the Home tab, as a list. Pure. */
export function homeTabFindings(manifest) {
  if (!manifest || !Object.keys(manifest).length) {
    return [['no-manifest', 'no manifest was read, so the switch itself could not be '
      + 'inspected; the coverage below needs no configuration token']];
  }
  const body = manifest.manifest ?? manifest;
  const features = (body.features ?? {}).app_home ?? {};
  const events = (body.settings ?? {}).event_subscriptions ?? {};
  const botEvents = new Set(events.bot_events ?? []);
  const out = [];
  if (!features.home_tab_enabled) {
    out.push(['home-tab-off', 'the Home tab is off, so views.publish stores a view '
      + 'for a surface that is not rendered and still answers ok true']);
    if (features.messages_tab_enabled) {
      out.push(['messages-tab-only', 'the Messages tab is on and the Home tab is off; '
        + 'those are different switches with different symptoms']);
    }
  }
  if (!botEvents.has(OPEN_EVENT)) {
    out.push(['no-app-home-opened-subscription', 'app_home_opened is not subscribed, '
      + 'so nothing tells the app when to publish for a particular user']);
  }
  return out;
}

/**
 * What triggers your publishes? Pure.
 * Returns [state, counts]; no-records, on-open, startup-only, mixed,
 * unknown-trigger.
 */
export function publishCadence(records) {
  const rows = (records ?? []).filter((r) => r && typeof r === 'object');
  const counts = { records: rows.length, on_open: 0, startup: 0, other: 0 };
  if (!rows.length) return ['no-records', counts];
  for (const row of rows) {
    const trigger = String(row.trigger ?? '').trim().toLowerCase();
    if (trigger === OPEN_EVENT) counts.on_open += 1;
    else if (STARTUP_TRIGGERS.includes(trigger)) counts.startup += 1;
    else counts.other += 1;
  }
  if (counts.on_open && counts.startup) return ['mixed', counts];
  if (counts.on_open) return ['on-open', counts];
  if (counts.startup) return ['startup-only', counts];
  return ['unknown-trigger', counts];
}

/**
 * How much of the workspace has ever had a view stored for it? Pure.
 * Returns [state, counts]; no-members, none-published, partial, covered.
 */
export function publishCoverage(members, records) {
  const people = (members ?? []).map((m) => String(m ?? '')).filter(Boolean);
  const served = new Set((records ?? [])
    .filter((r) => r && typeof r === 'object')
    .map((r) => String(r.user ?? '')).filter(Boolean));
  const covered = people.filter((m) => served.has(m));
  const counts = {
    members: people.length,
    covered: covered.length,
    never: people.length - covered.length,
  };
  if (!people.length) return ['no-members', counts];
  if (!covered.length) return ['none-published', counts];
  if (counts.never) return ['partial', counts];
  return ['covered', counts];
}

/**
 * How old is each user's view? Pure. Takes the most recent publish per user
 * rather than the most recent publish overall, because the second number is
 * always reassuring and never relevant.
 */
export function staleness(records, now = null, maxAgeDays = 30) {
  const at = Number(now ?? Date.now() / 1000);
  const latest = new Map();
  for (const row of records ?? []) {
    if (!row || typeof row !== 'object') continue;
    const user = String(row.user ?? '');
    const ts = Number(row.ts ?? 0);
    if (!user || !ts || Number.isNaN(ts)) continue;
    latest.set(user, Math.max(latest.get(user) ?? 0, ts));
  }
  const counts = { users: latest.size, stale: 0, fresh: 0 };
  if (!latest.size) return ['no-records', counts];
  const cutoff = at - Number(maxAgeDays) * DAY;
  for (const ts of latest.values()) {
    if (ts < cutoff) counts.stale += 1;
    else counts.fresh += 1;
  }
  return [counts.stale ? 'stale' : 'fresh', counts];
}

/** Hold the switch, the cadence and the coverage against each other. Pure. */
export function homeVerdict(codes, cadence, coverage) {
  const found = new Set(codes ?? []);
  if (found.has('home-tab-off')) {
    return ['tab-off', 'the Home tab is off, so nothing published for anybody is '
      + 'reachable; fix this before reading the coverage'];
  }
  if (found.has('no-app-home-opened-subscription')) {
    return ['no-subscription', 'the tab is on and nothing tells the app when to fill '
      + 'it, so only the users it publishes to by some other route have a view'];
  }
  if (found.has('no-manifest')) {
    return ['coverage-only', 'the switch was not readable, so this verdict rests on '
      + 'the publish log and the member list alone'];
  }
  if (cadence === 'startup-only') {
    return ['publish-once', 'every publish happened at startup, so anybody who joined '
      + 'since the last restart has an empty tab'];
  }
  if (coverage === 'none-published' || coverage === 'partial') {
    return ['under-published', 'the configuration is correct and most of the workspace '
      + 'has still never had a view stored'];
  }
  if (cadence === 'no-records') {
    return ['no-evidence', 'no publish records were given, so there is nothing to '
      + 'conclude about coverage'];
  }
  return ['consistent', 'the tab is on, the event is subscribed, and every member has '
    + 'a published view'];
}

/** Turn findings into the exact manifest lines that fix them. Pure. */
export function repairManifest(codes) {
  return (codes ?? []).filter((c) => REPAIRS[c]).map((c) => REPAIRS[c]);
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function read(method, params, token) {
  const qs = new URLSearchParams(params ?? {}).toString();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const r = await fetch(`${API}${method}${qs ? `?${qs}` : ''}`, { headers });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const appId = arg(args, '--app-id');
  const configTokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_ACCESS_TOKEN');
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const maxAgeDays = Number(arg(args, '--max-age-days', '30'));

  let manifest = {};
  const configToken = process.env[configTokenEnv];
  if (appId && configToken) {
    const body = await read('apps.manifest.export', { app_id: appId }, configToken);
    if (body.ok !== true) {
      console.warn('manifest   unavailable            apps.manifest.export answered '
        + `ok: false, error=${body.error}`);
    } else {
      manifest = body;
      console.log(`manifest   ok                     features.app_home read for ${appId}`);
    }
  } else {
    console.log(`manifest   skipped                set ${configTokenEnv} and --app-id `
      + 'to read the switch itself');
  }

  const findings = homeTabFindings(manifest);
  for (const [code, detail] of findings) {
    const line = `config     ${code.padEnd(22)} ${detail}`;
    if (code === 'no-manifest' || code === 'messages-tab-only') console.log(line);
    else console.warn(line);
  }
  if (findings.some(([code]) => code === 'messages-tab-only')) {
    console.log('           see also               /slack/messages-tab-disabled/');
  }

  let records = [];
  const publishes = arg(args, '--publishes');
  if (publishes) {
    records = JSON.parse(await readFile(publishes, 'utf8')) ?? [];
    console.log(`publishes  ${records.length} record(s)`);
  }

  let members = [];
  const token = process.env[tokenEnv];
  if (token) {
    const body = await read('users.list', { limit: arg(args, '--limit', '200') }, token);
    if (body.ok !== true) {
      console.warn(`members    unavailable            ${body.error}`);
    } else {
      members = (body.members ?? [])
        .filter((u) => u && !u.is_bot && !u.deleted && u.id !== 'USLACKBOT')
        .map((u) => u.id);
      console.log(`members    ${members.length} member(s)             bots and `
        + 'deactivated accounts removed');
    }
  } else {
    console.log(`members    skipped                set ${tokenEnv} to a bot token `
      + 'with users:read');
  }

  const [cadence, cadenceCounts] = publishCadence(records);
  const cadenceLine = `cadence    ${cadence.padEnd(22)} ${JSON.stringify(cadenceCounts)}`;
  if (cadence === 'on-open') console.log(cadenceLine);
  else console.warn(cadenceLine);

  const [coverage, coverageCounts] = publishCoverage(members, records);
  const coverageLine = `coverage   ${coverage.padEnd(22)} `
    + `${JSON.stringify(coverageCounts)}`;
  if (coverage === 'covered' || coverage === 'no-members') console.log(coverageLine);
  else console.warn(coverageLine);

  const [stale, staleCounts] = staleness(records, null, maxAgeDays);
  const staleLine = `stale      ${stale.padEnd(22)} ${JSON.stringify(staleCounts)}`;
  if (stale === 'stale') console.warn(staleLine);
  else console.log(staleLine);

  const codes = findings.map(([code]) => code);
  const [verdict, detail] = homeVerdict(codes, cadence, coverage);
  const verdictLine = `verdict    ${verdict.padEnd(22)} ${detail}`;
  if (verdict === 'consistent' || verdict === 'no-evidence') console.log(verdictLine);
  else console.warn(verdictLine);
  for (const line of repairManifest(codes)) console.warn(`repair: ${line}`);
  if (verdict !== 'consistent') {
    console.warn('repair: publish inside the app_home_opened handler, for event.user, '
      + 'on every open');
  }
  if (verdict !== 'consistent' && verdict !== 'no-evidence') process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures carry no credential, because nothing here needs one: a manifest fragment, a list of user ids, and a publish log with a trigger and a timestamp on each row. The assertions worth reading are the ones that keep the three findings apart. A manifest with the Home tab off and the Messages tab on has to produce the pointer to the other note rather than silently folding them together. Coverage has to be a set difference rather than a count of records, so eleven users and forty thousand publishes still reads as <code>partial</code>. And staleness has to be measured per user, so one refresh this morning does not make four hundred stale views look fresh.",
"test_py_file": "test_slack_home_tab.py",
"test_py": '''from slack_home_tab import (
    home_tab_findings, home_verdict, publish_cadence, publish_coverage,
    repair_manifest, staleness,
)

NOW = 1_800_000_000.0
DAY = 86400.0


def manifest(home=True, messages=False, events=("app_home_opened",)):
    return {"manifest": {
        "features": {"app_home": {"home_tab_enabled": home,
                                  "messages_tab_enabled": messages}},
        "settings": {"event_subscriptions": {"bot_events": list(events)}},
    }}


def codes_of(found):
    return [c for c, _d in found]


def test_a_correct_manifest_produces_no_findings_at_all():
    assert home_tab_findings(manifest()) == []


def test_the_home_tab_switch_is_reported_with_the_reason_there_is_no_error():
    found = home_tab_findings(manifest(home=False))
    assert "home-tab-off" in codes_of(found)
    assert "ok true" in dict(found)["home-tab-off"]


def test_a_missing_subscription_is_its_own_finding_on_an_enabled_tab():
    found = home_tab_findings(manifest(home=True, events=()))
    assert codes_of(found) == ["no-app-home-opened-subscription"]


def test_both_settings_wrong_are_both_reported_rather_than_the_first_one():
    found = home_tab_findings(manifest(home=False, events=()))
    assert "home-tab-off" in codes_of(found)
    assert "no-app-home-opened-subscription" in codes_of(found)


def test_a_messages_tab_without_a_home_tab_points_at_the_other_note():
    found = home_tab_findings(manifest(home=False, messages=True))
    assert "messages-tab-only" in codes_of(found)
    assert "different switches" in dict(found)["messages-tab-only"]


def test_no_manifest_says_what_is_still_readable_without_one():
    found = home_tab_findings({})
    assert codes_of(found) == ["no-manifest"]
    assert "configuration token" in dict(found)["no-manifest"]


def test_publishing_on_open_is_the_correct_cadence():
    state, counts = publish_cadence([{"user": "U1", "trigger": "app_home_opened"},
                                     {"user": "U2", "trigger": "app_home_opened"}])
    assert state == "on-open"
    assert counts["on_open"] == 2


def test_publishing_at_boot_only_is_the_shape_that_works_for_the_developer():
    state, counts = publish_cadence([{"user": "U1", "trigger": "startup"},
                                     {"user": "U2", "trigger": "deploy"}])
    assert state == "startup-only"
    assert counts["startup"] == 2


def test_a_migration_in_progress_reads_as_mixed():
    state, _counts = publish_cadence([{"user": "U1", "trigger": "startup"},
                                      {"user": "U2", "trigger": "app_home_opened"}])
    assert state == "mixed"


def test_an_unrecognised_trigger_is_named_rather_than_counted_as_correct():
    state, counts = publish_cadence([{"user": "U1", "trigger": "manual"}])
    assert state == "unknown-trigger"
    assert counts["other"] == 1


def test_an_empty_publish_log_is_no_records():
    assert publish_cadence([])[0] == "no-records"


def test_coverage_is_a_set_difference_not_a_count_of_publishes():
    records = [{"user": "U1"} for _ in range(40000)]
    state, counts = publish_coverage(["U1", "U2", "U3"], records)
    assert state == "partial"
    assert counts["never"] == 2
    assert counts["covered"] == 1


def test_everybody_served_is_covered():
    state, counts = publish_coverage(["U1", "U2"],
                                     [{"user": "U1"}, {"user": "U2"}])
    assert state == "covered"
    assert counts["never"] == 0


def test_nobody_served_is_reported_separately_from_a_partial_gap():
    assert publish_coverage(["U1", "U2"], [])[0] == "none-published"


def test_no_members_is_not_mistaken_for_full_coverage():
    assert publish_coverage([], [{"user": "U1"}])[0] == "no-members"


def test_staleness_is_measured_per_user_not_per_app():
    records = [{"user": "U1", "ts": NOW - 1}] + [
        {"user": "U%d" % i, "ts": NOW - 200 * DAY} for i in range(2, 6)]
    state, counts = staleness(records, now=NOW, max_age_days=30)
    assert state == "stale"
    assert counts["stale"] == 4
    assert counts["fresh"] == 1


def test_a_users_most_recent_publish_is_the_one_that_counts():
    records = [{"user": "U1", "ts": NOW - 400 * DAY}, {"user": "U1", "ts": NOW - 1}]
    state, counts = staleness(records, now=NOW, max_age_days=30)
    assert state == "fresh"
    assert counts["users"] == 1


def test_records_without_a_usable_timestamp_are_skipped_rather_than_counted():
    assert staleness([{"user": "U1"}, {"user": "U2", "ts": "nope"}], now=NOW)[0] \\
        == "no-records"


def test_the_switch_outranks_everything_else_in_the_verdict():
    verdict, detail = home_verdict(["home-tab-off"], "on-open", "covered")
    assert verdict == "tab-off"
    assert "before reading the coverage" in detail


def test_a_missing_subscription_outranks_the_publish_log():
    assert home_verdict(["no-app-home-opened-subscription"], "on-open",
                        "covered")[0] == "no-subscription"


def test_publishing_once_is_named_even_when_every_switch_is_correct():
    verdict, detail = home_verdict([], "startup-only", "partial")
    assert verdict == "publish-once"
    assert "last restart" in detail


def test_correct_config_and_poor_coverage_hands_the_problem_back():
    verdict, detail = home_verdict([], "on-open", "partial")
    assert verdict == "under-published"
    assert "never had a view stored" in detail


def test_without_a_manifest_the_verdict_says_what_it_rests_on():
    verdict, detail = home_verdict(["no-manifest"], "on-open", "covered")
    assert verdict == "coverage-only"
    assert "publish log" in detail


def test_a_working_surface_is_consistent():
    assert home_verdict([], "on-open", "covered")[0] == "consistent"


def test_the_repair_is_printed_as_manifest_keys_and_pointers_are_skipped():
    assert repair_manifest(["home-tab-off", "messages-tab-only"]) == [
        "features.app_home.home_tab_enabled: true"]
    assert repair_manifest(["no-manifest"]) == []
''',
"test_js_file": "slack-home-tab.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  homeTabFindings, homeVerdict, publishCadence, publishCoverage, repairManifest,
  staleness,
} from './slack-home-tab.mjs';

const NOW = 1800000000;
const DAY = 86400;

const manifest = (home = true, messages = false, events = ['app_home_opened']) => ({
  manifest: {
    features: { app_home: { home_tab_enabled: home, messages_tab_enabled: messages } },
    settings: { event_subscriptions: { bot_events: events } },
  },
});

const codesOf = (found) => found.map(([c]) => c);
const detailOf = (found, code) => Object.fromEntries(found)[code];

test('a correct manifest produces no findings at all', () => {
  assert.deepEqual(homeTabFindings(manifest()), []);
});

test('the home tab switch is reported with the reason there is no error', () => {
  const found = homeTabFindings(manifest(false));
  assert.equal(codesOf(found).includes('home-tab-off'), true);
  assert.match(detailOf(found, 'home-tab-off'), /ok true/);
});

test('a missing subscription is its own finding on an enabled tab', () => {
  assert.deepEqual(codesOf(homeTabFindings(manifest(true, false, []))),
    ['no-app-home-opened-subscription']);
});

test('both settings wrong are both reported rather than the first one', () => {
  const found = codesOf(homeTabFindings(manifest(false, false, [])));
  assert.equal(found.includes('home-tab-off'), true);
  assert.equal(found.includes('no-app-home-opened-subscription'), true);
});

test('a messages tab without a home tab points at the other note', () => {
  const found = homeTabFindings(manifest(false, true));
  assert.equal(codesOf(found).includes('messages-tab-only'), true);
  assert.match(detailOf(found, 'messages-tab-only'), /different switches/);
});

test('no manifest says what is still readable without one', () => {
  const found = homeTabFindings({});
  assert.deepEqual(codesOf(found), ['no-manifest']);
  assert.match(detailOf(found, 'no-manifest'), /configuration token/);
});

test('publishing on open is the correct cadence', () => {
  const [state, counts] = publishCadence([{ user: 'U1', trigger: 'app_home_opened' },
    { user: 'U2', trigger: 'app_home_opened' }]);
  assert.equal(state, 'on-open');
  assert.equal(counts.on_open, 2);
});

test('publishing at boot only is the shape that works for the developer', () => {
  const [state, counts] = publishCadence([{ user: 'U1', trigger: 'startup' },
    { user: 'U2', trigger: 'deploy' }]);
  assert.equal(state, 'startup-only');
  assert.equal(counts.startup, 2);
});

test('a migration in progress reads as mixed', () => {
  assert.equal(publishCadence([{ user: 'U1', trigger: 'startup' },
    { user: 'U2', trigger: 'app_home_opened' }])[0], 'mixed');
});

test('an unrecognised trigger is named rather than counted as correct', () => {
  const [state, counts] = publishCadence([{ user: 'U1', trigger: 'manual' }]);
  assert.equal(state, 'unknown-trigger');
  assert.equal(counts.other, 1);
});

test('an empty publish log is no records', () => {
  assert.equal(publishCadence([])[0], 'no-records');
});

test('coverage is a set difference not a count of publishes', () => {
  const records = Array.from({ length: 40000 }, () => ({ user: 'U1' }));
  const [state, counts] = publishCoverage(['U1', 'U2', 'U3'], records);
  assert.equal(state, 'partial');
  assert.equal(counts.never, 2);
  assert.equal(counts.covered, 1);
});

test('everybody served is covered', () => {
  const [state, counts] = publishCoverage(['U1', 'U2'],
    [{ user: 'U1' }, { user: 'U2' }]);
  assert.equal(state, 'covered');
  assert.equal(counts.never, 0);
});

test('nobody served is reported separately from a partial gap', () => {
  assert.equal(publishCoverage(['U1', 'U2'], [])[0], 'none-published');
});

test('no members is not mistaken for full coverage', () => {
  assert.equal(publishCoverage([], [{ user: 'U1' }])[0], 'no-members');
});

test('staleness is measured per user not per app', () => {
  const records = [{ user: 'U1', ts: NOW - 1 }];
  for (let i = 2; i < 6; i += 1) records.push({ user: `U${i}`, ts: NOW - 200 * DAY });
  const [state, counts] = staleness(records, NOW, 30);
  assert.equal(state, 'stale');
  assert.equal(counts.stale, 4);
  assert.equal(counts.fresh, 1);
});

test('a users most recent publish is the one that counts', () => {
  const [state, counts] = staleness([{ user: 'U1', ts: NOW - 400 * DAY },
    { user: 'U1', ts: NOW - 1 }], NOW, 30);
  assert.equal(state, 'fresh');
  assert.equal(counts.users, 1);
});

test('records without a usable timestamp are skipped rather than counted', () => {
  assert.equal(staleness([{ user: 'U1' }, { user: 'U2', ts: 'nope' }], NOW)[0],
    'no-records');
});

test('the switch outranks everything else in the verdict', () => {
  const [verdict, detail] = homeVerdict(['home-tab-off'], 'on-open', 'covered');
  assert.equal(verdict, 'tab-off');
  assert.match(detail, /before reading the coverage/);
});

test('a missing subscription outranks the publish log', () => {
  assert.equal(homeVerdict(['no-app-home-opened-subscription'], 'on-open',
    'covered')[0], 'no-subscription');
});

test('publishing once is named even when every switch is correct', () => {
  const [verdict, detail] = homeVerdict([], 'startup-only', 'partial');
  assert.equal(verdict, 'publish-once');
  assert.match(detail, /last restart/);
});

test('correct config and poor coverage hands the problem back', () => {
  const [verdict, detail] = homeVerdict([], 'on-open', 'partial');
  assert.equal(verdict, 'under-published');
  assert.match(detail, /never had a view stored/);
});

test('without a manifest the verdict says what it rests on', () => {
  const [verdict, detail] = homeVerdict(['no-manifest'], 'on-open', 'covered');
  assert.equal(verdict, 'coverage-only');
  assert.match(detail, /publish log/);
});

test('a working surface is consistent', () => {
  assert.equal(homeVerdict([], 'on-open', 'covered')[0], 'consistent');
});

test('the repair is printed as manifest keys and pointers are skipped', () => {
  assert.deepEqual(repairManifest(['home-tab-off', 'messages-tab-only']),
    ['features.app_home.home_tab_enabled: true']);
  assert.deepEqual(repairManifest(['no-manifest']), []);
});
''',
"faq": [
 ("How is this different from the Messages tab being disabled?",
  "Different switch, different surface, different symptom. The Messages tab governs whether a person may type at your app, it lives at features.app_home.messages_tab_enabled, and calling into a DM with it off produces a real error string, messages_tab_disabled, that your code can catch. The Home tab governs whether a view you published is reachable, it lives at features.app_home.home_tab_enabled, and publishing to it with the switch off produces ok: true and a view id. One refuses you on the way in; the other accepts everything and renders nothing. They sit next to each other in the same settings panel, which is why the script prints a pointer when it finds the Home tab off and the Messages tab on."),
 ("views.publish returns ok: true and a view object. How can that not mean it worked?",
  "Because the method did exactly what it says: it stored a view for a user. Whether there is a tab through which that user can reach it is a separate question about app configuration, and views.publish is not the thing that answers it. This is the general shape of Slack failures pushed to its limit, and it is worth internalising: a successful response tells you the call was accepted, never that the outcome you had in mind occurred."),
 ("Why does the script need my own publish log? Cannot it just ask Slack who has a view?",
  "There is no such method. Slack offers no read that enumerates the users with a published view for your app, so the per-user history exists in exactly one place, which is your side of the conversation. The alternative would be to publish a view in order to observe it, and that is a write: it would change what those users see in order to find out what they see. The log is a list of records carrying a user, a trigger and a timestamp, which most apps are already emitting."),
 ("Everything is configured correctly and most of the workspace still has an empty tab. What now?",
  "That is the under-published verdict, and it means the fault is in your handler rather than in a setting. The usual cause is publishing at startup for the users the process happened to know about, which serves the people who were already there and nobody who arrived afterwards. Move the publish into the app_home_opened handler and publish for event.user on every open. Coverage then fixes itself as people open the app, and staleness stops being possible at all, because every view is written at the moment it is looked at."),
 ("Do I have to publish the Home tab again after a reinstall?",
  "Yes, and this is the part that surprises people. The view is stored per user and per installation, so a reinstall gives you a new installation with no published views at all, and every user is back to the empty state until something publishes for them again. An app that publishes on app_home_opened does not notice, because the first open after the reinstall does the work. An app that publishes at startup notices only when somebody complains."),
],
"related": [
 ("/slack/messages-tab-disabled/", "the other App Home tab, and why it fails loudly"),
 ("/slack/no-event-subscriptions/", "a subscription list with nothing routed down it"),
 ("/slack/config-token-expired/", "the credential this check reads the manifest with"),
],
"citations": [CITE_APP_HOME, CITE_VIEWS_PUBLISH, CITE_APP_HOME_OPENED,
              CITE_MANIFEST_REF],
})
GUIDES.append({
"slug": "app-uninstalled-orphan-install-record",
"title": "The install store keeps rows for uninstalled workspaces",
"description": "The finding is a row in your database, not an error from Slack. Sweep the store with auth.test, size the dead fraction, and watch whether it grows.",
"h1": "The install store keeps rows for uninstalled workspaces",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack app_uninstalled delete installation",
             "bolt installation store not deleted",
             "slack tokens_revoked handler",
             "slack token_revoked every run scheduled job",
             "slack multi workspace dead tenants"],
"deps": "Python 3.9+ with requests, or Node.js 18+; your installation store exported as JSON, and read access to each stored token so auth.test can be called once per row",
"lead": "The nightly digest job iterates four hundred installations and logs a hundred and twenty errors. It has done that every night for eleven months. Nobody looks at the log any more, because the log is a hundred and twenty lines of <code>token_revoked</code> followed by the two lines that actually matter, and after the fourth week of that you stop scrolling.</p><p>Slack is not doing anything wrong here. Every one of those hundred and twenty workspaces removed your app, and Slack told you so at the time: it emitted <code>app_uninstalled</code>, it emitted <code>tokens_revoked</code>, and it invalidated the token immediately. What it did not do &mdash; what nothing does &mdash; is delete the row in your database. That was always your job, and the failure is sitting in your own table.",
"short_answer": """<p>Deleting the installation record is the app's responsibility, and the SDK installation stores do not do it for you. Handle <code>app_uninstalled</code> and <code>tokens_revoked</code> by removing the row and everything derived from it; without that, an install that ended two years ago is still iterated on every sweep, still consuming a request, and still writing an error line.</p>
<p>The measurement is a <strong>population</strong>, not an error. Walk the store, call <code>auth.test</code> once per token, and sort the answers into live, revoked, deactivated, expired and unreadable. What you want out of it is one number: the fraction of the store that is dead. That fraction is the finding, and it is the thing no single error message can tell you, because every individual error looks like ordinary bad luck.</p>
<p>The second number is the one that turns a fact into a diagnosis. Run the sweep twice, a fortnight apart, and compare. A dead fraction that <strong>shrinks</strong> means your cleanup works. A dead fraction that holds steady or grows means nothing is deleting anything, and every uninstall from here on is permanent sediment. Keep <code>token_expired</code> out of that count: rotation lapsing is recoverable by refreshing, and tombstoning it throws away a live customer.</p>""",
"problem": """<p>The reason this survives for years is that it is not an outage. Nothing is down. The app works perfectly for every workspace that still has it installed, and the errors are all attached to workspaces that do not exist as customers any more. There is no user to complain, no dashboard to go red, and no page to receive. It is a slow accumulation of things that are true and useless, and slow accumulations do not get tickets.</p>
<p>What it does instead is ruin your instrumentation. When a hundred and twenty of every four hundred iterations fail by design, the error rate for the job is thirty percent and always has been, so nobody can use the error rate for anything. A real failure &mdash; a genuine token problem in a paying tenant &mdash; arrives as one more line in a wall of identical lines, and the alerting threshold that would have caught it was raised months ago precisely because of the noise. The dead rows do not merely waste effort; they hide the failures that matter.</p>
<p>The events that should have prevented this are real, and apps that handle them still end up here. <code>app_uninstalled</code> and <code>tokens_revoked</code> arrive in an order that is not guaranteed, so a handler written to expect one before the other drops the second. <code>tokens_revoked</code> does not fire for every case &mdash; a single user revoking their own authorization is not the same as the app being removed &mdash; so a store keyed on user tokens keeps rows the event never mentioned. And an app that was deployed before the handler was written has a backlog that no future event will ever clear, because the events for those installs were emitted and discarded years ago.</p>
<p>Then there is the residue, which is the part people forget entirely. The installation row is not the only thing that referenced that workspace. There are scheduled messages queued against channels in it, cached channel and user ids, incoming webhook URLs, per-tenant cron entries, a row in a billing table. Deleting the token and leaving the rest produces a second generation of orphans that fail in less obvious ways: a scheduled message that will never send, a cron entry that wakes every hour to do nothing, a webhook URL that answers 404 forever.</p>""",
"why": """<p><strong>The unit of the finding is the store, not the token.</strong> A single <code>token_revoked</code> is a fact about one workspace and has its own note; it means the app was removed there, and there is nothing to diagnose. What this check produces is a proportion: how much of your table is sediment. That number cannot be reached by reading an error, only by walking every row and counting, which is why the script takes a store export rather than a log.</p>
<p><strong>Two audits beat one, and the second one is the whole argument.</strong> A dead fraction of thirty percent is a fact. A dead fraction that was twenty-nine percent a fortnight ago is a diagnosis: nothing is being cleaned up, the number only goes one way, and every future uninstall is permanent. So the script accepts a previous run's counts and reports the trend, because &ldquo;stable&rdquo; here means &ldquo;broken&rdquo; and that is not obvious.</p>
<p><strong>Recoverable and dead are different, and merging them deletes customers.</strong> <code>token_revoked</code> and <code>account_inactive</code> mean the grant is gone. <code>token_expired</code> means rotation is switched on and the refresh has lapsed, which is a live installation with a stale credential and is fixed by refreshing rather than by deletion. A sweep that tombstones on any error at all will eventually remove a paying tenant during a rotation outage, which is a considerably worse bug than the one it was written to fix.</p>
<p><strong>Rate limiting is not evidence of death, and neither is a network blip.</strong> A sweep of four hundred tokens will hit <code>ratelimited</code> somewhere in the middle, and a row that could not be read is unknown rather than dead. The classifier says so explicitly and the counts keep unknown rows in their own column, because rolling them into either side turns a transient into a permanent decision.</p>
<p><strong>Nothing prints a token, and the script does not need one to.</strong> Every row is identified by its store id and its team or enterprise id. Where the shape of a credential is genuinely useful &mdash; a store that has been quietly accumulating user tokens where bot tokens were intended &mdash; the script reports the prefix class and nothing else: <code>xoxb</code>, <code>xoxp</code>, <code>xapp</code>, or unrecognised. No value, no fragment, no length.</p>
<p><strong>The derived records are named because deleting the row alone creates a second generation.</strong> Scheduled messages, cached ids, webhook URLs and per-tenant schedules all outlive the install and all keep costing something. The script reports which of them a dead row still carries, so the cleanup you write covers them the first time rather than after a second incident.</p>""",
"steps": [
 {"h": "Export the store, tokens included, and keep the export out of your logs",
  "body": """<p>The script reads a JSON list of rows carrying at least an id, a team id and a token. It calls <code>auth.test</code> once per row and prints nothing but ids and states. Treat the export as a credential file for as long as it exists, because that is what it is.</p>"""},
 {"h": "Classify each answer into an action, not just a state",
  "body": """<p><code>classify_install</code> returns both: <code>revoked</code> and <code>inactive</code> map to <code>tombstone</code>, <code>expired</code> maps to <code>refresh</code>, <code>rate-limited</code> and <code>unreadable</code> map to <code>retry</code>, and anything unrecognised maps to <code>inspect</code> rather than to deletion. The action column is what a cleanup job would act on, and its default is deliberately to do nothing.</p>"""},
 {"h": "Size the dead fraction",
  "body": """<p><code>store_health</code> reports <code>clean</code>, <code>residue</code>, <code>dominated</code> or <code>empty</code>, with the counts behind each. Dominated means the majority of your sweep is spent on workspaces that removed the app, which is the state most multi-tenant Slack apps discover themselves to be in the first time anybody counts.</p>"""},
 {"h": "Compare against the last audit",
  "body": """<p><code>dead_trend</code> takes the previous run's counts and answers <code>growing</code>, <code>stable</code>, <code>shrinking</code> or <code>no-baseline</code>. Stable is a failure result: it means the number of dead rows is not going down, which is only possible if nothing deletes them.</p>"""},
 {"h": "Name what the dead row still points at",
  "body": """<p><code>orphan_residue</code> reads the row itself and reports the derived records that also need removing: scheduled message ids, cached channel ids, an incoming webhook URL, a per-tenant schedule. Each of those fails on its own timetable once the token is gone.</p>"""},
 {"h": "Handle both events, then reconcile anyway",
  "body": """<p>Subscribe to <code>app_uninstalled</code> and <code>tokens_revoked</code> and delete on either, idempotently, because the order is not guaranteed. Then keep this sweep as a scheduled reconciliation, because events get dropped during deploys and no event will ever arrive for the installs that ended before the handler existed.</p>"""},
],
"verify": """<p>Write the cleanup, let it run, and re-run the sweep a fortnight later with <code>--previous</code> pointing at the earlier counts. The line to read is <code>trend</code>: it should say <code>shrinking</code>.</p>
<pre><code class="language-bash">python3 slack_install_store_sweep.py --store installs.json --previous last-audit.json
# store      412 row(s)       read from installs.json
# row        inst-0031        revoked        tombstone      T04AB1  xoxb
# row        inst-0044        inactive       tombstone      T04CD2  xoxp
# row        inst-0102        expired        refresh        T04EF3  xoxb
# row        inst-0188        rate-limited   retry          T04GH4  xoxb
# health     dominated        412 row(s): 118 live, 279 dead, 12 recoverable, 3 unknown
# trend      stable           the dead share was 67.2% and is 67.7%; nothing is
#                             deleting anything
# residue    inst-0031        4 scheduled message(s), 1 webhook url, 1 channel cache
# cost       wasted           279 call(s) per sweep, 8,370 per day at 30 sweeps
# verdict    2 finding(s)
#   repair: handle app_uninstalled and tokens_revoked, delete the row idempotently on
#           either, and delete every derived record with it
#   repair: keep this sweep as a scheduled reconciliation; no event will ever arrive
#           for the installs that ended before the handler existed
#   note:   token_expired rows were left alone; that is a refresh, not a deletion</code></pre>""",
"code_intro": "Everything that decides anything is pure and takes a parsed response or a row, so the whole classifier can be tested without a token. <code>classify_install</code> returns a state and an action, and its default action is to do nothing, because a sweep that guesses wrong deletes a customer. <code>store_health</code> turns the states into the one number worth having. <code>dead_trend</code> is the function that makes the number mean something, and it treats a flat line as a failure. <code>orphan_residue</code> reads what else the row points at, and <code>token_shape</code> reports a prefix class so that nothing anywhere prints a credential.",
"py_file": "slack_install_store_sweep.py",
"py": '''"""Find the installations in your own store that no longer exist in Slack.

Read only. One GET is made per stored row, to auth.test, which is the cheapest
method that answers "is this token still a token". Nothing is written, nothing
is deleted, and no cleanup is performed: the script counts, classifies and
prints the repair for you to run.

No token value is printed by any path in this file. Rows are identified by
their store id and their team or enterprise id, and where the shape of a
credential matters the prefix class is reported and nothing else.

The finding here is not an error from Slack. It is a proportion of your own
table, which is why the script takes a store export rather than a log, and why
it accepts the previous audit's counts: a dead fraction that holds steady
between two audits is the proof that nothing is cleaning up.
"""
import argparse
import json
import logging
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_install_store_sweep")

API = "https://slack.com/api/"

# The grant is gone and the row is sediment.
DEAD = ("revoked", "inactive")
# The installation is alive and the credential is stale. Deleting one of these
# during a rotation outage removes a paying customer, which is a considerably
# worse bug than the one this script exists to find.
RECOVERABLE = ("expired",)
# Nothing was learned about this row. Not dead, not alive, counted separately.
UNKNOWN = ("rate-limited", "unreadable", "unrecognised")

# Errors that mean the grant itself has ended.
REVOKED_ERRORS = ("token_revoked", "invalid_auth", "not_authed")
INACTIVE_ERRORS = ("account_inactive", "team_disabled", "user_removed_from_team")
EXPIRED_ERRORS = ("token_expired",)
TRANSIENT_ERRORS = ("ratelimited", "service_unavailable", "fatal_error",
                    "request_timeout", "unparseable_body")

# Fields on a stored row that point at something outside it. Each one outlives
# the token and fails on its own timetable once the install has ended.
RESIDUE_FIELDS = (
    ("scheduled_message_ids", "scheduled message(s) queued against a workspace "
                              "that removed the app"),
    ("webhook_url", "an incoming webhook URL that will answer 404 forever"),
    ("cached_channels", "cached channel id(s) that can never be resolved again"),
    ("schedule_id", "a per-tenant schedule that wakes up and does nothing"),
)

# Where a dead fraction stops being untidy and starts being the whole sweep.
DOMINATED_SHARE = 0.5
RESIDUE_SHARE = 0.05
# Two audits will never land on the same number exactly; this is the band
# inside which "it did not change" is the honest reading.
TREND_TOLERANCE = 0.02


def token_shape(token):
    """The prefix class of a credential, and nothing else. Pure.

    Returns "xoxb", "xoxp", "xoxe", "xapp" or "unrecognised". Never returns any
    part of the value, and no caller in this file has any reason to want one.
    A store quietly accumulating user tokens where bot tokens were intended is
    worth seeing; the tokens themselves are not.
    """
    text = str(token or "")
    for prefix in ("xoxb", "xoxp", "xoxe", "xapp", "xoxa"):
        if text.startswith(prefix + "-"):
            return prefix
    return "unrecognised"


def classify_install(body):
    """Read one auth.test response as a state and an action. Pure.

    Returns (state, action). The action is the half a cleanup job would act on,
    and its default is to do nothing:

      live         ok true                          -> keep
      revoked      the grant has ended              -> tombstone
      inactive     the user or workspace is gone    -> tombstone
      expired      rotation lapsed, still a tenant  -> refresh
      rate-limited transient, nothing learned       -> retry
      unreadable   no ok field at all               -> retry
      unrecognised an error this script does not know -> inspect
    """
    doc = body or {}
    if doc.get("ok") is True:
        return ("live", "keep")
    error = str(doc.get("error") or "")
    if not error and "ok" not in doc:
        return ("unreadable", "retry")
    if error in EXPIRED_ERRORS:
        return ("expired", "refresh")
    if error in REVOKED_ERRORS:
        return ("revoked", "tombstone")
    if error in INACTIVE_ERRORS:
        return ("inactive", "tombstone")
    if error in TRANSIENT_ERRORS:
        return ("rate-limited", "retry")
    return ("unrecognised", "inspect")


def store_health(states):
    """What fraction of the store is dead? Pure.

    states: the state string from classify_install, one per row.

    Returns (state, counts). Unknown rows are kept in their own column rather
    than pushed to either side, because a rate limit in the middle of a sweep
    is not evidence of anything.
    """
    seen = [str(s) for s in (states or [])]
    counts = {"rows": len(seen), "live": 0, "dead": 0, "recoverable": 0, "unknown": 0}
    for state in seen:
        if state == "live":
            counts["live"] += 1
        elif state in DEAD:
            counts["dead"] += 1
        elif state in RECOVERABLE:
            counts["recoverable"] += 1
        else:
            counts["unknown"] += 1
    if not seen:
        return ("empty", counts)
    share = counts["dead"] / float(len(seen))
    counts["dead_share"] = round(share, 4)
    if share >= DOMINATED_SHARE:
        return ("dominated", counts)
    if share > RESIDUE_SHARE:
        return ("residue", counts)
    if counts["dead"]:
        return ("residue", counts)
    return ("clean", counts)


def dead_trend(previous, current):
    """Compare this audit's dead share against the last one. Pure.

    Returns (state, detail). Stable is a failure result and the detail says so:
    a dead fraction that does not fall is only possible if nothing is deleting
    anything, and every uninstall from here on is permanent.
    """
    def share(counts):
        rows = float((counts or {}).get("rows") or 0)
        if not rows:
            return None
        return float((counts or {}).get("dead") or 0) / rows

    was, now = share(previous), share(current)
    if now is None:
        return ("no-data", "this audit read no rows, so there is nothing to compare")
    if was is None:
        return ("no-baseline", "no previous audit was given; run this again in a "
                               "fortnight and compare, because the trend is the "
                               "finding rather than the number")
    delta = now - was
    detail = "the dead share was %.1f%% and is %.1f%%" % (was * 100, now * 100)
    if delta > TREND_TOLERANCE:
        return ("growing", detail + "; the store is accumulating dead rows faster "
                                    "than anything removes them")
    if delta < -TREND_TOLERANCE:
        return ("shrinking", detail + "; something is cleaning up")
    return ("stable", detail + "; nothing is deleting anything")


def orphan_residue(row):
    """What else does this row still point at? Pure.

    Returns a list of (code, detail). Deleting the installation and leaving
    these behind produces a second generation of orphans that fail on their own
    timetables: a message that will never send, a webhook that answers 404, a
    schedule that wakes every hour to do nothing.
    """
    doc = row or {}
    out = []
    for field, why in RESIDUE_FIELDS:
        value = doc.get(field)
        if isinstance(value, (list, tuple, set)):
            if value:
                out.append((field, "%d %s" % (len(value), why)))
        elif value:
            out.append((field, why))
    return out


def sweep_cost(counts, sweeps_per_day=1):
    """How much of every sweep is spent on workspaces that left? Pure.

    Returns (state, numbers). The point of the number is not the money, which
    is negligible; it is that a job whose error rate is thirty percent by
    design has no usable error rate at all.
    """
    dead = int((counts or {}).get("dead") or 0)
    rows = int((counts or {}).get("rows") or 0)
    per_day = dead * max(int(sweeps_per_day or 0), 0)
    numbers = {"calls_per_sweep": dead, "calls_per_day": per_day,
               "share": round(dead / float(rows), 4) if rows else 0.0}
    return (("wasted", numbers) if dead else ("none", numbers))


def auth_test(session, token):
    """One GET, with one stored token. Returns the parsed body."""
    r = session.get(API + "auth.test",
                    headers={"Authorization": "Bearer " + token}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store", required=True,
                    help="your installation store as JSON: a list of rows carrying "
                         "at least id, team_id and token")
    ap.add_argument("--previous", default="",
                    help="the counts written by a previous run, to read the trend")
    ap.add_argument("--sweeps-per-day", type=int, default=1)
    args = ap.parse_args()

    with open(args.store, encoding="utf-8") as handle:
        rows = json.load(handle) or []
    log.info("store      %d row(s)       read from %s", len(rows), args.store)

    session = requests.Session()
    states = []
    dead_rows = []
    for row in rows:
        row = row or {}
        token = row.get("token") or ""
        state, action = classify_install(auth_test(session, token) if token
                                         else {"ok": False, "error": "not_authed"})
        states.append(state)
        level = log.info if state == "live" else log.warning
        level("row        %-16s %-14s %-14s %-7s %s", row.get("id"), state, action,
              row.get("team_id") or row.get("enterprise_id") or "-",
              token_shape(token))
        if state in DEAD:
            dead_rows.append(row)

    health, counts = store_health(states)
    (log.info if health == "clean" else log.warning)(
        "health     %-14s %s", health, counts)

    previous = {}
    if args.previous:
        with open(args.previous, encoding="utf-8") as handle:
            previous = json.load(handle) or {}
    trend, detail = dead_trend(previous, counts)
    (log.info if trend == "shrinking" else log.warning)(
        "trend      %-14s %s", trend, detail)

    for row in dead_rows:
        residue = orphan_residue(row)
        if residue:
            log.warning("residue    %-16s %s", row.get("id"),
                        "; ".join(d for _c, d in residue))

    cost, numbers = sweep_cost(counts, args.sweeps_per_day)
    (log.info if cost == "none" else log.warning)("cost       %-14s %s", cost, numbers)

    findings = (1 if health != "clean" else 0) + (1 if trend in ("stable", "growing")
                                                  else 0)
    if not findings:
        log.info("verdict    clean          the store holds no dead rows")
        return 0
    log.warning("verdict    %d finding(s)", findings)
    log.warning("  repair: handle app_uninstalled and tokens_revoked, delete the row "
                "idempotently on either, and delete every derived record with it")
    log.warning("  repair: keep this sweep as a scheduled reconciliation; no event "
                "will ever arrive for the installs that ended before the handler "
                "existed")
    log.warning("  note:   token_expired rows were left alone; that is a refresh, "
                "not a deletion")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-install-store-sweep.mjs",
"js": '''/**
 * Find the installations in your own store that no longer exist in Slack.
 *
 * Read only. One GET is made per stored row, to auth.test. Nothing is written,
 * nothing is deleted, and no cleanup is performed: the script counts,
 * classifies and prints the repair for you to run.
 *
 * No token value is printed by any path in this file. Rows are identified by
 * their store id and their team or enterprise id, and where the shape of a
 * credential matters the prefix class is reported and nothing else.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// The grant is gone and the row is sediment.
export const DEAD = ['revoked', 'inactive'];
// Alive, with a stale credential. Deleting one of these removes a customer.
export const RECOVERABLE = ['expired'];

export const REVOKED_ERRORS = ['token_revoked', 'invalid_auth', 'not_authed'];
export const INACTIVE_ERRORS = ['account_inactive', 'team_disabled',
  'user_removed_from_team'];
export const EXPIRED_ERRORS = ['token_expired'];
export const TRANSIENT_ERRORS = ['ratelimited', 'service_unavailable', 'fatal_error',
  'request_timeout', 'unparseable_body'];

// Fields on a stored row that point at something outside it.
export const RESIDUE_FIELDS = [
  ['scheduled_message_ids', 'scheduled message(s) queued against a workspace that '
    + 'removed the app'],
  ['webhook_url', 'an incoming webhook URL that will answer 404 forever'],
  ['cached_channels', 'cached channel id(s) that can never be resolved again'],
  ['schedule_id', 'a per-tenant schedule that wakes up and does nothing'],
];

const DOMINATED_SHARE = 0.5;
const RESIDUE_SHARE = 0.05;
const TREND_TOLERANCE = 0.02;

/** The prefix class of a credential, and nothing else. Pure. */
export function tokenShape(token) {
  const text = String(token ?? '');
  for (const prefix of ['xoxb', 'xoxp', 'xoxe', 'xapp', 'xoxa']) {
    if (text.startsWith(`${prefix}-`)) return prefix;
  }
  return 'unrecognised';
}

/**
 * Read one auth.test response as a state and an action. Pure.
 * Returns [state, action]; the default action is to do nothing.
 */
export function classifyInstall(body) {
  const doc = body ?? {};
  if (doc.ok === true) return ['live', 'keep'];
  const error = String(doc.error ?? '');
  if (!error && !('ok' in doc)) return ['unreadable', 'retry'];
  if (EXPIRED_ERRORS.includes(error)) return ['expired', 'refresh'];
  if (REVOKED_ERRORS.includes(error)) return ['revoked', 'tombstone'];
  if (INACTIVE_ERRORS.includes(error)) return ['inactive', 'tombstone'];
  if (TRANSIENT_ERRORS.includes(error)) return ['rate-limited', 'retry'];
  return ['unrecognised', 'inspect'];
}

/**
 * What fraction of the store is dead? Pure.
 * Returns [state, counts]; empty, clean, residue, dominated.
 */
export function storeHealth(states) {
  const seen = (states ?? []).map((s) => String(s));
  const counts = { rows: seen.length, live: 0, dead: 0, recoverable: 0, unknown: 0 };
  for (const state of seen) {
    if (state === 'live') counts.live += 1;
    else if (DEAD.includes(state)) counts.dead += 1;
    else if (RECOVERABLE.includes(state)) counts.recoverable += 1;
    else counts.unknown += 1;
  }
  if (!seen.length) return ['empty', counts];
  const share = counts.dead / seen.length;
  counts.dead_share = Math.round(share * 10000) / 10000;
  if (share >= DOMINATED_SHARE) return ['dominated', counts];
  if (share > RESIDUE_SHARE) return ['residue', counts];
  if (counts.dead) return ['residue', counts];
  return ['clean', counts];
}

/**
 * Compare this audit's dead share against the last one. Pure.
 * Stable is a failure result and the detail says so.
 */
export function deadTrend(previous, current) {
  const share = (counts) => {
    const rows = Number((counts ?? {}).rows ?? 0);
    if (!rows) return null;
    return Number((counts ?? {}).dead ?? 0) / rows;
  };
  const was = share(previous);
  const now = share(current);
  if (now === null) {
    return ['no-data', 'this audit read no rows, so there is nothing to compare'];
  }
  if (was === null) {
    return ['no-baseline', 'no previous audit was given; run this again in a '
      + 'fortnight and compare, because the trend is the finding rather than the '
      + 'number'];
  }
  const delta = now - was;
  const detail = `the dead share was ${(was * 100).toFixed(1)}% and is `
    + `${(now * 100).toFixed(1)}%`;
  if (delta > TREND_TOLERANCE) {
    return ['growing', `${detail}; the store is accumulating dead rows faster than `
      + 'anything removes them'];
  }
  if (delta < -TREND_TOLERANCE) return ['shrinking', `${detail}; something is cleaning up`];
  return ['stable', `${detail}; nothing is deleting anything`];
}

/** What else does this row still point at? Pure. */
export function orphanResidue(row) {
  const doc = row ?? {};
  const out = [];
  for (const [field, why] of RESIDUE_FIELDS) {
    const value = doc[field];
    if (Array.isArray(value)) {
      if (value.length) out.push([field, `${value.length} ${why}`]);
    } else if (value) {
      out.push([field, why]);
    }
  }
  return out;
}

/** How much of every sweep is spent on workspaces that left? Pure. */
export function sweepCost(counts, sweepsPerDay = 1) {
  const dead = Number((counts ?? {}).dead ?? 0);
  const rows = Number((counts ?? {}).rows ?? 0);
  const perDay = dead * Math.max(Number(sweepsPerDay ?? 0), 0);
  const numbers = {
    calls_per_sweep: dead,
    calls_per_day: perDay,
    share: rows ? Math.round((dead / rows) * 10000) / 10000 : 0,
  };
  return [dead ? 'wasted' : 'none', numbers];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function authTest(token) {
  const r = await fetch(`${API}auth.test`,
    { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const storePath = arg(args, '--store');
  if (!storePath) {
    console.error('pass --store with your installation store as JSON');
    process.exitCode = 2;
    return;
  }
  const rows = JSON.parse(await readFile(storePath, 'utf8')) ?? [];
  console.log(`store      ${rows.length} row(s)       read from ${storePath}`);

  const states = [];
  const deadRows = [];
  for (const raw of rows) {
    const row = raw ?? {};
    const token = row.token ?? '';
    // eslint-disable-next-line no-await-in-loop
    const body = token ? await authTest(token) : { ok: false, error: 'not_authed' };
    const [state, action] = classifyInstall(body);
    states.push(state);
    const id = String(row.id ?? '').padEnd(16);
    const team = row.team_id ?? row.enterprise_id ?? '-';
    const line = `row        ${id} ${state.padEnd(14)} ${action.padEnd(14)} `
      + `${String(team).padEnd(7)} ${tokenShape(token)}`;
    if (state === 'live') console.log(line);
    else console.warn(line);
    if (DEAD.includes(state)) deadRows.push(row);
  }

  const [health, counts] = storeHealth(states);
  const healthLine = `health     ${health.padEnd(14)} ${JSON.stringify(counts)}`;
  if (health === 'clean') console.log(healthLine);
  else console.warn(healthLine);

  let previous = {};
  const previousPath = arg(args, '--previous');
  if (previousPath) previous = JSON.parse(await readFile(previousPath, 'utf8')) ?? {};
  const [trend, detail] = deadTrend(previous, counts);
  const trendLine = `trend      ${trend.padEnd(14)} ${detail}`;
  if (trend === 'shrinking') console.log(trendLine);
  else console.warn(trendLine);

  for (const row of deadRows) {
    const residue = orphanResidue(row);
    if (residue.length) {
      console.warn(`residue    ${String(row.id ?? '').padEnd(16)} `
        + `${residue.map(([, d]) => d).join('; ')}`);
    }
  }

  const [cost, numbers] = sweepCost(counts, Number(arg(args, '--sweeps-per-day', '1')));
  const costLine = `cost       ${cost.padEnd(14)} ${JSON.stringify(numbers)}`;
  if (cost === 'none') console.log(costLine);
  else console.warn(costLine);

  const findings = (health === 'clean' ? 0 : 1)
    + (trend === 'stable' || trend === 'growing' ? 1 : 0);
  if (!findings) {
    console.log('verdict    clean          the store holds no dead rows');
    return;
  }
  console.warn(`verdict    ${findings} finding(s)`);
  console.warn('  repair: handle app_uninstalled and tokens_revoked, delete the row '
    + 'idempotently on either, and delete every derived record with it');
  console.warn('  repair: keep this sweep as a scheduled reconciliation; no event '
    + 'will ever arrive for the installs that ended before the handler existed');
  console.warn('  note:   token_expired rows were left alone; that is a refresh, not '
    + 'a deletion');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixture tokens are obviously fake and deliberately short, because nothing in these tests needs a credential and a realistic-looking one in a repository is a liability with no upside. The assertions that carry the argument are the two conservative ones: <code>token_expired</code> must map to <code>refresh</code> rather than to <code>tombstone</code>, and an error the classifier has never seen must map to <code>inspect</code>, so that a cleanup written against this never removes a live tenant it did not understand. After that it is the trend, where a flat line has to read as a failure rather than as stability.",
"test_py_file": "test_slack_install_store_sweep.py",
"test_py": '''from slack_install_store_sweep import (
    classify_install, dead_trend, orphan_residue, store_health, sweep_cost,
    token_shape,
)

BOT = "xoxb-fake-1"
USER = "xoxp-fake-2"


def test_a_healthy_row_is_kept_and_says_so():
    assert classify_install({"ok": True, "team_id": "T1"}) == ("live", "keep")


def test_a_revoked_grant_is_the_one_state_that_earns_a_tombstone():
    assert classify_install({"ok": False, "error": "token_revoked"}) \\
        == ("revoked", "tombstone")


def test_a_deactivated_account_is_dead_but_reported_separately():
    state, action = classify_install({"ok": False, "error": "account_inactive"})
    assert state == "inactive"
    assert action == "tombstone"


def test_an_expired_token_is_refreshed_and_never_deleted():
    assert classify_install({"ok": False, "error": "token_expired"}) \\
        == ("expired", "refresh")


def test_a_rate_limit_in_the_middle_of_a_sweep_is_not_evidence_of_death():
    assert classify_install({"ok": False, "error": "ratelimited"}) \\
        == ("rate-limited", "retry")


def test_an_unreadable_body_is_retried_rather_than_judged():
    assert classify_install({}) == ("unreadable", "retry")


def test_an_error_the_classifier_has_never_seen_is_inspected_not_deleted():
    state, action = classify_install({"ok": False, "error": "something_new"})
    assert state == "unrecognised"
    assert action == "inspect"


def test_the_token_shape_is_a_prefix_class_and_nothing_else():
    assert token_shape(BOT) == "xoxb"
    assert token_shape(USER) == "xoxp"
    assert token_shape("xapp-fake-3") == "xapp"
    assert token_shape("nope") == "unrecognised"
    assert token_shape("") == "unrecognised"


def test_no_part_of_a_token_survives_the_shape_function():
    shape = token_shape(BOT)
    assert "fake" not in shape
    assert shape not in BOT[5:]


def test_a_store_where_most_rows_are_dead_is_dominated():
    states = ["live"] + ["revoked"] * 6 + ["inactive"] * 3
    state, counts = store_health(states)
    assert state == "dominated"
    assert counts["dead"] == 9
    assert counts["dead_share"] == 0.9


def test_a_single_dead_row_is_residue_rather_than_clean():
    state, counts = store_health(["live"] * 99 + ["revoked"])
    assert state == "residue"
    assert counts["dead"] == 1


def test_recoverable_and_unknown_rows_are_kept_out_of_the_dead_count():
    _state, counts = store_health(["live", "expired", "rate-limited", "unrecognised"])
    assert counts["dead"] == 0
    assert counts["recoverable"] == 1
    assert counts["unknown"] == 2


def test_a_store_of_only_live_rows_is_clean():
    assert store_health(["live", "live"])[0] == "clean"


def test_an_empty_store_is_empty_rather_than_clean():
    assert store_health([])[0] == "empty"


def test_a_flat_dead_share_between_audits_is_a_failure_not_stability():
    state, detail = dead_trend({"rows": 400, "dead": 269},
                               {"rows": 412, "dead": 279})
    assert state == "stable"
    assert "nothing is deleting anything" in detail


def test_a_rising_dead_share_says_the_store_is_accumulating():
    state, detail = dead_trend({"rows": 100, "dead": 10},
                               {"rows": 100, "dead": 40})
    assert state == "growing"
    assert "accumulating" in detail


def test_a_falling_dead_share_is_the_only_good_answer():
    assert dead_trend({"rows": 100, "dead": 40},
                      {"rows": 100, "dead": 5})[0] == "shrinking"


def test_without_a_previous_audit_the_script_asks_for_a_second_one():
    state, detail = dead_trend({}, {"rows": 10, "dead": 4})
    assert state == "no-baseline"
    assert "fortnight" in detail


def test_an_empty_audit_cannot_be_compared_at_all():
    assert dead_trend({"rows": 10, "dead": 4}, {"rows": 0, "dead": 0})[0] == "no-data"


def test_the_residue_on_a_dead_row_is_named_field_by_field():
    row = {"id": "inst-1", "token": BOT,
           "scheduled_message_ids": ["Q1", "Q2"],
           "webhook_url": "https://hooks.example/x",
           "cached_channels": [], "schedule_id": "sched-9"}
    codes = [c for c, _d in orphan_residue(row)]
    assert codes == ["scheduled_message_ids", "webhook_url", "schedule_id"]


def test_an_empty_collection_is_not_reported_as_residue():
    assert orphan_residue({"scheduled_message_ids": [], "cached_channels": []}) == []


def test_a_row_with_nothing_derived_produces_nothing():
    assert orphan_residue({"id": "inst-2", "token": BOT}) == []


def test_the_cost_is_reported_per_sweep_and_per_day():
    state, numbers = sweep_cost({"rows": 400, "dead": 120}, sweeps_per_day=30)
    assert state == "wasted"
    assert numbers["calls_per_sweep"] == 120
    assert numbers["calls_per_day"] == 3600
    assert numbers["share"] == 0.3


def test_a_clean_store_costs_nothing():
    assert sweep_cost({"rows": 400, "dead": 0}, sweeps_per_day=30)[0] == "none"
''',
"test_js_file": "slack-install-store-sweep.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classifyInstall, deadTrend, orphanResidue, storeHealth, sweepCost, tokenShape,
} from './slack-install-store-sweep.mjs';

const BOT = 'xoxb-fake-1';
const USER = 'xoxp-fake-2';

test('a healthy row is kept and says so', () => {
  assert.deepEqual(classifyInstall({ ok: true, team_id: 'T1' }), ['live', 'keep']);
});

test('a revoked grant is the one state that earns a tombstone', () => {
  assert.deepEqual(classifyInstall({ ok: false, error: 'token_revoked' }),
    ['revoked', 'tombstone']);
});

test('a deactivated account is dead but reported separately', () => {
  const [state, action] = classifyInstall({ ok: false, error: 'account_inactive' });
  assert.equal(state, 'inactive');
  assert.equal(action, 'tombstone');
});

test('an expired token is refreshed and never deleted', () => {
  assert.deepEqual(classifyInstall({ ok: false, error: 'token_expired' }),
    ['expired', 'refresh']);
});

test('a rate limit in the middle of a sweep is not evidence of death', () => {
  assert.deepEqual(classifyInstall({ ok: false, error: 'ratelimited' }),
    ['rate-limited', 'retry']);
});

test('an unreadable body is retried rather than judged', () => {
  assert.deepEqual(classifyInstall({}), ['unreadable', 'retry']);
});

test('an error the classifier has never seen is inspected not deleted', () => {
  const [state, action] = classifyInstall({ ok: false, error: 'something_new' });
  assert.equal(state, 'unrecognised');
  assert.equal(action, 'inspect');
});

test('the token shape is a prefix class and nothing else', () => {
  assert.equal(tokenShape(BOT), 'xoxb');
  assert.equal(tokenShape(USER), 'xoxp');
  assert.equal(tokenShape('xapp-fake-3'), 'xapp');
  assert.equal(tokenShape('nope'), 'unrecognised');
  assert.equal(tokenShape(''), 'unrecognised');
});

test('no part of a token survives the shape function', () => {
  const shape = tokenShape(BOT);
  assert.equal(shape.includes('fake'), false);
  assert.equal(BOT.slice(5).includes(shape), false);
});

test('a store where most rows are dead is dominated', () => {
  const states = ['live', ...Array(6).fill('revoked'), ...Array(3).fill('inactive')];
  const [state, counts] = storeHealth(states);
  assert.equal(state, 'dominated');
  assert.equal(counts.dead, 9);
  assert.equal(counts.dead_share, 0.9);
});

test('a single dead row is residue rather than clean', () => {
  const [state, counts] = storeHealth([...Array(99).fill('live'), 'revoked']);
  assert.equal(state, 'residue');
  assert.equal(counts.dead, 1);
});

test('recoverable and unknown rows are kept out of the dead count', () => {
  const [, counts] = storeHealth(['live', 'expired', 'rate-limited', 'unrecognised']);
  assert.equal(counts.dead, 0);
  assert.equal(counts.recoverable, 1);
  assert.equal(counts.unknown, 2);
});

test('a store of only live rows is clean', () => {
  assert.equal(storeHealth(['live', 'live'])[0], 'clean');
});

test('an empty store is empty rather than clean', () => {
  assert.equal(storeHealth([])[0], 'empty');
});

test('a flat dead share between audits is a failure not stability', () => {
  const [state, detail] = deadTrend({ rows: 400, dead: 269 },
    { rows: 412, dead: 279 });
  assert.equal(state, 'stable');
  assert.match(detail, /nothing is deleting anything/);
});

test('a rising dead share says the store is accumulating', () => {
  const [state, detail] = deadTrend({ rows: 100, dead: 10 }, { rows: 100, dead: 40 });
  assert.equal(state, 'growing');
  assert.match(detail, /accumulating/);
});

test('a falling dead share is the only good answer', () => {
  assert.equal(deadTrend({ rows: 100, dead: 40 }, { rows: 100, dead: 5 })[0],
    'shrinking');
});

test('without a previous audit the script asks for a second one', () => {
  const [state, detail] = deadTrend({}, { rows: 10, dead: 4 });
  assert.equal(state, 'no-baseline');
  assert.match(detail, /fortnight/);
});

test('an empty audit cannot be compared at all', () => {
  assert.equal(deadTrend({ rows: 10, dead: 4 }, { rows: 0, dead: 0 })[0], 'no-data');
});

test('the residue on a dead row is named field by field', () => {
  const row = {
    id: 'inst-1',
    token: BOT,
    scheduled_message_ids: ['Q1', 'Q2'],
    webhook_url: 'https://hooks.example/x',
    cached_channels: [],
    schedule_id: 'sched-9',
  };
  assert.deepEqual(orphanResidue(row).map(([c]) => c),
    ['scheduled_message_ids', 'webhook_url', 'schedule_id']);
});

test('an empty collection is not reported as residue', () => {
  assert.deepEqual(orphanResidue({ scheduled_message_ids: [], cached_channels: [] }),
    []);
});

test('a row with nothing derived produces nothing', () => {
  assert.deepEqual(orphanResidue({ id: 'inst-2', token: BOT }), []);
});

test('the cost is reported per sweep and per day', () => {
  const [state, numbers] = sweepCost({ rows: 400, dead: 120 }, 30);
  assert.equal(state, 'wasted');
  assert.equal(numbers.calls_per_sweep, 120);
  assert.equal(numbers.calls_per_day, 3600);
  assert.equal(numbers.share, 0.3);
});

test('a clean store costs nothing', () => {
  assert.equal(sweepCost({ rows: 400, dead: 0 }, 30)[0], 'none');
});
''',
"faq": [
 ("Slack already sends app_uninstalled and tokens_revoked. Why do I need a sweep as well?",
  "Because events are a best effort and your store is the record. The two events arrive in an order that is not guaranteed, so a handler written to expect one before the other drops the second. tokens_revoked does not fire for every case, so a store holding user tokens keeps rows the event never mentioned. Events are missed during deploys and restarts. And most decisively, no event will ever arrive for the installs that ended before you wrote the handler, so an app that adds one today still has years of sediment that only a reconciliation pass will find."),
 ("Is this not just token_revoked with extra steps?",
  "No, and the difference is the unit. token_revoked is a fact about one workspace: the app was removed there, and there is nothing further to work out. This note is about the population. What fraction of your table is dead, is that fraction going up or down between audits, and what else does each dead row still point at. None of that can be read from an error message, because every individual error looks exactly like ordinary bad luck; it only appears when you count."),
 ("Why does the sweep refuse to treat token_expired as dead?",
  "Because it is not. token_expired means token rotation is switched on and the refresh has lapsed, which is a live installation with a stale credential, and the repair is to redeem the refresh token rather than to delete the customer. A cleanup that tombstones on any error at all will eventually run during a rotation outage and remove paying tenants in bulk, which is a far worse bug than the one it was written to fix. The classifier keeps expired in its own column with the action refresh, and the same caution applies to rate limits and unreadable responses."),
 ("What counts as a derived record, and why does deleting the token not cover it?",
  "Anything your app created that only makes sense while that installation exists. Scheduled messages queued against channels in that workspace, cached channel and user ids, an incoming webhook URL, a per-tenant cron entry, a row in a billing table. The token is only the credential; these are the work. Delete the token alone and you get a second generation of orphans that fail on their own timetables, most of them silently, and each one eventually produces its own confusing incident."),
 ("The sweep says my store is dominated. Is there anything to do besides delete?",
  "Tombstone rather than hard delete, at least at first. Keep the row with a state and a timestamp so that a reinstall from the same workspace can be recognised and so that you can prove what happened when somebody asks why a tenant vanished from a report. Then exclude tombstoned rows from every sweep, which is where the actual saving is, and keep the reconciliation on a schedule so the number keeps falling. The measurement to watch afterwards is the trend, not the total."),
],
"related": [
 ("/slack/token-revoked/", "the single dead token, and what it means on its own"),
 ("/slack/account-inactive/", "the other way a stored credential stops working"),
 ("/slack/scheduled-messages-orphaned/", "one kind of derived record the row leaves behind"),
],
"citations": [CITE_TOKENS_REVOKED, CITE_AUTH_TEST, CITE_BOLT_1203, CITE_BOLT_673],
})
GUIDES.append({
"slug": "workspace-token-in-grid",
"title": "team_access_not_granted: the token reaches one workspace",
"description": "On Grid an install is org-wide or bound to one workspace. Read auth.test for the shape, probe each sibling, and separate a refusal from an invisibility.",
"h1": "team_access_not_granted: the token reaches one workspace",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack team_access_not_granted error",
             "slack enterprise grid org wide install",
             "is_enterprise_install auth.test",
             "slack team_id parameter org wide token",
             "slack app works in one workspace of the grid"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the token you want to test, and optionally a Grid user token with admin.teams:read to enumerate the organization's workspaces",
"lead": "The customer is one company with one contract and one invoice. Inside Slack they are forty workspaces in an Enterprise Grid organization, and your app was installed into exactly one of them, on a Tuesday, by somebody in Marketing who was trying to get a notification working.</p><p>Six weeks later the rollout starts and every call outside Marketing comes back <code>{\"ok\": false, \"error\": \"team_access_not_granted\"}</code>: <em>the token used is not granted the specific workspace access required</em>. The token is valid. The scopes are right. Nothing is expired, revoked or restricted. The token simply has a boundary, that boundary is one workspace, and nothing in your code has ever had a reason to know that boundaries exist.",
"short_answer": """<p>On Enterprise Grid an app is installed either <strong>org-wide</strong> or <strong>into a single workspace</strong>, and the two produce tokens with different reach. A workspace-scoped token can see that workspace's conversations and members and nothing else; point it at a channel id or a user id from a sibling workspace and Slack answers <code>team_access_not_granted</code>.</p>
<p><code>auth.test</code> tells you which one you are holding, in two fields read together. <code>is_enterprise_install: true</code> is an org-wide token. <code>is_enterprise_install: false</code> with a non-null <code>enterprise_id</code> is the configuration that produces this error: a workspace install sitting inside a Grid organization, which behaves exactly like a normal install right up to the moment somebody outside that workspace touches it.</p>
<p>The repair has two halves and the second one catches people out. Installing org-wide, with <code>settings.org_deploy_enabled: true</code>, mints a token that spans workspaces &mdash; and then several methods that were previously unambiguous start requiring a <code>team_id</code> parameter, because a token that can see forty workspaces has to be told which one you meant. Code that has never sent <code>team_id</code> in its life keeps working in the home workspace and returns the wrong workspace's data, or nothing at all, everywhere else.</p>""",
"problem": """<p>The first difficulty is that the failure has a shape nobody expects: it is per resource, not per call. The same token, in the same process, on the same line of code, succeeds for one channel and is refused for the next, and the only difference between them is which workspace of the customer's organization the channel lives in. That is not how tokens usually behave. A token is normally either good or not, so the natural first hypothesis is that something is intermittent, and an afternoon disappears into retry logic.</p>
<p>The second is that Grid is invisible from inside the workspace where everything works. A single-workspace install into a Grid org looks identical to an install into an ordinary standalone workspace: same token prefix, same scopes, same <code>team_id</code>, same everything. The only tell is the <code>enterprise_id</code> field sitting in the <code>auth.test</code> response, which nobody reads, because until the day this happens there has been no reason to.</p>
<p>The third is that the ambiguity is real and unfixable. A read against a channel your token cannot reach may answer <code>team_access_not_granted</code>, which is unambiguous and useful. It may equally answer <code>channel_not_found</code>, which means either that the channel does not exist or that you are not permitted to know whether it exists &mdash; and the API deliberately will not tell you which. Any check here has to report that as ambiguous rather than guessing, because guessing produces a confident answer that is wrong roughly half the time.</p>
<p>And the fourth is that the fix is somebody else's to make. Installing org-wide happens at the organization level, in an admin console you do not have access to, at a customer whose Slack administrators may be three approvals away from the person who filed the ticket. That makes the output of a diagnostic here unusually important: it is not a repair you apply, it is a sentence somebody has to be able to forward.</p>""",
"why": """<p><strong>Two fields read together, not one.</strong> <code>is_enterprise_install</code> alone does not identify the problem, because <code>false</code> is also the correct value for every ordinary workspace on the planet. <code>enterprise_id</code> alone does not either, because it is populated for org-wide installs too. It is the pair &mdash; <code>false</code> with a non-null <code>enterprise_id</code> &mdash; that names a workspace install inside a Grid org, which is the one configuration that produces this error.</p>
<p><strong>A refusal and an invisibility are different findings and the script never merges them.</strong> <code>team_access_not_granted</code> means the resource exists and you are outside its boundary. <code>channel_not_found</code> means either it does not exist or you are not allowed to know, and Slack will not say which. Reporting the second as the first turns an honest &ldquo;cannot tell&rdquo; into a confident wrong answer, and the reader has no way to notice.</p>
<p><strong>Reach is measured per workspace, because the boundary is per workspace.</strong> One refusal proves the token has a boundary; it does not tell you where the boundary is. Probing each workspace in the organization produces a map: reachable, refused, or unknown, workspace by workspace, and that map is what tells you whether you are looking at one missing install or at a token that only ever covered its home.</p>
<p><strong>The <code>team_id</code> half is checked before the org-wide install, not after.</strong> Going org-wide is the repair for the boundary and the cause of the next problem, because several methods that were unambiguous under a workspace token require disambiguation under an org-wide one. So the script reports which of the methods you named will need <code>team_id</code>, while you can still schedule that work alongside the install rather than discovering it in production the following week.</p>
<p><strong>Nothing here writes, and the probe is chosen for that reason.</strong> <code>team.info?team=T...</code> is a read that answers the reach question directly for any workspace id you can name, and it fails with exactly the error under investigation. Installing an app, deploying it org-wide, or joining a channel to test membership are all writes, and none of them is necessary to establish the answer.</p>
<p><strong>Storing the installation is a different note and is handed over.</strong> Whether your database can represent an org-wide install at all &mdash; whether it is keyed on <code>team_id</code> alone, and what happens when two workspaces in the same organization collide &mdash; is a data-modelling problem with its own failure mode and its own note. This one stops at the reach of the token in your hand.</p>""",
"steps": [
 {"h": "Read the pair of fields that identify the shape",
  "body": """<p><code>install_shape</code> takes the <code>auth.test</code> body and answers <code>org-wide</code>, <code>workspace-in-grid</code>, <code>single-workspace</code> or <code>unreadable</code>. <code>workspace-in-grid</code> is the finding: an install bounded to one workspace of an organization that has many.</p>"""},
 {"h": "Get a list of the organization's workspace ids from somewhere",
  "body": """<p>The script probes whatever you pass to <code>--teams</code>, because there is no way for it to enumerate them from a token that cannot reach them. Where you get the ids from is <code>admin.teams.list</code>, which needs <code>admin.teams:read</code> on a Grid user token, or the <code>team_id</code> field on the event payloads you are already receiving.</p>"""},
 {"h": "Probe each workspace with a read that fails in the right way",
  "body": """<p><code>team.info?team=T...</code> answers the reach question directly and writes nothing. <code>reach_verdict</code> maps the response to <code>in-reach</code>, <code>out-of-reach</code>, <code>ambiguous</code> or <code>not-assessed</code>, and it refuses to convert the third into either of the first two.</p>"""},
 {"h": "Read the map rather than the individual results",
  "body": """<p><code>reach_summary</code> answers <code>org-wide-reach</code>, <code>single-workspace-reach</code>, <code>partial</code> or <code>not-assessed</code>. Single-workspace reach across an organization of forty is the sentence to send the customer's Slack administrator, and it is considerably more persuasive than one error string.</p>"""},
 {"h": "Find out which of your calls will need team_id afterwards",
  "body": """<p><code>team_id_requirement</code> takes the methods you actually call and says which of them require <code>team_id</code> once the token is org-wide. Doing this before the install means the parameter work ships with the change rather than a week after it.</p>"""},
 {"h": "Install org-wide, or install per workspace and store one token each",
  "body": """<p><code>repair_plan</code> prints both routes, because org-wide is not always available. Where it is, the manifest key is <code>settings.org_deploy_enabled: true</code> and the install happens at the organization level. Where it is not, the answer is one install and one stored token per workspace, which is a data-modelling change rather than a configuration one.</p>"""},
],
"verify": """<p>After the org-wide install, re-run with the same workspace list. Every row should read <code>in-reach</code>, and the shape line should read <code>org-wide</code>.</p>
<pre><code class="language-bash">python3 slack_grid_token_reach.py --teams T04MKTG,T04ENG,T04SUP \\
  --methods conversations.list,users.list,chat.scheduledMessages.list
# shape      workspace-in-grid  is_enterprise_install is false and enterprise_id is
#                               E04NORTHWIND, so this install is bound to one
#                               workspace of an organization that has many
# home       T04MKTG            the workspace this token was installed into
# reach      T04MKTG            in-reach
# reach      T04ENG             out-of-reach   team_access_not_granted
# reach      T04SUP             ambiguous      channel_not_found tells you either that
#                               it does not exist or that you may not know
# summary    single-workspace-reach  1 of 3 workspace(s) reachable
# team_id    conversations.list required once the token is org-wide
# team_id    users.list         required once the token is org-wide
# team_id    chat.scheduledMessages.list  required once the token is org-wide
# verdict    2 finding(s)
#   repair: install the app at the organization level, with
#           settings.org_deploy_enabled: true in the manifest
#   repair: pass team_id explicitly on the 3 method(s) above once the token spans
#           workspaces, or they will answer for the wrong one
#   note:   1 workspace was ambiguous; channel_not_found and user_not_found cannot
#           distinguish absent from invisible</code></pre>""",
"code_intro": "Four small functions and one deliberate refusal. <code>install_shape</code> reads two fields together, because neither one identifies the configuration on its own. <code>reach_verdict</code> is where the refusal lives: <code>channel_not_found</code> is reported as <code>ambiguous</code> and never promoted to a finding, because the API genuinely will not say whether the resource is absent or merely invisible. <code>reach_summary</code> turns per-workspace results into the sentence you send an administrator, and <code>team_id_requirement</code> answers the question that only becomes urgent after the repair.",
"py_file": "slack_grid_token_reach.py",
"py": '''"""Work out how far one Slack token reaches across an Enterprise Grid org.

Read only. Two GET methods are used: auth.test to identify the install shape,
and team.info per workspace to probe reach. team.info is chosen because it is a
read that fails with exactly the error under investigation, so no write and no
install is needed to establish the answer.

One ambiguity is preserved rather than resolved. A read against a resource your
token cannot reach may answer team_access_not_granted, which is unambiguous, or
channel_not_found, which means either that the resource does not exist or that
you are not permitted to know whether it exists. Slack will not say which, so
neither does this script.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_grid_token_reach")

API = "https://slack.com/api/"

# The error that names the boundary directly.
BOUNDARY_ERROR = "team_access_not_granted"

# Errors that could mean "it is not there" or "you may not know it is there".
# The API does not distinguish them and neither does this script.
AMBIGUOUS_ERRORS = ("channel_not_found", "user_not_found", "team_not_found",
                    "not_in_channel")

# Errors about the credential rather than about reach.
UNASSESSABLE_ERRORS = ("missing_scope", "not_allowed_token_type", "invalid_auth",
                       "token_revoked", "account_inactive", "ratelimited",
                       "unparseable_body")

# Methods that take an optional team_id which becomes necessary once the token
# spans workspaces, because a token that can see forty of them has to be told
# which one you meant. This is the set the script knows about; a method outside
# it is reported as unknown rather than guessed at.
REQUIRES_TEAM_ID = ("conversations.list", "users.list", "usergroups.list",
                    "users.conversations", "emoji.list", "dnd.teamInfo",
                    "team.profile.get", "chat.scheduledMessages.list",
                    "team.billableInfo")
ACCEPTS_TEAM_ID = ("team.info", "admin.conversations.search", "admin.users.list")


def install_shape(auth):
    """Which of the three install shapes is this token? Pure.

    Takes an auth.test body. Returns (state, detail). The two fields are read
    together because neither identifies the configuration alone:
    is_enterprise_install is false for every ordinary workspace on the planet,
    and enterprise_id is populated for org-wide installs too.

      org-wide           is_enterprise_install is true; the token spans the org.
      workspace-in-grid  false, with an enterprise_id. This is the finding.
      single-workspace   no enterprise_id; Grid is not involved at all.
      unreadable         auth.test did not answer.
    """
    doc = auth or {}
    if doc.get("ok") is not True:
        return ("unreadable", "auth.test answered ok: false, error=%s"
                % (doc.get("error") or "none"))
    enterprise = doc.get("enterprise_id") or ""
    if doc.get("is_enterprise_install") is True:
        return ("org-wide", "is_enterprise_install is true, so this token spans the "
                            "workspaces of %s and several methods will need a "
                            "team_id" % (enterprise or "the organization"))
    if enterprise:
        return ("workspace-in-grid", "is_enterprise_install is false and "
                                     "enterprise_id is %s, so this install is bound "
                                     "to one workspace of an organization that has "
                                     "many" % enterprise)
    return ("single-workspace", "no enterprise_id, so this is an ordinary workspace "
                                "install and Grid is not involved")


def reach_verdict(body):
    """Can this token see the workspace the probe named? Pure.

    Returns (state, detail).

      in-reach      the read succeeded.
      out-of-reach  team_access_not_granted: the boundary, named exactly.
      ambiguous     an error that cannot distinguish absent from invisible.
      not-assessed  the call failed for a reason about the credential.
      other         anything else, handed on rather than absorbed.
    """
    doc = body or {}
    if doc.get("ok") is True:
        return ("in-reach", "the read succeeded, so this workspace is inside the "
                            "token's boundary")
    error = str(doc.get("error") or "")
    if error == BOUNDARY_ERROR:
        return ("out-of-reach", "%s: the resource exists and the token is outside "
                                "its workspace" % BOUNDARY_ERROR)
    if error in AMBIGUOUS_ERRORS:
        return ("ambiguous", "%s tells you either that it does not exist or that you "
                             "may not know; Slack does not distinguish them" % error)
    if error in UNASSESSABLE_ERRORS:
        return ("not-assessed", "%s is about the credential rather than about reach"
                % error)
    if not error:
        return ("not-assessed", "no ok field and no error, so nothing can be read "
                                "from this response")
    return ("other", "%s, which is a different problem" % error)


def reach_summary(rows, home_team=""):
    """Turn per-workspace results into one sentence. Pure.

    rows: [(team_id, state), ...]. Returns (state, counts).

      org-wide-reach          every workspace probed is reachable.
      single-workspace-reach  only the home workspace is, which is the shape this
                              note is about.
      partial                 some are and some are not.
      not-assessed            nothing conclusive came back.
      no-workspaces           nothing was probed.
    """
    seen = [(str(t), str(s)) for t, s in (rows or [])]
    counts = {"workspaces": len(seen), "in_reach": 0, "out_of_reach": 0,
              "ambiguous": 0, "not_assessed": 0}
    for _team, state in seen:
        if state == "in-reach":
            counts["in_reach"] += 1
        elif state == "out-of-reach":
            counts["out_of_reach"] += 1
        elif state == "ambiguous":
            counts["ambiguous"] += 1
        else:
            counts["not_assessed"] += 1
    if not seen:
        return ("no-workspaces", counts)
    if not counts["in_reach"] and not counts["out_of_reach"]:
        return ("not-assessed", counts)
    if not counts["out_of_reach"]:
        return ("org-wide-reach", counts)
    reachable = [t for t, s in seen if s == "in-reach"]
    if reachable and reachable == [home_team]:
        return ("single-workspace-reach", counts)
    if not counts["in_reach"]:
        return ("single-workspace-reach", counts)
    return ("partial", counts)


def team_id_requirement(method, org_wide):
    """Will this method need a team_id once the token spans workspaces? Pure.

    Returns (state, detail). Asked before the org-wide install rather than
    after it, so the parameter work ships with the change instead of a week
    later.
    """
    name = str(method or "").strip()
    known = name in REQUIRES_TEAM_ID or name in ACCEPTS_TEAM_ID
    if not known:
        return ("unknown-method", "this method is not in the list this script knows "
                                  "about; check its reference page for a team_id "
                                  "parameter before the install")
    if not org_wide:
        return ("unnecessary", "a workspace-scoped token has one workspace to answer "
                               "for, so the call is bounded whether team_id is sent "
                               "or not")
    if name in REQUIRES_TEAM_ID:
        return ("required", "required once the token is org-wide; without it the "
                            "call has forty workspaces to choose from")
    return ("optional", "accepted once the token is org-wide, and worth sending so "
                        "the call cannot answer for the wrong workspace")


def repair_plan(shape, summary, needing_team_id):
    """The two routes, printed as lines somebody can forward. Pure."""
    out = []
    if shape == "workspace-in-grid" or summary in ("single-workspace-reach", "partial"):
        out.append("install the app at the organization level, with "
                   "settings.org_deploy_enabled: true in the manifest")
        out.append("where an org-wide install is not possible, install per workspace "
                   "and store one token for each")
    if needing_team_id:
        out.append("pass team_id explicitly on the %d method(s) above once the token "
                   "spans workspaces, or they will answer for the wrong one"
                   % len(needing_team_id))
    return out


def get(session, method, params=None):
    """One GET against the Web API. Returns the parsed body."""
    r = session.get(API + method, params=params or {}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the token to test")
    ap.add_argument("--teams", default="",
                    help="comma separated workspace ids to probe, T...; collected "
                         "from event payloads if you cannot list them")
    ap.add_argument("--methods", default="",
                    help="comma separated methods your app calls, to check which "
                         "will need a team_id once the token is org-wide")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("token      missing            set %s to the token you want to "
                  "test", args.token_env)
        return 2
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    auth = get(session, "auth.test")
    shape, detail = install_shape(auth)
    (log.info if shape in ("org-wide", "single-workspace") else log.warning)(
        "shape      %-18s %s", shape, detail)
    if shape == "unreadable":
        return 2
    home = auth.get("team_id") or ""
    log.info("home       %-18s the workspace this token was installed into", home)

    rows = []
    teams = [t.strip() for t in args.teams.split(",") if t.strip()]
    for team in teams:
        state, why = reach_verdict(get(session, "team.info", {"team": team}))
        (log.info if state == "in-reach" else log.warning)(
            "reach      %-18s %-14s %s", team, state, why)
        rows.append((team, state))

    summary, counts = reach_summary(rows, home_team=home)
    (log.info if summary in ("org-wide-reach", "no-workspaces") else log.warning)(
        "summary    %-18s %d of %d workspace(s) reachable", summary,
        counts["in_reach"], counts["workspaces"])

    org_wide = shape == "org-wide"
    needing = []
    for method in [m.strip() for m in args.methods.split(",") if m.strip()]:
        state, why = team_id_requirement(method, org_wide or shape == "workspace-in-grid")
        if state in ("required", "optional"):
            needing.append(method)
        (log.info if state == "unnecessary" else log.warning)(
            "team_id    %-18s %s: %s", method, state, why)

    repairs = repair_plan(shape, summary, needing)
    findings = (1 if shape == "workspace-in-grid" else 0) + (1 if needing else 0)
    if not findings and summary != "partial":
        log.info("verdict    clean              the token reaches every workspace it "
                 "was asked about")
        return 0
    log.warning("verdict    %d finding(s)", findings)
    for line in repairs:
        log.warning("  repair: %s", line)
    if counts["ambiguous"]:
        log.warning("  note:   %d workspace(s) were ambiguous; channel_not_found and "
                    "user_not_found cannot distinguish absent from invisible",
                    counts["ambiguous"])
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-grid-token-reach.mjs",
"js": '''/**
 * Work out how far one Slack token reaches across an Enterprise Grid org.
 *
 * Read only. Two GET methods are used: auth.test to identify the install
 * shape, and team.info per workspace to probe reach. team.info is chosen
 * because it is a read that fails with exactly the error under investigation,
 * so no write and no install is needed to establish the answer.
 *
 * One ambiguity is preserved rather than resolved: channel_not_found means
 * either that the resource does not exist or that you may not know it exists,
 * and Slack will not say which.
 */

const API = 'https://slack.com/api/';

// The error that names the boundary directly.
export const BOUNDARY_ERROR = 'team_access_not_granted';

// Errors that could mean "not there" or "you may not know it is there".
export const AMBIGUOUS_ERRORS = ['channel_not_found', 'user_not_found',
  'team_not_found', 'not_in_channel'];

// Errors about the credential rather than about reach.
export const UNASSESSABLE_ERRORS = ['missing_scope', 'not_allowed_token_type',
  'invalid_auth', 'token_revoked', 'account_inactive', 'ratelimited',
  'unparseable_body'];

// Methods whose optional team_id becomes necessary once the token spans
// workspaces. A method outside these lists is reported as unknown.
export const REQUIRES_TEAM_ID = ['conversations.list', 'users.list',
  'usergroups.list', 'users.conversations', 'emoji.list', 'dnd.teamInfo',
  'team.profile.get', 'chat.scheduledMessages.list', 'team.billableInfo'];
export const ACCEPTS_TEAM_ID = ['team.info', 'admin.conversations.search',
  'admin.users.list'];

/**
 * Which of the three install shapes is this token? Pure.
 * Returns [state, detail]; org-wide, workspace-in-grid, single-workspace,
 * unreadable.
 */
export function installShape(auth) {
  const doc = auth ?? {};
  if (doc.ok !== true) {
    return ['unreadable',
      `auth.test answered ok: false, error=${doc.error ?? 'none'}`];
  }
  const enterprise = doc.enterprise_id ?? '';
  if (doc.is_enterprise_install === true) {
    return ['org-wide', 'is_enterprise_install is true, so this token spans the '
      + `workspaces of ${enterprise || 'the organization'} and several methods will `
      + 'need a team_id'];
  }
  if (enterprise) {
    return ['workspace-in-grid', 'is_enterprise_install is false and enterprise_id '
      + `is ${enterprise}, so this install is bound to one workspace of an `
      + 'organization that has many'];
  }
  return ['single-workspace', 'no enterprise_id, so this is an ordinary workspace '
    + 'install and Grid is not involved'];
}

/**
 * Can this token see the workspace the probe named? Pure.
 * Returns [state, detail]; in-reach, out-of-reach, ambiguous, not-assessed, other.
 */
export function reachVerdict(body) {
  const doc = body ?? {};
  if (doc.ok === true) {
    return ['in-reach', 'the read succeeded, so this workspace is inside the '
      + "token's boundary"];
  }
  const error = String(doc.error ?? '');
  if (error === BOUNDARY_ERROR) {
    return ['out-of-reach', `${BOUNDARY_ERROR}: the resource exists and the token is `
      + 'outside its workspace'];
  }
  if (AMBIGUOUS_ERRORS.includes(error)) {
    return ['ambiguous', `${error} tells you either that it does not exist or that `
      + 'you may not know; Slack does not distinguish them'];
  }
  if (UNASSESSABLE_ERRORS.includes(error)) {
    return ['not-assessed', `${error} is about the credential rather than about reach`];
  }
  if (!error) {
    return ['not-assessed', 'no ok field and no error, so nothing can be read from '
      + 'this response'];
  }
  return ['other', `${error}, which is a different problem`];
}

/**
 * Turn per-workspace results into one sentence. Pure.
 * Returns [state, counts].
 */
export function reachSummary(rows, homeTeam = '') {
  const seen = (rows ?? []).map(([t, s]) => [String(t), String(s)]);
  const counts = {
    workspaces: seen.length,
    in_reach: 0,
    out_of_reach: 0,
    ambiguous: 0,
    not_assessed: 0,
  };
  for (const [, state] of seen) {
    if (state === 'in-reach') counts.in_reach += 1;
    else if (state === 'out-of-reach') counts.out_of_reach += 1;
    else if (state === 'ambiguous') counts.ambiguous += 1;
    else counts.not_assessed += 1;
  }
  if (!seen.length) return ['no-workspaces', counts];
  if (!counts.in_reach && !counts.out_of_reach) return ['not-assessed', counts];
  if (!counts.out_of_reach) return ['org-wide-reach', counts];
  const reachable = seen.filter(([, s]) => s === 'in-reach').map(([t]) => t);
  if (reachable.length === 1 && reachable[0] === homeTeam) {
    return ['single-workspace-reach', counts];
  }
  if (!counts.in_reach) return ['single-workspace-reach', counts];
  return ['partial', counts];
}

/** Will this method need a team_id once the token spans workspaces? Pure. */
export function teamIdRequirement(method, orgWide) {
  const name = String(method ?? '').trim();
  const known = REQUIRES_TEAM_ID.includes(name) || ACCEPTS_TEAM_ID.includes(name);
  if (!known) {
    return ['unknown-method', 'this method is not in the list this script knows '
      + 'about; check its reference page for a team_id parameter before the install'];
  }
  if (!orgWide) {
    return ['unnecessary', 'a workspace-scoped token has one workspace to answer for, '
      + 'so the call is bounded whether team_id is sent or not'];
  }
  if (REQUIRES_TEAM_ID.includes(name)) {
    return ['required', 'required once the token is org-wide; without it the call has '
      + 'forty workspaces to choose from'];
  }
  return ['optional', 'accepted once the token is org-wide, and worth sending so the '
    + 'call cannot answer for the wrong workspace'];
}

/** The two routes, printed as lines somebody can forward. Pure. */
export function repairPlan(shape, summary, needingTeamId) {
  const out = [];
  if (shape === 'workspace-in-grid' || summary === 'single-workspace-reach'
    || summary === 'partial') {
    out.push('install the app at the organization level, with '
      + 'settings.org_deploy_enabled: true in the manifest');
    out.push('where an org-wide install is not possible, install per workspace and '
      + 'store one token for each');
  }
  if ((needingTeamId ?? []).length) {
    out.push(`pass team_id explicitly on the ${needingTeamId.length} method(s) above `
      + 'once the token spans workspaces, or they will answer for the wrong one');
  }
  return out;
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function read(token, method, params) {
  const qs = new URLSearchParams(params ?? {}).toString();
  const r = await fetch(`${API}${method}${qs ? `?${qs}` : ''}`,
    { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`token      missing            set ${tokenEnv} to the token you `
      + 'want to test');
    process.exitCode = 2;
    return;
  }

  const auth = await read(token, 'auth.test', {});
  const [shape, detail] = installShape(auth);
  const shapeLine = `shape      ${shape.padEnd(18)} ${detail}`;
  if (shape === 'org-wide' || shape === 'single-workspace') console.log(shapeLine);
  else console.warn(shapeLine);
  if (shape === 'unreadable') {
    process.exitCode = 2;
    return;
  }
  const home = auth.team_id ?? '';
  console.log(`home       ${String(home).padEnd(18)} the workspace this token was `
    + 'installed into');

  const rows = [];
  for (const team of arg(args, '--teams').split(',').map((t) => t.trim())
    .filter(Boolean)) {
    // eslint-disable-next-line no-await-in-loop
    const [state, why] = reachVerdict(await read(token, 'team.info', { team }));
    const line = `reach      ${team.padEnd(18)} ${state.padEnd(14)} ${why}`;
    if (state === 'in-reach') console.log(line);
    else console.warn(line);
    rows.push([team, state]);
  }

  const [summary, counts] = reachSummary(rows, home);
  const summaryLine = `summary    ${summary.padEnd(18)} ${counts.in_reach} of `
    + `${counts.workspaces} workspace(s) reachable`;
  if (summary === 'org-wide-reach' || summary === 'no-workspaces') {
    console.log(summaryLine);
  } else console.warn(summaryLine);

  const orgWide = shape === 'org-wide' || shape === 'workspace-in-grid';
  const needing = [];
  for (const method of arg(args, '--methods').split(',').map((m) => m.trim())
    .filter(Boolean)) {
    const [state, why] = teamIdRequirement(method, orgWide);
    if (state === 'required' || state === 'optional') needing.push(method);
    const line = `team_id    ${method.padEnd(18)} ${state}: ${why}`;
    if (state === 'unnecessary') console.log(line);
    else console.warn(line);
  }

  const findings = (shape === 'workspace-in-grid' ? 1 : 0) + (needing.length ? 1 : 0);
  if (!findings && summary !== 'partial') {
    console.log('verdict    clean              the token reaches every workspace it '
      + 'was asked about');
    return;
  }
  console.warn(`verdict    ${findings} finding(s)`);
  for (const line of repairPlan(shape, summary, needing)) {
    console.warn(`  repair: ${line}`);
  }
  if (counts.ambiguous) {
    console.warn(`  note:   ${counts.ambiguous} workspace(s) were ambiguous; `
      + 'channel_not_found and user_not_found cannot distinguish absent from '
      + 'invisible');
  }
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are <code>auth.test</code> and <code>team.info</code> bodies, which contain no secret and are worth reading on their own: the difference between an org-wide install and a workspace install inside the same organization is two fields and nothing else. The assertion that matters most is the one about restraint. <code>channel_not_found</code> has to stay <code>ambiguous</code> in every combination, because promoting it to <code>out-of-reach</code> would give the script a confident answer where the API has refused to provide one.",
"test_py_file": "test_slack_grid_token_reach.py",
"test_py": '''from slack_grid_token_reach import (
    install_shape, reach_summary, reach_verdict, repair_plan, team_id_requirement,
)

ORG = "E04NORTHWIND"
HOME = "T04MKTG"


def test_an_ordinary_workspace_install_is_not_a_grid_problem():
    state, detail = install_shape({"ok": True, "team_id": HOME})
    assert state == "single-workspace"
    assert "not involved" in detail


def test_an_org_wide_token_is_named_and_warned_about_team_id():
    state, detail = install_shape({"ok": True, "team_id": HOME,
                                   "enterprise_id": ORG,
                                   "is_enterprise_install": True})
    assert state == "org-wide"
    assert "team_id" in detail


def test_the_finding_needs_both_fields_read_together():
    state, detail = install_shape({"ok": True, "team_id": HOME,
                                   "enterprise_id": ORG,
                                   "is_enterprise_install": False})
    assert state == "workspace-in-grid"
    assert ORG in detail


def test_a_failed_auth_test_is_unreadable_rather_than_assumed():
    state, detail = install_shape({"ok": False, "error": "invalid_auth"})
    assert state == "unreadable"
    assert "invalid_auth" in detail


def test_the_boundary_error_is_the_one_unambiguous_answer():
    state, detail = reach_verdict({"ok": False, "error": "team_access_not_granted"})
    assert state == "out-of-reach"
    assert "outside its workspace" in detail


def test_a_successful_read_puts_the_workspace_inside_the_boundary():
    assert reach_verdict({"ok": True, "team": {"id": HOME}})[0] == "in-reach"


def test_not_found_is_kept_ambiguous_and_never_promoted():
    for error in ("channel_not_found", "user_not_found", "team_not_found"):
        state, detail = reach_verdict({"ok": False, "error": error})
        assert state == "ambiguous"
        assert "does not distinguish" in detail


def test_a_credential_problem_is_not_a_reach_problem():
    assert reach_verdict({"ok": False, "error": "missing_scope"})[0] == "not-assessed"
    assert reach_verdict({"ok": False, "error": "ratelimited"})[0] == "not-assessed"


def test_an_unrelated_error_is_handed_on():
    state, detail = reach_verdict({"ok": False, "error": "invalid_arguments"})
    assert state == "other"
    assert "different problem" in detail


def test_an_empty_body_is_not_assessed():
    assert reach_verdict({})[0] == "not-assessed"


def test_reaching_every_workspace_probed_is_org_wide_reach():
    state, counts = reach_summary([(HOME, "in-reach"), ("T04ENG", "in-reach")])
    assert state == "org-wide-reach"
    assert counts["in_reach"] == 2


def test_reaching_only_the_home_workspace_is_the_shape_of_this_note():
    state, counts = reach_summary(
        [(HOME, "in-reach"), ("T04ENG", "out-of-reach"), ("T04SUP", "ambiguous")],
        home_team=HOME)
    assert state == "single-workspace-reach"
    assert counts["ambiguous"] == 1


def test_reaching_some_but_not_all_is_partial():
    state, _counts = reach_summary(
        [(HOME, "in-reach"), ("T04ENG", "in-reach"), ("T04SUP", "out-of-reach")],
        home_team=HOME)
    assert state == "partial"


def test_a_sweep_of_only_ambiguous_answers_concludes_nothing():
    assert reach_summary([("T04ENG", "ambiguous"),
                          ("T04SUP", "not-assessed")])[0] == "not-assessed"


def test_probing_no_workspaces_says_so():
    assert reach_summary([])[0] == "no-workspaces"


def test_team_id_is_required_on_the_listing_methods_once_org_wide():
    state, detail = team_id_requirement("conversations.list", org_wide=True)
    assert state == "required"
    assert "org-wide" in detail


def test_team_id_is_merely_accepted_on_the_methods_that_take_it_optionally():
    assert team_id_requirement("team.info", org_wide=True)[0] == "optional"


def test_a_workspace_scoped_token_does_not_need_the_parameter_at_all():
    state, detail = team_id_requirement("users.list", org_wide=False)
    assert state == "unnecessary"
    assert "one workspace to answer for" in detail


def test_a_method_outside_the_list_is_not_guessed_at():
    state, detail = team_id_requirement("chat.postMessage", org_wide=True)
    assert state == "unknown-method"
    assert "reference page" in detail


def test_the_repair_prints_both_routes_when_the_token_is_bounded():
    lines = repair_plan("workspace-in-grid", "single-workspace-reach", [])
    assert any("org_deploy_enabled" in line for line in lines)
    assert any("per workspace" in line for line in lines)


def test_the_team_id_repair_counts_the_methods_it_applies_to():
    lines = repair_plan("org-wide", "org-wide-reach",
                        ["conversations.list", "users.list"])
    assert len(lines) == 1
    assert "2 method(s)" in lines[0]


def test_a_healthy_org_wide_token_needs_no_repair_at_all():
    assert repair_plan("org-wide", "org-wide-reach", []) == []
''',
"test_js_file": "slack-grid-token-reach.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  installShape, reachSummary, reachVerdict, repairPlan, teamIdRequirement,
} from './slack-grid-token-reach.mjs';

const ORG = 'E04NORTHWIND';
const HOME = 'T04MKTG';

test('an ordinary workspace install is not a grid problem', () => {
  const [state, detail] = installShape({ ok: true, team_id: HOME });
  assert.equal(state, 'single-workspace');
  assert.match(detail, /not involved/);
});

test('an org wide token is named and warned about team_id', () => {
  const [state, detail] = installShape({
    ok: true, team_id: HOME, enterprise_id: ORG, is_enterprise_install: true,
  });
  assert.equal(state, 'org-wide');
  assert.match(detail, /team_id/);
});

test('the finding needs both fields read together', () => {
  const [state, detail] = installShape({
    ok: true, team_id: HOME, enterprise_id: ORG, is_enterprise_install: false,
  });
  assert.equal(state, 'workspace-in-grid');
  assert.match(detail, /E04NORTHWIND/);
});

test('a failed auth test is unreadable rather than assumed', () => {
  const [state, detail] = installShape({ ok: false, error: 'invalid_auth' });
  assert.equal(state, 'unreadable');
  assert.match(detail, /invalid_auth/);
});

test('the boundary error is the one unambiguous answer', () => {
  const [state, detail] = reachVerdict({
    ok: false, error: 'team_access_not_granted',
  });
  assert.equal(state, 'out-of-reach');
  assert.match(detail, /outside its workspace/);
});

test('a successful read puts the workspace inside the boundary', () => {
  assert.equal(reachVerdict({ ok: true, team: { id: HOME } })[0], 'in-reach');
});

test('not found is kept ambiguous and never promoted', () => {
  for (const error of ['channel_not_found', 'user_not_found', 'team_not_found']) {
    const [state, detail] = reachVerdict({ ok: false, error });
    assert.equal(state, 'ambiguous');
    assert.match(detail, /does not distinguish/);
  }
});

test('a credential problem is not a reach problem', () => {
  assert.equal(reachVerdict({ ok: false, error: 'missing_scope' })[0], 'not-assessed');
  assert.equal(reachVerdict({ ok: false, error: 'ratelimited' })[0], 'not-assessed');
});

test('an unrelated error is handed on', () => {
  const [state, detail] = reachVerdict({ ok: false, error: 'invalid_arguments' });
  assert.equal(state, 'other');
  assert.match(detail, /different problem/);
});

test('an empty body is not assessed', () => {
  assert.equal(reachVerdict({})[0], 'not-assessed');
});

test('reaching every workspace probed is org wide reach', () => {
  const [state, counts] = reachSummary([[HOME, 'in-reach'], ['T04ENG', 'in-reach']]);
  assert.equal(state, 'org-wide-reach');
  assert.equal(counts.in_reach, 2);
});

test('reaching only the home workspace is the shape of this note', () => {
  const [state, counts] = reachSummary([[HOME, 'in-reach'],
    ['T04ENG', 'out-of-reach'], ['T04SUP', 'ambiguous']], HOME);
  assert.equal(state, 'single-workspace-reach');
  assert.equal(counts.ambiguous, 1);
});

test('reaching some but not all is partial', () => {
  const [state] = reachSummary([[HOME, 'in-reach'], ['T04ENG', 'in-reach'],
    ['T04SUP', 'out-of-reach']], HOME);
  assert.equal(state, 'partial');
});

test('a sweep of only ambiguous answers concludes nothing', () => {
  assert.equal(reachSummary([['T04ENG', 'ambiguous'],
    ['T04SUP', 'not-assessed']])[0], 'not-assessed');
});

test('probing no workspaces says so', () => {
  assert.equal(reachSummary([])[0], 'no-workspaces');
});

test('team_id is required on the listing methods once org wide', () => {
  const [state, detail] = teamIdRequirement('conversations.list', true);
  assert.equal(state, 'required');
  assert.match(detail, /org-wide/);
});

test('team_id is merely accepted on the methods that take it optionally', () => {
  assert.equal(teamIdRequirement('team.info', true)[0], 'optional');
});

test('a workspace scoped token does not need the parameter at all', () => {
  const [state, detail] = teamIdRequirement('users.list', false);
  assert.equal(state, 'unnecessary');
  assert.match(detail, /one workspace to answer for/);
});

test('a method outside the list is not guessed at', () => {
  const [state, detail] = teamIdRequirement('chat.postMessage', true);
  assert.equal(state, 'unknown-method');
  assert.match(detail, /reference page/);
});

test('the repair prints both routes when the token is bounded', () => {
  const lines = repairPlan('workspace-in-grid', 'single-workspace-reach', []);
  assert.equal(lines.some((l) => l.includes('org_deploy_enabled')), true);
  assert.equal(lines.some((l) => l.includes('per workspace')), true);
});

test('the team_id repair counts the methods it applies to', () => {
  const lines = repairPlan('org-wide', 'org-wide-reach',
    ['conversations.list', 'users.list']);
  assert.equal(lines.length, 1);
  assert.match(lines[0], /2 method\\(s\\)/);
});

test('a healthy org wide token needs no repair at all', () => {
  assert.deepEqual(repairPlan('org-wide', 'org-wide-reach', []), []);
});
''',
"faq": [
 ("How do I tell a Grid workspace install from an ordinary one?",
  "By reading two fields of auth.test together, because neither is conclusive alone. is_enterprise_install is false for every ordinary workspace in the world, so it means nothing by itself. enterprise_id is populated for org-wide installs too, so it means nothing by itself either. It is the pair that identifies the configuration: is_enterprise_install false with a non-null enterprise_id is a workspace install sitting inside a Grid organization, which behaves exactly like a normal install until somebody outside that workspace touches it."),
 ("Why does the check refuse to say whether a channel_not_found means the channel is out of reach?",
  "Because Slack refuses to say. That error covers both a resource that does not exist and a resource you are not permitted to know about, and the ambiguity is deliberate: telling you which one it was would leak the existence of private conversations to tokens that cannot see them. Any script that converts channel_not_found into out-of-reach is guessing, and it will be wrong roughly whenever the id was simply stale. Reporting ambiguous is less satisfying and considerably more useful, because it tells you the probe needs a resource you can confirm exists."),
 ("We installed org-wide and some calls started returning the wrong workspace's data. What happened?",
  "You crossed into the second half of the repair. A workspace-scoped token has exactly one workspace to answer for, so a call like conversations.list is unambiguous whether or not you pass team_id. An org-wide token can see many, and several methods then need to be told which one you meant. Code that has never sent the parameter keeps working in the home workspace, because that is the default resolution, and answers for the wrong one elsewhere. Run the check with --methods before the install so the parameter work ships alongside it."),
 ("Is this the same as keying our installation store on team_id alone?",
  "No, and they are worth keeping apart because one is about a token and the other is about a table. This note is about how far a single credential reaches: what one token can see, and what it is refused. The storage question is whether your database can even represent the answer, given that an org-wide install may have a null team_id and that two workspaces in the same organization can collide under a team_id key. That failure mode is cross-tenant data leakage rather than a refusal, and it has its own note, linked below."),
 ("The customer will not install org-wide. What are the options?",
  "Install per workspace and store one token for each, which is supported and is what many apps do. The cost is in your data model rather than in your code: the installation store now holds several rows for one customer, your lookup has to resolve an incoming event to the right one, and anything that reports per customer has to aggregate across them. It is more work than an org-wide install and less work than discovering the requirement after the contract is signed, which is the usual alternative."),
],
"related": [
 ("/slack/enterprise-id-not-stored/", "whether your store can represent the answer at all"),
 ("/slack/private-channel-invisible/", "the other place channel_not_found means two things"),
 ("/slack/accesslimited-ip-allowlist/", "a different organization-level refusal"),
],
"citations": [CITE_GRID, CITE_AUTH_TEST, CITE_CONVERSATIONS_LIST, CITE_BOLT_1778],
})
