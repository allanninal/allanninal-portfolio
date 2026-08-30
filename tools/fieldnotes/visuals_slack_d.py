#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch D.

Four notes that all end in a token that will not work, drawn so that nobody can
mistake one for another. Each problem chain fails at a different place: at the
consent screen, at an admin's Manage apps page, in the HR system, and on a clock.
Each fix branch sorts by the evidence its own script actually reads, so the four
right-hand columns share no rows: two scope lists, an error-to-disposition table,
a member directory, and an expiry computed from a stored timestamp. Drawn in
Slack aubergine.

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

V["slack/bot-vs-user-scope-mixup"] = {
    "flow_intro": (
        "The script reads two scope lists off two responses and compares them "
        "against each other, which is the one thing the app configuration page "
        "cannot do for you. The page shows what the app requests. The header "
        "shows what the running credential was given."
    ),
    "diagram_problem": D.chain(
        "sbusr-p",
        "A scope granted to the user token while the bot token makes the call",
        "Every step here succeeds. The scope was requested, approved and "
        "granted, and it landed on the credential the code never uses.",
        [
            ("Scope added in the config", "under User Token Scopes"),
            ("Admin approves the install", "one consent screen, two lists"),
            ("Grant lands on xoxp", "bot list unchanged"),
            ("Code calls with xoxb", "one env var, two tokens"),
            ("missing_scope again", "the reinstall changed nothing"),
        ],
        fail_at=2,
        loop=(4, 0, "add the scope again, reinstall again"),
    ),
    "diagram_fix": D.branch(
        "sbusr-f",
        "Sorting one needed scope by which of the two tokens holds it",
        "The advice splits on whether the scope is offered on both lists. "
        "Telling somebody to move search:read to the bot list costs them an "
        "afternoon looking for a list entry that does not exist.",
        ("Both X-OAuth-Scopes headers", "read from live responses"),
        [
            ("Held by the calling token", "nothing to do here", "good"),
            ("Held by the other token", "move it, or switch the call", "bad"),
            ("Only offered on one list", "the code has to change", "bad"),
            ("Held by neither", "an ordinary missing scope", "plain"),
            ("Held by both", "choose an identity deliberately", "plain"),
        ],
    ),
}

V["slack/token-revoked"] = {
    "flow_intro": (
        "One sweep, then two comparisons. The first asks every token whether it "
        "still authenticates; the second asks whether your store agrees. The "
        "second is where the rows nobody is serving turn up, because a disabled "
        "row produces no errors to notice."
    ),
    "diagram_problem": D.chain(
        "srvk-p",
        "An uninstall that reaches the token immediately and the store never",
        "The row survives the thing it describes. Work keeps being scheduled "
        "for a workspace that removed the app in January.",
        [
            ("Admin removes the app", "Manage apps, one click"),
            ("Slack kills the tokens", "immediately, all of them"),
            ("Event never handled", "not subscribed, or dropped"),
            ("Row still marked active", "scheduler keeps queueing"),
            ("Backoff retries a corpse", "for six weeks"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "srvk-f",
        "Sorting auth.test errors into the jobs they actually imply",
        "These codes are all auth failures and no two want the same treatment. "
        "Folding them into one bucket is how a store gets both a retry storm "
        "and a tombstoned paying customer.",
        ("auth.test per stored row", "error read from the body"),
        [
            ("token_revoked", "tombstone, never retry", "bad"),
            ("account_inactive", "the human, not the app", "bad"),
            ("token_expired", "refresh, then retry", "plain"),
            ("ratelimited", "the only true retry", "plain"),
            ("Live under a disabled row", "a customer you dropped", "bad"),
            ("Authenticates and active", "genuinely serving", "good"),
        ],
    ),
}

V["slack/account-inactive"] = {
    "flow_intro": (
        "The live half of this audit finds what already broke. The half worth "
        "running joins the installer ids against the member directory, which "
        "turns an outage into a register of which automations are standing on "
        "which people."
    ),
    "diagram_problem": D.chain(
        "sacin-p",
        "An integration that stops on the day its installer is offboarded",
        "Nothing in the workspace changed. The app is still installed and "
        "still listed; the credential belonged to a person and the person was "
        "deactivated at two in the morning.",
        [
            ("User token stored", "whoever ran the install"),
            ("Two years of green runs", "nobody records whose token"),
            ("She leaves the company", "SSO deprovisions overnight"),
            ("account_inactive", "app still shows installed"),
            ("Nightly export stops", "the config page looks fine"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sacin-f",
        "Sorting installs by the human account each one depends on",
        "A bot token has no exposure here at all and must be dismissed early, "
        "or the register fills with rows that cannot fail this way and nobody "
        "reads it twice.",
        ("Installer ids joined to users.list", "one paginated sweep"),
        [
            ("Bot token", "outlives everybody", "good"),
            ("Installer already deleted", "down now", "bad"),
            ("Installer active today", "down on their last day", "bad"),
            ("Installer is a guest", "deprovisioned soonest", "bad"),
            ("Row names another person", "monitoring the wrong human", "bad"),
            ("No installer id stored", "recover it while you can", "plain"),
        ],
    ),
}

V["slack/token-expired-rotation"] = {
    "flow_intro": (
        "This is the one finding in the section that exists before any request "
        "fails. The prefix says which regime the install is in and the stored "
        "timestamp says how much of the twelve hours is left, so the report is "
        "written in the afternoon about an outage due at midnight."
    ),
    "diagram_problem": D.chain(
        "srotc-p",
        "An app that works for twelve hours after every deploy and then stops",
        "The nightly redeploy was doing the refreshing. Removing it as an "
        "optimisation is what surfaced a bug that had been there for months.",
        [
            ("Manifest enables rotation", "token_rotation_enabled"),
            ("Install returns a pair", "expires_in 43200"),
            ("Only the access token kept", "refresh half discarded"),
            ("Redeploy hides it nightly", "clock reset each time"),
            ("Cadence slows, app dies", "token_expired at lunchtime"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "srotc-f",
        "Sorting installs by an expiry computed from what was persisted",
        "Reporting only expired tokens means speaking during the outage. The "
        "halfway mark is the row worth printing, because it is still working "
        "while there is time to fix it.",
        ("Prefix plus obtained_at", "arithmetic, no call needed"),
        [
            ("Rotation on, no refresh half", "broken on a timer", "bad"),
            ("Past the halfway mark", "will expire tonight", "bad"),
            ("Expired already", "every call is failing", "bad"),
            ("No timestamp persisted", "nothing to schedule from", "plain"),
            ("Clock and API disagree", "another replica refreshed", "plain"),
            ("Classic xoxb token", "no expiry to manage", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
