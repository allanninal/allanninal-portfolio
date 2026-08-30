#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch C.

These four are about questions the API answers only if you ask them precisely.
Every problem chain here ends in something that looks like success: a lookup that
returns a row, a call that returns 200, a profile that returns fields, a channel
that stays calm. So every fix branch spends most of its rows separating the one
state that is a finding from the several that merely resemble it. Drawn in Slack
aubergine.

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

V["slack/enterprise-id-not-stored"] = {
    "flow_intro": (
        "The script compares each stored key against the identity its own token "
        "reports, then looks across rows for the collision itself. Both halves are "
        "needed: a row can look perfectly consistent on its own and still be the "
        "second of two rows fighting over one key."
    ),
    "diagram_problem": D.chain(
        "sgrid-p",
        "A team id key that resolves to the wrong tenant on Enterprise Grid",
        "Nothing here fails. The lookup finds a row, the row holds a working "
        "token, and the call succeeds in a workspace that belongs to somebody "
        "else.",
        [
            ("Two installs, one org", "same team id shape"),
            ("Store keyed on team id", "enterprise id dropped"),
            ("Second write wins", "first row overwritten"),
            ("Lookup returns a token", "valid, wrong tenant"),
            ("Message lands next door", "ok is true"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sgrid-f",
        "Sorting stored rows by whether they round trip to auth.test",
        "A workspace install off Grid is genuinely fine today, and reporting it "
        "as a finding buries the two rows that are leaking right now.",
        ("auth.test per stored token", "compared against the key"),
        [
            ("Org, team and flag kept", "the row round trips", "good"),
            ("Enterprise id dropped", "cannot tell tenants apart", "bad"),
            ("Org wide under team key", "covers workspaces with no row", "bad"),
            ("One team, two orgs", "leakage already happening", "bad"),
            ("No org at all", "adequate until they migrate", "plain"),
        ],
    ),
}

V["slack/files-upload-retired"] = {
    "flow_intro": (
        "One probe settles the method and one listing dates the damage. The "
        "listing is restricted to the app's own uploads, because every other "
        "file in the workspace was put there by something that still works."
    ),
    "diagram_problem": D.chain(
        "sfupl-p",
        "A fleet of small tools that all stopped uploading on one day",
        "No deploy went out that week. A sunset announced eighteen months "
        "earlier arrived, and every caller of one method met it at once.",
        [
            ("Sunset date arrives", "12 November 2025"),
            ("files.upload refuses", "method_deprecated"),
            ("Answer is HTTP 200", "error sits in the body"),
            ("Scripts read the status", "logged as uploaded"),
            ("Screenshots stop", "nothing queued anywhere"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sfupl-f",
        "Reading the probe error as the answer it actually is",
        "missing_scope is the trap: it means the probe never reached the method, "
        "so it proves nothing, and folding it into good news is how a dead fleet "
        "gets a clean report.",
        ("files.upload, no arguments", "cannot create anything"),
        [
            ("method_deprecated", "the method is gone", "bad"),
            ("no_file_data", "it still parsed the call", "plain"),
            ("missing_scope", "never reached the method", "plain"),
            ("invalid_auth", "the token, not the method", "plain"),
            ("Uploads after the cutover", "some caller migrated", "good"),
        ],
    ),
}

V["slack/users-read-email-missing"] = {
    "flow_intro": (
        "The census counts humans and the header names the grant, and the two "
        "are read from the same response. A scope list from the app config page "
        "describes the app you meant to deploy, not the token that is running."
    ),
    "diagram_problem": D.chain(
        "semail-p",
        "A user sync that writes null emails and exits zero every night",
        "There is no error at any point in this chain. The field was withheld "
        "by leaving the key out, and a missing key is not an exception in any "
        "language the job is written in.",
        [
            ("users.list called", "users:read granted"),
            ("Profiles come back full", "ok is true"),
            ("Email key absent", "second scope withheld it"),
            ("Rows written as null", "insert succeeds"),
            ("Join matches nothing", "job still green"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "semail-f",
        "Sorting a census of emails by what would actually change it",
        "A handful of humans without an address is ordinary workspace life. "
        "Reporting it as the scope gap sends a team through a reinstall that "
        "changes nothing at all.",
        ("Humans counted, header read", "from one response"),
        [
            ("None, scope absent", "add it and reinstall", "bad"),
            ("None, scope granted", "admin policy, not scopes", "bad"),
            ("Most but not all", "guests and hidden addresses", "plain"),
            ("Every human has one", "the grant is working", "good"),
        ],
    ),
}

V["slack/event-subscriptions-auto-disabled"] = {
    "flow_intro": (
        "The script measures the distance between the last mention and the last "
        "reply, and then mostly declines to conclude. Delivery disabled, a dead "
        "handler and events never subscribed to are one shape from inside the "
        "workspace, and the script says which shape rather than which cause."
    ),
    "diagram_problem": D.chain(
        "sevdis-p",
        "An outage that ends and an app that never comes back",
        "Recovery restores the service and not the subscription. The switch "
        "Slack threw during the outage stays thrown until a human finds the "
        "page it lives on.",
        [
            ("Endpoint fails for an hour", "5xx, or over 3 seconds"),
            ("Slack passes 95 percent", "delivery disabled"),
            ("Email to the app owner", "nobody reads that inbox"),
            ("Service recovers", "delivery does not"),
            ("Mentions go unanswered", "app looks healthy"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sevdis-f",
        "Sorting channels by the shape of the silence, not by its cause",
        "The Web API never reports whether Slack is delivering, so the honest "
        "output names what was observed and points at the one page where the "
        "real state can be read.",
        ("Mentions and replies", "from one page of history"),
        [
            ("Replied after the last", "delivery is arriving", "good"),
            ("Answered, then stopped", "check the config page", "bad"),
            ("Addressed, never answered", "likelier never subscribed", "bad"),
            ("One mention pending", "not evidence yet", "plain"),
            ("Nobody addressed it", "no evidence either way", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
