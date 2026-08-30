#!/usr/bin/env python3
"""/github/ field notes, batch O — the writing.

Four more webhook notes into a section that already publishes ten, so each one
had to earn its place against the nine before it rather than against the blank
page.

The first is about the encoding of the body rather than anything in it. A hook
left on its default content type wraps the event JSON inside a urlencoded
payload= field, and a receiver written for application/json either rejects it or,
much worse, accepts it and parses nothing. The tolerant case is the reason for
the note: it answers 200, so the delivery log is spotless and the failure audit
that already exists in this section finds nothing at all.

The second is the only note in the section whose subject is not the hook. The
hook is fine; the firewall in front of the receiver is holding a copy of
GitHub's published source ranges that somebody pasted out of the documentation
once. GET /meta is the authoritative current list, it needs no token, and the
comparison is CIDR arithmetic against a file the caller supplies, because the
one thing the GitHub API can never read is your own network.

The third is deliberately the opposite of the note about a hook with no secret.
Here the secret is set, has always been set, and has never once been changed.
The API will not tell you a secret's age, so the note is honest about working
from a proxy: updated_at moves on any edit, which makes it conclusive in exactly
one direction, and the script says which direction it is arguing in. It also
reconciles the hook against a rotation date the caller claims, which is how you
find the rotation that updated the receiver and never reached GitHub.

The fourth moves up a level. A GitHub App's webhook is configured on the App,
not per installation, and it can be blank or still pointed at the smee.io proxy
from the tutorial. Nothing fails, because nothing is attempted: there are no
failed deliveries where there are no deliveries.

Read only throughout, and one of the four does not authenticate at all.
"""

CITE_REPO_HOOKS = ("Repository webhooks — GitHub REST API",
                   "https://docs.github.com/en/rest/repos/webhooks")
CITE_VALIDATING = ("Validating webhook deliveries — GitHub Docs",
                   "https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries")
CITE_CREATING_WEBHOOKS = ("Creating webhooks — GitHub Docs",
                          "https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks")
CITE_TROUBLESHOOT = ("Troubleshooting webhooks — GitHub Docs",
                     "https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/troubleshooting-webhooks")
CITE_WEBHOOK_BEST = ("Best practices for using webhooks — GitHub Docs",
                     "https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks")
CITE_FAILED_DELIVERIES = ("Handling failed webhook deliveries — GitHub Docs",
                          "https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries")
CITE_META = ("Meta — GitHub REST API",
             "https://docs.github.com/en/rest/meta/meta")
CITE_IP_ADDRESSES = ("About GitHub's IP addresses — GitHub Docs",
                     "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-githubs-ip-addresses")
CITE_APP_WEBHOOKS = ("App webhooks — GitHub REST API",
                     "https://docs.github.com/en/rest/apps/webhooks")
CITE_APPS_REST = ("Apps — GitHub REST API",
                  "https://docs.github.com/en/rest/apps/apps")
CITE_APP_AUTH = ("Authenticating as a GitHub App — GitHub Docs",
                 "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app")
CITE_APP_WEBHOOK_SETUP = ("Using webhooks with GitHub Apps — GitHub Docs",
                          "https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/using-webhooks-with-github-apps")

GUIDES = [

{
"slug": "webhook-content-type-mismatch",
"title": "The hook sends form-encoded bodies to a JSON receiver",
"description": "config.content_type defaults to form, which wraps the event in a payload= field. A strict receiver returns 400; a tolerant one returns 200 and does nothing.",
"h1": "the hook sends form-encoded bodies to a JSON receiver",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github webhook content_type form vs json",
             "github webhook payload= form encoded body",
             "github webhook application/x-www-form-urlencoded parse error",
             "github webhook json parse error 400 receiver",
             "github webhook signature form encoded raw body"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The handler is written, deployed and subscribed to the right event. GitHub says the delivery succeeded. Your receiver says it got a request and found nothing in it &mdash; or says nothing at all, because it returned 200 having parsed an empty object out of a body it never understood. Every field in the hook looks right, because the field that is wrong is the one nobody reads.",
"short_answer": """<p>Read <code>GET /repos/{owner}/{repo}/hooks</code> and look at <code>config.content_type</code>. There are two values: <code>json</code>, which posts the event as an <code>application/json</code> body, and <code>form</code>, which posts <code>application/x-www-form-urlencoded</code> with the entire event JSON stuffed into a single <code>payload=</code> field. <code>form</code> is the default, so a hook created without naming the value is a form hook, and the field is absent from <code>config</code> rather than set to anything you would notice.</p>
<p>Confirm it on a real delivery: <code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}</code> returns <code>request.headers</code>, and the <code>content-type</code> there is what GitHub actually sent. The body it recorded shows the same thing from the other side &mdash; a form delivery arrives as one <code>payload</code> key holding a JSON string, not as the event object your handler expects. What no API read can tell you is what your receiver parses, so the script takes that from you and says which half it measured and which half it was told.</p>""",
"problem": """<p>The symptom depends entirely on which web framework is underneath, which is why two teams with the same misconfiguration describe completely different bugs. A strict JSON parser refuses the body and the delivery is recorded with a 400, which at least points somewhere. A tolerant one shrugs, hands the handler an empty dictionary or a dictionary with one strange key in it, and the handler falls through every branch it has and returns 200. GitHub records a successful delivery. Your metrics record a successful request. Nothing anywhere records that the event was dropped.</p>
<p>That second case is what makes this expensive. The existing advice for a webhook that is not working is to read the delivery log, and the delivery log is green. So the investigation moves on to the things that are usually wrong: is the hook subscribed to the event, is the URL right, is the receiver deployed, is there a second hook somewhere sending to the old host. All of those get checked, all of them come back clean, and the check that would have taken one line never happens because <code>content_type</code> is not a field anybody has ever had a reason to look at.</p>
<p>Then somebody adds a log line to the receiver, sees a request body starting <code>payload=%7B%22action%22%3A</code>, and the whole thing resolves in a minute. The second half of the repair is the part that catches people out afterwards. Signature verification is computed over the exact bytes of the request, and on a form hook those bytes are the urlencoded wrapper. A receiver that url-decodes first, or that re-serialises the parsed object and hashes that, has been verifying nothing meaningful; switching the hook to <code>json</code> changes the bytes and can turn a passing signature check into a failing one on the same deploy that fixes the parse.</p>""",
"why": """<p><strong>Form is the default, and defaults are invisible.</strong> A hook created through the API without a <code>content_type</code> is a form hook, and <code>config</code> comes back without the key rather than with <code>"form"</code> in it. Anything auditing the hook by eye sees a URL, a secret and an events array, all correct, and no field at all where the problem is. The web UI shows a dropdown with the same default, already collapsed.</p>
<p><strong>The event is not the body, it is a field inside the body.</strong> A form delivery is a single urlencoded parameter, <code>payload</code>, whose value is the JSON document as a string. Your handler is not receiving a slightly different shape of the same object; it is receiving a different document entirely, one level of encoding out. That is why nothing partially works: no field your code reads exists at the top level of what arrived.</p>
<p><strong>A 200 is not evidence of anything here.</strong> Many frameworks answer a body they cannot parse with a default value rather than an exception, and the handler then does nothing successfully. This is the specific reason this note exists next to <a href="/github/webhook-deliveries-failing/">the delivery failure audit</a>: that audit groups attempts by status code and needs a non-OK status to find anything. Here the status is fine and the finding is in the request half of the record, not the response half.</p>
<p><strong>The signature is over the bytes, whichever bytes they are.</strong> <code>X-Hub-Signature-256</code> is the HMAC of the raw request body. On a form hook that is <code>payload=</code> followed by the percent-encoded document. A verifier written against the raw bytes is correct in both worlds and survives the change. A verifier that parses first and hashes a re-serialisation is broken in both worlds, and only finds out when the encoding moves. Fix the encoding and the verifier in the same change, in that order, and redeliver one event to check.</p>
<p><strong>The receiver's parser is not readable from here.</strong> This is the section's standing blind spot: the API describes what GitHub sends and never what you do with it. The script reads the configured encoding, and it reads the real <code>content-type</code> header and the recorded body shape from a sample of deliveries, so the sending half is measured rather than assumed. The receiving half is a flag you set, and the output labels it as declared rather than observed.</p>""",
"steps": [
 {"h": "Read the field nobody reads",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks</code> and look at <code>config.content_type</code> on each hook. Treat an absent key as <code>form</code>, because that is what it means. This one read is usually the whole diagnosis, and it costs a single request against a quota you can check for free.</p>"""},
 {"h": "Confirm on a delivery rather than trusting the config",
  "body": """<p>List deliveries with <code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries</code>, then fetch a handful of individual records. Only the individual record carries <code>request.headers</code> and <code>request.payload</code>. The <code>content-type</code> header is what GitHub sent; a body recorded as a single <code>payload</code> key holding a string is the wrapper, seen from the receiving end.</p>"""},
 {"h": "Say what your receiver actually parses",
  "body": """<p>The script takes <code>--receiver json</code> or <code>--receiver form</code>, because it cannot read your code. Answer it from the framework, not from intent: a handler that reads <code>request.json</code>, <code>await req.json()</code> or <code>json.loads(body)</code> is a JSON receiver whatever the comment above it says. If you genuinely do not know, leave it out and the script reports the encoding and the risk without claiming a mismatch.</p>"""},
 {"h": "Look for the parse statuses, and do not rely on them",
  "body": """<p>Count how many recent deliveries came back 400, 415 or 422. A run of those is a strict parser refusing the body, and it confirms the finding immediately. Zero of them confirms nothing at all, because the tolerant case answers 200. The script reports the count as corroboration and never as the test.</p>"""},
 {"h": "Change the encoding and the verifier together",
  "body": """<p>Set <code>config.content_type</code> to <code>json</code>, and in the same change make signature verification read the raw request bytes before any parsing happens. Then redeliver one event from the delivery log and watch it land. Doing only the first half moves a receiver that was quietly dropping events to one that rejects them loudly, which is progress but is not a working integration.</p>"""},
],
"verify": """<p>The check is cheap enough to keep in a deploy script, and it answers the same way whether or not anything has failed.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$RO_TOKEN python3 github_hook_content_type.py --repo acme/payments --receiver json
# hook 4218871 https://hooks.example.com/github content_type=form (default, key absent)
# deliveries sampled: 5, form content-type header on 5, payload= wrapper on 5
# parse statuses (400/415/422): 0 of 40 recent deliveries
# form-to-json: the hook sends application/x-www-form-urlencoded and the receiver
# was declared as JSON. Every event arrives wrapped in a payload= field.
# repair: set config.content_type to json, and verify the signature over the raw
# request bytes before parsing, in the same change.

# after the hook is switched to json
# consistent-json: the hook sends application/json and the receiver parses JSON.</code></pre>""",
"code_intro": "Everything that decides is pure, and everything impure is three GETs. The one judgement call in the whole script is what to do with an absent <code>content_type</code>, and it resolves it to <code>form</code> rather than to unknown, because that is the documented default and the single most common way this happens. The verdict function never lets a clean status code argue the finding away, and it keeps what it read separate from what it was told.",
"py_file": "github_hook_content_type.py",
"py": '''"""Say whether a webhook sends a body encoding its receiver cannot read.

Read only. Three kinds of GET: the hook list, for config.content_type; the
delivery list, for recent attempts; and a few individual delivery records, which
are the only place the request headers and the recorded body appear. Nothing is
created, edited or redelivered.

config.content_type defaults to form, which wraps the event JSON inside a
urlencoded payload= field. A receiver written for application/json either
rejects that body or, much more expensively, accepts it and parses nothing while
answering 200.

The API cannot see what your receiver parses. That half is declared with
--receiver and the output says which half was measured and which was told.

Environment:

    GITHUB_TOKEN   a read-only token with access to the repository
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_content_type")

API = "https://api.github.com"
UA = "github-hook-content-type/1.0"

FORM = "form"
JSON = "json"
# The documented default. A hook created without naming a content type is a form
# hook, and config comes back with the key absent rather than set.
DEFAULT_CONTENT_TYPE = FORM
# The statuses a strict parser answers a body it cannot read with. Corroboration
# only: the tolerant frameworks answer 200 and this count stays at zero.
PARSE_STATUSES = (400, 415, 422)


def content_type_of(config):
    """The hook's configured body encoding, normalised. Pure.

    An absent key is not unknown, it is form. Reporting it as unknown would lose
    the most common way a hook ends up form-encoded, which is nobody choosing.
    """
    if not isinstance(config, dict):
        return "unknown"
    raw = config.get("content_type")
    if raw is None:
        return DEFAULT_CONTENT_TYPE
    value = str(raw).strip().lower()
    if value in ("json", "application/json"):
        return JSON
    if value in ("form", "application/x-www-form-urlencoded"):
        return FORM
    return "unknown"


def content_type_was_explicit(config):
    """Whether the hook names its encoding or inherits the default. Pure."""
    return isinstance(config, dict) and config.get("content_type") is not None


def header_of(headers, name):
    """One header from a delivery record, case-insensitively. Pure."""
    if not isinstance(headers, dict):
        return None
    wanted = str(name).strip().lower()
    for key, value in headers.items():
        if str(key).strip().lower() == wanted:
            return value
    return None


def encoding_of_header(value):
    """Classify a content-type header value, ignoring parameters. Pure."""
    if value is None:
        return "unknown"
    text = str(value).split(";")[0].strip().lower()
    if text == "application/json":
        return JSON
    if text == "application/x-www-form-urlencoded":
        return FORM
    return "unknown"


def delivery_encoding(delivery):
    """What GitHub said it was sending on one delivery record. Pure."""
    if not isinstance(delivery, dict):
        return "unknown"
    request = delivery.get("request")
    if not isinstance(request, dict):
        return "unknown"
    return encoding_of_header(header_of(request.get("headers"), "content-type"))


def is_form_wrapped(payload):
    """Whether a recorded body is the payload= wrapper rather than the event. Pure.

    A form delivery records one key, payload, holding the event JSON as a string.
    An event object has many keys and none of that shape, so this is unambiguous
    where it fires and simply silent where the record has been normalised.
    """
    if not isinstance(payload, dict):
        return False
    return list(payload.keys()) == ["payload"] and isinstance(payload.get("payload"), str)


def wrapper_evidence(details):
    """Count the delivery records showing the form wrapper, both ways. Pure."""
    records = [d for d in (details or []) if isinstance(d, dict)]
    by_header = sum(1 for d in records if delivery_encoding(d) == FORM)
    by_body = sum(1 for d in records
                  if is_form_wrapped((d.get("request") or {}).get("payload")))
    return {"sampled": len(records), "form_header": by_header, "form_wrapper": by_body}


def parse_failures(deliveries):
    """How many recent attempts came back with a body-parse status. Pure."""
    records = [d for d in (deliveries or []) if isinstance(d, dict)]
    hits = 0
    for d in records:
        try:
            code = int(d.get("status_code"))
        except (TypeError, ValueError):
            continue
        if code in PARSE_STATUSES:
            hits += 1
    return hits, len(records)


def receiver_of(declared):
    """Normalise what the caller says the receiver parses. Pure."""
    value = str(declared or "unknown").strip().lower()
    return value if value in (JSON, FORM) else "unknown"


def verdict(hook_encoding, declared, evidence=None, failures=0, sampled_total=0):
    """Turn the configured encoding and the declared receiver into a finding. Pure.

    The status codes never decide. A clean delivery log is the expected state of
    this problem on a tolerant framework, so letting it soften the verdict would
    remove the only case worth writing a script for.
    """
    seen = evidence or {}
    confirmed = max(int(seen.get("form_header") or 0), int(seen.get("form_wrapper") or 0))
    parsed = receiver_of(declared)
    corroboration = ""
    if confirmed:
        corroboration = (" %d of %d sampled deliveries carry the form encoding."
                         % (confirmed, seen.get("sampled") or 0))
    if failures:
        corroboration += (" %d of %d recent attempts came back 400, 415 or 422."
                          % (failures, sampled_total))
    if hook_encoding == "unknown":
        return ("encoding-unknown",
                "config.content_type holds a value this script does not "
                "recognise. GitHub supports json and form; anything else needs "
                "reading by hand before the rest of this is meaningful.")
    if hook_encoding == FORM and parsed == JSON:
        return ("form-to-json",
                "the hook sends application/x-www-form-urlencoded and the "
                "receiver was declared as JSON. Every event arrives wrapped in "
                "a payload= field, so no key your handler reads exists at the "
                "top level of the body." + corroboration)
    if hook_encoding == JSON and parsed == FORM:
        return ("json-to-form",
                "the hook sends application/json and the receiver was declared "
                "as a form parser. The body has no payload= field to unwrap, so "
                "the parsed result is empty rather than wrong.")
    if hook_encoding == FORM and parsed == "unknown":
        return ("receiver-undeclared",
                "the hook sends application/x-www-form-urlencoded, which is the "
                "default rather than a decision. No receiver was declared, so "
                "this is a risk rather than a finding: confirm the handler "
                "unwraps the payload field before treating it as healthy."
                + corroboration)
    if hook_encoding == FORM:
        return ("consistent-form",
                "the hook sends application/x-www-form-urlencoded and the "
                "receiver was declared as a form parser. Consistent, but the "
                "signature covers the urlencoded wrapper, so verify over the raw "
                "bytes rather than over anything you unwrapped.")
    return ("consistent-json",
            "the hook sends application/json and the receiver parses JSON.")


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "form-to-json":
        return ("set config.content_type to json on the hook, and in the same "
                "change make signature verification read the raw request bytes "
                "before parsing. Then redeliver one event from the delivery log "
                "and confirm the handler ran.")
    if state == "json-to-form":
        return ("parse the body as JSON in the receiver. Changing the hook back "
                "to form to suit the parser is the wrong direction: form is the "
                "legacy encoding and it makes signature verification harder.")
    if state == "receiver-undeclared":
        return ("run this again with --receiver set from the handler code. If "
                "the handler reads the body as JSON, this is a live finding; if "
                "it unwraps the payload field first, it is working as built.")
    if state == "consistent-form":
        return ("nothing urgent. Moving to json is still worth doing, because "
                "it removes a layer of encoding between the signature and the "
                "document you verify.")
    if state == "encoding-unknown":
        return ("read config.content_type by hand. Only json and form are "
                "supported values and neither of them is what is set here.")
    return "nothing."


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def hooks_for(session, repo):
    """Every hook on the repository."""
    status, body = get(session, "/repos/%s/hooks?per_page=100" % repo)
    if status != 200 or not isinstance(body, list):
        log.error("GET /repos/%s/hooks returned %d", repo, status)
        return []
    return body


def deliveries_for(session, repo, hook_id):
    """The recent delivery list. No request headers here; that needs the detail."""
    status, body = get(session, "/repos/%s/hooks/%s/deliveries?per_page=100"
                       % (repo, hook_id))
    if status != 200 or not isinstance(body, list):
        log.info("deliveries for hook %s returned %d; the config read stands on "
                 "its own", hook_id, status)
        return []
    return body


def delivery_details(session, repo, hook_id, deliveries, sample):
    """Individual records, which are the only place request.headers appears."""
    out = []
    for d in deliveries[:max(0, int(sample))]:
        if not isinstance(d, dict) or d.get("id") is None:
            continue
        status, body = get(session, "/repos/%s/hooks/%s/deliveries/%s"
                           % (repo, hook_id, d["id"]))
        if status == 200 and isinstance(body, dict):
            out.append(body)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPO"),
                    help="owner/name of the repository holding the hook")
    ap.add_argument("--receiver", default=os.environ.get("GITHUB_RECEIVER_PARSES"),
                    help="what your receiver parses: json or form. The API "
                         "cannot see this, so it is declared rather than read")
    ap.add_argument("--sample", type=int, default=5,
                    help="how many individual delivery records to fetch")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN to a read-only token with access to the repository")
        return 2
    if not args.repo:
        log.error("set --repo to owner/name")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    findings = []
    report = []
    for hook in hooks_for(session, args.repo):
        config = hook.get("config") or {}
        encoding = content_type_of(config)
        explicit = content_type_was_explicit(config)
        log.info("hook %s %s content_type=%s (%s)", hook.get("id"),
                 config.get("url"), encoding,
                 "explicit" if explicit else "default, key absent")

        deliveries = deliveries_for(session, args.repo, hook.get("id"))
        details = delivery_details(session, args.repo, hook.get("id"),
                                   deliveries, args.sample)
        evidence = wrapper_evidence(details)
        failures, total = parse_failures(deliveries)
        log.info("deliveries sampled: %d, form content-type header on %d, "
                 "payload= wrapper on %d", evidence["sampled"],
                 evidence["form_header"], evidence["form_wrapper"])
        log.info("parse statuses (400/415/422): %d of %d recent deliveries",
                 failures, total)

        state, detail = verdict(encoding, args.receiver, evidence, failures, total)
        log.info("%s: %s", state, detail)
        log.info("repair: %s", repair(state))
        if state in ("form-to-json", "json-to-form", "encoding-unknown"):
            findings.append(hook.get("id"))
        report.append({
            "hook_id": hook.get("id"),
            "url": config.get("url"),
            "content_type": encoding,
            "content_type_explicit": explicit,
            "receiver_declared": receiver_of(args.receiver),
            "sampled": evidence["sampled"],
            "form_header_seen": evidence["form_header"],
            "form_wrapper_seen": evidence["form_wrapper"],
            "parse_status_count": failures,
            "deliveries_examined": total,
            "state": state,
            "detail": detail,
            "repair": repair(state),
        })

    print(json.dumps({"repository": args.repo, "hooks": report}, indent=2, default=str))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-content-type.mjs",
"js": '''/**
 * Say whether a webhook sends a body encoding its receiver cannot read.
 *
 * Read only. Three kinds of GET: the hook list, the delivery list, and a few
 * individual delivery records, which are the only place the request headers and
 * the recorded body appear. Nothing is created, edited or redelivered.
 *
 * Environment:
 *   GITHUB_TOKEN             a read-only token with access to the repository
 *   GITHUB_REPO              owner/name
 *   GITHUB_RECEIVER_PARSES   json or form, declared rather than read
 */
const API = 'https://api.github.com';
const UA = 'github-hook-content-type/1.0';

export const FORM = 'form';
export const JSON_CT = 'json';
/** The documented default: an absent key means form. */
export const DEFAULT_CONTENT_TYPE = FORM;
/** Corroboration only; a tolerant framework answers 200 and this stays empty. */
export const PARSE_STATUSES = [400, 415, 422];

/** The hook's configured body encoding, normalised. Pure. */
export function contentTypeOf(config) {
  if (!config || typeof config !== 'object') return 'unknown';
  const raw = config.content_type;
  if (raw === null || raw === undefined) return DEFAULT_CONTENT_TYPE;
  const value = String(raw).trim().toLowerCase();
  if (['json', 'application/json'].includes(value)) return JSON_CT;
  if (['form', 'application/x-www-form-urlencoded'].includes(value)) return FORM;
  return 'unknown';
}

/** Whether the hook names its encoding or inherits the default. Pure. */
export function contentTypeWasExplicit(config) {
  return Boolean(config && typeof config === 'object'
    && config.content_type !== null && config.content_type !== undefined);
}

/** One header from a delivery record, case-insensitively. Pure. */
export function headerOf(headers, name) {
  if (!headers || typeof headers !== 'object') return null;
  const wanted = String(name).trim().toLowerCase();
  for (const [key, value] of Object.entries(headers)) {
    if (String(key).trim().toLowerCase() === wanted) return value;
  }
  return null;
}

/** Classify a content-type header value, ignoring parameters. Pure. */
export function encodingOfHeader(value) {
  if (value === null || value === undefined) return 'unknown';
  const text = String(value).split(';')[0].trim().toLowerCase();
  if (text === 'application/json') return JSON_CT;
  if (text === 'application/x-www-form-urlencoded') return FORM;
  return 'unknown';
}

/** What GitHub said it was sending on one delivery record. Pure. */
export function deliveryEncoding(delivery) {
  if (!delivery || typeof delivery !== 'object') return 'unknown';
  const request = delivery.request;
  if (!request || typeof request !== 'object') return 'unknown';
  return encodingOfHeader(headerOf(request.headers, 'content-type'));
}

/** Whether a recorded body is the payload= wrapper rather than the event. Pure. */
export function isFormWrapped(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return false;
  const keys = Object.keys(payload);
  return keys.length === 1 && keys[0] === 'payload' && typeof payload.payload === 'string';
}

/** Count the delivery records showing the form wrapper, both ways. Pure. */
export function wrapperEvidence(details) {
  const records = (details || []).filter((d) => d && typeof d === 'object');
  const formHeader = records.filter((d) => deliveryEncoding(d) === FORM).length;
  const formWrapper = records.filter((d) => isFormWrapped((d.request || {}).payload)).length;
  return { sampled: records.length, form_header: formHeader, form_wrapper: formWrapper };
}

/** How many recent attempts came back with a body-parse status. Pure. */
export function parseFailures(deliveries) {
  const records = (deliveries || []).filter((d) => d && typeof d === 'object');
  let hits = 0;
  for (const d of records) {
    const code = Number(d.status_code);
    if (Number.isFinite(code) && PARSE_STATUSES.includes(code)) hits += 1;
  }
  return [hits, records.length];
}

/** Normalise what the caller says the receiver parses. Pure. */
export function receiverOf(declared) {
  const value = String(declared ?? 'unknown').trim().toLowerCase();
  return [JSON_CT, FORM].includes(value) ? value : 'unknown';
}

/** Turn the configured encoding and the declared receiver into a finding. Pure. */
export function verdict(hookEncoding, declared, evidence = null, failures = 0, sampledTotal = 0) {
  const seen = evidence || {};
  const confirmed = Math.max(Number(seen.form_header || 0), Number(seen.form_wrapper || 0));
  const parsed = receiverOf(declared);
  let corroboration = '';
  if (confirmed) {
    corroboration = ` ${confirmed} of ${seen.sampled || 0} sampled deliveries carry the form encoding.`;
  }
  if (failures) {
    corroboration += ` ${failures} of ${sampledTotal} recent attempts came back 400, 415 or 422.`;
  }
  if (hookEncoding === 'unknown') {
    return ['encoding-unknown',
      'config.content_type holds a value this script does not recognise. GitHub '
      + 'supports json and form; anything else needs reading by hand before the '
      + 'rest of this is meaningful.'];
  }
  if (hookEncoding === FORM && parsed === JSON_CT) {
    return ['form-to-json',
      'the hook sends application/x-www-form-urlencoded and the receiver was '
      + 'declared as JSON. Every event arrives wrapped in a payload= field, so no '
      + 'key your handler reads exists at the top level of the body.' + corroboration];
  }
  if (hookEncoding === JSON_CT && parsed === FORM) {
    return ['json-to-form',
      'the hook sends application/json and the receiver was declared as a form '
      + 'parser. The body has no payload= field to unwrap, so the parsed result '
      + 'is empty rather than wrong.'];
  }
  if (hookEncoding === FORM && parsed === 'unknown') {
    return ['receiver-undeclared',
      'the hook sends application/x-www-form-urlencoded, which is the default '
      + 'rather than a decision. No receiver was declared, so this is a risk '
      + 'rather than a finding: confirm the handler unwraps the payload field '
      + 'before treating it as healthy.' + corroboration];
  }
  if (hookEncoding === FORM) {
    return ['consistent-form',
      'the hook sends application/x-www-form-urlencoded and the receiver was '
      + 'declared as a form parser. Consistent, but the signature covers the '
      + 'urlencoded wrapper, so verify over the raw bytes rather than over '
      + 'anything you unwrapped.'];
  }
  return ['consistent-json', 'the hook sends application/json and the receiver parses JSON.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'form-to-json') {
    return 'set config.content_type to json on the hook, and in the same change '
      + 'make signature verification read the raw request bytes before parsing. '
      + 'Then redeliver one event from the delivery log and confirm the handler ran.';
  }
  if (state === 'json-to-form') {
    return 'parse the body as JSON in the receiver. Changing the hook back to '
      + 'form to suit the parser is the wrong direction: form is the legacy '
      + 'encoding and it makes signature verification harder.';
  }
  if (state === 'receiver-undeclared') {
    return 'run this again with the receiver declared from the handler code. If '
      + 'the handler reads the body as JSON, this is a live finding; if it '
      + 'unwraps the payload field first, it is working as built.';
  }
  if (state === 'consistent-form') {
    return 'nothing urgent. Moving to json is still worth doing, because it '
      + 'removes a layer of encoding between the signature and the document you verify.';
  }
  if (state === 'encoding-unknown') {
    return 'read config.content_type by hand. Only json and form are supported '
      + 'values and neither of them is what is set here.';
  }
  return 'nothing.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(token, path) {
  const res = await fetch(API + path, { headers: headers(token) });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  if (!token || !repo) {
    console.error('set GITHUB_TOKEN and GITHUB_REPO=owner/name');
    process.exitCode = 2;
    return;
  }
  const declared = process.env.GITHUB_RECEIVER_PARSES || null;
  const sample = Number(process.env.GITHUB_SAMPLE || 5);

  const list = await get(token, `/repos/${repo}/hooks?per_page=100`);
  if (list.status !== 200 || !Array.isArray(list.body)) {
    console.error(`GET /repos/${repo}/hooks returned ${list.status}`);
    process.exitCode = 2;
    return;
  }

  const report = [];
  let findings = 0;
  for (const hook of list.body) {
    const config = hook.config || {};
    const encoding = contentTypeOf(config);
    console.log(`hook ${hook.id} ${config.url} content_type=${encoding} `
      + `(${contentTypeWasExplicit(config) ? 'explicit' : 'default, key absent'})`);

    const dl = await get(token, `/repos/${repo}/hooks/${hook.id}/deliveries?per_page=100`);
    const deliveries = dl.status === 200 && Array.isArray(dl.body) ? dl.body : [];
    const details = [];
    for (const d of deliveries.slice(0, sample)) {
      const one = await get(token, `/repos/${repo}/hooks/${hook.id}/deliveries/${d.id}`);
      if (one.status === 200 && one.body) details.push(one.body);
    }
    const evidence = wrapperEvidence(details);
    const [failures, total] = parseFailures(deliveries);
    console.log(`deliveries sampled: ${evidence.sampled}, form content-type header on `
      + `${evidence.form_header}, payload= wrapper on ${evidence.form_wrapper}`);
    console.log(`parse statuses (400/415/422): ${failures} of ${total} recent deliveries`);

    const [state, detail] = verdict(encoding, declared, evidence, failures, total);
    console.log(`${state}: ${detail}`);
    console.log(`repair: ${repair(state)}`);
    if (['form-to-json', 'json-to-form', 'encoding-unknown'].includes(state)) findings += 1;
    report.push({
      hook_id: hook.id,
      url: config.url,
      content_type: encoding,
      content_type_explicit: contentTypeWasExplicit(config),
      receiver_declared: receiverOf(declared),
      sampled: evidence.sampled,
      parse_status_count: failures,
      deliveries_examined: total,
      state,
    });
  }
  console.log(JSON.stringify({ repository: repo, hooks: report }, null, 2));
  process.exitCode = findings ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The tests spend most of their attention on the two things that decide the answer. First, that an absent <code>content_type</code> resolves to <code>form</code> rather than to unknown, in every defensive branch, because that is the case the note exists for. Second, that a clean delivery log never turns a mismatch into a pass &mdash; a form hook feeding a JSON receiver with forty successful deliveries behind it is still the finding, and there is a test that says so in those words.",
"test_py_file": "test_github_hook_content_type.py",
"test_py": '''from github_hook_content_type import (
    content_type_of, content_type_was_explicit, delivery_encoding,
    encoding_of_header, header_of, is_form_wrapped, parse_failures, receiver_of,
    repair, verdict, wrapper_evidence,
)

FORM_DELIVERY = {
    "id": 1,
    "status_code": 200,
    "request": {
        "headers": {"Content-Type": "application/x-www-form-urlencoded",
                    "X-GitHub-Event": "push"},
        "payload": {"payload": '{ "action": "opened" }'},
    },
}
JSON_DELIVERY = {
    "id": 2,
    "status_code": 200,
    "request": {
        "headers": {"content-type": "application/json; charset=utf-8"},
        "payload": {"action": "opened", "number": 7},
    },
}


def test_an_absent_content_type_is_form_not_unknown():
    assert content_type_of({}) == "form"
    assert content_type_of({"url": "https://example.com"}) == "form"
    assert not content_type_was_explicit({})
    assert content_type_was_explicit({"content_type": "form"})


def test_both_spellings_of_each_encoding_are_understood():
    assert content_type_of({"content_type": "json"}) == "json"
    assert content_type_of({"content_type": "application/json"}) == "json"
    assert content_type_of({"content_type": " FORM "}) == "form"
    assert content_type_of({"content_type": "application/x-www-form-urlencoded"}) == "form"
    assert content_type_of({"content_type": "text/xml"}) == "unknown"
    assert content_type_of(None) == "unknown"


def test_headers_are_read_case_insensitively_and_parameters_ignored():
    assert header_of({"Content-Type": "application/json"}, "content-type") == "application/json"
    assert header_of({"CONTENT-TYPE": "x"}, "Content-Type") == "x"
    assert header_of({}, "content-type") is None
    assert header_of(None, "content-type") is None
    assert encoding_of_header("application/json; charset=utf-8") == "json"
    assert encoding_of_header("application/x-www-form-urlencoded") == "form"
    assert encoding_of_header(None) == "unknown"


def test_the_delivery_record_is_read_from_the_request_half():
    assert delivery_encoding(FORM_DELIVERY) == "form"
    assert delivery_encoding(JSON_DELIVERY) == "json"
    assert delivery_encoding({"status_code": 200}) == "unknown"
    assert delivery_encoding(None) == "unknown"


def test_the_wrapper_is_one_string_key_and_nothing_else():
    assert is_form_wrapped({"payload": "{}"})
    assert not is_form_wrapped({"payload": {"action": "opened"}})
    assert not is_form_wrapped({"payload": "{}", "extra": 1})
    assert not is_form_wrapped({"action": "opened"})
    assert not is_form_wrapped(None)


def test_evidence_counts_the_header_and_the_body_separately():
    ev = wrapper_evidence([FORM_DELIVERY, JSON_DELIVERY, None])
    assert ev == {"sampled": 2, "form_header": 1, "form_wrapper": 1}


def test_parse_statuses_are_counted_but_only_the_three():
    hits, total = parse_failures([{"status_code": 400}, {"status_code": 415},
                                  {"status_code": 500}, {"status_code": 200},
                                  {"status_code": None}])
    assert (hits, total) == (2, 5)


def test_a_form_hook_against_a_json_receiver_is_the_finding():
    state, detail = verdict("form", "json")
    assert state == "form-to-json"
    assert "payload= field" in detail


def test_a_clean_delivery_log_does_not_soften_the_finding():
    ev = {"sampled": 5, "form_header": 5, "form_wrapper": 5}
    state, detail = verdict("form", "json", ev, failures=0, sampled_total=40)
    assert state == "form-to-json"
    assert "5 of 5 sampled deliveries" in detail


def test_parse_statuses_are_reported_as_corroboration():
    state, detail = verdict("form", "json", None, failures=12, sampled_total=40)
    assert state == "form-to-json"
    assert "12 of 40 recent attempts" in detail


def test_the_mirror_case_is_named_rather_than_folded_in():
    assert verdict("json", "form")[0] == "json-to-form"
    assert "wrong direction" in repair("json-to-form")


def test_an_undeclared_receiver_gives_a_risk_and_not_a_verdict():
    state, detail = verdict("form", None)
    assert state == "receiver-undeclared"
    assert "risk rather than a finding" in detail


def test_consistent_pairs_are_not_findings():
    assert verdict("json", "json")[0] == "consistent-json"
    assert verdict("form", "form")[0] == "consistent-form"


def test_a_consistent_form_hook_is_still_warned_about_the_signature():
    assert "raw bytes" in verdict("form", "form")[1]


def test_an_unrecognised_encoding_is_never_guessed_at():
    state, _ = verdict("unknown", "json")
    assert state == "encoding-unknown"
    assert "by hand" in repair("encoding-unknown")


def test_the_receiver_flag_is_normalised_defensively():
    assert receiver_of("JSON") == "json"
    assert receiver_of(" form ") == "form"
    assert receiver_of("maybe") == "unknown"
    assert receiver_of(None) == "unknown"


def test_the_repair_always_pairs_the_encoding_with_the_verifier():
    assert "raw request bytes" in repair("form-to-json")
    assert repair("consistent-json") == "nothing."
''',
"test_js_file": "github-hook-content-type.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  contentTypeOf, contentTypeWasExplicit, deliveryEncoding, encodingOfHeader,
  headerOf, isFormWrapped, parseFailures, receiverOf, repair, verdict,
  wrapperEvidence,
} from './github-hook-content-type.mjs';

const FORM_DELIVERY = {
  id: 1,
  status_code: 200,
  request: {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-GitHub-Event': 'push' },
    payload: { payload: '{ "action": "opened" }' },
  },
};
const JSON_DELIVERY = {
  id: 2,
  status_code: 200,
  request: {
    headers: { 'content-type': 'application/json; charset=utf-8' },
    payload: { action: 'opened', number: 7 },
  },
};

test('an absent content_type is form, not unknown', () => {
  assert.equal(contentTypeOf({}), 'form');
  assert.equal(contentTypeOf({ url: 'https://example.com' }), 'form');
  assert.ok(!contentTypeWasExplicit({}));
  assert.ok(contentTypeWasExplicit({ content_type: 'form' }));
});

test('both spellings of each encoding are understood', () => {
  assert.equal(contentTypeOf({ content_type: 'json' }), 'json');
  assert.equal(contentTypeOf({ content_type: 'application/json' }), 'json');
  assert.equal(contentTypeOf({ content_type: ' FORM ' }), 'form');
  assert.equal(contentTypeOf({ content_type: 'application/x-www-form-urlencoded' }), 'form');
  assert.equal(contentTypeOf({ content_type: 'text/xml' }), 'unknown');
  assert.equal(contentTypeOf(null), 'unknown');
});

test('headers are read case insensitively and parameters ignored', () => {
  assert.equal(headerOf({ 'Content-Type': 'application/json' }, 'content-type'), 'application/json');
  assert.equal(headerOf({ 'CONTENT-TYPE': 'x' }, 'Content-Type'), 'x');
  assert.equal(headerOf({}, 'content-type'), null);
  assert.equal(headerOf(null, 'content-type'), null);
  assert.equal(encodingOfHeader('application/json; charset=utf-8'), 'json');
  assert.equal(encodingOfHeader('application/x-www-form-urlencoded'), 'form');
  assert.equal(encodingOfHeader(null), 'unknown');
});

test('the delivery record is read from the request half', () => {
  assert.equal(deliveryEncoding(FORM_DELIVERY), 'form');
  assert.equal(deliveryEncoding(JSON_DELIVERY), 'json');
  assert.equal(deliveryEncoding({ status_code: 200 }), 'unknown');
  assert.equal(deliveryEncoding(null), 'unknown');
});

test('the wrapper is one string key and nothing else', () => {
  assert.ok(isFormWrapped({ payload: '{}' }));
  assert.ok(!isFormWrapped({ payload: { action: 'opened' } }));
  assert.ok(!isFormWrapped({ payload: '{}', extra: 1 }));
  assert.ok(!isFormWrapped({ action: 'opened' }));
  assert.ok(!isFormWrapped(null));
});

test('evidence counts the header and the body separately', () => {
  const ev = wrapperEvidence([FORM_DELIVERY, JSON_DELIVERY, null]);
  assert.deepEqual(ev, { sampled: 2, form_header: 1, form_wrapper: 1 });
});

test('parse statuses are counted but only the three', () => {
  const [hits, total] = parseFailures([{ status_code: 400 }, { status_code: 415 },
    { status_code: 500 }, { status_code: 200 }, { status_code: null }]);
  assert.equal(hits, 2);
  assert.equal(total, 5);
});

test('a form hook against a JSON receiver is the finding', () => {
  const [state, detail] = verdict('form', 'json');
  assert.equal(state, 'form-to-json');
  assert.match(detail, /payload= field/);
});

test('a clean delivery log does not soften the finding', () => {
  const ev = { sampled: 5, form_header: 5, form_wrapper: 5 };
  const [state, detail] = verdict('form', 'json', ev, 0, 40);
  assert.equal(state, 'form-to-json');
  assert.match(detail, /5 of 5 sampled deliveries/);
});

test('parse statuses are reported as corroboration', () => {
  const [state, detail] = verdict('form', 'json', null, 12, 40);
  assert.equal(state, 'form-to-json');
  assert.match(detail, /12 of 40 recent attempts/);
});

test('the mirror case is named rather than folded in', () => {
  assert.equal(verdict('json', 'form')[0], 'json-to-form');
  assert.match(repair('json-to-form'), /wrong direction/);
});

test('an undeclared receiver gives a risk and not a verdict', () => {
  const [state, detail] = verdict('form', null);
  assert.equal(state, 'receiver-undeclared');
  assert.match(detail, /risk rather than a finding/);
});

test('consistent pairs are not findings', () => {
  assert.equal(verdict('json', 'json')[0], 'consistent-json');
  assert.equal(verdict('form', 'form')[0], 'consistent-form');
});

test('a consistent form hook is still warned about the signature', () => {
  assert.match(verdict('form', 'form')[1], /raw bytes/);
});

test('an unrecognised encoding is never guessed at', () => {
  assert.equal(verdict('unknown', 'json')[0], 'encoding-unknown');
  assert.match(repair('encoding-unknown'), /by hand/);
});

test('the receiver flag is normalised defensively', () => {
  assert.equal(receiverOf('JSON'), 'json');
  assert.equal(receiverOf(' form '), 'form');
  assert.equal(receiverOf('maybe'), 'unknown');
  assert.equal(receiverOf(null), 'unknown');
});

test('the repair always pairs the encoding with the verifier', () => {
  assert.match(repair('form-to-json'), /raw request bytes/);
  assert.equal(repair('consistent-json'), 'nothing.');
});
''',
"faq": [
 ("Every delivery is a 200. Is this still a problem?",
  "Very possibly, and that is the case worth writing a script for. Plenty of frameworks answer a body they cannot parse with a default value rather than an exception: your handler receives an empty object, matches none of its branches, and returns 200 having done nothing. GitHub records a success because it got one. The only way to tell that state apart from a working integration through the API is to read the request half of a delivery record rather than the response half, which is what the script does."),
 ("Can the script tell what my receiver parses?",
  "No, and it does not pretend to. This is the section's standing blind spot: the API describes what GitHub sends and is silent about what happens next. So the sending half is measured properly &mdash; the configured encoding, the real content-type header on a sample of deliveries, and the shape of the recorded body &mdash; and the receiving half is a flag you set from your own code. The output labels the declared half as declared. Run it without the flag and it reports the encoding and the risk rather than claiming a mismatch it cannot see."),
 ("Why did switching content_type to json break our signature check?",
  "Because the signature is an HMAC over the exact bytes of the request body, and you changed the bytes. On a form hook the body is <code>payload=</code> followed by the percent-encoded document, and that whole string is what the signature covers. If your verifier url-decoded first, or parsed the body and hashed a re-serialisation of the object, it was never really verifying the bytes GitHub signed, and it stops agreeing the moment the encoding moves. Read the raw body once, verify against that, and parse the same bytes afterwards."),
 ("How is this different from the delivery failure audit?",
  "That note groups delivery attempts by their status code and needs a non-OK status to have something to report. This one lives in the request half of the record, and its most important case has a clean status. They also produce different repairs: a failure audit sends you to your receiver's logs, and this sends you to one field in the hook config. If your deliveries really are failing with 400s, both notes point at the same place and you should read that one too."),
 ("Should we just make the receiver handle both encodings?",
  "You can, and it is a reasonable belt-and-braces measure for a receiver that several systems post to. It is not the repair, though. Handling both means two parse paths and, more awkwardly, deciding which bytes the signature covers in each of them, which is exactly the kind of branch that gets one case tested and the other one wrong. One field on one hook is a smaller change than a second code path you have to keep correct."),
],
"related": [
 ("/github/webhook-deliveries-failing/", "Deliveries failing where nobody reads the log"),
 ("/github/webhook-sha1-signature-only/", "A receiver still checking the SHA-1 signature"),
 ("/github/webhook-no-secret/", "A webhook with no secret sends no signature"),
],
"citations": [CITE_REPO_HOOKS, CITE_VALIDATING, CITE_CREATING_WEBHOOKS, CITE_TROUBLESHOOT],
},


{
"slug": "webhook-ip-allowlist-drift",
"title": "A firewall allow-list no longer matches GitHub's hook IPs",
"description": "GET /meta publishes the CIDR ranges webhooks are delivered from, and they change. An allow-list pasted from the docs once starts blocking the new ones.",
"h1": "a firewall allow-list no longer matches GitHub's hook IPs",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github webhook ip ranges allowlist",
             "github meta hooks cidr ranges firewall",
             "github webhook connection refused firewall",
             "github webhook ip address changed 2026",
             "github meta api hooks vs api ranges"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Some deliveries land and some do not, with no pattern anybody can find. It is not the event type, it is not the payload size, it is not the time of day. The hook is configured correctly, the receiver is up, and the delivery log shows connection failures scattered among successes. Nothing is wrong with the webhook. The problem is a text file on a firewall, written correctly two years ago.",
"short_answer": """<p><code>GET https://api.github.com/meta</code> returns the current source ranges GitHub uses, split by purpose: <code>hooks</code>, <code>api</code>, <code>web</code>, <code>git</code>, <code>packages</code>, <code>actions</code>, <code>dependabot</code> and more. The <code>hooks</code> array is the authoritative list of the addresses webhook deliveries come from, and it is the only one that matters here. The endpoint needs no token at all.</p>
<p>Everything after that is CIDR arithmetic against your own allow-list, because the one thing the GitHub API can never read is your network. Export the ranges your firewall or WAF actually permits, and compare: a published range that is only partly covered is the interesting case, because it fails intermittently rather than completely, and that is exactly what makes it hard to see from the delivery log. The repair is not to paste the new list in; it is to stop pasting, and generate the allow-list from this endpoint on a schedule.</p>""",
"problem": """<p>Somebody did this properly. They found GitHub's documented hook ranges, put them in the firewall, tested a delivery, and it worked. That was the correct action and it is why the problem is so durable: there is no mistake in the history to find. The ranges then changed, as published network ranges do, and nothing on your side is subscribed to that change.</p>
<p>What arrives is the worst possible symptom, which is a partial one. GitHub delivers from a pool, so a new range that your firewall does not know about only affects the deliveries that happen to leave from it. Roughly nine in ten events land. The tenth times out. Nobody debugs a webhook that mostly works, and the failures get absorbed as flakiness, retried by hand, or explained by whatever else was happening that afternoon. Months later somebody notices a customer whose events are always the ones that go missing, and that is coincidence too.</p>
<p>Then there is the version of this that is not drift at all but a copy of the wrong list. <code>GET /meta</code> returns several arrays and only one of them is about webhooks. <code>api</code> is where GitHub's API is served from, which is a completely different direction of traffic: it is what your requests go to, not what deliveries come from. An allow-list built out of <code>api</code> is a plausible-looking file full of GitHub addresses that will never send you a webhook, and it produces the same intermittent nothing.</p>
<p>Underneath all of it is an assumption worth naming. IP allow-listing is being used here as if it were authentication, and it is not. It is a network control that reduces exposure and it fails open in one direction and closed in the other: it will not stop anything that can route from an allowed address, and it will silently block legitimate traffic when the list ages. The thing that actually authenticates a webhook is the signature.</p>""",
"why": """<p><strong>The list is published, so treat it as data rather than documentation.</strong> <code>GET /meta</code> is a JSON document, unauthenticated, and its <code>hooks</code> array is the current answer at the moment you ask. A copy of it in a firewall config is a cache with no expiry and no invalidation, which is the shape of every problem in this genre. The fix for a stale cache is not a fresher copy.</p>
<p><strong>Partial coverage is the case that hides.</strong> If GitHub publishes a <code>/22</code> and your rule permits a <code>/24</code> inside it, three quarters of that range is blocked and one quarter works. Nothing in your firewall reports a conflict, because there is no conflict; the rule does exactly what it says. This is why the script measures coverage by address count rather than by comparing strings: a set difference on the text of the CIDRs would call the <code>/24</code> a mismatch without saying how much of the range is missing, and would call an equivalent rewrite of the same range a mismatch too.</p>
<p><strong>The arrays in <code>/meta</code> are not interchangeable.</strong> <code>hooks</code> is outbound webhook delivery. <code>api</code>, <code>web</code> and <code>git</code> are inbound: they are where you connect to. Allow-listing <code>api</code> for webhook delivery is a category error that survives review because every address in the file genuinely does belong to GitHub. The script scores your list against each array and names the one it matches best, which turns that mistake into a sentence rather than a mystery.</p>
<p><strong>A default route in the list means the list is decorative.</strong> A rule permitting <code>0.0.0.0/0</code> anywhere in the chain covers every published range perfectly, and the audit comes back clean while the control does nothing. That is a finding in its own right and it is reported as one rather than as a pass.</p>
<p><strong>Your firewall is outside the API's world.</strong> This is the only note in the section where the thing to fix is not visible to any token. The script reads the authoritative half from GitHub and takes the other half from a file you export, and it says so plainly: the accuracy of the answer is the accuracy of that export. Point it at a stale copy of your rules and it will confidently audit a stale copy of your rules.</p>""",
"steps": [
 {"h": "Read the authoritative list, with no credentials at all",
  "body": """<p><code>GET https://api.github.com/meta</code> and take the <code>hooks</code> array. No token is needed, which matters: this check belongs to whoever owns the firewall, and they should not have to be issued a GitHub credential to run it. Unauthenticated requests share the anonymous limit of 60 an hour per address, so an hourly job fits comfortably.</p>"""},
 {"h": "Export what your firewall really permits",
  "body": """<p>One CIDR per line, comments allowed. Export it from the device or the infrastructure-as-code that defines it, not from the wiki page that describes it, because the gap between those two is frequently the whole bug. Include every rule in the path: an edge WAF and a security group are two lists and events have to cross both.</p>"""},
 {"h": "Measure coverage by addresses, not by matching text",
  "body": """<p>For each published range, work out how much of it your rules actually permit. Full, partial and none are three different findings: none is a range that never works, partial is a range that works for some deliveries, and partial is the one that has been costing you afternoons. Comparing the CIDR strings for equality reports a correctly written superset as a mismatch and misses a subset entirely.</p>"""},
 {"h": "Check you copied the right array",
  "body": """<p>Score the same allow-list against the other arrays in <code>/meta</code>. If it covers <code>api</code> far better than it covers <code>hooks</code>, the list was built from the wrong section of the documentation and no amount of updating it will help. This costs nothing extra: the response already contains every array.</p>"""},
 {"h": "Automate it, and keep the signature as the real control",
  "body": """<p>Generate the allow-list from <code>/meta</code> on a schedule and alert when the published set changes, so the next change is a pull request rather than an incident. Then stop treating the allow-list as authentication: verify <code>X-Hub-Signature-256</code> on every request. An IP list is a blast-radius control, and it is the signature that establishes an event came from GitHub.</p>"""},
],
"verify": """<p>The check runs from anywhere that can reach api.github.com, with no GitHub credential of any kind.</p>
<pre><code class="language-bash">python3 github_meta_hook_ranges.py --allowlist firewall-github.txt
# GET /meta: 8 hooks range(s) published, allow-list holds 6 entry/entries
# 192.30.252.0/22        partial   25% covered
# 140.82.112.0/20        full     100% covered
# 2a0a:a440::/29         none       0% covered
# drifted: 2 of 8 published hook ranges are not fully covered by the allow-list.
# repair: generate the allow-list from GET /meta on a schedule. The current
# published set follows, in full, ready to paste into the rule that owns it.

# and the version worth catching early
# wrong-array: the allow-list covers the api ranges 100% and the hooks ranges
# 12%. This list was built from the wrong section of GET /meta.</code></pre>""",
"code_intro": "The network part is one unauthenticated GET and the rest is interval arithmetic that runs offline, which is the right split for something a firewall owner should be able to reason about. Coverage is computed over address counts rather than over the text of the CIDRs, so an equivalent rewrite of a range passes and a subset is reported with the fraction it actually permits. The Node version carries its own IPv4 and IPv6 parsing, because GitHub publishes v6 ranges and there is no address type in the standard library to lean on.",
"py_file": "github_meta_hook_ranges.py",
"py": '''"""Compare GitHub's published webhook source ranges against your allow-list.

Read only, and unauthenticated: GET /meta needs no token, which means the person
who owns the firewall can run this without being issued a GitHub credential.

GET /meta returns the current CIDR ranges GitHub uses, split by purpose. The
hooks array is where webhook deliveries come from. A firewall allow-list copied
out of the documentation once goes stale as those ranges change, and the failure
is partial: only deliveries leaving from a new range are blocked, which reads as
flakiness rather than as a configuration problem.

The allow-list is a file you export, because the one thing this API can never
read is your own network. The accuracy of the answer is the accuracy of that
export.

Usage:

    python3 github_meta_hook_ranges.py --allowlist firewall-github.txt
"""
import argparse
import ipaddress
import json
import logging
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_meta_hook_ranges")

META = "https://api.github.com/meta"
UA = "github-meta-hook-ranges/1.0"

# The array that answers this question, and the ones a list is most often built
# from by mistake. api and web are inbound: they are where you connect to.
HOOKS = "hooks"
OTHER_ARRAYS = ("api", "web", "git", "packages", "actions", "dependabot")
# How much better another array has to score before the finding is "you copied
# the wrong list" rather than "your list has drifted".
WRONG_ARRAY_MARGIN = 0.5


def parse_cidr(text):
    """(version, first_address, last_address) for one entry, or None. Pure.

    Host bits are tolerated, because firewall exports are full of 10.0.0.1/8 and
    refusing them would drop real rules on the floor.
    """
    raw = str(text or "").split("#")[0].strip()
    if not raw:
        return None
    try:
        net = ipaddress.ip_network(raw, strict=False)
    except ValueError:
        return None
    return (net.version, int(net.network_address), int(net.broadcast_address))


def read_allowlist(lines):
    """(ranges, unreadable) from an exported rule list. Pure.

    Unreadable lines are returned rather than skipped. A rule this script cannot
    parse is a hole in the audit, and silently ignoring it would report better
    coverage than the caller actually has.
    """
    ranges, unreadable = [], []
    for line in lines or []:
        text = str(line).split("#")[0].strip()
        if not text:
            continue
        parsed = parse_cidr(text)
        if parsed is None:
            unreadable.append(text)
        else:
            ranges.append(parsed)
    return ranges, unreadable


def size_of(rng):
    """How many addresses a parsed range holds. Pure."""
    return rng[2] - rng[1] + 1


def overlap(a, b):
    """The addresses two ranges share, or None. Pure."""
    if a[0] != b[0]:
        return None
    start, end = max(a[1], b[1]), min(a[2], b[2])
    return (start, end) if start <= end else None


def merge(intervals):
    """Merge overlapping and adjacent intervals. Pure.

    Without this, two allow-list entries that overlap would have their shared
    addresses counted twice and a range could report as more than fully covered.
    """
    out = []
    for start, end in sorted(intervals):
        if out and start <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [(start, end) for start, end in out]


def covered_addresses(published, allowed):
    """How many addresses of one published range the allow-list permits. Pure."""
    pieces = [piece for piece in (overlap(published, a) for a in allowed) if piece]
    return sum(end - start + 1 for start, end in merge(pieces))


def coverage(published, allowed):
    """(state, fraction) for one published range. Pure.

    Measured over addresses rather than over the text of the CIDRs, so an
    equivalent rewrite of a range is full coverage and a subset is partial with
    the fraction it really permits.
    """
    total = size_of(published)
    covered = covered_addresses(published, allowed)
    if covered <= 0:
        return ("none", 0.0)
    if covered >= total:
        return ("full", 1.0)
    return ("partial", covered / total)


def allows_everything(allowed):
    """Whether a default route makes the allow-list decorative. Pure."""
    for version, start, end in allowed:
        bits = 32 if version == 4 else 128
        if start == 0 and end == (1 << bits) - 1:
            return True
    return False


def audit(published_cidrs, allowed):
    """[(cidr, state, fraction)] for every published range. Pure."""
    rows = []
    for cidr in published_cidrs or []:
        parsed = parse_cidr(cidr)
        if parsed is None:
            rows.append((str(cidr), "unreadable", 0.0))
            continue
        state, fraction = coverage(parsed, allowed)
        rows.append((str(cidr), state, fraction))
    return rows


def uncovered(rows):
    """The published ranges that are not fully covered. Pure."""
    return [cidr for cidr, state, _ in rows if state != "full"]


def array_score(meta, allowed, key):
    """Mean coverage of one /meta array by the allow-list, 0 to 1. Pure."""
    values = (meta or {}).get(key)
    if not isinstance(values, list) or not values:
        return 0.0
    rows = audit(values, allowed)
    return sum(fraction for _, _, fraction in rows) / len(rows)


def best_other_array(meta, allowed):
    """(key, score) for the non-hooks array the allow-list matches best. Pure."""
    best, score = None, 0.0
    for key in OTHER_ARRAYS:
        value = array_score(meta, allowed, key)
        if value > score:
            best, score = key, value
    return (best, score)


def verdict(meta, allowed, unreadable=0):
    """Turn the comparison into a finding. Pure."""
    published = (meta or {}).get(HOOKS)
    if not isinstance(published, list) or not published:
        return ("no-hooks-array",
                "GET /meta did not return a hooks array. Nothing can be "
                "compared until it does.")
    if not allowed:
        return ("no-allowlist",
                "the allow-list is empty, so either nothing is permitted or the "
                "export is wrong. Check the export before reading anything else "
                "here.")
    if allows_everything(allowed):
        return ("allow-all",
                "the allow-list contains a default route, so every published "
                "range is covered and the control is not filtering anything. "
                "This audit will pass forever and mean nothing.")
    rows = audit(published, allowed)
    missing = uncovered(rows)
    hooks_score = array_score(meta, allowed, HOOKS)
    other, other_score = best_other_array(meta, allowed)
    if missing and other and other_score > hooks_score + WRONG_ARRAY_MARGIN:
        return ("wrong-array",
                "the allow-list covers the %s ranges %d%% and the hooks ranges "
                "%d%%. This list was built from the wrong section of GET /meta: "
                "%s is inbound traffic, and webhooks arrive from hooks."
                % (other, round(other_score * 100), round(hooks_score * 100), other))
    if missing:
        return ("drifted",
                "%d of %d published hook ranges are not fully covered by the "
                "allow-list. Partial coverage fails intermittently, which is "
                "why this reads as flakiness rather than as a blocked range."
                % (len(missing), len(rows)))
    if unreadable:
        return ("current-with-gaps",
                "every published hook range is covered, but %d allow-list "
                "entries could not be parsed and were left out of the audit."
                % unreadable)
    return ("current",
            "every published hook range is fully covered by the allow-list.")


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state in ("drifted", "current-with-gaps"):
        return ("generate the allow-list from GET /meta on a schedule rather "
                "than maintaining it by hand, and alert when the published set "
                "changes so the next change is a pull request instead of an "
                "incident. The current set is printed below in full.")
    if state == "wrong-array":
        return ("rebuild the allow-list from the hooks array. The array in use "
                "is where GitHub serves traffic you connect to, not where "
                "webhook deliveries come from.")
    if state == "allow-all":
        return ("remove the default route or accept that this control does "
                "nothing. Either way, verify X-Hub-Signature-256 on every "
                "request: the signature is what authenticates an event, and an "
                "IP list never was.")
    if state == "no-allowlist":
        return ("export the rules from the device or the infrastructure code "
                "that defines them, one CIDR per line, and run this again.")
    if state == "current":
        return ("nothing today. Put this on a schedule so the answer stays "
                "true, and keep signature verification as the real control.")
    return "nothing."


def fetch_meta(session):
    """The published ranges. Unauthenticated on purpose."""
    r = session.get(META, timeout=30)
    if r.status_code != 200:
        log.error("GET /meta returned %d", r.status_code)
        return None
    try:
        return r.json()
    except ValueError:
        log.error("GET /meta returned a body that is not JSON")
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--allowlist", required=True,
                    help="file of CIDRs your firewall permits, one per line")
    args = ap.parse_args()

    with open(args.allowlist, "r", encoding="utf-8") as fh:
        allowed, unreadable = read_allowlist(fh.readlines())
    for line in unreadable:
        log.warning("allow-list entry not understood, left out of the audit: %s", line)

    session = requests.Session()
    session.headers.update({"Accept": "application/vnd.github+json",
                            "User-Agent": UA})
    meta = fetch_meta(session)
    if meta is None:
        return 2

    published = meta.get(HOOKS) or []
    log.info("GET /meta: %d hooks range(s) published, allow-list holds %d entry/entries",
             len(published), len(allowed))
    rows = audit(published, allowed)
    for cidr, state, fraction in rows:
        log.info("%-22s %-9s %3d%% covered", cidr, state, round(fraction * 100))

    state, detail = verdict(meta, allowed, len(unreadable))
    log.info("%s: %s", state, detail)
    log.info("repair: %s", repair(state))
    if state in ("drifted", "wrong-array", "current-with-gaps"):
        log.info("the published hooks ranges, in full:")
        for cidr in published:
            log.info("  %s", cidr)

    print(json.dumps({
        "published_hooks_ranges": published,
        "allowlist_entries": len(allowed),
        "allowlist_unreadable": unreadable,
        "coverage": [{"cidr": c, "state": s, "fraction": round(f, 4)}
                     for c, s, f in rows],
        "not_fully_covered": uncovered(rows),
        "hooks_score": round(array_score(meta, allowed, HOOKS), 4),
        "best_other_array": best_other_array(meta, allowed)[0],
        "state": state,
        "detail": detail,
        "repair": repair(state),
    }, indent=2, default=str))
    return 1 if state in ("drifted", "wrong-array", "allow-all", "no-allowlist") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-meta-hook-ranges.mjs",
"js": '''/**
 * Compare GitHub's published webhook source ranges against your allow-list.
 *
 * Read only, and unauthenticated: GET /meta needs no token, so the person who
 * owns the firewall can run this without being issued a GitHub credential.
 *
 * The address arithmetic is written out here because there is no address type
 * in the standard library and GitHub publishes IPv6 ranges as well as IPv4.
 *
 * Usage:
 *   node github-meta-hook-ranges.mjs ./firewall-github.txt
 */
import { readFile } from 'node:fs/promises';

const META = 'https://api.github.com/meta';
const UA = 'github-meta-hook-ranges/1.0';

export const HOOKS = 'hooks';
export const OTHER_ARRAYS = ['api', 'web', 'git', 'packages', 'actions', 'dependabot'];
export const WRONG_ARRAY_MARGIN = 0.5;

function isDigits(text, maxLength) {
  if (typeof text !== 'string' || text.length === 0 || text.length > maxLength) return false;
  for (const ch of text) if (ch < '0' || ch > '9') return false;
  return true;
}

function ipv4ToBig(addr) {
  const parts = String(addr).split('.');
  if (parts.length !== 4) return null;
  let n = 0n;
  for (const part of parts) {
    if (!isDigits(part, 3)) return null;
    const value = Number(part);
    if (value > 255) return null;
    n = (n << 8n) | BigInt(value);
  }
  return n;
}

function ipv6ToBig(addr) {
  let text = String(addr).toLowerCase();
  if (text.includes('.')) {
    // An embedded IPv4 tail, as in ::ffff:192.0.2.1.
    const cut = text.lastIndexOf(':');
    const tail = ipv4ToBig(text.slice(cut + 1));
    if (tail === null) return null;
    text = `${text.slice(0, cut + 1)}${(tail >> 16n).toString(16)}:${(tail & 0xffffn).toString(16)}`;
  }
  const halves = text.split('::');
  if (halves.length > 2) return null;
  const head = halves[0] ? halves[0].split(':') : [];
  const tail = halves.length === 2 && halves[1] ? halves[1].split(':') : [];
  if (halves.length === 1 && head.length !== 8) return null;
  if (head.length + tail.length > 8) return null;
  const filler = new Array(8 - head.length - tail.length).fill('0');
  const groups = halves.length === 1 ? head : [...head, ...filler, ...tail];
  let n = 0n;
  for (const group of groups) {
    if (group.length === 0 || group.length > 4) return null;
    for (const ch of group) if (!'0123456789abcdef'.includes(ch)) return null;
    n = (n << 16n) | BigInt(parseInt(group, 16));
  }
  return n;
}

/** {version, start, end} for one entry, or null. Host bits tolerated. Pure. */
export function parseCidr(text) {
  const raw = String(text ?? '').split('#')[0].trim();
  if (!raw) return null;
  const slash = raw.indexOf('/');
  const addr = slash === -1 ? raw : raw.slice(0, slash);
  const prefixText = slash === -1 ? null : raw.slice(slash + 1);
  const version = addr.includes(':') ? 6 : 4;
  const bits = version === 4 ? 32 : 128;
  const base = version === 4 ? ipv4ToBig(addr) : ipv6ToBig(addr);
  if (base === null) return null;
  let prefix = bits;
  if (prefixText !== null) {
    if (!isDigits(prefixText, 3)) return null;
    prefix = Number(prefixText);
    if (prefix > bits) return null;
  }
  const hostBits = BigInt(bits - prefix);
  const start = (base >> hostBits) << hostBits;
  return { version, start, end: start + (1n << hostBits) - 1n };
}

/** [ranges, unreadable] from an exported rule list. Pure. */
export function readAllowlist(lines) {
  const ranges = [];
  const unreadable = [];
  for (const line of lines || []) {
    const text = String(line).split('#')[0].trim();
    if (!text) continue;
    const parsed = parseCidr(text);
    if (parsed === null) unreadable.push(text);
    else ranges.push(parsed);
  }
  return [ranges, unreadable];
}

/** How many addresses a parsed range holds. Pure. */
export function sizeOf(range) {
  return range.end - range.start + 1n;
}

/** The addresses two ranges share, or null. Pure. */
export function overlap(a, b) {
  if (a.version !== b.version) return null;
  const start = a.start > b.start ? a.start : b.start;
  const end = a.end < b.end ? a.end : b.end;
  return start <= end ? { version: a.version, start, end } : null;
}

/** Merge overlapping and adjacent intervals so nothing is counted twice. Pure. */
export function merge(intervals) {
  const sorted = [...intervals].sort((a, b) => {
    if (a.start < b.start) return -1;
    if (a.start > b.start) return 1;
    return 0;
  });
  const out = [];
  for (const piece of sorted) {
    const last = out[out.length - 1];
    if (last && piece.start <= last.end + 1n) {
      last.end = piece.end > last.end ? piece.end : last.end;
    } else {
      out.push({ version: piece.version, start: piece.start, end: piece.end });
    }
  }
  return out;
}

/** How many addresses of one published range the allow-list permits. Pure. */
export function coveredAddresses(published, allowed) {
  const pieces = (allowed || []).map((a) => overlap(published, a)).filter(Boolean);
  return merge(pieces).reduce((total, piece) => total + (piece.end - piece.start + 1n), 0n);
}

/** [state, fraction] for one published range, measured over addresses. Pure. */
export function coverage(published, allowed) {
  const total = sizeOf(published);
  const covered = coveredAddresses(published, allowed);
  if (covered <= 0n) return ['none', 0];
  if (covered >= total) return ['full', 1];
  return ['partial', Number((covered * 10000n) / total) / 10000];
}

/** Whether a default route makes the allow-list decorative. Pure. */
export function allowsEverything(allowed) {
  for (const range of allowed || []) {
    const bits = range.version === 4 ? 32n : 128n;
    if (range.start === 0n && range.end === (1n << bits) - 1n) return true;
  }
  return false;
}

/** [[cidr, state, fraction]] for every published range. Pure. */
export function audit(publishedCidrs, allowed) {
  const rows = [];
  for (const cidr of publishedCidrs || []) {
    const parsed = parseCidr(cidr);
    if (parsed === null) {
      rows.push([String(cidr), 'unreadable', 0]);
      continue;
    }
    const [state, fraction] = coverage(parsed, allowed);
    rows.push([String(cidr), state, fraction]);
  }
  return rows;
}

/** The published ranges that are not fully covered. Pure. */
export function uncovered(rows) {
  return (rows || []).filter(([, state]) => state !== 'full').map(([cidr]) => cidr);
}

/** Mean coverage of one /meta array by the allow-list, 0 to 1. Pure. */
export function arrayScore(meta, allowed, key) {
  const values = (meta || {})[key];
  if (!Array.isArray(values) || values.length === 0) return 0;
  const rows = audit(values, allowed);
  return rows.reduce((sum, [, , fraction]) => sum + fraction, 0) / rows.length;
}

/** [key, score] for the non-hooks array the allow-list matches best. Pure. */
export function bestOtherArray(meta, allowed) {
  let best = null;
  let score = 0;
  for (const key of OTHER_ARRAYS) {
    const value = arrayScore(meta, allowed, key);
    if (value > score) { best = key; score = value; }
  }
  return [best, score];
}

/** Turn the comparison into a finding. Pure. */
export function verdict(meta, allowed, unreadable = 0) {
  const published = (meta || {})[HOOKS];
  if (!Array.isArray(published) || published.length === 0) {
    return ['no-hooks-array',
      'GET /meta did not return a hooks array. Nothing can be compared until it does.'];
  }
  if (!allowed || allowed.length === 0) {
    return ['no-allowlist',
      'the allow-list is empty, so either nothing is permitted or the export is '
      + 'wrong. Check the export before reading anything else here.'];
  }
  if (allowsEverything(allowed)) {
    return ['allow-all',
      'the allow-list contains a default route, so every published range is '
      + 'covered and the control is not filtering anything. This audit will pass '
      + 'forever and mean nothing.'];
  }
  const rows = audit(published, allowed);
  const missing = uncovered(rows);
  const hooksScore = arrayScore(meta, allowed, HOOKS);
  const [other, otherScore] = bestOtherArray(meta, allowed);
  if (missing.length && other && otherScore > hooksScore + WRONG_ARRAY_MARGIN) {
    return ['wrong-array',
      `the allow-list covers the ${other} ranges ${Math.round(otherScore * 100)}% `
      + `and the hooks ranges ${Math.round(hooksScore * 100)}%. This list was built `
      + `from the wrong section of GET /meta: ${other} is inbound traffic, and `
      + 'webhooks arrive from hooks.'];
  }
  if (missing.length) {
    return ['drifted',
      `${missing.length} of ${rows.length} published hook ranges are not fully `
      + 'covered by the allow-list. Partial coverage fails intermittently, which '
      + 'is why this reads as flakiness rather than as a blocked range.'];
  }
  if (unreadable) {
    return ['current-with-gaps',
      `every published hook range is covered, but ${unreadable} allow-list entries `
      + 'could not be parsed and were left out of the audit.'];
  }
  return ['current', 'every published hook range is fully covered by the allow-list.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (['drifted', 'current-with-gaps'].includes(state)) {
    return 'generate the allow-list from GET /meta on a schedule rather than '
      + 'maintaining it by hand, and alert when the published set changes so the '
      + 'next change is a pull request instead of an incident. The current set is '
      + 'printed below in full.';
  }
  if (state === 'wrong-array') {
    return 'rebuild the allow-list from the hooks array. The array in use is '
      + 'where GitHub serves traffic you connect to, not where webhook '
      + 'deliveries come from.';
  }
  if (state === 'allow-all') {
    return 'remove the default route or accept that this control does nothing. '
      + 'Either way, verify X-Hub-Signature-256 on every request: the signature '
      + 'is what authenticates an event, and an IP list never was.';
  }
  if (state === 'no-allowlist') {
    return 'export the rules from the device or the infrastructure code that '
      + 'defines them, one CIDR per line, and run this again.';
  }
  if (state === 'current') {
    return 'nothing today. Put this on a schedule so the answer stays true, and '
      + 'keep signature verification as the real control.';
  }
  return 'nothing.';
}

async function main() {
  const path = process.argv[2] || process.env.GITHUB_ALLOWLIST;
  if (!path) {
    console.error('usage: node github-meta-hook-ranges.mjs ./firewall-github.txt');
    process.exitCode = 2;
    return;
  }
  const text = await readFile(path, 'utf8');
  const [allowed, unreadable] = readAllowlist(text.split(String.fromCharCode(10)));
  for (const line of unreadable) {
    console.error(`allow-list entry not understood, left out of the audit: ${line}`);
  }

  const res = await fetch(META, {
    headers: { Accept: 'application/vnd.github+json', 'User-Agent': UA },
  });
  if (res.status !== 200) {
    console.error(`GET /meta returned ${res.status}`);
    process.exitCode = 2;
    return;
  }
  const meta = await res.json();
  const published = meta[HOOKS] || [];
  console.log(`GET /meta: ${published.length} hooks range(s) published, `
    + `allow-list holds ${allowed.length} entry/entries`);
  const rows = audit(published, allowed);
  for (const [cidr, state, fraction] of rows) {
    console.log(`${cidr.padEnd(22)} ${state.padEnd(9)} ${Math.round(fraction * 100)}% covered`);
  }
  const [state, detail] = verdict(meta, allowed, unreadable.length);
  console.log(`${state}: ${detail}`);
  console.log(`repair: ${repair(state)}`);
  if (['drifted', 'wrong-array', 'current-with-gaps'].includes(state)) {
    console.log('the published hooks ranges, in full:');
    for (const cidr of published) console.log(`  ${cidr}`);
  }
  console.log(JSON.stringify({
    published_hooks_ranges: published,
    allowlist_entries: allowed.length,
    allowlist_unreadable: unreadable,
    not_fully_covered: uncovered(rows),
    hooks_score: Number(arrayScore(meta, allowed, HOOKS).toFixed(4)),
    best_other_array: bestOtherArray(meta, allowed)[0],
    state,
  }, null, 2));
  process.exitCode = ['drifted', 'wrong-array', 'allow-all', 'no-allowlist']
    .includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Address arithmetic is the kind of code that looks obviously right and is wrong at the edges, so the tests do the edges: a subset reported as a quarter covered rather than as a mismatch, a superset reported as full, two overlapping rules that must not double-count, IPv4 and IPv6 never counted against each other, and a default route recognised in both families. Then the two findings that matter to a reader &mdash; drift and a list built from the wrong array of <code>/meta</code> &mdash; are checked against fixtures shaped like the real response.",
"test_py_file": "test_github_meta_hook_ranges.py",
"test_py": '''from github_meta_hook_ranges import (
    allows_everything, array_score, audit, best_other_array, coverage,
    covered_addresses, merge, overlap, parse_cidr, read_allowlist, repair,
    size_of, uncovered, verdict,
)

META = {
    "hooks": ["192.30.252.0/22", "140.82.112.0/20", "2a0a:a440::/29"],
    "api": ["10.10.0.0/16", "10.20.0.0/16"],
    "web": ["10.30.0.0/16"],
}


def parsed(*entries):
    return [parse_cidr(e) for e in entries]


def test_a_cidr_is_parsed_into_a_range_of_addresses():
    version, start, end = parse_cidr("192.30.252.0/22")
    assert version == 4
    assert end - start + 1 == 1024


def test_host_bits_and_bare_addresses_are_tolerated():
    assert parse_cidr("192.30.252.7/22") == parse_cidr("192.30.252.0/22")
    assert size_of(parse_cidr("140.82.112.5")) == 1
    assert parse_cidr("not-an-address") is None
    assert parse_cidr("   ") is None
    assert parse_cidr("# a comment") is None


def test_ipv6_ranges_are_understood():
    version, start, end = parse_cidr("2a0a:a440::/29")
    assert version == 6
    assert end > start


def test_the_two_families_never_cover_each_other():
    assert overlap(parse_cidr("0.0.0.0/0"), parse_cidr("2a0a:a440::/29")) is None
    assert coverage(parse_cidr("2a0a:a440::/29"), parsed("0.0.0.0/0")) == ("none", 0.0)


def test_a_subset_is_partial_with_the_fraction_it_permits():
    state, fraction = coverage(parse_cidr("192.30.252.0/22"), parsed("192.30.252.0/24"))
    assert state == "partial"
    assert round(fraction, 4) == 0.25


def test_a_superset_is_full_coverage_not_a_mismatch():
    assert coverage(parse_cidr("140.82.112.0/20"), parsed("140.82.0.0/16")) == ("full", 1.0)


def test_overlapping_rules_are_never_counted_twice():
    published = parse_cidr("192.30.252.0/22")
    allowed = parsed("192.30.252.0/24", "192.30.252.0/23")
    assert covered_addresses(published, allowed) == 512
    assert coverage(published, allowed)[0] == "partial"


def test_adjacent_rules_add_up_to_full_coverage():
    published = parse_cidr("192.30.252.0/23")
    allowed = parsed("192.30.252.0/24", "192.30.253.0/24")
    assert coverage(published, allowed) == ("full", 1.0)
    assert len(merge([overlap(published, a) for a in allowed])) == 1


def test_a_default_route_is_recognised_in_both_families():
    assert allows_everything(parsed("0.0.0.0/0"))
    assert allows_everything(parsed("::/0"))
    assert not allows_everything(parsed("10.0.0.0/8"))


def test_unreadable_allowlist_lines_are_returned_not_swallowed():
    ranges, unreadable = read_allowlist([
        "192.30.252.0/22", "  # comment", "", "140.82.112.0/20 # inline",
        "hooks.github.com",
    ])
    assert len(ranges) == 2
    assert unreadable == ["hooks.github.com"]


def test_the_audit_names_every_published_range():
    rows = audit(META["hooks"], parsed("140.82.112.0/20"))
    assert [state for _, state, _ in rows] == ["none", "full", "none"]
    assert uncovered(rows) == ["192.30.252.0/22", "2a0a:a440::/29"]


def test_drift_is_the_finding_when_some_ranges_are_short():
    allowed = parsed("192.30.252.0/24", "140.82.112.0/20", "2a0a:a440::/29")
    state, detail = verdict(META, allowed)
    assert state == "drifted"
    assert "1 of 3" in detail
    assert "intermittently" in detail


def test_a_list_built_from_the_wrong_array_is_named_as_such():
    allowed = parsed("10.10.0.0/16", "10.20.0.0/16")
    state, detail = verdict(META, allowed)
    assert state == "wrong-array"
    assert "api" in detail
    assert round(array_score(META, allowed, "api"), 4) == 1.0
    assert best_other_array(META, allowed)[0] == "api"


def test_a_default_route_passes_the_arithmetic_and_still_fails_the_audit():
    state, detail = verdict(META, parsed("0.0.0.0/0", "::/0"))
    assert state == "allow-all"
    assert "not filtering" in detail
    assert "never was" in repair("allow-all")


def test_a_complete_allowlist_is_current():
    allowed = parsed("192.30.252.0/22", "140.82.112.0/20", "2a0a:a440::/29")
    assert verdict(META, allowed)[0] == "current"


def test_unparsed_entries_downgrade_a_clean_result():
    allowed = parsed("192.30.252.0/22", "140.82.112.0/20", "2a0a:a440::/29")
    state, detail = verdict(META, allowed, unreadable=2)
    assert state == "current-with-gaps"
    assert "2 allow-list entries" in detail


def test_an_empty_allowlist_is_reported_rather_than_scored():
    assert verdict(META, [])[0] == "no-allowlist"
    assert verdict({}, parsed("10.0.0.0/8"))[0] == "no-hooks-array"


def test_the_repair_for_drift_is_automation_and_not_a_fresh_paste():
    assert "on a schedule" in repair("drifted")
    assert "hooks array" in repair("wrong-array")
''',
"test_js_file": "github-meta-hook-ranges.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  allowsEverything, arrayScore, audit, bestOtherArray, coverage,
  coveredAddresses, merge, overlap, parseCidr, readAllowlist, repair, sizeOf,
  uncovered, verdict,
} from './github-meta-hook-ranges.mjs';

const META = {
  hooks: ['192.30.252.0/22', '140.82.112.0/20', '2a0a:a440::/29'],
  api: ['10.10.0.0/16', '10.20.0.0/16'],
  web: ['10.30.0.0/16'],
};

const parsed = (...entries) => entries.map((e) => parseCidr(e));

test('a CIDR is parsed into a range of addresses', () => {
  const range = parseCidr('192.30.252.0/22');
  assert.equal(range.version, 4);
  assert.equal(sizeOf(range), 1024n);
});

test('host bits and bare addresses are tolerated', () => {
  assert.deepEqual(parseCidr('192.30.252.7/22'), parseCidr('192.30.252.0/22'));
  assert.equal(sizeOf(parseCidr('140.82.112.5')), 1n);
  assert.equal(parseCidr('not-an-address'), null);
  assert.equal(parseCidr('   '), null);
  assert.equal(parseCidr('# a comment'), null);
});

test('ipv6 ranges are understood, compressed and expanded alike', () => {
  const range = parseCidr('2a0a:a440::/29');
  assert.equal(range.version, 6);
  assert.ok(range.end > range.start);
  assert.equal(parseCidr('2a0a:a440:0:0:0:0:0:0/29').start, range.start);
  assert.equal(parseCidr('2a0a:a440::zz/29'), null);
});

test('the two families never cover each other', () => {
  assert.equal(overlap(parseCidr('0.0.0.0/0'), parseCidr('2a0a:a440::/29')), null);
  assert.deepEqual(coverage(parseCidr('2a0a:a440::/29'), parsed('0.0.0.0/0')), ['none', 0]);
});

test('a subset is partial with the fraction it permits', () => {
  const [state, fraction] = coverage(parseCidr('192.30.252.0/22'), parsed('192.30.252.0/24'));
  assert.equal(state, 'partial');
  assert.equal(fraction, 0.25);
});

test('a superset is full coverage, not a mismatch', () => {
  assert.deepEqual(coverage(parseCidr('140.82.112.0/20'), parsed('140.82.0.0/16')), ['full', 1]);
});

test('overlapping rules are never counted twice', () => {
  const published = parseCidr('192.30.252.0/22');
  const allowed = parsed('192.30.252.0/24', '192.30.252.0/23');
  assert.equal(coveredAddresses(published, allowed), 512n);
  assert.equal(coverage(published, allowed)[0], 'partial');
});

test('adjacent rules add up to full coverage', () => {
  const published = parseCidr('192.30.252.0/23');
  const allowed = parsed('192.30.252.0/24', '192.30.253.0/24');
  assert.deepEqual(coverage(published, allowed), ['full', 1]);
  assert.equal(merge(allowed.map((a) => overlap(published, a))).length, 1);
});

test('a default route is recognised in both families', () => {
  assert.ok(allowsEverything(parsed('0.0.0.0/0')));
  assert.ok(allowsEverything(parsed('::/0')));
  assert.ok(!allowsEverything(parsed('10.0.0.0/8')));
});

test('unreadable allow-list lines are returned, not swallowed', () => {
  const [ranges, unreadable] = readAllowlist([
    '192.30.252.0/22', '  # comment', '', '140.82.112.0/20 # inline', 'hooks.github.com',
  ]);
  assert.equal(ranges.length, 2);
  assert.deepEqual(unreadable, ['hooks.github.com']);
});

test('the audit names every published range', () => {
  const rows = audit(META.hooks, parsed('140.82.112.0/20'));
  assert.deepEqual(rows.map(([, state]) => state), ['none', 'full', 'none']);
  assert.deepEqual(uncovered(rows), ['192.30.252.0/22', '2a0a:a440::/29']);
});

test('drift is the finding when some ranges are short', () => {
  const allowed = parsed('192.30.252.0/24', '140.82.112.0/20', '2a0a:a440::/29');
  const [state, detail] = verdict(META, allowed);
  assert.equal(state, 'drifted');
  assert.match(detail, /1 of 3/);
  assert.match(detail, /intermittently/);
});

test('a list built from the wrong array is named as such', () => {
  const allowed = parsed('10.10.0.0/16', '10.20.0.0/16');
  const [state, detail] = verdict(META, allowed);
  assert.equal(state, 'wrong-array');
  assert.match(detail, /api/);
  assert.equal(arrayScore(META, allowed, 'api'), 1);
  assert.equal(bestOtherArray(META, allowed)[0], 'api');
});

test('a default route passes the arithmetic and still fails the audit', () => {
  const [state, detail] = verdict(META, parsed('0.0.0.0/0', '::/0'));
  assert.equal(state, 'allow-all');
  assert.match(detail, /not filtering/);
  assert.match(repair('allow-all'), /never was/);
});

test('a complete allow-list is current', () => {
  const allowed = parsed('192.30.252.0/22', '140.82.112.0/20', '2a0a:a440::/29');
  assert.equal(verdict(META, allowed)[0], 'current');
});

test('unparsed entries downgrade a clean result', () => {
  const allowed = parsed('192.30.252.0/22', '140.82.112.0/20', '2a0a:a440::/29');
  const [state, detail] = verdict(META, allowed, 2);
  assert.equal(state, 'current-with-gaps');
  assert.match(detail, /2 allow-list entries/);
});

test('an empty allow-list is reported rather than scored', () => {
  assert.equal(verdict(META, [])[0], 'no-allowlist');
  assert.equal(verdict({}, parsed('10.0.0.0/8'))[0], 'no-hooks-array');
});

test('the repair for drift is automation and not a fresh paste', () => {
  assert.match(repair('drifted'), /on a schedule/);
  assert.match(repair('wrong-array'), /hooks array/);
});
''',
"faq": [
 ("Does GET /meta need a token?",
  "No. It is unauthenticated, which is deliberate on GitHub's part and useful on yours: the person who owns the firewall can run this check without being issued a GitHub credential at all, and the check can live in network tooling that has no business holding one. Unauthenticated requests share the anonymous limit of sixty an hour per source address, so an hourly job has plenty of room. If you already have a read-only token you can send it and get the authenticated limit instead, but nothing about the answer changes."),
 ("Why does it fail for some deliveries and not others?",
  "Because GitHub delivers from a pool of addresses rather than one, so a range your firewall does not know about only affects the deliveries that happen to leave from it. If one of eight published ranges is blocked you lose something like an eighth of your events, distributed randomly, which is the single hardest failure shape to notice. It has no pattern in event type, repository or time, so it gets absorbed as flakiness and retried by hand until somebody finally correlates it with source IP."),
 ("Can the script read my firewall?",
  "No, and that is the honest boundary of this note. Everything else in this section is answered by the GitHub API; here the API only holds half the comparison. You export the rules, the script reads the published ranges, and the arithmetic happens between them. Export from the device or from the infrastructure code that defines it rather than from a wiki page, because the difference between what is documented and what is deployed is often the entire bug."),
 ("We allow-listed GitHub's IP ranges. Why is the note saying we used the wrong ones?",
  "<code>GET /meta</code> returns several arrays and they point in opposite directions. <code>api</code>, <code>web</code> and <code>git</code> are where you connect to GitHub; <code>hooks</code> is where GitHub connects to you. Both are full of legitimate GitHub addresses, which is why a list built from the wrong one survives review. The script scores your list against every array in the response, so if it matches <code>api</code> perfectly and <code>hooks</code> barely at all, it says so instead of reporting eight separate blocked ranges."),
 ("Is IP allow-listing worth doing at all?",
  "As a blast-radius control, yes: it means a leaked URL cannot be hit from anywhere on the internet. As authentication, no, and treating it as authentication is how this becomes a real outage rather than a tidy-up. It fails open against anything that can route from a permitted address, and it fails closed the moment the published set moves, which is a control that hurts you when it ages and does not save you when it matters. Verify <code>X-Hub-Signature-256</code> on every request and keep the allow-list as the second layer it is."),
],
"related": [
 ("/github/webhook-deliveries-failing/", "Deliveries failing where nobody reads the log"),
 ("/github/webhook-inactive/", "The hook exists but somebody switched it off"),
 ("/github/webhook-no-secret/", "A webhook with no secret sends no signature"),
],
"citations": [CITE_META, CITE_IP_ADDRESSES, CITE_TROUBLESHOOT, CITE_WEBHOOK_BEST],
},


{
"slug": "webhook-secret-never-rotated",
"title": "The webhook secret is set and has never been rotated",
"description": "config.secret comes back masked, so the API cannot date it. updated_at is the only clock there is, and it is conclusive in exactly one direction.",
"h1": "the webhook secret is set and has never been rotated",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["rotate github webhook secret",
             "github webhook secret age updated_at",
             "github webhook secret rotation overlap window",
             "github webhook secret never expires",
             "github webhook secret masked api"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "There is no symptom. The hook works, the signatures verify, the deliveries are green, and the secret that authenticates every event has been sitting in the same configuration file since the integration was built. It has outlasted two contractors, a laptop that was never wiped, and a support ticket where somebody pasted the receiver's environment into a chat window to get help.",
"short_answer": """<p>This is the opposite state to <a href=\"/github/webhook-no-secret/\">a hook with no secret</a>. The secret is set, <code>config.secret</code> comes back as <code>********</code>, and everything is working. The question is how old it is, and the API will not answer it: the value is masked and there is no field anywhere that dates it.</p>
<p>What you can read is <code>updated_at</code> on the hook, which moves whenever the hook's configuration changes. That makes it a one-directional signal, and the direction is the useful one. A hook untouched for four years cannot have had its secret rotated in four years, because rotating it is an edit and an edit moves the timestamp. A hook edited last week proves nothing at all, since the edit may have been the URL. The script argues only in the direction the evidence supports and says which one it is in. Where you can tell it when you last rotated, it does one more thing: if your records claim a rotation the hook's own timestamp predates, the rotation never reached GitHub.</p>""",
"problem": """<p>Nothing brings this to anybody's attention, which is the whole difficulty. Credentials that expire get rotated because they force the issue; a GitHub webhook secret never expires, is never flagged, and appears in no dashboard. The integration keeps working, so there is no incident to attach the work to and no date at which somebody has to care.</p>
<p>Meanwhile the population of people who have seen the value only ever grows. It is in the receiver's environment, so it is in whatever holds that configuration, and probably in a second place because staging needs one too. It was pasted into a terminal during setup. It may be in a CI variable, in a screenshot in a ticket, in the shell history of a machine that has since been sold. None of that is negligence; it is what happens to a value that lives for six years and is needed by every deployment.</p>
<p>When the question finally does get asked &mdash; usually during an audit, or after somebody leaves in a way that makes people think &mdash; the answer is not in the API. Somebody looks at the hook, sees <code>secret: ********</code>, and reports that a secret is configured, which was never the question. Then the argument runs on vibes: it was probably rotated at some point, wasn't it, we changed something in there once. The hook's own timestamp settles that in one read, and usually settles it in the unwelcome direction.</p>
<p>There is a second failure hiding under this one, and it is the reason to reconcile against your records rather than just reading the age. Rotation is a two-sided change: the value has to move on GitHub and in the receiver. When it is done under pressure, the receiver gets the new value, the hook does not, signatures start failing, and somebody reverts the receiver to the old value to stop the bleeding. The runbook is then marked done. The secret was never rotated at all, and the record says it was.</p>""",
"why": """<p><strong>The value is unreadable, so the note is honest about using a proxy.</strong> <code>config.secret</code> is masked when set and absent when not. There is no created, rotated or expires field for it anywhere in the API. Every claim this script makes about age comes from <code>updated_at</code>, and the output says so rather than presenting an inference as a measurement.</p>
<p><strong>The proxy is conclusive in one direction only.</strong> <code>updated_at</code> moves on any change to the hook: the URL, the events array, the active flag, the content type, the secret. So an old timestamp is proof of no rotation, because a rotation would have moved it. A new timestamp is proof of an edit, and nothing more. Treating a recent <code>updated_at</code> as evidence of a recent rotation is the mistake this note is designed to stop, and the script reports that case as inconclusive rather than as healthy.</p>
<p><strong>A hook whose <code>created_at</code> and <code>updated_at</code> agree has never been touched at all.</strong> That is the strongest form of the finding: the configuration is exactly as it was created, so the secret is the original one, and its age is the age of the integration. It is also the most common shape, because hooks are set up once by whoever built the thing and then left alone.</p>
<p><strong>Your own records are the other half, and they can be wrong in a way the API can catch.</strong> If you claim a rotation on a date and the hook's <code>updated_at</code> is older than that date, the hook has not been modified since before the claimed rotation, so whatever was rotated, it was not this. That is a genuine finding produced entirely from read-only data, and it catches the half-applied rotation that quietly left the old secret in place.</p>
<p><strong>Rotation is not the whole repair for a leaked secret.</strong> If the value went somewhere it should not have, rotating removes future access and does nothing about events already captured or about the replay window on anything still in flight. Rotate, then look at what else was in that environment, because a webhook secret rarely leaks alone.</p>""",
"steps": [
 {"h": "Split the hooks that have a secret from the ones that do not",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks</code>, and add <code>GET /orgs/{org}/hooks</code> if you own the organization, because rotation is an org-wide process problem rather than a repository one. A hook with no <code>secret</code> key in <code>config</code> is a different finding with a different note; this script says so and moves on rather than folding two problems into one number.</p>"""},
 {"h": "Read the only clock there is",
  "body": """<p><code>updated_at</code> on the hook, compared against today. Compare it with <code>created_at</code> too: if they agree, the hook has never been edited since it was made, and the secret is the one it was born with. Neither field dates the secret directly, and the script never claims they do.</p>"""},
 {"h": "Argue in the direction the evidence supports",
  "body": """<p>Past your rotation interval, the age is conclusive: no rotation has happened in that window, whatever anybody remembers. Inside it, the age proves nothing, because the edit could have been anything. Report those two cases with different words. A check that calls a recently edited hook compliant is worse than no check, because it produces a green tick for a secret nobody has touched in years.</p>"""},
 {"h": "Reconcile the hook against your own rotation record",
  "body": """<p>Give the script the date you believe the secret was last rotated. If the hook's <code>updated_at</code> is earlier than that date, the hook was not modified at or after it, so the rotation did not land on GitHub &mdash; the runbook was marked done with only the receiver updated. This is the finding worth going looking for, and it is invisible until you compare the two sides.</p>"""},
 {"h": "Rotate with an overlap window rather than a cutover",
  "body": """<p>Teach the receiver to accept a signature from either the current or the previous secret, deploy that, then change the secret on GitHub, then remove the old value once deliveries have settled. A straight swap drops every event in flight during the gap and, worse, produces a burst of signature failures that looks exactly like an attack. This script cannot perform any of it: changing a hook is a write, and this section does not write.</p>"""},
],
"verify": """<p>Read-only, and cheap enough to run on a schedule so the age is a number somebody sees rather than a question nobody asks.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$RO_TOKEN python3 github_hook_secret_age.py --repo acme/payments --max-age-days 180
# hook 4218871 https://hooks.example.com/github secret=set
# created 2019-04-11, updated 2019-04-11, unedited since creation
# overdue: the hook has not been edited for 2698 days, so its secret has not
# been rotated for at least that long. created_at and updated_at agree, so this
# is the secret the hook was created with.
# repair: rotate with an overlap window: teach the receiver to accept the old
# and the new secret, change it on GitHub, then drop the old value.

# and the one worth going looking for
GITHUB_TOKEN=$RO_TOKEN python3 github_hook_secret_age.py --repo acme/payments --rotated-on 2026-02-14
# rotation-not-applied: the record claims a rotation on 2026-02-14, but the hook
# has not been edited since 2019-04-11. Whatever was rotated, it was not this.</code></pre>""",
"code_intro": "The secret never enters the program. <code>secret_state</code> answers a question about presence, and <code>redact</code> exists so that anything printed is built from a config the value has already been removed from &mdash; there is a test that puts a value where the mask should be and asserts it does not come out the other end. The rest is dates, and the care is all in the wording: the function that decides what the age proves has two branches and they are not two grades of the same answer, they are a finding and an admission.",
"py_file": "github_hook_secret_age.py",
"py": '''"""Say how long a webhook secret has gone without being rotated.

Read only. One GET per scope: the repository hook list, and the organization
hook list where the caller owns the organization. Nothing is changed, and no
secret value is ever read, held or printed.

This is the opposite finding to a hook with no secret. Here a secret is set and
working; the question is its age. The API will not answer that: config.secret is
masked and nothing dates it. updated_at on the hook is the only clock available,
and it moves on any edit, which makes it conclusive in exactly one direction. An
old timestamp proves no rotation. A recent one proves an edit and nothing else.

Where the caller can say when they last rotated, one more thing is checkable: a
claimed rotation that predates the hook's own updated_at never reached GitHub.

Environment:

    GITHUB_TOKEN   a read-only token with access to the repository
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_secret_age")

API = "https://api.github.com"
UA = "github-hook-secret-age/1.0"

# No published guidance exists for how often a webhook secret should be rotated,
# so this is a policy number rather than a fact. The value of the check is that
# somebody chose one.
DEFAULT_MAX_AGE_DAYS = 180
# created_at and updated_at written by the same request can differ by a second.
UNEDITED_TOLERANCE_SECONDS = 60


def secret_state(config):
    """Whether a secret is configured. Never returns the value. Pure.

    GitHub masks a set secret and omits the key when there is none, so presence
    is the only readable fact and it is the only one this function reports.
    """
    if not isinstance(config, dict):
        return "unknown"
    return "set" if config.get("secret") is not None else "absent"


def redact(config):
    """A copy of a hook config that is safe to print. Pure.

    The masked value never needs to leave the response, and building the report
    from this rather than from the raw config means a future change to what the
    API returns cannot turn into a secret in a log file.
    """
    if not isinstance(config, dict):
        return {}
    safe = {k: v for k, v in config.items() if k != "secret"}
    safe["secret"] = secret_state(config)
    return safe


def parse_time(text):
    """An ISO 8601 timestamp as an aware datetime, or None. Pure."""
    raw = str(text or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def age_days(text, now):
    """Whole days between a timestamp and now, or None. Pure."""
    moment = parse_time(text)
    if moment is None or now is None:
        return None
    return int((now - moment).total_seconds() // 86400)


def unedited_since_creation(created_at, updated_at):
    """Whether the hook is exactly as it was created. Pure."""
    created, updated = parse_time(created_at), parse_time(updated_at)
    if created is None or updated is None:
        return False
    return abs((updated - created).total_seconds()) <= UNEDITED_TOLERANCE_SECONDS


def evidence_direction(age, threshold):
    """What the age of the last edit actually proves. Pure.

    These are not two grades of the same answer. Past the threshold the age is a
    lower bound on the secret's age and the finding stands on its own. Inside it,
    the edit could have been the URL, and the honest report is that nothing is
    known. Calling that second case healthy is the mistake this exists to avoid.
    """
    if age is None:
        return "unknown"
    return "conclusive" if age >= int(threshold) else "inconclusive"


def reconcile(updated_at, claimed, now=None):
    """Compare a claimed rotation date against the hook's own timestamp. Pure."""
    claim = parse_time(claimed)
    updated = parse_time(updated_at)
    if claim is None or updated is None:
        return "unknown"
    if updated < claim:
        return "not-applied"
    return "consistent"


def verdict(config, created_at, updated_at, now, threshold=DEFAULT_MAX_AGE_DAYS,
            claimed=None):
    """Turn presence, age and any claimed rotation into a finding. Pure."""
    state = secret_state(config)
    if state != "set":
        return ("no-secret",
                "this hook has no secret at all, so there is nothing to rotate "
                "and every delivery arrives unsigned. That is a different and "
                "larger finding than this one.")
    age = age_days(updated_at, now)
    if age is None:
        return ("age-unknown",
                "a secret is set, but updated_at could not be read, so nothing "
                "about its age can be established from here.")
    if claimed:
        agreement = reconcile(updated_at, claimed)
        if agreement == "not-applied":
            return ("rotation-not-applied",
                    "the record claims a rotation on %s, but the hook has not "
                    "been edited since %s. Changing a secret is an edit, so "
                    "whatever was rotated, it was not this hook."
                    % (str(claimed)[:10], str(updated_at)[:10]))
    origin = ("created_at and updated_at agree, so this is the secret the hook "
              "was created with." if unedited_since_creation(created_at, updated_at)
              else "the hook has been edited since it was created, though not "
                   "necessarily its secret.")
    if evidence_direction(age, threshold) == "conclusive":
        return ("overdue",
                "the hook has not been edited for %d days, so its secret has "
                "not been rotated for at least that long. %s" % (age, origin))
    return ("inconclusive",
            "the hook was edited %d days ago, which is inside the rotation "
            "interval, but an edit is not a rotation: updated_at moves for a "
            "URL change too. This is unknown rather than compliant." % age)


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state in ("overdue", "rotation-not-applied"):
        return ("rotate with an overlap window: teach the receiver to accept a "
                "signature from the old or the new secret, deploy that, change "
                "the secret on GitHub, then drop the old value once deliveries "
                "have settled. A straight swap loses whatever is in flight.")
    if state == "inconclusive":
        return ("record rotations somewhere the next person can read, and run "
                "this again with that date. The API cannot date a secret, so a "
                "written record is the only thing that turns this into an answer.")
    if state == "no-secret":
        return ("set a secret on the hook and verify X-Hub-Signature-256 in the "
                "receiver. Age is not the problem here.")
    if state == "age-unknown":
        return "read created_at and updated_at on the hook by hand."
    return "nothing."


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    r = session.get(API + path, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def hooks_at(session, path, label):
    """Every hook at one scope."""
    status, body = get(session, path)
    if status != 200 or not isinstance(body, list):
        log.info("GET %s returned %d; %s hooks are not readable with this token",
                 path, status, label)
        return []
    return body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPO"),
                    help="owner/name of the repository holding the hook")
    ap.add_argument("--org", default=os.environ.get("GITHUB_ORG"),
                    help="organization to audit as well, if you can read it")
    ap.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS,
                    help="your rotation interval. There is no published one")
    ap.add_argument("--rotated-on", default=None,
                    help="the date your records claim the secret was last "
                         "rotated, as YYYY-MM-DD")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN to a read-only token")
        return 2
    if not args.repo and not args.org:
        log.error("set --repo, --org, or both")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    now = datetime.now(timezone.utc)
    scopes = []
    if args.repo:
        scopes.append(("/repos/%s/hooks?per_page=100" % args.repo, args.repo))
    if args.org:
        scopes.append(("/orgs/%s/hooks?per_page=100" % args.org, args.org))

    report = []
    findings = 0
    for path, label in scopes:
        for hook in hooks_at(session, path, label):
            config = hook.get("config") or {}
            safe = redact(config)
            log.info("hook %s %s secret=%s", hook.get("id"), safe.get("url"),
                     safe.get("secret"))
            log.info("created %s, updated %s, %s",
                     str(hook.get("created_at"))[:10], str(hook.get("updated_at"))[:10],
                     "unedited since creation"
                     if unedited_since_creation(hook.get("created_at"),
                                                hook.get("updated_at"))
                     else "edited since creation")
            state, detail = verdict(config, hook.get("created_at"),
                                    hook.get("updated_at"), now,
                                    args.max_age_days, args.rotated_on)
            log.info("%s: %s", state, detail)
            log.info("repair: %s", repair(state))
            if state in ("overdue", "rotation-not-applied", "no-secret"):
                findings += 1
            report.append({
                "scope": label,
                "hook_id": hook.get("id"),
                "config": safe,
                "created_at": hook.get("created_at"),
                "updated_at": hook.get("updated_at"),
                "days_since_edit": age_days(hook.get("updated_at"), now),
                "unedited_since_creation": unedited_since_creation(
                    hook.get("created_at"), hook.get("updated_at")),
                "evidence": evidence_direction(
                    age_days(hook.get("updated_at"), now), args.max_age_days),
                "rotation_record": reconcile(hook.get("updated_at"), args.rotated_on),
                "state": state,
                "detail": detail,
                "repair": repair(state),
            })

    print(json.dumps({"rotation_interval_days": args.max_age_days,
                      "hooks": report}, indent=2, default=str))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-secret-age.mjs",
"js": '''/**
 * Say how long a webhook secret has gone without being rotated.
 *
 * Read only. One GET per scope. Nothing is changed, and no secret value is ever
 * read, held or printed: presence is the only readable fact and the only one
 * this program reports.
 *
 * updated_at is the only clock the API offers, and it moves on any edit, which
 * makes it conclusive in one direction. An old timestamp proves no rotation. A
 * recent one proves an edit and nothing else.
 *
 * Environment:
 *   GITHUB_TOKEN        a read-only token
 *   GITHUB_REPO         owner/name
 *   GITHUB_ORG          optional, audited as well where readable
 *   GITHUB_ROTATED_ON   optional, the date your records claim, as YYYY-MM-DD
 */
const API = 'https://api.github.com';
const UA = 'github-hook-secret-age/1.0';

/** A policy number, not a published one. The value is in having chosen it. */
export const DEFAULT_MAX_AGE_DAYS = 180;
export const UNEDITED_TOLERANCE_SECONDS = 60;

/** Whether a secret is configured. Never returns the value. Pure. */
export function secretState(config) {
  if (!config || typeof config !== 'object') return 'unknown';
  return config.secret !== null && config.secret !== undefined ? 'set' : 'absent';
}

/** A copy of a hook config that is safe to print. Pure. */
export function redact(config) {
  if (!config || typeof config !== 'object') return {};
  const safe = {};
  for (const [key, value] of Object.entries(config)) {
    if (key !== 'secret') safe[key] = value;
  }
  safe.secret = secretState(config);
  return safe;
}

/** An ISO 8601 timestamp as a Date, or null. Pure. */
export function parseTime(text) {
  const raw = String(text ?? '').trim();
  if (!raw) return null;
  const moment = new Date(raw);
  return Number.isNaN(moment.getTime()) ? null : moment;
}

/** Whole days between a timestamp and now, or null. Pure. */
export function ageDays(text, now) {
  const moment = parseTime(text);
  const at = parseTime(now) || (now instanceof Date ? now : null);
  if (moment === null || at === null) return null;
  return Math.floor((at.getTime() - moment.getTime()) / 86400000);
}

/** Whether the hook is exactly as it was created. Pure. */
export function uneditedSinceCreation(createdAt, updatedAt) {
  const created = parseTime(createdAt);
  const updated = parseTime(updatedAt);
  if (created === null || updated === null) return false;
  return Math.abs(updated.getTime() - created.getTime()) <= UNEDITED_TOLERANCE_SECONDS * 1000;
}

/** What the age of the last edit actually proves. Pure. */
export function evidenceDirection(age, threshold) {
  if (age === null || age === undefined) return 'unknown';
  return age >= Number(threshold) ? 'conclusive' : 'inconclusive';
}

/** Compare a claimed rotation date against the hook's own timestamp. Pure. */
export function reconcile(updatedAt, claimed) {
  const claim = parseTime(claimed);
  const updated = parseTime(updatedAt);
  if (claim === null || updated === null) return 'unknown';
  return updated.getTime() < claim.getTime() ? 'not-applied' : 'consistent';
}

/** Turn presence, age and any claimed rotation into a finding. Pure. */
export function verdict(config, createdAt, updatedAt, now,
                        threshold = DEFAULT_MAX_AGE_DAYS, claimed = null) {
  if (secretState(config) !== 'set') {
    return ['no-secret',
      'this hook has no secret at all, so there is nothing to rotate and every '
      + 'delivery arrives unsigned. That is a different and larger finding than this one.'];
  }
  const age = ageDays(updatedAt, now);
  if (age === null) {
    return ['age-unknown',
      'a secret is set, but updated_at could not be read, so nothing about its '
      + 'age can be established from here.'];
  }
  if (claimed && reconcile(updatedAt, claimed) === 'not-applied') {
    return ['rotation-not-applied',
      `the record claims a rotation on ${String(claimed).slice(0, 10)}, but the `
      + `hook has not been edited since ${String(updatedAt).slice(0, 10)}. Changing `
      + 'a secret is an edit, so whatever was rotated, it was not this hook.'];
  }
  const origin = uneditedSinceCreation(createdAt, updatedAt)
    ? 'created_at and updated_at agree, so this is the secret the hook was created with.'
    : 'the hook has been edited since it was created, though not necessarily its secret.';
  if (evidenceDirection(age, threshold) === 'conclusive') {
    return ['overdue',
      `the hook has not been edited for ${age} days, so its secret has not been `
      + `rotated for at least that long. ${origin}`];
  }
  return ['inconclusive',
    `the hook was edited ${age} days ago, which is inside the rotation interval, `
    + 'but an edit is not a rotation: updated_at moves for a URL change too. '
    + 'This is unknown rather than compliant.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (['overdue', 'rotation-not-applied'].includes(state)) {
    return 'rotate with an overlap window: teach the receiver to accept a '
      + 'signature from the old or the new secret, deploy that, change the secret '
      + 'on GitHub, then drop the old value once deliveries have settled. A '
      + 'straight swap loses whatever is in flight.';
  }
  if (state === 'inconclusive') {
    return 'record rotations somewhere the next person can read, and run this '
      + 'again with that date. The API cannot date a secret, so a written record '
      + 'is the only thing that turns this into an answer.';
  }
  if (state === 'no-secret') {
    return 'set a secret on the hook and verify X-Hub-Signature-256 in the '
      + 'receiver. Age is not the problem here.';
  }
  if (state === 'age-unknown') return 'read created_at and updated_at on the hook by hand.';
  return 'nothing.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  const org = process.env.GITHUB_ORG;
  if (!token || (!repo && !org)) {
    console.error('set GITHUB_TOKEN and at least one of GITHUB_REPO, GITHUB_ORG');
    process.exitCode = 2;
    return;
  }
  const threshold = Number(process.env.GITHUB_MAX_AGE_DAYS || DEFAULT_MAX_AGE_DAYS);
  const claimed = process.env.GITHUB_ROTATED_ON || null;
  const now = new Date();

  const scopes = [];
  if (repo) scopes.push([`/repos/${repo}/hooks?per_page=100`, repo]);
  if (org) scopes.push([`/orgs/${org}/hooks?per_page=100`, org]);

  const report = [];
  let findings = 0;
  for (const [path, label] of scopes) {
    const res = await fetch(API + path, { headers: headers(token) });
    if (res.status !== 200) {
      console.log(`GET ${path} returned ${res.status}; ${label} hooks are not readable`);
      continue;
    }
    const hooks = await res.json();
    for (const hook of Array.isArray(hooks) ? hooks : []) {
      const config = hook.config || {};
      const safe = redact(config);
      console.log(`hook ${hook.id} ${safe.url} secret=${safe.secret}`);
      const [state, detail] = verdict(config, hook.created_at, hook.updated_at,
        now, threshold, claimed);
      console.log(`${state}: ${detail}`);
      console.log(`repair: ${repair(state)}`);
      if (['overdue', 'rotation-not-applied', 'no-secret'].includes(state)) findings += 1;
      report.push({
        scope: label,
        hook_id: hook.id,
        config: safe,
        created_at: hook.created_at,
        updated_at: hook.updated_at,
        days_since_edit: ageDays(hook.updated_at, now),
        unedited_since_creation: uneditedSinceCreation(hook.created_at, hook.updated_at),
        evidence: evidenceDirection(ageDays(hook.updated_at, now), threshold),
        rotation_record: reconcile(hook.updated_at, claimed),
        state,
      });
    }
  }
  console.log(JSON.stringify({ rotation_interval_days: threshold, hooks: report }, null, 2));
  process.exitCode = findings ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are worth testing here and the rest is arithmetic. The first is that nothing resembling a secret survives a round trip through the report: a fixture is given a value where the mask normally sits, and the test asserts the value is not in the printed output. The second is the asymmetry of the evidence &mdash; an old hook is a finding, a recently edited one is explicitly not a pass &mdash; because a check that quietly grades a recent edit as compliant would be worse than not running it.",
"test_py_file": "test_github_hook_secret_age.py",
"test_py": '''import json
from datetime import datetime, timezone

from github_hook_secret_age import (
    age_days, evidence_direction, parse_time, reconcile, redact, repair,
    secret_state, unedited_since_creation, verdict,
)

NOW = datetime(2026, 8, 31, tzinfo=timezone.utc)
OLD = "2019-04-11T22:14:38Z"
RECENT = "2026-08-01T09:00:00Z"
MASKED = {"url": "https://hooks.example.com/github", "secret": "********",
          "content_type": "json"}
NO_SECRET = {"url": "https://hooks.example.com/github", "content_type": "json"}


def test_presence_is_the_only_fact_read_about_a_secret():
    assert secret_state(MASKED) == "set"
    assert secret_state(NO_SECRET) == "absent"
    assert secret_state(None) == "unknown"


def test_no_secret_value_survives_into_the_report():
    leaked = {"url": "https://hooks.example.com", "secret": "not-a-real-value"}
    printed = json.dumps(redact(leaked))
    assert "not-a-real-value" not in printed
    assert redact(leaked)["secret"] == "set"
    assert redact(MASKED)["secret"] == "set"
    assert "********" not in json.dumps(redact(MASKED))


def test_timestamps_are_parsed_and_aged_in_whole_days():
    assert parse_time(OLD).year == 2019
    assert parse_time("2019-04-11T22:14:38+00:00") == parse_time(OLD)
    assert parse_time("nonsense") is None
    assert parse_time(None) is None
    assert age_days(RECENT, NOW) == 29
    assert age_days(None, NOW) is None


def test_a_hook_never_edited_since_creation_is_recognised():
    assert unedited_since_creation(OLD, OLD)
    assert unedited_since_creation("2019-04-11T22:14:38Z", "2019-04-11T22:14:59Z")
    assert not unedited_since_creation(OLD, RECENT)
    assert not unedited_since_creation(None, RECENT)


def test_the_evidence_only_points_one_way():
    assert evidence_direction(2698, 180) == "conclusive"
    assert evidence_direction(29, 180) == "inconclusive"
    assert evidence_direction(180, 180) == "conclusive"
    assert evidence_direction(None, 180) == "unknown"


def test_an_ancient_hook_is_the_finding():
    state, detail = verdict(MASKED, OLD, OLD, NOW, 180)
    assert state == "overdue"
    assert "2698 days" in detail
    assert "the secret the hook was created with" in detail


def test_a_recent_edit_is_not_graded_as_compliant():
    state, detail = verdict(MASKED, OLD, RECENT, NOW, 180)
    assert state == "inconclusive"
    assert "an edit is not a rotation" in detail
    assert "unknown rather than compliant" in detail


def test_an_absent_secret_is_handed_to_the_other_note():
    state, detail = verdict(NO_SECRET, OLD, OLD, NOW, 180)
    assert state == "no-secret"
    assert "nothing to rotate" in detail
    assert "Age is not the problem" in repair("no-secret")


def test_a_claimed_rotation_the_hook_predates_is_a_finding():
    assert reconcile(OLD, "2026-02-14") == "not-applied"
    assert reconcile(RECENT, "2026-02-14") == "consistent"
    assert reconcile(RECENT, None) == "unknown"
    state, detail = verdict(MASKED, OLD, OLD, NOW, 180, claimed="2026-02-14")
    assert state == "rotation-not-applied"
    assert "2026-02-14" in detail
    assert "it was not this hook" in detail


def test_a_claim_the_hook_supports_does_not_override_the_age():
    state, _ = verdict(MASKED, OLD, RECENT, NOW, 180, claimed="2026-02-14")
    assert state == "inconclusive"


def test_an_unreadable_timestamp_is_admitted_rather_than_guessed():
    state, detail = verdict(MASKED, OLD, "not a date", NOW, 180)
    assert state == "age-unknown"
    assert "nothing about its age" in detail


def test_the_repair_never_suggests_a_straight_swap():
    assert "overlap window" in repair("overdue")
    assert "overlap window" in repair("rotation-not-applied")
    assert "written record" in repair("inconclusive")
''',
"test_js_file": "github-hook-secret-age.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ageDays, evidenceDirection, parseTime, reconcile, redact, repair, secretState,
  uneditedSinceCreation, verdict,
} from './github-hook-secret-age.mjs';

const NOW = new Date('2026-08-31T00:00:00Z');
const OLD = '2019-04-11T22:14:38Z';
const RECENT = '2026-08-01T09:00:00Z';
const MASKED = { url: 'https://hooks.example.com/github', secret: '********', content_type: 'json' };
const NO_SECRET = { url: 'https://hooks.example.com/github', content_type: 'json' };

test('presence is the only fact read about a secret', () => {
  assert.equal(secretState(MASKED), 'set');
  assert.equal(secretState(NO_SECRET), 'absent');
  assert.equal(secretState(null), 'unknown');
});

test('no secret value survives into the report', () => {
  const leaked = { url: 'https://hooks.example.com', secret: 'not-a-real-value' };
  const printed = JSON.stringify(redact(leaked));
  assert.ok(!printed.includes('not-a-real-value'));
  assert.equal(redact(leaked).secret, 'set');
  assert.equal(redact(MASKED).secret, 'set');
  assert.ok(!JSON.stringify(redact(MASKED)).includes('********'));
});

test('timestamps are parsed and aged in whole days', () => {
  assert.equal(parseTime(OLD).getUTCFullYear(), 2019);
  assert.equal(parseTime('2019-04-11T22:14:38+00:00').getTime(), parseTime(OLD).getTime());
  assert.equal(parseTime('nonsense'), null);
  assert.equal(parseTime(null), null);
  assert.equal(ageDays(RECENT, NOW), 29);
  assert.equal(ageDays(null, NOW), null);
});

test('a hook never edited since creation is recognised', () => {
  assert.ok(uneditedSinceCreation(OLD, OLD));
  assert.ok(uneditedSinceCreation('2019-04-11T22:14:38Z', '2019-04-11T22:14:59Z'));
  assert.ok(!uneditedSinceCreation(OLD, RECENT));
  assert.ok(!uneditedSinceCreation(null, RECENT));
});

test('the evidence only points one way', () => {
  assert.equal(evidenceDirection(2698, 180), 'conclusive');
  assert.equal(evidenceDirection(29, 180), 'inconclusive');
  assert.equal(evidenceDirection(180, 180), 'conclusive');
  assert.equal(evidenceDirection(null, 180), 'unknown');
});

test('an ancient hook is the finding', () => {
  const [state, detail] = verdict(MASKED, OLD, OLD, NOW, 180);
  assert.equal(state, 'overdue');
  assert.match(detail, /2698 days/);
  assert.match(detail, /the secret the hook was created with/);
});

test('a recent edit is not graded as compliant', () => {
  const [state, detail] = verdict(MASKED, OLD, RECENT, NOW, 180);
  assert.equal(state, 'inconclusive');
  assert.match(detail, /an edit is not a rotation/);
  assert.match(detail, /unknown rather than compliant/);
});

test('an absent secret is handed to the other note', () => {
  const [state, detail] = verdict(NO_SECRET, OLD, OLD, NOW, 180);
  assert.equal(state, 'no-secret');
  assert.match(detail, /nothing to rotate/);
  assert.match(repair('no-secret'), /Age is not the problem/);
});

test('a claimed rotation the hook predates is a finding', () => {
  assert.equal(reconcile(OLD, '2026-02-14'), 'not-applied');
  assert.equal(reconcile(RECENT, '2026-02-14'), 'consistent');
  assert.equal(reconcile(RECENT, null), 'unknown');
  const [state, detail] = verdict(MASKED, OLD, OLD, NOW, 180, '2026-02-14');
  assert.equal(state, 'rotation-not-applied');
  assert.match(detail, /2026-02-14/);
  assert.match(detail, /it was not this hook/);
});

test('a claim the hook supports does not override the age', () => {
  assert.equal(verdict(MASKED, OLD, RECENT, NOW, 180, '2026-02-14')[0], 'inconclusive');
});

test('an unreadable timestamp is admitted rather than guessed', () => {
  const [state, detail] = verdict(MASKED, OLD, 'not a date', NOW, 180);
  assert.equal(state, 'age-unknown');
  assert.match(detail, /nothing about its age/);
});

test('the repair never suggests a straight swap', () => {
  assert.match(repair('overdue'), /overlap window/);
  assert.match(repair('rotation-not-applied'), /overlap window/);
  assert.match(repair('inconclusive'), /written record/);
});
''',
"faq": [
 ("Is this the same as the note about a hook with no secret?",
  "No, it is the opposite state. That note's finding is absence: <code>config</code> has no <code>secret</code> key, no signature header is sent, and any receiver checking a signature only when one is present is checking nothing. This note starts where that one ends. The secret is set, signatures are being sent and verified, and the question is how long the same value has been doing that job. The script recognises an absent secret and hands it straight to the other note rather than reporting it as very overdue, because the repairs are not the same work."),
 ("Why can the API not tell me how old the secret is?",
  "Because it will not tell you anything about the secret except that there is one. <code>config.secret</code> comes back as a row of asterisks when set and is missing entirely when not, and no field records when it was written. That is deliberate and correct &mdash; a read-only token should not be able to exfiltrate the value that authenticates your events &mdash; but it means age has to come from a proxy. <code>updated_at</code> is the only one available, and the script says out loud that it is using one."),
 ("Our hook was updated last month. Are we compliant?",
  "Unknown, which is a different answer from yes, and the script reports it as unknown on purpose. <code>updated_at</code> moves for any change to the hook: the URL, the events array, the active flag, the content type. A rotation would move it, and so would fixing a typo in the endpoint. The timestamp is only conclusive when it is old, because then it rules a rotation out. When it is recent it rules nothing in, and a check that grades that as a pass is producing a green tick with no evidence behind it."),
 ("How do we rotate without losing events?",
  "Use an overlap window rather than a cutover. Teach the receiver to accept a signature computed with either the current or the previous secret and deploy that first. Then change the secret on GitHub. Then, once deliveries have settled and you can see the new value working, remove the old one from the receiver. A straight swap drops everything in flight during the gap and generates a burst of signature failures that reads exactly like someone attacking your endpoint, which is a bad thing to schedule for a Friday."),
 ("How old is too old?",
  "GitHub publishes no guidance, so this is a policy number you choose rather than a fact you look up: ninety days, a hundred and eighty, a year. The number matters far less than having one, because the failure mode here is not a secret that is slightly too old, it is a secret that has never been changed since 2019 and is on a laptop somebody sold. If the value has actually leaked, rotation is only the first step: it closes future access and does nothing about events already captured, so look at what else lived in that environment."),
],
"related": [
 ("/github/webhook-no-secret/", "A webhook with no secret sends no signature"),
 ("/github/webhook-insecure-ssl/", "Certificate verification switched off on the hook"),
 ("/github/token-expiring-soon/", "A token that expires in a few days"),
],
"citations": [CITE_VALIDATING, CITE_REPO_HOOKS, CITE_WEBHOOK_BEST, CITE_CREATING_WEBHOOKS],
},


{
"slug": "app-webhook-url-unset",
"title": "The GitHub App has no webhook URL configured",
"description": "An App's webhook lives on the App, not the installation. GET /app/hook/config reads it, and a blank or smee.io URL means no event has ever arrived.",
"h1": "the GitHub App has no webhook URL configured",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app webhook url not set",
             "github app hook config api",
             "github app not receiving webhooks",
             "github app smee.io left in production",
             "github app hook deliveries empty"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The App is installed on forty repositories, the permissions were approved, the event subscriptions are exactly right, and it has never once reacted to anything. There is nothing in the delivery log to read, no failures to group, no status codes to explain. Nothing is failing, because nothing is being attempted.",
"short_answer": """<p>A GitHub App's webhook is configured on the <em>App</em>, not on each installation, and it is a separate thing from the App's event subscriptions. You can subscribe an App to a dozen events and leave the destination blank, and GitHub will not complain: there is simply nowhere to deliver to.</p>
<p>Authenticate as the App with a JWT and read <code>GET /app/hook/config</code>, which returns <code>url</code>, <code>content_type</code>, <code>insecure_ssl</code> and a masked <code>secret</code>. An empty <code>url</code> is the finding outright. A <code>url</code> that still points at <code>smee.io</code>, <code>localhost</code> or <code>example.com</code> is the same finding wearing a disguise, and it is the more common one, because those are what the tutorials put there. Corroborate with <code>GET /app/hook/deliveries</code>: an empty list where the App subscribes to busy events says the destination has never worked. Pair it with <code>GET /app</code>, which lists the events the App is subscribed to, because an App subscribed to nothing has a different problem.</p>""",
"problem": """<p>Every webhook diagnostic anybody knows starts with the delivery log, and this one has nothing in it. That is not a subtle signal; it is the absence of a signal, and absence gets read as "we must be looking in the wrong place". So the search moves outward. People check the installation, the permissions, the event subscriptions, whether the App is suspended, whether the customer really did install it on that repository. All of those are readable, all of them come back correct, and none of them is the destination.</p>
<p>The reason the destination gets skipped is that it lives somewhere nobody is looking. Repository webhooks are configured on the repository, and that is where a decade of habit says to look. An App's webhook is configured once, on the App itself, in a settings page most of the team has never opened and which is not visible from any installation. Reading it through the API needs a JWT signed with the App's private key, which is a different credential from the installation token everything else uses, so the check is not one that falls out of normal work.</p>
<p>The version that costs the most is not a blank field. It is <code>https://smee.io/</code> followed by a random string, put there by the quickstart during the first hour of development, working perfectly on a laptop, and never changed because it never broke. The App ships. Events flow to a proxy that nobody is listening to. It looks configured, it passes a glance, and it is exactly as broken as a blank field while being much harder to see.</p>""",
"why": """<p><strong>The webhook is App-level, and so is the blast radius.</strong> One <code>url</code>, one secret, one content type, shared by every installation of the App. That is convenient &mdash; you fix it once for every customer &mdash; and it is why the failure is total rather than partial. There is no installation you can compare against a working one, because they all point at the same nothing.</p>
<p><strong>Subscriptions and destination are independent.</strong> <code>GET /app</code> lists the events the App is subscribed to. <code>GET /app/hook/config</code> holds where they go. Neither validates the other, so an App can be subscribed to <code>pull_request</code>, <code>push</code> and <code>issues</code> with nowhere to send them, and nothing in the interface objects. If the events array is empty as well, that is <a href="/github/app-not-subscribed-to-event/">a different note</a>, and this script says which of the two you are looking at instead of merging them.</p>
<p><strong>A placeholder is a finding, not a URL.</strong> <code>smee.io</code>, <code>localhost</code>, <code>ngrok</code> and <code>example.com</code> are the four ways this actually happens, and they all pass any check that only asks whether the field is empty. The script classifies the host rather than testing for blankness, because "there is a URL there" is the sentence that ends most investigations of this prematurely.</p>
<p><strong>An empty delivery list corroborates and does not prove.</strong> Deliveries are retained for a limited window, so an empty list can also mean a quiet App or a long weekend. It is evidence when read next to the subscriptions: no deliveries and a subscription to <code>push</code> on forty active repositories is conclusive; no deliveries on an App subscribed to <code>member</code> is a Tuesday. The script reports the two together and never treats emptiness alone as the finding.</p>
<p><strong>The JWT is the price of admission, and the script does not mint it.</strong> Reading an App's own configuration requires authenticating as the App, which an installation token cannot do. The script takes a JWT from the environment rather than loading a private key and signing one, so the key never enters this process. That is a smaller program and a much smaller thing to have in your history.</p>""",
"steps": [
 {"h": "Authenticate as the App, not as an installation",
  "body": """<p>Everything here needs a JWT signed with the App's private key. An installation access token &mdash; the one the rest of your code uses &mdash; gets a 403 on these endpoints, and that 403 is not a permissions problem to chase. Mint the JWT wherever you already mint them and hand it to the script through the environment.</p>"""},
 {"h": "Read the destination",
  "body": """<p><code>GET /app/hook/config</code> returns <code>url</code>, <code>content_type</code>, <code>insecure_ssl</code> and <code>secret</code>, with the secret masked when set. An empty <code>url</code> is the finding immediately. Anything else needs the host looked at rather than the field checked for emptiness.</p>"""},
 {"h": "Classify the host instead of testing for blank",
  "body": """<p><code>smee.io</code> and <code>ngrok</code> are development proxies; <code>localhost</code> and <code>127.0.0.1</code> are unreachable from GitHub entirely; <code>example.com</code> is a placeholder from a template. Each of them is as broken as an empty field and none of them looks it. A plain <code>http://</code> host is a separate and worse problem covered in <a href="/github/webhook-http-url/">its own note</a>, and the script names it rather than absorbing it.</p>"""},
 {"h": "Read the subscriptions and the deliveries together",
  "body": """<p><code>GET /app</code> gives the events the App is subscribed to and how many installations it has. <code>GET /app/hook/deliveries</code> gives what has actually arrived. Empty deliveries plus busy subscriptions plus installations is conclusive. Empty deliveries plus an empty events array is a different finding entirely, and one this script hands off rather than reporting as a broken URL.</p>"""},
 {"h": "Set the destination, then prove it with the delivery log",
  "body": """<p>Point the App's webhook at the production receiver, set a secret, set <code>content_type</code> to <code>json</code>, and then come back to <code>GET /app/hook/deliveries</code> and watch events appear. That last read is the only confirmation that means anything: the settings page will happily show you a URL that nothing can reach.</p>"""},
],
"verify": """<p>One JWT and three GETs. Nothing is created and nothing is redelivered.</p>
<pre><code class="language-bash">GITHUB_APP_JWT=$APP_JWT python3 github_app_hook_config.py
# app: acme-deploy-bot, 41 installation(s), subscribed to 4 event(s)
# hook config: url=https://smee.io/aB3xQ9pLm content_type=form secret=set
# tunnel-url: the App delivers to smee.io, which is a development proxy from
# the quickstart. Every event goes to a channel nobody is listening to.
# deliveries: 128 in the retained window, most recent 2026-08-30
# repair: point the App's webhook at the production receiver, keep the secret,
# and set content_type to json.

# and the blank case, which is quieter
# no-url-subscribed: the App subscribes to 4 events and has no webhook URL, so
# nothing is delivered and nothing fails. There is no log to read.</code></pre>""",
"code_intro": "The interesting function is the one that classifies a host, because everything this note is about is the difference between a field that is empty and a field that is full of something useless. It sorts unset, malformed, placeholder, tunnel, loopback and plain-http before it will call anything a production destination, and the ordering matters: <code>http://localhost:3000</code> is a loopback problem rather than a transport one, and saying so sends the reader to the right repair. The delivery evidence is deliberately weak on its own and only firms up next to the subscription list.",
"py_file": "github_app_hook_config.py",
"py": '''"""Say whether a GitHub App has a webhook destination that can work.

Read only. Three GETs against the App itself: its own record, its webhook
configuration, and a page of its deliveries. Nothing is created or changed.

A GitHub App's webhook lives on the App rather than on each installation, and it
is independent of the App's event subscriptions. It can be blank, or left
pointing at the smee.io proxy the quickstart hands out, and nothing complains:
there are no failed deliveries where there are no deliveries at all.

Authentication is a JWT signed with the App's private key. This script takes the
JWT from the environment and never loads or signs with the key, so the key never
enters this process.

Environment:

    GITHUB_APP_JWT   a JWT signed with the App's private key
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_app_hook_config")

API = "https://api.github.com"
UA = "github-app-hook-config/1.0"

# The four ways this actually happens. All of them pass a check that only asks
# whether the field is empty, which is why the host is classified instead.
PLACEHOLDER_HOSTS = ("example.com", "example.org", "example.net",
                     "your-domain.com", "yourdomain.com", "changeme", "todo")
TUNNEL_HOSTS = ("smee.io", "ngrok.io", "ngrok-free.app", "ngrok.app",
                "loca.lt", "trycloudflare.com", "serveo.net")
LOOPBACK_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "::1")
# Past this, a destination that has delivered before has gone quiet.
DEFAULT_STALE_DAYS = 30


def host_of(url):
    """The lowercase hostname of a URL, or an empty string. Pure."""
    try:
        parts = urlsplit(str(url or "").strip())
    except ValueError:
        return ""
    return (parts.hostname or "").lower()


def host_matches(host, suffixes):
    """Whether a host is one of these names or a subdomain of one. Pure."""
    for suffix in suffixes:
        if host == suffix or host.endswith("." + suffix):
            return True
    return False


def url_class(url):
    """Sort a webhook destination into what it can actually reach. Pure.

    Ordered so the most specific reason wins: http://localhost is a loopback
    problem, not a transport one, and sending the reader to the transport note
    would waste their afternoon.
    """
    raw = str(url or "").strip()
    if not raw:
        return "unset"
    parts = urlsplit(raw)
    host = host_of(raw)
    if parts.scheme not in ("http", "https") or not host:
        return "malformed"
    if host_matches(host, PLACEHOLDER_HOSTS) or host.startswith("example."):
        return "placeholder"
    if host_matches(host, TUNNEL_HOSTS):
        return "tunnel"
    if host in LOOPBACK_HOSTS or host.endswith(".local"):
        return "loopback"
    if parts.scheme == "http":
        return "insecure"
    return "production"


def secret_state(config):
    """Whether a secret is set. Never returns the value. Pure."""
    if not isinstance(config, dict):
        return "unknown"
    return "set" if config.get("secret") is not None else "absent"


def content_type_of(config):
    """The App hook's body encoding, with the documented default applied. Pure."""
    if not isinstance(config, dict):
        return "unknown"
    raw = config.get("content_type")
    if raw is None:
        return "form"
    value = str(raw).strip().lower()
    return value if value in ("json", "form") else "unknown"


def subscribed_events(app):
    """The events the App is subscribed to. Pure."""
    events = (app or {}).get("events") if isinstance(app, dict) else None
    return [str(e) for e in events] if isinstance(events, list) else []


def parse_time(text):
    """An ISO 8601 timestamp as an aware datetime, or None. Pure."""
    raw = str(text or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def last_delivery(deliveries):
    """The most recent delivered_at in a delivery list, or None. Pure."""
    stamps = []
    for record in deliveries or []:
        if not isinstance(record, dict):
            continue
        moment = parse_time(record.get("delivered_at"))
        if moment is not None:
            stamps.append(moment)
    return max(stamps) if stamps else None


def delivery_state(deliveries, now, stale_days=DEFAULT_STALE_DAYS):
    """Whether anything has arrived recently. Corroboration, never proof. Pure.

    Deliveries are retained for a limited window, so an empty list can also mean
    a quiet App. This is only worth reading next to the subscription list.
    """
    if deliveries is None:
        return "unknown"
    if not deliveries:
        return "none"
    latest = last_delivery(deliveries)
    if latest is None or now is None:
        return "unknown"
    days = int((now - latest).total_seconds() // 86400)
    return "stale" if days >= int(stale_days) else "recent"


def verdict(url, events, deliveries_state, installations=None):
    """Turn the destination, the subscriptions and the log into a finding. Pure."""
    klass = url_class(url)
    count = len(events or [])
    if klass == "unset":
        if count:
            return ("no-url-subscribed",
                    "the App subscribes to %d event(s) and has no webhook URL, "
                    "so nothing is delivered and nothing fails. There is no log "
                    "to read because there are no deliveries." % count)
        return ("no-url",
                "the App has no webhook URL and subscribes to no events. That "
                "is a coherent configuration for an App that only polls or "
                "creates its own repository hooks, so this is reported rather "
                "than judged.")
    if klass == "malformed":
        return ("malformed-url",
                "the webhook URL is not a usable http or https URL, so no "
                "delivery can be attempted against it.")
    if klass == "placeholder":
        return ("placeholder-url",
                "the webhook URL points at a placeholder host from a template. "
                "It looks configured and it reaches nothing you own.")
    if klass == "tunnel":
        return ("tunnel-url",
                "the App delivers to a development proxy from the quickstart. "
                "Every event goes to a channel nobody is listening to, and the "
                "field looks filled in to anyone glancing at it.")
    if klass == "loopback":
        return ("loopback-url",
                "the webhook URL is a loopback or link-local address, which "
                "GitHub cannot reach from the internet at all.")
    if klass == "insecure":
        return ("insecure-url",
                "the App delivers over plain http, so payloads and signatures "
                "cross the network in the clear. Deliveries do arrive, which is "
                "why this survives so long.")
    if deliveries_state == "none" and count:
        return ("no-deliveries",
                "the URL looks like a real destination and the App subscribes "
                "to %d event(s), but nothing has been delivered in the retained "
                "window. Either the events have genuinely not happened or the "
                "destination has never worked." % count)
    if deliveries_state == "stale" and count:
        return ("silent",
                "the destination has delivered before and has gone quiet. That "
                "is a receiver or subscription question rather than a "
                "configuration one.")
    if not count:
        return ("no-events",
                "the webhook URL is a real destination but the App subscribes "
                "to no events, so nothing will ever be sent to it. That is a "
                "subscription finding, not a URL one.")
    return ("delivering",
            "the App has a real destination, subscribes to %d event(s), and "
            "events are arriving." % count)


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state in ("no-url-subscribed", "placeholder-url", "tunnel-url",
                 "loopback-url", "malformed-url"):
        return ("point the App's webhook at the production receiver, set a "
                "secret, set content_type to json, and then confirm with GET "
                "/app/hook/deliveries that events start arriving. The settings "
                "page will show a URL that nothing can reach.")
    if state == "insecure-url":
        return ("move the destination to https before anything else. The "
                "payload and its signature are readable in transit today.")
    if state == "no-deliveries":
        return ("check the receiver is reachable from the internet, then wait "
                "for an event you can cause on purpose and read the delivery "
                "log again. An empty log alone is not proof of anything.")
    if state == "no-events":
        return ("subscribe the App to the events it handles. The destination is "
                "fine and there is nothing being sent to it.")
    if state == "no-url":
        return ("nothing, if the App is meant to poll or manage its own "
                "repository hooks. If it is meant to react to events, this is "
                "the whole problem.")
    if state == "silent":
        return ("look at the receiver and the subscription list rather than the "
                "URL, which is working.")
    return "nothing."


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    r = session.get(API + path, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS,
                    help="days without a delivery before a destination is quiet")
    args = ap.parse_args()

    jwt = os.environ.get("GITHUB_APP_JWT")
    if not jwt:
        log.error("set GITHUB_APP_JWT to a JWT signed with the App's private "
                  "key. An installation token cannot read the App's own "
                  "configuration and will answer 403 here")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + jwt,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    status, app = get(session, "/app")
    if status != 200 or not isinstance(app, dict):
        log.error("GET /app returned %d; the JWT is not being accepted as an App", status)
        return 2
    events = subscribed_events(app)
    log.info("app: %s, %s installation(s), subscribed to %d event(s)",
             app.get("slug"), app.get("installations_count"), len(events))

    status, config = get(session, "/app/hook/config")
    if status != 200 or not isinstance(config, dict):
        log.error("GET /app/hook/config returned %d", status)
        return 2
    url = config.get("url")
    log.info("hook config: url=%s content_type=%s secret=%s",
             url or "(empty)", content_type_of(config), secret_state(config))

    status, deliveries = get(session, "/app/hook/deliveries?per_page=100")
    records = deliveries if status == 200 and isinstance(deliveries, list) else None
    now = datetime.now(timezone.utc)
    state_of_log = delivery_state(records, now, args.stale_days)
    latest = last_delivery(records or [])
    log.info("deliveries: %s in the retained window, most recent %s",
             len(records) if records is not None else "unreadable",
             str(latest)[:10] if latest else "none")

    state, detail = verdict(url, events, state_of_log, app.get("installations_count"))
    log.info("%s: %s", state, detail)
    log.info("repair: %s", repair(state))

    print(json.dumps({
        "app": app.get("slug"),
        "installations": app.get("installations_count"),
        "events": events,
        "hook_url": url,
        "url_class": url_class(url),
        "content_type": content_type_of(config),
        "secret": secret_state(config),
        "deliveries_retained": len(records) if records is not None else None,
        "last_delivery": str(latest) if latest else None,
        "delivery_state": state_of_log,
        "state": state,
        "detail": detail,
        "repair": repair(state),
    }, indent=2, default=str))
    return 1 if state in ("no-url-subscribed", "placeholder-url", "tunnel-url",
                          "loopback-url", "malformed-url", "insecure-url") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-app-hook-config.mjs",
"js": '''/**
 * Say whether a GitHub App has a webhook destination that can work.
 *
 * Read only. Three GETs against the App itself: its own record, its webhook
 * configuration, and a page of its deliveries. Nothing is created or changed.
 *
 * Authentication is a JWT signed with the App's private key, taken from the
 * environment. The key never enters this process.
 *
 * Environment:
 *   GITHUB_APP_JWT   a JWT signed with the App's private key
 */
const API = 'https://api.github.com';
const UA = 'github-app-hook-config/1.0';

/** The four ways this actually happens, none of which is an empty field. */
export const PLACEHOLDER_HOSTS = ['example.com', 'example.org', 'example.net',
  'your-domain.com', 'yourdomain.com', 'changeme', 'todo'];
export const TUNNEL_HOSTS = ['smee.io', 'ngrok.io', 'ngrok-free.app', 'ngrok.app',
  'loca.lt', 'trycloudflare.com', 'serveo.net'];
export const LOOPBACK_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '::1'];
export const DEFAULT_STALE_DAYS = 30;

/** The lowercase hostname of a URL, or an empty string. Pure. */
export function hostOf(url) {
  try {
    return new URL(String(url ?? '').trim()).hostname.toLowerCase().replace('[', '').replace(']', '');
  } catch {
    return '';
  }
}

/** Whether a host is one of these names or a subdomain of one. Pure. */
export function hostMatches(host, suffixes) {
  return (suffixes || []).some((suffix) => host === suffix || host.endsWith(`.${suffix}`));
}

/** Sort a webhook destination into what it can actually reach. Pure. */
export function urlClass(url) {
  const raw = String(url ?? '').trim();
  if (!raw) return 'unset';
  let parsed = null;
  try { parsed = new URL(raw); } catch { return 'malformed'; }
  const host = hostOf(raw);
  if (!['http:', 'https:'].includes(parsed.protocol) || !host) return 'malformed';
  if (hostMatches(host, PLACEHOLDER_HOSTS) || host.startsWith('example.')) return 'placeholder';
  if (hostMatches(host, TUNNEL_HOSTS)) return 'tunnel';
  if (LOOPBACK_HOSTS.includes(host) || host.endsWith('.local')) return 'loopback';
  if (parsed.protocol === 'http:') return 'insecure';
  return 'production';
}

/** Whether a secret is set. Never returns the value. Pure. */
export function secretState(config) {
  if (!config || typeof config !== 'object') return 'unknown';
  return config.secret !== null && config.secret !== undefined ? 'set' : 'absent';
}

/** The App hook's body encoding, with the documented default applied. Pure. */
export function contentTypeOf(config) {
  if (!config || typeof config !== 'object') return 'unknown';
  const raw = config.content_type;
  if (raw === null || raw === undefined) return 'form';
  const value = String(raw).trim().toLowerCase();
  return ['json', 'form'].includes(value) ? value : 'unknown';
}

/** The events the App is subscribed to. Pure. */
export function subscribedEvents(app) {
  const events = (app || {}).events;
  return Array.isArray(events) ? events.map((e) => String(e)) : [];
}

/** An ISO 8601 timestamp as a Date, or null. Pure. */
export function parseTime(text) {
  const raw = String(text ?? '').trim();
  if (!raw) return null;
  const moment = new Date(raw);
  return Number.isNaN(moment.getTime()) ? null : moment;
}

/** The most recent delivered_at in a delivery list, or null. Pure. */
export function lastDelivery(deliveries) {
  let latest = null;
  for (const record of deliveries || []) {
    if (!record || typeof record !== 'object') continue;
    const moment = parseTime(record.delivered_at);
    if (moment && (latest === null || moment > latest)) latest = moment;
  }
  return latest;
}

/** Whether anything has arrived recently. Corroboration, never proof. Pure. */
export function deliveryState(deliveries, now, staleDays = DEFAULT_STALE_DAYS) {
  if (deliveries === null || deliveries === undefined) return 'unknown';
  if (deliveries.length === 0) return 'none';
  const latest = lastDelivery(deliveries);
  if (latest === null || !now) return 'unknown';
  const days = Math.floor((now.getTime() - latest.getTime()) / 86400000);
  return days >= Number(staleDays) ? 'stale' : 'recent';
}

/** Turn the destination, the subscriptions and the log into a finding. Pure. */
export function verdict(url, events, deliveriesState) {
  const klass = urlClass(url);
  const count = (events || []).length;
  if (klass === 'unset') {
    if (count) {
      return ['no-url-subscribed',
        `the App subscribes to ${count} event(s) and has no webhook URL, so `
        + 'nothing is delivered and nothing fails. There is no log to read '
        + 'because there are no deliveries.'];
    }
    return ['no-url',
      'the App has no webhook URL and subscribes to no events. That is a '
      + 'coherent configuration for an App that only polls or creates its own '
      + 'repository hooks, so this is reported rather than judged.'];
  }
  if (klass === 'malformed') {
    return ['malformed-url',
      'the webhook URL is not a usable http or https URL, so no delivery can be '
      + 'attempted against it.'];
  }
  if (klass === 'placeholder') {
    return ['placeholder-url',
      'the webhook URL points at a placeholder host from a template. It looks '
      + 'configured and it reaches nothing you own.'];
  }
  if (klass === 'tunnel') {
    return ['tunnel-url',
      'the App delivers to a development proxy from the quickstart. Every event '
      + 'goes to a channel nobody is listening to, and the field looks filled in '
      + 'to anyone glancing at it.'];
  }
  if (klass === 'loopback') {
    return ['loopback-url',
      'the webhook URL is a loopback or link-local address, which GitHub cannot '
      + 'reach from the internet at all.'];
  }
  if (klass === 'insecure') {
    return ['insecure-url',
      'the App delivers over plain http, so payloads and signatures cross the '
      + 'network in the clear. Deliveries do arrive, which is why this survives so long.'];
  }
  if (deliveriesState === 'none' && count) {
    return ['no-deliveries',
      `the URL looks like a real destination and the App subscribes to ${count} `
      + 'event(s), but nothing has been delivered in the retained window. Either '
      + 'the events have genuinely not happened or the destination has never worked.'];
  }
  if (deliveriesState === 'stale' && count) {
    return ['silent',
      'the destination has delivered before and has gone quiet. That is a '
      + 'receiver or subscription question rather than a configuration one.'];
  }
  if (!count) {
    return ['no-events',
      'the webhook URL is a real destination but the App subscribes to no '
      + 'events, so nothing will ever be sent to it. That is a subscription '
      + 'finding, not a URL one.'];
  }
  return ['delivering',
    `the App has a real destination, subscribes to ${count} event(s), and events are arriving.`];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (['no-url-subscribed', 'placeholder-url', 'tunnel-url', 'loopback-url',
    'malformed-url'].includes(state)) {
    return "point the App's webhook at the production receiver, set a secret, "
      + 'set content_type to json, and then confirm with GET /app/hook/deliveries '
      + 'that events start arriving. The settings page will show a URL that '
      + 'nothing can reach.';
  }
  if (state === 'insecure-url') {
    return 'move the destination to https before anything else. The payload and '
      + 'its signature are readable in transit today.';
  }
  if (state === 'no-deliveries') {
    return 'check the receiver is reachable from the internet, then wait for an '
      + 'event you can cause on purpose and read the delivery log again. An empty '
      + 'log alone is not proof of anything.';
  }
  if (state === 'no-events') {
    return 'subscribe the App to the events it handles. The destination is fine '
      + 'and there is nothing being sent to it.';
  }
  if (state === 'no-url') {
    return 'nothing, if the App is meant to poll or manage its own repository '
      + 'hooks. If it is meant to react to events, this is the whole problem.';
  }
  if (state === 'silent') {
    return 'look at the receiver and the subscription list rather than the URL, '
      + 'which is working.';
  }
  return 'nothing.';
}

function headers(jwt) {
  return {
    Authorization: `Bearer ${jwt}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(jwt, path) {
  const res = await fetch(API + path, { headers: headers(jwt) });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const jwt = process.env.GITHUB_APP_JWT;
  if (!jwt) {
    console.error("set GITHUB_APP_JWT to a JWT signed with the App's private key");
    process.exitCode = 2;
    return;
  }
  const staleDays = Number(process.env.GITHUB_STALE_DAYS || DEFAULT_STALE_DAYS);

  const app = await get(jwt, '/app');
  if (app.status !== 200 || !app.body) {
    console.error(`GET /app returned ${app.status}; the JWT is not being accepted as an App`);
    process.exitCode = 2;
    return;
  }
  const events = subscribedEvents(app.body);
  console.log(`app: ${app.body.slug}, ${app.body.installations_count} installation(s), `
    + `subscribed to ${events.length} event(s)`);

  const cfg = await get(jwt, '/app/hook/config');
  if (cfg.status !== 200 || !cfg.body) {
    console.error(`GET /app/hook/config returned ${cfg.status}`);
    process.exitCode = 2;
    return;
  }
  const url = cfg.body.url;
  console.log(`hook config: url=${url || '(empty)'} content_type=${contentTypeOf(cfg.body)} `
    + `secret=${secretState(cfg.body)}`);

  const dl = await get(jwt, '/app/hook/deliveries?per_page=100');
  const records = dl.status === 200 && Array.isArray(dl.body) ? dl.body : null;
  const now = new Date();
  const stateOfLog = deliveryState(records, now, staleDays);
  const latest = lastDelivery(records || []);
  console.log(`deliveries: ${records === null ? 'unreadable' : records.length} in the `
    + `retained window, most recent ${latest ? latest.toISOString().slice(0, 10) : 'none'}`);

  const [state, detail] = verdict(url, events, stateOfLog);
  console.log(`${state}: ${detail}`);
  console.log(`repair: ${repair(state)}`);
  console.log(JSON.stringify({
    app: app.body.slug,
    installations: app.body.installations_count,
    events,
    hook_url: url,
    url_class: urlClass(url),
    content_type: contentTypeOf(cfg.body),
    secret: secretState(cfg.body),
    deliveries_retained: records === null ? null : records.length,
    delivery_state: stateOfLog,
    state,
  }, null, 2));
  process.exitCode = ['no-url-subscribed', 'placeholder-url', 'tunnel-url',
    'loopback-url', 'malformed-url', 'insecure-url'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The host classifier gets a case each for the four ways this happens in the wild, plus the ordering rule that keeps <code>http://localhost:3000</code> a loopback finding rather than a transport one. After that, the pairs that decide the verdict: a blank URL means something different when the App subscribes to a dozen events than when it subscribes to none, and an empty delivery list is corroboration on its own and a conclusion only when there is something that should have arrived.",
"test_py_file": "test_github_app_hook_config.py",
"test_py": '''from datetime import datetime, timezone

from github_app_hook_config import (
    content_type_of, delivery_state, host_of, last_delivery, repair,
    secret_state, subscribed_events, url_class, verdict,
)

NOW = datetime(2026, 8, 31, tzinfo=timezone.utc)
EVENTS = ["push", "pull_request", "issues", "release"]
RECENT = [{"delivered_at": "2026-08-30T10:00:00Z"}, {"delivered_at": "2026-08-29T10:00:00Z"}]
OLD = [{"delivered_at": "2026-01-04T10:00:00Z"}]


def test_a_host_is_pulled_out_of_a_url_or_admitted_missing():
    assert host_of("https://Hooks.Example.COM/github") == "hooks.example.com"
    assert host_of("nonsense") == ""
    assert host_of(None) == ""


def test_the_four_ways_this_actually_happens_are_each_named():
    assert url_class("") == "unset"
    assert url_class(None) == "unset"
    assert url_class("https://smee.io/aB3xQ9pLm") == "tunnel"
    assert url_class("https://1a2b3c.ngrok-free.app/hook") == "tunnel"
    assert url_class("https://example.com/webhook") == "placeholder"
    assert url_class("https://localhost:3000/hook") == "loopback"


def test_a_real_destination_is_not_swept_up_by_the_placeholder_list():
    assert url_class("https://hooks.acme.dev/github") == "production"
    assert url_class("https://api.example-corp.com/github") == "production"


def test_loopback_beats_transport_so_the_reader_goes_to_the_right_note():
    assert url_class("http://localhost:3000/hook") == "loopback"
    assert url_class("http://hooks.acme.dev/github") == "insecure"
    assert url_class("ftp://hooks.acme.dev/github") == "malformed"
    assert url_class("just-a-string") == "malformed"


def test_the_config_is_read_without_touching_the_secret():
    assert secret_state({"secret": "********"}) == "set"
    assert secret_state({"url": "https://x.dev"}) == "absent"
    assert content_type_of({}) == "form"
    assert content_type_of({"content_type": "JSON"}) == "json"
    assert subscribed_events({"events": EVENTS}) == EVENTS
    assert subscribed_events({}) == []


def test_a_blank_url_with_subscriptions_is_the_sharpest_form():
    state, detail = verdict("", EVENTS, "none")
    assert state == "no-url-subscribed"
    assert "4 event(s)" in detail
    assert "no log to read" in detail


def test_a_blank_url_with_no_subscriptions_is_reported_not_judged():
    state, detail = verdict("", [], "none")
    assert state == "no-url"
    assert "reported rather than judged" in detail


def test_a_tunnel_url_is_as_broken_as_a_blank_one_and_harder_to_see():
    state, detail = verdict("https://smee.io/aB3xQ9pLm", EVENTS, "recent")
    assert state == "tunnel-url"
    assert "nobody is listening" in detail


def test_the_delivery_log_is_read_and_never_trusted_alone():
    assert delivery_state([], NOW) == "none"
    assert delivery_state(RECENT, NOW) == "recent"
    assert delivery_state(OLD, NOW) == "stale"
    assert delivery_state(None, NOW) == "unknown"
    assert last_delivery(RECENT).day == 30
    assert last_delivery([]) is None


def test_an_empty_log_on_a_real_url_is_a_question_and_not_a_verdict():
    state, detail = verdict("https://hooks.acme.dev/github", EVENTS, "none")
    assert state == "no-deliveries"
    assert "genuinely not happened" in detail
    assert "not proof of anything" in repair("no-deliveries")


def test_a_real_url_with_no_subscriptions_is_handed_to_the_other_note():
    state, detail = verdict("https://hooks.acme.dev/github", [], "none")
    assert state == "no-events"
    assert "subscription finding" in detail


def test_a_working_app_is_not_a_finding():
    assert verdict("https://hooks.acme.dev/github", EVENTS, "recent")[0] == "delivering"
    assert verdict("https://hooks.acme.dev/github", EVENTS, "stale")[0] == "silent"


def test_the_repair_ends_at_the_delivery_log_rather_than_the_settings_page():
    assert "app/hook/deliveries" in repair("tunnel-url")
    assert "settings page" in repair("no-url-subscribed")
    assert "https" in repair("insecure-url")
''',
"test_js_file": "github-app-hook-config.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  contentTypeOf, deliveryState, hostOf, lastDelivery, repair, secretState,
  subscribedEvents, urlClass, verdict,
} from './github-app-hook-config.mjs';

const NOW = new Date('2026-08-31T00:00:00Z');
const EVENTS = ['push', 'pull_request', 'issues', 'release'];
const RECENT = [{ delivered_at: '2026-08-30T10:00:00Z' }, { delivered_at: '2026-08-29T10:00:00Z' }];
const OLD = [{ delivered_at: '2026-01-04T10:00:00Z' }];

test('a host is pulled out of a URL or admitted missing', () => {
  assert.equal(hostOf('https://Hooks.Example.COM/github'), 'hooks.example.com');
  assert.equal(hostOf('nonsense'), '');
  assert.equal(hostOf(null), '');
});

test('the four ways this actually happens are each named', () => {
  assert.equal(urlClass(''), 'unset');
  assert.equal(urlClass(null), 'unset');
  assert.equal(urlClass('https://smee.io/aB3xQ9pLm'), 'tunnel');
  assert.equal(urlClass('https://1a2b3c.ngrok-free.app/hook'), 'tunnel');
  assert.equal(urlClass('https://example.com/webhook'), 'placeholder');
  assert.equal(urlClass('https://localhost:3000/hook'), 'loopback');
});

test('a real destination is not swept up by the placeholder list', () => {
  assert.equal(urlClass('https://hooks.acme.dev/github'), 'production');
  assert.equal(urlClass('https://api.example-corp.com/github'), 'production');
});

test('loopback beats transport so the reader goes to the right note', () => {
  assert.equal(urlClass('http://localhost:3000/hook'), 'loopback');
  assert.equal(urlClass('http://hooks.acme.dev/github'), 'insecure');
  assert.equal(urlClass('ftp://hooks.acme.dev/github'), 'malformed');
  assert.equal(urlClass('just-a-string'), 'malformed');
});

test('the config is read without touching the secret', () => {
  assert.equal(secretState({ secret: '********' }), 'set');
  assert.equal(secretState({ url: 'https://x.dev' }), 'absent');
  assert.equal(contentTypeOf({}), 'form');
  assert.equal(contentTypeOf({ content_type: 'JSON' }), 'json');
  assert.deepEqual(subscribedEvents({ events: EVENTS }), EVENTS);
  assert.deepEqual(subscribedEvents({}), []);
});

test('a blank URL with subscriptions is the sharpest form', () => {
  const [state, detail] = verdict('', EVENTS, 'none');
  assert.equal(state, 'no-url-subscribed');
  assert.ok(detail.includes('4 event(s)'));
  assert.match(detail, /no log to read/);
});

test('a blank URL with no subscriptions is reported, not judged', () => {
  const [state, detail] = verdict('', [], 'none');
  assert.equal(state, 'no-url');
  assert.match(detail, /reported rather than judged/);
});

test('a tunnel URL is as broken as a blank one and harder to see', () => {
  const [state, detail] = verdict('https://smee.io/aB3xQ9pLm', EVENTS, 'recent');
  assert.equal(state, 'tunnel-url');
  assert.match(detail, /nobody is listening/);
});

test('the delivery log is read and never trusted alone', () => {
  assert.equal(deliveryState([], NOW), 'none');
  assert.equal(deliveryState(RECENT, NOW), 'recent');
  assert.equal(deliveryState(OLD, NOW), 'stale');
  assert.equal(deliveryState(null, NOW), 'unknown');
  assert.equal(lastDelivery(RECENT).getUTCDate(), 30);
  assert.equal(lastDelivery([]), null);
});

test('an empty log on a real URL is a question and not a verdict', () => {
  const [state, detail] = verdict('https://hooks.acme.dev/github', EVENTS, 'none');
  assert.equal(state, 'no-deliveries');
  assert.match(detail, /genuinely not happened/);
  assert.match(repair('no-deliveries'), /not proof of anything/);
});

test('a real URL with no subscriptions is handed to the other note', () => {
  const [state, detail] = verdict('https://hooks.acme.dev/github', [], 'none');
  assert.equal(state, 'no-events');
  assert.match(detail, /subscription finding/);
});

test('a working App is not a finding', () => {
  assert.equal(verdict('https://hooks.acme.dev/github', EVENTS, 'recent')[0], 'delivering');
  assert.equal(verdict('https://hooks.acme.dev/github', EVENTS, 'stale')[0], 'silent');
});

test('the repair ends at the delivery log rather than the settings page', () => {
  assert.ok(repair('tunnel-url').includes('app/hook/deliveries'));
  assert.match(repair('no-url-subscribed'), /settings page/);
  assert.match(repair('insecure-url'), /https/);
});
''',
"faq": [
 ("Why is there nothing in the delivery log?",
  "Because there is nothing to log. A failed delivery is a record of an attempt; with no destination there is no attempt, so the log is not empty because something went wrong, it is empty because nothing happened. That is why this problem defeats the usual webhook playbook, which starts by reading the failures. The absence of failures is being read as a good sign, when here it is the finding itself."),
 ("Do I need the App's private key to run this?",
  "You need a JWT signed with it, which is not quite the same thing. The script takes the JWT from the environment and never loads a key or signs anything, so the key stays wherever you already keep it and never enters this process. If you have no JWT to hand, mint one with whatever your App already uses to authenticate. An installation access token will not work here and will answer 403: reading an App's own configuration is something only the App can do."),
 ("Our App creates a webhook on each repository instead. Is a blank App URL wrong?",
  "No, and the script does not call it wrong. That is a real architecture: the App manages its own repository hooks and the App-level webhook stays unused. What tells the two apart is the events array on <code>GET /app</code>. A blank URL with no App-level subscriptions is coherent and gets reported rather than judged; a blank URL with a dozen subscriptions is an App configured to receive things it has nowhere to put. Only the second is a finding."),
 ("Why is smee.io treated as harshly as an empty field?",
  "Because it is exactly as broken and much harder to notice. It is what the quickstart hands you, it works beautifully on a laptop, and it never breaks in a way that forces anybody to revisit it. Then the App ships and every event goes to a proxy channel with no listener. An audit that only asks whether the URL field is populated passes it. That is the reason the script classifies the host rather than testing for blankness, and the same goes for <code>ngrok</code>, <code>localhost</code> and <code>example.com</code>."),
 ("The delivery list is empty but our URL looks fine. Is that the same problem?",
  "Not necessarily, and the script reports it as a question rather than a verdict. Deliveries are retained for a limited window, so an empty list can mean a quiet App, a long weekend, or a subscription to events that genuinely have not happened. What makes it conclusive is what sits next to it: no deliveries while subscribed to <code>push</code> across forty active installations is a destination that has never worked. Cause an event you control, then read the log again."),
],
"related": [
 ("/github/app-not-subscribed-to-event/", "The App is not subscribed to the event"),
 ("/github/webhook-http-url/", "A webhook posting to a plain http:// URL"),
 ("/github/webhook-content-type-mismatch/", "Form-encoded bodies sent to a JSON receiver"),
],
"citations": [CITE_APP_WEBHOOKS, CITE_APP_WEBHOOK_SETUP, CITE_APP_AUTH, CITE_FAILED_DELIVERIES],
},

]
