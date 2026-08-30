#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch H.

Four notes about one credential seen from four angles, so the four problem
chains deliberately end in four different places. One ends at a refusal. One
ends at a number of repositories and no refusal at all. One ends at a shape
that keeps working and should not. One ends at a log line, which is the only
one of the four that nothing anywhere reports as an error.

Each fix branch sorts on a different reading: a header pair diffed against
itself, a scope set diffed against a declared job, a base64 payload decoded
locally with no request at all, and a digest that says whether two sightings
are the same secret. Drawn in GitHub blue.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
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

V["github/missing-oauth-scope"] = {
    "flow_intro": (
        "Two requests, and the second one is the call that was already "
        "failing. Everything after that is arithmetic on two header values: "
        "close the held set over the scopes it implies, read the accepted "
        "list as alternatives rather than as requirements, and report the one "
        "that adds the least. The output is a single scope name, which is the "
        "only form of this answer anybody acts on correctly."
    ),
    "diagram_problem": D.chain(
        "ghmscope-p",
        "A token refused by one endpoint while nineteen others work",
        "The one response that names the answer is the one response nobody "
        "keeps, because almost no client logs headers on a failure.",
        [
            ("Token minted fast", "public_repo, read:org"),
            ("Nineteen calls work", "reads look fine"),
            ("Hook list 403s", "prose about admin rights"),
            ("Headers discarded", "the answer was on them"),
            ("Every box ticked", "widest token wins"),
        ],
        fail_at=1,
        loop=(4, 0, "and the next ticket widens it again"),
    ),
    "diagram_fix": D.branch(
        "ghmscope-f",
        "Diffing held scopes against the accepted list on the same response",
        "Held scopes imply narrower ones and the accepted list is a "
        "disjunction, so both sides have to be expanded before they are "
        "subtracted.",
        ("Two headers, one response", "held against accepted"),
        [
            ("Missing, with alternatives", "add the narrowest one, not repo", "bad"),
            ("Accepted list is empty", "any token works, so not scopes", "plain"),
            ("No scope header at all", "permissions model, not scopes", "plain"),
            ("Held already covers it", "look at SSO or installation", "good"),
        ],
    ),
}

V["github/over-scoped-token"] = {
    "flow_intro": (
        "One request, and it is GET /user. Nothing is probed, because a write "
        "probe that succeeds is a write. The report is an inventory rather "
        "than a diff: the verbs this credential authorizes, the repositories "
        "they reach, and the one state that no re-minting of a classic token "
        "can clear."
    ),
    "diagram_problem": D.chain(
        "ghovers-p",
        "A read only job holding write access to every repository",
        "Nothing in this chain errors. The only step that changes anything is "
        "the last one, and it happens on somebody else's afternoon.",
        [
            ("Read only job", "lists pull requests"),
            ("repo ticked once", "the only box that works"),
            ("Green for a year", "nothing to debug"),
            ("Token copied onward", "CI, image, laptop"),
            ("100 repos writable", "on the day it leaks"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "ghovers-f",
        "Sorting held scopes against the reads a job actually declares",
        "Three of these four outcomes come from a system that is working "
        "perfectly, which is why the report has to name verbs rather than "
        "scope names.",
        ("GET /user, one request", "scopes against declared reads"),
        [
            ("Write scopes nothing uses", "delete_repo on a reader", "bad"),
            ("Minimum is still repo", "no classic token is narrower", "bad"),
            ("Unused read scopes", "untidy rather than dangerous", "plain"),
            ("No scope header", "fine grained already, nothing to do", "good"),
        ],
    ),
}

V["github/basic-auth-password-removed"] = {
    "flow_intro": (
        "The useful half of this script makes no request. Base64 is an "
        "encoding, so the client can decode its own header and read the half "
        "after the colon on its own machine. Only the replacement goes on the "
        "wire, and only with a credential from the environment, which "
        "separates a good token in a retired envelope from a bad token in the "
        "right one."
    ),
    "diagram_problem": D.chain(
        "ghbauth-p",
        "A username and password refused by every endpoint at once",
        "The message names the repair and people apply half of it, which is "
        "how a retired shape survives its own migration.",
        [
            ("Basic user:password", "from a 2016 snippet"),
            ("401 on everything", "reads like an outage"),
            ("Token pasted in", "username left in place"),
            ("Basic user:token", "works, so it ships"),
            ("Shape survives", "in netrc and curl -u"),
        ],
        fail_at=0,
        loop=(4, 0, "and the next copy inherits it"),
    ),
    "diagram_fix": D.branch(
        "ghbauth-f",
        "Classifying the authentication scheme before anything is sent",
        "The password case is the one the script refuses to test on the wire. "
        "Sending it buys nothing the header already said and costs a copy in "
        "every log on the way.",
        ("Decode the header locally", "no request at all"),
        [
            ("Password after the colon", "refuse to send, print the header", "bad"),
            ("Token after the colon", "accepted today, wrong shape", "bad"),
            ("Bearer, and still 401", "credential, not mechanism", "plain"),
            ("Bearer, and 200", "envelope and credential both good", "good"),
        ],
    ),
}

V["github/token-in-query-string"] = {
    "flow_intro": (
        "The script audits strings you already have rather than making the "
        "leak again: it never puts a credential in a URL, not even to "
        "reproduce the documented anonymous tier reading. Findings carry a "
        "shape, a length and a truncated digest, so two sightings can be "
        "matched to each other and neither one is another copy of the secret."
    ),
    "diagram_problem": D.chain(
        "ghqstr-p",
        "A credential in a URL copied into every log on the path",
        "The 401 is the small half. The large half is the step before it, "
        "which nothing anywhere reports as an error.",
        [
            ("access_token in URL", "inherited from a sample"),
            ("Parameter ignored", "request goes out anonymous"),
            ("Public reads still work", "private ones 401"),
            ("URL written everywhere", "proxy, CI, history"),
            ("Header fix ships", "the log lines stay"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ghqstr-f",
        "Sorting URLs by whether the credential in them is still usable",
        "Liveness is the only part of this the API can answer, and it answers "
        "it from a header. Everything else is arithmetic on digests.",
        ("Shape, digest, location", "never the value"),
        [
            ("Matches the live token", "revoke first, then scrub", "bad"),
            ("Credential nobody claims", "assume live until proven", "bad"),
            ("Matches a dead token", "historical, habit is not", "plain"),
            ("Nothing credential shaped", "the URLs are clean", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
