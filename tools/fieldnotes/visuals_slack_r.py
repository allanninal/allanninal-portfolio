#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch R.

Four notes about work that is either already accepted and cannot be recalled,
or will never start and says nothing about it. Drawn as four different shapes,
because two of them are absences and an absence drawn the same way twice reads
as the same absence.

The first carries the loop, since the queue is refilled by every deploy that
does not drain it, and the loop is literally the leak. The second goes red at
the second box and everything downstream is grey, because nothing failed: an
event was never created, so there is nothing after that point to colour. The
third goes red at the fourth box, where a call that was correct in every
respect arrives a few hundred milliseconds after its permission ran out. And
the fourth goes red in the middle, which is the note: three operations, and the
one that breaks is the one nobody instrumented. Drawn in Slack aubergine.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
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

V["slack/scheduled-messages-orphaned"] = {
    "flow_intro": (
        "The only chain in this batch with a loop under it, and the loop is "
        "the whole failure rather than an illustration of it. Each deploy "
        "hands Slack a fresh set of sends and takes nothing back, so the queue "
        "is topped up faster than it drains and the tail grows quietly for "
        "months. The red box is the fourth one, where nothing happens, because "
        "nothing happening is the bug: no call was made, so there is no error "
        "to find. The fix branch sorts the queue by who still stands behind "
        "each entry, and the top two rows are the two that most often get "
        "counted together and should not be."
    ),
    "diagram_problem": D.chain(
        "skorph-p",
        "A reminder scheduled once, and delivered long after its reason closed",
        "Slack took the message and will deliver it up to 120 days later "
        "whatever happens to your application in between. Deleting the row is "
        "not an API call, and the queue never hears about it.",
        [
            ("Scheduler queues it", "Slack keeps the id"),
            ("Ticket is closed", "the row is deleted"),
            ("Deploy replaces it", "new logic ships"),
            ("Nothing cancels", "no call was ever made"),
            ("It fires in November", "for a ticket closed in July"),
        ],
        fail_at=2,
        loop=(4, 0, "every deploy adds another tail and takes none away"),
    ),
    "diagram_fix": D.branch(
        "skorph-f",
        "The pending queue read back and joined against your own scheduling records",
        "Reading the queue is a read and cancelling from it is not, so the "
        "bottom of this is a list of lines rather than an action. The join is "
        "the point: a count of pending sends decides nothing, and a count of "
        "pending sends nobody can account for decides everything.",
        ("The queue, and your records", "id, channel, post_at"),
        [
            ("No record of this id", "nothing you own can cancel it", "bad"),
            ("Your row says completed", "one missing cancel, in one path", "bad"),
            ("Aimed at an archived channel", "wanted, and already doomed", "bad"),
            ("More arriving than leaving", "the leak, stated as a rate", "plain"),
            ("Tracked, live, deliverable", "a backlog rather than a leak", "good"),
        ],
    ),
}

V["slack/unfurl-domain-not-configured"] = {
    "flow_intro": (
        "The red box here is the second one and everything after it is grey, "
        "which is unusual and is the note. Nothing failed. No request was "
        "refused, no handler timed out, no scope was checked and found "
        "wanting. Slack looked at a list, did not find your app on it, and "
        "created no event, so the three boxes downstream are not failures but "
        "consequences of an absence. The fix branch is ordered rather than "
        "sorted: it names the first missing switch, because the ones after it "
        "cannot be tested until that one is flipped."
    ),
    "diagram_problem": D.chain(
        "skunfd-p",
        "A link posted, a list checked, and no event created for anybody to handle",
        "The handler is correct and is never called. There is no error to "
        "search for, because an absence has no error code and a message that "
        "was never sent leaves nothing behind.",
        [
            ("Somebody pastes a link", "in a channel the bot is in"),
            ("Your app is not listed", "the domain was never added"),
            ("No event is created", "so none is delivered"),
            ("Handler never runs", "and logs nothing at all"),
            ("Bare blue URL", "reported as a bug in the code"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "skunfd-f",
        "Four preconditions checked in the order they have to be fixed in",
        "The order is the output. A missing domain makes the scopes "
        "unknowable and a missing links:read makes links:write academic, so a "
        "list of all four at once is a list nobody can start on. The last two "
        "rows are the same feature failing at opposite ends.",
        ("The manifest and the header", "domains, events, scopes"),
        [
            ("No domain registered", "nothing else can be tested yet", "bad"),
            ("link_shared not subscribed", "registering is not subscribing", "bad"),
            ("links:read not granted", "the silent one, no error anywhere", "bad"),
            ("links:write not granted", "the loud one, after the work is done", "plain"),
            ("All four, and links unadorned", "reinstall; the grant predates them",
             "good"),
        ],
    ),
}

V["slack/trigger-id-expired"] = {
    "flow_intro": (
        "The red box is the fourth one, and every box before it is correct. "
        "The payload was valid, the handler woke up, the database answered, "
        "the modal was built properly and the call was well formed. It simply "
        "arrived after a permission that started counting down when the user "
        "clicked, not when your process did. The fix branch sorts by cause "
        "rather than by error string, and only the top row is one that going "
        "faster will fix."
    ),
    "diagram_problem": D.chain(
        "sktrig-p",
        "A click, a cold start, a database read, and a view opened too late",
        "Three seconds is the ceiling and it is measured from the click. What "
        "the handler actually gets is whatever the round trip and the cold "
        "start left behind, which on a Monday morning is a few hundred "
        "milliseconds.",
        [
            ("User clicks", "the clock starts here"),
            ("Round trip, cold start", "most of it already spent"),
            ("Options fetched first", "so the modal looks complete"),
            ("views.open", "expired_trigger_id"),
            ("Try again?", "and the work never happens"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sktrig-f",
        "Every interaction judged on two timestamps your own handler recorded",
        "Slack exposes no trigger state at all, so the instrument is your own "
        "ledger: when the payload arrived and when the view was opened. The "
        "middle rows are the ones speed cannot help, and the reflex of adding "
        "a retry makes both of them worse.",
        ("Arrived at, opened at", "and the error, if any"),
        [
            ("Over a second before open", "fetching first, opening second", "bad"),
            ("The same trigger used twice", "a trigger opens exactly one view", "bad"),
            ("Carried from an older payload", "the submission handed you a new one",
             "bad"),
            ("Three dots and it still failed", "a token problem wearing the wrong name",
             "plain"),
            ("Open first, update after", "views.update has no deadline", "good"),
        ],
    ),
}

V["slack/incomplete-external-upload"] = {
    "flow_intro": (
        "The red box is the third one, in the middle, and that position is the "
        "argument. An upload is three operations across two systems with no "
        "transaction around them, and the id you write down is handed out by "
        "the first one before a single byte exists. Break the sequence "
        "anywhere and you keep a perfectly valid looking handle to nothing. "
        "The fix branch is the only one in this batch whose rows end in a "
        "retry direction rather than a repair, because going the wrong way "
        "here does not fail, it duplicates."
    ),
    "diagram_problem": D.chain(
        "skxupl-p",
        "An id issued before any bytes, and a sequence that stops before it finishes",
        "The middle step does not go to the Slack API at all, so it is absent "
        "from every trace, metric and retry policy wrapped around your Slack "
        "client. The last step is the one that needs files:write.",
        [
            ("An id, and a URL", "before any bytes exist"),
            ("Bytes go to that URL", "not a Slack call at all"),
            ("Completion refused", "files:write was never granted"),
            ("Your ledger has the id", "and Slack has no file"),
            ("A link to nothing", "and no exception anywhere"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skxupl-f",
        "Every recorded file id asked about, and the one step to repeat named",
        "file_not_found against an id from your own logs is one of the few "
        "unambiguous answers in this whole API. What it does not say is which "
        "step broke, and that is what decides whether the retry costs one call "
        "or leaves a second orphan behind the first.",
        ("Your ids, and files.info", "step reached, then the answer"),
        [
            ("No file under this id", "repeat the completion, only that", "bad"),
            ("Registered at zero bytes", "the middle step, start again", "bad"),
            ("Declared more than was sent", "a character count, not a byte count",
             "bad"),
            ("Exists and shared nowhere", "finished; the channel is another note",
             "plain"),
            ("Real bytes, real shares", "and files:write held from the start", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
