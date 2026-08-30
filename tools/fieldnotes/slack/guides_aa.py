#!/usr/bin/env python3
"""/slack/ field notes, batch AA - the writing.

Five refusals that all arrive from the administrative surface and have five
different causes. Written together on purpose, because the temptation with
this group is to write one note five times, and the thing that keeps them
apart is that each one is repaired by a different person doing a different
thing.

The first is the credential class. Every admin.* method wants a user token,
and admin.*:read is a scope that appears only under User Token Scopes: it
cannot be attached to a bot token at any price. So the finding is not an error
from a method, it is an absence in your own environment - the user half of the
OAuth grant, authed_user.access_token, which install handlers routinely throw
away because the bot token is the one everything else needs. This note never
calls an admin method. The note next door, not-allowed-token-type, does the
runtime reading of one method's refusal and asks which class that method
wanted; this one asks whether the class exists in your store at all, and the
repair is a change to the install rather than a change to the call.

The second is the person. The class is right and the scopes are granted, and
the method still refuses, because admin.* scopes can be granted to any user
token while the methods check the caller's actual role at call time. The trap
that makes this survive an afternoon of debugging is that users.info returns
two different is_admin fields: the root one is the workspace role, and the
org role the methods check lives in enterprise_user.

The third is neither: the plan. admin.* is an Enterprise Grid surface and a
Pro or Business+ workspace answers feature_not_enabled no matter who calls it
with what. The reading here is a per-tenant capability matrix, and its most
important rule is that a refusal caused by role or by class must never be
recorded as "this customer is not on Enterprise", which is exactly what a
naive matrix does.

The fourth is a policy aimed at the app. An organization keeps an approved
list and a restricted list, per workspace, and an app can sit on one in some
workspaces and the other in others. Nothing tells you when it moves. The
already-published app-access-restricted note owns the runtime refusal that a
particular person meets and diagnoses it as a cohort of people; this one owns
the app's own listing status across the org's workspaces, plus the approval
requests aging in a queue nobody reads, and the symptom is usually not an
error at all - it is installs quietly not happening.

The fifth is a different mechanism entirely. Enterprise Key Management puts
the encryption keys in the customer's hands, and when access to a key is
revoked Slack refuses the content rather than the caller. No scope, no role
and no plan change touches it, and the only useful thing an app can do is
measure how much is affected and stop retrying.

Read only throughout. The fourth calls four admin read methods and the third
calls one; none of them calls an admin write method, and the first calls no
admin method at all, on the principle that a question answerable from a token
class and a documented requirement should not be answered by spending a
request on a surface where several neighbouring methods write. No token,
client secret or signing secret is read, printed or transmitted by anything
here.
"""

CITE_ADMIN_APPS_APPROVED = ("admin.apps.approved.list method reference - Slack Docs",
                            "https://docs.slack.dev/reference/methods/"
                            "admin.apps.approved.list")
CITE_ADMIN_APPS_RESTRICTED = ("admin.apps.restricted.list method reference - Slack Docs",
                              "https://docs.slack.dev/reference/methods/"
                              "admin.apps.restricted.list")
CITE_ADMIN_APPS_REQUESTS = ("admin.apps.requests.list method reference - Slack Docs",
                            "https://docs.slack.dev/reference/methods/"
                            "admin.apps.requests.list")
CITE_ADMIN_TEAMS_LIST = ("admin.teams.list method reference - Slack Docs",
                         "https://docs.slack.dev/reference/methods/admin.teams.list")
CITE_SCOPE_ADMIN_APPS = ("admin.apps:read scope reference - Slack Docs",
                         "https://docs.slack.dev/reference/scopes/admin.apps.read")
CITE_OAUTH_V2 = ("oauth.v2.access method reference - Slack Docs",
                 "https://docs.slack.dev/reference/methods/oauth.v2.access")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_USERS_INFO = ("users.info method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.info")
CITE_USER_OBJECT = ("The user object, including enterprise_user - Slack Docs",
                    "https://docs.slack.dev/reference/objects/user-object")
CITE_USERS_LIST = ("users.list method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.list")
CITE_TEAM_INFO = ("team.info method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/team.info")
CITE_GRID = ("Enterprise Grid for app developers - Slack Docs",
             "https://docs.slack.dev/enterprise-grid/")
CITE_CONVERSATIONS_HISTORY = ("conversations.history method reference - Slack Docs",
                              "https://docs.slack.dev/reference/methods/"
                              "conversations.history")
CITE_CONVERSATIONS_INFO = ("conversations.info method reference - Slack Docs",
                           "https://docs.slack.dev/reference/methods/conversations.info")
CITE_CHAT_POSTMESSAGE = ("chat.postMessage method reference - Slack Docs",
                         "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_EKM = ("Slack Enterprise Key Management - Slack Help Center",
            "https://slack.com/help/articles/360019110974-Slack-Enterprise-Key-Management")

GUIDES = []

GUIDES.append({
"slug": "admin-method-needs-user-token",
"title": "admin.* needs a user token your install never stored",
"description": "admin.*:read cannot be granted to a bot token at all. Inventory the credentials you hold and find the missing half of the OAuth grant before you call anything.",
"h1": "admin.* needs a user token your install never stored",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack admin api not_allowed_token_type bot token",
             "slack admin.apps:read user token scope",
             "slack authed_user access_token oauth v2",
             "slack admin methods require user token",
             "slack bot token cannot have admin scopes"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the environment variables that hold your Slack credentials, and optionally your stored OAuth install record as JSON with the token values removed",
"lead": "The scope is granted. You can see it in the app configuration, you added it deliberately, and the install went through without complaint: <code>admin.apps:read</code>, right there on the list. And <code>admin.apps.approved.list</code> comes back <code>{\"ok\": false, \"error\": \"not_allowed_token_type\"}</code> every single time.</p><p>So you reinstall. Then you check the scope again, and it is still there, and the error is still the same. What has happened is that the scope you are looking at and the token you are sending were never attached to each other. Slack issued two credentials at the end of that OAuth flow, your install handler kept one of them, and the one it kept is the one that can never do this.",
"short_answer": """<p>Every <code>admin.*</code> method requires a <strong>user</strong> token. Not a bot token with more scopes &mdash; a different credential entirely. The scopes themselves make this unambiguous: <code>admin.apps:read</code> is documented as supporting <strong>User</strong> tokens only, and the same is true across the family. There is no configuration in which a <code>xoxb-</code> token holds an <code>admin.*</code> scope, so no amount of reinstalling the bot fixes this.</p>
<p>The user token exists. <code>oauth.v2.access</code> returns it as <code>authed_user.access_token</code>, alongside the bot token at the top level as <code>access_token</code>, with its own separate grant string in <code>authed_user.scope</code>. Install handlers routinely persist the top-level one and drop the rest, because for every other purpose the bot token is the one you want. The admin surface is the one place where it is useless.</p>
<p>So this is a pre-flight inventory rather than a runtime diagnosis, and the script below never calls an admin method to reach its conclusion. It asks <code>auth.test</code> what class each credential in your environment is, reads the grant from the <code>X-OAuth-Scopes</code> response header, and compares that against what the methods you intend to call are documented to require. If no user token is stored, every admin call is going to fail and you already know it.</p>
<p>One more requirement that catches people after they fix the token: <code>admin.apps:read</code> is documented as requiring installation by an Admin or Owner of an Enterprise organization <strong>on the whole org</strong>, not on an individual workspace.</p>""",
"problem": """<p>The confusion starts with a screen that is telling the truth in a way nobody reads carefully. App configuration lists scopes under two headings, <strong>Bot Token Scopes</strong> and <strong>User Token Scopes</strong>, and the <code>admin.*</code> scopes only ever appear under the second. If you added <code>admin.apps:read</code> you added it there, because that is the only place it can go. Nothing on that page then reminds you that the token you copied into your environment came from the other list.</p>
<p>The error compounds it. <code>not_allowed_token_type</code> says what is wrong with the credential you brought and nothing about the one it wanted, and <code>missing_scope</code> &mdash; which the same method returns in a different configuration &mdash; sends you straight back to the scopes screen where everything looks correct. Both errors are read as "add a scope and reinstall", and both survive that.</p>
<p>Underneath is an install handler that is perfectly reasonable everywhere else. The OAuth exchange returns an object with a bot token at the top level, a user token nested under <code>authed_user</code>, and a separate scope string for each. A store built for a bot app persists <code>access_token</code>, <code>bot_user_id</code>, <code>team.id</code> and moves on. Nothing in the app's daily work notices the omission, because posting messages, reading channels and publishing views all use the bot token. The gap surfaces months later when someone asks for a feature that needs the admin surface, and by then the installs that would have carried the user token have all already happened.</p>
<p>And there is a second gap behind the first, which is why fixing the storage sometimes is not enough. A user token carries admin authority only if the human who authorised the install had that authority, and only if the install was performed at the level the scope requires. <code>admin.apps:read</code> is documented as requiring an org Admin or Owner installing on the entire organization. A developer who clicks through the install themselves gets a user token with the scope string on it and no authority behind it, which fails differently and is <a href="/slack/not-an-admin/">a separate note</a>.</p>""",
"why": """<p><strong>This note asks a different question from the one next door, and the difference is the repair.</strong> <a href="/slack/not-allowed-token-type/">not_allowed_token_type</a> is about reading one method's refusal at runtime and working out which class of credential that method wanted; it assumes you hold several and are sending the wrong one. This note assumes you probably hold exactly one, and the finding is that the class the admin family requires is <em>absent from your environment altogether</em>. One is fixed by changing which variable the call reads. This one is fixed by changing the install handler and reinstalling, which is a deploy and a conversation with the customer's administrator.</p>
<p><strong>Nothing here calls an admin method, and that is a design decision rather than caution.</strong> The question "will <code>admin.users.list</code> accept this token" is answered completely by two facts that are both already available: what class the token is, and what class the method requires. Slack publishes the second. <code>auth.test</code> gives you the first for the cost of one request. Calling the method to find out adds no information, and the <code>admin.*</code> family is one where the neighbouring methods write &mdash; <code>admin.users.remove</code>, <code>admin.conversations.archive</code>, <code>admin.apps.restrict</code> &mdash; so a script that gets into the habit of probing that surface to see what happens is a script one typo away from doing something to a customer's organization.</p>
<p><strong>The class is read from <code>auth.test</code>, not from the prefix.</strong> A bot token's <code>auth.test</code> response carries a <code>bot_id</code>; a user token's does not. The prefix is a good first signal and <a href="/slack/invalid-auth-wrong-token-type/">has its own note</a>, but it is a string in your environment and the response is Slack's own answer about the credential you actually sent. Where they disagree, the response wins.</p>
<p><strong>The scope requirement is derived per method and printed, not summarised.</strong> "Admin methods need admin scopes" is not actionable. <code>admin.conversations.search &rarr; admin.conversations:read, user token</code> is. The map in the script derives the scope from the method family and the read or write half from the method name, and any method it does not recognise is reported as unknown with a pointer to the reference rather than guessed at, because a confidently wrong scope name sends someone to request a scope that does not exist.</p>
<p><strong>Write methods are named and refused, not planned for.</strong> If you pass <code>admin.users.remove</code> the script tells you it is a write and declines to include it in the plan. This is a read-only audit; the credential it recommends storing is a read credential, and quietly helping someone assemble the token for a destructive call is not the job.</p>
<p><strong>Nothing prints a credential.</strong> The inventory reports the class, the prefix family and the number of scopes granted. It never prints the token, never prints a prefix of the token beyond the documented class marker, and the install record it reads is expected to have the token values removed first &mdash; the finding is about which keys are present, and their values are irrelevant to it.</p>""",
"steps": [
 {"h": "Name every Slack credential your app holds, not just the one that broke",
  "body": """<p>Pass <code>--tokens</code> with the environment variable names: <code>SLACK_BOT_TOKEN,SLACK_USER_TOKEN,SLACK_APP_TOKEN</code>. The finding is usually the variable that is not on the list, so listing what you think you have is the first half of the check.</p>"""},
 {"h": "Let auth.test say what class each one is",
  "body": """<p><code>token_class</code> reads the response: a <code>bot_id</code> means a bot token, its absence with a <code>user_id</code> means a user token. A refusal is reported as unknown rather than guessed from the prefix, because a revoked user token and a bot token both fail to be admin-capable for different reasons.</p>"""},
 {"h": "Read the grant from the response header",
  "body": """<p><code>X-OAuth-Scopes</code> carries the complete granted list on every Web API response. <code>admin_capable</code> combines it with the class, and its most important behaviour is that a bot token is never capable no matter what the header says, because that scope cannot be attached to it.</p>"""},
 {"h": "Derive what each method you call actually requires",
  "body": """<p><code>requirement_for</code> turns <code>admin.apps.approved.list</code> into <code>admin.apps:read</code> on a user token. Unrecognised families come back <code>unknown</code> with a pointer to the method reference; write methods come back refused, because this audit does not help you assemble a credential for one.</p>"""},
 {"h": "Read your install record for the half that was dropped",
  "body": """<p><code>install_gap</code> takes your stored OAuth record with the token values removed and reports on key presence: no <code>authed_user</code>, no <code>authed_user.access_token</code>, an <code>authed_user.scope</code> with no admin scope in it, or <code>is_enterprise_install: false</code> where the scope documentation requires an org-level install.</p>"""},
 {"h": "Fix the install, not the call",
  "body": """<p>Request the <code>admin.*</code> scopes under <strong>User Token Scopes</strong>, persist <code>authed_user.access_token</code> and <code>authed_user.scope</code> next to the bot token rather than instead of it, and have an org Admin or Owner perform the install on the organization. Then route only <code>admin.*</code> calls at that credential.</p>"""},
],
"verify": """<p>Store the user token, re-run with both variables named, and the plan should resolve every admin method to a credential.</p>
<pre><code class="language-bash">python3 slack_admin_credential.py \\
  --tokens SLACK_BOT_TOKEN,SLACK_USER_TOKEN \\
  --methods admin.apps.approved.list,admin.conversations.search,conversations.list
# cred       SLACK_BOT_TOKEN   bot        xoxb  14 scope(s)  not admin capable
#            reason            admin.*:read is a user token scope and cannot be
#                              granted to a bot token in any configuration
# cred       SLACK_USER_TOKEN  user       xoxp   3 scope(s)  admin capable
# method     admin.apps.approved.list       needs admin.apps:read on a user token
#            served by        SLACK_USER_TOKEN
# method     admin.conversations.search     needs admin.conversations:read on a user token
#            served by        SLACK_USER_TOKEN
# method     conversations.list             needs channels:read on a bot or user token
#            served by        SLACK_BOT_TOKEN
# verdict    clean            3 method(s) resolved, 0 unserved
#   note:   no admin method was called to establish any of this</code></pre>""",
"code_intro": "Everything that decides anything is pure, and the network surface is one method wide: <code>READS</code> is <code>(\"auth.test\",)</code> and the tests assert it, because the promise that this script never touches the admin surface is worth checking mechanically. <code>token_class</code> reads Slack's own answer rather than a prefix. <code>admin_capable</code> is the function with the strong opinion: a bot token is not capable even when the scope header says otherwise, because that combination does not exist. <code>requirement_for</code> derives the scope and the token class per method and refuses to guess at families it does not know, and <code>install_gap</code> reads key presence in a redacted install record so the missing half of the grant shows up before anybody calls anything.",
"py_file": "slack_admin_credential.py",
"py": '''"""Decide whether you hold a credential the admin.* family will accept.

Read only, and deliberately narrower than it could be: it never calls an
admin method. The question here is not "did that method refuse me" but "does
the class of credential that method requires exist in my environment at all",
and that is settled by the token class plus the method's own documented
requirement. Calling admin.apps.approved.list to find out would add nothing,
and the family it lives in contains methods that write.

READS is the entire network surface of this script: auth.test, once per
credential named on the command line. The tests assert that.

Nothing here prints a credential. The inventory reports a class, a prefix
family and a count of granted scopes, and the install record it reads is
expected to arrive with the token values already removed.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_admin_credential")

API = "https://slack.com/api/"

# The whole network surface. One method, one class of question.
READS = ("auth.test",)

# Families whose scope name follows the documented admin.<family>:<read|write>
# shape and which this script is willing to state. Anything outside this tuple
# is reported as unknown with a pointer, because inventing a scope name sends
# somebody to request a permission that does not exist.
KNOWN_ADMIN_FAMILIES = ("apps", "barriers", "conversations", "inviteRequests",
                        "teams", "usergroups", "users", "workflows")

# Method name endings that identify a read. Everything else in the admin family
# is treated as a write and refused: this is a read-only audit and it does not
# help assemble the credential for admin.users.remove.
READ_SUFFIXES = ("list", "search", "lookup", "info", "get", "getentities",
                 "listassignments", "listchannels")

# Non-admin methods worth naming, so a mixed --methods list produces a whole
# plan rather than a plan with holes in it.
ORDINARY_SCOPES = {
    "conversations.list": "channels:read",
    "conversations.info": "channels:read",
    "conversations.history": "channels:history",
    "users.list": "users:read",
    "users.info": "users:read",
    "team.info": "team:read",
    "auth.test": "none",
}


def credential_shape(token):
    """The documented class marker of a token, and nothing else. Pure.

    Returns the prefix family only: xoxb, xoxp, xapp, xoxe or unknown. No
    character of the secret itself is returned by this or by anything that
    calls it.
    """
    text = str(token or "")
    for prefix in ("xoxb-", "xoxp-", "xapp-", "xoxe-", "xoxe."):
        if text.startswith(prefix):
            return prefix.rstrip("-.")
    return "unknown" if text else "absent"


def token_class(body):
    """What class of credential did Slack just answer for? Pure.

    Reads auth.test rather than the prefix, because the prefix is a string in
    your environment and the response is Slack's answer about the credential
    that actually arrived. Returns (klass, detail) with klass one of "bot",
    "user" or "unknown".
    """
    doc = body or {}
    if doc.get("ok") is not True:
        error = str(doc.get("error") or "unknown_error")
        return ("unknown", "auth.test refused this credential: " + error)
    if doc.get("bot_id"):
        return ("bot", "auth.test returned a bot_id")
    if doc.get("user_id"):
        return ("user", "auth.test returned a user_id and no bot_id")
    return ("unknown", "auth.test answered ok with neither bot_id nor user_id")


def granted_scopes(header_value):
    """The X-OAuth-Scopes header as a sorted list. Pure."""
    return sorted({s.strip() for s in str(header_value or "").split(",") if s.strip()})


def admin_capable(klass, scopes):
    """Can this credential ever serve an admin.* method? Pure.

    The opinionated one. A bot token is not capable even when a scope list
    handed to this function says otherwise, because admin.*:read is documented
    as a user token scope and that combination does not exist: if you are
    looking at it, you are looking at two different credentials.

    Returns (state, why) with state one of "capable", "wrong-class",
    "no-admin-scope" or "unknown".
    """
    admin_scopes = [s for s in (scopes or []) if str(s).startswith("admin.")]
    if klass == "bot":
        return ("wrong-class", "admin.*:read is a user token scope and cannot be "
                               "granted to a bot token in any configuration")
    if klass == "user":
        if admin_scopes:
            return ("capable", "%d admin scope(s) on a user token" % len(admin_scopes))
        return ("no-admin-scope", "a user token, but no admin.* scope was granted to "
                                  "it; request them under User Token Scopes")
    return ("unknown", "the class of this credential was not established, so its "
                       "capability is not known either")


def requirement_for(method):
    """What one method requires, derived rather than remembered. Pure.

    Returns (scope, klass, note). klass is "user", "bot-or-user" or "unknown".
    An admin write comes back refused, and an admin family this script has not
    been taught comes back unknown with a pointer, because a confidently wrong
    scope name is worse than an admission.
    """
    name = str(method or "").strip()
    if not name:
        return (None, "unknown", "no method given")
    if not name.startswith("admin."):
        scope = ORDINARY_SCOPES.get(name)
        if scope:
            return (scope, "bot-or-user", "an ordinary Web API method")
        return (None, "bot-or-user", "not an admin method; check the method "
                                     "reference for its scope")
    parts = name.split(".")
    if len(parts) < 3:
        return (None, "user", "an admin method, but the family could not be read "
                              "from the name")
    family = parts[1]
    tail = parts[-1].lower()
    if tail not in READ_SUFFIXES:
        return (None, "user", "this is an admin write; a read-only audit does not "
                              "plan a credential for it")
    if family not in KNOWN_ADMIN_FAMILIES:
        return (None, "user", "an admin read in a family this script does not name; "
                              "check the method reference for the exact scope")
    return ("admin.%s:read" % family, "user", "an admin read")


def serves(requirement, inventory):
    """Which stored credential can serve this method? Pure.

    inventory: [(env_name, klass, scopes, capability), ...]. Returns
    (env_name or None, why). The rule is class first and scope second, because
    a scope on the wrong class is not a partial answer, it is a different
    credential.
    """
    scope, klass, _note = requirement
    for name, cred_class, scopes, _capability in inventory or []:
        if klass == "user" and cred_class != "user":
            continue
        if klass == "bot-or-user" and cred_class not in ("bot", "user"):
            continue
        if scope and scope != "none" and scope not in (scopes or []):
            continue
        return (name, "class %s, scope %s" % (cred_class, scope or "unknown"))
    if klass == "user":
        return (None, "no user token is stored, so nothing here can serve an "
                      "admin method")
    return (None, "no stored credential holds the required scope")


def install_gap(record):
    """Read a redacted OAuth install record for the half that was dropped. Pure.

    Takes the stored oauth.v2.access response with the token values removed and
    reports on which keys are present. Values are never read, so a record that
    still contains a secret is not a hazard this function creates.
    """
    doc = record or {}
    out = []
    if "access_token" not in doc:
        out.append(("no-bot-token", "the record has no top level access_token, so "
                                    "this may not be an oauth.v2.access response"))
    authed = doc.get("authed_user")
    if not isinstance(authed, dict):
        out.append(("user-half-dropped", "no authed_user object; the user half of "
                                         "the grant was not persisted"))
    else:
        if "access_token" not in authed:
            out.append(("user-token-dropped", "authed_user exists but its "
                                              "access_token was not persisted"))
        scope = str(authed.get("scope") or "")
        if scope and not any(s.strip().startswith("admin.") for s in scope.split(",")):
            out.append(("no-admin-scope-asked", "the user grant carries no admin.* "
                                                "scope; it was never requested"))
    if doc.get("is_enterprise_install") is False:
        out.append(("workspace-level-install", "admin.apps:read is documented as "
                                               "requiring an org level install by an "
                                               "Admin or Owner of the organization"))
    return out


def plan_verdict(rows):
    """One line for the whole plan. Pure.

    rows: [(method, env_name or None), ...]. Refuses to say clean while any
    method has no credential behind it.
    """
    total = len(rows or [])
    unserved = [m for m, name in (rows or []) if not name]
    if not total:
        return ("empty", "no methods were named, so nothing was planned")
    if unserved:
        return ("%d unserved" % len(unserved),
                "%d of %d method(s) have no stored credential: %s"
                % (len(unserved), total, ", ".join(unserved[:4])))
    return ("clean", "%d method(s) resolved, 0 unserved" % total)


def auth_test(session, token):
    """One GET. Returns (body, granted scopes) and never returns the token."""
    r = session.get(API + "auth.test",
                    headers={"Authorization": "Bearer " + token}, timeout=30)
    scopes = granted_scopes(r.headers.get("X-OAuth-Scopes"))
    try:
        return (r.json(), scopes)
    except ValueError:
        return ({"ok": False, "error": "unparseable_body"}, scopes)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tokens", default="SLACK_BOT_TOKEN,SLACK_USER_TOKEN",
                    help="comma separated environment variable names holding your "
                         "Slack credentials")
    ap.add_argument("--methods", default="admin.apps.approved.list",
                    help="comma separated method names your app calls")
    ap.add_argument("--install-record", default="",
                    help="your stored oauth.v2.access record as JSON, with the token "
                         "values removed; only key presence is read")
    args = ap.parse_args()

    session = requests.Session()
    inventory = []
    for env_name in [n.strip() for n in args.tokens.split(",") if n.strip()]:
        token = os.environ.get(env_name)
        if not token:
            log.warning("cred       %-18s absent     set %s if your app holds one",
                        env_name, env_name)
            continue
        body, scopes = auth_test(session, token)
        klass, detail = token_class(body)
        capability, why = admin_capable(klass, scopes)
        level = log.info if capability in ("capable", "no-admin-scope") else log.warning
        level("cred       %-18s %-10s %-5s %2d scope(s)  %s", env_name, klass,
              credential_shape(token), len(scopes),
              "admin capable" if capability == "capable" else "not admin capable")
        log.info("           class read from %s", detail)
        if capability != "capable":
            log.warning("           reason           %s", why)
        inventory.append((env_name, klass, scopes, capability))

    rows = []
    for method in [m.strip() for m in args.methods.split(",") if m.strip()]:
        requirement = requirement_for(method)
        scope, klass, note = requirement
        if scope is None and klass == "user":
            log.warning("method     %-30s %s", method, note)
            rows.append((method, None))
            continue
        log.info("method     %-30s needs %s on a %s token", method,
                 scope or "an unnamed scope", "user" if klass == "user" else "bot or user")
        served, why = serves(requirement, inventory)
        if served:
            log.info("           served by        %s (%s)", served, why)
        else:
            log.warning("           unserved         %s", why)
        rows.append((method, served))

    if args.install_record:
        with open(args.install_record, encoding="utf-8") as handle:
            record = json.load(handle) or {}
        for code, why in install_gap(record):
            log.warning("install    %-18s %s", code, why)

    state, detail = plan_verdict(rows)
    if state == "clean":
        log.info("verdict    clean            %s", detail)
        log.info("  note:   no admin method was called to establish any of this")
        return 0
    log.warning("verdict    %-16s %s", state, detail)
    log.warning("  repair: request the admin.* scopes under User Token Scopes, not Bot "
                "Token Scopes; they cannot be attached to a bot token")
    log.warning("  repair: persist authed_user.access_token and authed_user.scope "
                "alongside the bot token, and route only admin.* calls at it")
    log.warning("  repair: have an org Admin or Owner install on the organization; "
                "admin.apps:read is documented as requiring that")
    log.warning("  note:   no admin method was called to establish any of this")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-admin-credential.mjs",
"js": '''/**
 * Decide whether you hold a credential the admin.* family will accept.
 *
 * Read only, and it never calls an admin method. The question is not "did
 * that method refuse me" but "does the class of credential it requires exist
 * in my environment at all", which is settled by the token class plus the
 * method's documented requirement. READS is the entire network surface of
 * this module, and the tests assert it.
 *
 * Nothing here prints a credential: the inventory reports a class, a prefix
 * family and a count of scopes, and the install record is expected to arrive
 * with its token values already removed.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// The whole network surface. One method, one class of question.
export const READS = ['auth.test'];

export const KNOWN_ADMIN_FAMILIES = ['apps', 'barriers', 'conversations',
  'inviteRequests', 'teams', 'usergroups', 'users', 'workflows'];

export const READ_SUFFIXES = ['list', 'search', 'lookup', 'info', 'get',
  'getentities', 'listassignments', 'listchannels'];

export const ORDINARY_SCOPES = {
  'conversations.list': 'channels:read',
  'conversations.info': 'channels:read',
  'conversations.history': 'channels:history',
  'users.list': 'users:read',
  'users.info': 'users:read',
  'team.info': 'team:read',
  'auth.test': 'none',
};

// The documented class marker and nothing else. No character of the secret.
export function credentialShape(token) {
  const text = String(token ?? '');
  for (const prefix of ['xoxb-', 'xoxp-', 'xapp-', 'xoxe-', 'xoxe.']) {
    if (text.startsWith(prefix)) return prefix.replace(/[-.]$/, '');
  }
  return text ? 'unknown' : 'absent';
}

// Slack's own answer about the credential that arrived, not the prefix.
export function tokenClass(body) {
  const doc = body ?? {};
  if (doc.ok !== true) {
    return ['unknown', `auth.test refused this credential: ${doc.error ?? 'unknown_error'}`];
  }
  if (doc.bot_id) return ['bot', 'auth.test returned a bot_id'];
  if (doc.user_id) return ['user', 'auth.test returned a user_id and no bot_id'];
  return ['unknown', 'auth.test answered ok with neither bot_id nor user_id'];
}

export function grantedScopes(headerValue) {
  const parts = String(headerValue ?? '').split(',').map((s) => s.trim()).filter(Boolean);
  return [...new Set(parts)].sort();
}

// A bot token is never capable, whatever a scope list says: that combination
// does not exist, so seeing it means you are looking at two credentials.
export function adminCapable(klass, scopes) {
  const admin = (scopes ?? []).filter((s) => String(s).startsWith('admin.'));
  if (klass === 'bot') {
    return ['wrong-class', 'admin.*:read is a user token scope and cannot be granted '
      + 'to a bot token in any configuration'];
  }
  if (klass === 'user') {
    if (admin.length) return ['capable', `${admin.length} admin scope(s) on a user token`];
    return ['no-admin-scope', 'a user token, but no admin.* scope was granted to it; '
      + 'request them under User Token Scopes'];
  }
  return ['unknown', 'the class of this credential was not established, so its '
    + 'capability is not known either'];
}

export function requirementFor(method) {
  const name = String(method ?? '').trim();
  if (!name) return [null, 'unknown', 'no method given'];
  if (!name.startsWith('admin.')) {
    const scope = ORDINARY_SCOPES[name];
    if (scope) return [scope, 'bot-or-user', 'an ordinary Web API method'];
    return [null, 'bot-or-user', 'not an admin method; check the method reference '
      + 'for its scope'];
  }
  const parts = name.split('.');
  if (parts.length < 3) {
    return [null, 'user', 'an admin method, but the family could not be read from the name'];
  }
  const family = parts[1];
  const tail = parts[parts.length - 1].toLowerCase();
  if (!READ_SUFFIXES.includes(tail)) {
    return [null, 'user', 'this is an admin write; a read-only audit does not plan a '
      + 'credential for it'];
  }
  if (!KNOWN_ADMIN_FAMILIES.includes(family)) {
    return [null, 'user', 'an admin read in a family this script does not name; check '
      + 'the method reference for the exact scope'];
  }
  return [`admin.${family}:read`, 'user', 'an admin read'];
}

// Class first, scope second: a scope on the wrong class is not a partial
// answer, it is a different credential.
export function serves(requirement, inventory) {
  const [scope, klass] = requirement;
  for (const [name, credClass, scopes] of inventory ?? []) {
    if (klass === 'user' && credClass !== 'user') continue;
    if (klass === 'bot-or-user' && credClass !== 'bot' && credClass !== 'user') continue;
    if (scope && scope !== 'none' && !(scopes ?? []).includes(scope)) continue;
    return [name, `class ${credClass}, scope ${scope ?? 'unknown'}`];
  }
  if (klass === 'user') {
    return [null, 'no user token is stored, so nothing here can serve an admin method'];
  }
  return [null, 'no stored credential holds the required scope'];
}

// Key presence only. Values are never read, so a record that still holds a
// secret is not a hazard this function creates.
export function installGap(record) {
  const doc = record ?? {};
  const out = [];
  if (!('access_token' in doc)) {
    out.push(['no-bot-token', 'the record has no top level access_token, so this may '
      + 'not be an oauth.v2.access response']);
  }
  const authed = doc.authed_user;
  if (!authed || typeof authed !== 'object') {
    out.push(['user-half-dropped', 'no authed_user object; the user half of the grant '
      + 'was not persisted']);
  } else {
    if (!('access_token' in authed)) {
      out.push(['user-token-dropped', 'authed_user exists but its access_token was '
        + 'not persisted']);
    }
    const scope = String(authed.scope ?? '');
    if (scope && !scope.split(',').some((s) => s.trim().startsWith('admin.'))) {
      out.push(['no-admin-scope-asked', 'the user grant carries no admin.* scope; it '
        + 'was never requested']);
    }
  }
  if (doc.is_enterprise_install === false) {
    out.push(['workspace-level-install', 'admin.apps:read is documented as requiring '
      + 'an org level install by an Admin or Owner of the organization']);
  }
  return out;
}

export function planVerdict(rows) {
  const total = (rows ?? []).length;
  const unserved = (rows ?? []).filter(([, name]) => !name).map(([m]) => m);
  if (!total) return ['empty', 'no methods were named, so nothing was planned'];
  if (unserved.length) {
    return [`${unserved.length} unserved`,
      `${unserved.length} of ${total} method(s) have no stored credential: `
      + `${unserved.slice(0, 4).join(', ')}`];
  }
  return ['clean', `${total} method(s) resolved, 0 unserved`];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function authTest(token) {
  const r = await fetch(`${API}auth.test`, { headers: { Authorization: `Bearer ${token}` } });
  const scopes = grantedScopes(r.headers.get('x-oauth-scopes'));
  try {
    return [await r.json(), scopes];
  } catch {
    return [{ ok: false, error: 'unparseable_body' }, scopes];
  }
}

async function main() {
  const args = process.argv.slice(2);
  const names = arg(args, '--tokens', 'SLACK_BOT_TOKEN,SLACK_USER_TOKEN')
    .split(',').map((s) => s.trim()).filter(Boolean);
  const methods = arg(args, '--methods', 'admin.apps.approved.list')
    .split(',').map((s) => s.trim()).filter(Boolean);

  const inventory = [];
  for (const envName of names) {
    const token = process.env[envName];
    if (!token) {
      console.warn(`cred       ${envName.padEnd(18)} absent     set ${envName} if your `
        + 'app holds one');
      continue;
    }
    // eslint-disable-next-line no-await-in-loop
    const [body, scopes] = await authTest(token);
    const [klass, detail] = tokenClass(body);
    const [capability, why] = adminCapable(klass, scopes);
    const line = `cred       ${envName.padEnd(18)} ${klass.padEnd(10)} `
      + `${credentialShape(token).padEnd(5)} ${String(scopes.length).padStart(2)} scope(s)  `
      + `${capability === 'capable' ? 'admin capable' : 'not admin capable'}`;
    if (capability === 'capable' || capability === 'no-admin-scope') console.log(line);
    else console.warn(line);
    console.log(`           class read from ${detail}`);
    if (capability !== 'capable') console.warn(`           reason           ${why}`);
    inventory.push([envName, klass, scopes, capability]);
  }

  const rows = [];
  for (const method of methods) {
    const requirement = requirementFor(method);
    const [scope, klass, note] = requirement;
    if (scope === null && klass === 'user') {
      console.warn(`method     ${method.padEnd(30)} ${note}`);
      rows.push([method, null]);
      continue;
    }
    console.log(`method     ${method.padEnd(30)} needs ${scope ?? 'an unnamed scope'} `
      + `on a ${klass === 'user' ? 'user' : 'bot or user'} token`);
    const [served, why] = serves(requirement, inventory);
    if (served) console.log(`           served by        ${served} (${why})`);
    else console.warn(`           unserved         ${why}`);
    rows.push([method, served]);
  }

  const recordPath = arg(args, '--install-record');
  if (recordPath) {
    const record = JSON.parse(await readFile(recordPath, 'utf8')) ?? {};
    for (const [code, why] of installGap(record)) {
      console.warn(`install    ${code.padEnd(18)} ${why}`);
    }
  }

  const [state, detail] = planVerdict(rows);
  if (state === 'clean') {
    console.log(`verdict    clean            ${detail}`);
    console.log('  note:   no admin method was called to establish any of this');
    return;
  }
  console.warn(`verdict    ${state.padEnd(16)} ${detail}`);
  console.warn('  repair: request the admin.* scopes under User Token Scopes, not Bot '
    + 'Token Scopes; they cannot be attached to a bot token');
  console.warn('  repair: persist authed_user.access_token and authed_user.scope '
    + 'alongside the bot token, and route only admin.* calls at it');
  console.warn('  repair: have an org Admin or Owner install on the organization; '
    + 'admin.apps:read is documented as requiring that');
  console.warn('  note:   no admin method was called to establish any of this');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two assertions carry the argument and the rest support them. The first is that a bot token holding a list of <code>admin.*</code> scopes is still reported as incapable, because that pairing does not exist in Slack and a script that believes the header over the class will send someone round the reinstall loop a fourth time. The second is mechanical: <code>READS</code> must contain <code>auth.test</code> and nothing else, so the claim that this script never touches the admin surface is checked rather than asserted in a comment. After that it is the refusals &mdash; an admin write is refused rather than planned, an unknown family declines to invent a scope name &mdash; and the install record, where the fixture is key-shaped and carries no token values at all.",
"test_py_file": "test_slack_admin_credential.py",
"test_py": '''from slack_admin_credential import (
    READS, admin_capable, credential_shape, granted_scopes, install_gap,
    plan_verdict, requirement_for, serves, token_class,
)

BOT = "xoxb-fake-1"
USER = "xoxp-fake-2"


def test_the_network_surface_is_one_read_method():
    assert READS == ("auth.test",)


def test_a_bot_token_is_never_admin_capable_whatever_the_header_says():
    state, why = admin_capable("bot", ["admin.apps:read", "admin.users:read"])
    assert state == "wrong-class"
    assert "cannot be granted to a bot token" in why


def test_a_user_token_with_an_admin_scope_is_capable():
    assert admin_capable("user", ["admin.apps:read"])[0] == "capable"


def test_a_user_token_without_one_is_a_different_finding():
    state, why = admin_capable("user", ["channels:read"])
    assert state == "no-admin-scope"
    assert "User Token Scopes" in why


def test_the_class_comes_from_the_response_not_the_prefix():
    assert token_class({"ok": True, "bot_id": "B1", "user_id": "U1"})[0] == "bot"
    assert token_class({"ok": True, "user_id": "U1"})[0] == "user"
    assert token_class({"ok": False, "error": "invalid_auth"})[0] == "unknown"


def test_a_refused_credential_is_unknown_rather_than_assumed():
    klass, detail = token_class({"ok": False, "error": "token_revoked"})
    assert klass == "unknown"
    assert "token_revoked" in detail


def test_the_shape_reports_a_class_marker_and_no_secret():
    assert credential_shape(BOT) == "xoxb"
    assert credential_shape(USER) == "xoxp"
    assert credential_shape("") == "absent"
    assert "fake" not in credential_shape(BOT)


def test_scopes_are_split_deduplicated_and_sorted():
    assert granted_scopes("users:read, channels:read ,users:read") == [
        "channels:read", "users:read"]


def test_an_admin_read_derives_its_scope_from_the_family():
    assert requirement_for("admin.apps.approved.list") == (
        "admin.apps:read", "user", "an admin read")
    assert requirement_for("admin.conversations.search")[0] == "admin.conversations:read"
    assert requirement_for("admin.teams.list")[0] == "admin.teams:read"


def test_an_admin_write_is_refused_rather_than_planned_for():
    scope, klass, note = requirement_for("admin.users.remove")
    assert scope is None and klass == "user"
    assert "read-only audit" in note


def test_an_unknown_admin_family_does_not_invent_a_scope_name():
    scope, _klass, note = requirement_for("admin.somethingNew.list")
    assert scope is None
    assert "does not name" in note


def test_an_ordinary_method_is_served_by_the_bot_token():
    inventory = [("SLACK_BOT_TOKEN", "bot", ["channels:read"], "wrong-class")]
    assert serves(requirement_for("conversations.list"), inventory)[0] == "SLACK_BOT_TOKEN"


def test_an_admin_method_is_not_served_by_a_bot_token_holding_the_scope():
    inventory = [("SLACK_BOT_TOKEN", "bot", ["admin.apps:read"], "wrong-class")]
    served, why = serves(requirement_for("admin.apps.approved.list"), inventory)
    assert served is None
    assert "no user token is stored" in why


def test_the_user_token_serves_it_once_stored():
    inventory = [("SLACK_BOT_TOKEN", "bot", ["channels:read"], "wrong-class"),
                 ("SLACK_USER_TOKEN", "user", ["admin.apps:read"], "capable")]
    assert serves(requirement_for("admin.apps.approved.list"),
                  inventory)[0] == "SLACK_USER_TOKEN"


def test_the_install_record_shows_the_half_that_was_dropped():
    codes = [c for c, _w in install_gap({"access_token": "", "team": {"id": "T1"}})]
    assert "user-half-dropped" in codes


def test_a_user_grant_without_admin_scopes_is_named_separately():
    record = {"access_token": "", "authed_user": {"id": "U1", "access_token": "",
                                                  "scope": "identify,channels:read"}}
    codes = [c for c, _w in install_gap(record)]
    assert codes == ["no-admin-scope-asked"]


def test_a_workspace_level_install_is_flagged_against_the_scope_requirement():
    record = {"access_token": "", "is_enterprise_install": False,
              "authed_user": {"access_token": "", "scope": "admin.apps:read"}}
    codes = [c for c, _w in install_gap(record)]
    assert codes == ["workspace-level-install"]


def test_a_complete_record_produces_nothing():
    record = {"access_token": "", "is_enterprise_install": True,
              "authed_user": {"id": "U1", "access_token": "", "scope": "admin.apps:read"}}
    assert install_gap(record) == []


def test_the_verdict_refuses_to_be_clean_with_an_unserved_method():
    state, detail = plan_verdict([("admin.apps.approved.list", None),
                                  ("conversations.list", "SLACK_BOT_TOKEN")])
    assert state == "1 unserved"
    assert "admin.apps.approved.list" in detail


def test_a_fully_served_plan_is_clean():
    assert plan_verdict([("conversations.list", "SLACK_BOT_TOKEN")])[0] == "clean"
''',
"test_js_file": "slack-admin-credential.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  READS, adminCapable, credentialShape, grantedScopes, installGap, planVerdict,
  requirementFor, serves, tokenClass,
} from './slack-admin-credential.mjs';

const BOT = 'xoxb-fake-1';
const USER = 'xoxp-fake-2';

test('the network surface is one read method', () => {
  assert.deepEqual(READS, ['auth.test']);
});

test('a bot token is never admin capable whatever the header says', () => {
  const [state, why] = adminCapable('bot', ['admin.apps:read', 'admin.users:read']);
  assert.equal(state, 'wrong-class');
  assert.match(why, /cannot be granted to a bot token/);
});

test('a user token with an admin scope is capable', () => {
  assert.equal(adminCapable('user', ['admin.apps:read'])[0], 'capable');
});

test('a user token without one is a different finding', () => {
  const [state, why] = adminCapable('user', ['channels:read']);
  assert.equal(state, 'no-admin-scope');
  assert.match(why, /User Token Scopes/);
});

test('the class comes from the response not the prefix', () => {
  assert.equal(tokenClass({ ok: true, bot_id: 'B1', user_id: 'U1' })[0], 'bot');
  assert.equal(tokenClass({ ok: true, user_id: 'U1' })[0], 'user');
  assert.equal(tokenClass({ ok: false, error: 'invalid_auth' })[0], 'unknown');
});

test('a refused credential is unknown rather than assumed', () => {
  const [klass, detail] = tokenClass({ ok: false, error: 'token_revoked' });
  assert.equal(klass, 'unknown');
  assert.match(detail, /token_revoked/);
});

test('the shape reports a class marker and no secret', () => {
  assert.equal(credentialShape(BOT), 'xoxb');
  assert.equal(credentialShape(USER), 'xoxp');
  assert.equal(credentialShape(''), 'absent');
  assert.equal(credentialShape(BOT).includes('fake'), false);
});

test('scopes are split, deduplicated and sorted', () => {
  assert.deepEqual(grantedScopes('users:read, channels:read ,users:read'),
    ['channels:read', 'users:read']);
});

test('an admin read derives its scope from the family', () => {
  assert.deepEqual(requirementFor('admin.apps.approved.list'),
    ['admin.apps:read', 'user', 'an admin read']);
  assert.equal(requirementFor('admin.conversations.search')[0], 'admin.conversations:read');
  assert.equal(requirementFor('admin.teams.list')[0], 'admin.teams:read');
});

test('an admin write is refused rather than planned for', () => {
  const [scope, klass, note] = requirementFor('admin.users.remove');
  assert.equal(scope, null);
  assert.equal(klass, 'user');
  assert.match(note, /read-only audit/);
});

test('an unknown admin family does not invent a scope name', () => {
  const [scope, , note] = requirementFor('admin.somethingNew.list');
  assert.equal(scope, null);
  assert.match(note, /does not name/);
});

test('an admin method is not served by a bot token holding the scope', () => {
  const inventory = [['SLACK_BOT_TOKEN', 'bot', ['admin.apps:read'], 'wrong-class']];
  const [served, why] = serves(requirementFor('admin.apps.approved.list'), inventory);
  assert.equal(served, null);
  assert.match(why, /no user token is stored/);
});

test('the user token serves it once stored', () => {
  const inventory = [['SLACK_BOT_TOKEN', 'bot', ['channels:read'], 'wrong-class'],
    ['SLACK_USER_TOKEN', 'user', ['admin.apps:read'], 'capable']];
  assert.equal(serves(requirementFor('admin.apps.approved.list'), inventory)[0],
    'SLACK_USER_TOKEN');
});

test('the install record shows the half that was dropped', () => {
  const codes = installGap({ access_token: '', team: { id: 'T1' } }).map(([c]) => c);
  assert.equal(codes.includes('user-half-dropped'), true);
});

test('a user grant without admin scopes is named separately', () => {
  const record = { access_token: '',
    authed_user: { id: 'U1', access_token: '', scope: 'identify,channels:read' } };
  assert.deepEqual(installGap(record).map(([c]) => c), ['no-admin-scope-asked']);
});

test('a workspace level install is flagged against the scope requirement', () => {
  const record = { access_token: '', is_enterprise_install: false,
    authed_user: { access_token: '', scope: 'admin.apps:read' } };
  assert.deepEqual(installGap(record).map(([c]) => c), ['workspace-level-install']);
});

test('the verdict refuses to be clean with an unserved method', () => {
  const [state, detail] = planVerdict([['admin.apps.approved.list', null],
    ['conversations.list', 'SLACK_BOT_TOKEN']]);
  assert.equal(state, '1 unserved');
  assert.match(detail, /admin\\.apps\\.approved\\.list/);
});

test('a fully served plan is clean', () => {
  assert.equal(planVerdict([['conversations.list', 'SLACK_BOT_TOKEN']])[0], 'clean');
});
''',
"faq": [
 ("I added admin.apps:read and reinstalled twice. Why does the bot token still not work?",
  "Because the scope and the token were never attached to each other. Slack lists scopes under two headings, and admin.* scopes only appear under User Token Scopes, so adding one adds it to the user grant. The install then returns two credentials: the bot token at the top level of the oauth.v2.access response, and the user token at authed_user.access_token with its own scope string. Reinstalling faithfully repeats that, and if your handler stores only the first one, the second one arrives and is discarded every time."),
 ("How is this different from the not_allowed_token_type note?",
  "That note is about runtime and about one method: you hold several credentials, a method refuses one of them, and the question is which class it wanted. This note is about your environment before any call happens, and the usual finding is that the class the admin family requires is not stored anywhere. The repairs are different sizes. One is changing which variable a call reads. This one is a change to the install handler, a redeploy, and asking the customer's org administrator to reinstall."),
 ("Why will the script not just call admin.apps.approved.list and tell me what happens?",
  "Because the answer is already available for less. The token class comes from auth.test and the method's requirement is documented, so calling it adds a request and no information. There is also a reason to keep a habit here: the admin family contains methods that remove users, archive conversations and restrict apps, and a diagnostic that pokes that surface to see what comes back is one typo away from doing something to a customer's organization. This one calls auth.test and stops."),
 ("The user token is stored now and admin calls still fail. What next?",
  "Read the error. not_allowed_token_type means the class is still wrong, so check which variable the call reads. missing_scope means the class is right and the grant is short, which is a scope request and a reinstall. not_an_admin means both are right and the human who authorised the install does not hold the role, which is a different note. feature_not_enabled means the customer is not on a plan that has the admin API at all, which is a third. The ladder is short and each rung has a different owner."),
 ("Does a service account help?",
  "Considerably, and for a reason that has nothing to do with this note's error. A user token carries one person's authority, so when that person changes role or leaves the organization the integration stops with no configuration change anywhere. Installing with a dedicated account that holds the admin role, rather than with a named individual's account, survives both. It does not change anything about the token class: the credential is still a user token and still comes back as authed_user.access_token."),
],
"related": [
 ("/slack/not-allowed-token-type/", "the runtime refusal, read per method"),
 ("/slack/not-an-admin/", "the class is right and the person is not"),
 ("/slack/bot-vs-user-scope-mixup/", "the scope landed on the other token"),
],
"citations": [CITE_SCOPE_ADMIN_APPS, CITE_OAUTH_V2, CITE_ADMIN_APPS_APPROVED,
              CITE_AUTH_TEST],
})

GUIDES.append({
"slug": "not-an-admin",
"title": "not_an_admin: workspace admin is not the org role",
"description": "The token class is right and the human is not. users.info returns two different is_admin fields, and admin.* checks the one under enterprise_user.",
"h1": "not_an_admin: workspace admin is not the org role",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack not_an_admin error admin api",
             "slack enterprise_user is_admin org owner",
             "slack users.info is_admin workspace vs org",
             "slack admin methods org owner required",
             "slack admin api installing user role"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a user token with users:read, and optionally the role you recorded for the installer at install time so the drift can be read",
"lead": "The token is a user token. The scopes are on it &mdash; you checked, twice. And <code>admin.teams.list</code> answers <code>{\"ok\": false, \"error\": \"not_an_admin\"}</code>, which is a strange thing to be told when you are, demonstrably, an admin: it says so on your own profile.</p><p>It does say so. It says so in the field that describes your role <em>in one workspace</em>. The methods you are calling are organization methods, they check an organization role, and that role lives in a different object in the same response. Both fields are called <code>is_admin</code>, one is <code>true</code>, and the one the method reads is the other one.",
"short_answer": """<p><code>admin.*</code> scopes can be granted to any user token regardless of who holds it. The methods do not rely on the grant: they check the caller's actual role when the call arrives, and they want an <strong>organization</strong> Admin or Owner. So a user token with a perfect scope list and an ordinary account behind it produces <code>not_an_admin</code> forever, and no reinstall changes that unless a different person performs it.</p>
<p>The confusion is a field name collision, and it is worth being precise about. <code>users.info</code> returns <code>is_admin</code>, <code>is_owner</code> and <code>is_primary_owner</code> at the root of the user object, and those describe the role <strong>in the workspace</strong> the call is scoped to. On Enterprise Grid the same user object carries an <code>enterprise_user</code> object, and <em>that</em> is where the org role lives: <code>enterprise_user.is_admin</code> and <code>enterprise_user.is_owner</code> are documented as indicating whether the user is an Admin or an Owner of the Enterprise organization. A workspace admin in forty workspaces is still not an org admin.</p>
<p>The script below reads the role rather than probing methods. <code>auth.test</code> gives you the caller's user id, <code>users.info</code> gives you both role objects, and the answer is a sentence about a person: this account holds the workspace admin role and not the org role, so every <code>admin.*</code> call it makes will be refused. It will also, given <code>users.list</code>, name the accounts that <em>do</em> hold the org role, because the useful output of this check is not "you cannot" but "ask one of these three people".</p>
<p>And there is a second finding hiding in the same read: a role can be lost after the install. Nothing in your configuration changes when that happens.</p>""",
"problem": """<p>The install worked, which is what makes this so slow to diagnose. OAuth completed, the consent screen listed the admin scopes and the person clicked through them, and the resulting token carries exactly the grant you asked for. Every check you can perform on the credential itself passes. <a href="/slack/admin-method-needs-user-token/">The class is right</a>, the scopes are right, and the call is still refused, so the natural next move is to look at the scopes again, which is the one place the answer is not.</p>
<p>Then the profile confirms your innocence. The developer doing the debugging opens Slack, sees the admin badge on their own account, and reasonably concludes that the error is wrong or that some other scope is missing. On Grid, a workspace admin genuinely is an admin: they can manage members and channels in that workspace, and the <code>is_admin</code> field on their user object is <code>true</code>. It is simply a different role from the one that governs organization-level methods, and nothing in the error string distinguishes them.</p>
<p>The second half of the problem is time. Role is not a property of the installation, it is a property of a person, and people move. The person who installed the app was an org admin in March and is a team lead in a different department by October, and on the day their role changes an integration that has run without incident for seven months starts returning <code>not_an_admin</code> with no deploy, no configuration change and nothing in any changelog to point at. Departures do the same thing more permanently.</p>
<p>There is a structural version of the same trouble. Installing with a named individual's account ties an organization-wide capability to one employee's continued role and continued employment, which is a fragile arrangement even when nobody's job changes: it makes the integration invisible to the organization's own access review, and it means the offboarding checklist that disables the account also breaks a production system nobody associated with that person.</p>""",
"why": """<p><strong>The finding is about a person, so the check reads a person.</strong> It would be possible to establish this by calling an admin method and catching <code>not_an_admin</code>, and that is a fine confirmation, but it produces one bit of information and no next step. Reading <code>users.info</code> for the installing account produces the whole sentence: this is the account, here is its workspace role, here is its org role, and here is the specific field the method is checking.</p>
<p><strong>Two <code>is_admin</code> fields is the entire trap, so the script never conflates them.</strong> <code>roles()</code> returns the workspace role and the org role separately and carries a third value, <code>org_role_known</code>, which is false when the user object has no <code>enterprise_user</code> at all. That absence has two quite different causes &mdash; the workspace is not part of an Enterprise organization, or the token cannot see the org identity &mdash; and neither of them means "not an admin". Reporting <code>unknown</code> is the honest answer and the script says so rather than rounding down.</p>
<p><strong>An unknown org role is never reported as a failure.</strong> This is the conservative rule that keeps the check usable in a multi-tenant audit: if the org role cannot be read, the verdict is that it cannot be read. A checker that treats missing evidence as a negative finding will tell every non-Grid customer that their installer lacks a role that does not exist on their plan, which is <a href="/slack/feature-not-enabled/">a different note entirely</a>.</p>
<p><strong>The candidate list is the actionable half.</strong> Knowing the installer lacks the role does not tell anybody what to do next; naming the accounts that hold it does. <code>candidates()</code> walks <code>users.list</code> and returns the accounts whose <code>enterprise_user</code> shows the org role, along with a coverage number, because a candidate list built from a page of members you could not fully read is a shorter list than the truth and should say so.</p>
<p><strong>Role drift is a first-class finding rather than an afterthought.</strong> If you recorded the installer's role at install time, <code>role_drift()</code> compares it to now and reports <code>lost</code>, which is the only diagnosis that explains an integration breaking on a Tuesday with no deploy. If you did not record it, that is itself the recommendation: store the role alongside the installation, and assert it at startup.</p>
<p><strong>Nothing here writes and nothing escalates itself.</strong> The repair is a human one &mdash; an org Admin or Owner re-runs the install, ideally from a dedicated service account with the role rather than from an individual &mdash; and the script prints it. There is no API that grants a role, and any script that appeared to offer one would be doing something else.</p>""",
"steps": [
 {"h": "Identify the account the token actually belongs to",
  "body": """<p><code>auth.test</code> returns <code>user_id</code> for a user token. Use that rather than a user id from your configuration, because the account that performed the install and the account you think performed it are not reliably the same person.</p>"""},
 {"h": "Read both role objects out of one users.info response",
  "body": """<p><code>roles</code> pulls the workspace role from the root of the user object and the org role from <code>enterprise_user</code>, and sets <code>org_role_known</code> to false when that object is absent. One call, two answers, kept apart.</p>"""},
 {"h": "Let the verdict say unknown when it is unknown",
  "body": """<p><code>satisfies</code> returns <code>yes</code>, <code>no</code> or <code>unknown</code>. It answers <code>no</code> only when the org role was readable and both flags were false. A workspace admin with no <code>enterprise_user</code> object is <code>unknown</code>, and the reason is printed.</p>"""},
 {"h": "Name the people who can fix it",
  "body": """<p>Pass <code>--team-id</code> and <code>candidates</code> walks <code>users.list</code> for accounts whose <code>enterprise_user</code> shows the org role, skipping bots and deactivated accounts. It reports coverage alongside the names, because a list built from partial data is a partial list.</p>"""},
 {"h": "Compare against the role you recorded at install time",
  "body": """<p><code>role_drift</code> takes the role you stored with the installation and reports <code>lost</code>, <code>gained</code>, <code>stable</code> or <code>unknown</code>. <code>lost</code> is the only finding that explains a working integration failing with no change on your side.</p>"""},
 {"h": "Reinstall as the right account, and assert it at startup",
  "body": """<p>Have an org Admin or Owner perform the install, preferably a dedicated service account holding the role rather than an individual's account. Then assert the org role on boot and fail loudly, so the next role change is a startup error rather than a silent afternoon.</p>"""},
],
"verify": """<p>Reinstall from an account that holds the org role and re-run. The role line should read <code>yes</code>, and the drift line should read <code>stable</code> on every run after that.</p>
<pre><code class="language-bash">python3 slack_admin_role.py --team-id T00000001 --recorded-role org-admin
# caller     U04XXXXXX        auth.test returned a user_id and no bot_id
# role       workspace        admin=true owner=false primary_owner=false
# role       organization     admin=false owner=false  (from enterprise_user)
# admin.*    no               the org role was readable and neither flag is set;
#                             workspace admin is a different role from org admin
# drift      lost             recorded org-admin at install time, reads member now
# candidate  U01AAAAAA        org owner
# candidate  U02BBBBBB        org admin
# coverage   partial          312 of 400 members carried an enterprise_user object
# verdict    1 finding(s)     the installing account cannot satisfy admin.* methods
#   repair: have one of the accounts above re-run the installation
#   repair: prefer a service account holding the org role over an individual's
#   repair: assert enterprise_user.is_admin at startup and fail loudly</code></pre>""",
"code_intro": "The reading is one <code>users.info</code> call and everything after it is pure. <code>roles</code> is the function that refuses to collapse two fields with the same name into one answer: the workspace role and the org role come back separately, with a flag saying whether the second was readable at all. <code>satisfies</code> is deliberately three-valued, because &ldquo;no <code>enterprise_user</code> object&rdquo; is not evidence of anything and must not be reported as a failing role. <code>candidates</code> turns the finding into a next step by naming the accounts that hold the role, and <code>role_drift</code> catches the version of this that arrives seven months after a successful install.",
"py_file": "slack_admin_role.py",
"py": '''"""Decide whether the human behind your user token can satisfy admin.* methods.

Read only. The token class question is a different script; this one assumes
the class is right and asks about the person, because admin.* scopes can be
granted to any user token while the methods check the caller's actual role at
call time.

The trap this is built around is a field name collision. users.info returns
is_admin, is_owner and is_primary_owner at the root of the user object, which
describe the role in the workspace the call is scoped to. On Enterprise Grid
the same object carries enterprise_user, and that is where the organization
role lives. Both fields are called is_admin. The methods read the second one.

The rule that keeps this honest in a multi-tenant audit: an org role that
could not be read is reported as unknown, never as absent.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_admin_role")

API = "https://slack.com/api/"

# This note explains exactly one of the refusals the admin surface produces.
# The others have their own, and pointing at them beats a shallow paragraph.
EXPLAINED_HERE = "not_an_admin"
OWNED_ELSEWHERE = {
    "not_allowed_token_type": "/slack/admin-method-needs-user-token/",
    "missing_scope": "/slack/missing-scope-on-read/",
    "feature_not_enabled": "/slack/feature-not-enabled/",
    "app_access_restricted": "/slack/app-access-restricted/",
    "ekm_access_denied": "/slack/ekm-access-denied/",
}


def roles(user):
    """Read both role objects out of one user object. Pure.

    Returns a dict with the workspace role, the organization role and
    org_role_known. The last one matters more than it looks: an absent
    enterprise_user object means either that this workspace is not part of an
    Enterprise organization or that the token cannot see the org identity, and
    neither of those is evidence that the person lacks a role.
    """
    doc = user or {}
    enterprise = doc.get("enterprise_user")
    known = isinstance(enterprise, dict)
    enterprise = enterprise if known else {}
    return {
        "user_id": doc.get("id"),
        "workspace_admin": bool(doc.get("is_admin")),
        "workspace_owner": bool(doc.get("is_owner")),
        "primary_owner": bool(doc.get("is_primary_owner")),
        "org_admin": bool(enterprise.get("is_admin")),
        "org_owner": bool(enterprise.get("is_owner")),
        "org_role_known": known,
        "is_bot": bool(doc.get("is_bot")),
        "deleted": bool(doc.get("deleted")),
    }


def satisfies(role):
    """Can this person satisfy an admin.* method? Pure.

    Three valued on purpose. "no" is returned only when the org role was
    readable and neither flag was set. Everything else that is not a yes is
    unknown, because a checker that reads missing evidence as a failure tells
    every non-Grid customer that their installer lacks a role their plan does
    not have.
    """
    doc = role or {}
    if doc.get("deleted"):
        return ("no", "the account is deactivated, so it holds no role at all")
    if doc.get("is_bot"):
        return ("no", "this is a bot account; admin.* methods want a human org "
                      "Admin or Owner")
    if doc.get("org_admin") or doc.get("org_owner"):
        return ("yes", "enterprise_user shows the organization role the methods check")
    if not doc.get("org_role_known"):
        if doc.get("workspace_admin") or doc.get("workspace_owner"):
            return ("unknown", "this account holds a workspace role, but the user "
                               "object carries no enterprise_user, so the "
                               "organization role could not be read")
        return ("unknown", "no enterprise_user object, so the organization role "
                           "could not be read either way")
    return ("no", "the org role was readable and neither flag is set; workspace "
                  "admin is a different role from org admin")


def role_drift(recorded, role):
    """Compare the role you stored at install time with the role now. Pure.

    Returns (state, detail). "lost" is the finding that explains an integration
    breaking with no deploy, no configuration change and nothing to bisect.
    """
    now = "org-owner" if (role or {}).get("org_owner") else (
        "org-admin" if (role or {}).get("org_admin") else "member")
    if not (role or {}).get("org_role_known"):
        now = "unknown"
    was = str(recorded or "").strip().lower()
    if not was:
        return ("unrecorded", "no role was stored with the installation, so drift "
                              "cannot be read; store it and this becomes readable")
    if now == "unknown":
        return ("unknown", "recorded %s at install time, and the org role cannot be "
                           "read now" % was)
    privileged = ("org-admin", "org-owner")
    if was in privileged and now not in privileged:
        return ("lost", "recorded %s at install time, reads %s now" % (was, now))
    if was not in privileged and now in privileged:
        return ("gained", "recorded %s at install time, reads %s now" % (was, now))
    return ("stable", "recorded %s, reads %s" % (was, now))


def candidates(members, limit=10):
    """Who in this workspace holds the organization role? Pure.

    Returns (people, coverage). Coverage is the honest half: a candidate list
    assembled from member objects that carried no enterprise_user is shorter
    than the truth, and a short list of people to ask is worse than a short
    list that says it is short.
    """
    people, seen, readable = [], 0, 0
    for member in members or []:
        role = roles(member)
        if role["is_bot"] or role["deleted"]:
            continue
        seen += 1
        if role["org_role_known"]:
            readable += 1
        if role["org_owner"]:
            people.append((role["user_id"], "org owner"))
        elif role["org_admin"]:
            people.append((role["user_id"], "org admin"))
    if not seen:
        coverage = ("none", "no readable member objects")
    elif readable == seen:
        coverage = ("full", "%d of %d members carried an enterprise_user object"
                            % (readable, seen))
    else:
        coverage = ("partial", "%d of %d members carried an enterprise_user object"
                               % (readable, seen))
    return (people[:limit], coverage)


def explains(error):
    """Is this refusal the one this note is about? Pure.

    Returns (state, pointer). Keeping the map here rather than in prose means
    a script that catches an unexpected error still hands the reader somewhere
    useful rather than silently mis-diagnosing it as a role problem.
    """
    name = str(error or "").strip()
    if name == EXPLAINED_HERE:
        return ("this-note", "a role problem: the class is right and the person "
                             "does not hold the organization role")
    if name in OWNED_ELSEWHERE:
        return ("elsewhere", OWNED_ELSEWHERE[name])
    if not name:
        return ("none", "no error was passed")
    return ("unknown", "not a refusal this note recognises; check the method "
                       "reference for its error list")


def verdict(state, drift):
    """One line for the whole check. Pure."""
    findings = (1 if state == "no" else 0) + (1 if drift == "lost" else 0)
    if state == "unknown":
        return ("inconclusive", "the organization role could not be read, so this "
                                "account was neither cleared nor faulted")
    if not findings:
        return ("clean", "the installing account holds the organization role")
    return ("%d finding(s)" % findings,
            "the installing account cannot satisfy admin.* methods")


def get(session, method, params=None):
    """One GET. Returns the parsed body."""
    r = session.get(API + method, params=params or {}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_USER_TOKEN",
                    help="environment variable holding the user token your admin "
                         "calls use")
    ap.add_argument("--team-id", default="",
                    help="workspace id, so the candidate scan can run")
    ap.add_argument("--recorded-role", default="",
                    help="the role you stored for the installer at install time: "
                         "org-owner, org-admin or member")
    ap.add_argument("--error", default="",
                    help="a refusal you captured, to check this note explains it")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("token      missing        set %s", args.token_env)
        return 2
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    if args.error:
        state, detail = explains(args.error)
        (log.info if state == "this-note" else log.warning)(
            "error      %-14s %s", state, detail)

    auth = get(session, "auth.test")
    if auth.get("ok") is not True:
        log.error("caller     unreadable     auth.test: %s", auth.get("error"))
        return 2
    user_id = auth.get("user_id")
    if auth.get("bot_id"):
        log.warning("caller     %-16s this is a bot token; admin.* wants a user "
                    "token held by an org Admin or Owner", user_id)
    log.info("caller     %-16s auth.test returned the account this token belongs to",
             user_id)

    body = get(session, "users.info", {"user": user_id})
    if body.get("ok") is not True:
        log.error("role       unreadable     users.info: %s", body.get("error"))
        return 2
    role = roles(body.get("user"))
    log.info("role       workspace        admin=%s owner=%s primary_owner=%s",
             str(role["workspace_admin"]).lower(), str(role["workspace_owner"]).lower(),
             str(role["primary_owner"]).lower())
    if role["org_role_known"]:
        log.info("role       organization     admin=%s owner=%s  (from enterprise_user)",
                 str(role["org_admin"]).lower(), str(role["org_owner"]).lower())
    else:
        log.warning("role       organization     not readable; the user object carries "
                    "no enterprise_user")

    state, why = satisfies(role)
    (log.info if state == "yes" else log.warning)("admin.*    %-16s %s", state, why)

    drift, detail = role_drift(args.recorded_role, role)
    (log.info if drift in ("stable", "gained") else log.warning)(
        "drift      %-16s %s", drift, detail)

    if args.team_id and state != "yes":
        page = get(session, "users.list", {"team_id": args.team_id, "limit": 200})
        people, coverage = candidates(page.get("members") or [])
        for user, label in people:
            log.info("candidate  %-16s %s", user, label)
        if not people:
            log.warning("candidate  none found       no member on this page showed the "
                        "organization role")
        log.info("coverage   %-16s %s", coverage[0], coverage[1])

    final, summary = verdict(state, drift)
    if final == "clean":
        log.info("verdict    clean            %s", summary)
        return 0
    log.warning("verdict    %-16s %s", final, summary)
    log.warning("  repair: have an org Admin or Owner re-run the installation so the "
                "user token belongs to a privileged account")
    log.warning("  repair: prefer a dedicated service account holding the org role "
                "over an individual's account, which changes when they do")
    log.warning("  repair: assert the org role at startup and fail loudly, so the next "
                "role change is a boot error rather than a silent afternoon")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-admin-role.mjs",
"js": '''/**
 * Decide whether the human behind your user token can satisfy admin.* methods.
 *
 * Read only. The token class question is a different module; this one assumes
 * the class is right and asks about the person, because admin.* scopes can be
 * granted to any user token while the methods check the caller's actual role
 * at call time.
 *
 * The trap this is built around is a field name collision: users.info returns
 * is_admin at the root of the user object for the workspace role, and again
 * inside enterprise_user for the organization role. The methods read the
 * second one. An org role that could not be read is reported as unknown,
 * never as absent.
 */

const API = 'https://slack.com/api/';

export const EXPLAINED_HERE = 'not_an_admin';
export const OWNED_ELSEWHERE = {
  not_allowed_token_type: '/slack/admin-method-needs-user-token/',
  missing_scope: '/slack/missing-scope-on-read/',
  feature_not_enabled: '/slack/feature-not-enabled/',
  app_access_restricted: '/slack/app-access-restricted/',
  ekm_access_denied: '/slack/ekm-access-denied/',
};

export function roles(user) {
  const doc = user ?? {};
  const known = doc.enterprise_user !== null && typeof doc.enterprise_user === 'object';
  const enterprise = known ? doc.enterprise_user : {};
  return {
    user_id: doc.id,
    workspace_admin: Boolean(doc.is_admin),
    workspace_owner: Boolean(doc.is_owner),
    primary_owner: Boolean(doc.is_primary_owner),
    org_admin: Boolean(enterprise.is_admin),
    org_owner: Boolean(enterprise.is_owner),
    org_role_known: known,
    is_bot: Boolean(doc.is_bot),
    deleted: Boolean(doc.deleted),
  };
}

// Three valued on purpose: "no" only when the org role was readable and
// neither flag was set.
export function satisfies(role) {
  const doc = role ?? {};
  if (doc.deleted) return ['no', 'the account is deactivated, so it holds no role at all'];
  if (doc.is_bot) {
    return ['no', 'this is a bot account; admin.* methods want a human org Admin or Owner'];
  }
  if (doc.org_admin || doc.org_owner) {
    return ['yes', 'enterprise_user shows the organization role the methods check'];
  }
  if (!doc.org_role_known) {
    if (doc.workspace_admin || doc.workspace_owner) {
      return ['unknown', 'this account holds a workspace role, but the user object '
        + 'carries no enterprise_user, so the organization role could not be read'];
    }
    return ['unknown', 'no enterprise_user object, so the organization role could not '
      + 'be read either way'];
  }
  return ['no', 'the org role was readable and neither flag is set; workspace admin is '
    + 'a different role from org admin'];
}

export function roleDrift(recorded, role) {
  const doc = role ?? {};
  let now = doc.org_owner ? 'org-owner' : (doc.org_admin ? 'org-admin' : 'member');
  if (!doc.org_role_known) now = 'unknown';
  const was = String(recorded ?? '').trim().toLowerCase();
  if (!was) {
    return ['unrecorded', 'no role was stored with the installation, so drift cannot '
      + 'be read; store it and this becomes readable'];
  }
  if (now === 'unknown') {
    return ['unknown', `recorded ${was} at install time, and the org role cannot be read now`];
  }
  const privileged = ['org-admin', 'org-owner'];
  if (privileged.includes(was) && !privileged.includes(now)) {
    return ['lost', `recorded ${was} at install time, reads ${now} now`];
  }
  if (!privileged.includes(was) && privileged.includes(now)) {
    return ['gained', `recorded ${was} at install time, reads ${now} now`];
  }
  return ['stable', `recorded ${was}, reads ${now}`];
}

export function candidates(members, limit = 10) {
  const people = [];
  let seen = 0;
  let readable = 0;
  for (const member of members ?? []) {
    const role = roles(member);
    if (role.is_bot || role.deleted) continue;
    seen += 1;
    if (role.org_role_known) readable += 1;
    if (role.org_owner) people.push([role.user_id, 'org owner']);
    else if (role.org_admin) people.push([role.user_id, 'org admin']);
  }
  let coverage;
  if (!seen) coverage = ['none', 'no readable member objects'];
  else if (readable === seen) {
    coverage = ['full', `${readable} of ${seen} members carried an enterprise_user object`];
  } else {
    coverage = ['partial', `${readable} of ${seen} members carried an enterprise_user object`];
  }
  return [people.slice(0, limit), coverage];
}

export function explains(error) {
  const name = String(error ?? '').trim();
  if (name === EXPLAINED_HERE) {
    return ['this-note', 'a role problem: the class is right and the person does not '
      + 'hold the organization role'];
  }
  if (name in OWNED_ELSEWHERE) return ['elsewhere', OWNED_ELSEWHERE[name]];
  if (!name) return ['none', 'no error was passed'];
  return ['unknown', 'not a refusal this note recognises; check the method reference '
    + 'for its error list'];
}

export function verdict(state, drift) {
  const findings = (state === 'no' ? 1 : 0) + (drift === 'lost' ? 1 : 0);
  if (state === 'unknown') {
    return ['inconclusive', 'the organization role could not be read, so this account '
      + 'was neither cleared nor faulted'];
  }
  if (!findings) return ['clean', 'the installing account holds the organization role'];
  return [`${findings} finding(s)`,
    'the installing account cannot satisfy admin.* methods'];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function read(token, method, params = {}) {
  const url = new URL(API + method);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_USER_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`token      missing        set ${tokenEnv}`);
    process.exitCode = 2;
    return;
  }

  const captured = arg(args, '--error');
  if (captured) {
    const [state, detail] = explains(captured);
    const line = `error      ${state.padEnd(14)} ${detail}`;
    if (state === 'this-note') console.log(line);
    else console.warn(line);
  }

  const auth = await read(token, 'auth.test');
  if (auth.ok !== true) {
    console.error(`caller     unreadable     auth.test: ${auth.error}`);
    process.exitCode = 2;
    return;
  }
  const userId = auth.user_id;
  if (auth.bot_id) {
    console.warn(`caller     ${String(userId).padEnd(16)} this is a bot token; admin.* `
      + 'wants a user token held by an org Admin or Owner');
  }
  console.log(`caller     ${String(userId).padEnd(16)} auth.test returned the account `
    + 'this token belongs to');

  const body = await read(token, 'users.info', { user: userId });
  if (body.ok !== true) {
    console.error(`role       unreadable     users.info: ${body.error}`);
    process.exitCode = 2;
    return;
  }
  const role = roles(body.user);
  console.log(`role       workspace        admin=${role.workspace_admin} `
    + `owner=${role.workspace_owner} primary_owner=${role.primary_owner}`);
  if (role.org_role_known) {
    console.log(`role       organization     admin=${role.org_admin} `
      + `owner=${role.org_owner}  (from enterprise_user)`);
  } else {
    console.warn('role       organization     not readable; the user object carries no '
      + 'enterprise_user');
  }

  const [state, why] = satisfies(role);
  const roleLine = `admin.*    ${state.padEnd(16)} ${why}`;
  if (state === 'yes') console.log(roleLine);
  else console.warn(roleLine);

  const [drift, detail] = roleDrift(arg(args, '--recorded-role'), role);
  const driftLine = `drift      ${drift.padEnd(16)} ${detail}`;
  if (drift === 'stable' || drift === 'gained') console.log(driftLine);
  else console.warn(driftLine);

  const teamId = arg(args, '--team-id');
  if (teamId && state !== 'yes') {
    const page = await read(token, 'users.list', { team_id: teamId, limit: 200 });
    const [people, coverage] = candidates(page.members ?? []);
    for (const [user, label] of people) {
      console.log(`candidate  ${String(user).padEnd(16)} ${label}`);
    }
    if (!people.length) {
      console.warn('candidate  none found       no member on this page showed the '
        + 'organization role');
    }
    console.log(`coverage   ${coverage[0].padEnd(16)} ${coverage[1]}`);
  }

  const [final, summary] = verdict(state, drift);
  if (final === 'clean') {
    console.log(`verdict    clean            ${summary}`);
    return;
  }
  console.warn(`verdict    ${final.padEnd(16)} ${summary}`);
  console.warn('  repair: have an org Admin or Owner re-run the installation so the '
    + 'user token belongs to a privileged account');
  console.warn("  repair: prefer a dedicated service account holding the org role over "
    + "an individual's account, which changes when they do");
  console.warn('  repair: assert the org role at startup and fail loudly, so the next '
    + 'role change is a boot error rather than a silent afternoon');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are user objects, which is all this check reads, and the assertion that matters most is the one about absence: a workspace admin with no <code>enterprise_user</code> object must come back <code>unknown</code> rather than <code>no</code>, because that shape is what every non-Grid workspace looks like and a checker that faults it will fault every customer on a smaller plan. The mirror of it is that a member with a readable org role and both flags false must come back <code>no</code>, since that is the actual finding. After those, the drift table &mdash; where losing the role has to be distinguishable from never having recorded one &mdash; and the candidate scan, which has to report partial coverage rather than pretending a short list is the whole list.",
"test_py_file": "test_slack_admin_role.py",
"test_py": '''from slack_admin_role import (
    candidates, explains, role_drift, roles, satisfies, verdict,
)

ORG_ADMIN = {"id": "U1", "is_admin": True,
             "enterprise_user": {"id": "W1", "is_admin": True, "is_owner": False}}
ORG_MEMBER = {"id": "U2", "is_admin": True,
              "enterprise_user": {"id": "W2", "is_admin": False, "is_owner": False}}
NO_ENTERPRISE = {"id": "U3", "is_admin": True, "is_owner": False}


def test_the_two_is_admin_fields_are_read_separately():
    role = roles(ORG_MEMBER)
    assert role["workspace_admin"] is True
    assert role["org_admin"] is False
    assert role["org_role_known"] is True


def test_an_org_admin_satisfies_the_methods():
    assert satisfies(roles(ORG_ADMIN))[0] == "yes"


def test_a_workspace_admin_with_a_readable_org_role_does_not():
    state, why = satisfies(roles(ORG_MEMBER))
    assert state == "no"
    assert "workspace admin is a different role" in why


def test_a_missing_enterprise_user_is_unknown_and_never_a_failure():
    state, why = satisfies(roles(NO_ENTERPRISE))
    assert state == "unknown"
    assert "could not be read" in why


def test_a_deactivated_account_holds_no_role():
    assert satisfies(roles({"id": "U9", "deleted": True}))[0] == "no"


def test_a_bot_account_is_refused_with_its_own_reason():
    state, why = satisfies(roles({"id": "B1", "is_bot": True}))
    assert state == "no"
    assert "bot account" in why


def test_an_org_owner_counts_even_without_the_admin_flag():
    owner = {"id": "U4", "enterprise_user": {"is_admin": False, "is_owner": True}}
    assert satisfies(roles(owner))[0] == "yes"


def test_losing_the_role_is_the_finding_that_explains_a_silent_break():
    state, detail = role_drift("org-admin", roles(ORG_MEMBER))
    assert state == "lost"
    assert "reads member now" in detail


def test_never_recording_the_role_is_not_the_same_as_losing_it():
    assert role_drift("", roles(ORG_MEMBER))[0] == "unrecorded"


def test_drift_is_unknown_when_the_org_role_cannot_be_read():
    assert role_drift("org-admin", roles(NO_ENTERPRISE))[0] == "unknown"


def test_a_stable_role_says_so():
    assert role_drift("org-admin", roles(ORG_ADMIN))[0] == "stable"


def test_candidates_name_the_people_who_can_reinstall():
    members = [ORG_ADMIN, ORG_MEMBER,
               {"id": "U5", "enterprise_user": {"is_owner": True}},
               {"id": "B2", "is_bot": True,
                "enterprise_user": {"is_admin": True}}]
    people, coverage = candidates(members)
    assert ("U1", "org admin") in people
    assert ("U5", "org owner") in people
    assert coverage[0] == "full"


def test_candidate_coverage_is_partial_when_members_lack_the_object():
    people, coverage = candidates([ORG_ADMIN, NO_ENTERPRISE])
    assert people == [("U1", "org admin")]
    assert coverage[0] == "partial"
    assert "1 of 2" in coverage[1]


def test_this_note_explains_one_refusal_and_hands_over_the_rest():
    assert explains("not_an_admin")[0] == "this-note"
    assert explains("feature_not_enabled") == ("elsewhere", "/slack/feature-not-enabled/")
    assert explains("nonsense_error")[0] == "unknown"


def test_the_verdict_is_inconclusive_rather_than_clean_when_unknown():
    assert verdict("unknown", "unrecorded")[0] == "inconclusive"


def test_two_findings_are_counted_together():
    assert verdict("no", "lost")[0] == "2 finding(s)"


def test_a_privileged_account_with_a_stable_role_is_clean():
    assert verdict("yes", "stable")[0] == "clean"
''',
"test_js_file": "slack-admin-role.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  candidates, explains, roleDrift, roles, satisfies, verdict,
} from './slack-admin-role.mjs';

const ORG_ADMIN = { id: 'U1', is_admin: true,
  enterprise_user: { id: 'W1', is_admin: true, is_owner: false } };
const ORG_MEMBER = { id: 'U2', is_admin: true,
  enterprise_user: { id: 'W2', is_admin: false, is_owner: false } };
const NO_ENTERPRISE = { id: 'U3', is_admin: true, is_owner: false };

test('the two is_admin fields are read separately', () => {
  const role = roles(ORG_MEMBER);
  assert.equal(role.workspace_admin, true);
  assert.equal(role.org_admin, false);
  assert.equal(role.org_role_known, true);
});

test('an org admin satisfies the methods', () => {
  assert.equal(satisfies(roles(ORG_ADMIN))[0], 'yes');
});

test('a workspace admin with a readable org role does not', () => {
  const [state, why] = satisfies(roles(ORG_MEMBER));
  assert.equal(state, 'no');
  assert.match(why, /workspace admin is a different role/);
});

test('a missing enterprise_user is unknown and never a failure', () => {
  const [state, why] = satisfies(roles(NO_ENTERPRISE));
  assert.equal(state, 'unknown');
  assert.match(why, /could not be read/);
});

test('a deactivated account holds no role', () => {
  assert.equal(satisfies(roles({ id: 'U9', deleted: true }))[0], 'no');
});

test('a bot account is refused with its own reason', () => {
  const [state, why] = satisfies(roles({ id: 'B1', is_bot: true }));
  assert.equal(state, 'no');
  assert.match(why, /bot account/);
});

test('an org owner counts even without the admin flag', () => {
  const owner = { id: 'U4', enterprise_user: { is_admin: false, is_owner: true } };
  assert.equal(satisfies(roles(owner))[0], 'yes');
});

test('losing the role is the finding that explains a silent break', () => {
  const [state, detail] = roleDrift('org-admin', roles(ORG_MEMBER));
  assert.equal(state, 'lost');
  assert.match(detail, /reads member now/);
});

test('never recording the role is not the same as losing it', () => {
  assert.equal(roleDrift('', roles(ORG_MEMBER))[0], 'unrecorded');
});

test('drift is unknown when the org role cannot be read', () => {
  assert.equal(roleDrift('org-admin', roles(NO_ENTERPRISE))[0], 'unknown');
});

test('candidates name the people who can reinstall', () => {
  const members = [ORG_ADMIN, ORG_MEMBER,
    { id: 'U5', enterprise_user: { is_owner: true } },
    { id: 'B2', is_bot: true, enterprise_user: { is_admin: true } }];
  const [people, coverage] = candidates(members);
  assert.deepEqual(people, [['U1', 'org admin'], ['U5', 'org owner']]);
  assert.equal(coverage[0], 'full');
});

test('candidate coverage is partial when members lack the object', () => {
  const [people, coverage] = candidates([ORG_ADMIN, NO_ENTERPRISE]);
  assert.deepEqual(people, [['U1', 'org admin']]);
  assert.equal(coverage[0], 'partial');
  assert.match(coverage[1], /1 of 2/);
});

test('this note explains one refusal and hands over the rest', () => {
  assert.equal(explains('not_an_admin')[0], 'this-note');
  assert.deepEqual(explains('feature_not_enabled'),
    ['elsewhere', '/slack/feature-not-enabled/']);
  assert.equal(explains('nonsense_error')[0], 'unknown');
});

test('the verdict is inconclusive rather than clean when unknown', () => {
  assert.equal(verdict('unknown', 'unrecorded')[0], 'inconclusive');
});

test('two findings are counted together', () => {
  assert.equal(verdict('no', 'lost')[0], '2 finding(s)');
});

test('a privileged account with a stable role is clean', () => {
  assert.equal(verdict('yes', 'stable')[0], 'clean');
});
''',
"faq": [
 ("My Slack profile says I am an admin. Why does Slack say I am not?",
  "Because there are two roles with almost the same name. The is_admin field at the root of the user object describes your role in one workspace, and it is the one your profile badge reflects. Organization methods check the role in the enterprise_user object, which is a different field describing whether you are an Admin or Owner of the whole Enterprise organization. Somebody can be a workspace admin in every workspace an organization has and still not hold the org role, and admin.* refuses them."),
 ("The user object has no enterprise_user at all. Does that mean no role?",
  "No, and treating it as one is the main way this check goes wrong. That object is absent for two quite different reasons: the workspace is not part of an Enterprise organization, or the token could not read the org identity. Neither is evidence about the person. The script reports unknown, and if the workspace is genuinely not on Enterprise Grid the real answer is that the admin API is not available at all on that plan, which is its own note."),
 ("It worked for seven months and then stopped, with no deploy. What changed?",
  "Almost certainly the person. Role is a property of a human, not of the installation, so when the account that authorised the install loses the org role or leaves the organization, every admin.* call starts returning not_an_admin with nothing on your side having changed. That is what the drift line is for, and it can only be read if you stored the role at install time. If you did not, storing it now makes the next occurrence diagnosable in one line."),
 ("Can I grant the role from the API to fix this?",
  "No, and nothing in this section would. Role assignment is an administrative action inside the customer's organization, and it is theirs to make. The most useful thing an integration can do is produce the sentence its administrator needs: this account holds the workspace role and not the organization role, and here are the accounts that do hold it. That is the candidate list, and it turns a failed API call into a request somebody can action."),
 ("Should we install with a service account instead of a person's account?",
  "For anything organization-wide, yes. An individual's account ties a production capability to one person's role and one person's continued employment, and the offboarding process that disables the account will break the integration without anybody connecting the two. A dedicated account holding the org role survives reorganisations and departures, and it appears in the organization's own access review as what it is, which an engineer's personal token does not."),
],
"related": [
 ("/slack/admin-method-needs-user-token/", "the class before the person"),
 ("/slack/feature-not-enabled/", "the plan before either"),
 ("/slack/missing-scope-on-read/", "the refusal that names what it wants"),
],
"citations": [CITE_USER_OBJECT, CITE_USERS_INFO, CITE_ADMIN_TEAMS_LIST, CITE_USERS_LIST],
})

GUIDES.append({
"slug": "feature-not-enabled",
"title": "feature_not_enabled: the admin API needs Enterprise",
"description": "Nobody is wrong here: the customer is not on a plan that has the admin surface. Measure capability per tenant and never store an unknown as an absence.",
"h1": "feature_not_enabled: the admin API needs Enterprise",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack feature_not_enabled admin api",
             "slack admin api enterprise grid only",
             "slack admin.teams.list feature_not_enabled",
             "slack multi tenant feature detection",
             "slack admin api fallback conversations.list"],
"deps": "Python 3.9+ with requests, or Node.js 18+; one user token per installation you want to measure, as a JSON list, each with admin.teams:read if you want the probe to be conclusive",
"lead": "The token is a user token, the human behind it is an org owner, the scopes are exactly right, and <code>admin.teams.list</code> answers <code>{\"ok\": false, \"error\": \"feature_not_enabled\"}</code>. You have now spent an afternoon fixing two things that were never broken.</p><p>This customer is on Business+. The admin API is an Enterprise Grid surface, and on a plan that does not include it there is no configuration &mdash; no scope, no role, no reinstall &mdash; that makes those methods answer. The interesting version of this is not the afternoon; it is the multi-tenant app that ships an admin-powered feature to four hundred installations and discovers on the third day that a hundred and eighty of them cannot use it.",
"short_answer": """<p>The <code>admin.*</code> families are Enterprise Grid features. On a workspace that is not part of an Enterprise organization they return <code>feature_not_enabled</code> regardless of who calls them with which scopes, and <code>admin.apps.restricted.list</code> is documented as available only on the Enterprise plan. This is a property of the customer's contract, not of your integration.</p>
<p><strong>The plan itself is not readable.</strong> There is no documented read method that returns it: <code>team.info</code> comes back with <code>id</code>, <code>name</code>, <code>domain</code>, <code>email_domain</code>, <code>icon</code> and, on Grid, <code>enterprise_id</code> and <code>enterprise_name</code>, and nothing about billing or tier. So capability has to be <em>measured</em> rather than looked up: a non-null <code>enterprise_id</code> on <code>auth.test</code> is a signal that the workspace sits inside an organization, and a single <code>admin.teams.list?limit=1</code> probe turns that signal into an answer.</p>
<p>The whole value of the script below is in one rule it refuses to break. <code>feature_not_enabled</code> means the surface is unavailable. <code>not_an_admin</code>, <code>not_allowed_token_type</code> and <code>missing_scope</code> mean the probe never reached the question, and recording any of those as &ldquo;this customer is not on Enterprise&rdquo; poisons the matrix with a permanent false negative that no later run corrects, because the feature is now gated off and never probed again.</p>
<p>Then degrade rather than fail. <code>conversations.list</code> for <code>admin.conversations.search</code>, <code>users.list</code> for <code>admin.users.list</code>, <code>team.info</code> for <code>admin.teams.list</code> &mdash; each narrower, each real.</p>""",
"problem": """<p>A single-tenant integration meets this once, spends an afternoon on it and is done. A multi-tenant app meets it as an architecture problem, because availability now varies per customer and the code has no vocabulary for that. The feature was built against one workspace &mdash; usually the developer's own Grid sandbox, where everything works &mdash; and the assumption that the admin surface exists is baked into a call path with no branch in it.</p>
<p>What ships is an outage that only some customers see. The nightly job that reconciles channels across the organization runs fine for the Enterprise tenants and throws for everybody else, and because the error arrives inside a loop over installations, the log fills with a stack trace whose only distinguishing feature is a tenant id. Support hears "the app is broken" from a subset of customers that nobody can characterise, which is the most expensive shape a bug can have.</p>
<p>The naive fix makes it worse. Somebody adds a <code>try</code> around the call and sets <code>admin_available = False</code> in the handler, which is correct exactly when the error was <code>feature_not_enabled</code> and wrong every other time. A tenant whose token was briefly missing a scope, or whose admin account lost its role for a week, gets permanently marked as not-Enterprise. The flag is stored, the feature is hidden, the probe never runs again because the flag says not to, and the customer's own administrator cannot work out why the capability they are paying for is invisible.</p>
<p>Underneath all of it is the thing that cannot be read: the plan. There is no method that answers "what tier is this workspace on", so an app cannot look up the answer at install time and be done. It has to conduct an experiment, interpret the result carefully, and re-run the experiment when the result was inconclusive &mdash; which is a different discipline from feature detection against a documented capability list.</p>""",
"why": """<p><strong>Capability is measured, and the measurement is one cheap read.</strong> <code>admin.teams.list?limit=1</code> is a Tier 2 read that returns a single row on a Grid organization and <code>feature_not_enabled</code> where the surface does not exist. One request per installation, at install time, answers the question for good &mdash; and the answer is stored, so the feature is gated on a measured fact rather than on an assumption made in a sprint planning meeting.</p>
<p><strong>The <code>enterprise_id</code> on <code>auth.test</code> is a signal and is labelled as one.</strong> Its absence strongly suggests a workspace outside any organization, and its presence suggests the opposite, but neither is the capability. Treating the signal as the answer is how an app decides a customer has the admin surface and then fails on the first call anyway. The script prints the signal, prints the probe, and only the probe feeds the gate.</p>
<p><strong>An unknown is never stored as an absence, and that is the whole discipline.</strong> <code>capability()</code> distinguishes <code>unavailable-plan</code> from <code>unknown-role</code>, <code>unknown-class</code>, <code>unknown-scope</code> and <code>unknown-transient</code>, and <code>gate()</code> turns only the first into an off switch. Everything else becomes <code>retry</code>, which means the tenant is probed again rather than written off. A false <em>off</em> is invisible and permanent; a false <em>retry</em> costs one request.</p>
<p><strong>The fallbacks are named per method, with what they cost.</strong> "Degrade gracefully" is not an instruction. <code>conversations.list</code> in place of <code>admin.conversations.search</code> sees only the conversations the token can see, in one workspace, which for most tenants is most of what the feature needed. Printing the replacement and the loss together lets somebody decide whether the degraded version is worth building, which is the actual decision.</p>
<p><strong>The refusals that belong to other notes are handed over rather than absorbed.</strong> A probe that comes back <code>not_an_admin</code> is a real finding, just not this one, and the script says which note owns it. This matters more here than elsewhere, because this is the check people run first when an admin call fails, and its most common honest output is "this is not a plan problem".</p>
<p><strong>Nothing writes, and the probe is chosen because it cannot.</strong> <code>admin.teams.list</code> reads. It is the smallest question that produces <code>feature_not_enabled</code>, and it does not enumerate anything sensitive at <code>limit=1</code>.</p>""",
"steps": [
 {"h": "Read the signal before you spend a request",
  "body": """<p><code>grid_signal</code> reads <code>enterprise_id</code> from <code>auth.test</code>. A null value is a strong hint that no admin method will work, and the script prints it as a hint. It never feeds the stored flag, because a hint that gates a feature is an assumption with extra steps.</p>"""},
 {"h": "Probe once, with the cheapest admin read there is",
  "body": """<p><code>admin.teams.list?limit=1</code>. One row, Tier 2, and its error list contains <code>feature_not_enabled</code> explicitly. That single response is the measurement, and everything downstream reads it rather than re-deriving it.</p>"""},
 {"h": "Classify the refusal into available, unavailable or unknown",
  "body": """<p><code>capability</code> returns one of seven states. Only <code>unavailable-plan</code> comes from <code>feature_not_enabled</code>; <code>not_an_admin</code>, <code>not_allowed_token_type</code> and <code>missing_scope</code> each get their own <code>unknown-</code> state and a pointer to the note that owns them.</p>"""},
 {"h": "Store a flag, and refuse to store an unknown as an absence",
  "body": """<p><code>gate</code> maps the capability to <code>on</code>, <code>off</code> or <code>retry</code>. Only a measured <code>feature_not_enabled</code> produces <code>off</code>. Everything inconclusive produces <code>retry</code>, so the tenant is asked again instead of being quietly written off forever.</p>"""},
 {"h": "Print the fallback and what it costs",
  "body": """<p><code>fallback_for</code> maps each admin method your feature uses to its non-admin equivalent and states the loss: one workspace instead of the organization, visible conversations instead of all of them, no cross-workspace search.</p>"""},
 {"h": "Gate the feature on the stored flag, and say why in the product",
  "body": """<p>A tenant with <code>off</code> should see &ldquo;this requires Enterprise Grid&rdquo; rather than a spinner or a stack trace. A tenant with <code>retry</code> should see the feature as pending, not missing, and be re-probed on the next run.</p>"""},
],
"verify": """<p>Run across every installation you hold. The matrix should contain no <code>unknown-</code> rows: each tenant is either measured available or measured unavailable, and anything else is a probe that needs a better credential before it means anything.</p>
<pre><code class="language-bash">python3 slack_admin_capability.py --installs installs.json \\
  --methods admin.conversations.search,admin.users.list
# tenant     acme-grid        signal=grid       capability=available     gate=on
# tenant     bolt-co          signal=not-grid   capability=unavailable-plan gate=off
#            note             feature_not_enabled; no scope or role changes this
# tenant     crate-ltd        signal=grid       capability=unknown-role  gate=retry
#            see also         /slack/not-an-admin/
# fallback   admin.conversations.search -> conversations.list
#            loses            one workspace instead of the organization, and only
#                             conversations this token can already see
# fallback   admin.users.list -> users.list
#            loses            one workspace instead of every workspace in the org
# matrix     3 tenant(s)      1 available, 1 unavailable, 1 unknown
# verdict    1 unknown        re-probe before gating; an unknown is not an absence
#   note:   the plan itself is not readable; team.info returns no billing field</code></pre>""",
"code_intro": "One probe per tenant and the rest is bookkeeping with an opinion. <code>capability</code> is the classifier and it is deliberately verbose in its unknown states, because the difference between &ldquo;this customer is not on Enterprise&rdquo; and &ldquo;this probe never got that far&rdquo; is the difference between a correct feature gate and a permanent invisible one. <code>gate</code> encodes that as a rule with tests: only <code>feature_not_enabled</code> turns a feature off. <code>grid_signal</code> is labelled a signal everywhere it appears, <code>plan_is_readable</code> exists to record that the plan is not available from any documented read method, and <code>fallback_for</code> names the narrower call and what it costs.",
"py_file": "slack_admin_capability.py",
"py": '''"""Measure, per installation, whether the admin API surface exists at all.

Read only, one probe per tenant. The admin.* families are Enterprise Grid
features, and a workspace on a smaller plan answers feature_not_enabled no
matter who calls them with what scopes. That is a property of the customer's
contract rather than of your integration, so the job here is to measure it and
store it, not to fix it.

The plan is not readable. No documented read method returns it: team.info
comes back with id, name, domain, email_domain, icon and, on Grid,
enterprise_id and enterprise_name, and nothing about tier or billing. So
capability is an experiment: one admin.teams.list?limit=1 per installation.

The rule this script exists to enforce: only feature_not_enabled means the
surface is unavailable. not_an_admin, not_allowed_token_type and missing_scope
mean the probe never reached the question, and storing any of them as an
absence creates a permanent false negative that no later run corrects, because
the feature is gated off and never probed again.
"""
import argparse
import json
import logging
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_admin_capability")

API = "https://slack.com/api/"

# The cheapest admin read that produces the answer. Tier 2, one row, and
# feature_not_enabled is in its documented error list.
PROBE = ("admin.teams.list", {"limit": 1})

# Refusals that mean the probe never reached the question, mapped to the note
# that owns each one. Every value here becomes an unknown, never an absence.
NOT_THIS_QUESTION = {
    "not_an_admin": "/slack/not-an-admin/",
    "not_allowed_token_type": "/slack/admin-method-needs-user-token/",
    "missing_scope": "/slack/missing-scope-on-read/",
    "accesslimited": "/slack/accesslimited-ip-allowlist/",
    "ekm_access_denied": "/slack/ekm-access-denied/",
}

TRANSIENT = ("ratelimited", "internal_error", "service_unavailable", "fatal_error",
             "request_timeout", "unparseable_body")

# Admin method -> (non-admin equivalent, what the equivalent cannot see).
FALLBACKS = {
    "admin.conversations.search": (
        "conversations.list",
        "one workspace instead of the organization, and only conversations this "
        "token can already see"),
    "admin.users.list": (
        "users.list",
        "one workspace instead of every workspace in the org"),
    "admin.teams.list": (
        "team.info",
        "the workspace you are in, rather than an enumeration of the org"),
    "admin.usergroups.listChannels": (
        "usergroups.list with include_users",
        "the groups in this workspace, without the org wide channel assignment"),
}


def plan_is_readable():
    """Can the workspace's plan be read from the API? Pure.

    A function rather than a comment because it is load bearing: every other
    decision here is shaped by the fact that the answer is no, and a test
    keeps the claim attached to the code that depends on it.
    """
    return (False, "no documented read method returns the plan; team.info returns "
                   "id, name, domain, email_domain, icon and, on Grid, enterprise_id "
                   "and enterprise_name, and no billing or tier field")


def grid_signal(auth_body):
    """Does this token sit inside an Enterprise organization? Pure.

    A signal, and labelled one everywhere it is printed. It is suggestive
    about capability and it is not capability, so it never feeds the gate.
    """
    doc = auth_body or {}
    if doc.get("ok") is not True:
        return ("unknown", "auth.test did not answer: %s" % (doc.get("error") or "?"))
    if doc.get("enterprise_id"):
        return ("grid", "auth.test returned an enterprise_id, so this workspace sits "
                        "inside an organization")
    return ("not-grid", "auth.test returned no enterprise_id, which strongly suggests "
                        "the admin surface will not answer")


def capability(body):
    """Read one probe response as a capability. Pure.

    Seven states, and the verbosity of the unknown half is the point:

      available          the probe answered ok.
      unavailable-plan   feature_not_enabled; the only state that gates a feature off.
      unknown-role       not_an_admin; the caller lacks the organization role.
      unknown-class      not_allowed_token_type; a bot token was used.
      unknown-scope      missing_scope; the grant is short.
      unknown-transient  ratelimited or a 5xx shaped error; ask again.
      unknown-other      anything else, including the Grid session refusals.
    """
    doc = body or {}
    if doc.get("ok") is True:
        return ("available", "the probe answered ok, so the admin surface exists here")
    error = str(doc.get("error") or "")
    if error == "feature_not_enabled":
        return ("unavailable-plan", "feature_not_enabled; the admin API is an "
                                    "Enterprise Grid surface and no scope or role "
                                    "changes that")
    if error == "not_an_admin":
        return ("unknown-role", "not_an_admin; the caller does not hold the "
                                "organization role, so the plan was never tested")
    if error == "not_allowed_token_type":
        return ("unknown-class", "not_allowed_token_type; this is a bot token, so the "
                                 "plan was never tested")
    if error == "missing_scope":
        return ("unknown-scope", "missing_scope; the grant is short, so the plan was "
                                 "never tested")
    if error in TRANSIENT:
        return ("unknown-transient", "%s; ask again rather than concluding anything"
                                     % (error or "no error"))
    return ("unknown-other", "%s; not a refusal that answers the plan question"
                             % (error or "no error"))


def gate(state):
    """Turn a capability into the flag you are allowed to store. Pure.

    on     the feature is available for this tenant.
    off    measured unavailable, and only ever from feature_not_enabled.
    retry  inconclusive; probe again rather than writing the tenant off.

    A false off is invisible and permanent, because a gated feature is never
    probed again. A false retry costs one request.
    """
    if state == "available":
        return ("on", "measured available")
    if state == "unavailable-plan":
        return ("off", "measured unavailable; this is the only state that gates a "
                       "feature off")
    return ("retry", "inconclusive; an unknown is not an absence and must not be "
                     "stored as one")


def owner_of(error):
    """Which note owns this refusal, if not this one? Pure."""
    return NOT_THIS_QUESTION.get(str(error or "").strip())


def fallback_for(method):
    """The non-admin equivalent and what it cannot see. Pure."""
    return FALLBACKS.get(str(method or "").strip())


def matrix_verdict(rows):
    """One line for the whole matrix. Pure.

    rows: [(tenant, capability), ...]. Unknowns are reported as the finding,
    because a matrix with unknowns in it is not yet a matrix.
    """
    counts = {}
    for _tenant, state in rows or []:
        key = "unknown" if state.startswith("unknown") else state
        counts[key] = counts.get(key, 0) + 1
    if not rows:
        return ("empty", "no installations were probed")
    unknown = counts.get("unknown", 0)
    summary = "%d available, %d unavailable, %d unknown" % (
        counts.get("available", 0), counts.get("unavailable-plan", 0), unknown)
    if unknown:
        return ("%d unknown" % unknown, summary)
    return ("measured", summary)


def get(session, method, token, params=None):
    """One GET with one tenant's token. Returns the parsed body."""
    r = session.get(API + method, params=params or {},
                    headers={"Authorization": "Bearer " + token}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--installs", required=True,
                    help="JSON list of installations, each with id and user_token")
    ap.add_argument("--methods", default="admin.conversations.search",
                    help="comma separated admin methods your feature depends on, so "
                         "their fallbacks are printed")
    args = ap.parse_args()

    with open(args.installs, encoding="utf-8") as handle:
        installs = json.load(handle) or []

    readable, why = plan_is_readable()
    if not readable:
        log.info("plan       not readable     %s", why)

    session = requests.Session()
    rows = []
    for row in installs:
        row = row or {}
        tenant = str(row.get("id") or "?")
        token = row.get("user_token") or ""
        if not token:
            log.warning("tenant     %-16s no user token stored, so nothing can be "
                        "measured", tenant)
            rows.append((tenant, "unknown-class"))
            continue
        signal, signal_why = grid_signal(get(session, "auth.test", token))
        body = get(session, PROBE[0], token, PROBE[1])
        state, detail = capability(body)
        flag, flag_why = gate(state)
        level = log.info if state in ("available", "unavailable-plan") else log.warning
        level("tenant     %-16s signal=%-9s capability=%-18s gate=%s",
              tenant, signal, state, flag)
        log.info("           signal           %s", signal_why)
        log.info("           note             %s", detail)
        if flag == "retry":
            log.warning("           gate             %s", flag_why)
        pointer = owner_of(body.get("error"))
        if pointer:
            log.info("           see also         %s", pointer)
        rows.append((tenant, state))

    for method in [m.strip() for m in args.methods.split(",") if m.strip()]:
        pair = fallback_for(method)
        if not pair:
            log.info("fallback   %-30s none named here; check the method reference",
                     method)
            continue
        log.info("fallback   %s -> %s", method, pair[0])
        log.info("           loses            %s", pair[1])

    state, summary = matrix_verdict(rows)
    if state == "measured":
        log.info("matrix     %d tenant(s)      %s", len(rows), summary)
        log.info("verdict    measured         every tenant was gated on a measurement")
        return 0
    log.warning("matrix     %d tenant(s)      %s", len(rows), summary)
    log.warning("verdict    %-16s re-probe before gating; an unknown is not an "
                "absence", state)
    log.warning("  repair: feature detect at install time and store the result, so the "
                "gate reads a measured fact rather than an assumption")
    log.warning("  repair: present a clear requires Enterprise Grid message for a "
                "measured off, and a pending state for a retry")
    log.warning("  repair: build the non-admin fallback where the narrower answer is "
                "worth having; the loss is printed above")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-admin-capability.mjs",
"js": '''/**
 * Measure, per installation, whether the admin API surface exists at all.
 *
 * Read only, one probe per tenant. The admin.* families are Enterprise Grid
 * features and a workspace on a smaller plan answers feature_not_enabled
 * whoever calls them with whatever scopes.
 *
 * The plan is not readable: no documented read method returns it, so
 * capability is an experiment rather than a lookup. The rule this module
 * exists to enforce is that only feature_not_enabled means unavailable.
 * not_an_admin, not_allowed_token_type and missing_scope mean the probe never
 * reached the question, and storing one of those as an absence creates a
 * permanent false negative that no later run corrects.
 */
import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

export const PROBE = ['admin.teams.list', { limit: 1 }];

export const NOT_THIS_QUESTION = {
  not_an_admin: '/slack/not-an-admin/',
  not_allowed_token_type: '/slack/admin-method-needs-user-token/',
  missing_scope: '/slack/missing-scope-on-read/',
  accesslimited: '/slack/accesslimited-ip-allowlist/',
  ekm_access_denied: '/slack/ekm-access-denied/',
};

export const TRANSIENT = ['ratelimited', 'internal_error', 'service_unavailable',
  'fatal_error', 'request_timeout', 'unparseable_body'];

export const FALLBACKS = {
  'admin.conversations.search': ['conversations.list',
    'one workspace instead of the organization, and only conversations this token '
    + 'can already see'],
  'admin.users.list': ['users.list',
    'one workspace instead of every workspace in the org'],
  'admin.teams.list': ['team.info',
    'the workspace you are in, rather than an enumeration of the org'],
  'admin.usergroups.listChannels': ['usergroups.list with include_users',
    'the groups in this workspace, without the org wide channel assignment'],
};

// A function rather than a comment because it is load bearing.
export function planIsReadable() {
  return [false, 'no documented read method returns the plan; team.info returns id, '
    + 'name, domain, email_domain, icon and, on Grid, enterprise_id and '
    + 'enterprise_name, and no billing or tier field'];
}

// Suggestive about capability, and not capability. Never feeds the gate.
export function gridSignal(authBody) {
  const doc = authBody ?? {};
  if (doc.ok !== true) return ['unknown', `auth.test did not answer: ${doc.error ?? '?'}`];
  if (doc.enterprise_id) {
    return ['grid', 'auth.test returned an enterprise_id, so this workspace sits '
      + 'inside an organization'];
  }
  return ['not-grid', 'auth.test returned no enterprise_id, which strongly suggests '
    + 'the admin surface will not answer'];
}

export function capability(body) {
  const doc = body ?? {};
  if (doc.ok === true) {
    return ['available', 'the probe answered ok, so the admin surface exists here'];
  }
  const error = String(doc.error ?? '');
  if (error === 'feature_not_enabled') {
    return ['unavailable-plan', 'feature_not_enabled; the admin API is an Enterprise '
      + 'Grid surface and no scope or role changes that'];
  }
  if (error === 'not_an_admin') {
    return ['unknown-role', 'not_an_admin; the caller does not hold the organization '
      + 'role, so the plan was never tested'];
  }
  if (error === 'not_allowed_token_type') {
    return ['unknown-class', 'not_allowed_token_type; this is a bot token, so the plan '
      + 'was never tested'];
  }
  if (error === 'missing_scope') {
    return ['unknown-scope', 'missing_scope; the grant is short, so the plan was never '
      + 'tested'];
  }
  if (TRANSIENT.includes(error)) {
    return ['unknown-transient', `${error || 'no error'}; ask again rather than `
      + 'concluding anything'];
  }
  return ['unknown-other', `${error || 'no error'}; not a refusal that answers the `
    + 'plan question'];
}

// A false off is invisible and permanent. A false retry costs one request.
export function gate(state) {
  if (state === 'available') return ['on', 'measured available'];
  if (state === 'unavailable-plan') {
    return ['off', 'measured unavailable; this is the only state that gates a feature off'];
  }
  return ['retry', 'inconclusive; an unknown is not an absence and must not be stored '
    + 'as one'];
}

export function ownerOf(error) {
  return NOT_THIS_QUESTION[String(error ?? '').trim()] ?? null;
}

export function fallbackFor(method) {
  return FALLBACKS[String(method ?? '').trim()] ?? null;
}

export function matrixVerdict(rows) {
  const counts = {};
  for (const [, state] of rows ?? []) {
    const key = state.startsWith('unknown') ? 'unknown' : state;
    counts[key] = (counts[key] ?? 0) + 1;
  }
  if (!(rows ?? []).length) return ['empty', 'no installations were probed'];
  const unknown = counts.unknown ?? 0;
  const summary = `${counts.available ?? 0} available, `
    + `${counts['unavailable-plan'] ?? 0} unavailable, ${unknown} unknown`;
  if (unknown) return [`${unknown} unknown`, summary];
  return ['measured', summary];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function read(token, method, params = {}) {
  const url = new URL(API + method);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const installsPath = arg(args, '--installs');
  if (!installsPath) {
    console.error('pass --installs with a JSON list of installations');
    process.exitCode = 2;
    return;
  }
  const installs = JSON.parse(await readFile(installsPath, 'utf8')) ?? [];
  const methods = arg(args, '--methods', 'admin.conversations.search')
    .split(',').map((s) => s.trim()).filter(Boolean);

  const [readable, why] = planIsReadable();
  if (!readable) console.log(`plan       not readable     ${why}`);

  const rows = [];
  for (const raw of installs) {
    const row = raw ?? {};
    const tenant = String(row.id ?? '?');
    const token = row.user_token ?? '';
    if (!token) {
      console.warn(`tenant     ${tenant.padEnd(16)} no user token stored, so nothing `
        + 'can be measured');
      rows.push([tenant, 'unknown-class']);
      continue;
    }
    // eslint-disable-next-line no-await-in-loop
    const [signal, signalWhy] = gridSignal(await read(token, 'auth.test'));
    // eslint-disable-next-line no-await-in-loop
    const body = await read(token, PROBE[0], PROBE[1]);
    const [state, detail] = capability(body);
    const [flag, flagWhy] = gate(state);
    const line = `tenant     ${tenant.padEnd(16)} signal=${signal.padEnd(9)} `
      + `capability=${state.padEnd(18)} gate=${flag}`;
    if (state === 'available' || state === 'unavailable-plan') console.log(line);
    else console.warn(line);
    console.log(`           signal           ${signalWhy}`);
    console.log(`           note             ${detail}`);
    if (flag === 'retry') console.warn(`           gate             ${flagWhy}`);
    const pointer = ownerOf(body.error);
    if (pointer) console.log(`           see also         ${pointer}`);
    rows.push([tenant, state]);
  }

  for (const method of methods) {
    const pair = fallbackFor(method);
    if (!pair) {
      console.log(`fallback   ${method.padEnd(30)} none named here; check the method `
        + 'reference');
      continue;
    }
    console.log(`fallback   ${method} -> ${pair[0]}`);
    console.log(`           loses            ${pair[1]}`);
  }

  const [state, summary] = matrixVerdict(rows);
  if (state === 'measured') {
    console.log(`matrix     ${rows.length} tenant(s)      ${summary}`);
    console.log('verdict    measured         every tenant was gated on a measurement');
    return;
  }
  console.warn(`matrix     ${rows.length} tenant(s)      ${summary}`);
  console.warn(`verdict    ${state.padEnd(16)} re-probe before gating; an unknown is `
    + 'not an absence');
  console.warn('  repair: feature detect at install time and store the result, so the '
    + 'gate reads a measured fact rather than an assumption');
  console.warn('  repair: present a clear requires Enterprise Grid message for a '
    + 'measured off, and a pending state for a retry');
  console.warn('  repair: build the non-admin fallback where the narrower answer is '
    + 'worth having; the loss is printed above');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The classifier gets one test per refusal, and then the gate gets the assertion the whole note is built on: every state except <code>unavailable-plan</code> has to produce <code>retry</code>, so no inconclusive probe can ever turn a customer's feature off. There is a matching test that <code>feature_not_enabled</code> really does produce <code>off</code>, because a check so cautious it never concludes anything is just as useless. <code>plan_is_readable</code> is tested too, which looks odd until you notice that every design decision here rests on it: if the plan were readable this script would be a lookup.",
"test_py_file": "test_slack_admin_capability.py",
"test_py": '''from slack_admin_capability import (
    capability, fallback_for, gate, grid_signal, matrix_verdict, owner_of,
    plan_is_readable,
)


def test_the_plan_is_not_readable_and_the_code_says_so():
    readable, why = plan_is_readable()
    assert readable is False
    assert "team.info" in why


def test_an_ok_probe_is_available():
    assert capability({"ok": True, "teams": []})[0] == "available"


def test_feature_not_enabled_is_the_only_state_that_gates_a_feature_off():
    state, why = capability({"ok": False, "error": "feature_not_enabled"})
    assert state == "unavailable-plan"
    assert gate(state)[0] == "off"
    assert "Enterprise Grid surface" in why


def test_a_role_refusal_never_becomes_an_absence():
    state, _why = capability({"ok": False, "error": "not_an_admin"})
    assert state == "unknown-role"
    assert gate(state)[0] == "retry"


def test_a_class_refusal_never_becomes_an_absence():
    assert gate(capability({"ok": False, "error": "not_allowed_token_type"})[0])[0] \\
        == "retry"


def test_a_scope_refusal_never_becomes_an_absence():
    assert gate(capability({"ok": False, "error": "missing_scope"})[0])[0] == "retry"


def test_a_transient_refusal_is_asked_again():
    assert capability({"ok": False, "error": "ratelimited"})[0] == "unknown-transient"
    assert gate("unknown-transient")[0] == "retry"


def test_an_unrecognised_refusal_is_unknown_rather_than_unavailable():
    state, why = capability({"ok": False, "error": "org_login_required"})
    assert state == "unknown-other"
    assert "org_login_required" in why


def test_every_unknown_state_gates_to_retry():
    for state in ("unknown-role", "unknown-class", "unknown-scope",
                  "unknown-transient", "unknown-other"):
        assert gate(state)[0] == "retry"


def test_the_grid_signal_is_a_signal_and_is_labelled_one():
    assert grid_signal({"ok": True, "enterprise_id": "E1"})[0] == "grid"
    state, why = grid_signal({"ok": True, "team_id": "T1"})
    assert state == "not-grid"
    assert "suggests" in why


def test_an_unanswered_auth_test_leaves_the_signal_unknown():
    assert grid_signal({"ok": False, "error": "invalid_auth"})[0] == "unknown"


def test_refusals_that_belong_elsewhere_are_handed_over():
    assert owner_of("not_an_admin") == "/slack/not-an-admin/"
    assert owner_of("feature_not_enabled") is None


def test_each_fallback_names_the_method_and_the_loss():
    replacement, loses = fallback_for("admin.conversations.search")
    assert replacement == "conversations.list"
    assert "one workspace" in loses
    assert fallback_for("admin.somethingNew.list") is None


def test_the_matrix_reports_unknowns_as_the_finding():
    state, summary = matrix_verdict([("a", "available"), ("b", "unavailable-plan"),
                                     ("c", "unknown-role")])
    assert state == "1 unknown"
    assert summary == "1 available, 1 unavailable, 1 unknown"


def test_a_fully_measured_matrix_says_measured():
    assert matrix_verdict([("a", "available"), ("b", "unavailable-plan")])[0] == "measured"


def test_an_empty_matrix_is_not_a_measurement():
    assert matrix_verdict([])[0] == "empty"
''',
"test_js_file": "slack-admin-capability.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  capability, fallbackFor, gate, gridSignal, matrixVerdict, ownerOf, planIsReadable,
} from './slack-admin-capability.mjs';

test('the plan is not readable and the code says so', () => {
  const [readable, why] = planIsReadable();
  assert.equal(readable, false);
  assert.match(why, /team\\.info/);
});

test('an ok probe is available', () => {
  assert.equal(capability({ ok: true, teams: [] })[0], 'available');
});

test('feature_not_enabled is the only state that gates a feature off', () => {
  const [state, why] = capability({ ok: false, error: 'feature_not_enabled' });
  assert.equal(state, 'unavailable-plan');
  assert.equal(gate(state)[0], 'off');
  assert.match(why, /Enterprise Grid surface/);
});

test('a role refusal never becomes an absence', () => {
  const [state] = capability({ ok: false, error: 'not_an_admin' });
  assert.equal(state, 'unknown-role');
  assert.equal(gate(state)[0], 'retry');
});

test('a class refusal never becomes an absence', () => {
  assert.equal(gate(capability({ ok: false, error: 'not_allowed_token_type' })[0])[0],
    'retry');
});

test('a scope refusal never becomes an absence', () => {
  assert.equal(gate(capability({ ok: false, error: 'missing_scope' })[0])[0], 'retry');
});

test('a transient refusal is asked again', () => {
  assert.equal(capability({ ok: false, error: 'ratelimited' })[0], 'unknown-transient');
  assert.equal(gate('unknown-transient')[0], 'retry');
});

test('an unrecognised refusal is unknown rather than unavailable', () => {
  const [state, why] = capability({ ok: false, error: 'org_login_required' });
  assert.equal(state, 'unknown-other');
  assert.match(why, /org_login_required/);
});

test('every unknown state gates to retry', () => {
  for (const state of ['unknown-role', 'unknown-class', 'unknown-scope',
    'unknown-transient', 'unknown-other']) {
    assert.equal(gate(state)[0], 'retry');
  }
});

test('the grid signal is a signal and is labelled one', () => {
  assert.equal(gridSignal({ ok: true, enterprise_id: 'E1' })[0], 'grid');
  const [state, why] = gridSignal({ ok: true, team_id: 'T1' });
  assert.equal(state, 'not-grid');
  assert.match(why, /suggests/);
});

test('an unanswered auth.test leaves the signal unknown', () => {
  assert.equal(gridSignal({ ok: false, error: 'invalid_auth' })[0], 'unknown');
});

test('refusals that belong elsewhere are handed over', () => {
  assert.equal(ownerOf('not_an_admin'), '/slack/not-an-admin/');
  assert.equal(ownerOf('feature_not_enabled'), null);
});

test('each fallback names the method and the loss', () => {
  const [replacement, loses] = fallbackFor('admin.conversations.search');
  assert.equal(replacement, 'conversations.list');
  assert.match(loses, /one workspace/);
  assert.equal(fallbackFor('admin.somethingNew.list'), null);
});

test('the matrix reports unknowns as the finding', () => {
  const [state, summary] = matrixVerdict([['a', 'available'], ['b', 'unavailable-plan'],
    ['c', 'unknown-role']]);
  assert.equal(state, '1 unknown');
  assert.equal(summary, '1 available, 1 unavailable, 1 unknown');
});

test('a fully measured matrix says measured', () => {
  assert.equal(matrixVerdict([['a', 'available'], ['b', 'unavailable-plan']])[0],
    'measured');
});

test('an empty matrix is not a measurement', () => {
  assert.equal(matrixVerdict([])[0], 'empty');
});
''',
"faq": [
 ("Can I just read the workspace's plan and skip the probe?",
  "There is no documented read method that returns it. team.info gives you the workspace id, name, domain, email domain, icon and, on Enterprise Grid, the enterprise id and name, and nothing about tier or billing. The nearest available signal is whether auth.test returns an enterprise_id, which tells you the workspace sits inside an organization and still does not tell you the admin API will answer. So the plan question is settled by an experiment, which is one cheap read, once, stored."),
 ("Why not set the flag to false whenever the admin call throws?",
  "Because four different refusals arrive at that catch block and only one of them is about the plan. A tenant whose token was briefly missing a scope, or whose admin account lost the role for a week, gets permanently marked as not-Enterprise, and the damage is invisible: the feature is now gated off, so the probe never runs again and nothing ever corrects the record. Only feature_not_enabled turns the flag off here. Everything else is retry."),
 ("A tenant is on Enterprise Grid and still gets feature_not_enabled. Is the check wrong?",
  "Check the credential before the plan. That error is specific, but it is also worth confirming that the probe used the tenant's own user token rather than a token from another installation, since a matrix built by looping over installations is exactly the code that mixes those up. If the token is right and the org is genuinely on Grid, the customer's administrator is the next stop: admin API availability is something they can confirm from their side in a way your app cannot."),
 ("What can the non-admin fallbacks actually do?",
  "Less, but usefully less. conversations.list sees the conversations your token can see in one workspace instead of every conversation in the organization; users.list is one workspace instead of all of them; team.info describes the workspace you are in rather than enumerating the org. For a single-workspace customer, which is what a non-Enterprise customer is, the narrower call is frequently the whole answer. The script prints the loss next to the replacement so you can decide."),
 ("Should the customer see anything about this?",
  "Yes, and it should say what it means. A measured off should produce a clear line that the capability requires Enterprise Grid, not a spinner, an empty state or a stack trace, because the customer's administrator is the only person who can act on it and they need to know it is a plan boundary rather than a bug. A retry should show as pending rather than missing, since it means your own probe has not yet succeeded."),
],
"related": [
 ("/slack/not-an-admin/", "a refusal that looks like this and is not"),
 ("/slack/admin-method-needs-user-token/", "the credential the probe needs"),
 ("/slack/workspace-token-in-grid/", "what one token can reach inside an org"),
],
"citations": [CITE_ADMIN_TEAMS_LIST, CITE_TEAM_INFO, CITE_ADMIN_APPS_RESTRICTED,
              CITE_GRID],
})

GUIDES.append({
"slug": "app-restricted-by-admin",
"title": "Approved in 37 workspaces and restricted in three",
"description": "An app can sit on the approved list in one workspace and the restricted list in another. Map your own app_id across the org and read the request queue.",
"h1": "Approved in 37 workspaces and restricted in three",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack admin.apps.restricted.list app blocked",
             "slack app approval enterprise grid workspace",
             "slack admin.apps.requests.list pending approval",
             "slack app restricted by admin install fails",
             "slack app approved list per workspace"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a user token held by an org Admin or Owner with admin.apps:read, and your own app_id",
"lead": "Installs from one customer stopped six weeks ago. Not failed &mdash; stopped. There is no error in your logs, because the request that would have produced one was never made: the person clicking <strong>Add to Slack</strong> is told by Slack that an administrator has to approve this, and whatever happens next happens entirely inside the customer's organization.</p><p>Meanwhile the app is working perfectly for the same customer's other thirty-seven workspaces, which is why nobody noticed. An Enterprise Grid organization keeps an approved list and a restricted list, both of which can be scoped per workspace, and your app is on the first one in most places and the second one in three. Nothing told you when it moved.",
"short_answer": """<p>Two admin read methods answer this directly. <code>admin.apps.approved.list</code> and <code>admin.apps.restricted.list</code> each return the apps on that list, and each accepts either a <code>team_id</code> for one workspace or an <code>enterprise_id</code> for the organization &mdash; <strong>not both</strong>. So the finding is a map: your <code>app_id</code>, held against every workspace in the org, showing where it is approved, where it is restricted, and where it appears on neither list.</p>
<p>The third method is the one people forget. <code>admin.apps.requests.list</code> returns the approval requests that members have raised and no administrator has actioned, each with a <code>date_created</code>, the requesting user, the scopes asked for and the app. A request sitting in that queue for six weeks is not a refusal and does not appear on either list; it is a silent blocker, and it is the single most common reason installs stop without anything going wrong.</p>
<p><strong>Unlisted is genuinely ambiguous and the script says so.</strong> An app on neither list may be installable or may be blocked, depending on whether that organization requires app approval at all &mdash; a setting these two methods do not report. Reporting <code>unlisted</code> as <code>allowed</code> is a guess, and this is one of the places where a confident wrong answer costs a customer conversation.</p>
<p>This is the app's own status. The refusal a particular <em>person</em> meets at runtime is <a href="/slack/app-access-restricted/">a different note</a>.</p>""",
"problem": """<p>The symptom is an absence, which is why it survives so long. A restricted app does not generate traffic that fails; it generates traffic that never happens. Your error rate is flat, your dashboards are green, and the number that moved is installs per week for one customer, which nobody is watching per customer. The first signal is usually a support conversation months later about a rollout that quietly did not happen.</p>
<p>The per-workspace granularity is what makes it hard to reason about. It is natural to assume an app is approved or not approved for an organization, and the model is finer than that: the lists are maintained per workspace as well as org-wide, so an app genuinely can be approved for thirty-seven workspaces and restricted in three, with the three being the ones that had a security review or an incident or an administrator with a different opinion. An engineer testing against the org-level list sees "approved" and concludes the customer is fine.</p>
<p>Nothing notifies you when the status changes. There is no event, no webhook and no field on any response your app already reads that says an administrator moved you from one list to the other on a Tuesday afternoon. From your side the status is only ever observable by asking, which means it is only ever observed if somebody wrote the code that asks.</p>
<p>And the request queue is its own category of stuck. When an organization requires approval, a member who tries to install raises a request with a message and a scope list, and it goes to an administrator's queue. Nobody is refusing you. Nobody has decided anything. The request is simply sitting there behind other work, aging, in a place your app cannot see without an admin token &mdash; and the requesting member, who assumed it went through, has moved on.</p>""",
"why": """<p><strong>This note owns the app's status, not a person's experience.</strong> The already-published <a href="/slack/app-access-restricted/">app_access_restricted note</a> starts from a runtime error that some users get and some do not, and resolves it into a cohort of people who share an attribute. This one starts from an app id and produces a map over workspaces, and its most common finding &mdash; a stalled approval request &mdash; produces no runtime error at all, for anybody, ever. Different input, different output, different person to send it to.</p>
<p><strong>The map is per workspace because the lists are.</strong> Querying only the org level answers a narrower question than the one you have. The script enumerates the organization's workspaces with <code>admin.teams.list</code>, queries both lists per workspace, and reports the shape: uniform, split, or absent. A split is the finding worth having, because it names exactly which workspaces to raise with the administrator.</p>
<p><strong><code>team_id</code> and <code>enterprise_id</code> are documented as mutually exclusive, so the argument builder enforces it.</strong> Sending both is an argument error rather than a broader query, and building the parameters in one tested function keeps that out of the request loop where it would be discovered against a live org.</p>
<p><strong>Unlisted is reported as unknown, never as allowed.</strong> Whether an app that is on neither list can be installed depends on whether the organization requires approval, and that setting is not returned by these methods. An audit that prints <code>allowed</code> there will eventually tell a customer their app is fine in a workspace where members cannot install it, which is worse than printing nothing.</p>
<p><strong>The request queue is read with an age, because the age is the finding.</strong> A request raised this morning is a normal part of the process. The same request at forty-one days is a decision nobody has made, and it is actionable in a way the raw list is not: the administrator can be shown their own queue, with dates, and the name of the member of their organization who is waiting.</p>
<p><strong>Everything is a read, and the write half of the family is not touched.</strong> <code>admin.apps.approve</code> and <code>admin.apps.restrict</code> exist and would change a customer's organization. This script calls the three <code>list</code> methods and nothing else, and the repair it prints is a sentence for an administrator rather than a call for you.</p>""",
"steps": [
 {"h": "Get an admin token, or stop here",
  "body": """<p>All three methods want a user token held by an org Admin or Owner with <code>admin.apps:read</code>. Without one, none of this is visible &mdash; the app's listing status is simply not exposed to the app. If you do not have that token, the <a href="/slack/app-access-restricted/">cohort approach</a> is what is left.</p>"""},
 {"h": "Enumerate the organization's workspaces",
  "body": """<p><code>admin.teams.list</code>, paginated with <code>cursor</code>. The workspace count is also the denominator for coverage: a map over eight of forty workspaces is not a map of the organization, and the script says which it is.</p>"""},
 {"h": "Build the scoping argument correctly",
  "body": """<p><code>scope_args</code> returns the parameters for one query and refuses to set <code>team_id</code> and <code>enterprise_id</code> together, because the methods document them as mutually exclusive. Org-level and workspace-level are separate queries, and both are worth making.</p>"""},
 {"h": "Look for your own app_id on both lists",
  "body": """<p><code>listing_status</code> takes the two sets of app ids and returns <code>approved</code>, <code>restricted</code>, <code>unlisted</code> or <code>contradictory</code>. The last one is rare and worth surfacing rather than resolving silently.</p>"""},
 {"h": "Read the shape of the map, not just the rows",
  "body": """<p><code>status_map</code> turns forty rows into one sentence: uniform-approved, uniform-restricted, split, or unlisted-everywhere. A split names the workspaces, which is the part an administrator can act on.</p>"""},
 {"h": "Age the request queue",
  "body": """<p><code>stalled_requests</code> reads <code>date_created</code> against now and returns the requests older than your threshold, with the member who raised each one. Send that list, with dates, to the administrator who owns the queue.</p>"""},
],
"verify": """<p>After the administrator approves the app in the affected workspaces and clears the queue, re-run. The shape should read <code>uniform-approved</code> and the queue should be empty.</p>
<pre><code class="language-bash">python3 slack_app_approval_map.py --app-id A012345678 --workspaces 40
# scope      organization     enterprise_id=E0123, approved
# workspace  T001 acme-core        approved
# workspace  T014 acme-security    restricted
# workspace  T022 acme-legal       restricted
# workspace  T031 acme-labs        unlisted
#            note             neither list mentions this app; whether that permits
#                             installation depends on the org approval setting,
#                             which these methods do not report
# shape      split            approved in 36, restricted in 2, unlisted in 1
# request    R0091            41 day(s) old, raised by U07AAAA in T014
# request    R0104            12 day(s) old, raised by U09BBBB in T022
# coverage   full             39 of 39 workspaces queried
# verdict    3 finding(s)     2 restricted, 1 request older than 30 days
#   repair: ask the org admin to approve the app in the named workspaces
#   repair: ask them to action the pending requests above; nobody has refused you
#   note:   nothing here was approved, restricted or requested by this script</code></pre>""",
"code_intro": "The three list methods are ordinary paginated reads and the interest is in what is done with them. <code>scope_args</code> is small and tested because it encodes a documented exclusivity that is otherwise discovered against a live organization. <code>listing_status</code> is the per-workspace answer, and its <code>unlisted</code> state is deliberately not an <code>allowed</code> state. <code>status_map</code> collapses the rows into the sentence you send to an administrator, <code>stalled_requests</code> ages the queue because the age is the finding, and <code>coverage</code> keeps a partial map from reading as a complete one.",
"py_file": "slack_app_approval_map.py",
"py": '''"""Map your own app's approval status across an Enterprise Grid organization.

Read only. Three list methods, all of which want a user token held by an org
Admin or Owner with admin.apps:read: admin.apps.approved.list,
admin.apps.restricted.list and admin.apps.requests.list. The write half of
that family, which would change a customer's organization, is never called.

The finding is a map rather than an error. An app can sit on the approved list
in most workspaces of an organization and on the restricted list in a few, and
nothing notifies the developer when it moves. The most common finding of all
produces no error anywhere: an approval request sitting unactioned in an
administrator's queue for six weeks.

One deliberate refusal to guess: an app on neither list is reported as
unlisted, not as allowed. Whether an unlisted app can be installed depends on
whether the organization requires app approval, and these methods do not
report that setting.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_app_approval_map")

API = "https://slack.com/api/"

# Reads only. The approve and restrict methods in this family would change the
# customer's organization and are not called, named or accepted as arguments.
READS = ("admin.teams.list", "admin.apps.approved.list",
         "admin.apps.restricted.list", "admin.apps.requests.list")

DAY = 86400.0


def scope_args(team_id=None, enterprise_id=None, limit=100, cursor=None):
    """Build the scoping parameters for one list query. Pure.

    Returns (params, note) or raises ValueError. team_id and enterprise_id are
    documented as mutually exclusive, and sending both is an argument error
    rather than a broader query. Encoded here, with a test, rather than
    discovered against a live organization.
    """
    if team_id and enterprise_id:
        raise ValueError("team_id and enterprise_id cannot be used together")
    params = {"limit": int(limit)}
    if cursor:
        params["cursor"] = cursor
    if team_id:
        params["team_id"] = team_id
        return (params, "one workspace")
    if enterprise_id:
        params["enterprise_id"] = enterprise_id
        return (params, "the organization")
    return (params, "the default scope of this token")


def app_ids(entries):
    """The app ids on one page of an approved or restricted list. Pure.

    Each entry carries an app object; the id is read from there, and from a
    top level app_id where a caller has already flattened the rows.
    """
    out = []
    for entry in entries or []:
        doc = entry or {}
        app = doc.get("app") or {}
        found = app.get("id") or doc.get("app_id")
        if found:
            out.append(str(found))
    return out


def listing_status(app_id, approved, restricted):
    """Where does one app stand in one scope? Pure.

    Returns (state, why). "unlisted" is not "allowed": whether an unlisted app
    can be installed depends on whether the organization requires approval,
    which these methods do not report.
    """
    wanted = str(app_id or "")
    on_approved = wanted in set(approved or [])
    on_restricted = wanted in set(restricted or [])
    if on_approved and on_restricted:
        return ("contradictory", "this app appears on both lists in this scope, which "
                                 "is worth raising rather than resolving quietly")
    if on_restricted:
        return ("restricted", "an administrator has placed this app on the restricted "
                              "list for this scope")
    if on_approved:
        return ("approved", "this app is on the approved list for this scope")
    return ("unlisted", "neither list mentions this app; whether that permits "
                        "installation depends on the org approval setting, which "
                        "these methods do not report")


def status_map(rows):
    """Collapse the per-workspace rows into one sentence. Pure.

    rows: [(team_id, state), ...]. Returns (shape, detail, named) where named
    is the workspaces an administrator has to be told about.
    """
    counts = {}
    for _team, state in rows or []:
        counts[state] = counts.get(state, 0) + 1
    total = len(rows or [])
    if not total:
        return ("empty", "no workspaces were queried", [])
    restricted = [t for t, s in rows if s == "restricted"]
    contradictory = [t for t, s in rows if s == "contradictory"]
    detail = ", ".join("%s in %d" % (state, n) for state, n in sorted(counts.items()))
    if counts.get("approved") == total:
        return ("uniform-approved", detail, [])
    if counts.get("restricted") == total:
        return ("uniform-restricted", detail, restricted)
    if counts.get("unlisted") == total:
        return ("unlisted-everywhere", detail, [])
    return ("split", detail, restricted + contradictory)


def request_age(request, now=None):
    """How long has this approval request been waiting? Pure.

    Returns (days, detail). A request raised this morning is the process
    working. The same request at forty-one days is a decision nobody made.
    """
    doc = request or {}
    created = doc.get("date_created")
    if not created:
        return (None, "no date_created on this request, so its age is unknown")
    now = float(now if now is not None else time.time())
    days = max(0.0, (now - float(created)) / DAY)
    return (round(days, 1), "raised by %s in %s"
            % ((doc.get("user") or {}).get("id") or "an unnamed member",
               (doc.get("team") or {}).get("id") or "an unnamed workspace"))


def stalled_requests(requests, now=None, threshold_days=30):
    """The requests old enough to be a finding. Pure."""
    out = []
    for request in requests or []:
        days, detail = request_age(request, now)
        if days is not None and days >= float(threshold_days):
            out.append(((request or {}).get("id"), days, detail))
    return sorted(out, key=lambda row: row[1], reverse=True)


def coverage(queried, total):
    """Is this a map of the organization or a sample of it? Pure."""
    queried, total = int(queried or 0), int(total or 0)
    if not total:
        return ("unknown", "the organization's workspace count was not established")
    if queried >= total:
        return ("full", "%d of %d workspaces queried" % (queried, total))
    return ("partial", "%d of %d workspaces queried; the rest are unmeasured, not "
                       "approved" % (queried, total))


def verdict(shape, named, stalled):
    """One line for the whole map. Pure."""
    findings = len(named or []) + len(stalled or [])
    if shape in ("empty", "unknown"):
        return ("inconclusive", "nothing was measured")
    if not findings:
        return ("clean", "the app is not restricted anywhere measured and no request "
                         "is stalled")
    return ("%d finding(s)" % findings,
            "%d restricted or contradictory workspace(s), %d stalled request(s)"
            % (len(named or []), len(stalled or [])))


def paged(session, method, params):
    """Every page of one list method. Read only, cursor paginated."""
    out, cursor = [], None
    while True:
        page = dict(params)
        if cursor:
            page["cursor"] = cursor
        r = session.get(API + method, params=page, timeout=30)
        try:
            body = r.json()
        except ValueError:
            return (out, "unparseable_body")
        if body.get("ok") is not True:
            return (out, str(body.get("error") or "unknown_error"))
        for key in ("apps", "restricted_apps", "approved_apps", "app_requests"):
            if isinstance(body.get(key), list):
                out.extend(body[key])
        cursor = (body.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            return (out, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app-id", required=True, help="your own app id, as A0123...")
    ap.add_argument("--token-env", default="SLACK_ADMIN_USER_TOKEN",
                    help="environment variable holding an org admin user token with "
                         "admin.apps:read")
    ap.add_argument("--enterprise-id", default="",
                    help="the organization id, for the org level query")
    ap.add_argument("--workspaces", type=int, default=0,
                    help="the organization's workspace count, if you know it, so "
                         "coverage can be reported")
    ap.add_argument("--stale-days", type=int, default=30)
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("token      missing        set %s to an org admin user token",
                  args.token_env)
        return 2
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    if args.enterprise_id:
        params, note = scope_args(enterprise_id=args.enterprise_id)
        approved, err_a = paged(session, "admin.apps.approved.list", params)
        restricted, err_r = paged(session, "admin.apps.restricted.list", params)
        if err_a or err_r:
            log.warning("scope      organization     unreadable: %s", err_a or err_r)
        else:
            state, why = listing_status(args.app_id, app_ids(approved),
                                        app_ids(restricted))
            log.info("scope      organization     enterprise_id=%s, %s (%s)",
                     args.enterprise_id, state, note)
            if state != "approved":
                log.warning("           note             %s", why)

    teams, err = paged(session, "admin.teams.list", {"limit": 100})
    if err:
        log.error("teams      unreadable     admin.teams.list: %s", err)
        return 2

    rows = []
    for team in teams:
        team_id = (team or {}).get("id")
        if not team_id:
            continue
        params, _note = scope_args(team_id=team_id)
        approved, err_a = paged(session, "admin.apps.approved.list", params)
        restricted, err_r = paged(session, "admin.apps.restricted.list", params)
        if err_a or err_r:
            log.warning("workspace  %-6s %-16s unreadable: %s", team_id,
                        (team or {}).get("name") or "", err_a or err_r)
            continue
        state, why = listing_status(args.app_id, app_ids(approved), app_ids(restricted))
        level = log.info if state == "approved" else log.warning
        level("workspace  %-6s %-16s %s", team_id, (team or {}).get("name") or "", state)
        if state == "unlisted":
            log.info("           note             %s", why)
        rows.append((team_id, state))

    shape, detail, named = status_map(rows)
    (log.info if shape == "uniform-approved" else log.warning)(
        "shape      %-16s %s", shape, detail)

    requests_out, err_q = paged(session, "admin.apps.requests.list", {"limit": 100})
    stalled = [] if err_q else stalled_requests(requests_out,
                                                threshold_days=args.stale_days)
    if err_q:
        log.warning("request    unreadable     admin.apps.requests.list: %s", err_q)
    for request_id, days, who in stalled:
        log.warning("request    %-16s %s day(s) old, %s", request_id, days, who)

    cover, cover_why = coverage(len(rows), args.workspaces or len(teams))
    (log.info if cover == "full" else log.warning)("coverage   %-16s %s", cover,
                                                   cover_why)

    final, summary = verdict(shape, named, stalled)
    if final == "clean":
        log.info("verdict    clean            %s", summary)
        log.info("  note:   nothing here was approved, restricted or requested by this "
                 "script")
        return 0
    log.warning("verdict    %-16s %s", final, summary)
    if named:
        log.warning("  repair: ask the org admin to approve the app in %s",
                    ", ".join(named[:6]))
    if stalled:
        log.warning("  repair: ask them to action the pending requests above; nobody "
                    "has refused you, the queue simply has not been read")
    log.warning("  repair: an unlisted status is not a refusal and not a clearance; "
                "confirm the org's app approval setting with the administrator")
    log.warning("  note:   nothing here was approved, restricted or requested by this "
                "script")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-app-approval-map.mjs",
"js": '''/**
 * Map your own app's approval status across an Enterprise Grid organization.
 *
 * Read only. Three list methods, all wanting a user token held by an org Admin
 * or Owner with admin.apps:read. The write half of that family, which would
 * change a customer's organization, is never called.
 *
 * The finding is a map rather than an error: an app can be approved in most
 * workspaces of an org and restricted in a few, and the most common finding of
 * all produces no error anywhere, because it is an approval request sitting
 * unactioned in an administrator's queue.
 *
 * One deliberate refusal to guess: an app on neither list is unlisted, not
 * allowed. Whether an unlisted app can be installed depends on the org's app
 * approval setting, which these methods do not report.
 */

const API = 'https://slack.com/api/';

export const READS = ['admin.teams.list', 'admin.apps.approved.list',
  'admin.apps.restricted.list', 'admin.apps.requests.list'];

const DAY = 86400;

// team_id and enterprise_id are documented as mutually exclusive.
export function scopeArgs({ teamId = '', enterpriseId = '', limit = 100, cursor = '' } = {}) {
  if (teamId && enterpriseId) {
    throw new Error('team_id and enterprise_id cannot be used together');
  }
  const params = { limit: Number(limit) };
  if (cursor) params.cursor = cursor;
  if (teamId) {
    params.team_id = teamId;
    return [params, 'one workspace'];
  }
  if (enterpriseId) {
    params.enterprise_id = enterpriseId;
    return [params, 'the organization'];
  }
  return [params, 'the default scope of this token'];
}

export function appIds(entries) {
  const out = [];
  for (const entry of entries ?? []) {
    const doc = entry ?? {};
    const found = (doc.app ?? {}).id ?? doc.app_id;
    if (found) out.push(String(found));
  }
  return out;
}

// "unlisted" is not "allowed".
export function listingStatus(appId, approved, restricted) {
  const wanted = String(appId ?? '');
  const onApproved = new Set(approved ?? []).has(wanted);
  const onRestricted = new Set(restricted ?? []).has(wanted);
  if (onApproved && onRestricted) {
    return ['contradictory', 'this app appears on both lists in this scope, which is '
      + 'worth raising rather than resolving quietly'];
  }
  if (onRestricted) {
    return ['restricted', 'an administrator has placed this app on the restricted list '
      + 'for this scope'];
  }
  if (onApproved) return ['approved', 'this app is on the approved list for this scope'];
  return ['unlisted', 'neither list mentions this app; whether that permits '
    + 'installation depends on the org approval setting, which these methods do not report'];
}

export function statusMap(rows) {
  const counts = {};
  for (const [, state] of rows ?? []) counts[state] = (counts[state] ?? 0) + 1;
  const total = (rows ?? []).length;
  if (!total) return ['empty', 'no workspaces were queried', []];
  const restricted = rows.filter(([, s]) => s === 'restricted').map(([t]) => t);
  const contradictory = rows.filter(([, s]) => s === 'contradictory').map(([t]) => t);
  const detail = Object.entries(counts).sort()
    .map(([state, n]) => `${state} in ${n}`).join(', ');
  if (counts.approved === total) return ['uniform-approved', detail, []];
  if (counts.restricted === total) return ['uniform-restricted', detail, restricted];
  if (counts.unlisted === total) return ['unlisted-everywhere', detail, []];
  return ['split', detail, [...restricted, ...contradictory]];
}

export function requestAge(request, now = null) {
  const doc = request ?? {};
  const created = doc.date_created;
  if (!created) return [null, 'no date_created on this request, so its age is unknown'];
  const at = Number(now ?? Date.now() / 1000);
  const days = Math.max(0, (at - Number(created)) / DAY);
  const who = (doc.user ?? {}).id ?? 'an unnamed member';
  const where = (doc.team ?? {}).id ?? 'an unnamed workspace';
  return [Math.round(days * 10) / 10, `raised by ${who} in ${where}`];
}

export function stalledRequests(requests, now = null, thresholdDays = 30) {
  const out = [];
  for (const request of requests ?? []) {
    const [days, detail] = requestAge(request, now);
    if (days !== null && days >= Number(thresholdDays)) {
      out.push([(request ?? {}).id, days, detail]);
    }
  }
  return out.sort((a, b) => b[1] - a[1]);
}

export function coverage(queried, total) {
  const q = Number(queried ?? 0);
  const t = Number(total ?? 0);
  if (!t) return ['unknown', "the organization's workspace count was not established"];
  if (q >= t) return ['full', `${q} of ${t} workspaces queried`];
  return ['partial', `${q} of ${t} workspaces queried; the rest are unmeasured, not approved`];
}

export function verdict(shape, named, stalled) {
  const findings = (named ?? []).length + (stalled ?? []).length;
  if (shape === 'empty' || shape === 'unknown') {
    return ['inconclusive', 'nothing was measured'];
  }
  if (!findings) {
    return ['clean', 'the app is not restricted anywhere measured and no request is stalled'];
  }
  return [`${findings} finding(s)`,
    `${(named ?? []).length} restricted or contradictory workspace(s), `
    + `${(stalled ?? []).length} stalled request(s)`];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function paged(token, method, params) {
  const out = [];
  let cursor = '';
  for (;;) {
    const url = new URL(API + method);
    for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
    if (cursor) url.searchParams.set('cursor', cursor);
    // eslint-disable-next-line no-await-in-loop
    const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    let body;
    try {
      // eslint-disable-next-line no-await-in-loop
      body = await r.json();
    } catch {
      return [out, 'unparseable_body'];
    }
    if (body.ok !== true) return [out, String(body.error ?? 'unknown_error')];
    for (const key of ['apps', 'restricted_apps', 'approved_apps', 'app_requests']) {
      if (Array.isArray(body[key])) out.push(...body[key]);
    }
    cursor = (body.response_metadata ?? {}).next_cursor ?? '';
    if (!cursor) return [out, null];
  }
}

async function main() {
  const args = process.argv.slice(2);
  const appId = arg(args, '--app-id');
  if (!appId) {
    console.error('pass --app-id with your own app id');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_ADMIN_USER_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`token      missing        set ${tokenEnv} to an org admin user token`);
    process.exitCode = 2;
    return;
  }

  const enterpriseId = arg(args, '--enterprise-id');
  if (enterpriseId) {
    const [params, note] = scopeArgs({ enterpriseId });
    const [approved, errA] = await paged(token, 'admin.apps.approved.list', params);
    const [restricted, errR] = await paged(token, 'admin.apps.restricted.list', params);
    if (errA || errR) {
      console.warn(`scope      organization     unreadable: ${errA ?? errR}`);
    } else {
      const [state, why] = listingStatus(appId, appIds(approved), appIds(restricted));
      console.log(`scope      organization     enterprise_id=${enterpriseId}, `
        + `${state} (${note})`);
      if (state !== 'approved') console.warn(`           note             ${why}`);
    }
  }

  const [teams, err] = await paged(token, 'admin.teams.list', { limit: 100 });
  if (err) {
    console.error(`teams      unreadable     admin.teams.list: ${err}`);
    process.exitCode = 2;
    return;
  }

  const rows = [];
  for (const team of teams) {
    const teamId = (team ?? {}).id;
    if (!teamId) continue;
    const [params] = scopeArgs({ teamId });
    // eslint-disable-next-line no-await-in-loop
    const [approved, errA] = await paged(token, 'admin.apps.approved.list', params);
    // eslint-disable-next-line no-await-in-loop
    const [restricted, errR] = await paged(token, 'admin.apps.restricted.list', params);
    const name = String((team ?? {}).name ?? '').padEnd(16);
    if (errA || errR) {
      console.warn(`workspace  ${String(teamId).padEnd(6)} ${name} unreadable: `
        + `${errA ?? errR}`);
      continue;
    }
    const [state, why] = listingStatus(appId, appIds(approved), appIds(restricted));
    const line = `workspace  ${String(teamId).padEnd(6)} ${name} ${state}`;
    if (state === 'approved') console.log(line);
    else console.warn(line);
    if (state === 'unlisted') console.log(`           note             ${why}`);
    rows.push([teamId, state]);
  }

  const [shape, detail, named] = statusMap(rows);
  const shapeLine = `shape      ${shape.padEnd(16)} ${detail}`;
  if (shape === 'uniform-approved') console.log(shapeLine);
  else console.warn(shapeLine);

  const [queue, errQ] = await paged(token, 'admin.apps.requests.list', { limit: 100 });
  const staleDays = Number(arg(args, '--stale-days', '30'));
  const stalled = errQ ? [] : stalledRequests(queue, null, staleDays);
  if (errQ) console.warn(`request    unreadable     admin.apps.requests.list: ${errQ}`);
  for (const [requestId, days, who] of stalled) {
    console.warn(`request    ${String(requestId).padEnd(16)} ${days} day(s) old, ${who}`);
  }

  const workspaces = Number(arg(args, '--workspaces', '0')) || teams.length;
  const [cover, coverWhy] = coverage(rows.length, workspaces);
  const coverLine = `coverage   ${cover.padEnd(16)} ${coverWhy}`;
  if (cover === 'full') console.log(coverLine);
  else console.warn(coverLine);

  const [final, summary] = verdict(shape, named, stalled);
  if (final === 'clean') {
    console.log(`verdict    clean            ${summary}`);
    console.log('  note:   nothing here was approved, restricted or requested by this script');
    return;
  }
  console.warn(`verdict    ${final.padEnd(16)} ${summary}`);
  if (named.length) {
    console.warn(`  repair: ask the org admin to approve the app in ${named.slice(0, 6).join(', ')}`);
  }
  if (stalled.length) {
    console.warn('  repair: ask them to action the pending requests above; nobody has '
      + 'refused you, the queue simply has not been read');
  }
  console.warn('  repair: an unlisted status is not a refusal and not a clearance; '
    + "confirm the org's app approval setting with the administrator");
  console.warn('  note:   nothing here was approved, restricted or requested by this script');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are list pages and request rows, and the clock is passed in rather than read, so the aging tests are not a source of intermittent failures at midnight. Three assertions carry the note. An app on neither list must come back <code>unlisted</code> and the reason must say that this is not a clearance. A map that is approved in most workspaces and restricted in a couple must come back <code>split</code> with the restricted workspaces named, because those names are the whole message to the administrator. And <code>scope_args</code> must refuse to send <code>team_id</code> and <code>enterprise_id</code> together, which is the documented exclusivity that would otherwise be discovered against a live organization.",
"test_py_file": "test_slack_app_approval_map.py",
"test_py": '''import pytest

from slack_app_approval_map import (
    READS, app_ids, coverage, listing_status, request_age, scope_args,
    stalled_requests, status_map, verdict,
)

APP = "A0123"
NOW = 1_700_000_000.0
DAY = 86400.0


def test_only_list_methods_are_ever_called():
    assert all(name.endswith(".list") for name in READS)


def test_the_two_scopes_cannot_be_combined():
    with pytest.raises(ValueError):
        scope_args(team_id="T1", enterprise_id="E1")


def test_each_scope_produces_its_own_parameter():
    assert scope_args(team_id="T1")[0]["team_id"] == "T1"
    assert scope_args(enterprise_id="E1")[0]["enterprise_id"] == "E1"
    assert "team_id" not in scope_args(enterprise_id="E1")[0]


def test_app_ids_are_read_from_the_nested_app_object():
    assert app_ids([{"app": {"id": "A1"}}, {"app_id": "A2"}, {}]) == ["A1", "A2"]


def test_a_restricted_app_is_named_as_such():
    state, why = listing_status(APP, [], [APP])
    assert state == "restricted"
    assert "restricted list" in why


def test_an_unlisted_app_is_not_reported_as_allowed():
    state, why = listing_status(APP, ["A9"], ["A8"])
    assert state == "unlisted"
    assert "do not report" in why
    assert "allowed" not in state


def test_being_on_both_lists_is_surfaced_rather_than_resolved():
    assert listing_status(APP, [APP], [APP])[0] == "contradictory"


def test_the_split_is_the_finding_and_it_names_the_workspaces():
    rows = [("T1", "approved"), ("T2", "approved"), ("T3", "restricted"),
            ("T4", "restricted"), ("T5", "unlisted")]
    shape, detail, named = status_map(rows)
    assert shape == "split"
    assert named == ["T3", "T4"]
    assert "restricted in 2" in detail


def test_a_uniform_approval_names_nobody():
    shape, _detail, named = status_map([("T1", "approved"), ("T2", "approved")])
    assert shape == "uniform-approved"
    assert named == []


def test_unlisted_everywhere_has_its_own_shape():
    assert status_map([("T1", "unlisted")])[0] == "unlisted-everywhere"


def test_a_request_is_aged_against_a_clock_you_pass_in():
    days, detail = request_age({"date_created": NOW - 41 * DAY,
                                "user": {"id": "U7"}, "team": {"id": "T14"}}, NOW)
    assert days == 41.0
    assert "U7" in detail and "T14" in detail


def test_a_request_without_a_date_is_unknown_rather_than_zero():
    assert request_age({"id": "R1"}, NOW)[0] is None


def test_only_the_old_requests_are_findings_and_the_oldest_leads():
    queue = [{"id": "R1", "date_created": NOW - 41 * DAY},
             {"id": "R2", "date_created": NOW - 2 * DAY},
             {"id": "R3", "date_created": NOW - 60 * DAY}]
    stalled = stalled_requests(queue, NOW, 30)
    assert [row[0] for row in stalled] == ["R3", "R1"]


def test_a_partial_map_says_the_rest_are_unmeasured():
    state, why = coverage(8, 40)
    assert state == "partial"
    assert "not approved" in why


def test_a_full_map_says_full():
    assert coverage(39, 39)[0] == "full"


def test_the_verdict_counts_workspaces_and_requests_together():
    state, summary = verdict("split", ["T3"], [("R1", 41.0, "")])
    assert state == "2 finding(s)"
    assert "1 restricted" in summary


def test_a_clean_org_says_so():
    assert verdict("uniform-approved", [], [])[0] == "clean"
''',
"test_js_file": "slack-app-approval-map.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  READS, appIds, coverage, listingStatus, requestAge, scopeArgs, stalledRequests,
  statusMap, verdict,
} from './slack-app-approval-map.mjs';

const APP = 'A0123';
const NOW = 1700000000;
const DAY = 86400;

test('only list methods are ever called', () => {
  assert.equal(READS.every((name) => name.endsWith('.list')), true);
});

test('the two scopes cannot be combined', () => {
  assert.throws(() => scopeArgs({ teamId: 'T1', enterpriseId: 'E1' }));
});

test('each scope produces its own parameter', () => {
  assert.equal(scopeArgs({ teamId: 'T1' })[0].team_id, 'T1');
  assert.equal(scopeArgs({ enterpriseId: 'E1' })[0].enterprise_id, 'E1');
  assert.equal('team_id' in scopeArgs({ enterpriseId: 'E1' })[0], false);
});

test('app ids are read from the nested app object', () => {
  assert.deepEqual(appIds([{ app: { id: 'A1' } }, { app_id: 'A2' }, {}]), ['A1', 'A2']);
});

test('a restricted app is named as such', () => {
  const [state, why] = listingStatus(APP, [], [APP]);
  assert.equal(state, 'restricted');
  assert.match(why, /restricted list/);
});

test('an unlisted app is not reported as allowed', () => {
  const [state, why] = listingStatus(APP, ['A9'], ['A8']);
  assert.equal(state, 'unlisted');
  assert.match(why, /do not report/);
});

test('being on both lists is surfaced rather than resolved', () => {
  assert.equal(listingStatus(APP, [APP], [APP])[0], 'contradictory');
});

test('the split is the finding and it names the workspaces', () => {
  const rows = [['T1', 'approved'], ['T2', 'approved'], ['T3', 'restricted'],
    ['T4', 'restricted'], ['T5', 'unlisted']];
  const [shape, detail, named] = statusMap(rows);
  assert.equal(shape, 'split');
  assert.deepEqual(named, ['T3', 'T4']);
  assert.match(detail, /restricted in 2/);
});

test('a uniform approval names nobody', () => {
  const [shape, , named] = statusMap([['T1', 'approved'], ['T2', 'approved']]);
  assert.equal(shape, 'uniform-approved');
  assert.deepEqual(named, []);
});

test('unlisted everywhere has its own shape', () => {
  assert.equal(statusMap([['T1', 'unlisted']])[0], 'unlisted-everywhere');
});

test('a request is aged against a clock you pass in', () => {
  const [days, detail] = requestAge({ date_created: NOW - 41 * DAY,
    user: { id: 'U7' }, team: { id: 'T14' } }, NOW);
  assert.equal(days, 41);
  assert.match(detail, /U7/);
  assert.match(detail, /T14/);
});

test('a request without a date is unknown rather than zero', () => {
  assert.equal(requestAge({ id: 'R1' }, NOW)[0], null);
});

test('only the old requests are findings and the oldest leads', () => {
  const queue = [{ id: 'R1', date_created: NOW - 41 * DAY },
    { id: 'R2', date_created: NOW - 2 * DAY },
    { id: 'R3', date_created: NOW - 60 * DAY }];
  assert.deepEqual(stalledRequests(queue, NOW, 30).map(([id]) => id), ['R3', 'R1']);
});

test('a partial map says the rest are unmeasured', () => {
  const [state, why] = coverage(8, 40);
  assert.equal(state, 'partial');
  assert.match(why, /not approved/);
});

test('a full map says full', () => {
  assert.equal(coverage(39, 39)[0], 'full');
});

test('the verdict counts workspaces and requests together', () => {
  const [state, summary] = verdict('split', ['T3'], [['R1', 41, '']]);
  assert.equal(state, '2 finding(s)');
  assert.match(summary, /1 restricted/);
});

test('a clean org says so', () => {
  assert.equal(verdict('uniform-approved', [], [])[0], 'clean');
});
''',
"faq": [
 ("How is this different from the app_access_restricted note?",
  "That note starts from a runtime error that some people get and some do not, and resolves it into a cohort: the four users who were refused are all multi-channel guests, or all in one workspace. This note starts from your app id and produces a map over the organization's workspaces, showing where your app is approved and where it is restricted. Its most common finding produces no runtime error for anybody, because it is an approval request nobody has actioned, and nothing has been refused yet."),
 ("I have no admin token. Can I still see this?",
  "Not directly. An app's listing status is not exposed to the app itself; the three list methods all want a user token held by an org Admin or Owner. What is left is inference from the outside: the aggregate app_access_restricted rate for a given team id, and the fact that installs from one customer have stopped. If the customer is willing, the fastest path is asking their administrator to look at Organization settings rather than trying to deduce it."),
 ("The app is on neither list. Is that good news?",
  "It is not news at all, which is why the script refuses to call it allowed. Whether an unlisted app can be installed depends on whether the organization requires app approval, and neither of these methods reports that setting. In an org that requires approval, unlisted means members must raise a request first, and that request is where installs go to wait. Ask the administrator which posture their org is in, once, and record it per customer."),
 ("Why check per workspace when there is an org-level list?",
  "Because both exist and they can disagree. The methods accept either a team_id or an enterprise_id, and an app can be approved at the org level and restricted in an individual workspace, which is the exact configuration that produces the phone call about the app working everywhere except in Legal. Querying only the org level answers a narrower question than the one you have, and the per-workspace map is what names the workspaces to raise."),
 ("Can the script ask for approval, or approve the app itself?",
  "No, on both counts, and deliberately. The approve and restrict methods change the customer's organization and no diagnostic in this section calls a method like that. Raising an approval request is also an action taken by a member of that organization, not by your app. What this produces is the sentence an administrator can act on: this app is restricted in these two workspaces, and these requests have been pending for forty-one days."),
],
"related": [
 ("/slack/app-access-restricted/", "the same policy met by one person, at runtime"),
 ("/slack/admin-method-needs-user-token/", "the token these three reads need"),
 ("/slack/app-not-distributed/", "the install that fails before any of this"),
],
"citations": [CITE_ADMIN_APPS_RESTRICTED, CITE_ADMIN_APPS_APPROVED,
              CITE_ADMIN_APPS_REQUESTS, CITE_ADMIN_TEAMS_LIST],
})

GUIDES.append({
"slug": "ekm-access-denied",
"title": "ekm_access_denied: the customer holds the keys",
"description": "Enterprise Key Management refuses the content, not the caller. Map which channels are affected with two reads each, then skip them instead of retrying.",
"h1": "ekm_access_denied: the customer holds the keys",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack ekm_access_denied error",
             "slack enterprise key management app",
             "slack conversations.history ekm_access_denied",
             "slack admins have disabled sending messages to this channel",
             "slack ekm revoked key channel"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a bot or user token with channels:read and channels:history, and the list of channel ids your app works in",
"lead": "<code>{\"ok\": false, \"error\": \"ekm_access_denied\"}</code>, and the human-readable version Slack prints beside it: &ldquo;Your message couldn't be sent because your admins have disabled sending messages to this channel.&rdquo; It affects eleven channels out of two hundred. It started on a Thursday. Nothing you deployed went out that week.</p><p>Every instinct says scope. It is not a scope, and no grant you can request will change it, because this refusal is not about your app at all: it is about a key. The customer's organization holds its own encryption keys for its Slack content, somebody revoked access to some of them, and Slack is now declining to decrypt that content for anybody &mdash; including you, with a perfectly valid token and every scope you asked for.",
"short_answer": """<p>Enterprise Key Management lets an organization encrypt its Slack content with keys it controls: messages, files, the search index, and the messages and files generated by apps and bots. When access to a key is revoked, Slack refuses the content it protects. The error is <code>ekm_access_denied</code>, and it appears in the documented error list of read methods as well as writes &mdash; <code>conversations.history</code>, <code>conversations.info</code> and <code>admin.teams.list</code> all carry it, alongside <code>chat.postMessage</code>.</p>
<p>That matters, because it means the extent is measurable read-only. Two reads per channel &mdash; <code>conversations.info</code> for the metadata and <code>conversations.history?limit=1</code> for the content &mdash; produce a map of what your app can still see, and the two layers can disagree: a channel whose metadata answers while its history is refused is the characteristic shape of content held under a key you have lost access to.</p>
<p><strong>Do not retry.</strong> This is a decision recorded in a customer's key management, not a condition that clears. The tenth attempt is refused identically, and a retry loop turns a policy into rate-limit pressure and a job that never finishes. Skip the affected channels, complete the run over the rest, and report the affected set once.</p>
<p>And be careful about the words used for the extent. Slack documents that access can be revoked granularly and does not publish the exact levels, so the shape in the output below is an inference from what was observed, and labelled as one.</p>""",
"problem": """<p>The first difficulty is that it reads like every other refusal. <code>ekm_access_denied</code> arrives in the same envelope as <code>missing_scope</code> and <code>not_in_channel</code>, inside an HTTP 200, and lands in the same catch block. A team that has been trained by this API to respond to a refusal by checking the scope list will check the scope list, find nothing wrong, reinstall, find nothing changed, and start looking for the bug they introduced. There is no bug. There is nothing on your side to find.</p>
<p>The second is the partial extent. If everything failed you would have an outage and an obvious cause; instead eleven channels out of two hundred fail while the rest are fine, which looks exactly like a data problem in your own code. Engineers reach for the channels themselves &mdash; are they archived, private, externally shared, unusually old &mdash; and the shared property is not a property of the channels at all, it is which key protects them.</p>
<p>The third is retry behaviour, and it is the expensive one. A refusal that arrives intermittently across a run trains a queue into retrying, and the retries are refused identically because nothing about the situation changes between attempts. A job that would have finished in four minutes runs for an hour, burns quota that other calls needed, and ends with the same eleven failures it started with. Worse, the retry noise buries a genuine transient failure somewhere in the same log.</p>
<p>The fourth is escalation. This is one of the few problems in the section where the correct response is a message to somebody else's administrator, and the message has to contain enough for them to act: which channels, which workspace, and the specific error string, because from their side the question is which key was revoked and when. A monitoring alert that says "Slack errors elevated" cannot start that conversation. A line that names eleven channels in one workspace and one error string can.</p>""",
"why": """<p><strong>Two reads per channel, because the two layers answer different questions.</strong> <code>conversations.info</code> asks whether the channel's metadata is visible; <code>conversations.history?limit=1</code> asks whether its content is. Both document <code>ekm_access_denied</code>. When the first answers and the second does not, you are looking at content protected by a key rather than at a channel you cannot see, and that distinction is what stops this being misfiled as a membership or scope problem.</p>
<p><strong>The other refusals are separated out, and one of them stays ambiguous on purpose.</strong> <code>not_in_channel</code> means <a href="/slack/bot-not-in-channel/">invite the bot</a>; <code>missing_scope</code> means <a href="/slack/missing-scope-on-read/">grant the scope</a>. <code>channel_not_found</code> is genuinely undecidable from outside: a channel that does not exist and a private channel your token cannot see return the same thing, and a script that picks one is confidently wrong about half the time. It is reported as ambiguous and left that way.</p>
<p><strong>The extent is an inference and is labelled an inference.</strong> Slack documents that an organization can revoke granular access to its keys and does not publish the granularity, so &ldquo;this looks workspace-wide&rdquo; is a description of the rows collected, not a claim about how the customer's key policy is configured. The function that produces it returns a confidence alongside the shape, and the confidence is always the same value, which is the honest one.</p>
<p><strong>Retry classification is a first-class output rather than a note in the prose.</strong> <code>retry_class</code> puts <code>ekm_access_denied</code> in <code>do-not-retry</code> next to the errors that genuinely should back off, so the difference is expressed in code that your job can import rather than in a paragraph somebody has to remember. A policy is not a transient condition and treating it as one is the most common expensive mistake here.</p>
<p><strong>The output is built to be forwarded.</strong> The affected set, the workspace, the error string and the shape are printed as a block because the next step is a message to the customer's administrator, and the useful version of that message is specific. No app-side change affects this, so anything the script prints about your configuration would be a distraction.</p>
<p><strong>Everything is a read, and the write that produced the original symptom is not repeated.</strong> The complaint that starts this investigation is usually a failed <code>chat.postMessage</code>. The script never posts to find out whether posting works; it maps what can be read, which is enough to establish the extent and costs the workspace nothing.</p>""",
"steps": [
 {"h": "Take the channel list from your app, not from the workspace",
  "body": """<p>Pass <code>--channels</code> with the ids your integration actually works in. Sweeping every channel in the workspace produces a bigger map that answers a question nobody asked, and costs a great deal more quota.</p>"""},
 {"h": "Ask each channel twice",
  "body": """<p><code>conversations.info</code> then <code>conversations.history?limit=1</code>. One request each, and the pair is what distinguishes content held under a revoked key from a channel that is simply invisible to this token.</p>"""},
 {"h": "Classify each response rather than counting failures",
  "body": """<p><code>read_outcome</code> returns <code>ok</code>, <code>blocked</code>, <code>ambiguous</code> or <code>other</code>, and names the error. Only <code>ekm_access_denied</code> becomes <code>blocked</code>; <code>channel_not_found</code> becomes <code>ambiguous</code> and stays there.</p>"""},
 {"h": "Read the two layers together",
  "body": """<p><code>layer</code> combines the metadata outcome with the content outcome: <code>content-blocked</code> is the characteristic EKM shape, <code>both-blocked</code> is broader, and <code>clear</code> is a channel with nothing wrong with it.</p>"""},
 {"h": "Describe the extent, and say that it is inferred",
  "body": """<p><code>extent_shape</code> reports whether the blocked channels are scattered, confined to one workspace, or everything measured. It returns a confidence, and that confidence is always <code>inferred</code>, because the granularity of key revocation is not published.</p>"""},
 {"h": "Skip, do not retry, and send the block to an administrator",
  "body": """<p><code>skip_plan</code> lists the channels the job should pass over so the run completes. <code>retry_class</code> keeps <code>ekm_access_denied</code> out of your backoff path. Then send the affected list, the workspace and the error string to the customer's Slack administrators, which is where the only available repair lives.</p>"""},
],
"verify": """<p>After the customer's administrators restore access, re-run over the same list. Every channel should read <code>clear</code>, and the skip plan should be empty.</p>
<pre><code class="language-bash">python3 slack_ekm_extent.py --channels C001,C002,C003,C004
# channel    C001             metadata=ok      content=ok        clear
# channel    C002             metadata=ok      content=blocked   content-blocked
# channel    C003             metadata=blocked content=blocked   both-blocked
# channel    C004             metadata=ok      content=ambiguous  unknown
#            note             channel_not_found is undecidable from here: absent, or
#                             invisible to this token
# extent     partial          inferred  2 of 4 channel(s) blocked, all in T0123
# retry      do-not-retry     ekm_access_denied is a decision, not a condition
# skip       C002,C003        skip these so the run completes over the rest
# verdict    2 finding(s)     escalate to the customer's Slack administrators
#   repair: no app side change affects this; access to the key is theirs to restore
#   repair: treat ekm_access_denied as a permanent per channel failure and skip it
#   repair: alert on it distinctly, so it is never read as a scope problem again</code></pre>""",
"code_intro": "Two reads per channel and one classifier per layer. <code>read_outcome</code> is where the discipline sits: only <code>ekm_access_denied</code> becomes <code>blocked</code>, <code>channel_not_found</code> becomes <code>ambiguous</code> and is never resolved into a guess, and every other refusal is named and handed on. <code>layer</code> reads the metadata and content outcomes as a pair, which is what makes the EKM shape recognisable rather than just another failure. <code>extent_shape</code> returns a confidence with its shape and that confidence never rises above <code>inferred</code>, because the granularity of key revocation is not published. <code>retry_class</code> and <code>skip_plan</code> exist so a job can import the two behaviours that matter.",
"py_file": "slack_ekm_extent.py",
"py": '''"""Map how far an Enterprise Key Management refusal reaches, read only.

ekm_access_denied is not about your app. An organization using Enterprise Key
Management holds its own encryption keys for its Slack content, and when
access to a key is revoked Slack declines to serve the content it protects to
anybody, with any token, holding any scope. There is no app side repair.

What an app can usefully do is measure the extent and stop retrying. Two reads
per channel: conversations.info for the metadata layer and
conversations.history with limit=1 for the content layer. Both document
ekm_access_denied in their error lists, and the two layers can disagree, which
is what makes this recognisable rather than just another refusal.

The extent is reported as an inference. Slack documents that an organization
can revoke granular access to its keys and does not publish the exact
granularity, so the shape below describes the rows that were collected and
makes no claim about how the customer's policy is configured.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_ekm_extent")

API = "https://slack.com/api/"

EKM_ERROR = "ekm_access_denied"

# Refusals that are somebody else's note. Named so a sweep that meets one hands
# the reader on rather than filing it under encryption.
ELSEWHERE = {
    "not_in_channel": "/slack/bot-not-in-channel/",
    "missing_scope": "/slack/missing-scope-on-read/",
    "is_archived": "/slack/archived-channel-target/",
    "accesslimited": "/slack/accesslimited-ip-allowlist/",
    "not_allowed_token_type": "/slack/admin-method-needs-user-token/",
}

# Errors that a job should back off on, as against the one it must not.
TRANSIENT = ("ratelimited", "internal_error", "service_unavailable", "fatal_error",
             "request_timeout")


def read_outcome(body):
    """Read one response as an outcome for one layer. Pure.

    Returns (state, detail). Four states:

      ok         the layer answered.
      blocked    ekm_access_denied, and nothing else produces this.
      ambiguous  channel_not_found, which is undecidable from outside: absent,
                 or present and invisible to this token. Left undecided.
      other      any other refusal, named, and handed on where a note owns it.
    """
    doc = body or {}
    if doc.get("ok") is True:
        return ("ok", "the layer answered")
    error = str(doc.get("error") or "unknown_error")
    if error == EKM_ERROR:
        return ("blocked", "ekm_access_denied; the content is protected by a key this "
                           "token no longer has access to")
    if error == "channel_not_found":
        return ("ambiguous", "channel_not_found is undecidable from here: absent, or "
                             "invisible to this token")
    pointer = ELSEWHERE.get(error)
    if pointer:
        return ("other", "%s; that refusal is owned by %s" % (error, pointer))
    return ("other", "%s; not an encryption refusal" % error)


def layer(metadata_state, content_state):
    """Read the two layers together. Pure.

    The pair is the diagnosis. Metadata that answers while content is refused
    is the characteristic shape of a key revocation, because the channel is
    plainly there and its contents are what cannot be served.
    """
    if metadata_state == "blocked" and content_state == "blocked":
        return ("both-blocked", "neither the channel's metadata nor its content can "
                                "be served")
    if content_state == "blocked":
        return ("content-blocked", "the channel is visible and its content is not; "
                                   "this is the characteristic shape")
    if metadata_state == "blocked":
        return ("metadata-blocked", "the metadata is refused while content answered, "
                                    "which is unusual and worth reporting as seen")
    if "ambiguous" in (metadata_state, content_state):
        return ("unknown", "one layer was undecidable, so this channel is neither "
                           "cleared nor counted")
    if metadata_state == "ok" and content_state == "ok":
        return ("clear", "both layers answered")
    return ("other", "a refusal that is not about encryption")


def extent_shape(rows):
    """Describe how far the blocking reaches. Pure.

    rows: [(channel, team_id, layer_state), ...]. Returns (shape, confidence,
    detail). The confidence is always "inferred": Slack documents granular
    revocation and does not publish the granularity, so this describes the
    rows collected rather than the customer's policy.
    """
    total = len(rows or [])
    blocked = [r for r in (rows or []) if r[2] in ("content-blocked", "both-blocked",
                                                   "metadata-blocked")]
    if not total:
        return ("none-measured", "inferred", "no channels were read")
    if not blocked:
        return ("clear", "inferred", "no channel in this set was refused")
    teams = {r[1] for r in blocked if r[1]}
    where = "all in %s" % list(teams)[0] if len(teams) == 1 else \\
            "across %d workspace(s)" % len(teams)
    detail = "%d of %d channel(s) blocked, %s" % (len(blocked), total, where)
    if len(blocked) == total:
        return ("everything-measured", "inferred", detail)
    return ("partial", "inferred", detail)


def retry_class(error):
    """What should a job do with this error? Pure.

    The one behaviour worth importing. ekm_access_denied is a decision recorded
    in a customer's key management, not a condition that clears, and retrying
    it converts a policy into rate limit pressure and a job that never
    finishes.
    """
    name = str(error or "").strip()
    if name == EKM_ERROR:
        return ("do-not-retry", "a decision, not a condition; the tenth attempt is "
                                "refused identically")
    if name in TRANSIENT:
        return ("backoff", "a condition that may clear; retry with backoff")
    if name in ELSEWHERE:
        return ("do-not-retry", "a configuration problem; retrying cannot fix it")
    if not name:
        return ("proceed", "no error")
    return ("retry-once", "unrecognised; one retry, then report it rather than "
                          "looping")


def skip_plan(rows):
    """The channels a run should pass over so it completes. Pure."""
    return [r[0] for r in (rows or []) if r[2] in ("content-blocked", "both-blocked",
                                                   "metadata-blocked")]


def alerting(shape):
    """How should this be surfaced? Pure.

    Deliberately never a page. Nothing on call can act on a customer's key
    policy at three in the morning, and an alert that wakes somebody up to
    tell them a decision was made is training them to ignore alerts.
    """
    if shape in ("clear", "none-measured"):
        return ("none", "nothing to report")
    if shape == "everything-measured":
        return ("escalate", "every channel measured is refused; tell the customer's "
                            "administrators today, and do not page your own on call")
    return ("notify", "report the affected set distinctly, so it is never read as a "
                      "scope problem; this is not an outage on your side")


def verdict(rows):
    """One line for the sweep. Pure."""
    blocked = skip_plan(rows)
    unknown = [r[0] for r in (rows or []) if r[2] == "unknown"]
    if not rows:
        return ("inconclusive", "no channels were read")
    if not blocked:
        return ("clean", "no channel in this set is refused on encryption grounds")
    return ("%d finding(s)" % len(blocked),
            "escalate to the customer's Slack administrators%s"
            % ("; %d channel(s) undecided" % len(unknown) if unknown else ""))


def get(session, method, params):
    """One GET. Returns the parsed body."""
    r = session.get(API + method, params=params, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--channels", required=True,
                    help="comma separated channel ids your app works in")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a read scoped token")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("token      missing        set %s", args.token_env)
        return 2
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    auth = get(session, "auth.test", {})
    team_id = auth.get("team_id") or ""
    if auth.get("enterprise_id"):
        log.info("context    %-16s enterprise_id=%s, so key management is available "
                 "to this organization", team_id, auth.get("enterprise_id"))
    else:
        log.info("context    %-16s no enterprise_id on auth.test", team_id or "?")

    rows = []
    for channel in [c.strip() for c in args.channels.split(",") if c.strip()]:
        meta_state, meta_why = read_outcome(
            get(session, "conversations.info", {"channel": channel}))
        content_state, content_why = read_outcome(
            get(session, "conversations.history", {"channel": channel, "limit": 1}))
        state, why = layer(meta_state, content_state)
        level = log.info if state == "clear" else log.warning
        level("channel    %-16s metadata=%-9s content=%-9s %s", channel, meta_state,
              content_state, state)
        if state != "clear":
            log.info("           note             %s", why)
        for detail in (meta_why, content_why):
            if "owned by" in detail or "undecidable" in detail:
                log.info("           note             %s", detail)
        rows.append((channel, team_id, state))

    shape, confidence, detail = extent_shape(rows)
    (log.info if shape == "clear" else log.warning)(
        "extent     %-16s %-9s %s", shape, confidence, detail)

    action, why = retry_class(EKM_ERROR)
    log.info("retry      %-16s %s", action, why)

    skip = skip_plan(rows)
    if skip:
        log.warning("skip       %-16s skip these so the run completes over the rest",
                    ",".join(skip[:8]))

    route, route_why = alerting(shape)
    log.info("alert      %-16s %s", route, route_why)

    final, summary = verdict(rows)
    if final == "clean":
        log.info("verdict    clean            %s", summary)
        return 0
    log.warning("verdict    %-16s %s", final, summary)
    log.warning("  repair: no app side change affects this; access to the key is the "
                "customer's to restore")
    log.warning("  repair: treat %s as a permanent per channel failure and skip the "
                "affected channels rather than blocking the run", EKM_ERROR)
    log.warning("  repair: alert on it distinctly, so it is never read as a scope "
                "problem again")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-ekm-extent.mjs",
"js": '''/**
 * Map how far an Enterprise Key Management refusal reaches, read only.
 *
 * ekm_access_denied is not about your app. An organization using Enterprise
 * Key Management holds its own encryption keys for its Slack content, and when
 * access to a key is revoked Slack declines to serve the content it protects
 * to anybody, with any token, holding any scope. There is no app side repair.
 *
 * Two reads per channel: conversations.info for the metadata layer and
 * conversations.history with limit=1 for the content layer. Both document
 * ekm_access_denied, and the two layers can disagree, which is what makes this
 * recognisable rather than just another refusal.
 *
 * The extent is reported as an inference, because Slack documents granular
 * key revocation without publishing the granularity.
 */

const API = 'https://slack.com/api/';

export const EKM_ERROR = 'ekm_access_denied';

export const ELSEWHERE = {
  not_in_channel: '/slack/bot-not-in-channel/',
  missing_scope: '/slack/missing-scope-on-read/',
  is_archived: '/slack/archived-channel-target/',
  accesslimited: '/slack/accesslimited-ip-allowlist/',
  not_allowed_token_type: '/slack/admin-method-needs-user-token/',
};

export const TRANSIENT = ['ratelimited', 'internal_error', 'service_unavailable',
  'fatal_error', 'request_timeout'];

export function readOutcome(body) {
  const doc = body ?? {};
  if (doc.ok === true) return ['ok', 'the layer answered'];
  const error = String(doc.error ?? 'unknown_error');
  if (error === EKM_ERROR) {
    return ['blocked', 'ekm_access_denied; the content is protected by a key this '
      + 'token no longer has access to'];
  }
  if (error === 'channel_not_found') {
    return ['ambiguous', 'channel_not_found is undecidable from here: absent, or '
      + 'invisible to this token'];
  }
  const pointer = ELSEWHERE[error];
  if (pointer) return ['other', `${error}; that refusal is owned by ${pointer}`];
  return ['other', `${error}; not an encryption refusal`];
}

// The pair is the diagnosis.
export function layer(metadataState, contentState) {
  if (metadataState === 'blocked' && contentState === 'blocked') {
    return ['both-blocked', "neither the channel's metadata nor its content can be served"];
  }
  if (contentState === 'blocked') {
    return ['content-blocked', 'the channel is visible and its content is not; this is '
      + 'the characteristic shape'];
  }
  if (metadataState === 'blocked') {
    return ['metadata-blocked', 'the metadata is refused while content answered, which '
      + 'is unusual and worth reporting as seen'];
  }
  if (metadataState === 'ambiguous' || contentState === 'ambiguous') {
    return ['unknown', 'one layer was undecidable, so this channel is neither cleared '
      + 'nor counted'];
  }
  if (metadataState === 'ok' && contentState === 'ok') return ['clear', 'both layers answered'];
  return ['other', 'a refusal that is not about encryption'];
}

// The confidence is always "inferred".
export function extentShape(rows) {
  const all = rows ?? [];
  const blocked = all.filter(([, , state]) => ['content-blocked', 'both-blocked',
    'metadata-blocked'].includes(state));
  if (!all.length) return ['none-measured', 'inferred', 'no channels were read'];
  if (!blocked.length) {
    return ['clear', 'inferred', 'no channel in this set was refused'];
  }
  const teams = [...new Set(blocked.map(([, team]) => team).filter(Boolean))];
  const where = teams.length === 1 ? `all in ${teams[0]}`
    : `across ${teams.length} workspace(s)`;
  const detail = `${blocked.length} of ${all.length} channel(s) blocked, ${where}`;
  if (blocked.length === all.length) return ['everything-measured', 'inferred', detail];
  return ['partial', 'inferred', detail];
}

// The one behaviour worth importing.
export function retryClass(error) {
  const name = String(error ?? '').trim();
  if (name === EKM_ERROR) {
    return ['do-not-retry', 'a decision, not a condition; the tenth attempt is refused '
      + 'identically'];
  }
  if (TRANSIENT.includes(name)) {
    return ['backoff', 'a condition that may clear; retry with backoff'];
  }
  if (name in ELSEWHERE) {
    return ['do-not-retry', 'a configuration problem; retrying cannot fix it'];
  }
  if (!name) return ['proceed', 'no error'];
  return ['retry-once', 'unrecognised; one retry, then report it rather than looping'];
}

export function skipPlan(rows) {
  return (rows ?? []).filter(([, , state]) => ['content-blocked', 'both-blocked',
    'metadata-blocked'].includes(state)).map(([channel]) => channel);
}

// Deliberately never a page.
export function alerting(shape) {
  if (shape === 'clear' || shape === 'none-measured') return ['none', 'nothing to report'];
  if (shape === 'everything-measured') {
    return ['escalate', "every channel measured is refused; tell the customer's "
      + 'administrators today, and do not page your own on call'];
  }
  return ['notify', 'report the affected set distinctly, so it is never read as a scope '
    + 'problem; this is not an outage on your side'];
}

export function verdict(rows) {
  const blocked = skipPlan(rows);
  const unknown = (rows ?? []).filter(([, , state]) => state === 'unknown');
  if (!(rows ?? []).length) return ['inconclusive', 'no channels were read'];
  if (!blocked.length) {
    return ['clean', 'no channel in this set is refused on encryption grounds'];
  }
  return [`${blocked.length} finding(s)`,
    "escalate to the customer's Slack administrators"
    + (unknown.length ? `; ${unknown.length} channel(s) undecided` : '')];
}

function arg(args, name, fallback = '') {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

async function read(token, method, params) {
  const url = new URL(API + method);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  try {
    return await r.json();
  } catch {
    return { ok: false, error: 'unparseable_body' };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const channels = arg(args, '--channels').split(',').map((c) => c.trim()).filter(Boolean);
  if (!channels.length) {
    console.error('pass --channels with the channel ids your app works in');
    process.exitCode = 2;
    return;
  }
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`token      missing        set ${tokenEnv}`);
    process.exitCode = 2;
    return;
  }

  const auth = await read(token, 'auth.test', {});
  const teamId = auth.team_id ?? '';
  if (auth.enterprise_id) {
    console.log(`context    ${String(teamId).padEnd(16)} enterprise_id=`
      + `${auth.enterprise_id}, so key management is available to this organization`);
  } else {
    console.log(`context    ${String(teamId || '?').padEnd(16)} no enterprise_id on auth.test`);
  }

  const rows = [];
  for (const channel of channels) {
    // eslint-disable-next-line no-await-in-loop
    const [metaState, metaWhy] = readOutcome(await read(token, 'conversations.info',
      { channel }));
    // eslint-disable-next-line no-await-in-loop
    const [contentState, contentWhy] = readOutcome(await read(token,
      'conversations.history', { channel, limit: 1 }));
    const [state, why] = layer(metaState, contentState);
    const line = `channel    ${channel.padEnd(16)} metadata=${metaState.padEnd(9)} `
      + `content=${contentState.padEnd(9)} ${state}`;
    if (state === 'clear') console.log(line);
    else console.warn(line);
    if (state !== 'clear') console.log(`           note             ${why}`);
    for (const detail of [metaWhy, contentWhy]) {
      if (detail.includes('owned by') || detail.includes('undecidable')) {
        console.log(`           note             ${detail}`);
      }
    }
    rows.push([channel, teamId, state]);
  }

  const [shape, confidence, detail] = extentShape(rows);
  const extentLine = `extent     ${shape.padEnd(16)} ${confidence.padEnd(9)} ${detail}`;
  if (shape === 'clear') console.log(extentLine);
  else console.warn(extentLine);

  const [action, why] = retryClass(EKM_ERROR);
  console.log(`retry      ${action.padEnd(16)} ${why}`);

  const skip = skipPlan(rows);
  if (skip.length) {
    console.warn(`skip       ${skip.slice(0, 8).join(',').padEnd(16)} skip these so the `
      + 'run completes over the rest');
  }

  const [route, routeWhy] = alerting(shape);
  console.log(`alert      ${route.padEnd(16)} ${routeWhy}`);

  const [final, summary] = verdict(rows);
  if (final === 'clean') {
    console.log(`verdict    clean            ${summary}`);
    return;
  }
  console.warn(`verdict    ${final.padEnd(16)} ${summary}`);
  console.warn('  repair: no app side change affects this; access to the key is the '
    + "customer's to restore");
  console.warn(`  repair: treat ${EKM_ERROR} as a permanent per channel failure and `
    + 'skip the affected channels rather than blocking the run');
  console.warn('  repair: alert on it distinctly, so it is never read as a scope '
    + 'problem again');
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions that carry this note are about restraint again, in three places. <code>channel_not_found</code> has to stay <code>ambiguous</code> and must never be resolved into either an absence or a block, because Slack genuinely does not say which it is. <code>ekm_access_denied</code> has to land in <code>do-not-retry</code>, next to a test that puts <code>ratelimited</code> in <code>backoff</code>, so the difference between a policy and a condition is checked rather than described. And <code>extent_shape</code> has to return <code>inferred</code> for every input, including the ones where the pattern looks obvious, because the granularity of key revocation is not published and a script that says <code>workspace-level</code> with confidence is asserting something nobody outside the customer's organization knows.",
"test_py_file": "test_slack_ekm_extent.py",
"test_py": '''from slack_ekm_extent import (
    alerting, extent_shape, layer, read_outcome, retry_class, skip_plan, verdict,
)

BLOCKED = {"ok": False, "error": "ekm_access_denied"}
FINE = {"ok": True, "channel": {"id": "C1"}}


def test_only_the_encryption_error_is_blocked():
    assert read_outcome(BLOCKED)[0] == "blocked"
    assert read_outcome(FINE)[0] == "ok"
    assert read_outcome({"ok": False, "error": "not_in_channel"})[0] == "other"


def test_channel_not_found_stays_undecided():
    state, why = read_outcome({"ok": False, "error": "channel_not_found"})
    assert state == "ambiguous"
    assert "undecidable" in why


def test_refusals_owned_elsewhere_are_handed_over_by_name():
    _state, why = read_outcome({"ok": False, "error": "missing_scope"})
    assert "/slack/missing-scope-on-read/" in why


def test_visible_metadata_with_refused_content_is_the_shape():
    state, why = layer("ok", "blocked")
    assert state == "content-blocked"
    assert "characteristic shape" in why


def test_both_layers_refused_is_broader():
    assert layer("blocked", "blocked")[0] == "both-blocked"


def test_a_channel_that_answers_twice_is_clear():
    assert layer("ok", "ok")[0] == "clear"


def test_an_ambiguous_layer_leaves_the_channel_uncounted():
    assert layer("ok", "ambiguous")[0] == "unknown"


def test_the_extent_is_always_inferred():
    rows = [("C1", "T1", "clear"), ("C2", "T1", "content-blocked")]
    shape, confidence, detail = extent_shape(rows)
    assert shape == "partial"
    assert confidence == "inferred"
    assert "all in T1" in detail


def test_the_extent_is_inferred_even_when_everything_is_blocked():
    rows = [("C1", "T1", "both-blocked"), ("C2", "T1", "content-blocked")]
    shape, confidence, _detail = extent_shape(rows)
    assert shape == "everything-measured"
    assert confidence == "inferred"


def test_a_clean_set_reports_clear_and_still_says_inferred():
    assert extent_shape([("C1", "T1", "clear")]) == (
        "clear", "inferred", "no channel in this set was refused")


def test_nothing_measured_is_not_a_clean_result():
    assert extent_shape([])[0] == "none-measured"


def test_the_encryption_error_is_never_retried():
    action, why = retry_class("ekm_access_denied")
    assert action == "do-not-retry"
    assert "not a condition" in why


def test_a_genuine_transient_still_backs_off():
    assert retry_class("ratelimited")[0] == "backoff"


def test_an_unrecognised_error_is_tried_once_and_then_reported():
    assert retry_class("something_new")[0] == "retry-once"


def test_the_skip_plan_lists_the_channels_a_run_should_pass_over():
    rows = [("C1", "T1", "clear"), ("C2", "T1", "content-blocked"),
            ("C3", "T1", "both-blocked"), ("C4", "T1", "unknown")]
    assert skip_plan(rows) == ["C2", "C3"]


def test_this_is_never_a_page():
    assert alerting("partial")[0] == "notify"
    assert alerting("everything-measured")[0] == "escalate"
    assert alerting("clear")[0] == "none"


def test_the_verdict_counts_blocked_channels_and_flags_the_undecided():
    state, summary = verdict([("C1", "T1", "content-blocked"), ("C2", "T1", "unknown")])
    assert state == "1 finding(s)"
    assert "1 channel(s) undecided" in summary


def test_a_clean_sweep_says_clean():
    assert verdict([("C1", "T1", "clear")])[0] == "clean"
''',
"test_js_file": "slack-ekm-extent.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  alerting, extentShape, layer, readOutcome, retryClass, skipPlan, verdict,
} from './slack-ekm-extent.mjs';

const BLOCKED = { ok: false, error: 'ekm_access_denied' };
const FINE = { ok: true, channel: { id: 'C1' } };

test('only the encryption error is blocked', () => {
  assert.equal(readOutcome(BLOCKED)[0], 'blocked');
  assert.equal(readOutcome(FINE)[0], 'ok');
  assert.equal(readOutcome({ ok: false, error: 'not_in_channel' })[0], 'other');
});

test('channel_not_found stays undecided', () => {
  const [state, why] = readOutcome({ ok: false, error: 'channel_not_found' });
  assert.equal(state, 'ambiguous');
  assert.match(why, /undecidable/);
});

test('refusals owned elsewhere are handed over by name', () => {
  const [, why] = readOutcome({ ok: false, error: 'missing_scope' });
  assert.match(why, /\\/slack\\/missing-scope-on-read\\//);
});

test('visible metadata with refused content is the shape', () => {
  const [state, why] = layer('ok', 'blocked');
  assert.equal(state, 'content-blocked');
  assert.match(why, /characteristic shape/);
});

test('both layers refused is broader', () => {
  assert.equal(layer('blocked', 'blocked')[0], 'both-blocked');
});

test('a channel that answers twice is clear', () => {
  assert.equal(layer('ok', 'ok')[0], 'clear');
});

test('an ambiguous layer leaves the channel uncounted', () => {
  assert.equal(layer('ok', 'ambiguous')[0], 'unknown');
});

test('the extent is always inferred', () => {
  const rows = [['C1', 'T1', 'clear'], ['C2', 'T1', 'content-blocked']];
  const [shape, confidence, detail] = extentShape(rows);
  assert.equal(shape, 'partial');
  assert.equal(confidence, 'inferred');
  assert.match(detail, /all in T1/);
});

test('the extent is inferred even when everything is blocked', () => {
  const rows = [['C1', 'T1', 'both-blocked'], ['C2', 'T1', 'content-blocked']];
  const [shape, confidence] = extentShape(rows);
  assert.equal(shape, 'everything-measured');
  assert.equal(confidence, 'inferred');
});

test('a clean set reports clear and still says inferred', () => {
  assert.deepEqual(extentShape([['C1', 'T1', 'clear']]),
    ['clear', 'inferred', 'no channel in this set was refused']);
});

test('nothing measured is not a clean result', () => {
  assert.equal(extentShape([])[0], 'none-measured');
});

test('the encryption error is never retried', () => {
  const [action, why] = retryClass('ekm_access_denied');
  assert.equal(action, 'do-not-retry');
  assert.match(why, /not a condition/);
});

test('a genuine transient still backs off', () => {
  assert.equal(retryClass('ratelimited')[0], 'backoff');
});

test('an unrecognised error is tried once and then reported', () => {
  assert.equal(retryClass('something_new')[0], 'retry-once');
});

test('the skip plan lists the channels a run should pass over', () => {
  const rows = [['C1', 'T1', 'clear'], ['C2', 'T1', 'content-blocked'],
    ['C3', 'T1', 'both-blocked'], ['C4', 'T1', 'unknown']];
  assert.deepEqual(skipPlan(rows), ['C2', 'C3']);
});

test('this is never a page', () => {
  assert.equal(alerting('partial')[0], 'notify');
  assert.equal(alerting('everything-measured')[0], 'escalate');
  assert.equal(alerting('clear')[0], 'none');
});

test('the verdict counts blocked channels and flags the undecided', () => {
  const [state, summary] = verdict([['C1', 'T1', 'content-blocked'],
    ['C2', 'T1', 'unknown']]);
  assert.equal(state, '1 finding(s)');
  assert.match(summary, /1 channel\\(s\\) undecided/);
});

test('a clean sweep says clean', () => {
  assert.equal(verdict([['C1', 'T1', 'clear']])[0], 'clean');
});
''',
"faq": [
 ("Which scope fixes ekm_access_denied?",
  "None of them, and that is the first thing to internalise about it. The refusal is not about your token's permissions; it is about a key held by the customer's organization under Enterprise Key Management. Slack is declining to serve content encrypted with a key whose access has been revoked, and it will decline for any caller with any grant. The only path to it being served again runs through the customer's own administrators."),
 ("Can I tell whether this is one channel, one workspace or the whole organization?",
  "You can describe what you measured, and the script is careful to phrase it that way. Slack documents that an organization can revoke granular access to its encryption keys and does not publish the exact levels at which that happens, so a map showing eleven blocked channels in one workspace is a description of eleven channels, not a statement about the customer's key policy. The confidence value in the output is always inferred for exactly that reason."),
 ("Should the job retry these?",
  "No, and the retry classifier is in the module so your job can import the decision rather than reimplement it. A revoked key is a decision that persists until somebody changes it, so the second attempt and the two-hundredth are refused identically. All a retry loop adds is quota pressure, a job that runs for an hour instead of four minutes, and a log in which a genuinely transient failure is buried among identical permanent ones."),
 ("Why read conversations.info as well as conversations.history?",
  "Because the pair is the diagnosis. Both methods document ekm_access_denied, and when the metadata answers while the content is refused you know the channel is there and visible and that what cannot be served is its contents, which is the characteristic shape of a key problem. If you only called one method you would have a failure that looks like every other failure, and the natural conclusion would be that the bot is not in the channel."),
 ("What exactly should I send the customer?",
  "The specific block: the error string ekm_access_denied, the affected channel ids, the workspace they are in, and roughly when the failures began. Their administrators can look up which key covers that content and whether its access was revoked, which is a question they can answer in minutes and you cannot answer at all. A generic alert that Slack errors are elevated cannot start that conversation, which is why the script prints the affected set as a block rather than a count."),
],
"related": [
 ("/slack/read-only-channel/", "an administrator's decision, made in the channel"),
 ("/slack/accesslimited-ip-allowlist/", "a refusal decided by the network instead"),
 ("/slack/app-restricted-by-admin/", "a policy aimed at the app rather than the content"),
],
"citations": [CITE_EKM, CITE_CONVERSATIONS_HISTORY, CITE_CONVERSATIONS_INFO,
              CITE_CHAT_POSTMESSAGE],
})
