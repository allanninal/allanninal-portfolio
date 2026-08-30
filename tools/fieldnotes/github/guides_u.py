#!/usr/bin/env python3
"""/github/ field notes, batch U — the writing.

Four notes about a write being refused, and not one of them is about the
credential. The section already owns credential state thoroughly: a scope that
was never granted, a fine-grained permission the endpoint wanted, an App
installation that has been suspended, a token minted narrower than the job. Each
of those is answered by changing what the caller holds. These four are answered
by changing the repository, and in two of them no credential in the world would
have helped.

The first is a rule on a ref. Branch protection is readable only with repository
admin, so an auditing token gets 403 where a privileged one gets the rules, and
the failure is that a compliance sweep converts that refusal into "not
protected" and reports a fully protected organisation as wide open. The honest
fallback is a boolean on the branch object that anyone with read access can see,
and there is a second reading beside it — the rules a ruleset contributes, which
are readable without admin at all. Three readings, one of which is a refusal, and
the note is about never letting the refusal masquerade as an absence.

The second is a whole repository frozen. Archiving makes a repository read-only:
the API still serves every read, which is why the failure looks selective and
personal, and refuses every write regardless of who is asking. One boolean on the
repository object explains it, and the useful consequence is not a repair but a
classification — this is a permanent skip rather than a retryable error, and a
bot that retries it is spending quota on a request that will never be accepted.

The third is a repository that is not readable either. Disabled is a different
platform state with a different owner: it is set for billing or a terms problem
rather than by anybody on the team, most sub-resources stop answering, and the
repository stays in the organisation listing the whole time. That combination is
what makes it dangerous, because an org-wide sweep counts it as zero webhooks,
zero branches and zero open pull requests, and those zeroes are indistinguishable
from real ones in the aggregate at the bottom of the report.

The fourth is the closest to credential territory and is deliberately kept out of
it. A deploy key is an object on the repository with a boolean on it that was
chosen when the key was created, and read-only is both the default and the right
choice for almost every use. Nothing about scopes, permissions or installations
is involved: the key declares a narrower capability than the workflow assumed,
the refusal arrives from Git over SSH rather than from the API, and the diagnosis
therefore starts in the wrong tool. The finding is one field on one object, and
the key material itself is never printed.

Every script here is read only, and that constraint bites harder in this batch
than anywhere else in the section, because all four notes are about writes. Not
one of them attempts the write it is describing. Protection is established from
the rules, an archived repository from its own boolean, a disabled one from its
boolean and the shape of what its sub-resources answer, and a read-only deploy
key from the field the key object carries. Pushing a commit to find out whether
protection blocks it, or patching an archived repository to watch the 403 arrive,
would be a faster way to the same fact and is exactly the thing this section does
not do.
"""

CITE_BRANCH_PROTECTION = ("Branch protection — GitHub REST API",
                          "https://docs.github.com/en/rest/branches/branch-protection")
CITE_BRANCHES = ("Branches — GitHub REST API",
                 "https://docs.github.com/en/rest/branches/branches")
CITE_ABOUT_PROTECTED = ("About protected branches — GitHub Docs",
                        "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches")
CITE_RULES = ("Rules — GitHub REST API",
              "https://docs.github.com/en/rest/repos/rules")
CITE_REPOS = ("Repositories — GitHub REST API",
              "https://docs.github.com/en/rest/repos/repos")
CITE_ARCHIVING = ("Archiving repositories — GitHub Docs",
                  "https://docs.github.com/en/repositories/archiving-a-github-repository/archiving-repositories")
CITE_TROUBLESHOOTING = ("Troubleshooting the REST API — GitHub Docs",
                        "https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api")
CITE_BEST_PRACTICES = ("Best practices for using the REST API — GitHub Docs",
                       "https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api")
CITE_PAGINATION = ("Using pagination in the REST API — GitHub Docs",
                   "https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api")
CITE_ABOUT_REPOS = ("About repositories — GitHub Docs",
                    "https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories")
CITE_DEPLOY_KEYS_REST = ("Deploy keys — GitHub REST API",
                         "https://docs.github.com/en/rest/deploy-keys/deploy-keys")
CITE_MANAGING_DEPLOY_KEYS = ("Managing deploy keys — GitHub Docs",
                             "https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys")
CITE_APP_INSTALL_AUTH = ("Authenticating as a GitHub App installation — GitHub Docs",
                         "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation")
CITE_APP_PERMS = ("Permissions required for GitHub Apps — GitHub Docs",
                  "https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps")

GUIDES = [
{
"slug": "branch-protection-requires-admin",
"title": "Branch protection is unreadable without admin, not absent",
"description": "GET .../protection answers 403 without repository admin. An auditor that reads that as absence reports a fully protected organisation as unprotected.",
"h1": "branch protection is unreadable without admin, not absent",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api branch protection 403 must have admin rights",
             "must have admin rights to repository branch protection",
             "github branch protection api returns 404 branch not protected",
             "github audit branch protection read only token",
             "github rules for a branch api without admin"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The compliance report says nought out of two hundred and twelve repositories have branch protection. The security lead opens three of them at random and every one has protection on <code>main</code>, with required reviews and required checks, exactly as the policy says. The script is not lying about what it saw. It asked for the protection rules with a token that has read access and no more, GitHub answered <code>403 Must have admin rights to Repository.</code>, and somewhere in a <code>try</code> block that refusal became <code>protected = False</code>.",
"short_answer": """<p>The detailed protection rules on a branch are readable only with <strong>admin</strong> on the repository. <code>GET /repos/{owner}/{repo}/branches/{branch}/protection</code> has three distinct outcomes and they must never be collapsed into two: <code>200</code> with a protection object means protected and readable, <code>404</code> with <code>{"message":"Branch not protected"}</code> means genuinely unprotected, and <code>403</code> with the admin-rights message means <em>you cannot see</em>. A 403 is not an absence.</p>
<p>Two readings are available without admin and are the honest fallback. <code>GET /repos/{owner}/{repo}/branches/{branch}</code> returns a <code>protected</code> boolean, which is enough for coverage reporting. <code>GET /repos/{owner}/{repo}/rules/branches/{branch}</code> returns the rules a ruleset contributes to that branch, with no admin required at all. Report coverage from those, keep &ldquo;unknown&rdquo; as its own column, and grant repository admin only where the detailed rules genuinely have to be audited.</p>""",
"problem": """<p>The report is worse than useless because it is confident. A coverage number that says zero per cent reads as an emergency, so somebody spends a morning proving it wrong one repository at a time in the web interface, and the conclusion at the end of that morning is &ldquo;the script is broken&rdquo; rather than anything about the estate. The next version of the script is written to be less strict, which is the wrong lesson entirely.</p>
<p>The reason the refusal turns into an absence is that the two failures look alike from inside an exception handler. Both are non-200. Both have a JSON body with a <code>message</code>. Both happen on the same URL, on repositories that otherwise read perfectly, and the code that catches them is usually one <code>except</code> or one <code>if not response.ok</code> with a single fallback value underneath it, written on the reasonable-sounding grounds that a missing protection object means there is no protection. That is true of exactly one of the two failures.</p>
<p>It also fails asymmetrically, which is how it survives review. An auditor run by a repository administrator on their own repositories works perfectly, because that token gets 200s. The same script scheduled with an organisation-wide read-only token gets 403s everywhere, and the difference between the two runs is invisible in the output: both produce a clean list of repositories with a boolean next to each one, and only one of them is measuring anything.</p>
<p>The mirror-image failure is quieter and more dangerous. A script that reports the estate as fully protected because it was run by an owner is not going to notice the repository where protection was removed on a Friday, because the finding it was built to detect is the one it never gets to see.</p>""",
"why": """<p><strong>Three outcomes, not two.</strong> The protection endpoint is documented as requiring admin rights, so its refusal is a normal answer rather than an error condition. The states have different meanings and different repairs: <code>200</code> is a measurement, <code>404 Branch not protected</code> is a finding, and <code>403</code> is a gap in your instrument. Compressing three into two is where the whole failure lives, and it is one line of code.</p>
<p><strong>The <code>protected</code> boolean is visible to anyone who can read the branch.</strong> <code>GET /repos/{owner}/{repo}/branches/{branch}</code> carries <code>protected: true|false</code>, and it costs the same request whether or not the rules are readable. For the question a compliance sweep is actually asking &mdash; is this branch protected at all &mdash; that field is the answer and admin is not needed. What it cannot tell you is <em>how</em>: two approving reviews or one, which status checks, whether administrators are included.</p>
<p><strong>Rulesets are readable without admin, and they are a second source of protection.</strong> <code>GET /repos/{owner}/{repo}/rules/branches/{branch}</code> lists the rules that apply to a branch from repository and organisation rulesets, including the ruleset each one came from. A branch can be governed entirely by a ruleset, and an audit that only looks at the classic protection endpoint will describe such a branch in terms of what it could not read rather than in terms of the rules that are plainly published to it.</p>
<p><strong>A push is refused by the rule, and the rule is readable.</strong> The refusal a developer sees is <code>GH006: Protected branch update failed</code> or <code>protected branch hook declined</code>, arriving from Git rather than from the API. There is no need to send a commit to find out which rule declined it: required reviews refuse a direct push outright, required status checks refuse a merge until the named contexts pass, <code>restrictions</code> names the only actors allowed to push, and <code>enforce_admins</code> decides whether an administrator is exempt. Every one of those is a field, and every one of them can be read, printed and explained without touching the branch.</p>
<p><strong>This is not the multi-cause 404.</strong> <a href="/github/404-masking-403/">A 404 on the repository</a> means several things at once and needs a credential triage. The 403 here is unusually informative: it names admin rights, it arrives on a repository the same token just read successfully, and the fix is a grant on one repository rather than a new token. Where the protection endpoint answers 404 <em>without</em> the &ldquo;Branch not protected&rdquo; message, that is the other note and the script says so rather than guessing.</p>
<p><strong>Granting admin to an auditor is a real cost, so be sure you need it.</strong> Repository admin carries settings, collaborators, deploy keys and deletion along with the ability to read protection, which is a large grant to hand a scheduled job for the sake of one field. A GitHub App with <code>administration: read</code> is the narrow version of the same thing and is the answer where the detailed rules are genuinely required. Where they are not, the boolean and the ruleset listing cost nothing and expose nothing.</p>""",
"steps": [
 {"h": "Read the branch before you read its rules",
  "body": """<p>One <code>GET /repos/{owner}/{repo}/branches/{branch}</code>. The <code>protected</code> boolean in that response is visible to any token that can read the repository, and it is the field a coverage report should be built on. Everything after this step is about <em>how</em> the branch is protected, which is a different and more expensive question.</p>"""},
 {"h": "Ask for the protection rules and keep the refusal as a refusal",
  "body": """<p>One <code>GET /repos/{owner}/{repo}/branches/{branch}/protection</code>, and then three branches rather than two. Only a <code>404</code> whose message is <code>Branch not protected</code> is evidence of absence. A <code>403</code> is evidence about your token, and the script records it as <code>unknown</code> so it can never be counted as a repository at risk.</p>"""},
 {"h": "Read the ruleset rules, which need no admin at all",
  "body": """<p>One <code>GET /repos/{owner}/{repo}/rules/branches/{branch}</code>. This returns the rules contributed by repository and organisation rulesets along with the ruleset each came from, and it answers with read access. On an estate that has moved to rulesets this is often the only readable description of what governs the branch, and it turns a row that would have said &ldquo;cannot see&rdquo; into a row that says &ldquo;pull request required, two approvals, non-fast-forward blocked&rdquo;.</p>"""},
 {"h": "Turn the readable rules into the writes they refuse",
  "body": """<p>The script converts whatever it could read into plain statements about what will happen to a push: refused outright, refused until named checks pass, allowed only for listed actors, allowed for administrators or not. That is the part people actually want from a protection audit, and it comes out of fields rather than out of an experiment. No commit is created, no branch is touched, nothing is pushed.</p>"""},
 {"h": "Report unknown as a number, not as a zero",
  "body": """<p>The summary prints four counts: protected with readable rules, protected but opaque, confirmed unprotected, and unknown. If the unknown column is large, the finding is about the auditing token and not about the estate, and the repair is to grant repository admin or an App with <code>administration: read</code> where the detail is needed. Three requests per branch, printed before they are spent.</p>"""},
],
"verify": """<p>Run it once with the read-only auditing token and once with a token that has admin on one repository. The estate does not change between the two runs; the number of rows the instrument can resolve does.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_branch_protection_audit.py \\
    --branch acme/platform-api:main --branch acme/legacy-tools:main
# read cost: at most 3 request(s) per branch against the core hourly quota
# read cost: at most 6 request(s) in total
# acme/platform-api:main protected=True protection=403 rules=2
# protected-rules-hidden: the branch reports protected=true and the protection
# endpoint refused with admin rights required, so the classic rules are not
# readable by this token. Two ruleset rule(s) are readable and are reported.
#   a pull request is required, so a direct push to this branch is refused
#   non-fast-forward updates are blocked, so a force push is refused
# repair: report this as protected. To read the detailed rules, grant this token
# repository admin or use an App with administration: read.
# acme/legacy-tools:main protected=False protection=404 rules=0
# unprotected-confirmed: protected=false and the protection endpoint answered
# 404 Branch not protected, which is the one 404 that means absence
# repair: this branch really is unprotected. Protect it or record the exception.
#
# summary: 1 protected, 0 readable in detail, 1 unprotected, 0 unknown</code></pre>""",
"code_intro": "The whole note is one function that refuses to fold three outcomes into two, and everything else exists to give that function something to be careful with. Three reads per branch, all of them cheap, and the classification afterwards is pure: which of the three answers came back, what the branch object said about itself, and what the ruleset listing published. The translation from rules to refused writes is also pure, which is the point &mdash; a protection audit that has to push a commit to find out what protection does is not an audit, it is a change.",
"py_file": "github_branch_protection_audit.py",
"py": '''"""Audit branch protection without mistaking a refusal for an absence.

Read only. Three GETs per branch and nothing is written: no commit is created,
no ref is updated, no protection setting is changed. What a push would be
refused for is derived from the rules the API publishes, never by attempting a
push and reading the error.

The point of the note: the detailed protection rules are readable only with
repository admin. Without it, GET .../protection answers 403 with an
admin-rights message, and an auditor that treats every non-200 as "not
protected" reports a fully protected estate as wide open. Only a 404 whose
message is "Branch not protected" is evidence of absence.

What this can and cannot see: with a read-only token the classic rules on a
protected branch are genuinely invisible, and that is reported as unknown
rather than guessed at. Two things are visible without admin and are used
instead -- the protected boolean on the branch object, and the rules a ruleset
contributes, which GET /repos/{owner}/{repo}/rules/branches/{branch} publishes
to anyone who can read the repository.

Environment:

    GITHUB_TOKEN    a token with read access to the repositories
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_branch_protection_audit")

API = "https://api.github.com"
UA = "github-branch-protection-audit/1.0"

# The one message that turns a 404 into a finding. Anything else answering 404
# is ambiguous and belongs to the 404 triage note instead.
ABSENCE_MESSAGE = "branch not protected"

# What the protection endpoint says when the token can reach the repository but
# not its settings. Matched loosely because the wording has varied.
ADMIN_MESSAGE = "admin rights"

# Three reads per branch: the branch, the classic protection, the ruleset rules.
REQUESTS_PER_BRANCH = 3


def is_absence(status, message):
    """Whether this answer is evidence that the branch is unprotected. Pure.

    The single most important function in this script, and the one the broken
    auditors are missing. A 403 is never an absence: it says the token cannot
    see, which is a statement about the instrument rather than about the
    branch. A 404 is an absence only when it names the reason.
    """
    try:
        code = int(status)
    except (TypeError, ValueError):
        return False
    if code != 404:
        return False
    return ABSENCE_MESSAGE in str(message or "").lower()


def visibility(status, message):
    """What the protection endpoint's answer tells you. Pure.

    Returns one of: readable, not-protected, admin-required, ambiguous-404,
    unknown. Four of those five are not measurements of the branch.
    """
    try:
        code = int(status)
    except (TypeError, ValueError):
        return "unknown"
    if code == 200:
        return "readable"
    if is_absence(code, message):
        return "not-protected"
    if code == 403:
        return "admin-required"
    if code == 404:
        return "ambiguous-404"
    return "unknown"


def verdict(protected_flag, status, message, rules=None):
    """Classify one branch from all three readings. Pure. (state, detail).

    The branch object's boolean is authoritative for coverage because it is
    visible without admin. The protection endpoint decides only whether the
    detail is available, and the ruleset listing can rescue a row that would
    otherwise have been opaque.
    """
    seen = visibility(status, message)
    rule_count = len(rules or [])

    if protected_flag is None:
        return ("branch-unreadable",
                "the branch itself did not come back, so there is nothing to "
                "judge. That is a repository or credential problem rather than "
                "a protection one.")

    if protected_flag:
        if seen == "readable":
            return ("protected-rules-readable",
                    "the branch is protected and this token can read the rules, "
                    "so the refusals below are quoted from settings rather than "
                    "inferred.")
        if seen == "admin-required":
            detail = ("the branch reports protected=true and the protection "
                      "endpoint refused with admin rights required, so the "
                      "classic rules are not readable by this token.")
            if rule_count:
                detail += (" %d ruleset rule(s) are readable and are reported."
                           % rule_count)
            return ("protected-rules-hidden", detail)
        if seen == "not-protected":
            return ("contradictory",
                    "the branch says protected=true and the protection endpoint "
                    "says the branch is not protected. A ruleset governs this "
                    "branch without classic branch protection behind it.")
        return ("protected-rules-hidden",
                "the branch reports protected=true and the protection endpoint "
                "answered %s, which is not a readable rule set. Treat this as "
                "protected and unmeasured." % status)

    if rule_count:
        return ("ruleset-only",
                "protected=false, but %d rule(s) reach this branch from a "
                "ruleset. Classic protection is not the only thing that refuses "
                "a push." % rule_count)
    if seen == "not-protected":
        return ("unprotected-confirmed",
                "protected=false and the protection endpoint answered 404 "
                "Branch not protected, which is the one 404 that means absence.")
    if seen == "admin-required":
        return ("unprotected-by-flag",
                "protected=false on the branch object, which is visible without "
                "admin and is the honest reading. The protection endpoint "
                "refused separately and adds nothing here.")
    return ("unknown",
            "protected=false but the protection endpoint answered %s rather "
            "than a recognised absence, so this row is not resolved." % status)


def refused_writes(protection):
    """Plain statements of what the classic rules refuse. Pure.

    Derived from fields. Nothing here is learned by pushing anything.
    """
    if not isinstance(protection, dict):
        return []
    out = []
    reviews = protection.get("required_pull_request_reviews")
    if isinstance(reviews, dict):
        count = reviews.get("required_approving_review_count")
        if count:
            out.append("a direct push is refused: %s approving review(s) are "
                       "required through a pull request" % count)
        else:
            out.append("a direct push is refused: a pull request is required")
    checks = protection.get("required_status_checks")
    if isinstance(checks, dict):
        contexts = checks.get("contexts") or []
        out.append("a merge is refused until %d status check(s) pass"
                   % len(contexts))
        if checks.get("strict"):
            out.append("a merge is refused while the branch is behind its base")
    if (protection.get("enforce_admins") or {}).get("enabled"):
        out.append("administrators are not exempt from any of the above")
    restrictions = protection.get("restrictions")
    if isinstance(restrictions, dict):
        actors = (len(restrictions.get("users") or [])
                  + len(restrictions.get("teams") or [])
                  + len(restrictions.get("apps") or []))
        out.append("a push is refused for everyone except %d listed actor(s)"
                   % actors)
    if (protection.get("required_signatures") or {}).get("enabled"):
        out.append("an unsigned commit is refused")
    if (protection.get("lock_branch") or {}).get("enabled"):
        out.append("the branch is locked, so every write is refused")
    force = protection.get("allow_force_pushes")
    if isinstance(force, dict) and not force.get("enabled"):
        out.append("a force push is refused")
    deletions = protection.get("allow_deletions")
    if isinstance(deletions, dict) and not deletions.get("enabled"):
        out.append("deleting the branch is refused")
    return out


def refused_by_rules(rules):
    """The same statements, from the ruleset listing. Pure.

    This is the half that needs no admin, so on a read-only run it is often
    the only description of the branch anybody gets.
    """
    if not isinstance(rules, list):
        return []
    kinds = [r.get("type") for r in rules if isinstance(r, dict)]
    out = []
    if "pull_request" in kinds:
        out.append("a pull request is required, so a direct push to this "
                   "branch is refused")
    if "required_status_checks" in kinds:
        out.append("a merge is refused until the ruleset's status checks pass")
    if "non_fast_forward" in kinds:
        out.append("non-fast-forward updates are blocked, so a force push is "
                   "refused")
    if "deletion" in kinds:
        out.append("deleting the branch is refused")
    if "creation" in kinds:
        out.append("creating this ref is refused")
    if "update" in kinds:
        out.append("updating this ref directly is refused")
    if "required_signatures" in kinds:
        out.append("an unsigned commit is refused")
    return out


def rulesets_named(rules):
    """Which rulesets contributed the rules, for the report. Pure."""
    names = []
    for rule in rules or []:
        if not isinstance(rule, dict):
            continue
        source = rule.get("ruleset_source") or rule.get("ruleset_source_type")
        if source and source not in names:
            names.append(source)
    return names


def push_allowlist(protection):
    """Who is allowed to push to a restricted branch. Pure. Names only."""
    restrictions = (protection or {}).get("restrictions")
    if not isinstance(restrictions, dict):
        return []
    out = []
    for user in restrictions.get("users") or []:
        if isinstance(user, dict) and user.get("login"):
            out.append("user:" + str(user["login"]))
    for team in restrictions.get("teams") or []:
        if isinstance(team, dict) and team.get("slug"):
            out.append("team:" + str(team["slug"]))
    for app in restrictions.get("apps") or []:
        if isinstance(app, dict) and app.get("slug"):
            out.append("app:" + str(app["slug"]))
    return out


def coverage(states):
    """Summarise a sweep without letting unknown become unprotected. Pure."""
    counts = {"protected": 0, "readable_in_detail": 0, "unprotected": 0,
              "unknown": 0}
    for state in states or []:
        if state in ("protected-rules-readable", "protected-rules-hidden",
                     "contradictory", "ruleset-only"):
            counts["protected"] += 1
            if state == "protected-rules-readable":
                counts["readable_in_detail"] += 1
        elif state in ("unprotected-confirmed", "unprotected-by-flag"):
            counts["unprotected"] += 1
        else:
            counts["unknown"] += 1
    return counts


def instrument_verdict(counts):
    """Whether the sweep measured the estate or measured its own token. Pure."""
    counts = counts or {}
    protected = int(counts.get("protected") or 0)
    detail = int(counts.get("readable_in_detail") or 0)
    unknown = int(counts.get("unknown") or 0)
    total = protected + int(counts.get("unprotected") or 0) + unknown
    if not total:
        return ("no-rows", "nothing was checked.")
    if unknown:
        return ("instrument-gap",
                "%d of %d row(s) are unresolved. Those are not findings about "
                "the estate." % (unknown, total))
    if protected and not detail:
        return ("coverage-only",
                "every protected branch was counted from its boolean and none "
                "of the classic rules were readable. Coverage is trustworthy, "
                "detail is absent.")
    return ("measured", "every row resolved to a state about the branch.")


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "protected-rules-hidden":
        return ("report this as protected. To read the detailed rules, grant "
                "this token repository admin or use an App with "
                "administration: read.")
    if state == "protected-rules-readable":
        return ("nothing on visibility. Check the rules against your policy; "
                "the refusals above are what a push actually meets.")
    if state == "unprotected-confirmed":
        return ("this branch really is unprotected. Protect it or record the "
                "exception.")
    if state == "unprotected-by-flag":
        return ("this branch is unprotected on the boolean that needs no "
                "admin. Do not upgrade the token to confirm an absence you can "
                "already see.")
    if state == "ruleset-only":
        return ("read the ruleset rather than the branch protection settings. "
                "A ruleset refuses pushes without setting protected=true.")
    if state == "contradictory":
        return ("audit the ruleset that governs this branch. Classic protection "
                "is not what is refusing writes here.")
    if state == "branch-unreadable":
        return ("triage the repository and the token before the protection: "
                "check the name, the visibility and the installation.")
    return ("record this row as unknown. An unresolved answer is not a finding "
            "and must never be counted as unprotected.")


def read_cost(branches):
    """Requests this run will spend against the core quota. Pure."""
    return REQUESTS_PER_BRANCH * len(branches or [])


def split_target(target):
    """owner/repo:branch into its three parts. Pure."""
    text = str(target or "").strip()
    if ":" in text:
        repo, branch = text.rsplit(":", 1)
    else:
        repo, branch = text, "main"
    if repo.count("/") != 1 or not branch:
        return None
    owner, name = repo.split("/")
    if not owner or not name:
        return None
    return (owner, name, branch)


def message_of(body):
    """The message field of an error body, if there is one. Pure."""
    if isinstance(body, dict):
        return str(body.get("message") or "")
    return ""


def get_json(session, path):
    """One GET. Returns (status, parsed-body-or-None). Never writes."""
    r = session.get(API + path, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset "
                         "time and does not itself consume quota")
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, None


def inspect(session, owner, name, branch):
    """All three readings for one branch. Reads only."""
    base = "/repos/%s/%s" % (owner, name)
    b_status, b_body = get_json(session, "%s/branches/%s" % (base, branch))
    flag = None
    if b_status == 200 and isinstance(b_body, dict):
        flag = bool(b_body.get("protected"))

    p_status, p_body = get_json(session, "%s/branches/%s/protection"
                                % (base, branch))
    protection = p_body if (p_status == 200 and isinstance(p_body, dict)) else None

    r_status, r_body = get_json(session, "%s/rules/branches/%s" % (base, branch))
    rules = r_body if (r_status == 200 and isinstance(r_body, list)) else []

    return {
        "branch_status": b_status,
        "protected_flag": flag,
        "protection_status": p_status,
        "protection_message": message_of(p_body),
        "protection": protection,
        "rules_status": r_status,
        "rules": rules,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--branch", action="append", required=True,
                    help="owner/repo:branch to audit. Repeatable. The branch "
                         "defaults to main when the colon is left off.")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    targets = []
    for raw in args.branch:
        parts = split_target(raw)
        if not parts:
            log.error("cannot parse %r: expected owner/repo:branch", raw)
            return 2
        targets.append(parts)

    log.info("read cost: at most %d request(s) per branch against the core "
             "hourly quota", REQUESTS_PER_BRANCH)
    log.info("read cost: at most %d request(s) in total", read_cost(targets))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    findings = []
    for owner, name, branch in targets:
        label = "%s/%s:%s" % (owner, name, branch)
        seen = inspect(session, owner, name, branch)
        state, detail = verdict(seen["protected_flag"], seen["protection_status"],
                                seen["protection_message"], seen["rules"])
        refusals = refused_writes(seen["protection"]) or refused_by_rules(seen["rules"])

        log.info("%s protected=%s protection=%s rules=%d", label,
                 seen["protected_flag"], seen["protection_status"],
                 len(seen["rules"]))
        log.info("%s: %s", state, detail)
        for line in refusals:
            log.info("  %s", line)
        allowlist = push_allowlist(seen["protection"])
        if allowlist:
            log.info("  push allowed for: %s", ", ".join(allowlist))
        sources = rulesets_named(seen["rules"])
        if sources:
            log.info("  ruleset source(s): %s", ", ".join(str(s) for s in sources))
        log.info("repair: %s", repair(state))

        findings.append({
            "branch": label,
            "protected": seen["protected_flag"],
            "protection_status": seen["protection_status"],
            "protection_visibility": visibility(seen["protection_status"],
                                                seen["protection_message"]),
            "ruleset_rule_count": len(seen["rules"]),
            "ruleset_sources": sources,
            "refused_writes": refusals,
            "push_allowlist": allowlist,
            "state": state,
            "detail": detail,
            "repair": repair(state),
        })

    counts = coverage([f["state"] for f in findings])
    instrument, note = instrument_verdict(counts)
    log.info("summary: %d protected, %d readable in detail, %d unprotected, "
             "%d unknown", counts["protected"], counts["readable_in_detail"],
             counts["unprotected"], counts["unknown"])
    log.info("%s: %s", instrument, note)

    print(json.dumps({
        "requests_spent_at_most": read_cost(targets),
        "coverage": counts,
        "instrument": {"state": instrument, "detail": note},
        "findings": findings,
    }, indent=2, default=str))
    bad = {"unprotected-confirmed", "unprotected-by-flag"}
    return 1 if counts["unknown"] or any(f["state"] in bad for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-branch-protection-audit.mjs",
"js": '''/**
 * Audit branch protection without mistaking a refusal for an absence.
 *
 * Read only. Three GETs per branch and nothing is written: no commit, no ref
 * update, no settings change. What a push would be refused for is derived from
 * the rules the API publishes, never by attempting a push.
 *
 * The detailed protection rules need repository admin. Without it,
 * GET .../protection answers 403, and only a 404 whose message is "Branch not
 * protected" is evidence of absence. The protected boolean on the branch and
 * the ruleset rules for the branch are both readable without admin.
 *
 * Environment:
 *   GITHUB_TOKEN      a token with read access to the repositories
 *   GITHUB_BRANCHES   comma-separated owner/repo:branch values
 */
const API = 'https://api.github.com';
const UA = 'github-branch-protection-audit/1.0';

/** The one message that turns a 404 into a finding. */
export const ABSENCE_MESSAGE = 'branch not protected';

/** Three reads per branch: the branch, the protection, the ruleset rules. */
export const REQUESTS_PER_BRANCH = 3;

/** Whether this answer is evidence that the branch is unprotected. Pure. */
export function isAbsence(status, message) {
  const code = Number(status);
  if (!Number.isFinite(code) || code !== 404) return false;
  return String(message ?? '').toLowerCase().includes(ABSENCE_MESSAGE);
}

/** What the protection endpoint's answer tells you. Pure. */
export function visibility(status, message) {
  const code = Number(status);
  if (!Number.isFinite(code)) return 'unknown';
  if (code === 200) return 'readable';
  if (isAbsence(code, message)) return 'not-protected';
  if (code === 403) return 'admin-required';
  if (code === 404) return 'ambiguous-404';
  return 'unknown';
}

/** Classify one branch from all three readings. Pure. [state, detail]. */
export function verdict(protectedFlag, status, message, rules = []) {
  const seen = visibility(status, message);
  const ruleCount = Array.isArray(rules) ? rules.length : 0;

  if (protectedFlag === null || protectedFlag === undefined) {
    return ['branch-unreadable', 'the branch itself did not come back, so there '
      + 'is nothing to judge. That is a repository or credential problem rather '
      + 'than a protection one.'];
  }

  if (protectedFlag) {
    if (seen === 'readable') {
      return ['protected-rules-readable', 'the branch is protected and this '
        + 'token can read the rules, so the refusals below are quoted from '
        + 'settings rather than inferred.'];
    }
    if (seen === 'admin-required') {
      let detail = 'the branch reports protected=true and the protection '
        + 'endpoint refused with admin rights required, so the classic rules '
        + 'are not readable by this token.';
      if (ruleCount) {
        detail += ` ${ruleCount} ruleset rule(s) are readable and are reported.`;
      }
      return ['protected-rules-hidden', detail];
    }
    if (seen === 'not-protected') {
      return ['contradictory', 'the branch says protected=true and the '
        + 'protection endpoint says the branch is not protected. A ruleset '
        + 'governs this branch without classic branch protection behind it.'];
    }
    return ['protected-rules-hidden', `the branch reports protected=true and `
      + `the protection endpoint answered ${status}, which is not a readable `
      + 'rule set. Treat this as protected and unmeasured.'];
  }

  if (ruleCount) {
    return ['ruleset-only', `protected=false, but ${ruleCount} rule(s) reach `
      + 'this branch from a ruleset. Classic protection is not the only thing '
      + 'that refuses a push.'];
  }
  if (seen === 'not-protected') {
    return ['unprotected-confirmed', 'protected=false and the protection '
      + 'endpoint answered 404 Branch not protected, which is the one 404 that '
      + 'means absence.'];
  }
  if (seen === 'admin-required') {
    return ['unprotected-by-flag', 'protected=false on the branch object, which '
      + 'is visible without admin and is the honest reading. The protection '
      + 'endpoint refused separately and adds nothing here.'];
  }
  return ['unknown', `protected=false but the protection endpoint answered `
    + `${status} rather than a recognised absence, so this row is not resolved.`];
}

/** Plain statements of what the classic rules refuse. Pure. */
export function refusedWrites(protection) {
  if (!protection || typeof protection !== 'object') return [];
  const out = [];
  const reviews = protection.required_pull_request_reviews;
  if (reviews && typeof reviews === 'object') {
    const count = reviews.required_approving_review_count;
    if (count) {
      out.push(`a direct push is refused: ${count} approving review(s) are `
        + 'required through a pull request');
    } else {
      out.push('a direct push is refused: a pull request is required');
    }
  }
  const checks = protection.required_status_checks;
  if (checks && typeof checks === 'object') {
    const contexts = checks.contexts || [];
    out.push(`a merge is refused until ${contexts.length} status check(s) pass`);
    if (checks.strict) {
      out.push('a merge is refused while the branch is behind its base');
    }
  }
  if ((protection.enforce_admins || {}).enabled) {
    out.push('administrators are not exempt from any of the above');
  }
  const restrictions = protection.restrictions;
  if (restrictions && typeof restrictions === 'object') {
    const actors = (restrictions.users || []).length
      + (restrictions.teams || []).length + (restrictions.apps || []).length;
    out.push(`a push is refused for everyone except ${actors} listed actor(s)`);
  }
  if ((protection.required_signatures || {}).enabled) {
    out.push('an unsigned commit is refused');
  }
  if ((protection.lock_branch || {}).enabled) {
    out.push('the branch is locked, so every write is refused');
  }
  const force = protection.allow_force_pushes;
  if (force && typeof force === 'object' && !force.enabled) {
    out.push('a force push is refused');
  }
  const deletions = protection.allow_deletions;
  if (deletions && typeof deletions === 'object' && !deletions.enabled) {
    out.push('deleting the branch is refused');
  }
  return out;
}

/** The same statements, from the ruleset listing. Pure. */
export function refusedByRules(rules) {
  if (!Array.isArray(rules)) return [];
  const kinds = rules.filter((r) => r && typeof r === 'object').map((r) => r.type);
  const out = [];
  if (kinds.includes('pull_request')) {
    out.push('a pull request is required, so a direct push to this branch is refused');
  }
  if (kinds.includes('required_status_checks')) {
    out.push("a merge is refused until the ruleset's status checks pass");
  }
  if (kinds.includes('non_fast_forward')) {
    out.push('non-fast-forward updates are blocked, so a force push is refused');
  }
  if (kinds.includes('deletion')) out.push('deleting the branch is refused');
  if (kinds.includes('creation')) out.push('creating this ref is refused');
  if (kinds.includes('update')) out.push('updating this ref directly is refused');
  if (kinds.includes('required_signatures')) out.push('an unsigned commit is refused');
  return out;
}

/** Which rulesets contributed the rules, for the report. Pure. */
export function rulesetsNamed(rules) {
  const names = [];
  for (const rule of rules || []) {
    if (!rule || typeof rule !== 'object') continue;
    const source = rule.ruleset_source || rule.ruleset_source_type;
    if (source && !names.includes(source)) names.push(source);
  }
  return names;
}

/** Who is allowed to push to a restricted branch. Pure. Names only. */
export function pushAllowlist(protection) {
  const restrictions = (protection || {}).restrictions;
  if (!restrictions || typeof restrictions !== 'object') return [];
  const out = [];
  for (const user of restrictions.users || []) {
    if (user && user.login) out.push(`user:${user.login}`);
  }
  for (const team of restrictions.teams || []) {
    if (team && team.slug) out.push(`team:${team.slug}`);
  }
  for (const app of restrictions.apps || []) {
    if (app && app.slug) out.push(`app:${app.slug}`);
  }
  return out;
}

/** Summarise a sweep without letting unknown become unprotected. Pure. */
export function coverage(states) {
  const counts = {
    protected: 0, readable_in_detail: 0, unprotected: 0, unknown: 0,
  };
  for (const state of states || []) {
    if (['protected-rules-readable', 'protected-rules-hidden', 'contradictory',
      'ruleset-only'].includes(state)) {
      counts.protected += 1;
      if (state === 'protected-rules-readable') counts.readable_in_detail += 1;
    } else if (['unprotected-confirmed', 'unprotected-by-flag'].includes(state)) {
      counts.unprotected += 1;
    } else {
      counts.unknown += 1;
    }
  }
  return counts;
}

/** Whether the sweep measured the estate or measured its own token. Pure. */
export function instrumentVerdict(counts) {
  const c = counts || {};
  const protectedCount = Number(c.protected) || 0;
  const detail = Number(c.readable_in_detail) || 0;
  const unknown = Number(c.unknown) || 0;
  const total = protectedCount + (Number(c.unprotected) || 0) + unknown;
  if (!total) return ['no-rows', 'nothing was checked.'];
  if (unknown) {
    return ['instrument-gap', `${unknown} of ${total} row(s) are unresolved. `
      + 'Those are not findings about the estate.'];
  }
  if (protectedCount && !detail) {
    return ['coverage-only', 'every protected branch was counted from its '
      + 'boolean and none of the classic rules were readable. Coverage is '
      + 'trustworthy, detail is absent.'];
  }
  return ['measured', 'every row resolved to a state about the branch.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'protected-rules-hidden') {
    return 'report this as protected. To read the detailed rules, grant this '
      + 'token repository admin or use an App with administration: read.';
  }
  if (state === 'protected-rules-readable') {
    return 'nothing on visibility. Check the rules against your policy; the '
      + 'refusals above are what a push actually meets.';
  }
  if (state === 'unprotected-confirmed') {
    return 'this branch really is unprotected. Protect it or record the exception.';
  }
  if (state === 'unprotected-by-flag') {
    return 'this branch is unprotected on the boolean that needs no admin. Do '
      + 'not upgrade the token to confirm an absence you can already see.';
  }
  if (state === 'ruleset-only') {
    return 'read the ruleset rather than the branch protection settings. A '
      + 'ruleset refuses pushes without setting protected=true.';
  }
  if (state === 'contradictory') {
    return 'audit the ruleset that governs this branch. Classic protection is '
      + 'not what is refusing writes here.';
  }
  if (state === 'branch-unreadable') {
    return 'triage the repository and the token before the protection: check '
      + 'the name, the visibility and the installation.';
  }
  return 'record this row as unknown. An unresolved answer is not a finding and '
    + 'must never be counted as unprotected.';
}

/** Requests this run will spend against the core quota. Pure. */
export function readCost(branches) {
  return REQUESTS_PER_BRANCH * ((branches || []).length);
}

/** owner/repo:branch into its three parts. Pure. */
export function splitTarget(target) {
  const text = String(target ?? '').trim();
  const at = text.lastIndexOf(':');
  const repo = at > 0 ? text.slice(0, at) : text;
  const branch = at > 0 ? text.slice(at + 1) : 'main';
  const parts = repo.split('/');
  if (parts.length !== 2 || !parts[0] || !parts[1] || !branch) return null;
  return [parts[0], parts[1], branch];
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function getJson(token, path) {
  const res = await fetch(`${API}${path}`, { headers: headers(token) });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const raw = process.env.GITHUB_BRANCHES;
  if (!token || !raw) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_BRANCHES');
    process.exitCode = 2;
    return;
  }
  const targets = raw.split(',').map((t) => splitTarget(t)).filter(Boolean);
  if (!targets.length) {
    console.error('GITHUB_BRANCHES should hold owner/repo:branch values');
    process.exitCode = 2;
    return;
  }

  console.log(`read cost: at most ${REQUESTS_PER_BRANCH} request(s) per branch `
    + 'against the core hourly quota');
  console.log(`read cost: at most ${readCost(targets)} request(s) in total`);

  const findings = [];
  for (const [owner, name, branch] of targets) {
    const base = `/repos/${owner}/${name}`;
    const b = await getJson(token, `${base}/branches/${branch}`);
    const flag = b.status === 200 && b.body ? Boolean(b.body.protected) : null;
    const p = await getJson(token, `${base}/branches/${branch}/protection`);
    const protection = p.status === 200 && p.body ? p.body : null;
    const r = await getJson(token, `${base}/rules/branches/${branch}`);
    const rules = r.status === 200 && Array.isArray(r.body) ? r.body : [];

    const message = p.body && typeof p.body === 'object' ? p.body.message : '';
    const [state, detail] = verdict(flag, p.status, message, rules);
    const refusals = refusedWrites(protection).length
      ? refusedWrites(protection) : refusedByRules(rules);
    const label = `${owner}/${name}:${branch}`;

    console.log(`${label} protected=${flag} protection=${p.status} rules=${rules.length}`);
    console.log(`${state}: ${detail}`);
    for (const line of refusals) console.log(`  ${line}`);
    console.log(`repair: ${repair(state)}`);

    findings.push({
      branch: label,
      protected: flag,
      protection_status: p.status,
      protection_visibility: visibility(p.status, message),
      ruleset_rule_count: rules.length,
      ruleset_sources: rulesetsNamed(rules),
      refused_writes: refusals,
      push_allowlist: pushAllowlist(protection),
      state,
      detail,
      repair: repair(state),
    });
  }

  const counts = coverage(findings.map((f) => f.state));
  const [instrument, note] = instrumentVerdict(counts);
  console.log(`summary: ${counts.protected} protected, `
    + `${counts.readable_in_detail} readable in detail, ${counts.unprotected} `
    + `unprotected, ${counts.unknown} unknown`);
  console.log(`${instrument}: ${note}`);

  console.log(JSON.stringify({
    requests_spent_at_most: readCost(targets),
    coverage: counts,
    instrument: { state: instrument, detail: note },
    findings,
  }, null, 2));
  const bad = ['unprotected-confirmed', 'unprotected-by-flag'];
  process.exitCode = counts.unknown
    || findings.some((f) => bad.includes(f.state)) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first assertion is the one the broken auditors would fail: a 403 is not an absence, and no message on a 403 can make it one. From there the tests pin each of the three outcomes to its own state, check that the branch object's boolean is trusted over the endpoint that refused, and confirm that a branch governed only by a ruleset is still reported as refusing pushes. The summary is tested separately because that is where the damage was done originally &mdash; an unknown row must survive as unknown all the way into the counts rather than being quietly added to the unprotected pile.",
"test_py_file": "test_github_branch_protection_audit.py",
"test_py": '''from github_branch_protection_audit import (
    REQUESTS_PER_BRANCH, coverage, instrument_verdict, is_absence,
    push_allowlist, read_cost, refused_by_rules, refused_writes, repair,
    rulesets_named, split_target, verdict, visibility,
)

ADMIN_403 = "Must have admin rights to Repository."
ABSENT_404 = "Branch not protected"

PROTECTION = {
    "required_pull_request_reviews": {"required_approving_review_count": 2},
    "required_status_checks": {"strict": True, "contexts": ["build", "lint"]},
    "enforce_admins": {"enabled": True},
    "restrictions": {"users": [{"login": "release-bot"}],
                     "teams": [{"slug": "platform"}], "apps": []},
    "required_signatures": {"enabled": False},
    "allow_force_pushes": {"enabled": False},
    "allow_deletions": {"enabled": False},
}

RULES = [
    {"type": "pull_request", "ruleset_id": 42, "ruleset_source": "acme"},
    {"type": "non_fast_forward", "ruleset_id": 42, "ruleset_source": "acme"},
]


def test_a_403_is_never_evidence_that_a_branch_is_unprotected():
    assert is_absence(403, ADMIN_403) is False
    # Not even when the refusal happens to carry the absence wording.
    assert is_absence(403, ABSENT_404) is False
    assert visibility(403, ADMIN_403) == "admin-required"


def test_only_a_404_that_names_the_reason_is_an_absence():
    assert is_absence(404, ABSENT_404) is True
    assert is_absence(404, "Not Found") is False
    assert visibility(404, ABSENT_404) == "not-protected"
    assert visibility(404, "Not Found") == "ambiguous-404"


def test_the_three_outcomes_stay_three():
    assert visibility(200, "") == "readable"
    assert visibility(500, "") == "unknown"
    assert visibility(None, "") == "unknown"


def test_a_refused_read_on_a_protected_branch_is_protected_and_unmeasured():
    state, detail = verdict(True, 403, ADMIN_403, RULES)
    assert state == "protected-rules-hidden"
    assert "not readable by this token" in detail
    assert "2 ruleset rule(s)" in detail
    assert "administration: read" in repair(state)


def test_a_protected_branch_with_readable_rules_is_the_measured_case():
    state, _ = verdict(True, 200, "", [])
    assert state == "protected-rules-readable"


def test_an_unprotected_branch_needs_both_readings_to_agree():
    assert verdict(False, 404, ABSENT_404, [])[0] == "unprotected-confirmed"
    state, detail = verdict(False, 403, ADMIN_403, [])
    assert state == "unprotected-by-flag"
    assert "visible without admin" in detail
    assert "already see" in repair(state)


def test_a_ruleset_protects_a_branch_that_reports_protected_false():
    state, detail = verdict(False, 404, ABSENT_404, RULES)
    assert state == "ruleset-only"
    assert "from a ruleset" in detail
    assert "read the ruleset" in repair(state)


def test_a_branch_that_did_not_come_back_is_not_a_protection_finding():
    state, _ = verdict(None, 404, "Not Found", [])
    assert state == "branch-unreadable"
    assert "triage the repository" in repair(state)


def test_the_refusals_are_derived_from_fields_not_from_a_push():
    lines = refused_writes(PROTECTION)
    assert "a direct push is refused: 2 approving review(s) are required through a pull request" in lines
    assert "a merge is refused until 2 status check(s) pass" in lines
    assert "a merge is refused while the branch is behind its base" in lines
    assert "administrators are not exempt from any of the above" in lines
    assert "a push is refused for everyone except 2 listed actor(s)" in lines
    assert "a force push is refused" in lines
    assert "deleting the branch is refused" in lines
    assert refused_writes(None) == []


def test_an_unsigned_commit_rule_is_only_reported_when_enabled():
    assert "an unsigned commit is refused" not in refused_writes(PROTECTION)
    signed = dict(PROTECTION, required_signatures={"enabled": True})
    assert "an unsigned commit is refused" in refused_writes(signed)


def test_a_locked_branch_refuses_everything():
    locked = dict(PROTECTION, lock_branch={"enabled": True})
    assert "the branch is locked, so every write is refused" in refused_writes(locked)


def test_the_ruleset_listing_describes_the_same_refusals_without_admin():
    lines = refused_by_rules(RULES)
    assert "a pull request is required, so a direct push to this branch is refused" in lines
    assert "non-fast-forward updates are blocked, so a force push is refused" in lines
    assert refused_by_rules([]) == []
    assert refused_by_rules("not a list") == []
    assert rulesets_named(RULES) == ["acme"]


def test_the_allowlist_reports_names_and_nothing_else():
    assert push_allowlist(PROTECTION) == ["user:release-bot", "team:platform"]
    assert push_allowlist({}) == []
    assert push_allowlist(None) == []


def test_an_unknown_row_never_becomes_an_unprotected_row():
    counts = coverage(["protected-rules-hidden", "unknown", "branch-unreadable",
                       "unprotected-confirmed", "protected-rules-readable"])
    assert counts == {"protected": 2, "readable_in_detail": 1,
                      "unprotected": 1, "unknown": 2}
    state, detail = instrument_verdict(counts)
    assert state == "instrument-gap"
    assert "2 of 5" in detail


def test_a_sweep_with_no_detail_says_so_rather_than_claiming_a_measurement():
    counts = coverage(["protected-rules-hidden", "protected-rules-hidden"])
    state, detail = instrument_verdict(counts)
    assert state == "coverage-only"
    assert "detail is absent" in detail
    assert instrument_verdict({})[0] == "no-rows"
    assert instrument_verdict(coverage(["protected-rules-readable"]))[0] == "measured"


def test_targets_and_cost_are_worked_out_before_anything_is_fetched():
    assert split_target("acme/platform-api:release/2.1") == (
        "acme", "platform-api", "release/2.1")
    assert split_target("acme/platform-api") == ("acme", "platform-api", "main")
    assert split_target("platform-api") is None
    assert split_target("") is None
    assert REQUESTS_PER_BRANCH == 3
    assert read_cost(["a", "b"]) == 6
    assert read_cost([]) == 0
    assert read_cost(None) == 0
''',
"test_js_file": "github-branch-protection-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  REQUESTS_PER_BRANCH, coverage, instrumentVerdict, isAbsence, pushAllowlist,
  readCost, refusedByRules, refusedWrites, repair, rulesetsNamed, splitTarget,
  verdict, visibility,
} from './github-branch-protection-audit.mjs';

const ADMIN_403 = 'Must have admin rights to Repository.';
const ABSENT_404 = 'Branch not protected';

const PROTECTION = {
  required_pull_request_reviews: { required_approving_review_count: 2 },
  required_status_checks: { strict: true, contexts: ['build', 'lint'] },
  enforce_admins: { enabled: true },
  restrictions: {
    users: [{ login: 'release-bot' }], teams: [{ slug: 'platform' }], apps: [],
  },
  required_signatures: { enabled: false },
  allow_force_pushes: { enabled: false },
  allow_deletions: { enabled: false },
};

const RULES = [
  { type: 'pull_request', ruleset_id: 42, ruleset_source: 'acme' },
  { type: 'non_fast_forward', ruleset_id: 42, ruleset_source: 'acme' },
];

test('a 403 is never evidence that a branch is unprotected', () => {
  assert.equal(isAbsence(403, ADMIN_403), false);
  assert.equal(isAbsence(403, ABSENT_404), false);
  assert.equal(visibility(403, ADMIN_403), 'admin-required');
});

test('only a 404 that names the reason is an absence', () => {
  assert.equal(isAbsence(404, ABSENT_404), true);
  assert.equal(isAbsence(404, 'Not Found'), false);
  assert.equal(visibility(404, ABSENT_404), 'not-protected');
  assert.equal(visibility(404, 'Not Found'), 'ambiguous-404');
});

test('the three outcomes stay three', () => {
  assert.equal(visibility(200, ''), 'readable');
  assert.equal(visibility(500, ''), 'unknown');
  assert.equal(visibility(null, ''), 'unknown');
});

test('a refused read on a protected branch is protected and unmeasured', () => {
  const [state, detail] = verdict(true, 403, ADMIN_403, RULES);
  assert.equal(state, 'protected-rules-hidden');
  assert.match(detail, /not readable by this token/);
  assert.match(detail, /2 ruleset rule\\(s\\)/);
  assert.match(repair(state), /administration: read/);
});

test('a protected branch with readable rules is the measured case', () => {
  assert.equal(verdict(true, 200, '', [])[0], 'protected-rules-readable');
});

test('an unprotected branch needs both readings to agree', () => {
  assert.equal(verdict(false, 404, ABSENT_404, [])[0], 'unprotected-confirmed');
  const [state, detail] = verdict(false, 403, ADMIN_403, []);
  assert.equal(state, 'unprotected-by-flag');
  assert.match(detail, /visible without admin/);
  assert.match(repair(state), /already see/);
});

test('a ruleset protects a branch that reports protected false', () => {
  const [state, detail] = verdict(false, 404, ABSENT_404, RULES);
  assert.equal(state, 'ruleset-only');
  assert.match(detail, /from a ruleset/);
  assert.match(repair(state), /read the ruleset/);
});

test('a branch that did not come back is not a protection finding', () => {
  const [state] = verdict(null, 404, 'Not Found', []);
  assert.equal(state, 'branch-unreadable');
  assert.match(repair(state), /triage the repository/);
});

test('the refusals are derived from fields not from a push', () => {
  const lines = refusedWrites(PROTECTION);
  assert.ok(lines.includes('a direct push is refused: 2 approving review(s) are '
    + 'required through a pull request'));
  assert.ok(lines.includes('a merge is refused until 2 status check(s) pass'));
  assert.ok(lines.includes('a merge is refused while the branch is behind its base'));
  assert.ok(lines.includes('administrators are not exempt from any of the above'));
  assert.ok(lines.includes('a push is refused for everyone except 2 listed actor(s)'));
  assert.ok(lines.includes('a force push is refused'));
  assert.ok(lines.includes('deleting the branch is refused'));
  assert.deepEqual(refusedWrites(null), []);
});

test('an unsigned commit rule is only reported when enabled', () => {
  assert.ok(!refusedWrites(PROTECTION).includes('an unsigned commit is refused'));
  const signed = { ...PROTECTION, required_signatures: { enabled: true } };
  assert.ok(refusedWrites(signed).includes('an unsigned commit is refused'));
});

test('a locked branch refuses everything', () => {
  const locked = { ...PROTECTION, lock_branch: { enabled: true } };
  assert.ok(refusedWrites(locked).includes(
    'the branch is locked, so every write is refused'));
});

test('the ruleset listing describes the same refusals without admin', () => {
  const lines = refusedByRules(RULES);
  assert.ok(lines.includes(
    'a pull request is required, so a direct push to this branch is refused'));
  assert.ok(lines.includes(
    'non-fast-forward updates are blocked, so a force push is refused'));
  assert.deepEqual(refusedByRules([]), []);
  assert.deepEqual(refusedByRules('not a list'), []);
  assert.deepEqual(rulesetsNamed(RULES), ['acme']);
});

test('the allowlist reports names and nothing else', () => {
  assert.deepEqual(pushAllowlist(PROTECTION), ['user:release-bot', 'team:platform']);
  assert.deepEqual(pushAllowlist({}), []);
  assert.deepEqual(pushAllowlist(null), []);
});

test('an unknown row never becomes an unprotected row', () => {
  const counts = coverage(['protected-rules-hidden', 'unknown',
    'branch-unreadable', 'unprotected-confirmed', 'protected-rules-readable']);
  assert.deepEqual(counts, {
    protected: 2, readable_in_detail: 1, unprotected: 1, unknown: 2,
  });
  const [state, detail] = instrumentVerdict(counts);
  assert.equal(state, 'instrument-gap');
  assert.match(detail, /2 of 5/);
});

test('a sweep with no detail says so rather than claiming a measurement', () => {
  const counts = coverage(['protected-rules-hidden', 'protected-rules-hidden']);
  const [state, detail] = instrumentVerdict(counts);
  assert.equal(state, 'coverage-only');
  assert.match(detail, /detail is absent/);
  assert.equal(instrumentVerdict({})[0], 'no-rows');
  assert.equal(instrumentVerdict(coverage(['protected-rules-readable']))[0], 'measured');
});

test('targets and cost are worked out before anything is fetched', () => {
  assert.deepEqual(splitTarget('acme/platform-api:release/2.1'),
    ['acme', 'platform-api', 'release/2.1']);
  assert.deepEqual(splitTarget('acme/platform-api'), ['acme', 'platform-api', 'main']);
  assert.equal(splitTarget('platform-api'), null);
  assert.equal(splitTarget(''), null);
  assert.equal(REQUESTS_PER_BRANCH, 3);
  assert.equal(readCost(['a', 'b']), 6);
  assert.equal(readCost([]), 0);
  assert.equal(readCost(null), 0);
});
''',
"faq": [
 ("Why not just catch the error and assume no protection?",
  "Because the two errors mean opposite things and only one of them is about the branch. A 404 saying &ldquo;Branch not protected&rdquo; is a measurement: the branch has no protection and the API is telling you so. A 403 saying admin rights are required is a measurement of your token: the branch may be protected to the hilt and you are not allowed to look. Folding them together produces a compliance report whose numbers depend on who ran it, which is worse than no report, because it will be believed once and then distrusted forever."),
 ("Do I have to give the auditing token repository admin?",
  "Only if you need the detail. The <code>protected</code> boolean on the branch object answers the coverage question and needs nothing beyond read access, and the ruleset rules for a branch are published to anyone who can read the repository. Repository admin brings settings, collaborators, deploy keys and deletion with it, which is a lot to hand a scheduled job for the sake of one field. Where the detailed rules genuinely matter, a GitHub App with <code>administration: read</code> is the narrow version of the same grant and is what to reach for."),
 ("The branch says protected=false but pushes are still refused. Why?",
  "A ruleset. Rulesets are a separate mechanism from classic branch protection, they can be defined at the organisation level and applied to many repositories at once, and a branch governed entirely by one can refuse pull requests, force pushes and deletions without the classic protection settings existing at all. Read <code>GET /repos/{owner}/{repo}/rules/branches/{branch}</code>, which lists the rules reaching that branch and names the ruleset each came from. The script reports this as its own state rather than as a contradiction."),
 ("Should the script push a commit to confirm what is blocked?",
  "No, and it does not. Every script in this section holds a token that can reach real repositories and none of them writes. It is also unnecessary: required reviews, required status checks, the push allowlist, force-push and deletion settings, and whether administrators are exempt are all fields on an object you can read. The script turns those fields into sentences about what a push would meet. Creating a commit on somebody's default branch to learn a fact that is already published is a change, not a diagnostic."),
 ("What about the 404 that does not say Branch not protected?",
  "That one is ambiguous and the script refuses to resolve it. A bare 404 on this path can mean the branch does not exist, the repository does not exist, the repository is private and invisible to this credential, or an App is not installed on it &mdash; and GitHub answers 404 rather than 403 for private resources precisely so those cannot be told apart. It is a credential triage rather than a protection finding, and it gets counted in the unknown column where somebody can act on it."),
],
"related": [
 ("/github/404-masking-403/", "A 404 that means four different things at once"),
 ("/github/repo-archived-writes-403/", "The repository itself refuses every write"),
 ("/github/over-scoped-token/", "What granting admin to a read-only job costs"),
],
"citations": [CITE_BRANCH_PROTECTION, CITE_BRANCHES, CITE_RULES, CITE_ABOUT_PROTECTED],
},
{
"slug": "repo-archived-writes-403",
"title": "The repository is archived so every write returns 403",
"description": "Reads work perfectly and writes 403 forever. The archived boolean on the repository explains it in one field, and it is a permanent skip, not a retry.",
"h1": "the repository is archived so every write returns 403",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api 403 repository was archived",
             "repository was archived so is read-only github api",
             "github archived repository write 403 bot",
             "github api archived boolean skip automation",
             "github org sweep archived repositories list"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The labelling bot has been failing on one repository since March. Everything it reads comes back perfectly: issues, labels, the repository object itself, all 200. The moment it tries to add a label it gets <code>403</code>, so the on-call runbook says permissions, so somebody widens the token, and it still gets 403. The token was never the problem. Somebody archived the repository seven months ago, which makes it read-only for everyone and every credential, and the bot has been retrying a request that will not be accepted by anyone until it is unarchived.",
"short_answer": """<p>Archiving a repository makes it read-only. The API keeps serving every read, which is why the failure looks selective, and refuses every write with <code>403</code> and a message about the repository being archived &mdash; regardless of the token, the scopes, the App permissions or the caller's role.</p>
<p>One field settles it before any write is attempted: <code>GET /repos/{owner}/{repo}</code> returns <code>archived</code>, alongside <code>disabled</code>. For a whole organisation, <code>GET /orgs/{org}/repos?type=all&amp;per_page=100</code> returns the same boolean per repository. Filter <code>archived: true</code> out at the top of any write-path loop and treat it as a <strong>permanent skip</strong> rather than a retryable error. Nothing in your integration can fix it; only unarchiving can, and that is a decision about whether the repository is still in use.</p>""",
"problem": """<p>Everything about this points at credentials. A 403 is the permission-denied status, the failure is on one repository out of many, and the same token works everywhere else &mdash; which is the exact signature of a narrowed grant. So the investigation goes where that signature leads: check the scopes, check the App installation, check whether the repository was left off a selective installation, mint a wider token, try again. Each of those is an hour, each of them is reasonable, and none of them changes the answer.</p>
<p>The read path making it worse is the cruel part. If the repository had gone away entirely, the bot would have got 404s on everything and somebody would have looked at the repository first. Instead the repository is completely healthy from the outside: it lists, it reads, its issues are all there, its metadata is current. A resource that answers every question except one looks like an authorisation problem, because normally that is what it is.</p>
<p>Then the retry logic quietly makes it expensive. A 403 is usually transient enough to be worth retrying &mdash; rate limits arrive as 403 &mdash; so most clients retry it, some with backoff and some without. A daily job with three retries against forty archived repositories is a few hundred requests a day spent on a refusal that has been permanent since March, and because the failures are caught and logged the job still reports success. Nobody sees the number until somebody asks why the quota chart has a floor under it.</p>""",
"why": """<p><strong>Read-only is the whole feature.</strong> Archiving exists to preserve a repository as it was: readable, searchable, cloneable, and frozen. The API implements exactly that, so a read and a write to the same path get different answers by design. The response says so &mdash; the message names the repository as archived &mdash; but it arrives as a 403 alongside every other kind of refusal, and most clients bucket by status code long before they read a message.</p>
<p><strong>No credential can override it.</strong> This is the unusual part and the reason it wastes so much time. Every other 403 in this section is answered by changing what the caller holds: <a href="/github/missing-oauth-scope/">a scope that was never granted</a>, <a href="/github/app-permission-missing/">a permission the endpoint wanted</a>, an installation that was narrowed. Here the owner of the repository, with admin and a token that can delete organisations, gets the same 403. The state belongs to the repository, so no amount of work on the credential moves it.</p>
<p><strong>It is permanent until a human decides otherwise, so it is a skip and not a retry.</strong> Retrying is the correct response to a rate limit, a 502 and a timeout, and it is the wrong response to this. The classification a client needs is not &ldquo;is this a 403&rdquo; but &ldquo;can this ever succeed&rdquo;, and <code>archived</code> answers that in advance, before the request is sent, for free, on a field the client is usually already fetching.</p>
<p><strong>Filter at the top of the loop, not in the error handler.</strong> The reason to read <code>archived</code> up front rather than parse the 403 afterwards is that the up-front version costs nothing and covers everything. One organisation listing at <code>per_page=100</code> gives you the boolean for every repository you were about to touch, in one request per hundred repositories, and the write loop simply never visits them. Handling it in the error path means you pay for the failed request every time, for every repository, forever.</p>
<p><strong><code>archived</code> and <code>disabled</code> are different states and sit next to each other.</strong> They arrive in the same response and are easy to conflate, and they should not be: an archived repository is fully readable and was frozen deliberately by someone on your side, while <a href="/github/repo-disabled/">a disabled one</a> is not fully readable and was disabled by GitHub over billing or a terms problem. The remedies have different owners, so the report keeps them apart.</p>
<p><strong>This script never attempts the write.</strong> It reads <code>archived</code> and reports it, and where you paste in a refusal you already recorded it attributes that message. Sending a write to an archived repository to watch the 403 arrive would prove the same fact one request later, and it would be a write &mdash; against a repository somebody deliberately froze, which is the last place to be experimenting.</p>""",
"steps": [
 {"h": "Read the boolean before the loop, not the error after it",
  "body": """<p>One <code>GET /repos/{owner}/{repo}</code> per repository, or one <code>GET /orgs/{org}/repos?type=all&amp;per_page=100</code> per hundred repositories for a whole organisation. <code>archived</code> comes back on every one of them. This is the entire detection and it happens before a single write is contemplated.</p>"""},
 {"h": "Separate archived from disabled while you are there",
  "body": """<p>The same response carries <code>disabled</code>. They mean different things, have different owners and need different reports, so the script classifies into four states rather than two and hands the disabled ones to their own note. A repository can be both, and that is reported as both.</p>"""},
 {"h": "Classify the state as permanent or retryable",
  "body": """<p>The output your client needs is not the status code, it is the policy: <em>permanent skip</em> for archived and disabled, <em>retry</em> for the transient failures, <em>unknown</em> where the repository could not be read. Wire that verdict into the write path and the retry loop stops existing for these repositories rather than being tuned.</p>"""},
 {"h": "Price the retries you have already spent",
  "body": """<p>Give the script <code>--attempts-per-hour</code> and it multiplies out what a retrying client has been spending against the hourly core quota on requests that could never have been accepted. This is usually the number that gets the fix prioritised, because it converts &ldquo;some errors in the log&rdquo; into a share of the quota that everything else on that token is competing for.</p>"""},
 {"h": "Attribute a 403 you already recorded, without reproducing it",
  "body": """<p>Paste the message from your logs into <code>--failure-message</code> and the script names the cause rather than leaving you to infer it: an archived repository, a rate limit, a credential refusal or something else. It does not reproduce the failure to check. The repository object already said <code>archived: true</code>, and a second opinion obtained by writing to somebody's frozen repository is not worth having.</p>"""},
],
"verify": """<p>After the filter is at the top of the loop, the archived repositories are skipped rather than attempted, and the requests they were consuming come back.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_archived_repo_guard.py \\
    --org acme --attempts-per-hour 12 \\
    --failure-message "Repository was archived so is read-only."
# read cost: 1 request(s) per 100 repositories in an org sweep
# acme: 212 repository(ies) read in 3 request(s)
# acme/legacy-billing: archived
#   permanent-skip: archiving makes a repository read-only, so no write will
#   ever be accepted here regardless of the token
#   last push 214 day(s) ago
#   repair: filter archived repositories out at the top of the write loop and
#   treat this as a permanent skip. Unarchive only if it is genuinely in use.
# acme/legacy-reports: archived
# acme/vendor-mirror: archived
#
# recorded failure -> archived-refusal: the message names the repository as
# archived, which is a property of the repository and not of your credential
# retry cost: 12 attempt(s)/hour against 3 archived repository(ies) is 36
# request(s)/hour, 864 a day, 17% of a 5000/hour quota
# summary: 212 repositories, 3 archived, 0 disabled, 209 writable</code></pre>""",
"code_intro": "The detection is one field, so the code around it is about what to do with the field rather than how to obtain it. The classification is pure and has four states because <code>archived</code> and <code>disabled</code> can each be true independently; the retry policy is a separate function from the state because it is the part that goes into your client; and the arithmetic exists to turn a log line into a number of requests an hour. The one thing the script will not do is attempt the write, so the sweep and the attribution both work from readable state and from a message you already have.",
"py_file": "github_archived_repo_guard.py",
"py": '''"""Find archived repositories before a write loop discovers them the hard way.

Read only. One GET per repository, or one per hundred in an organisation
sweep, and nothing is written. In particular no write is attempted against an
archived repository to confirm the 403: the archived boolean on the repository
object is the finding, it arrives before any write would be sent, and the
repository was deliberately frozen by somebody who would rather it stayed that
way.

The point of the note: archiving makes a repository read-only. Reads keep
working, which is why the failure looks selective and looks like permissions,
and every write is refused with 403 regardless of the token, the scopes, the
App permissions or the caller's role. No credential change fixes it.

What this can and cannot see: whether your own client retries a 403 is
invisible from here, so the retry cost is computed from a rate you supply. The
archived boolean itself is exact.

Environment:

    GITHUB_TOKEN    a token with read access to the repositories
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_archived_repo_guard")

API = "https://api.github.com"
UA = "github-archived-repo-guard/1.0"

# The core hourly quota a retrying client is spending these requests out of.
CORE_QUOTA_PER_HOUR = 5000

# One listing request covers this many repositories.
ORG_PAGE_SIZE = 100

# Words that identify an archived repository in a refusal you already recorded.
ARCHIVED_WORDS = ("archived", "read-only", "read only")


def lifecycle(repo):
    """Which platform state this repository is in. Pure.

    Four states rather than two: archived and disabled are separate booleans
    that arrive in the same response, they can both be set, and they have
    different owners and different remedies.
    """
    if not isinstance(repo, dict):
        return "unknown"
    archived = bool(repo.get("archived"))
    disabled = bool(repo.get("disabled"))
    if archived and disabled:
        return "archived-and-disabled"
    if archived:
        return "archived"
    if disabled:
        return "disabled"
    return "active"


def accepts_writes(state):
    """Whether a write to this repository can ever be accepted. Pure."""
    if state in ("archived", "disabled", "archived-and-disabled"):
        return False
    if state == "active":
        return True
    return None


def retry_policy(state):
    """What a client should do with a failure here. Pure.

    This is the output that belongs in the write path. A 403 from a rate limit
    is worth retrying and a 403 from an archived repository never is, and the
    status code cannot tell them apart.
    """
    if accepts_writes(state) is False:
        return "permanent-skip"
    if state == "active":
        return "retry"
    return "unknown"


def explain(state):
    """Why this repository refuses writes, in one sentence. Pure."""
    if state == "archived":
        return ("archiving makes a repository read-only, so no write will ever "
                "be accepted here regardless of the token.")
    if state == "disabled":
        return ("the repository is disabled, which is a different state with a "
                "different owner: see the disabled repository note.")
    if state == "archived-and-disabled":
        return ("the repository is both archived and disabled. Unarchiving it "
                "would still leave it disabled, so the disabled state is the "
                "one to resolve first.")
    if state == "active":
        return "the repository accepts writes; this refusal is about something else."
    return "the repository could not be read, so its state is unknown."


def classify_failure(status, message):
    """Attribute a refusal you already recorded. Pure. (state, detail).

    Nothing is sent to produce this. The message comes out of your logs, and
    the repository object has already answered the same question independently.
    """
    text = str(message or "").lower()
    try:
        code = int(status)
    except (TypeError, ValueError):
        code = None

    if any(word in text for word in ARCHIVED_WORDS):
        return ("archived-refusal",
                "the message names the repository as archived, which is a "
                "property of the repository and not of your credential.")
    if "rate limit" in text:
        return ("rate-limited",
                "a rate limit, which is a transient 403 and the one kind worth "
                "retrying. That is a different note.")
    if "not accessible" in text or "integration" in text or "personal access token" in text:
        return ("credential-refusal",
                "the message blames the credential rather than the repository, "
                "so this is a permissions problem and widening the grant may "
                "actually help.")
    if code == 404:
        return ("not-found",
                "404 rather than 403, which means several things at once and "
                "needs its own triage.")
    if code == 403:
        return ("forbidden-unattributed",
                "a 403 whose message names neither the repository state nor a "
                "rate limit. Read the repository object to settle it.")
    return ("no-failure", "nothing here names a refusal.")


def days_since(timestamp, now=None):
    """Whole days between an ISO 8601 timestamp and now. Pure. None if absent."""
    if not timestamp:
        return None
    text = str(timestamp).replace("Z", "+00:00")
    try:
        when = datetime.fromisoformat(text)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return max(0, (now - when).days)


def wasted_requests(attempts_per_hour, repositories, hours=1):
    """Requests a retrying client spends on refusals that cannot succeed. Pure."""
    try:
        rate = max(0, int(attempts_per_hour or 0))
        count = max(0, int(repositories or 0))
        span = max(0, int(hours or 0))
    except (TypeError, ValueError):
        return 0
    return rate * count * span


def quota_share(requests_per_hour, quota=CORE_QUOTA_PER_HOUR):
    """That spend as a whole-number percentage of the hourly quota. Pure."""
    try:
        spend = max(0, int(requests_per_hour or 0))
    except (TypeError, ValueError):
        return 0
    if not quota:
        return 0
    return int(round(100.0 * spend / quota))


def skip_list(rows):
    """The repositories a write loop should never visit. Pure and sorted."""
    names = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        if accepts_writes(row.get("state")) is False and row.get("full_name"):
            names.append(str(row["full_name"]))
    return sorted(set(names))


def summarise(rows):
    """Counts for the bottom of the report. Pure."""
    counts = {"total": 0, "archived": 0, "disabled": 0, "writable": 0,
              "unknown": 0}
    for row in rows or []:
        state = (row or {}).get("state")
        counts["total"] += 1
        if state in ("archived", "archived-and-disabled"):
            counts["archived"] += 1
        if state in ("disabled", "archived-and-disabled"):
            counts["disabled"] += 1
        if state == "active":
            counts["writable"] += 1
        if state == "unknown":
            counts["unknown"] += 1
    return counts


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "archived":
        return ("filter archived repositories out at the top of the write loop "
                "and treat this as a permanent skip. Unarchive only if the "
                "repository is genuinely still in use.")
    if state == "disabled":
        return ("see /github/repo-disabled/ -- a disabled repository is a "
                "different state with a different owner, usually billing or a "
                "terms problem rather than a decision on your side.")
    if state == "archived-and-disabled":
        return ("resolve the disabled state with GitHub first; unarchiving on "
                "its own will not make this repository writable.")
    if state == "active":
        return ("nothing here. This repository accepts writes, so a refusal "
                "against it is about the credential or the branch.")
    if state == "archived-refusal":
        return ("stop retrying and skip. No token, scope or App permission "
                "makes an archived repository writable.")
    if state == "rate-limited":
        return ("honour retry-after and slow down. This one really is worth "
                "retrying.")
    if state == "credential-refusal":
        return ("triage the credential: the message blames the token or the "
                "integration rather than the repository state.")
    return ("read the repository object and use the archived and disabled "
            "booleans rather than inferring state from a status code.")


def read_cost_for_repos(repos):
    """Requests a per-repository run will spend. Pure."""
    return len(repos or [])


def pages_for(count, page_size=ORG_PAGE_SIZE):
    """Listing requests an organisation of this size needs. Pure."""
    try:
        total = max(0, int(count or 0))
    except (TypeError, ValueError):
        return 0
    if not total:
        return 0
    return (total + page_size - 1) // page_size


def parse_link(header):
    """The Link header as {rel: url}. Pure.

    Scanned rather than split on commas, because a URL may contain one and a
    naive split turns the next page into two unusable halves.
    """
    text = str(header or "")
    links, i = {}, 0
    while True:
        start = text.find("<", i)
        if start < 0:
            break
        end = text.find(">", start)
        if end < 0:
            break
        url = text[start + 1:end]
        tail = text[end + 1:]
        stop = tail.find("<")
        segment = tail if stop < 0 else tail[:stop]
        rel = ""
        for bit in segment.split(";"):
            bit = bit.strip()
            if bit.startswith("rel="):
                rel = bit[4:].strip().strip(",").strip('"')
        if rel:
            links[rel] = url
        i = end + 1
    return links


def row_for(repo):
    """One report row from one repository object. Pure."""
    state = lifecycle(repo)
    return {
        "full_name": (repo or {}).get("full_name"),
        "state": state,
        "accepts_writes": accepts_writes(state),
        "retry_policy": retry_policy(state),
        "explanation": explain(state),
        "days_since_last_push": days_since((repo or {}).get("pushed_at")),
        "repair": repair(state),
    }


def get_repo(session, full_name):
    """One GET of a repository object. Returns a dict or None."""
    r = session.get(API + "/repos/" + full_name, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset "
                         "time and does not itself consume quota")
    if r.status_code != 200:
        return None
    try:
        body = r.json()
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def list_org_repos(session, org, max_pages=20):
    """Every repository in an organisation. Returns (repos, requests_spent)."""
    url = "%s/orgs/%s/repos?type=all&per_page=%d" % (API, org, ORG_PAGE_SIZE)
    repos, spent = [], 0
    while url and spent < max_pages:
        r = session.get(url, timeout=30)
        spent += 1
        if r.status_code != 200:
            break
        try:
            page = r.json()
        except ValueError:
            break
        if not isinstance(page, list):
            break
        repos.extend(item for item in page if isinstance(item, dict))
        url = parse_link(r.headers.get("Link")).get("next")
    return repos, spent


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", default=[],
                    help="owner/name to check. Repeatable.")
    ap.add_argument("--org", help="sweep every repository in an organisation")
    ap.add_argument("--attempts-per-hour", type=int, default=0,
                    help="how often your write loop retries a failing "
                         "repository, so the waste can be stated in requests")
    ap.add_argument("--failure-message", default="",
                    help="a refusal you already recorded, to attribute it "
                         "without reproducing it")
    ap.add_argument("--failure-status", default="",
                    help="the status code recorded alongside it")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2
    if not args.repo and not args.org:
        log.error("give at least one --repo or an --org to sweep")
        return 2

    if args.repo:
        log.info("read cost: %d request(s) against the core hourly quota",
                 read_cost_for_repos(args.repo))
    if args.org:
        log.info("read cost: 1 request(s) per %d repositories in an org sweep",
                 ORG_PAGE_SIZE)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    rows = []
    if args.org:
        repos, spent = list_org_repos(session, args.org)
        log.info("%s: %d repository(ies) read in %d request(s)", args.org,
                 len(repos), spent)
        rows.extend(row_for(repo) for repo in repos)
    for name in args.repo:
        repo = get_repo(session, name)
        if repo is None:
            rows.append({"full_name": name, "state": "unknown",
                         "accepts_writes": None, "retry_policy": "unknown",
                         "explanation": explain("unknown"),
                         "days_since_last_push": None,
                         "repair": repair("unknown")})
        else:
            rows.append(row_for(repo))

    frozen = [row for row in rows if row["accepts_writes"] is False]
    for row in frozen:
        log.info("%s: %s", row["full_name"], row["state"])
        log.info("  %s: %s", row["retry_policy"], row["explanation"])
        if row["days_since_last_push"] is not None:
            log.info("  last push %d day(s) ago", row["days_since_last_push"])
        log.info("  repair: %s", row["repair"])

    recorded = None
    if args.failure_message or args.failure_status:
        state, detail = classify_failure(args.failure_status, args.failure_message)
        log.info("recorded failure -> %s: %s", state, detail)
        log.info("repair: %s", repair(state))
        recorded = {"state": state, "detail": detail}

    spend = wasted_requests(args.attempts_per_hour, len(frozen))
    if spend:
        log.info("retry cost: %d attempt(s)/hour against %d frozen "
                 "repository(ies) is %d request(s)/hour, %d a day, %d%% of a "
                 "%d/hour quota", args.attempts_per_hour, len(frozen), spend,
                 spend * 24, quota_share(spend), CORE_QUOTA_PER_HOUR)

    counts = summarise(rows)
    log.info("summary: %d repositories, %d archived, %d disabled, %d writable",
             counts["total"], counts["archived"], counts["disabled"],
             counts["writable"])

    print(json.dumps({
        "counts": counts,
        "skip_list": skip_list(rows),
        "wasted_requests_per_hour": spend,
        "quota_share_percent": quota_share(spend),
        "recorded_failure": recorded,
        "repositories": rows,
    }, indent=2, default=str))
    return 1 if frozen else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-archived-repo-guard.mjs",
"js": '''/**
 * Find archived repositories before a write loop discovers them the hard way.
 *
 * Read only. One GET per repository, or one per hundred in an organisation
 * sweep, and nothing is written. No write is attempted against an archived
 * repository to confirm the 403: the archived boolean is the finding and it
 * arrives before any write would be sent.
 *
 * Archiving makes a repository read-only. Reads keep working, every write is
 * refused with 403, and no token, scope or App permission changes that.
 *
 * Environment:
 *   GITHUB_TOKEN      a token with read access to the repositories
 *   GITHUB_REPOS      comma-separated owner/name values
 *   GITHUB_ORG        an organisation to sweep instead
 *   GITHUB_ATTEMPTS   retries an hour your write loop makes
 *   GITHUB_FAILURE    a refusal message you already recorded
 */
const API = 'https://api.github.com';
const UA = 'github-archived-repo-guard/1.0';

/** The core hourly quota a retrying client spends these requests out of. */
export const CORE_QUOTA_PER_HOUR = 5000;

/** One listing request covers this many repositories. */
export const ORG_PAGE_SIZE = 100;

/** Words that identify an archived repository in a recorded refusal. */
export const ARCHIVED_WORDS = ['archived', 'read-only', 'read only'];

/** Which platform state this repository is in. Pure. */
export function lifecycle(repo) {
  if (!repo || typeof repo !== 'object') return 'unknown';
  const archived = Boolean(repo.archived);
  const disabled = Boolean(repo.disabled);
  if (archived && disabled) return 'archived-and-disabled';
  if (archived) return 'archived';
  if (disabled) return 'disabled';
  return 'active';
}

/** Whether a write to this repository can ever be accepted. Pure. */
export function acceptsWrites(state) {
  if (['archived', 'disabled', 'archived-and-disabled'].includes(state)) return false;
  if (state === 'active') return true;
  return null;
}

/** What a client should do with a failure here. Pure. */
export function retryPolicy(state) {
  if (acceptsWrites(state) === false) return 'permanent-skip';
  if (state === 'active') return 'retry';
  return 'unknown';
}

/** Why this repository refuses writes, in one sentence. Pure. */
export function explain(state) {
  if (state === 'archived') {
    return 'archiving makes a repository read-only, so no write will ever be '
      + 'accepted here regardless of the token.';
  }
  if (state === 'disabled') {
    return 'the repository is disabled, which is a different state with a '
      + 'different owner: see the disabled repository note.';
  }
  if (state === 'archived-and-disabled') {
    return 'the repository is both archived and disabled. Unarchiving it would '
      + 'still leave it disabled, so the disabled state is the one to resolve first.';
  }
  if (state === 'active') {
    return 'the repository accepts writes; this refusal is about something else.';
  }
  return 'the repository could not be read, so its state is unknown.';
}

/** Attribute a refusal you already recorded. Pure. [state, detail]. */
export function classifyFailure(status, message) {
  const text = String(message ?? '').toLowerCase();
  const code = Number(status);

  if (ARCHIVED_WORDS.some((word) => text.includes(word))) {
    return ['archived-refusal', 'the message names the repository as archived, '
      + 'which is a property of the repository and not of your credential.'];
  }
  if (text.includes('rate limit')) {
    return ['rate-limited', 'a rate limit, which is a transient 403 and the one '
      + 'kind worth retrying. That is a different note.'];
  }
  if (text.includes('not accessible') || text.includes('integration')
    || text.includes('personal access token')) {
    return ['credential-refusal', 'the message blames the credential rather '
      + 'than the repository, so this is a permissions problem and widening the '
      + 'grant may actually help.'];
  }
  if (code === 404) {
    return ['not-found', '404 rather than 403, which means several things at '
      + 'once and needs its own triage.'];
  }
  if (code === 403) {
    return ['forbidden-unattributed', 'a 403 whose message names neither the '
      + 'repository state nor a rate limit. Read the repository object to settle it.'];
  }
  return ['no-failure', 'nothing here names a refusal.'];
}

/** Whole days between an ISO 8601 timestamp and now. Pure. Null if absent. */
export function daysSince(timestamp, now = Date.now()) {
  if (!timestamp) return null;
  const when = Date.parse(String(timestamp));
  if (!Number.isFinite(when)) return null;
  return Math.max(0, Math.floor((now - when) / 86400000));
}

/** Requests a retrying client spends on refusals that cannot succeed. Pure. */
export function wastedRequests(attemptsPerHour, repositories, hours = 1) {
  const rate = Math.max(0, Math.trunc(Number(attemptsPerHour) || 0));
  const count = Math.max(0, Math.trunc(Number(repositories) || 0));
  const span = Math.max(0, Math.trunc(Number(hours) || 0));
  return rate * count * span;
}

/** That spend as a whole-number percentage of the hourly quota. Pure. */
export function quotaShare(requestsPerHour, quota = CORE_QUOTA_PER_HOUR) {
  const spend = Math.max(0, Math.trunc(Number(requestsPerHour) || 0));
  if (!quota) return 0;
  return Math.round((100 * spend) / quota);
}

/** The repositories a write loop should never visit. Pure and sorted. */
export function skipList(rows) {
  const names = new Set();
  for (const row of rows || []) {
    if (!row || typeof row !== 'object') continue;
    if (acceptsWrites(row.state) === false && row.full_name) {
      names.add(String(row.full_name));
    }
  }
  return [...names].sort();
}

/** Counts for the bottom of the report. Pure. */
export function summarise(rows) {
  const counts = {
    total: 0, archived: 0, disabled: 0, writable: 0, unknown: 0,
  };
  for (const row of rows || []) {
    const state = (row || {}).state;
    counts.total += 1;
    if (['archived', 'archived-and-disabled'].includes(state)) counts.archived += 1;
    if (['disabled', 'archived-and-disabled'].includes(state)) counts.disabled += 1;
    if (state === 'active') counts.writable += 1;
    if (state === 'unknown') counts.unknown += 1;
  }
  return counts;
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'archived') {
    return 'filter archived repositories out at the top of the write loop and '
      + 'treat this as a permanent skip. Unarchive only if the repository is '
      + 'genuinely still in use.';
  }
  if (state === 'disabled') {
    return 'see /github/repo-disabled/ -- a disabled repository is a different '
      + 'state with a different owner, usually billing or a terms problem '
      + 'rather than a decision on your side.';
  }
  if (state === 'archived-and-disabled') {
    return 'resolve the disabled state with GitHub first; unarchiving on its '
      + 'own will not make this repository writable.';
  }
  if (state === 'active') {
    return 'nothing here. This repository accepts writes, so a refusal against '
      + 'it is about the credential or the branch.';
  }
  if (state === 'archived-refusal') {
    return 'stop retrying and skip. No token, scope or App permission makes an '
      + 'archived repository writable.';
  }
  if (state === 'rate-limited') {
    return 'honour retry-after and slow down. This one really is worth retrying.';
  }
  if (state === 'credential-refusal') {
    return 'triage the credential: the message blames the token or the '
      + 'integration rather than the repository state.';
  }
  return 'read the repository object and use the archived and disabled booleans '
    + 'rather than inferring state from a status code.';
}

/** Requests a per-repository run will spend. Pure. */
export function readCostForRepos(repos) {
  return (repos || []).length;
}

/** Listing requests an organisation of this size needs. Pure. */
export function pagesFor(count, pageSize = ORG_PAGE_SIZE) {
  const total = Math.max(0, Math.trunc(Number(count) || 0));
  if (!total) return 0;
  return Math.ceil(total / pageSize);
}

/** The Link header as {rel: url}. Pure. Comma-safe. */
export function parseLink(header) {
  const text = String(header ?? '');
  const links = {};
  let i = 0;
  for (;;) {
    const start = text.indexOf('<', i);
    if (start < 0) break;
    const end = text.indexOf('>', start);
    if (end < 0) break;
    const url = text.slice(start + 1, end);
    const tail = text.slice(end + 1);
    const stop = tail.indexOf('<');
    const segment = stop < 0 ? tail : tail.slice(0, stop);
    let rel = '';
    for (const raw of segment.split(';')) {
      const bit = raw.trim();
      if (bit.startsWith('rel=')) rel = bit.slice(4).trim().replace(/[",]/g, '');
    }
    if (rel) links[rel] = url;
    i = end + 1;
  }
  return links;
}

/** One report row from one repository object. Pure. */
export function rowFor(repo) {
  const state = lifecycle(repo);
  return {
    full_name: (repo || {}).full_name,
    state,
    accepts_writes: acceptsWrites(state),
    retry_policy: retryPolicy(state),
    explanation: explain(state),
    days_since_last_push: daysSince((repo || {}).pushed_at),
    repair: repair(state),
  };
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function listOrgRepos(token, org, maxPages = 20) {
  let url = `${API}/orgs/${org}/repos?type=all&per_page=${ORG_PAGE_SIZE}`;
  const repos = [];
  let spent = 0;
  while (url && spent < maxPages) {
    const res = await fetch(url, { headers: headers(token) });
    spent += 1;
    if (!res.ok) break;
    let page = null;
    try { page = await res.json(); } catch { page = null; }
    if (!Array.isArray(page)) break;
    repos.push(...page.filter((item) => item && typeof item === 'object'));
    url = parseLink(res.headers.get('link')).next;
  }
  return { repos, spent };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const org = process.env.GITHUB_ORG;
  const names = (process.env.GITHUB_REPOS || '').split(',')
    .map((n) => n.trim()).filter(Boolean);
  if (!token || (!org && !names.length)) {
    console.error('set GITHUB_TOKEN and either GITHUB_ORG or GITHUB_REPOS');
    process.exitCode = 2;
    return;
  }

  if (names.length) {
    console.log(`read cost: ${readCostForRepos(names)} request(s) against the `
      + 'core hourly quota');
  }
  if (org) {
    console.log(`read cost: 1 request(s) per ${ORG_PAGE_SIZE} repositories in `
      + 'an org sweep');
  }

  const rows = [];
  if (org) {
    const { repos, spent } = await listOrgRepos(token, org);
    console.log(`${org}: ${repos.length} repository(ies) read in ${spent} request(s)`);
    rows.push(...repos.map(rowFor));
  }
  for (const name of names) {
    const res = await fetch(`${API}/repos/${name}`, { headers: headers(token) });
    let body = null;
    try { body = await res.json(); } catch { body = null; }
    rows.push(res.status === 200 && body ? rowFor(body) : {
      full_name: name,
      state: 'unknown',
      accepts_writes: null,
      retry_policy: 'unknown',
      explanation: explain('unknown'),
      days_since_last_push: null,
      repair: repair('unknown'),
    });
  }

  const frozen = rows.filter((row) => row.accepts_writes === false);
  for (const row of frozen) {
    console.log(`${row.full_name}: ${row.state}`);
    console.log(`  ${row.retry_policy}: ${row.explanation}`);
    if (row.days_since_last_push !== null) {
      console.log(`  last push ${row.days_since_last_push} day(s) ago`);
    }
    console.log(`  repair: ${row.repair}`);
  }

  let recorded = null;
  const message = process.env.GITHUB_FAILURE || '';
  if (message) {
    const [state, detail] = classifyFailure('', message);
    console.log(`recorded failure -> ${state}: ${detail}`);
    console.log(`repair: ${repair(state)}`);
    recorded = { state, detail };
  }

  const attempts = Number(process.env.GITHUB_ATTEMPTS || 0);
  const spend = wastedRequests(attempts, frozen.length);
  if (spend) {
    console.log(`retry cost: ${attempts} attempt(s)/hour against ${frozen.length} `
      + `frozen repository(ies) is ${spend} request(s)/hour, ${spend * 24} a day, `
      + `${quotaShare(spend)}% of a ${CORE_QUOTA_PER_HOUR}/hour quota`);
  }

  const counts = summarise(rows);
  console.log(`summary: ${counts.total} repositories, ${counts.archived} `
    + `archived, ${counts.disabled} disabled, ${counts.writable} writable`);

  console.log(JSON.stringify({
    counts,
    skip_list: skipList(rows),
    wasted_requests_per_hour: spend,
    quota_share_percent: quotaShare(spend),
    recorded_failure: recorded,
    repositories: rows,
  }, null, 2));
  process.exitCode = frozen.length ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The state machine is asserted first, including the case people forget: a repository can be archived and disabled at once, and unarchiving it would still leave it refusing. Then the part that actually changes a client's behaviour &mdash; the retry policy, which has to come out as a permanent skip rather than as a status code &mdash; and the attribution of a refusal already in your logs, which is tested to blame the repository when the message names it and the credential when the message names that instead. The arithmetic and the Link parsing are pinned last, the latter with a comma inside a URL because that is what breaks a naive sweep on page two.",
"test_py_file": "test_github_archived_repo_guard.py",
"test_py": '''from github_archived_repo_guard import (
    CORE_QUOTA_PER_HOUR, ORG_PAGE_SIZE, accepts_writes, classify_failure,
    days_since, explain, lifecycle, pages_for, parse_link, quota_share,
    read_cost_for_repos, repair, retry_policy, row_for, skip_list, summarise,
    wasted_requests,
)

ARCHIVED = {"full_name": "acme/legacy-billing", "archived": True,
            "disabled": False, "pushed_at": "2025-01-27T09:14:00Z"}
ACTIVE = {"full_name": "acme/platform-api", "archived": False,
          "disabled": False, "pushed_at": "2026-08-20T09:14:00Z"}
DISABLED = {"full_name": "acme/suspended-thing", "archived": False,
            "disabled": True}
BOTH = {"full_name": "acme/frozen-and-gone", "archived": True, "disabled": True}


def test_the_two_booleans_make_four_states():
    assert lifecycle(ARCHIVED) == "archived"
    assert lifecycle(ACTIVE) == "active"
    assert lifecycle(DISABLED) == "disabled"
    assert lifecycle(BOTH) == "archived-and-disabled"
    assert lifecycle(None) == "unknown"
    assert lifecycle("not a repo") == "unknown"


def test_an_archived_repository_can_never_accept_a_write():
    assert accepts_writes("archived") is False
    assert accepts_writes("archived-and-disabled") is False
    assert accepts_writes("disabled") is False
    assert accepts_writes("active") is True
    assert accepts_writes("unknown") is None


def test_the_output_a_client_needs_is_a_policy_not_a_status_code():
    assert retry_policy("archived") == "permanent-skip"
    assert retry_policy("disabled") == "permanent-skip"
    assert retry_policy("active") == "retry"
    assert retry_policy("unknown") == "unknown"


def test_the_explanation_says_the_token_is_irrelevant():
    assert "regardless of the token" in explain("archived")
    assert "different owner" in explain("disabled")
    assert "would still leave it disabled" in explain("archived-and-disabled")
    assert "unknown" in explain("nonsense")


def test_a_recorded_refusal_is_attributed_without_being_reproduced():
    state, detail = classify_failure(403, "Repository was archived so is read-only.")
    assert state == "archived-refusal"
    assert "not of your credential" in detail
    assert "No token, scope or App permission" in repair(state)


def test_a_rate_limit_is_the_one_403_worth_retrying():
    state, _ = classify_failure(403, "API rate limit exceeded for user ID 1")
    assert state == "rate-limited"
    assert "retry-after" in repair(state)


def test_a_credential_refusal_is_handed_back_to_the_credential():
    state, detail = classify_failure(403, "Resource not accessible by integration")
    assert state == "credential-refusal"
    assert "blames the credential" in detail
    assert classify_failure(404, "Not Found")[0] == "not-found"
    assert classify_failure(403, "Forbidden")[0] == "forbidden-unattributed"
    assert classify_failure("", "")[0] == "no-failure"


def test_the_retry_waste_is_stated_in_requests_and_in_quota():
    assert wasted_requests(12, 3) == 36
    assert wasted_requests(12, 3, 24) == 864
    assert wasted_requests(0, 3) == 0
    assert wasted_requests(None, None) == 0
    assert quota_share(864) == 17
    assert quota_share(0) == 0
    assert CORE_QUOTA_PER_HOUR == 5000


def test_the_skip_list_holds_everything_that_cannot_be_written_to():
    rows = [row_for(ARCHIVED), row_for(ACTIVE), row_for(DISABLED), row_for(BOTH)]
    assert skip_list(rows) == ["acme/frozen-and-gone", "acme/legacy-billing",
                               "acme/suspended-thing"]
    assert skip_list([]) == []
    assert skip_list(None) == []


def test_the_summary_counts_a_repository_in_both_columns_when_it_is_both():
    counts = summarise([row_for(ARCHIVED), row_for(ACTIVE), row_for(BOTH)])
    assert counts == {"total": 3, "archived": 2, "disabled": 1, "writable": 1,
                      "unknown": 0}


def test_a_row_carries_the_policy_and_the_repair_together():
    row = row_for(ARCHIVED)
    assert row["state"] == "archived"
    assert row["retry_policy"] == "permanent-skip"
    assert row["accepts_writes"] is False
    assert "top of the write loop" in row["repair"]
    assert row["days_since_last_push"] is not None


def test_an_age_is_read_from_the_timestamp_or_left_alone():
    from datetime import datetime, timezone
    now = datetime(2026, 8, 31, tzinfo=timezone.utc)
    assert days_since("2026-08-01T00:00:00Z", now) == 30
    assert days_since("2027-01-01T00:00:00Z", now) == 0
    assert days_since(None) is None
    assert days_since("not a date") is None


def test_the_cost_is_worked_out_before_anything_is_fetched():
    assert read_cost_for_repos(["a", "b", "c"]) == 3
    assert read_cost_for_repos([]) == 0
    assert ORG_PAGE_SIZE == 100
    assert pages_for(212) == 3
    assert pages_for(100) == 1
    assert pages_for(0) == 0


def test_the_link_header_survives_a_comma_inside_a_url():
    header = ('<https://api.github.com/orgs/acme/repos?type=all,public&page=2>; '
              'rel="next", <https://api.github.com/orgs/acme/repos?page=3>; rel="last"')
    links = parse_link(header)
    assert links["next"].endswith("page=2")
    assert links["last"].endswith("page=3")
    assert parse_link("") == {}
    assert parse_link(None) == {}
''',
"test_js_file": "github-archived-repo-guard.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  CORE_QUOTA_PER_HOUR, ORG_PAGE_SIZE, acceptsWrites, classifyFailure, daysSince,
  explain, lifecycle, pagesFor, parseLink, quotaShare, readCostForRepos, repair,
  retryPolicy, rowFor, skipList, summarise, wastedRequests,
} from './github-archived-repo-guard.mjs';

const ARCHIVED = {
  full_name: 'acme/legacy-billing',
  archived: true,
  disabled: false,
  pushed_at: '2025-01-27T09:14:00Z',
};
const ACTIVE = {
  full_name: 'acme/platform-api',
  archived: false,
  disabled: false,
  pushed_at: '2026-08-20T09:14:00Z',
};
const DISABLED = {
  full_name: 'acme/suspended-thing', archived: false, disabled: true,
};
const BOTH = { full_name: 'acme/frozen-and-gone', archived: true, disabled: true };

test('the two booleans make four states', () => {
  assert.equal(lifecycle(ARCHIVED), 'archived');
  assert.equal(lifecycle(ACTIVE), 'active');
  assert.equal(lifecycle(DISABLED), 'disabled');
  assert.equal(lifecycle(BOTH), 'archived-and-disabled');
  assert.equal(lifecycle(null), 'unknown');
  assert.equal(lifecycle('not a repo'), 'unknown');
});

test('an archived repository can never accept a write', () => {
  assert.equal(acceptsWrites('archived'), false);
  assert.equal(acceptsWrites('archived-and-disabled'), false);
  assert.equal(acceptsWrites('disabled'), false);
  assert.equal(acceptsWrites('active'), true);
  assert.equal(acceptsWrites('unknown'), null);
});

test('the output a client needs is a policy not a status code', () => {
  assert.equal(retryPolicy('archived'), 'permanent-skip');
  assert.equal(retryPolicy('disabled'), 'permanent-skip');
  assert.equal(retryPolicy('active'), 'retry');
  assert.equal(retryPolicy('unknown'), 'unknown');
});

test('the explanation says the token is irrelevant', () => {
  assert.match(explain('archived'), /regardless of the token/);
  assert.match(explain('disabled'), /different owner/);
  assert.match(explain('archived-and-disabled'), /would still leave it disabled/);
  assert.match(explain('nonsense'), /unknown/);
});

test('a recorded refusal is attributed without being reproduced', () => {
  const [state, detail] = classifyFailure(403,
    'Repository was archived so is read-only.');
  assert.equal(state, 'archived-refusal');
  assert.match(detail, /not of your credential/);
  assert.match(repair(state), /No token, scope or App permission/);
});

test('a rate limit is the one 403 worth retrying', () => {
  assert.equal(classifyFailure(403, 'API rate limit exceeded for user ID 1')[0],
    'rate-limited');
  assert.match(repair('rate-limited'), /retry-after/);
});

test('a credential refusal is handed back to the credential', () => {
  const [state, detail] = classifyFailure(403, 'Resource not accessible by integration');
  assert.equal(state, 'credential-refusal');
  assert.match(detail, /blames the credential/);
  assert.equal(classifyFailure(404, 'Not Found')[0], 'not-found');
  assert.equal(classifyFailure(403, 'Forbidden')[0], 'forbidden-unattributed');
  assert.equal(classifyFailure('', '')[0], 'no-failure');
});

test('the retry waste is stated in requests and in quota', () => {
  assert.equal(wastedRequests(12, 3), 36);
  assert.equal(wastedRequests(12, 3, 24), 864);
  assert.equal(wastedRequests(0, 3), 0);
  assert.equal(wastedRequests(null, null), 0);
  assert.equal(quotaShare(864), 17);
  assert.equal(quotaShare(0), 0);
  assert.equal(CORE_QUOTA_PER_HOUR, 5000);
});

test('the skip list holds everything that cannot be written to', () => {
  const rows = [rowFor(ARCHIVED), rowFor(ACTIVE), rowFor(DISABLED), rowFor(BOTH)];
  assert.deepEqual(skipList(rows), ['acme/frozen-and-gone', 'acme/legacy-billing',
    'acme/suspended-thing']);
  assert.deepEqual(skipList([]), []);
  assert.deepEqual(skipList(null), []);
});

test('the summary counts a repository in both columns when it is both', () => {
  assert.deepEqual(summarise([rowFor(ARCHIVED), rowFor(ACTIVE), rowFor(BOTH)]), {
    total: 3, archived: 2, disabled: 1, writable: 1, unknown: 0,
  });
});

test('a row carries the policy and the repair together', () => {
  const row = rowFor(ARCHIVED);
  assert.equal(row.state, 'archived');
  assert.equal(row.retry_policy, 'permanent-skip');
  assert.equal(row.accepts_writes, false);
  assert.match(row.repair, /top of the write loop/);
  assert.notEqual(row.days_since_last_push, null);
});

test('an age is read from the timestamp or left alone', () => {
  const now = Date.parse('2026-08-31T00:00:00Z');
  assert.equal(daysSince('2026-08-01T00:00:00Z', now), 30);
  assert.equal(daysSince('2027-01-01T00:00:00Z', now), 0);
  assert.equal(daysSince(null), null);
  assert.equal(daysSince('not a date'), null);
});

test('the cost is worked out before anything is fetched', () => {
  assert.equal(readCostForRepos(['a', 'b', 'c']), 3);
  assert.equal(readCostForRepos([]), 0);
  assert.equal(ORG_PAGE_SIZE, 100);
  assert.equal(pagesFor(212), 3);
  assert.equal(pagesFor(100), 1);
  assert.equal(pagesFor(0), 0);
});

test('the link header survives a comma inside a url', () => {
  const header = '<https://api.github.com/orgs/acme/repos?type=all,public&page=2>; '
    + 'rel="next", <https://api.github.com/orgs/acme/repos?page=3>; rel="last"';
  const links = parseLink(header);
  assert.ok(links.next.endsWith('page=2'));
  assert.ok(links.last.endsWith('page=3'));
  assert.deepEqual(parseLink(''), {});
  assert.deepEqual(parseLink(null), {});
});
''',
"faq": [
 ("Can I widen the token so writes work again?",
  "No, and this is the fact that saves the afternoon. Archiving is a property of the repository rather than of your access to it, so the organisation owner with full admin gets exactly the same 403 as a narrow read-only token. Every other 403 in this section is answered by changing what the caller holds; this one is answered only by unarchiving, which is a decision about whether the repository is still in use rather than a permissions task. If a wider token was the first thing you tried, that instinct was reasonable and it cannot work here."),
 ("Why do reads keep working?",
  "Because that is the entire point of archiving. The repository is preserved exactly as it was and stays readable, searchable and cloneable indefinitely; only mutation is refused. From an integration's point of view this is the worst possible shape of failure, since a resource that answers every question except one looks like an authorisation problem rather than a lifecycle one. If the repository had been deleted you would have got 404s everywhere and looked at the repository first."),
 ("Should my client retry the 403?",
  "Not this one. Retrying is right for a rate limit, a 502 and a timeout, and wrong for a state that will not change until a person changes it. The useful classification is not the status code but whether the request can ever succeed, and <code>archived</code> answers that before the request is sent. Treat it as a permanent skip: filter those repositories out at the top of the loop, and if you want the number that makes the case for doing it, the script multiplies your retry rate by the count and reports it as a share of the hourly quota."),
 ("How do I sweep a whole organisation cheaply?",
  "<code>GET /orgs/{org}/repos?type=all&amp;per_page=100</code> returns <code>archived</code> and <code>disabled</code> on every repository, so an organisation of two hundred costs three requests and gives you the complete skip list. Follow the <code>Link</code> header for the remaining pages. That is cheaper than discovering the same thing one failed write at a time, and it happens before the write loop rather than inside its error handler."),
 ("Does the script write to an archived repository to prove the 403?",
  "It does not, and it will not. Every script in this section is read only, and this is the case where that discipline matters most: the repository was frozen deliberately, so it is the last place to run an experiment. The proof is a boolean the API hands you for free on a read you were probably making anyway. If you have a 403 in your logs, paste the message in and the script attributes it &mdash; archived repository, rate limit, or credential &mdash; from the text and the repository object together."),
],
"related": [
 ("/github/repo-disabled/", "Disabled is a different state with a different owner"),
 ("/github/repo-renamed-301-redirect/", "The repository moved rather than froze"),
 ("/github/retry-after-ignored/", "Retrying the refusals that are worth retrying"),
],
"citations": [CITE_REPOS, CITE_ARCHIVING, CITE_TROUBLESHOOTING, CITE_BEST_PRACTICES],
},
{
"slug": "repo-disabled",
"title": "The repository is disabled and behaves like a ghost",
"description": "A disabled repository still appears in the org listing while its sub-resources stop answering, so every org-wide aggregate quietly counts it as zero.",
"h1": "the repository is disabled and behaves like a ghost",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api repository disabled true",
             "github disabled repository 404 sub resources",
             "github repo disabled billing terms of service api",
             "github org repo listing includes disabled repository",
             "github api partial data disabled repository aggregate"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The weekly platform report says the organisation has one repository with no branch protection, no webhooks, no open pull requests and no contributors. It is not a new repository and it is not empty; it shipped for three years. Every call the report makes against it either 404s or comes back with nothing in it, while the repository itself reads fine and sits in the organisation listing next to everything else. One boolean on the repository object explains all of it, and it is not <code>archived</code>.",
"short_answer": """<p><code>GET /repos/{owner}/{repo}</code> returns <code>disabled</code> next to <code>archived</code>, <code>private</code> and <code>fork</code>. A disabled repository is one GitHub has switched off &mdash; typically for a billing problem, a terms violation, or because the account that owns it is suspended. It keeps appearing in organisation listings and its repository object keeps reading, and most of its sub-resources stop working.</p>
<p>That combination is the danger: the repository is present enough to be counted and absent enough to contribute nothing, so an organisation-wide sweep records it as zero of everything. Report <code>disabled: true</code> as its own finding, separate from <code>archived</code>, and exclude those repositories from aggregates rather than letting them contribute false zeroes. The remedy is an account or billing matter with GitHub, not a change to your integration.</p>""",
"problem": """<p>The failure has no single symptom, which is why nothing gets diagnosed. One endpoint 404s, another returns an empty list, a third returns a perfectly normal object. Each of those on its own is a plausible thing for a real repository to do: a repository with no webhooks returns an empty list, a repository with no protected branches has none, a path can 404 because it does not exist. Read one at a time, none of them is evidence of anything.</p>
<p>So the investigation goes after each symptom separately and each one dead-ends. The 404 gets attributed to permissions, which is the usual and usually correct reading, and a wider token changes nothing. The empty lists get attributed to a genuinely quiet repository. The whole thing has the flavour of a repository that was abandoned rather than one that was switched off, and there is nothing in any individual response that says otherwise.</p>
<p>Meanwhile the aggregate at the bottom of the report is wrong and looks right. If one repository in two hundred contributes zero open pull requests, zero webhooks, zero protected branches and zero contributors, the totals barely move and the averages shift a little. Nobody notices a number that is a fraction of a per cent out. What they notice, months later, is that the coverage percentage on some compliance metric is not what the same query returns when run against a smaller set, and reconciling those two numbers is a very long afternoon.</p>
<p>And it is nobody's bug, which is the last thing that makes it durable. The team that owns the repository did not disable it. The team that owns the report cannot fix it. It is set on GitHub's side and stays set until the underlying account or billing problem is resolved by whoever owns that relationship.</p>""",
"why": """<p><strong>Disabled is not archived, and the difference matters twice.</strong> <a href="/github/repo-archived-writes-403/">An archived repository</a> is fully readable and was frozen deliberately by somebody on your side; its reads all work and only writes are refused. A disabled repository is not fully readable, was not frozen by you, and refuses much more than writes. They are two booleans in the same response and they conflate easily, but the report they belong in and the person who can fix them are different, so the check keeps them apart.</p>
<p><strong>The repository object still reads, and that is what hides it.</strong> Because <code>GET /repos/{owner}/{repo}</code> answers 200 with a normal-looking object, and because the organisation listing still includes it, every mechanism you might use to notice a missing repository keeps saying it is present. A deleted repository disappears from the listing and 404s cleanly, which is loud. This is quiet in exactly the way that survives a code review.</p>
<p><strong>A zero from a disabled repository is not a zero.</strong> This is the practical damage and it is a data-quality problem rather than an availability one. &ldquo;Zero webhooks&rdquo; is a fact about a normal repository and an artefact about a disabled one, and once both have been written into the same column nothing downstream can tell them apart. The right move is to exclude those repositories from the denominator and report their count separately, which is a one-line filter as long as somebody knows to write it.</p>
<p><strong>A 409 is a different explanation and a common false positive.</strong> An empty repository &mdash; created and never pushed to &mdash; answers <code>409</code> with &ldquo;Git Repository is empty&rdquo; on the endpoints that need a commit, and it will otherwise look exactly like the ghost you are hunting. The check treats 409 as its own state so that a brand new repository is never reported as disabled.</p>
<p><strong>No credential changes anything here.</strong> The 404s a disabled repository produces are not permission 404s and cannot be resolved by widening a token, adding an App permission or fixing an installation. That is worth stating plainly because <a href="/github/404-masking-403/">the 404 triage note</a> is the right instinct for almost every other 404 on this API, and it will send you round a loop of credential experiments that all come back the same. Reading the boolean first is one request and settles it.</p>
<p><strong>What a read-only script can prove, and what it cannot.</strong> The boolean is exact and the pattern of sub-resource answers is real evidence. Why the repository was disabled is not exposed anywhere in the API: billing, a terms violation and a suspended owning account all present identically, and the script says so rather than guessing. That question is answered by whoever holds the account relationship with GitHub.</p>""",
"steps": [
 {"h": "Read the repository object and both booleans",
  "body": """<p>One <code>GET /repos/{owner}/{repo}</code>. <code>disabled</code> and <code>archived</code> arrive together and are classified into four states, because a repository can be both and the two have different remedies. This single field is the finding; everything after it is corroboration and reporting.</p>"""},
 {"h": "Probe a few sub-resources at per_page=1",
  "body": """<p>Branches, commits, contributors and languages, one cheap request each. The point is not to discover anything new &mdash; the boolean already told you &mdash; but to produce the evidence in the shape the confusing symptoms arrived in, so the pattern in your logs is explained line by line rather than in the abstract.</p>"""},
 {"h": "Keep the empty repository out of it",
  "body": """<p>A repository created and never pushed to answers <code>409 Git Repository is empty</code> on anything that needs a commit, and looks like a ghost from a distance. The script gives that its own state. Reporting a new repository as disabled is the one false positive this check can produce and it is worth the extra branch to avoid it.</p>"""},
 {"h": "Decide what the row does to your aggregates",
  "body": """<p>For every repository the script prints whether it may be counted, and for the disabled ones it prints the reason it may not: the zeroes it would contribute are artefacts. Feed that into the sweep as an exclusion and report the excluded count next to the total, so the denominator is honest and the missing repositories are visible rather than silently averaged away.</p>"""},
 {"h": "Send the remedy to the right person",
  "body": """<p>Nothing in your integration fixes a disabled repository. The script names the owner of the remedy &mdash; GitHub, through the billing or support relationship for that account &mdash; rather than printing a code change, and it says explicitly that the API does not expose which of the possible reasons applies. In the meantime the exclusion keeps the reporting honest.</p>"""},
],
"verify": """<p>Once the exclusion is in place, the disabled repository stops contributing zeroes and starts being reported as what it is.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_disabled_repo_probe.py \\
    --repo acme/payments-legacy --repo acme/platform-api
# read cost: 5 request(s) per repository against the core hourly quota
# read cost: 10 request(s) in total
# acme/payments-legacy: disabled=True archived=False
# ghost-confirmed: the repository object reads and 3 of 4 sub-resource(s) do
# not, which is what disabled looks like from the outside
#   /branches 404 explained by the disabled state
#   /commits 404 explained by the disabled state
#   /contributors 404 explained by the disabled state
#   /languages 200 answered
#   aggregates: exclude. Every zero this repository contributes is an artefact
#   of the disabled state rather than a measurement.
#   remedy owner: GitHub, through the billing or support relationship for this
#   account. The API does not say which reason applies.
# acme/platform-api: disabled=False archived=False
# healthy: the repository reads and every sub-resource answered
#
# summary: 2 repositories, 1 disabled, 0 archived, 1 countable</code></pre>""",
"code_intro": "One read settles it and four more make the evidence legible, which is the right ratio for a problem whose difficulty was never detection but recognition. The classification is pure and deliberately refuses two shortcuts: a 409 from an empty repository is its own state rather than a ghost, and a sub-resource failure on a repository that is <em>not</em> disabled is handed to the 404 triage rather than explained away. The aggregate functions are the part worth stealing &mdash; they decide whether a row may enter a denominator, which is the actual damage this state does.",
"py_file": "github_disabled_repo_probe.py",
"py": '''"""Recognise a disabled repository and keep its zeroes out of your aggregates.

Read only. One GET for the repository object and one cheap GET per probed
sub-resource, all at per_page=1. Nothing is written, and no write is attempted
to characterise the state: disabled is a boolean on the repository object and
the sub-resource probes are reads that would have happened anyway in the sweep
this note is about.

The point of the note: a disabled repository -- switched off by GitHub for a
billing problem, a terms violation or a suspended owning account -- keeps
appearing in organisation listings and keeps serving its own repository object
while most of its sub-resources stop answering. It is therefore present enough
to be counted and absent enough to contribute nothing, so every org-wide
aggregate silently records it as zero of everything.

What this can and cannot see: the boolean is exact and the pattern of answers
is real evidence. Why the repository was disabled is not exposed anywhere in
the API; billing, a terms violation and a suspended account are
indistinguishable from here, so the script names the owner of the remedy
rather than the reason.

Environment:

    GITHUB_TOKEN    a token with read access to the repositories
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_disabled_repo_probe")

API = "https://api.github.com"
UA = "github-disabled-repo-probe/1.0"

# Cheap reads that a repository normally answers. per_page=1 everywhere: the
# question is whether the endpoint answers at all, not what is in it.
DEFAULT_PROBES = ("/branches?per_page=1", "/commits?per_page=1",
                  "/contributors?per_page=1", "/languages")

# An empty repository answers this on anything that needs a commit. It is the
# one false positive this check can produce, so it gets its own state.
EMPTY_REPOSITORY = 409


def platform_state(repo):
    """Which platform state this repository is in. Pure.

    disabled and archived are separate booleans on the same object with
    different owners and different remedies, so they make four states rather
    than one flag with two names.
    """
    if not isinstance(repo, dict):
        return "unknown"
    disabled = bool(repo.get("disabled"))
    archived = bool(repo.get("archived"))
    if disabled and archived:
        return "disabled-and-archived"
    if disabled:
        return "disabled"
    if archived:
        return "archived"
    return "active"


def is_disabled(state):
    """Whether the disabled boolean is set, in either combination. Pure."""
    return state in ("disabled", "disabled-and-archived")


def explains_subresource(state, status):
    """Whether the repository state accounts for this answer. Pure.

    Returns (explained, why). A failure on a repository that is not disabled
    is deliberately not explained away: that is a credential triage and it
    belongs to another note.
    """
    try:
        code = int(status)
    except (TypeError, ValueError):
        return (False, "no readable status for this probe.")
    if 200 <= code < 300:
        return (True, "answered")
    if code == EMPTY_REPOSITORY:
        return (False, "409, which is an empty repository rather than a "
                       "disabled one")
    if is_disabled(state) and code in (403, 404, 451):
        return (True, "explained by the disabled state")
    if state == "archived" and code in (403, 404):
        return (False, "not explained by archiving, which leaves reads working")
    return (False, "not explained by the repository state")


def probe_verdict(state, probes):
    """Classify a repository from its state and its probe answers. Pure.

    probes: [{"path": str, "status": int}, ...]
    """
    rows = [p for p in (probes or []) if isinstance(p, dict)]
    failing = [p for p in rows
               if not explains_subresource(state, p.get("status"))[0]
               or not (200 <= int(p.get("status") or 0) < 300)]
    empty = [p for p in rows if str(p.get("status")) == str(EMPTY_REPOSITORY)]

    if state == "unknown":
        return ("repository-unreadable",
                "the repository object itself did not come back, so this is a "
                "credential or name problem rather than a platform state.")
    if is_disabled(state):
        if failing:
            return ("ghost-confirmed",
                    "the repository object reads and %d of %d sub-resource(s) "
                    "do not, which is what disabled looks like from the outside."
                    % (len(failing), len(rows)))
        return ("disabled-but-answering",
                "disabled is set and every probe answered anyway. Trust the "
                "boolean: the repository is switched off and must still be "
                "excluded from aggregates.")
    if empty:
        return ("empty-repository",
                "%d probe(s) answered 409 Git Repository is empty. This "
                "repository has never been pushed to and is not disabled."
                % len(empty))
    if state == "archived":
        return ("archived-not-disabled",
                "archived rather than disabled. Reads work and only writes are "
                "refused, which is a different note.")
    if failing:
        return ("not-explained-by-state",
                "%d sub-resource(s) failed on a repository that is neither "
                "disabled nor archived, so the repository state does not "
                "explain it." % len(failing))
    return ("healthy", "the repository reads and every sub-resource answered.")


def aggregate_safety(state):
    """Whether this repository may enter an org-wide aggregate. Pure."""
    if is_disabled(state):
        return ("exclude",
                "every zero this repository contributes is an artefact of the "
                "disabled state rather than a measurement.")
    if state == "unknown":
        return ("exclude",
                "the repository could not be read, so it has no values to "
                "contribute and its absence should be visible in the report.")
    if state == "archived":
        return ("include",
                "an archived repository is fully readable, so its values are "
                "real. Only its writes are refused.")
    return ("include", "nothing here disqualifies this repository from a count.")


def is_real_zero(state, value):
    """Whether a zero measured on this repository means anything. Pure.

    Returns True for a genuine zero, False for an artefact, None where the
    value is not a zero at all.
    """
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number != 0:
        return None
    if is_disabled(state) or state == "unknown":
        return False
    return True


def aggregate_impact(rows):
    """What a sweep should report alongside its total. Pure."""
    counted, excluded, false_zeroes = 0, 0, 0
    for row in rows or []:
        state = (row or {}).get("state")
        decision, _ = aggregate_safety(state)
        if decision == "exclude":
            excluded += 1
            if is_disabled(state):
                false_zeroes += 1
        else:
            counted += 1
    return {"counted": counted, "excluded": excluded,
            "false_zeroes_avoided": false_zeroes}


def remedy_owner(state):
    """Who can actually change this state. Pure."""
    if is_disabled(state):
        return ("GitHub, through the billing or support relationship for this "
                "account. The API does not say which reason applies.")
    if state == "archived":
        return ("whoever owns the repository, by unarchiving it. That is a "
                "decision about whether it is still in use.")
    if state == "unknown":
        return "nobody yet: the repository could not be read."
    return "no remedy needed."


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state in ("ghost-confirmed", "disabled-but-answering"):
        return ("exclude this repository from org-wide aggregates and report it "
                "separately. Nothing in your integration can re-enable it; that "
                "is a billing or account matter with GitHub.")
    if state == "empty-repository":
        return ("nothing. A repository that has never been pushed to answers "
                "409 on anything needing a commit, and that is not this "
                "problem.")
    if state == "archived-not-disabled":
        return ("see /github/repo-archived-writes-403/ -- reads work there and "
                "only writes are refused.")
    if state == "not-explained-by-state":
        return ("triage the failures as a credential problem: the repository "
                "state does not account for them.")
    if state == "repository-unreadable":
        return ("check the name, the visibility and the installation before "
                "anything else. A 404 on the repository means several things.")
    return "nothing on the platform state."


def read_cost(repos, probes=DEFAULT_PROBES):
    """Requests this run will spend against the core quota. Pure."""
    per_repo = 1 + len(probes or ())
    return per_repo * len(repos or [])


def get_repo(session, full_name):
    """One GET of a repository object. Returns (status, dict-or-None)."""
    r = session.get(API + "/repos/" + full_name, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset "
                         "time and does not itself consume quota")
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, (body if isinstance(body, dict) else None)


def probe(session, full_name, path):
    """One cheap GET of a sub-resource. Returns its status only."""
    r = session.get(API + "/repos/" + full_name + path, timeout=30)
    return r.status_code


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", required=True,
                    help="owner/name to check. Repeatable.")
    ap.add_argument("--probe", action="append", default=[],
                    help="sub-resource path to probe, defaulting to branches, "
                         "commits, contributors and languages")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    probes = tuple(args.probe) or DEFAULT_PROBES
    log.info("read cost: %d request(s) per repository against the core hourly "
             "quota", 1 + len(probes))
    log.info("read cost: %d request(s) in total", read_cost(args.repo, probes))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    findings = []
    for name in args.repo:
        status, repo = get_repo(session, name)
        state = platform_state(repo) if status == 200 else "unknown"
        results = []
        if status == 200:
            for path in probes:
                code = probe(session, name, path)
                explained, why = explains_subresource(state, code)
                results.append({"path": path.split("?")[0], "status": code,
                                "explained": explained, "why": why})

        verdict, detail = probe_verdict(state, results)
        decision, reason = aggregate_safety(state)

        log.info("%s: disabled=%s archived=%s", name,
                 bool((repo or {}).get("disabled")),
                 bool((repo or {}).get("archived")))
        log.info("%s: %s", verdict, detail)
        for row in results:
            log.info("  %s %s %s", row["path"], row["status"], row["why"])
        log.info("  aggregates: %s. %s", decision, reason)
        log.info("  remedy owner: %s", remedy_owner(state))
        log.info("  repair: %s", repair(verdict))

        findings.append({
            "repository": name,
            "repository_status": status,
            "platform_state": state,
            "probes": results,
            "state": verdict,
            "detail": detail,
            "aggregate_decision": decision,
            "aggregate_reason": reason,
            "remedy_owner": remedy_owner(state),
            "repair": repair(verdict),
        })

    impact = aggregate_impact([{"state": f["platform_state"]} for f in findings])
    disabled = sum(1 for f in findings if is_disabled(f["platform_state"]))
    archived = sum(1 for f in findings
                   if f["platform_state"] in ("archived", "disabled-and-archived"))
    log.info("summary: %d repositories, %d disabled, %d archived, %d countable",
             len(findings), disabled, archived, impact["counted"])

    print(json.dumps({
        "requests_spent": read_cost(args.repo, probes),
        "aggregate_impact": impact,
        "findings": findings,
    }, indent=2, default=str))
    return 1 if disabled else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-disabled-repo-probe.mjs",
"js": '''/**
 * Recognise a disabled repository and keep its zeroes out of your aggregates.
 *
 * Read only. One GET for the repository object and one cheap GET per probed
 * sub-resource, all at per_page=1. Nothing is written and no write is attempted
 * to characterise the state.
 *
 * A disabled repository keeps appearing in organisation listings and keeps
 * serving its own repository object while most of its sub-resources stop
 * answering, so an org-wide sweep records it as zero of everything.
 *
 * Environment:
 *   GITHUB_TOKEN      a token with read access to the repositories
 *   GITHUB_REPOS      comma-separated owner/name values
 */
const API = 'https://api.github.com';
const UA = 'github-disabled-repo-probe/1.0';

/** Cheap reads a repository normally answers. */
export const DEFAULT_PROBES = ['/branches?per_page=1', '/commits?per_page=1',
  '/contributors?per_page=1', '/languages'];

/** An empty repository answers this on anything that needs a commit. */
export const EMPTY_REPOSITORY = 409;

/** Which platform state this repository is in. Pure. */
export function platformState(repo) {
  if (!repo || typeof repo !== 'object') return 'unknown';
  const disabled = Boolean(repo.disabled);
  const archived = Boolean(repo.archived);
  if (disabled && archived) return 'disabled-and-archived';
  if (disabled) return 'disabled';
  if (archived) return 'archived';
  return 'active';
}

/** Whether the disabled boolean is set, in either combination. Pure. */
export function isDisabled(state) {
  return state === 'disabled' || state === 'disabled-and-archived';
}

/** Whether the repository state accounts for this answer. Pure. */
export function explainsSubresource(state, status) {
  const code = Number(status);
  if (!Number.isFinite(code)) return [false, 'no readable status for this probe.'];
  if (code >= 200 && code < 300) return [true, 'answered'];
  if (code === EMPTY_REPOSITORY) {
    return [false, '409, which is an empty repository rather than a disabled one'];
  }
  if (isDisabled(state) && [403, 404, 451].includes(code)) {
    return [true, 'explained by the disabled state'];
  }
  if (state === 'archived' && [403, 404].includes(code)) {
    return [false, 'not explained by archiving, which leaves reads working'];
  }
  return [false, 'not explained by the repository state'];
}

/** Classify a repository from its state and its probe answers. Pure. */
export function probeVerdict(state, probes) {
  const rows = (probes || []).filter((p) => p && typeof p === 'object');
  const failing = rows.filter((p) => {
    const code = Number(p.status);
    return !explainsSubresource(state, p.status)[0]
      || !(Number.isFinite(code) && code >= 200 && code < 300);
  });
  const empty = rows.filter((p) => Number(p.status) === EMPTY_REPOSITORY);

  if (state === 'unknown') {
    return ['repository-unreadable', 'the repository object itself did not come '
      + 'back, so this is a credential or name problem rather than a platform state.'];
  }
  if (isDisabled(state)) {
    if (failing.length) {
      return ['ghost-confirmed', `the repository object reads and ${failing.length} `
        + `of ${rows.length} sub-resource(s) do not, which is what disabled looks `
        + 'like from the outside.'];
    }
    return ['disabled-but-answering', 'disabled is set and every probe answered '
      + 'anyway. Trust the boolean: the repository is switched off and must still '
      + 'be excluded from aggregates.'];
  }
  if (empty.length) {
    return ['empty-repository', `${empty.length} probe(s) answered 409 Git `
      + 'Repository is empty. This repository has never been pushed to and is '
      + 'not disabled.'];
  }
  if (state === 'archived') {
    return ['archived-not-disabled', 'archived rather than disabled. Reads work '
      + 'and only writes are refused, which is a different note.'];
  }
  if (failing.length) {
    return ['not-explained-by-state', `${failing.length} sub-resource(s) failed `
      + 'on a repository that is neither disabled nor archived, so the '
      + 'repository state does not explain it.'];
  }
  return ['healthy', 'the repository reads and every sub-resource answered.'];
}

/** Whether this repository may enter an org-wide aggregate. Pure. */
export function aggregateSafety(state) {
  if (isDisabled(state)) {
    return ['exclude', 'every zero this repository contributes is an artefact of '
      + 'the disabled state rather than a measurement.'];
  }
  if (state === 'unknown') {
    return ['exclude', 'the repository could not be read, so it has no values to '
      + 'contribute and its absence should be visible in the report.'];
  }
  if (state === 'archived') {
    return ['include', 'an archived repository is fully readable, so its values '
      + 'are real. Only its writes are refused.'];
  }
  return ['include', 'nothing here disqualifies this repository from a count.'];
}

/** Whether a zero measured on this repository means anything. Pure. */
export function isRealZero(state, value) {
  const number = Number(value);
  if (!Number.isFinite(number) || value === null || value === '') return null;
  if (number !== 0) return null;
  if (isDisabled(state) || state === 'unknown') return false;
  return true;
}

/** What a sweep should report alongside its total. Pure. */
export function aggregateImpact(rows) {
  let counted = 0;
  let excluded = 0;
  let falseZeroes = 0;
  for (const row of rows || []) {
    const state = (row || {}).state;
    const [decision] = aggregateSafety(state);
    if (decision === 'exclude') {
      excluded += 1;
      if (isDisabled(state)) falseZeroes += 1;
    } else {
      counted += 1;
    }
  }
  return { counted, excluded, false_zeroes_avoided: falseZeroes };
}

/** Who can actually change this state. Pure. */
export function remedyOwner(state) {
  if (isDisabled(state)) {
    return 'GitHub, through the billing or support relationship for this '
      + 'account. The API does not say which reason applies.';
  }
  if (state === 'archived') {
    return 'whoever owns the repository, by unarchiving it. That is a decision '
      + 'about whether it is still in use.';
  }
  if (state === 'unknown') return 'nobody yet: the repository could not be read.';
  return 'no remedy needed.';
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (['ghost-confirmed', 'disabled-but-answering'].includes(state)) {
    return 'exclude this repository from org-wide aggregates and report it '
      + 'separately. Nothing in your integration can re-enable it; that is a '
      + 'billing or account matter with GitHub.';
  }
  if (state === 'empty-repository') {
    return 'nothing. A repository that has never been pushed to answers 409 on '
      + 'anything needing a commit, and that is not this problem.';
  }
  if (state === 'archived-not-disabled') {
    return 'see /github/repo-archived-writes-403/ -- reads work there and only '
      + 'writes are refused.';
  }
  if (state === 'not-explained-by-state') {
    return 'triage the failures as a credential problem: the repository state '
      + 'does not account for them.';
  }
  if (state === 'repository-unreadable') {
    return 'check the name, the visibility and the installation before anything '
      + 'else. A 404 on the repository means several things.';
  }
  return 'nothing on the platform state.';
}

/** Requests this run will spend against the core quota. Pure. */
export function readCost(repos, probes = DEFAULT_PROBES) {
  const perRepo = 1 + (probes || []).length;
  return perRepo * ((repos || []).length);
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
  const names = (process.env.GITHUB_REPOS || '').split(',')
    .map((n) => n.trim()).filter(Boolean);
  if (!token || !names.length) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPOS');
    process.exitCode = 2;
    return;
  }

  console.log(`read cost: ${1 + DEFAULT_PROBES.length} request(s) per repository `
    + 'against the core hourly quota');
  console.log(`read cost: ${readCost(names)} request(s) in total`);

  const findings = [];
  for (const name of names) {
    const res = await fetch(`${API}/repos/${name}`, { headers: headers(token) });
    let repo = null;
    try { repo = await res.json(); } catch { repo = null; }
    const state = res.status === 200 ? platformState(repo) : 'unknown';

    const probes = [];
    if (res.status === 200) {
      for (const path of DEFAULT_PROBES) {
        const p = await fetch(`${API}/repos/${name}${path}`, { headers: headers(token) });
        const [explained, why] = explainsSubresource(state, p.status);
        probes.push({ path: path.split('?')[0], status: p.status, explained, why });
      }
    }

    const [verdict, detail] = probeVerdict(state, probes);
    const [decision, reason] = aggregateSafety(state);

    console.log(`${name}: disabled=${Boolean((repo || {}).disabled)} `
      + `archived=${Boolean((repo || {}).archived)}`);
    console.log(`${verdict}: ${detail}`);
    for (const row of probes) console.log(`  ${row.path} ${row.status} ${row.why}`);
    console.log(`  aggregates: ${decision}. ${reason}`);
    console.log(`  remedy owner: ${remedyOwner(state)}`);
    console.log(`  repair: ${repair(verdict)}`);

    findings.push({
      repository: name,
      repository_status: res.status,
      platform_state: state,
      probes,
      state: verdict,
      detail,
      aggregate_decision: decision,
      aggregate_reason: reason,
      remedy_owner: remedyOwner(state),
      repair: repair(verdict),
    });
  }

  const impact = aggregateImpact(findings.map((f) => ({ state: f.platform_state })));
  const disabled = findings.filter((f) => isDisabled(f.platform_state)).length;
  console.log(`summary: ${findings.length} repositories, ${disabled} disabled, `
    + `${impact.counted} countable`);

  console.log(JSON.stringify({
    requests_spent: readCost(names),
    aggregate_impact: impact,
    findings,
  }, null, 2));
  process.exitCode = disabled ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two of these tests exist to stop the check being wrong in the direction that would matter. A brand new repository answering 409 must never be reported as a ghost, and a sub-resource failure on a repository that is neither disabled nor archived must be handed to the credential triage rather than explained away by a state that is not set. The rest pin the four platform states, the aggregate decision that is the actual output of the note, and the small function that decides whether a zero measured on a repository means anything at all.",
"test_py_file": "test_github_disabled_repo_probe.py",
"test_py": '''from github_disabled_repo_probe import (
    DEFAULT_PROBES, EMPTY_REPOSITORY, aggregate_impact, aggregate_safety,
    explains_subresource, is_disabled, is_real_zero, platform_state,
    probe_verdict, read_cost, remedy_owner, repair,
)

DISABLED = {"full_name": "acme/payments-legacy", "disabled": True, "archived": False}
ARCHIVED = {"full_name": "acme/legacy-billing", "disabled": False, "archived": True}
BOTH = {"full_name": "acme/gone", "disabled": True, "archived": True}
ACTIVE = {"full_name": "acme/platform-api", "disabled": False, "archived": False}

GHOST_PROBES = [{"path": "/branches", "status": 404},
                {"path": "/commits", "status": 404},
                {"path": "/contributors", "status": 404},
                {"path": "/languages", "status": 200}]
ALL_FINE = [{"path": "/branches", "status": 200},
            {"path": "/commits", "status": 200}]
NEW_REPO = [{"path": "/branches", "status": 200},
            {"path": "/commits", "status": EMPTY_REPOSITORY}]


def test_the_two_booleans_make_four_platform_states():
    assert platform_state(DISABLED) == "disabled"
    assert platform_state(ARCHIVED) == "archived"
    assert platform_state(BOTH) == "disabled-and-archived"
    assert platform_state(ACTIVE) == "active"
    assert platform_state(None) == "unknown"
    assert is_disabled("disabled-and-archived") is True
    assert is_disabled("archived") is False


def test_a_failure_is_only_explained_when_the_state_explains_it():
    assert explains_subresource("disabled", 404)[0] is True
    assert explains_subresource("disabled", 403)[0] is True
    assert explains_subresource("disabled", 200)[0] is True
    explained, why = explains_subresource("active", 404)
    assert explained is False
    assert "not explained by the repository state" in why


def test_archiving_does_not_explain_a_failed_read():
    explained, why = explains_subresource("archived", 404)
    assert explained is False
    assert "leaves reads working" in why


def test_an_empty_repository_is_never_reported_as_a_ghost():
    state, detail = probe_verdict("active", NEW_REPO)
    assert state == "empty-repository"
    assert "never been pushed to" in detail
    assert explains_subresource("disabled", EMPTY_REPOSITORY)[0] is False
    assert repair(state).startswith("nothing.")


def test_the_ghost_is_the_repository_object_reading_and_nothing_else_doing():
    state, detail = probe_verdict("disabled", GHOST_PROBES)
    assert state == "ghost-confirmed"
    assert "3 of 4 sub-resource(s)" in detail
    assert "billing or account matter" in repair(state)


def test_a_disabled_repository_that_answers_is_still_disabled():
    state, detail = probe_verdict("disabled", ALL_FINE)
    assert state == "disabled-but-answering"
    assert "Trust the boolean" in detail


def test_failures_without_a_state_to_explain_them_go_to_the_other_note():
    state, detail = probe_verdict("active", [{"path": "/branches", "status": 404}])
    assert state == "not-explained-by-state"
    assert "neither disabled nor archived" in detail
    assert "credential problem" in repair(state)


def test_archived_and_unreadable_are_handed_on_rather_than_absorbed():
    assert probe_verdict("archived", ALL_FINE)[0] == "archived-not-disabled"
    assert "repo-archived-writes-403" in repair("archived-not-disabled")
    assert probe_verdict("unknown", [])[0] == "repository-unreadable"
    assert probe_verdict("active", ALL_FINE)[0] == "healthy"


def test_the_aggregate_decision_is_the_output_that_matters():
    decision, reason = aggregate_safety("disabled")
    assert decision == "exclude"
    assert "artefact" in reason
    assert aggregate_safety("archived")[0] == "include"
    assert aggregate_safety("active")[0] == "include"
    assert aggregate_safety("unknown")[0] == "exclude"


def test_a_zero_from_a_disabled_repository_is_not_a_zero():
    assert is_real_zero("disabled", 0) is False
    assert is_real_zero("unknown", 0) is False
    assert is_real_zero("active", 0) is True
    assert is_real_zero("archived", 0) is True
    assert is_real_zero("disabled", 4) is None
    assert is_real_zero("active", None) is None


def test_the_sweep_reports_what_it_left_out():
    impact = aggregate_impact([{"state": "disabled"}, {"state": "active"},
                               {"state": "archived"}, {"state": "unknown"}])
    assert impact == {"counted": 2, "excluded": 2, "false_zeroes_avoided": 1}
    assert aggregate_impact([]) == {"counted": 0, "excluded": 0,
                                    "false_zeroes_avoided": 0}


def test_the_remedy_is_addressed_to_whoever_can_apply_it():
    assert "GitHub" in remedy_owner("disabled")
    assert "does not say which reason" in remedy_owner("disabled")
    assert "unarchiving" in remedy_owner("archived")
    assert remedy_owner("active") == "no remedy needed."


def test_the_cost_is_worked_out_before_anything_is_fetched():
    assert len(DEFAULT_PROBES) == 4
    assert read_cost(["a", "b"]) == 10
    assert read_cost(["a"], ("/languages",)) == 2
    assert read_cost([]) == 0
    assert read_cost(None) == 0
''',
"test_js_file": "github-disabled-repo-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DEFAULT_PROBES, EMPTY_REPOSITORY, aggregateImpact, aggregateSafety,
  explainsSubresource, isDisabled, isRealZero, platformState, probeVerdict,
  readCost, remedyOwner, repair,
} from './github-disabled-repo-probe.mjs';

const DISABLED = { full_name: 'acme/payments-legacy', disabled: true, archived: false };
const ARCHIVED = { full_name: 'acme/legacy-billing', disabled: false, archived: true };
const BOTH = { full_name: 'acme/gone', disabled: true, archived: true };
const ACTIVE = { full_name: 'acme/platform-api', disabled: false, archived: false };

const GHOST_PROBES = [
  { path: '/branches', status: 404 },
  { path: '/commits', status: 404 },
  { path: '/contributors', status: 404 },
  { path: '/languages', status: 200 },
];
const ALL_FINE = [
  { path: '/branches', status: 200 }, { path: '/commits', status: 200 },
];
const NEW_REPO = [
  { path: '/branches', status: 200 }, { path: '/commits', status: EMPTY_REPOSITORY },
];

test('the two booleans make four platform states', () => {
  assert.equal(platformState(DISABLED), 'disabled');
  assert.equal(platformState(ARCHIVED), 'archived');
  assert.equal(platformState(BOTH), 'disabled-and-archived');
  assert.equal(platformState(ACTIVE), 'active');
  assert.equal(platformState(null), 'unknown');
  assert.equal(isDisabled('disabled-and-archived'), true);
  assert.equal(isDisabled('archived'), false);
});

test('a failure is only explained when the state explains it', () => {
  assert.equal(explainsSubresource('disabled', 404)[0], true);
  assert.equal(explainsSubresource('disabled', 403)[0], true);
  assert.equal(explainsSubresource('disabled', 200)[0], true);
  const [explained, why] = explainsSubresource('active', 404);
  assert.equal(explained, false);
  assert.match(why, /not explained by the repository state/);
});

test('archiving does not explain a failed read', () => {
  const [explained, why] = explainsSubresource('archived', 404);
  assert.equal(explained, false);
  assert.match(why, /leaves reads working/);
});

test('an empty repository is never reported as a ghost', () => {
  const [state, detail] = probeVerdict('active', NEW_REPO);
  assert.equal(state, 'empty-repository');
  assert.match(detail, /never been pushed to/);
  assert.equal(explainsSubresource('disabled', EMPTY_REPOSITORY)[0], false);
  assert.ok(repair(state).startsWith('nothing.'));
});

test('the ghost is the repository object reading and nothing else doing', () => {
  const [state, detail] = probeVerdict('disabled', GHOST_PROBES);
  assert.equal(state, 'ghost-confirmed');
  assert.match(detail, /3 of 4 sub-resource\\(s\\)/);
  assert.match(repair(state), /billing or account matter/);
});

test('a disabled repository that answers is still disabled', () => {
  const [state, detail] = probeVerdict('disabled', ALL_FINE);
  assert.equal(state, 'disabled-but-answering');
  assert.match(detail, /Trust the boolean/);
});

test('failures without a state to explain them go to the other note', () => {
  const [state, detail] = probeVerdict('active', [{ path: '/branches', status: 404 }]);
  assert.equal(state, 'not-explained-by-state');
  assert.match(detail, /neither disabled nor archived/);
  assert.match(repair(state), /credential problem/);
});

test('archived and unreadable are handed on rather than absorbed', () => {
  assert.equal(probeVerdict('archived', ALL_FINE)[0], 'archived-not-disabled');
  assert.match(repair('archived-not-disabled'), /repo-archived-writes-403/);
  assert.equal(probeVerdict('unknown', [])[0], 'repository-unreadable');
  assert.equal(probeVerdict('active', ALL_FINE)[0], 'healthy');
});

test('the aggregate decision is the output that matters', () => {
  const [decision, reason] = aggregateSafety('disabled');
  assert.equal(decision, 'exclude');
  assert.match(reason, /artefact/);
  assert.equal(aggregateSafety('archived')[0], 'include');
  assert.equal(aggregateSafety('active')[0], 'include');
  assert.equal(aggregateSafety('unknown')[0], 'exclude');
});

test('a zero from a disabled repository is not a zero', () => {
  assert.equal(isRealZero('disabled', 0), false);
  assert.equal(isRealZero('unknown', 0), false);
  assert.equal(isRealZero('active', 0), true);
  assert.equal(isRealZero('archived', 0), true);
  assert.equal(isRealZero('disabled', 4), null);
  assert.equal(isRealZero('active', null), null);
});

test('the sweep reports what it left out', () => {
  const impact = aggregateImpact([{ state: 'disabled' }, { state: 'active' },
    { state: 'archived' }, { state: 'unknown' }]);
  assert.deepEqual(impact, { counted: 2, excluded: 2, false_zeroes_avoided: 1 });
  assert.deepEqual(aggregateImpact([]),
    { counted: 0, excluded: 0, false_zeroes_avoided: 0 });
});

test('the remedy is addressed to whoever can apply it', () => {
  assert.match(remedyOwner('disabled'), /GitHub/);
  assert.match(remedyOwner('disabled'), /does not say which reason/);
  assert.match(remedyOwner('archived'), /unarchiving/);
  assert.equal(remedyOwner('active'), 'no remedy needed.');
});

test('the cost is worked out before anything is fetched', () => {
  assert.equal(DEFAULT_PROBES.length, 4);
  assert.equal(readCost(['a', 'b']), 10);
  assert.equal(readCost(['a'], ['/languages']), 2);
  assert.equal(readCost([]), 0);
  assert.equal(readCost(null), 0);
});
''',
"faq": [
 ("How is disabled different from archived?",
  "Archiving is a decision somebody on your side made and it leaves the repository completely readable; only writes are refused. Disabling is done by GitHub, usually over billing, a terms violation or a suspended owning account, and it takes most of the repository's sub-resources with it. The two booleans arrive in the same response and are easy to conflate, but they need different columns in a report because the person who can undo them is different: one is a team decision, the other is an account relationship with GitHub."),
 ("Why does the repository object still read?",
  "Because the repository record itself is intact; what has been switched off is the machinery around it. That is exactly why this is hard to spot, since every mechanism you would normally use to detect a missing repository keeps reporting it as present: it stays in the organisation listing, its metadata is current, and a plain read of it returns 200. A deleted repository disappears and 404s cleanly, which is loud and gets noticed the same day."),
 ("What does the API say about why it was disabled?",
  "Nothing. There is no field naming the reason and no endpoint that exposes it, so billing, a terms violation and a suspended owning account are indistinguishable from a script's point of view. This is a genuine blind spot rather than a matter of permissions, and the script says so rather than guessing: it names the owner of the remedy, which is whoever holds the billing or support relationship for that account, and leaves the reason to them."),
 ("Could this just be an empty repository?",
  "It could, and the check separates them deliberately. A repository created and never pushed to answers <code>409 Git Repository is empty</code> on anything that needs a commit, which from a distance looks like the same ghost. The script gives 409 its own state and never reports a new repository as disabled. If your own sweep does not make that distinction, it will eventually raise an alarm about a repository somebody created ten minutes earlier."),
 ("What should the sweep do with a disabled repository?",
  "Exclude it from the aggregates and report the excluded count next to the total. The damage here is not a failed request, it is a zero that looks like a measurement: zero webhooks, zero protected branches, zero open pull requests, all of which are artefacts of the repository being switched off. Leaving those in the denominator quietly moves every coverage percentage in the report, and the discrepancy usually surfaces months later when two people run the same query over different sets."),
],
"related": [
 ("/github/repo-archived-writes-403/", "Archived is readable and refuses only writes"),
 ("/github/404-masking-403/", "When a 404 really is about the credential"),
 ("/github/saml-partial-results/", "A listing that omits rows without saying so"),
],
"citations": [CITE_REPOS, CITE_TROUBLESHOOTING, CITE_ABOUT_REPOS, CITE_PAGINATION],
},
{
"slug": "deploy-key-read-only-assumed-write",
"title": "The deploy key is read-only and the push needs write",
"description": "Clones succeed and the push fails from Git rather than the API. read_only on the deploy key object is the finding, and no scope change moves it.",
"h1": "the deploy key is read-only and the push needs write",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github deploy key read only push denied",
             "the key you are authenticating with has been marked as read only",
             "github deploy key read_only field api",
             "write access to repository not granted deploy key",
             "github deploy key vs github app installation token"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The pipeline has cloned this repository twice a day for eighteen months. Somebody adds a step that pushes a version bump back, and it fails with <code>ERROR: The key you are authenticating with has been marked as read only.</code> &mdash; from Git, over SSH, with no HTTP status and nothing in the API logs. So the investigation starts in the wrong tool, goes through the known-hosts file and the agent and the private key in the secret store, and none of that is where the answer is. The answer is a boolean on an object the API will hand you in one request.",
"short_answer": """<p>A deploy key carries a <code>read_only</code> flag chosen when the key was created, and read-only is both the default and the right choice for almost every use. A read-only key clones and fetches perfectly and refuses to push, and the refusal comes from Git rather than from the API, which is why the diagnosis usually starts somewhere unhelpful.</p>
<p><code>GET /repos/{owner}/{repo}/keys</code> lists every deploy key on the repository with its <code>id</code>, <code>title</code>, <code>read_only</code>, <code>created_at</code>, <code>verified</code> and <code>added_by</code>. A repository whose automation pushes and whose every key is <code>read_only: true</code> is the finding. No scope, App permission or token change alters it &mdash; the capability is declared on the key object itself. Replace the key with one created with write access, or better, move that job to a GitHub App installation token with <code>contents: write</code>, which is scoped, expiring and auditable.</p>""",
"problem": """<p>The refusal arrives outside the API, and that is most of the difficulty. There is no status code, no <code>x-accepted</code> header, no JSON body and no entry in any HTTP log; there is a line on stderr from a Git subprocess, usually buried inside a build log, often truncated. Everything this section normally works with is absent, so the usual triage does not start.</p>
<p>What starts instead is an SSH investigation, because that is what the error looks like. Someone checks whether the key is loaded in the agent, whether the private key in the secret store matches the public key on GitHub, whether the host key changed, whether the runner has an IPv6 problem. All of that is careful work on a connection that is working perfectly: the key authenticated, GitHub identified it, and then declined the operation. Authentication succeeded and authorisation did not, which is exactly the distinction the error line is making and exactly the one that gets missed at four in the afternoon.</p>
<p>The second wrong turn is the token. On a repository where a personal access token or an App installation is also in play, the natural next thought is scopes, and there is always something to adjust there. Widening the token changes nothing at all, because the push is not authenticating with the token; SSH and HTTPS are different credentials to the same repository and the deploy key is the one being used. Time spent on the token is time spent on a credential that is not involved.</p>
<p>Underneath all of it is a perfectly reasonable history. The key was added years ago for a CI job that only ever read, and read-only was the correct and careful choice at the time. Nothing was misconfigured. The requirement changed and the credential did not, and nothing in the repository records that the assumption was ever made.</p>""",
"why": """<p><strong>The capability is a field on the key, not a property of your account.</strong> This is what keeps it out of the rest of the section's permission notes. <a href="/github/missing-oauth-scope/">A missing OAuth scope</a>, <a href="/github/app-permission-missing/">an App permission the endpoint wanted</a> and a narrowed installation token are all statements about a credential's grants and are answered by re-issuing the credential with more. A deploy key's <code>read_only</code> is a fixed attribute of that specific key object, set when it was created and not editable afterwards. There is no widening; there is only replacement.</p>
<p><strong>Read-only is the default, and it should be.</strong> GitHub's own guidance is to prefer read-only deploy keys, and most uses of one are a build fetching source. That means the shape of this failure is not a mistake anybody made but a requirement that changed underneath a correct decision. It also means a repository full of read-only keys is a healthy repository, and the finding only exists in relation to what the automation now needs to do.</p>
<p><strong>SSH and HTTPS are different credentials to the same repository.</strong> A job can clone over SSH with a deploy key and call the API over HTTPS with a token in the same script, and the two have nothing to do with each other. When a push fails and an API call succeeds, that is not a contradiction; it is two credentials with different capabilities. Working out which one refused you is the first useful step, and the wording of the error is what tells you.</p>
<p><strong>Read the git error before reading anything else.</strong> The refusals are distinguishable in text. A key marked read only names the key directly. <code>Write access to repository not granted</code> can be either the key or the token depending on the protocol in use. <code>Permission denied (publickey)</code> is a different problem entirely &mdash; the key was not accepted at all, so it is not on this repository. And <code>protected branch hook declined</code> means the credential was fine and <a href="/github/branch-protection-requires-admin/">the branch refused the update</a>. Four different repairs, all in the same corner of the same build log.</p>
<p><strong>Deploy keys are also an inventory problem.</strong> The listing shows <code>created_at</code> and <code>added_by</code>, and it usually turns up keys nobody remembers, added by people who have left, for jobs that no longer run. That inventory is worth reading while you are here, especially for any key that is <em>not</em> read-only: a write-capable key with no rotation date on a repository that does not push is a standing grant nobody is thinking about.</p>
<p><strong>The key material is never printed, and the check never pushes.</strong> The listing includes the public key itself, and this script drops that field before anything is written to a log or a JSON file: what gets reported is the id, the title, the boolean and the dates. Nor does it test the key by attempting a push. The declared capability is the finding, it is one field, and confirming it by pushing to somebody's repository would be a change made to learn something already published.</p>""",
"steps": [
 {"h": "Decide which credential refused you",
  "body": """<p>Paste the line from the build log into <code>--git-error</code>. A key marked read only, a write access not granted, a plain public-key rejection and a protected-branch refusal are four different problems with four different repairs, and the wording separates them. This step costs nothing and stops the SSH investigation before it starts.</p>"""},
 {"h": "List the deploy keys on the repository",
  "body": """<p>One <code>GET /repos/{owner}/{repo}/keys</code>. Every key comes back with <code>read_only</code>, <code>title</code>, <code>created_at</code>, <code>verified</code> and <code>added_by</code>. The endpoint needs repository admin; where the token does not have it the script says the keys are unreadable rather than reporting that there are none, because those are different findings and one of them is about your token.</p>"""},
 {"h": "Compare the capability against what the job now does",
  "body": """<p>Tell the script whether the automation pushes with <code>--needs-write</code>. A repository that pushes and has no write-capable key is the finding; a repository that only reads and has only read-only keys is correct and is reported as correct. The state that deserves a second look is the opposite one &mdash; a write-capable key on a repository whose automation only ever reads.</p>"""},
 {"h": "Read the inventory while the listing is in front of you",
  "body": """<p><code>created_at</code> and <code>added_by</code> are in the same response. Keys older than your rotation policy are listed with their age, which is usually how a key added for a migration in 2021 by somebody who has since left gets noticed. The key material itself is dropped before anything is printed: ids, titles and booleans are what a report needs.</p>"""},
 {"h": "Prefer an installation token to a wider key",
  "body": """<p>If writes are genuinely required, the narrow repair is a new deploy key created with write access and the old one deleted. The better one is usually a GitHub App installation token with <code>contents: write</code>, which expires in an hour, is scoped to the repositories you choose, and shows up in the audit log as the App rather than as an anonymous key on a repository. The script prints both, and performs neither.</p>"""},
],
"verify": """<p>After the key is replaced, or the job is moved to an installation token, the same listing answers the question without any of the SSH archaeology.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_deploy_key_capability.py \\
    --repo acme/platform-api --needs-write \\
    --git-error "ERROR: The key you are authenticating with has been marked as read only."
# read cost: 1 request(s) per repository against the core hourly quota
# git error -> deploy-key-read-only: the message names the key itself, so the
# refusal is the key's declared capability and not a scope, a token or SSH
# acme/platform-api: 3 deploy key(s), 0 of them write-capable
#   key 41288114 "ci-fetch" read-only created 2021-06-02 by dana-ops, 1550 day(s) old
#   key 55210987 "release-runner" read-only created 2024-11-18 by build-bot
#   key 61004422 "docs-mirror" read-only created 2025-03-04 by dana-ops
# write-needed-none-capable: this repository's automation pushes and every
# deploy key on it is read-only, which is the whole failure
# repair: create a replacement deploy key with write access and delete the old
# one, or move the job to a GitHub App installation token with contents: write,
# which is scoped, expiring and auditable
# rotation: 1 key(s) older than 365 day(s)</code></pre>""",
"code_intro": "One request and a text classifier, which is the right shape for a failure whose difficulty is recognising it rather than finding it. The classifier goes first because it decides whether to keep reading at all: three of its four outcomes send you somewhere other than the deploy keys. The listing is then reduced to metadata before anything else touches it &mdash; the public key material is dropped in one place, so nothing downstream can leak it into a log or a JSON artefact &mdash; and the verdict is a comparison between a boolean the API declares and a fact about your job that only you can supply.",
"py_file": "github_deploy_key_capability.py",
"py": '''"""Check whether a repository's deploy keys can do what its automation needs.

Read only. One GET per repository, nothing is written, and the keys are never
exercised: no push is attempted to find out whether a key can push. The
capability is declared on the key object as read_only, which is the same fact
one request earlier and without changing anybody's repository.

The point of the note: a deploy key's read_only flag is chosen when the key is
created and cannot be edited afterwards. Read-only is the default and is right
for almost every use, so a key added for a CI job that reads works perfectly
until somebody adds a push step. The refusal then arrives from Git over SSH
rather than from the API, so the diagnosis starts in the wrong tool, and no
scope, App permission or token change moves it.

The public key material is dropped before anything is printed. What this
reports is ids, titles, the boolean and the dates.

What this can and cannot see: the keys endpoint needs repository admin, so a
token without it gets a refusal, which is reported as unreadable rather than as
"no keys" -- those are different findings. Which key your SSH client actually
presents is invisible from here; the declared capability of every key on the
repository is not.

Environment:

    GITHUB_TOKEN    a token with admin read on the repository, for the keys
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_deploy_key_capability")

API = "https://api.github.com"
UA = "github-deploy-key-capability/1.0"

# The only fields that leave this script. The listing also carries the public
# key itself; it is dropped here rather than at each print site, so nothing
# downstream can put it in a log or a JSON artefact.
SAFE_FIELDS = ("id", "title", "read_only", "created_at", "verified", "added_by")

# A deploy key older than this is worth a look during the same read.
DEFAULT_MAX_AGE_DAYS = 365


def redact(key):
    """One deploy key reduced to metadata. Pure. Never carries key material."""
    if not isinstance(key, dict):
        return {}
    out = {}
    for field in SAFE_FIELDS:
        if field in key:
            out[field] = key[field]
    return out


def redact_all(keys):
    """The whole listing, reduced. Pure."""
    return [redact(k) for k in (keys or []) if isinstance(k, dict)]


def capability(key):
    """What this key is allowed to do, as declared. Pure."""
    if not isinstance(key, dict) or "read_only" not in key:
        return "unknown"
    return "read-only" if key.get("read_only") else "read-write"


def writable_keys(keys):
    """The ids of keys that can push. Pure."""
    return [k.get("id") for k in (keys or [])
            if isinstance(k, dict) and capability(k) == "read-write"]


def verdict(status, keys, needs_write):
    """Classify one repository's deploy keys. Pure. (state, detail).

    needs_write is a fact about your job rather than about the repository, so
    it has to be supplied. The API knows what the keys can do; it does not know
    what you were going to ask them to do.
    """
    try:
        code = int(status)
    except (TypeError, ValueError):
        code = None

    if code != 200:
        if code in (403, 404):
            return ("keys-unreadable",
                    "the deploy keys endpoint needs repository admin and this "
                    "token does not have it. That is not the same as the "
                    "repository having no keys.")
        return ("keys-unreadable",
                "the deploy keys could not be listed, so nothing here is a "
                "finding about the keys.")

    rows = [k for k in (keys or []) if isinstance(k, dict)]
    writable = writable_keys(rows)

    if not rows:
        if needs_write:
            return ("no-deploy-keys",
                    "this repository has no deploy keys at all, so a push over "
                    "SSH is authenticating with something else or not at all.")
        return ("no-deploy-keys",
                "this repository has no deploy keys, which is fine if nothing "
                "clones it over SSH.")

    if needs_write and not writable:
        return ("write-needed-none-capable",
                "this repository's automation pushes and all %d deploy key(s) "
                "on it are read-only, which is the whole failure." % len(rows))
    if needs_write:
        return ("write-capable-key-present",
                "%d of %d deploy key(s) can push, so a read-only key is not "
                "what refused this write." % (len(writable), len(rows)))
    if writable:
        return ("write-capable-but-unused",
                "%d deploy key(s) can push on a repository whose automation "
                "only reads. That is a standing grant rather than a failure."
                % len(writable))
    return ("read-only-and-correct",
            "every deploy key is read-only and nothing here needs to push, "
            "which is the recommended arrangement.")


def attribute_git_error(text):
    """Work out which credential refused a push, from the message. Pure.

    Returns (state, detail). Three of the four outcomes send the reader
    somewhere other than the deploy keys, which is the point: the same corner
    of the same build log holds four different problems.
    """
    message = str(text or "").lower()
    if not message.strip():
        return ("no-message", "nothing was supplied to attribute.")
    if "marked as read only" in message or "marked as read-only" in message:
        return ("deploy-key-read-only",
                "the message names the key itself, so the refusal is the key's "
                "declared capability and not a scope, a token or SSH.")
    if "protected branch" in message or "gh006" in message:
        return ("refused-by-branch-protection",
                "the credential was accepted and the branch refused the update. "
                "That is a rule on the ref rather than a capability problem.")
    if "archived" in message:
        return ("repository-archived",
                "the repository is archived and read-only, so no credential of "
                "any kind can write to it.")
    if "permission denied (publickey)" in message:
        return ("key-not-accepted",
                "the key was not accepted at all, so it is not on this "
                "repository or the agent presented a different one. This is "
                "authentication, not capability.")
    if "write access to repository not granted" in message:
        return ("write-not-granted",
                "the write was refused without naming the key. Over SSH that is "
                "a read-only deploy key; over HTTPS it is the token or the "
                "installation. The keys listing settles it.")
    return ("unattributed",
            "the message does not name a known refusal. List the keys anyway "
            "and check which credential the remote URL implies.")


def age_days(created_at, now=None):
    """How old a key is, in whole days. Pure. None when unreadable."""
    if not created_at:
        return None
    text = str(created_at).replace("Z", "+00:00")
    try:
        when = datetime.fromisoformat(text)
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    return max(0, (now - when).days)


def stale_keys(keys, max_age_days=DEFAULT_MAX_AGE_DAYS, now=None):
    """Keys older than the rotation policy. Pure. Metadata only."""
    out = []
    for key in keys or []:
        if not isinstance(key, dict):
            continue
        age = age_days(key.get("created_at"), now)
        if age is not None and age >= max_age_days:
            row = redact(key)
            row["age_days"] = age
            out.append(row)
    return out


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state in ("write-needed-none-capable", "deploy-key-read-only"):
        return ("create a replacement deploy key with write access and delete "
                "the old one, or move the job to a GitHub App installation "
                "token with contents: write, which is scoped, expiring and "
                "auditable. read_only cannot be edited on an existing key.")
    if state == "write-capable-key-present":
        return ("look elsewhere for this refusal: a key that can push exists, "
                "so check the branch rules and the repository state.")
    if state == "write-capable-but-unused":
        return ("delete the write-capable key if nothing pushes with it. A "
                "standing write grant on a repository that only gets read is "
                "the kind of thing nobody revisits.")
    if state == "read-only-and-correct":
        return ("nothing. Read-only is the recommended default and this "
                "repository matches what its automation does.")
    if state == "no-deploy-keys":
        return ("check which credential your clone actually uses. With no "
                "deploy keys, an SSH remote is authenticating as a user rather "
                "than as the repository.")
    if state == "keys-unreadable":
        return ("run this with a token that has repository admin, or an App "
                "with administration: read. Do not record the keys as absent.")
    if state == "refused-by-branch-protection":
        return ("read the branch rules rather than the credential. The push was "
                "authorised and the ref refused it.")
    if state == "repository-archived":
        return ("skip the repository. An archived repository is read-only for "
                "every credential.")
    if state == "key-not-accepted":
        return ("fix authentication first: confirm the public key is on this "
                "repository and that the agent is presenting the matching "
                "private key.")
    if state == "write-not-granted":
        return ("check the remote URL. An SSH remote points at the deploy keys, "
                "an HTTPS one points at the token or the installation.")
    return ("list the deploy keys and read read_only before investigating SSH "
            "or scopes.")


def read_cost(repos):
    """Requests this run will spend against the core quota. Pure."""
    return len(repos or [])


def list_keys(session, full_name):
    """One GET of a repository's deploy keys. Returns (status, list)."""
    r = session.get(API + "/repos/" + full_name + "/keys?per_page=100",
                    timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise SystemExit("403 rate limited. GET /rate_limit reports the reset "
                         "time and does not itself consume quota")
    if r.status_code != 200:
        return r.status_code, []
    try:
        body = r.json()
    except ValueError:
        return r.status_code, []
    return r.status_code, (body if isinstance(body, list) else [])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", required=True,
                    help="owner/name to check. Repeatable.")
    ap.add_argument("--needs-write", action="store_true",
                    help="this repository's automation pushes over SSH")
    ap.add_argument("--git-error", default="",
                    help="the line your build log recorded, to attribute the "
                         "refusal without reproducing it")
    ap.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS,
                    help="rotation policy for deploy keys, in days")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (read access plus repository admin for the "
                  "keys endpoint)")
        return 2

    log.info("read cost: %d request(s) per repository against the core hourly "
             "quota", 1)
    log.info("read cost: %d request(s) in total", read_cost(args.repo))

    attributed = None
    if args.git_error:
        state, detail = attribute_git_error(args.git_error)
        log.info("git error -> %s: %s", state, detail)
        log.info("repair: %s", repair(state))
        attributed = {"state": state, "detail": detail, "repair": repair(state)}

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    findings = []
    for name in args.repo:
        status, keys = list_keys(session, name)
        # Reduced here, once. Nothing below this line has the key material.
        rows = redact_all(keys)
        state, detail = verdict(status, rows, args.needs_write)
        stale = stale_keys(rows, args.max_age_days)

        log.info("%s: %d deploy key(s), %d of them write-capable", name,
                 len(rows), len(writable_keys(rows)))
        for row in rows:
            added_by = row.get("added_by") or "unknown"
            age = age_days(row.get("created_at"))
            log.info('  key %s "%s" %s created %s by %s%s', row.get("id"),
                     row.get("title"), capability(row),
                     str(row.get("created_at") or "")[:10], added_by,
                     ", %d day(s) old" % age if age is not None else "")
        log.info("%s: %s", state, detail)
        log.info("repair: %s", repair(state))
        if stale:
            log.info("rotation: %d key(s) older than %d day(s)", len(stale),
                     args.max_age_days)

        findings.append({
            "repository": name,
            "keys_status": status,
            "keys": rows,
            "write_capable_ids": writable_keys(rows),
            "stale_keys": stale,
            "state": state,
            "detail": detail,
            "repair": repair(state),
        })

    print(json.dumps({
        "requests_spent": read_cost(args.repo),
        "git_error": attributed,
        "findings": findings,
    }, indent=2, default=str))
    bad = {"write-needed-none-capable", "write-capable-but-unused"}
    return 1 if any(f["state"] in bad for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-deploy-key-capability.mjs",
"js": '''/**
 * Check whether a repository's deploy keys can do what its automation needs.
 *
 * Read only. One GET per repository, nothing is written, and the keys are never
 * exercised: no push is attempted to find out whether a key can push. The
 * capability is declared on the key object as read_only.
 *
 * A deploy key's read_only flag is chosen at creation and cannot be edited
 * afterwards, so a read-only key added for a CI job that reads works perfectly
 * until somebody adds a push step. The refusal then arrives from Git over SSH
 * rather than from the API, and no scope or token change moves it.
 *
 * The public key material is dropped before anything is printed.
 *
 * Environment:
 *   GITHUB_TOKEN       read access plus repository admin, for the keys endpoint
 *   GITHUB_REPOS       comma-separated owner/name values
 *   GITHUB_NEEDS_WRITE set to 1 when the automation pushes over SSH
 *   GITHUB_GIT_ERROR   the line your build log recorded
 */
const API = 'https://api.github.com';
const UA = 'github-deploy-key-capability/1.0';

/** The only fields that leave this script. The key material is not among them. */
export const SAFE_FIELDS = ['id', 'title', 'read_only', 'created_at', 'verified',
  'added_by'];

/** A deploy key older than this is worth a look during the same read. */
export const DEFAULT_MAX_AGE_DAYS = 365;

/** One deploy key reduced to metadata. Pure. Never carries key material. */
export function redact(key) {
  if (!key || typeof key !== 'object') return {};
  const out = {};
  for (const field of SAFE_FIELDS) {
    if (field in key) out[field] = key[field];
  }
  return out;
}

/** The whole listing, reduced. Pure. */
export function redactAll(keys) {
  return (keys || []).filter((k) => k && typeof k === 'object').map(redact);
}

/** What this key is allowed to do, as declared. Pure. */
export function capability(key) {
  if (!key || typeof key !== 'object' || !('read_only' in key)) return 'unknown';
  return key.read_only ? 'read-only' : 'read-write';
}

/** The ids of keys that can push. Pure. */
export function writableKeys(keys) {
  return (keys || []).filter((k) => k && typeof k === 'object'
    && capability(k) === 'read-write').map((k) => k.id);
}

/** Classify one repository's deploy keys. Pure. [state, detail]. */
export function verdict(status, keys, needsWrite) {
  const code = Number(status);

  if (code !== 200) {
    if (code === 403 || code === 404) {
      return ['keys-unreadable', 'the deploy keys endpoint needs repository '
        + 'admin and this token does not have it. That is not the same as the '
        + 'repository having no keys.'];
    }
    return ['keys-unreadable', 'the deploy keys could not be listed, so nothing '
      + 'here is a finding about the keys.'];
  }

  const rows = (keys || []).filter((k) => k && typeof k === 'object');
  const writable = writableKeys(rows);

  if (!rows.length) {
    if (needsWrite) {
      return ['no-deploy-keys', 'this repository has no deploy keys at all, so '
        + 'a push over SSH is authenticating with something else or not at all.'];
    }
    return ['no-deploy-keys', 'this repository has no deploy keys, which is fine '
      + 'if nothing clones it over SSH.'];
  }

  if (needsWrite && !writable.length) {
    return ['write-needed-none-capable', "this repository's automation pushes "
      + `and all ${rows.length} deploy key(s) on it are read-only, which is the `
      + 'whole failure.'];
  }
  if (needsWrite) {
    return ['write-capable-key-present', `${writable.length} of ${rows.length} `
      + 'deploy key(s) can push, so a read-only key is not what refused this write.'];
  }
  if (writable.length) {
    return ['write-capable-but-unused', `${writable.length} deploy key(s) can `
      + 'push on a repository whose automation only reads. That is a standing '
      + 'grant rather than a failure.'];
  }
  return ['read-only-and-correct', 'every deploy key is read-only and nothing '
    + 'here needs to push, which is the recommended arrangement.'];
}

/** Work out which credential refused a push, from the message. Pure. */
export function attributeGitError(text) {
  const message = String(text ?? '').toLowerCase();
  if (!message.trim()) return ['no-message', 'nothing was supplied to attribute.'];
  if (message.includes('marked as read only') || message.includes('marked as read-only')) {
    return ['deploy-key-read-only', 'the message names the key itself, so the '
      + "refusal is the key's declared capability and not a scope, a token or SSH."];
  }
  if (message.includes('protected branch') || message.includes('gh006')) {
    return ['refused-by-branch-protection', 'the credential was accepted and the '
      + 'branch refused the update. That is a rule on the ref rather than a '
      + 'capability problem.'];
  }
  if (message.includes('archived')) {
    return ['repository-archived', 'the repository is archived and read-only, so '
      + 'no credential of any kind can write to it.'];
  }
  if (message.includes('permission denied (publickey)')) {
    return ['key-not-accepted', 'the key was not accepted at all, so it is not on '
      + 'this repository or the agent presented a different one. This is '
      + 'authentication, not capability.'];
  }
  if (message.includes('write access to repository not granted')) {
    return ['write-not-granted', 'the write was refused without naming the key. '
      + 'Over SSH that is a read-only deploy key; over HTTPS it is the token or '
      + 'the installation. The keys listing settles it.'];
  }
  return ['unattributed', 'the message does not name a known refusal. List the '
    + 'keys anyway and check which credential the remote URL implies.'];
}

/** How old a key is, in whole days. Pure. Null when unreadable. */
export function ageDays(createdAt, now = Date.now()) {
  if (!createdAt) return null;
  const when = Date.parse(String(createdAt));
  if (!Number.isFinite(when)) return null;
  return Math.max(0, Math.floor((now - when) / 86400000));
}

/** Keys older than the rotation policy. Pure. Metadata only. */
export function staleKeys(keys, maxAgeDays = DEFAULT_MAX_AGE_DAYS, now = Date.now()) {
  const out = [];
  for (const key of keys || []) {
    if (!key || typeof key !== 'object') continue;
    const age = ageDays(key.created_at, now);
    if (age !== null && age >= maxAgeDays) out.push({ ...redact(key), age_days: age });
  }
  return out;
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (['write-needed-none-capable', 'deploy-key-read-only'].includes(state)) {
    return 'create a replacement deploy key with write access and delete the old '
      + 'one, or move the job to a GitHub App installation token with '
      + 'contents: write, which is scoped, expiring and auditable. read_only '
      + 'cannot be edited on an existing key.';
  }
  if (state === 'write-capable-key-present') {
    return 'look elsewhere for this refusal: a key that can push exists, so check '
      + 'the branch rules and the repository state.';
  }
  if (state === 'write-capable-but-unused') {
    return 'delete the write-capable key if nothing pushes with it. A standing '
      + 'write grant on a repository that only gets read is the kind of thing '
      + 'nobody revisits.';
  }
  if (state === 'read-only-and-correct') {
    return 'nothing. Read-only is the recommended default and this repository '
      + 'matches what its automation does.';
  }
  if (state === 'no-deploy-keys') {
    return 'check which credential your clone actually uses. With no deploy keys, '
      + 'an SSH remote is authenticating as a user rather than as the repository.';
  }
  if (state === 'keys-unreadable') {
    return 'run this with a token that has repository admin, or an App with '
      + 'administration: read. Do not record the keys as absent.';
  }
  if (state === 'refused-by-branch-protection') {
    return 'read the branch rules rather than the credential. The push was '
      + 'authorised and the ref refused it.';
  }
  if (state === 'repository-archived') {
    return 'skip the repository. An archived repository is read-only for every '
      + 'credential.';
  }
  if (state === 'key-not-accepted') {
    return 'fix authentication first: confirm the public key is on this '
      + 'repository and that the agent is presenting the matching private key.';
  }
  if (state === 'write-not-granted') {
    return 'check the remote URL. An SSH remote points at the deploy keys, an '
      + 'HTTPS one points at the token or the installation.';
  }
  return 'list the deploy keys and read read_only before investigating SSH or scopes.';
}

/** Requests this run will spend against the core quota. Pure. */
export function readCost(repos) {
  return (repos || []).length;
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
  const names = (process.env.GITHUB_REPOS || '').split(',')
    .map((n) => n.trim()).filter(Boolean);
  if (!token || !names.length) {
    console.error('set GITHUB_TOKEN and GITHUB_REPOS');
    process.exitCode = 2;
    return;
  }
  const needsWrite = process.env.GITHUB_NEEDS_WRITE === '1';

  console.log('read cost: 1 request(s) per repository against the core hourly quota');
  console.log(`read cost: ${readCost(names)} request(s) in total`);

  let attributed = null;
  const gitError = process.env.GITHUB_GIT_ERROR || '';
  if (gitError) {
    const [state, detail] = attributeGitError(gitError);
    console.log(`git error -> ${state}: ${detail}`);
    console.log(`repair: ${repair(state)}`);
    attributed = { state, detail, repair: repair(state) };
  }

  const findings = [];
  for (const name of names) {
    const res = await fetch(`${API}/repos/${name}/keys?per_page=100`,
      { headers: headers(token) });
    let body = null;
    try { body = await res.json(); } catch { body = null; }
    // Reduced here, once. Nothing below this line has the key material.
    const rows = redactAll(Array.isArray(body) ? body : []);
    const [state, detail] = verdict(res.status, rows, needsWrite);
    const stale = staleKeys(rows);

    console.log(`${name}: ${rows.length} deploy key(s), `
      + `${writableKeys(rows).length} of them write-capable`);
    for (const row of rows) {
      const age = ageDays(row.created_at);
      console.log(`  key ${row.id} "${row.title}" ${capability(row)} created `
        + `${String(row.created_at || '').slice(0, 10)} by ${row.added_by || 'unknown'}`
        + (age === null ? '' : `, ${age} day(s) old`));
    }
    console.log(`${state}: ${detail}`);
    console.log(`repair: ${repair(state)}`);
    if (stale.length) {
      console.log(`rotation: ${stale.length} key(s) older than ${DEFAULT_MAX_AGE_DAYS} day(s)`);
    }

    findings.push({
      repository: name,
      keys_status: res.status,
      keys: rows,
      write_capable_ids: writableKeys(rows),
      stale_keys: stale,
      state,
      detail,
      repair: repair(state),
    });
  }

  console.log(JSON.stringify({
    requests_spent: readCost(names),
    git_error: attributed,
    findings,
  }, null, 2));
  const bad = ['write-needed-none-capable', 'write-capable-but-unused'];
  process.exitCode = findings.some((f) => bad.includes(f.state)) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The first test is about the thing that must never happen: the key material goes in and does not come out, asserted against the serialised report rather than against a field name, because that is where a leak would actually appear. After that the error classifier gets a test per outcome, since its whole job is to send three readers out of four somewhere else, and the verdict is tested against both answers to the one question the API cannot answer &mdash; whether this repository's automation pushes. A refusal to list the keys is asserted to stay a refusal rather than becoming an empty inventory.",
"test_py_file": "test_github_deploy_key_capability.py",
"test_py": '''import json

from github_deploy_key_capability import (
    DEFAULT_MAX_AGE_DAYS, SAFE_FIELDS, age_days, attribute_git_error,
    capability, read_cost, redact, redact_all, repair, stale_keys, verdict,
    writable_keys,
)

# Obviously not a key. The point of the fixture is that it never comes back out.
FAKE_MATERIAL = "ssh-ed25519 FAKE"

READ_ONLY = {"id": 41288114, "key": FAKE_MATERIAL, "title": "ci-fetch",
             "read_only": True, "created_at": "2021-06-02T11:03:00Z",
             "verified": True, "added_by": "dana-ops"}
WRITABLE = {"id": 55210987, "key": FAKE_MATERIAL, "title": "release-runner",
            "read_only": False, "created_at": "2024-11-18T08:00:00Z",
            "verified": True, "added_by": "build-bot"}


def test_the_key_material_never_leaves_the_script():
    reduced = redact(READ_ONLY)
    assert "key" not in reduced
    assert FAKE_MATERIAL not in json.dumps(reduced)
    assert FAKE_MATERIAL not in json.dumps(redact_all([READ_ONLY, WRITABLE]))
    assert set(reduced) <= set(SAFE_FIELDS)
    assert reduced["id"] == 41288114
    assert reduced["read_only"] is True


def test_redaction_survives_junk_without_leaking_it():
    assert redact(None) == {}
    assert redact("not a key") == {}
    assert redact_all(None) == []
    assert redact_all([None, "x", READ_ONLY]) == [redact(READ_ONLY)]


def test_the_capability_is_a_declared_field_not_an_experiment():
    assert capability(READ_ONLY) == "read-only"
    assert capability(WRITABLE) == "read-write"
    assert capability({"id": 1}) == "unknown"
    assert capability(None) == "unknown"
    assert writable_keys([READ_ONLY, WRITABLE]) == [55210987]
    assert writable_keys([READ_ONLY]) == []


def test_a_pushing_job_with_only_read_only_keys_is_the_finding():
    state, detail = verdict(200, [READ_ONLY, READ_ONLY], True)
    assert state == "write-needed-none-capable"
    assert "all 2 deploy key(s)" in detail
    assert "cannot be edited on an existing key" in repair(state)
    assert "contents: write" in repair(state)


def test_the_same_keys_are_correct_when_nothing_pushes():
    state, detail = verdict(200, [READ_ONLY], False)
    assert state == "read-only-and-correct"
    assert "recommended arrangement" in detail
    assert repair(state).startswith("nothing.")


def test_a_write_capable_key_is_reported_either_way():
    assert verdict(200, [READ_ONLY, WRITABLE], True)[0] == "write-capable-key-present"
    state, detail = verdict(200, [READ_ONLY, WRITABLE], False)
    assert state == "write-capable-but-unused"
    assert "standing grant" in detail


def test_a_refused_listing_is_not_an_empty_inventory():
    state, detail = verdict(403, [], True)
    assert state == "keys-unreadable"
    assert "not the same as the repository having no keys" in detail
    assert "Do not record the keys as absent" in repair(state)
    assert verdict(404, [], False)[0] == "keys-unreadable"
    assert verdict(None, [], False)[0] == "keys-unreadable"


def test_no_keys_at_all_is_its_own_answer():
    state, detail = verdict(200, [], True)
    assert state == "no-deploy-keys"
    assert "authenticating with something else" in detail
    assert "which credential your clone actually uses" in repair(state)


def test_the_read_only_message_names_the_key_itself():
    state, detail = attribute_git_error(
        "ERROR: The key you are authenticating with has been marked as read only.")
    assert state == "deploy-key-read-only"
    assert "not a scope, a token or SSH" in detail


def test_three_of_the_four_messages_send_you_somewhere_else():
    assert attribute_git_error(
        "remote: error: GH006: Protected branch update failed")[0] == (
        "refused-by-branch-protection")
    assert attribute_git_error(
        "remote: Repository was archived so is read-only.")[0] == "repository-archived"
    assert attribute_git_error(
        "git@github.com: Permission denied (publickey).")[0] == "key-not-accepted"


def test_an_unnamed_write_refusal_depends_on_the_protocol():
    state, detail = attribute_git_error(
        "remote: Write access to repository not granted.")
    assert state == "write-not-granted"
    assert "Over SSH" in detail
    assert "remote URL" in repair(state)


def test_an_unknown_or_absent_message_is_not_invented():
    assert attribute_git_error("something else entirely")[0] == "unattributed"
    assert attribute_git_error("")[0] == "no-message"
    assert attribute_git_error(None)[0] == "no-message"


def test_the_inventory_reports_age_without_reporting_material():
    from datetime import datetime, timezone
    now = datetime(2026, 8, 31, tzinfo=timezone.utc)
    assert age_days("2021-06-02T11:03:00Z", now) == 1915
    assert age_days(None) is None
    assert age_days("not a date") is None
    stale = stale_keys([READ_ONLY, WRITABLE], DEFAULT_MAX_AGE_DAYS, now)
    assert len(stale) == 2
    assert stale[0]["age_days"] == 1915
    assert FAKE_MATERIAL not in json.dumps(stale)
    assert stale_keys([READ_ONLY], 10000, now) == []


def test_the_cost_is_worked_out_before_anything_is_fetched():
    assert read_cost(["a", "b"]) == 2
    assert read_cost([]) == 0
    assert read_cost(None) == 0
    assert DEFAULT_MAX_AGE_DAYS == 365
''',
"test_js_file": "github-deploy-key-capability.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DEFAULT_MAX_AGE_DAYS, SAFE_FIELDS, ageDays, attributeGitError, capability,
  readCost, redact, redactAll, repair, staleKeys, verdict, writableKeys,
} from './github-deploy-key-capability.mjs';

// Obviously not a key. The point of the fixture is that it never comes back out.
const FAKE_MATERIAL = 'ssh-ed25519 FAKE';

const READ_ONLY = {
  id: 41288114,
  key: FAKE_MATERIAL,
  title: 'ci-fetch',
  read_only: true,
  created_at: '2021-06-02T11:03:00Z',
  verified: true,
  added_by: 'dana-ops',
};
const WRITABLE = {
  id: 55210987,
  key: FAKE_MATERIAL,
  title: 'release-runner',
  read_only: false,
  created_at: '2024-11-18T08:00:00Z',
  verified: true,
  added_by: 'build-bot',
};

test('the key material never leaves the script', () => {
  const reduced = redact(READ_ONLY);
  assert.ok(!('key' in reduced));
  assert.ok(!JSON.stringify(reduced).includes(FAKE_MATERIAL));
  assert.ok(!JSON.stringify(redactAll([READ_ONLY, WRITABLE])).includes(FAKE_MATERIAL));
  assert.ok(Object.keys(reduced).every((k) => SAFE_FIELDS.includes(k)));
  assert.equal(reduced.id, 41288114);
  assert.equal(reduced.read_only, true);
});

test('redaction survives junk without leaking it', () => {
  assert.deepEqual(redact(null), {});
  assert.deepEqual(redact('not a key'), {});
  assert.deepEqual(redactAll(null), []);
  assert.deepEqual(redactAll([null, 'x', READ_ONLY]), [redact(READ_ONLY)]);
});

test('the capability is a declared field not an experiment', () => {
  assert.equal(capability(READ_ONLY), 'read-only');
  assert.equal(capability(WRITABLE), 'read-write');
  assert.equal(capability({ id: 1 }), 'unknown');
  assert.equal(capability(null), 'unknown');
  assert.deepEqual(writableKeys([READ_ONLY, WRITABLE]), [55210987]);
  assert.deepEqual(writableKeys([READ_ONLY]), []);
});

test('a pushing job with only read only keys is the finding', () => {
  const [state, detail] = verdict(200, [READ_ONLY, READ_ONLY], true);
  assert.equal(state, 'write-needed-none-capable');
  assert.match(detail, /all 2 deploy key\\(s\\)/);
  assert.match(repair(state), /cannot be edited on an existing key/);
  assert.match(repair(state), /contents: write/);
});

test('the same keys are correct when nothing pushes', () => {
  const [state, detail] = verdict(200, [READ_ONLY], false);
  assert.equal(state, 'read-only-and-correct');
  assert.match(detail, /recommended arrangement/);
  assert.ok(repair(state).startsWith('nothing.'));
});

test('a write capable key is reported either way', () => {
  assert.equal(verdict(200, [READ_ONLY, WRITABLE], true)[0], 'write-capable-key-present');
  const [state, detail] = verdict(200, [READ_ONLY, WRITABLE], false);
  assert.equal(state, 'write-capable-but-unused');
  assert.match(detail, /standing grant/);
});

test('a refused listing is not an empty inventory', () => {
  const [state, detail] = verdict(403, [], true);
  assert.equal(state, 'keys-unreadable');
  assert.match(detail, /not the same as the repository having no keys/);
  assert.match(repair(state), /Do not record the keys as absent/);
  assert.equal(verdict(404, [], false)[0], 'keys-unreadable');
  assert.equal(verdict(null, [], false)[0], 'keys-unreadable');
});

test('no keys at all is its own answer', () => {
  const [state, detail] = verdict(200, [], true);
  assert.equal(state, 'no-deploy-keys');
  assert.match(detail, /authenticating with something else/);
  assert.match(repair(state), /which credential your clone actually uses/);
});

test('the read only message names the key itself', () => {
  const [state, detail] = attributeGitError(
    'ERROR: The key you are authenticating with has been marked as read only.');
  assert.equal(state, 'deploy-key-read-only');
  assert.match(detail, /not a scope, a token or SSH/);
});

test('three of the four messages send you somewhere else', () => {
  assert.equal(attributeGitError(
    'remote: error: GH006: Protected branch update failed')[0],
  'refused-by-branch-protection');
  assert.equal(attributeGitError(
    'remote: Repository was archived so is read-only.')[0], 'repository-archived');
  assert.equal(attributeGitError(
    'git@github.com: Permission denied (publickey).')[0], 'key-not-accepted');
});

test('an unnamed write refusal depends on the protocol', () => {
  const [state, detail] = attributeGitError(
    'remote: Write access to repository not granted.');
  assert.equal(state, 'write-not-granted');
  assert.match(detail, /Over SSH/);
  assert.match(repair(state), /remote URL/);
});

test('an unknown or absent message is not invented', () => {
  assert.equal(attributeGitError('something else entirely')[0], 'unattributed');
  assert.equal(attributeGitError('')[0], 'no-message');
  assert.equal(attributeGitError(null)[0], 'no-message');
});

test('the inventory reports age without reporting material', () => {
  const now = Date.parse('2026-08-31T00:00:00Z');
  assert.equal(ageDays('2021-06-02T11:03:00Z', now), 1915);
  assert.equal(ageDays(null), null);
  assert.equal(ageDays('not a date'), null);
  const stale = staleKeys([READ_ONLY, WRITABLE], DEFAULT_MAX_AGE_DAYS, now);
  assert.equal(stale.length, 2);
  assert.equal(stale[0].age_days, 1915);
  assert.ok(!JSON.stringify(stale).includes(FAKE_MATERIAL));
  assert.deepEqual(staleKeys([READ_ONLY], 10000, now), []);
});

test('the cost is worked out before anything is fetched', () => {
  assert.equal(readCost(['a', 'b']), 2);
  assert.equal(readCost([]), 0);
  assert.equal(readCost(null), 0);
  assert.equal(DEFAULT_MAX_AGE_DAYS, 365);
});
''',
"faq": [
 ("Can I make an existing deploy key writable?",
  "No. <code>read_only</code> is set when the key is created and is not editable afterwards, which is why this is a replacement rather than an adjustment. Add a new key created with write access, point the job at it, and delete the old one so nobody is left wondering which of the two is live. That is also the moment to ask whether a deploy key is still the right credential, because a key on a repository has no expiry and no identity beyond its title."),
 ("Why did widening my token change nothing?",
  "Because the push was not using the token. A repository can be reached over SSH with a deploy key and over HTTPS with a token, and a job that does both is using two unrelated credentials with independent capabilities. If the remote is <code>git@github.com:owner/repo.git</code>, the deploy key is what authorised the push and the token is irrelevant to it. Check the remote URL first; it tells you which credential to investigate and saves the hour that usually goes into scopes."),
 ("Should we use a GitHub App instead?",
  "Usually, yes, for anything that writes. An installation token with <code>contents: write</code> expires in about an hour, is scoped to the repositories you select, and appears in the audit log as the App that used it, whereas a write-capable deploy key is permanent, anonymous beyond its title, and sits on the repository until somebody notices it. Deploy keys remain a good answer for read-only cloning where an App would be more machinery than the job deserves."),
 ("The keys endpoint returned 403. Does that mean there are no keys?",
  "It means you cannot see them, and the two must not be recorded the same way. Listing deploy keys needs repository admin, so a read-only auditing token gets a refusal on repositories that may have any number of keys. The script reports that as unreadable rather than as an empty inventory, because a report saying &ldquo;no deploy keys anywhere&rdquo; that was produced by a token which could not read any of them is worse than no report."),
 ("Does the script try a push to confirm the key cannot write?",
  "No. Every script in this section is read only, and here it is not even a limitation: the capability is declared on the key object as a boolean, so pushing would establish the same fact one request later while writing to somebody's repository. The script reads the field, reports ids and titles and dates &mdash; never the key material itself &mdash; and classifies the error line you already have from the build log."),
],
"related": [
 ("/github/over-scoped-token/", "The mirror image: a credential that can do too much"),
 ("/github/branch-protection-requires-admin/", "When the ref refuses the push, not the key"),
 ("/github/app-permission-missing/", "Permissions on an App, which are a different model"),
],
"citations": [CITE_DEPLOY_KEYS_REST, CITE_MANAGING_DEPLOY_KEYS, CITE_APP_INSTALL_AUTH, CITE_APP_PERMS],
},
]
