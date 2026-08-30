#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch T.

Two notes about what Slack does to your content over time, and two about the
delivery mode the app was configured with. Four chains that each break in a
different place, on purpose, because a batch drawn the same way four times
teaches a reader nothing on the second page.

The first breaks in the middle, at the byte transfer, which is the one step of
an upload that is not a Slack API call and therefore behaves like nothing else
in the sequence. The second never goes red at all: every call in it returns ok
with an empty array, and the only motion is the loop underneath, which is the
retention horizon advancing a day every day whether anybody is watching or not.
The third breaks late, because the configuration is fine and stays fine right
up to the moment two processes both receive the same event. The fourth breaks
at the very first arrow, on the afternoon somebody switched Socket Mode on, and
every box after it is a year of things going well.

The branches sort four different kinds of thing: bytes into bands, ages into a
policy, delivery paths into what is configured, and an app into whether it can
ever be listed.

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

V["slack/file-size-limit"] = {
    "flow_intro": (
        "The red box is in the middle of this chain rather than at either end, "
        "and that placement is the note. The first step is a Slack API call "
        "and the last step is a Slack API call, and the one between them is a "
        "plain HTTP request to a storage host that has never heard of your "
        "Slack client, your timeouts or your retry policy. The fix branch "
        "sorts bytes into bands rather than errors into causes, because "
        "nothing here has failed yet: the top rows are a date in the future, "
        "and the fourth row is a stalled sequence that belongs to another "
        "note and is deliberately kept out of the count."
    ),
    "diagram_problem": D.chain(
        "skfsize-p",
        "An upload that grew past the step that is not a Slack API call",
        "The ceiling in the documentation is 1 GB. The one that stops you is "
        "your own HTTP client's default timeout, on a request to a host "
        "nobody on the team has heard of.",
        [
            ("The export grows", "4 MB, then 60"),
            ("Slack hands back a URL", "ok, and a file id"),
            ("Bytes to another host", "your defaults, not Slack's"),
            ("The client gives up", "no ok false anywhere"),
            ("Sometimes it works", "on a quiet morning"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skfsize-f",
        "Every file the app owns, sorted into the bands that decide whether it survives",
        "A size finding is predictive, so the report leads with the biggest "
        "file as a fraction of the cap. The bottom row is the arithmetic that "
        "turns a mysterious timeout into a number you chose.",
        ("files.list, the app's own output", "size in bytes, per file"),
        [
            ("Past the 1 GB ceiling", "refused outright, and rare", "bad"),
            ("Three quarters of the way", "next quarter's outage", "bad"),
            ("Inside the transfer band", "the timeout, not the cap", "bad"),
            ("Zero bytes", "a stalled sequence, not a size", "plain"),
            ("Needs longer than you allow", "and no retry ever fixes that", "good"),
        ],
    ),
}

V["slack/file-retention-deletes-history"] = {
    "flow_intro": (
        "Nothing in this chain is red, because nothing in it fails. Every "
        "call returns ok, every window comes back empty and well formed, and "
        "the deletion happened months before anybody went looking. The loop "
        "underneath is the only thing moving: retention is a clock rather "
        "than an event, and the horizon advances one day every day whether or "
        "not the app is running. The fix branch sorts ages rather than "
        "objects, and the two plain rows are the ones that stop the check "
        "from inventing a policy out of a channel nobody posted in."
    ),
    "diagram_problem": D.chain(
        "skfretn-p",
        "An archive built on Slack quietly inheriting somebody else's deletion policy",
        "An admin set a policy, possibly years ago, possibly before the app "
        "existed. Nothing announces it and nothing errors: content older than "
        "a line simply is not there any more.",
        [
            ("An admin sets a policy", "90 days, once, in 2023"),
            ("Slack deletes daily", "messages and files together"),
            ("The app reads a year", "ok, and an empty array"),
            ("The export has a hole", "tidy, and dated"),
            ("Somebody rewrites the backfill", "and gets the same hole"),
        ],
        loop=(4, 1, "the horizon advances one day, every day"),
    ),
    "diagram_fix": D.branch(
        "skfretn-f",
        "Windows probed at increasing ages, and the boundary only several channels can prove",
        "One channel cannot tell deletion from silence, so the answer is "
        "agreement rather than a reading. The last row is the sentence that "
        "belongs in the ticket, because it is a number about your app rather "
        "than about the workspace.",
        ("A ladder of windows, per channel", "30, 60, 90, 180, 365, 730 days"),
        [
            ("Several channels, one age", "a workspace setting", "bad"),
            ("Different ages each", "quiet channels, not a policy", "plain"),
            ("Empty even last month", "this channel decides nothing", "plain"),
            ("History past the empty window", "monotonic, so not an edge", "plain"),
            ("Kept days against read days", "the shortfall, in days", "good"),
        ],
    ),
}

V["slack/socket-mode-and-request-url-both-on"] = {
    "flow_intro": (
        "This chain stays black until the fourth arrow, which is the point: "
        "every step in it is a reasonable decision made by a competent "
        "person, and the configuration is not wrong at any moment along the "
        "way. It only becomes wrong when two processes are running at once, "
        "which is a Tuesday rather than a deploy. The fix branch sorts "
        "delivery paths rather than symptoms, and the two middle rows exist "
        "so this note can hand a reader to the retry note instead of "
        "half-solving somebody else's problem."
    ),
    "diagram_problem": D.chain(
        "skdualp-p",
        "One app configuration serving a laptop and a production deployment at once",
        "Slack has no environments. One app is one switch, one Request URL "
        "and one set of subscriptions, and every process holding the "
        "credentials is a peer rather than a subscriber.",
        [
            ("One app, every environment", "there is no other kind"),
            ("Socket Mode on, for dev", "delivery moves to the socket"),
            ("The URL stays stored", "hidden, and not cleared"),
            ("Whoever connects wins", "a laptop, or nobody"),
            ("Duplicates, or silence", "and nothing errored"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "skdualp-f",
        "The manifest and the message spacing, read together",
        "The manifest half is two fields and the evidence half is one "
        "subtraction. A gap of a second cannot be a retry and a gap of a "
        "minute cannot be two handlers, so the timestamps decide which note "
        "you are actually in.",
        ("The manifest, and one history read", "the switch, the URLs, the gaps"),
        [
            ("Socket on, URLs still stored", "dormant, and one switch away", "bad"),
            ("One app id in every environment", "the root cause, in one field", "bad"),
            ("Copies a second apart", "two handlers, not a retry", "bad"),
            ("Copies a minute apart", "the retry ladder, another note", "plain"),
            ("One path, and two app ids", "which is what the split buys", "good"),
        ],
    ),
}

V["slack/socket-mode-blocks-distribution"] = {
    "flow_intro": (
        "The break is at the very first arrow here, on the afternoon somebody "
        "chose Socket Mode, and every box after it is a year of the app "
        "working perfectly. That is what makes this one expensive: there is "
        "no failure to notice, no error to log and no warning to heed, only a "
        "road that ends when somebody finally reads the distribution "
        "requirements. The fix branch sorts an app into what it can become "
        "rather than what is wrong with it, and the fourth row is the "
        "supported use of the feature, printed as a verdict so that nobody "
        "reports it as a fault."
    ),
    "diagram_problem": D.chain(
        "skmktbl-p",
        "A year of good decisions ending at a requirement nobody read on day one",
        "Nothing here goes wrong. The app works, the customers arrive, and "
        "the delivery architecture chosen on the first afternoon turns out to "
        "be the one thing that cannot come with it.",
        [
            ("Socket Mode, day one", "the fastest way to working"),
            ("A year of it working", "no error, ever"),
            ("A customer asks to install", "then two more do"),
            ("The submission is read", "listing needs a public URL"),
            ("A platform project", "in the middle of a sale"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "skmktbl-f",
        "The transport crossed against where the app has already been installed",
        "Intent and reality disagree more often than anybody expects, so the "
        "plan and the installation records are read separately. The last row "
        "is the second half of the same decision, and it is cheaper to find "
        "it in the same run.",
        ("The manifest, and your installs", "the switch, redirects, team ids"),
        [
            ("Socket, and unrelated workspaces", "distributed already", "bad"),
            ("Socket, and a redirect setup", "a migration, not a submission", "bad"),
            ("Socket across one enterprise", "org deployment, a ceiling", "plain"),
            ("Socket, one workspace, no plans", "the feature, used correctly", "plain"),
            ("History reads, on either", "the clamp shares the repair", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
