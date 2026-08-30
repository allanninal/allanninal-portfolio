#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch I.

Four notes that all end at a refusal and get there by four different routes,
so the four problem chains are deliberately about four different objects: a
header that is not the credential, a word in front of the credential, a clock
nobody started, and somebody else's decision on somebody else's afternoon.

The fix branches sort on four different readings too. One sorts a 403 by the
sentence in its body. One sorts a credential by its own prefix, locally, before
anything is sent. One sorts a fleet by how much margin each credential has
against a one year reaping window. One sorts a fleet by how many of its tokens
answered, because a single 401 and a hundred 401s have opposite repairs.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where
nothing downstream will ever catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the file.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this module and no further: visuals.py imports all of
# these in one process, and a theme left set retints whichever section is
# imported next.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/user-agent-missing"] = {
    "flow_intro": (
        "One request, and the half of the answer that matters does not come "
        "back over the wire at all: the client already holds the headers it "
        "sent and can read them off its own request object. So the script "
        "sorts the refusal by the sentence in its body, then grades the "
        "User-Agent it actually put on the wire, and prints a replacement "
        "string that names the application and a way to reach you."
    ),
    "diagram_problem": D.chain(
        "ghua-p",
        "A 403 caused by a missing header rather than by the credential",
        "Every step here is somebody reasonably chasing the word 403, which "
        "in this section means quota or permission four times out of five.",
        [
            ("Raw HTTP client", "no SDK underneath"),
            ("403 on everything", "even the open endpoints"),
            ("Token re-minted", "twice, widely scoped"),
            ("Quota checked", "5000 remaining"),
            ("Body never read", "the rule was in it"),
        ],
        fail_at=0,
        loop=(4, 2, "and the token gets wider again"),
    ),
    "diagram_fix": D.branch(
        "ghua-f",
        "Sorting a 403 by the sentence in its body before anything is rotated",
        "Four of these mean four different repairs and only one of them is on "
        "this page, which is the entire reason the sort happens first.",
        ("One GET, body and headers", "plus what you sent"),
        [
            ("Administrative rules", "no User-Agent, set one and stop", "bad"),
            ("Remaining is zero", "quota, and the reset is a number", "plain"),
            ("Secondary rate limit", "concurrency or write bursts", "plain"),
            ("Header present, request fine", "default agent, name your app", "good"),
        ],
    ),
}

V["github/wrong-authorization-scheme"] = {
    "flow_intro": (
        "The pairing is decided locally. A GitHub credential announces its own "
        "type in its first few characters, and a JWT announces itself by "
        "having three dot separated segments, so the script knows which scheme "
        "word belongs in front of it before it opens a socket. Only the "
        "confirmation goes out: the same path, twice, with the two words."
    ),
    "diagram_problem": D.chain(
        "ghscheme-p",
        "A valid credential refused because of the word in front of it",
        "The credential in this chain is correct at every step. Only the "
        "envelope is wrong, and the message never mentions envelopes.",
        [
            ("JWT minted, signed", "the key is right"),
            ("Sent as token", "copied from a PAT sample"),
            ("401 Bad credentials", "says nothing about schemes"),
            ("Key regenerated", "twice, same result"),
            ("Clock blamed", "then the App itself"),
        ],
        fail_at=1,
        loop=(4, 0, "and the next key is generated"),
    ),
    "diagram_fix": D.branch(
        "ghscheme-f",
        "Pairing the scheme word against the shape of the credential",
        "Three of these four are decided from the credential's own first "
        "characters, with nothing sent and nothing logged.",
        ("Read the shape locally", "prefix or three segments"),
        [
            ("JWT under token", "the one that always fails", "bad"),
            ("No scheme word at all", "a bare value, always refused", "bad"),
            ("PAT under token", "accepted, legacy, move to Bearer", "plain"),
            ("Right word, still 401", "credential, not envelope", "good"),
        ],
    ),
}

V["github/unused-classic-token-auto-revoked"] = {
    "flow_intro": (
        "Nothing is failing when you run this, and the API cannot tell you "
        "when a credential was last used, so the clock has to come from your "
        "own side: how often each job exercises each credential. The script "
        "probes every credential once against a call that costs no quota, "
        "which both answers the question and resets the clock it is measuring."
    ),
    "diagram_problem": D.chain(
        "ghdorm-p",
        "A credential deleted for dormancy on the day it was finally needed",
        "The interval that makes this token valuable is the same interval "
        "that gets it reaped. Nothing warns, because nothing is watching.",
        [
            ("Restore token minted", "no expiry set"),
            ("Filed for emergencies", "used once, at setup"),
            ("Twelve quiet months", "no calls, no header"),
            ("Removed for disuse", "silently, by policy"),
            ("Drill day, 401", "on the worst morning"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "ghdorm-f",
        "Sorting credentials by their margin against a one year reaping window",
        "Margin is exercise interval subtracted from the window, so a yearly "
        "job has none and a weekly one has fifty one weeks of it.",
        ("Probe each credential", "zero quota, and a keep alive"),
        [
            ("Interval at or past a year", "no margin, it will be reaped", "bad"),
            ("Already gone", "401, and nothing to rotate", "bad"),
            ("Under a year, thin margin", "schedule the probe separately", "plain"),
            ("Expiry header present", "different clock, different note", "good"),
        ],
    ),
}

V["github/oauth-token-revoked-by-user"] = {
    "flow_intro": (
        "The reading is a population, not a request. One probe per stored user "
        "token, and the shape of the answers is the diagnosis: one refusal "
        "among many successes is that person, every refusal at once is you. "
        "The script also names the disposition, because a 401 on a stored user "
        "token is terminal and retrying it is how the next limit gets tripped."
    ),
    "diagram_problem": D.chain(
        "ghrvk-p",
        "One user's token dying while every other user of the integration works",
        "The retry loop is the expensive half. A dead token retried on a "
        "schedule is a hundred refusals a day that nothing will ever fix.",
        [
            ("User revokes access", "from their settings"),
            ("No notification", "the app is not told"),
            ("Sync 401s for one", "everyone else is fine"),
            ("Treated as transient", "backoff, then retry"),
            ("Retried for weeks", "until a limit trips"),
        ],
        fail_at=2,
        loop=(4, 3, "and the backoff starts over"),
    ),
    "diagram_fix": D.branch(
        "ghrvk-f",
        "Reading the fleet of stored tokens rather than the failing request",
        "Two of these look identical from inside one request and have "
        "opposite repairs, which is why the probe runs over all of them.",
        ("Probe every stored token", "count, do not retry"),
        [
            ("One dead, others alive", "that person reauthorizes", "bad"),
            ("Every token dead at once", "the app, not the people", "bad"),
            ("Only one token stored", "cannot tell the two apart", "plain"),
            ("All alive", "nothing revoked, look elsewhere", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
