#!/usr/bin/env python3
"""/llm/ field notes, batch T — the writing.

Four faults that a probe of `GET /v1/models` can prove. That is the premise and
it is also the hazard: four notes that all call the same endpoint will collapse
into one note about curl unless each is given a different second reading to
compare the first against. So none of these scripts grades a status code on its
own. Each one grades a pair.

`anthropic-version-header-missing-or-ancient` owns the **version header**, read
as a matrix rather than a call: no header, `2023-06-01`, `2023-01-01`, and every
version string your own clients send. A required header is only proved required
by two probes that disagree about it, and the same matrix repeated through a
gateway base URL is the only way to see a header that is injected or stripped in
transit — the case that makes a broken client pass in staging and fail in
production.

`invalid-beta-header-value` owns the **beta header**, in two passes. The first
sorts every string your code sends into 400 and 200, near-matching the rejects
against the enum the Models API reference publishes. The second re-reads one
endpoint with and without each accepted string and diffs the JSON by key,
because a beta that graduated still returns 200 and still pins you to the shape
it shipped with. The Files API is the worked example and it is documented
precisely: with `files-api-2025-04-14` a list returns `has_more`/`first_id`/
`last_id` and no `expires_at`; without it, `next_page` and `expires_at`.

Those two are deliberately about **headers**, never about model ids. The
published `retired-model-id-still-in-code` and `model-past-shutdown-date` own
diffing configured model strings against the model list, and nothing here
re-reads that. Nor is this the published `long-context-gated-on-obsolete-beta`,
which is about a context window and which explicitly *refuses* to probe the beta
header, on the correct grounds that a 200 from `GET /v1/models` says nothing
about what the beta does on `/v1/messages`. This batch takes the other half of
that sentence: the probe is worthless as evidence of effect and conclusive as
evidence of validity, so the note that owns validity is the one that should make
the call.

`org-verification-required` is the one note here that never sees the error it is
about. Neither provider replays yesterday's 400, and no endpoint reports whether
an organization is verified — that state is Console-only, and the note says so
rather than inventing a field. What survives is a row in the usage report, and
the row is ambiguous: requests billed with no tokens either side is also the
signature of the published `reasoning-model-rejects-max-tokens`. The separation
is the comparison this script makes and that one does not — one model, one hour,
**two keys**, one of them producing output and one of them not. A parameter a
model refuses is refused for every key; a gate on the streaming route is not.
Where the reading comes out model-wide, this script says so and hands it back by
name instead of claiming it.

`unsupported-country-region` is the only note in the section whose variable is
the machine. The call, the key and the endpoint are all held fixed and the
location moves, so one run proves nothing: it has to be issued from the
production egress path and compared against the same run from a host you already
trust. That pairing is also what keeps it out of credential territory — a 401 on
both hosts is the key, and the script names it as somebody else's finding.

Two honesty notes carried through the prose, because both of the last two
describe conditions that are not directly readable. Verification status is not
an API field, and the geography check depends entirely on where you run it. Each
script prints what it proved and what it merely narrowed, in those words.

Read only, and stricter than the section baseline: every request in this batch
is a GET, no script constructs a request body, and nothing here calls
`count_tokens`. Two of the four deliberately send requests that are expected to
fail; a 400 from a model listing costs nothing and generates nothing, which is
the entire reason these four can be checked at all.
"""

CITE_VERSIONING = ("API versions — Claude API reference",
                   "https://platform.claude.com/docs/en/api/versioning")
CITE_OVERVIEW = ("API overview, including the required headers table",
                 "https://platform.claude.com/docs/en/api/overview")
CITE_ERRORS = ("Errors — Claude API reference",
               "https://platform.claude.com/docs/en/api/errors")
CITE_MODELS_LIST = ("List Models — Claude API reference",
                    "https://platform.claude.com/docs/en/api/models/list")
CITE_BETA = ("Beta headers — Claude API reference",
             "https://platform.claude.com/docs/en/api/beta-headers")
CITE_FILES = ("Files API, including the files-api-2025-04-14 migration table",
              "https://platform.claude.com/docs/en/build-with-claude/files")
CITE_REGIONS = ("Supported regions — Claude API reference",
                "https://platform.claude.com/docs/en/api/supported-regions")
CITE_OAI_ERRORS = ("Error codes — OpenAI platform docs",
                   "https://developers.openai.com/api/docs/guides/error-codes")
CITE_OAI_USAGE = ("Usage — OpenAI API reference",
                  "https://platform.openai.com/docs/api-reference/usage/completions")
CITE_OAI_MODELS = ("Models — OpenAI API reference",
                   "https://platform.openai.com/docs/api-reference/models")
CITE_OAI_ADMIN = ("Admin APIs — OpenAI platform docs",
                  "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_OAI_VERIFY = ("API organization verification — OpenAI help centre",
                   "https://help.openai.com/en/articles/10910291-api-organization-verification")

REL_VERSION = ("/llm/anthropic-version-header-missing-or-ancient/",
               "The other header on the same request, and the matrix that proves it")
REL_BETA = ("/llm/invalid-beta-header-value/",
            "The other header, sorted by status code and then by response shape")
REL_VERIFY = ("/llm/org-verification-required/",
              "When the model resolves and one route still cannot use it")
REL_REGION = ("/llm/unsupported-country-region/",
              "When the same key works here and 403s where it is deployed")
REL_1M = ("/llm/long-context-gated-on-obsolete-beta/",
          "A beta header that is valid, accepted, and does nothing")
REL_RETIRED = ("/llm/retired-model-id-still-in-code/",
               "The model ids in your config, diffed against the model list")
REL_ZERO_OUT = ("/llm/reasoning-model-rejects-max-tokens/",
                "The same usage row, when every key on the model is silent")
REL_LIMITER = ("/llm/rate-limit-429-limiter-unidentified/",
               "What else one probe of the model list tells you")
REL_GEO_COST = ("/llm/us-inference-geo-premium-unnoticed/",
                "Geography as a line on the bill rather than a wall")
REL_QUOTA = ("/llm/quota-exhausted-not-rate-limited/",
             "The other refusal that has nothing to do with your request")

GUIDES = [
{
"slug": "anthropic-version-header-missing-or-ancient",
"title": "anthropic-version is missing, ancient, or added in transit",
"description": "Probe GET /v1/models three ways: no version header, 2023-06-01, 2023-01-01. Repeat through your gateway, because a header added in transit hides the fault.",
"h1": "anthropic-version is missing, ancient, or added in transit",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic-version header required 400",
             "anthropic-version 2023-06-01 vs 2023-01-01",
             "claude api missing anthropic-version invalid_request_error",
             "gateway injects anthropic-version header",
             "anthropic api version header proxy stripped"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_API_KEY, a workspace key, used only for GETs of /v1/models. Optionally a gateway base URL and the version strings your own clients send, because nothing in the API can read your source tree.",
"lead": "The webhook receiver has worked for a year. It is forty lines of <code>fetch</code> written the afternoon somebody needed it, it posts to Claude, and it has never once been touched. Today it returns <code>400 invalid_request_error</code> on every call and the message is about a header you have never had to think about, because the SDK sets it and this thing is not the SDK. The part worth understanding is not the fix, which is one line. It is why it worked yesterday: the request used to go through the gateway, the gateway added <code>anthropic-version</code> for you, and last week somebody pointed that service straight at the API.",
"short_answer": """<p>Probe, do not read. There is no endpoint that reports which version header your clients send, so the script measures the behaviour instead: <code>GET /v1/models</code> with a <strong>workspace key</strong>, three times. Once with <strong>no <code>anthropic-version</code> header at all</strong>, once with <code>2023-06-01</code>, once with <code>2023-01-01</code>. The listing generates nothing and bills nothing, and a 400 from it costs exactly as little as a 200.</p>
<p>No single status is the finding. <em>Absent 400, current 200</em> is the shape a direct connection should have. <em>Absent 200</em> means something on that path is supplying the header for you, which is the interesting result, because every client behind it is untested. <em>Current not 200</em> is a credential problem wearing a versioning costume, and the script says so instead of grading the rest of a matrix it cannot trust.</p>
<p>Then repeat the whole matrix through the base URL your production traffic actually leaves by and diff the two. A gateway that <strong>injects</strong> the header turns a broken client into a passing one in staging and a 400 storm in production. A gateway that <strong>strips</strong> or rewrites it does the reverse. Neither is visible from a single host, and that comparison is the reason this note has a script rather than a sentence.</p>
<p>Only two values have ever existed: <code>2023-01-01</code>, the initial release, and <code>2023-06-01</code>, the current one. So declare the strings your clients send and the script grades them too. Anything that is not one of those two is a typo or an invention, whatever the probe returns for it.</p>
<p>A client pinned to <code>2023-01-01</code> may well still get a 200. That is not reassurance. Previous versions are documented as deprecated and may be unavailable to new users, and the pin freezes you before the <code>2023-06-01</code> streaming format: incremental named events, and no <code>data: [DONE]</code>.</p>""",
"problem": """<p><code>anthropic-version</code> is required on every request to the Claude API. It sits in the same headers table as <code>x-api-key</code> and it is not optional. Every official SDK sets it for you, which is precisely why nobody thinks about it: the header is invisible until somebody writes HTTP by hand, and somebody always does. A webhook receiver, a shell script, a Lambda that could not carry the dependency, an internal proxy, a code sample from a blog post that predates the SDK.</p>
<p>What makes it a field note rather than a footnote is that the fault is not stable across environments. Gateways, service meshes and API management layers add default headers, and adding a sensible <code>anthropic-version</code> to outbound Anthropic traffic is exactly the sort of sensible thing they are configured to do. So the same client is correct behind the gateway and broken beside it, and the discovery event is a deployment that changes which of the two it is.</p>
<p>The ancient pin is quieter and lasts longer. <code>2023-01-01</code> is a real version, so it does not necessarily error. It is also the version before streaming got named events, before <code>data: [DONE]</code> was removed, and before the legacy <code>exception</code> and <code>truncated</code> response values were dropped. A client pinned there is being served the old contract, and the version policy explicitly reserves the right to change error conditions and add enum variants between versions, which is the whole point of the header.</p>
<p>And the invented value is worth its own line because it is so easy to produce. <code>2024-06-01</code> looks like a version. <code>2023-06-01 </code> with a trailing space looks identical in a config file. Neither has ever existed, and neither will announce itself as fiction.</p>""",
"why": """<p><strong>One status code is not evidence about a required header.</strong> If you send the header and get a 200, you have learned that your request worked, not that the header was needed, not that you sent it, and certainly not that the header reaching Anthropic is the one you set. The claim "this header is required on this path" needs two probes that disagree: absent must fail where present succeeds. That is why the unit here is a matrix and why the script refuses to grade anything else when the current-version probe is not a 200.</p>
<p><strong>The gateway comparison is the finding, not a nicety.</strong> A header injected in transit is undetectable from either side alone. From the client you see a 200. From the API you see a valid request. The only thing that reveals it is the same probe issued twice down two paths, and the result you are looking for is the pleasant one: staging is fine. That is the environment where a broken client passes review.</p>
<p><strong>Acceptance of <code>2023-01-01</code> is not permission to keep it.</strong> The probe reports what the host does today. The documentation says previous versions are deprecated and may be unavailable for new users, and a version pin freezes error-condition and enum behaviour that Anthropic reserves the right to evolve. So the script reports the status and grades the pin as a finding regardless of it, because those are two different questions and only one of them is answered by a number.</p>
<p><strong>This note owns a header and not a model id.</strong> There is a published note that diffs the model strings in your configuration against the model list, and another that reads shutdown dates. Nothing here touches either. The version header is a property of the client, it fails identically on every model, and it fails before any model is selected — which is also why <code>GET /v1/models</code> is the right endpoint to prove it on.</p>
<p><strong>A declared version string is graded even when the probe likes it.</strong> The API is not the authority on whether your configuration is sensible; the documented version history is. Two values exist. A script that only reported non-200s would wave through a client pinned to <code>2023-01-01</code> that works today and is one deprecation away from not, and would wave through <code>2024-06-01</code> as long as some host somewhere was lenient about it.</p>""",
"steps": [
 {"h": "Use a workspace key, and know what it can do",
  "body": """<p>Anthropic has no read-only tier on the data plane: the same workspace key that reads <code>/v1/models</code> could send a message. This script is trusted not to rather than prevented from it, and it makes only GETs. An Admin key is the wrong credential here and cannot reach the models endpoint at all.</p>"""},
 {"h": "Run the three probes against the API directly",
  "body": """<p><code>GET https://api.anthropic.com/v1/models</code> with no <code>anthropic-version</code> header, then with <code>2023-06-01</code>, then with <code>2023-01-01</code>. Record the status codes; do not raise on a 400. The listing costs nothing either way, which is the reason a deliberately failing probe is acceptable here at all.</p>"""},
 {"h": "Declare the version strings your own clients send",
  "body": """<p><code>ANTHROPIC_VERSIONS</code> as a comma-separated list, or repeated <code>--version</code>. Take them out of the deployed configuration, not from memory. Each one is probed and graded against the documented version history, which has exactly two entries.</p>"""},
 {"h": "Repeat the matrix through your gateway base URL",
  "body": """<p><code>--gateway</code>, or <code>ANTHROPIC_BASE_URL</code>. The same three probes down the path production actually uses. The script diffs the two matrices and names the difference: injected, stripped, or merely disagreeing.</p>"""},
 {"h": "Read the disagreements, then print the repair",
  "body": """<p>Absent-200 anywhere means a header is being added for you. Current-non-200 through the gateway means one is being removed. The repair is always the same line &mdash; send <code>anthropic-version: 2023-06-01</code> from the client itself, or drop the hand-rolled HTTP for the SDK, which sets it &mdash; and the script prints it without applying it.</p>"""},
],
"verify": """<p>Fix the client and re-run. The direct matrix should not move at all, because it never described your client; the gateway matrix should now agree with it. The re-run that matters is the one from the environment that was passing, since that is where an injected header was doing the work you thought your code was doing.</p>
<pre><code class="language-bash">ANTHROPIC_VERSIONS=2023-06-01,2023-01-01 \\
  python3 anthropic_version_header_probe.py --gateway https://llm-gw.internal
# host https://api.anthropic.com
#   (absent)      400  enforced             400 with no version header, which is correct
#   2023-06-01    200  accepted             200, the current version
#   2023-01-01    200  accepted-deprecated  200, but 2023-01-01 is deprecated and
#                                           predates the named SSE events
# version-enforced     400 without the header and 200 with 2023-06-01
# host https://llm-gw.internal
#   (absent)      200  not-enforced         200 with no version header, so something
#                                           on this path is supplying one for you
#   2023-06-01    200  accepted             200, the current version
#   2023-01-01    200  accepted-deprecated  200, but 2023-01-01 is deprecated
# version-not-enforced 200 with no anthropic-version header at all
# gateway-injects      the direct host 400s without the header and the gateway
#                      returns 200, so the gateway adds anthropic-version for you.
#                      Every client behind it is untested
#   repair: set anthropic-version: 2023-06-01 in the client itself. A header the
#           gateway adds is a header your client does not have.
# ancient-pinned       2023-01-01 is the initial release and is deprecated
#   repair: move the pin to 2023-06-01 and re-read your SSE handling first
# 2 finding(s)</code></pre>""",
"code_intro": "Three GETs per host and six pure functions. <code>probe_headers</code>, which returns an empty dict for the absent probe and is kept separate from the credential so a test can assert that no version header is sent; <code>probe_labels</code>, which builds the ordered, de-duplicated probe set from the two real versions plus yours; <code>classify_status</code>, which says what one result means in isolation and never more than that; <code>host_verdict</code>, which refuses to grade a matrix whose current-version probe is not a 200; <code>declared_findings</code>, which grades your configured strings against the documented version history rather than against a status code; and <code>gateway_verdict</code>, which is the only function here that looks at two hosts at once.",
"py_file": "anthropic_version_header_probe.py",
"py": '''"""Probe the anthropic-version header three ways, direct and via a gateway.

Read only. Every request is a GET of /v1/models, which lists model metadata,
generates no tokens and bills nothing. Nothing here sends a message, and a 400
from this endpoint costs exactly as little as a 200 -- which is the only reason
a deliberately failing probe is acceptable at all.

Three probes per host: no version header, the current 2023-06-01, and the
2023-01-01 initial release, plus every version string your own clients send,
declared on the command line because nothing in the API can read your source.

No single status is the finding. A required header is only proved required by
two probes that disagree about it, and a header injected or stripped in transit
is only visible by running the same matrix down two paths and diffing them.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_version_header_probe")

API_PATH = "/v1/models"
DIRECT = "https://api.anthropic.com"

# The complete version history. Two entries, and there have never been more.
INITIAL = "2023-01-01"
CURRENT = "2023-06-01"
KNOWN = (INITIAL, CURRENT)

# The label for the probe that deliberately sends no version header. It is not
# a version string and is never sent as one; probe_headers() is where that is
# enforced, and there is a test that says so.
ABSENT = "(absent)"

FINDINGS = ("version-not-enforced", "current-rejected", "ancient-pinned",
            "unknown-version-pinned", "gateway-injects", "gateway-strips",
            "gateway-disagrees", "unreachable")

REPAIRS = {
    "version-not-enforced":
        "something on this path adds anthropic-version for you. Find it, then "
        "set the header in each client as well: a header the infrastructure "
        "supplies is a header your code does not have.",
    "gateway-injects":
        "set anthropic-version: 2023-06-01 in the client itself. A client that "
        "only works behind the gateway is one routing change from a 400 on "
        "every request.",
    "gateway-strips":
        "the gateway is removing or rewriting anthropic-version. Fix it there; "
        "a client cannot compensate for a header that does not survive the "
        "hop.",
    "gateway-disagrees":
        "the two paths do not behave the same. Read the gateway's request "
        "header policy before trusting either matrix as a description of what "
        "your clients send.",
    "current-rejected":
        "the current version probe did not return 200, so this is a credential "
        "or connectivity problem rather than a versioning one. Nothing else in "
        "this matrix can be trusted until it is.",
    "ancient-pinned":
        "move the pin to anthropic-version: 2023-06-01, and read your streaming "
        "code first: 2023-06-01 sends incremental named events and no "
        "data: [DONE].",
    "unknown-version-pinned":
        "only 2023-01-01 and 2023-06-01 have ever existed. Replace the string "
        "with 2023-06-01 rather than trying to make it work.",
}


def probe_headers(label):
    """The version header for one probe. Pure. Empty dict for ABSENT.

    Deliberately separate from the credential. The absent probe has to send no
    anthropic-version at all, and a function that merged the auth header in
    would make that hard to assert without handling a key in a test.
    """
    if label == ABSENT:
        return {}
    return {"anthropic-version": str(label).strip()}


def probe_labels(declared):
    """The ordered probe set. Pure. ABSENT, the two real versions, then yours.

    De-duplicated with order preserved so the printed matrix is stable between
    runs, and stripped so a trailing space in an environment variable does not
    become a fourth version that has never existed.
    """
    out = [ABSENT, CURRENT, INITIAL]
    for raw in declared or []:
        text = str(raw or "").strip()
        if text and text not in out:
            out.append(text)
    return out


def classify_status(label, status):
    """What one probe result means on its own. Pure. Returns (state, detail).

    On its own is the operative phrase. Nothing here is a verdict; the verdicts
    need two rows and live in host_verdict() and gateway_verdict().
    """
    if status is None:
        return ("unreachable", "no response at all from this host")
    status = int(status)
    if label == ABSENT:
        if status == 400:
            return ("enforced", "400 with no version header, which is correct")
        if status == 200:
            return ("not-enforced",
                    "200 with no version header, so something on this path is "
                    "supplying one for you")
        if status in (401, 403):
            return ("credentials",
                    "%d, so this probe says nothing about the version header"
                    % status)
        return ("unexpected", "%d with no version header" % status)
    if status == 200:
        if label == CURRENT:
            return ("accepted", "200, the current version")
        if label == INITIAL:
            return ("accepted-deprecated",
                    "200, but 2023-01-01 is deprecated and predates the named "
                    "SSE events")
        return ("accepted-unknown",
                "200 for a string that is not one of the two documented "
                "versions")
    if status in (401, 403):
        return ("credentials",
                "%d, which is the credential rather than the version" % status)
    if status in (400, 404, 410):
        return ("refused",
                "%d, this host will not serve that version" % status)
    return ("unexpected", "%d" % status)


def host_verdict(results):
    """Grade one host's whole matrix. Pure. Returns (state, detail).

    The current-version probe is the gate. If it is not a 200 then the key, the
    host or the network is the story and every other row is noise, so this
    returns early rather than reporting a header problem it cannot see.
    """
    results = dict(results or {})
    current = results.get(CURRENT)
    absent = results.get(ABSENT)
    if current is None:
        return ("unreachable",
                "the current version probe got no response, so nothing else on "
                "this host can be read")
    if int(current) in (401, 403):
        return ("current-rejected",
                "%d for anthropic-version: %s, which is a credential problem "
                "and not a versioning one" % (int(current), CURRENT))
    if int(current) != 200:
        return ("current-rejected",
                "%d for anthropic-version: %s, which should be 200"
                % (int(current), CURRENT))
    if absent is not None and int(absent) == 200:
        return ("version-not-enforced",
                "200 with no anthropic-version header at all. The header is "
                "documented as required, so a proxy, SDK or gateway on this "
                "path is adding it")
    return ("version-enforced",
            "400 without the header and 200 with %s, which is the shape a "
            "direct connection should have" % CURRENT)


def declared_findings(results, declared):
    """[(version, state, detail)] for the strings your clients send. Pure.

    Graded against the documented version history, not against the status code.
    A pin that works today and is deprecated is still a pin that is deprecated,
    and a script that only reported non-200s would wave both of these through.
    """
    results = dict(results or {})
    seen = set()
    out = []
    for raw in declared or []:
        text = str(raw or "").strip()
        if not text or text in seen or text == CURRENT:
            continue
        seen.add(text)
        status = results.get(text)
        suffix = ("" if status is None
                  else " (this host returns %d for it)" % int(status))
        if text == INITIAL:
            out.append((text, "ancient-pinned",
                        "2023-01-01 is the initial release and is deprecated. A "
                        "client pinned there does not get the 2023-06-01 SSE "
                        "format: incremental named events, and no "
                        "data: [DONE]" + suffix))
        else:
            out.append((text, "unknown-version-pinned",
                        "only 2023-01-01 and 2023-06-01 have ever existed, so "
                        "this string is a typo or an invention" + suffix))
    out.sort()
    return out


def gateway_verdict(direct, proxy):
    """Compare two hosts' matrices. Pure. Returns (state, detail).

    The only function here that looks at two hosts at once, and the only way a
    header rewritten in transit becomes visible: from the client it is a 200,
    from the API it is a valid request, and nothing but the diff shows it.
    """
    direct = dict(direct or {})
    proxy = dict(proxy or {})
    if not proxy:
        return ("no-gateway",
                "no gateway base URL was given, so nothing was compared. A "
                "header added in transit is invisible to a single host")
    d_absent, p_absent = direct.get(ABSENT), proxy.get(ABSENT)
    d_current, p_current = direct.get(CURRENT), proxy.get(CURRENT)
    if (d_absent is not None and p_absent is not None
            and int(d_absent) == 400 and int(p_absent) == 200):
        return ("gateway-injects",
                "the direct host 400s without the header and the gateway "
                "returns 200, so the gateway adds anthropic-version for you. "
                "Every client behind it is untested")
    if (d_current is not None and p_current is not None
            and int(d_current) == 200 and int(p_current) != 200):
        return ("gateway-strips",
                "anthropic-version: %s is accepted directly and returns %d "
                "through the gateway, so it is being stripped or rewritten in "
                "transit" % (CURRENT, int(p_current)))
    differing = sorted(label for label in set(direct) | set(proxy)
                       if direct.get(label) != proxy.get(label))
    if differing:
        return ("gateway-disagrees",
                "the two hosts return different statuses for: "
                + ", ".join(differing))
    return ("gateway-agrees",
            "both hosts return the same status for every probe, so nothing on "
            "the way is rewriting the header")


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed."""
    line = REPAIRS.get(state)
    if not line:
        return []
    if state in ("gateway-injects", "gateway-strips", "version-not-enforced"):
        return [line,
                "the durable fix is the official SDK, which sets "
                "anthropic-version on every request whether or not anything "
                "else does."]
    return [line]


def probe(session, base, key, label, timeout=30):
    """One GET. Returns a status code, or None when the host is unreachable.

    Never raises on a 4xx: a 400 is the expected answer to one of these probes
    and is the most informative result the script can get.
    """
    headers = {"x-api-key": key}
    headers.update(probe_headers(label))
    try:
        r = session.get(base.rstrip("/") + API_PATH, headers=headers,
                        params={"limit": 1}, timeout=timeout)
    except requests.RequestException as exc:
        log.debug("probe %s against %s failed: %s", label, base, exc)
        return None
    return r.status_code


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version", action="append", default=[],
                    help="a version string your clients send (repeatable)")
    ap.add_argument("--gateway", default=os.environ.get("ANTHROPIC_BASE_URL"),
                    help="base URL of the proxy or gateway to compare against")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY to a workspace key. This script only "
                  "issues GET requests against %s", API_PATH)
        return 2

    declared = list(args.version)
    declared += [p.strip() for p in
                 (os.environ.get("ANTHROPIC_VERSIONS") or "").split(",")
                 if p.strip()]
    labels = probe_labels(declared)

    hosts = [("direct", DIRECT)]
    if args.gateway and args.gateway.rstrip("/") != DIRECT:
        hosts.append(("gateway", args.gateway))

    session = requests.Session()
    matrices = {}
    findings = 0

    for role, base in hosts:
        results = {}
        log.info("host %s", base)
        for label in labels:
            status = probe(session, base, key, label)
            results[label] = status
            state, detail = classify_status(label, status)
            emit = log.warning if state in ("not-enforced", "unreachable") else log.info
            emit("  %-13s %s  %-20s %s", label,
                 "---" if status is None else status, state, detail)
        matrices[role] = results

        state, detail = host_verdict(results)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-20s %s", state, detail)
        for line in repair_lines(state):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    state, detail = gateway_verdict(matrices.get("direct"),
                                    matrices.get("gateway"))
    emit = log.warning if state in FINDINGS else log.info
    emit("%-20s %s", state, detail)
    for line in repair_lines(state):
        emit("  repair: %s", line)
    if state in FINDINGS:
        findings += 1

    for version, state, detail in declared_findings(matrices.get("direct"),
                                                    declared):
        log.warning("%-20s %s: %s", state, version, detail)
        for line in repair_lines(state):
            log.warning("  repair: %s", line)
        findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-version-header-probe.mjs",
"js": '''/**
 * Probe the anthropic-version header three ways, direct and via a gateway.
 *
 * Read only. Every request is a GET of /v1/models, which generates no tokens
 * and bills nothing. Nothing here sends a message, and a 400 from this
 * endpoint costs exactly as little as a 200.
 *
 * No single status is the finding. A required header is only proved required
 * by two probes that disagree about it, and a header injected or stripped in
 * transit is only visible by running the same matrix down two paths.
 */
const API_PATH = '/v1/models';
export const DIRECT = 'https://api.anthropic.com';

export const INITIAL = '2023-01-01';
export const CURRENT = '2023-06-01';
export const KNOWN = [INITIAL, CURRENT];

// The label for the probe that deliberately sends no version header.
export const ABSENT = '(absent)';

const FINDINGS = new Set(['version-not-enforced', 'current-rejected',
  'ancient-pinned', 'unknown-version-pinned', 'gateway-injects',
  'gateway-strips', 'gateway-disagrees', 'unreachable']);

const REPAIRS = {
  'version-not-enforced':
    'something on this path adds anthropic-version for you. Find it, then set '
    + 'the header in each client as well: a header the infrastructure supplies '
    + 'is a header your code does not have.',
  'gateway-injects':
    'set anthropic-version: 2023-06-01 in the client itself. A client that only '
    + 'works behind the gateway is one routing change from a 400 on every '
    + 'request.',
  'gateway-strips':
    'the gateway is removing or rewriting anthropic-version. Fix it there; a '
    + 'client cannot compensate for a header that does not survive the hop.',
  'gateway-disagrees':
    'the two paths do not behave the same. Read the gateway request header '
    + 'policy before trusting either matrix as a description of your clients.',
  'current-rejected':
    'the current version probe did not return 200, so this is a credential or '
    + 'connectivity problem rather than a versioning one. Nothing else in this '
    + 'matrix can be trusted until it is.',
  'ancient-pinned':
    'move the pin to anthropic-version: 2023-06-01, and read your streaming '
    + 'code first: 2023-06-01 sends incremental named events and no '
    + 'data: [DONE].',
  'unknown-version-pinned':
    'only 2023-01-01 and 2023-06-01 have ever existed. Replace the string with '
    + '2023-06-01 rather than trying to make it work.',
};

/** The version header for one probe. Pure. Empty object for ABSENT. */
export function probeHeaders(label) {
  if (label === ABSENT) return {};
  return { 'anthropic-version': String(label).trim() };
}

/** The ordered probe set. Pure. ABSENT, the two real versions, then yours. */
export function probeLabels(declared) {
  const out = [ABSENT, CURRENT, INITIAL];
  for (const raw of declared ?? []) {
    const text = String(raw ?? '').trim();
    if (text && !out.includes(text)) out.push(text);
  }
  return out;
}

/** What one probe result means on its own. Pure. Returns [state, detail]. */
export function classifyStatus(label, status) {
  if (status === null || status === undefined) {
    return ['unreachable', 'no response at all from this host'];
  }
  const code = Math.trunc(Number(status));
  if (label === ABSENT) {
    if (code === 400) return ['enforced', '400 with no version header, which is correct'];
    if (code === 200) {
      return ['not-enforced',
        '200 with no version header, so something on this path is supplying '
        + 'one for you'];
    }
    if (code === 401 || code === 403) {
      return ['credentials',
        `${code}, so this probe says nothing about the version header`];
    }
    return ['unexpected', `${code} with no version header`];
  }
  if (code === 200) {
    if (label === CURRENT) return ['accepted', '200, the current version'];
    if (label === INITIAL) {
      return ['accepted-deprecated',
        '200, but 2023-01-01 is deprecated and predates the named SSE events'];
    }
    return ['accepted-unknown',
      '200 for a string that is not one of the two documented versions'];
  }
  if (code === 401 || code === 403) {
    return ['credentials', `${code}, which is the credential rather than the version`];
  }
  if (code === 400 || code === 404 || code === 410) {
    return ['refused', `${code}, this host will not serve that version`];
  }
  return ['unexpected', `${code}`];
}

/** Grade one host's whole matrix. Pure. Returns [state, detail]. */
export function hostVerdict(results) {
  const r = { ...(results ?? {}) };
  const current = r[CURRENT];
  const absent = r[ABSENT];
  if (current === null || current === undefined) {
    return ['unreachable',
      'the current version probe got no response, so nothing else on this host '
      + 'can be read'];
  }
  const code = Math.trunc(Number(current));
  if (code === 401 || code === 403) {
    return ['current-rejected',
      `${code} for anthropic-version: ${CURRENT}, which is a credential problem `
      + 'and not a versioning one'];
  }
  if (code !== 200) {
    return ['current-rejected',
      `${code} for anthropic-version: ${CURRENT}, which should be 200`];
  }
  if (absent !== null && absent !== undefined && Math.trunc(Number(absent)) === 200) {
    return ['version-not-enforced',
      '200 with no anthropic-version header at all. The header is documented as '
      + 'required, so a proxy, SDK or gateway on this path is adding it'];
  }
  return ['version-enforced',
    `400 without the header and 200 with ${CURRENT}, which is the shape a `
    + 'direct connection should have'];
}

/** [[version, state, detail]] for the strings your clients send. Pure. */
export function declaredFindings(results, declared) {
  const r = { ...(results ?? {}) };
  const seen = new Set();
  const out = [];
  for (const raw of declared ?? []) {
    const text = String(raw ?? '').trim();
    if (!text || seen.has(text) || text === CURRENT) continue;
    seen.add(text);
    const status = r[text];
    const suffix = (status === null || status === undefined)
      ? '' : ` (this host returns ${Math.trunc(Number(status))} for it)`;
    if (text === INITIAL) {
      out.push([text, 'ancient-pinned',
        '2023-01-01 is the initial release and is deprecated. A client pinned '
        + 'there does not get the 2023-06-01 SSE format: incremental named '
        + 'events, and no data: [DONE]' + suffix]);
    } else {
      out.push([text, 'unknown-version-pinned',
        'only 2023-01-01 and 2023-06-01 have ever existed, so this string is a '
        + 'typo or an invention' + suffix]);
    }
  }
  out.sort((a, b) => a[0].localeCompare(b[0]));
  return out;
}

/** Compare two hosts' matrices. Pure. Returns [state, detail]. */
export function gatewayVerdict(direct, proxy) {
  const d = { ...(direct ?? {}) };
  const p = { ...(proxy ?? {}) };
  if (Object.keys(p).length === 0) {
    return ['no-gateway',
      'no gateway base URL was given, so nothing was compared. A header added '
      + 'in transit is invisible to a single host'];
  }
  const num = (v) => ((v === null || v === undefined) ? null : Math.trunc(Number(v)));
  const dAbsent = num(d[ABSENT]);
  const pAbsent = num(p[ABSENT]);
  const dCurrent = num(d[CURRENT]);
  const pCurrent = num(p[CURRENT]);
  if (dAbsent === 400 && pAbsent === 200) {
    return ['gateway-injects',
      'the direct host 400s without the header and the gateway returns 200, so '
      + 'the gateway adds anthropic-version for you. Every client behind it is '
      + 'untested'];
  }
  if (dCurrent === 200 && pCurrent !== null && pCurrent !== 200) {
    return ['gateway-strips',
      `anthropic-version: ${CURRENT} is accepted directly and returns ${pCurrent} `
      + 'through the gateway, so it is being stripped or rewritten in transit'];
  }
  const labels = [...new Set([...Object.keys(d), ...Object.keys(p)])].sort();
  const differing = labels.filter((l) => (d[l] ?? null) !== (p[l] ?? null));
  if (differing.length) {
    return ['gateway-disagrees',
      'the two hosts return different statuses for: ' + differing.join(', ')];
  }
  return ['gateway-agrees',
    'both hosts return the same status for every probe, so nothing on the way '
    + 'is rewriting the header'];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  const line = REPAIRS[state];
  if (!line) return [];
  if (state === 'gateway-injects' || state === 'gateway-strips'
      || state === 'version-not-enforced') {
    return [line,
      'the durable fix is the official SDK, which sets anthropic-version on '
      + 'every request whether or not anything else does.'];
  }
  return [line];
}

async function probe(base, key, label) {
  const url = new URL(base.replace(/\\/+$/, '') + API_PATH);
  url.searchParams.set('limit', '1');
  try {
    const r = await fetch(url, { headers: { 'x-api-key': key, ...probeHeaders(label) } });
    return r.status;
  } catch {
    return null;
  }
}

async function main() {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY to a workspace key. This script only '
                  + 'issues GET requests against /v1/models');
    process.exitCode = 2;
    return;
  }
  const declared = (process.env.ANTHROPIC_VERSIONS ?? '')
    .split(',').map((s) => s.trim()).filter(Boolean);
  const labels = probeLabels(declared);

  const gateway = process.env.ANTHROPIC_BASE_URL;
  const hosts = [['direct', DIRECT]];
  if (gateway && gateway.replace(/\\/+$/, '') !== DIRECT) hosts.push(['gateway', gateway]);

  const matrices = {};
  let findings = 0;

  for (const [role, base] of hosts) {
    const results = {};
    console.log(`host ${base}`);
    for (const label of labels) {
      const status = await probe(base, key, label);
      results[label] = status;
      const [state, detail] = classifyStatus(label, status);
      console.log(`  ${label.padEnd(13)} ${status ?? '---'}  ${state.padEnd(20)} ${detail}`);
    }
    matrices[role] = results;
    const [state, detail] = hostVerdict(results);
    console.log(`${state.padEnd(20)} ${detail}`);
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }

  const [gstate, gdetail] = gatewayVerdict(matrices.direct, matrices.gateway);
  console.log(`${gstate.padEnd(20)} ${gdetail}`);
  for (const line of repairLines(gstate)) console.log(`  repair: ${line}`);
  if (FINDINGS.has(gstate)) findings += 1;

  for (const [version, state, detail] of declaredFindings(matrices.direct, declared)) {
    console.log(`${state.padEnd(20)} ${version}: ${detail}`);
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    findings += 1;
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the whole argument: a matrix where the absent probe 400s and the current one 200s is healthy, and the same matrix with the absent probe returning 200 is not &mdash; the difference is one number and it is the only thing that proves the header is enforced on that path. Then the gateway pair, injecting and stripping, which no single host can see. Then the gate: a 401 on the current-version probe must produce <code>current-rejected</code> and stop, because a matrix you cannot authenticate is not evidence about a header. Then <code>probe_headers</code>, asserted to send nothing at all for the absent label, since a bug there would quietly turn the entire script into three identical probes. And finally the declared strings, graded against a version history with two entries in it rather than against a status code.",
"test_py_file": "test_anthropic_version_header_probe.py",
"test_py": '''from anthropic_version_header_probe import (ABSENT, CURRENT, INITIAL,
                                            classify_status,
                                            declared_findings,
                                            gateway_verdict, host_verdict,
                                            probe_headers, probe_labels,
                                            repair_lines)


def matrix(absent=400, current=200, ancient=200, **extra):
    out = {ABSENT: absent, CURRENT: current, INITIAL: ancient}
    out.update(extra)
    return out


def test_the_pair_of_probes_is_what_proves_the_header_is_required():
    # One status code says nothing. Absent-400 next to current-200 is the whole
    # claim, and flipping the absent probe to 200 inverts the verdict.
    state, detail = host_verdict(matrix())
    assert state == "version-enforced"
    assert "400 without the header" in detail

    state, detail = host_verdict(matrix(absent=200))
    assert state == "version-not-enforced"
    assert "gateway on this path is adding it" in detail
    assert classify_status(ABSENT, 200)[1].endswith("supplying one for you")
    assert any("does not have" in line for line in repair_lines(state))


def test_a_gateway_that_injects_the_header_is_only_visible_from_two_hosts():
    state, detail = gateway_verdict(matrix(absent=400), matrix(absent=200))
    assert state == "gateway-injects"
    assert "Every client behind it is untested" in detail
    lines = repair_lines(state)
    assert any("in the client itself" in line for line in lines)
    assert any("official SDK" in line for line in lines)


def test_a_gateway_that_strips_the_header_is_the_mirror_case():
    state, detail = gateway_verdict(matrix(), matrix(current=400))
    assert state == "gateway-strips"
    assert "stripped or rewritten in transit" in detail

    # Same statuses on both paths is not a finding, and a missing gateway is a
    # statement about coverage rather than about health.
    assert gateway_verdict(matrix(), matrix())[0] == "gateway-agrees"
    state, detail = gateway_verdict(matrix(), {})
    assert state == "no-gateway"
    assert "invisible to a single host" in detail


def test_a_matrix_you_cannot_authenticate_is_not_evidence_about_a_header():
    # The gate. A 401 on the current-version probe means the key is the story,
    # and grading the absent probe on top of it would invent a header problem.
    state, detail = host_verdict(matrix(absent=401, current=401))
    assert state == "current-rejected"
    assert "credential problem" in detail
    assert classify_status(ABSENT, 401)[0] == "credentials"
    assert host_verdict(matrix(current=None))[0] == "unreachable"
    assert host_verdict({})[0] == "unreachable"


def test_the_absent_probe_really_sends_no_version_header():
    # A bug here turns the whole script into three identical probes that all
    # pass, so it is asserted rather than assumed.
    assert probe_headers(ABSENT) == {}
    assert probe_headers(CURRENT) == {"anthropic-version": "2023-06-01"}
    assert probe_headers("  2023-01-01 ") == {"anthropic-version": "2023-01-01"}
    assert probe_labels([]) == [ABSENT, CURRENT, INITIAL]
    assert probe_labels(["2023-06-01", " ", "2024-06-01", "2024-06-01"]) == [
        ABSENT, CURRENT, INITIAL, "2024-06-01"]


def test_declared_versions_are_graded_against_the_history_not_the_status():
    rows = declared_findings(matrix(**{"2024-06-01": 400}),
                             [CURRENT, INITIAL, "2024-06-01"])
    states = {version: state for version, state, _ in rows}
    assert CURRENT not in states
    assert states[INITIAL] == "ancient-pinned"
    assert states["2024-06-01"] == "unknown-version-pinned"

    ancient = [d for v, _, d in rows if v == INITIAL][0]
    assert "data: [DONE]" in ancient
    assert "this host returns 200 for it" in ancient
    assert any("2023-06-01" in line for line in repair_lines("ancient-pinned"))


def test_single_statuses_are_described_and_never_promoted_to_verdicts():
    assert classify_status(INITIAL, 200)[0] == "accepted-deprecated"
    assert classify_status(INITIAL, 410)[0] == "refused"
    assert classify_status("2024-06-01", 200)[0] == "accepted-unknown"
    assert classify_status(CURRENT, 529)[0] == "unexpected"
    assert classify_status(CURRENT, None)[0] == "unreachable"
    assert repair_lines("version-enforced") == []
''',
"test_js_file": "anthropic-version-header-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ABSENT, CURRENT, INITIAL, classifyStatus, declaredFindings,
         gatewayVerdict, hostVerdict, probeHeaders, probeLabels,
         repairLines } from './anthropic-version-header-probe.mjs';

const matrix = ({ absent = 400, current = 200, ancient = 200, ...extra } = {}) =>
  ({ [ABSENT]: absent, [CURRENT]: current, [INITIAL]: ancient, ...extra });

test('the pair of probes is what proves the header is required', () => {
  let [state, detail] = hostVerdict(matrix());
  assert.equal(state, 'version-enforced');
  assert.ok(detail.includes('400 without the header'));

  [state, detail] = hostVerdict(matrix({ absent: 200 }));
  assert.equal(state, 'version-not-enforced');
  assert.ok(detail.includes('gateway on this path is adding it'));
  assert.ok(classifyStatus(ABSENT, 200)[1].endsWith('supplying one for you'));
  assert.ok(repairLines(state).some((l) => l.includes('does not have')));
});

test('a gateway that injects the header is only visible from two hosts', () => {
  const [state, detail] = gatewayVerdict(matrix({ absent: 400 }), matrix({ absent: 200 }));
  assert.equal(state, 'gateway-injects');
  assert.ok(detail.includes('Every client behind it is untested'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('in the client itself')));
  assert.ok(lines.some((l) => l.includes('official SDK')));
});

test('a gateway that strips the header is the mirror case', () => {
  const [state, detail] = gatewayVerdict(matrix(), matrix({ current: 400 }));
  assert.equal(state, 'gateway-strips');
  assert.ok(detail.includes('stripped or rewritten in transit'));
  assert.equal(gatewayVerdict(matrix(), matrix())[0], 'gateway-agrees');
  const [nostate, nodetail] = gatewayVerdict(matrix(), {});
  assert.equal(nostate, 'no-gateway');
  assert.ok(nodetail.includes('invisible to a single host'));
});

test('a matrix you cannot authenticate is not evidence about a header', () => {
  const [state, detail] = hostVerdict(matrix({ absent: 401, current: 401 }));
  assert.equal(state, 'current-rejected');
  assert.ok(detail.includes('credential problem'));
  assert.equal(classifyStatus(ABSENT, 401)[0], 'credentials');
  assert.equal(hostVerdict(matrix({ current: null }))[0], 'unreachable');
  assert.equal(hostVerdict({})[0], 'unreachable');
});

test('the absent probe really sends no version header', () => {
  assert.deepEqual(probeHeaders(ABSENT), {});
  assert.deepEqual(probeHeaders(CURRENT), { 'anthropic-version': '2023-06-01' });
  assert.deepEqual(probeHeaders('  2023-01-01 '), { 'anthropic-version': '2023-01-01' });
  assert.deepEqual(probeLabels([]), [ABSENT, CURRENT, INITIAL]);
  assert.deepEqual(probeLabels(['2023-06-01', ' ', '2024-06-01', '2024-06-01']),
                   [ABSENT, CURRENT, INITIAL, '2024-06-01']);
});

test('declared versions are graded against the history not the status', () => {
  const rows = declaredFindings(matrix({ '2024-06-01': 400 }),
                                [CURRENT, INITIAL, '2024-06-01']);
  const states = Object.fromEntries(rows.map(([v, s]) => [v, s]));
  assert.equal(states[CURRENT], undefined);
  assert.equal(states[INITIAL], 'ancient-pinned');
  assert.equal(states['2024-06-01'], 'unknown-version-pinned');
  const ancient = rows.find(([v]) => v === INITIAL)[2];
  assert.ok(ancient.includes('data: [DONE]'));
  assert.ok(ancient.includes('this host returns 200 for it'));
  assert.ok(repairLines('ancient-pinned').some((l) => l.includes('2023-06-01')));
});

test('single statuses are described and never promoted to verdicts', () => {
  assert.equal(classifyStatus(INITIAL, 200)[0], 'accepted-deprecated');
  assert.equal(classifyStatus(INITIAL, 410)[0], 'refused');
  assert.equal(classifyStatus('2024-06-01', 200)[0], 'accepted-unknown');
  assert.equal(classifyStatus(CURRENT, 529)[0], 'unexpected');
  assert.equal(classifyStatus(CURRENT, null)[0], 'unreachable');
  assert.deepEqual(repairLines('version-enforced'), []);
});
''',
"faq": [
 ("Which values of anthropic-version are valid?",
  "Two, and there have only ever been two. 2023-01-01 was the initial release and 2023-06-01 is current. 2023-06-01 changed the streaming format to incremental named server-sent events, removed the data: [DONE] event, and dropped the legacy exception and truncated response values. Anything else is a typo or an invention, and the script grades a declared string against that history rather than against whatever a host happens to return for it today."),
 ("The header is required, so why does a request without it sometimes work?",
  "Because something between your client and the API is adding it. Gateways, service meshes and API management layers inject default headers as a matter of routine, and adding a sensible anthropic-version to outbound Anthropic traffic is exactly the sort of thing they are configured to do. That is the case this note exists for: the client is broken the whole time and only one of your two network paths says so. It is also why the script runs the same three probes through your gateway base URL and diffs the two matrices, since neither host can see it alone."),
 ("Is this the same as the note about an obsolete beta header?",
  "No. That note is about the 1M context window, it reads max_input_tokens off the model object, and it deliberately does not probe anything, because a 200 from GET /v1/models with a beta header proves the name is recognised and says nothing about what the beta does on /v1/messages. It is right to refuse. This note is the opposite situation: anthropic-version is not a feature flag, it is a required header, and a probe that returns 400 without it and 200 with it is a direct measurement of the thing the note is about."),
 ("Why probe GET /v1/models rather than an endpoint I actually use?",
  "Because it is free in every sense that matters. The models listing generates no tokens, bills nothing and changes nothing, so both the 200 and the deliberate 400 cost the same as each other, which is nothing. Sending a message to test a header would be a generation, and a script in this section that spends money to find out whether a header is set has misunderstood the assignment."),
 ("Can this tell me which of my services is missing the header?",
  "Not on its own, and the script does not pretend otherwise. Neither API exposes the headers of requests you have already made, so there is no endpoint that can name the offending client. What the script gives you is the shape of the fault plus the paths it applies to: if the absent probe returns 200 through your gateway and 400 directly, every service behind that gateway is untested and the search is a grep of your own tree for hand-rolled HTTP. That is a much smaller search than the one you started with."),
],
"related": [REL_BETA, REL_1M, REL_LIMITER],
"citations": [CITE_VERSIONING, CITE_OVERVIEW, CITE_MODELS_LIST, CITE_ERRORS],
},
{
"slug": "invalid-beta-header-value",
"title": "The anthropic-beta value that 400s, and the one that went GA",
"description": "GET /v1/models validates any anthropic-beta string for free. Loop every value your code sends, then diff one GET with and without it to find the GA ones.",
"h1": "The anthropic-beta value that 400s, and the one that went GA",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["anthropic-beta unexpected value 400",
             "invalid_request_error anthropic-beta header",
             "anthropic beta header validate without sending a message",
             "files-api-2025-04-14 graduated response shape",
             "anthropic-beta comma separated multiple betas"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs ANTHROPIC_API_KEY, a workspace key, used only for GETs of /v1/models and /v1/files. Also needs the beta strings your code sends, declared per call site, because nothing in the API can read your source tree.",
"lead": "The pull request adds one header and it is nine characters different from the one in the documentation. Every request the service makes now returns <code>400</code>, the message names the header, and it takes about four minutes to spot. That is the easy half. The hard half is the header three services along that is spelled perfectly, was correct when it was written, returns <code>200</code> today, and is quietly holding that client on a response shape the platform stopped documenting in August &mdash; no error, no warning, and a list endpoint that has been missing <code>expires_at</code> for months.",
"short_answer": """<p>Use the model listing as a validator. <code>GET /v1/models</code> accepts and validates an <code>anthropic-beta</code> header, so with a <strong>workspace key</strong> it is a free, zero-token check for any beta string: <code>400</code> means the value is rejected, <code>200</code> means it is accepted. Loop it over every string your code sends and you have graded the whole set for the price of nothing.</p>
<p>A <code>400</code> does not tell you which of two problems you have. The documented message &mdash; <em>Unexpected value(s) <code>invalid-beta-name</code> for the <code>anthropic-beta</code> header</em> &mdash; is returned both for a name that does not exist and for a beta your organization is not entitled to. The script says so in one line rather than picking, and near-matches the rejected string against the beta enum the Models API reference publishes, so a typo comes back with the name you meant.</p>
<p>Then the second pass, which is the half nobody runs. A beta that graduated still returns <code>200</code> and is not inert: it pins you to the response shape it shipped with. So the script issues the same GET twice, once with the header and once without, and diffs the two JSON bodies by key. The Files API is the documented worked example: with <code>files-api-2025-04-14</code> a listing returns <code>has_more</code>, <code>first_id</code> and <code>last_id</code> and no <code>expires_at</code>; without it, <code>next_page</code> and an <code>expires_at</code> on every file.</p>
<p>Two structural faults come out of the same input without any request at all. Multiple betas go in <strong>one comma-separated header</strong>, so a trailing comma, an internal space or a duplicated name is a bug in the string itself. And endpoint-scoped betas are not freely combinable: on memory-store endpoints <code>agent-memory-2026-07-22</code> <em>replaces</em> <code>managed-agents-2026-04-01</code>, and sending both returns a <code>400</code>.</p>
<p>What a <code>200</code> does not prove is worth stating plainly, because <a href="/llm/long-context-gated-on-obsolete-beta/">the note about the 1M context window</a> refuses to make this call for exactly this reason. Acceptance at <code>/v1/models</code> means the name is recognised. It says nothing about whether the beta still does anything on <code>/v1/messages</code>. This script claims validity and shape, and nothing else.</p>""",
"problem": """<p>Beta names follow <code>feature-name-YYYY-MM-DD</code> and must match exactly. They are long, they are dated, they are copied by hand out of documentation and Slack messages, and there is no autocomplete for a string in a header. So they get misspelled, they get pinned to the wrong date, and they get copied from a page that has since been rewritten. The failure is total and immediate: the whole call returns <code>400</code> before anything else about the request is considered.</p>
<p>The entitlement case wears the same clothes. A beta your organization does not have access to returns the same message as a beta that does not exist, which means the obvious debugging move &mdash; checking the spelling &mdash; can be correct and useless at the same time. Somebody spends an hour proving a string matches the docs character for character while the actual answer is that the feature was never enabled for that organization.</p>
<p>The quiet failure is the graduated header, and it is the reason this note exists rather than being a paragraph in an error-message reference. Betas graduate. When they do, the header becomes optional but not inert: requests that still send it keep receiving the response shape from the beta era. The Files API graduation is documented as a table of exactly these differences. A client sitting on the old header gets <code>has_more</code>/<code>first_id</code>/<code>last_id</code> pagination instead of <code>next_page</code>, cannot use the <code>ids[]</code> filter, and never sees <code>expires_at</code> at all &mdash; which means expiry handling it does not know it needs.</p>
<p>And the header is a single string carrying a list, which is its own small hazard. Multiple betas are comma-separated in one header. A trailing comma produces an empty segment. A space after the comma may or may not survive. A duplicate is silently pointless. None of these is a spelling mistake and none of them is visible by reading the name.</p>""",
"why": """<p><strong>The endpoint that validates the header for free is not the endpoint the header is for, and that is fine here.</strong> Beta names are validated at the request layer, so the models listing rejects an unknown one exactly as the messages endpoint would, at a cost of zero tokens and zero dollars. That makes a loop over every string in your tree cheap enough to run on every deploy, which is the only frequency at which this kind of check is worth anything.</p>
<p><strong>A 400 is two findings sharing a message, and collapsing them would be a lie.</strong> Invalid name and missing entitlement return the same body. The script reports both possibilities on one line and adds the near-match if there is one, because a suggested spelling resolves the ambiguity for free in the common case and an invented certainty resolves nothing in the other one.</p>
<p><strong>The published enum is a hint corpus, never the verdict.</strong> The Models API reference lists the beta names the endpoint accepts, which makes it an excellent source of near-matches. It is also a document, and documents lag. So a string the API accepts and the enum does not list is reported as <em>the enum is behind</em>, not as an error &mdash; the probe is the authority and the list is the dictionary.</p>
<p><strong>A 200 with no shape difference is unproven, not proven fine.</strong> Only some betas change a readable GET, and the two endpoints this script can safely read are the models listing and the files listing. When the two bodies come back identical the honest output is that no difference was observable here, which is a statement about the test and not about the header. Reporting that as healthy would be the same mistake as treating acceptance as effect.</p>
<p><strong>The structural faults need no network at all, and are graded first.</strong> An empty segment from a trailing comma, an internal space, a duplicate, and the documented conflicting pair on memory-store endpoints are all properties of the string you declared. Probing them wastes a request and, worse, buries a definite finding underneath a set of status codes.</p>
<p><strong>This is a note about a header, not about a model.</strong> A configured model id that no longer exists belongs to <a href="/llm/retired-model-id-still-in-code/">the retired-id note</a>, and a context window capped in software belongs to the 1M note. Both of those read the model object. Nothing here does: every finding in this script is a property of a string in a header, which is why the same script covers betas for features this organization may not even use.</p>""",
"steps": [
 {"h": "Collect the beta strings per call site, not as a set",
  "body": """<p><code>ANTHROPIC_BETA_HEADERS</code> as JSON mapping a call site to the raw header value it sends, or repeated <code>--beta</code> for a flat list. Per call site matters: the conflicting-pair check and the malformed-string checks are properties of one header value, and a flattened set loses both.</p>"""},
 {"h": "Grade the strings before making a single request",
  "body": """<p>Split each value on commas. Empty segments, internal whitespace, duplicates and uppercase are faults in the string itself. Then check for the documented conflicting pair: on memory-store endpoints <code>agent-memory-2026-07-22</code> replaces <code>managed-agents-2026-04-01</code>, and both together is a 400.</p>"""},
 {"h": "Probe every distinct name against the model listing",
  "body": """<p><code>GET /v1/models?limit=1</code> with <code>anthropic-version: 2023-06-01</code> and <code>anthropic-beta: &lt;value&gt;</code>. 400 is rejected, 200 is accepted. Do not raise on the 400 &mdash; it is the answer. Near-match every rejected name against the published enum and print the candidates.</p>"""},
 {"h": "Diff the response shape with and without each accepted name",
  "body": """<p>The same GET twice, on <code>/v1/models</code> and on <code>/v1/files</code>. Compare the top-level keys and the keys of the first item in <code>data</code>. A difference proves the header still changes what you receive, which for a graduated beta is exactly the finding.</p>"""},
 {"h": "Print the repair, and print what was not proved",
  "body": """<p>Per rejected name: the near-matches and the entitlement possibility. Per shape difference: the keys you are missing and the migration to read. And for every accepted name with no observable difference, the sentence that this endpoint pair could not tell &mdash; not that the header is fine.</p>"""},
],
"verify": """<p>Fix a spelling and re-run: that name should move from <code>rejected-typo</code> to <code>accepted</code>. Drop a graduated header and re-run: the shape diff for it disappears, because there is no longer a header to diff against. The result that should <em>not</em> change is <code>no-visible-difference</code>, which is the script declining to grade rather than the script approving.</p>
<pre><code class="language-bash">ANTHROPIC_BETA_HEADERS='{"src/messages.py":"context-management-2025-06-27,contxt-1m-2025-08-07",
                         "src/files.py":"files-api-2025-04-14",
                         "src/memory.py":"agent-memory-2026-07-22,managed-agents-2026-04-01"}' \\
  python3 anthropic_beta_header_audit.py
# 4 distinct beta string(s) across 3 call site(s)
# rejected-typo        contxt-1m-2025-08-07: 400. Invalid, or a beta this
#                      organization is not entitled to; the API returns the same
#                      message for both
#   closest documented names: context-1m-2025-08-07, context-management-2025-06-27
#   repair: replace it with context-1m-2025-08-07, then re-run this probe.
# pinned-to-beta-shape files-api-2025-04-14: accepted, and the response differs
#                      with and without it
#   /v1/files top-level keys only with the header: first_id, has_more, last_id
#   /v1/files top-level keys only without it: next_page
#   /v1/files item keys only without it: expires_at
#   repair: the beta graduated. Removing the header switches you to page and
#           next_page cursors, the ids[] filter, and an expires_at on every
#           file. Read the migration table before dropping it.
# conflicting-pair     src/memory.py sends agent-memory-2026-07-22 with
#                      managed-agents-2026-04-01
#   repair: on memory store endpoints the first replaces the second. Sending
#           both returns 400. Send agent-memory-2026-07-22 alone there.
# accepted             context-management-2025-06-27: 200, documented
# no-visible-difference context-management-2025-06-27: same keys with and
#                      without it on the endpoints this script can read, which
#                      is not evidence that the header does nothing
# 3 finding(s)</code></pre>""",
"code_intro": "Two GETs per accepted name per endpoint, and eight pure functions. <code>split_betas</code>, which turns one header value into names plus the structural faults in the string; <code>load_call_sites</code>, which accepts JSON, a list or a bare comma string so the input can come from wherever your config keeps it; <code>levenshtein</code> and <code>near_matches</code>, which rank a rejected name against the published enum; <code>classify_probe</code>, which reports the two meanings of a 400 without choosing between them; <code>key_sets</code> and <code>shape_delta</code>, which compare two bodies by key at the top level and at the first item; <code>graduation_verdict</code>, which is careful to say that an identical pair proves nothing; and <code>conflicting</code>, for the one documented pair that must not be sent together.",
"py_file": "anthropic_beta_header_audit.py",
"py": '''"""Grade every anthropic-beta string your code sends, without sending one.

Read only. Every request is a GET: /v1/models to validate a beta name, and
/v1/models plus /v1/files twice each to compare a response with and without a
header. No request body is constructed and nothing is generated or billed.

Two passes, because the two failures do not share a signal. A misspelled or
unentitled name returns 400 and is loud. A name that graduated to GA returns
200 and is silent, and the only read-only evidence of it is that the same GET
returns a different shape with the header than without it.

What a 200 proves is narrow and the script says so: the name is recognised by
the request layer. It is not evidence that the beta still does anything on
/v1/messages, and nothing here claims that it is.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("anthropic_beta_header_audit")

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"

# The beta names the Models API reference publishes as accepted values. This is
# a dictionary for near-matching a rejected string, never a verdict: it is a
# document, documents lag, and the probe is the authority. A name the API
# accepts that is missing from here is reported as the list being behind.
KNOWN_BETAS = (
    "message-batches-2024-09-24", "prompt-caching-2024-07-31",
    "computer-use-2024-10-22", "computer-use-2025-01-24",
    "computer-use-2025-11-24", "pdfs-2024-09-25",
    "token-counting-2024-11-01", "token-efficient-tools-2025-02-19",
    "output-128k-2025-02-19", "output-300k-2026-03-24",
    "files-api-2025-04-14", "mcp-client-2025-04-04", "mcp-client-2025-11-20",
    "mcp-tunnels-2026-06-22", "dev-full-thinking-2025-05-14",
    "interleaved-thinking-2025-05-14", "code-execution-2025-05-22",
    "extended-cache-ttl-2025-04-11", "context-1m-2025-08-07",
    "context-management-2025-06-27",
    "model-context-window-exceeded-2025-08-26", "skills-2025-10-02",
    "fast-mode-2026-02-01", "user-profiles-2026-03-24",
    "user-profiles-2026-08-18", "advisor-tool-2026-03-01",
    "managed-agents-2026-04-01", "agent-memory-2026-07-22",
    "cache-diagnosis-2026-04-07", "dreaming-2026-04-21",
    "thinking-token-count-2026-05-13", "thinking-display-updates-2026-08-18",
    "server-side-fallback-2026-06-01", "server-side-fallback-2026-07-01",
    "fallback-credit-2026-06-01", "fallback-credit-2026-07-01",
    "mid-conversation-tool-changes-2026-07-01", "compact-2026-01-12",
    "structured-outputs-2025-11-13", "task-budgets-2026-03-13",
    "ce-user-management-2026-07-13",
)

# Endpoint-scoped betas that are not freely combinable. On memory store
# endpoints the first replaces the second and sending both returns 400.
CONFLICTS = (("agent-memory-2026-07-22", "managed-agents-2026-04-01"),)

# The two listings this script can read with a workspace key. Both are GETs and
# both are free. They are the entire evidence base for the shape comparison,
# which is why "no difference here" is reported as a limit and not as health.
DIFF_PATHS = ("/models", "/files")

FINDINGS = ("rejected-typo", "rejected-unknown", "pinned-to-beta-shape",
            "conflicting-pair", "malformed-header")


def split_betas(raw):
    """(names, faults) from one anthropic-beta header value. Pure.

    Multiple betas travel in one comma-separated header, so the string itself
    can be wrong in ways that have nothing to do with spelling: a trailing
    comma leaves an empty segment, a duplicate is silently pointless, and an
    embedded space is not part of any documented name.
    """
    names = []
    faults = []
    seen = set()
    for segment in str(raw or "").split(","):
        piece = segment.strip()
        if not piece:
            if segment or str(raw or "").count(","):
                faults.append("an empty segment, usually a trailing comma")
            continue
        if piece != piece.lower():
            faults.append("%r is not lower case; beta names are exact" % piece)
            piece = piece.lower()
        if " " in piece or "\\t" in piece:
            faults.append("%r contains whitespace inside the name" % piece)
        if piece in seen:
            faults.append("%r is listed more than once" % piece)
            continue
        seen.add(piece)
        names.append(piece)
    # De-duplicated, order preserved, so the printed report is stable.
    return (tuple(names), tuple(dict.fromkeys(faults)))


def load_call_sites(raw):
    """{call site: raw header value}. Pure. Accepts JSON, a list or a string.

    Config lives in different shapes in different repositories and none of them
    is worth an argument, so all three are read and a value that cannot be
    parsed becomes one anonymous call site rather than an exception.
    """
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except ValueError:
        return {"(declared)": text}
    if isinstance(parsed, dict):
        return {str(k): str(v) for k, v in parsed.items()}
    if isinstance(parsed, list):
        return {"(declared)": ",".join(str(v) for v in parsed)}
    return {"(declared)": str(parsed)}


def levenshtein(a, b):
    """Edit distance between two strings. Pure.

    Written out rather than imported so the Python and Node.js versions rank
    candidates identically. A suggestion that differs between the two scripts
    is a suggestion nobody trusts.
    """
    a, b = str(a or ""), str(b or "")
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(previous[j] + 1,
                               current[j - 1] + 1,
                               previous[j - 1] + (0 if ca == cb else 1)))
        previous = current
    return previous[-1]


def near_matches(name, known=KNOWN_BETAS, limit=3, max_distance=6):
    """The closest documented names to a rejected string. Pure.

    Sorted by distance then alphabetically so the output does not reshuffle
    between runs. Empty when nothing is close, because a list of unrelated beta
    names is worse than no suggestion at all.
    """
    scored = []
    for candidate in known or ():
        distance = levenshtein(name, candidate)
        if distance <= max_distance:
            scored.append((distance, candidate))
    scored.sort()
    return tuple(candidate for _, candidate in scored[:limit])


def classify_probe(name, status, known=KNOWN_BETAS):
    """What one probe of one beta name means. Pure. Returns (state, detail).

    The 400 is deliberately not resolved into one cause. An invalid name and a
    beta this organization is not entitled to return the same documented
    message, and picking one would be an invention.
    """
    if status is None:
        return ("unreachable", "no response, so this name was not graded")
    status = int(status)
    documented = name in set(known or ())
    if status == 200:
        if documented:
            return ("accepted", "200, and the published enum lists it")
        return ("accepted-undocumented",
                "200, but the published enum does not list it. The endpoint "
                "accepts it, so the list is behind rather than the header "
                "being wrong")
    if status == 400:
        return ("rejected-typo" if near_matches(name, known) else "rejected-unknown",
                "400. Invalid, or a beta this organization is not entitled to; "
                "the API returns the same message for both")
    if status in (401, 403):
        return ("credentials",
                "%d, which is the key rather than the beta name" % status)
    return ("unexpected", "%d" % status)


def key_sets(payload):
    """(top-level keys, keys on the first data item). Pure.

    Two granularities because the documented graduation differences live at
    both: pagination cursors move at the top level, and expires_at appears on
    the individual objects.
    """
    body = payload if isinstance(payload, dict) else {}
    top = tuple(sorted(str(k) for k in body.keys()))
    data = body.get("data")
    first = data[0] if isinstance(data, list) and data else None
    item = tuple(sorted(str(k) for k in first.keys())) if isinstance(first, dict) else ()
    return (top, item)


def shape_delta(with_header, without_header):
    """Which keys differ between two bodies. Pure.

    {"top": (only_with, only_without), "item": (only_with, only_without)}.
    Sets rather than a diff of values: a beta header changes which fields exist,
    and comparing values would report every id and timestamp as a difference.
    """
    w_top, w_item = key_sets(with_header)
    n_top, n_item = key_sets(without_header)
    return {
        "top": (tuple(sorted(set(w_top) - set(n_top))),
                tuple(sorted(set(n_top) - set(w_top)))),
        "item": (tuple(sorted(set(w_item) - set(n_item))),
                 tuple(sorted(set(n_item) - set(w_item)))),
    }


def graduation_verdict(name, deltas):
    """Grade one accepted name by response shape. Pure. Returns (state, detail).

    deltas: {path: shape_delta(...)}. An identical pair is reported as a limit
    of the test rather than as a clean bill of health, because only some betas
    change a readable GET and this script can read exactly two of them.
    """
    changed = []
    for path in sorted(deltas or {}):
        delta = (deltas or {})[path] or {}
        if any(delta.get(scope, ((), ()))[side]
               for scope in ("top", "item") for side in (0, 1)):
            changed.append(path)
    if changed:
        return ("pinned-to-beta-shape",
                "accepted, and the response differs with and without it on: "
                + ", ".join(changed))
    return ("no-visible-difference",
            "same keys with and without it on the endpoints this script can "
            "read, which is not evidence that the header does nothing")


def conflicting(names):
    """[(a, b)] documented pairs present together. Pure."""
    have = set(str(n).strip().lower() for n in names or ())
    return [pair for pair in CONFLICTS if have.issuperset(pair)]


def repair_lines(state, name=None, matches=(), deltas=None):
    """The repair for one verdict. Pure. Printed, never performed."""
    if state == "rejected-typo":
        return ["replace it with %s, then re-run this probe."
                % (matches[0] if matches else "the documented name"),
                "if the spelling is already exact, the other cause is "
                "entitlement: the same 400 is returned for a beta this "
                "organization does not have access to."]
    if state == "rejected-unknown":
        return ["nothing in the published enum is close to %r. Read the beta "
                "headers reference for the current name, and check entitlement "
                "before assuming it is a typo." % str(name)]
    if state == "pinned-to-beta-shape":
        lines = ["the beta graduated. The header is optional now and it is not "
                 "inert: it holds this client on the response shape it shipped "
                 "with. Read the migration notes before dropping it."]
        for path in sorted(deltas or {}):
            delta = (deltas or {})[path] or {}
            only_with, only_without = delta.get("top", ((), ()))
            if only_with:
                lines.append("%s top-level keys only with the header: %s"
                             % (path, ", ".join(only_with)))
            if only_without:
                lines.append("%s top-level keys only without it: %s"
                             % (path, ", ".join(only_without)))
            i_with, i_without = delta.get("item", ((), ()))
            if i_with:
                lines.append("%s item keys only with the header: %s"
                             % (path, ", ".join(i_with)))
            if i_without:
                lines.append("%s item keys only without it: %s"
                             % (path, ", ".join(i_without)))
        return lines
    if state == "conflicting-pair":
        return ["on memory store endpoints the first replaces the second. "
                "Sending both returns 400. Send agent-memory-2026-07-22 alone "
                "there and keep managed-agents-2026-04-01 for the agent, "
                "session and environment endpoints."]
    if state == "malformed-header":
        return ["multiple betas go in one comma separated header. Rebuild the "
                "string from a list rather than concatenating, and note that "
                "repeating a --beta flag on the CLI keeps only the first."]
    return []


def get(session, path, headers=None, params=None, timeout=60):
    """One GET. Returns (status, parsed body or None). Never raises on a 4xx.

    A 400 is the expected answer to half the probes here and is the most
    informative result the script can get, so it is data rather than an error.
    """
    try:
        r = session.get(API + path, headers=headers or {},
                        params=params or {}, timeout=timeout)
    except requests.RequestException as exc:
        log.debug("GET %s failed: %s", path, exc)
        return (None, None)
    try:
        return (r.status_code, r.json())
    except ValueError:
        return (r.status_code, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--beta", action="append", default=[],
                    help="a beta name your code sends (repeatable)")
    ap.add_argument("--skip-shape-diff", action="store_true",
                    help="probe validity only and do not compare responses")
    args = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        log.error("set ANTHROPIC_API_KEY to a workspace key. This script only "
                  "issues GET requests")
        return 2

    call_sites = load_call_sites(os.environ.get("ANTHROPIC_BETA_HEADERS"))
    if args.beta:
        call_sites.setdefault("(command line)", ",".join(args.beta))
    if not call_sites:
        log.error("nothing to grade. Set ANTHROPIC_BETA_HEADERS to a JSON map "
                  "of call site to header value, or pass --beta")
        return 2

    session = requests.Session()
    session.headers.update({"x-api-key": key, "anthropic-version": VERSION})

    findings = 0
    distinct = []
    for site in sorted(call_sites):
        names, faults = split_betas(call_sites[site])
        for name in names:
            if name not in distinct:
                distinct.append(name)
        for fault in faults:
            log.warning("%-20s %s sends %s", "malformed-header", site, fault)
            findings += 1
        if faults:
            for line in repair_lines("malformed-header"):
                log.warning("  repair: %s", line)
        for pair in conflicting(names):
            log.warning("%-20s %s sends %s with %s", "conflicting-pair", site,
                        pair[0], pair[1])
            for line in repair_lines("conflicting-pair"):
                log.warning("  repair: %s", line)
            findings += 1

    log.info("%d distinct beta string(s) across %d call site(s)",
             len(distinct), len(call_sites))

    for name in distinct:
        status, _ = get(session, "/models",
                        headers={"anthropic-beta": name}, params={"limit": 1})
        state, detail = classify_probe(name, status)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-20s %s: %s", state, name, detail)
        matches = near_matches(name) if state.startswith("rejected") else ()
        if matches:
            emit("  closest documented names: %s", ", ".join(matches))
        for line in repair_lines(state, name, matches):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1
            continue
        if state not in ("accepted", "accepted-undocumented") or args.skip_shape_diff:
            continue

        deltas = {}
        for path in DIFF_PATHS:
            with_status, with_body = get(session, path,
                                         headers={"anthropic-beta": name},
                                         params={"limit": 1})
            without_status, without_body = get(session, path, params={"limit": 1})
            if with_status != 200 or without_status != 200:
                continue
            deltas[path] = shape_delta(with_body, without_body)
        if not deltas:
            log.info("  neither listing was readable, so no shape comparison "
                     "was made for this name")
            continue
        state, detail = graduation_verdict(name, deltas)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-20s %s: %s", state, name, detail)
        for line in repair_lines(state, name, (), deltas):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "anthropic-beta-header-audit.mjs",
"js": '''/**
 * Grade every anthropic-beta string your code sends, without sending one.
 *
 * Read only. Every request is a GET: /v1/models to validate a name, and the
 * two readable listings twice each to compare a response with and without a
 * header. No request body is constructed and nothing is generated or billed.
 *
 * A 200 proves the name is recognised by the request layer. It is not evidence
 * that the beta still does anything on /v1/messages, and nothing here says so.
 */
const API = 'https://api.anthropic.com/v1';
const VERSION = '2023-06-01';

// A dictionary for near-matching a rejected string, never a verdict. The probe
// is the authority; a document lags.
export const KNOWN_BETAS = [
  'message-batches-2024-09-24', 'prompt-caching-2024-07-31',
  'computer-use-2024-10-22', 'computer-use-2025-01-24',
  'computer-use-2025-11-24', 'pdfs-2024-09-25',
  'token-counting-2024-11-01', 'token-efficient-tools-2025-02-19',
  'output-128k-2025-02-19', 'output-300k-2026-03-24',
  'files-api-2025-04-14', 'mcp-client-2025-04-04', 'mcp-client-2025-11-20',
  'mcp-tunnels-2026-06-22', 'dev-full-thinking-2025-05-14',
  'interleaved-thinking-2025-05-14', 'code-execution-2025-05-22',
  'extended-cache-ttl-2025-04-11', 'context-1m-2025-08-07',
  'context-management-2025-06-27',
  'model-context-window-exceeded-2025-08-26', 'skills-2025-10-02',
  'fast-mode-2026-02-01', 'user-profiles-2026-03-24',
  'user-profiles-2026-08-18', 'advisor-tool-2026-03-01',
  'managed-agents-2026-04-01', 'agent-memory-2026-07-22',
  'cache-diagnosis-2026-04-07', 'dreaming-2026-04-21',
  'thinking-token-count-2026-05-13', 'thinking-display-updates-2026-08-18',
  'server-side-fallback-2026-06-01', 'server-side-fallback-2026-07-01',
  'fallback-credit-2026-06-01', 'fallback-credit-2026-07-01',
  'mid-conversation-tool-changes-2026-07-01', 'compact-2026-01-12',
  'structured-outputs-2025-11-13', 'task-budgets-2026-03-13',
  'ce-user-management-2026-07-13',
];

// On memory store endpoints the first replaces the second; both is a 400.
export const CONFLICTS = [['agent-memory-2026-07-22', 'managed-agents-2026-04-01']];

const DIFF_PATHS = ['/models', '/files'];

const FINDINGS = new Set(['rejected-typo', 'rejected-unknown',
  'pinned-to-beta-shape', 'conflicting-pair', 'malformed-header']);

/** [names, faults] from one anthropic-beta header value. Pure. */
export function splitBetas(raw) {
  const names = [];
  const faults = [];
  const seen = new Set();
  const text = String(raw ?? '');
  for (const segment of text.split(',')) {
    let piece = segment.trim();
    if (!piece) {
      if (segment || text.includes(',')) {
        faults.push('an empty segment, usually a trailing comma');
      }
      continue;
    }
    if (piece !== piece.toLowerCase()) {
      faults.push(`'${piece}' is not lower case; beta names are exact`);
      piece = piece.toLowerCase();
    }
    if (piece.includes(' ') || piece.includes('\\t')) {
      faults.push(`'${piece}' contains whitespace inside the name`);
    }
    if (seen.has(piece)) {
      faults.push(`'${piece}' is listed more than once`);
      continue;
    }
    seen.add(piece);
    names.push(piece);
  }
  return [names, [...new Set(faults)]];
}

/** {call site: raw header value}. Pure. Accepts JSON, a list or a string. */
export function loadCallSites(raw) {
  const text = String(raw ?? '').trim();
  if (!text) return {};
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    return { '(declared)': text };
  }
  if (Array.isArray(parsed)) return { '(declared)': parsed.map(String).join(',') };
  if (parsed && typeof parsed === 'object') {
    return Object.fromEntries(Object.entries(parsed).map(([k, v]) => [String(k), String(v)]));
  }
  return { '(declared)': String(parsed) };
}

/** Edit distance between two strings. Pure. Written out to match the Python. */
export function levenshtein(a, b) {
  const x = String(a ?? '');
  const y = String(b ?? '');
  if (x === y) return 0;
  if (!x.length) return y.length;
  if (!y.length) return x.length;
  let previous = Array.from({ length: y.length + 1 }, (_, i) => i);
  for (let i = 1; i <= x.length; i += 1) {
    const current = [i];
    for (let j = 1; j <= y.length; j += 1) {
      current.push(Math.min(previous[j] + 1, current[j - 1] + 1,
                            previous[j - 1] + (x[i - 1] === y[j - 1] ? 0 : 1)));
    }
    previous = current;
  }
  return previous[y.length];
}

/** The closest documented names to a rejected string. Pure. */
export function nearMatches(name, known = KNOWN_BETAS, limit = 3, maxDistance = 6) {
  const scored = [];
  for (const candidate of known ?? []) {
    const distance = levenshtein(name, candidate);
    if (distance <= maxDistance) scored.push([distance, candidate]);
  }
  scored.sort((a, b) => (a[0] - b[0]) || a[1].localeCompare(b[1]));
  return scored.slice(0, limit).map(([, candidate]) => candidate);
}

/** What one probe of one beta name means. Pure. Returns [state, detail]. */
export function classifyProbe(name, status, known = KNOWN_BETAS) {
  if (status === null || status === undefined) {
    return ['unreachable', 'no response, so this name was not graded'];
  }
  const code = Math.trunc(Number(status));
  const documented = (known ?? []).includes(name);
  if (code === 200) {
    if (documented) return ['accepted', '200, and the published enum lists it'];
    return ['accepted-undocumented',
      '200, but the published enum does not list it. The endpoint accepts it, '
      + 'so the list is behind rather than the header being wrong'];
  }
  if (code === 400) {
    return [nearMatches(name, known).length ? 'rejected-typo' : 'rejected-unknown',
      '400. Invalid, or a beta this organization is not entitled to; the API '
      + 'returns the same message for both'];
  }
  if (code === 401 || code === 403) {
    return ['credentials', `${code}, which is the key rather than the beta name`];
  }
  return ['unexpected', `${code}`];
}

/** [top-level keys, keys on the first data item]. Pure. */
export function keySets(payload) {
  const body = (payload && typeof payload === 'object' && !Array.isArray(payload))
    ? payload : {};
  const top = Object.keys(body).map(String).sort();
  const data = body.data;
  const first = Array.isArray(data) && data.length ? data[0] : null;
  const item = (first && typeof first === 'object')
    ? Object.keys(first).map(String).sort() : [];
  return [top, item];
}

/** Which keys differ between two bodies. Pure. */
export function shapeDelta(withHeader, withoutHeader) {
  const [wTop, wItem] = keySets(withHeader);
  const [nTop, nItem] = keySets(withoutHeader);
  const only = (a, b) => a.filter((k) => !b.includes(k)).sort();
  return {
    top: [only(wTop, nTop), only(nTop, wTop)],
    item: [only(wItem, nItem), only(nItem, wItem)],
  };
}

/** Grade one accepted name by response shape. Pure. Returns [state, detail]. */
export function graduationVerdict(name, deltas) {
  const changed = [];
  for (const path of Object.keys(deltas ?? {}).sort()) {
    const delta = (deltas ?? {})[path] ?? {};
    const groups = [delta.top ?? [[], []], delta.item ?? [[], []]];
    if (groups.some((g) => g.some((side) => (side ?? []).length))) changed.push(path);
  }
  if (changed.length) {
    return ['pinned-to-beta-shape',
      'accepted, and the response differs with and without it on: ' + changed.join(', ')];
  }
  return ['no-visible-difference',
    'same keys with and without it on the endpoints this script can read, which '
    + 'is not evidence that the header does nothing'];
}

/** [[a, b]] documented pairs present together. Pure. */
export function conflicting(names) {
  const have = new Set((names ?? []).map((n) => String(n).trim().toLowerCase()));
  return CONFLICTS.filter((pair) => pair.every((n) => have.has(n)));
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, name = null, matches = [], deltas = null) {
  if (state === 'rejected-typo') {
    return [`replace it with ${matches[0] ?? 'the documented name'}, then re-run this probe.`,
      'if the spelling is already exact, the other cause is entitlement: the '
      + 'same 400 is returned for a beta this organization does not have access to.'];
  }
  if (state === 'rejected-unknown') {
    return [`nothing in the published enum is close to '${name}'. Read the beta `
      + 'headers reference for the current name, and check entitlement before '
      + 'assuming it is a typo.'];
  }
  if (state === 'pinned-to-beta-shape') {
    const lines = ['the beta graduated. The header is optional now and it is not '
      + 'inert: it holds this client on the response shape it shipped with. Read '
      + 'the migration notes before dropping it.'];
    for (const path of Object.keys(deltas ?? {}).sort()) {
      const delta = (deltas ?? {})[path] ?? {};
      const [onlyWith, onlyWithout] = delta.top ?? [[], []];
      if (onlyWith.length) lines.push(`${path} top-level keys only with the header: ${onlyWith.join(', ')}`);
      if (onlyWithout.length) lines.push(`${path} top-level keys only without it: ${onlyWithout.join(', ')}`);
      const [iWith, iWithout] = delta.item ?? [[], []];
      if (iWith.length) lines.push(`${path} item keys only with the header: ${iWith.join(', ')}`);
      if (iWithout.length) lines.push(`${path} item keys only without it: ${iWithout.join(', ')}`);
    }
    return lines;
  }
  if (state === 'conflicting-pair') {
    return ['on memory store endpoints the first replaces the second. Sending '
      + 'both returns 400. Send agent-memory-2026-07-22 alone there and keep '
      + 'managed-agents-2026-04-01 for the agent, session and environment endpoints.'];
  }
  if (state === 'malformed-header') {
    return ['multiple betas go in one comma separated header. Rebuild the string '
      + 'from a list rather than concatenating, and note that repeating a --beta '
      + 'flag on the CLI keeps only the first.'];
  }
  return [];
}

async function read(key, path, beta, params = { limit: 1 }) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const headers = { 'x-api-key': key, 'anthropic-version': VERSION };
  if (beta) headers['anthropic-beta'] = beta;
  try {
    const r = await fetch(url, { headers });
    let body = null;
    try { body = await r.json(); } catch { body = null; }
    return [r.status, body];
  } catch {
    return [null, null];
  }
}

async function main() {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    console.error('set ANTHROPIC_API_KEY to a workspace key. This script only '
                  + 'issues GET requests');
    process.exitCode = 2;
    return;
  }
  const callSites = loadCallSites(process.env.ANTHROPIC_BETA_HEADERS);
  if (!Object.keys(callSites).length) {
    console.error('nothing to grade. Set ANTHROPIC_BETA_HEADERS to a JSON map of '
                  + 'call site to header value');
    process.exitCode = 2;
    return;
  }

  let findings = 0;
  const distinct = [];
  for (const site of Object.keys(callSites).sort()) {
    const [names, faults] = splitBetas(callSites[site]);
    for (const name of names) if (!distinct.includes(name)) distinct.push(name);
    for (const fault of faults) {
      console.log(`${'malformed-header'.padEnd(20)} ${site} sends ${fault}`);
      findings += 1;
    }
    if (faults.length) {
      for (const line of repairLines('malformed-header')) console.log(`  repair: ${line}`);
    }
    for (const pair of conflicting(names)) {
      console.log(`${'conflicting-pair'.padEnd(20)} ${site} sends ${pair[0]} with ${pair[1]}`);
      for (const line of repairLines('conflicting-pair')) console.log(`  repair: ${line}`);
      findings += 1;
    }
  }

  console.log(`${distinct.length} distinct beta string(s) across `
              + `${Object.keys(callSites).length} call site(s)`);

  for (const name of distinct) {
    const [status] = await read(key, '/models', name);
    const [state, detail] = classifyProbe(name, status);
    console.log(`${state.padEnd(20)} ${name}: ${detail}`);
    const matches = state.startsWith('rejected') ? nearMatches(name) : [];
    if (matches.length) console.log(`  closest documented names: ${matches.join(', ')}`);
    for (const line of repairLines(state, name, matches)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) { findings += 1; continue; }
    if (state !== 'accepted' && state !== 'accepted-undocumented') continue;

    const deltas = {};
    for (const path of DIFF_PATHS) {
      const [withStatus, withBody] = await read(key, path, name);
      const [withoutStatus, withoutBody] = await read(key, path, null);
      if (withStatus !== 200 || withoutStatus !== 200) continue;
      deltas[path] = shapeDelta(withBody, withoutBody);
    }
    if (!Object.keys(deltas).length) {
      console.log('  neither listing was readable, so no shape comparison was '
                  + 'made for this name');
      continue;
    }
    const [gstate, gdetail] = graduationVerdict(name, deltas);
    console.log(`${gstate.padEnd(20)} ${name}: ${gdetail}`);
    for (const line of repairLines(gstate, name, [], deltas)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(gstate)) findings += 1;
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the loud half: a name one letter away from a documented beta comes back rejected and carries the correct suggestion, and the same rejection also states the entitlement possibility, because the API returns one message for two causes. The second is the quiet half, built from the documented Files API migration table &mdash; <code>has_more</code>/<code>first_id</code>/<code>last_id</code> with the header, <code>next_page</code> and <code>expires_at</code> without it &mdash; and it has to come back as a finding naming those exact keys. The third is the one that keeps the script honest: two identical bodies must produce <code>no-visible-difference</code> and must not be a finding, with a detail line saying the test could not tell rather than that the header is fine. Then the enum lagging behind the endpoint, the structural faults in a comma-separated header, and the one documented pair that must not travel together.",
"test_py_file": "test_anthropic_beta_header_audit.py",
"test_py": '''from anthropic_beta_header_audit import (classify_probe, conflicting,
                                          graduation_verdict, key_sets,
                                          levenshtein, load_call_sites,
                                          near_matches, repair_lines,
                                          shape_delta, split_betas)


def files_listing(beta):
    """The documented Files API shapes, with and without files-api-2025-04-14."""
    if beta:
        return {"data": [{"id": "file_01", "type": "file", "size_bytes": 12}],
                "has_more": False, "first_id": "file_01", "last_id": "file_01"}
    return {"data": [{"id": "file_01", "type": "file", "size_bytes": 12,
                      "expires_at": None}],
            "next_page": None}


def test_a_misspelled_beta_is_rejected_and_the_suggestion_is_the_repair():
    state, detail = classify_probe("contxt-1m-2025-08-07", 400)
    assert state == "rejected-typo"
    # One message, two causes, and the script refuses to pick between them.
    assert "not entitled to" in detail
    matches = near_matches("contxt-1m-2025-08-07")
    assert matches[0] == "context-1m-2025-08-07"
    lines = repair_lines(state, "contxt-1m-2025-08-07", matches)
    assert any("context-1m-2025-08-07" in line for line in lines)
    assert any("entitlement" in line for line in lines)


def test_a_graduated_beta_returns_200_and_pins_the_older_shape():
    # The documented Files API migration table, asserted as a diff.
    deltas = {"/files": shape_delta(files_listing(True), files_listing(False))}
    state, detail = graduation_verdict("files-api-2025-04-14", deltas)
    assert state == "pinned-to-beta-shape"
    assert "/files" in detail
    assert deltas["/files"]["top"][0] == ("first_id", "has_more", "last_id")
    assert deltas["/files"]["top"][1] == ("next_page",)
    assert deltas["/files"]["item"][1] == ("expires_at",)
    lines = repair_lines(state, "files-api-2025-04-14", (), deltas)
    assert any("expires_at" in line for line in lines)
    assert any("graduated" in line for line in lines)


def test_identical_bodies_prove_nothing_and_are_not_a_finding():
    same = {"data": [{"id": "m1"}], "has_more": False}
    deltas = {"/models": shape_delta(same, same)}
    state, detail = graduation_verdict("context-management-2025-06-27", deltas)
    assert state == "no-visible-difference"
    assert "not evidence that the header does nothing" in detail
    assert repair_lines(state) == []


def test_the_published_enum_is_a_dictionary_and_not_the_verdict():
    state, detail = classify_probe("brand-new-beta-2026-09-01", 200)
    assert state == "accepted-undocumented"
    assert "the list is behind" in detail
    assert classify_probe("files-api-2025-04-14", 200)[0] == "accepted"
    assert near_matches("nothing-like-a-beta-name") == ()
    assert classify_probe("nothing-like-a-beta-name", 400)[0] == "rejected-unknown"
    assert levenshtein("abc", "abc") == 0 and levenshtein("", "abc") == 3


def test_the_header_is_one_string_carrying_a_list_so_it_can_be_malformed():
    names, faults = split_betas("files-api-2025-04-14, skills-2025-10-02,")
    assert names == ("files-api-2025-04-14", "skills-2025-10-02")
    assert any("trailing comma" in f for f in faults)

    names, faults = split_betas("Skills-2025-10-02,skills-2025-10-02")
    assert names == ("skills-2025-10-02",)
    assert any("lower case" in f for f in faults)
    assert any("more than once" in f for f in faults)

    names, faults = split_betas("files api 2025-04-14")
    assert any("whitespace inside" in f for f in list(names) + list(faults))
    assert any("comma separated" in line
               for line in repair_lines("malformed-header"))


def test_the_documented_conflicting_pair_needs_no_request_at_all():
    assert conflicting(["agent-memory-2026-07-22",
                        "managed-agents-2026-04-01"]) == [
        ("agent-memory-2026-07-22", "managed-agents-2026-04-01")]
    assert conflicting(["managed-agents-2026-04-01"]) == []
    assert any("replaces the second" in line
               for line in repair_lines("conflicting-pair"))


def test_input_and_bodies_are_read_in_whatever_shape_they_arrive():
    assert load_call_sites('{"a.py": "x,y"}') == {"a.py": "x,y"}
    assert load_call_sites('["x", "y"]') == {"(declared)": "x,y"}
    assert load_call_sites("x,y") == {"(declared)": "x,y"}
    assert load_call_sites("") == {}
    assert key_sets(None) == ((), ())
    assert key_sets({"data": []}) == (("data",), ())
    assert classify_probe("files-api-2025-04-14", None)[0] == "unreachable"
    assert classify_probe("files-api-2025-04-14", 401)[0] == "credentials"
''',
"test_js_file": "anthropic-beta-header-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classifyProbe, conflicting, graduationVerdict, keySets, levenshtein,
         loadCallSites, nearMatches, repairLines, shapeDelta,
         splitBetas } from './anthropic-beta-header-audit.mjs';

const filesListing = (beta) => (beta
  ? { data: [{ id: 'file_01', type: 'file', size_bytes: 12 }],
      has_more: false, first_id: 'file_01', last_id: 'file_01' }
  : { data: [{ id: 'file_01', type: 'file', size_bytes: 12, expires_at: null }],
      next_page: null });

test('a misspelled beta is rejected and the suggestion is the repair', () => {
  const [state, detail] = classifyProbe('contxt-1m-2025-08-07', 400);
  assert.equal(state, 'rejected-typo');
  assert.ok(detail.includes('not entitled to'));
  const matches = nearMatches('contxt-1m-2025-08-07');
  assert.equal(matches[0], 'context-1m-2025-08-07');
  const lines = repairLines(state, 'contxt-1m-2025-08-07', matches);
  assert.ok(lines.some((l) => l.includes('context-1m-2025-08-07')));
  assert.ok(lines.some((l) => l.includes('entitlement')));
});

test('a graduated beta returns 200 and pins the older shape', () => {
  const deltas = { '/files': shapeDelta(filesListing(true), filesListing(false)) };
  const [state, detail] = graduationVerdict('files-api-2025-04-14', deltas);
  assert.equal(state, 'pinned-to-beta-shape');
  assert.ok(detail.includes('/files'));
  assert.deepEqual(deltas['/files'].top[0], ['first_id', 'has_more', 'last_id']);
  assert.deepEqual(deltas['/files'].top[1], ['next_page']);
  assert.deepEqual(deltas['/files'].item[1], ['expires_at']);
  const lines = repairLines(state, 'files-api-2025-04-14', [], deltas);
  assert.ok(lines.some((l) => l.includes('expires_at')));
  assert.ok(lines.some((l) => l.includes('graduated')));
});

test('identical bodies prove nothing and are not a finding', () => {
  const same = { data: [{ id: 'm1' }], has_more: false };
  const deltas = { '/models': shapeDelta(same, same) };
  const [state, detail] = graduationVerdict('context-management-2025-06-27', deltas);
  assert.equal(state, 'no-visible-difference');
  assert.ok(detail.includes('not evidence that the header does nothing'));
  assert.deepEqual(repairLines(state), []);
});

test('the published enum is a dictionary and not the verdict', () => {
  const [state, detail] = classifyProbe('brand-new-beta-2026-09-01', 200);
  assert.equal(state, 'accepted-undocumented');
  assert.ok(detail.includes('the list is behind'));
  assert.equal(classifyProbe('files-api-2025-04-14', 200)[0], 'accepted');
  assert.deepEqual(nearMatches('nothing-like-a-beta-name'), []);
  assert.equal(classifyProbe('nothing-like-a-beta-name', 400)[0], 'rejected-unknown');
  assert.equal(levenshtein('abc', 'abc'), 0);
  assert.equal(levenshtein('', 'abc'), 3);
});

test('the header is one string carrying a list so it can be malformed', () => {
  let [names, faults] = splitBetas('files-api-2025-04-14, skills-2025-10-02,');
  assert.deepEqual(names, ['files-api-2025-04-14', 'skills-2025-10-02']);
  assert.ok(faults.some((f) => f.includes('trailing comma')));

  [names, faults] = splitBetas('Skills-2025-10-02,skills-2025-10-02');
  assert.deepEqual(names, ['skills-2025-10-02']);
  assert.ok(faults.some((f) => f.includes('lower case')));
  assert.ok(faults.some((f) => f.includes('more than once')));

  [names, faults] = splitBetas('files api 2025-04-14');
  assert.ok([...names, ...faults].some((f) => f.includes('whitespace inside')));
  assert.ok(repairLines('malformed-header').some((l) => l.includes('comma separated')));
});

test('the documented conflicting pair needs no request at all', () => {
  assert.deepEqual(conflicting(['agent-memory-2026-07-22', 'managed-agents-2026-04-01']),
                   [['agent-memory-2026-07-22', 'managed-agents-2026-04-01']]);
  assert.deepEqual(conflicting(['managed-agents-2026-04-01']), []);
  assert.ok(repairLines('conflicting-pair').some((l) => l.includes('replaces the second')));
});

test('input and bodies are read in whatever shape they arrive', () => {
  assert.deepEqual(loadCallSites('{"a.py": "x,y"}'), { 'a.py': 'x,y' });
  assert.deepEqual(loadCallSites('["x", "y"]'), { '(declared)': 'x,y' });
  assert.deepEqual(loadCallSites('x,y'), { '(declared)': 'x,y' });
  assert.deepEqual(loadCallSites(''), {});
  assert.deepEqual(keySets(null), [[], []]);
  assert.deepEqual(keySets({ data: [] }), [['data'], []]);
  assert.equal(classifyProbe('files-api-2025-04-14', null)[0], 'unreachable');
  assert.equal(classifyProbe('files-api-2025-04-14', 401)[0], 'credentials');
});
''',
"faq": [
 ("A beta name that 400s: is it a typo or a permissions problem?",
  "The API cannot tell you, and neither can this script. The documented response for an unrecognised beta name and for a beta your organization is not entitled to is the same message: Unexpected value(s) for the anthropic-beta header. So the output says both, in one line, and adds the closest documented names when there are any. In practice the near-match resolves it most of the time, because a rejected string one character away from a real beta is a typo and a rejected string with nothing near it is usually an entitlement question for your account team."),
 ("How is this different from the note about the obsolete 1M context beta?",
  "That note is about a context window, this one is about a header string, and the boundary is a sentence that note gets right: a 200 from GET /v1/models with a beta header proves the name is recognised and proves nothing about what the beta does on /v1/messages. So it refuses to probe, reads max_input_tokens off the model object instead, and grades your enforced ceiling. This note takes the half that a probe genuinely answers, which is validity, plus one that a pair of probes answers, which is whether the header still changes the shape of a response. Neither script claims the other's evidence."),
 ("Why does an accepted beta header need checking at all?",
  "Because acceptance and necessity are different things. Betas graduate, and when they do the header becomes optional but not inert: requests that still send it keep receiving the pre-GA response shape. The Files API graduation is documented as a table of exactly these differences, and the effect on a client that never dropped the header is concrete rather than theoretical. It gets has_more, first_id and last_id instead of next_page, it cannot use the ids[] filter, and it never sees expires_at, which means expiry handling it does not know it is missing."),
 ("What does 'no visible difference' actually mean in the output?",
  "That the two endpoints this script can safely read returned the same keys with and without the header. It is a statement about the test, not about the header. Only some betas change a readable GET, most of them change behaviour on /v1/messages instead, and a script that never sends a message cannot see those. Reporting that as healthy would be the same error as treating a 200 as proof of effect, so the state is named for what it is and is not counted as a finding either way."),
 ("Can the script find the beta strings in my code for me?",
  "No, and that is a scope decision rather than a limitation of effort. Nothing in either API returns the headers of requests you have already sent, and this section's scripts read APIs rather than source trees. So the strings are declared as input, per call site, and the per-call-site part earns its keep twice: the malformed-string checks and the conflicting-pair check are both properties of one header value, and a flattened set of names loses both of them."),
],
"related": [REL_VERSION, REL_1M, REL_RETIRED],
"citations": [CITE_BETA, CITE_MODELS_LIST, CITE_FILES, CITE_ERRORS],
},
{
"slug": "org-verification-required",
"title": "Model visible, streaming refused: the org is unverified",
"description": "The model resolves 200 while one key on it bills requests with zero tokens and a sibling key does not. That pairing is verification rather than access.",
"h1": "Model visible, streaming refused: the org is unverified",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Admin read key", "Python and Node.js", "Tests included"],
"keywords": ["openai organization must be verified to stream this model",
             "unsupported_value param stream verification",
             "openai verify organization reasoning summary",
             "openai usage num_model_requests zero output tokens",
             "openai model 404 must be verified to use the model"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_ADMIN_KEY, an organization admin key provisioned read-only, for the usage report. Optionally OPENAI_API_KEY, a project key set to Read Only, for one model lookup per id.",
"lead": "The nightly summarisation job is fine. The evaluation suite is fine. CI is fine. The chat panel in the product returns nothing at all, and has since the release that switched it to the newer model, and the only thing anyone can say about it is that it used to work. The model id is right &mdash; you checked, it resolves. The key is right &mdash; it is the same key the job uses. The difference between the route that works and the route that does not is one field in the request body, <code>\"stream\": true</code>, and the reason it fails has nothing to do with your code at all.",
"short_answer": """<p>Compare two keys on one model, not one model against itself. With an <strong>organization admin key</strong>: <code>GET /v1/organization/usage/completions?start_time={now-24h}&amp;bucket_width=1h&amp;group_by[]=model&amp;group_by[]=api_key_id</code>. Fold the buckets per model and look for the shape where <strong>one key shows <code>num_model_requests</code> above zero with no tokens either side, while another key on the same model in the same window produces output normally</strong>.</p>
<p>That contrast is the whole note. Requests billed with nothing generated means calls rejected on validation before they reached the model, and there are several reasons for that &mdash; but a reason that lives in the model, like <a href="/llm/reasoning-model-rejects-max-tokens/">a parameter the model refuses by name</a>, refuses it for every key. A gate on the streaming path does not: the batch key buffers a whole response and is served, the UI key sets <code>stream</code> and is not.</p>
<p>Confirm the model is reachable with a <strong>Read Only project key</strong>: <code>GET /v1/models/{model}</code> returning <code>200</code> proves the id is valid and entitled for that key, which is what separates this from access. If it <code>404</code>s instead, this is not the note &mdash; <a href="/llm/retired-model-id-still-in-code/">that reading belongs to the model-list diff</a>, and the script hands it over by name rather than grading it.</p>
<p>Now the honest part. <strong>No endpoint on the OpenAI API reports whether your organization is verified.</strong> That state lives in Console, the 400 body that would name it is not replayable, and there is no field to read. What this script proves is that a set of requests on one key was rejected before generation while a sibling key on the same model was not. What it infers, and says it is inferring, is the most common cause of exactly that shape: verification is required for streaming and for reasoning summaries on the advanced models, and a non-streaming path is unaffected.</p>
<p>The repair is a link and a stopgap. Verify the organization in Console and allow up to fifteen minutes for it to propagate; meanwhile buffer the affected route with <code>stream</code> unset and drop <code>reasoning.summary</code>, which is gated the same way.</p>""",
"problem": """<p>Organization verification is a gate on capabilities, not on models. The id is in your model list, <code>GET /v1/models/{id}</code> returns it, a plain request against it works, and the platform is in every respect willing to serve you. Then you add <code>\"stream\": true</code> and get a <code>400</code> whose message is a link to a settings page. Reasoning summaries are gated the same way, which means the two features most associated with a responsive product surface are exactly the two that are unavailable.</p>
<p>Because the gate is on the feature and not the credential, it splits your traffic along the least convenient line. Batch jobs buffer. Evaluations buffer. Tests buffer. The only code path that streams is the one a person is sitting in front of, and it is often the only one that was not covered when the model was rolled out. So the failure is discovered by a user, in production, on a route that never appeared in a test run.</p>
<p>Then it disappears into the aggregate. Neither provider exposes a request log, so there is no endpoint that will tell you which requests failed yesterday or why. All that survives of a rejected call is arithmetic: the usage report counts the request and reports no tokens against it, because nothing was generated. One such row among thousands of healthy ones is not something anybody notices, and it looks identical to several other faults that also reject before generation.</p>
<p>The variant worth knowing about is the <code>404</code>. Some models refuse an unverified organization at the model lookup itself, with a message about verification rather than about the id. That is a different symptom with a different first move, and it is indistinguishable from a retired or unentitled id without reading the message body &mdash; which is why the script routes it elsewhere rather than guessing.</p>""",
"why": """<p><strong>The row shape belongs to more than one fault, so the row alone is not a finding.</strong> Requests counted with zero tokens either side is the signature of every rejection that happens before generation. The published note on reasoning models reaching for <code>max_tokens</code> reads exactly this shape and reaches a completely different conclusion. What separates them is not the row, it is the comparison: a parameter a model refuses is refused on every key, and a gate on one route is not. So this script folds by <code>api_key_id</code> within a model and looks for disagreement between keys, which the other one has no reason to do.</p>
<p><strong>When the keys agree, this note is wrong, and it says so by name.</strong> If every key on the model is mute, the fault is a property of the model or of the request body that every caller shares, and the script prints the other note rather than reporting a verification problem it has no evidence for. A diagnostic that only ever confirms itself is worse than no diagnostic.</p>
<p><strong>One key using the model is not evidence of anything and must not be graded as if it were.</strong> Plenty of models are called from exactly one place. With nothing to compare against, the contrast this note depends on does not exist, so the script names the state, says what would resolve it &mdash; route a canary through a second key, or read the setting in Console &mdash; and declines to guess.</p>
<p><strong>Zero output with non-zero input is a different animal and gets its own state.</strong> A request that was rejected before generation bills nothing at all. A request that consumed input and produced no output ran, and stopped, which is a content or a truncation question rather than a rejection. Folding the two together would put a real class of problem behind the wrong repair.</p>
<p><strong>Verification status is not an API field, and pretending otherwise would be the whole failure of this note.</strong> There is no endpoint that returns it. The error body that names it cannot be fetched after the fact. So the output separates what was measured from what is being inferred, in those words, and the inference is offered with its most likely alternative attached rather than as a verdict.</p>
<p><strong>The model lookup is one cheap call and it removes the largest competing explanation.</strong> A <code>200</code> from <code>GET /v1/models/{id}</code> with a project key says the id exists and is reachable for that credential, which rules out retirement and entitlement in a single request. A <code>404</code> says the opposite loudly enough that the script stops and hands the reading to the note that owns the model list.</p>""",
"steps": [
 {"h": "Use an admin-read key for usage and a project key for the lookup",
  "body": """<p><code>OPENAI_ADMIN_KEY</code> is an organization admin key; <code>/v1/organization/*</code> rejects a project key outright. <code>OPENAI_API_KEY</code> is a Read Only project key and is used for nothing except <code>GET /v1/models/{id}</code>. Both are GETs, and the script never constructs a request body.</p>"""},
 {"h": "Read 24 hours of hourly buckets grouped by model and key",
  "body": """<p><code>group_by[]=model&amp;group_by[]=api_key_id</code>. The key dimension is the point: without it the report answers a question about models, and this note is a question about two keys that disagree.</p>"""},
 {"h": "Classify each key on each model",
  "body": """<p>Requests above zero with no tokens either side is <em>mute</em>: rejected before generation. Requests with input and no output is <em>ran and produced nothing</em>, which is a different problem. Anything with output is producing. No requests is idle and is not evidence.</p>"""},
 {"h": "Look for disagreement, not for a threshold",
  "body": """<p>One mute key beside one producing key on the same model is the finding. Every key mute is the parameter note. One key in total is unresolvable, and the script says which of the three it is instead of printing a percentage.</p>"""},
 {"h": "Confirm reachability, then print the repair and the caveat",
  "body": """<p><code>GET /v1/models/{model}</code>. On <code>200</code>, print the verification repair with the fifteen-minute propagation note and the buffering stopgap. On <code>404</code>, print the other note's name. Either way, print the sentence that verification state is not readable through any endpoint.</p>"""},
],
"verify": """<p>After verifying, re-run with the same window and give it fifteen minutes plus an hour, because the buckets are hourly and the propagation is not instant. The mute key should start producing output on the same model. What should <em>not</em> change is the shape of the output for the models where every key was mute: those were never this note, and a run that quietly starts reporting them as verification problems is a run to distrust.</p>
<pre><code class="language-bash">python3 openai_streaming_verification_probe.py --hours 24
# 3 model(s) with traffic in the last 24h
# verification-suspected  gpt-5.6: key_9fA2 billed 1,204 request(s) with no tokens
#                         either side while key_3bQ7 produced 812,004 output
#                         token(s) on the same model in the same window
#   model lookup: 200, so the id resolves for this key and access is not the fault
#   measured: requests on one key were rejected before generation, on a model
#             another key is generating with normally
#   inferred: organization verification, which gates streaming and reasoning
#             summaries. No endpoint reports verification state, so this is the
#             most likely cause and not a reading
#   repair: verify the organization in Console, then allow up to 15 minutes to
#           propagate. One government ID verifies one organization per 90 days.
#   repair: as a stopgap on the affected route only, unset stream and buffer the
#           whole response, and remove reasoning summary requests.
# model-wide-mute         o4-mini: all 3 key(s) with traffic are mute, so this is
#                         a property of the model or the body every caller sends
#   repair: not this note. Read the reasoning-model parameter note: max_tokens,
#           temperature and top_p are refused by name on those families.
# healthy                 gpt-5.1: 4 key(s) with traffic, all producing output
# 1 finding(s)</code></pre>""",
"code_intro": "One paged GET for usage, one GET per model id, and six pure functions. <code>flatten</code>, which walks buckets into rows and coerces every count so a missing field cannot become a string in a comparison; <code>by_model</code>, which sums per model and per key because the same key appears once per hourly bucket; <code>key_state</code>, which separates <em>rejected before generation</em> from <em>ran and produced nothing</em> rather than folding them together; <code>contrast</code>, which is the note itself and looks only for disagreement between keys; <code>verdict</code>, which lets the model lookup override the contrast and hands a 404 to another note by name; and <code>repair_lines</code>, which always prints what was measured next to what is being inferred.",
"py_file": "openai_streaming_verification_probe.py",
"py": '''"""Find a model that one key can list and another key cannot generate with.

Read only. Two GET endpoints: /v1/organization/usage/completions with an admin
read key, and /v1/models/{id} with a Read Only project key. No request body is
ever constructed, and nothing here sends a completion of any kind.

The subject is a contrast, not a row. Requests counted with no tokens either
side means calls rejected before generation, which is the signature of several
different faults. A fault that lives in the model refuses every key; a gate on
one route does not. So this folds usage by api_key_id inside a model and looks
for two keys that disagree.

What cannot be read is stated rather than guessed: no OpenAI endpoint reports
whether an organization is verified, and the 400 body that would name it is not
retrievable after the fact. The script separates the measurement from the
inference in its own output.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("openai_streaming_verification_probe")

API = "https://api.openai.com/v1"

# Only one state here is this note's finding. The others are real states that
# belong to other notes, and they are printed with the other note's name rather
# than folded into a verdict this script has no evidence for.
FINDINGS = ("verification-suspected",)

MEASURED = ("requests on one key were rejected before generation, on a model "
            "another key is generating with normally")
INFERRED = ("organization verification, which gates streaming and reasoning "
            "summaries. No endpoint reports verification state, so this is the "
            "most likely cause and not a reading")


def flatten(buckets):
    """[(model, api_key_id, requests, input_tokens, output_tokens)]. Pure.

    Every count is coerced. A missing field becomes 0 rather than None, because
    the whole note is a comparison between two numbers and a None propagating
    into it would read as silence from a key that was merely unreported.
    """
    rows = []
    for bucket in buckets or []:
        for entry in (bucket or {}).get("results") or []:
            row = entry or {}
            counts = []
            for field in ("num_model_requests", "input_tokens", "output_tokens"):
                try:
                    counts.append(int(row.get(field) or 0))
                except (TypeError, ValueError):
                    counts.append(0)
            rows.append((str(row.get("model") or "(unattributed)"),
                         str(row.get("api_key_id") or "(unattributed)"),
                         counts[0], counts[1], counts[2]))
    return rows


def by_model(rows):
    """{model: {api_key_id: {requests, input, output}}}. Pure.

    Summed, because a key appears once per hourly bucket and the question is
    about a whole window rather than about any one hour in it.
    """
    out = {}
    for model, key_id, requests_n, input_n, output_n in rows or []:
        slot = out.setdefault(model, {}).setdefault(
            key_id, {"requests": 0, "input": 0, "output": 0})
        slot["requests"] += requests_n
        slot["input"] += input_n
        slot["output"] += output_n
    return out


def key_state(row, min_requests=1):
    """What one key did on one model. Pure. One of four words.

    "mute" and "no-output" are deliberately not the same word. A request that
    was rejected before generation bills nothing at all; a request that read
    input and produced nothing ran and stopped, which is a truncation or
    content question with an entirely different repair.
    """
    row = row or {}
    requests_n = int(row.get("requests") or 0)
    if requests_n < max(1, int(min_requests)):
        return "idle"
    if int(row.get("output") or 0) > 0:
        return "producing"
    if int(row.get("input") or 0) > 0:
        return "no-output"
    return "mute"


def contrast(per_key, min_requests=1):
    """The note itself. Pure. Returns (state, detail).

    Looks for disagreement between keys and nothing else. No threshold, no
    ratio: one mute key beside one producing key on the same model in the same
    window is the entire claim, and any other combination is somebody else's.
    """
    per_key = dict(per_key or {})
    states = {k: key_state(v, min_requests) for k, v in per_key.items()}
    mute = sorted(k for k, s in states.items() if s == "mute")
    producing = sorted(k for k, s in states.items() if s == "producing")
    silent = sorted(k for k, s in states.items() if s == "no-output")
    active = mute + producing + silent

    if not active:
        return ("no-traffic", "no key sent enough requests to grade")
    if mute and producing:
        first_mute = per_key[mute[0]]
        first_prod = per_key[producing[0]]
        return ("verification-suspected",
                "%s billed %s request(s) with no tokens either side while %s "
                "produced %s output token(s) on the same model in the same "
                "window" % (mute[0], format(first_mute["requests"], ","),
                            producing[0], format(first_prod["output"], ",")))
    if mute and len(active) == 1:
        return ("single-key-model",
                "%s is the only key with traffic on this model, so there is "
                "nothing to compare it against" % mute[0])
    if mute:
        return ("model-wide-mute",
                "all %d key(s) with traffic are mute, so this is a property of "
                "the model or the body every caller sends" % len(active))
    if silent and not producing:
        return ("input-without-output",
                "%d key(s) consumed input and produced no output, which is a "
                "request that ran rather than one that was refused"
                % len(silent))
    return ("healthy",
            "%d key(s) with traffic, all producing output" % len(producing))


def verdict(model_status, per_key, min_requests=1):
    """Combine reachability with the contrast. Pure. Returns (state, detail).

    The lookup can veto. A model that does not resolve for a project key is a
    question about the model list, which is another note entirely, and grading
    a usage contrast on top of it would attach the wrong repair to it.
    """
    state, detail = contrast(per_key, min_requests)
    if model_status is None:
        return (state, detail + " (the model id itself was not checked, so "
                                "supply a project key to rule out access)")
    status = int(model_status)
    if status == 404:
        return ("model-not-visible",
                "the id does not resolve for the project key. That is "
                "retirement or entitlement rather than a gated feature, and it "
                "belongs to the model-list note")
    if status in (401, 403):
        return (state, detail + " (the model lookup was refused, so access was "
                                "not confirmed either way)")
    if status != 200:
        return (state, detail + " (the model lookup returned %d)" % status)
    return (state, detail)


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed.

    The measured line and the inferred line are always printed together for the
    finding, because the difference between them is the difference between what
    this script saw and what it thinks it means.
    """
    if state == "verification-suspected":
        return [
            "measured: " + MEASURED,
            "inferred: " + INFERRED,
            "verify the organization in Console, then allow up to 15 minutes "
            "to propagate. One government ID verifies one organization per 90 "
            "days, which matters if several organizations share an owner.",
            "as a stopgap on the affected route only, unset stream and buffer "
            "the whole response, and remove reasoning summary requests. Leave "
            "the batch and evaluation routes alone; they are already working.",
            "if the organization is already verified, the next candidate is a "
            "parameter that route sends and the working key does not. Diff the "
            "two request builders before changing anything in Console.",
        ]
    if state == "model-wide-mute":
        return ["not this note. Read the reasoning-model parameter note: "
                "max_tokens, temperature and top_p are refused by name on "
                "those families, and a refusal by name hits every key."]
    if state == "single-key-model":
        return ["route a canary through a second key on the same model, or "
                "read the verification setting in Console. With one key there "
                "is no contrast, and this script will not invent one.",
                "measured: requests were rejected before generation on the "
                "only key that uses this model. Nothing more than that."]
    if state == "model-not-visible":
        return ["check the id against GET /v1/models first. A model that does "
                "not resolve is a retirement or entitlement question, and it "
                "has a different repair from a gated capability."]
    if state == "input-without-output":
        return ["these requests reached the model and returned nothing, which "
                "is truncation or a refusal rather than a rejected body. Read "
                "the structured-output and refusal notes instead."]
    return []


def get(session, path, params=None):
    r = session.get(API + path, params=params or {}, timeout=90)
    if r.status_code in (401, 403):
        raise SystemExit("%d from OpenAI: /v1/organization/* needs an "
                         "organization admin key (sk-admin-), not a project key"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def pages(session, path, params, max_pages=40):
    """Walk the usage report, which paginates on an opaque page cursor."""
    params = dict(params)
    for _ in range(max_pages):
        page = get(session, path, params)
        for bucket in page.get("data") or []:
            yield bucket
        if not page.get("has_more") or not page.get("next_page"):
            return
        params = dict(params)
        params["page"] = page["next_page"]


def check_model(key, model):
    """One cheap GET to prove the id is reachable. Returns a status code."""
    if not key:
        return None
    try:
        r = requests.get(API + "/models/" + str(model),
                         headers={"Authorization": "Bearer " + key}, timeout=30)
    except requests.RequestException:
        return None
    return r.status_code


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hours", type=int, default=24,
                    help="hours of hourly buckets to read (default 24)")
    ap.add_argument("--min-requests", type=int, default=20,
                    help="requests below which a key is treated as idle")
    ap.add_argument("--model", action="append", default=[],
                    help="restrict to these model ids (repeatable)")
    args = ap.parse_args()

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.error("set OPENAI_ADMIN_KEY (an organization admin key; read-only "
                  "scopes are enough)")
        return 2
    project_key = os.environ.get("OPENAI_API_KEY")

    hours = max(1, min(int(args.hours), 168))
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + admin})

    buckets = pages(session, "/organization/usage/completions", {
        "start_time": int(time.time()) - hours * 3600,
        "bucket_width": "1h",
        "limit": hours,
        "group_by": ["model", "api_key_id"],
    })
    grouped = by_model(flatten(buckets))
    wanted = set(args.model or [])
    if wanted:
        grouped = {m: v for m, v in grouped.items() if m in wanted}
    if not grouped:
        log.info("no completions usage in the last %d hour(s)", hours)
        return 0

    log.info("%d model(s) with traffic in the last %dh", len(grouped), hours)
    findings = 0

    for model in sorted(grouped, key=lambda m: -sum(
            r["requests"] for r in grouped[m].values())):
        per_key = grouped[model]
        preliminary, _ = contrast(per_key, args.min_requests)
        status = (check_model(project_key, model)
                  if preliminary in ("verification-suspected",
                                     "single-key-model", "model-wide-mute")
                  else None)
        state, detail = verdict(status, per_key, args.min_requests)

        emit = log.warning if state in FINDINGS or state != "healthy" else log.info
        emit("%-23s %s: %s", state, model, detail)
        if status is not None:
            emit("  model lookup: %d", int(status))
        for line in repair_lines(state):
            emit("  repair: %s" if not line.startswith(("measured:", "inferred:"))
                 else "  %s", line)
        if state in FINDINGS:
            findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "openai-streaming-verification-probe.mjs",
"js": '''/**
 * Find a model that one key can list and another key cannot generate with.
 *
 * Read only. Two GET endpoints: the organization usage report with an admin
 * read key, and /v1/models/{id} with a Read Only project key. No request body
 * is ever constructed and nothing here sends a completion.
 *
 * The subject is a contrast, not a row. A fault that lives in the model
 * refuses every key; a gate on one route does not. What cannot be read is
 * stated rather than guessed: no endpoint reports verification state.
 */
const API = 'https://api.openai.com/v1';

const FINDINGS = new Set(['verification-suspected']);

export const MEASURED =
  'requests on one key were rejected before generation, on a model another key '
  + 'is generating with normally';
export const INFERRED =
  'organization verification, which gates streaming and reasoning summaries. No '
  + 'endpoint reports verification state, so this is the most likely cause and '
  + 'not a reading';

const int = (v) => {
  const n = Number(v ?? 0);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
};

/** [[model, apiKeyId, requests, input, output]]. Pure. */
export function flatten(buckets) {
  const rows = [];
  for (const bucket of buckets ?? []) {
    for (const entry of (bucket ?? {}).results ?? []) {
      const row = entry ?? {};
      rows.push([String(row.model ?? '(unattributed)'),
                 String(row.api_key_id ?? '(unattributed)'),
                 int(row.num_model_requests), int(row.input_tokens),
                 int(row.output_tokens)]);
    }
  }
  return rows;
}

/** {model: {apiKeyId: {requests, input, output}}}. Pure. Summed. */
export function byModel(rows) {
  const out = {};
  for (const [model, keyId, requests, input, output] of rows ?? []) {
    const perModel = (out[model] ??= {});
    const slot = (perModel[keyId] ??= { requests: 0, input: 0, output: 0 });
    slot.requests += requests;
    slot.input += input;
    slot.output += output;
  }
  return out;
}

/** What one key did on one model. Pure. One of four words. */
export function keyState(row, minRequests = 1) {
  const r = row ?? {};
  if (int(r.requests) < Math.max(1, int(minRequests))) return 'idle';
  if (int(r.output) > 0) return 'producing';
  if (int(r.input) > 0) return 'no-output';
  return 'mute';
}

/** The note itself. Pure. Returns [state, detail]. */
export function contrast(perKey, minRequests = 1) {
  const rows = { ...(perKey ?? {}) };
  const states = Object.fromEntries(
    Object.entries(rows).map(([k, v]) => [k, keyState(v, minRequests)]));
  const pick = (want) => Object.keys(states).filter((k) => states[k] === want).sort();
  const mute = pick('mute');
  const producing = pick('producing');
  const silent = pick('no-output');
  const active = [...mute, ...producing, ...silent];

  if (!active.length) return ['no-traffic', 'no key sent enough requests to grade'];
  if (mute.length && producing.length) {
    const n = (v) => v.toLocaleString('en-US');
    return ['verification-suspected',
      `${mute[0]} billed ${n(rows[mute[0]].requests)} request(s) with no tokens `
      + `either side while ${producing[0]} produced ${n(rows[producing[0]].output)} `
      + 'output token(s) on the same model in the same window'];
  }
  if (mute.length && active.length === 1) {
    return ['single-key-model',
      `${mute[0]} is the only key with traffic on this model, so there is `
      + 'nothing to compare it against'];
  }
  if (mute.length) {
    return ['model-wide-mute',
      `all ${active.length} key(s) with traffic are mute, so this is a property `
      + 'of the model or the body every caller sends'];
  }
  if (silent.length && !producing.length) {
    return ['input-without-output',
      `${silent.length} key(s) consumed input and produced no output, which is a `
      + 'request that ran rather than one that was refused'];
  }
  return ['healthy', `${producing.length} key(s) with traffic, all producing output`];
}

/** Combine reachability with the contrast. Pure. Returns [state, detail]. */
export function verdict(modelStatus, perKey, minRequests = 1) {
  const [state, detail] = contrast(perKey, minRequests);
  if (modelStatus === null || modelStatus === undefined) {
    return [state, detail + ' (the model id itself was not checked, so supply a '
      + 'project key to rule out access)'];
  }
  const status = int(modelStatus);
  if (status === 404) {
    return ['model-not-visible',
      'the id does not resolve for the project key. That is retirement or '
      + 'entitlement rather than a gated feature, and it belongs to the '
      + 'model-list note'];
  }
  if (status === 401 || status === 403) {
    return [state, detail + ' (the model lookup was refused, so access was not '
      + 'confirmed either way)'];
  }
  if (status !== 200) return [state, detail + ` (the model lookup returned ${status})`];
  return [state, detail];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  if (state === 'verification-suspected') {
    return [
      'measured: ' + MEASURED,
      'inferred: ' + INFERRED,
      'verify the organization in Console, then allow up to 15 minutes to '
      + 'propagate. One government ID verifies one organization per 90 days, '
      + 'which matters if several organizations share an owner.',
      'as a stopgap on the affected route only, unset stream and buffer the '
      + 'whole response, and remove reasoning summary requests. Leave the batch '
      + 'and evaluation routes alone; they are already working.',
      'if the organization is already verified, the next candidate is a '
      + 'parameter that route sends and the working key does not. Diff the two '
      + 'request builders before changing anything in Console.',
    ];
  }
  if (state === 'model-wide-mute') {
    return ['not this note. Read the reasoning-model parameter note: max_tokens, '
      + 'temperature and top_p are refused by name on those families, and a '
      + 'refusal by name hits every key.'];
  }
  if (state === 'single-key-model') {
    return ['route a canary through a second key on the same model, or read the '
      + 'verification setting in Console. With one key there is no contrast, and '
      + 'this script will not invent one.',
      'measured: requests were rejected before generation on the only key that '
      + 'uses this model. Nothing more than that.'];
  }
  if (state === 'model-not-visible') {
    return ['check the id against GET /v1/models first. A model that does not '
      + 'resolve is a retirement or entitlement question, and it has a different '
      + 'repair from a gated capability.'];
  }
  if (state === 'input-without-output') {
    return ['these requests reached the model and returned nothing, which is '
      + 'truncation or a refusal rather than a rejected body. Read the '
      + 'structured-output and refusal notes instead.'];
  }
  return [];
}

async function read(key, path, params) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params ?? {})) {
    if (Array.isArray(v)) for (const item of v) url.searchParams.append(k, String(item));
    else url.searchParams.set(k, String(v));
  }
  const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (r.status === 401 || r.status === 403) {
    throw new Error(`${r.status} from OpenAI: /v1/organization/* needs an `
                    + 'organization admin key, not a project key');
  }
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

async function* pages(key, path, params, maxPages = 40) {
  let q = { ...params };
  for (let i = 0; i < maxPages; i += 1) {
    const page = await read(key, path, q);
    for (const bucket of page.data ?? []) yield bucket;
    if (!page.has_more || !page.next_page) return;
    q = { ...q, page: page.next_page };
  }
}

async function checkModel(key, model) {
  if (!key) return null;
  try {
    const r = await fetch(`${API}/models/${model}`,
                          { headers: { Authorization: `Bearer ${key}` } });
    return r.status;
  } catch {
    return null;
  }
}

async function main() {
  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.error('set OPENAI_ADMIN_KEY (an organization admin key; read-only '
                  + 'scopes are enough)');
    process.exitCode = 2;
    return;
  }
  const projectKey = process.env.OPENAI_API_KEY;
  const hours = Math.max(1, Math.min(int(process.env.USAGE_HOURS ?? 24), 168));
  const minRequests = Math.max(1, int(process.env.MIN_REQUESTS ?? 20));

  const buckets = [];
  for await (const bucket of pages(admin, '/organization/usage/completions', {
    start_time: Math.floor(Date.now() / 1000) - hours * 3600,
    bucket_width: '1h',
    limit: hours,
    group_by: ['model', 'api_key_id'],
  })) buckets.push(bucket);

  const grouped = byModel(flatten(buckets));
  const models = Object.keys(grouped);
  if (!models.length) {
    console.log(`no completions usage in the last ${hours} hour(s)`);
    return;
  }
  console.log(`${models.length} model(s) with traffic in the last ${hours}h`);

  const total = (m) => Object.values(grouped[m]).reduce((a, r) => a + r.requests, 0);
  let findings = 0;

  for (const model of models.sort((a, b) => total(b) - total(a))) {
    const perKey = grouped[model];
    const [preliminary] = contrast(perKey, minRequests);
    const status = ['verification-suspected', 'single-key-model', 'model-wide-mute']
      .includes(preliminary) ? await checkModel(projectKey, model) : null;
    const [state, detail] = verdict(status, perKey, minRequests);

    console.log(`${state.padEnd(23)} ${model}: ${detail}`);
    if (status !== null && status !== undefined) console.log(`  model lookup: ${status}`);
    for (const line of repairLines(state)) {
      const prefix = (line.startsWith('measured:') || line.startsWith('inferred:'))
        ? '  ' : '  repair: ';
      console.log(prefix + line);
    }
    if (FINDINGS.has(state)) findings += 1;
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the pairing the note is built on: one key with requests and no tokens beside one key producing output, on the same model, has to be the finding and has to name both keys. The second is the boundary that keeps this out of the published parameter note &mdash; every key mute must come back as <code>model-wide-mute</code>, must not be this note's finding, and must print the other note by name. The third is the case the script refuses to grade, a model used by exactly one key, where the contrast simply does not exist. Then the 404 handed to the model-list note, the separation of <em>rejected before generation</em> from <em>ran and produced nothing</em>, and last the assertion that the finding always prints what was measured next to what is only inferred.",
"test_py_file": "test_openai_streaming_verification_probe.py",
"test_py": '''from openai_streaming_verification_probe import (INFERRED, MEASURED, by_model,
                                                 contrast, flatten, key_state,
                                                 repair_lines, verdict)


def bucket(*results):
    return {"start_time": 1_700_000_000, "results": list(results)}


def result(model, key_id, requests, input_tokens=0, output_tokens=0):
    return {"model": model, "api_key_id": key_id,
            "num_model_requests": requests, "input_tokens": input_tokens,
            "output_tokens": output_tokens}


def test_two_keys_disagreeing_on_one_model_is_the_finding():
    rows = flatten([bucket(result("gpt-5.6", "key_9fA2", 1204),
                           result("gpt-5.6", "key_3bQ7", 900, 400_000, 812_004))])
    per_key = by_model(rows)["gpt-5.6"]
    state, detail = verdict(200, per_key)
    assert state == "verification-suspected"
    assert "key_9fA2" in detail and "key_3bQ7" in detail
    assert "1,204" in detail and "812,004" in detail


def test_every_key_mute_is_the_other_note_and_says_so():
    # The boundary. A parameter a model refuses by name is refused for every
    # key, so agreement between keys means this note has no evidence at all.
    per_key = by_model(flatten([bucket(result("o4-mini", "key_a", 400),
                                       result("o4-mini", "key_b", 900),
                                       result("o4-mini", "key_c", 30))]))["o4-mini"]
    state, detail = verdict(200, per_key)
    assert state == "model-wide-mute"
    assert "every caller sends" in detail
    assert any("reasoning-model parameter note" in line
               for line in repair_lines(state))
    assert repair_lines(state) and state not in ("verification-suspected",)


def test_one_key_on_a_model_is_unresolvable_and_is_not_graded():
    per_key = by_model(flatten([bucket(result("gpt-5.1", "key_only", 800))]))["gpt-5.1"]
    state, detail = verdict(200, per_key)
    assert state == "single-key-model"
    assert "nothing to compare it against" in detail
    lines = repair_lines(state)
    assert any("canary" in line for line in lines)
    assert any(line.startswith("measured:") for line in lines)


def test_a_model_that_does_not_resolve_belongs_to_the_model_list_note():
    per_key = by_model(flatten([bucket(result("gpt-4-0613", "key_a", 500),
                                       result("gpt-4-0613", "key_b", 500, 1, 9))]))["gpt-4-0613"]
    state, detail = verdict(404, per_key)
    assert state == "model-not-visible"
    assert "model-list note" in detail
    assert any("GET /v1/models" in line for line in repair_lines(state))


def test_rejected_before_generation_is_not_the_same_as_produced_nothing():
    assert key_state({"requests": 100, "input": 0, "output": 0}) == "mute"
    assert key_state({"requests": 100, "input": 900, "output": 0}) == "no-output"
    assert key_state({"requests": 100, "input": 900, "output": 4}) == "producing"
    assert key_state({"requests": 0, "input": 0, "output": 0}) == "idle"
    assert key_state({"requests": 5, "input": 0, "output": 0}, 20) == "idle"

    per_key = by_model(flatten([bucket(result("m", "key_a", 100, 900, 0))]))["m"]
    state, _ = contrast(per_key)
    assert state == "input-without-output"
    assert any("truncation or a refusal" in line for line in repair_lines(state))


def test_the_finding_separates_what_was_measured_from_what_was_inferred():
    lines = repair_lines("verification-suspected")
    assert lines[0] == "measured: " + MEASURED
    assert lines[1] == "inferred: " + INFERRED
    assert "No endpoint reports verification state" in INFERRED
    assert any("15 minutes" in line for line in lines)
    assert any("unset stream" in line for line in lines)
    assert any("already verified" in line for line in lines)


def test_counts_are_coerced_and_missing_fields_do_not_become_silence():
    rows = flatten([bucket({"model": None, "api_key_id": None,
                            "num_model_requests": "not-a-number"})])
    assert rows == [("(unattributed)", "(unattributed)", 0, 0, 0)]
    assert flatten(None) == [] and by_model(None) == {}
    assert contrast({})[0] == "no-traffic"
    assert verdict(None, {})[1].endswith("to rule out access)")
    assert repair_lines("healthy") == []
''',
"test_js_file": "openai-streaming-verification-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { INFERRED, MEASURED, byModel, contrast, flatten, keyState, repairLines,
         verdict } from './openai-streaming-verification-probe.mjs';

const bucket = (...results) => ({ start_time: 1700000000, results });
const result = (model, keyId, requests, inputTokens = 0, outputTokens = 0) =>
  ({ model, api_key_id: keyId, num_model_requests: requests,
     input_tokens: inputTokens, output_tokens: outputTokens });

test('two keys disagreeing on one model is the finding', () => {
  const rows = flatten([bucket(result('gpt-5.6', 'key_9fA2', 1204),
                               result('gpt-5.6', 'key_3bQ7', 900, 400000, 812004))]);
  const perKey = byModel(rows)['gpt-5.6'];
  const [state, detail] = verdict(200, perKey);
  assert.equal(state, 'verification-suspected');
  assert.ok(detail.includes('key_9fA2') && detail.includes('key_3bQ7'));
  assert.ok(detail.includes('1,204') && detail.includes('812,004'));
});

test('every key mute is the other note and says so', () => {
  const perKey = byModel(flatten([bucket(result('o4-mini', 'key_a', 400),
                                         result('o4-mini', 'key_b', 900),
                                         result('o4-mini', 'key_c', 30))]))['o4-mini'];
  const [state, detail] = verdict(200, perKey);
  assert.equal(state, 'model-wide-mute');
  assert.ok(detail.includes('every caller sends'));
  assert.ok(repairLines(state).some((l) => l.includes('reasoning-model parameter note')));
});

test('one key on a model is unresolvable and is not graded', () => {
  const perKey = byModel(flatten([bucket(result('gpt-5.1', 'key_only', 800))]))['gpt-5.1'];
  const [state, detail] = verdict(200, perKey);
  assert.equal(state, 'single-key-model');
  assert.ok(detail.includes('nothing to compare it against'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('canary')));
  assert.ok(lines.some((l) => l.startsWith('measured:')));
});

test('a model that does not resolve belongs to the model list note', () => {
  const perKey = byModel(flatten([bucket(result('gpt-4-0613', 'key_a', 500),
                                         result('gpt-4-0613', 'key_b', 500, 1, 9))]))['gpt-4-0613'];
  const [state, detail] = verdict(404, perKey);
  assert.equal(state, 'model-not-visible');
  assert.ok(detail.includes('model-list note'));
  assert.ok(repairLines(state).some((l) => l.includes('GET /v1/models')));
});

test('rejected before generation is not the same as produced nothing', () => {
  assert.equal(keyState({ requests: 100, input: 0, output: 0 }), 'mute');
  assert.equal(keyState({ requests: 100, input: 900, output: 0 }), 'no-output');
  assert.equal(keyState({ requests: 100, input: 900, output: 4 }), 'producing');
  assert.equal(keyState({ requests: 0, input: 0, output: 0 }), 'idle');
  assert.equal(keyState({ requests: 5, input: 0, output: 0 }, 20), 'idle');

  const perKey = byModel(flatten([bucket(result('m', 'key_a', 100, 900, 0))])).m;
  assert.equal(contrast(perKey)[0], 'input-without-output');
  assert.ok(repairLines('input-without-output').some((l) => l.includes('truncation or a refusal')));
});

test('the finding separates what was measured from what was inferred', () => {
  const lines = repairLines('verification-suspected');
  assert.equal(lines[0], 'measured: ' + MEASURED);
  assert.equal(lines[1], 'inferred: ' + INFERRED);
  assert.ok(INFERRED.includes('No endpoint reports verification state'));
  assert.ok(lines.some((l) => l.includes('15 minutes')));
  assert.ok(lines.some((l) => l.includes('unset stream')));
  assert.ok(lines.some((l) => l.includes('already verified')));
});

test('counts are coerced and missing fields do not become silence', () => {
  const rows = flatten([bucket({ model: null, api_key_id: null,
                                 num_model_requests: 'not-a-number' })]);
  assert.deepEqual(rows, [['(unattributed)', '(unattributed)', 0, 0, 0]]);
  assert.deepEqual(flatten(null), []);
  assert.deepEqual(byModel(null), {});
  assert.equal(contrast({})[0], 'no-traffic');
  assert.ok(verdict(null, {})[1].endsWith('to rule out access)'));
  assert.deepEqual(repairLines('healthy'), []);
});
''',
"faq": [
 ("Can the script actually tell me my organization is unverified?",
  "No, and it says so in its own output. There is no endpoint on the OpenAI API that reports verification status; it is a Console setting. There is also no request log, so the 400 body that would have named it cannot be fetched after the fact. What the script proves is narrower and still useful: on this model, in this window, one key had requests billed with no tokens either side while another key produced output normally. That rules out the model, the id and the credential in one reading, and leaves verification as the most likely of a short list of causes. The output prints the measurement and the inference on separate lines for exactly that reason."),
 ("How is this different from the note about reasoning models refusing max_tokens?",
  "They read the same row and separate on one thing. Both are looking at requests counted with zero tokens either side, which is what a rejection before generation looks like in an aggregate that has no error field. That note groups by model and project and concludes that a parameter is being refused by name; this one groups by api_key_id inside a model and looks for two keys that disagree. The logic is that a parameter a model refuses is refused for every caller, and a gate on the streaming path is not. When the keys agree, this script prints that note's name and stops."),
 ("Why does it matter that only one route is broken?",
  "Because it decides where you look and it explains why nothing caught it. Verification gates streaming and reasoning summaries, not the model, so every code path that buffers a complete response keeps working: batch jobs, evaluations, tests, back-office scripts. The only path that streams is usually the one with a person waiting at the end of it, and it is often the least covered. That asymmetry is also what makes the two-key comparison possible, since in most organizations those routes are served by different keys."),
 ("What if the model returns 404 rather than serving the request?",
  "Then this is not the note and the script hands it over. Some models refuse an unverified organization at the lookup itself with a message about verification, and a retired or unentitled id refuses with a message about the id. Both are a 404 and the script cannot read the message body of a request it did not make. Since the repair for a model that does not resolve starts by diffing your configured ids against the model list, that reading belongs to the retired-id note, and duplicating it here would put two different repairs behind one symptom."),
 ("The model is used by exactly one key. Can I still get an answer?",
  "Not from this script, deliberately. The finding is a disagreement between two keys, and with one key there is nothing to disagree with. The state is named single-key-model, and the printed suggestion is to create the contrast rather than to guess: route a canary through a second key on the same model, or read the setting in Console directly. A script that graded one mute key as a verification problem would be right sometimes and would also flag every model whose only caller has a broken request body."),
],
"related": [REL_ZERO_OUT, REL_RETIRED, REL_REGION],
"citations": [CITE_OAI_VERIFY, CITE_OAI_USAGE, CITE_OAI_MODELS, CITE_OAI_ADMIN],
},
{
"slug": "unsupported-country-region",
"title": "The same key works on your laptop and 403s in production",
"description": "Run GET /v1/models from the production egress path and compare it with the same call from a known-good host. 403 here and 200 there is geography, not the key.",
"h1": "The same key works on your laptop and 403s in production",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["unsupported_country_region_territory 403 openai",
             "country region or territory not supported api",
             "openai 403 from cloud run asia-northeast3",
             "edge function openai request blocked region",
             "anthropic supported regions api 403"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Uses whichever of OPENAI_API_KEY and ANTHROPIC_API_KEY are set, both read-only GETs of /v1/models. Must be run from the production egress path, and once from a host you already trust, to produce the baseline it compares against.",
"lead": "The feature works. It works on two laptops, it works in CI, it worked in the preview deployment, and it has never once failed in review. It is promoted to production on a Thursday and every request returns <code>403</code>. Not a rate limit, not an expired key, not a model id: a flat refusal with a message about countries. Nobody changed the code. Nobody rotated the key. What changed is that the edge platform picked a point of presence closer to the user, and the request now leaves the internet somewhere the provider does not serve.",
"short_answer": """<p>Run the probe where the problem is. <code>GET /v1/models</code> with the same read-only key your application uses, <strong>from inside the production egress path</strong> &mdash; the same VPC, the same region, the same edge runtime. A <code>200</code> proves that geography is allowed from that host. A <code>403</code> with <code>code: \"unsupported_country_region_territory\"</code> proves it is not.</p>
<p>One run is not enough, because a <code>403</code> on its own has more than one cause. So run the identical probe from a host you already trust, and compare. The script prints a one-line JSON observation which you carry to the other host as <code>LLM_EGRESS_BASELINE</code>; it holds a provider, a status code and an error code, and nothing else. <strong>403 here and 200 there is geography.</strong> 403 on both is the account rather than the location. 401 on both is the credential, which is a different note.</p>
<p>Both providers are probed if both keys are set, because both geo-block and the answer can differ between them. OpenAI documents the refusal as a <code>403</code> whose code is <code>unsupported_country_region_territory</code>. Anthropic publishes a list of the countries, regions and territories it can serve, and does not document a distinct error code, so the script records whatever <code>error.type</code> comes back verbatim rather than asserting one it cannot cite.</p>
<p>Two things the script deliberately does not do. It does not call any third-party service to discover its own public IP or country: that is an external dependency added to a diagnostic, and the provider's own answer is the only one that matters anyway. And it does not print a proxy as a repair. The fix is to pin execution to a supported region &mdash; a Vercel <code>regions</code> config, a Cloud Run or Lambda redeploy in a supported region, a VPN turned off &mdash; and routing around a geographic restriction is not a repair this section will suggest.</p>""",
"problem": """<p>The block is on the request's egress IP, not on your account's country. That single sentence explains every strange thing about this failure. Your organization is in a supported country, your billing address is fine, your key is fine, and the request is refused because of where the packet came from &mdash; which is a property of the machine, not of you.</p>
<p>Modern deployment targets move that machine without telling you. Edge platforms run your function at whichever point of presence is nearest the user, so the same code executes from a different country per request. A cloud region chosen for latency to a customer base can sit outside the supported list. A corporate VPN relocates a developer's egress. A newly added region in a multi-region deployment inherits the code and not the assumption.</p>
<p>So the failure has the worst possible test profile: total from the affected host and absent from every host where anybody looks. CI passes, staging passes, the laptop passes, and the only environment that fails is the one you cannot easily attach a debugger to. And because it is a <code>403</code> rather than a <code>429</code> or a <code>500</code>, no amount of retrying helps; a retry loop simply produces the same refusal faster.</p>
<p>The second-order problem is diagnosis by guesswork. A <code>403</code> gets read as a permissions problem, so somebody rotates the key, which changes nothing, and then somebody widens the key's scopes, which changes nothing and leaves you with a more powerful credential than you started with. The refusal is not about the credential at all, and the only cheap way to prove that is to send the identical request with the identical key from somewhere else.</p>""",
"why": """<p><strong>One observation cannot be a finding here, because the variable is the machine.</strong> Every other note in this section reads state that is the same wherever you read it from. This one reads state that only exists relative to a location, so the unit of evidence is a pair: the same call, the same key, two hosts. That is also why the script's output is designed to be carried &mdash; a small JSON blob you paste into the environment of the second run &mdash; rather than assumed.</p>
<p><strong>The pair is what separates geography from credentials, and that separation is the whole value.</strong> A 403 read alone sends people to the key page. A 403 here beside a 200 there, on the same key, makes the credential impossible as an explanation. The script states each of those outcomes as its own verdict and, in the credentials case, says plainly that this is not the note and points elsewhere.</p>
<p><strong>Both providers get probed, and they do not answer the same way.</strong> OpenAI documents a 403 with <code>unsupported_country_region_territory</code>, which is a code the script can match on and treat as proof. Anthropic publishes a supported-regions list rather than a documented error code for this case, so the script records the returned <code>error.type</code> verbatim and grades it as an unexplained 403 rather than pattern-matching a string it has no source for. Inventing that code would be worse than not having it.</p>
<p><strong>No third-party geolocation call, on purpose.</strong> It would be easy to fetch a public IP and look up its country, and it would add a network dependency, a privacy question and a second thing that can be wrong to a script whose entire job is to reduce ambiguity. The provider's 403 already is the answer to "is this location allowed", and it is the only authority that counts.</p>
<p><strong>The repair is a region pin, never a proxy.</strong> The documented fix is to pin execution: an explicit region on an edge function, a redeploy of a container or function into a supported region, a VPN disabled. Routing the provider's host through an egress somewhere else is a way to defeat a restriction rather than to resolve one, and this section prints repairs you should actually run.</p>
<p><strong>Corroborating this from the usage report would be somebody else's reading.</strong> A deployed project with no requests in it does look like a hard block, and it also looks like a dead credential, a paused deploy or a feature nobody used &mdash; which is exactly the ambiguity <a href="/llm/live-project-zero-usage-buckets/">the zero-usage note</a> exists to grade. This script stays with the probe pair, where the evidence is unambiguous.</p>""",
"steps": [
 {"h": "Run it first from a host you trust, and keep the blob",
  "body": """<p>A laptop, a CI runner, a bastion in a region you know works. The script prints one line of JSON: provider, status, error code. It contains no key and no hostname. That line is the baseline.</p>"""},
 {"h": "Run it again from the production egress path",
  "body": """<p>The same VPC, the same region, the same edge runtime, with <code>LLM_EGRESS_BASELINE</code> set to the line from step one. Same code, same key, different machine, which is the only variable that matters.</p>"""},
 {"h": "Read the pair rather than the status",
  "body": """<p>403 here and 200 there is geography. 403 on both is the account or an organization-level restriction. 401 on both is the credential and belongs elsewhere. 200 here is the end of it, whatever anybody suspected.</p>"""},
 {"h": "Record the error code verbatim, and only claim what it says",
  "body": """<p><code>unsupported_country_region_territory</code> on OpenAI is documented and is treated as proof. Anything else, including any Anthropic 403, is printed exactly as returned and graded as an unexplained refusal rather than assigned a cause the script cannot cite.</p>"""},
 {"h": "Print the region pin",
  "body": """<p>For an edge function, the platform's region configuration. For Cloud Run, Lambda or a container, a redeploy into a supported region. For a VPN, disable it. Never a proxy, and the script does not offer one.</p>"""},
],
"verify": """<p>Re-run from the pinned deployment with the same baseline. The production observation should move to <code>200</code> and the verdict to <code>clear</code>. The check that matters more is the negative one: if you fixed it by routing the provider's host through somewhere else, this script will now say <code>clear</code> and it will be telling you about the proxy rather than about your deployment, which is precisely why the repair it prints is a region pin.</p>
<pre><code class="language-bash"># on a host you trust
python3 llm_egress_region_probe.py
# openai      200  reachable      this egress path is allowed for this key
# anthropic   200  reachable      this egress path is allowed for this key
# baseline: {"anthropic":{"code":"","status":200},"openai":{"code":"","status":200}}

# from the production egress path
LLM_EGRESS_BASELINE='{"anthropic":{"code":"","status":200},"openai":{"code":"","status":200}}' \\
  python3 llm_egress_region_probe.py
# openai      403  region-blocked unsupported_country_region_territory
# geography-isolated   openai: 403 here and 200 from the baseline host on the same
#                      key, so the difference is the egress path and not the
#                      credential
#   repair: pin execution to a supported region. On Vercel, export const config
#           = { regions: ['iad1'] }. On Cloud Run, Lambda or a container,
#           redeploy in a supported region. On a VPN, turn it off.
#   repair: do not route the provider host through another egress to get around
#           this. Move the workload, not the packets.
# anthropic   200  reachable      this egress path is allowed for this key
# clear                anthropic: 200 from this host, so the egress path is fine
# 1 finding(s)</code></pre>""",
"code_intro": "Two GETs at most and six pure functions. <code>error_code</code>, which reads <code>error.code</code> and falls back to <code>error.type</code> so one function covers both providers' error envelopes; <code>observation</code>, which reduces a response to a provider, a status and a code and is the only thing that ever leaves the process; <code>classify</code>, which grades one observation and treats only the documented code as proof of a region block; <code>compare</code>, which is the note, and is the only function that sees two hosts; <code>blob</code> and <code>load_baseline</code>, which round-trip the observation as one sorted line of JSON with no credential in it; and <code>repair_lines</code>, which prints region pins and refuses to print a proxy.",
"py_file": "llm_egress_region_probe.py",
"py": '''"""Prove whether a 403 is about where the request left from, or about the key.

Read only. One GET of /v1/models per provider whose key is present, and
nothing else. No request body is constructed, nothing is generated, nothing is
billed, and no third-party service is contacted -- in particular the script
never looks up its own public IP, because the provider's own answer to "is this
location allowed" is the only authority that matters.

The variable here is the machine. Every other reading in this section is the
same wherever it is taken from; this one only exists relative to a location, so
the unit of evidence is a pair. Run it once from a host you trust, carry the
one-line observation it prints, and run it again from the production egress
path with that line in LLM_EGRESS_BASELINE.

The blob carries a provider, a status and an error code. It never contains a
key, a hostname or anything else, and there is a test that says so.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("llm_egress_region_probe")

# Both are model listings: free, read-only, and refused by a geographic block
# exactly as any other call from the same host would be.
PROVIDERS = {
    "openai": {"url": "https://api.openai.com/v1/models",
               "env": "OPENAI_API_KEY"},
    "anthropic": {"url": "https://api.anthropic.com/v1/models",
                  "env": "ANTHROPIC_API_KEY"},
}

# The one code this script treats as proof of a geographic block, because it is
# the one that is documented. Anthropic publishes a supported-regions list and
# no distinct code for this case, so an Anthropic 403 is recorded verbatim and
# graded as unexplained rather than assigned a cause with no source.
BLOCK_CODE = "unsupported_country_region_territory"

FINDINGS = ("geography-isolated", "region-blocked-unconfirmed",
            "region-blocked-everywhere", "forbidden-unexplained")


def error_code(body):
    """The provider's error code from a JSON body. Pure. Empty when absent.

    One function for both envelopes: OpenAI puts a machine-readable string in
    error.code and Anthropic puts one in error.type, and falling back covers
    both without branching on the provider.
    """
    error = (body or {}).get("error") if isinstance(body, dict) else None
    if not isinstance(error, dict):
        return ""
    for field in ("code", "type"):
        value = error.get(field)
        if value:
            return str(value).strip()
    return ""


def observation(provider, status, body):
    """One probe result, reduced. Pure. The only thing that leaves the process.

    Three fields on purpose. A response body can contain an organization name,
    a request id or a message quoting the request, and none of that needs to be
    carried between two machines to answer a question about a status code.
    """
    return {"provider": str(provider),
            "status": None if status is None else int(status),
            "code": str(error_code(body) or "")}


def classify(obs):
    """Grade one observation. Pure. Returns (state, detail)."""
    obs = obs or {}
    status = obs.get("status")
    code = str(obs.get("code") or "")
    if status is None:
        return ("unreachable",
                "no response at all, which is a network answer rather than a "
                "policy one")
    status = int(status)
    if status == 200:
        return ("reachable", "this egress path is allowed for this key")
    if status == 403 and code == BLOCK_CODE:
        return ("region-blocked", BLOCK_CODE)
    if status == 403:
        return ("forbidden-other",
                "403 with code %r, which is not the documented geographic block"
                % (code or "(none returned)"))
    if status == 401:
        return ("credentials", "401, which is the key and not the location")
    if status == 429:
        return ("rate-limited",
                "429, so this host reaches the provider fine and the question "
                "is capacity rather than geography")
    return ("unexpected", "%d with code %r" % (status, code or "(none)"))


def compare(local, baseline):
    """The note. Pure. Returns (state, detail). The only two-host function.

    A 403 read alone sends people to the key page. A 403 here beside a 200
    there, on the same key, makes the credential impossible as an explanation,
    and that is the entire reason this script asks to be run twice.
    """
    local_state, local_detail = classify(local)
    provider = (local or {}).get("provider") or "(unknown)"
    if not baseline:
        if local_state == "region-blocked":
            return ("region-blocked-unconfirmed",
                    "%s: 403 %s from this host. The code is documented, but "
                    "with no baseline this has not been separated from an "
                    "account-level restriction" % (provider, BLOCK_CODE))
        if local_state in ("forbidden-other", "credentials"):
            return ("no-baseline",
                    "%s: %s, and no baseline to compare it against. Run this "
                    "from a host you trust first" % (provider, local_detail))
        return (("clear" if local_state == "reachable" else local_state),
                "%s: %s" % (provider, local_detail))

    base_state, _ = classify(baseline)
    if local_state == "reachable":
        return ("clear",
                "%s: 200 from this host, so the egress path is fine"
                % provider)
    if local_state == "region-blocked" and base_state == "reachable":
        return ("geography-isolated",
                "%s: 403 here and 200 from the baseline host on the same key, "
                "so the difference is the egress path and not the credential"
                % provider)
    if local_state == "region-blocked" and base_state == "region-blocked":
        return ("region-blocked-everywhere",
                "%s: 403 %s from both hosts, so this is the account or an "
                "organization-level restriction rather than this deployment's "
                "location" % (provider, BLOCK_CODE))
    if local_state == "credentials" and base_state == "credentials":
        return ("credentials-not-geography",
                "%s: 401 from both hosts on the same key, which is the "
                "credential and not the location" % provider)
    if local_state == "credentials":
        return ("credentials-here-only",
                "%s: 401 here and %s from the baseline host. A key that "
                "authenticates elsewhere and not here is usually a different "
                "key in the environment, not a geographic block"
                % (provider, base_state))
    if local_state == "forbidden-other" and base_state == "reachable":
        return ("forbidden-unexplained",
                "%s: %s here and 200 from the baseline host. The host is the "
                "difference; the code is not one this script can attribute"
                % (provider, local_detail))
    return ("inconclusive",
            "%s: %s here, %s from the baseline host"
            % (provider, local_state, base_state))


def blob(observations):
    """The one line to carry to the other host. Pure. Sorted, and no secrets.

    Keys are sorted so two runs of the same script produce a byte-identical
    string, which makes it obvious when the thing being pasted around has
    changed.
    """
    payload = {}
    for obs in observations or []:
        row = obs or {}
        payload[str(row.get("provider"))] = {
            "status": row.get("status"),
            "code": str(row.get("code") or ""),
        }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def load_baseline(raw):
    """{provider: observation} from the blob. Pure. Empty dict on anything odd.

    Deliberately forgiving. The blob is pasted between machines by a human
    under time pressure, and a mangled paste should produce "no baseline" and a
    clear instruction rather than a stack trace on the host that is on fire.
    """
    try:
        parsed = json.loads(str(raw or "").strip() or "{}")
    except ValueError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    out = {}
    for provider, row in parsed.items():
        if not isinstance(row, dict):
            continue
        status = row.get("status")
        try:
            status = None if status is None else int(status)
        except (TypeError, ValueError):
            status = None
        out[str(provider)] = {"provider": str(provider), "status": status,
                              "code": str(row.get("code") or "")}
    return out


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed.

    A region pin, never a proxy. Routing the provider's host through an egress
    somewhere else defeats a restriction rather than resolving one, and this
    section prints repairs that are meant to be run.
    """
    pin = ("pin execution to a supported region. On Vercel, export const "
           "config = { regions: ['iad1'] }. On Cloud Run, Lambda or a "
           "container, redeploy in a supported region. On a VPN, turn it off.")
    no_proxy = ("do not route the provider host through another egress to get "
                "around this. Move the workload, not the packets.")
    if state == "geography-isolated":
        return [pin, no_proxy]
    if state == "region-blocked-unconfirmed":
        return ["run this same script from a host you already trust and paste "
                "its blob into LLM_EGRESS_BASELINE here. One 403 does not "
                "separate the location from the account.", pin]
    if state == "region-blocked-everywhere":
        return ["both hosts are refused, so moving this deployment will not "
                "help. Check the organization's country and any access "
                "restriction on the account before touching infrastructure."]
    if state == "credentials-not-geography":
        return ["not this note. The same key is refused from both hosts, which "
                "is a credential question: check that the key exists, is "
                "enabled, and belongs to the project you think it does."]
    if state == "credentials-here-only":
        return ["compare the environment on the two hosts. A key that works "
                "from one machine and 401s from another is almost always a "
                "different value in the environment rather than a location."]
    if state == "forbidden-unexplained":
        return ["record the error code exactly as printed and check the "
                "provider's supported regions list for the country this host "
                "egresses from.", pin]
    if state == "no-baseline":
        return ["run this from a host you trust and set LLM_EGRESS_BASELINE to "
                "the blob it prints. Without the pair there is one status code "
                "and no conclusion."]
    return []


def probe(provider, key, timeout=30):
    """One GET. Returns (status, body). Never raises on a 4xx: it is the answer."""
    spec = PROVIDERS[provider]
    headers = {}
    if provider == "openai":
        headers["Authorization"] = "Bearer " + key
    else:
        headers["x-api-key"] = key
        headers["anthropic-version"] = "2023-06-01"
    try:
        r = requests.get(spec["url"], headers=headers, params={"limit": 1},
                         timeout=timeout)
    except requests.RequestException as exc:
        log.debug("probe of %s failed: %s", provider, exc)
        return (None, None)
    try:
        return (r.status_code, r.json())
    except ValueError:
        return (r.status_code, None)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", default=os.environ.get("LLM_EGRESS_BASELINE"),
                    help="the blob printed by a run on a host you trust")
    args = ap.parse_args()

    present = [p for p in sorted(PROVIDERS)
               if os.environ.get(PROVIDERS[p]["env"])]
    if not present:
        log.error("set OPENAI_API_KEY or ANTHROPIC_API_KEY. Both are used for "
                  "one read-only GET of /v1/models and nothing else")
        return 2

    baseline = load_baseline(args.baseline)
    observations = []
    findings = 0

    for provider in present:
        status, body = probe(provider, os.environ[PROVIDERS[provider]["env"]])
        obs = observation(provider, status, body)
        observations.append(obs)
        state, detail = classify(obs)
        emit = log.warning if state != "reachable" else log.info
        emit("%-11s %s  %-14s %s", provider,
             "---" if obs["status"] is None else obs["status"], state, detail)

        verdict, why = compare(obs, baseline.get(provider))
        emit = log.warning if verdict in FINDINGS else log.info
        emit("%-20s %s", verdict, why)
        for line in repair_lines(verdict):
            emit("  repair: %s", line)
        if verdict in FINDINGS:
            findings += 1

    log.info("baseline: %s", blob(observations))
    if not baseline:
        log.info("no baseline was supplied. Carry that line to the other host "
                 "and run this again there")
    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "llm-egress-region-probe.mjs",
"js": '''/**
 * Prove whether a 403 is about where the request left from, or about the key.
 *
 * Read only. One GET of /v1/models per provider whose key is present, and
 * nothing else. No request body, nothing generated, nothing billed, and no
 * third-party service contacted: the script never looks up its own public IP,
 * because the provider's own answer is the only authority that counts.
 *
 * The variable is the machine, so the unit of evidence is a pair. Run it from
 * a host you trust, carry the one-line blob, run it again from production with
 * that line in LLM_EGRESS_BASELINE.
 */
const PROVIDERS = {
  openai: { url: 'https://api.openai.com/v1/models', env: 'OPENAI_API_KEY' },
  anthropic: { url: 'https://api.anthropic.com/v1/models', env: 'ANTHROPIC_API_KEY' },
};

// The one code treated as proof, because it is the one that is documented.
export const BLOCK_CODE = 'unsupported_country_region_territory';

const FINDINGS = new Set(['geography-isolated', 'region-blocked-unconfirmed',
  'region-blocked-everywhere', 'forbidden-unexplained']);

/** The provider's error code from a JSON body. Pure. Empty when absent. */
export function errorCode(body) {
  const error = (body && typeof body === 'object') ? body.error : null;
  if (!error || typeof error !== 'object') return '';
  for (const field of ['code', 'type']) {
    if (error[field]) return String(error[field]).trim();
  }
  return '';
}

/** One probe result, reduced. Pure. The only thing that leaves the process. */
export function observation(provider, status, body) {
  return {
    provider: String(provider),
    status: (status === null || status === undefined) ? null : Math.trunc(Number(status)),
    code: String(errorCode(body) || ''),
  };
}

/** Grade one observation. Pure. Returns [state, detail]. */
export function classify(obs) {
  const row = obs ?? {};
  const code = String(row.code ?? '');
  if (row.status === null || row.status === undefined) {
    return ['unreachable',
      'no response at all, which is a network answer rather than a policy one'];
  }
  const status = Math.trunc(Number(row.status));
  if (status === 200) return ['reachable', 'this egress path is allowed for this key'];
  if (status === 403 && code === BLOCK_CODE) return ['region-blocked', BLOCK_CODE];
  if (status === 403) {
    return ['forbidden-other',
      `403 with code '${code || '(none returned)'}', which is not the documented `
      + 'geographic block'];
  }
  if (status === 401) return ['credentials', '401, which is the key and not the location'];
  if (status === 429) {
    return ['rate-limited',
      '429, so this host reaches the provider fine and the question is capacity '
      + 'rather than geography'];
  }
  return ['unexpected', `${status} with code '${code || '(none)'}'`];
}

/** The note. Pure. Returns [state, detail]. The only two-host function. */
export function compare(local, baseline) {
  const [localState, localDetail] = classify(local);
  const provider = (local ?? {}).provider ?? '(unknown)';
  if (!baseline) {
    if (localState === 'region-blocked') {
      return ['region-blocked-unconfirmed',
        `${provider}: 403 ${BLOCK_CODE} from this host. The code is documented, `
        + 'but with no baseline this has not been separated from an '
        + 'account-level restriction'];
    }
    if (localState === 'forbidden-other' || localState === 'credentials') {
      return ['no-baseline',
        `${provider}: ${localDetail}, and no baseline to compare it against. Run `
        + 'this from a host you trust first'];
    }
    return [localState === 'reachable' ? 'clear' : localState,
            `${provider}: ${localDetail}`];
  }

  const [baseState] = classify(baseline);
  if (localState === 'reachable') {
    return ['clear', `${provider}: 200 from this host, so the egress path is fine`];
  }
  if (localState === 'region-blocked' && baseState === 'reachable') {
    return ['geography-isolated',
      `${provider}: 403 here and 200 from the baseline host on the same key, so `
      + 'the difference is the egress path and not the credential'];
  }
  if (localState === 'region-blocked' && baseState === 'region-blocked') {
    return ['region-blocked-everywhere',
      `${provider}: 403 ${BLOCK_CODE} from both hosts, so this is the account or `
      + "an organization-level restriction rather than this deployment's location"];
  }
  if (localState === 'credentials' && baseState === 'credentials') {
    return ['credentials-not-geography',
      `${provider}: 401 from both hosts on the same key, which is the credential `
      + 'and not the location'];
  }
  if (localState === 'credentials') {
    return ['credentials-here-only',
      `${provider}: 401 here and ${baseState} from the baseline host. A key that `
      + 'authenticates elsewhere and not here is usually a different key in the '
      + 'environment, not a geographic block'];
  }
  if (localState === 'forbidden-other' && baseState === 'reachable') {
    return ['forbidden-unexplained',
      `${provider}: ${localDetail} here and 200 from the baseline host. The host `
      + 'is the difference; the code is not one this script can attribute'];
  }
  return ['inconclusive',
    `${provider}: ${localState} here, ${baseState} from the baseline host`];
}

/** The one line to carry to the other host. Pure. Sorted, and no secrets. */
export function blob(observations) {
  const payload = {};
  for (const obs of observations ?? []) {
    const row = obs ?? {};
    payload[String(row.provider)] = {
      code: String(row.code ?? ''),
      status: row.status ?? null,
    };
  }
  const sorted = {};
  for (const key of Object.keys(payload).sort()) {
    const inner = payload[key];
    sorted[key] = { code: inner.code, status: inner.status };
  }
  return JSON.stringify(sorted);
}

/** {provider: observation} from the blob. Pure. Empty object on anything odd. */
export function loadBaseline(raw) {
  let parsed;
  try {
    parsed = JSON.parse(String(raw ?? '').trim() || '{}');
  } catch {
    return {};
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {};
  const out = {};
  for (const [provider, row] of Object.entries(parsed)) {
    if (!row || typeof row !== 'object') continue;
    const raw_status = row.status;
    const status = (raw_status === null || raw_status === undefined
                    || !Number.isFinite(Number(raw_status)))
      ? null : Math.trunc(Number(raw_status));
    out[String(provider)] = { provider: String(provider), status,
                              code: String(row.code ?? '') };
  }
  return out;
}

/** The repair for one verdict. Pure. A region pin, never a proxy. */
export function repairLines(state) {
  const pin = "pin execution to a supported region. On Vercel, export const "
    + "config = { regions: ['iad1'] }. On Cloud Run, Lambda or a container, "
    + "redeploy in a supported region. On a VPN, turn it off.";
  const noProxy = 'do not route the provider host through another egress to get '
    + 'around this. Move the workload, not the packets.';
  if (state === 'geography-isolated') return [pin, noProxy];
  if (state === 'region-blocked-unconfirmed') {
    return ['run this same script from a host you already trust and paste its '
      + 'blob into LLM_EGRESS_BASELINE here. One 403 does not separate the '
      + 'location from the account.', pin];
  }
  if (state === 'region-blocked-everywhere') {
    return ['both hosts are refused, so moving this deployment will not help. '
      + "Check the organization's country and any access restriction on the "
      + 'account before touching infrastructure.'];
  }
  if (state === 'credentials-not-geography') {
    return ['not this note. The same key is refused from both hosts, which is a '
      + 'credential question: check that the key exists, is enabled, and belongs '
      + 'to the project you think it does.'];
  }
  if (state === 'credentials-here-only') {
    return ['compare the environment on the two hosts. A key that works from one '
      + 'machine and 401s from another is almost always a different value in the '
      + 'environment rather than a location.'];
  }
  if (state === 'forbidden-unexplained') {
    return ['record the error code exactly as printed and check the provider '
      + 'supported regions list for the country this host egresses from.', pin];
  }
  if (state === 'no-baseline') {
    return ['run this from a host you trust and set LLM_EGRESS_BASELINE to the '
      + 'blob it prints. Without the pair there is one status code and no '
      + 'conclusion.'];
  }
  return [];
}

async function probe(provider, key) {
  const spec = PROVIDERS[provider];
  const url = new URL(spec.url);
  url.searchParams.set('limit', '1');
  const headers = provider === 'openai'
    ? { Authorization: `Bearer ${key}` }
    : { 'x-api-key': key, 'anthropic-version': '2023-06-01' };
  try {
    const r = await fetch(url, { headers });
    let body = null;
    try { body = await r.json(); } catch { body = null; }
    return [r.status, body];
  } catch {
    return [null, null];
  }
}

async function main() {
  const present = Object.keys(PROVIDERS).sort()
    .filter((p) => process.env[PROVIDERS[p].env]);
  if (!present.length) {
    console.error('set OPENAI_API_KEY or ANTHROPIC_API_KEY. Both are used for '
                  + 'one read-only GET of /v1/models and nothing else');
    process.exitCode = 2;
    return;
  }
  const baseline = loadBaseline(process.env.LLM_EGRESS_BASELINE);
  const observations = [];
  let findings = 0;

  for (const provider of present) {
    const [status, body] = await probe(provider, process.env[PROVIDERS[provider].env]);
    const obs = observation(provider, status, body);
    observations.push(obs);
    const [state, detail] = classify(obs);
    console.log(`${provider.padEnd(11)} ${obs.status ?? '---'}  ${state.padEnd(14)} ${detail}`);

    const [verdict, why] = compare(obs, baseline[provider]);
    console.log(`${verdict.padEnd(20)} ${why}`);
    for (const line of repairLines(verdict)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(verdict)) findings += 1;
  }

  console.log(`baseline: ${blob(observations)}`);
  if (!Object.keys(baseline).length) {
    console.log('no baseline was supplied. Carry that line to the other host and '
                + 'run this again there');
  }
  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the pair the note is built on: the documented 403 here beside a 200 from the baseline host has to produce <code>geography-isolated</code>, and the detail has to say why the credential is ruled out. The second and third are the outcomes that hand the reading away &mdash; 403 from both hosts is the account, 401 from both is the key &mdash; because a diagnostic that can only reach its own conclusion is not a diagnostic. Then the single-observation case, which must refuse to conclude even when the code is the documented one. Then the blob, round-tripped and asserted to contain no credential, which is the one property that makes it safe to paste between machines. And last, an undocumented 403 graded as unexplained rather than pattern-matched into a cause the script cannot cite.",
"test_py_file": "test_llm_egress_region_probe.py",
"test_py": '''from llm_egress_region_probe import (BLOCK_CODE, blob, classify, compare,
                                     error_code, load_baseline, observation,
                                     repair_lines)


def blocked(provider="openai"):
    return observation(provider, 403,
                       {"error": {"message": "Country, region, or territory "
                                             "not supported.",
                                  "type": "invalid_request_error",
                                  "code": BLOCK_CODE}})


def ok(provider="openai"):
    return observation(provider, 200, {"data": [], "object": "list"})


def test_the_pair_is_what_turns_a_403_into_a_statement_about_geography():
    state, detail = compare(blocked(), ok())
    assert state == "geography-isolated"
    assert "not the credential" in detail
    lines = repair_lines(state)
    assert any("regions: ['iad1']" in line for line in lines)
    assert any("Move the workload, not the packets" in line for line in lines)
    # A repair that routes around the block is never printed.
    assert not any("proxy the" in line.lower() for line in lines)


def test_blocked_from_both_hosts_is_the_account_and_not_this_deployment():
    state, detail = compare(blocked(), blocked())
    assert state == "region-blocked-everywhere"
    assert "organization-level restriction" in detail
    assert any("moving this deployment will not help" in line
               for line in repair_lines(state))


def test_a_401_from_both_hosts_is_handed_to_the_credential_question():
    unauth = observation("openai", 401, {"error": {"code": "invalid_api_key"}})
    state, detail = compare(unauth, unauth)
    assert state == "credentials-not-geography"
    assert "not the location" in detail
    assert any("not this note" in line for line in repair_lines(state))

    state, _ = compare(unauth, ok())
    assert state == "credentials-here-only"
    assert any("different value in the environment" in line
               for line in repair_lines(state))


def test_one_observation_refuses_to_conclude_even_with_the_documented_code():
    state, detail = compare(blocked(), None)
    assert state == "region-blocked-unconfirmed"
    assert "has not been separated from an account-level restriction" in detail
    assert any("host you already trust" in line for line in repair_lines(state))
    assert compare(ok(), None)[0] == "clear"


def test_the_blob_round_trips_and_carries_no_credential():
    line = blob([blocked(), ok("anthropic")])
    assert "sk-" not in line and "api" not in line.lower().replace("api.", "")
    assert line == ('{"anthropic":{"code":"","status":200},'
                    '"openai":{"code":"unsupported_country_region_territory",'
                    '"status":403}}')
    back = load_baseline(line)
    assert classify(back["openai"])[0] == "region-blocked"
    assert classify(back["anthropic"])[0] == "reachable"
    # A mangled paste produces no baseline and an instruction, not a traceback.
    assert load_baseline("{not json") == {}
    assert load_baseline(None) == {}


def test_an_undocumented_403_is_recorded_rather_than_attributed():
    other = observation("anthropic", 403,
                        {"error": {"type": "permission_error",
                                   "message": "..."}})
    state, detail = classify(other)
    assert state == "forbidden-other"
    assert "permission_error" in detail
    verdict, why = compare(other, ok("anthropic"))
    assert verdict == "forbidden-unexplained"
    assert "not one this script can attribute" in why
    assert any("supported regions list" in line for line in repair_lines(verdict))


def test_bodies_are_read_in_either_envelope_and_odd_ones_do_not_raise():
    assert error_code({"error": {"code": "a", "type": "b"}}) == "a"
    assert error_code({"error": {"type": "b"}}) == "b"
    assert error_code({"error": "a string"}) == ""
    assert error_code(None) == ""
    assert observation("openai", None, None)["status"] is None
    assert classify(observation("openai", None, None))[0] == "unreachable"
    assert classify(observation("openai", 429, None))[0] == "rate-limited"
    assert repair_lines("clear") == []
''',
"test_js_file": "llm-egress-region-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { BLOCK_CODE, blob, classify, compare, errorCode, loadBaseline,
         observation, repairLines } from './llm-egress-region-probe.mjs';

const blocked = (provider = 'openai') => observation(provider, 403, {
  error: { message: 'Country, region, or territory not supported.',
           type: 'invalid_request_error', code: BLOCK_CODE },
});
const ok = (provider = 'openai') =>
  observation(provider, 200, { data: [], object: 'list' });

test('the pair is what turns a 403 into a statement about geography', () => {
  const [state, detail] = compare(blocked(), ok());
  assert.equal(state, 'geography-isolated');
  assert.ok(detail.includes('not the credential'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes("regions: ['iad1']")));
  assert.ok(lines.some((l) => l.includes('Move the workload, not the packets')));
  assert.ok(!lines.some((l) => l.toLowerCase().includes('proxy the')));
});

test('blocked from both hosts is the account and not this deployment', () => {
  const [state, detail] = compare(blocked(), blocked());
  assert.equal(state, 'region-blocked-everywhere');
  assert.ok(detail.includes('organization-level restriction'));
  assert.ok(repairLines(state).some((l) => l.includes('moving this deployment will not help')));
});

test('a 401 from both hosts is handed to the credential question', () => {
  const unauth = observation('openai', 401, { error: { code: 'invalid_api_key' } });
  const [state, detail] = compare(unauth, unauth);
  assert.equal(state, 'credentials-not-geography');
  assert.ok(detail.includes('not the location'));
  assert.ok(repairLines(state).some((l) => l.includes('not this note')));

  assert.equal(compare(unauth, ok())[0], 'credentials-here-only');
  assert.ok(repairLines('credentials-here-only')
    .some((l) => l.includes('different value in the environment')));
});

test('one observation refuses to conclude even with the documented code', () => {
  const [state, detail] = compare(blocked(), null);
  assert.equal(state, 'region-blocked-unconfirmed');
  assert.ok(detail.includes('has not been separated from an account-level restriction'));
  assert.ok(repairLines(state).some((l) => l.includes('host you already trust')));
  assert.equal(compare(ok(), null)[0], 'clear');
});

test('the blob round trips and carries no credential', () => {
  const line = blob([blocked(), ok('anthropic')]);
  assert.ok(!line.includes('sk-'));
  assert.equal(line, '{"anthropic":{"code":"","status":200},'
    + '"openai":{"code":"unsupported_country_region_territory","status":403}}');
  const back = loadBaseline(line);
  assert.equal(classify(back.openai)[0], 'region-blocked');
  assert.equal(classify(back.anthropic)[0], 'reachable');
  assert.deepEqual(loadBaseline('{not json'), {});
  assert.deepEqual(loadBaseline(null), {});
});

test('an undocumented 403 is recorded rather than attributed', () => {
  const other = observation('anthropic', 403,
    { error: { type: 'permission_error', message: '...' } });
  const [state, detail] = classify(other);
  assert.equal(state, 'forbidden-other');
  assert.ok(detail.includes('permission_error'));
  const [verdict, why] = compare(other, ok('anthropic'));
  assert.equal(verdict, 'forbidden-unexplained');
  assert.ok(why.includes('not one this script can attribute'));
  assert.ok(repairLines(verdict).some((l) => l.includes('supported regions list')));
});

test('bodies are read in either envelope and odd ones do not raise', () => {
  assert.equal(errorCode({ error: { code: 'a', type: 'b' } }), 'a');
  assert.equal(errorCode({ error: { type: 'b' } }), 'b');
  assert.equal(errorCode({ error: 'a string' }), '');
  assert.equal(errorCode(null), '');
  assert.equal(observation('openai', null, null).status, null);
  assert.equal(classify(observation('openai', null, null))[0], 'unreachable');
  assert.equal(classify(observation('openai', 429, null))[0], 'rate-limited');
  assert.deepEqual(repairLines('clear'), []);
});
''',
"faq": [
 ("Why can't the script just check what country the server is in?",
  "It could, by calling a third-party geolocation service, and it deliberately does not. That would add a network dependency, a privacy question and a second thing that can be wrong to a script whose entire purpose is to remove ambiguity. It would also answer the wrong question: what matters is not which country an IP database thinks the host is in, it is whether the provider will serve a request from it. The provider's own 403 is that answer, and it is authoritative in a way no lookup can be."),
 ("Is a 403 not just a permissions problem with the key?",
  "That is exactly the wrong turn this note exists to prevent, and it is why the script insists on two runs. A 403 read alone sends people to rotate the key, which changes nothing, and then to widen its scopes, which changes nothing and leaves a more powerful credential in production. The same key returning 200 from another host makes the credential impossible as an explanation. When the pair says the opposite, the script says so too: 401 from both hosts is named credentials-not-geography and pointed elsewhere."),
 ("Which regions are actually supported?",
  "It differs by provider and it changes, so the script does not carry a list. OpenAI documents the refusal as a 403 whose code is unsupported_country_region_territory and publishes its supported countries separately. Anthropic publishes a list of the countries, regions and territories it can support access from, with some entries carved out at sub-national level. Both are pages to check rather than constants to hardcode, and a script that shipped a copy of either would be wrong within a release or two."),
 ("The block only happens sometimes. Is that possible?",
  "Yes, and it is the most confusing version. Edge platforms run your function at whichever point of presence is nearest the user, so a single deployment can egress from several countries and the failure will correlate with your users' locations rather than with anything in your code. Run the probe from inside the same runtime rather than from a build step or a shell on the same account, and run it more than once. Intermittent is still a region pin; it just means more than one region is in play."),
 ("Why not confirm it from the usage report as well?",
  "Because a project with no requests in it is a genuinely ambiguous signal and there is already a note that grades it properly. Zero usage looks like a hard block, and it also looks like a dead credential, a deploy that never rolled out, or a feature nobody used. Folding that into this script would import an ambiguity it exists to remove, so it stays with the probe pair, where a 403 here and a 200 there means exactly one thing."),
],
"related": [REL_VERIFY, REL_VERSION, REL_GEO_COST],
"citations": [CITE_OAI_ERRORS, CITE_REGIONS, CITE_OAI_MODELS, CITE_MODELS_LIST],
},
]
