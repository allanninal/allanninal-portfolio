#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch J.

Four notes about a request that is refused for a reason nothing in the
credential explains. Two of them are mismatches and they run in opposite
directions: one is a good credential pointed at a route that will never accept
its class, the other is a route that accepts the credential perfectly and a
principal nobody meant to depend on. One is a date string that the calendar
retired while the code stood still. One is arithmetic on two numbers the client
itself chose, provable on the machine that chose them.

So the four problem chains end in four different places: a substitute endpoint,
a resignation letter, a 410 on an untouched deployment, and a claim that was
wrong before it left the process. And the fix branches sort on four different
readings: a path matched against the audiences it accepts, a profile body read
for human signals, a pinned date diffed against a served list, and a lifetime
subtracted from a ceiling with no request at all.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where
nothing downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further: visuals.py imports several of
# these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/installation-token-rejected-by-endpoint"] = {
    "flow_intro": (
        "Two GETs, and neither of them is the one that hurts. The first is "
        "the liveness proof: an installation token that can list its own "
        "repositories is not a broken credential, whatever the second "
        "response says. The second is the path you were already calling. "
        "Everything after that is a lookup, because the answer is a property "
        "of the route rather than of the token, and the useful output is a "
        "different path to call rather than a permission to add."
    ),
    "diagram_problem": D.chain(
        "ghaud-p",
        "A valid installation token refused by one route it can never satisfy",
        "Every step in this loop is reasonable, and the loop has no exit "
        "because the thing being adjusted is not the thing that is wrong.",
        [
            ("App installs fine", "token mints, calls work"),
            ("GET /user 403s", "not accessible by integration"),
            ("Permission added", "installers asked to accept"),
            ("Same 403 returns", "no header named anything"),
            ("Blamed on GitHub", "ticket filed, closed"),
        ],
        fail_at=1,
        loop=(3, 2, "so a wider permission is tried next"),
    ),
    "diagram_fix": D.branch(
        "ghaud-f",
        "Sorting a refused path by the credential classes it accepts",
        "Three of these four have nothing to do with permissions, which is "
        "why the report names a replacement route rather than a scope.",
        ("Path against its audiences", "token proven alive first"),
        [
            ("Route wants a user", "swap in the App equivalent", "bad"),
            ("Route wants the App JWT", "sign one, do not send this", "bad"),
            ("Route does accept it", "permission problem, other note", "plain"),
            ("Route is not refusing", "the 403 came from elsewhere", "good"),
        ],
    ),
}

V["github/unsupported-api-version"] = {
    "flow_intro": (
        "One unauthenticated GET carries the whole check. The list of "
        "versions GitHub still serves is public, so the comparison costs "
        "nothing and can run on a schedule rather than during an incident. "
        "The pinned value is a string your own client owns, which makes this "
        "the rare failure that is knowable months before it happens: a "
        "version drops off the list first and starts answering 410 later."
    ),
    "diagram_problem": D.chain(
        "ghapiv-p",
        "A date pinned in a header outliving the version it names",
        "Nothing in this chain is a change to the integration. The only "
        "moving part is the calendar, which is why the search starts in the "
        "wrong place.",
        [
            ("Version pinned once", "copied from a 2022 sample"),
            ("Years of green", "header never revisited"),
            ("Retirement announced", "in a changelog nobody reads"),
            ("410 on everything", "looks like an outage"),
            ("Credentials rotated", "the header is untouched"),
        ],
        fail_at=2,
        loop=(4, 3, "and the next theory is the network"),
    ),
    "diagram_fix": D.branch(
        "ghapiv-f",
        "Diffing the pinned version against the list GitHub still serves",
        "Two of these are healthy and one of them is still worth an alert, "
        "because being behind is the only state you can act on calmly.",
        ("GET /versions, no token", "pinned value against served list"),
        [
            ("Pinned and retired", "410 now, move the pin forward", "bad"),
            ("Not a version at all", "typo, so the header is ignored", "bad"),
            ("Supported but behind", "read the notes, schedule it", "plain"),
            ("Pinned and current", "the pin is doing its job", "good"),
        ],
    ),
}

V["github/wrong-identity-token"] = {
    "flow_intro": (
        "One GET, and it is the profile rather than the headers. This script "
        "reads no scopes and no expiry: the question is not what the "
        "credential may do but who it is, and the answer is in the body. The "
        "signals are counted and named, so the report says a person rather "
        "than a probability, and the optional commit sweep turns that into a "
        "number that a reviewer can see in the history."
    ),
    "diagram_problem": D.chain(
        "ghwho-p",
        "An integration whose identity is somebody's employment",
        "There is no failure anywhere in this chain until the last box, and "
        "the last box is a calendar event in a different department.",
        [
            ("PAT made in a hurry", "on a personal account"),
            ("Bot posts as a human", "reviews signed with a face"),
            ("Everyone forgets", "it has worked for years"),
            ("Account deprovisioned", "leaver process runs"),
            ("401 everywhere", "and nobody owns the fix"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "ghwho-f",
        "Reading the profile body for whether the actor is a person",
        "Only one of these four is an App. The middle two work today and are "
        "still coupled to a human, which is the finding worth writing down.",
        ("GET /user, the body", "identity, not permissions"),
        [
            ("Human account", "name, bio, followers, a face", "bad"),
            ("Shared machine login", "human shaped, owner unknown", "bad"),
            ("Machine account, owned", "documented, in a vault", "plain"),
            ("Ends in bracket bot", "an App installation acts", "good"),
        ],
    ),
}

V["github/jwt-exp-too-far-future"] = {
    "flow_intro": (
        "The finding needs no network at all. A JWT is three base64url "
        "segments and two of the claims in the middle one are numbers your "
        "own code chose, so the ceiling check is a subtraction on the machine "
        "that did the choosing. The single GET is confirmation rather than "
        "diagnosis, and the script stops there: minting an installation token "
        "is a write, and this page never writes."
    ),
    "diagram_problem": D.chain(
        "ghjwte-p",
        "A JWT rejected for a lifetime the client chose before sending it",
        "The key is right, the App exists and the signature verifies. The "
        "request is refused on a number, and the number was decided three "
        "lines above the request.",
        [
            ("exp set to an hour", "habit from another system"),
            ("401 from GET /app", "before any permission check"),
            ("Key regenerated", "the obvious suspect first"),
            ("Same 401 returns", "prose blamed on the docs"),
            ("Retries every minute", "each one wrong the same way"),
        ],
        fail_at=1,
        loop=(4, 2, "and the key is replaced again"),
    ),
    "diagram_fix": D.branch(
        "ghjwte-f",
        "Subtracting iat from exp against the ten minute ceiling",
        "Four verdicts from two integers and a local clock. Nothing is "
        "transmitted to reach any of them, and the signature is never read.",
        ("Decode the payload locally", "no key, no request"),
        [
            ("Lifetime over ten minutes", "print the seconds to remove", "bad"),
            ("exp already in the past", "the JWT was cached too long", "bad"),
            ("iat ahead of this clock", "drift, a different repair", "plain"),
            ("Inside the ceiling", "the 401 is not about exp", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
