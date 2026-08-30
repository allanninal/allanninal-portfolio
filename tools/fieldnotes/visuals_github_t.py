#!/usr/bin/env python3
"""Diagrams for the /github/ field notes, batch T.

Four more GraphQL notes, and only one of them is about an error arriving. That
made the branches easy to keep apart, because each one sorts a different kind
of object: a document, a walk, an identifier and a credential.

The first sorts documents by price. Its chain is a backfill that gets throttled
while the bucket everybody is watching stays full, and its branch is the only
one in the batch whose rows are rates rather than states, because the whole note
is a ratio between two numbers.

The second sorts a completed walk. Its chain is a migration undertaken to escape
a ceiling and landing on the same one, and its branch puts a truncated walk and
a complete walk next to each other, since both end with hasNextPage false and no
error at all.

The third sorts identifiers. Nothing in its branch is a response: the rows are
shapes of stored string, which is right, because the bug lives in a database
column and the API never sees it.

The fourth sorts refusals by which credential they blame. Its chain is an hour
spent looking for a header that does not exist, and its branch keeps the 404 row
deliberately unresolved, because converting it into a no is the mistake the note
is written to prevent.

Drawn in GitHub blue. No em dashes inside SVG text: one mis-sniffed encoding
turns a single character into three mojibake ones inside an image, where nothing
downstream will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be
# active across exactly this file and no further.
BRAND = "#0969DA"
D.set_theme(BRAND)

V = {}

V["github/graphql-mutation-secondary-cost"] = {
    "flow_intro": (
        "The parser earns its place twice. It is the guard that keeps a "
        "mutation off the wire, and it is also the pricer, because the "
        "question the secondary limit asks of a request is exactly the "
        "question the guard asks: does this document contain a mutation. "
        "Everything after it is arithmetic over integers, which is why the "
        "documents can be priced without being sent. The one live call is a "
        "single read query, and the hourly budget beside it comes from a free "
        "REST call, so a throttle you already recorded can be attributed to "
        "the per-minute ceiling rather than to the bucket that was never empty."
    ),
    "diagram_problem": D.chain(
        "ghgqlmut-p",
        "A write loop throttled while the hourly point budget stays full",
        "Every reading here is honest. The bucket that emptied is not the "
        "bucket anybody can see, and it has no gauge at all.",
        [
            ("Backfill of 11,000 rows", "one mutation per row"),
            ("Concurrency raised", "500 requests a minute"),
            ("403 after 11 minutes", "secondary rate limit"),
            ("Budget checked", "4,863 points left"),
            ("Retry loop added", "and it throttles harder"),
        ],
        fail_at=1,
        loop=(4, 2, "and the wrong bucket is watched again"),
    ),
    "diagram_fix": D.branch(
        "ghgqlmut-f",
        "Sorting a GraphQL document by what one request of it costs a minute",
        "The first and third rows are the same request rate. One of them is "
        "over the wall and the other is a fifth of the way to it.",
        ("One document, priced", "5 points if it mutates, 1 if not"),
        [
            ("Mutations at 500 a minute", "2,500 points against a limit of 2,000", "bad"),
            ("Secondary 403, budget fine", "the per-minute ceiling, not the hour", "bad"),
            ("Queries at 500 a minute", "500 points, a fifth of the ceiling", "plain"),
            ("Batched and serialised", "five points buys the whole document", "good"),
        ],
    ),
}

V["github/graphql-search-same-1000-cap"] = {
    "flow_intro": (
        "The walk itself is four lines and the arithmetic around it is the "
        "note. Reachable and unreachable halves of a match count, pages that "
        "fit under the ceiling, slices a partition needs, and the typed "
        "connection that answers the same question without a ceiling are all "
        "computed rather than fetched. The live part pages the search "
        "connection with after: endCursor until it stops, then compares what "
        "it collected against what the index said it matched. That comparison "
        "is the only thing separating a truncated answer from a complete one, "
        "because both of them end the same way and neither raises an error."
    ),
    "diagram_problem": D.chain(
        "ghgqlsrch-p",
        "A search migration that escapes a loud ceiling and lands on a quiet one",
        "The rewrite is better in every visible way. It also returns six per "
        "cent of the data, and every improvement hides the loss.",
        [
            ("REST 422 on page 11", "the loud ceiling"),
            ("Rewritten in GraphQL", "cursors, no page numbers"),
            ("hasNextPage goes false", "after 1,000 nodes"),
            ("Loop exits cleanly", "no error anywhere"),
            ("issueCount says 18,231", "and nobody reads it"),
        ],
        fail_at=1,
        loop=(4, 2, "and the next export is trusted too"),
    ),
    "diagram_fix": D.branch(
        "ghgqlsrch-f",
        "Sorting a finished walk by its node count against the index match count",
        "The top row and the bottom row are the same shape of ending. Only "
        "the count the index reported tells them apart.",
        ("Nodes collected", "against issueCount"),
        [
            ("1,000 of 18,231, no error", "the ceiling, arriving silently", "bad"),
            ("Short and under 1,000", "a timed-out search, another note", "plain"),
            ("Inventory, not a ranking", "typed connection, no ceiling at all", "good"),
            ("Collected equals the count", "this answer really is whole", "good"),
        ],
    ),
}

V["github/graphql-id-vs-databaseid"] = {
    "flow_intro": (
        "Almost all of this runs without a token. Which key space a string "
        "belongs to, what a legacy node id decodes to, how many rows a join "
        "recovers across two spaces and after normalising to one, and which "
        "stored ids can be rewritten offline are all decided locally. The live "
        "part is deliberately tiny: one REST read and one GraphQL read of the "
        "same issue, whose only job is to show on real data what the pure "
        "functions assert about fixtures. The four identifiers are printed "
        "together because seeing them lined up is what makes the crosswalk "
        "stick, and because two of them are integers that are not the same."
    ),
    "diagram_problem": D.chain(
        "ghgqlid-p",
        "Two correct writers filling one column with two different key spaces",
        "Neither side is wrong on its own. Both responses call their own "
        "identifier the id, and the column accepts whatever arrived.",
        [
            ("REST importer stores id", "1347"),
            ("GraphQL sync stores id", "MDU6SXNzdWUxMzQ3"),
            ("One column, two spaces", "both called the id"),
            ("Join returns zero rows", "and nothing throws"),
            ("Blamed on timestamps", "for three days"),
        ],
        fail_at=1,
        loop=(4, 2, "and duplicate rows keep arriving"),
    ),
    "diagram_fix": D.branch(
        "ghgqlid-f",
        "Sorting a stored identifier by which of the two key spaces it belongs to",
        "Not one of these rows is about a response. The bug lives in a "
        "column, and the two middle rows decide how big the migration is.",
        ("Each identifier in the store", "classified before it is joined"),
        [
            ("Numeric and node ids mixed", "one entity keyed two ways", "bad"),
            ("Legacy node id", "decodes to a number offline", "plain"),
            ("New format node id", "opaque, has to be refetched", "bad"),
            ("One space everywhere", "and number kept out of it", "good"),
        ],
    ),
}

V["github/resource-not-accessible-by-pat"] = {
    "flow_intro": (
        "Two things have to be established and they need different evidence. "
        "What the endpoint wanted is a header, so it is parsed carefully: "
        "commas separate alternatives and semicolons join requirements, and "
        "flattening the two is how somebody grants more than was ever asked "
        "for. What the token holds cannot be read anywhere, so it is measured "
        "with one cheap request per permission, and the measurement has three "
        "outcomes rather than two because a 404 is not a no. The credential "
        "itself is identified from a prefix and from a header that is missing, "
        "and the same refusal is then shown arriving through GraphQL with no "
        "header attached to it at all."
    ),
    "diagram_problem": D.chain(
        "ghfgpat-p",
        "An hour spent looking for a header a fine-grained token never sends",
        "The token authenticates, reads the repository and refuses one call. "
        "The half of the diff you want to read does not exist.",
        [
            ("Fine grained token minted", "permissions ticked by hand"),
            ("403 on one endpoint", "not accessible by this token"),
            ("Token page reread", "the list still looks right"),
            ("No scope header exists", "nothing says what it holds"),
            ("Endpoint blamed instead", "for an hour"),
        ],
        fail_at=1,
        loop=(4, 2, "and the same box is ticked again"),
    ),
    "diagram_fix": D.branch(
        "ghfgpat-f",
        "Sorting a 403 by which credential its message blames, then probing",
        "The second row is a different note entirely. The third is left "
        "unresolved on purpose, because turning it into a no picks the "
        "wrong box.",
        ("One refusal, then five reads", "header read, grants measured"),
        [
            ("Blames the access token", "x-accepted names the permission", "bad"),
            ("Blames an integration", "a GitHub App, another note", "plain"),
            ("404 inside the matrix", "ambiguous, and never a no", "plain"),
            ("Every probe granted", "the token holds what it needs", "good"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
