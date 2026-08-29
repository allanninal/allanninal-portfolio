#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch Q.

Four messaging-delivery error codes, two of which look identical in a status
callback and are not: 30003 is a handset that may answer later, 30005 is a number
the carrier does not have. Same two shapes as the rest of the site: the problem
is a chain that breaks at one step, the fix is a branch, because every script in
this section classifies what it finds rather than guessing. Drawn in Twilio red.

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

V["twilio/unreachable-destination-handset-30003"] = {
    "flow_intro": (
        "The script groups the same failures twice, because one 30003 means "
        "nothing and the shape of a thousand means everything: by recipient it "
        "finds dead numbers, by sender it finds a carrier refusing you."
    ),
    "diagram_problem": D.chain(
        "t30003-p",
        "A retry loop that keeps a permanently unreachable number on the list",
        "Every step is the documented handling for a transient error. The loop "
        "only becomes a cost once the number stops being transient.",
        [
            ("Send accepted", "201 and a Message SID"),
            ("Carrier tries", "handset does not answer"),
            ("Undelivered 30003", "logged as transient"),
            ("Queued for retry", "same schedule as always"),
            ("Repeats forever", "billed each attempt"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "t30003-f",
        "Sorting 30003 by how wide the failures are spread across recipients",
        "Twelve failures over three numbers and thirty over thirty recipients "
        "are the same error code describing two unrelated problems.",
        ("Messages.json, filtered client side", "grouped by recipient and by sender"),
        [
            ("Thin and spread out", "ordinary handsets, retry once", "good"),
            ("Fails but also delivers", "flaky line, keep it", "plain"),
            ("Many hits, few numbers", "list decay, run Lookup", "bad"),
            ("A fifth of one sender", "carrier is blocking you", "bad"),
        ],
    ),
}

V["twilio/unknown-destination-handset-30005"] = {
    "flow_intro": (
        "The distinct day count is the whole rule, and it rests on parsing an "
        "RFC 2822 timestamp: a ten character slice of it reads the same for "
        "every message ever sent, so every dead number looks like a one off."
    ),
    "diagram_problem": D.chain(
        "t30005-p",
        "A permanent failure handled by code that was written for a transient one",
        "Nothing in the payload marks 30005 as permanent. It arrives through the "
        "same field, in the same shape, as the error that is worth retrying.",
        [
            ("Number disconnected", "carrier drops the record"),
            ("Campaign sends", "contact list unchanged"),
            ("Undelivered 30005", "same shape as 30003"),
            ("Handler retries", "switched on status"),
            ("Never succeeds", "billed every cycle"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "t30005-f",
        "Sorting recipients by whether the carrier answered the same way twice",
        "A delivery anywhere in the window outranks every failure: carriers "
        "reissue disconnected numbers to new subscribers.",
        ("30005 rows, grouped by recipient", "distinct days and delivered count"),
        [
            ("Delivered later too", "reassigned, keep it", "good"),
            ("One failure only", "confirm with Lookup first", "plain"),
            ("Repeats inside a day", "your queue is retrying", "bad"),
            ("Failed on separate days", "carrier has no such number", "bad"),
        ],
    ),
}

V["twilio/validity-period-expired-30036"] = {
    "flow_intro": (
        "The three codes are counted apart rather than summed, because 30045 and "
        "30012 are refused at request time and never queue at all. Changing the "
        "service setting cannot touch a send that was rejected outright."
    ),
    "diagram_problem": D.chain(
        "t30036-p",
        "A passcode that expired in the queue behind a campaign",
        "The deadline is measured from acceptance, not from transmission, so "
        "every second spent waiting for the sender counts against it.",
        [
            ("Five minute TTL", "sensible for a passcode"),
            ("Campaign queues first", "4000 segments ahead"),
            ("Long code drains", "about one per second"),
            ("Deadline passes", "still waiting its turn"),
            ("Dropped, 30036", "never transmitted"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "t30036-f",
        "Sorting senders by which of the three TTL codes they are producing",
        "A short deadline and a deep queue produce the same code. Only the "
        "service level cap tells you which of the two you are looking at.",
        ("Message counts plus validity_period", "per sender, from two APIs"),
        [
            ("No expiries", "queue drains in time", "good"),
            ("30045 or 30012", "rejected outright, fix the caller", "bad"),
            ("Service cap far too low", "raise it and widen the pool", "bad"),
            ("Cap is the default", "send call or a ten hour queue", "plain"),
        ],
    ),
}

V["twilio/mms-content-size-exceeds-carrier-30019"] = {
    "flow_intro": (
        "Two ceilings apply and only one of them rejects you up front. Twilio "
        "takes 5 MB; the destination carrier stops somewhere between about 300 kB "
        "and 3.5 MB, and you cannot ask which before sending."
    ),
    "diagram_problem": D.chain(
        "t30019-p",
        "An MMS accepted by Twilio and refused by half the carriers",
        "The test send went to a tier one handset, so the file passed every "
        "check anyone actually ran.",
        [
            ("Photo from a camera", "about 4 MB"),
            ("Twilio accepts", "under its own 5 MB"),
            ("Tester receives it", "tier one carrier"),
            ("Other networks refuse", "ceiling near 600 kB"),
            ("Undelivered 30019", "scattered complaints"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "t30019-f",
        "Sorting media by which carrier ceilings it fits under",
        "The middle band is the one that produces the confusing tickets: it "
        "delivers to some recipients and fails for the rest, every time.",
        ("Content-Length on the media", "read, body never downloaded"),
        [
            ("Under 300 kB", "fits every network", "good"),
            ("300 kB to 600 kB", "at the short code cap", "plain"),
            ("600 kB to 3.5 MB", "delivers to some, 30019 to others", "bad"),
            ("Over 3.5 MB", "no carrier is taking it", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
