#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch L.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Twilio red.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#F22F46"
D.set_theme(BRAND)

V = {}

V["twilio/studio-flow-draft-not-published"] = {
    "flow_intro": (
        "The classifier keys on status rather than on the canvas, because the "
        "canvas is the draft and the runtime is the last published revision. "
        "Which of those two a caller hears is not a field you can read back."
    ),
    "diagram_problem": D.chain(
        "tsdr-p",
        "An edited Studio Flow that works for one handset and nobody else",
        "Nothing failed. The Console shows the new definition, the runtime keeps "
        "serving the old one, and the only person who sees the change is the "
        "person on the TEST USERS list.",
        [
            ("Widget edited", "greeting rewritten"),
            ("Saved", "revision goes up"),
            ("Never published", "no Publish pressed"),
            ("Tested from a test user", "the draft answers"),
            ("Callers hear the old flow", "for as long as it takes"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tsdr-f",
        "Sorting Studio Flows by whether the definition on screen is the live one",
        "A draft with executions is an outage; a draft with none is somebody's "
        "unfinished work. An invalid definition cannot be published at all, so it "
        "never gets told to press Publish.",
        ("GET /v2/Flows and its Executions", "status, revision, valid"),
        [
            ("Published", "the canvas is the runtime", "good"),
            ("Draft, no executions", "edits live nowhere yet", "plain"),
            ("Draft, taking traffic", "callers run an older revision", "bad"),
            ("valid is false", "publishing will not work", "bad"),
        ],
    ),
}

V["twilio/studio-flow-not-wired-to-number"] = {
    "flow_intro": (
        "Attachment is a URL on the number, not a reference to the Flow, so the "
        "check is a substring match on the FlowSid. Executions are the second "
        "opinion: a Flow can be reached from places the number list cannot see."
    ),
    "diagram_problem": D.chain(
        "tswn-p",
        "A finished Flow with an empty Executions tab and no entry point",
        "Publishing tells Studio the definition is live. It does not tell a "
        "single phone number to send anything to it, and both halves look "
        "correct on their own pages.",
        [
            ("Flow built", "reviewed and approved"),
            ("Flow published", "definition is live"),
            ("Number untouched", "sms_url unchanged"),
            ("Inbound hits the old URL", "or the demo TwiML"),
            ("Zero executions", "no error anywhere"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tswn-f",
        "Sorting published Flows by whether anything can actually reach them",
        "Executions with no number is not an orphan: the REST API, a Trigger "
        "widget or a Messaging Service can start a Flow. Calling that broken is "
        "how a report stops being read.",
        ("Flows against IncomingPhoneNumbers", "FlowSid inside voice_url or sms_url"),
        [
            ("Number attached, running", "wired", "good"),
            ("Executions, no number", "triggered from elsewhere", "good"),
            ("Attached, never run", "wired and untested", "plain"),
            ("No number, no executions", "nothing can reach it", "bad"),
        ],
    ),
}

V["twilio/conversations-webhook-url-missing"] = {
    "flow_intro": (
        "The target field decides whether a URL is required at all. A Studio "
        "target routes to a flow_sid and correctly has none, which is the one "
        "false positive that would make this report unreadable."
    ),
    "diagram_problem": D.chain(
        "tcwu-p",
        "A conversation webhook that raises 50369 on every single event",
        "The conversation is perfect. Participants send messages, the transcript "
        "is complete, and the application is never told any of it happened.",
        [
            ("Webhook created", "URL left empty"),
            ("Attached to the conversation", "target is webhook"),
            ("Message added", "the event matches"),
            ("Nowhere to deliver", "error 50369"),
            ("App never hears", "alerts pile up unread"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "tcwu-f",
        "Sorting conversation-scoped webhooks by whether they can deliver",
        "One broken webhook on a busy conversation raises hundreds of alerts, so "
        "the finding is the conversation, not the alert. Deduplicate before "
        "looking anything up.",
        ("Alerts 50369, then the Webhooks list", "target and configuration.url"),
        [
            ("Target webhook, https URL", "delivering", "good"),
            ("Target studio, flow_sid set", "no URL is required", "good"),
            ("Plain http URL", "message bodies in the clear", "plain"),
            ("Target webhook, no URL", "50369 on every event", "bad"),
        ],
    ),
}

V["twilio/event-streams-sink-failed"] = {
    "flow_intro": (
        "Sinks and subscriptions are separate resources joined only by sink_sid, "
        "and that join is the diagnosis. The same failed status means an outage "
        "or a dead resource depending on what is pointed at it."
    ),
    "diagram_problem": D.chain(
        "tesf-p",
        "A sink marked failed while every message and call carries on normally",
        "A table that stops growing looks exactly like a table nobody wrote to, "
        "and a dashboard on top of it draws a flat line rather than an error.",
        [
            ("Destination stalls", "past the delivery timeout"),
            ("Sink marked failed", "delivery stops"),
            ("Messaging unchanged", "calls and sends fine"),
            ("Warehouse stops filling", "no rows, no errors"),
            ("Found weeks later", "a chart ending on a Tuesday"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tesf-f",
        "Sorting Event Streams sinks by what is actually flowing through them",
        "Fixing the endpoint does not un-fail the sink. It has to be validated "
        "again and the subscriptions re-attached, so an active sink with nothing "
        "subscribed is the state people create while repairing this.",
        ("GET /v1/Sinks and /v1/Subscriptions", "status joined on sink_sid"),
        [
            ("Active, subscriptions attached", "delivering", "good"),
            ("Failed, nothing attached", "litter, not an outage", "plain"),
            ("Active, nothing attached", "green and carrying no events", "bad"),
            ("Failed, subscriptions attached", "events dropped since it broke", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
