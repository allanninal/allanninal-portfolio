#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch B.

All four notes read the same resource, so all four problem chains have the same
spine: a send that is accepted, then something downstream that produces no error
anyone is watching for. The fix is a branch every time, because each script sorts
what it finds rather than guessing at it. Drawn in Twilio red.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#F22F46"
D.set_theme(BRAND)

V = {}

V["twilio/carrier-filtered-messages-30007"] = {
    "flow_intro": (
        "The script groups by sender before it judges anything, because filtering "
        "attaches to a sender's reputation rather than to a message: one poisoned "
        "long code averaged with seven healthy ones disappears completely."
    ),
    "diagram_problem": D.chain(
        "tflt-p",
        "A message accepted, billed, and then filtered by the carrier",
        "Nothing here returns an error to your code. The only trace is an integer "
        "on a resource that has no filter for it.",
        [
            ("Send accepted", "201 and a message sid"),
            ("Segments billed", "priced on the way out"),
            ("Carrier filters", "content or reputation"),
            ("error_code 30007", "status undelivered"),
            ("Nobody reads it", "no alert exists"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tflt-f",
        "Sorting senders by how much of their traffic is being filtered",
        "Two filtered messages is not a ticket and half a sender's traffic is not "
        "a wording problem, so they are deliberately different states.",
        ("Messages paged by date", "grouped by from or service sid"),
        [
            ("No 30007 at all", "clean, nothing to do", "good"),
            ("One or two filtered", "too few to escalate", "plain"),
            ("A steady few percent", "content or use case", "bad"),
            ("Half the traffic gone", "the sender is burned", "bad"),
        ],
    ),
}

V["twilio/opted-out-recipients-21610"] = {
    "flow_intro": (
        "The script joins two directions of the same conversation: the inbound STOP "
        "is keyed on the sender's number and the rejected sends are keyed on the "
        "recipient's, and the finding only exists when both land on one person."
    ),
    "diagram_problem": D.chain(
        "topt-p",
        "An opt-out honoured by Twilio and never recorded by the application",
        "Every step behaves correctly. The opt-out is enforced, nobody is "
        "contacted, nothing is billed, and the record of trying keeps growing.",
        [
            ("Recipient texts STOP", "inbound message"),
            ("Twilio blocks sender", "opt-out stored"),
            ("Your app never hears", "webhook missed it"),
            ("Next send rejected", "error 21610"),
            ("Queue retries it", "again tomorrow"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "topt-f",
        "Sorting recipients by whether the opt-out ever reached your database",
        "There is no read API for the opt-out list, so these rejections are the "
        "only material a read-only credential has to rebuild it from.",
        ("Rejections and keywords", "joined on the consumer number"),
        [
            ("STOP, then silence", "suppressed correctly", "good"),
            ("STOP, then more sends", "your database missed it", "bad"),
            ("Rejections, no STOP", "opted out before the window", "bad"),
            ("Dozens of rejections", "a retry loop, not a contact", "bad"),
        ],
    ),
}

V["twilio/landline-destination-30006"] = {
    "flow_intro": (
        "The script asks Lookup for the line type only on numbers that already "
        "failed, because Line Type Intelligence is billed per number and the "
        "failure history is free."
    ),
    "diagram_problem": D.chain(
        "tlnd-p",
        "A desk phone retried every night because the failure looks temporary",
        "Nothing in the message resource marks 30006 as permanent, so the retry "
        "queue treats a desk phone like a flat battery.",
        [
            ("Customer gives office line", "signup succeeds"),
            ("SMS sent and billed", "handed to a carrier"),
            ("Landline cannot receive", "error 30006"),
            ("Queue retries", "failure looks transient"),
            ("Billed again nightly", "forever"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tlnd-f",
        "Sorting failed destinations by what the carrier says the line actually is",
        "A mobile handset returning 30006 is the opposite finding: the line is "
        "fine and the sending route cannot reach it.",
        ("30006 and 21614 rows", "one Lookup per destination"),
        [
            ("Lookup says mobile", "your sender cannot reach it", "bad"),
            ("Lookup says landline", "permanent, suppress it", "bad"),
            ("Repeated, no lookup", "treat as permanent", "plain"),
            ("One failure only", "confirm before dropping", "plain"),
        ],
    ),
}

V["twilio/messages-stuck-queued-or-accepted"] = {
    "flow_intro": (
        "The script ages every non-final message against a clock you pass in, "
        "because three of the four non-final states are healthy and only the "
        "timestamp separates them from the one that is not."
    ),
    "diagram_problem": D.chain(
        "tstk-p",
        "A passcode queued behind a bulk job on a one message per second sender",
        "There is no event for not moving, so the first alert anyone gets is the "
        "failure hours later, long after the code expired.",
        [
            ("Bulk job queued", "thousands of segments"),
            ("Passcode queued next", "same long code"),
            ("Sender meters it out", "about one per second"),
            ("Hours in queued", "no error_code"),
            ("Fails with 30001", "or expires 30036"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tstk-f",
        "Sorting non-final messages by age, status and the clock",
        "Counting scheduled and sent messages as stuck is how a queue report "
        "loses the reader's trust on its first run.",
        ("Messages aged on date_created", "against a clock passed in"),
        [
            ("Scheduled for later", "waiting on purpose", "good"),
            ("Sent, no receipt", "terminal and successful", "good"),
            ("Queued under an hour", "still in flight", "plain"),
            ("Queued for hours", "the queue is not draining", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
