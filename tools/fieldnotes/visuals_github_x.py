#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch X.

Four notes about organization policy rather than about credentials, which is
the line that keeps them off the token shelf this section already publishes. In
every chain here the token is valid the whole way through, and none of the four
branches sorts a scope.

The first sorts a refusal by what its body contains. Its chain is the loop
people run when a job fails in CI and passes on a laptop: every experiment
varies the credential, and the credential was never the variable. Its branch is
the only one in the batch whose rows are causes of one status code, and the row
that matters is the one holding an address.

The second sorts a membership. Its chain has no refusal in it at all, because
the account did not lose a permission, it left the organization without moving.
Its branch rows are statuses of one endpoint, and the finding is a redirect,
which is the row every default HTTP client throws away.

The third sorts a count against a count. Nothing in its chain fails either: the
job succeeds, faster than usual, on a tenth of the data. Its branch is the only
one here where two rows carry the same coverage and different causes, because a
short list has more than one way of getting short.

The fourth sorts an account against two records: what the App has and what the
product believes. Its branch is the only one whose rows are disagreements
rather than states, and one row points at a note that owns the case where the
installation is real.

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

V["github/ip-allow-list-blocks-requests"] = {
    "flow_intro": (
        "The whole diagnosis is one probe read twice over: once for its status "
        "and once for its body. A refusal from this API can be four things, "
        "and exactly one of them contains an IP address, so the script sorts "
        "on the presence of an address rather than on a sentence GitHub can "
        "reword. That address is also the finding, because it is the one "
        "GitHub applied the rule to, which is better evidence than any echo "
        "service about what this job really egresses through. The list itself "
        "is read only where the token is allowed to read it, and where it is "
        "not, the script says the rule is unreadable rather than implying it "
        "is empty."
    ),
    "diagram_problem": D.chain(
        "ghipal-p",
        "A job refused in CI and accepted on a laptop while every experiment varies the token",
        "Every reading in this chain is true and none of them touches the "
        "rule. The variable being changed is not the variable.",
        [
            ("403 on the runner", "one organization"),
            ("Token tried locally", "and it works"),
            ("Scopes widened", "same refusal"),
            ("Public repo probed", "answers 200"),
            ("Address never allowed", "on the org list"),
        ],
        fail_at=1,
        loop=(3, 2, "and another credential is minted"),
    ),
    "diagram_fix": D.branch(
        "ghipal-f",
        "Sorting one 403 by what its body carries, and comparing the address against the list",
        "Four causes, one status code. Only the top row names an address, "
        "which is what makes the sort survive a reworded sentence.",
        ("One probe, body and headers", "sorted before anything is believed"),
        [
            ("Body names an address", "the source address, not the token", "bad"),
            ("Entry exists but is off", "switch it on, do not add a second", "bad"),
            ("Quota or secondary limit", "a different 403 with its own repair", "plain"),
            ("Covered and still refused", "look at which org the call named", "good"),
        ],
    ),
}

V["github/org-2fa-requirement-removed-member"] = {
    "flow_intro": (
        "Two reads settle this and the second one has to be sent carefully. "
        "GET /user proves the credential is healthy, which is the line that "
        "ends the search everybody runs first. The membership call is then "
        "sent with redirects disabled, because its 302 means the account "
        "asking is not a member, and asking about yourself that redirect is "
        "the finding. A client that follows it lands on the public members "
        "endpoint and answers a question about public listing instead, just as "
        "confidently. The motive is read last and is often unreadable, because "
        "losing organization access is exactly what the removal did."
    ),
    "diagram_problem": D.chain(
        "gh2fa-p",
        "A machine account removed by a policy change while its token stays valid",
        "Nothing here is refused. The account stopped being a member, and a "
        "non-member sees private repositories the way a stranger does.",
        [
            ("2FA required", "owner enables it"),
            ("Non compliant accounts out", "removed, not refused"),
            ("Token still valid", "GET /user is 200"),
            ("Org repos all 404", "not 403"),
            ("Credential blamed", "for a week"),
        ],
        fail_at=1,
        loop=(4, 2, "and the token is rotated again"),
    ),
    "diagram_fix": D.branch(
        "gh2fa-f",
        "Sorting one membership read taken with redirects disabled",
        "Each row is a status from one endpoint. The first row is the one a "
        "redirect following client never sees.",
        ("Membership read, redirects off", "204, 302 or 404"),
        [
            ("302 asking about yourself", "the requester is not a member", "bad"),
            ("Requirement on, 2FA off", "a removal that has not happened yet", "bad"),
            ("Requirement unreadable", "losing access is the finding", "plain"),
            ("204 and compliant", "membership is not your 404", "good"),
        ],
    ),
}

V["github/org-base-permission-changed"] = {
    "flow_intro": (
        "This one is measured rather than caught, because nothing fails. The "
        "organization read gives the base permission and the size of the "
        "organization; one more request, asking for a single item per page, "
        "gives the number of repositories the account can actually reach, "
        "because at one per page the last page number is the count. Two "
        "numbers, one comparison, and the grade is a word rather than a ratio "
        "so it can be alerted on. The script will not blame the field it just "
        "read: a coverage that collapsed while the base permission still "
        "grants implicit access is somebody else's note, and it says so."
    ),
    "diagram_problem": D.chain(
        "ghbase-p",
        "An inventory job that succeeds on a tenth of the repositories it used to cover",
        "No arrow in this chain is red because nothing fails. The run is "
        "clean, fast and wrong about four hundred repositories.",
        [
            ("Base permission tightened", "read to none"),
            ("Implicit access ends", "org wide, at once"),
            ("Job still succeeds", "no errors at all"),
            ("Nine repos reported", "of four hundred"),
            ("Green dashboard", "for a fortnight"),
        ],
        loop=(4, 2, "and next week reports nine again"),
    ),
    "diagram_fix": D.branch(
        "ghbase-f",
        "Sorting a shorter repository list by the organization default and a coverage count",
        "The middle rows carry the same shortfall and different causes, which "
        "is why the base permission is read before it is blamed.",
        ("Base permission and a count", "one field, one page number"),
        [
            ("none, coverage collapsed", "implicit access is gone", "bad"),
            ("read, coverage collapsed", "not this field: look elsewhere", "plain"),
            ("Field unreadable", "a measurement with no explanation", "plain"),
            ("none, coverage intact", "grants are explicit and immune", "good"),
        ],
    ),
}

V["github/app-installation-request-pending"] = {
    "flow_intro": (
        "The API can only supply half of this, and the note is built around "
        "saying which half. GET /app/installations lists what the App really "
        "has, and a per account probe confirms an absence one account at a "
        "time. Neither of them reports a pending request, because nothing "
        "does: absence covers pending, declined and never started with the "
        "same silence. The other half is your own record of who began a flow "
        "and when, and the reconciliation between the two runs in both "
        "directions, since an installation the product never noticed is the "
        "same bug seen from the far side."
    ),
    "diagram_problem": D.chain(
        "ghpend-p",
        "A product showing a connection for an App installation that was only ever requested",
        "Both sides are telling the truth. The user completed a flow and the "
        "App was never installed, and no call in between disagrees.",
        [
            ("Non owner installs", "it becomes a request"),
            ("Owner never approves", "one notification"),
            ("Product says connected", "the flow completed"),
            ("No events, no repos", "nothing to debug"),
            ("Webhooks blamed", "for three weeks"),
        ],
        fail_at=1,
        loop=(4, 0, "and the user starts the flow again"),
    ),
    "diagram_fix": D.branch(
        "ghpend-f",
        "Reconciling the App's own installation list against the product's connection record",
        "Every row is a disagreement between two records. The third row is "
        "the one that sends you to a different note entirely.",
        ("What the App has, what you believe", "reconciled both ways"),
        [
            ("Connected, nothing installed", "requested and never approved", "bad"),
            ("Installed, not recorded", "approved after the user gave up", "bad"),
            ("Installed and suspended", "the approval is not what is missing", "plain"),
            ("Both agree", "nothing here to reconcile", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
