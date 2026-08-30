#!/usr/bin/env python3
"""/github/ field notes, batch V — the writing.

Four notes about the state of a repository rather than the state of a
credential. The section already publishes a shelf of token notes, and the risk
with a permissions batch is that it becomes a fifth way of saying "your token is
too narrow". None of these four is that. In three of them the credential is
correct and unchanged throughout, and in the fourth the credential is absent on
purpose.

The first owns a ceiling that no scope can lift. Scopes bound what a token may
do on the account's behalf; they cannot grant access the account itself does not
have, so a token holding `repo` against an account holding read on that one
repository is powerless there, and every instinct after the refusal points at
the token. The permissions object arrives on an ordinary repository read and
names the role outright, which means the refusal can be predicted rather than
provoked. The script never merges anything, never labels anything, and never
asks the API to refuse it: it reads the role and compares it against a table.

The second owns a genuinely confusing distinction. A 403 usually means a grant
is missing, and on these endpoints it can instead mean the feature is switched
off for that repository, which no grant will ever open. Worse, the same off
switch answers with three different status codes depending on which family of
endpoint you touched: 403 for code scanning, 404 for secret scanning, 410 for
issues. One repository read carries every flag, so the whole matrix is settled
before an alert endpoint is called even once, and the third state is stated
honestly because the security block is only returned to a caller with admin.

The third owns a bug where nothing fails. A fork is a separate repository with
its own issues, its own releases and its own branches, so an integration pointed
at one answers every call with a 200 and is wrong about all of them. There is no
error to catch and no status code to sort, which is why this note compares two
repositories instead of classifying one response, and why it checks the stored
id as well as the name.

The fourth owns a transition. The section already publishes the multi-cause 404
triage, and this is not that: it is the narrower case where a caller that read a
repository successfully for years starts getting 404 because the repository
became private. That is provable from a pair of readings the triage note never
takes, the same URL fetched with a token and with none, and the pair separates
went-private from deleted in a way that neither half can.

Nothing here writes. Several of these notes are about a write being refused, and
that is exactly the situation in which a read-only tool has to establish its
finding from readable state: the permission object, the feature flags, the fork
pointers, the visibility field. Every script GETs, prints its read cost before
it spends it, and prints the repair for a human to run.
"""

CITE_REPOS = ("Repositories — GitHub REST API",
              "https://docs.github.com/en/rest/repos/repos")
CITE_COLLABORATORS = ("Collaborators — GitHub REST API",
                      "https://docs.github.com/en/rest/collaborators/collaborators")
CITE_REPO_ROLES = ("Repository roles for an organization — GitHub Docs",
                   "https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-outside-collaborators/repository-roles-for-an-organization")
CITE_PERSONAL_REPO_PERMS = ("Permission levels for a personal account repository — GitHub Docs",
                            "https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-user-account-settings/permission-levels-for-a-personal-account-repository")
CITE_SCOPES = ("Scopes for OAuth apps — GitHub Docs",
               "https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps")
CITE_SECRET_SCANNING = ("Secret scanning — GitHub REST API",
                        "https://docs.github.com/en/rest/secret-scanning/secret-scanning")
CITE_CODE_SCANNING = ("Code scanning — GitHub REST API",
                      "https://docs.github.com/en/rest/code-scanning/code-scanning")
CITE_DEPENDABOT_ALERTS = ("Dependabot alerts — GitHub REST API",
                          "https://docs.github.com/en/rest/dependabot/alerts")
CITE_SECURITY_SETTINGS = ("Configuring security features for your repository — GitHub Docs",
                          "https://docs.github.com/en/code-security/getting-started/securing-your-repository")
CITE_FORKS_ABOUT = ("About forks — GitHub Docs",
                    "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks")
CITE_FORKS_REST = ("Forks — GitHub REST API",
                   "https://docs.github.com/en/rest/repos/forks")
CITE_FORK_PERMISSIONS = ("About permissions and visibility of forks — GitHub Docs",
                         "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-permissions-and-visibility-of-forks")
CITE_VISIBILITY = ("Setting repository visibility — GitHub Docs",
                   "https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility")
CITE_ABOUT_REPOS = ("About repositories — GitHub Docs",
                    "https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories")
CITE_RATE_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")

GUIDES = [
{
"slug": "collaborator-permission-insufficient",
"title": "The scope is right, the account's role on the repo is read",
"description": "GET /repos carries a permissions object for the authenticated user. push: false explains every refused write, and widening the token's scopes cannot lift it.",
"h1": "The scope is right, the account's role on the repo is read",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github token repo scope still 403 write",
             "github collaborator permission read only api",
             "github repos permissions push false",
             "github repository role insufficient merge",
             "github collaborators permission endpoint role_name"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The bot has a token with the <code>repo</code> scope. It reads the repository, lists the pull requests, fetches the diff, and then the merge comes back <code>403</code>. Somebody checks the token, sees <code>repo</code> ticked, mints a wider one with <code>workflow</code> and <code>admin:org</code> on it for good measure, and gets the same 403 back in the same millisecond. The scopes were never the ceiling. The account those scopes act on behalf of is a collaborator with read on that repository, and no token minted by that account will ever be able to merge anything into it.",
"short_answer": """<p>A scope bounds what a token may do <em>on the account's behalf</em>. It cannot grant the account access it does not have. So a token carrying <code>repo</code> held by a user whose role on that repository is read is powerless there, and the fix is a role change made by somebody with admin, not a new token.</p>
<p>Read the role rather than deducing it from a refusal. <code>GET /repos/{owner}/{repo}</code> returns a <code>permissions</code> object describing the authenticated user's own access — <code>{"admin": false, "maintain": false, "push": false, "triage": false, "pull": true}</code> — and the highest flag that is <code>true</code> is the role. <code>push: false</code> explains every failed write in one line. For somebody else's access, <code>GET /repos/{owner}/{repo}/collaborators/{username}/permission</code> returns both a legacy <code>permission</code> string and an exact <code>role_name</code>; prefer <code>role_name</code>, because the legacy field collapses maintain into <code>write</code> and triage into <code>read</code>.</p>""",
"problem": """<p>What makes this one expensive is that every visible signal points at the credential. The failure is a 403, which is the status a missing scope produces. The token is the thing the engineer controls and the thing they just changed. The account's role lives in a settings page they may not be able to open, on a repository that may belong to another team, and it is not mentioned anywhere in the error.</p>
<p>So the loop runs: widen the scopes, mint a fresh token, try again, and get the identical refusal. Then somebody suspects the token type and tries a fine-grained one, which fails differently and adds a second mystery. Then somebody suspects the endpoint and reads the documentation for the merge API, which is correct and unhelpful. Meanwhile the same token is happily reading the repository, listing branches and fetching pull requests, which is taken as proof that access is fine.</p>
<p>The other thing that hides it is that read access is often invisible to the person holding it. Being able to see a private repository, clone it, open issues on it and comment feels like being on the team. On GitHub it is one role below the first role that can push, and the difference only shows up on the first write. A CI account added to twelve repositories with write and a thirteenth with read looks completely uniform until the thirteenth repository is the one being released.</p>""",
"why": """<p><strong>Two independent gates, and only one of them is on the token.</strong> A call succeeds when the credential is allowed to make it <em>and</em> the account behind the credential has enough access to the resource. Scopes and fine-grained permissions are the first gate. The repository role is the second. Widening the first cannot open the second, which is why the reminted token changed nothing, and it is also why an over-wide token can sit for months in a job that never noticed it was over-wide.</p>
<p><strong>The permissions object is the authenticated user's own access, not the repository's settings.</strong> That is the part people misread. It is not a description of the repository; it is a description of you on that repository, computed per request, and it arrives free on a call the integration is already making. Five booleans in a fixed hierarchy: <code>pull</code>, <code>triage</code>, <code>push</code>, <code>maintain</code>, <code>admin</code>. Every higher role implies the ones below it, so the finding is simply the highest <code>true</code>.</p>
<p><strong>The role that matters is the effective one.</strong> It is the union of a direct collaborator grant, every team the account belongs to, and the organization's base permission. That is a strength for diagnosis — the object already accounts for all three, so there is no arithmetic to get wrong — and a limit for repair, because the object reports the effect and never the source. Naming which team or which base permission produced a role needs organization-level reads that a repository-scoped token does not have. State that plainly rather than guessing; the repair is still correct, it just has more than one place to be applied.</p>
<p><strong>The legacy <code>permission</code> string lies by rounding.</strong> The collaborator permission endpoint returns <code>permission</code> with four possible values and <code>role_name</code> with the real one. A maintainer comes back as <code>write</code> and a triager comes back as <code>read</code>. If you are checking whether somebody can label an issue, the legacy field will tell you no about a triager who can. Read <code>role_name</code>, fall back to <code>permission</code> only when it is absent, and treat an unrecognised <code>role_name</code> as a custom organization role whose abilities the API does not enumerate.</p>
<p><strong>The refusal is predictable, so it should never be provoked.</strong> This is the whole reason the note exists in a read-only section. The role is readable in advance, the minimum role for each action is documented, and a comparison between the two is arithmetic. A tool that establishes "this account cannot merge" by attempting a merge has, in the successful case, merged something. Reading the role costs one request and answers for every action at once.</p>
<p><strong>A 403 whose cause is the role looks nothing like one whose cause is the token, once you have both readings.</strong> A missing classic scope arrives with <code>x-accepted-oauth-scopes</code> naming what would have worked, which is <a href="/github/missing-oauth-scope/">its own note</a>; a fine-grained token gets <a href="/github/resource-not-accessible-by-pat/">a message that names the token and no header describing it</a>. A role that is too low produces neither. It produces a plain refusal beside a <code>permissions</code> object that already said <code>push: false</code> before you called.</p>""",
"steps": [
 {"h": "Read the role off the call you are already making",
  "body": """<p>Point the script at the repository and it reads <code>GET /repos/{owner}/{repo}</code>, pulls the <code>permissions</code> object out and names the highest role that is <code>true</code>. One request, and it is the same request your integration makes to resolve the repository, so in practice this costs nothing you were not already spending.</p>"""},
 {"h": "Name the action instead of describing the symptom",
  "body": """<p>Pass <code>--action merge-pull-request</code>, or <code>label-issue</code>, or <code>push-branch</code>. The script holds the documented minimum role for each and compares. The output is a sentence rather than a table: this account holds read, merging a pull request needs write, so the call will be refused. It is the same answer the 403 gives, arrived at without asking for the 403.</p>"""},
 {"h": "Rule the token out loudly",
  "body": """<p>The script reads <code>x-oauth-scopes</code> off <code>GET /user</code> and prints the combination explicitly when it finds it: a token carrying <code>repo</code> against an account carrying read. That line exists to stop the next hour of work, because that is the exact shape that sends people to mint a wider credential. It also names the token type from its prefix, since a fine-grained token has no scopes to widen at all.</p>"""},
 {"h": "Ask about a specific account when it is not your own",
  "body": """<p>With <code>--user octobot</code> the script adds <code>GET /repos/{owner}/{repo}/collaborators/{username}/permission</code> and reports <code>role_name</code> rather than the legacy <code>permission</code> field, so a maintainer is not reported as a plain writer and a triager is not reported as a reader. An unrecognised <code>role_name</code> is reported as a custom organization role and left unpriced, because the API does not publish what a custom role can do.</p>"""},
 {"h": "Take the repair to the role, and to the right place",
  "body": """<p>The printed repair names the role to raise to and the smallest one that suffices, which is often lower than people assume — labelling and closing issues need triage, not write. It also says what it cannot tell you: whether the current role came from a direct grant, a team or the organization's base permission. Nothing is changed by the script. It prints and exits.</p>"""},
],
"verify": """<p>After the role is raised, the same read reports the new one and the action stops being a prediction of failure.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_repo_role.py octo-org/deploy-tools \\
    --action merge-pull-request
# read cost: 2 request(s) against the core hourly quota
# token: classic PAT, scopes=repo, workflow
# octo-org/deploy-tools: permissions={admin:false maintain:false push:false triage:false pull:true}
# role: read
# role-insufficient: this account holds 'read' and merge-pull-request needs
#   'write', which is 2 role(s) higher.
# scopes-are-not-the-ceiling: the token carries 'repo', which is as wide as a
#   classic token gets. Reminting it wider cannot change this answer.
# repair: have somebody with admin raise this account to 'write' on
#   octo-org/deploy-tools, or add it to a team that has it. The permissions
#   object reports the effective role and never its source, so the grant may
#   need making in a team or in the org's base permission.</code></pre>""",
"code_intro": "Almost all of this is a comparison between two strings, and the interesting part is that the comparison is enough. The role hierarchy is fixed and documented, every higher role implies the lower ones, and the minimum role for each action is a table. So the script reads one object, resolves it to a role, and answers for any action without touching the endpoint that would have refused it. The two live reads are the repository and the token's own identity; the third, only when you name somebody else, is the collaborator permission endpoint, which is read for <code>role_name</code> rather than for the legacy field that rounds two roles into their neighbours.",
"py_file": "github_repo_role.py",
"py": '''"""Read an account's role on one repository instead of provoking a 403.

Read only. GET requests and nothing else. This script is about writes being
refused and it never attempts one: the role is readable in advance on an
ordinary repository read, the minimum role for each action is documented, and
the comparison between them is arithmetic done locally. A tool that proved
"this account cannot merge" by attempting a merge would, in the case where it
was wrong, have merged something.

The point of the note: an OAuth scope bounds what a token may do on the
account's behalf and cannot grant the account access it does not have. A token
carrying `repo` held by an account whose role on that repository is read is
powerless there, and widening the token cannot change that.

What this can and cannot see: the permissions object is the effective role,
already accounting for a direct collaborator grant, every team the account is
in and the organization base permission. It never reports which of those
produced the role. Naming the source needs organization reads a repository
token does not have, so this script reports the effect and says so.

Environment:

    GITHUB_TOKEN    a token with read access to the repository
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_repo_role")

API = "https://api.github.com"
UA = "github-repo-role/1.0"

# Weakest first. Every role implies the ones below it, which is why resolving
# the permissions object is "highest flag that is true" and nothing more.
ROLES = ("none", "read", "triage", "write", "maintain", "admin")

# The booleans GitHub returns, paired with the role each one names. Ordered
# strongest first so the first hit is the answer.
PERMISSION_FLAGS = (
    ("admin", "admin"),
    ("maintain", "maintain"),
    ("push", "write"),
    ("triage", "triage"),
    ("pull", "read"),
)

# The legacy `permission` string on the collaborator endpoint has four values
# and rounds two roles into their neighbours: a maintainer reads as write, a
# triager reads as read. role_name carries the real one.
LEGACY_ROUNDING = {
    "admin": "admin",
    "write": "write",
    "read": "read",
    "none": "none",
}

# Minimum role for actions people actually get refused on. Kept short and
# documented rather than exhaustive: the value is in the four rows that
# surprise people, not in a transcription of the whole roles table.
ACTION_MINIMUM = {
    "read-code": "read",
    "clone": "read",
    "open-issue": "read",
    "comment": "read",
    "label-issue": "triage",
    "close-issue": "triage",
    "assign-issue": "triage",
    "request-review": "triage",
    "push-branch": "write",
    "merge-pull-request": "write",
    "create-release": "write",
    "dismiss-review": "write",
    "manage-repository-settings": "maintain",
    "manage-webhooks": "admin",
    "add-collaborator": "admin",
    "change-visibility": "admin",
}

# Longest prefixes first so a future prefix extending an existing one is not
# swallowed by its shorter neighbour.
TOKEN_PREFIXES = (
    ("github_pat_", "fine-grained PAT"),
    ("ghp_", "classic PAT"),
    ("gho_", "OAuth user token"),
    ("ghu_", "App user-to-server token"),
    ("ghs_", "App installation token"),
    ("ghr_", "App refresh token"),
)

# The widest a classic token gets on repositories. Holding it and still being
# refused is the shape this note exists to interrupt.
WIDEST_CLASSIC_REPO_SCOPE = "repo"


def read_cost(with_user=False):
    """Requests this run will spend against the core quota. Pure."""
    return 3 if with_user else 2


def token_kind(token):
    """Name the credential from its prefix. Pure; nothing leaves the machine."""
    value = (token or "").strip()
    for prefix, name in TOKEN_PREFIXES:
        if value.startswith(prefix):
            return name
    return "unknown"


def scope_list(header_value):
    """Read x-oauth-scopes into a list, keeping absent and empty apart. Pure.

    A classic token with nothing ticked sends the header with an empty value; a
    fine-grained token or an App token does not send it at all. Collapsing both
    to [] would lose the signal that decides whether "widen the scopes" is even
    a sentence that applies.
    """
    if header_value is None:
        return None
    return [s.strip() for s in header_value.split(",") if s.strip()]


def role_rank(role):
    """Position in the hierarchy, or -1 for something unrecognised. Pure."""
    try:
        return ROLES.index(str(role or "none").strip().lower())
    except ValueError:
        return -1


def role_from_permissions(permissions):
    """The role a permissions object describes. Pure.

    Highest true flag wins. An empty or missing object is "unreported" rather
    than "none": an unauthenticated read returns no permissions object at all,
    and reporting that as no access would be a different and wrong finding.
    """
    if not isinstance(permissions, dict) or not permissions:
        return "unreported"
    for flag, role in PERMISSION_FLAGS:
        if permissions.get(flag) is True:
            return role
    return "none"


def role_from_collaborator(payload):
    """Resolve the collaborator permission endpoint. Pure.

    Returns (role, exact, note). role_name is preferred because the legacy
    `permission` field rounds maintain down to write and triage down to read.
    An unrecognised role_name is a custom organization role: named, not priced,
    because the API does not publish what a custom role can do.
    """
    if not isinstance(payload, dict):
        return ("unreported", False, "no collaborator permission payload was read.")
    name = str(payload.get("role_name") or "").strip().lower()
    legacy = str(payload.get("permission") or "").strip().lower()
    if name and role_rank(name) >= 0:
        return (name, True, "role_name reported the exact role.")
    if name:
        return ("custom:" + name, False,
                "role_name is '%s', a custom organization role. Its abilities "
                "are defined by the organization and are not published through "
                "this API, so nothing here prices it." % name)
    if legacy in LEGACY_ROUNDING:
        return (LEGACY_ROUNDING[legacy], False,
                "only the legacy permission field was present. It rounds "
                "maintain to write and triage to read, so a maintainer and a "
                "triager are both misreported by it.")
    return ("unreported", False, "neither role_name nor permission was present.")


def can(role, action):
    """Does this role reach the documented minimum for this action. Pure."""
    needed = ACTION_MINIMUM.get(str(action or "").strip().lower())
    if needed is None:
        return None
    held = role_rank(role)
    if held < 0:
        return None
    return held >= role_rank(needed)


def deficit(role, action):
    """How many roles short this account is for this action. Pure.

    0 means it is sufficient. None means the question could not be asked, which
    happens for a custom role or an unknown action and is not the same as no.
    """
    needed = ACTION_MINIMUM.get(str(action or "").strip().lower())
    held = role_rank(role)
    if needed is None or held < 0:
        return None
    return max(0, role_rank(needed) - held)


def blocked_actions(role):
    """Every documented action this role cannot perform. Pure."""
    held = role_rank(role)
    if held < 0:
        return []
    return sorted(a for a, need in ACTION_MINIMUM.items() if held < role_rank(need))


def scopes_are_the_ceiling(role, scopes, kind, action):
    """Is widening the credential capable of changing the answer. Pure.

    Returns (state, detail). This is the question the reader is actually asking
    and it deserves an explicit answer rather than an inference, because the
    default guess is yes and the default guess is wrong.
    """
    short = deficit(role, action)
    if short is None or short == 0:
        return ("not-the-question",
                "the role is sufficient for this action, so the credential is "
                "the next thing to look at rather than the first.")
    if scopes is None:
        return ("no-scopes-to-widen",
                "this credential is a %s and carries no OAuth scopes at all, so "
                "there is nothing to widen. Its per-resource permissions are a "
                "separate gate and neither gate raises a repository role."
                % kind)
    if WIDEST_CLASSIC_REPO_SCOPE in scopes:
        return ("scopes-are-not-the-ceiling",
                "the token carries '%s', which is as wide as a classic token "
                "gets on repositories. Reminting it wider cannot change this "
                "answer." % WIDEST_CLASSIC_REPO_SCOPE)
    return ("two-gates-open",
            "the token holds %s and not '%s', so the scope is worth fixing too. "
            "Fixing it alone will not help: the role is short as well, and both "
            "gates have to open."
            % (", ".join(scopes) or "no scopes at all", WIDEST_CLASSIC_REPO_SCOPE))


def verdict(role, action):
    """Classify one account's role against one action. Pure. (state, detail)."""
    if str(role).startswith("custom:"):
        return ("custom-role",
                "the role is a custom organization role, which this script "
                "names and does not price. Ask an organization owner what it "
                "grants, or compare against the base role it was built from.")
    if role == "unreported":
        return ("role-unreported",
                "no permissions object came back. An unauthenticated read never "
                "carries one, so authenticate before reading anything into this.")
    if role == "none":
        return ("no-access",
                "the account has no role on this repository at all. Reads of a "
                "private repository will 404 rather than 403, which is a "
                "different symptom with the same cause.")
    short = deficit(role, action)
    if short is None:
        return ("action-unknown",
                "no documented minimum role is held here for that action, so "
                "the role is reported and the comparison is left to you.")
    if short == 0:
        return ("role-sufficient",
                "this account holds '%s' and %s needs '%s', so the role is not "
                "what refused the call."
                % (role, action, ACTION_MINIMUM[action]))
    return ("role-insufficient",
            "this account holds '%s' and %s needs '%s', which is %d role(s) "
            "higher." % (role, action, ACTION_MINIMUM[action], short))


def repair(state, role, action, subject="this account"):
    """The sentence a reader has to act on. Pure."""
    if state == "role-insufficient":
        return ("have somebody with admin raise %s to '%s' on this repository, "
                "or add it to a team that has it. The permissions object "
                "reports the effective role and never its source, so the grant "
                "may need making in a team or in the org's base permission."
                % (subject, ACTION_MINIMUM[action]))
    if state == "no-access":
        return ("grant %s a role on the repository. Until then the repository "
                "is invisible rather than forbidden if it is private." % subject)
    if state == "role-sufficient":
        return ("nothing on the role. Read the refusal's headers next: a "
                "classic token names what it accepts in x-accepted-oauth-scopes "
                "and a fine-grained one names nothing at all.")
    if state == "custom-role":
        return ("ask an organization owner which base role this custom role was "
                "built from, then compare that against the action.")
    if state == "role-unreported":
        return ("authenticate the read. The permissions object only arrives on "
                "an authenticated request.")
    return ("name an action with --action to turn the role into a verdict. "
            "The role itself is already reported above.")


def get(session, path):
    """One GET. Returns the response object."""
    r = session.get(API + path, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", help="owner/name of the repository")
    ap.add_argument("--action", default="merge-pull-request",
                    help="the action being refused, e.g. merge-pull-request, "
                         "label-issue, push-branch")
    ap.add_argument("--user",
                    help="report this account's role instead of the token's own")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2
    if "/" not in args.repo:
        log.error("repo should be owner/name")
        return 2

    log.info("read cost: %d request(s) against the core hourly quota",
             read_cost(bool(args.user)))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    kind = token_kind(token)
    me = get(session, "/user")
    scopes = scope_list(me.headers.get("x-oauth-scopes"))
    log.info("token: %s, scopes=%s", kind,
             "none" if scopes is None else (", ".join(scopes) or "empty"))

    repo_response = get(session, "/repos/" + args.repo)
    if repo_response.status_code != 200:
        log.error("%s: HTTP %s reading the repository. A 404 here is its own "
                  "note; this one starts from a repository you can read.",
                  args.repo, repo_response.status_code)
        return 2
    repo = repo_response.json()
    permissions = repo.get("permissions") or {}
    role = role_from_permissions(permissions)
    subject = "this account"
    note = None

    if args.user:
        collab = get(session, "/repos/%s/collaborators/%s/permission"
                     % (args.repo, args.user))
        if collab.status_code == 200:
            role, _exact, note = role_from_collaborator(collab.json())
            subject = args.user
        else:
            log.warning("collaborator permission read returned HTTP %s; "
                        "reporting the token's own role instead",
                        collab.status_code)

    log.info("%s: permissions=%s", args.repo, json.dumps(permissions))
    log.info("role: %s", role)
    if note:
        log.info("role source: %s", note)

    state, detail = verdict(role, args.action)
    log.info("%s: %s", state, detail)
    ceiling_state, ceiling_detail = scopes_are_the_ceiling(
        role, scopes, kind, args.action)
    log.info("%s: %s", ceiling_state, ceiling_detail)
    log.info("repair: %s", repair(state, role, args.action, subject))

    blocked = blocked_actions(role)
    if blocked:
        log.info("also blocked at this role: %s", ", ".join(blocked))

    print(json.dumps({
        "repository": args.repo,
        "subject": subject,
        "token_kind": kind,
        "scopes": scopes,
        "permissions": permissions,
        "role": role,
        "action": args.action,
        "minimum_role": ACTION_MINIMUM.get(args.action),
        "roles_short": deficit(role, args.action),
        "state": state,
        "detail": detail,
        "credential_state": ceiling_state,
        "credential_detail": ceiling_detail,
        "blocked_actions": blocked,
        "repair": repair(state, role, args.action, subject),
    }, indent=2, default=str))
    return 1 if state in ("role-insufficient", "no-access") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-repo-role.mjs",
"js": '''/**
 * Read an account's role on one repository instead of provoking a 403.
 *
 * Read only. GET requests and nothing else. The note is about writes being
 * refused and this script never attempts one: the role arrives on an ordinary
 * repository read, the minimum role for each action is documented, and the
 * comparison between them happens locally.
 *
 * A scope bounds what a token may do on the account's behalf and cannot grant
 * the account access it does not have, so a token carrying `repo` held by an
 * account with read on that repository is powerless there.
 *
 * Environment:
 *   GITHUB_TOKEN    a token with read access to the repository
 *   GITHUB_REPO     owner/name
 *   GITHUB_ACTION   the action being refused, default merge-pull-request
 *   GITHUB_USER     report this account's role instead of the token's own
 */
const API = 'https://api.github.com';
const UA = 'github-repo-role/1.0';

/** Weakest first. Every role implies the ones below it. */
export const ROLES = ['none', 'read', 'triage', 'write', 'maintain', 'admin'];

/** The booleans GitHub returns, strongest first, so the first hit is the role. */
export const PERMISSION_FLAGS = [
  ['admin', 'admin'],
  ['maintain', 'maintain'],
  ['push', 'write'],
  ['triage', 'triage'],
  ['pull', 'read'],
];

/** The legacy permission string rounds maintain to write and triage to read. */
export const LEGACY_ROUNDING = {
  admin: 'admin', write: 'write', read: 'read', none: 'none',
};

/** Minimum role for the actions people actually get refused on. */
export const ACTION_MINIMUM = {
  'read-code': 'read',
  clone: 'read',
  'open-issue': 'read',
  comment: 'read',
  'label-issue': 'triage',
  'close-issue': 'triage',
  'assign-issue': 'triage',
  'request-review': 'triage',
  'push-branch': 'write',
  'merge-pull-request': 'write',
  'create-release': 'write',
  'dismiss-review': 'write',
  'manage-repository-settings': 'maintain',
  'manage-webhooks': 'admin',
  'add-collaborator': 'admin',
  'change-visibility': 'admin',
};

/** Longest prefixes first. */
export const TOKEN_PREFIXES = [
  ['github_pat_', 'fine-grained PAT'],
  ['ghp_', 'classic PAT'],
  ['gho_', 'OAuth user token'],
  ['ghu_', 'App user-to-server token'],
  ['ghs_', 'App installation token'],
  ['ghr_', 'App refresh token'],
];

/** The widest a classic token gets on repositories. */
export const WIDEST_CLASSIC_REPO_SCOPE = 'repo';

/** Requests this run will spend against the core quota. Pure. */
export function readCost(withUser = false) {
  return withUser ? 3 : 2;
}

/** Name the credential from its prefix. Pure. */
export function tokenKind(token) {
  const value = String(token ?? '').trim();
  for (const [prefix, name] of TOKEN_PREFIXES) {
    if (value.startsWith(prefix)) return name;
  }
  return 'unknown';
}

/** Read x-oauth-scopes into a list, keeping absent and empty apart. Pure. */
export function scopeList(headerValue) {
  if (headerValue === null || headerValue === undefined) return null;
  return String(headerValue).split(',').map((s) => s.trim()).filter(Boolean);
}

/** Position in the hierarchy, or -1 for something unrecognised. Pure. */
export function roleRank(role) {
  return ROLES.indexOf(String(role ?? 'none').trim().toLowerCase());
}

/** The role a permissions object describes. Pure. */
export function roleFromPermissions(permissions) {
  if (!permissions || typeof permissions !== 'object'
      || Object.keys(permissions).length === 0) {
    return 'unreported';
  }
  for (const [flag, role] of PERMISSION_FLAGS) {
    if (permissions[flag] === true) return role;
  }
  return 'none';
}

/** Resolve the collaborator permission endpoint. Pure. [role, exact, note]. */
export function roleFromCollaborator(payload) {
  if (!payload || typeof payload !== 'object') {
    return ['unreported', false, 'no collaborator permission payload was read.'];
  }
  const name = String(payload.role_name ?? '').trim().toLowerCase();
  const legacy = String(payload.permission ?? '').trim().toLowerCase();
  if (name && roleRank(name) >= 0) {
    return [name, true, 'role_name reported the exact role.'];
  }
  if (name) {
    return [`custom:${name}`, false, `role_name is '${name}', a custom `
      + 'organization role. Its abilities are defined by the organization and '
      + 'are not published through this API, so nothing here prices it.'];
  }
  if (Object.prototype.hasOwnProperty.call(LEGACY_ROUNDING, legacy)) {
    return [LEGACY_ROUNDING[legacy], false, 'only the legacy permission field '
      + 'was present. It rounds maintain to write and triage to read, so a '
      + 'maintainer and a triager are both misreported by it.'];
  }
  return ['unreported', false, 'neither role_name nor permission was present.'];
}

/** Does this role reach the documented minimum for this action. Pure. */
export function can(role, action) {
  const needed = ACTION_MINIMUM[String(action ?? '').trim().toLowerCase()];
  if (needed === undefined) return null;
  const held = roleRank(role);
  if (held < 0) return null;
  return held >= roleRank(needed);
}

/** How many roles short this account is. 0 is sufficient, null unanswerable. */
export function deficit(role, action) {
  const needed = ACTION_MINIMUM[String(action ?? '').trim().toLowerCase()];
  const held = roleRank(role);
  if (needed === undefined || held < 0) return null;
  return Math.max(0, roleRank(needed) - held);
}

/** Every documented action this role cannot perform. Pure. */
export function blockedActions(role) {
  const held = roleRank(role);
  if (held < 0) return [];
  return Object.keys(ACTION_MINIMUM)
    .filter((a) => held < roleRank(ACTION_MINIMUM[a]))
    .sort();
}

/** Is widening the credential capable of changing the answer. Pure. */
export function scopesAreTheCeiling(role, scopes, kind, action) {
  const short = deficit(role, action);
  if (short === null || short === 0) {
    return ['not-the-question', 'the role is sufficient for this action, so the '
      + 'credential is the next thing to look at rather than the first.'];
  }
  if (scopes === null || scopes === undefined) {
    return ['no-scopes-to-widen', `this credential is a ${kind} and carries no `
      + 'OAuth scopes at all, so there is nothing to widen. Its per-resource '
      + 'permissions are a separate gate and neither gate raises a repository role.'];
  }
  if (scopes.includes(WIDEST_CLASSIC_REPO_SCOPE)) {
    return ['scopes-are-not-the-ceiling', `the token carries `
      + `'${WIDEST_CLASSIC_REPO_SCOPE}', which is as wide as a classic token `
      + 'gets on repositories. Reminting it wider cannot change this answer.'];
  }
  return ['two-gates-open', `the token holds ${scopes.join(', ') || 'no scopes at all'} `
    + `and not '${WIDEST_CLASSIC_REPO_SCOPE}', so the scope is worth fixing too. `
    + 'Fixing it alone will not help: the role is short as well, and both gates '
    + 'have to open.'];
}

/** Classify one account's role against one action. Pure. [state, detail]. */
export function verdict(role, action) {
  if (String(role).startsWith('custom:')) {
    return ['custom-role', 'the role is a custom organization role, which this '
      + 'script names and does not price. Ask an organization owner what it '
      + 'grants, or compare against the base role it was built from.'];
  }
  if (role === 'unreported') {
    return ['role-unreported', 'no permissions object came back. An '
      + 'unauthenticated read never carries one, so authenticate before reading '
      + 'anything into this.'];
  }
  if (role === 'none') {
    return ['no-access', 'the account has no role on this repository at all. '
      + 'Reads of a private repository will 404 rather than 403, which is a '
      + 'different symptom with the same cause.'];
  }
  const short = deficit(role, action);
  if (short === null) {
    return ['action-unknown', 'no documented minimum role is held here for that '
      + 'action, so the role is reported and the comparison is left to you.'];
  }
  if (short === 0) {
    return ['role-sufficient', `this account holds '${role}' and ${action} needs `
      + `'${ACTION_MINIMUM[action]}', so the role is not what refused the call.`];
  }
  return ['role-insufficient', `this account holds '${role}' and ${action} needs `
    + `'${ACTION_MINIMUM[action]}', which is ${short} role(s) higher.`];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, role, action, subject = 'this account') {
  if (state === 'role-insufficient') {
    return `have somebody with admin raise ${subject} to '${ACTION_MINIMUM[action]}' `
      + 'on this repository, or add it to a team that has it. The permissions '
      + 'object reports the effective role and never its source, so the grant may '
      + "need making in a team or in the org's base permission.";
  }
  if (state === 'no-access') {
    return `grant ${subject} a role on the repository. Until then the repository `
      + 'is invisible rather than forbidden if it is private.';
  }
  if (state === 'role-sufficient') {
    return 'nothing on the role. Read the refusal\\'s headers next: a classic '
      + 'token names what it accepts in x-accepted-oauth-scopes and a '
      + 'fine-grained one names nothing at all.';
  }
  if (state === 'custom-role') {
    return 'ask an organization owner which base role this custom role was built '
      + 'from, then compare that against the action.';
  }
  if (state === 'role-unreported') {
    return 'authenticate the read. The permissions object only arrives on an '
      + 'authenticated request.';
  }
  return 'name an action to turn the role into a verdict. The role itself is '
    + 'already reported above.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repoName = process.env.GITHUB_REPO;
  if (!token || !repoName) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPO');
    process.exitCode = 2;
    return;
  }
  const action = process.env.GITHUB_ACTION || 'merge-pull-request';
  const user = process.env.GITHUB_USER || '';

  console.log(`read cost: ${readCost(Boolean(user))} request(s) against the core hourly quota`);

  const me = await fetch(`${API}/user`, { headers: headers(token) });
  const kind = tokenKind(token);
  const scopes = scopeList(me.headers.get('x-oauth-scopes'));
  console.log(`token: ${kind}, scopes=${scopes === null ? 'none' : (scopes.join(', ') || 'empty')}`);

  const res = await fetch(`${API}/repos/${repoName}`, { headers: headers(token) });
  if (res.status !== 200) {
    console.error(`${repoName}: HTTP ${res.status} reading the repository`);
    process.exitCode = 2;
    return;
  }
  const repo = await res.json();
  const permissions = repo.permissions || {};
  let role = roleFromPermissions(permissions);
  let subject = 'this account';

  if (user) {
    const collab = await fetch(
      `${API}/repos/${repoName}/collaborators/${user}/permission`,
      { headers: headers(token) },
    );
    if (collab.status === 200) {
      const [resolved, , note] = roleFromCollaborator(await collab.json());
      role = resolved;
      subject = user;
      console.log(`role source: ${note}`);
    }
  }

  console.log(`${repoName}: permissions=${JSON.stringify(permissions)}`);
  console.log(`role: ${role}`);
  const [state, detail] = verdict(role, action);
  console.log(`${state}: ${detail}`);
  const [ceilingState, ceilingDetail] = scopesAreTheCeiling(role, scopes, kind, action);
  console.log(`${ceilingState}: ${ceilingDetail}`);
  console.log(`repair: ${repair(state, role, action, subject)}`);

  console.log(JSON.stringify({
    repository: repoName,
    subject,
    token_kind: kind,
    scopes,
    permissions,
    role,
    action,
    minimum_role: ACTION_MINIMUM[action] ?? null,
    roles_short: deficit(role, action),
    state,
    detail,
    credential_state: ceilingState,
    blocked_actions: blockedActions(role),
    repair: repair(state, role, action, subject),
  }, null, 2));
  process.exitCode = ['role-insufficient', 'no-access'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The hierarchy is asserted first, because everything else is a comparison against it: the highest true flag is the role, an empty object is unreported rather than none, and an unauthenticated read is therefore never mistaken for an account with no access. Then the two rounding traps, both of which produce a wrong answer that looks right — the legacy <code>permission</code> field reporting a maintainer as a writer and a triager as a reader, and a custom organization role that must be named and left unpriced. The last group is the one the note exists for: a token holding <code>repo</code> beside an account holding read has to come back as scopes-are-not-the-ceiling, in those words, because that is the sentence that stops the next token from being minted.",
"test_py_file": "test_github_repo_role.py",
"test_py": '''from github_repo_role import (
    ACTION_MINIMUM, ROLES, blocked_actions, can, deficit, read_cost, repair,
    role_from_collaborator, role_from_permissions, role_rank, scope_list,
    scopes_are_the_ceiling, token_kind, verdict,
)

READ_ONLY = {"admin": False, "maintain": False, "push": False,
             "triage": False, "pull": True}
TRIAGE = {"admin": False, "maintain": False, "push": False,
          "triage": True, "pull": True}
WRITE = {"admin": False, "maintain": False, "push": True,
         "triage": True, "pull": True}
ADMIN = {"admin": True, "maintain": True, "push": True,
         "triage": True, "pull": True}


def test_the_hierarchy_runs_weakest_to_strongest():
    assert ROLES == ("none", "read", "triage", "write", "maintain", "admin")
    assert role_rank("read") < role_rank("triage") < role_rank("write")
    assert role_rank("write") < role_rank("maintain") < role_rank("admin")
    assert role_rank("nonsense") == -1


def test_the_role_is_the_highest_true_flag():
    assert role_from_permissions(READ_ONLY) == "read"
    assert role_from_permissions(TRIAGE) == "triage"
    assert role_from_permissions(WRITE) == "write"
    assert role_from_permissions(ADMIN) == "admin"


def test_an_absent_permissions_object_is_unreported_not_none():
    # An unauthenticated read carries no permissions object at all. Reporting
    # that as "no access" would be a different and wrong finding.
    assert role_from_permissions({}) == "unreported"
    assert role_from_permissions(None) == "unreported"
    assert role_from_permissions({"admin": False, "pull": False}) == "none"


def test_read_explains_every_refused_write_in_one_flag():
    assert READ_ONLY["push"] is False
    assert can("read", "merge-pull-request") is False
    assert can("read", "push-branch") is False
    assert can("read", "read-code") is True


def test_labelling_needs_triage_and_not_write():
    # The role people are told to ask for is usually higher than the one they
    # need, and this is the row that shows it.
    assert ACTION_MINIMUM["label-issue"] == "triage"
    assert can("triage", "label-issue") is True
    assert can("triage", "merge-pull-request") is False
    assert deficit("triage", "merge-pull-request") == 1


def test_the_deficit_counts_roles_not_booleans():
    assert deficit("read", "merge-pull-request") == 2
    assert deficit("read", "add-collaborator") == 4
    assert deficit("admin", "merge-pull-request") == 0
    assert deficit("read", "not-an-action") is None


def test_the_legacy_permission_field_rounds_two_roles_away():
    exact, is_exact, _ = role_from_collaborator(
        {"permission": "write", "role_name": "maintain"})
    assert (exact, is_exact) == ("maintain", True)
    rounded, is_exact, note = role_from_collaborator({"permission": "write"})
    assert rounded == "write" and is_exact is False
    assert "rounds maintain to write" in note
    # A triager comes back as read through the legacy field, which would deny a
    # label they can actually apply.
    assert role_from_collaborator({"permission": "read"})[0] == "read"
    assert role_from_collaborator({"role_name": "triage"})[0] == "triage"


def test_a_custom_org_role_is_named_and_not_priced():
    role, is_exact, note = role_from_collaborator(
        {"permission": "read", "role_name": "security-auditor"})
    assert role == "custom:security-auditor"
    assert is_exact is False and "custom organization role" in note
    state, detail = verdict(role, "merge-pull-request")
    assert state == "custom-role"
    assert "does not price" in detail or "not priced" in detail


def test_a_repo_scope_beside_a_read_role_is_the_headline():
    state, detail = scopes_are_the_ceiling(
        "read", ["repo", "workflow"], "classic PAT", "merge-pull-request")
    assert state == "scopes-are-not-the-ceiling"
    assert "cannot change this answer" in detail


def test_a_fine_grained_token_has_no_scopes_to_widen():
    state, detail = scopes_are_the_ceiling(
        "read", None, "fine-grained PAT", "merge-pull-request")
    assert state == "no-scopes-to-widen"
    assert "nothing to widen" in detail


def test_a_narrow_scope_and_a_low_role_are_both_reported():
    state, detail = scopes_are_the_ceiling(
        "read", ["public_repo"], "classic PAT", "merge-pull-request")
    assert state == "two-gates-open"
    assert "both" in detail


def test_a_sufficient_role_sends_the_reader_to_the_credential():
    state, _ = scopes_are_the_ceiling(
        "write", ["repo"], "classic PAT", "merge-pull-request")
    assert state == "not-the-question"
    assert verdict("write", "merge-pull-request")[0] == "role-sufficient"


def test_the_verdict_and_its_repair_hang_together():
    state, detail = verdict("read", "merge-pull-request")
    assert state == "role-insufficient"
    assert "2 role(s) higher" in detail
    fix = repair(state, "read", "merge-pull-request", "octobot")
    assert "octobot" in fix and "'write'" in fix
    assert "never its source" in fix


def test_no_access_is_kept_apart_from_a_low_role():
    state, detail = verdict("none", "merge-pull-request")
    assert state == "no-access"
    assert "404" in detail
    assert verdict("unreported", "merge-pull-request")[0] == "role-unreported"


def test_the_blocked_list_grows_as_the_role_shrinks():
    assert "merge-pull-request" in blocked_actions("read")
    assert "label-issue" in blocked_actions("read")
    assert "label-issue" not in blocked_actions("triage")
    assert blocked_actions("admin") == []


def test_scopes_absent_and_scopes_empty_are_different_readings():
    assert scope_list(None) is None
    assert scope_list("") == []
    assert scope_list("repo, workflow") == ["repo", "workflow"]


def test_the_credential_type_comes_from_its_prefix():
    assert token_kind("ghp_x") == "classic PAT"
    assert token_kind("github_pat_x") == "fine-grained PAT"
    assert token_kind("ghs_x") == "App installation token"
    assert token_kind("nope") == "unknown"


def test_the_run_costs_two_reads_or_three():
    assert read_cost() == 2
    assert read_cost(True) == 3
''',
"test_js_file": "github-repo-role.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ACTION_MINIMUM, ROLES, blockedActions, can, deficit, readCost, repair,
  roleFromCollaborator, roleFromPermissions, roleRank, scopeList,
  scopesAreTheCeiling, tokenKind, verdict,
} from './github-repo-role.mjs';

const READ_ONLY = {
  admin: false, maintain: false, push: false, triage: false, pull: true,
};
const TRIAGE = {
  admin: false, maintain: false, push: false, triage: true, pull: true,
};
const WRITE = {
  admin: false, maintain: false, push: true, triage: true, pull: true,
};

test('the hierarchy runs weakest to strongest', () => {
  assert.deepEqual(ROLES, ['none', 'read', 'triage', 'write', 'maintain', 'admin']);
  assert.ok(roleRank('read') < roleRank('triage'));
  assert.ok(roleRank('write') < roleRank('admin'));
  assert.equal(roleRank('nonsense'), -1);
});

test('the role is the highest true flag', () => {
  assert.equal(roleFromPermissions(READ_ONLY), 'read');
  assert.equal(roleFromPermissions(TRIAGE), 'triage');
  assert.equal(roleFromPermissions(WRITE), 'write');
});

test('an absent permissions object is unreported not none', () => {
  assert.equal(roleFromPermissions({}), 'unreported');
  assert.equal(roleFromPermissions(null), 'unreported');
  assert.equal(roleFromPermissions({ admin: false, pull: false }), 'none');
});

test('read explains every refused write in one flag', () => {
  assert.equal(READ_ONLY.push, false);
  assert.equal(can('read', 'merge-pull-request'), false);
  assert.equal(can('read', 'read-code'), true);
});

test('labelling needs triage and not write', () => {
  assert.equal(ACTION_MINIMUM['label-issue'], 'triage');
  assert.equal(can('triage', 'label-issue'), true);
  assert.equal(can('triage', 'merge-pull-request'), false);
  assert.equal(deficit('triage', 'merge-pull-request'), 1);
});

test('the deficit counts roles not booleans', () => {
  assert.equal(deficit('read', 'merge-pull-request'), 2);
  assert.equal(deficit('read', 'add-collaborator'), 4);
  assert.equal(deficit('admin', 'merge-pull-request'), 0);
  assert.equal(deficit('read', 'not-an-action'), null);
});

test('the legacy permission field rounds two roles away', () => {
  assert.deepEqual(
    roleFromCollaborator({ permission: 'write', role_name: 'maintain' }).slice(0, 2),
    ['maintain', true],
  );
  const [rounded, exact, note] = roleFromCollaborator({ permission: 'write' });
  assert.equal(rounded, 'write');
  assert.equal(exact, false);
  assert.match(note, /rounds maintain to write/);
  assert.equal(roleFromCollaborator({ role_name: 'triage' })[0], 'triage');
});

test('a custom org role is named and not priced', () => {
  const [role, exact, note] = roleFromCollaborator(
    { permission: 'read', role_name: 'security-auditor' },
  );
  assert.equal(role, 'custom:security-auditor');
  assert.equal(exact, false);
  assert.match(note, /custom organization role/);
  assert.equal(verdict(role, 'merge-pull-request')[0], 'custom-role');
});

test('a repo scope beside a read role is the headline', () => {
  const [state, detail] = scopesAreTheCeiling(
    'read', ['repo', 'workflow'], 'classic PAT', 'merge-pull-request');
  assert.equal(state, 'scopes-are-not-the-ceiling');
  assert.match(detail, /cannot change this answer/);
});

test('a fine grained token has no scopes to widen', () => {
  const [state, detail] = scopesAreTheCeiling(
    'read', null, 'fine-grained PAT', 'merge-pull-request');
  assert.equal(state, 'no-scopes-to-widen');
  assert.match(detail, /nothing to widen/);
});

test('a narrow scope and a low role are both reported', () => {
  const [state, detail] = scopesAreTheCeiling(
    'read', ['public_repo'], 'classic PAT', 'merge-pull-request');
  assert.equal(state, 'two-gates-open');
  assert.match(detail, /both/);
});

test('a sufficient role sends the reader to the credential', () => {
  assert.equal(
    scopesAreTheCeiling('write', ['repo'], 'classic PAT', 'merge-pull-request')[0],
    'not-the-question',
  );
  assert.equal(verdict('write', 'merge-pull-request')[0], 'role-sufficient');
});

test('the verdict and its repair hang together', () => {
  const [state, detail] = verdict('read', 'merge-pull-request');
  assert.equal(state, 'role-insufficient');
  assert.match(detail, /2 role\\(s\\) higher/);
  const fix = repair(state, 'read', 'merge-pull-request', 'octobot');
  assert.match(fix, /octobot/);
  assert.match(fix, /never its source/);
});

test('no access is kept apart from a low role', () => {
  const [state, detail] = verdict('none', 'merge-pull-request');
  assert.equal(state, 'no-access');
  assert.match(detail, /404/);
  assert.equal(verdict('unreported', 'merge-pull-request')[0], 'role-unreported');
});

test('the blocked list grows as the role shrinks', () => {
  assert.ok(blockedActions('read').includes('merge-pull-request'));
  assert.ok(blockedActions('read').includes('label-issue'));
  assert.ok(!blockedActions('triage').includes('label-issue'));
  assert.deepEqual(blockedActions('admin'), []);
});

test('scopes absent and scopes empty are different readings', () => {
  assert.equal(scopeList(null), null);
  assert.deepEqual(scopeList(''), []);
  assert.deepEqual(scopeList('repo, workflow'), ['repo', 'workflow']);
});

test('the credential type comes from its prefix', () => {
  assert.equal(tokenKind('ghp_x'), 'classic PAT');
  assert.equal(tokenKind('github_pat_x'), 'fine-grained PAT');
  assert.equal(tokenKind('nope'), 'unknown');
});

test('the run costs two reads or three', () => {
  assert.equal(readCost(), 2);
  assert.equal(readCost(true), 3);
});
''',
"faq": [
 ("Why does adding more scopes to the token not help?",
  "Because scopes and repository roles are two different gates and the call has to pass both. A scope is a limit the account places on a token acting for it; it can only ever be a subset of what the account itself can do. If the account has read on that repository, a token it mints can at most read that repository, no matter how many boxes were ticked. That is also why a token with <code>repo</code> works beautifully on eleven repositories and is refused on the twelfth: the token is identical in every call, and the role behind it is not."),
 ("How do I tell this apart from a missing scope, given both are 403?",
  "Read both halves. A classic token that is short a scope gets <code>x-accepted-oauth-scopes</code> on the refusal naming what would have worked, and the token's own <code>x-oauth-scopes</code> is on the same response, so the diff is right there. A role that is too low produces no such header. The decisive reading is the <code>permissions</code> object on <code>GET /repos/{owner}/{repo}</code>: if <code>push</code> is <code>false</code>, no scope change will make a write succeed, and you can know that before making the call that would fail."),
 ("Should the script not try the merge to be sure?",
  "No, and this is the case where that matters most. The whole section holds tokens that can reach real repositories, and a script that establishes &ldquo;this account cannot merge&rdquo; by attempting a merge has merged something whenever it was wrong. It is also unnecessary: the role is readable in advance, the minimum role for each action is documented, and the comparison is local. The script reads, compares, prints the repair and exits. Nothing it does can change the state of a repository."),
 ("The permissions object says read, but I am in a team that has write. Which is right?",
  "The permissions object. It is the effective access, already combining the direct collaborator grant, every team you belong to and the organization's base permission, computed for you on that repository at that moment. If it says read, then whatever you believe about the team either does not apply to that repository or has not taken effect. What the object cannot do is tell you which of the three produced the answer, so the repair may need making in a team rather than on the repository, and a read-only token cannot narrow that down further."),
 ("Why does the collaborator endpoint call a maintainer a writer?",
  "Because the <code>permission</code> field predates the roles it now has to describe. It has four values — admin, write, read, none — and GitHub has six roles, so maintain is reported as <code>write</code> and triage is reported as <code>read</code>. That rounding is only a nuisance until you use it to decide something: it will tell you a triager cannot label an issue, when triage is exactly the role that can. Read <code>role_name</code> instead, and treat a value that is not one of the six as a custom organization role whose abilities are not published."),
],
"related": [
 ("/github/missing-oauth-scope/", "When the token really is the problem, two headers say so"),
 ("/github/resource-not-accessible-by-pat/", "A fine-grained token's refusal names no permission"),
 ("/github/404-masking-403/", "No access at all returns 404, not 403"),
],
"citations": [CITE_COLLABORATORS, CITE_REPOS, CITE_REPO_ROLES, CITE_SCOPES],
},
{
"slug": "feature-disabled-endpoint-403",
"title": "A 403 that means the feature is disabled, not the permission",
"description": "One switched-off feature answers 403, 404 or 410 depending on the endpoint. security_and_analysis and the has_ flags say which before you call any of them.",
"h1": "A 403 that means the feature is disabled, not the permission",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github code scanning alerts 403 advanced security not enabled",
             "github secret scanning alerts 404 disabled",
             "github dependabot alerts 403 disabled for repository",
             "github security_and_analysis status disabled api",
             "github issues endpoint 410 gone disabled"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The security dashboard job gets <code>403</code> from <code>/code-scanning/alerts</code>. That is the status a missing grant produces, so somebody adds the security-events permission. Same 403. They swap the fine-grained token for an App installation with every security permission ticked. Same 403. Two weeks later a repository admin opens the settings page and code scanning has never been turned on for that repository, which is a checkbox, not a grant, and no credential in the world was going to open it.",
"short_answer": """<p>Some endpoints require the underlying <em>feature</em> to be switched on for that repository as well as a permission on the caller. When the feature is off, the endpoint refuses everybody, including a token holding exactly the permission it names.</p>
<p>Read the switch instead of guessing at the grant. <code>GET /repos/{owner}/{repo}</code> carries <code>security_and_analysis</code>, with a <code>status</code> of <code>enabled</code> or <code>disabled</code> for <code>advanced_security</code>, <code>secret_scanning</code>, <code>secret_scanning_push_protection</code> and <code>dependabot_security_updates</code>, alongside the plain toggles <code>has_issues</code>, <code>has_wiki</code>, <code>has_projects</code> and <code>has_discussions</code>. One read settles the whole matrix before any alert endpoint is called.</p>
<p>The trap worth naming: one off switch produces three different status codes. Code scanning refuses with <code>403</code>, secret scanning with <code>404</code>, and an issues endpoint on a repository with issues disabled answers <code>410 Gone</code>. Only the first looks like permissions, and all three mean the same thing.</p>""",
"problem": """<p>The reason this eats a fortnight is that the 403 arrives without the header that normally ends these arguments. A grant-shaped 403 from a fine-grained token or an App carries <code>x-accepted-github-permissions</code> naming what the endpoint wanted; a feature-shaped one has nothing to name, because the endpoint is not asking for anything. Nobody notices an absent header. They notice the status code, and the status code says permissions.</p>
<p>So the escalation runs upward through credential types. Add the permission. Regenerate the token. Try a classic PAT. Install a GitHub App with everything ticked, which is the point at which somebody has quietly created an over-wide credential in production to solve a problem that was never about credentials. Each step is plausible, each step fails identically, and the failure never varies enough to suggest the search is in the wrong place.</p>
<p>The second thing that hides it is the inconsistency of the codes. A team that has learned the 403 for code scanning will meet the 404 for secret scanning and file it as a different bug — probably as a missing repository, or as the alerts endpoint not existing on that plan. And an issues endpoint returning <code>410 Gone</code> reads like a deprecation, which is exactly what it is not: it is GitHub saying issues are switched off for this repository, in the status code reserved for something that used to be here.</p>
<p>Then there is the plan. Advanced Security features on private repositories depend on what the organization is paying for, so a flag can be <code>disabled</code> in a way no repository admin can change. That distinction does not show up in the refusal either.</p>""",
"why": """<p><strong>Two switches in series, and only one of them is on your side of the call.</strong> The permission is a property of the caller. The feature is a property of the repository. An endpoint gated on both refuses when either is missing, and the two refusals are not distinguishable by status code — which is why the diagnosis has to come from a reading rather than from the error.</p>
<p><strong>The security block is the single readable source, and it is not always readable.</strong> <code>security_and_analysis</code> is returned on the repository object only to a caller with admin on that repository. A collaborator with read gets the same repository object with the block absent entirely. That gives a third state that must not be collapsed into the other two: <em>unreported</em> is not <em>disabled</em>. It also gives a neat handoff, because the reason it is unreported is the caller's own role, which is <a href="/github/collaborator-permission-insufficient/">the note next door</a>.</p>
<p><strong>One switch, three status codes, and only the first looks like permissions.</strong> Code scanning answers <code>403</code> when Advanced Security is not enabled. Secret scanning answers <code>404</code>, which reads as a missing resource. Issues endpoints on a repository with <code>has_issues: false</code> answer <code>410 Gone</code>. Wikis and discussions do not have general REST alert endpoints at all, so the flag is the only signal you get. Knowing the mapping is the difference between one diagnosis and three separate investigations.</p>
<p><strong>Some flags describe the feature exactly and some are the closest thing available.</strong> <code>secret_scanning</code> governs the secret-scanning endpoints directly. <code>advanced_security</code> governs code scanning on private repositories directly. <code>dependabot_security_updates</code> is the automatic-pull-request setting rather than a flag for Dependabot alerts as such, so a <code>disabled</code> there is strong evidence about the alerts endpoint and not proof. The script marks which mappings are exact and which are proxies rather than presenting a uniform confidence it does not have.</p>
<p><strong>Plan-dependence is a repair a repository admin cannot perform.</strong> On a private or internal repository, the Advanced Security features are only available where the plan includes them, so <code>advanced_security: disabled</code> can mean nobody has ticked it or can mean nobody is able to. On public repositories the same features are generally available, which is why the identical script run against a public fork of a private repository sometimes answers differently and confuses everybody.</p>
<p><strong>Everything here is established by reading, and the probe is a read too.</strong> The repository object is one GET. The optional confirmation step is a GET per endpoint, which is the same call the failing job makes, so it costs nothing that job was not already spending and changes nothing. The script records the status it got and compares it against the status a disabled feature is documented to produce, so a mismatch is reported as a mismatch rather than forced into the story.</p>""",
"steps": [
 {"h": "Read every flag in one request",
  "body": """<p>The script fetches <code>GET /repos/{owner}/{repo}</code> once and prints the whole matrix: the <code>security_and_analysis</code> statuses and the <code>has_issues</code>, <code>has_wiki</code>, <code>has_projects</code>, <code>has_discussions</code> toggles beside them. That is the entire question answered for every feature at once, for one request against the core quota.</p>"""},
 {"h": "Name the endpoint that refused you",
  "body": """<p>Pass <code>--endpoint /code-scanning/alerts</code> and the script maps it to the feature that gates it, reports that feature's state, and says which status code a disabled feature produces on that endpoint. A full URL works too — the owner and repository are stripped, so you can paste the line out of your logs.</p>"""},
 {"h": "Separate the switch from the grant",
  "body": """<p>If you have the refusal, give the script <code>--status 403</code> and <code>--accepted-permissions security_events=read</code> if the response carried that header. A named permission with the feature enabled is a permission problem and belongs to a different note; a disabled feature with no header is this one. A status that does not match what a disabled feature produces is reported as a mismatch rather than quietly assimilated.</p>"""},
 {"h": "Confirm with a read if you want to, and only a read",
  "body": """<p><code>--probe</code> sends one GET per mapped endpoint and records the status. It is the same call your job already makes and it changes nothing; the read cost is printed before any of it is spent. The probe exists to corroborate the flag, not to establish the finding, which is why the script is just as useful without it.</p>"""},
 {"h": "Send the repair to the right desk",
  "body": """<p>A disabled feature is a repository setting, so the repair goes to somebody with admin on the repository or to the organization's security settings, not to whoever manages tokens. Where the flag is <code>disabled</code> on a private repository and the feature is Advanced Security, the script says plainly that the plan may be the constraint. Where the block is absent it says the reading is unavailable at your role rather than pretending the feature is off.</p>"""},
],
"verify": """<p>Once the feature is enabled the same read reports it, and the endpoint that spent a fortnight looking like a permissions problem starts answering.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_feature_flags.py octo-org/payments \\
    --endpoint /code-scanning/alerts --status 403
# read cost: 1 request(s) against the core hourly quota
# octo-org/payments: private=True
# security_and_analysis: advanced_security=disabled secret_scanning=disabled
#   secret_scanning_push_protection=disabled dependabot_security_updates=enabled
# toggles: has_issues=True has_wiki=False has_projects=True has_discussions=False
# /code-scanning/alerts -> advanced_security (exact), 403 when disabled
# feature-disabled: advanced_security is disabled on this repository, and the
#   403 you recorded is exactly what a disabled feature produces here. No
#   permission opens it.
# plan-note: this is a private repository, so Advanced Security availability
#   depends on the plan as well as on the checkbox.
# repair: enable code scanning on octo-org/payments in the repository's
#   security settings, or at organization level, then grant the token
#   security_events read. Both, in that order.</code></pre>""",
"code_intro": "The mapping table is the substance of this one, and it carries more than a feature name: each row says which flag gates the endpoint, whether that mapping is exact or a proxy, and which status code a disabled feature produces there. Everything else reads one repository object and looks things up. The three states are kept strictly apart — enabled, disabled, and unreported for the block a non-admin never receives — because collapsing the third into the second would turn a limit of the reader's own access into a confident and wrong claim about the repository.",
"py_file": "github_feature_flags.py",
"py": '''"""Say whether an endpoint refused you because the feature is switched off.

Read only. GET requests and nothing else. Nothing here is established by
attempting anything: the repository object carries every feature flag, and the
optional probe is the same GET the failing job already makes.

The point of the note: some endpoints are gated on a repository feature as well
as on a permission. When the feature is off they refuse everybody, including a
caller holding exactly the permission the endpoint names, and one off switch
produces three different status codes depending on the endpoint family.

What this can and cannot see: security_and_analysis is only returned to a
caller with admin on the repository. An absent block is therefore unreported,
not disabled, and the script keeps those apart. Some flags gate their endpoint
exactly and one is the closest available proxy; the table says which.

Environment:

    GITHUB_TOKEN    a token with read access to the repository
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_feature_flags")

API = "https://api.github.com"
UA = "github-feature-flags/1.0"

# Read out of security_and_analysis, which is a map of {name: {status: ...}}.
SECURITY_FEATURES = (
    "advanced_security",
    "secret_scanning",
    "secret_scanning_push_protection",
    "secret_scanning_non_provider_patterns",
    "dependabot_security_updates",
)

# Plain booleans on the repository object itself. These come back to any caller
# who can read the repository, unlike the security block.
TOGGLES = ("has_issues", "has_wiki", "has_projects", "has_discussions",
           "has_pages", "has_downloads")

# The table this note exists for. Each row: which flag gates the endpoint, where
# that flag is read from, the status a disabled feature produces there, and
# whether the mapping is exact or the closest available proxy.
#
# The three status codes are the whole trap. Only the 403 looks like a
# permissions problem, and all three mean the feature is off.
ENDPOINT_FEATURES = {
    "/code-scanning/alerts": ("advanced_security", "security", 403, "exact"),
    "/code-scanning/analyses": ("advanced_security", "security", 403, "exact"),
    "/secret-scanning/alerts": ("secret_scanning", "security", 404, "exact"),
    "/dependabot/alerts": ("dependabot_security_updates", "security", 403, "proxy"),
    "/issues": ("has_issues", "toggle", 410, "exact"),
    "/issues/comments": ("has_issues", "toggle", 410, "exact"),
    "/milestones": ("has_issues", "toggle", 410, "exact"),
}

# Why the proxy rows are not presented as certainties.
PROXY_NOTE = ("this flag is the closest one the repository object publishes for "
              "that endpoint rather than a switch for it exactly, so a disabled "
              "reading here is strong evidence and not proof.")

# Advanced Security on a private or internal repository depends on the plan as
# well as on the checkbox, which is a repair a repository admin cannot make.
PLAN_DEPENDENT = ("advanced_security", "secret_scanning",
                  "secret_scanning_push_protection")


def read_cost(probes=0):
    """Requests this run will spend against the core quota. Pure."""
    return 1 + max(0, int(probes or 0))


def normalise_endpoint(path):
    """Reduce a logged URL to a key in the table. Pure.

    Accepts a full URL, a /repos/{owner}/{repo}/... path or the bare suffix, so
    a line can be pasted straight out of a log without editing.
    """
    text = str(path or "").strip()
    for prefix in ("https://api.github.com", "http://api.github.com"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    text = text.split("?")[0].rstrip("/")
    if not text:
        return ""
    if not text.startswith("/"):
        text = "/" + text
    if text.startswith("/repos/"):
        parts = text.split("/")
        # /repos/{owner}/{repo}/rest -> /rest
        if len(parts) > 4:
            text = "/" + "/".join(parts[4:])
        else:
            text = "/"
    return text


def feature_for(path):
    """The table row for an endpoint, or None. Pure."""
    key = normalise_endpoint(path)
    row = ENDPOINT_FEATURES.get(key)
    if row is None:
        return None
    feature, source, status, confidence = row
    return {"endpoint": key, "feature": feature, "source": source,
            "status_when_disabled": status, "confidence": confidence}


def security_block(repo):
    """The security_and_analysis map, or None when it was not returned. Pure."""
    block = (repo or {}).get("security_and_analysis")
    return block if isinstance(block, dict) else None


def flag_state(repo, feature, source):
    """enabled, disabled or unreported for one feature. Pure.

    unreported is a real third answer. The security block is only sent to a
    caller with admin on the repository, so its absence describes the reader
    rather than the repository, and calling that "disabled" would be a
    confident claim built on a missing grant.
    """
    if source == "toggle":
        value = (repo or {}).get(feature)
        if value is True:
            return "enabled"
        if value is False:
            return "disabled"
        return "unreported"
    block = security_block(repo)
    if block is None:
        return "unreported"
    entry = block.get(feature)
    if not isinstance(entry, dict):
        return "unreported"
    status = str(entry.get("status") or "").strip().lower()
    if status in ("enabled", "disabled"):
        return status
    return "unreported"


def matrix(repo):
    """Every endpoint in the table with the state of the flag gating it. Pure."""
    rows = []
    for key in sorted(ENDPOINT_FEATURES):
        row = feature_for(key)
        row["state"] = flag_state(repo, row["feature"], row["source"])
        row["will_serve"] = {"enabled": True, "disabled": False}.get(row["state"])
        rows.append(row)
    return rows


def plan_may_be_the_constraint(repo, feature):
    """Is this a repair a repository admin might not be able to make. Pure."""
    if feature not in PLAN_DEPENDENT:
        return False
    visibility = str((repo or {}).get("visibility") or "").strip().lower()
    return bool((repo or {}).get("private")) or visibility in ("private", "internal")


def status_matches(row, observed):
    """Does the recorded status match what a disabled feature produces. Pure.

    Returns True, False, or None when nothing was recorded. A mismatch is worth
    saying out loud: it means the refusal probably has a different cause, and
    forcing it into the story here would be the same mistake in a new direction.
    """
    if observed in (None, ""):
        return None
    try:
        return int(observed) == int(row["status_when_disabled"])
    except (TypeError, ValueError):
        return None


def classify(repo, row, observed_status=None, accepted_permissions=None):
    """Attribute one refusal to the switch or to the grant. Pure.

    Returns (state, detail).
    """
    if row is None:
        return ("endpoint-unknown",
                "that endpoint is not one of the feature-gated ones in this "
                "table, so a refusal from it is not this note. Read the whole "
                "flag matrix above and check the permission headers instead.")
    state_of_flag = row["state"] if "state" in row else flag_state(
        repo, row["feature"], row["source"])
    named = str(accepted_permissions or "").strip()
    match = status_matches(row, observed_status)

    if state_of_flag == "unreported":
        return ("feature-unreported",
                "%s could not be read. The security_and_analysis block is only "
                "returned to a caller with admin on the repository, so this "
                "says something about your own role rather than about the "
                "feature." % row["feature"])
    if state_of_flag == "disabled":
        if match is False:
            return ("status-mismatch",
                    "%s is disabled, but a disabled feature answers %s on this "
                    "endpoint and you recorded %s. Fix the feature and expect "
                    "the other failure to survive it."
                    % (row["feature"], row["status_when_disabled"], observed_status))
        return ("feature-disabled",
                "%s is disabled on this repository, and %s is what a disabled "
                "feature produces here. No permission opens it."
                % (row["feature"], row["status_when_disabled"]))
    if named:
        return ("permission-named",
                "%s is enabled and the response named '%s' in "
                "x-accepted-github-permissions, so this is a grant that is "
                "missing rather than a feature that is off."
                % (row["feature"], named))
    return ("feature-enabled",
            "%s is enabled, so the feature is not what refused you. Look at the "
            "credential next: a fine-grained token names no permission on its "
            "own refusal, and an App names one in a header." % row["feature"])


def repair(state, row, repo=None):
    """The sentence a reader has to act on. Pure."""
    feature = (row or {}).get("feature", "the feature")
    if state == "feature-disabled":
        text = ("enable %s on this repository in its security settings, or at "
                "organization level for every repository, then grant the "
                "caller the matching read permission. Both, in that order."
                % feature)
        if plan_may_be_the_constraint(repo or {}, feature):
            text += (" This is a private or internal repository, so "
                     "availability depends on the plan as well as on the "
                     "checkbox, and that part is not a repository setting.")
        if (row or {}).get("confidence") == "proxy":
            text += " Note that " + PROXY_NOTE
        return text
    if state == "feature-unreported":
        return ("read the repository with an account that has admin on it, or "
                "ask an admin what the setting says. Do not record this as "
                "disabled: an absent block is a limit on your reading.")
    if state == "permission-named":
        return ("grant the named permission. The feature is on, so this is the "
                "ordinary permissions path and not this note.")
    if state == "status-mismatch":
        return ("enable the feature anyway, then diagnose the recorded status "
                "separately. Two causes were in play and only one of them is "
                "addressed here.")
    if state == "feature-enabled":
        return ("look at the credential. Nothing about the repository's "
                "features explains this refusal.")
    return ("name the endpoint that refused you with --endpoint so the flag can "
            "be mapped to it.")


def get(session, path):
    """One GET. Returns the response object."""
    r = session.get(API + path, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", help="owner/name of the repository")
    ap.add_argument("--endpoint", default="",
                    help="the endpoint that refused you, e.g. "
                         "/code-scanning/alerts. A full URL is accepted.")
    ap.add_argument("--status", default="",
                    help="the status code you recorded from it")
    ap.add_argument("--accepted-permissions", default="",
                    help="x-accepted-github-permissions off that response, if "
                         "it carried one")
    ap.add_argument("--probe", action="store_true",
                    help="also GET each mapped endpoint to record its status. "
                         "Reads only, and the same call your job already makes.")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2
    if "/" not in args.repo:
        log.error("repo should be owner/name")
        return 2

    probes = len(ENDPOINT_FEATURES) if args.probe else 0
    log.info("read cost: %d request(s) against the core hourly quota",
             read_cost(probes))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    response = get(session, "/repos/" + args.repo)
    if response.status_code != 200:
        log.error("%s: HTTP %s reading the repository", args.repo,
                  response.status_code)
        return 2
    repo = response.json()

    log.info("%s: private=%s", args.repo, repo.get("private"))
    block = security_block(repo)
    if block is None:
        log.info("security_and_analysis: not returned. That block is only sent "
                 "to a caller with admin on the repository.")
    else:
        log.info("security_and_analysis: %s", " ".join(
            "%s=%s" % (f, flag_state(repo, f, "security"))
            for f in SECURITY_FEATURES))
    log.info("toggles: %s", " ".join(
        "%s=%s" % (t, repo.get(t)) for t in TOGGLES))

    rows = matrix(repo)
    probed = {}
    if args.probe:
        for row in rows:
            r = get(session, "/repos/%s%s" % (args.repo, row["endpoint"]))
            probed[row["endpoint"]] = r.status_code
            log.info("probe %s -> HTTP %s (flag %s)", row["endpoint"],
                     r.status_code, row["state"])

    target = feature_for(args.endpoint) if args.endpoint else None
    if target:
        target["state"] = flag_state(repo, target["feature"], target["source"])
        log.info("%s -> %s (%s), %s when disabled", target["endpoint"],
                 target["feature"], target["confidence"],
                 target["status_when_disabled"])
    state, detail = classify(repo, target, args.status,
                             args.accepted_permissions)
    log.info("%s: %s", state, detail)
    if target and plan_may_be_the_constraint(repo, target["feature"]):
        log.info("plan-note: this is a private or internal repository, so "
                 "availability depends on the plan as well as on the checkbox.")
    log.info("repair: %s", repair(state, target, repo))

    print(json.dumps({
        "repository": args.repo,
        "private": repo.get("private"),
        "visibility": repo.get("visibility"),
        "security_block_returned": block is not None,
        "security_and_analysis": {
            f: flag_state(repo, f, "security") for f in SECURITY_FEATURES},
        "toggles": {t: repo.get(t) for t in TOGGLES},
        "matrix": rows,
        "probed": probed,
        "endpoint": target,
        "state": state,
        "detail": detail,
        "repair": repair(state, target, repo),
    }, indent=2, default=str))
    return 1 if state in ("feature-disabled", "status-mismatch") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-feature-flags.mjs",
"js": '''/**
 * Say whether an endpoint refused you because the feature is switched off.
 *
 * Read only. GET requests and nothing else. The repository object carries every
 * feature flag, so nothing here is established by attempting anything.
 *
 * Some endpoints are gated on a repository feature as well as on a permission.
 * When the feature is off they refuse everybody, and one off switch produces
 * three different status codes depending on the endpoint family: 403 for code
 * scanning, 404 for secret scanning, 410 for issues.
 *
 * Environment:
 *   GITHUB_TOKEN        a token with read access to the repository
 *   GITHUB_REPO         owner/name
 *   GITHUB_ENDPOINT     the endpoint that refused you
 *   GITHUB_STATUS       the status code you recorded from it
 *   GITHUB_ACCEPTED     x-accepted-github-permissions, if the response had one
 */
const API = 'https://api.github.com';
const UA = 'github-feature-flags/1.0';

/** Read out of security_and_analysis, a map of {name: {status}}. */
export const SECURITY_FEATURES = [
  'advanced_security',
  'secret_scanning',
  'secret_scanning_push_protection',
  'secret_scanning_non_provider_patterns',
  'dependabot_security_updates',
];

/** Plain booleans on the repository object, visible to any reader. */
export const TOGGLES = ['has_issues', 'has_wiki', 'has_projects',
  'has_discussions', 'has_pages', 'has_downloads'];

/** Flag, where it is read, status when disabled, and how exact the mapping is. */
export const ENDPOINT_FEATURES = {
  '/code-scanning/alerts': ['advanced_security', 'security', 403, 'exact'],
  '/code-scanning/analyses': ['advanced_security', 'security', 403, 'exact'],
  '/secret-scanning/alerts': ['secret_scanning', 'security', 404, 'exact'],
  '/dependabot/alerts': ['dependabot_security_updates', 'security', 403, 'proxy'],
  '/issues': ['has_issues', 'toggle', 410, 'exact'],
  '/issues/comments': ['has_issues', 'toggle', 410, 'exact'],
  '/milestones': ['has_issues', 'toggle', 410, 'exact'],
};

/** Why the proxy rows are not presented as certainties. */
export const PROXY_NOTE = 'this flag is the closest one the repository object '
  + 'publishes for that endpoint rather than a switch for it exactly, so a '
  + 'disabled reading here is strong evidence and not proof.';

/** Advanced Security on a private repository depends on the plan too. */
export const PLAN_DEPENDENT = ['advanced_security', 'secret_scanning',
  'secret_scanning_push_protection'];

/** Requests this run will spend against the core quota. Pure. */
export function readCost(probes = 0) {
  return 1 + Math.max(0, Math.trunc(Number(probes) || 0));
}

/** Reduce a logged URL to a key in the table. Pure. */
export function normaliseEndpoint(path) {
  let text = String(path ?? '').trim();
  for (const prefix of ['https://api.github.com', 'http://api.github.com']) {
    if (text.startsWith(prefix)) text = text.slice(prefix.length);
  }
  [text] = text.split('?');
  text = text.replace(/\\/+$/, '');
  if (!text) return '';
  if (!text.startsWith('/')) text = `/${text}`;
  if (text.startsWith('/repos/')) {
    const parts = text.split('/');
    text = parts.length > 4 ? `/${parts.slice(4).join('/')}` : '/';
  }
  return text;
}

/** The table row for an endpoint, or null. Pure. */
export function featureFor(path) {
  const key = normaliseEndpoint(path);
  const row = ENDPOINT_FEATURES[key];
  if (!row) return null;
  const [feature, source, status, confidence] = row;
  return {
    endpoint: key, feature, source, status_when_disabled: status, confidence,
  };
}

/** The security_and_analysis map, or null when it was not returned. Pure. */
export function securityBlock(repo) {
  const block = (repo || {}).security_and_analysis;
  return block && typeof block === 'object' ? block : null;
}

/** enabled, disabled or unreported for one feature. Pure. */
export function flagState(repo, feature, source) {
  if (source === 'toggle') {
    const value = (repo || {})[feature];
    if (value === true) return 'enabled';
    if (value === false) return 'disabled';
    return 'unreported';
  }
  const block = securityBlock(repo);
  if (!block) return 'unreported';
  const entry = block[feature];
  if (!entry || typeof entry !== 'object') return 'unreported';
  const status = String(entry.status ?? '').trim().toLowerCase();
  return status === 'enabled' || status === 'disabled' ? status : 'unreported';
}

/** Every endpoint with the state of the flag gating it. Pure. */
export function matrix(repo) {
  return Object.keys(ENDPOINT_FEATURES).sort().map((key) => {
    const row = featureFor(key);
    row.state = flagState(repo, row.feature, row.source);
    row.will_serve = { enabled: true, disabled: false }[row.state] ?? null;
    return row;
  });
}

/** Is this a repair a repository admin might not be able to make. Pure. */
export function planMayBeTheConstraint(repo, feature) {
  if (!PLAN_DEPENDENT.includes(feature)) return false;
  const visibility = String((repo || {}).visibility ?? '').trim().toLowerCase();
  return Boolean((repo || {}).private) || ['private', 'internal'].includes(visibility);
}

/** Does the recorded status match what a disabled feature produces. Pure. */
export function statusMatches(row, observed) {
  if (observed === null || observed === undefined || observed === '') return null;
  const n = Number(observed);
  if (!Number.isFinite(n)) return null;
  return n === Number(row.status_when_disabled);
}

/** Attribute one refusal to the switch or to the grant. Pure. */
export function classify(repo, row, observedStatus = null, acceptedPermissions = null) {
  if (!row) {
    return ['endpoint-unknown', 'that endpoint is not one of the feature-gated '
      + 'ones in this table, so a refusal from it is not this note. Read the '
      + 'whole flag matrix above and check the permission headers instead.'];
  }
  const stateOfFlag = row.state ?? flagState(repo, row.feature, row.source);
  const named = String(acceptedPermissions ?? '').trim();
  const match = statusMatches(row, observedStatus);

  if (stateOfFlag === 'unreported') {
    return ['feature-unreported', `${row.feature} could not be read. The `
      + 'security_and_analysis block is only returned to a caller with admin on '
      + 'the repository, so this says something about your own role rather than '
      + 'about the feature.'];
  }
  if (stateOfFlag === 'disabled') {
    if (match === false) {
      return ['status-mismatch', `${row.feature} is disabled, but a disabled `
        + `feature answers ${row.status_when_disabled} on this endpoint and you `
        + `recorded ${observedStatus}. Fix the feature and expect the other `
        + 'failure to survive it.'];
    }
    return ['feature-disabled', `${row.feature} is disabled on this repository, `
      + `and ${row.status_when_disabled} is what a disabled feature produces `
      + 'here. No permission opens it.'];
  }
  if (named) {
    return ['permission-named', `${row.feature} is enabled and the response `
      + `named '${named}' in x-accepted-github-permissions, so this is a grant `
      + 'that is missing rather than a feature that is off.'];
  }
  return ['feature-enabled', `${row.feature} is enabled, so the feature is not `
    + 'what refused you. Look at the credential next: a fine-grained token names '
    + 'no permission on its own refusal, and an App names one in a header.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, row, repo = {}) {
  const feature = (row || {}).feature || 'the feature';
  if (state === 'feature-disabled') {
    let text = `enable ${feature} on this repository in its security settings, `
      + 'or at organization level for every repository, then grant the caller '
      + 'the matching read permission. Both, in that order.';
    if (planMayBeTheConstraint(repo, feature)) {
      text += ' This is a private or internal repository, so availability '
        + 'depends on the plan as well as on the checkbox, and that part is not '
        + 'a repository setting.';
    }
    if ((row || {}).confidence === 'proxy') text += ` Note that ${PROXY_NOTE}`;
    return text;
  }
  if (state === 'feature-unreported') {
    return 'read the repository with an account that has admin on it, or ask an '
      + 'admin what the setting says. Do not record this as disabled: an absent '
      + 'block is a limit on your reading.';
  }
  if (state === 'permission-named') {
    return 'grant the named permission. The feature is on, so this is the '
      + 'ordinary permissions path and not this note.';
  }
  if (state === 'status-mismatch') {
    return 'enable the feature anyway, then diagnose the recorded status '
      + 'separately. Two causes were in play and only one of them is addressed here.';
  }
  if (state === 'feature-enabled') {
    return 'look at the credential. Nothing about the repository features '
      + 'explains this refusal.';
  }
  return 'name the endpoint that refused you so the flag can be mapped to it.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repoName = process.env.GITHUB_REPO;
  if (!token || !repoName) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPO');
    process.exitCode = 2;
    return;
  }
  console.log(`read cost: ${readCost(0)} request(s) against the core hourly quota`);

  const res = await fetch(`${API}/repos/${repoName}`, { headers: headers(token) });
  if (res.status !== 200) {
    console.error(`${repoName}: HTTP ${res.status} reading the repository`);
    process.exitCode = 2;
    return;
  }
  const repo = await res.json();

  console.log(`${repoName}: private=${repo.private}`);
  if (!securityBlock(repo)) {
    console.log('security_and_analysis: not returned. That block is only sent to '
      + 'a caller with admin on the repository.');
  } else {
    console.log(`security_and_analysis: ${SECURITY_FEATURES
      .map((f) => `${f}=${flagState(repo, f, 'security')}`).join(' ')}`);
  }
  console.log(`toggles: ${TOGGLES.map((t) => `${t}=${repo[t]}`).join(' ')}`);

  const target = process.env.GITHUB_ENDPOINT
    ? featureFor(process.env.GITHUB_ENDPOINT) : null;
  if (target) {
    target.state = flagState(repo, target.feature, target.source);
    console.log(`${target.endpoint} -> ${target.feature} (${target.confidence}), `
      + `${target.status_when_disabled} when disabled`);
  }
  const [state, detail] = classify(repo, target, process.env.GITHUB_STATUS,
    process.env.GITHUB_ACCEPTED);
  console.log(`${state}: ${detail}`);
  console.log(`repair: ${repair(state, target, repo)}`);

  console.log(JSON.stringify({
    repository: repoName,
    private: repo.private,
    visibility: repo.visibility,
    security_block_returned: securityBlock(repo) !== null,
    matrix: matrix(repo),
    endpoint: target,
    state,
    detail,
    repair: repair(state, target, repo),
  }, null, 2));
  process.exitCode = ['feature-disabled', 'status-mismatch'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The three status codes are asserted as data, because the note stands or falls on them: 403 for code scanning, 404 for secret scanning, 410 for issues, all produced by the same kind of off switch. Then the three flag states, where the one that matters is <code>unreported</code> — a repository object with no security block has to come back as unreported and never as disabled, since the block's absence describes the reader's role and not the repository. The rest is the classifier: a named permission beside an enabled feature is somebody else's note, a recorded status that does not match the documented one is called a mismatch rather than folded into the story, and the endpoint normaliser is fed the kind of full URL people actually paste out of a log.",
"test_py_file": "test_github_feature_flags.py",
"test_py": '''from github_feature_flags import (
    ENDPOINT_FEATURES, PLAN_DEPENDENT, classify, feature_for, flag_state,
    matrix, normalise_endpoint, plan_may_be_the_constraint, read_cost, repair,
    security_block, status_matches,
)

ADMIN_VIEW = {
    "private": True,
    "visibility": "private",
    "has_issues": False,
    "has_wiki": True,
    "security_and_analysis": {
        "advanced_security": {"status": "disabled"},
        "secret_scanning": {"status": "disabled"},
        "secret_scanning_push_protection": {"status": "disabled"},
        "dependabot_security_updates": {"status": "enabled"},
    },
}
# The same repository read by a collaborator without admin: no security block.
READER_VIEW = {"private": True, "visibility": "private", "has_issues": False,
               "has_wiki": True}
HEALTHY = {
    "private": False,
    "visibility": "public",
    "has_issues": True,
    "security_and_analysis": {
        "advanced_security": {"status": "enabled"},
        "secret_scanning": {"status": "enabled"},
    },
}


def test_one_off_switch_produces_three_status_codes():
    assert feature_for("/code-scanning/alerts")["status_when_disabled"] == 403
    assert feature_for("/secret-scanning/alerts")["status_when_disabled"] == 404
    assert feature_for("/issues")["status_when_disabled"] == 410
    # Only the first of those looks like a permissions problem.


def test_a_logged_url_is_reduced_to_a_table_key():
    assert normalise_endpoint(
        "https://api.github.com/repos/octo/pay/code-scanning/alerts?state=open"
    ) == "/code-scanning/alerts"
    assert normalise_endpoint("/repos/octo/pay/issues") == "/issues"
    assert normalise_endpoint("issues") == "/issues"
    assert normalise_endpoint("") == ""


def test_an_absent_security_block_is_unreported_and_never_disabled():
    assert security_block(READER_VIEW) is None
    assert flag_state(READER_VIEW, "advanced_security", "security") == "unreported"
    assert flag_state(ADMIN_VIEW, "advanced_security", "security") == "disabled"
    assert flag_state(ADMIN_VIEW, "dependabot_security_updates", "security") == "enabled"


def test_a_toggle_is_readable_by_anybody_who_can_read_the_repo():
    assert flag_state(READER_VIEW, "has_issues", "toggle") == "disabled"
    assert flag_state(READER_VIEW, "has_wiki", "toggle") == "enabled"
    assert flag_state(READER_VIEW, "has_discussions", "toggle") == "unreported"


def test_a_disabled_feature_is_named_and_no_permission_opens_it():
    row = feature_for("/code-scanning/alerts")
    state, detail = classify(ADMIN_VIEW, row, 403)
    assert state == "feature-disabled"
    assert "No permission opens it" in detail


def test_the_unreported_case_blames_the_readers_role_not_the_repo():
    row = feature_for("/code-scanning/alerts")
    state, detail = classify(READER_VIEW, row, 403)
    assert state == "feature-unreported"
    assert "admin on the repository" in detail
    assert "absent block is a limit on your reading" in repair(state, row)


def test_an_enabled_feature_with_a_named_permission_is_somebody_elses_note():
    row = feature_for("/code-scanning/alerts")
    state, detail = classify(HEALTHY, row, 403, "security_events=read")
    assert state == "permission-named"
    assert "security_events=read" in detail
    state, _ = classify(HEALTHY, row, 403, "")
    assert state == "feature-enabled"


def test_a_status_that_does_not_match_is_called_a_mismatch():
    row = feature_for("/secret-scanning/alerts")
    assert status_matches(row, 404) is True
    assert status_matches(row, 403) is False
    assert status_matches(row, None) is None
    state, detail = classify(ADMIN_VIEW, row, 403)
    assert state == "status-mismatch"
    assert "404" in detail and "403" in detail


def test_the_issues_toggle_answers_410_gone_which_reads_as_deprecation():
    row = feature_for("/issues")
    state, detail = classify(ADMIN_VIEW, row, 410)
    assert state == "feature-disabled"
    assert "410" in detail


def test_the_matrix_covers_every_endpoint_in_the_table():
    rows = matrix(ADMIN_VIEW)
    assert len(rows) == len(ENDPOINT_FEATURES)
    by_endpoint = {r["endpoint"]: r for r in rows}
    assert by_endpoint["/issues"]["will_serve"] is False
    assert by_endpoint["/dependabot/alerts"]["will_serve"] is True
    assert matrix(READER_VIEW)[0]["will_serve"] in (True, False, None)


def test_a_proxy_mapping_is_flagged_as_one():
    assert feature_for("/dependabot/alerts")["confidence"] == "proxy"
    assert feature_for("/secret-scanning/alerts")["confidence"] == "exact"
    row = feature_for("/dependabot/alerts")
    row["state"] = "disabled"
    assert "not proof" in repair("feature-disabled", row, ADMIN_VIEW)


def test_the_plan_can_be_a_repair_an_admin_cannot_make():
    assert "advanced_security" in PLAN_DEPENDENT
    assert plan_may_be_the_constraint(ADMIN_VIEW, "advanced_security") is True
    assert plan_may_be_the_constraint(HEALTHY, "advanced_security") is False
    assert plan_may_be_the_constraint(ADMIN_VIEW, "has_issues") is False
    row = feature_for("/code-scanning/alerts")
    assert "depends on the plan" in repair("feature-disabled", row, ADMIN_VIEW)


def test_an_endpoint_outside_the_table_is_handed_back():
    assert feature_for("/pulls") is None
    state, _ = classify(ADMIN_VIEW, None, 403)
    assert state == "endpoint-unknown"


def test_the_run_costs_one_read_plus_any_probes():
    assert read_cost() == 1
    assert read_cost(len(ENDPOINT_FEATURES)) == 1 + len(ENDPOINT_FEATURES)
''',
"test_js_file": "github-feature-flags.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ENDPOINT_FEATURES, PLAN_DEPENDENT, classify, featureFor, flagState, matrix,
  normaliseEndpoint, planMayBeTheConstraint, readCost, repair, securityBlock,
  statusMatches,
} from './github-feature-flags.mjs';

const ADMIN_VIEW = {
  private: true,
  visibility: 'private',
  has_issues: false,
  has_wiki: true,
  security_and_analysis: {
    advanced_security: { status: 'disabled' },
    secret_scanning: { status: 'disabled' },
    secret_scanning_push_protection: { status: 'disabled' },
    dependabot_security_updates: { status: 'enabled' },
  },
};
const READER_VIEW = {
  private: true, visibility: 'private', has_issues: false, has_wiki: true,
};
const HEALTHY = {
  private: false,
  visibility: 'public',
  has_issues: true,
  security_and_analysis: {
    advanced_security: { status: 'enabled' },
    secret_scanning: { status: 'enabled' },
  },
};

test('one off switch produces three status codes', () => {
  assert.equal(featureFor('/code-scanning/alerts').status_when_disabled, 403);
  assert.equal(featureFor('/secret-scanning/alerts').status_when_disabled, 404);
  assert.equal(featureFor('/issues').status_when_disabled, 410);
});

test('a logged url is reduced to a table key', () => {
  assert.equal(
    normaliseEndpoint('https://api.github.com/repos/octo/pay/code-scanning/alerts?state=open'),
    '/code-scanning/alerts',
  );
  assert.equal(normaliseEndpoint('/repos/octo/pay/issues'), '/issues');
  assert.equal(normaliseEndpoint('issues'), '/issues');
  assert.equal(normaliseEndpoint(''), '');
});

test('an absent security block is unreported and never disabled', () => {
  assert.equal(securityBlock(READER_VIEW), null);
  assert.equal(flagState(READER_VIEW, 'advanced_security', 'security'), 'unreported');
  assert.equal(flagState(ADMIN_VIEW, 'advanced_security', 'security'), 'disabled');
  assert.equal(flagState(ADMIN_VIEW, 'dependabot_security_updates', 'security'), 'enabled');
});

test('a toggle is readable by anybody who can read the repo', () => {
  assert.equal(flagState(READER_VIEW, 'has_issues', 'toggle'), 'disabled');
  assert.equal(flagState(READER_VIEW, 'has_wiki', 'toggle'), 'enabled');
  assert.equal(flagState(READER_VIEW, 'has_discussions', 'toggle'), 'unreported');
});

test('a disabled feature is named and no permission opens it', () => {
  const [state, detail] = classify(ADMIN_VIEW, featureFor('/code-scanning/alerts'), 403);
  assert.equal(state, 'feature-disabled');
  assert.match(detail, /No permission opens it/);
});

test('the unreported case blames the readers role not the repo', () => {
  const row = featureFor('/code-scanning/alerts');
  const [state, detail] = classify(READER_VIEW, row, 403);
  assert.equal(state, 'feature-unreported');
  assert.match(detail, /admin on the repository/);
  assert.match(repair(state, row), /absent block is a limit on your reading/);
});

test('an enabled feature with a named permission is somebody elses note', () => {
  const row = featureFor('/code-scanning/alerts');
  const [state, detail] = classify(HEALTHY, row, 403, 'security_events=read');
  assert.equal(state, 'permission-named');
  assert.match(detail, /security_events=read/);
  assert.equal(classify(HEALTHY, row, 403, '')[0], 'feature-enabled');
});

test('a status that does not match is called a mismatch', () => {
  const row = featureFor('/secret-scanning/alerts');
  assert.equal(statusMatches(row, 404), true);
  assert.equal(statusMatches(row, 403), false);
  assert.equal(statusMatches(row, null), null);
  const [state, detail] = classify(ADMIN_VIEW, row, 403);
  assert.equal(state, 'status-mismatch');
  assert.match(detail, /404/);
});

test('the issues toggle answers 410 gone which reads as deprecation', () => {
  const [state, detail] = classify(ADMIN_VIEW, featureFor('/issues'), 410);
  assert.equal(state, 'feature-disabled');
  assert.match(detail, /410/);
});

test('the matrix covers every endpoint in the table', () => {
  const rows = matrix(ADMIN_VIEW);
  assert.equal(rows.length, Object.keys(ENDPOINT_FEATURES).length);
  const byEndpoint = Object.fromEntries(rows.map((r) => [r.endpoint, r]));
  assert.equal(byEndpoint['/issues'].will_serve, false);
  assert.equal(byEndpoint['/dependabot/alerts'].will_serve, true);
});

test('a proxy mapping is flagged as one', () => {
  assert.equal(featureFor('/dependabot/alerts').confidence, 'proxy');
  assert.equal(featureFor('/secret-scanning/alerts').confidence, 'exact');
  const row = featureFor('/dependabot/alerts');
  row.state = 'disabled';
  assert.match(repair('feature-disabled', row, ADMIN_VIEW), /not proof/);
});

test('the plan can be a repair an admin cannot make', () => {
  assert.ok(PLAN_DEPENDENT.includes('advanced_security'));
  assert.equal(planMayBeTheConstraint(ADMIN_VIEW, 'advanced_security'), true);
  assert.equal(planMayBeTheConstraint(HEALTHY, 'advanced_security'), false);
  assert.equal(planMayBeTheConstraint(ADMIN_VIEW, 'has_issues'), false);
  assert.match(
    repair('feature-disabled', featureFor('/code-scanning/alerts'), ADMIN_VIEW),
    /depends on the plan/,
  );
});

test('an endpoint outside the table is handed back', () => {
  assert.equal(featureFor('/pulls'), null);
  assert.equal(classify(ADMIN_VIEW, null, 403)[0], 'endpoint-unknown');
});

test('the run costs one read plus any probes', () => {
  assert.equal(readCost(), 1);
  assert.equal(readCost(7), 8);
});
''',
"faq": [
 ("The token has the security-events permission and still gets 403. What is missing?",
  "The feature, not the grant. Code scanning, secret scanning and Dependabot alerts each have to be switched on for that repository before their endpoints will serve anybody, and the permission is checked separately on top of that. A caller holding exactly the permission the endpoint names is still refused while the feature is off, which is why widening the credential never changes anything. Read <code>security_and_analysis</code> on <code>GET /repos/{owner}/{repo}</code> first: if the relevant status is <code>disabled</code>, no permission you can grant will open it."),
 ("Why does secret scanning answer 404 when code scanning answers 403 for the same reason?",
  "Because the endpoint families were built at different times with different conventions, and nobody harmonised them. It is worth memorising rather than rationalising: a disabled code-scanning feature refuses with <code>403</code>, a disabled secret-scanning feature refuses with <code>404</code>, and issues endpoints on a repository with issues switched off answer <code>410 Gone</code>. Three status codes, one cause. The 404 is the most costly of the three, because it sends people to look for a missing repository, and the 410 is the second, because it reads as a deprecated endpoint."),
 ("The repository object has no security_and_analysis block at all. Is the feature off?",
  "Unknown, and that is a real answer rather than a hedge. GitHub only returns that block to a caller with admin on the repository, so its absence describes your access, not the repository's configuration. Recording it as disabled would be exactly the mistake this note is about, in the other direction: a confident claim built on a missing grant. Either read the repository with an account that has admin, or ask somebody who does. The plain toggles — <code>has_issues</code>, <code>has_wiki</code> — do come back to any reader, so those are still usable."),
 ("Could the script not just call the alerts endpoint and see what happens?",
  "It can, and <code>--probe</code> does exactly that, because a GET to an alerts endpoint is a read and the same call your job already makes. What the probe cannot do is tell you <em>why</em> it was refused, which is the whole question: a 403 from a disabled feature and a 403 from a missing permission are the same bytes. The flag is the evidence and the probe is corroboration. That is also why the script reports a mismatch when the status you recorded is not the one a disabled feature produces on that endpoint, instead of assuming its own answer."),
 ("The feature is disabled and enabling it is greyed out. What now?",
  "Then the constraint is the plan rather than the checkbox. Advanced Security features on private and internal repositories are only available where the organization's plan includes them, so <code>advanced_security: disabled</code> can mean nobody has enabled it or can mean nobody currently can. The script says which case is possible by looking at <code>private</code> and <code>visibility</code> alongside the flag. The repair then leaves engineering entirely and becomes a billing conversation, which is worth knowing an hour in rather than a fortnight in."),
],
"related": [
 ("/github/collaborator-permission-insufficient/", "Why the security block is missing from your view"),
 ("/github/app-permission-missing/", "When a header does name the permission the endpoint wanted"),
 ("/github/404-masking-403/", "The other reason a read comes back 404"),
],
"citations": [CITE_REPOS, CITE_CODE_SCANNING, CITE_SECRET_SCANNING, CITE_SECURITY_SETTINGS],
},
{
"slug": "fork-vs-upstream-confusion",
"title": "Every call succeeds and reports on a fork, not the upstream",
"description": "fork is true and source.full_name names the repository you meant. Nothing errors, nothing retries, and the audit is entirely accurate about the wrong object.",
"h1": "Every call succeeds and reports on a fork, not the upstream",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api reading fork instead of upstream",
             "github repos fork parent source full_name",
             "github integration pointed at wrong repository",
             "github fork no issues no releases api",
             "github repository id changed same name"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The quarterly report says the platform repository had four merged pull requests, no releases and eleven open issues. It is a repository with nine thousand issues. Nothing failed to produce that report: every call returned 200, the pagination was followed properly, the retries never fired, the JSON parsed. The configuration was copied a year ago from an engineer's personal fork, and a fork is a different repository with its own issues, its own releases and its own branches. The integration has been right about the wrong object for four quarters.",
"short_answer": """<p>Read <code>fork</code> on <code>GET /repos/{owner}/{repo}</code>. When it is <code>true</code>, the same response carries <code>parent.full_name</code> — the repository this one was forked from — and <code>source.full_name</code>, the root of the network. If your integration treats a repository with <code>fork: true</code> as canonical, that is the bug, and <code>source.full_name</code> names what it should have been reading.</p>
<p>There is nothing to catch here. A fork answers every endpoint with a 200 and correct data about itself, so no status code, retry or alert will ever fire. The finding has to come from a reading you take deliberately, before the audit rather than after it.</p>
<p>Then key your stored state on the repository's numeric <code>id</code> rather than on <code>owner/name</code>. A name can come to point at a different object — a repository is deleted and somebody's fork is renamed into the gap, or a rename frees a name that is then taken. The <code>id</code> never moves, so a mismatch between the stored id and the live one is the same bug arriving without anybody having edited a configuration.</p>""",
"problem": """<p>Everything that normally surfaces a misconfiguration is absent. There is no error, so nothing pages anybody. The data is internally consistent, so no validation trips. The numbers are low rather than zero, which is worse than zero would have been: zero looks broken, and four looks like a quiet quarter. And the report is delivered on time every time, which builds confidence in it.</p>
<p>The ways integrations end up here are all mundane. Somebody sets it up from their own fork because that is the URL in their browser while they are working. A repository is transferred to an organization and the old personal copy stays behind, still reachable, still answering. A vendor's onboarding form is filled in by copying a clone URL out of a terminal. A repository gets deleted and a fork is renamed into the same path, so a configuration nobody touched now resolves to a different object.</p>
<p>What finally exposes it is usually an argument about a number. Someone says the release cadence is monthly and the dashboard says there have been no releases at all, and half a day goes into the dashboard's release-fetching code before anybody checks which repository it is fetching them from. By then the report has been believed for a year, which is the real cost: not a failed run, but a stack of accepted conclusions that have to be withdrawn.</p>""",
"why": """<p><strong>A fork is a repository, not a view of one.</strong> It has its own issue list, its own releases, its own labels, milestones, webhooks and branch protection. The only things it shares with its parent are commits and the upstream pointers in the API response. So an integration aimed at a fork is not seeing a partial or stale version of the upstream; it is seeing a different, complete, correct repository that happens to have similar code in it.</p>
<p><strong>Forks are created with issues switched off.</strong> That is why the symptom so often arrives as an empty or erroring issue list rather than as a wrong count — a fork whose owner never enabled issues answers <code>410 Gone</code> on those endpoints, which sends the investigation towards <a href="/github/feature-disabled-endpoint-403/">disabled features</a> and away from the fact that this was never the right repository. Both notes are true at once here, and only one of them is the root cause.</p>
<p><strong><code>parent</code> and <code>source</code> are different fields and they can disagree.</strong> <code>parent</code> is what this repository was forked directly from; <code>source</code> is the root of the whole network. For a fork of a fork they differ, and it is <code>source</code> you almost always want. Reading <code>parent</code> and stopping there repoints the integration one hop closer and leaves it still wrong, which is a particularly annoying way to fix something.</p>
<p><strong>Names are mutable and ids are not.</strong> <code>owner/name</code> is a lookup key that GitHub is free to reassign: renames free the old name, deletions free the whole path, and a rename leaves <a href="/github/repo-renamed-301-redirect/">a redirect that only lasts as long as nothing else claims the name</a>. The numeric <code>id</code> and the <code>node_id</code> are permanent. Storing the id alongside the name costs nothing and turns an undetectable substitution into a mismatch your code can raise.</p>
<p><strong>The size difference is the corroboration a human recognises.</strong> Nobody looks at <code>fork: true</code> and feels anything. Everybody looks at "this repository has 41 stars, the one it was forked from has 12,400, and it was last pushed to nineteen months ago" and knows immediately. So the script reads the upstream too and prints the gap, because the point is not only to be correct but to be believed quickly.</p>
<p><strong>Nothing is written to establish any of this.</strong> That is easy here and worth saying anyway: the whole finding is two repository reads and a comparison of integers, and the repair — repoint the configuration, store the id — happens in your configuration rather than through the API at all.</p>""",
"steps": [
 {"h": "Ask the repository whether it is one",
  "body": """<p>One read of <code>GET /repos/{owner}/{repo}</code> returns <code>fork</code>, and when that is <code>true</code>, <code>parent.full_name</code> and <code>source.full_name</code> beside it. The script reports all three and names <code>source.full_name</code> as the repository the configuration should hold. It prefers <code>source</code> over <code>parent</code> and says so when the two differ, which is the fork-of-a-fork case.</p>"""},
 {"h": "Read the upstream too and print the gap",
  "body": """<p>A second read fetches the repository named by <code>source</code> and prints the difference in stars, open issues, forks and how far behind the fork's last push is. This is the output you can put in front of somebody who set the integration up and get agreement in ten seconds, which is worth one extra request against a quota of five thousand.</p>"""},
 {"h": "Check the stored id against the live one",
  "body": """<p>Pass <code>--expect-id 1296269</code> with whatever your state store recorded and the script compares it to the id the name resolves to now. A mismatch means the name has moved to a different object since you last looked, which is a bug nobody introduced and nothing else will detect. If you have no id stored, the script prints the one to store.</p>"""},
 {"h": "Collect the symptoms that were blamed on something else",
  "body": """<p>The script lists the things about this repository that would make an audit look quiet: issues disabled, no releases, no open issues, a stale <code>pushed_at</code>, a default branch that differs from the upstream's. Seeing them gathered under one cause is what stops the next person debugging the release-fetching code.</p>"""},
 {"h": "Repoint the configuration, and key it on the id",
  "body": """<p>The printed repair names the repository to switch to and the id to store next to it. Nothing is changed by the script — the fix lives in your configuration, not in the API — and once the id is stored, the same run catches the next silent substitution instead of reporting a quiet quarter.</p>"""},
],
"verify": """<p>After repointing, the same run reports a root repository whose id matches the one you stored.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_fork_or_upstream.py \\
    jsmith/platform-core --expect-id 20221
# read cost: 2 request(s) against the core hourly quota
# jsmith/platform-core: fork=True id=904113 pushed_at=2025-01-14T09:22:10Z
#   parent=octo-org/platform-core source=octo-org/platform-core
# fork-as-canonical: this repository has fork=true, so it is a separate
#   repository with its own issues, releases and branches. The integration is
#   reading it as if it were octo-org/platform-core.
# id-drift: the stored id is 20221 and this name now resolves to 904113.
# gap against octo-org/platform-core: stars 41 vs 12400, open issues 0 vs 9134,
#   forks 0 vs 1875, last push 592 day(s) behind
# quiet-audit-explained: issues are disabled on this fork; no open issues; no
#   releases; pushed_at is over a year old
# repair: point the integration at octo-org/platform-core and store its id
#   20221 beside the name, so a future rename or substitution is a mismatch
#   rather than a quiet quarter.</code></pre>""",
"code_intro": "There is no error to classify here, so the script compares objects instead of responses. One read establishes what the configured repository is; a second reads the repository <code>source</code> names, and the difference between them is printed in units a person recognises rather than in booleans. The id comparison is the part worth keeping in your own code afterwards: it is three lines, it costs nothing, and it is the only thing that catches the version of this bug where the configuration was right when it was written.",
"py_file": "github_fork_or_upstream.py",
"py": '''"""Say whether the configured repository is a fork of the one you meant.

Read only. GET requests and nothing else. There is nothing to attempt here in
any case: the failure mode of this bug is that everything succeeds, so the
finding comes from reading two repositories and comparing them rather than from
catching anything.

The point of the note: a fork is a separate repository with its own issues,
releases and branches. An integration pointed at one answers every call with a
200 and is accurate about the wrong object, so no status code, retry or alert
will ever fire.

What this can and cannot see: the API says whether a repository is a fork and
what it was forked from. It cannot say what you intended, so the verdict is
"this is a fork and here is the root of its network", and the decision to
repoint stays with you. Nor can it tell you when a name started resolving to a
different object; it can only compare the id you stored against the id now.

Environment:

    GITHUB_TOKEN    a token with read access to the repositories
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_fork_or_upstream")

API = "https://api.github.com"
UA = "github-fork-or-upstream/1.0"

# Gaps large enough that a human recognises the mistake immediately. These are
# presentation thresholds, not truth: fork=true is the finding either way.
STAR_RATIO_OBVIOUS = 10
PUSH_DAYS_OBVIOUS = 90

# GitHub timestamps are RFC 3339 in UTC with a literal Z. Python 3.9's
# fromisoformat does not accept the Z, so parse the exact shape rather than
# depending on a version difference nobody will reproduce locally.
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def read_cost(with_upstream=True, with_releases=False):
    """Requests this run will spend against the core quota. Pure."""
    cost = 1
    if with_upstream:
        cost += 1
    if with_releases:
        cost += 2 if with_upstream else 1
    return cost


def parse_ts(value):
    """One GitHub timestamp to a datetime, or None. Pure."""
    try:
        return datetime.strptime(str(value), TS_FORMAT)
    except (TypeError, ValueError):
        return None


def days_between(earlier, later):
    """Whole days from one timestamp to another, or None. Pure."""
    a, b = parse_ts(earlier), parse_ts(later)
    if a is None or b is None:
        return None
    return (b - a).days


def is_fork(repo):
    """The one boolean the whole note turns on. Pure."""
    return bool((repo or {}).get("fork"))


def upstream_of(repo):
    """The repository this one should probably have been. Pure.

    source is the root of the fork network and parent is one hop up. They
    differ for a fork of a fork, and it is source you almost always want:
    repointing at parent moves the integration one hop closer and leaves it
    wrong, which is a maddening way to fix something.
    """
    repo = repo or {}
    source = (repo.get("source") or {}).get("full_name")
    parent = (repo.get("parent") or {}).get("full_name")
    return source or parent or None


def fork_chain(repo):
    """parent and source as they were reported, for the fork-of-fork case. Pure."""
    repo = repo or {}
    return {
        "parent": (repo.get("parent") or {}).get("full_name"),
        "source": (repo.get("source") or {}).get("full_name"),
    }


def classify(repo, expected_id=None):
    """Sort the configured repository. Pure. Returns (state, detail).

    id drift is checked before the fork question because it is the case where
    nobody changed anything: a name that used to resolve to one object now
    resolves to another, and no amount of reading the configuration finds it.
    """
    repo = repo or {}
    live_id = repo.get("id")
    if expected_id not in (None, "") and live_id is not None:
        try:
            if int(expected_id) != int(live_id):
                return ("id-drift",
                        "the stored id is %s and this name now resolves to %s. "
                        "The name has moved to a different object since you "
                        "last looked, which nothing else will detect."
                        % (expected_id, live_id))
        except (TypeError, ValueError):
            pass
    if not repo:
        return ("unknown", "no repository object was read.")
    chain = fork_chain(repo)
    if is_fork(repo):
        if chain["parent"] and chain["source"] and chain["parent"] != chain["source"]:
            return ("fork-of-fork",
                    "this is a fork of %s, which is itself a fork. The root of "
                    "the network is %s and that is almost certainly the "
                    "repository you want."
                    % (chain["parent"], chain["source"]))
        return ("fork-as-canonical",
                "this repository has fork=true, so it is a separate repository "
                "with its own issues, releases and branches. Every call against "
                "it succeeds and describes it rather than %s."
                % (upstream_of(repo) or "the upstream"))
    return ("canonical",
            "fork=false, so this is a root repository and not a copy of "
            "something else.")


def divergence(fork, source):
    """The size difference between two repositories, in units people feel. Pure."""
    fork, source = fork or {}, source or {}

    def gap(key):
        a, b = fork.get(key), source.get(key)
        if a is None or b is None:
            return None
        return {"fork": a, "upstream": b, "difference": b - a}

    behind = days_between(fork.get("pushed_at"), source.get("pushed_at"))
    stars_fork = fork.get("stargazers_count") or 0
    stars_up = source.get("stargazers_count") or 0
    return {
        "stargazers_count": gap("stargazers_count"),
        "open_issues_count": gap("open_issues_count"),
        "forks_count": gap("forks_count"),
        "pushed_days_behind": behind,
        "default_branch": {"fork": fork.get("default_branch"),
                           "upstream": source.get("default_branch")},
        "obvious": bool(
            (stars_up >= STAR_RATIO_OBVIOUS * max(1, stars_fork))
            or (behind is not None and behind >= PUSH_DAYS_OBVIOUS)),
    }


def quiet_audit_reasons(repo, releases=None):
    """Why an audit of this repository would look uneventful. Pure.

    Every one of these gets blamed on something else when it arrives alone. The
    value is in seeing them gathered under one cause.
    """
    repo = repo or {}
    reasons = []
    if repo.get("has_issues") is False:
        reasons.append("issues are disabled on this fork, so issue endpoints "
                       "answer 410 rather than an empty list")
    if (repo.get("open_issues_count") or 0) == 0:
        reasons.append("no open issues")
    if releases == 0:
        reasons.append("no releases")
    if (repo.get("forks_count") or 0) == 0:
        reasons.append("nothing has forked it")
    if repo.get("archived"):
        reasons.append("the repository is archived")
    return reasons


def repair(state, repo, expected_id=None):
    """The sentence a reader has to act on. Pure."""
    upstream = upstream_of(repo)
    live_id = (repo or {}).get("id")
    if state in ("fork-as-canonical", "fork-of-fork"):
        return ("point the integration at %s and store its id beside the name, "
                "so a future rename or substitution is a mismatch rather than a "
                "quiet quarter." % (upstream or "the repository named by source"))
    if state == "id-drift":
        return ("stop trusting the name. It resolves to id %s today and your "
                "store says %s, so confirm which object you meant and rekey the "
                "state on the id." % (live_id, expected_id))
    if state == "canonical":
        return ("nothing on the fork question. Store id %s alongside the name "
                "anyway; it is the only key that survives a rename."
                % (live_id,))
    return "read the repository first; there is nothing to judge yet."


def get(session, path):
    """One GET. Returns the response object."""
    r = session.get(API + path, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    return r


def release_count(session, full_name):
    """0, 1-or-more, or None if it could not be read. Cheap on purpose."""
    r = get(session, "/repos/%s/releases?per_page=1" % full_name)
    if r.status_code != 200:
        return None
    try:
        return len(r.json())
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", help="owner/name the integration is configured with")
    ap.add_argument("--expect-id", default="",
                    help="the repository id your state store recorded")
    ap.add_argument("--no-upstream", action="store_true",
                    help="skip the second read of the upstream repository")
    ap.add_argument("--releases", action="store_true",
                    help="also check whether either repository has releases")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2
    if "/" not in args.repo:
        log.error("repo should be owner/name")
        return 2

    log.info("read cost: %d request(s) against the core hourly quota",
             read_cost(not args.no_upstream, args.releases))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    response = get(session, "/repos/" + args.repo)
    if response.status_code != 200:
        log.error("%s: HTTP %s reading the repository", args.repo,
                  response.status_code)
        return 2
    repo = response.json()
    chain = fork_chain(repo)
    log.info("%s: fork=%s id=%s pushed_at=%s", args.repo, repo.get("fork"),
             repo.get("id"), repo.get("pushed_at"))
    log.info("  parent=%s source=%s", chain["parent"], chain["source"])

    state, detail = classify(repo, args.expect_id or None)
    log.info("%s: %s", state, detail)

    gaps = None
    upstream = upstream_of(repo)
    if upstream and not args.no_upstream:
        up = get(session, "/repos/" + upstream)
        if up.status_code == 200:
            gaps = divergence(repo, up.json())
            log.info("gap against %s: stars %s vs %s, open issues %s vs %s, "
                     "forks %s vs %s, last push %s day(s) behind", upstream,
                     (gaps["stargazers_count"] or {}).get("fork"),
                     (gaps["stargazers_count"] or {}).get("upstream"),
                     (gaps["open_issues_count"] or {}).get("fork"),
                     (gaps["open_issues_count"] or {}).get("upstream"),
                     (gaps["forks_count"] or {}).get("fork"),
                     (gaps["forks_count"] or {}).get("upstream"),
                     gaps["pushed_days_behind"])
        else:
            log.warning("could not read %s: HTTP %s", upstream, up.status_code)

    releases = release_count(session, args.repo) if args.releases else None
    reasons = quiet_audit_reasons(repo, releases)
    if reasons:
        log.info("quiet-audit-explained: %s", "; ".join(reasons))
    log.info("repair: %s", repair(state, repo, args.expect_id or None))

    print(json.dumps({
        "configured": args.repo,
        "id": repo.get("id"),
        "node_id": repo.get("node_id"),
        "fork": repo.get("fork"),
        "chain": chain,
        "upstream": upstream,
        "state": state,
        "detail": detail,
        "divergence": gaps,
        "quiet_audit_reasons": reasons,
        "repair": repair(state, repo, args.expect_id or None),
    }, indent=2, default=str))
    return 1 if state in ("fork-as-canonical", "fork-of-fork", "id-drift") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-fork-or-upstream.mjs",
"js": '''/**
 * Say whether the configured repository is a fork of the one you meant.
 *
 * Read only. GET requests and nothing else, and there is nothing to attempt in
 * any case: the failure mode of this bug is that everything succeeds. A fork is
 * a separate repository with its own issues, releases and branches, so an
 * integration pointed at one answers every call with a 200 and is accurate
 * about the wrong object.
 *
 * Environment:
 *   GITHUB_TOKEN      a token with read access to the repositories
 *   GITHUB_REPO       owner/name the integration is configured with
 *   GITHUB_EXPECT_ID  the repository id your state store recorded
 */
const API = 'https://api.github.com';
const UA = 'github-fork-or-upstream/1.0';

/** Gaps large enough that a human recognises the mistake immediately. */
export const STAR_RATIO_OBVIOUS = 10;
export const PUSH_DAYS_OBVIOUS = 90;

const DAY_MS = 86400000;

/** Requests this run will spend against the core quota. Pure. */
export function readCost(withUpstream = true, withReleases = false) {
  let cost = 1;
  if (withUpstream) cost += 1;
  if (withReleases) cost += withUpstream ? 2 : 1;
  return cost;
}

/** One GitHub timestamp to milliseconds, or null. Pure. */
export function parseTs(value) {
  const ms = Date.parse(String(value ?? ''));
  return Number.isFinite(ms) ? ms : null;
}

/** Whole days from one timestamp to another, or null. Pure. */
export function daysBetween(earlier, later) {
  const a = parseTs(earlier);
  const b = parseTs(later);
  if (a === null || b === null) return null;
  return Math.floor((b - a) / DAY_MS);
}

/** The one boolean the whole note turns on. Pure. */
export function isFork(repo) {
  return Boolean((repo || {}).fork);
}

/** parent and source as they were reported. Pure. */
export function forkChain(repo) {
  const r = repo || {};
  return {
    parent: (r.parent || {}).full_name ?? null,
    source: (r.source || {}).full_name ?? null,
  };
}

/** The repository this one should probably have been. Pure. */
export function upstreamOf(repo) {
  const chain = forkChain(repo);
  return chain.source || chain.parent || null;
}

/** Sort the configured repository. Pure. [state, detail]. */
export function classify(repo, expectedId = null) {
  const r = repo || {};
  const liveId = r.id;
  if (expectedId !== null && expectedId !== undefined && expectedId !== ''
      && liveId !== undefined && liveId !== null
      && Number(expectedId) !== Number(liveId)) {
    return ['id-drift', `the stored id is ${expectedId} and this name now `
      + `resolves to ${liveId}. The name has moved to a different object since `
      + 'you last looked, which nothing else will detect.'];
  }
  if (Object.keys(r).length === 0) return ['unknown', 'no repository object was read.'];
  const chain = forkChain(r);
  if (isFork(r)) {
    if (chain.parent && chain.source && chain.parent !== chain.source) {
      return ['fork-of-fork', `this is a fork of ${chain.parent}, which is `
        + `itself a fork. The root of the network is ${chain.source} and that is `
        + 'almost certainly the repository you want.'];
    }
    return ['fork-as-canonical', 'this repository has fork=true, so it is a '
      + 'separate repository with its own issues, releases and branches. Every '
      + `call against it succeeds and describes it rather than ${upstreamOf(r) || 'the upstream'}.`];
  }
  return ['canonical', 'fork=false, so this is a root repository and not a copy '
    + 'of something else.'];
}

/** The size difference between two repositories. Pure. */
export function divergence(fork, source) {
  const f = fork || {};
  const s = source || {};
  const gap = (key) => {
    const a = f[key];
    const b = s[key];
    if (a === undefined || a === null || b === undefined || b === null) return null;
    return { fork: a, upstream: b, difference: b - a };
  };
  const behind = daysBetween(f.pushed_at, s.pushed_at);
  const starsFork = f.stargazers_count || 0;
  const starsUp = s.stargazers_count || 0;
  return {
    stargazers_count: gap('stargazers_count'),
    open_issues_count: gap('open_issues_count'),
    forks_count: gap('forks_count'),
    pushed_days_behind: behind,
    default_branch: { fork: f.default_branch ?? null, upstream: s.default_branch ?? null },
    obvious: Boolean(starsUp >= STAR_RATIO_OBVIOUS * Math.max(1, starsFork)
      || (behind !== null && behind >= PUSH_DAYS_OBVIOUS)),
  };
}

/** Why an audit of this repository would look uneventful. Pure. */
export function quietAuditReasons(repo, releases = null) {
  const r = repo || {};
  const reasons = [];
  if (r.has_issues === false) {
    reasons.push('issues are disabled on this fork, so issue endpoints answer '
      + '410 rather than an empty list');
  }
  if ((r.open_issues_count || 0) === 0) reasons.push('no open issues');
  if (releases === 0) reasons.push('no releases');
  if ((r.forks_count || 0) === 0) reasons.push('nothing has forked it');
  if (r.archived) reasons.push('the repository is archived');
  return reasons;
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, repo, expectedId = null) {
  const upstream = upstreamOf(repo);
  const liveId = (repo || {}).id;
  if (state === 'fork-as-canonical' || state === 'fork-of-fork') {
    return `point the integration at ${upstream || 'the repository named by source'} `
      + 'and store its id beside the name, so a future rename or substitution is '
      + 'a mismatch rather than a quiet quarter.';
  }
  if (state === 'id-drift') {
    return `stop trusting the name. It resolves to id ${liveId} today and your `
      + `store says ${expectedId}, so confirm which object you meant and rekey `
      + 'the state on the id.';
  }
  if (state === 'canonical') {
    return `nothing on the fork question. Store id ${liveId} alongside the name `
      + 'anyway; it is the only key that survives a rename.';
  }
  return 'read the repository first; there is nothing to judge yet.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repoName = process.env.GITHUB_REPO;
  if (!token || !repoName) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPO');
    process.exitCode = 2;
    return;
  }
  const expectId = process.env.GITHUB_EXPECT_ID || null;
  console.log(`read cost: ${readCost(true)} request(s) against the core hourly quota`);

  const res = await fetch(`${API}/repos/${repoName}`, { headers: headers(token) });
  if (res.status !== 200) {
    console.error(`${repoName}: HTTP ${res.status} reading the repository`);
    process.exitCode = 2;
    return;
  }
  const repo = await res.json();
  const chain = forkChain(repo);
  console.log(`${repoName}: fork=${repo.fork} id=${repo.id} pushed_at=${repo.pushed_at}`);
  console.log(`  parent=${chain.parent} source=${chain.source}`);

  const [state, detail] = classify(repo, expectId);
  console.log(`${state}: ${detail}`);

  let gaps = null;
  const upstream = upstreamOf(repo);
  if (upstream) {
    const up = await fetch(`${API}/repos/${upstream}`, { headers: headers(token) });
    if (up.status === 200) {
      gaps = divergence(repo, await up.json());
      console.log(`gap against ${upstream}: stars `
        + `${gaps.stargazers_count?.fork} vs ${gaps.stargazers_count?.upstream}, `
        + `last push ${gaps.pushed_days_behind} day(s) behind`);
    }
  }

  const reasons = quietAuditReasons(repo);
  if (reasons.length) console.log(`quiet-audit-explained: ${reasons.join('; ')}`);
  console.log(`repair: ${repair(state, repo, expectId)}`);

  console.log(JSON.stringify({
    configured: repoName,
    id: repo.id,
    node_id: repo.node_id,
    fork: repo.fork,
    chain,
    upstream,
    state,
    detail,
    divergence: gaps,
    quiet_audit_reasons: reasons,
    repair: repair(state, repo, expectId),
  }, null, 2));
  process.exitCode = ['fork-as-canonical', 'fork-of-fork', 'id-drift'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fork-of-a-fork case is asserted early because it is where the obvious fix is wrong: repointing at <code>parent</code> when <code>parent</code> and <code>source</code> disagree moves the integration one hop and leaves it reading a fork. Then id drift, which is checked ahead of the fork question in the classifier and has to stay that way, since it is the only case where nobody edited anything and the fork boolean is no help. The divergence tests assert differences rather than states, because the output that convinces a human is a pair of numbers, and the last group is the list of symptoms that get blamed on something else when they arrive one at a time.",
"test_py_file": "test_github_fork_or_upstream.py",
"test_py": '''from github_fork_or_upstream import (
    PUSH_DAYS_OBVIOUS, classify, days_between, divergence, fork_chain, is_fork,
    parse_ts, quiet_audit_reasons, read_cost, repair, upstream_of,
)

FORK = {
    "id": 904113,
    "node_id": "R_kgDONjA",
    "fork": True,
    "has_issues": False,
    "open_issues_count": 0,
    "forks_count": 0,
    "stargazers_count": 41,
    "pushed_at": "2025-01-14T09:22:10Z",
    "default_branch": "master",
    "parent": {"full_name": "octo-org/platform-core"},
    "source": {"full_name": "octo-org/platform-core"},
}
FORK_OF_FORK = dict(FORK, parent={"full_name": "acme/platform-core"},
                    source={"full_name": "octo-org/platform-core"})
UPSTREAM = {
    "id": 20221,
    "fork": False,
    "has_issues": True,
    "open_issues_count": 9134,
    "forks_count": 1875,
    "stargazers_count": 12400,
    "pushed_at": "2026-08-28T17:03:44Z",
    "default_branch": "main",
}


def test_a_fork_is_a_separate_repository_and_that_is_the_finding():
    assert is_fork(FORK) is True
    state, detail = classify(FORK)
    assert state == "fork-as-canonical"
    assert "own issues, releases and branches" in detail
    assert classify(UPSTREAM)[0] == "canonical"


def test_source_is_preferred_over_parent():
    # Repointing at parent when the two disagree moves the integration one hop
    # closer and leaves it reading a fork, which is the annoying half-fix.
    assert upstream_of(FORK_OF_FORK) == "octo-org/platform-core"
    assert fork_chain(FORK_OF_FORK)["parent"] == "acme/platform-core"
    state, detail = classify(FORK_OF_FORK)
    assert state == "fork-of-fork"
    assert "root of the network is octo-org/platform-core" in detail


def test_a_repository_with_no_upstream_reports_none():
    assert upstream_of(UPSTREAM) is None
    assert fork_chain({}) == {"parent": None, "source": None}


def test_id_drift_is_checked_before_the_fork_question():
    # This is the case where nobody changed anything: the name now resolves to
    # a different object, and fork=false is no help at all.
    state, detail = classify(dict(UPSTREAM, id=88), expected_id=20221)
    assert state == "id-drift"
    assert "20221" in detail and "88" in detail
    assert classify(UPSTREAM, expected_id=20221)[0] == "canonical"
    assert classify(UPSTREAM, expected_id="")[0] == "canonical"


def test_the_gap_is_reported_in_units_a_person_recognises():
    gaps = divergence(FORK, UPSTREAM)
    assert gaps["stargazers_count"] == {"fork": 41, "upstream": 12400,
                                        "difference": 12359}
    assert gaps["open_issues_count"]["difference"] == 9134
    assert gaps["default_branch"] == {"fork": "master", "upstream": "main"}
    assert gaps["obvious"] is True


def test_a_close_copy_is_not_reported_as_obvious():
    near = dict(FORK, stargazers_count=12000, pushed_at="2026-08-27T10:00:00Z")
    gaps = divergence(near, UPSTREAM)
    assert gaps["obvious"] is False
    assert gaps["pushed_days_behind"] < PUSH_DAYS_OBVIOUS


def test_timestamps_are_parsed_and_differenced():
    assert parse_ts("2026-08-28T17:03:44Z") is not None
    assert parse_ts("not a date") is None
    assert parse_ts(None) is None
    assert days_between("2026-08-01T00:00:00Z", "2026-08-28T00:00:00Z") == 27
    assert days_between("nope", "2026-08-28T00:00:00Z") is None


def test_the_quiet_symptoms_are_gathered_under_one_cause():
    reasons = quiet_audit_reasons(FORK, releases=0)
    joined = " ".join(reasons)
    assert "issues are disabled" in joined
    assert "no open issues" in joined
    assert "no releases" in joined
    assert "nothing has forked it" in joined
    assert quiet_audit_reasons(UPSTREAM, releases=3) == []


def test_disabled_issues_on_a_fork_answers_410_not_an_empty_list():
    # The symptom that sends people to the disabled-feature note instead of to
    # the fact that this was never the right repository.
    assert "410" in " ".join(quiet_audit_reasons(FORK))


def test_the_repair_names_the_upstream_and_the_id_to_store():
    fix = repair("fork-as-canonical", FORK)
    assert "octo-org/platform-core" in fix
    assert "store its id" in fix
    drift = repair("id-drift", dict(UPSTREAM, id=88), expected_id=20221)
    assert "88" in drift and "20221" in drift
    assert "survives a rename" in repair("canonical", UPSTREAM)


def test_the_run_costs_two_reads_by_default():
    assert read_cost() == 2
    assert read_cost(False) == 1
    assert read_cost(True, True) == 4
''',
"test_js_file": "github-fork-or-upstream.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  PUSH_DAYS_OBVIOUS, classify, daysBetween, divergence, forkChain, isFork,
  parseTs, quietAuditReasons, readCost, repair, upstreamOf,
} from './github-fork-or-upstream.mjs';

const FORK = {
  id: 904113,
  node_id: 'R_kgDONjA',
  fork: true,
  has_issues: false,
  open_issues_count: 0,
  forks_count: 0,
  stargazers_count: 41,
  pushed_at: '2025-01-14T09:22:10Z',
  default_branch: 'master',
  parent: { full_name: 'octo-org/platform-core' },
  source: { full_name: 'octo-org/platform-core' },
};
const FORK_OF_FORK = {
  ...FORK,
  parent: { full_name: 'acme/platform-core' },
  source: { full_name: 'octo-org/platform-core' },
};
const UPSTREAM = {
  id: 20221,
  fork: false,
  has_issues: true,
  open_issues_count: 9134,
  forks_count: 1875,
  stargazers_count: 12400,
  pushed_at: '2026-08-28T17:03:44Z',
  default_branch: 'main',
};

test('a fork is a separate repository and that is the finding', () => {
  assert.equal(isFork(FORK), true);
  const [state, detail] = classify(FORK);
  assert.equal(state, 'fork-as-canonical');
  assert.match(detail, /own issues, releases and branches/);
  assert.equal(classify(UPSTREAM)[0], 'canonical');
});

test('source is preferred over parent', () => {
  assert.equal(upstreamOf(FORK_OF_FORK), 'octo-org/platform-core');
  assert.equal(forkChain(FORK_OF_FORK).parent, 'acme/platform-core');
  const [state, detail] = classify(FORK_OF_FORK);
  assert.equal(state, 'fork-of-fork');
  assert.match(detail, /root of the network is octo-org\\/platform-core/);
});

test('a repository with no upstream reports none', () => {
  assert.equal(upstreamOf(UPSTREAM), null);
  assert.deepEqual(forkChain({}), { parent: null, source: null });
});

test('id drift is checked before the fork question', () => {
  const [state, detail] = classify({ ...UPSTREAM, id: 88 }, 20221);
  assert.equal(state, 'id-drift');
  assert.match(detail, /20221/);
  assert.match(detail, /88/);
  assert.equal(classify(UPSTREAM, 20221)[0], 'canonical');
  assert.equal(classify(UPSTREAM, '')[0], 'canonical');
});

test('the gap is reported in units a person recognises', () => {
  const gaps = divergence(FORK, UPSTREAM);
  assert.deepEqual(gaps.stargazers_count,
    { fork: 41, upstream: 12400, difference: 12359 });
  assert.equal(gaps.open_issues_count.difference, 9134);
  assert.deepEqual(gaps.default_branch, { fork: 'master', upstream: 'main' });
  assert.equal(gaps.obvious, true);
});

test('a close copy is not reported as obvious', () => {
  const near = { ...FORK, stargazers_count: 12000, pushed_at: '2026-08-27T10:00:00Z' };
  const gaps = divergence(near, UPSTREAM);
  assert.equal(gaps.obvious, false);
  assert.ok(gaps.pushed_days_behind < PUSH_DAYS_OBVIOUS);
});

test('timestamps are parsed and differenced', () => {
  assert.notEqual(parseTs('2026-08-28T17:03:44Z'), null);
  assert.equal(parseTs('not a date'), null);
  assert.equal(daysBetween('2026-08-01T00:00:00Z', '2026-08-28T00:00:00Z'), 27);
  assert.equal(daysBetween('nope', '2026-08-28T00:00:00Z'), null);
});

test('the quiet symptoms are gathered under one cause', () => {
  const reasons = quietAuditReasons(FORK, 0).join(' ');
  assert.match(reasons, /issues are disabled/);
  assert.match(reasons, /no open issues/);
  assert.match(reasons, /no releases/);
  assert.match(reasons, /nothing has forked it/);
  assert.deepEqual(quietAuditReasons(UPSTREAM, 3), []);
});

test('disabled issues on a fork answers 410 not an empty list', () => {
  assert.match(quietAuditReasons(FORK).join(' '), /410/);
});

test('the repair names the upstream and the id to store', () => {
  const fix = repair('fork-as-canonical', FORK);
  assert.match(fix, /octo-org\\/platform-core/);
  assert.match(fix, /store its id/);
  const drift = repair('id-drift', { ...UPSTREAM, id: 88 }, 20221);
  assert.match(drift, /88/);
  assert.match(drift, /20221/);
  assert.match(repair('canonical', UPSTREAM), /survives a rename/);
});

test('the run costs two reads by default', () => {
  assert.equal(readCost(), 2);
  assert.equal(readCost(false), 1);
  assert.equal(readCost(true, true), 4);
});
''',
"faq": [
 ("If everything returns 200, how would anyone ever notice?",
  "Usually from an argument about a number, weeks later. That is the whole problem with this one: there is no failure to alert on, no retry to exhaust, no status code to sort. The report is well formed and internally consistent, so the only thing that exposes it is somebody who knows the repository disagreeing with the output. The defence is to check <code>fork</code> once when the integration is configured and then again on every run, because it costs one field on a call you are already making and it is the only signal the API gives you."),
 ("Why prefer source over parent when they both name a repository?",
  "Because <code>parent</code> is one hop and <code>source</code> is the root. For a plain fork they are identical and it does not matter; for a fork of a fork, repointing at <code>parent</code> takes you to another fork, and you get to discover the same bug again with slightly better numbers. Read <code>source.full_name</code>, and treat a disagreement between the two as worth logging: it tells you the repository you were given is at least two hops from the thing anybody meant."),
 ("Should the integration just refuse to run against a fork?",
  "That depends on what it does, and the script deliberately does not decide for you. Plenty of legitimate integrations target forks — a CI bot for a contributor's copy, a mirror checker, a security scanner sweeping every fork in a network. What is never legitimate is treating a fork as the canonical repository without knowing that is what you are doing. Reporting <code>fork: true</code> alongside the result, so the reader can see which object the numbers describe, is a smaller and more honest change than a refusal."),
 ("The configuration has not changed and it used to be right. How is that possible?",
  "Names are reassignable and ids are not. A repository can be renamed, freeing its old name for anyone to claim; a repository can be deleted, freeing its whole path; and a fork can then be renamed into the gap. Your configuration still says <code>owner/name</code>, that name still resolves, and it now resolves to a different object. Nothing in the response announces the substitution. Store the numeric <code>id</code> next to the name, compare it on every run, and this becomes a mismatch you can raise instead of a quarter you have to withdraw."),
 ("Why does the fork have no issues at all rather than a shorter list?",
  "Because forks are created with issues switched off. The endpoints then answer <code>410 Gone</code> rather than an empty array, which reads like a deprecated API and sends the investigation somewhere else entirely. It is worth knowing that both things are true at once here: the feature really is disabled, and the deeper cause is that this was never the repository you wanted. Fixing the feature would give you an empty issue list on a fork, which is a more convincing wrong answer than the error was."),
],
"related": [
 ("/github/repo-renamed-301-redirect/", "The other way a repository name stops meaning what it did"),
 ("/github/private-repo-visibility-changed/", "When the upstream disappears from an anonymous reader"),
 ("/github/installation-repository-selection-partial/", "An audit that reports its own coverage"),
],
"citations": [CITE_REPOS, CITE_FORKS_ABOUT, CITE_FORKS_REST, CITE_FORK_PERMISSIONS],
},
{
"slug": "private-repo-visibility-changed",
"title": "A repository went private and anonymous callers now see 404",
"description": "The same URL answers 200 with a token and 404 without one. That pair is the visibility change; deletion answers 404 both ways and a rename answers 301.",
"h1": "A repository went private and anonymous callers now see 404",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github repo went private 404 api",
             "github repository visibility changed integration broke",
             "github public repo now private unauthenticated 404",
             "github visibility internal private difference api",
             "github anonymous api 404 private repository"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The dependency dashboard has read one repository's tags and release notes since 2019, anonymously, because it is a public repository and there was never any reason to authenticate. On a Tuesday it starts returning <code>404</code>. Nothing was deployed, no code changed, the URL is character-for-character the one that worked on Monday. Somebody checks whether the repository was deleted, finds it in their browser because their browser is logged in, and now has two contradictory facts and no idea which to believe.",
"short_answer": """<p>Take two readings of the same URL and compare them. <code>GET /repos/{owner}/{repo}</code> with a token that still has access, and the same call with no credential at all. A <code>200</code> authenticated beside a <code>404</code> anonymous is a repository that is no longer public. Neither half proves it alone, which is why one reading has kept people arguing.</p>
<p>The authenticated response then says which state it moved to: <code>private: true</code> with <code>visibility</code> of <code>private</code> or <code>internal</code>. Those two are not the same and the boolean cannot tell them apart — an internal repository is readable by every member of the enterprise and reports <code>private: true</code> exactly like a private one.</p>
<p>The repair is a credential, not a URL. A classic token needs the <code>repo</code> scope, because <code>public_repo</code> covers precisely what has just stopped being true; a fine-grained token needs <code>Metadata: Read</code> plus <code>Contents: Read</code> on that repository, granted by its owner. And <code>GET /rate_limit</code>, which is free, tells you whether your client was ever authenticated at all: a <code>core.limit</code> of 60 means it was not.</p>""",
"problem": """<p>The status code is the problem. GitHub answers <code>404</code> rather than <code>403</code> for a private resource a caller cannot see, deliberately, so that error codes cannot be used to enumerate repositories that exist. The consequence is that "this repository is now private" and "this repository was deleted" arrive as the same bytes, and a client has no way to tell them apart from its own side of the call.</p>
<p>What follows is a specific and unproductive argument. One person, logged in, opens the URL in a browser and sees the repository. The dashboard, which is not logged in, insists it is gone. Both are right. The disagreement usually resolves as "the API is flaky" or "GitHub deleted it and restored it", and the integration gets a retry loop, or gets pointed at a mirror, or gets quietly disabled.</p>
<p>The forks make it worse. When a public repository becomes private, the forks that already existed are split off into a network of their own and stay public, so search results and vendored links still find something that looks like the repository. A dependency tool that follows one of those is now tracking a copy that has stopped receiving upstream commits, which produces a second, slower failure a month later.</p>
<p>And the anonymity is often accidental. Plenty of clients were written against public repositories, never given a token, and then inherited by somebody who assumes there is one, because there is a <code>GITHUB_TOKEN</code> in the environment somewhere. Checking that assumption is one free call and it is almost never made.</p>""",
"why": """<p><strong>Going private removes anonymous access completely.</strong> Not partially, not for some endpoints. An unauthenticated client sees the same 404 for a private repository as it does for one that never existed. That is a design decision rather than an oversight, and it means the only way to distinguish the cases is to bring a credential that does have access and take a second reading.</p>
<p><strong>Two readings are the evidence, and each alone is ambiguous.</strong> An anonymous 404 by itself is consistent with deletion, with a typo, with a rename, and with going private. An authenticated 200 by itself just says you can read it. Together they say: this exists, and it is not public. That pair is what this note is for, and it is the reading the general <a href="/github/404-masking-403/">404 triage</a> does not take, because that note is answering a wider question for a caller who may never have had access at all.</p>
<p><strong><code>private</code> and <code>visibility</code> are not the same field.</strong> An internal repository — visible to every member of an enterprise, invisible to the public — reports <code>private: true</code>. A client keying on the boolean sees internal and private as identical, and they have different repairs: internal access is granted by enterprise membership, private access by a per-repository grant. Read <code>visibility</code>, which has three values, and keep the boolean for backwards compatibility only.</p>
<p><strong><code>public_repo</code> is the scope that describes what just changed.</strong> A classic token holding <code>public_repo</code> can read every public repository and no private one, so it is exactly as blind as no token at all here. The upgrade is <code>repo</code>, which is read and write together and is <a href="/github/over-scoped-token/">more authority than a reader needs</a>; a fine-grained token with <code>Metadata: Read</code> and <code>Contents: Read</code> on that one repository is the narrower credential and the better answer.</p>
<p><strong>The moment of the change is not readable, and pretending otherwise would be worse than not knowing.</strong> There is no visibility-changed timestamp on the repository object. <code>updated_at</code> moves for a dozen unrelated reasons, and the organization audit log, which does record it, needs <code>admin:org</code>-class access that a repository-scoped reader does not have. So the honest finding is the current asymmetry, plus whatever your own logs say about when the 404s started. The script reports the state, not a date it cannot see.</p>
<p><strong>Every part of this is a read, including the anonymous one.</strong> Two GETs against the repository and one free <code>GET /rate_limit</code>. The anonymous call is billed to the unauthenticated bucket for your IP address, which is 60 an hour and shared with anything else on that address, so the script says so before spending one.</p>""",
"steps": [
 {"h": "Read the URL twice, once with the token and once with nothing",
  "body": """<p>The script sends <code>GET /repos/{owner}/{repo}</code> authenticated, then sends the identical call from a session carrying no <code>Authorization</code> header at all. Two reads, and the pair of status codes is the finding. It prints both before interpreting either, so you can see the asymmetry yourself rather than take the verdict on trust.</p>"""},
 {"h": "Confirm your client really is anonymous",
  "body": """<p><code>GET /rate_limit</code> costs nothing and reports <code>core.limit</code> as 60 for an unauthenticated caller and 5,000 for an authenticated one. That single number settles the question people spend an afternoon on: whether the failing integration was ever sending a credential. It is checked for both sessions, because a token that has expired authenticates as nobody and produces the anonymous limit.</p>"""},
 {"h": "Read the state it moved to, not just the boolean",
  "body": """<p>The authenticated response carries <code>visibility</code> with three possible values. The script reports it beside <code>private</code> and names them separately, because <code>internal</code> is <code>private: true</code> with a completely different repair: enterprise membership rather than a repository grant.</p>"""},
 {"h": "Rule out deletion and renaming explicitly",
  "body": """<p>404 on both readings is not this note, and the script says so rather than guessing: it hands you to the wider 404 triage, because a repository you cannot see with any credential is either gone or was never granted to you. A <code>301</code> on either reading is a rename and belongs somewhere else again. Only the asymmetric pair is reported as a visibility change.</p>"""},
 {"h": "Take the repair to the credential, and pick the narrow one",
  "body": """<p>The printed repair names what the client needs: <code>repo</code> for a classic token, or <code>Metadata: Read</code> and <code>Contents: Read</code> on that repository for a fine-grained one, with the owner granting access. If the client is holding <code>public_repo</code> the script names that specifically, because it is the scope that looks like it should work and cannot. Nothing is changed by the script.</p>"""},
],
"verify": """<p>Once the client carries a credential with access, the two readings stop disagreeing in the way that matters and the state is reported rather than inferred.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_visibility_change.py \\
    octo-org/schema-registry
# read cost: 2 request(s) against the core hourly quota, plus 2 free
#   /rate_limit calls. One of the reads is anonymous and is billed to the
#   unauthenticated bucket for this IP address, which is 60 an hour.
# authenticated: HTTP 200  core.limit=5000
# anonymous:     HTTP 404  core.limit=60
# octo-org/schema-registry: private=True visibility=private
# went-private: the repository is readable with a token and invisible without
#   one, so it exists and is no longer public. Deletion would answer 404 to
#   both readings.
# forks-note: forks that existed while it was public were split into their own
#   network and are still public, so a link that still resolves may be a copy
#   that stopped receiving commits.
# blind-spot: no visibility-changed timestamp is exposed to a reader, and the
#   audit log that records it needs org-level access. When it happened is in
#   your own logs, not in this response.
# repair: give the client the repo scope (classic) or Metadata: Read and
#   Contents: Read on this repository (fine-grained), granted by the owner.
#   public_repo covers exactly what has stopped being true.</code></pre>""",
"code_intro": "The unusual part of this script is the session that carries no credential. It is built deliberately and kept separate from the authenticated one, because the whole method is a comparison between two callers and mixing them would silently destroy the finding. Everything after the two reads is a small classifier over a pair of status codes plus the <code>visibility</code> field, with the ambiguous combinations named as ambiguous rather than resolved: 404 to both readings is handed to the wider triage, and a 301 anywhere is a rename and somebody else's note.",
"py_file": "github_visibility_change.py",
"py": '''"""Tell a repository that went private apart from one that was deleted.

Read only. GET requests and nothing else, and one of them carries no credential
at all: the method here is a comparison between two callers reading the same
URL, so the anonymous session is built on purpose and kept separate from the
authenticated one.

The point of the note: making a repository private removes anonymous access
entirely, and GitHub answers 404 rather than 403 so that error codes cannot be
used to enumerate resources. A client that read the repository anonymously for
years therefore sees exactly what it would see if the repository had been
deleted. One reading cannot separate those. Two can.

What this can and cannot see: there is no visibility-changed timestamp on the
repository object. updated_at moves for unrelated reasons and the audit log
that records the change needs organization-level access. So this reports the
current asymmetry and never a date it cannot read.

Environment:

    GITHUB_TOKEN    a token that still has access to the repository
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_visibility_change")

API = "https://api.github.com"
UA = "github-visibility-change/1.0"

# The unauthenticated core quota, per IP address. Reading this number is how a
# client proves whether it is authenticated at all, and the read is free.
ANONYMOUS_CORE_LIMIT = 60

# The three values of `visibility`. `private` the boolean is true for two of
# them, which is why a client keying on the boolean cannot tell them apart.
VISIBILITIES = ("public", "private", "internal")

# The classic scope that describes exactly what has stopped being true.
BLIND_SCOPE = "public_repo"
PRIVATE_SCOPE = "repo"

# What a fine-grained token needs instead, on that one repository.
FINE_GRAINED_PERMISSIONS = ("Metadata: Read", "Contents: Read")


def read_cost():
    """Billable requests this run spends against the core quota. Pure.

    Two repository reads. The two /rate_limit calls are free and one of the
    repository reads is billed to the unauthenticated bucket for this IP
    address rather than to the token.
    """
    return 2


def client_is_anonymous(core_limit):
    """Was this caller authenticated. Pure.

    A limit of 60 is the unauthenticated bucket. An expired or revoked token
    authenticates as nobody and produces the same number, which is why this is
    a better question than "is a token set in the environment".
    """
    try:
        return int(core_limit) <= ANONYMOUS_CORE_LIMIT
    except (TypeError, ValueError):
        return None


def visibility_of(repo):
    """The three-valued visibility, falling back to the boolean. Pure."""
    repo = repo or {}
    value = str(repo.get("visibility") or "").strip().lower()
    if value in VISIBILITIES:
        return value
    if repo.get("private") is True:
        return "private"
    if repo.get("private") is False:
        return "public"
    return "unreported"


def scope_list(header_value):
    """Read x-oauth-scopes into a list, keeping absent and empty apart. Pure."""
    if header_value is None:
        return None
    return [s.strip() for s in header_value.split(",") if s.strip()]


def scope_gap(scopes, visibility):
    """Is the client's scope set exactly the wrong shape for this. Pure.

    Returns (state, detail). public_repo is the interesting one: it grants
    every public repository and no private one, so it is precisely as useful
    as no token at all once the repository stops being public.
    """
    if visibility == "public":
        return ("not-applicable",
                "the repository is public, so no scope is required to read it.")
    if scopes is None:
        return ("no-scopes-reported",
                "this credential reports no OAuth scopes, so it is a "
                "fine-grained or App token. It needs %s on this repository, "
                "granted by the owner." % ", ".join(FINE_GRAINED_PERMISSIONS))
    if PRIVATE_SCOPE in scopes:
        return ("scope-sufficient",
                "the token carries '%s', which covers a private repository. If "
                "it still cannot read this one, the account behind it has no "
                "grant on the repository." % PRIVATE_SCOPE)
    if BLIND_SCOPE in scopes:
        return ("blind-scope",
                "the token carries '%s' and not '%s'. That scope grants every "
                "public repository and no private one, so it is exactly as "
                "blind here as sending no token at all."
                % (BLIND_SCOPE, PRIVATE_SCOPE))
    return ("scope-insufficient",
            "the token carries %s, none of which reaches a private repository. "
            "It needs '%s'." % (", ".join(scopes) or "no scopes at all",
                                PRIVATE_SCOPE))


def classify(anon_status, auth_status, repo=None):
    """Sort a pair of readings of one URL. Pure. Returns (state, detail).

    The ambiguous combinations are named as ambiguous. Resolving them here
    would be the same mistake the 404 makes, committed on purpose.
    """
    visibility = visibility_of(repo)
    if str(anon_status) == "301" or str(auth_status) == "301":
        return ("moved",
                "a 301 means the repository was renamed or transferred and a "
                "redirect was left behind. That is a different note; follow it "
                "once and rewrite your configuration.")
    if auth_status == 200 and anon_status == 404:
        if visibility == "internal":
            return ("internal-visibility",
                    "the repository is internal: private=true, but readable by "
                    "every member of the enterprise rather than by a named list. "
                    "A client keying on the private boolean cannot see that "
                    "difference, and the repair for it is membership rather "
                    "than a repository grant.")
        return ("went-private",
                "the repository is readable with a token and invisible without "
                "one, so it exists and is no longer public. Deletion would "
                "answer 404 to both readings.")
    if auth_status == 200 and anon_status == 200:
        return ("still-public",
                "both readings succeeded, so visibility is not what broke. The "
                "404 your client recorded has another cause.")
    if auth_status == 404 and anon_status == 404:
        return ("invisible-to-both",
                "neither reading can see it, so this is deletion or an account "
                "that was never granted access. That is the wider 404 triage "
                "and not this note.")
    if auth_status != 200 and anon_status == 200:
        return ("token-is-the-problem",
                "the anonymous read succeeded and the authenticated one did "
                "not, so the repository is public and the credential is "
                "failing. Check whether the token is expired or revoked.")
    return ("unclassified",
            "authenticated %s and anonymous %s is not a combination this sorts. "
            "Report both codes before drawing a conclusion."
            % (auth_status, anon_status))


def fork_fallout(repo):
    """The second, slower failure this change produces. Pure, or None.

    Forks that existed while the repository was public are split into their own
    network and stay public. Something that looks like the repository therefore
    still resolves, and a tool that follows it starts tracking a copy that no
    longer receives commits.
    """
    repo = repo or {}
    if visibility_of(repo) == "public":
        return None
    if (repo.get("forks_count") or 0) <= 0:
        return None
    return ("forks that existed while it was public were split into their own "
            "network and are still public, so a link that still resolves may be "
            "a copy that stopped receiving commits.")


def blind_spot():
    """What this cannot establish, said out loud. Pure."""
    return ("no visibility-changed timestamp is exposed to a reader, and the "
            "audit log that records it needs organization-level access. When it "
            "happened is in your own logs, not in this response.")


def repair(state, scope_state=None):
    """The sentence a reader has to act on. Pure."""
    credential = ("give the client the '%s' scope (classic) or %s on this "
                  "repository (fine-grained), granted by the owner."
                  % (PRIVATE_SCOPE, " and ".join(FINE_GRAINED_PERMISSIONS)))
    if state == "went-private":
        text = credential
        if scope_state == "blind-scope":
            text += (" The scope it holds now, '%s', covers exactly what has "
                     "stopped being true." % BLIND_SCOPE)
        return text
    if state == "internal-visibility":
        return ("the repository is internal, so access follows enterprise "
                "membership. A machine account has to be a member of the "
                "enterprise, and after that " + credential)
    if state == "invisible-to-both":
        return ("stop here and run the wider 404 triage. Nothing about "
                "visibility can be established when no credential can see it.")
    if state == "still-public":
        return ("look elsewhere. The repository is public and readable "
                "anonymously, so the 404 came from something other than "
                "visibility.")
    if state == "token-is-the-problem":
        return ("check the credential rather than the repository. An expired "
                "or revoked token authenticates as nobody.")
    if state == "moved":
        return ("follow the redirect once, take full_name from the response, "
                "and store the repository id so the next rename is not a "
                "surprise either.")
    return "report both status codes before drawing a conclusion."


def core_limit(session):
    """core.limit for whichever caller this session is. Free to read."""
    r = session.get(API + "/rate_limit", timeout=30)
    if r.status_code != 200:
        return None
    try:
        return ((r.json().get("resources") or {}).get("core") or {}).get("limit")
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", help="owner/name of the repository that started 404ing")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token with access is enough)")
        return 2
    if "/" not in args.repo:
        log.error("repo should be owner/name")
        return 2

    log.info("read cost: %d request(s) against the core hourly quota, plus 2 "
             "free /rate_limit calls. One of the reads is anonymous and is "
             "billed to the unauthenticated bucket for this IP address, which "
             "is %d an hour.", read_cost(), ANONYMOUS_CORE_LIMIT)

    common = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    }
    authed = requests.Session()
    authed.headers.update(dict(common, Authorization="Bearer " + token))
    # Deliberately credential-free. The whole method is a comparison between
    # two callers, so this session must never acquire an Authorization header.
    anon = requests.Session()
    anon.headers.update(common)

    auth_limit = core_limit(authed)
    anon_limit = core_limit(anon)

    auth_response = authed.get(API + "/repos/" + args.repo, timeout=30,
                               allow_redirects=False)
    anon_response = anon.get(API + "/repos/" + args.repo, timeout=30,
                             allow_redirects=False)
    log.info("authenticated: HTTP %s  core.limit=%s", auth_response.status_code,
             auth_limit)
    log.info("anonymous:     HTTP %s  core.limit=%s", anon_response.status_code,
             anon_limit)
    if client_is_anonymous(auth_limit):
        log.warning("the authenticated session reports the unauthenticated "
                    "limit, so GITHUB_TOKEN is expired, revoked or not being "
                    "sent. Fix that before reading anything else here.")

    repo = None
    scopes = scope_list(auth_response.headers.get("x-oauth-scopes"))
    if auth_response.status_code == 200:
        repo = auth_response.json()
        log.info("%s: private=%s visibility=%s", args.repo, repo.get("private"),
                 visibility_of(repo))

    state, detail = classify(anon_response.status_code,
                             auth_response.status_code, repo)
    log.info("%s: %s", state, detail)
    scope_state, scope_detail = scope_gap(scopes, visibility_of(repo))
    log.info("%s: %s", scope_state, scope_detail)
    fallout = fork_fallout(repo)
    if fallout:
        log.info("forks-note: %s", fallout)
    log.info("blind-spot: %s", blind_spot())
    log.info("repair: %s", repair(state, scope_state))

    print(json.dumps({
        "repository": args.repo,
        "authenticated_status": auth_response.status_code,
        "anonymous_status": anon_response.status_code,
        "authenticated_core_limit": auth_limit,
        "anonymous_core_limit": anon_limit,
        "client_was_anonymous": client_is_anonymous(auth_limit),
        "private": (repo or {}).get("private"),
        "visibility": visibility_of(repo),
        "scopes": scopes,
        "state": state,
        "detail": detail,
        "scope_state": scope_state,
        "forks_note": fallout,
        "blind_spot": blind_spot(),
        "repair": repair(state, scope_state),
    }, indent=2, default=str))
    return 1 if state in ("went-private", "internal-visibility") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-visibility-change.mjs",
"js": '''/**
 * Tell a repository that went private apart from one that was deleted.
 *
 * Read only. GET requests and nothing else, and one of them carries no
 * credential at all: the method is a comparison between two callers reading the
 * same URL, so the anonymous request is made on purpose and never given an
 * Authorization header.
 *
 * Making a repository private removes anonymous access entirely, and GitHub
 * answers 404 rather than 403 so error codes cannot enumerate resources. A
 * client that read it anonymously for years sees exactly what it would see if
 * the repository had been deleted. One reading cannot separate those; two can.
 *
 * Environment:
 *   GITHUB_TOKEN    a token that still has access to the repository
 *   GITHUB_REPO     owner/name of the repository that started 404ing
 */
const API = 'https://api.github.com';
const UA = 'github-visibility-change/1.0';

/** The unauthenticated core quota, per IP address. Free to read. */
export const ANONYMOUS_CORE_LIMIT = 60;

/** The three values of visibility. The boolean is true for two of them. */
export const VISIBILITIES = ['public', 'private', 'internal'];

/** The classic scope that describes exactly what has stopped being true. */
export const BLIND_SCOPE = 'public_repo';
export const PRIVATE_SCOPE = 'repo';

/** What a fine-grained token needs instead, on that one repository. */
export const FINE_GRAINED_PERMISSIONS = ['Metadata: Read', 'Contents: Read'];

/** Billable requests this run spends against the core quota. Pure. */
export function readCost() {
  return 2;
}

/** Was this caller authenticated. Pure. */
export function clientIsAnonymous(coreLimit) {
  if (coreLimit === null || coreLimit === undefined || coreLimit === '') return null;
  const n = Number(coreLimit);
  if (!Number.isFinite(n)) return null;
  return n <= ANONYMOUS_CORE_LIMIT;
}

/** The three-valued visibility, falling back to the boolean. Pure. */
export function visibilityOf(repo) {
  const r = repo || {};
  const value = String(r.visibility ?? '').trim().toLowerCase();
  if (VISIBILITIES.includes(value)) return value;
  if (r.private === true) return 'private';
  if (r.private === false) return 'public';
  return 'unreported';
}

/** Read x-oauth-scopes into a list, keeping absent and empty apart. Pure. */
export function scopeList(headerValue) {
  if (headerValue === null || headerValue === undefined) return null;
  return String(headerValue).split(',').map((s) => s.trim()).filter(Boolean);
}

/** Is the client's scope set exactly the wrong shape for this. Pure. */
export function scopeGap(scopes, visibility) {
  if (visibility === 'public') {
    return ['not-applicable', 'the repository is public, so no scope is '
      + 'required to read it.'];
  }
  if (scopes === null || scopes === undefined) {
    return ['no-scopes-reported', 'this credential reports no OAuth scopes, so '
      + `it is a fine-grained or App token. It needs ${FINE_GRAINED_PERMISSIONS.join(', ')} `
      + 'on this repository, granted by the owner.'];
  }
  if (scopes.includes(PRIVATE_SCOPE)) {
    return ['scope-sufficient', `the token carries '${PRIVATE_SCOPE}', which `
      + 'covers a private repository. If it still cannot read this one, the '
      + 'account behind it has no grant on the repository.'];
  }
  if (scopes.includes(BLIND_SCOPE)) {
    return ['blind-scope', `the token carries '${BLIND_SCOPE}' and not `
      + `'${PRIVATE_SCOPE}'. That scope grants every public repository and no `
      + 'private one, so it is exactly as blind here as sending no token at all.'];
  }
  return ['scope-insufficient', `the token carries ${scopes.join(', ') || 'no scopes at all'}, `
    + `none of which reaches a private repository. It needs '${PRIVATE_SCOPE}'.`];
}

/** Sort a pair of readings of one URL. Pure. [state, detail]. */
export function classify(anonStatus, authStatus, repo = null) {
  const visibility = visibilityOf(repo);
  if (String(anonStatus) === '301' || String(authStatus) === '301') {
    return ['moved', 'a 301 means the repository was renamed or transferred and '
      + 'a redirect was left behind. That is a different note; follow it once '
      + 'and rewrite your configuration.'];
  }
  if (authStatus === 200 && anonStatus === 404) {
    if (visibility === 'internal') {
      return ['internal-visibility', 'the repository is internal: private=true, '
        + 'but readable by every member of the enterprise rather than by a named '
        + 'list. A client keying on the private boolean cannot see that '
        + 'difference, and the repair for it is membership rather than a '
        + 'repository grant.'];
    }
    return ['went-private', 'the repository is readable with a token and '
      + 'invisible without one, so it exists and is no longer public. Deletion '
      + 'would answer 404 to both readings.'];
  }
  if (authStatus === 200 && anonStatus === 200) {
    return ['still-public', 'both readings succeeded, so visibility is not what '
      + 'broke. The 404 your client recorded has another cause.'];
  }
  if (authStatus === 404 && anonStatus === 404) {
    return ['invisible-to-both', 'neither reading can see it, so this is '
      + 'deletion or an account that was never granted access. That is the wider '
      + '404 triage and not this note.'];
  }
  if (authStatus !== 200 && anonStatus === 200) {
    return ['token-is-the-problem', 'the anonymous read succeeded and the '
      + 'authenticated one did not, so the repository is public and the '
      + 'credential is failing. Check whether the token is expired or revoked.'];
  }
  return ['unclassified', `authenticated ${authStatus} and anonymous `
    + `${anonStatus} is not a combination this sorts. Report both codes before `
    + 'drawing a conclusion.'];
}

/** The second, slower failure this change produces. Pure, or null. */
export function forkFallout(repo) {
  const r = repo || {};
  if (visibilityOf(r) === 'public') return null;
  if ((r.forks_count || 0) <= 0) return null;
  return 'forks that existed while it was public were split into their own '
    + 'network and are still public, so a link that still resolves may be a copy '
    + 'that stopped receiving commits.';
}

/** What this cannot establish, said out loud. Pure. */
export function blindSpot() {
  return 'no visibility-changed timestamp is exposed to a reader, and the audit '
    + 'log that records it needs organization-level access. When it happened is '
    + 'in your own logs, not in this response.';
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, scopeState = null) {
  const credential = `give the client the '${PRIVATE_SCOPE}' scope (classic) or `
    + `${FINE_GRAINED_PERMISSIONS.join(' and ')} on this repository `
    + '(fine-grained), granted by the owner.';
  if (state === 'went-private') {
    let text = credential;
    if (scopeState === 'blind-scope') {
      text += ` The scope it holds now, '${BLIND_SCOPE}', covers exactly what `
        + 'has stopped being true.';
    }
    return text;
  }
  if (state === 'internal-visibility') {
    return 'the repository is internal, so access follows enterprise membership. '
      + 'A machine account has to be a member of the enterprise, and after that '
      + credential;
  }
  if (state === 'invisible-to-both') {
    return 'stop here and run the wider 404 triage. Nothing about visibility can '
      + 'be established when no credential can see it.';
  }
  if (state === 'still-public') {
    return 'look elsewhere. The repository is public and readable anonymously, '
      + 'so the 404 came from something other than visibility.';
  }
  if (state === 'token-is-the-problem') {
    return 'check the credential rather than the repository. An expired or '
      + 'revoked token authenticates as nobody.';
  }
  if (state === 'moved') {
    return 'follow the redirect once, take full_name from the response, and '
      + 'store the repository id so the next rename is not a surprise either.';
  }
  return 'report both status codes before drawing a conclusion.';
}

const COMMON = {
  Accept: 'application/vnd.github+json',
  'X-GitHub-Api-Version': '2022-11-28',
  'User-Agent': UA,
};

async function coreLimit(headers) {
  const res = await fetch(`${API}/rate_limit`, { headers });
  if (!res.ok) return null;
  try {
    const body = await res.json();
    return ((body.resources || {}).core || {}).limit ?? null;
  } catch { return null; }
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repoName = process.env.GITHUB_REPO;
  if (!token || !repoName) {
    console.error('set GITHUB_TOKEN (read-only with access) and GITHUB_REPO');
    process.exitCode = 2;
    return;
  }
  console.log(`read cost: ${readCost()} request(s) against the core hourly quota, `
    + `plus 2 free /rate_limit calls. One read is anonymous and is billed to the `
    + `unauthenticated bucket for this IP address, which is ${ANONYMOUS_CORE_LIMIT} an hour.`);

  const authedHeaders = { ...COMMON, Authorization: `Bearer ${token}` };
  // Deliberately credential-free, and it must stay that way.
  const anonHeaders = { ...COMMON };

  const authLimit = await coreLimit(authedHeaders);
  const anonLimit = await coreLimit(anonHeaders);

  const authRes = await fetch(`${API}/repos/${repoName}`,
    { headers: authedHeaders, redirect: 'manual' });
  const anonRes = await fetch(`${API}/repos/${repoName}`,
    { headers: anonHeaders, redirect: 'manual' });
  console.log(`authenticated: HTTP ${authRes.status}  core.limit=${authLimit}`);
  console.log(`anonymous:     HTTP ${anonRes.status}  core.limit=${anonLimit}`);

  let repo = null;
  const scopes = scopeList(authRes.headers.get('x-oauth-scopes'));
  if (authRes.status === 200) {
    repo = await authRes.json();
    console.log(`${repoName}: private=${repo.private} visibility=${visibilityOf(repo)}`);
  }

  const [state, detail] = classify(anonRes.status, authRes.status, repo);
  console.log(`${state}: ${detail}`);
  const [scopeState, scopeDetail] = scopeGap(scopes, visibilityOf(repo));
  console.log(`${scopeState}: ${scopeDetail}`);
  const fallout = forkFallout(repo);
  if (fallout) console.log(`forks-note: ${fallout}`);
  console.log(`blind-spot: ${blindSpot()}`);
  console.log(`repair: ${repair(state, scopeState)}`);

  console.log(JSON.stringify({
    repository: repoName,
    authenticated_status: authRes.status,
    anonymous_status: anonRes.status,
    authenticated_core_limit: authLimit,
    anonymous_core_limit: anonLimit,
    client_was_anonymous: clientIsAnonymous(authLimit),
    private: (repo || {}).private ?? null,
    visibility: visibilityOf(repo),
    scopes,
    state,
    detail,
    scope_state: scopeState,
    forks_note: fallout,
    blind_spot: blindSpot(),
    repair: repair(state, scopeState),
  }, null, 2));
  process.exitCode = ['went-private', 'internal-visibility'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The classifier is tested as a matrix of pairs rather than as a set of single readings, because that is the claim the note makes: 200-with-a-token beside 404-without-one is a visibility change, and 404 to both is not this note at all and has to say so. The internal case gets its own assertions since it is <code>private: true</code> and still not private, and the boolean cannot separate them. Then the scope arithmetic, where <code>public_repo</code> has to come back as blind rather than as merely insufficient, and finally the two honest refusals: the missing timestamp and the ambiguous pair, both of which are asserted to be reported rather than resolved.",
"test_py_file": "test_github_visibility_change.py",
"test_py": '''from github_visibility_change import (
    ANONYMOUS_CORE_LIMIT, BLIND_SCOPE, PRIVATE_SCOPE, blind_spot, classify,
    client_is_anonymous, fork_fallout, read_cost, repair, scope_gap, scope_list,
    visibility_of,
)

PRIVATE_NOW = {"private": True, "visibility": "private", "forks_count": 37}
INTERNAL = {"private": True, "visibility": "internal", "forks_count": 0}
PUBLIC = {"private": False, "visibility": "public", "forks_count": 12}


def test_the_pair_of_readings_is_the_finding():
    state, detail = classify(404, 200, PRIVATE_NOW)
    assert state == "went-private"
    assert "invisible without one" in detail
    assert "Deletion would answer 404 to both" in detail


def test_404_to_both_readings_is_handed_to_the_wider_triage():
    state, detail = classify(404, 404, None)
    assert state == "invisible-to-both"
    assert "wider 404 triage" in detail
    assert "wider 404 triage" in repair(state)


def test_a_public_repository_is_not_reported_as_a_transition():
    assert classify(200, 200, PUBLIC)[0] == "still-public"


def test_an_anonymous_success_beside_an_authenticated_failure_blames_the_token():
    state, detail = classify(200, 401, None)
    assert state == "token-is-the-problem"
    assert "expired or revoked" in detail


def test_a_redirect_anywhere_is_a_rename_and_a_different_note():
    assert classify(301, 200, PRIVATE_NOW)[0] == "moved"
    assert classify(404, 301, None)[0] == "moved"


def test_internal_is_private_true_and_still_not_private():
    assert visibility_of(INTERNAL) == "internal"
    assert INTERNAL["private"] is True
    state, detail = classify(404, 200, INTERNAL)
    assert state == "internal-visibility"
    assert "every member of the enterprise" in detail
    assert "membership" in repair(state)


def test_visibility_falls_back_to_the_boolean_but_prefers_the_field():
    assert visibility_of({"private": True}) == "private"
    assert visibility_of({"private": False}) == "public"
    assert visibility_of({}) == "unreported"
    assert visibility_of(None) == "unreported"


def test_the_anonymous_bucket_proves_whether_a_client_authenticated():
    assert ANONYMOUS_CORE_LIMIT == 60
    assert client_is_anonymous(60) is True
    assert client_is_anonymous(5000) is False
    assert client_is_anonymous(None) is None


def test_public_repo_is_blind_rather_than_merely_narrow():
    state, detail = scope_gap([BLIND_SCOPE], "private")
    assert state == "blind-scope"
    assert "as blind here as sending no token at all" in detail
    assert BLIND_SCOPE in repair("went-private", state)


def test_the_repo_scope_covers_it_and_points_at_the_account_instead():
    state, detail = scope_gap([PRIVATE_SCOPE, "workflow"], "private")
    assert state == "scope-sufficient"
    assert "no grant on the repository" in detail


def test_a_fine_grained_token_reports_no_scopes_and_needs_permissions():
    state, detail = scope_gap(None, "private")
    assert state == "no-scopes-reported"
    assert "Metadata: Read" in detail and "Contents: Read" in detail


def test_scopes_are_not_asked_about_a_public_repository():
    assert scope_gap(["public_repo"], "public")[0] == "not-applicable"
    assert scope_gap([], "private")[0] == "scope-insufficient"


def test_absent_and_empty_scope_headers_are_different_readings():
    assert scope_list(None) is None
    assert scope_list("") == []
    assert scope_list("repo, workflow") == ["repo", "workflow"]


def test_the_detached_forks_are_reported_as_a_second_failure():
    note = fork_fallout(PRIVATE_NOW)
    assert note and "still public" in note
    assert fork_fallout(PUBLIC) is None
    assert fork_fallout(INTERNAL) is None


def test_the_missing_timestamp_is_stated_rather_than_guessed():
    assert "no visibility-changed timestamp" in blind_spot()
    assert "your own logs" in blind_spot()


def test_an_unsorted_pair_is_left_unsorted():
    state, detail = classify(403, 500, None)
    assert state == "unclassified"
    assert "500" in detail and "403" in detail


def test_the_run_costs_two_billable_reads():
    assert read_cost() == 2
''',
"test_js_file": "github-visibility-change.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ANONYMOUS_CORE_LIMIT, BLIND_SCOPE, PRIVATE_SCOPE, blindSpot, classify,
  clientIsAnonymous, forkFallout, readCost, repair, scopeGap, scopeList,
  visibilityOf,
} from './github-visibility-change.mjs';

const PRIVATE_NOW = { private: true, visibility: 'private', forks_count: 37 };
const INTERNAL = { private: true, visibility: 'internal', forks_count: 0 };
const PUBLIC = { private: false, visibility: 'public', forks_count: 12 };

test('the pair of readings is the finding', () => {
  const [state, detail] = classify(404, 200, PRIVATE_NOW);
  assert.equal(state, 'went-private');
  assert.match(detail, /invisible without one/);
  assert.match(detail, /Deletion would answer 404 to both/);
});

test('404 to both readings is handed to the wider triage', () => {
  const [state, detail] = classify(404, 404, null);
  assert.equal(state, 'invisible-to-both');
  assert.match(detail, /wider 404 triage/);
  assert.match(repair(state), /wider 404 triage/);
});

test('a public repository is not reported as a transition', () => {
  assert.equal(classify(200, 200, PUBLIC)[0], 'still-public');
});

test('an anonymous success beside an authenticated failure blames the token', () => {
  const [state, detail] = classify(200, 401, null);
  assert.equal(state, 'token-is-the-problem');
  assert.match(detail, /expired or revoked/);
});

test('a redirect anywhere is a rename and a different note', () => {
  assert.equal(classify(301, 200, PRIVATE_NOW)[0], 'moved');
  assert.equal(classify(404, 301, null)[0], 'moved');
});

test('internal is private true and still not private', () => {
  assert.equal(visibilityOf(INTERNAL), 'internal');
  assert.equal(INTERNAL.private, true);
  const [state, detail] = classify(404, 200, INTERNAL);
  assert.equal(state, 'internal-visibility');
  assert.match(detail, /every member of the enterprise/);
  assert.match(repair(state), /membership/);
});

test('visibility falls back to the boolean but prefers the field', () => {
  assert.equal(visibilityOf({ private: true }), 'private');
  assert.equal(visibilityOf({ private: false }), 'public');
  assert.equal(visibilityOf({}), 'unreported');
  assert.equal(visibilityOf(null), 'unreported');
});

test('the anonymous bucket proves whether a client authenticated', () => {
  assert.equal(ANONYMOUS_CORE_LIMIT, 60);
  assert.equal(clientIsAnonymous(60), true);
  assert.equal(clientIsAnonymous(5000), false);
  assert.equal(clientIsAnonymous(null), null);
});

test('public_repo is blind rather than merely narrow', () => {
  const [state, detail] = scopeGap([BLIND_SCOPE], 'private');
  assert.equal(state, 'blind-scope');
  assert.match(detail, /as blind here as sending no token at all/);
  assert.match(repair('went-private', state), new RegExp(BLIND_SCOPE));
});

test('the repo scope covers it and points at the account instead', () => {
  const [state, detail] = scopeGap([PRIVATE_SCOPE, 'workflow'], 'private');
  assert.equal(state, 'scope-sufficient');
  assert.match(detail, /no grant on the repository/);
});

test('a fine grained token reports no scopes and needs permissions', () => {
  const [state, detail] = scopeGap(null, 'private');
  assert.equal(state, 'no-scopes-reported');
  assert.match(detail, /Metadata: Read/);
  assert.match(detail, /Contents: Read/);
});

test('scopes are not asked about a public repository', () => {
  assert.equal(scopeGap(['public_repo'], 'public')[0], 'not-applicable');
  assert.equal(scopeGap([], 'private')[0], 'scope-insufficient');
});

test('absent and empty scope headers are different readings', () => {
  assert.equal(scopeList(null), null);
  assert.deepEqual(scopeList(''), []);
  assert.deepEqual(scopeList('repo, workflow'), ['repo', 'workflow']);
});

test('the detached forks are reported as a second failure', () => {
  const note = forkFallout(PRIVATE_NOW);
  assert.match(note, /still public/);
  assert.equal(forkFallout(PUBLIC), null);
  assert.equal(forkFallout(INTERNAL), null);
});

test('the missing timestamp is stated rather than guessed', () => {
  assert.match(blindSpot(), /no visibility-changed timestamp/);
  assert.match(blindSpot(), /your own logs/);
});

test('an unsorted pair is left unsorted', () => {
  const [state, detail] = classify(403, 500, null);
  assert.equal(state, 'unclassified');
  assert.match(detail, /500/);
  assert.match(detail, /403/);
});

test('the run costs two billable reads', () => {
  assert.equal(readCost(), 2);
});
''',
"faq": [
 ("How is this different from the general 404 triage already in this section?",
  "That note answers a wider question for a caller who may never have had access: it sorts a 404 into a dead token, a missing scope, a repository outside an App's installation, or no grant at all. This one is the narrower case where a caller demonstrably <em>did</em> have access, anonymously, for a long time, and the resource changed underneath it. The evidence is different too. The triage takes three reads with one credential; this takes the same read twice with two different callers, and it is the asymmetry between them that names the cause. When both readings 404, this note stops and hands you to that one."),
 ("Can the script tell me when the repository went private?",
  "No, and it says so rather than estimating. There is no visibility-changed timestamp on the repository object. <code>updated_at</code> moves whenever a description, a topic or a default branch changes, so reading a date out of it would be a guess dressed as a finding. The organization audit log does record the event, and reading it needs <code>admin:org</code>-class access that a repository reader does not have. What you can date precisely is the first 404 in your own logs, which is usually close enough and is evidence you already own."),
 ("The repository shows private: true but colleagues outside the team can read it. Why?",
  "Because it is internal rather than private, and the boolean cannot express the difference. <code>visibility</code> has three values — <code>public</code>, <code>private</code> and <code>internal</code> — and internal repositories report <code>private: true</code> while being readable by every member of the enterprise. It matters for the repair: private access is granted per repository, internal access follows enterprise membership, so a machine account that is not a member will keep getting 404 no matter how many repository-level grants it is given."),
 ("Our token has public_repo. Is that not enough for a repository we already read?",
  "It is the one scope guaranteed not to be enough. <code>public_repo</code> grants access to public repositories and to nothing else, so at the exact moment this repository stopped being public, that token became precisely as blind as sending no credential at all. A classic token needs <code>repo</code>, which is read and write together and is more authority than a reader should hold; a fine-grained token with <code>Metadata: Read</code> and <code>Contents: Read</code> on that one repository is the narrower and better answer, and it has to be granted by the repository's owner."),
 ("A URL that looks like the repository still works. Which one am I reading?",
  "Probably a fork. When a public repository becomes private, the forks that already existed are split off into their own network and remain public, so links, search results and vendored references keep resolving to something with the same name and the same history up to the moment of the change. A dependency tool that quietly follows one starts tracking a copy that no longer receives commits, which surfaces weeks later as a version that never updates. Check <code>fork</code> and <code>source</code> on whatever is still answering before you rely on it."),
],
"related": [
 ("/github/404-masking-403/", "The wider triage for a 404 with several possible causes"),
 ("/github/rate-limit-unauthenticated/", "What an unauthenticated client is actually working with"),
 ("/github/fork-vs-upstream-confusion/", "The copy that still resolves after the change"),
],
"citations": [CITE_REPOS, CITE_VISIBILITY, CITE_ABOUT_REPOS, CITE_RATE_LIMITS],
},
]
