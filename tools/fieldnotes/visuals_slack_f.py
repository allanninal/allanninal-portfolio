#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch F.

Four notes about how an app is configured rather than how its runtime token is
holding up, and each one is drawn around a different kind of evidence. One
sorts a list of words into three vocabularies and finds the answer in the
grammar. One asks a question it is not allowed to ask directly and reads the
refusal as the answer. One has no error to draw at all, so its problem chain is
a delivery that succeeds while most of its audience is skipped, and its fix
branch is ranked by how many workspaces are installed. And one draws a
credential whose death breaks nothing except the report that was supposed to
notice. Drawn in Slack aubergine.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#4A154B"
D.set_theme(BRAND)

V = {}

V["slack/classic-app-coarse-scopes"] = {
    "flow_intro": (
        "The whole diagnosis is grammar. A scope with a colon belongs to the "
        "current model, a bare word to the one before it, and the two cannot "
        "sit on the same app. So the script sorts the granted list into three "
        "vocabularies and reports which era it is standing in, because the "
        "usual repair of adding a scope has nowhere to land."
    ),
    "diagram_problem": D.chain(
        "sclas-p",
        "A classic Slack app that cannot be given the scope it needs",
        "Nothing here throws. The app works exactly as it has for years, and "
        "the only symptom is a button that is not on the page and a scope name "
        "the documentation no longer knows.",
        [
            ("App created pre-2020", "coarse scopes granted"),
            ("A feature needs a scope", "channels:history"),
            ("No scope picker", "wrong permission model"),
            ("Reinstall attempted", "same grant returns"),
            ("Work postponed", "a rebuild, not an edit"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sclas-f",
        "Sorting a granted scope list by which permission era each name is from",
        "A stale write scope and a coarse scope both read as wrong scopes and "
        "lead opposite ways: one is an afternoon, the other is a second app "
        "and an RTM rewrite.",
        ("X-OAuth-Scopes, one call", "the grant as granted"),
        [
            ("A bare word like bot", "no scope can be added", "bad"),
            ("chat:write:bot", "collapsed, fixable in place", "plain"),
            ("commands, incoming-webhook", "granular without a colon", "good"),
            ("No header at all", "the call never authenticated", "plain"),
            ("All namespaced", "current model, nothing to do", "good"),
        ],
    ),
}

V["slack/app-level-token-missing-connections-write"] = {
    "flow_intro": (
        "The method that would settle this mints a connection, so the script "
        "is not allowed to call it. It asks the neighbouring read method a "
        "question with a made-up argument instead, and takes the complaint "
        "about that argument as proof the credential got past every check "
        "before it."
    ),
    "diagram_problem": D.chain(
        "saltc-p",
        "An app-level token minted with one scope where two were needed",
        "The process stays up and the health check passes. A Socket Mode "
        "client treats a refused connection as transient, so the failure looks "
        "like a workspace that has gone quiet.",
        [
            ("Token generated", "one scope ticked"),
            ("Socket Mode starts", "connections:write absent"),
            ("missing_scope", "no socket opens"),
            ("Client retries", "forever, quietly"),
            ("No events arrive", "nothing has crashed"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "saltc-f",
        "Reading one deliberately wrong probe as a statement about the token",
        "The unusual row is the healthy one: a complaint about the argument "
        "means the credential, the app and the scope were all accepted before "
        "the method looked at it.",
        ("Probe plus exported manifest", "no connection minted"),
        [
            ("invalid_event_context", "credential and scope cleared", "good"),
            ("missing_scope, socket on", "why nothing connects", "bad"),
            ("auth_mismatch", "another app's token", "bad"),
            ("Socket off, no request URL", "no transport at all", "bad"),
            ("No manifest supplied", "say so, do not assume", "plain"),
        ],
    ),
}

V["slack/authorizations-read-missing"] = {
    "flow_intro": (
        "There is no error to sort here, so the script sorts by tenancy "
        "instead. The same missing scope is a customer-facing correctness bug "
        "on a distributed app and a roadmap note on a single workspace, and "
        "reporting both at one severity is how the real one gets ignored."
    ),
    "diagram_problem": D.chain(
        "sazr-p",
        "One Slack event delivered, one installation served, the rest skipped",
        "Every step succeeds. The handler acknowledges inside three seconds "
        "and logs a clean run, and the only wrong number is one nobody "
        "computes: how many installations should have seen this.",
        [
            ("Event seen by many installs", "one delivery sent"),
            ("authorizations truncated", "one entry, by design"),
            ("Length read as audience", "no expansion call"),
            ("Other tenants skipped", "no error, no log"),
            ("Works for some customers", "not for others"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sazr-f",
        "Ranking a missing expansion scope by how many workspaces installed",
        "A single-workspace app is not broken and should not fail the run. It "
        "is one customer away from broken, which is a different sentence and "
        "belongs in a different place.",
        ("Install store plus one probe", "tenancy decides severity"),
        [
            ("Org-wide install, no scope", "workspaces silently dropped", "bad"),
            ("Many teams, no scope", "one tenant per event", "bad"),
            ("One team, no scope", "dormant, fix before you sell", "plain"),
            ("Scope present, many teams", "handler still unverified", "plain"),
            ("One team, scope present", "nothing to fan out", "good"),
        ],
    ),
}

V["slack/config-token-expired"] = {
    "flow_intro": (
        "The finding is not that a credential died. It is what the death does "
        "to the report: six checks that could not run are not six checks that "
        "passed, so the script splits its own list into assessed and deferred "
        "and refuses to summarise the second as clean."
    ),
    "diagram_problem": D.chain(
        "scfgt-p",
        "A twelve-hour app configuration token pasted into a CI secret",
        "The app never notices. What stops is the tooling around it, and the "
        "audit beside it keeps printing a clean summary because a check that "
        "cannot run has nothing to complain about.",
        [
            ("Access token pasted", "into a CI secret"),
            ("Twelve hours pass", "no rotate step"),
            ("Manifest read refused", "token_expired"),
            ("Regenerated by hand", "clock resets"),
            ("Audit reports clean", "six checks never ran"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "scfgt-f",
        "Turning one credential state into an honest statement about coverage",
        "Four different errors carry four different repairs, and every one of "
        "them has the same second consequence: the manifest branch of the "
        "audit is unknown rather than clean.",
        ("One manifest read", "state, then coverage"),
        [
            ("token_expired", "rotate, do not regenerate", "bad"),
            ("missing_scope", "reissue with the read scope", "bad"),
            ("app_not_found", "another app account", "bad"),
            ("Access half stored alone", "fails again tomorrow", "bad"),
            ("Readable, nothing deferred", "the summary means something", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
