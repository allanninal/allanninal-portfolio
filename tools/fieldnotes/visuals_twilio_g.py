#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch G.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Twilio red.

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

V["twilio/idle-phone-numbers-billed"] = {
    "flow_intro": (
        "The script joins three resources, because no single one shows the finding: "
        "the numbers come from the account API, the spend from the monthly usage "
        "record, and the traffic from four small queries per number."
    ),
    "diagram_problem": D.chain(
        "tidl-p",
        "A number bought for one test and rented for three years",
        "Nothing here fails. The number is provisioned, billed and never used, "
        "and the invoice reports a category total rather than a number.",
        [
            ("Number bought", "to reproduce one bug"),
            ("Test finished", "nobody releases it"),
            ("Monthly rent", "charged whatever happens"),
            ("Invoice aggregates", "phonenumbers, one total"),
            ("Three years on", "nobody knows what it is for"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tidl-f",
        "Sorting phone numbers by traffic in both directions against monthly rent",
        "Checking outbound only is how somebody releases a working support line, "
        "so the inbound half of the query is not optional.",
        ("Numbers, usage and traffic", "four reads per number"),
        [
            ("Traffic both ways", "earning its rent", "good"),
            ("Inbound only", "confirm before releasing", "plain"),
            ("A few events a quarter", "costs more per message", "bad"),
            ("Silent for 90 days", "release it, here is the yearly cost", "bad"),
        ],
    ),
}

V["twilio/trial-account-segment-limit-30044"] = {
    "flow_intro": (
        "The script reads the account type first, because 30044 only exists on a "
        "trial account: the same rejection on a paid one means the sending code is "
        "authenticating as an account you are not looking at."
    ),
    "diagram_problem": D.chain(
        "ttsl-p",
        "One emoji turning a tested template into a rejected message",
        "The character added costs one unit. The encoding change it forces costs "
        "the whole budget, from 160 characters down to 70.",
        [
            ("Template written", "150 characters, tested"),
            ("Emoji appended", "one friendly character"),
            ("Body flips to UCS-2", "budget drops to 70"),
            ("Trial cap exceeded", "error 30044"),
            ("Nothing sent", "short tests still pass"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ttsl-f",
        "Sorting an account by type against the 30044 rejections in its message list",
        "A trial account with no rejections yet is not safe, it is untested: one "
        "accented name in real data and the same cap applies.",
        ("Account type and Messages", "joined on error_code"),
        [
            ("Paid, no 30044", "cap does not apply", "good"),
            ("Trial, no 30044 yet", "one emoji away from it", "plain"),
            ("Trial, 30044 present", "upgrade or shorten", "bad"),
            ("Paid, 30044 present", "you are reading the wrong account", "bad"),
        ],
    ),
}

V["twilio/outbound-messaging-disabled-30037"] = {
    "flow_intro": (
        "The script buckets every failure by the account_sid on the message row, "
        "because four different causes produce this one error code and only the "
        "join against the account list tells them apart."
    ),
    "diagram_problem": D.chain(
        "tomd-p",
        "One tenant refused while nineteen identical ones keep sending",
        "Every per-request theory checks out. The variable is the account the "
        "credential belongs to, and nobody re-reads that.",
        [
            ("Same code deployed", "twenty tenants"),
            ("One subaccount suspended", "billing or compliance"),
            ("No notification", "status is a field nobody polls"),
            ("Every send 30037", "outbound not allowed"),
            ("Body and numbers checked", "all identical to the ones that work"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tomd-f",
        "Sorting accounts by status against the 30037 failures attributed to each",
        "The most useful row is the last one: failures on a SID that is not in "
        "your account list at all.",
        ("Accounts plus Messages", "bucketed by account_sid"),
        [
            ("Active, no 30037", "sending normally", "good"),
            ("Suspended", "reactivate, or Support", "bad"),
            ("Active but refused", "messaging disabled on it", "bad"),
            ("SID not in your list", "wrong credential entirely", "bad"),
        ],
    ),
}

V["twilio/deactivated-number-recycling"] = {
    "flow_intro": (
        "The script normalises both sides before comparing, because the feed is "
        "E.164 and a contact table is not: intersecting the raw strings matches "
        "nothing and prints a clean report."
    ),
    "diagram_problem": D.chain(
        "tdnr-p",
        "A verification code delivered successfully to the wrong person",
        "Every metric says the send worked, and it did. The only thing that "
        "changed is who is holding the handset.",
        [
            ("Consent recorded", "by the previous owner"),
            ("Number disconnected", "carrier reclaims it"),
            ("Reissued", "new subscriber, same digits"),
            ("OTP delivered", "status reads delivered"),
            ("Complaints rise", "30007 filtering months later"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tdnr-f",
        "Sorting contacts against the daily deactivation feed by what you already sent",
        "A match you have not messaged yet is a suppression job. A match you have "
        "is an incident with a date on it.",
        ("Deactivations and contacts", "both normalised to E.164"),
        [
            ("Not in the feed", "still the same owner", "good"),
            ("Matched, already suppressed", "keep the record", "plain"),
            ("Matched, never messaged", "suppress before the next send", "bad"),
            ("Matched, messaged since", "a stranger got the code", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
