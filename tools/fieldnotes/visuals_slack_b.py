#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch B.

Three of these four notes read one resource, conversations.history, and the
fourth reads files.list. That is the shape worth drawing: the evidence is already
sitting in the workspace, in a list nobody pages, and the whole job is grouping it
and then refusing to over-report. So every problem chain ends at a record that
exists, and every fix branch spends most of its rows on the states that look like
the finding and are not. Drawn in Slack aubergine.

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

V["slack/duplicate-messages-no-dedupe"] = {
    "flow_intro": (
        "The script groups identical app-authored messages first and only then "
        "looks at the clock, because the count tells you there is a duplicate and "
        "the spacing between the copies tells you which of four different bugs "
        "produced it."
    ),
    "diagram_problem": D.chain(
        "sdup-p",
        "One event retried by Slack, handled twice, posted twice",
        "Nothing here is an error. Slack retried because it was not acknowledged "
        "in time, and chat.postMessage has no idempotency key to collapse the "
        "second send.",
        [
            ("Event delivered", "your handler starts"),
            ("Handler runs long", "past three seconds"),
            ("Slack retries", "same event_id, 60s later"),
            ("Handler runs again", "no key to check"),
            ("Two identical posts", "sixty seconds apart"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sdup-f",
        "Sorting duplicate groups by the gap between the copies",
        "The gap is the diagnosis. A double subscription and a retry loop need "
        "opposite repairs, and a nightly digest is not a bug at all.",
        ("Identical messages grouped", "then sorted by ts delta"),
        [
            ("One copy only", "nothing to explain", "good"),
            ("Under a second apart", "two delivery paths", "bad"),
            ("Sixty or 300s apart", "retries, no event_id check", "bad"),
            ("Hours apart", "overlapping cron runs", "plain"),
        ],
    ),
}

V["slack/bot-message-echo-loop"] = {
    "flow_intro": (
        "The script walks each channel in time order and measures runs of "
        "consecutive self-authored messages, because a run broken by a human is a "
        "conversation and a run that is never broken is a loop."
    ),
    "diagram_problem": D.chain(
        "secho-p",
        "A message handler that replies to its own reply",
        "message.channels delivers every message in the channel, including the "
        "ones your app just posted. A handler matching on text alone cannot tell "
        "the difference.",
        [
            ("Human posts", "one message"),
            ("Bot replies", "chat.postMessage"),
            ("Slack delivers reply", "to your own handler"),
            ("Handler replies again", "no bot_id guard"),
            ("Channel floods", "until someone removes the bot"),
        ],
        fail_at=2,
        loop=(4, 2, "every reply is a new event"),
    ),
    "diagram_fix": D.branch(
        "secho-f",
        "Sorting runs of self-authored messages by length and spacing",
        "A digest job posting twelve messages in a row is not a loop. Reporting "
        "it as one is how this check gets switched off.",
        ("Consecutive self-authored runs", "measured per channel"),
        [
            ("Runs of one", "replying to humans", "good"),
            ("Short runs, slow", "a batch or a thread", "good"),
            ("Long runs, seconds apart", "a poster, not a loop", "plain"),
            ("Long runs, sub-second", "the handler hears itself", "bad"),
        ],
    ),
}

V["slack/public-file-links-exposed"] = {
    "flow_intro": (
        "The script reads two flags per file and keeps them apart, because "
        "is_public means members of a public channel can see it and "
        "public_url_shared means anybody on the internet can."
    ),
    "diagram_problem": D.chain(
        "sfil-p",
        "A public link minted for Block Kit and never revoked",
        "Block Kit image_url has to be fetchable without a Slack login, so the "
        "workaround is to make the file public. The link outlives the message by "
        "years.",
        [
            ("App uploads a file", "url_private, authenticated"),
            ("Block Kit needs a URL", "image_url must be open"),
            ("Public URL minted", "permalink_public"),
            ("Message deleted later", "link is unaffected"),
            ("Readable by anyone", "no login, no expiry"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sfil-f",
        "Sorting files by which of the two visibility flags is set",
        "Only one of these rows is a data exposure. Treating a file in a public "
        "channel as one buries the finding that matters.",
        ("Every file and its flags", "public_url_shared and is_public"),
        [
            ("Neither flag set", "Slack login required", "good"),
            ("Only is_public", "workspace members, still gated", "good"),
            ("public_url_shared set", "open to the internet", "bad"),
            ("Public and in no channel", "nobody in Slack can see it", "bad"),
        ],
    ),
}

V["slack/non-marketplace-history-clamp"] = {
    "flow_intro": (
        "The script asks for 200 messages and counts what comes back, then checks "
        "the cursor, because a page of 15 with no cursor is a small channel and a "
        "page of 15 with a cursor is the clamp."
    ),
    "diagram_problem": D.chain(
        "sclm-p",
        "A backfill that slows by two orders of magnitude with no code change",
        "The request is still valid and the response is still ok true. Only the "
        "size of the page and the interval between calls changed.",
        [
            ("App asks for 1000", "as it always did"),
            ("App is not on Marketplace", "unlisted distribution"),
            ("Slack caps the page", "15 objects"),
            ("Second call in a minute", "error ratelimited"),
            ("Backfill takes weeks", "no error to alert on"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sclm-f",
        "Sorting a history probe by page size and whether a cursor came back",
        "A quiet channel returns a short page too. The cursor is what separates "
        "a small channel from a clamped app.",
        ("One history call, limit 200", "count returned, read cursor"),
        [
            ("More than 15 back", "Tier 3 limits intact", "good"),
            ("Short page, no cursor", "the channel is that small", "good"),
            ("Exactly 15, no cursor", "cannot tell, probe again", "plain"),
            ("Exactly 15 plus cursor", "the clamp is active", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
