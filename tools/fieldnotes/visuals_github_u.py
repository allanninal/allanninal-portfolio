#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch U.

Four notes about a write being refused, and none of the four is about the
credential, so the branches all sort something other than a token. That is the
constraint this batch is drawn against: the section already has several fans of
scopes and permissions, and a fifth would be indistinguishable at a glance.

The first sorts answers to one question by whether they are answers at all. Its
chain is a compliance sweep that converts a refusal into a zero, and its branch
has a row that is deliberately not a verdict, because the whole note is about
keeping the unknown row unknown.

The second sorts a repository by two booleans. Its chain is seven months of
blaming a credential for a state that no credential touches, and its branch is
the only one in the batch whose rows are all about one object read once.

The third sorts a repository by whether it may enter a total. Its chain ends in
a report that looks right, which is why the loop goes back to the sweep rather
than to the failure, and its branch keeps an empty repository next to a disabled
one because from a distance they are the same shape.

The fourth sorts a line of build-log text by which credential it blames. Its
chain is an SSH investigation into a connection that worked perfectly, and three
of the four rows in its branch send the reader somewhere other than the keys.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where nothing
downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/branch-protection-requires-admin"] = {
    "flow_intro": (
        "Three readings per branch and only one of them can be refused. The "
        "boolean on the branch object and the ruleset rules for the branch are "
        "both published to anyone who can read the repository, so a run with a "
        "read-only token still resolves coverage and often still resolves the "
        "rules; it is the classic protection object that needs admin. "
        "Everything after the three reads is pure: which of the three answers "
        "arrived, what the rules refuse a push for, and a summary that carries "
        "an unknown column so that a gap in the instrument can never be added "
        "to the pile of findings about the estate."
    ),
    "diagram_problem": D.chain(
        "ghbprot-p",
        "A compliance sweep that turns an admin refusal into a coverage zero",
        "Nothing in this run is a lie. The one non-200 that meant nothing "
        "about the branch was read as though it meant everything.",
        [
            ("Sweep of 212 repos", "read-only auditor token"),
            ("403 on protection", "must have admin rights"),
            ("Caught as unprotected", "one except block"),
            ("Report says 0 of 212", "and it is believed"),
            ("Three checked by hand", "all three are protected"),
        ],
        fail_at=1,
        loop=(4, 2, "and the script is loosened instead"),
    ),
    "diagram_fix": D.branch(
        "ghbprot-f",
        "Sorting one branch by which of the three possible answers arrived",
        "The top row is the one that broke the report. It stays unresolved on "
        "purpose, because converting it into a no is the whole failure.",
        ("One branch, three reads", "boolean, rules, ruleset"),
        [
            ("403 admin rights required", "unknown, and never an absence", "plain"),
            ("404 Branch not protected", "the one 404 that means absent", "bad"),
            ("200 with the rule object", "refusals quoted from settings", "good"),
            ("Ruleset rules for the ref", "readable with no admin at all", "good"),
        ],
    ),
}

V["github/repo-archived-writes-403"] = {
    "flow_intro": (
        "The detection is one field, so the script is mostly about what to do "
        "with it. One read per repository, or one per hundred across an "
        "organisation, gives archived and disabled for everything the write "
        "loop was about to touch. The classification afterwards turns those two "
        "booleans into the output a client actually needs, which is a policy "
        "rather than a status code: permanent skip or retry. Beside it sits "
        "arithmetic that converts a retry rate into requests an hour and a "
        "share of the quota, and an attribution of a 403 you already recorded, "
        "done from its message rather than by sending it again."
    ),
    "diagram_problem": D.chain(
        "gharch-p",
        "Seven months of widening a token against a state no token can change",
        "Every read succeeds throughout. A resource that answers every "
        "question except one looks exactly like a permissions problem.",
        [
            ("Bot writes twice a day", "one label per issue"),
            ("403 on every write", "reads all still fine"),
            ("Token widened twice", "scopes, then an App"),
            ("Still 403, since March", "nothing changed at all"),
            ("Retried on a schedule", "864 requests a day"),
        ],
        fail_at=1,
        loop=(4, 2, "and the credential is blamed again"),
    ),
    "diagram_fix": D.branch(
        "gharch-f",
        "Sorting a repository by the two lifecycle booleans it publishes",
        "One read, two booleans, four answers. Only the last one leaves the "
        "credential as a suspect.",
        ("One repository object", "archived and disabled, read once"),
        [
            ("archived true", "permanent skip, never a retry", "bad"),
            ("disabled true", "a different note and a different owner", "plain"),
            ("Both true", "unarchiving alone changes nothing", "bad"),
            ("Neither", "the refusal is about something else", "good"),
        ],
    ),
}

V["github/repo-disabled"] = {
    "flow_intro": (
        "One read settles it and four cheap probes make the evidence legible. "
        "The boolean is the finding; the probes exist because the symptoms "
        "arrived as a scatter of unrelated 404s and empty lists, and seeing "
        "them explained line by line is what makes the state recognisable next "
        "time. Two shortcuts are refused on purpose: a 409 is an empty "
        "repository rather than a ghost, and a failure on a repository that is "
        "not disabled is handed to the credential triage rather than absorbed. "
        "The output that matters is the last one, which decides whether a row "
        "may enter a total at all."
    ),
    "diagram_problem": D.chain(
        "ghdisab-p",
        "A repository present enough to count and absent enough to hold nothing",
        "Each symptom on its own is something a healthy repository does. The "
        "aggregate at the bottom moves by half a per cent and looks right.",
        [
            ("Org sweep of 212 repos", "one row reads oddly"),
            ("Branches and commits 404", "languages answers fine"),
            ("Blamed on the token", "widened twice, no change"),
            ("Counted as zero", "hooks, checks, reviews"),
            ("Coverage looks healthy", "and is quietly wrong"),
        ],
        fail_at=1,
        loop=(4, 0, "and next week it is zero again"),
    ),
    "diagram_fix": D.branch(
        "ghdisab-f",
        "Sorting a repository by whether its numbers may enter an aggregate",
        "The second row is the false positive worth avoiding. A repository "
        "made ten minutes ago looks like a ghost from a distance.",
        ("Each repository, classified", "before it enters a total"),
        [
            ("disabled true", "exclude: the zeroes are artefacts", "bad"),
            ("409 on commits", "an empty repository, not a ghost", "plain"),
            ("archived true", "fully readable, so the values are real", "good"),
            ("Active and answering", "counts, and a zero is a zero", "good"),
        ],
    ),
}

V["github/deploy-key-read-only-assumed-write"] = {
    "flow_intro": (
        "The text classifier runs before the network call, because three of "
        "its four outcomes send the reader somewhere other than the deploy "
        "keys: a ref that refused the update, a repository that is archived, "
        "or a key that was never accepted in the first place. Only then does "
        "the one request go out, and the listing is reduced to metadata in a "
        "single place so that nothing downstream can put key material in a log "
        "or a JSON artefact. The verdict is a comparison between a boolean the "
        "API declares and one fact the API cannot know, which is whether the "
        "job on this repository pushes."
    ),
    "diagram_problem": D.chain(
        "ghdkro-p",
        "An SSH investigation into a connection that authenticated perfectly",
        "The key was accepted and then the operation was declined. "
        "Authentication worked; authorisation is what did not.",
        [
            ("Clone works for months", "fetch twice a day"),
            ("Push step added", "a version bump back"),
            ("Marked as read only", "from git, with no status"),
            ("Agent and host key read", "both entirely fine"),
            ("Token widened anyway", "not the credential in use"),
        ],
        fail_at=1,
        loop=(4, 3, "and the wrong credential again"),
    ),
    "diagram_fix": D.branch(
        "ghdkro-f",
        "Sorting a git refusal by which credential the message actually blames",
        "Three of these four rows are somebody else's note. Only the top one "
        "is answered by the field on the key.",
        ("One error line, then one read", "keys listed, material dropped"),
        [
            ("Marked as read only", "declared on the key object itself", "bad"),
            ("Protected branch declined", "the ref refused, not the key", "plain"),
            ("Permission denied publickey", "authentication, a different problem", "plain"),
            ("A write capable key exists", "read only is not what refused", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
