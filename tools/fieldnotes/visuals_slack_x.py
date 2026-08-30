#!/usr/bin/env python3
"""Diagrams for the /slack/ field notes, batch X.

Three of these four are about incoming webhooks, which is a genuine hazard for
a set of pictures: draw them carelessly and you get the same box labelled "the
webhook" three times. So each chain is pinned to a different part of the
webhook's life. The first is about the URL outliving the thing that issued it,
so its chain runs on a calendar rather than on a request: the install dies in
one quarter and the alert stops in another, and nobody connects the two. The
second is about a field that used to work, so its chain has no failure in it at
all - every arrow is green and the message still lands in the wrong room. The
third is about bytes, so its chain starts inside a shell script and never
reaches Slack's parser intact. The fourth leaves webhooks entirely and is about
a date: a surface Slack switched off, still sitting in a live manifest.

The branches sort four different things: an inventory of URLs against the
installs behind them, the destinations a codebase asks for against the one it
gets, a byte string against the shapes a JSON parser rejects, and a manifest
against a retirement.

Drawn in Slack aubergine. No em dashes inside SVG text: one mis-sniffed
encoding turns a single character into three mojibake ones inside an image,
where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the
# module. Every diagram here is constructed at import time, so the theme has to
# be active across exactly this file and no further.
BRAND = "#4A154B"
D.set_theme(BRAND)

V = {}

V["slack/incoming-webhook-dead"] = {
    "flow_intro": (
        "This chain runs on a calendar rather than on a request, because the "
        "two halves of the fault are months apart. Somebody leaves, or an app "
        "is reinstalled, and the URL that a build server has been holding for "
        "two years stops working at that moment. Nothing tells the build "
        "server. The red step is not an error anybody read: it is a 404 "
        "landing in a curl command whose exit status nothing checks, in a "
        "pipeline that goes green. The fix branch sorts an inventory rather "
        "than a token, because the question is never really whether one URL "
        "works. It is which systems hold a URL at all, and whether the "
        "install behind each one is still standing."
    ),
    "diagram_problem": D.chain(
        "skwhdead-p",
        "A webhook URL that keeps its shape long after the install behind it died",
        "The URL is a bearer credential with no expiry stamped on it and no "
        "owner recorded anywhere. It looks exactly the same the day it stops "
        "working as it did the day it was minted.",
        [
            ("A webhook is minted", "pasted into a build server"),
            ("Two years of alerts", "and nobody owns the URL"),
            ("The installer leaves", "or the app is reinstalled"),
            ("404 no_service", "into a curl nothing checks"),
            ("The channel goes quiet", "and quiet reads as calm"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skwhdead-f",
        "Stored webhook records joined to install records and to the bound channel",
        "Nothing is sent to any URL to reach this. The shape of the URL, the "
        "state of the install, the installing user and what the bound channel "
        "has actually received are all readable, and together they say more "
        "than a delivery attempt would.",
        ("Inventory beside installs", "shape, owner, install, history"),
        [
            ("Install already revoked", "the URL answers no_service", "bad"),
            ("Installer deactivated", "the bot token still works", "bad"),
            ("Issued for another team", "an inventory row from elsewhere", "bad"),
            ("No system recorded", "a rotation has nowhere to land", "plain"),
            ("Delivered this week", "install live, channel receiving", "good"),
        ],
    ),
}

V["slack/webhook-locked-to-one-channel"] = {
    "flow_intro": (
        "Nothing in the first three arrows fails, which is the whole point. "
        "No call was refused, no status code was wrong, no error was "
        "swallowed. The code asked for four channels, Slack accepted every "
        "request and answered each one with a real timestamp, and the "
        "messages all arrived in the same room because the destination was "
        "decided once, at creation, by whoever clicked through the install. "
        "The only red box is the last, and it is not a failure Slack ever "
        "reports: it is one room full of four teams' alerts and three teams "
        "seeing nothing. The fix branch sorts destinations rather than "
        "errors, and the row that carries the finding is the one where "
        "several routing keys turn up in a single channel's history."
    ),
    "diagram_problem": D.chain(
        "skwhchan-p",
        "Four destinations asked for and one channel receiving all of them",
        "The channel field in the payload was a custom integration feature. "
        "On an app based webhook it is inert, so a routing table written "
        "years ago quietly became a single destination.",
        [
            ("A routing table", "four channels, one webhook"),
            ("channel set per send", "as every old post shows"),
            ("Slack accepts it", "no error, a real timestamp"),
            ("The field is ignored", "the binding was made at install"),
            ("One room, four teams", "and three teams see nothing"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "skwhchan-f",
        "The destinations a codebase asks for held against the one it is bound to",
        "Two readings agree or they do not. What the sending code intends is "
        "in the sending code; where the messages went is in the bound "
        "channel's history. Neither reading needs a message to be sent.",
        ("Intended beside bound", "code, install record, history"),
        [
            ("Several keys, one room", "the routing collapsed", "bad"),
            ("Addressed elsewhere", "every send names another channel", "bad"),
            ("A field that does nothing", "inert on an app webhook", "bad"),
            ("One webhook per channel", "one secret each to manage", "plain"),
            ("A bot token and an id", "any channel, chosen per message", "good"),
        ],
    ),
}

V["slack/webhook-invalid-payload"] = {
    "flow_intro": (
        "The failure here happens before Slack is involved at all, which is "
        "why the chain starts inside a shell script. A commit message picks "
        "up a double quote, the quote is interpolated straight into a JSON "
        "literal, and the body that leaves the machine is no longer JSON. "
        "The red arrow is at the parser, and it is the earliest one in the "
        "batch that Slack itself draws: unusually for this section the answer "
        "is a real 400 with a real reason in it, and the reason nobody sees "
        "it is that shell scripts do not check exit codes. The fix branch "
        "sorts a byte string, not a message. Block structure comes later and "
        "belongs to another note."
    ),
    "diagram_problem": D.chain(
        "skwhpay-p",
        "A shell script building JSON by hand until one quote ends the message",
        "String interpolation into a JSON literal works until the "
        "interpolated text contains a quote, a newline or a backslash. Then "
        "the body stops parsing, and the pipeline stays green.",
        [
            ("A commit message", "with a quote in it"),
            ("Interpolated into JSON", "by a shell heredoc"),
            ("Sent as a webhook body", "form encoded by default"),
            ("400 invalid_payload", "a real status, plain text"),
            ("curl exits 0", "the build goes green"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "skwhpay-f",
        "One captured body read as bytes and sorted before anything is sent",
        "Read locally, from a file, with no network call of any kind. A "
        "payload that fails here would have failed at Slack, and finding out "
        "on your own machine costs nobody a message in a channel.",
        ("The body as bytes", "decode, parse, then envelope"),
        [
            ("A raw newline in a string", "a log fragment pasted in", "bad"),
            ("Text outside every string", "a quote that was not escaped", "bad"),
            ("Parses, but carries nothing", "no text, blocks or attachments", "bad"),
            ("Web API keys in the body", "copied from chat.postMessage", "plain"),
            ("Built by a serializer", "and typed application/json", "good"),
        ],
    ),
}

V["slack/legacy-workflow-steps"] = {
    "flow_intro": (
        "This is the only chain in the batch with a date in it, and the date "
        "is the mechanism. Slack retired Steps from Apps on 26 September "
        "2024: the workflows containing them stopped running, the steps "
        "stopped working, and the events stopped being subscribable. Nothing "
        "in your app changed, and nothing in your app reports it, because the "
        "handler that would have logged something is simply never called. The "
        "red arrow is the first one, before any request exists. The fix "
        "branch sorts a manifest rather than traffic, because dead "
        "configuration is the only trace the retirement left behind and it is "
        "sitting in a document you can export."
    ),
    "diagram_problem": D.chain(
        "skwfstep-p",
        "A workflow step that stopped being called on a date nobody logged",
        "A retirement is not an error. The handler is healthy, the app is "
        "installed, the scope is granted, and the event that would have "
        "reached the handler is no longer sent by anybody.",
        [
            ("A custom step ships", "used in real workflows"),
            ("26 September 2024", "Steps from Apps retired"),
            ("The workflows stop", "and the steps stop with them"),
            ("No execute event", "the handler is never called"),
            ("Dead config remains", "in a live manifest"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "skwfstep-f",
        "A live manifest and a grant read for configuration a retirement left behind",
        "Three readings, none of which needs traffic: what the manifest still "
        "declares, which retired events it still lists, and whether the grant "
        "carries a scope only legacy step apps were ever given.",
        ("Manifest, grant, source", "what the retirement left standing"),
        [
            ("workflow_steps declared", "a feature that no longer runs", "bad"),
            ("Retired events listed", "five names nobody can send", "bad"),
            ("workflow.steps:execute", "a scope only legacy apps hold", "bad"),
            ("Legacy and modern both", "half migrated, both declared", "plain"),
            ("Custom functions only", "rebuilt on the current model", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
