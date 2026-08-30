#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch Z.

Four Enterprise Grid notes, and four pictures that are pinned to the object
each note is about rather than to the error string, because three of these four
share an error vocabulary and a diagram of an error string would be four copies
of the same image.

The first fails between two things that both worked. The install was approved
correctly and the grant genuinely covers forty workspaces; the red arrow sits
where a workspace asks the store a question and the store has an organization
where a workspace was expected. Nothing is called after that, which is why
there is no error to catch.

The second fails on the call itself, and it fails for exactly one customer out
of two hundred. Its red arrow is early because the refusal arrives on the first
attempt and never moves. The three boxes after it are the week that gets spent
adding scopes to a method that will not accept any.

The third fails nowhere in Slack at all. Slack announces the migration, keeps
announcing it, and finishes it. The red arrow is between the failure count
climbing and the housekeeping agreeing, which is a line of your own code
deleting a customer who was in the middle of becoming an Enterprise account.

The fourth fails two days after everything recovered. Its red arrow is the
third, the latest in the batch, because the outage ended, the app came back,
and the identifiers underneath it are the part nobody re-read.

The branches sort four different populations: workspaces, methods,
installations and identifiers. Drawn in Slack aubergine. No em dashes inside
SVG text: one mis-sniffed encoding turns a single character into three mojibake
ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the
# module. Every diagram here is constructed at import time, so the theme has to
# be active across exactly this file and no further.
BRAND = "#4A154B"
D.set_theme(BRAND)

V = {}

V["slack/org-wide-install-mishandled"] = {
    "flow_intro": (
        "The red arrow is the third, and everything to the left of it is "
        "correct. An org owner approved the app at the organization level, "
        "Slack minted a grant that genuinely covers every workspace in the "
        "organization, and the OAuth response said as much by returning a "
        "null where a workspace would normally be. The failure is the box the "
        "arrow points at, which is your own store being asked for a workspace "
        "and holding an organization, and the thing to notice about it is "
        "that no call is made afterwards. There is no error string on this "
        "wire because nothing ever reached the wire. The fix branch sorts "
        "workspaces rather than errors, one resolution each, and its most "
        "important row is the third: a row that matches on workspace id but "
        "belongs to a different organization must be refused rather than "
        "used, because using it is the cross tenant case."
    ),
    "diagram_problem": D.chain(
        "skorgwi-p",
        "One installation row asked to answer for forty workspaces",
        "The install was approved correctly and the grant covers everything. "
        "The lookup is what has one workspace in mind, and a lookup that "
        "returns nothing makes no call and raises no error.",
        [
            ("Approved at the org", "one grant, forty workspaces"),
            ("The row is written", "under one workspace id"),
            ("A sibling workspace asks", "carrying its own team_id"),
            ("The store answers nothing", "and no call is made"),
            ("Thirty-nine more", "the same, every day"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skorgwi-f",
        "Every workspace in the organization resolved twice, with and without the fallback",
        "Two runs of the same lookup over the same rows. The difference "
        "between the two coverage figures is the whole of the bug, and it is "
        "measured against an enumerated organization rather than a guess.",
        ("Each workspace, resolved twice", "with the fallback, and without"),
        [
            ("Misses with no fallback", "thirty-nine of forty", "bad"),
            ("team_id kept as a string", "written one key, read another", "bad"),
            ("Same team, another org", "refused, and never resolved", "plain"),
            ("No flag either way", "unstated, which is not false", "plain"),
            ("The org row answers", "one row, forty workspaces", "good"),
        ],
    ),
}

V["slack/enterprise-is-restricted"] = {
    "flow_intro": (
        "The red arrow is the second, which is early, and that is the point: "
        "the refusal arrives on the first attempt and never moves. What "
        "follows it is not an outage, it is a week. The natural reading of a "
        "refusal is that something is missing, so scopes get added, an "
        "install gets repeated, an org owner gets asked to try it themselves, "
        "and none of it changes anything, because the refusal is attached to "
        "the method rather than to the credential or the person. The fix "
        "branch sorts methods, and it exists mostly to keep four different "
        "Grid refusals apart. Only the first row is this note. The fourth is "
        "the read only rule: a write in your call list is named and mapped "
        "and never issued, because the only way to ask a write method whether "
        "it is barred is to perform it in somebody else's organization."
    ),
    "diagram_problem": D.chain(
        "skenres-p",
        "A method that answers everywhere except at the one Enterprise customer",
        "The same call and the same code that serve two hundred workspaces. "
        "The refusal is attached to the method, so no scope, no role and no "
        "reinstall moves it.",
        [
            ("Two hundred customers", "and one of them on Grid"),
            ("The same call, same code", "nothing about it changed"),
            ("enterprise_is_restricted", "the method, not the token"),
            ("Scopes get added", "and nothing changes"),
            ("The evaluation ends", "with the work still owed"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skenres-f",
        "Each method in the call list sorted by which refusal it produces",
        "Four Grid refusals arrive in the same field and only one of them is "
        "this problem. Sorting them is most of the work, because three of the "
        "four are repaired by something other than a substitution.",
        ("Each method you call, probed once", "reads only, one at a time"),
        [
            ("Barred on the Enterprise", "the method, for everyone", "bad"),
            ("Outside the workspace", "a boundary, not a bar", "bad"),
            ("Mid migration", "it will answer later", "plain"),
            ("A write in the list", "named, mapped, never called", "plain"),
            ("Answers ok true", "for this token, today", "good"),
        ],
    ),
}

V["slack/org-login-required"] = {
    "flow_intro": (
        "The red arrow is the third, and nothing in Slack is on the wrong "
        "side of it. The workspace is migrating, Slack says so on every "
        "response, and the migration will finish. The box the arrow points at "
        "is a piece of your own housekeeping doing exactly what it was "
        "written to do, which is remove installations that have failed "
        "continuously for long enough, and the input it is reading cannot "
        "distinguish a customer who has left from a customer who is "
        "unreachable for the afternoon. The fix branch sorts installations "
        "into dispositions rather than into states, because a state gets "
        "translated into an action by whoever is on call and they will "
        "translate it differently each time. The third row is the boundary "
        "the whole note is about: two errors retire a row, and no length of "
        "outage adds a third."
    ),
    "diagram_problem": D.chain(
        "skmighold-p",
        "A migration that Slack handled correctly and a cleanup that did not",
        "Every box here is somebody doing their job. The customer migrates, "
        "Slack reports it, the jobs fail honestly, and the housekeeping "
        "removes a row that has failed for two days.",
        [
            ("The workspace migrates", "and Slack says so plainly"),
            ("Every job fails", "for that one customer"),
            ("The failure count climbs", "hour after hour"),
            ("The cleanup agrees", "and removes the row"),
            ("The migration completes", "and nobody is there"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skmighold-f",
        "Every failing installation given one disposition rather than one state",
        "A state is not an instruction. Each installation gets the word the "
        "scheduler acts on, and the default is to keep the row, because the "
        "expensive mistake here is deleting a customer rather than holding a "
        "dead one an extra week.",
        ("Each installation, one auth.test", "a disposition, not a state"),
        [
            ("Migrating", "hold: suspend, do not fail", "bad"),
            ("Held past three days", "a person looks; still no delete", "bad"),
            ("The grant has ended", "retire, and only for these two", "plain"),
            ("Rate limited mid sweep", "retry; nothing is wrong", "plain"),
            ("Answers ok true", "serve, and it is a customer", "good"),
        ],
    ),
}

V["slack/team-added-to-org"] = {
    "flow_intro": (
        "The red arrow is the third, which is the latest in this batch, and "
        "the delay is the whole character of the failure. The migration ended "
        "on the Saturday. The app recovered by itself, which is what everyone "
        "hoped for and also what stops anybody looking further. Two days "
        "later a cached identifier is used the way it has been used for a "
        "year, and the id is not malformed, not expired and not revoked. It "
        "is historical. The last box is the one worth sitting with, because a "
        "stale id that fails is a bug and a stale id that resolves to "
        "somebody else is an incident. The fix branch sorts identifiers "
        "against one map, and its middle row is the discipline: an id that "
        "came back in neither list is unresolved, and calling it unchanged is "
        "how a cache audit reports clean while leaving rows unaccounted for."
    ),
    "diagram_problem": D.chain(
        "skidremap-p",
        "Cached user identifiers that the migration superseded two days ago",
        "The outage was the visible half and it ended. The half that costs "
        "you Monday is an identifier that is still well formed, still in your "
        "database, and no longer the one Slack uses.",
        [
            ("The migration ends", "and the app recovers itself"),
            ("Everything works", "for two whole days"),
            ("A cached id is used", "exactly as it always was"),
            ("user_not_found", "for an id that resolved"),
            ("Or worse, it resolves", "to a different person"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skidremap-f",
        "Every cached identifier held against one map from migration.exchange",
        "One method answers this and nothing else does. The map is read in "
        "batches of four hundred, and an identifier it does not account for "
        "is counted separately rather than assumed to be fine.",
        ("Each cached id, against the map", "batched by four hundred"),
        [
            ("Maps to a W id", "the row points at nothing", "bad"),
            ("In invalid_user_ids", "not recognised at all", "bad"),
            ("In neither list", "unresolved, not unchanged", "plain"),
            ("Only a Slack id stored", "nothing to re-resolve from", "plain"),
            ("Maps to itself", "nothing keyed on it moved", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
