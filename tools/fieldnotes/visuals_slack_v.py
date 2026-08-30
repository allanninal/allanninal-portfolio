#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch V.

Four notes about the app configuration screen, and the risk in a batch like
this is drawing the same picture four times, because every one of them is
ultimately a field somebody did not fill in. So the red arrow sits somewhere
different in each chain and each branch sorts a different kind of thing.

The first goes red in the middle, at the moment Slack looks for a destination
and finds neither one. Everything before that arrow is correct, including the
decision to turn the switch off, which is why nobody sees it coming.

The second goes red late, at the fourth arrow, because more of this failure is
healthy than in any other note here: the message posts, the client renders it,
the person clicks and a payload is genuinely produced. Only the last step, the
lookup, has nothing to find.

The third carries the loop, because drift is the only failure of the four that
widens on its own: every emergency fix made through the web UI moves the two
documents further apart while nobody deploys anything.

The fourth goes red at the very first arrow, which is the shape of a gate: the
whole picture after it is a consequence of one thing never having been done,
and none of the steps that follow is a fault in the app at all.

The branches sort four different things on purpose: a count of transports, two
surfaces measured against each other, three lists of scopes, and a checklist of
prerequisites.

Drawn in Slack aubergine. No em dashes inside SVG text: one mis-sniffed
encoding turns a single character into three mojibake ones inside an image,
where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further: visuals.py imports several of
# these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#4A154B"
D.set_theme(BRAND)

V = {}

V["slack/socket-mode-off-but-no-request-url"] = {
    "flow_intro": (
        "The red arrow is in the middle, and everything to the left of it is "
        "correct. Turning Socket Mode off was a reasonable thing to do, there "
        "was no Request URL underneath it because there had never needed to be "
        "one, and Slack is behaving exactly as documented when it drops what "
        "it cannot deliver. The failure only exists at the join. The fix "
        "branch sorts a count rather than an error, because the four possible "
        "counts are four different notes, and the two rows in the middle are "
        "the ones that keep an investigation honest: commands that still "
        "answer are not evidence that delivery works, and a series that simply "
        "ends is not the same statistic as a fraction going missing."
    ),
    "diagram_problem": D.chain(
        "sknotr-p",
        "An app with neither Socket Mode nor a Request URL and no error anywhere",
        "There is no fallback between the two transports. With neither "
        "configured Slack has no destination for an event, so it drops it, and "
        "nothing on either side reports a failure.",
        [
            ("A switch moves", "Socket Mode goes off"),
            ("No URL underneath", "none was ever set"),
            ("An event happens", "somebody types a mention"),
            ("Nowhere to deliver", "so Slack drops it"),
            ("Nine days of quiet", "and no error anywhere"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sknotr-f",
        "The transports counted from the manifest, then the date the app stopped posting",
        "Four counts, four different notes. One is healthy, one is this note, "
        "and the other two belong somewhere else, so the check is a count "
        "rather than a boolean on either field.",
        ("Count the transports", "socket, URL, both, neither"),
        [
            ("Neither is configured", "declared events with no route at all", "bad"),
            ("The series just ends", "a date to take to the audit log", "bad"),
            ("Both at once", "duplicates, and a different note", "plain"),
            ("Commands still answer", "each one keeps a URL of its own", "plain"),
            ("Exactly one transport", "and the app is talking again", "good"),
        ],
    ),
}

V["slack/interactivity-not-enabled"] = {
    "flow_intro": (
        "The red arrow is the last one, later than anywhere else in this "
        "batch, and that lateness is the note. Four of the five steps work "
        "perfectly: the message posts with nothing more than chat:write, the "
        "client renders the buttons without consulting any configuration, a "
        "person clicks, and Slack genuinely produces a payload. Only the "
        "lookup at the end has nothing to find. The fix branch is the only one "
        "here that sorts two things at once, because a single count of silence "
        "cannot tell a missing switch from a missing transport, and those live "
        "on different screens with different repairs."
    ),
    "diagram_problem": D.chain(
        "skclick-p",
        "A button that renders correctly on an app that cannot receive the click",
        "Posting an interactive message and receiving the interaction are two "
        "separate capabilities. The first needs a scope, the second needs a "
        "switch, and only the first one is visible.",
        [
            ("A message with buttons", "chat:write is all it takes"),
            ("The client draws them", "no configuration consulted"),
            ("A person clicks", "a payload is produced"),
            ("Slack looks up the URL", "on the other screen"),
            ("There is not one", "and your handler never ran"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "skclick-f",
        "Two surfaces of one app measured separately and reported as a pair",
        "The finding is an asymmetry rather than a silence. One surface "
        "answering while the other never does is what a missing route looks "
        "like; both silent is a transport and a different note.",
        ("Two surfaces, apart", "mentions, and then clicks"),
        [
            ("Mentions answered, clicks not", "the switch, and this note", "bad"),
            ("Enabled, field left empty", "produced and then dropped", "bad"),
            ("Menus that open empty", "the third URL, for options", "bad"),
            ("Neither surface answers", "a transport, not a switch", "plain"),
            ("Both answer", "one route serving both", "good"),
        ],
    ),
}

V["slack/manifest-drift"] = {
    "flow_intro": (
        "This is the only chain in the batch with a loop under it, and the "
        "loop is the whole failure: every emergency fix made through the web "
        "UI moves the two documents further apart, while nobody deploys "
        "anything and nothing complains. The red arrow is early, at the point "
        "where the two editors fail to reconcile, and the two steps after it "
        "are simply time passing. The fix branch sorts scopes rather than "
        "paths, because the third list is the one that explains the errors you "
        "are actually seeing, and the fourth row is the one that decides "
        "whether anybody keeps the check: a reordered array is not a finding."
    ),
    "diagram_problem": D.chain(
        "skmdrift-p",
        "A repository manifest and a live manifest diverging with nothing to reconcile them",
        "Two editors, no reconciliation. The divergence has no symptom at all "
        "until something applies one document over the other, which is usually "
        "an install nobody thought of as a deploy.",
        [
            ("One manifest in the repo", "reviewed, merged, forgotten"),
            ("One live on the app", "edited at 2am in March"),
            ("Neither reconciles", "and nothing complains"),
            ("A reinstall applies one", "whichever one is live"),
            ("Scopes disappear", "with no deploy at all"),
        ],
        fail_at=1,
        loop=(4, 1, "every fix made in the web UI widens the gap"),
    ),
    "diagram_fix": D.branch(
        "skmdrift-f",
        "The repository scopes, the live scopes and the granted scopes sorted three ways",
        "Sorted and flattened before anything is compared, so ordering is "
        "never a finding. Then three lists that move on three different "
        "clocks, and only one of them says what the code may do today.",
        ("Three lists, sorted first", "repo, live, and the grant"),
        [
            ("Removed from the app", "the token still carries it", "bad"),
            ("In the repo alone", "the change was never deployed", "bad"),
            ("Added in the web UI", "and the next CI run deletes it", "bad"),
            ("Only the order changed", "not a finding, by design", "plain"),
            ("All three agree", "and the build can pass", "good"),
        ],
    ),
}

V["slack/app-not-distributed"] = {
    "flow_intro": (
        "The red arrow is the first one, which is what a gate looks like: "
        "everything after it is a consequence of one thing never having been "
        "done, and not one of those steps is a fault in the app. The app "
        "works. It has worked for eight months. The fix branch is a checklist "
        "rather than a diagnosis, and its first row is the boundary this note "
        "shares with its neighbour: an app on Socket Mode is barred outright, "
        "so the script stops instead of printing a tidy list of items that "
        "cannot help. The row that matters most is the token, because it is "
        "the only one that is code, and the only one whose failure arrives "
        "after a customer has already installed."
    ),
    "diagram_problem": D.chain(
        "skndist-p",
        "A finished app that has never been installed outside the workspace it was built in",
        "Public distribution is a separate gate with its own checklist, not a "
        "consequence of the app being finished. Nothing blocks this app. "
        "Nobody ever walked it through.",
        [
            ("A customer says yes", "and asks for the link"),
            ("No redirect URL", "so the flow cannot start"),
            ("An error page", "not a consent screen"),
            ("The gate never opened", "nothing was ever blocking"),
            ("One token, one workspace", "and nowhere for a second"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "skndist-f",
        "The distribution prerequisites read from the manifest and from the deployment",
        "A checklist with real states rather than a score. Blocked, optional "
        "and failing are three different answers, and flattening them into a "
        "percentage would be alarming or reassuring for the wrong reason.",
        ("Read the gate, not the app", "manifest, then your code"),
        [
            ("Socket Mode is on", "barred outright, and another note", "plain"),
            ("No redirect URL at all", "one workspace, and only ever one", "bad"),
            ("One token in the environment", "the second install has nowhere", "bad"),
            ("Org-wide not enabled", "optional until a Grid customer", "plain"),
            ("Every prerequisite met", "and the link works for anyone", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
