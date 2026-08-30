#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch Y. The last five.

Five notes about a claim that is weaker than it looks, so every branch here
sorts one reading into what it does and does not establish. None of them sorts
a scope, and in four of the five nothing is refused at all.

The first sorts a field. Its chain is a compliance check that has been green
for a year and a half while testing a string anybody can set; the arrow that
fails is the one nobody looks at. Its branch is the only one in the batch whose
rows are values of a single field, and two of those rows mean "unknown", which
is the answer a boolean cannot carry.

The second sorts a status code by what its body points at. Its chain is the
hour that goes into permissions because a 404 is what permissions look like
here, and the loop is the experiment that would settle it by writing. Its
branch is the only one whose rows separate "nothing was routed" from "a handler
answered", and the discriminator is a documentation link.

The third sorts a period against a period. Nothing in its chain is refused
globally: the token authenticates the whole way through and one namespace turns
it away. Its branch is the only one here where two rows carry the same symptom
and different time horizons, because a token that dies early and a schedule
that cannot work look identical on the day they fail.

The fourth sorts a relationship. Its chain is a scope ladder that climbs to
somewhere alarming and changes nothing, because the account never had standing
to widen. Its branch is the only one whose most dangerous row is a success: an
organization listing that answers 200 and returns a third of the data.

The fifth sorts a host. Its chain is the one where the credential is blamed for
a hostname, and its branch is the only one in the batch whose rows are three
independent readings of the same question, one of which survives a redirect.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where
nothing downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the
# module. Every diagram here is constructed at import time, so the theme has to
# be active across exactly this file and no further.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/unverified-commit-signature-assumed"] = {
    "flow_intro": (
        "The whole diagnosis is one list read twice: once by the check that "
        "was written and once by the check that was meant. The first reads a "
        "string the committing client chose and authenticates nothing; the "
        "second reads the verification object GitHub produced. Running both "
        "over the same commits turns an argument about policy into a count of "
        "commits where they disagree, in both directions. Then the reason "
        "field is sorted into families, because a good signature from an "
        "unregistered key and a signature that failed to verify are not the "
        "same finding, and GitHub being unable to check at all is not a "
        "finding about your repository. Last comes the rule, since a report "
        "describes commits that exist and a rule is what stops the next one."
    ),
    "diagram_problem": D.chain(
        "ghvsig-p",
        "A signed commit policy implemented as a check on the commit author string",
        "Every reading here is true and none of them is a signature. The "
        "field being asserted on is not the field that was verified.",
        [
            ("Policy says all signed", "written down"),
            ("Script checks author", "a client set string"),
            ("Green for 18 months", "no commit ever fails"),
            ("Verification never read", "same response"),
            ("Audit asks how", "and there is no answer"),
        ],
        fail_at=1,
        loop=(3, 2, "and the check passes again"),
    ),
    "diagram_fix": D.branch(
        "ghvsig-f",
        "Sorting the verification object by its reason rather than by its boolean",
        "Rows are values of one field. Two of them mean unknown, which is the "
        "answer a boolean was never able to carry.",
        ("One verification object, five fields", "reason before verified"),
        [
            ("Unsigned or rejected", "the finding the policy exists for", "bad"),
            ("Good key, no account", "upload a public key, nothing else", "bad"),
            ("GitHub could not check", "an outage, not a violation", "plain"),
            ("Object absent entirely", "unknown, and never counted either way", "plain"),
            ("Verified and a rule requires it", "the only combination that binds", "good"),
        ],
    ),
}

V["github/missing-endpoint-404-vs-405"] = {
    "flow_intro": (
        "Two reads and a table, and the read that matters is the one nobody "
        "takes: the body rather than the status. A 404 whose documentation "
        "link names a specific endpoint came from that endpoint, so a handler "
        "ran and the question is access. A 404 whose link degrades to the bare "
        "REST index never reached a handler, and then only two things are "
        "left, both checkable without spending anything: the shape of the path "
        "and the verb the documentation gives for a route of that shape. The "
        "one experiment the script will not run is the obvious one. Sending "
        "the verb performs the operation when it is accepted and returns this "
        "same 404 when it is not, so there is no branch of it that answers the "
        "question."
    ),
    "diagram_problem": D.chain(
        "ghverb-p",
        "A path copied correctly from the documentation answering 404 for its method",
        "Nothing here is a permission and every step assumed it was. The "
        "status code carries less than it does on other APIs.",
        [
            ("Path from the docs", "correct, substituted"),
            ("404 on every attempt", "no 405, no Allow"),
            ("Scopes widened", "same 404"),
            ("Token swapped", "same 404"),
            ("Verb never checked", "it is in a library"),
        ],
        fail_at=1,
        loop=(3, 0, "or send the write and see what happens"),
    ),
    "diagram_fix": D.branch(
        "ghverb-f",
        "Sorting a 404 by the documentation link in its body and the shape of the path",
        "The top row is a handler answering; the rest never reached one. The "
        "last row is a request this script declines to make.",
        ("One GET, body and path", "link read before status"),
        [
            ("Link names an endpoint", "a handler answered: access, not routing", "plain"),
            ("Trailing slash or placeholder", "a documented cause of 404", "bad"),
            ("Route takes another verb", "the table names the documented one", "bad"),
            ("Nothing routed, verb fine", "check which host you are talking to", "plain"),
            ("Probe with the write verb", "performs it, or repeats the 404", "good"),
        ],
    ),
}

V["github/org-token-lifetime-policy"] = {
    "flow_intro": (
        "One free call carries the expiry, and one date you supply turns it "
        "into a lifetime. That subtraction is the whole method, because a "
        "token with forty days left could be a short one at its start or a "
        "long one near its end, and only one of those is a policy problem. "
        "The comparison that follows is between two periods rather than "
        "between a date and today, which is what separates this from a "
        "countdown: a rotation interval longer than any permitted lifetime "
        "fails once per cycle forever, and no alert about days remaining will "
        "ever say so. The cap itself is a declared number, because nothing "
        "documented reports it, and the script labels it as declared "
        "throughout rather than dressing an assumption as a reading."
    ),
    "diagram_problem": D.chain(
        "ghcap-p",
        "A token refused at one organization while it authenticates everywhere else",
        "No arrow here is a dead credential. The token is alive and correct "
        "and one namespace will not take it.",
        [
            ("Owner sets a maximum", "in March, quietly"),
            ("Long token still valid", "policy blocks, not shortens"),
            ("One org refuses", "everything else answers"),
            ("Rotate, it recovers", "new token fits the cap"),
            ("Runbook untouched", "still says yearly"),
        ],
        fail_at=1,
        loop=(4, 2, "and it happens again next quarter"),
    ),
    "diagram_fix": D.branch(
        "ghcap-f",
        "Comparing a granted lifetime against a declared cap and a rotation interval",
        "The middle rows share a symptom and differ in horizon. One is a "
        "calendar entry; the other is a schedule that cannot ever work.",
        ("Expiry, issue date, interval", "two periods, one comparison"),
        [
            ("Lifetime over the cap", "refused there, fine everywhere else", "bad"),
            ("Interval longer than lifetime", "breaks once per cycle, forever", "bad"),
            ("This token dies first", "rotate early, the schedule is sound", "plain"),
            ("No issue date supplied", "unknown, and it stays unknown", "plain"),
            ("Interval inside the cap", "and the alert reads the header", "good"),
        ],
    ),
}

V["github/outside-collaborator-invisible-org-data"] = {
    "flow_intro": (
        "The partition is the proof and it costs two reads. Repositories "
        "reached because the account is in an organization arrive under one "
        "affiliation; repositories reached because somebody added the account "
        "to them one at a time arrive under another. Present in the second and "
        "absent from the first, with the organization missing from the "
        "membership list, is an outside collaborator and nothing else is. The "
        "SSO header is read on the same response for a reason: this note is "
        "next door to the one about data GitHub tells you it withheld, and the "
        "difference is that nothing here is announced. Where the header does "
        "say partial, the script stops and hands the case over rather than "
        "drawing a membership conclusion from a list that admits it is short."
    ),
    "diagram_problem": D.chain(
        "ghoutco-p",
        "A scope ladder climbed to no effect because the account is not a member",
        "The repositories work the whole way along. Widening a token cannot "
        "grant a relationship the account never had.",
        [
            ("Repos read fine", "for months"),
            ("Teams call 404s", "same organization"),
            ("read:org added", "no change at all"),
            ("admin:org tried", "no change at all"),
            ("Never a member", "only a collaborator"),
        ],
        fail_at=1,
        loop=(3, 2, "and another scope goes on the token"),
    ),
    "diagram_fix": D.branch(
        "ghoutco-f",
        "Partitioning the account's repositories by the affiliation that reached them",
        "The dangerous row is the one that succeeds. An organization listing "
        "that answers 200 and returns a third of the data raises nothing.",
        ("Two affiliations, one membership list", "partitioned, not counted"),
        [
            ("Collaborator yes, member no", "repos in the org, no standing in it", "bad"),
            ("Org listing answers 200", "public only, no header, no error", "bad"),
            ("Header says partial results", "that is the SAML note, not this", "plain"),
            ("Member, no implicit repos", "read the base permission instead", "plain"),
            ("Member and affiliated", "membership is not what is missing", "good"),
        ],
    ),
}

V["github/enterprise-endpoint-on-dotcom"] = {
    "flow_intro": (
        "Three independent readings of one question, two of them free and "
        "neither needing a credential. The URL you configured is a guess about "
        "where the request lands. The host's own answer to a metadata read "
        "settles which product it is, because an appliance reports its "
        "installed version and github.com does not. The root endpoint map "
        "settles something the other two cannot: its URLs are absolute, so the "
        "host inside them is the host that actually served you, which is the "
        "only reading that survives a redirect or a proxy. The credential is "
        "checked last and by behaviour alone, because a token's prefix names "
        "its class and never the installation that issued it."
    ),
    "diagram_problem": D.chain(
        "ghhost-p",
        "A client talking to a different GitHub installation from the one holding the data",
        "A total failure that reads as a permission problem, because on this "
        "API a 404 is what a permission problem looks like.",
        [
            ("Base URL defaulted", "nobody typed it"),
            ("Every route 404s", "or a flat 401"),
            ("Token blamed", "it was minted today"),
            ("Encoding checked", "whitespace, quoting"),
            ("Wrong installation", "different users entirely"),
        ],
        fail_at=1,
        loop=(3, 2, "and a fresh token is minted"),
    ),
    "diagram_fix": D.branch(
        "ghhost-f",
        "Comparing the configured host, the host's own answer and the host that replied",
        "Three readings of one question. The third row is the only one a "
        "config file could never have given you.",
        ("URL, metadata, root map", "three readings, compared"),
        [
            ("Installed version present", "an appliance, not github.com", "bad"),
            ("HTML instead of JSON", "the web interface, answering 200", "bad"),
            ("Replying host differs", "a redirect the config cannot show", "bad"),
            ("Token rejected outright", "minted at another installation", "plain"),
            ("All three agree", "assert it at startup, not after a week", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
