#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch O.

One list, read four ways. Every chain here starts from the same place, which is
a credential sitting in a roster, and the four of them have to look different
enough that nobody reads the batch as one picture drawn with four captions.

The first chain ends in a credential nothing depends on, and its fix branch is
sorted by revocation safety rather than by age, because the whole practical
point is which rows can be deleted this afternoon. The second ends in money
moving through a person, and its branch deliberately grades the same key the
same way whatever share of the bill it holds: that is the line between this
note and the published concentration one, and the picture has to hold it too.

The third is the odd one out and is drawn that way. Nothing in its chain goes
wrong at any step. The service account was the right decision, the key works
perfectly, and the failure is that a second key has never existed, so the fix
branch keys off the key count rather than the age.

The fourth has no object in it at all. It is a feed nobody subscribed to, and
its branch is the only one in the batch whose least useful outcome is an empty
result: a log that says nothing is not a log that says everything is fine.

Drawn in teal, matching the rest of the section. No em dashes inside SVG text:
one mis-sniffed encoding turns a single character into three mojibake ones
inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further: visuals.py imports several of
# these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#0D9488"
D.set_theme(BRAND)

V = {}

V["llm/api-key-never-used"] = {
    "flow_intro": (
        "An unused credential is the only fault in this section that emits "
        "nothing at all: no requests, no tokens, no cost line, no audit entry "
        "after the one that created it. The only place it exists is a list, "
        "and the two parameters that decide what that list contains both "
        "default to showing you less of it."
    ),
    "diagram_problem": D.chain(
        "llmnever-p",
        "A credential minted for a reason that evaporated, and never revoked",
        "Nobody left and nothing broke. The owner is still here and could "
        "tell you in one sentence what this key was for.",
        [
            ("Key minted in a hurry", "for a trial, a spike, a 2am fix"),
            ("The reason evaporates", "and nothing marks the key"),
            ("No traffic, no cost", "so no report mentions it"),
            ("Sweep misses it too", "narrow defaults hide rows"),
            ("Still live, full access", "in a chat thread somewhere"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmnever-f",
        "Sorting each key by what its usage evidence actually supports",
        "Ordered by revocation safety, not by age. A key nothing has ever "
        "used cannot break anything when it goes.",
        ("last_used_at, or a set", "difference where there is none"),
        [
            ("Null, and older than the threshold", "never used: the safest one to revoke", "bad"),
            ("Real, but idle for months", "something was built here. Ask first", "bad"),
            ("Absent from the report window", "unused in the window, not ever", "plain"),
            ("Minted in the last month", "too new to conclude anything", "plain"),
            ("Used this week", "load bearing, and it is fine", "good"),
        ],
    ),
}

V["llm/legacy-user-owned-keys-in-project"] = {
    "flow_intro": (
        "Two lifecycles get bound together on the first afternoon of a "
        "project and stay bound for years, because a personal key "
        "authenticates immediately and a service account asks you to have an "
        "opinion about structure first. There is no failure state until an "
        "employment record changes, which is why this survives so long."
    ),
    "diagram_problem": D.chain(
        "llmuown-p",
        "A service standing on a credential attached to somebody's employment",
        "Every step is somebody making a reasonable choice under time "
        "pressure. Nothing here is a mistake on the day it happens.",
        [
            ("Personal key minted", "it works immediately"),
            ("Service ships on it", "nothing prompts a change"),
            ("Spend attributes to a person", "who forgot it exists"),
            ("Team move or departure", "an HR event, not a deploy"),
            ("Emergency rotation", "at 2am, with no overlap"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "llmuown-f",
        "Sorting each key by who owns it, with money used only to rank the repair",
        "The share of the bill is not an input. Two personal keys splitting "
        "production evenly are two findings here.",
        ("owner.type, joined to", "cost by api_key_id"),
        [
            ("A person owns it, money moves on it", "migrate: create, deploy, verify, revoke", "bad"),
            ("A person owns it, no spend behind it", "a revocation, not a migration", "bad"),
            ("Spending user keys, no service accounts", "the project has never had the mechanism", "bad"),
            ("Owner block missing or unrecognised", "unattributable: nobody owns the lifecycle", "plain"),
            ("A service account owns it", "bound to the service, as intended", "good"),
        ],
    ),
}

V["llm/service-account-key-never-rotated"] = {
    "flow_intro": (
        "This chain is the reward for having done it right, which is why "
        "nothing in it fails. Service accounts fix ownership and in doing so "
        "remove the last event that would ever have forced anybody to think "
        "about the key again. There is no rotated_at field on either "
        "provider, so created_at on the newest key is the only clock there is."
    ),
    "diagram_problem": D.chain(
        "llmsarot-p",
        "A key that works perfectly and has never been replaced",
        "No step here is wrong. The account was the right call, the key is "
        "healthy, and the second key has simply never existed.",
        [
            ("Service account created", "exactly as advised"),
            ("One key minted", "and deployed everywhere"),
            ("No expiry, no prompt", "nothing ages it out"),
            ("Rotation is a cutover", "one key, so no rollback"),
            ("Deferred again", "and the clock keeps running"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmsarot-f",
        "Sorting each service account by the age of its newest key and the key count",
        "Newest, not oldest. An account rotated last week still holds the "
        "retired key until somebody revokes it.",
        ("Newest created_at", "and how many keys exist"),
        [
            ("Past the threshold, and the only key", "no overlap has ever existed", "bad"),
            ("Past the threshold, several keys", "overlap was available and unused", "bad"),
            ("One fresh key, one old and still live", "a rotation that was never finished", "bad"),
            ("No keys at all on the account", "a migration that stopped halfway", "plain"),
            ("Newest key inside the window", "rotating on a cadence", "good"),
        ],
    ),
}

V["llm/unreviewed-key-lifecycle-in-audit-log"] = {
    "flow_intro": (
        "The only note in this batch whose subject is events rather than "
        "objects, and therefore the only one that can see a credential that "
        "no longer exists. Both providers record all of this faithfully and "
        "neither pushes any of it anywhere, so the control is complete, "
        "correct, and has never once been read."
    ),
    "diagram_problem": D.chain(
        "llmkevt-p",
        "A complete audit trail that nothing subscribes to",
        "The log is not broken. It is doing exactly what it was built to do, "
        "which is to store events until somebody asks.",
        [
            ("Key minted at 02:14", "by an actor nobody knows"),
            ("Recorded correctly", "with the IP and the country"),
            ("Pull only", "no webhook, no email, no alert"),
            ("Nobody built the puller", "a healthy log looks empty"),
            ("Read during an incident", "five months too late"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmkevt-f",
        "Sorting each event by its actor, its hour and where it came from",
        "The roster join is the whole thing. An email in a log entry is a "
        "string until it is checked against who still works here.",
        ("Lifecycle events, actors", "resolved against the roster"),
        [
            ("Actor is no longer on the roster", "an action nobody has ever read", "bad"),
            ("Country outside your geographies", "OpenAI session actors only", "bad"),
            ("Created outside business hours", "worth one question, at least", "bad"),
            ("An api_key actor, so no email", "unattributable to any person", "plain"),
            ("The feed returned nothing at all", "unknown, and never clean", "plain"),
            ("On roster, in hours, expected", "reviewable, and reviewed", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
