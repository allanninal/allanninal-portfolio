#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch V.

Four notes about repository state rather than about credentials, which is the
line that keeps them off the permission notes already published. Each branch
sorts a different object, and none of them sorts a token.

The first sorts a role. Its chain is the loop everybody runs when a write is
refused: widen the scopes, mint another token, try again, and the ceiling never
moves because the ceiling was never the token. Its branch reads the permissions
object instead and the rows are roles, not responses.

The second sorts an off switch. Its chain is a fortnight spent granting
permissions to an endpoint that was never asking for one, and its branch is the
only one in the batch whose rows carry three different status codes for one
cause, because that is exactly what a disabled feature does.

The third sorts a repository. Nothing in its chain fails, which is the point:
every arrow is a success and the report at the end is confidently wrong. Its
branch is the only one here where the healthy row and the broken row return
identical HTTP.

The fourth sorts a pair of readings rather than one. Its branch rows are what
the same URL said with a token and without one, because a single reading cannot
tell a repository that went private from one that was deleted.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where nothing
downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/collaborator-permission-insufficient"] = {
    "flow_intro": (
        "The whole finding is one object that arrives on a call nobody thinks "
        "to read. GET /repos returns a permissions map for the authenticated "
        "user, and the highest true flag in it is the account's role on that "
        "repository. Everything after that is a comparison against a table of "
        "what each role unlocks, done locally, so the script can say the merge "
        "will be refused without going anywhere near the merge. The scopes are "
        "read too, and only so the script can rule them out loudly: a token "
        "holding repo against an account holding read is the exact shape that "
        "sends people to widen a credential that was never the ceiling."
    ),
    "diagram_problem": D.chain(
        "ghrole-p",
        "A write refused by the account's role while the token keeps getting wider",
        "Every token in this chain is correct. The thing being adjusted is not "
        "the thing that says no.",
        [
            ("Merge call refused", "403 on one repository"),
            ("Scopes checked", "repo is ticked"),
            ("Token reminted wider", "workflow added too"),
            ("Refused again", "identically"),
            ("Endpoint blamed", "for a fortnight"),
        ],
        fail_at=1,
        loop=(4, 2, "and a wider token is minted again"),
    ),
    "diagram_fix": D.branch(
        "ghrole-f",
        "Sorting the account's role on one repository against the action it must take",
        "Not one of these rows is about the token. The second row is the one "
        "that ends the search, because no scope can move it.",
        ("permissions on GET /repos", "highest true flag is the role"),
        [
            ("pull only, push false", "read: every write is refused", "bad"),
            ("Role below the action", "raise the role, not the scopes", "bad"),
            ("triage, and a label needed", "sufficient without any write", "good"),
            ("push true, action allowed", "look elsewhere for the 403", "good"),
        ],
    ),
}

V["github/feature-disabled-endpoint-403"] = {
    "flow_intro": (
        "One repository read answers the question, and it answers it for every "
        "feature at once. security_and_analysis carries a status per security "
        "feature and the has_ flags carry the rest, so the script can say which "
        "endpoints this repository will serve before any of them is called. The "
        "third state matters as much as the other two: that block is only "
        "returned to a caller with admin on the repository, so an absent flag "
        "is unreported rather than off, and the reason it is absent is the "
        "reader's own role. The optional probe is a GET per endpoint, and the "
        "status it records is compared against the one a disabled feature is "
        "documented to produce."
    ),
    "diagram_problem": D.chain(
        "ghfeat-p",
        "Permissions granted for a fortnight to an endpoint that wanted a checkbox",
        "The header everybody reaches for is absent here, and its absence is "
        "the signal that gets skipped.",
        [
            ("403 on code scanning", "alerts endpoint"),
            ("Permission granted", "security events read"),
            ("Refused again", "same status"),
            ("Token type changed", "an App this time"),
            ("Feature never enabled", "on the repository"),
        ],
        fail_at=1,
        loop=(3, 1, "and another permission is ticked"),
    ),
    "diagram_fix": D.branch(
        "ghfeat-f",
        "Sorting a refusal by whether the feature is switched off or the grant is missing",
        "One cause, three status codes. The top three rows are all the same "
        "off switch seen through three different endpoint families.",
        ("One repository read", "flags before any alert call"),
        [
            ("Code scanning off", "403, and no permission would help", "bad"),
            ("Secret scanning off", "404, which reads as not found", "bad"),
            ("Issues off", "410 Gone, and it means disabled", "plain"),
            ("Flag enabled, header named", "a permission problem after all", "good"),
        ],
    ),
}

V["github/fork-vs-upstream-confusion"] = {
    "flow_intro": (
        "There is no failure to catch here, so the script compares two "
        "repositories instead of classifying one response. The fork boolean and "
        "source.full_name come off a single read and settle which object the "
        "configuration is pointed at; a second read of the upstream turns that "
        "into a size difference the reader can recognise, in stars, in open "
        "issues, in how long ago each was pushed to. The stored id is checked "
        "against the live one in the same pass, because a name that resolves to "
        "a different object than it did last month is the same bug arriving "
        "without anybody editing the configuration."
    ),
    "diagram_problem": D.chain(
        "ghfork-p",
        "An audit that succeeds at every step and reports on the wrong repository",
        "No arrow in this chain is red because nothing fails. The report is "
        "well formed, delivered on time and about somebody's fork.",
        [
            ("Config copied", "from a personal fork"),
            ("Every call returns 200", "nothing to alert on"),
            ("Zero releases found", "issues empty too"),
            ("Reported as healthy", "a quiet quarter"),
            ("Upstream busy all along", "9,000 issues"),
        ],
        loop=(4, 1, "and next quarter reads the same fork"),
    ),
    "diagram_fix": D.branch(
        "ghfork-f",
        "Sorting a configured repository by whether it is the canonical one",
        "The first and last rows return identical HTTP on every call. Only "
        "the fork boolean and the id separate them.",
        ("fork, parent and source", "read once, before the audit"),
        [
            ("fork true, treated as source", "repoint at source.full_name", "bad"),
            ("Stored id no longer matches", "the name moved to another object", "bad"),
            ("Fork of a fork", "parent and source disagree", "plain"),
            ("fork false, id matches", "this really is the upstream", "good"),
        ],
    ),
}

V["github/private-repo-visibility-changed"] = {
    "flow_intro": (
        "One reading cannot answer this, so the script takes two of the same "
        "URL: once with the token and once with no credential at all. The pair "
        "is the finding. A token that sees 200 beside an anonymous request that "
        "sees 404 is a repository that is no longer public, which is a "
        "different sentence from the repository is gone, and the two are "
        "indistinguishable from either half alone. The unauthenticated rate "
        "limit is read for free alongside, because a limit of 60 is proof that "
        "the caller really was anonymous rather than quietly authenticated by "
        "an environment variable somebody forgot about."
    ),
    "diagram_problem": D.chain(
        "ghvis-p",
        "An anonymous reader losing a repository it had read for years",
        "Nothing in the integration changed. The object it reads changed "
        "underneath it, and the status code chosen for that is the same one "
        "deletion gets.",
        [
            ("Anonymous reads for years", "no token at all"),
            ("Owner flips visibility", "public to private"),
            ("404 on every call", "same URL as yesterday"),
            ("Read as deleted", "the URL is retired"),
            ("Forks detached too", "and blamed on the same thing"),
        ],
        fail_at=1,
        loop=(3, 2, "and the retired URL is never rechecked"),
    ),
    "diagram_fix": D.branch(
        "ghvis-f",
        "Sorting one repository URL by what it answers with a token and without one",
        "Each row is a pair of readings. The first two rows differ only in "
        "what the authenticated half said.",
        ("Same URL, read twice", "once with a token, once without"),
        [
            ("404 anonymous, 200 with token", "private now, and reachable", "bad"),
            ("404 both ways", "gone, or never granted: another note", "plain"),
            ("visibility internal", "private true, but org wide readable", "plain"),
            ("200 both ways", "still public: the 404 is elsewhere", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
