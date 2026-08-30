#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch L.

Four notes about a GitHub App whose configuration and whose reality have come
apart, in four different places.

The first is a switch somebody else flipped. The installation still exists, the
App still lists it, and every token it mints is refused, because an owner chose
to suspend rather than to uninstall. The problem chain is a retry loop that can
never succeed, and the fix branch sorts on one timestamp.

The second is a change that was made and never landed. The App's declared
permissions moved forward; the installations kept the grant they accepted, so
some 403 and some do not and the split looks arbitrary. The fix branch is a
diff between two permission maps rather than a lookup in a header.

The third is an event that was never declared. Nothing fails, nothing is
logged, and the handler simply never runs. The gating detail is that an App
cannot subscribe to an event it lacks the permission for, so the repair has
three ordered steps and doing only the last is the common mistake.

The fourth is a narrowing your own code asked for. The installation is wide,
the token minted from it is not, and the 404 arrives from one code path while
every other path using the same App is fine. The fix branch compares the reach
a token has against the reach the job needs.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where
nothing downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further: visuals.py imports several of
# these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/installation-suspended"] = {
    "flow_intro": (
        "One GET carries the finding, and it is not the call that failed. "
        "The installation token can only report the symptom, because a "
        "suspended installation answers every request the same refusing way. "
        "The App JWT reads the installation record itself, where a single "
        "timestamp names the cause, the account and the moment. The output "
        "that matters is not a repair you can run: it is the fact that this "
        "state is not retryable, so the integration should stop rather than "
        "spend the next month failing on a schedule."
    ),
    "diagram_problem": D.chain(
        "ghsusp-p",
        "A suspended installation refusing every call while the retry loop continues",
        "Nothing in the integration changed and nothing in it can help. The "
        "decision that broke it was made in an organization settings page.",
        [
            ("Owner clicks suspend", "instead of uninstall"),
            ("Every call 403s", "and webhooks stop too"),
            ("Backoff kicks in", "treated as a transient"),
            ("Retries forever", "quota burnt on nothing"),
            ("Alert fatigue", "the page is ignored"),
        ],
        fail_at=1,
        loop=(3, 2, "and the next retry is scheduled"),
    ),
    "diagram_fix": D.branch(
        "ghsusp-f",
        "Sorting an installation by the suspended_at field on its own record",
        "Only the first of these is this note. The other three matter because "
        "a blanket 403 looks identical from inside the failing process.",
        ("GET /app/installations", "read suspended_at per row"),
        [
            ("suspended_at is set", "not retryable, ask an owner", "bad"),
            ("The id is not listed", "uninstalled or reinstalled", "bad"),
            ("Listed and active", "the 403 is about something else", "plain"),
            ("Active and reachable", "token lists its repositories", "good"),
        ],
    ),
}

V["github/app-permission-upgrade-not-accepted"] = {
    "flow_intro": (
        "Two GETs and a diff. The first reads what the App declares today, "
        "the second reads what each installation actually granted, and the "
        "answer is the set difference taken per installation rather than "
        "once. That shape is the whole point: a single answer cannot describe "
        "a fleet where some installations accepted the upgrade and some have "
        "not, and the list of the ones that have not is the deliverable."
    ),
    "diagram_problem": D.chain(
        "ghupg-p",
        "An App permission added centrally that installations never accepted",
        "The settings page and the running installations disagree, and every "
        "screenshot taken during the investigation is of the settings page.",
        [
            ("Permission added", "App settings look right"),
            ("Some installs 403", "others are perfectly fine"),
            ("Blamed on caching", "a redeploy is tried"),
            ("Split looks random", "it is per installation"),
            ("Reverted in panic", "which fixes nothing"),
        ],
        fail_at=1,
        loop=(3, 2, "so the App is redeployed again"),
    ),
    "diagram_fix": D.branch(
        "ghupg-f",
        "Diffing the App declaration against each installation grant",
        "The middle two are the reason this is a per installation report. One "
        "fleet can hold all four rows at the same time.",
        ("GET /app and its installations", "compare the permission maps"),
        [
            ("Grant is behind", "owner must accept the request", "bad"),
            ("Behind on one level", "read where write was asked", "bad"),
            ("Grant is ahead", "a permission was removed", "plain"),
            ("Maps agree", "this installation is current", "good"),
        ],
    ),
}

V["github/app-not-subscribed-to-event"] = {
    "flow_intro": (
        "Two GETs, one of which is evidence rather than diagnosis. The App "
        "record names the events it subscribes to and the permissions it "
        "holds, and those two facts are related: an event can only be "
        "declared once the permission gating it is held. The delivery log "
        "confirms from the other side, by showing which events have actually "
        "arrived. The repair has three steps in a fixed order, and the script "
        "prints all three because doing only the last one is the usual "
        "mistake."
    ),
    "diagram_problem": D.chain(
        "ghsub-p",
        "A handler for an event the App was never subscribed to",
        "There is no failure to find. The delivery that would have triggered "
        "the handler was never created, so nothing anywhere records its "
        "absence.",
        [
            ("Handler written", "tested against a fixture"),
            ("Never fires live", "no error, no delivery"),
            ("Receiver debugged", "logs, routing, signature"),
            ("Log is empty", "for that event only"),
            ("Called a GitHub bug", "and worked around"),
        ],
        fail_at=1,
        loop=(3, 2, "so the receiver is instrumented again"),
    ),
    "diagram_fix": D.branch(
        "ghsub-f",
        "Sorting each handled event by subscription and by the permission gating it",
        "The first two are both unsubscribed and they need different repairs, "
        "which is why one bit is not enough to answer with.",
        ("GET /app, events and permissions", "against the events you handle"),
        [
            ("Not subscribed, not permitted", "add the permission first", "bad"),
            ("Not subscribed, permitted", "tick it, then get it accepted", "bad"),
            ("Subscribed, never delivered", "nothing has happened yet", "plain"),
            ("Subscribed and arriving", "seen in the delivery log", "good"),
        ],
    ),
}

V["github/app-token-scoped-down-too-far"] = {
    "flow_intro": (
        "The narrowing happens in a request this script will never make. "
        "Minting a token is a write, so the script reads the token you "
        "already hold and asks what it can actually reach, then compares that "
        "against the repositories and permissions the job says it needs. One "
        "half of the comparison has a blind spot worth stating out loud: a "
        "token cannot report its own permission map, so that half comes from "
        "the mint response your own code received, or not at all."
    ),
    "diagram_problem": D.chain(
        "ghnarr-p",
        "A token narrowed at mint time below what one code path needs",
        "Every other path using the same App works, which is exactly why the "
        "search goes to the App and not to the four lines that minted this "
        "particular token.",
        [
            ("Token minted narrow", "one repo, one permission"),
            ("404 on repo B", "from one job only"),
            ("App settings checked", "the grant is generous"),
            ("Reinstalled on B", "no change at all"),
            ("Permission widened", "still the same 404"),
        ],
        fail_at=1,
        loop=(4, 2, "and the App is widened once more"),
    ),
    "diagram_fix": D.branch(
        "ghnarr-f",
        "Comparing the reach a token has against the reach the job needs",
        "The third row is the honest one. A token that looks fine may still "
        "be narrowed in a way no read can see.",
        ("What this token reaches", "against what the job asked for"),
        [
            ("Repository out of reach", "widen the mint, not the App", "bad"),
            ("Permission below need", "the mint asked for less", "bad"),
            ("Narrowing not visible", "no read returns the grant", "plain"),
            ("Reach covers the job", "the 404 is about something else", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
