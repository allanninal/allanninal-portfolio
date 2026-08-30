#!/usr/bin/env python3
"""/github/ field notes, batch S — the writing.

The section's second four GraphQL notes. The first batch owned the response
envelope: the status line, the errors array, the point budget and the node
ceiling. These four own the query document and the price of running it, and each
one had to be kept off the others' ground.

The first owns one argument. Every connection caps `first` and `last` at 100,
and going over is rejected during validation rather than during execution, which
is a different failure from anything in batch R: the body has no `data` key at
all, the entries in `errors` carry no `type`, and nothing is billed because
nothing ran. The interesting part is not the ceiling, which is a single number
anybody can memorise, but that the value being compared against it is very often
not written in the document. It arrives through a variable default or through
the variables map, so a scan for literals over 100 reports a clean document that
fails on every call.

The second owns the cursors nobody followed. An outer connection paginates
correctly and every inner connection restarts at the beginning of each outer
page, so the truncation is per parent and multiplies. The section already
publishes the REST version of losing pages, and this is deliberately not that:
there is no `Link` header here, no `rel="last"` to read a true total from, and
the evidence is `totalCount` sitting inside each node next to a shorter list of
`nodes`. The script also reports the connections that asked for neither
`totalCount` nor `pageInfo`, because those are the ones that cannot be checked
at all.

The third owns the number on the bill. Batch R measures how much budget is left
and converts it into queries; this one goes the other way and asks whether the
price of a single query shape is what its author believes. It predicts the cost
from the text, injects `rateLimit` into the document to measure the real one,
and reports the disagreement, plus the drift against a recorded baseline, which
is what catches the deploy that quietly doubled a dashboard query.

The fourth owns the ten seconds. A query that runs too long is killed and
charged, and it is charged more than it would have cost had it finished. That is
measured by reading the GraphQL bucket either side of the call, which is free,
and by taking a second pair of readings with nothing in between so the drain
from every other process holding the same token can be subtracted. The bucket is
shared and never attributable, so the measurement is reported with that caveat
rather than as a clean number.

Queries only, never mutations. The GraphQL endpoint is reached by POST for reads
as well as writes because the document travels in the body, so every script here
parses its document and refuses to open a socket if any top-level operation is a
mutation or a subscription, exactly as batch R does. Every one of them prints
what it will spend before it spends it, and two of the four spend nothing at all
unless you ask them to send.
"""

CITE_GQL_RESOURCE = ("Resource limitations — GitHub GraphQL API",
                     "https://docs.github.com/en/graphql/overview/resource-limitations")
CITE_GQL_RATE = ("Rate limits and node limits for the GraphQL API — GitHub Docs",
                 "https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api")
CITE_GQL_PAGINATION = ("Using pagination in the GraphQL API — GitHub Docs",
                       "https://docs.github.com/en/graphql/guides/using-pagination-in-the-graphql-api")
CITE_GQL_FORMING = ("Forming calls with GraphQL — GitHub Docs",
                    "https://docs.github.com/en/graphql/guides/forming-calls-with-graphql")
CITE_GQL_GUIDE = ("Using the GraphQL API — GitHub Docs",
                  "https://docs.github.com/en/graphql/guides/using-the-graphql-api")
CITE_SPEC_VALIDATION = ("GraphQL specification: Validation",
                        "https://spec.graphql.org/October2021/#sec-Validation")
CITE_SPEC_VALUES = ("GraphQL specification: Values of Correct Type",
                    "https://spec.graphql.org/October2021/#sec-Values-of-Correct-Type")
CITE_SPEC_RESPONSE = ("GraphQL specification: Response Format",
                      "https://spec.graphql.org/October2021/#sec-Response-Format")
CITE_RELAY_CONNECTIONS = ("GraphQL Cursor Connections Specification",
                          "https://relay.dev/graphql/connections.htm")
CITE_REST_PAGINATION = ("Using pagination in the REST API — GitHub Docs",
                        "https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api")
CITE_REST_RATE_LIMIT = ("Rate limit — GitHub REST API",
                        "https://docs.github.com/en/rest/rate-limit/rate-limit")

GUIDES = [

{
"slug": "graphql-first-over-100",
"title": "A GraphQL connection asks for first: 500 and is rejected",
"description": "Every GraphQL connection caps first and last at 100. Unlike REST, which clamps per_page silently, the query is rejected before it runs and returns no data key.",
"h1": "A GraphQL connection asks for first: 500 and is rejected",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github graphql first 100 limit",
             "graphql argument first has an invalid value",
             "github graphql first must be between 1 and 100",
             "github graphql more than 100 results",
             "graphql first last maximum github api"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The query is fifteen lines long and it has never run once. The body comes back with <code>Argument 'first' on Field 'issues' has an invalid value (500)</code>, there is no <code>data</code> key in it at all, and the 500 is not written anywhere in the document — it is the default on a variable somebody added a year ago. The code was ported from a REST client where <code>per_page=500</code> quietly became 100 and the job kept working, so nobody ever learned that the number was wrong.",
"short_answer": """<p>Every connection in GitHub's GraphQL schema caps <code>first</code> and <code>last</code> at 100. Ask for more and the query is rejected during <strong>validation</strong>, before a single field is resolved. That is a different response shape from the failures batch R covers: there is no <code>data</code> key in the body at all, the entries in <code>errors</code> have no <code>type</code> field, and nothing is billed against your point budget, because nothing ran.</p>
<p>Set <code>first: 100</code> and paginate with <code>after: $cursor</code> until <code>pageInfo.hasNextPage</code> is false. The ceiling is not adjustable and there is no header, parameter or preview that raises it. The part worth checking with a script is not the number but where the number comes from: a value over 100 arriving through a variable default or through the variables map is invisible to a text search for <code>first: 500</code>, and that is the version of this bug that survives review.</p>""",
"problem": """<p>This one is imported rather than invented. The REST API accepts <code>per_page=500</code>, silently gives you 100, and carries on, so a client written against REST has usually learned that oversized page sizes are harmless and that asking for more is a free optimisation. That habit ports across to GraphQL along with the code, and GraphQL does not share it. It refuses.</p>
<p>The refusal is at least loud, which is why this note is short on symptoms and long on where the number hides. In the simple case somebody wrote <code>first: 500</code>, the error names the field and the argument, and the fix takes ninety seconds. The case that eats an afternoon is the one where the document says <code>first: $first</code> and looks entirely reasonable, and the offending value is either a default in the operation's variable definitions or a number computed by the caller and passed in the variables map. Grepping the repository for <code>first: 5</code> finds nothing.</p>
<p>The computed version is the worst of the three, because it is intermittent by construction. A page size derived from a batch size, a config value or a leftover count works for months while the input is small and fails the first time somebody asks for a big report. It then fails identically on retry, which sends people looking for a rate limit or an outage, because a failure that reproduces exactly usually is one of those.</p>""",
"why": """<p><strong>100 is a schema constant, not a policy.</strong> The ceiling on <code>first</code> and <code>last</code> is part of the connection contract in GitHub's schema and applies to every connection in it. There is no scope, header, preview or Enterprise plan that moves it. Anything you read that suggests raising it is describing a different API.</p>
<p><strong>Rejection happens at validation, and validation is not execution.</strong> The GraphQL specification says that when a request fails before execution begins, the response must not contain a <code>data</code> entry at all. So the body you get here has <code>errors</code> and nothing else — not <code>data: null</code>, which is what an execution failure produces, but no <code>data</code> key. A client written to read <code>body.data.repository</code> throws on the missing key rather than on a null, which is a different stack trace pointing at a different line.</p>
<p><strong>It costs nothing, and that is a real consolation.</strong> The query never ran, so no points are deducted for it. That makes this the cheapest possible failure and it also means a retry loop stuck on it is not draining the budget, unlike almost every other failure in this section. It is still an infinite loop, but it is a free one.</p>
<p><strong>The value is not always in the document.</strong> A slicing argument can be written as a literal, as a variable with a default in the operation definition, or as a variable supplied at call time. Only the first is visible to a text search, and the third is not knowable from the repository at all without the caller. Any check worth running has to resolve all three, which is what this script does: it reads the literals, reads the defaults out of the variable definitions, and takes the variables map you actually send.</p>
<p><strong>This is not the node limit.</strong> A query can sit at <code>first: 100</code> on every connection and still be rejected, because <a href="/github/graphql-node-limit-exceeded/">the node count multiplies down through the nesting toward a cap of 500,000</a>. That is an aggregate about the whole document; this is a ceiling on one argument, checked per connection, with a different error and a different repair. Lowering a <code>first</code> from 500 to 100 fixes this one and can leave the other one failing.</p>
<p><strong>REST clamps, GraphQL rejects, and the difference is worth keeping.</strong> Sending <code>per_page=200</code> to a REST endpoint gets you 100 items and no complaint, which is <a href="/github/per-page-over-100-clamped/">its own quiet trap</a>: the client believes it asked for 200 and got everything. GraphQL refusing outright is the better behaviour of the two. It is only surprising because the REST habit came first.</p>""",
"steps": [
 {"h": "Resolve every slicing argument, not just the literal ones",
  "body": """<p>Feed the document to the checker with the variables you actually send. It lists every <code>first</code> and <code>last</code> in the query, resolves each one through a literal, a variable default or the supplied variables map, and says which of the three it came from. The source is as much of the finding as the number, because it tells you which file to open.</p>"""},
 {"h": "Compare each resolved value against 100",
  "body": """<p>One line per argument, one verdict per line. Over the ceiling is a rejection, exactly 100 is the maximum and fine, and an argument the checker could not resolve is reported as unresolved rather than assumed safe. Nothing is silently rolled into a total, because the ceiling applies to each connection on its own.</p>"""},
 {"h": "Read the pages that number actually implies",
  "body": """<p>The script prints how many round trips the requested size becomes at 100 per page: 500 is five pages, 2,000 is twenty. That is the honest cost of the thing the query was trying to avoid, and seeing it usually settles the argument about whether to paginate or to try to get more per call.</p>"""},
 {"h": "Confirm the shape of the rejection if you want to see it",
  "body": """<p>Sending the document returns a body with <code>errors</code> and no <code>data</code> key at all, which is what validation failure looks like and is worth seeing once. The script names the field and argument out of the message. Use <code>--offline</code> to skip this entirely: the audit needs no token and nothing is sent.</p>"""},
 {"h": "Rewrite as 100 plus a cursor, and check the node count separately",
  "body": """<p>Set the value to 100, add <code>pageInfo { hasNextPage endCursor }</code> and follow <code>after: $cursor</code> until it stops. Then run the node-count check as well, because a document that is legal on every individual argument can still be rejected for the product of them, and that is a different note with a different number.</p>"""},
],
"verify": """<p>The audit runs on a query file with no token and no points, and names both the value and where it came from.</p>
<pre><code class="language-bash">python3 github_graphql_slice.py --file queries/issue_export.graphql --offline
# point cost: 0 point(s). The ceiling is checked against the query text and the
# variables you supply; nothing is sent.
#   issues.first        written $first    value 250   variable-default   OVER  needs 3 pages
#   comments.first      written 100       value 100   literal            at the ceiling
#   labels.first        written $labels   value ?     unresolved         supply it to check
# over-ceiling-through-a-variable: issues.first resolves to 250 through a
# variable default, so a search of the document for a number over 100 finds
# nothing and every call is still rejected
# repair: set the default on $first to 100 and page with after: $cursor

GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_slice.py --repo acme/monorepo
# point cost: up to 1 point(s). A document rejected during validation never
# executes and is not billed at all.
# HTTP 200, phase=validation, data key present=no, errors=1
# rejected argument: first on field issues
# validation-rejected: the body carries errors and no data key, which is what a
# failure before execution looks like</code></pre>""",
"code_intro": "The audit is pure and needs nothing but text: strip the comments and string literals, walk the document, collect every <code>first</code> and <code>last</code> with the field it belongs to, then resolve each written value through three sources in order — a literal, the operation's variable definitions, and the variables map you pass in. Only after that is anything compared against 100. The optional probe sends the document once, purely to show that a validation failure comes back with no <code>data</code> key, and it refuses to open a socket if the document contains a mutation or a subscription.",
"py_file": "github_graphql_slice.py",
"py": '''"""Resolve every first and last in a GraphQL document against the ceiling of 100.

Read only, and queries only. GitHub's GraphQL endpoint takes a document in the
request body, so a read is carried by POST there just as a write would be; that
is transport, not intent. This script sends queries and refuses any document
containing a mutation or a subscription before it opens a socket. Nothing is
written and the repair is printed rather than performed.

Every connection in the schema caps first and last at 100. Over that the query
is rejected during validation, before execution begins, which is why the body
comes back with an errors array and no data key at all and why nothing is
billed. The number being rejected is often not written in the document: it
arrives through a variable default or through the variables map, so a text
search for a literal over 100 reports a clean document that fails every call.

What this can and cannot see: the ceiling is a fact about the schema and the
audit is a fact about the text plus the variables you hand it. A value computed
by a caller at run time is not in either, so the script reports an unresolved
argument as unresolved rather than as safe.

Environment:

    GITHUB_TOKEN    a token with read access to the GraphQL API. Not needed
                    with --offline.
"""
import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_slice")

API = "https://api.github.com"
UA = "github-graphql-slice/1.0"

# The ceiling on first and last, on every connection in the schema. Not a
# policy, not adjustable, and the same on every plan.
CEILING = 100

# A simple query costs one point, and a query rejected during validation costs
# none at all because it never runs.
POINTS_PER_QUERY = 1

# The default deliberately hides its oversized value in a variable default,
# because that is the version of this bug a grep does not find.
DEFAULT_QUERY = (
    "query($owner: String!, $name: String!, $first: Int = 250) {"
    " repository(owner: $owner, name: $name) {"
    " issues(first: $first, states: OPEN) { totalCount nodes { number title } }"
    " } }"
)

ARGUMENT_IN_MESSAGE = re.compile(
    "Argument '([A-Za-z_][A-Za-z0-9_]*)' on Field '([A-Za-z_][A-Za-z0-9_]*)'")


def strip_noise(document):
    """Remove GraphQL comments and string literals from a document. Pure.

    Written as a scanner rather than a regex because a hash inside a string
    literal is a legitimate character and a comment marker outside one.
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
    """Why this document will not be sent, or None if it is a read. Pure.

    The endpoint is the same one mutations go to, so the guard lives here rather
    than in a comment.
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


def argument_value(argument_text, name):
    """The text written for one named argument, or None. Pure.

    Splits on top-level commas so a nested object or list argument does not
    confuse the scan, and requires an exact name match so a variable definition
    such as `$first: Int = 250` is never mistaken for an argument called first.
    """
    src = str(argument_text or "")
    parts, depth, cur = [], 0, ""
    for ch in src:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
            continue
        cur += ch
    parts.append(cur)
    for part in parts:
        key, sep, value = part.partition(":")
        if not sep:
            continue
        if key.strip() == name:
            return value.strip() or None
    return None


def variable_defaults(document):
    """Defaults declared in the operation's variable definitions. Pure.

    Keyed with the leading dollar so the keys read the way they are written in
    the document: {"$first": "250"}.
    """
    src = strip_noise(document)
    head = src.split("{", 1)[0]
    out = {}
    for part in head.replace("(", " ").replace(")", " ").split(","):
        name, sep, rest = part.partition(":")
        if not sep:
            continue
        # The first part still carries the operation keyword and name in front
        # of the variable, so take the last token rather than the whole thing.
        name = (name.strip().rsplit(None, 1) or [""])[-1]
        if not name.startswith("$") or "=" not in rest:
            continue
        out[name] = rest.split("=", 1)[1].strip()
    return out


def slicing_arguments(document):
    """Every first and last in the document, with the field carrying it. Pure.

    Depth is counted in selection sets, so a reader can see which connection is
    where without reading the query again.
    """
    src = strip_noise(document)
    out, i, n, depth, word = [], 0, len(src), 0, ""
    while i < n:
        ch = src[i]
        if ch.isalnum() or ch == "_":
            word += ch
            i += 1
            continue
        if ch == "(" and word:
            field, j, level = word, i, 0
            while j < n:
                if src[j] == "(":
                    level += 1
                elif src[j] == ")":
                    level -= 1
                    if level == 0:
                        break
                j += 1
            args = src[i + 1:j]
            for arg in ("first", "last"):
                raw = argument_value(args, arg)
                if raw is not None:
                    out.append({"field": field, "arg": arg, "raw": raw, "depth": depth})
            i, word = j + 1, ""
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        word = ""
        i += 1
    return out


def as_int(value):
    """An integer, or None if this is not one. Pure."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def resolve_slice(raw, defaults=None, variables=None):
    """One written slicing value resolved to (value, source). Pure.

    Three sources in the order that decides the call: a literal in the document,
    a value supplied in the variables map, and a default in the operation's
    variable definitions. A supplied value beats a default because that is what
    the server sees.
    """
    text = str(raw or "").strip()
    if not text:
        return (None, "missing")
    if not text.startswith("$"):
        return (as_int(text), "literal")
    supplied = variables if isinstance(variables, dict) else {}
    if text[1:] in supplied:
        return (as_int(supplied[text[1:]]), "variable-supplied")
    if text in (defaults or {}):
        return (as_int((defaults or {})[text]), "variable-default")
    return (None, "unresolved")


def verdict(value):
    """One resolved value against the ceiling. Pure."""
    if value is None:
        return "unresolved"
    if value < 1:
        return "below-one"
    if value > CEILING:
        return "over-ceiling"
    if value == CEILING:
        return "at-ceiling"
    return "under-ceiling"


def pages_needed(value):
    """Round trips at 100 per page for a requested size. Pure."""
    if value is None or value < 1:
        return None
    return -(-value // CEILING)


def audit(document, variables=None):
    """Every slicing argument, resolved and judged. Pure."""
    defaults = variable_defaults(document)
    out = []
    for found in slicing_arguments(document):
        value, source = resolve_slice(found["raw"], defaults, variables)
        out.append({
            "field": found["field"],
            "arg": found["arg"],
            "depth": found["depth"],
            "written": found["raw"],
            "value": value,
            "source": source,
            "verdict": verdict(value),
            "pages": pages_needed(value),
        })
    return out


def classify(findings):
    """Classify a whole document. Pure. Returns (state, detail)."""
    if not findings:
        return ("no-slicing-argument",
                "no first or last appears anywhere in this document. GitHub "
                "requires a slicing argument on every connection, so either "
                "there is no connection here or the query is rejected for a "
                "different reason than this note describes.")
    over = [f for f in findings if f["verdict"] == "over-ceiling"]
    literal = [f for f in over if f["source"] == "literal"]
    if literal:
        f = literal[0]
        return ("over-ceiling-in-the-document",
                "%s.%s asks for %d, which is over the ceiling of %d, and the "
                "number is written in the query."
                % (f["field"], f["arg"], f["value"], CEILING))
    if over:
        f = over[0]
        return ("over-ceiling-through-a-variable",
                "%s.%s resolves to %d through a %s, so a search of the document "
                "for a number over %d finds nothing and every call is still "
                "rejected." % (f["field"], f["arg"], f["value"], f["source"], CEILING))
    unresolved = [f for f in findings if f["verdict"] == "unresolved"]
    if unresolved:
        f = unresolved[0]
        return ("unresolved-slice",
                "%s.%s is written as %s and no default or supplied value "
                "explains it, so this document cannot be cleared from the text "
                "alone." % (f["field"], f["arg"], f["written"]))
    below = [f for f in findings if f["verdict"] == "below-one"]
    if below:
        f = below[0]
        return ("slice-below-one",
                "%s.%s resolves to %d. The range is 1 to %d and zero is "
                "rejected the same way an oversized value is."
                % (f["field"], f["arg"], f["value"], CEILING))
    return ("within-the-ceiling",
            "all %d slicing argument(s) resolve to between 1 and %d. This "
            "document is not rejected for an argument value; the node count is "
            "a separate question." % (len(findings), CEILING))


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "over-ceiling-in-the-document":
        return ("set the value to 100 and page with after: $cursor until "
                "pageInfo.hasNextPage is false. The ceiling is not adjustable.")
    if state == "over-ceiling-through-a-variable":
        return ("fix the value where it is set, not in the query text. Cap it "
                "at 100 in the caller or in the variable default, and page "
                "with after: $cursor for the rest.")
    if state == "unresolved-slice":
        return ("run this again with --variables so the value can be resolved. "
                "An argument nobody can resolve is not an argument anybody has "
                "checked.")
    if state == "slice-below-one":
        return ("use a value of at least 1. A slicing argument of 0 is not a "
                "cheap query, it is a rejected one.")
    if state == "within-the-ceiling":
        return ("nothing on the argument ceiling. Check the node count as well: "
                "see /github/graphql-node-limit-exceeded/ -- a document legal on "
                "every argument can still be rejected for the product of them.")
    return "point the check at a document containing a connection."


def error_phase(status, body):
    """Which phase of the request failed. Pure.

    The specification is precise here and the distinction is the whole reason
    this note has a different shape from the errors-array notes: a request that
    fails before execution must not carry a data entry at all, while one that
    fails during execution carries data with nulls in it.
    """
    if not isinstance(body, dict):
        return "unreadable"
    if not body.get("errors"):
        return "clean"
    if "data" not in body:
        return "validation"
    return "execution"


def offending_argument(body):
    """The (argument, field) the server named, or (None, None). Pure."""
    if not isinstance(body, dict):
        return (None, None)
    for err in body.get("errors") or []:
        message = err.get("message", "") if isinstance(err, dict) else ""
        m = ARGUMENT_IN_MESSAGE.search(message)
        if m:
            return (m.group(1), m.group(2))
    return (None, None)


def point_cost(sending):
    """Points this run can spend. Pure."""
    return POINTS_PER_QUERY if sending else 0


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
    ap.add_argument("--file", help="a .graphql file to audit")
    ap.add_argument("--query", help="the document as a string")
    ap.add_argument("--variables", default="{}",
                    help="JSON object of the variables you actually send")
    ap.add_argument("--repo", help="owner/name, to fill the default query")
    ap.add_argument("--offline", action="store_true",
                    help="audit the text only. No token, nothing sent.")
    args = ap.parse_args()

    if args.file:
        document = Path(args.file).read_text(encoding="utf-8")
    else:
        document = args.query or DEFAULT_QUERY

    try:
        variables = json.loads(args.variables)
    except ValueError:
        log.error("--variables takes a JSON object")
        return 2
    if not isinstance(variables, dict):
        log.error("--variables takes a JSON object")
        return 2

    if args.repo:
        try:
            owner, name = args.repo.split("/", 1)
        except ValueError:
            log.error("--repo takes owner/name")
            return 2
        variables.setdefault("owner", owner)
        variables.setdefault("name", name)

    why_not = refusal(document)
    if why_not:
        log.error("refusing to send: %s", why_not)
        return 2

    findings = audit(document, variables)
    log.info("point cost: %d point(s). The ceiling is checked against the query "
             "text and the variables you supply; a document rejected during "
             "validation never executes and is not billed at all.",
             point_cost(not args.offline))
    for f in findings:
        log.info("  %s.%s  written %s  value %s  %s  %s",
                 f["field"], f["arg"], f["written"],
                 "?" if f["value"] is None else f["value"],
                 f["source"],
                 "OVER, needs %d pages" % f["pages"]
                 if f["verdict"] == "over-ceiling" else f["verdict"])
    state, detail = classify(findings)
    log.info("%s: %s", state, detail)
    log.info("repair: %s", repair(state))

    probe = None
    if not args.offline:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            log.error("set GITHUB_TOKEN, or pass --offline to audit the text only")
            return 2
        session = requests.Session()
        session.headers.update({
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            # GitHub rejects requests with no User-Agent outright.
            "User-Agent": UA,
        })
        status, body = run_query(session, document, variables)
        phase = error_phase(status, body)
        arg, field = offending_argument(body)
        log.info("HTTP %s, phase=%s, data key present=%s",
                 status, phase, "yes" if isinstance(body, dict) and "data" in body else "no")
        if arg:
            log.info("rejected argument: %s on field %s", arg, field)
        if phase == "validation":
            log.info("validation-rejected: the body carries errors and no data "
                     "key, which is what a failure before execution looks like")
        probe = {"status": status, "phase": phase,
                 "rejected_argument": arg, "rejected_field": field}

    print(json.dumps({"ceiling": CEILING, "state": state, "findings": findings,
                      "probe": probe}, indent=2, default=str))
    return 1 if state not in ("within-the-ceiling", "no-slicing-argument") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-slice.mjs",
"js": '''/**
 * Resolve every first and last in a GraphQL document against the ceiling of 100.
 *
 * Read only, and queries only. GitHub's GraphQL endpoint takes a document in
 * the request body, so a read is carried by POST there just as a write would
 * be; that is transport, not intent. Any document containing a mutation or a
 * subscription is refused before a socket opens.
 *
 * Environment:
 *   GITHUB_TOKEN      a token with read access. Not needed with GITHUB_OFFLINE.
 *   GITHUB_QUERY      the document as a string
 *   GITHUB_VARIABLES  JSON object of the variables you actually send
 *   GITHUB_REPO       owner/name, to fill the default query
 *   GITHUB_OFFLINE    set to 1 to audit the text only
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-slice/1.0';

/** The ceiling on first and last, on every connection in the schema. */
export const CEILING = 100;

/** A simple query costs one point; a validation rejection costs none. */
export const POINTS_PER_QUERY = 1;

const DEFAULT_QUERY = 'query($owner: String!, $name: String!, $first: Int = 250) {'
  + ' repository(owner: $owner, name: $name) {'
  + ' issues(first: $first, states: OPEN) { totalCount nodes { number title } }'
  + ' } }';

const ARGUMENT_IN_MESSAGE = /Argument '([A-Za-z_][A-Za-z0-9_]*)' on Field '([A-Za-z_][A-Za-z0-9_]*)'/;

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

/** The text written for one named argument, or null. Pure. */
export function argumentValue(argumentText, name) {
  const src = String(argumentText ?? '');
  const parts = [];
  let depth = 0;
  let cur = '';
  for (const ch of src) {
    if ('([{'.includes(ch)) depth += 1;
    else if (')]}'.includes(ch)) depth = Math.max(0, depth - 1);
    if (ch === ',' && depth === 0) { parts.push(cur); cur = ''; continue; }
    cur += ch;
  }
  parts.push(cur);
  for (const part of parts) {
    const at = part.indexOf(':');
    if (at < 0) continue;
    if (part.slice(0, at).trim() === name) {
      return part.slice(at + 1).trim() || null;
    }
  }
  return null;
}

/** Defaults declared in the operation's variable definitions. Pure. */
export function variableDefaults(document) {
  const head = stripNoise(document).split('{')[0];
  const out = {};
  for (const part of head.replace(/\\(/g, ' ').replace(/\\)/g, ' ').split(',')) {
    const at = part.indexOf(':');
    if (at < 0) continue;
    // The first part still carries the operation keyword and name in front
    // of the variable, so take the last token rather than the whole thing.
    const name = part.slice(0, at).trim().split(/\\s+/).pop();
    const rest = part.slice(at + 1);
    if (!name || !name.startsWith('$') || !rest.includes('=')) continue;
    out[name] = rest.slice(rest.indexOf('=') + 1).trim();
  }
  return out;
}

/** Every first and last in the document, with the field carrying it. Pure. */
export function slicingArguments(document) {
  const src = stripNoise(document);
  const out = [];
  let i = 0;
  let depth = 0;
  let word = '';
  while (i < src.length) {
    const ch = src[i];
    if (/[A-Za-z0-9_]/.test(ch)) { word += ch; i += 1; continue; }
    if (ch === '(' && word) {
      const field = word;
      let j = i;
      let level = 0;
      while (j < src.length) {
        if (src[j] === '(') level += 1;
        else if (src[j] === ')') { level -= 1; if (level === 0) break; }
        j += 1;
      }
      const args = src.slice(i + 1, j);
      for (const arg of ['first', 'last']) {
        const raw = argumentValue(args, arg);
        if (raw !== null) out.push({ field, arg, raw, depth });
      }
      i = j + 1;
      word = '';
      continue;
    }
    if (ch === '{') depth += 1;
    else if (ch === '}') depth = Math.max(0, depth - 1);
    word = '';
    i += 1;
  }
  return out;
}

/** An integer, or null if this is not one. Pure. */
export function asInt(value) {
  const text = String(value ?? '').trim();
  if (!/^-?[0-9]+$/.test(text)) return null;
  return Number(text);
}

/** One written slicing value resolved to [value, source]. Pure. */
export function resolveSlice(raw, defaults, variables) {
  const text = String(raw ?? '').trim();
  if (!text) return [null, 'missing'];
  if (!text.startsWith('$')) return [asInt(text), 'literal'];
  const supplied = (variables && typeof variables === 'object') ? variables : {};
  const bare = text.slice(1);
  if (Object.prototype.hasOwnProperty.call(supplied, bare)) {
    return [asInt(supplied[bare]), 'variable-supplied'];
  }
  if (defaults && Object.prototype.hasOwnProperty.call(defaults, text)) {
    return [asInt(defaults[text]), 'variable-default'];
  }
  return [null, 'unresolved'];
}

/** One resolved value against the ceiling. Pure. */
export function verdict(value) {
  if (value === null || value === undefined) return 'unresolved';
  if (value < 1) return 'below-one';
  if (value > CEILING) return 'over-ceiling';
  if (value === CEILING) return 'at-ceiling';
  return 'under-ceiling';
}

/** Round trips at 100 per page for a requested size. Pure. */
export function pagesNeeded(value) {
  if (value === null || value === undefined || value < 1) return null;
  return Math.ceil(value / CEILING);
}

/** Every slicing argument, resolved and judged. Pure. */
export function audit(document, variables) {
  const defaults = variableDefaults(document);
  return slicingArguments(document).map((found) => {
    const [value, source] = resolveSlice(found.raw, defaults, variables);
    return {
      field: found.field,
      arg: found.arg,
      depth: found.depth,
      written: found.raw,
      value,
      source,
      verdict: verdict(value),
      pages: pagesNeeded(value),
    };
  });
}

/** Classify a whole document. Pure. Returns [state, detail]. */
export function classify(findings) {
  if (!findings || findings.length === 0) {
    return ['no-slicing-argument', 'no first or last appears anywhere in this '
      + 'document. GitHub requires a slicing argument on every connection, so '
      + 'either there is no connection here or the query is rejected for a '
      + 'different reason than this note describes.'];
  }
  const over = findings.filter((f) => f.verdict === 'over-ceiling');
  const literal = over.filter((f) => f.source === 'literal');
  if (literal.length) {
    const f = literal[0];
    return ['over-ceiling-in-the-document',
      `${f.field}.${f.arg} asks for ${f.value}, which is over the ceiling of `
      + `${CEILING}, and the number is written in the query.`];
  }
  if (over.length) {
    const f = over[0];
    return ['over-ceiling-through-a-variable',
      `${f.field}.${f.arg} resolves to ${f.value} through a ${f.source}, so a `
      + `search of the document for a number over ${CEILING} finds nothing and `
      + 'every call is still rejected.'];
  }
  const unresolved = findings.filter((f) => f.verdict === 'unresolved');
  if (unresolved.length) {
    const f = unresolved[0];
    return ['unresolved-slice',
      `${f.field}.${f.arg} is written as ${f.written} and no default or `
      + 'supplied value explains it, so this document cannot be cleared from '
      + 'the text alone.'];
  }
  const below = findings.filter((f) => f.verdict === 'below-one');
  if (below.length) {
    const f = below[0];
    return ['slice-below-one',
      `${f.field}.${f.arg} resolves to ${f.value}. The range is 1 to ${CEILING} `
      + 'and zero is rejected the same way an oversized value is.'];
  }
  return ['within-the-ceiling',
    `all ${findings.length} slicing argument(s) resolve to between 1 and `
    + `${CEILING}. This document is not rejected for an argument value; the `
    + 'node count is a separate question.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'over-ceiling-in-the-document') {
    return 'set the value to 100 and page with after: $cursor until '
      + 'pageInfo.hasNextPage is false. The ceiling is not adjustable.';
  }
  if (state === 'over-ceiling-through-a-variable') {
    return 'fix the value where it is set, not in the query text. Cap it at '
      + '100 in the caller or in the variable default, and page with '
      + 'after: $cursor for the rest.';
  }
  if (state === 'unresolved-slice') {
    return 'run this again with the variables so the value can be resolved. An '
      + 'argument nobody can resolve is not an argument anybody has checked.';
  }
  if (state === 'slice-below-one') {
    return 'use a value of at least 1. A slicing argument of 0 is not a cheap '
      + 'query, it is a rejected one.';
  }
  if (state === 'within-the-ceiling') {
    return 'nothing on the argument ceiling. Check the node count as well: see '
      + '/github/graphql-node-limit-exceeded/ -- a document legal on every '
      + 'argument can still be rejected for the product of them.';
  }
  return 'point the check at a document containing a connection.';
}

/** Which phase of the request failed. Pure. */
export function errorPhase(status, body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return 'unreadable';
  if (!(Array.isArray(body.errors) && body.errors.length > 0)) return 'clean';
  if (!Object.prototype.hasOwnProperty.call(body, 'data')) return 'validation';
  return 'execution';
}

/** The [argument, field] the server named, or [null, null]. Pure. */
export function offendingArgument(body) {
  if (!body || typeof body !== 'object' || !Array.isArray(body.errors)) return [null, null];
  for (const err of body.errors) {
    const message = (err && typeof err === 'object' && err.message) || '';
    const m = ARGUMENT_IN_MESSAGE.exec(message);
    if (m) return [m[1], m[2]];
  }
  return [null, null];
}

/** Points this run can spend. Pure. */
export function pointCost(sending) {
  return sending ? POINTS_PER_QUERY : 0;
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
  const offline = process.env.GITHUB_OFFLINE === '1';
  const document = process.env.GITHUB_QUERY || DEFAULT_QUERY;
  let variables = {};
  try { variables = JSON.parse(process.env.GITHUB_VARIABLES || '{}'); } catch {
    console.error('GITHUB_VARIABLES takes a JSON object');
    process.exitCode = 2;
    return;
  }
  if (process.env.GITHUB_REPO) {
    const [owner, name] = process.env.GITHUB_REPO.split('/');
    if (!owner || !name) {
      console.error('GITHUB_REPO takes owner/name');
      process.exitCode = 2;
      return;
    }
    if (!('owner' in variables)) variables.owner = owner;
    if (!('name' in variables)) variables.name = name;
  }

  const whyNot = refusal(document);
  if (whyNot) {
    console.error(`refusing to send: ${whyNot}`);
    process.exitCode = 2;
    return;
  }

  const findings = audit(document, variables);
  console.log(`point cost: ${pointCost(!offline)} point(s). A document rejected `
    + 'during validation never executes and is not billed at all.');
  for (const f of findings) {
    console.log(`  ${f.field}.${f.arg}  written ${f.written}  value `
      + `${f.value === null ? '?' : f.value}  ${f.source}  `
      + `${f.verdict === 'over-ceiling' ? `OVER, needs ${f.pages} pages` : f.verdict}`);
  }
  const [state, detail] = classify(findings);
  console.log(`${state}: ${detail}`);
  console.log(`repair: ${repair(state)}`);

  let probe = null;
  if (!offline) {
    const token = process.env.GITHUB_TOKEN;
    if (!token) {
      console.error('set GITHUB_TOKEN, or GITHUB_OFFLINE=1 to audit the text only');
      process.exitCode = 2;
      return;
    }
    const { status, body } = await runQuery(token, document, variables);
    const phase = errorPhase(status, body);
    const [arg, field] = offendingArgument(body);
    const hasData = !!body && typeof body === 'object'
      && Object.prototype.hasOwnProperty.call(body, 'data');
    console.log(`HTTP ${status}, phase=${phase}, data key present=${hasData ? 'yes' : 'no'}`);
    if (arg) console.log(`rejected argument: ${arg} on field ${field}`);
    if (phase === 'validation') {
      console.log('validation-rejected: the body carries errors and no data key, '
        + 'which is what a failure before execution looks like');
    }
    probe = { status, phase, rejected_argument: arg, rejected_field: field };
  }

  console.log(JSON.stringify({ ceiling: CEILING, state, findings, probe }, null, 2));
  process.exitCode = (state === 'within-the-ceiling' || state === 'no-slicing-argument') ? 0 : 1;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The suite is mostly about where a number comes from, because that is where this bug lives. A literal over the ceiling, a variable default over the ceiling, a supplied variable that overrides a safe default with an unsafe one, and a variable nobody can resolve are four separate cases with four separate verdicts. After that: that a variable definition reading <code>$first: Int = 250</code> is never mistaken for an argument called <code>first</code>, that <code>last</code> is treated exactly like <code>first</code>, that a validation failure with no <code>data</code> key is told apart from an execution failure that has one, and that the offline path spends nothing.",
"test_py_file": "test_github_graphql_slice.py",
"test_py": '''from github_graphql_slice import (
    CEILING, POINTS_PER_QUERY, argument_value, audit, classify, error_phase,
    offending_argument, operations, pages_needed, point_cost, refusal, repair,
    resolve_slice, slicing_arguments, variable_defaults, verdict,
)

LITERAL = "query { repository(owner: \\"a\\", name: \\"b\\") { issues(first: 500) { totalCount } } }"
VIA_DEFAULT = ("query($first: Int = 250) { repository(owner: \\"a\\", name: \\"b\\")"
               " { issues(first: $first) { totalCount } } }")
SAFE = ("query($first: Int = 100) { repository(owner: \\"a\\", name: \\"b\\")"
        " { issues(first: $first) { totalCount } } }")

VALIDATION_BODY = {"errors": [{"message": "Argument 'first' on Field 'issues' has an "
                                          "invalid value (500). Expected type 'Int'."}]}
EXECUTION_BODY = {"data": {"repository": None},
                  "errors": [{"type": "NOT_FOUND", "message": "Could not resolve"}]}


def test_the_ceiling_is_one_hundred_everywhere():
    assert CEILING == 100
    assert verdict(101) == "over-ceiling"
    assert verdict(100) == "at-ceiling"
    assert verdict(1) == "under-ceiling"
    assert verdict(0) == "below-one"
    assert verdict(None) == "unresolved"


def test_a_literal_over_the_ceiling_is_found_in_the_text():
    found = audit(LITERAL, {})
    assert [(f["field"], f["arg"], f["value"], f["source"]) for f in found] == [
        ("issues", "first", 500, "literal")]
    state, detail = classify(found)
    assert state == "over-ceiling-in-the-document"
    assert "500" in detail


def test_a_variable_default_over_the_ceiling_is_invisible_to_a_grep():
    assert "250" not in "".join(f["written"] for f in audit(VIA_DEFAULT, {}))
    found = audit(VIA_DEFAULT, {})
    assert found[0]["value"] == 250
    assert found[0]["source"] == "variable-default"
    state, detail = classify(found)
    assert state == "over-ceiling-through-a-variable"
    assert "finds nothing" in detail


def test_a_supplied_variable_beats_the_default_because_the_server_sees_it():
    found = audit(SAFE, {"first": 400})
    assert found[0]["value"] == 400
    assert found[0]["source"] == "variable-supplied"
    assert classify(found)[0] == "over-ceiling-through-a-variable"
    assert classify(audit(SAFE, {}))[0] == "within-the-ceiling"


def test_an_unresolved_variable_is_never_assumed_safe():
    doc = "query($n: Int!) { repository(owner: \\"a\\", name: \\"b\\") { issues(first: $n) { totalCount } } }"
    found = audit(doc, {})
    assert found[0]["source"] == "unresolved"
    assert found[0]["verdict"] == "unresolved"
    state = classify(found)[0]
    assert state == "unresolved-slice"
    assert "--variables" in repair(state)


def test_a_variable_definition_is_not_an_argument_called_first():
    assert variable_defaults(VIA_DEFAULT) == {"$first": "250"}
    args = slicing_arguments(VIA_DEFAULT)
    assert len(args) == 1
    assert args[0]["field"] == "issues"
    assert argument_value("$first: Int = 250", "first") is None
    assert argument_value("first: 100, states: OPEN", "first") == "100"


def test_last_is_treated_exactly_like_first():
    doc = "query { repository(owner: \\"a\\", name: \\"b\\") { issues(last: 250) { totalCount } } }"
    found = audit(doc, {})
    assert found[0]["arg"] == "last"
    assert classify(found)[0] == "over-ceiling-in-the-document"


def test_the_word_first_inside_a_string_is_not_an_argument():
    doc = 'query { search(query: "first: 500", type: ISSUE, first: 10) { issueCount } }'
    found = audit(doc, {})
    assert [(f["arg"], f["value"]) for f in found] == [("first", 10)]
    assert classify(found)[0] == "within-the-ceiling"


def test_a_clean_document_is_sent_on_to_the_node_count_rather_than_cleared():
    state = classify(audit(SAFE, {}))[0]
    assert state == "within-the-ceiling"
    assert "graphql-node-limit-exceeded" in repair(state)


def test_the_pages_that_number_really_means():
    assert pages_needed(500) == 5
    assert pages_needed(101) == 2
    assert pages_needed(100) == 1
    assert pages_needed(0) is None
    assert pages_needed(None) is None


def test_a_validation_failure_carries_no_data_key_at_all():
    assert error_phase(200, VALIDATION_BODY) == "validation"
    assert error_phase(200, EXECUTION_BODY) == "execution"
    assert error_phase(200, {"data": {"repository": {"name": "x"}}}) == "clean"
    assert error_phase(200, None) == "unreadable"


def test_the_server_names_the_argument_and_the_field():
    assert offending_argument(VALIDATION_BODY) == ("first", "issues")
    assert offending_argument(EXECUTION_BODY) == (None, None)
    assert offending_argument(None) == (None, None)


def test_the_script_refuses_to_send_a_mutation():
    assert operations("query Q { viewer { login } }") == ["query"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal("subscription S { thing { id } }")
    assert refusal("") == "the document contains no operation to send."
    assert refusal(LITERAL) is None


def test_the_offline_audit_spends_nothing():
    assert POINTS_PER_QUERY == 1
    assert point_cost(False) == 0
    assert point_cost(True) == 1
''',
"test_js_file": "github-graphql-slice.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  CEILING, POINTS_PER_QUERY, argumentValue, audit, classify, errorPhase,
  offendingArgument, operations, pagesNeeded, pointCost, refusal, repair,
  slicingArguments, variableDefaults, verdict,
} from './github-graphql-slice.mjs';

const LITERAL = 'query { repository(owner: "a", name: "b") { issues(first: 500) { totalCount } } }';
const VIA_DEFAULT = 'query($first: Int = 250) { repository(owner: "a", name: "b")'
  + ' { issues(first: $first) { totalCount } } }';
const SAFE = 'query($first: Int = 100) { repository(owner: "a", name: "b")'
  + ' { issues(first: $first) { totalCount } } }';

const VALIDATION_BODY = {
  errors: [{ message: "Argument 'first' on Field 'issues' has an invalid value (500)." }],
};
const EXECUTION_BODY = {
  data: { repository: null },
  errors: [{ type: 'NOT_FOUND', message: 'Could not resolve' }],
};

test('the ceiling is one hundred everywhere', () => {
  assert.equal(CEILING, 100);
  assert.equal(verdict(101), 'over-ceiling');
  assert.equal(verdict(100), 'at-ceiling');
  assert.equal(verdict(1), 'under-ceiling');
  assert.equal(verdict(0), 'below-one');
  assert.equal(verdict(null), 'unresolved');
});

test('a literal over the ceiling is found in the text', () => {
  const found = audit(LITERAL, {});
  assert.deepEqual(found.map((f) => [f.field, f.arg, f.value, f.source]),
    [['issues', 'first', 500, 'literal']]);
  const [state, detail] = classify(found);
  assert.equal(state, 'over-ceiling-in-the-document');
  assert.match(detail, /500/);
});

test('a variable default over the ceiling is invisible to a grep', () => {
  const found = audit(VIA_DEFAULT, {});
  assert.ok(!found.map((f) => f.written).join('').includes('250'));
  assert.equal(found[0].value, 250);
  assert.equal(found[0].source, 'variable-default');
  const [state, detail] = classify(found);
  assert.equal(state, 'over-ceiling-through-a-variable');
  assert.match(detail, /finds nothing/);
});

test('a supplied variable beats the default because the server sees it', () => {
  const found = audit(SAFE, { first: 400 });
  assert.equal(found[0].value, 400);
  assert.equal(found[0].source, 'variable-supplied');
  assert.equal(classify(found)[0], 'over-ceiling-through-a-variable');
  assert.equal(classify(audit(SAFE, {}))[0], 'within-the-ceiling');
});

test('an unresolved variable is never assumed safe', () => {
  const doc = 'query($n: Int!) { repository(owner: "a", name: "b") { issues(first: $n) { totalCount } } }';
  const found = audit(doc, {});
  assert.equal(found[0].source, 'unresolved');
  assert.equal(found[0].verdict, 'unresolved');
  const state = classify(found)[0];
  assert.equal(state, 'unresolved-slice');
  assert.match(repair(state), /variables/);
});

test('a variable definition is not an argument called first', () => {
  assert.deepEqual(variableDefaults(VIA_DEFAULT), { $first: '250' });
  const args = slicingArguments(VIA_DEFAULT);
  assert.equal(args.length, 1);
  assert.equal(args[0].field, 'issues');
  assert.equal(argumentValue('$first: Int = 250', 'first'), null);
  assert.equal(argumentValue('first: 100, states: OPEN', 'first'), '100');
});

test('last is treated exactly like first', () => {
  const doc = 'query { repository(owner: "a", name: "b") { issues(last: 250) { totalCount } } }';
  const found = audit(doc, {});
  assert.equal(found[0].arg, 'last');
  assert.equal(classify(found)[0], 'over-ceiling-in-the-document');
});

test('the word first inside a string is not an argument', () => {
  const doc = 'query { search(query: "first: 500", type: ISSUE, first: 10) { issueCount } }';
  const found = audit(doc, {});
  assert.deepEqual(found.map((f) => [f.arg, f.value]), [['first', 10]]);
  assert.equal(classify(found)[0], 'within-the-ceiling');
});

test('a clean document is sent on to the node count rather than cleared', () => {
  const state = classify(audit(SAFE, {}))[0];
  assert.equal(state, 'within-the-ceiling');
  assert.match(repair(state), /graphql-node-limit-exceeded/);
});

test('the pages that number really means', () => {
  assert.equal(pagesNeeded(500), 5);
  assert.equal(pagesNeeded(101), 2);
  assert.equal(pagesNeeded(100), 1);
  assert.equal(pagesNeeded(0), null);
  assert.equal(pagesNeeded(null), null);
});

test('a validation failure carries no data key at all', () => {
  assert.equal(errorPhase(200, VALIDATION_BODY), 'validation');
  assert.equal(errorPhase(200, EXECUTION_BODY), 'execution');
  assert.equal(errorPhase(200, { data: { repository: { name: 'x' } } }), 'clean');
  assert.equal(errorPhase(200, null), 'unreadable');
});

test('the server names the argument and the field', () => {
  assert.deepEqual(offendingArgument(VALIDATION_BODY), ['first', 'issues']);
  assert.deepEqual(offendingArgument(EXECUTION_BODY), [null, null]);
  assert.deepEqual(offendingArgument(null), [null, null]);
});

test('the script refuses to send a mutation', () => {
  assert.deepEqual(operations('query Q { viewer { login } }'), ['query']);
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.ok(refusal('subscription S { thing { id } }'));
  assert.equal(refusal(''), 'the document contains no operation to send.');
  assert.equal(refusal(LITERAL), null);
});

test('the offline audit spends nothing', () => {
  assert.equal(POINTS_PER_QUERY, 1);
  assert.equal(pointCost(false), 0);
  assert.equal(pointCost(true), 1);
});
''',
"faq": [
 ("Can I raise the limit above 100 with a header or a preview?",
  "No. The cap on first and last is part of the connection contract in GitHub's schema and applies to every connection in it. There is no scope, header, API version, preview or Enterprise plan that changes it, and anything you find suggesting otherwise is describing a different GraphQL API. The only way to read more than 100 items from a connection is to ask for 100 and then follow the cursor, which is the design rather than a workaround."),
 ("Why did the same number work fine against the REST API?",
  "Because REST clamps and GraphQL rejects. Sending per_page=200 to a REST list endpoint returns 100 items with no error and no warning, so a client that asked for 200 believes it received everything, which is a quieter bug than this one and has its own note. GraphQL refusing outright is the better of the two behaviours. It is only surprising because most people meet the clamping version first and learn from it that an oversized page size is harmless."),
 ("The query has no number over 100 anywhere in it. Where is the 500 coming from?",
  "From a variable, almost certainly. A slicing value can be written as a literal, given a default in the operation's variable definitions, or supplied by the caller in the variables map, and only the first of those is in the document. This script resolves all three and prints which one each value came from, because that is what tells you which file to open. A value the caller computes at run time is not knowable from the repository at all, so it is reported as unresolved rather than assumed to be fine."),
 ("Does a rejected query cost points?",
  "No. Rejection happens during validation, before execution begins, so the query never runs and nothing is deducted from the hourly point budget. That makes it the cheapest failure in this section and it also means a retry loop stuck on it will not drain your quota, which is unusual here. It is still an infinite loop that returns nothing, and it will fail identically forever, because the document is the problem and retrying does not change the document."),
 ("I set every first to 100 and the query is still rejected. What now?",
  "Then you have the other limit. Node count multiplies down through the nesting, so 100 repositories each with 100 pull requests each with 100 comments asks for over a million nodes against a cap of 500,000, and every individual argument in that document is legal. That is a different error, MAX_NODE_LIMIT_EXCEEDED, and a different note. The two checks are worth running together: this one clears each argument on its own, and the node count clears the product of them."),
],
"related": [
 ("/github/graphql-node-limit-exceeded/", "The node count multiplies down the nesting"),
 ("/github/graphql-nested-pagination-ignored/", "Inner connections truncate per parent"),
 ("/github/per-page-over-100-clamped/", "REST clamps per_page instead of rejecting"),
],
"citations": [CITE_GQL_RESOURCE, CITE_SPEC_VALIDATION, CITE_SPEC_VALUES, CITE_REST_PAGINATION],
},

{
"slug": "graphql-nested-pagination-ignored",
"title": "Nested GraphQL connections truncate at 100 per parent",
"description": "The outer connection pages correctly and the inner ones restart each time, so every parent quietly returns its first 100 children and totalCount proves it.",
"h1": "Nested GraphQL connections truncate at 100 per parent",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github graphql nested pagination",
             "graphql paginate nested connection cursor",
             "github graphql only first 100 pull requests",
             "graphql inner connection pageInfo hasNextPage",
             "github graphql totalCount more than nodes"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The pagination loop is correct. It reads <code>pageInfo.hasNextPage</code>, follows <code>endCursor</code>, and walks every repository in the organisation without missing one. Inside each of those repositories the query also asks for pull requests, and every repository returns exactly one hundred of them, including the one that has four hundred and six. The response says so, in a <code>totalCount</code> sitting three lines above the truncated list, and nothing anywhere raises an error.",
"short_answer": """<p>Every connection in a GraphQL query has its own cursor. Paginating the outer one does nothing whatsoever for the inner ones: each new outer page starts the inner connections again from their first item, so each parent gives you its first <code>first: n</code> children and stops. There is no error, no warning and no partial-response marker, because from the server's point of view it answered exactly what was asked.</p>
<p>Ask every nested connection for <code>totalCount</code> and <code>pageInfo { hasNextPage endCursor }</code>, then compare <code>totalCount</code> against the number of <code>nodes</code> you received, per parent. Any parent where those disagree is truncated, and the repair is a second loop: for each such parent, issue a follow-up query scoped to it with <code>after: endCursor</code>. One outer walk plus a per-parent inner walk, not one query.</p>""",
"problem": """<p>This is what a fixed pagination bug looks like when it was only fixed once. Somebody learned the lesson properly, wrote a loop that follows cursors until they run out, and tested it: the repository count comes back right, the loop terminates, the numbers match the web interface. What was tested was the outer connection, because the outer connection is the one the loop is about, and it is genuinely correct.</p>
<p>The inner connections were never in scope. They came along as fields of the objects being paged, they look like plain lists in the response, and code that consumes them reads <code>repo.pullRequests.nodes</code> as though it were an array of everything. Nothing about the shape suggests a cursor exists underneath it. In JSON a connection with a hundred nodes and a connection with all of them are the same shape.</p>
<p>What makes it worse than the single-list version of this bug is that it multiplies and averages out. Truncating one list gives you a number that is obviously wrong. Truncating four hundred lists at a hundred each gives you a plausible number that is stable, moves smoothly, and is wrong by however much the busiest repositories exceed the cap. Reports built on it look healthy. The repositories most likely to be truncated are the ones with the most activity, so the error concentrates precisely where the interesting data was.</p>""",
"why": """<p><strong>One cursor per connection, and they do not interact.</strong> A connection's position is carried by <code>after</code> and reported by <code>pageInfo</code>, and both belong to that connection alone. When the outer connection advances to its next page it fetches new parent objects, and each of those resolves its inner connections from the start. Nothing carries an inner cursor across an outer page, and there is no argument that would make it.</p>
<p><strong>The response is not an error, so nothing tells you.</strong> The server returned the number of items it was asked for. There is no <code>errors</code> entry, no status change and no flag on the connection saying it stopped early. The only evidence is arithmetic you have to opt into: <code>totalCount</code> next to the length of <code>nodes</code>, or <code>pageInfo.hasNextPage</code> coming back true on a connection nobody intends to follow.</p>
<p><strong>A connection with neither field cannot be checked at all.</strong> If the query asks only for <code>nodes</code>, the response contains no information about whether more existed. Not "it looks complete" but "it is unknowable from this response". That is worth reporting separately from truncation, because the repair is different: the first thing to do is add the fields, and only then can you ask the question.</p>
<p><strong>Seeing the truncation and being able to resume it are two different things.</strong> <code>totalCount</code> tells you a connection stopped short. <code>pageInfo.endCursor</code> is what lets you continue it. A query that asks for the first and not the second produces a response that proves data is missing and gives you no way to fetch it without starting the parent again, which is a needlessly expensive place to be.</p>
<p><strong>This is not the REST version of losing pages.</strong> When a REST client <a href="/github/link-header-not-followed/">ignores the <code>Link</code> header</a> it loses everything past the first page of one list, and the <code>rel="last"</code> link hands you the true count for free. Here there is no <code>Link</code> header, no <code>rel="last"</code>, and the loss is per parent rather than once. Same family, different evidence and different arithmetic, so the two notes do not share a script.</p>
<p><strong>Doing it correctly costs more queries, and that is the real decision.</strong> One follow-up query per truncated parent is the price, and on four hundred repositories that is four hundred more calls against a point budget. That is the honest trade, and it is why lowering the inner <code>first</code> and paging deliberately usually beats asking for the maximum and hoping. The script counts the follow-ups your response implies so the number is in front of you before you write the loop.</p>""",
"steps": [
 {"h": "Ask every connection for totalCount and pageInfo, including the inner ones",
  "body": """<p>A connection that asks only for <code>nodes</code> cannot be audited by anybody, including you. Adding <code>totalCount</code> and <code>pageInfo { hasNextPage endCursor }</code> to each one costs nothing in points and turns an unanswerable question into an arithmetic one. The script reports any connection in your document that is missing them.</p>"""},
 {"h": "Compare totalCount against the nodes you received, per parent",
  "body": """<p>Not in aggregate. The whole character of this bug is that it happens once per parent, so a single total hides it. The script walks the response tree, finds every connection wherever it is nested, and prints the returned count against the true count with the path that leads to it.</p>"""},
 {"h": "Separate the outer connection from the inner ones",
  "body": """<p>An outer connection that is truncated is a bug you already know how to see, and probably already handle. An inner one is the one nobody is looking at. The script reports them at different depths and says which is which, because they have the same evidence and very different likelihoods of being noticed.</p>"""},
 {"h": "Check that what truncated can also be resumed",
  "body": """<p>A connection with <code>totalCount</code> and no <code>pageInfo</code> proves the loss and gives you no cursor to continue from. That is reported on its own, because the fix is one line in the query and without it the only way to get the rest is to fetch the parent again.</p>"""},
 {"h": "Count the follow-up queries before you write the loop",
  "body": """<p>Correct nested pagination is an outer walk plus one inner walk per truncated parent, and each of those is a query with a price. The script totals them from what it saw, so the cost of doing it properly is a number rather than a surprise. The audit itself is one query and it says so first.</p>"""},
],
"verify": """<p>The truncation is per parent, so the report is per parent, and the follow-up cost is stated rather than discovered.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_nested.py --login acme
# point cost: 1 point(s) against the 5,000/hour GraphQL budget
# document: issues asks for totalCount but not pageInfo, so truncation is
# visible and cannot be resumed without refetching the parent
#   repositoryOwner.repositories                 depth 0   5 of 218   more pages
#   ...repositories.nodes[0].issues              depth 1   5 of 406   401 missing, no cursor
#   ...repositories.nodes[1].issues              depth 1   2 of 2     complete
#   ...repositories.nodes[2].issues              depth 1   5 of 88    83 missing, no cursor
# inner-connection-truncated: 2 of 3 inner connection(s) returned fewer items
# than they contain and 484 item(s) are missing with no error raised
# following them properly costs 98 more queries, at least one per truncated parent
# repair: add pageInfo { hasNextPage endCursor } to every nested connection and
# walk each truncated parent separately with after: endCursor</code></pre>""",
"code_intro": "Two halves, both pure. The document half finds connections by their shape rather than by their arguments — a field whose own selection set contains <code>nodes</code> or <code>edges</code> — and reports which of them asked for <code>totalCount</code> and <code>pageInfo</code>, ignoring fields that belong to a connection nested inside. The response half walks the returned tree, finds the same connections wherever they ended up, and reports the returned count against the true count with the path that reaches it. One query is sent, after the document has been checked for a mutation or a subscription and refused if it contains either.",
"py_file": "github_graphql_nested.py",
"py": '''"""Find nested GraphQL connections that truncated once per parent.

Read only, and queries only. GitHub's GraphQL endpoint takes a document in the
request body, so a read is carried by POST there just as a write would be; that
is transport, not intent. This script sends queries and refuses any document
containing a mutation or a subscription before it opens a socket. Nothing is
written and the repair is printed rather than performed.

Every connection carries its own cursor. Paginating the outer connection does
nothing for the inner ones: each new outer page restarts them from the start, so
each parent returns its first n children and stops, with no error and no marker.
The evidence is totalCount sitting next to a shorter list of nodes, once per
parent, and pageInfo.hasNextPage coming back true on a connection nobody
intended to follow.

What this can and cannot see: the API cannot tell whether your client follows a
cursor. What it can do is measure one response, report every connection that
returned fewer items than it holds, name the connections that asked for neither
totalCount nor pageInfo and therefore cannot be checked at all, and count the
follow-up queries that doing it properly would cost.

Environment:

    GITHUB_TOKEN    a token with read access to the GraphQL API
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_nested")

API = "https://api.github.com"
UA = "github-graphql-nested/1.0"

POINTS_PER_QUERY = 1

# Deliberately imperfect: the inner connection asks for totalCount but not for
# pageInfo, which is the common shape. It proves the truncation and gives you no
# cursor to continue from.
DEFAULT_QUERY = (
    "query($login: String!, $outer: Int = 5, $inner: Int = 5) {"
    " repositoryOwner(login: $login) {"
    " repositories(first: $outer, orderBy: {field: PUSHED_AT, direction: DESC}) {"
    " totalCount pageInfo { hasNextPage endCursor }"
    " nodes { name issues(first: $inner, states: OPEN) {"
    " totalCount nodes { number } } }"
    " } } }"
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


def outer_text(block):
    """A selection set with everything nested inside it blanked out. Pure.

    So that a pageInfo belonging to an inner connection is never credited to the
    connection that contains it, which is the mistake that makes a text-level
    audit of nested queries useless.
    """
    out, depth = [], 0
    for ch in str(block or ""):
        if ch == "{":
            depth += 1
            out.append(" ")
            continue
        if ch == "}":
            depth = max(0, depth - 1)
            out.append(" ")
            continue
        out.append(ch if depth == 0 else " ")
    return "".join(out)


def connection_fields(document, _depth=0, _stripped=False):
    """Every connection in the document, found by shape. Pure.

    A connection is a field whose own selection set contains nodes or edges.
    Identifying them that way rather than by their slicing argument means a
    connection paginated by a variable, or one written without arguments at all,
    is still found.
    """
    src = str(document or "") if _stripped else strip_noise(document)
    out, i, n, word, field = [], 0, len(src), "", ""
    while i < n:
        ch = src[i]
        if ch.isalnum() or ch == "_":
            word += ch
            i += 1
            continue
        # The field name has to survive the whitespace and the argument list
        # between it and its selection set, so it is remembered rather than
        # read off whatever happens to precede the brace.
        if word:
            field, word = word, ""
        if ch == "(":
            j, level = i, 0
            while j < n:
                if src[j] == "(":
                    level += 1
                elif src[j] == ")":
                    level -= 1
                    if level == 0:
                        break
                j += 1
            i = j + 1
            continue
        if ch == "{":
            j, level = i, 0
            while j < n:
                if src[j] == "{":
                    level += 1
                elif src[j] == "}":
                    level -= 1
                    if level == 0:
                        break
                j += 1
            block = src[i + 1:j]
            own = outer_text(block).split()
            if field and ("nodes" in own or "edges" in own):
                out.append({"field": field, "depth": _depth,
                            "has_page_info": "pageInfo" in own,
                            "has_total_count": "totalCount" in own})
                out.extend(connection_fields(block, _depth + 1, True))
            else:
                out.extend(connection_fields(block, _depth, True))
            i, field = j + 1, ""
            continue
        if ch == "}":
            field = ""
        i += 1
    return out


def unauditable(fields):
    """Inner connections that asked for neither totalCount nor pageInfo. Pure."""
    return [f for f in fields
            if f["depth"] >= 1 and not f["has_total_count"] and not f["has_page_info"]]


def unresumable(fields):
    """Inner connections that can be seen to truncate but not continued. Pure."""
    return [f for f in fields
            if f["depth"] >= 1 and f["has_total_count"] and not f["has_page_info"]]


def is_connection(value):
    """Whether a decoded object is a connection. Pure."""
    if not isinstance(value, dict):
        return False
    return isinstance(value.get("nodes"), list) or isinstance(value.get("edges"), list)


def walk_connections(data, path="", depth=0):
    """Every connection in a decoded response, with its path and depth. Pure.

    Depth counts connections above this one rather than keys, so an inner
    connection is depth 1 however many plain objects sit between it and its
    parent connection.
    """
    out = []
    if isinstance(data, dict):
        if is_connection(data):
            items = data.get("nodes")
            if not isinstance(items, list):
                items = data.get("edges") or []
            page = data.get("pageInfo")
            total = data.get("totalCount")
            out.append({
                "path": path or "(root)",
                "depth": depth,
                "returned": len(items),
                "total_count": total if isinstance(total, int) else None,
                "has_next_page": page.get("hasNextPage") if isinstance(page, dict) else None,
                "end_cursor": page.get("endCursor") if isinstance(page, dict) else None,
            })
            depth += 1
        for key, value in data.items():
            out.extend(walk_connections(value, key if not path else path + "." + key, depth))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            out.extend(walk_connections(item, "%s[%d]" % (path, index), depth))
    return out


def missing(entry):
    """Items this connection holds and did not return, or None. Pure."""
    total = entry.get("total_count")
    if not isinstance(total, int):
        return None
    return max(0, total - entry.get("returned", 0))


def truncated(entry):
    """Whether this connection stopped short of what it holds. Pure."""
    if entry.get("has_next_page") is True:
        return True
    gap = missing(entry)
    return bool(gap)


def auditable(entry):
    """Whether the response says anything at all about completeness. Pure."""
    return entry.get("total_count") is not None or entry.get("has_next_page") is not None


def resumable(entry):
    """Whether this connection can be continued without refetching its parent."""
    return bool(entry.get("end_cursor")) or entry.get("has_next_page") is not None


def followup_queries(entries):
    """Queries a correct inner walk would cost, from what this response shows.

    One per truncated parent at minimum, and more where the gap is wider than a
    single page of the size that was requested. Pure.
    """
    total = 0
    for entry in entries or []:
        if entry.get("depth", 0) < 1 or not truncated(entry):
            continue
        gap = missing(entry)
        page = entry.get("returned") or 0
        if gap and page > 0:
            total += -(-gap // page)
        else:
            total += 1
    return total


def classify(entries):
    """Classify one response. Pure. Returns (state, detail)."""
    if not entries:
        return ("no-connection-in-the-response",
                "nothing in this response has nodes or edges, so there is no "
                "connection here to be truncated.")
    inner = [e for e in entries if e["depth"] >= 1]
    inner_cut = [e for e in inner if truncated(e)]
    if inner_cut:
        gaps = [missing(e) for e in inner_cut if missing(e) is not None]
        return ("inner-connection-truncated",
                "%d of %d inner connection(s) returned fewer items than they "
                "contain and %s item(s) are missing with no error raised."
                % (len(inner_cut), len(inner),
                   sum(gaps) if gaps else "an unknown number of"))
    blind = [e for e in inner if not auditable(e)]
    if blind:
        return ("inner-connection-unauditable",
                "%d of %d inner connection(s) asked for neither totalCount nor "
                "pageInfo, so this response cannot say whether they truncated."
                % (len(blind), len(inner)))
    outer_cut = [e for e in entries if e["depth"] == 0 and truncated(e)]
    if outer_cut:
        return ("outer-connection-truncated",
                "the outer connection has more pages and every inner connection "
                "in it is complete. This is the truncation people do notice.")
    return ("complete",
            "every connection in this response returned everything it holds, so "
            "a total computed over it really is a total.")


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "inner-connection-truncated":
        return ("add pageInfo { hasNextPage endCursor } to every nested "
                "connection and walk each truncated parent separately with "
                "after: endCursor. An outer loop cannot do this for you.")
    if state == "inner-connection-unauditable":
        return ("add totalCount and pageInfo { hasNextPage endCursor } to the "
                "nested connections first. They cost nothing and without them "
                "nobody can tell whether this response is complete.")
    if state == "outer-connection-truncated":
        return ("follow the outer cursor as you already do, and keep checking "
                "the inner connections on every page: they restart from the "
                "beginning each time the outer one advances.")
    if state == "complete":
        return ("nothing here. Re-run it against a parent that really has more "
                "than one page of children, since a connection that fits cannot "
                "demonstrate a connection that does not.")
    return "point the query at something with a connection in it."


def point_cost(queries):
    """Points this run will spend. Pure."""
    return int(queries or 0) * POINTS_PER_QUERY


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
    ap.add_argument("--login", help="user or organisation to probe with the "
                                    "default query")
    ap.add_argument("--outer", type=int, default=5, help="outer page size")
    ap.add_argument("--inner", type=int, default=5, help="inner page size")
    ap.add_argument("--file", help="a .graphql file to send instead")
    ap.add_argument("--query", help="the document as a string")
    ap.add_argument("--variables", default="{}", help="JSON object of variables")
    args = ap.parse_args()

    if args.file:
        document = Path(args.file).read_text(encoding="utf-8")
    else:
        document = args.query or DEFAULT_QUERY

    try:
        variables = json.loads(args.variables)
    except ValueError:
        log.error("--variables takes a JSON object")
        return 2
    if not isinstance(variables, dict):
        log.error("--variables takes a JSON object")
        return 2
    if not args.file and not args.query:
        if not args.login:
            log.error("--login takes a user or organisation name")
            return 2
        variables.update({"login": args.login, "outer": args.outer,
                          "inner": args.inner})

    why_not = refusal(document)
    if why_not:
        log.error("refusing to send: %s", why_not)
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    log.info("point cost: %d point(s) against the 5,000/hour GraphQL budget",
             point_cost(1))

    fields = connection_fields(document)
    for f in unauditable(fields):
        log.info("document: %s asks for neither totalCount nor pageInfo, so no "
                 "response can say whether it truncated", f["field"])
    for f in unresumable(fields):
        log.info("document: %s asks for totalCount but not pageInfo, so "
                 "truncation is visible and cannot be resumed without "
                 "refetching the parent", f["field"])

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })
    status, body = run_query(session, document, variables)
    if not isinstance(body, dict):
        log.error("HTTP %s and no JSON body to read", status)
        return 2
    if body.get("errors"):
        log.error("the query itself failed: %s",
                  json.dumps(body["errors"])[:400])
        return 2

    entries = walk_connections(body.get("data") or {})
    for e in entries:
        gap = missing(e)
        note = "complete"
        if truncated(e):
            note = ("%s missing" % gap) if gap is not None else "more pages"
            if not resumable(e):
                note += ", no cursor"
        log.info("  %-46s depth %d  %d of %s  %s",
                 e["path"], e["depth"], e["returned"],
                 "?" if e["total_count"] is None else e["total_count"], note)

    state, detail = classify(entries)
    log.info("%s: %s", state, detail)
    follow = followup_queries(entries)
    if follow:
        log.info("following them properly costs %d more quer%s, at least one "
                 "per truncated parent", follow, "y" if follow == 1 else "ies")
    log.info("repair: %s", repair(state))

    print(json.dumps({"points_spent": point_cost(1), "state": state,
                      "followup_queries": follow, "connections": entries,
                      "document": fields}, indent=2, default=str))
    return 1 if state in ("inner-connection-truncated",
                          "inner-connection-unauditable") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-nested.mjs",
"js": '''/**
 * Find nested GraphQL connections that truncated once per parent.
 *
 * Read only, and queries only. GitHub's GraphQL endpoint takes a document in
 * the request body, so a read is carried by POST there just as a write would
 * be; that is transport, not intent. Any document containing a mutation or a
 * subscription is refused before a socket opens.
 *
 * Environment:
 *   GITHUB_TOKEN      a token with read access to the GraphQL API
 *   GITHUB_LOGIN      user or organisation to probe with the default query
 *   GITHUB_OUTER      outer page size (default 5)
 *   GITHUB_INNER      inner page size (default 5)
 *   GITHUB_QUERY      the document as a string
 *   GITHUB_VARIABLES  JSON object of variables
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-nested/1.0';

export const POINTS_PER_QUERY = 1;

const DEFAULT_QUERY = 'query($login: String!, $outer: Int = 5, $inner: Int = 5) {'
  + ' repositoryOwner(login: $login) {'
  + ' repositories(first: $outer, orderBy: {field: PUSHED_AT, direction: DESC}) {'
  + ' totalCount pageInfo { hasNextPage endCursor }'
  + ' nodes { name issues(first: $inner, states: OPEN) {'
  + ' totalCount nodes { number } } }'
  + ' } } }';

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

/** A selection set with everything nested inside it blanked out. Pure. */
export function outerText(block) {
  const out = [];
  let depth = 0;
  for (const ch of String(block ?? '')) {
    if (ch === '{') { depth += 1; out.push(' '); continue; }
    if (ch === '}') { depth = Math.max(0, depth - 1); out.push(' '); continue; }
    out.push(depth === 0 ? ch : ' ');
  }
  return out.join('');
}

/** Every connection in the document, found by shape. Pure. */
export function connectionFields(document, depthIn = 0, stripped = false) {
  const src = stripped ? String(document ?? '') : stripNoise(document);
  const out = [];
  let i = 0;
  let word = '';
  let field = '';
  while (i < src.length) {
    const ch = src[i];
    if (/[A-Za-z0-9_]/.test(ch)) { word += ch; i += 1; continue; }
    // The field name has to survive the whitespace and the argument list
    // between it and its selection set, so it is remembered rather than read
    // off whatever happens to precede the brace.
    if (word) { field = word; word = ''; }
    if (ch === '(') {
      let j = i;
      let level = 0;
      while (j < src.length) {
        if (src[j] === '(') level += 1;
        else if (src[j] === ')') { level -= 1; if (level === 0) break; }
        j += 1;
      }
      i = j + 1;
      continue;
    }
    if (ch === '{') {
      let j = i;
      let level = 0;
      while (j < src.length) {
        if (src[j] === '{') level += 1;
        else if (src[j] === '}') { level -= 1; if (level === 0) break; }
        j += 1;
      }
      const block = src.slice(i + 1, j);
      const own = outerText(block).split(/\\s+/).filter(Boolean);
      if (field && (own.includes('nodes') || own.includes('edges'))) {
        out.push({
          field,
          depth: depthIn,
          has_page_info: own.includes('pageInfo'),
          has_total_count: own.includes('totalCount'),
        });
        out.push(...connectionFields(block, depthIn + 1, true));
      } else {
        out.push(...connectionFields(block, depthIn, true));
      }
      i = j + 1;
      field = '';
      continue;
    }
    if (ch === '}') field = '';
    i += 1;
  }
  return out;
}

/** Inner connections that asked for neither totalCount nor pageInfo. Pure. */
export function unauditable(fields) {
  return (fields || []).filter((f) => f.depth >= 1 && !f.has_total_count && !f.has_page_info);
}

/** Inner connections that can be seen to truncate but not continued. Pure. */
export function unresumable(fields) {
  return (fields || []).filter((f) => f.depth >= 1 && f.has_total_count && !f.has_page_info);
}

/** Whether a decoded object is a connection. Pure. */
export function isConnection(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  return Array.isArray(value.nodes) || Array.isArray(value.edges);
}

/** Every connection in a decoded response, with its path and depth. Pure. */
export function walkConnections(data, path = '', depth = 0) {
  const out = [];
  if (Array.isArray(data)) {
    data.forEach((item, index) => {
      out.push(...walkConnections(item, `${path}[${index}]`, depth));
    });
    return out;
  }
  if (!data || typeof data !== 'object') return out;
  let next = depth;
  if (isConnection(data)) {
    const items = Array.isArray(data.nodes) ? data.nodes : (data.edges || []);
    const page = (data.pageInfo && typeof data.pageInfo === 'object') ? data.pageInfo : null;
    out.push({
      path: path || '(root)',
      depth,
      returned: items.length,
      total_count: Number.isInteger(data.totalCount) ? data.totalCount : null,
      has_next_page: page ? page.hasNextPage : null,
      end_cursor: page ? page.endCursor : null,
    });
    next = depth + 1;
  }
  for (const [key, value] of Object.entries(data)) {
    out.push(...walkConnections(value, path ? `${path}.${key}` : key, next));
  }
  return out;
}

/** Items this connection holds and did not return, or null. Pure. */
export function missing(entry) {
  const total = entry && entry.total_count;
  if (!Number.isInteger(total)) return null;
  return Math.max(0, total - ((entry && entry.returned) || 0));
}

/** Whether this connection stopped short of what it holds. Pure. */
export function truncated(entry) {
  if (entry && entry.has_next_page === true) return true;
  return !!missing(entry);
}

/** Whether the response says anything at all about completeness. Pure. */
export function auditable(entry) {
  if (!entry) return false;
  return entry.total_count !== null || (entry.has_next_page !== null
    && entry.has_next_page !== undefined);
}

/** Whether this connection can be continued without refetching its parent. */
export function resumable(entry) {
  if (!entry) return false;
  return !!entry.end_cursor || (entry.has_next_page !== null
    && entry.has_next_page !== undefined);
}

/** Queries a correct inner walk would cost, from what this response shows. */
export function followupQueries(entries) {
  let total = 0;
  for (const entry of entries || []) {
    if ((entry.depth || 0) < 1 || !truncated(entry)) continue;
    const gap = missing(entry);
    const page = entry.returned || 0;
    if (gap && page > 0) total += Math.ceil(gap / page);
    else total += 1;
  }
  return total;
}

/** Classify one response. Pure. Returns [state, detail]. */
export function classify(entries) {
  if (!entries || entries.length === 0) {
    return ['no-connection-in-the-response', 'nothing in this response has '
      + 'nodes or edges, so there is no connection here to be truncated.'];
  }
  const inner = entries.filter((e) => e.depth >= 1);
  const innerCut = inner.filter((e) => truncated(e));
  if (innerCut.length) {
    const gaps = innerCut.map((e) => missing(e)).filter((g) => g !== null);
    const sum = gaps.length ? gaps.reduce((a, b) => a + b, 0) : 'an unknown number of';
    return ['inner-connection-truncated',
      `${innerCut.length} of ${inner.length} inner connection(s) returned fewer `
      + `items than they contain and ${sum} item(s) are missing with no error raised.`];
  }
  const blind = inner.filter((e) => !auditable(e));
  if (blind.length) {
    return ['inner-connection-unauditable',
      `${blind.length} of ${inner.length} inner connection(s) asked for neither `
      + 'totalCount nor pageInfo, so this response cannot say whether they truncated.'];
  }
  const outerCut = entries.filter((e) => e.depth === 0 && truncated(e));
  if (outerCut.length) {
    return ['outer-connection-truncated', 'the outer connection has more pages '
      + 'and every inner connection in it is complete. This is the truncation '
      + 'people do notice.'];
  }
  return ['complete', 'every connection in this response returned everything it '
    + 'holds, so a total computed over it really is a total.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'inner-connection-truncated') {
    return 'add pageInfo { hasNextPage endCursor } to every nested connection '
      + 'and walk each truncated parent separately with after: endCursor. An '
      + 'outer loop cannot do this for you.';
  }
  if (state === 'inner-connection-unauditable') {
    return 'add totalCount and pageInfo { hasNextPage endCursor } to the nested '
      + 'connections first. They cost nothing and without them nobody can tell '
      + 'whether this response is complete.';
  }
  if (state === 'outer-connection-truncated') {
    return 'follow the outer cursor as you already do, and keep checking the '
      + 'inner connections on every page: they restart from the beginning each '
      + 'time the outer one advances.';
  }
  if (state === 'complete') {
    return 'nothing here. Re-run it against a parent that really has more than '
      + 'one page of children, since a connection that fits cannot demonstrate '
      + 'a connection that does not.';
  }
  return 'point the query at something with a connection in it.';
}

/** Points this run will spend. Pure. */
export function pointCost(queries) {
  return Number(queries || 0) * POINTS_PER_QUERY;
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
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const document = process.env.GITHUB_QUERY || DEFAULT_QUERY;
  let variables = {};
  try { variables = JSON.parse(process.env.GITHUB_VARIABLES || '{}'); } catch {
    console.error('GITHUB_VARIABLES takes a JSON object');
    process.exitCode = 2;
    return;
  }
  if (!process.env.GITHUB_QUERY) {
    if (!process.env.GITHUB_LOGIN) {
      console.error('set GITHUB_LOGIN to a user or organisation name');
      process.exitCode = 2;
      return;
    }
    variables.login = process.env.GITHUB_LOGIN;
    variables.outer = Number(process.env.GITHUB_OUTER || 5);
    variables.inner = Number(process.env.GITHUB_INNER || 5);
  }

  const whyNot = refusal(document);
  if (whyNot) {
    console.error(`refusing to send: ${whyNot}`);
    process.exitCode = 2;
    return;
  }

  console.log(`point cost: ${pointCost(1)} point(s) against the 5,000/hour GraphQL budget`);
  const fields = connectionFields(document);
  for (const f of unauditable(fields)) {
    console.log(`document: ${f.field} asks for neither totalCount nor pageInfo, `
      + 'so no response can say whether it truncated');
  }
  for (const f of unresumable(fields)) {
    console.log(`document: ${f.field} asks for totalCount but not pageInfo, so `
      + 'truncation is visible and cannot be resumed without refetching the parent');
  }

  const { status, body } = await runQuery(token, document, variables);
  if (!body || typeof body !== 'object') {
    console.error(`HTTP ${status} and no JSON body to read`);
    process.exitCode = 2;
    return;
  }
  if (Array.isArray(body.errors) && body.errors.length) {
    console.error(`the query itself failed: ${JSON.stringify(body.errors).slice(0, 400)}`);
    process.exitCode = 2;
    return;
  }

  const entries = walkConnections(body.data || {});
  for (const e of entries) {
    const gap = missing(e);
    let note = 'complete';
    if (truncated(e)) {
      note = gap !== null ? `${gap} missing` : 'more pages';
      if (!resumable(e)) note += ', no cursor';
    }
    console.log(`  ${e.path}  depth ${e.depth}  ${e.returned} of `
      + `${e.total_count === null ? '?' : e.total_count}  ${note}`);
  }

  const [state, detail] = classify(entries);
  console.log(`${state}: ${detail}`);
  const follow = followupQueries(entries);
  if (follow) {
    console.log(`following them properly costs ${follow} more `
      + `${follow === 1 ? 'query' : 'queries'}, at least one per truncated parent`);
  }
  console.log(`repair: ${repair(state)}`);

  console.log(JSON.stringify({
    points_spent: pointCost(1), state, followup_queries: follow,
    connections: entries, document: fields,
  }, null, 2));
  process.exitCode = ['inner-connection-truncated',
    'inner-connection-unauditable'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The response fixture is a real shape: one outer connection with a cursor and three parents underneath it, one of which is complete and two of which are not. The walk is asserted to find the inner connections by path and to give them a depth greater than the outer one, and the arithmetic is asserted per parent rather than in total, which is the point of the note. The text side gets its own test that an inner connection's <code>pageInfo</code> is never credited to the connection that contains it, because that single mistake would make the document audit report the opposite of the truth.",
"test_py_file": "test_github_graphql_nested.py",
"test_py": '''from github_graphql_nested import (
    POINTS_PER_QUERY, auditable, classify, connection_fields, followup_queries,
    is_connection, missing, operations, outer_text, point_cost, refusal, repair,
    resumable, truncated, unauditable, unresumable, walk_connections,
)

DATA = {"repositoryOwner": {"repositories": {
    "totalCount": 218,
    "pageInfo": {"hasNextPage": True, "endCursor": "Y3Vyc29yOjU="},
    "nodes": [
        {"name": "monorepo",
         "issues": {"totalCount": 406, "nodes": [{"number": 1}, {"number": 2}]}},
        {"name": "tiny",
         "issues": {"totalCount": 2, "nodes": [{"number": 9}, {"number": 10}]}},
    ],
}}}

NESTED_QUERY = ("query { repositoryOwner(login: \\"acme\\") {"
                " repositories(first: 5) { totalCount"
                " pageInfo { hasNextPage endCursor }"
                " nodes { name issues(first: 5) { totalCount nodes { number } } } } } }")


def test_the_walk_finds_inner_connections_by_path():
    entries = walk_connections(DATA)
    paths = [e["path"] for e in entries]
    assert "repositoryOwner.repositories" in paths
    assert "repositoryOwner.repositories.nodes[0].issues" in paths
    assert "repositoryOwner.repositories.nodes[1].issues" in paths


def test_an_inner_connection_is_deeper_than_the_one_containing_it():
    by_path = {e["path"]: e for e in walk_connections(DATA)}
    assert by_path["repositoryOwner.repositories"]["depth"] == 0
    assert by_path["repositoryOwner.repositories.nodes[0].issues"]["depth"] == 1


def test_truncation_is_measured_per_parent_and_not_in_total():
    by_path = {e["path"]: e for e in walk_connections(DATA)}
    big = by_path["repositoryOwner.repositories.nodes[0].issues"]
    small = by_path["repositoryOwner.repositories.nodes[1].issues"]
    assert missing(big) == 404
    assert truncated(big)
    assert missing(small) == 0
    assert not truncated(small)


def test_has_next_page_alone_is_enough_to_call_it_truncated():
    entry = {"depth": 1, "returned": 100, "total_count": None,
             "has_next_page": True, "end_cursor": "abc"}
    assert truncated(entry)
    assert missing(entry) is None
    assert auditable(entry)


def test_a_connection_with_neither_field_cannot_be_judged_at_all():
    entry = {"depth": 1, "returned": 100, "total_count": None,
             "has_next_page": None, "end_cursor": None}
    assert not auditable(entry)
    assert not truncated(entry)
    state, detail = classify([{"depth": 0, "returned": 5, "total_count": 5,
                               "has_next_page": False, "end_cursor": None}, entry])
    assert state == "inner-connection-unauditable"
    assert "neither totalCount nor pageInfo" in detail


def test_seeing_the_gap_and_being_able_to_resume_it_are_different():
    seen_only = {"depth": 1, "returned": 5, "total_count": 406,
                 "has_next_page": None, "end_cursor": None}
    assert truncated(seen_only)
    assert not resumable(seen_only)
    assert resumable({"depth": 1, "returned": 5, "total_count": 406,
                      "has_next_page": True, "end_cursor": "abc"})


def test_the_inner_truncation_outranks_the_outer_one():
    state, detail = classify(walk_connections(DATA))
    assert state == "inner-connection-truncated"
    assert "404" in detail
    assert "after: endCursor" in repair(state)


def test_an_outer_only_truncation_is_named_as_the_one_people_notice():
    data = {"repositories": {"totalCount": 218,
                             "pageInfo": {"hasNextPage": True, "endCursor": "c"},
                             "nodes": [{"name": "tiny",
                                        "issues": {"totalCount": 2,
                                                   "nodes": [{"number": 1}, {"number": 2}]}}]}}
    state, detail = classify(walk_connections(data))
    assert state == "outer-connection-truncated"
    assert "do notice" in detail


def test_a_complete_response_is_not_reported_as_a_finding():
    data = {"repositories": {"totalCount": 1,
                             "pageInfo": {"hasNextPage": False, "endCursor": None},
                             "nodes": [{"name": "tiny",
                                        "issues": {"totalCount": 1,
                                                   "nodes": [{"number": 1}]}}]}}
    assert classify(walk_connections(data))[0] == "complete"
    assert classify([])[0] == "no-connection-in-the-response"


def test_an_inner_page_info_is_never_credited_to_its_parent():
    doc = ("query { a(first: 10) { totalCount nodes {"
           " b(first: 10) { pageInfo { hasNextPage } nodes { id } } } } }")
    fields = {f["field"]: f for f in connection_fields(doc)}
    assert fields["a"]["has_total_count"] and not fields["a"]["has_page_info"]
    assert fields["b"]["has_page_info"] and not fields["b"]["has_total_count"]
    assert fields["a"]["depth"] == 0 and fields["b"]["depth"] == 1
    assert "pageInfo" not in outer_text(" totalCount nodes { pageInfo { x } } ")


def test_the_document_audit_names_what_cannot_be_checked_or_resumed():
    fields = connection_fields(NESTED_QUERY)
    assert [f["field"] for f in unresumable(fields)] == ["issues"]
    assert unauditable(fields) == []
    bare = "query { a(first: 5) { nodes { b(first: 5) { nodes { id } } } } }"
    assert [f["field"] for f in unauditable(connection_fields(bare))] == ["b"]


def test_a_connection_is_recognised_by_nodes_or_edges():
    assert is_connection({"nodes": []})
    assert is_connection({"edges": []})
    assert not is_connection({"nodes": 3})
    assert not is_connection({"name": "monorepo"})


def test_the_cost_of_doing_it_properly_is_counted_before_the_loop_is_written():
    assert followup_queries(walk_connections(DATA)) == 202
    assert followup_queries([]) == 0
    assert POINTS_PER_QUERY == 1
    assert point_cost(1) == 1
    assert point_cost(0) == 0


def test_the_script_refuses_to_send_a_mutation():
    assert operations("query Q { viewer { login } }") == ["query"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal("subscription S { thing { id } }")
    assert refusal(NESTED_QUERY) is None
''',
"test_js_file": "github-graphql-nested.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  POINTS_PER_QUERY, auditable, classify, connectionFields, followupQueries,
  isConnection, missing, operations, outerText, pointCost, refusal, repair,
  resumable, truncated, unauditable, unresumable, walkConnections,
} from './github-graphql-nested.mjs';

const DATA = {
  repositoryOwner: {
    repositories: {
      totalCount: 218,
      pageInfo: { hasNextPage: true, endCursor: 'Y3Vyc29yOjU=' },
      nodes: [
        { name: 'monorepo', issues: { totalCount: 406, nodes: [{ number: 1 }, { number: 2 }] } },
        { name: 'tiny', issues: { totalCount: 2, nodes: [{ number: 9 }, { number: 10 }] } },
      ],
    },
  },
};

const NESTED_QUERY = 'query { repositoryOwner(login: "acme") {'
  + ' repositories(first: 5) { totalCount'
  + ' pageInfo { hasNextPage endCursor }'
  + ' nodes { name issues(first: 5) { totalCount nodes { number } } } } } }';

test('the walk finds inner connections by path', () => {
  const paths = walkConnections(DATA).map((e) => e.path);
  assert.ok(paths.includes('repositoryOwner.repositories'));
  assert.ok(paths.includes('repositoryOwner.repositories.nodes[0].issues'));
  assert.ok(paths.includes('repositoryOwner.repositories.nodes[1].issues'));
});

test('an inner connection is deeper than the one containing it', () => {
  const byPath = Object.fromEntries(walkConnections(DATA).map((e) => [e.path, e]));
  assert.equal(byPath['repositoryOwner.repositories'].depth, 0);
  assert.equal(byPath['repositoryOwner.repositories.nodes[0].issues'].depth, 1);
});

test('truncation is measured per parent and not in total', () => {
  const byPath = Object.fromEntries(walkConnections(DATA).map((e) => [e.path, e]));
  const big = byPath['repositoryOwner.repositories.nodes[0].issues'];
  const small = byPath['repositoryOwner.repositories.nodes[1].issues'];
  assert.equal(missing(big), 404);
  assert.ok(truncated(big));
  assert.equal(missing(small), 0);
  assert.ok(!truncated(small));
});

test('has next page alone is enough to call it truncated', () => {
  const entry = {
    depth: 1, returned: 100, total_count: null, has_next_page: true, end_cursor: 'abc',
  };
  assert.ok(truncated(entry));
  assert.equal(missing(entry), null);
  assert.ok(auditable(entry));
});

test('a connection with neither field cannot be judged at all', () => {
  const entry = {
    depth: 1, returned: 100, total_count: null, has_next_page: null, end_cursor: null,
  };
  assert.ok(!auditable(entry));
  assert.ok(!truncated(entry));
  const [state, detail] = classify([{
    depth: 0, returned: 5, total_count: 5, has_next_page: false, end_cursor: null,
  }, entry]);
  assert.equal(state, 'inner-connection-unauditable');
  assert.match(detail, /neither totalCount nor pageInfo/);
});

test('seeing the gap and being able to resume it are different', () => {
  const seenOnly = {
    depth: 1, returned: 5, total_count: 406, has_next_page: null, end_cursor: null,
  };
  assert.ok(truncated(seenOnly));
  assert.ok(!resumable(seenOnly));
  assert.ok(resumable({
    depth: 1, returned: 5, total_count: 406, has_next_page: true, end_cursor: 'abc',
  }));
});

test('the inner truncation outranks the outer one', () => {
  const [state, detail] = classify(walkConnections(DATA));
  assert.equal(state, 'inner-connection-truncated');
  assert.match(detail, /404/);
  assert.match(repair(state), /after: endCursor/);
});

test('an outer only truncation is named as the one people notice', () => {
  const data = {
    repositories: {
      totalCount: 218,
      pageInfo: { hasNextPage: true, endCursor: 'c' },
      nodes: [{ name: 'tiny', issues: { totalCount: 2, nodes: [{ number: 1 }, { number: 2 }] } }],
    },
  };
  const [state, detail] = classify(walkConnections(data));
  assert.equal(state, 'outer-connection-truncated');
  assert.match(detail, /do notice/);
});

test('a complete response is not reported as a finding', () => {
  const data = {
    repositories: {
      totalCount: 1,
      pageInfo: { hasNextPage: false, endCursor: null },
      nodes: [{ name: 'tiny', issues: { totalCount: 1, nodes: [{ number: 1 }] } }],
    },
  };
  assert.equal(classify(walkConnections(data))[0], 'complete');
  assert.equal(classify([])[0], 'no-connection-in-the-response');
});

test('an inner page info is never credited to its parent', () => {
  const doc = 'query { a(first: 10) { totalCount nodes {'
    + ' b(first: 10) { pageInfo { hasNextPage } nodes { id } } } } }';
  const fields = Object.fromEntries(connectionFields(doc).map((f) => [f.field, f]));
  assert.ok(fields.a.has_total_count && !fields.a.has_page_info);
  assert.ok(fields.b.has_page_info && !fields.b.has_total_count);
  assert.equal(fields.a.depth, 0);
  assert.equal(fields.b.depth, 1);
  assert.ok(!outerText(' totalCount nodes { pageInfo { x } } ').includes('pageInfo'));
});

test('the document audit names what cannot be checked or resumed', () => {
  const fields = connectionFields(NESTED_QUERY);
  assert.deepEqual(unresumable(fields).map((f) => f.field), ['issues']);
  assert.deepEqual(unauditable(fields), []);
  const bare = 'query { a(first: 5) { nodes { b(first: 5) { nodes { id } } } } }';
  assert.deepEqual(unauditable(connectionFields(bare)).map((f) => f.field), ['b']);
});

test('a connection is recognised by nodes or edges', () => {
  assert.ok(isConnection({ nodes: [] }));
  assert.ok(isConnection({ edges: [] }));
  assert.ok(!isConnection({ nodes: 3 }));
  assert.ok(!isConnection({ name: 'monorepo' }));
});

test('the cost of doing it properly is counted before the loop is written', () => {
  assert.equal(followupQueries(walkConnections(DATA)), 202);
  assert.equal(followupQueries([]), 0);
  assert.equal(POINTS_PER_QUERY, 1);
  assert.equal(pointCost(1), 1);
  assert.equal(pointCost(0), 0);
});

test('the script refuses to send a mutation', () => {
  assert.deepEqual(operations('query Q { viewer { login } }'), ['query']);
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.ok(refusal('subscription S { thing { id } }'));
  assert.equal(refusal(NESTED_QUERY), null);
});
''',
"faq": [
 ("Can I pass a cursor to the inner connection and page everything in one query?",
  "Only for one parent at a time, which is the point. An inner after: argument applies to every instance of that connection in the response, so supplying a cursor taken from repository A and applying it to repository B is meaningless: cursors are opaque and scoped to the connection they came from. Correct nested pagination is an outer walk plus a separate, parent-scoped query for each parent that has more, and there is no single document that expresses it."),
 ("Is totalCount reliable enough to compare against?",
  "For this purpose, yes. It is the count the connection reports for the filters you applied, so as long as you compare it against the nodes from the same response it answers exactly the question being asked, which is whether this connection gave you everything. Do not treat it as a snapshot of the world: it can move between calls, and on very large or heavily filtered connections it is a count the server computes rather than a number you should reconcile against another system."),
 ("Why not just set the inner first to 100 and accept the loss?",
  "Because the loss is silent and unbounded, which is a different thing from a documented cap. A hundred is enough for most parents and wrong for exactly the ones that matter, since the repositories with the most pull requests are usually the ones being reported on. If truncating is genuinely acceptable, make it explicit: read totalCount as well, and publish the number as a floor rather than a total, so the report says what it is."),
 ("How much does correct nested pagination cost?",
  "One query per truncated parent at least, and more where a parent has several pages of children. Four hundred repositories with more pull requests than fit is four hundred extra calls, each with its own point cost, so this is a real budget decision rather than a free correction. The script counts the follow-ups the response it saw implies, which is the number to take into the decision. What the budget is and how fast you can spend it is a separate note."),
 ("Is this the same bug as not following the Link header in REST?",
  "It is the same family and it behaves differently enough to need its own check. In REST the loss happens once, on one list, and the Link header hands you a rel=\"last\" that gives you the true page count for free. Here there is no Link header, the loss happens once per parent so it multiplies, and the only evidence is a totalCount you have to have asked for. A client can also be completely correct about the REST version and still have this one."),
],
"related": [
 ("/github/link-header-not-followed/", "The REST version: only the first page is read"),
 ("/github/graphql-first-over-100/", "A connection asks for more than 100 and is rejected"),
 ("/github/graphql-node-limit-exceeded/", "Asking for too much in one document"),
],
"citations": [CITE_GQL_PAGINATION, CITE_RELAY_CONNECTIONS, CITE_GQL_FORMING, CITE_REST_PAGINATION],
},

{
"slug": "graphql-cost-not-measured",
"title": "Nobody measured what the GraphQL query actually costs",
"description": "A query's point cost comes from the connections it could traverse, not the data it returns, so a query returning twelve rows can quietly cost fourteen points.",
"h1": "Nobody measured what the GraphQL query actually costs",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github graphql query cost points",
             "github graphql rateLimit cost field",
             "how much does a github graphql query cost",
             "github graphql cost calculation connections",
             "github graphql query price nodeCount"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The dashboard query has been running every fifteen seconds for a year. Last Tuesday somebody added one nested field to it, the review was two lines long and entirely reasonable, and on Thursday afternoon the whole integration started returning <code>RATE_LIMITED</code> at about ten past two. Nothing in the pull request said the price had gone from three points to fourteen, because nobody had ever written down that it was three.",
"short_answer": """<p>Ask the server. Adding <code>rateLimit { cost nodeCount remaining }</code> to a query makes every response report its own price, and that price is the only authoritative number: the cost is derived from how many connections the query <em>could</em> traverse and how many items each was asked for, not from how much data came back. A query returning twelve rows can legitimately cost fourteen points.</p>
<p>Then compare that measurement against two other numbers. The first is what the query text predicts, which is roughly the sum of the <code>first</code> and <code>last</code> values divided by 100 — if the server charges several times that, something in the document is traversing more than it looks like it does. The second is what it cost last time. Recording a cost per query shape and alerting when a deploy changes it is the whole discipline, and it is what turns a mid-afternoon outage into a line in a diff.</p>""",
"problem": """<p>The reason nobody measures it is that the first version is cheap and works. A GraphQL query written to replace a hundred REST calls costs one or two points, comes back fast, and drops the REST quota problem off the board entirely. That is a success, and successes do not get instrumented. The cost field exists, it is documented, and there is no reason to add it to a query that is obviously fine.</p>
<p>Then the query grows the way every useful query grows: one field at a time, each added by somebody solving a real problem, each reviewed on its own. A nested connection here, a wider <code>first</code> there, a second connection alongside the first because the dashboard needed one more column. Every one of those diffs is small and none of them mentions points, because the price is not written anywhere for the diff to change.</p>
<p>What makes the eventual failure so confusing is the timing. The quota does not degrade; it holds up perfectly until a threshold, and then every call fails for the rest of the hour and works again after the reset. So it looks like an incident rather than a change, and the search goes to infrastructure, deploys, GitHub status pages and concurrency, when the actual cause is a field added on Tuesday to a query nobody had priced.</p>""",
"why": """<p><strong>Cost is a property of the request, not of the response.</strong> GitHub computes it from the number of connections the query could traverse and the slice each one asked for. A query that asks for a hundred items and finds three still asked for a hundred. This is why "it only returns a few rows" is never an argument about price, and why the cheapest way to make a query cheaper is almost always to lower a <code>first</code> rather than to filter harder.</p>
<p><strong>The server will tell you, in band, for free.</strong> <code>rateLimit { cost nodeCount limit remaining resetAt }</code> can be added to a query you were already sending, and it comes back in the same response with no extra round trip. That makes the measurement essentially free once, and continuous if you log it. There is no server-side history of your query costs to consult afterwards, so if you do not record it, it is gone.</p>
<p><strong>Predicting from the text is useful precisely where it is wrong.</strong> The documented approximation is the sum of the <code>first</code> and <code>last</code> values divided by 100, rounded, with a minimum of one. When the server agrees, the document says what it does. When the server charges several times more, the query is traversing something the arithmetic did not see, and that disagreement is worth more than either number on its own.</p>
<p><strong>Cost drift is a code review problem, not an operations problem.</strong> The change that breaks the budget arrives in a pull request, not in an alert, and it arrives weeks before the failure. A recorded cost per query shape turns that into a reviewable fact: this query was 3, this diff makes it 14, is that intended. Without the record there is nothing for a reviewer to react to.</p>
<p><strong>This is not the budget, and it is not the node limit.</strong> How many points you have left, which bucket they came from and how fast you may spend them is <a href="/github/graphql-rate-limited/">a separate note that owns the budget</a>. Whether the query is so large it will be rejected before it runs is <a href="/github/graphql-node-limit-exceeded/">a third note that owns the node ceiling</a>. This one owns a narrower question: what does this particular query shape cost, and is that what its author believes. A query can be comfortably inside both limits and still be four times the price anybody thinks it is.</p>
<p><strong>The measurement costs one point and is only about this shape.</strong> Sending the query once to measure it spends a point, which the script prints before it spends. And the number belongs to the shape rather than to the target: pointing the same document at a larger organisation does not change the price, which is the whole reason a baseline recorded once stays useful.</p>""",
"steps": [
 {"h": "Predict the cost from the query text before you send it",
  "body": """<p>The script sums the <code>first</code> and <code>last</code> values it can resolve, divides by 100 and prints the result with the arguments that produced it. This is free and it is a prediction rather than an answer. Its value is as something for the measurement to disagree with.</p>"""},
 {"h": "Inject rateLimit and measure the real price once",
  "body": """<p>The script inserts <code>rateLimit { cost nodeCount limit remaining resetAt }</code> into the document's top-level selection set and sends it, which costs one point and returns the server's own number. If the document already asks for it, nothing is changed. This is the authoritative figure and everything else is compared against it.</p>"""},
 {"h": "Compare it against what the caller assumed",
  "body": """<p>Pass <code>--assumed</code> with the number in somebody's head or in the scheduling comment. A query believed to cost 1 and charging 14 is not a tuning opportunity, it is a fourteenfold error in every capacity calculation built on it, and stating the ratio out loud is what gets it fixed.</p>"""},
 {"h": "Compare it against what it cost last time",
  "body": """<p>Point <code>--baseline</code> at a JSON file of recorded costs per query name. The script reports whether this shape has become more expensive since the file was written and by how much. Run it in CI on the queries a repository ships and the price change arrives as a review comment rather than as an outage.</p>"""},
 {"h": "Check the price against the data, then take the budget elsewhere",
  "body": """<p>The script counts the nodes actually returned beside the points charged, because seeing 12 rows for 14 points is what finally kills the idea that cost follows data. It also projects an hourly total for a given call rate. What that total means against your quota belongs to the budget note, and the script says so rather than repeating it.</p>"""},
],
"verify": """<p>Three numbers for one query: what the text predicts, what the server charges, and what somebody assumed.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_cost.py \\
    --file queries/dashboard.graphql --name dashboard --assumed 1 \\
    --baseline costs.json --calls-per-hour 240
# point cost: 1 point(s) against the 5,000/hour GraphQL budget
# predicted from the text: 3 point(s) from 4 slicing argument(s) totalling 220
# measured by the server: 14 point(s), nodeCount 3,180
# assumed by the caller: 1 point(s); recorded baseline: 3 point(s)
# cost-increased-since-the-baseline: this shape cost 3 point(s) when the
# baseline was written and costs 14 now, a rise of 367%
# 12 node(s) came back for 14 point(s), so the price is not the size of the answer
# at 240 call(s)/hour this shape needs 3,360 points/hour
# repair: record the new cost against the shape and treat the change as part of
# the diff that caused it. Add this line to costs.json: "dashboard": 14</code></pre>""",
"code_intro": "Two numbers and their disagreement. The prediction is pure text: blank out the comments and string literals, walk the argument lists, resolve each <code>first</code> and <code>last</code> through literals, variable defaults and the variables map, and apply the documented approximation. The measurement needs one query, so the script performs the surgery that gets it — inserting <code>rateLimit</code> into the document's top-level selection set, and only there, which is why the noise is blanked to spaces rather than removed and the index still lines up with the original text. As everywhere in this section, a document containing a mutation or a subscription is refused before a socket opens.",
"py_file": "github_graphql_cost.py",
"py": '''"""Measure what a GraphQL query costs and compare it with what anybody assumed.

Read only, and queries only. GitHub's GraphQL endpoint takes a document in the
request body, so a read is carried by POST there just as a write would be; that
is transport, not intent. This script sends queries and refuses any document
containing a mutation or a subscription before it opens a socket. Nothing is
written -- including the baseline file, which is printed for you to update
rather than rewritten here.

A query's point cost is computed from the connections it could traverse and the
slice each one asked for, not from the data that came back, so a query returning
a dozen rows can cost more than a dozen points. The server reports the number in
band if you ask for it, and there is no server-side history of what your queries
cost, so a price nobody recorded is a price nobody can compare against.

What this can and cannot see: the measurement is authoritative for the document
and variables handed to it. It cannot see the other shapes your integration
sends, and it cannot attribute the budget's drain to any of them, because the
bucket is shared by every process holding the token.

Environment:

    GITHUB_TOKEN    a token with read access to the GraphQL API
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_cost")

API = "https://api.github.com"
UA = "github-graphql-cost/1.0"

POINTS_PER_QUERY = 1

# The selection that makes a response report its own price. Cheap to carry: it
# adds no round trip and the response is one object longer.
RATE_LIMIT_SELECTION = "rateLimit { cost nodeCount limit remaining resetAt }"

DEFAULT_QUERY = (
    "query($login: String!) {"
    " repositoryOwner(login: $login) {"
    " repositories(first: 50) { totalCount nodes { name"
    " issues(first: 20, states: OPEN) { totalCount nodes { number } } } }"
    " } }"
)


def blank_noise(document):
    """Comments and string literals replaced by spaces. Pure.

    Length preserving, unlike a scanner that removes them, because this one is
    used to compute an index back into the original text.
    """
    src = str(document or "")
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "#":
            while i < n and src[i] != "\\n":
                out[i] = " "
                i += 1
            continue
        if src.startswith('"""', i):
            j = src.find('"""', i + 3)
            end = n if j < 0 else j + 3
            for k in range(i, end):
                out[k] = " "
            i = end
            continue
        if ch == '"':
            out[i] = " "
            i += 1
            while i < n and src[i] != '"':
                step = 2 if src[i] == "\\\\" else 1
                for k in range(i, min(n, i + step)):
                    out[k] = " "
                i += step
            if i < n:
                out[i] = " "
            i += 1
            continue
        i += 1
    return "".join(out)


def operations(document):
    """The top-level operations in a document, in order. Pure."""
    src = blank_noise(document)
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


def selection_set_start(document):
    """Index of the operation's opening brace, or -1. Pure.

    Braces inside the variable definitions -- an input object used as a default
    value -- are skipped, because inserting a selection there would produce a
    document that no longer parses.
    """
    src = blank_noise(document)
    parens = 0
    for i, ch in enumerate(src):
        if ch == "(":
            parens += 1
        elif ch == ")":
            parens = max(0, parens - 1)
        elif ch == "{" and parens == 0:
            return i
    return -1


def inject_rate_limit(document):
    """The document with rateLimit added to its top-level selection. Pure.

    Idempotent: a document that already asks for it comes back untouched, so
    running this over a repository of queries does not accumulate duplicates.
    """
    src = str(document or "")
    if "rateLimit" in blank_noise(src):
        return src
    at = selection_set_start(src)
    if at < 0:
        return src
    return src[:at + 1] + " " + RATE_LIMIT_SELECTION + src[at + 1:]


def slicing_pairs(argument_text):
    """The first and last arguments in one argument list. Pure.

    Splits on top-level commas so a nested input object does not confuse the
    scan, and matches the key exactly so a variable definition reading
    `$first: Int = 250` is never counted as an argument called first.
    """
    src = str(argument_text or "")
    parts, depth, cur = [], 0, ""
    for ch in src:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
            continue
        cur += ch
    parts.append(cur)
    out = []
    for part in parts:
        key, sep, value = part.partition(":")
        if sep and key.strip() in ("first", "last"):
            out.append((key.strip(), value.strip()))
    return out


def variable_defaults(document):
    """Defaults declared in the operation's variable definitions. Pure."""
    head = blank_noise(document).split("{", 1)[0]
    out = {}
    for part in head.replace("(", " ").replace(")", " ").split(","):
        name, sep, rest = part.partition(":")
        if not sep:
            continue
        name = (name.strip().rsplit(None, 1) or [""])[-1]
        if not name.startswith("$") or "=" not in rest:
            continue
        out[name] = rest.split("=", 1)[1].strip()
    return out


def as_int(value):
    """An integer, or None if this is not one. Pure."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def resolve_slice(raw, defaults=None, variables=None):
    """One written slicing value resolved to (value, source). Pure."""
    text = str(raw or "").strip()
    if not text:
        return (None, "missing")
    if not text.startswith("$"):
        return (as_int(text), "literal")
    supplied = variables if isinstance(variables, dict) else {}
    if text[1:] in supplied:
        return (as_int(supplied[text[1:]]), "variable-supplied")
    if text in (defaults or {}):
        return (as_int((defaults or {})[text]), "variable-default")
    return (None, "unresolved")


def slice_values(document, variables=None):
    """Every first and last in the document, resolved. Pure."""
    src = blank_noise(document)
    defaults = variable_defaults(document)
    out, i, n, word, field = [], 0, len(src), "", ""
    while i < n:
        ch = src[i]
        if ch.isalnum() or ch == "_":
            word += ch
            i += 1
            continue
        if word:
            field, word = word, ""
        if ch == "(":
            j, level = i, 0
            while j < n:
                if src[j] == "(":
                    level += 1
                elif src[j] == ")":
                    level -= 1
                    if level == 0:
                        break
                j += 1
            for arg, raw in slicing_pairs(src[i + 1:j]):
                value, source = resolve_slice(raw, defaults, variables)
                out.append({"field": field, "arg": arg, "written": raw,
                            "value": value, "source": source})
            i = j + 1
            continue
        i += 1
    return out


def predicted_cost(document, variables=None):
    """The documented approximation, from the text. Pure.

    Returns (points, unresolved). Roughly the sum of the slices divided by 100
    with a minimum of one, which is a prediction rather than an answer: its job
    is to be something the server's number can disagree with.
    """
    values = slice_values(document, variables)
    total, unresolved = 0, 0
    for v in values:
        if isinstance(v["value"], int) and v["value"] > 0:
            total += v["value"]
        else:
            unresolved += 1
    return (max(1, -(-total // 100)), unresolved)


def find_rate_limit(body):
    """The rateLimit object anywhere in a response. Pure."""
    if isinstance(body, dict):
        node = body.get("rateLimit")
        if isinstance(node, dict):
            return node
        for value in body.values():
            found = find_rate_limit(value)
            if found is not None:
                return found
    elif isinstance(body, list):
        for item in body:
            found = find_rate_limit(item)
            if found is not None:
                return found
    return None


def measured_cost(body):
    """What the server charged for this call, or None. Pure."""
    node = find_rate_limit(body) or {}
    cost = node.get("cost")
    return cost if isinstance(cost, int) else None


def measured_nodes(body):
    """The node count the server computed for this call, or None. Pure."""
    node = find_rate_limit(body) or {}
    count = node.get("nodeCount")
    return count if isinstance(count, int) else None


def returned_nodes(body):
    """How many items actually came back in every nodes list. Pure."""
    total = 0
    if isinstance(body, dict):
        for key, value in body.items():
            if key in ("nodes", "edges") and isinstance(value, list):
                total += len(value)
            total += returned_nodes(value)
    elif isinstance(body, list):
        for item in body:
            total += returned_nodes(item)
    return total


def gap(predicted, measured):
    """The disagreement between the text and the server. Pure."""
    if measured is None:
        return (None, "unmeasured")
    if not predicted or predicted <= 0:
        return (None, "unpredictable")
    ratio = measured / float(predicted)
    if ratio >= 2:
        return (ratio, "far-above-the-text")
    if ratio > 1.25:
        return (ratio, "above-the-text")
    if ratio < 0.75:
        return (ratio, "below-the-text")
    return (ratio, "close-to-the-text")


def drift(baseline, measured):
    """This shape's price against the recorded one. Pure."""
    if not isinstance(baseline, int):
        return ("no-baseline",
                "no recorded cost for this shape, so nothing can be compared. "
                "Record this one and the next change becomes visible.")
    if measured is None:
        return ("unmeasured", "nothing to compare the baseline against.")
    if measured == baseline:
        return ("unchanged",
                "this shape costs the same %d point(s) it did when the baseline "
                "was written." % baseline)
    direction = "rise" if measured > baseline else "fall"
    percent = abs(measured - baseline) * 100.0 / max(1, baseline)
    return ("increased" if measured > baseline else "decreased",
            "this shape cost %d point(s) when the baseline was written and costs "
            "%d now, a %s of %.0f%%." % (baseline, measured, direction, percent))


def classify(measured, predicted, baseline=None, returned=None):
    """Classify one measurement. Pure. Returns (state, detail)."""
    if measured is None:
        return ("cost-unmeasured",
                "the response carried no rateLimit { cost }, so this run "
                "measured nothing. Nothing else here is worth reading.")
    drift_state, drift_detail = drift(baseline, measured)
    if drift_state == "increased":
        return ("cost-increased-since-the-baseline", drift_detail)
    ratio, verdict = gap(predicted, measured)
    if verdict in ("far-above-the-text", "above-the-text"):
        return ("cost-above-the-shape-of-the-query",
                "the server charged %d where the document predicted %d, a "
                "factor of %.1f." % (measured, predicted, ratio))
    if isinstance(returned, int) and measured >= 5 and returned <= measured:
        return ("cost-unrelated-to-the-data-returned",
                "%d node(s) came back for %d point(s). The price follows what "
                "the query asked for, not what it found."
                % (returned, measured))
    return ("cost-measured",
            "this shape costs %d point(s), which is what the document predicts "
            "and what the baseline says." % measured)


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "cost-increased-since-the-baseline":
        return ("record the new cost against the shape and treat the change as "
                "part of the diff that caused it. A price change belongs in a "
                "code review, not in an incident.")
    if state == "cost-above-the-shape-of-the-query":
        return ("find what the document traverses that the arithmetic did not "
                "see -- usually a connection nested inside another -- and split "
                "the query rather than widening the budget.")
    if state == "cost-unrelated-to-the-data-returned":
        return ("lower the first values rather than filtering harder. Filters "
                "change what comes back; only the slice changes the price.")
    if state == "cost-unmeasured":
        return ("add rateLimit { cost nodeCount remaining } to the query. It "
                "costs no extra round trip and there is no other way to learn "
                "the number.")
    if state == "cost-measured":
        return ("record this number so the next change to the query has "
                "something to be compared against.")
    return "point the check at a document this endpoint can answer."


def points_per_hour(cost, calls_per_hour):
    """What a schedule spends. Pure."""
    if not isinstance(cost, int) or not calls_per_hour:
        return None
    return cost * int(calls_per_hour)


def point_cost(queries):
    """Points this run will spend. Pure."""
    return int(queries or 0) * POINTS_PER_QUERY


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
    ap.add_argument("--file", help="a .graphql file to price")
    ap.add_argument("--query", help="the document as a string")
    ap.add_argument("--variables", default="{}", help="JSON object of variables")
    ap.add_argument("--login", help="user or organisation for the default query")
    ap.add_argument("--name", default="query", help="name for this shape in the baseline")
    ap.add_argument("--assumed", type=int, help="the cost somebody believes this has")
    ap.add_argument("--baseline", help="JSON file of recorded costs per shape name")
    ap.add_argument("--calls-per-hour", type=int, default=0,
                    help="how often this shape is sent, for an hourly projection")
    args = ap.parse_args()

    document = Path(args.file).read_text(encoding="utf-8") if args.file \\
        else (args.query or DEFAULT_QUERY)
    try:
        variables = json.loads(args.variables)
    except ValueError:
        log.error("--variables takes a JSON object")
        return 2
    if not isinstance(variables, dict):
        log.error("--variables takes a JSON object")
        return 2
    if not args.file and not args.query:
        if not args.login:
            log.error("--login takes a user or organisation name")
            return 2
        variables.setdefault("login", args.login)

    why_not = refusal(document)
    if why_not:
        log.error("refusing to send: %s", why_not)
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    baseline = None
    if args.baseline:
        recorded = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        value = recorded.get(args.name) if isinstance(recorded, dict) else None
        baseline = value if isinstance(value, int) else None

    log.info("point cost: %d point(s) against the 5,000/hour GraphQL budget",
             point_cost(1))
    predicted, unresolved = predicted_cost(document, variables)
    slices = slice_values(document, variables)
    log.info("predicted from the text: %d point(s) from %d slicing argument(s) "
             "totalling %d", predicted, len(slices),
             sum(v["value"] for v in slices if isinstance(v["value"], int)))
    if unresolved:
        log.info("%d slicing argument(s) could not be resolved, so the "
                 "prediction is a lower bound", unresolved)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })
    status, body = run_query(session, inject_rate_limit(document), variables)
    if isinstance(body, dict) and body.get("errors"):
        log.error("the query itself failed: %s", json.dumps(body["errors"])[:400])
        return 2

    measured = measured_cost(body)
    nodes = measured_nodes(body)
    returned = returned_nodes(body.get("data") if isinstance(body, dict) else None)
    log.info("measured by the server: %s point(s), nodeCount %s",
             "?" if measured is None else measured, "?" if nodes is None else nodes)
    if args.assumed is not None:
        log.info("assumed by the caller: %d point(s)", args.assumed)
    if baseline is not None:
        log.info("recorded baseline: %d point(s)", baseline)

    state, detail = classify(measured, predicted, baseline, returned)
    log.info("%s: %s", state, detail)
    if measured is not None:
        log.info("%d node(s) came back for %d point(s), so the price is not the "
                 "size of the answer", returned, measured)
        if args.assumed is not None and args.assumed != measured:
            log.info("the assumption is out by a factor of %.1f, and every "
                     "capacity number built on it is out by the same factor",
                     measured / float(max(1, args.assumed)))
    projected = points_per_hour(measured, args.calls_per_hour)
    if projected:
        log.info("at %d call(s)/hour this shape needs %d points/hour. What that "
                 "means against your quota is /github/graphql-rate-limited/",
                 args.calls_per_hour, projected)
    log.info("repair: %s", repair(state))
    if measured is not None:
        log.info('record it: "%s": %d', args.name, measured)

    print(json.dumps({"points_spent": point_cost(1), "state": state,
                      "predicted": predicted, "measured": measured,
                      "assumed": args.assumed, "baseline": baseline,
                      "node_count": nodes, "returned_nodes": returned,
                      "points_per_hour": projected, "slices": slices},
                     indent=2, default=str))
    return 1 if state in ("cost-increased-since-the-baseline",
                          "cost-above-the-shape-of-the-query",
                          "cost-unrelated-to-the-data-returned") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-cost.mjs",
"js": '''/**
 * Measure what a GraphQL query costs and compare it with what anybody assumed.
 *
 * Read only, and queries only. GitHub's GraphQL endpoint takes a document in
 * the request body, so a read is carried by POST there just as a write would
 * be; that is transport, not intent. Any document containing a mutation or a
 * subscription is refused before a socket opens. The baseline file is printed
 * for you to update rather than rewritten here.
 *
 * Environment:
 *   GITHUB_TOKEN      a token with read access to the GraphQL API
 *   GITHUB_QUERY      the document as a string
 *   GITHUB_VARIABLES  JSON object of variables
 *   GITHUB_LOGIN      user or organisation for the default query
 *   GITHUB_ASSUMED    the cost somebody believes this has
 *   GITHUB_CALLS      how often this shape is sent, for an hourly projection
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-cost/1.0';

export const POINTS_PER_QUERY = 1;

/** The selection that makes a response report its own price. */
export const RATE_LIMIT_SELECTION = 'rateLimit { cost nodeCount limit remaining resetAt }';

const DEFAULT_QUERY = 'query($login: String!) {'
  + ' repositoryOwner(login: $login) {'
  + ' repositories(first: 50) { totalCount nodes { name'
  + ' issues(first: 20, states: OPEN) { totalCount nodes { number } } } }'
  + ' } }';

/** Comments and string literals replaced by spaces. Length preserving. Pure. */
export function blankNoise(document) {
  const src = String(document ?? '');
  const out = src.split('');
  let i = 0;
  while (i < src.length) {
    const ch = src[i];
    if (ch === '#') {
      while (i < src.length && src[i] !== '\\n') { out[i] = ' '; i += 1; }
      continue;
    }
    if (src.startsWith('"""', i)) {
      const j = src.indexOf('"""', i + 3);
      const end = j < 0 ? src.length : j + 3;
      for (let k = i; k < end; k += 1) out[k] = ' ';
      i = end;
      continue;
    }
    if (ch === '"') {
      out[i] = ' ';
      i += 1;
      while (i < src.length && src[i] !== '"') {
        const step = src[i] === '\\\\' ? 2 : 1;
        for (let k = i; k < Math.min(src.length, i + step); k += 1) out[k] = ' ';
        i += step;
      }
      if (i < src.length) out[i] = ' ';
      i += 1;
      continue;
    }
    i += 1;
  }
  return out.join('');
}

/** The top-level operations in a document, in order. Pure. */
export function operations(document) {
  const src = `${blankNoise(document)} `;
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

/** Index of the operation's opening brace, or -1. Pure. */
export function selectionSetStart(document) {
  const src = blankNoise(document);
  let parens = 0;
  for (let i = 0; i < src.length; i += 1) {
    const ch = src[i];
    if (ch === '(') parens += 1;
    else if (ch === ')') parens = Math.max(0, parens - 1);
    else if (ch === '{' && parens === 0) return i;
  }
  return -1;
}

/** The document with rateLimit added to its top-level selection. Pure. */
export function injectRateLimit(document) {
  const src = String(document ?? '');
  if (blankNoise(src).includes('rateLimit')) return src;
  const at = selectionSetStart(src);
  if (at < 0) return src;
  return `${src.slice(0, at + 1)} ${RATE_LIMIT_SELECTION}${src.slice(at + 1)}`;
}

/** The first and last arguments in one argument list. Pure. */
export function slicingPairs(argumentText) {
  const src = String(argumentText ?? '');
  const parts = [];
  let depth = 0;
  let cur = '';
  for (const ch of src) {
    if ('([{'.includes(ch)) depth += 1;
    else if (')]}'.includes(ch)) depth = Math.max(0, depth - 1);
    if (ch === ',' && depth === 0) { parts.push(cur); cur = ''; continue; }
    cur += ch;
  }
  parts.push(cur);
  const out = [];
  for (const part of parts) {
    const at = part.indexOf(':');
    if (at < 0) continue;
    const key = part.slice(0, at).trim();
    if (key === 'first' || key === 'last') out.push([key, part.slice(at + 1).trim()]);
  }
  return out;
}

/** Defaults declared in the operation's variable definitions. Pure. */
export function variableDefaults(document) {
  const head = blankNoise(document).split('{')[0];
  const out = {};
  for (const part of head.replace(/\\(/g, ' ').replace(/\\)/g, ' ').split(',')) {
    const at = part.indexOf(':');
    if (at < 0) continue;
    const name = part.slice(0, at).trim().split(/\\s+/).pop();
    const rest = part.slice(at + 1);
    if (!name || !name.startsWith('$') || !rest.includes('=')) continue;
    out[name] = rest.slice(rest.indexOf('=') + 1).trim();
  }
  return out;
}

/** An integer, or null if this is not one. Pure. */
export function asInt(value) {
  const text = String(value ?? '').trim();
  if (!/^-?[0-9]+$/.test(text)) return null;
  return Number(text);
}

/** One written slicing value resolved to [value, source]. Pure. */
export function resolveSlice(raw, defaults, variables) {
  const text = String(raw ?? '').trim();
  if (!text) return [null, 'missing'];
  if (!text.startsWith('$')) return [asInt(text), 'literal'];
  const supplied = (variables && typeof variables === 'object') ? variables : {};
  const bare = text.slice(1);
  if (Object.prototype.hasOwnProperty.call(supplied, bare)) {
    return [asInt(supplied[bare]), 'variable-supplied'];
  }
  if (defaults && Object.prototype.hasOwnProperty.call(defaults, text)) {
    return [asInt(defaults[text]), 'variable-default'];
  }
  return [null, 'unresolved'];
}

/** Every first and last in the document, resolved. Pure. */
export function sliceValues(document, variables) {
  const src = blankNoise(document);
  const defaults = variableDefaults(document);
  const out = [];
  let i = 0;
  let word = '';
  let field = '';
  while (i < src.length) {
    const ch = src[i];
    if (/[A-Za-z0-9_]/.test(ch)) { word += ch; i += 1; continue; }
    if (word) { field = word; word = ''; }
    if (ch === '(') {
      let j = i;
      let level = 0;
      while (j < src.length) {
        if (src[j] === '(') level += 1;
        else if (src[j] === ')') { level -= 1; if (level === 0) break; }
        j += 1;
      }
      for (const [arg, raw] of slicingPairs(src.slice(i + 1, j))) {
        const [value, source] = resolveSlice(raw, defaults, variables);
        out.push({ field, arg, written: raw, value, source });
      }
      i = j + 1;
      continue;
    }
    i += 1;
  }
  return out;
}

/** The documented approximation, from the text. Pure. Returns [points, unresolved]. */
export function predictedCost(document, variables) {
  const values = sliceValues(document, variables);
  let total = 0;
  let unresolved = 0;
  for (const v of values) {
    if (Number.isInteger(v.value) && v.value > 0) total += v.value;
    else unresolved += 1;
  }
  return [Math.max(1, Math.ceil(total / 100)), unresolved];
}

/** The rateLimit object anywhere in a response. Pure. */
export function findRateLimit(body) {
  if (Array.isArray(body)) {
    for (const item of body) {
      const found = findRateLimit(item);
      if (found !== null) return found;
    }
    return null;
  }
  if (!body || typeof body !== 'object') return null;
  if (body.rateLimit && typeof body.rateLimit === 'object') return body.rateLimit;
  for (const value of Object.values(body)) {
    const found = findRateLimit(value);
    if (found !== null) return found;
  }
  return null;
}

/** What the server charged for this call, or null. Pure. */
export function measuredCost(body) {
  const node = findRateLimit(body) || {};
  return Number.isInteger(node.cost) ? node.cost : null;
}

/** The node count the server computed for this call, or null. Pure. */
export function measuredNodes(body) {
  const node = findRateLimit(body) || {};
  return Number.isInteger(node.nodeCount) ? node.nodeCount : null;
}

/** How many items actually came back in every nodes list. Pure. */
export function returnedNodes(body) {
  let total = 0;
  if (Array.isArray(body)) {
    for (const item of body) total += returnedNodes(item);
    return total;
  }
  if (!body || typeof body !== 'object') return 0;
  for (const [key, value] of Object.entries(body)) {
    if ((key === 'nodes' || key === 'edges') && Array.isArray(value)) total += value.length;
    total += returnedNodes(value);
  }
  return total;
}

/** The disagreement between the text and the server. Pure. */
export function gap(predicted, measured) {
  if (measured === null || measured === undefined) return [null, 'unmeasured'];
  if (!predicted || predicted <= 0) return [null, 'unpredictable'];
  const ratio = measured / predicted;
  if (ratio >= 2) return [ratio, 'far-above-the-text'];
  if (ratio > 1.25) return [ratio, 'above-the-text'];
  if (ratio < 0.75) return [ratio, 'below-the-text'];
  return [ratio, 'close-to-the-text'];
}

/** This shape's price against the recorded one. Pure. */
export function drift(baseline, measured) {
  if (!Number.isInteger(baseline)) {
    return ['no-baseline', 'no recorded cost for this shape, so nothing can be '
      + 'compared. Record this one and the next change becomes visible.'];
  }
  if (measured === null || measured === undefined) {
    return ['unmeasured', 'nothing to compare the baseline against.'];
  }
  if (measured === baseline) {
    return ['unchanged', `this shape costs the same ${baseline} point(s) it did `
      + 'when the baseline was written.'];
  }
  const direction = measured > baseline ? 'rise' : 'fall';
  const percent = (Math.abs(measured - baseline) * 100) / Math.max(1, baseline);
  return [measured > baseline ? 'increased' : 'decreased',
    `this shape cost ${baseline} point(s) when the baseline was written and `
    + `costs ${measured} now, a ${direction} of ${percent.toFixed(0)}%.`];
}

/** Classify one measurement. Pure. Returns [state, detail]. */
export function classify(measured, predicted, baseline, returned) {
  if (measured === null || measured === undefined) {
    return ['cost-unmeasured', 'the response carried no rateLimit { cost }, so '
      + 'this run measured nothing. Nothing else here is worth reading.'];
  }
  const [driftState, driftDetail] = drift(baseline, measured);
  if (driftState === 'increased') return ['cost-increased-since-the-baseline', driftDetail];
  const [ratio, verdict] = gap(predicted, measured);
  if (verdict === 'far-above-the-text' || verdict === 'above-the-text') {
    return ['cost-above-the-shape-of-the-query',
      `the server charged ${measured} where the document predicted ${predicted}, `
      + `a factor of ${ratio.toFixed(1)}.`];
  }
  if (Number.isInteger(returned) && measured >= 5 && returned <= measured) {
    return ['cost-unrelated-to-the-data-returned',
      `${returned} node(s) came back for ${measured} point(s). The price follows `
      + 'what the query asked for, not what it found.'];
  }
  return ['cost-measured', `this shape costs ${measured} point(s), which is what `
    + 'the document predicts and what the baseline says.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'cost-increased-since-the-baseline') {
    return 'record the new cost against the shape and treat the change as part '
      + 'of the diff that caused it. A price change belongs in a code review, '
      + 'not in an incident.';
  }
  if (state === 'cost-above-the-shape-of-the-query') {
    return 'find what the document traverses that the arithmetic did not see -- '
      + 'usually a connection nested inside another -- and split the query '
      + 'rather than widening the budget.';
  }
  if (state === 'cost-unrelated-to-the-data-returned') {
    return 'lower the first values rather than filtering harder. Filters change '
      + 'what comes back; only the slice changes the price.';
  }
  if (state === 'cost-unmeasured') {
    return 'add rateLimit { cost nodeCount remaining } to the query. It costs no '
      + 'extra round trip and there is no other way to learn the number.';
  }
  if (state === 'cost-measured') {
    return 'record this number so the next change to the query has something to '
      + 'be compared against.';
  }
  return 'point the check at a document this endpoint can answer.';
}

/** What a schedule spends. Pure. */
export function pointsPerHour(cost, callsPerHour) {
  if (!Number.isInteger(cost) || !callsPerHour) return null;
  return cost * Number(callsPerHour);
}

/** Points this run will spend. Pure. */
export function pointCost(queries) {
  return Number(queries || 0) * POINTS_PER_QUERY;
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
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const document = process.env.GITHUB_QUERY || DEFAULT_QUERY;
  let variables = {};
  try { variables = JSON.parse(process.env.GITHUB_VARIABLES || '{}'); } catch {
    console.error('GITHUB_VARIABLES takes a JSON object');
    process.exitCode = 2;
    return;
  }
  if (!process.env.GITHUB_QUERY) {
    if (!process.env.GITHUB_LOGIN) {
      console.error('set GITHUB_LOGIN to a user or organisation name');
      process.exitCode = 2;
      return;
    }
    variables.login = process.env.GITHUB_LOGIN;
  }

  const whyNot = refusal(document);
  if (whyNot) {
    console.error(`refusing to send: ${whyNot}`);
    process.exitCode = 2;
    return;
  }

  console.log(`point cost: ${pointCost(1)} point(s) against the 5,000/hour GraphQL budget`);
  const [predicted, unresolved] = predictedCost(document, variables);
  const slices = sliceValues(document, variables);
  const asked = slices.reduce((a, v) => a + (Number.isInteger(v.value) ? v.value : 0), 0);
  console.log(`predicted from the text: ${predicted} point(s) from ${slices.length} `
    + `slicing argument(s) totalling ${asked}`);
  if (unresolved) {
    console.log(`${unresolved} slicing argument(s) could not be resolved, so the `
      + 'prediction is a lower bound');
  }

  const { body } = await runQuery(token, injectRateLimit(document), variables);
  if (body && Array.isArray(body.errors) && body.errors.length) {
    console.error(`the query itself failed: ${JSON.stringify(body.errors).slice(0, 400)}`);
    process.exitCode = 2;
    return;
  }

  const measured = measuredCost(body);
  const nodes = measuredNodes(body);
  const returned = returnedNodes(body && body.data);
  const assumed = process.env.GITHUB_ASSUMED ? Number(process.env.GITHUB_ASSUMED) : null;
  console.log(`measured by the server: ${measured === null ? '?' : measured} point(s), `
    + `nodeCount ${nodes === null ? '?' : nodes}`);
  if (assumed !== null) console.log(`assumed by the caller: ${assumed} point(s)`);

  const [state, detail] = classify(measured, predicted, null, returned);
  console.log(`${state}: ${detail}`);
  if (measured !== null) {
    console.log(`${returned} node(s) came back for ${measured} point(s), so the `
      + 'price is not the size of the answer');
  }
  const projected = pointsPerHour(measured, Number(process.env.GITHUB_CALLS || 0));
  if (projected) {
    console.log(`at ${process.env.GITHUB_CALLS} call(s)/hour this shape needs `
      + `${projected} points/hour. What that means against your quota is `
      + '/github/graphql-rate-limited/');
  }
  console.log(`repair: ${repair(state)}`);

  console.log(JSON.stringify({
    points_spent: pointCost(1), state, predicted, measured, assumed,
    node_count: nodes, returned_nodes: returned, points_per_hour: projected, slices,
  }, null, 2));
  process.exitCode = ['cost-increased-since-the-baseline',
    'cost-above-the-shape-of-the-query',
    'cost-unrelated-to-the-data-returned'].includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The surgery gets the most attention, because a broken injection produces a document that does not parse and a run that measures nothing. It is asserted to land inside the operation's selection set, to leave a document that already asks for <code>rateLimit</code> exactly as it found it, and to step over a brace that belongs to an input object in the variable definitions rather than to the query. After that the arithmetic: the prediction, the three-way comparison between predicted, measured and assumed, the drift against a baseline, and the count of nodes actually returned, which is what makes the point about price not following data.",
"test_py_file": "test_github_graphql_cost.py",
"test_py": '''from github_graphql_cost import (
    POINTS_PER_QUERY, blank_noise, classify, drift, gap, inject_rate_limit,
    measured_cost, measured_nodes, operations, point_cost, points_per_hour,
    predicted_cost, refusal, repair, returned_nodes, selection_set_start,
    slice_values,
)

QUERY = ("query($login: String!) { repositoryOwner(login: $login) {"
         " repositories(first: 50) { nodes { name"
         " issues(first: 20) { nodes { number } } } } } }")

BODY = {"data": {
    "rateLimit": {"cost": 14, "nodeCount": 3180, "limit": 5000, "remaining": 4986},
    "repositoryOwner": {"repositories": {"nodes": [
        {"name": "a", "issues": {"nodes": [{"number": 1}, {"number": 2}]}},
        {"name": "b", "issues": {"nodes": [{"number": 3}]}},
    ]}}}}


def test_the_injection_lands_in_the_operations_selection_set():
    out = inject_rate_limit(QUERY)
    assert "rateLimit { cost nodeCount limit remaining resetAt }" in out
    at = out.index("rateLimit")
    assert out.index("repositoryOwner") > at
    assert out.count("rateLimit") == 1


def test_a_document_that_already_asks_for_it_is_left_alone():
    once = inject_rate_limit(QUERY)
    assert inject_rate_limit(once) == once
    already = "query { rateLimit { cost } viewer { login } }"
    assert inject_rate_limit(already) == already


def test_a_brace_in_the_variable_definitions_is_not_the_selection_set():
    doc = 'query($order: IssueOrder = {field: CREATED_AT}) { viewer { login } }'
    at = selection_set_start(doc)
    assert doc[at:at + 3] == "{ v"
    out = inject_rate_limit(doc)
    assert out.index("IssueOrder") < out.index("rateLimit") < out.index("viewer")


def test_blanking_the_noise_keeps_every_index_where_it_was():
    doc = 'query { search(query: "a { b }", type: ISSUE, first: 5) { issueCount } }'
    blanked = blank_noise(doc)
    assert len(blanked) == len(doc)
    assert "{ b }" not in blanked
    assert blanked.index("issueCount") == doc.index("issueCount")


def test_the_prediction_comes_from_the_slices_and_never_from_zero():
    assert predicted_cost(QUERY, {}) == (1, 0)
    big = "query { a(first: 100) { nodes { b(first: 100) { nodes { id } } } } }"
    assert predicted_cost(big, {})[0] == 2
    assert predicted_cost("query { viewer { login } }", {}) == (1, 0)


def test_an_unresolved_slice_makes_the_prediction_a_lower_bound():
    doc = "query($n: Int!) { a(first: $n) { nodes { id } } }"
    points, unresolved = predicted_cost(doc, {})
    assert unresolved == 1
    assert points == 1
    assert predicted_cost(doc, {"n": 300})[0] == 3


def test_a_variable_definition_is_not_counted_as_a_slice():
    doc = "query($first: Int = 250) { a(first: 10) { nodes { id } } }"
    assert [(v["arg"], v["value"]) for v in slice_values(doc, {})] == [("first", 10)]


def test_the_server_number_is_read_out_of_the_response_wherever_it_sits():
    assert measured_cost(BODY) == 14
    assert measured_nodes(BODY) == 3180
    assert measured_cost({"data": {"viewer": {"login": "x"}}}) is None
    assert measured_cost(None) is None


def test_the_price_is_compared_with_the_data_that_came_back():
    assert returned_nodes(BODY["data"]) == 5
    assert returned_nodes({"nodes": [1, 2, 3]}) == 3
    assert returned_nodes({"name": "a"}) == 0


def test_the_gap_between_the_text_and_the_server_is_the_finding():
    assert gap(3, 14)[1] == "far-above-the-text"
    assert gap(4, 6)[1] == "above-the-text"
    assert gap(4, 4)[1] == "close-to-the-text"
    assert gap(10, 2)[1] == "below-the-text"
    assert gap(3, None)[1] == "unmeasured"


def test_drift_against_a_recorded_baseline_is_reported_as_a_percentage():
    state, detail = drift(3, 14)
    assert state == "increased"
    assert "367%" in detail
    assert drift(3, 3)[0] == "unchanged"
    assert drift(14, 3)[0] == "decreased"
    assert drift(None, 14)[0] == "no-baseline"


def test_a_price_rise_outranks_everything_else_because_it_is_reviewable():
    state, detail = classify(14, 3, 3, 5)
    assert state == "cost-increased-since-the-baseline"
    assert "367%" in detail
    assert "code review" in repair(state)


def test_a_query_costing_more_than_its_text_suggests_is_named_as_that():
    state, detail = classify(14, 3, None, 5)
    assert state == "cost-above-the-shape-of-the-query"
    assert "factor of 4.7" in detail


def test_cost_not_following_the_data_is_its_own_finding():
    state, detail = classify(9, 9, 9, 4)
    assert state == "cost-unrelated-to-the-data-returned"
    assert "4 node(s) came back for 9 point(s)" in detail
    assert "Filters change" in repair(state)


def test_an_unmeasured_run_says_so_rather_than_guessing():
    state, _detail = classify(None, 3, 3, 5)
    assert state == "cost-unmeasured"
    assert "rateLimit { cost nodeCount remaining }" in repair(state)


def test_the_hourly_projection_is_multiplication_and_nothing_more():
    assert points_per_hour(14, 240) == 3360
    assert points_per_hour(14, 0) is None
    assert points_per_hour(None, 240) is None


def test_the_script_refuses_to_send_a_mutation():
    assert operations("query Q { viewer { login } }") == ["query"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal("subscription S { thing { id } }")
    assert refusal(QUERY) is None


def test_the_run_says_what_it_will_spend():
    assert POINTS_PER_QUERY == 1
    assert point_cost(1) == 1
    assert point_cost(0) == 0
''',
"test_js_file": "github-graphql-cost.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  POINTS_PER_QUERY, blankNoise, classify, drift, gap, injectRateLimit,
  measuredCost, measuredNodes, operations, pointCost, pointsPerHour,
  predictedCost, refusal, repair, returnedNodes, selectionSetStart, sliceValues,
} from './github-graphql-cost.mjs';

const QUERY = 'query($login: String!) { repositoryOwner(login: $login) {'
  + ' repositories(first: 50) { nodes { name'
  + ' issues(first: 20) { nodes { number } } } } } }';

const BODY = {
  data: {
    rateLimit: {
      cost: 14, nodeCount: 3180, limit: 5000, remaining: 4986,
    },
    repositoryOwner: {
      repositories: {
        nodes: [
          { name: 'a', issues: { nodes: [{ number: 1 }, { number: 2 }] } },
          { name: 'b', issues: { nodes: [{ number: 3 }] } },
        ],
      },
    },
  },
};

test('the injection lands in the operation selection set', () => {
  const out = injectRateLimit(QUERY);
  assert.ok(out.includes('rateLimit { cost nodeCount limit remaining resetAt }'));
  assert.ok(out.indexOf('repositoryOwner') > out.indexOf('rateLimit'));
  assert.equal(out.split('rateLimit').length - 1, 1);
});

test('a document that already asks for it is left alone', () => {
  const once = injectRateLimit(QUERY);
  assert.equal(injectRateLimit(once), once);
  const already = 'query { rateLimit { cost } viewer { login } }';
  assert.equal(injectRateLimit(already), already);
});

test('a brace in the variable definitions is not the selection set', () => {
  const doc = 'query($order: IssueOrder = {field: CREATED_AT}) { viewer { login } }';
  const at = selectionSetStart(doc);
  assert.equal(doc.slice(at, at + 3), '{ v');
  const out = injectRateLimit(doc);
  assert.ok(out.indexOf('IssueOrder') < out.indexOf('rateLimit'));
  assert.ok(out.indexOf('rateLimit') < out.indexOf('viewer'));
});

test('blanking the noise keeps every index where it was', () => {
  const doc = 'query { search(query: "a { b }", type: ISSUE, first: 5) { issueCount } }';
  const blanked = blankNoise(doc);
  assert.equal(blanked.length, doc.length);
  assert.ok(!blanked.includes('{ b }'));
  assert.equal(blanked.indexOf('issueCount'), doc.indexOf('issueCount'));
});

test('the prediction comes from the slices and never from zero', () => {
  assert.deepEqual(predictedCost(QUERY, {}), [1, 0]);
  const big = 'query { a(first: 100) { nodes { b(first: 100) { nodes { id } } } } }';
  assert.equal(predictedCost(big, {})[0], 2);
  assert.deepEqual(predictedCost('query { viewer { login } }', {}), [1, 0]);
});

test('an unresolved slice makes the prediction a lower bound', () => {
  const doc = 'query($n: Int!) { a(first: $n) { nodes { id } } }';
  const [points, unresolved] = predictedCost(doc, {});
  assert.equal(unresolved, 1);
  assert.equal(points, 1);
  assert.equal(predictedCost(doc, { n: 300 })[0], 3);
});

test('a variable definition is not counted as a slice', () => {
  const doc = 'query($first: Int = 250) { a(first: 10) { nodes { id } } }';
  assert.deepEqual(sliceValues(doc, {}).map((v) => [v.arg, v.value]), [['first', 10]]);
});

test('the server number is read out of the response wherever it sits', () => {
  assert.equal(measuredCost(BODY), 14);
  assert.equal(measuredNodes(BODY), 3180);
  assert.equal(measuredCost({ data: { viewer: { login: 'x' } } }), null);
  assert.equal(measuredCost(null), null);
});

test('the price is compared with the data that came back', () => {
  assert.equal(returnedNodes(BODY.data), 5);
  assert.equal(returnedNodes({ nodes: [1, 2, 3] }), 3);
  assert.equal(returnedNodes({ name: 'a' }), 0);
});

test('the gap between the text and the server is the finding', () => {
  assert.equal(gap(3, 14)[1], 'far-above-the-text');
  assert.equal(gap(4, 6)[1], 'above-the-text');
  assert.equal(gap(4, 4)[1], 'close-to-the-text');
  assert.equal(gap(10, 2)[1], 'below-the-text');
  assert.equal(gap(3, null)[1], 'unmeasured');
});

test('drift against a recorded baseline is reported as a percentage', () => {
  const [state, detail] = drift(3, 14);
  assert.equal(state, 'increased');
  assert.match(detail, /367%/);
  assert.equal(drift(3, 3)[0], 'unchanged');
  assert.equal(drift(14, 3)[0], 'decreased');
  assert.equal(drift(null, 14)[0], 'no-baseline');
});

test('a price rise outranks everything else because it is reviewable', () => {
  const [state, detail] = classify(14, 3, 3, 5);
  assert.equal(state, 'cost-increased-since-the-baseline');
  assert.match(detail, /367%/);
  assert.match(repair(state), /code review/);
});

test('a query costing more than its text suggests is named as that', () => {
  const [state, detail] = classify(14, 3, null, 5);
  assert.equal(state, 'cost-above-the-shape-of-the-query');
  assert.match(detail, /factor of 4\\.7/);
});

test('cost not following the data is its own finding', () => {
  const [state, detail] = classify(9, 9, 9, 4);
  assert.equal(state, 'cost-unrelated-to-the-data-returned');
  assert.match(detail, /4 node\\(s\\) came back for 9 point\\(s\\)/);
  assert.match(repair(state), /Filters change/);
});

test('an unmeasured run says so rather than guessing', () => {
  const [state] = classify(null, 3, 3, 5);
  assert.equal(state, 'cost-unmeasured');
  assert.match(repair(state), /rateLimit \\{ cost nodeCount remaining \\}/);
});

test('the hourly projection is multiplication and nothing more', () => {
  assert.equal(pointsPerHour(14, 240), 3360);
  assert.equal(pointsPerHour(14, 0), null);
  assert.equal(pointsPerHour(null, 240), null);
});

test('the script refuses to send a mutation', () => {
  assert.deepEqual(operations('query Q { viewer { login } }'), ['query']);
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.ok(refusal('subscription S { thing { id } }'));
  assert.equal(refusal(QUERY), null);
});

test('the run says what it will spend', () => {
  assert.equal(POINTS_PER_QUERY, 1);
  assert.equal(pointCost(1), 1);
  assert.equal(pointCost(0), 0);
});
''',
"faq": [
 ("How is the cost actually calculated?",
  "From the request rather than the response. GitHub derives it from the number of unique connections the query could traverse and the slice each one was given, then divides by 100 and rounds up, with a minimum of one point per query. The important consequence is that filtering does not make a query cheaper: a connection asked for a hundred items costs the same whether it finds a hundred or none. Only lowering the slice, or removing a connection, moves the number."),
 ("Does adding rateLimit to my query make it more expensive?",
  "No. It is a field on the query root and it does not traverse a connection, so it adds nothing to the cost of a query you were sending anyway. Sending it as a query all by itself costs one point, like any other query. That is the argument for putting it into your real queries permanently rather than probing for it: the measurement becomes continuous and free, and you end up with a log of what each shape costs over time instead of a single reading."),
 ("What is the difference between cost and nodeCount?",
  "Cost is what you are billed, in points against the hourly budget. nodeCount is how many nodes the query could return, which is checked against a separate ceiling of 500,000 and has nothing to do with the budget. A query can be cheap and over the node limit, or expensive and nowhere near it. They are reported side by side because they are both computed from the request, but they answer different questions and have different failure modes."),
 ("My query costs one point. Do I need any of this?",
  "Not today, and that is exactly how the trap is set. The queries that break a budget were all one point once, and they grew a field at a time with nobody watching the price because there was never a moment where watching it seemed necessary. Recording the number costs nothing and turns the eventual change into a line in a diff. If you only do one thing, put rateLimit into the query and log the cost; the comparison can come later."),
 ("Should the baseline live in the repository or in monitoring?",
  "In the repository, next to the queries. The change you want to catch arrives in a pull request weeks before it causes an incident, and a file a reviewer can see the diff of catches it there. Monitoring catches it once it is already spending real quota, which is later and more expensive. This script deliberately does not update the file for you: it prints the line to add, so changing a recorded price is always somebody's explicit decision."),
],
"related": [
 ("/github/graphql-rate-limited/", "The budget these points are spent from"),
 ("/github/graphql-timeout-point-penalty/", "A query charged extra for taking too long"),
 ("/github/graphql-node-limit-exceeded/", "The node ceiling, which is not the budget"),
],
"citations": [CITE_GQL_RATE, CITE_GQL_RESOURCE, CITE_GQL_GUIDE, CITE_REST_RATE_LIMIT],
},

{
"slug": "graphql-timeout-point-penalty",
"title": "A GraphQL query times out at 10s and is charged anyway",
"description": "GitHub kills a GraphQL request that runs past ten seconds and deducts extra points for it, so a retry loop spends the budget twice and returns nothing.",
"h1": "A GraphQL query times out at 10s and is charged anyway",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github graphql timeout 10 seconds",
             "github graphql 502 bad gateway query",
             "github graphql query timeout points deducted",
             "github graphql could not respond in time",
             "github graphql 504 retry rate limit"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The nightly job started failing with a <code>502</code> about ten seconds into a query that used to take four. The retry logic did the obvious thing and sent it again, three times, with backoff, exactly as it should for a gateway error. By the time somebody looked, the run had produced nothing at all and the hourly point budget was several hundred lighter than a run that produced nothing has any business being.",
"short_answer": """<p>GitHub terminates a GraphQL request that takes longer than roughly ten seconds and returns a <code>502</code> or <code>504</code> with a message about not being able to respond in time. It also deducts <strong>additional</strong> points from the primary rate limit as a penalty, on top of what the query would have cost. So a timed-out query is charged more than a successful one and gives you nothing back.</p>
<p>That makes a blind retry the worst possible response. The same document against the same data will take the same time, hit the same cutoff and pay the same penalty, so three retries is three charges for zero rows. Measure it once by reading <code>resources.graphql.used</code> from <code>GET /rate_limit</code> either side of the call — that endpoint is free — then make the query smaller instead: fewer nested connections and lower <code>first</code> values, paginated.</p>""",
"problem": """<p>Everything about this failure is dressed as something else. A <code>502</code> is a gateway error, and every piece of retry advice ever written says a gateway error is transient and should be retried with backoff. The client is doing what it was told. The one thing that makes this case different — that the request was killed deliberately, for taking too long, and that the cause is entirely inside your own query — is not visible in the status code at all.</p>
<p>It also arrives without a code change. The query that times out today ran in four seconds last month, against the same organisation, with the same shape. What grew was the data underneath it: more repositories, more open pull requests, more comments on the ones that matter. There is nothing to bisect and nothing in a diff, which sends people to GitHub's status page and then to their own network before anybody looks at the query.</p>
<p>Then the budget goes missing and nobody connects the two. Points disappear from a bucket that is shared by every process using that token, during a run that returned no data, so the natural conclusion is that something else on the token is spending them. The idea that a failed call costs more than a successful one is not most people's mental model of an API, and until somebody measures it, the arithmetic never quite adds up.</p>""",
"why": """<p><strong>Ten seconds is a server-side cutoff, not your client's timeout.</strong> GitHub stops executing a GraphQL request that runs past its limit and returns an error rather than a partial result. Raising your own HTTP timeout does nothing whatsoever; the connection is not the constraint. The only lever is how much work the document asks for.</p>
<p><strong>The penalty is documented and it is on top of the normal cost.</strong> GitHub says explicitly that it deducts additional points from the primary rate limit for queries that time out. That inverts the usual assumption that a failed call is a free call, and it is what makes the retry loop expensive rather than merely useless.</p>
<p><strong>Retrying reproduces it exactly.</strong> Nothing about the query changes between attempts, and neither does the data, so the second attempt takes as long as the first and dies in the same place. This is the same reasoning as for <a href="/github/graphql-node-limit-exceeded/">a query rejected for its node count</a>, with one difference that matters here: a node-limit rejection is free, and this one is charged every time round.</p>
<p><strong>The measurement is free, and it is a subtraction.</strong> <code>GET /rate_limit</code> reports <code>resources.graphql.used</code> and is documented not to consume quota, so reading it immediately before and immediately after the failing call gives you what that call cost. If the delta is larger than the query's normal cost, you have measured the penalty directly rather than believing a document about it.</p>
<p><strong>The bucket is shared, so the subtraction has a caveat and the script states it.</strong> Every process holding that token draws on the same budget, and the API never says which one spent what. This script takes two readings with nothing sent between them first: if the bucket moves during that gap, something else is spending and the measurement that follows cannot be attributed. That is reported as a contaminated result rather than quietly presented as a number.</p>
<p><strong>Time is the symptom; the query is the cause.</strong> A query at eight seconds is not healthy, it is one busy repository away from this note. The script reports elapsed time against the cutoff even on a successful call, because the interesting moment is before the failure rather than after it, and a query using eighty per cent of the budget is a finding on its own.</p>""",
"steps": [
 {"h": "Take two free readings with nothing in between",
  "body": """<p><code>GET /rate_limit</code> does not consume quota, so reading <code>resources.graphql.used</code> twice back to back costs nothing and answers a question that has to be answered first: is anything else spending from this token right now. If the bucket moves while nothing is being sent, every later subtraction is contaminated and the script says so instead of reporting a number.</p>"""},
 {"h": "Send the query once, with a clock on it",
  "body": """<p>One attempt, timed. What comes back is either a result with an elapsed time worth knowing or a <code>502</code> or <code>504</code> at around ten seconds with a message about not responding in time. The script never retries, on purpose: retrying is the behaviour this note exists to stop.</p>"""},
 {"h": "Read the bucket again and subtract",
  "body": """<p>The difference in <code>used</code> is what that one call cost. If the reset timestamp moved between readings the window rolled over and the measurement is void, which the script detects rather than reporting a nonsense number.</p>"""},
 {"h": "Compare the charge against what the query normally costs",
  "body": """<p>Pass the query's normal cost with <code>--normal-cost</code>; measuring it is what the cost note is for. Anything charged above that on a call that returned nothing is the penalty, stated as a number. That is the sentence that changes a retry policy.</p>"""},
 {"h": "Make the query smaller, and read the clock even when it passes",
  "body": """<p>Fewer nested connections, lower <code>first</code> values, and paginate what you shrank. The script also reports how much of the ten seconds a successful call used, because a query at eight seconds is not a healthy query — it is this failure waiting for the busiest repository in the organisation to get one more pull request.</p>"""},
],
"verify": """<p>The penalty stops being a rumour once it is a subtraction, and the retry projection prices the loop that made it worse.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_graphql_timeout.py \\
    --login acme --normal-cost 12 --retries 3
# point cost: up to 1 point(s) for the query plus whatever the timeout penalty
# adds, which is the number this run measures. Both /rate_limit reads are free.
# idle check: graphql used 1204 -> 1204 with nothing sent, so the bucket is quiet
# sending one query. This script never retries a timed-out query.
# HTTP 502 after 10.4s: "Something went wrong while executing your query. This
# may be the result of a timeout"
# graphql used 1204 -> 1225, so this call was charged 21 point(s)
# timed-out-and-charged-extra: the query was killed at the 10s cutoff and cost
# 21 point(s) against a normal cost of 12, a penalty of 9 point(s)
# 3 retries of this document would spend 63 more point(s) and return nothing
# repair: lower the first values and split the nested connections. Do not retry
# a timed-out query: the same document reproduces the timeout and the penalty.</code></pre>""",
"code_intro": "The instrument is a subtraction over a free endpoint, and almost all of the code is about not lying with it. <code>GET /rate_limit</code> is read twice with nothing in between to establish that the bucket is quiet, then either side of the single attempt; a reset timestamp that moves between readings voids the measurement rather than producing a negative number, and a bucket that moves while nothing is being sent marks the result unattributable. The query is sent exactly once and never retried, and as everywhere in this section the document is parsed and refused before a socket opens if it contains a mutation or a subscription.",
"py_file": "github_graphql_timeout.py",
"py": '''"""Measure what a timed-out GraphQL query is charged, without retrying it.

Read only, and queries only. GitHub's GraphQL endpoint takes a document in the
request body, so a read is carried by POST there just as a write would be; that
is transport, not intent. This script sends queries and refuses any document
containing a mutation or a subscription before it opens a socket. Nothing is
written and the repair is printed rather than performed.

GitHub kills a GraphQL request that runs past roughly ten seconds and returns a
502 or 504, and it deducts additional points from the primary rate limit as a
penalty. A timed-out query therefore costs more than a successful one and
returns nothing, which makes a blind retry the most expensive possible response:
the same document against the same data reproduces the timeout and the charge.

What this can and cannot see: GET /rate_limit is free and reports
resources.graphql.used, so the cost of one call is a subtraction. The bucket is
shared by every process holding the token and the API never says which one spent
what, so this script first reads the bucket twice with nothing in between. If it
moves during that gap the measurement is reported as unattributable rather than
as a number.

Environment:

    GITHUB_TOKEN    a token with read access to the GraphQL API
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_graphql_timeout")

API = "https://api.github.com"
UA = "github-graphql-timeout/1.0"

# The server-side cutoff. Raising the client's own timeout does nothing at all:
# the connection was never the constraint.
TIMEOUT_SECONDS = 10

POINTS_PER_QUERY = 1

# A call using this much of the cutoff is not healthy, it is one busy repository
# away from failing, so it is reported as a finding on a successful run.
NEAR_LIMIT = 0.7

# Substrings GitHub uses when it kills a query for time. Matched case
# insensitively and alongside the status code rather than instead of it.
TIMEOUT_MARKERS = (
    "timeout",
    "timed out",
    "took too long",
    "respond in time",
    "responding in time",
)

# Deliberately heavy: three connections deep with wide slices, which is the
# shape that runs past the cutoff long before it approaches the node limit.
DEFAULT_QUERY = (
    "query($login: String!, $repos: Int = 100, $prs: Int = 40) {"
    " repositoryOwner(login: $login) {"
    " repositories(first: $repos, orderBy: {field: PUSHED_AT, direction: DESC}) {"
    " nodes { name pullRequests(first: $prs, states: OPEN) {"
    " nodes { number title comments(first: 20) { totalCount nodes { createdAt } } }"
    " } } } } }"
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


def bucket_reading(payload, name="graphql"):
    """One bucket out of a GET /rate_limit body. Pure.

    The GraphQL bucket, not the core one. Reading the wrong bucket here would
    produce a measurement that never moves and a note that concludes there is no
    penalty.
    """
    if not isinstance(payload, dict):
        return None
    resources = payload.get("resources")
    if not isinstance(resources, dict):
        return None
    bucket = resources.get(name)
    if not isinstance(bucket, dict):
        return None
    return {"limit": bucket.get("limit"), "used": bucket.get("used"),
            "remaining": bucket.get("remaining"), "reset": bucket.get("reset")}


def charged(before, after):
    """Points spent between two readings. Pure. Returns (points, state).

    A reset timestamp that moved means the hourly window rolled over between the
    readings and the subtraction is meaningless, which is worth detecting rather
    than reporting as a negative number or as zero.
    """
    if not isinstance(before, dict) or not isinstance(after, dict):
        return (None, "unreadable")
    if before.get("reset") != after.get("reset"):
        return (None, "window-reset")
    start, end = before.get("used"), after.get("used")
    if not isinstance(start, int) or not isinstance(end, int):
        return (None, "unreadable")
    if end < start:
        return (None, "window-reset")
    return (end - start, "measured")


def net_charge(delta, background):
    """The charge with a known background drain removed. Pure."""
    if not isinstance(delta, int):
        return None
    if not isinstance(background, int) or background <= 0:
        return delta
    return max(0, delta - background)


def timeout_message(body):
    """The message GitHub returned, or None. Pure."""
    if not isinstance(body, dict):
        return None
    errors = body.get("errors")
    if isinstance(errors, list):
        for err in errors:
            if isinstance(err, dict) and err.get("message"):
                return str(err["message"])
    if body.get("message"):
        return str(body["message"])
    return None


def looks_like_timeout(status, body):
    """Whether this response is the server giving up on time. Pure."""
    if status in (502, 504):
        return True
    message = (timeout_message(body) or "").lower()
    return any(marker in message for marker in TIMEOUT_MARKERS)


def timing_consistent(elapsed):
    """Whether the elapsed time agrees with the documented cutoff. Pure."""
    if not isinstance(elapsed, (int, float)):
        return False
    return elapsed >= TIMEOUT_SECONDS * 0.8


def headroom(elapsed):
    """How much of the cutoff this call used, as a fraction. Pure."""
    if not isinstance(elapsed, (int, float)) or elapsed < 0:
        return None
    return elapsed / float(TIMEOUT_SECONDS)


def penalty(points, normal_cost):
    """Points charged above what the query would have cost. Pure."""
    if not isinstance(points, int) or not isinstance(normal_cost, int):
        return None
    return points - normal_cost


def retry_projection(points, retries):
    """What retrying this document would spend for nothing. Pure."""
    if not isinstance(points, int) or not retries or retries < 1:
        return 0
    return points * int(retries)


def classify(status, elapsed, points, normal_cost, background=0, body=None):
    """Classify one attempt. Pure. Returns (state, detail)."""
    timed_out = looks_like_timeout(status, body)
    if points is None:
        return ("charge-not-measurable",
                "the two rate-limit readings do not support a subtraction, so "
                "what this call cost cannot be stated%s."
                % (" -- and it did time out" if timed_out else ""))
    if timed_out and isinstance(background, int) and background > 0:
        return ("timed-out-charge-not-attributable",
                "the query was killed and %d point(s) moved, but the bucket was "
                "already draining with nothing sent, so the charge belongs to "
                "more than this call." % points)
    extra = penalty(points, normal_cost)
    if timed_out and isinstance(extra, int) and extra > 0:
        return ("timed-out-and-charged-extra",
                "the query was killed at the %ds cutoff and cost %d point(s) "
                "against a normal cost of %d, a penalty of %d point(s)."
                % (TIMEOUT_SECONDS, points, normal_cost, extra))
    if timed_out:
        return ("timed-out-charge-not-proved",
                "the query was killed at the %ds cutoff and the bucket moved by "
                "%d point(s), which is not more than its normal cost. The "
                "timeout is real; the penalty is not demonstrated by this run."
                % (TIMEOUT_SECONDS, points))
    fraction = headroom(elapsed)
    if fraction is not None and fraction >= NEAR_LIMIT:
        return ("close-to-the-timeout",
                "the query returned, in %.1fs, which is %d%% of the %ds cutoff. "
                "This one is one busy repository away from the failure above."
                % (elapsed, round(fraction * 100), TIMEOUT_SECONDS))
    return ("completed-inside-the-limit",
            "the query returned in %.1fs and was charged %d point(s), which is "
            "the ordinary case." % (elapsed or 0.0, points))


def repair(state):
    """The sentence a reader has to act on. Pure."""
    if state == "timed-out-and-charged-extra":
        return ("lower the first values and split the nested connections. Do "
                "not retry a timed-out query: the same document reproduces the "
                "timeout and the penalty.")
    if state == "timed-out-charge-not-proved":
        return ("make the query smaller anyway. The timeout is the finding; "
                "whether this particular run demonstrated the extra charge does "
                "not change the repair.")
    if state == "timed-out-charge-not-attributable":
        return ("re-run this when nothing else is holding the token, or give "
                "the job its own token. A shared bucket cannot attribute a "
                "charge to a call.")
    if state == "charge-not-measurable":
        return ("re-run it away from the top of the hour, when the window is "
                "less likely to reset between the two readings.")
    if state == "close-to-the-timeout":
        return ("shrink it now rather than after the outage. Fewer nested "
                "connections and lower first values, paginated.")
    if state == "completed-inside-the-limit":
        return ("nothing here. Keep the elapsed time in your logs so the day it "
                "starts climbing is visible before the day it fails.")
    return "point the check at a document this endpoint can answer."


def point_cost(queries):
    """Points this run will spend before any penalty. Pure."""
    return int(queries or 0) * POINTS_PER_QUERY


def read_bucket(session):
    """GET /rate_limit, which is free and does not consume quota."""
    r = session.get(API + "/rate_limit", timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    try:
        return bucket_reading(r.json())
    except ValueError:
        return None


def run_query(session, document, variables):
    """Send one query, once. Returns (status, body-or-None, elapsed).

    A GraphQL query is a read; POST is only how the document reaches the
    endpoint, which is why the verb is written here beside the URL rather than
    tucked into a constant where it could be mistaken for a write path. There is
    no retry here by design: retrying is the behaviour this script exists to
    stop.
    """
    started = time.monotonic()
    r = session.post(API + "/graphql",
                     json={"query": document, "variables": variables or {}},
                     timeout=60)
    elapsed = time.monotonic() - started
    if r.status_code == 401:
        raise SystemExit("401 from GitHub: GITHUB_TOKEN is missing, malformed "
                         "or revoked")
    try:
        return r.status_code, r.json(), elapsed
    except ValueError:
        return r.status_code, {"message": r.text[:300]}, elapsed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--login", help="user or organisation for the default query")
    ap.add_argument("--file", help="a .graphql file to send instead")
    ap.add_argument("--query", help="the document as a string")
    ap.add_argument("--variables", default="{}", help="JSON object of variables")
    ap.add_argument("--normal-cost", type=int, default=1,
                    help="what this query costs when it finishes. Measure it "
                         "with the cost note rather than guessing.")
    ap.add_argument("--retries", type=int, default=3,
                    help="how many retries to price. Nothing is retried.")
    args = ap.parse_args()

    document = Path(args.file).read_text(encoding="utf-8") if args.file \\
        else (args.query or DEFAULT_QUERY)
    try:
        variables = json.loads(args.variables)
    except ValueError:
        log.error("--variables takes a JSON object")
        return 2
    if not isinstance(variables, dict):
        log.error("--variables takes a JSON object")
        return 2
    if not args.file and not args.query:
        if not args.login:
            log.error("--login takes a user or organisation name")
            return 2
        variables.setdefault("login", args.login)

    why_not = refusal(document)
    if why_not:
        log.error("refusing to send: %s", why_not)
        return 2

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        # GitHub rejects requests with no User-Agent outright.
        "User-Agent": UA,
    })

    log.info("point cost: up to %d point(s) for the query plus whatever the "
             "timeout penalty adds, which is the number this run measures. Both "
             "/rate_limit reads are free.", point_cost(1))

    idle_before = read_bucket(session)
    idle_after = read_bucket(session)
    background, idle_state = charged(idle_before, idle_after)
    if idle_state == "measured":
        log.info("idle check: graphql used %s -> %s with nothing sent, so the "
                 "bucket is %s", idle_before.get("used"), idle_after.get("used"),
                 "quiet" if background == 0 else "already draining")
    else:
        log.info("idle check: %s, so the background drain is unknown", idle_state)
        background = 0

    log.info("sending one query. This script never retries a timed-out query.")
    before = idle_after
    status, body, elapsed = run_query(session, document, variables)
    after = read_bucket(session)

    message = timeout_message(body)
    log.info("HTTP %s after %.1fs%s", status, elapsed,
             ": %s" % message[:160] if message else "")
    delta, state_of_charge = charged(before, after)
    points = net_charge(delta, background)
    if state_of_charge == "measured":
        log.info("graphql used %s -> %s, so this call was charged %s point(s)",
                 before.get("used"), after.get("used"), points)
    else:
        log.info("the charge could not be measured: %s", state_of_charge)

    state, detail = classify(status, elapsed, points, args.normal_cost,
                             background, body)
    log.info("%s: %s", state, detail)
    if timing_consistent(elapsed) and looks_like_timeout(status, body):
        log.info("the elapsed time agrees with the documented %ds cutoff",
                 TIMEOUT_SECONDS)
    projected = retry_projection(points, args.retries)
    if projected and state.startswith("timed-out"):
        log.info("%d retries of this document would spend %d more point(s) and "
                 "return nothing", args.retries, projected)
    log.info("repair: %s", repair(state))

    print(json.dumps({"status": status, "elapsed_seconds": round(elapsed, 2),
                      "headroom": headroom(elapsed), "charged": points,
                      "background_drain": background,
                      "normal_cost": args.normal_cost,
                      "penalty": penalty(points, args.normal_cost),
                      "retry_cost": projected, "state": state,
                      "detail": detail}, indent=2, default=str))
    return 1 if state.startswith("timed-out") or state == "close-to-the-timeout" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-graphql-timeout.mjs",
"js": '''/**
 * Measure what a timed-out GraphQL query is charged, without retrying it.
 *
 * Read only, and queries only. GitHub's GraphQL endpoint takes a document in
 * the request body, so a read is carried by POST there just as a write would
 * be; that is transport, not intent. Any document containing a mutation or a
 * subscription is refused before a socket opens, and nothing is ever retried.
 *
 * Environment:
 *   GITHUB_TOKEN        a token with read access to the GraphQL API
 *   GITHUB_LOGIN        user or organisation for the default query
 *   GITHUB_QUERY        the document as a string
 *   GITHUB_VARIABLES    JSON object of variables
 *   GITHUB_NORMAL_COST  what this query costs when it finishes
 *   GITHUB_RETRIES      how many retries to price. Nothing is retried.
 */
const API = 'https://api.github.com';
const UA = 'github-graphql-timeout/1.0';

/** The server-side cutoff. A longer client timeout changes nothing. */
export const TIMEOUT_SECONDS = 10;

export const POINTS_PER_QUERY = 1;

/** A call using this much of the cutoff is a finding on a successful run. */
export const NEAR_LIMIT = 0.7;

/** Substrings GitHub uses when it kills a query for time. */
export const TIMEOUT_MARKERS = [
  'timeout', 'timed out', 'took too long', 'respond in time', 'responding in time',
];

const DEFAULT_QUERY = 'query($login: String!, $repos: Int = 100, $prs: Int = 40) {'
  + ' repositoryOwner(login: $login) {'
  + ' repositories(first: $repos, orderBy: {field: PUSHED_AT, direction: DESC}) {'
  + ' nodes { name pullRequests(first: $prs, states: OPEN) {'
  + ' nodes { number title comments(first: 20) { totalCount nodes { createdAt } } }'
  + ' } } } } }';

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

/** One bucket out of a GET /rate_limit body. Pure. */
export function bucketReading(payload, name = 'graphql') {
  if (!payload || typeof payload !== 'object') return null;
  const resources = payload.resources;
  if (!resources || typeof resources !== 'object') return null;
  const bucket = resources[name];
  if (!bucket || typeof bucket !== 'object') return null;
  return {
    limit: bucket.limit, used: bucket.used, remaining: bucket.remaining, reset: bucket.reset,
  };
}

/** Points spent between two readings. Pure. Returns [points, state]. */
export function charged(before, after) {
  if (!before || typeof before !== 'object' || !after || typeof after !== 'object') {
    return [null, 'unreadable'];
  }
  if (before.reset !== after.reset) return [null, 'window-reset'];
  if (!Number.isInteger(before.used) || !Number.isInteger(after.used)) {
    return [null, 'unreadable'];
  }
  if (after.used < before.used) return [null, 'window-reset'];
  return [after.used - before.used, 'measured'];
}

/** The charge with a known background drain removed. Pure. */
export function netCharge(delta, background) {
  if (!Number.isInteger(delta)) return null;
  if (!Number.isInteger(background) || background <= 0) return delta;
  return Math.max(0, delta - background);
}

/** The message GitHub returned, or null. Pure. */
export function timeoutMessage(body) {
  if (!body || typeof body !== 'object') return null;
  if (Array.isArray(body.errors)) {
    for (const err of body.errors) {
      if (err && typeof err === 'object' && err.message) return String(err.message);
    }
  }
  if (body.message) return String(body.message);
  return null;
}

/** Whether this response is the server giving up on time. Pure. */
export function looksLikeTimeout(status, body) {
  if (status === 502 || status === 504) return true;
  const message = (timeoutMessage(body) || '').toLowerCase();
  return TIMEOUT_MARKERS.some((marker) => message.includes(marker));
}

/** Whether the elapsed time agrees with the documented cutoff. Pure. */
export function timingConsistent(elapsed) {
  if (typeof elapsed !== 'number' || Number.isNaN(elapsed)) return false;
  return elapsed >= TIMEOUT_SECONDS * 0.8;
}

/** How much of the cutoff this call used, as a fraction. Pure. */
export function headroom(elapsed) {
  if (typeof elapsed !== 'number' || Number.isNaN(elapsed) || elapsed < 0) return null;
  return elapsed / TIMEOUT_SECONDS;
}

/** Points charged above what the query would have cost. Pure. */
export function penalty(points, normalCost) {
  if (!Number.isInteger(points) || !Number.isInteger(normalCost)) return null;
  return points - normalCost;
}

/** What retrying this document would spend for nothing. Pure. */
export function retryProjection(points, retries) {
  if (!Number.isInteger(points) || !retries || retries < 1) return 0;
  return points * Number(retries);
}

/** Classify one attempt. Pure. Returns [state, detail]. */
export function classify(status, elapsed, points, normalCost, background = 0, body = null) {
  const timedOut = looksLikeTimeout(status, body);
  if (points === null || points === undefined) {
    return ['charge-not-measurable', 'the two rate-limit readings do not support '
      + 'a subtraction, so what this call cost cannot be stated'
      + `${timedOut ? ' -- and it did time out' : ''}.`];
  }
  if (timedOut && Number.isInteger(background) && background > 0) {
    return ['timed-out-charge-not-attributable',
      `the query was killed and ${points} point(s) moved, but the bucket was `
      + 'already draining with nothing sent, so the charge belongs to more than '
      + 'this call.'];
  }
  const extra = penalty(points, normalCost);
  if (timedOut && Number.isInteger(extra) && extra > 0) {
    return ['timed-out-and-charged-extra',
      `the query was killed at the ${TIMEOUT_SECONDS}s cutoff and cost ${points} `
      + `point(s) against a normal cost of ${normalCost}, a penalty of ${extra} point(s).`];
  }
  if (timedOut) {
    return ['timed-out-charge-not-proved',
      `the query was killed at the ${TIMEOUT_SECONDS}s cutoff and the bucket `
      + `moved by ${points} point(s), which is not more than its normal cost. `
      + 'The timeout is real; the penalty is not demonstrated by this run.'];
  }
  const fraction = headroom(elapsed);
  if (fraction !== null && fraction >= NEAR_LIMIT) {
    return ['close-to-the-timeout',
      `the query returned, in ${elapsed.toFixed(1)}s, which is `
      + `${Math.round(fraction * 100)}% of the ${TIMEOUT_SECONDS}s cutoff. This `
      + 'one is one busy repository away from the failure above.'];
  }
  return ['completed-inside-the-limit',
    `the query returned in ${(elapsed || 0).toFixed(1)}s and was charged `
    + `${points} point(s), which is the ordinary case.`];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'timed-out-and-charged-extra') {
    return 'lower the first values and split the nested connections. Do not '
      + 'retry a timed-out query: the same document reproduces the timeout and '
      + 'the penalty.';
  }
  if (state === 'timed-out-charge-not-proved') {
    return 'make the query smaller anyway. The timeout is the finding; whether '
      + 'this particular run demonstrated the extra charge does not change the '
      + 'repair.';
  }
  if (state === 'timed-out-charge-not-attributable') {
    return 're-run this when nothing else is holding the token, or give the job '
      + 'its own token. A shared bucket cannot attribute a charge to a call.';
  }
  if (state === 'charge-not-measurable') {
    return 're-run it away from the top of the hour, when the window is less '
      + 'likely to reset between the two readings.';
  }
  if (state === 'close-to-the-timeout') {
    return 'shrink it now rather than after the outage. Fewer nested '
      + 'connections and lower first values, paginated.';
  }
  if (state === 'completed-inside-the-limit') {
    return 'nothing here. Keep the elapsed time in your logs so the day it '
      + 'starts climbing is visible before the day it fails.';
  }
  return 'point the check at a document this endpoint can answer.';
}

/** Points this run will spend before any penalty. Pure. */
export function pointCost(queries) {
  return Number(queries || 0) * POINTS_PER_QUERY;
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'Content-Type': 'application/json',
    'User-Agent': UA,
  };
}

async function readBucket(token) {
  const res = await fetch(`${API}/rate_limit`, { headers: headers(token) });
  if (res.status === 401) throw new Error('401 from GitHub: GITHUB_TOKEN is missing or revoked');
  try { return bucketReading(await res.json()); } catch { return null; }
}

async function runQuery(token, document, variables) {
  const started = Date.now();
  const res = await fetch(`${API}/graphql`, {
    // A GraphQL query is a read. POST is only how the document reaches the
    // endpoint, and refusal() has already rejected anything that is not a read.
    method: 'POST',
    headers: headers(token),
    body: JSON.stringify({ query: document, variables: variables || {} }),
  });
  const elapsed = (Date.now() - started) / 1000;
  let body = null;
  try { body = await res.json(); } catch { body = { message: 'no JSON body' }; }
  return { status: res.status, body, elapsed };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const document = process.env.GITHUB_QUERY || DEFAULT_QUERY;
  let variables = {};
  try { variables = JSON.parse(process.env.GITHUB_VARIABLES || '{}'); } catch {
    console.error('GITHUB_VARIABLES takes a JSON object');
    process.exitCode = 2;
    return;
  }
  if (!process.env.GITHUB_QUERY) {
    if (!process.env.GITHUB_LOGIN) {
      console.error('set GITHUB_LOGIN to a user or organisation name');
      process.exitCode = 2;
      return;
    }
    variables.login = process.env.GITHUB_LOGIN;
  }

  const whyNot = refusal(document);
  if (whyNot) {
    console.error(`refusing to send: ${whyNot}`);
    process.exitCode = 2;
    return;
  }

  const normalCost = Number(process.env.GITHUB_NORMAL_COST || 1);
  const retries = Number(process.env.GITHUB_RETRIES || 3);
  console.log(`point cost: up to ${pointCost(1)} point(s) for the query plus `
    + 'whatever the timeout penalty adds, which is the number this run '
    + 'measures. Both /rate_limit reads are free.');

  const idleBefore = await readBucket(token);
  const idleAfter = await readBucket(token);
  let [background, idleState] = charged(idleBefore, idleAfter);
  if (idleState === 'measured') {
    console.log(`idle check: graphql used ${idleBefore.used} -> ${idleAfter.used} `
      + `with nothing sent, so the bucket is ${background === 0 ? 'quiet' : 'already draining'}`);
  } else {
    console.log(`idle check: ${idleState}, so the background drain is unknown`);
    background = 0;
  }

  console.log('sending one query. This script never retries a timed-out query.');
  const { status, body, elapsed } = await runQuery(token, document, variables);
  const after = await readBucket(token);

  const message = timeoutMessage(body);
  console.log(`HTTP ${status} after ${elapsed.toFixed(1)}s`
    + `${message ? `: ${message.slice(0, 160)}` : ''}`);
  const [delta, chargeState] = charged(idleAfter, after);
  const points = netCharge(delta, background);
  if (chargeState === 'measured') {
    console.log(`graphql used ${idleAfter.used} -> ${after.used}, so this call `
      + `was charged ${points} point(s)`);
  } else {
    console.log(`the charge could not be measured: ${chargeState}`);
  }

  const [state, detail] = classify(status, elapsed, points, normalCost, background, body);
  console.log(`${state}: ${detail}`);
  if (timingConsistent(elapsed) && looksLikeTimeout(status, body)) {
    console.log(`the elapsed time agrees with the documented ${TIMEOUT_SECONDS}s cutoff`);
  }
  const projected = retryProjection(points, retries);
  if (projected && state.startsWith('timed-out')) {
    console.log(`${retries} retries of this document would spend ${projected} `
      + 'more point(s) and return nothing');
  }
  console.log(`repair: ${repair(state)}`);

  console.log(JSON.stringify({
    status,
    elapsed_seconds: Number(elapsed.toFixed(2)),
    headroom: headroom(elapsed),
    charged: points,
    background_drain: background,
    normal_cost: normalCost,
    penalty: penalty(points, normalCost),
    retry_cost: projected,
    state,
    detail,
  }, null, 2));
  process.exitCode = (state.startsWith('timed-out') || state === 'close-to-the-timeout') ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The subtraction gets tested harder than anything else, because a measurement that quietly returns a wrong number is worse than one that refuses. A window that reset between the readings, a used counter that went backwards, a body that is not a rate-limit payload and a bucket that moved while nothing was being sent all produce a refusal rather than a figure. Then the classifier: a timeout charged more than its normal cost, a timeout that did not demonstrate the penalty, a timeout nobody can attribute, and a successful call that used eighty per cent of the ten seconds and is therefore still a finding.",
"test_py_file": "test_github_graphql_timeout.py",
"test_py": '''from github_graphql_timeout import (
    NEAR_LIMIT, POINTS_PER_QUERY, TIMEOUT_SECONDS, bucket_reading, charged,
    classify, headroom, looks_like_timeout, net_charge, operations, penalty,
    point_cost, refusal, repair, retry_projection, timeout_message,
    timing_consistent,
)

PAYLOAD = {"resources": {
    "core": {"limit": 5000, "used": 900, "remaining": 4100, "reset": 1780000000},
    "graphql": {"limit": 5000, "used": 1204, "remaining": 3796, "reset": 1780000000},
}}

TIMED_OUT = {"errors": [{"message": "Something went wrong while executing your "
                                    "query. This may be the result of a timeout"}]}
BEFORE = {"limit": 5000, "used": 1204, "remaining": 3796, "reset": 1780000000}
AFTER = {"limit": 5000, "used": 1225, "remaining": 3775, "reset": 1780000000}


def test_the_reading_comes_from_the_graphql_bucket_and_not_core():
    reading = bucket_reading(PAYLOAD)
    assert reading["used"] == 1204
    assert bucket_reading(PAYLOAD, "core")["used"] == 900
    assert bucket_reading({}) is None
    assert bucket_reading(None) is None


def test_the_charge_is_a_subtraction_over_one_window():
    assert charged(BEFORE, AFTER) == (21, "measured")
    assert charged(BEFORE, BEFORE) == (0, "measured")


def test_a_window_that_reset_between_readings_voids_the_measurement():
    rolled = dict(AFTER, reset=1780003600, used=3)
    assert charged(BEFORE, rolled) == (None, "window-reset")
    backwards = dict(AFTER, used=1100)
    assert charged(BEFORE, backwards) == (None, "window-reset")
    assert charged(BEFORE, None) == (None, "unreadable")
    assert charged({"used": "many", "reset": 1}, {"used": 2, "reset": 1}) == (None, "unreadable")


def test_a_known_background_drain_is_subtracted_rather_than_ignored():
    assert net_charge(21, 0) == 21
    assert net_charge(21, 5) == 16
    assert net_charge(3, 9) == 0
    assert net_charge(None, 0) is None


def test_a_timeout_is_recognised_by_status_or_by_message():
    assert looks_like_timeout(502, None)
    assert looks_like_timeout(504, None)
    assert looks_like_timeout(200, TIMED_OUT)
    assert not looks_like_timeout(200, {"data": {"viewer": {"login": "x"}}})
    assert timeout_message(TIMED_OUT).startswith("Something went wrong")
    assert timeout_message({"message": "Bad gateway"}) == "Bad gateway"
    assert timeout_message(None) is None


def test_the_clock_is_checked_against_the_documented_cutoff():
    assert TIMEOUT_SECONDS == 10
    assert timing_consistent(10.4)
    assert timing_consistent(8.0)
    assert not timing_consistent(3.2)
    assert not timing_consistent(None)
    assert round(headroom(8.0), 2) == 0.8
    assert headroom(-1) is None


def test_a_timeout_charged_above_its_normal_cost_is_the_headline():
    state, detail = classify(502, 10.4, 21, 12, 0, None)
    assert state == "timed-out-and-charged-extra"
    assert "penalty of 9 point(s)" in detail
    assert penalty(21, 12) == 9
    assert "Do not retry" in repair(state)


def test_a_timeout_that_did_not_prove_the_penalty_says_so():
    state, detail = classify(504, 10.1, 12, 12, 0, None)
    assert state == "timed-out-charge-not-proved"
    assert "not demonstrated by this run" in detail
    assert "smaller anyway" in repair(state)


def test_a_bucket_that_was_already_draining_makes_the_charge_unattributable():
    state, detail = classify(502, 10.2, 40, 12, 7, None)
    assert state == "timed-out-charge-not-attributable"
    assert "belongs to more than this call" in detail
    assert "its own token" in repair(state)


def test_an_unmeasurable_charge_is_never_reported_as_zero():
    state, detail = classify(502, 10.2, None, 12, 0, None)
    assert state == "charge-not-measurable"
    assert "did time out" in detail


def test_a_successful_call_near_the_cutoff_is_still_a_finding():
    state, detail = classify(200, 8.2, 12, 12, 0, {"data": {"x": 1}})
    assert state == "close-to-the-timeout"
    assert "82%" in detail
    assert NEAR_LIMIT == 0.7
    assert "rather than after the outage" in repair(state)


def test_an_ordinary_call_is_not_dressed_up_as_a_problem():
    state, detail = classify(200, 3.4, 12, 12, 0, {"data": {"x": 1}})
    assert state == "completed-inside-the-limit"
    assert "ordinary case" in detail


def test_the_retry_loop_is_priced_but_never_run():
    assert retry_projection(21, 3) == 63
    assert retry_projection(21, 0) == 0
    assert retry_projection(None, 3) == 0


def test_the_script_refuses_to_send_a_mutation():
    assert operations("query Q { viewer { login } }") == ["query"]
    assert refusal("mutation M { addStar(input: {}) { clientMutationId } }")
    assert refusal("subscription S { thing { id } }")
    assert refusal("query Q { viewer { login } }") is None


def test_the_run_says_what_it_will_spend_before_the_penalty():
    assert POINTS_PER_QUERY == 1
    assert point_cost(1) == 1
    assert point_cost(0) == 0
''',
"test_js_file": "github-graphql-timeout.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  NEAR_LIMIT, POINTS_PER_QUERY, TIMEOUT_SECONDS, bucketReading, charged,
  classify, headroom, looksLikeTimeout, netCharge, operations, penalty,
  pointCost, refusal, repair, retryProjection, timeoutMessage, timingConsistent,
} from './github-graphql-timeout.mjs';

const PAYLOAD = {
  resources: {
    core: {
      limit: 5000, used: 900, remaining: 4100, reset: 1780000000,
    },
    graphql: {
      limit: 5000, used: 1204, remaining: 3796, reset: 1780000000,
    },
  },
};

const TIMED_OUT = {
  errors: [{
    message: 'Something went wrong while executing your query. This may be the '
      + 'result of a timeout',
  }],
};
const BEFORE = {
  limit: 5000, used: 1204, remaining: 3796, reset: 1780000000,
};
const AFTER = {
  limit: 5000, used: 1225, remaining: 3775, reset: 1780000000,
};

test('the reading comes from the graphql bucket and not core', () => {
  assert.equal(bucketReading(PAYLOAD).used, 1204);
  assert.equal(bucketReading(PAYLOAD, 'core').used, 900);
  assert.equal(bucketReading({}), null);
  assert.equal(bucketReading(null), null);
});

test('the charge is a subtraction over one window', () => {
  assert.deepEqual(charged(BEFORE, AFTER), [21, 'measured']);
  assert.deepEqual(charged(BEFORE, BEFORE), [0, 'measured']);
});

test('a window that reset between readings voids the measurement', () => {
  assert.deepEqual(charged(BEFORE, { ...AFTER, reset: 1780003600, used: 3 }),
    [null, 'window-reset']);
  assert.deepEqual(charged(BEFORE, { ...AFTER, used: 1100 }), [null, 'window-reset']);
  assert.deepEqual(charged(BEFORE, null), [null, 'unreadable']);
  assert.deepEqual(charged({ used: 'many', reset: 1 }, { used: 2, reset: 1 }),
    [null, 'unreadable']);
});

test('a known background drain is subtracted rather than ignored', () => {
  assert.equal(netCharge(21, 0), 21);
  assert.equal(netCharge(21, 5), 16);
  assert.equal(netCharge(3, 9), 0);
  assert.equal(netCharge(null, 0), null);
});

test('a timeout is recognised by status or by message', () => {
  assert.ok(looksLikeTimeout(502, null));
  assert.ok(looksLikeTimeout(504, null));
  assert.ok(looksLikeTimeout(200, TIMED_OUT));
  assert.ok(!looksLikeTimeout(200, { data: { viewer: { login: 'x' } } }));
  assert.ok(timeoutMessage(TIMED_OUT).startsWith('Something went wrong'));
  assert.equal(timeoutMessage({ message: 'Bad gateway' }), 'Bad gateway');
  assert.equal(timeoutMessage(null), null);
});

test('the clock is checked against the documented cutoff', () => {
  assert.equal(TIMEOUT_SECONDS, 10);
  assert.ok(timingConsistent(10.4));
  assert.ok(timingConsistent(8.0));
  assert.ok(!timingConsistent(3.2));
  assert.ok(!timingConsistent(null));
  assert.equal(Number(headroom(8.0).toFixed(2)), 0.8);
  assert.equal(headroom(-1), null);
});

test('a timeout charged above its normal cost is the headline', () => {
  const [state, detail] = classify(502, 10.4, 21, 12, 0, null);
  assert.equal(state, 'timed-out-and-charged-extra');
  assert.match(detail, /penalty of 9 point\\(s\\)/);
  assert.equal(penalty(21, 12), 9);
  assert.match(repair(state), /not retry/);
});

test('a timeout that did not prove the penalty says so', () => {
  const [state, detail] = classify(504, 10.1, 12, 12, 0, null);
  assert.equal(state, 'timed-out-charge-not-proved');
  assert.match(detail, /not demonstrated by this run/);
  assert.match(repair(state), /smaller anyway/);
});

test('a bucket that was already draining makes the charge unattributable', () => {
  const [state, detail] = classify(502, 10.2, 40, 12, 7, null);
  assert.equal(state, 'timed-out-charge-not-attributable');
  assert.match(detail, /belongs to more than this call/);
  assert.match(repair(state), /its own token/);
});

test('an unmeasurable charge is never reported as zero', () => {
  const [state, detail] = classify(502, 10.2, null, 12, 0, null);
  assert.equal(state, 'charge-not-measurable');
  assert.match(detail, /did time out/);
});

test('a successful call near the cutoff is still a finding', () => {
  const [state, detail] = classify(200, 8.2, 12, 12, 0, { data: { x: 1 } });
  assert.equal(state, 'close-to-the-timeout');
  assert.match(detail, /82%/);
  assert.equal(NEAR_LIMIT, 0.7);
  assert.match(repair(state), /rather than after the outage/);
});

test('an ordinary call is not dressed up as a problem', () => {
  const [state, detail] = classify(200, 3.4, 12, 12, 0, { data: { x: 1 } });
  assert.equal(state, 'completed-inside-the-limit');
  assert.match(detail, /ordinary case/);
});

test('the retry loop is priced but never run', () => {
  assert.equal(retryProjection(21, 3), 63);
  assert.equal(retryProjection(21, 0), 0);
  assert.equal(retryProjection(null, 3), 0);
});

test('the script refuses to send a mutation', () => {
  assert.deepEqual(operations('query Q { viewer { login } }'), ['query']);
  assert.ok(refusal('mutation M { addStar(input: {}) { clientMutationId } }'));
  assert.ok(refusal('subscription S { thing { id } }'));
  assert.equal(refusal('query Q { viewer { login } }'), null);
});

test('the run says what it will spend before the penalty', () => {
  assert.equal(POINTS_PER_QUERY, 1);
  assert.equal(pointCost(1), 1);
  assert.equal(pointCost(0), 0);
});
''',
"faq": [
 ("Can I raise the ten-second limit or ask for more time?",
  "No. It is a server-side execution limit, applied to the query rather than to the connection, and there is no header, parameter or plan that extends it. Raising your own HTTP client timeout has no effect at all, because your client is not the thing giving up. The only lever available is the amount of work the document asks for: fewer nested connections, lower first values, and pagination in place of one large traversal."),
 ("Is retrying really that bad? Every other 502 should be retried.",
  "For a genuine gateway error, yes, retry. For this one the retry is worse than useless, because the query is deterministic: the same document over the same data takes the same time and dies at the same cutoff, and each attempt is charged with the penalty on top. Three retries is three charges for nothing. The distinction a client can act on is elapsed time — a 502 that arrives after ten seconds is a timeout, and a 502 that arrives in 200 milliseconds is the gateway error you should retry."),
 ("How do I know the penalty is real rather than something else spending the budget?",
  "You measure it, and the script is careful about exactly this. GET /rate_limit is free, so it reads resources.graphql.used twice with nothing sent between them first: if the bucket moves during that gap, another process is holding the same token and the result is reported as unattributable rather than as a number. When the bucket is quiet, the delta across the failing call is that call's charge, and anything above the query's normal cost is the penalty."),
 ("What counts as the query's normal cost for the comparison?",
  "What the same document costs when it finishes, which is a number you measure rather than guess: add rateLimit { cost } to the query and read it back on a run that succeeds, usually against a smaller target. That is a separate note in this section. Pass the figure with --normal-cost so the subtraction has something to compare against; left at the default of 1, the script will still report the charge but the penalty it names will be an overestimate."),
 ("The query returns in eight seconds and never fails. Is that fine?",
  "It is a finding, and the script reports it as one. Eight seconds is eighty per cent of the cutoff on a limit you do not control, against data that only grows, so the query is one busy repository away from failing every night. It will also fail at the least convenient moment, since the slowest runs are the ones with the most to report. Shrinking it while it still works is very much cheaper than shrinking it during an incident."),
],
"related": [
 ("/github/graphql-cost-not-measured/", "What the query costs when it does finish"),
 ("/github/graphql-rate-limited/", "The budget the penalty is deducted from"),
 ("/github/request-timeout-502/", "The REST version of a request that ran too long"),
],
"citations": [CITE_GQL_RESOURCE, CITE_GQL_RATE, CITE_REST_RATE_LIMIT, CITE_GQL_GUIDE],
},

]
