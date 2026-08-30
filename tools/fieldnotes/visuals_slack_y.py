#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch Y.

Four notes whose failures happen in four different places, and the pictures are
pinned to that rather than to the errors, because two of these four produce no
error at all and a diagram of an error string would be a diagram of nothing.

The first fails on a call that succeeded. The red arrow sits between a response
that returned everything it was asked for and the client that read the payload
and dropped the envelope, which is where the retirement notice was. Everything
after it is the outage arriving on schedule, months later, with nothing to
bisect.

The second fails at the far end, past the last thing anybody instruments: the
call worked, the tests asserted on the response and passed, and the surface the
view was stored for is not rendered. Its red arrow is the fourth, the latest in
the batch, because every step before it is a genuine success. That is what
separates it from the Messages tab note next door, whose failure is a person
being refused on the way in and which at least has an error string to catch.

The third fails first. The red arrow is the very first one, because the
uninstall itself was correct and complete: Slack revoked the token and said so
twice, and the fault is the row in your own table that nothing removed. Every
box after that is the same day repeating.

The fourth fails in the middle, and only for some resources. Six weeks of
perfect operation, then a boundary that was always there.

The branches sort four different populations: methods, members, rows of your
own database, and workspaces. Drawn in Slack aubergine. No em dashes inside SVG
text: one mis-sniffed encoding turns a single character into three mojibake
ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the
# module. Every diagram here is constructed at import time, so the theme has to
# be active across exactly this file and no further.
BRAND = "#4A154B"
D.set_theme(BRAND)

V = {}

V["slack/deprecated-method-in-use"] = {
    "flow_intro": (
        "The red arrow is between two boxes that both look like successes, "
        "which is the whole character of this one. The call worked. The data "
        "came back. Slack attached a date to the response and the client did "
        "what every client does with a successful response, which is read the "
        "payload and throw the envelope away. Everything to the right of that "
        "arrow is the outage arriving on time, months later, with no deploy "
        "to bisect and no change to point at. The fix branch sorts methods "
        "rather than errors, and the row that matters most is the third: a "
        "deprecated write is named and never issued, because there is no way "
        "to ask a write method whether it still works except by doing it."
    ),
    "diagram_problem": D.chain(
        "skdepm-p",
        "A retirement notice delivered on a successful response and never read",
        "The only failure here happens on a call that succeeded. The notice "
        "arrives in a field nobody logs, because nothing needs investigating "
        "when the response says ok true.",
        [
            ("The call succeeds", "ok true, data returned"),
            ("A warning rides along", "a date, in a field"),
            ("The client reads the payload", "and drops the envelope"),
            ("The retirement date passes", "nothing was changed"),
            ("method_deprecated", "and the job returns nothing"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skdepm-f",
        "Legacy methods sorted by how they answer and by whether they may be asked",
        "Two questions per method, not one. Is it dying, and am I allowed to "
        "ask. The second question is what keeps a read-only sweep read only, "
        "and it is answered from the map rather than from the wire.",
        ("One method, two questions", "is it dying, may I ask"),
        [
            ("Dead already", "method_deprecated on a read", "bad"),
            ("Still works, and warns", "a date you can still act on", "bad"),
            ("A deprecated write", "named, mapped, never called", "plain"),
            ("Charset noise only", "not a deprecation at all", "plain"),
            ("Live, and quiet", "nothing scheduled for it", "good"),
        ],
    ),
}

V["slack/app-home-tab-disabled"] = {
    "flow_intro": (
        "The red arrow is the fourth, which is the latest in this batch and "
        "the reason this failure survives review. Every step before it is a "
        "real success: the view was built, the method returned ok true with a "
        "view id, and the test that asserts on that response passes. The "
        "failure is a page that is not rendered, and no call in the API will "
        "tell you what that page looks like. It is worth holding this against "
        "the Messages tab, which is the switch next door: that one refuses a "
        "person on the way in and hands your code an error string to catch, "
        "while this one accepts everything and shows nobody anything. The fix "
        "branch sorts members rather than settings, because the surface is "
        "stored per person and a publish rate cannot tell you how many people "
        "have one."
    ),
    "diagram_problem": D.chain(
        "skhtab-p",
        "A published view stored for a surface that was never switched on",
        "Four genuine successes and then a page that does not exist. There is "
        "no error on this wire at any point, and the integration test that "
        "reads the response passes every time.",
        [
            ("The Home tab is built", "four sections and a chart"),
            ("views.publish runs", "ok true, a real view id"),
            ("The tests assert on it", "and they pass"),
            ("A user opens the app", "expecting the dashboard"),
            ("There is no Home tab", "and no error, ever"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "skhtab-f",
        "Every member of the workspace held against the users a view was published for",
        "Forty thousand publishes for the same eleven people is a broken "
        "feature with excellent metrics. The measurement is a set difference "
        "over members, and the age of each view is asked per person rather "
        "than per app.",
        ("Every member, against the log", "who has a view, and how old"),
        [
            ("The switch is off", "so none of it is reachable", "bad"),
            ("Never published to", "most of the workspace", "bad"),
            ("Published once, at boot", "and nobody has since", "bad"),
            ("A view from last quarter", "stale action ids inside it", "plain"),
            ("Published on every open", "coverage looks after itself", "good"),
        ],
    ),
}

V["slack/app-uninstalled-orphan-install-record"] = {
    "flow_intro": (
        "The red arrow is the first one, and nothing to the left of it went "
        "wrong. The workspace removed the app, which customers are entitled "
        "to do, and Slack did everything correctly: it invalidated the token "
        "immediately and announced the end twice, with app_uninstalled and "
        "with tokens_revoked. The failure is the box the arrow points at, "
        "which is a row in your own database that nothing deleted, and every "
        "box after it is the same day repeating for eleven months. That is "
        "also why the fix branch sorts rows of a table rather than responses "
        "from an API. The row that keeps the whole thing honest is the third: "
        "a lapsed rotation looks like every other failure and is a live "
        "customer, so a cleanup that deletes on any error will eventually "
        "remove paying tenants in bulk."
    ),
    "diagram_problem": D.chain(
        "skuninst-p",
        "An uninstall that Slack completed correctly and the store never acted on",
        "Nothing is down and nothing is broken in Slack. The sediment is on "
        "your side, it grows by one row per departing customer, and it "
        "eventually drowns the failures that matter.",
        [
            ("The app is removed", "and Slack says so twice"),
            ("Nothing deletes the row", "that part was always yours"),
            ("Every sweep hits it again", "one call, one error line"),
            ("Eleven months of this", "the fraction only grows"),
            ("A real failure arrives", "as one line among 120"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "skuninst-f",
        "Every stored installation classified into the action a cleanup should take",
        "A state is not an instruction. Each row gets both, and the default "
        "action is to do nothing, because the expensive mistake here is not "
        "keeping a dead row for a week longer than necessary.",
        ("Every row, one auth.test", "a state, and its action"),
        [
            ("The grant has ended", "tombstone, with its residue", "bad"),
            ("The account is gone", "tombstone, for the same reason", "bad"),
            ("Rotation has lapsed", "refresh; deleting loses a tenant", "plain"),
            ("Rate limited mid sweep", "unknown, so try it again", "plain"),
            ("Answers ok true", "keep, and it is a customer", "good"),
        ],
    ),
}

V["slack/workspace-token-in-grid"] = {
    "flow_intro": (
        "The red arrow is in the middle, and the six weeks before it are not "
        "a grace period. The token was always bounded; nothing had crossed "
        "the boundary yet. That is what makes this hard to recognise from "
        "inside the workspace where it works, because a single-workspace "
        "install into a Grid organization is indistinguishable from an "
        "ordinary install in every field except one that nobody reads. The "
        "fix branch sorts workspaces, one read each, and its third row is the "
        "one to respect: a resource that answers not_found may be absent or "
        "may be invisible, Slack declines to say which, and a script that "
        "picks one is confidently wrong about half the time."
    ),
    "diagram_problem": D.chain(
        "skwstok-p",
        "A token bounded to one workspace of an organization that has forty",
        "The same token, the same code and the same line succeed for one "
        "channel and are refused for the next. The only difference is which "
        "workspace of the customer the channel lives in.",
        [
            ("Installed into one workspace", "by somebody in Marketing"),
            ("It works perfectly", "for six weeks"),
            ("The rollout begins", "channels in a sibling"),
            ("team_access_not_granted", "the token has a boundary"),
            ("Retried, and refused", "the boundary does not move"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skwstok-f",
        "Each workspace in the organization probed once, with the ambiguity preserved",
        "One refusal proves the token has an edge. A workspace by workspace "
        "map says where the edge is, which is the sentence an administrator "
        "can act on, and nothing in it is written to find out.",
        ("Each workspace, one read", "team.info, nothing written"),
        [
            ("team_access_not_granted", "outside the boundary, exactly", "bad"),
            ("Only the home workspace", "one of forty, and no more", "bad"),
            ("Answers not_found", "absent, or invisible, unknown", "plain"),
            ("Org wide, and no team_id", "it answers for the wrong one", "plain"),
            ("Every workspace answers", "the install spans the org", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
