#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch P.

Org topology: the shape of the organization rather than the credentials inside
it. Three of the four problem chains end in a container that does not exist, and
the fourth ends in a grant that was offered and never collected. None of them
contains an error, and two of them contain a step that was the correct decision
at the time, which is why they survive: nobody is ever going to go back and undo
a promotion that unblocked a colleague or a default that shipped the first
request.

The fix branches are all classifiers, and two of them have an outcome whose
whole job is to hand the reading back. A dominant project in an org that has
nine projects is a concentration finding and belongs to another note. A null
workspace bucket that is mostly Console playground has no key migration in it at
all. Drawing those as ordinary outcomes rather than as failures is the point:
the script's value is as much in what it declines to claim as in what it finds.

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

V["llm/no-prod-dev-project-separation"] = {
    "flow_intro": (
        "Nothing in this chain is a mistake at the moment it happens. The "
        "default project is created for you and serves the first request, "
        "which is a good onboarding decision, and every environment that "
        "arrives afterwards arrives one key at a time. The count of containers "
        "is the reading, not the size of the bill: a share of total needs "
        "something to compare against, and a single project is a hundred per "
        "cent of everything by construction."
    ),
    "diagram_problem": D.chain(
        "llmtopo-p",
        "How every environment ends up inside one project nobody chose",
        "No step here is wrong on its own. The structural decision gets made "
        "by never being made, at the point where nobody knows the answer yet.",
        [
            ("Default project, first request", "it just works"),
            ("CI, laptops, evals", "each arrives as one more key"),
            ("Customer traffic joins them", "same container, same limits"),
            ("A cap would cap production", "so nobody sets one"),
            ("One number, no owner", "and nothing left to enforce"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmtopo-f",
        "Sorting an organization by how many active projects it actually has",
        "The container count is read before any money. Concentration inside a "
        "real boundary is a different question and goes back to another note.",
        ("Active projects", "then cost by project_id"),
        [
            ("Exactly one active", "nothing to cap or attribute", "bad"),
            ("Others exist, all at zero", "the routing, not the boundary", "bad"),
            ("One dominant of nine", "read it as concentration", "plain"),
            ("Ungrouped null rows", "not a project at all", "plain"),
            ("Spend across several", "controls can differ", "good"),
        ],
    ),
}

V["llm/default-workspace-cost-unattributable"] = {
    "flow_intro": (
        "One unallocated row on a chargeback report, and two entirely "
        "different causes underneath it. Keys that land in the default "
        "workspace have names and ids and can be replaced inside a named one. "
        "Console playground requests carry no key at all, so no migration "
        "touches them. Reporting the bucket as a single number promises a fix "
        "that only works on part of it."
    ),
    "diagram_problem": D.chain(
        "llmnullws-p",
        "How the default workspace becomes the biggest line nobody owns",
        "The default workspace is the path of least resistance and nothing "
        "ever pushes back on it, including the rate limiter.",
        [
            ("A key made in a hurry", "no workspace chosen"),
            ("Org scoped keys join it", "never bound to one"),
            ("Cost reports workspace null", "no id exists to report"),
            ("Chargeback bucket grows", "carried forward each month"),
            ("No override possible here", "unbounded against the org limit"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmnullws-f",
        "Splitting the null cost bucket into the half that moves and the half that does not",
        "Only one branch has a migration in it. The script sizes both before "
        "it recommends any work at all.",
        ("Null workspace share", "split by api_key_id"),
        [
            ("Keys in the default space", "recreate in a named one", "bad"),
            ("Organization scoped keys", "no workspace to move to", "bad"),
            ("Mostly playground usage", "no key to move anywhere", "plain"),
            ("Every key already named", "the spender is already gone", "plain"),
            ("Null share under threshold", "chargeback adds up", "good"),
        ],
    ),
}

V["llm/too-many-organization-owners"] = {
    "flow_intro": (
        "Two roles, no middle, and one direction of travel. Every unblock in "
        "the history of the organization is recorded as a promotion, and "
        "nothing anywhere asks for a demotion, so the distinction erodes "
        "quietly until a configuration change has fourteen candidate authors. "
        "The reading has to remove service accounts first, because they are on "
        "the same roster and are frequently owners by design."
    ),
    "diagram_problem": D.chain(
        "llmowners-p",
        "How the owner role becomes the default rather than the exception",
        "Every promotion in this chain was the right call that afternoon. "
        "None of them was ever the wrong call later, which is the problem.",
        [
            ("Reader cannot do the task", "and there is no middle role"),
            ("Promote to unblock", "correct, and quick"),
            ("Nothing reviews it after", "demotion has a social cost"),
            ("Owners can mint admin keys", "org wide, long lived"),
            ("A change has no author", "everyone could have made it"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmowners-f",
        "Sorting the roster by role once the service accounts are removed",
        "The member floor comes first. Two owners in a three person company is "
        "a company, and grading it teaches people to ignore the report.",
        ("Human members only", "owner against reader"),
        [
            ("Nearly all are owners", "the distinction is gone", "bad"),
            ("Owners in the majority", "demote, grant per project", "bad"),
            ("SCIM managed owners", "fix the group mapping", "plain"),
            ("Owner, no key use ever", "a question, not a verdict", "plain"),
            ("A few named owners", "a change has an author", "good"),
        ],
    ),
}

V["llm/openai-invites-pending-past-expiry"] = {
    "flow_intro": (
        "The sender's half of this finishes the moment the invite goes out, "
        "because sending it was the ticket. The recipient's half happens in a "
        "mailbox nobody else can see. What connects them is a record whose "
        "status field and whose clock disagree, which is also the only reason "
        "a script can find it: the row still reads pending long after its "
        "expiry passed, so a status filter never returns it."
    ),
    "diagram_problem": D.chain(
        "llminvite-p",
        "An invite that lapsed, and the borrowed key that replaced it",
        "Nothing chases the recipient and nothing tells the sender. The work "
        "still gets done, under somebody else's identity.",
        [
            ("Invite sent, ticket closed", "sending it was the task"),
            ("Filtered, or misread", "no delivery status exists"),
            ("Expiry passes quietly", "no notice either way"),
            ("A colleague lends a key", "the work was still due"),
            ("Status still reads pending", "and owner grants sit unclaimed"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llminvite-f",
        "Sorting invites by the clock rather than by the status string",
        "expires_at is compared against now before status is compared against "
        "a word, because that ordering is what surfaces the lapsed rows.",
        ("Every invite", "expires_at against now"),
        [
            ("Pending, expiry passed", "the row a filter misses", "bad"),
            ("Owner grant outstanding", "read this one first", "bad"),
            ("Pending, already a member", "a record, not a failure", "plain"),
            ("Expired and uncollected", "a backlog to clear", "plain"),
            ("Sent recently, still live", "nothing to do yet", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
