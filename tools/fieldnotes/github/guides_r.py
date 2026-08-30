#!/usr/bin/env python3
"""/github/ field notes, batch R — the writing.

The section's first four GraphQL notes. Every one of them reads the same
response envelope, so the work of this batch was keeping them from becoming
four descriptions of one object. Each owns a different part of it and stops
where the next one starts.

The first owns the status line. GraphQL answers 200 whether or not the query
worked, so a client that branches on `response.ok` walks straight past a
top-level `errors` array and hands `null` to code that expected a repository.
The finding is the disagreement between two predicates over one response, and
every case where `data` survives alongside the errors is handed to the second
note by name rather than absorbed.

The second owns `errors[].path`. A response can be partly right: fields the
token cannot see resolve to null and add an entry to `errors` while everything
else succeeds. That is a third outcome, not a softer failure, and its repair is
different — widen the token or record the field as unknown, never retry, never
aggregate. The distinction that carries the note is between a null that has a
matching errors entry, which was withheld, and a null that does not, which is
genuinely absent. Those two look identical in the data and mean opposite things.

The third owns the money. GraphQL is billed in points from a bucket that has
nothing to do with the REST `core` bucket, which is why a REST health check can
report green while every GraphQL call in the system is failing. The section
already publishes the REST buckets — the hourly `core` quota and the per-minute
secondary limit — and this note deliberately does not restate either. It reads
both buckets side by side purely to show they move independently, and converts
points into the only unit anybody can act on, which is how many more queries you
can send.

The fourth owns the query document. The node limit is computed from the
`first`/`last` values you asked for rather than from anything that exists, and it
is enforced before the query runs, so the whole thing can be decided from the
text. That script sends nothing at all by default: it parses, multiplies, and
prints the smaller number to use. It is the only note in the batch that needs no
token.

Queries only, never mutations. The GraphQL endpoint is POST for reads as well as
writes, because the document travels in the body, and that makes this the one
batch in the section where a POST is unavoidable. Every script here refuses a
document containing a mutation or a subscription before it opens a socket, and
every one of them prints its point cost before it spends a point.
"""

CITE_GQL_GUIDE = ("Using the GraphQL API — GitHub Docs",
                  "https://docs.github.com/en/graphql/guides/using-the-graphql-api")
CITE_GQL_FORMING = ("Forming calls with GraphQL — GitHub Docs",
                    "https://docs.github.com/en/graphql/guides/forming-calls-with-graphql")
CITE_GQL_INTRO = ("Introduction to GraphQL — GitHub Docs",
                  "https://docs.github.com/en/graphql/guides/introduction-to-graphql")
CITE_GQL_MIGRATE = ("Migrating from REST to GraphQL — GitHub Docs",
                    "https://docs.github.com/en/graphql/guides/migrating-from-rest-to-graphql")
CITE_GQL_RATE = ("Rate limits and node limits for the GraphQL API — GitHub Docs",
                 "https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api")
CITE_GQL_RESOURCE = ("Resource limitations — GitHub GraphQL API",
                     "https://docs.github.com/en/graphql/overview/resource-limitations")
CITE_SPEC_ERRORS = ("GraphQL specification: Errors",
                    "https://spec.graphql.org/October2021/#sec-Errors")
CITE_SPEC_RESPONSE = ("GraphQL specification: Response Format",
                      "https://spec.graphql.org/October2021/#sec-Response-Format")
CITE_REST_RATE_LIMIT = ("Rate limit — GitHub REST API",
                        "https://docs.github.com/en/rest/rate-limit/rate-limit")
CITE_REST_RATE_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                         "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_TOKEN_PERMS = ("Permissions required for fine-grained personal access tokens — GitHub Docs",
                    "https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens")
CITE_PAGINATION_GQL = ("Using pagination in the GraphQL API — GitHub Docs",
                       "https://docs.github.com/en/graphql/guides/using-pagination-in-the-graphql-api")

GUIDES = [

{
"slug": "graphql-200-with-errors",
"title": "GraphQL returns 200 with an errors array and null data",
"description": "The response is a 200, response.ok is true, and data.repository is null because the failure was written into the body instead of the status line.",
"h1": "GraphQL returns 200 with an errors array and null data",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github graphql returns 200 with errors",
             "graphql data null but status 200",
             "github graphql errors array not checked",
             "github api v4 error handling status code",
             "graphql cannot read property of null github"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The call succeeded. <code>response.ok</code> is <code>true</code>, the status is <code>200</code>, the body is valid JSON, and <code>data.repository</code> is <code>null</code>. Downstream something throws <code>Cannot read property 'name' of null</code>, or, far worse, nothing throws at all and the dashboard records that the repository has zero open pull requests. The reason is one line further down the body, in an <code>errors</code> array nobody wrote a branch for.",
"short_answer": """<p>GraphQL reports application failures in the response body, not in the status line. A query that hit a missing repository, a permission your token does not have, an exhausted point budget or a query too large to run still comes back as <code>200 OK</code> with <code>{"data": ..., "errors": [{"type": "...", "message": "..."}]}</code>. Error handling written around HTTP status codes sees a success and carries on.</p>
<p>Read <code>body.errors</code> before you touch <code>body.data</code>, on every single response, and branch on <code>errors[].type</code> rather than on the message text: <code>RATE_LIMITED</code> waits, <code>FORBIDDEN</code> alerts a human, <code>NOT_FOUND</code> marks the record missing, <code>MAX_NODE_LIMIT_EXCEEDED</code> means the query has to be reshaped and will never succeed on a retry. A non-empty <code>errors</code> array is the finding whatever the status says.</p>""",
"problem": """<p>This one is written by good habits rather than bad ones. Every REST client in the codebase checks the status code, because for REST that is the right thing to check, and the GraphQL client gets written by the same person on the same afternoon with the same shape: send it, check <code>res.ok</code>, parse the JSON, use the data. Nothing about that reads as wrong in review. The <code>errors</code> key is not in the happy-path response at all, so nobody who has only ever seen a working call knows it can be there.</p>
<p>It then holds up beautifully in development, where the token is your own and has every permission, the repository definitely exists, and the point budget is nowhere near spent. The first response that carries an <code>errors</code> array arrives in production, from a token that is deliberately narrower than yours, against a repository that got renamed last week.</p>
<p>What it looks like from the outside is not an error at all. If you are lucky it is a <code>TypeError</code> on a null, thrown three frames away from the request, with a stack trace that points at your own code and a logged status of 200 that makes the API look innocent. If you are unlucky the code is defensive in the wrong direction: it treats a null repository as an empty one, writes zero into the metrics table, and the number is wrong for months in a way that looks like a real decline in activity.</p>""",
"why": """<p><strong>The status code describes the transport, not the query.</strong> A 200 from <code>/graphql</code> means the endpoint received a document, parsed it and produced a response. It does not mean the response contains what you asked for. The GraphQL specification puts execution errors in a top-level <code>errors</code> entry in the response body precisely because a single document can fail in many places at once, which a single status code cannot express.</p>
<p><strong>Every interesting failure arrives this way.</strong> A repository your token cannot see, a repository that does not exist, an exhausted point budget, a query over the node limit, an internal error on GitHub's side: all of them are 200 responses with a typed entry in <code>errors</code>. The failures that do change the status line are the boring ones — 401 for a bad token, 502 for an outage — and those are the ones your status check already handles.</p>
<p><strong>The <code>type</code> field is the part to branch on.</strong> <code>NOT_FOUND</code>, <code>FORBIDDEN</code>, <code>RATE_LIMITED</code>, <code>MAX_NODE_LIMIT_EXCEEDED</code> and <code>INTERNAL</code> demand four genuinely different responses and one of them is "stop retrying, this query can never work". Matching on message text instead is fragile in the ordinary way, and it also loses the distinction between a failure that will clear on its own and one that will not.</p>
<p><strong>A 404 does not exist here, and that matters.</strong> The REST API answers 404 for a repository you cannot see as well as for one that is not there, which is <a href="/github/404-masking-403/">its own well-known trap</a>. GraphQL is better: it tells you <code>NOT_FOUND</code> or <code>FORBIDDEN</code> in the <code>type</code> field and it will happily tell you both about different fields of the same query. You only get that resolution if you read the array.</p>
<p><strong>Errors alongside surviving data are a different problem.</strong> When <code>data</code> is null and <code>errors</code> is non-empty, the whole query failed and this note is the one you want. When <code>data</code> is populated and <code>errors</code> is non-empty, some fields resolved and some did not, which is <a href="/github/graphql-partial-data-nulls/">partial success and a different repair</a>. This script separates the two and refuses to give advice about the second, because "the call failed, retry it" is the wrong instruction for a response that is nine tenths correct.</p>
<p><strong>The API cannot see your error handling.</strong> Nothing GitHub returns says whether your client reads <code>errors</code>. What a script can do is make the endpoint produce the shape on demand, print the two predicates side by side, and show you which one your code is using. That is the trap being demonstrated, not your bug being found, and the script says so.</p>""",
"steps": [
 {"h": "Send one query that is guaranteed to fail in the body",
  "body": """<p>Ask for a repository that does not exist, or one this token cannot see. One query, one point. What comes back is a <code>200</code>, a valid JSON body, <code>data.repository</code> set to <code>null</code> and an <code>errors</code> array with a <code>type</code> in it. That is the whole phenomenon in a single response, and it is much more convincing than reading about it.</p>"""},
 {"h": "Print both predicates over that one response",
  "body": """<p>Evaluate "the status is 200" and "the errors array is empty" against the same body and print both answers. On this response the first says success and the second says failure. Their disagreement is the finding, and it is the sentence that changes somebody's client, because it names the exact line that has to move.</p>"""},
 {"h": "Read the type, not the message",
  "body": """<p>Pull <code>errors[].type</code> out and map it to a behaviour before you write a handler. The script prints the mapping it recommends for each type it sees, so that <code>RATE_LIMITED</code> becomes a wait, <code>FORBIDDEN</code> becomes an alert to a human, <code>NOT_FOUND</code> becomes a recorded absence, and <code>MAX_NODE_LIMIT_EXCEEDED</code> becomes a query change rather than a retry loop that can never terminate.</p>"""},
 {"h": "Split total failure from partial success",
  "body": """<p>If <code>data</code> came back with real values in it alongside the errors, this is not a failed call and treating it as one throws away good data. The script labels that case separately and points at the partial-response note instead of pretending one rule covers both. Getting this boundary right is most of the value of reading the envelope at all.</p>"""},
 {"h": "Move the check to the front of the client and keep the run cheap",
  "body": """<p>Put the <code>errors</code> check in the one function that sends queries, before any caller sees a body, so it cannot be forgotten per call site. The audit itself costs one point per probe, two by default, out of 5,000 an hour. <code>GET /rate_limit</code> reports the GraphQL budget and does not consume any of it.</p>"""},
],
"verify": """<p>Once the client reads the envelope, the same probe reports the disagreement and the client no longer has it.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_envelope.py --repo acme/renamed-last-week
# point cost: 2 point(s) against the 5,000/hour GraphQL budget
# probe missing-repository: HTTP 200, errors=1, data present=no
# 200-with-errors-no-data: the status line says success and the body carries 1
# error(s) of type NOT_FOUND with no usable data
# status check passes: yes    envelope check passes: no    they disagree: yes
# repair: read body.errors before body.data and branch on errors[].type

# a probe that returns errors alongside real data is handed on, not absorbed
# 200-with-errors-and-data: 1 error(s) of type FORBIDDEN arrived with usable
# data, which is partial success and a different repair
# repair: see /github/graphql-partial-data-nulls/ -- do not retry this one</code></pre>""",
"code_intro": "One query per probe, sent to the GraphQL endpoint because that is the only way a document travels, and refused outright if the document contains a mutation or a subscription. Everything after the request is pure: the predicate a status-code client uses, the predicate a correct client uses, the disagreement between them, the error types lifted out of the body and the behaviour each one demands. The whole rule is therefore testable against recorded envelopes without a token, which is the point, because the envelopes you most need to handle are the ones you cannot conveniently produce.",
"py_file": "github_graphql_envelope.py",
"py": '''"""Show that a GraphQL 200 can carry an errors array a status check walks past.

Read only, and queries only. GitHub's GraphQL endpoint takes a document in the
request body, so a read is carried by POST there just as a write would be; that
is a transport detail, not a licence to write. This script sends queries and
refuses any document containing a mutation or a subscription before it opens a
socket. Nothing is written and the repair is printed rather than performed.

GraphQL reports application failures in the response body. A query that hit a
missing repository, a permission the token lacks, an exhausted point budget or a
query too large to run still returns 200 OK with an errors array beside a null
data field. Error handling written around HTTP status codes sees a success.

What this can and cannot see: the API has no idea whether your client reads the
errors array. What it can do is make the endpoint produce the shape on demand
and print both predicates over the same response so you can compare them against
your own code. That is the trap, not the fall.

Environment:

    GITHUB_TOKEN    a token with read access to the GraphQL API
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_envelope")

API = "https://api.github.com"
UA = "github-graphql-envelope/1.0"

# A simple query costs one point. Named because it is printed before anything is
# spent, and a reader comparing this against the documentation should find it in
# one place.
POINTS_PER_QUERY = 1

DEFAULT_QUERY = (
    "query($owner: String!, $name: String!) {"
    " repository(owner: $owner, name: $name) { name isPrivate } }"
)

# The behaviours the five documented error types actually demand. Two of these
# are retryable, one is a permission change, one is a query change that no
# amount of retrying will fix, and one is a fact about the world.
BEHAVIOUR = {
    "RATE_LIMITED": ("wait", "the point budget is spent. Wait for the reset that "
                             "GET /rate_limit reports and do not retry before it."),
    "FORBIDDEN": ("alert", "the token cannot see this. Retrying changes nothing; "
                           "a human has to widen the permission or accept the gap."),
    "NOT_FOUND": ("record-absent", "the resource is missing or invisible to this "
                                   "token. Record the absence; do not treat it as zero."),
    "MAX_NODE_LIMIT_EXCEEDED": ("reshape", "the query asks for too many nodes and "
                                           "will fail identically every time. Lower "
                                           "the first values and paginate."),
    "INTERNAL": ("retry-once", "a failure on GitHub's side. Retry once with backoff, "
                               "then give up and log the query."),
    "SERVICE_UNAVAILABLE": ("retry-once", "a transient failure on GitHub's side. "
                                          "Retry once with backoff."),
}


def strip_noise(document):
    """Remove GraphQL comments and string literals from a document. Pure.

    Written as a scanner rather than a regex because a hash inside a string
    literal is a legitimate character and a comment marker outside one, and a
    single pattern that gets that right is harder to read than this loop.
    """
    src = str(document or "")
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "#":
            while i < n and src[i] != "\\n":
                i += 1
            continue
        if src.startswith('"""', i):
            j = src.find('"""', i + 3)
            i = n if j < 0 else j + 3
            out.append(" ")
            continue
        if ch == '"':
            i += 1
            while i < n and src[i] != '"':
                i += 2 if src[i] == "\\\\" else 1
            i += 1
            out.append(" ")
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def operations(document):
    """The top-level operations in a document, in order. Pure.

    One entry per brace group at depth zero: "query", "mutation",
    "subscription" or "fragment". An anonymous document is the query shorthand.
    """
    src = strip_noise(document)
    ops, depth, word, declared = [], 0, "", None
    for ch in src + " ":
        if ch.isalnum() or ch == "_":
            word += ch
            continue
        if word:
            if depth == 0 and word in ("query", "mutation", "subscription", "fragment"):
                declared = word
            word = ""
        if ch == "{":
            if depth == 0:
                ops.append(declared or "query")
                declared = None
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
    return ops


def refusal(document):
    """Why this document will not be sent, or None if it is a read. Pure.

    The endpoint is the same one mutations go to, so the guard lives here rather
    than in a comment. A section that promises its scripts never write has to
    mean it on the one endpoint where writing is a body away.
    """
    ops = operations(document)
    if not ops:
        return "the document contains no operation to send."
    for kind in ("mutation", "subscription"):
        if kind in ops:
            return ("the document contains a %s. This script sends queries only: "
                    "a query is a read, and the section it belongs to promises "
                    "its scripts never write." % kind)
    return None


def status_says_ok(status):
    """The predicate a status-code client uses. Pure."""
    try:
        return 200 <= int(status) < 300
    except (TypeError, ValueError):
        return False


def envelope_says_ok(body):
    """The predicate a correct client uses. Pure."""
    if not isinstance(body, dict):
        return False
    return not body.get("errors")


def error_types(body):
    """The type of every entry in the errors array, in order. Pure.

    An entry with no type is reported as UNTYPED rather than dropped, because a
    handler keyed on type has to have something to fall through to.
    """
    if not isinstance(body, dict):
        return []
    out = []
    for err in body.get("errors") or []:
        if isinstance(err, dict):
            out.append(err.get("type") or "UNTYPED")
        else:
            out.append("UNTYPED")
    return out


def has_usable_data(body):
    """Whether any field in data resolved to something other than null. Pure."""
    if not isinstance(body, dict):
        return False
    data = body.get("data")
    if not isinstance(data, dict):
        return False
    return any(v is not None for v in data.values())


def predicates_disagree(status, body):
    """Whether a status check would pass on a response the envelope fails."""
    return status_says_ok(status) and not envelope_says_ok(body)


def behaviour_for(error_type):
    """What one error type demands of a client. Pure. Returns (action, detail)."""
    if error_type in BEHAVIOUR:
        return BEHAVIOUR[error_type]
    return ("log-verbatim",
            "an error type this script does not know. Log it verbatim and fail "
            "the call rather than guessing; new types get added over time.")


def classify(status, body):
    """Classify one response envelope. Pure. Returns (state, detail).

    The two states that both carry errors are kept apart on purpose. One is a
    call that failed and the other is a call that mostly worked, and giving the
    same advice for both throws away good data.
    """
    if not isinstance(body, dict):
        return ("unreadable",
                "the response was not a JSON object, so neither predicate can be "
                "evaluated over it.")
    if not status_says_ok(status):
        return ("transport-failure",
                "HTTP %s, which a status check already catches. The errors array "
                "is not where this one hides." % status)
    types = error_types(body)
    if not types:
        return ("200-clean",
                "the status line and the errors array agree that this worked. "
                "Both predicates pass, which on this response is agreement rather "
                "than proof that your client checks the second one.")
    if has_usable_data(body):
        return ("200-with-errors-and-data",
                "%d error(s) of type %s arrived with usable data, which is partial "
                "success and a different repair."
                % (len(types), ", ".join(sorted(set(types)))))
    return ("200-with-errors-no-data",
            "the status line says success and the body carries %d error(s) of type "
            "%s with no usable data."
            % (len(types), ", ".join(sorted(set(types)))))


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "200-with-errors-no-data":
        return ("read body.errors before body.data and branch on errors[].type. "
                "Put the check in the function that sends queries so no caller "
                "can skip it.")
    if state == "200-with-errors-and-data":
        return ("see /github/graphql-partial-data-nulls/ -- do not retry this "
                "one. Some fields resolved and discarding them because the call "
                "carried errors loses data that arrived correctly.")
    if state == "transport-failure":
        return ("handle the status code as you already do. This note is about "
                "the failures that arrive as a 200.")
    if state == "200-clean":
        return ("nothing on this response. Check that the errors array is read "
                "at all: the two predicates agree here and part company on the "
                "first failure.")
    return "point the check at a document this endpoint can answer."


def point_cost(probes):
    """Points this run will spend against the GraphQL budget. Pure."""
    return len(probes or []) * POINTS_PER_QUERY


def run_query(session, document, variables):
    """Send one query. Returns (status, body-or-None).

    A GraphQL query is a read; POST is only how the document reaches the
    endpoint, which is why the verb is written here beside the URL rather than
    tucked into a constant where it could be mistaken for a write path.
    """
    r = session.post(API + "/graphql",
                     json={"query": document, "variables": variables or {}},
                     timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True,
                    help="owner/name to probe. A repository that does not exist "
                         "is the cheapest way to see the shape.")
    ap.add_argument("--query",
                    help="send your own query document instead of the default. "
                         "Mutations and subscriptions are refused.")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    try:
        owner, name = args.repo.split("/", 1)
    except ValueError:
        log.error("--repo takes owner/name")
        return 2

    document = args.query or DEFAULT_QUERY
    why_not = refusal(document)
    if why_not:
        log.error("refusing to send: %s", why_not)
        return 2

    probes = [
        ("missing-repository", document,
         {"owner": owner, "name": name + "-does-not-exist-probe"}),
        ("as-configured", document, {"owner": owner, "name": name}),
    ]
    log.info("point cost: %d point(s) against the 5,000/hour GraphQL budget",
             point_cost(probes))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    findings = []
    for label, doc, variables in probes:
        status, body = run_query(session, doc, variables)
        state, detail = classify(status, body)
        types = error_types(body)
        log.info("probe %s: HTTP %s, errors=%d, data present=%s",
                 label, status, len(types), "yes" if has_usable_data(body) else "no")
        log.info("%s: %s", state, detail)
        log.info("status check passes: %s    envelope check passes: %s    "
                 "they disagree: %s",
                 "yes" if status_says_ok(status) else "no",
                 "yes" if envelope_says_ok(body) else "no",
                 "yes" if predicates_disagree(status, body) else "no")
        for t in sorted(set(types)):
            action, why = behaviour_for(t)
            log.info("  %s -> %s: %s", t, action, why)
        log.info("repair: %s", repair(state))

        findings.append({
            "probe": label,
            "status": status,
            "error_types": types,
            "has_usable_data": has_usable_data(body),
            "status_check_passes": status_says_ok(status),
            "envelope_check_passes": envelope_says_ok(body),
            "predicates_disagree": predicates_disagree(status, body),
            "behaviours": {t: behaviour_for(t)[0] for t in sorted(set(types))},
            "state": state,
            "detail": detail,
        })

    print(json.dumps({"points_spent": point_cost(probes), "findings": findings},
                     indent=2, default=str))
    return 1 if any(f["predicates_disagree"] for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-envelope.mjs",
"js": '''/**
 * Show that a GraphQL 200 can carry an errors array a status check walks past.
 *
 * Read only, and queries only. GitHub's GraphQL endpoint takes a document in
 * the request body, so a read is carried by POST there just as a write would
 * be; that is a transport detail, not a licence to write. Any document
 * containing a mutation or a subscription is refused before a socket opens.
 *
 * Environment:
 *   GITHUB_TOKEN   a token with read access to the GraphQL API
 *   GITHUB_REPO    owner/name to probe
 *   GITHUB_QUERY   send your own query document instead of the default
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-envelope/1.0';

/** A simple query costs one point. */
export const POINTS_PER_QUERY = 1;

const DEFAULT_QUERY = 'query($owner: String!, $name: String!) {'
  + ' repository(owner: $owner, name: $name) { name isPrivate } }';

/** The behaviours the documented error types actually demand. */
export const BEHAVIOUR = {
  RATE_LIMITED: ['wait', 'the point budget is spent. Wait for the reset that '
    + 'GET /rate_limit reports and do not retry before it.'],
  FORBIDDEN: ['alert', 'the token cannot see this. Retrying changes nothing; a '
    + 'human has to widen the permission or accept the gap.'],
  NOT_FOUND: ['record-absent', 'the resource is missing or invisible to this '
    + 'token. Record the absence; do not treat it as zero.'],
  MAX_NODE_LIMIT_EXCEEDED: ['reshape', 'the query asks for too many nodes and '
    + 'will fail identically every time. Lower the first values and paginate.'],
  INTERNAL: ['retry-once', "a failure on GitHub's side. Retry once with "
    + 'backoff, then give up and log the query.'],
  SERVICE_UNAVAILABLE: ['retry-once', "a transient failure on GitHub's side. "
    + 'Retry once with backoff.'],
};

/** Remove GraphQL comments and string literals from a document. Pure. */
export function stripNoise(document) {
  const src = String(document ?? '');
  const out = [];
  let i = 0;
  while (i < src.length) {
    const ch = src[i];
    if (ch === '#') {
      while (i < src.length && src[i] !== '\\n') i += 1;
      continue;
    }
    if (src.startsWith('"""', i)) {
      const j = src.indexOf('"""', i + 3);
      i = j < 0 ? src.length : j + 3;
      out.push(' ');
      continue;
    }
    if (ch === '"') {
      i += 1;
      while (i < src.length && src[i] !== '"') i += src[i] === '\\\\' ? 2 : 1;
      i += 1;
      out.push(' ');
      continue;
    }
    out.push(ch);
    i += 1;
  }
  return out.join('');
}

/** The top-level operations in a document, in order. Pure. */
export function operations(document) {
  const src = `${stripNoise(document)} `;
  const ops = [];
  let depth = 0;
  let word = '';
  let declared = null;
  for (const ch of src) {
    if (/[A-Za-z0-9_]/.test(ch)) { word += ch; continue; }
    if (word) {
      if (depth === 0 && ['query', 'mutation', 'subscription', 'fragment'].includes(word)) {
        declared = word;
      }
      word = '';
    }
    if (ch === '{') {
      if (depth === 0) { ops.push(declared || 'query'); declared = null; }
      depth += 1;
    } else if (ch === '}') {
      depth = Math.max(0, depth - 1);
    }
  }
  return ops;
}

/** Why this document will not be sent, or null if it is a read. Pure. */
export function refusal(document) {
  const ops = operations(document);
  if (ops.length === 0) return 'the document contains no operation to send.';
  for (const kind of ['mutation', 'subscription']) {
    if (ops.includes(kind)) {
      return `the document contains a ${kind}. This script sends queries only: `
        + 'a query is a read, and the section it belongs to promises its '
        + 'scripts never write.';
    }
  }
  return null;
}

/** The predicate a status-code client uses. Pure. */
export function statusSaysOk(status) {
  const n = Number(status);
  return Number.isFinite(n) && n >= 200 && n < 300;
}

/** The predicate a correct client uses. Pure. */
export function envelopeSaysOk(body) {
  if (!body || typeof body !== 'object') return false;
  return !(Array.isArray(body.errors) && body.errors.length > 0);
}

/** The type of every entry in the errors array, in order. Pure. */
export function errorTypes(body) {
  if (!body || typeof body !== 'object' || !Array.isArray(body.errors)) return [];
  return body.errors.map((e) => (e && typeof e === 'object' && e.type) || 'UNTYPED');
}

/** Whether any field in data resolved to something other than null. Pure. */
export function hasUsableData(body) {
  if (!body || typeof body !== 'object') return false;
  const data = body.data;
  if (!data || typeof data !== 'object' || Array.isArray(data)) return false;
  return Object.values(data).some((v) => v !== null && v !== undefined);
}

/** Whether a status check would pass on a response the envelope fails. Pure. */
export function predicatesDisagree(status, body) {
  return statusSaysOk(status) && !envelopeSaysOk(body);
}

/** What one error type demands of a client. Pure. Returns [action, detail]. */
export function behaviourFor(errorType) {
  if (Object.prototype.hasOwnProperty.call(BEHAVIOUR, errorType)) {
    return BEHAVIOUR[errorType];
  }
  return ['log-verbatim', 'an error type this script does not know. Log it '
    + 'verbatim and fail the call rather than guessing; new types get added '
    + 'over time.'];
}

/** Classify one response envelope. Pure. Returns [state, detail]. */
export function classify(status, body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return ['unreadable', 'the response was not a JSON object, so neither '
      + 'predicate can be evaluated over it.'];
  }
  if (!statusSaysOk(status)) {
    return ['transport-failure', `HTTP ${status}, which a status check already `
      + 'catches. The errors array is not where this one hides.'];
  }
  const types = errorTypes(body);
  if (types.length === 0) {
    return ['200-clean', 'the status line and the errors array agree that this '
      + 'worked. Both predicates pass, which on this response is agreement '
      + 'rather than proof that your client checks the second one.'];
  }
  const named = [...new Set(types)].sort().join(', ');
  if (hasUsableData(body)) {
    return ['200-with-errors-and-data',
      `${types.length} error(s) of type ${named} arrived with usable data, `
      + 'which is partial success and a different repair.'];
  }
  return ['200-with-errors-no-data',
    `the status line says success and the body carries ${types.length} error(s) `
    + `of type ${named} with no usable data.`];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === '200-with-errors-no-data') {
    return 'read body.errors before body.data and branch on errors[].type. Put '
      + 'the check in the function that sends queries so no caller can skip it.';
  }
  if (state === '200-with-errors-and-data') {
    return 'see /github/graphql-partial-data-nulls/ -- do not retry this one. '
      + 'Some fields resolved and discarding them because the call carried '
      + 'errors loses data that arrived correctly.';
  }
  if (state === 'transport-failure') {
    return 'handle the status code as you already do. This note is about the '
      + 'failures that arrive as a 200.';
  }
  if (state === '200-clean') {
    return 'nothing on this response. Check that the errors array is read at '
      + 'all: the two predicates agree here and part company on the first '
      + 'failure.';
  }
  return 'point the check at a document this endpoint can answer.';
}

/** Points this run will spend against the GraphQL budget. Pure. */
export function pointCost(probes) {
  return (Array.isArray(probes) ? probes.length : 0) * POINTS_PER_QUERY;
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'Content-Type': 'application/json',
    'User-Agent': UA,
  };
}

async function runQuery(token, document, variables) {
  const res = await fetch(`${API}/graphql`, {
    // A GraphQL query is a read. POST is only how the document reaches the
    // endpoint, and refusal() has already rejected anything that is not a read.
    method: 'POST',
    headers: headers(token),
    body: JSON.stringify({ query: document, variables: variables || {} }),
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  if (!token || !repo) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPO=owner/name');
    process.exitCode = 2;
    return;
  }
  const [owner, name] = repo.split('/');
  if (!owner || !name) {
    console.error('GITHUB_REPO takes owner/name');
    process.exitCode = 2;
    return;
  }
  const document = process.env.GITHUB_QUERY || DEFAULT_QUERY;
  const whyNot = refusal(document);
  if (whyNot) {
    console.error(`refusing to send: ${whyNot}`);
    process.exitCode = 2;
    return;
  }

  const probes = [
    ['missing-repository', { owner, name: `${name}-does-not-exist-probe` }],
    ['as-configured', { owner, name }],
  ];
  console.log(`point cost: ${pointCost(probes)} point(s) against the 5,000/hour GraphQL budget`);

  const findings = [];
  for (const [label, variables] of probes) {
    const { status, body } = await runQuery(token, document, variables);
    const [state, detail] = classify(status, body);
    const types = errorTypes(body);
    console.log(`probe ${label}: HTTP ${status}, errors=${types.length}, `
      + `data present=${hasUsableData(body) ? 'yes' : 'no'}`);
    console.log(`${state}: ${detail}`);
    console.log(`status check passes: ${statusSaysOk(status) ? 'yes' : 'no'}    `
      + `envelope check passes: ${envelopeSaysOk(body) ? 'yes' : 'no'}    `
      + `they disagree: ${predicatesDisagree(status, body) ? 'yes' : 'no'}`);
    for (const t of [...new Set(types)].sort()) {
      const [action, why] = behaviourFor(t);
      console.log(`  ${t} -> ${action}: ${why}`);
    }
    console.log(`repair: ${repair(state)}`);

    findings.push({
      probe: label,
      status,
      error_types: types,
      has_usable_data: hasUsableData(body),
      status_check_passes: statusSaysOk(status),
      envelope_check_passes: envelopeSaysOk(body),
      predicates_disagree: predicatesDisagree(status, body),
      state,
      detail,
    });
  }

  console.log(JSON.stringify({ points_spent: pointCost(probes), findings }, null, 2));
  process.exitCode = findings.some((f) => f.predicates_disagree) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Most of the suite is envelopes: a 200 with errors and no data, a 200 with errors and real data beside them, a clean 200, a genuine transport failure and a body that is not an object at all. The two predicates are asserted separately and then asserted to disagree on exactly one of those shapes, because the disagreement is the note. After that, the error-type mapping, including the fall-through for a type that did not exist when this was written, the refusal that keeps a mutation off the wire, and the point cost, which is asserted because a script that prints a number before spending it should be held to the number.",
"test_py_file": "test_github_graphql_envelope.py",
"test_py": '''from github_graphql_envelope import (
    POINTS_PER_QUERY, behaviour_for, classify, envelope_says_ok, error_types,
    has_usable_data, operations, point_cost, predicates_disagree, refusal,
    repair, status_says_ok,
)

FAILED = {"data": {"repository": None},
          "errors": [{"type": "NOT_FOUND", "message": "Could not resolve to a Repository"}]}
PARTIAL = {"data": {"repository": {"name": "monorepo", "diskUsage": None}},
           "errors": [{"type": "FORBIDDEN", "path": ["repository", "diskUsage"]}]}
CLEAN = {"data": {"repository": {"name": "monorepo"}}}


def test_the_status_line_says_success_on_a_failed_query():
    assert status_says_ok(200)
    assert status_says_ok("201")
    assert not status_says_ok(403)
    assert not status_says_ok(None)


def test_the_envelope_check_reads_the_body_instead():
    assert not envelope_says_ok(FAILED)
    assert not envelope_says_ok(PARTIAL)
    assert envelope_says_ok(CLEAN)
    assert envelope_says_ok({"data": {}, "errors": []})
    assert not envelope_says_ok("not a body")


def test_the_finding_is_exactly_the_disagreement():
    assert predicates_disagree(200, FAILED)
    assert predicates_disagree(200, PARTIAL)
    assert not predicates_disagree(200, CLEAN)
    assert not predicates_disagree(502, FAILED)


def test_error_types_survive_an_entry_with_no_type():
    assert error_types(FAILED) == ["NOT_FOUND"]
    assert error_types({"errors": [{"message": "boom"}]}) == ["UNTYPED"]
    assert error_types({"errors": ["a string"]}) == ["UNTYPED"]
    assert error_types(CLEAN) == []


def test_usable_data_means_at_least_one_field_resolved():
    assert not has_usable_data(FAILED)
    assert has_usable_data(PARTIAL)
    assert has_usable_data(CLEAN)
    assert not has_usable_data({"data": None, "errors": [{"type": "RATE_LIMITED"}]})


def test_a_200_carrying_errors_and_no_data_is_the_headline():
    state, detail = classify(200, FAILED)
    assert state == "200-with-errors-no-data"
    assert "NOT_FOUND" in detail
    assert "read body.errors before body.data" in repair(state)


def test_errors_alongside_real_data_are_handed_on_rather_than_absorbed():
    state, detail = classify(200, PARTIAL)
    assert state == "200-with-errors-and-data"
    assert "partial success" in detail
    assert "graphql-partial-data-nulls" in repair(state)
    assert "do not retry" in repair(state)


def test_a_real_transport_failure_is_not_this_note():
    state, _detail = classify(502, {"errors": [{"type": "INTERNAL"}]})
    assert state == "transport-failure"
    assert "status code as you already do" in repair(state)


def test_a_clean_response_is_not_reported_as_proof_of_anything():
    state, detail = classify(200, CLEAN)
    assert state == "200-clean"
    assert "agreement rather than proof" in detail


def test_an_unreadable_body_is_not_reported_as_success():
    assert classify(200, None)[0] == "unreadable"
    assert classify(200, [1, 2])[0] == "unreadable"


def test_each_error_type_gets_its_own_behaviour():
    assert behaviour_for("RATE_LIMITED")[0] == "wait"
    assert behaviour_for("FORBIDDEN")[0] == "alert"
    assert behaviour_for("NOT_FOUND")[0] == "record-absent"
    assert behaviour_for("MAX_NODE_LIMIT_EXCEEDED")[0] == "reshape"
    assert behaviour_for("INTERNAL")[0] == "retry-once"


def test_a_node_limit_error_is_never_advised_to_retry():
    action, detail = behaviour_for("MAX_NODE_LIMIT_EXCEEDED")
    assert action == "reshape"
    assert "fail identically every time" in detail


def test_an_unknown_error_type_falls_through_rather_than_being_guessed():
    action, detail = behaviour_for("SOMETHING_NEW_IN_2027")
    assert action == "log-verbatim"
    assert "does not know" in detail


def test_the_script_refuses_to_send_a_mutation():
    assert operations("query Q { viewer { login } }") == ["query"]
    assert operations("{ viewer { login } }") == ["query"]
    assert operations("mutation M { addStar(input: {}) { clientMutationId } }") == ["mutation"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal("subscription S { thing { id } }")
    assert refusal("") == "the document contains no operation to send."
    assert refusal("query Q { viewer { login } }") is None


def test_the_word_mutation_inside_a_string_is_not_a_mutation():
    doc = 'query Q { search(query: "mutation", type: ISSUE, first: 1) { issueCount } }'
    assert operations(doc) == ["query"]
    assert refusal(doc) is None


def test_a_commented_out_mutation_is_not_sent_and_not_feared():
    doc = "# mutation M { addStar }\\nquery Q { viewer { login } }"
    assert operations(doc) == ["query"]
    assert refusal(doc) is None


def test_the_run_says_what_it_will_spend():
    assert POINTS_PER_QUERY == 1
    assert point_cost([1, 2]) == 2
    assert point_cost([]) == 0
    assert point_cost(None) == 0
''',
"test_js_file": "github-graphql-envelope.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  POINTS_PER_QUERY, behaviourFor, classify, envelopeSaysOk, errorTypes,
  hasUsableData, operations, pointCost, predicatesDisagree, refusal, repair,
  statusSaysOk,
} from './github-graphql-envelope.mjs';

const FAILED = {
  data: { repository: null },
  errors: [{ type: 'NOT_FOUND', message: 'Could not resolve to a Repository' }],
};
const PARTIAL = {
  data: { repository: { name: 'monorepo', diskUsage: null } },
  errors: [{ type: 'FORBIDDEN', path: ['repository', 'diskUsage'] }],
};
const CLEAN = { data: { repository: { name: 'monorepo' } } };

test('the status line says success on a failed query', () => {
  assert.ok(statusSaysOk(200));
  assert.ok(statusSaysOk('201'));
  assert.ok(!statusSaysOk(403));
  assert.ok(!statusSaysOk(null));
});

test('the envelope check reads the body instead', () => {
  assert.ok(!envelopeSaysOk(FAILED));
  assert.ok(!envelopeSaysOk(PARTIAL));
  assert.ok(envelopeSaysOk(CLEAN));
  assert.ok(envelopeSaysOk({ data: {}, errors: [] }));
  assert.ok(!envelopeSaysOk('not a body'));
});

test('the finding is exactly the disagreement', () => {
  assert.ok(predicatesDisagree(200, FAILED));
  assert.ok(predicatesDisagree(200, PARTIAL));
  assert.ok(!predicatesDisagree(200, CLEAN));
  assert.ok(!predicatesDisagree(502, FAILED));
});

test('error types survive an entry with no type', () => {
  assert.deepEqual(errorTypes(FAILED), ['NOT_FOUND']);
  assert.deepEqual(errorTypes({ errors: [{ message: 'boom' }] }), ['UNTYPED']);
  assert.deepEqual(errorTypes({ errors: ['a string'] }), ['UNTYPED']);
  assert.deepEqual(errorTypes(CLEAN), []);
});

test('usable data means at least one field resolved', () => {
  assert.ok(!hasUsableData(FAILED));
  assert.ok(hasUsableData(PARTIAL));
  assert.ok(hasUsableData(CLEAN));
  assert.ok(!hasUsableData({ data: null, errors: [{ type: 'RATE_LIMITED' }] }));
});

test('a 200 carrying errors and no data is the headline', () => {
  const [state, detail] = classify(200, FAILED);
  assert.equal(state, '200-with-errors-no-data');
  assert.match(detail, /NOT_FOUND/);
  assert.match(repair(state), /read body\\.errors before body\\.data/);
});

test('errors alongside real data are handed on rather than absorbed', () => {
  const [state, detail] = classify(200, PARTIAL);
  assert.equal(state, '200-with-errors-and-data');
  assert.match(detail, /partial success/);
  assert.match(repair(state), /graphql-partial-data-nulls/);
  assert.match(repair(state), /do not retry/);
});

test('a real transport failure is not this note', () => {
  const [state] = classify(502, { errors: [{ type: 'INTERNAL' }] });
  assert.equal(state, 'transport-failure');
  assert.match(repair(state), /status code as you already do/);
});

test('a clean response is not reported as proof of anything', () => {
  const [state, detail] = classify(200, CLEAN);
  assert.equal(state, '200-clean');
  assert.match(detail, /agreement rather than proof/);
});

test('an unreadable body is not reported as success', () => {
  assert.equal(classify(200, null)[0], 'unreadable');
  assert.equal(classify(200, [1, 2])[0], 'unreadable');
});

test('each error type gets its own behaviour', () => {
  assert.equal(behaviourFor('RATE_LIMITED')[0], 'wait');
  assert.equal(behaviourFor('FORBIDDEN')[0], 'alert');
  assert.equal(behaviourFor('NOT_FOUND')[0], 'record-absent');
  assert.equal(behaviourFor('MAX_NODE_LIMIT_EXCEEDED')[0], 'reshape');
  assert.equal(behaviourFor('INTERNAL')[0], 'retry-once');
});

test('a node limit error is never advised to retry', () => {
  const [action, detail] = behaviourFor('MAX_NODE_LIMIT_EXCEEDED');
  assert.equal(action, 'reshape');
  assert.match(detail, /fail identically every time/);
});

test('an unknown error type falls through rather than being guessed', () => {
  const [action, detail] = behaviourFor('SOMETHING_NEW_IN_2027');
  assert.equal(action, 'log-verbatim');
  assert.match(detail, /does not know/);
});

test('the script refuses to send a mutation', () => {
  assert.deepEqual(operations('query Q { viewer { login } }'), ['query']);
  assert.deepEqual(operations('{ viewer { login } }'), ['query']);
  assert.deepEqual(
    operations('mutation M { addStar(input: {}) { clientMutationId } }'),
    ['mutation'],
  );
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.ok(refusal('subscription S { thing { id } }'));
  assert.equal(refusal(''), 'the document contains no operation to send.');
  assert.equal(refusal('query Q { viewer { login } }'), null);
});

test('the word mutation inside a string is not a mutation', () => {
  const doc = 'query Q { search(query: "mutation", type: ISSUE, first: 1) { issueCount } }';
  assert.deepEqual(operations(doc), ['query']);
  assert.equal(refusal(doc), null);
});

test('a commented out mutation is not sent and not feared', () => {
  const doc = '# mutation M { addStar }\\nquery Q { viewer { login } }';
  assert.deepEqual(operations(doc), ['query']);
  assert.equal(refusal(doc), null);
});

test('the run says what it will spend', () => {
  assert.equal(POINTS_PER_QUERY, 1);
  assert.equal(pointCost([1, 2]), 2);
  assert.equal(pointCost([]), 0);
  assert.equal(pointCost(null), 0);
});
''',
"faq": [
 ("Why does GitHub not return a 4xx when the query fails?",
  "Because one GraphQL document can succeed and fail at the same time. A query over fifty repositories can resolve forty-two of them and be forbidden on eight, and there is no status code that means that. The specification puts execution errors in the body so that a response can carry both outcomes at once, and GitHub follows it. The consequence for you is that the status line stops being the place to look: 401 and 502 still mean what they always meant, and everything else that goes wrong arrives as a 200."),
 ("Should I just throw whenever the errors array is non-empty?",
  "For a total failure, yes. For a response that also carries usable data, no, and that is why this script separates the two states rather than treating them as one. Throwing away forty-two resolved repositories because eight were forbidden turns a partial answer into no answer, and re-running the query costs points and returns the same shape. The rule that holds in both cases is narrower: never touch data without having read errors first, and never aggregate over a response whose errors array is non-empty without recording that you did."),
 ("Can I branch on the error message instead of the type?",
  "You can, and it will break. Messages are written for humans and get reworded; the type field is the machine-readable classification and it is what the documented behaviours attach to. The type also carries a distinction the message tends to blur, which is whether retrying can ever help: RATE_LIMITED clears by itself, INTERNAL might, and MAX_NODE_LIMIT_EXCEEDED never will, because the query is the problem and it has not changed. A retry loop keyed on message text will happily spin on that last one until the point budget is gone."),
 ("How much does this check cost?",
  "One point per probe, two by default, out of a budget of 5,000 points an hour for a user token. The script computes and prints that number before it sends anything, so pointing it at a list of repositories is a decision rather than an accident. If you want to know what is left before you start, GET /rate_limit reports the GraphQL bucket and does not itself consume any of it, which is a separate bucket from the REST one and has its own note."),
 ("Does the script ever write anything?",
  "No. The GraphQL endpoint is reached by POST for queries as well as mutations, because the document travels in the request body rather than in the path, so the verb here is transport rather than intent. The script makes that explicit rather than relying on the reader to know it: it parses the document, lists its top-level operations, and refuses to open a socket at all if any of them is a mutation or a subscription. The word appearing inside a string literal or a comment is not treated as one."),
],
"related": [
 ("/github/graphql-partial-data-nulls/", "GraphQL fields come back null one at a time"),
 ("/github/graphql-rate-limited/", "GraphQL points run out in their own bucket"),
 ("/github/404-masking-403/", "A 404 that is really a permission problem"),
],
"citations": [CITE_GQL_GUIDE, CITE_SPEC_ERRORS, CITE_SPEC_RESPONSE, CITE_GQL_FORMING],
},

{
"slug": "graphql-partial-data-nulls",
"title": "GraphQL data is present but individual fields are null",
"description": "A query over 50 repositories returns 50 objects and eight of them have null where a private field should be. Nothing throws and the totals under-count.",
"h1": "GraphQL data is present but individual fields are null",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github graphql null fields permissions",
             "graphql partial data errors path",
             "github graphql forbidden field null",
             "graphql errors path null field github",
             "github graphql resource not accessible by personal access token"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The query asked for fifty repositories and fifty came back. Nothing threw, nothing logged, the job took the usual eleven seconds. Eight of the fifty have <code>null</code> where <code>diskUsage</code> should be, because the token cannot read that field on a private repository, and the total that gets written to the dashboard is the sum of forty-two numbers presented as the sum of fifty. The response told you which eight, in an <code>errors</code> array that arrived alongside perfectly good data.",
"short_answer": """<p>GraphQL resolves every field independently. A field your token cannot see resolves to <code>null</code> and adds an entry to the top-level <code>errors</code> array with a <code>type</code> and, crucially, a <code>path</code> pointing at the exact field that was nulled. Everything else in the query succeeds. The response is genuinely partial by design, and it is a third outcome rather than a softer kind of failure.</p>
<p>The repair is not a retry, because the same token will produce the same nulls forever. Walk <code>errors[].path</code>, mark those fields <strong>unknown</strong> rather than zero, and refuse to publish an aggregate computed across them without saying how many were withheld. Then decide whether to widen the token or to accept the gap. The distinction that matters is between a null that has a matching entry in <code>errors</code>, which was withheld from you, and a null that has none, which is genuinely empty.</p>""",
"problem": """<p>The client that hits this has usually already been fixed once. Somebody found out the hard way that a 200 can carry errors, added a check, and made it throw. That check is right for a response where <code>data</code> is null and wrong for this one, because throwing here discards forty-two repositories that resolved perfectly in order to react to eight that did not. So the check gets softened to a warning, the warning goes to a log nobody reads, and the aggregation runs over the whole array as though nothing happened.</p>
<p>The reason it stays hidden is that a null is a perfectly ordinary value in this API. A repository with no license has a null <code>licenseInfo</code>. An unassigned issue has a null assignee. Code that walks a response is full of null handling already, and one more null looks like all the others. There is no visual difference between a field that is empty and a field you were not allowed to read; the difference is recorded somewhere else entirely, in an array most code never looks at.</p>
<p>What it produces is the worst kind of wrong number: a plausible one. Not zero, not an exception, just a total that is quietly sixteen per cent low and moves whenever somebody makes a repository private. The finance-adjacent version of this is a storage report that under-bills. The security-adjacent version is a vulnerability count that misses the repositories the token cannot see, which are disproportionately the ones you would most want counted.</p>""",
"why": """<p><strong>Field-level resolution is the whole design.</strong> A GraphQL server resolves each field on its own, so a permission failure on one field does not fail the document. The failed field takes the value <code>null</code> in <code>data</code> and contributes an entry to <code>errors</code>. That is the specification working as intended, and it is exactly why a client cannot decide anything from <code>data</code> alone.</p>
<p><strong><code>path</code> is the field that makes this actionable.</strong> Every execution error that belongs to a field carries a <code>path</code> array naming the route to it, list indices included, so <code>["repository", "pullRequests", "nodes", 3, "author"]</code> tells you which element of which connection was withheld. Without reading <code>path</code> you know only that something went wrong somewhere; with it you know precisely which cells of your result set are unknown.</p>
<p><strong>A null with an errors entry and a null without one mean opposite things.</strong> The first was withheld and its true value is unknown. The second is a real answer: the repository genuinely has no license, the issue genuinely has no milestone. Treating the first as the second is what produces the under-count, and it is the single distinction this script exists to draw. Every null it reports is labelled as one or the other, never as "a null".</p>
<p><strong>This is not the note about a call that failed.</strong> When <code>data</code> is null and <code>errors</code> is non-empty, the query failed outright, the status was still 200, and <a href="/github/graphql-200-with-errors/">that has its own note and its own repair</a>. This note starts where that one ends: the call worked, most of the data is correct and usable, and throwing it away would be a bug of its own. Same envelope, opposite instruction.</p>
<p><strong>Widening the token is a decision, not automatically the fix.</strong> Some of these fields need <code>read:org</code>, some need admin rights on the repository, and some are only visible to an installation with an explicit permission granted. Handing a reporting job the permissions it would need to see everything is sometimes right and sometimes a much larger problem than an under-count. The script tells you which permission each nulled field would want and leaves the choice with you.</p>
<p><strong>The API cannot see your aggregation.</strong> Nothing GitHub returns says whether you summed across the nulls. What a script can do is run your own query shape against a repository you name, count how many of the requested fields resolved, and say which of the nulls were explained by an errors entry. That is a measurement of the response, not an audit of your code, and it is enough to tell you whether the trap is live for this token.</p>""",
"steps": [
 {"h": "Send the query your integration actually sends",
  "body": """<p>Not a simplified version. The nulls follow the fields, so a probe that asks for <code>name</code> and <code>id</code> will come back clean while the real query loses <code>diskUsage</code> and <code>collaborators</code>. One query, one point. Pass your own document with <code>--query</code> if the default does not resemble yours.</p>"""},
 {"h": "Walk errors[].path rather than counting errors",
  "body": """<p>The number of errors is not the finding; the paths are. Each one names a field that resolved to null because the server refused it, list indices and all. Print them, because a list of eight dotted paths is a bug report somebody can act on and "8 errors" is not.</p>"""},
 {"h": "Separate the withheld nulls from the real ones",
  "body": """<p>Walk the data tree, collect every path that is null, and subtract the paths that appear in <code>errors</code>. What is left is genuinely empty: no license, no milestone, no assignee. What matched is unknown. This is the step that turns an ambiguous response into two unambiguous sets, and every later decision depends on it.</p>"""},
 {"h": "Ask whether the aggregate is still safe to publish",
  "body": """<p>Give the script the root you sum over and it will tell you how many withheld fields lie underneath it. If the answer is more than zero, the total is a lower bound and has to be labelled as one. Publishing it as a total is the actual harm here; the nulls themselves are only the mechanism.</p>"""},
 {"h": "Decide on the permission, then keep the run cheap",
  "body": """<p>For each nulled field the script names the permission that would let the token read it, so widening the token is a considered choice rather than a reflex. The audit costs one point per query, one by default, out of 5,000 an hour, and it prints that before it spends it. Retrying is never the repair: the same token produces the same nulls every time.</p>"""},
],
"verify": """<p>Once the nulls are separated and the aggregate is labelled, the same run reports the gap instead of hiding it.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_partial.py --repo acme/monorepo --root repository
# point cost: 1 point(s) against the 5,000/hour GraphQL budget
# HTTP 200, errors=2, data usable=yes
# partial-withheld: 2 field(s) resolved to null and errors[].path explains both
#   repository.diskUsage           withheld  FORBIDDEN   wants: metadata + admin on the repository
#   repository.collaborators       withheld  FORBIDDEN   wants: read access to members
#   repository.licenseInfo         absent    -           genuinely empty, safe to read as none
# aggregation over 'repository' is NOT safe: 2 withheld field(s) underneath it
# repair: record the withheld paths as unknown, not zero, and label the total a
# lower bound. Do not retry: this token returns the same nulls every time.</code></pre>""",
"code_intro": "One query, sent as the integration sends it, and refused outright if the document turns out to contain a mutation or a subscription. What follows is a set-difference done properly: every path in the data tree that is null, every path named in errors, and the two sets compared so a withheld field can never be confused with an empty one. The path resolver handles list indices because real GraphQL error paths contain them. Nothing about the rule needs a network, so the entire classification is tested against recorded envelopes, including the ones that are inconvenient to produce on purpose.",
"py_file": "github_graphql_partial.py",
"py": '''"""Separate the fields a GraphQL response withheld from the ones that are empty.

Read only, and queries only. GitHub's GraphQL endpoint takes a document in the
request body, so a read is carried by POST there just as a write would be; that
is transport, not intent. This script sends queries and refuses any document
containing a mutation or a subscription before it opens a socket. Nothing is
written and the repair is printed rather than performed.

GraphQL resolves each field independently. A field the token cannot see becomes
null in data and adds an entry to errors carrying a path that names it exactly,
while the rest of the response succeeds. The response is genuinely partial. The
danger is that a withheld null and a real null look identical in the data and
mean opposite things: unknown versus none.

What this can and cannot see: the API has no idea whether your code aggregates
across the nulls. It can measure this response, name which nulls were explained
by an errors entry and say whether a sum over a given root is still honest.

Environment:

    GITHUB_TOKEN    a token with read access to the GraphQL API
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_partial")

API = "https://api.github.com"
UA = "github-graphql-partial/1.0"

POINTS_PER_QUERY = 1

# Deliberately a mixture. Two of these fields commonly resolve to null because a
# read-only token is not allowed to see them, and one commonly resolves to null
# because the repository really has nothing there. Telling those apart is the
# whole job.
DEFAULT_QUERY = (
    "query($owner: String!, $name: String!) {"
    " repository(owner: $owner, name: $name) {"
    " name isPrivate diskUsage"
    " licenseInfo { key }"
    " collaborators(first: 1) { totalCount }"
    " } }"
)

# What a withheld field would need to be readable. Not a promise that granting
# it is the right move: some of these are a much bigger decision than an
# under-count, which is exactly why the script names them instead of advising.
PERMISSION_HINT = {
    "diskUsage": "metadata read plus admin on the repository",
    "collaborators": "read access to repository members",
    "vulnerabilityAlerts": "Dependabot alerts read",
    "projectsV2": "organization projects read",
    "members": "read:org on the organization",
    "email": "user email read, and the user must have a public email",
}

MISSING = object()


def strip_noise(document):
    """Remove GraphQL comments and string literals from a document. Pure."""
    src = str(document or "")
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "#":
            while i < n and src[i] != "\\n":
                i += 1
            continue
        if src.startswith('"""', i):
            j = src.find('"""', i + 3)
            i = n if j < 0 else j + 3
            out.append(" ")
            continue
        if ch == '"':
            i += 1
            while i < n and src[i] != '"':
                i += 2 if src[i] == "\\\\" else 1
            i += 1
            out.append(" ")
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def operations(document):
    """The top-level operations in a document, in order. Pure."""
    src = strip_noise(document)
    ops, depth, word, declared = [], 0, "", None
    for ch in src + " ":
        if ch.isalnum() or ch == "_":
            word += ch
            continue
        if word:
            if depth == 0 and word in ("query", "mutation", "subscription", "fragment"):
                declared = word
            word = ""
        if ch == "{":
            if depth == 0:
                ops.append(declared or "query")
                declared = None
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
    return ops


def refusal(document):
    """Why this document will not be sent, or None if it is a read. Pure."""
    ops = operations(document)
    if not ops:
        return "the document contains no operation to send."
    for kind in ("mutation", "subscription"):
        if kind in ops:
            return ("the document contains a %s. This script sends queries only: "
                    "a query is a read, and the section it belongs to promises "
                    "its scripts never write." % kind)
    return None


def path_key(path):
    """A GraphQL error path rendered as a dotted string. Pure.

    List indices are kept as segments, because an error on element 3 of a
    connection is a different fact from an error on the connection.
    """
    if isinstance(path, str):
        return path
    return ".".join(str(p) for p in (path or []))


def value_at(data, dotted):
    """Resolve a dotted path in a data tree. Pure. MISSING if there is no such path."""
    cur = data
    if not dotted:
        return cur
    for seg in str(dotted).split("."):
        if isinstance(cur, dict):
            if seg not in cur:
                return MISSING
            cur = cur[seg]
        elif isinstance(cur, list):
            try:
                cur = cur[int(seg)]
            except (ValueError, IndexError):
                return MISSING
        else:
            return MISSING
    return cur


def null_paths(data, prefix=""):
    """Every path in a data tree whose value is null. Pure."""
    out = []
    if isinstance(data, dict):
        items = data.items()
    elif isinstance(data, list):
        items = ((str(i), v) for i, v in enumerate(data))
    else:
        return out
    for key, value in items:
        here = key if not prefix else prefix + "." + str(key)
        if value is None:
            out.append(here)
        else:
            out.extend(null_paths(value, here))
    return sorted(out)


def error_paths(body):
    """Dotted paths named by the errors array, mapped to their type. Pure."""
    out = {}
    if not isinstance(body, dict):
        return out
    for err in body.get("errors") or []:
        if not isinstance(err, dict) or not err.get("path"):
            continue
        out[path_key(err["path"])] = err.get("type") or "UNTYPED"
    return out


def unpathed_errors(body):
    """Errors that name no field, so nothing can be attributed to them. Pure."""
    if not isinstance(body, dict):
        return 0
    return sum(1 for e in (body.get("errors") or [])
               if not isinstance(e, dict) or not e.get("path"))


def has_usable_data(body):
    """Whether any top-level field resolved to something other than null. Pure."""
    if not isinstance(body, dict):
        return False
    data = body.get("data")
    if not isinstance(data, dict):
        return False
    return any(v is not None for v in data.values())


def withheld(body):
    """Paths that are null in data and explained by an errors entry. Pure."""
    if not isinstance(body, dict):
        return []
    named = error_paths(body)
    nulls = set(null_paths(body.get("data")))
    return sorted(p for p in named if p in nulls)


def absent(body):
    """Paths that are null with no errors entry: genuinely empty, not hidden. Pure."""
    if not isinstance(body, dict):
        return []
    named = set(error_paths(body))
    return sorted(p for p in null_paths(body.get("data")) if p not in named)


def orphan_error_paths(body):
    """Error paths that do not resolve to a null in data. Pure.

    Rare, and reported rather than swallowed: it usually means the path points
    into a list element that was dropped entirely, and a script that silently
    ignored it would be under-reporting the very thing it exists to count.
    """
    if not isinstance(body, dict):
        return []
    nulls = set(null_paths(body.get("data")))
    return sorted(p for p in error_paths(body) if p not in nulls)


def permission_hint(dotted):
    """The permission a withheld field would want. Pure."""
    leaf = str(dotted).split(".")[-1]
    return PERMISSION_HINT.get(leaf, "the permission that covers this field")


def tally(body):
    """Counts for one response. Pure."""
    return {
        "withheld": len(withheld(body)),
        "absent": len(absent(body)),
        "orphaned": len(orphan_error_paths(body)),
        "unpathed_errors": unpathed_errors(body),
    }


def is_partial_success(body):
    """Data survived and errors arrived beside it. Pure."""
    if not isinstance(body, dict):
        return False
    return bool(body.get("errors")) and has_usable_data(body)


def safe_to_aggregate(body, root):
    """Whether a sum under this root is honest. Pure. Returns (bool, sentence)."""
    under = [p for p in withheld(body)
             if not root or p == root or p.startswith(str(root) + ".")]
    if not under:
        return True, ("no withheld fields under %r, so a total over it is a "
                      "total." % root)
    return False, ("%d withheld field(s) under %r, so a total over it is a lower "
                   "bound and has to be labelled as one." % (len(under), root))


def classify(body):
    """Classify one response. Pure. Returns (state, detail).

    Total failure is named and handed on rather than absorbed, because the
    repair for a query that failed outright is not the repair for one that
    mostly worked.
    """
    if not isinstance(body, dict):
        return ("unreadable",
                "the response was not a JSON object, so nothing can be counted "
                "in it.")
    errs = body.get("errors") or []
    hidden = withheld(body)
    empty = absent(body)
    if errs and not has_usable_data(body):
        return ("total-failure",
                "%d error(s) arrived and no field resolved, so this is a failed "
                "query wearing a 200 rather than a partial one." % len(errs))
    if errs and not hidden and unpathed_errors(body):
        return ("errors-without-path",
                "%d error(s) arrived beside usable data but none of them names a "
                "field, so nothing can be attributed to a column."
                % unpathed_errors(body))
    if hidden:
        return ("partial-withheld",
                "%d field(s) resolved to null and errors[].path explains %s."
                % (len(hidden), "both" if len(hidden) == 2 else "each of them"))
    if empty:
        return ("nulls-unexplained",
                "%d null(s) in the data and no errors entry for any of them, so "
                "they are genuinely empty rather than withheld." % len(empty))
    return ("complete",
            "every requested field resolved and the errors array is empty.")


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "partial-withheld":
        return ("record the withheld paths as unknown, not zero, and label the "
                "total a lower bound. Do not retry: this token returns the same "
                "nulls every time.")
    if state == "nulls-unexplained":
        return ("nothing on the nulls: with no errors entry beside them they are "
                "real answers. Keep reading errors[].path anyway, because that "
                "is what will tell you when one of them stops being real.")
    if state == "total-failure":
        return ("see /github/graphql-200-with-errors/ -- nothing resolved here, "
                "so this is the total-failure case and partial-response handling "
                "does not apply.")
    if state == "errors-without-path":
        return ("log these errors verbatim and treat the whole response as "
                "suspect. An error with no path cannot be attributed to a "
                "column, so no per-field repair is available.")
    if state == "complete":
        return "nothing."
    return "point the check at a document this endpoint can answer."


def point_cost(queries):
    """Points this run will spend against the GraphQL budget. Pure."""
    try:
        return max(0, int(queries)) * POINTS_PER_QUERY
    except (TypeError, ValueError):
        return 0


def run_query(session, document, variables):
    """Send one query. Returns (status, body-or-None).

    A GraphQL query is a read; POST is only how the document reaches the
    endpoint, which is why the verb is written here beside the URL rather than
    hidden in a constant where it could be mistaken for a write path.
    """
    r = session.post(API + "/graphql",
                     json={"query": document, "variables": variables or {}},
                     timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--query",
                    help="send your own query document instead of the default. "
                         "Use the one your integration actually sends: the nulls "
                         "follow the fields. Mutations are refused.")
    ap.add_argument("--root", default="repository",
                    help="the path you aggregate over, checked for withheld "
                         "fields underneath it")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2
    try:
        owner, name = args.repo.split("/", 1)
    except ValueError:
        log.error("--repo takes owner/name")
        return 2

    document = args.query or DEFAULT_QUERY
    why_not = refusal(document)
    if why_not:
        log.error("refusing to send: %s", why_not)
        return 2

    log.info("point cost: %d point(s) against the 5,000/hour GraphQL budget",
             point_cost(1))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
    })

    status, body = run_query(session, document, {"owner": owner, "name": name})
    state, detail = classify(body)
    counts = tally(body)
    named = error_paths(body)

    log.info("HTTP %s, errors=%d, data usable=%s", status,
             len(((body or {}).get("errors")) or []),
             "yes" if has_usable_data(body) else "no")
    log.info("%s: %s", state, detail)
    for p in withheld(body):
        log.info("  %-34s withheld  %-11s wants: %s",
                 p, named.get(p, "UNTYPED"), permission_hint(p))
    for p in absent(body):
        log.info("  %-34s absent    %-11s genuinely empty, safe to read as none",
                 p, "-")
    for p in orphan_error_paths(body):
        log.info("  %-34s orphaned  %-11s named by errors but not null in data",
                 p, named.get(p, "UNTYPED"))

    ok, sentence = safe_to_aggregate(body, args.root)
    log.info("aggregation over %r is %s: %s", args.root,
             "safe" if ok else "NOT safe", sentence)
    log.info("repair: %s", repair(state))

    print(json.dumps({
        "points_spent": point_cost(1),
        "status": status,
        "state": state,
        "detail": detail,
        "partial_success": is_partial_success(body),
        "withheld": withheld(body),
        "absent": absent(body),
        "orphan_error_paths": orphan_error_paths(body),
        "tally": counts,
        "aggregation_root": args.root,
        "aggregation_safe": ok,
    }, indent=2, default=str))
    return 1 if state in ("partial-withheld", "errors-without-path") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-partial.mjs",
"js": '''/**
 * Separate the fields a GraphQL response withheld from the ones that are empty.
 *
 * Read only, and queries only. GitHub's GraphQL endpoint takes a document in
 * the request body, so a read is carried by POST there just as a write would
 * be; that is transport, not intent. Any document containing a mutation or a
 * subscription is refused before a socket opens.
 *
 * Environment:
 *   GITHUB_TOKEN   a token with read access to the GraphQL API
 *   GITHUB_REPO    owner/name
 *   GITHUB_QUERY   send your own query document instead of the default
 *   GITHUB_ROOT    the path you aggregate over, default 'repository'
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-partial/1.0';

export const POINTS_PER_QUERY = 1;

const DEFAULT_QUERY = 'query($owner: String!, $name: String!) {'
  + ' repository(owner: $owner, name: $name) {'
  + ' name isPrivate diskUsage'
  + ' licenseInfo { key }'
  + ' collaborators(first: 1) { totalCount }'
  + ' } }';

/** What a withheld field would need to be readable. */
export const PERMISSION_HINT = {
  diskUsage: 'metadata read plus admin on the repository',
  collaborators: 'read access to repository members',
  vulnerabilityAlerts: 'Dependabot alerts read',
  projectsV2: 'organization projects read',
  members: 'read:org on the organization',
  email: 'user email read, and the user must have a public email',
};

const MISSING = Symbol('missing');

/** Remove GraphQL comments and string literals from a document. Pure. */
export function stripNoise(document) {
  const src = String(document ?? '');
  const out = [];
  let i = 0;
  while (i < src.length) {
    const ch = src[i];
    if (ch === '#') {
      while (i < src.length && src[i] !== '\\n') i += 1;
      continue;
    }
    if (src.startsWith('"""', i)) {
      const j = src.indexOf('"""', i + 3);
      i = j < 0 ? src.length : j + 3;
      out.push(' ');
      continue;
    }
    if (ch === '"') {
      i += 1;
      while (i < src.length && src[i] !== '"') i += src[i] === '\\\\' ? 2 : 1;
      i += 1;
      out.push(' ');
      continue;
    }
    out.push(ch);
    i += 1;
  }
  return out.join('');
}

/** The top-level operations in a document, in order. Pure. */
export function operations(document) {
  const src = `${stripNoise(document)} `;
  const ops = [];
  let depth = 0;
  let word = '';
  let declared = null;
  for (const ch of src) {
    if (/[A-Za-z0-9_]/.test(ch)) { word += ch; continue; }
    if (word) {
      if (depth === 0 && ['query', 'mutation', 'subscription', 'fragment'].includes(word)) {
        declared = word;
      }
      word = '';
    }
    if (ch === '{') {
      if (depth === 0) { ops.push(declared || 'query'); declared = null; }
      depth += 1;
    } else if (ch === '}') {
      depth = Math.max(0, depth - 1);
    }
  }
  return ops;
}

/** Why this document will not be sent, or null if it is a read. Pure. */
export function refusal(document) {
  const ops = operations(document);
  if (ops.length === 0) return 'the document contains no operation to send.';
  for (const kind of ['mutation', 'subscription']) {
    if (ops.includes(kind)) {
      return `the document contains a ${kind}. This script sends queries only: `
        + 'a query is a read, and the section it belongs to promises its '
        + 'scripts never write.';
    }
  }
  return null;
}

/** A GraphQL error path rendered as a dotted string. Pure. */
export function pathKey(path) {
  if (typeof path === 'string') return path;
  return (path || []).map(String).join('.');
}

/** Resolve a dotted path in a data tree. Pure. MISSING if there is no such path. */
export function valueAt(data, dotted) {
  let cur = data;
  if (!dotted) return cur;
  for (const seg of String(dotted).split('.')) {
    if (Array.isArray(cur)) {
      const i = Number(seg);
      if (!Number.isInteger(i) || i < 0 || i >= cur.length) return MISSING;
      cur = cur[i];
    } else if (cur && typeof cur === 'object') {
      if (!Object.prototype.hasOwnProperty.call(cur, seg)) return MISSING;
      cur = cur[seg];
    } else {
      return MISSING;
    }
  }
  return cur;
}

/** Every path in a data tree whose value is null. Pure. */
export function nullPaths(data, prefix = '') {
  const out = [];
  let entries;
  if (Array.isArray(data)) entries = data.map((v, i) => [String(i), v]);
  else if (data && typeof data === 'object') entries = Object.entries(data);
  else return out;
  for (const [key, value] of entries) {
    const here = prefix ? `${prefix}.${key}` : key;
    if (value === null || value === undefined) out.push(here);
    else out.push(...nullPaths(value, here));
  }
  return out.sort();
}

/** Dotted paths named by the errors array, mapped to their type. Pure. */
export function errorPaths(body) {
  const out = {};
  if (!body || typeof body !== 'object' || !Array.isArray(body.errors)) return out;
  for (const err of body.errors) {
    if (!err || typeof err !== 'object' || !err.path || err.path.length === 0) continue;
    out[pathKey(err.path)] = err.type || 'UNTYPED';
  }
  return out;
}

/** Errors that name no field, so nothing can be attributed to them. Pure. */
export function unpathedErrors(body) {
  if (!body || typeof body !== 'object' || !Array.isArray(body.errors)) return 0;
  return body.errors.filter(
    (e) => !e || typeof e !== 'object' || !e.path || e.path.length === 0,
  ).length;
}

/** Whether any top-level field resolved to something other than null. Pure. */
export function hasUsableData(body) {
  if (!body || typeof body !== 'object') return false;
  const data = body.data;
  if (!data || typeof data !== 'object' || Array.isArray(data)) return false;
  return Object.values(data).some((v) => v !== null && v !== undefined);
}

/** Paths that are null in data and explained by an errors entry. Pure. */
export function withheld(body) {
  if (!body || typeof body !== 'object') return [];
  const named = errorPaths(body);
  const nulls = new Set(nullPaths(body.data));
  return Object.keys(named).filter((p) => nulls.has(p)).sort();
}

/** Paths that are null with no errors entry: genuinely empty, not hidden. Pure. */
export function absent(body) {
  if (!body || typeof body !== 'object') return [];
  const named = new Set(Object.keys(errorPaths(body)));
  return nullPaths(body.data).filter((p) => !named.has(p)).sort();
}

/** Error paths that do not resolve to a null in data. Pure. */
export function orphanErrorPaths(body) {
  if (!body || typeof body !== 'object') return [];
  const nulls = new Set(nullPaths(body.data));
  return Object.keys(errorPaths(body)).filter((p) => !nulls.has(p)).sort();
}

/** The permission a withheld field would want. Pure. */
export function permissionHint(dotted) {
  const leaf = String(dotted).split('.').pop();
  return Object.prototype.hasOwnProperty.call(PERMISSION_HINT, leaf)
    ? PERMISSION_HINT[leaf]
    : 'the permission that covers this field';
}

/** Counts for one response. Pure. */
export function tally(body) {
  return {
    withheld: withheld(body).length,
    absent: absent(body).length,
    orphaned: orphanErrorPaths(body).length,
    unpathed_errors: unpathedErrors(body),
  };
}

/** Data survived and errors arrived beside it. Pure. */
export function isPartialSuccess(body) {
  if (!body || typeof body !== 'object') return false;
  return Array.isArray(body.errors) && body.errors.length > 0 && hasUsableData(body);
}

/** Whether a sum under this root is honest. Pure. Returns [bool, sentence]. */
export function safeToAggregate(body, root) {
  const under = withheld(body).filter(
    (p) => !root || p === root || p.startsWith(`${root}.`),
  );
  if (under.length === 0) {
    return [true, `no withheld fields under '${root}', so a total over it is a total.`];
  }
  return [false, `${under.length} withheld field(s) under '${root}', so a total `
    + 'over it is a lower bound and has to be labelled as one.'];
}

/** Classify one response. Pure. Returns [state, detail]. */
export function classify(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return ['unreadable', 'the response was not a JSON object, so nothing can '
      + 'be counted in it.'];
  }
  const errs = Array.isArray(body.errors) ? body.errors : [];
  const hidden = withheld(body);
  const empty = absent(body);
  if (errs.length > 0 && !hasUsableData(body)) {
    return ['total-failure', `${errs.length} error(s) arrived and no field `
      + 'resolved, so this is a failed query wearing a 200 rather than a '
      + 'partial one.'];
  }
  if (errs.length > 0 && hidden.length === 0 && unpathedErrors(body) > 0) {
    return ['errors-without-path', `${unpathedErrors(body)} error(s) arrived `
      + 'beside usable data but none of them names a field, so nothing can be '
      + 'attributed to a column.'];
  }
  if (hidden.length > 0) {
    return ['partial-withheld', `${hidden.length} field(s) resolved to null and `
      + `errors[].path explains ${hidden.length === 2 ? 'both' : 'each of them'}.`];
  }
  if (empty.length > 0) {
    return ['nulls-unexplained', `${empty.length} null(s) in the data and no `
      + 'errors entry for any of them, so they are genuinely empty rather than '
      + 'withheld.'];
  }
  return ['complete', 'every requested field resolved and the errors array is empty.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'partial-withheld') {
    return 'record the withheld paths as unknown, not zero, and label the total '
      + 'a lower bound. Do not retry: this token returns the same nulls every time.';
  }
  if (state === 'nulls-unexplained') {
    return 'nothing on the nulls: with no errors entry beside them they are real '
      + 'answers. Keep reading errors[].path anyway, because that is what will '
      + 'tell you when one of them stops being real.';
  }
  if (state === 'total-failure') {
    return 'see /github/graphql-200-with-errors/ -- nothing resolved here, so '
      + 'this is the total-failure case and partial-response handling does not apply.';
  }
  if (state === 'errors-without-path') {
    return 'log these errors verbatim and treat the whole response as suspect. '
      + 'An error with no path cannot be attributed to a column, so no per-field '
      + 'repair is available.';
  }
  if (state === 'complete') return 'nothing.';
  return 'point the check at a document this endpoint can answer.';
}

/** Points this run will spend against the GraphQL budget. Pure. */
export function pointCost(queries) {
  const n = Number(queries);
  if (!Number.isFinite(n) || n < 0) return 0;
  return Math.trunc(n) * POINTS_PER_QUERY;
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'Content-Type': 'application/json',
    'User-Agent': UA,
  };
}

async function runQuery(token, document, variables) {
  const res = await fetch(`${API}/graphql`, {
    // A GraphQL query is a read. POST is only how the document reaches the
    // endpoint, and refusal() has already rejected anything that is not a read.
    method: 'POST',
    headers: headers(token),
    body: JSON.stringify({ query: document, variables: variables || {} }),
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  if (!token || !repo) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_REPO=owner/name');
    process.exitCode = 2;
    return;
  }
  const [owner, name] = repo.split('/');
  if (!owner || !name) {
    console.error('GITHUB_REPO takes owner/name');
    process.exitCode = 2;
    return;
  }
  const document = process.env.GITHUB_QUERY || DEFAULT_QUERY;
  const root = process.env.GITHUB_ROOT || 'repository';
  const whyNot = refusal(document);
  if (whyNot) {
    console.error(`refusing to send: ${whyNot}`);
    process.exitCode = 2;
    return;
  }

  console.log(`point cost: ${pointCost(1)} point(s) against the 5,000/hour GraphQL budget`);
  const { status, body } = await runQuery(token, document, { owner, name });
  const [state, detail] = classify(body);
  const named = errorPaths(body);
  const errs = (body && Array.isArray(body.errors)) ? body.errors.length : 0;

  console.log(`HTTP ${status}, errors=${errs}, data usable=${hasUsableData(body) ? 'yes' : 'no'}`);
  console.log(`${state}: ${detail}`);
  for (const p of withheld(body)) {
    console.log(`  ${p.padEnd(34)} withheld  ${(named[p] || 'UNTYPED').padEnd(11)} wants: ${permissionHint(p)}`);
  }
  for (const p of absent(body)) {
    console.log(`  ${p.padEnd(34)} absent    ${'-'.padEnd(11)} genuinely empty, safe to read as none`);
  }
  for (const p of orphanErrorPaths(body)) {
    console.log(`  ${p.padEnd(34)} orphaned  ${(named[p] || 'UNTYPED').padEnd(11)} named by errors but not null in data`);
  }

  const [ok, sentence] = safeToAggregate(body, root);
  console.log(`aggregation over '${root}' is ${ok ? 'safe' : 'NOT safe'}: ${sentence}`);
  console.log(`repair: ${repair(state)}`);

  console.log(JSON.stringify({
    points_spent: pointCost(1),
    status,
    state,
    detail,
    partial_success: isPartialSuccess(body),
    withheld: withheld(body),
    absent: absent(body),
    orphan_error_paths: orphanErrorPaths(body),
    tally: tally(body),
    aggregation_root: root,
    aggregation_safe: ok,
  }, null, 2));
  process.exitCode = ['partial-withheld', 'errors-without-path'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The suite is built around one envelope that is deliberately awkward: a repository object with three nulls in it, two of which are named in errors[].path and one of which is not. Everything important falls out of that. The path resolver is tested against list indices, because real error paths contain them and a resolver that only walks objects would silently report the interesting cases as unexplained. Then the set difference in both directions, an error path that resolves to nothing at all, the aggregation verdict under a named root, the boundary against the total-failure case that belongs to the other note, and the refusal that keeps a mutation off the wire.",
"test_py_file": "test_github_graphql_partial.py",
"test_py": '''from github_graphql_partial import (
    MISSING, absent, classify, error_paths, is_partial_success, null_paths, operations,
    orphan_error_paths, path_key, permission_hint, point_cost, refusal, repair,
    safe_to_aggregate, tally, unpathed_errors, value_at, withheld,
)

PARTIAL = {
    "data": {"repository": {
        "name": "monorepo",
        "isPrivate": True,
        "diskUsage": None,
        "licenseInfo": None,
        "collaborators": None,
    }},
    "errors": [
        {"type": "FORBIDDEN", "path": ["repository", "diskUsage"],
         "message": "Resource not accessible by personal access token"},
        {"type": "FORBIDDEN", "path": ["repository", "collaborators"],
         "message": "Must have push access to view repository collaborators."},
    ],
}

IN_A_LIST = {
    "data": {"repository": {"pullRequests": {"nodes": [
        {"number": 1, "author": {"login": "ada"}},
        {"number": 2, "author": None},
    ]}}},
    "errors": [{"type": "FORBIDDEN",
                "path": ["repository", "pullRequests", "nodes", 1, "author"]}],
}

TOTAL_FAILURE = {"data": {"repository": None},
                 "errors": [{"type": "NOT_FOUND", "path": ["repository"]}]}

CLEAN = {"data": {"repository": {"name": "monorepo", "isPrivate": False}}}


def test_a_partial_response_is_a_third_outcome_not_a_failure():
    assert is_partial_success(PARTIAL)
    assert not is_partial_success(TOTAL_FAILURE)
    assert not is_partial_success(CLEAN)


def test_withheld_and_absent_are_the_two_kinds_of_null():
    assert withheld(PARTIAL) == ["repository.collaborators", "repository.diskUsage"]
    assert absent(PARTIAL) == ["repository.licenseInfo"]


def test_a_null_with_no_errors_entry_is_a_real_answer():
    body = {"data": {"repository": {"name": "x", "licenseInfo": None}}}
    assert withheld(body) == []
    assert absent(body) == ["repository.licenseInfo"]
    state, detail = classify(body)
    assert state == "nulls-unexplained"
    assert "genuinely empty" in detail


def test_error_paths_survive_a_list_index():
    assert path_key(["repository", "pullRequests", "nodes", 1, "author"]) == \\
        "repository.pullRequests.nodes.1.author"
    assert withheld(IN_A_LIST) == ["repository.pullRequests.nodes.1.author"]
    assert absent(IN_A_LIST) == []


def test_the_path_resolver_walks_lists_as_well_as_objects():
    data = IN_A_LIST["data"]
    assert value_at(data, "repository.pullRequests.nodes.0.number") == 1
    assert value_at(data, "repository.pullRequests.nodes.1.author") is None
    assert value_at(data, "repository.pullRequests.nodes.9") is MISSING
    assert value_at(data, "repository.nothingLikeThis") is MISSING
    assert null_paths({"a": None, "b": {"c": None, "d": 1}}) == ["a", "b.c"]


def test_an_error_path_that_matches_no_null_is_reported_not_swallowed():
    body = {"data": {"repository": {"name": "x"}},
            "errors": [{"type": "FORBIDDEN", "path": ["repository", "gone"]}]}
    assert orphan_error_paths(body) == ["repository.gone"]
    assert withheld(body) == []


def test_an_error_with_no_path_cannot_be_attributed():
    body = {"data": {"repository": {"name": "x"}},
            "errors": [{"type": "INTERNAL", "message": "something broke"}]}
    assert unpathed_errors(body) == 1
    assert error_paths(body) == {}
    state, _ = classify(body)
    assert state == "errors-without-path"
    assert "verbatim" in repair(state)


def test_a_query_where_nothing_resolved_belongs_to_the_other_note():
    state, detail = classify(TOTAL_FAILURE)
    assert state == "total-failure"
    assert "failed query wearing a 200" in detail
    assert "graphql-200-with-errors" in repair(state)


def test_the_finding_names_the_paths_rather_than_counting_errors():
    state, detail = classify(PARTIAL)
    assert state == "partial-withheld"
    assert "errors[].path" in detail
    assert "unknown, not zero" in repair(state)
    assert "Do not retry" in repair(state)


def test_an_aggregate_over_a_root_with_withheld_fields_is_a_lower_bound():
    ok, sentence = safe_to_aggregate(PARTIAL, "repository")
    assert not ok
    assert "lower bound" in sentence
    ok2, sentence2 = safe_to_aggregate(PARTIAL, "viewer")
    assert ok2
    assert "is a total" in sentence2


def test_the_aggregation_root_is_matched_on_a_boundary_not_a_prefix():
    body = {"data": {"repo": {"a": None}, "repository": {"b": 1}},
            "errors": [{"type": "FORBIDDEN", "path": ["repo", "a"]}]}
    ok, _ = safe_to_aggregate(body, "repository")
    assert ok


def test_each_withheld_field_names_the_permission_it_would_want():
    assert "admin" in permission_hint("repository.diskUsage")
    assert "members" in permission_hint("repository.collaborators")
    assert permission_hint("repository.somethingNew") == \\
        "the permission that covers this field"


def test_the_tally_counts_all_four_kinds_of_thing():
    assert tally(PARTIAL) == {"withheld": 2, "absent": 1, "orphaned": 0,
                              "unpathed_errors": 0}
    assert tally(CLEAN) == {"withheld": 0, "absent": 0, "orphaned": 0,
                            "unpathed_errors": 0}


def test_a_clean_response_says_so_plainly():
    state, _ = classify(CLEAN)
    assert state == "complete"
    assert repair(state) == "nothing."
    assert classify(None)[0] == "unreadable"


def test_the_script_refuses_to_send_a_mutation():
    assert operations("query Q { viewer { login } }") == ["query"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal("subscription S { thing { id } }")
    assert refusal("query Q { repository(owner: \\"o\\", name: \\"n\\") { name } }") is None


def test_the_run_says_what_it_will_spend():
    assert point_cost(1) == 1
    assert point_cost(0) == 0
    assert point_cost(None) == 0
''',
"test_js_file": "github-graphql-partial.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  absent, classify, errorPaths, isPartialSuccess, nullPaths, operations,
  orphanErrorPaths, pathKey, permissionHint, pointCost, refusal, repair,
  safeToAggregate, tally, unpathedErrors, valueAt, withheld,
} from './github-graphql-partial.mjs';

const PARTIAL = {
  data: {
    repository: {
      name: 'monorepo',
      isPrivate: true,
      diskUsage: null,
      licenseInfo: null,
      collaborators: null,
    },
  },
  errors: [
    { type: 'FORBIDDEN', path: ['repository', 'diskUsage'] },
    { type: 'FORBIDDEN', path: ['repository', 'collaborators'] },
  ],
};

const IN_A_LIST = {
  data: {
    repository: {
      pullRequests: {
        nodes: [
          { number: 1, author: { login: 'ada' } },
          { number: 2, author: null },
        ],
      },
    },
  },
  errors: [{ type: 'FORBIDDEN', path: ['repository', 'pullRequests', 'nodes', 1, 'author'] }],
};

const TOTAL_FAILURE = {
  data: { repository: null },
  errors: [{ type: 'NOT_FOUND', path: ['repository'] }],
};

const CLEAN = { data: { repository: { name: 'monorepo', isPrivate: false } } };

test('a partial response is a third outcome, not a failure', () => {
  assert.ok(isPartialSuccess(PARTIAL));
  assert.ok(!isPartialSuccess(TOTAL_FAILURE));
  assert.ok(!isPartialSuccess(CLEAN));
});

test('withheld and absent are the two kinds of null', () => {
  assert.deepEqual(withheld(PARTIAL), ['repository.collaborators', 'repository.diskUsage']);
  assert.deepEqual(absent(PARTIAL), ['repository.licenseInfo']);
});

test('a null with no errors entry is a real answer', () => {
  const body = { data: { repository: { name: 'x', licenseInfo: null } } };
  assert.deepEqual(withheld(body), []);
  assert.deepEqual(absent(body), ['repository.licenseInfo']);
  const [state, detail] = classify(body);
  assert.equal(state, 'nulls-unexplained');
  assert.match(detail, /genuinely empty/);
});

test('error paths survive a list index', () => {
  assert.equal(
    pathKey(['repository', 'pullRequests', 'nodes', 1, 'author']),
    'repository.pullRequests.nodes.1.author',
  );
  assert.deepEqual(withheld(IN_A_LIST), ['repository.pullRequests.nodes.1.author']);
  assert.deepEqual(absent(IN_A_LIST), []);
});

test('the path resolver walks lists as well as objects', () => {
  const data = IN_A_LIST.data;
  assert.equal(valueAt(data, 'repository.pullRequests.nodes.0.number'), 1);
  assert.equal(valueAt(data, 'repository.pullRequests.nodes.1.author'), null);
  assert.deepEqual(nullPaths({ a: null, b: { c: null, d: 1 } }), ['a', 'b.c']);
});

test('an error path that matches no null is reported, not swallowed', () => {
  const body = {
    data: { repository: { name: 'x' } },
    errors: [{ type: 'FORBIDDEN', path: ['repository', 'gone'] }],
  };
  assert.deepEqual(orphanErrorPaths(body), ['repository.gone']);
  assert.deepEqual(withheld(body), []);
});

test('an error with no path cannot be attributed', () => {
  const body = {
    data: { repository: { name: 'x' } },
    errors: [{ type: 'INTERNAL', message: 'something broke' }],
  };
  assert.equal(unpathedErrors(body), 1);
  assert.deepEqual(errorPaths(body), {});
  const [state] = classify(body);
  assert.equal(state, 'errors-without-path');
  assert.match(repair(state), /verbatim/);
});

test('a query where nothing resolved belongs to the other note', () => {
  const [state, detail] = classify(TOTAL_FAILURE);
  assert.equal(state, 'total-failure');
  assert.match(detail, /failed query wearing a 200/);
  assert.match(repair(state), /graphql-200-with-errors/);
});

test('the finding names the paths rather than counting errors', () => {
  const [state, detail] = classify(PARTIAL);
  assert.equal(state, 'partial-withheld');
  assert.match(detail, /errors\\[\\]\\.path/);
  assert.match(repair(state), /unknown, not zero/);
  assert.match(repair(state), /Do not retry/);
});

test('an aggregate over a root with withheld fields is a lower bound', () => {
  const [ok, sentence] = safeToAggregate(PARTIAL, 'repository');
  assert.ok(!ok);
  assert.match(sentence, /lower bound/);
  const [ok2, sentence2] = safeToAggregate(PARTIAL, 'viewer');
  assert.ok(ok2);
  assert.match(sentence2, /is a total/);
});

test('the aggregation root is matched on a boundary, not a prefix', () => {
  const body = {
    data: { repo: { a: null }, repository: { b: 1 } },
    errors: [{ type: 'FORBIDDEN', path: ['repo', 'a'] }],
  };
  const [ok] = safeToAggregate(body, 'repository');
  assert.ok(ok);
});

test('each withheld field names the permission it would want', () => {
  assert.match(permissionHint('repository.diskUsage'), /admin/);
  assert.match(permissionHint('repository.collaborators'), /members/);
  assert.equal(
    permissionHint('repository.somethingNew'),
    'the permission that covers this field',
  );
});

test('the tally counts all four kinds of thing', () => {
  assert.deepEqual(tally(PARTIAL),
    { withheld: 2, absent: 1, orphaned: 0, unpathed_errors: 0 });
  assert.deepEqual(tally(CLEAN),
    { withheld: 0, absent: 0, orphaned: 0, unpathed_errors: 0 });
});

test('a clean response says so plainly', () => {
  const [state] = classify(CLEAN);
  assert.equal(state, 'complete');
  assert.equal(repair(state), 'nothing.');
  assert.equal(classify(null)[0], 'unreadable');
});

test('the script refuses to send a mutation', () => {
  assert.deepEqual(operations('query Q { viewer { login } }'), ['query']);
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.ok(refusal('subscription S { thing { id } }'));
  assert.equal(refusal('query Q { repository(owner: "o", name: "n") { name } }'), null);
});

test('the run says what it will spend', () => {
  assert.equal(pointCost(1), 1);
  assert.equal(pointCost(0), 0);
  assert.equal(pointCost(null), 0);
});
''',
"faq": [
 ("Why does a forbidden field not fail the whole query?",
  "Because GraphQL resolves fields independently, and failing the document because one field out of forty was refused would make the API almost unusable for anyone holding a narrow token. The design decision is deliberate: you get everything you were allowed to have, plus an exact statement of what you were not. It is a better contract than the REST equivalent, which is a 404 that will not say whether the thing is missing or hidden. It only helps if the errors array is read."),
 ("How do I tell a withheld null from a genuinely empty field?",
  "By whether a path in errors[].path points at it. That is the only signal, and it is reliable: a field that resolved to null because there is nothing there produces no error entry at all, while a field the server refused produces one naming the exact route to it, list indices included. The script does this comparison as a set difference in both directions, and it also reports the leftovers, meaning error paths that do not correspond to any null, because those usually mean an element was dropped from a list rather than nulled in place."),
 ("Should I retry a partial response?",
  "No. The nulls come from what this token is permitted to read, and that does not change between one request and the next, so a retry costs another point and returns the same shape. Retrying is the right reflex for RATE_LIMITED and sometimes for INTERNAL; it is exactly wrong here. The two available moves are to widen the token, which is a decision about access rather than a bug fix, and to record the withheld fields as unknown so nothing downstream sums across them."),
 ("Can I just filter out the objects that have nulls?",
  "Only if you also report how many you dropped. Dropping the eight private repositories from a fifty-repository storage report and publishing the total for forty-two as though it were the total for fifty is the same error the nulls caused, arrived at more deliberately. The honest shape is a number plus a count of unknowns, and the script prints exactly that so it can be carried through to whatever consumes the result."),
 ("Does this need a token with more permissions to run?",
  "It needs less, not more, and that is rather the point: run it with the same read-only token your integration uses and it will show you the gaps that token has. Running it as an administrator would report a clean response and tell you nothing, because the nulls are a property of the credential rather than of the repository. One query, one point out of 5,000 an hour, printed before it is spent."),
],
"related": [
 ("/github/graphql-200-with-errors/", "A GraphQL 200 that carries an errors array"),
 ("/github/app-permission-missing/", "An App permission the integration never asked for"),
 ("/github/saml-partial-results/", "SSO quietly removes rows from a list"),
],
"citations": [CITE_SPEC_ERRORS, CITE_GQL_GUIDE, CITE_TOKEN_PERMS, CITE_GQL_INTRO],
},

{
"slug": "graphql-rate-limited",
"title": "GraphQL points run out in a bucket separate from REST",
"description": "Every GraphQL call returns RATE_LIMITED while REST calls with the same token still work, because GraphQL is billed in points from its own hourly budget.",
"h1": "GraphQL points run out in a bucket separate from REST",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github graphql rate limit points",
             "graphql RATE_LIMITED api rate limit exceeded",
             "github graphql 5000 points per hour",
             "github rateLimit cost remaining query",
             "graphql rate limit separate from rest github"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Every GraphQL call is coming back <code>200</code> with <code>errors[0].type</code> set to <code>RATE_LIMITED</code>. The health check is green, because the health check is a REST call and REST calls with the same token are working perfectly. Somebody is going to spend an hour looking for a difference between the two code paths, and the difference is not in the code: they are billed from two different buckets, and only one of them is empty.",
"short_answer": """<p>GraphQL has its own hourly budget, measured in <strong>points</strong> rather than requests: 5,000 points an hour for a user token, 1,000 for the <code>GITHUB_TOKEN</code> inside GitHub Actions, 10,000 on Enterprise Cloud. Draining it has no effect on the REST <code>core</code> bucket and draining <code>core</code> has no effect on it. That is why a REST-based health check reports green while every GraphQL query in the system is failing.</p>
<p>Read <code>GET /rate_limit</code> and look at <code>resources.graphql</code>, not <code>resources.core</code>. That endpoint is free and covers both. Then put <code>rateLimit { cost remaining }</code> into your real queries so every response tells you its own price, and throttle on <code>remaining</code> instead of finding out when it reaches zero. A query costing 12 points means the budget is 416 queries an hour, and that is the number to plan against.</p>""",
"problem": """<p>The migration is what sets this up. Somebody replaces a hundred REST calls with one GraphQL query, which is the correct move and does exactly what it promised: the REST bucket stops being the constraint. Nobody adds a second gauge, because the first gauge is now reading comfortably and a gauge that reads comfortably does not invite questions. The monitoring, the alerting and the mental model all stay pointed at <code>core</code>.</p>
<p>What makes the failure so disorienting when it lands is the shape of the evidence. The token works. You can prove it works, in a terminal, in front of somebody, with a <code>curl</code> against a REST endpoint that returns instantly. The GraphQL calls from the same process with the same header fail every time. Every instinct says the problem is in the client, and hours go into the client.</p>
<p>The second thing that goes wrong is arithmetic. Even once somebody has found the right bucket, "5,000" gets read as five thousand queries, because that is what the number means on the REST side. A query that fans out over a few connections can cost ten or twenty points, so the real budget might be two or three hundred calls an hour. A job sized against the wrong unit does not fail gradually; it works fine in testing at ten queries and dies at four hundred.</p>""",
"why": """<p><strong>Two buckets, no relationship.</strong> <code>GET /rate_limit</code> returns <code>resources.core</code> and <code>resources.graphql</code> as independent objects with their own <code>limit</code>, <code>used</code>, <code>remaining</code> and <code>reset</code>. Nothing you do to one moves the other. This script prints both side by side for exactly that reason: seeing 4,983 remaining next to 0 remaining ends the argument about whether the token is fine faster than any explanation.</p>
<p><strong>The unit is points, and points are not requests.</strong> A query's cost is derived from how many connections it traverses and how many items it asks for, and it is reported back to you in the response if you ask for it. One query can cost one point or several dozen. The only honest way to state your budget is to measure the cost of the query you actually send and divide, which is what the script does rather than repeating the headline number.</p>
<p><strong>The limit tells you which budget you are on.</strong> A user token gets 5,000 points an hour and the <code>GITHUB_TOKEN</code> issued to a GitHub Actions workflow gets 1,000. A job that works on a laptop and fails in CI at a fifth of the volume is usually this, not a difference in code, and reading <code>resources.graphql.limit</code> identifies it in one call. The script names which budget the observed limit implies.</p>
<p><strong>This is not either of the REST buckets.</strong> The hourly REST quota running out is <a href="/github/rate-limit-core-exhausted/">its own problem with its own note</a>, and the per-minute point cap on a single hot REST endpoint is <a href="/github/secondary-limit-points-per-minute/">a third thing again</a>, undocumented in the response and only visible after the fact. Three buckets, three notes, and this one owns the 5,000-points-an-hour GraphQL budget and nothing else. When the script sees REST in trouble and GraphQL healthy it says so and sends you to the right note rather than giving advice about points.</p>
<p><strong>Asking for the budget in-band costs one point.</strong> Adding <code>rateLimit { limit cost remaining resetAt }</code> to a query you were sending anyway is free of extra round trips and tells you the exact price of that query. Sending it as a query of its own costs a point, which is why this script uses the free REST endpoint by default and only goes in-band when you ask it to.</p>
<p><strong>Consumption is not attributable.</strong> The bucket is shared by every process holding that token, and the API reports the drain without ever saying who caused it. If the budget is vanishing and you cannot account for it, the answer is a separate token per workload rather than a better query, because separate tokens are the only way to make the number mean something per job.</p>""",
"steps": [
 {"h": "Read both buckets in one free call",
  "body": """<p><code>GET /rate_limit</code> returns <code>resources.core</code> and <code>resources.graphql</code> together and consumes neither. Print them side by side. If GraphQL is at zero while core is nearly full, the investigation is over in one line and nobody has to look at the client at all.</p>"""},
 {"h": "Check which budget the limit implies",
  "body": """<p>A <code>limit</code> of 5,000 is a user token, 1,000 is the <code>GITHUB_TOKEN</code> inside a workflow, 10,000 is Enterprise Cloud. If the number surprises you, that is the finding: the job is running as a different actor than you assumed, and no amount of query tuning fixes a fivefold difference in budget.</p>"""},
 {"h": "Measure what your query actually costs",
  "body": """<p>Add <code>rateLimit { cost remaining }</code> to the query your integration sends and read the <code>cost</code> back. This is the only way to know the price; it depends on the connections traversed and the <code>first</code> values requested. The script will do it in-band for one point if you pass <code>--in-band</code>, and it says so before spending.</p>"""},
 {"h": "Convert points into queries, because that is what you schedule",
  "body": """<p>Divide the budget by the measured cost. Five thousand points at twelve points a query is 416 queries an hour, or roughly one every nine seconds. That number is schedulable and "5,000 points" is not, and getting it wrong is what turns a job that passed testing at ten queries into one that dies at four hundred.</p>"""},
 {"h": "Throttle on remaining, and split the token if you cannot account for the drain",
  "body": """<p>Read <code>remaining</code> from every response and slow down before it reaches zero rather than reacting to <code>RATE_LIMITED</code>. If the budget is disappearing faster than your own queries explain, the bucket is shared with something else holding the same token, and the repair is a separate token per workload. The API will never tell you which process spent it.</p>"""},
],
"verify": """<p>With the right gauge in front of you, the two buckets stop looking like one broken token.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_points.py
# point cost: 0 point(s). GET /rate_limit reports the GraphQL bucket and does
# not consume any of it.
# core     4211 / 5000 remaining, resets in 41m
# graphql     0 / 5000 remaining, resets in 12m
# budget: a limit of 5000 points/hour is a user token
# graphql-exhausted-rest-healthy: the GraphQL bucket is empty while core is at
# 84% remaining, so a REST health check reports green on a dead integration
# repair: throttle on resources.graphql.remaining, not on core

GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_points.py --in-band
# point cost: 1 point(s) against the 5,000/hour GraphQL budget
# measured cost: 12 point(s) for this query shape
# at 12 points a query the budget is 416 queries/hour, one every 8.7s</code></pre>""",
"code_intro": "The default run spends nothing: <code>GET /rate_limit</code> is a plain GET, it reports both buckets, and it is documented not to count against either. The in-band probe is opt-in, costs one point and is the only way to learn what a particular query shape actually prices at. Everything else is arithmetic held in pure functions: used fractions, seconds to reset, which budget a limit implies, and the conversion from points into the unit anybody can schedule against, which is queries per hour at a measured cost.",
"py_file": "github_graphql_points.py",
"py": '''"""Read the GraphQL point budget, which is not the REST one.

Read only. The default run spends nothing at all: GET /rate_limit reports both
buckets and is documented not to count against either. The optional in-band
probe sends one query and costs one point, and it says so first.

Queries only. GitHub's GraphQL endpoint takes a document in the request body, so
a read is carried by POST there just as a write would be; that is transport, not
intent. Any document containing a mutation or a subscription is refused before a
socket opens. Nothing is written and the repair is printed rather than performed.

GraphQL is billed in points from its own hourly budget: 5,000 for a user token,
1,000 for the GITHUB_TOKEN inside GitHub Actions, 10,000 on Enterprise Cloud.
The REST core bucket is untouched by GraphQL traffic and vice versa, which is why
a REST health check reports green while every GraphQL call is failing.

What this can and cannot see: the bucket is shared by every process using the
token and the API never says which one spent it. A drain you cannot account for
is a reason to issue a separate token per workload, not a query to tune.

Environment:

    GITHUB_TOKEN    a token with read access to the GraphQL API
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_points")

API = "https://api.github.com"
UA = "github-graphql-points/1.0"

# The published hourly point budgets, keyed by the actor they belong to. Read
# backwards, from an observed limit to the actor, this identifies a job that is
# running as something other than what its author assumed.
BUDGETS = {
    5000: "a user token",
    1000: "the GITHUB_TOKEN issued to a GitHub Actions workflow",
    10000: "an Enterprise Cloud token",
}

# The smallest useful in-band probe. Asking for cost alone would not report the
# node count, and nodeCount is the number the query-shape note needs.
BUDGET_QUERY = "query { rateLimit { limit cost remaining used resetAt nodeCount } }"

# Below this fraction of budget left, slow down rather than discover zero.
TIGHT = 0.2


def strip_noise(document):
    """Remove GraphQL comments and string literals from a document. Pure."""
    src = str(document or "")
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "#":
            while i < n and src[i] != "\\n":
                i += 1
            continue
        if src.startswith('"""', i):
            j = src.find('"""', i + 3)
            i = n if j < 0 else j + 3
            out.append(" ")
            continue
        if ch == '"':
            i += 1
            while i < n and src[i] != '"':
                i += 2 if src[i] == "\\\\" else 1
            i += 1
            out.append(" ")
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def operations(document):
    """The top-level operations in a document, in order. Pure."""
    src = strip_noise(document)
    ops, depth, word, declared = [], 0, "", None
    for ch in src + " ":
        if ch.isalnum() or ch == "_":
            word += ch
            continue
        if word:
            if depth == 0 and word in ("query", "mutation", "subscription", "fragment"):
                declared = word
            word = ""
        if ch == "{":
            if depth == 0:
                ops.append(declared or "query")
                declared = None
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
    return ops


def refusal(document):
    """Why this document will not be sent, or None if it is a read. Pure."""
    ops = operations(document)
    if not ops:
        return "the document contains no operation to send."
    for kind in ("mutation", "subscription"):
        if kind in ops:
            return ("the document contains a %s. This script sends queries only: "
                    "a query is a read, and the section it belongs to promises "
                    "its scripts never write." % kind)
    return None


def bucket(rate_limit_body, name):
    """One resource object out of GET /rate_limit. Pure. None if absent."""
    if not isinstance(rate_limit_body, dict):
        return None
    res = rate_limit_body.get("resources")
    if not isinstance(res, dict):
        return None
    b = res.get(name)
    return b if isinstance(b, dict) else None


def used_fraction(b):
    """How much of a bucket is gone, 0.0 to 1.0. Pure. None if unreadable."""
    if not isinstance(b, dict):
        return None
    try:
        limit = int(b.get("limit"))
        remaining = int(b.get("remaining"))
    except (TypeError, ValueError):
        return None
    if limit <= 0:
        return None
    return max(0.0, min(1.0, (limit - remaining) / float(limit)))


def seconds_to_reset(b, now):
    """Seconds until this bucket refills. Pure. None if unreadable."""
    if not isinstance(b, dict):
        return None
    try:
        return max(0, int(b.get("reset")) - int(now))
    except (TypeError, ValueError):
        return None


def identify_budget(limit):
    """Which actor an observed hourly limit implies. Pure."""
    try:
        n = int(limit)
    except (TypeError, ValueError):
        return "an unreadable limit"
    if n in BUDGETS:
        return BUDGETS[n]
    return ("a limit of %d, which matches none of the published budgets. Read "
            "it as the truth and plan against it." % n)


def queries_left(remaining, cost_per_query):
    """How many more queries of this shape fit in what is left. Pure."""
    try:
        rem = int(remaining)
        cost = int(cost_per_query)
    except (TypeError, ValueError):
        return None
    if cost <= 0:
        return None
    return max(0, rem // cost)


def sustainable_rate(limit, cost_per_query):
    """Queries per hour this budget supports at a measured cost. Pure."""
    try:
        lim = int(limit)
        cost = int(cost_per_query)
    except (TypeError, ValueError):
        return None
    if cost <= 0 or lim <= 0:
        return None
    return lim // cost


def seconds_between(limit, cost_per_query):
    """The gap to leave between queries to stay inside the budget. Pure."""
    rate = sustainable_rate(limit, cost_per_query)
    if not rate:
        return None
    return round(3600.0 / rate, 1)


def error_types(body):
    """The type of every entry in a GraphQL errors array. Pure."""
    if not isinstance(body, dict):
        return []
    return [(e.get("type") or "UNTYPED") if isinstance(e, dict) else "UNTYPED"
            for e in (body.get("errors") or [])]


def is_rate_limited(body):
    """Whether a GraphQL envelope reports the budget as spent. Pure."""
    return "RATE_LIMITED" in error_types(body)


def in_band_cost(body):
    """The cost this query reported for itself. Pure. None if not asked for."""
    if not isinstance(body, dict):
        return None
    data = body.get("data")
    if not isinstance(data, dict):
        return None
    rl = data.get("rateLimit")
    if not isinstance(rl, dict):
        return None
    try:
        return int(rl.get("cost"))
    except (TypeError, ValueError):
        return None


def classify(graphql_b, core_b):
    """Compare the two buckets. Pure. Returns (state, detail).

    The point of comparing rather than reporting one is that the confusing case
    has a shape: one bucket empty, the other nearly full, same token.
    """
    g = used_fraction(graphql_b)
    c = used_fraction(core_b)
    if g is None:
        return ("unreadable",
                "resources.graphql was not present in the response, so the "
                "GraphQL budget cannot be read from it.")
    g_left = 1.0 - g
    c_left = 1.0 - c if c is not None else None
    g_empty = (graphql_b or {}).get("remaining") == 0
    c_empty = c_left is not None and (core_b or {}).get("remaining") == 0

    if g_empty and c_empty:
        return ("both-exhausted",
                "both buckets are empty, so this is not the confusing case: "
                "everything fails and everything is meant to.")
    if g_empty:
        return ("graphql-exhausted-rest-healthy",
                "the GraphQL bucket is empty while core is at %d%% remaining, so "
                "a REST health check reports green on a dead integration."
                % round((c_left or 0) * 100))
    if c_empty:
        return ("rest-exhausted-graphql-healthy",
                "core is empty and the GraphQL budget is at %d%% remaining. That "
                "is the REST hourly quota, not this one."
                % round(g_left * 100))
    if g_left < TIGHT:
        return ("graphql-tight",
                "%d%% of the GraphQL budget is left, which is close enough that "
                "the next burst decides it." % round(g_left * 100))
    return ("both-healthy",
            "%d%% of the GraphQL budget and %s of core are left."
            % (round(g_left * 100),
               "an unknown amount" if c_left is None else "%d%%" % round(c_left * 100)))


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "graphql-exhausted-rest-healthy":
        return ("throttle on resources.graphql.remaining, not on core. Add "
                "rateLimit { cost remaining } to your real queries so each one "
                "reports its own price, and point the health check at the bucket "
                "the traffic actually spends.")
    if state == "graphql-tight":
        return ("slow down now rather than at zero. Divide the remaining points "
                "by the measured cost of your query to get the number of calls "
                "you have left, and space them out.")
    if state == "rest-exhausted-graphql-healthy":
        return ("see /github/rate-limit-core-exhausted/ -- this is the REST "
                "hourly quota and the repair for it is conditional requests and "
                "webhooks, not point budgeting.")
    if state == "both-exhausted":
        return ("wait for the resets and then fix them separately: they refill "
                "on their own schedules and neither repair helps the other.")
    if state == "both-healthy":
        return ("nothing today. Measure the cost of your query anyway, because "
                "the budget in queries is what you schedule against and it is "
                "not 5,000.")
    return "read GET /rate_limit with a token this API accepts."


def point_cost(in_band):
    """Points this run will spend. Pure. Zero unless the in-band probe is asked for."""
    return 1 if in_band else 0


def fmt_reset(seconds):
    """A reset delay in something readable. Pure."""
    if seconds is None:
        return "unknown"
    if seconds < 90:
        return "%ds" % seconds
    return "%dm" % round(seconds / 60.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in-band", action="store_true",
                    help="spend one point sending { rateLimit { ... } } to "
                         "measure a query cost directly")
    ap.add_argument("--query",
                    help="measure this document's cost instead of the minimal "
                         "probe. Add rateLimit { cost remaining } to it first. "
                         "Mutations are refused.")
    ap.add_argument("--cost", type=int, default=1,
                    help="the cost of one of your queries, if you already know "
                         "it, used to convert points into queries")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    document = args.query or BUDGET_QUERY
    if args.in_band:
        why_not = refusal(document)
        if why_not:
            log.error("refusing to send: %s", why_not)
            return 2
        log.info("point cost: %d point(s) against the 5,000/hour GraphQL budget",
                 point_cost(True))
    else:
        log.info("point cost: %d point(s). GET /rate_limit reports the GraphQL "
                 "bucket and does not consume any of it.", point_cost(False))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
    })

    r = session.get(API + "/rate_limit", timeout=30)
    if r.status_code == 401:
        log.error("401 from GitHub: GITHUB_TOKEN is missing, malformed or revoked")
        return 2
    body = r.json() if r.status_code == 200 else None
    graphql_b = bucket(body, "graphql")
    core_b = bucket(body, "core")
    now = int(time.time())

    for name, b in (("core", core_b), ("graphql", graphql_b)):
        if b is None:
            log.info("%-8s not reported", name)
            continue
        log.info("%-8s %s / %s remaining, resets in %s",
                 name, b.get("remaining"), b.get("limit"),
                 fmt_reset(seconds_to_reset(b, now)))
    if graphql_b:
        log.info("budget: a limit of %s points/hour is %s",
                 graphql_b.get("limit"), identify_budget(graphql_b.get("limit")))

    state, detail = classify(graphql_b, core_b)
    log.info("%s: %s", state, detail)

    measured = args.cost
    envelope = None
    if args.in_band:
        # A GraphQL query is a read; POST is only how the document reaches the
        # endpoint, which is why the verb sits here beside the URL rather than
        # in a constant where it could be mistaken for a write path.
        resp = session.post(API + "/graphql", json={"query": document}, timeout=30)
        try:
            envelope = resp.json()
        except ValueError:
            envelope = None
        if is_rate_limited(envelope):
            log.info("the in-band probe itself came back RATE_LIMITED, which is "
                     "the finding stated by the endpoint rather than inferred")
        cost = in_band_cost(envelope)
        if cost is not None:
            measured = cost
            log.info("measured cost: %d point(s) for this query shape", cost)
        else:
            log.info("the response carried no rateLimit.cost; add "
                     "rateLimit { cost remaining } to the document")

    limit = (graphql_b or {}).get("limit")
    remaining = (graphql_b or {}).get("remaining")
    rate = sustainable_rate(limit, measured)
    gap = seconds_between(limit, measured)
    if rate:
        log.info("at %d points a query the budget is %d queries/hour, one every %ss",
                 measured, rate, gap)
    left = queries_left(remaining, measured)
    if left is not None:
        log.info("%s point(s) left is %d more quer%s of this shape",
                 remaining, left, "y" if left == 1 else "ies")
    log.info("repair: %s", repair(state))

    print(json.dumps({
        "points_spent": point_cost(args.in_band),
        "graphql": graphql_b,
        "core": core_b,
        "graphql_used_fraction": used_fraction(graphql_b),
        "core_used_fraction": used_fraction(core_b),
        "budget_identified_as": identify_budget(limit),
        "measured_cost": measured,
        "queries_per_hour": rate,
        "seconds_between_queries": gap,
        "queries_left": left,
        "in_band_rate_limited": is_rate_limited(envelope),
        "state": state,
        "detail": detail,
    }, indent=2, default=str))
    bad = {"graphql-exhausted-rest-healthy", "graphql-tight", "both-exhausted"}
    return 1 if state in bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-points.mjs",
"js": '''/**
 * Read the GraphQL point budget, which is not the REST one.
 *
 * Read only. The default run spends nothing: GET /rate_limit reports both
 * buckets and is documented not to count against either. The optional in-band
 * probe sends one query and costs one point, and it says so first.
 *
 * Queries only. GitHub's GraphQL endpoint takes a document in the request body,
 * so a read is carried by POST there just as a write would be; that is
 * transport, not intent. Any document containing a mutation or a subscription
 * is refused before a socket opens.
 *
 * Environment:
 *   GITHUB_TOKEN     a token with read access to the GraphQL API
 *   GITHUB_IN_BAND   set to spend one point measuring a query cost directly
 *   GITHUB_QUERY     measure this document instead of the minimal probe
 *   GITHUB_COST      the cost of one of your queries, if you already know it
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-points/1.0';

/** The published hourly point budgets, keyed by the actor they belong to. */
export const BUDGETS = {
  5000: 'a user token',
  1000: 'the GITHUB_TOKEN issued to a GitHub Actions workflow',
  10000: 'an Enterprise Cloud token',
};

const BUDGET_QUERY = 'query { rateLimit { limit cost remaining used resetAt nodeCount } }';

/** Below this fraction of budget left, slow down rather than discover zero. */
export const TIGHT = 0.2;

/** Remove GraphQL comments and string literals from a document. Pure. */
export function stripNoise(document) {
  const src = String(document ?? '');
  const out = [];
  let i = 0;
  while (i < src.length) {
    const ch = src[i];
    if (ch === '#') {
      while (i < src.length && src[i] !== '\\n') i += 1;
      continue;
    }
    if (src.startsWith('"""', i)) {
      const j = src.indexOf('"""', i + 3);
      i = j < 0 ? src.length : j + 3;
      out.push(' ');
      continue;
    }
    if (ch === '"') {
      i += 1;
      while (i < src.length && src[i] !== '"') i += src[i] === '\\\\' ? 2 : 1;
      i += 1;
      out.push(' ');
      continue;
    }
    out.push(ch);
    i += 1;
  }
  return out.join('');
}

/** The top-level operations in a document, in order. Pure. */
export function operations(document) {
  const src = `${stripNoise(document)} `;
  const ops = [];
  let depth = 0;
  let word = '';
  let declared = null;
  for (const ch of src) {
    if (/[A-Za-z0-9_]/.test(ch)) { word += ch; continue; }
    if (word) {
      if (depth === 0 && ['query', 'mutation', 'subscription', 'fragment'].includes(word)) {
        declared = word;
      }
      word = '';
    }
    if (ch === '{') {
      if (depth === 0) { ops.push(declared || 'query'); declared = null; }
      depth += 1;
    } else if (ch === '}') {
      depth = Math.max(0, depth - 1);
    }
  }
  return ops;
}

/** Why this document will not be sent, or null if it is a read. Pure. */
export function refusal(document) {
  const ops = operations(document);
  if (ops.length === 0) return 'the document contains no operation to send.';
  for (const kind of ['mutation', 'subscription']) {
    if (ops.includes(kind)) {
      return `the document contains a ${kind}. This script sends queries only: `
        + 'a query is a read, and the section it belongs to promises its '
        + 'scripts never write.';
    }
  }
  return null;
}

/** One resource object out of GET /rate_limit. Pure. null if absent. */
export function bucket(rateLimitBody, name) {
  if (!rateLimitBody || typeof rateLimitBody !== 'object') return null;
  const res = rateLimitBody.resources;
  if (!res || typeof res !== 'object') return null;
  const b = res[name];
  return b && typeof b === 'object' ? b : null;
}

/** How much of a bucket is gone, 0..1. Pure. null if unreadable. */
export function usedFraction(b) {
  if (!b || typeof b !== 'object') return null;
  const limit = Number(b.limit);
  const remaining = Number(b.remaining);
  if (!Number.isFinite(limit) || !Number.isFinite(remaining) || limit <= 0) return null;
  return Math.max(0, Math.min(1, (limit - remaining) / limit));
}

/** Seconds until this bucket refills. Pure. null if unreadable. */
export function secondsToReset(b, now) {
  if (!b || typeof b !== 'object') return null;
  const reset = Number(b.reset);
  const t = Number(now);
  if (!Number.isFinite(reset) || !Number.isFinite(t)) return null;
  return Math.max(0, Math.trunc(reset) - Math.trunc(t));
}

/** Which actor an observed hourly limit implies. Pure. */
export function identifyBudget(limit) {
  const n = Number(limit);
  if (!Number.isFinite(n)) return 'an unreadable limit';
  if (Object.prototype.hasOwnProperty.call(BUDGETS, String(Math.trunc(n)))) {
    return BUDGETS[String(Math.trunc(n))];
  }
  return `a limit of ${Math.trunc(n)}, which matches none of the published `
    + 'budgets. Read it as the truth and plan against it.';
}

/** How many more queries of this shape fit in what is left. Pure. */
export function queriesLeft(remaining, costPerQuery) {
  const rem = Number(remaining);
  const cost = Number(costPerQuery);
  if (!Number.isFinite(rem) || !Number.isFinite(cost) || cost <= 0) return null;
  return Math.max(0, Math.floor(rem / cost));
}

/** Queries per hour this budget supports at a measured cost. Pure. */
export function sustainableRate(limit, costPerQuery) {
  const lim = Number(limit);
  const cost = Number(costPerQuery);
  if (!Number.isFinite(lim) || !Number.isFinite(cost) || cost <= 0 || lim <= 0) return null;
  return Math.floor(lim / cost);
}

/** The gap to leave between queries to stay inside the budget. Pure. */
export function secondsBetween(limit, costPerQuery) {
  const rate = sustainableRate(limit, costPerQuery);
  if (!rate) return null;
  return Math.round((3600 / rate) * 10) / 10;
}

/** The type of every entry in a GraphQL errors array. Pure. */
export function errorTypes(body) {
  if (!body || typeof body !== 'object' || !Array.isArray(body.errors)) return [];
  return body.errors.map((e) => (e && typeof e === 'object' && e.type) || 'UNTYPED');
}

/** Whether a GraphQL envelope reports the budget as spent. Pure. */
export function isRateLimited(body) {
  return errorTypes(body).includes('RATE_LIMITED');
}

/** The cost this query reported for itself. Pure. null if not asked for. */
export function inBandCost(body) {
  if (!body || typeof body !== 'object') return null;
  const data = body.data;
  if (!data || typeof data !== 'object') return null;
  const rl = data.rateLimit;
  if (!rl || typeof rl !== 'object') return null;
  const cost = Number(rl.cost);
  return Number.isFinite(cost) ? Math.trunc(cost) : null;
}

/** Compare the two buckets. Pure. Returns [state, detail]. */
export function classify(graphqlB, coreB) {
  const g = usedFraction(graphqlB);
  const c = usedFraction(coreB);
  if (g === null) {
    return ['unreadable', 'resources.graphql was not present in the response, '
      + 'so the GraphQL budget cannot be read from it.'];
  }
  const gLeft = 1 - g;
  const cLeft = c === null ? null : 1 - c;
  const gEmpty = Number(graphqlB.remaining) === 0;
  const cEmpty = cLeft !== null && Number(coreB.remaining) === 0;

  if (gEmpty && cEmpty) {
    return ['both-exhausted', 'both buckets are empty, so this is not the '
      + 'confusing case: everything fails and everything is meant to.'];
  }
  if (gEmpty) {
    return ['graphql-exhausted-rest-healthy',
      `the GraphQL bucket is empty while core is at ${Math.round((cLeft || 0) * 100)}% `
      + 'remaining, so a REST health check reports green on a dead integration.'];
  }
  if (cEmpty) {
    return ['rest-exhausted-graphql-healthy',
      `core is empty and the GraphQL budget is at ${Math.round(gLeft * 100)}% `
      + 'remaining. That is the REST hourly quota, not this one.'];
  }
  if (gLeft < TIGHT) {
    return ['graphql-tight', `${Math.round(gLeft * 100)}% of the GraphQL budget `
      + 'is left, which is close enough that the next burst decides it.'];
  }
  return ['both-healthy', `${Math.round(gLeft * 100)}% of the GraphQL budget and `
    + `${cLeft === null ? 'an unknown amount' : `${Math.round(cLeft * 100)}%`} of core are left.`];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'graphql-exhausted-rest-healthy') {
    return 'throttle on resources.graphql.remaining, not on core. Add '
      + 'rateLimit { cost remaining } to your real queries so each one reports '
      + 'its own price, and point the health check at the bucket the traffic '
      + 'actually spends.';
  }
  if (state === 'graphql-tight') {
    return 'slow down now rather than at zero. Divide the remaining points by '
      + 'the measured cost of your query to get the number of calls you have '
      + 'left, and space them out.';
  }
  if (state === 'rest-exhausted-graphql-healthy') {
    return 'see /github/rate-limit-core-exhausted/ -- this is the REST hourly '
      + 'quota and the repair for it is conditional requests and webhooks, not '
      + 'point budgeting.';
  }
  if (state === 'both-exhausted') {
    return 'wait for the resets and then fix them separately: they refill on '
      + 'their own schedules and neither repair helps the other.';
  }
  if (state === 'both-healthy') {
    return 'nothing today. Measure the cost of your query anyway, because the '
      + 'budget in queries is what you schedule against and it is not 5,000.';
  }
  return 'read GET /rate_limit with a token this API accepts.';
}

/** Points this run will spend. Pure. Zero unless the in-band probe is asked for. */
export function pointCost(inBand) {
  return inBand ? 1 : 0;
}

/** A reset delay in something readable. Pure. */
export function fmtReset(seconds) {
  if (seconds === null || seconds === undefined) return 'unknown';
  const n = Number(seconds);
  if (!Number.isFinite(n)) return 'unknown';
  return n < 90 ? `${Math.trunc(n)}s` : `${Math.round(n / 60)}m`;
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'Content-Type': 'application/json',
    'User-Agent': UA,
  };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (read-only is enough)');
    process.exitCode = 2;
    return;
  }
  const inBand = Boolean(process.env.GITHUB_IN_BAND);
  const document = process.env.GITHUB_QUERY || BUDGET_QUERY;
  if (inBand) {
    const whyNot = refusal(document);
    if (whyNot) {
      console.error(`refusing to send: ${whyNot}`);
      process.exitCode = 2;
      return;
    }
    console.log(`point cost: ${pointCost(true)} point(s) against the 5,000/hour GraphQL budget`);
  } else {
    console.log(`point cost: ${pointCost(false)} point(s). GET /rate_limit reports `
      + 'the GraphQL bucket and does not consume any of it.');
  }

  const res = await fetch(`${API}/rate_limit`, { headers: headers(token) });
  if (res.status === 401) {
    console.error('401 from GitHub: GITHUB_TOKEN is missing, malformed or revoked');
    process.exitCode = 2;
    return;
  }
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  const graphqlB = bucket(body, 'graphql');
  const coreB = bucket(body, 'core');
  const now = Math.trunc(Date.now() / 1000);

  for (const [name, b] of [['core', coreB], ['graphql', graphqlB]]) {
    if (!b) { console.log(`${name.padEnd(8)} not reported`); continue; }
    console.log(`${name.padEnd(8)} ${b.remaining} / ${b.limit} remaining, `
      + `resets in ${fmtReset(secondsToReset(b, now))}`);
  }
  if (graphqlB) {
    console.log(`budget: a limit of ${graphqlB.limit} points/hour is ${identifyBudget(graphqlB.limit)}`);
  }

  const [state, detail] = classify(graphqlB, coreB);
  console.log(`${state}: ${detail}`);

  let measured = Number(process.env.GITHUB_COST || 1);
  let envelope = null;
  if (inBand) {
    const probe = await fetch(`${API}/graphql`, {
      // A GraphQL query is a read. POST is only how the document reaches the
      // endpoint, and refusal() has already rejected anything that is not.
      method: 'POST',
      headers: headers(token),
      body: JSON.stringify({ query: document }),
    });
    try { envelope = await probe.json(); } catch { envelope = null; }
    if (isRateLimited(envelope)) {
      console.log('the in-band probe itself came back RATE_LIMITED, which is the '
        + 'finding stated by the endpoint rather than inferred');
    }
    const cost = inBandCost(envelope);
    if (cost !== null) {
      measured = cost;
      console.log(`measured cost: ${cost} point(s) for this query shape`);
    } else {
      console.log('the response carried no rateLimit.cost; add '
        + 'rateLimit { cost remaining } to the document');
    }
  }

  const limit = graphqlB ? graphqlB.limit : null;
  const remaining = graphqlB ? graphqlB.remaining : null;
  const rate = sustainableRate(limit, measured);
  const gap = secondsBetween(limit, measured);
  if (rate) {
    console.log(`at ${measured} points a query the budget is ${rate} queries/hour, one every ${gap}s`);
  }
  const left = queriesLeft(remaining, measured);
  if (left !== null) {
    console.log(`${remaining} point(s) left is ${left} more quer${left === 1 ? 'y' : 'ies'} of this shape`);
  }
  console.log(`repair: ${repair(state)}`);

  console.log(JSON.stringify({
    points_spent: pointCost(inBand),
    graphql: graphqlB,
    core: coreB,
    graphql_used_fraction: usedFraction(graphqlB),
    core_used_fraction: usedFraction(coreB),
    budget_identified_as: identifyBudget(limit),
    measured_cost: measured,
    queries_per_hour: rate,
    seconds_between_queries: gap,
    queries_left: left,
    in_band_rate_limited: isRateLimited(envelope),
    state,
    detail,
  }, null, 2));
  const bad = ['graphql-exhausted-rest-healthy', 'graphql-tight', 'both-exhausted'];
  process.exitCode = bad.includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The comparison carries the note, so the suite spends most of its time on pairs of buckets: GraphQL empty beside a healthy core, which is the case that wastes an afternoon; core empty beside a healthy GraphQL, which belongs to a different note and is sent there by name; both empty, which is confusing in no way at all. After that, the arithmetic that turns points into something schedulable, asserted at a realistic cost rather than at one, the reverse lookup from an observed limit to the actor it implies, and the point cost, which has to be zero on the default run because the whole claim is that reading the budget is free.",
"test_py_file": "test_github_graphql_points.py",
"test_py": '''from github_graphql_points import (
    TIGHT, bucket, classify, fmt_reset, identify_budget, in_band_cost,
    is_rate_limited, operations, point_cost, queries_left, refusal, repair,
    seconds_between, seconds_to_reset, sustainable_rate, used_fraction,
)


def rl(core_remaining, graphql_remaining, core_limit=5000, graphql_limit=5000):
    return {"resources": {
        "core": {"limit": core_limit, "remaining": core_remaining,
                 "used": core_limit - core_remaining, "reset": 1_800_000_000},
        "graphql": {"limit": graphql_limit, "remaining": graphql_remaining,
                    "used": graphql_limit - graphql_remaining, "reset": 1_800_000_000},
    }}


def test_the_two_buckets_are_read_separately():
    body = rl(4983, 0)
    assert bucket(body, "core")["remaining"] == 4983
    assert bucket(body, "graphql")["remaining"] == 0
    assert bucket(body, "search") is None
    assert bucket({}, "graphql") is None


def test_an_empty_graphql_bucket_beside_a_healthy_core_is_the_headline():
    body = rl(4983, 0)
    state, detail = classify(bucket(body, "graphql"), bucket(body, "core"))
    assert state == "graphql-exhausted-rest-healthy"
    assert "health check reports green" in detail
    assert "resources.graphql.remaining" in repair(state)


def test_an_empty_core_beside_a_healthy_graphql_belongs_to_another_note():
    body = rl(0, 4983)
    state, _ = classify(bucket(body, "graphql"), bucket(body, "core"))
    assert state == "rest-exhausted-graphql-healthy"
    assert "rate-limit-core-exhausted" in repair(state)
    assert "point budgeting" in repair(state)


def test_both_empty_is_not_the_confusing_case():
    body = rl(0, 0)
    state, detail = classify(bucket(body, "graphql"), bucket(body, "core"))
    assert state == "both-exhausted"
    assert "not the confusing case" in detail


def test_a_tight_budget_is_flagged_before_it_reaches_zero():
    body = rl(4983, 500)
    state, _ = classify(bucket(body, "graphql"), bucket(body, "core"))
    assert state == "graphql-tight"
    assert TIGHT == 0.2
    healthy = rl(4983, 4000)
    assert classify(bucket(healthy, "graphql"), bucket(healthy, "core"))[0] == "both-healthy"


def test_a_missing_graphql_bucket_is_reported_rather_than_assumed_full():
    state, _ = classify(None, {"limit": 5000, "remaining": 4983})
    assert state == "unreadable"


def test_used_fraction_survives_a_bucket_that_makes_no_sense():
    assert used_fraction({"limit": 5000, "remaining": 2500}) == 0.5
    assert used_fraction({"limit": 0, "remaining": 0}) is None
    assert used_fraction({"limit": "many", "remaining": 1}) is None
    assert used_fraction(None) is None


def test_points_are_converted_into_the_unit_you_can_schedule():
    assert sustainable_rate(5000, 12) == 416
    assert seconds_between(5000, 12) == 8.7
    assert queries_left(1200, 12) == 100
    assert queries_left(11, 12) == 0


def test_the_conversion_refuses_a_cost_that_cannot_be_divided_by():
    assert sustainable_rate(5000, 0) is None
    assert queries_left(1200, 0) is None
    assert seconds_between(5000, "free") is None


def test_an_observed_limit_names_the_actor_it_belongs_to():
    assert identify_budget(5000) == "a user token"
    assert "GitHub Actions" in identify_budget(1000)
    assert "Enterprise Cloud" in identify_budget(10000)
    assert "matches none of the published budgets" in identify_budget(2500)


def test_the_error_type_is_read_from_the_envelope_not_the_status():
    assert is_rate_limited({"errors": [{"type": "RATE_LIMITED"}]})
    assert not is_rate_limited({"errors": [{"type": "NOT_FOUND"}]})
    assert not is_rate_limited({"data": {"rateLimit": {"cost": 1}}})
    assert not is_rate_limited(None)


def test_the_in_band_cost_is_read_only_when_it_was_asked_for():
    assert in_band_cost({"data": {"rateLimit": {"cost": 12, "remaining": 4988}}}) == 12
    assert in_band_cost({"data": {"viewer": {"login": "ada"}}}) is None
    assert in_band_cost({"data": None}) is None


def test_the_reset_delay_is_readable_and_never_negative():
    assert seconds_to_reset({"reset": 1000}, 940) == 60
    assert seconds_to_reset({"reset": 1000}, 2000) == 0
    assert seconds_to_reset({}, 100) is None
    assert fmt_reset(45) == "45s"
    assert fmt_reset(720) == "12m"
    assert fmt_reset(None) == "unknown"


def test_the_default_run_spends_nothing():
    assert point_cost(False) == 0
    assert point_cost(True) == 1


def test_the_script_refuses_to_send_a_mutation():
    assert operations("query { rateLimit { cost } }") == ["query"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal("query { rateLimit { cost remaining } }") is None
''',
"test_js_file": "github-graphql-points.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  TIGHT, bucket, classify, fmtReset, identifyBudget, inBandCost, isRateLimited,
  operations, pointCost, queriesLeft, refusal, repair, secondsBetween,
  secondsToReset, sustainableRate, usedFraction,
} from './github-graphql-points.mjs';

function rl(coreRemaining, graphqlRemaining, coreLimit = 5000, graphqlLimit = 5000) {
  return {
    resources: {
      core: {
        limit: coreLimit,
        remaining: coreRemaining,
        used: coreLimit - coreRemaining,
        reset: 1800000000,
      },
      graphql: {
        limit: graphqlLimit,
        remaining: graphqlRemaining,
        used: graphqlLimit - graphqlRemaining,
        reset: 1800000000,
      },
    },
  };
}

test('the two buckets are read separately', () => {
  const body = rl(4983, 0);
  assert.equal(bucket(body, 'core').remaining, 4983);
  assert.equal(bucket(body, 'graphql').remaining, 0);
  assert.equal(bucket(body, 'search'), null);
  assert.equal(bucket({}, 'graphql'), null);
});

test('an empty GraphQL bucket beside a healthy core is the headline', () => {
  const body = rl(4983, 0);
  const [state, detail] = classify(bucket(body, 'graphql'), bucket(body, 'core'));
  assert.equal(state, 'graphql-exhausted-rest-healthy');
  assert.match(detail, /health check reports green/);
  assert.match(repair(state), /resources\\.graphql\\.remaining/);
});

test('an empty core beside a healthy GraphQL belongs to another note', () => {
  const body = rl(0, 4983);
  const [state] = classify(bucket(body, 'graphql'), bucket(body, 'core'));
  assert.equal(state, 'rest-exhausted-graphql-healthy');
  assert.match(repair(state), /rate-limit-core-exhausted/);
  assert.match(repair(state), /point budgeting/);
});

test('both empty is not the confusing case', () => {
  const body = rl(0, 0);
  const [state, detail] = classify(bucket(body, 'graphql'), bucket(body, 'core'));
  assert.equal(state, 'both-exhausted');
  assert.match(detail, /not the confusing case/);
});

test('a tight budget is flagged before it reaches zero', () => {
  const body = rl(4983, 500);
  assert.equal(classify(bucket(body, 'graphql'), bucket(body, 'core'))[0], 'graphql-tight');
  assert.equal(TIGHT, 0.2);
  const healthy = rl(4983, 4000);
  assert.equal(
    classify(bucket(healthy, 'graphql'), bucket(healthy, 'core'))[0],
    'both-healthy',
  );
});

test('a missing GraphQL bucket is reported rather than assumed full', () => {
  const [state] = classify(null, { limit: 5000, remaining: 4983 });
  assert.equal(state, 'unreadable');
});

test('usedFraction survives a bucket that makes no sense', () => {
  assert.equal(usedFraction({ limit: 5000, remaining: 2500 }), 0.5);
  assert.equal(usedFraction({ limit: 0, remaining: 0 }), null);
  assert.equal(usedFraction({ limit: 'many', remaining: 1 }), null);
  assert.equal(usedFraction(null), null);
});

test('points are converted into the unit you can schedule', () => {
  assert.equal(sustainableRate(5000, 12), 416);
  assert.equal(secondsBetween(5000, 12), 8.7);
  assert.equal(queriesLeft(1200, 12), 100);
  assert.equal(queriesLeft(11, 12), 0);
});

test('the conversion refuses a cost that cannot be divided by', () => {
  assert.equal(sustainableRate(5000, 0), null);
  assert.equal(queriesLeft(1200, 0), null);
  assert.equal(secondsBetween(5000, 'free'), null);
});

test('an observed limit names the actor it belongs to', () => {
  assert.equal(identifyBudget(5000), 'a user token');
  assert.match(identifyBudget(1000), /GitHub Actions/);
  assert.match(identifyBudget(10000), /Enterprise Cloud/);
  assert.match(identifyBudget(2500), /matches none of the published budgets/);
});

test('the error type is read from the envelope, not the status', () => {
  assert.ok(isRateLimited({ errors: [{ type: 'RATE_LIMITED' }] }));
  assert.ok(!isRateLimited({ errors: [{ type: 'NOT_FOUND' }] }));
  assert.ok(!isRateLimited({ data: { rateLimit: { cost: 1 } } }));
  assert.ok(!isRateLimited(null));
});

test('the in-band cost is read only when it was asked for', () => {
  assert.equal(inBandCost({ data: { rateLimit: { cost: 12, remaining: 4988 } } }), 12);
  assert.equal(inBandCost({ data: { viewer: { login: 'ada' } } }), null);
  assert.equal(inBandCost({ data: null }), null);
});

test('the reset delay is readable and never negative', () => {
  assert.equal(secondsToReset({ reset: 1000 }, 940), 60);
  assert.equal(secondsToReset({ reset: 1000 }, 2000), 0);
  assert.equal(secondsToReset({}, 100), null);
  assert.equal(fmtReset(45), '45s');
  assert.equal(fmtReset(720), '12m');
  assert.equal(fmtReset(null), 'unknown');
});

test('the default run spends nothing', () => {
  assert.equal(pointCost(false), 0);
  assert.equal(pointCost(true), 1);
});

test('the script refuses to send a mutation', () => {
  assert.deepEqual(operations('query { rateLimit { cost } }'), ['query']);
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.equal(refusal('query { rateLimit { cost remaining } }'), null);
});
''',
"faq": [
 ("Why does my REST health check say the token is fine?",
  "Because it is fine, for REST. The GraphQL budget and the REST core quota are separate buckets with separate limits, separate counters and separate reset times, and GET /rate_limit returns them as two independent objects. A check that reads resources.core is reporting on traffic that has nothing to do with the traffic that is failing. Point the check at resources.graphql, or better, at both, and print them together so the difference is impossible to miss."),
 ("Is 5,000 points the same as 5,000 queries?",
  "Almost never. A point cost is derived from the connections a query traverses and the number of items each one asks for, so a flat query costs a point or two and one that fans out over repositories and their pull requests can cost dozens. Measure yours by adding rateLimit { cost remaining } to the document and reading the number back. At twelve points a query the real budget is 416 calls an hour, which is a schedule; 5,000 points is not."),
 ("How is this different from the secondary rate limit?",
  "Different bucket, different window, different evidence. The GraphQL budget is 5,000 points an hour, it is reported by GET /rate_limit before you hit it, and running out produces a 200 with RATE_LIMITED in the errors array. The secondary limit is a per-minute cap on a single REST endpoint, it appears in no response header at all, and it announces itself as a 403 or 429 after the fact. They have separate notes because they are found by separate means."),
 ("My budget disappears and my own queries do not account for it. Where did it go?",
  "The API cannot tell you, and that is a documented blind spot rather than a gap in this script. The bucket belongs to the token and is shared by every process holding it, so a scheduled job, a developer's laptop and a bot can all be drawing on the same 5,000 points while each of them believes it is the only consumer. The only repair that makes the number mean something is a separate token per workload, after which the drain is attributable by construction."),
 ("Does asking for the budget cost anything?",
  "GET /rate_limit is free and reports both buckets, which is why this script uses it by default and prints a point cost of zero. Adding rateLimit { cost remaining } to a query you were already sending is also effectively free, since it rides along on a request you were making anyway, and it is the only way to learn the price of that specific shape. Sending a query whose sole purpose is to ask about the budget costs one point, which is what --in-band does and what it announces before doing."),
],
"related": [
 ("/github/rate-limit-core-exhausted/", "The REST core quota is empty"),
 ("/github/secondary-limit-points-per-minute/", "A hot endpoint burns 900 points a minute"),
 ("/github/graphql-node-limit-exceeded/", "A query over the 500,000 node limit"),
],
"citations": [CITE_GQL_RATE, CITE_REST_RATE_LIMIT, CITE_REST_RATE_LIMITS, CITE_GQL_RESOURCE],
},

{
"slug": "graphql-node-limit-exceeded",
"title": "A nested GraphQL query requests more than 500,000 nodes",
"description": "Three levels of first: 100 asks for 1,010,100 nodes against a cap of 500,000. GitHub rejects the query before running it, however small the org is.",
"h1": "A nested GraphQL query requests more than 500,000 nodes",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["No token needed", "Python and Node.js", "Tests included"],
"keywords": ["github graphql MAX_NODE_LIMIT_EXCEEDED",
             "graphql node limit 500000 github",
             "github graphql query requests too many nodes",
             "github graphql nodeCount rateLimit",
             "github graphql nested first 100 error"],
"deps": "Python 3.9+, or Node.js 18+. No token required.",
"lead": "The query worked all week against the test org, which has four repositories. Pointed at the real one it comes back rejected with <code>MAX_NODE_LIMIT_EXCEEDED</code> before a single row is read. The instinct is that the org is too big, so somebody reduces the date range and it fails identically, because the limit was never about how much data exists. It is about the numbers written in the query, and those did not change.",
"short_answer": """<p>GitHub caps a single GraphQL query at 500,000 nodes, and the count is computed from the <code>first</code> and <code>last</code> values you <em>requested</em>, multiplied down through the nesting. One hundred repositories, each with one hundred pull requests, each with one hundred comments is <code>100 + 10,000 + 1,000,000</code>, which is 1,010,100 nodes and over the cap. The query is rejected before execution, so a small organisation fails exactly as fast as a large one.</p>
<p>The repair is arithmetic rather than filtering. Lower the <code>first</code> values at the deepest levels, where the multiplier is largest, and page those connections separately with <code>pageInfo { hasNextPage endCursor }</code>. Because the whole calculation depends only on the query text, you can do it without sending anything: this is the one check in the section that needs no token and spends no points.</p>""",
"problem": """<p>The query gets built by a reasonable process. Someone needs repositories, their pull requests and the comments on those pull requests, and writing that as one GraphQL document instead of ten thousand REST calls is exactly the right instinct. Then <code>first: 100</code> goes on every connection, because 100 is the maximum and asking for the maximum means fewer round trips, which is the lesson everybody learned from the REST pagination bugs. Both decisions are individually correct and together they are a million nodes.</p>
<p>It passes review for the same reason. Nothing in the document looks large; it is about fifteen lines and every number in it is 100. The multiplication that makes it enormous happens nowhere on the screen, and there is no linter watching for it, so the query goes to production with the same confidence as any other.</p>
<p>The failure then misleads on arrival. Everything about the error says "too much data" and the org is the biggest thing in sight, so the fix people reach for is a narrower filter: a date range, a label, an archived-repository exclusion. None of it helps, because the cost is derived from what the query asks for rather than from what exists, and the numbers being asked for are still 100. Watching four consecutive narrower filters fail identically is the part that eats the afternoon.</p>""",
"why": """<p><strong>The count multiplies, it does not add.</strong> Each connection contributes the product of its own <code>first</code> and every <code>first</code> above it. Three levels of 100 is <code>100 + (100 &times; 100) + (100 &times; 100 &times; 100)</code>, so the deepest level supplies 99 per cent of the total on its own. That is also why the repair is aimed at the bottom of the query: halving the outermost number halves everything, but lowering the innermost one is where the cheap wins are.</p>
<p><strong>It is computed from the request, not the response.</strong> A limit derived from what exists could be discovered by trying. This one is derived from the document, which is why the same query fails against an organisation with four repositories and against one with four thousand. It also means the whole thing can be decided statically, before anything is sent, which is what this script does.</p>
<p><strong>Rejection happens before execution, so it costs nothing and teaches nothing.</strong> There is no partial result and no indication of which connection was responsible. The error names the limit and stops. If you want the actual number, ask for <code>rateLimit { nodeCount cost }</code> in a query small enough to run, and the server will report the computed node total for that call.</p>
<p><strong>It is not the point budget.</strong> Points measure what a query costs against an hourly allowance and <a href="/github/graphql-rate-limited/">running out of them is a different failure with a different error type</a>: it clears on its own, and the same query will succeed later. A node-limit rejection never clears. Nothing about waiting, retrying or having more quota changes it, because the query itself is the thing that is too large, and a retry loop that does not know the difference will spin against it until the point budget is gone as well.</p>
<p><strong>The static count has two honest blind spots.</strong> A <code>first</code> supplied as a variable cannot be evaluated without the variables, so the script asks for them rather than guessing. And a named fragment spread hides part of the selection set from a text-level analyser, so the computed total is a lower bound when one is present. Both are reported as caveats rather than quietly rolled into the number.</p>
<p><strong>A connection with no <code>first</code> at all is a separate error.</strong> GitHub requires a slicing argument on connections, so leaving one off is rejected too, with a different message. That is a schema problem rather than a size problem and this script does not attempt to diagnose it; the node count it reports simply does not include a connection it could not see a number for.</p>""",
"steps": [
 {"h": "Compute the node count before you send anything",
  "body": """<p>Feed the query text to the checker. It walks the document, multiplies each connection's <code>first</code> by the product of everything above it, and prints the total against the 500,000 cap. No token, no request, no points. This runs in CI on a file of queries as easily as it runs on one.</p>"""},
 {"h": "Look at where the nodes actually are",
  "body": """<p>The per-connection breakdown almost always shows one line carrying the overwhelming majority. In the three-level example the comments connection is 1,000,000 of the 1,010,100. Knowing that turns a vague "make the query smaller" into a specific number to change in a specific place.</p>"""},
 {"h": "Take the suggested value at the deepest level",
  "body": """<p>The script solves for the largest <code>first</code> at the deepest connection that brings the total under the cap and prints it. For the example that is 48. It is a starting point rather than a target: a smaller number leaves headroom for the day somebody adds another level.</p>"""},
 {"h": "Page the connection you shrank",
  "body": """<p>Reducing a <code>first</code> only helps if the rest of the data is still reachable, so add <code>pageInfo { hasNextPage endCursor }</code> to the connection you shrank and follow the cursor. One hundred repositories with ten pull requests each, paging the pull requests, reads the same data as one hundred by one hundred and stays comfortably inside the limit.</p>"""},
 {"h": "Confirm against the server only if you want to",
  "body": """<p><code>--confirm</code> sends the document and reports whether GitHub agrees, either by rejecting it or by returning <code>rateLimit { nodeCount }</code> if the document asks for it. That costs one point and the script says so first. It is not required: the arithmetic is the same arithmetic the server does.</p>"""},
],
"verify": """<p>The check runs on a file in CI, with no token, and the repair is a number rather than an instruction.</p>
<pre><code class="language-bash">python3 github_graphql_nodes.py --file queries/org_activity.graphql
# point cost: 0 point(s). The node count is computed from the query text and
# nothing is sent.
# node count: 1,010,100 against a limit of 500,000
#   repositories     first=100   depth 3   ancestors x1        100 nodes
#   pullRequests     first=100   depth 5   ancestors x100      10,000 nodes
#   comments         first=100   depth 7   ancestors x10,000   1,000,000 nodes
# over-node-limit: 1,010,100 nodes is 202% of the 500,000 cap, so this query is
# rejected before it runs whatever the organisation contains
# repair: lower first on comments from 100 to 48 and paginate it separately
# with pageInfo { hasNextPage endCursor }

# after the change
# node count: 490,100 against a limit of 500,000
# near-node-limit: 98% of the cap, which leaves no room for another level</code></pre>""",
"code_intro": "A parser and some multiplication. The document is stripped of comments and string literals, walked once while a stack of multipliers is maintained, and every connection carrying a <code>first</code> or <code>last</code> contributes the product of that value and everything above it. The total, the per-connection breakdown and the largest value the deepest connection could take are all pure functions of the text, so the default run opens no socket and needs no credential. Confirming against the server is one opt-in point, announced before it is spent.",
"py_file": "github_graphql_nodes.py",
"py": '''"""Compute a GraphQL query's node count from its text, before sending it.

Read only, and by default not even that: the node count is derived from the
query document, so the standard run makes no request, needs no token and spends
no points. The optional --confirm sends the document once and costs one point.

Queries only. GitHub's GraphQL endpoint takes a document in the request body, so
a read is carried by POST there just as a write would be; that is transport, not
intent. Any document containing a mutation or a subscription is refused before a
socket opens. Nothing is written and the repair is printed rather than performed.

GitHub caps one query at 500,000 nodes and computes the count from the first and
last values you requested, multiplied down through the nesting. Three levels of
first: 100 is 100 + 10,000 + 1,000,000 nodes. Because the cost comes from the
request rather than from what exists, a four-repository organisation fails
exactly as a four-thousand-repository one does.

What this can and cannot see: a first supplied as a variable cannot be evaluated
without the variables, and a named fragment spread hides part of the selection
set from a text-level analyser. Both are reported as caveats rather than folded
silently into the number.
"""
import argparse
import json
import logging
import os
import re
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_nodes")

API = "https://api.github.com"
UA = "github-graphql-nodes/1.0"

# The documented ceiling on one query. Named because it is printed and a reader
# checking this against the documentation should find it in one place.
NODE_LIMIT = 500_000

# Above this fraction of the cap, say so: a query at 98 per cent is one schema
# change away from being rejected.
NEAR = 0.8

# The canonical shape of the problem, used when no document is supplied.
DEMO_QUERY = """query {
  organization(login: "acme") {
    repositories(first: 100) {
      nodes {
        pullRequests(first: 100) {
          nodes {
            comments(first: 100) { nodes { id } }
          }
        }
      }
    }
  }
}"""

PAGING = re.compile(r"\\b(first|last)\\s*:\\s*(\\$?[A-Za-z0-9_]+)")
SPREAD = re.compile(r"\\.\\.\\.\\s*([A-Za-z_][A-Za-z0-9_]*)")


def strip_noise(document):
    """Remove GraphQL comments and string literals from a document. Pure."""
    src = str(document or "")
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "#":
            while i < n and src[i] != "\\n":
                i += 1
            continue
        if src.startswith('"""', i):
            j = src.find('"""', i + 3)
            i = n if j < 0 else j + 3
            out.append(" ")
            continue
        if ch == '"':
            i += 1
            while i < n and src[i] != '"':
                i += 2 if src[i] == "\\\\" else 1
            i += 1
            out.append(" ")
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def operations(document):
    """The top-level operations in a document, in order. Pure."""
    src = strip_noise(document)
    ops, depth, word, declared = [], 0, "", None
    for ch in src + " ":
        if ch.isalnum() or ch == "_":
            word += ch
            continue
        if word:
            if depth == 0 and word in ("query", "mutation", "subscription", "fragment"):
                declared = word
            word = ""
        if ch == "{":
            if depth == 0:
                ops.append(declared or "query")
                declared = None
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
    return ops


def refusal(document):
    """Why this document will not be sent, or None if it is a read. Pure."""
    ops = operations(document)
    if not ops:
        return "the document contains no operation to send."
    for kind in ("mutation", "subscription"):
        if kind in ops:
            return ("the document contains a %s. This script sends queries only: "
                    "a query is a read, and the section it belongs to promises "
                    "its scripts never write." % kind)
    return None


def commas(n):
    """Group a count in thousands so it can be read at a glance. Pure."""
    try:
        return "{:,}".format(int(n))
    except (TypeError, ValueError):
        return str(n)


def _paging(field, args, variables):
    """The slicing argument on one field, if there is one. Pure."""
    m = PAGING.search(args or "")
    if not m:
        return None
    arg, raw = m.group(1), m.group(2)
    variable = raw[1:] if raw.startswith("$") else None
    value = (variables or {}).get(variable) if variable else raw
    try:
        requested = int(value)
    except (TypeError, ValueError):
        requested = None
    return {"field": field or "?", "arg": arg, "variable": variable,
            "requested": requested}


def connections(document, variables=None):
    """Every sliced connection in a document, with its node contribution. Pure.

    Walks the text once with a stack of multipliers. A connection contributes
    the product of its own first/last and every one enclosing it, which is the
    rule the server applies and the reason a three-level query is a million
    nodes rather than three hundred.
    """
    src = strip_noise(document)
    out, stack, pending, field = [], [], None, None
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "(":
            j = src.find(")", i)
            args = src[i + 1:j] if j >= 0 else src[i + 1:]
            found = _paging(field, args, variables)
            # Only overwrite a pending slice when this argument group carries one,
            # so a directive such as @include(if: $x) cannot erase the first:
            # value that came immediately before it.
            if found is not None:
                pending = found
            i = n if j < 0 else j + 1
            continue
        if ch == "{":
            if pending is not None:
                ancestors = 1
                for m in stack:
                    ancestors *= m
                rec = dict(pending)
                rec["depth"] = len(stack) + 1
                rec["ancestors"] = ancestors
                rec["nodes"] = (None if rec["requested"] is None
                                else ancestors * rec["requested"])
                out.append(rec)
                stack.append(rec["requested"] if rec["requested"] else 1)
            else:
                stack.append(1)
            pending, field = None, None
            i += 1
            continue
        if ch == "}":
            if stack:
                stack.pop()
            pending, field = None, None
            i += 1
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            field = src[i:j]
            i = j
            continue
        i += 1
    return out


def node_count(document, variables=None):
    """The node total the server will compute for this document. Pure."""
    return sum(c["nodes"] for c in connections(document, variables)
               if c["nodes"] is not None)


def unresolved(document, variables=None):
    """Connections whose slice is a variable nobody supplied. Pure."""
    return [c["field"] for c in connections(document, variables)
            if c["requested"] is None]


def fragment_spreads(document):
    """Named fragment spreads, which hide part of the selection set. Pure."""
    src = strip_noise(document)
    return sorted({m.group(1) for m in SPREAD.finditer(src) if m.group(1) != "on"})


def caveats(document, variables=None):
    """Everything that makes the computed total less than certain. Pure."""
    out = []
    missing = unresolved(document, variables)
    if missing:
        out.append("the slice on %s is a variable this run has no value for, so "
                   "those connections are not in the total. Pass --variables."
                   % ", ".join(sorted(set(missing))))
    spreads = fragment_spreads(document)
    if spreads:
        out.append("the document spreads the fragment(s) %s, whose selection set "
                   "this text-level check does not expand, so the total is a "
                   "lower bound." % ", ".join(spreads))
    return out


def deepest(document, variables=None):
    """The connection carrying the largest multiplier. Pure. None if there is none."""
    resolved = [c for c in connections(document, variables) if c["nodes"] is not None]
    if not resolved:
        return None
    return max(resolved, key=lambda c: (c["depth"], c["nodes"]))


def reshape(document, variables=None, limit=NODE_LIMIT):
    """The largest slice the deepest connection could take. Pure.

    Returns (field, current, suggested). suggested is None when even a slice of
    one leaves the query over the cap, which means the shape itself has to
    change rather than a number in it.
    """
    d = deepest(document, variables)
    if d is None:
        return (None, None, None)
    total = node_count(document, variables)
    without = total - d["nodes"]
    room = limit - without
    if d["ancestors"] <= 0:
        return (d["field"], d["requested"], None)
    k = room // d["ancestors"]
    if k < 1:
        return (d["field"], d["requested"], None)
    return (d["field"], d["requested"], int(min(k, 100)))


def exceeds(count, limit=NODE_LIMIT):
    """Whether this node total is over the cap. Pure."""
    try:
        return int(count) > int(limit)
    except (TypeError, ValueError):
        return False


def verdict(document, variables=None, limit=NODE_LIMIT):
    """Classify one document. Pure. Returns (state, detail)."""
    conns = connections(document, variables)
    if not conns:
        return ("no-connections",
                "this document slices no connections, so it has no node count "
                "worth speaking of.")
    if any(c["nodes"] is None for c in conns):
        return ("unresolved-variables",
                "at least one slice is a variable with no value supplied, so the "
                "node count cannot be computed from the text alone.")
    total = node_count(document, variables)
    pct = round(100.0 * total / float(limit))
    if exceeds(total, limit):
        return ("over-node-limit",
                "%s nodes is %d%% of the %s cap, so this query is rejected before "
                "it runs whatever the organisation contains."
                % (commas(total), pct, commas(limit)))
    if total > limit * NEAR:
        return ("near-node-limit",
                "%s nodes is %d%% of the cap, which leaves no room for another "
                "level." % (commas(total), pct))
    return ("within-node-limit",
            "%s nodes is %d%% of the cap." % (commas(total), pct))


def repair(state, field=None, current=None, suggested=None):
    """The sentence a reader has to act on. Pure."""
    if state in ("over-node-limit", "near-node-limit"):
        if suggested is not None:
            return ("lower first on %s from %s to %d and paginate it separately "
                    "with pageInfo { hasNextPage endCursor }."
                    % (field, current, suggested))
        return ("even a slice of one on %s leaves this query over the cap, so "
                "split it into separate queries rather than tuning a number."
                % field)
    if state == "unresolved-variables":
        return ("pass the variables with --variables so the slices can be "
                "resolved. A slice you cannot evaluate is a slice you cannot "
                "budget for.")
    if state == "no-connections":
        return "nothing. There is nothing here to multiply."
    return "nothing on the node count."


def reported_node_count(body):
    """The node count the server computed, if the document asked for it. Pure."""
    if not isinstance(body, dict):
        return None
    data = body.get("data")
    if not isinstance(data, dict):
        return None
    rl = data.get("rateLimit")
    if not isinstance(rl, dict):
        return None
    try:
        return int(rl.get("nodeCount"))
    except (TypeError, ValueError):
        return None


def rejected_for_nodes(body):
    """Whether the server refused this document for its size. Pure."""
    if not isinstance(body, dict):
        return False
    for err in body.get("errors") or []:
        if isinstance(err, dict) and err.get("type") == "MAX_NODE_LIMIT_EXCEEDED":
            return True
    return False


def point_cost(confirm):
    """Points this run will spend. Pure. Zero unless --confirm is passed."""
    return 1 if confirm else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", help="read the query document from this file")
    ap.add_argument("--query", help="the query document itself")
    ap.add_argument("--variables", help="JSON object supplying the query's variables")
    ap.add_argument("--confirm", action="store_true",
                    help="spend one point sending the document so the server can "
                         "agree or disagree")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            document = fh.read()
    else:
        document = args.query or DEMO_QUERY

    try:
        variables = json.loads(args.variables) if args.variables else {}
    except ValueError:
        log.error("--variables must be a JSON object")
        return 2

    why_not = refusal(document)
    if why_not:
        log.error("refusing to analyse and send: %s", why_not)
        return 2

    if args.confirm:
        log.info("point cost: %d point(s) against the 5,000/hour GraphQL budget",
                 point_cost(True))
    else:
        log.info("point cost: %d point(s). The node count is computed from the "
                 "query text and nothing is sent.", point_cost(False))

    conns = connections(document, variables)
    total = node_count(document, variables)
    log.info("node count: %s against a limit of %s", commas(total), commas(NODE_LIMIT))
    for c in conns:
        log.info("  %-16s %s=%-6s depth %-3d ancestors x%-8s %s nodes",
                 c["field"], c["arg"],
                 c["requested"] if c["requested"] is not None else "?",
                 c["depth"], commas(c["ancestors"]),
                 commas(c["nodes"]) if c["nodes"] is not None else "?")

    state, detail = verdict(document, variables)
    log.info("%s: %s", state, detail)
    for c in caveats(document, variables):
        log.info("caveat: %s", c)
    field, current, suggested = reshape(document, variables)
    log.info("repair: %s", repair(state, field, current, suggested))

    server = {}
    if args.confirm:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            log.error("--confirm needs GITHUB_TOKEN (a read-only token is enough)")
            return 2
        import requests
        session = requests.Session()
        session.headers.update({
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": UA,
        })
        # A GraphQL query is a read; POST is only how the document reaches the
        # endpoint, which is why the verb sits here beside the URL rather than
        # in a constant where it could be mistaken for a write path.
        resp = session.post(API + "/graphql",
                            json={"query": document, "variables": variables},
                            timeout=30)
        try:
            body = resp.json()
        except ValueError:
            body = None
        server = {"rejected": rejected_for_nodes(body),
                  "reported_node_count": reported_node_count(body)}
        if server["rejected"]:
            log.info("the server rejected the document for its node count, which "
                     "confirms the arithmetic above")
        elif server["reported_node_count"] is not None:
            log.info("the server computed %s node(s); this check computed %s",
                     commas(server["reported_node_count"]), commas(total))
        else:
            log.info("the server accepted the document and reported no node "
                     "count. Add rateLimit { nodeCount } to compare directly.")

    print(json.dumps({
        "points_spent": point_cost(args.confirm),
        "node_count": total,
        "node_limit": NODE_LIMIT,
        "over_limit": exceeds(total),
        "connections": conns,
        "caveats": caveats(document, variables),
        "deepest": deepest(document, variables),
        "suggested": {"field": field, "current": current, "first": suggested},
        "server": server,
        "state": state,
        "detail": detail,
    }, indent=2, default=str))
    return 1 if state in ("over-node-limit", "near-node-limit") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-nodes.mjs",
"js": '''/**
 * Compute a GraphQL query's node count from its text, before sending it.
 *
 * Read only, and by default not even that: the node count is derived from the
 * query document, so the standard run makes no request, needs no token and
 * spends no points. The optional confirm step sends the document once and
 * costs one point.
 *
 * Queries only. GitHub's GraphQL endpoint takes a document in the request body,
 * so a read is carried by POST there just as a write would be; that is
 * transport, not intent. Any document containing a mutation or a subscription
 * is refused before a socket opens.
 *
 * Environment:
 *   GITHUB_QUERY      the query document itself
 *   GITHUB_VARIABLES  JSON object supplying the query's variables
 *   GITHUB_CONFIRM    set to spend one point asking the server to agree
 *   GITHUB_TOKEN      only needed when confirming
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-nodes/1.0';

/** The documented ceiling on one query. */
export const NODE_LIMIT = 500000;

/** Above this fraction of the cap, say so. */
export const NEAR = 0.8;

const DEMO_QUERY = `query {
  organization(login: "acme") {
    repositories(first: 100) {
      nodes {
        pullRequests(first: 100) {
          nodes {
            comments(first: 100) { nodes { id } }
          }
        }
      }
    }
  }
}`;

const PAGING = /\\b(first|last)\\s*:\\s*(\\$?[A-Za-z0-9_]+)/;
const SPREAD = /\\.\\.\\.\\s*([A-Za-z_][A-Za-z0-9_]*)/g;

/** Remove GraphQL comments and string literals from a document. Pure. */
export function stripNoise(document) {
  const src = String(document ?? '');
  const out = [];
  let i = 0;
  while (i < src.length) {
    const ch = src[i];
    if (ch === '#') {
      while (i < src.length && src[i] !== '\\n') i += 1;
      continue;
    }
    if (src.startsWith('"""', i)) {
      const j = src.indexOf('"""', i + 3);
      i = j < 0 ? src.length : j + 3;
      out.push(' ');
      continue;
    }
    if (ch === '"') {
      i += 1;
      while (i < src.length && src[i] !== '"') i += src[i] === '\\\\' ? 2 : 1;
      i += 1;
      out.push(' ');
      continue;
    }
    out.push(ch);
    i += 1;
  }
  return out.join('');
}

/** The top-level operations in a document, in order. Pure. */
export function operations(document) {
  const src = `${stripNoise(document)} `;
  const ops = [];
  let depth = 0;
  let word = '';
  let declared = null;
  for (const ch of src) {
    if (/[A-Za-z0-9_]/.test(ch)) { word += ch; continue; }
    if (word) {
      if (depth === 0 && ['query', 'mutation', 'subscription', 'fragment'].includes(word)) {
        declared = word;
      }
      word = '';
    }
    if (ch === '{') {
      if (depth === 0) { ops.push(declared || 'query'); declared = null; }
      depth += 1;
    } else if (ch === '}') {
      depth = Math.max(0, depth - 1);
    }
  }
  return ops;
}

/** Why this document will not be sent, or null if it is a read. Pure. */
export function refusal(document) {
  const ops = operations(document);
  if (ops.length === 0) return 'the document contains no operation to send.';
  for (const kind of ['mutation', 'subscription']) {
    if (ops.includes(kind)) {
      return `the document contains a ${kind}. This script sends queries only: `
        + 'a query is a read, and the section it belongs to promises its '
        + 'scripts never write.';
    }
  }
  return null;
}

/** Group a count in thousands so it can be read at a glance. Pure. */
export function commas(n) {
  if (n === null || n === undefined || n === '') return String(n);
  const v = Number(n);
  if (!Number.isFinite(v)) return String(n);
  return Math.trunc(v).toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
}

function paging(field, args, variables) {
  const m = PAGING.exec(args || '');
  if (!m) return null;
  const [, arg, raw] = m;
  const variable = raw.startsWith('$') ? raw.slice(1) : null;
  const value = variable ? (variables || {})[variable] : raw;
  const n = Number(value);
  return {
    field: field || '?',
    arg,
    variable,
    requested: Number.isInteger(n) ? n : null,
  };
}

/** Every sliced connection in a document, with its node contribution. Pure. */
export function connections(document, variables = null) {
  const src = stripNoise(document);
  const out = [];
  const stack = [];
  let pending = null;
  let field = null;
  let i = 0;
  while (i < src.length) {
    const ch = src[i];
    if (ch === '(') {
      const j = src.indexOf(')', i);
      const args = j < 0 ? src.slice(i + 1) : src.slice(i + 1, j);
      const found = paging(field, args, variables);
      // Only overwrite a pending slice when this argument group carries one, so
      // a directive such as @include(if: $x) cannot erase the first: value that
      // came immediately before it.
      if (found !== null) pending = found;
      i = j < 0 ? src.length : j + 1;
      continue;
    }
    if (ch === '{') {
      if (pending !== null) {
        const ancestors = stack.reduce((a, b) => a * b, 1);
        const rec = { ...pending, depth: stack.length + 1, ancestors };
        rec.nodes = rec.requested === null ? null : ancestors * rec.requested;
        out.push(rec);
        stack.push(rec.requested || 1);
      } else {
        stack.push(1);
      }
      pending = null;
      field = null;
      i += 1;
      continue;
    }
    if (ch === '}') {
      stack.pop();
      pending = null;
      field = null;
      i += 1;
      continue;
    }
    if (/[A-Za-z_]/.test(ch)) {
      let j = i;
      while (j < src.length && /[A-Za-z0-9_]/.test(src[j])) j += 1;
      field = src.slice(i, j);
      i = j;
      continue;
    }
    i += 1;
  }
  return out;
}

/** The node total the server will compute for this document. Pure. */
export function nodeCount(document, variables = null) {
  return connections(document, variables)
    .filter((c) => c.nodes !== null)
    .reduce((sum, c) => sum + c.nodes, 0);
}

/** Connections whose slice is a variable nobody supplied. Pure. */
export function unresolved(document, variables = null) {
  return connections(document, variables)
    .filter((c) => c.requested === null)
    .map((c) => c.field);
}

/** Named fragment spreads, which hide part of the selection set. Pure. */
export function fragmentSpreads(document) {
  const src = stripNoise(document);
  const found = new Set();
  for (const m of src.matchAll(SPREAD)) {
    if (m[1] !== 'on') found.add(m[1]);
  }
  return [...found].sort();
}

/** Everything that makes the computed total less than certain. Pure. */
export function caveats(document, variables = null) {
  const out = [];
  const missing = [...new Set(unresolved(document, variables))].sort();
  if (missing.length > 0) {
    out.push(`the slice on ${missing.join(', ')} is a variable this run has no `
      + 'value for, so those connections are not in the total. Pass GITHUB_VARIABLES.');
  }
  const spreads = fragmentSpreads(document);
  if (spreads.length > 0) {
    out.push(`the document spreads the fragment(s) ${spreads.join(', ')}, whose `
      + 'selection set this text-level check does not expand, so the total is a '
      + 'lower bound.');
  }
  return out;
}

/** The connection carrying the largest multiplier. Pure. null if there is none. */
export function deepest(document, variables = null) {
  const resolved = connections(document, variables).filter((c) => c.nodes !== null);
  if (resolved.length === 0) return null;
  return resolved.reduce((best, c) => {
    if (c.depth > best.depth) return c;
    if (c.depth === best.depth && c.nodes > best.nodes) return c;
    return best;
  }, resolved[0]);
}

/** The largest slice the deepest connection could take. Pure. */
export function reshape(document, variables = null, limit = NODE_LIMIT) {
  const d = deepest(document, variables);
  if (d === null) return [null, null, null];
  const total = nodeCount(document, variables);
  const room = limit - (total - d.nodes);
  if (d.ancestors <= 0) return [d.field, d.requested, null];
  const k = Math.floor(room / d.ancestors);
  if (k < 1) return [d.field, d.requested, null];
  return [d.field, d.requested, Math.min(k, 100)];
}

/** Whether this node total is over the cap. Pure. */
export function exceeds(count, limit = NODE_LIMIT) {
  const n = Number(count);
  return Number.isFinite(n) && n > Number(limit);
}

/** Classify one document. Pure. Returns [state, detail]. */
export function verdict(document, variables = null, limit = NODE_LIMIT) {
  const conns = connections(document, variables);
  if (conns.length === 0) {
    return ['no-connections', 'this document slices no connections, so it has '
      + 'no node count worth speaking of.'];
  }
  if (conns.some((c) => c.nodes === null)) {
    return ['unresolved-variables', 'at least one slice is a variable with no '
      + 'value supplied, so the node count cannot be computed from the text alone.'];
  }
  const total = nodeCount(document, variables);
  const pct = Math.round((100 * total) / limit);
  if (exceeds(total, limit)) {
    return ['over-node-limit', `${commas(total)} nodes is ${pct}% of the `
      + `${commas(limit)} cap, so this query is rejected before it runs whatever `
      + 'the organisation contains.'];
  }
  if (total > limit * NEAR) {
    return ['near-node-limit', `${commas(total)} nodes is ${pct}% of the cap, `
      + 'which leaves no room for another level.'];
  }
  return ['within-node-limit', `${commas(total)} nodes is ${pct}% of the cap.`];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, field = null, current = null, suggested = null) {
  if (state === 'over-node-limit' || state === 'near-node-limit') {
    if (suggested !== null && suggested !== undefined) {
      return `lower first on ${field} from ${current} to ${suggested} and `
        + 'paginate it separately with pageInfo { hasNextPage endCursor }.';
    }
    return `even a slice of one on ${field} leaves this query over the cap, so `
      + 'split it into separate queries rather than tuning a number.';
  }
  if (state === 'unresolved-variables') {
    return 'pass the variables with GITHUB_VARIABLES so the slices can be '
      + 'resolved. A slice you cannot evaluate is a slice you cannot budget for.';
  }
  if (state === 'no-connections') return 'nothing. There is nothing here to multiply.';
  return 'nothing on the node count.';
}

/** The node count the server computed, if the document asked for it. Pure. */
export function reportedNodeCount(body) {
  if (!body || typeof body !== 'object') return null;
  const data = body.data;
  if (!data || typeof data !== 'object') return null;
  const rl = data.rateLimit;
  if (!rl || typeof rl !== 'object') return null;
  const n = Number(rl.nodeCount);
  return Number.isFinite(n) ? Math.trunc(n) : null;
}

/** Whether the server refused this document for its size. Pure. */
export function rejectedForNodes(body) {
  if (!body || typeof body !== 'object' || !Array.isArray(body.errors)) return false;
  return body.errors.some(
    (e) => e && typeof e === 'object' && e.type === 'MAX_NODE_LIMIT_EXCEEDED',
  );
}

/** Points this run will spend. Pure. Zero unless the confirm step is asked for. */
export function pointCost(confirm) {
  return confirm ? 1 : 0;
}

async function main() {
  const document = process.env.GITHUB_QUERY || DEMO_QUERY;
  let variables = {};
  if (process.env.GITHUB_VARIABLES) {
    try { variables = JSON.parse(process.env.GITHUB_VARIABLES); } catch {
      console.error('GITHUB_VARIABLES must be a JSON object');
      process.exitCode = 2;
      return;
    }
  }
  const confirm = Boolean(process.env.GITHUB_CONFIRM);

  const whyNot = refusal(document);
  if (whyNot) {
    console.error(`refusing to analyse and send: ${whyNot}`);
    process.exitCode = 2;
    return;
  }

  if (confirm) {
    console.log(`point cost: ${pointCost(true)} point(s) against the 5,000/hour GraphQL budget`);
  } else {
    console.log(`point cost: ${pointCost(false)} point(s). The node count is `
      + 'computed from the query text and nothing is sent.');
  }

  const conns = connections(document, variables);
  const total = nodeCount(document, variables);
  console.log(`node count: ${commas(total)} against a limit of ${commas(NODE_LIMIT)}`);
  for (const c of conns) {
    console.log(`  ${c.field.padEnd(16)} ${c.arg}=${String(c.requested ?? '?').padEnd(6)} `
      + `depth ${String(c.depth).padEnd(3)} ancestors x${commas(c.ancestors).padEnd(8)} `
      + `${c.nodes === null ? '?' : commas(c.nodes)} nodes`);
  }

  const [state, detail] = verdict(document, variables);
  console.log(`${state}: ${detail}`);
  for (const c of caveats(document, variables)) console.log(`caveat: ${c}`);
  const [field, current, suggested] = reshape(document, variables);
  console.log(`repair: ${repair(state, field, current, suggested)}`);

  let server = {};
  if (confirm) {
    const token = process.env.GITHUB_TOKEN;
    if (!token) {
      console.error('confirming needs GITHUB_TOKEN (read-only is enough)');
      process.exitCode = 2;
      return;
    }
    const res = await fetch(`${API}/graphql`, {
      // A GraphQL query is a read. POST is only how the document reaches the
      // endpoint, and refusal() has already rejected anything that is not.
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json',
        'User-Agent': UA,
      },
      body: JSON.stringify({ query: document, variables }),
    });
    let body = null;
    try { body = await res.json(); } catch { body = null; }
    server = { rejected: rejectedForNodes(body), reported_node_count: reportedNodeCount(body) };
    if (server.rejected) {
      console.log('the server rejected the document for its node count, which '
        + 'confirms the arithmetic above');
    } else if (server.reported_node_count !== null) {
      console.log(`the server computed ${commas(server.reported_node_count)} node(s); `
        + `this check computed ${commas(total)}`);
    } else {
      console.log('the server accepted the document and reported no node count. '
        + 'Add rateLimit { nodeCount } to compare directly.');
    }
  }

  console.log(JSON.stringify({
    points_spent: pointCost(confirm),
    node_count: total,
    node_limit: NODE_LIMIT,
    over_limit: exceeds(total),
    connections: conns,
    caveats: caveats(document, variables),
    deepest: deepest(document, variables),
    suggested: { field, current, first: suggested },
    server,
    state,
    detail,
  }, null, 2));
  process.exitCode = ['over-node-limit', 'near-node-limit'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The arithmetic is the note, so the canonical three-level query is asserted at exactly 1,010,100 nodes and the suggested repair at exactly 48, which is the largest slice the deepest connection can take and still fit. Around that: the multiplier chain checked at each level, a slice supplied as a variable both with and without its value, a directive that must not erase the first: that precedes it, a fragment spread that makes the total a lower bound rather than an answer, the word first appearing inside a string literal, and the boundary cases at and just over the cap. Nothing in this suite needs a network, which is the same reason the script does not.",
"test_py_file": "test_github_graphql_nodes.py",
"test_py": '''from github_graphql_nodes import (
    NODE_LIMIT, caveats, commas, connections, deepest, exceeds,
    fragment_spreads, node_count, operations, point_cost, refusal, repair,
    reported_node_count, rejected_for_nodes, reshape, unresolved, verdict,
)

THREE_LEVELS = """query {
  organization(login: "acme") {
    repositories(first: 100) {
      nodes {
        pullRequests(first: 100) {
          nodes {
            comments(first: 100) { nodes { id } }
          }
        }
      }
    }
  }
}"""

SMALL = """query {
  organization(login: "acme") {
    repositories(first: 100) {
      nodes { pullRequests(first: 10) { nodes { number } } }
    }
  }
}"""


def test_the_canonical_query_is_the_documented_million():
    assert node_count(THREE_LEVELS) == 1_010_100
    assert exceeds(node_count(THREE_LEVELS))
    assert NODE_LIMIT == 500_000


def test_the_multiplier_chain_is_what_makes_it_large():
    conns = connections(THREE_LEVELS)
    by_field = {c["field"]: c for c in conns}
    assert by_field["repositories"]["ancestors"] == 1
    assert by_field["repositories"]["nodes"] == 100
    assert by_field["pullRequests"]["ancestors"] == 100
    assert by_field["pullRequests"]["nodes"] == 10_000
    assert by_field["comments"]["ancestors"] == 10_000
    assert by_field["comments"]["nodes"] == 1_000_000


def test_the_deepest_connection_carries_almost_all_of_it():
    d = deepest(THREE_LEVELS)
    assert d["field"] == "comments"
    assert d["nodes"] == 1_000_000


def test_the_repair_is_a_number_and_the_number_fits():
    field, current, suggested = reshape(THREE_LEVELS)
    assert field == "comments"
    assert current == 100
    assert suggested == 48
    # The point of the suggestion is that taking it works.
    fixed = THREE_LEVELS.replace("comments(first: 100)", "comments(first: 48)")
    assert node_count(fixed) == 490_100
    assert not exceeds(node_count(fixed))


def test_a_query_that_cannot_be_rescued_by_one_number_says_so():
    huge = ("query { a(first: 100) { nodes { b(first: 100) { nodes { "
            "c(first: 100) { nodes { d(first: 100) { nodes { id } } } } } } } } }")
    assert exceeds(node_count(huge))
    field, _current, suggested = reshape(huge)
    assert suggested is None
    assert "split it into separate queries" in repair("over-node-limit", field, 100, None)


def test_a_small_query_is_not_flagged():
    assert node_count(SMALL) == 1_100
    state, detail = verdict(SMALL)
    assert state == "within-node-limit"
    assert "0%" in detail or "%" in detail


def test_the_verdict_names_the_three_bands():
    assert verdict(THREE_LEVELS)[0] == "over-node-limit"
    near = "query { a(first: 100) { nodes { b(first: 4500) { nodes { id } } } } }"
    assert node_count(near) == 450_100
    assert verdict(near)[0] == "near-node-limit"
    assert verdict(SMALL)[0] == "within-node-limit"
    assert verdict("query { viewer { login } }")[0] == "no-connections"


def test_a_slice_supplied_as_a_variable_is_resolved_or_reported():
    doc = "query($n: Int!) { a(first: $n) { nodes { id } } }"
    assert node_count(doc, {"n": 50}) == 50
    assert verdict(doc, {"n": 50})[0] == "within-node-limit"
    assert unresolved(doc) == ["a"]
    assert verdict(doc)[0] == "unresolved-variables"
    assert "Pass --variables" in caveats(doc)[0]


def test_a_directive_does_not_erase_the_slice_before_it():
    doc = ("query($show: Boolean!) { repositories(first: 100) @include(if: $show) "
           "{ nodes { id } } }")
    assert node_count(doc) == 100


def test_a_fragment_spread_makes_the_total_a_lower_bound():
    doc = ("query { repositories(first: 100) { nodes { ...RepoBits } } } "
           "fragment RepoBits on Repository { pullRequests(first: 100) { nodes { id } } }")
    assert fragment_spreads(doc) == ["RepoBits"]
    assert any("lower bound" in c for c in caveats(doc))


def test_an_inline_fragment_is_not_mistaken_for_a_spread():
    doc = "query { search(query: \\"x\\", type: ISSUE, first: 10) { nodes { ... on Issue { id } } } }"
    assert fragment_spreads(doc) == []
    assert node_count(doc) == 10


def test_the_word_first_inside_a_string_is_not_a_slice():
    doc = 'query { search(query: "first: 100", type: ISSUE, first: 5) { nodes { id } } }'
    assert node_count(doc) == 5


def test_a_comment_is_not_read_as_part_of_the_query():
    doc = "# repositories(first: 100)\\nquery { a(first: 7) { nodes { id } } }"
    assert node_count(doc) == 7


def test_the_server_can_be_asked_to_agree_but_does_not_have_to_be():
    assert rejected_for_nodes({"errors": [{"type": "MAX_NODE_LIMIT_EXCEEDED"}]})
    assert not rejected_for_nodes({"errors": [{"type": "RATE_LIMITED"}]})
    assert reported_node_count({"data": {"rateLimit": {"nodeCount": 1100}}}) == 1100
    assert reported_node_count({"data": {"viewer": {"login": "ada"}}}) is None


def test_counts_are_printed_in_something_readable():
    assert commas(1_010_100) == "1,010,100"
    assert commas(100) == "100"
    assert commas(None) == "None"


def test_the_default_run_spends_nothing():
    assert point_cost(False) == 0
    assert point_cost(True) == 1


def test_the_script_refuses_to_analyse_and_send_a_mutation():
    assert operations(THREE_LEVELS) == ["query"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal(THREE_LEVELS) is None
''',
"test_js_file": "github-graphql-nodes.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  NODE_LIMIT, caveats, commas, connections, deepest, exceeds, fragmentSpreads,
  nodeCount, operations, pointCost, refusal, rejectedForNodes, repair,
  reportedNodeCount, reshape, unresolved, verdict,
} from './github-graphql-nodes.mjs';

const THREE_LEVELS = `query {
  organization(login: "acme") {
    repositories(first: 100) {
      nodes {
        pullRequests(first: 100) {
          nodes {
            comments(first: 100) { nodes { id } }
          }
        }
      }
    }
  }
}`;

const SMALL = `query {
  organization(login: "acme") {
    repositories(first: 100) {
      nodes { pullRequests(first: 10) { nodes { number } } }
    }
  }
}`;

test('the canonical query is the documented million', () => {
  assert.equal(nodeCount(THREE_LEVELS), 1010100);
  assert.ok(exceeds(nodeCount(THREE_LEVELS)));
  assert.equal(NODE_LIMIT, 500000);
});

test('the multiplier chain is what makes it large', () => {
  const byField = Object.fromEntries(connections(THREE_LEVELS).map((c) => [c.field, c]));
  assert.equal(byField.repositories.ancestors, 1);
  assert.equal(byField.repositories.nodes, 100);
  assert.equal(byField.pullRequests.ancestors, 100);
  assert.equal(byField.pullRequests.nodes, 10000);
  assert.equal(byField.comments.ancestors, 10000);
  assert.equal(byField.comments.nodes, 1000000);
});

test('the deepest connection carries almost all of it', () => {
  const d = deepest(THREE_LEVELS);
  assert.equal(d.field, 'comments');
  assert.equal(d.nodes, 1000000);
});

test('the repair is a number and the number fits', () => {
  const [field, current, suggested] = reshape(THREE_LEVELS);
  assert.equal(field, 'comments');
  assert.equal(current, 100);
  assert.equal(suggested, 48);
  const fixed = THREE_LEVELS.replace('comments(first: 100)', 'comments(first: 48)');
  assert.equal(nodeCount(fixed), 490100);
  assert.ok(!exceeds(nodeCount(fixed)));
});

test('a query that cannot be rescued by one number says so', () => {
  const huge = 'query { a(first: 100) { nodes { b(first: 100) { nodes { '
    + 'c(first: 100) { nodes { d(first: 100) { nodes { id } } } } } } } } }';
  assert.ok(exceeds(nodeCount(huge)));
  const [field, , suggested] = reshape(huge);
  assert.equal(suggested, null);
  assert.match(repair('over-node-limit', field, 100, null), /split it into separate queries/);
});

test('a small query is not flagged', () => {
  assert.equal(nodeCount(SMALL), 1100);
  assert.equal(verdict(SMALL)[0], 'within-node-limit');
});

test('the verdict names the three bands', () => {
  assert.equal(verdict(THREE_LEVELS)[0], 'over-node-limit');
  const near = 'query { a(first: 100) { nodes { b(first: 4500) { nodes { id } } } } }';
  assert.equal(nodeCount(near), 450100);
  assert.equal(verdict(near)[0], 'near-node-limit');
  assert.equal(verdict(SMALL)[0], 'within-node-limit');
  assert.equal(verdict('query { viewer { login } }')[0], 'no-connections');
});

test('a slice supplied as a variable is resolved or reported', () => {
  const doc = 'query($n: Int!) { a(first: $n) { nodes { id } } }';
  assert.equal(nodeCount(doc, { n: 50 }), 50);
  assert.equal(verdict(doc, { n: 50 })[0], 'within-node-limit');
  assert.deepEqual(unresolved(doc), ['a']);
  assert.equal(verdict(doc)[0], 'unresolved-variables');
  assert.match(caveats(doc)[0], /GITHUB_VARIABLES/);
});

test('a directive does not erase the slice before it', () => {
  const doc = 'query($show: Boolean!) { repositories(first: 100) @include(if: $show) '
    + '{ nodes { id } } }';
  assert.equal(nodeCount(doc), 100);
});

test('a fragment spread makes the total a lower bound', () => {
  const doc = 'query { repositories(first: 100) { nodes { ...RepoBits } } } '
    + 'fragment RepoBits on Repository { pullRequests(first: 100) { nodes { id } } }';
  assert.deepEqual(fragmentSpreads(doc), ['RepoBits']);
  assert.ok(caveats(doc).some((c) => c.includes('lower bound')));
});

test('an inline fragment is not mistaken for a spread', () => {
  const doc = 'query { search(query: "x", type: ISSUE, first: 10) { nodes { ... on Issue { id } } } }';
  assert.deepEqual(fragmentSpreads(doc), []);
  assert.equal(nodeCount(doc), 10);
});

test('the word first inside a string is not a slice', () => {
  const doc = 'query { search(query: "first: 100", type: ISSUE, first: 5) { nodes { id } } }';
  assert.equal(nodeCount(doc), 5);
});

test('a comment is not read as part of the query', () => {
  const doc = '# repositories(first: 100)\\nquery { a(first: 7) { nodes { id } } }';
  assert.equal(nodeCount(doc), 7);
});

test('the server can be asked to agree but does not have to be', () => {
  assert.ok(rejectedForNodes({ errors: [{ type: 'MAX_NODE_LIMIT_EXCEEDED' }] }));
  assert.ok(!rejectedForNodes({ errors: [{ type: 'RATE_LIMITED' }] }));
  assert.equal(reportedNodeCount({ data: { rateLimit: { nodeCount: 1100 } } }), 1100);
  assert.equal(reportedNodeCount({ data: { viewer: { login: 'ada' } } }), null);
});

test('counts are printed in something readable', () => {
  assert.equal(commas(1010100), '1,010,100');
  assert.equal(commas(100), '100');
  assert.equal(commas(null), 'null');
});

test('the default run spends nothing', () => {
  assert.equal(pointCost(false), 0);
  assert.equal(pointCost(true), 1);
});

test('the script refuses to analyse and send a mutation', () => {
  assert.deepEqual(operations(THREE_LEVELS), ['query']);
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.equal(refusal(THREE_LEVELS), null);
});
''',
"faq": [
 ("Why does the query fail against a tiny organisation?",
  "Because the node count is computed from the numbers in the query, not from the rows behind them. A request for 100 repositories with 100 pull requests each with 100 comments each is 1,010,100 nodes whether the organisation has four repositories or four thousand, and the check happens before anything is fetched. This is also why narrowing a date range or excluding archived repositories does not help: those change what exists, and the limit does not care what exists."),
 ("Is this the same thing as running out of points?",
  "No, and confusing them wastes real time. Points are an hourly allowance and running out is temporary: the same query succeeds an hour later. A node-limit rejection is permanent for that query text, because the query is what is too large. The error types are different too, MAX_NODE_LIMIT_EXCEEDED against RATE_LIMITED, which is exactly why a client should branch on the type rather than on the message: one of these deserves a wait and a retry and the other will burn the point budget in a loop that can never succeed."),
 ("Which first should I lower?",
  "The deepest one, because it is multiplied by everything above it and therefore contributes almost the whole total. In the three-level example the comments connection is 1,000,000 of the 1,010,100 nodes; lowering it from 100 to 48 brings the query in, while halving the outermost value only gets you to about 505,000. The script prints the per-connection breakdown so this is a reading rather than a guess, and it solves for the largest value the deepest connection can take."),
 ("Do I need a token to run this?",
  "No, and that is deliberate. The node count is a function of the query text, so the check parses, multiplies and prints without a credential, without a request and without spending a point. That makes it something you can run in CI over a directory of query files, which is where it belongs: the failure it prevents is a query going to production with an arithmetic problem nobody could see by reading it. The --confirm flag will ask the server to agree, costs one point and says so first."),
 ("What can a text-level check not see?",
  "Two things, and it reports both rather than hiding them. A first supplied as a variable cannot be evaluated without the variables, so the script asks for them instead of assuming a value. And a named fragment spread hides part of the selection set, so when one is present the computed total is a lower bound rather than the answer; inline fragments are fine, since their selection set is right there in the document. Beyond that the arithmetic is the same arithmetic the server does."),
],
"related": [
 ("/github/graphql-rate-limited/", "GraphQL points run out in their own bucket"),
 ("/github/graphql-200-with-errors/", "A GraphQL 200 that carries an errors array"),
 ("/github/per-page-over-100-clamped/", "per_page above 100 is clamped, not rejected"),
],
"citations": [CITE_GQL_RESOURCE, CITE_GQL_RATE, CITE_PAGINATION_GQL, CITE_GQL_MIGRATE],
},

]
