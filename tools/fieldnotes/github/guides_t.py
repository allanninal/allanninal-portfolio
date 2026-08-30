#!/usr/bin/env python3
"""/github/ field notes, batch T — the writing.

Four more GraphQL notes, and the danger with a second GraphQL batch is that it
becomes a set of footnotes to the first. Each of these owns something the first
batch does not touch, and three of them are not about an error response at all.

The first owns the price of writing. GitHub weighs a GraphQL document that
contains a mutation at five points against the per-minute secondary limit and a
document that does not at one, so a write loop reaches the wall at a fifth of the
rate a read loop tolerates. The section already publishes the hourly point budget
and the REST per-minute limits, and this note restates neither: it is about the
weight, the ratio, and the differential diagnosis that separates a secondary
throttle from an exhausted budget. The script that does the arithmetic is the one
script in the section that reads mutation documents, and it never sends one. It
parses them, prices them, refuses them, and sends a single read of its own.

The second owns a disappointment. People move a search from REST to GraphQL
specifically to escape the thousand-result ceiling, and the ceiling is a property
of the search index rather than of the protocol, so it comes with them. The
published REST note owns the 422 that says so out loud. This one owns the fact
that GraphQL does not say it out loud: pagination simply stops, hasNextPage turns
false with issueCount still reporting eighteen thousand, and a walk that trusts
hasNextPage terminates cleanly on an answer that is missing ninety-four per cent
of the matches. Silent where the other is loud, and with one escape the other
does not have.

The third is not an error at all. GraphQL's id is an opaque global node id and
REST's id is an integer, each is called "the id" in its own response, and a store
that takes whichever one arrived ends up with two key spaces for one entity and a
join that returns nothing. The crosswalk is exact in both directions and the
script proves it on a live object. There is a third integer hiding in there too,
because an issue's number is not its databaseId and both fit the same column.

The fourth owns one 403 message. Fine-grained personal access tokens carry
per-resource permissions rather than scopes, and the response that refuses one
names no permission the token holds because there is no header that reports them.
That absence is the note: the classic-scope note diffs two headers, and here only
one of the two exists, so the other side has to be measured behaviourally with
cheap reads. It is also the one refusal in the section that reaches you through
GraphQL as an errors entry with no header attached at all.

Queries only, never mutations. The GraphQL endpoint takes its document in the
request body, so a read travels by POST there exactly as a write would, and every
script in this batch parses the document and refuses to open a socket if any
top-level operation is a mutation or a subscription. Every one of them prints
what it will spend before it spends it.
"""

CITE_GQL_RESOURCE = ("Resource limitations — GitHub GraphQL API",
                     "https://docs.github.com/en/graphql/overview/resource-limitations")
CITE_GQL_RATE = ("Rate limits and node limits for the GraphQL API — GitHub Docs",
                 "https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api")
CITE_REST_RATE_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                         "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_REST_RATE_LIMIT = ("Rate limit — GitHub REST API",
                        "https://docs.github.com/en/rest/rate-limit/rate-limit")
CITE_GQL_QUERIES = ("Queries — GitHub GraphQL API reference",
                    "https://docs.github.com/en/graphql/reference/queries")
CITE_GQL_SEARCH_SO = ("GitHub GraphQL search with filtering — Stack Overflow",
                      "https://stackoverflow.com/questions/49344444/github-graphql-search-with-filtering")
CITE_REST_SEARCH = ("Search — GitHub REST API",
                    "https://docs.github.com/en/rest/search/search")
CITE_PAGINATION_GQL = ("Using pagination in the GraphQL API — GitHub Docs",
                       "https://docs.github.com/en/graphql/guides/using-pagination-in-the-graphql-api")
CITE_NODE_IDS = ("Using global node IDs — GitHub Docs",
                 "https://docs.github.com/en/graphql/guides/using-global-node-ids")
CITE_GQL_INTERFACES = ("Interfaces — GitHub GraphQL API reference",
                       "https://docs.github.com/en/graphql/reference/interfaces")
CITE_GQL_MIGRATE = ("Migrating from REST to GraphQL — GitHub Docs",
                    "https://docs.github.com/en/graphql/guides/migrating-from-rest-to-graphql")
CITE_REST_ISSUES = ("Issues — GitHub REST API",
                    "https://docs.github.com/en/rest/issues/issues")
CITE_PAT_SO = ("Resource not accessible by personal access token — Stack Overflow",
               "https://stackoverflow.com/questions/76333420/error-message-resource-not-accessible-by-personal-access-token-when-trying-to")
CITE_FG_PERMS = ("Permissions required for fine-grained personal access tokens — GitHub Docs",
                 "https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens")
CITE_MANAGE_PATS = ("Managing your personal access tokens — GitHub Docs",
                    "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens")
CITE_APP_PERMS = ("Permissions required for GitHub Apps — GitHub Docs",
                  "https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps")

GUIDES = [
{
"slug": "graphql-mutation-secondary-cost",
"title": "A mutation costs five secondary points, a query costs one",
"description": "Secondary limits weigh a GraphQL document with a mutation at 5 points and one without at 1, against 2,000 a minute. Writes hit the wall sooner.",
"h1": "A mutation costs five secondary points, a query costs one",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github graphql secondary rate limit mutation",
             "you have exceeded a secondary rate limit graphql",
             "github graphql mutation points per minute",
             "github bulk mutation throttled 403",
             "graphql mutation cost secondary limit github"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The read job runs all day without complaint. The write job, which sends fewer requests, dies eleven minutes in with <code>403</code> and <code>You have exceeded a secondary rate limit</code>. Somebody checks <code>GET /rate_limit</code>, sees four thousand GraphQL points still sitting there unspent, and concludes GitHub is wrong. GitHub is not wrong. The bucket that emptied is not the one being looked at, and the reason the write job reached it first is that every document containing a mutation is priced at five times a read.",
"short_answer": """<p>The GraphQL endpoint has a per-minute secondary limit of 2,000 points that is entirely separate from the hourly point budget. Against that limit a request whose document contains a mutation counts as <strong>5 points</strong> and a request whose document does not counts as <strong>1</strong>. The arithmetic is the whole note: 2,000 read requests a minute, 400 mutation requests a minute, from one token.</p>
<p>So a write loop trips at roughly a fifth of the request rate a read loop survives, and it trips with the hourly budget almost untouched, which is what makes it look like a bug. Diagnose it by reading both facts at once: a 403 or 429 whose body says &ldquo;secondary rate limit&rdquo; while <code>resources.graphql.remaining</code> is still healthy is this limit and not the budget. Repair it by rate-limiting mutations against 2,000 points a minute rather than against a request count, serialising them instead of fanning them out, and honouring <code>retry-after</code> when it arrives.</p>""",
"problem": """<p>The shape that produces this is a migration or a backfill: label eleven thousand issues, close six thousand stale pull requests, add a project item for every repository in the org. Somebody writes it as a loop, runs it against a hundred rows to check the logic, and it is fine. They raise the concurrency because a hundred rows took a while and eleven thousand will take all afternoon, and now it dies.</p>
<p>Every instinct after that points at the wrong bucket. The error says rate limit, so the first thing anybody does is look at the rate limit, and the rate limit is fine — thousands of points remaining, a reset an hour away, nothing near zero. The natural conclusion is that the 403 is spurious, which leads to a retry loop, which sends the same requests faster, which extends the throttle. There is no header to check, because the secondary limit has no bucket in <code>GET /rate_limit</code> and never reports headroom. It is only ever visible after you have crossed it.</p>
<p>The second thing that misleads is the comparison with the read job. The read job sends more requests than the write job and does not get throttled, so request rate looks like it is not the problem. It is the problem; it is just being counted in a unit nobody converted to. Four hundred is a much smaller number than two thousand, and the only place that difference is written down is a sentence in the resource-limitations documentation about how mutations are weighed.</p>""",
"why": """<p><strong>Two buckets, two units, two time windows.</strong> The primary budget is 5,000 points an hour and is measurable before you spend it: <code>GET /rate_limit</code> reports <code>resources.graphql</code> for free, and that is <a href="/github/graphql-rate-limited/">its own note</a>. The secondary limit is 2,000 points a <em>minute</em>, is not reported anywhere, and exists to stop bursts rather than to meter volume. A job can be comfortably inside its hourly budget and outside the per-minute one on every single minute of its run.</p>
<p><strong>The weight is per request, not per mutation.</strong> A document that contains a mutation is priced at 5 points whether it contains one mutation or six. That cuts both ways: batching several mutations into one document is a real reduction in secondary cost, and it is the cheapest fix available, whereas splitting one document into six is a fivefold increase for the same work. A document with no mutation in it is 1 point regardless of how expensive it is against the hourly budget — the two prices are unrelated, and a query can be costly in one and trivial in the other.</p>
<p><strong>The REST secondary limits are different limits with different numbers.</strong> REST has its own per-minute ceilings — <a href="/github/secondary-limit-points-per-minute/">900 points a minute on a single endpoint, with a CPU-time cap beside it</a> — and a separate allowance for <a href="/github/secondary-limit-content-creation/">content-generating requests, around 80 a minute</a>. Those apply to the REST path. This one applies to <code>/graphql</code>, and a client that moved its writes to GraphQL to escape the REST content-creation limit landed on a different number rather than on none.</p>
<p><strong>Concurrency is a separate ceiling on top of this one.</strong> No more than 100 concurrent requests are allowed across the REST and GraphQL APIs together, and GitHub asks for at least one second between mutations that affect the same resource. Those rules are not expressed in points, so satisfying the point arithmetic does not satisfy them; fanning 400 mutations out across 200 workers respects the per-minute ceiling and violates the concurrency one.</p>
<p><strong>The differential diagnosis is two readings taken together.</strong> A GraphQL rate-limit failure that arrives as a 200 with <code>errors[0].type: "RATE_LIMITED"</code> is the hourly budget. A 403 or 429 with &ldquo;secondary rate limit&rdquo; in the body is this one. Reading <code>resources.graphql.remaining</code> at the same moment settles which: healthy remaining plus a secondary message is proof, and it is the reading that stops somebody rewriting the retry logic for a bug that is not there.</p>
<p><strong>This script prices mutations and never sends one.</strong> The section promises its scripts never write, and the note is about writes, so the arithmetic is done on the document text. The parser that decides whether a document is a read — the guard every GraphQL script in this section runs before it opens a socket — is the same parser that decides whether it is worth 5 points or 1. Refusing to send it and pricing it are the same question asked twice.</p>""",
"steps": [
 {"h": "Price your own documents without sending them",
  "body": """<p>Point the script at the query files your writer sends, or paste one in. It parses each document, lists its top-level operations, and prices it: 5 points if any operation is a mutation, 1 if not. Mutation documents are refused for sending in the same breath — they are read, priced and never transmitted, which is the only way a read-only tool can have an opinion about a write.</p>"""},
 {"h": "Convert the price into a rate you can put in a scheduler",
  "body": """<p>2,000 points a minute divided by the weight is the ceiling: 400 mutation requests a minute, 2,000 read requests a minute. The script prints the ceiling for each document and the minimum gap between calls it implies, so the number that goes into your limiter is a number rather than a guess. Then it prints how long your actual batch will take at that rate, because the honest version of this repair is usually &ldquo;this backfill takes forty minutes&rdquo;.</p>"""},
 {"h": "Compare that against the rate the job actually runs at",
  "body": """<p>Give the script the loop's real rate with <code>--rate</code> and it multiplies rate by weight to get points a minute, then says whether that number is over 2,000. A loop sending 500 mutation requests a minute is 2,500 points and will be throttled; the same loop sending queries is 500 points and will not. Seeing both lines next to each other is what explains why the read job never had this problem.</p>"""},
 {"h": "Separate a secondary throttle from an exhausted budget",
  "body": """<p>The script reads the GraphQL budget for free from <code>GET /rate_limit</code> and sends exactly one read query of its own to confirm the endpoint answers. If your logs carry a 403 or 429 that says &ldquo;secondary rate limit&rdquo; while that budget was healthy, feed it in and the script names the limit rather than leaving you to infer it. This is the step that prevents the retry loop.</p>"""},
 {"h": "Fix it in the writer, not in the retry handler",
  "body": """<p>Batch several mutations into one document where the API allows it, since the 5 points are charged per request. Serialise the writes rather than fanning them out, leave at least a second between mutations touching the same resource, and honour <code>retry-after</code> exactly rather than backing off by a guess. The whole audit costs one point, printed before it is spent, out of 5,000 an hour.</p>"""},
],
"verify": """<p>Once the writer is limited against points a minute instead of requests a minute, the same arithmetic reports headroom instead of a breach.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_mutation_budget.py \\
    --document label_issue.graphql --document fetch_issues.graphql --rate 500
# point cost: 1 point(s) against the 5000/hour GraphQL budget
# graphql budget: 4863/5000 remaining
# probe read query: HTTP 200, 1 point(s) spent
#
# label_issue.graphql: operations=mutation -> 5 point(s) per request
#   not sent: the document contains a mutation. This script prices documents,
#   it does not send them.
#   ceiling 400 request(s)/minute, minimum gap 0.150s on one worker
#   over-ceiling: 500 request(s)/minute of this document is 2500 point(s)/minute
#   against a limit of 2000.
#   11000 row(s) takes at least 28 minute(s) at the ceiling
#   repair: batch mutations into one document, serialise the loop, and cap it
#   at 400/minute or below.
#
# fetch_issues.graphql: operations=query -> 1 point(s) per request
#   ceiling 2000 request(s)/minute, minimum gap 0.030s on one worker
#   within-ceiling: 500 request(s)/minute is 500 point(s)/minute against a
#   limit of 2000.</code></pre>""",
"code_intro": "The parser is doing double duty here. It is the guard that keeps a mutation off the wire, and it is also the pricer, because the question &ldquo;does this document contain a mutation&rdquo; is exactly the question the secondary limit asks. Everything downstream of it is arithmetic over integers: weight, ceiling, points per minute at a given rate, minutes to finish a batch. The one live call is a single read query, and the budget beside it comes from a free REST call, so the script can prove which bucket is which without spending anything meaningful in either.",
"py_file": "github_graphql_mutation_budget.py",
"py": '''"""Price GraphQL documents against the per-minute secondary limit.

Read only, and queries only. GitHub's GraphQL endpoint takes its document in
the request body, so a read travels by POST there exactly as a write would;
that is a transport detail, not a licence to write. This script parses every
document it is given, refuses to open a socket for anything containing a
mutation or a subscription, and sends exactly one read query of its own.

The point of the note: against the secondary rate limit of 2,000 points per
minute, a GraphQL request whose document contains a mutation counts as 5
points and one that does not counts as 1. So a write loop reaches the limit at
roughly a fifth of the request rate a read loop survives, and it does so with
the separate hourly point budget almost untouched.

What this can and cannot see: secondary limits have no bucket. GET /rate_limit
reports the hourly budget only, and nothing anywhere reports how close you are
to the per-minute ceiling. So the ceiling is computed from the documented
weights and compared against a rate you supply, and a throttle you already
recorded is classified after the fact.

Environment:

    GITHUB_TOKEN    a token with read access to the GraphQL API
"""
import argparse
import json
import logging
import math
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_mutation_budget")

API = "https://api.github.com"
UA = "github-graphql-mutation-budget/1.0"

# The secondary limit on the GraphQL endpoint, and the two weights it applies.
# Documented, not measurable: no response reports headroom against this.
SECONDARY_POINTS_PER_MINUTE = 2000
WEIGHT_WITH_MUTATION = 5
WEIGHT_WITHOUT_MUTATION = 1

# The other bucket entirely, quoted here only so the two are never confused.
PRIMARY_POINTS_PER_HOUR = 5000

# GitHub asks for at least this long between mutations affecting one resource.
# Not expressed in points, so satisfying the arithmetic does not satisfy it.
SAME_RESOURCE_GAP_SECONDS = 1.0

# The one document this script ever sends. A read, and it is put through the
# same refusal check as anything supplied on the command line.
PROBE_QUERY = "query { rateLimit { limit cost remaining used resetAt } }"

# This run's own cost against the hourly budget.
POINTS_PER_QUERY = 1


def strip_noise(document):
    """Remove GraphQL comments and string literals from a document. Pure.

    A scanner rather than a regex: a hash inside a string literal is an
    ordinary character and a comment marker outside one, and the word
    "mutation" inside a search string is not a mutation. Getting that wrong
    here would misprice a document as well as misjudge whether to send it.
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
    "subscription" or "fragment". An anonymous document is query shorthand.
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

    The endpoint is the same one mutations go to, so the guard lives in code
    rather than in a comment. This script has an opinion about mutations and
    still never transmits one.
    """
    ops = operations(document)
    if not ops:
        return "the document contains no operation to send."
    for kind in ("mutation", "subscription"):
        if kind in ops:
            return ("the document contains a %s. This script prices documents, "
                    "it does not send them: a query is a read, and the section "
                    "it belongs to promises its scripts never write." % kind)
    return None


def weight(document):
    """Secondary-limit points for one request carrying this document. Pure.

    Per request, not per mutation: a document with six mutations in it is
    priced at 5, the same as a document with one. That is why batching is a
    real reduction and splitting is a fivefold increase.
    """
    return WEIGHT_WITH_MUTATION if "mutation" in operations(document) else WEIGHT_WITHOUT_MUTATION


def ceiling_per_minute(points):
    """Requests a minute this weight allows before the limit binds. Pure."""
    if not points or points <= 0:
        return 0
    return SECONDARY_POINTS_PER_MINUTE // int(points)


def min_gap_seconds(points):
    """Seconds between requests implied by the ceiling, one worker. Pure."""
    ceiling = ceiling_per_minute(points)
    return 0.0 if ceiling <= 0 else 60.0 / ceiling


def points_per_minute(rate, points):
    """What a given request rate costs against the per-minute limit. Pure."""
    return max(0, int(rate or 0)) * int(points or 0)


def minutes_for_batch(count, rate):
    """How long a batch of this size takes at this rate, in minutes. Pure."""
    rate = max(0, int(rate or 0))
    if rate <= 0:
        return None
    return math.ceil(max(0, int(count or 0)) / rate)


def classify_rate(rate, points):
    """Judge a request rate against the per-minute limit. Pure.

    Returns (state, detail). The middle state matters: a rate can be legal on
    points and still wrong, because concurrency and the same-resource gap are
    separate rules that points do not express.
    """
    spend = points_per_minute(rate, points)
    ceiling = ceiling_per_minute(points)
    if not rate:
        return ("not-measured",
                "no rate given, so this document is priced but not judged. "
                "Its ceiling is %d request(s)/minute." % ceiling)
    if spend > SECONDARY_POINTS_PER_MINUTE:
        return ("over-ceiling",
                "%d request(s)/minute of this document is %d point(s)/minute "
                "against a limit of %d." % (rate, spend, SECONDARY_POINTS_PER_MINUTE))
    if spend > SECONDARY_POINTS_PER_MINUTE * 0.8:
        return ("near-ceiling",
                "%d request(s)/minute is %d point(s)/minute, inside the limit of "
                "%d but with under a fifth of it left."
                % (rate, spend, SECONDARY_POINTS_PER_MINUTE))
    return ("within-ceiling",
            "%d request(s)/minute is %d point(s)/minute against a limit of %d."
            % (rate, spend, SECONDARY_POINTS_PER_MINUTE))


def classify_throttle(status, message, graphql_remaining):
    """Attribute a recorded failure to one bucket or the other. Pure.

    Returns (state, detail). The whole diagnosis is two readings taken
    together: which failure arrived, and what the hourly budget said at that
    moment. Either on its own is ambiguous.
    """
    text = str(message or "").lower()
    secondary = "secondary rate limit" in text
    try:
        remaining = int(graphql_remaining)
    except (TypeError, ValueError):
        remaining = None
    healthy = remaining is not None and remaining > PRIMARY_POINTS_PER_HOUR * 0.1

    if secondary and healthy:
        return ("secondary-not-budget",
                "a secondary rate limit with %d point(s) still in the hourly "
                "budget. This is the per-minute ceiling, and no amount of "
                "waiting for the hourly reset will help." % remaining)
    if secondary:
        return ("secondary-limit",
                "a secondary rate limit. The hourly budget was not readable or "
                "was itself low, so slow down and check both.")
    if "rate limit" in text and remaining == 0:
        return ("primary-exhausted",
                "the hourly point budget is spent. That is a different bucket "
                "with a different note and it refills on a schedule.")
    if "rate limit" in text:
        return ("rate-limited-unclassified",
                "a rate-limit message that does not name the secondary limit. "
                "Read resources.graphql at the moment of failure to attribute it.")
    if str(status) in ("403", "429"):
        return ("forbidden-not-throttled",
                "HTTP %s with no rate-limit wording, so this is a permission "
                "problem rather than a throttle." % status)
    return ("no-throttle", "nothing in this record names a rate limit.")


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "over-ceiling":
        return ("batch mutations into one document, serialise the loop, and cap "
                "it at %d/minute or below. The 5 points are charged per "
                "request, so fewer requests is the whole lever."
                % ceiling_per_minute(WEIGHT_WITH_MUTATION))
    if state == "near-ceiling":
        return ("leave headroom. A retry, a redeploy or one extra worker puts "
                "this over, and the limit gives no warning before it binds.")
    if state == "secondary-not-budget":
        return ("rate-limit the writer against points a minute, not requests a "
                "minute, and honour retry-after. Do not rewrite the retry "
                "logic around the hourly budget; that bucket was fine.")
    if state == "secondary-limit":
        return ("slow the writer down and record resources.graphql at the "
                "moment of failure so the next one can be attributed.")
    if state == "primary-exhausted":
        return ("see /github/graphql-rate-limited/ -- the hourly point budget "
                "is a different bucket and this is not the note for it.")
    if state == "within-ceiling":
        return ("nothing on the point arithmetic. Check concurrency and the "
                "one-second gap between mutations on the same resource "
                "separately; points do not express either.")
    return ("supply the rate the loop actually runs at, or the failure you "
            "recorded, and the arithmetic becomes a verdict.")


def price(label, document, rate):
    """Everything this script knows about one document. Pure."""
    ops = operations(document)
    points = weight(document)
    state, detail = classify_rate(rate, points)
    return {
        "document": label,
        "operations": ops,
        "points_per_request": points,
        "ceiling_per_minute": ceiling_per_minute(points),
        "min_gap_seconds": round(min_gap_seconds(points), 4),
        "points_per_minute_at_rate": points_per_minute(rate, points),
        "not_sent": refusal(document),
        "state": state,
        "detail": detail,
        "repair": repair(state),
    }


def run_query(session, document, variables=None):
    """Send one read query. Returns (status, body-or-None).

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


def graphql_budget(session):
    """The hourly GraphQL bucket, read for free. Returns a dict or None."""
    r = session.get(API + "/rate_limit", timeout=30)
    if r.status_code != 200:
        return None
    try:
        return (r.json().get("resources") or {}).get("graphql")
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--document", action="append", default=[],
                    help="path to a .graphql file to price. Repeatable. "
                         "Mutation documents are priced and never sent.")
    ap.add_argument("--query",
                    help="price a document given inline instead of from a file")
    ap.add_argument("--rate", type=int, default=0,
                    help="requests a minute the loop actually sends")
    ap.add_argument("--batch", type=int, default=0,
                    help="how many rows the job has to get through")
    ap.add_argument("--throttle-message", default="",
                    help="the error body you recorded, to attribute it")
    ap.add_argument("--throttle-status", default="",
                    help="the status code you recorded alongside it")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    documents = []
    for path in args.document:
        try:
            documents.append((path, open(path, encoding="utf-8").read()))
        except OSError as exc:
            log.error("cannot read %s: %s", path, exc)
            return 2
    if args.query:
        documents.append(("--query", args.query))
    if not documents:
        log.error("give at least one --document or --query to price")
        return 2

    log.info("point cost: %d point(s) against the %d/hour GraphQL budget",
             POINTS_PER_QUERY, PRIMARY_POINTS_PER_HOUR)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    budget = graphql_budget(session)
    if budget:
        log.info("graphql budget: %s/%s remaining", budget.get("remaining"),
                 budget.get("limit"))
    # The probe goes through the same guard as anything supplied by the caller.
    if refusal(PROBE_QUERY) is None:
        status, body = run_query(session, PROBE_QUERY)
        log.info("probe read query: HTTP %s, %d point(s) spent", status,
                 POINTS_PER_QUERY)
        if isinstance(body, dict) and body.get("errors"):
            log.warning("the probe itself carried errors: %s",
                        json.dumps(body["errors"])[:200])

    priced = [price(label, doc, args.rate) for label, doc in documents]
    for p in priced:
        log.info("%s: operations=%s -> %d point(s) per request",
                 p["document"], ", ".join(p["operations"]) or "none",
                 p["points_per_request"])
        if p["not_sent"]:
            log.info("  not sent: %s", p["not_sent"])
        log.info("  ceiling %d request(s)/minute, minimum gap %.3fs on one worker",
                 p["ceiling_per_minute"], p["min_gap_seconds"])
        log.info("  %s: %s", p["state"], p["detail"])
        if args.batch:
            at_ceiling = minutes_for_batch(args.batch, p["ceiling_per_minute"])
            log.info("  %d row(s) takes at least %s minute(s) at the ceiling",
                     args.batch, at_ceiling)
        log.info("  repair: %s", p["repair"])

    throttle = None
    if args.throttle_message or args.throttle_status:
        state, detail = classify_throttle(
            args.throttle_status, args.throttle_message,
            (budget or {}).get("remaining"))
        log.info("recorded failure -> %s: %s", state, detail)
        log.info("repair: %s", repair(state))
        throttle = {"state": state, "detail": detail}

    print(json.dumps({
        "points_spent": POINTS_PER_QUERY,
        "secondary_points_per_minute": SECONDARY_POINTS_PER_MINUTE,
        "same_resource_gap_seconds": SAME_RESOURCE_GAP_SECONDS,
        "graphql_budget": budget,
        "documents": priced,
        "recorded_failure": throttle,
    }, indent=2, default=str))
    over = [p for p in priced if p["state"] in ("over-ceiling", "near-ceiling")]
    return 1 if over or (throttle and throttle["state"].startswith("secondary")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-mutation-budget.mjs",
"js": '''/**
 * Price GraphQL documents against the per-minute secondary limit.
 *
 * Read only, and queries only. GitHub's GraphQL endpoint takes its document in
 * the request body, so a read travels by POST there exactly as a write would.
 * Every document is parsed first, anything containing a mutation or a
 * subscription is refused before a socket opens, and the only document this
 * script sends is a read query of its own.
 *
 * Against the secondary limit of 2,000 points a minute, a request whose
 * document contains a mutation counts as 5 points and one that does not counts
 * as 1. A write loop therefore reaches the wall at a fifth of the rate a read
 * loop survives, with the separate hourly budget almost untouched.
 *
 * Environment:
 *   GITHUB_TOKEN      a token with read access to the GraphQL API
 *   GITHUB_QUERY      a document to price
 *   GITHUB_RATE       requests a minute the loop actually sends
 *   GITHUB_BATCH      how many rows the job has to get through
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-mutation-budget/1.0';

/** The secondary limit on the GraphQL endpoint, and its two weights. */
export const SECONDARY_POINTS_PER_MINUTE = 2000;
export const WEIGHT_WITH_MUTATION = 5;
export const WEIGHT_WITHOUT_MUTATION = 1;

/** The other bucket entirely, named so the two are never confused. */
export const PRIMARY_POINTS_PER_HOUR = 5000;

/** GitHub asks for at least this long between mutations on one resource. */
export const SAME_RESOURCE_GAP_SECONDS = 1.0;

/** The one document this script ever sends, and it is guarded like any other. */
export const PROBE_QUERY = 'query { rateLimit { limit cost remaining used resetAt } }';

/** This run's own cost against the hourly budget. */
export const POINTS_PER_QUERY = 1;

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
      return `the document contains a ${kind}. This script prices documents, it `
        + 'does not send them: a query is a read, and the section it belongs to '
        + 'promises its scripts never write.';
    }
  }
  return null;
}

/** Secondary-limit points for one request carrying this document. Pure. */
export function weight(document) {
  return operations(document).includes('mutation')
    ? WEIGHT_WITH_MUTATION : WEIGHT_WITHOUT_MUTATION;
}

/** Requests a minute this weight allows before the limit binds. Pure. */
export function ceilingPerMinute(points) {
  const n = Number(points);
  if (!Number.isFinite(n) || n <= 0) return 0;
  return Math.floor(SECONDARY_POINTS_PER_MINUTE / n);
}

/** Seconds between requests implied by the ceiling, one worker. Pure. */
export function minGapSeconds(points) {
  const ceiling = ceilingPerMinute(points);
  return ceiling <= 0 ? 0 : 60 / ceiling;
}

/** What a given request rate costs against the per-minute limit. Pure. */
export function pointsPerMinute(rate, points) {
  const r = Math.max(0, Math.trunc(Number(rate) || 0));
  const p = Math.trunc(Number(points) || 0);
  return r * p;
}

/** How long a batch of this size takes at this rate, in minutes. Pure. */
export function minutesForBatch(count, rate) {
  const r = Math.max(0, Math.trunc(Number(rate) || 0));
  if (r <= 0) return null;
  return Math.ceil(Math.max(0, Math.trunc(Number(count) || 0)) / r);
}

/** Judge a request rate against the per-minute limit. Pure. [state, detail]. */
export function classifyRate(rate, points) {
  const spend = pointsPerMinute(rate, points);
  const ceiling = ceilingPerMinute(points);
  if (!rate) {
    return ['not-measured', 'no rate given, so this document is priced but not '
      + `judged. Its ceiling is ${ceiling} request(s)/minute.`];
  }
  if (spend > SECONDARY_POINTS_PER_MINUTE) {
    return ['over-ceiling', `${rate} request(s)/minute of this document is `
      + `${spend} point(s)/minute against a limit of ${SECONDARY_POINTS_PER_MINUTE}.`];
  }
  if (spend > SECONDARY_POINTS_PER_MINUTE * 0.8) {
    return ['near-ceiling', `${rate} request(s)/minute is ${spend} `
      + `point(s)/minute, inside the limit of ${SECONDARY_POINTS_PER_MINUTE} but `
      + 'with under a fifth of it left.'];
  }
  return ['within-ceiling', `${rate} request(s)/minute is ${spend} `
    + `point(s)/minute against a limit of ${SECONDARY_POINTS_PER_MINUTE}.`];
}

/** Attribute a recorded failure to one bucket or the other. Pure. */
export function classifyThrottle(status, message, graphqlRemaining) {
  const text = String(message ?? '').toLowerCase();
  const secondary = text.includes('secondary rate limit');
  const parsed = Number(graphqlRemaining);
  const remaining = Number.isFinite(parsed) && graphqlRemaining !== null
    && graphqlRemaining !== '' ? parsed : null;
  const healthy = remaining !== null && remaining > PRIMARY_POINTS_PER_HOUR * 0.1;

  if (secondary && healthy) {
    return ['secondary-not-budget', `a secondary rate limit with ${remaining} `
      + 'point(s) still in the hourly budget. This is the per-minute ceiling, '
      + 'and no amount of waiting for the hourly reset will help.'];
  }
  if (secondary) {
    return ['secondary-limit', 'a secondary rate limit. The hourly budget was '
      + 'not readable or was itself low, so slow down and check both.'];
  }
  if (text.includes('rate limit') && remaining === 0) {
    return ['primary-exhausted', 'the hourly point budget is spent. That is a '
      + 'different bucket with a different note and it refills on a schedule.'];
  }
  if (text.includes('rate limit')) {
    return ['rate-limited-unclassified', 'a rate-limit message that does not '
      + 'name the secondary limit. Read resources.graphql at the moment of '
      + 'failure to attribute it.'];
  }
  if (['403', '429'].includes(String(status))) {
    return ['forbidden-not-throttled', `HTTP ${status} with no rate-limit `
      + 'wording, so this is a permission problem rather than a throttle.'];
  }
  return ['no-throttle', 'nothing in this record names a rate limit.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'over-ceiling') {
    return 'batch mutations into one document, serialise the loop, and cap it '
      + `at ${ceilingPerMinute(WEIGHT_WITH_MUTATION)}/minute or below. The 5 `
      + 'points are charged per request, so fewer requests is the whole lever.';
  }
  if (state === 'near-ceiling') {
    return 'leave headroom. A retry, a redeploy or one extra worker puts this '
      + 'over, and the limit gives no warning before it binds.';
  }
  if (state === 'secondary-not-budget') {
    return 'rate-limit the writer against points a minute, not requests a '
      + 'minute, and honour retry-after. Do not rewrite the retry logic around '
      + 'the hourly budget; that bucket was fine.';
  }
  if (state === 'secondary-limit') {
    return 'slow the writer down and record resources.graphql at the moment of '
      + 'failure so the next one can be attributed.';
  }
  if (state === 'primary-exhausted') {
    return 'see /github/graphql-rate-limited/ -- the hourly point budget is a '
      + 'different bucket and this is not the note for it.';
  }
  if (state === 'within-ceiling') {
    return 'nothing on the point arithmetic. Check concurrency and the '
      + 'one-second gap between mutations on the same resource separately; '
      + 'points do not express either.';
  }
  return 'supply the rate the loop actually runs at, or the failure you '
    + 'recorded, and the arithmetic becomes a verdict.';
}

/** Everything this script knows about one document. Pure. */
export function price(label, document, rate) {
  const ops = operations(document);
  const points = weight(document);
  const [state, detail] = classifyRate(rate, points);
  return {
    document: label,
    operations: ops,
    points_per_request: points,
    ceiling_per_minute: ceilingPerMinute(points),
    min_gap_seconds: Number(minGapSeconds(points).toFixed(4)),
    points_per_minute_at_rate: pointsPerMinute(rate, points),
    not_sent: refusal(document),
    state,
    detail,
    repair: repair(state),
  };
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'Content-Type': 'application/json',
    'User-Agent': UA,
  };
}

async function runQuery(token, document) {
  const res = await fetch(`${API}/graphql`, {
    // A GraphQL query is a read. POST is only how the document reaches the
    // endpoint, and refusal() has already rejected anything that is not a read.
    method: 'POST',
    headers: headers(token),
    body: JSON.stringify({ query: document, variables: {} }),
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function graphqlBudget(token) {
  const res = await fetch(`${API}/rate_limit`, { headers: headers(token) });
  if (!res.ok) return null;
  try {
    const body = await res.json();
    return (body.resources || {}).graphql || null;
  } catch { return null; }
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const document = process.env.GITHUB_QUERY;
  if (!token || !document) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_QUERY');
    process.exitCode = 2;
    return;
  }
  const rate = Number(process.env.GITHUB_RATE || 0);
  const batch = Number(process.env.GITHUB_BATCH || 0);

  console.log(`point cost: ${POINTS_PER_QUERY} point(s) against the `
    + `${PRIMARY_POINTS_PER_HOUR}/hour GraphQL budget`);

  const budget = await graphqlBudget(token);
  if (budget) {
    console.log(`graphql budget: ${budget.remaining}/${budget.limit} remaining`);
  }
  if (refusal(PROBE_QUERY) === null) {
    const { status } = await runQuery(token, PROBE_QUERY);
    console.log(`probe read query: HTTP ${status}, ${POINTS_PER_QUERY} point(s) spent`);
  }

  const p = price('GITHUB_QUERY', document, rate);
  console.log(`${p.document}: operations=${p.operations.join(', ') || 'none'} -> `
    + `${p.points_per_request} point(s) per request`);
  if (p.not_sent) console.log(`  not sent: ${p.not_sent}`);
  console.log(`  ceiling ${p.ceiling_per_minute} request(s)/minute, minimum gap `
    + `${p.min_gap_seconds.toFixed(3)}s on one worker`);
  console.log(`  ${p.state}: ${p.detail}`);
  if (batch) {
    console.log(`  ${batch} row(s) takes at least `
      + `${minutesForBatch(batch, p.ceiling_per_minute)} minute(s) at the ceiling`);
  }
  console.log(`  repair: ${p.repair}`);

  console.log(JSON.stringify({
    points_spent: POINTS_PER_QUERY,
    secondary_points_per_minute: SECONDARY_POINTS_PER_MINUTE,
    graphql_budget: budget,
    documents: [p],
  }, null, 2));
  process.exitCode = ['over-ceiling', 'near-ceiling'].includes(p.state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The weights are asserted directly, because the whole note is two numbers and a ratio: a document with one mutation and a document with six are both 5 points, a document with none is 1, and the word appearing in a string literal or a comment changes nothing. On top of that sit the derived figures — the ceiling, the gap, the points a given rate spends — and then the differential, which is asserted on both readings together, since a secondary message with a healthy budget and a secondary message with an empty one are different findings. The refusal is tested last, including on the script's own probe, which has to pass the same guard as anything a caller supplies.",
"test_py_file": "test_github_graphql_mutation_budget.py",
"test_py": '''from github_graphql_mutation_budget import (
    PROBE_QUERY, SECONDARY_POINTS_PER_MINUTE, WEIGHT_WITHOUT_MUTATION,
    WEIGHT_WITH_MUTATION, ceiling_per_minute, classify_rate, classify_throttle,
    min_gap_seconds, minutes_for_batch, operations, points_per_minute, price,
    refusal, repair, weight,
)

READ = "query Q($n: Int!) { repository(owner: \\"a\\", name: \\"b\\") { issues(first: $n) { nodes { id } } } }"
WRITE = "mutation M($id: ID!) { addLabelsToLabelable(input: {labelableId: $id, labelIds: []}) { clientMutationId } }"
THREE_WRITES = ("mutation A { one { clientMutationId } } "
                "mutation B { two { clientMutationId } } "
                "mutation C { three { clientMutationId } }")


def test_a_mutation_document_is_five_points_and_a_query_is_one():
    assert weight(WRITE) == WEIGHT_WITH_MUTATION == 5
    assert weight(READ) == WEIGHT_WITHOUT_MUTATION == 1


def test_the_weight_is_per_request_not_per_mutation():
    assert operations(THREE_WRITES) == ["mutation", "mutation", "mutation"]
    assert weight(THREE_WRITES) == 5
    # Which is why batching is a real reduction: three separate requests would
    # be 15 points, the same three in one document are 5.
    assert weight(WRITE) * 3 > weight(THREE_WRITES)


def test_the_word_mutation_in_a_string_or_a_comment_is_not_one():
    quoted = 'query Q { search(query: "mutation", type: ISSUE, first: 1) { issueCount } }'
    assert weight(quoted) == 1
    assert refusal(quoted) is None
    commented = "# mutation M { addStar }\\nquery Q { viewer { login } }"
    assert weight(commented) == 1
    assert refusal(commented) is None


def test_the_ceiling_is_the_limit_divided_by_the_weight():
    assert SECONDARY_POINTS_PER_MINUTE == 2000
    assert ceiling_per_minute(5) == 400
    assert ceiling_per_minute(1) == 2000
    assert ceiling_per_minute(0) == 0
    assert ceiling_per_minute(None) == 0


def test_the_gap_falls_out_of_the_ceiling():
    assert round(min_gap_seconds(5), 3) == 0.15
    assert round(min_gap_seconds(1), 3) == 0.03
    assert min_gap_seconds(0) == 0.0


def test_a_rate_is_priced_in_points_not_in_requests():
    assert points_per_minute(500, 5) == 2500
    assert points_per_minute(500, 1) == 500
    assert points_per_minute(0, 5) == 0
    assert points_per_minute(None, 5) == 0


def test_the_same_rate_breaks_the_writer_and_not_the_reader():
    write_state, _ = classify_rate(500, weight(WRITE))
    read_state, _ = classify_rate(500, weight(READ))
    assert write_state == "over-ceiling"
    assert read_state == "within-ceiling"


def test_a_rate_just_inside_the_limit_is_still_reported():
    state, detail = classify_rate(340, 5)
    assert state == "near-ceiling"
    assert "1700" in detail
    assert "headroom" in repair(state)


def test_an_unmeasured_rate_is_priced_but_not_judged():
    state, detail = classify_rate(0, 5)
    assert state == "not-measured"
    assert "400" in detail


def test_a_secondary_message_with_a_healthy_budget_is_the_finding():
    state, detail = classify_throttle(
        403, "You have exceeded a secondary rate limit", 4863)
    assert state == "secondary-not-budget"
    assert "4863" in detail
    assert "points a minute" in repair(state)


def test_a_secondary_message_with_an_empty_budget_is_not_conclusive():
    state, _ = classify_throttle(
        429, "You have exceeded a secondary rate limit", 0)
    assert state == "secondary-limit"


def test_an_exhausted_hourly_budget_is_handed_to_the_other_note():
    state, _ = classify_throttle(200, "API rate limit exceeded", 0)
    assert state == "primary-exhausted"
    assert "graphql-rate-limited" in repair(state)


def test_a_403_that_is_not_a_throttle_is_not_called_one():
    state, _ = classify_throttle(403, "Resource not accessible", 4900)
    assert state == "forbidden-not-throttled"
    assert classify_throttle("", "", 4900)[0] == "no-throttle"


def test_a_batch_is_costed_in_minutes():
    assert minutes_for_batch(11000, 400) == 28
    assert minutes_for_batch(11000, 2000) == 6
    assert minutes_for_batch(11000, 0) is None


def test_the_document_is_priced_and_refused_in_the_same_breath():
    p = price("label_issue.graphql", WRITE, 500)
    assert p["points_per_request"] == 5
    assert p["ceiling_per_minute"] == 400
    assert p["state"] == "over-ceiling"
    assert p["not_sent"] and "does not send them" in p["not_sent"]
    assert price("fetch.graphql", READ, 500)["not_sent"] is None


def test_the_scripts_own_probe_passes_its_own_guard():
    assert refusal(PROBE_QUERY) is None
    assert weight(PROBE_QUERY) == 1
    assert refusal("subscription S { thing { id } }")
    assert refusal("") == "the document contains no operation to send."
''',
"test_js_file": "github-graphql-mutation-budget.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  PROBE_QUERY, SECONDARY_POINTS_PER_MINUTE, WEIGHT_WITHOUT_MUTATION,
  WEIGHT_WITH_MUTATION, ceilingPerMinute, classifyRate, classifyThrottle,
  minGapSeconds, minutesForBatch, operations, pointsPerMinute, price, refusal,
  repair, weight,
} from './github-graphql-mutation-budget.mjs';

const READ = 'query Q($n: Int!) { repository(owner: "a", name: "b") { issues(first: $n) { nodes { id } } } }';
const WRITE = 'mutation M($id: ID!) { addLabelsToLabelable(input: {labelableId: $id, labelIds: []}) { clientMutationId } }';
const THREE_WRITES = 'mutation A { one { clientMutationId } } '
  + 'mutation B { two { clientMutationId } } '
  + 'mutation C { three { clientMutationId } }';

test('a mutation document is five points and a query is one', () => {
  assert.equal(weight(WRITE), WEIGHT_WITH_MUTATION);
  assert.equal(WEIGHT_WITH_MUTATION, 5);
  assert.equal(weight(READ), WEIGHT_WITHOUT_MUTATION);
  assert.equal(WEIGHT_WITHOUT_MUTATION, 1);
});

test('the weight is per request not per mutation', () => {
  assert.deepEqual(operations(THREE_WRITES), ['mutation', 'mutation', 'mutation']);
  assert.equal(weight(THREE_WRITES), 5);
  assert.ok(weight(WRITE) * 3 > weight(THREE_WRITES));
});

test('the word mutation in a string or a comment is not one', () => {
  const quoted = 'query Q { search(query: "mutation", type: ISSUE, first: 1) { issueCount } }';
  assert.equal(weight(quoted), 1);
  assert.equal(refusal(quoted), null);
  const commented = '# mutation M { addStar }\\nquery Q { viewer { login } }';
  assert.equal(weight(commented), 1);
  assert.equal(refusal(commented), null);
});

test('the ceiling is the limit divided by the weight', () => {
  assert.equal(SECONDARY_POINTS_PER_MINUTE, 2000);
  assert.equal(ceilingPerMinute(5), 400);
  assert.equal(ceilingPerMinute(1), 2000);
  assert.equal(ceilingPerMinute(0), 0);
  assert.equal(ceilingPerMinute(null), 0);
});

test('the gap falls out of the ceiling', () => {
  assert.equal(Number(minGapSeconds(5).toFixed(3)), 0.15);
  assert.equal(Number(minGapSeconds(1).toFixed(3)), 0.03);
  assert.equal(minGapSeconds(0), 0);
});

test('a rate is priced in points not in requests', () => {
  assert.equal(pointsPerMinute(500, 5), 2500);
  assert.equal(pointsPerMinute(500, 1), 500);
  assert.equal(pointsPerMinute(0, 5), 0);
  assert.equal(pointsPerMinute(null, 5), 0);
});

test('the same rate breaks the writer and not the reader', () => {
  assert.equal(classifyRate(500, weight(WRITE))[0], 'over-ceiling');
  assert.equal(classifyRate(500, weight(READ))[0], 'within-ceiling');
});

test('a rate just inside the limit is still reported', () => {
  const [state, detail] = classifyRate(340, 5);
  assert.equal(state, 'near-ceiling');
  assert.match(detail, /1700/);
  assert.match(repair(state), /headroom/);
});

test('an unmeasured rate is priced but not judged', () => {
  const [state, detail] = classifyRate(0, 5);
  assert.equal(state, 'not-measured');
  assert.match(detail, /400/);
});

test('a secondary message with a healthy budget is the finding', () => {
  const [state, detail] = classifyThrottle(
    403, 'You have exceeded a secondary rate limit', 4863);
  assert.equal(state, 'secondary-not-budget');
  assert.match(detail, /4863/);
  assert.match(repair(state), /points a minute/);
});

test('a secondary message with an empty budget is not conclusive', () => {
  assert.equal(
    classifyThrottle(429, 'You have exceeded a secondary rate limit', 0)[0],
    'secondary-limit',
  );
});

test('an exhausted hourly budget is handed to the other note', () => {
  const [state] = classifyThrottle(200, 'API rate limit exceeded', 0);
  assert.equal(state, 'primary-exhausted');
  assert.match(repair(state), /graphql-rate-limited/);
});

test('a 403 that is not a throttle is not called one', () => {
  assert.equal(classifyThrottle(403, 'Resource not accessible', 4900)[0],
    'forbidden-not-throttled');
  assert.equal(classifyThrottle('', '', 4900)[0], 'no-throttle');
});

test('a batch is costed in minutes', () => {
  assert.equal(minutesForBatch(11000, 400), 28);
  assert.equal(minutesForBatch(11000, 2000), 6);
  assert.equal(minutesForBatch(11000, 0), null);
});

test('the document is priced and refused in the same breath', () => {
  const p = price('label_issue.graphql', WRITE, 500);
  assert.equal(p.points_per_request, 5);
  assert.equal(p.ceiling_per_minute, 400);
  assert.equal(p.state, 'over-ceiling');
  assert.match(p.not_sent, /does not send them/);
  assert.equal(price('fetch.graphql', READ, 500).not_sent, null);
});

test('the scripts own probe passes its own guard', () => {
  assert.equal(refusal(PROBE_QUERY), null);
  assert.equal(weight(PROBE_QUERY), 1);
  assert.ok(refusal('subscription S { thing { id } }'));
  assert.equal(refusal(''), 'the document contains no operation to send.');
});
''',
"faq": [
 ("Why does GET /rate_limit show plenty of points left when I am being throttled?",
  "Because it reports a different bucket. GET /rate_limit describes the primary budget: 5,000 points an hour for a user token, refilling on a schedule, with a remaining count you can read before you spend it. The secondary limit is a per-minute burst control with no bucket, no header and no endpoint that reports headroom, and it is the one a fast mutation loop hits. Seeing a healthy remaining count next to a secondary-rate-limit message is not a contradiction, it is the diagnosis: those two readings together are what tell you which limit you crossed."),
 ("Does a document with ten mutations in it cost 50 points?",
  "No. The weight is applied to the request, not to the operations inside it: any document containing a mutation is 5 points, whether that is one mutation or ten. That makes batching the cheapest fix available, because ten separate requests are 50 points and the same ten in one document are 5. It also means the reverse is a real regression — splitting one document into several to make the code tidier multiplies the secondary cost by the number of pieces, and nothing in the response will tell you that happened."),
 ("Is 400 mutations a minute actually safe to run at?",
  "It is the ceiling, not a target. Two other rules sit on top of the point arithmetic and neither is expressed in points: no more than 100 concurrent requests across the REST and GraphQL APIs together, and at least one second between mutations that affect the same resource. A loop that satisfies the points and violates either of those is still throttled. Treat 400 as the number you must stay under and pick your real rate from the shape of the work, leaving room for retries, which cost the same as first attempts."),
 ("Should the script not just send a mutation to prove the limit exists?",
  "It should not, and it cannot. Every script in this section holds a token that can reach real repositories and none of them writes, so a note about mutations has to be built out of the document text, the documented weights and failures you already recorded. That is enough: the weight is a property of the document, the ceiling is division, and the attribution of a past 403 is a comparison between its message and the budget at that moment. The script parses your mutation documents, prices them, and refuses to open a socket for them."),
 ("How is this different from the REST secondary limits?",
  "Different endpoint, different numbers, same family of control. REST has a per-endpoint allowance of 900 points a minute alongside a CPU-time cap, and a separate ceiling of roughly 80 content-generating requests a minute; both have their own notes here. The GraphQL endpoint has this one: 2,000 points a minute, mutations at 5 and everything else at 1. A team that moved its writes to GraphQL to get away from the content-creation limit did not escape a limit, it changed which arithmetic applies, and 400 requests a minute is the number that matters afterwards."),
],
"related": [
 ("/github/graphql-rate-limited/", "The hourly GraphQL point budget is a separate bucket"),
 ("/github/secondary-limit-content-creation/", "The REST content-creation limit, around 80 a minute"),
 ("/github/retry-after-ignored/", "Ignoring retry-after extends the throttle"),
],
"citations": [CITE_GQL_RESOURCE, CITE_GQL_RATE, CITE_REST_RATE_LIMITS, CITE_REST_RATE_LIMIT],
},
{
"slug": "graphql-search-same-1000-cap",
"title": "GraphQL search stops at the same 1,000 results as REST",
"description": "issueCount reports 18,000 and hasNextPage turns false after ten pages. Moving the query to GraphQL to escape the REST cap moves it onto the same index.",
"h1": "GraphQL search stops at the same 1,000 results as REST",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github graphql search 1000 results limit",
             "graphql search hasnextpage false issuecount",
             "github graphql search pagination stops",
             "github search api 1000 limit graphql v4",
             "github graphql search all issues cap"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The REST search was hitting the thousand-result ceiling, loudly, with a <code>422</code> on page eleven that nobody could miss. So the query got rewritten in GraphQL, which is the modern API, has cursors instead of page numbers, and does not document a page limit anywhere obvious. The rewrite works. It runs to completion with no error at all, <code>hasNextPage</code> turns <code>false</code>, the loop exits cleanly, and it has collected 1,000 of the 18,231 issues that <code>issueCount</code> is reporting in the very same response.",
"short_answer": """<p>The ceiling belongs to the search index, not to the protocol. GraphQL's <code>search</code> connection is served by the same index as <code>GET /search/*</code> and inherits the same limit of about 1,000 retrievable results per query. Changing API changed nothing about how many results you can reach.</p>
<p>What did change is how the truncation announces itself. REST refuses page 11 with <code>422 Validation Failed</code> and the words &ldquo;Only the first 1000 search results are available&rdquo;, which is impossible to miss. GraphQL just stops: <code>pageInfo.hasNextPage</code> becomes <code>false</code> after roughly ten pages of 100 and the walk terminates normally, with <code>issueCount</code> still reporting the full match count beside it. Compare those two numbers on every search you paginate, and where you need everything rather than the best matches, use a typed connection — <code>repository.issues</code>, <code>organization.repositories</code> — which paginates with no ceiling at all.</p>""",
"problem": """<p>This one is a reward for doing the right thing. Somebody hit the REST ceiling, read the note, understood that partitioning the query is the answer, and then noticed that GitHub has a second API which is newer, is cursor-based, and whose search field says nothing about a thousand of anything. Migrating looks like the structural fix and partitioning looks like the workaround, so the migration gets scheduled and the workaround gets dropped.</p>
<p>The migrated code is then better in every visible way. It asks for exactly the fields it wants, it costs one point a page instead of a search-bucket request, it uses cursors so pages cannot slip, and it has a proper termination condition instead of a page counter. It also silently returns six per cent of the data, and every property that makes it better makes the loss harder to see: there is no error to catch, no status code to check, and the loop ends the way a correct loop ends.</p>
<p>The detail that keeps it hidden for months is that <code>issueCount</code> is right. The response tells you there are 18,231 matches and hands you 1,000 of them, in the same object, and nothing anywhere compares the two. Dashboards built on this do not look empty; they look plausible and stable, because the truncation is deterministic. The first person to notice is usually someone who knows a specific issue exists and cannot find it in the export.</p>""",
"why": """<p><strong>The limit lives in the index.</strong> Search on GitHub is a separate system from the object store, and it serves ranked results with a cap on how deep into the ranking you may page. Both APIs are front ends to it. That is why the number is the same on both, why it is not a page-size problem, and why no combination of <code>first</code> and <code>after</code> gets past it: you are asking the index for its 1,001st best match and it does not serve one.</p>
<p><strong>Silent truncation is the actual difference between the two notes.</strong> The <a href="/github/search-1000-result-cap/">REST ceiling has its own note</a> and it is a note about an error: <code>total_count</code> is huge, page 11 returns 422, and the repair is to partition. This note is about the same ceiling arriving with no error at all. A client that treats <code>hasNextPage: false</code> as &ldquo;there is no more data&rdquo; — which is exactly what the pagination documentation tells you to do — cannot distinguish a complete answer from a truncated one without looking at <code>issueCount</code>.</p>
<p><strong><code>issueCount</code> is a match count, not a fetch count.</strong> It reports how many documents the index matched, the same way <code>total_count</code> does in REST, and it keeps reporting the full number after the ceiling has cut you off. That makes it the single most useful field in the response for this problem: the gap between <code>issueCount</code> and the number of nodes you actually collected is the size of what you did not get, and it is available on page one, before you spend anything.</p>
<p><strong>GraphQL has one escape REST does not.</strong> Typed connections are not search: <code>repository.issues</code>, <code>repository.pullRequests</code>, <code>organization.repositories</code>, <code>repository.discussions</code> read the object store directly and paginate without a ceiling. If what you want is an inventory rather than a ranking — every issue in this repository, every repository in this org — the search connection is the wrong tool and swapping to a typed connection removes the limit rather than working around it. Only the queries that genuinely need cross-repository search terms have to be partitioned.</p>
<p><strong>Partitioning works the same as it does in REST, with better ergonomics.</strong> Slice by <code>created:</code> date ranges, by <code>repo:</code>, by label, until every slice reports an <code>issueCount</code> under 1,000, then union them. GraphQL lets you run several slices in one document as aliased fields, which costs fewer requests than the REST equivalent, though each slice still counts toward the point cost and each still has its own ceiling.</p>
<p><strong>This is not the incomplete-results flag and not the node limit.</strong> <a href="/github/search-incomplete-results/">A timed-out search returns partial results with a flag set</a> and is non-deterministic; this ceiling is exact and repeatable. And the node limit rejects a query for its shape before it runs, which is loud and happens at 500,000 rather than 1,000. The script names which of the three it is looking at so none of them gets the wrong repair.</p>""",
"steps": [
 {"h": "Read issueCount on the first page and compare it to nothing else",
  "body": """<p>One page, one point. If <code>issueCount</code> is above 1,000 you already know the tail is unreachable through this connection, before you have paged anywhere. That single comparison is the cheapest version of this whole audit, and it is the one to put in the client permanently.</p>"""},
 {"h": "Walk the cursor until it stops and record where it stopped",
  "body": """<p>The script pages with <code>after: endCursor</code> at 100 a page and keeps count. Ten or eleven pages is enough: the point is to watch <code>hasNextPage</code> turn <code>false</code> while <code>issueCount</code> is still enormous. It prints the point cost before it starts, because a page is a point and a long walk is a real spend.</p>"""},
 {"h": "Name the shape of the stop",
  "body": """<p>Pagination ending with a full collection and a large <code>issueCount</code> is the ceiling. Pagination ending early with a small count is a complete answer. Pagination that never ends is a client bug. The script sorts the run into one of those rather than reporting &ldquo;done&rdquo;, and it says explicitly that no error was raised, because the absence of an error is the thing people find hardest to believe.</p>"""},
 {"h": "Decide between partitioning and abandoning search",
  "body": """<p>If the goal is an inventory, the script names the typed connection that answers the same question with no ceiling, and that is the better repair. If the goal is genuinely a search, it computes how many slices the match count needs and suggests the axis to slice on. Those are different repairs and picking the wrong one costs a week.</p>"""},
 {"h": "Put the comparison in the client, not in a runbook",
  "body": """<p>The permanent fix is two lines: request <code>issueCount</code> alongside <code>nodes</code>, and refuse to publish a result set whose length is below it without labelling it truncated. A walk that trusts <code>hasNextPage</code> alone will keep terminating cleanly on an incomplete answer for as long as the query is popular enough to match a thousand things.</p>"""},
],
"verify": """<p>Once the walk compares what it collected against what the index matched, the run reports the ceiling instead of terminating quietly on top of it.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_search_ceiling.py \\
    --query "org:acme is:issue is:open" --type ISSUE --max-pages 11
# point cost: up to 11 point(s) against the 5,000/hour GraphQL budget
# page 1: 100 node(s), collected=100, matches=18231, hasNextPage=yes
# page 10: 100 node(s), collected=1000, matches=18231, hasNextPage=no
# ceiling-hit-silently: pagination stopped after 1000 node(s) with the index
# reporting 18231 match(es). No error was raised and hasNextPage simply turned
# false.
# reachable: 1000    unreachable: 17231
# the REST twin of this stop is 422 Validation Failed on page 11 [...]
# here it is no error at all. pageInfo.hasNextPage turns false and the walk
# terminates the way a complete walk terminates.
# repair: for an inventory use the typed connection repository.issues or
# repository.pullRequests, which has no ceiling. For a genuine search,
# partition into at least 19 slice(s) by created: date range and union them.</code></pre>""",
"code_intro": "The walk is small and the arithmetic around it is the note. Everything that decides anything is pure: the reachable and unreachable halves of a match count, the number of pages that fit under the ceiling, the classification of how a walk ended, the number of slices a partition needs, and the typed connection that answers the same question without a ceiling. The live part sends one search query per page with <code>after: endCursor</code>, refuses any document that is not a read, and prints the maximum it might spend before it spends any of it.",
"py_file": "github_graphql_search_ceiling.py",
"py": '''"""Show that GraphQL search stops at the same 1,000 results REST does.

Read only, and queries only. GitHub's GraphQL endpoint takes its document in
the request body, so a read travels by POST there exactly as a write would;
that is a transport detail, not a licence to write. This script parses the
document it is about to send and refuses to open a socket if it contains a
mutation or a subscription.

GraphQL's search connection is served by the same index as GET /search/*, and
inherits the same ceiling of roughly 1,000 retrievable results per query. The
difference is how it says so: REST returns 422 Validation Failed on page 11,
GraphQL just sets pageInfo.hasNextPage to false and lets the walk finish
normally with issueCount still reporting the full match count beside it.

What this can and cannot see: the API cannot tell you whether your client
compares the two numbers. What it can do is walk the connection until it stops,
report where it stopped against what the index matched, and say plainly that no
error was raised.

Environment:

    GITHUB_TOKEN    a token with read access to the GraphQL API
"""
import argparse
import json
import logging
import math
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_search_ceiling")

API = "https://api.github.com"
UA = "github-graphql-search-ceiling/1.0"

# The retrievable-result ceiling on the search index. Identical on both APIs
# because it is a property of the index rather than of the protocol.
SEARCH_RESULT_CEILING = 1000

# The largest page any GraphQL connection will serve.
MAX_PAGE_SIZE = 100

# One search connection at first: 100 costs one point.
POINTS_PER_PAGE = 1

SEARCH_QUERY = (
    "query($q: String!, $type: SearchType!, $after: String) {"
    " search(query: $q, type: $type, first: 100, after: $after) {"
    " issueCount repositoryCount userCount"
    " pageInfo { hasNextPage endCursor }"
    " nodes { __typename } } }"
)

# The connections that answer an inventory question without going through the
# index at all, and therefore without a ceiling.
TYPED_CONNECTIONS = {
    "ISSUE": "repository.issues or repository.pullRequests",
    "REPOSITORY": "organization.repositories or user.repositories",
    "USER": "organization.membersWithRole",
    "DISCUSSION": "repository.discussions",
}


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


def reachable(total):
    """How many of the matches can actually be paged to. Pure."""
    try:
        total = max(0, int(total))
    except (TypeError, ValueError):
        return 0
    return min(total, SEARCH_RESULT_CEILING)


def unreachable(total):
    """How many matches exist that no cursor will ever reach. Pure."""
    try:
        total = max(0, int(total))
    except (TypeError, ValueError):
        return 0
    return max(0, total - SEARCH_RESULT_CEILING)


def pages_to_ceiling(page_size=MAX_PAGE_SIZE):
    """How many pages of this size fit under the ceiling. Pure."""
    size = min(max(1, int(page_size or 1)), MAX_PAGE_SIZE)
    return math.ceil(SEARCH_RESULT_CEILING / size)


def slices_needed(total):
    """How many under-the-ceiling slices a partition needs. Pure."""
    try:
        total = max(0, int(total))
    except (TypeError, ValueError):
        return 0
    return math.ceil(total / SEARCH_RESULT_CEILING) if total else 0


def typed_connection_for(search_type):
    """The ceiling-free connection that answers the same question. Pure."""
    return TYPED_CONNECTIONS.get(str(search_type or "").upper(),
                                 "the typed connection for this object type")


def truncation_signal(protocol):
    """How each API announces the same ceiling. Pure.

    Kept as data because the whole note is the difference between these two
    sentences, and a reader who has only ever seen the first one does not
    believe the second until it is written down next to it.
    """
    if str(protocol).lower() == "rest":
        return ("422 Validation Failed on page 11, with the message "
                "\\"Only the first 1000 search results are available\\".")
    return ("no error at all. pageInfo.hasNextPage turns false and the walk "
            "terminates the way a complete walk terminates.")


def classify_walk(total, collected, has_next_page, pages_walked, max_pages):
    """How this walk ended, and whether that ending was honest. Pure.

    Returns (state, detail). The two states that both end with hasNextPage
    false are the point: one of them is a complete answer and one of them is
    six per cent of an answer, and they are the same shape of response.
    """
    total = reachable(total) + unreachable(total)
    collected = max(0, int(collected or 0))
    if has_next_page and pages_walked >= max_pages:
        return ("stopped-early-by-request",
                "the walk stopped at the --max-pages limit with more pages "
                "available, so nothing about the ceiling is proved yet. "
                "%d of %d node(s) collected." % (collected, total))
    if has_next_page:
        return ("still-paging",
                "the connection still reports another page. Keep walking or "
                "raise --max-pages.")
    if collected >= SEARCH_RESULT_CEILING and total > collected:
        return ("ceiling-hit-silently",
                "pagination stopped after %d node(s) with the index reporting "
                "%d match(es). No error was raised and hasNextPage simply "
                "turned false." % (collected, total))
    if total > collected:
        return ("truncated-early",
                "the walk ended with %d of %d match(es) and below the ceiling, "
                "which is not this note: check for a timed-out search or a "
                "filter applied after the count." % (collected, total))
    return ("complete",
            "%d node(s) collected against %d match(es). This query is under "
            "the ceiling and the answer is whole." % (collected, total))


def repair(state, total, search_type):
    """The sentence a reader has to act on. Pure."""
    if state == "ceiling-hit-silently":
        return ("for an inventory use the typed connection %s, which has no "
                "ceiling. For a genuine search, partition into at least %d "
                "slice(s) by created: date range and union them."
                % (typed_connection_for(search_type), slices_needed(total)))
    if state == "truncated-early":
        return ("see /github/search-incomplete-results/ -- a search that ends "
                "below the ceiling ended for a different reason, and that one "
                "is not deterministic.")
    if state == "still-paging":
        return ("nothing yet. Walk to the end, or read issueCount on page one "
                "and compare it against %d." % SEARCH_RESULT_CEILING)
    if state == "stopped-early-by-request":
        return ("raise --max-pages to at least %d to reach the ceiling, or "
                "trust issueCount, which already tells you."
                % pages_to_ceiling())
    return ("request issueCount alongside nodes and refuse to publish a result "
            "set shorter than it without labelling it truncated.")


def point_cost(max_pages):
    """The most this run can spend against the hourly budget. Pure."""
    return max(0, int(max_pages or 0)) * POINTS_PER_PAGE


def run_query(session, document, variables):
    """Send one search page. Returns (status, body-or-None).

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


def match_count(search, search_type):
    """The index's own count for this search type. Pure."""
    if not isinstance(search, dict):
        return 0
    key = {"ISSUE": "issueCount", "REPOSITORY": "repositoryCount",
           "USER": "userCount"}.get(str(search_type or "").upper(), "issueCount")
    return int(search.get(key) or 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", required=True,
                    help="the search string, e.g. 'org:acme is:issue is:open'")
    ap.add_argument("--type", default="ISSUE",
                    choices=["ISSUE", "REPOSITORY", "USER", "DISCUSSION"],
                    help="the GraphQL SearchType to use")
    ap.add_argument("--max-pages", type=int, default=11,
                    help="how many pages of 100 to walk. Ten reaches the "
                         "ceiling; eleven proves the walk stops there.")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    why_not = refusal(SEARCH_QUERY)
    if why_not:
        log.error("refusing to send: %s", why_not)
        return 2

    log.info("point cost: up to %d point(s) against the 5,000/hour GraphQL budget",
             point_cost(args.max_pages))

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    cursor, collected, total, pages = None, 0, 0, 0
    has_next = False
    while pages < args.max_pages:
        status, body = run_query(session, SEARCH_QUERY,
                                 {"q": args.query, "type": args.type,
                                  "after": cursor})
        if not isinstance(body, dict) or body.get("errors"):
            log.error("the search itself failed: HTTP %s %s", status,
                      json.dumps((body or {}).get("errors", []))[:300])
            return 2
        search = (body.get("data") or {}).get("search") or {}
        nodes = search.get("nodes") or []
        info = search.get("pageInfo") or {}
        pages += 1
        collected += len(nodes)
        total = match_count(search, args.type)
        has_next = bool(info.get("hasNextPage"))
        cursor = info.get("endCursor")
        log.info("page %d: %d node(s), collected=%d, matches=%d, hasNextPage=%s",
                 pages, len(nodes), collected, total, "yes" if has_next else "no")
        if not has_next:
            break

    state, detail = classify_walk(total, collected, has_next, pages, args.max_pages)
    log.info("%s: %s", state, detail)
    log.info("reachable: %d    unreachable: %d", reachable(total), unreachable(total))
    log.info("the REST twin of this stop is %s", truncation_signal("rest"))
    log.info("here it is %s", truncation_signal("graphql"))
    log.info("repair: %s", repair(state, total, args.type))

    print(json.dumps({
        "points_spent": pages * POINTS_PER_PAGE,
        "search": args.query,
        "type": args.type,
        "matches": total,
        "collected": collected,
        "pages_walked": pages,
        "has_next_page": has_next,
        "reachable": reachable(total),
        "unreachable": unreachable(total),
        "slices_needed": slices_needed(total),
        "typed_connection": typed_connection_for(args.type),
        "state": state,
        "detail": detail,
        "repair": repair(state, total, args.type),
    }, indent=2, default=str))
    return 1 if state == "ceiling-hit-silently" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-search-ceiling.mjs",
"js": '''/**
 * Show that GraphQL search stops at the same 1,000 results REST does.
 *
 * Read only, and queries only. GitHub's GraphQL endpoint takes its document in
 * the request body, so a read travels by POST there exactly as a write would.
 * The document is parsed first and anything containing a mutation or a
 * subscription is refused before a socket opens.
 *
 * The search connection is served by the same index as GET /search/* and
 * inherits the same ceiling of roughly 1,000 retrievable results. REST says so
 * with 422 Validation Failed on page 11; GraphQL just sets hasNextPage to
 * false and lets the walk finish normally.
 *
 * Environment:
 *   GITHUB_TOKEN        a token with read access to the GraphQL API
 *   GITHUB_SEARCH       the search string
 *   GITHUB_SEARCH_TYPE  ISSUE, REPOSITORY, USER or DISCUSSION
 *   GITHUB_MAX_PAGES    how many pages of 100 to walk
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-search-ceiling/1.0';

/** The retrievable-result ceiling on the search index, both APIs alike. */
export const SEARCH_RESULT_CEILING = 1000;

/** The largest page any GraphQL connection will serve. */
export const MAX_PAGE_SIZE = 100;

/** One search connection at first: 100 costs one point. */
export const POINTS_PER_PAGE = 1;

const SEARCH_QUERY = 'query($q: String!, $type: SearchType!, $after: String) {'
  + ' search(query: $q, type: $type, first: 100, after: $after) {'
  + ' issueCount repositoryCount userCount'
  + ' pageInfo { hasNextPage endCursor }'
  + ' nodes { __typename } } }';

/** Connections that answer an inventory question without the index. */
export const TYPED_CONNECTIONS = {
  ISSUE: 'repository.issues or repository.pullRequests',
  REPOSITORY: 'organization.repositories or user.repositories',
  USER: 'organization.membersWithRole',
  DISCUSSION: 'repository.discussions',
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

function asCount(total) {
  const n = Number(total);
  return Number.isFinite(n) ? Math.max(0, Math.trunc(n)) : 0;
}

/** How many of the matches can actually be paged to. Pure. */
export function reachable(total) {
  return Math.min(asCount(total), SEARCH_RESULT_CEILING);
}

/** How many matches exist that no cursor will ever reach. Pure. */
export function unreachable(total) {
  return Math.max(0, asCount(total) - SEARCH_RESULT_CEILING);
}

/** How many pages of this size fit under the ceiling. Pure. */
export function pagesToCeiling(pageSize = MAX_PAGE_SIZE) {
  const size = Math.min(Math.max(1, Math.trunc(Number(pageSize) || 1)), MAX_PAGE_SIZE);
  return Math.ceil(SEARCH_RESULT_CEILING / size);
}

/** How many under-the-ceiling slices a partition needs. Pure. */
export function slicesNeeded(total) {
  const n = asCount(total);
  return n ? Math.ceil(n / SEARCH_RESULT_CEILING) : 0;
}

/** The ceiling-free connection that answers the same question. Pure. */
export function typedConnectionFor(searchType) {
  const key = String(searchType ?? '').toUpperCase();
  return TYPED_CONNECTIONS[key] || 'the typed connection for this object type';
}

/** How each API announces the same ceiling. Pure. */
export function truncationSignal(protocol) {
  if (String(protocol).toLowerCase() === 'rest') {
    return '422 Validation Failed on page 11, with the message "Only the first '
      + '1000 search results are available".';
  }
  return 'no error at all. pageInfo.hasNextPage turns false and the walk '
    + 'terminates the way a complete walk terminates.';
}

/** How this walk ended, and whether that ending was honest. Pure. */
export function classifyWalk(total, collected, hasNextPage, pagesWalked, maxPages) {
  const matches = asCount(total);
  const got = asCount(collected);
  if (hasNextPage && pagesWalked >= maxPages) {
    return ['stopped-early-by-request', 'the walk stopped at the --max-pages '
      + 'limit with more pages available, so nothing about the ceiling is '
      + `proved yet. ${got} of ${matches} node(s) collected.`];
  }
  if (hasNextPage) {
    return ['still-paging', 'the connection still reports another page. Keep '
      + 'walking or raise --max-pages.'];
  }
  if (got >= SEARCH_RESULT_CEILING && matches > got) {
    return ['ceiling-hit-silently', `pagination stopped after ${got} node(s) `
      + `with the index reporting ${matches} match(es). No error was raised and `
      + 'hasNextPage simply turned false.'];
  }
  if (matches > got) {
    return ['truncated-early', `the walk ended with ${got} of ${matches} `
      + 'match(es) and below the ceiling, which is not this note: check for a '
      + 'timed-out search or a filter applied after the count.'];
  }
  return ['complete', `${got} node(s) collected against ${matches} match(es). `
    + 'This query is under the ceiling and the answer is whole.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, total, searchType) {
  if (state === 'ceiling-hit-silently') {
    return `for an inventory use the typed connection ${typedConnectionFor(searchType)}, `
      + `which has no ceiling. For a genuine search, partition into at least `
      + `${slicesNeeded(total)} slice(s) by created: date range and union them.`;
  }
  if (state === 'truncated-early') {
    return 'see /github/search-incomplete-results/ -- a search that ends below '
      + 'the ceiling ended for a different reason, and that one is not '
      + 'deterministic.';
  }
  if (state === 'still-paging') {
    return 'nothing yet. Walk to the end, or read issueCount on page one and '
      + `compare it against ${SEARCH_RESULT_CEILING}.`;
  }
  if (state === 'stopped-early-by-request') {
    return `raise --max-pages to at least ${pagesToCeiling()} to reach the `
      + 'ceiling, or trust issueCount, which already tells you.';
  }
  return 'request issueCount alongside nodes and refuse to publish a result set '
    + 'shorter than it without labelling it truncated.';
}

/** The most this run can spend against the hourly budget. Pure. */
export function pointCost(maxPages) {
  return asCount(maxPages) * POINTS_PER_PAGE;
}

/** The index's own count for this search type. Pure. */
export function matchCount(search, searchType) {
  if (!search || typeof search !== 'object') return 0;
  const key = { ISSUE: 'issueCount', REPOSITORY: 'repositoryCount', USER: 'userCount' }[
    String(searchType ?? '').toUpperCase()] || 'issueCount';
  return asCount(search[key]);
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
  const search = process.env.GITHUB_SEARCH;
  if (!token || !search) {
    console.error('set GITHUB_TOKEN (read-only is enough) and GITHUB_SEARCH');
    process.exitCode = 2;
    return;
  }
  const type = (process.env.GITHUB_SEARCH_TYPE || 'ISSUE').toUpperCase();
  const maxPages = Number(process.env.GITHUB_MAX_PAGES || 11);

  const whyNot = refusal(SEARCH_QUERY);
  if (whyNot) {
    console.error(`refusing to send: ${whyNot}`);
    process.exitCode = 2;
    return;
  }
  console.log(`point cost: up to ${pointCost(maxPages)} point(s) against the `
    + '5,000/hour GraphQL budget');

  let cursor = null;
  let collected = 0;
  let total = 0;
  let pages = 0;
  let hasNext = false;
  while (pages < maxPages) {
    // eslint-disable-next-line no-await-in-loop
    const { status, body } = await runQuery(token, SEARCH_QUERY,
      { q: search, type, after: cursor });
    if (!body || body.errors) {
      console.error(`the search itself failed: HTTP ${status} `
        + `${JSON.stringify((body || {}).errors || []).slice(0, 300)}`);
      process.exitCode = 2;
      return;
    }
    const node = ((body.data || {}).search) || {};
    const nodes = node.nodes || [];
    const info = node.pageInfo || {};
    pages += 1;
    collected += nodes.length;
    total = matchCount(node, type);
    hasNext = Boolean(info.hasNextPage);
    cursor = info.endCursor;
    console.log(`page ${pages}: ${nodes.length} node(s), collected=${collected}, `
      + `matches=${total}, hasNextPage=${hasNext ? 'yes' : 'no'}`);
    if (!hasNext) break;
  }

  const [state, detail] = classifyWalk(total, collected, hasNext, pages, maxPages);
  console.log(`${state}: ${detail}`);
  console.log(`reachable: ${reachable(total)}    unreachable: ${unreachable(total)}`);
  console.log(`the REST twin of this stop is ${truncationSignal('rest')}`);
  console.log(`here it is ${truncationSignal('graphql')}`);
  console.log(`repair: ${repair(state, total, type)}`);

  console.log(JSON.stringify({
    points_spent: pages * POINTS_PER_PAGE,
    search,
    type,
    matches: total,
    collected,
    pages_walked: pages,
    has_next_page: hasNext,
    reachable: reachable(total),
    unreachable: unreachable(total),
    slices_needed: slicesNeeded(total),
    typed_connection: typedConnectionFor(type),
    state,
    detail,
  }, null, 2));
  process.exitCode = state === 'ceiling-hit-silently' ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The interesting assertions are all about endings that look the same. A walk that collected 1,000 of 18,231 and a walk that collected 40 of 40 both finish with hasNextPage false, and the suite pins the classifier on exactly that pair before it checks anything else. Around it sit the arithmetic — reachable and unreachable halves, pages to the ceiling, slices for a partition — the typed connection each search type should have used instead, and the two truncation signals kept side by side so the REST wording and the GraphQL silence stay distinguishable. The refusal guard is tested last, on the document this script actually sends.",
"test_py_file": "test_github_graphql_search_ceiling.py",
"test_py": '''from github_graphql_search_ceiling import (
    MAX_PAGE_SIZE, SEARCH_RESULT_CEILING, classify_walk, match_count,
    operations, pages_to_ceiling, point_cost, reachable, refusal, repair,
    slices_needed, truncation_signal, typed_connection_for, unreachable,
)


def test_the_ceiling_is_a_property_of_the_index_not_the_page_size():
    assert SEARCH_RESULT_CEILING == 1000
    assert MAX_PAGE_SIZE == 100
    assert pages_to_ceiling(100) == 10
    assert pages_to_ceiling(30) == 34
    assert pages_to_ceiling(1) == 1000


def test_a_match_count_splits_into_a_reachable_and_an_unreachable_half():
    assert reachable(18231) == 1000
    assert unreachable(18231) == 17231
    assert reachable(400) == 400
    assert unreachable(400) == 0
    assert reachable(None) == 0
    assert unreachable("not a number") == 0


def test_the_ceiling_stop_and_a_complete_walk_are_the_same_shape():
    hit, detail = classify_walk(18231, 1000, False, 10, 11)
    done, _ = classify_walk(40, 40, False, 1, 11)
    assert hit == "ceiling-hit-silently"
    assert done == "complete"
    # Both ended with hasNextPage false and no error. That is the note.
    assert "No error was raised" in detail
    assert "18231" in detail


def test_a_walk_cut_short_by_the_operator_proves_nothing():
    state, detail = classify_walk(18231, 500, True, 5, 5)
    assert state == "stopped-early-by-request"
    assert "nothing about the ceiling is proved" in detail
    assert "at least 10" in repair(state, 18231, "ISSUE")


def test_a_walk_still_going_is_not_a_finding():
    state, _ = classify_walk(18231, 300, True, 3, 11)
    assert state == "still-paging"


def test_ending_below_the_ceiling_is_a_different_note():
    state, detail = classify_walk(900, 640, False, 7, 11)
    assert state == "truncated-early"
    assert "not this note" in detail
    assert "search-incomplete-results" in repair(state, 900, "ISSUE")


def test_the_repair_names_a_ceiling_free_connection_and_a_slice_count():
    fix = repair("ceiling-hit-silently", 18231, "ISSUE")
    assert "repository.issues" in fix
    assert "19 slice(s)" in fix
    assert "organization.repositories" in repair(
        "ceiling-hit-silently", 4000, "REPOSITORY")


def test_a_partition_needs_one_slice_per_thousand_matches():
    assert slices_needed(18231) == 19
    assert slices_needed(1000) == 1
    assert slices_needed(1001) == 2
    assert slices_needed(0) == 0


def test_every_search_type_has_a_connection_that_has_no_ceiling():
    assert "repository.issues" in typed_connection_for("ISSUE")
    assert "organization.repositories" in typed_connection_for("repository")
    assert "membersWithRole" in typed_connection_for("USER")
    assert "discussions" in typed_connection_for("DISCUSSION")
    assert typed_connection_for("SOMETHING_ELSE").startswith("the typed connection")


def test_the_two_apis_announce_the_same_ceiling_differently():
    assert "422" in truncation_signal("rest")
    assert "1000 search results" in truncation_signal("rest")
    assert "no error at all" in truncation_signal("graphql")
    assert "hasNextPage" in truncation_signal("graphql")


def test_the_count_field_follows_the_search_type():
    search = {"issueCount": 18231, "repositoryCount": 12, "userCount": 3}
    assert match_count(search, "ISSUE") == 18231
    assert match_count(search, "REPOSITORY") == 12
    assert match_count(search, "USER") == 3
    assert match_count(None, "ISSUE") == 0


def test_the_run_says_the_most_it_can_spend():
    assert point_cost(11) == 11
    assert point_cost(0) == 0
    assert point_cost(None) == 0


def test_the_document_this_script_sends_is_a_read():
    assert operations("query($q: String!) { search(query: $q, type: ISSUE, first: 100) { issueCount } }") == ["query"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal("subscription S { thing { id } }")
    assert refusal("") == "the document contains no operation to send."
''',
"test_js_file": "github-graphql-search-ceiling.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  MAX_PAGE_SIZE, SEARCH_RESULT_CEILING, classifyWalk, matchCount, operations,
  pagesToCeiling, pointCost, reachable, refusal, repair, slicesNeeded,
  truncationSignal, typedConnectionFor, unreachable,
} from './github-graphql-search-ceiling.mjs';

test('the ceiling is a property of the index not the page size', () => {
  assert.equal(SEARCH_RESULT_CEILING, 1000);
  assert.equal(MAX_PAGE_SIZE, 100);
  assert.equal(pagesToCeiling(100), 10);
  assert.equal(pagesToCeiling(30), 34);
  assert.equal(pagesToCeiling(1), 1000);
});

test('a match count splits into a reachable and an unreachable half', () => {
  assert.equal(reachable(18231), 1000);
  assert.equal(unreachable(18231), 17231);
  assert.equal(reachable(400), 400);
  assert.equal(unreachable(400), 0);
  assert.equal(reachable(null), 0);
  assert.equal(unreachable('not a number'), 0);
});

test('the ceiling stop and a complete walk are the same shape', () => {
  const [hit, detail] = classifyWalk(18231, 1000, false, 10, 11);
  const [done] = classifyWalk(40, 40, false, 1, 11);
  assert.equal(hit, 'ceiling-hit-silently');
  assert.equal(done, 'complete');
  assert.match(detail, /No error was raised/);
  assert.match(detail, /18231/);
});

test('a walk cut short by the operator proves nothing', () => {
  const [state, detail] = classifyWalk(18231, 500, true, 5, 5);
  assert.equal(state, 'stopped-early-by-request');
  assert.match(detail, /nothing about the ceiling is proved/);
  assert.match(repair(state, 18231, 'ISSUE'), /at least 10/);
});

test('a walk still going is not a finding', () => {
  assert.equal(classifyWalk(18231, 300, true, 3, 11)[0], 'still-paging');
});

test('ending below the ceiling is a different note', () => {
  const [state, detail] = classifyWalk(900, 640, false, 7, 11);
  assert.equal(state, 'truncated-early');
  assert.match(detail, /not this note/);
  assert.match(repair(state, 900, 'ISSUE'), /search-incomplete-results/);
});

test('the repair names a ceiling free connection and a slice count', () => {
  const fix = repair('ceiling-hit-silently', 18231, 'ISSUE');
  assert.match(fix, /repository\\.issues/);
  assert.match(fix, /19 slice\\(s\\)/);
  assert.match(repair('ceiling-hit-silently', 4000, 'REPOSITORY'),
    /organization\\.repositories/);
});

test('a partition needs one slice per thousand matches', () => {
  assert.equal(slicesNeeded(18231), 19);
  assert.equal(slicesNeeded(1000), 1);
  assert.equal(slicesNeeded(1001), 2);
  assert.equal(slicesNeeded(0), 0);
});

test('every search type has a connection that has no ceiling', () => {
  assert.match(typedConnectionFor('ISSUE'), /repository\\.issues/);
  assert.match(typedConnectionFor('repository'), /organization\\.repositories/);
  assert.match(typedConnectionFor('USER'), /membersWithRole/);
  assert.match(typedConnectionFor('DISCUSSION'), /discussions/);
  assert.ok(typedConnectionFor('SOMETHING_ELSE').startsWith('the typed connection'));
});

test('the two apis announce the same ceiling differently', () => {
  assert.match(truncationSignal('rest'), /422/);
  assert.match(truncationSignal('rest'), /1000 search results/);
  assert.match(truncationSignal('graphql'), /no error at all/);
  assert.match(truncationSignal('graphql'), /hasNextPage/);
});

test('the count field follows the search type', () => {
  const search = { issueCount: 18231, repositoryCount: 12, userCount: 3 };
  assert.equal(matchCount(search, 'ISSUE'), 18231);
  assert.equal(matchCount(search, 'REPOSITORY'), 12);
  assert.equal(matchCount(search, 'USER'), 3);
  assert.equal(matchCount(null, 'ISSUE'), 0);
});

test('the run says the most it can spend', () => {
  assert.equal(pointCost(11), 11);
  assert.equal(pointCost(0), 0);
  assert.equal(pointCost(null), 0);
});

test('the document this script sends is a read', () => {
  assert.deepEqual(
    operations('query($q: String!) { search(query: $q, type: ISSUE, first: 100) { issueCount } }'),
    ['query'],
  );
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.ok(refusal('subscription S { thing { id } }'));
  assert.equal(refusal(''), 'the document contains no operation to send.');
});
''',
"faq": [
 ("Is the GraphQL limit really the same 1,000, or is it just similar?",
  "It is the same limit, because it is the same index. Search on GitHub is a separate ranked-retrieval system from the object store, and both APIs are front ends to it; the cap is on how deep into a ranking you may page, not on how a request is framed. So no page size, cursor strategy or query rewrite gets past it, and the number does not differ between the two APIs. What differs is only the announcement: REST refuses the request that would cross the line, GraphQL serves you up to the line and stops."),
 ("How do I tell a truncated walk from a complete one?",
  "Compare the count the index reports against the number of nodes you actually collected. issueCount, repositoryCount and userCount describe the match set and keep reporting the full figure after the ceiling has cut you off, so a walk that ends with 1,000 nodes and a count of 18,231 is truncated and a walk that ends with 40 nodes and a count of 40 is complete. Both end with hasNextPage false and neither raises an error, which is why the comparison has to be explicit and cannot be inferred from how the loop terminated."),
 ("Can I get past it by sorting differently and paging from both ends?",
  "You can double your reach that way and it is a genuinely used trick: run the query ascending for the first 1,000 and descending for the last 1,000. It is still a partition, just an awkward one with two slices, and it breaks down the moment the match set exceeds 2,000 or the sort field has ties at the boundary. Slicing by created: date ranges scales to any size, is easy to reason about, and gives you slices you can re-run independently when one of them fails."),
 ("When should I use a typed connection instead?",
  "Whenever the question is an inventory rather than a ranking. repository.issues, repository.pullRequests, organization.repositories and repository.discussions read the object store directly, paginate with cursors and have no result ceiling at all, so &ldquo;every open issue in this repository&rdquo; is answerable in full and &ldquo;the thousand most relevant issues mentioning a phrase across the org&rdquo; is not. Search earns its place when the filter genuinely spans repositories or depends on full-text matching; for everything else it is a ceiling you did not have to accept."),
 ("Does each page of the walk cost a point?",
  "Yes. A search connection asking for first: 100 costs one point per request against the hourly GraphQL budget, so a full walk to the ceiling is ten or eleven points and a nineteen-slice partition run to completion is closer to two hundred. That is small against 5,000 an hour but not free, which is why this script prints the maximum it might spend before the first request and stops at --max-pages. Reading issueCount on page one costs one point and answers the question on its own."),
],
"related": [
 ("/github/search-1000-result-cap/", "The REST ceiling, which says so with a 422"),
 ("/github/search-incomplete-results/", "A search that timed out and returned part of an answer"),
 ("/github/link-header-not-followed/", "Only the first page of results is ever read"),
],
"citations": [CITE_GQL_QUERIES, CITE_REST_SEARCH, CITE_PAGINATION_GQL, CITE_GQL_SEARCH_SO],
},
{
"slug": "graphql-id-vs-databaseid",
"title": "GraphQL node ids get stored where REST ids are expected",
"description": "GraphQL id is an opaque node id, REST id is an integer, and both are called the id. Store whichever arrived and the join between the two returns zero rows.",
"h1": "GraphQL node ids get stored where REST ids are expected",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github graphql id vs databaseid",
             "github node_id vs id rest api",
             "github graphql global node id decode",
             "github api join graphql rest ids",
             "github databaseid missing graphql"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The importer that reads through REST and the sync job that reads through GraphQL have been running side by side for a year. Neither has ever thrown. The join between their two tables returns nothing, so somebody widens it to a left join, sees a wall of nulls, and starts checking timestamps. There is nothing wrong with the timestamps. One table has <code>1347</code> in its id column and the other has <code>MDU6SXNzdWUxMzQ3</code>, and those are the same issue.",
"short_answer": """<p>The two APIs give the same object two identifiers and each calls its own one <code>id</code>. GraphQL's <code>id</code> is the global node ID, an opaque string. REST's <code>id</code> is the numeric database ID. Neither is wrong and neither is the default in the other place: GraphQL exposes the number as <code>databaseId</code> and REST exposes the string as <code>node_id</code>, and you have to ask for them.</p>
<p>The crosswalk is exact in both directions. REST <code>node_id</code> equals GraphQL <code>id</code>; REST <code>id</code> equals GraphQL <code>databaseId</code>. Pick one key space per entity, request that field explicitly on whichever path does not return it by default, and migrate the rows you already have rather than joining across two spaces. And watch the third integer: an issue's <code>number</code> is not its <code>databaseId</code>, both are small integers, and they fit the same column perfectly.</p>""",
"problem": """<p>Nothing fails here, which is why it survives review. Both writers are correct in isolation: the REST importer stores the id its response gave it, the GraphQL sync stores the id its response gave it, and both of them wrote <code>id</code> in the field mapping because both responses call it that. The column is a string in one migration and a bigint in another, or it is a string in both and nobody notices that half of it is digits.</p>
<p>It is usually introduced by a rewrite rather than by a mistake. A service starts on REST, somebody adds a GraphQL path for a screen that needed three round trips, and the new path writes into the same tables. From that day the table holds two key spaces for one entity type, growing in whichever proportion the two code paths run. Deduplication stops working — the same issue is inserted twice, once under each key — and the duplicate count looks like a retry bug.</p>
<p>The discovery is nearly always a join returning zero rows, which is a hard bug to read because zero is not a suspicious number when you are expecting a small result. The alternative discovery is a lookup that 404s: somebody takes an id out of the store and puts it in a REST URL, GitHub answers 404, and now it looks like a permissions or an existence problem rather than a type error carried a hundred lines from where it was made.</p>""",
"why": """<p><strong>Two identifiers, one word.</strong> Every object in GitHub's GraphQL schema implements the <code>Node</code> interface, whose <code>id</code> is a global identifier unique across the whole API. REST predates it and identifies rows by an integer primary key, also called <code>id</code>. Both responses are self-consistent and neither warns you that the other exists. GraphQL adds <code>databaseId</code> for the integer; REST adds <code>node_id</code> for the global one. Those two extra fields are the entire bridge and both are easy to never notice.</p>
<p><strong>Old node ids are decodable and new ones are not.</strong> The legacy format is base64 of <code>&lt;length&gt;:&lt;Type&gt;&lt;databaseId&gt;</code>, so <code>MDU6SXNzdWUxMzQ3</code> decodes to <code>05:Issue1347</code> and yields the number directly. GitHub has moved to a new opaque format — <code>I_kwDO...</code> — that carries no recoverable database ID at all. So a migration cannot be done by decoding the ids you already hold; the ones minted since the change have to be re-fetched. Any code that parses a node ID to get a number is a bug waiting for the next object to be created.</p>
<p><strong>The third integer is the one that bites twice.</strong> An issue has a <code>number</code>, which is what appears in the URL and what REST paths address it by, and a <code>databaseId</code>, which is the global row key. Both are integers, both are small for a young repository, and they are not equal. <code>GET /repos/o/r/issues/1347</code> means issue <em>number</em> 1347, not the row whose id is 1347, so storing <code>databaseId</code> and then using it as a path segment produces a confident 404 or, much worse, the wrong issue.</p>
<p><strong>Each key space buys something.</strong> Node IDs are globally unique, are the only thing <code>node(id:)</code> accepts, and are what every GraphQL mutation wants as an input. Database IDs are what REST paths, webhook payloads and most exports carry. If your system is mostly REST, store <code>databaseId</code> and request it explicitly in every GraphQL query. If it is mostly GraphQL, store <code>node_id</code> from REST responses. What you cannot do is decide per code path.</p>
<p><strong><code>databaseId</code> is not on everything.</strong> Newer types added after the transition expose no <code>databaseId</code> at all, and on some types it is nullable. Where it is missing the node ID is the only key that exists, and a schema that requires an integer key has no row to write. The script says which of the two you got rather than reporting a null and letting you assume it was a permission problem, which is <a href="/github/graphql-partial-data-nulls/">a different note about a different null</a>.</p>
<p><strong>The API cannot see your schema.</strong> Nothing GitHub returns knows what your store holds. What a script can do is fetch one object down both paths and prove the crosswalk on live data, then take a sample of the ids you already have and tell you which key space each belongs to. A sample that contains both is the finding, and it is a finding you can get in one query and one REST call.</p>""",
"steps": [
 {"h": "Fetch one object down both paths",
  "body": """<p>One REST call and one GraphQL query, one point. The script asks REST for an issue and GraphQL for the same issue, then prints the four identifiers side by side. Seeing <code>node_id</code> and <code>id</code> match across the two responses, and <code>id</code> and <code>databaseId</code> match the other way, is what makes the crosswalk concrete rather than a rule you half remember.</p>"""},
 {"h": "Take a sample of what your store actually holds",
  "body": """<p>Paste a handful of ids from the column in question. The script classifies each one as a database ID, a node ID or unrecognisable, and reports the mix. A column containing both spaces for one entity type is the bug, and the proportion tells you which code path has been winning.</p>"""},
 {"h": "Watch the join fail and then watch it work",
  "body": """<p>Given two id lists the script counts how many rows join. Across two key spaces the answer is zero. Normalised to one space first, it is the number you expected. That before-and-after is worth more than any explanation, because zero-row joins are usually blamed on filters.</p>"""},
 {"h": "Find out which ids can be migrated offline",
  "body": """<p>Legacy node IDs decode to a type and a database ID with no network call at all, so those rows can be rewritten in place. New-format ids cannot, and the script counts them separately so the migration plan is honest about how many objects have to be re-fetched. Do not write a decoder that guesses at the new format.</p>"""},
 {"h": "Pin one key space and request it everywhere",
  "body": """<p>Add <code>databaseId</code> to every GraphQL selection or read <code>node_id</code> from every REST response, whichever direction your store points, and add the <code>number</code> field explicitly wherever a path is built so nobody reaches for the integer that happens to be nearby. The whole audit costs one point and one core request.</p>"""},
],
"verify": """<p>Once one key space is chosen and requested everywhere, the crosswalk is a check rather than a surprise.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_id_crosswalk.py \\
    --repo acme/monorepo --issue 1347 --ids MDU6SXNzdWUxMzQ3,1347,I_kwDOAbCdEf4AbCdE
# point cost: 1 point(s) against the 5,000/hour GraphQL budget, plus 1 core request
# rest:    id=1347  node_id=MDU6SXNzdWUxMzQ3  number=1347
# graphql: databaseId=1347  id=MDU6SXNzdWUxMzQ3  number=1347
# crosswalk-confirmed: REST node_id equals GraphQL id, and REST id equals
# GraphQL databaseId.
# number and databaseId are both integers and are equal by coincidence on this
# object; they are never the same field
#
# store sample: MDU6SXNzdWUxMzQ3 -> graphql-node-id, 1347 -> rest-database-id,
# I_kwDOAbCdEf4AbCdE -> graphql-node-id
# mixed-key-space: one entity type is keyed two ways in the same column: 1
# database id(s) and 2 node id(s).
# migratable offline: 1    needs re-fetching: 1    already numeric: 1
# repair: pick one key space, request databaseId in every GraphQL selection or
# node_id from every REST response, and migrate the rows you hold.</code></pre>""",
"code_intro": "Almost all of this is pure and runs without a token: which key space a string belongs to, what a legacy node ID decodes to, whether two objects crosswalk, how many rows a join across a mixed column recovers, and which ids can be migrated offline. The live part is deliberately tiny — one REST read and one GraphQL read of the same issue — because its only job is to demonstrate on real data what the pure functions assert about fixtures. The GraphQL document is parsed and refused if it is anything other than a read, as everywhere else in this section.",
"py_file": "github_graphql_id_crosswalk.py",
"py": '''"""Prove the crosswalk between GraphQL node ids and REST database ids.

Read only, and queries only. GitHub's GraphQL endpoint takes its document in
the request body, so a read travels by POST there exactly as a write would;
that is a transport detail, not a licence to write. The document is parsed
before anything is sent and refused if it contains a mutation or a
subscription.

GraphQL's id is an opaque global node ID and REST's id is a numeric database
ID, and each response calls its own one "id". The mapping is exact: REST
node_id equals GraphQL id, and REST id equals GraphQL databaseId. A store that
takes whichever field arrived ends up with two key spaces for one entity and a
join that returns nothing.

What this can and cannot see: nothing GitHub returns knows what your schema
holds. This fetches one object down both paths to prove the crosswalk, then
classifies a sample of ids you supply so you can see which spaces your own
column contains.

Environment:

    GITHUB_TOKEN    a token with read access to the repository
"""
import argparse
import base64
import binascii
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_id_crosswalk")

API = "https://api.github.com"
UA = "github-graphql-id-crosswalk/1.0"

# One repository plus one issue in a single document costs one point.
POINTS_PER_QUERY = 1

# The legacy global node ID is base64 of "<length>:<Type><databaseId>", so
# MDU6SXNzdWUxMzQ3 decodes to 05:Issue1347. The newer format is opaque and
# carries nothing recoverable, which is why decoding is never a migration plan.
LEGACY_DECODED = re.compile(r"^(\\d+):([A-Za-z]+)(\\d+)$")
NEW_NODE_ID = re.compile(r"^[A-Za-z]{1,4}_[A-Za-z0-9_-]{8,}$")
ALL_DIGITS = re.compile(r"^\\d+$")

ISSUE_QUERY = (
    "query($owner: String!, $name: String!, $number: Int!) {"
    " repository(owner: $owner, name: $name) {"
    " id databaseId"
    " issue(number: $number) { id databaseId number } } }"
)


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


def decode_legacy_node_id(value):
    """(type, database_id) for a legacy node ID, or None. Pure.

    The legacy format is base64 of "<length>:<Type><databaseId>" where the
    length is the length of the type name. Checking that length is what stops
    an ordinary base64 string being read as an identifier.
    """
    text = str(value or "")
    if not text or ALL_DIGITS.match(text):
        return None
    padded = text + "=" * (-len(text) % 4)
    try:
        raw = base64.b64decode(padded, validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    m = LEGACY_DECODED.match(raw)
    if not m:
        return None
    declared_len, type_name, database_id = m.group(1), m.group(2), m.group(3)
    if int(declared_len) != len(type_name):
        return None
    return (type_name, int(database_id))


def id_space(value):
    """Which key space a stored identifier belongs to. Pure.

    Returns "rest-database-id", "graphql-node-id" or "unknown". An integer or
    an all-digit string is a database ID; anything that decodes as a legacy
    node ID or matches the newer opaque shape is a node ID.
    """
    if isinstance(value, bool):
        return "unknown"
    if isinstance(value, int):
        return "rest-database-id"
    text = str(value or "").strip()
    if not text:
        return "unknown"
    if ALL_DIGITS.match(text):
        return "rest-database-id"
    if decode_legacy_node_id(text) or NEW_NODE_ID.match(text):
        return "graphql-node-id"
    return "unknown"


def to_database_id(value):
    """The numeric key for this identifier without a network call, or None. Pure.

    Legacy node IDs carry the number and can be migrated offline. New-format
    ones carry nothing and have to be re-fetched, which is the difference that
    decides how large the migration is.
    """
    space = id_space(value)
    if space == "rest-database-id":
        return int(str(value).strip())
    decoded = decode_legacy_node_id(value)
    return decoded[1] if decoded else None


def crosswalk(rest_object, graphql_object):
    """Compare one object fetched both ways. Pure. Returns a dict of facts."""
    rest_object = rest_object if isinstance(rest_object, dict) else {}
    graphql_object = graphql_object if isinstance(graphql_object, dict) else {}
    rest_id = rest_object.get("id")
    rest_node_id = rest_object.get("node_id")
    gql_id = graphql_object.get("id")
    gql_database_id = graphql_object.get("databaseId")
    return {
        "rest_id": rest_id,
        "rest_node_id": rest_node_id,
        "rest_number": rest_object.get("number"),
        "graphql_id": gql_id,
        "graphql_database_id": gql_database_id,
        "graphql_number": graphql_object.get("number"),
        "node_ids_match": bool(rest_node_id) and rest_node_id == gql_id,
        "database_ids_match": rest_id is not None and rest_id == gql_database_id,
        "database_id_present": gql_database_id is not None,
    }


def number_is_not_the_database_id(rest_object):
    """Whether an object's number and database id differ. Pure.

    They usually do, and both are integers, so a column typed for one accepts
    the other silently. Where they happen to be equal the warning still stands.
    """
    rest_object = rest_object if isinstance(rest_object, dict) else {}
    number, database_id = rest_object.get("number"), rest_object.get("id")
    if number is None or database_id is None:
        return None
    return number != database_id


def classify_pair(rest_object, graphql_object):
    """Judge one crosswalk. Pure. Returns (state, detail)."""
    facts = crosswalk(rest_object, graphql_object)
    if facts["rest_id"] is None or facts["graphql_id"] is None:
        return ("incomplete",
                "one of the two responses did not carry an identifier, so "
                "nothing can be compared.")
    if not facts["database_id_present"]:
        return ("database-id-absent",
                "this type exposes no databaseId, so the node ID is the only "
                "key it has. A store that requires an integer has no row to "
                "write for it.")
    if facts["node_ids_match"] and facts["database_ids_match"]:
        return ("crosswalk-confirmed",
                "REST node_id equals GraphQL id, and REST id equals GraphQL "
                "databaseId.")
    return ("crosswalk-broken",
            "the two responses disagree, which means they are not the same "
            "object. Check that the number and the query are pointing at one "
            "thing before reading anything into the ids.")


def classify_store(values):
    """Judge a sample of stored identifiers. Pure. Returns (state, detail)."""
    values = list(values or [])
    if not values:
        return ("no-sample", "no identifiers were supplied to classify.")
    counts = {"rest-database-id": 0, "graphql-node-id": 0, "unknown": 0}
    for v in values:
        counts[id_space(v)] += 1
    if counts["rest-database-id"] and counts["graphql-node-id"]:
        return ("mixed-key-space",
                "one entity type is keyed two ways in the same column: %d "
                "database id(s) and %d node id(s)."
                % (counts["rest-database-id"], counts["graphql-node-id"]))
    if counts["unknown"] == len(values):
        return ("unrecognised",
                "none of these look like either key space. They may be your "
                "own surrogate keys, which is fine and not this note.")
    if counts["graphql-node-id"]:
        return ("consistent-node-id",
                "every identifier is a global node ID. Read node_id from REST "
                "responses to keep it that way.")
    return ("consistent-database-id",
            "every identifier is a numeric database ID. Request databaseId "
            "explicitly in every GraphQL selection to keep it that way.")


def join_rows(left, right):
    """How many identifiers appear in both lists, compared as given. Pure."""
    return len({str(v) for v in (left or [])} & {str(v) for v in (right or [])})


def join_rows_normalised(left, right):
    """The same join after both sides are reduced to database ids. Pure.

    New-format node IDs drop out, because nothing local can turn one into a
    number. That is the honest answer and it is why the count can still be
    short after normalising.
    """
    def keys(values):
        out = set()
        for v in values or []:
            k = to_database_id(v)
            if k is not None:
                out.add(k)
        return out
    return len(keys(left) & keys(right))


def migration_split(values):
    """How many stored ids can be rewritten offline, and how many cannot. Pure."""
    offline, refetch, already = 0, 0, 0
    for v in values or []:
        space = id_space(v)
        if space == "rest-database-id":
            already += 1
        elif space == "graphql-node-id":
            if to_database_id(v) is None:
                refetch += 1
            else:
                offline += 1
    return {"already_numeric": already, "decodable_offline": offline,
            "needs_refetching": refetch}


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "mixed-key-space":
        return ("pick one key space, request databaseId in every GraphQL "
                "selection or node_id from every REST response, and migrate "
                "the rows you hold. Do not join across the two.")
    if state == "crosswalk-broken":
        return ("stop and confirm both calls address the same object. An "
                "issue's number is not its databaseId, and using one where "
                "the other belongs is the usual cause.")
    if state == "database-id-absent":
        return ("key this entity by its node ID. There is no integer to store "
                "and decoding the node ID will not produce one.")
    if state == "consistent-node-id":
        return ("nothing to migrate. Keep reading node_id on the REST side so "
                "a new code path cannot introduce the other space.")
    if state == "consistent-database-id":
        return ("nothing to migrate. Keep asking for databaseId on the GraphQL "
                "side so a new code path cannot introduce the other space.")
    if state == "unrecognised":
        return ("nothing here is a GitHub identifier. Point the sample at the "
                "column that holds them.")
    return ("fetch one object down both paths and compare the four fields "
            "before changing any schema.")


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
    ap.add_argument("--issue", type=int, required=True,
                    help="an issue NUMBER, which is not its database id")
    ap.add_argument("--ids", default="",
                    help="comma-separated identifiers from your own store")
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

    why_not = refusal(ISSUE_QUERY)
    if why_not:
        log.error("refusing to send: %s", why_not)
        return 2

    log.info("point cost: %d point(s) against the 5,000/hour GraphQL budget, "
             "plus 1 core request", POINTS_PER_QUERY)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    r = session.get("%s/repos/%s/%s/issues/%d" % (API, owner, name, args.issue),
                    timeout=30)
    rest_object = r.json() if r.status_code == 200 else {}
    if r.status_code != 200:
        log.error("REST read failed with HTTP %s; the crosswalk needs both "
                  "sides", r.status_code)

    status, body = run_query(session, ISSUE_QUERY,
                             {"owner": owner, "name": name, "number": args.issue})
    repository = ((body or {}).get("data") or {}).get("repository") or {}
    graphql_object = repository.get("issue") or {}
    if isinstance(body, dict) and body.get("errors"):
        log.error("the query carried errors: %s",
                  json.dumps(body["errors"])[:300])

    log.info("rest:    id=%s  node_id=%s  number=%s", rest_object.get("id"),
             rest_object.get("node_id"), rest_object.get("number"))
    log.info("graphql: databaseId=%s  id=%s  number=%s",
             graphql_object.get("databaseId"), graphql_object.get("id"),
             graphql_object.get("number"))

    state, detail = classify_pair(rest_object, graphql_object)
    log.info("%s: %s", state, detail)
    differs = number_is_not_the_database_id(rest_object)
    if differs is not None:
        log.info("number and databaseId are both integers and are %s on this "
                 "object; they are never the same field",
                 "different" if differs else "equal by coincidence")
    log.info("repair: %s", repair(state))

    sample = [v.strip() for v in args.ids.split(",") if v.strip()]
    store_state, store_detail = classify_store(sample)
    split = migration_split(sample)
    if sample:
        log.info("store sample: %s", ", ".join(
            "%s -> %s" % (v, id_space(v)) for v in sample))
        log.info("%s: %s", store_state, store_detail)
        log.info("migratable offline: %d    needs re-fetching: %d    already "
                 "numeric: %d", split["decodable_offline"],
                 split["needs_refetching"], split["already_numeric"])
        log.info("repair: %s", repair(store_state))

    print(json.dumps({
        "points_spent": POINTS_PER_QUERY,
        "http_status": status,
        "crosswalk": crosswalk(rest_object, graphql_object),
        "state": state,
        "detail": detail,
        "store_state": store_state,
        "store_detail": store_detail,
        "migration": split,
    }, indent=2, default=str))
    return 1 if state in ("crosswalk-broken",) or store_state == "mixed-key-space" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-id-crosswalk.mjs",
"js": '''/**
 * Prove the crosswalk between GraphQL node ids and REST database ids.
 *
 * Read only, and queries only. GitHub's GraphQL endpoint takes its document in
 * the request body, so a read travels by POST there exactly as a write would.
 * The document is parsed first and refused if it contains a mutation or a
 * subscription.
 *
 * GraphQL's id is an opaque global node ID and REST's id is a numeric database
 * ID, and each response calls its own one "id". REST node_id equals GraphQL
 * id; REST id equals GraphQL databaseId. A store that takes whichever field
 * arrived ends up with two key spaces for one entity.
 *
 * Environment:
 *   GITHUB_TOKEN   a token with read access to the repository
 *   GITHUB_REPO    owner/name
 *   GITHUB_ISSUE   an issue NUMBER, which is not its database id
 *   GITHUB_IDS     comma-separated identifiers from your own store
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-id-crosswalk/1.0';

/** One repository plus one issue in a single document costs one point. */
export const POINTS_PER_QUERY = 1;

const LEGACY_DECODED = /^(\\d+):([A-Za-z]+)(\\d+)$/;
const NEW_NODE_ID = /^[A-Za-z]{1,4}_[A-Za-z0-9_-]{8,}$/;
const ALL_DIGITS = /^\\d+$/;

const ISSUE_QUERY = 'query($owner: String!, $name: String!, $number: Int!) {'
  + ' repository(owner: $owner, name: $name) {'
  + ' id databaseId'
  + ' issue(number: $number) { id databaseId number } } }';

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

/** [type, databaseId] for a legacy node ID, or null. Pure. */
export function decodeLegacyNodeId(value) {
  const text = String(value ?? '');
  if (!text || ALL_DIGITS.test(text)) return null;
  const padded = text + '='.repeat((4 - (text.length % 4)) % 4);
  let raw;
  try {
    raw = Buffer.from(padded, 'base64').toString('utf8');
    if (Buffer.from(raw, 'utf8').toString('base64').replace(/=+$/, '')
        !== padded.replace(/=+$/, '')) return null;
  } catch { return null; }
  const m = LEGACY_DECODED.exec(raw);
  if (!m) return null;
  const [, declaredLen, typeName, databaseId] = m;
  if (Number(declaredLen) !== typeName.length) return null;
  return [typeName, Number(databaseId)];
}

/** Which key space a stored identifier belongs to. Pure. */
export function idSpace(value) {
  if (typeof value === 'boolean') return 'unknown';
  if (typeof value === 'number' && Number.isInteger(value)) return 'rest-database-id';
  const text = String(value ?? '').trim();
  if (!text) return 'unknown';
  if (ALL_DIGITS.test(text)) return 'rest-database-id';
  if (decodeLegacyNodeId(text) || NEW_NODE_ID.test(text)) return 'graphql-node-id';
  return 'unknown';
}

/** The numeric key for this identifier without a network call, or null. Pure. */
export function toDatabaseId(value) {
  const space = idSpace(value);
  if (space === 'rest-database-id') return Number(String(value).trim());
  const decoded = decodeLegacyNodeId(value);
  return decoded ? decoded[1] : null;
}

/** Compare one object fetched both ways. Pure. */
export function crosswalk(restObject, graphqlObject) {
  const rest = (restObject && typeof restObject === 'object') ? restObject : {};
  const gql = (graphqlObject && typeof graphqlObject === 'object') ? graphqlObject : {};
  const restId = rest.id ?? null;
  const restNodeId = rest.node_id ?? null;
  const gqlId = gql.id ?? null;
  const gqlDatabaseId = gql.databaseId ?? null;
  return {
    rest_id: restId,
    rest_node_id: restNodeId,
    rest_number: rest.number ?? null,
    graphql_id: gqlId,
    graphql_database_id: gqlDatabaseId,
    graphql_number: gql.number ?? null,
    node_ids_match: Boolean(restNodeId) && restNodeId === gqlId,
    database_ids_match: restId !== null && restId === gqlDatabaseId,
    database_id_present: gqlDatabaseId !== null,
  };
}

/** Whether an object's number and database id differ. Pure. */
export function numberIsNotTheDatabaseId(restObject) {
  const rest = (restObject && typeof restObject === 'object') ? restObject : {};
  const number = rest.number ?? null;
  const databaseId = rest.id ?? null;
  if (number === null || databaseId === null) return null;
  return number !== databaseId;
}

/** Judge one crosswalk. Pure. Returns [state, detail]. */
export function classifyPair(restObject, graphqlObject) {
  const facts = crosswalk(restObject, graphqlObject);
  if (facts.rest_id === null || facts.graphql_id === null) {
    return ['incomplete', 'one of the two responses did not carry an '
      + 'identifier, so nothing can be compared.'];
  }
  if (!facts.database_id_present) {
    return ['database-id-absent', 'this type exposes no databaseId, so the node '
      + 'ID is the only key it has. A store that requires an integer has no row '
      + 'to write for it.'];
  }
  if (facts.node_ids_match && facts.database_ids_match) {
    return ['crosswalk-confirmed', 'REST node_id equals GraphQL id, and REST id '
      + 'equals GraphQL databaseId.'];
  }
  return ['crosswalk-broken', 'the two responses disagree, which means they are '
    + 'not the same object. Check that the number and the query are pointing at '
    + 'one thing before reading anything into the ids.'];
}

/** Judge a sample of stored identifiers. Pure. Returns [state, detail]. */
export function classifyStore(values) {
  const list = Array.isArray(values) ? values : [];
  if (list.length === 0) return ['no-sample', 'no identifiers were supplied to classify.'];
  const counts = { 'rest-database-id': 0, 'graphql-node-id': 0, unknown: 0 };
  for (const v of list) counts[idSpace(v)] += 1;
  if (counts['rest-database-id'] && counts['graphql-node-id']) {
    return ['mixed-key-space', 'one entity type is keyed two ways in the same '
      + `column: ${counts['rest-database-id']} database id(s) and `
      + `${counts['graphql-node-id']} node id(s).`];
  }
  if (counts.unknown === list.length) {
    return ['unrecognised', 'none of these look like either key space. They may '
      + 'be your own surrogate keys, which is fine and not this note.'];
  }
  if (counts['graphql-node-id']) {
    return ['consistent-node-id', 'every identifier is a global node ID. Read '
      + 'node_id from REST responses to keep it that way.'];
  }
  return ['consistent-database-id', 'every identifier is a numeric database ID. '
    + 'Request databaseId explicitly in every GraphQL selection to keep it that way.'];
}

/** How many identifiers appear in both lists, compared as given. Pure. */
export function joinRows(left, right) {
  const a = new Set((left || []).map((v) => String(v)));
  const b = new Set((right || []).map((v) => String(v)));
  let n = 0;
  for (const v of a) if (b.has(v)) n += 1;
  return n;
}

/** The same join after both sides are reduced to database ids. Pure. */
export function joinRowsNormalised(left, right) {
  const keys = (values) => {
    const out = new Set();
    for (const v of values || []) {
      const k = toDatabaseId(v);
      if (k !== null) out.add(k);
    }
    return out;
  };
  const a = keys(left);
  const b = keys(right);
  let n = 0;
  for (const v of a) if (b.has(v)) n += 1;
  return n;
}

/** How many stored ids can be rewritten offline, and how many cannot. Pure. */
export function migrationSplit(values) {
  let already = 0;
  let offline = 0;
  let refetch = 0;
  for (const v of values || []) {
    const space = idSpace(v);
    if (space === 'rest-database-id') already += 1;
    else if (space === 'graphql-node-id') {
      if (toDatabaseId(v) === null) refetch += 1; else offline += 1;
    }
  }
  return { already_numeric: already, decodable_offline: offline, needs_refetching: refetch };
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'mixed-key-space') {
    return 'pick one key space, request databaseId in every GraphQL selection '
      + 'or node_id from every REST response, and migrate the rows you hold. '
      + 'Do not join across the two.';
  }
  if (state === 'crosswalk-broken') {
    return 'stop and confirm both calls address the same object. An issue\\'s '
      + 'number is not its databaseId, and using one where the other belongs '
      + 'is the usual cause.';
  }
  if (state === 'database-id-absent') {
    return 'key this entity by its node ID. There is no integer to store and '
      + 'decoding the node ID will not produce one.';
  }
  if (state === 'consistent-node-id') {
    return 'nothing to migrate. Keep reading node_id on the REST side so a new '
      + 'code path cannot introduce the other space.';
  }
  if (state === 'consistent-database-id') {
    return 'nothing to migrate. Keep asking for databaseId on the GraphQL side '
      + 'so a new code path cannot introduce the other space.';
  }
  if (state === 'unrecognised') {
    return 'nothing here is a GitHub identifier. Point the sample at the column '
      + 'that holds them.';
  }
  return 'fetch one object down both paths and compare the four fields before '
    + 'changing any schema.';
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
  const number = Number(process.env.GITHUB_ISSUE || 0);
  if (!token || !repo || !number) {
    console.error('set GITHUB_TOKEN (read-only is enough), GITHUB_REPO=owner/name '
      + 'and GITHUB_ISSUE=<issue number>');
    process.exitCode = 2;
    return;
  }
  const [owner, name] = repo.split('/');
  const whyNot = refusal(ISSUE_QUERY);
  if (whyNot) {
    console.error(`refusing to send: ${whyNot}`);
    process.exitCode = 2;
    return;
  }
  console.log(`point cost: ${POINTS_PER_QUERY} point(s) against the 5,000/hour `
    + 'GraphQL budget, plus 1 core request');

  const restRes = await fetch(`${API}/repos/${owner}/${name}/issues/${number}`,
    { headers: headers(token) });
  const restObject = restRes.ok ? await restRes.json() : {};

  const { body } = await runQuery(token, ISSUE_QUERY, { owner, name, number });
  const repository = ((body || {}).data || {}).repository || {};
  const graphqlObject = repository.issue || {};

  console.log(`rest:    id=${restObject.id} node_id=${restObject.node_id} `
    + `number=${restObject.number}`);
  console.log(`graphql: databaseId=${graphqlObject.databaseId} `
    + `id=${graphqlObject.id} number=${graphqlObject.number}`);

  const [state, detail] = classifyPair(restObject, graphqlObject);
  console.log(`${state}: ${detail}`);
  console.log(`repair: ${repair(state)}`);

  const sample = String(process.env.GITHUB_IDS || '').split(',')
    .map((v) => v.trim()).filter(Boolean);
  const [storeState, storeDetail] = classifyStore(sample);
  const split = migrationSplit(sample);
  if (sample.length) {
    console.log(sample.map((v) => `${v} -> ${idSpace(v)}`).join(', '));
    console.log(`${storeState}: ${storeDetail}`);
    console.log(`migratable offline: ${split.decodable_offline}    needs `
      + `re-fetching: ${split.needs_refetching}    already numeric: `
      + `${split.already_numeric}`);
    console.log(`repair: ${repair(storeState)}`);
  }

  console.log(JSON.stringify({
    points_spent: POINTS_PER_QUERY,
    crosswalk: crosswalk(restObject, graphqlObject),
    state,
    store_state: storeState,
    migration: split,
  }, null, 2));
  process.exitCode = (state === 'crosswalk-broken' || storeState === 'mixed-key-space') ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The decoder is the part worth pinning hardest, because it is the part somebody will be tempted to lean on: MDU6SXNzdWUxMzQ3 really does decode to Issue 1347, and the newer opaque format really does yield nothing, so a migration written around decoding covers only the rows minted before the change. Around it the suite asserts the crosswalk in both directions on recorded objects, the classifier that spots a column holding both key spaces, and the join that returns zero across them and the right number after normalising. The last group is the third integer: an issue's number and its databaseId, side by side, different, and both perfectly castable to the same column type.",
"test_py_file": "test_github_graphql_id_crosswalk.py",
"test_py": '''from github_graphql_id_crosswalk import (
    classify_pair, classify_store, crosswalk, decode_legacy_node_id, id_space,
    join_rows, join_rows_normalised, migration_split,
    number_is_not_the_database_id, operations, refusal, repair, to_database_id,
)

REST_ISSUE = {"id": 1347, "node_id": "MDU6SXNzdWUxMzQ3", "number": 1347,
              "title": "Found a bug"}
GQL_ISSUE = {"id": "MDU6SXNzdWUxMzQ3", "databaseId": 1347, "number": 1347}
NEW_STYLE = "I_kwDOAbCdEf4AbCdE"


def test_a_legacy_node_id_carries_the_database_id_inside_it():
    assert decode_legacy_node_id("MDU6SXNzdWUxMzQ3") == ("Issue", 1347)
    assert decode_legacy_node_id("MDU6SXNzdWUx") == ("Issue", 1)
    assert decode_legacy_node_id("MDEwOlJlcG9zaXRvcnkxMjk2MjY5") == ("Repository", 1296269)


def test_the_new_format_carries_nothing_and_must_be_refetched():
    assert decode_legacy_node_id(NEW_STYLE) is None
    assert id_space(NEW_STYLE) == "graphql-node-id"
    assert to_database_id(NEW_STYLE) is None


def test_an_ordinary_string_is_not_mistaken_for_an_identifier():
    assert decode_legacy_node_id("aGVsbG8gd29ybGQ=") is None
    assert decode_legacy_node_id("not base64 at all") is None
    assert decode_legacy_node_id("") is None
    assert decode_legacy_node_id("1347") is None


def test_each_identifier_is_placed_in_exactly_one_key_space():
    assert id_space(1347) == "rest-database-id"
    assert id_space("1347") == "rest-database-id"
    assert id_space("MDU6SXNzdWUxMzQ3") == "graphql-node-id"
    assert id_space("acme/monorepo#1347") == "unknown"
    assert id_space(None) == "unknown"
    assert id_space(True) == "unknown"


def test_the_crosswalk_holds_in_both_directions():
    facts = crosswalk(REST_ISSUE, GQL_ISSUE)
    assert facts["node_ids_match"]
    assert facts["database_ids_match"]
    state, detail = classify_pair(REST_ISSUE, GQL_ISSUE)
    assert state == "crosswalk-confirmed"
    assert "REST node_id equals GraphQL id" in detail


def test_two_different_objects_are_not_reported_as_a_key_problem():
    state, detail = classify_pair(REST_ISSUE, {"id": "MDU6SXNzdWUx", "databaseId": 1})
    assert state == "crosswalk-broken"
    assert "not the same object" in detail
    assert "number is not its databaseId" in repair(state)


def test_a_type_with_no_database_id_has_only_one_key():
    state, _ = classify_pair(REST_ISSUE, {"id": NEW_STYLE, "databaseId": None})
    assert state == "database-id-absent"
    assert "node ID" in repair(state)
    assert classify_pair({}, {})[0] == "incomplete"


def test_a_column_holding_both_spaces_is_the_finding():
    state, detail = classify_store(["1347", "MDU6SXNzdWUxMzQ3", NEW_STYLE])
    assert state == "mixed-key-space"
    assert "1 database id(s)" in detail
    assert "2 node id(s)" in detail
    assert "pick one key space" in repair(state)


def test_a_consistent_column_is_left_alone():
    assert classify_store(["1347", "1348"])[0] == "consistent-database-id"
    assert classify_store(["MDU6SXNzdWUxMzQ3", NEW_STYLE])[0] == "consistent-node-id"
    assert classify_store(["acme/monorepo#1"])[0] == "unrecognised"
    assert classify_store([])[0] == "no-sample"


def test_the_join_returns_nothing_across_two_key_spaces():
    rest_side = ["1347", "1348"]
    graphql_side = ["MDU6SXNzdWUxMzQ3", "MDU6SXNzdWUxMzQ4"]
    assert join_rows(rest_side, graphql_side) == 0
    assert join_rows_normalised(rest_side, graphql_side) == 2


def test_normalising_cannot_rescue_the_new_format():
    assert join_rows_normalised(["1347"], ["MDU6SXNzdWUxMzQ3"]) == 1
    assert join_rows_normalised(["1347"], [NEW_STYLE]) == 0


def test_the_migration_is_split_into_offline_and_refetch():
    split = migration_split(["1347", "MDU6SXNzdWUxMzQ3", NEW_STYLE, "junk"])
    assert split == {"already_numeric": 1, "decodable_offline": 1,
                     "needs_refetching": 1}


def test_the_number_is_a_third_integer_and_not_the_database_id():
    other = {"id": 2136843289, "node_id": "MDU6SXNzdWUx", "number": 1347}
    assert number_is_not_the_database_id(other) is True
    assert number_is_not_the_database_id(REST_ISSUE) is False
    assert number_is_not_the_database_id({}) is None
    # Both are integers, so a column typed for one silently accepts the other.
    assert id_space(other["number"]) == id_space(other["id"])


def test_the_document_this_script_sends_is_a_read():
    assert operations("query Q { repository(owner: \\"a\\", name: \\"b\\") { id databaseId } }") == ["query"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal("subscription S { thing { id } }")
    assert refusal("") == "the document contains no operation to send."
''',
"test_js_file": "github-graphql-id-crosswalk.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classifyPair, classifyStore, crosswalk, decodeLegacyNodeId, idSpace, joinRows,
  joinRowsNormalised, migrationSplit, numberIsNotTheDatabaseId, operations,
  refusal, repair, toDatabaseId,
} from './github-graphql-id-crosswalk.mjs';

const REST_ISSUE = {
  id: 1347, node_id: 'MDU6SXNzdWUxMzQ3', number: 1347, title: 'Found a bug',
};
const GQL_ISSUE = { id: 'MDU6SXNzdWUxMzQ3', databaseId: 1347, number: 1347 };
const NEW_STYLE = 'I_kwDOAbCdEf4AbCdE';

test('a legacy node id carries the database id inside it', () => {
  assert.deepEqual(decodeLegacyNodeId('MDU6SXNzdWUxMzQ3'), ['Issue', 1347]);
  assert.deepEqual(decodeLegacyNodeId('MDU6SXNzdWUx'), ['Issue', 1]);
  assert.deepEqual(decodeLegacyNodeId('MDEwOlJlcG9zaXRvcnkxMjk2MjY5'),
    ['Repository', 1296269]);
});

test('the new format carries nothing and must be refetched', () => {
  assert.equal(decodeLegacyNodeId(NEW_STYLE), null);
  assert.equal(idSpace(NEW_STYLE), 'graphql-node-id');
  assert.equal(toDatabaseId(NEW_STYLE), null);
});

test('an ordinary string is not mistaken for an identifier', () => {
  assert.equal(decodeLegacyNodeId('aGVsbG8gd29ybGQ='), null);
  assert.equal(decodeLegacyNodeId('not base64 at all'), null);
  assert.equal(decodeLegacyNodeId(''), null);
  assert.equal(decodeLegacyNodeId('1347'), null);
});

test('each identifier is placed in exactly one key space', () => {
  assert.equal(idSpace(1347), 'rest-database-id');
  assert.equal(idSpace('1347'), 'rest-database-id');
  assert.equal(idSpace('MDU6SXNzdWUxMzQ3'), 'graphql-node-id');
  assert.equal(idSpace('acme/monorepo#1347'), 'unknown');
  assert.equal(idSpace(null), 'unknown');
  assert.equal(idSpace(true), 'unknown');
});

test('the crosswalk holds in both directions', () => {
  const facts = crosswalk(REST_ISSUE, GQL_ISSUE);
  assert.ok(facts.node_ids_match);
  assert.ok(facts.database_ids_match);
  const [state, detail] = classifyPair(REST_ISSUE, GQL_ISSUE);
  assert.equal(state, 'crosswalk-confirmed');
  assert.match(detail, /REST node_id equals GraphQL id/);
});

test('two different objects are not reported as a key problem', () => {
  const [state, detail] = classifyPair(REST_ISSUE,
    { id: 'MDU6SXNzdWUx', databaseId: 1 });
  assert.equal(state, 'crosswalk-broken');
  assert.match(detail, /not the same object/);
  assert.match(repair(state), /number is not its databaseId/);
});

test('a type with no database id has only one key', () => {
  const [state] = classifyPair(REST_ISSUE, { id: NEW_STYLE, databaseId: null });
  assert.equal(state, 'database-id-absent');
  assert.match(repair(state), /node ID/);
  assert.equal(classifyPair({}, {})[0], 'incomplete');
});

test('a column holding both spaces is the finding', () => {
  const [state, detail] = classifyStore(['1347', 'MDU6SXNzdWUxMzQ3', NEW_STYLE]);
  assert.equal(state, 'mixed-key-space');
  assert.match(detail, /1 database id\\(s\\)/);
  assert.match(detail, /2 node id\\(s\\)/);
  assert.match(repair(state), /pick one key space/);
});

test('a consistent column is left alone', () => {
  assert.equal(classifyStore(['1347', '1348'])[0], 'consistent-database-id');
  assert.equal(classifyStore(['MDU6SXNzdWUxMzQ3', NEW_STYLE])[0], 'consistent-node-id');
  assert.equal(classifyStore(['acme/monorepo#1'])[0], 'unrecognised');
  assert.equal(classifyStore([])[0], 'no-sample');
});

test('the join returns nothing across two key spaces', () => {
  const restSide = ['1347', '1348'];
  const graphqlSide = ['MDU6SXNzdWUxMzQ3', 'MDU6SXNzdWUxMzQ4'];
  assert.equal(joinRows(restSide, graphqlSide), 0);
  assert.equal(joinRowsNormalised(restSide, graphqlSide), 2);
});

test('normalising cannot rescue the new format', () => {
  assert.equal(joinRowsNormalised(['1347'], ['MDU6SXNzdWUxMzQ3']), 1);
  assert.equal(joinRowsNormalised(['1347'], [NEW_STYLE]), 0);
});

test('the migration is split into offline and refetch', () => {
  assert.deepEqual(migrationSplit(['1347', 'MDU6SXNzdWUxMzQ3', NEW_STYLE, 'junk']),
    { already_numeric: 1, decodable_offline: 1, needs_refetching: 1 });
});

test('the number is a third integer and not the database id', () => {
  const other = { id: 2136843289, node_id: 'MDU6SXNzdWUx', number: 1347 };
  assert.equal(numberIsNotTheDatabaseId(other), true);
  assert.equal(numberIsNotTheDatabaseId(REST_ISSUE), false);
  assert.equal(numberIsNotTheDatabaseId({}), null);
  assert.equal(idSpace(other.number), idSpace(other.id));
});

test('the document this script sends is a read', () => {
  assert.deepEqual(
    operations('query Q { repository(owner: "a", name: "b") { id databaseId } }'),
    ['query'],
  );
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.ok(refusal('subscription S { thing { id } }'));
  assert.equal(refusal(''), 'the document contains no operation to send.');
});
''',
"faq": [
 ("Which one should I store?",
  "Whichever your system is mostly built on, and then everywhere. If most of your code paths are REST, or you consume webhook payloads, or you export to something that expects integers, store the database ID and add databaseId to every GraphQL selection you write. If you are mostly on GraphQL, or you call mutations, which take node IDs as inputs, store node_id from every REST response instead. The decision that causes this bug is not choosing wrong, it is choosing per code path, so write the choice down somewhere a reviewer will see it."),
 ("Can I convert one to the other locally?",
  "Only for the old ones. A legacy node ID is base64 of the type name and the database ID, so MDU6SXNzdWUxMzQ3 decodes to Issue 1347 with no network call and those rows can be migrated in place. GitHub's newer format is deliberately opaque and carries no recoverable number, so ids minted since that change have to be re-fetched from the API to learn their databaseId. Any decoder you write will therefore be correct on your historical rows and silently wrong on new ones, which is the worst possible failure mode; the script counts both groups so the migration plan can be sized honestly."),
 ("Why did my REST call 404 with a databaseId in the URL?",
  "Because REST addresses issues and pull requests by number, not by database ID. GET /repos/owner/repo/issues/1347 means the issue numbered 1347 in that repository, and issue numbers restart at 1 in every repository while database IDs are global and large. Passing a databaseId there asks for an issue number that usually does not exist, which is a 404, or that does exist and is a completely different issue, which is worse and will not raise anything. Request number explicitly wherever you build a path."),
 ("Is databaseId available on everything?",
  "No, and that is a real constraint rather than a permission problem. Types introduced after GitHub moved to opaque identifiers expose no databaseId at all, and on some types the field is nullable. Where it is absent, the node ID is the only identifier the object has, so a schema whose key column is an integer has nothing to write. The script names that case explicitly rather than reporting a null, because a null in a GraphQL response is otherwise ambiguous between an absent field and a withheld one, and the withheld kind is a different note."),
 ("Nothing is failing. Is this worth fixing?",
  "The failure mode is silence, so &ldquo;nothing is failing&rdquo; is not evidence. What it looks like in practice is a join that quietly returns fewer rows than it should, duplicate rows accumulating because deduplication compares two different key spaces, and counts that drift apart between two systems that are supposedly reading the same data. Take fifty ids out of the column and classify them; if they are all in one space you are fine and it costs a minute, and if they are not you have found the reason for a discrepancy somebody is probably already investigating."),
],
"related": [
 ("/github/graphql-partial-data-nulls/", "A null field that was withheld rather than empty"),
 ("/github/graphql-200-with-errors/", "A 200 that carries an errors array"),
 ("/github/repo-renamed-301-redirect/", "Identity that moves when a repository is renamed"),
],
"citations": [CITE_NODE_IDS, CITE_GQL_INTERFACES, CITE_GQL_MIGRATE, CITE_REST_ISSUES],
},
{
"slug": "resource-not-accessible-by-pat",
"title": "403 Resource not accessible by personal access token",
"description": "A fine-grained token carries permissions rather than scopes and sends no header saying which. Only the endpoint says what it wanted, and only on REST.",
"h1": "403 Resource not accessible by personal access token",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["resource not accessible by personal access token",
             "github fine grained pat 403",
             "github_pat_ token permissions missing",
             "x-accepted-github-permissions header",
             "github fine grained token no x-oauth-scopes"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The token was minted this morning with the permissions somebody carefully ticked, it reads the repository perfectly well, and one call comes back <code>403 {&quot;message&quot;: &quot;Resource not accessible by personal access token&quot;}</code>. The obvious next move is to look at what the token holds and compare it against what the endpoint wanted. Half of that is possible. The endpoint will tell you what it wanted. Nothing anywhere will tell you what the token holds.",
"short_answer": """<p>Fine-grained personal access tokens carry per-resource permissions — <code>Issues: Read</code>, <code>Contents: Read</code>, <code>Actions: Read</code> — rather than the coarse scopes a classic token carries. When one of those permissions is missing the response is <code>403</code> with the message <code>Resource not accessible by personal access token</code>, naming nothing.</p>
<p>There is exactly one readable half of the diff. The refusing response carries <code>x-accepted-github-permissions</code>, which names the permission and level the endpoint accepts, in the form <code>issues=read</code>. There is no counterpart header for what the token holds: a fine-grained token sends <strong>no</strong> <code>x-oauth-scopes</code> at all, and that absence is itself the reliable way to tell it apart from a classic token, which always sends the header even when it is empty. So the other half of the diff has to be measured — one cheap read per permission, sorted into granted, refused and ambiguous — and then the missing permission ticked on the token's settings page.</p>""",
"problem": """<p>Fine-grained tokens are the right thing to be using and this is the tax. A classic token is a blunt instrument you can at least inspect: every response tells you the scopes it carries, so the fix is a subtraction you can do in your head. A fine-grained token is precise, which is the point, and opaque, which is not something anybody mentions while recommending it.</p>
<p>What makes the 403 hard is that the token is obviously working. It authenticates. It reads the repository. Nine calls out of ten succeed. So the first hypothesis is never &ldquo;this token lacks a permission&rdquo;, it is that the endpoint is wrong, or the path is wrong, or the resource does not exist, and an hour goes into a call that was refused for a reason the message declined to state. When the same token is used from two services, one of which touches issues and one of which does not, the failure also looks environment-specific, which sends somebody into the deployment config.</p>
<p>The second trap is the settings page. Permissions were ticked when the token was created, and they look right when you go back and read them, because reading a list of permissions does not tell you which endpoint needed which one. <code>Contents: Read</code> feels like it should cover an issue — issues live in the repository — and it does not. And where the resource belongs to an organization rather than a repository, the token may also be waiting on an owner's approval, in which case every permission on the page is granted on paper and none of them is in effect.</p>""",
"why": """<p><strong>Permissions are not scopes and the header set proves it.</strong> A classic token or an OAuth token sends <code>x-oauth-scopes</code> on every authenticated response — sometimes an empty string, but the header is there — and the endpoint answers with <code>x-accepted-oauth-scopes</code>, so <a href="/github/missing-oauth-scope/">both halves of that diff arrive in one response</a>. A fine-grained token sends no <code>x-oauth-scopes</code> header whatsoever. That absence, alongside the <code>github_pat_</code> prefix, is how you identify what you are holding, and it is the reason this note needs a different technique rather than a different table.</p>
<p><strong>The endpoint still names what it wanted.</strong> <code>x-accepted-github-permissions</code> arrives on the refusing response and reads like <code>issues=read</code> or <code>contents=read;pull_requests=write</code>. A comma separates alternatives, any one of which is sufficient; a semicolon joins permissions that are all required together. It is the same header a GitHub App gets, which is why it is worth reading carefully rather than skimming for a word.</p>
<p><strong>The message names the actor, and that is the routing decision.</strong> &ldquo;Resource not accessible by personal access token&rdquo; is a fine-grained PAT. <a href="/github/app-permission-missing/">&ldquo;Resource not accessible by integration&rdquo; is a GitHub App installation token</a> and has a different repair, because an App's permissions <em>are</em> readable through <code>GET /app</code> and because adding one requires every installation to accept an upgrade. Confusing the two wastes an afternoon in the wrong settings page, so the script reads the actor out of the message before it does anything else.</p>
<p><strong>What the token holds can only be measured, not read.</strong> One cheap read per permission, against a repository you know exists: the repository itself for Metadata, the issues list for Issues, the pulls list for Pull requests, the workflows list for Actions. A 200 proves the permission is granted; a 403 with this message proves it is not. That matrix is the missing half of the diff, and it is worth keeping because it is also the fastest way to answer &ldquo;what is this token actually for&rdquo; six months later.</p>
<p><strong>A 404 in that matrix is not a no.</strong> GitHub answers 404 rather than 403 for resources a token cannot see at all, so a 404 in the middle of a probe run is ambiguous between a missing permission, a missing repository and a disabled feature. <a href="/github/404-masking-403/">Untangling that is its own note</a>; here the script marks the row ambiguous and refuses to guess, because a matrix that quietly converts 404 into &ldquo;not granted&rdquo; will send you to tick a permission that was never the problem.</p>
<p><strong>Through GraphQL the same refusal arrives with nothing attached.</strong> There is no status code to read — it is a 200 — and no <code>x-accepted-github-permissions</code> header on the response at all. The refusal is an entry in <code>errors</code> with a message that mentions the personal access token and a <code>path</code> pointing at the field. That is enough to know which field was refused and not enough to know which permission it wanted, so the technique is to find the REST endpoint that returns the same object and read the header off its refusal. The script does both in one run so the correspondence is visible.</p>
<p><strong>An organization-level refusal may not be about permissions at all.</strong> If every repository probe passes and only organization resources refuse, the likelier cause is that the token is waiting on an organization owner's approval, or that the organization restricts fine-grained tokens by policy. Ticking more permissions cannot fix either, so the script separates that shape rather than folding it into a permissions verdict.</p>""",
"steps": [
 {"h": "Identify the credential before diagnosing it",
  "body": """<p>One call to <code>GET /user</code>. The <code>github_pat_</code> prefix and the complete absence of an <code>x-oauth-scopes</code> header together say fine-grained, and the presence of that header — even empty — says classic. If the answer is classic, this is the wrong note and the script says so and points at the scope diff instead of running a probe matrix that does not apply.</p>"""},
 {"h": "Read x-accepted-github-permissions off the refusal itself",
  "body": """<p>Make the failing call again and read the header. It names the permission and level in fine-grained terms, with commas meaning alternatives and semicolons meaning conjunctions. This is the only authoritative statement of what the endpoint wanted, and it is worth quoting verbatim in the ticket rather than paraphrasing.</p>"""},
 {"h": "Measure what the token holds, one permission at a time",
  "body": """<p>The script runs one cheap read per permission and sorts each into granted, refused or ambiguous. Nothing here is a guess: a 200 is a grant, a 403 with this message is a refusal, and a 404 is neither, because a 404 can mean a resource that is not there. Five requests against a core budget of 5,000 an hour.</p>"""},
 {"h": "See the same refusal arrive through GraphQL with no header",
  "body": """<p>One query, one point. The refusal comes back as a 200 with an <code>errors</code> entry naming the personal access token and a <code>path</code> to the field, and with no <code>x-accepted-github-permissions</code> anywhere on the response. The script pairs it with the REST refusal so the field and the permission line up, which is the practical technique for diagnosing a GraphQL-only integration.</p>"""},
 {"h": "Tick exactly what the header named, then check for approval",
  "body": """<p>Edit the token's repository permissions to add the permission by name and no more. If the refusals are only on organization resources while every repository probe passes, stop and check whether the token is pending an owner's approval, because no permission you tick will take effect until it is granted.</p>"""},
],
"verify": """<p>Once the missing permission is added, the probe matrix answers the question the 403 would not.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_fine_grained_pat_probe.py \\
    --repo acme/monorepo
# cost: 6 core request(s) out of 5,000/hour, plus 1 GraphQL point
# credential: fine-grained personal access token
#   prefix github_pat_ and no x-oauth-scopes header on GET /user, which a
#   classic token always sends even when it is empty
#
# metadata       200  granted
# contents       200  granted
# issues         403  refused    x-accepted-github-permissions: issues=read
# pull_requests  200  granted
# actions        404  ambiguous  a 404 can hide a 403; see /github/404-masking-403/
#
# fine-grained-permission-missing: the endpoint accepts issues=read and this
# token does not hold it.
# graphql: HTTP 200, 1 refusal(s) naming the personal access token
#   path=repository.issues  Resource not accessible by personal access token
# through graphql the requirement lives nowhere on this response [...] make the
# equivalent REST call and read it off that refusal instead.
# repair: add issues=read to this token's repository permissions -- exactly
# what x-accepted-github-permissions named, and nothing else.</code></pre>""",
"code_intro": "Two things are being established and they need different evidence. What the endpoint wants is a header, so parsing it correctly matters: commas are alternatives and semicolons are conjunctions, and a parser that flattens them tells you to grant more than you need. What the token holds cannot be read at all, so it is measured, and the measurement has three outcomes rather than two because a 404 is not a no. Everything except the six requests is pure, including the credential identification, which is a fact about a prefix and a missing header.",
"py_file": "github_fine_grained_pat_probe.py",
"py": '''"""Work out which permission a fine-grained token is missing.

Read only. Every call here is a GET except the single GraphQL query, and the
GraphQL endpoint takes its document in the request body, so a read travels by
POST there exactly as a write would; that is a transport detail, not a licence
to write. The document is parsed first and refused if it contains a mutation or
a subscription.

A fine-grained personal access token carries per-resource permissions rather
than scopes. When one is missing the answer is 403 "Resource not accessible by
personal access token", which names nothing. The refusing response does carry
x-accepted-github-permissions, naming what the endpoint accepts, but there is
no header at all for what the token holds: fine-grained tokens send no
x-oauth-scopes, and that absence is how you tell one from a classic token.

So one half of the diff is read and the other half is measured, with one cheap
request per permission. A 200 is a grant and a 403 with this message is a
refusal; a 404 is neither, because GitHub hides 403s behind 404s.

Environment:

    GITHUB_TOKEN    the fine-grained token you are diagnosing
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_fine_grained_pat_probe")

API = "https://api.github.com"
UA = "github-fine-grained-pat-probe/1.0"

POINTS_PER_QUERY = 1

# Token prefixes GitHub documents. Only the prefix is ever printed; the token
# itself comes from the environment and never appears in output.
TOKEN_PREFIXES = [
    ("github_pat_", "fine-grained personal access token"),
    ("ghp_", "classic personal access token"),
    ("gho_", "OAuth user token"),
    ("ghu_", "GitHub App user-to-server token"),
    ("ghs_", "GitHub App installation token"),
    ("ghr_", "GitHub App refresh token"),
]

# One cheap read per fine-grained permission, all of them GETs that return at
# most one item. The permission name is the one shown on the token's settings
# page, so the repair can be followed without translation.
PROBES = [
    ("metadata", "/repos/{owner}/{repo}", "Metadata"),
    ("contents", "/repos/{owner}/{repo}/contents/", "Contents"),
    ("issues", "/repos/{owner}/{repo}/issues?per_page=1", "Issues"),
    ("pull_requests", "/repos/{owner}/{repo}/pulls?per_page=1", "Pull requests"),
    ("actions", "/repos/{owner}/{repo}/actions/workflows?per_page=1", "Actions"),
]

# The GraphQL twin of the issues probe, sent to show the same refusal arriving
# with no header attached to it.
ISSUES_QUERY = (
    "query($owner: String!, $name: String!) {"
    " repository(owner: $owner, name: $name) {"
    " issues(first: 1) { totalCount } } }"
)


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


def token_kind(token):
    """The credential type named by the token's prefix. Pure."""
    text = str(token or "")
    for prefix, label in TOKEN_PREFIXES:
        if text.startswith(prefix):
            return label
    return "unrecognised credential"


def token_prefix(token):
    """The prefix alone, safe to print. Pure."""
    text = str(token or "")
    for prefix, _label in TOKEN_PREFIXES:
        if text.startswith(prefix):
            return prefix
    return "none"


def scope_header_state(headers):
    """Whether x-oauth-scopes arrived, and empty or not. Pure.

    A classic or OAuth token always sends this header, even as an empty string
    when the token holds no scopes. A fine-grained token never sends it at all.
    Present-but-empty and absent therefore mean completely different things and
    are the one signal that separates the two credential families from the
    response alone.
    """
    if not isinstance(headers, dict):
        return "absent"
    for key, value in headers.items():
        if str(key).lower() == "x-oauth-scopes":
            return "present-empty" if str(value).strip() == "" else "present"
    return "absent"


def identify(token, headers):
    """What credential this is, from the prefix and the header. Pure.

    Returns (kind, detail). The two signals agreeing is worth stating, because
    a disagreement usually means the header was captured from a different call
    than the token was used on.
    """
    kind = token_kind(token)
    state = scope_header_state(headers)
    fine_grained = kind.startswith("fine-grained")
    if fine_grained and state == "absent":
        return (kind,
                "prefix %s and no x-oauth-scopes header, which a classic token "
                "always sends even when it is empty." % token_prefix(token))
    if fine_grained:
        return (kind,
                "prefix says fine-grained but an x-oauth-scopes header arrived, "
                "which fine-grained tokens do not send. Check that the header "
                "came from a call made with this token.")
    if state in ("present", "present-empty"):
        return (kind,
                "an x-oauth-scopes header arrived, so this credential carries "
                "scopes rather than fine-grained permissions.")
    return (kind, "no x-oauth-scopes header and no fine-grained prefix.")


def parse_accepted_permissions(value):
    """Parse x-accepted-github-permissions. Pure.

    Returns a list of alternatives, each a list of (permission, level) pairs
    that are required together. A comma separates alternatives, any one of
    which is sufficient; a semicolon joins permissions that are all required.
    Flattening the two is how somebody ends up granting more than the endpoint
    ever asked for.
    """
    out = []
    for alternative in str(value or "").split(","):
        pairs = []
        for clause in alternative.split(";"):
            clause = clause.strip()
            if not clause:
                continue
            name, _, level = clause.partition("=")
            pairs.append((name.strip(), level.strip() or "read"))
        if pairs:
            out.append(pairs)
    return out


def actor_from_message(message):
    """Which credential the refusal blames. Pure.

    The routing decision for the whole note: the same 403 body names the actor,
    and each actor has a different place to go and fix it.
    """
    text = str(message or "").lower()
    if "personal access token" in text:
        return "fine-grained-pat"
    if "by integration" in text:
        return "github-app"
    if "oauth app" in text or "oauth application" in text:
        return "oauth-app"
    return None


def grant_from_probe(status, message):
    """What one probe proves about one permission. Pure.

    Three outcomes, not two. A 404 proves nothing, because GitHub answers 404
    rather than 403 for resources a token cannot see, and a matrix that reads
    404 as "not granted" sends people to tick the wrong box.
    """
    try:
        code = int(status)
    except (TypeError, ValueError):
        return ("error", "no status to read.")
    if 200 <= code < 300:
        return ("granted", "the read succeeded, so this permission is held.")
    if code == 403 and actor_from_message(message) == "fine-grained-pat":
        return ("refused", "403 naming the personal access token, so this "
                           "permission is not held.")
    if code == 403:
        return ("refused-other", "403 that does not name a personal access "
                                 "token. Read the message: another actor or "
                                 "another rule refused this.")
    if code == 404:
        return ("ambiguous", "a 404 can hide a 403; see "
                             "/github/404-masking-403/ before concluding "
                             "anything from this row.")
    if code == 401:
        return ("unauthenticated", "the token itself was rejected, which is a "
                                   "credential problem rather than a "
                                   "permission one.")
    return ("error", "HTTP %s, which is neither a grant nor a refusal." % code)


def classify(status, message, headers, token, org_only=False):
    """Judge one refusal. Pure. Returns (state, detail)."""
    kind, _detail = identify(token, headers)
    actor = actor_from_message(message)
    try:
        code = int(status)
    except (TypeError, ValueError):
        code = 0
    if 200 <= code < 300:
        return ("clean", "this call was not refused.")
    if actor == "github-app":
        return ("not-this-note-app",
                "the message names an integration, so this is a GitHub App "
                "installation token and its permissions are readable through "
                "GET /app.")
    if actor == "oauth-app":
        return ("not-this-note-oauth-app",
                "the message names an OAuth App, so the organization is "
                "restricting the App rather than the token lacking a "
                "permission.")
    if code == 404:
        return ("ambiguous-404",
                "a 404 rather than a 403, which GitHub uses to avoid "
                "confirming that a private resource exists.")
    if actor == "fine-grained-pat" and org_only:
        return ("org-resource-refused",
                "every repository probe passed and only organization resources "
                "were refused, which is more often a pending approval or an "
                "organization token policy than a missing permission.")
    if actor == "fine-grained-pat":
        wanted = parse_accepted_permissions(
            (headers or {}).get("x-accepted-github-permissions", ""))
        named = " or ".join(
            ", ".join("%s=%s" % pair for pair in alternative)
            for alternative in wanted) or "nothing the response named"
        return ("fine-grained-permission-missing",
                "the endpoint accepts %s and this token does not hold it." % named)
    if not kind.startswith("fine-grained"):
        return ("not-this-note-classic",
                "this credential carries scopes rather than fine-grained "
                "permissions, so the two scope headers answer it directly.")
    return ("unclassified",
            "a refusal whose message names no actor. Log it verbatim rather "
            "than guessing which credential was blamed.")


def graphql_pat_refusals(body):
    """Errors in a GraphQL response that blame the personal access token. Pure.

    Returns a list of (path, message). The response carries no
    x-accepted-github-permissions header at all, so this identifies the field
    that was refused and nothing about the permission it wanted.
    """
    if not isinstance(body, dict):
        return []
    out = []
    for err in body.get("errors") or []:
        if not isinstance(err, dict):
            continue
        if actor_from_message(err.get("message")) == "fine-grained-pat":
            path = ".".join(str(p) for p in (err.get("path") or [])) or "(no path)"
            out.append((path, str(err.get("message") or "")))
    return out


def where_the_requirement_lives(protocol):
    """Where to read what the endpoint wanted, per API. Pure."""
    if str(protocol).lower() == "graphql":
        return ("nowhere on this response. GraphQL refusals carry no "
                "x-accepted-github-permissions header, so make the equivalent "
                "REST call and read it off that refusal instead.")
    return ("the x-accepted-github-permissions header on the refusing "
            "response itself.")


def missing_permissions(headers, grants):
    """Permissions the endpoint named that the probes show are not held. Pure."""
    wanted = parse_accepted_permissions(
        (headers or {}).get("x-accepted-github-permissions", ""))
    missing = []
    for alternative in wanted:
        for name, level in alternative:
            if grants.get(name) in ("refused", None):
                missing.append((name, level))
    return missing


def repair(state, headers=None):
    """The sentence a reader has to act on. Pure."""
    if state == "fine-grained-permission-missing":
        wanted = parse_accepted_permissions(
            (headers or {}).get("x-accepted-github-permissions", ""))
        named = ", ".join("%s=%s" % pair
                          for alternative in wanted for pair in alternative)
        return ("add %s to this token's repository permissions -- exactly what "
                "x-accepted-github-permissions named, and nothing else."
                % (named or "the permission the header names"))
    if state == "org-resource-refused":
        return ("check whether an organization owner still has to approve this "
                "token, and whether the organization allows fine-grained "
                "tokens at all. No permission you tick takes effect first.")
    if state == "not-this-note-app":
        return ("see /github/app-permission-missing/ -- an App's permissions "
                "are readable and adding one needs every installation to "
                "accept the upgrade.")
    if state == "not-this-note-classic":
        return ("see /github/missing-oauth-scope/ -- both halves of that diff "
                "arrive as headers on the same response.")
    if state == "ambiguous-404":
        return ("see /github/404-masking-403/ -- decide between missing and "
                "invisible before changing any permission.")
    if state == "clean":
        return ("nothing on this call. Run the probe matrix anyway if you want "
                "to know what the token can reach before it matters.")
    return ("record the status, the message and the "
            "x-accepted-github-permissions header verbatim; between them they "
            "name the actor and the requirement.")


def run_query(session, document, variables):
    """Send one query. Returns (status, body-or-None).

    A GraphQL query is a read; POST is only how the document reaches the
    endpoint, which is why the verb is written here beside the URL rather than
    hidden in a constant where it could be mistaken for a write path.
    """
    r = session.post(API + "/graphql",
                     json={"query": document, "variables": variables or {}},
                     timeout=30)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, None


def message_of(response):
    """The message field of an error body, or an empty string."""
    try:
        return str((response.json() or {}).get("message") or "")
    except ValueError:
        return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/name to probe")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (the token you are diagnosing)")
        return 2
    try:
        owner, repo = args.repo.split("/", 1)
    except ValueError:
        log.error("--repo takes owner/name")
        return 2

    why_not = refusal(ISSUES_QUERY)
    if why_not:
        log.error("refusing to send: %s", why_not)
        return 2

    log.info("cost: %d core request(s) out of 5,000/hour, plus %d GraphQL point",
             len(PROBES) + 1, POINTS_PER_QUERY)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    who = session.get(API + "/user", timeout=30)
    kind, detail = identify(token, dict(who.headers))
    log.info("credential: %s", kind)
    log.info("  %s", detail)

    grants, rows = {}, []
    refusal_headers, refusal_message, refusal_status = {}, "", 0
    for name, path, label in PROBES:
        r = session.get(API + path.format(owner=owner, repo=repo), timeout=30)
        msg = message_of(r) if r.status_code >= 400 else ""
        verdict, why = grant_from_probe(r.status_code, msg)
        grants[name] = verdict
        accepted = r.headers.get("x-accepted-github-permissions", "")
        if verdict == "refused" and not refusal_message:
            refusal_headers = dict(r.headers)
            refusal_message, refusal_status = msg, r.status_code
        log.info("%-14s %s  %-10s %s", name, r.status_code, verdict,
                 ("x-accepted-github-permissions: " + accepted) if accepted else why)
        rows.append({"permission": name, "settings_label": label,
                     "status": r.status_code, "verdict": verdict,
                     "accepted": accepted})

    state, why = classify(refusal_status, refusal_message, refusal_headers, token)
    log.info("%s: %s", state, why)
    log.info("the requirement lives in %s", where_the_requirement_lives("rest"))

    status, body = run_query(session, ISSUES_QUERY, {"owner": owner, "name": repo})
    gql = graphql_pat_refusals(body)
    log.info("graphql: HTTP %s, %d refusal(s) naming the personal access token",
             status, len(gql))
    for path, msg in gql:
        log.info("  path=%s  %s", path, msg)
    if gql:
        log.info("through graphql the requirement lives %s",
                 where_the_requirement_lives("graphql"))

    log.info("repair: %s", repair(state, refusal_headers))

    print(json.dumps({
        "credential": kind,
        "prefix": token_prefix(token),
        "scope_header": scope_header_state(dict(who.headers)),
        "probes": rows,
        "missing_permissions": missing_permissions(refusal_headers, grants),
        "graphql_refusals": gql,
        "state": state,
        "detail": why,
        "repair": repair(state, refusal_headers),
    }, indent=2, default=str))
    return 1 if state.startswith(("fine-grained", "org-resource")) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-fine-grained-pat-probe.mjs",
"js": '''/**
 * Work out which permission a fine-grained token is missing.
 *
 * Read only. Every call is a GET except the single GraphQL query, and the
 * GraphQL endpoint takes its document in the request body, so a read travels
 * by POST there exactly as a write would. The document is parsed first and
 * refused if it contains a mutation or a subscription.
 *
 * A fine-grained personal access token carries per-resource permissions rather
 * than scopes. The refusing response names what the endpoint accepts in
 * x-accepted-github-permissions, and nothing anywhere names what the token
 * holds: fine-grained tokens send no x-oauth-scopes at all. So one half of the
 * diff is read and the other is measured, one cheap request per permission.
 *
 * Environment:
 *   GITHUB_TOKEN   the fine-grained token you are diagnosing
 *   GITHUB_REPO    owner/name to probe
 */
const API = 'https://api.github.com';
const UA = 'github-fine-grained-pat-probe/1.0';

export const POINTS_PER_QUERY = 1;

/** Token prefixes GitHub documents. Only the prefix is ever printed. */
export const TOKEN_PREFIXES = [
  ['github_pat_', 'fine-grained personal access token'],
  ['ghp_', 'classic personal access token'],
  ['gho_', 'OAuth user token'],
  ['ghu_', 'GitHub App user-to-server token'],
  ['ghs_', 'GitHub App installation token'],
  ['ghr_', 'GitHub App refresh token'],
];

/** One cheap read per fine-grained permission. */
export const PROBES = [
  ['metadata', '/repos/{owner}/{repo}', 'Metadata'],
  ['contents', '/repos/{owner}/{repo}/contents/', 'Contents'],
  ['issues', '/repos/{owner}/{repo}/issues?per_page=1', 'Issues'],
  ['pull_requests', '/repos/{owner}/{repo}/pulls?per_page=1', 'Pull requests'],
  ['actions', '/repos/{owner}/{repo}/actions/workflows?per_page=1', 'Actions'],
];

const ISSUES_QUERY = 'query($owner: String!, $name: String!) {'
  + ' repository(owner: $owner, name: $name) {'
  + ' issues(first: 1) { totalCount } } }';

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

/** The credential type named by the token's prefix. Pure. */
export function tokenKind(token) {
  const text = String(token ?? '');
  for (const [prefix, label] of TOKEN_PREFIXES) {
    if (text.startsWith(prefix)) return label;
  }
  return 'unrecognised credential';
}

/** The prefix alone, safe to print. Pure. */
export function tokenPrefix(token) {
  const text = String(token ?? '');
  for (const [prefix] of TOKEN_PREFIXES) {
    if (text.startsWith(prefix)) return prefix;
  }
  return 'none';
}

/** Whether x-oauth-scopes arrived, and empty or not. Pure. */
export function scopeHeaderState(headers) {
  if (!headers || typeof headers !== 'object') return 'absent';
  for (const [key, value] of Object.entries(headers)) {
    if (String(key).toLowerCase() === 'x-oauth-scopes') {
      return String(value).trim() === '' ? 'present-empty' : 'present';
    }
  }
  return 'absent';
}

/** What credential this is, from the prefix and the header. Pure. */
export function identify(token, headers) {
  const kind = tokenKind(token);
  const state = scopeHeaderState(headers);
  const fineGrained = kind.startsWith('fine-grained');
  if (fineGrained && state === 'absent') {
    return [kind, `prefix ${tokenPrefix(token)} and no x-oauth-scopes header, `
      + 'which a classic token always sends even when it is empty.'];
  }
  if (fineGrained) {
    return [kind, 'prefix says fine-grained but an x-oauth-scopes header '
      + 'arrived, which fine-grained tokens do not send. Check that the header '
      + 'came from a call made with this token.'];
  }
  if (state === 'present' || state === 'present-empty') {
    return [kind, 'an x-oauth-scopes header arrived, so this credential carries '
      + 'scopes rather than fine-grained permissions.'];
  }
  return [kind, 'no x-oauth-scopes header and no fine-grained prefix.'];
}

/** Parse x-accepted-github-permissions into alternatives. Pure. */
export function parseAcceptedPermissions(value) {
  const out = [];
  for (const alternative of String(value ?? '').split(',')) {
    const pairs = [];
    for (const raw of alternative.split(';')) {
      const clause = raw.trim();
      if (!clause) continue;
      const idx = clause.indexOf('=');
      const name = idx < 0 ? clause : clause.slice(0, idx);
      const level = idx < 0 ? '' : clause.slice(idx + 1);
      pairs.push([name.trim(), level.trim() || 'read']);
    }
    if (pairs.length) out.push(pairs);
  }
  return out;
}

/** Which credential the refusal blames. Pure. */
export function actorFromMessage(message) {
  const text = String(message ?? '').toLowerCase();
  if (text.includes('personal access token')) return 'fine-grained-pat';
  if (text.includes('by integration')) return 'github-app';
  if (text.includes('oauth app') || text.includes('oauth application')) return 'oauth-app';
  return null;
}

/** What one probe proves about one permission. Pure. [verdict, why]. */
export function grantFromProbe(status, message) {
  const code = Number(status);
  if (!Number.isFinite(code) || status === null || status === '') {
    return ['error', 'no status to read.'];
  }
  if (code >= 200 && code < 300) {
    return ['granted', 'the read succeeded, so this permission is held.'];
  }
  if (code === 403 && actorFromMessage(message) === 'fine-grained-pat') {
    return ['refused', '403 naming the personal access token, so this '
      + 'permission is not held.'];
  }
  if (code === 403) {
    return ['refused-other', '403 that does not name a personal access token. '
      + 'Read the message: another actor or another rule refused this.'];
  }
  if (code === 404) {
    return ['ambiguous', 'a 404 can hide a 403; see /github/404-masking-403/ '
      + 'before concluding anything from this row.'];
  }
  if (code === 401) {
    return ['unauthenticated', 'the token itself was rejected, which is a '
      + 'credential problem rather than a permission one.'];
  }
  return ['error', `HTTP ${code}, which is neither a grant nor a refusal.`];
}

/** Judge one refusal. Pure. Returns [state, detail]. */
export function classify(status, message, headers, token, orgOnly = false) {
  const [kind] = identify(token, headers);
  const actor = actorFromMessage(message);
  const code = Number(status) || 0;
  if (code >= 200 && code < 300) return ['clean', 'this call was not refused.'];
  if (actor === 'github-app') {
    return ['not-this-note-app', 'the message names an integration, so this is '
      + 'a GitHub App installation token and its permissions are readable '
      + 'through GET /app.'];
  }
  if (actor === 'oauth-app') {
    return ['not-this-note-oauth-app', 'the message names an OAuth App, so the '
      + 'organization is restricting the App rather than the token lacking a '
      + 'permission.'];
  }
  if (code === 404) {
    return ['ambiguous-404', 'a 404 rather than a 403, which GitHub uses to '
      + 'avoid confirming that a private resource exists.'];
  }
  if (actor === 'fine-grained-pat' && orgOnly) {
    return ['org-resource-refused', 'every repository probe passed and only '
      + 'organization resources were refused, which is more often a pending '
      + 'approval or an organization token policy than a missing permission.'];
  }
  if (actor === 'fine-grained-pat') {
    const wanted = parseAcceptedPermissions(
      (headers || {})['x-accepted-github-permissions'] || '');
    const named = wanted
      .map((alt) => alt.map(([n, l]) => `${n}=${l}`).join(', '))
      .join(' or ') || 'nothing the response named';
    return ['fine-grained-permission-missing',
      `the endpoint accepts ${named} and this token does not hold it.`];
  }
  if (!kind.startsWith('fine-grained')) {
    return ['not-this-note-classic', 'this credential carries scopes rather '
      + 'than fine-grained permissions, so the two scope headers answer it '
      + 'directly.'];
  }
  return ['unclassified', 'a refusal whose message names no actor. Log it '
    + 'verbatim rather than guessing which credential was blamed.'];
}

/** Errors in a GraphQL response that blame the personal access token. Pure. */
export function graphqlPatRefusals(body) {
  if (!body || typeof body !== 'object' || !Array.isArray(body.errors)) return [];
  const out = [];
  for (const err of body.errors) {
    if (!err || typeof err !== 'object') continue;
    if (actorFromMessage(err.message) === 'fine-grained-pat') {
      const path = (err.path || []).map((p) => String(p)).join('.') || '(no path)';
      out.push([path, String(err.message ?? '')]);
    }
  }
  return out;
}

/** Where to read what the endpoint wanted, per API. Pure. */
export function whereTheRequirementLives(protocol) {
  if (String(protocol).toLowerCase() === 'graphql') {
    return 'nowhere on this response. GraphQL refusals carry no '
      + 'x-accepted-github-permissions header, so make the equivalent REST call '
      + 'and read it off that refusal instead.';
  }
  return 'the x-accepted-github-permissions header on the refusing response itself.';
}

/** Permissions the endpoint named that the probes show are not held. Pure. */
export function missingPermissions(headers, grants) {
  const wanted = parseAcceptedPermissions(
    (headers || {})['x-accepted-github-permissions'] || '');
  const missing = [];
  for (const alternative of wanted) {
    for (const [name, level] of alternative) {
      const held = (grants || {})[name];
      if (held === 'refused' || held === undefined) missing.push([name, level]);
    }
  }
  return missing;
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, headers = null) {
  if (state === 'fine-grained-permission-missing') {
    const wanted = parseAcceptedPermissions(
      (headers || {})['x-accepted-github-permissions'] || '');
    const named = wanted.flat().map(([n, l]) => `${n}=${l}`).join(', ');
    return `add ${named || 'the permission the header names'} to this token's `
      + 'repository permissions -- exactly what x-accepted-github-permissions '
      + 'named, and nothing else.';
  }
  if (state === 'org-resource-refused') {
    return 'check whether an organization owner still has to approve this '
      + 'token, and whether the organization allows fine-grained tokens at all. '
      + 'No permission you tick takes effect first.';
  }
  if (state === 'not-this-note-app') {
    return 'see /github/app-permission-missing/ -- an App\\'s permissions are '
      + 'readable and adding one needs every installation to accept the upgrade.';
  }
  if (state === 'not-this-note-classic') {
    return 'see /github/missing-oauth-scope/ -- both halves of that diff arrive '
      + 'as headers on the same response.';
  }
  if (state === 'ambiguous-404') {
    return 'see /github/404-masking-403/ -- decide between missing and '
      + 'invisible before changing any permission.';
  }
  if (state === 'clean') {
    return 'nothing on this call. Run the probe matrix anyway if you want to '
      + 'know what the token can reach before it matters.';
  }
  return 'record the status, the message and the x-accepted-github-permissions '
    + 'header verbatim; between them they name the actor and the requirement.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'Content-Type': 'application/json',
    'User-Agent': UA,
  };
}

function headerObject(res) {
  const out = {};
  res.headers.forEach((value, key) => { out[key.toLowerCase()] = value; });
  return out;
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
    console.error('set GITHUB_TOKEN (the token you are diagnosing) and GITHUB_REPO=owner/name');
    process.exitCode = 2;
    return;
  }
  const [owner, name] = repo.split('/');
  const whyNot = refusal(ISSUES_QUERY);
  if (whyNot) {
    console.error(`refusing to send: ${whyNot}`);
    process.exitCode = 2;
    return;
  }
  console.log(`cost: ${PROBES.length + 1} core request(s) out of 5,000/hour, `
    + `plus ${POINTS_PER_QUERY} GraphQL point`);

  const who = await fetch(`${API}/user`, { headers: headers(token) });
  const [kind, detail] = identify(token, headerObject(who));
  console.log(`credential: ${kind}`);
  console.log(`  ${detail}`);

  const grants = {};
  const rows = [];
  let refusalHeaders = {};
  let refusalMessage = '';
  let refusalStatus = 0;
  for (const [permission, path, label] of PROBES) {
    const url = API + path.replace('{owner}', owner).replace('{repo}', name);
    // eslint-disable-next-line no-await-in-loop
    const res = await fetch(url, { headers: headers(token) });
    let message = '';
    if (res.status >= 400) {
      // eslint-disable-next-line no-await-in-loop
      try { message = String(((await res.json()) || {}).message || ''); } catch { message = ''; }
    }
    const [verdict, why] = grantFromProbe(res.status, message);
    grants[permission] = verdict;
    const all = headerObject(res);
    const accepted = all['x-accepted-github-permissions'] || '';
    if (verdict === 'refused' && !refusalMessage) {
      refusalHeaders = all;
      refusalMessage = message;
      refusalStatus = res.status;
    }
    console.log(`${permission.padEnd(14)} ${res.status}  ${verdict.padEnd(10)} `
      + `${accepted ? `x-accepted-github-permissions: ${accepted}` : why}`);
    rows.push({ permission, settings_label: label, status: res.status, verdict, accepted });
  }

  const [state, why] = classify(refusalStatus, refusalMessage, refusalHeaders, token);
  console.log(`${state}: ${why}`);
  console.log(`the requirement lives in ${whereTheRequirementLives('rest')}`);

  const { status, body } = await runQuery(token, ISSUES_QUERY, { owner, name });
  const gql = graphqlPatRefusals(body);
  console.log(`graphql: HTTP ${status}, ${gql.length} refusal(s) naming the `
    + 'personal access token');
  for (const [path, message] of gql) console.log(`  path=${path}  ${message}`);
  if (gql.length) {
    console.log(`through graphql the requirement lives ${whereTheRequirementLives('graphql')}`);
  }
  console.log(`repair: ${repair(state, refusalHeaders)}`);

  console.log(JSON.stringify({
    credential: kind,
    prefix: tokenPrefix(token),
    probes: rows,
    missing_permissions: missingPermissions(refusalHeaders, grants),
    graphql_refusals: gql,
    state,
    detail: why,
  }, null, 2));
  process.exitCode = state.startsWith('fine-grained') || state.startsWith('org-resource') ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The two assertions that carry the note are about absence. A fine-grained token is identified by the fact that no scope header arrived, and an empty scope header is asserted to mean the opposite of a missing one, because that is the single response-level signal separating the two credential families. After that: the actor read out of the message, which routes three different 403s to three different notes; the permission header parsed with commas as alternatives and semicolons as conjunctions rather than flattened into one list; the three-outcome probe verdict, with a 404 refusing to become a no; and the GraphQL refusal, which is recognisable by its message and carries no header at all. Tokens in the fixtures are obviously fake and short.",
"test_py_file": "test_github_fine_grained_pat_probe.py",
"test_py": '''from github_fine_grained_pat_probe import (
    actor_from_message, classify, grant_from_probe, graphql_pat_refusals,
    identify, missing_permissions, operations, parse_accepted_permissions,
    refusal, repair, scope_header_state, token_kind, token_prefix,
    where_the_requirement_lives,
)

# Obviously fake, and short enough that nobody could mistake one for a secret.
FG = "github_pat_FAKE"
CLASSIC = "ghp_FAKE"
APP = "ghs_FAKE"

REFUSED = {"x-accepted-github-permissions": "issues=read"}
PAT_403 = "Resource not accessible by personal access token"
APP_403 = "Resource not accessible by integration"


def test_a_fine_grained_token_is_known_by_a_header_that_is_not_there():
    kind, detail = identify(FG, {"x-github-api-version-selected": "2022-11-28"})
    assert kind == "fine-grained personal access token"
    assert "no x-oauth-scopes header" in detail
    assert token_prefix(FG) == "github_pat_"


def test_an_empty_scope_header_is_the_opposite_of_a_missing_one():
    assert scope_header_state({"x-oauth-scopes": ""}) == "present-empty"
    assert scope_header_state({"X-OAuth-Scopes": "repo"}) == "present"
    assert scope_header_state({"x-github-request-id": "abc"}) == "absent"
    assert scope_header_state(None) == "absent"
    # A classic token with no scopes still sends the header, so present-empty
    # identifies a classic token just as firmly as a populated one does.
    kind, _ = identify(CLASSIC, {"x-oauth-scopes": ""})
    assert kind == "classic personal access token"


def test_every_documented_prefix_is_named():
    assert token_kind(FG).startswith("fine-grained")
    assert token_kind(CLASSIC).startswith("classic")
    assert token_kind(APP) == "GitHub App installation token"
    assert token_kind("nonsense") == "unrecognised credential"
    assert token_prefix("nonsense") == "none"


def test_the_message_names_the_actor_and_routes_the_repair():
    assert actor_from_message(PAT_403) == "fine-grained-pat"
    assert actor_from_message(APP_403) == "github-app"
    assert actor_from_message("Although you appear to have the correct "
                              "authorization credentials, the OAuth App is "
                              "restricted") == "oauth-app"
    assert actor_from_message("Not Found") is None


def test_an_app_refusal_is_handed_to_the_app_note():
    state, _ = classify(403, APP_403, {}, APP)
    assert state == "not-this-note-app"
    assert "app-permission-missing" in repair(state)


def test_a_classic_token_is_handed_to_the_scope_note():
    state, _ = classify(403, "Must have admin rights to Repository.",
                        {"x-oauth-scopes": "public_repo"}, CLASSIC)
    assert state == "not-this-note-classic"
    assert "missing-oauth-scope" in repair(state)


def test_the_fine_grained_refusal_names_what_the_endpoint_accepts():
    state, detail = classify(403, PAT_403, REFUSED, FG)
    assert state == "fine-grained-permission-missing"
    assert "issues=read" in detail
    assert "issues=read" in repair(state, REFUSED)


def test_an_organization_only_refusal_is_not_a_missing_permission():
    state, detail = classify(403, PAT_403, REFUSED, FG, org_only=True)
    assert state == "org-resource-refused"
    assert "approval" in detail
    assert "approve this token" in repair(state)


def test_commas_are_alternatives_and_semicolons_are_requirements():
    assert parse_accepted_permissions("issues=read") == [[("issues", "read")]]
    assert parse_accepted_permissions("issues=read,pull_requests=read") == [
        [("issues", "read")], [("pull_requests", "read")]]
    assert parse_accepted_permissions("contents=read;pull_requests=write") == [
        [("contents", "read"), ("pull_requests", "write")]]
    assert parse_accepted_permissions("metadata") == [[("metadata", "read")]]
    assert parse_accepted_permissions("") == []


def test_a_probe_has_three_outcomes_because_a_404_is_not_a_no():
    assert grant_from_probe(200, "")[0] == "granted"
    assert grant_from_probe(403, PAT_403)[0] == "refused"
    assert grant_from_probe(403, APP_403)[0] == "refused-other"
    assert grant_from_probe(401, "Bad credentials")[0] == "unauthenticated"
    verdict, why = grant_from_probe(404, "Not Found")
    assert verdict == "ambiguous"
    assert "404-masking-403" in why
    assert grant_from_probe(None, "")[0] == "error"


def test_a_404_in_the_matrix_is_never_reported_as_a_refusal():
    state, _ = classify(404, "Not Found", {}, FG)
    assert state == "ambiguous-404"
    assert "404-masking-403" in repair(state)


def test_the_missing_permission_is_the_named_one_the_probes_refused():
    grants = {"metadata": "granted", "issues": "refused"}
    assert missing_permissions(REFUSED, grants) == [("issues", "read")]
    assert missing_permissions(REFUSED, {"issues": "granted"}) == []
    assert missing_permissions({}, grants) == []


def test_the_same_refusal_through_graphql_carries_no_header():
    body = {"data": {"repository": None},
            "errors": [{"type": "FORBIDDEN", "path": ["repository", "issues"],
                        "message": PAT_403},
                       {"type": "NOT_FOUND", "message": "Could not resolve"}]}
    found = graphql_pat_refusals(body)
    assert found == [("repository.issues", PAT_403)]
    assert graphql_pat_refusals({"data": {}}) == []
    assert "no x-accepted-github-permissions header" in where_the_requirement_lives("graphql")
    assert "x-accepted-github-permissions header" in where_the_requirement_lives("rest")


def test_the_document_this_script_sends_is_a_read():
    assert operations("query Q { repository(owner: \\"a\\", name: \\"b\\") { issues(first: 1) { totalCount } } }") == ["query"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal("subscription S { thing { id } }")
    assert refusal("") == "the document contains no operation to send."
''',
"test_js_file": "github-fine-grained-pat-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  actorFromMessage, classify, grantFromProbe, graphqlPatRefusals, identify,
  missingPermissions, operations, parseAcceptedPermissions, refusal, repair,
  scopeHeaderState, tokenKind, tokenPrefix, whereTheRequirementLives,
} from './github-fine-grained-pat-probe.mjs';

// Obviously fake, and short enough that nobody could mistake one for a secret.
const FG = 'github_pat_FAKE';
const CLASSIC = 'ghp_FAKE';
const APP = 'ghs_FAKE';

const REFUSED = { 'x-accepted-github-permissions': 'issues=read' };
const PAT_403 = 'Resource not accessible by personal access token';
const APP_403 = 'Resource not accessible by integration';

test('a fine grained token is known by a header that is not there', () => {
  const [kind, detail] = identify(FG, { 'x-github-api-version-selected': '2022-11-28' });
  assert.equal(kind, 'fine-grained personal access token');
  assert.match(detail, /no x-oauth-scopes header/);
  assert.equal(tokenPrefix(FG), 'github_pat_');
});

test('an empty scope header is the opposite of a missing one', () => {
  assert.equal(scopeHeaderState({ 'x-oauth-scopes': '' }), 'present-empty');
  assert.equal(scopeHeaderState({ 'X-OAuth-Scopes': 'repo' }), 'present');
  assert.equal(scopeHeaderState({ 'x-github-request-id': 'abc' }), 'absent');
  assert.equal(scopeHeaderState(null), 'absent');
  assert.equal(identify(CLASSIC, { 'x-oauth-scopes': '' })[0],
    'classic personal access token');
});

test('every documented prefix is named', () => {
  assert.ok(tokenKind(FG).startsWith('fine-grained'));
  assert.ok(tokenKind(CLASSIC).startsWith('classic'));
  assert.equal(tokenKind(APP), 'GitHub App installation token');
  assert.equal(tokenKind('nonsense'), 'unrecognised credential');
  assert.equal(tokenPrefix('nonsense'), 'none');
});

test('the message names the actor and routes the repair', () => {
  assert.equal(actorFromMessage(PAT_403), 'fine-grained-pat');
  assert.equal(actorFromMessage(APP_403), 'github-app');
  assert.equal(actorFromMessage('Although you appear to have the correct '
    + 'authorization credentials, the OAuth App is restricted'), 'oauth-app');
  assert.equal(actorFromMessage('Not Found'), null);
});

test('an app refusal is handed to the app note', () => {
  const [state] = classify(403, APP_403, {}, APP);
  assert.equal(state, 'not-this-note-app');
  assert.match(repair(state), /app-permission-missing/);
});

test('a classic token is handed to the scope note', () => {
  const [state] = classify(403, 'Must have admin rights to Repository.',
    { 'x-oauth-scopes': 'public_repo' }, CLASSIC);
  assert.equal(state, 'not-this-note-classic');
  assert.match(repair(state), /missing-oauth-scope/);
});

test('the fine grained refusal names what the endpoint accepts', () => {
  const [state, detail] = classify(403, PAT_403, REFUSED, FG);
  assert.equal(state, 'fine-grained-permission-missing');
  assert.match(detail, /issues=read/);
  assert.match(repair(state, REFUSED), /issues=read/);
});

test('an organization only refusal is not a missing permission', () => {
  const [state, detail] = classify(403, PAT_403, REFUSED, FG, true);
  assert.equal(state, 'org-resource-refused');
  assert.match(detail, /approval/);
  assert.match(repair(state), /approve this token/);
});

test('commas are alternatives and semicolons are requirements', () => {
  assert.deepEqual(parseAcceptedPermissions('issues=read'), [[['issues', 'read']]]);
  assert.deepEqual(parseAcceptedPermissions('issues=read,pull_requests=read'),
    [[['issues', 'read']], [['pull_requests', 'read']]]);
  assert.deepEqual(parseAcceptedPermissions('contents=read;pull_requests=write'),
    [[['contents', 'read'], ['pull_requests', 'write']]]);
  assert.deepEqual(parseAcceptedPermissions('metadata'), [[['metadata', 'read']]]);
  assert.deepEqual(parseAcceptedPermissions(''), []);
});

test('a probe has three outcomes because a 404 is not a no', () => {
  assert.equal(grantFromProbe(200, '')[0], 'granted');
  assert.equal(grantFromProbe(403, PAT_403)[0], 'refused');
  assert.equal(grantFromProbe(403, APP_403)[0], 'refused-other');
  assert.equal(grantFromProbe(401, 'Bad credentials')[0], 'unauthenticated');
  const [verdict, why] = grantFromProbe(404, 'Not Found');
  assert.equal(verdict, 'ambiguous');
  assert.match(why, /404-masking-403/);
  assert.equal(grantFromProbe(null, '')[0], 'error');
});

test('a 404 in the matrix is never reported as a refusal', () => {
  const [state] = classify(404, 'Not Found', {}, FG);
  assert.equal(state, 'ambiguous-404');
  assert.match(repair(state), /404-masking-403/);
});

test('the missing permission is the named one the probes refused', () => {
  const grants = { metadata: 'granted', issues: 'refused' };
  assert.deepEqual(missingPermissions(REFUSED, grants), [['issues', 'read']]);
  assert.deepEqual(missingPermissions(REFUSED, { issues: 'granted' }), []);
  assert.deepEqual(missingPermissions({}, grants), []);
});

test('the same refusal through graphql carries no header', () => {
  const body = {
    data: { repository: null },
    errors: [
      { type: 'FORBIDDEN', path: ['repository', 'issues'], message: PAT_403 },
      { type: 'NOT_FOUND', message: 'Could not resolve' },
    ],
  };
  assert.deepEqual(graphqlPatRefusals(body), [['repository.issues', PAT_403]]);
  assert.deepEqual(graphqlPatRefusals({ data: {} }), []);
  assert.match(whereTheRequirementLives('graphql'),
    /no x-accepted-github-permissions header/);
  assert.match(whereTheRequirementLives('rest'),
    /x-accepted-github-permissions header/);
});

test('the document this script sends is a read', () => {
  assert.deepEqual(
    operations('query Q { repository(owner: "a", name: "b") { issues(first: 1) { totalCount } } }'),
    ['query'],
  );
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.ok(refusal('subscription S { thing { id } }'));
  assert.equal(refusal(''), 'the document contains no operation to send.');
});
''',
"faq": [
 ("How do I tell a fine-grained token from a classic one at runtime?",
  "Two signals that agree. The prefix is the obvious one: github_pat_ for fine-grained, ghp_ for classic, gho_ for an OAuth user token, ghs_ for a GitHub App installation token. The response-level signal is stronger, because it survives a token being passed through something that trims it: a classic or OAuth token gets x-oauth-scopes on every authenticated response, even as an empty string when it holds no scopes, and a fine-grained token never gets that header at all. An empty header and an absent header therefore mean opposite things, and code that checks truthiness rather than presence gets this backwards."),
 ("Why does GitHub not just say which permission is missing?",
  "It does say what the endpoint accepts — that is x-accepted-github-permissions, and it arrives on the refusing response — but it deliberately never reports what a token holds. Publishing a credential's full grant set on every response would hand an attacker who captured one response a complete map of what the stolen token can reach. The consequence for you is that the diff has one readable side, so the other side has to be measured with cheap reads against a repository you know exists."),
 ("Is this the same as the error a GitHub App gets?",
  "Same shape, different actor, different repair. An App gets &ldquo;Resource not accessible by integration&rdquo; and its permissions are readable through GET /app under the App's JWT, so that diff can be done from two responses without probing. Adding a permission to an App also requires every existing installation to accept the upgrade, which has no counterpart here: editing a fine-grained token's permissions takes effect immediately for you, and only needs approval when the token reaches organization-owned resources. Read the word in the message before deciding which page to open."),
 ("The token has every permission I ticked and organization resources still 403.",
  "Then the likely answer is not a permission at all. Organizations can require an owner to approve any fine-grained token that touches their resources, and can also refuse fine-grained tokens by policy. Until that approval lands, the token holds its permissions on paper and none of them in effect, so the shape you see is every personal and repository read succeeding while every organization read fails. Ticking more boxes changes nothing; the script separates that case so you go and find an owner rather than re-minting the token twice."),
 ("Does the refusal look different through GraphQL?",
  "Completely, and that is worth knowing before you debug a GraphQL-only integration. There is no 403 to catch, because the response is a 200 with the failure written into the errors array, and there is no x-accepted-github-permissions header anywhere on the response, so the one authoritative statement of what was required is simply absent. What you get is a message naming the personal access token and a path pointing at the field that was refused. The technique is to take that path, find the REST endpoint that returns the same object, call it, and read the header off its refusal."),
],
"related": [
 ("/github/missing-oauth-scope/", "The classic-token version, where both headers arrive"),
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
 ("/github/404-masking-403/", "A permission error disguised as 404 Not Found"),
],
"citations": [CITE_PAT_SO, CITE_FG_PERMS, CITE_MANAGE_PATS, CITE_APP_PERMS],
},
]
