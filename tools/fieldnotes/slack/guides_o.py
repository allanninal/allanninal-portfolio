#!/usr/bin/env python3
"""/slack/ field notes, batch O - the writing.

Four notes about the payload rather than the destination. The rest of this
section is mostly about where a message is going: a channel the bot is not in,
a channel nobody may post to, a thread that cannot take a reply. These four are
about the thing being sent, and they are deliberately written as four different
rules with four different endings.

One block is structurally wrong and Slack refuses the entire message with a
single error that names nothing. Every block is fine and the message as a whole
is over a ceiling that only exists at the message level. Every rule is
satisfied, the send succeeds, and the notification the reader gets is blank -
the only one of the four where nothing anywhere fails. And a single field is a
few characters too long, where the interesting part is that some fields reject
and some silently truncate.

Read only throughout, and more literally here than anywhere else in the
section: the Block Kit limits are documented and the payloads are yours, so
three of these four scripts will run with no Slack token at all against a
payload file. Validating a payload by sending it is how a test message ends up
in a customer channel.
"""

CITE_BLOCKS = ("Blocks reference - Slack Docs",
               "https://docs.slack.dev/reference/block-kit/blocks")
CITE_COMPOSITION = ("Composition objects - Slack Docs",
                    "https://docs.slack.dev/reference/block-kit/composition-objects")
CITE_BLOCK_KIT = ("Block Kit - Slack Docs", "https://docs.slack.dev/block-kit/")
CITE_POSTMESSAGE = ("chat.postMessage method reference - Slack Docs",
                    "https://docs.slack.dev/reference/methods/chat.postMessage")
CITE_CONV_HISTORY = ("conversations.history method reference - Slack Docs",
                     "https://docs.slack.dev/reference/methods/conversations.history")
CITE_RETRIEVING = ("Retrieving messages - Slack Docs",
                   "https://docs.slack.dev/messaging/retrieving-messages")
CITE_VIEWS_OPEN = ("views.open method reference - Slack Docs",
                   "https://docs.slack.dev/reference/methods/views.open")
CITE_UPLOAD = ("files.getUploadURLExternal method reference - Slack Docs",
               "https://docs.slack.dev/reference/methods/files.getUploadURLExternal")
CITE_AUTH_TEST = ("auth.test method reference - Slack Docs",
                  "https://docs.slack.dev/reference/methods/auth.test")
CITE_WEB_API = ("Web API - Slack Docs", "https://docs.slack.dev/apis/web-api/")

GUIDES = []

GUIDES.append({
"slug": "invalid-blocks",
"title": "invalid_blocks: the whole message dies on one block",
"description": "Slack refuses the entire blocks array with one error that names nothing. Validate the payload locally, and fetch every image URL from outside your session.",
"h1": "invalid_blocks: the whole message dies on one block",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack invalid_blocks", "slack invalid_blocks_format",
             "slack block kit validation error", "slack image block not rendering",
             "slack blocks rejected but valid in block kit builder"],
"deps": "Python 3.9+ with requests, or Node.js 18+; no token at all if you check a payload file",
"lead": "The payload renders perfectly in Block Kit Builder. The JSON parses. The same generator produced a hundred messages that worked. This one comes back <code>{\"ok\": false, \"error\": \"invalid_blocks\"}</code> and Slack does not say which block, which field, or which rule.</p><p>So the message did not land, and the only information you have is that something in an array of eleven objects is wrong. This is a payload problem rather than a delivery problem: the channel is fine, the bot is in it, the token is valid, and the thing you handed Slack is not a thing Slack will accept.",
"short_answer": """<p>Slack validates the whole <code>blocks</code> array server-side and rejects the entire message on the first violation, returning one opaque string. <code>invalid_blocks</code> means a block broke a rule; <code>invalid_blocks_format</code> means the array itself was not what the API expected, which is almost always an object where a JSON array should be, or a string that was encoded twice.</p>
<p>The structural rules are documented and your payload is in your hands, so this check needs no token and no network: hand the script the JSON and it names the block index, the field and the rule. The one rule it cannot check locally is the one that causes most of these, which is that an <code>image</code> block's <code>image_url</code> must be fetchable <strong>by Slack</strong>, unauthenticated, returning an image content type. A chart URL behind your SSO works flawlessly in the browser where you tested it, because your browser had a session cookie. Slack does not, and an image Slack cannot fetch does not degrade to <code>alt_text</code> - it kills the message.</p>""",
"problem": """<p>The debugging loop this creates is the expensive part. There is one error string for perhaps twenty distinct rules, no block index, no field name, and no partial success to reason from. So the loop becomes bisection by sending: comment out half the blocks, post, see if it works, repeat. Every iteration is a real message into a real channel, which means either a scratch channel that does not have the data that reproduces the bug, or a customer-facing channel that now has six half-rendered diagnostic messages in it.</p>
<p>Worse, the payload usually validates everywhere you look. Block Kit Builder renders it. Your schema tests pass. A colleague pastes it into their own workspace and it posts. That last one is genuinely maddening and it is the tell: the difference is not the payload, it is whether the thing the payload points at can be reached from where Slack is standing.</p>
<p>Image blocks are the reason this note leads with images. <code>image_url</code> is fetched by Slack's own infrastructure at post time. If the URL needs a cookie, a bearer token, a VPN, or resolves to <code>localhost</code> on the developer's machine, Slack gets a 401, a 403 or a connection refused, and refuses the message rather than dropping the image. A developer who opens the same URL in the browser they are logged into sees a chart and concludes the URL is fine. It is fine for them. The check has to be made from a client with no credentials, which is the whole point of the unauthenticated fetch this script makes.</p>
<p>The rest is a long tail of shapes that look right and are not: a <code>section</code> whose <code>text</code> came out empty because a template variable was blank, a <code>static_select</code> whose options array is empty because the query returned nothing, two buttons that ended up with the same <code>action_id</code> because the loop that built them reused a constant, a block type from an SDK newer than the workspace. Each is obvious once named, and Slack names none of them.</p>""",
"why": """<p><strong>Rejection is all-or-nothing, so one bad block costs the whole message.</strong> There is no partial render and no fallback path. That is why a nineteen-block digest can be destroyed by the twentieth block containing an image nobody looks at, and why the fix has to be pre-send validation rather than post-send inspection.</p>
<p><strong>The structural rules are checkable without Slack, and should be checked without Slack.</strong> Every rule in this script's table comes from the published block reference. Running them locally turns a send-and-see loop into a function call, which is the difference between a fix that takes ten minutes and one that takes an afternoon and leaves debris in a channel.</p>
<p><strong>An unauthenticated fetch is the only honest test of an image URL.</strong> Your browser, your terminal on the VPN, and your CI runner inside the VPC all have access Slack does not. The script sends no <code>Authorization</code> header deliberately, and reports a <code>401</code> or <code>403</code> as the finding rather than as an error in the check.</p>
<p><strong>A private or loopback host is a certainty, not a suspicion.</strong> <code>http://localhost:3000/chart.png</code> and <code>http://10.0.1.14/graph.svg</code> cannot be fetched by Slack from anywhere, ever. The script decides those from the URL alone and does not bother making a request, because a request from inside your network would succeed and tell you the wrong thing.</p>
<p><strong>Unknown is not the same as wrong.</strong> Slack adds block types. An element this script's table does not recognise is reported as unknown and never as a fault, because an audit that fails on a new block type gets switched off the first time somebody upgrades an SDK.</p>
<p><strong>Length ceilings are a different rule with the same error string.</strong> A 3,001-character <code>section</code> text also produces <code>invalid_blocks</code>, and it is measured rather than inspected, so it lives in its own note and this script deliberately does not duplicate it. Two audits reporting the same row is how a team fixes one problem twice.</p>""",
"steps": [
 {"h": "Check the payload before you check anything else",
  "body": """<p>Write the failing payload to a file and run the script with <code>--payload</code>. No token, no network, no message. <code>audit_blocks</code> walks the array and names the index, the field and the rule for every violation it can decide from the JSON alone, which is most of them.</p>"""},
 {"h": "Separate the format error from the block error",
  "body": """<p><code>invalid_blocks_format</code> and <code>invalid_blocks</code> are not the same finding. The first means the array is not an array: an object came back from the builder, or the SDK encoded an already-encoded string. The script returns that as a fault on <code>blocks</code> itself rather than on any block, because no amount of staring at block seven will fix it.</p>"""},
 {"h": "Fetch every image URL with nothing attached",
  "body": """<p>Each <code>image_url</code> in the payload gets one unauthenticated <code>HEAD</code>. <code>image_verdict</code> sorts the answer into <code>public-image</code>, <code>auth-required</code>, <code>not-found</code>, <code>not-an-image</code>, <code>unreachable</code> or <code>not-public</code>. Only the first of those is a URL Slack can use.</p>"""},
 {"h": "Decide loopback and private hosts from the URL, without asking",
  "body": """<p>A request to <code>localhost</code> from your own machine answers <code>200</code> and proves nothing. The script classifies those from the hostname and skips the fetch, because the only useful answer here is the one Slack would get, and you cannot get it from inside.</p>"""},
 {"h": "Run the same audit over what the app has already posted",
  "body": """<p>With a token and <code>--channel</code>, the script reads <code>conversations.history</code> and audits the blocks Slack stored for your app's own messages. The same generator produced those and the failing one, so a rule that is nearly broken across a hundred successful messages is the rule about to break on the next one.</p>"""},
 {"h": "Read the severities as three different instructions",
  "body": """<p><code>fatal</code> means Slack will refuse this. <code>risky</code> means it will post and will not do what you meant. <code>unknown</code> means the script does not have a rule and you should read the block reference. Collapsing the three into a pass or fail is how a real fault gets buried under a list of shrugs.</p>"""},
],
"verify": """<p>Fix the block the script names, run it again on the same file, and the verdict should move from <code>reject</code> to <code>clean</code> before you send anything.</p>
<pre><code class="language-bash">python3 slack_invalid_blocks.py --payload failing-digest.json
# payload    11 block(s) read from failing-digest.json
# verdict    reject         1 fatal, 0 risky, 0 unknown
# fatal      blocks[7](image)  https://charts.internal/deploys.png answered 403 to an
#                              unauthenticated request: Slack fetches this itself and
#                              has no session; your browser does
# images     1 checked, 1 unusable
#   repair: host the image at a URL that answers 200 with an image content type to a
#           client holding no credentials, or upload it and reference the returned file</code></pre>""",
"code_intro": "Three pure functions and one deliberately unauthenticated request. <code>block_fault</code> is the block reference turned into a table, and returns severities rather than booleans. <code>audit_blocks</code> adds the two rules that only exist across blocks: the array must be an array, and an <code>action_id</code> must be unique within one message. <code>image_verdict</code> is the one that earns the note, because it turns <code>403</code> into a sentence about session cookies rather than a status code nobody connects to a rejected message.",
"py_file": "slack_invalid_blocks.py",
"py": '''"""Find the block that would make Slack reject the whole message.

Read only, and with --payload it holds no token and calls no Slack method at
all. Nothing is posted from here: bisecting a Block Kit payload by sending it
is how a scratch message ends up in a customer channel, so this validates the
JSON you hand it, or the payloads conversations.history says your app already
sent, and issues one unauthenticated HEAD per image URL to see what Slack's
own fetcher would see.
"""
import argparse
import json
import logging
import os
import sys
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_invalid_blocks")

API = "https://slack.com/api/"

# Block types whose rules are in the table below. A type that is not here is
# reported as unknown and never as a fault: Slack ships new block types, and an
# audit that fails on an SDK upgrade gets switched off within a week.
KNOWN_BLOCKS = {"actions", "context", "divider", "file", "header", "image",
                "input", "rich_text", "section", "video"}

# Elements that must carry at least one option. An empty options array is what
# a query returning no rows produces, and it kills the entire message.
OPTION_ELEMENTS = {"static_select", "multi_static_select", "radio_buttons",
                   "checkboxes", "overflow"}

TEXT_TYPES = {"plain_text", "mrkdwn"}

# Slack fetches image_url from its own infrastructure. These never resolve to
# anything it can reach, so they are decided from the hostname and the fetch is
# skipped: a request to localhost from your own machine answers 200 and tells
# you the opposite of the truth.
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "host.docker.internal"}


def _is_private_host(host):
    """Is this a host Slack could never reach from the public internet? Pure."""
    h = str(host or "").strip().lower().strip("[]")
    if not h:
        return True
    if h in LOOPBACK_HOSTS or h.endswith(".local") or h.endswith(".internal"):
        return True
    if "." not in h and ":" not in h:
        return True  # a bare hostname only your resolver knows
    parts = h.split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        a, b = int(parts[0]), int(parts[1])
        if a == 10 or a == 127 or (a == 192 and b == 168) or (a == 169 and b == 254):
            return True
        if a == 172 and 16 <= b <= 31:
            return True
    return False


def _text_ok(obj):
    """Is this a usable text composition object? Pure."""
    if not isinstance(obj, dict):
        return False
    if obj.get("type") not in TEXT_TYPES:
        return False
    return bool(str(obj.get("text") or "").strip())


def _element_fault(el, path):
    """Faults in one interactive or context element. Pure."""
    if not isinstance(el, dict):
        return [("fatal", path, "an element must be an object; this is a %s"
                 % type(el).__name__)]
    etype = str(el.get("type") or "").strip()
    if not etype:
        return [("fatal", path, "an element with no type field")]
    where = "%s(%s)" % (path, etype)
    rows = []
    if etype in OPTION_ELEMENTS:
        options = el.get("options")
        groups = el.get("option_groups")
        has_options = isinstance(options, list) and len(options) > 0
        has_groups = isinstance(groups, list) and any(
            isinstance(g, dict) and g.get("options") for g in groups)
        if not has_options and not has_groups:
            rows.append(("fatal", where, "%s with no options; an empty options array "
                                         "is what a query returning no rows produces "
                                         "and it rejects the whole message" % etype))
    if etype == "button":
        if not _text_ok(el.get("text")):
            rows.append(("fatal", where, "a button needs a non-empty plain_text label"))
        url = str(el.get("url") or "")
        if url and not url.startswith(("http://", "https://")):
            rows.append(("risky", where, "button url %r is not an http or https URL"
                         % url[:60]))
    if etype in TEXT_TYPES and not _text_ok(el):
        rows.append(("fatal", where, "an empty text object; a blank template variable "
                                     "produces exactly this"))
    return rows


def _child_elements(block, path):
    """Yield (path, element) for everything inside a block. Pure."""
    for key in ("accessory", "element"):
        child = block.get(key)
        if child is not None:
            yield ("%s.%s" % (path, key), child)
    elements = block.get("elements")
    if isinstance(elements, list):
        for i, el in enumerate(elements):
            yield ("%s.elements[%d]" % (path, i), el)


def _action_ids(block, path):
    """Yield (action_id, where) for every element in one block. Pure."""
    if not isinstance(block, dict):
        return
    for where, el in _child_elements(block, path):
        if isinstance(el, dict) and str(el.get("action_id") or "").strip():
            yield (str(el["action_id"]), where)


def block_fault(block, index=0):
    """Return the structural faults in one block. Pure.

    Rows are (severity, path, detail). fatal means Slack refuses the message,
    risky means it posts and does not do what you meant, unknown means this
    table has no rule and you should read the block reference.

    Character ceilings are deliberately absent. A 3001 character section text
    produces the same error string from a different rule, it is measured rather
    than inspected, and it has its own note; two audits reporting one row is
    how a team fixes one problem twice.
    """
    path = "blocks[%d]" % index
    if not isinstance(block, dict):
        return [("fatal", path, "a block must be an object; this is a %s"
                 % type(block).__name__)]
    btype = str(block.get("type") or "").strip()
    if not btype:
        return [("fatal", path, "no type field, so Slack cannot dispatch this block")]
    where = "%s(%s)" % (path, btype)
    rows = []
    if btype not in KNOWN_BLOCKS:
        rows.append(("unknown", where, "%s is not in this table; it is either newer "
                                       "than the table or a typo, and only one of "
                                       "those is a fault" % btype))

    if btype == "section":
        fields = block.get("fields")
        has_fields = isinstance(fields, list) and any(_text_ok(f) for f in fields)
        if not _text_ok(block.get("text")) and not has_fields:
            rows.append(("fatal", where, "a section needs text or fields and this has "
                                         "neither usable; an empty template variable "
                                         "lands here"))
        if isinstance(fields, list) and len(fields) > 10:
            rows.append(("fatal", where, "%d fields; a section takes at most 10"
                         % len(fields)))
    elif btype == "header":
        head = block.get("text")
        if not _text_ok(head):
            rows.append(("fatal", where, "a header needs a non-empty text object"))
        elif head.get("type") != "plain_text":
            rows.append(("fatal", where, "a header text object must be plain_text, "
                                         "not %s" % head.get("type")))
    elif btype == "image":
        if not block.get("image_url") and not block.get("slack_file"):
            rows.append(("fatal", where, "an image block needs image_url or slack_file"))
        if not str(block.get("alt_text") or "").strip():
            rows.append(("fatal", where, "an image block needs alt_text, which is also "
                                         "the only thing a screen reader is given"))
    elif btype == "actions":
        elements = block.get("elements")
        if not isinstance(elements, list) or not elements:
            rows.append(("fatal", where, "an actions block with no elements"))
        elif len(elements) > 25:
            rows.append(("fatal", where, "%d elements; an actions block takes at most 25"
                         % len(elements)))
    elif btype == "context":
        elements = block.get("elements")
        if not isinstance(elements, list) or not elements:
            rows.append(("fatal", where, "a context block with no elements"))
        elif len(elements) > 10:
            rows.append(("fatal", where, "%d elements; a context block takes at most 10"
                         % len(elements)))
    elif btype == "input":
        if not _text_ok(block.get("label")):
            rows.append(("fatal", where, "an input block needs a label"))
        if block.get("element") is None:
            rows.append(("fatal", where, "an input block needs an element"))

    for sub, el in _child_elements(block, path):
        rows.extend(_element_fault(el, sub))
    return rows


def audit_blocks(blocks):
    """Validate a whole payload, including the rules that span blocks. Pure.

    Returns (verdict, rows) where verdict is reject, suspect or clean. The
    difference matters: reject names something Slack will refuse, suspect names
    something this script cannot decide from the payload alone and will not
    pretend to have decided.
    """
    if isinstance(blocks, str):
        return ("reject", [("fatal", "blocks", "blocks is a string. It was encoded to "
                                               "JSON once too often, which Slack "
                                               "answers with invalid_blocks_format")])
    if not isinstance(blocks, list):
        return ("reject", [("fatal", "blocks", "blocks must be a JSON array and this "
                                               "is a %s. Passing the object your "
                                               "builder returned produces "
                                               "invalid_blocks_format"
                            % type(blocks).__name__)])
    rows = []
    if not blocks:
        rows.append(("unknown", "blocks", "an empty blocks array. Slack accepts it "
                                          "beside a text field, but it usually means "
                                          "the generator produced nothing"))
    if len(blocks) > 50:
        rows.append(("unknown", "blocks", "%d blocks is past the 50 a message takes. "
                                          "That is a different error and its own note"
                     % len(blocks)))
    for i, block in enumerate(blocks):
        rows.extend(block_fault(block, i))

    seen = {}
    for i, block in enumerate(blocks):
        for action_id, where in _action_ids(block, "blocks[%d]" % i):
            seen.setdefault(action_id, []).append(where)
    for action_id, wheres in sorted(seen.items()):
        if len(wheres) > 1:
            rows.append(("fatal", ", ".join(wheres),
                         "action_id %s appears %d times in one message and must be "
                         "unique within the payload; a loop reusing a constant is the "
                         "usual cause" % (action_id, len(wheres))))

    if any(r[0] == "fatal" for r in rows):
        return ("reject", rows)
    return ("suspect", rows) if rows else ("clean", rows)


def image_verdict(url, status=None, content_type=None, error=None):
    """Could Slack's own fetcher have loaded this image? Pure.

    Returns (verdict, detail). Only public-image is a URL Slack can use, and an
    image Slack cannot fetch does not fall back to alt_text: it rejects the
    entire message.
    """
    text = str(url or "").strip()
    if not text:
        return ("missing", "no image_url on an image block")
    if not text.startswith(("http://", "https://")):
        return ("not-http", "%s is not an http or https URL; a data: URI or a bare "
                            "path is not something Slack can fetch" % text[:80])
    host = urlsplit(text).hostname
    if _is_private_host(host):
        return ("not-public", "%s resolves only inside your own network. Slack fetches "
                              "this from its infrastructure, so it can never load; "
                              "testing it from here would answer 200 and mislead you"
                % (host or text[:60]))
    if error:
        return ("unreachable", "%s did not answer an unauthenticated request (%s)"
                % (text[:80], error))
    code = int(status or 0)
    if code in (401, 403):
        return ("auth-required", "%s answered %d to a request carrying no credentials. "
                                 "Slack has no session cookie and your browser does, "
                                 "which is why this looks fine when you open it"
                % (text[:80], code))
    if code == 404:
        return ("not-found", "%s answered 404 unauthenticated" % text[:80])
    if code >= 400:
        return ("error-status", "%s answered %d unauthenticated" % (text[:80], code))
    if code == 0:
        return ("unchecked", "%s was not fetched" % text[:80])
    ctype = str(content_type or "").split(";")[0].strip().lower()
    if not ctype.startswith("image/"):
        return ("not-an-image", "%s answered %d with content type %r. An HTML error "
                                "page returned with a 200 looks like success to "
                                "everything except Slack's image fetcher"
                % (text[:80], code, ctype or "none"))
    return ("public-image", "%s answered %d as %s to a client holding no credentials"
            % (text[:80], code, ctype))


def image_urls(blocks):
    """Every image_url in a payload, with where it was found. Pure."""
    out = []
    for i, block in enumerate(blocks or []):
        if not isinstance(block, dict):
            continue
        if block.get("type") == "image" and block.get("image_url"):
            out.append(("blocks[%d](image)" % i, str(block["image_url"])))
        for where, el in _child_elements(block, "blocks[%d]" % i):
            if isinstance(el, dict) and el.get("type") == "image" and el.get("image_url"):
                out.append((where, str(el["image_url"])))
    return out


def probe(url, timeout=10):
    """One unauthenticated HEAD, so the answer is the one Slack would get.

    No Authorization header, no cookie jar, on purpose: every credential you
    hold is a credential Slack does not, and the whole question is what a
    stranger sees.
    """
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code in (405, 501):
            r = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
            r.close()
        return (r.status_code, r.headers.get("Content-Type", ""), None)
    except requests.RequestException as exc:
        return (None, "", str(exc))


def report(verdict, rows, label):
    counts = {"fatal": 0, "risky": 0, "unknown": 0}
    for severity, _, _ in rows:
        counts[severity] = counts.get(severity, 0) + 1
    (log.warning if verdict == "reject" else log.info)(
        "verdict    %-14s %s: %d fatal, %d risky, %d unknown", verdict, label,
        counts.get("fatal", 0), counts.get("risky", 0), counts.get("unknown", 0))
    for severity, where, detail in rows:
        (log.warning if severity == "fatal" else log.info)(
            "%-10s %s  %s", severity, where, detail)
    return counts.get("fatal", 0)


def check_images(blocks, timeout, skip):
    bad = 0
    urls = image_urls(blocks)
    checked = 0
    for where, url in urls:
        host = urlsplit(url).hostname if url.startswith(("http://", "https://")) else None
        if skip or (host and _is_private_host(host)) or not url.startswith(("http://", "https://")):
            verdict, detail = image_verdict(url, status=0 if skip else None)
        else:
            status, ctype, err = probe(url, timeout)
            checked += 1
            verdict, detail = image_verdict(url, status, ctype, err)
        if verdict == "public-image":
            log.info("image      %-14s %s  %s", verdict, where, detail)
        else:
            bad += 1
            log.warning("image      %-14s %s  %s", verdict, where, detail)
    if urls:
        log.info("images     %d found, %d fetched, %d unusable", len(urls), checked, bad)
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--payload", default="",
                    help="a JSON file holding a blocks array or a whole message; "
                         "with this the script needs no Slack token at all")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel to audit your app's own stored blocks in; repeatable")
    ap.add_argument("--limit", type=int, default=200, help="messages read per channel")
    ap.add_argument("--timeout", type=float, default=10.0, help="seconds per image fetch")
    ap.add_argument("--skip-images", action="store_true",
                    help="structure only; useful on a machine with no egress")
    args = ap.parse_args()

    if args.payload:
        raw = json.loads(open(args.payload, encoding="utf-8").read())
        blocks = raw if isinstance(raw, (list, str)) else raw.get("blocks")
        count = len(blocks) if isinstance(blocks, list) else "an unusable"
        log.info("payload    %s block(s) read from %s", count, args.payload)
        verdict, rows = audit_blocks(blocks)
        fatal = report(verdict, rows, args.payload)
        fatal += check_images(blocks if isinstance(blocks, list) else [],
                              args.timeout, args.skip_images)
        if fatal:
            log.warning("  repair: fix the block named above and run this again before "
                        "you send anything; bisecting by posting leaves debris")
            log.warning("  repair: an image_url must answer 200 with an image content "
                        "type to a client holding no credentials, or upload the file "
                        "and reference what Slack gives you back")
            return 1
        return 0

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s, or pass --payload to check a file with no token at all",
                  args.token_env)
        return 2
    if not args.channel:
        log.error("pass at least one --channel, or --payload")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    bot_id = who.get("bot_id") or ""
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    fatal = 0
    for channel in args.channel:
        body = s.get(API + "conversations.history", timeout=30,
                     params={"channel": channel, "limit": str(args.limit)}).json()
        if body.get("ok") is not True:
            log.warning("history    unavailable    %s: %s", channel, body.get("error"))
            continue
        ours = [m for m in body.get("messages") or []
                if m.get("blocks") and (not bot_id or m.get("bot_id") == bot_id)]
        log.info("history    %s: %d message(s) of ours carrying blocks", channel,
                 len(ours))
        for m in ours:
            verdict, rows = audit_blocks(m.get("blocks"))
            if verdict != "clean":
                fatal += report(verdict, rows, "%s ts=%s" % (channel, m.get("ts")))
            fatal += check_images(m.get("blocks"), args.timeout, args.skip_images)

    if fatal:
        log.warning("  repair: validate the generated payload in the message builder, "
                    "before the call, and log the payload beside any invalid_blocks")
        log.warning("  repair: host every image at a publicly fetchable URL with an "
                    "image content type, or upload it to Slack and use the file")
        return 1
    log.info("verdict    clean          nothing in these payloads breaks a structural rule")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-invalid-blocks.mjs",
"js": '''/**
 * Find the block that would make Slack reject the whole message.
 *
 * Read only, and with --payload it holds no token and calls no Slack method at
 * all. Nothing is posted from here: bisecting a Block Kit payload by sending it
 * is how a scratch message ends up in a customer channel, so this validates the
 * JSON you hand it, or the payloads conversations.history says your app already
 * sent, and issues one unauthenticated HEAD per image URL.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// A type that is not here is reported as unknown and never as a fault: Slack
// ships new block types, and an audit that fails on an SDK upgrade gets
// switched off within a week.
const KNOWN_BLOCKS = new Set(['actions', 'context', 'divider', 'file', 'header',
  'image', 'input', 'rich_text', 'section', 'video']);

const OPTION_ELEMENTS = new Set(['static_select', 'multi_static_select',
  'radio_buttons', 'checkboxes', 'overflow']);

const TEXT_TYPES = new Set(['plain_text', 'mrkdwn']);

const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '0.0.0.0', '::1',
  'host.docker.internal']);

/** Is this a host Slack could never reach from the public internet? Pure. */
export function isPrivateHost(host) {
  const h = String(host ?? '').trim().toLowerCase().replace(/^\\[|\\]$/g, '');
  if (!h) return true;
  if (LOOPBACK_HOSTS.has(h) || h.endsWith('.local') || h.endsWith('.internal')) return true;
  if (!h.includes('.') && !h.includes(':')) return true;
  const parts = h.split('.');
  if (parts.length === 4 && parts.every((p) => /^\\d{1,3}$/.test(p))) {
    const [a, b] = parts.map(Number);
    if (a === 10 || a === 127 || (a === 192 && b === 168) || (a === 169 && b === 254)) {
      return true;
    }
    if (a === 172 && b >= 16 && b <= 31) return true;
  }
  return false;
}

function textOk(obj) {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return false;
  if (!TEXT_TYPES.has(obj.type)) return false;
  return String(obj.text ?? '').trim().length > 0;
}

function elementFault(el, path) {
  if (!el || typeof el !== 'object' || Array.isArray(el)) {
    return [['fatal', path, `an element must be an object; this is a ${typeof el}`]];
  }
  const etype = String(el.type ?? '').trim();
  if (!etype) return [['fatal', path, 'an element with no type field']];
  const where = `${path}(${etype})`;
  const rows = [];
  if (OPTION_ELEMENTS.has(etype)) {
    const hasOptions = Array.isArray(el.options) && el.options.length > 0;
    const hasGroups = Array.isArray(el.option_groups)
      && el.option_groups.some((g) => g && Array.isArray(g.options) && g.options.length);
    if (!hasOptions && !hasGroups) {
      rows.push(['fatal', where, `${etype} with no options; an empty options array is ` +
        'what a query returning no rows produces and it rejects the whole message']);
    }
  }
  if (etype === 'button') {
    if (!textOk(el.text)) {
      rows.push(['fatal', where, 'a button needs a non-empty plain_text label']);
    }
    const url = String(el.url ?? '');
    if (url && !/^https?:\\/\\//.test(url)) {
      rows.push(['risky', where, `button url ${url.slice(0, 60)} is not an http or https URL`]);
    }
  }
  if (TEXT_TYPES.has(etype) && !textOk(el)) {
    rows.push(['fatal', where, 'an empty text object; a blank template variable ' +
      'produces exactly this']);
  }
  return rows;
}

function* childElements(block, path) {
  for (const key of ['accessory', 'element']) {
    if (block[key] !== undefined && block[key] !== null) yield [`${path}.${key}`, block[key]];
  }
  if (Array.isArray(block.elements)) {
    for (let i = 0; i < block.elements.length; i += 1) {
      yield [`${path}.elements[${i}]`, block.elements[i]];
    }
  }
}

function* actionIds(block, path) {
  if (!block || typeof block !== 'object') return;
  for (const [where, el] of childElements(block, path)) {
    if (el && typeof el === 'object' && String(el.action_id ?? '').trim()) {
      yield [String(el.action_id), where];
    }
  }
}

/**
 * Return the structural faults in one block. Pure.
 *
 * Rows are [severity, path, detail]. Character ceilings are deliberately
 * absent: they produce the same error string from a different rule and have
 * their own note.
 */
export function blockFault(block, index = 0) {
  let path = `blocks[${index}]`;
  if (!block || typeof block !== 'object' || Array.isArray(block)) {
    return [['fatal', path, `a block must be an object; this is a ${typeof block}`]];
  }
  const btype = String(block.type ?? '').trim();
  if (!btype) {
    return [['fatal', path, 'no type field, so Slack cannot dispatch this block']];
  }
  const where = `${path}(${btype})`;
  const rows = [];
  if (!KNOWN_BLOCKS.has(btype)) {
    rows.push(['unknown', where, `${btype} is not in this table; it is either newer ` +
      'than the table or a typo, and only one of those is a fault']);
  }

  if (btype === 'section') {
    const fields = block.fields;
    const hasFields = Array.isArray(fields) && fields.some(textOk);
    if (!textOk(block.text) && !hasFields) {
      rows.push(['fatal', where, 'a section needs text or fields and this has neither ' +
        'usable; an empty template variable lands here']);
    }
    if (Array.isArray(fields) && fields.length > 10) {
      rows.push(['fatal', where, `${fields.length} fields; a section takes at most 10`]);
    }
  } else if (btype === 'header') {
    if (!textOk(block.text)) {
      rows.push(['fatal', where, 'a header needs a non-empty text object']);
    } else if (block.text.type !== 'plain_text') {
      rows.push(['fatal', where,
        `a header text object must be plain_text, not ${block.text.type}`]);
    }
  } else if (btype === 'image') {
    if (!block.image_url && !block.slack_file) {
      rows.push(['fatal', where, 'an image block needs image_url or slack_file']);
    }
    if (!String(block.alt_text ?? '').trim()) {
      rows.push(['fatal', where, 'an image block needs alt_text, which is also the ' +
        'only thing a screen reader is given']);
    }
  } else if (btype === 'actions') {
    if (!Array.isArray(block.elements) || !block.elements.length) {
      rows.push(['fatal', where, 'an actions block with no elements']);
    } else if (block.elements.length > 25) {
      rows.push(['fatal', where,
        `${block.elements.length} elements; an actions block takes at most 25`]);
    }
  } else if (btype === 'context') {
    if (!Array.isArray(block.elements) || !block.elements.length) {
      rows.push(['fatal', where, 'a context block with no elements']);
    } else if (block.elements.length > 10) {
      rows.push(['fatal', where,
        `${block.elements.length} elements; a context block takes at most 10`]);
    }
  } else if (btype === 'input') {
    if (!textOk(block.label)) rows.push(['fatal', where, 'an input block needs a label']);
    if (block.element === undefined || block.element === null) {
      rows.push(['fatal', where, 'an input block needs an element']);
    }
  }

  for (const [sub, el] of childElements(block, path)) {
    rows.push(...elementFault(el, sub));
  }
  return rows;
}

/**
 * Validate a whole payload, including the rules that span blocks. Pure.
 * Returns [verdict, rows] where verdict is reject, suspect or clean.
 */
export function auditBlocks(blocks) {
  if (typeof blocks === 'string') {
    return ['reject', [['fatal', 'blocks', 'blocks is a string. It was encoded to JSON ' +
      'once too often, which Slack answers with invalid_blocks_format']]];
  }
  if (!Array.isArray(blocks)) {
    return ['reject', [['fatal', 'blocks', `blocks must be a JSON array and this is a ` +
      `${typeof blocks}. Passing the object your builder returned produces ` +
      'invalid_blocks_format']]];
  }
  const rows = [];
  if (!blocks.length) {
    rows.push(['unknown', 'blocks', 'an empty blocks array. Slack accepts it beside a ' +
      'text field, but it usually means the generator produced nothing']);
  }
  if (blocks.length > 50) {
    rows.push(['unknown', 'blocks', `${blocks.length} blocks is past the 50 a message ` +
      'takes. That is a different error and its own note']);
  }
  blocks.forEach((block, i) => rows.push(...blockFault(block, i)));

  const seen = new Map();
  blocks.forEach((block, i) => {
    for (const [id, where] of actionIds(block, `blocks[${i}]`)) {
      if (!seen.has(id)) seen.set(id, []);
      seen.get(id).push(where);
    }
  });
  for (const [id, wheres] of [...seen.entries()].sort()) {
    if (wheres.length > 1) {
      rows.push(['fatal', wheres.join(', '), `action_id ${id} appears ${wheres.length} ` +
        'times in one message and must be unique within the payload; a loop reusing a ' +
        'constant is the usual cause']);
    }
  }

  if (rows.some((r) => r[0] === 'fatal')) return ['reject', rows];
  return rows.length ? ['suspect', rows] : ['clean', rows];
}

/**
 * Could Slack's own fetcher have loaded this image? Pure.
 * Only public-image is a URL Slack can use, and an image Slack cannot fetch
 * does not fall back to alt_text: it rejects the entire message.
 */
export function imageVerdict(url, status = null, contentType = null, error = null) {
  const text = String(url ?? '').trim();
  if (!text) return ['missing', 'no image_url on an image block'];
  if (!/^https?:\\/\\//.test(text)) {
    return ['not-http', `${text.slice(0, 80)} is not an http or https URL; a data: URI ` +
      'or a bare path is not something Slack can fetch'];
  }
  let host = '';
  try { host = new URL(text).hostname; } catch { host = ''; }
  if (isPrivateHost(host)) {
    return ['not-public', `${host || text.slice(0, 60)} resolves only inside your own ` +
      'network. Slack fetches this from its infrastructure, so it can never load; ' +
      'testing it from here would answer 200 and mislead you'];
  }
  if (error) {
    return ['unreachable',
      `${text.slice(0, 80)} did not answer an unauthenticated request (${error})`];
  }
  const code = Number(status ?? 0);
  if (code === 401 || code === 403) {
    return ['auth-required', `${text.slice(0, 80)} answered ${code} to a request ` +
      'carrying no credentials. Slack has no session cookie and your browser does, ' +
      'which is why this looks fine when you open it'];
  }
  if (code === 404) return ['not-found', `${text.slice(0, 80)} answered 404 unauthenticated`];
  if (code >= 400) {
    return ['error-status', `${text.slice(0, 80)} answered ${code} unauthenticated`];
  }
  if (code === 0) return ['unchecked', `${text.slice(0, 80)} was not fetched`];
  const ctype = String(contentType ?? '').split(';')[0].trim().toLowerCase();
  if (!ctype.startsWith('image/')) {
    return ['not-an-image', `${text.slice(0, 80)} answered ${code} with content type ` +
      `${ctype || 'none'}. An HTML error page returned with a 200 looks like success ` +
      "to everything except Slack's image fetcher"];
  }
  return ['public-image',
    `${text.slice(0, 80)} answered ${code} as ${ctype} to a client holding no credentials`];
}

/** Every image_url in a payload, with where it was found. Pure. */
export function imageUrls(blocks) {
  const out = [];
  (blocks ?? []).forEach((block, i) => {
    if (!block || typeof block !== 'object') return;
    if (block.type === 'image' && block.image_url) {
      out.push([`blocks[${i}](image)`, String(block.image_url)]);
    }
    for (const [where, el] of childElements(block, `blocks[${i}]`)) {
      if (el && typeof el === 'object' && el.type === 'image' && el.image_url) {
        out.push([where, String(el.image_url)]);
      }
    }
  });
  return out;
}

// No Authorization header and no cookie jar, on purpose: every credential you
// hold is one Slack does not, and the whole question is what a stranger sees.
async function probe(url) {
  try {
    const res = await fetch(url, { method: 'HEAD', redirect: 'follow' });
    return [res.status, res.headers.get('content-type') ?? '', null];
  } catch (err) {
    return [null, '', err.message];
  }
}

function report(verdict, rows, label) {
  const counts = { fatal: 0, risky: 0, unknown: 0 };
  for (const [severity] of rows) counts[severity] = (counts[severity] ?? 0) + 1;
  const line = `verdict    ${verdict.padEnd(14)} ${label}: ${counts.fatal} fatal, ` +
    `${counts.risky} risky, ${counts.unknown} unknown`;
  (verdict === 'reject' ? console.warn : console.log)(line);
  for (const [severity, where, detail] of rows) {
    (severity === 'fatal' ? console.warn : console.log)(
      `${severity.padEnd(10)} ${where}  ${detail}`);
  }
  return counts.fatal;
}

async function checkImages(blocks, skip) {
  const urls = imageUrls(blocks);
  let bad = 0;
  let checked = 0;
  for (const [where, url] of urls) {
    let host = '';
    try { host = new URL(url).hostname; } catch { host = ''; }
    let verdict;
    let detail;
    if (skip || isPrivateHost(host) || !/^https?:\\/\\//.test(url)) {
      [verdict, detail] = imageVerdict(url, skip ? 0 : null);
    } else {
      const [status, ctype, err] = await probe(url);
      checked += 1;
      [verdict, detail] = imageVerdict(url, status, ctype, err);
    }
    if (verdict === 'public-image') {
      console.log(`image      ${verdict.padEnd(14)} ${where}  ${detail}`);
    } else {
      bad += 1;
      console.warn(`image      ${verdict.padEnd(14)} ${where}  ${detail}`);
    }
  }
  if (urls.length) {
    console.log(`images     ${urls.length} found, ${checked} fetched, ${bad} unusable`);
  }
  return bad;
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function argAll(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const skipImages = args.includes('--skip-images');
  const payload = arg(args, '--payload', '');

  if (payload) {
    const raw = JSON.parse(await readFile(payload, 'utf8'));
    const blocks = Array.isArray(raw) || typeof raw === 'string' ? raw : raw.blocks;
    const count = Array.isArray(blocks) ? blocks.length : 'an unusable';
    console.log(`payload    ${count} block(s) read from ${payload}`);
    const [verdict, rows] = auditBlocks(blocks);
    let fatal = report(verdict, rows, payload);
    fatal += await checkImages(Array.isArray(blocks) ? blocks : [], skipImages);
    if (fatal) {
      console.warn('  repair: fix the block named above and run this again before you ' +
        'send anything; bisecting by posting leaves debris');
      console.warn('  repair: an image_url must answer 200 with an image content type ' +
        'to a client holding no credentials, or upload the file and reference what ' +
        'Slack gives you back');
      process.exitCode = 1;
    }
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}, or pass --payload to check a file with no token at all`);
    process.exitCode = 2;
    return;
  }
  const channels = argAll(args, '--channel');
  if (!channels.length) {
    console.error('pass at least one --channel, or --payload');
    process.exitCode = 2;
    return;
  }
  const limit = arg(args, '--limit', '200');
  const headers = { Authorization: `Bearer ${token}` };

  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  const botId = who.bot_id ?? '';
  console.log(`identity   ${who.user_id} in ${who.team}`);

  let fatal = 0;
  for (const channel of channels) {
    const url = `${API}conversations.history?channel=${encodeURIComponent(channel)}` +
      `&limit=${encodeURIComponent(limit)}`;
    const body = await (await fetch(url, { headers })).json();
    if (body.ok !== true) {
      console.warn(`history    unavailable    ${channel}: ${body.error}`);
      continue;
    }
    const ours = (body.messages ?? []).filter(
      (m) => m.blocks && (!botId || m.bot_id === botId));
    console.log(`history    ${channel}: ${ours.length} message(s) of ours carrying blocks`);
    for (const m of ours) {
      const [verdict, rows] = auditBlocks(m.blocks);
      if (verdict !== 'clean') fatal += report(verdict, rows, `${channel} ts=${m.ts}`);
      fatal += await checkImages(m.blocks, skipImages);
    }
  }

  if (fatal) {
    console.warn('  repair: validate the generated payload in the message builder, ' +
      'before the call, and log the payload beside any invalid_blocks');
    console.warn('  repair: host every image at a publicly fetchable URL with an image ' +
      'content type, or upload it to Slack and use the file');
    process.exitCode = 1;
  } else {
    console.log('verdict    clean          nothing in these payloads breaks a structural rule');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertions that matter are the ones about restraint. A block type this table has never heard of must come back <code>unknown</code> and must not push the verdict to <code>reject</code>, because an audit that fails on an SDK upgrade is an audit nobody runs twice. A <code>401</code> from an image URL must be reported as a session problem rather than as a broken link, since that is the reading that changes what somebody does next. And a URL on <code>localhost</code> must be decided without a request at all, because the request would succeed and the answer would be wrong.",
"test_py_file": "test_slack_invalid_blocks.py",
"test_py": '''from slack_invalid_blocks import (audit_blocks, block_fault, image_urls,
                                  image_verdict)


def section(text="hello"):
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def test_a_healthy_payload_is_clean():
    verdict, rows = audit_blocks([section(), {"type": "divider"}])
    assert verdict == "clean"
    assert rows == []


def test_a_section_with_neither_text_nor_fields_is_fatal():
    rows = block_fault({"type": "section"}, 3)
    assert rows[0][0] == "fatal"
    assert "blocks[3](section)" == rows[0][1]
    assert "text or fields" in rows[0][2]


def test_a_section_whose_text_is_an_empty_string_is_also_fatal():
    assert block_fault(section(""), 0)[0][0] == "fatal"
    assert block_fault(section("   "), 0)[0][0] == "fatal"


def test_more_than_ten_fields_is_fatal():
    block = {"type": "section",
             "fields": [{"type": "mrkdwn", "text": "x"} for _ in range(11)]}
    assert any("at most 10" in r[2] for r in block_fault(block))


def test_an_unknown_block_type_is_unknown_and_never_reject():
    verdict, rows = audit_blocks([{"type": "quantum_carousel"}])
    assert rows[0][0] == "unknown"
    assert verdict == "suspect"


def test_a_select_with_no_options_is_fatal():
    block = {"type": "actions",
             "elements": [{"type": "static_select", "options": []}]}
    assert audit_blocks([block])[0] == "reject"


def test_a_select_with_option_groups_is_accepted():
    block = {"type": "actions", "elements": [
        {"type": "static_select",
         "option_groups": [{"options": [{"text": {"type": "plain_text", "text": "a"},
                                         "value": "a"}]}]}]}
    assert audit_blocks([block])[0] == "clean"


def test_an_image_block_needs_a_url_and_alt_text():
    rows = block_fault({"type": "image"}, 0)
    assert len(rows) == 2
    assert all(r[0] == "fatal" for r in rows)
    assert any("alt_text" in r[2] for r in rows)


def test_a_header_must_be_plain_text():
    block = {"type": "header", "text": {"type": "mrkdwn", "text": "Deploys"}}
    assert "plain_text" in block_fault(block)[0][2]


def test_blocks_as_an_object_or_a_string_is_the_format_error():
    verdict, rows = audit_blocks({"blocks": []})
    assert verdict == "reject"
    assert "invalid_blocks_format" in rows[0][2]
    assert "once too often" in audit_blocks("[]")[1][0][2]


def test_a_duplicate_action_id_across_two_blocks_is_fatal():
    button = {"type": "button", "action_id": "approve",
              "text": {"type": "plain_text", "text": "Approve"}}
    verdict, rows = audit_blocks([{"type": "actions", "elements": [button]},
                                  {"type": "actions", "elements": [dict(button)]}])
    assert verdict == "reject"
    assert any("appears 2 times" in r[2] for r in rows)


def test_the_same_action_id_in_different_messages_is_fine():
    button = {"type": "button", "action_id": "approve",
              "text": {"type": "plain_text", "text": "Approve"}}
    assert audit_blocks([{"type": "actions", "elements": [button]}])[0] == "clean"


def test_more_than_fifty_blocks_is_handed_to_the_other_note():
    verdict, rows = audit_blocks([{"type": "divider"} for _ in range(51)])
    assert verdict == "suspect"
    assert "its own note" in rows[0][2]


def test_an_image_that_wants_credentials_is_named_as_a_session_problem():
    verdict, detail = image_verdict("https://charts.example.com/a.png", 403, "image/png")
    assert verdict == "auth-required"
    assert "session cookie" in detail


def test_a_two_hundred_that_is_not_an_image_is_caught():
    verdict, detail = image_verdict("https://example.com/a.png", 200, "text/html")
    assert verdict == "not-an-image"
    assert "error page" in detail


def test_a_usable_image_is_the_only_clean_verdict():
    assert image_verdict("https://example.com/a.png", 200, "image/png; charset=utf-8")[0] \\
        == "public-image"


def test_loopback_and_private_hosts_are_decided_without_a_request():
    for url in ("http://localhost:3000/a.png", "http://127.0.0.1/a.png",
                "http://10.0.1.14/a.png", "http://192.168.1.5/a.png",
                "http://172.20.0.3/a.png", "https://charts.internal/a.png"):
        assert image_verdict(url)[0] == "not-public", url


def test_a_public_address_is_not_mistaken_for_a_private_one():
    assert image_verdict("https://203.0.113.10/a.png", 200, "image/png")[0] == "public-image"


def test_a_data_uri_and_a_bare_path_are_not_fetchable():
    assert image_verdict("data:image/png;base64,AAAA")[0] == "not-http"
    assert image_verdict("/static/a.png")[0] == "not-http"
    assert image_verdict("")[0] == "missing"


def test_a_transport_error_is_unreachable_rather_than_a_status():
    assert image_verdict("https://example.com/a.png", None, None, "timed out")[0] \\
        == "unreachable"


def test_image_urls_finds_accessories_as_well_as_image_blocks():
    blocks = [{"type": "image", "image_url": "https://a/1.png", "alt_text": "a"},
              {"type": "section", "text": {"type": "mrkdwn", "text": "x"},
               "accessory": {"type": "image", "image_url": "https://a/2.png",
                             "alt_text": "b"}}]
    found = image_urls(blocks)
    assert [u for _, u in found] == ["https://a/1.png", "https://a/2.png"]
    assert found[1][0].endswith(".accessory")
''',
"test_js_file": "slack-invalid-blocks.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  auditBlocks, blockFault, imageUrls, imageVerdict, isPrivateHost,
} from './slack-invalid-blocks.mjs';

const section = (text = 'hello') => ({ type: 'section', text: { type: 'mrkdwn', text } });

test('a healthy payload is clean', () => {
  const [verdict, rows] = auditBlocks([section(), { type: 'divider' }]);
  assert.equal(verdict, 'clean');
  assert.equal(rows.length, 0);
});

test('a section with neither text nor fields is fatal', () => {
  const rows = blockFault({ type: 'section' }, 3);
  assert.equal(rows[0][0], 'fatal');
  assert.equal(rows[0][1], 'blocks[3](section)');
  assert.match(rows[0][2], /text or fields/);
});

test('a section whose text is an empty string is also fatal', () => {
  assert.equal(blockFault(section(''), 0)[0][0], 'fatal');
  assert.equal(blockFault(section('   '), 0)[0][0], 'fatal');
});

test('more than ten fields is fatal', () => {
  const block = { type: 'section', fields: Array.from({ length: 11 },
    () => ({ type: 'mrkdwn', text: 'x' })) };
  assert.ok(blockFault(block).some((r) => /at most 10/.test(r[2])));
});

test('an unknown block type is unknown and never reject', () => {
  const [verdict, rows] = auditBlocks([{ type: 'quantum_carousel' }]);
  assert.equal(rows[0][0], 'unknown');
  assert.equal(verdict, 'suspect');
});

test('a select with no options is fatal', () => {
  const block = { type: 'actions', elements: [{ type: 'static_select', options: [] }] };
  assert.equal(auditBlocks([block])[0], 'reject');
});

test('a select with option groups is accepted', () => {
  const block = { type: 'actions', elements: [{ type: 'static_select',
    option_groups: [{ options: [{ text: { type: 'plain_text', text: 'a' }, value: 'a' }] }] }] };
  assert.equal(auditBlocks([block])[0], 'clean');
});

test('an image block needs a url and alt text', () => {
  const rows = blockFault({ type: 'image' }, 0);
  assert.equal(rows.length, 2);
  assert.ok(rows.every((r) => r[0] === 'fatal'));
  assert.ok(rows.some((r) => /alt_text/.test(r[2])));
});

test('a header must be plain_text', () => {
  const block = { type: 'header', text: { type: 'mrkdwn', text: 'Deploys' } };
  assert.match(blockFault(block)[0][2], /plain_text/);
});

test('blocks as an object or a string is the format error', () => {
  const [verdict, rows] = auditBlocks({ blocks: [] });
  assert.equal(verdict, 'reject');
  assert.match(rows[0][2], /invalid_blocks_format/);
  assert.match(auditBlocks('[]')[1][0][2], /once too often/);
});

test('a duplicate action_id across two blocks is fatal', () => {
  const button = { type: 'button', action_id: 'approve',
    text: { type: 'plain_text', text: 'Approve' } };
  const [verdict, rows] = auditBlocks([
    { type: 'actions', elements: [button] },
    { type: 'actions', elements: [{ ...button }] },
  ]);
  assert.equal(verdict, 'reject');
  assert.ok(rows.some((r) => /appears 2 times/.test(r[2])));
});

test('the same action_id in different messages is fine', () => {
  const button = { type: 'button', action_id: 'approve',
    text: { type: 'plain_text', text: 'Approve' } };
  assert.equal(auditBlocks([{ type: 'actions', elements: [button] }])[0], 'clean');
});

test('more than fifty blocks is handed to the other note', () => {
  const [verdict, rows] = auditBlocks(Array.from({ length: 51 }, () => ({ type: 'divider' })));
  assert.equal(verdict, 'suspect');
  assert.match(rows[0][2], /its own note/);
});

test('an image that wants credentials is named as a session problem', () => {
  const [verdict, detail] = imageVerdict('https://charts.example.com/a.png', 403, 'image/png');
  assert.equal(verdict, 'auth-required');
  assert.match(detail, /session cookie/);
});

test('a two hundred that is not an image is caught', () => {
  const [verdict, detail] = imageVerdict('https://example.com/a.png', 200, 'text/html');
  assert.equal(verdict, 'not-an-image');
  assert.match(detail, /error page/);
});

test('a usable image is the only clean verdict', () => {
  assert.equal(
    imageVerdict('https://example.com/a.png', 200, 'image/png; charset=utf-8')[0],
    'public-image');
});

test('loopback and private hosts are decided without a request', () => {
  for (const url of ['http://localhost:3000/a.png', 'http://127.0.0.1/a.png',
    'http://10.0.1.14/a.png', 'http://192.168.1.5/a.png', 'http://172.20.0.3/a.png',
    'https://charts.internal/a.png']) {
    assert.equal(imageVerdict(url)[0], 'not-public', url);
  }
});

test('a public address is not mistaken for a private one', () => {
  assert.equal(imageVerdict('https://203.0.113.10/a.png', 200, 'image/png')[0],
    'public-image');
  assert.equal(isPrivateHost('example.com'), false);
});

test('a data uri and a bare path are not fetchable', () => {
  assert.equal(imageVerdict('data:image/png;base64,AAAA')[0], 'not-http');
  assert.equal(imageVerdict('/static/a.png')[0], 'not-http');
  assert.equal(imageVerdict('')[0], 'missing');
});

test('a transport error is unreachable rather than a status', () => {
  assert.equal(imageVerdict('https://example.com/a.png', null, null, 'timed out')[0],
    'unreachable');
});

test('imageUrls finds accessories as well as image blocks', () => {
  const blocks = [
    { type: 'image', image_url: 'https://a/1.png', alt_text: 'a' },
    { type: 'section', text: { type: 'mrkdwn', text: 'x' },
      accessory: { type: 'image', image_url: 'https://a/2.png', alt_text: 'b' } },
  ];
  const found = imageUrls(blocks);
  assert.deepEqual(found.map((f) => f[1]), ['https://a/1.png', 'https://a/2.png']);
  assert.ok(found[1][0].endsWith('.accessory'));
});
''',
"faq": [
 ("Slack said invalid_blocks. Why will it not say which block?",
  "The API returns a single error code for the whole call, and Block Kit validation happens as one server-side pass over the array. There is no field in the response that carries a block index, and there is no verbose mode that adds one. That asymmetry is the entire reason this script exists: the rules are published, so the index Slack will not give you can be computed on your side before the call is made."),
 ("The payload renders fine in Block Kit Builder. How can it be invalid?",
  "Block Kit Builder validates the structure, and structure is only part of the contract. It does not fetch your image URLs from Slack's network, it does not know whether an action_id collides with one in another block you pasted separately, and it renders with whatever preview it has rather than with the workspace's supported types. An image URL that needs a cookie is the classic case: the builder is running in your browser, which has the cookie."),
 ("Is invalid_blocks_format different from invalid_blocks?",
  "Yes, and the distinction saves time. invalid_blocks means the array was read and a block inside it broke a rule. invalid_blocks_format means the array could not be read as an array of blocks at all, which in practice is an object that should have been a list, or a value that was JSON-encoded twice on its way through an SDK. No amount of examining individual blocks will fix the second one."),
 ("Why check my own posted messages if those are the ones that worked?",
  "Because the same generator produced them and the failing one. A hundred successful messages that each carry nine of the ten permitted section fields tell you the tenth is arriving next week. The historical audit is a leading indicator; the payload check is the incident. They answer different questions and the script does both because you will want both at different times."),
 ("Can I just retry without the blocks and send plain text instead?",
  "As a fallback in the send path, yes, and it is a reasonable safety net so an alert still reaches somebody. As a fix, no: it converts a loud failure into a permanent silent downgrade, and nobody will notice that the rich message stopped being rich. Log the rejected payload, send the plain-text fallback, and treat the log line as a bug rather than as the resolution."),
],
"related": [
 ("/slack/text-length-limits/", "the same error string, from a length rule instead"),
 ("/slack/msg-blocks-too-long/", "when every block is valid and the message is not"),
 ("/slack/http-200-ok-false/", "why the rejection arrived looking like a success"),
],
"citations": [CITE_BLOCKS, CITE_COMPOSITION, CITE_POSTMESSAGE, CITE_BLOCK_KIT],
})

GUIDES.append({
"slug": "msg-blocks-too-long",
"title": "msg_blocks_too_long: the digest that grew past 50",
"description": "Every block is valid and the message is not. A payload built one block per item is a capacity problem, so measure the headroom before the busy day finds it.",
"h1": "msg_blocks_too_long: the digest that grew past 50",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack msg_blocks_too_long", "slack 50 block limit",
             "slack message too many blocks", "slack block kit payload size limit",
             "slack digest message fails on busy day"],
"deps": "Python 3.9+ with requests, or Node.js 18+; no token at all if you measure a payload file",
"lead": "The nightly digest has run for eight months. This morning it returned <code>{\"ok\": false, \"error\": \"msg_blocks_too_long\"}</code> and nobody deployed anything. The incident yesterday produced sixty failing checks instead of the usual twenty, the generator emitted one block per check, and the message crossed a ceiling that has been sitting there since the day it was written.</p><p>Nothing in the payload is malformed. Every block would pass validation on its own. This is a size rule that only exists at the message level, and it is the one payload failure that is a function of your traffic rather than of your code.",
"short_answer": """<p>A message takes at most <strong>50 blocks</strong>. Modals and Home tabs take 100. Past that, <code>chat.postMessage</code> answers <code>msg_blocks_too_long</code> and nothing is delivered.</p>
<p>There is a second ceiling that catches people harder, because it is on the encoded size of the payload rather than on the count. A message can sit comfortably at 20 blocks and still be refused, and reports of rejections cluster around 13,000 characters of block JSON. Twenty blocks each carrying 700 characters of log output crosses that long before it comes anywhere near block 50.</p>
<p>So the useful question is not "is this message legal" - today's is, or you would not be reading this. It is <strong>how much bigger can it get before it is not</strong>, and <strong>which of the two ceilings it hits first</strong>. This script measures both on a payload you hand it, or on every message your app has already posted, and reports the growth multiple that breaks each one.</p>""",
"problem": """<p>What makes this expensive is that it fires on exactly the wrong day. The generator maps a collection to blocks, one per item, so the payload is proportional to how much went wrong. On a quiet Tuesday there are twelve items and the message is 15 blocks. During the incident there are sixty, and the message that would have told everybody what was failing is the one message that does not arrive. The alerting goes silent at the moment the alerting matters, and it goes silent with an error most people have never seen.</p>
<p>Then the investigation goes the wrong way twice. The first wrong turn is treating it as a validation bug and staring at the blocks, all of which are fine. The second is fixing it at the call site: wrapping the send in a try, catching the error, and retrying with the first 40 blocks. That works, and it means that from then on the digest silently drops content on precisely the busiest days, with no record of what was cut.</p>
<p>The size ceiling makes it worse by being invisible. A team that learns about the 50-block limit adds an assertion on <code>len(blocks)</code>, watches it pass, and is rejected anyway because the blocks got fatter rather than more numerous. Nothing in the error string distinguishes the two, so the assertion that was supposed to prevent the problem becomes evidence that the problem is something else.</p>
<p>And the growth is invisible in the ordinary case. A message at 34 blocks looks perfectly healthy in a channel. Nobody counts blocks by eye. The only way to know you are one busy day from the ceiling is to measure the tail of what you have already sent, which nobody does until after the first failure.</p>""",
"why": """<p><strong>This is a capacity finding, not a correctness one.</strong> Every block passes. The message passes today. The output that matters is a number with a unit: at 1.6 times today's volume, this breaks. That is a sentence a team can act on before the incident, which is the only useful time to act on it.</p>
<p><strong>Two ceilings, and the smaller one is not always the obvious one.</strong> The script computes the growth multiple against the block count and against the encoded size, and names whichever comes first. A digest of many short lines is block-bound; a digest carrying stack traces is size-bound. Those have different repairs, and guessing which one you have is how a cap on block count fails to fix anything.</p>
<p><strong>The size ceiling is observed, not documented, and the script says so.</strong> Slack publishes the block counts. The payload size at which rejections start is a figure the community converged on rather than one you can cite, so it is a configurable default that is labelled as observed. An audit that presents a folk number as a specification is worse than one that presents it honestly.</p>
<p><strong>The median tells you nothing; the tail is the whole story.</strong> Reporting the average message size of a generator whose output is proportional to failures is close to useless. The script reports the maximum, the 90th percentile and the single tightest message in the sample, because the message that breaks is by definition the biggest one.</p>
<p><strong>The cap belongs in the generator, not at the call site.</strong> A cap where the blocks are built can decide what to keep, count what it dropped, and say so in the message. A cap at the send is a truncation with no knowledge of what it removed, which is how a digest quietly stops mentioning the worst failures.</p>
<p><strong>Measuring the size means encoding it the way Slack receives it.</strong> The number that counts is the length of the JSON on the wire, with no pretty-printing, not the length of your Python objects. The script encodes with compact separators for exactly that reason, and a whitespace-heavy encoder is itself a finding worth knowing about.</p>""",
"steps": [
 {"h": "Measure the payload you are about to send, with no token",
  "body": """<p><code>--payload</code> takes the JSON your generator produced and reports the count, the encoded size and the growth multiple. No Slack call, no message, no channel. This is the check that belongs in a test for the generator rather than in an incident.</p>"""},
 {"h": "Encode the way the API receives it",
  "body": """<p><code>budget</code> serialises with compact separators, because that is what goes on the wire. If your client sends indented JSON, the number it should be measuring is larger than the one your objects suggest, and that gap is worth knowing before it costs you a message.</p>"""},
 {"h": "Ask which ceiling arrives first",
  "body": """<p><code>break_multiple</code> returns a growth factor and the name of the ceiling that trips at it. <code>blocks</code> and <code>size</code> want different repairs: one wants fewer items, the other wants shorter ones. A message that is size-bound will not be saved by capping the block count.</p>"""},
 {"h": "Read the tail of what you have already sent",
  "body": """<p>With a token and a channel, the script measures every message your app posted and reports the maximum, the 90th percentile and the tightest single message. A distribution whose tail sits at 40 blocks is not healthy because the median is 12.</p>"""},
 {"h": "State the busy day as a number",
  "body": """<p><code>--growth</code> is your multiple for a bad day: three times the usual volume, say. <code>at_growth</code> reports how many of the messages you have already sent would be refused at that multiple. That converts "we might have a problem" into "eleven of last week's forty messages fail at 3x".</p>"""},
 {"h": "Cap where the blocks are built, and say what was dropped",
  "body": """<p>Emit at most about 45 blocks, append a footer saying how many items are not shown and where to find them, and thread or upload the remainder. The number in that footer is the thing a truncation at the call site can never produce.</p>"""},
],
"verify": """<p>Add the cap to the generator, then run the measurement over the same fixture that broke. The growth multiple should be the thing that changed, not the block count alone.</p>
<pre><code class="language-bash">python3 slack_block_budget.py --payload nightly-digest.json --growth 3
# payload    62 block(s), 18944 encoded characters
# headroom   over           62 blocks is past the 50 a message takes
# ceiling    blocks         over already: the block count went first, at 62 of 50
# growth     would-break    at 3.0x this payload is refused; it already is
#   repair: cap the generator at about 45 blocks and append a showing N of M footer</code></pre>""",
"code_intro": "Four pure functions and no cleverness. <code>budget</code> is two measurements taken the way the API takes them. <code>headroom</code> is the state today. <code>break_multiple</code> is the one worth having: a growth factor and the name of the ceiling that arrives first, which is the difference between a repair that shortens the list and one that shortens the lines. <code>at_growth</code> turns a fleet of past messages into how many of them a bad day would have destroyed.",
"py_file": "slack_block_budget.py",
"py": '''"""Measure how much bigger your messages can get before Slack refuses them.

Read only, and with --payload it holds no token and calls nothing. Nothing is
sent from here: finding the ceiling by walking a generator up to it is how a
channel fills with half-rendered test digests. This measures a payload you hand
it, or the payloads conversations.history says your app already sent, and
reports the growth multiple at which each ceiling arrives.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_block_budget")

API = "https://slack.com/api/"

# Documented block counts per surface.
SURFACES = {"message": 50, "modal": 100, "home": 100}

# Not documented. Rejections are widely reported to begin around this much
# encoded block JSON, and the script labels it observed everywhere it prints
# it: presenting a folk number as a specification is worse than presenting it
# honestly, and this one is a --size-ceiling away from being yours instead.
OBSERVED_SIZE_CEILING = 13200

# Above this share of either ceiling a payload is one bad day from failing.
AT_RISK = 0.8


def budget(blocks):
    """Count the two things that are actually limited. Pure.

    Returns (count, size). size is the length of the JSON as the API receives
    it, encoded with compact separators, because indentation in your client is
    payload too and the ceiling does not care that it is only whitespace.
    """
    if not isinstance(blocks, list):
        return (0, 0)
    encoded = json.dumps(blocks, separators=(",", ":"), ensure_ascii=False)
    return (len(blocks), len(encoded))


def headroom(count, size, surface="message", size_ceiling=OBSERVED_SIZE_CEILING):
    """Where this payload stands today. Pure.

    Returns (verdict, detail): over, at-risk, roomy, empty or unknown-surface.
    """
    limit = SURFACES.get(surface)
    if limit is None:
        return ("unknown-surface", "%r is not one of %s" % (
            surface, ", ".join(sorted(SURFACES))))
    if count <= 0:
        return ("empty", "no blocks, so there is nothing to measure")
    if count > limit:
        return ("over", "%d blocks is past the %d a %s takes" % (count, limit, surface))
    if size > size_ceiling:
        return ("over", "%d encoded characters is past the observed ceiling of %d, "
                        "with only %d blocks: this one is bound by size and not by "
                        "count" % (size, size_ceiling, count))
    if count >= limit * AT_RISK or size >= size_ceiling * AT_RISK:
        return ("at-risk", "%d of %d blocks and %d of an observed %d characters; this "
                           "is inside the last fifth of both budgets" % (
                               count, limit, size, size_ceiling))
    return ("roomy", "%d of %d blocks and %d of an observed %d characters" % (
        count, limit, size, size_ceiling))


def break_multiple(count, size, surface="message", size_ceiling=OBSERVED_SIZE_CEILING):
    """How much bigger can this get, and which ceiling arrives first. Pure.

    Returns (multiple, ceiling, detail). The ceiling name is the useful half:
    a block-bound message wants fewer items and a size-bound one wants shorter
    ones, and a cap on the block count does nothing at all for the second.
    """
    limit = SURFACES.get(surface)
    if limit is None:
        return (0.0, "unknown-surface", "%r is not a surface this script knows" % surface)
    if count <= 0:
        return (0.0, "empty", "no blocks, so there is no ceiling to grow into")
    if count > limit:
        return (0.0, "blocks", "over already: the block count went first, at %d of %d"
                % (count, limit))
    if size > size_ceiling:
        return (0.0, "size", "over already: the encoded size went first, at %d of an "
                             "observed %d, on only %d blocks"
                % (size, size_ceiling, count))
    by_blocks = limit / float(count)
    by_size = (size_ceiling / float(size)) if size > 0 else by_blocks
    if by_blocks <= by_size:
        return (round(by_blocks, 2), "blocks",
                "%.2fx more items and the block count reaches %d; fewer rows is the "
                "repair, not shorter ones" % (by_blocks, limit))
    return (round(by_size, 2), "size",
            "%.2fx more content and the encoded payload reaches an observed %d, while "
            "the block count is still only %d of %d; shorter rows is the repair"
            % (by_size, size_ceiling, count, limit))


def at_growth(samples, growth, surface="message", size_ceiling=OBSERVED_SIZE_CEILING):
    """How many of these payloads a busy day of this size would destroy. Pure.

    samples is [(count, size)]. Returns (breaking, total, detail). The point of
    the function is to answer with a count of real messages rather than with a
    hypothetical, because "eleven of last week's forty" is an argument and "we
    might have a problem" is not.
    """
    rows = [s for s in samples or [] if s and s[0] > 0]
    total = len(rows)
    if not total:
        return (0, 0, "no payloads with blocks in the sample")
    factor = float(growth)
    if factor <= 0:
        return (0, total, "a growth factor of %s cannot break anything" % growth)
    breaking = 0
    ceilings = {"blocks": 0, "size": 0}
    for count, size in rows:
        multiple, ceiling, _ = break_multiple(count, size, surface, size_ceiling)
        if multiple <= factor:
            breaking += 1
            if ceiling in ceilings:
                ceilings[ceiling] += 1
    if not breaking:
        return (0, total, "none of %d payload(s) break at %.1fx today's volume" % (
            total, factor))
    return (breaking, total, "%d of %d payload(s) are refused at %.1fx today's volume: "
                             "%d on the block count, %d on the encoded size" % (
                                 breaking, total, factor, ceilings["blocks"],
                                 ceilings["size"]))


def distribution(samples):
    """Reduce a fleet of payloads to the tail that decides. Pure.

    The median of a generator whose output is proportional to failures is close
    to meaningless, so this reports the maximum, the 90th percentile and the
    single tightest payload in the sample.
    """
    rows = [s for s in samples or [] if s and s[0] > 0]
    if not rows:
        return {"n": 0, "max_count": 0, "max_size": 0, "p90_count": 0, "p90_size": 0}
    counts = sorted(r[0] for r in rows)
    sizes = sorted(r[1] for r in rows)
    idx = int(round(0.9 * (len(rows) - 1)))
    return {"n": len(rows), "max_count": counts[-1], "max_size": sizes[-1],
            "p90_count": counts[idx], "p90_size": sizes[idx]}


def tightest(samples, surface="message", size_ceiling=OBSERVED_SIZE_CEILING):
    """The payload with the least room left, and how much that is. Pure."""
    best = None
    for count, size in [s for s in samples or [] if s and s[0] > 0]:
        multiple, ceiling, detail = break_multiple(count, size, surface, size_ceiling)
        if best is None or multiple < best[0]:
            best = (multiple, ceiling, detail, count, size)
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--payload", default="",
                    help="a JSON file holding a blocks array or a whole message; "
                         "with this the script needs no Slack token at all")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel your app posts into; repeatable")
    ap.add_argument("--limit", type=int, default=200, help="messages read per channel")
    ap.add_argument("--surface", default="message", choices=sorted(SURFACES),
                    help="message takes 50 blocks; a modal or Home tab takes 100")
    ap.add_argument("--size-ceiling", type=int, default=OBSERVED_SIZE_CEILING,
                    help="encoded characters at which rejections are observed to begin")
    ap.add_argument("--growth", type=float, default=3.0,
                    help="how much bigger a bad day is than an ordinary one")
    args = ap.parse_args()

    if args.payload:
        raw = json.loads(open(args.payload, encoding="utf-8").read())
        blocks = raw if isinstance(raw, list) else (raw or {}).get("blocks")
        count, size = budget(blocks)
        log.info("payload    %d block(s), %d encoded characters", count, size)
        verdict, detail = headroom(count, size, args.surface, args.size_ceiling)
        (log.warning if verdict in ("over", "at-risk") else log.info)(
            "headroom   %-14s %s", verdict, detail)
        multiple, ceiling, why = break_multiple(count, size, args.surface,
                                                args.size_ceiling)
        (log.warning if multiple and multiple <= args.growth else log.info)(
            "ceiling    %-14s %s", ceiling, why)
        breaking, total, growth_detail = at_growth([(count, size)], args.growth,
                                                   args.surface, args.size_ceiling)
        (log.warning if breaking else log.info)(
            "growth     %-14s %s", "would-break" if breaking else "survives",
            growth_detail)
        if verdict == "over" or breaking:
            log.warning("  repair: cap the generator at about 45 blocks and append a "
                        "showing N of M footer, so the truncation is visible")
            log.warning("  repair: if the ceiling is size, shorten the rows; upload the "
                        "long content as a file snippet and reference it from a "
                        "short block")
            return 1
        return 0

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s, or pass --payload to measure a file with no token at all",
                  args.token_env)
        return 2
    if not args.channel:
        log.error("pass at least one --channel, or --payload")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    bot_id = who.get("bot_id") or ""
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    samples = []
    for channel in args.channel:
        body = s.get(API + "conversations.history", timeout=30,
                     params={"channel": channel, "limit": str(args.limit)}).json()
        if body.get("ok") is not True:
            log.warning("history    unavailable    %s: %s", channel, body.get("error"))
            continue
        for m in body.get("messages") or []:
            if not m.get("blocks"):
                continue
            if bot_id and m.get("bot_id") != bot_id:
                continue
            samples.append(budget(m["blocks"]))
        log.info("history    %s: %d message(s) of ours carrying blocks", channel,
                 len(samples))

    d = distribution(samples)
    if not d["n"]:
        log.info("sample     empty          nothing of ours in these channels used blocks")
        return 0
    log.info("sample     %d payload(s), max %d blocks / %d chars, p90 %d blocks / %d chars",
             d["n"], d["max_count"], d["max_size"], d["p90_count"], d["p90_size"])

    worst = tightest(samples, args.surface, args.size_ceiling)
    multiple, ceiling, why, count, size = worst
    (log.warning if multiple <= args.growth else log.info)(
        "tightest   %-14s %d blocks / %d chars: %s", ceiling, count, size, why)

    breaking, total, growth_detail = at_growth(samples, args.growth, args.surface,
                                               args.size_ceiling)
    (log.warning if breaking else log.info)(
        "growth     %-14s %s", "would-break" if breaking else "survives", growth_detail)

    if breaking or multiple <= args.growth:
        log.warning("  repair: cap the block count in the generator at about 45 and "
                    "append a showing N of M footer with a link to the rest")
        log.warning("  repair: for a size-bound payload, thread the remainder with "
                    "thread_ts or upload it as a file snippet and post a summary")
        log.warning("  repair: for a modal, paginate the view and move the rest behind "
                    "a Next button that calls views.update")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-block-budget.mjs",
"js": '''/**
 * Measure how much bigger your messages can get before Slack refuses them.
 *
 * Read only, and with --payload it holds no token and calls nothing. Nothing is
 * sent from here: finding the ceiling by walking a generator up to it is how a
 * channel fills with half-rendered test digests. This measures a payload you
 * hand it, or the payloads conversations.history says your app already sent.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// Documented block counts per surface.
const SURFACES = new Map([['message', 50], ['modal', 100], ['home', 100]]);

// Not documented. Rejections are widely reported to begin around this much
// encoded block JSON, and it is labelled observed everywhere it is printed:
// presenting a folk number as a specification is worse than being honest.
const OBSERVED_SIZE_CEILING = 13200;

const AT_RISK = 0.8;

/**
 * Count the two things that are actually limited. Pure.
 * Returns [count, size], where size is the JSON the API receives.
 */
export function budget(blocks) {
  if (!Array.isArray(blocks)) return [0, 0];
  return [blocks.length, JSON.stringify(blocks).length];
}

/**
 * Where this payload stands today. Pure.
 * Returns [verdict, detail]: over, at-risk, roomy, empty or unknown-surface.
 */
export function headroom(count, size, surface = 'message',
  sizeCeiling = OBSERVED_SIZE_CEILING) {
  const limit = SURFACES.get(surface);
  if (limit === undefined) {
    return ['unknown-surface',
      `${surface} is not one of ${[...SURFACES.keys()].sort().join(', ')}`];
  }
  if (count <= 0) return ['empty', 'no blocks, so there is nothing to measure'];
  if (count > limit) {
    return ['over', `${count} blocks is past the ${limit} a ${surface} takes`];
  }
  if (size > sizeCeiling) {
    return ['over', `${size} encoded characters is past the observed ceiling of ` +
      `${sizeCeiling}, with only ${count} blocks: this one is bound by size and not ` +
      'by count'];
  }
  if (count >= limit * AT_RISK || size >= sizeCeiling * AT_RISK) {
    return ['at-risk', `${count} of ${limit} blocks and ${size} of an observed ` +
      `${sizeCeiling} characters; this is inside the last fifth of both budgets`];
  }
  return ['roomy',
    `${count} of ${limit} blocks and ${size} of an observed ${sizeCeiling} characters`];
}

/**
 * How much bigger can this get, and which ceiling arrives first. Pure.
 * Returns [multiple, ceiling, detail]. The ceiling name is the useful half: a
 * block-bound message wants fewer items and a size-bound one wants shorter
 * ones, and a cap on the block count does nothing at all for the second.
 */
export function breakMultiple(count, size, surface = 'message',
  sizeCeiling = OBSERVED_SIZE_CEILING) {
  const limit = SURFACES.get(surface);
  if (limit === undefined) {
    return [0, 'unknown-surface', `${surface} is not a surface this script knows`];
  }
  if (count <= 0) return [0, 'empty', 'no blocks, so there is no ceiling to grow into'];
  if (count > limit) {
    return [0, 'blocks',
      `over already: the block count went first, at ${count} of ${limit}`];
  }
  if (size > sizeCeiling) {
    return [0, 'size', `over already: the encoded size went first, at ${size} of an ` +
      `observed ${sizeCeiling}, on only ${count} blocks`];
  }
  const byBlocks = limit / count;
  const bySize = size > 0 ? sizeCeiling / size : byBlocks;
  if (byBlocks <= bySize) {
    return [Math.round(byBlocks * 100) / 100, 'blocks',
      `${byBlocks.toFixed(2)}x more items and the block count reaches ${limit}; ` +
      'fewer rows is the repair, not shorter ones'];
  }
  return [Math.round(bySize * 100) / 100, 'size',
    `${bySize.toFixed(2)}x more content and the encoded payload reaches an observed ` +
    `${sizeCeiling}, while the block count is still only ${count} of ${limit}; ` +
    'shorter rows is the repair'];
}

/**
 * How many of these payloads a busy day of this size would destroy. Pure.
 * Answers with a count of real messages rather than a hypothetical.
 */
export function atGrowth(samples, growth, surface = 'message',
  sizeCeiling = OBSERVED_SIZE_CEILING) {
  const rows = (samples ?? []).filter((s) => s && s[0] > 0);
  const total = rows.length;
  if (!total) return [0, 0, 'no payloads with blocks in the sample'];
  const factor = Number(growth);
  if (!(factor > 0)) return [0, total, `a growth factor of ${growth} cannot break anything`];
  let breaking = 0;
  const ceilings = { blocks: 0, size: 0 };
  for (const [count, size] of rows) {
    const [multiple, ceiling] = breakMultiple(count, size, surface, sizeCeiling);
    if (multiple <= factor) {
      breaking += 1;
      if (ceiling in ceilings) ceilings[ceiling] += 1;
    }
  }
  if (!breaking) {
    return [0, total,
      `none of ${total} payload(s) break at ${factor.toFixed(1)}x today's volume`];
  }
  return [breaking, total, `${breaking} of ${total} payload(s) are refused at ` +
    `${factor.toFixed(1)}x today's volume: ${ceilings.blocks} on the block count, ` +
    `${ceilings.size} on the encoded size`];
}

/**
 * Reduce a fleet of payloads to the tail that decides. Pure.
 * The median of a generator whose output is proportional to failures is close
 * to meaningless.
 */
export function distribution(samples) {
  const rows = (samples ?? []).filter((s) => s && s[0] > 0);
  if (!rows.length) {
    return { n: 0, maxCount: 0, maxSize: 0, p90Count: 0, p90Size: 0 };
  }
  const counts = rows.map((r) => r[0]).sort((a, b) => a - b);
  const sizes = rows.map((r) => r[1]).sort((a, b) => a - b);
  const idx = Math.round(0.9 * (rows.length - 1));
  return { n: rows.length,
    maxCount: counts[counts.length - 1],
    maxSize: sizes[sizes.length - 1],
    p90Count: counts[idx],
    p90Size: sizes[idx] };
}

/** The payload with the least room left, and how much that is. Pure. */
export function tightest(samples, surface = 'message',
  sizeCeiling = OBSERVED_SIZE_CEILING) {
  let best = null;
  for (const [count, size] of (samples ?? []).filter((s) => s && s[0] > 0)) {
    const [multiple, ceiling, detail] = breakMultiple(count, size, surface, sizeCeiling);
    if (best === null || multiple < best[0]) best = [multiple, ceiling, detail, count, size];
  }
  return best;
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function argAll(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const surface = arg(args, '--surface', 'message');
  const sizeCeiling = Number(arg(args, '--size-ceiling', OBSERVED_SIZE_CEILING));
  const growth = Number(arg(args, '--growth', '3'));
  const payload = arg(args, '--payload', '');

  if (payload) {
    const raw = JSON.parse(await readFile(payload, 'utf8'));
    const blocks = Array.isArray(raw) ? raw : (raw ?? {}).blocks;
    const [count, size] = budget(blocks);
    console.log(`payload    ${count} block(s), ${size} encoded characters`);
    const [verdict, detail] = headroom(count, size, surface, sizeCeiling);
    (verdict === 'over' || verdict === 'at-risk' ? console.warn : console.log)(
      `headroom   ${verdict.padEnd(14)} ${detail}`);
    const [multiple, ceiling, why] = breakMultiple(count, size, surface, sizeCeiling);
    (multiple <= growth ? console.warn : console.log)(
      `ceiling    ${ceiling.padEnd(14)} ${why}`);
    const [breaking, , growthDetail] = atGrowth([[count, size]], growth, surface,
      sizeCeiling);
    (breaking ? console.warn : console.log)(
      `growth     ${(breaking ? 'would-break' : 'survives').padEnd(14)} ${growthDetail}`);
    if (verdict === 'over' || breaking) {
      console.warn('  repair: cap the generator at about 45 blocks and append a ' +
        'showing N of M footer, so the truncation is visible');
      console.warn('  repair: if the ceiling is size, shorten the rows; upload the long ' +
        'content as a file snippet and reference it from a short block');
      process.exitCode = 1;
    }
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}, or pass --payload to measure a file with no token`);
    process.exitCode = 2;
    return;
  }
  const channels = argAll(args, '--channel');
  if (!channels.length) {
    console.error('pass at least one --channel, or --payload');
    process.exitCode = 2;
    return;
  }
  const limit = arg(args, '--limit', '200');
  const headers = { Authorization: `Bearer ${token}` };

  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  const botId = who.bot_id ?? '';
  console.log(`identity   ${who.user_id} in ${who.team}`);

  const samples = [];
  for (const channel of channels) {
    const url = `${API}conversations.history?channel=${encodeURIComponent(channel)}` +
      `&limit=${encodeURIComponent(limit)}`;
    const body = await (await fetch(url, { headers })).json();
    if (body.ok !== true) {
      console.warn(`history    unavailable    ${channel}: ${body.error}`);
      continue;
    }
    for (const m of body.messages ?? []) {
      if (!m.blocks) continue;
      if (botId && m.bot_id !== botId) continue;
      samples.push(budget(m.blocks));
    }
    console.log(`history    ${channel}: ${samples.length} message(s) of ours with blocks`);
  }

  const d = distribution(samples);
  if (!d.n) {
    console.log('sample     empty          nothing of ours in these channels used blocks');
    return;
  }
  console.log(`sample     ${d.n} payload(s), max ${d.maxCount} blocks / ${d.maxSize} ` +
    `chars, p90 ${d.p90Count} blocks / ${d.p90Size} chars`);

  const [multiple, ceiling, why, count, size] = tightest(samples, surface, sizeCeiling);
  (multiple <= growth ? console.warn : console.log)(
    `tightest   ${ceiling.padEnd(14)} ${count} blocks / ${size} chars: ${why}`);

  const [breaking, , growthDetail] = atGrowth(samples, growth, surface, sizeCeiling);
  (breaking ? console.warn : console.log)(
    `growth     ${(breaking ? 'would-break' : 'survives').padEnd(14)} ${growthDetail}`);

  if (breaking || multiple <= growth) {
    console.warn('  repair: cap the block count in the generator at about 45 and append ' +
      'a showing N of M footer with a link to the rest');
    console.warn('  repair: for a size-bound payload, thread the remainder with ' +
      'thread_ts or upload it as a file snippet and post a summary');
    console.warn('  repair: for a modal, paginate the view and move the rest behind a ' +
      'Next button that calls views.update');
    process.exitCode = 1;
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertion that matters most is that a payload can be size-bound while sitting at a quarter of the block count, because that is the case an assertion on <code>len(blocks)</code> was written to catch and does not. The rest keep the arithmetic honest: a message already over reports a growth multiple of zero rather than a negative one, an empty payload is not treated as infinitely safe, and the growth calculation reports how many real messages break rather than a probability.",
"test_py_file": "test_slack_block_budget.py",
"test_py": '''import json

from slack_block_budget import (at_growth, break_multiple, budget, distribution,
                                headroom, tightest)


def blocks(n, text="x"):
    return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}
            for _ in range(n)]


def test_budget_measures_the_encoding_the_api_receives():
    count, size = budget(blocks(3))
    assert count == 3
    assert size == len(json.dumps(blocks(3), separators=(",", ":")))


def test_budget_of_something_that_is_not_a_list_is_zero():
    assert budget(None) == (0, 0)
    assert budget({"blocks": []}) == (0, 0)


def test_fifty_one_blocks_is_over_and_fifty_is_not():
    assert headroom(51, 100)[0] == "over"
    assert headroom(50, 100)[0] == "at-risk"


def test_a_modal_gets_a_hundred_blocks():
    assert headroom(60, 100, "modal")[0] == "roomy"
    assert headroom(60, 100, "message")[0] == "over"
    assert headroom(1, 1, "carousel")[0] == "unknown-surface"


def test_a_payload_can_be_over_on_size_with_room_on_count():
    verdict, detail = headroom(20, 18000)
    assert verdict == "over"
    assert "bound by size and not by count" in detail


def test_the_block_ceiling_arrives_first_for_many_short_rows():
    multiple, ceiling, detail = break_multiple(25, 3000)
    assert ceiling == "blocks"
    assert multiple == 2.0
    assert "fewer rows" in detail


def test_the_size_ceiling_arrives_first_for_few_long_rows():
    multiple, ceiling, detail = break_multiple(10, 6600)
    assert ceiling == "size"
    assert multiple == 2.0
    assert "shorter rows" in detail


def test_a_payload_already_over_reports_zero_not_a_negative_multiple():
    assert break_multiple(60, 100) == (0.0, "blocks",
                                       "over already: the block count went first, "
                                       "at 60 of 50")
    assert break_multiple(10, 20000)[1] == "size"


def test_an_empty_payload_is_not_treated_as_infinitely_safe():
    assert break_multiple(0, 0)[1] == "empty"
    assert headroom(0, 0)[0] == "empty"


def test_growth_counts_real_messages_rather_than_guessing():
    samples = [(10, 1000), (20, 2000), (45, 4500)]
    breaking, total, detail = at_growth(samples, 2.0)
    assert (breaking, total) == (1, 3)
    assert "1 of 3" in detail and "on the block count" in detail


def test_growth_names_which_ceiling_each_breakage_hit():
    breaking, _, detail = at_growth([(45, 1000), (5, 9000)], 2.0)
    assert breaking == 2
    assert "1 on the block count, 1 on the encoded size" in detail


def test_a_zero_or_negative_growth_factor_breaks_nothing():
    assert at_growth([(45, 4500)], 0)[0] == 0
    assert at_growth([], 3.0)[1] == 0


def test_distribution_reports_the_tail_and_not_the_middle():
    d = distribution([(2, 200)] * 8 + [(40, 4000), (48, 4800)])
    assert d["n"] == 10
    assert d["max_count"] == 48
    assert d["p90_count"] == 40
    assert d["max_size"] == 4800


def test_distribution_of_an_empty_sample_is_empty_rather_than_an_error():
    assert distribution([])["n"] == 0
    assert distribution(None)["n"] == 0


def test_tightest_finds_the_one_message_that_decides():
    worst = tightest([(10, 1000), (40, 2000), (12, 12000)])
    assert worst[1] == "size"
    assert worst[3] == 12
''',
"test_js_file": "slack-block-budget.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  atGrowth, breakMultiple, budget, distribution, headroom, tightest,
} from './slack-block-budget.mjs';

const blocks = (n, text = 'x') => Array.from({ length: n },
  () => ({ type: 'section', text: { type: 'mrkdwn', text } }));

test('budget measures the encoding the api receives', () => {
  const [count, size] = budget(blocks(3));
  assert.equal(count, 3);
  assert.equal(size, JSON.stringify(blocks(3)).length);
});

test('budget of something that is not a list is zero', () => {
  assert.deepEqual(budget(null), [0, 0]);
  assert.deepEqual(budget({ blocks: [] }), [0, 0]);
});

test('fifty one blocks is over and fifty is not', () => {
  assert.equal(headroom(51, 100)[0], 'over');
  assert.equal(headroom(50, 100)[0], 'at-risk');
});

test('a modal gets a hundred blocks', () => {
  assert.equal(headroom(60, 100, 'modal')[0], 'roomy');
  assert.equal(headroom(60, 100, 'message')[0], 'over');
  assert.equal(headroom(1, 1, 'carousel')[0], 'unknown-surface');
});

test('a payload can be over on size with room on count', () => {
  const [verdict, detail] = headroom(20, 18000);
  assert.equal(verdict, 'over');
  assert.match(detail, /bound by size and not by count/);
});

test('the block ceiling arrives first for many short rows', () => {
  const [multiple, ceiling, detail] = breakMultiple(25, 3000);
  assert.equal(ceiling, 'blocks');
  assert.equal(multiple, 2);
  assert.match(detail, /fewer rows/);
});

test('the size ceiling arrives first for few long rows', () => {
  const [multiple, ceiling, detail] = breakMultiple(10, 6600);
  assert.equal(ceiling, 'size');
  assert.equal(multiple, 2);
  assert.match(detail, /shorter rows/);
});

test('a payload already over reports zero not a negative multiple', () => {
  const [multiple, ceiling, detail] = breakMultiple(60, 100);
  assert.equal(multiple, 0);
  assert.equal(ceiling, 'blocks');
  assert.match(detail, /over already/);
  assert.equal(breakMultiple(10, 20000)[1], 'size');
});

test('an empty payload is not treated as infinitely safe', () => {
  assert.equal(breakMultiple(0, 0)[1], 'empty');
  assert.equal(headroom(0, 0)[0], 'empty');
});

test('growth counts real messages rather than guessing', () => {
  const [breaking, total, detail] = atGrowth([[10, 1000], [20, 2000], [45, 4500]], 2);
  assert.equal(breaking, 1);
  assert.equal(total, 3);
  assert.match(detail, /1 of 3/);
});

test('growth names which ceiling each breakage hit', () => {
  const [breaking, , detail] = atGrowth([[45, 1000], [5, 9000]], 2);
  assert.equal(breaking, 2);
  assert.match(detail, /1 on the block count, 1 on the encoded size/);
});

test('a zero or negative growth factor breaks nothing', () => {
  assert.equal(atGrowth([[45, 4500]], 0)[0], 0);
  assert.equal(atGrowth([], 3)[1], 0);
});

test('distribution reports the tail and not the middle', () => {
  const samples = Array.from({ length: 8 }, () => [2, 200]);
  samples.push([40, 4000], [48, 4800]);
  const d = distribution(samples);
  assert.equal(d.n, 10);
  assert.equal(d.maxCount, 48);
  assert.equal(d.p90Count, 40);
  assert.equal(d.maxSize, 4800);
});

test('distribution of an empty sample is empty rather than an error', () => {
  assert.equal(distribution([]).n, 0);
  assert.equal(distribution(null).n, 0);
});

test('tightest finds the one message that decides', () => {
  const worst = tightest([[10, 1000], [40, 2000], [12, 12000]]);
  assert.equal(worst[1], 'size');
  assert.equal(worst[3], 12);
});
''',
"faq": [
 ("Is the 50-block limit really 50, or is it fewer in practice?",
  "The count is 50 for a message and 100 for a modal or a Home tab, and those are documented. What is not documented is that a payload can be refused well under 50 blocks because the encoded JSON is too large; rejections are widely reported to start around 13,000 characters. The script treats the count as a specification and the size as an observed figure you can override, because that is what each of them actually is."),
 ("Why does the script measure characters instead of bytes?",
  "Because the reported threshold is expressed in characters of encoded JSON and that is what people compare against. For ASCII content the two are the same number. For content with a lot of emoji or non-Latin text the byte count is larger, so if you are close to the ceiling with such content, treat the character measurement as the optimistic one and leave more room."),
 ("Can I just catch msg_blocks_too_long and retry with fewer blocks?",
  "You can, and as a last-resort safety net in the send path it is better than losing the message. It is a bad fix, though, because the truncation happens where nothing knows what was removed, so the digest silently drops content on precisely the days the content matters most. Cap in the generator, where you can count what you dropped and say so."),
 ("Should I thread the overflow or upload it as a file?",
  "Thread it when the extra content is more of the same and a reader might want to scroll it. Upload it when the extra content is bulk that nobody reads in a chat client, such as a full log or a diff. The deciding question is whether the overflow is more message or more artefact, and the two answers produce very different channels to live in."),
 ("Our messages are nowhere near 50 blocks. Do we still need this?",
  "Run it once. The number you want is not the block count, it is the growth multiple, and a generator that emits one block per item has a multiple that is entirely determined by how bad a day can get. If the tightest message in a week of history breaks at 1.4x, you have a problem that has not happened yet, and that is the only time it is cheap to fix."),
],
"related": [
 ("/slack/invalid-blocks/", "when a single block is the thing that is wrong"),
 ("/slack/text-length-limits/", "the per-field ceilings underneath this one"),
 ("/slack/files-upload-retired/", "before you make uploading the overflow your repair"),
],
"citations": [CITE_BLOCK_KIT, CITE_POSTMESSAGE, CITE_VIEWS_OPEN, CITE_UPLOAD],
})

GUIDES.append({
"slug": "blocks-without-text-fallback",
"title": "Blocks with no fallback text, so notifications are blank",
"description": "Nothing fails. The message posts, answers ok true and renders correctly, and the push notification, the sidebar preview and the screen reader all get nothing.",
"h1": "Blocks with no fallback text, so notifications are blank",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack blocks no text fallback", "slack notification says this content can't be displayed",
             "slack mobile push notification blank", "slack chat.postMessage text and blocks",
             "slack bot alerts useless on mobile"],
"deps": "Python 3.9+ with requests, or Node.js 18+; channels:history on the channels your app posts into",
"lead": "Somebody says the bot's alerts are useless on their phone. You open the channel and the messages are perfect: headers, coloured context lines, a button. You open the API logs and every call returned <code>ok: true</code>. Nothing has ever errored.</p><p>Then you look at your own lock screen. The push says the app's name and <em>This content can't be displayed</em>. The sidebar preview beside the channel is empty. Search finds nothing. The message is fine everywhere it is rendered as Block Kit, and it is blank everywhere it is not, which is most of the places anybody actually notices a message.",
"short_answer": """<p><code>text</code> is not the legacy alternative to <code>blocks</code>. It is the <strong>fallback string</strong>, and Slack uses it on every surface that cannot render Block Kit: mobile and desktop push notifications, the channel list preview, notification emails, search results, and screen readers. Send <code>blocks</code> without <code>text</code> and Slack accepts the message, renders it correctly in the channel, and has nothing to show anywhere else.</p>
<p>This is the only note in this batch where nothing fails. There is no error code, no <code>ok: false</code>, no rejected payload, no log line, and no metric that moves. The message succeeded. What degraded is a surface your sending code never sees, and the only place the evidence exists is in what your app has already posted.</p>
<p>So the detector is not looking for a failure - there isn't one. It reads your own messages back and <strong>renders the notification each of them produced</strong>, so you can look at the string a person on a phone was given. A payload with a zero-width space in <code>text</code>, or the literal word <code>message</code>, passes every check that tests for presence and fails the only test that matters.</p>""",
"problem": """<p>The reason this survives for years is that every feedback loop points away from it. The developer builds the message, looks at it in the channel, and it is beautiful. QA checks the channel. The screenshot in the pull request is of the channel. The monitoring checks that the call returned <code>ok</code>. Every one of those observations is of the one surface where the fallback is never used.</p>
<p>Meanwhile the failure is reported in language nobody can search for. "The alerts are useless on mobile." "I never know what the notification is about." "I stopped looking at them." That is not a bug report anybody files against a message builder, and when it is raised it sounds like a complaint about notification settings, so it gets routed to whoever owns notification settings and dies there.</p>
<p>The workarounds make it permanent. A team that hits the related <code>no_text</code> error - which Slack does return when attachments are in play and there is no text anywhere - fixes it by putting something in the field. A space. A zero-width space. The word <code>message</code>. The error goes away, the send succeeds, and the notification now says <code>message</code> instead of nothing, which is arguably worse because it looks deliberate.</p>
<p>And the cost is asymmetric. The people harmed are the ones reading on a phone during an incident, which is exactly the population and exactly the moment when a one-line summary is worth the most. An alerting system whose alerts do not survive the trip to a lock screen is not alerting anybody.</p>""",
"why": """<p><strong>The finding is not an error, so it has to be a rendering.</strong> There is no failure to report and no code to look up. The only output that changes anybody's mind is the actual notification string their users received, printed beside the message that looks perfect in the channel. That is why the central function returns a preview rather than a verdict.</p>
<p><strong>Presence is not the test.</strong> Every naive checker asks whether <code>text</code> is set. A zero-width space is set. The word <code>alert</code> is set. A JSON dump of the blocks is set. Each of those passes a presence check and produces a useless notification, so the classifier sorts a present string into <code>good</code>, <code>bulky</code>, <code>thin</code>, <code>placeholder</code> or <code>markup</code> and only one of those is fine.</p>
<p><strong>Slack has a preference order and the script has to model it.</strong> Message <code>text</code> comes first; an attachment's <code>fallback</code> is used when there is no message text. A checker that ignores attachments will report a degraded notification for a message whose notification is fine, and a finding that is wrong once is a finding nobody trusts again.</p>
<p><strong>A ratio is the argument, not an example.</strong> One bad message is a curiosity. "Ninety-one percent of what this app posted last week notifies as nothing" is a sentence that gets a builder function changed. The script reports the share and then shows the previews, in that order.</p>
<p><strong>The repair is an invariant, not an edit.</strong> Adding <code>text</code> to the seven call sites you can find fixes seven call sites. Making <code>text</code> a required positional argument of the function that builds messages fixes the eighth one, which somebody will write next month. The script prints the second repair because the first one does not hold.</p>
<p><strong>It costs nothing visually, which removes the only objection.</strong> The fallback is never rendered when the blocks display, so there is no design tradeoff to weigh and no reason to leave it out. This is unusually rare among quality findings and worth saying plainly.</p>""",
"steps": [
 {"h": "Read back what your app actually posted",
  "body": """<p><code>conversations.history</code> returns each message's stored <code>text</code>, <code>blocks</code> and <code>attachments</code> exactly as Slack holds them. Filter to your own <code>bot_id</code> from <code>auth.test</code>. This is the only place the evidence lives, because nothing in the send path recorded anything.</p>"""},
 {"h": "Judge the string, not its presence",
  "body": """<p><code>fallback_quality</code> strips zero-width characters before it decides anything, then sorts what is left. <code>absent</code>, <code>placeholder</code> and <code>markup</code> are the three that notify as nothing useful, and a presence check calls all three of them fine.</p>"""},
 {"h": "Let an attachment fallback count, because Slack does",
  "body": """<p>A message with no <code>text</code> but a real <code>fallback</code> on its attachment notifies correctly. <code>notification_preview</code> falls through to it and says where the string came from, so the report does not flag a message that is actually fine.</p>"""},
 {"h": "Render the notification instead of describing it",
  "body": """<p>The output is the string a person on a phone was shown: one line, whitespace collapsed, truncated the way a lock screen truncates. Seeing <em>This content can't be displayed</em> beside a screenshot of a perfectly rendered message is the thing that ends the argument.</p>"""},
 {"h": "Report the share before the examples",
  "body": """<p><code>coverage</code> returns how many of your own messages degrade and what fraction that is. Lead with the fraction. A list of twelve message timestamps invites somebody to fix twelve messages; a percentage invites them to fix the builder.</p>"""},
 {"h": "Make the summary a required argument",
  "body": """<p>The repair is one line of human text per message: <em>3 deploys failed in prod</em>. Put it in the signature of the function that builds your messages so it cannot be omitted, and the class of bug closes rather than shrinking.</p>"""},
],
"verify": """<p>Nothing about the send changes, so verification is the same read done again. The share should fall and the previews should start saying something.</p>
<pre><code class="language-bash">python3 slack_fallback_text.py --channel C01ABCDE9
# identity   U0APPBOT11 in acme
# coverage   34 of ours, 34 with blocks, 31 notify as nothing (91.2%)
# quality    absent           28  no text field at all beside a rendered blocks array
# quality    placeholder       3  the literal string "message"
# quality    good              3  a one line summary a reader can act on
# preview    ts=1735689600.001  degraded  "This content can't be displayed."
# preview    ts=1735689612.004  fine      "3 deploys failed in prod, oldest 14m ago"
#   repair: send text beside blocks, set to a one line human summary of the message</code></pre>""",
"code_intro": "Two pure functions and a reducer, and the interesting one does not return a verdict at all. <code>fallback_quality</code> sorts a present string into the five things it can be, because a zero-width space and a JSON dump both pass a presence check. <code>notification_preview</code> renders what the reader was actually shown, following Slack's own preference order down to an attachment fallback. <code>coverage</code> turns a page of history into the one number that changes a builder function.",
"py_file": "slack_fallback_text.py",
"py": '''"""Show the notification each of your app's messages actually produced.

Read only. auth.test for identity and conversations.history for what your app
posted. Nothing here failed and nothing is sent: every message this script
reports came back ok true, rendered correctly in the channel, and notified as
nothing. The finding is the notification string, printed beside a message that
looks perfect everywhere anybody thought to look.
"""
import argparse
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_fallback_text")

API = "https://slack.com/api/"

# What a reader is shown when Slack has blocks it cannot render on this surface
# and no fallback string to use instead. Reproduced so the report can show the
# notification rather than describe it.
DEGRADED = "This content can't be displayed."

# Characters that satisfy a presence check and say nothing. A zero-width space
# in text is the usual way a team makes a no_text error go away.
INVISIBLE = "\\u200b\\u200c\\u200d\\u2060\\ufeff"

# Strings that are present, non-empty, and tell a reader nothing at all. These
# are what people put in the field to silence the error rather than to inform
# anybody, and a presence check calls every one of them a pass.
PLACEHOLDERS = {
    "message", "new message", "notification", "alert", "update", "notice",
    "bot", "bot message", "attachment", "see message", "no text", "(no text)",
    "n/a", "na", "none", "null", "undefined", "-", ".", "..", "...",
}

# Below this a fallback cannot carry a fact. "Build" is present and useless.
THIN = 12
# Above this, or past this many lines, it is a document rather than a summary
# and the notification surface will cut it anyway.
BULKY = 400
BULKY_LINES = 4


def _clean(text):
    """Strip the characters that are present but invisible. Pure."""
    if text is None:
        return ""
    out = str(text)
    for ch in INVISIBLE:
        out = out.replace(ch, "")
    return out.strip()


def _first_fallback(attachments):
    """The first usable attachment fallback, which Slack will use. Pure."""
    for a in attachments or []:
        if isinstance(a, dict):
            candidate = _clean(a.get("fallback"))
            if candidate and candidate.lower() not in PLACEHOLDERS:
                return candidate
    return ""


def fallback_quality(text, blocks=None, attachments=None):
    """Judge the string Slack will use when Block Kit cannot be rendered. Pure.

    Returns (quality, detail): no-blocks, good, bulky, thin, placeholder,
    markup or absent. Presence is not the test. A zero-width space is present,
    the word "message" is present, and a JSON dump of the blocks is present,
    and all three notify as nothing worth reading.
    """
    has_blocks = isinstance(blocks, list) and len(blocks) > 0
    has_attachments = isinstance(attachments, list) and len(attachments) > 0
    clean = _clean(text)
    if not has_blocks and not has_attachments:
        if not clean:
            return ("absent", "no blocks and no text; there is no message here")
        return ("no-blocks", "no blocks, so text is the message itself and every "
                             "surface shows the same thing")
    if not clean:
        return ("absent", "blocks with no text field. Slack has nothing to put in a "
                          "push notification, a sidebar preview, a notification email "
                          "or a screen reader")
    if clean.lower() in PLACEHOLDERS:
        return ("placeholder", "text is %r, which is present, silences the no_text "
                               "error and tells a reader nothing" % clean[:40])
    if clean.startswith(("{", "[")) or '"type"' in clean or "\\\\u003c" in clean:
        return ("markup", "text looks like serialised block markup rather than a "
                          "sentence; the notification will show JSON")
    if len(clean) > BULKY or clean.count("\\n") >= BULKY_LINES:
        return ("bulky", "text is %d characters over %d line(s); a notification shows "
                         "one line, so most of this is cut and the first line has to "
                         "stand alone" % (len(clean), clean.count("\\n") + 1))
    if len(clean) < THIN:
        return ("thin", "text is %d characters (%r), which is present but too short "
                        "to carry what happened" % (len(clean), clean[:40]))
    return ("good", "a one line summary a reader can act on without opening Slack")


def notification_preview(text, blocks=None, attachments=None, width=110):
    """Render what the reader was actually shown. Pure.

    Returns (preview, degraded, source). Slack prefers the message text and
    falls through to an attachment's fallback, so this does too: flagging a
    message whose notification is fine is how a report stops being trusted.
    """
    quality, _ = fallback_quality(text, blocks, attachments)
    clean = _clean(text)
    if quality in ("good", "bulky", "thin", "no-blocks"):
        return (_one_line(clean, width), quality == "thin", "text")
    fallback = _first_fallback(attachments)
    if fallback:
        return (_one_line(fallback, width), False, "attachment.fallback")
    if quality == "placeholder":
        return (_one_line(clean, width), True, "text")
    if quality == "markup":
        return (_one_line(clean, width), True, "text")
    return (DEGRADED, True, "none")


def _one_line(text, width):
    """Collapse to the single line a lock screen has room for. Pure."""
    line = re.sub(r"\\s+", " ", str(text or "")).strip()
    if len(line) <= width:
        return line
    return line[:max(1, width - 3)].rstrip() + "..."


def coverage(messages, bot_id="", bot_user="", width=110):
    """Reduce a page of history to the share that notifies as nothing. Pure.

    The share is the argument. A list of timestamps invites somebody to fix
    twelve messages; a percentage invites them to fix the function that built
    all of them.
    """
    ours, carrying, degraded = 0, 0, 0
    by_quality = {}
    rows = []
    for m in messages or []:
        mine = (bot_id and m.get("bot_id") == bot_id) or (
            bot_user and m.get("user") == bot_user) or not (bot_id or bot_user)
        if not mine:
            continue
        ours += 1
        blocks, attachments = m.get("blocks"), m.get("attachments")
        if not (isinstance(blocks, list) and blocks):
            continue
        carrying += 1
        quality, detail = fallback_quality(m.get("text"), blocks, attachments)
        entry = by_quality.setdefault(quality, {"count": 0, "detail": detail})
        entry["count"] += 1
        preview, is_degraded, source = notification_preview(
            m.get("text"), blocks, attachments, width)
        if is_degraded:
            degraded += 1
        rows.append({"ts": m.get("ts"), "quality": quality, "preview": preview,
                     "degraded": is_degraded, "source": source})
    return {"authored": ours, "with_blocks": carrying, "degraded": degraded,
            "share_percent": round(degraded * 100.0 / carrying, 1) if carrying else 0.0,
            "by_quality": by_quality, "rows": rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel your app posts into; repeatable")
    ap.add_argument("--limit", type=int, default=200, help="messages read per channel")
    ap.add_argument("--width", type=int, default=110,
                    help="characters a notification surface has room for")
    ap.add_argument("--show", type=int, default=8,
                    help="how many rendered notifications to print per channel")
    args = ap.parse_args()

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s (channels:history is enough)", args.token_env)
        return 2
    if not args.channel:
        log.error("pass at least one --channel your app actually posts into")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    bot_id, bot_user = who.get("bot_id") or "", who.get("user_id") or ""
    log.info("identity   %s in %s", bot_user, who.get("team"))

    findings = 0
    for channel in args.channel:
        body = s.get(API + "conversations.history", timeout=30,
                     params={"channel": channel, "limit": str(args.limit)}).json()
        if body.get("ok") is not True:
            log.warning("history    unavailable    %s: %s", channel, body.get("error"))
            continue
        c = coverage(body.get("messages") or [], bot_id, bot_user, args.width)
        if not c["with_blocks"]:
            log.info("coverage   %s: nothing of ours used blocks here", channel)
            continue
        (log.warning if c["degraded"] else log.info)(
            "coverage   %s: %d of ours, %d with blocks, %d notify as nothing (%.1f%%)",
            channel, c["authored"], c["with_blocks"], c["degraded"], c["share_percent"])
        for quality, info in sorted(c["by_quality"].items(),
                                    key=lambda kv: (-kv[1]["count"], kv[0])):
            (log.info if quality in ("good", "no-blocks") else log.warning)(
                "quality    %-14s %4d  %s", quality, info["count"], info["detail"])
        for row in c["rows"][:max(0, args.show)]:
            (log.warning if row["degraded"] else log.info)(
                "preview    ts=%-18s %-8s from %-18s %r",
                row["ts"], "degraded" if row["degraded"] else "fine", row["source"],
                row["preview"])
        findings += c["degraded"]

    if findings:
        log.warning("  repair: send text beside blocks on every call, set to a one line "
                    "human summary such as '3 deploys failed in prod'")
        log.warning("  repair: make that summary a required argument of the function "
                    "that builds your messages, so the next call site cannot omit it")
        log.warning("  repair: for messages still using attachments, set fallback on "
                    "each one; it is the same idea one level down")
        log.warning("  note: nothing here failed. Every one of these messages returned "
                    "ok true and renders correctly in the channel")
        return 1
    log.info("verdict    clear          every message of ours carries a usable fallback")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-fallback-text.mjs",
"js": '''/**
 * Show the notification each of your app's messages actually produced.
 *
 * Read only. auth.test for identity and conversations.history for what your
 * app posted. Nothing here failed and nothing is sent: every message this
 * script reports came back ok true, rendered correctly in the channel, and
 * notified as nothing.
 */

const API = 'https://slack.com/api/';

// What a reader is shown when Slack has blocks it cannot render on this
// surface and no fallback string to use instead.
const DEGRADED = "This content can't be displayed.";

// Present, invisible, and enough to silence a no_text error.
const INVISIBLE = /[\\u200b\\u200c\\u200d\\u2060\\ufeff]/g;

// Present, non-empty, and useless. A presence check passes every one of these.
const PLACEHOLDERS = new Set(['message', 'new message', 'notification', 'alert',
  'update', 'notice', 'bot', 'bot message', 'attachment', 'see message', 'no text',
  '(no text)', 'n/a', 'na', 'none', 'null', 'undefined', '-', '.', '..', '...']);

const THIN = 12;
const BULKY = 400;
const BULKY_LINES = 4;

function clean(text) {
  if (text === null || text === undefined) return '';
  return String(text).replace(INVISIBLE, '').trim();
}

function firstFallback(attachments) {
  for (const a of attachments ?? []) {
    if (a && typeof a === 'object') {
      const candidate = clean(a.fallback);
      if (candidate && !PLACEHOLDERS.has(candidate.toLowerCase())) return candidate;
    }
  }
  return '';
}

/**
 * Judge the string Slack will use when Block Kit cannot be rendered. Pure.
 * Presence is not the test: a zero-width space is present, the word "message"
 * is present, and a JSON dump of the blocks is present.
 */
export function fallbackQuality(text, blocks = null, attachments = null) {
  const hasBlocks = Array.isArray(blocks) && blocks.length > 0;
  const hasAttachments = Array.isArray(attachments) && attachments.length > 0;
  const body = clean(text);
  if (!hasBlocks && !hasAttachments) {
    if (!body) return ['absent', 'no blocks and no text; there is no message here'];
    return ['no-blocks', 'no blocks, so text is the message itself and every surface ' +
      'shows the same thing'];
  }
  if (!body) {
    return ['absent', 'blocks with no text field. Slack has nothing to put in a push ' +
      'notification, a sidebar preview, a notification email or a screen reader'];
  }
  if (PLACEHOLDERS.has(body.toLowerCase())) {
    return ['placeholder', `text is "${body.slice(0, 40)}", which is present, silences ` +
      'the no_text error and tells a reader nothing'];
  }
  if (body.startsWith('{') || body.startsWith('[') || body.includes('"type"')) {
    return ['markup', 'text looks like serialised block markup rather than a sentence; ' +
      'the notification will show JSON'];
  }
  const lines = body.split('\\n').length;
  if (body.length > BULKY || lines > BULKY_LINES) {
    return ['bulky', `text is ${body.length} characters over ${lines} line(s); a ` +
      'notification shows one line, so most of this is cut and the first line has to ' +
      'stand alone'];
  }
  if (body.length < THIN) {
    return ['thin', `text is ${body.length} characters ("${body.slice(0, 40)}"), which ` +
      'is present but too short to carry what happened'];
  }
  return ['good', 'a one line summary a reader can act on without opening Slack'];
}

function oneLine(text, width) {
  const line = String(text ?? '').replace(/\\s+/g, ' ').trim();
  if (line.length <= width) return line;
  return `${line.slice(0, Math.max(1, width - 3)).trimEnd()}...`;
}

/**
 * Render what the reader was actually shown. Pure.
 * Returns [preview, degraded, source]. Slack prefers the message text and
 * falls through to an attachment's fallback, so this does too.
 */
export function notificationPreview(text, blocks = null, attachments = null, width = 110) {
  const [quality] = fallbackQuality(text, blocks, attachments);
  const body = clean(text);
  if (['good', 'bulky', 'thin', 'no-blocks'].includes(quality)) {
    return [oneLine(body, width), quality === 'thin', 'text'];
  }
  const fallback = firstFallback(attachments);
  if (fallback) return [oneLine(fallback, width), false, 'attachment.fallback'];
  if (quality === 'placeholder' || quality === 'markup') {
    return [oneLine(body, width), true, 'text'];
  }
  return [DEGRADED, true, 'none'];
}

/**
 * Reduce a page of history to the share that notifies as nothing. Pure.
 * The share is the argument; a list of timestamps invites somebody to fix
 * twelve messages instead of the function that built all of them.
 */
export function coverage(messages, botId = '', botUser = '', width = 110) {
  let authored = 0;
  let withBlocks = 0;
  let degraded = 0;
  const byQuality = new Map();
  const rows = [];
  for (const m of messages ?? []) {
    const mine = (botId && m.bot_id === botId) || (botUser && m.user === botUser)
      || !(botId || botUser);
    if (!mine) continue;
    authored += 1;
    const { blocks, attachments } = m;
    if (!Array.isArray(blocks) || !blocks.length) continue;
    withBlocks += 1;
    const [quality, detail] = fallbackQuality(m.text, blocks, attachments);
    if (!byQuality.has(quality)) byQuality.set(quality, { count: 0, detail });
    byQuality.get(quality).count += 1;
    const [preview, isDegraded, source] = notificationPreview(
      m.text, blocks, attachments, width);
    if (isDegraded) degraded += 1;
    rows.push({ ts: m.ts, quality, preview, degraded: isDegraded, source });
  }
  return { authored,
    withBlocks,
    degraded,
    sharePercent: withBlocks ? Math.round((degraded * 1000) / withBlocks) / 10 : 0,
    byQuality,
    rows };
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function argAll(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv} (channels:history is enough)`);
    process.exitCode = 2;
    return;
  }
  const channels = argAll(args, '--channel');
  if (!channels.length) {
    console.error('pass at least one --channel your app actually posts into');
    process.exitCode = 2;
    return;
  }
  const limit = arg(args, '--limit', '200');
  const width = Number(arg(args, '--width', '110'));
  const show = Number(arg(args, '--show', '8'));
  const headers = { Authorization: `Bearer ${token}` };

  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  const botId = who.bot_id ?? '';
  const botUser = who.user_id ?? '';
  console.log(`identity   ${botUser} in ${who.team}`);

  let findings = 0;
  for (const channel of channels) {
    const url = `${API}conversations.history?channel=${encodeURIComponent(channel)}` +
      `&limit=${encodeURIComponent(limit)}`;
    const body = await (await fetch(url, { headers })).json();
    if (body.ok !== true) {
      console.warn(`history    unavailable    ${channel}: ${body.error}`);
      continue;
    }
    const c = coverage(body.messages ?? [], botId, botUser, width);
    if (!c.withBlocks) {
      console.log(`coverage   ${channel}: nothing of ours used blocks here`);
      continue;
    }
    (c.degraded ? console.warn : console.log)(
      `coverage   ${channel}: ${c.authored} of ours, ${c.withBlocks} with blocks, ` +
      `${c.degraded} notify as nothing (${c.sharePercent}%)`);
    const ordered = [...c.byQuality.entries()].sort(
      (a, b) => b[1].count - a[1].count || a[0].localeCompare(b[0]));
    for (const [quality, info] of ordered) {
      (['good', 'no-blocks'].includes(quality) ? console.log : console.warn)(
        `quality    ${quality.padEnd(14)} ${String(info.count).padStart(4)}  ${info.detail}`);
    }
    for (const row of c.rows.slice(0, Math.max(0, show))) {
      (row.degraded ? console.warn : console.log)(
        `preview    ts=${String(row.ts).padEnd(18)} ` +
        `${(row.degraded ? 'degraded' : 'fine').padEnd(8)} from ` +
        `${row.source.padEnd(18)} "${row.preview}"`);
    }
    findings += c.degraded;
  }

  if (findings) {
    console.warn("  repair: send text beside blocks on every call, set to a one line " +
      "human summary such as '3 deploys failed in prod'");
    console.warn('  repair: make that summary a required argument of the function that ' +
      'builds your messages, so the next call site cannot omit it');
    console.warn('  repair: for messages still using attachments, set fallback on each ' +
      'one; it is the same idea one level down');
    console.warn('  note: nothing here failed. Every one of these messages returned ok ' +
      'true and renders correctly in the channel');
    process.exitCode = 1;
  } else {
    console.log('verdict    clear          every message of ours carries a usable fallback');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "These tests are mostly about the ways a message passes a presence check and still notifies as nothing: a zero-width space, the literal word <code>message</code>, a JSON dump. Each is asserted separately because each is a real thing a team has typed into that field to make an error go away. The other half protects the report's credibility in the other direction: a message with no <code>text</code> but a genuine attachment <code>fallback</code> must come back as fine, because a checker that cries wolf once is a checker nobody runs twice.",
"test_py_file": "test_slack_fallback_text.py",
"test_js_file": "slack-fallback-text.test.mjs",
"test_py": '''from slack_fallback_text import coverage, fallback_quality, notification_preview

BLOCKS = [{"type": "section", "text": {"type": "mrkdwn", "text": "*3 deploys failed*"}}]


def test_a_real_summary_beside_blocks_is_good():
    quality, _ = fallback_quality("3 deploys failed in prod, oldest 14m ago", BLOCKS)
    assert quality == "good"
    preview, degraded, source = notification_preview(
        "3 deploys failed in prod, oldest 14m ago", BLOCKS)
    assert degraded is False
    assert source == "text"
    assert preview.startswith("3 deploys failed")


def test_blocks_with_no_text_notify_as_nothing():
    quality, detail = fallback_quality(None, BLOCKS)
    assert quality == "absent"
    assert "push notification" in detail
    preview, degraded, source = notification_preview(None, BLOCKS)
    assert degraded is True
    assert source == "none"
    assert preview == "This content can't be displayed."


def test_a_zero_width_space_is_not_a_fallback():
    assert fallback_quality("\\u200b", BLOCKS)[0] == "absent"
    assert fallback_quality("   \\ufeff  ", BLOCKS)[0] == "absent"
    assert notification_preview("\\u200b", BLOCKS)[1] is True


def test_a_placeholder_word_is_present_and_useless():
    quality, detail = fallback_quality("message", BLOCKS)
    assert quality == "placeholder"
    assert "no_text" in detail
    preview, degraded, _ = notification_preview("Alert", BLOCKS)
    assert degraded is True
    assert preview == "Alert"


def test_a_json_dump_in_the_text_field_is_caught():
    dumped = '[{"type": "section", "text": {"type": "mrkdwn", "text": "hi"}}]'
    assert fallback_quality(dumped, BLOCKS)[0] == "markup"
    assert notification_preview(dumped, BLOCKS)[1] is True


def test_a_string_too_short_to_carry_a_fact_is_thin():
    quality, detail = fallback_quality("Build", BLOCKS)
    assert quality == "thin"
    assert "too short" in detail


def test_a_wall_of_text_is_bulky_rather_than_good():
    quality, detail = fallback_quality("x" * 500, BLOCKS)
    assert quality == "bulky"
    assert "one line" in detail
    assert fallback_quality("a\\nb\\nc\\nd\\ne\\nf", BLOCKS)[0] == "bulky"


def test_a_message_with_no_blocks_is_not_this_note():
    quality, detail = fallback_quality("just a plain message", None, None)
    assert quality == "no-blocks"
    assert "the message itself" in detail
    assert notification_preview("just a plain message")[1] is False


def test_an_attachment_fallback_rescues_a_message_with_no_text():
    attachments = [{"fallback": "3 deploys failed in prod"}]
    preview, degraded, source = notification_preview(None, BLOCKS, attachments)
    assert degraded is False
    assert source == "attachment.fallback"
    assert preview == "3 deploys failed in prod"


def test_a_placeholder_attachment_fallback_rescues_nothing():
    assert notification_preview(None, BLOCKS, [{"fallback": "message"}])[1] is True
    assert notification_preview(None, BLOCKS, [{"fallback": "  "}])[1] is True


def test_the_preview_is_one_line_and_truncated_the_way_a_lock_screen_truncates():
    preview, _, _ = notification_preview("a" * 200, BLOCKS, None, width=40)
    assert len(preview) == 40
    assert preview.endswith("...")
    assert notification_preview("two\\n\\nlines here now", BLOCKS)[0] == "two lines here now"


def test_coverage_reports_the_share_and_not_just_the_rows():
    messages = [
        {"ts": "1", "bot_id": "B1", "blocks": BLOCKS},
        {"ts": "2", "bot_id": "B1", "blocks": BLOCKS, "text": "message"},
        {"ts": "3", "bot_id": "B1", "blocks": BLOCKS,
         "text": "3 deploys failed in prod"},
        {"ts": "4", "bot_id": "B1", "text": "a plain message with no blocks"},
    ]
    c = coverage(messages, bot_id="B1")
    assert c["authored"] == 4
    assert c["with_blocks"] == 3
    assert c["degraded"] == 2
    assert c["share_percent"] == 66.7
    assert c["by_quality"]["absent"]["count"] == 1


def test_coverage_ignores_messages_that_are_not_ours():
    messages = [{"ts": "1", "bot_id": "B2", "blocks": BLOCKS},
                {"ts": "2", "user": "U9", "blocks": BLOCKS}]
    c = coverage(messages, bot_id="B1", bot_user="U1")
    assert c["authored"] == 0
    assert c["share_percent"] == 0.0


def test_an_empty_channel_is_not_a_finding():
    c = coverage([], bot_id="B1")
    assert c["with_blocks"] == 0
    assert c["degraded"] == 0
    assert c["share_percent"] == 0.0
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  coverage, fallbackQuality, notificationPreview,
} from './slack-fallback-text.mjs';

const BLOCKS = [{ type: 'section', text: { type: 'mrkdwn', text: '*3 deploys failed*' } }];

test('a real summary beside blocks is good', () => {
  assert.equal(fallbackQuality('3 deploys failed in prod, oldest 14m ago', BLOCKS)[0],
    'good');
  const [preview, degraded, source] = notificationPreview(
    '3 deploys failed in prod, oldest 14m ago', BLOCKS);
  assert.equal(degraded, false);
  assert.equal(source, 'text');
  assert.match(preview, /^3 deploys failed/);
});

test('blocks with no text notify as nothing', () => {
  const [quality, detail] = fallbackQuality(null, BLOCKS);
  assert.equal(quality, 'absent');
  assert.match(detail, /push notification/);
  const [preview, degraded, source] = notificationPreview(null, BLOCKS);
  assert.equal(degraded, true);
  assert.equal(source, 'none');
  assert.equal(preview, "This content can't be displayed.");
});

test('a zero width space is not a fallback', () => {
  assert.equal(fallbackQuality('\\u200b', BLOCKS)[0], 'absent');
  assert.equal(fallbackQuality('   \\ufeff  ', BLOCKS)[0], 'absent');
  assert.equal(notificationPreview('\\u200b', BLOCKS)[1], true);
});

test('a placeholder word is present and useless', () => {
  const [quality, detail] = fallbackQuality('message', BLOCKS);
  assert.equal(quality, 'placeholder');
  assert.match(detail, /no_text/);
  const [preview, degraded] = notificationPreview('Alert', BLOCKS);
  assert.equal(degraded, true);
  assert.equal(preview, 'Alert');
});

test('a json dump in the text field is caught', () => {
  const dumped = '[{"type": "section", "text": {"type": "mrkdwn", "text": "hi"}}]';
  assert.equal(fallbackQuality(dumped, BLOCKS)[0], 'markup');
  assert.equal(notificationPreview(dumped, BLOCKS)[1], true);
});

test('a string too short to carry a fact is thin', () => {
  const [quality, detail] = fallbackQuality('Build', BLOCKS);
  assert.equal(quality, 'thin');
  assert.match(detail, /too short/);
});

test('a wall of text is bulky rather than good', () => {
  const [quality, detail] = fallbackQuality('x'.repeat(500), BLOCKS);
  assert.equal(quality, 'bulky');
  assert.match(detail, /one line/);
  assert.equal(fallbackQuality('a\\nb\\nc\\nd\\ne\\nf', BLOCKS)[0], 'bulky');
});

test('a message with no blocks is not this note', () => {
  const [quality, detail] = fallbackQuality('just a plain message', null, null);
  assert.equal(quality, 'no-blocks');
  assert.match(detail, /the message itself/);
  assert.equal(notificationPreview('just a plain message')[1], false);
});

test('an attachment fallback rescues a message with no text', () => {
  const [preview, degraded, source] = notificationPreview(
    null, BLOCKS, [{ fallback: '3 deploys failed in prod' }]);
  assert.equal(degraded, false);
  assert.equal(source, 'attachment.fallback');
  assert.equal(preview, '3 deploys failed in prod');
});

test('a placeholder attachment fallback rescues nothing', () => {
  assert.equal(notificationPreview(null, BLOCKS, [{ fallback: 'message' }])[1], true);
  assert.equal(notificationPreview(null, BLOCKS, [{ fallback: '  ' }])[1], true);
});

test('the preview is one line and truncated the way a lock screen truncates', () => {
  const [preview] = notificationPreview('a'.repeat(200), BLOCKS, null, 40);
  assert.equal(preview.length, 40);
  assert.ok(preview.endsWith('...'));
  assert.equal(notificationPreview('two\\n\\nlines here now', BLOCKS)[0],
    'two lines here now');
});

test('coverage reports the share and not just the rows', () => {
  const messages = [
    { ts: '1', bot_id: 'B1', blocks: BLOCKS },
    { ts: '2', bot_id: 'B1', blocks: BLOCKS, text: 'message' },
    { ts: '3', bot_id: 'B1', blocks: BLOCKS, text: '3 deploys failed in prod' },
    { ts: '4', bot_id: 'B1', text: 'a plain message with no blocks' },
  ];
  const c = coverage(messages, 'B1');
  assert.equal(c.authored, 4);
  assert.equal(c.withBlocks, 3);
  assert.equal(c.degraded, 2);
  assert.equal(c.sharePercent, 66.7);
  assert.equal(c.byQuality.get('absent').count, 1);
});

test('coverage ignores messages that are not ours', () => {
  const c = coverage([{ ts: '1', bot_id: 'B2', blocks: BLOCKS },
    { ts: '2', user: 'U9', blocks: BLOCKS }], 'B1', 'U1');
  assert.equal(c.authored, 0);
  assert.equal(c.sharePercent, 0);
});

test('an empty channel is not a finding', () => {
  const c = coverage([], 'B1');
  assert.equal(c.withBlocks, 0);
  assert.equal(c.degraded, 0);
  assert.equal(c.sharePercent, 0);
});
''',
"faq": [
 ("If nothing fails, is this actually a bug?",
  "It is a bug with no failure signal, which is a category worth naming. The message is delivered and rendered, so nothing in your monitoring can see it, and the people affected experience it as the product being bad rather than as something being broken. The absence of an error is what makes it last for years, not evidence that it does not matter."),
 ("Will the text field show up twice if I send both?",
  "No. When Slack renders the blocks, the text field is not displayed at all. It is used only on surfaces that cannot render Block Kit. That is the unusual thing about this fix: there is no visual tradeoff to weigh, so the only reason to leave it out is not knowing what the field is for."),
 ("We put a zero-width space in text to stop a no_text error. Is that a problem?",
  "It is the specific case this script was written to catch. The zero-width space satisfies the API, so the error stops, and the notification is now empty rather than being rejected. The script strips those characters before it judges anything, which is why a message that passes every presence check in your codebase can still come back as absent here."),
 ("What should the fallback actually say?",
  "One line that would be useful on a lock screen with Slack closed: the fact and the count. &quot;3 deploys failed in prod&quot; rather than &quot;Deploy notification&quot; and rather than the whole message repeated. If a reader could decide whether to open their laptop from that line alone, it is doing its job."),
 ("Does the same thing apply to attachments?",
  "Yes, one level down. An attachment's fallback string plays the same role for that attachment, and Slack will use it when there is no message-level text, which is why this script checks it before reporting a message as degraded. If you are still on attachments, set fallback on each one, and treat that as a stopgap while you move to blocks."),
],
"related": [
 ("/slack/invalid-blocks/", "the same builder, on the days it does fail loudly"),
 ("/slack/message-subtypes-ignored/", "the other note where nothing errors and the data is wrong"),
 ("/slack/duplicate-messages-no-dedupe/", "another message quality problem only your history shows"),
],
"citations": [CITE_POSTMESSAGE, CITE_BLOCK_KIT, CITE_CONV_HISTORY, CITE_RETRIEVING],
})

GUIDES.append({
"slug": "text-length-limits",
"title": "Block Kit field ceilings: some reject, some truncate",
"description": "A section text at 3,001 characters kills the whole message. A 41,000 character text is quietly cut. Measure every field before the long stack trace arrives.",
"h1": "Block Kit field ceilings: some reject, some truncate",
"category": "Slack",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["slack section text 3000 character limit",
             "slack block kit character limits", "slack header text 150 characters",
             "slack invalid_blocks long text", "slack message truncated no error"],
"deps": "Python 3.9+ with requests, or Node.js 18+; no token at all if you measure a payload file",
"lead": "The alert works for months. Then a service produces a stack trace instead of a one-line error, the formatter interpolates it into a <code>section</code>, and the message is refused with <code>invalid_blocks</code>. The block is the right shape. The message is nowhere near 50 blocks. One field is 3,140 characters long and the ceiling is 3,000.</p><p>The confusing part comes next: some fields behave completely differently. A message <code>text</code> of 41,000 characters is not refused, it is cut, and nobody is told. So the same class of mistake produces a loud failure in one field and a silent one in another, which is why this never quite feels like one problem.",
"short_answer": """<p>Block Kit enforces a character ceiling on every text-bearing field, and exceeding one invalidates the whole message. The ones that bite are <code>section.text</code> and each entry of <code>section.fields</code> at <strong>3,000</strong>, <code>header.text</code> at <strong>150</strong>, a button label and a <code>context</code> element at <strong>75</strong>, an option label at <strong>75</strong> and its value at <strong>150</strong>, an input label at <strong>2,000</strong>, and <code>block_id</code> and <code>action_id</code> at <strong>255</strong>.</p>
<p>The message-level <code>text</code> field is the exception that causes the confusion: at around <strong>40,000</strong> characters it is <em>truncated</em> rather than rejected. So the behaviour on overflow is per field, not global, and the two behaviours want two different responses. A rejection is an incident you find immediately. A truncation is a message that looks complete and is not, which nobody finds at all.</p>
<p>This is a measurement, not an inspection, so it runs with no token: hand the script a payload and it walks every text-bearing field, holds it against its ceiling, and says which fields are over, which are within ten percent, and for each one whether Slack rejects or cuts.</p>""",
"problem": """<p>What makes this expensive is that it fires on content rather than on code. The formatter is correct. The template is correct. The tests pass, because the fixtures in the tests are short. The message breaks the day something real is longer than the thing you wrote the test with, and the things that get long are exactly the things you most want in the alert: a stack trace, a diff, a query plan, a list of the forty failing checks.</p>
<p>Then the two behaviours pull the investigation in opposite directions. When a <code>section</code> is over, the failure is loud and immediate and lands in the same <code>invalid_blocks</code> bucket as every structural fault, so the first hour goes into checking the shape of a payload whose shape is perfect. When a message <code>text</code> is over, there is no failure at all: the message posts, the last third is gone, and the report reads as complete because the part that would have said otherwise is the part that was removed.</p>
<p>The small ceilings catch people the other way round. Nobody expects a header to be limited to 150 characters, because headers are short by convention, so the one place a header is built from a user-supplied string is the one place it is unbounded. A <code>context</code> element at 75 characters is smaller than a single sentence. And <code>action_id</code> at 255 catches teams who encode state into the identifier, which works beautifully until the encoded state is a long one.</p>
<p>None of this is visible from a message that worked. A field sitting at 2,900 of 3,000 characters renders identically to one at 300. The distance to the ceiling is invisible in the product and only exists as a number somebody has to go and measure.</p>""",
"why": """<p><strong>Reject and truncate are the same mistake with opposite symptoms, and the report has to say which.</strong> A finding that says "over the limit" and stops sends a team looking for an error that, for half these fields, was never raised. Every row this script prints carries the behaviour beside the number.</p>
<p><strong>It is a measurement, so it needs nothing from Slack.</strong> The ceilings are published and the payload is yours. Running this against a file is a unit test for your message builder, and that is the right place for it: the check that runs before the send costs nothing, and the one that runs after costs a message.</p>
<p><strong>Proximity is the finding, not just overflow.</strong> A field at 2,950 of 3,000 has already broken for somebody whose stack trace was fifty characters longer than the one you sampled. The default flags anything inside ten percent of its ceiling, because the interesting report is the one delivered before the incident.</p>
<p><strong>The path matters more than the number.</strong> <code>blocks[4].fields[7].text</code> tells you which interpolation to bound. "A field is too long" tells you to go and read a payload. The walker keeps the full path on every row for exactly that reason.</p>
<p><strong>Truncation must be defensive and visible.</strong> Cutting at the ceiling produces a message that ends mid-word and claims to be whole. Cutting below it and appending an explicit marker plus a link to the full content produces a message that is honest about being a summary, and the difference is one line in the builder.</p>
<p><strong>Never interpolate unbounded output into a block.</strong> That is the rule the whole note reduces to. A log line, a stack trace, a user-supplied name or an LLM response has no length you control, and a block field does. Bound it where the two meet.</p>""",
"steps": [
 {"h": "Measure the payload, with no token and no call",
  "body": """<p><code>--payload</code> takes the JSON your builder produced and walks it. This belongs in the test suite for the message builder, run against the longest fixture you can find rather than the tidiest one.</p>"""},
 {"h": "Keep the full path on every row",
  "body": """<p><code>measure_blocks</code> reports <code>blocks[4].fields[7].text</code> rather than "a section field". The path is what tells you which interpolation to bound, and it is the difference between a fix and a search.</p>"""},
 {"h": "Read the behaviour column, not only the number",
  "body": """<p><code>ceiling_verdict</code> returns <code>over-rejects</code> or <code>over-truncates</code>, never a bare "over". One of those explains an error you saw; the other explains a message that looked fine and was not, and going looking for an error that was never raised is a wasted afternoon.</p>"""},
 {"h": "Treat ten percent of headroom as a finding",
  "body": """<p>Anything inside the margin comes back <code>at-risk</code>. That is the row worth acting on, because it is the one that has not cost anything yet. A payload with no <code>at-risk</code> rows is a payload with genuine slack in it.</p>"""},
 {"h": "Let the message-level text be the exception it is",
  "body": """<p><code>message.text</code> is measured at about 40,000 characters with a <code>truncate</code> behaviour, and the report says so explicitly. It is the one field where being over does not stop the send, and the only one where the damage is invisible.</p>"""},
 {"h": "Bound at the builder, with a marker and a link",
  "body": """<p>Cut below the ceiling, append something that says it was cut, and link to the whole thing. Uploading long content as a file and referencing it from a short block is the version of this that scales, and it is the only version that keeps the full text available at all.</p>"""},
],
"verify": """<p>Bound the interpolation, run the measurement again on the same fixture, and the worst row should move from <code>over-rejects</code> to <code>ok</code> without anything being sent.</p>
<pre><code class="language-bash">python3 slack_block_field_limits.py --payload alert-with-trace.json
# payload    6 block(s), 14 measured field(s)
# worst      reject         blocks[2].text is 3140 of 3000 (section.text): Slack refuses
#                           the entire message on this field alone
# at-risk    blocks[0].text 142 of 150 (header.text), 94.7% of the ceiling
# summary    section.text max 3140/3000, header.text max 142/150, action_id max 31/255
#   repair: truncate below the ceiling in the builder, append an explicit marker, and
#           link to the full content rather than inlining it</code></pre>""",
"code_intro": "One table and three pure functions. The table is the block reference expressed as ceilings and, for each ceiling, what Slack does when you cross it. <code>measure_blocks</code> walks a payload and keeps the full path on every row. <code>ceiling_verdict</code> refuses to say a bare &quot;over&quot;: it says <code>over-rejects</code> or <code>over-truncates</code>, because those are two different afternoons. <code>worst</code> picks the field that decides the message's fate, preferring a rejection over a truncation when both are present.",
"py_file": "slack_block_field_limits.py",
"py": '''"""Hold every text-bearing field in a Block Kit payload against its ceiling.

Read only, and with --payload it holds no token and calls nothing. Nothing is
sent from here: discovering which field is too long by posting the message is
the loop this replaces. The ceilings are published and the payload is yours, so
this is a measurement rather than a request.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("slack_block_field_limits")

API = "https://slack.com/api/"

# field kind -> (ceiling, what Slack does when you cross it).
#
# The behaviour column is the reason this table exists rather than a set of
# constants. Every reject row is an invalid_blocks you will see within seconds.
# The one truncate row is a message that posts, looks complete, and is not, and
# nobody is told. Reporting those two as one thing sends half the readers
# looking for an error that was never raised.
LIMITS = {
    "message.text": (40000, "truncate"),
    "section.text": (3000, "reject"),
    "section.field": (3000, "reject"),
    "header.text": (150, "reject"),
    "context.text": (75, "reject"),
    "button.text": (75, "reject"),
    "button.url": (3000, "reject"),
    "button.value": (2000, "reject"),
    "option.text": (75, "reject"),
    "option.value": (150, "reject"),
    "placeholder.text": (150, "reject"),
    "input.label": (2000, "reject"),
    "input.hint": (2000, "reject"),
    "image.alt_text": (2000, "reject"),
    "image.title": (2000, "reject"),
    "block_id": (255, "reject"),
    "action_id": (255, "reject"),
}

TEXT_TYPES = {"plain_text", "mrkdwn"}

# Inside this share of a ceiling, a field has not failed yet and will. The
# report that is worth reading is the one delivered before the incident.
MARGIN = 0.1


def _length(value):
    """The measured length of a text object or a bare string. Pure."""
    if isinstance(value, dict):
        return len(str(value.get("text") or ""))
    if isinstance(value, str):
        return len(value)
    return None


def _add(rows, path, kind, value):
    n = _length(value)
    if n is None:
        return
    limit, behaviour = LIMITS[kind]
    rows.append((path, kind, n, limit, behaviour))


def _measure_option(opt, path, rows):
    if not isinstance(opt, dict):
        return
    _add(rows, path + ".text", "option.text", opt.get("text"))
    if opt.get("value") is not None:
        _add(rows, path + ".value", "option.value", opt.get("value"))


def _measure_element(el, path, rows):
    """Everything measurable inside one interactive element. Pure."""
    if not isinstance(el, dict):
        return
    etype = str(el.get("type") or "")
    if el.get("action_id") is not None:
        _add(rows, path + ".action_id", "action_id", el.get("action_id"))
    if etype == "button":
        _add(rows, path + ".text", "button.text", el.get("text"))
        if el.get("url") is not None:
            _add(rows, path + ".url", "button.url", el.get("url"))
        if el.get("value") is not None:
            _add(rows, path + ".value", "button.value", el.get("value"))
    elif etype == "image":
        _add(rows, path + ".alt_text", "image.alt_text", el.get("alt_text"))
    elif etype in TEXT_TYPES:
        _add(rows, path + ".text", "context.text", el)
    if el.get("placeholder") is not None:
        _add(rows, path + ".placeholder", "placeholder.text", el.get("placeholder"))
    for i, opt in enumerate(el.get("options") or []):
        _measure_option(opt, "%s.options[%d]" % (path, i), rows)
    for gi, group in enumerate(el.get("option_groups") or []):
        if not isinstance(group, dict):
            continue
        _add(rows, "%s.option_groups[%d].label" % (path, gi), "placeholder.text",
             group.get("label"))
        for i, opt in enumerate(group.get("options") or []):
            _measure_option(opt, "%s.option_groups[%d].options[%d]" % (path, gi, i), rows)


def _measure_block(block, path, rows):
    if not isinstance(block, dict):
        return
    if block.get("block_id") is not None:
        _add(rows, path + ".block_id", "block_id", block.get("block_id"))
    btype = str(block.get("type") or "")
    if btype == "section":
        _add(rows, path + ".text", "section.text", block.get("text"))
        for i, field in enumerate(block.get("fields") or []):
            _add(rows, "%s.fields[%d].text" % (path, i), "section.field", field)
        if block.get("accessory") is not None:
            _measure_element(block["accessory"], path + ".accessory", rows)
    elif btype == "header":
        _add(rows, path + ".text", "header.text", block.get("text"))
    elif btype == "image":
        _add(rows, path + ".alt_text", "image.alt_text", block.get("alt_text"))
        if block.get("title") is not None:
            _add(rows, path + ".title", "image.title", block.get("title"))
    elif btype == "context":
        for i, el in enumerate(block.get("elements") or []):
            _measure_element(el, "%s.elements[%d]" % (path, i), rows)
    elif btype == "input":
        _add(rows, path + ".label", "input.label", block.get("label"))
        if block.get("hint") is not None:
            _add(rows, path + ".hint", "input.hint", block.get("hint"))
        if block.get("element") is not None:
            _measure_element(block["element"], path + ".element", rows)
    else:
        for i, el in enumerate(block.get("elements") or []):
            _measure_element(el, "%s.elements[%d]" % (path, i), rows)
        if block.get("accessory") is not None:
            _measure_element(block["accessory"], path + ".accessory", rows)


def measure_blocks(blocks, text=None):
    """Every length-limited field in a payload, with its full path. Pure.

    Rows are (path, kind, length, limit, behaviour). The path is the point:
    blocks[4].fields[7].text names the interpolation to bound, while "a section
    field is too long" only tells you to go and read a payload.
    """
    rows = []
    if text is not None:
        _add(rows, "message.text", "message.text", text)
    for i, block in enumerate(blocks or []):
        _measure_block(block, "blocks[%d]" % i, rows)
    return rows


def ceiling_verdict(length, kind, margin=MARGIN):
    """Where one field stands against its ceiling. Pure.

    Returns (verdict, detail) and never a bare "over": over-rejects and
    over-truncates are two different afternoons, and a report that merges them
    sends half its readers hunting for an error that was never raised.
    """
    known = LIMITS.get(kind)
    if known is None:
        return ("unmeasured", "%s has no ceiling in this table; check the block "
                              "reference by hand" % kind)
    limit, behaviour = known
    n = int(length or 0)
    if n > limit and behaviour == "reject":
        return ("over-rejects", "%d of %d characters: Slack refuses the entire message "
                                "on this field alone, with invalid_blocks and no "
                                "indication of which field" % (n, limit))
    if n > limit:
        return ("over-truncates", "%d of %d characters: this is not rejected, it is "
                                  "cut. The message posts, looks complete, and the end "
                                  "is gone with nobody told" % (n, limit))
    if limit and n >= limit * (1 - margin):
        return ("at-risk", "%d of %d characters, %.1f%% of the ceiling. This has not "
                           "failed yet and will, for somebody whose input is slightly "
                           "longer than yours" % (n, limit, 100.0 * n / limit))
    return ("ok", "%d of %d characters" % (n, limit))


def worst(rows, margin=MARGIN):
    """The field that decides the message's fate. Pure.

    A rejection outranks a truncation when both are present, because one of
    them stops the send and the other only spoils it.
    """
    order = {"over-rejects": 0, "over-truncates": 1, "at-risk": 2, "unmeasured": 3,
             "ok": 4}
    best = None
    for row in rows or []:
        path, kind, length, _, _ = row
        verdict, detail = ceiling_verdict(length, kind, margin)
        rank = (order.get(verdict, 5), -float(length or 0))
        if best is None or rank < best[0]:
            best = (rank, verdict, row, detail)
    if best is None:
        return ("clear", None, "no length-limited fields in this payload")
    _, verdict, row, detail = best
    if verdict == "ok":
        return ("clear", row, "every measured field has room; the longest is %s at %s"
                % (row[0], detail))
    return (verdict, row, "%s (%s): %s" % (row[0], row[1], detail))


def summarise(rows):
    """The longest field observed per kind, for the report. Pure."""
    out = {}
    for path, kind, length, limit, behaviour in rows or []:
        current = out.get(kind)
        if current is None or length > current["length"]:
            out[kind] = {"length": length, "limit": limit, "behaviour": behaviour,
                         "path": path}
    return out


def audit(blocks, text, margin, label):
    rows = measure_blocks(blocks, text)
    log.info("payload    %s: %d block(s), %d measured field(s)", label,
             len(blocks or []), len(rows))
    verdict, row, detail = worst(rows, margin)
    (log.info if verdict == "clear" else log.warning)(
        "worst      %-16s %s", verdict, detail)
    at_risk = 0
    for path, kind, length, _, _ in rows:
        state, why = ceiling_verdict(length, kind, margin)
        if state == "at-risk":
            at_risk += 1
            log.warning("at-risk    %-16s %s (%s): %s", "", path, kind, why)
    for kind, info in sorted(summarise(rows).items()):
        log.info("summary    %-18s max %d of %d (%s), at %s", kind, info["length"],
                 info["limit"], info["behaviour"], info["path"])
    return verdict, at_risk


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--payload", default="",
                    help="a JSON file holding a blocks array or a whole message; "
                         "with this the script needs no Slack token at all")
    ap.add_argument("--token-env", default="SLACK_BOT_TOKEN",
                    help="environment variable holding the bot token")
    ap.add_argument("--channel", action="append", default=[],
                    help="a channel your app posts into; repeatable")
    ap.add_argument("--limit", type=int, default=200, help="messages read per channel")
    ap.add_argument("--margin", type=float, default=MARGIN,
                    help="share of a ceiling within which a field counts as at risk")
    args = ap.parse_args()

    if args.payload:
        raw = json.loads(open(args.payload, encoding="utf-8").read())
        blocks = raw if isinstance(raw, list) else (raw or {}).get("blocks")
        text = None if isinstance(raw, list) else (raw or {}).get("text")
        verdict, at_risk = audit(blocks, text, args.margin, args.payload)
        if verdict.startswith("over") or at_risk:
            log.warning("  repair: truncate below the ceiling in the builder, append an "
                        "explicit marker so the cut is visible, and link to the full "
                        "content rather than inlining it")
            log.warning("  repair: never interpolate unbounded output into a block; a "
                        "stack trace, a diff or a user supplied name has no length you "
                        "control and a block field does")
            return 1
        return 0

    token = os.environ.get(args.token_env)
    if not token:
        log.error("set %s, or pass --payload to measure a file with no token at all",
                  args.token_env)
        return 2
    if not args.channel:
        log.error("pass at least one --channel, or --payload")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + token})
    who = s.get(API + "auth.test", timeout=30).json()
    if who.get("ok") is not True:
        log.error("auth.test  unavailable    %s", who.get("error"))
        return 2
    bot_id = who.get("bot_id") or ""
    log.info("identity   %s in %s", who.get("user_id"), who.get("team"))

    findings = 0
    for channel in args.channel:
        body = s.get(API + "conversations.history", timeout=30,
                     params={"channel": channel, "limit": str(args.limit)}).json()
        if body.get("ok") is not True:
            log.warning("history    unavailable    %s: %s", channel, body.get("error"))
            continue
        for m in body.get("messages") or []:
            if not m.get("blocks"):
                continue
            if bot_id and m.get("bot_id") != bot_id:
                continue
            verdict, at_risk = audit(m.get("blocks"), m.get("text"), args.margin,
                                     "%s ts=%s" % (channel, m.get("ts")))
            if verdict.startswith("over") or at_risk:
                findings += 1

    if findings:
        log.warning("  repair: bound every interpolation in the message builder, at a "
                    "length below the ceiling, with a visible marker on the cut")
        log.warning("  repair: for genuinely long content, upload it and reference it "
                    "from a short block instead of inlining it")
        return 1
    log.info("verdict    clear          every measured field has room left")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "slack-block-field-limits.mjs",
"js": '''/**
 * Hold every text-bearing field in a Block Kit payload against its ceiling.
 *
 * Read only, and with --payload it holds no token and calls nothing. Nothing is
 * sent from here: discovering which field is too long by posting the message is
 * the loop this replaces. The ceilings are published and the payload is yours,
 * so this is a measurement rather than a request.
 */

import { readFile } from 'node:fs/promises';

const API = 'https://slack.com/api/';

// field kind -> [ceiling, what Slack does when you cross it].
// The behaviour column is the reason this is a table rather than a set of
// constants: every reject row is an invalid_blocks you see in seconds, and the
// one truncate row is a message that posts, looks complete, and is not.
const LIMITS = new Map([
  ['message.text', [40000, 'truncate']],
  ['section.text', [3000, 'reject']],
  ['section.field', [3000, 'reject']],
  ['header.text', [150, 'reject']],
  ['context.text', [75, 'reject']],
  ['button.text', [75, 'reject']],
  ['button.url', [3000, 'reject']],
  ['button.value', [2000, 'reject']],
  ['option.text', [75, 'reject']],
  ['option.value', [150, 'reject']],
  ['placeholder.text', [150, 'reject']],
  ['input.label', [2000, 'reject']],
  ['input.hint', [2000, 'reject']],
  ['image.alt_text', [2000, 'reject']],
  ['image.title', [2000, 'reject']],
  ['block_id', [255, 'reject']],
  ['action_id', [255, 'reject']],
]);

const TEXT_TYPES = new Set(['plain_text', 'mrkdwn']);

const MARGIN = 0.1;

function lengthOf(value) {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return String(value.text ?? '').length;
  }
  if (typeof value === 'string') return value.length;
  return null;
}

function add(rows, path, kind, value) {
  const n = lengthOf(value);
  if (n === null) return;
  const [limit, behaviour] = LIMITS.get(kind);
  rows.push([path, kind, n, limit, behaviour]);
}

function measureOption(opt, path, rows) {
  if (!opt || typeof opt !== 'object') return;
  add(rows, `${path}.text`, 'option.text', opt.text);
  if (opt.value !== undefined && opt.value !== null) {
    add(rows, `${path}.value`, 'option.value', opt.value);
  }
}

function measureElement(el, path, rows) {
  if (!el || typeof el !== 'object' || Array.isArray(el)) return;
  const etype = String(el.type ?? '');
  if (el.action_id !== undefined && el.action_id !== null) {
    add(rows, `${path}.action_id`, 'action_id', el.action_id);
  }
  if (etype === 'button') {
    add(rows, `${path}.text`, 'button.text', el.text);
    if (el.url !== undefined && el.url !== null) add(rows, `${path}.url`, 'button.url', el.url);
    if (el.value !== undefined && el.value !== null) {
      add(rows, `${path}.value`, 'button.value', el.value);
    }
  } else if (etype === 'image') {
    add(rows, `${path}.alt_text`, 'image.alt_text', el.alt_text);
  } else if (TEXT_TYPES.has(etype)) {
    add(rows, `${path}.text`, 'context.text', el);
  }
  if (el.placeholder !== undefined && el.placeholder !== null) {
    add(rows, `${path}.placeholder`, 'placeholder.text', el.placeholder);
  }
  (el.options ?? []).forEach((opt, i) => measureOption(opt, `${path}.options[${i}]`, rows));
  (el.option_groups ?? []).forEach((group, gi) => {
    if (!group || typeof group !== 'object') return;
    add(rows, `${path}.option_groups[${gi}].label`, 'placeholder.text', group.label);
    (group.options ?? []).forEach((opt, i) => measureOption(
      opt, `${path}.option_groups[${gi}].options[${i}]`, rows));
  });
}

function measureBlock(block, path, rows) {
  if (!block || typeof block !== 'object' || Array.isArray(block)) return;
  if (block.block_id !== undefined && block.block_id !== null) {
    add(rows, `${path}.block_id`, 'block_id', block.block_id);
  }
  const btype = String(block.type ?? '');
  if (btype === 'section') {
    add(rows, `${path}.text`, 'section.text', block.text);
    (block.fields ?? []).forEach((field, i) => add(
      rows, `${path}.fields[${i}].text`, 'section.field', field));
    if (block.accessory) measureElement(block.accessory, `${path}.accessory`, rows);
  } else if (btype === 'header') {
    add(rows, `${path}.text`, 'header.text', block.text);
  } else if (btype === 'image') {
    add(rows, `${path}.alt_text`, 'image.alt_text', block.alt_text);
    if (block.title) add(rows, `${path}.title`, 'image.title', block.title);
  } else if (btype === 'context') {
    (block.elements ?? []).forEach((el, i) => measureElement(
      el, `${path}.elements[${i}]`, rows));
  } else if (btype === 'input') {
    add(rows, `${path}.label`, 'input.label', block.label);
    if (block.hint) add(rows, `${path}.hint`, 'input.hint', block.hint);
    if (block.element) measureElement(block.element, `${path}.element`, rows);
  } else {
    (block.elements ?? []).forEach((el, i) => measureElement(
      el, `${path}.elements[${i}]`, rows));
    if (block.accessory) measureElement(block.accessory, `${path}.accessory`, rows);
  }
}

/**
 * Every length-limited field in a payload, with its full path. Pure.
 * Rows are [path, kind, length, limit, behaviour].
 */
export function measureBlocks(blocks, text = null) {
  const rows = [];
  if (text !== null && text !== undefined) add(rows, 'message.text', 'message.text', text);
  (blocks ?? []).forEach((block, i) => measureBlock(block, `blocks[${i}]`, rows));
  return rows;
}

/**
 * Where one field stands against its ceiling. Pure.
 * Never returns a bare "over": over-rejects and over-truncates are two
 * different afternoons.
 */
export function ceilingVerdict(length, kind, margin = MARGIN) {
  const known = LIMITS.get(kind);
  if (!known) {
    return ['unmeasured',
      `${kind} has no ceiling in this table; check the block reference by hand`];
  }
  const [limit, behaviour] = known;
  const n = Number(length ?? 0);
  if (n > limit && behaviour === 'reject') {
    return ['over-rejects', `${n} of ${limit} characters: Slack refuses the entire ` +
      'message on this field alone, with invalid_blocks and no indication of which field'];
  }
  if (n > limit) {
    return ['over-truncates', `${n} of ${limit} characters: this is not rejected, it ` +
      'is cut. The message posts, looks complete, and the end is gone with nobody told'];
  }
  if (limit && n >= limit * (1 - margin)) {
    return ['at-risk', `${n} of ${limit} characters, ${(100 * n / limit).toFixed(1)}% ` +
      'of the ceiling. This has not failed yet and will, for somebody whose input is ' +
      'slightly longer than yours'];
  }
  return ['ok', `${n} of ${limit} characters`];
}

/**
 * The field that decides the message's fate. Pure.
 * A rejection outranks a truncation: one stops the send, the other spoils it.
 */
export function worst(rows, margin = MARGIN) {
  const order = { 'over-rejects': 0, 'over-truncates': 1, 'at-risk': 2, unmeasured: 3, ok: 4 };
  let best = null;
  for (const row of rows ?? []) {
    const [, kind, length] = row;
    const [verdict, detail] = ceilingVerdict(length, kind, margin);
    const rank = [order[verdict] ?? 5, -Number(length ?? 0)];
    if (best === null || rank[0] < best.rank[0]
      || (rank[0] === best.rank[0] && rank[1] < best.rank[1])) {
      best = { rank, verdict, row, detail };
    }
  }
  if (best === null) return ['clear', null, 'no length-limited fields in this payload'];
  if (best.verdict === 'ok') {
    return ['clear', best.row,
      `every measured field has room; the longest is ${best.row[0]} at ${best.detail}`];
  }
  return [best.verdict, best.row, `${best.row[0]} (${best.row[1]}): ${best.detail}`];
}

/** The longest field observed per kind, for the report. Pure. */
export function summarise(rows) {
  const out = new Map();
  for (const [path, kind, length, limit, behaviour] of rows ?? []) {
    const current = out.get(kind);
    if (!current || length > current.length) {
      out.set(kind, { length, limit, behaviour, path });
    }
  }
  return out;
}

function auditPayload(blocks, text, margin, label) {
  const rows = measureBlocks(blocks, text);
  console.log(`payload    ${label}: ${(blocks ?? []).length} block(s), ` +
    `${rows.length} measured field(s)`);
  const [verdict, , detail] = worst(rows, margin);
  (verdict === 'clear' ? console.log : console.warn)(
    `worst      ${verdict.padEnd(16)} ${detail}`);
  let atRisk = 0;
  for (const [path, kind, length] of rows) {
    const [state, why] = ceilingVerdict(length, kind, margin);
    if (state === 'at-risk') {
      atRisk += 1;
      console.warn(`at-risk    ${''.padEnd(16)} ${path} (${kind}): ${why}`);
    }
  }
  for (const [kind, info] of [...summarise(rows).entries()].sort()) {
    console.log(`summary    ${kind.padEnd(18)} max ${info.length} of ${info.limit} ` +
      `(${info.behaviour}), at ${info.path}`);
  }
  return [verdict, atRisk];
}

function arg(args, name, fallback = null) {
  const i = args.indexOf(name);
  return i === -1 ? fallback : args[i + 1];
}

function argAll(args, name) {
  const out = [];
  for (let i = 0; i < args.length; i += 1) {
    if (args[i] === name && args[i + 1] !== undefined) out.push(args[i + 1]);
  }
  return out;
}

async function main() {
  const args = process.argv.slice(2);
  const margin = Number(arg(args, '--margin', String(MARGIN)));
  const payload = arg(args, '--payload', '');

  if (payload) {
    const raw = JSON.parse(await readFile(payload, 'utf8'));
    const blocks = Array.isArray(raw) ? raw : (raw ?? {}).blocks;
    const text = Array.isArray(raw) ? null : (raw ?? {}).text;
    const [verdict, atRisk] = auditPayload(blocks, text, margin, payload);
    if (verdict.startsWith('over') || atRisk) {
      console.warn('  repair: truncate below the ceiling in the builder, append an ' +
        'explicit marker so the cut is visible, and link to the full content rather ' +
        'than inlining it');
      console.warn('  repair: never interpolate unbounded output into a block; a stack ' +
        'trace, a diff or a user supplied name has no length you control and a block ' +
        'field does');
      process.exitCode = 1;
    }
    return;
  }

  const tokenEnv = arg(args, '--token-env', 'SLACK_BOT_TOKEN');
  const token = process.env[tokenEnv];
  if (!token) {
    console.error(`set ${tokenEnv}, or pass --payload to measure a file with no token`);
    process.exitCode = 2;
    return;
  }
  const channels = argAll(args, '--channel');
  if (!channels.length) {
    console.error('pass at least one --channel, or --payload');
    process.exitCode = 2;
    return;
  }
  const limit = arg(args, '--limit', '200');
  const headers = { Authorization: `Bearer ${token}` };

  const who = await (await fetch(`${API}auth.test`, { headers })).json();
  if (who.ok !== true) {
    console.error(`auth.test  unavailable    ${who.error}`);
    process.exitCode = 2;
    return;
  }
  const botId = who.bot_id ?? '';
  console.log(`identity   ${who.user_id} in ${who.team}`);

  let findings = 0;
  for (const channel of channels) {
    const url = `${API}conversations.history?channel=${encodeURIComponent(channel)}` +
      `&limit=${encodeURIComponent(limit)}`;
    const body = await (await fetch(url, { headers })).json();
    if (body.ok !== true) {
      console.warn(`history    unavailable    ${channel}: ${body.error}`);
      continue;
    }
    for (const m of body.messages ?? []) {
      if (!m.blocks) continue;
      if (botId && m.bot_id !== botId) continue;
      const [verdict, atRisk] = auditPayload(m.blocks, m.text, margin,
        `${channel} ts=${m.ts}`);
      if (verdict.startsWith('over') || atRisk) findings += 1;
    }
  }

  if (findings) {
    console.warn('  repair: bound every interpolation in the message builder, at a ' +
      'length below the ceiling, with a visible marker on the cut');
    console.warn('  repair: for genuinely long content, upload it and reference it from ' +
      'a short block instead of inlining it');
    process.exitCode = 1;
  } else {
    console.log('verdict    clear          every measured field has room left');
  }
}

// Only run when invoked directly, so importing this module in the tests does
// not execute main() and fail the file on a missing token.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The assertion the whole note rests on is that <code>message.text</code> at 41,000 characters comes back <code>over-truncates</code> while a section at 3,001 comes back <code>over-rejects</code>. Those are the two behaviours that make this feel like two unrelated problems, and a checker that reports both as &quot;over&quot; is why. The rest keep the walker honest: a field nested three levels down inside an option group still arrives with a path you can act on, and a payload with nothing measurable is reported as such rather than as clean.",
"test_py_file": "test_slack_block_field_limits.py",
"test_js_file": "slack-block-field-limits.test.mjs",
"test_py": '''from slack_block_field_limits import (ceiling_verdict, measure_blocks, summarise,
                                       worst)


def section(text):
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def test_a_section_over_three_thousand_rejects_the_whole_message():
    verdict, detail = ceiling_verdict(3001, "section.text")
    assert verdict == "over-rejects"
    assert "entire message" in detail


def test_the_message_text_field_is_cut_rather_than_refused():
    verdict, detail = ceiling_verdict(41000, "message.text")
    assert verdict == "over-truncates"
    assert "nobody told" in detail


def test_a_field_inside_the_margin_is_at_risk_before_it_fails():
    verdict, detail = ceiling_verdict(2950, "section.text")
    assert verdict == "at-risk"
    assert "has not failed yet" in detail
    assert ceiling_verdict(2000, "section.text")[0] == "ok"


def test_the_margin_is_adjustable():
    assert ceiling_verdict(2500, "section.text", margin=0.2)[0] == "at-risk"
    assert ceiling_verdict(2500, "section.text", margin=0.1)[0] == "ok"


def test_the_small_ceilings_are_the_ones_nobody_expects():
    assert ceiling_verdict(151, "header.text")[0] == "over-rejects"
    assert ceiling_verdict(76, "button.text")[0] == "over-rejects"
    assert ceiling_verdict(76, "context.text")[0] == "over-rejects"
    assert ceiling_verdict(256, "action_id")[0] == "over-rejects"


def test_a_kind_with_no_ceiling_is_unmeasured_rather_than_ok():
    verdict, detail = ceiling_verdict(10, "video.description")
    assert verdict == "unmeasured"
    assert "by hand" in detail


def test_measure_keeps_the_full_path_on_every_row():
    rows = measure_blocks([{"type": "section",
                            "fields": [{"type": "mrkdwn", "text": "a"},
                                       {"type": "mrkdwn", "text": "bb"}]}])
    assert [r[0] for r in rows] == ["blocks[0].fields[0].text", "blocks[0].fields[1].text"]
    assert rows[1][2] == 2
    assert rows[0][1] == "section.field"


def test_measure_reaches_a_button_inside_an_actions_block():
    blocks = [{"type": "actions", "block_id": "b1", "elements": [
        {"type": "button", "action_id": "go", "value": "x",
         "text": {"type": "plain_text", "text": "Approve"}}]}]
    rows = dict((r[0], r) for r in measure_blocks(blocks))
    assert rows["blocks[0].block_id"][1] == "block_id"
    assert rows["blocks[0].elements[0].action_id"][2] == 2
    assert rows["blocks[0].elements[0].text"][1] == "button.text"
    assert rows["blocks[0].elements[0].value"][3] == 2000


def test_measure_reaches_an_option_inside_an_option_group():
    blocks = [{"type": "actions", "elements": [
        {"type": "static_select",
         "placeholder": {"type": "plain_text", "text": "pick"},
         "option_groups": [{"label": {"type": "plain_text", "text": "g"},
                            "options": [{"text": {"type": "plain_text", "text": "one"},
                                         "value": "1"}]}]}]}]
    paths = [r[0] for r in measure_blocks(blocks)]
    assert "blocks[0].elements[0].option_groups[0].options[0].text" in paths
    assert "blocks[0].elements[0].placeholder" in paths


def test_context_elements_are_measured_at_seventy_five():
    blocks = [{"type": "context", "elements": [{"type": "mrkdwn", "text": "x" * 80}]}]
    row = measure_blocks(blocks)[0]
    assert row[1] == "context.text"
    assert row[3] == 75
    assert ceiling_verdict(row[2], row[1])[0] == "over-rejects"


def test_the_message_text_is_measured_when_it_is_supplied():
    rows = measure_blocks([section("hi")], text="a summary")
    assert rows[0][0] == "message.text"
    assert rows[0][4] == "truncate"


def test_worst_prefers_a_rejection_over_a_truncation():
    rows = measure_blocks([section("x" * 3100)], text="y" * 41000)
    verdict, row, detail = worst(rows)
    assert verdict == "over-rejects"
    assert row[0] == "blocks[0].text"
    assert "section.text" in detail


def test_worst_reports_a_lone_truncation_as_a_truncation():
    assert worst(measure_blocks([section("ok")], text="y" * 41000))[0] == "over-truncates"


def test_a_payload_with_room_is_clear_and_names_its_longest_field():
    verdict, row, detail = worst(measure_blocks([section("hello")]))
    assert verdict == "clear"
    assert row[0] == "blocks[0].text"
    assert "every measured field has room" in detail


def test_a_payload_with_nothing_measurable_says_so():
    verdict, row, detail = worst(measure_blocks([{"type": "divider"}]))
    assert verdict == "clear"
    assert row is None
    assert "no length-limited fields" in detail


def test_summarise_reports_the_longest_of_each_kind():
    rows = measure_blocks([section("x" * 10), section("y" * 40)])
    got = summarise(rows)
    assert got["section.text"]["length"] == 40
    assert got["section.text"]["path"] == "blocks[1].text"
    assert got["section.text"]["behaviour"] == "reject"
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ceilingVerdict, measureBlocks, summarise, worst,
} from './slack-block-field-limits.mjs';

const section = (text) => ({ type: 'section', text: { type: 'mrkdwn', text } });

test('a section over three thousand rejects the whole message', () => {
  const [verdict, detail] = ceilingVerdict(3001, 'section.text');
  assert.equal(verdict, 'over-rejects');
  assert.match(detail, /entire message/);
});

test('the message text field is cut rather than refused', () => {
  const [verdict, detail] = ceilingVerdict(41000, 'message.text');
  assert.equal(verdict, 'over-truncates');
  assert.match(detail, /nobody told/);
});

test('a field inside the margin is at risk before it fails', () => {
  const [verdict, detail] = ceilingVerdict(2950, 'section.text');
  assert.equal(verdict, 'at-risk');
  assert.match(detail, /has not failed yet/);
  assert.equal(ceilingVerdict(2000, 'section.text')[0], 'ok');
});

test('the margin is adjustable', () => {
  assert.equal(ceilingVerdict(2500, 'section.text', 0.2)[0], 'at-risk');
  assert.equal(ceilingVerdict(2500, 'section.text', 0.1)[0], 'ok');
});

test('the small ceilings are the ones nobody expects', () => {
  assert.equal(ceilingVerdict(151, 'header.text')[0], 'over-rejects');
  assert.equal(ceilingVerdict(76, 'button.text')[0], 'over-rejects');
  assert.equal(ceilingVerdict(76, 'context.text')[0], 'over-rejects');
  assert.equal(ceilingVerdict(256, 'action_id')[0], 'over-rejects');
});

test('a kind with no ceiling is unmeasured rather than ok', () => {
  const [verdict, detail] = ceilingVerdict(10, 'video.description');
  assert.equal(verdict, 'unmeasured');
  assert.match(detail, /by hand/);
});

test('measure keeps the full path on every row', () => {
  const rows = measureBlocks([{ type: 'section', fields: [
    { type: 'mrkdwn', text: 'a' }, { type: 'mrkdwn', text: 'bb' }] }]);
  assert.deepEqual(rows.map((r) => r[0]),
    ['blocks[0].fields[0].text', 'blocks[0].fields[1].text']);
  assert.equal(rows[1][2], 2);
  assert.equal(rows[0][1], 'section.field');
});

test('measure reaches a button inside an actions block', () => {
  const blocks = [{ type: 'actions', block_id: 'b1', elements: [{ type: 'button',
    action_id: 'go', value: 'x', text: { type: 'plain_text', text: 'Approve' } }] }];
  const rows = new Map(measureBlocks(blocks).map((r) => [r[0], r]));
  assert.equal(rows.get('blocks[0].block_id')[1], 'block_id');
  assert.equal(rows.get('blocks[0].elements[0].action_id')[2], 2);
  assert.equal(rows.get('blocks[0].elements[0].text')[1], 'button.text');
  assert.equal(rows.get('blocks[0].elements[0].value')[3], 2000);
});

test('measure reaches an option inside an option group', () => {
  const blocks = [{ type: 'actions', elements: [{ type: 'static_select',
    placeholder: { type: 'plain_text', text: 'pick' },
    option_groups: [{ label: { type: 'plain_text', text: 'g' },
      options: [{ text: { type: 'plain_text', text: 'one' }, value: '1' }] }] }] }];
  const paths = measureBlocks(blocks).map((r) => r[0]);
  assert.ok(paths.includes('blocks[0].elements[0].option_groups[0].options[0].text'));
  assert.ok(paths.includes('blocks[0].elements[0].placeholder'));
});

test('context elements are measured at seventy five', () => {
  const blocks = [{ type: 'context',
    elements: [{ type: 'mrkdwn', text: 'x'.repeat(80) }] }];
  const row = measureBlocks(blocks)[0];
  assert.equal(row[1], 'context.text');
  assert.equal(row[3], 75);
  assert.equal(ceilingVerdict(row[2], row[1])[0], 'over-rejects');
});

test('the message text is measured when it is supplied', () => {
  const rows = measureBlocks([section('hi')], 'a summary');
  assert.equal(rows[0][0], 'message.text');
  assert.equal(rows[0][4], 'truncate');
});

test('worst prefers a rejection over a truncation', () => {
  const rows = measureBlocks([section('x'.repeat(3100))], 'y'.repeat(41000));
  const [verdict, row, detail] = worst(rows);
  assert.equal(verdict, 'over-rejects');
  assert.equal(row[0], 'blocks[0].text');
  assert.match(detail, /section\\.text/);
});

test('worst reports a lone truncation as a truncation', () => {
  assert.equal(worst(measureBlocks([section('ok')], 'y'.repeat(41000)))[0],
    'over-truncates');
});

test('a payload with room is clear and names its longest field', () => {
  const [verdict, row, detail] = worst(measureBlocks([section('hello')]));
  assert.equal(verdict, 'clear');
  assert.equal(row[0], 'blocks[0].text');
  assert.match(detail, /every measured field has room/);
});

test('a payload with nothing measurable says so', () => {
  const [verdict, row, detail] = worst(measureBlocks([{ type: 'divider' }]));
  assert.equal(verdict, 'clear');
  assert.equal(row, null);
  assert.match(detail, /no length-limited fields/);
});

test('summarise reports the longest of each kind', () => {
  const got = summarise(measureBlocks([section('x'.repeat(10)), section('y'.repeat(40))]));
  assert.equal(got.get('section.text').length, 40);
  assert.equal(got.get('section.text').path, 'blocks[1].text');
  assert.equal(got.get('section.text').behaviour, 'reject');
});
''',
"faq": [
 ("Is the section limit 3,000 characters or 3,000 bytes?",
  "It is characters, and for anything outside the Latin alphabet that distinction is worth holding onto: a message of Japanese text or emoji is well under the ceiling by character count and much larger on the wire. The character measurement is the one the ceiling uses, so it is the one this script reports, but if you are close to the limit with such content, leave more room than the number suggests."),
 ("Why does the message text field truncate when everything else rejects?",
  "Because it predates Block Kit and behaves like the field it always was. It is the fallback string, and Slack would rather show a cut summary on a notification than refuse the whole message over one. The practical consequence is the one worth remembering: a section that is too long tells you immediately, and a fallback that is too long tells you nothing at all."),
 ("Should I truncate at exactly the ceiling?",
  "No, cut below it and say that you did. Truncating at exactly 3,000 characters produces a message that ends mid-word and gives a reader no way to tell whether anything is missing. Cutting at 2,900 with an explicit marker and a link to the full content costs one line in the builder and makes the message honest about what it is."),
 ("Which field catches teams out most often?",
  "Two, and for opposite reasons. Section text, because that is where log output and stack traces are interpolated, and header text at 150, because headers are short by convention so nobody thinks to bound the one that is built from a user-supplied string. The 255 on action_id is a distant third and only bites teams who encode state into it."),
 ("Can I check this without a Slack token?",
  "Yes, and that is how it is meant to be used. Pass --payload with the JSON your builder produced and nothing here talks to Slack at all. The ceilings are published, the payload is yours, and the whole check belongs in your test suite pointed at the longest fixture you have rather than the tidiest."),
],
"related": [
 ("/slack/invalid-blocks/", "the same error string, from a structural rule instead"),
 ("/slack/msg-blocks-too-long/", "the ceiling one level up, on the whole message"),
 ("/slack/blocks-without-text-fallback/", "the other field on this payload nobody sets"),
],
"citations": [CITE_COMPOSITION, CITE_BLOCKS, CITE_POSTMESSAGE, CITE_WEB_API],
})

