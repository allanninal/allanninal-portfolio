#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch B.

All four notes share one spine: GitHub answers, the answer is well-formed, and
the answer is not the whole truth. So every problem chain ends on somebody
trusting a response that was never complete, and every fix is a branch, because
each script sorts what it found rather than guessing at it. Drawn in GitHub blue.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/404-masking-403"] = {
    "flow_intro": (
        "The script spends three cheap reads before it says anything, because a "
        "404 on its own carries no information at all: the fact that separates a "
        "dead token from a missing scope from a missing installation lives on a "
        "different endpoint every time."
    ),
    "diagram_problem": D.chain(
        "gh404-p",
        "A repository visible in the browser and absent from the API",
        "Nothing here is an error. The status code is the one GitHub chose on "
        "purpose, and it is the same code a typo produces.",
        [
            ("Repo open in a tab", "you can see it"),
            ("Script asks for it", "GET /repos/owner/name"),
            ("Token cannot see it", "no scope, or no install"),
            ("GitHub answers 404", "not 403, deliberately"),
            ("An hour on spelling", "the name was fine"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "gh404-f",
        "Sorting one 404 by what three other reads say about the credential",
        "The last outcome stays ambiguous on purpose. No grant and genuinely "
        "deleted are the same response, and a confident guess there costs more "
        "than an honest shrug.",
        ("Identity, repo, installation", "three GET requests"),
        [
            ("Repo answers 200", "it exists and you reach it", "good"),
            ("404, no repo scope", "the scope, not the name", "bad"),
            ("404, outside the install", "add the repository", "bad"),
            ("404, scope is present", "no grant, or really gone", "plain"),
        ],
    ),
}

V["github/saml-partial-results"] = {
    "flow_intro": (
        "The script reads a header on every page rather than the body on the "
        "first, because the omission is never in the JSON: a partial answer and "
        "a complete one are byte for byte the same shape."
    ),
    "diagram_problem": D.chain(
        "ghsso-p",
        "An organization list that is short by two and says so nowhere in the body",
        "Every step is a success. The inventory is wrong for two years and never "
        "logs a single warning.",
        [
            ("Token lists the orgs", "GET /user/orgs"),
            ("Two enforce SAML", "token not authorized"),
            ("GitHub answers 200", "four orgs, valid JSON"),
            ("Omission in a header", "X-GitHub-SSO"),
            ("Inventory under reports", "nightly, for years"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ghsso-f",
        "Sorting a response by what the X-GitHub-SSO header says about it",
        "A header value the parser does not recognise is the dangerous one: read "
        "as absence it turns a partial answer into a clean bill of health.",
        ("Header read on every page", "not the body, not page one"),
        [
            ("No header on a 200", "the list is the whole list", "good"),
            ("partial-results", "org ids that were withheld", "bad"),
            ("required, with a url", "at least it failed loudly", "bad"),
            ("A value you cannot parse", "never read as clean", "plain"),
        ],
    ),
}

V["github/installation-repository-selection-partial"] = {
    "flow_intro": (
        "The script needs a number from outside the App, because nothing inside "
        "an installation can tell you what the installation is missing. Every "
        "endpoint under it is answering completely, about a smaller world."
    ),
    "diagram_problem": D.chain(
        "ghsel-p",
        "An audit that reports clean across nine percent of an organization",
        "No truncation flag, no warning and no error. The response is correct; "
        "the question was smaller than anyone thought.",
        [
            ("App installed in 2023", "selected repositories"),
            ("140 repos exist now", "12 were ever ticked"),
            ("Audit lists what it sees", "12 rows, no error"),
            ("Summary says all clear", "across 12 of 140"),
            ("128 never scanned", "nobody asked about them"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ghsel-f",
        "Sorting an installation by its own count against the organization's",
        "Selected and complete is deliberately not the same verdict as all: it "
        "is correct today and nothing keeps it correct tomorrow.",
        ("Installation count vs org count", "one read inside, one outside"),
        [
            ("Selection is all", "new repos join by themselves", "good"),
            ("Selected, counts match", "complete by coincidence", "plain"),
            ("Selected, 12 of 140", "a clean report on 9 percent", "bad"),
            ("Org total unreadable", "a count, not a coverage figure", "plain"),
        ],
    ),
}

V["github/app-permission-missing"] = {
    "flow_intro": (
        "This is the one where GitHub does answer, so the script mostly reads: "
        "the header on the failing 403 names what the endpoint wanted, and "
        "GET /app names what the App holds. The diff is the whole diagnosis."
    ),
    "diagram_problem": D.chain(
        "ghperm-p",
        "A 403 whose message names nothing and whose header names everything",
        "The answer travels back on the same response that failed. It is dropped "
        "by the client, not withheld by the API.",
        [
            ("One endpoint 403s", "Resource not accessible"),
            ("The other 19 work", "so it reads as a bug"),
            ("Header names the fix", "x-accepted-github-permissions"),
            ("Client kept status only", "days on the wrong theory"),
            ("Permission added, inert", "installers never accepted"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ghperm-f",
        "Sorting a 403 by the endpoint's header against the App's own map",
        "Read where write was needed is its own state, because it is the case "
        "that survives a careful look down a settings page.",
        ("Header vs GET /app", "what was wanted, what is held"),
        [
            ("Held at the right level", "look at the installation", "good"),
            ("Read where write is needed", "raise the level", "bad"),
            ("Not in the map at all", "add it, then get it accepted", "bad"),
            ("403 with no header", "the endpoint refuses App tokens", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
