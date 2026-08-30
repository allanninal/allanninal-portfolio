#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch E.

Four notes that all sit under the word "token" and none of which reaches its
answer the same way. One follows a clock: two workers, one secret, sixty
seconds. One never leaves the machine: the first eight characters of a string
settle it. One follows a single call as it is refused by a method rather than by
Slack. And one has no failure to draw at all, so its problem chain is a scope
list growing while nothing goes wrong, and its fix branch sorts by what a leak
would cost rather than by what broke. Drawn in Slack aubergine.

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

V["slack/refresh-token-reused"] = {
    "flow_intro": (
        "The script reads timestamps before it reads Slack. Two redemptions "
        "inside the lock window is the finding, and the live call exists only "
        "to say whether it has landed yet: expired means it has, and ok means "
        "the same bug is still waiting."
    ),
    "diagram_problem": D.chain(
        "srtr-p",
        "Two replicas redeeming one single-use Slack refresh token",
        "The replay usually succeeds. Both workers get a valid pair, both write "
        "one, and the breakage arrives a cycle later when the stored half turns "
        "out to be the superseded one.",
        [
            ("Cron fires on both", "one installation"),
            ("Both redeem at once", "the token is single use"),
            ("Two pairs issued", "last write wins"),
            ("Third redemption", "oldest retired"),
            ("Every call refused", "only OAuth recovers"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "srtr-f",
        "Sorting refresh history by the shape of the misuse, not by the symptom",
        "A missing lock and a retried timeout produce the identical error and "
        "need opposite repairs, so the split has to happen before anyone is sent "
        "to fix something.",
        ("Ledger plus one auth.test", "timestamps and worker ids"),
        [
            ("Two workers, one minute", "no lock anywhere", "bad"),
            ("Same worker, after a timeout", "a retry spent it twice", "bad"),
            ("Three in twelve hours", "over the active limit", "bad"),
            ("Expired, ledger clean", "the loop never ran", "plain"),
            ("Once per window", "serialised and healthy", "good"),
        ],
    ),
}

V["slack/invalid-auth-wrong-token-type"] = {
    "flow_intro": (
        "The whole finding is available before a packet leaves the machine: a "
        "prefix names the class, and the variable it sits in names the role. "
        "The one call afterwards exists to separate a wrong class from a right "
        "class with a newline stuck on the end."
    ),
    "diagram_problem": D.chain(
        "siat-p",
        "An app-level token copied into the slot the Web API reads",
        "Nothing about the error names the mistake. invalid_auth is what Slack "
        "says for a revoked token, a truncated one, and a class this endpoint "
        "has never accepted.",
        [
            ("Two config pages", "both show a token"),
            ("xapp copied", "into the bot slot"),
            ("Web API refuses", "invalid_auth"),
            ("Read as stale", "app reinstalled"),
            ("Same variable", "same error again"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "siat-f",
        "Sorting each credential by its prefix against the role of its slot",
        "A working Socket Mode token must come back clean. An audit that flags "
        "a correctly configured xapp credential is one nobody runs a second "
        "time.",
        ("Prefix, slot and hygiene", "checked offline"),
        [
            ("xapp in a Web API slot", "never accepted there", "bad"),
            ("Refresh token as access", "only the other half is one", "bad"),
            ("Trailing newline", "same error, different fix", "bad"),
            ("xoxc from the browser", "a person's session", "bad"),
            ("xapp in the socket slot", "exactly where it belongs", "good"),
        ],
    ),
}

V["slack/not-allowed-token-type"] = {
    "flow_intro": (
        "Every probe is sent the credential its family calls for, and the "
        "answer is read as a statement about class. The unusual row is the "
        "argument error: a method checks the credential before it checks the "
        "arguments, so a complaint about arguments is a confirmation."
    ),
    "diagram_problem": D.chain(
        "snatt-p",
        "One method refusing a token that a dozen others accept",
        "The token is valid and in the right variable. The error names what is "
        "wrong with the class you brought and says nothing about which class "
        "the method wanted.",
        [
            ("One client, one token", "used everywhere"),
            ("admin method called", "with the bot token"),
            ("not_allowed_token_type", "class refused"),
            ("Scopes added instead", "wrong screen"),
            ("Error unchanged", "no bot scope exists"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "snatt-f",
        "Reading one probe's error as a statement about token class",
        "missing_scope has to leave this branch entirely. It means the class "
        "was accepted and the grant was short, and treating it as a class "
        "problem sends people to a different page for a different repair.",
        ("Probe, with the right class", "auth.test first"),
        [
            ("not_allowed_token_type", "the class is wrong", "bad"),
            ("Argument complaint", "the class was accepted", "good"),
            ("Answered ok", "nothing to route", "good"),
            ("missing_scope", "grant, not class", "plain"),
            ("invalid_auth", "the credential itself", "plain"),
        ],
    ),
}

V["slack/over-broad-scopes"] = {
    "flow_intro": (
        "There is no error anywhere in this one, so the script compares two "
        "lists instead: the grant Slack returns in a header, and the methods "
        "the code actually calls. A method it cannot map is reported rather "
        "than ignored, because ignoring it turns a gap in the audit into a "
        "confident instruction to delete something."
    ),
    "diagram_problem": D.chain(
        "sobs-p",
        "A scope list growing on a token while nothing ever fails",
        "Every step here succeeds. That is the whole problem: nothing in the "
        "loop ever removes a scope, because removing one needs a reinstall and "
        "the scope is not breaking anything today.",
        [
            ("missing_scope once", "needed is an OR list"),
            ("All of them added", "reinstall, move on"),
            ("Feature abandoned", "scopes stay"),
            ("Token leaks to a log", "full grant, no attenuation"),
            ("Archive readable", "nothing was ever broken"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "sobs-f",
        "Ranking unjustified scopes by what a leak of this token would cost",
        "An unused emoji read is tidying. An unused admin scope is an incident "
        "waiting for a laptop backup, and flattening the two into one list is "
        "how the real finding gets ignored.",
        ("Grant against call sites", "header versus inventory"),
        [
            ("admin, no call site", "acts across the org", "bad"),
            ("A write on a reader", "should hold none", "bad"),
            ("Email and history", "staff list, full archive", "bad"),
            ("Method not in the table", "cannot conclude yet", "plain"),
            ("Every scope has a caller", "least privilege holds", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
