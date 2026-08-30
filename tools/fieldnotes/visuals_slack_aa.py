#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch AA.

Five refusals from the same surface, so the pictures are pinned to where each
one actually happens rather than to the error string, which for three of these
five is identical or absent.

The first fails before anything is called. Its red arrow is the very first
one, between an OAuth exchange that returned two credentials and a store that
kept one, and every box after it is months of the app working perfectly for
everything except the surface nobody has asked for yet.

The second fails last. Every step before the final arrow is correct: the
scopes were requested properly, the install completed, the token carries the
grant. The refusal happens when the method looks up a role, which is a
property of a person rather than of the credential, and no earlier box could
have shown it.

The third fails in the middle and then loops. The red arrow is where a
customer on a smaller plan meets a surface their contract does not include,
and the curve underneath is the expensive part: an inconclusive probe stored
as an absence gates the feature off, which stops the probe, which preserves
the wrong answer forever.

The fourth has no error at all. Its red arrow points at silence: an
administrator moves the app to the restricted list, nothing notifies anybody,
and the remaining boxes are six weeks of an error rate that stays flat because
the requests that would have failed were never made.

The fifth fails mid run and only for some resources, and the failure is about
content rather than about the caller. The channel is plainly there; what
cannot be served is what is inside it.

The branches sort five different populations: credentials, people, probe
responses, workspaces and channels. Drawn in Slack aubergine. No em dashes
inside SVG text: one mis-sniffed encoding turns a single character into three
mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the
# module. Every diagram here is constructed at import time, so the theme has to
# be active across exactly this file and no further.
BRAND = "#4A154B"
D.set_theme(BRAND)

V = {}

V["slack/admin-method-needs-user-token"] = {
    "flow_intro": (
        "The red arrow is the first one, and what it points at is not a "
        "failure in Slack. The OAuth exchange did everything right: it "
        "returned a bot token at the top level and a user token underneath "
        "it, each with its own grant, exactly as documented. The box the "
        "arrow lands on is your own install handler keeping one of them, "
        "which is a reasonable thing to do for an app that never touches the "
        "admin surface, and every box after it is that decision being "
        "correct for months. The refusal at the end arrives on the first "
        "call that needs the credential nobody stored. The fix branch sorts "
        "credentials rather than errors, and its second row is the one that "
        "costs people an afternoon: a bot token carrying admin scopes is not "
        "a credential with a problem, it is two credentials being confused "
        "for one."
    ),
    "diagram_problem": D.chain(
        "skadmcred-p",
        "An OAuth exchange that returned two credentials and a store that kept one",
        "Nothing here is broken on Slack's side and nothing fails for "
        "months. The missing half of the grant is only noticed by the first "
        "feature that needs it.",
        [
            ("Two tokens are issued", "bot, and authed_user"),
            ("The handler keeps one", "the bot one, reasonably"),
            ("Everything works", "posting, reading, views"),
            ("An admin feature ships", "the first admin call"),
            ("not_allowed_token_type", "the class was never stored"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "skadmcred-f",
        "Every credential in the environment held against what the methods require",
        "The question is asked of your environment, not of a method. Nothing "
        "on this branch requires calling the admin surface, which is a "
        "family where the neighbouring methods write.",
        ("Each credential, one auth.test", "a class, and a grant"),
        [
            ("No user token at all", "so no admin call can work", "bad"),
            ("A bot token, admin scopes", "two credentials, confused", "bad"),
            ("A user token, short grant", "ask under User Token Scopes", "bad"),
            ("An app level token", "a third surface entirely", "plain"),
            ("A user token, admin scopes", "this is the one to route at", "good"),
        ],
    ),
}

V["slack/not-an-admin"] = {
    "flow_intro": (
        "The red arrow is the last one, which is what makes this refusal so "
        "durable. Read the chain from the left and every box is a step done "
        "properly: the scopes were requested in the right place, the install "
        "was authorised, the token came back carrying the grant it was "
        "supposed to carry. Nothing about the credential is wrong, and every "
        "check you can run on the credential passes. The failure happens at "
        "the far end, where the method stops looking at the token and looks "
        "up a role, and a role is a property of a person. The fix branch "
        "sorts accounts, and the row that matters most is the fourth: a "
        "workspace admin with no enterprise_user object is not a person "
        "without the role, it is a question that could not be answered, and "
        "reporting it as a failure faults every customer on a smaller plan."
    ),
    "diagram_problem": D.chain(
        "skadmrole-p",
        "A correctly issued token refused by a check that reads a person",
        "Four correct steps and then a lookup that has nothing to do with "
        "the credential. The badge on the installer's own profile says admin "
        "throughout, because it describes a different role.",
        [
            ("Scopes asked for properly", "under User Token Scopes"),
            ("A developer installs", "their own account, clicked through"),
            ("The token carries the grant", "every check on it passes"),
            ("The method reads a role", "not the token, the person"),
            ("not_an_admin", "and no reinstall changes it"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "skadmrole-f",
        "Accounts sorted by the role the admin methods actually check",
        "One users.info answers two questions with the same field name. The "
        "workspace role is the one on the profile badge; the org role is the "
        "one the methods read, and only the second decides anything.",
        ("The account behind the token", "two roles, one field name"),
        [
            ("Org admin or owner", "the methods will accept this", "good"),
            ("Org role read, both false", "the finding, stated plainly", "bad"),
            ("Held the role in March", "and does not hold it now", "bad"),
            ("No enterprise_user object", "unknown, and never a failure", "plain"),
            ("Someone else holds it", "name them, and ask them", "plain"),
        ],
    ),
}

V["slack/feature-not-enabled"] = {
    "flow_intro": (
        "Two things go wrong here and the second is worse than the first. "
        "The red arrow is where a customer on a smaller plan meets a surface "
        "their contract does not include, which is nobody's mistake and is "
        "repaired by a branch in your code rather than by a change in "
        "theirs. The curve underneath is the expensive one. A probe that was "
        "refused for some other reason gets recorded as this reason, the "
        "feature is gated off on the strength of it, and a gated feature is "
        "never probed again, so the wrong answer preserves itself "
        "indefinitely and the customer's administrator cannot work out why a "
        "capability they pay for is invisible. The fix branch sorts probe "
        "responses into the flag each one is allowed to set, and only the "
        "second row is allowed to switch anything off."
    ),
    "diagram_problem": D.chain(
        "skadmplan-p",
        "A capability assumed at build time and a wrong answer that preserves itself",
        "The refusal is a plan boundary. The loop underneath is the audit "
        "storing an inconclusive probe as an absence, which removes the only "
        "thing that could ever correct it.",
        [
            ("Built on a Grid sandbox", "where everything answers"),
            ("Shipped to 400 installs", "one call path, no branch"),
            ("A Business+ tenant", "same code, same token"),
            ("feature_not_enabled", "the plan, not the caller"),
            ("The flag is stored off", "on whatever came back"),
        ],
        fail_at=2,
        loop=(4, 1, "gated off, so never probed again"),
    ),
    "diagram_fix": D.branch(
        "skadmplan-f",
        "Probe responses sorted by the feature flag each one is entitled to set",
        "Four refusals arrive at the same catch block and only one of them "
        "is about the plan. A false off is invisible and permanent. A false "
        "retry costs one request.",
        ("One probe per tenant", "and what it may conclude"),
        [
            ("Answered ok", "available, and store it on", "good"),
            ("feature_not_enabled", "the only off switch there is", "bad"),
            ("not_an_admin", "retry; the plan was not tested", "plain"),
            ("not_allowed_token_type", "retry; the plan was not tested", "plain"),
            ("Rate limited mid sweep", "retry; ask again later", "plain"),
        ],
    ),
}

V["slack/app-restricted-by-admin"] = {
    "flow_intro": (
        "The red arrow points at nothing happening, which is the hardest "
        "kind of failure to notice. An administrator moves the app from one "
        "list to another, or a member raises an approval request that goes "
        "into a queue, and from that moment the thing that changes is a "
        "number that was never being watched: installs, for one customer. No "
        "error is generated anywhere, because the calls that would have "
        "failed were never made. Every box after the arrow is six weeks of "
        "flat, healthy metrics. The fix branch sorts workspaces, one pair of "
        "reads each, and its fourth row is the one to be careful with: an "
        "app on neither list is not a cleared app, it is an app whose status "
        "depends on a setting these methods do not return."
    ),
    "diagram_problem": D.chain(
        "skadmmap-p",
        "An administrative decision that generates no error anywhere",
        "The signal is an absence. Installs from one customer stop, the "
        "error rate stays flat because nothing failed, and the first person "
        "to notice is in support, months later.",
        [
            ("The app works everywhere", "37 workspaces, happily"),
            ("An admin restricts it", "in three of them, quietly"),
            ("Nothing notifies anyone", "no event, no field, no mail"),
            ("Installs simply stop", "for those workspaces only"),
            ("A support ticket, later", "about a rollout that did not"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skadmmap-f",
        "Each workspace in the organization checked against both lists",
        "The lists are kept per workspace, so the answer is a map rather "
        "than a status. A split names the workspaces, and the names are the "
        "whole message to an administrator.",
        ("Each workspace, both lists", "plus the request queue"),
        [
            ("On the restricted list", "named, and actionable today", "bad"),
            ("A request aged 41 days", "nobody refused you, or read it", "bad"),
            ("On both lists at once", "rare, and worth raising", "plain"),
            ("On neither list", "not cleared; the setting is unread", "plain"),
            ("On the approved list", "installs work here", "good"),
        ],
    ),
}

V["slack/ekm-access-denied"] = {
    "flow_intro": (
        "The red arrow is in the middle and it separates two things that "
        "look identical from inside a catch block. Everything to the left is "
        "an ordinary working integration; the arrow is a key being revoked "
        "somewhere inside the customer's organization, which is an event "
        "your app has no view of and no part in. What follows is the "
        "expensive habit rather than the refusal itself: a job that retries a "
        "decision runs for an hour, burns quota that other calls needed, and "
        "ends with the same eleven failures. The fix branch sorts channels "
        "by what each of two reads returned, because the pair is the "
        "diagnosis: a channel whose metadata answers while its content is "
        "refused is plainly there, and what cannot be served is what is "
        "inside it."
    ),
    "diagram_problem": D.chain(
        "skadmekm-p",
        "A key revoked inside the customer and a retry loop that cannot help",
        "The scope list is checked first, because that is what this looks "
        "like, and there is nothing wrong with it. The refusal is about "
        "content held under a key, and it does not clear.",
        [
            ("200 channels, all working", "for a year and a half"),
            ("A key is revoked", "inside the customer, on a Thursday"),
            ("ekm_access_denied", "on eleven of them, not 200"),
            ("The scopes are checked", "twice, and they are fine"),
            ("The job retries forever", "and finishes with 11 failures"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skadmekm-f",
        "Channels sorted by what the metadata read and the content read each returned",
        "Two reads per channel, and the disagreement between them is the "
        "finding. Nothing is written to establish any of it, and the "
        "affected set is the message an administrator can act on.",
        ("Each channel, read twice", "metadata, then content"),
        [
            ("Visible, content refused", "the characteristic shape", "bad"),
            ("Both layers refused", "broader, same cause", "bad"),
            ("Refused for another reason", "a scope, or an invitation", "plain"),
            ("channel_not_found", "absent, or invisible, undecided", "plain"),
            ("Both layers answer", "nothing wrong with this one", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
