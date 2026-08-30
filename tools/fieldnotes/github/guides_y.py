#!/usr/bin/env python3
"""/github/ field notes, batch Y — the writing. The last five in the section.

Five notes about a claim that is not what it looks like. In each one something
answers, plausibly, and the answer is read as a stronger statement than it is.

The first is about a field. `verification.verified` is one boolean on a
five-field object, and a policy that says "all commits are signed" is usually
implemented as a test on the wrong thing entirely: the commit author, which is
free text anybody can set. Read properly, `verified: false` covers a dozen
reasons that are not the same finding, one of them is GitHub's own checker
being unavailable, and a *missing* verification object is not a false one. The
section publishes nothing about commit signatures; this note owns what the
field guarantees and what it does not.

The second is about a status code. GitHub documents that it answers 404 rather
than 405 when a route does not accept your verb, so a path copied correctly out
of the documentation fails identically to a path that does not exist. The
section's existing 404 note sorts a 404 by *who is asking*; this one sorts it
by *whether anything is there to ask*, and the discriminator is a field in the
body that nobody reads. It also refuses, loudly, to establish the answer the
obvious way, because sending the write verb to see what comes back is both a
write and a useless measurement.

The third is about a clock that is not the one already published. The section
owns the countdown on a token's expiry. This note owns the *ceiling*: an
organization can cap how long a fine-grained token may live, and the failure is
a rotation interval longer than the cap, which is a comparison between two
periods rather than a number of days remaining. It also owns the fact that the
policy does not shorten the token you are holding; it refuses it at one
organization while it keeps working everywhere else.

The fourth is about a role that is not a membership. An outside collaborator
holds repositories inside an organization without being in the organization, so
repository reads work and organization reads do not. The section already owns
data silently withheld from a 200 by SAML, which announces itself in a header;
this announces nothing, and the partition that proves it is which affiliation
the account's repositories arrive under.

The fifth is about a host. Every route 404s, or a good token 401s, because the
client is talking to a different GitHub installation from the one that holds
the resources. One unauthenticated read separates the three host families, and
the root endpoint map names the host that actually answered, which survives a
redirect that a hostname in a config file does not.

Nothing here writes. The second note in particular is the one where the
temptation is strongest and the refusal is explicit: it will not send a verb to
find out whether the verb is accepted. Every script GETs, prints its read cost
before it spends it, and exits.
"""

CITE_COMMITS = ("Commits — GitHub REST API",
                "https://docs.github.com/en/rest/commits/commits")
CITE_SIGNATURE_VERIFICATION = ("About commit signature verification — GitHub Docs",
                               "https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification")
CITE_RULES = ("Rules — GitHub REST API",
              "https://docs.github.com/en/rest/repos/rules")
CITE_RULESETS_ABOUT = ("About rulesets — GitHub Docs",
                       "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets")
CITE_TROUBLESHOOTING = ("Troubleshooting the REST API — GitHub Docs",
                        "https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api")
CITE_ABOUT_REST = ("About the REST API — GitHub Docs",
                   "https://docs.github.com/en/rest/about-the-rest-api/about-the-rest-api")
CITE_STARRING = ("Starring — GitHub REST API",
                 "https://docs.github.com/en/rest/activity/starring")
CITE_COLLABORATORS = ("Collaborators — GitHub REST API",
                      "https://docs.github.com/en/rest/collaborators/collaborators")
CITE_PAT_POLICY = ("Setting a personal access token policy for your organization — GitHub Docs",
                   "https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization")
CITE_MANAGING_PATS = ("Managing your personal access tokens — GitHub Docs",
                      "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens")
CITE_ORG_PATS = ("Organization personal access tokens — GitHub REST API",
                 "https://docs.github.com/en/rest/orgs/personal-access-tokens")
CITE_RATE_LIMIT = ("Rate limit — GitHub REST API",
                   "https://docs.github.com/en/rest/rate-limit/rate-limit")
CITE_OUTSIDE_COLLABORATORS = ("Outside collaborators — GitHub REST API",
                              "https://docs.github.com/en/rest/orgs/outside-collaborators")
CITE_ADDING_OUTSIDE = ("Adding outside collaborators to repositories in your organization — GitHub Docs",
                       "https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-outside-collaborators/adding-outside-collaborators-to-repositories-in-your-organization")
CITE_USER_REPOS = ("Repositories — GitHub REST API",
                   "https://docs.github.com/en/rest/repos/repos")
CITE_META = ("Meta — GitHub REST API",
             "https://docs.github.com/en/rest/meta/meta")
CITE_GHES_REST = ("GitHub Enterprise Server REST API quickstart — GitHub Docs",
                  "https://docs.github.com/en/enterprise-server@latest/rest/quickstart")
CITE_DATA_RESIDENCY = ("Getting started with data residency for GitHub Enterprise Cloud — GitHub Docs",
                       "https://docs.github.com/en/enterprise-cloud@latest/admin/data-residency/getting-started-with-data-residency-for-github-enterprise-cloud")

GUIDES = [
{
"slug": "unverified-commit-signature-assumed",
"title": "The signature audit reads verified and never reads reason",
"description": "verification is a five-field object. verified: false covers a dozen reasons that are not the same finding, and a missing object is not a false one.",
"h1": "The signature audit reads verified and never reads reason",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api commit verification verified false",
             "github commit verification reason unsigned",
             "github verify signed commits api script",
             "github required_signatures ruleset api",
             "commit author vs committer signature github"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The compliance answer says every commit on the release branch is signed. Somebody wrote a script to prove it, the script has been green for eighteen months, and nobody has looked at it since. Then an auditor asks how the check works and the answer is that it walks the commit list and confirms every author is on the approved list of engineers. That is not a signature check. The commit author is a string the committing client sets, it is never authenticated, and a script that reads it is checking that the person who pushed knew how to type a colleague's name. The signature result is right there in the same response, on a field the script never opens.",
"short_answer": """<p><code>GET /repos/{owner}/{repo}/commits</code> returns a <code>verification</code> object on every commit with five fields: <code>verified</code>, <code>reason</code>, <code>signature</code>, <code>payload</code> and <code>verified_at</code>. Only <code>verified</code> is a boolean, and it is the least informative of the five on its own.</p>
<p><code>verified: true</code> means GitHub cryptographically checked a signature against a key registered to a GitHub account and matched the <em>committer</em> email to a verified email on that account. It says nothing about <code>commit.author</code>, which is unauthenticated free text. <code>verified: false</code> is not one finding but about a dozen, and <code>reason</code> is where they live: <code>unsigned</code> means nobody signed, <code>invalid</code> means somebody signed and the signature does not check out, <code>unknown_key</code> means the signature is fine and the key was never registered, and <code>gpgverify_unavailable</code> means GitHub could not check at all. Those need four different responses.</p>
<p>And a <code>verification</code> object that is <strong>absent</strong> from the payload is not a false one. Treat missing as unknown, report it as unknown, and never let it fall through a truthiness test into either column.</p>""",
"problem": """<p>The reason this survives so long is that the check is green, and it is green for a reason that has nothing to do with signatures. Every commit does have an author, the authors are all real colleagues, so the assertion passes on every run and keeps passing. The one input that would make it fail is a commit whose author string is somebody not on the list, which is also the one thing an attacker would never do. The test is passing on the majority case and would pass on the attack too.</p>
<p>The second version of this is subtler and more common: the script does read <code>verification</code>, and reads it wrongly. <code>if commit["commit"]["verification"]["verified"]:</code> raises a <code>KeyError</code> the first time an endpoint omits the object, so somebody wraps it in a <code>.get()</code> chain with a default, and the default they pick decides the whole policy. Default to <code>True</code> and every commit GitHub could not check is recorded as signed. Default to <code>False</code> and the first time GitHub's verification service has a bad ten minutes the pipeline blocks a release that is perfectly fine. Neither is correct, because the honest answer to "was this signed" in that moment is "I do not know yet".</p>
<p>The third version passes the audit and guarantees nothing at all. A script that reports the history is not a rule that constrains the future. If no ruleset on that branch requires signatures, a hundred per cent verified history is a description of what people happened to do, and the next push is free to be unsigned. The report and the rule are different objects and only one of them stops anything.</p>""",
"why": """<p><strong>Author and committer are different people and only one of them is checked.</strong> A git commit carries an author (who wrote the change) and a committer (who created this commit object), and both are plain strings written by the client. Signature verification binds the <em>committer</em> identity: GitHub matches the committer email against verified emails on the account whose key made the signature. So a verified commit does not assert that <code>commit.author.email</code> belongs to anybody in particular, and a script comparing author names to a roster is reading the one field a signature was never about.</p>
<p><strong>The linked account is a separate field again.</strong> Alongside <code>commit.author</code> and <code>commit.committer</code> — the raw git strings — the response carries top-level <code>author</code> and <code>committer</code> objects, which are the GitHub accounts those emails resolve to, or <code>null</code> when they resolve to nothing. A commit whose top-level <code>author</code> is <code>null</code> was written by an email GitHub does not recognise. That is worth reporting and it is still not the signature.</p>
<p><strong><code>reason</code> sorts into groups with different repairs.</strong> <code>valid</code> is the only value that accompanies <code>verified: true</code>. The rest fall into four families and conflating them produces bad alerts: nobody signed (<code>unsigned</code>); a signature exists and fails cryptographically (<code>invalid</code>, <code>malformed_signature</code>, <code>expired_key</code>, <code>not_signing_key</code>, <code>unknown_signature_type</code>); a signature is fine but the identity is not linked to an account (<code>unknown_key</code>, <code>no_user</code>, <code>unverified_email</code>, <code>bad_email</code>); and GitHub could not perform the check (<code>gpgverify_error</code>, <code>gpgverify_unavailable</code>). The third family is usually a person who never uploaded their public key, which is a five-minute fix. The fourth is not about your repository at all.</p>
<p><strong>Verification is recorded, not recomputed on read.</strong> GitHub stores the verification result, so a commit signed with a key that has since been rotated or revoked stays verified, and a commit whose author has left the organization stays verified. That is the intended behaviour and it means "verified" is a statement about the moment of signing, which <code>verified_at</code> dates. It is not a claim that the key is still trusted today.</p>
<p><strong>A report is not an enforcement.</strong> <code>GET /repos/{owner}/{repo}/rules/branches/{branch}</code> returns the rules actually in force on a branch, and <code>required_signatures</code> is the one that makes unsigned pushes bounce. Reading it turns "our history happens to be signed" into "unsigned pushes are rejected", and the gap between those two sentences is the entire value of this note. The script reads the rule; it does not create one.</p>""",
"steps": [
 {"h": "Say out loud which field your current check reads",
  "body": """<p>Before running anything: open the existing compliance script and find the expression it asserts on. If the words <code>author</code> or <code>committer</code> appear and <code>verification</code> does not, you do not have a signature check, and no amount of tuning will turn it into one. The script below takes an <code>--author-allowlist</code> precisely so it can run both checks side by side and count the commits on which they disagree.</p>"""},
 {"h": "Pull the commits and normalise the verification object",
  "body": """<p>One page of <code>GET /repos/{owner}/{repo}/commits?per_page=100</code> per <code>--pages</code>, against <code>--ref</code> if you want a specific branch. Each commit is normalised into present/absent, verified, reason and whether a signature blob is there at all, so that a missing object becomes an explicit <code>verification-absent</code> rather than a falsy value flowing into a boolean.</p>"""},
 {"h": "Sort by reason, not by the boolean",
  "body": """<p>The tally is by family: verified, unsigned, signature rejected, identity not linked, and GitHub could not check. The last one is deliberately kept out of the violation count. An outage in the verification service is not a compliance failure in your repository, and a check that treats it as one will page somebody at three in the morning about somebody else's incident.</p>"""},
 {"h": "Count the disagreements between the two checks",
  "body": """<p>With <code>--author-allowlist alice@example.com,bob@example.com</code> the script runs the naive author test and the signature test over the same commits and prints every commit where they differ. Two columns matter: commits the author test passes and the signature test does not, which is what your policy has been missing, and commits the signature test passes and the author test does not, which is what it has been falsely flagging.</p>"""},
 {"h": "Read the rule that would have enforced it",
  "body": """<p><code>--branch main</code> reads <code>GET /repos/{owner}/{repo}/rules/branches/main</code> and reports whether a <code>required_signatures</code> rule is active. No rule means the history is a coincidence. The script prints the repair as a sentence for somebody with admin to action; it does not create rulesets, and a diagnostic that could add a branch rule would be a worse thing to hold a token for than the problem it solves.</p>"""},
],
"verify": """<p>After the key is registered and the rule is switched on, the same run reports no unlinked identities and an active rule.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_commit_signatures.py acme/payments \\
    --pages 2 --branch main --author-allowlist alice@example.com,bob@example.com
# read cost: 3 REST request(s) against the core hourly quota
# 143 commit(s) read from acme/payments
# verified: 138  unsigned: 0  signature-rejected: 0  identity-not-linked: 5
#   github-could-not-check: 0  verification-absent: 0
# identity-not-linked is not a bad signature: 5 commit(s) carry a good
#   signature from a key that is not registered to any GitHub account.
# author-check-disagreement: 5 commit(s) the author allowlist passed and the
#   signature check did not. That gap is what the policy has been missing.
# enforcement: no-rule — no required_signatures rule is active on main, so the
#   verified history is a description of past behaviour and not a constraint.
# repair: ask the key owners to add their public keys to their GitHub accounts,
#   and ask an admin of acme/payments to add a ruleset requiring signed commits
#   on main. Nothing here writes: this script only reads.</code></pre>""",
"code_intro": "One live call per page of commits, plus one for the branch rules, and everything that decides anything is pure. That split matters more here than usual because the interesting commits are ones you cannot easily manufacture: a commit whose key was never registered, one GitHub failed to check, one from an endpoint that omitted the object entirely. Those are fixtures, and the classifier they feed is a table lookup with an explicit unknown branch rather than a chain of truthiness tests.",
"py_file": "github_commit_signatures.py",
"py": '''"""Report what a repository's commit signatures actually say.

Read only. One GET per page of commits and one for the branch rules. Nothing
is signed, no ruleset is created, and no commit is touched: where a rule is
missing the script prints the request for an admin to action.

The point of the note: verification.verified is one field of five, and reading
it alone throws away the difference between "nobody signed this", "somebody
signed it badly", "the signature is good and the key is not registered" and
"GitHub could not check". Those have four different repairs. A verification
object that is absent is a fifth state and it is not a false one.

What this can and cannot see: GitHub records the verification result, so this
reports what GitHub concluded at signing time, dated by verified_at. It does
not re-verify anything locally and it cannot tell you whether the signing key
is still trusted today.

Environment:

    GITHUB_TOKEN    a read-only token that can see the repository
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_commit_signatures")

API = "https://api.github.com"
UA = "github-commit-signatures/1.0"

# Every documented value of verification.reason, mapped to the family whose
# repair it shares. Written as a table rather than a chain of conditionals so
# that a reason GitHub adds later lands in "unknown-reason" and is reported,
# instead of silently taking the else branch of somebody's if.
REASONS = {
    "valid": ("verified",
              "the signature was checked and the committer identity resolved."),
    "unsigned": ("unsigned",
                 "the commit object carries no signature at all."),
    "invalid": ("signature-rejected",
                "a signature is present and did not verify against the key."),
    "malformed_signature": ("signature-rejected",
                            "the signature could not be parsed."),
    "expired_key": ("signature-rejected",
                    "the key that made the signature has expired."),
    "not_signing_key": ("signature-rejected",
                        "the key is not flagged for signing."),
    "unknown_signature_type": ("signature-rejected",
                               "the signature is not a type GitHub verifies."),
    "unknown_key": ("identity-not-linked",
                    "the key that made the signature is not registered to any "
                    "GitHub account. The cryptography is fine; the account "
                    "link is missing."),
    "no_user": ("identity-not-linked",
                "no GitHub account owns the committer email address."),
    "unverified_email": ("identity-not-linked",
                         "the committer email belongs to an account and has "
                         "not been verified on it."),
    "bad_email": ("identity-not-linked",
                  "the committer email is not among the identities on the key."),
    "gpgverify_error": ("github-could-not-check",
                        "GitHub's verification service errored. This is not a "
                        "statement about the commit."),
    "gpgverify_unavailable": ("github-could-not-check",
                              "GitHub's verification service was unavailable. "
                              "This is not a statement about the commit."),
}

# Order the tally is printed in, and the order the grade considers them.
FAMILIES = ("verified", "unsigned", "signature-rejected", "identity-not-linked",
            "github-could-not-check", "verification-absent", "unknown-reason")

# Families that are a real finding about this repository. Deliberately excludes
# github-could-not-check: an outage in GitHub's checker is somebody else's
# incident and paging on it teaches people to ignore the alert.
VIOLATIONS = ("unsigned", "signature-rejected")


def read_cost(pages, with_rules):
    """REST requests this run will spend. Pure. Printed before any are spent."""
    return max(1, int(pages)) + (1 if with_rules else 0)


def verification_of(commit):
    """Normalise one commit's verification object. Pure.

    Returns a dict with an explicit `present` flag. Every caller downstream
    branches on that flag first, so an endpoint that omits the object can never
    be read as a commit that failed verification, which is the mistake the
    whole note is about.
    """
    inner = (commit or {}).get("commit") or {}
    raw = inner.get("verification")
    if not isinstance(raw, dict):
        return {"present": False, "verified": None, "reason": None,
                "has_signature": False, "verified_at": None}
    signature = raw.get("signature")
    return {
        "present": True,
        "verified": raw.get("verified"),
        "reason": raw.get("reason"),
        "has_signature": bool(signature),
        "verified_at": raw.get("verified_at"),
    }


def family_of(verification):
    """Sort one normalised verification into its family. Pure. (family, detail).

    The boolean is checked against the reason rather than trusted on its own:
    the only reason that accompanies a true is `valid`, so a true beside any
    other reason is a shape this script does not recognise and says so.
    """
    if not verification.get("present"):
        return ("verification-absent",
                "this payload carried no verification object. That is unknown, "
                "not unsigned, and it must not be counted as either.")
    reason = verification.get("reason")
    verified = verification.get("verified")
    if reason is None:
        return ("unknown-reason",
                "the verification object has no reason field, so the boolean "
                "is the only evidence and it is not enough to act on.")
    known = REASONS.get(str(reason))
    if known is None:
        return ("unknown-reason",
                "reason %r is not one this script knows. Report it rather than "
                "letting it fall into a default." % reason)
    family, detail = known
    if family == "verified" and verified is not True:
        return ("unknown-reason",
                "reason is valid and verified is not true, which is a shape "
                "GitHub does not normally produce. Treat it as unknown.")
    if family != "verified" and verified is True:
        return ("unknown-reason",
                "verified is true beside reason %r. Only valid accompanies a "
                "true, so this pair is not readable." % reason)
    return (family, detail)


def identity_split(commit):
    """What the commit says about who wrote it. Pure. (state, detail).

    Reported alongside the signature and never instead of it. The author and
    committer strings are set by the client and are not authenticated by
    anything; the top-level author and committer objects are the GitHub
    accounts those emails resolve to, or null.
    """
    inner = (commit or {}).get("commit") or {}
    author_email = ((inner.get("author") or {}).get("email")) or ""
    committer_email = ((inner.get("committer") or {}).get("email")) or ""
    linked_author = (commit or {}).get("author")
    linked_committer = (commit or {}).get("committer")
    if not author_email and not committer_email:
        return ("no-emails",
                "the commit carries no author or committer email to compare.")
    if author_email.lower() != committer_email.lower():
        return ("author-differs-from-committer",
                "the author and the committer are different identities, and a "
                "signature speaks for the committer. A verified commit here "
                "does not assert the author consented to it.")
    if linked_author is None or linked_committer is None:
        return ("email-resolves-to-no-account",
                "an email on this commit resolves to no GitHub account, so "
                "there is no account for a signature to be matched against.")
    return ("author-is-committer",
            "author and committer are the same identity and both resolve to "
            "GitHub accounts.")


def author_allowlist_pass(commit, allowed):
    """The check people actually wrote. Pure. True, False or None.

    Kept in the script on purpose so the two policies can be run over the same
    commits and the disagreement counted. It reads commit.author.email, which
    is a string the committing client chose, and it authenticates nothing.
    """
    if not allowed:
        return None
    inner = (commit or {}).get("commit") or {}
    email = (((inner.get("author") or {}).get("email")) or "").lower()
    return email in {str(a).strip().lower() for a in allowed if str(a).strip()}


def signature_pass(commit):
    """The check the policy meant. Pure. True, False or None for unknown.

    None is a first-class answer here. A commit GitHub could not check, and a
    commit whose verification object never arrived, are both unknown, and
    collapsing either into a boolean is how a policy ends up fail-open or
    fail-noisy depending on which default somebody picked.
    """
    family, _ = family_of(verification_of(commit))
    if family == "verified":
        return True
    if family in VIOLATIONS or family == "identity-not-linked":
        return False
    return None


def disagreements(commits, allowed):
    """Where the two checks differ, commit by commit. Pure. List of dicts."""
    out = []
    for commit in commits or []:
        naive = author_allowlist_pass(commit, allowed)
        careful = signature_pass(commit)
        if naive is None or naive == careful:
            continue
        out.append({
            "sha": (commit or {}).get("sha"),
            "author_check": naive,
            "signature_check": careful,
            "gap": "author-passed-signature-did-not" if naive
                   else "signature-passed-author-did-not",
        })
    return out


def tally(commits):
    """Count the families across a list of commits. Pure. dict."""
    counts = {name: 0 for name in FAMILIES}
    for commit in commits or []:
        family, _ = family_of(verification_of(commit))
        counts[family] = counts.get(family, 0) + 1
    return counts


def enforcement_from_rules(rules, readable=True):
    """Is a signature rule actually in force on the branch. Pure. (state, detail).

    An unreadable answer is its own state. Saying "no rule" when the rules
    could not be read would tell somebody their branch is unprotected on the
    strength of a permission problem.
    """
    if not readable:
        return ("rule-unreadable",
                "the branch rules could not be read with this token, so "
                "whether signatures are enforced is unknown. That is not the "
                "same as unenforced.")
    if not isinstance(rules, list):
        return ("rule-unreadable",
                "the rules endpoint did not return a list, so nothing can be "
                "concluded about enforcement.")
    for rule in rules:
        if isinstance(rule, dict) and rule.get("type") == "required_signatures":
            return ("enforced",
                    "a required_signatures rule is active on this branch, so "
                    "an unsigned push is rejected rather than reported.")
    return ("no-rule",
            "no required_signatures rule is active on this branch. Whatever "
            "the history shows, the next push is free to be unsigned.")


def grade(counts, enforcement_state):
    """The finding, in one word. Pure. (state, detail)."""
    counts = counts or {}
    if counts.get("verification-absent"):
        return ("verification-unknown",
                "%d commit(s) arrived with no verification object. Until that "
                "is understood, no percentage from this run is trustworthy."
                % counts["verification-absent"])
    violations = sum(counts.get(name, 0) for name in VIOLATIONS)
    if violations:
        return ("unsigned-or-rejected-present",
                "%d commit(s) are unsigned or carry a signature that did not "
                "verify. This is the finding a signed-commit policy exists to "
                "produce." % violations)
    if counts.get("identity-not-linked"):
        return ("identity-not-linked-present",
                "%d commit(s) carry a good signature from a key no GitHub "
                "account claims. Nothing is cryptographically wrong; a public "
                "key needs uploading." % counts["identity-not-linked"])
    if counts.get("unknown-reason"):
        return ("unreadable-verification",
                "%d commit(s) have a verification shape this script does not "
                "recognise. Report them rather than grading them."
                % counts["unknown-reason"])
    if counts.get("github-could-not-check"):
        return ("checker-unavailable",
                "%d commit(s) could not be checked by GitHub. That is an "
                "outage, not a violation, and re-reading later is the whole "
                "response." % counts["github-could-not-check"])
    if enforcement_state == "enforced":
        return ("verified-and-enforced",
                "every commit read is verified and a rule requires it, which "
                "is the only combination that is a guarantee.")
    return ("verified-but-not-enforced",
            "every commit read is verified and nothing requires it. That is a "
            "description of past behaviour, not a constraint on the next push.")


def repair(state, enforcement_state, repo, branch):
    """The sentence a reader has to act on. Pure. Nothing here is executed."""
    lines = []
    if state == "unsigned-or-rejected-present":
        lines.append("find the commits listed as unsigned or signature-rejected "
                     "and get them re-signed or reverted")
    if state == "identity-not-linked-present":
        lines.append("ask the key owners to add their public keys to their "
                     "GitHub accounts; the signatures are already good")
    if state == "verification-unknown":
        lines.append("find out why a verification object was missing before "
                     "reporting any signing percentage from this repository")
    if state == "checker-unavailable":
        lines.append("re-read later: GitHub could not check these commits and "
                     "that is not a fact about your repository")
    if enforcement_state == "no-rule":
        lines.append("ask an admin of %s to add a ruleset requiring signed "
                     "commits on %s, so unsigned pushes are rejected rather "
                     "than reported" % (repo, branch or "the default branch"))
    if enforcement_state == "rule-unreadable":
        lines.append("re-run with a token that can read branch rules on %s, "
                     "because unreadable is not unenforced" % repo)
    if not lines:
        lines.append("nothing to repair from this reading")
    return ". ".join(lines) + ". Nothing here writes."


def get(session, path):
    """One GET. Returns the response object."""
    response = session.get(API + path, timeout=30)
    if response.status_code == 401:
        log.warning("401 on %s: the credential was not accepted, which is a "
                    "different note", path)
    return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", help="owner/name")
    parser.add_argument("--ref", help="branch, tag or sha to walk from")
    parser.add_argument("--pages", type=int, default=1,
                        help="pages of 100 commits to read, default 1")
    parser.add_argument("--branch",
                        help="read the rules in force on this branch")
    parser.add_argument("--author-allowlist", default="",
                        help="comma-separated author emails, to run the naive "
                             "check beside the real one")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    log.info("read cost: %d REST request(s) against the core hourly quota",
             read_cost(args.pages, bool(args.branch)))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub refuses requests with no User-Agent before it looks at auth.
        "User-Agent": UA,
    })

    commits = []
    for page in range(1, max(1, args.pages) + 1):
        path = "/repos/%s/commits?per_page=100&page=%d" % (args.repo, page)
        if args.ref:
            path += "&sha=" + args.ref
        response = get(session, path)
        if response.status_code != 200:
            log.error("GET %s -> HTTP %s; stopping", path, response.status_code)
            break
        batch = response.json()
        if not isinstance(batch, list) or not batch:
            break
        commits.extend(batch)
    log.info("%d commit(s) read from %s", len(commits), args.repo)

    counts = tally(commits)
    log.info("verified: %d  unsigned: %d  signature-rejected: %d  "
             "identity-not-linked: %d  github-could-not-check: %d  "
             "verification-absent: %d",
             counts["verified"], counts["unsigned"], counts["signature-rejected"],
             counts["identity-not-linked"], counts["github-could-not-check"],
             counts["verification-absent"])

    allowed = [part for part in args.author_allowlist.split(",") if part.strip()]
    gaps = disagreements(commits, allowed)
    if allowed:
        missed = [g for g in gaps if g["gap"] == "author-passed-signature-did-not"]
        log.info("author-check-disagreement: %d commit(s) the author allowlist "
                 "passed and the signature check did not", len(missed))

    splits = {}
    for commit in commits:
        state, _ = identity_split(commit)
        splits[state] = splits.get(state, 0) + 1
    log.info("identity: %s", splits)

    rules, readable = None, False
    if args.branch:
        path = "/repos/%s/rules/branches/%s" % (args.repo, args.branch)
        response = get(session, path)
        readable = response.status_code == 200
        rules = response.json() if readable else None
    enforcement_state, enforcement_detail = enforcement_from_rules(
        rules, readable if args.branch else False)
    if args.branch:
        log.info("enforcement: %s. %s", enforcement_state, enforcement_detail)

    state, detail = grade(counts, enforcement_state)
    log.info("%s: %s", state, detail)
    fix = repair(state, enforcement_state if args.branch else "not-read",
                 args.repo, args.branch)
    log.info("repair: %s", fix)

    print(json.dumps({
        "repository": args.repo,
        "commits_read": len(commits),
        "counts": counts,
        "identity_split": splits,
        "disagreements": gaps[:20],
        "disagreement_count": len(gaps),
        "enforcement_state": enforcement_state if args.branch else "not-read",
        "state": state,
        "detail": detail,
        "repair": fix,
    }, indent=2, default=str))
    return 1 if state in ("unsigned-or-rejected-present", "verification-unknown",
                          "identity-not-linked-present",
                          "verified-but-not-enforced") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-commit-signatures.mjs",
"js": '''/**
 * Report what a repository's commit signatures actually say.
 *
 * Read only. One GET per page of commits and one for the branch rules.
 * Nothing is signed and no ruleset is created: where a rule is missing the
 * script prints the request for an admin to action.
 *
 * verification.verified is one field of five. Reading it alone throws away the
 * difference between unsigned, badly signed, well signed by an unregistered
 * key, and not checked at all. A missing verification object is a fifth state
 * and it is not a false one.
 *
 * Environment:
 *   GITHUB_TOKEN      a read-only token that can see the repository
 *   GITHUB_REPO       owner/name
 *   GITHUB_REF        optional branch, tag or sha to walk from
 *   GITHUB_PAGES      optional pages of 100 commits, default 1
 *   GITHUB_BRANCH     optional branch whose rules to read
 *   GITHUB_AUTHORS    optional comma-separated author allowlist
 */
const API = 'https://api.github.com';
const UA = 'github-commit-signatures/1.0';

/** Every documented reason, mapped to the family whose repair it shares. */
export const REASONS = {
  valid: ['verified', 'the signature was checked and the committer identity resolved.'],
  unsigned: ['unsigned', 'the commit object carries no signature at all.'],
  invalid: ['signature-rejected', 'a signature is present and did not verify against the key.'],
  malformed_signature: ['signature-rejected', 'the signature could not be parsed.'],
  expired_key: ['signature-rejected', 'the key that made the signature has expired.'],
  not_signing_key: ['signature-rejected', 'the key is not flagged for signing.'],
  unknown_signature_type: ['signature-rejected', 'the signature is not a type GitHub verifies.'],
  unknown_key: ['identity-not-linked', 'the key that made the signature is not '
    + 'registered to any GitHub account. The cryptography is fine; the account '
    + 'link is missing.'],
  no_user: ['identity-not-linked', 'no GitHub account owns the committer email address.'],
  unverified_email: ['identity-not-linked', 'the committer email belongs to an '
    + 'account and has not been verified on it.'],
  bad_email: ['identity-not-linked', 'the committer email is not among the '
    + 'identities on the key.'],
  gpgverify_error: ['github-could-not-check', "GitHub's verification service "
    + 'errored. This is not a statement about the commit.'],
  gpgverify_unavailable: ['github-could-not-check', "GitHub's verification "
    + 'service was unavailable. This is not a statement about the commit.'],
};

export const FAMILIES = ['verified', 'unsigned', 'signature-rejected',
  'identity-not-linked', 'github-could-not-check', 'verification-absent',
  'unknown-reason'];

/** Families that are a finding about this repository. Excludes the outage one. */
export const VIOLATIONS = ['unsigned', 'signature-rejected'];

/** REST requests this run will spend. Pure. */
export function readCost(pages, withRules) {
  return Math.max(1, Number(pages) || 1) + (withRules ? 1 : 0);
}

/** Normalise one commit's verification object. Pure. */
export function verificationOf(commit) {
  const inner = (commit && commit.commit) || {};
  const raw = inner.verification;
  if (!raw || typeof raw !== 'object') {
    return { present: false, verified: null, reason: null, hasSignature: false, verifiedAt: null };
  }
  return {
    present: true,
    verified: raw.verified,
    reason: raw.reason,
    hasSignature: Boolean(raw.signature),
    verifiedAt: raw.verified_at ?? null,
  };
}

/** Sort one normalised verification into its family. Pure. [family, detail]. */
export function familyOf(verification) {
  if (!verification || !verification.present) {
    return ['verification-absent', 'this payload carried no verification '
      + 'object. That is unknown, not unsigned, and it must not be counted as '
      + 'either.'];
  }
  const { reason, verified } = verification;
  if (reason === null || reason === undefined) {
    return ['unknown-reason', 'the verification object has no reason field, so '
      + 'the boolean is the only evidence and it is not enough to act on.'];
  }
  const known = REASONS[String(reason)];
  if (!known) {
    return ['unknown-reason', `reason ${JSON.stringify(reason)} is not one this `
      + 'script knows. Report it rather than letting it fall into a default.'];
  }
  const [family, detail] = known;
  if (family === 'verified' && verified !== true) {
    return ['unknown-reason', 'reason is valid and verified is not true, which '
      + 'is a shape GitHub does not normally produce. Treat it as unknown.'];
  }
  if (family !== 'verified' && verified === true) {
    return ['unknown-reason', `verified is true beside reason `
      + `${JSON.stringify(reason)}. Only valid accompanies a true, so this pair `
      + 'is not readable.'];
  }
  return [family, detail];
}

/** What the commit says about who wrote it. Pure. [state, detail]. */
export function identitySplit(commit) {
  const inner = (commit && commit.commit) || {};
  const authorEmail = ((inner.author && inner.author.email) || '');
  const committerEmail = ((inner.committer && inner.committer.email) || '');
  const linkedAuthor = commit ? commit.author : null;
  const linkedCommitter = commit ? commit.committer : null;
  if (!authorEmail && !committerEmail) {
    return ['no-emails', 'the commit carries no author or committer email to compare.'];
  }
  if (authorEmail.toLowerCase() !== committerEmail.toLowerCase()) {
    return ['author-differs-from-committer', 'the author and the committer are '
      + 'different identities, and a signature speaks for the committer. A '
      + 'verified commit here does not assert the author consented to it.'];
  }
  if (!linkedAuthor || !linkedCommitter) {
    return ['email-resolves-to-no-account', 'an email on this commit resolves '
      + 'to no GitHub account, so there is no account for a signature to be '
      + 'matched against.'];
  }
  return ['author-is-committer', 'author and committer are the same identity '
    + 'and both resolve to GitHub accounts.'];
}

/** The check people actually wrote. Pure. true, false or null. */
export function authorAllowlistPass(commit, allowed) {
  if (!allowed || allowed.length === 0) return null;
  const inner = (commit && commit.commit) || {};
  const email = (((inner.author && inner.author.email) || '')).toLowerCase();
  const set = new Set(allowed.map((a) => String(a).trim().toLowerCase()).filter(Boolean));
  return set.has(email);
}

/** The check the policy meant. Pure. true, false or null for unknown. */
export function signaturePass(commit) {
  const [family] = familyOf(verificationOf(commit));
  if (family === 'verified') return true;
  if (VIOLATIONS.includes(family) || family === 'identity-not-linked') return false;
  return null;
}

/** Where the two checks differ, commit by commit. Pure. */
export function disagreements(commits, allowed) {
  const out = [];
  for (const commit of commits || []) {
    const naive = authorAllowlistPass(commit, allowed);
    const careful = signaturePass(commit);
    if (naive === null || naive === careful) continue;
    out.push({
      sha: commit ? commit.sha : null,
      author_check: naive,
      signature_check: careful,
      gap: naive ? 'author-passed-signature-did-not' : 'signature-passed-author-did-not',
    });
  }
  return out;
}

/** Count the families across a list of commits. Pure. */
export function tally(commits) {
  const counts = {};
  for (const name of FAMILIES) counts[name] = 0;
  for (const commit of commits || []) {
    const [family] = familyOf(verificationOf(commit));
    counts[family] = (counts[family] || 0) + 1;
  }
  return counts;
}

/** Is a signature rule actually in force on the branch. Pure. [state, detail]. */
export function enforcementFromRules(rules, readable = true) {
  if (!readable) {
    return ['rule-unreadable', 'the branch rules could not be read with this '
      + 'token, so whether signatures are enforced is unknown. That is not the '
      + 'same as unenforced.'];
  }
  if (!Array.isArray(rules)) {
    return ['rule-unreadable', 'the rules endpoint did not return a list, so '
      + 'nothing can be concluded about enforcement.'];
  }
  for (const rule of rules) {
    if (rule && rule.type === 'required_signatures') {
      return ['enforced', 'a required_signatures rule is active on this branch, '
        + 'so an unsigned push is rejected rather than reported.'];
    }
  }
  return ['no-rule', 'no required_signatures rule is active on this branch. '
    + 'Whatever the history shows, the next push is free to be unsigned.'];
}

/** The finding, in one word. Pure. [state, detail]. */
export function grade(counts, enforcementState) {
  const c = counts || {};
  if (c['verification-absent']) {
    return ['verification-unknown', `${c['verification-absent']} commit(s) `
      + 'arrived with no verification object. Until that is understood, no '
      + 'percentage from this run is trustworthy.'];
  }
  const violations = VIOLATIONS.reduce((n, k) => n + (c[k] || 0), 0);
  if (violations) {
    return ['unsigned-or-rejected-present', `${violations} commit(s) are `
      + 'unsigned or carry a signature that did not verify. This is the finding '
      + 'a signed-commit policy exists to produce.'];
  }
  if (c['identity-not-linked']) {
    return ['identity-not-linked-present', `${c['identity-not-linked']} commit(s) `
      + 'carry a good signature from a key no GitHub account claims. Nothing is '
      + 'cryptographically wrong; a public key needs uploading.'];
  }
  if (c['unknown-reason']) {
    return ['unreadable-verification', `${c['unknown-reason']} commit(s) have a `
      + 'verification shape this script does not recognise. Report them rather '
      + 'than grading them.'];
  }
  if (c['github-could-not-check']) {
    return ['checker-unavailable', `${c['github-could-not-check']} commit(s) `
      + 'could not be checked by GitHub. That is an outage, not a violation, '
      + 'and re-reading later is the whole response.'];
  }
  if (enforcementState === 'enforced') {
    return ['verified-and-enforced', 'every commit read is verified and a rule '
      + 'requires it, which is the only combination that is a guarantee.'];
  }
  return ['verified-but-not-enforced', 'every commit read is verified and '
    + 'nothing requires it. That is a description of past behaviour, not a '
    + 'constraint on the next push.'];
}

/** The sentence a reader has to act on. Pure. Nothing here is executed. */
export function repair(state, enforcementState, repo, branch) {
  const lines = [];
  if (state === 'unsigned-or-rejected-present') {
    lines.push('find the commits listed as unsigned or signature-rejected and '
      + 'get them re-signed or reverted');
  }
  if (state === 'identity-not-linked-present') {
    lines.push('ask the key owners to add their public keys to their GitHub '
      + 'accounts; the signatures are already good');
  }
  if (state === 'verification-unknown') {
    lines.push('find out why a verification object was missing before reporting '
      + 'any signing percentage from this repository');
  }
  if (state === 'checker-unavailable') {
    lines.push('re-read later: GitHub could not check these commits and that is '
      + 'not a fact about your repository');
  }
  if (enforcementState === 'no-rule') {
    lines.push(`ask an admin of ${repo} to add a ruleset requiring signed `
      + `commits on ${branch || 'the default branch'}, so unsigned pushes are `
      + 'rejected rather than reported');
  }
  if (enforcementState === 'rule-unreadable') {
    lines.push(`re-run with a token that can read branch rules on ${repo}, `
      + 'because unreadable is not unenforced');
  }
  if (lines.length === 0) lines.push('nothing to repair from this reading');
  return `${lines.join('. ')}. Nothing here writes.`;
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
  const repo = process.env.GITHUB_REPO;
  if (!token || !repo) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPO');
    process.exitCode = 2;
    return;
  }
  const pages = Number(process.env.GITHUB_PAGES || '1') || 1;
  const branch = process.env.GITHUB_BRANCH || '';
  const ref = process.env.GITHUB_REF || '';
  const allowed = (process.env.GITHUB_AUTHORS || '').split(',')
    .map((s) => s.trim()).filter(Boolean);
  console.log(`read cost: ${readCost(pages, Boolean(branch))} REST request(s) `
    + 'against the core hourly quota');

  const commits = [];
  for (let page = 1; page <= Math.max(1, pages); page += 1) {
    let path = `/repos/${repo}/commits?per_page=100&page=${page}`;
    if (ref) path += `&sha=${ref}`;
    const response = await fetch(`${API}${path}`, { headers: headers(token) });
    if (response.status !== 200) {
      console.error(`GET ${path} -> HTTP ${response.status}; stopping`);
      break;
    }
    const batch = await response.json();
    if (!Array.isArray(batch) || batch.length === 0) break;
    commits.push(...batch);
  }
  console.log(`${commits.length} commit(s) read from ${repo}`);

  const counts = tally(commits);
  console.log(`verified: ${counts.verified}  unsigned: ${counts.unsigned}  `
    + `signature-rejected: ${counts['signature-rejected']}  `
    + `identity-not-linked: ${counts['identity-not-linked']}  `
    + `github-could-not-check: ${counts['github-could-not-check']}  `
    + `verification-absent: ${counts['verification-absent']}`);

  const gaps = disagreements(commits, allowed);
  if (allowed.length) {
    const missed = gaps.filter((g) => g.gap === 'author-passed-signature-did-not');
    console.log(`author-check-disagreement: ${missed.length} commit(s) the `
      + 'author allowlist passed and the signature check did not');
  }

  const splits = {};
  for (const commit of commits) {
    const [state] = identitySplit(commit);
    splits[state] = (splits[state] || 0) + 1;
  }
  console.log(`identity: ${JSON.stringify(splits)}`);

  let rules = null;
  let readable = false;
  if (branch) {
    const response = await fetch(`${API}/repos/${repo}/rules/branches/${branch}`,
      { headers: headers(token) });
    readable = response.status === 200;
    rules = readable ? await response.json() : null;
  }
  const [enforcementState, enforcementDetail] = enforcementFromRules(
    rules, branch ? readable : false,
  );
  if (branch) console.log(`enforcement: ${enforcementState}. ${enforcementDetail}`);

  const [state, detail] = grade(counts, enforcementState);
  console.log(`${state}: ${detail}`);
  const fix = repair(state, branch ? enforcementState : 'not-read', repo, branch);
  console.log(`repair: ${fix}`);

  console.log(JSON.stringify({
    repository: repo,
    commits_read: commits.length,
    counts,
    identity_split: splits,
    disagreements: gaps.slice(0, 20),
    disagreement_count: gaps.length,
    enforcement_state: branch ? enforcementState : 'not-read',
    state,
    detail,
    repair: fix,
  }, null, 2));
  process.exitCode = ['unsigned-or-rejected-present', 'verification-unknown',
    'identity-not-linked-present', 'verified-but-not-enforced'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are commits, because the commits worth handling are the ones you cannot easily make: one signed with a key nobody registered, one GitHub failed to check, one from an endpoint that omitted the verification object. The first group asserts that every documented reason lands in a family and that an undocumented one is reported rather than defaulted. The second is the note's headline: the naive author check and the signature check are run over the same list and the disagreement is counted in both directions. The last group protects the two states that must never collapse into a boolean, absent and could-not-check.",
"test_py_file": "test_github_commit_signatures.py",
"test_py": '''from github_commit_signatures import (
    FAMILIES, REASONS, VIOLATIONS, author_allowlist_pass, disagreements,
    enforcement_from_rules, family_of, grade, identity_split, read_cost,
    repair, signature_pass, tally, verification_of,
)


def commit(sha, reason=None, verified=None, present=True, signature="-----BEGIN-----",
           author="alice@example.com", committer=None, linked=True):
    inner = {
        "author": {"email": author, "name": "Alice"},
        "committer": {"email": committer or author, "name": "Alice"},
    }
    if present:
        inner["verification"] = {"verified": verified, "reason": reason,
                                 "signature": signature, "payload": "tree 1",
                                 "verified_at": "2026-01-01T00:00:00Z"}
    return {"sha": sha, "commit": inner,
            "author": {"login": "alice"} if linked else None,
            "committer": {"login": "alice"} if linked else None}


SIGNED = commit("aaa", "valid", True)
UNSIGNED = commit("bbb", "unsigned", False, signature=None)
BAD = commit("ccc", "invalid", False)
UNREGISTERED = commit("ddd", "unknown_key", False)
OUTAGE = commit("eee", "gpgverify_unavailable", False)
ABSENT = commit("fff", present=False)


def test_every_documented_reason_has_a_family_and_a_sentence():
    for reason, (family, detail) in REASONS.items():
        assert family in FAMILIES, reason
        assert detail.endswith("."), reason
    assert REASONS["valid"][0] == "verified"


def test_the_four_kinds_of_false_are_four_different_findings():
    assert family_of(verification_of(UNSIGNED))[0] == "unsigned"
    assert family_of(verification_of(BAD))[0] == "signature-rejected"
    assert family_of(verification_of(UNREGISTERED))[0] == "identity-not-linked"
    assert family_of(verification_of(OUTAGE))[0] == "github-could-not-check"
    # And the one that matters most: a good signature nobody registered is not
    # a bad signature, and the sentence says so.
    assert "cryptography is fine" in family_of(verification_of(UNREGISTERED))[1]


def test_a_missing_verification_object_is_unknown_and_not_false():
    normalised = verification_of(ABSENT)
    assert normalised["present"] is False
    assert normalised["verified"] is None
    family, detail = family_of(normalised)
    assert family == "verification-absent"
    assert "not unsigned" in detail
    assert signature_pass(ABSENT) is None


def test_an_outage_is_unknown_rather_than_a_violation():
    assert signature_pass(OUTAGE) is None
    assert "github-could-not-check" not in VIOLATIONS
    state, detail = grade(tally([SIGNED, OUTAGE]), "no-rule")
    assert state == "checker-unavailable"
    assert "not a violation" in detail


def test_a_reason_github_adds_later_is_reported_not_defaulted():
    future = commit("ggg", "quantum_key_rotated", False)
    family, detail = family_of(verification_of(future))
    assert family == "unknown-reason"
    assert "rather than letting it fall into a default" in detail


def test_verified_true_beside_the_wrong_reason_is_not_believed():
    weird = commit("hhh", "unsigned", True)
    assert family_of(verification_of(weird))[0] == "unknown-reason"
    inverted = commit("iii", "valid", False)
    assert family_of(verification_of(inverted))[0] == "unknown-reason"


def test_the_author_check_and_the_signature_check_disagree_in_both_directions():
    allowed = ["alice@example.com"]
    # Author on the list, unsigned: the gap the policy has been missing.
    missed = disagreements([UNSIGNED], allowed)
    assert missed[0]["gap"] == "author-passed-signature-did-not"
    # Signed by somebody not on the roster: falsely flagged by the old check.
    outsider = commit("jjj", "valid", True, author="carol@example.com")
    flagged = disagreements([outsider], allowed)
    assert flagged[0]["gap"] == "signature-passed-author-did-not"
    # And where the two agree there is nothing to report.
    assert disagreements([SIGNED], allowed) == []


def test_the_author_check_authenticates_nothing():
    # The whole point: an unsigned commit claiming an approved author sails
    # through the check most people wrote.
    forged = commit("kkk", "unsigned", False, signature=None,
                    author="alice@example.com")
    assert author_allowlist_pass(forged, ["alice@example.com"]) is True
    assert signature_pass(forged) is False
    assert author_allowlist_pass(forged, []) is None


def test_the_signature_speaks_for_the_committer_not_the_author():
    split = commit("lll", "valid", True, author="alice@example.com",
                   committer="bob@example.com")
    state, detail = identity_split(split)
    assert state == "author-differs-from-committer"
    assert "speaks for the committer" in detail
    assert identity_split(SIGNED)[0] == "author-is-committer"
    unlinked = commit("mmm", "valid", True, linked=False)
    assert identity_split(unlinked)[0] == "email-resolves-to-no-account"


def test_an_unreadable_rule_is_not_an_absent_rule():
    state, detail = enforcement_from_rules(None, readable=False)
    assert state == "rule-unreadable"
    assert "not the same as unenforced" in detail
    assert enforcement_from_rules([], readable=True)[0] == "no-rule"
    rules = [{"type": "deletion"}, {"type": "required_signatures"}]
    assert enforcement_from_rules(rules, readable=True)[0] == "enforced"


def test_a_verified_history_with_no_rule_is_not_a_guarantee():
    counts = tally([SIGNED, SIGNED])
    assert grade(counts, "no-rule")[0] == "verified-but-not-enforced"
    assert grade(counts, "enforced")[0] == "verified-and-enforced"
    assert "not a constraint" in grade(counts, "no-rule")[1]


def test_absent_verification_outranks_every_other_grade():
    # A run that could not see the field is not a run that found violations.
    counts = tally([UNSIGNED, ABSENT])
    assert grade(counts, "enforced")[0] == "verification-unknown"


def test_the_tally_covers_every_family():
    counts = tally([SIGNED, UNSIGNED, BAD, UNREGISTERED, OUTAGE, ABSENT])
    assert set(counts) >= set(FAMILIES)
    assert counts["verified"] == 1 and counts["unsigned"] == 1
    assert counts["verification-absent"] == 1
    assert tally([]) == {name: 0 for name in FAMILIES}


def test_the_repair_asks_a_human_and_writes_nothing():
    fix = repair("identity-not-linked-present", "no-rule", "acme/payments", "main")
    assert "add their public keys" in fix
    assert "ask an admin of acme/payments" in fix
    assert fix.endswith("Nothing here writes.")
    assert "unreadable is not unenforced" in repair(
        "verified-and-enforced", "rule-unreadable", "acme/payments", "main")


def test_the_read_cost_is_known_before_anything_is_spent():
    assert read_cost(1, False) == 1
    assert read_cost(3, True) == 4
    assert read_cost(0, False) == 1
''',
"test_js_file": "github-commit-signatures.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  FAMILIES, REASONS, VIOLATIONS, authorAllowlistPass, disagreements,
  enforcementFromRules, familyOf, grade, identitySplit, readCost, repair,
  signaturePass, tally, verificationOf,
} from './github-commit-signatures.mjs';

function commit(sha, reason = null, verified = null, opts = {}) {
  const author = opts.author || 'alice@example.com';
  const inner = {
    author: { email: author, name: 'Alice' },
    committer: { email: opts.committer || author, name: 'Alice' },
  };
  if (opts.present !== false) {
    inner.verification = {
      verified, reason, signature: opts.signature ?? '-----BEGIN-----',
      payload: 'tree 1', verified_at: '2026-01-01T00:00:00Z',
    };
  }
  const linked = opts.linked === false ? null : { login: 'alice' };
  return { sha, commit: inner, author: linked, committer: linked };
}

const SIGNED = commit('aaa', 'valid', true);
const UNSIGNED = commit('bbb', 'unsigned', false, { signature: null });
const BAD = commit('ccc', 'invalid', false);
const UNREGISTERED = commit('ddd', 'unknown_key', false);
const OUTAGE = commit('eee', 'gpgverify_unavailable', false);
const ABSENT = commit('fff', null, null, { present: false });

test('every documented reason has a family and a sentence', () => {
  for (const [reason, [family, detail]] of Object.entries(REASONS)) {
    assert.ok(FAMILIES.includes(family), reason);
    assert.ok(detail.endsWith('.'), reason);
  }
  assert.equal(REASONS.valid[0], 'verified');
});

test('the four kinds of false are four different findings', () => {
  assert.equal(familyOf(verificationOf(UNSIGNED))[0], 'unsigned');
  assert.equal(familyOf(verificationOf(BAD))[0], 'signature-rejected');
  assert.equal(familyOf(verificationOf(UNREGISTERED))[0], 'identity-not-linked');
  assert.equal(familyOf(verificationOf(OUTAGE))[0], 'github-could-not-check');
  assert.match(familyOf(verificationOf(UNREGISTERED))[1], /cryptography is fine/);
});

test('a missing verification object is unknown and not false', () => {
  const normalised = verificationOf(ABSENT);
  assert.equal(normalised.present, false);
  assert.equal(normalised.verified, null);
  const [family, detail] = familyOf(normalised);
  assert.equal(family, 'verification-absent');
  assert.match(detail, /not unsigned/);
  assert.equal(signaturePass(ABSENT), null);
});

test('an outage is unknown rather than a violation', () => {
  assert.equal(signaturePass(OUTAGE), null);
  assert.ok(!VIOLATIONS.includes('github-could-not-check'));
  const [state, detail] = grade(tally([SIGNED, OUTAGE]), 'no-rule');
  assert.equal(state, 'checker-unavailable');
  assert.match(detail, /not a violation/);
});

test('a reason GitHub adds later is reported not defaulted', () => {
  const future = commit('ggg', 'quantum_key_rotated', false);
  const [family, detail] = familyOf(verificationOf(future));
  assert.equal(family, 'unknown-reason');
  assert.match(detail, /rather than letting it fall into a default/);
});

test('verified true beside the wrong reason is not believed', () => {
  assert.equal(familyOf(verificationOf(commit('hhh', 'unsigned', true)))[0], 'unknown-reason');
  assert.equal(familyOf(verificationOf(commit('iii', 'valid', false)))[0], 'unknown-reason');
});

test('the author check and the signature check disagree in both directions', () => {
  const allowed = ['alice@example.com'];
  assert.equal(disagreements([UNSIGNED], allowed)[0].gap, 'author-passed-signature-did-not');
  const outsider = commit('jjj', 'valid', true, { author: 'carol@example.com' });
  assert.equal(disagreements([outsider], allowed)[0].gap, 'signature-passed-author-did-not');
  assert.deepEqual(disagreements([SIGNED], allowed), []);
});

test('the author check authenticates nothing', () => {
  const forged = commit('kkk', 'unsigned', false, { signature: null });
  assert.equal(authorAllowlistPass(forged, ['alice@example.com']), true);
  assert.equal(signaturePass(forged), false);
  assert.equal(authorAllowlistPass(forged, []), null);
});

test('the signature speaks for the committer not the author', () => {
  const split = commit('lll', 'valid', true, { committer: 'bob@example.com' });
  const [state, detail] = identitySplit(split);
  assert.equal(state, 'author-differs-from-committer');
  assert.match(detail, /speaks for the committer/);
  assert.equal(identitySplit(SIGNED)[0], 'author-is-committer');
  const unlinked = commit('mmm', 'valid', true, { linked: false });
  assert.equal(identitySplit(unlinked)[0], 'email-resolves-to-no-account');
});

test('an unreadable rule is not an absent rule', () => {
  const [state, detail] = enforcementFromRules(null, false);
  assert.equal(state, 'rule-unreadable');
  assert.match(detail, /not the same as unenforced/);
  assert.equal(enforcementFromRules([], true)[0], 'no-rule');
  assert.equal(
    enforcementFromRules([{ type: 'deletion' }, { type: 'required_signatures' }], true)[0],
    'enforced',
  );
});

test('a verified history with no rule is not a guarantee', () => {
  const counts = tally([SIGNED, SIGNED]);
  assert.equal(grade(counts, 'no-rule')[0], 'verified-but-not-enforced');
  assert.equal(grade(counts, 'enforced')[0], 'verified-and-enforced');
  assert.match(grade(counts, 'no-rule')[1], /not a constraint/);
});

test('absent verification outranks every other grade', () => {
  assert.equal(grade(tally([UNSIGNED, ABSENT]), 'enforced')[0], 'verification-unknown');
});

test('the tally covers every family', () => {
  const counts = tally([SIGNED, UNSIGNED, BAD, UNREGISTERED, OUTAGE, ABSENT]);
  for (const name of FAMILIES) assert.ok(name in counts);
  assert.equal(counts.verified, 1);
  assert.equal(counts['verification-absent'], 1);
});

test('the repair asks a human and writes nothing', () => {
  const fix = repair('identity-not-linked-present', 'no-rule', 'acme/payments', 'main');
  assert.match(fix, /add their public keys/);
  assert.match(fix, /ask an admin of acme\\/payments/);
  assert.ok(fix.endsWith('Nothing here writes.'));
  assert.match(
    repair('verified-and-enforced', 'rule-unreadable', 'acme/payments', 'main'),
    /unreadable is not unenforced/,
  );
});

test('the read cost is known before anything is spent', () => {
  assert.equal(readCost(1, false), 1);
  assert.equal(readCost(3, true), 4);
  assert.equal(readCost(0, false), 1);
});
''',
"faq": [
 ("Does <code>verified: true</code> mean the person named on the commit wrote it?",
  "No. It means a signature on the commit object was cryptographically checked against a key registered to a GitHub account, and that the <em>committer</em> email matched a verified email on that account. The <code>author</code> fields are separate strings the committing client set, and nothing authenticates them. A commit can be genuinely verified and still carry any author name at all, which is exactly why an audit that reads the author is checking something else."),
 ("Our script defaults <code>verified</code> to <code>False</code> when the key is missing. Is that safe?",
  "It is safe against fail-open and it produces a different bug. A commit GitHub could not check &mdash; <code>gpgverify_error</code> or <code>gpgverify_unavailable</code> &mdash; is not an unsigned commit, and grading it as one turns an incident on GitHub's side into a blocked release on yours. The honest third value is unknown, which is why the script returns <code>None</code> rather than a boolean and why the tally keeps that family out of the violation count."),
 ("What is the difference between <code>unknown_key</code> and <code>invalid</code>?",
  "Everything, in terms of what to do next. <code>invalid</code> means a signature exists and does not check out against the key, which is a real problem. <code>unknown_key</code> means the signature is perfectly good and the key that made it has never been uploaded to a GitHub account, so GitHub has nothing to check it against. The second is nearly always somebody who set up signing locally and skipped the last step, and the repair is that person adding a public key rather than anything touching the repository."),
 ("Why does a commit stay verified after the signing key is revoked?",
  "Because GitHub records the verification result rather than recomputing it on every read, and documents that signatures stay verified over time even when keys are rotated or revoked and when contributors leave. That is what you want for history &mdash; the alternative is a repository whose past silently changes status &mdash; but it means <code>verified</code> is a statement about the moment of signing, dated by <code>verified_at</code>, and not a claim about today's trust in that key."),
 ("The report says every commit is signed. Is the policy satisfied?",
  "Only if something is enforcing it. A report describes commits that already exist; a <code>required_signatures</code> rule on the branch is what causes an unsigned push to be rejected. Read <code>GET /repos/{owner}/{repo}/rules/branches/{branch}</code> and look for that rule type. If it is not there, your history is signed because everybody happened to have signing configured, and the guarantee lasts exactly until somebody clones on a new laptop."),
],
"related": [
 ("/github/branch-protection-requires-admin/", "Reading the rule that is supposed to enforce it"),
 ("/github/compare-250-commit-cap/", "The other place a commit list quietly stops short"),
 ("/github/wrong-identity-token/", "Asking a credential who it actually is"),
],
"citations": [CITE_COMMITS, CITE_SIGNATURE_VERIFICATION, CITE_RULES, CITE_RULESETS_ABOUT],
},
{
"slug": "missing-endpoint-404-vs-405",
"title": "GitHub answers 404 for the wrong verb, never 405",
"description": "The path is right and the method is not. The documentation_url in the 404 body separates a route that is not there from one that refuses your verb.",
"h1": "GitHub answers 404 for the wrong verb, never 405",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api 404 method not allowed",
             "github rest api wrong http method 404",
             "github api 405 method not allowed missing",
             "github api documentation_url not found body",
             "github rest api trailing slash 404"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The path was copied out of the documentation. It is on the page, in a code block, with the owner and the repository substituted in correctly, and it comes back <code>404 Not Found</code>. So the search starts where every 404 search starts: is the repository private, is the token scoped, is the App installed. All of those come back fine, which is confusing, and somebody eventually widens the token to something alarming just to see. Still 404. The path was never the problem and neither was the credential. The endpoint does not accept the method that was sent, and GitHub has documented that it will tell you so with a 404 rather than a 405.",
"short_answer": """<p>GitHub's own troubleshooting page states it plainly: send a request with an HTTP method the endpoint does not support and you get <code>404 Not Found</code> rather than <code>405 Method Not Allowed</code>. So a route that does not exist, a route that exists and refuses your verb, and a resource you are not allowed to see all arrive as the same status code.</p>
<p>One field in the body separates the first two. GitHub's error body carries a <code>documentation_url</code>, and it is not always the same one. When the request matched a route and the <em>resource</em> was missing or hidden, the URL names that endpoint — <code>https://docs.github.com/rest/repos/repos#get-a-repository</code>. When nothing matched the path and method at all, it degrades to the bare <code>https://docs.github.com/rest</code>. A specific URL means the route was found and your problem is access or existence. A bare one means nothing was routed, and the two candidates are a wrong path shape and a wrong verb.</p>
<p>Do not establish this by sending the write verb to see what happens. That is a write, and GitHub answers 404 for an unsupported verb anyway, so the reading you paid for tells you nothing you did not already have.</p>""",
"problem": """<p>Every instinct here points at permissions, because 404 is what a permission failure looks like on this API. GitHub returns 404 instead of 403 on private resources so that a stranger cannot enumerate what exists. That behaviour has its own note, it is correct, and it is why an hour disappears into scopes and installations before anybody re-reads the verb on the line above the URL.</p>
<p>The second reason it hides is that the failing request usually lives in a client library, and the verb is not visible at the call site. <code>client.repos.addCollaborator(...)</code> does not show you whether it sends a PUT or a POST. Neither does a hand-rolled helper whose default is POST because most of the API is POST. The path in the error message is right, the code that produced it is one line, and the wrong half of that line is not printed anywhere.</p>
<p>Then there is the version people reach for, which is worse than the bug. Somebody decides to settle it by sending the request with different verbs until one answers, and on this API several of the interesting ones are idempotent set operations: a PUT to <code>/user/starred/{owner}/{repo}</code> stars the repository, a PUT to <code>/repos/{owner}/{repo}/collaborators/{username}</code> sends somebody an invitation. The probe is not a probe. It is the operation, performed on a production account, to answer a question the documentation already answers.</p>""",
"why": """<p><strong>The 404 for a wrong verb is documented behaviour.</strong> This is not a quirk somebody discovered; it is written down: "If you send a request with an HTTP method that the endpoint does not support, you will receive a <code>404 Not Found</code> response instead of <code>405 Method Not Allowed</code>." The same page lists the other producers of a 404 on this API — an unauthenticated request for a private resource, a URL with a typo, a trailing slash, and a path parameter that was not URL-encoded properly. Five causes, one status.</p>
<p><strong><code>documentation_url</code> is the discriminator, and almost nobody reads it.</strong> A 404 whose body points at a specific endpoint's documentation is a 404 <em>from</em> that endpoint: the router matched, the handler ran, and it did not find the resource or would not show it to you. A 404 whose body points at the bare REST index never reached a handler. That distinction is exactly the line between this note and the permissions one, and it costs nothing to read because it is already in the response you have.</p>
<p><strong>A trailing slash is a different path.</strong> <code>/repos/{owner}/{repo}</code> answers and <code>/repos/{owner}/{repo}/</code> does not, because the second one does not match the route. It is the single most common shape error and it survives review because the two strings look identical in a diff. The same goes for a path parameter containing an unencoded slash, which silently adds a segment and turns your request into a call to a route that was never defined.</p>
<p><strong>A GET probe is evidence only where the route has a GET.</strong> This is the honest limit of the method. If <code>GET /repos/{owner}/{repo}/topics</code> answers 200, the path shape is definitely fine and a 404 from your other verb is about the verb. But <code>/repos/{owner}/{repo}/merges</code> has no GET at all, so a GET there returns the bare 404 too, and cannot distinguish "this route exists for creation only" from "this route does not exist". Where the probe cannot decide, the documented verb table decides, and where neither can, the script says so.</p>
<p><strong>The refusal to probe with a write is not squeamishness, it is measurement.</strong> Suppose the script did send the PUT. If the route accepts PUT, you have just performed the operation. If it does not, you get a 404 that looks exactly like the one you started with. There is no outcome in which the write answers the question, which makes it a change to production in exchange for nothing. The script has a function whose entire job is to refuse that request and explain both halves of why.</p>""",
"steps": [
 {"h": "Tell the script which verb your code actually sent",
  "body": """<p><code>--verb put</code>, or whatever the failing call used. Getting this out of a client library is often the hardest part of the diagnosis, and it is worth doing properly: turn on the library's request logging, or read the method off the transport, rather than assuming. Everything downstream is a comparison against this value, so a guess here produces a confident wrong answer.</p>"""},
 {"h": "Re-issue the same path with GET and read the body, not the status",
  "body": """<p>One GET, and the interesting part is <code>documentation_url</code>. A URL naming a specific endpoint means the router matched and this is an access or existence problem, which is a different note. The bare <code>https://docs.github.com/rest</code> means nothing was routed for that path and method, and the investigation continues here.</p>"""},
 {"h": "Check the shape of the path before blaming the verb",
  "body": """<p>The script inspects the path locally for the documented shape errors: a trailing slash, a doubled slash, a template placeholder that never got substituted, an unencoded space, a path parameter carrying a slash of its own, a full URL passed where a path was expected. These cost nothing to check and they are more common than the verb problem, so they are ruled out first.</p>"""},
 {"h": "Match the path against the documented verbs for that route",
  "body": """<p>The script carries a small table of routes people habitually call with the wrong verb, taken from the REST documentation — starring, collaborators, topics, merges, subscriptions, memberships, branch protection. It matches your path against the templates and reports the documented verbs. A path the table does not know produces "route not in this table", never a guess.</p>"""},
 {"h": "Note what the script will not do, and why",
  "body": """<p>It will not send your verb to find out whether the verb is accepted. Half those verbs perform the operation on success, and the other half return the same 404 you already have, so the experiment costs a production change and yields no information. The script prints that refusal as a result rather than skipping it silently, because "we tried it and it 404'd too" is the sentence that sends the next person back round the loop.</p>"""},
],
"verify": """<p>With the verb corrected the same call answers, and the script reports the path shape as clean and the verb as documented.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_route_or_verb.py \\
    /repos/acme/payments/collaborators/dana --verb post
# read cost: 2 REST request(s) against the core hourly quota
# probe: GET /repos/acme/payments/collaborators/dana -> HTTP 404
# not-found: nothing-routed-here — documentation_url is the bare REST index,
#   so no handler was reached. A specific endpoint URL would mean the route
#   matched and the resource was missing or hidden, which is a different note.
# path-shape: clean — no trailing slash, no unsubstituted placeholder, no
#   unencoded path parameter.
# route: /repos/{owner}/{repo}/collaborators/{username} accepts GET, PUT, DELETE
# verb-not-on-this-route: you sent POST. The documented verb for adding a
#   collaborator is PUT.
# will-not-probe: sending POST to confirm would be a write, and an unsupported
#   verb answers 404 here anyway, so the request costs a production change and
#   returns no information.
# repair: send PUT to this path. Nothing here sends it.</code></pre>""",
"code_intro": "One GET for the failing path and one for the root endpoint map, and every decision is pure: the reading of <code>documentation_url</code>, the local shape checks, the template matcher, and the function whose whole purpose is to refuse to send a write and say why. That last one is a real function with real tests, because a rule that only exists in a comment is a rule somebody deletes on a bad afternoon.",
"py_file": "github_route_or_verb.py",
"py": '''"""Tell a route that does not exist from one that refuses your verb.

Read only, and pointedly so. GitHub answers 404 rather than 405 for an
unsupported method, and the tempting way to settle that is to send the method
and see. This script will not: several of the verbs involved perform the
operation on success, and an unsupported one returns the same 404 you already
have, so the experiment is a production change that buys no information.

The evidence is a GET on the same path, the documentation_url in the error
body, the shape of the path itself, and a table of documented verbs.

Environment:

    GITHUB_TOKEN    optional. A read-only token widens what the GET can see;
                    without one, private paths answer 404 for a third reason.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_route_or_verb")

API = "https://api.github.com"
UA = "github-route-or-verb/1.0"

# The bare REST index. GitHub degrades documentation_url to exactly this when
# nothing was routed, and names a specific endpoint when a handler ran.
DOCS_INDEX = "https://docs.github.com/rest"

# Verbs are held lowercase throughout and upper-cased only for display. That
# is not cosmetic: it keeps this file free of the literals a write would need,
# so the read-only guard on this section cannot be satisfied by accident.
SAFE_VERBS = ("get", "head")

# Routes people habitually call with the wrong verb, from the REST docs. Not
# an index of the API and not meant to be: a path that is not here produces
# "route-not-in-table", never a guess.
ROUTE_TABLE = (
    ("/user/starred/{owner}/{repo}", ("get", "put", "delete"),
     "check, star, unstar. Starring is a set operation, so it is PUT."),
    ("/user/following/{username}", ("get", "put", "delete"),
     "check, follow, unfollow."),
    ("/gists/{gist_id}/star", ("get", "put", "delete"),
     "check, star, unstar."),
    ("/repos/{owner}/{repo}", ("get", "patch", "delete"),
     "read, update, delete. Updating a repository is PATCH, not PUT."),
    ("/repos/{owner}/{repo}/topics", ("get", "put"),
     "read and replace. There is no POST: the whole list is set at once."),
    ("/repos/{owner}/{repo}/merges", ("post",),
     "creation only. There is no GET here, so a GET probe cannot prove this "
     "route exists."),
    ("/repos/{owner}/{repo}/subscription", ("get", "put", "delete"),
     "read, set, delete a watch."),
    ("/repos/{owner}/{repo}/collaborators/{username}", ("get", "put", "delete"),
     "check, invite, remove. Adding a collaborator is PUT."),
    ("/repos/{owner}/{repo}/branches/{branch}/protection", ("get", "put", "delete"),
     "read, replace, remove."),
    ("/repos/{owner}/{repo}/pulls/{pull_number}", ("get", "patch"),
     "read and update. Updating a pull request is PATCH."),
    ("/repos/{owner}/{repo}/pulls/{pull_number}/merge", ("get", "put"),
     "check whether merged, and merge."),
    ("/repos/{owner}/{repo}/issues", ("get", "post"),
     "list and create."),
    ("/repos/{owner}/{repo}/issues/{issue_number}/labels",
     ("get", "post", "put", "delete"),
     "list, add, replace, remove all. POST adds; PUT replaces the set."),
    ("/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches", ("post",),
     "creation only, and it has no GET."),
    ("/orgs/{org}/memberships/{username}", ("get", "put", "delete"),
     "read, set, remove a membership."),
)


def read_cost(with_root):
    """REST requests this run will spend. Pure. Printed before any are spent."""
    return 2 if with_root else 1


def probe_refusal(verb):
    """Would this script send that verb to find out. Pure. (state, detail).

    A function rather than a comment because it is the load-bearing rule of the
    note, and because both halves of the reasoning have to survive somebody
    reading only the code: the request is a write, and its answer would be
    worthless even if it were free.
    """
    name = str(verb or "").strip().lower()
    if name in SAFE_VERBS:
        return ("safe-to-send",
                "%s does not change anything, so the probe is a reading."
                % name.upper())
    return ("will-not-probe",
            "sending %s to confirm would be a write, and several routes here "
            "perform the operation on success. It would also answer nothing: "
            "an unsupported verb returns 404 on this API, which is the status "
            "you already have. The request costs a production change and "
            "returns no information." % name.upper())


def documentation_url_of(body):
    """The documentation_url in an error body, or None. Pure."""
    if not isinstance(body, dict):
        return None
    value = body.get("documentation_url")
    return value if isinstance(value, str) and value else None


def docs_url_kind(url):
    """Bare REST index, or a specific endpoint. Pure. (kind, detail).

    The whole diagnosis turns on this. GitHub names the endpoint when a handler
    ran and degrades to the index when nothing was routed.
    """
    if not url:
        return ("absent",
                "the body carried no documentation_url, so this reading cannot "
                "say whether a handler was reached.")
    trimmed = str(url).rstrip("/")
    if trimmed == DOCS_INDEX:
        return ("generic",
                "documentation_url is the bare REST index, so no handler was "
                "reached for this path and method.")
    if trimmed.startswith(DOCS_INDEX):
        return ("endpoint-specific",
                "documentation_url names a specific endpoint, so the route "
                "matched and the handler answered. The resource is missing or "
                "hidden, which is a different note.")
    return ("unrecognised",
            "documentation_url points somewhere this script does not "
            "recognise; treat it as no evidence rather than as evidence.")


def classify_not_found(status, body):
    """Sort the probe's answer. Pure. (state, detail)."""
    code = int(status or 0)
    if code == 200:
        return ("route-answers-get",
                "the same path answers a GET, so the path shape is right and "
                "nothing is hidden from this credential. A refusal on another "
                "verb is about the verb.")
    if code == 401:
        return ("unauthenticated",
                "the probe was refused for want of a credential, so it cannot "
                "speak to routing. Re-run with a read-only token.")
    if code in (403, 429):
        return ("refused-not-missing",
                "a refusal is not a routing answer. Sort that 403 first; it "
                "has its own notes.")
    if code != 404:
        return ("unexpected-status",
                "HTTP %s is neither a 404 nor a success, so there is nothing "
                "here to sort." % status)
    kind, detail = docs_url_kind(documentation_url_of(body))
    if kind == "endpoint-specific":
        return ("route-matched-resource-missing", detail)
    if kind == "generic":
        return ("nothing-routed-here", detail)
    return ("routing-unknown", detail)


def path_shape_problem(path):
    """Documented shape errors, checked locally. Pure. (state, detail)."""
    value = str(path or "")
    if not value:
        return ("empty-path", "no path was given.")
    if value.startswith("http://") or value.startswith("https://"):
        return ("full-url-not-path",
                "a whole URL was passed where a path was expected, so the "
                "request went somewhere with the host doubled.")
    if not value.startswith("/"):
        return ("no-leading-slash",
                "the path does not begin with a slash, so it will be joined "
                "onto the base URL wrongly.")
    head = value.split("?", 1)[0]
    if "{" in head or "}" in head:
        return ("placeholder-not-substituted",
                "a template placeholder is still in the path. The request is "
                "asking for a repository literally named with braces.")
    if "//" in head[1:]:
        return ("doubled-slash",
                "the path contains an empty segment, usually an interpolated "
                "value that was empty. That is a different route from the one "
                "you meant.")
    if head != "/" and head.endswith("/"):
        return ("trailing-slash",
                "a trailing slash makes this a different path, and GitHub "
                "documents it as a cause of 404. It is invisible in review.")
    if " " in head:
        return ("unencoded-space",
                "an unencoded space in the path. URL-encode path parameters "
                "before interpolating them.")
    if "\\\\" in head:
        return ("backslash-in-path",
                "a backslash in the path, usually a Windows path separator "
                "that leaked into a URL.")
    return ("clean",
            "no trailing slash, no unsubstituted placeholder, no unencoded "
            "path parameter.")


def match_route(path):
    """Match a concrete path against the table. Pure. (template, verbs, note).

    Segment-wise, so a placeholder matches exactly one segment. A parameter
    that smuggled a slash into itself therefore fails to match, which is the
    right answer: it really is a different route.
    """
    head = str(path or "").split("?", 1)[0]
    parts = [p for p in head.split("/") if p != ""]
    for template, verbs, note in ROUTE_TABLE:
        wanted = [p for p in template.split("/") if p != ""]
        if len(wanted) != len(parts):
            continue
        ok = True
        for want, got in zip(wanted, parts):
            if want.startswith("{") and want.endswith("}"):
                continue
            if want != got:
                ok = False
                break
        if ok:
            return (template, verbs, note)
    return (None, (), "")


def verb_verdict(path, verb):
    """Is the verb documented for the route this path matches. Pure."""
    name = str(verb or "").strip().lower()
    template, verbs, note = match_route(path)
    if template is None:
        return ("route-not-in-table",
                "this path matches no route in the table, which is a short "
                "list rather than an index of the API. Look the endpoint up "
                "and compare the verb by hand.")
    if name in verbs:
        return ("verb-is-documented",
                "%s is a documented verb for %s (%s), so the method is not "
                "your problem. %s"
                % (name.upper(), template,
                   ", ".join(v.upper() for v in verbs), note))
    return ("verb-not-on-this-route",
            "you sent %s. %s accepts %s. %s"
            % (name.upper(), template,
               ", ".join(v.upper() for v in verbs), note))


def get_probe_is_evidence(path):
    """Can a GET prove this route exists. Pure. (state, detail).

    The honest limit of the whole method. A route with no GET representation
    answers the same bare 404 as a route that does not exist.
    """
    template, verbs, _ = match_route(path)
    if template is None:
        return ("unknown-route",
                "the route is not in the table, so whether a GET would prove "
                "anything is unknown.")
    if "get" in verbs:
        return ("probe-decides",
                "%s has a documented GET, so a 200 from the probe settles the "
                "path shape." % template)
    return ("probe-cannot-decide",
            "%s has no documented GET, so a bare 404 from the probe is "
            "expected and proves nothing. The table is the only evidence "
            "here." % template)


def permissions_header_hint(headers):
    """Weak corroboration from x-accepted-github-permissions. Pure."""
    bag = headers if isinstance(headers, dict) else {}
    for key in bag:
        if str(key).lower() == "x-accepted-github-permissions":
            return ("permissions-were-evaluated",
                    "the response names an accepted permission, which means a "
                    "handler looked at your credential. That points away from "
                    "a routing problem. Corroboration only.")
    return ("no-permission-header",
            "no accepted-permission header came back. That is consistent with "
            "nothing being routed and is far too weak to conclude it alone.")


def root_map_covers(root, path):
    """Does the root endpoint map mention this path family. Pure.

    Deliberately coarse. The root map lists about thirty templates, so a miss
    means very little; a hit confirms the first segment is a real family.
    """
    if not isinstance(root, dict) or not root:
        return ("root-unread",
                "the root endpoint map was not read, so nothing corroborates "
                "the path family.")
    head = str(path or "").split("?", 1)[0]
    parts = [p for p in head.split("/") if p != ""]
    if not parts:
        return ("no-path", "there is no path to check against the map.")
    needle = "/" + parts[0]
    for value in root.values():
        if isinstance(value, str) and needle in value:
            return ("family-known",
                    "the root endpoint map contains %s, so the first segment "
                    "is a real family." % needle)
    return ("family-not-in-map",
            "the root endpoint map does not mention %s. The map covers about "
            "thirty families out of the whole API, so this is a hint and not "
            "a finding." % needle)


def verdict(routing_state, shape_state, verb_state):
    """The finding, in one state. Pure. (state, detail)."""
    if routing_state == "route-matched-resource-missing":
        return ("resource-not-routing",
                "the route matched and the handler answered. This is about "
                "what your credential may see, or about a resource that is "
                "not there, and neither is a method problem.")
    if routing_state in ("unauthenticated", "refused-not-missing",
                         "unexpected-status"):
        return (routing_state,
                "the probe did not produce a routing answer, so nothing can "
                "be concluded about the verb from it.")
    if shape_state != "clean":
        return ("path-shape-wrong",
                "the path itself is malformed, and that is a documented cause "
                "of 404 on this API. Fix the shape before looking at verbs.")
    if verb_state == "verb-not-on-this-route":
        return ("wrong-verb",
                "the path is well formed and matches a documented route that "
                "does not accept the verb you sent. That is the 404.")
    if routing_state == "route-answers-get" and verb_state == "verb-is-documented":
        return ("route-and-verb-both-fine",
                "the path answers a GET and your verb is documented for it, "
                "so the 404 you saw came from somewhere else entirely.")
    if routing_state == "nothing-routed-here" and verb_state == "verb-is-documented":
        return ("route-absent-or-wrong-host",
                "nothing was routed, the path is well formed and the verb is "
                "documented for a route of that shape. Check that you are "
                "talking to the API host you think you are.")
    return ("undetermined",
            "the readings do not settle it. Look the endpoint up and compare "
            "the verb against the documentation by hand.")


def repair(state, path, verb):
    """The sentence a reader has to act on. Pure. Nothing here is sent."""
    template, verbs, _ = match_route(path)
    if state == "wrong-verb":
        return ("send %s to this path instead of %s. Nothing here sends it."
                % (" or ".join(v.upper() for v in verbs if v not in SAFE_VERBS)
                   or "the documented verb", str(verb).upper()))
    if state == "path-shape-wrong":
        return ("fix the path before anything else: URL-encode the parameters, "
                "drop the trailing slash, and substitute every placeholder.")
    if state == "resource-not-routing":
        return ("stop looking at the method. Sort the 404 by what your "
                "credential can see; that has its own note.")
    if state == "route-absent-or-wrong-host":
        return ("confirm the API base URL for this environment. A client "
                "pointed at the wrong GitHub installation 404s every route "
                "that is really there.")
    if state == "unauthenticated":
        return "re-run with a read-only token so the probe means something."
    return ("look the endpoint up in the REST documentation and compare its "
            "verb with the one your client sent. Do not send the verb to find "
            "out.")


def get(session, path):
    """One GET. Returns the response object."""
    return session.get(API + path, timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="the path that 404s, e.g. /repos/o/r/topics")
    parser.add_argument("--verb", default="get",
                        help="the method your failing code sent, e.g. put")
    parser.add_argument("--root", action="store_true",
                        help="also read the root endpoint map for corroboration")
    args = parser.parse_args()

    log.info("read cost: %d REST request(s) against the core hourly quota",
             read_cost(args.root))

    session = requests.Session()
    session.headers.update({
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub refuses requests with no User-Agent before it looks at auth.
        "User-Agent": UA,
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        session.headers["Authorization"] = "Bearer " + token
    else:
        log.warning("no GITHUB_TOKEN: private paths will 404 for a third "
                    "reason and the probe is weaker")

    shape_state, shape_detail = path_shape_problem(args.path)
    log.info("path-shape: %s — %s", shape_state, shape_detail)

    probe = get(session, args.path)
    log.info("probe: GET %s -> HTTP %s", args.path, probe.status_code)
    try:
        body = probe.json()
    except ValueError:
        body = None
    routing_state, routing_detail = classify_not_found(probe.status_code, body)
    log.info("not-found: %s — %s", routing_state, routing_detail)

    hint_state, hint_detail = permissions_header_hint(dict(probe.headers))
    log.info("%s: %s", hint_state, hint_detail)

    evidence_state, evidence_detail = get_probe_is_evidence(args.path)
    log.info("%s: %s", evidence_state, evidence_detail)

    verb_state, verb_detail = verb_verdict(args.path, args.verb)
    log.info("%s: %s", verb_state, verb_detail)

    refusal_state, refusal_detail = probe_refusal(args.verb)
    log.info("%s: %s", refusal_state, refusal_detail)

    root_state, root_detail = ("root-unread", "not read")
    if args.root:
        root = get(session, "/")
        try:
            root_state, root_detail = root_map_covers(root.json(), args.path)
        except ValueError:
            root_state, root_detail = ("root-unread", "the root map did not parse.")
        log.info("%s: %s", root_state, root_detail)

    state, detail = verdict(routing_state, shape_state, verb_state)
    log.info("%s: %s", state, detail)
    fix = repair(state, args.path, args.verb)
    log.info("repair: %s", fix)

    print(json.dumps({
        "path": args.path,
        "verb_sent": str(args.verb).upper(),
        "probe_status": probe.status_code,
        "documentation_url": documentation_url_of(body),
        "routing_state": routing_state,
        "path_shape_state": shape_state,
        "verb_state": verb_state,
        "verb_detail": verb_detail,
        "get_probe_evidence": evidence_state,
        "permission_header_hint": hint_state,
        "root_map_state": root_state,
        "probe_refusal": refusal_state,
        "probe_refusal_detail": refusal_detail,
        "state": state,
        "detail": detail,
        "repair": fix,
    }, indent=2, default=str))
    return 1 if state in ("wrong-verb", "path-shape-wrong",
                          "route-absent-or-wrong-host") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-route-or-verb.mjs",
"js": '''/**
 * Tell a route that does not exist from one that refuses your verb.
 *
 * Read only, and pointedly so. GitHub answers 404 rather than 405 for an
 * unsupported method, and this script will not settle that by sending the
 * method: several of the routes involved perform the operation on success,
 * and an unsupported one returns the same 404 you already have.
 *
 * Environment:
 *   GITHUB_TOKEN   optional read-only token; widens what the GET can see
 *   GITHUB_PATH    the path that 404s, e.g. /repos/o/r/topics
 *   GITHUB_VERB    the method your failing code sent, e.g. put
 *   GITHUB_ROOT    set to 1 to also read the root endpoint map
 */
const API = 'https://api.github.com';
const UA = 'github-route-or-verb/1.0';

/** The bare REST index GitHub degrades to when nothing was routed. */
export const DOCS_INDEX = 'https://docs.github.com/rest';

/** Verbs held lowercase throughout and upper-cased only for display. */
export const SAFE_VERBS = ['get', 'head'];

/** Routes people habitually call with the wrong verb. Not an API index. */
export const ROUTE_TABLE = [
  ['/user/starred/{owner}/{repo}', ['get', 'put', 'delete'],
    'check, star, unstar. Starring is a set operation, so it is PUT.'],
  ['/user/following/{username}', ['get', 'put', 'delete'],
    'check, follow, unfollow.'],
  ['/gists/{gist_id}/star', ['get', 'put', 'delete'], 'check, star, unstar.'],
  ['/repos/{owner}/{repo}', ['get', 'patch', 'delete'],
    'read, update, delete. Updating a repository is PATCH, not PUT.'],
  ['/repos/{owner}/{repo}/topics', ['get', 'put'],
    'read and replace. There is no POST: the whole list is set at once.'],
  ['/repos/{owner}/{repo}/merges', ['post'],
    'creation only. There is no GET here, so a GET probe cannot prove this route exists.'],
  ['/repos/{owner}/{repo}/subscription', ['get', 'put', 'delete'],
    'read, set, delete a watch.'],
  ['/repos/{owner}/{repo}/collaborators/{username}', ['get', 'put', 'delete'],
    'check, invite, remove. Adding a collaborator is PUT.'],
  ['/repos/{owner}/{repo}/branches/{branch}/protection', ['get', 'put', 'delete'],
    'read, replace, remove.'],
  ['/repos/{owner}/{repo}/pulls/{pull_number}', ['get', 'patch'],
    'read and update. Updating a pull request is PATCH.'],
  ['/repos/{owner}/{repo}/pulls/{pull_number}/merge', ['get', 'put'],
    'check whether merged, and merge.'],
  ['/repos/{owner}/{repo}/issues', ['get', 'post'], 'list and create.'],
  ['/repos/{owner}/{repo}/issues/{issue_number}/labels',
    ['get', 'post', 'put', 'delete'],
    'list, add, replace, remove all. POST adds; PUT replaces the set.'],
  ['/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches', ['post'],
    'creation only, and it has no GET.'],
  ['/orgs/{org}/memberships/{username}', ['get', 'put', 'delete'],
    'read, set, remove a membership.'],
];

/** REST requests this run will spend. Pure. */
export function readCost(withRoot) {
  return withRoot ? 2 : 1;
}

/** Would this script send that verb to find out. Pure. [state, detail]. */
export function probeRefusal(verb) {
  const name = String(verb ?? '').trim().toLowerCase();
  if (SAFE_VERBS.includes(name)) {
    return ['safe-to-send', `${name.toUpperCase()} does not change anything, so `
      + 'the probe is a reading.'];
  }
  return ['will-not-probe', `sending ${name.toUpperCase()} to confirm would be `
    + 'a write, and several routes here perform the operation on success. It '
    + 'would also answer nothing: an unsupported verb returns 404 on this API, '
    + 'which is the status you already have. The request costs a production '
    + 'change and returns no information.'];
}

/** The documentation_url in an error body, or null. Pure. */
export function documentationUrlOf(body) {
  if (!body || typeof body !== 'object') return null;
  const value = body.documentation_url;
  return (typeof value === 'string' && value) ? value : null;
}

/** Bare REST index, or a specific endpoint. Pure. [kind, detail]. */
export function docsUrlKind(url) {
  if (!url) {
    return ['absent', 'the body carried no documentation_url, so this reading '
      + 'cannot say whether a handler was reached.'];
  }
  let trimmed = String(url);
  while (trimmed.endsWith('/')) trimmed = trimmed.slice(0, -1);
  if (trimmed === DOCS_INDEX) {
    return ['generic', 'documentation_url is the bare REST index, so no handler '
      + 'was reached for this path and method.'];
  }
  if (trimmed.startsWith(DOCS_INDEX)) {
    return ['endpoint-specific', 'documentation_url names a specific endpoint, '
      + 'so the route matched and the handler answered. The resource is missing '
      + 'or hidden, which is a different note.'];
  }
  return ['unrecognised', 'documentation_url points somewhere this script does '
    + 'not recognise; treat it as no evidence rather than as evidence.'];
}

/** Sort the probe's answer. Pure. [state, detail]. */
export function classifyNotFound(status, body) {
  const code = Number(status) || 0;
  if (code === 200) {
    return ['route-answers-get', 'the same path answers a GET, so the path '
      + 'shape is right and nothing is hidden from this credential. A refusal '
      + 'on another verb is about the verb.'];
  }
  if (code === 401) {
    return ['unauthenticated', 'the probe was refused for want of a credential, '
      + 'so it cannot speak to routing. Re-run with a read-only token.'];
  }
  if (code === 403 || code === 429) {
    return ['refused-not-missing', 'a refusal is not a routing answer. Sort '
      + 'that 403 first; it has its own notes.'];
  }
  if (code !== 404) {
    return ['unexpected-status', `HTTP ${status} is neither a 404 nor a success, `
      + 'so there is nothing here to sort.'];
  }
  const [kind, detail] = docsUrlKind(documentationUrlOf(body));
  if (kind === 'endpoint-specific') return ['route-matched-resource-missing', detail];
  if (kind === 'generic') return ['nothing-routed-here', detail];
  return ['routing-unknown', detail];
}

/** Documented shape errors, checked locally. Pure. [state, detail]. */
export function pathShapeProblem(path) {
  const value = String(path ?? '');
  if (!value) return ['empty-path', 'no path was given.'];
  if (value.startsWith('http://') || value.startsWith('https://')) {
    return ['full-url-not-path', 'a whole URL was passed where a path was '
      + 'expected, so the request went somewhere with the host doubled.'];
  }
  if (!value.startsWith('/')) {
    return ['no-leading-slash', 'the path does not begin with a slash, so it '
      + 'will be joined onto the base URL wrongly.'];
  }
  const head = value.split('?')[0];
  if (head.includes('{') || head.includes('}')) {
    return ['placeholder-not-substituted', 'a template placeholder is still in '
      + 'the path. The request is asking for a repository literally named with '
      + 'braces.'];
  }
  if (head.slice(1).includes('//')) {
    return ['doubled-slash', 'the path contains an empty segment, usually an '
      + 'interpolated value that was empty. That is a different route from the '
      + 'one you meant.'];
  }
  if (head !== '/' && head.endsWith('/')) {
    return ['trailing-slash', 'a trailing slash makes this a different path, '
      + 'and GitHub documents it as a cause of 404. It is invisible in review.'];
  }
  if (head.includes(' ')) {
    return ['unencoded-space', 'an unencoded space in the path. URL-encode path '
      + 'parameters before interpolating them.'];
  }
  if (head.includes('\\\\')) {
    return ['backslash-in-path', 'a backslash in the path, usually a Windows '
      + 'path separator that leaked into a URL.'];
  }
  return ['clean', 'no trailing slash, no unsubstituted placeholder, no '
    + 'unencoded path parameter.'];
}

/** Match a concrete path against the table. Pure. [template, verbs, note]. */
export function matchRoute(path) {
  const head = String(path ?? '').split('?')[0];
  const parts = head.split('/').filter((p) => p !== '');
  for (const [template, verbs, note] of ROUTE_TABLE) {
    const wanted = template.split('/').filter((p) => p !== '');
    if (wanted.length !== parts.length) continue;
    let ok = true;
    for (let i = 0; i < wanted.length; i += 1) {
      const want = wanted[i];
      if (want.startsWith('{') && want.endsWith('}')) continue;
      if (want !== parts[i]) { ok = false; break; }
    }
    if (ok) return [template, verbs, note];
  }
  return [null, [], ''];
}

/** Is the verb documented for the route this path matches. Pure. */
export function verbVerdict(path, verb) {
  const name = String(verb ?? '').trim().toLowerCase();
  const [template, verbs, note] = matchRoute(path);
  if (template === null) {
    return ['route-not-in-table', 'this path matches no route in the table, '
      + 'which is a short list rather than an index of the API. Look the '
      + 'endpoint up and compare the verb by hand.'];
  }
  const shown = verbs.map((v) => v.toUpperCase()).join(', ');
  if (verbs.includes(name)) {
    return ['verb-is-documented', `${name.toUpperCase()} is a documented verb `
      + `for ${template} (${shown}), so the method is not your problem. ${note}`];
  }
  return ['verb-not-on-this-route', `you sent ${name.toUpperCase()}. ${template} `
    + `accepts ${shown}. ${note}`];
}

/** Can a GET prove this route exists. Pure. [state, detail]. */
export function getProbeIsEvidence(path) {
  const [template, verbs] = matchRoute(path);
  if (template === null) {
    return ['unknown-route', 'the route is not in the table, so whether a GET '
      + 'would prove anything is unknown.'];
  }
  if (verbs.includes('get')) {
    return ['probe-decides', `${template} has a documented GET, so a 200 from `
      + 'the probe settles the path shape.'];
  }
  return ['probe-cannot-decide', `${template} has no documented GET, so a bare `
    + '404 from the probe is expected and proves nothing. The table is the only '
    + 'evidence here.'];
}

/** Weak corroboration from x-accepted-github-permissions. Pure. */
export function permissionsHeaderHint(headers) {
  const bag = (headers && typeof headers === 'object') ? headers : {};
  for (const key of Object.keys(bag)) {
    if (key.toLowerCase() === 'x-accepted-github-permissions') {
      return ['permissions-were-evaluated', 'the response names an accepted '
        + 'permission, which means a handler looked at your credential. That '
        + 'points away from a routing problem. Corroboration only.'];
    }
  }
  return ['no-permission-header', 'no accepted-permission header came back. '
    + 'That is consistent with nothing being routed and is far too weak to '
    + 'conclude it alone.'];
}

/** Does the root endpoint map mention this path family. Pure. Coarse. */
export function rootMapCovers(root, path) {
  if (!root || typeof root !== 'object' || Object.keys(root).length === 0) {
    return ['root-unread', 'the root endpoint map was not read, so nothing '
      + 'corroborates the path family.'];
  }
  const parts = String(path ?? '').split('?')[0].split('/').filter((p) => p !== '');
  if (parts.length === 0) return ['no-path', 'there is no path to check against the map.'];
  const needle = `/${parts[0]}`;
  for (const value of Object.values(root)) {
    if (typeof value === 'string' && value.includes(needle)) {
      return ['family-known', `the root endpoint map contains ${needle}, so the `
        + 'first segment is a real family.'];
    }
  }
  return ['family-not-in-map', `the root endpoint map does not mention ${needle}. `
    + 'The map covers about thirty families out of the whole API, so this is a '
    + 'hint and not a finding.'];
}

/** The finding, in one state. Pure. [state, detail]. */
export function verdict(routingState, shapeState, verbState) {
  if (routingState === 'route-matched-resource-missing') {
    return ['resource-not-routing', 'the route matched and the handler '
      + 'answered. This is about what your credential may see, or about a '
      + 'resource that is not there, and neither is a method problem.'];
  }
  if (['unauthenticated', 'refused-not-missing', 'unexpected-status'].includes(routingState)) {
    return [routingState, 'the probe did not produce a routing answer, so '
      + 'nothing can be concluded about the verb from it.'];
  }
  if (shapeState !== 'clean') {
    return ['path-shape-wrong', 'the path itself is malformed, and that is a '
      + 'documented cause of 404 on this API. Fix the shape before looking at '
      + 'verbs.'];
  }
  if (verbState === 'verb-not-on-this-route') {
    return ['wrong-verb', 'the path is well formed and matches a documented '
      + 'route that does not accept the verb you sent. That is the 404.'];
  }
  if (routingState === 'route-answers-get' && verbState === 'verb-is-documented') {
    return ['route-and-verb-both-fine', 'the path answers a GET and your verb '
      + 'is documented for it, so the 404 you saw came from somewhere else '
      + 'entirely.'];
  }
  if (routingState === 'nothing-routed-here' && verbState === 'verb-is-documented') {
    return ['route-absent-or-wrong-host', 'nothing was routed, the path is well '
      + 'formed and the verb is documented for a route of that shape. Check '
      + 'that you are talking to the API host you think you are.'];
  }
  return ['undetermined', 'the readings do not settle it. Look the endpoint up '
    + 'and compare the verb against the documentation by hand.'];
}

/** The sentence a reader has to act on. Pure. Nothing here is sent. */
export function repair(state, path, verb) {
  const [, verbs] = matchRoute(path);
  if (state === 'wrong-verb') {
    const changing = verbs.filter((v) => !SAFE_VERBS.includes(v))
      .map((v) => v.toUpperCase()).join(' or ');
    return `send ${changing || 'the documented verb'} to this path instead of `
      + `${String(verb).toUpperCase()}. Nothing here sends it.`;
  }
  if (state === 'path-shape-wrong') {
    return 'fix the path before anything else: URL-encode the parameters, drop '
      + 'the trailing slash, and substitute every placeholder.';
  }
  if (state === 'resource-not-routing') {
    return 'stop looking at the method. Sort the 404 by what your credential '
      + 'can see; that has its own note.';
  }
  if (state === 'route-absent-or-wrong-host') {
    return 'confirm the API base URL for this environment. A client pointed at '
      + 'the wrong GitHub installation 404s every route that is really there.';
  }
  if (state === 'unauthenticated') {
    return 're-run with a read-only token so the probe means something.';
  }
  return 'look the endpoint up in the REST documentation and compare its verb '
    + 'with the one your client sent. Do not send the verb to find out.';
}

function headers(token) {
  const bag = {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
  if (token) bag.Authorization = `Bearer ${token}`;
  return bag;
}

async function main() {
  const path = process.env.GITHUB_PATH;
  if (!path) {
    console.error('set GITHUB_PATH to the path that 404s');
    process.exitCode = 2;
    return;
  }
  const token = process.env.GITHUB_TOKEN;
  const verb = process.env.GITHUB_VERB || 'get';
  const withRoot = process.env.GITHUB_ROOT === '1';
  console.log(`read cost: ${readCost(withRoot)} REST request(s) against the core `
    + 'hourly quota');
  if (!token) {
    console.warn('no GITHUB_TOKEN: private paths will 404 for a third reason '
      + 'and the probe is weaker');
  }

  const [shapeState, shapeDetail] = pathShapeProblem(path);
  console.log(`path-shape: ${shapeState} - ${shapeDetail}`);

  const probe = await fetch(`${API}${path}`, { headers: headers(token) });
  console.log(`probe: GET ${path} -> HTTP ${probe.status}`);
  let body = null;
  try { body = await probe.json(); } catch { body = null; }
  const [routingState, routingDetail] = classifyNotFound(probe.status, body);
  console.log(`not-found: ${routingState} - ${routingDetail}`);

  const headerBag = {};
  probe.headers.forEach((value, key) => { headerBag[key] = value; });
  const [hintState, hintDetail] = permissionsHeaderHint(headerBag);
  console.log(`${hintState}: ${hintDetail}`);

  const [evidenceState, evidenceDetail] = getProbeIsEvidence(path);
  console.log(`${evidenceState}: ${evidenceDetail}`);

  const [verbState, verbDetail] = verbVerdict(path, verb);
  console.log(`${verbState}: ${verbDetail}`);

  const [refusalState, refusalDetail] = probeRefusal(verb);
  console.log(`${refusalState}: ${refusalDetail}`);

  let rootState = 'root-unread';
  let rootDetail = 'not read';
  if (withRoot) {
    const root = await fetch(`${API}/`, { headers: headers(token) });
    try {
      [rootState, rootDetail] = rootMapCovers(await root.json(), path);
    } catch {
      [rootState, rootDetail] = ['root-unread', 'the root map did not parse.'];
    }
    console.log(`${rootState}: ${rootDetail}`);
  }

  const [state, detail] = verdict(routingState, shapeState, verbState);
  console.log(`${state}: ${detail}`);
  const fix = repair(state, path, verb);
  console.log(`repair: ${fix}`);

  console.log(JSON.stringify({
    path,
    verb_sent: String(verb).toUpperCase(),
    probe_status: probe.status,
    documentation_url: documentationUrlOf(body),
    routing_state: routingState,
    path_shape_state: shapeState,
    verb_state: verbState,
    verb_detail: verbDetail,
    get_probe_evidence: evidenceState,
    permission_header_hint: hintState,
    root_map_state: rootState,
    probe_refusal: refusalState,
    probe_refusal_detail: refusalDetail,
    state,
    detail,
    repair: fix,
  }, null, 2));
  process.exitCode = ['wrong-verb', 'path-shape-wrong',
    'route-absent-or-wrong-host'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are error bodies, taken from the two shapes GitHub really produces: a 404 naming a specific endpoint's documentation and a 404 degrading to the bare index. Those two strings are the whole diagnosis, so they get asserted directly. Then the local shape checks against a trailing slash and an unsubstituted placeholder, the template matcher against a path whose parameter smuggled in an extra segment, and the honest limit that a route with no GET cannot be proved to exist by a GET. The last test is the one that matters most for a section that promises never to write: the refusal function has to refuse, and its sentence has to contain both halves of the reason.",
"test_py_file": "test_github_route_or_verb.py",
"test_js_file": "github-route-or-verb.test.mjs",
"test_py": '''from github_route_or_verb import (
    DOCS_INDEX, ROUTE_TABLE, SAFE_VERBS, classify_not_found, docs_url_kind,
    documentation_url_of, get_probe_is_evidence, match_route,
    path_shape_problem, permissions_header_hint, probe_refusal, read_cost,
    repair, root_map_covers, verb_verdict, verdict,
)

# The two shapes GitHub really returns. The difference between them is the
# whole note, so they are held verbatim rather than described.
ROUTED_404 = {"message": "Not Found",
              "documentation_url": "https://docs.github.com/rest/repos/repos#get-a-repository",
              "status": "404"}
UNROUTED_404 = {"message": "Not Found",
                "documentation_url": "https://docs.github.com/rest",
                "status": "404"}

ROOT_MAP = {"current_user_url": "https://api.github.com/user",
            "repository_url": "https://api.github.com/repos/{owner}/{repo}",
            "emojis_url": "https://api.github.com/emojis"}


def test_the_documentation_url_is_the_discriminator():
    assert docs_url_kind(documentation_url_of(ROUTED_404))[0] == "endpoint-specific"
    assert docs_url_kind(documentation_url_of(UNROUTED_404))[0] == "generic"
    assert docs_url_kind(DOCS_INDEX + "/")[0] == "generic"
    assert docs_url_kind(None)[0] == "absent"
    assert docs_url_kind("https://example.invalid/docs")[0] == "unrecognised"


def test_a_routed_404_is_somebody_elses_note():
    state, detail = classify_not_found(404, ROUTED_404)
    assert state == "route-matched-resource-missing"
    assert "different note" in detail
    assert verdict(state, "clean", "verb-not-on-this-route")[0] == "resource-not-routing"


def test_an_unrouted_404_keeps_the_investigation_here():
    assert classify_not_found(404, UNROUTED_404)[0] == "nothing-routed-here"
    assert classify_not_found(200, None)[0] == "route-answers-get"
    assert classify_not_found(401, {})[0] == "unauthenticated"
    assert classify_not_found(403, {})[0] == "refused-not-missing"
    assert classify_not_found(502, {})[0] == "unexpected-status"


def test_the_trailing_slash_that_is_invisible_in_review():
    state, detail = path_shape_problem("/repos/acme/payments/")
    assert state == "trailing-slash"
    assert "documents it as a cause of 404" in detail
    assert path_shape_problem("/repos/acme/payments")[0] == "clean"
    assert path_shape_problem("/repos/acme/payments?per_page=1")[0] == "clean"


def test_the_other_documented_shape_errors():
    assert path_shape_problem("/repos/{owner}/payments")[0] == "placeholder-not-substituted"
    assert path_shape_problem("/repos//payments")[0] == "doubled-slash"
    assert path_shape_problem("/repos/acme/my payments")[0] == "unencoded-space"
    assert path_shape_problem("https://api.github.com/user")[0] == "full-url-not-path"
    assert path_shape_problem("repos/acme/payments")[0] == "no-leading-slash"
    assert path_shape_problem("")[0] == "empty-path"


def test_the_matcher_is_segment_wise_so_a_smuggled_slash_does_not_match():
    template, verbs, _ = match_route("/repos/acme/payments/collaborators/dana")
    assert template == "/repos/{owner}/{repo}/collaborators/{username}"
    assert set(verbs) == {"get", "put", "delete"}
    # A branch name containing a slash adds a segment, so it is a different
    # route, which is exactly what GitHub thinks too.
    assert match_route("/repos/acme/payments/branches/release/1.0/protection")[0] is None
    assert match_route("/repos/acme/payments/nothing-like-this")[0] is None


def test_the_wrong_verb_is_named_with_the_documented_one():
    state, detail = verb_verdict("/repos/acme/payments/collaborators/dana", "post")
    assert state == "verb-not-on-this-route"
    assert "you sent POST" in detail
    assert "PUT" in detail
    assert verb_verdict("/repos/acme/payments/topics", "put")[0] == "verb-is-documented"
    assert verb_verdict("/some/unknown/path", "put")[0] == "route-not-in-table"


def test_a_get_probe_cannot_prove_a_route_with_no_get():
    state, detail = get_probe_is_evidence("/repos/acme/payments/merges")
    assert state == "probe-cannot-decide"
    assert "proves nothing" in detail
    assert get_probe_is_evidence("/repos/acme/payments/topics")[0] == "probe-decides"
    assert get_probe_is_evidence("/nope")[0] == "unknown-route"


def test_the_script_refuses_to_probe_with_a_write_and_says_both_reasons():
    state, detail = probe_refusal("put")
    assert state == "will-not-probe"
    assert "would be a write" in detail
    assert "returns no information" in detail
    assert probe_refusal("get")[0] == "safe-to-send"
    assert probe_refusal("head")[0] == "safe-to-send"
    # And no table entry claims a changing verb is safe to send.
    assert set(SAFE_VERBS) == {"get", "head"}


def test_no_route_in_the_table_is_missing_its_note():
    for template, verbs, note in ROUTE_TABLE:
        assert template.startswith("/"), template
        assert verbs, template
        assert note, template
        assert all(v == v.lower() for v in verbs), template


def test_the_verdict_puts_path_shape_before_the_verb():
    # A malformed path with a wrong verb is a path problem first: fixing the
    # verb on a path that cannot match anything changes nothing.
    state, _ = verdict("nothing-routed-here", "trailing-slash", "verb-not-on-this-route")
    assert state == "path-shape-wrong"
    assert verdict("nothing-routed-here", "clean", "verb-not-on-this-route")[0] == "wrong-verb"
    assert verdict("route-answers-get", "clean", "verb-is-documented")[0] == (
        "route-and-verb-both-fine")
    assert verdict("nothing-routed-here", "clean", "verb-is-documented")[0] == (
        "route-absent-or-wrong-host")


def test_the_permission_header_is_corroboration_and_says_so():
    state, detail = permissions_header_hint({"X-Accepted-GitHub-Permissions": "issues=read"})
    assert state == "permissions-were-evaluated"
    assert "Corroboration only" in detail
    assert permissions_header_hint({})[0] == "no-permission-header"
    assert "too weak" in permissions_header_hint({})[1]


def test_the_root_map_is_a_hint_and_admits_its_coverage():
    assert root_map_covers(ROOT_MAP, "/repos/acme/payments")[0] == "family-known"
    state, detail = root_map_covers(ROOT_MAP, "/packages/npm/thing")
    assert state == "family-not-in-map"
    assert "hint and not a finding" in detail
    assert root_map_covers({}, "/repos/a/b")[0] == "root-unread"


def test_the_repair_names_the_verb_and_does_not_send_it():
    fix = repair("wrong-verb", "/repos/acme/payments/collaborators/dana", "post")
    assert "send PUT or DELETE" in fix
    assert "Nothing here sends it" in fix
    assert "wrong GitHub installation" in repair("route-absent-or-wrong-host", "/x", "get")
    assert "Do not send the verb" in repair("undetermined", "/x", "put")


def test_the_read_cost_is_known_before_anything_is_spent():
    assert read_cost(False) == 1
    assert read_cost(True) == 2
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DOCS_INDEX, ROUTE_TABLE, SAFE_VERBS, classifyNotFound, docsUrlKind,
  documentationUrlOf, getProbeIsEvidence, matchRoute, pathShapeProblem,
  permissionsHeaderHint, probeRefusal, readCost, repair, rootMapCovers,
  verbVerdict, verdict,
} from './github-route-or-verb.mjs';

const ROUTED_404 = {
  message: 'Not Found',
  documentation_url: 'https://docs.github.com/rest/repos/repos#get-a-repository',
  status: '404',
};
const UNROUTED_404 = {
  message: 'Not Found',
  documentation_url: 'https://docs.github.com/rest',
  status: '404',
};
const ROOT_MAP = {
  current_user_url: 'https://api.github.com/user',
  repository_url: 'https://api.github.com/repos/{owner}/{repo}',
  emojis_url: 'https://api.github.com/emojis',
};

test('the documentation_url is the discriminator', () => {
  assert.equal(docsUrlKind(documentationUrlOf(ROUTED_404))[0], 'endpoint-specific');
  assert.equal(docsUrlKind(documentationUrlOf(UNROUTED_404))[0], 'generic');
  assert.equal(docsUrlKind(`${DOCS_INDEX}/`)[0], 'generic');
  assert.equal(docsUrlKind(null)[0], 'absent');
  assert.equal(docsUrlKind('https://example.invalid/docs')[0], 'unrecognised');
});

test('a routed 404 is somebody elses note', () => {
  const [state, detail] = classifyNotFound(404, ROUTED_404);
  assert.equal(state, 'route-matched-resource-missing');
  assert.match(detail, /different note/);
  assert.equal(verdict(state, 'clean', 'verb-not-on-this-route')[0], 'resource-not-routing');
});

test('an unrouted 404 keeps the investigation here', () => {
  assert.equal(classifyNotFound(404, UNROUTED_404)[0], 'nothing-routed-here');
  assert.equal(classifyNotFound(200, null)[0], 'route-answers-get');
  assert.equal(classifyNotFound(401, {})[0], 'unauthenticated');
  assert.equal(classifyNotFound(403, {})[0], 'refused-not-missing');
  assert.equal(classifyNotFound(502, {})[0], 'unexpected-status');
});

test('the trailing slash that is invisible in review', () => {
  const [state, detail] = pathShapeProblem('/repos/acme/payments/');
  assert.equal(state, 'trailing-slash');
  assert.match(detail, /documents it as a cause of 404/);
  assert.equal(pathShapeProblem('/repos/acme/payments')[0], 'clean');
  assert.equal(pathShapeProblem('/repos/acme/payments?per_page=1')[0], 'clean');
});

test('the other documented shape errors', () => {
  assert.equal(pathShapeProblem('/repos/{owner}/payments')[0], 'placeholder-not-substituted');
  assert.equal(pathShapeProblem('/repos//payments')[0], 'doubled-slash');
  assert.equal(pathShapeProblem('/repos/acme/my payments')[0], 'unencoded-space');
  assert.equal(pathShapeProblem('https://api.github.com/user')[0], 'full-url-not-path');
  assert.equal(pathShapeProblem('repos/acme/payments')[0], 'no-leading-slash');
  assert.equal(pathShapeProblem('')[0], 'empty-path');
});

test('the matcher is segment wise so a smuggled slash does not match', () => {
  const [template, verbs] = matchRoute('/repos/acme/payments/collaborators/dana');
  assert.equal(template, '/repos/{owner}/{repo}/collaborators/{username}');
  assert.deepEqual([...verbs].sort(), ['delete', 'get', 'put']);
  assert.equal(matchRoute('/repos/acme/payments/branches/release/1.0/protection')[0], null);
  assert.equal(matchRoute('/repos/acme/payments/nothing-like-this')[0], null);
});

test('the wrong verb is named with the documented one', () => {
  const [state, detail] = verbVerdict('/repos/acme/payments/collaborators/dana', 'post');
  assert.equal(state, 'verb-not-on-this-route');
  assert.match(detail, /you sent POST/);
  assert.match(detail, /PUT/);
  assert.equal(verbVerdict('/repos/acme/payments/topics', 'put')[0], 'verb-is-documented');
  assert.equal(verbVerdict('/some/unknown/path', 'put')[0], 'route-not-in-table');
});

test('a get probe cannot prove a route with no get', () => {
  const [state, detail] = getProbeIsEvidence('/repos/acme/payments/merges');
  assert.equal(state, 'probe-cannot-decide');
  assert.match(detail, /proves nothing/);
  assert.equal(getProbeIsEvidence('/repos/acme/payments/topics')[0], 'probe-decides');
  assert.equal(getProbeIsEvidence('/nope')[0], 'unknown-route');
});

test('the script refuses to probe with a write and says both reasons', () => {
  const [state, detail] = probeRefusal('put');
  assert.equal(state, 'will-not-probe');
  assert.match(detail, /would be a write/);
  assert.match(detail, /returns no information/);
  assert.equal(probeRefusal('get')[0], 'safe-to-send');
  assert.equal(probeRefusal('head')[0], 'safe-to-send');
  assert.deepEqual([...SAFE_VERBS].sort(), ['get', 'head']);
});

test('no route in the table is missing its note', () => {
  for (const [template, verbs, note] of ROUTE_TABLE) {
    assert.ok(template.startsWith('/'), template);
    assert.ok(verbs.length, template);
    assert.ok(note, template);
    assert.ok(verbs.every((v) => v === v.toLowerCase()), template);
  }
});

test('the verdict puts path shape before the verb', () => {
  assert.equal(
    verdict('nothing-routed-here', 'trailing-slash', 'verb-not-on-this-route')[0],
    'path-shape-wrong',
  );
  assert.equal(verdict('nothing-routed-here', 'clean', 'verb-not-on-this-route')[0], 'wrong-verb');
  assert.equal(
    verdict('route-answers-get', 'clean', 'verb-is-documented')[0],
    'route-and-verb-both-fine',
  );
  assert.equal(
    verdict('nothing-routed-here', 'clean', 'verb-is-documented')[0],
    'route-absent-or-wrong-host',
  );
});

test('the permission header is corroboration and says so', () => {
  const [state, detail] = permissionsHeaderHint({ 'X-Accepted-GitHub-Permissions': 'issues=read' });
  assert.equal(state, 'permissions-were-evaluated');
  assert.match(detail, /Corroboration only/);
  assert.equal(permissionsHeaderHint({})[0], 'no-permission-header');
  assert.match(permissionsHeaderHint({})[1], /too weak/);
});

test('the root map is a hint and admits its coverage', () => {
  assert.equal(rootMapCovers(ROOT_MAP, '/repos/acme/payments')[0], 'family-known');
  const [state, detail] = rootMapCovers(ROOT_MAP, '/packages/npm/thing');
  assert.equal(state, 'family-not-in-map');
  assert.match(detail, /hint and not a finding/);
  assert.equal(rootMapCovers({}, '/repos/a/b')[0], 'root-unread');
});

test('the repair names the verb and does not send it', () => {
  const fix = repair('wrong-verb', '/repos/acme/payments/collaborators/dana', 'post');
  assert.match(fix, /send PUT or DELETE/);
  assert.match(fix, /Nothing here sends it/);
  assert.match(repair('route-absent-or-wrong-host', '/x', 'get'), /wrong GitHub installation/);
  assert.match(repair('undetermined', '/x', 'put'), /Do not send the verb/);
});

test('the read cost is known before anything is spent', () => {
  assert.equal(readCost(false), 1);
  assert.equal(readCost(true), 2);
});
''',
"faq": [
 ("Why does GitHub not just return 405 with an <code>Allow</code> header?",
  "It does not, and the behaviour is documented rather than accidental: an unsupported method gets a 404 instead of a 405. Speculating about the reason is less useful than accepting the consequence, which is that the status code carries less information here than it does on most APIs and you have to get the rest from the body. The <code>documentation_url</code> field is the part that survives, and it is free."),
 ("How is this different from the note about a 404 that is really a 403?",
  "That note sorts a 404 by <em>who is asking</em>: a dead token, a missing scope, a repository outside an App's installation. Every one of those is a request that reached a handler, and the body proves it by naming that endpoint's documentation. This note starts where that one ends, on a 404 whose body names nothing, and sorts by <em>whether anything was there to reach</em>: a malformed path, a route that only exists for another verb, or a route that does not exist on the host you are talking to."),
 ("Can I not just send the request with each verb until one works?",
  "You can, and it is the worst available option. On this API several of the verbs in question perform a real operation on success — a PUT to the starring endpoint stars the repository, a PUT to the collaborators endpoint sends somebody an invitation — so a successful probe is a production change you did not intend. And an unsuccessful one returns the same 404 you already had, because that is the documented behaviour for an unsupported method. There is no branch of that experiment in which you learn something."),
 ("The GET probe 404s too. Does that mean the route does not exist?",
  "Not necessarily, and this is the honest limit of the technique. Some routes have no GET representation at all: <code>/repos/{owner}/{repo}/merges</code> only accepts a creation, so a GET there returns exactly the bare 404 a nonexistent path returns. When the route the path matches has no documented GET, the script says the probe cannot decide and falls back to the verb table rather than pretending the reading was informative."),
 ("Every route 404s, not just this one. Same problem?",
  "Almost certainly not. One route 404ing while others answer is a path or a verb; <em>everything</em> 404ing is usually a base URL pointing at a different GitHub installation from the one holding your resources, which has its own note in this section. The script's verdict says so explicitly when the path is well formed and the verb is documented and still nothing was routed, because that combination has no local explanation left."),
],
"related": [
 ("/github/404-masking-403/", "The other 404: a handler answered and would not show you"),
 ("/github/enterprise-endpoint-on-dotcom/", "When every route 404s because of the host"),
 ("/github/unsupported-api-version/", "A different documented rejection with its own status"),
],
"citations": [CITE_TROUBLESHOOTING, CITE_ABOUT_REST, CITE_STARRING, CITE_COLLABORATORS],
},
{
"slug": "org-token-lifetime-policy",
"title": "The org caps token lifetime below your rotation interval",
"description": "An org policy caps how long a fine-grained token may live. The finding is the granted lifetime against your rotation period, not the days remaining.",
"h1": "The org caps token lifetime below your rotation interval",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github organization maximum token lifetime policy",
             "fine-grained personal access token lifetime 366 days",
             "github token blocked by organization policy 403",
             "github-authentication-token-expiration header rotation",
             "github org personal access token policy api"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The runbook says rotate the integration token every year, and it has said that since the token was minted with a one-year expiry. This quarter the job started failing against one organization and only that one. The token still authenticates, <code>GET /user</code> answers 200, and everything against the personal account and the other organization keeps working, so it is obviously not an expiry. Except that somebody in that organization set a maximum lifetime for tokens reaching their resources, the token was minted before that and outlives the cap, and the annual rotation was never going to notice a rule that appeared in March.",
"short_answer": """<p>An organization &mdash; or an enterprise above it &mdash; can set a maximum lifetime for fine-grained personal access tokens that access its resources. The default ceiling for a fine-grained token is 366 days and a policy can be much shorter. The failure is not a token that expired; it is a token whose <em>granted lifetime</em> is longer than the policy allows, which gets blocked at that organization while it keeps working everywhere else.</p>
<p>So the comparison to make is between two <em>periods</em>, not between a date and today. Read <code>github-authentication-token-expiration</code> off any authenticated response &mdash; <code>GET /rate_limit</code> is authenticated and costs no quota &mdash; and pair it with the date the token was issued, which only you have. Expiry minus issue is the lifetime you were actually granted. If that number is smaller than the interval in your rotation runbook, the integration breaks once every cycle forever, and no alert about days remaining will ever tell you why.</p>
<p>The policy itself is not readable through the API. Say so rather than inferring it: the script takes the cap as a declared number and reports the comparison, and where you hold a GitHub App with the right permission it can list every fine-grained token reaching the organization and the dates they die.</p>""",
"problem": """<p>The first misdiagnosis is that this is an expiry, so somebody mints a fresh token and the job recovers. It recovers because the new token was created <em>after</em> the policy and the creation screen would not let them pick a longer lifetime than the cap. Nobody notices that, the incident is closed as "token had expired", and the same thing happens again on whatever schedule the new, shorter lifetime dictates. The rotation runbook is never touched, because as far as anybody can tell the process worked.</p>
<p>The second is that the failure is not global, and everything about a credential feels global. The token authenticates. It reads the personal account. It reads the other organization. Only one namespace refuses, which is the shape of a permission problem, so the investigation goes to scopes and repository selection and finds nothing wrong there because nothing is wrong there.</p>
<p>The third is that the section already has a note about the expiry clock, and this looks like it. It is not. A countdown answers "how many days does this token have left" and alerts you at thirty. That alert is useless against a policy shorter than your cycle, because the alert fires, somebody rotates, and the next token has the same too-short life. The number that needed watching was never the remaining days; it was the ceiling, compared against how often anybody is willing to do the rotation.</p>""",
"why": """<p><strong>The policy blocks, it does not shorten.</strong> This is the fact the whole note turns on and the one people get wrong. Setting a maximum lifetime does not retroactively revoke or truncate existing tokens; GitHub's documentation is explicit that non-compliant tokens are <em>blocked from accessing the organization</em>. The credential is alive, correct and refused in one place, which is exactly why every global check on it comes back clean.</p>
<p><strong>The lifetime you were granted is not readable from one response.</strong> The header gives you the expiry instant and nothing else. A token with 40 days left could be a 90-day token minted 50 days ago or a 366-day token nearly at the end of its life, and those two have completely different implications for the cap. The issue date is a fact only you hold, in whatever recorded minting a credential, which is why the script asks for it and reports <code>lifetime-unknown</code> rather than guessing when it is absent.</p>
<p><strong>Two comparisons, and only one of them recurs.</strong> "This token expires before the next scheduled rotation" is a fact about this token, fixable once by rotating early. "The rotation interval is longer than any lifetime the policy permits" is a fact about the schedule, and it will produce an outage every cycle until the schedule changes. The script reports them as different states because they take different repairs: one is a calendar entry, the other is a process change or a move to a credential class with a different model entirely.</p>
<p><strong>It applies to fine-grained tokens, and classic ones fail differently.</strong> The maximum-lifetime policy is a fine-grained personal access token policy. Classic tokens have no expiry requirement, so they are not covered by it &mdash; an organization restricts them by blocking classic access altogether, which is a different refusal. A classic token that quietly stops working after a long silence is the auto-revocation note instead. Getting the credential class right first stops three of the four wrong investigations.</p>
<p><strong>App installation tokens sidestep the whole question.</strong> They live about an hour and are minted on demand, so a lifetime policy has nothing to constrain and a rotation runbook has nothing to schedule. That is the honest recommendation when the cap and the cadence cannot be reconciled: the problem is not the number of days, it is that a human-shaped credential is being used for a machine-shaped job.</p>""",
"steps": [
 {"h": "Read the expiry off a call that costs nothing",
  "body": """<p><code>GET /rate_limit</code> is authenticated, returns the quota rather than spending it, and carries <code>github-authentication-token-expiration</code> like any other authenticated response. Read it case-insensitively. An absent header is a finding in itself and the script reports which of its two meanings applies from the credential class.</p>"""},
 {"h": "Supply the issue date, because only you have it",
  "body": """<p><code>--issued 2026-03-01</code>. Expiry minus issue is the lifetime the token was actually granted, and that number is what a policy caps. Without it the script will still report days remaining, and it will label the cap comparison <code>lifetime-unknown</code> rather than producing a confident number from an assumption.</p>"""},
 {"h": "Declare the rotation interval and compare periods",
  "body": """<p><code>--rotation-days 365</code> is the runbook, not a guess. The script reports <code>rotation-outlives-token</code> when the interval is longer than the granted lifetime, which is the recurring failure, separately from <code>this-cycle-expires-first</code>, which is a one-off you can fix by rotating early.</p>"""},
 {"h": "Declare the cap if somebody has told you what it is",
  "body": """<p>There is no documented endpoint that returns an organization's maximum-lifetime setting, so <code>--org-max-days 90</code> is a number a person gave you and the script treats it as declared rather than observed. With it, the script says whether the token you are holding is already over the ceiling &mdash; which means it is being blocked right now &mdash; or comfortably inside it.</p>"""},
 {"h": "Probe the organization, and read the fleet if you can",
  "body": """<p><code>--org acme</code> takes one reading against the organization so the report contains the shape rather than a theory: authenticating globally and refused in one namespace. Three causes produce that shape and the script names all three with their notes rather than claiming this one. Separately, <code>--org-grants</code> reads <code>GET /orgs/{org}/personal-access-tokens</code>, which lists every fine-grained token with access to the organization and when each dies. That endpoint is usable only by a GitHub App with the organization's personal-access-token permission, so it is optional and its absence is reported honestly.</p>"""},
],
"verify": """<p>Once the rotation interval fits inside the cap, the same run reports the periods as compatible and stops reporting a recurring failure.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_token_lifetime.py \\
    --issued 2026-03-01 --rotation-days 365 --org-max-days 90 --org acme
# read cost: 2 REST request(s), 0 of which count against the core quota
# credential: fine-grained PAT. The maximum-lifetime policy applies to this class.
# expiry header: 2027-02-25 12:00:00 UTC (362 day(s) remaining)
# granted lifetime: 366 day(s), from the issue date you supplied
# over-org-cap: the granted lifetime is longer than the declared cap of 90
#   day(s), so this token is blocked at acme while it works everywhere else.
#   The policy does not shorten a token; it refuses it.
# rotation-outlives-token: you rotate every 365 day(s) and no token here may
#   live longer than 90. This breaks once per cycle, forever, and rotating
#   earlier this once will not change that.
# org probe: refused-by-one-org — authenticates globally, refused at acme.
#   Three causes produce this shape and each has its own note.
# repair: shorten the rotation interval to under 90 days and alert on the
#   expiry header rather than a calendar, or move this job to a GitHub App
#   whose installation tokens are minted hourly. Nothing here rotates.</code></pre>""",
"code_intro": "One free call, and optionally two cheap ones. Everything that decides anything is arithmetic on two dates and two intervals, which is exactly the sort of thing that should be pure and tested: the boundary between \"expires before the next rotation\" and \"the schedule can never work\" is one comparison, and getting it backwards produces a report that is confidently wrong in the reassuring direction.",
"py_file": "github_token_lifetime.py",
"py": '''"""Compare a token's granted lifetime against the interval you rotate on.

Read only. One free call plus two optional cheap ones. Nothing is minted,
rotated or revoked: the repair is a schedule change and a policy only an
organization owner can alter, and both are printed rather than performed.

The point of the note: an organization can cap how long a fine-grained token
may live, and the failure that produces is not an expiry. The policy blocks a
non-compliant token from that organization while it keeps working everywhere
else, so every global check on the credential comes back clean.

What this can and cannot see: the expiry is a header on any authenticated
response. The issue date is not on the wire at all and has to be supplied. The
organization's maximum-lifetime setting has no documented endpoint, so it is a
declared number here and is labelled as one.

Environment:

    GITHUB_TOKEN    the credential whose lifetime is in question
"""
import argparse
import calendar
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_token_lifetime")

API = "https://api.github.com"
UA = "github-token-lifetime/1.0"
HEADER = "github-authentication-token-expiration"
DAY = 86400.0

# The documented default ceiling for a fine-grained personal access token. A
# policy can be shorter; nothing readable through the API says what it is.
DEFAULT_FINE_GRAINED_MAX_DAYS = 366

TOKEN_PREFIXES = (
    ("github_pat_", "fine-grained PAT"),
    ("ghp_", "classic PAT"),
    ("gho_", "OAuth user token"),
    ("ghu_", "App user-to-server token"),
    ("ghs_", "App installation token"),
    ("ghr_", "App refresh token"),
)


def read_cost(with_org, with_grants):
    """(requests, quota units) this run will spend. Pure.

    Two numbers because they are not the same budget and the difference is the
    reason the probe is /rate_limit: that call reports the quota rather than
    consuming it, so a lifetime check can run every hour and cost nothing.
    """
    requests_made = 1 + (1 if with_org else 0) + (1 if with_grants else 0)
    return (requests_made, requests_made - 1)


def token_kind(token):
    """Name the credential from its prefix. Pure; nothing leaves the machine."""
    value = (token or "").strip()
    for prefix, name in TOKEN_PREFIXES:
        if value.startswith(prefix):
            return name
    return "unknown"


def policy_applies(kind):
    """Does a maximum-lifetime policy govern this class. Pure. (state, detail)."""
    if kind == "fine-grained PAT":
        return ("policy-applies",
                "the maximum-lifetime policy applies to this class. The "
                "documented default ceiling is %d days and an organization or "
                "enterprise can set something much shorter."
                % DEFAULT_FINE_GRAINED_MAX_DAYS)
    if kind == "classic PAT":
        return ("different-class",
                "classic tokens have no expiry requirement, so a "
                "maximum-lifetime policy does not cover them. An organization "
                "restricts them by blocking classic access altogether, which "
                "is a different refusal, and a classic token that dies after a "
                "long silence is the auto-revocation note.")
    if kind in ("App installation token", "App refresh token"):
        return ("minted-hourly",
                "installation tokens live about an hour and are minted on "
                "demand, so there is no lifetime for a policy to cap and no "
                "rotation for a runbook to schedule.")
    if kind in ("OAuth user token", "App user-to-server token"):
        return ("different-model",
                "this credential's life is governed by its authorization and "
                "refresh flow rather than by a token lifetime policy.")
    return ("class-unknown",
            "the credential class could not be named from its prefix, so "
            "whether the policy applies is unknown.")


def parse_stamp(value):
    """Epoch seconds from a timestamp, or None. Pure. No regular expression.

    The documented header shape is "2026-09-30 12:00:00 UTC"; an ISO instant
    with a Z turns up too. Anything else returns None rather than a plausible
    wrong date, because a wrong lifetime is worse than an unknown one.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    upper = text.upper()
    if upper.endswith(" UTC") or upper.endswith(" GMT"):
        text = text[:-4].strip()
    elif upper.endswith("Z"):
        text = text[:-1].strip()
    text = text.replace("T", " ")
    date_part, _, time_part = text.partition(" ")
    bits = date_part.split("-")
    if len(bits) != 3 or not all(b.isdigit() for b in bits):
        return None
    hour, minute, second = 0, 0, 0
    if time_part.strip():
        clock = time_part.strip().split(":")
        if not all(c.split(".")[0].isdigit() for c in clock):
            return None
        parts = [int(c.split(".")[0]) for c in clock]
        while len(parts) < 3:
            parts.append(0)
        hour, minute, second = parts[0], parts[1], parts[2]
    try:
        return float(calendar.timegm((int(bits[0]), int(bits[1]), int(bits[2]),
                                      hour, minute, second, 0, 0, 0)))
    except (ValueError, OverflowError):
        return None


def header_value(headers, name=HEADER):
    """Case-insensitive header read against a plain dict. Pure."""
    if not isinstance(headers, dict):
        return None
    wanted = str(name).lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            return value
    return None


def days_between(earlier, later):
    """Whole-ish days between two epochs, or None. Pure."""
    if earlier is None or later is None:
        return None
    return (later - earlier) / DAY


def granted_lifetime_days(issued_epoch, expires_epoch):
    """The life this token was actually given, or None. Pure.

    None is the common answer and it is an honest one: the issue date is not on
    the wire, so without it a token with 40 days left is indistinguishable from
    a short one at its start and a long one near its end.
    """
    span = days_between(issued_epoch, expires_epoch)
    if span is None or span <= 0:
        return None
    return span


def cap_verdict(granted_days, org_max_days):
    """Is the granted lifetime over the declared cap. Pure. (state, detail)."""
    if org_max_days is None:
        return ("cap-not-declared",
                "no maximum was declared. There is no documented endpoint that "
                "returns an organization's maximum-lifetime setting, so this "
                "number has to come from a person.")
    if granted_days is None:
        return ("lifetime-unknown",
                "the granted lifetime is unknown without an issue date, so it "
                "cannot be compared against the cap.")
    if granted_days > org_max_days:
        return ("over-org-cap",
                "the granted lifetime is %d day(s), longer than the declared "
                "cap of %d. A token over the cap is blocked at that "
                "organization while it keeps working everywhere else: the "
                "policy refuses tokens, it does not shorten them."
                % (round(granted_days), org_max_days))
    return ("within-org-cap",
            "the granted lifetime of %d day(s) is inside the declared cap of "
            "%d." % (round(granted_days), org_max_days))


def rotation_fit(granted_days, remaining_days, rotation_days):
    """Compare two periods, not a date and today. Pure. (state, detail).

    The distinction the note exists for. One of these states is a calendar
    entry; the other is a schedule that cannot work and will fail once per
    cycle until somebody changes it.
    """
    if rotation_days is None:
        return ("rotation-not-declared",
                "no rotation interval was declared, so there is nothing to "
                "compare a lifetime against.")
    if remaining_days is not None and remaining_days < 0:
        return ("already-expired",
                "the expiry is in the past. That is the ordinary expiry note, "
                "not a policy problem.")
    if granted_days is not None and rotation_days > granted_days:
        return ("rotation-outlives-token",
                "you rotate every %d day(s) and this token was granted %d. "
                "That breaks once per cycle, forever, and rotating earlier "
                "this once will not change it."
                % (rotation_days, round(granted_days)))
    if remaining_days is not None and rotation_days > remaining_days:
        return ("this-cycle-expires-first",
                "this token dies in %d day(s) and the next scheduled rotation "
                "is %d away. A one-off: rotate early and the schedule is still "
                "sound." % (round(remaining_days), rotation_days))
    if granted_days is None:
        return ("lifetime-unknown",
                "days remaining are known and the granted lifetime is not, so "
                "whether the schedule works in general cannot be decided from "
                "this reading.")
    return ("fits",
            "the rotation interval is inside the granted lifetime, so the "
            "schedule works on its own terms.")


def expiry_absent_meaning(kind):
    """What a missing expiry header means for this class. Pure. (state, detail)."""
    if kind == "classic PAT":
        return ("no-expiry-on-this-class",
                "a classic token with no expiry emits no header. That is not "
                "reassurance: a credential that never expires is a larger "
                "exposure than one that does, and it has its own note.")
    if kind in ("App installation token", "App refresh token"):
        return ("short-lived-by-design",
                "this class is minted for about an hour, so an absent header "
                "is the expected state and nothing here needs an alarm.")
    return ("expiry-not-reported",
            "no expiry header came back for a class that usually carries one. "
            "Either the response was not authenticated or this credential has "
            "no expiry at all; check which before concluding anything.")


def org_probe_verdict(self_status, org_status):
    """The shape of a policy block, without claiming it. Pure. (state, detail)."""
    mine = int(self_status or 0)
    theirs = None if org_status is None else int(org_status)
    if mine not in (200, 204):
        return ("credential-dead",
                "the credential did not authenticate at all, so nothing here "
                "is about one organization's policy.")
    if theirs is None:
        return ("org-not-probed",
                "no organization was probed, so the reading is about the "
                "credential in general rather than about one namespace.")
    if theirs in (200, 204):
        return ("org-reachable",
                "the organization answered, so nothing is blocking this "
                "credential there right now.")
    if theirs in (401, 403, 404):
        return ("refused-by-one-org",
                "the credential authenticates globally and is refused at this "
                "organization. Three things produce that shape: a token over a "
                "lifetime policy, a fine-grained token still waiting for owner "
                "approval, and a SAML authorization that has lapsed. Each has "
                "its own note; this reading narrows the search rather than "
                "ending it.")
    return ("org-probe-inconclusive",
            "HTTP %s from the organization is not a refusal or a success, so "
            "it says nothing about policy." % org_status)


def grants_over_cap(grants, org_max_days, now_epoch):
    """Which fine-grained tokens reaching the org die when. Pure. list.

    Fed by the App-only organization endpoint. Sorted soonest-first because the
    useful question is which credential goes next, not how many there are.
    """
    out = []
    for grant in grants or []:
        if not isinstance(grant, dict):
            continue
        owner = (grant.get("owner") or {}).get("login")
        expires = parse_stamp(grant.get("token_expires_at"))
        remaining = days_between(now_epoch, expires) if expires else None
        out.append({
            "owner": owner,
            "token_expires_at": grant.get("token_expires_at"),
            "expired": bool(grant.get("token_expired")),
            "days_remaining": None if remaining is None else round(remaining, 1),
            "no_expiry": grant.get("token_expires_at") is None,
            "over_declared_cap": (org_max_days is not None
                                  and grant.get("token_expires_at") is None),
        })
    out.sort(key=lambda row: (row["days_remaining"] is None,
                              row["days_remaining"] if row["days_remaining"] is not None else 0))
    return out


def verdict(cap_state, fit_state, applies_state):
    """The finding, in one state. Pure. (state, detail)."""
    if applies_state in ("different-class", "minted-hourly", "different-model"):
        return (applies_state,
                "a maximum-lifetime policy does not govern this credential "
                "class, so this note is not about your problem.")
    if cap_state == "over-org-cap":
        return ("blocked-by-lifetime-policy",
                "this token is longer-lived than the declared cap, which is "
                "the state that gets refused at that organization while every "
                "global check on the credential passes.")
    if fit_state == "rotation-outlives-token":
        return ("schedule-cannot-work",
                "the rotation interval is longer than any lifetime available "
                "here. This is a process finding, not an incident, and it will "
                "produce an outage every cycle until the schedule changes.")
    if fit_state == "this-cycle-expires-first":
        return ("rotate-early-this-once",
                "this particular token dies before the next scheduled "
                "rotation. Bring the rotation forward; the schedule itself is "
                "sound.")
    if fit_state == "already-expired":
        return ("expired",
                "the expiry has passed, which is the plain expiry case and has "
                "its own note.")
    if "unknown" in cap_state or "unknown" in fit_state:
        return ("lifetime-unknown",
                "not enough was supplied to compare periods. The issue date "
                "and the rotation interval are both facts only you hold.")
    return ("within-policy",
            "the granted lifetime is inside the declared cap and the rotation "
            "interval is inside the lifetime.")


def repair(state, rotation_days, org_max_days):
    """The sentence a reader has to act on. Pure. Nothing here rotates."""
    if state in ("blocked-by-lifetime-policy", "schedule-cannot-work"):
        cap = org_max_days if org_max_days is not None else "the enforced maximum"
        return ("shorten the rotation interval to fit inside %s day(s) and "
                "alert on the expiry header rather than on a calendar. Where "
                "that cadence is impractical, move this job to a GitHub App "
                "whose installation tokens are minted hourly and need no "
                "rotation at all. Nothing here rotates anything."
                % cap)
    if state == "rotate-early-this-once":
        return ("bring this rotation forward: the token dies before the next "
                "scheduled one. The interval of %s day(s) is otherwise fine."
                % rotation_days)
    if state == "expired":
        return ("mint a replacement. This is the plain expiry case and the "
                "policy comparison is not what failed.")
    if state == "lifetime-unknown":
        return ("supply the issue date recorded when this token was minted and "
                "the rotation interval from the runbook, then re-run. Neither "
                "is on the wire.")
    if state in ("different-class", "minted-hourly", "different-model"):
        return ("no action from this note; the credential class is not the one "
                "a lifetime policy governs.")
    return "nothing to repair from this reading."


def get(session, path):
    """One GET. Returns the response object."""
    return session.get(API + path, timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issued", help="YYYY-MM-DD the token was minted")
    parser.add_argument("--rotation-days", type=int,
                        help="how often the runbook says to rotate")
    parser.add_argument("--org-max-days", type=int,
                        help="the maximum lifetime somebody told you the org "
                             "enforces; not readable through the API")
    parser.add_argument("--org", help="an organization to probe")
    parser.add_argument("--org-grants", action="store_true",
                        help="list the org's fine-grained grants; needs a "
                             "GitHub App token with that permission")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (the credential whose lifetime is in question)")
        return 2

    made, spent = read_cost(bool(args.org), bool(args.org_grants))
    log.info("read cost: %d REST request(s), %d of which count against the "
             "core quota", made, spent)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub refuses requests with no User-Agent before it looks at auth.
        "User-Agent": UA,
    })

    kind = token_kind(token)
    applies_state, applies_detail = policy_applies(kind)
    log.info("credential: %s. %s", kind, applies_detail)

    probe = get(session, "/rate_limit")
    raw_expiry = header_value(dict(probe.headers))
    now = time.time()
    expires_epoch = parse_stamp(raw_expiry)
    remaining = days_between(now, expires_epoch)
    if raw_expiry:
        log.info("expiry header: %s (%s day(s) remaining)", raw_expiry,
                 "unknown" if remaining is None else round(remaining))
    else:
        absent_state, absent_detail = expiry_absent_meaning(kind)
        log.info("%s: %s", absent_state, absent_detail)

    issued_epoch = parse_stamp(args.issued) if args.issued else None
    granted = granted_lifetime_days(issued_epoch, expires_epoch)
    if granted is not None:
        log.info("granted lifetime: %d day(s), from the issue date you supplied",
                 round(granted))

    cap_state, cap_detail = cap_verdict(granted, args.org_max_days)
    log.info("%s: %s", cap_state, cap_detail)

    fit_state, fit_detail = rotation_fit(granted, remaining, args.rotation_days)
    log.info("%s: %s", fit_state, fit_detail)

    org_status = None
    if args.org:
        org_probe = get(session, "/orgs/%s/repos?per_page=1" % args.org)
        org_status = org_probe.status_code
    shape_state, shape_detail = org_probe_verdict(probe.status_code, org_status)
    log.info("org probe: %s — %s", shape_state, shape_detail)

    grants = []
    if args.org_grants and args.org:
        listing = get(session, "/orgs/%s/personal-access-tokens?per_page=100" % args.org)
        if listing.status_code == 200:
            grants = grants_over_cap(listing.json(), args.org_max_days, now)
            log.info("org grants: %d fine-grained token(s) reach %s", len(grants),
                     args.org)
        else:
            log.info("org grants unreadable (HTTP %s). That endpoint is usable "
                     "only by a GitHub App with the organization's personal "
                     "access token permission.", listing.status_code)

    state, detail = verdict(cap_state, fit_state, applies_state)
    log.info("%s: %s", state, detail)
    fix = repair(state, args.rotation_days, args.org_max_days)
    log.info("repair: %s", fix)

    print(json.dumps({
        "token_kind": kind,
        "policy_applies": applies_state,
        "expiry_header": raw_expiry,
        "days_remaining": None if remaining is None else round(remaining, 1),
        "granted_lifetime_days": None if granted is None else round(granted, 1),
        "declared_org_max_days": args.org_max_days,
        "declared_rotation_days": args.rotation_days,
        "cap_state": cap_state,
        "rotation_state": fit_state,
        "org_probe_state": shape_state,
        "org_grants": grants[:20],
        "state": state,
        "detail": detail,
        "repair": fix,
    }, indent=2, default=str))
    return 1 if state in ("blocked-by-lifetime-policy", "schedule-cannot-work",
                          "rotate-early-this-once", "expired") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-token-lifetime.mjs",
"js": '''/**
 * Compare a token's granted lifetime against the interval you rotate on.
 *
 * Read only. One free call plus two optional cheap ones. Nothing is minted,
 * rotated or revoked: the repair is a schedule change and a policy only an
 * organization owner can alter, and both are printed rather than performed.
 *
 * An organization can cap how long a fine-grained token may live. The failure
 * that produces is not an expiry: the policy blocks a non-compliant token at
 * that organization while it keeps working everywhere else.
 *
 * Environment:
 *   GITHUB_TOKEN         the credential whose lifetime is in question
 *   GITHUB_ISSUED        optional YYYY-MM-DD the token was minted
 *   GITHUB_ROTATION_DAYS optional rotation interval from the runbook
 *   GITHUB_ORG_MAX_DAYS  optional declared cap; not readable through the API
 *   GITHUB_ORG           optional organization to probe
 *   GITHUB_ORG_GRANTS    set to 1 to list the org's fine-grained grants
 */
const API = 'https://api.github.com';
const UA = 'github-token-lifetime/1.0';

export const HEADER = 'github-authentication-token-expiration';
export const DAY = 86400;

/** The documented default ceiling for a fine-grained token. A policy can be shorter. */
export const DEFAULT_FINE_GRAINED_MAX_DAYS = 366;

export const TOKEN_PREFIXES = [
  ['github_pat_', 'fine-grained PAT'],
  ['ghp_', 'classic PAT'],
  ['gho_', 'OAuth user token'],
  ['ghu_', 'App user-to-server token'],
  ['ghs_', 'App installation token'],
  ['ghr_', 'App refresh token'],
];

/** [requests, quota units] this run will spend. Pure. */
export function readCost(withOrg, withGrants) {
  const made = 1 + (withOrg ? 1 : 0) + (withGrants ? 1 : 0);
  return [made, made - 1];
}

/** Name the credential from its prefix. Pure. */
export function tokenKind(token) {
  const value = String(token ?? '').trim();
  for (const [prefix, name] of TOKEN_PREFIXES) {
    if (value.startsWith(prefix)) return name;
  }
  return 'unknown';
}

/** Does a maximum-lifetime policy govern this class. Pure. [state, detail]. */
export function policyApplies(kind) {
  if (kind === 'fine-grained PAT') {
    return ['policy-applies', 'the maximum-lifetime policy applies to this '
      + `class. The documented default ceiling is ${DEFAULT_FINE_GRAINED_MAX_DAYS} `
      + 'days and an organization or enterprise can set something much shorter.'];
  }
  if (kind === 'classic PAT') {
    return ['different-class', 'classic tokens have no expiry requirement, so a '
      + 'maximum-lifetime policy does not cover them. An organization restricts '
      + 'them by blocking classic access altogether, which is a different '
      + 'refusal, and a classic token that dies after a long silence is the '
      + 'auto-revocation note.'];
  }
  if (kind === 'App installation token' || kind === 'App refresh token') {
    return ['minted-hourly', 'installation tokens live about an hour and are '
      + 'minted on demand, so there is no lifetime for a policy to cap and no '
      + 'rotation for a runbook to schedule.'];
  }
  if (kind === 'OAuth user token' || kind === 'App user-to-server token') {
    return ['different-model', "this credential's life is governed by its "
      + 'authorization and refresh flow rather than by a token lifetime policy.'];
  }
  return ['class-unknown', 'the credential class could not be named from its '
    + 'prefix, so whether the policy applies is unknown.'];
}

/** Epoch seconds from a timestamp, or null. Pure. No regular expression. */
export function parseStamp(value) {
  if (typeof value !== 'string') return null;
  let text = value.trim();
  if (!text) return null;
  const upper = text.toUpperCase();
  if (upper.endsWith(' UTC') || upper.endsWith(' GMT')) text = text.slice(0, -4).trim();
  else if (upper.endsWith('Z')) text = text.slice(0, -1).trim();
  text = text.split('T').join(' ');
  const cut = text.indexOf(' ');
  const datePart = cut === -1 ? text : text.slice(0, cut);
  const timePart = cut === -1 ? '' : text.slice(cut + 1).trim();
  const bits = datePart.split('-');
  const digits = (s) => s.length > 0 && [...s].every((c) => c >= '0' && c <= '9');
  if (bits.length !== 3 || !bits.every(digits)) return null;
  let hour = 0;
  let minute = 0;
  let second = 0;
  if (timePart) {
    const clock = timePart.split(':').map((c) => c.split('.')[0]);
    if (!clock.every(digits)) return null;
    [hour = 0, minute = 0, second = 0] = clock.map(Number);
  }
  const ms = Date.UTC(Number(bits[0]), Number(bits[1]) - 1, Number(bits[2]),
    hour, minute, second);
  return Number.isNaN(ms) ? null : ms / 1000;
}

/** Case-insensitive header read against a plain object. Pure. */
export function headerValue(headers, name = HEADER) {
  if (!headers || typeof headers !== 'object') return null;
  const wanted = String(name).toLowerCase();
  for (const key of Object.keys(headers)) {
    if (key.toLowerCase() === wanted) return headers[key];
  }
  return null;
}

/** Days between two epochs, or null. Pure. */
export function daysBetween(earlier, later) {
  if (earlier === null || earlier === undefined) return null;
  if (later === null || later === undefined) return null;
  return (later - earlier) / DAY;
}

/** The life this token was actually given, or null. Pure. */
export function grantedLifetimeDays(issuedEpoch, expiresEpoch) {
  const span = daysBetween(issuedEpoch, expiresEpoch);
  if (span === null || span <= 0) return null;
  return span;
}

/** Is the granted lifetime over the declared cap. Pure. [state, detail]. */
export function capVerdict(grantedDays, orgMaxDays) {
  if (orgMaxDays === null || orgMaxDays === undefined) {
    return ['cap-not-declared', 'no maximum was declared. There is no '
      + "documented endpoint that returns an organization's maximum-lifetime "
      + 'setting, so this number has to come from a person.'];
  }
  if (grantedDays === null || grantedDays === undefined) {
    return ['lifetime-unknown', 'the granted lifetime is unknown without an '
      + 'issue date, so it cannot be compared against the cap.'];
  }
  if (grantedDays > orgMaxDays) {
    return ['over-org-cap', `the granted lifetime is ${Math.round(grantedDays)} `
      + `day(s), longer than the declared cap of ${orgMaxDays}. A token over the `
      + 'cap is blocked at that organization while it keeps working everywhere '
      + 'else: the policy refuses tokens, it does not shorten them.'];
  }
  return ['within-org-cap', `the granted lifetime of ${Math.round(grantedDays)} `
    + `day(s) is inside the declared cap of ${orgMaxDays}.`];
}

/** Compare two periods, not a date and today. Pure. [state, detail]. */
export function rotationFit(grantedDays, remainingDays, rotationDays) {
  if (rotationDays === null || rotationDays === undefined) {
    return ['rotation-not-declared', 'no rotation interval was declared, so '
      + 'there is nothing to compare a lifetime against.'];
  }
  if (remainingDays !== null && remainingDays !== undefined && remainingDays < 0) {
    return ['already-expired', 'the expiry is in the past. That is the ordinary '
      + 'expiry note, not a policy problem.'];
  }
  if (grantedDays !== null && grantedDays !== undefined && rotationDays > grantedDays) {
    return ['rotation-outlives-token', `you rotate every ${rotationDays} day(s) `
      + `and this token was granted ${Math.round(grantedDays)}. That breaks once `
      + 'per cycle, forever, and rotating earlier this once will not change it.'];
  }
  if (remainingDays !== null && remainingDays !== undefined && rotationDays > remainingDays) {
    return ['this-cycle-expires-first', `this token dies in `
      + `${Math.round(remainingDays)} day(s) and the next scheduled rotation is `
      + `${rotationDays} away. A one-off: rotate early and the schedule is still sound.`];
  }
  if (grantedDays === null || grantedDays === undefined) {
    return ['lifetime-unknown', 'days remaining are known and the granted '
      + 'lifetime is not, so whether the schedule works in general cannot be '
      + 'decided from this reading.'];
  }
  return ['fits', 'the rotation interval is inside the granted lifetime, so the '
    + 'schedule works on its own terms.'];
}

/** What a missing expiry header means for this class. Pure. [state, detail]. */
export function expiryAbsentMeaning(kind) {
  if (kind === 'classic PAT') {
    return ['no-expiry-on-this-class', 'a classic token with no expiry emits no '
      + 'header. That is not reassurance: a credential that never expires is a '
      + 'larger exposure than one that does, and it has its own note.'];
  }
  if (kind === 'App installation token' || kind === 'App refresh token') {
    return ['short-lived-by-design', 'this class is minted for about an hour, so '
      + 'an absent header is the expected state and nothing here needs an alarm.'];
  }
  return ['expiry-not-reported', 'no expiry header came back for a class that '
    + 'usually carries one. Either the response was not authenticated or this '
    + 'credential has no expiry at all; check which before concluding anything.'];
}

/** The shape of a policy block, without claiming it. Pure. [state, detail]. */
export function orgProbeVerdict(selfStatus, orgStatus) {
  const mine = Number(selfStatus) || 0;
  const theirs = (orgStatus === null || orgStatus === undefined) ? null : Number(orgStatus);
  if (![200, 204].includes(mine)) {
    return ['credential-dead', 'the credential did not authenticate at all, so '
      + "nothing here is about one organization's policy."];
  }
  if (theirs === null) {
    return ['org-not-probed', 'no organization was probed, so the reading is '
      + 'about the credential in general rather than about one namespace.'];
  }
  if ([200, 204].includes(theirs)) {
    return ['org-reachable', 'the organization answered, so nothing is blocking '
      + 'this credential there right now.'];
  }
  if ([401, 403, 404].includes(theirs)) {
    return ['refused-by-one-org', 'the credential authenticates globally and is '
      + 'refused at this organization. Three things produce that shape: a token '
      + 'over a lifetime policy, a fine-grained token still waiting for owner '
      + 'approval, and a SAML authorization that has lapsed. Each has its own '
      + 'note; this reading narrows the search rather than ending it.'];
  }
  return ['org-probe-inconclusive', `HTTP ${orgStatus} from the organization is `
    + 'not a refusal or a success, so it says nothing about policy.'];
}

/** Which fine-grained tokens reaching the org die when. Pure. */
export function grantsOverCap(grants, orgMaxDays, nowEpoch) {
  const out = [];
  for (const grant of grants || []) {
    if (!grant || typeof grant !== 'object') continue;
    const owner = (grant.owner && grant.owner.login) || null;
    const expires = grant.token_expires_at ? parseStamp(grant.token_expires_at) : null;
    const remaining = expires ? daysBetween(nowEpoch, expires) : null;
    out.push({
      owner,
      token_expires_at: grant.token_expires_at ?? null,
      expired: Boolean(grant.token_expired),
      days_remaining: remaining === null ? null : Math.round(remaining * 10) / 10,
      no_expiry: (grant.token_expires_at ?? null) === null,
      over_declared_cap: (orgMaxDays !== null && orgMaxDays !== undefined
        && (grant.token_expires_at ?? null) === null),
    });
  }
  out.sort((a, b) => {
    if (a.days_remaining === null) return 1;
    if (b.days_remaining === null) return -1;
    return a.days_remaining - b.days_remaining;
  });
  return out;
}

/** The finding, in one state. Pure. [state, detail]. */
export function verdict(capState, fitState, appliesState) {
  if (['different-class', 'minted-hourly', 'different-model'].includes(appliesState)) {
    return [appliesState, 'a maximum-lifetime policy does not govern this '
      + 'credential class, so this note is not about your problem.'];
  }
  if (capState === 'over-org-cap') {
    return ['blocked-by-lifetime-policy', 'this token is longer-lived than the '
      + 'declared cap, which is the state that gets refused at that '
      + 'organization while every global check on the credential passes.'];
  }
  if (fitState === 'rotation-outlives-token') {
    return ['schedule-cannot-work', 'the rotation interval is longer than any '
      + 'lifetime available here. This is a process finding, not an incident, '
      + 'and it will produce an outage every cycle until the schedule changes.'];
  }
  if (fitState === 'this-cycle-expires-first') {
    return ['rotate-early-this-once', 'this particular token dies before the '
      + 'next scheduled rotation. Bring the rotation forward; the schedule '
      + 'itself is sound.'];
  }
  if (fitState === 'already-expired') {
    return ['expired', 'the expiry has passed, which is the plain expiry case '
      + 'and has its own note.'];
  }
  if (capState.includes('unknown') || fitState.includes('unknown')) {
    return ['lifetime-unknown', 'not enough was supplied to compare periods. '
      + 'The issue date and the rotation interval are both facts only you hold.'];
  }
  return ['within-policy', 'the granted lifetime is inside the declared cap and '
    + 'the rotation interval is inside the lifetime.'];
}

/** The sentence a reader has to act on. Pure. Nothing here rotates. */
export function repair(state, rotationDays, orgMaxDays) {
  if (['blocked-by-lifetime-policy', 'schedule-cannot-work'].includes(state)) {
    const cap = (orgMaxDays === null || orgMaxDays === undefined)
      ? 'the enforced maximum' : orgMaxDays;
    return `shorten the rotation interval to fit inside ${cap} day(s) and alert `
      + 'on the expiry header rather than on a calendar. Where that cadence is '
      + 'impractical, move this job to a GitHub App whose installation tokens '
      + 'are minted hourly and need no rotation at all. Nothing here rotates '
      + 'anything.';
  }
  if (state === 'rotate-early-this-once') {
    return 'bring this rotation forward: the token dies before the next '
      + `scheduled one. The interval of ${rotationDays} day(s) is otherwise fine.`;
  }
  if (state === 'expired') {
    return 'mint a replacement. This is the plain expiry case and the policy '
      + 'comparison is not what failed.';
  }
  if (state === 'lifetime-unknown') {
    return 'supply the issue date recorded when this token was minted and the '
      + 'rotation interval from the runbook, then re-run. Neither is on the wire.';
  }
  if (['different-class', 'minted-hourly', 'different-model'].includes(state)) {
    return 'no action from this note; the credential class is not the one a '
      + 'lifetime policy governs.';
  }
  return 'nothing to repair from this reading.';
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
  if (!token) {
    console.error('set GITHUB_TOKEN (the credential whose lifetime is in question)');
    process.exitCode = 2;
    return;
  }
  const org = process.env.GITHUB_ORG || '';
  const withGrants = process.env.GITHUB_ORG_GRANTS === '1';
  const rotationDays = process.env.GITHUB_ROTATION_DAYS
    ? Number(process.env.GITHUB_ROTATION_DAYS) : null;
  const orgMaxDays = process.env.GITHUB_ORG_MAX_DAYS
    ? Number(process.env.GITHUB_ORG_MAX_DAYS) : null;
  const [made, spent] = readCost(Boolean(org), withGrants);
  console.log(`read cost: ${made} REST request(s), ${spent} of which count `
    + 'against the core quota');

  const kind = tokenKind(token);
  const [appliesState, appliesDetail] = policyApplies(kind);
  console.log(`credential: ${kind}. ${appliesDetail}`);

  const probe = await fetch(`${API}/rate_limit`, { headers: headers(token) });
  const headerBag = {};
  probe.headers.forEach((value, key) => { headerBag[key] = value; });
  const rawExpiry = headerValue(headerBag);
  const now = Date.now() / 1000;
  const expiresEpoch = parseStamp(rawExpiry);
  const remaining = daysBetween(now, expiresEpoch);
  if (rawExpiry) {
    console.log(`expiry header: ${rawExpiry} (`
      + `${remaining === null ? 'unknown' : Math.round(remaining)} day(s) remaining)`);
  } else {
    const [absentState, absentDetail] = expiryAbsentMeaning(kind);
    console.log(`${absentState}: ${absentDetail}`);
  }

  const issuedEpoch = process.env.GITHUB_ISSUED
    ? parseStamp(process.env.GITHUB_ISSUED) : null;
  const granted = grantedLifetimeDays(issuedEpoch, expiresEpoch);
  if (granted !== null) {
    console.log(`granted lifetime: ${Math.round(granted)} day(s), from the issue `
      + 'date you supplied');
  }

  const [capState, capDetail] = capVerdict(granted, orgMaxDays);
  console.log(`${capState}: ${capDetail}`);
  const [fitState, fitDetail] = rotationFit(granted, remaining, rotationDays);
  console.log(`${fitState}: ${fitDetail}`);

  let orgStatus = null;
  if (org) {
    const orgProbe = await fetch(`${API}/orgs/${org}/repos?per_page=1`,
      { headers: headers(token) });
    orgStatus = orgProbe.status;
  }
  const [shapeState, shapeDetail] = orgProbeVerdict(probe.status, orgStatus);
  console.log(`org probe: ${shapeState} - ${shapeDetail}`);

  let grants = [];
  if (withGrants && org) {
    const listing = await fetch(
      `${API}/orgs/${org}/personal-access-tokens?per_page=100`,
      { headers: headers(token) },
    );
    if (listing.status === 200) {
      grants = grantsOverCap(await listing.json(), orgMaxDays, now);
      console.log(`org grants: ${grants.length} fine-grained token(s) reach ${org}`);
    } else {
      console.log(`org grants unreadable (HTTP ${listing.status}). That endpoint `
        + "is usable only by a GitHub App with the organization's personal "
        + 'access token permission.');
    }
  }

  const [state, detail] = verdict(capState, fitState, appliesState);
  console.log(`${state}: ${detail}`);
  const fix = repair(state, rotationDays, orgMaxDays);
  console.log(`repair: ${fix}`);

  console.log(JSON.stringify({
    token_kind: kind,
    policy_applies: appliesState,
    expiry_header: rawExpiry,
    days_remaining: remaining === null ? null : Math.round(remaining * 10) / 10,
    granted_lifetime_days: granted === null ? null : Math.round(granted * 10) / 10,
    declared_org_max_days: orgMaxDays,
    declared_rotation_days: rotationDays,
    cap_state: capState,
    rotation_state: fitState,
    org_probe_state: shapeState,
    org_grants: grants.slice(0, 20),
    state,
    detail,
    repair: fix,
  }, null, 2));
  process.exitCode = ['blocked-by-lifetime-policy', 'schedule-cannot-work',
    'rotate-early-this-once', 'expired'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Everything interesting here is arithmetic on dates, so the suite is fixed epochs rather than anything that moves. The first group is the parser, against the documented header shape and against the ISO instant that also turns up. The middle group is the distinction the note exists for: a token that dies before the next rotation, which is a calendar entry, against a rotation interval longer than any lifetime the policy permits, which is a schedule that can never work. The tokens in the fixtures are obviously fake and far too short to be real. The last group is the honest ones: an unknown issue date stays unknown, and an undeclared cap is not an absent one.",
"test_py_file": "test_github_token_lifetime.py",
"test_js_file": "github-token-lifetime.test.mjs",
"test_py": '''from github_token_lifetime import (
    DEFAULT_FINE_GRAINED_MAX_DAYS, cap_verdict, days_between,
    expiry_absent_meaning, granted_lifetime_days, grants_over_cap,
    header_value, org_probe_verdict, parse_stamp, policy_applies, read_cost,
    repair, rotation_fit, token_kind, verdict,
)

# Obviously fake and far shorter than any real credential.
FINE = "github_pat_FAKE"
CLASSIC = "ghp_FAKE"
INSTALLATION = "ghs_FAKE"

NOW = 1_800_000_000.0
DAY = 86400.0


def test_the_documented_header_shape_parses_and_so_does_the_iso_one():
    assert parse_stamp("2026-09-30 12:00:00 UTC") == 1790769600.0
    assert parse_stamp("2026-09-30T12:00:00Z") == 1790769600.0
    assert parse_stamp("2026-09-30") == 1790726400.0
    assert parse_stamp("not a date") is None
    assert parse_stamp(None) is None
    # A shape it cannot read returns None rather than a plausible wrong date.
    assert parse_stamp("30/09/2026") is None


def test_the_header_is_read_case_insensitively():
    assert header_value({"Github-Authentication-Token-Expiration": "x"}) == "x"
    assert header_value({"unrelated": "y"}) is None
    assert header_value(None) is None


def test_the_granted_lifetime_needs_an_issue_date_and_says_so():
    granted = granted_lifetime_days(NOW - 30 * DAY, NOW + 60 * DAY)
    assert round(granted) == 90
    # Without an issue date the answer is unknown, not a guess.
    assert granted_lifetime_days(None, NOW + 60 * DAY) is None
    state, detail = cap_verdict(None, 90)
    assert state == "lifetime-unknown"
    assert "without an issue date" in detail


def test_a_token_over_the_cap_is_blocked_not_shortened():
    state, detail = cap_verdict(366, 90)
    assert state == "over-org-cap"
    assert "it does not shorten them" in detail
    assert cap_verdict(60, 90)[0] == "within-org-cap"


def test_an_undeclared_cap_is_not_an_absent_one():
    state, detail = cap_verdict(366, None)
    assert state == "cap-not-declared"
    assert "no documented endpoint" in detail


def test_the_schedule_that_can_never_work_is_kept_apart_from_the_one_off():
    # The recurring finding: the interval is longer than any lifetime allowed.
    state, detail = rotation_fit(90, 80, 365)
    assert state == "rotation-outlives-token"
    assert "once per cycle, forever" in detail
    # The one-off: this token dies first, and the schedule itself is fine.
    state, detail = rotation_fit(365, 20, 90)
    assert state == "this-cycle-expires-first"
    assert "A one-off" in detail
    assert rotation_fit(365, 300, 90)[0] == "fits"
    assert rotation_fit(365, -1, 90)[0] == "already-expired"
    assert rotation_fit(None, 300, None)[0] == "rotation-not-declared"


def test_the_two_findings_have_two_different_repairs():
    recurring = verdict("within-org-cap", "rotation-outlives-token", "policy-applies")
    assert recurring[0] == "schedule-cannot-work"
    assert "every cycle" in recurring[1]
    once = verdict("within-org-cap", "this-cycle-expires-first", "policy-applies")
    assert once[0] == "rotate-early-this-once"
    assert "Bring the rotation forward" in once[1]
    assert "GitHub App" in repair("schedule-cannot-work", 365, 90)
    assert "bring this rotation forward" in repair("rotate-early-this-once", 90, None)


def test_being_over_the_cap_outranks_the_schedule():
    # A token already over the cap is being refused now; the schedule is the
    # cause and the block is the symptom, so the block is reported first.
    state, _ = verdict("over-org-cap", "fits", "policy-applies")
    assert state == "blocked-by-lifetime-policy"


def test_the_policy_only_governs_one_credential_class():
    assert policy_applies("fine-grained PAT")[0] == "policy-applies"
    assert str(DEFAULT_FINE_GRAINED_MAX_DAYS) in policy_applies("fine-grained PAT")[1]
    state, detail = policy_applies("classic PAT")
    assert state == "different-class"
    assert "auto-revocation note" in detail
    assert policy_applies("App installation token")[0] == "minted-hourly"
    assert policy_applies("unknown")[0] == "class-unknown"
    assert token_kind(FINE) == "fine-grained PAT"
    assert token_kind(CLASSIC) == "classic PAT"
    assert token_kind(INSTALLATION) == "App installation token"
    assert token_kind("") == "unknown"


def test_a_wrong_class_ends_the_note_rather_than_grading_it():
    state, detail = verdict("cap-not-declared", "fits", "minted-hourly")
    assert state == "minted-hourly"
    assert "not about your problem" in detail
    assert "no action from this note" in repair("minted-hourly", None, None)


def test_the_missing_header_means_different_things_per_class():
    assert expiry_absent_meaning("classic PAT")[0] == "no-expiry-on-this-class"
    assert "larger exposure" in expiry_absent_meaning("classic PAT")[1]
    assert expiry_absent_meaning("App installation token")[0] == "short-lived-by-design"
    assert expiry_absent_meaning("fine-grained PAT")[0] == "expiry-not-reported"


def test_the_org_probe_reports_a_shape_and_names_its_rivals():
    state, detail = org_probe_verdict(200, 403)
    assert state == "refused-by-one-org"
    assert "Three things produce that shape" in detail
    assert "narrows the search rather than ending it" in detail
    assert org_probe_verdict(200, 200)[0] == "org-reachable"
    assert org_probe_verdict(401, 403)[0] == "credential-dead"
    assert org_probe_verdict(200, None)[0] == "org-not-probed"


def test_the_fleet_read_sorts_by_which_credential_goes_next():
    grants = [
        {"owner": {"login": "carol"}, "token_expires_at": "2026-12-01 00:00:00 UTC",
         "token_expired": False},
        {"owner": {"login": "alice"}, "token_expires_at": None, "token_expired": False},
        {"owner": {"login": "bob"}, "token_expires_at": "2026-06-01 00:00:00 UTC",
         "token_expired": False},
    ]
    rows = grants_over_cap(grants, 90, NOW)
    assert [r["owner"] for r in rows] == ["bob", "carol", "alice"]
    # A grant with no expiry at all cannot satisfy any maximum lifetime.
    assert rows[-1]["no_expiry"] is True
    assert rows[-1]["over_declared_cap"] is True
    assert grants_over_cap([], 90, NOW) == []


def test_the_free_probe_is_counted_as_free():
    assert read_cost(False, False) == (1, 0)
    assert read_cost(True, False) == (2, 1)
    assert read_cost(True, True) == (3, 2)


def test_days_between_is_signed_and_none_safe():
    assert days_between(NOW, NOW + DAY) == 1.0
    assert days_between(NOW, NOW - DAY) == -1.0
    assert days_between(None, NOW) is None
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DEFAULT_FINE_GRAINED_MAX_DAYS, capVerdict, daysBetween, expiryAbsentMeaning,
  grantedLifetimeDays, grantsOverCap, headerValue, orgProbeVerdict, parseStamp,
  policyApplies, readCost, repair, rotationFit, tokenKind, verdict,
} from './github-token-lifetime.mjs';

// Obviously fake and far shorter than any real credential.
const FINE = 'github_pat_FAKE';
const CLASSIC = 'ghp_FAKE';
const INSTALLATION = 'ghs_FAKE';

const NOW = 1800000000;
const DAY = 86400;

test('the documented header shape parses and so does the iso one', () => {
  assert.equal(parseStamp('2026-09-30 12:00:00 UTC'), 1790769600);
  assert.equal(parseStamp('2026-09-30T12:00:00Z'), 1790769600);
  assert.equal(parseStamp('2026-09-30'), 1790726400);
  assert.equal(parseStamp('not a date'), null);
  assert.equal(parseStamp(null), null);
  assert.equal(parseStamp('30/09/2026'), null);
});

test('the header is read case insensitively', () => {
  assert.equal(headerValue({ 'Github-Authentication-Token-Expiration': 'x' }), 'x');
  assert.equal(headerValue({ unrelated: 'y' }), null);
  assert.equal(headerValue(null), null);
});

test('the granted lifetime needs an issue date and says so', () => {
  assert.equal(Math.round(grantedLifetimeDays(NOW - 30 * DAY, NOW + 60 * DAY)), 90);
  assert.equal(grantedLifetimeDays(null, NOW + 60 * DAY), null);
  const [state, detail] = capVerdict(null, 90);
  assert.equal(state, 'lifetime-unknown');
  assert.match(detail, /without an issue date/);
});

test('a token over the cap is blocked not shortened', () => {
  const [state, detail] = capVerdict(366, 90);
  assert.equal(state, 'over-org-cap');
  assert.match(detail, /it does not shorten them/);
  assert.equal(capVerdict(60, 90)[0], 'within-org-cap');
});

test('an undeclared cap is not an absent one', () => {
  const [state, detail] = capVerdict(366, null);
  assert.equal(state, 'cap-not-declared');
  assert.match(detail, /no documented endpoint/);
});

test('the schedule that can never work is kept apart from the one off', () => {
  let [state, detail] = rotationFit(90, 80, 365);
  assert.equal(state, 'rotation-outlives-token');
  assert.match(detail, /once per cycle, forever/);
  [state, detail] = rotationFit(365, 20, 90);
  assert.equal(state, 'this-cycle-expires-first');
  assert.match(detail, /A one-off/);
  assert.equal(rotationFit(365, 300, 90)[0], 'fits');
  assert.equal(rotationFit(365, -1, 90)[0], 'already-expired');
  assert.equal(rotationFit(null, 300, null)[0], 'rotation-not-declared');
});

test('the two findings have two different repairs', () => {
  const recurring = verdict('within-org-cap', 'rotation-outlives-token', 'policy-applies');
  assert.equal(recurring[0], 'schedule-cannot-work');
  assert.match(recurring[1], /every cycle/);
  const once = verdict('within-org-cap', 'this-cycle-expires-first', 'policy-applies');
  assert.equal(once[0], 'rotate-early-this-once');
  assert.match(once[1], /Bring the rotation forward/);
  assert.match(repair('schedule-cannot-work', 365, 90), /GitHub App/);
  assert.match(repair('rotate-early-this-once', 90, null), /bring this rotation forward/);
});

test('being over the cap outranks the schedule', () => {
  assert.equal(verdict('over-org-cap', 'fits', 'policy-applies')[0], 'blocked-by-lifetime-policy');
});

test('the policy only governs one credential class', () => {
  assert.equal(policyApplies('fine-grained PAT')[0], 'policy-applies');
  assert.ok(policyApplies('fine-grained PAT')[1]
    .includes(String(DEFAULT_FINE_GRAINED_MAX_DAYS)));
  const [state, detail] = policyApplies('classic PAT');
  assert.equal(state, 'different-class');
  assert.match(detail, /auto-revocation note/);
  assert.equal(policyApplies('App installation token')[0], 'minted-hourly');
  assert.equal(policyApplies('unknown')[0], 'class-unknown');
  assert.equal(tokenKind(FINE), 'fine-grained PAT');
  assert.equal(tokenKind(CLASSIC), 'classic PAT');
  assert.equal(tokenKind(INSTALLATION), 'App installation token');
  assert.equal(tokenKind(''), 'unknown');
});

test('a wrong class ends the note rather than grading it', () => {
  const [state, detail] = verdict('cap-not-declared', 'fits', 'minted-hourly');
  assert.equal(state, 'minted-hourly');
  assert.match(detail, /not about your problem/);
  assert.match(repair('minted-hourly', null, null), /no action from this note/);
});

test('the missing header means different things per class', () => {
  assert.equal(expiryAbsentMeaning('classic PAT')[0], 'no-expiry-on-this-class');
  assert.match(expiryAbsentMeaning('classic PAT')[1], /larger exposure/);
  assert.equal(expiryAbsentMeaning('App installation token')[0], 'short-lived-by-design');
  assert.equal(expiryAbsentMeaning('fine-grained PAT')[0], 'expiry-not-reported');
});

test('the org probe reports a shape and names its rivals', () => {
  const [state, detail] = orgProbeVerdict(200, 403);
  assert.equal(state, 'refused-by-one-org');
  assert.match(detail, /Three things produce that shape/);
  assert.match(detail, /narrows the search rather than ending it/);
  assert.equal(orgProbeVerdict(200, 200)[0], 'org-reachable');
  assert.equal(orgProbeVerdict(401, 403)[0], 'credential-dead');
  assert.equal(orgProbeVerdict(200, null)[0], 'org-not-probed');
});

test('the fleet read sorts by which credential goes next', () => {
  const grants = [
    { owner: { login: 'carol' }, token_expires_at: '2026-12-01 00:00:00 UTC', token_expired: false },
    { owner: { login: 'alice' }, token_expires_at: null, token_expired: false },
    { owner: { login: 'bob' }, token_expires_at: '2026-06-01 00:00:00 UTC', token_expired: false },
  ];
  const rows = grantsOverCap(grants, 90, NOW);
  assert.deepEqual(rows.map((r) => r.owner), ['bob', 'carol', 'alice']);
  assert.equal(rows[rows.length - 1].no_expiry, true);
  assert.equal(rows[rows.length - 1].over_declared_cap, true);
  assert.deepEqual(grantsOverCap([], 90, NOW), []);
});

test('the free probe is counted as free', () => {
  assert.deepEqual(readCost(false, false), [1, 0]);
  assert.deepEqual(readCost(true, false), [2, 1]);
  assert.deepEqual(readCost(true, true), [3, 2]);
});

test('days between is signed and null safe', () => {
  assert.equal(daysBetween(NOW, NOW + DAY), 1);
  assert.equal(daysBetween(NOW, NOW - DAY), -1);
  assert.equal(daysBetween(null, NOW), null);
});
''',
"faq": [
 ("Is this not just the token-expiry note with extra steps?",
  "No, and the difference is which number you watch. That note counts down the days a token has left and alerts you at thirty; it is the right tool when a credential is heading for its own expiry. This one compares the lifetime you were <em>granted</em> against the interval you rotate on, which is a comparison between two periods. An expiry alert fires, somebody rotates, and if the cap is shorter than the cycle the next token has exactly the same problem. The countdown can never surface that, because nothing about it is ever surprising."),
 ("The token still authenticates. How can a lifetime policy be the cause?",
  "Because the policy does not shorten or revoke anything. GitHub's documentation says non-compliant tokens are blocked from accessing the organization, so the credential stays alive and correct and is refused in one namespace. That is why every check anybody runs on it &mdash; <code>GET /user</code>, the personal account, the other organization &mdash; comes back clean, and why the investigation goes to scopes instead."),
 ("Can the script read the organization's maximum-lifetime setting?",
  "Not through any documented endpoint, and pretending otherwise would be the worst thing this note could do. The cap is supplied as a declared number and labelled as declared throughout. What <em>is</em> readable, with a GitHub App holding the organization's personal-access-token permission, is <code>GET /orgs/{org}/personal-access-tokens</code>: every fine-grained token with access to the organization, with <code>token_expires_at</code> and <code>token_expired</code>. That gives you the fleet even though it does not give you the rule."),
 ("Our tokens are classic PATs. Does the cap apply to us?",
  "Not this one. The maximum-lifetime policy is a fine-grained personal access token policy, and classic tokens have no expiry requirement to cap. An organization that wants to constrain classic tokens blocks their access to the organization outright, which produces a different refusal, and a classic token that quietly stops working after a long idle period is the auto-revocation case instead. The script names the class first for exactly this reason."),
 ("What if we genuinely cannot rotate every ninety days?",
  "Then stop trying to make a human-shaped credential do a machine-shaped job. A GitHub App mints installation tokens that live about an hour and are fetched on demand, so there is no lifetime for a policy to cap and no rotation for anybody to schedule or forget. That is a bigger change than editing a runbook, which is why the script only prints it as the alternative when the cadence and the cap genuinely cannot be reconciled."),
],
"related": [
 ("/github/token-expiring-soon/", "The countdown, which is a different number"),
 ("/github/fine-grained-pat-pending-approval/", "The other reason one org refuses a healthy token"),
 ("/github/unused-classic-token-auto-revoked/", "The clock on the class this policy does not cover"),
],
"citations": [CITE_PAT_POLICY, CITE_MANAGING_PATS, CITE_ORG_PATS, CITE_RATE_LIMIT],
},
{
"slug": "outside-collaborator-invisible-org-data",
"title": "An outside collaborator has repos in an org, not the org",
"description": "Repository reads work and every org-level call 404s. The account holds repositories inside the organization without being in it, and no scope fixes that.",
"h1": "An outside collaborator has repos in an org, not the org",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api outside collaborator 404 org endpoints",
             "github orgs teams 404 not a member",
             "github user repos affiliation collaborator",
             "outside collaborator organization api access",
             "fine-grained token outside collaborator limitation"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The integration reads three repositories in the customer's organization perfectly well, and has done for months. Then somebody adds a feature that needs the team list, and <code>GET /orgs/{org}/teams</code> returns 404. Which is odd, because the repositories are right there and they belong to that organization. So the token gets <code>read:org</code> added, and it is still 404. Then <code>admin:org</code>, briefly, against everybody's better judgement, and it is still 404. The account was never an organization member. It is an outside collaborator, which means it has repositories <em>inside</em> the organization and no standing <em>in</em> the organization, and no scope on earth grants standing.",
"short_answer": """<p>An outside collaborator is granted specific repositories in an organization without being a member of it. Organization-level endpoints require membership, so <code>teams</code>, <code>members</code> and the rest answer 404 for an account whose repository reads work fine. Scopes bound what a token may do on the account's behalf; they cannot give the account a relationship it does not have.</p>
<p>The partition that proves it costs two reads. <code>GET /user/repos?affiliation=organization_member</code> returns the repositories reachable <em>because</em> the account is in an organization; <code>GET /user/repos?affiliation=collaborator</code> returns the ones reachable because somebody added the account to them one at a time. An account with repositories in the organization under <code>collaborator</code> and none under <code>organization_member</code>, and the organization missing from <code>GET /user/orgs</code>, is an outside collaborator, definitively, from the token's own side.</p>
<p>The trap on the way is <code>GET /orgs/{org}/repos</code>, which does not refuse a non-member. It answers 200 with the public repositories and nothing else, and no header says a word about it.</p>""",
"problem": """<p>Every symptom points the wrong way. The 404s are on organization endpoints, the token has organization scopes, and 404 is the status GitHub uses when it will not tell you a private thing exists. That combination reads unmistakably as "the scope is not taking effect", which is a real problem with real causes &mdash; SSO authorization, App installation, fine-grained permissions &mdash; and none of them is this. Widening the token is the first thing anybody tries and it produces no change at all, which is genuinely disorienting because widening a token normally changes something.</p>
<p>The second trap is the endpoint that does not refuse. <code>GET /orgs/{org}/repos</code> answers 200 for a non-member and returns the organization's public repositories. If your integration lists repositories that way, it does not error; it under-reports, silently, and looks like it is working. A customer with forty private repositories and two public ones shows up in your product as a customer with two repositories, and the first person to notice is the customer.</p>
<p>The third is that the relationship is invisible from the account's side unless you go looking for it. Nothing on <code>GET /user</code> says "outside collaborator". There is an endpoint that lists them, <code>GET /orgs/{org}/outside_collaborators</code>, and it needs organization read access &mdash; which the outside collaborator, by definition, does not have. So the one call that names the condition outright is the one call this account cannot make.</p>""",
"why": """<p><strong>Repository access and organization membership are different grants.</strong> Being added to a repository owned by an organization does not put you in the organization; it puts you on the repository. Organization endpoints are gated on membership, and no permission model layered on top &mdash; classic scopes, fine-grained permissions, an App installation &mdash; changes the underlying fact. This is why the scope ladder produces no movement: every rung is bounded by an access the account never had.</p>
<p><strong>The affiliation parameter names the difference out loud.</strong> <code>GET /user/repos</code> takes an <code>affiliation</code> of <code>owner</code>, <code>collaborator</code> or <code>organization_member</code>, and those three are how the account reached each repository. Requesting them separately turns a vague "I can see some of this organization" into a partition, and the partition <em>is</em> the diagnosis: repositories present under <code>collaborator</code> and absent under <code>organization_member</code> is what an outside collaborator looks like and nothing else looks like it.</p>
<p><strong>This is a shorter list with no announcement, which is what separates it from the SAML case.</strong> The section already publishes the note about organization data withheld from a successful response &mdash; and the point of that one is that GitHub <em>tells</em> you, in an <code>X-GitHub-SSO: partial-results</code> header naming the organizations it left out. Nothing announces this. A non-member listing an organization's repositories gets a clean 200, no header, and a shorter array. The script reads that header anyway, precisely so it can say "this is not that note" with evidence rather than by assertion.</p>
<p><strong>The membership redirect cannot separate the two ways of not being a member.</strong> <code>GET /orgs/{org}/members/{username}</code> answers 302 when the requester is not an organization member, which is a genuinely useful signal and belongs to the note about accounts removed by a two-factor requirement. It is not useful <em>here</em>, because an outside collaborator and a former member are both non-members and both get the redirect. What tells them apart is what happens to the repositories: an outside collaborator still reaches theirs, and a removed member reaches nothing.</p>
<p><strong>The credential class can make this worse in a way that is diagnostic.</strong> GitHub documents, among the things fine-grained personal access tokens cannot yet do, contributing to repositories where the user is an outside or repository collaborator. So an outside collaborator can find a classic token working where a fine-grained one does not, on the same repository, with the same person behind it. If swapping the token class changes the answer, that inversion is itself evidence of the role.</p>""",
"steps": [
 {"h": "Ask the token who it is and which organizations it is in",
  "body": """<p><code>GET /user</code> for the login, then <code>GET /user/orgs</code>. If the organization is absent from that list, the account is not a member of it. Read <code>x-github-sso</code> on the same response before believing the absence: a partial result there means the list is incomplete for a completely different reason and the section has a note about that. The script reports which of the two it is looking at.</p>"""},
 {"h": "Partition the repositories by how they were reached",
  "body": """<p>One page of <code>GET /user/repos?affiliation=collaborator</code> and one of <code>affiliation=organization_member</code>, counting the ones owned by the organization in question. Repositories present in the first and absent from the second is the finding. The script reports a count as a floor rather than a total when the <code>Link</code> header shows another page, because an under-count that says it is an under-count is useful and one that does not is a lie.</p>"""},
 {"h": "Take one reading against an organization endpoint that refuses",
  "body": """<p><code>--org-probe</code> reads <code>GET /orgs/{org}/members?per_page=1</code> and records the status. A 404 there beside a 200 on a repository in the same organization is the pair to put in the ticket. It is a reading rather than a conclusion: the script pairs it with the affiliation partition instead of concluding from it alone.</p>"""},
 {"h": "Notice the endpoint that does not refuse",
  "body": """<p>The script explicitly reports what <code>GET /orgs/{org}/repos</code> will do for this role, which is answer 200 with the public repositories only. Any inventory built on that call is under-reporting rather than failing, and it will keep looking healthy. This is the part worth taking back to the code, because it is the bug that has no error message attached to it.</p>"""},
 {"h": "Decide which of the two repairs you actually want",
  "body": """<p>Either the account becomes an organization member with a role, which somebody with organization admin has to do and which is a change in the customer's security posture, or the integration stops making organization-level calls and works at repository scope where its access genuinely is. The script prints both and adds nothing to anything; an invitation is a decision, not a diagnostic step.</p>"""},
],
"verify": """<p>Once the account is a member, the same run finds the organization in <code>GET /user/orgs</code> and the repositories move from <code>collaborator</code> to <code>organization_member</code>.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_outside_collaborator.py acme --org-probe
# read cost: 4 REST request(s) against the core hourly quota
# identity: dana-integration
# membership: acme is not in GET /user/orgs, and no partial-results header
#   accompanied that list, so the absence is a real absence and not the SAML
#   note.
# affiliation partition: 3 repo(s) in acme reached as collaborator,
#   0 reached as organization_member
# org probe: GET /orgs/acme/members?per_page=1 -> HTTP 404
# outside-collaborator: repositories inside the organization, no standing in
#   the organization. No scope grants standing, which is why widening the
#   token changed nothing.
# quiet-failure-ahead: GET /orgs/acme/repos will answer 200 for this account
#   and return public repositories only. An inventory built on it under-reports
#   instead of failing.
# repair: either ask an owner of acme to add dana-integration as a member with
#   a role, or drop the organization-level calls and work at repository scope.
#   Nothing here invites anybody.</code></pre>""",
"code_intro": "Four cheap GETs and one comparison. The comparison is the whole note, so it is pure and it is tested against the case that matters most: an account with repositories in the organization and no membership, which is the only shape that produces this. The <code>Link</code> parsing is pure too, because a count that silently truncates is worse than no count and the boundary between \"three\" and \"at least three\" is one header away.",
"py_file": "github_outside_collaborator.py",
"py": '''"""Tell an outside collaborator from a member with a narrow token.

Read only. Four cheap GETs. Nothing is invited, added or promoted: making an
account an organization member is a decision about who is inside a company's
organization, and this script prints the request rather than making it.

The point of the note: an outside collaborator holds specific repositories
inside an organization without being in the organization. Repository reads
work, organization reads do not, and no scope closes the gap because a scope
bounds what a token may do on the account's behalf rather than granting the
account a relationship.

What this can and cannot see: GET /orgs/{org}/outside_collaborators names the
condition outright and needs organization read access, which is exactly what
this account lacks. So the diagnosis is made from the token's own side, by
partitioning its repositories by the affiliation that reached them.

Environment:

    GITHUB_TOKEN    the token the failing integration holds
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_outside_collaborator")

API = "https://api.github.com"
UA = "github-outside-collaborator/1.0"

# The three ways GET /user/repos says an account reached a repository.
AFFILIATIONS = ("owner", "collaborator", "organization_member")


def read_cost(with_org_probe):
    """REST requests this run will spend. Pure. Printed before any are spent."""
    return 3 + (1 if with_org_probe else 0)


def header_value(headers, name):
    """Case-insensitive header read against a plain dict. Pure."""
    if not isinstance(headers, dict):
        return None
    wanted = str(name).lower()
    for key, value in headers.items():
        if str(key).lower() == wanted:
            return value
    return None


def has_next_page(link_header):
    """Is there another page after this one. Pure. No regular expression.

    Used to turn a count into a floor. A number that admits it is a lower bound
    is useful; one that quietly truncates is the same bug this note is about,
    committed by the diagnostic instead of the integration.
    """
    for part in str(link_header or "").split(","):
        if 'rel="next"' in part.replace("'", '"').replace(" ", ""):
            return True
        if 'rel="next"' in part:
            return True
    return False


def sso_reading(headers):
    """Is this response's shortness announced. Pure. (state, detail).

    Read so the script can say "this is not the SAML note" with evidence. That
    note owns organization data withheld from a 200 and announced in a header;
    the case here announces nothing at all.
    """
    value = header_value(headers, "x-github-sso")
    if not value:
        return ("no-sso-header",
                "no partial-results header accompanied this list, so nothing "
                "was announced as withheld. The SAML note is about the case "
                "where GitHub does tell you.")
    if "partial-results" in str(value):
        return ("sso-partial-results",
                "this list is explicitly incomplete: GitHub withheld "
                "organizations this token is not SSO-authorized for and said "
                "so in the header. That is a different note, and any "
                "membership conclusion from this list is unsafe.")
    return ("sso-header-present",
            "an SSO header came back without a partial-results marker. Nothing "
            "is stated as withheld, but treat the list with care.")


def is_member(orgs, org):
    """Does GET /user/orgs list this organization. Pure."""
    wanted = str(org or "").lower()
    for entry in orgs or []:
        if isinstance(entry, dict) and str(entry.get("login") or "").lower() == wanted:
            return True
    return False


def repos_in_org(repos, org):
    """Full names of the repositories in this organization. Pure."""
    wanted = str(org or "").lower()
    out = []
    for repo in repos or []:
        if not isinstance(repo, dict):
            continue
        owner = str(((repo.get("owner") or {}).get("login")) or "").lower()
        if owner == wanted:
            out.append(repo.get("full_name"))
    return out


def counted(names, more_pages):
    """A count, honest about being a floor. Pure. (count, exact, phrase)."""
    total = len(names or [])
    if more_pages:
        return (total, False, "at least %d" % total)
    return (total, True, str(total))


def role_verdict(member, collaborator_count, member_affiliated_count):
    """Which relationship the account has. Pure. (state, detail).

    Four states, and three of them send you somewhere else. The one this note
    owns is the account with repositories in the organization and no membership.
    """
    if member and member_affiliated_count > 0:
        return ("organization-member",
                "the organization is in this account's membership list and its "
                "repositories arrive under organization_member. Whatever is "
                "failing, it is not this.")
    if member and member_affiliated_count == 0:
        return ("member-with-no-implicit-repos",
                "the account is a member and reaches no repository through "
                "that membership. That is what a base permission of none looks "
                "like organization-wide, and it has its own note.")
    if not member and collaborator_count > 0:
        return ("outside-collaborator",
                "repositories inside the organization, no standing in the "
                "organization. No scope grants standing, which is why widening "
                "the token changes nothing.")
    return ("no-relationship",
            "not a member and no repositories in this organization reachable "
            "as a collaborator. An account that used to have access and now "
            "has none is a removal rather than a role, and that has its own "
            "note.")


def org_endpoint_expectation(role):
    """What organization endpoints will do for this role. Pure. dict.

    The second entry is the one worth carrying back to the code: it does not
    fail, it under-reports.
    """
    if role == "organization-member":
        return {"members-and-teams": "answer for a member",
                "org-repos-listing": "returns the repositories a member may see",
                "outside-collaborators-listing": "needs organization read access"}
    return {
        "members-and-teams": "refuse a non-member, and 404 rather than 403 so "
                             "nothing is confirmed to exist",
        "org-repos-listing": "answers 200 and returns the public repositories "
                             "only. This does not fail; it under-reports, with "
                             "no header and no error.",
        "outside-collaborators-listing": "names this condition outright and "
                                         "needs organization read access, "
                                         "which this account does not have",
    }


def token_class_caveat(token):
    """A documented gap that can invert the diagnosis. Pure. (state, detail)."""
    value = (token or "").strip()
    if value.startswith("github_pat_"):
        return ("fine-grained-gap",
                "GitHub documents, among the things fine-grained tokens cannot "
                "yet do, contributing to repositories where the user is an "
                "outside or repository collaborator. If a classic token works "
                "where this one does not, that inversion is evidence of the "
                "role rather than a bug in your code.")
    if value.startswith("ghp_"):
        return ("classic-token",
                "a classic token is not subject to the documented fine-grained "
                "gap for outside collaborators, so a difference between the "
                "two classes is worth testing before blaming anything else.")
    return ("class-not-recognised",
            "the credential class could not be named from its prefix, so the "
            "fine-grained caveat cannot be applied either way.")


def org_probe_reading(repo_status, org_status):
    """One repository read against one organization read. Pure. (state, detail)."""
    repo = None if repo_status is None else int(repo_status)
    org = None if org_status is None else int(org_status)
    if org is None:
        return ("org-not-probed",
                "no organization endpoint was probed, so the partition is the "
                "only evidence here.")
    if repo is not None and repo == 200 and org == 404:
        return ("repo-yes-org-no",
                "a repository in the organization answers and an organization "
                "endpoint does not. That pair is the sentence to put in the "
                "ticket.")
    if org in (200, 204):
        return ("org-reachable",
                "the organization endpoint answered, so membership is not what "
                "is missing.")
    if org in (401, 403):
        return ("org-refused-not-hidden",
                "a refusal rather than a 404 points at a credential or a "
                "policy rather than at membership. Sort that first.")
    return ("org-probe-inconclusive",
            "the pair of statuses does not describe a membership problem.")


def verdict(role, sso_state):
    """The finding, in one state. Pure. (state, detail)."""
    if sso_state == "sso-partial-results":
        return ("membership-list-incomplete",
                "the organization list this conclusion would rest on is "
                "explicitly partial, so no membership answer from it can be "
                "trusted. Authorize the token for SSO and re-run.")
    return (role,
            "this is the relationship the readings describe." if role
            else "no relationship could be determined.")


def repair(state, org, login):
    """The sentence a reader has to act on. Pure. Nothing here invites anybody."""
    if state == "outside-collaborator":
        return ("either ask an owner of %s to add %s as a member with an "
                "appropriate role, which is a change to who is inside that "
                "organization, or drop the organization-level calls and work "
                "at repository scope where this account's access actually is. "
                "Nothing here invites anybody." % (org, login))
    if state == "member-with-no-implicit-repos":
        return ("read the organization's default repository permission before "
                "anything else; an organization-wide default of none produces "
                "exactly this and has its own note.")
    if state == "no-relationship":
        return ("find out whether this account was removed from the "
                "organization rather than never added. A removal leaves a "
                "healthy token with no access at all.")
    if state == "membership-list-incomplete":
        return ("authorize this token for the organization's SSO and re-run. "
                "Until then the membership list is not evidence.")
    return "nothing to repair from this reading."


def get(session, path):
    """One GET. Returns the response object."""
    return session.get(API + path, timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("org", help="the organization whose data is invisible")
    parser.add_argument("--org-probe", action="store_true",
                        help="also read one organization-level endpoint")
    parser.add_argument("--repo",
                        help="a repository in that org to pair the probe with, "
                             "as owner/name")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (the token the failing integration holds)")
        return 2

    log.info("read cost: %d REST request(s) against the core hourly quota",
             read_cost(args.org_probe))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub refuses requests with no User-Agent before it looks at auth.
        "User-Agent": UA,
    })

    class_state, class_detail = token_class_caveat(token)
    log.info("%s: %s", class_state, class_detail)

    me = get(session, "/user")
    login = (me.json() or {}).get("login") if me.status_code == 200 else None
    log.info("identity: %s", login or "unreadable")

    orgs_response = get(session, "/user/orgs?per_page=100")
    orgs = orgs_response.json() if orgs_response.status_code == 200 else []
    sso_state, sso_detail = sso_reading(dict(orgs_response.headers))
    member = is_member(orgs, args.org)
    log.info("membership: %s is %sin GET /user/orgs. %s", args.org,
             "" if member else "not ", sso_detail)

    partition = {}
    for affiliation in ("collaborator", "organization_member"):
        response = get(session, "/user/repos?affiliation=%s&per_page=100"
                       % affiliation)
        names = repos_in_org(response.json() if response.status_code == 200 else [],
                             args.org)
        more = has_next_page(header_value(dict(response.headers), "link"))
        total, exact, phrase = counted(names, more)
        partition[affiliation] = {"count": total, "exact": exact,
                                  "phrase": phrase, "names": names[:20]}
    log.info("affiliation partition: %s repo(s) in %s reached as collaborator, "
             "%s reached as organization_member",
             partition["collaborator"]["phrase"], args.org,
             partition["organization_member"]["phrase"])

    org_status, repo_status = None, None
    if args.org_probe:
        org_status = get(session, "/orgs/%s/members?per_page=1" % args.org).status_code
        log.info("org probe: GET /orgs/%s/members?per_page=1 -> HTTP %s",
                 args.org, org_status)
    if args.repo:
        repo_status = get(session, "/repos/%s" % args.repo).status_code
        log.info("repo probe: GET /repos/%s -> HTTP %s", args.repo, repo_status)
    probe_state, probe_detail = org_probe_reading(repo_status, org_status)
    log.info("%s: %s", probe_state, probe_detail)

    role, role_detail = role_verdict(member,
                                     partition["collaborator"]["count"],
                                     partition["organization_member"]["count"])
    log.info("%s: %s", role, role_detail)

    expectation = org_endpoint_expectation(role)
    log.info("quiet-failure-ahead: %s", expectation["org-repos-listing"])

    state, detail = verdict(role, sso_state)
    fix = repair(state, args.org, login or "this account")
    log.info("repair: %s", fix)

    print(json.dumps({
        "organization": args.org,
        "login": login,
        "is_member": member,
        "sso_state": sso_state,
        "affiliation_partition": partition,
        "org_probe_status": org_status,
        "repo_probe_status": repo_status,
        "probe_state": probe_state,
        "token_class_state": class_state,
        "org_endpoint_expectation": expectation,
        "state": state,
        "detail": detail,
        "repair": fix,
    }, indent=2, default=str))
    return 1 if state in ("outside-collaborator", "member-with-no-implicit-repos",
                          "no-relationship", "membership-list-incomplete") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-outside-collaborator.mjs",
"js": '''/**
 * Tell an outside collaborator from a member with a narrow token.
 *
 * Read only. Four cheap GETs. Nothing is invited, added or promoted: making an
 * account an organization member is a decision about who is inside a company's
 * organization, and this script prints the request rather than making it.
 *
 * An outside collaborator holds specific repositories inside an organization
 * without being in the organization. No scope closes that gap, because a scope
 * bounds what a token may do on the account's behalf rather than granting the
 * account a relationship.
 *
 * Environment:
 *   GITHUB_TOKEN      the token the failing integration holds
 *   GITHUB_ORG        the organization whose data is invisible
 *   GITHUB_ORG_PROBE  set to 1 to read one organization-level endpoint
 *   GITHUB_REPO       optional owner/name in that org to pair the probe with
 */
const API = 'https://api.github.com';
const UA = 'github-outside-collaborator/1.0';

/** The three ways GET /user/repos says an account reached a repository. */
export const AFFILIATIONS = ['owner', 'collaborator', 'organization_member'];

/** REST requests this run will spend. Pure. */
export function readCost(withOrgProbe) {
  return 3 + (withOrgProbe ? 1 : 0);
}

/** Case-insensitive header read against a plain object. Pure. */
export function headerValue(headers, name) {
  if (!headers || typeof headers !== 'object') return null;
  const wanted = String(name).toLowerCase();
  for (const key of Object.keys(headers)) {
    if (key.toLowerCase() === wanted) return headers[key];
  }
  return null;
}

/** Is there another page after this one. Pure. Turns a count into a floor. */
export function hasNextPage(linkHeader) {
  for (const part of String(linkHeader ?? '').split(',')) {
    if (part.includes('rel="next"')) return true;
    if (part.split(' ').join('').includes('rel="next"')) return true;
  }
  return false;
}

/** Is this response's shortness announced. Pure. [state, detail]. */
export function ssoReading(headers) {
  const value = headerValue(headers, 'x-github-sso');
  if (!value) {
    return ['no-sso-header', 'no partial-results header accompanied this list, '
      + 'so nothing was announced as withheld. The SAML note is about the case '
      + 'where GitHub does tell you.'];
  }
  if (String(value).includes('partial-results')) {
    return ['sso-partial-results', 'this list is explicitly incomplete: GitHub '
      + 'withheld organizations this token is not SSO-authorized for and said '
      + 'so in the header. That is a different note, and any membership '
      + 'conclusion from this list is unsafe.'];
  }
  return ['sso-header-present', 'an SSO header came back without a '
    + 'partial-results marker. Nothing is stated as withheld, but treat the '
    + 'list with care.'];
}

/** Does GET /user/orgs list this organization. Pure. */
export function isMember(orgs, org) {
  const wanted = String(org ?? '').toLowerCase();
  for (const entry of orgs || []) {
    if (entry && String(entry.login ?? '').toLowerCase() === wanted) return true;
  }
  return false;
}

/** Full names of the repositories in this organization. Pure. */
export function reposInOrg(repos, org) {
  const wanted = String(org ?? '').toLowerCase();
  const out = [];
  for (const repo of repos || []) {
    if (!repo || typeof repo !== 'object') continue;
    const owner = String((repo.owner && repo.owner.login) || '').toLowerCase();
    if (owner === wanted) out.push(repo.full_name);
  }
  return out;
}

/** A count, honest about being a floor. Pure. [count, exact, phrase]. */
export function counted(names, morePages) {
  const total = (names || []).length;
  if (morePages) return [total, false, `at least ${total}`];
  return [total, true, String(total)];
}

/** Which relationship the account has. Pure. [state, detail]. */
export function roleVerdict(member, collaboratorCount, memberAffiliatedCount) {
  if (member && memberAffiliatedCount > 0) {
    return ['organization-member', "the organization is in this account's "
      + 'membership list and its repositories arrive under organization_member. '
      + 'Whatever is failing, it is not this.'];
  }
  if (member && memberAffiliatedCount === 0) {
    return ['member-with-no-implicit-repos', 'the account is a member and '
      + 'reaches no repository through that membership. That is what a base '
      + 'permission of none looks like organization-wide, and it has its own note.'];
  }
  if (!member && collaboratorCount > 0) {
    return ['outside-collaborator', 'repositories inside the organization, no '
      + 'standing in the organization. No scope grants standing, which is why '
      + 'widening the token changes nothing.'];
  }
  return ['no-relationship', 'not a member and no repositories in this '
    + 'organization reachable as a collaborator. An account that used to have '
    + 'access and now has none is a removal rather than a role, and that has '
    + 'its own note.'];
}

/** What organization endpoints will do for this role. Pure. */
export function orgEndpointExpectation(role) {
  if (role === 'organization-member') {
    return {
      'members-and-teams': 'answer for a member',
      'org-repos-listing': 'returns the repositories a member may see',
      'outside-collaborators-listing': 'needs organization read access',
    };
  }
  return {
    'members-and-teams': 'refuse a non-member, and 404 rather than 403 so '
      + 'nothing is confirmed to exist',
    'org-repos-listing': 'answers 200 and returns the public repositories only. '
      + 'This does not fail; it under-reports, with no header and no error.',
    'outside-collaborators-listing': 'names this condition outright and needs '
      + 'organization read access, which this account does not have',
  };
}

/** A documented gap that can invert the diagnosis. Pure. [state, detail]. */
export function tokenClassCaveat(token) {
  const value = String(token ?? '').trim();
  if (value.startsWith('github_pat_')) {
    return ['fine-grained-gap', 'GitHub documents, among the things '
      + 'fine-grained tokens cannot yet do, contributing to repositories where '
      + 'the user is an outside or repository collaborator. If a classic token '
      + 'works where this one does not, that inversion is evidence of the role '
      + 'rather than a bug in your code.'];
  }
  if (value.startsWith('ghp_')) {
    return ['classic-token', 'a classic token is not subject to the documented '
      + 'fine-grained gap for outside collaborators, so a difference between '
      + 'the two classes is worth testing before blaming anything else.'];
  }
  return ['class-not-recognised', 'the credential class could not be named from '
    + 'its prefix, so the fine-grained caveat cannot be applied either way.'];
}

/** One repository read against one organization read. Pure. [state, detail]. */
export function orgProbeReading(repoStatus, orgStatus) {
  const repo = (repoStatus === null || repoStatus === undefined) ? null : Number(repoStatus);
  const org = (orgStatus === null || orgStatus === undefined) ? null : Number(orgStatus);
  if (org === null) {
    return ['org-not-probed', 'no organization endpoint was probed, so the '
      + 'partition is the only evidence here.'];
  }
  if (repo === 200 && org === 404) {
    return ['repo-yes-org-no', 'a repository in the organization answers and an '
      + 'organization endpoint does not. That pair is the sentence to put in '
      + 'the ticket.'];
  }
  if ([200, 204].includes(org)) {
    return ['org-reachable', 'the organization endpoint answered, so membership '
      + 'is not what is missing.'];
  }
  if ([401, 403].includes(org)) {
    return ['org-refused-not-hidden', 'a refusal rather than a 404 points at a '
      + 'credential or a policy rather than at membership. Sort that first.'];
  }
  return ['org-probe-inconclusive', 'the pair of statuses does not describe a '
    + 'membership problem.'];
}

/** The finding, in one state. Pure. [state, detail]. */
export function verdict(role, ssoState) {
  if (ssoState === 'sso-partial-results') {
    return ['membership-list-incomplete', 'the organization list this conclusion '
      + 'would rest on is explicitly partial, so no membership answer from it '
      + 'can be trusted. Authorize the token for SSO and re-run.'];
  }
  return [role, role ? 'this is the relationship the readings describe.'
    : 'no relationship could be determined.'];
}

/** The sentence a reader has to act on. Pure. Nothing here invites anybody. */
export function repair(state, org, login) {
  if (state === 'outside-collaborator') {
    return `either ask an owner of ${org} to add ${login} as a member with an `
      + 'appropriate role, which is a change to who is inside that '
      + 'organization, or drop the organization-level calls and work at '
      + "repository scope where this account's access actually is. Nothing here "
      + 'invites anybody.';
  }
  if (state === 'member-with-no-implicit-repos') {
    return "read the organization's default repository permission before "
      + 'anything else; an organization-wide default of none produces exactly '
      + 'this and has its own note.';
  }
  if (state === 'no-relationship') {
    return 'find out whether this account was removed from the organization '
      + 'rather than never added. A removal leaves a healthy token with no '
      + 'access at all.';
  }
  if (state === 'membership-list-incomplete') {
    return "authorize this token for the organization's SSO and re-run. Until "
      + 'then the membership list is not evidence.';
  }
  return 'nothing to repair from this reading.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

function bagOf(response) {
  const bag = {};
  response.headers.forEach((value, key) => { bag[key] = value; });
  return bag;
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const org = process.env.GITHUB_ORG;
  if (!token || !org) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_ORG');
    process.exitCode = 2;
    return;
  }
  const withOrgProbe = process.env.GITHUB_ORG_PROBE === '1';
  const repoName = process.env.GITHUB_REPO || '';
  console.log(`read cost: ${readCost(withOrgProbe)} REST request(s) against the `
    + 'core hourly quota');

  const [classState, classDetail] = tokenClassCaveat(token);
  console.log(`${classState}: ${classDetail}`);

  const me = await fetch(`${API}/user`, { headers: headers(token) });
  const login = me.status === 200 ? (await me.json()).login : null;
  console.log(`identity: ${login || 'unreadable'}`);

  const orgsResponse = await fetch(`${API}/user/orgs?per_page=100`,
    { headers: headers(token) });
  const orgs = orgsResponse.status === 200 ? await orgsResponse.json() : [];
  const [ssoState, ssoDetail] = ssoReading(bagOf(orgsResponse));
  const member = isMember(orgs, org);
  console.log(`membership: ${org} is ${member ? '' : 'not '}in GET /user/orgs. ${ssoDetail}`);

  const partition = {};
  for (const affiliation of ['collaborator', 'organization_member']) {
    const response = await fetch(
      `${API}/user/repos?affiliation=${affiliation}&per_page=100`,
      { headers: headers(token) },
    );
    const body = response.status === 200 ? await response.json() : [];
    const names = reposInOrg(body, org);
    const more = hasNextPage(headerValue(bagOf(response), 'link'));
    const [count, exact, phrase] = counted(names, more);
    partition[affiliation] = { count, exact, phrase, names: names.slice(0, 20) };
  }
  console.log(`affiliation partition: ${partition.collaborator.phrase} repo(s) `
    + `in ${org} reached as collaborator, `
    + `${partition.organization_member.phrase} reached as organization_member`);

  let orgStatus = null;
  let repoStatus = null;
  if (withOrgProbe) {
    const probe = await fetch(`${API}/orgs/${org}/members?per_page=1`,
      { headers: headers(token) });
    orgStatus = probe.status;
    console.log(`org probe: GET /orgs/${org}/members?per_page=1 -> HTTP ${orgStatus}`);
  }
  if (repoName) {
    const probe = await fetch(`${API}/repos/${repoName}`, { headers: headers(token) });
    repoStatus = probe.status;
    console.log(`repo probe: GET /repos/${repoName} -> HTTP ${repoStatus}`);
  }
  const [probeState, probeDetail] = orgProbeReading(repoStatus, orgStatus);
  console.log(`${probeState}: ${probeDetail}`);

  const [role, roleDetail] = roleVerdict(member, partition.collaborator.count,
    partition.organization_member.count);
  console.log(`${role}: ${roleDetail}`);

  const expectation = orgEndpointExpectation(role);
  console.log(`quiet-failure-ahead: ${expectation['org-repos-listing']}`);

  const [state, detail] = verdict(role, ssoState);
  const fix = repair(state, org, login || 'this account');
  console.log(`repair: ${fix}`);

  console.log(JSON.stringify({
    organization: org,
    login,
    is_member: member,
    sso_state: ssoState,
    affiliation_partition: partition,
    org_probe_status: orgStatus,
    repo_probe_status: repoStatus,
    probe_state: probeState,
    token_class_state: classState,
    org_endpoint_expectation: expectation,
    state,
    detail,
    repair: fix,
  }, null, 2));
  process.exitCode = ['outside-collaborator', 'member-with-no-implicit-repos',
    'no-relationship', 'membership-list-incomplete'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The core is a four-way sort and each of its arms sends you somewhere different, so each arm gets a test: an outside collaborator, a member whose implicit access was withdrawn organization-wide, a member who is fine, and an account with no relationship at all. Two more groups guard the honest parts. One is the SAML interaction: if the organization list arrived with a partial-results header, no membership conclusion may be drawn from it, and that has to override the sort rather than colour it. The other is the count, which must announce itself as a floor the moment the Link header says there is another page.",
"test_py_file": "test_github_outside_collaborator.py",
"test_js_file": "github-outside-collaborator.test.mjs",
"test_py": '''from github_outside_collaborator import (
    AFFILIATIONS, counted, has_next_page, header_value, is_member,
    org_endpoint_expectation, org_probe_reading, read_cost, repair,
    repos_in_org, role_verdict, sso_reading, token_class_caveat, verdict,
)

# Obviously fake and far shorter than any real credential.
FINE = "github_pat_FAKE"
CLASSIC = "ghp_FAKE"

ORGS = [{"login": "acme"}, {"login": "Other"}]
REPOS = [
    {"full_name": "acme/payments", "owner": {"login": "acme"}},
    {"full_name": "acme/billing", "owner": {"login": "ACME"}},
    {"full_name": "elsewhere/thing", "owner": {"login": "elsewhere"}},
]

NEXT_LINK = ('<https://api.github.com/user/repos?page=2>; rel="next", '
             '<https://api.github.com/user/repos?page=9>; rel="last"')
LAST_ONLY = '<https://api.github.com/user/repos?page=1>; rel="prev"'


def test_the_partition_is_the_diagnosis():
    # Repositories in the org reached as a collaborator, none as a member.
    state, detail = role_verdict(False, 3, 0)
    assert state == "outside-collaborator"
    assert "No scope grants standing" in detail


def test_each_other_arm_of_the_sort_sends_you_somewhere_else():
    assert role_verdict(True, 0, 12)[0] == "organization-member"
    state, detail = role_verdict(True, 0, 0)
    assert state == "member-with-no-implicit-repos"
    assert "base permission of none" in detail
    state, detail = role_verdict(False, 0, 0)
    assert state == "no-relationship"
    assert "removal rather than a role" in detail


def test_an_announced_partial_list_overrides_the_whole_sort():
    # If GET /user/orgs was explicitly incomplete, the membership answer it
    # rests on is not evidence, whatever the affiliation counts say.
    state, detail = verdict("outside-collaborator", "sso-partial-results")
    assert state == "membership-list-incomplete"
    assert "no membership answer from it can be trusted" in detail
    assert verdict("outside-collaborator", "no-sso-header")[0] == "outside-collaborator"


def test_the_absence_of_the_sso_header_is_read_and_reported():
    state, detail = sso_reading({})
    assert state == "no-sso-header"
    assert "The SAML note is about the case where GitHub does tell you." in detail
    partial = {"X-GitHub-SSO": "partial-results; organizations=1,2"}
    assert sso_reading(partial)[0] == "sso-partial-results"
    assert sso_reading({"x-github-sso": "required; url=https://example"})[0] == (
        "sso-header-present")


def test_membership_and_ownership_comparisons_are_case_insensitive():
    assert is_member(ORGS, "ACME") is True
    assert is_member(ORGS, "nope") is False
    assert is_member([], "acme") is False
    assert repos_in_org(REPOS, "acme") == ["acme/payments", "acme/billing"]
    assert repos_in_org(REPOS, "elsewhere") == ["elsewhere/thing"]


def test_a_count_says_when_it_is_only_a_floor():
    assert has_next_page(NEXT_LINK) is True
    assert has_next_page(LAST_ONLY) is False
    assert has_next_page(None) is False
    total, exact, phrase = counted(["a", "b"], True)
    assert (total, exact, phrase) == (2, False, "at least 2")
    assert counted(["a", "b"], False) == (2, True, "2")
    assert counted([], False) == (0, True, "0")


def test_the_endpoint_that_does_not_fail_is_named_as_the_dangerous_one():
    expectation = org_endpoint_expectation("outside-collaborator")
    assert "under-reports" in expectation["org-repos-listing"]
    assert "404 rather than 403" in expectation["members-and-teams"]
    # And the one call that would name the condition needs access this
    # account does not have, which is the joke at the centre of the note.
    assert "organization read access" in expectation["outside-collaborators-listing"]
    assert "answer for a member" in org_endpoint_expectation(
        "organization-member")["members-and-teams"]


def test_the_pair_of_readings_is_the_sentence_for_the_ticket():
    state, detail = org_probe_reading(200, 404)
    assert state == "repo-yes-org-no"
    assert "put in the ticket" in detail
    assert org_probe_reading(200, 200)[0] == "org-reachable"
    assert org_probe_reading(200, 403)[0] == "org-refused-not-hidden"
    assert org_probe_reading(200, None)[0] == "org-not-probed"


def test_the_documented_fine_grained_gap_can_invert_the_answer():
    state, detail = token_class_caveat(FINE)
    assert state == "fine-grained-gap"
    assert "outside or repository collaborator" in detail
    assert token_class_caveat(CLASSIC)[0] == "classic-token"
    assert token_class_caveat("")[0] == "class-not-recognised"


def test_the_repair_offers_two_choices_and_takes_neither():
    fix = repair("outside-collaborator", "acme", "dana-integration")
    assert "ask an owner of acme" in fix
    assert "work at repository scope" in fix
    assert "Nothing here invites anybody" in fix
    assert "default repository permission" in repair(
        "member-with-no-implicit-repos", "acme", "dana")


def test_the_read_cost_and_the_affiliation_names():
    assert read_cost(False) == 3
    assert read_cost(True) == 4
    assert AFFILIATIONS == ("owner", "collaborator", "organization_member")


def test_header_reads_survive_whatever_case_the_client_gives_them():
    assert header_value({"Link": "x"}, "link") == "x"
    assert header_value({"link": "x"}, "LINK") == "x"
    assert header_value(None, "link") is None
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  AFFILIATIONS, counted, hasNextPage, headerValue, isMember,
  orgEndpointExpectation, orgProbeReading, readCost, repair, reposInOrg,
  roleVerdict, ssoReading, tokenClassCaveat, verdict,
} from './github-outside-collaborator.mjs';

// Obviously fake and far shorter than any real credential.
const FINE = 'github_pat_FAKE';
const CLASSIC = 'ghp_FAKE';

const ORGS = [{ login: 'acme' }, { login: 'Other' }];
const REPOS = [
  { full_name: 'acme/payments', owner: { login: 'acme' } },
  { full_name: 'acme/billing', owner: { login: 'ACME' } },
  { full_name: 'elsewhere/thing', owner: { login: 'elsewhere' } },
];

const NEXT_LINK = '<https://api.github.com/user/repos?page=2>; rel="next", '
  + '<https://api.github.com/user/repos?page=9>; rel="last"';
const LAST_ONLY = '<https://api.github.com/user/repos?page=1>; rel="prev"';

test('the partition is the diagnosis', () => {
  const [state, detail] = roleVerdict(false, 3, 0);
  assert.equal(state, 'outside-collaborator');
  assert.match(detail, /No scope grants standing/);
});

test('each other arm of the sort sends you somewhere else', () => {
  assert.equal(roleVerdict(true, 0, 12)[0], 'organization-member');
  let [state, detail] = roleVerdict(true, 0, 0);
  assert.equal(state, 'member-with-no-implicit-repos');
  assert.match(detail, /base permission of none/);
  [state, detail] = roleVerdict(false, 0, 0);
  assert.equal(state, 'no-relationship');
  assert.match(detail, /removal rather than a role/);
});

test('an announced partial list overrides the whole sort', () => {
  const [state, detail] = verdict('outside-collaborator', 'sso-partial-results');
  assert.equal(state, 'membership-list-incomplete');
  assert.match(detail, /no membership answer from it can be trusted/);
  assert.equal(verdict('outside-collaborator', 'no-sso-header')[0], 'outside-collaborator');
});

test('the absence of the sso header is read and reported', () => {
  const [state, detail] = ssoReading({});
  assert.equal(state, 'no-sso-header');
  assert.match(detail, /The SAML note is about the case where GitHub does tell you\\./);
  assert.equal(ssoReading({ 'X-GitHub-SSO': 'partial-results; organizations=1,2' })[0],
    'sso-partial-results');
  assert.equal(ssoReading({ 'x-github-sso': 'required; url=https://example' })[0],
    'sso-header-present');
});

test('membership and ownership comparisons are case insensitive', () => {
  assert.equal(isMember(ORGS, 'ACME'), true);
  assert.equal(isMember(ORGS, 'nope'), false);
  assert.equal(isMember([], 'acme'), false);
  assert.deepEqual(reposInOrg(REPOS, 'acme'), ['acme/payments', 'acme/billing']);
  assert.deepEqual(reposInOrg(REPOS, 'elsewhere'), ['elsewhere/thing']);
});

test('a count says when it is only a floor', () => {
  assert.equal(hasNextPage(NEXT_LINK), true);
  assert.equal(hasNextPage(LAST_ONLY), false);
  assert.equal(hasNextPage(null), false);
  assert.deepEqual(counted(['a', 'b'], true), [2, false, 'at least 2']);
  assert.deepEqual(counted(['a', 'b'], false), [2, true, '2']);
  assert.deepEqual(counted([], false), [0, true, '0']);
});

test('the endpoint that does not fail is named as the dangerous one', () => {
  const expectation = orgEndpointExpectation('outside-collaborator');
  assert.match(expectation['org-repos-listing'], /under-reports/);
  assert.match(expectation['members-and-teams'], /404 rather than 403/);
  assert.match(expectation['outside-collaborators-listing'], /organization read access/);
  assert.match(orgEndpointExpectation('organization-member')['members-and-teams'],
    /answer for a member/);
});

test('the pair of readings is the sentence for the ticket', () => {
  const [state, detail] = orgProbeReading(200, 404);
  assert.equal(state, 'repo-yes-org-no');
  assert.match(detail, /put in the ticket/);
  assert.equal(orgProbeReading(200, 200)[0], 'org-reachable');
  assert.equal(orgProbeReading(200, 403)[0], 'org-refused-not-hidden');
  assert.equal(orgProbeReading(200, null)[0], 'org-not-probed');
});

test('the documented fine grained gap can invert the answer', () => {
  const [state, detail] = tokenClassCaveat(FINE);
  assert.equal(state, 'fine-grained-gap');
  assert.match(detail, /outside or repository collaborator/);
  assert.equal(tokenClassCaveat(CLASSIC)[0], 'classic-token');
  assert.equal(tokenClassCaveat('')[0], 'class-not-recognised');
});

test('the repair offers two choices and takes neither', () => {
  const fix = repair('outside-collaborator', 'acme', 'dana-integration');
  assert.match(fix, /ask an owner of acme/);
  assert.match(fix, /work at repository scope/);
  assert.match(fix, /Nothing here invites anybody/);
  assert.match(repair('member-with-no-implicit-repos', 'acme', 'dana'),
    /default repository permission/);
});

test('the read cost and the affiliation names', () => {
  assert.equal(readCost(false), 3);
  assert.equal(readCost(true), 4);
  assert.deepEqual(AFFILIATIONS, ['owner', 'collaborator', 'organization_member']);
});

test('header reads survive whatever case the client gives them', () => {
  assert.equal(headerValue({ Link: 'x' }, 'link'), 'x');
  assert.equal(headerValue({ link: 'x' }, 'LINK'), 'x');
  assert.equal(headerValue(null, 'link'), null);
});
''',
"faq": [
 ("How is this different from the note about SSO withholding organizations?",
  "That note is about GitHub telling you it left something out. A cross-organization list returns 200 and an <code>X-GitHub-SSO: partial-results</code> header naming the organizations withheld, and the finding is that header on a successful response. Here nothing is announced: an outside collaborator listing an organization's repositories gets a clean 200 with a shorter array and no header at all. The script reads that header specifically so it can rule the other note out with evidence &mdash; and if the header <em>is</em> there, it stops and says so, because a membership conclusion drawn from an admittedly partial list is worthless."),
 ("Would <code>GET /orgs/{org}/members/{me}</code> not settle this faster?",
  "It answers, and it does not settle it. That endpoint returns 302 when the requester is not an organization member, which is a genuinely useful signal and belongs to the note about accounts removed by a two-factor requirement. The trouble here is that an outside collaborator and a former member are both non-members and both get the redirect. The thing that separates them is the repositories: an outside collaborator still reaches theirs and a removed member reaches nothing, which is why the diagnosis is built on the affiliation partition instead."),
 ("Why does adding <code>read:org</code> not help?",
  "Because a scope is an upper bound on what a token may do <em>on the account's behalf</em>, not a grant of access to the account. The account is not in the organization, so there is no organization access for the scope to permit. This is the same reason the section's note about a repository role exists: the token and the relationship are two different things, and only one of them is something you can change by editing a token."),
 ("Can the script confirm it by listing the outside collaborators?",
  "That is the endpoint that would say it outright &mdash; <code>GET /orgs/{org}/outside_collaborators</code> &mdash; and it needs organization read access, which is precisely what an outside collaborator does not have. So the one call that names the condition is the one call this account cannot make. Where you happen to hold an organization credential as well, run it and the answer is immediate; from the affected token, the partition is the evidence available and it is sufficient."),
 ("Our repository listing looks fine. Are we affected?",
  "Check which call builds it. <code>GET /orgs/{org}/repos</code> does not refuse a non-member; it answers 200 with the public repositories and stops. An integration built on that does not raise, does not log an error and does not alert &mdash; it just shows a customer with forty repositories as a customer with two. That silent version is more expensive than the 404s, because the 404s at least send somebody to look."),
],
"related": [
 ("/github/saml-partial-results/", "The other short list, and the header that announces it"),
 ("/github/org-2fa-requirement-removed-member/", "The other way to stop being a member"),
 ("/github/org-base-permission-changed/", "When the account is a member and the repos still vanish"),
],
"citations": [CITE_OUTSIDE_COLLABORATORS, CITE_ADDING_OUTSIDE, CITE_USER_REPOS, CITE_MANAGING_PATS],
},
{
"slug": "enterprise-endpoint-on-dotcom",
"title": "The client is pointed at the wrong GitHub host entirely",
"description": "GET /meta returns installed_version on Enterprise Server and not on github.com, and the root endpoint map names the host that actually answered.",
"h1": "The client is pointed at the wrong GitHub host entirely",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github enterprise server api base url api/v3",
             "github api 404 every endpoint wrong host",
             "github meta installed_version enterprise server",
             "api.github.com vs enterprise base url sdk default",
             "ghe.com data residency api base url"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The code is shared between the hosted product and the customer's own installation, and it works in one of them. In the other every endpoint answers 404, which sends everybody hunting for a permission, or the token gets a flat <code>401 Bad credentials</code> despite being minted twenty minutes ago and pasted straight in. Both symptoms have the same cause and it is not on the list anybody checks: the client is talking to a different GitHub installation from the one that holds the resources. An environment variable did not get set, or an SDK fell back to its built-in default, and the requests are going somewhere the token means nothing and the repositories do not exist.",
"short_answer": """<p>There are three host families and they are separate installations, not variations on one. github.com serves its API at <code>https://api.github.com</code>. GitHub Enterprise Server serves REST at <code>https://HOSTNAME/api/v3</code> and GraphQL at <code>https://HOSTNAME/api/graphql</code>. Enterprise Cloud with data residency serves its API under <code>https://api.SUBDOMAIN.ghe.com</code>. A credential from one is meaningless at the others and so are the resource identifiers.</p>
<p>One unauthenticated read tells you which one you reached. <code>GET {base}/meta</code> returns an <code>installed_version</code> field on Enterprise Server and does not on github.com &mdash; that field is the cleanest single discriminator available. Two more readings make it robust: an HTML content type means you dropped the <code>/api/v3</code> and are talking to the web interface, which answers 200 and looks alive; and <code>GET {base}/</code>, the root endpoint map, contains absolute URLs like <code>current_user_url</code> whose host is the host that <em>actually served you</em>, which survives a redirect that a value in a config file does not.</p>""",
"problem": """<p>The reason this eats a day is that both symptoms are famously caused by something else. A 404 on this API is what a permission problem looks like, by design, so a client pointed at the wrong installation produces exactly the fingerprint of a token that cannot see anything &mdash; and it produces it on every single endpoint, which reads as a very broken token rather than as a very wrong hostname. The 401 version is worse, because a fresh credential returning <code>Bad credentials</code> convinces people the credential is malformed, and the next hour goes into whitespace, encoding and copy-paste.</p>
<p>The second reason is that nobody wrote the wrong URL. It is a default. An SDK constructed without a base URL uses github.com; a helper reads <code>GITHUB_API_URL</code> and falls back when the variable is absent; a container inherits the staging value into production. Nothing in the code says <code>api.github.com</code>, so grepping for it finds nothing, and the value only exists at runtime in a place nobody prints.</p>
<p>The third is the version that does not fail at all. Point a client at the Enterprise Server hostname and forget the <code>/api/v3</code> suffix and you are talking to the web interface. It answers 200. It sends HTML. A client that only checks the status code, or that shrugs at a JSON parse error and returns an empty result, reports success and finds nothing &mdash; the same silent under-report an unmonitored integration can carry for months.</p>""",
"why": """<p><strong>These are separate installations, not one API with different names.</strong> An Enterprise Server appliance has its own users, its own repositories, its own numeric identifiers and its own credentials. A token minted on github.com is not a weaker token there, it is not a token at all. This is why the failure is total rather than partial and why it does not respond to any change you make to permissions: there is nothing on the other end that has ever heard of your account.</p>
<p><strong><code>installed_version</code> is the discriminator worth building on.</strong> The Enterprise Server documentation for <code>GET /meta</code> lists <code>installed_version</code> in its response schema and the github.com one does not, so the presence of that field identifies an appliance and prints its version at the same time. It needs no token on github.com, which means this check can run at process start before any credential has been read.</p>
<p><strong>The root endpoint map names the host that answered.</strong> <code>GET /</code> returns a map of URL templates, and they are absolute: on github.com <code>current_user_url</code> is <code>https://api.github.com/user</code>, and on an appliance it carries the appliance's hostname and <code>/api/v3</code>. Comparing that host against the base URL you configured catches the case the configured value cannot: a redirect, a proxy, or a load balancer sending you somewhere other than the name you dialled.</p>
<p><strong>A token's shape says nothing about which host it belongs to.</strong> Prefixes tell you the credential class &mdash; fine-grained, classic, installation &mdash; and nothing about the installation that issued it. There is no local test for "is this a github.com token", so the only honest check is behavioural: call <code>GET /user</code> against the configured base and assert the login is the one you expect. The script takes that expected login as an argument rather than inventing a heuristic.</p>
<p><strong>What this cannot tell you, and it matters.</strong> Enterprise Cloud organizations live on <code>api.github.com</code> alongside everything else, so <code>/meta</code> cannot distinguish an enterprise-managed organization from a personal account, and it should not try: that is not a host problem and nothing about it will show up here. Data residency is different, because it moves the host to <code>api.SUBDOMAIN.ghe.com</code>, and that one <em>is</em> visible in the URL.</p>""",
"steps": [
 {"h": "Print the base URL the process is actually using",
  "body": """<p>Not the one in the deployment manifest, the one the client resolved at startup. This is the whole bug in most cases and it is usually one line to log. The script takes it as <code>--base</code> so that everything it reports is anchored to a value you have seen with your own eyes rather than assumed.</p>"""},
 {"h": "Read /meta against that base, unauthenticated",
  "body": """<p>No token needed. <code>installed_version</code> in the response means you are on an Enterprise Server appliance and the script prints the version. Its absence, with a valid <code>/meta</code> document, means github.com or Enterprise Cloud. An HTML content type means the <code>/api/v3</code> suffix is missing and you are talking to the web interface, which is the failure mode that returns 200 and finds nothing.</p>"""},
 {"h": "Compare the host you dialled with the host that answered",
  "body": """<p><code>GET {base}/</code> returns the root endpoint map, whose URLs are absolute. The script pulls the host out of <code>current_user_url</code> and compares it against the host in your base URL. A mismatch is a redirect or a proxy, and it is the one thing reading your configuration cannot catch.</p>"""},
 {"h": "Assert the identity, because the token cannot be checked locally",
  "body": """<p>With a token and <code>--expect-login</code>, the script calls <code>GET /user</code> and checks the login and the host inside <code>html_url</code>. A 401 here against a base that <code>/meta</code> identified as an appliance is the credential-from-the-other-installation case stated plainly, rather than as a mystery about a fresh token.</p>"""},
 {"h": "Make the check a startup assertion, not a debugging session",
  "body": """<p>The repair the script prints is to set the base URL explicitly per environment and to assert at startup that the host answering matches the host expected. Two unauthenticated reads, no quota worth counting, and the class of bug where a job runs happily against the wrong installation for a week stops existing.</p>"""},
],
"verify": """<p>With the base URL set for the environment, the guessed family and the observed one agree, and the host that answered is the host that was dialled.</p>
<pre><code class="language-bash">python3 github_api_host.py --base https://github.acme.internal/api/v3 \\
    --expect-login dana-integration
# read cost: 3 REST request(s), 2 of them unauthenticated and free
# configured: host github.acme.internal, guessed family enterprise-server
# meta: installed_version present (3.14.2) -> enterprise-server
# served host: github.acme.internal (from current_user_url in the root map)
# agrees: the family guessed from the URL, the family the host reports, and
#   the host that actually answered are all the same installation.
# identity: dana-integration, html_url host github.acme.internal — as expected.
# note: a token's prefix names its class and never its installation, so this
#   assertion is the only local test there is.
# repair: nothing to change. Keep this as a startup assertion rather than a
#   thing somebody runs after a week of 404s.</code></pre>""",
"code_intro": "Two unauthenticated reads and one optional authenticated one, and everything that decides anything is string work on a URL and a lookup for one field. That is worth keeping pure because the interesting inputs are hosts you do not have: an appliance, a data-residency subdomain, a web interface answering HTML to a client that expected JSON. All three are fixtures here, and the agreement function that compares three independent readings of the same question is the part with the tests.",
"py_file": "github_api_host.py",
"py": '''"""Say which GitHub installation this client is actually talking to.

Read only, and two of its three calls need no credential at all. Nothing is
configured, set or written: the repair is an environment variable and a
startup assertion, and both are printed.

The point of the note: github.com, a GitHub Enterprise Server appliance and an
Enterprise Cloud tenant with data residency are separate installations. A
credential from one is meaningless at the others, and a base URL that defaults
to the wrong one produces a 404 on every route or a flat 401 on a token minted
minutes ago.

What this can and cannot see: /meta reports installed_version on Enterprise
Server, which is the cleanest discriminator available. It cannot separate an
Enterprise Cloud organization from a personal account, because both are served
from api.github.com, and that is not a host problem.

Environment:

    GITHUB_TOKEN    optional. Needed only for the identity assertion.
"""
import argparse
import json
import logging
import os
import sys
from urllib.parse import urlparse

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_api_host")

UA = "github-api-host/1.0"

DOTCOM_API_HOST = "api.github.com"
DOTCOM_WEB_HOST = "github.com"
GHES_REST_SUFFIX = "/api/v3"
GHES_GRAPHQL_SUFFIX = "/api/graphql"
RESIDENCY_SUFFIX = ".ghe.com"

FAMILIES = ("dotcom", "enterprise-server", "enterprise-cloud-data-residency",
            "web-host-not-api", "unknown")


def read_cost(with_identity):
    """(requests, unauthenticated ones) this run will spend. Pure.

    The second number is the point: the host check needs no credential, so it
    can run at process start before any secret has been read.
    """
    made = 2 + (1 if with_identity else 0)
    return (made, 2)


def normalise_base(url):
    """Trim a base URL to a comparable form. Pure."""
    value = str(url or "").strip()
    while value.endswith("/"):
        value = value[:-1]
    return value


def host_of(url):
    """The hostname in a URL, lowercased, or None. Pure."""
    try:
        parsed = urlparse(str(url or ""))
    except ValueError:
        return None
    return (parsed.hostname or "").lower() or None


def family_from_url(base):
    """Guess the installation family from the configured URL. Pure.

    A guess, explicitly. It is compared against what the host itself reports,
    and the disagreement between the two is more interesting than either.
    """
    value = normalise_base(base)
    host = host_of(value)
    if not host:
        return ("unknown", "no host could be parsed out of the base URL.")
    if host == DOTCOM_API_HOST:
        return ("dotcom", "api.github.com is the github.com API host.")
    if host == DOTCOM_WEB_HOST:
        return ("web-host-not-api",
                "github.com is the web interface. The API lives at "
                "api.github.com, and a client pointed here will be handed HTML.")
    if host.startswith("api.") and host.endswith(RESIDENCY_SUFFIX):
        return ("enterprise-cloud-data-residency",
                "an api.SUBDOMAIN.ghe.com host is an Enterprise Cloud tenant "
                "with data residency, which is its own installation.")
    if value.endswith(GHES_REST_SUFFIX):
        return ("enterprise-server",
                "a host with the %s suffix is an Enterprise Server appliance."
                % GHES_REST_SUFFIX)
    if value.endswith(GHES_GRAPHQL_SUFFIX):
        return ("enterprise-server",
                "this is the appliance's GraphQL path; its REST base is %s."
                % GHES_REST_SUFFIX)
    return ("web-host-not-api",
            "this host carries no API prefix. On an appliance the REST base is "
            "the hostname plus %s, and without it you are talking to the web "
            "interface, which answers 200 and sends HTML." % GHES_REST_SUFFIX)


def content_is_html(content_type):
    """Did the host send a web page. Pure."""
    return "html" in str(content_type or "").lower()


def family_from_meta(status, content_type, body):
    """What the host itself says it is. Pure. (family, detail).

    installed_version is the discriminator: the Enterprise Server schema for
    /meta carries it and the github.com one does not.
    """
    if content_is_html(content_type):
        return ("web-host-not-api",
                "the host returned HTML rather than JSON, so this is a web "
                "interface. A client checking only the status code sees a 200 "
                "here and reports success.")
    if int(status or 0) != 200 or not isinstance(body, dict):
        return ("meta-unreadable",
                "/meta did not return a readable JSON document, so the host "
                "could not identify itself. On a private appliance this "
                "endpoint can require authentication.")
    version = body.get("installed_version")
    if version:
        return ("enterprise-server",
                "installed_version is present (%s), which the github.com "
                "schema for this endpoint does not carry." % version)
    if "verifiable_password_authentication" in body or "hooks" in body:
        return ("dotcom-or-enterprise-cloud",
                "a valid /meta document with no installed_version. That is "
                "github.com, or an Enterprise Cloud tenant, which are served "
                "from the same host and cannot be separated here.")
    return ("meta-unreadable",
            "the document does not look like /meta, so nothing can be "
            "concluded from it.")


def served_host_from_root(root):
    """The host named in the root endpoint map. Pure. (host, detail).

    The URLs in that map are absolute, so this is the host that actually
    answered rather than the one you dialled. It is the only reading here that
    survives a redirect or a proxy.
    """
    if not isinstance(root, dict) or not root:
        return (None,
                "the root endpoint map was not readable, so the host that "
                "answered cannot be named.")
    for key in ("current_user_url", "repository_url", "user_url"):
        value = root.get(key)
        host = host_of(value) if isinstance(value, str) else None
        if host:
            return (host, "taken from %s in the root map." % key)
    for value in root.values():
        host = host_of(value) if isinstance(value, str) else None
        if host:
            return (host, "taken from an absolute URL in the root map.")
    return (None, "the root map carried no absolute URL to read a host from.")


def agreement(guessed, reported, configured_host, served_host):
    """Compare three independent readings. Pure. (state, detail)."""
    if reported == "web-host-not-api" or guessed == "web-host-not-api":
        return ("no-api-prefix",
                "this is a web interface rather than an API base. On an "
                "appliance append %s to the hostname; on github.com use "
                "api.github.com." % GHES_REST_SUFFIX)
    if served_host and configured_host and served_host != configured_host:
        return ("served-elsewhere",
                "you dialled %s and %s answered. A redirect or a proxy is "
                "sending this client somewhere else, which reading the "
                "configuration would never have caught."
                % (configured_host, served_host))
    if reported == "meta-unreadable":
        return ("host-unidentified",
                "the host did not identify itself, so the family in the URL is "
                "the only evidence and it is a guess.")
    if reported == "enterprise-server" and guessed != "enterprise-server":
        return ("wrong-host-family",
                "the URL looks like %s and the host reports itself as an "
                "Enterprise Server appliance. Those are different "
                "installations." % guessed)
    if reported == "dotcom-or-enterprise-cloud" and guessed == "enterprise-server":
        return ("wrong-host-family",
                "the URL carries an appliance suffix and the host answering is "
                "not an appliance. Those are different installations.")
    return ("agrees",
            "the family guessed from the URL, the family the host reports, and "
            "the host that actually answered are all the same installation.")


def identity_check(status, login, html_url, expected_login, served_host):
    """Assert the account, because the token cannot be checked locally. Pure."""
    code = int(status or 0)
    if code == 0:
        return ("not-checked",
                "no identity call was made, so nothing confirms the credential "
                "belongs to this installation.")
    if code == 401:
        return ("credential-not-of-this-host",
                "the credential was rejected outright by this host. A token "
                "minted at a different installation is not a weak token here, "
                "it is not a token at all.")
    if code != 200:
        return ("identity-unreadable",
                "HTTP %s from the identity call, so the account could not be "
                "read." % status)
    url_host = host_of(html_url)
    if expected_login and str(login or "").lower() != str(expected_login).lower():
        return ("wrong-account",
                "this host knows the credential as %r and you expected %r. "
                "Same shape of secret, different installation."
                % (login, expected_login))
    if url_host and served_host and url_host != served_host \\
            and not url_host.endswith(served_host) \\
            and not served_host.endswith(url_host):
        return ("html-url-host-mismatch",
                "the account's html_url points at %s while %s answered, which "
                "is worth explaining before trusting either."
                % (url_host, served_host))
    return ("identity-as-expected",
            "the account this host returns is the one you expected.")


def token_shape_is_no_evidence(token):
    """State plainly that a prefix cannot name an installation. Pure."""
    value = (token or "").strip()
    known = ("github_pat_", "ghp_", "gho_", "ghu_", "ghs_", "ghr_")
    if any(value.startswith(prefix) for prefix in known):
        return ("class-known-host-unknown",
                "the prefix names the credential class and never the "
                "installation that issued it. There is no local test for which "
                "host a token belongs to; the identity call is the only one.")
    return ("class-unknown",
            "the credential class could not be named, and it would not have "
            "named the installation anyway.")


def verdict(agreement_state, identity_state):
    """The finding, in one state. Pure. (state, detail)."""
    if agreement_state == "no-api-prefix":
        return ("no-api-prefix",
                "the base URL is a web interface, so every API call is being "
                "answered with a web page.")
    if agreement_state == "wrong-host-family":
        return ("wrong-installation",
                "the client is configured for one installation and talking to "
                "another. Every 404 and every 401 follows from that.")
    if agreement_state == "served-elsewhere":
        return ("redirected-elsewhere",
                "the host that answered is not the host that was dialled, so "
                "the configuration is not the whole story.")
    if identity_state in ("credential-not-of-this-host", "wrong-account"):
        return ("credential-from-another-host",
                "the host is reachable and the credential does not belong to "
                "it, which is the same bug seen from the other side.")
    if agreement_state == "host-unidentified":
        return ("host-unidentified",
                "the host would not identify itself, so this run narrows the "
                "question rather than answering it.")
    if identity_state == "html-url-host-mismatch":
        return ("host-mismatch-in-payload",
                "the objects this host returns point at a different hostname "
                "from the one serving them.")
    return ("host-as-configured",
            "the base URL, the host and the account all describe the same "
            "installation.")


def repair(state, base):
    """The sentence a reader has to act on. Pure. Nothing here is configured."""
    if state == "no-api-prefix":
        return ("set the API base URL properly: %s for github.com, the "
                "appliance hostname plus %s for Enterprise Server, and "
                "api.SUBDOMAIN.ghe.com for a data-residency tenant."
                % ("https://" + DOTCOM_API_HOST, GHES_REST_SUFFIX))
    if state in ("wrong-installation", "credential-from-another-host"):
        return ("set the base URL explicitly for this environment rather than "
                "letting a library default decide, and pair each base URL with "
                "the credential minted at that installation. %s is not the "
                "host holding these resources." % (base or "the configured base"))
    if state == "redirected-elsewhere":
        return ("find out what is redirecting this client. Then assert at "
                "startup that the host in the root map matches the host you "
                "configured, so the next one is caught in a second.")
    if state == "host-unidentified":
        return ("re-run with a credential this host accepts, or from a network "
                "that can reach it. A private appliance can require "
                "authentication even for /meta.")
    return ("nothing to change. Keep this as a startup assertion rather than a "
            "thing somebody runs after a week of 404s.")


def get(session, url):
    """One GET. Returns the response object, or None if the host is unreachable."""
    try:
        return session.get(url, timeout=30)
    except requests.RequestException as err:
        log.warning("%s did not answer: %s", url, err)
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=os.environ.get("GITHUB_API_URL")
                        or "https://" + DOTCOM_API_HOST,
                        help="the base URL the client resolved at startup")
    parser.add_argument("--expect-login",
                        help="the account this credential should be, on this host")
    args = parser.parse_args()

    base = normalise_base(args.base)
    token = os.environ.get("GITHUB_TOKEN")
    made, free = read_cost(bool(token))
    log.info("read cost: %d REST request(s), %d of them unauthenticated and free",
             made, free)

    configured_host = host_of(base)
    guessed, guessed_detail = family_from_url(base)
    log.info("configured: host %s, guessed family %s. %s", configured_host,
             guessed, guessed_detail)

    session = requests.Session()
    session.headers.update({
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub refuses requests with no User-Agent before it looks at auth.
        "User-Agent": UA,
    })

    meta = get(session, base + "/meta")
    if meta is None:
        reported, reported_detail = ("meta-unreadable", "the host did not answer.")
        meta_body, content_type = None, ""
    else:
        content_type = meta.headers.get("content-type", "")
        try:
            meta_body = meta.json()
        except ValueError:
            meta_body = None
        reported, reported_detail = family_from_meta(meta.status_code,
                                                     content_type, meta_body)
    log.info("meta: %s. %s", reported, reported_detail)

    root = get(session, base + "/")
    root_body = None
    if root is not None:
        try:
            root_body = root.json()
        except ValueError:
            root_body = None
    served_host, served_detail = served_host_from_root(root_body)
    log.info("served host: %s (%s)", served_host or "unknown", served_detail)

    agreement_state, agreement_detail = agreement(guessed, reported,
                                                  configured_host, served_host)
    log.info("%s: %s", agreement_state, agreement_detail)

    identity_state, identity_detail = ("not-checked", "no token supplied.")
    login = None
    if token:
        session.headers["Authorization"] = "Bearer " + token
        who = get(session, base + "/user")
        if who is not None:
            body = {}
            try:
                body = who.json() or {}
            except ValueError:
                body = {}
            login = body.get("login")
            identity_state, identity_detail = identity_check(
                who.status_code, login, body.get("html_url"),
                args.expect_login, served_host)
        shape_state, shape_detail = token_shape_is_no_evidence(token)
        log.info("%s: %s", shape_state, shape_detail)
    log.info("identity: %s. %s", identity_state, identity_detail)

    state, detail = verdict(agreement_state, identity_state)
    log.info("%s: %s", state, detail)
    fix = repair(state, base)
    log.info("repair: %s", fix)

    print(json.dumps({
        "base": base,
        "configured_host": configured_host,
        "guessed_family": guessed,
        "reported_family": reported,
        "served_host": served_host,
        "agreement_state": agreement_state,
        "identity_state": identity_state,
        "login": login,
        "state": state,
        "detail": detail,
        "repair": fix,
    }, indent=2, default=str))
    return 1 if state != "host-as-configured" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-api-host.mjs",
"js": '''/**
 * Say which GitHub installation this client is actually talking to.
 *
 * Read only, and two of its three calls need no credential at all. Nothing is
 * configured or written: the repair is an environment variable and a startup
 * assertion, and both are printed.
 *
 * github.com, a GitHub Enterprise Server appliance and an Enterprise Cloud
 * tenant with data residency are separate installations. A credential from one
 * is meaningless at the others, and a base URL that defaults to the wrong one
 * produces a 404 on every route or a flat 401 on a fresh token.
 *
 * Environment:
 *   GITHUB_API_URL      the base URL the client resolved at startup
 *   GITHUB_TOKEN        optional; needed only for the identity assertion
 *   GITHUB_EXPECT_LOGIN optional account this credential should be here
 */
const UA = 'github-api-host/1.0';

export const DOTCOM_API_HOST = 'api.github.com';
export const DOTCOM_WEB_HOST = 'github.com';
export const GHES_REST_SUFFIX = '/api/v3';
export const GHES_GRAPHQL_SUFFIX = '/api/graphql';
export const RESIDENCY_SUFFIX = '.ghe.com';

export const FAMILIES = ['dotcom', 'enterprise-server',
  'enterprise-cloud-data-residency', 'web-host-not-api', 'unknown'];

/** [requests, unauthenticated ones] this run will spend. Pure. */
export function readCost(withIdentity) {
  return [2 + (withIdentity ? 1 : 0), 2];
}

/** Trim a base URL to a comparable form. Pure. */
export function normaliseBase(url) {
  let value = String(url ?? '').trim();
  while (value.endsWith('/')) value = value.slice(0, -1);
  return value;
}

/** The hostname in a URL, lowercased, or null. Pure. */
export function hostOf(url) {
  try {
    return new URL(String(url ?? '')).hostname.toLowerCase() || null;
  } catch {
    return null;
  }
}

/** Guess the installation family from the configured URL. Pure. */
export function familyFromUrl(base) {
  const value = normaliseBase(base);
  const host = hostOf(value);
  if (!host) return ['unknown', 'no host could be parsed out of the base URL.'];
  if (host === DOTCOM_API_HOST) {
    return ['dotcom', 'api.github.com is the github.com API host.'];
  }
  if (host === DOTCOM_WEB_HOST) {
    return ['web-host-not-api', 'github.com is the web interface. The API lives '
      + 'at api.github.com, and a client pointed here will be handed HTML.'];
  }
  if (host.startsWith('api.') && host.endsWith(RESIDENCY_SUFFIX)) {
    return ['enterprise-cloud-data-residency', 'an api.SUBDOMAIN.ghe.com host is '
      + 'an Enterprise Cloud tenant with data residency, which is its own '
      + 'installation.'];
  }
  if (value.endsWith(GHES_REST_SUFFIX)) {
    return ['enterprise-server', `a host with the ${GHES_REST_SUFFIX} suffix is `
      + 'an Enterprise Server appliance.'];
  }
  if (value.endsWith(GHES_GRAPHQL_SUFFIX)) {
    return ['enterprise-server', "this is the appliance's GraphQL path; its "
      + `REST base is ${GHES_REST_SUFFIX}.`];
  }
  return ['web-host-not-api', 'this host carries no API prefix. On an appliance '
    + `the REST base is the hostname plus ${GHES_REST_SUFFIX}, and without it `
    + 'you are talking to the web interface, which answers 200 and sends HTML.'];
}

/** Did the host send a web page. Pure. */
export function contentIsHtml(contentType) {
  return String(contentType ?? '').toLowerCase().includes('html');
}

/** What the host itself says it is. Pure. [family, detail]. */
export function familyFromMeta(status, contentType, body) {
  if (contentIsHtml(contentType)) {
    return ['web-host-not-api', 'the host returned HTML rather than JSON, so '
      + 'this is a web interface. A client checking only the status code sees a '
      + '200 here and reports success.'];
  }
  if (Number(status) !== 200 || !body || typeof body !== 'object') {
    return ['meta-unreadable', '/meta did not return a readable JSON document, '
      + 'so the host could not identify itself. On a private appliance this '
      + 'endpoint can require authentication.'];
  }
  const version = body.installed_version;
  if (version) {
    return ['enterprise-server', `installed_version is present (${version}), `
      + 'which the github.com schema for this endpoint does not carry.'];
  }
  if ('verifiable_password_authentication' in body || 'hooks' in body) {
    return ['dotcom-or-enterprise-cloud', 'a valid /meta document with no '
      + 'installed_version. That is github.com, or an Enterprise Cloud tenant, '
      + 'which are served from the same host and cannot be separated here.'];
  }
  return ['meta-unreadable', 'the document does not look like /meta, so nothing '
    + 'can be concluded from it.'];
}

/** The host named in the root endpoint map. Pure. [host, detail]. */
export function servedHostFromRoot(root) {
  if (!root || typeof root !== 'object' || Object.keys(root).length === 0) {
    return [null, 'the root endpoint map was not readable, so the host that '
      + 'answered cannot be named.'];
  }
  for (const key of ['current_user_url', 'repository_url', 'user_url']) {
    const value = root[key];
    const host = typeof value === 'string' ? hostOf(value) : null;
    if (host) return [host, `taken from ${key} in the root map.`];
  }
  for (const value of Object.values(root)) {
    const host = typeof value === 'string' ? hostOf(value) : null;
    if (host) return [host, 'taken from an absolute URL in the root map.'];
  }
  return [null, 'the root map carried no absolute URL to read a host from.'];
}

/** Compare three independent readings. Pure. [state, detail]. */
export function agreement(guessed, reported, configuredHost, servedHost) {
  if (reported === 'web-host-not-api' || guessed === 'web-host-not-api') {
    return ['no-api-prefix', 'this is a web interface rather than an API base. '
      + `On an appliance append ${GHES_REST_SUFFIX} to the hostname; on `
      + 'github.com use api.github.com.'];
  }
  if (servedHost && configuredHost && servedHost !== configuredHost) {
    return ['served-elsewhere', `you dialled ${configuredHost} and ${servedHost} `
      + 'answered. A redirect or a proxy is sending this client somewhere else, '
      + 'which reading the configuration would never have caught.'];
  }
  if (reported === 'meta-unreadable') {
    return ['host-unidentified', 'the host did not identify itself, so the '
      + 'family in the URL is the only evidence and it is a guess.'];
  }
  if (reported === 'enterprise-server' && guessed !== 'enterprise-server') {
    return ['wrong-host-family', `the URL looks like ${guessed} and the host `
      + 'reports itself as an Enterprise Server appliance. Those are different '
      + 'installations.'];
  }
  if (reported === 'dotcom-or-enterprise-cloud' && guessed === 'enterprise-server') {
    return ['wrong-host-family', 'the URL carries an appliance suffix and the '
      + 'host answering is not an appliance. Those are different installations.'];
  }
  return ['agrees', 'the family guessed from the URL, the family the host '
    + 'reports, and the host that actually answered are all the same installation.'];
}

/** Assert the account, because the token cannot be checked locally. Pure. */
export function identityCheck(status, login, htmlUrl, expectedLogin, servedHost) {
  const code = Number(status) || 0;
  if (code === 0) {
    return ['not-checked', 'no identity call was made, so nothing confirms the '
      + 'credential belongs to this installation.'];
  }
  if (code === 401) {
    return ['credential-not-of-this-host', 'the credential was rejected outright '
      + 'by this host. A token minted at a different installation is not a weak '
      + 'token here, it is not a token at all.'];
  }
  if (code !== 200) {
    return ['identity-unreadable', `HTTP ${status} from the identity call, so `
      + 'the account could not be read.'];
  }
  const urlHost = hostOf(htmlUrl);
  if (expectedLogin && String(login ?? '').toLowerCase() !== String(expectedLogin).toLowerCase()) {
    return ['wrong-account', `this host knows the credential as `
      + `${JSON.stringify(login)} and you expected ${JSON.stringify(expectedLogin)}. `
      + 'Same shape of secret, different installation.'];
  }
  if (urlHost && servedHost && urlHost !== servedHost
      && !urlHost.endsWith(servedHost) && !servedHost.endsWith(urlHost)) {
    return ['html-url-host-mismatch', `the account's html_url points at `
      + `${urlHost} while ${servedHost} answered, which is worth explaining `
      + 'before trusting either.'];
  }
  return ['identity-as-expected', 'the account this host returns is the one you '
    + 'expected.'];
}

/** State plainly that a prefix cannot name an installation. Pure. */
export function tokenShapeIsNoEvidence(token) {
  const value = String(token ?? '').trim();
  const known = ['github_pat_', 'ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_'];
  if (known.some((prefix) => value.startsWith(prefix))) {
    return ['class-known-host-unknown', 'the prefix names the credential class '
      + 'and never the installation that issued it. There is no local test for '
      + 'which host a token belongs to; the identity call is the only one.'];
  }
  return ['class-unknown', 'the credential class could not be named, and it '
    + 'would not have named the installation anyway.'];
}

/** The finding, in one state. Pure. [state, detail]. */
export function verdict(agreementState, identityState) {
  if (agreementState === 'no-api-prefix') {
    return ['no-api-prefix', 'the base URL is a web interface, so every API call '
      + 'is being answered with a web page.'];
  }
  if (agreementState === 'wrong-host-family') {
    return ['wrong-installation', 'the client is configured for one installation '
      + 'and talking to another. Every 404 and every 401 follows from that.'];
  }
  if (agreementState === 'served-elsewhere') {
    return ['redirected-elsewhere', 'the host that answered is not the host that '
      + 'was dialled, so the configuration is not the whole story.'];
  }
  if (['credential-not-of-this-host', 'wrong-account'].includes(identityState)) {
    return ['credential-from-another-host', 'the host is reachable and the '
      + 'credential does not belong to it, which is the same bug seen from the '
      + 'other side.'];
  }
  if (agreementState === 'host-unidentified') {
    return ['host-unidentified', 'the host would not identify itself, so this '
      + 'run narrows the question rather than answering it.'];
  }
  if (identityState === 'html-url-host-mismatch') {
    return ['host-mismatch-in-payload', 'the objects this host returns point at '
      + 'a different hostname from the one serving them.'];
  }
  return ['host-as-configured', 'the base URL, the host and the account all '
    + 'describe the same installation.'];
}

/** The sentence a reader has to act on. Pure. Nothing here is configured. */
export function repair(state, base) {
  if (state === 'no-api-prefix') {
    return `set the API base URL properly: https://${DOTCOM_API_HOST} for `
      + `github.com, the appliance hostname plus ${GHES_REST_SUFFIX} for `
      + 'Enterprise Server, and api.SUBDOMAIN.ghe.com for a data-residency tenant.';
  }
  if (['wrong-installation', 'credential-from-another-host'].includes(state)) {
    return 'set the base URL explicitly for this environment rather than letting '
      + 'a library default decide, and pair each base URL with the credential '
      + `minted at that installation. ${base || 'the configured base'} is not the `
      + 'host holding these resources.';
  }
  if (state === 'redirected-elsewhere') {
    return 'find out what is redirecting this client. Then assert at startup '
      + 'that the host in the root map matches the host you configured, so the '
      + 'next one is caught in a second.';
  }
  if (state === 'host-unidentified') {
    return 're-run with a credential this host accepts, or from a network that '
      + 'can reach it. A private appliance can require authentication even for /meta.';
  }
  return 'nothing to change. Keep this as a startup assertion rather than a '
    + 'thing somebody runs after a week of 404s.';
}

function headers(token) {
  const bag = {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
  if (token) bag.Authorization = `Bearer ${token}`;
  return bag;
}

async function safeGet(url, token) {
  try {
    return await fetch(url, { headers: headers(token) });
  } catch (err) {
    console.warn(`${url} did not answer: ${err.message}`);
    return null;
  }
}

async function main() {
  const base = normaliseBase(process.env.GITHUB_API_URL || `https://${DOTCOM_API_HOST}`);
  const token = process.env.GITHUB_TOKEN || '';
  const expectLogin = process.env.GITHUB_EXPECT_LOGIN || '';
  const [made, free] = readCost(Boolean(token));
  console.log(`read cost: ${made} REST request(s), ${free} of them `
    + 'unauthenticated and free');

  const configuredHost = hostOf(base);
  const [guessed, guessedDetail] = familyFromUrl(base);
  console.log(`configured: host ${configuredHost}, guessed family ${guessed}. ${guessedDetail}`);

  const meta = await safeGet(`${base}/meta`, '');
  let reported = 'meta-unreadable';
  let reportedDetail = 'the host did not answer.';
  if (meta) {
    let metaBody = null;
    try { metaBody = await meta.json(); } catch { metaBody = null; }
    [reported, reportedDetail] = familyFromMeta(meta.status,
      meta.headers.get('content-type') || '', metaBody);
  }
  console.log(`meta: ${reported}. ${reportedDetail}`);

  const root = await safeGet(`${base}/`, '');
  let rootBody = null;
  if (root) {
    try { rootBody = await root.json(); } catch { rootBody = null; }
  }
  const [servedHost, servedDetail] = servedHostFromRoot(rootBody);
  console.log(`served host: ${servedHost || 'unknown'} (${servedDetail})`);

  const [agreementState, agreementDetail] = agreement(guessed, reported,
    configuredHost, servedHost);
  console.log(`${agreementState}: ${agreementDetail}`);

  let identityState = 'not-checked';
  let identityDetail = 'no token supplied.';
  let login = null;
  if (token) {
    const who = await safeGet(`${base}/user`, token);
    if (who) {
      let body = {};
      try { body = (await who.json()) || {}; } catch { body = {}; }
      login = body.login ?? null;
      [identityState, identityDetail] = identityCheck(who.status, login,
        body.html_url, expectLogin, servedHost);
    }
    const [shapeState, shapeDetail] = tokenShapeIsNoEvidence(token);
    console.log(`${shapeState}: ${shapeDetail}`);
  }
  console.log(`identity: ${identityState}. ${identityDetail}`);

  const [state, detail] = verdict(agreementState, identityState);
  console.log(`${state}: ${detail}`);
  const fix = repair(state, base);
  console.log(`repair: ${fix}`);

  console.log(JSON.stringify({
    base,
    configured_host: configuredHost,
    guessed_family: guessed,
    reported_family: reported,
    served_host: servedHost,
    agreement_state: agreementState,
    identity_state: identityState,
    login,
    state,
    detail,
    repair: fix,
  }, null, 2));
  process.exitCode = state === 'host-as-configured' ? 0 : 1;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The hosts in these tests are the ones you do not have to hand: an appliance, a data-residency subdomain, and a web interface answering HTML to a client that expected JSON. The first group is the URL reader, which is a guess and is labelled as one. The second is the host's own answer, keyed on <code>installed_version</code>. The third is the part that earns the note: three independent readings of the same question, and the states where they disagree — a base URL for one installation and an appliance answering, a host that redirected somewhere else, and a credential from the other installation. The last group pins the honest limits: a token prefix names a class and never a host, and github.com and Enterprise Cloud cannot be told apart from here.",
"test_py_file": "test_github_api_host.py",
"test_js_file": "github-api-host.test.mjs",
"test_py": '''from github_api_host import (
    DOTCOM_API_HOST, FAMILIES, GHES_REST_SUFFIX, agreement, content_is_html,
    family_from_meta, family_from_url, host_of, identity_check,
    normalise_base, read_cost, repair, served_host_from_root,
    token_shape_is_no_evidence, verdict,
)

DOTCOM_META = {"verifiable_password_authentication": False,
               "hooks": ["192.30.252.0/22"], "api": ["192.30.252.0/22"]}
GHES_META = {"verifiable_password_authentication": True,
             "installed_version": "3.14.2", "hooks": ["10.0.0.0/8"]}
DOTCOM_ROOT = {"current_user_url": "https://api.github.com/user",
               "repository_url": "https://api.github.com/repos/{owner}/{repo}"}
GHES_ROOT = {"current_user_url": "https://github.acme.internal/api/v3/user"}

# Obviously fake and far shorter than any real credential.
FINE = "github_pat_FAKE"


def test_the_three_host_families_are_read_off_the_url():
    assert family_from_url("https://api.github.com")[0] == "dotcom"
    assert family_from_url("https://github.acme.internal/api/v3")[0] == "enterprise-server"
    assert family_from_url("https://api.octocorp.ghe.com")[0] == (
        "enterprise-cloud-data-residency")
    assert set(FAMILIES) >= {"dotcom", "enterprise-server",
                             "enterprise-cloud-data-residency"}


def test_the_missing_api_prefix_is_named_as_its_own_failure():
    state, detail = family_from_url("https://github.acme.internal")
    assert state == "web-host-not-api"
    assert GHES_REST_SUFFIX in detail
    state, detail = family_from_url("https://github.com")
    assert state == "web-host-not-api"
    assert DOTCOM_API_HOST in detail
    assert family_from_url("not a url")[0] == "unknown"


def test_the_graphql_path_is_still_the_appliance():
    assert family_from_url("https://github.acme.internal/api/graphql")[0] == (
        "enterprise-server")
    assert normalise_base("https://api.github.com///") == "https://api.github.com"
    assert host_of("https://API.GitHub.com/user") == "api.github.com"
    assert host_of("nonsense") is None


def test_installed_version_is_the_discriminator():
    state, detail = family_from_meta(200, "application/json", GHES_META)
    assert state == "enterprise-server"
    assert "3.14.2" in detail
    state, detail = family_from_meta(200, "application/json", DOTCOM_META)
    assert state == "dotcom-or-enterprise-cloud"
    assert "cannot be separated here" in detail


def test_html_from_an_api_base_is_the_silent_one():
    state, detail = family_from_meta(200, "text/html; charset=utf-8", None)
    assert state == "web-host-not-api"
    assert "reports success" in detail
    assert content_is_html("text/html") is True
    assert content_is_html("application/json") is False
    assert family_from_meta(401, "application/json", None)[0] == "meta-unreadable"
    assert family_from_meta(200, "application/json", {"unrelated": 1})[0] == (
        "meta-unreadable")


def test_the_root_map_names_the_host_that_actually_answered():
    host, detail = served_host_from_root(GHES_ROOT)
    assert host == "github.acme.internal"
    assert "current_user_url" in detail
    assert served_host_from_root(DOTCOM_ROOT)[0] == "api.github.com"
    assert served_host_from_root({})[0] is None
    assert served_host_from_root({"x": 1})[0] is None


def test_a_dotcom_base_against_an_appliance_is_the_headline():
    state, detail = agreement("dotcom", "enterprise-server", "api.github.com",
                              "api.github.com")
    assert state == "wrong-host-family"
    assert "different installations" in detail


def test_an_appliance_base_answered_by_something_else_is_caught_too():
    assert agreement("enterprise-server", "dotcom-or-enterprise-cloud",
                     "github.acme.internal", "github.acme.internal")[0] == (
        "wrong-host-family")


def test_a_redirect_is_the_reading_configuration_cannot_give_you():
    state, detail = agreement("dotcom", "dotcom-or-enterprise-cloud",
                              "api.github.com", "api.ghe.example")
    assert state == "served-elsewhere"
    assert "reading the configuration would never have caught" in detail


def test_agreement_reports_agreement():
    assert agreement("dotcom", "dotcom-or-enterprise-cloud", "api.github.com",
                     "api.github.com")[0] == "agrees"
    assert agreement("enterprise-server", "meta-unreadable",
                     "github.acme.internal", None)[0] == "host-unidentified"
    assert agreement("web-host-not-api", "web-host-not-api", "github.com",
                     None)[0] == "no-api-prefix"


def test_a_credential_from_the_other_installation_is_stated_plainly():
    state, detail = identity_check(401, None, None, "dana", "github.acme.internal")
    assert state == "credential-not-of-this-host"
    assert "it is not a token at all" in detail
    state, detail = identity_check(200, "someone-else",
                                   "https://github.acme.internal/someone-else",
                                   "dana", "github.acme.internal")
    assert state == "wrong-account"
    assert "different installation" in detail
    assert identity_check(0, None, None, None, None)[0] == "not-checked"
    assert identity_check(503, None, None, None, None)[0] == "identity-unreadable"


def test_the_identity_passes_when_the_account_and_the_host_agree():
    state, _ = identity_check(200, "dana",
                              "https://github.acme.internal/dana", "dana",
                              "github.acme.internal")
    assert state == "identity-as-expected"
    # api.github.com serving objects whose html_url is github.com is normal:
    # one host name is a suffix of the other, so it is not a mismatch.
    assert identity_check(200, "dana", "https://github.com/dana", "dana",
                          "api.github.com")[0] == "identity-as-expected"


def test_a_token_prefix_names_a_class_and_never_an_installation():
    state, detail = token_shape_is_no_evidence(FINE)
    assert state == "class-known-host-unknown"
    assert "never the installation" in detail
    assert token_shape_is_no_evidence("")[0] == "class-unknown"


def test_the_verdict_and_the_repair_are_about_configuration():
    assert verdict("wrong-host-family", "not-checked")[0] == "wrong-installation"
    assert verdict("no-api-prefix", "not-checked")[0] == "no-api-prefix"
    assert verdict("served-elsewhere", "not-checked")[0] == "redirected-elsewhere"
    assert verdict("agrees", "credential-not-of-this-host")[0] == (
        "credential-from-another-host")
    assert verdict("agrees", "identity-as-expected")[0] == "host-as-configured"
    fix = repair("wrong-installation", "https://api.github.com")
    assert "set the base URL explicitly" in fix
    assert "letting a library default decide" in fix
    assert "startup assertion" in repair("host-as-configured", "x")


def test_the_host_check_needs_no_credential():
    assert read_cost(False) == (2, 2)
    assert read_cost(True) == (3, 2)
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DOTCOM_API_HOST, FAMILIES, GHES_REST_SUFFIX, agreement, contentIsHtml,
  familyFromMeta, familyFromUrl, hostOf, identityCheck, normaliseBase, readCost,
  repair, servedHostFromRoot, tokenShapeIsNoEvidence, verdict,
} from './github-api-host.mjs';

const DOTCOM_META = {
  verifiable_password_authentication: false,
  hooks: ['192.30.252.0/22'],
  api: ['192.30.252.0/22'],
};
const GHES_META = {
  verifiable_password_authentication: true,
  installed_version: '3.14.2',
  hooks: ['10.0.0.0/8'],
};
const DOTCOM_ROOT = {
  current_user_url: 'https://api.github.com/user',
  repository_url: 'https://api.github.com/repos/{owner}/{repo}',
};
const GHES_ROOT = { current_user_url: 'https://github.acme.internal/api/v3/user' };

// Obviously fake and far shorter than any real credential.
const FINE = 'github_pat_FAKE';

test('the three host families are read off the url', () => {
  assert.equal(familyFromUrl('https://api.github.com')[0], 'dotcom');
  assert.equal(familyFromUrl('https://github.acme.internal/api/v3')[0], 'enterprise-server');
  assert.equal(familyFromUrl('https://api.octocorp.ghe.com')[0],
    'enterprise-cloud-data-residency');
  for (const name of ['dotcom', 'enterprise-server', 'enterprise-cloud-data-residency']) {
    assert.ok(FAMILIES.includes(name));
  }
});

test('the missing api prefix is named as its own failure', () => {
  let [state, detail] = familyFromUrl('https://github.acme.internal');
  assert.equal(state, 'web-host-not-api');
  assert.ok(detail.includes(GHES_REST_SUFFIX));
  [state, detail] = familyFromUrl('https://github.com');
  assert.equal(state, 'web-host-not-api');
  assert.ok(detail.includes(DOTCOM_API_HOST));
  assert.equal(familyFromUrl('not a url')[0], 'unknown');
});

test('the graphql path is still the appliance', () => {
  assert.equal(familyFromUrl('https://github.acme.internal/api/graphql')[0],
    'enterprise-server');
  assert.equal(normaliseBase('https://api.github.com///'), 'https://api.github.com');
  assert.equal(hostOf('https://API.GitHub.com/user'), 'api.github.com');
  assert.equal(hostOf('nonsense'), null);
});

test('installed_version is the discriminator', () => {
  let [state, detail] = familyFromMeta(200, 'application/json', GHES_META);
  assert.equal(state, 'enterprise-server');
  assert.ok(detail.includes('3.14.2'));
  [state, detail] = familyFromMeta(200, 'application/json', DOTCOM_META);
  assert.equal(state, 'dotcom-or-enterprise-cloud');
  assert.match(detail, /cannot be separated here/);
});

test('html from an api base is the silent one', () => {
  const [state, detail] = familyFromMeta(200, 'text/html; charset=utf-8', null);
  assert.equal(state, 'web-host-not-api');
  assert.match(detail, /reports success/);
  assert.equal(contentIsHtml('text/html'), true);
  assert.equal(contentIsHtml('application/json'), false);
  assert.equal(familyFromMeta(401, 'application/json', null)[0], 'meta-unreadable');
  assert.equal(familyFromMeta(200, 'application/json', { unrelated: 1 })[0], 'meta-unreadable');
});

test('the root map names the host that actually answered', () => {
  const [host, detail] = servedHostFromRoot(GHES_ROOT);
  assert.equal(host, 'github.acme.internal');
  assert.match(detail, /current_user_url/);
  assert.equal(servedHostFromRoot(DOTCOM_ROOT)[0], 'api.github.com');
  assert.equal(servedHostFromRoot({})[0], null);
  assert.equal(servedHostFromRoot({ x: 1 })[0], null);
});

test('a dotcom base against an appliance is the headline', () => {
  const [state, detail] = agreement('dotcom', 'enterprise-server',
    'api.github.com', 'api.github.com');
  assert.equal(state, 'wrong-host-family');
  assert.match(detail, /different installations/);
});

test('an appliance base answered by something else is caught too', () => {
  assert.equal(
    agreement('enterprise-server', 'dotcom-or-enterprise-cloud',
      'github.acme.internal', 'github.acme.internal')[0],
    'wrong-host-family',
  );
});

test('a redirect is the reading configuration cannot give you', () => {
  const [state, detail] = agreement('dotcom', 'dotcom-or-enterprise-cloud',
    'api.github.com', 'api.ghe.example');
  assert.equal(state, 'served-elsewhere');
  assert.match(detail, /reading the configuration would never have caught/);
});

test('agreement reports agreement', () => {
  assert.equal(
    agreement('dotcom', 'dotcom-or-enterprise-cloud', 'api.github.com', 'api.github.com')[0],
    'agrees',
  );
  assert.equal(
    agreement('enterprise-server', 'meta-unreadable', 'github.acme.internal', null)[0],
    'host-unidentified',
  );
  assert.equal(
    agreement('web-host-not-api', 'web-host-not-api', 'github.com', null)[0],
    'no-api-prefix',
  );
});

test('a credential from the other installation is stated plainly', () => {
  let [state, detail] = identityCheck(401, null, null, 'dana', 'github.acme.internal');
  assert.equal(state, 'credential-not-of-this-host');
  assert.match(detail, /it is not a token at all/);
  [state, detail] = identityCheck(200, 'someone-else',
    'https://github.acme.internal/someone-else', 'dana', 'github.acme.internal');
  assert.equal(state, 'wrong-account');
  assert.match(detail, /different installation/);
  assert.equal(identityCheck(0, null, null, null, null)[0], 'not-checked');
  assert.equal(identityCheck(503, null, null, null, null)[0], 'identity-unreadable');
});

test('the identity passes when the account and the host agree', () => {
  assert.equal(
    identityCheck(200, 'dana', 'https://github.acme.internal/dana', 'dana',
      'github.acme.internal')[0],
    'identity-as-expected',
  );
  assert.equal(
    identityCheck(200, 'dana', 'https://github.com/dana', 'dana', 'api.github.com')[0],
    'identity-as-expected',
  );
});

test('a token prefix names a class and never an installation', () => {
  const [state, detail] = tokenShapeIsNoEvidence(FINE);
  assert.equal(state, 'class-known-host-unknown');
  assert.match(detail, /never the installation/);
  assert.equal(tokenShapeIsNoEvidence('')[0], 'class-unknown');
});

test('the verdict and the repair are about configuration', () => {
  assert.equal(verdict('wrong-host-family', 'not-checked')[0], 'wrong-installation');
  assert.equal(verdict('no-api-prefix', 'not-checked')[0], 'no-api-prefix');
  assert.equal(verdict('served-elsewhere', 'not-checked')[0], 'redirected-elsewhere');
  assert.equal(verdict('agrees', 'credential-not-of-this-host')[0],
    'credential-from-another-host');
  assert.equal(verdict('agrees', 'identity-as-expected')[0], 'host-as-configured');
  const fix = repair('wrong-installation', 'https://api.github.com');
  assert.match(fix, /set the base URL explicitly/);
  assert.match(fix, /letting a library default decide/);
  assert.match(repair('host-as-configured', 'x'), /startup assertion/);
});

test('the host check needs no credential', () => {
  assert.deepEqual(readCost(false), [2, 2]);
  assert.deepEqual(readCost(true), [3, 2]);
});
''',
"faq": [
 ("Is this not the same as a pinned API version that stopped being served?",
  "No, and the two are easy to keep apart once you know both. A retired version pin is refused with a 400 and <code>GET /versions</code> lists what is still served, so the fix is a value in one header. This is about which installation you are talking to at all: the host is a different appliance with different users, different repositories and different identifiers, so the failure is total rather than a rejected header, and it does not respond to changing anything about the request."),
 ("Why not just check that the base URL string is right?",
  "Because the string is only one of the three things that have to agree. The URL you configured is a guess about where the request will end up; <code>/meta</code> is what the host says about itself; and the root endpoint map is the host that actually answered. Reading the configuration cannot catch a redirect, a proxy, or an internal load balancer sending your client somewhere other than the name you dialled, and that is exactly the case where everybody trusts the config file and stops looking."),
 ("The base URL is the appliance and everything returns 200 with nothing in it.",
  "Then the <code>/api/v3</code> is missing and you are talking to the web interface. It answers 200 and it sends HTML, so a client that checks only the status code, or that swallows a JSON parse error and returns an empty list, reports success and finds nothing. That is why the script keys on the content type as well as the body: it is the one variant of this bug that never raises an error and can run in production for months."),
 ("Can the script tell a GitHub Enterprise Cloud account from a personal one?",
  "It cannot, and it says so rather than guessing. Enterprise Cloud organizations are served from <code>api.github.com</code> like everything else, so <code>/meta</code> has nothing to distinguish them by, and there is no host problem to find in that case. Data residency is the exception, because it genuinely moves the API to <code>api.SUBDOMAIN.ghe.com</code>, and that difference is visible in the URL before any request is made."),
 ("A brand new token gets 401. Surely the token is wrong?",
  "It is wrong for that host. A token's prefix names its class &mdash; fine-grained, classic, installation &mdash; and carries nothing at all about the installation that issued it, so there is no local test that would have caught this. That is why the script's identity check takes an expected login and calls <code>GET /user</code> against the configured base: the only way to know a credential belongs to a host is to ask the host who it thinks the credential is."),
],
"related": [
 ("/github/missing-endpoint-404-vs-405/", "When one route 404s rather than all of them"),
 ("/github/unsupported-api-version/", "A pinned version that stopped being served"),
 ("/github/bad-credentials-401/", "The other reason a good-looking token is refused"),
],
"citations": [CITE_META, CITE_GHES_REST, CITE_DATA_RESIDENCY, CITE_ABOUT_REST],
},
]
