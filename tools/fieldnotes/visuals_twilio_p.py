#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch P.

The same two shapes as the rest of the site: the problem is a chain that breaks
at one step, the fix is a branch, because every script in this section sorts
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

V["twilio/balance-below-safety-floor"] = {
    "flow_intro": (
        "The classifier divides one number by another, and the whole judgement "
        "lives in which day it divides by. The median day gives the runway; the "
        "busiest day already seen is the one that ends the account."
    ),
    "diagram_problem": D.chain(
        "tbal-p",
        "A healthy looking balance ending as a suspension during peak traffic",
        "Nothing degrades on the way down. The account runs at full speed until "
        "the balance is gone, and then refuses everything at once.",
        [
            ("Balance looks fine", "months at the old rate"),
            ("Traffic multiplies", "a launch, a campaign"),
            ("Balance crosses zero", "no throttle, no warning"),
            ("Account suspended", "20005 on every call"),
            ("Queue fails too", "30002, nothing replayed"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tbal-f",
        "Sorting a balance by the number of days of spend it actually covers",
        "A stock divided by a flow. Ninety dollars is six months on one account "
        "and forty minutes on another, and only the quotient says which.",
        ("Balance.json and daily usage", "balance over the median day"),
        [
            ("Past the floor and the peak", "leave it", "good"),
            ("No priced usage at all", "no rate to divide by", "plain"),
            ("Under the seven day floor", "a card, a weekend, gone", "bad"),
            ("Smaller than one busy day", "one repeat suspends it", "bad"),
        ],
    ),
}

V["twilio/subaccount-suspended-silently"] = {
    "flow_intro": (
        "The parent is not a useful place to watch from, so the script asks the "
        "account list for the stopped ones by status and then checks ownership, "
        "because the parent's own row lists itself as its owner."
    ),
    "diagram_problem": D.chain(
        "tsusp-p",
        "One tenant stopped for days while the parent account looks healthy",
        "Suspension cascades down and never up, so every health check written "
        "against the parent SID reports green throughout.",
        [
            ("Subaccount suspended", "by API or by cascade"),
            ("No notification", "no email, no webhook"),
            ("Tenant traffic stops", "20005 and 30002"),
            ("Parent looks green", "totals barely move"),
            ("Customer opens a ticket", "days later, by phone"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tsusp-f",
        "Sorting accounts under one parent by whether that tenant can still send",
        "Suspended and closed must never be summed. One is a single write away "
        "from working; the other has already released the numbers.",
        ("GET Accounts.json by status", "sid, owner_account_sid, status"),
        [
            ("Active tenant", "nothing to do", "good"),
            ("The parent's own row", "it owns itself", "plain"),
            ("Suspended", "one write restores it", "bad"),
            ("Closed", "terminal, numbers gone", "bad"),
        ],
    ),
}

V["twilio/rest-api-concurrency-exhausted"] = {
    "flow_intro": (
        "There is no readable limit field, so the check samples what it can see "
        "and asks you for the ceiling. A peak with no threshold beside it is an "
        "observation, and the classifier says so rather than inventing one."
    ),
    "diagram_problem": D.chain(
        "tconc-p",
        "Slower responses filling the concurrency budget without the send rate changing",
        "Concurrency is requests in flight, not requests per second. Latency "
        "alone can breach the ceiling on traffic that never grew.",
        [
            ("Steady request rate", "unchanged all week"),
            ("Responses slow down", "in flight count climbs"),
            ("Ceiling reached", "429 with 20429"),
            ("Client retries at once", "no backoff, no jitter"),
            ("Pinned at the limit", "rejections take slots too"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tconc-f",
        "Sorting sampled concurrency readings against the ceiling for the account",
        "Sample during the busiest ten minutes. A reading taken at three in the "
        "morning describes an idle account and reassures you about nothing.",
        ("Twilio-Concurrent-Requests", "sampled through the peak"),
        [
            ("Well under the ceiling", "headroom", "good"),
            ("No ceiling supplied", "a peak, not a finding", "plain"),
            ("Near the ceiling", "one slow patch closes it", "bad"),
            ("A 429 during the sample", "at the limit right now", "bad"),
        ],
    ),
}

V["twilio/unreleased-recordings-storage"] = {
    "flow_intro": (
        "A count of files is a number nobody can price. The classifier reports "
        "the accumulated spend and a year of the current rate, because those are "
        "the units that get a deletion job scheduled."
    ),
    "diagram_problem": D.chain(
        "trecs-p",
        "Recordings billing for storage every month because nothing ever deletes them",
        "The archiving code works. The half it skips is invisible, and the "
        "monthly increase is never large enough to open a ticket about.",
        [
            ("Recording enabled", "on one support line"),
            ("Media downloaded", "archived in your bucket"),
            ("Twilio copy kept", "no expiry, no lifecycle"),
            ("Storage billed monthly", "per stored minute"),
            ("Four years later", "a pile nobody priced"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "trecs-f",
        "Sorting an account's recordings by whether anything is deleting them",
        "date_created is RFC 2822, not ISO 8601. A parser that throws on every "
        "row produces a clean report for an account full of old media.",
        ("All time spend and oldest file", "priced, not counted"),
        [
            ("Nothing older than the window", "something deletes them", "good"),
            ("Spend but nothing stored", "the pile is already gone", "good"),
            ("Old files, priced daily", "project the year ahead", "bad"),
            ("Old files, no priced usage", "check the category name", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
