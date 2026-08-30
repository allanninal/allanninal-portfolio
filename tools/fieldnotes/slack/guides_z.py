#!/usr/bin/env python3
"""/slack/ field notes, batch Z - the writing.

Four Enterprise Grid notes, and the only thing that keeps four Grid notes apart
is being ruthless about which object each one is looking at. The section
already publishes several, so each of these is pinned to a noun.

The first looks at a row in your installation store and asks how many
workspaces it has to answer for. An org-wide install is one grant covering an
organisation that may hold forty workspaces, and the documented OAuth response
for it carries "team": null. A lookup that asks for a workspace id and nothing
else finds nothing, forty times over, and the SDK issues are exactly that: a
team_id stored as the literal string "none", and a global shortcut in a
workspace with no row. This is not the note about whether the token reaches a
sibling workspace, and it is not the note about two rows colliding under one
key. It is the note about one row and the workspaces it must serve.

The second looks at a method. enterprise_is_restricted is documented, in every
errors table that carries it, as "The method cannot be called from an
Enterprise" - a refusal attached to the method itself rather than to a person,
a token boundary or a network. The neighbouring note about an admin blocking an
app for a user is about a person; this one is about a name in your call list
and whether an org-level equivalent for it exists.

The third looks at the clock. org_login_required says the workspace "will not
be available until migration is complete", which is a whole installation going
dark for a period measured in hours or days. The finding is a disposition, not
an error: a scheduler that treats this like a revoked token retires a paying
customer, and one that retries it like a rate limit hammers a workspace that
cannot answer.

The fourth looks at an identifier. team_added_to_org is documented as
"intermittently unavailable", and when the window closes the workspace-local
U ids have global W equivalents. migration.exchange is the documented, read-only
mapper between them, and the audit it enables is a cache audit rather than an
availability one.

Read only throughout. Every call is a GET. Nothing installs, joins, posts or
deletes, and no token, client secret or signing secret is read, printed or
transmitted by anything here.
"""

CITE_GRID = ("Enterprise organizations - Slack Docs",
             "https://docs.slack.dev/enterprise-grid/")
CITE_GRID_DEV = ("Developing for Enterprise organizations - Slack Docs",
                 "https://docs.slack.dev/enterprise/developing-for-enterprise-orgs")
CITE_ORG_DEPLOY = ("Migrating to organization-wide deployment - Slack Docs",
                   "https://docs.slack.dev/enterprise/migrating-to-organization-wide-deployment")
CITE_OAUTH_V2 = ("oauth.v2.access method reference - Slack Docs",
                 "https://docs.slack.dev/reference/methods/oauth.v2.access")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_CONVERSATIONS_LIST = ("conversations.list method reference - Slack Docs",
                           "https://docs.slack.dev/reference/methods/conversations.list")
CITE_CONVERSATIONS_HISTORY = ("conversations.history method reference - Slack Docs",
                              "https://docs.slack.dev/reference/methods/conversations.history")
CITE_CHAT_POST = ("chat.postMessage method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_USERS_INFO = ("users.info method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/users.info")
CITE_ADMIN_TEAMS_LIST = ("admin.teams.list method reference - Slack Docs",
                         "https://docs.slack.dev/reference/methods/admin.teams.list")
CITE_ADMIN_USERS_LIST = ("admin.users.list method reference - Slack Docs",
                         "https://docs.slack.dev/reference/methods/admin.users.list")
CITE_MIGRATION_EXCHANGE = ("migration.exchange method reference - Slack Docs",
                           "https://docs.slack.dev/reference/methods/migration.exchange")
CITE_SDK_1639 = ("python-slack-sdk #1639: team ID not set to 'none' when doing an "
                 "org-wide install",
                 "https://github.com/slackapi/python-slack-sdk/issues/1639")
CITE_BOLT_1944 = ("bolt-js #1944: fetchInstallation is not called for a global "
                  "shortcut in a Grid workspace with no install",
                  "https://github.com/slackapi/bolt-js/issues/1944")

GUIDES = []

GUIDES.append({
"slug": "org-wide-install-mishandled",
"title": "is_enterprise_install: one row for forty workspaces",
"description": "An org-wide install is one grant covering every workspace. Enumerate the organisation, simulate your lookup, and count the workspaces that resolve to nothing.",
"h1": "is_enterprise_install: one row for forty workspaces",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack is_enterprise_install true",
             "slack org wide install team_id null",
             "bolt fetchinstallation not called grid",
             "slack installation store org wide fallback",
             "slack team_id none org install"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the org-wide token you want to check, optionally a Grid user token with admin.teams:read to enumerate the organization's workspaces, and a JSON export of your installation store",
"lead": "The install went perfectly. An org owner at the customer approved the app at the organization level, the OAuth callback fired, your store wrote a row, and the welcome message posted. Three days later somebody in a workspace called <code>#brand-studio</code> runs the global shortcut and gets an error, and so does everybody in the other thirty-eight workspaces, and the one workspace where it works is the one whose id happened to land in the row.</p><p>Nothing is broken in Slack. The grant genuinely covers all forty. What broke is the lookup: your store was asked for a workspace and it has a row for an organization, and those are not the same kind of thing.",
"short_answer": """<p>An org-wide install is <strong>one installation that covers every workspace in the organization, present and future</strong>. Slack says so in the shape of the OAuth response: for an enterprise install <code>oauth.v2.access</code> returns <code>&quot;team&quot;: null</code>, an <code>enterprise</code> object with its own id, and <code>&quot;is_enterprise_install&quot;: true</code>. There is no workspace to file it under, because it is not scoped to one.</p>
<p>The failure is therefore a <strong>lookup</strong> failure rather than a storage failure. An event or a shortcut arrives carrying a <code>team_id</code> for whichever workspace the person was in. Your code asks the store for that workspace, the store has an organization row and no workspace row, and the answer is nothing at all. Bolt models this by passing three fields &mdash; <code>enterpriseId</code>, <code>teamId</code>, <code>isEnterpriseInstall</code> &mdash; and expecting <code>fetchInstallation</code> to fall back from the workspace row to the org-wide one. Code that keys on <code>team_id</code> has nothing to fall back to.</p>
<p>Two traps sit either side of it. A store that cannot hold a null writes a placeholder instead, and the SDK issue is exactly that: a <code>team_id</code> persisted as the literal string <code>&quot;none&quot;</code>, after which every read looks for a key that was never written. And the whole thing is untestable in the workspace you developed in, because <code>team_id</code> on a method like <code>conversations.list</code> is documented as <em>ignored</em> when the call is sent with a workspace-level token.</p>""",
"problem": """<p>The first difficulty is arithmetic that nobody does. One row, forty workspaces. Every other install your app has ever handled was one row, one workspace, and the ratio was so reliably one that it never became a variable. On Grid it becomes a variable, and it becomes one silently: the OAuth callback looks the same, the token looks the same, the first message posts. The denominator only shows up when somebody in the thirty-ninth workspace tries to use the app.</p>
<p>The second is that a null is a real value here and most stores dislike it. <code>&quot;team&quot;: null</code> is the documented, correct response for an enterprise install, and it is exactly the value that a schema with a non-null primary key, a composite string key, or a helpfully-coercing ORM will quietly turn into something else. The reported version of this is a <code>team_id</code> of <code>&quot;none&quot;</code>: the row was written under one key and read back under another, and the object store answered with a missing-key error that reads like an infrastructure fault rather than a modelling one.</p>
<p>The third is that the payloads are not uniform. Slack attaches an <code>authorizations</code> array to event payloads, carrying <code>is_enterprise_install</code> so the receiver can tell what kind of installation the event belongs to &mdash; and the documentation states plainly that <strong>the array is truncated at a single installation</strong>. Meanwhile interactive payloads and shortcuts have their own shape, and the Bolt issue behind this note is a global shortcut fired from a Grid workspace where the app was never separately installed, where <code>fetchInstallation</code> was not called at all.</p>
<p>And the fourth is that none of it reproduces on your own workspace. Your development workspace is not in an organization, so <code>is_enterprise_install</code> is <code>false</code>, <code>enterprise_id</code> is absent, and the <code>team_id</code> parameter that the org-wide path depends on is documented as ignored on a workspace-level token. Every test passes. The code path that fails in production is a path your tests cannot enter.</p>""",
"why": """<p><strong>The unit under test is a row, not a token.</strong> The question this check answers is not &ldquo;what can this credential see&rdquo; &mdash; that is the reach of the token and it has its own note. It is &ldquo;for how many of this organization's workspaces does my lookup return something&rdquo;. Those two questions can have opposite answers: an org-wide token that reaches all forty workspaces is useless if thirty-nine of them resolve to no row.</p>
<p><strong>Coverage is measured against an enumerated denominator, because a guessed one is worthless.</strong> <code>admin.teams.list</code> returns the organization's workspaces and needs <code>admin.teams:read</code> on a Grid <strong>user</strong> token. Without that token the script takes the workspace ids you pass it, harvested from event payloads, and says so &mdash; a coverage figure over three workspaces out of forty is reported as three, not extrapolated.</p>
<p><strong>The fallback is simulated rather than assumed.</strong> <code>resolve_install</code> is the store lookup written out as a pure function, run once per workspace with the fallback on and once with it off. The difference between those two runs is the entire finding: with the fallback, one row serves forty; without it, one row serves one and the other thirty-nine are misses that your logs record as a user error.</p>
<p><strong>A stored null and a stored placeholder are different findings.</strong> <code>null</code> is the correct value and the script says so. <code>&quot;none&quot;</code>, <code>&quot;null&quot;</code>, an empty string or a workspace id filed against an org-wide grant are each named separately, because the repair differs: one is a schema change, one is a serialisation bug, and one is a row that was written from the wrong field.</p>
<p><strong>Absence is not <code>false</code>.</strong> <code>is_enterprise_install</code> is documented on the <code>oauth.v2.access</code> response, and the <code>auth.test</code> reference does not show it in its example. So a body that does not carry the field is reported as <code>unstated</code> and the answer is taken from what you persisted at install time. Inferring <code>false</code> from a missing key is how an org-wide install gets classified as an ordinary one by a script written to catch exactly that.</p>
<p><strong>A row that matches on <code>team_id</code> across organizations is refused, not used.</strong> If the only candidate row holds the right workspace id under a different <code>enterprise_id</code>, the lookup returns nothing rather than a token. That is the cross-tenant case, it has its own note, and this script's job is to make sure the simulation never resolves it into a hit.</p>""",
"steps": [
 {"h": "Read the install shape, and allow it to be unstated",
  "body": """<p><code>install_scope</code> takes the <code>auth.test</code> body and the row you persisted at install time. It answers <code>org-wide</code>, <code>workspace-in-org</code>, <code>not-on-grid</code> or <code>unstated</code>. <code>unstated</code> is a real answer: <code>is_enterprise_install</code> is documented on the OAuth response, so a body without it is missing information rather than reporting <code>false</code>.</p>"""},
 {"h": "Check what the org-wide row actually holds in its team_id column",
  "body": """<p><code>stored_team_id</code> separates <code>null-as-stored</code>, which is correct, from <code>placeholder</code>, <code>empty-string</code> and <code>workspace-id-on-an-org-install</code>. The placeholder case is the reported one: a <code>team_id</code> of <code>&quot;none&quot;</code> means the key you write and the key you read are different strings.</p>"""},
 {"h": "Enumerate the organization so the denominator is real",
  "body": """<p><code>admin.teams.list</code>, paginated with <code>cursor</code>, needs <code>admin.teams:read</code> on a Grid user token. If you do not have one, pass <code>--teams</code> with the workspace ids you have seen in event payloads. The script reports which of the two it used, because a coverage number is meaningless without knowing what it is over.</p>"""},
 {"h": "Run your lookup as a pure function, twice",
  "body": """<p><code>resolve_install</code> takes the three-field query and your rows and answers <code>exact</code>, <code>org-wide-fallback</code>, <code>miss-no-fallback</code>, <code>cross-org-refused</code> or <code>miss</code>. Run it with <code>--fallback</code> and without. The gap between the two coverage figures is the size of the bug.</p>"""},
 {"h": "Derive the key from a real payload rather than from the part you remember",
  "body": """<p><code>event_key</code> reads <code>authorizations[0]</code> when it is present and falls back to the top-level <code>enterprise_id</code> and <code>team_id</code>. It flags a payload with no <code>team_id</code> at all rather than substituting one, and it notes that the <code>authorizations</code> array is documented as truncated to a single entry.</p>"""},
 {"h": "Re-key on the triple and implement the fallback",
  "body": """<p><code>repair_plan</code> prints the change: store <code>(enterprise_id, team_id, is_enterprise_install)</code> with <code>team_id</code> genuinely null for an org-wide install, and make the lookup prefer an exact workspace row and fall back to the organization's row. Refusing to fall back across a different <code>enterprise_id</code> is part of the same change.</p>"""},
],
"verify": """<p>After the fallback ships, re-run with the same workspace list. The two coverage lines should agree, and every workspace should resolve.</p>
<pre><code class="language-bash">python3 slack_org_install_coverage.py --store installs.json \\
  --admin-token-env SLACK_ADMIN_USER_TOKEN --event shortcut.json
# scope      org-wide           is_enterprise_install is true for E04NORTHWIND, so this
#                               one grant covers every workspace in the organization
# rows       1                  read from installs.json
# team_id    placeholder        row 1 stores team_id as "none"; the key written at
#                               install time and the key read at lookup are different
#                               strings
# teams      39                 enumerated with admin.teams.list
# coverage   uncovered          0 of 39 workspace(s) resolve without the fallback
# coverage   fallback-only      39 of 39 workspace(s) resolve with it
# event      from-authorizations  E04NORTHWIND / T04BRAND / org-wide=true
#                               authorizations is documented as truncated to one entry
# verdict    3 finding(s)
#   repair: store team_id as a real null for an org-wide install; "none" is a string
#           and it is not the key anything reads
#   repair: key the store on (enterprise_id, team_id, is_enterprise_install) and make
#           the lookup fall back from the workspace row to the organization row
#   repair: never fall back across a different enterprise_id; that path hands one
#           tenant another tenant's token</code></pre>""",
"code_intro": "Five pure functions and two GETs. The two GETs are <code>auth.test</code>, for the shape of the install, and <code>admin.teams.list</code>, for the denominator. Everything else is your own data: <code>resolve_install</code> is your store lookup written out so it can be run forty times without a database, and running it twice &mdash; once with the fallback and once without &mdash; is what turns &ldquo;a user reported an error&rdquo; into &ldquo;thirty-nine of thirty-nine workspaces resolve to nothing&rdquo;.",
"py_file": "slack_org_install_coverage.py",
"py": '''"""Measure how many of a Grid organization's workspaces your store can serve.

Read only. Two GET methods: auth.test for the shape of the installation, and
admin.teams.list to enumerate the organization's workspaces. Your installation
rows are read from a JSON export; nothing is written to your store and nothing
is installed, joined or posted.

The lookup itself is a pure function here rather than a call into your
database, so it can be run once per workspace with the org-wide fallback on and
once with it off. The gap between those two coverage figures is the finding.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_org_install_coverage")

API = "https://slack.com/api/"

# Values a store writes when it cannot hold a null. The documented OAuth
# response for an enterprise install carries "team": null, and a column that
# refuses nulls turns that into one of these.
PLACEHOLDERS = ("none", "null", "undefined", "nil", "nan", "-")


def install_scope(auth, row=None):
    """What kind of installation is this? Pure.

    `auth` is an auth.test body, `row` is whatever you persisted from the
    oauth.v2.access response. Returns (state, detail).

      org-wide          one grant covering every workspace in the organization.
      workspace-in-org  a workspace install that happens to sit inside an org.
      not-on-grid       no enterprise_id anywhere; an ordinary workspace.
      unstated          an enterprise_id, and nothing says which kind it is.
      unreadable        auth.test did not answer.

    is_enterprise_install is documented on the oauth.v2.access response. The
    auth.test reference does not show it, so its absence is reported as
    unstated rather than read as false.
    """
    doc = auth or {}
    stored = row or {}
    if doc.get("ok") is not True:
        return ("unreadable", "auth.test answered ok: false, error=%s"
                % (doc.get("error") or "none"))
    enterprise = doc.get("enterprise_id") or stored.get("enterprise_id") or ""
    flag = doc.get("is_enterprise_install")
    if flag is None:
        flag = stored.get("is_enterprise_install")
    if not enterprise:
        return ("not-on-grid", "no enterprise_id in the response or the stored row, "
                               "so this is an ordinary workspace install")
    if flag is True:
        return ("org-wide", "is_enterprise_install is true for %s, so this one grant "
                            "covers every workspace in the organization" % enterprise)
    if flag is False:
        return ("workspace-in-org", "is_enterprise_install is false and enterprise_id "
                                    "is %s, so this grant covers one workspace of an "
                                    "organization that has many" % enterprise)
    return ("unstated", "enterprise_id is %s and nothing in the response or the "
                        "stored row states is_enterprise_install; it is documented "
                        "on the oauth.v2.access response, so persist it there rather "
                        "than assuming false" % enterprise)


def stored_team_id(row):
    """What did the store actually put in the team_id column? Pure.

    Returns (state, detail).

      null-as-stored     a real null on an org-wide row. Correct.
      placeholder        "none" and friends: written under one key, read under
                         another.
      empty-string       the same fault with a different coercion.
      workspace-id-on-an-org-install  a T id filed against a grant that covers
                         the whole organization.
      workspace-id       a T id on a workspace row. Correct.
      absent             the column was never populated.
      unrecognised       something else entirely.
    """
    doc = row or {}
    org = doc.get("is_enterprise_install") is True
    if "team_id" not in doc:
        return ("absent", "the row has no team_id at all, so a three-field lookup "
                          "cannot be satisfied by it")
    value = doc.get("team_id")
    if value is None:
        if org:
            return ("null-as-stored", "a real null on an org-wide row, which is the "
                                      "documented shape of an enterprise install")
        return ("absent", "a workspace row with a null team_id cannot be looked up "
                          "by workspace")
    text = str(value).strip()
    if not text:
        return ("empty-string", "an empty string is not a null; the key written at "
                                "install time is not the key read at lookup")
    if text.lower() in PLACEHOLDERS:
        return ("placeholder", "row stores team_id as %r; the key written at install "
                               "time and the key read at lookup are different strings"
                % text)
    if org and text.upper().startswith("T"):
        return ("workspace-id-on-an-org-install",
                "team_id %s is filed against a grant that covers the whole "
                "organization, so a lookup for any other workspace misses" % text)
    if text.upper().startswith("T"):
        return ("workspace-id", "team_id %s on a workspace install, which is the "
                                "ordinary case" % text)
    return ("unrecognised", "team_id %r is neither a workspace id nor a null" % text)


def resolve_install(query, rows, org_fallback=False):
    """Your store lookup, written out so it can be run without a database. Pure.

    `query` is Bolt's three-field InstallationQuery: enterprise_id, team_id and
    is_enterprise_install. Returns (state, detail).

      exact              a row matches all three fields.
      org-wide-fallback  no workspace row, and the organization's row covers it.
      miss-no-fallback   the organization's row covers it and the lookup will
                         not use it. This is the bug.
      cross-org-refused  the only candidate holds this team_id under a different
                         organization, and using it would be a cross-tenant leak.
      miss               nothing covers it.
      no-rows            the store is empty.
    """
    q = query or {}
    want_ent = str(q.get("enterprise_id") or "")
    want_team = str(q.get("team_id") or "")
    want_org = q.get("is_enterprise_install") is True
    stored = list(rows or [])
    if not stored:
        return ("no-rows", "the store holds nothing, so nothing resolves")

    for row in stored:
        same_org = str(row.get("enterprise_id") or "") == want_ent
        same_team = str(row.get("team_id") or "") == want_team
        same_kind = (row.get("is_enterprise_install") is True) == want_org
        if same_org and same_team and same_kind:
            return ("exact", "a row matches enterprise_id, team_id and "
                             "is_enterprise_install together")

    org_rows = [r for r in stored
                if r.get("is_enterprise_install") is True
                and want_ent and str(r.get("enterprise_id") or "") == want_ent]
    if org_rows and not want_org:
        if org_fallback:
            return ("org-wide-fallback", "no workspace row for %s, and the org-wide "
                                         "row for %s covers it"
                    % (want_team or "this workspace", want_ent))
        return ("miss-no-fallback", "the org-wide row for %s covers this workspace "
                                    "and a lookup keyed on team_id %s will not reach "
                                    "it" % (want_ent, want_team or "<absent>"))

    if want_team:
        elsewhere = [r for r in stored
                     if str(r.get("team_id") or "") == want_team
                     and str(r.get("enterprise_id") or "") != want_ent]
        if elsewhere:
            return ("cross-org-refused", "a row holds team_id %s under a different "
                                         "organization; resolving it would hand one "
                                         "tenant another tenant's token" % want_team)
    return ("miss", "no row covers %s in %s"
            % (want_team or "<absent>", want_ent or "<no organization>"))


def coverage(states):
    """Turn per-workspace resolutions into one sentence. Pure.

    `states` is the list of states resolve_install returned. Returns
    (state, counts).

      covered        at least one exact match and nothing missing.
      fallback-only  everything resolves, and only because of the fallback.
      partial        some resolve and some do not.
      uncovered      nothing resolves.
      no-workspaces  nothing was asked.
    """
    seen = [str(s) for s in (states or [])]
    counts = {"workspaces": len(seen), "exact": 0, "fallback": 0, "miss": 0,
              "refused": 0}
    for state in seen:
        if state == "exact":
            counts["exact"] += 1
        elif state == "org-wide-fallback":
            counts["fallback"] += 1
        elif state == "cross-org-refused":
            counts["refused"] += 1
        else:
            counts["miss"] += 1
    if not seen:
        return ("no-workspaces", counts)
    resolved = counts["exact"] + counts["fallback"]
    if not resolved:
        return ("uncovered", counts)
    if counts["miss"] or counts["refused"]:
        return ("partial", counts)
    if not counts["exact"]:
        return ("fallback-only", counts)
    return ("covered", counts)


def event_key(payload):
    """Derive the store key an incoming payload asks for. Pure.

    Returns (state, key, detail), where key is the three-field query. The
    authorizations array is documented as truncated to a single installation,
    so the first entry is authoritative for this event and is not a census of
    who else can see it.
    """
    doc = payload or {}
    auths = doc.get("authorizations") or []
    if auths and isinstance(auths[0], dict):
        first = auths[0]
        key = {"enterprise_id": first.get("enterprise_id") or "",
               "team_id": first.get("team_id") or "",
               "is_enterprise_install": first.get("is_enterprise_install") is True}
        if key["is_enterprise_install"] and not key["team_id"]:
            return ("from-authorizations-org-wide", key,
                    "authorizations[0] names an org-wide installation with no "
                    "workspace, which is the shape your lookup has to accept")
        if not key["team_id"]:
            return ("team-id-absent", key,
                    "authorizations[0] carries no team_id and does not claim to be "
                    "org-wide; do not substitute one")
        return ("from-authorizations", key,
                "authorizations[0] names %s / %s; the array is documented as "
                "truncated to one entry"
                % (key["enterprise_id"] or "<no organization>", key["team_id"]))

    key = {"enterprise_id": doc.get("enterprise_id") or "",
           "team_id": doc.get("team_id") or "",
           "is_enterprise_install": doc.get("is_enterprise_install") is True}
    if not key["team_id"] and not key["enterprise_id"]:
        return ("unusable", key, "no authorizations array and no ids at the top "
                                 "level; this payload cannot key a lookup")
    if not key["team_id"]:
        return ("team-id-absent", key, "an enterprise_id and no team_id, which is "
                                       "reported rather than filled in")
    return ("from-top-level", key, "no authorizations array; read %s / %s from the "
                                   "top level of the payload"
            % (key["enterprise_id"] or "<no organization>", key["team_id"]))


def repair_plan(scope, team_id_states, cover_without, cover_with):
    """The change, printed as lines somebody can act on. Pure."""
    out = []
    if any(s in ("placeholder", "empty-string") for s in team_id_states):
        out.append("store team_id as a real null for an org-wide install; a "
                   "placeholder string is not the key anything reads")
    if "workspace-id-on-an-org-install" in team_id_states:
        out.append("an org-wide grant filed under one workspace id serves that "
                   "workspace and no other; re-write the row with a null team_id")
    if cover_without in ("uncovered", "partial") and cover_with in ("covered",
                                                                   "fallback-only"):
        out.append("key the store on (enterprise_id, team_id, is_enterprise_install) "
                   "and make the lookup fall back from the workspace row to the "
                   "organization row")
    if scope == "unstated":
        out.append("persist is_enterprise_install from the oauth.v2.access response; "
                   "it is not something to infer from a missing field")
    if out:
        out.append("never fall back across a different enterprise_id; that path hands "
                   "one tenant another tenant's token")
    return out


def get(session, method, params=None, token=None):
    """One GET against the Web API. Returns the parsed body."""
    headers = {"Authorization": "Bearer " + token} if token else {}
    r = session.get(API + method, params=params or {}, headers=headers, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def list_workspaces(session, admin_token):
    """admin.teams.list, paginated. Needs admin.teams:read on a user token."""
    ids, cursor = [], ""
    while True:
        params = {"limit": 200}
        if cursor:
            params["cursor"] = cursor
        body = get(session, "admin.teams.list", params, admin_token)
        if body.get("ok") is not True:
            return ids, str(body.get("error") or "unknown")
        for team in body.get("teams") or []:
            if team.get("id"):
                ids.append(team["id"])
        cursor = ((body.get("response_metadata") or {}).get("next_cursor") or "")
        if not cursor:
            return ids, ""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the installation's token")
    ap.add_argument("--admin-token-env", default="",
                    help="environment variable holding a Grid user token with "
                         "admin.teams:read, to enumerate the organization")
    ap.add_argument("--store", help="JSON array of installation rows as your store "
                                    "holds them")
    ap.add_argument("--teams", default="",
                    help="comma separated workspace ids, if you cannot enumerate them")
    ap.add_argument("--event", help="a JSON event or interactive payload, to check "
                                    "the key your handler would derive from it")
    ap.add_argument("--fallback", action="store_true",
                    help="your lookup already falls back to the org-wide row")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("token      missing            set %s to the installation's token",
                  args.token_env)
        return 2
    session = requests.Session()

    rows = []
    if args.store:
        with open(args.store, encoding="utf-8") as fh:
            rows = json.load(fh)
    auth = get(session, "auth.test", token=token)
    scope, detail = install_scope(auth, rows[0] if rows else {})
    (log.info if scope in ("org-wide", "not-on-grid") else log.warning)(
        "scope      %-18s %s", scope, detail)
    if scope == "unreadable":
        return 2
    enterprise = auth.get("enterprise_id") or ""

    if not rows:
        rows = [{"enterprise_id": enterprise, "team_id": auth.get("team_id"),
                 "is_enterprise_install": scope == "org-wide"}]
        log.info("rows       %-18s synthesised from auth.test; pass --store for the "
                 "real ones", "1")
    else:
        log.info("rows       %-18s read from %s", str(len(rows)), args.store)

    team_id_states = []
    for i, row in enumerate(rows, start=1):
        state, why = stored_team_id(row)
        team_id_states.append(state)
        (log.info if state in ("null-as-stored", "workspace-id") else log.warning)(
            "team_id    %-18s row %d: %s", state, i, why)

    teams = [t.strip() for t in args.teams.split(",") if t.strip()]
    source = "the --teams list"
    if args.admin_token_env:
        admin = os.environ.get(args.admin_token_env)
        if not admin:
            log.warning("teams      %-18s %s is unset", "no-admin-token",
                        args.admin_token_env)
        else:
            found, err = list_workspaces(session, admin)
            if err:
                log.warning("teams      %-18s admin.teams.list answered %s",
                            "not-enumerated", err)
            else:
                teams, source = found, "admin.teams.list"
    log.info("teams      %-18s enumerated from %s", str(len(teams)), source)

    without, with_fallback = [], []
    for team in teams:
        query = {"enterprise_id": enterprise, "team_id": team,
                 "is_enterprise_install": False}
        without.append(resolve_install(query, rows, org_fallback=False)[0])
        with_fallback.append(resolve_install(query, rows, org_fallback=True)[0])
    cover_without, counts_without = coverage(without)
    cover_with, counts_with = coverage(with_fallback)
    (log.info if cover_without == "covered" else log.warning)(
        "coverage   %-18s %d of %d workspace(s) resolve without the fallback",
        cover_without, counts_without["exact"] + counts_without["fallback"],
        counts_without["workspaces"])
    log.info("coverage   %-18s %d of %d workspace(s) resolve with it", cover_with,
             counts_with["exact"] + counts_with["fallback"],
             counts_with["workspaces"])

    if args.event:
        with open(args.event, encoding="utf-8") as fh:
            state, key, why = event_key(json.load(fh))
        (log.info if state.startswith("from-") else log.warning)(
            "event      %-18s %s / %s / org-wide=%s: %s", state,
            key["enterprise_id"] or "<none>", key["team_id"] or "<none>",
            key["is_enterprise_install"], why)

    repairs = repair_plan(scope, team_id_states, cover_without, cover_with)
    if not repairs:
        log.info("verdict    clean              every workspace asked about resolves "
                 "to a row")
        return 0
    log.warning("verdict    %d finding(s)", len(repairs))
    for line in repairs:
        log.warning("  repair: %s", line)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-org-install-coverage.mjs",
"js": '''/**
 * Measure how many of a Grid organization's workspaces your store can serve.
 *
 * Read only. Two GET methods: auth.test for the shape of the installation, and
 * admin.teams.list to enumerate the organization's workspaces. Installation
 * rows are read from a JSON export; nothing is written to your store.
 *
 * The lookup is a pure function here rather than a call into your database, so
 * it can be run once per workspace with the org-wide fallback on and once with
 * it off. The gap between those two coverage figures is the finding.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Values a store writes when it cannot hold a null. The documented OAuth
// response for an enterprise install carries "team": null.
export const PLACEHOLDERS = ['none', 'null', 'undefined', 'nil', 'nan', '-'];

/**
 * What kind of installation is this? Pure.
 * Returns [state, detail]; org-wide, workspace-in-org, not-on-grid, unstated,
 * unreadable.
 */
export function installScope(auth, row = {}) {
  const doc = auth ?? {};
  const stored = row ?? {};
  if (doc.ok !== true) {
    return ['unreadable', `auth.test answered ok: false, error=${doc.error ?? 'none'}`];
  }
  const enterprise = doc.enterprise_id || stored.enterprise_id || '';
  let flag = doc.is_enterprise_install;
  if (flag === undefined || flag === null) flag = stored.is_enterprise_install;
  if (!enterprise) {
    return ['not-on-grid', 'no enterprise_id in the response or the stored row, so '
      + 'this is an ordinary workspace install'];
  }
  if (flag === true) {
    return ['org-wide', `is_enterprise_install is true for ${enterprise}, so this one `
      + 'grant covers every workspace in the organization'];
  }
  if (flag === false) {
    return ['workspace-in-org', 'is_enterprise_install is false and enterprise_id is '
      + `${enterprise}, so this grant covers one workspace of an organization that `
      + 'has many'];
  }
  return ['unstated', `enterprise_id is ${enterprise} and nothing states `
    + 'is_enterprise_install; it is documented on the oauth.v2.access response, so '
    + 'persist it there rather than assuming false'];
}

/**
 * What did the store actually put in the team_id column? Pure.
 * Returns [state, detail].
 */
export function storedTeamId(row) {
  const doc = row ?? {};
  const org = doc.is_enterprise_install === true;
  if (!Object.prototype.hasOwnProperty.call(doc, 'team_id')) {
    return ['absent', 'the row has no team_id at all, so a three-field lookup cannot '
      + 'be satisfied by it'];
  }
  const value = doc.team_id;
  if (value === null) {
    if (org) {
      return ['null-as-stored', 'a real null on an org-wide row, which is the '
        + 'documented shape of an enterprise install'];
    }
    return ['absent', 'a workspace row with a null team_id cannot be looked up by '
      + 'workspace'];
  }
  const text = String(value).trim();
  if (!text) {
    return ['empty-string', 'an empty string is not a null; the key written at install '
      + 'time is not the key read at lookup'];
  }
  if (PLACEHOLDERS.includes(text.toLowerCase())) {
    return ['placeholder', `row stores team_id as "${text}"; the key written at `
      + 'install time and the key read at lookup are different strings'];
  }
  if (org && text.toUpperCase().startsWith('T')) {
    return ['workspace-id-on-an-org-install', `team_id ${text} is filed against a `
      + 'grant that covers the whole organization, so a lookup for any other '
      + 'workspace misses'];
  }
  if (text.toUpperCase().startsWith('T')) {
    return ['workspace-id', `team_id ${text} on a workspace install, which is the `
      + 'ordinary case'];
  }
  return ['unrecognised', `team_id "${text}" is neither a workspace id nor a null`];
}

/**
 * Your store lookup, written out so it can be run without a database. Pure.
 * Returns [state, detail]; exact, org-wide-fallback, miss-no-fallback,
 * cross-org-refused, miss, no-rows.
 */
export function resolveInstall(query, rows, orgFallback = false) {
  const q = query ?? {};
  const wantEnt = String(q.enterprise_id ?? '');
  const wantTeam = String(q.team_id ?? '');
  const wantOrg = q.is_enterprise_install === true;
  const stored = rows ?? [];
  if (!stored.length) return ['no-rows', 'the store holds nothing, so nothing resolves'];

  for (const row of stored) {
    const sameOrg = String(row.enterprise_id ?? '') === wantEnt;
    const sameTeam = String(row.team_id ?? '') === wantTeam;
    const sameKind = (row.is_enterprise_install === true) === wantOrg;
    if (sameOrg && sameTeam && sameKind) {
      return ['exact', 'a row matches enterprise_id, team_id and '
        + 'is_enterprise_install together'];
    }
  }

  const orgRows = stored.filter((r) => r.is_enterprise_install === true
    && wantEnt && String(r.enterprise_id ?? '') === wantEnt);
  if (orgRows.length && !wantOrg) {
    if (orgFallback) {
      return ['org-wide-fallback', `no workspace row for ${wantTeam || 'this workspace'}`
        + `, and the org-wide row for ${wantEnt} covers it`];
    }
    return ['miss-no-fallback', `the org-wide row for ${wantEnt} covers this workspace `
      + `and a lookup keyed on team_id ${wantTeam || '<absent>'} will not reach it`];
  }

  if (wantTeam) {
    const elsewhere = stored.filter((r) => String(r.team_id ?? '') === wantTeam
      && String(r.enterprise_id ?? '') !== wantEnt);
    if (elsewhere.length) {
      return ['cross-org-refused', `a row holds team_id ${wantTeam} under a different `
        + "organization; resolving it would hand one tenant another tenant's token"];
    }
  }
  return ['miss', `no row covers ${wantTeam || '<absent>'} in `
    + `${wantEnt || '<no organization>'}`];
}

/**
 * Turn per-workspace resolutions into one sentence. Pure.
 * Returns [state, counts].
 */
export function coverage(states) {
  const seen = (states ?? []).map(String);
  const counts = {
    workspaces: seen.length, exact: 0, fallback: 0, miss: 0, refused: 0,
  };
  for (const state of seen) {
    if (state === 'exact') counts.exact += 1;
    else if (state === 'org-wide-fallback') counts.fallback += 1;
    else if (state === 'cross-org-refused') counts.refused += 1;
    else counts.miss += 1;
  }
  if (!seen.length) return ['no-workspaces', counts];
  const resolved = counts.exact + counts.fallback;
  if (!resolved) return ['uncovered', counts];
  if (counts.miss || counts.refused) return ['partial', counts];
  if (!counts.exact) return ['fallback-only', counts];
  return ['covered', counts];
}

/**
 * Derive the store key an incoming payload asks for. Pure.
 * Returns [state, key, detail].
 */
export function eventKey(payload) {
  const doc = payload ?? {};
  const auths = doc.authorizations ?? [];
  if (auths.length && typeof auths[0] === 'object' && auths[0] !== null) {
    const first = auths[0];
    const key = {
      enterprise_id: first.enterprise_id || '',
      team_id: first.team_id || '',
      is_enterprise_install: first.is_enterprise_install === true,
    };
    if (key.is_enterprise_install && !key.team_id) {
      return ['from-authorizations-org-wide', key,
        'authorizations[0] names an org-wide installation with no workspace, which '
        + 'is the shape your lookup has to accept'];
    }
    if (!key.team_id) {
      return ['team-id-absent', key,
        'authorizations[0] carries no team_id and does not claim to be org-wide; do '
        + 'not substitute one'];
    }
    return ['from-authorizations', key,
      `authorizations[0] names ${key.enterprise_id || '<no organization>'} / `
      + `${key.team_id}; the array is documented as truncated to one entry`];
  }

  const key = {
    enterprise_id: doc.enterprise_id || '',
    team_id: doc.team_id || '',
    is_enterprise_install: doc.is_enterprise_install === true,
  };
  if (!key.team_id && !key.enterprise_id) {
    return ['unusable', key, 'no authorizations array and no ids at the top level; '
      + 'this payload cannot key a lookup'];
  }
  if (!key.team_id) {
    return ['team-id-absent', key, 'an enterprise_id and no team_id, which is '
      + 'reported rather than filled in'];
  }
  return ['from-top-level', key, 'no authorizations array; read '
    + `${key.enterprise_id || '<no organization>'} / ${key.team_id} from the top `
    + 'level of the payload'];
}

/** The change, printed as lines somebody can act on. Pure. */
export function repairPlan(scope, teamIdStates, coverWithout, coverWith) {
  const states = teamIdStates ?? [];
  const out = [];
  if (states.some((s) => s === 'placeholder' || s === 'empty-string')) {
    out.push('store team_id as a real null for an org-wide install; a placeholder '
      + 'string is not the key anything reads');
  }
  if (states.includes('workspace-id-on-an-org-install')) {
    out.push('an org-wide grant filed under one workspace id serves that workspace '
      + 'and no other; re-write the row with a null team_id');
  }
  if ((coverWithout === 'uncovered' || coverWithout === 'partial')
    && (coverWith === 'covered' || coverWith === 'fallback-only')) {
    out.push('key the store on (enterprise_id, team_id, is_enterprise_install) and '
      + 'make the lookup fall back from the workspace row to the organization row');
  }
  if (scope === 'unstated') {
    out.push('persist is_enterprise_install from the oauth.v2.access response; it is '
      + 'not something to infer from a missing field');
  }
  if (out.length) {
    out.push('never fall back across a different enterprise_id; that path hands one '
      + "tenant another tenant's token");
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

async function listWorkspaces(adminToken) {
  const ids = [];
  let cursor = '';
  for (;;) {
    const params = cursor ? { limit: 200, cursor } : { limit: 200 };
    // eslint-disable-next-line no-await-in-loop
    const body = await read(adminToken, 'admin.teams.list', params);
    if (body.ok !== true) return [ids, String(body.error ?? 'unknown')];
    for (const team of body.teams ?? []) if (team.id) ids.push(team.id);
    cursor = body.response_metadata?.next_cursor ?? '';
    if (!cursor) return [ids, ''];
  }
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`token      missing            set ${tokenEnv} to the `
      + "installation's token");
    process.exitCode = 2;
    return;
  }

  const storePath = arg(args, '--store');
  let rows = [];
  if (storePath) rows = JSON.parse(await readFile(storePath, 'utf8'));

  const auth = await read(token, 'auth.test', {});
  const [scope, detail] = installScope(auth, rows[0] ?? {});
  const scopeLine = `scope      ${scope.padEnd(18)} ${detail}`;
  if (scope === 'org-wide' || scope === 'not-on-grid') console.log(scopeLine);
  else console.warn(scopeLine);
  if (scope === 'unreadable') {
    process.exitCode = 2;
    return;
  }
  const enterprise = auth.enterprise_id ?? '';

  if (!rows.length) {
    rows = [{
      enterprise_id: enterprise,
      team_id: auth.team_id ?? null,
      is_enterprise_install: scope === 'org-wide',
    }];
    console.log('rows       1                  synthesised from auth.test; pass '
      + '--store for the real ones');
  } else {
    console.log(`rows       ${String(rows.length).padEnd(18)} read from ${storePath}`);
  }

  const teamIdStates = [];
  rows.forEach((row, i) => {
    const [state, why] = storedTeamId(row);
    teamIdStates.push(state);
    const line = `team_id    ${state.padEnd(18)} row ${i + 1}: ${why}`;
    if (state === 'null-as-stored' || state === 'workspace-id') console.log(line);
    else console.warn(line);
  });

  let teams = arg(args, '--teams').split(',').map((t) => t.trim()).filter(Boolean);
  let source = 'the --teams list';
  const adminEnv = arg(args, '--admin-token-env');
  if (adminEnv) {
    const admin = process.env[adminEnv];
    if (!admin) {
      console.warn(`teams      no-admin-token     ${adminEnv} is unset`);
    } else {
      const [found, err] = await listWorkspaces(admin);
      if (err) console.warn(`teams      not-enumerated     admin.teams.list ${err}`);
      else {
        teams = found;
        source = 'admin.teams.list';
      }
    }
  }
  console.log(`teams      ${String(teams.length).padEnd(18)} enumerated from ${source}`);

  const without = [];
  const withFallback = [];
  for (const team of teams) {
    const query = {
      enterprise_id: enterprise, team_id: team, is_enterprise_install: false,
    };
    without.push(resolveInstall(query, rows, false)[0]);
    withFallback.push(resolveInstall(query, rows, true)[0]);
  }
  const [coverWithout, countsWithout] = coverage(without);
  const [coverWith, countsWith] = coverage(withFallback);
  const line = `coverage   ${coverWithout.padEnd(18)} `
    + `${countsWithout.exact + countsWithout.fallback} of ${countsWithout.workspaces} `
    + 'workspace(s) resolve without the fallback';
  if (coverWithout === 'covered') console.log(line);
  else console.warn(line);
  console.log(`coverage   ${coverWith.padEnd(18)} `
    + `${countsWith.exact + countsWith.fallback} of ${countsWith.workspaces} `
    + 'workspace(s) resolve with it');

  const eventPath = arg(args, '--event');
  if (eventPath) {
    const [state, key, why] = eventKey(JSON.parse(await readFile(eventPath, 'utf8')));
    const evLine = `event      ${state.padEnd(18)} ${key.enterprise_id || '<none>'} / `
      + `${key.team_id || '<none>'} / org-wide=${key.is_enterprise_install}: ${why}`;
    if (state.startsWith('from-')) console.log(evLine);
    else console.warn(evLine);
  }

  const repairs = repairPlan(scope, teamIdStates, coverWithout, coverWith);
  if (!repairs.length) {
    console.log('verdict    clean              every workspace asked about resolves '
      + 'to a row');
    return;
  }
  console.warn(`verdict    ${repairs.length} finding(s)`);
  for (const repair of repairs) console.warn(`  repair: ${repair}`);
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are installation rows and an event payload, and the row worth reading twice is the one whose <code>team_id</code> is the string <code>&quot;none&quot;</code>, because that is the reported bug rather than an invented one. The assertions that carry the note are the pair around <code>resolve_install</code>: the same query against the same rows must answer <code>miss-no-fallback</code> without the fallback and <code>org-wide-fallback</code> with it, and it must answer <code>cross-org-refused</code> when the only candidate belongs to a different organization.",
"test_py_file": "test_slack_org_install_coverage.py",
"test_py": '''from slack_org_install_coverage import (
    coverage, event_key, install_scope, repair_plan, resolve_install, stored_team_id,
)

ORG = "E04NORTHWIND"
OTHER_ORG = "E09SOUTHWIND"
HOME = "T04MKTG"
SIBLING = "T04BRAND"

ORG_ROW = {"enterprise_id": ORG, "team_id": None, "is_enterprise_install": True}


def test_an_org_wide_install_is_named_from_the_flag():
    state, detail = install_scope({"ok": True, "enterprise_id": ORG,
                                   "is_enterprise_install": True})
    assert state == "org-wide"
    assert "every workspace" in detail


def test_a_workspace_install_inside_an_org_is_a_different_shape():
    state, _ = install_scope({"ok": True, "enterprise_id": ORG, "team_id": HOME,
                              "is_enterprise_install": False})
    assert state == "workspace-in-org"


def test_an_absent_flag_is_unstated_rather_than_false():
    state, detail = install_scope({"ok": True, "enterprise_id": ORG, "team_id": HOME})
    assert state == "unstated"
    assert "oauth.v2.access" in detail


def test_the_stored_row_supplies_the_flag_when_the_response_does_not():
    state, _ = install_scope({"ok": True, "enterprise_id": ORG},
                             {"is_enterprise_install": True})
    assert state == "org-wide"


def test_no_enterprise_id_anywhere_is_not_a_grid_problem():
    assert install_scope({"ok": True, "team_id": HOME})[0] == "not-on-grid"


def test_a_failed_auth_test_is_unreadable():
    assert install_scope({"ok": False, "error": "invalid_auth"})[0] == "unreadable"


def test_a_real_null_on_an_org_row_is_correct():
    state, detail = stored_team_id(ORG_ROW)
    assert state == "null-as-stored"
    assert "documented shape" in detail


def test_the_reported_placeholder_is_named_exactly():
    state, detail = stored_team_id({"enterprise_id": ORG, "team_id": "none",
                                    "is_enterprise_install": True})
    assert state == "placeholder"
    assert "different strings" in detail


def test_an_empty_string_is_not_a_null():
    assert stored_team_id({"team_id": "   ", "is_enterprise_install": True})[0] == \\
        "empty-string"


def test_an_org_grant_filed_under_one_workspace_is_its_own_finding():
    state, detail = stored_team_id({"enterprise_id": ORG, "team_id": HOME,
                                    "is_enterprise_install": True})
    assert state == "workspace-id-on-an-org-install"
    assert "misses" in detail


def test_a_workspace_row_with_a_workspace_id_is_the_ordinary_case():
    assert stored_team_id({"team_id": HOME})[0] == "workspace-id"


def test_a_row_without_the_column_at_all_is_absent():
    assert stored_team_id({"enterprise_id": ORG})[0] == "absent"


def test_the_org_row_matches_an_org_query_exactly():
    query = {"enterprise_id": ORG, "team_id": "", "is_enterprise_install": True}
    assert resolve_install(query, [ORG_ROW])[0] == "exact"


def test_a_sibling_workspace_misses_without_the_fallback():
    query = {"enterprise_id": ORG, "team_id": SIBLING,
             "is_enterprise_install": False}
    state, detail = resolve_install(query, [ORG_ROW], org_fallback=False)
    assert state == "miss-no-fallback"
    assert SIBLING in detail


def test_the_same_query_resolves_once_the_fallback_is_on():
    query = {"enterprise_id": ORG, "team_id": SIBLING,
             "is_enterprise_install": False}
    assert resolve_install(query, [ORG_ROW], org_fallback=True)[0] == \\
        "org-wide-fallback"


def test_a_workspace_row_still_wins_over_the_org_row():
    rows = [ORG_ROW, {"enterprise_id": ORG, "team_id": SIBLING,
                      "is_enterprise_install": False}]
    query = {"enterprise_id": ORG, "team_id": SIBLING,
             "is_enterprise_install": False}
    assert resolve_install(query, rows, org_fallback=True)[0] == "exact"


def test_a_matching_team_id_in_another_org_is_refused_not_used():
    rows = [{"enterprise_id": OTHER_ORG, "team_id": SIBLING,
             "is_enterprise_install": False}]
    query = {"enterprise_id": ORG, "team_id": SIBLING,
             "is_enterprise_install": False}
    state, detail = resolve_install(query, rows, org_fallback=True)
    assert state == "cross-org-refused"
    assert "another tenant" in detail


def test_an_empty_store_says_so_rather_than_missing():
    assert resolve_install({"team_id": HOME}, [])[0] == "no-rows"


def test_coverage_without_the_fallback_is_the_finding():
    state, counts = coverage(["miss-no-fallback"] * 39)
    assert state == "uncovered"
    assert counts["miss"] == 39


def test_coverage_with_the_fallback_is_complete_but_named_as_such():
    state, counts = coverage(["org-wide-fallback"] * 39)
    assert state == "fallback-only"
    assert counts["fallback"] == 39


def test_a_mixed_result_is_partial():
    assert coverage(["exact", "miss"])[0] == "partial"


def test_a_refusal_counts_against_coverage():
    _state, counts = coverage(["exact", "cross-org-refused"])
    assert counts["refused"] == 1


def test_probing_no_workspaces_says_so():
    assert coverage([])[0] == "no-workspaces"


def test_the_authorizations_array_is_preferred_and_its_truncation_is_noted():
    state, key, detail = event_key({
        "team_id": "T00WRONG",
        "authorizations": [{"enterprise_id": ORG, "team_id": SIBLING,
                            "is_enterprise_install": False}],
    })
    assert state == "from-authorizations"
    assert key["team_id"] == SIBLING
    assert "truncated" in detail


def test_an_org_wide_authorization_with_no_workspace_is_accepted():
    state, key, _ = event_key({
        "authorizations": [{"enterprise_id": ORG, "is_enterprise_install": True}]})
    assert state == "from-authorizations-org-wide"
    assert key["is_enterprise_install"] is True


def test_a_payload_without_authorizations_falls_back_to_the_top_level():
    state, key, _ = event_key({"enterprise_id": ORG, "team_id": SIBLING})
    assert state == "from-top-level"
    assert key["enterprise_id"] == ORG


def test_a_missing_team_id_is_reported_and_never_substituted():
    state, key, detail = event_key({"enterprise_id": ORG})
    assert state == "team-id-absent"
    assert key["team_id"] == ""
    assert "filled in" in detail


def test_a_payload_with_no_ids_at_all_cannot_key_a_lookup():
    assert event_key({"type": "shortcut"})[0] == "unusable"


def test_the_repair_names_the_placeholder_and_the_fallback():
    lines = repair_plan("org-wide", ["placeholder"], "uncovered", "fallback-only")
    assert any("real null" in line for line in lines)
    assert any("fall back" in line for line in lines)
    assert any("enterprise_id" in line and "tenant" in line for line in lines)


def test_an_unstated_flag_earns_its_own_repair_line():
    lines = repair_plan("unstated", ["workspace-id"], "covered", "covered")
    assert any("oauth.v2.access" in line for line in lines)


def test_a_healthy_store_needs_no_repair():
    assert repair_plan("org-wide", ["null-as-stored"], "covered", "covered") == []
''',
"test_js_file": "slack-org-install-coverage.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  coverage, eventKey, installScope, repairPlan, resolveInstall, storedTeamId,
} from './slack-org-install-coverage.mjs';

const ORG = 'E04NORTHWIND';
const OTHER_ORG = 'E09SOUTHWIND';
const HOME = 'T04MKTG';
const SIBLING = 'T04BRAND';

const ORG_ROW = { enterprise_id: ORG, team_id: null, is_enterprise_install: true };

test('an org wide install is named from the flag', () => {
  const [state, detail] = installScope({
    ok: true, enterprise_id: ORG, is_enterprise_install: true,
  });
  assert.equal(state, 'org-wide');
  assert.match(detail, /every workspace/);
});

test('a workspace install inside an org is a different shape', () => {
  const [state] = installScope({
    ok: true, enterprise_id: ORG, team_id: HOME, is_enterprise_install: false,
  });
  assert.equal(state, 'workspace-in-org');
});

test('an absent flag is unstated rather than false', () => {
  const [state, detail] = installScope({
    ok: true, enterprise_id: ORG, team_id: HOME,
  });
  assert.equal(state, 'unstated');
  assert.match(detail, /oauth.v2.access/);
});

test('the stored row supplies the flag when the response does not', () => {
  const [state] = installScope({ ok: true, enterprise_id: ORG },
    { is_enterprise_install: true });
  assert.equal(state, 'org-wide');
});

test('no enterprise id anywhere is not a grid problem', () => {
  assert.equal(installScope({ ok: true, team_id: HOME })[0], 'not-on-grid');
});

test('a failed auth test is unreadable', () => {
  assert.equal(installScope({ ok: false, error: 'invalid_auth' })[0], 'unreadable');
});

test('a real null on an org row is correct', () => {
  const [state, detail] = storedTeamId(ORG_ROW);
  assert.equal(state, 'null-as-stored');
  assert.match(detail, /documented shape/);
});

test('the reported placeholder is named exactly', () => {
  const [state, detail] = storedTeamId({
    enterprise_id: ORG, team_id: 'none', is_enterprise_install: true,
  });
  assert.equal(state, 'placeholder');
  assert.match(detail, /different strings/);
});

test('an empty string is not a null', () => {
  assert.equal(storedTeamId({ team_id: '   ', is_enterprise_install: true })[0],
    'empty-string');
});

test('an org grant filed under one workspace is its own finding', () => {
  const [state, detail] = storedTeamId({
    enterprise_id: ORG, team_id: HOME, is_enterprise_install: true,
  });
  assert.equal(state, 'workspace-id-on-an-org-install');
  assert.match(detail, /misses/);
});

test('a workspace row with a workspace id is the ordinary case', () => {
  assert.equal(storedTeamId({ team_id: HOME })[0], 'workspace-id');
});

test('a row without the column at all is absent', () => {
  assert.equal(storedTeamId({ enterprise_id: ORG })[0], 'absent');
});

test('the org row matches an org query exactly', () => {
  const query = { enterprise_id: ORG, team_id: '', is_enterprise_install: true };
  assert.equal(resolveInstall(query, [ORG_ROW])[0], 'exact');
});

test('a sibling workspace misses without the fallback', () => {
  const query = { enterprise_id: ORG, team_id: SIBLING, is_enterprise_install: false };
  const [state, detail] = resolveInstall(query, [ORG_ROW], false);
  assert.equal(state, 'miss-no-fallback');
  assert.match(detail, /T04BRAND/);
});

test('the same query resolves once the fallback is on', () => {
  const query = { enterprise_id: ORG, team_id: SIBLING, is_enterprise_install: false };
  assert.equal(resolveInstall(query, [ORG_ROW], true)[0], 'org-wide-fallback');
});

test('a workspace row still wins over the org row', () => {
  const rows = [ORG_ROW,
    { enterprise_id: ORG, team_id: SIBLING, is_enterprise_install: false }];
  const query = { enterprise_id: ORG, team_id: SIBLING, is_enterprise_install: false };
  assert.equal(resolveInstall(query, rows, true)[0], 'exact');
});

test('a matching team id in another org is refused not used', () => {
  const rows = [{
    enterprise_id: OTHER_ORG, team_id: SIBLING, is_enterprise_install: false,
  }];
  const query = { enterprise_id: ORG, team_id: SIBLING, is_enterprise_install: false };
  const [state, detail] = resolveInstall(query, rows, true);
  assert.equal(state, 'cross-org-refused');
  assert.match(detail, /another tenant/);
});

test('an empty store says so rather than missing', () => {
  assert.equal(resolveInstall({ team_id: HOME }, [])[0], 'no-rows');
});

test('coverage without the fallback is the finding', () => {
  const [state, counts] = coverage(new Array(39).fill('miss-no-fallback'));
  assert.equal(state, 'uncovered');
  assert.equal(counts.miss, 39);
});

test('coverage with the fallback is complete but named as such', () => {
  const [state, counts] = coverage(new Array(39).fill('org-wide-fallback'));
  assert.equal(state, 'fallback-only');
  assert.equal(counts.fallback, 39);
});

test('a mixed result is partial', () => {
  assert.equal(coverage(['exact', 'miss'])[0], 'partial');
});

test('a refusal counts against coverage', () => {
  const [, counts] = coverage(['exact', 'cross-org-refused']);
  assert.equal(counts.refused, 1);
});

test('probing no workspaces says so', () => {
  assert.equal(coverage([])[0], 'no-workspaces');
});

test('the authorizations array is preferred and its truncation is noted', () => {
  const [state, key, detail] = eventKey({
    team_id: 'T00WRONG',
    authorizations: [{
      enterprise_id: ORG, team_id: SIBLING, is_enterprise_install: false,
    }],
  });
  assert.equal(state, 'from-authorizations');
  assert.equal(key.team_id, SIBLING);
  assert.match(detail, /truncated/);
});

test('an org wide authorization with no workspace is accepted', () => {
  const [state, key] = eventKey({
    authorizations: [{ enterprise_id: ORG, is_enterprise_install: true }],
  });
  assert.equal(state, 'from-authorizations-org-wide');
  assert.equal(key.is_enterprise_install, true);
});

test('a payload without authorizations falls back to the top level', () => {
  const [state, key] = eventKey({ enterprise_id: ORG, team_id: SIBLING });
  assert.equal(state, 'from-top-level');
  assert.equal(key.enterprise_id, ORG);
});

test('a missing team id is reported and never substituted', () => {
  const [state, key, detail] = eventKey({ enterprise_id: ORG });
  assert.equal(state, 'team-id-absent');
  assert.equal(key.team_id, '');
  assert.match(detail, /filled in/);
});

test('a payload with no ids at all cannot key a lookup', () => {
  assert.equal(eventKey({ type: 'shortcut' })[0], 'unusable');
});

test('the repair names the placeholder and the fallback', () => {
  const lines = repairPlan('org-wide', ['placeholder'], 'uncovered', 'fallback-only');
  assert.equal(lines.some((l) => l.includes('real null')), true);
  assert.equal(lines.some((l) => l.includes('fall back')), true);
  assert.equal(lines.some((l) => l.includes('enterprise_id') && l.includes('tenant')),
    true);
});

test('an unstated flag earns its own repair line', () => {
  const lines = repairPlan('unstated', ['workspace-id'], 'covered', 'covered');
  assert.equal(lines.some((l) => l.includes('oauth.v2.access')), true);
});

test('a healthy store needs no repair', () => {
  assert.deepEqual(repairPlan('org-wide', ['null-as-stored'], 'covered', 'covered'),
    []);
});
''',
"faq": [
 ("Is this the same problem as our token not reaching a sibling workspace?",
  "No, and the two can be true independently, which is why they are separate notes. Token reach is about what one credential is permitted to see, and it announces itself with team_access_not_granted. This is about what your store returns when something asks it for a workspace. An org-wide token that reaches all forty workspaces still produces a broken app if thirty-nine of those workspaces resolve to no installation row, because the failure happens before any call is made. If you are seeing an explicit refusal from Slack, that is the reach note. If you are seeing nothing at all, no token and no call, that is this one."),
 ("Why is team_id null for an org-wide install, and why can we not just store the id of the workspace it was installed from?",
  "Because it was not installed from a workspace. An org-wide install is approved at the organization level and covers every workspace in it, including workspaces created next year. The documented oauth.v2.access response for an enterprise install carries a null team field and an enterprise object instead. Filing that grant under one workspace id is not a compromise, it is a wrong answer: it makes the row look like a workspace install, so a lookup for any of the other thirty-nine matches nothing, and a lookup for that one matches a row whose scope it misrepresents."),
 ("Our stored team_id is the literal string none. Where does that come from?",
  "From a store that cannot represent a null, plus a serialisation step that turns the absent value into text. This is a reported SDK issue rather than a theoretical one: the installation is written under one key and then read back under a key containing that placeholder, and the object store answers with a missing-key error that looks like infrastructure. The script names it separately from a real null for exactly that reason. The repair is to allow the column to be null and to write it as one."),
 ("Can we test the org-wide path in our development workspace?",
  "Not usefully, and this is worth knowing before you plan the work. A development workspace has no enterprise_id, so is_enterprise_install is false and the org-wide branch of your code never runs. Worse, the team_id parameter that org-wide calls depend on is documented as ignored when a call is made with a workspace-level token, so a test that passes it and gets sensible data back has proved nothing. That is why the lookup is a pure function here: it is the one part you can exercise honestly without an organization to test against."),
 ("A global shortcut fired from a workspace where our app is not separately installed does nothing. Is that this?",
  "Very probably. It is the shape behind the Bolt issue cited below: the shortcut arrives from a workspace with no installation of its own, the framework asks the store for that workspace, and the org-wide row that covers it is never considered. Run the check with --event and the payload the shortcut delivered; the derived key will show you what your handler asked for, and the coverage lines will show you whether the fallback would have answered it."),
],
"related": [
 ("/slack/enterprise-id-not-stored/", "the same triple, from the collision side"),
 ("/slack/workspace-token-in-grid/", "how far one token reaches, which is a different question"),
 ("/slack/manifest-drift/", "where org_deploy_enabled lives, and what else the manifest states"),
],
"citations": [CITE_GRID_DEV, CITE_OAUTH_V2, CITE_SDK_1639, CITE_BOLT_1944],
})

GUIDES.append({
"slug": "enterprise-is-restricted",
"title": "enterprise_is_restricted: the method is barred on Grid",
"description": "The refusal is attached to the method, not to your token or your user. Inventory the calls your app makes, probe the reads, map each to its org equivalent.",
"h1": "enterprise_is_restricted: the method is barred on Grid",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack enterprise_is_restricted error",
             "the method cannot be called from an enterprise",
             "slack admin.conversations.search instead of conversations.list",
             "slack org level token method not allowed",
             "slack grid api method equivalents"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the token your app uses on the Enterprise customer, and the list of Web API methods your code calls",
"lead": "One customer, out of two hundred, is on Enterprise Grid. Their evaluation started on Monday and by Wednesday the integration engineer has a list of four methods that answer <code>{\"ok\": false, \"error\": \"enterprise_is_restricted\"}</code> &mdash; <em>the method cannot be called from an Enterprise</em>.</p><p>Nothing is wrong with the token. Nothing is wrong with the scopes. The person calling is an org owner. The refusal is attached to the method: some of the Web API is simply not callable in this context, the organization-level equivalents live somewhere else under different scopes and a different token class, and you are finding this out during a customer's evaluation because there was no earlier moment when you could have.",
"short_answer": """<p><code>enterprise_is_restricted</code> is documented, in the errors table of every method that carries it, as <strong>&ldquo;The method cannot be called from an Enterprise.&rdquo;</strong> It appears on ordinary workspace methods including <code>chat.postMessage</code>, <code>conversations.list</code>, <code>conversations.history</code> and <code>users.info</code>. It is not about scopes, not about admin roles, and not about which workspace you pointed at.</p>
<p>It is one of <strong>four different refusals that all appear on Grid and all need different repairs</strong>, and telling them apart is most of the work. <code>enterprise_is_restricted</code> means this method, here, no. <code>team_access_not_granted</code> means the token is bounded to a workspace and you reached outside it. <code>org_login_required</code> and <code>team_added_to_org</code> mean the workspace is migrating and will answer later. <code>not_allowed_token_type</code> means the wrong class of credential. A retry helps exactly one of those four.</p>
<p>The repair, where one exists, is an <strong>organization-level equivalent</strong>: <code>admin.conversations.search</code> in place of a cross-org <code>conversations.list</code>, <code>admin.users.list</code> in place of <code>users.list</code>, <code>admin.teams.list</code> in place of enumerating workspaces by hand. Those need <code>admin.*:read</code> scopes on an <strong>admin user token</strong>, which is a different credential from your bot token. Where no equivalent exists, the answer is to keep using the workspace-scoped path, per workspace, and accept the fan-out.</p>""",
"problem": """<p>The first thing that makes this hard is that there is no published list. The set of methods that can answer <code>enterprise_is_restricted</code> is discoverable only by reading each method's own errors table, one page at a time, and the wording never varies enough to tell you <em>why</em> a particular method is on the list. So you cannot audit your call surface from the documentation in an afternoon; you can only look up the methods you already know you call, and hope the list you have is the list your code has.</p>
<p>The second is that the natural way to find out is to call everything, and half of your call surface writes. Probing <code>conversations.list</code> costs nothing. Probing <code>chat.postMessage</code> posts a message into a customer's workspace during their evaluation, probing <code>conversations.create</code> leaves a channel behind with whatever name the probe invented, and probing <code>conversations.invite</code> adds somebody to something. An audit that answers the question by trying is an audit that changes the thing it is auditing.</p>
<p>The third is the diagnosis, and it is where most of the lost time goes. Four different Grid refusals arrive through the same field of the same JSON body, and three of the four look like a permissions problem to anyone who has not met them before. Teams add scopes for a refusal that is not about scopes. They add retries for a refusal that is a decision. They re-install for a refusal that will clear on its own in six hours. Only <code>org_login_required</code> and <code>team_added_to_org</code> reward waiting, and only <code>team_access_not_granted</code> rewards a different install.</p>
<p>And the fourth is that the fix crosses a credential boundary. Every organization-level equivalent lives under <code>admin.*</code>, and those scopes exist only as <strong>user</strong> token scopes held by an org owner or admin. Swapping a call is a one-line change; obtaining the credential to make it with is an installation flow, an approval, and a conversation with somebody at the customer who has never heard of your app.</p>""",
"why": """<p><strong>The unit is a method name, not an error.</strong> This check takes the list of methods your code calls &mdash; from a grep of your source, not from memory &mdash; and produces one row per method. The output is a table you can hand to whoever is doing the Grid work, and every row already carries its own repair.</p>
<p><strong>Writes are named and never issued.</strong> Every method in the map is marked as a read or a write. Reads are probed. Writes are reported from the map with their expected classification and are not called, because there is no way to ask a write method whether it is barred except by writing, and this is somebody else's production organization.</p>
<p><strong>The four Grid refusals are separated by a single function, because that separation is the finding.</strong> <code>refusal_kind</code> maps a response body to <code>barred-on-enterprise</code>, <code>wrong-workspace</code>, <code>migration</code>, <code>token-class</code>, <code>scope</code> or <code>callable</code>, and each of those prints a different next action. Collapsing them into &ldquo;Grid problem&rdquo; is what produces a week of adding scopes to a call that will never accept any.</p>
<p><strong>The equivalence map is deliberately small and honest.</strong> It contains the substitutions that are actually equivalent and marks everything else <code>no-equivalent</code>, which means &ldquo;iterate per workspace with a workspace-scoped token&rdquo;. Inventing a plausible-looking <code>admin.*</code> replacement for a method that has none would be worse than saying nothing, because somebody would go and build it.</p>
<p><strong>A method the map has never heard of is reported as unknown.</strong> Since Slack does not publish the restricted set, a script that classifies an unfamiliar method by guessing is asserting something it cannot know. <code>unknown-method</code> prints the reference page to read instead, which is a smaller answer and a true one.</p>
<p><strong>A probe that comes back <code>callable</code> is evidence about this token in this organization, and nothing more.</strong> The same method may be barred for a different token class, and the script says so rather than issuing a clean bill of health for the whole customer base.</p>""",
"steps": [
 {"h": "Get the method list out of your source, not out of your head",
  "body": """<p>Grep for <code>slack.com/api/</code> or for your SDK's call sites and pass the result to <code>--methods</code>. The point of the exercise is completeness: the method that breaks the Grid deployment is nearly always one nobody remembered was in there.</p>"""},
 {"h": "Decide, per method, whether the audit is allowed to call it",
  "body": """<p><code>may_probe</code> answers <code>read</code>, <code>needs-argument</code>, <code>write-report-only</code> or <code>unknown</code>. A write is reported from the map and never issued. A read that requires a channel or user id is skipped until you pass <code>--channel</code> or <code>--user</code>, because a probe that fails on a missing argument tells you nothing about Enterprise.</p>"""},
 {"h": "Classify the refusal rather than the failure",
  "body": """<p><code>refusal_kind</code> separates the four Grid refusals that arrive in the same field. Only <code>barred-on-enterprise</code> is this note. <code>migration</code> clears by itself, <code>wrong-workspace</code> is a token-reach problem, and <code>token-class</code> and <code>scope</code> are credential problems with their own repairs.</p>"""},
 {"h": "Look up the organization-level equivalent, or the absence of one",
  "body": """<p><code>org_equivalent</code> answers <code>has-equivalent</code> with the replacement method, its <code>admin.*:read</code> scope and the fact that it needs a user token; <code>no-equivalent</code>, which means per-workspace iteration; <code>already-admin</code>; or <code>unknown-method</code>.</p>"""},
 {"h": "Read the surface, not the individual rows",
  "body": """<p><code>surface_summary</code> answers <code>clean</code>, <code>partially-barred</code>, <code>barred</code> or <code>not-assessed</code>. Three barred methods out of forty is a substitution job. Forty out of forty means the token class itself is wrong and you should read the row that says <code>token-class</code> first.</p>"""},
 {"h": "Get the admin user token before you change any calls",
  "body": """<p><code>repair_plan</code> prints the credential work first because it is the long pole: an <code>admin.*:read</code> scope is a user token scope, the install has to be performed by an org owner or admin, and the resulting token is stored separately from the bot token and used only for <code>admin.*</code> calls.</p>"""},
],
"verify": """<p>Once the substitutions ship and the admin token is stored, re-run with the same method list against the same organization. Every row should read <code>callable</code> or <code>write-report-only</code>.</p>
<pre><code class="language-bash">python3 slack_enterprise_method_audit.py \\
  --methods conversations.list,users.list,conversations.history,chat.postMessage
# context    enterprise         enterprise_id E04NORTHWIND, so a refusal here may be
#                               about the Enterprise rather than about your token
# method     conversations.list barred-on-enterprise  the method cannot be called
#                               from an Enterprise
#            -> admin.conversations.search  needs admin.conversations:read on an
#               admin user token
# method     users.list         barred-on-enterprise  the method cannot be called
#                               from an Enterprise
#            -> admin.users.list  needs admin.users:read on an admin user token
# method     conversations.history  needs-argument   pass --channel to probe it
# method     chat.postMessage   write-report-only    named, mapped, never called;
#                               no org-level equivalent, so keep a workspace-scoped
#                               token for it
# surface    partially-barred   2 barred, 1 callable, 1 not probed, of 4
# verdict    3 finding(s)
#   repair: request admin.conversations:read and admin.users:read as USER token
#           scopes and have an org owner or admin perform the installation
#   repair: store the resulting user token separately and use it only for admin.*
#   repair: for methods with no org-level equivalent, iterate per workspace with a
#           workspace-scoped token</code></pre>""",
"code_intro": "Four pure functions and one probe loop. <code>refusal_kind</code> is the one that earns the note: four different Grid refusals arrive in the same <code>error</code> field and only one of them is this problem, so the script never reports &ldquo;Grid failure&rdquo;. <code>may_probe</code> is the read-only guard, and it is a map rather than a heuristic, because guessing that a method is safe to call in somebody else's organization is not a guess worth making.",
"py_file": "slack_enterprise_method_audit.py",
"py": '''"""Find which of your Slack methods are barred in an Enterprise organization.

Read only. Every probe is a GET, and only methods the map marks as reads are
issued at all. Writes are named, mapped to their organization-level equivalent
where one exists, and never called: there is no way to ask a write method
whether it is barred except by performing it, and this runs against a
customer's production organization.

enterprise_is_restricted is documented as "The method cannot be called from an
Enterprise." Slack does not publish the set of methods that can return it, so
this script reports what it observed plus what the map knows, and says unknown
for anything else.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_enterprise_method_audit")

API = "https://slack.com/api/"

# Reads that answer with no arguments at all, so a probe is meaningful.
ARGUMENT_FREE_READS = ("auth.test", "conversations.list", "users.list", "team.info",
                       "emoji.list", "usergroups.list", "users.conversations",
                       "files.list", "team.profile.get", "team.billableInfo",
                       "chat.scheduledMessages.list", "admin.teams.list",
                       "admin.users.list", "admin.conversations.search")

# Reads that need a channel, user or message to mean anything. Probed only when
# the argument is supplied, because a missing-argument error says nothing about
# Enterprise.
ARGUMENT_READS = ("conversations.info", "conversations.history",
                  "conversations.members", "conversations.replies", "users.info",
                  "bots.info", "reactions.get", "pins.list", "files.info")

# Writes. Named, mapped, never issued.
WRITE_METHODS = ("chat.postMessage", "chat.postEphemeral", "chat.update",
                 "chat.delete", "chat.scheduleMessage", "conversations.create",
                 "conversations.invite", "conversations.join", "conversations.archive",
                 "conversations.rename", "views.publish", "views.open",
                 "usergroups.create", "usergroups.update", "usergroups.disable",
                 "usergroups.enable", "files.upload", "files.completeUploadExternal",
                 "reactions.add", "pins.add")

# The substitutions that are genuinely equivalent. Everything absent from this
# map is reported as having no equivalent, which means "iterate per workspace",
# because inventing a plausible admin.* replacement is worse than saying nothing.
ORG_EQUIVALENTS = {
    "conversations.list": ("admin.conversations.search", "admin.conversations:read"),
    "users.list": ("admin.users.list", "admin.users:read"),
    "team.info": ("admin.teams.list", "admin.teams:read"),
}

MIGRATION_ERRORS = ("org_login_required", "team_added_to_org")
TRANSIENT_ERRORS = ("ratelimited", "service_unavailable", "internal_error",
                    "fatal_error", "request_timeout", "unparseable_body")


def may_probe(method):
    """Is this audit allowed to call this method? Pure.

    Returns (state, detail).

      read                the method is argument-free and safe to issue.
      needs-argument      a read that needs a channel, user or message id.
      write-report-only   a write. Named and mapped; never called.
      unknown             not in any list; reported rather than guessed at.
    """
    name = str(method or "").strip()
    if name in WRITE_METHODS:
        return ("write-report-only", "this method writes, so it is named and mapped "
                                     "and never issued by an audit")
    if name in ARGUMENT_FREE_READS:
        return ("read", "an argument-free read, so a probe is meaningful on its own")
    if name in ARGUMENT_READS:
        return ("needs-argument", "a read that needs a channel, user or message id; "
                                  "pass one or this method is skipped")
    return ("unknown", "not in the map this script carries; check the method's own "
                       "reference page for enterprise_is_restricted in its errors "
                       "table")


def refusal_kind(body):
    """Which of the Grid refusals is this? Pure.

    Four different refusals arrive in the same error field and only one of them
    is this note. Returns (state, detail).

      callable             ok: true.
      barred-on-enterprise enterprise_is_restricted. This note.
      wrong-workspace      team_access_not_granted: the token has a boundary.
      migration            org_login_required or team_added_to_org: wait.
      token-class          not_allowed_token_type: the wrong kind of credential.
      scope                missing_scope: a grant, not a context.
      admin-role           not_an_admin: the right token, the wrong person.
      plan                 feature_not_enabled: not an Enterprise at all.
      argument             the probe was malformed or under-specified.
      transient            retry later; nothing was learned.
      other                handed on rather than absorbed.
    """
    doc = body or {}
    if doc.get("ok") is True:
        return ("callable", "the method answered ok: true for this token in this "
                            "organization")
    error = str(doc.get("error") or "")
    if error == "enterprise_is_restricted":
        return ("barred-on-enterprise", "enterprise_is_restricted: the method cannot "
                                        "be called from an Enterprise")
    if error == "team_access_not_granted":
        return ("wrong-workspace", "team_access_not_granted: the token is bounded to "
                                   "one workspace, which is a reach problem rather "
                                   "than a method problem")
    if error in MIGRATION_ERRORS:
        return ("migration", "%s: the workspace is migrating into an organization and "
                             "will answer once it settles" % error)
    if error == "not_allowed_token_type":
        return ("token-class", "not_allowed_token_type: the credential is the wrong "
                               "class for this method, most often a bot token where a "
                               "user token is required")
    if error == "missing_scope":
        return ("scope", "missing_scope: a grant is absent, which is a different "
                         "repair from a method being barred")
    if error == "not_an_admin":
        return ("admin-role", "not_an_admin: the token class is right and the person "
                              "behind it lacks the role")
    if error == "feature_not_enabled":
        return ("plan", "feature_not_enabled: the admin surface is an Enterprise "
                        "feature and this customer is not on it")
    if error in ("invalid_arguments", "invalid_arg_name", "channel_not_found",
                 "user_not_found", "not_in_channel"):
        return ("argument", "%s: the probe was under-specified, so nothing was "
                            "learned about Enterprise" % error)
    if error in TRANSIENT_ERRORS:
        return ("transient", "%s: try again later; this probe established nothing"
                % error)
    if not error:
        return ("other", "no ok field and no error, so nothing can be read from this "
                         "response")
    return ("other", "%s, which is a different problem" % error)


def org_equivalent(method):
    """Is there an organization-level replacement for this method? Pure.

    Returns (state, detail).

      has-equivalent  the replacement, its scope, and the token class it needs.
      already-admin   the method is already an admin.* method.
      no-equivalent   none exists; iterate per workspace with a workspace token.
      unknown-method  not in this script's map at all.
    """
    name = str(method or "").strip()
    if name.startswith("admin."):
        return ("already-admin", "this is an organization-level method; it needs an "
                                 "admin.*:read scope on an admin user token")
    if name in ORG_EQUIVALENTS:
        replacement, scope = ORG_EQUIVALENTS[name]
        return ("has-equivalent", "%s, which needs %s on an admin user token held by "
                                  "an org owner or admin" % (replacement, scope))
    known = (name in ARGUMENT_FREE_READS or name in ARGUMENT_READS
             or name in WRITE_METHODS)
    if known:
        return ("no-equivalent", "no organization-level equivalent; keep a "
                                 "workspace-scoped token and iterate per workspace")
    return ("unknown-method", "not in this script's map; read the method's own "
                              "reference page rather than assuming a replacement")


def surface_summary(rows):
    """One sentence about the whole call surface. Pure.

    rows: [(method, kind), ...] where kind came from refusal_kind or may_probe.
    Returns (state, counts).
    """
    seen = [(str(m), str(k)) for m, k in (rows or [])]
    counts = {"methods": len(seen), "barred": 0, "callable": 0, "not_probed": 0,
              "other": 0}
    for _method, kind in seen:
        if kind == "barred-on-enterprise":
            counts["barred"] += 1
        elif kind == "callable":
            counts["callable"] += 1
        elif kind in ("write-report-only", "needs-argument", "unknown", "transient"):
            counts["not_probed"] += 1
        else:
            counts["other"] += 1
    if not seen:
        return ("nothing-probed", counts)
    if not counts["barred"] and not counts["callable"]:
        return ("not-assessed", counts)
    if not counts["barred"]:
        return ("clean", counts)
    if not counts["callable"]:
        return ("barred", counts)
    return ("partially-barred", counts)


def repair_plan(rows):
    """The credential work first, because it is the long pole. Pure.

    rows: [(method, kind, equivalent_state, equivalent_detail), ...].
    """
    scopes, per_workspace, other = [], [], []
    for method, kind, eq_state, eq_detail in (rows or []):
        if kind not in ("barred-on-enterprise", "token-class"):
            continue
        if eq_state == "has-equivalent":
            scopes.append("%s -> %s" % (method, eq_detail))
        elif eq_state in ("no-equivalent", "already-admin"):
            per_workspace.append(method)
        else:
            other.append(method)
    out = []
    if scopes:
        out.append("request the admin.*:read scopes below as USER token scopes and "
                   "have an org owner or admin perform the installation")
        out.extend("  " + line for line in scopes)
        out.append("store the resulting user token separately from the bot token and "
                   "use it only for admin.* calls")
    if per_workspace:
        out.append("no organization-level equivalent for %s; iterate per workspace "
                   "with a workspace-scoped token" % ", ".join(per_workspace))
    if other:
        out.append("read the reference page for %s; this script will not guess a "
                   "replacement" % ", ".join(other))
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
                    help="environment variable holding the token your app uses")
    ap.add_argument("--methods", default="",
                    help="comma separated Web API methods your code calls")
    ap.add_argument("--channel", default="",
                    help="a channel id, so channel-scoped reads can be probed")
    ap.add_argument("--user", default="",
                    help="a user id, so user-scoped reads can be probed")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("token      missing            set %s to the token your app uses",
                  args.token_env)
        return 2
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    auth = get(session, "auth.test")
    if auth.get("ok") is not True:
        log.error("context    unreadable         auth.test answered %s",
                  auth.get("error") or "nothing")
        return 2
    enterprise = auth.get("enterprise_id") or ""
    if enterprise:
        log.info("context    enterprise         enterprise_id %s, so a refusal here "
                 "may be about the Enterprise rather than about your token",
                 enterprise)
    else:
        log.info("context    standalone         no enterprise_id, so "
                 "enterprise_is_restricted cannot arise for this installation")

    rows, repair_rows = [], []
    for method in [m.strip() for m in args.methods.split(",") if m.strip()]:
        safety, why = may_probe(method)
        if safety == "read":
            kind, detail = refusal_kind(get(session, method, {"limit": 1}))
        elif safety == "needs-argument" and (args.channel or args.user):
            params = {"limit": 1}
            if args.channel:
                params["channel"] = args.channel
            if args.user:
                params["user"] = args.user
            kind, detail = refusal_kind(get(session, method, params))
        else:
            kind, detail = safety, why
        eq_state, eq_detail = org_equivalent(method)
        rows.append((method, kind))
        repair_rows.append((method, kind, eq_state, eq_detail))
        (log.info if kind in ("callable", "write-report-only") else log.warning)(
            "method     %-22s %-22s %s", method, kind, detail)
        if kind in ("barred-on-enterprise", "token-class"):
            log.warning("           -> %-19s %s", eq_state, eq_detail)

    summary, counts = surface_summary(rows)
    (log.info if summary in ("clean", "nothing-probed") else log.warning)(
        "surface    %-18s %d barred, %d callable, %d not probed, of %d",
        summary, counts["barred"], counts["callable"], counts["not_probed"],
        counts["methods"])

    repairs = repair_plan(repair_rows)
    if not repairs:
        log.info("verdict    clean              no method in the list is barred for "
                 "this token in this organization")
        return 0
    log.warning("verdict    %d finding(s)", len(repairs))
    for line in repairs:
        log.warning("  repair: %s", line)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-enterprise-method-audit.mjs",
"js": '''/**
 * Find which of your Slack methods are barred in an Enterprise organization.
 *
 * Read only. Every probe is a GET, and only methods the map marks as reads are
 * issued at all. Writes are named, mapped to their organization-level
 * equivalent where one exists, and never called.
 *
 * enterprise_is_restricted is documented as "The method cannot be called from
 * an Enterprise." Slack does not publish the set of methods that can return it,
 * so this script reports what it observed plus what the map knows.
 */

const API = 'https://slack.com/api/';

// Reads that answer with no arguments at all.
export const ARGUMENT_FREE_READS = ['auth.test', 'conversations.list', 'users.list',
  'team.info', 'emoji.list', 'usergroups.list', 'users.conversations', 'files.list',
  'team.profile.get', 'team.billableInfo', 'chat.scheduledMessages.list',
  'admin.teams.list', 'admin.users.list', 'admin.conversations.search'];

// Reads that need a channel, user or message to mean anything.
export const ARGUMENT_READS = ['conversations.info', 'conversations.history',
  'conversations.members', 'conversations.replies', 'users.info', 'bots.info',
  'reactions.get', 'pins.list', 'files.info'];

// Writes. Named, mapped, never issued.
export const WRITE_METHODS = ['chat.postMessage', 'chat.postEphemeral', 'chat.update',
  'chat.delete', 'chat.scheduleMessage', 'conversations.create',
  'conversations.invite', 'conversations.join', 'conversations.archive',
  'conversations.rename', 'views.publish', 'views.open', 'usergroups.create',
  'usergroups.update', 'usergroups.disable', 'usergroups.enable', 'files.upload',
  'files.completeUploadExternal', 'reactions.add', 'pins.add'];

// Only substitutions that are genuinely equivalent.
export const ORG_EQUIVALENTS = {
  'conversations.list': ['admin.conversations.search', 'admin.conversations:read'],
  'users.list': ['admin.users.list', 'admin.users:read'],
  'team.info': ['admin.teams.list', 'admin.teams:read'],
};

export const MIGRATION_ERRORS = ['org_login_required', 'team_added_to_org'];
export const TRANSIENT_ERRORS = ['ratelimited', 'service_unavailable',
  'internal_error', 'fatal_error', 'request_timeout', 'unparseable_body'];

/**
 * Is this audit allowed to call this method? Pure.
 * Returns [state, detail]; read, needs-argument, write-report-only, unknown.
 */
export function mayProbe(method) {
  const name = String(method ?? '').trim();
  if (WRITE_METHODS.includes(name)) {
    return ['write-report-only', 'this method writes, so it is named and mapped and '
      + 'never issued by an audit'];
  }
  if (ARGUMENT_FREE_READS.includes(name)) {
    return ['read', 'an argument-free read, so a probe is meaningful on its own'];
  }
  if (ARGUMENT_READS.includes(name)) {
    return ['needs-argument', 'a read that needs a channel, user or message id; pass '
      + 'one or this method is skipped'];
  }
  return ['unknown', 'not in the map this script carries; check the method\\'s own '
    + 'reference page for enterprise_is_restricted in its errors table'];
}

/**
 * Which of the Grid refusals is this? Pure.
 * Returns [state, detail].
 */
export function refusalKind(body) {
  const doc = body ?? {};
  if (doc.ok === true) {
    return ['callable', 'the method answered ok: true for this token in this '
      + 'organization'];
  }
  const error = String(doc.error ?? '');
  if (error === 'enterprise_is_restricted') {
    return ['barred-on-enterprise', 'enterprise_is_restricted: the method cannot be '
      + 'called from an Enterprise'];
  }
  if (error === 'team_access_not_granted') {
    return ['wrong-workspace', 'team_access_not_granted: the token is bounded to one '
      + 'workspace, which is a reach problem rather than a method problem'];
  }
  if (MIGRATION_ERRORS.includes(error)) {
    return ['migration', `${error}: the workspace is migrating into an organization `
      + 'and will answer once it settles'];
  }
  if (error === 'not_allowed_token_type') {
    return ['token-class', 'not_allowed_token_type: the credential is the wrong class '
      + 'for this method, most often a bot token where a user token is required'];
  }
  if (error === 'missing_scope') {
    return ['scope', 'missing_scope: a grant is absent, which is a different repair '
      + 'from a method being barred'];
  }
  if (error === 'not_an_admin') {
    return ['admin-role', 'not_an_admin: the token class is right and the person '
      + 'behind it lacks the role'];
  }
  if (error === 'feature_not_enabled') {
    return ['plan', 'feature_not_enabled: the admin surface is an Enterprise feature '
      + 'and this customer is not on it'];
  }
  if (['invalid_arguments', 'invalid_arg_name', 'channel_not_found', 'user_not_found',
    'not_in_channel'].includes(error)) {
    return ['argument', `${error}: the probe was under-specified, so nothing was `
      + 'learned about Enterprise'];
  }
  if (TRANSIENT_ERRORS.includes(error)) {
    return ['transient', `${error}: try again later; this probe established nothing`];
  }
  if (!error) {
    return ['other', 'no ok field and no error, so nothing can be read from this '
      + 'response'];
  }
  return ['other', `${error}, which is a different problem`];
}

/**
 * Is there an organization-level replacement for this method? Pure.
 * Returns [state, detail]; has-equivalent, already-admin, no-equivalent,
 * unknown-method.
 */
export function orgEquivalent(method) {
  const name = String(method ?? '').trim();
  if (name.startsWith('admin.')) {
    return ['already-admin', 'this is an organization-level method; it needs an '
      + 'admin.*:read scope on an admin user token'];
  }
  if (Object.prototype.hasOwnProperty.call(ORG_EQUIVALENTS, name)) {
    const [replacement, scope] = ORG_EQUIVALENTS[name];
    return ['has-equivalent', `${replacement}, which needs ${scope} on an admin user `
      + 'token held by an org owner or admin'];
  }
  const known = ARGUMENT_FREE_READS.includes(name) || ARGUMENT_READS.includes(name)
    || WRITE_METHODS.includes(name);
  if (known) {
    return ['no-equivalent', 'no organization-level equivalent; keep a '
      + 'workspace-scoped token and iterate per workspace'];
  }
  return ['unknown-method', 'not in this script\\'s map; read the method\\'s own '
    + 'reference page rather than assuming a replacement'];
}

/**
 * One sentence about the whole call surface. Pure.
 * Returns [state, counts].
 */
export function surfaceSummary(rows) {
  const seen = (rows ?? []).map(([m, k]) => [String(m), String(k)]);
  const counts = {
    methods: seen.length, barred: 0, callable: 0, not_probed: 0, other: 0,
  };
  for (const [, kind] of seen) {
    if (kind === 'barred-on-enterprise') counts.barred += 1;
    else if (kind === 'callable') counts.callable += 1;
    else if (['write-report-only', 'needs-argument', 'unknown',
      'transient'].includes(kind)) counts.not_probed += 1;
    else counts.other += 1;
  }
  if (!seen.length) return ['nothing-probed', counts];
  if (!counts.barred && !counts.callable) return ['not-assessed', counts];
  if (!counts.barred) return ['clean', counts];
  if (!counts.callable) return ['barred', counts];
  return ['partially-barred', counts];
}

/** The credential work first, because it is the long pole. Pure. */
export function repairPlan(rows) {
  const scopes = [];
  const perWorkspace = [];
  const other = [];
  for (const [method, kind, eqState, eqDetail] of (rows ?? [])) {
    if (kind !== 'barred-on-enterprise' && kind !== 'token-class') continue;
    if (eqState === 'has-equivalent') scopes.push(`${method} -> ${eqDetail}`);
    else if (eqState === 'no-equivalent' || eqState === 'already-admin') {
      perWorkspace.push(method);
    } else other.push(method);
  }
  const out = [];
  if (scopes.length) {
    out.push('request the admin.*:read scopes below as USER token scopes and have an '
      + 'org owner or admin perform the installation');
    for (const line of scopes) out.push(`  ${line}`);
    out.push('store the resulting user token separately from the bot token and use it '
      + 'only for admin.* calls');
  }
  if (perWorkspace.length) {
    out.push(`no organization-level equivalent for ${perWorkspace.join(', ')}; `
      + 'iterate per workspace with a workspace-scoped token');
  }
  if (other.length) {
    out.push(`read the reference page for ${other.join(', ')}; this script will not `
      + 'guess a replacement');
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
    console.error(`token      missing            set ${tokenEnv} to the token your `
      + 'app uses');
    process.exitCode = 2;
    return;
  }

  const auth = await read(token, 'auth.test', {});
  if (auth.ok !== true) {
    console.error(`context    unreadable         auth.test answered `
      + `${auth.error ?? 'nothing'}`);
    process.exitCode = 2;
    return;
  }
  const enterprise = auth.enterprise_id ?? '';
  if (enterprise) {
    console.log(`context    enterprise         enterprise_id ${enterprise}, so a `
      + 'refusal here may be about the Enterprise rather than about your token');
  } else {
    console.log('context    standalone         no enterprise_id, so '
      + 'enterprise_is_restricted cannot arise for this installation');
  }

  const channel = arg(args, '--channel');
  const user = arg(args, '--user');
  const rows = [];
  const repairRows = [];
  for (const method of arg(args, '--methods').split(',').map((m) => m.trim())
    .filter(Boolean)) {
    const [safety, why] = mayProbe(method);
    let kind = safety;
    let detail = why;
    if (safety === 'read') {
      // eslint-disable-next-line no-await-in-loop
      [kind, detail] = refusalKind(await read(token, method, { limit: 1 }));
    } else if (safety === 'needs-argument' && (channel || user)) {
      const params = { limit: 1 };
      if (channel) params.channel = channel;
      if (user) params.user = user;
      // eslint-disable-next-line no-await-in-loop
      [kind, detail] = refusalKind(await read(token, method, params));
    }
    const [eqState, eqDetail] = orgEquivalent(method);
    rows.push([method, kind]);
    repairRows.push([method, kind, eqState, eqDetail]);
    const line = `method     ${method.padEnd(22)} ${kind.padEnd(22)} ${detail}`;
    if (kind === 'callable' || kind === 'write-report-only') console.log(line);
    else console.warn(line);
    if (kind === 'barred-on-enterprise' || kind === 'token-class') {
      console.warn(`           -> ${eqState.padEnd(19)} ${eqDetail}`);
    }
  }

  const [summary, counts] = surfaceSummary(rows);
  const summaryLine = `surface    ${summary.padEnd(18)} ${counts.barred} barred, `
    + `${counts.callable} callable, ${counts.not_probed} not probed, of `
    + `${counts.methods}`;
  if (summary === 'clean' || summary === 'nothing-probed') console.log(summaryLine);
  else console.warn(summaryLine);

  const repairs = repairPlan(repairRows);
  if (!repairs.length) {
    console.log('verdict    clean              no method in the list is barred for '
      + 'this token in this organization');
    return;
  }
  console.warn(`verdict    ${repairs.length} finding(s)`);
  for (const line of repairs) console.warn(`  repair: ${line}`);
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are response bodies with one field in them, which is all these refusals ever amount to. The assertions worth reading are the block around <code>refusal_kind</code>: five different errors that a reader might file under &ldquo;Grid problem&rdquo; must come back as five different states, because each one has a different repair and three of them are not this note. The other assertion that matters is negative: every write in the map must classify as <code>write-report-only</code>, and no test anywhere calls one.",
"test_py_file": "test_slack_enterprise_method_audit.py",
"test_py": '''from slack_enterprise_method_audit import (
    may_probe, org_equivalent, refusal_kind, repair_plan, surface_summary,
)


def test_an_argument_free_read_may_be_probed():
    state, detail = may_probe("conversations.list")
    assert state == "read"
    assert "meaningful" in detail


def test_a_write_is_named_and_never_issued():
    state, detail = may_probe("chat.postMessage")
    assert state == "write-report-only"
    assert "never issued" in detail


def test_every_write_in_the_map_is_report_only():
    from slack_enterprise_method_audit import WRITE_METHODS
    assert all(may_probe(m)[0] == "write-report-only" for m in WRITE_METHODS)


def test_a_read_needing_a_channel_is_skipped_until_one_is_supplied():
    assert may_probe("conversations.history")[0] == "needs-argument"


def test_a_method_outside_the_map_is_not_guessed_at():
    state, detail = may_probe("some.newMethod")
    assert state == "unknown"
    assert "reference page" in detail


def test_the_barred_error_is_this_note():
    state, detail = refusal_kind({"ok": False, "error": "enterprise_is_restricted"})
    assert state == "barred-on-enterprise"
    assert "cannot be called from an Enterprise" in detail


def test_a_workspace_boundary_is_a_different_note():
    state, detail = refusal_kind({"ok": False, "error": "team_access_not_granted"})
    assert state == "wrong-workspace"
    assert "reach problem" in detail


def test_both_migration_errors_land_in_one_state_that_says_wait():
    for error in ("org_login_required", "team_added_to_org"):
        state, detail = refusal_kind({"ok": False, "error": error})
        assert state == "migration"
        assert "settles" in detail


def test_the_wrong_credential_class_is_not_a_barred_method():
    assert refusal_kind({"ok": False,
                         "error": "not_allowed_token_type"})[0] == "token-class"


def test_a_missing_scope_is_a_grant_not_a_context():
    state, detail = refusal_kind({"ok": False, "error": "missing_scope"})
    assert state == "scope"
    assert "different repair" in detail


def test_the_role_and_the_plan_are_separated_from_each_other():
    assert refusal_kind({"ok": False, "error": "not_an_admin"})[0] == "admin-role"
    assert refusal_kind({"ok": False, "error": "feature_not_enabled"})[0] == "plan"


def test_an_under_specified_probe_learns_nothing_and_says_so():
    state, detail = refusal_kind({"ok": False, "error": "channel_not_found"})
    assert state == "argument"
    assert "nothing was learned" in detail


def test_a_rate_limit_establishes_nothing():
    assert refusal_kind({"ok": False, "error": "ratelimited"})[0] == "transient"


def test_a_successful_call_is_evidence_about_this_token_only():
    state, detail = refusal_kind({"ok": True})
    assert state == "callable"
    assert "this token" in detail


def test_an_empty_body_is_handed_on_rather_than_absorbed():
    assert refusal_kind({})[0] == "other"


def test_the_three_substitutions_carry_their_scope_and_token_class():
    for method, replacement in (("conversations.list", "admin.conversations.search"),
                                ("users.list", "admin.users.list"),
                                ("team.info", "admin.teams.list")):
        state, detail = org_equivalent(method)
        assert state == "has-equivalent"
        assert replacement in detail
        assert "user token" in detail


def test_an_admin_method_is_already_at_the_organization_level():
    assert org_equivalent("admin.conversations.search")[0] == "already-admin"


def test_a_known_method_with_no_replacement_says_iterate_per_workspace():
    state, detail = org_equivalent("chat.postMessage")
    assert state == "no-equivalent"
    assert "per workspace" in detail


def test_an_unknown_method_gets_no_invented_replacement():
    state, detail = org_equivalent("some.newMethod")
    assert state == "unknown-method"
    assert "assuming a replacement" in detail


def test_a_surface_with_no_barred_methods_is_clean():
    state, counts = surface_summary([("conversations.list", "callable"),
                                     ("users.list", "callable")])
    assert state == "clean"
    assert counts["callable"] == 2


def test_a_mixed_surface_is_partially_barred():
    state, counts = surface_summary([("conversations.list", "barred-on-enterprise"),
                                     ("users.list", "callable"),
                                     ("chat.postMessage", "write-report-only")])
    assert state == "partially-barred"
    assert counts["barred"] == 1
    assert counts["not_probed"] == 1


def test_a_wholly_barred_surface_points_at_the_token_class():
    assert surface_summary([("conversations.list", "barred-on-enterprise"),
                            ("users.list", "barred-on-enterprise")])[0] == "barred"


def test_a_surface_of_only_unprobed_methods_concludes_nothing():
    assert surface_summary([("chat.postMessage", "write-report-only")])[0] == \\
        "not-assessed"


def test_probing_nothing_says_so():
    assert surface_summary([])[0] == "nothing-probed"


def test_the_repair_puts_the_credential_work_first():
    lines = repair_plan([("conversations.list", "barred-on-enterprise",
                          "has-equivalent", "admin.conversations.search, which needs "
                                            "admin.conversations:read on an admin "
                                            "user token")])
    assert "USER token scopes" in lines[0]
    assert any("admin.conversations.search" in line for line in lines)
    assert any("separately from the bot token" in line for line in lines)


def test_a_barred_method_with_no_equivalent_gets_the_per_workspace_line():
    lines = repair_plan([("chat.postMessage", "barred-on-enterprise",
                          "no-equivalent", "none")])
    assert any("iterate per workspace" in line for line in lines)


def test_an_unknown_barred_method_is_handed_to_the_reference_page():
    lines = repair_plan([("some.newMethod", "barred-on-enterprise",
                          "unknown-method", "none")])
    assert any("will not guess" in line for line in lines)


def test_a_callable_surface_needs_no_repair():
    assert repair_plan([("conversations.list", "callable", "has-equivalent",
                         "x")]) == []
''',
"test_js_file": "slack-enterprise-method-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  WRITE_METHODS, mayProbe, orgEquivalent, refusalKind, repairPlan, surfaceSummary,
} from './slack-enterprise-method-audit.mjs';

test('an argument free read may be probed', () => {
  const [state, detail] = mayProbe('conversations.list');
  assert.equal(state, 'read');
  assert.match(detail, /meaningful/);
});

test('a write is named and never issued', () => {
  const [state, detail] = mayProbe('chat.postMessage');
  assert.equal(state, 'write-report-only');
  assert.match(detail, /never issued/);
});

test('every write in the map is report only', () => {
  assert.equal(WRITE_METHODS.every((m) => mayProbe(m)[0] === 'write-report-only'),
    true);
});

test('a read needing a channel is skipped until one is supplied', () => {
  assert.equal(mayProbe('conversations.history')[0], 'needs-argument');
});

test('a method outside the map is not guessed at', () => {
  const [state, detail] = mayProbe('some.newMethod');
  assert.equal(state, 'unknown');
  assert.match(detail, /reference page/);
});

test('the barred error is this note', () => {
  const [state, detail] = refusalKind({
    ok: false, error: 'enterprise_is_restricted',
  });
  assert.equal(state, 'barred-on-enterprise');
  assert.match(detail, /cannot be called from an Enterprise/);
});

test('a workspace boundary is a different note', () => {
  const [state, detail] = refusalKind({
    ok: false, error: 'team_access_not_granted',
  });
  assert.equal(state, 'wrong-workspace');
  assert.match(detail, /reach problem/);
});

test('both migration errors land in one state that says wait', () => {
  for (const error of ['org_login_required', 'team_added_to_org']) {
    const [state, detail] = refusalKind({ ok: false, error });
    assert.equal(state, 'migration');
    assert.match(detail, /settles/);
  }
});

test('the wrong credential class is not a barred method', () => {
  assert.equal(refusalKind({ ok: false, error: 'not_allowed_token_type' })[0],
    'token-class');
});

test('a missing scope is a grant not a context', () => {
  const [state, detail] = refusalKind({ ok: false, error: 'missing_scope' });
  assert.equal(state, 'scope');
  assert.match(detail, /different repair/);
});

test('the role and the plan are separated from each other', () => {
  assert.equal(refusalKind({ ok: false, error: 'not_an_admin' })[0], 'admin-role');
  assert.equal(refusalKind({ ok: false, error: 'feature_not_enabled' })[0], 'plan');
});

test('an under specified probe learns nothing and says so', () => {
  const [state, detail] = refusalKind({ ok: false, error: 'channel_not_found' });
  assert.equal(state, 'argument');
  assert.match(detail, /nothing was learned/);
});

test('a rate limit establishes nothing', () => {
  assert.equal(refusalKind({ ok: false, error: 'ratelimited' })[0], 'transient');
});

test('a successful call is evidence about this token only', () => {
  const [state, detail] = refusalKind({ ok: true });
  assert.equal(state, 'callable');
  assert.match(detail, /this token/);
});

test('an empty body is handed on rather than absorbed', () => {
  assert.equal(refusalKind({})[0], 'other');
});

test('the three substitutions carry their scope and token class', () => {
  const pairs = [['conversations.list', 'admin.conversations.search'],
    ['users.list', 'admin.users.list'], ['team.info', 'admin.teams.list']];
  for (const [method, replacement] of pairs) {
    const [state, detail] = orgEquivalent(method);
    assert.equal(state, 'has-equivalent');
    assert.equal(detail.includes(replacement), true);
    assert.match(detail, /user token/);
  }
});

test('an admin method is already at the organization level', () => {
  assert.equal(orgEquivalent('admin.conversations.search')[0], 'already-admin');
});

test('a known method with no replacement says iterate per workspace', () => {
  const [state, detail] = orgEquivalent('chat.postMessage');
  assert.equal(state, 'no-equivalent');
  assert.match(detail, /per workspace/);
});

test('an unknown method gets no invented replacement', () => {
  const [state, detail] = orgEquivalent('some.newMethod');
  assert.equal(state, 'unknown-method');
  assert.match(detail, /assuming a replacement/);
});

test('a surface with no barred methods is clean', () => {
  const [state, counts] = surfaceSummary([['conversations.list', 'callable'],
    ['users.list', 'callable']]);
  assert.equal(state, 'clean');
  assert.equal(counts.callable, 2);
});

test('a mixed surface is partially barred', () => {
  const [state, counts] = surfaceSummary([
    ['conversations.list', 'barred-on-enterprise'],
    ['users.list', 'callable'],
    ['chat.postMessage', 'write-report-only'],
  ]);
  assert.equal(state, 'partially-barred');
  assert.equal(counts.barred, 1);
  assert.equal(counts.not_probed, 1);
});

test('a wholly barred surface points at the token class', () => {
  assert.equal(surfaceSummary([['conversations.list', 'barred-on-enterprise'],
    ['users.list', 'barred-on-enterprise']])[0], 'barred');
});

test('a surface of only unprobed methods concludes nothing', () => {
  assert.equal(surfaceSummary([['chat.postMessage', 'write-report-only']])[0],
    'not-assessed');
});

test('probing nothing says so', () => {
  assert.equal(surfaceSummary([])[0], 'nothing-probed');
});

test('the repair puts the credential work first', () => {
  const lines = repairPlan([['conversations.list', 'barred-on-enterprise',
    'has-equivalent',
    'admin.conversations.search, which needs admin.conversations:read on an admin '
    + 'user token']]);
  assert.match(lines[0], /USER token scopes/);
  assert.equal(lines.some((l) => l.includes('admin.conversations.search')), true);
  assert.equal(lines.some((l) => l.includes('separately from the bot token')), true);
});

test('a barred method with no equivalent gets the per workspace line', () => {
  const lines = repairPlan([['chat.postMessage', 'barred-on-enterprise',
    'no-equivalent', 'none']]);
  assert.equal(lines.some((l) => l.includes('iterate per workspace')), true);
});

test('an unknown barred method is handed to the reference page', () => {
  const lines = repairPlan([['some.newMethod', 'barred-on-enterprise',
    'unknown-method', 'none']]);
  assert.equal(lines.some((l) => l.includes('will not guess')), true);
});

test('a callable surface needs no repair', () => {
  assert.deepEqual(repairPlan([['conversations.list', 'callable', 'has-equivalent',
    'x']]), []);
});
''',
"faq": [
 ("Which methods return enterprise_is_restricted? Is there a list?",
  "Not a published one, and that is the honest answer rather than a gap in this note. The error appears in the errors table of individual method reference pages, so you can confirm it for a method you already suspect but you cannot enumerate the set from the documentation. That is why the script probes the methods you actually call rather than trying to be a catalogue, and why a method it has never heard of is reported as unknown with a pointer to its reference page instead of being classified."),
 ("An admin blocked our app for one user and we get app_access_restricted. Is that the same thing?",
  "No. That refusal is about a person: an administrator has decided this app may be used by some members and not others, and the same call succeeds for everybody else in the same workspace with the same token. enterprise_is_restricted is about the method: it fails for every user, because the method itself is not callable in this context. The quickest way to tell them apart in a log is to group the failures by user id. If they cluster into a cohort, it is the per-user restriction. If they cluster by method name, it is this."),
 ("We are an org owner with every scope. Why does adding more scopes not help?",
  "Because the refusal is not a scope check. A scope says what a token is permitted to do; this error says the method is not available in this context at all, so there is no grant that would satisfy it. Adding scopes to a barred method costs you a re-install and changes nothing. The productive move is the substitution: find whether an organization-level equivalent exists, request that method's admin.*:read scope as a user token scope, and have an org owner install it."),
 ("Why does the script refuse to probe chat.postMessage?",
  "Because probing it posts a message. There is no read-only way to ask a write method whether it works, and the audit is running against a customer's production organization, often during an evaluation. So every write in the map is classified from the map, printed with whatever equivalent exists, and never issued. The cost is that a write is reported as write-report-only rather than as callable or barred; the benefit is that the audit does not leave channels, messages or invitations behind it."),
 ("Our probe came back callable for every method. Are we safe on Grid?",
  "Safe for that token, in that organization, on that day. The script reports exactly that and no more. A different customer may be on a different plan, a different token class may be refused where yours was not, and the write methods in your list were never probed at all. Treat a clean run as the removal of one hypothesis rather than as a clearance, and keep the error handling for enterprise_is_restricted in place regardless, because the first time you meet it will be in production at a customer you have not audited."),
],
"related": [
 ("/slack/app-access-restricted/", "the refusal that is about a person rather than a method"),
 ("/slack/not-allowed-token-type/", "the credential-class refusal it is most often confused with"),
 ("/slack/accesslimited-ip-allowlist/", "a third organization-level refusal, this one about the network"),
],
"citations": [CITE_CONVERSATIONS_HISTORY, CITE_CHAT_POST, CITE_ADMIN_USERS_LIST, CITE_GRID],
})

GUIDES.append({
"slug": "org-login-required",
"title": "org_login_required: hold the installation, do not retire it",
"description": "The workspace is migrating and will not answer until it finishes. Turn the error into a disposition, suspend the installation, and keep the cleanup away.",
"h1": "org_login_required: hold the installation, do not retire it",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack org_login_required error",
             "slack enterprise migration api unavailable",
             "slack installation suspended during migration",
             "slack retry backoff migration error",
             "slack workspace undergoing enterprise migration"],
"deps": "Python 3.9+ with requests, or Node.js 18+; the tokens for the installations you want to classify, and optionally a JSON log of the errors you have already recorded per installation",
"lead": "At 06:40 a customer stops working. Every scheduled job for them fails, every webhook delivery fails, and the body is the same each time: <code>{\"ok\": false, \"error\": \"org_login_required\"}</code> &mdash; <em>the workspace is undergoing an enterprise migration and will not be available until migration is complete</em>.</p><p>What happens next is usually one of two mistakes. The retry logic treats it like a rate limit and hammers a workspace that cannot answer, thousands of times an hour, for two days. Or the health check treats a persistently failing installation as a dead one, the nightly cleanup agrees, and by Thursday the customer has been deleted from your database by a script that was written to tidy up after uninstalls.",
"short_answer": """<p>The error means what it says: <strong>the workspace is migrating into an Enterprise organization and the platform will not answer for it until that finishes</strong>. It is neither a bug in your app nor a permanent condition. It is a period, measured in hours or days rather than seconds, during which one installation is simply unreachable.</p>
<p>So the finding is not an error, it is a <strong>disposition</strong>: what should the scheduler do with this installation now. There are only a few answers &mdash; <code>serve</code>, <code>hold</code>, <code>retry</code>, <code>retire</code>, <code>escalate</code>, <code>investigate</code> &mdash; and the whole note is about the boundary between two of them. <code>token_revoked</code> and <code>account_inactive</code> mean the grant has ended and the row is dead. <code>org_login_required</code> and <code>team_added_to_org</code> mean the grant is fine and the door is temporarily shut. A pipeline that cannot tell those apart will eventually delete a paying customer.</p>
<p><strong>Hold means suspend, not retry.</strong> Stop the scheduled work for that installation, back off in a schedule capped in hours, and keep one cheap <code>auth.test</code> probe running so you know the moment it clears. When it clears, do not simply resume: re-read the identity, because the workspace has just acquired an <code>enterprise_id</code> and possibly a good deal else.</p>""",
"problem": """<p>The first difficulty is that this error breaks the shape every other failure has. Slack failures are per call: this channel, that user, this missing scope. This one is per installation and per hour. Nothing about the call is wrong, and there is no version of the call that would have worked. That is a state your error handling probably has no room for, because error handling is usually organised around what to do differently next time, and here the answer is to do nothing for a while.</p>
<p>The second is that the two obvious behaviours are both wrong, in opposite directions. Retrying is wrong because the workspace cannot answer and will not answer sooner for being asked more often; a migration that lasts eighteen hours against a five-second retry loop is a quarter of a million pointless calls, which is its own rate-limit incident laid on top of the outage. Giving up is wrong because the installation is alive and the customer is still paying, and giving up quietly is how a real outage lasts two days longer than the migration did.</p>
<p>The third is that this error looks exactly like death to any automated cleanup. Housekeeping that removes installations which have failed continuously for N days is a good idea and most mature integrations have one. Its input is usually &ldquo;the token stopped working&rdquo;, and during a migration that is precisely what a token appears to do. The customer is not gone. They are the opposite of gone: they have just been bought, or restructured, or grown into an Enterprise contract, which is a migration into Grid and often the largest account you have.</p>
<p>And the fourth is that when it clears, things have changed underneath. The workspace now belongs to an organization, so it has an <code>enterprise_id</code> where it had none, and your installation row does not. Resuming the suspended queue as though nothing happened is how a migration that Slack handled correctly turns into a data problem a week later.</p>""",
"why": """<p><strong>The output is an instruction, not a diagnosis.</strong> <code>disposition</code> maps an error string to what the scheduler should do, because that is the decision actually being made at three in the morning. A state name that does not imply an action gets translated into one by whoever is on call, and they will translate it differently each time.</p>
<p><strong>No hold error may ever map to <code>retire</code>, and there is a test that says so.</strong> That single assertion is the reason this script exists. It is a property of the mapping rather than a case in it, so it is checked as a property: every error in the hold set, asserted against every disposition that would delete a row.</p>
<p><strong>Backoff is capped in hours because the outage is measured in hours.</strong> <code>backoff_seconds</code> starts at fifteen minutes and caps at four, which for a migration is roughly one probe per cap rather than one per second. The cap is deliberate: an uncapped exponential eventually stops checking altogether, and a five-second retry is an attack on a workspace that is already having a difficult day.</p>
<p><strong>A hold has a duration, and the duration is the thing you tell the customer.</strong> <code>hold_state</code> turns a log of observations into <code>held</code>, <code>cleared</code> or <code>long-hold</code> with a span attached. &ldquo;Your workspace has been unreachable for nineteen hours and Slack reports an enterprise migration in progress&rdquo; is a sentence a customer success manager can send. &ldquo;It is erroring&rdquo; is not.</p>
<p><strong>A long hold escalates to a person and still does not delete.</strong> Past three days the assumption that this is an ordinary migration is worth questioning, so the state changes &mdash; and it changes to <code>long-hold</code>, which means somebody should look, rather than to anything that removes the row. There is no elapsed time after which deleting an installation on the strength of this error becomes correct.</p>
<p><strong>Resuming is a separate step from clearing.</strong> <code>resume_actions</code> compares the identity you stored against the one <code>auth.test</code> returns now. An <code>enterprise_id</code> that has appeared where there was none is the migration's signature, and it means the installation row needs re-keying before the queue restarts. The user and channel identifiers may also have moved, which is a larger job with a note of its own.</p>""",
"steps": [
 {"h": "Turn the error into a disposition before anything else looks at it",
  "body": """<p><code>disposition</code> answers <code>serve</code>, <code>hold</code>, <code>retry</code>, <code>retire</code>, <code>escalate</code>, <code>investigate</code> or <code>unknown</code>. Everything downstream &mdash; alerting, cleanup, the queue &mdash; reads that word rather than the error string, so there is one place where the hold-versus-retire boundary is decided.</p>"""},
 {"h": "Suspend the installation rather than failing its jobs",
  "body": """<p>A held installation should have its scheduled work paused, not attempted and caught. Failing the jobs fills the dead-letter queue with work that was never wrong, and replaying that queue afterwards is considerably harder than never having enqueued it.</p>"""},
 {"h": "Back off in hours, and keep exactly one probe alive",
  "body": """<p><code>backoff_seconds</code> starts at fifteen minutes, doubles, and caps at four hours. One <code>auth.test</code> per interval is enough to notice the moment it clears, and <code>auth.test</code> is the cheapest call in the API.</p>"""},
 {"h": "Record when the hold started so its duration is a fact",
  "body": """<p><code>hold_state</code> reads your observation log and answers <code>held</code>, <code>cleared</code>, <code>long-hold</code> or <code>not-held</code>, with a span in minutes. Without a first-seen timestamp there is no duration, and without a duration there is nothing to tell the customer or to decide on.</p>"""},
 {"h": "Keep the cleanup away from held rows, explicitly",
  "body": """<p>Whatever removes dead installations must read the disposition, not the error. <code>queue_verdict</code> summarises a whole store into how many rows are being served and how many are held, which is the number to put in front of anybody proposing to prune on failure count.</p>"""},
 {"h": "When it clears, re-read the identity before resuming",
  "body": """<p><code>resume_actions</code> compares the stored identity against a fresh <code>auth.test</code>. An <code>enterprise_id</code> where there was none means the workspace is now in an organization and the row must be re-keyed. Changed user or channel identifiers are a re-resolution job, and that job has its own note.</p>"""},
],
"verify": """<p>During a migration the run should show <code>hold</code> and a growing span, and the cleanup should report zero eligible rows. After it clears, the disposition returns to <code>serve</code> and the resume line tells you what changed.</p>
<pre><code class="language-bash">python3 slack_migration_hold.py --store installs.json --log observations.json
# install    T04MKTG            hold        org_login_required: the workspace is
#                               migrating into an organization and will answer once
#                               it settles; suspend the work, do not fail it
# hold       T04MKTG            held        1140 minute(s) since the first hold was
#                               recorded
# backoff    T04MKTG            14400s      capped; one auth.test per interval is
#                               enough to notice the moment it clears
# install    T09OPS             serve       ok: true
# install    T02OLD             retire      token_revoked: the grant has ended and
#                               the row is dead
# queue      some-held          1 held, 1 serving, 1 retiring, of 3
# verdict    2 finding(s)
#   repair: suspend scheduled work for 1 held installation(s); a held row must never
#           be eligible for the cleanup that removes dead ones
#   repair: when the hold clears, re-run auth.test and compare the identity before
#           resuming; a workspace that has just joined an organization has an
#           enterprise_id it did not have</code></pre>""",
"code_intro": "Five pure functions and one <code>auth.test</code> per installation. The function that carries the note is <code>disposition</code>, and the test that carries it is the one asserting that no error in the hold set can produce a disposition which deletes a row &mdash; a property rather than a case, checked as a property. <code>backoff_seconds</code> is four lines and exists so the cap is written down somewhere rather than living as a constant in whoever's retry decorator.",
"py_file": "slack_migration_hold.py",
"py": '''"""Decide what a scheduler should do with a Slack installation that is migrating.

Read only. One GET per installation: auth.test, which is the cheapest call in
the API and the only one worth making against a workspace that has told you it
cannot answer.

The point of the script is one boundary. org_login_required and
team_added_to_org mean the installation is temporarily unreachable; token_revoked
and account_inactive mean the grant has ended. A pipeline that cannot tell those
apart eventually deletes a paying customer in the middle of the migration that
made them an Enterprise account.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_migration_hold")

API = "https://slack.com/api/"

# The workspace is migrating into an organization. Temporary, and measured in
# hours. Nothing in this set may ever produce a disposition that deletes a row.
HOLD_ERRORS = ("org_login_required", "team_added_to_org")

# The grant has ended. These are the only errors that justify retiring a row.
DEAD_ERRORS = ("token_revoked", "account_inactive")

# Try the same call again shortly; nothing about the installation is wrong.
RETRY_ERRORS = ("ratelimited", "service_unavailable", "internal_error", "fatal_error",
                "request_timeout", "unparseable_body")

# Somebody has to do something, and it is not the scheduler.
ESCALATE_ERRORS = ("missing_scope", "not_allowed_token_type", "enterprise_is_restricted",
                   "app_access_restricted", "ekm_access_denied", "not_an_admin",
                   "feature_not_enabled", "accesslimited")

# Could be a rotation that lapsed, could be a credential that was replaced. A
# human decides; the scheduler does not delete.
INVESTIGATE_ERRORS = ("invalid_auth", "token_expired", "not_authed")

MINUTES_PER_HOUR = 60


def disposition(error):
    """What should the scheduler do with this installation? Pure.

    Returns (action, detail). The whole note lives in the boundary between hold
    and retire: no error in HOLD_ERRORS may ever produce retire.

      serve       nothing is wrong.
      hold        temporarily unreachable; suspend the work.
      retry       transient; try the same call again shortly.
      retire      the grant has ended and the row is dead.
      escalate    a policy or configuration decision somebody has to make.
      investigate ambiguous credential state; a human looks, nothing is deleted.
      unknown     unrecognised; treated as investigate rather than as death.
    """
    name = str(error or "").strip()
    if not name:
        return ("serve", "ok: true, so the installation is answering normally")
    if name in HOLD_ERRORS:
        return ("hold", "%s: the workspace is migrating into an organization and will "
                        "answer once it settles; suspend the work, do not fail it"
                % name)
    if name in DEAD_ERRORS:
        return ("retire", "%s: the grant has ended and the row is dead" % name)
    if name in RETRY_ERRORS:
        return ("retry", "%s: transient, so the same call is worth making again "
                         "shortly" % name)
    if name in ESCALATE_ERRORS:
        return ("escalate", "%s: a policy or configuration decision that no amount of "
                            "retrying will change" % name)
    if name in INVESTIGATE_ERRORS:
        return ("investigate", "%s: the credential state is ambiguous; a person looks "
                               "at it and nothing is deleted on the strength of it"
                % name)
    return ("unknown", "%s is not in this map; treated as investigate, because the "
                       "safe default for an unrecognised failure is to keep the row"
            % name)


def backoff_seconds(attempt, base=900, cap=14400):
    """How long to wait before the next probe. Pure.

    Fifteen minutes, doubling, capped at four hours. The cap is the point: an
    uncapped exponential eventually stops checking, and a five second retry is
    an attack on a workspace that is already having a difficult day.
    """
    try:
        n = int(attempt)
    except (TypeError, ValueError):
        n = 0
    n = max(0, min(n, 30))
    return int(min(cap, base * (2 ** n)))


def hold_state(observations, give_up_hours=72):
    """Is this installation held now, and for how long? Pure.

    observations: [(minute, error), ...] where an empty error means the call
    succeeded. Returns (state, minutes).

      not-held        no hold error was ever recorded.
      held            the most recent observation is a hold error.
      long-hold       held for longer than give_up_hours. A person should look;
                      the row is still not deleted.
      cleared         a hold was recorded and the latest observation succeeded.
      nothing-observed  the log is empty.
    """
    seen = sorted(((int(m), str(e or "")) for m, e in (observations or [])),
                  key=lambda row: row[0])
    if not seen:
        return ("nothing-observed", 0)
    holds = [row for row in seen if row[1] in HOLD_ERRORS]
    if not holds:
        return ("not-held", 0)
    span = seen[-1][0] - holds[0][0]
    if seen[-1][1] not in HOLD_ERRORS:
        return ("cleared", span)
    if span >= give_up_hours * MINUTES_PER_HOUR:
        return ("long-hold", span)
    return ("held", span)


def resume_actions(before, after):
    """What has to happen before the suspended work restarts? Pure.

    `before` is the identity you stored, `after` is a fresh auth.test body.
    Returns (state, actions).
    """
    was = before or {}
    now = after or {}
    if now.get("ok") is not True:
        return ("not-resumable", ["the installation is still not answering; keep "
                                  "holding rather than resuming"])
    was_ent = str(was.get("enterprise_id") or "")
    now_ent = str(now.get("enterprise_id") or "")
    actions, state = [], "identity-unchanged"
    if now_ent and not was_ent:
        state = "enterprise-id-appeared"
        actions.append("the workspace now belongs to organization %s and the stored "
                       "row has no enterprise_id; re-key the installation before "
                       "resuming" % now_ent)
    elif now_ent != was_ent:
        state = "enterprise-id-changed"
        actions.append("stored enterprise_id is %r and the token reports %r; the row "
                       "does not describe this installation"
                       % (was_ent or None, now_ent or None))
    if str(was.get("team_id") or "") != str(now.get("team_id") or ""):
        if state == "identity-unchanged":
            state = "team-id-changed"
        actions.append("the workspace id moved from %s to %s; every cached channel id "
                       "for it is suspect"
                       % (was.get("team_id") or "<none>", now.get("team_id") or
                          "<none>"))
    if str(was.get("user_id") or "") != str(now.get("user_id") or ""):
        if state == "identity-unchanged":
            state = "user-id-changed"
        actions.append("the authorising user id moved from %s to %s; cached user ids "
                       "need re-resolving, which is a job of its own"
                       % (was.get("user_id") or "<none>", now.get("user_id") or
                          "<none>"))
    if not actions:
        actions.append("the identity is unchanged; resume the suspended work as it "
                       "was left")
    return (state, actions)


def queue_verdict(rows):
    """One sentence about the whole installation store. Pure.

    rows: [(install, action), ...]. Returns (state, counts).
    """
    seen = [(str(i), str(a)) for i, a in (rows or [])]
    counts = {"installs": len(seen), "held": 0, "serving": 0, "retiring": 0,
              "other": 0}
    for _install, action in seen:
        if action == "hold":
            counts["held"] += 1
        elif action == "serve":
            counts["serving"] += 1
        elif action == "retire":
            counts["retiring"] += 1
        else:
            counts["other"] += 1
    if not seen:
        return ("empty", counts)
    if not counts["held"]:
        return ("serving", counts)
    if counts["held"] == len(seen):
        return ("all-held", counts)
    return ("some-held", counts)


def get(session, method, token, params=None):
    """One GET against the Web API. Returns the parsed body."""
    r = session.get(API + method, params=params or {},
                    headers={"Authorization": "Bearer " + token}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--store", help="JSON array of installation rows; each row needs "
                                    "an install name and a token_env")
    ap.add_argument("--log", help="JSON object of install -> [[minute, error], ...] "
                                  "observations you have already recorded")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="used when --store is not given")
    args = ap.parse_args()

    rows = []
    if args.store:
        with open(args.store, encoding="utf-8") as fh:
            rows = json.load(fh)
    else:
        rows = [{"install": "<the only row>", "token_env": args.token_env}]

    observations = {}
    if args.log:
        with open(args.log, encoding="utf-8") as fh:
            observations = json.load(fh)

    session = requests.Session()
    verdicts, findings = [], []
    for row in rows:
        install = str(row.get("install") or row.get("team_id") or "<unnamed>")
        token = os.environ.get(row.get("token_env") or args.token_env)
        if not token:
            log.warning("install    %-18s no-token    %s is unset", install,
                        row.get("token_env") or args.token_env)
            verdicts.append((install, "investigate"))
            continue
        body = get(session, "auth.test", token)
        error = "" if body.get("ok") is True else str(body.get("error") or "unknown")
        action, why = disposition(error)
        verdicts.append((install, action))
        (log.info if action == "serve" else log.warning)(
            "install    %-18s %-11s %s", install, action, why)

        if action == "hold":
            state, minutes = hold_state(observations.get(install) or
                                        [[0, error]])
            log.warning("hold       %-18s %-11s %d minute(s) since the first hold was "
                        "recorded", install, state, minutes)
            attempt = len(observations.get(install) or [])
            log.warning("backoff    %-18s %-11s capped; one auth.test per interval is "
                        "enough to notice the moment it clears", install,
                        "%ds" % backoff_seconds(attempt))
        elif action == "serve" and observations.get(install):
            state, minutes = hold_state(observations[install] + [[10 ** 6, ""]])
            if state == "cleared":
                resume, actions = resume_actions(row, body)
                log.warning("resume     %-18s %-11s after %d minute(s) held", install,
                            resume, minutes)
                for line in actions:
                    log.warning("           %s", line)
                    if resume != "identity-unchanged":
                        findings.append(line)

    summary, counts = queue_verdict(verdicts)
    (log.info if summary == "serving" else log.warning)(
        "queue      %-18s %d held, %d serving, %d retiring, of %d", summary,
        counts["held"], counts["serving"], counts["retiring"], counts["installs"])

    if counts["held"]:
        findings.append("suspend scheduled work for %d held installation(s); a held "
                        "row must never be eligible for the cleanup that removes dead "
                        "ones" % counts["held"])
        findings.append("when the hold clears, re-run auth.test and compare the "
                        "identity before resuming; a workspace that has just joined "
                        "an organization has an enterprise_id it did not have")
    if not findings:
        log.info("verdict    clean              nothing is held and nothing needs "
                 "re-keying")
        return 0
    log.warning("verdict    %d finding(s)", len(findings))
    for line in findings:
        log.warning("  repair: %s", line)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-migration-hold.mjs",
"js": '''/**
 * Decide what a scheduler should do with a Slack installation that is migrating.
 *
 * Read only. One GET per installation: auth.test, which is the cheapest call in
 * the API and the only one worth making against a workspace that has told you
 * it cannot answer.
 *
 * The point of the script is one boundary. org_login_required and
 * team_added_to_org mean the installation is temporarily unreachable;
 * token_revoked and account_inactive mean the grant has ended.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Temporary, measured in hours. Nothing here may ever produce a disposition
// that deletes a row.
export const HOLD_ERRORS = ['org_login_required', 'team_added_to_org'];

// The grant has ended. The only errors that justify retiring a row.
export const DEAD_ERRORS = ['token_revoked', 'account_inactive'];

export const RETRY_ERRORS = ['ratelimited', 'service_unavailable', 'internal_error',
  'fatal_error', 'request_timeout', 'unparseable_body'];

export const ESCALATE_ERRORS = ['missing_scope', 'not_allowed_token_type',
  'enterprise_is_restricted', 'app_access_restricted', 'ekm_access_denied',
  'not_an_admin', 'feature_not_enabled', 'accesslimited'];

export const INVESTIGATE_ERRORS = ['invalid_auth', 'token_expired', 'not_authed'];

const MINUTES_PER_HOUR = 60;

/**
 * What should the scheduler do with this installation? Pure.
 * Returns [action, detail]; serve, hold, retry, retire, escalate, investigate,
 * unknown.
 */
export function disposition(error) {
  const name = String(error ?? '').trim();
  if (!name) return ['serve', 'ok: true, so the installation is answering normally'];
  if (HOLD_ERRORS.includes(name)) {
    return ['hold', `${name}: the workspace is migrating into an organization and `
      + 'will answer once it settles; suspend the work, do not fail it'];
  }
  if (DEAD_ERRORS.includes(name)) {
    return ['retire', `${name}: the grant has ended and the row is dead`];
  }
  if (RETRY_ERRORS.includes(name)) {
    return ['retry', `${name}: transient, so the same call is worth making again `
      + 'shortly'];
  }
  if (ESCALATE_ERRORS.includes(name)) {
    return ['escalate', `${name}: a policy or configuration decision that no amount `
      + 'of retrying will change'];
  }
  if (INVESTIGATE_ERRORS.includes(name)) {
    return ['investigate', `${name}: the credential state is ambiguous; a person `
      + 'looks at it and nothing is deleted on the strength of it'];
  }
  return ['unknown', `${name} is not in this map; treated as investigate, because the `
    + 'safe default for an unrecognised failure is to keep the row'];
}

/**
 * How long to wait before the next probe. Pure.
 * Fifteen minutes, doubling, capped at four hours.
 */
export function backoffSeconds(attempt, base = 900, cap = 14400) {
  let n = Number.parseInt(attempt, 10);
  if (!Number.isFinite(n)) n = 0;
  n = Math.max(0, Math.min(n, 30));
  return Math.min(cap, base * (2 ** n));
}

/**
 * Is this installation held now, and for how long? Pure.
 * observations: [[minute, error], ...]. Returns [state, minutes].
 */
export function holdState(observations, giveUpHours = 72) {
  const seen = (observations ?? [])
    .map(([m, e]) => [Number.parseInt(m, 10) || 0, String(e ?? '')])
    .sort((a, b) => a[0] - b[0]);
  if (!seen.length) return ['nothing-observed', 0];
  const holds = seen.filter(([, e]) => HOLD_ERRORS.includes(e));
  if (!holds.length) return ['not-held', 0];
  const span = seen[seen.length - 1][0] - holds[0][0];
  if (!HOLD_ERRORS.includes(seen[seen.length - 1][1])) return ['cleared', span];
  if (span >= giveUpHours * MINUTES_PER_HOUR) return ['long-hold', span];
  return ['held', span];
}

/**
 * What has to happen before the suspended work restarts? Pure.
 * Returns [state, actions].
 */
export function resumeActions(before, after) {
  const was = before ?? {};
  const now = after ?? {};
  if (now.ok !== true) {
    return ['not-resumable', ['the installation is still not answering; keep holding '
      + 'rather than resuming']];
  }
  const wasEnt = String(was.enterprise_id ?? '');
  const nowEnt = String(now.enterprise_id ?? '');
  const actions = [];
  let state = 'identity-unchanged';
  if (nowEnt && !wasEnt) {
    state = 'enterprise-id-appeared';
    actions.push(`the workspace now belongs to organization ${nowEnt} and the stored `
      + 'row has no enterprise_id; re-key the installation before resuming');
  } else if (nowEnt !== wasEnt) {
    state = 'enterprise-id-changed';
    actions.push(`stored enterprise_id is ${wasEnt || 'None'} and the token reports `
      + `${nowEnt || 'None'}; the row does not describe this installation`);
  }
  if (String(was.team_id ?? '') !== String(now.team_id ?? '')) {
    if (state === 'identity-unchanged') state = 'team-id-changed';
    actions.push(`the workspace id moved from ${was.team_id ?? '<none>'} to `
      + `${now.team_id ?? '<none>'}; every cached channel id for it is suspect`);
  }
  if (String(was.user_id ?? '') !== String(now.user_id ?? '')) {
    if (state === 'identity-unchanged') state = 'user-id-changed';
    actions.push(`the authorising user id moved from ${was.user_id ?? '<none>'} to `
      + `${now.user_id ?? '<none>'}; cached user ids need re-resolving, which is a `
      + 'job of its own');
  }
  if (!actions.length) {
    actions.push('the identity is unchanged; resume the suspended work as it was left');
  }
  return [state, actions];
}

/**
 * One sentence about the whole installation store. Pure.
 * Returns [state, counts].
 */
export function queueVerdict(rows) {
  const seen = (rows ?? []).map(([i, a]) => [String(i), String(a)]);
  const counts = {
    installs: seen.length, held: 0, serving: 0, retiring: 0, other: 0,
  };
  for (const [, action] of seen) {
    if (action === 'hold') counts.held += 1;
    else if (action === 'serve') counts.serving += 1;
    else if (action === 'retire') counts.retiring += 1;
    else counts.other += 1;
  }
  if (!seen.length) return ['empty', counts];
  if (!counts.held) return ['serving', counts];
  if (counts.held === seen.length) return ['all-held', counts];
  return ['some-held', counts];
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
  const defaultEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const storePath = arg(args, '--store');
  const logPath = arg(args, '--log');

  const rows = storePath
    ? JSON.parse(await readFile(storePath, 'utf8'))
    : [{ install: '<the only row>', token_env: defaultEnv }];
  const observations = logPath ? JSON.parse(await readFile(logPath, 'utf8')) : {};

  const verdicts = [];
  const findings = [];
  for (const row of rows) {
    const install = String(row.install ?? row.team_id ?? '<unnamed>');
    const token = process.env[row.token_env ?? defaultEnv];
    if (!token) {
      console.warn(`install    ${install.padEnd(18)} no-token    `
        + `${row.token_env ?? defaultEnv} is unset`);
      verdicts.push([install, 'investigate']);
      continue;
    }
    // eslint-disable-next-line no-await-in-loop
    const body = await read(token, 'auth.test', {});
    const error = body.ok === true ? '' : String(body.error ?? 'unknown');
    const [action, why] = disposition(error);
    verdicts.push([install, action]);
    const line = `install    ${install.padEnd(18)} ${action.padEnd(11)} ${why}`;
    if (action === 'serve') console.log(line);
    else console.warn(line);

    if (action === 'hold') {
      const [state, minutes] = holdState(observations[install] ?? [[0, error]]);
      console.warn(`hold       ${install.padEnd(18)} ${state.padEnd(11)} ${minutes} `
        + 'minute(s) since the first hold was recorded');
      const attempt = (observations[install] ?? []).length;
      console.warn(`backoff    ${install.padEnd(18)} `
        + `${`${backoffSeconds(attempt)}s`.padEnd(11)} capped; one auth.test per `
        + 'interval is enough to notice the moment it clears');
    } else if (action === 'serve' && observations[install]) {
      const [state, minutes] = holdState([...observations[install], [10 ** 6, '']]);
      if (state === 'cleared') {
        const [resume, actions] = resumeActions(row, body);
        console.warn(`resume     ${install.padEnd(18)} ${resume.padEnd(11)} after `
          + `${minutes} minute(s) held`);
        for (const action2 of actions) {
          console.warn(`           ${action2}`);
          if (resume !== 'identity-unchanged') findings.push(action2);
        }
      }
    }
  }

  const [summary, counts] = queueVerdict(verdicts);
  const summaryLine = `queue      ${summary.padEnd(18)} ${counts.held} held, `
    + `${counts.serving} serving, ${counts.retiring} retiring, of ${counts.installs}`;
  if (summary === 'serving') console.log(summaryLine);
  else console.warn(summaryLine);

  if (counts.held) {
    findings.push(`suspend scheduled work for ${counts.held} held installation(s); a `
      + 'held row must never be eligible for the cleanup that removes dead ones');
    findings.push('when the hold clears, re-run auth.test and compare the identity '
      + 'before resuming; a workspace that has just joined an organization has an '
      + 'enterprise_id it did not have');
  }
  if (!findings.length) {
    console.log('verdict    clean              nothing is held and nothing needs '
      + 're-keying');
    return;
  }
  console.warn(`verdict    ${findings.length} finding(s)`);
  for (const line of findings) console.warn(`  repair: ${line}`);
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Most of these fixtures are a single error string, because that is all a disposition ever gets to work with. The test to read first is the property test: every error in the hold set, asserted against the dispositions that would remove an installation row. It is written as a loop over the set rather than as three separate cases so that adding a migration error to the constant cannot quietly add one that deletes customers.",
"test_py_file": "test_slack_migration_hold.py",
"test_py": '''from slack_migration_hold import (
    DEAD_ERRORS, HOLD_ERRORS, backoff_seconds, disposition, hold_state, queue_verdict,
    resume_actions,
)


def test_a_successful_call_is_served():
    state, detail = disposition("")
    assert state == "serve"
    assert "answering normally" in detail


def test_the_migration_errors_are_held_and_say_suspend_not_fail():
    for error in HOLD_ERRORS:
        state, detail = disposition(error)
        assert state == "hold"
        assert "do not fail it" in detail


def test_no_hold_error_can_ever_delete_a_row():
    for error in HOLD_ERRORS:
        assert disposition(error)[0] not in ("retire",)


def test_only_the_dead_errors_retire_a_row():
    for error in DEAD_ERRORS:
        assert disposition(error)[0] == "retire"


def test_a_rate_limit_is_a_retry_rather_than_a_hold():
    assert disposition("ratelimited")[0] == "retry"


def test_a_policy_refusal_escalates_instead_of_retrying():
    state, detail = disposition("app_access_restricted")
    assert state == "escalate"
    assert "no amount of retrying" in detail


def test_an_ambiguous_credential_is_investigated_not_deleted():
    for error in ("invalid_auth", "token_expired"):
        state, detail = disposition(error)
        assert state == "investigate"
        assert "nothing is deleted" in detail


def test_an_unrecognised_error_keeps_the_row():
    state, detail = disposition("some_new_error")
    assert state == "unknown"
    assert "keep the row" in detail


def test_the_first_backoff_is_a_quarter_of_an_hour():
    assert backoff_seconds(0) == 900


def test_the_backoff_doubles():
    assert backoff_seconds(1) == 1800
    assert backoff_seconds(2) == 3600


def test_the_backoff_is_capped_in_hours():
    assert backoff_seconds(20) == 14400
    assert backoff_seconds(400) == 14400


def test_a_nonsense_attempt_count_does_not_produce_a_tight_loop():
    assert backoff_seconds(-9) == 900
    assert backoff_seconds(None) == 900


def test_an_installation_with_no_hold_recorded_is_not_held():
    assert hold_state([[0, ""], [30, "ratelimited"]])[0] == "not-held"


def test_a_current_hold_carries_its_span():
    state, minutes = hold_state([[0, "org_login_required"],
                                 [1140, "org_login_required"]])
    assert state == "held"
    assert minutes == 1140


def test_a_hold_that_has_cleared_is_reported_as_cleared():
    state, minutes = hold_state([[0, "team_added_to_org"], [600, ""]])
    assert state == "cleared"
    assert minutes == 600


def test_a_hold_past_three_days_escalates_and_still_does_not_delete():
    state, _ = hold_state([[0, "org_login_required"], [72 * 60, "org_login_required"]])
    assert state == "long-hold"


def test_the_give_up_threshold_is_a_parameter_not_a_constant():
    assert hold_state([[0, "org_login_required"], [120, "org_login_required"]],
                      give_up_hours=1)[0] == "long-hold"


def test_observations_are_sorted_before_they_are_read():
    state, minutes = hold_state([[600, ""], [0, "org_login_required"]])
    assert state == "cleared"
    assert minutes == 600


def test_an_empty_log_concludes_nothing():
    assert hold_state([])[0] == "nothing-observed"


def test_an_enterprise_id_appearing_is_the_signature_of_the_migration():
    state, actions = resume_actions({"team_id": "T04MKTG"},
                                    {"ok": True, "team_id": "T04MKTG",
                                     "enterprise_id": "E04NORTHWIND"})
    assert state == "enterprise-id-appeared"
    assert any("re-key" in line for line in actions)


def test_a_changed_workspace_id_makes_cached_channels_suspect():
    state, actions = resume_actions({"team_id": "T04MKTG"},
                                    {"ok": True, "team_id": "T04NEW"})
    assert state == "team-id-changed"
    assert any("cached channel id" in line for line in actions)


def test_a_changed_user_id_is_handed_to_a_job_of_its_own():
    state, actions = resume_actions({"team_id": "T04MKTG", "user_id": "U01"},
                                    {"ok": True, "team_id": "T04MKTG",
                                     "user_id": "W01"})
    assert state == "user-id-changed"
    assert any("job of its own" in line for line in actions)


def test_an_unchanged_identity_simply_resumes():
    state, actions = resume_actions({"team_id": "T04MKTG"},
                                    {"ok": True, "team_id": "T04MKTG"})
    assert state == "identity-unchanged"
    assert "resume the suspended work" in actions[0]


def test_an_installation_that_still_will_not_answer_is_not_resumable():
    state, actions = resume_actions({"team_id": "T04MKTG"},
                                    {"ok": False, "error": "org_login_required"})
    assert state == "not-resumable"
    assert "keep holding" in actions[0]


def test_a_store_with_nothing_held_is_serving():
    state, counts = queue_verdict([("T04MKTG", "serve"), ("T09OPS", "serve")])
    assert state == "serving"
    assert counts["serving"] == 2


def test_a_store_with_one_hold_is_reported_as_such():
    state, counts = queue_verdict([("T04MKTG", "hold"), ("T09OPS", "serve"),
                                   ("T02OLD", "retire")])
    assert state == "some-held"
    assert counts["held"] == 1
    assert counts["retiring"] == 1


def test_every_installation_held_at_once_is_its_own_state():
    assert queue_verdict([("T04MKTG", "hold"), ("T09OPS", "hold")])[0] == "all-held"


def test_an_empty_store_says_so():
    assert queue_verdict([])[0] == "empty"
''',
"test_js_file": "slack-migration-hold.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DEAD_ERRORS, HOLD_ERRORS, backoffSeconds, disposition, holdState, queueVerdict,
  resumeActions,
} from './slack-migration-hold.mjs';

test('a successful call is served', () => {
  const [state, detail] = disposition('');
  assert.equal(state, 'serve');
  assert.match(detail, /answering normally/);
});

test('the migration errors are held and say suspend not fail', () => {
  for (const error of HOLD_ERRORS) {
    const [state, detail] = disposition(error);
    assert.equal(state, 'hold');
    assert.match(detail, /do not fail it/);
  }
});

test('no hold error can ever delete a row', () => {
  for (const error of HOLD_ERRORS) {
    assert.notEqual(disposition(error)[0], 'retire');
  }
});

test('only the dead errors retire a row', () => {
  for (const error of DEAD_ERRORS) {
    assert.equal(disposition(error)[0], 'retire');
  }
});

test('a rate limit is a retry rather than a hold', () => {
  assert.equal(disposition('ratelimited')[0], 'retry');
});

test('a policy refusal escalates instead of retrying', () => {
  const [state, detail] = disposition('app_access_restricted');
  assert.equal(state, 'escalate');
  assert.match(detail, /no amount of retrying/);
});

test('an ambiguous credential is investigated not deleted', () => {
  for (const error of ['invalid_auth', 'token_expired']) {
    const [state, detail] = disposition(error);
    assert.equal(state, 'investigate');
    assert.match(detail, /nothing is deleted/);
  }
});

test('an unrecognised error keeps the row', () => {
  const [state, detail] = disposition('some_new_error');
  assert.equal(state, 'unknown');
  assert.match(detail, /keep the row/);
});

test('the first backoff is a quarter of an hour', () => {
  assert.equal(backoffSeconds(0), 900);
});

test('the backoff doubles', () => {
  assert.equal(backoffSeconds(1), 1800);
  assert.equal(backoffSeconds(2), 3600);
});

test('the backoff is capped in hours', () => {
  assert.equal(backoffSeconds(20), 14400);
  assert.equal(backoffSeconds(400), 14400);
});

test('a nonsense attempt count does not produce a tight loop', () => {
  assert.equal(backoffSeconds(-9), 900);
  assert.equal(backoffSeconds(null), 900);
});

test('an installation with no hold recorded is not held', () => {
  assert.equal(holdState([[0, ''], [30, 'ratelimited']])[0], 'not-held');
});

test('a current hold carries its span', () => {
  const [state, minutes] = holdState([[0, 'org_login_required'],
    [1140, 'org_login_required']]);
  assert.equal(state, 'held');
  assert.equal(minutes, 1140);
});

test('a hold that has cleared is reported as cleared', () => {
  const [state, minutes] = holdState([[0, 'team_added_to_org'], [600, '']]);
  assert.equal(state, 'cleared');
  assert.equal(minutes, 600);
});

test('a hold past three days escalates and still does not delete', () => {
  const [state] = holdState([[0, 'org_login_required'],
    [72 * 60, 'org_login_required']]);
  assert.equal(state, 'long-hold');
});

test('the give up threshold is a parameter not a constant', () => {
  assert.equal(holdState([[0, 'org_login_required'], [120, 'org_login_required']],
    1)[0], 'long-hold');
});

test('observations are sorted before they are read', () => {
  const [state, minutes] = holdState([[600, ''], [0, 'org_login_required']]);
  assert.equal(state, 'cleared');
  assert.equal(minutes, 600);
});

test('an empty log concludes nothing', () => {
  assert.equal(holdState([])[0], 'nothing-observed');
});

test('an enterprise id appearing is the signature of the migration', () => {
  const [state, actions] = resumeActions({ team_id: 'T04MKTG' },
    { ok: true, team_id: 'T04MKTG', enterprise_id: 'E04NORTHWIND' });
  assert.equal(state, 'enterprise-id-appeared');
  assert.equal(actions.some((a) => a.includes('re-key')), true);
});

test('a changed workspace id makes cached channels suspect', () => {
  const [state, actions] = resumeActions({ team_id: 'T04MKTG' },
    { ok: true, team_id: 'T04NEW' });
  assert.equal(state, 'team-id-changed');
  assert.equal(actions.some((a) => a.includes('cached channel id')), true);
});

test('a changed user id is handed to a job of its own', () => {
  const [state, actions] = resumeActions({ team_id: 'T04MKTG', user_id: 'U01' },
    { ok: true, team_id: 'T04MKTG', user_id: 'W01' });
  assert.equal(state, 'user-id-changed');
  assert.equal(actions.some((a) => a.includes('job of its own')), true);
});

test('an unchanged identity simply resumes', () => {
  const [state, actions] = resumeActions({ team_id: 'T04MKTG' },
    { ok: true, team_id: 'T04MKTG' });
  assert.equal(state, 'identity-unchanged');
  assert.match(actions[0], /resume the suspended work/);
});

test('an installation that still will not answer is not resumable', () => {
  const [state, actions] = resumeActions({ team_id: 'T04MKTG' },
    { ok: false, error: 'org_login_required' });
  assert.equal(state, 'not-resumable');
  assert.match(actions[0], /keep holding/);
});

test('a store with nothing held is serving', () => {
  const [state, counts] = queueVerdict([['T04MKTG', 'serve'], ['T09OPS', 'serve']]);
  assert.equal(state, 'serving');
  assert.equal(counts.serving, 2);
});

test('a store with one hold is reported as such', () => {
  const [state, counts] = queueVerdict([['T04MKTG', 'hold'], ['T09OPS', 'serve'],
    ['T02OLD', 'retire']]);
  assert.equal(state, 'some-held');
  assert.equal(counts.held, 1);
  assert.equal(counts.retiring, 1);
});

test('every installation held at once is its own state', () => {
  assert.equal(queueVerdict([['T04MKTG', 'hold'], ['T09OPS', 'hold']])[0], 'all-held');
});

test('an empty store says so', () => {
  assert.equal(queueVerdict([])[0], 'empty');
});
''',
"faq": [
 ("How long does an enterprise migration take?",
  "Slack does not publish a figure, and this note deliberately does not invent one. What the documentation says is that the workspace will not be available until the migration is complete, which is why the script measures the duration you actually observe rather than predicting it. Reports range from a few hours to more than a day, and the practical consequence is the shape of the backoff: capped in hours, one cheap probe per interval, and a state change past three days that asks a person to look rather than concluding anything."),
 ("Should we alert on this?",
  "Alert once, as a notice rather than a page, and then stay quiet. The condition is expected, the resolution is somebody else's, and there is no action for whoever is on call except to confirm that the installation is held rather than failing. What is worth paging on is the opposite condition: an installation that has been held for longer than your give-up threshold, because that is the case where the assumption that this is an ordinary migration has stopped being safe."),
 ("Is this the same as team_added_to_org?",
  "They are two errors from the same event, and the script gives them the same disposition on purpose, but their documented wording differs in a way that matters. org_login_required says the workspace will not be available until the migration completes. team_added_to_org says platform operations will be intermittently unavailable during the transition, and intermittent is a genuinely different thing to sample: some calls succeed, which makes a single health check unreliable. The second error also has consequences that outlive the window, because the identifiers get renumbered, and that part has its own note."),
 ("Our cleanup deleted an installation during a migration. How do we stop that happening again?",
  "Make the cleanup read a disposition rather than a failure count. A failure count cannot distinguish a workspace that has left from a workspace that is temporarily unreachable, and both look like a token that stopped working. The rule to encode is narrow and absolute: only token_revoked and account_inactive justify retiring a row, everything else is served, held, retried, escalated or investigated. The test in this note asserts that no hold error can produce a retiring disposition, which is the property you want in your own code rather than in a script that inspects it."),
 ("Can we do anything to make it finish faster?",
  "No. The migration is being performed by Slack on behalf of the customer's administrators and nothing your app does affects it, which is worth saying plainly because the instinct is to try. The useful work is on your side and it is all preparation: make sure the queue suspends rather than fails, make sure the cleanup cannot see held rows, and have the resume path ready, because the moment it clears you will want to re-read the identity before the first job runs."),
],
"related": [
 ("/slack/team-added-to-org/", "the other half of the same migration, and what it renumbers"),
 ("/slack/app-uninstalled-orphan-install-record/", "the cleanup this note is asking you to restrain"),
 ("/slack/ratelimited-retry-after-ignored/", "the retry discipline for the failures that are transient"),
],
"citations": [CITE_CONVERSATIONS_HISTORY, CITE_AUTH_TEST, CITE_GRID_DEV, CITE_ORG_DEPLOY],
})

GUIDES.append({
"slug": "team-added-to-org",
"title": "team_added_to_org: user ids are renumbered by the migration",
"description": "The window is intermittent, so one health check proves nothing, and when it closes your cached U ids have W equivalents. Audit them with migration.exchange.",
"h1": "team_added_to_org: user ids are renumbered by the migration",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack team_added_to_org error",
             "slack migration.exchange user id map",
             "slack U id to W id enterprise grid",
             "slack user_not_found after grid migration",
             "slack cached user ids stale migration"],
"deps": "Python 3.9+ with requests, or Node.js 18+; a token with tokens.basic for migration.exchange, and the list of Slack user ids your database has cached for that workspace",
"lead": "The migration finished on Saturday and the app came back on its own, which is what everybody hoped for. On Monday a report comes in that notifications are going to the wrong people, or to nobody, and the log is full of <code>user_not_found</code> for ids that resolved perfectly a week ago.</p><p>The error that preceded all this was <code>{\"ok\": false, \"error\": \"team_added_to_org\"}</code> &mdash; <em>the workspace associated with your request is currently undergoing migration to an Enterprise Organization. Web API and other platform operations will be intermittently unavailable until the transition is complete.</em> The outage was the visible half. The half that costs you Monday is that the workspace's user identifiers now have organization-level equivalents, and every one you cached is a workspace-local id for a workspace that is no longer standalone.",
"short_answer": """<p><strong>Intermittently unavailable</strong> is the important word in the error, and it is the word that separates this from the other migration error. Some calls succeed during the window. A health check that samples once and gets a good answer will report the installation healthy while two thirds of its work is failing, so the window has to be measured over a run of observations rather than a single one.</p>
<p>When the window closes, the identifiers have moved. A workspace inside an Enterprise organization has organization-level user ids beginning with <code>W</code> alongside the workspace-local ones beginning with <code>U</code>, and Slack publishes exactly one method for converting between them: <strong><code>migration.exchange</code></strong>, which takes up to 400 user ids per request, needs the <code>tokens.basic</code> scope, and returns a <code>user_id_map</code> plus an <code>invalid_user_ids</code> list. Passing <code>to_old=true</code> converts in the other direction.</p>
<p>So the audit is a cache audit rather than an availability one. Feed it the user ids your database holds for that workspace, batch them by 400, and read the map: an id that maps to itself is fine, an id that maps to a different one is a row in your database pointing at nothing, and an id that comes back in <code>invalid_user_ids</code> is not recognised in this organization at all.</p>""",
"problem": """<p>The first difficulty is that the failure is delayed and the cause is not. The migration is loud &mdash; errors everywhere, for hours &mdash; and then it ends and everything works, which reads as a full recovery. The consequences arrive days later as <code>user_not_found</code> on ids nobody has touched, or worse, as a notification delivered to the wrong person because a stale id was reused. By then the migration is not in anybody's mind as a possible cause, because the migration was last week and it resolved.</p>
<p>The second is that intermittency defeats the instruments. During the window some calls answer and some do not, so a monitor that samples the installation once every five minutes will show a flapping service rather than a migration, and a retry that succeeds on the third attempt will hide the condition entirely. The error string is the only thing that names what is happening, and it only appears on the attempts that failed &mdash; which are the ones a retry decorator swallows.</p>
<p>The third is that the id problem is invisible to every ordinary check. Your database is internally consistent. The ids are well-formed. Nothing in your app can tell that a <code>U</code> id has been superseded, because the id has not become malformed, it has become <em>historical</em>. The only way to find out is to ask Slack, and the only method that answers is the one built for this exact purpose.</p>
<p>And the fourth is what you are left with if the ids cannot be recovered. If the only key you ever stored for a person was their Slack user id, an id that no longer resolves is a row you cannot re-associate with a human being. If you stored an email address or your own internal id alongside it, the same event is a re-resolution: enumerate the workspace again, match on the stable key, write the new id. That difference is decided long before the migration happens.</p>""",
"why": """<p><strong>The window is read over a run of observations, not one.</strong> Because the documented condition is intermittent, a single probe is not evidence of anything: a success does not mean the migration finished and a failure does not mean it has not. The script asks for the observations you recorded and reports the proportion, because a proportion is what an intermittent condition actually looks like.</p>
<p><strong>The remap check uses the method Slack built for it, and no other.</strong> <code>migration.exchange</code> exists specifically to map workspace-local ids to organization-level ones. Guessing at the mapping, or trying to derive a <code>W</code> id from a <code>U</code> id, is not possible; probing each id with <code>users.info</code> tells you only that it failed, not what it became.</p>
<p><strong>Four outcomes per id, and the fourth is the one to be careful with.</strong> An id can be unchanged, remapped, listed as invalid, or simply not returned. The last one is not the same as unchanged, and a script that treats a missing key as &ldquo;no change&rdquo; will report a clean cache while quietly ignoring the ids it could not account for. It is reported as unresolved and counted separately.</p>
<p><strong>Batches are 400 because the method says 400.</strong> The documented limit is 400 user ids per request, and a cache of nine thousand is twenty-three requests rather than one. The batching is a pure function so the boundary is testable without a token, which matters because getting it wrong produces <code>too_many_users</code> against a customer who is already having a bad week.</p>
<p><strong>The stable-key question is asked even when nothing has moved.</strong> The most valuable output of this check, on a workspace that has not migrated at all, is the count of records whose only identifier is a Slack id. That is the number that decides whether a future migration is a re-resolution or a data loss, and it is knowable today.</p>
<p><strong>The availability half is deliberately handed over.</strong> What the scheduler should do while the workspace is unreachable &mdash; suspend rather than fail, back off in hours, and keep the cleanup away from the row &mdash; is a different decision with its own note. This one starts where that one ends: the calls are answering again, and now the identifiers need checking.</p>""",
"steps": [
 {"h": "Record the error rather than letting the retry swallow it",
  "body": """<p>An intermittent failure is only visible if the failed attempts are logged with their error string. If your client retries three times and reports success, <code>team_added_to_org</code> never reaches your logs and the migration is invisible until its consequences arrive.</p>"""},
 {"h": "Check that migration.exchange is available before trusting its answer",
  "body": """<p><code>exchange_availability</code> separates <code>available</code> from <code>not-an-enterprise</code> (<code>not_enterprise_team</code>, meaning this workspace is not in an organization), <code>scope-missing</code> (<code>tokens.basic</code> is not granted), <code>migration-in-progress</code> and <code>batch-too-large</code>. Only the first justifies reading the map.</p>"""},
 {"h": "Batch the cached ids by 400",
  "body": """<p><code>chunk_users</code> splits your id list into requests of the documented maximum. It clamps the size rather than trusting the caller, because the failure for exceeding it is <code>too_many_users</code> and it costs a round trip against a workspace you are already worried about.</p>"""},
 {"h": "Read four outcomes per id, and keep the fourth separate",
  "body": """<p><code>remap_verdict</code> answers <code>unchanged</code>, <code>remapped</code>, <code>invalid</code> or <code>not-returned</code>. Only the first means the row in your database is still correct. <code>not-returned</code> is explicitly not a synonym for unchanged.</p>"""},
 {"h": "Take the census before you take any action",
  "body": """<p><code>cache_verdict</code> answers <code>clean</code>, <code>stale-ids</code>, <code>unrecognised-ids</code> or <code>partially-assessed</code> with counts. Nine remapped ids out of nine thousand is an afternoon. Nine thousand out of nine thousand is a re-enumeration, and it is better to know which before starting.</p>"""},
 {"h": "Check whether you can re-resolve at all",
  "body": """<p><code>stable_key_audit</code> counts the records whose only identifier is a Slack id. Those are the ones a remap turns into orphans. Storing an email address or your own key alongside the Slack id converts the whole class of problem into a lookup.</p>"""},
],
"verify": """<p>After re-resolving, run it again with the same id list. Every row should read <code>unchanged</code>, and the stable-key line should be the number you want it to be rather than the number you inherited.</p>
<pre><code class="language-bash">python3 slack_id_remap_audit.py --cache people.json
# context    enterprise         enterprise_id E04NORTHWIND, so workspace-local ids
#                               may have organization-level equivalents
# exchange   available          migration.exchange answered for the first batch
# batches    3                  1174 cached id(s) in requests of at most 400
# id         U06UBSUN5          remapped    U06UBSUN5 is W06M56XJM at the organization
#                               level; every row keyed on the old id points at nothing
# id         W06UAZ65Q          unchanged   already an organization level id
# id         U21ABZZXX          invalid     in invalid_user_ids: Slack does not
#                               recognise it in this organization at all
# cache      stale-ids          842 remapped, 1 invalid, 331 unchanged, of 1174
# keys       some-stable        409 of 1174 record(s) carry only a Slack id
# verdict    2 finding(s)
#   repair: re-resolve the 842 remapped id(s) from the user_id_map before any of them
#           is used again; a remapped id is a row pointing at nothing
#   repair: 409 record(s) carry no stable key of your own; store an email address or
#           your own id alongside the Slack id so the next remap is a lookup rather
#           than a loss</code></pre>""",
"code_intro": "Two GETs and five pure functions. The GETs are <code>auth.test</code>, for whether an organization is involved at all, and <code>migration.exchange</code>, which is the only method that answers the question this note asks. The function to read carefully is <code>remap_verdict</code>, because it has four outcomes rather than the obvious two: an id that came back in neither the map nor the invalid list is reported as unresolved and never quietly filed as unchanged.",
"py_file": "slack_id_remap_audit.py",
"py": '''"""Find cached Slack user ids that a Grid migration has superseded.

Read only. Two GET methods: auth.test, for whether an organization is involved,
and migration.exchange, which maps workspace-local user ids to their
organization-level equivalents. migration.exchange returns a mapping; it changes
nothing, and this script never writes to your database either. The repairs are
printed for a human to run.

The method is documented as accepting up to 400 user ids per request, needing
the tokens.basic scope, and returning user_id_map alongside invalid_user_ids.
Passing to_old converts in the opposite direction, which this script does not
do: the question here is what a cached old id became.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_id_remap_audit")

API = "https://slack.com/api/"

# The documented maximum number of user ids in one migration.exchange request.
MAX_USERS_PER_REQUEST = 400

# Fields that count as a key of your own: something that survives a remap.
STABLE_KEY_FIELDS = ("email", "external_id", "local_id", "person_id")


def id_shape(user_id):
    """Which kind of Slack user id is this? Pure.

    Returns (state, detail).

      workspace-local  a U id, local to one workspace.
      org-global       a W id, the organization-level identity.
      bot              a B id, which is not a person.
      absent           nothing to classify.
      unrecognised     anything else; reported rather than assumed.
    """
    uid = str(user_id or "").strip().upper()
    if not uid:
        return ("absent", "no id to classify")
    if uid.startswith("U"):
        return ("workspace-local", "%s is a workspace-local id, which is the kind a "
                                   "migration supersedes" % uid)
    if uid.startswith("W"):
        return ("org-global", "%s is already an organization-level id" % uid)
    if uid.startswith("B"):
        return ("bot", "%s is a bot id rather than a person" % uid)
    return ("unrecognised", "%s is not a shape this script recognises" % uid)


def exchange_availability(body):
    """Can migration.exchange answer for this token and workspace? Pure.

    Returns (state, detail).

      available            the map came back.
      not-an-enterprise    not_enterprise_team: this workspace is not in an org,
                           so there is nothing to exchange.
      scope-missing        tokens.basic was not granted.
      migration-in-progress  the window has not closed; the answer would be
                           unreliable even where the call succeeds.
      batch-too-large      too_many_users: more than the documented maximum.
      transient            try again; nothing was learned.
      unassessable         anything else.
    """
    doc = body or {}
    if doc.get("ok") is True:
        return ("available", "migration.exchange answered, so the map can be read")
    error = str(doc.get("error") or "")
    if error == "not_enterprise_team":
        return ("not-an-enterprise", "not_enterprise_team: this workspace is not part "
                                     "of an organization, so no id has an "
                                     "organization-level equivalent")
    if error == "missing_scope":
        return ("scope-missing", "missing_scope: migration.exchange needs tokens.basic")
    if error in ("org_login_required", "team_added_to_org"):
        return ("migration-in-progress", "%s: the window has not closed, and an answer "
                                         "taken during it would be unreliable even "
                                         "where the call succeeds" % error)
    if error == "too_many_users":
        return ("batch-too-large", "too_many_users: the documented maximum is %d ids "
                                   "per request" % MAX_USERS_PER_REQUEST)
    if error in ("ratelimited", "service_unavailable", "internal_error",
                 "unparseable_body"):
        return ("transient", "%s: try again; this call established nothing" % error)
    if not error:
        return ("unassessable", "no ok field and no error, so nothing can be read "
                                "from this response")
    return ("unassessable", "%s, which is a different problem" % error)


def chunk_users(user_ids, size=MAX_USERS_PER_REQUEST):
    """Split cached ids into requests of at most the documented maximum. Pure.

    The size is clamped rather than trusted, because exceeding it costs a round
    trip and a too_many_users error against a workspace that has just migrated.
    """
    ids = [str(u).strip() for u in (user_ids or []) if str(u).strip()]
    try:
        step = int(size)
    except (TypeError, ValueError):
        step = MAX_USERS_PER_REQUEST
    step = max(1, min(step, MAX_USERS_PER_REQUEST))
    return [ids[i:i + step] for i in range(0, len(ids), step)]


def remap_verdict(cached_id, id_map, invalid_ids=()):
    """What happened to one cached id? Pure.

    Four outcomes, and the fourth is the one to be careful with: an id that came
    back in neither the map nor the invalid list is unresolved, not unchanged.

    Returns (state, detail).
    """
    uid = str(cached_id or "").strip()
    mapping = id_map or {}
    invalid = {str(i) for i in (invalid_ids or ())}
    if not uid:
        return ("absent", "no id to check")
    if uid in invalid:
        return ("invalid", "%s came back in invalid_user_ids: Slack does not "
                           "recognise it in this organization at all" % uid)
    if uid not in mapping:
        return ("not-returned", "%s appeared in neither the map nor the invalid list; "
                                "treat it as unresolved rather than as unchanged"
                % uid)
    mapped = str(mapping[uid])
    if mapped == uid:
        return ("unchanged", "%s is its own organization-level id, so nothing keyed "
                             "on it moved" % uid)
    if id_shape(uid)[0] == "workspace-local" and id_shape(mapped)[0] == "org-global":
        return ("remapped", "%s is %s at the organization level; every row keyed on "
                            "the old id points at nothing" % (uid, mapped))
    return ("changed", "%s now maps to %s, which is not the shape this script "
                       "expected" % (uid, mapped))


def cache_verdict(states):
    """The census over the whole cache. Pure. Returns (state, counts)."""
    seen = [str(s) for s in (states or [])]
    counts = {"ids": len(seen), "remapped": 0, "invalid": 0, "unchanged": 0,
              "unresolved": 0}
    for state in seen:
        if state == "remapped":
            counts["remapped"] += 1
        elif state == "invalid":
            counts["invalid"] += 1
        elif state == "unchanged":
            counts["unchanged"] += 1
        else:
            counts["unresolved"] += 1
    if not seen:
        return ("nothing-checked", counts)
    if counts["remapped"]:
        return ("stale-ids", counts)
    if counts["invalid"]:
        return ("unrecognised-ids", counts)
    if counts["unresolved"]:
        return ("partially-assessed", counts)
    return ("clean", counts)


def stable_key_audit(records):
    """How many records could survive a remap? Pure. Returns (state, counts).

    A record carrying only a Slack user id becomes an orphan the moment that id
    is superseded. A record carrying an email address or an id of your own turns
    the same event into a lookup.
    """
    rows = list(records or [])
    counts = {"records": len(rows), "stable": 0, "slack_only": 0}
    for row in rows:
        doc = row if isinstance(row, dict) else {}
        if any(str(doc.get(field) or "").strip() for field in STABLE_KEY_FIELDS):
            counts["stable"] += 1
        else:
            counts["slack_only"] += 1
    if not rows:
        return ("nothing-checked", counts)
    if not counts["slack_only"]:
        return ("all-stable", counts)
    if not counts["stable"]:
        return ("slack-id-only", counts)
    return ("some-stable", counts)


def get(session, method, params=None):
    """One GET against the Web API. Returns the parsed body."""
    r = session.get(API + method, params=params or {}, timeout=30)
    try:
        return r.json()
    except ValueError:
        return {"ok": False, "error": "unparseable_body"}


def load_records(path, ids):
    """Records as your database holds them, or bare ids from the command line."""
    if path:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return [{"slack_user_id": u.strip()} for u in ids.split(",") if u.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding a token with tokens.basic")
    ap.add_argument("--cache", help="JSON array of your records; each needs "
                                    "slack_user_id, plus whatever else you store")
    ap.add_argument("--ids", default="", help="comma separated user ids, if you have "
                                              "no export to hand")
    ap.add_argument("--team", default="", help="team_id, required when the token is "
                                               "an organization-level one")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("token      missing            set %s to a token with tokens.basic",
                  args.token_env)
        return 2
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token})

    auth = get(session, "auth.test")
    if auth.get("ok") is not True:
        log.error("context    unreadable         auth.test answered %s",
                  auth.get("error") or "nothing")
        return 2
    enterprise = auth.get("enterprise_id") or ""
    if enterprise:
        log.info("context    enterprise         enterprise_id %s, so workspace-local "
                 "ids may have organization-level equivalents", enterprise)
    else:
        log.info("context    standalone         no enterprise_id, so nothing here has "
                 "been renumbered yet; the stable-key count below is still worth "
                 "reading")

    records = load_records(args.cache, args.ids)
    cached = [str((r or {}).get("slack_user_id") or "") for r in records]
    batches = chunk_users([u for u in cached if u])
    log.info("batches    %-18s %d cached id(s) in requests of at most %d",
             str(len(batches)), len([u for u in cached if u]), MAX_USERS_PER_REQUEST)

    mapping, invalid, availability = {}, [], "nothing-checked"
    for batch in batches:
        params = {"users": ",".join(batch)}
        if args.team:
            params["team_id"] = args.team
        body = get(session, "migration.exchange", params)
        availability, why = exchange_availability(body)
        if availability != "available":
            (log.warning)("exchange   %-18s %s", availability, why)
            break
        mapping.update(body.get("user_id_map") or {})
        invalid.extend(body.get("invalid_user_ids") or [])
    if availability == "available":
        log.info("exchange   %-18s migration.exchange answered for %d batch(es)",
                 availability, len(batches))

    states = []
    for uid in cached:
        if not uid:
            continue
        state, why = remap_verdict(uid, mapping, invalid)
        states.append(state)
        (log.info if state == "unchanged" else log.warning)(
            "id         %-18s %-11s %s", uid, state, why)

    cache_state, counts = cache_verdict(states)
    (log.info if cache_state == "clean" else log.warning)(
        "cache      %-18s %d remapped, %d invalid, %d unchanged, of %d", cache_state,
        counts["remapped"], counts["invalid"], counts["unchanged"], counts["ids"])

    key_state, key_counts = stable_key_audit(records)
    (log.info if key_state == "all-stable" else log.warning)(
        "keys       %-18s %d of %d record(s) carry only a Slack id", key_state,
        key_counts["slack_only"], key_counts["records"])

    findings = []
    if counts["remapped"]:
        findings.append("re-resolve the %d remapped id(s) from the user_id_map before "
                        "any of them is used again; a remapped id is a row pointing "
                        "at nothing" % counts["remapped"])
    if counts["invalid"]:
        findings.append("%d id(s) came back in invalid_user_ids; re-enumerate the "
                        "workspace and match those records on a key of your own"
                        % counts["invalid"])
    if key_counts["slack_only"]:
        findings.append("%d record(s) carry no stable key of your own; store an email "
                        "address or your own id alongside the Slack id so the next "
                        "remap is a lookup rather than a loss"
                        % key_counts["slack_only"])
    if not findings:
        log.info("verdict    clean              nothing cached has been superseded")
        return 0
    log.warning("verdict    %d finding(s)", len(findings))
    for line in findings:
        log.warning("  repair: %s", line)
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-id-remap-audit.mjs",
"js": '''/**
 * Find cached Slack user ids that a Grid migration has superseded.
 *
 * Read only. Two GET methods: auth.test, for whether an organization is
 * involved, and migration.exchange, which maps workspace-local user ids to
 * their organization-level equivalents. migration.exchange returns a mapping;
 * it changes nothing, and this script never writes to your database either.
 *
 * The method is documented as accepting up to 400 user ids per request, needing
 * the tokens.basic scope, and returning user_id_map alongside invalid_user_ids.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// The documented maximum number of user ids in one migration.exchange request.
export const MAX_USERS_PER_REQUEST = 400;

// Fields that count as a key of your own: something that survives a remap.
export const STABLE_KEY_FIELDS = ['email', 'external_id', 'local_id', 'person_id'];

/**
 * Which kind of Slack user id is this? Pure.
 * Returns [state, detail]; workspace-local, org-global, bot, absent,
 * unrecognised.
 */
export function idShape(userId) {
  const uid = String(userId ?? '').trim().toUpperCase();
  if (!uid) return ['absent', 'no id to classify'];
  if (uid.startsWith('U')) {
    return ['workspace-local', `${uid} is a workspace-local id, which is the kind a `
      + 'migration supersedes'];
  }
  if (uid.startsWith('W')) {
    return ['org-global', `${uid} is already an organization-level id`];
  }
  if (uid.startsWith('B')) return ['bot', `${uid} is a bot id rather than a person`];
  return ['unrecognised', `${uid} is not a shape this script recognises`];
}

/**
 * Can migration.exchange answer for this token and workspace? Pure.
 * Returns [state, detail].
 */
export function exchangeAvailability(body) {
  const doc = body ?? {};
  if (doc.ok === true) {
    return ['available', 'migration.exchange answered, so the map can be read'];
  }
  const error = String(doc.error ?? '');
  if (error === 'not_enterprise_team') {
    return ['not-an-enterprise', 'not_enterprise_team: this workspace is not part of '
      + 'an organization, so no id has an organization-level equivalent'];
  }
  if (error === 'missing_scope') {
    return ['scope-missing', 'missing_scope: migration.exchange needs tokens.basic'];
  }
  if (error === 'org_login_required' || error === 'team_added_to_org') {
    return ['migration-in-progress', `${error}: the window has not closed, and an `
      + 'answer taken during it would be unreliable even where the call succeeds'];
  }
  if (error === 'too_many_users') {
    return ['batch-too-large', 'too_many_users: the documented maximum is '
      + `${MAX_USERS_PER_REQUEST} ids per request`];
  }
  if (['ratelimited', 'service_unavailable', 'internal_error',
    'unparseable_body'].includes(error)) {
    return ['transient', `${error}: try again; this call established nothing`];
  }
  if (!error) {
    return ['unassessable', 'no ok field and no error, so nothing can be read from '
      + 'this response'];
  }
  return ['unassessable', `${error}, which is a different problem`];
}

/** Split cached ids into requests of at most the documented maximum. Pure. */
export function chunkUsers(userIds, size = MAX_USERS_PER_REQUEST) {
  const ids = (userIds ?? []).map((u) => String(u).trim()).filter(Boolean);
  let step = Number.parseInt(size, 10);
  if (!Number.isFinite(step)) step = MAX_USERS_PER_REQUEST;
  step = Math.max(1, Math.min(step, MAX_USERS_PER_REQUEST));
  const out = [];
  for (let i = 0; i < ids.length; i += step) out.push(ids.slice(i, i + step));
  return out;
}

/**
 * What happened to one cached id? Pure.
 * Four outcomes, and an id that came back in neither the map nor the invalid
 * list is unresolved, not unchanged.
 */
export function remapVerdict(cachedId, idMap, invalidIds = []) {
  const uid = String(cachedId ?? '').trim();
  const mapping = idMap ?? {};
  const invalid = new Set((invalidIds ?? []).map(String));
  if (!uid) return ['absent', 'no id to check'];
  if (invalid.has(uid)) {
    return ['invalid', `${uid} came back in invalid_user_ids: Slack does not `
      + 'recognise it in this organization at all'];
  }
  if (!Object.prototype.hasOwnProperty.call(mapping, uid)) {
    return ['not-returned', `${uid} appeared in neither the map nor the invalid list; `
      + 'treat it as unresolved rather than as unchanged'];
  }
  const mapped = String(mapping[uid]);
  if (mapped === uid) {
    return ['unchanged', `${uid} is its own organization-level id, so nothing keyed `
      + 'on it moved'];
  }
  if (idShape(uid)[0] === 'workspace-local' && idShape(mapped)[0] === 'org-global') {
    return ['remapped', `${uid} is ${mapped} at the organization level; every row `
      + 'keyed on the old id points at nothing'];
  }
  return ['changed', `${uid} now maps to ${mapped}, which is not the shape this `
    + 'script expected'];
}

/** The census over the whole cache. Pure. Returns [state, counts]. */
export function cacheVerdict(states) {
  const seen = (states ?? []).map(String);
  const counts = {
    ids: seen.length, remapped: 0, invalid: 0, unchanged: 0, unresolved: 0,
  };
  for (const state of seen) {
    if (state === 'remapped') counts.remapped += 1;
    else if (state === 'invalid') counts.invalid += 1;
    else if (state === 'unchanged') counts.unchanged += 1;
    else counts.unresolved += 1;
  }
  if (!seen.length) return ['nothing-checked', counts];
  if (counts.remapped) return ['stale-ids', counts];
  if (counts.invalid) return ['unrecognised-ids', counts];
  if (counts.unresolved) return ['partially-assessed', counts];
  return ['clean', counts];
}

/** How many records could survive a remap? Pure. Returns [state, counts]. */
export function stableKeyAudit(records) {
  const rows = records ?? [];
  const counts = { records: rows.length, stable: 0, slack_only: 0 };
  for (const row of rows) {
    const doc = (row && typeof row === 'object') ? row : {};
    const stable = STABLE_KEY_FIELDS.some((f) => String(doc[f] ?? '').trim());
    if (stable) counts.stable += 1;
    else counts.slack_only += 1;
  }
  if (!rows.length) return ['nothing-checked', counts];
  if (!counts.slack_only) return ['all-stable', counts];
  if (!counts.stable) return ['slack-id-only', counts];
  return ['some-stable', counts];
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
    console.error(`token      missing            set ${tokenEnv} to a token with `
      + 'tokens.basic');
    process.exitCode = 2;
    return;
  }

  const auth = await read(token, 'auth.test', {});
  if (auth.ok !== true) {
    console.error(`context    unreadable         auth.test answered `
      + `${auth.error ?? 'nothing'}`);
    process.exitCode = 2;
    return;
  }
  const enterprise = auth.enterprise_id ?? '';
  if (enterprise) {
    console.log(`context    enterprise         enterprise_id ${enterprise}, so `
      + 'workspace-local ids may have organization-level equivalents');
  } else {
    console.log('context    standalone         no enterprise_id, so nothing here has '
      + 'been renumbered yet; the stable-key count below is still worth reading');
  }

  const cachePath = arg(args, '--cache');
  const records = cachePath
    ? JSON.parse(await readFile(cachePath, 'utf8'))
    : arg(args, '--ids').split(',').map((u) => u.trim()).filter(Boolean)
      .map((u) => ({ slack_user_id: u }));
  const cached = records.map((r) => String((r ?? {}).slack_user_id ?? ''));
  const present = cached.filter(Boolean);
  const batches = chunkUsers(present);
  console.log(`batches    ${String(batches.length).padEnd(18)} ${present.length} `
    + `cached id(s) in requests of at most ${MAX_USERS_PER_REQUEST}`);

  const team = arg(args, '--team');
  const mapping = {};
  const invalid = [];
  let availability = 'nothing-checked';
  for (const batch of batches) {
    const params = { users: batch.join(',') };
    if (team) params.team_id = team;
    // eslint-disable-next-line no-await-in-loop
    const body = await read(token, 'migration.exchange', params);
    let why;
    [availability, why] = exchangeAvailability(body);
    if (availability !== 'available') {
      console.warn(`exchange   ${availability.padEnd(18)} ${why}`);
      break;
    }
    Object.assign(mapping, body.user_id_map ?? {});
    invalid.push(...(body.invalid_user_ids ?? []));
  }
  if (availability === 'available') {
    console.log(`exchange   ${availability.padEnd(18)} migration.exchange answered `
      + `for ${batches.length} batch(es)`);
  }

  const states = [];
  for (const uid of present) {
    const [state, why] = remapVerdict(uid, mapping, invalid);
    states.push(state);
    const line = `id         ${uid.padEnd(18)} ${state.padEnd(11)} ${why}`;
    if (state === 'unchanged') console.log(line);
    else console.warn(line);
  }

  const [cacheState, counts] = cacheVerdict(states);
  const cacheLine = `cache      ${cacheState.padEnd(18)} ${counts.remapped} remapped, `
    + `${counts.invalid} invalid, ${counts.unchanged} unchanged, of ${counts.ids}`;
  if (cacheState === 'clean') console.log(cacheLine);
  else console.warn(cacheLine);

  const [keyState, keyCounts] = stableKeyAudit(records);
  const keyLine = `keys       ${keyState.padEnd(18)} ${keyCounts.slack_only} of `
    + `${keyCounts.records} record(s) carry only a Slack id`;
  if (keyState === 'all-stable') console.log(keyLine);
  else console.warn(keyLine);

  const findings = [];
  if (counts.remapped) {
    findings.push(`re-resolve the ${counts.remapped} remapped id(s) from the `
      + 'user_id_map before any of them is used again; a remapped id is a row '
      + 'pointing at nothing');
  }
  if (counts.invalid) {
    findings.push(`${counts.invalid} id(s) came back in invalid_user_ids; `
      + 're-enumerate the workspace and match those records on a key of your own');
  }
  if (keyCounts.slack_only) {
    findings.push(`${keyCounts.slack_only} record(s) carry no stable key of your own; `
      + 'store an email address or your own id alongside the Slack id so the next '
      + 'remap is a lookup rather than a loss');
  }
  if (!findings.length) {
    console.log('verdict    clean              nothing cached has been superseded');
    return;
  }
  console.warn(`verdict    ${findings.length} finding(s)`);
  for (const line of findings) console.warn(`  repair: ${line}`);
  process.exitCode = 1;
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main().
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixture worth reading is the <code>user_id_map</code>, because it is shaped exactly like the one in the method's own reference page: several workspace ids mapping to organization ids, and one id that maps to itself. That last entry is the trap the tests exist to hold: an id which maps to itself is genuinely unchanged, whereas an id which does not appear in the map at all is unresolved, and the two must never collapse into one state.",
"test_py_file": "test_slack_id_remap_audit.py",
"test_py": '''from slack_id_remap_audit import (
    MAX_USERS_PER_REQUEST, cache_verdict, chunk_users, exchange_availability, id_shape,
    remap_verdict, stable_key_audit,
)

# Shaped like the example on the method's own reference page: workspace ids
# mapping to organization ids, and one id that is already its own.
ID_MAP = {"U06UBSUN5": "W06M56XJM", "U06UEB62U": "W06PTT6GH",
          "W06UAZ65Q": "W06UAZ65Q"}
INVALID = ["U21ABZZXX"]


def test_a_workspace_local_id_is_the_kind_that_gets_superseded():
    state, detail = id_shape("U06UBSUN5")
    assert state == "workspace-local"
    assert "supersedes" in detail


def test_an_organization_level_id_is_recognised():
    assert id_shape("W06M56XJM")[0] == "org-global"


def test_a_bot_id_is_not_a_person():
    assert id_shape("B01BOT")[0] == "bot"


def test_an_empty_id_is_absent_rather_than_unrecognised():
    assert id_shape("")[0] == "absent"


def test_an_unfamiliar_shape_is_reported_not_assumed():
    assert id_shape("X99")[0] == "unrecognised"


def test_a_successful_exchange_is_available():
    assert exchange_availability({"ok": True, "user_id_map": {}})[0] == "available"


def test_a_workspace_outside_an_organization_has_nothing_to_exchange():
    state, detail = exchange_availability({"ok": False,
                                           "error": "not_enterprise_team"})
    assert state == "not-an-enterprise"
    assert "not part of an organization" in detail


def test_the_scope_the_method_needs_is_named():
    state, detail = exchange_availability({"ok": False, "error": "missing_scope"})
    assert state == "scope-missing"
    assert "tokens.basic" in detail


def test_an_answer_taken_during_the_window_is_refused():
    for error in ("team_added_to_org", "org_login_required"):
        state, detail = exchange_availability({"ok": False, "error": error})
        assert state == "migration-in-progress"
        assert "unreliable" in detail


def test_the_documented_batch_limit_is_named_in_the_error():
    state, detail = exchange_availability({"ok": False, "error": "too_many_users"})
    assert state == "batch-too-large"
    assert str(MAX_USERS_PER_REQUEST) in detail


def test_a_rate_limit_establishes_nothing():
    assert exchange_availability({"ok": False, "error": "ratelimited"})[0] == \\
        "transient"


def test_an_empty_body_is_unassessable():
    assert exchange_availability({})[0] == "unassessable"


def test_a_small_cache_is_one_request():
    assert chunk_users(["U1", "U2", "U3"]) == [["U1", "U2", "U3"]]


def test_the_batch_size_is_the_documented_maximum():
    batches = chunk_users(["U%d" % i for i in range(1174)])
    assert len(batches) == 3
    assert len(batches[0]) == MAX_USERS_PER_REQUEST
    assert len(batches[-1]) == 1174 - 2 * MAX_USERS_PER_REQUEST


def test_an_oversized_request_is_clamped_rather_than_trusted():
    batches = chunk_users(["U%d" % i for i in range(500)], size=5000)
    assert len(batches[0]) == MAX_USERS_PER_REQUEST


def test_blank_ids_are_dropped_before_batching():
    assert chunk_users(["U1", "  ", "", "U2"]) == [["U1", "U2"]]


def test_no_ids_is_no_requests():
    assert chunk_users([]) == []


def test_a_remapped_id_names_both_halves():
    state, detail = remap_verdict("U06UBSUN5", ID_MAP, INVALID)
    assert state == "remapped"
    assert "W06M56XJM" in detail
    assert "points at nothing" in detail


def test_an_id_that_maps_to_itself_is_unchanged():
    state, detail = remap_verdict("W06UAZ65Q", ID_MAP, INVALID)
    assert state == "unchanged"
    assert "nothing keyed on it moved" in detail


def test_an_id_in_the_invalid_list_is_not_recognised_at_all():
    state, detail = remap_verdict("U21ABZZXX", ID_MAP, INVALID)
    assert state == "invalid"
    assert "invalid_user_ids" in detail


def test_an_id_in_neither_list_is_unresolved_and_never_called_unchanged():
    state, detail = remap_verdict("U00MISSING", ID_MAP, INVALID)
    assert state == "not-returned"
    assert "rather than as unchanged" in detail


def test_an_empty_id_is_absent():
    assert remap_verdict("", ID_MAP, INVALID)[0] == "absent"


def test_a_cache_with_any_remap_is_stale():
    state, counts = cache_verdict(["remapped", "unchanged", "unchanged"])
    assert state == "stale-ids"
    assert counts["remapped"] == 1


def test_invalid_ids_alone_are_their_own_state():
    assert cache_verdict(["invalid", "unchanged"])[0] == "unrecognised-ids"


def test_unresolved_ids_alone_mean_the_check_is_incomplete():
    state, counts = cache_verdict(["not-returned", "unchanged"])
    assert state == "partially-assessed"
    assert counts["unresolved"] == 1


def test_a_cache_where_nothing_moved_is_clean():
    assert cache_verdict(["unchanged", "unchanged"])[0] == "clean"


def test_checking_no_ids_says_so():
    assert cache_verdict([])[0] == "nothing-checked"


def test_a_record_with_an_email_survives_a_remap():
    state, counts = stable_key_audit([{"slack_user_id": "U1",
                                       "email": "ada@example.com"}])
    assert state == "all-stable"
    assert counts["stable"] == 1


def test_a_record_with_only_a_slack_id_is_the_finding():
    state, counts = stable_key_audit([{"slack_user_id": "U1"}])
    assert state == "slack-id-only"
    assert counts["slack_only"] == 1


def test_a_mixed_cache_is_counted_rather_than_rounded():
    state, counts = stable_key_audit([{"slack_user_id": "U1", "local_id": "42"},
                                      {"slack_user_id": "U2"}])
    assert state == "some-stable"
    assert counts["stable"] == 1
    assert counts["slack_only"] == 1


def test_a_blank_stable_key_does_not_count_as_one():
    assert stable_key_audit([{"slack_user_id": "U1", "email": "   "}])[0] == \\
        "slack-id-only"


def test_no_records_at_all_says_so():
    assert stable_key_audit([])[0] == "nothing-checked"
''',
"test_js_file": "slack-id-remap-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  MAX_USERS_PER_REQUEST, cacheVerdict, chunkUsers, exchangeAvailability, idShape,
  remapVerdict, stableKeyAudit,
} from './slack-id-remap-audit.mjs';

// Shaped like the example on the method's own reference page.
const ID_MAP = {
  U06UBSUN5: 'W06M56XJM', U06UEB62U: 'W06PTT6GH', W06UAZ65Q: 'W06UAZ65Q',
};
const INVALID = ['U21ABZZXX'];

test('a workspace local id is the kind that gets superseded', () => {
  const [state, detail] = idShape('U06UBSUN5');
  assert.equal(state, 'workspace-local');
  assert.match(detail, /supersedes/);
});

test('an organization level id is recognised', () => {
  assert.equal(idShape('W06M56XJM')[0], 'org-global');
});

test('a bot id is not a person', () => {
  assert.equal(idShape('B01BOT')[0], 'bot');
});

test('an empty id is absent rather than unrecognised', () => {
  assert.equal(idShape('')[0], 'absent');
});

test('an unfamiliar shape is reported not assumed', () => {
  assert.equal(idShape('X99')[0], 'unrecognised');
});

test('a successful exchange is available', () => {
  assert.equal(exchangeAvailability({ ok: true, user_id_map: {} })[0], 'available');
});

test('a workspace outside an organization has nothing to exchange', () => {
  const [state, detail] = exchangeAvailability({
    ok: false, error: 'not_enterprise_team',
  });
  assert.equal(state, 'not-an-enterprise');
  assert.match(detail, /not part of an organization/);
});

test('the scope the method needs is named', () => {
  const [state, detail] = exchangeAvailability({ ok: false, error: 'missing_scope' });
  assert.equal(state, 'scope-missing');
  assert.match(detail, /tokens.basic/);
});

test('an answer taken during the window is refused', () => {
  for (const error of ['team_added_to_org', 'org_login_required']) {
    const [state, detail] = exchangeAvailability({ ok: false, error });
    assert.equal(state, 'migration-in-progress');
    assert.match(detail, /unreliable/);
  }
});

test('the documented batch limit is named in the error', () => {
  const [state, detail] = exchangeAvailability({ ok: false, error: 'too_many_users' });
  assert.equal(state, 'batch-too-large');
  assert.equal(detail.includes(String(MAX_USERS_PER_REQUEST)), true);
});

test('a rate limit establishes nothing', () => {
  assert.equal(exchangeAvailability({ ok: false, error: 'ratelimited' })[0],
    'transient');
});

test('an empty body is unassessable', () => {
  assert.equal(exchangeAvailability({})[0], 'unassessable');
});

test('a small cache is one request', () => {
  assert.deepEqual(chunkUsers(['U1', 'U2', 'U3']), [['U1', 'U2', 'U3']]);
});

test('the batch size is the documented maximum', () => {
  const ids = Array.from({ length: 1174 }, (_, i) => `U${i}`);
  const batches = chunkUsers(ids);
  assert.equal(batches.length, 3);
  assert.equal(batches[0].length, MAX_USERS_PER_REQUEST);
  assert.equal(batches[batches.length - 1].length,
    1174 - 2 * MAX_USERS_PER_REQUEST);
});

test('an oversized request is clamped rather than trusted', () => {
  const ids = Array.from({ length: 500 }, (_, i) => `U${i}`);
  assert.equal(chunkUsers(ids, 5000)[0].length, MAX_USERS_PER_REQUEST);
});

test('blank ids are dropped before batching', () => {
  assert.deepEqual(chunkUsers(['U1', '  ', '', 'U2']), [['U1', 'U2']]);
});

test('no ids is no requests', () => {
  assert.deepEqual(chunkUsers([]), []);
});

test('a remapped id names both halves', () => {
  const [state, detail] = remapVerdict('U06UBSUN5', ID_MAP, INVALID);
  assert.equal(state, 'remapped');
  assert.match(detail, /W06M56XJM/);
  assert.match(detail, /points at nothing/);
});

test('an id that maps to itself is unchanged', () => {
  const [state, detail] = remapVerdict('W06UAZ65Q', ID_MAP, INVALID);
  assert.equal(state, 'unchanged');
  assert.match(detail, /nothing keyed on it moved/);
});

test('an id in the invalid list is not recognised at all', () => {
  const [state, detail] = remapVerdict('U21ABZZXX', ID_MAP, INVALID);
  assert.equal(state, 'invalid');
  assert.match(detail, /invalid_user_ids/);
});

test('an id in neither list is unresolved and never called unchanged', () => {
  const [state, detail] = remapVerdict('U00MISSING', ID_MAP, INVALID);
  assert.equal(state, 'not-returned');
  assert.match(detail, /rather than as unchanged/);
});

test('an empty id is absent', () => {
  assert.equal(remapVerdict('', ID_MAP, INVALID)[0], 'absent');
});

test('a cache with any remap is stale', () => {
  const [state, counts] = cacheVerdict(['remapped', 'unchanged', 'unchanged']);
  assert.equal(state, 'stale-ids');
  assert.equal(counts.remapped, 1);
});

test('invalid ids alone are their own state', () => {
  assert.equal(cacheVerdict(['invalid', 'unchanged'])[0], 'unrecognised-ids');
});

test('unresolved ids alone mean the check is incomplete', () => {
  const [state, counts] = cacheVerdict(['not-returned', 'unchanged']);
  assert.equal(state, 'partially-assessed');
  assert.equal(counts.unresolved, 1);
});

test('a cache where nothing moved is clean', () => {
  assert.equal(cacheVerdict(['unchanged', 'unchanged'])[0], 'clean');
});

test('checking no ids says so', () => {
  assert.equal(cacheVerdict([])[0], 'nothing-checked');
});

test('a record with an email survives a remap', () => {
  const [state, counts] = stableKeyAudit([{
    slack_user_id: 'U1', email: 'ada@example.com',
  }]);
  assert.equal(state, 'all-stable');
  assert.equal(counts.stable, 1);
});

test('a record with only a slack id is the finding', () => {
  const [state, counts] = stableKeyAudit([{ slack_user_id: 'U1' }]);
  assert.equal(state, 'slack-id-only');
  assert.equal(counts.slack_only, 1);
});

test('a mixed cache is counted rather than rounded', () => {
  const [state, counts] = stableKeyAudit([{ slack_user_id: 'U1', local_id: '42' },
    { slack_user_id: 'U2' }]);
  assert.equal(state, 'some-stable');
  assert.equal(counts.stable, 1);
  assert.equal(counts.slack_only, 1);
});

test('a blank stable key does not count as one', () => {
  assert.equal(stableKeyAudit([{ slack_user_id: 'U1', email: '   ' }])[0],
    'slack-id-only');
});

test('no records at all says so', () => {
  assert.equal(stableKeyAudit([])[0], 'nothing-checked');
});
''',
"faq": [
 ("What is the difference between team_added_to_org and org_login_required?",
  "They arrive from the same event and their documented wording differs in one word that matters. team_added_to_org says platform operations will be intermittently unavailable during the transition; org_login_required says the workspace will not be available until the migration completes. Intermittent means some calls succeed, so a single health check is unreliable and a retry can hide the condition entirely. The scheduling response to both is the same and has its own note; what is specific to this one is what the migration leaves behind, which is a set of renumbered user identifiers."),
 ("Our user ids still start with U after the migration. Have they changed or not?",
  "Both are possible and only migration.exchange can tell you. A workspace inside an organization has organization-level ids beginning with W, and the mapping is what the method returns: an id that maps to itself has not moved, an id that maps to a different one has. The shape of the id is not sufficient evidence, which is why the script asks rather than inferring. Passing to_old converts in the other direction if you need the workspace-local id back for something that still expects it."),
 ("An id came back in neither the map nor invalid_user_ids. What does that mean?",
  "It means the method did not account for it, and the honest answer is that you do not know. The script reports it as not-returned and counts it separately rather than filing it as unchanged, because filing it as unchanged is how a cache audit comes back clean while leaving rows unaccounted for. Re-run the batch it was in, and if it is still unaccounted for, treat that record as needing re-resolution from a key of your own."),
 ("Do we need to check channel ids too?",
  "Yes, and this script does not do it, which is a limit worth stating rather than hiding. migration.exchange maps user ids and nothing else. For conversations the answer is to re-enumerate with conversations.list after the window closes and match on name or on your own stored key, accepting that a name is not a stable identifier either. The general rule after a migration is that any Slack identifier you cached for that workspace is a hypothesis until you have re-resolved it."),
 ("How do we make the next migration a non-event?",
  "Store a key of your own next to every Slack id, today, before anything migrates. An email address is usually enough, an internal person id is better, and either one turns a remap from a data-loss event into a lookup: re-enumerate the workspace, match on the stable key, write the new Slack id. The script counts the records that have no such key even on a workspace that is not in an organization, because that count is the whole of your exposure and it is knowable long before it matters."),
],
"related": [
 ("/slack/org-login-required/", "the scheduling half: what to do while the workspace is dark"),
 ("/slack/channel-renamed-hardcoded/", "the same lesson about identifiers, one object over"),
 ("/slack/enterprise-id-not-stored/", "the installation row that also needs re-keying afterwards"),
],
"citations": [CITE_MIGRATION_EXCHANGE, CITE_CONVERSATIONS_HISTORY, CITE_USERS_INFO, CITE_GRID_DEV],
})
