#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch V.

Four states of the account itself rather than of anything it sends. Same two
shapes as the rest of the site: the problem is a chain that breaks at one step,
the fix is a branch, because every script in this section classifies what it
finds rather than guessing. Drawn in Twilio red.

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

V["twilio/account-suspended-or-closed"] = {
    "flow_intro": (
        "The script reads one field and then counts what the suspension already "
        "cost, because a balance suspension can clear itself within minutes and "
        "the block of 30002 rows is the only evidence it leaves behind."
    ),
    "diagram_problem": D.chain(
        "tacct-p",
        "An account suspended mid traffic while every read still succeeds",
        "Reads are not what stops. The Console loads, the message list loads, "
        "and only the requests that create something are refused.",
        [
            ("Balance crosses zero", "no grace period"),
            ("Status set suspended", "no notification"),
            ("New sends refused", "403 with 20005"),
            ("Queued backlog dies", "30002 on each row"),
            ("Health checks pass", "reads still answer"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tacct-f",
        "Sorting one account by its status field and the 30002s behind it",
        "Closed is one word away from suspended in the same field and a "
        "completely different outcome: it is not reopened.",
        ("GET Accounts/{Sid}.json", "status, plus 30002 in the window"),
        [
            ("Active, window clean", "nothing to do", "good"),
            ("Active, 30002s behind", "it was down, date it", "plain"),
            ("Suspended", "everything refused now", "bad"),
            ("Closed", "terminal, new account", "bad"),
        ],
    ),
}

V["twilio/trial-account-still-in-use"] = {
    "flow_intro": (
        "The script counts distinct destinations rather than messages, because "
        "volume can be one tester pressing a button while four destinations on a "
        "trial account is already more than it can ever reach."
    ),
    "diagram_problem": D.chain(
        "ttrial-p",
        "A trial account carrying a launch it can never deliver",
        "Every step works. The same SDK, the same credentials and the same 201 "
        "responses as a paid account, right up to real recipients.",
        [
            ("Account made to test", "trial, costs nothing"),
            ("Two phones verified", "both work all week"),
            ("Staging ships", "nothing says upgrade"),
            ("Real users added", "21608 on each one"),
            ("Delivered ones tagged", "trial prefix on the body"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "ttrial-f",
        "Sorting a trial account by how much real traffic is aimed at it",
        "Trial is not a fault by itself. A development account should be on "
        "trial, and reporting that as an incident teaches people to ignore it.",
        ("Account type plus the window", "distinct destinations, 21608 count"),
        [
            ("Type is Full", "no restriction, no prefix", "good"),
            ("Trial, few destinations", "a dev account, upgrade first", "plain"),
            ("Trial, many destinations", "aimed at people it cannot reach", "bad"),
            ("Trial with 21608s", "already failing in the open", "bad"),
        ],
    ),
}

V["twilio/trial-verified-caller-ids-exhausted"] = {
    "flow_intro": (
        "The script joins the verified list to the destinations actually used, "
        "because a count on its own is a number between zero and three with no "
        "way of knowing whether it was enough."
    ),
    "diagram_problem": D.chain(
        "tvcid-p",
        "A fourth tester refused by a quota spent months earlier",
        "Nothing recently changed. The countdown was spent one ordinary "
        "verification at a time, and the wall is only reached later.",
        [
            ("Your phone verified", "slot one"),
            ("Test handset verified", "slot two"),
            ("A personal number", "slot three, one Sunday"),
            ("Colleague joins", "no slots remain"),
            ("Their phone 21608s", "yours still works"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tvcid-f",
        "Sorting the verified pool against the numbers the app actually sends to",
        "Deleting a caller ID to free a slot loses a working verification and "
        "returns nothing: the quota counts verifications, not entries.",
        ("Caller IDs plus destinations", "compared in E.164"),
        [
            ("Type is Full", "the list no longer gates", "good"),
            ("All covered, slots left", "fine for now", "good"),
            ("Unverified destinations", "those sends get 21608", "bad"),
            ("Three verified already", "lifetime quota spent", "bad"),
        ],
    ),
}

V["twilio/read-credential-permission-denied"] = {
    "flow_intro": (
        "The script probes the account resource first because it is the "
        "narrowest read the credential could be allowed at all: if that answers, "
        "every 20003 further out is a boundary rather than a fault."
    ),
    "diagram_problem": D.chain(
        "t20003-p",
        "A healthy read key rotated because one endpoint said 20003",
        "One code covers a deleted key, a crossed SID, a stripped header and a "
        "key working exactly as issued. The response is identical for all four.",
        [
            ("Read key issued", "standard, works fine"),
            ("Script reads Keys.json", "main key only"),
            ("401 with 20003", "no detail in the body"),
            ("Read as a bad key", "credential blamed"),
            ("Key rotated", "same answer, hours gone"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "t20003-f",
        "Sorting a 20003 by which probe returned it",
        "A 403 carrying 20005 is not a permission problem at all: the account "
        "has stopped, and no credential change moves it.",
        ("Probe account, then Keys", "status plus the code in the body"),
        [
            ("All three read", "full read access", "good"),
            ("Account fine, Keys 20003", "standard key boundary", "good"),
            ("Account 20003", "dead credential, fix it", "bad"),
            ("Different sid returned", "parent and child crossed", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
