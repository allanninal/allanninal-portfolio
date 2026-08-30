#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch K.

Four notes about a GitHub App that cannot get in, and four different doors, so
the four problem chains have to end somewhere different from each other or the
pages start to look like one page repeated. They end at a container whose clock
nobody owns, a rotation that deleted the wrong key, a migration that died at
fifty-eight minutes, and a repository created after the installation that was
meant to cover it.

The fix branches sort on four different readings too, and none of them is a
permission: a Date header against a local clock, a PEM label against a
fingerprint, a lifetime against a refresh interval, and a per-repository
presence question that returns a yes or a no. Two of the four could have been
drawn as "the 401 is explained" and are deliberately not, because the useful
output in one case is a number of seconds and in the other is which App you
turned out to be.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where
nothing downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the
# module. Every diagram here is constructed at import time, so the theme has to
# be active across exactly this file and no further: visuals.py imports several
# of these modules in one process, and a theme left set would silently retint
# whichever section happened to be imported next.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/jwt-clock-drift-iat"] = {
    "flow_intro": (
        "The measurement needs no credential, which is what makes it worth "
        "running before anything is wrong. GitHub states its own clock on "
        "every response, so the samples are unauthenticated, cost no quota "
        "and can run as a startup probe on each host that signs. The "
        "confirming request is optional and it only ever agrees or "
        "disagrees: the number that matters was known before it was sent."
    ),
    "diagram_problem": D.chain(
        "ghskew-p",
        "A JWT refused for a clock nobody thought to look at",
        "Nothing in this chain is a property of the request. The variable is "
        "which machine did the signing, and the request carries no record of "
        "that at all.",
        [
            ("Works on the laptop", "same key, same App"),
            ("401 in the container", "iat named in the message"),
            ("Key redeployed", "the obvious suspect"),
            ("Fails one call in five", "looks like upstream noise"),
            ("Retry loop added", "and the drift keeps growing"),
        ],
        fail_at=1,
        loop=(4, 2, "so the credential is replaced again"),
    ),
    "diagram_fix": D.branch(
        "ghskew-f",
        "Sorting a measured clock offset by direction and by size",
        "Four verdicts from one free header. Two of them are healthy, and the "
        "one that is neither drift nor sync is the one worth naming.",
        ("Date header, timed both ends", "no token, no quota"),
        [
            ("Ahead, past the backdate", "iat lands in GitHub's future", "bad"),
            ("A whole number of hours", "a timezone, not a clock", "bad"),
            ("Behind GitHub", "the JWT arrives part spent", "plain"),
            ("Inside the error bar", "the clocks agree", "good"),
        ],
    ),
}

V["github/jwt-wrong-key-or-algorithm"] = {
    "flow_intro": (
        "One sentence from GitHub covers five causes, so almost all of the "
        "work happens before the request. A PEM is a label, a run of base64 "
        "and an end line, and each of those can be wrong in a way that is "
        "visible locally and safe to print. The single GET adds the one fact "
        "no local check can reach: which App the key turned out to belong to."
    ),
    "diagram_problem": D.chain(
        "ghkey-p",
        "A rotation that removed the key every host was still using",
        "The credential is not corrupt and the App is not missing. Two "
        "correct steps were taken in the wrong order, and the error message "
        "is the same one a mangled PEM produces.",
        [
            ("New key generated", "in the App settings"),
            ("Old key deleted", "tidying up, same afternoon"),
            ("Every host 401s", "could not be decoded"),
            ("PEM pasted around", "checked by eye, looks fine"),
            ("Blamed on the library", "a different one is tried"),
        ],
        fail_at=1,
        loop=(4, 3, "and the key is re-downloaded again"),
    ),
    "diagram_fix": D.branch(
        "ghkey-f",
        "Sorting a key by its PEM shape and by the App that answered",
        "Three of these are settled without a request, and the fourth is the "
        "one that returns 200 and is still wrong.",
        ("Label, lines, fingerprint", "nothing secret in the output"),
        [
            ("Backslash n in the value", "the newlines were escaped", "bad"),
            ("Not an RSA private key", "it cannot sign RS256 at all", "bad"),
            ("Answers as another App", "staging key, production host", "plain"),
            ("Named App, matching key", "the fingerprint is the proof", "good"),
        ],
    ),
}

V["github/installation-token-expired"] = {
    "flow_intro": (
        "One GET against the route only an installation token can answer, and "
        "the rest is arithmetic on timestamps. The useful half runs on a "
        "healthy process: a refresh interval compared against a fixed hour "
        "finds the defect in the afternoon rather than at three in the "
        "morning, and the mint endpoint is a write, so the numbers come from "
        "your own record or from GitHub's stated expiry and the report says "
        "which."
    ),
    "diagram_problem": D.chain(
        "ghitok-p",
        "A long job that outlived the credential it started with",
        "Everything about this shape argues for a leak: sudden, total, and "
        "fixed by a restart. The restart is the repair, applied by accident.",
        [
            ("Token minted at start", "held in a variable"),
            ("Fifty-eight good minutes", "eleven thousand repos"),
            ("Every call 401s at once", "bad credentials, all of them"),
            ("Heap graphs opened", "the restart did fix it"),
            ("Job restarted nightly", "and dies at the same hour"),
        ],
        fail_at=1,
        loop=(4, 3, "so the memory is examined again"),
    ),
    "diagram_fix": D.branch(
        "ghitok-f",
        "Sorting a token by the hour it has left and the timer meant to renew it",
        "Two of these fire on a process that is working perfectly, which is "
        "the only time this is cheap to fix.",
        ("Mint time against the hour", "and the interval against it"),
        [
            ("No refresh at all", "the cliff is at sixty minutes", "bad"),
            ("Timer as long as the hour", "a race, not a refresh", "bad"),
            ("Records disagree", "this is not the token you logged", "plain"),
            ("Renewed at fifty minutes", "ten minutes of margin", "good"),
        ],
    ),
}

V["github/app-not-installed-on-repo"] = {
    "flow_intro": (
        "Three GETs and the first one carries no credential, because whether "
        "the repository is publicly readable is a fact about the world rather "
        "than about your App. The other two are the same presence question "
        "asked at two scopes, and the pair of answers is what splits one "
        "unhelpful 404 into two repairs that involve different people."
    ),
    "diagram_problem": D.chain(
        "ghpres-p",
        "A 404 on a public repository the App was never installed on",
        "Eleven repositories work, so the twelfth looks like the odd one. The "
        "thing that differs is not in the repository's settings.",
        [
            ("New repo created", "the installation is unchanged"),
            ("404 from the App", "on a public repository"),
            ("Repo settings audited", "archived, renamed, private"),
            ("Permissions widened", "installers asked to accept"),
            ("Same 404 returns", "and the next new repo too"),
        ],
        fail_at=1,
        loop=(4, 3, "so a broader grant is tried next"),
    ),
    "diagram_fix": D.branch(
        "ghpres-f",
        "Sorting one repository by presence at repository and account scope",
        "Two different repairs and two different people, from a pair of "
        "status codes that the failing call could never have given you.",
        ("Presence at both scopes", "asked with the App JWT"),
        [
            ("On the account, not here", "add it, or select them all", "bad"),
            ("Not on the account", "somebody has to install it", "bad"),
            ("Newer than the install", "it will happen again next time", "plain"),
            ("Installed on this repo", "the 404 is something else", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
