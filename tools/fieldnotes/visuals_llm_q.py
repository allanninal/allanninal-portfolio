#!/usr/bin/env python3
"""Diagrams for the /llm/ field notes, batch Q.

Controls everyone assumes are on. The four problem chains share a shape that
none of the earlier batches has: there is no failing step in them at all. Every
box is somebody doing a reasonable thing, and the fault is that a second step
which was never scheduled did not happen. So the red arrow in each chain lands
on the moment a claim starts being made about a control that was never
finished, rather than on an error, because that is genuinely where these go
wrong.

The fix branches are classifiers with an unusual amount of grey in them. Two of
the four have an outcome whose entire job is to refuse a conclusion: a hosted
tool with no usage endpoint cannot be called unused, and a key config attached
to something the admin key cannot enumerate must not be called orphaned. Those
are drawn plain rather than bad, because they are answers, not failures.

Drawn in teal, matching the rest of the section. No em dashes inside SVG text:
one mis-sniffed encoding turns a single character into three mojibake ones
inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further.
BRAND = "#0D9488"
D.set_theme(BRAND)

V = {}

V["llm/moderation-never-called"] = {
    "flow_intro": (
        "Nothing in this chain raises an error, and the middle of it is the "
        "reason: the model refuses most of what it should refuse on its own, "
        "so the absence of a screening step looks like a working screening "
        "step for as long as nothing arrives that needed one. The endpoint "
        "that would have caught it is free, opt in, and reachable only by "
        "code somebody has to write on purpose."
    ),
    "diagram_problem": D.chain(
        "llmmodz-p",
        "How a public product ends up with no moderation call in it at all",
        "Every step here is a reasonable decision made with the information "
        "available at the time. The gap only becomes visible from outside.",
        [
            ("Public input ships", "the form works"),
            ("Model refuses most of it", "looks like screening"),
            ("No separate call written", "nothing prompts one"),
            ("Uploads added later", "the surface doubles"),
            ("A ticket with a screenshot", "and no record of any check"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmmodz-f",
        "Reading two usage reports to find out what was actually screened",
        "The model id is read before any count, because a project moderating "
        "everything through a retired id looks healthy in a ratio.",
        ("Two usage reports", "moderations against completions"),
        [
            ("No moderation at all", "on real public traffic", "bad"),
            ("All on text-moderation", "retired, and text only", "bad"),
            ("Thin ratio", "a hint, not a verdict", "plain"),
            ("Under the volume floor", "somebody's laptop", "plain"),
            ("Current id, real volume", "and a per category log", "good"),
        ],
    ),
}

V["llm/zero-data-retention-not-configured"] = {
    "flow_intro": (
        "The claim and the configuration are made in different systems by "
        "different people two years apart, and nothing connects them. A "
        "project created after the contract takes whatever the organization "
        "default happens to be that morning, and no header, field or log line "
        "on the inference path ever mentions retention, so the only way the "
        "drift surfaces is if somebody goes and asks the admin endpoint."
    ),
    "diagram_problem": D.chain(
        "llmzdr-p",
        "How a retention claim stops matching the project it was made about",
        "The sentence in the questionnaire was true of the organization on the "
        "day it was written. It was never a property of the project.",
        [
            ("Retention negotiated", "at the account level"),
            ("Answer written down", "in a document, not a system"),
            ("New projects created", "each takes the default"),
            ("Nothing on the request path", "no header, no field"),
            ("The claim outlives the setting", "and nobody re-reads it"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "llmzdr-f",
        "Resolving each project against the organization default",
        "Inherited and compliant is a third answer with its own sentence. It "
        "is correct today and pinned to nothing.",
        ("Org default", "then each project type"),
        [
            ("type is none", "no control at all", "bad"),
            ("Weaker than claimed", "whether set or inherited", "bad"),
            ("Inherited, not pinned", "moves with the org", "plain"),
            ("Unrecognised value", "never graded as safe", "plain"),
            ("Pinned on the project", "and the residency matches", "good"),
        ],
    ),
}

V["llm/project-model-permissions-unrestricted"] = {
    "flow_intro": (
        "The question at the end of the postmortem is not why somebody picked "
        "the expensive model. It is what would have stopped them, and the "
        "answer is a policy object that is opt in, per project, and does not "
        "inherit. The middle of this chain is the state worth naming: an empty "
        "deny list, which permits everything and looks configured to anyone "
        "who opens the console."
    ),
    "diagram_problem": D.chain(
        "llmmperm-p",
        "How every project keeps reaching every model in the catalogue",
        "A control that has to be applied per project, by hand, at creation "
        "time, is a control that covers the projects that existed that week.",
        [
            ("Access open by default", "every model, every project"),
            ("Policy written once", "for the projects that exist"),
            ("Deny list left empty", "opened, never finished"),
            ("New project, no policy", "nothing inherits"),
            ("Nothing would have stopped it", "and nothing did"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmmperm-f",
        "Sorting projects by whether their policy has ever excluded anything",
        "Two of these permit exactly the same set of models. They are still "
        "two findings, because only one of them looks configured.",
        ("Policy object", "against models observed"),
        [
            ("Deny list, empty", "looks done, permits all", "bad"),
            ("No policy at all", "never touched", "bad"),
            ("Allow list far too wide", "trim to what is used", "plain"),
            ("Deny list with entries", "open to whatever ships", "plain"),
            ("Allow list matches use", "and tools that are used", "good"),
        ],
    ),
}

V["llm/external-key-config-unattached"] = {
    "flow_intro": (
        "Creating a key config and attaching it are two steps, and only the "
        "second one encrypts anything. The first is the visible one, with the "
        "KMS work and the ARN and the colleague from the platform team, so it "
        "is the one that gets remembered as the task. An unattached config "
        "does not fail. It sits in the listing looking exactly like a config "
        "that is protecting something."
    ),
    "diagram_problem": D.chain(
        "llmcmek-p",
        "How a customer managed key ends up encrypting nothing at all",
        "No request fails, no report mentions encryption, and the claim lives "
        "in a document that has no way to check itself.",
        [
            ("Key created in KMS", "the hard part, done"),
            ("Config registered", "and it looks right"),
            ("Attach step not scheduled", "a field on a workspace"),
            ("Questionnaire answered", "from the config existing"),
            ("Config sits inert", "in no encryption path"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "llmcmek-f",
        "Reconciling the key configs against the workspaces that name them",
        "Only one branch here prints a delete. Two of the others look equally "
        "abandoned and are holding data that cannot be recovered without them.",
        ("attachment.type", "against external_key_id"),
        [
            ("Unattached, unused", "inert, safe to delete", "bad"),
            ("Geo does not match", "and cannot be re-pointed", "bad"),
            ("Unattached, yet named", "the listings disagree", "plain"),
            ("Archived workspaces only", "deleting destroys data", "plain"),
            ("Attached, geo agrees", "and coverage is known", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
