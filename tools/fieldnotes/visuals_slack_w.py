#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch W.

Four notes about app configuration, and the risk in a batch like this is that
every picture becomes "a switch was off". So each chain is pinned to a
different moment in a different flow, and each branch sorts a different kind of
thing entirely.

The first fails at the last arrow, which is unusual: the install runs, the user
consents, the browser comes back, and the refusal lands on the one step that
cannot be retried, because the code it was carrying is now spent. The second
has no failing arrow in the app at all - the red step is a decision made
elsewhere, months later, which is why its chain starts with an admin rather
than with a deploy. The third fails at the very last hop, in the user's own
composer, after every call your app made succeeded. The fourth never starts:
its red arrow is the first one, because Slack has no route to send and the
request that would have failed was never made.

The branches sort four different things: the components of two URLs, a cohort
of people, the traffic in a set of DMs, and a set difference between two lists.

Drawn in Slack aubergine. No em dashes inside SVG text: one mis-sniffed
encoding turns a single character into three mojibake ones inside an image,
where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the
# module. Every diagram here is constructed at import time, so the theme has to
# be active across exactly this file and no further.
BRAND = "#4A154B"
D.set_theme(BRAND)

V = {}

V["slack/oauth-redirect-mismatch"] = {
    "flow_intro": (
        "The red arrow is the last one, which is rare in this section and is "
        "the whole character of the failure. Everything before it worked: the "
        "authorize URL was built, the user consented, Slack sent the browser "
        "back to your callback with a code in hand. The refusal lands on the "
        "one step that cannot be attempted twice, because the code it was "
        "carrying is single use and is now spent. That is also why the fix "
        "branch sorts URL components rather than error strings. The answer "
        "has to name which part of the URL disagrees, and it has to reach "
        "that answer without redeeming anything."
    ),
    "diagram_problem": D.chain(
        "skoredir-p",
        "An install that runs perfectly until the token exchange refuses the redirect",
        "Four steps succeed and the fifth cannot be retried. The code is "
        "single use, so the evidence expires with the attempt and the user "
        "has to start the install again from the beginning.",
        [
            ("Add to Slack", "the authorize URL is built"),
            ("The user consents", "scopes shown and accepted"),
            ("Back to the callback", "with a code in the query"),
            ("Exchange the code", "redirect_uri sent as http"),
            ("bad_redirect_uri", "and the code is now spent"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "skoredir-f",
        "Two URLs split into components and compared part by part, with nothing sent",
        "Whole-string comparison answers yes or no. Component comparison "
        "answers which part, which is the difference between a squint and a "
        "repair. Nothing is transmitted and no code is redeemed to reach it.",
        ("Deployed against configured", "scheme, host, port, path"),
        [
            ("Same but for the scheme", "TLS ends at the load balancer", "bad"),
            ("Same but for the port", "a port that exists in a container", "bad"),
            ("A slash on the wrong side", "matching runs forward only", "bad"),
            ("Sent in one leg only", "present in both, or in neither", "bad"),
            ("Covered, and both agree", "the install completes", "good"),
        ],
    ),
}

V["slack/app-access-restricted"] = {
    "flow_intro": (
        "This is the only chain in the batch that does not begin with your "
        "app, and that is the point: nothing in the picture is a bug. An "
        "administrator made a decision, the decision was not announced, and "
        "your code met it months later on one call in a hundred. The red step "
        "is the refusal, and there is no arrow after it because there is "
        "nothing your process can do next. The fix branch sorts people rather "
        "than errors, and the row that keeps it honest is the fourth: without "
        "a group of users who succeeded, an attribute the refused ones share "
        "may simply be what all your users look like."
    ),
    "diagram_problem": D.chain(
        "skappres-p",
        "An admin policy that arrives long after installation and refuses one cohort",
        "The same token, the same server and the same code succeed for one "
        "person and are refused for the next. Retrying re-asks a question "
        "that has already been answered.",
        [
            ("An admin restricts", "months after the install"),
            ("Nothing is announced", "no event, no webhook"),
            ("A call acts for a user", "one of the excluded set"),
            ("app_access_restricted", "no scope, no channel named"),
            ("Retried, and refused", "identically, every time"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skappres-f",
        "Refused callers held against served callers until one attribute separates them",
        "One refusal is bad luck. Two cohorts are a rule. The attribute is "
        "only reported when every refused caller has it and no served caller "
        "does, which is what stops a coincidence becoming a policy.",
        ("Refused beside served", "profiles, teams, groups"),
        [
            ("All guests, none served", "restricted to full members", "bad"),
            ("One team_id, Grid", "not approved on that workspace", "bad"),
            ("One user group holds them", "the grant missed a department", "bad"),
            ("Nothing succeeded at all", "no control group, so no rule", "plain"),
            ("Nobody refused", "the policy is not the problem", "good"),
        ],
    ),
}

V["slack/messages-tab-disabled"] = {
    "flow_intro": (
        "The red arrow is at the very last hop, past the end of anything you "
        "operate. Your call succeeded, Slack stored the message, the user can "
        "read it, and the failure is a composer that will not accept a reply. "
        "That is why the boxes narrow towards a person rather than towards a "
        "server, and why nothing in this chain produces a log line. The fix "
        "branch sorts DM traffic instead of settings, because most readers "
        "have a bot token and no configuration token, and forty conversations "
        "in which no human has ever typed is an answer on its own."
    ),
    "diagram_problem": D.chain(
        "skmtabd-p",
        "A DM that the app can write to and the user cannot answer",
        "Three switches have to agree and only one of them ever produces an "
        "error. This is the shape with none: every call returns ok true and "
        "the conversation is one way by configuration.",
        [
            ("The app DMs a user", "ok true, a real timestamp"),
            ("The message arrives", "visible in the sidebar"),
            ("The user types back", "the composer is greyed out"),
            ("No reply is possible", "read only was left checked"),
            ("Silence, and no error", "on either side of the wire"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skmtabd-f",
        "Every DM the app holds, classified by who has ever spoken in it",
        "Counted across conversations rather than inside one. A single quiet "
        "DM proves nothing; forty in which no person has ever typed is the "
        "finding, and it needs no configuration credential to reach.",
        ("Who spoke, in every DM", "app, person, or nobody"),
        [
            ("Tab off in the manifest", "the app cannot post at all", "bad"),
            ("Only the app has spoken", "read only, or no subscription", "bad"),
            ("Open DMs, all empty", "the surface was never used", "plain"),
            ("Switches right, still one way", "the handler, not the config", "plain"),
            ("People reply and are answered", "the surface is working", "good"),
        ],
    ),
}

V["slack/slash-command-not-registered"] = {
    "flow_intro": (
        "The red arrow here is the first one, and it is the earliest failure "
        "in the batch: Slack has no route for the name, so nothing is ever "
        "sent and no request exists to go wrong. Every box after it is an "
        "absence, which is why the chain ends in a healthy service rather "
        "than in an error. The fix branch is the only one in the batch that "
        "sorts a set difference, and it deliberately reads in both "
        "directions, because the mirror image of a dead handler is a live "
        "command that anybody in the workspace can type."
    ),
    "diagram_problem": D.chain(
        "skslcmd-p",
        "A command typed in Slack that reaches no server because it was never declared",
        "The handler exists, is tested and is deployed. Slack has never heard "
        "of the name, so there is no request, no log line and nothing at all "
        "for the application to report.",
        [
            ("A handler is written", "and reviewed and shipped"),
            ("Somebody types it", "in a real channel"),
            ("Slack has no route", "nothing was declared"),
            ("No request is made", "your access log is empty"),
            ("Not a valid command", "and the service is healthy"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skslcmd-f",
        "Registered commands and handled commands diffed in both directions",
        "Two lists, two gaps, two different victims. One costs you a feature "
        "nobody can reach; the other hands strangers an error with your app "
        "name on it. Reporting only the first leaves half the fault standing.",
        ("Declared beside handled", "after the names are normalised"),
        [
            ("Handled, never declared", "dead code and a puzzled user", "bad"),
            ("Declared, never handled", "anyone typing it gets an error", "bad"),
            ("A name Slack owns", "unavailable in every workspace", "bad"),
            ("Matched by a pattern", "counted, and never guessed at", "plain"),
            ("Both lists agree", "and the app was reinstalled", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
