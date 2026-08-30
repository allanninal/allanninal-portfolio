#!/usr/bin/env python3
"""/slack/ field notes, batch W - the writing.

Four notes about app configuration, separated by which surface the reader is
standing on when it fails, and by what a script is actually allowed to read.

The first fails before a token exists. An install runs, the browser comes back
to your callback, and the exchange answers bad_redirect_uri because the string
your code sent as redirect_uri is not the string Slack has on its allow list -
a scheme, a port, a trailing slash, or the parameter present in one leg of the
flow and absent from the other. The reading is two URLs held against each
other component by component, and the one method that would "just answer this"
is refused: oauth.v2.access redeems a single-use code and completes an
installation, so a diagnostic that calls it destroys its own evidence.

The second is not about your app being wrong at all. app_access_restricted is
an admin saying a particular set of people may not use this app, decided after
installation and changed without notice. The reading is a cohort: which users
got the refusal, which users did not, and what the first group share that the
second does not. It is a policy on the app and the person, which is a
different axis from a policy on the network the call came from.

The third is one switch and one subscription that have to agree. The App Home
Messages tab is off by default, a separate checkbox makes it read only, and
neither of them delivers anything without message.im in the event list. The
reading is a triple from the manifest, corroborated by IM conversations that
carry only outbound messages.

The fourth is a set difference. Slash commands are declared in app
configuration, not in code, so a handler added in Bolt without a matching
registration is dead code and a registration without a handler answers users
with dispatch_failed. The reading is the two lists, from the manifest and from
your own source, diffed in both directions.

Read only throughout. Three of the four make one GET each to
apps.manifest.export, which needs an app configuration token - a different
credential class from the bot token your app runs on - and every one of them
degrades to the half of the check that does not need it rather than refusing to
run. No client secret, signing secret or authorization code is read, printed or
transmitted by anything here.
"""

CITE_OAUTH_ACCESS = ("oauth.v2.access method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/oauth.v2.access")
CITE_INSTALL_OAUTH = ("Installing with OAuth - Slack Docs",
                      "https://docs.slack.dev/authentication/installing-with-oauth")
CITE_MANIFEST_EXPORT = ("apps.manifest.export method reference - Slack Docs",
                        "https://docs.slack.dev/reference/methods/apps.manifest.export")
CITE_MANIFEST_REF = ("App manifest reference - Slack Docs",
                     "https://docs.slack.dev/reference/manifests")
CITE_SO_REDIRECT = ("Stack Overflow: Slack OAuth returns bad_redirect_uri",
                    "https://stackoverflow.com/questions/52690878")
CITE_POST_MESSAGE = ("chat.postMessage method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_ADMIN_RESTRICTED = ("admin.apps.restricted.list method reference - Slack Docs",
                         "https://docs.slack.dev/reference/methods/"
                         "admin.apps.restricted.list")
CITE_ADMIN_APPROVED = ("admin.apps.approved.list method reference - Slack Docs",
                       "https://docs.slack.dev/reference/methods/"
                       "admin.apps.approved.list")
CITE_USERS_INFO = ("users.info method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.info")
CITE_APP_HOME = ("App Home surfaces - Slack Docs",
                 "https://docs.slack.dev/surfaces/app-home")
CITE_MESSAGE_IM = ("message.im event reference - Slack Docs",
                   "https://docs.slack.dev/reference/events/message.im")
CITE_SO_MSG_TAB = ("Stack Overflow: cannot send a DM, messages_tab_disabled",
                   "https://stackoverflow.com/questions/67672427")
CITE_SLASH_COMMANDS = ("Implementing slash commands - Slack Docs",
                       "https://docs.slack.dev/interactivity/implementing-slash-commands")
CITE_BOLT_579 = ("bolt-js #579: a command handler that never fires because the "
                 "command was never registered",
                 "https://github.com/slackapi/bolt-js/issues/579")
CITE_SO_SLASH = ("Stack Overflow: /command is not a valid command in Slack",
                 "https://stackoverflow.com/questions/63665120")

GUIDES = []

GUIDES.append({
"slug": "oauth-redirect-mismatch",
"title": "bad_redirect_uri: the callback URL is not on the allow list",
"description": "Slack compares redirect_uri character for character at the exchange. Hold every deployed callback against the configured list without redeeming a code.",
"h1": "bad_redirect_uri: the callback URL is not on the allow list",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack bad_redirect_uri oauth.v2.access",
             "slack oauth redirect_uri mismatch",
             "slack redirect url not on allow list",
             "slack install works in staging fails in production",
             "slack oauth_config redirect_urls manifest"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token with app_configurations:read to export the manifest, or the configured Redirect URLs pasted in by hand",
"lead": "The install works. You have run it forty times on your laptop, and every one of them came back with a workspace, a bot user and a token. Then the app goes to production behind a real domain, the first customer clicks <em>Add to Slack</em>, and the browser lands on a Slack error page or your callback logs <code>{\"ok\": false, \"error\": \"bad_redirect_uri\"}</code> and nothing else.</p><p>Nothing about your code changed. What changed is one string. Slack holds the <code>redirect_uri</code> you present at the exchange against the Redirect URLs configured on the app, and the comparison is unforgiving about the parts of a URL people treat as decoration: the scheme, the port, the path, the trailing slash, and whether the parameter was sent at all.",
"short_answer": """<p><code>bad_redirect_uri</code> means the <code>redirect_uri</code> your server sent to <code>oauth.v2.access</code> is not covered by any entry under <strong>OAuth &amp; Permissions &rarr; Redirect URLs</strong>. Slack matches from the configured entry forward, so a configured <code>https://app.example.com/slack</code> covers <code>https://app.example.com/slack/callback</code> &mdash; but only after the scheme, the host and the port have matched exactly. <code>http</code> against <code>https</code> is a miss. <code>:8080</code> against nothing is a miss. <code>/slack/callback/</code> against a configured <code>/slack/callback</code> is a match, and the reverse is not.</p>
<p>There is a second rule that catches the installs which worked yesterday. <code>redirect_uri</code> must be <strong>present and identical in both legs</strong> of the flow, or absent from both. Send it on the authorize URL and omit it at the exchange, or the other way round, and Slack refuses even though the URL itself is on the list. Omitting it from both is tolerated only while exactly one Redirect URL is configured &mdash; so adding a second one breaks an app that never sent the parameter, at a moment unconnected to any deploy.</p>
<p>None of this needs a live install to diagnose, and the temptation to get one is the trap. <strong>Do not call <code>oauth.v2.access</code> to see what it says.</strong> That call redeems an authorization code: the code is single use, it expires in minutes, and a successful exchange installs the app and mints a token. A diagnostic that runs it consumes the evidence and changes the thing it was measuring. The script below compares strings you already have, and makes exactly one read: the manifest.</p>""",
"problem": """<p>Every part of this is invisible in normal use, because the flow that fails is the one flow you cannot step through in a debugger. The user leaves your site, does something on Slack's domain, and comes back with a code that is valid for one attempt. Whatever is wrong has already happened by the time your handler runs, and the only thing your handler gets to see is the refusal.</p>
<p>The commonest shape is an environment that grew a new URL. Development ran on <code>http://localhost:3000/slack/callback</code>, which somebody added to the Redirect URLs list on day one and never removed. Staging arrived on a preview domain. Production arrived on the real one, behind a load balancer that terminates TLS, and the application &mdash; which now sees plain HTTP on the inside &mdash; builds its callback URL from the request it received and confidently sends <code>http://app.example.com/slack/callback</code> to an allow list containing only the <code>https</code> form. The proxy header that would have told it otherwise was never trusted.</p>
<p>The second shape is punctuation. A trailing slash appended by a framework's router. A port spelled out that the browser omits. A host with a capital letter, which does not matter, next to a path with one, which does. An entry pasted into the Slack form with a stray space at the end. These are all sub-visual differences between two strings that a human comparing them side by side will read as identical, which is exactly why the comparison belongs in a script.</p>
<p>The third shape is asymmetry, and it is the one that fails without warning long after the code was written. A library builds the authorize URL for you and includes <code>redirect_uri</code> automatically; your own exchange call, hand-rolled, does not. While one Redirect URL was configured, Slack filled in the blank and everything worked. The day somebody adds a second environment to the list, the blank becomes ambiguous and every install starts failing &mdash; on a change nobody associates with the install flow, made in a web form rather than in the repository.</p>
<p>And a note on the error itself, because it is not always the one you get. Slack's OAuth surface returns HTTP 200 with <code>ok: false</code> like the rest of the Web API, so a client checking the status code sees success and reads a token field that is not there. Some redirect problems never reach your server at all: the user is bounced to a Slack error page mid-install and your logs contain nothing, because nothing was ever sent to you.</p>""",
"why": """<p><strong>The exchange is a write, and this is the one place in this section where that word has teeth.</strong> <code>oauth.v2.access</code> does not report on an installation; it performs one. It redeems a code that can only be redeemed once, and on success it creates a token and an install record. Running it as a test either burns the user's code so they have to start over, or quietly installs your app into a workspace with whatever scopes were requested. The script here never sends a code anywhere.</p>
<p><strong>Comparing components beats comparing strings, because the answer has to name the difference.</strong> &ldquo;This callback is not on the list&rdquo; sends somebody to squint at two URLs. &ldquo;This callback matches the third configured entry in every part except the scheme&rdquo; is a repair. So the check splits both sides into scheme, host, port and path, normalises only the parts Slack treats as case-insensitive, and reports which component disagrees.</p>
<p><strong>The trailing slash is asymmetric and the script has to be too.</strong> Prefix matching runs from the configured entry forward, so a configured path is allowed to be shorter than the deployed one and never longer. That means <code>/slack</code> covers <code>/slack/callback</code>, and a configured <code>/slack/callback/</code> does <em>not</em> cover <code>/slack/callback</code>. Treating the slash as noise on both sides would produce a confident pass on an install that fails.</p>
<p><strong>The presence rule is worth a check of its own, because it has no error message that names it.</strong> Slack answers <code>bad_redirect_uri</code> whether the URL is wrong or merely inconsistent between the two legs, so the error cannot distinguish the two cases. The script asks for both strings and classifies the pair, which turns an identical error message into two different repairs.</p>
<p><strong>Nothing here reads a secret, and that is a design constraint rather than a courtesy.</strong> The client secret is required to complete an exchange and is required for nothing else in this diagnosis. A redirect URL is not sensitive: it is in the browser's address bar during every install. So the script reads URLs, prints URLs, and has no code path that touches <code>SLACK_CLIENT_SECRET</code> at all.</p>
<p><strong>This is the install flow, before any token exists.</strong> If your exchange succeeds and the token you get back stops working twelve hours later, or a refresh fails, that is the token lifecycle and it is a different note with a different check. The boundary is clean: this one ends the moment <code>oauth.v2.access</code> returns <code>ok: true</code>.</p>""",
"steps": [
 {"h": "Read the configured list from the manifest, or paste it in",
  "body": """<p><code>apps.manifest.export</code> returns <code>oauth_config.redirect_urls</code>. It needs an app configuration token, which is a different credential class from your bot token &mdash; if you do not have one, pass <code>--configured</code> with the entries copied from the OAuth &amp; Permissions page and every other check still runs. The list is the allow list, and it is the only side of the comparison Slack owns.</p>"""},
 {"h": "Say what is wrong with each configured entry on its own",
  "body": """<p><code>redirect_concerns</code> reads one entry and reports <code>insecure-scheme</code>, <code>loopback</code>, <code>has-query</code>, <code>has-fragment</code>, <code>trailing-slash</code>, <code>explicit-default-port</code> and <code>userinfo</code>. A <code>localhost</code> entry on a distributed app is not an error today and is a support ticket eventually; a query string is a misunderstanding, because Slack does not match on it and <code>state</code> is where per-install data belongs.</p>"""},
 {"h": "Hold every deployed callback against the list",
  "body": """<p><code>match_callback</code> answers <code>exact</code>, <code>prefix</code>, <code>near-miss</code>, <code>no-match</code> or <code>unusable</code>. The verdict that earns its keep is <code>near-miss</code>: it names the closest configured entry and the single component that differs, which is almost always the scheme behind a TLS-terminating proxy or a port that only exists inside a container.</p>"""},
 {"h": "Check the parameter is present in both legs or neither",
  "body": """<p><code>parameter_symmetry</code> takes the <code>redirect_uri</code> your authorize URL carries and the one your exchange sends, plus how many URLs are configured, and returns <code>identical</code>, <code>authorize-only</code>, <code>exchange-only</code>, <code>different</code>, <code>both-absent</code> or <code>ambiguous</code>. <code>ambiguous</code> is the time bomb: neither leg sends it and more than one URL is configured.</p>"""},
 {"h": "Trust the proxy header, or stop building the URL from the request",
  "body": """<p>The repair the script prints for <code>near-miss</code> on the scheme is not a Slack change. It is either configuring your framework to honour <code>X-Forwarded-Proto</code>, or &mdash; better &mdash; putting the callback URL in configuration as a literal string, the same string that is on the allow list, so that the two can only ever drift on purpose.</p>"""},
 {"h": "Put the list in the manifest so environments cannot drift",
  "body": """<p>Every entry belongs under <code>oauth_config.redirect_urls</code> in a manifest kept in the repository. A Redirect URL added through the web form exists in exactly one place, is invisible to code review, and is the reason an app can break on a Tuesday afternoon with no deploy attached to it.</p>"""},
],
"verify": """<p>Fix the string, redeploy, and run it again. The line to read is the last <code>callback</code> row: it should say <code>exact</code>, and the symmetry row should say <code>identical</code>.</p>
<pre><code class="language-bash">python3 slack_oauth_redirect.py --app-id A05NW7XQ1 \\
  --callbacks https://app.northwind.example/slack/callback \\
  --authorize-redirect https://app.northwind.example/slack/callback \\
  --exchange-redirect http://app.northwind.example/slack/callback
# manifest   ok             3 configured redirect url(s) for A05NW7XQ1
# configured 1              http://localhost:3000/slack/callback
#            loopback       an install that lands here only works on the machine
#                           that ran it; remove it before the app is distributed
# configured 2              https://staging.northwind.example/slack/callback/
#            trailing-slash matching runs from the configured entry forward, so this
#                           entry does not cover the same path without the slash
# configured 3              https://app.northwind.example/slack/callback
# callback   near-miss      https://app.northwind.example/slack/callback matches
#                           configured entry 3 in every part except the scheme
# symmetry   different      the authorize url and the exchange send different strings
# verdict    2 finding(s)
#   repair: send the identical redirect_uri in both the authorize url and the
#           oauth.v2.access exchange, or omit it from both
#   repair: build the callback url from configuration, not from the inbound
#           request, or honour X-Forwarded-Proto behind the load balancer
#   note:   no code was redeemed to establish this; oauth.v2.access is a write</code></pre>""",
"code_intro": "One network call, to <code>apps.manifest.export</code>, and it is optional. Everything that decides anything is a pure function over URL strings: <code>normalise_url</code> splits a callback into the four parts Slack compares and lowercases only the two that are case-insensitive, <code>redirect_concerns</code> reads one configured entry on its own terms, <code>match_callback</code> finds the closest entry and names the component that differs, and <code>parameter_symmetry</code> applies the present-in-both-or-neither rule. There is no code path that reads a client secret and none that redeems a code.",
"py_file": "slack_oauth_redirect.py",
"py": '''"""Compare the callback URLs you deploy against the ones Slack will accept.

Read only, and one method is refused on principle. oauth.v2.access redeems an
authorization code: the code is single use, it expires in minutes, and a
successful exchange installs the app and mints a token. A diagnostic that
"just tries it" consumes the evidence and performs the installation it was
asked to explain. Nothing here sends a code anywhere.

At most one GET is made, to apps.manifest.export, using an app configuration
token. Without one, pass --configured with the entries from the OAuth &
Permissions page and every other check still runs. No client secret is read,
printed or transmitted by any path in this file.
"""
import argparse
import logging
import os
import sys
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_oauth_redirect")

API = "https://slack.com/api/"

# Made explicit during normalisation so https://x and https://x:443 compare
# equal, which they do to Slack and do not to a string comparison.
DEFAULT_PORTS = {"http": "80", "https": "443"}

# Fine on a laptop, a support ticket in a distributed app: an install that
# lands on one of these only ever completes on the machine that started it.
LOCAL_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "::1", "host.docker.internal")

# The order matters: the component reported as the difference is the first one
# that disagrees, and a scheme mismatch explains a port mismatch rather than
# the other way round.
COMPONENTS = ("scheme", "host", "port", "path")


def _difference(got, want):
    """Which components disagree? Pure, and one subsumption is applied.

    Changing the scheme changes the default port with it, so http against
    https would otherwise be reported as two differences and never as a near
    miss - which is precisely the case this check exists to name. When both
    sides are sitting on the default port for their own scheme, the port is
    not an independent disagreement.
    """
    diff = [k for k in COMPONENTS if got[k] != want[k]]
    if ("scheme" in diff and "port" in diff
            and got["port"] == DEFAULT_PORTS.get(got["scheme"])
            and want["port"] == DEFAULT_PORTS.get(want["scheme"])):
        diff.remove("port")
    return diff


def normalise_url(url):
    """Split a callback URL into the four parts Slack compares. Pure.

    Returns (parts, notes). The scheme and the host are lowercased because they
    are case insensitive; the path is left exactly as written because it is
    not, and because a trailing slash is a real difference rather than a
    typographic one. The port is made explicit so that the two spellings of the
    default port stop being different strings.
    """
    text = str(url or "").strip()
    notes = []
    empty = {"scheme": "", "host": "", "port": "", "path": ""}
    if not text:
        return (empty, ["empty"])
    if "://" not in text:
        notes.append("no-scheme")
        text = "https://" + text
    try:
        split = urlsplit(text)
        port = split.port
    except ValueError:
        return (empty, ["unparseable"])
    scheme = (split.scheme or "").lower()
    host = (split.hostname or "").lower()
    if not host:
        return (empty, notes + ["unparseable"])
    if split.username or split.password:
        notes.append("userinfo")
    if port is not None and str(port) == DEFAULT_PORTS.get(scheme):
        notes.append("explicit-default-port")
    if split.query:
        notes.append("has-query")
    if split.fragment:
        notes.append("has-fragment")
    parts = {
        "scheme": scheme,
        "host": host,
        "port": str(port) if port is not None else DEFAULT_PORTS.get(scheme, ""),
        "path": split.path or "/",
    }
    return (parts, notes)


def redirect_concerns(url):
    """Everything worth saying about one configured Redirect URL. Pure.

    Returns a list of (code, why). Nothing here is fatal on its own; these are
    the entries that will fail later, for somebody else, on a machine you do
    not have.
    """
    parts, notes = normalise_url(url)
    if "empty" in notes:
        return [("empty", "an empty entry matches nothing and hides the list length")]
    if "unparseable" in notes:
        return [("unusable", "this is not a URL Slack can match a callback against")]
    out = []
    if "no-scheme" in notes:
        out.append(("no-scheme", "the entry has no scheme, so it cannot match "
                                 "anything; write it out in full"))
    if parts["host"] in LOCAL_HOSTS:
        out.append(("loopback", "an install that lands here only works on the "
                                "machine that ran it; remove it before the app "
                                "is distributed"))
    elif parts["scheme"] == "http":
        out.append(("insecure-scheme", "the authorization code travels back on "
                                       "this URL in clear text, and a callback "
                                       "built as https will not match it"))
    if "has-query" in notes:
        out.append(("has-query", "Slack does not match on the query string; carry "
                                 "per-install data in the state parameter"))
    if "has-fragment" in notes:
        out.append(("has-fragment", "a fragment never reaches your server, so it "
                                    "cannot be part of a callback URL"))
    if "userinfo" in notes:
        out.append(("userinfo", "credentials embedded in the URL will not match "
                                "and should not exist"))
    if "explicit-default-port" in notes:
        out.append(("explicit-default-port", "the default port is spelled out here "
                                             "and omitted by every browser"))
    if parts["path"] != "/" and parts["path"].endswith("/"):
        out.append(("trailing-slash", "matching runs from this entry forward, so it "
                                      "does not cover the same path without the "
                                      "trailing slash"))
    return out


def match_callback(callback, configured):
    """Is this deployed callback covered by any configured entry? Pure.

    Returns (state, detail). States:

      exact      the callback is one of the configured entries, character for
                 character once case and the default port are settled.
      prefix     a configured entry is a prefix of it, with the scheme, host
                 and port identical. This is what Slack actually accepts.
      near-miss  the closest entry differs in exactly one component, and the
                 detail names which. Almost always the scheme.
      no-match   nothing on the list is close.
      unusable   the callback itself does not parse.
    """
    want, notes = normalise_url(callback)
    if "empty" in notes or "unparseable" in notes or not want["host"]:
        return ("unusable", "the callback URL given is not a URL")
    entries = []
    for raw in configured or []:
        got, gnotes = normalise_url(raw)
        if "empty" in gnotes or "unparseable" in gnotes or not got["host"]:
            continue
        entries.append((raw, got))
    if not entries:
        return ("no-match", "no usable entry is configured, so every install fails")
    for raw, got in entries:
        if got == want:
            return ("exact", "matches %s character for character" % raw)
    for raw, got in entries:
        same_origin = all(got[k] == want[k] for k in ("scheme", "host", "port"))
        if same_origin and want["path"].startswith(got["path"]):
            return ("prefix", "%s is a prefix of this callback, which Slack accepts; "
                              "the string sent as redirect_uri still has to be one "
                              "Slack can match" % raw)
    best, best_diff = None, None
    for raw, got in entries:
        diff = _difference(got, want)
        if best_diff is None or len(diff) < len(best_diff):
            best, best_diff = raw, diff
    if len(best_diff) == 1:
        return ("near-miss", "matches %s in every part except the %s"
                % (best, best_diff[0]))
    return ("no-match", "the closest entry is %s and it differs in the %s"
            % (best, ", ".join(best_diff)))


def parameter_symmetry(authorize_redirect, exchange_redirect, configured_count):
    """Apply the present-in-both-legs-or-neither rule. Pure.

    Returns (state, detail). Slack answers bad_redirect_uri for an inconsistent
    pair exactly as it does for a wrong URL, so the error cannot tell these
    apart and this function has to.

      identical      both legs send the same string. Correct.
      both-absent    neither leg sends it, and one URL is configured. Tolerated.
      ambiguous      neither leg sends it and more than one URL is configured.
                     This is the install that breaks when somebody edits a web
                     form months after the code was written.
      authorize-only / exchange-only / different are the three ways to send it
      inconsistently, and all three are refused.
    """
    left = str(authorize_redirect or "").strip()
    right = str(exchange_redirect or "").strip()
    if left and right:
        if normalise_url(left)[0] == normalise_url(right)[0]:
            return ("identical", "both legs send the same redirect_uri")
        return ("different", "the authorize URL sends %s and the exchange sends %s; "
                             "they must be the identical string" % (left, right))
    if left and not right:
        return ("authorize-only", "the authorize URL carries redirect_uri and the "
                                  "exchange omits it; send it in both or neither")
    if right and not left:
        return ("exchange-only", "the exchange sends redirect_uri and the authorize "
                                 "URL omits it; send it in both or neither")
    if int(configured_count or 0) > 1:
        return ("ambiguous", "neither leg sends redirect_uri and %d URLs are "
                             "configured, so Slack has nothing to disambiguate with"
                % int(configured_count))
    return ("both-absent", "neither leg sends redirect_uri and exactly one URL is "
                           "configured, which Slack tolerates; sending it in both "
                           "is still the safer shape")


def export_manifest(session, token, app_id):
    """One GET, with an app configuration token. Returns the parsed body."""
    r = session.get(API + "apps.manifest.export",
                    headers={"Authorization": "Bearer " + token},
                    params={"app_id": app_id}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app-id", default="", help="the app id to export, A...")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_ACCESS_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--configured", default="",
                    help="comma separated Redirect URLs, if you have no config token")
    ap.add_argument("--callbacks", default="",
                    help="comma separated callback URLs your deployments actually use")
    ap.add_argument("--authorize-redirect", default="",
                    help="the redirect_uri your authorize URL carries, if any")
    ap.add_argument("--exchange-redirect", default="",
                    help="the redirect_uri your oauth.v2.access call sends, if any")
    args = ap.parse_args()

    findings = 0
    configured = [u.strip() for u in args.configured.split(",") if u.strip()]
    token = os.environ.get(args.config_token_env)
    if args.app_id and token and not configured:
        body = export_manifest(requests.Session(), token, args.app_id)
        if body.get("ok") is not True:
            log.warning("manifest   unavailable    apps.manifest.export answered "
                        "ok: false, error=%s", body.get("error"))
        else:
            oauth_config = (body.get("manifest") or body).get("oauth_config") or {}
            configured = list(oauth_config.get("redirect_urls") or [])
            log.info("manifest   ok             %d configured redirect url(s) for %s",
                     len(configured), args.app_id)
    elif not configured:
        log.info("manifest   skipped        set %s, or pass --configured with the "
                 "entries from the OAuth & Permissions page", args.config_token_env)

    for i, entry in enumerate(configured, start=1):
        log.info("configured %-14d %s", i, entry)
        for code, why in redirect_concerns(entry):
            log.warning("           %-14s %s", code, why)
            findings += 1

    for callback in [u.strip() for u in args.callbacks.split(",") if u.strip()]:
        state, detail = match_callback(callback, configured)
        line = ("callback   %-14s %s -> %s", state, callback, detail)
        if state in ("exact", "prefix"):
            log.info(*line)
        else:
            log.warning(*line)
            findings += 1

    state, detail = parameter_symmetry(args.authorize_redirect, args.exchange_redirect,
                                       len(configured))
    if state in ("identical", "both-absent"):
        log.info("symmetry   %-14s %s", state, detail)
    else:
        log.warning("symmetry   %-14s %s", state, detail)
        findings += 1

    if not findings:
        log.info("verdict    clean          every deployed callback is covered and "
                 "both legs agree")
        return 0
    log.warning("verdict    %d finding(s)", findings)
    log.warning("  repair: add the exact callback URL for every environment under "
                "OAuth & Permissions, scheme and path included")
    log.warning("  repair: send the identical redirect_uri in both the authorize URL "
                "and the oauth.v2.access exchange, or omit it from both")
    log.warning("  repair: keep the list in the manifest under "
                "oauth_config.redirect_urls so environments cannot drift")
    log.warning("  note:   no code was redeemed to establish this; oauth.v2.access "
                "is a write and would install the app")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-oauth-redirect.mjs",
"js": '''/**
 * Compare the callback URLs you deploy against the ones Slack will accept.
 *
 * Read only, and one method is refused on principle. oauth.v2.access redeems
 * an authorization code: the code is single use, it expires in minutes, and a
 * successful exchange installs the app and mints a token. Nothing here sends a
 * code anywhere.
 *
 * At most one GET is made, to apps.manifest.export, using an app configuration
 * token. No client secret is read, printed or transmitted by any path here.
 */

const API = 'https://slack.com/api/';

// Made explicit during normalisation so https://x and https://x:443 compare
// equal, which they do to Slack and do not to a string comparison.
export const DEFAULT_PORTS = { http: '80', https: '443' };

// Fine on a laptop, a support ticket in a distributed app.
export const LOCAL_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '::1',
  'host.docker.internal'];

// The reported difference is the first component that disagrees, and a scheme
// mismatch explains a port mismatch rather than the other way round.
export const COMPONENTS = ['scheme', 'host', 'port', 'path'];

/**
 * Which components disagree? Pure, and one subsumption is applied. Changing
 * the scheme changes the default port with it, so http against https would
 * otherwise be two differences and never a near miss - which is precisely the
 * case this check exists to name.
 */
function difference(got, want) {
  const diff = COMPONENTS.filter((k) => got[k] !== want[k]);
  if (diff.includes('scheme') && diff.includes('port')
    && got.port === DEFAULT_PORTS[got.scheme]
    && want.port === DEFAULT_PORTS[want.scheme]) {
    return diff.filter((k) => k !== 'port');
  }
  return diff;
}

/**
 * Split a callback URL into the four parts Slack compares. Pure.
 * Returns [parts, notes].
 */
export function normaliseUrl(url) {
  const empty = { scheme: '', host: '', port: '', path: '' };
  let text = String(url ?? '').trim();
  const notes = [];
  if (!text) return [empty, ['empty']];
  if (!text.includes('://')) {
    notes.push('no-scheme');
    text = `https://${text}`;
  }
  let parsed;
  try {
    parsed = new URL(text);
  } catch {
    return [empty, notes.concat(['unparseable'])];
  }
  const scheme = parsed.protocol.replace(':', '').toLowerCase();
  const host = parsed.hostname.toLowerCase().replace(/^\\[|\\]$/g, '');
  if (!host) return [empty, notes.concat(['unparseable'])];
  if (parsed.username || parsed.password) notes.push('userinfo');
  if (parsed.port && parsed.port === DEFAULT_PORTS[scheme]) {
    notes.push('explicit-default-port');
  }
  if (parsed.search) notes.push('has-query');
  if (parsed.hash) notes.push('has-fragment');
  const parts = {
    scheme,
    host,
    port: parsed.port || DEFAULT_PORTS[scheme] || '',
    path: parsed.pathname || '/',
  };
  return [parts, notes];
}

/** Everything worth saying about one configured Redirect URL. Pure. */
export function redirectConcerns(url) {
  const [parts, notes] = normaliseUrl(url);
  if (notes.includes('empty')) {
    return [['empty', 'an empty entry matches nothing and hides the list length']];
  }
  if (notes.includes('unparseable')) {
    return [['unusable', 'this is not a URL Slack can match a callback against']];
  }
  const out = [];
  if (notes.includes('no-scheme')) {
    out.push(['no-scheme', 'the entry has no scheme, so it cannot match anything; '
      + 'write it out in full']);
  }
  if (LOCAL_HOSTS.includes(parts.host)) {
    out.push(['loopback', 'an install that lands here only works on the machine that '
      + 'ran it; remove it before the app is distributed']);
  } else if (parts.scheme === 'http') {
    out.push(['insecure-scheme', 'the authorization code travels back on this URL in '
      + 'clear text, and a callback built as https will not match it']);
  }
  if (notes.includes('has-query')) {
    out.push(['has-query', 'Slack does not match on the query string; carry '
      + 'per-install data in the state parameter']);
  }
  if (notes.includes('has-fragment')) {
    out.push(['has-fragment', 'a fragment never reaches your server, so it cannot be '
      + 'part of a callback URL']);
  }
  if (notes.includes('userinfo')) {
    out.push(['userinfo', 'credentials embedded in the URL will not match and should '
      + 'not exist']);
  }
  if (notes.includes('explicit-default-port')) {
    out.push(['explicit-default-port', 'the default port is spelled out here and '
      + 'omitted by every browser']);
  }
  if (parts.path !== '/' && parts.path.endsWith('/')) {
    out.push(['trailing-slash', 'matching runs from this entry forward, so it does '
      + 'not cover the same path without the trailing slash']);
  }
  return out;
}

/**
 * Is this deployed callback covered by any configured entry? Pure.
 * Returns [state, detail]; exact, prefix, near-miss, no-match, unusable.
 */
export function matchCallback(callback, configured) {
  const [want, notes] = normaliseUrl(callback);
  if (notes.includes('empty') || notes.includes('unparseable') || !want.host) {
    return ['unusable', 'the callback URL given is not a URL'];
  }
  const entries = [];
  for (const raw of configured ?? []) {
    const [got, gnotes] = normaliseUrl(raw);
    if (gnotes.includes('empty') || gnotes.includes('unparseable') || !got.host) {
      continue;
    }
    entries.push([raw, got]);
  }
  if (!entries.length) {
    return ['no-match', 'no usable entry is configured, so every install fails'];
  }
  for (const [raw, got] of entries) {
    if (COMPONENTS.every((k) => got[k] === want[k])) {
      return ['exact', `matches ${raw} character for character`];
    }
  }
  for (const [raw, got] of entries) {
    const sameOrigin = ['scheme', 'host', 'port'].every((k) => got[k] === want[k]);
    if (sameOrigin && want.path.startsWith(got.path)) {
      return ['prefix', `${raw} is a prefix of this callback, which Slack accepts; `
        + 'the string sent as redirect_uri still has to be one Slack can match'];
    }
  }
  let best = null;
  let bestDiff = null;
  for (const [raw, got] of entries) {
    const diff = difference(got, want);
    if (bestDiff === null || diff.length < bestDiff.length) {
      best = raw;
      bestDiff = diff;
    }
  }
  if (bestDiff.length === 1) {
    return ['near-miss', `matches ${best} in every part except the ${bestDiff[0]}`];
  }
  return ['no-match',
    `the closest entry is ${best} and it differs in the ${bestDiff.join(', ')}`];
}

/**
 * Apply the present-in-both-legs-or-neither rule. Pure.
 * Returns [state, detail]; identical, both-absent, ambiguous, authorize-only,
 * exchange-only, different.
 */
export function parameterSymmetry(authorizeRedirect, exchangeRedirect, configuredCount) {
  const left = String(authorizeRedirect ?? '').trim();
  const right = String(exchangeRedirect ?? '').trim();
  if (left && right) {
    const a = normaliseUrl(left)[0];
    const b = normaliseUrl(right)[0];
    if (COMPONENTS.every((k) => a[k] === b[k])) {
      return ['identical', 'both legs send the same redirect_uri'];
    }
    return ['different', `the authorize URL sends ${left} and the exchange sends `
      + `${right}; they must be the identical string`];
  }
  if (left && !right) {
    return ['authorize-only', 'the authorize URL carries redirect_uri and the '
      + 'exchange omits it; send it in both or neither'];
  }
  if (right && !left) {
    return ['exchange-only', 'the exchange sends redirect_uri and the authorize URL '
      + 'omits it; send it in both or neither'];
  }
  if (Number(configuredCount ?? 0) > 1) {
    return ['ambiguous', `neither leg sends redirect_uri and ${Number(configuredCount)} `
      + 'URLs are configured, so Slack has nothing to disambiguate with'];
  }
  return ['both-absent', 'neither leg sends redirect_uri and exactly one URL is '
    + 'configured, which Slack tolerates; sending it in both is still the safer shape'];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function exportManifest(token, appId) {
  const url = `${API}apps.manifest.export?app_id=${encodeURIComponent(appId)}`;
  const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const appId = arg(args, '--app-id');
  const tokenEnv = arg(args, '--config-token-env', 'SLACK_CONFIG_ACCESS_TOKEN');
  let configured = arg(args, '--configured').split(',')
    .map((u) => u.trim()).filter(Boolean);
  let findings = 0;

  const token = process.env[tokenEnv];
  if (appId && token && !configured.length) {
    const body = await exportManifest(token, appId);
    if (body.ok !== true) {
      console.warn('manifest   unavailable    apps.manifest.export answered ok: false, '
        + `error=${body.error}`);
    } else {
      const oauthConfig = (body.manifest ?? body).oauth_config ?? {};
      configured = [...(oauthConfig.redirect_urls ?? [])];
      console.log(`manifest   ok             ${configured.length} configured redirect `
        + `url(s) for ${appId}`);
    }
  } else if (!configured.length) {
    console.log(`manifest   skipped        set ${tokenEnv}, or pass --configured with `
      + 'the entries from the OAuth & Permissions page');
  }

  configured.forEach((entry, i) => {
    console.log(`configured ${String(i + 1).padEnd(14)} ${entry}`);
    for (const [code, why] of redirectConcerns(entry)) {
      console.warn(`           ${code.padEnd(14)} ${why}`);
      findings += 1;
    }
  });

  for (const callback of arg(args, '--callbacks').split(',')
    .map((u) => u.trim()).filter(Boolean)) {
    const [state, detail] = matchCallback(callback, configured);
    const line = `callback   ${state.padEnd(14)} ${callback} -> ${detail}`;
    if (state === 'exact' || state === 'prefix') console.log(line);
    else { console.warn(line); findings += 1; }
  }

  const [state, detail] = parameterSymmetry(arg(args, '--authorize-redirect'),
    arg(args, '--exchange-redirect'), configured.length);
  const line = `symmetry   ${state.padEnd(14)} ${detail}`;
  if (state === 'identical' || state === 'both-absent') console.log(line);
  else { console.warn(line); findings += 1; }

  if (!findings) {
    console.log('verdict    clean          every deployed callback is covered and both '
      + 'legs agree');
    return;
  }
  console.warn(`verdict    ${findings} finding(s)`);
  console.warn('  repair: add the exact callback URL for every environment under OAuth '
    + '& Permissions, scheme and path included');
  console.warn('  repair: send the identical redirect_uri in both the authorize URL and '
    + 'the oauth.v2.access exchange, or omit it from both');
  console.warn('  repair: keep the list in the manifest under '
    + 'oauth_config.redirect_urls so environments cannot drift');
  console.warn('  note:   no code was redeemed to establish this; oauth.v2.access is a '
    + 'write and would install the app');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "No credential appears in these fixtures at all, which is the point worth noticing: the whole diagnosis runs on URLs that are already in a browser address bar during every install. The assertions that matter are the asymmetric ones &mdash; a configured path may be shorter than the callback and never longer, so <code>/slack</code> covering <code>/slack/callback</code> and <code>/slack/callback/</code> failing to cover <code>/slack/callback</code> are both pinned &mdash; and the <code>ambiguous</code> case, where neither leg sends the parameter and a second configured URL has quietly turned a working install into a broken one.",
"test_py_file": "test_slack_oauth_redirect.py",
"test_py": '''from slack_oauth_redirect import (
    match_callback, normalise_url, parameter_symmetry, redirect_concerns,
)

PROD = "https://app.example.com/slack/callback"
STAGE = "https://staging.example.com/slack/callback"


def test_the_default_port_is_made_explicit_so_two_spellings_agree():
    assert normalise_url("https://a.example.com/x")[0]["port"] == "443"
    assert normalise_url("https://a.example.com:443/x")[0]["port"] == "443"


def test_the_host_folds_case_and_the_path_does_not():
    parts, _notes = normalise_url("https://APP.Example.COM/Slack/Callback")
    assert parts["host"] == "app.example.com"
    assert parts["path"] == "/Slack/Callback"


def test_an_entry_with_no_scheme_is_flagged_rather_than_guessed_at():
    assert "no-scheme" in normalise_url("app.example.com/slack")[1]
    assert redirect_concerns("app.example.com/slack")[0][0] == "no-scheme"


def test_a_localhost_entry_is_reported_before_it_reaches_a_customer():
    codes = [c for c, _w in redirect_concerns("http://localhost:3000/slack/callback")]
    assert "loopback" in codes
    assert "insecure-scheme" not in codes


def test_plain_http_on_a_real_host_is_its_own_finding():
    codes = [c for c, _w in redirect_concerns("http://app.example.com/slack/callback")]
    assert "insecure-scheme" in codes


def test_a_query_string_is_a_misunderstanding_and_says_so():
    codes = [c for c, w in redirect_concerns(PROD + "?tenant=northwind")]
    assert "has-query" in codes


def test_a_trailing_slash_on_a_configured_entry_is_reported():
    codes = [c for c, _w in redirect_concerns(PROD + "/")]
    assert "trailing-slash" in codes


def test_an_empty_or_unusable_entry_is_named_rather_than_skipped():
    assert redirect_concerns("")[0][0] == "empty"
    assert redirect_concerns("https://")[0][0] == "unusable"


def test_an_exact_match_is_exact():
    state, detail = match_callback(PROD, [STAGE, PROD])
    assert state == "exact"
    assert PROD in detail


def test_a_configured_prefix_covers_a_longer_callback_path():
    assert match_callback(PROD, ["https://app.example.com/slack"])[0] == "prefix"


def test_a_configured_path_that_is_longer_does_not_cover_the_callback():
    assert match_callback(PROD, [PROD + "/"])[0] != "prefix"
    assert match_callback(PROD, [PROD + "/"])[0] != "exact"


def test_the_scheme_alone_is_named_as_the_difference():
    state, detail = match_callback("http://app.example.com/slack/callback", [PROD])
    assert state == "near-miss"
    assert "scheme" in detail


def test_a_port_that_only_exists_inside_the_container_is_named_too():
    state, detail = match_callback("https://app.example.com:8080/slack/callback",
                                   [PROD])
    assert state == "near-miss"
    assert "port" in detail


def test_a_wholly_different_host_and_path_is_a_plain_no_match():
    state, detail = match_callback("https://other.example.net/auth", [PROD])
    assert state == "no-match"
    assert "host" in detail


def test_an_empty_configured_list_fails_every_install():
    assert match_callback(PROD, [])[0] == "no-match"


def test_both_legs_sending_the_same_string_is_the_correct_shape():
    assert parameter_symmetry(PROD, PROD, 2)[0] == "identical"


def test_sending_it_in_one_leg_only_is_refused_either_way_round():
    assert parameter_symmetry(PROD, "", 1)[0] == "authorize-only"
    assert parameter_symmetry("", PROD, 1)[0] == "exchange-only"


def test_two_different_strings_are_reported_as_different_not_as_a_mismatch():
    state, detail = parameter_symmetry(PROD, STAGE, 2)
    assert state == "different"
    assert STAGE in detail


def test_omitting_it_everywhere_is_tolerated_with_exactly_one_url():
    assert parameter_symmetry("", "", 1)[0] == "both-absent"


def test_omitting_it_everywhere_becomes_ambiguous_the_day_a_second_url_appears():
    state, detail = parameter_symmetry("", "", 2)
    assert state == "ambiguous"
    assert "2" in detail
''',
"test_js_file": "slack-oauth-redirect.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  matchCallback, normaliseUrl, parameterSymmetry, redirectConcerns,
} from './slack-oauth-redirect.mjs';

const PROD = 'https://app.example.com/slack/callback';
const STAGE = 'https://staging.example.com/slack/callback';

const codes = (url) => redirectConcerns(url).map(([c]) => c);

test('the default port is made explicit so two spellings agree', () => {
  assert.equal(normaliseUrl('https://a.example.com/x')[0].port, '443');
  assert.equal(normaliseUrl('https://a.example.com:443/x')[0].port, '443');
});

test('the host folds case and the path does not', () => {
  const [parts] = normaliseUrl('https://APP.Example.COM/Slack/Callback');
  assert.equal(parts.host, 'app.example.com');
  assert.equal(parts.path, '/Slack/Callback');
});

test('an entry with no scheme is flagged rather than guessed at', () => {
  assert.equal(normaliseUrl('app.example.com/slack')[1].includes('no-scheme'), true);
  assert.equal(redirectConcerns('app.example.com/slack')[0][0], 'no-scheme');
});

test('a localhost entry is reported before it reaches a customer', () => {
  const found = codes('http://localhost:3000/slack/callback');
  assert.equal(found.includes('loopback'), true);
  assert.equal(found.includes('insecure-scheme'), false);
});

test('plain http on a real host is its own finding', () => {
  assert.equal(codes('http://app.example.com/slack/callback')
    .includes('insecure-scheme'), true);
});

test('a query string is a misunderstanding and says so', () => {
  assert.equal(codes(`${PROD}?tenant=northwind`).includes('has-query'), true);
});

test('a trailing slash on a configured entry is reported', () => {
  assert.equal(codes(`${PROD}/`).includes('trailing-slash'), true);
});

test('an empty or unusable entry is named rather than skipped', () => {
  assert.equal(redirectConcerns('')[0][0], 'empty');
  assert.equal(redirectConcerns('https://')[0][0], 'unusable');
});

test('an exact match is exact', () => {
  const [state, detail] = matchCallback(PROD, [STAGE, PROD]);
  assert.equal(state, 'exact');
  assert.match(detail, /app\\.example\\.com/);
});

test('a configured prefix covers a longer callback path', () => {
  assert.equal(matchCallback(PROD, ['https://app.example.com/slack'])[0], 'prefix');
});

test('a configured path that is longer does not cover the callback', () => {
  assert.notEqual(matchCallback(PROD, [`${PROD}/`])[0], 'prefix');
  assert.notEqual(matchCallback(PROD, [`${PROD}/`])[0], 'exact');
});

test('the scheme alone is named as the difference', () => {
  const [state, detail] = matchCallback('http://app.example.com/slack/callback',
    [PROD]);
  assert.equal(state, 'near-miss');
  assert.match(detail, /scheme/);
});

test('a port that only exists inside the container is named too', () => {
  const [state, detail] = matchCallback('https://app.example.com:8080/slack/callback',
    [PROD]);
  assert.equal(state, 'near-miss');
  assert.match(detail, /port/);
});

test('a wholly different host and path is a plain no match', () => {
  const [state, detail] = matchCallback('https://other.example.net/auth', [PROD]);
  assert.equal(state, 'no-match');
  assert.match(detail, /host/);
});

test('an empty configured list fails every install', () => {
  assert.equal(matchCallback(PROD, [])[0], 'no-match');
});

test('both legs sending the same string is the correct shape', () => {
  assert.equal(parameterSymmetry(PROD, PROD, 2)[0], 'identical');
});

test('sending it in one leg only is refused either way round', () => {
  assert.equal(parameterSymmetry(PROD, '', 1)[0], 'authorize-only');
  assert.equal(parameterSymmetry('', PROD, 1)[0], 'exchange-only');
});

test('two different strings are reported as different not as a mismatch', () => {
  const [state, detail] = parameterSymmetry(PROD, STAGE, 2);
  assert.equal(state, 'different');
  assert.match(detail, /staging/);
});

test('omitting it everywhere is tolerated with exactly one url', () => {
  assert.equal(parameterSymmetry('', '', 1)[0], 'both-absent');
});

test('omitting it everywhere becomes ambiguous the day a second url appears', () => {
  const [state, detail] = parameterSymmetry('', '', 2);
  assert.equal(state, 'ambiguous');
  assert.match(detail, /2/);
});
''',
"faq": [
 ("Why not just run one install and read the error from oauth.v2.access?",
  "Because that call is a write, and an unusually consequential one. It redeems an authorization code, which is single use and expires within minutes, so a test run either burns the code a real user was in the middle of using or completes an installation into a workspace with every scope your authorize URL asked for. There is no read-only variant. Everything this note needs is already in your hands: the configured list, the URLs your deployments use, and the two strings your code sends. The script compares those and never transmits a code."),
 ("Does Slack match the redirect URL exactly, or by prefix?",
  "By prefix, forward from the configured entry, after the scheme, host and port have matched exactly. A configured https://app.example.com/slack covers /slack/callback and /slack/callback/v2 underneath it. It does not cover a different port, it does not cover the http form, and it does not work backwards: a configured path ending in a slash cannot cover the same path without one. The script encodes that asymmetry deliberately, because normalising the slash away on both sides would report a pass on an install that fails."),
 ("It worked for a year and broke the day we added a second environment. Why?",
  "Almost certainly because neither leg of your flow sends redirect_uri. While exactly one Redirect URL is configured Slack can fill in the blank, and while that was true your install worked. Adding a second URL makes the blank ambiguous and every install starts failing, with no deploy and no code change to point at. That is the ambiguous verdict from parameter_symmetry, and the repair is to send the parameter explicitly in both the authorize URL and the exchange."),
 ("We terminate TLS at the load balancer and build the callback from the request. Is that the problem?",
  "It is the single most common cause of a near-miss on the scheme. Inside the perimeter your application sees plain HTTP, so a callback URL built from the inbound request comes out as http://app.example.com/slack/callback and gets held against an allow list containing only the https form. Honouring X-Forwarded-Proto fixes it; putting the callback URL in configuration as a literal string fixes it better, because then the deployed value and the configured value are the same string in two places rather than one string and one derivation."),
 ("The install succeeds and the token stops working later. Same problem?",
  "No, and the boundary is clean. This note covers everything up to the moment oauth.v2.access answers ok: true. A token that expires after twelve hours means rotation is switched on and the refresh is not being done; a refresh that fails once and poisons the pair is the single-use refresh token being replayed. Both are linked below, and neither of them can be caused by a redirect URL, because by the time they happen the redirect URL has already done its job."),
],
"related": [
 ("/slack/config-token-expired/", "the credential this check reads the manifest with"),
 ("/slack/http-200-ok-false/", "why the exchange looks like a success"),
 ("/slack/token-expired-rotation/", "the token's life after the install succeeds"),
],
"citations": [CITE_OAUTH_ACCESS, CITE_INSTALL_OAUTH, CITE_MANIFEST_EXPORT,
              CITE_SO_REDIRECT],
})
GUIDES.append({
"slug": "app-access-restricted",
"title": "app_access_restricted: an admin blocked the app for a user",
"description": "The refusal is a policy on the app and the person, not on your token or your network. Resolve the affected users and find what they have in common.",
"h1": "app_access_restricted: an admin blocked the app for a user",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack app_access_restricted error",
             "slack admin restricted app for user",
             "slack app approval enterprise grid",
             "admin.apps.restricted.list",
             "slack app works for some users not others"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot token with users:read and usergroups:read, and optionally an Enterprise Grid user token with admin.apps:read",
"lead": "The bug report says the app is broken. The dashboard says the app is fine. Both are right: 340 people used it this week and four did not, and the four are all in the same customer's org, and one of them is the person who filed the ticket.</p><p>What they got back was <code>{\"ok\": false, \"error\": \"app_access_restricted\"}</code>, which reads like a scope problem and is not one. Your token is fine. Your scopes are fine. An administrator, at some point after the app was installed, decided that this app may be used by some people and not by others &mdash; and your app was not told, because there is no event for a policy change.",
"short_answer": """<p><code>app_access_restricted</code> means the action was attempted <strong>on behalf of a user</strong> who is not permitted to use this app. Workspace and Grid admins can restrict an app to particular members or groups, and can require app approval before installation on each workspace. Neither decision involves you, neither generates a notification, and both can change on an afternoon.</p>
<p>Because it is a per-user policy, the finding is a <strong>cohort</strong>, not an error string. Collect the user ids that came back refused and the ones that came back fine, resolve both sets with <code>users.info</code>, and look for the attribute the first set holds and the second does not: guest accounts (<code>is_restricted</code> or <code>is_ultra_restricted</code>), a single <code>team_id</code> on Enterprise Grid, or membership of one user group. That attribute is the sentence you send to the admin, and it is the difference between &ldquo;the app is broken&rdquo; and &ldquo;multi-channel guests cannot use this app, here are the four of them.&rdquo;</p>
<p>Two things follow immediately. <strong>Do not retry.</strong> This refusal is a decision, not a condition; the tenth attempt will be refused identically and the only thing repetition adds is rate-limit pressure. And <strong>do not report it as an outage</strong>: catch it, tell that one user their administrator has restricted the app, and carry on serving everybody else.</p>""",
"problem": """<p>The reason this is confusing is that it arrives on the same wire, from the same token, in the same shape as errors that are genuinely yours. <code>missing_scope</code> is your fault and tells you precisely how to fix it. <code>not_in_channel</code> is your fault and tells you which room to join. <code>app_access_restricted</code> is not your fault, cannot be fixed by you, and tells you nothing except that somebody, somewhere, said no.</p>
<p>It is also intermittent in a way that defeats the usual instincts. The app works. It works for the overwhelming majority of calls. Retry logic makes no difference, so the failure is not transient; but it is not universal either, so it does not look like a broken credential. Teams commonly spend a day checking scopes, because a scope problem is the failure that looks most like this from a distance, and the scope list comes back correct every time.</p>
<p>There are three policies hiding behind one error string. The first is <strong>app management restrictions</strong>: an admin has limited which members may use apps, or this app specifically, and typically guests are outside the permitted set. The second is <strong>app approval</strong>: on a workspace that requires approval, an app that has not been approved &mdash; or has been explicitly restricted &mdash; is unavailable to everyone on it, which on Enterprise Grid can mean one workspace in a Grid of forty. The third is a narrower grant: the app was allowed for one department's user group and your new caller is not in it.</p>
<p>And it is worth being exact about what this is <em>not</em>, because there is a neighbouring error that produces an almost identical support conversation. <code>accesslimited</code> is a policy about <strong>where the call came from</strong>: an org has an IP allow list, your servers are outside it, and every call fails regardless of which user it acts for. <code>app_access_restricted</code> is a policy about <strong>who the call acts for</strong>: the network is irrelevant, and the same server calling for a different user succeeds. One is fixed by an allow list entry, the other by a permission grant, and they are handled by different people at the customer.</p>""",
"why": """<p><strong>A single error is not a finding here; a cohort is.</strong> One refusal tells you almost nothing, because a per-user policy looks like bad luck at n=1. Two sets &mdash; refused and served &mdash; held against each other tell you the rule. That is why the script takes records rather than a single error, and why it insists on a control group: without users who succeeded, &ldquo;all affected users are guests&rdquo; might simply mean everybody in the sample is a guest.</p>
<p><strong>The attribute is the message to the administrator.</strong> Nobody can act on &ldquo;the app is restricted.&rdquo; An admin can act immediately on &ldquo;these four accounts are multi-channel guests and the app is restricted to full members,&rdquo; or on &ldquo;every refusal is from workspace T04XYZ, where the app has not been approved.&rdquo; The script exists to turn the first sentence into the second.</p>
<p><strong>Retrying cannot work, and the code has to know that.</strong> A generic error handler that backs off and tries again will burn a rate-limit budget re-asking a question that has already been answered. Worse, it turns an instant, explainable refusal into a slow one. The correct behaviour is to catch this specific error, degrade for that user, and not touch it again until the policy changes.</p>
<p><strong>The Grid admin methods answer directly, and most callers do not have them.</strong> <code>admin.apps.approved.list</code> and <code>admin.apps.restricted.list</code> report the app's status per workspace and settle the question in one read. They need <code>admin.apps:read</code> on an Enterprise Grid user token, which a runtime bot token is not. So the script uses them when they are available and reaches the same conclusion from the cohort when they are not, rather than refusing to run.</p>
<p><strong>This is a different axis from the token and from the network, and the output says so.</strong> The script classifies whichever errors it is given onto four axes &mdash; the app policy, the network origin, the token's scopes, and channel membership &mdash; because a records file collected from production will contain more than one kind of refusal, and quietly counting them all as this note would produce a confident, wrong cohort.</p>
<p><strong>No user data leaves the script.</strong> It reads profiles to compare flags and prints ids, display names and the flag that mattered. Email addresses are never read or printed, and the profile blob is never dumped.</p>""",
"steps": [
 {"h": "Sort the records onto the four axes first",
  "body": """<p><code>refusal_axis</code> maps an error to <code>app-policy</code>, <code>network</code>, <code>token</code>, <code>membership</code> or <code>other</code>, and says whether retrying can ever succeed. Run this before anything else: a production log contains several kinds of refusal, and building a cohort out of all of them finds a pattern that is not there.</p>"""},
 {"h": "Split the callers into refused and served",
  "body": """<p><code>split_cohorts</code> reads the records and returns two sets of user ids. A record with <code>ok: true</code> is as important as a refusal, because the control group is what makes the shared attribute meaningful; if you have no successful calls recorded, the script says so and stops short of the conclusion.</p>"""},
 {"h": "Resolve both sets and find what only one of them shares",
  "body": """<p><code>shared_attribute</code> holds the two cohorts against each other and answers <code>guest-accounts</code>, <code>one-workspace</code>, <code>single-user</code>, <code>no-control</code>, <code>no-common-attribute</code> or <code>no-evidence</code>. It only reports an attribute that <em>every</em> refused user has and <em>no</em> served user has, which is what stops it inventing a rule out of a coincidence.</p>"""},
 {"h": "Check the user groups, because that is the third policy shape",
  "body": """<p><code>usergroup_overlap</code> takes the user groups and their members and returns any group that contains every refused user and no served one. A grant made to a department's group is invisible in a profile, so this is the check that catches &ldquo;the app was allowed for Engineering and Support was never added.&rdquo;</p>"""},
 {"h": "Ask Grid directly, if the token you have can",
  "body": """<p><code>approval_state</code> reads <code>admin.apps.approved.list</code> and <code>admin.apps.restricted.list</code> and answers <code>restricted</code>, <code>approved</code>, <code>unlisted</code> or <code>unavailable</code>, per workspace. This needs an Enterprise Grid user token with <code>admin.apps:read</code>. When it is available it is the shortest path to the answer; when it is not, the cohort has already told you.</p>"""},
 {"h": "Degrade for that user instead of failing the request",
  "body": """<p>The repair the script prints has two halves. The admin's half is a grant: add the users or the group under <strong>Manage apps &rarr; the app &rarr; permissions</strong>, or approve the app on the workspace. Your half is a code change: catch this error by name, tell that one person their administrator has restricted the app, do not retry, and do not raise it as an incident.</p>"""},
],
"verify": """<p>Once the grant is made, re-run against a fresh set of records. The cohort should be empty and the axis line should be the only one left.</p>
<pre><code class="language-bash">python3 slack_app_restriction.py --records calls.json --app-id A05NW7XQ1
# axis       app-policy     4 record(s): a policy on the app and the person, not on
#                           your token; retrying cannot succeed
# axis       token          1 record(s): missing_scope, which is a different note
# cohort     refused        4 user(s), served 61 user(s)
# profile    U08GUEST1      Dana Okafor        is_ultra_restricted
# profile    U08GUEST2      Sam Reyes          is_ultra_restricted
# profile    U08GUEST3      Wei Zhang          is_ultra_restricted
# profile    U08GUEST4      Priya Nair         is_ultra_restricted
# shared     guest-accounts every refused caller is a guest account and no served
#                           caller is; the app is restricted to full members
# usergroup  none           no single user group separates the two cohorts
# approval   unavailable    set SLACK_ADMIN_TOKEN to an Enterprise Grid user token
#                           with admin.apps:read to read the app status per workspace
# verdict    1 finding(s)
#   repair: ask an admin to permit these 4 account(s), or the group they belong to,
#           under Manage apps -> this app -> permissions
#   repair: catch app_access_restricted by name, tell that user their admin has
#           restricted the app, and do not retry</code></pre>""",
"code_intro": "The reads are ordinary and the reasoning is the interesting part. <code>refusal_axis</code> keeps the other refusals out of the cohort. <code>split_cohorts</code> insists on a control group. <code>shared_attribute</code> will only report an attribute held by every refused caller and no served one, which is the rule that stops it turning a coincidence into a policy. <code>usergroup_overlap</code> covers the case a profile cannot show. <code>approval_state</code> is the shortcut for the callers who happen to hold a Grid admin token, and everything works without it.",
"py_file": "slack_app_restriction.py",
"py": '''"""Explain app_access_restricted by naming the people it happens to.

Read only. Four GET methods are used: users.info to resolve the callers,
usergroups.list and usergroups.users.list to test the group shape, and the two
Enterprise Grid admin listings when a token that can read them is available.
Nothing is written, no app is installed, approved or requested, and no email
address is read or printed.

The input is a records file: the calls your application already made, each with
the user it acted for and what came back. That is deliberate. This error is a
per-user policy, so a single instance proves nothing and the two cohorts prove
everything.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_app_restriction")

API = "https://slack.com/api/"

# Four different policies wearing four different error names. Sorting first is
# what keeps a records file from producing a cohort that is really a mixture.
AXES = {
    "app_access_restricted": (
        "app-policy", False,
        "a policy on the app and the person, not on your token; retrying cannot "
        "succeed"),
    "accesslimited": (
        "network", False,
        "a policy on where the call came from. Every user fails from this address "
        "and none of them fails from an allowed one. A different note"),
    "missing_scope": (
        "token", False,
        "the token lacks a scope, and Slack names both the one needed and the ones "
        "provided. A different note"),
    "invalid_auth": (
        "token", False,
        "the credential itself is refused, for every user equally"),
    "not_in_channel": (
        "membership", False,
        "the app is not a member of the conversation. Nothing to do with policy"),
    "ratelimited": (
        "transient", True,
        "the only answer here worth retrying"),
}

# The profile flags that make a person a guest. Guests are the group most often
# left outside an app permission grant, and they are visible without any admin
# credential at all.
GUEST_FLAGS = ("is_restricted", "is_ultra_restricted")


def refusal_axis(error):
    """Which policy is this error about? Pure.

    Returns (axis, retryable, detail). Called before the cohort is built so
    that a mixed log does not become a confident, wrong pattern.
    """
    text = str(error or "").strip()
    if not text:
        return ("none", False, "no error was recorded on this call")
    if text in AXES:
        axis, retryable, detail = AXES[text]
        return (axis, retryable, "%s: %s" % (text, detail))
    return ("other", False, "%s is not one of the policy refusals; read it against "
                            "the method reference" % text)


def split_cohorts(records):
    """Sort call records into the users refused and the users served. Pure.

    Returns (refused, served), both sorted lists of user ids. A user who
    appears in both is counted as refused, because a policy that bites
    sometimes is still the policy that bites.
    """
    refused, served = set(), set()
    for rec in records or []:
        user = str((rec or {}).get("user") or "").strip()
        if not user:
            continue
        axis = refusal_axis((rec or {}).get("error"))[0]
        if axis == "app-policy":
            refused.add(user)
        elif (rec or {}).get("ok") is True or axis == "none":
            served.add(user)
    return (sorted(refused), sorted(served - refused))


def shared_attribute(refused_profiles, served_profiles):
    """What do the refused callers share that the served ones do not? Pure.

    Takes two dicts of user id to users.info profile. Returns (code, detail).

      no-evidence         nothing was refused.
      no-control          nothing succeeded, so any attribute the refused
                          callers share might just be what your callers are.
                          The app may be restricted outright.
      guest-accounts      every refused caller is a guest and no served one is.
      one-workspace       every refusal comes from one team_id that no served
                          caller belongs to. The Grid shape.
      single-user         one person, and no rule to infer from one person.
      no-common-attribute the cohorts overlap on every attribute checked, which
                          points at an explicit per-user grant.

    An attribute is only reported when every refused caller has it and no
    served caller does. Anything weaker is a coincidence with a good story.
    """
    refused = {k: (v or {}) for k, v in (refused_profiles or {}).items()}
    served = {k: (v or {}) for k, v in (served_profiles or {}).items()}
    if not refused:
        return ("no-evidence", "no call was refused with app_access_restricted")
    if not served:
        return ("no-control", "%d refused caller(s) and no successful call to compare "
                              "against; the app may be restricted for everyone rather "
                              "than for a subset" % len(refused))

    def is_guest(p):
        return any(bool(p.get(flag)) for flag in GUEST_FLAGS)

    if all(is_guest(p) for p in refused.values()) and \\
            not any(is_guest(p) for p in served.values()):
        return ("guest-accounts", "every refused caller is a guest account and no "
                                  "served caller is; the app is restricted to full "
                                  "members")
    teams = {str(p.get("team_id") or "") for p in refused.values()}
    served_teams = {str(p.get("team_id") or "") for p in served.values()}
    if len(teams) == 1 and teams and "" not in teams and not (teams & served_teams):
        team = sorted(teams)[0]
        return ("one-workspace", "every refusal comes from %s and no served caller is "
                                 "on it; the app is not approved on that workspace"
                % team)
    if len(refused) == 1:
        return ("single-user", "one refused caller, %s, and one person is not a "
                               "pattern; collect more records before naming a rule"
                % sorted(refused)[0])
    return ("no-common-attribute", "%d refused caller(s) share no attribute the %d "
                                   "served callers lack; the grant is probably "
                                   "per-user" % (len(refused), len(served)))


def usergroup_overlap(refused, served, groups):
    """Which user group contains every refused caller and no served one? Pure.

    groups: [{"handle": ..., "users": [...]}, ...]. Returns a list of
    (handle, detail). A grant made to a group leaves no trace in a profile, so
    this is the only way to see the third shape of this policy.
    """
    refused_set, served_set = set(refused or []), set(served or [])
    out = []
    if not refused_set:
        return out
    for group in groups or []:
        members = set((group or {}).get("users") or [])
        if refused_set <= members and not (served_set & members):
            out.append((str((group or {}).get("handle") or "?"),
                        "contains all %d refused caller(s) and none of the served "
                        "ones" % len(refused_set)))
    return out


def approval_state(app_id, approved, restricted):
    """Read the app's status from the two Grid listings. Pure.

    approved / restricted are the lists those methods return, or None when the
    token could not read them. Returns (state, detail).
    """
    if approved is None and restricted is None:
        return ("unavailable", "set an Enterprise Grid user token with "
                               "admin.apps:read to read the app status per workspace")
    wanted = str(app_id or "").strip()

    def teams_for(rows):
        found = []
        for row in rows or []:
            app = ((row or {}).get("app") or {})
            if str(app.get("id") or "") == wanted:
                found.append(str((row or {}).get("scope") or
                                 (row or {}).get("team_id") or "the org"))
        return found

    blocked = teams_for(restricted)
    if blocked:
        return ("restricted", "this app is on the restricted list for %s"
                % ", ".join(blocked))
    allowed = teams_for(approved)
    if allowed:
        return ("approved", "this app is approved for %s, so the refusal is a "
                            "per-user grant rather than an approval" % ", ".join(allowed))
    return ("unlisted", "this app appears on neither list, so on a workspace that "
                        "requires approval it is unavailable to everyone there")


def get(session, method, params=None):
    """One GET against the Web API. Returns the parsed body."""
    r = session.get(API + method, params=params or {}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def resolve(session, user_ids):
    """users.info for each id. Only the flags this check compares are kept."""
    out = {}
    for user in user_ids:
        body = get(session, "users.info", {"user": user})
        if body.get("ok") is not True:
            log.warning("profile    %-14s unavailable    %s", user, body.get("error"))
            out[user] = {}
            continue
        info = body.get("user") or {}
        out[user] = {
            "name": info.get("real_name") or info.get("name") or "",
            "team_id": info.get("team_id") or "",
            "is_restricted": bool(info.get("is_restricted")),
            "is_ultra_restricted": bool(info.get("is_ultra_restricted")),
            "deleted": bool(info.get("deleted")),
        }
    return out


def load_groups(session):
    """usergroups.list, then usergroups.users.list for each. Reads only."""
    body = get(session, "usergroups.list")
    if body.get("ok") is not True:
        log.info("usergroup  unavailable    %s", body.get("error"))
        return []
    groups = []
    for group in body.get("usergroups") or []:
        members = get(session, "usergroups.users.list", {"usergroup": group.get("id")})
        groups.append({"handle": group.get("handle") or group.get("name") or "?",
                       "users": list(members.get("users") or [])})
    return groups


def admin_list(session, method, token):
    """One of the two Grid listings. Returns the rows, or None if unreadable."""
    r = session.get(API + method, headers={"Authorization": "Bearer " + token},
                    params={"limit": "200"}, timeout=30)
    try:
        body = r.json()
    except ValueError:
        return None
    if body.get("ok") is not True:
        log.info("approval   %-14s %s", method.split(".")[2], body.get("error"))
        return None
    return body.get("apps") or []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--records", required=True,
                    help="json file of call records: user, ok and error per call")
    ap.add_argument("--app-id", default="", help="the app id to look for, A...")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a token with users:read")
    ap.add_argument("--admin-token-env", default="SLACK_ADMIN_TOKEN",
                    help="environment variable holding a Grid token with "
                         "admin.apps:read")
    args = ap.parse_args()

    records = json.loads(open(args.records, encoding="utf-8").read())
    counts = {}
    for rec in records:
        axis, _retryable, detail = refusal_axis((rec or {}).get("error"))
        counts.setdefault(axis, [0, detail])
        counts[axis][0] += 1
    for axis in sorted(counts):
        if axis == "none":
            continue
        count, detail = counts[axis]
        log.info("axis       %-14s %d record(s): %s", axis, count, detail)

    refused, served = split_cohorts(records)
    log.info("cohort     refused        %d user(s), served %d user(s)",
             len(refused), len(served))
    if not refused:
        log.info("verdict    clean          nothing in these records was refused by "
                 "an app policy")
        return 0

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s to a token with users:read and usergroups:read",
                  args.token_env)
        return 2
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    refused_profiles = resolve(session, refused)
    served_profiles = resolve(session, served)
    for user in refused:
        p = refused_profiles.get(user) or {}
        flags = ",".join(f for f in GUEST_FLAGS if p.get(f)) or "full member"
        log.warning("profile    %-14s %-18s %s", user, p.get("name") or "?", flags)

    code, detail = shared_attribute(refused_profiles, served_profiles)
    log.warning("shared     %-14s %s", code, detail)

    overlaps = usergroup_overlap(refused, served, load_groups(session))
    if overlaps:
        for handle, why in overlaps:
            log.warning("usergroup  %-14s %s", handle, why)
    else:
        log.info("usergroup  none           no single user group separates the two "
                 "cohorts")

    admin_token = os.environ.get(args.admin_token_env)
    approved = restricted = None
    if admin_token and args.app_id:
        approved = admin_list(session, "admin.apps.approved.list", admin_token)
        restricted = admin_list(session, "admin.apps.restricted.list", admin_token)
    state, why = approval_state(args.app_id, approved, restricted)
    (log.info if state in ("approved", "unavailable") else log.warning)(
        "approval   %-14s %s", state, why)

    log.warning("verdict    1 finding(s)")
    log.warning("  repair: ask an admin to permit these %d account(s), or the group "
                "they belong to, under Manage apps -> this app -> permissions",
                len(refused))
    log.warning("  repair: catch app_access_restricted by name, tell that user their "
                "admin has restricted the app, and do not retry")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-app-restriction.mjs",
"js": '''/**
 * Explain app_access_restricted by naming the people it happens to.
 *
 * Read only. Four GET methods are used: users.info, usergroups.list,
 * usergroups.users.list, and the two Enterprise Grid admin listings when a
 * token that can read them is available. No email address is read or printed.
 *
 * The input is a records file of calls your application already made, because
 * this error is a per-user policy: one instance proves nothing and two cohorts
 * prove everything.
 */

import { readFileSync } from 'node:fs';

const API = 'https://slack.com/api/';

// Four policies wearing four error names. Sorting first is what keeps a
// records file from producing a cohort that is really a mixture.
export const AXES = {
  app_access_restricted: ['app-policy', false,
    'a policy on the app and the person, not on your token; retrying cannot succeed'],
  accesslimited: ['network', false,
    'a policy on where the call came from. Every user fails from this address and '
    + 'none of them fails from an allowed one. A different note'],
  missing_scope: ['token', false,
    'the token lacks a scope, and Slack names both the one needed and the ones '
    + 'provided. A different note'],
  invalid_auth: ['token', false,
    'the credential itself is refused, for every user equally'],
  not_in_channel: ['membership', false,
    'the app is not a member of the conversation. Nothing to do with policy'],
  ratelimited: ['transient', true, 'the only answer here worth retrying'],
};

// The profile flags that make a person a guest, visible without any admin
// credential at all.
export const GUEST_FLAGS = ['is_restricted', 'is_ultra_restricted'];

/** Which policy is this error about? Pure. Returns [axis, retryable, detail]. */
export function refusalAxis(error) {
  const text = String(error ?? '').trim();
  if (!text) return ['none', false, 'no error was recorded on this call'];
  if (Object.prototype.hasOwnProperty.call(AXES, text)) {
    const [axis, retryable, detail] = AXES[text];
    return [axis, retryable, `${text}: ${detail}`];
  }
  return ['other', false,
    `${text} is not one of the policy refusals; read it against the method reference`];
}

/** Sort call records into the users refused and the users served. Pure. */
export function splitCohorts(records) {
  const refused = new Set();
  const served = new Set();
  for (const rec of records ?? []) {
    const user = String((rec ?? {}).user ?? '').trim();
    if (!user) continue;
    const axis = refusalAxis((rec ?? {}).error)[0];
    if (axis === 'app-policy') refused.add(user);
    else if ((rec ?? {}).ok === true || axis === 'none') served.add(user);
  }
  return [[...refused].sort(),
    [...served].filter((u) => !refused.has(u)).sort()];
}

/**
 * What do the refused callers share that the served ones do not? Pure.
 * Returns [code, detail]; no-evidence, no-control, guest-accounts,
 * one-workspace, single-user, no-common-attribute.
 */
export function sharedAttribute(refusedProfiles, servedProfiles) {
  const refused = Object.entries(refusedProfiles ?? {})
    .map(([k, v]) => [k, v ?? {}]);
  const served = Object.entries(servedProfiles ?? {}).map(([k, v]) => [k, v ?? {}]);
  if (!refused.length) {
    return ['no-evidence', 'no call was refused with app_access_restricted'];
  }
  if (!served.length) {
    return ['no-control', `${refused.length} refused caller(s) and no successful call `
      + 'to compare against; the app may be restricted for everyone rather than for a '
      + 'subset'];
  }
  const isGuest = (p) => GUEST_FLAGS.some((flag) => Boolean(p[flag]));
  if (refused.every(([, p]) => isGuest(p)) && !served.some(([, p]) => isGuest(p))) {
    return ['guest-accounts', 'every refused caller is a guest account and no served '
      + 'caller is; the app is restricted to full members'];
  }
  const teams = new Set(refused.map(([, p]) => String(p.team_id ?? '')));
  const servedTeams = new Set(served.map(([, p]) => String(p.team_id ?? '')));
  const team = [...teams][0];
  if (teams.size === 1 && team && !servedTeams.has(team)) {
    return ['one-workspace', `every refusal comes from ${team} and no served caller is `
      + 'on it; the app is not approved on that workspace'];
  }
  if (refused.length === 1) {
    return ['single-user', `one refused caller, ${refused[0][0]}, and one person is `
      + 'not a pattern; collect more records before naming a rule'];
  }
  return ['no-common-attribute', `${refused.length} refused caller(s) share no `
    + `attribute the ${served.length} served callers lack; the grant is probably `
    + 'per-user'];
}

/** Which user group holds every refused caller and no served one? Pure. */
export function usergroupOverlap(refused, served, groups) {
  const refusedSet = new Set(refused ?? []);
  const servedSet = new Set(served ?? []);
  const out = [];
  if (!refusedSet.size) return out;
  for (const group of groups ?? []) {
    const members = new Set((group ?? {}).users ?? []);
    const holdsAll = [...refusedSet].every((u) => members.has(u));
    const holdsNone = ![...servedSet].some((u) => members.has(u));
    if (holdsAll && holdsNone) {
      out.push([String((group ?? {}).handle ?? '?'),
        `contains all ${refusedSet.size} refused caller(s) and none of the served ones`]);
    }
  }
  return out;
}

/** Read the app status from the two Grid listings. Pure. */
export function approvalState(appId, approved, restricted) {
  if (approved === null && restricted === null) {
    return ['unavailable', 'set an Enterprise Grid user token with admin.apps:read to '
      + 'read the app status per workspace'];
  }
  const wanted = String(appId ?? '').trim();
  const teamsFor = (rows) => (rows ?? [])
    .filter((row) => String(((row ?? {}).app ?? {}).id ?? '') === wanted)
    .map((row) => String((row ?? {}).scope ?? (row ?? {}).team_id ?? 'the org'));
  const blocked = teamsFor(restricted);
  if (blocked.length) {
    return ['restricted', `this app is on the restricted list for ${blocked.join(', ')}`];
  }
  const allowed = teamsFor(approved);
  if (allowed.length) {
    return ['approved', `this app is approved for ${allowed.join(', ')}, so the `
      + 'refusal is a per-user grant rather than an approval'];
  }
  return ['unlisted', 'this app appears on neither list, so on a workspace that '
    + 'requires approval it is unavailable to everyone there'];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function get(headers, method, params = {}) {
  const query = new URLSearchParams(params);
  const r = await fetch(`${API}${method}?${query}`, { headers });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function resolve(headers, userIds) {
  const out = {};
  for (const user of userIds) {
    const body = await get(headers, 'users.info', { user });
    if (body.ok !== true) {
      console.warn(`profile    ${user.padEnd(14)} unavailable    ${body.error}`);
      out[user] = {};
      continue;
    }
    const info = body.user ?? {};
    out[user] = {
      name: info.real_name ?? info.name ?? '',
      team_id: info.team_id ?? '',
      is_restricted: Boolean(info.is_restricted),
      is_ultra_restricted: Boolean(info.is_ultra_restricted),
      deleted: Boolean(info.deleted),
    };
  }
  return out;
}

async function loadGroups(headers) {
  const body = await get(headers, 'usergroups.list');
  if (body.ok !== true) {
    console.log(`usergroup  unavailable    ${body.error}`);
    return [];
  }
  const groups = [];
  for (const group of body.usergroups ?? []) {
    const members = await get(headers, 'usergroups.users.list',
      { usergroup: group.id });
    groups.push({
      handle: group.handle ?? group.name ?? '?',
      users: [...(members.users ?? [])],
    });
  }
  return groups;
}

async function adminList(method, token) {
  const r = await fetch(`${API}${method}?limit=200`,
    { headers: { Authorization: `Bearer ${token}` } });
  let body;
  try {
    body = await r.json();
  } catch {
    return null;
  }
  if (body.ok !== true) {
    console.log(`approval   ${method.split('.')[2].padEnd(14)} ${body.error}`);
    return null;
  }
  return body.apps ?? [];
}

async function main() {
  const args = process.argv.slice(2);
  const records = JSON.parse(readFileSync(arg(args, '--records'), 'utf-8'));
  const appId = arg(args, '--app-id');

  const counts = new Map();
  for (const rec of records) {
    const [axis, , detail] = refusalAxis((rec ?? {}).error);
    if (!counts.has(axis)) counts.set(axis, [0, detail]);
    counts.get(axis)[0] += 1;
  }
  for (const axis of [...counts.keys()].sort()) {
    if (axis === 'none') continue;
    const [count, detail] = counts.get(axis);
    console.log(`axis       ${axis.padEnd(14)} ${count} record(s): ${detail}`);
  }

  const [refused, served] = splitCohorts(records);
  console.log(`cohort     refused        ${refused.length} user(s), served `
    + `${served.length} user(s)`);
  if (!refused.length) {
    console.log('verdict    clean          nothing in these records was refused by an '
      + 'app policy');
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} to a token with users:read and usergroups:read`);
    process.exitCode = 2;
    return;
  }
  const headers = { Authorization: `Bearer ${token}` };

  const refusedProfiles = await resolve(headers, refused);
  const servedProfiles = await resolve(headers, served);
  for (const user of refused) {
    const p = refusedProfiles[user] ?? {};
    const flags = GUEST_FLAGS.filter((f) => p[f]).join(',') || 'full member';
    console.warn(`profile    ${user.padEnd(14)} ${String(p.name || '?').padEnd(18)} `
      + `${flags}`);
  }

  const [code, detail] = sharedAttribute(refusedProfiles, servedProfiles);
  console.warn(`shared     ${code.padEnd(14)} ${detail}`);

  const overlaps = usergroupOverlap(refused, served, await loadGroups(headers));
  if (overlaps.length) {
    for (const [handle, why] of overlaps) {
      console.warn(`usergroup  ${handle.padEnd(14)} ${why}`);
    }
  } else {
    console.log('usergroup  none           no single user group separates the two '
      + 'cohorts');
  }

  const adminToken = process.env[arg(args, '--admin-token-env', 'SLACK_ADMIN_TOKEN')];
  let approved = null;
  let restricted = null;
  if (adminToken && appId) {
    approved = await adminList('admin.apps.approved.list', adminToken);
    restricted = await adminList('admin.apps.restricted.list', adminToken);
  }
  const [state, why] = approvalState(appId, approved, restricted);
  console.log(`approval   ${state.padEnd(14)} ${why}`);

  console.warn('verdict    1 finding(s)');
  console.warn(`  repair: ask an admin to permit these ${refused.length} account(s), `
    + 'or the group they belong to, under Manage apps -> this app -> permissions');
  console.warn('  repair: catch app_access_restricted by name, tell that user their '
    + 'admin has restricted the app, and do not retry');
  process.exitCode = 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions to read are the ones about restraint, because the whole risk in a cohort check is inventing a rule from a coincidence. <code>shared_attribute</code> is tested for the case where a served caller is also a guest &mdash; which makes &ldquo;guests are excluded&rdquo; false, and the function has to say so rather than report the attribute anyway &mdash; and for the case where nothing succeeded, where the honest answer is that there is no control group. <code>refusal_axis</code> is tested to keep <code>accesslimited</code> out of the cohort entirely, since a network policy and an app policy produce the same shrug from a user and different work for the customer.",
"test_py_file": "test_slack_app_restriction.py",
"test_py": '''from slack_app_restriction import (
    approval_state, refusal_axis, shared_attribute, split_cohorts, usergroup_overlap,
)

GUEST = {"name": "Dana", "team_id": "T1", "is_ultra_restricted": True}
MEMBER = {"name": "Sam", "team_id": "T1"}
OTHER_TEAM = {"name": "Wei", "team_id": "T2"}


def test_the_app_policy_error_is_on_its_own_axis():
    axis, retryable, detail = refusal_axis("app_access_restricted")
    assert axis == "app-policy"
    assert retryable is False
    assert "not on your token" in detail


def test_a_network_policy_is_a_different_axis_and_says_so():
    axis, _retryable, detail = refusal_axis("accesslimited")
    assert axis == "network"
    assert "where the call came from" in detail


def test_a_scope_error_is_not_swept_into_the_cohort():
    assert refusal_axis("missing_scope")[0] == "token"
    assert refusal_axis("not_in_channel")[0] == "membership"


def test_only_ratelimited_is_worth_retrying():
    assert refusal_axis("ratelimited")[1] is True
    for err in ("app_access_restricted", "accesslimited", "missing_scope",
                "invalid_auth", "not_in_channel"):
        assert refusal_axis(err)[1] is False


def test_the_cohorts_come_only_from_the_app_policy_error():
    records = [{"user": "U1", "error": "app_access_restricted"},
               {"user": "U2", "error": "accesslimited"},
               {"user": "U3", "ok": True}]
    refused, served = split_cohorts(records)
    assert refused == ["U1"]
    assert served == ["U3"]


def test_a_user_refused_once_counts_as_refused_even_if_served_elsewhere():
    records = [{"user": "U1", "ok": True},
               {"user": "U1", "error": "app_access_restricted"}]
    refused, served = split_cohorts(records)
    assert refused == ["U1"]
    assert served == []


def test_guests_refused_and_members_served_names_the_rule():
    code, detail = shared_attribute({"U1": GUEST, "U2": GUEST}, {"U3": MEMBER})
    assert code == "guest-accounts"
    assert "full members" in detail


def test_a_served_guest_disproves_the_guest_rule():
    code, _detail = shared_attribute({"U1": GUEST, "U2": GUEST},
                                     {"U3": GUEST, "U4": MEMBER})
    assert code != "guest-accounts"


def test_one_workspace_is_the_grid_shape():
    code, detail = shared_attribute({"U1": OTHER_TEAM, "U2": OTHER_TEAM},
                                    {"U3": MEMBER})
    assert code == "one-workspace"
    assert "T2" in detail


def test_no_successful_call_means_there_is_no_control_group():
    code, detail = shared_attribute({"U1": GUEST}, {})
    assert code == "no-control"
    assert "restricted for everyone" in detail


def test_one_refused_user_is_not_a_pattern():
    assert shared_attribute({"U1": MEMBER}, {"U3": MEMBER})[0] == "single-user"


def test_cohorts_that_look_alike_report_a_per_user_grant():
    code, _detail = shared_attribute({"U1": MEMBER, "U2": MEMBER}, {"U3": MEMBER})
    assert code == "no-common-attribute"


def test_nothing_refused_is_no_evidence_rather_than_a_clean_bill():
    assert shared_attribute({}, {"U3": MEMBER})[0] == "no-evidence"


def test_a_group_holding_every_refused_caller_and_no_other_is_reported():
    groups = [{"handle": "support", "users": ["U1", "U2"]},
              {"handle": "everyone", "users": ["U1", "U2", "U3"]}]
    found = usergroup_overlap(["U1", "U2"], ["U3"], groups)
    assert [h for h, _w in found] == ["support"]


def test_a_group_with_no_refused_callers_is_not_reported():
    assert usergroup_overlap(["U1"], ["U3"], [{"handle": "x", "users": ["U9"]}]) == []


def test_the_restricted_listing_settles_it_when_it_is_available():
    state, detail = approval_state("A1", [], [{"app": {"id": "A1"}, "scope": "T2"}])
    assert state == "restricted"
    assert "T2" in detail


def test_an_approved_app_points_back_at_a_per_user_grant():
    state, detail = approval_state("A1", [{"app": {"id": "A1"}, "scope": "T1"}], [])
    assert state == "approved"
    assert "per-user grant" in detail


def test_an_app_on_neither_list_is_unlisted_not_approved():
    assert approval_state("A1", [], [])[0] == "unlisted"


def test_without_an_admin_token_the_check_says_so_rather_than_guessing():
    state, detail = approval_state("A1", None, None)
    assert state == "unavailable"
    assert "admin.apps:read" in detail
''',
"test_js_file": "slack-app-restriction.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  approvalState, refusalAxis, sharedAttribute, splitCohorts, usergroupOverlap,
} from './slack-app-restriction.mjs';

const GUEST = { name: 'Dana', team_id: 'T1', is_ultra_restricted: true };
const MEMBER = { name: 'Sam', team_id: 'T1' };
const OTHER_TEAM = { name: 'Wei', team_id: 'T2' };

test('the app policy error is on its own axis', () => {
  const [axis, retryable, detail] = refusalAxis('app_access_restricted');
  assert.equal(axis, 'app-policy');
  assert.equal(retryable, false);
  assert.match(detail, /not on your token/);
});

test('a network policy is a different axis and says so', () => {
  const [axis, , detail] = refusalAxis('accesslimited');
  assert.equal(axis, 'network');
  assert.match(detail, /where the call came from/);
});

test('a scope error is not swept into the cohort', () => {
  assert.equal(refusalAxis('missing_scope')[0], 'token');
  assert.equal(refusalAxis('not_in_channel')[0], 'membership');
});

test('only ratelimited is worth retrying', () => {
  assert.equal(refusalAxis('ratelimited')[1], true);
  for (const err of ['app_access_restricted', 'accesslimited', 'missing_scope',
    'invalid_auth', 'not_in_channel']) {
    assert.equal(refusalAxis(err)[1], false);
  }
});

test('the cohorts come only from the app policy error', () => {
  const records = [{ user: 'U1', error: 'app_access_restricted' },
    { user: 'U2', error: 'accesslimited' },
    { user: 'U3', ok: true }];
  const [refused, served] = splitCohorts(records);
  assert.deepEqual(refused, ['U1']);
  assert.deepEqual(served, ['U3']);
});

test('a user refused once counts as refused even if served elsewhere', () => {
  const records = [{ user: 'U1', ok: true },
    { user: 'U1', error: 'app_access_restricted' }];
  const [refused, served] = splitCohorts(records);
  assert.deepEqual(refused, ['U1']);
  assert.deepEqual(served, []);
});

test('guests refused and members served names the rule', () => {
  const [code, detail] = sharedAttribute({ U1: GUEST, U2: GUEST }, { U3: MEMBER });
  assert.equal(code, 'guest-accounts');
  assert.match(detail, /full members/);
});

test('a served guest disproves the guest rule', () => {
  const [code] = sharedAttribute({ U1: GUEST, U2: GUEST },
    { U3: GUEST, U4: MEMBER });
  assert.notEqual(code, 'guest-accounts');
});

test('one workspace is the grid shape', () => {
  const [code, detail] = sharedAttribute({ U1: OTHER_TEAM, U2: OTHER_TEAM },
    { U3: MEMBER });
  assert.equal(code, 'one-workspace');
  assert.match(detail, /T2/);
});

test('no successful call means there is no control group', () => {
  const [code, detail] = sharedAttribute({ U1: GUEST }, {});
  assert.equal(code, 'no-control');
  assert.match(detail, /restricted for everyone/);
});

test('one refused user is not a pattern', () => {
  assert.equal(sharedAttribute({ U1: MEMBER }, { U3: MEMBER })[0], 'single-user');
});

test('cohorts that look alike report a per user grant', () => {
  const [code] = sharedAttribute({ U1: MEMBER, U2: MEMBER }, { U3: MEMBER });
  assert.equal(code, 'no-common-attribute');
});

test('nothing refused is no evidence rather than a clean bill', () => {
  assert.equal(sharedAttribute({}, { U3: MEMBER })[0], 'no-evidence');
});

test('a group holding every refused caller and no other is reported', () => {
  const groups = [{ handle: 'support', users: ['U1', 'U2'] },
    { handle: 'everyone', users: ['U1', 'U2', 'U3'] }];
  const found = usergroupOverlap(['U1', 'U2'], ['U3'], groups);
  assert.deepEqual(found.map(([h]) => h), ['support']);
});

test('a group with no refused callers is not reported', () => {
  assert.deepEqual(usergroupOverlap(['U1'], ['U3'],
    [{ handle: 'x', users: ['U9'] }]), []);
});

test('the restricted listing settles it when it is available', () => {
  const [state, detail] = approvalState('A1', [],
    [{ app: { id: 'A1' }, scope: 'T2' }]);
  assert.equal(state, 'restricted');
  assert.match(detail, /T2/);
});

test('an approved app points back at a per user grant', () => {
  const [state, detail] = approvalState('A1', [{ app: { id: 'A1' }, scope: 'T1' }], []);
  assert.equal(state, 'approved');
  assert.match(detail, /per-user grant/);
});

test('an app on neither list is unlisted not approved', () => {
  assert.equal(approvalState('A1', [], [])[0], 'unlisted');
});

test('without an admin token the check says so rather than guessing', () => {
  const [state, detail] = approvalState('A1', null, null);
  assert.equal(state, 'unavailable');
  assert.match(detail, /admin\\.apps:read/);
});
''',
"faq": [
 ("How is this different from accesslimited?",
  "They are policies on different axes and they are fixed by different people. accesslimited is about the origin of the call: the org has an IP allow list and your servers are outside it, so every call fails, for every user, until the network is allowed. app_access_restricted is about the person the call acts for: the same server, on the same network, succeeds for a colleague and fails for this user. If your refusals are universal, look at the network. If they are a subset, look at the people, which is what the cohort in this script does."),
 ("Should we retry, or back off and retry later?",
  "Neither. This is a decision rather than a condition, and the tenth attempt is refused exactly like the first. A retry loop here spends your rate-limit budget re-asking a settled question and turns an instant, explainable refusal into a slow one. Catch the error by name, degrade for that one user with a message that says their administrator has restricted the app, and carry on with everybody else."),
 ("We do not have a Grid admin token. Can we still diagnose it?",
  "Yes, and that is why the admin listings are the last step rather than the first. admin.apps.approved.list and admin.apps.restricted.list answer directly but need admin.apps:read on an Enterprise Grid user token, which a runtime bot token is not. Everything before them runs on users:read and usergroups:read: the refused and served cohorts, the profile flags, and the user groups. The cohort will usually name the rule on its own."),
 ("It works in our workspace and fails entirely in one customer's org. What is that?",
  "Most likely app approval rather than a per-user grant. A workspace can require that apps are approved before use, and on Enterprise Grid approval is per workspace, so one workspace in a Grid of forty can be the only place your app is unavailable. The cohort reports that shape as one-workspace: every refusal shares a team_id that no served caller has. The repair is an approval request, not a permission edit."),
 ("Could this be a missing scope wearing a different name?",
  "No, and the two are easy to tell apart because Slack is unusually specific about scopes. A scope failure returns missing_scope and names both the scope needed and the scopes provided, which is enough to fix it without any investigation. app_access_restricted names nothing, because there is nothing about your app to name. That is exactly why the script sorts errors onto axes before it builds a cohort: a records file with both in it would otherwise produce a pattern made of two different problems."),
],
"related": [
 ("/slack/accesslimited-ip-allowlist/", "the same shrug, decided by the network instead"),
 ("/slack/missing-scope-on-read/", "the refusal that is genuinely yours to fix"),
 ("/slack/bot-not-in-channel/", "the refusal about the room rather than the person"),
],
"citations": [CITE_ADMIN_RESTRICTED, CITE_ADMIN_APPROVED, CITE_USERS_INFO,
              CITE_POST_MESSAGE],
})
GUIDES.append({
"slug": "messages-tab-disabled",
"title": "messages_tab_disabled: the App Home DM surface is off",
"description": "The Messages tab is off by default and a second checkbox makes it read only. Read both flags, and the message.im subscription that has to accompany them.",
"h1": "messages_tab_disabled: the App Home DM surface is off",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack messages_tab_disabled error",
             "slack app home messages tab enable",
             "slack bot cannot receive dm",
             "you cannot reply to this conversation slack bot",
             "messages_tab_read_only_enabled manifest"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token with app_configurations:read for the manifest, and a bot token with im:read and im:history for the corroboration",
"lead": "The onboarding flow is a conversation. The app DMs a new hire, asks four questions, and files the answers. It works beautifully in the demo, because the demo was recorded in the workspace where the app was first built and somebody clicked something there eighteen months ago.</p><p>In the customer's workspace it fails at the first message with <code>{\"ok\": false, \"error\": \"messages_tab_disabled\"}</code>, or it succeeds and then nothing comes back, because the person on the other end is looking at a greyed-out composer that says they cannot reply to this conversation. The bot has a DM surface. It is switched off, it was switched off by default the day the app was created, and nothing in the code has any way of knowing.",
"short_answer": """<p>App Home has three tabs &mdash; Home, Messages and About &mdash; and <strong>the Messages tab is off by default</strong>. It is enabled under <strong>App Home &rarr; Show Tabs</strong>, and a second, separate checkbox controls whether people may type back. That gives three configurations that look identical from the outside and behave completely differently: no tab at all, a tab that reads like a broadcast channel, and a tab that is a conversation.</p>
<p>There is a third setting, and it is the one that catches teams who have already found the first two. Turning the tab on does not deliver anything. Replies reach your app only if <code>message.im</code> is in the event subscriptions and the bot token holds <code>im:history</code>. Enable the tab, uncheck read-only, and forget the subscription, and you get the worst version of this: users can type, they do type, and their messages go nowhere at all.</p>
<p>All three live in the app manifest, under <code>features.app_home</code> and <code>settings.event_subscriptions.bot_events</code>, so a single export settles it. The workspace corroborates without any configuration credential at all: list the app's IM conversations, read their history, and if every message in every DM was written by the app and none by a person, you are looking at a one-way surface.</p>""",
"problem": """<p>The trap in this one is that the default is silence rather than an error. A brand new Slack app can post into channels the moment it is installed, so the first hour of building one teaches you that things work. The DM surface is the exception: it exists, it is visible to users, it appears in the sidebar under Apps, and it is inert until somebody opts in. Nothing in the app creation flow mentions it, and the code you write is identical either way.</p>
<p>The error itself only shows up on one of the three failure shapes. <code>messages_tab_disabled</code> comes back when the app tries to post into a DM with the tab switched off. With the tab on and read-only left checked, your outbound messages succeed perfectly &mdash; <code>ok: true</code>, a real <code>ts</code>, a message the user can see &mdash; and the failure is entirely on their side, where the composer is disabled and there is no error for anyone to read. Your logs are clean. The feature does not work.</p>
<p>The third shape is the cruellest, because everything visible is correct. Tab on, read-only off, users typing away, and no <code>message.im</code> in the subscription list. Slack accepts the message, shows it in the thread, and delivers it to nobody. From the user's chair the bot is ignoring them. From your chair the app is healthy and idle. The only way to see the gap is to hold the surface configuration against the event configuration, which are two different pages in the app settings and two different objects in the manifest.</p>
<p>And it is workspace-independent in a way that surprises people: this is app configuration, not workspace configuration, so it is the same for every install. If it is off, it is off for everyone who ever installs the app, including the customer who is about to renew. It also survives a reinstall, because a reinstall changes scopes and tokens, not surfaces.</p>""",
"why": """<p><strong>Three settings have to agree, and no single one of them is the answer.</strong> A check that reports &ldquo;the Messages tab is disabled&rdquo; and stops will send somebody to flip one switch, watch users start typing, and file a second ticket a week later when the replies still go nowhere. So the script reads the pair of App Home flags and the event subscription together, and reports every one of them that is out of step in a single pass.</p>
<p><strong>The read-only case has no error at all, so it must be read from configuration.</strong> This is the one shape that cannot be found by instrumenting your code, because your code succeeds. <code>messages_tab_read_only_enabled</code> is a boolean in the manifest and a checkbox in the console, and it is the entire explanation for &ldquo;the bot talks and nobody can answer&rdquo;.</p>
<p><strong>The workspace can corroborate without any configuration credential.</strong> Most people running this script have a bot token and no app configuration token. So the second half of the check reads IM conversations and their history and classifies the traffic: <code>two-way</code>, <code>outbound-only</code>, <code>silent</code> or <code>no-im-conversations</code>. <code>outbound-only</code> across many DMs over a long window is a strong signal on its own, and it is available to everybody.</p>
<p><strong>Configuration and behaviour are reported separately, then combined.</strong> They can disagree, and when they do the disagreement is informative. A correctly configured surface with nothing but outbound traffic is not this note &mdash; it means the surface is fine and the handler is not answering &mdash; and the script says exactly that instead of blaming a switch that is already on.</p>
<p><strong>The repair is printed as manifest keys, not as a click path.</strong> A checkbox flipped in a web console exists in one place, is invisible to review, and is the reason this can regress silently on a second app created next quarter. The script prints the exact manifest lines to set, because a surface declared in a file that lives in your repository is a surface that stays declared.</p>
<p><strong>This is not the note about opening a DM.</strong> If your app has never had a conversation with a user at all, the question may be that no IM channel was ever opened, which is a different failure with a different error. This note is about the surface being switched off once the conversation exists.</p>""",
"steps": [
 {"h": "Export the manifest, or run on behaviour alone",
  "body": """<p><code>apps.manifest.export</code> returns <code>features.app_home</code> and <code>settings.event_subscriptions</code>. It needs an app configuration token, which is a different credential class from your bot token. Without one the script skips straight to the DM traffic, which is the half most readers can run.</p>"""},
 {"h": "Read all three settings at once",
  "body": """<p><code>app_home_findings</code> returns every code that applies: <code>messages-tab-off</code>, <code>messages-tab-read-only</code>, <code>no-message-im-subscription</code> and <code>no-im-history-scope</code>. It returns a list rather than a verdict on purpose, because these co-occur and fixing one of them is how a team ends up filing this ticket twice.</p>"""},
 {"h": "Classify the DM traffic in the workspace",
  "body": """<p><code>dm_shape</code> takes the IM conversations and their messages and answers <code>two-way</code>, <code>outbound-only</code>, <code>silent</code> or <code>no-im-conversations</code>. Counted across conversations rather than within one, because a single quiet DM proves nothing and forty DMs in which no human has ever typed proves a great deal.</p>"""},
 {"h": "Hold the configuration against the behaviour",
  "body": """<p><code>tab_verdict</code> combines the two halves and is allowed to disagree with either. Its most useful answer is <code>config-clean</code>: the surface is set up correctly, the traffic is still one-way, and therefore the problem is in your handler rather than in your app configuration. That is the verdict that stops somebody flipping switches that are already on.</p>"""},
 {"h": "Subscribe to the event, not just the surface",
  "body": """<p>The composer and the delivery path are separate settings on separate pages. <code>message.im</code> under Event Subscriptions and <code>im:history</code> in the bot scopes are what turn a user's reply into a request to your app. Adding scopes requires a reinstall, which is worth planning for rather than discovering.</p>"""},
 {"h": "Write the three settings into the manifest",
  "body": """<p><code>repair_manifest</code> prints the exact keys: <code>features.app_home.messages_tab_enabled: true</code>, <code>messages_tab_read_only_enabled: false</code>, and <code>message.im</code> in <code>settings.event_subscriptions.bot_events</code>. Put them in the manifest in your repository so the next app you create starts with a DM surface that works.</p>"""},
],
"verify": """<p>Flip the switches, reinstall if the scope changed, and run it again after a few real conversations. <code>dm_shape</code> should move from <code>outbound-only</code> to <code>two-way</code>.</p>
<pre><code class="language-bash">python3 slack_app_home_messages.py --app-id A05NW7XQ1 --max-conversations 40
# manifest   ok             features.app_home read for A05NW7XQ1
# config     messages-tab-off        the Messages tab is off, which is the default;
#                                    the app cannot post into a DM at all
# config     no-message-im-subscription
#                                    message.im is not subscribed, so a reply typed
#                                    by a user is delivered nowhere
# config     no-im-history-scope     im:history is not in the bot scopes, so the
#                                    subscription could not deliver even if added
# im         37 conversation(s)      1,204 message(s) read
# traffic    outbound-only           37 DM(s), 1,204 message(s) from the app and 0
#                                    from a person
# verdict    tab-off                 configuration and traffic agree
# repair: features.app_home.messages_tab_enabled: true
# repair: features.app_home.messages_tab_read_only_enabled: false
# repair: settings.event_subscriptions.bot_events: add message.im
# repair: oauth_config.scopes.bot: add im:history, then reinstall the app</code></pre>""",
"code_intro": "The manifest half and the workspace half are deliberately independent, and either one runs without the other. <code>app_home_findings</code> returns a list because the three settings co-occur and a check that reported only the first would send you back here in a week. <code>dm_shape</code> counts across conversations rather than inside one. <code>tab_verdict</code> is where they meet, and its job is as much to say <em>this is not the problem</em> as to confirm that it is. <code>repair_manifest</code> turns whatever was found into the manifest lines that fix it.",
"py_file": "slack_app_home_messages.py",
"py": '''"""Decide whether your app has a working DM surface, from both sides.

Read only. Up to three GET methods are used: apps.manifest.export with an app
configuration token for the App Home flags, and conversations.list and
conversations.history with a bot token for the traffic. Nothing is written, no
DM is opened, and no setting is changed - the repair is printed as manifest
keys for you to apply.

Either half runs without the other. Most people have a bot token and no app
configuration token, so the traffic classification is written to stand alone.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_app_home_messages")

API = "https://slack.com/api/"

# The event that carries a user's reply, and the scope without which the
# subscription cannot deliver it. Both are separate from the tab itself, which
# is the entire reason this note exists.
REPLY_EVENT = "message.im"
REPLY_SCOPE = "im:history"

# What each finding costs, and the manifest key that settles it. Keeping the
# repair next to the finding is what lets the script print manifest lines
# rather than a click path through a web console.
REPAIRS = {
    "messages-tab-off": "features.app_home.messages_tab_enabled: true",
    "messages-tab-read-only": "features.app_home.messages_tab_read_only_enabled: false",
    "no-message-im-subscription":
        "settings.event_subscriptions.bot_events: add message.im",
    "no-im-history-scope":
        "oauth_config.scopes.bot: add im:history, then reinstall the app",
}


def app_home_findings(manifest):
    """Every App Home setting that is out of step, as a list. Pure.

    Returns a list of (code, detail). A list rather than a verdict because
    these co-occur: the tab, the read-only checkbox, the event subscription and
    the scope are four separate switches, and a check that reported only the
    first one found would be answered with "I fixed it and it still does not
    work" a week later.
    """
    if not manifest:
        return [("no-manifest", "no manifest was read, so the switches themselves "
                                "could not be inspected; the traffic below is the "
                                "evidence that does not need a config token")]
    body = manifest.get("manifest") or manifest
    features = (body.get("features") or {}).get("app_home") or {}
    events = ((body.get("settings") or {}).get("event_subscriptions") or {})
    bot_events = set(events.get("bot_events") or [])
    scopes = set(((body.get("oauth_config") or {}).get("scopes") or {}).get("bot") or [])
    out = []
    if not features.get("messages_tab_enabled"):
        out.append(("messages-tab-off", "the Messages tab is off, which is the "
                                        "default; the app cannot post into a DM "
                                        "at all"))
    elif features.get("messages_tab_read_only_enabled"):
        out.append(("messages-tab-read-only", "the tab is on and read only, so the "
                                              "app can post and nobody can answer. "
                                              "This shape produces no error at all"))
    if REPLY_EVENT not in bot_events:
        out.append(("no-message-im-subscription", "message.im is not subscribed, so a "
                                                  "reply typed by a user is delivered "
                                                  "nowhere"))
    if REPLY_SCOPE not in scopes:
        out.append(("no-im-history-scope", "im:history is not in the bot scopes, so "
                                           "the subscription could not deliver even "
                                           "if it were added"))
    return out


def dm_shape(conversations, histories, bot_user_id):
    """What does the app's DM traffic look like? Pure.

    conversations: the im entries from conversations.list.
    histories: {channel_id: [message, ...]}.

    Returns (state, counts). Counted across conversations rather than within
    one, because a single quiet DM proves nothing and forty DMs in which no
    human has ever typed proves a great deal.

      no-im-conversations  the app has no open DMs to look at.
      silent               DMs exist and hold no messages at all.
      outbound-only        every message in every DM was written by the app.
      two-way              at least one person has replied.
    """
    ims = [c for c in (conversations or []) if (c or {}).get("is_im")]
    counts = {"conversations": len(ims), "app_messages": 0, "human_messages": 0}
    if not ims:
        return ("no-im-conversations", counts)
    for conv in ims:
        for m in (histories or {}).get((conv or {}).get("id")) or []:
            author = (m or {}).get("user") or ""
            if (m or {}).get("bot_id") or (bot_user_id and author == bot_user_id):
                counts["app_messages"] += 1
            elif author:
                counts["human_messages"] += 1
    if not counts["app_messages"] and not counts["human_messages"]:
        return ("silent", counts)
    if not counts["human_messages"]:
        return ("outbound-only", counts)
    return ("two-way", counts)


def tab_verdict(codes, shape):
    """Hold the configuration against the behaviour. Pure.

    Returns (verdict, detail). This function is allowed to contradict either
    half, and its most useful answer is config-clean: the surface is set up
    correctly and the traffic is still one-way, so the fault is in the handler
    rather than in any switch. That is the verdict that stops somebody
    enabling a tab that is already enabled.
    """
    found = set(codes or [])
    corroborated = shape in ("outbound-only", "silent")
    if "messages-tab-off" in found:
        return ("tab-off", "configuration and traffic agree" if corroborated else
                "the tab is off in the manifest, and yet a person has replied; read "
                "the manifest again, it may not be this app")
    if "messages-tab-read-only" in found:
        return ("read-only", "the app can post and users see a disabled composer; "
                             "there is no error for either side to log")
    if "no-message-im-subscription" in found or "no-im-history-scope" in found:
        return ("undeliverable", "the surface is open and the delivery path is not; "
                                 "users can type and nothing reaches the app")
    if "no-manifest" in found:
        return ("traffic-only", "the switches were not readable, so this verdict "
                                "rests on the traffic alone")
    if shape == "outbound-only":
        return ("config-clean", "every switch is set correctly and no person has ever "
                                "replied, so the fault is in the handler rather than "
                                "in app configuration")
    if shape == "no-im-conversations":
        return ("no-evidence", "the app has no open DMs, so there is nothing to "
                               "conclude from traffic")
    return ("consistent", "the surface is configured and people are using it")


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


def list_ims(session, limit):
    """conversations.list restricted to IMs. A read."""
    body = get(session, "conversations.list", {"types": "im", "limit": str(limit)})
    if body.get("ok") is not True:
        log.warning("im         unavailable    %s", body.get("error"))
        return []
    return body.get("channels") or []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app-id", default="", help="the app id to export, A...")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_ACCESS_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a bot token with im:read")
    ap.add_argument("--max-conversations", type=int, default=25)
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()

    manifest = {}
    config_token = os.environ.get(args.config_token_env)
    session = requests.Session()
    if args.app_id and config_token:
        body = get(session, "apps.manifest.export", {"app_id": args.app_id},
                   token=config_token)
        if body.get("ok") is not True:
            log.warning("manifest   unavailable    apps.manifest.export answered "
                        "ok: false, error=%s", body.get("error"))
        else:
            manifest = body
            log.info("manifest   ok             features.app_home read for %s",
                     args.app_id)
    else:
        log.info("manifest   skipped        set %s and --app-id to read the switches "
                 "themselves", args.config_token_env)

    findings = app_home_findings(manifest)
    for code, detail in findings:
        (log.info if code == "no-manifest" else log.warning)(
            "config     %-22s %s", code, detail)

    shape, counts = ("no-im-conversations", {})
    token = os.environ.get(args.token_env)
    if token:
        session.headers.update({"Authorization": "Bearer " + token})
        who = get(session, "auth.test")
        if who.get("ok") is not True:
            log.error("auth.test  unavailable    %s", who.get("error"))
            return 2
        ims = list_ims(session, args.max_conversations)
        histories = {}
        for conv in ims[:args.max_conversations]:
            body = get(session, "conversations.history",
                       {"channel": conv.get("id"), "limit": str(args.limit)})
            histories[conv.get("id")] = body.get("messages") or []
        shape, counts = dm_shape(ims, histories, who.get("user_id"))
        log.info("im         %d conversation(s)  %d message(s) read", len(ims),
                 sum(len(v) for v in histories.values()))
        (log.info if shape == "two-way" else log.warning)(
            "traffic    %-22s %s", shape, counts)
    else:
        log.info("traffic    skipped        set %s to a bot token with im:read and "
                 "im:history", args.token_env)

    codes = [c for c, _d in findings]
    verdict, detail = tab_verdict(codes, shape)
    (log.info if verdict in ("consistent", "no-evidence") else log.warning)(
        "verdict    %-22s %s", verdict, detail)
    for line in repair_manifest(codes):
        log.warning("repair: %s", line)
    if verdict in ("consistent", "no-evidence"):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-app-home-messages.mjs",
"js": '''/**
 * Decide whether your app has a working DM surface, from both sides.
 *
 * Read only. Up to three GET methods are used: apps.manifest.export with an
 * app configuration token for the App Home flags, and conversations.list and
 * conversations.history with a bot token for the traffic. Nothing is written,
 * no DM is opened, and no setting is changed - the repair is printed as
 * manifest keys for you to apply.
 *
 * Either half runs without the other.
 */

const API = 'https://slack.com/api/';

// The event that carries a user reply, and the scope without which the
// subscription cannot deliver it. Both separate from the tab itself.
export const REPLY_EVENT = 'message.im';
export const REPLY_SCOPE = 'im:history';

// Keeping the repair next to the finding is what lets the script print
// manifest lines rather than a click path through a web console.
export const REPAIRS = {
  'messages-tab-off': 'features.app_home.messages_tab_enabled: true',
  'messages-tab-read-only':
    'features.app_home.messages_tab_read_only_enabled: false',
  'no-message-im-subscription':
    'settings.event_subscriptions.bot_events: add message.im',
  'no-im-history-scope':
    'oauth_config.scopes.bot: add im:history, then reinstall the app',
};

/** Every App Home setting that is out of step, as a list. Pure. */
export function appHomeFindings(manifest) {
  if (!manifest || !Object.keys(manifest).length) {
    return [['no-manifest', 'no manifest was read, so the switches themselves could '
      + 'not be inspected; the traffic below is the evidence that does not need a '
      + 'config token']];
  }
  const body = manifest.manifest ?? manifest;
  const features = (body.features ?? {}).app_home ?? {};
  const events = (body.settings ?? {}).event_subscriptions ?? {};
  const botEvents = new Set(events.bot_events ?? []);
  const scopes = new Set(((body.oauth_config ?? {}).scopes ?? {}).bot ?? []);
  const out = [];
  if (!features.messages_tab_enabled) {
    out.push(['messages-tab-off', 'the Messages tab is off, which is the default; the '
      + 'app cannot post into a DM at all']);
  } else if (features.messages_tab_read_only_enabled) {
    out.push(['messages-tab-read-only', 'the tab is on and read only, so the app can '
      + 'post and nobody can answer. This shape produces no error at all']);
  }
  if (!botEvents.has(REPLY_EVENT)) {
    out.push(['no-message-im-subscription', 'message.im is not subscribed, so a reply '
      + 'typed by a user is delivered nowhere']);
  }
  if (!scopes.has(REPLY_SCOPE)) {
    out.push(['no-im-history-scope', 'im:history is not in the bot scopes, so the '
      + 'subscription could not deliver even if it were added']);
  }
  return out;
}

/**
 * What does the app DM traffic look like? Pure.
 * Returns [state, counts]; no-im-conversations, silent, outbound-only, two-way.
 */
export function dmShape(conversations, histories, botUserId) {
  const ims = (conversations ?? []).filter((c) => (c ?? {}).is_im);
  const counts = { conversations: ims.length, app_messages: 0, human_messages: 0 };
  if (!ims.length) return ['no-im-conversations', counts];
  for (const conv of ims) {
    for (const m of (histories ?? {})[(conv ?? {}).id] ?? []) {
      const author = (m ?? {}).user ?? '';
      if ((m ?? {}).bot_id || (botUserId && author === botUserId)) {
        counts.app_messages += 1;
      } else if (author) {
        counts.human_messages += 1;
      }
    }
  }
  if (!counts.app_messages && !counts.human_messages) return ['silent', counts];
  if (!counts.human_messages) return ['outbound-only', counts];
  return ['two-way', counts];
}

/** Hold the configuration against the behaviour. Pure. */
export function tabVerdict(codes, shape) {
  const found = new Set(codes ?? []);
  const corroborated = shape === 'outbound-only' || shape === 'silent';
  if (found.has('messages-tab-off')) {
    return ['tab-off', corroborated ? 'configuration and traffic agree'
      : 'the tab is off in the manifest, and yet a person has replied; read the '
        + 'manifest again, it may not be this app'];
  }
  if (found.has('messages-tab-read-only')) {
    return ['read-only', 'the app can post and users see a disabled composer; there '
      + 'is no error for either side to log'];
  }
  if (found.has('no-message-im-subscription') || found.has('no-im-history-scope')) {
    return ['undeliverable', 'the surface is open and the delivery path is not; users '
      + 'can type and nothing reaches the app'];
  }
  if (found.has('no-manifest')) {
    return ['traffic-only', 'the switches were not readable, so this verdict rests on '
      + 'the traffic alone'];
  }
  if (shape === 'outbound-only') {
    return ['config-clean', 'every switch is set correctly and no person has ever '
      + 'replied, so the fault is in the handler rather than in app configuration'];
  }
  if (shape === 'no-im-conversations') {
    return ['no-evidence', 'the app has no open DMs, so there is nothing to conclude '
      + 'from traffic'];
  }
  return ['consistent', 'the surface is configured and people are using it'];
}

/** Turn findings into the exact manifest lines that fix them. Pure. */
export function repairManifest(codes) {
  return (codes ?? []).filter((c) => c in REPAIRS).map((c) => REPAIRS[c]);
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function get(method, params = {}, token = null) {
  const query = new URLSearchParams(params);
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const r = await fetch(`${API}${method}?${query}`, { headers });
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
  const maxConversations = Number(arg(args, '--max-conversations', '25'));
  const limit = arg(args, '--limit', '100');

  let manifest = {};
  const configToken = process.env[configTokenEnv];
  if (appId && configToken) {
    const body = await get('apps.manifest.export', { app_id: appId }, configToken);
    if (body.ok !== true) {
      console.warn('manifest   unavailable    apps.manifest.export answered ok: false, '
        + `error=${body.error}`);
    } else {
      manifest = body;
      console.log(`manifest   ok             features.app_home read for ${appId}`);
    }
  } else {
    console.log(`manifest   skipped        set ${configTokenEnv} and --app-id to read `
      + 'the switches themselves');
  }

  const findings = appHomeFindings(manifest);
  for (const [code, detail] of findings) {
    const line = `config     ${code.padEnd(22)} ${detail}`;
    if (code === 'no-manifest') console.log(line);
    else console.warn(line);
  }

  let shape = 'no-im-conversations';
  let counts = {};
  const token = process.env[tokenEnv];
  if (token) {
    const who = await get('auth.test', {}, token);
    if (who.ok !== true) {
      console.error(`auth.test  unavailable    ${who.error}`);
      process.exitCode = 2;
      return;
    }
    const listed = await get('conversations.list',
      { types: 'im', limit: String(maxConversations) }, token);
    if (listed.ok !== true) {
      console.warn(`im         unavailable    ${listed.error}`);
    }
    const ims = (listed.channels ?? []).slice(0, maxConversations);
    const histories = {};
    let read = 0;
    for (const conv of ims) {
      const body = await get('conversations.history',
        { channel: conv.id, limit: String(limit) }, token);
      histories[conv.id] = body.messages ?? [];
      read += histories[conv.id].length;
    }
    [shape, counts] = dmShape(ims, histories, who.user_id);
    console.log(`im         ${ims.length} conversation(s)  ${read} message(s) read`);
    const line = `traffic    ${shape.padEnd(22)} ${JSON.stringify(counts)}`;
    if (shape === 'two-way') console.log(line);
    else console.warn(line);
  } else {
    console.log(`traffic    skipped        set ${tokenEnv} to a bot token with `
      + 'im:read and im:history');
  }

  const codes = findings.map(([c]) => c);
  const [verdict, detail] = tabVerdict(codes, shape);
  const line = `verdict    ${verdict.padEnd(22)} ${detail}`;
  if (verdict === 'consistent' || verdict === 'no-evidence') console.log(line);
  else console.warn(line);
  for (const repair of repairManifest(codes)) console.warn(`repair: ${repair}`);
  if (verdict !== 'consistent' && verdict !== 'no-evidence') process.exitCode = 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "There are no tokens in these fixtures at all, because nothing in the diagnosis needs one: a manifest fragment and a handful of messages are the entire input. The assertions to look at are the ones that keep the check honest in both directions. The read-only finding is only raised when the tab is actually on, since a disabled tab makes the second checkbox meaningless. And <code>tab_verdict</code> is tested for the case where every switch is correct and the traffic is still one-way, where the right answer is that this note is not your problem.",
"test_py_file": "test_slack_app_home_messages.py",
"test_py": '''from slack_app_home_messages import (
    app_home_findings, dm_shape, repair_manifest, tab_verdict,
)


def manifest(tab=True, read_only=False, events=("message.im",),
             scopes=("im:history",)):
    return {"manifest": {
        "features": {"app_home": {"messages_tab_enabled": tab,
                                  "messages_tab_read_only_enabled": read_only}},
        "settings": {"event_subscriptions": {"bot_events": list(events)}},
        "oauth_config": {"scopes": {"bot": list(scopes)}},
    }}


def codes(m):
    return [c for c, _d in app_home_findings(m)]


def test_a_healthy_configuration_produces_no_findings():
    assert app_home_findings(manifest()) == []


def test_the_tab_being_off_is_named_as_the_default_it_is():
    found = app_home_findings(manifest(tab=False))
    assert found[0][0] == "messages-tab-off"
    assert "default" in found[0][1]


def test_read_only_is_only_raised_when_the_tab_is_actually_on():
    assert "messages-tab-read-only" in codes(manifest(read_only=True))
    assert "messages-tab-read-only" not in codes(manifest(tab=False, read_only=True))


def test_a_missing_subscription_is_reported_alongside_the_tab_not_instead():
    found = codes(manifest(tab=False, events=()))
    assert found == ["messages-tab-off", "no-message-im-subscription"]


def test_a_missing_scope_is_its_own_finding():
    assert "no-im-history-scope" in codes(manifest(scopes=()))


def test_no_manifest_is_a_stated_gap_rather_than_a_clean_bill():
    assert codes({}) == ["no-manifest"]
    assert codes(None) == ["no-manifest"]


def test_dms_where_only_the_app_ever_spoke_are_outbound_only():
    convs = [{"id": "D1", "is_im": True}, {"id": "D2", "is_im": True}]
    hist = {"D1": [{"user": "UBOT"}, {"bot_id": "B1"}], "D2": [{"user": "UBOT"}]}
    state, counts = dm_shape(convs, hist, "UBOT")
    assert state == "outbound-only"
    assert counts == {"conversations": 2, "app_messages": 3, "human_messages": 0}


def test_one_human_reply_anywhere_makes_it_two_way():
    convs = [{"id": "D1", "is_im": True}, {"id": "D2", "is_im": True}]
    hist = {"D1": [{"user": "UBOT"}], "D2": [{"user": "U9"}]}
    assert dm_shape(convs, hist, "UBOT")[0] == "two-way"


def test_open_dms_with_nothing_in_them_are_silent_rather_than_outbound():
    convs = [{"id": "D1", "is_im": True}]
    assert dm_shape(convs, {"D1": []}, "UBOT")[0] == "silent"


def test_no_dms_at_all_is_no_evidence():
    assert dm_shape([], {}, "UBOT")[0] == "no-im-conversations"
    assert dm_shape([{"id": "C1", "is_channel": True}], {}, "UBOT")[0] == \\
        "no-im-conversations"


def test_the_tab_being_off_and_the_traffic_agreeing_is_the_note():
    verdict, detail = tab_verdict(["messages-tab-off"], "outbound-only")
    assert verdict == "tab-off"
    assert "agree" in detail


def test_a_reply_in_a_workspace_whose_manifest_says_the_tab_is_off_is_doubted():
    verdict, detail = tab_verdict(["messages-tab-off"], "two-way")
    assert verdict == "tab-off"
    assert "may not be this app" in detail


def test_read_only_is_reported_as_the_shape_with_no_error():
    verdict, detail = tab_verdict(["messages-tab-read-only"], "outbound-only")
    assert verdict == "read-only"
    assert "no error" in detail


def test_an_open_surface_with_no_delivery_path_is_undeliverable():
    assert tab_verdict(["no-message-im-subscription"], "outbound-only")[0] == \\
        "undeliverable"
    assert tab_verdict(["no-im-history-scope"], "silent")[0] == "undeliverable"


def test_every_switch_correct_and_still_one_way_hands_the_problem_back():
    verdict, detail = tab_verdict([], "outbound-only")
    assert verdict == "config-clean"
    assert "handler" in detail


def test_a_working_surface_is_reported_as_consistent():
    assert tab_verdict([], "two-way")[0] == "consistent"


def test_without_a_manifest_the_verdict_says_what_it_rests_on():
    verdict, detail = tab_verdict(["no-manifest"], "outbound-only")
    assert verdict == "traffic-only"
    assert "traffic alone" in detail


def test_the_repair_is_printed_as_manifest_keys():
    lines = repair_manifest(["messages-tab-off", "no-message-im-subscription"])
    assert lines == ["features.app_home.messages_tab_enabled: true",
                     "settings.event_subscriptions.bot_events: add message.im"]


def test_a_finding_with_no_manifest_repair_is_skipped_rather_than_faked():
    assert repair_manifest(["no-manifest"]) == []
''',
"test_js_file": "slack-app-home-messages.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  appHomeFindings, dmShape, repairManifest, tabVerdict,
} from './slack-app-home-messages.mjs';

function manifest({ tab = true, readOnly = false, events = ['message.im'],
  scopes = ['im:history'] } = {}) {
  return {
    manifest: {
      features: {
        app_home: {
          messages_tab_enabled: tab,
          messages_tab_read_only_enabled: readOnly,
        },
      },
      settings: { event_subscriptions: { bot_events: [...events] } },
      oauth_config: { scopes: { bot: [...scopes] } },
    },
  };
}

const codes = (m) => appHomeFindings(m).map(([c]) => c);

test('a healthy configuration produces no findings', () => {
  assert.deepEqual(appHomeFindings(manifest()), []);
});

test('the tab being off is named as the default it is', () => {
  const found = appHomeFindings(manifest({ tab: false }));
  assert.equal(found[0][0], 'messages-tab-off');
  assert.match(found[0][1], /default/);
});

test('read only is only raised when the tab is actually on', () => {
  assert.equal(codes(manifest({ readOnly: true }))
    .includes('messages-tab-read-only'), true);
  assert.equal(codes(manifest({ tab: false, readOnly: true }))
    .includes('messages-tab-read-only'), false);
});

test('a missing subscription is reported alongside the tab not instead', () => {
  assert.deepEqual(codes(manifest({ tab: false, events: [] })),
    ['messages-tab-off', 'no-message-im-subscription']);
});

test('a missing scope is its own finding', () => {
  assert.equal(codes(manifest({ scopes: [] })).includes('no-im-history-scope'), true);
});

test('no manifest is a stated gap rather than a clean bill', () => {
  assert.deepEqual(codes({}), ['no-manifest']);
  assert.deepEqual(codes(null), ['no-manifest']);
});

test('dms where only the app ever spoke are outbound only', () => {
  const convs = [{ id: 'D1', is_im: true }, { id: 'D2', is_im: true }];
  const hist = { D1: [{ user: 'UBOT' }, { bot_id: 'B1' }], D2: [{ user: 'UBOT' }] };
  const [state, counts] = dmShape(convs, hist, 'UBOT');
  assert.equal(state, 'outbound-only');
  assert.deepEqual(counts, { conversations: 2, app_messages: 3, human_messages: 0 });
});

test('one human reply anywhere makes it two way', () => {
  const convs = [{ id: 'D1', is_im: true }, { id: 'D2', is_im: true }];
  const hist = { D1: [{ user: 'UBOT' }], D2: [{ user: 'U9' }] };
  assert.equal(dmShape(convs, hist, 'UBOT')[0], 'two-way');
});

test('open dms with nothing in them are silent rather than outbound', () => {
  assert.equal(dmShape([{ id: 'D1', is_im: true }], { D1: [] }, 'UBOT')[0], 'silent');
});

test('no dms at all is no evidence', () => {
  assert.equal(dmShape([], {}, 'UBOT')[0], 'no-im-conversations');
  assert.equal(dmShape([{ id: 'C1', is_channel: true }], {}, 'UBOT')[0],
    'no-im-conversations');
});

test('the tab being off and the traffic agreeing is the note', () => {
  const [verdict, detail] = tabVerdict(['messages-tab-off'], 'outbound-only');
  assert.equal(verdict, 'tab-off');
  assert.match(detail, /agree/);
});

test('a reply in a workspace whose manifest says the tab is off is doubted', () => {
  const [verdict, detail] = tabVerdict(['messages-tab-off'], 'two-way');
  assert.equal(verdict, 'tab-off');
  assert.match(detail, /may not be this app/);
});

test('read only is reported as the shape with no error', () => {
  const [verdict, detail] = tabVerdict(['messages-tab-read-only'], 'outbound-only');
  assert.equal(verdict, 'read-only');
  assert.match(detail, /no error/);
});

test('an open surface with no delivery path is undeliverable', () => {
  assert.equal(tabVerdict(['no-message-im-subscription'], 'outbound-only')[0],
    'undeliverable');
  assert.equal(tabVerdict(['no-im-history-scope'], 'silent')[0], 'undeliverable');
});

test('every switch correct and still one way hands the problem back', () => {
  const [verdict, detail] = tabVerdict([], 'outbound-only');
  assert.equal(verdict, 'config-clean');
  assert.match(detail, /handler/);
});

test('a working surface is reported as consistent', () => {
  assert.equal(tabVerdict([], 'two-way')[0], 'consistent');
});

test('without a manifest the verdict says what it rests on', () => {
  const [verdict, detail] = tabVerdict(['no-manifest'], 'outbound-only');
  assert.equal(verdict, 'traffic-only');
  assert.match(detail, /traffic alone/);
});

test('the repair is printed as manifest keys', () => {
  assert.deepEqual(repairManifest(['messages-tab-off', 'no-message-im-subscription']),
    ['features.app_home.messages_tab_enabled: true',
      'settings.event_subscriptions.bot_events: add message.im']);
});

test('a finding with no manifest repair is skipped rather than faked', () => {
  assert.deepEqual(repairManifest(['no-manifest']), []);
});
''',
"faq": [
 ("Why is the Messages tab off by default?",
  "Because App Home is a surface rather than a capability, and Slack does not assume an app wants one. A new app can post into channels the moment it is installed, which teaches you in the first hour that things work; the DM surface is the exception, and there is nothing in the creation flow that mentions it. It is also app configuration rather than workspace configuration, so if it is off it is off for every workspace that ever installs the app, and no reinstall will change that."),
 ("We enabled the tab and users still get no answer. What is left?",
  "The delivery path, which is a different page in the settings. Enabling the tab lets people type; message.im in the event subscriptions and im:history in the bot scopes are what turn what they typed into a request to your app. Without both, Slack accepts the message, shows it in the conversation, and delivers it nowhere. The script reports that as undeliverable, and adding the scope means a reinstall, so plan for one."),
 ("Users see a message saying they cannot reply to this conversation. Which setting is that?",
  "The read-only checkbox, which sits next to the tab switch and is the second half of the same feature. In the manifest it is features.app_home.messages_tab_read_only_enabled. This is the one shape of the problem that produces no error anywhere: your outbound messages succeed with ok: true and a real timestamp, and the failure is entirely in a disabled composer on the user's screen. It cannot be found by instrumenting your own code, only by reading the setting."),
 ("Can a bot token read these flags?",
  "No. features.app_home lives in the app manifest, and reading it needs an app configuration token with app_configurations:read, which is a different credential class from the bot token your app runs on. That is why the second half of this check exists: listing the app's DMs and reading their history needs only im:read and im:history, and a pattern of many conversations in which no person has ever typed is strong evidence on its own."),
 ("Is this the same as the app never having opened a DM with the user?",
  "No, and the errors differ. If no IM channel exists, the failure is that the conversation id does not resolve, and the fix is on your side. This note is about the surface being switched off once the conversation exists: the DM is there, the user can see it in the sidebar under Apps, and either the app cannot post into it or the person cannot answer. dm_shape distinguishes them for you, because no-im-conversations and outbound-only are different findings with different repairs."),
],
"related": [
 ("/slack/dm-never-opened/", "the DM that does not exist yet, which is a different failure"),
 ("/slack/no-event-subscriptions/", "a delivery path with nothing routed down it"),
 ("/slack/event-scope-mismatch/", "a subscribed event whose scope was never granted"),
],
"citations": [CITE_APP_HOME, CITE_MESSAGE_IM, CITE_SO_MSG_TAB, CITE_MANIFEST_EXPORT],
})
GUIDES.append({
"slug": "slash-command-not-registered",
"title": "A slash command your code handles was never registered",
"description": "Commands are declared in app configuration, not in code. Diff the registered set against the handlers in your source, in both directions.",
"h1": "A slash command your code handles was never registered",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack slash command is not a valid command",
             "slack command handler never fires",
             "slack dispatch_failed slash command",
             "slack slash command requires reinstall",
             "features.slash_commands manifest"],
"deps": "Python 3.9+ with requests, or Node.js 18+; an app configuration token with app_configurations:read, and read access to the source files that register your handlers",
"lead": "The handler is written. It has a unit test. Somebody reviewed it, it went out in the release, and the release notes said <em>you can now type <code>/deploy</code> in any channel</em>.</p><p>Type <code>/deploy</code> in a channel and Slack says <code>/deploy is not a valid command</code>, or quietly autocompletes to something else entirely, or does nothing at all. There is no request in your access log, no error in your application log, and no event anywhere. Slack never contacted you, because as far as Slack is concerned this app has no such command &mdash; and it never will until somebody declares it in the app configuration and reinstalls.",
"short_answer": """<p>Slash commands are <strong>declared in app configuration, not in code</strong>. A handler registered in Bolt is a routing rule for a request that has to arrive from somewhere, and the only thing that makes Slack send it is an entry under <strong>Slash Commands</strong> &mdash; or, in a manifest, under <code>features.slash_commands</code> &mdash; carrying a name, a Request URL and a description. Without one, the handler is dead code that nothing will ever call.</p>
<p>Two more things follow from that split, and both bite. Adding a command <strong>requires reinstalling the app</strong>, so declaring it and stopping halfway leaves the same symptom you started with. And command names are <strong>workspace-unique</strong>: Slack's own commands and every other installed app compete for the same namespace, so a generic <code>/deploy</code> may simply belong to somebody else in that workspace, and no amount of configuration on your side will take it back.</p>
<p>The check is a set difference, run in both directions. Export <code>features.slash_commands</code>, scan your source for the commands it handles, and print the two gaps. <strong>Handled but not registered</strong> is this note: the user gets &ldquo;not a valid command&rdquo;. <strong>Registered but not handled</strong> is the mirror image and is worse, because the request does arrive: Slack sends it, your app has no route for it, and the user sees <code>dispatch_failed</code>.</p>""",
"problem": """<p>The reason this survives to production is that nothing fails. There is no exception, no warning at startup, and no signal from Slack. A Bolt app with a handler for a command that does not exist boots exactly like one with a handler that does, serves every other route perfectly, and reports itself healthy. The bug is an absence in a web form.</p>
<p>It is also unusually easy to do halfway. A command is added in the console; the person adding it moves on without reinstalling, and reinstalling is not optional here. A command is added to the manifest in the repository, and the manifest is never deployed, so the file that describes the app and the app itself disagree. A command works in the development app, because that is where the console was open, and the production app &mdash; a separate Slack app, since Slack has no notion of environments &mdash; never got the same edit.</p>
<p>The opposite direction fails differently and more visibly. A command left registered after its handler was removed, or renamed in code and not in configuration, produces a live entry in the Slack autocomplete that anybody can type. Slack sends the request, your app returns a 404 for the route or throws before acknowledging, and the user gets <code>dispatch_failed</code> in the channel with your app's name attached to it. Nobody files a bug for a command they did not know existed; they just conclude the app is broken.</p>
<p>Then there is the namespace, which is not yours. Command names are unique per workspace across every installed app plus Slack's own built-ins, so <code>/remind</code>, <code>/invite</code> and <code>/status</code> are gone before you start, and <code>/deploy</code> is a coin toss in any workspace with more than a handful of apps. What makes this one hard is that it is genuinely invisible to the API: no read method tells you which other app owns a name in a customer's workspace. All a script can do is tell you when you are gambling.</p>""",
"why": """<p><strong>The diff has to run in both directions, because the two gaps are different bugs with different victims.</strong> A handler with no registration is invisible: nobody can trigger it, and it costs you only the feature. A registration with no handler is public: it appears in autocomplete, it can be typed by anyone, and it answers with an error that carries your app's name. Reporting one and not the other leaves half the problem in place.</p>
<p><strong>The handled set should come from the source, not from a list somebody typed.</strong> The whole failure is a divergence between two artefacts, and asking a human to enumerate one of them reintroduces the divergence into the check. So the script scans the files you point it at for <code>.command(...)</code> registrations and builds the set from what is actually in the code.</p>
<p><strong>Handlers registered by pattern have to be counted and not guessed at.</strong> Bolt lets you route a command with a regular expression. Those cannot be diffed against a name, so the script counts them separately and says so, rather than reporting a registered command as unhandled when a pattern quietly covers it. A check that produces confident false positives gets switched off.</p>
<p><strong>Names are normalised before they are compared, because that is where the near misses hide.</strong> <code>deploy</code>, <code>/deploy</code> and <code>/Deploy</code> are the same command written three ways across a manifest, a console form and a source file. Comparing raw strings would report a command as both unregistered and unhandled at the same time, which is the least useful output available.</p>
<p><strong>The namespace is a blind spot and the script says so out loud.</strong> There is no read method that reports which app owns <code>/deploy</code> in a workspace you do not administer. What a script can do is flag a name that Slack itself owns, and flag a name generic enough to be somebody else's, and recommend a prefix. Pretending to more certainty than that would be a lie about the API.</p>
<p><strong>Nothing here is a probe.</strong> There is no way to test a slash command from a script without typing it into a workspace, which posts, which is a write. Every finding comes from the manifest and from your own files.</p>""",
"steps": [
 {"h": "Export the registered commands",
  "body": """<p><code>apps.manifest.export</code> returns <code>features.slash_commands</code>, each entry with <code>command</code>, <code>url</code>, <code>description</code>, <code>usage_hint</code> and <code>should_escape</code>. It needs an app configuration token. Without one, pass <code>--registered</code> with the names from the Slash Commands page and the diff still runs.</p>"""},
 {"h": "Build the handled set from the code itself",
  "body": """<p><code>commands_in_source</code> reads the files you name and returns the command literals it finds in <code>.command(...)</code> registrations, plus a count of pattern-based handlers it deliberately will not guess about. Building this set from source rather than from a list somebody typed is the point: the failure is a divergence between two artefacts, and typing one of them out by hand recreates it inside the check.</p>"""},
 {"h": "Normalise before comparing",
  "body": """<p><code>normalise_command</code> settles the leading slash and the case, and reports <code>no-slash</code>, <code>uppercase</code>, <code>has-space</code>, <code>too-long</code> and <code>invalid-char</code> along the way. Without this step the same command written three ways in three places is reported as three findings, none of them true.</p>"""},
 {"h": "Diff in both directions and read both answers",
  "body": """<p><code>command_diff</code> returns the dead handlers, the unhandled registrations and the matched set. The first list is the one users report as &ldquo;not a valid command&rdquo;. The second is the one that answers strangers with <code>dispatch_failed</code>, and it is usually the one nobody knew about.</p>"""},
 {"h": "Look at the names you are about to gamble on",
  "body": """<p><code>name_risk</code> answers <code>reserved</code>, <code>generic</code>, <code>namespaced</code> or <code>invalid</code>. Slack's own commands are unavailable everywhere; a bare English verb is available until the workspace installs one more app. A prefix is not decoration, it is the only defence, and there is no API that will warn you before a customer collides.</p>"""},
 {"h": "Register, then reinstall, then check the registrations you already have",
  "body": """<p><code>registration_gaps</code> reads each registered entry for a missing Request URL, a plain <code>http</code> URL or a missing description. Then reinstall: a new command does not take effect until the app is reinstalled, which is the step that turns &ldquo;I added it and nothing changed&rdquo; into a working command.</p>"""},
],
"verify": """<p>Register the missing command, reinstall, and run it again. Both gaps should be empty and <code>matched</code> should hold everything your app answers.</p>
<pre><code class="language-bash">python3 slack_slash_commands.py --app-id A05NW7XQ1 --source app/commands.py,app/legacy.py
# manifest   ok             3 registered command(s) for A05NW7XQ1
# source     2 file(s)      3 handled command(s), 1 pattern handler(s) not diffed
# dead       /deploy        handled in your source and registered nowhere; users get
#                           "/deploy is not a valid command"
# unhandled  /oldsync       registered with a Request URL and handled by nothing;
#                           whoever types it gets dispatch_failed from your app
# matched    /acme-status, /acme-whoami
# risk       /deploy        generic     a bare name in a namespace shared with every
#                           other installed app; consider /acme-deploy
# risk       /oldsync       generic     ...
# gap        /oldsync       no-description   Slack shows this in the autocomplete
# verdict    2 finding(s)
#   repair: declare /deploy under features.slash_commands with the production
#           Request URL, then reinstall the app; new commands need a reinstall
#   repair: remove /oldsync from the app configuration, or add a handler for it
#   note:   no read method reports which other app owns a name in a workspace</code></pre>""",
"code_intro": "One optional network call and one local read. <code>normalise_command</code> exists so that the same command written three ways in three places stops being three findings. <code>commands_in_source</code> builds the handled set out of the code rather than out of somebody's memory, and counts the pattern-based handlers separately instead of guessing about them. <code>command_diff</code> is the whole check, run in both directions. <code>name_risk</code> and <code>registration_gaps</code> cover the two things that are true of a command even when the diff is clean.",
"py_file": "slack_slash_commands.py",
"py": '''"""Diff the slash commands your app registers against the ones it handles.

Read only. At most one GET is made, to apps.manifest.export with an app
configuration token; everything else is your own source, read from disk. There
is no way to test a slash command from a script without typing it into a
workspace, which would be a write, so nothing here probes anything.

The one thing this cannot see is the rest of the namespace. Command names are
unique per workspace across every installed app, and no read method reports
which app owns a name in a workspace you do not administer. The script flags
the names worth worrying about and is honest that it cannot settle them.
"""
import argparse
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_slash_commands")

API = "https://slack.com/api/"

# Slack's own commands. These are unavailable in every workspace, everywhere,
# and no configuration on your side will take one back.
SLACK_BUILTINS = frozenset({
    "/active", "/away", "/archive", "/call", "/collapse", "/dm", "/dnd", "/expand",
    "/feed", "/feedback", "/giphy", "/help", "/invite", "/join", "/leave", "/me",
    "/msg", "/mute", "/open", "/prefs", "/remind", "/remove", "/rename", "/search",
    "/shortcuts", "/shrug", "/star", "/status", "/topic", "/who",
})

# Slack's ceiling for a command name, the slash included.
MAX_NAME = 32

# Two patterns rather than one: the literal registrations can be diffed by
# name, and the rest are pattern handlers that cannot. Counting them separately
# is what stops the script reporting a registered command as unhandled because
# a regular expression quietly covers it.
CMD_CALL = re.compile(r"""\\.command\\(""")
CMD_LITERAL = re.compile(r"""\\.command\\(\\s*["']([^"']+)["']""")

ALLOWED = re.compile(r"^[a-z0-9_-]+$")


def normalise_command(name):
    """Settle the slash and the case so two spellings compare equal. Pure.

    Returns (canonical, notes). Without this, the same command written as
    deploy in a manifest, /deploy in a console and /Deploy in a source file is
    reported as three separate findings, none of which is real.
    """
    text = str(name or "").strip()
    notes = []
    if not text:
        return ("", ["empty"])
    if not text.startswith("/"):
        notes.append("no-slash")
        text = "/" + text
    body = text[1:]
    if body != body.lower():
        notes.append("uppercase")
        body = body.lower()
    if " " in body or "\\t" in body:
        notes.append("has-space")
        body = body.split()[0] if body.split() else ""
    if len(body) + 1 > MAX_NAME:
        notes.append("too-long")
    if body and not ALLOWED.match(body):
        notes.append("invalid-char")
    return ("/" + body if body else "", notes)


def commands_in_source(text):
    """Which commands does this source register? Pure.

    Returns (names, dynamic). names is the sorted set of canonical command
    literals; dynamic counts the .command(...) registrations whose argument is
    not a string literal - a regular expression, or a name held in a variable.
    Those cannot be diffed against a list of names, and pretending otherwise
    would produce confident false positives.
    """
    body = str(text or "")
    names = set()
    for match in CMD_LITERAL.finditer(body):
        canonical, _notes = normalise_command(match.group(1))
        if canonical:
            names.add(canonical)
    dynamic = len(CMD_CALL.findall(body)) - len(CMD_LITERAL.findall(body))
    return (sorted(names), max(0, dynamic))


def command_diff(registered, handled):
    """The two gaps, and the overlap. Pure.

    Returns (dead_handlers, unhandled_registrations, matched), all sorted lists
    of canonical names.

      dead_handlers            handled in code, registered nowhere. Users get
                               "not a valid command" and your handler is dead.
      unhandled_registrations  registered and handled by nothing. Slack sends
                               the request, your app has no route, and the user
                               sees dispatch_failed with your app name on it.
    """
    reg = {normalise_command(n)[0] for n in (registered or [])}
    hand = {normalise_command(n)[0] for n in (handled or [])}
    reg.discard("")
    hand.discard("")
    return (sorted(hand - reg), sorted(reg - hand), sorted(reg & hand))


def name_risk(name):
    """How likely is this name to be somebody else's? Pure.

    Returns (risk, detail). This is the honest limit of the check: the API
    cannot tell you who owns a name in a workspace you do not administer, so
    the script grades the gamble instead of pretending to settle it.
    """
    canonical, notes = normalise_command(name)
    if not canonical:
        return ("invalid", "an empty command name")
    bad = [n for n in notes if n in ("has-space", "too-long", "invalid-char")]
    if bad:
        return ("invalid", "Slack will not accept this name: %s" % ", ".join(bad))
    if canonical in SLACK_BUILTINS:
        return ("reserved", "%s is one of Slack's own commands and is unavailable in "
                            "every workspace" % canonical)
    body = canonical[1:]
    if "-" in body or "_" in body:
        return ("namespaced", "the name carries a prefix, which is the only defence "
                              "against a collision")
    return ("generic", "a bare name in a namespace shared with every other installed "
                       "app; consider a prefix such as /acme-%s" % body)


def registration_gaps(entry):
    """What is missing from one registered command? Pure.

    Returns a list of (code, detail). The Request URL's health beyond the
    scheme is a separate question with a separate check; this one only reports
    that the URL is absent or plainly wrong.
    """
    command = str((entry or {}).get("command") or "")
    url = str((entry or {}).get("url") or "").strip()
    out = []
    if not url:
        out.append(("no-url", "no Request URL, so Slack has nowhere to send %s"
                    % (command or "this command")))
    elif url.lower().startswith("http://"):
        out.append(("insecure-url", "the Request URL is plain http; the payload "
                                    "carries a signing header and a user's text"))
    if not str((entry or {}).get("description") or "").strip():
        out.append(("no-description", "Slack shows the description in the autocomplete "
                                      "and requires one"))
    return out


def export_manifest(session, token, app_id):
    """One GET, with an app configuration token. Returns the parsed body."""
    r = session.get(API + "apps.manifest.export",
                    headers={"Authorization": "Bearer " + token},
                    params={"app_id": app_id}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app-id", default="", help="the app id to export, A...")
    ap.add_argument("--config-token-env", default="SLACK_CONFIG_ACCESS_TOKEN",
                    help="environment variable holding an app configuration token")
    ap.add_argument("--registered", default="",
                    help="comma separated command names, if you have no config token")
    ap.add_argument("--source", default="",
                    help="comma separated source files that register handlers")
    ap.add_argument("--handled", default="",
                    help="comma separated command names your app handles")
    args = ap.parse_args()

    entries = []
    registered = [n.strip() for n in args.registered.split(",") if n.strip()]
    token = os.environ.get(args.config_token_env)
    if args.app_id and token and not registered:
        body = export_manifest(requests.Session(), token, args.app_id)
        if body.get("ok") is not True:
            log.warning("manifest   unavailable    apps.manifest.export answered "
                        "ok: false, error=%s", body.get("error"))
        else:
            features = ((body.get("manifest") or body).get("features") or {})
            entries = list(features.get("slash_commands") or [])
            registered = [str(e.get("command") or "") for e in entries]
            log.info("manifest   ok             %d registered command(s) for %s",
                     len(registered), args.app_id)
    elif not registered:
        log.info("manifest   skipped        set %s, or pass --registered with the "
                 "names from the Slash Commands page", args.config_token_env)

    handled = [n.strip() for n in args.handled.split(",") if n.strip()]
    files = [p.strip() for p in args.source.split(",") if p.strip()]
    dynamic = 0
    for path in files:
        found, patterns = commands_in_source(open(path, encoding="utf-8").read())
        handled.extend(found)
        dynamic += patterns
    if files:
        log.info("source     %d file(s)      %d handled command(s), %d pattern "
                 "handler(s) not diffed", len(files), len(set(handled)), dynamic)

    dead, unhandled, matched = command_diff(registered, handled)
    findings = 0
    for name in dead:
        log.warning("dead       %-14s handled in your source and registered nowhere; "
                    'users get "%s is not a valid command"', name, name)
        findings += 1
    for name in unhandled:
        if dynamic:
            log.info("unhandled  %-14s registered and not matched by a literal "
                     "handler; %d pattern handler(s) may cover it", name, dynamic)
            continue
        log.warning("unhandled  %-14s registered with a Request URL and handled by "
                    "nothing; whoever types it gets dispatch_failed from your app",
                    name)
        findings += 1
    log.info("matched    %s", ", ".join(matched) or "none")

    for name in sorted(set(registered) | set(handled)):
        risk, detail = name_risk(name)
        if risk in ("reserved", "invalid"):
            log.warning("risk       %-14s %-10s %s", normalise_command(name)[0], risk,
                        detail)
            findings += 1
        elif risk == "generic":
            log.info("risk       %-14s %-10s %s", normalise_command(name)[0], risk,
                     detail)

    for entry in entries:
        for code, detail in registration_gaps(entry):
            log.warning("gap        %-14s %-16s %s",
                        normalise_command(entry.get("command"))[0], code, detail)
            findings += 1

    if not findings:
        log.info("verdict    clean          every handler is registered and every "
                 "registration is handled")
        return 0
    log.warning("verdict    %d finding(s)", findings)
    log.warning("  repair: declare the missing command(s) under "
                "features.slash_commands with the production Request URL, then "
                "reinstall the app; new commands need a reinstall")
    log.warning("  repair: remove the registrations nothing handles, or add a handler "
                "for them, so nobody can type one and get dispatch_failed")
    log.warning("  note:   no read method reports which other app owns a name in a "
                "workspace, so a generic name stays a gamble")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-slash-commands.mjs",
"js": '''/**
 * Diff the slash commands your app registers against the ones it handles.
 *
 * Read only. At most one GET is made, to apps.manifest.export with an app
 * configuration token; everything else is your own source, read from disk.
 * There is no way to test a slash command from a script without typing it into
 * a workspace, which would be a write, so nothing here probes anything.
 *
 * The one thing this cannot see is the rest of the namespace: no read method
 * reports which app owns a name in a workspace you do not administer.
 */

import { readFileSync } from 'node:fs';

const API = 'https://slack.com/api/';

// Slack's own commands, unavailable in every workspace, everywhere.
export const SLACK_BUILTINS = new Set([
  '/active', '/away', '/archive', '/call', '/collapse', '/dm', '/dnd', '/expand',
  '/feed', '/feedback', '/giphy', '/help', '/invite', '/join', '/leave', '/me',
  '/msg', '/mute', '/open', '/prefs', '/remind', '/remove', '/rename', '/search',
  '/shortcuts', '/shrug', '/star', '/status', '/topic', '/who',
]);

// Slack's ceiling for a command name, the slash included.
export const MAX_NAME = 32;

const CMD_CALL = /\\.command\\(/g;
const CMD_LITERAL = /\\.command\\(\\s*["']([^"']+)["']/g;
const ALLOWED = /^[a-z0-9_-]+$/;

/** Settle the slash and the case so two spellings compare equal. Pure. */
export function normaliseCommand(name) {
  let text = String(name ?? '').trim();
  const notes = [];
  if (!text) return ['', ['empty']];
  if (!text.startsWith('/')) {
    notes.push('no-slash');
    text = `/${text}`;
  }
  let body = text.slice(1);
  if (body !== body.toLowerCase()) {
    notes.push('uppercase');
    body = body.toLowerCase();
  }
  if (/\\s/.test(body)) {
    notes.push('has-space');
    [body] = body.split(/\\s+/).filter(Boolean).concat(['']);
  }
  if (body.length + 1 > MAX_NAME) notes.push('too-long');
  if (body && !ALLOWED.test(body)) notes.push('invalid-char');
  return [body ? `/${body}` : '', notes];
}

/**
 * Which commands does this source register? Pure.
 * Returns [names, dynamic]; dynamic counts pattern handlers that cannot be
 * diffed against a name and must not be guessed about.
 */
export function commandsInSource(text) {
  const body = String(text ?? '');
  const names = new Set();
  for (const match of body.matchAll(CMD_LITERAL)) {
    const [canonical] = normaliseCommand(match[1]);
    if (canonical) names.add(canonical);
  }
  const calls = [...body.matchAll(CMD_CALL)].length;
  const literals = [...body.matchAll(CMD_LITERAL)].length;
  return [[...names].sort(), Math.max(0, calls - literals)];
}

/**
 * The two gaps, and the overlap. Pure.
 * Returns [deadHandlers, unhandledRegistrations, matched].
 */
export function commandDiff(registered, handled) {
  const reg = new Set((registered ?? []).map((n) => normaliseCommand(n)[0]));
  const hand = new Set((handled ?? []).map((n) => normaliseCommand(n)[0]));
  reg.delete('');
  hand.delete('');
  const only = (a, b) => [...a].filter((n) => !b.has(n)).sort();
  return [only(hand, reg), only(reg, hand),
    [...reg].filter((n) => hand.has(n)).sort()];
}

/** How likely is this name to be somebody else? Pure. */
export function nameRisk(name) {
  const [canonical, notes] = normaliseCommand(name);
  if (!canonical) return ['invalid', 'an empty command name'];
  const bad = notes.filter((n) => ['has-space', 'too-long', 'invalid-char'].includes(n));
  if (bad.length) {
    return ['invalid', `Slack will not accept this name: ${bad.join(', ')}`];
  }
  if (SLACK_BUILTINS.has(canonical)) {
    return ['reserved', `${canonical} is one of Slack own commands and is unavailable `
      + 'in every workspace'];
  }
  const body = canonical.slice(1);
  if (body.includes('-') || body.includes('_')) {
    return ['namespaced', 'the name carries a prefix, which is the only defence '
      + 'against a collision'];
  }
  return ['generic', 'a bare name in a namespace shared with every other installed '
    + `app; consider a prefix such as /acme-${body}`];
}

/** What is missing from one registered command? Pure. */
export function registrationGaps(entry) {
  const command = String((entry ?? {}).command ?? '');
  const url = String((entry ?? {}).url ?? '').trim();
  const out = [];
  if (!url) {
    out.push(['no-url',
      `no Request URL, so Slack has nowhere to send ${command || 'this command'}`]);
  } else if (url.toLowerCase().startsWith('http://')) {
    out.push(['insecure-url', 'the Request URL is plain http; the payload carries a '
      + 'signing header and a user text']);
  }
  if (!String((entry ?? {}).description ?? '').trim()) {
    out.push(['no-description',
      'Slack shows the description in the autocomplete and requires one']);
  }
  return out;
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function exportManifest(token, appId) {
  const url = `${API}apps.manifest.export?app_id=${encodeURIComponent(appId)}`;
  const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
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
  let entries = [];
  let registered = arg(args, '--registered').split(',')
    .map((n) => n.trim()).filter(Boolean);

  const token = process.env[configTokenEnv];
  if (appId && token && !registered.length) {
    const body = await exportManifest(token, appId);
    if (body.ok !== true) {
      console.warn('manifest   unavailable    apps.manifest.export answered ok: false, '
        + `error=${body.error}`);
    } else {
      const features = (body.manifest ?? body).features ?? {};
      entries = [...(features.slash_commands ?? [])];
      registered = entries.map((e) => String(e.command ?? ''));
      console.log(`manifest   ok             ${registered.length} registered `
        + `command(s) for ${appId}`);
    }
  } else if (!registered.length) {
    console.log(`manifest   skipped        set ${configTokenEnv}, or pass --registered `
      + 'with the names from the Slash Commands page');
  }

  const handled = arg(args, '--handled').split(',').map((n) => n.trim()).filter(Boolean);
  const files = arg(args, '--source').split(',').map((p) => p.trim()).filter(Boolean);
  let dynamic = 0;
  for (const path of files) {
    const [found, patterns] = commandsInSource(readFileSync(path, 'utf-8'));
    handled.push(...found);
    dynamic += patterns;
  }
  if (files.length) {
    console.log(`source     ${files.length} file(s)      ${new Set(handled).size} `
      + `handled command(s), ${dynamic} pattern handler(s) not diffed`);
  }

  const [dead, unhandled, matched] = commandDiff(registered, handled);
  let findings = 0;
  for (const name of dead) {
    console.warn(`dead       ${name.padEnd(14)} handled in your source and registered `
      + `nowhere; users get "${name} is not a valid command"`);
    findings += 1;
  }
  for (const name of unhandled) {
    if (dynamic) {
      console.log(`unhandled  ${name.padEnd(14)} registered and not matched by a `
        + `literal handler; ${dynamic} pattern handler(s) may cover it`);
      continue;
    }
    console.warn(`unhandled  ${name.padEnd(14)} registered with a Request URL and `
      + 'handled by nothing; whoever types it gets dispatch_failed from your app');
    findings += 1;
  }
  console.log(`matched    ${matched.join(', ') || 'none'}`);

  for (const name of [...new Set([...registered, ...handled])].sort()) {
    const [risk, detail] = nameRisk(name);
    const canonical = normaliseCommand(name)[0];
    if (risk === 'reserved' || risk === 'invalid') {
      console.warn(`risk       ${canonical.padEnd(14)} ${risk.padEnd(10)} ${detail}`);
      findings += 1;
    } else if (risk === 'generic') {
      console.log(`risk       ${canonical.padEnd(14)} ${risk.padEnd(10)} ${detail}`);
    }
  }

  for (const entry of entries) {
    for (const [code, detail] of registrationGaps(entry)) {
      console.warn(`gap        ${normaliseCommand(entry.command)[0].padEnd(14)} `
        + `${code.padEnd(16)} ${detail}`);
      findings += 1;
    }
  }

  if (!findings) {
    console.log('verdict    clean          every handler is registered and every '
      + 'registration is handled');
    return;
  }
  console.warn(`verdict    ${findings} finding(s)`);
  console.warn('  repair: declare the missing command(s) under features.slash_commands '
    + 'with the production Request URL, then reinstall the app');
  console.warn('  repair: remove the registrations nothing handles, or add a handler '
    + 'for them, so nobody can type one and get dispatch_failed');
  console.warn('  note:   no read method reports which other app owns a name in a '
    + 'workspace, so a generic name stays a gamble');
  process.exitCode = 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures here are source snippets rather than credentials, because the input to this check is your own code. The assertions worth reading are the ones that stop the diff lying: a pattern-based handler is counted and never named, so a registered command covered by a regular expression is not reported as unhandled; and normalisation is pinned hard, because <code>deploy</code>, <code>/deploy</code> and <code>/Deploy</code> written across a manifest, a console and a source file must collapse to one name before anything is compared.",
"test_py_file": "test_slack_slash_commands.py",
"test_py": '''from slack_slash_commands import (
    command_diff, commands_in_source, name_risk, normalise_command, registration_gaps,
)


def test_the_leading_slash_is_settled_in_both_directions():
    assert normalise_command("deploy")[0] == "/deploy"
    assert normalise_command("/deploy")[0] == "/deploy"
    assert "no-slash" in normalise_command("deploy")[1]


def test_case_is_folded_and_reported():
    canonical, notes = normalise_command("/Deploy")
    assert canonical == "/deploy"
    assert "uppercase" in notes


def test_a_name_with_a_space_is_cut_and_flagged():
    canonical, notes = normalise_command("/deploy now")
    assert canonical == "/deploy"
    assert "has-space" in notes


def test_a_name_past_the_ceiling_is_flagged():
    assert "too-long" in normalise_command("/" + "a" * 40)[1]


def test_an_empty_name_is_empty_rather_than_a_slash():
    assert normalise_command("")[0] == ""
    assert normalise_command(None)[0] == ""


def test_handlers_are_found_in_both_bolt_dialects():
    src = """
    app.command("/acme-deploy")(handle)
    @app.command('/acme-status')
    def status(ack): ack()
    """
    names, dynamic = commands_in_source(src)
    assert names == ["/acme-deploy", "/acme-status"]
    assert dynamic == 0


def test_a_pattern_handler_is_counted_and_never_named():
    src = "app.command(re.compile(r'^/acme-.*'))(handle)"
    names, dynamic = commands_in_source(src)
    assert names == []
    assert dynamic == 1


def test_source_with_no_handlers_is_empty_rather_than_an_error():
    assert commands_in_source("") == ([], 0)
    assert commands_in_source(None) == ([], 0)


def test_a_handler_with_no_registration_is_the_dead_one():
    dead, unhandled, matched = command_diff(["/acme-status"],
                                            ["/acme-status", "/deploy"])
    assert dead == ["/deploy"]
    assert unhandled == []
    assert matched == ["/acme-status"]


def test_a_registration_with_no_handler_is_the_one_users_can_type():
    dead, unhandled, _matched = command_diff(["/oldsync"], [])
    assert dead == []
    assert unhandled == ["/oldsync"]


def test_the_diff_normalises_before_comparing():
    dead, unhandled, matched = command_diff(["deploy"], ["/Deploy"])
    assert dead == []
    assert unhandled == []
    assert matched == ["/deploy"]


def test_empty_names_do_not_become_a_finding():
    assert command_diff(["", None], ["", None]) == ([], [], [])


def test_a_slack_builtin_is_reserved_everywhere():
    risk, detail = name_risk("/remind")
    assert risk == "reserved"
    assert "every workspace" in detail


def test_a_prefixed_name_is_the_defended_one():
    assert name_risk("/acme-deploy")[0] == "namespaced"
    assert name_risk("/acme_deploy")[0] == "namespaced"


def test_a_bare_name_is_a_gamble_and_the_advice_is_a_prefix():
    risk, detail = name_risk("/deploy")
    assert risk == "generic"
    assert "/acme-deploy" in detail


def test_a_name_slack_will_not_accept_is_invalid_rather_than_generic():
    assert name_risk("/deploy now")[0] == "invalid"
    assert name_risk("")[0] == "invalid"


def test_a_registration_without_a_url_has_nowhere_to_send_anything():
    codes = [c for c, _d in registration_gaps({"command": "/x", "description": "d"})]
    assert codes == ["no-url"]


def test_a_plain_http_request_url_is_reported():
    codes = [c for c, _d in registration_gaps(
        {"command": "/x", "url": "http://example.com/s", "description": "d"})]
    assert codes == ["insecure-url"]


def test_a_missing_description_is_its_own_gap():
    codes = [c for c, _d in registration_gaps(
        {"command": "/x", "url": "https://example.com/s"})]
    assert codes == ["no-description"]


def test_a_complete_registration_has_no_gaps():
    assert registration_gaps({"command": "/x", "url": "https://example.com/s",
                              "description": "does a thing"}) == []
''',
"test_js_file": "slack-slash-commands.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  commandDiff, commandsInSource, nameRisk, normaliseCommand, registrationGaps,
} from './slack-slash-commands.mjs';

const codes = (entry) => registrationGaps(entry).map(([c]) => c);

test('the leading slash is settled in both directions', () => {
  assert.equal(normaliseCommand('deploy')[0], '/deploy');
  assert.equal(normaliseCommand('/deploy')[0], '/deploy');
  assert.equal(normaliseCommand('deploy')[1].includes('no-slash'), true);
});

test('case is folded and reported', () => {
  const [canonical, notes] = normaliseCommand('/Deploy');
  assert.equal(canonical, '/deploy');
  assert.equal(notes.includes('uppercase'), true);
});

test('a name with a space is cut and flagged', () => {
  const [canonical, notes] = normaliseCommand('/deploy now');
  assert.equal(canonical, '/deploy');
  assert.equal(notes.includes('has-space'), true);
});

test('a name past the ceiling is flagged', () => {
  assert.equal(normaliseCommand(`/${'a'.repeat(40)}`)[1].includes('too-long'), true);
});

test('an empty name is empty rather than a slash', () => {
  assert.equal(normaliseCommand('')[0], '');
  assert.equal(normaliseCommand(null)[0], '');
});

test('handlers are found in both bolt dialects', () => {
  const src = `
    app.command("/acme-deploy", handle);
    app.command('/acme-status', status);
  `;
  const [names, dynamic] = commandsInSource(src);
  assert.deepEqual(names, ['/acme-deploy', '/acme-status']);
  assert.equal(dynamic, 0);
});

test('a pattern handler is counted and never named', () => {
  const [names, dynamic] = commandsInSource('app.command(/^\\\\/acme-.*/, handle);');
  assert.deepEqual(names, []);
  assert.equal(dynamic, 1);
});

test('source with no handlers is empty rather than an error', () => {
  assert.deepEqual(commandsInSource(''), [[], 0]);
  assert.deepEqual(commandsInSource(null), [[], 0]);
});

test('a handler with no registration is the dead one', () => {
  const [dead, unhandled, matched] = commandDiff(['/acme-status'],
    ['/acme-status', '/deploy']);
  assert.deepEqual(dead, ['/deploy']);
  assert.deepEqual(unhandled, []);
  assert.deepEqual(matched, ['/acme-status']);
});

test('a registration with no handler is the one users can type', () => {
  const [dead, unhandled] = commandDiff(['/oldsync'], []);
  assert.deepEqual(dead, []);
  assert.deepEqual(unhandled, ['/oldsync']);
});

test('the diff normalises before comparing', () => {
  const [dead, unhandled, matched] = commandDiff(['deploy'], ['/Deploy']);
  assert.deepEqual(dead, []);
  assert.deepEqual(unhandled, []);
  assert.deepEqual(matched, ['/deploy']);
});

test('empty names do not become a finding', () => {
  assert.deepEqual(commandDiff(['', null], ['', null]), [[], [], []]);
});

test('a slack builtin is reserved everywhere', () => {
  const [risk, detail] = nameRisk('/remind');
  assert.equal(risk, 'reserved');
  assert.match(detail, /every workspace/);
});

test('a prefixed name is the defended one', () => {
  assert.equal(nameRisk('/acme-deploy')[0], 'namespaced');
  assert.equal(nameRisk('/acme_deploy')[0], 'namespaced');
});

test('a bare name is a gamble and the advice is a prefix', () => {
  const [risk, detail] = nameRisk('/deploy');
  assert.equal(risk, 'generic');
  assert.match(detail, /\\/acme-deploy/);
});

test('a name slack will not accept is invalid rather than generic', () => {
  assert.equal(nameRisk('/deploy now')[0], 'invalid');
  assert.equal(nameRisk('')[0], 'invalid');
});

test('a registration without a url has nowhere to send anything', () => {
  assert.deepEqual(codes({ command: '/x', description: 'd' }), ['no-url']);
});

test('a plain http request url is reported', () => {
  assert.deepEqual(codes({ command: '/x', url: 'http://example.com/s',
    description: 'd' }), ['insecure-url']);
});

test('a missing description is its own gap', () => {
  assert.deepEqual(codes({ command: '/x', url: 'https://example.com/s' }),
    ['no-description']);
});

test('a complete registration has no gaps', () => {
  assert.deepEqual(registrationGaps({ command: '/x', url: 'https://example.com/s',
    description: 'does a thing' }), []);
});
''',
"faq": [
 ("The handler is in the code and it never fires. Why?",
  "Because a handler is a routing rule for a request that has to arrive, and nothing makes Slack send it except an entry in the app configuration. Bolt will happily register a route for a command that does not exist, boot cleanly, and serve everything else, because from the framework's point of view nothing is wrong. Until the command is declared under Slash Commands, or features.slash_commands in a manifest, Slack has never heard of it and no request is ever made."),
 ("I added it in the app configuration and it still says it is not a valid command.",
  "Reinstall the app. A new slash command does not take effect on an existing installation until the app is installed again into that workspace, and this is the step that gets skipped most often, because everything on the configuration page looks correct afterwards. If you distribute the app, every workspace needs the reinstall, which is worth batching with other configuration changes rather than doing one command at a time."),
 ("Another app in the workspace already uses the name we want. Can we detect that?",
  "Not from the API, and the script says so rather than pretending. Command names are unique per workspace across every installed app plus Slack's own built-ins, and there is no read method that reports which app owns a name in a workspace you do not administer. What the check can do is tell you when you are gambling: reserved for Slack's own commands, and generic for a bare English word that any other app might claim. The only real defence is a prefix."),
 ("What produces dispatch_failed, and how is it different from what we have here?",
  "It is the same divergence read from the other end. dispatch_failed means the command is registered, Slack sent the request to your Request URL, and your app did not answer it usefully: no route for that name, or an unhandled exception before the acknowledgement. That is the second list the diff prints, and it is more public than the first, because a registered command appears in the autocomplete and anyone can type it and see your app's name attached to the error."),
 ("Can we run this without an app configuration token?",
  "Partly, and the missing half is the important one. The set of handled commands comes from your own source, which you always have. The set of registered commands comes from the manifest, which needs an app configuration token with app_configurations:read, and a bot token cannot substitute for it. Pass --registered with the names copied from the Slash Commands page and the diff runs identically; it just means the list has been transcribed by a person, which is exactly the kind of step this check exists to remove."),
],
"related": [
 ("/slack/http-or-dead-tunnel-request-url/", "the Request URL a registered command points at"),
 ("/slack/three-second-timeout/", "what the handler has to do once the request arrives"),
 ("/slack/config-token-expired/", "the credential that reads the registrations"),
],
"citations": [CITE_SLASH_COMMANDS, CITE_MANIFEST_REF, CITE_BOLT_579, CITE_SO_SLASH],
})
