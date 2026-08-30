#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch W.

Four notes about an organization refusing a credential it has no complaint
about. None of these branches sorts a scope or a permission, which is the line
that keeps them off the token notes already published: every row here is about
admission rather than about capability.

The first two are drawn as a pair and have to stay one. Both chains end in a
refusal that looks identical, so what separates them on the page is what each
branch sorts. The first sorts the form of one response header, which anybody
holding the refused credential can read. The second sorts a dated record only an
owner can see, and its rows carry days rather than statuses, because the useful
version of that note is the run you make while everything still works.

The third sorts a matrix rather than a response. Its rows are pairs of readings
taken with the same token in two namespaces, plus the one taken with no token at
all, which is the row that turns an argument into a fact: refused where an
anonymous caller succeeds.

The fourth sorts a shape. Its branch is the only one in the batch whose rows are
patterns instead of values, because the whole finding is whether refusals
cluster around one owner or around one endpoint family, and no single response
carries that.

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

V["github/saml-token-not-authorized"] = {
    "flow_intro": (
        "Three reads and a header parser. The pair of organization reads is "
        "there to rule out the boring explanations before the header is "
        "trusted: a name that does not resolve fails both, a dead credential "
        "fails everything, and SAML enforcement is the case where the public "
        "record answers and the listing does not. Then the header does the "
        "work. Its required form carries the URL that is the entire repair, "
        "and its partial-results form belongs to another note, so the script "
        "sorts on the form rather than on the header being present. The last "
        "read is local: the credential's prefix decides whether a click can "
        "help it at all, because sending an installation token to an SSO page "
        "costs a day and explains nothing."
    ),
    "diagram_problem": D.chain(
        "ghsamlau-p",
        "A new token refused by an organization while the token keeps getting wider",
        "Every credential in this chain is valid. The organization is not "
        "arguing about what the token may do.",
        [
            ("Fresh token minted", "every scope ticked"),
            ("Org call refused", "403, then a bare 404"),
            ("Wider token minted", "and reissued twice"),
            ("Refused identically", "in the same millisecond"),
            ("Header never read", "it was on the failure"),
        ],
        fail_at=0,
        loop=(3, 2, "and another credential is minted"),
    ),
    "diagram_fix": D.branch(
        "ghsamlau-f",
        "Sorting a refusal by the form of the x-github-sso header on it",
        "The header is sorted by form, not by presence. The top two rows carry "
        "the same header name and mean opposite things.",
        ("x-github-sso on the reply", "form first, then its parameters"),
        [
            ("required, plus a URL", "never authorized: one human click", "bad"),
            ("partial-results, plus IDs", "nothing refused: another note", "plain"),
            ("Absent on a 403", "not SAML: read the scopes instead", "plain"),
            ("Absent on a 200", "admitted to this organization today", "good"),
        ],
    ),
}

V["github/saml-session-expired"] = {
    "flow_intro": (
        "This script holds two credentials and asks one about the other. The "
        "one in trouble supplies eight characters for a match that happens in "
        "memory and is never printed; an owner's credential reads the "
        "authorization record, because a credential is not allowed to see its "
        "own grant. What comes back is a date. Expired yesterday, expiring in "
        "three days and good for another month are three different sentences, "
        "and only the second one is worth being woken up for, which is why the "
        "best run of this script is the one made while everything still works. "
        "No record at all is its own finding: a credential that was never "
        "authorized is the sibling note rather than a lapse."
    ),
    "diagram_problem": D.chain(
        "ghsamlex-p",
        "A nightly job failing on a schedule nobody recognises",
        "The rerun did not fix it. A person logging into a browser two minutes "
        "earlier did, and nobody wrote that down.",
        [
            ("Six weeks of green", "nothing changed"),
            ("403 on every org call", "SAML enforcement"),
            ("Someone opens GitHub", "and signs in"),
            ("Rerun succeeds", "closed as transient"),
            ("Fails again in eight days", "at a new hour"),
        ],
        fail_at=0,
        loop=(4, 1, "and the next ticket says flaky"),
    ),
    "diagram_fix": D.branch(
        "ghsamlex-f",
        "Sorting one credential authorization record by the date it expires",
        "Rows carry days rather than status codes. The second one is the "
        "reason to run this while nothing is broken.",
        ("credential-authorizations", "matched on the last eight, in memory"),
        [
            ("Expiry in the past", "lapsed: renew, and it will recur", "bad"),
            ("Expiry within a week", "a date, early enough to plan for", "plain"),
            ("No record at all", "never authorized: the sibling note", "plain"),
            ("Weeks of headroom", "and a reason to move off user tokens", "good"),
        ],
    ),
}

V["github/oauth-app-access-restricted"] = {
    "flow_intro": (
        "The verdict here is a shape and two absences. One token reads its own "
        "namespace and then the organization's, and personal succeeding beside "
        "organization refused is a gate around the organization rather than a "
        "complaint about the credential. The first absence is the SAML header, "
        "whose presence would make this somebody else's note, so the script "
        "records not finding it as a reading rather than as nothing. The "
        "second is that no endpoint publishes the policy at all, which is why "
        "the message string is scored separately as corroboration. The "
        "anonymous read costs nothing against core quota and produces the line "
        "no one can argue with: refused where no credential at all succeeds."
    ),
    "diagram_problem": D.chain(
        "ghoauthr-p",
        "An integration invisible to one customer and perfect for every other",
        "Two people are looking at different halves of this. Only one of them "
        "can see the half that matters.",
        [
            ("Works for nine orgs", "same code, same scopes"),
            ("One org sees nothing", "403 on every call"),
            ("Author checks the app", "registration is correct"),
            ("User reauthorizes", "twice, then a new account"),
            ("Policy invisible to both", "it names the app"),
        ],
        fail_at=1,
        loop=(3, 1, "and the ticket is reopened"),
    ),
    "diagram_fix": D.branch(
        "ghoauthr-f",
        "Sorting a refusal by two namespaces and by the headers that are absent",
        "The bottom row is free and decisive. A token refused where no token "
        "succeeds is blocked, not under-privileged.",
        ("One token, two namespaces", "plus one read with no token"),
        [
            ("Personal 200, org 403", "an org gate, not a credential", "bad"),
            ("No SSO header on it", "an app policy, not SAML", "bad"),
            ("Accepted-scopes header", "a scope after all: another note", "plain"),
            ("Anonymous 200, token 403", "blocked below no credential", "good"),
        ],
    ),
}

V["github/fine-grained-pat-pending-approval"] = {
    "flow_intro": (
        "Six cheap reads and one question: do the refusals cluster around an "
        "owner or around an endpoint family. A permission the token lacks "
        "fails the same family everywhere, including on repositories the "
        "account owns outright. A token waiting in an approval queue fails "
        "every family under one owner and none of them at home. That is the "
        "whole diagnosis, and it is arithmetic over six numbers, which is why "
        "the script refuses to answer on one organization family alone. The "
        "permissions header is read and then explicitly set aside: it "
        "describes the endpoint and never the token, so it agrees with the "
        "settings page and settles nothing. Where an owner's credential is "
        "offered, the pending request adds a date to the finding."
    ),
    "diagram_problem": D.chain(
        "ghfgpend-p",
        "A correctly permissioned token refused on everything an organization owns",
        "The move in the middle is the expensive one. A replacement token files "
        "a second request behind the first.",
        [
            ("Token created", "permissions ticked"),
            ("Org calls 403", "personal calls fine"),
            ("Header names a permission", "the token already holds it"),
            ("Token deleted and remade", "queue gets longer"),
            ("Owner never told", "the request waits"),
        ],
        fail_at=1,
        loop=(3, 0, "and a third token is minted"),
    ),
    "diagram_fix": D.branch(
        "ghfgpend-f",
        "Sorting refusals by whether they cluster around an owner or an endpoint",
        "These rows are patterns, not values. No single response carries the "
        "one thing that separates the top two.",
        ("Six reads, two namespaces", "three endpoint families each"),
        [
            ("Every org family refused", "owner-shaped: waiting for approval", "bad"),
            ("One family refused at home too", "endpoint-shaped: a permission", "plain"),
            ("Only one family read", "not enough to name a cause", "plain"),
            ("Org families answering", "the owner has admitted this token", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
