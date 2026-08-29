#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch M.

Regulatory and geographic failures. Two of these have no setting to read at all,
so the fix diagram sorts evidence rather than configuration: what the traffic did
is the only input the script has.

Same two shapes as the rest of the site, drawn in Twilio red: the problem is a
chain that breaks at one step, the fix is a branch, because every script in this
section classifies what it finds rather than guessing.

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

V["twilio/sms-geo-permissions-disabled"] = {
    "flow_intro": (
        "The script reads traffic rather than configuration, because SMS Geo "
        "Permissions has no REST resource in either direction. Grouping the 21408 "
        "rejections by destination country is what turns a pile of failed messages "
        "into a list of countries to enable."
    ),
    "diagram_problem": D.chain(
        "tgeo-p",
        "An international launch blocked by a geo permission nobody could read",
        "Nothing in the account is misconfigured in a way any API can show you. "
        "The country was simply never on the list.",
        [
            ("Account opened", "home country enabled"),
            ("Product ships", "no country setting in code"),
            ("First user abroad", "send looks identical"),
            ("Rejected 21408", "region not enabled"),
            ("No setting to read", "console only, both ways"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tgeo-f",
        "Sorting destination countries by what their 21408 rejections mean",
        "The same error code covers a country nobody enabled, a To value with a "
        "mangled prefix, and a destination that can never be enabled at all.",
        ("Messages grouped by country", "blocked against accepted"),
        [
            ("No 21408 at all", "permitted, on this evidence", "good"),
            ("Blocked and accepted mixed", "the To values are wrong", "plain"),
            ("Every send blocked", "country was never enabled", "bad"),
            ("Iran, Syria, Cuba", "no permission can be set", "bad"),
        ],
    ),
}

V["twilio/alphanumeric-sender-id-unregistered"] = {
    "flow_intro": (
        "The script keys the tally on the sender and the destination country "
        "together, because registration is granted for one string in one country. "
        "A per-sender total averages a dead market into a healthy number."
    ),
    "diagram_problem": D.chain(
        "talpha-p",
        "An alphanumeric sender ID accepted by the API and refused by the carrier",
        "The create call cannot fail on this. The rule belongs to a regulator in "
        "the destination country, which Twilio has no way to check at request time.",
        [
            ("Sender works in EU", "two years, no trouble"),
            ("Launch in India", "same string, same code"),
            ("API returns 201", "message row created"),
            ("Carrier rejects", "30040 or 30041"),
            ("Billed, undelivered", "seen only in the row"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "talpha-f",
        "Sorting sender and destination pairs by what the rejection says",
        "A case difference is a one line change in your sending code. A missing "
        "registration is a form and a wait, so the two belong in different rows.",
        ("Sender plus destination", "against the configured senders"),
        [
            ("Nothing rejected", "delivering there", "good"),
            ("Only 30018 so far", "warning level, notice given", "plain"),
            ("Blocked, case differs", "fix the string you send", "bad"),
            ("Blocked, string matches", "unregistered in that country", "bad"),
        ],
    ),
}

V["twilio/emergency-address-unregistered"] = {
    "flow_intro": (
        "The script judges on emergency_address_status rather than on "
        "emergency_address_sid, because the SID records a submission and the "
        "status records whether the validation accepted it."
    ),
    "diagram_problem": D.chain(
        "te911-p",
        "A 911 call from a number that never completed its address registration",
        "There is no failure anywhere until the call is placed. The number works "
        "perfectly for every other kind of traffic.",
        [
            ("Number bought", "address is optional"),
            ("Voice in production", "a year of clean calls"),
            ("Somebody dials 911", "softphone, sales floor"),
            ("No address to send", "routed to a national centre"),
            ("Operator asks where", "and a fee is passed on"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "te911-f",
        "Sorting numbers by whether a dispatcher would actually receive an address",
        "The rejected registration is the one that survives every check: the "
        "console shows a street address on a number that has none that works.",
        ("Numbers in scope for E911", "plus one status field"),
        [
            ("Registered and active", "a dispatcher gets it", "good"),
            ("Not plus one, or no voice", "out of scope, not a finding", "plain"),
            ("No address at all", "national centre, per call fee", "bad"),
            ("Rejected or pending", "looks done, is not", "bad"),
        ],
    ),
}

V["twilio/shortcode-cross-border-sender-mismatch"] = {
    "flow_intro": (
        "The script takes the licensing country as an argument, because the "
        "ShortCode resource carries the digits and no country. Everything else is "
        "read: the pool shape from the service, the destinations from the traffic."
    ),
    "diagram_problem": D.chain(
        "tshort-p",
        "A short code selected for a handset in a country it is not licensed for",
        "Sender selection happens per message, which is why this arrives as a few "
        "customers never receiving anything rather than as an outage.",
        [
            ("Short code added", "high domestic throughput"),
            ("Long codes in same pool", "one service for everything"),
            ("Send to another country", "selection picks per message"),
            ("Short code chosen", "licensed nationally only"),
            ("Rejected 21612", "before any carrier hop"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tshort-f",
        "Sorting Messaging Services by how their short codes meet foreign traffic",
        "A mixed pool that has never sent abroad is not clean, it is unproven. The "
        "first international recipient is what changes the answer.",
        ("Pool shape plus destinations", "home country as an argument"),
        [
            ("No short code in pool", "nothing to select wrongly", "good"),
            ("All traffic domestic", "correct today, fused", "plain"),
            ("Mixed pool, foreign sends", "the draw decides who fails", "bad"),
            ("Short codes only, abroad", "no sender can carry it", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
