"""Day 95 -- 2026-07-28 -- Broken link reporter."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "broken-link-reporter"
NAME = "Broken link reporter"

SPEC = {
 "slug": SLUG, "date": "2026-07-28", "name": NAME,
 "tagline": ("Crawls your own site weekly, checks every link that leaves a page, and reports "
             "the ones that are broken in a way that says which page to edit -- ordered by how "
             "many people actually hit them."),
 "lede": ("A small system that crawls your site, follows every internal and external link, and "
          "reports what is broken, ordered by how much traffic the containing page gets. It "
          "distinguishes a page that is gone from a site that is briefly down, and it never "
          "edits anything. Seven posts on the same system -- one diagram at a time -- with a "
          "cost breakdown and an engineering reference at the end."),
 "keywords": ["broken links", "site maintenance", "SEO", "crawling", "web", "serverless"],
 "icons": ["link", "search", "report"],
 "faq": [
  ("What is a broken link reporter?",
   "A small serverless system that crawls your own site weekly, checks every link on every "
   "page, and reports the broken ones with the page they are on and how much traffic that page "
   "gets. It reports; it never edits a page."),
  ("Why not one of the many existing tools?",
   "Plenty are good and this is genuinely a build-or-buy decision. What a small custom one gives "
   "you is ordering by your own traffic data, a report shaped like your own site, and no "
   "per-page pricing on a site that has grown to a few thousand pages."),
  ("How does it tell a dead link from a site being down?",
   "It does not, on the first check. A failure has to persist across three consecutive weekly "
   "runs before it is reported, which removes almost all transient noise at the cost of a "
   "fortnight's delay on genuinely new breakage."),
  ("Does it respect robots.txt?",
   "On your own site it reads it and follows it, because a path you have disallowed is a path "
   "you do not want crawled. For external link checks it makes a single HEAD request per URL and "
   "caches the result, which is about as polite as checking can be."),
  ("What does it cost to run?",
   "A couple of dollars a month for a site of a few thousand pages. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "broken-link-reporter-on-aws",
 "title": "A broken link reporter on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Crawls your site weekly, checks every link, and reports what is broken ordered by "
          "the traffic on the page it is on. AWS, about $2 a month."),
 "og": ("A list of four hundred broken links is not actionable. Ordered by the traffic on the "
        "page containing them, the first six are."),
 "abstract": ("The whole system on one page -- a crawler, a checker and a reporter -- with the "
              "ordering that turns an unreadable list into a morning's work."),
 "lede": ("Every broken-link tool produces the same output and the same outcome: a list of four "
          "hundred URLs, an intention to work through it, and nothing. The list is correct and "
          "unusable, because four hundred items with no priority is not a task. This post walks "
          "through a small system whose main design decision is what order to put things in."),
 "tags": ["broken links", "site maintenance", "SEO", "crawling", "reporting", "serverless"],
 "takeaways": [
  "Crawl weekly, check every link, but only report failures that persist for three runs.",
  "Order by the traffic on the page containing the link, not by the link.",
  "Report the page to edit, not the URL that is broken. Those are different things.",
  "Internal and external breakage are different problems and go to different lists.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Your site", "sub": ["crawled weekly"], "icon": "browser"},
      {"title": "Analytics", "sub": ["pageviews per page"], "icon": "chart"},
      {"title": "Whoever edits", "sub": ["a short ordered list"], "icon": "person"}],
    "inside": [
      {"title": "Crawler", "sub": ["pages, and every", "link on them"], "icon": "search"},
      {"title": "Checker", "sub": ["one request per URL,", "cached"], "icon": "link"},
      {"title": "Reporter", "sub": ["persistent failures,", "by traffic"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "pages and links"},
              {"from": 1, "to": 1, "label": "how much it matters"},
              {"from": 2, "to": 2, "label": "which pages to edit", "up": True}],
    "note": "The output is a list of pages to edit, ordered by how many people see them."}),
   "Three things outside the account, three pieces inside it. Analytics is what turns a correct "
   "list into a useful one, and it is the input most link checkers do not have.",
   "System: a site crawled, links checked, pages to edit reported",
   "Three boxes across the top sit outside the AWS account. On the left, Your site: crawled "
   "weekly. In the middle, Analytics: pageviews per page. On the right, Whoever edits: the "
   "person who receives a short ordered list. Each connects by an arrow to the AWS account "
   "container below. Pages and links flow down into the account. Analytics feeds in how much "
   "each page matters. A list of which pages to edit goes back out. Inside the AWS account are "
   "three components in a row. On the left, the Crawler, which fetches pages and every link on "
   "them. In the middle, the Checker, which makes one request per unique URL and caches the "
   "result. On the right, the Reporter, which surfaces persistent failures ordered by traffic. A "
   "note at the bottom says the output is a list of pages to edit, ordered by how many people "
   "see them."),
  ("h3", "Order by the page, not the link"),
  ("p", "This is the whole design. A conventional report lists broken URLs, and a broken URL that "
        "appears in a footer template is four hundred rows. Ordered that way it dominates the "
        "list; grouped by page it is one fix."),
  ("p", "And the pages are not equal. A dead link on a page nobody visits costs approximately "
        "nothing; the same dead link on your third most-visited page costs a customer. Ordering "
        "by pageviews turns four hundred rows into a first line that says \"six broken links on "
        "your pricing page, which had 4,100 views last month\", which is a thing somebody does "
        "on a Tuesday morning."),
  ("h3", "What runs weekly (the inside)"),
  ("ul", [
   "<strong>The crawler.</strong> Starts from the sitemap and the home page, follows internal "
   "links, and records every link it finds along with the page it was on. Part 2 covers the "
   "boundaries: what it follows, what it records without following, and where it stops.",
   "<strong>The checker.</strong> One request per unique URL, cached, with results shared across "
   "every page that links to it. A URL in a site-wide footer is checked once, not four hundred "
   "times, which matters both for cost and for not hammering somebody else's server.",
   "<strong>The reporter.</strong> Applies the three-run rule, joins to traffic, groups by page, "
   "and produces a list short enough to act on. Part 5 is about what it leaves out.",
  ]),
  ("h2", "One link, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Found", "sub": ["on a page, while crawling"], "icon": "search"},
      {"title": "Checked", "sub": ["once per unique URL"], "icon": "link"},
      {"title": "Failed", "sub": ["run 1"], "icon": "alarm"},
      {"title": "Failed again", "sub": ["runs 2 and 3"], "icon": "retry"},
      {"title": "Reported", "sub": ["with its page and traffic"], "icon": "report"}],
    "title": "ONE BROKEN LINK, END TO END",
    "note": "Three weeks before reporting. Almost everything transient resolves itself by then."}),
   "The same system as one line. The deliberate delay between the first failure and the report "
   "is what keeps the list short enough to be worth reading.",
   "One broken link from discovery to report, in five stages",
   "A horizontal row of five boxes joined by arrows. Found: on a page, while crawling. Checked: "
   "once per unique URL. Failed: on run one. Failed again: on runs two and three. Reported: with "
   "its page and that page's traffic. A note says three weeks before reporting, and almost "
   "everything transient resolves itself by then."),
  ("h2", "In plain words"),
  ("p", "A site has about two thousand pages accumulated over eight years. The first full run "
        "finds four hundred and eleven links that fail. A conventional tool would send that list "
        "and nothing would happen, because four hundred and eleven is not a number anybody "
        "starts."),
  ("p", "This one waits three weeks. By the third run, sixty-odd have resolved themselves &mdash; "
        "sites that were down, rate limits, a certificate that was renewed. Three hundred and "
        "forty-seven remain. Grouped by containing page that is a hundred and twelve pages, and "
        "ordered by traffic the first six pages account for eleven thousand views a month and "
        "twenty-two broken links between them."),
  ("p", "The report leads with those six. Somebody spends forty minutes on a Tuesday and fixes "
        "the links that most of the site's visitors would have hit. The remaining hundred and six "
        "pages, with about eight hundred views a month between them, are on page two of the "
        "report and will get done eventually or will not, and either outcome is fine. That is the "
        "difference between a list and a priority."),
  ("callout", "Design rules that shaped every decision", [
   "Report pages, not URLs. A footer link is one fix, not four hundred rows.",
   "Order by the traffic on the containing page. A broken link nobody sees is not a problem "
   "worth anybody's Tuesday.",
   "Three runs before reporting. Almost all transient failures resolve within a fortnight.",
   "One request per unique URL, cached. Politeness to other people's servers is not optional.",
   "Internal and external breakage are separate lists, because they have different fixes and "
   "different owners.",
   "It never edits a page. The output is a list; the fix is a person's.",
  ]),
  ("h2", "Why this shape"),
  ("p", "There is no shortage of link checkers and most of them are technically fine. What they "
        "share is an output shaped by what is easy to produce rather than by what somebody can "
        "act on, and the result is that broken-link reports are famously generated and famously "
        "ignored."),
  ("p", "So this design spends its effort on three things a generic tool cannot do: it knows "
        "which of your pages people actually read, it waits long enough to be confident, and it "
        "groups by the unit of work &mdash; a page somebody opens in an editor &mdash; rather "
        "than by the unit of failure. The crawling itself is the least interesting part."),
  ("p", "The next four posts walk through each piece: how the crawl is bounded, how a link is "
        "checked politely, the three-run rule, and what the report leaves out. One diagram per "
        "post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-the-crawl-is-bounded",
 "title": "How the crawl is bounded",
 "nav": "How it is bounded",
 "read": 5, "words": 750,
 "desc": ("Where to start, what to follow, what to record without following, and the four traps "
          "that turn a crawl into an infinite one."),
 "og": ("Crawling your own site is easy until a calendar widget generates a link for every day "
        "until 2087. Four bounds, and the fourth is a hard page cap."),
 "abstract": ("Where a crawl starts, what it follows versus records, the four traps that produce "
              "an unbounded crawl, and the cap that ends the argument."),
 "lede": ("Crawling your own site is a solved problem right up until it is not, and the way it "
          "stops being solved is always the same: something on the site generates links, and the "
          "crawler follows them forever."),
 "tags": ["crawling", "broken links", "robots.txt", "site maintenance", "web", "serverless"],
 "takeaways": [
  "Start from the sitemap, and separately from the home page, because they disagree.",
  "Follow internal HTML links. Record everything else without following it.",
  "Four traps: calendars, faceted filters, session parameters, and infinite pagination.",
  "Normalise URLs before deduplicating, or the same page is crawled forty times.",
  "A hard page cap, because no bound is perfect and an unbounded crawl is expensive.",
 ],
 "blocks": [
  ("h2", "Two starting points"),
  ("p", "The sitemap and the home page find different things, and the difference between them is "
        "itself useful. Pages in the sitemap that are not reachable by following links are "
        "orphans. Pages reachable by links that are not in the sitemap are missing from it. Both "
        "are worth knowing and neither is visible from a single starting point."),
  ("fig", ("chain", {
    "entry": {"title": "Start", "sub": ["sitemap and home"], "icon": "browser"},
    "steps": [
      {"title": "Read robots.txt", "sub": ["and obey it on your own site"], "icon": "doc"},
      {"title": "Internal HTML link?", "sub": ["same host, text/html"], "icon": "branch",
       "exit": {"title": "Record, do not follow", "sub": ["PDFs, images, externals"],
                "icon": "log", "label": "no"}},
      {"title": "Normalise the URL", "sub": ["before deduplicating"], "icon": "filter"},
      {"title": "Seen it?", "sub": ["after normalising"], "icon": "branch",
       "exit": {"title": "Skip", "sub": ["the usual outcome"], "icon": "check", "label": "yes"}},
      {"title": "Fetch and parse", "sub": ["until the cap"], "icon": "search"}],
    "note": "Normalising before deduplicating is the difference between 2,000 pages and 40,000."}),
   "The crawl loop. Normalisation before deduplication is the single line that decides whether "
   "the crawl finishes.",
   "How the site crawl is bounded",
   "A vertical chain of five steps entered by a box labelled Start, from the sitemap and the "
   "home page. Step one reads robots.txt and obeys it on your own site. Step two asks whether "
   "this is an internal HTML link on the same host; if not it exits to Record but do not follow, "
   "covering PDFs, images and external links. Step three normalises the URL before "
   "deduplicating. Step four asks whether it has been seen after normalising; if so it exits to "
   "Skip, the usual outcome. Step five fetches and parses, up to the cap. A note says "
   "normalising before deduplicating is the difference between two thousand pages and forty "
   "thousand."),
  ("h3", "Normalisation"),
  ("p", "The same page is reachable as <code>/about</code>, <code>/about/</code>, "
        "<code>/About</code>, <code>/about?utm_source=x</code> and <code>/about#team</code>. "
        "Without normalisation the crawler treats those as five pages, fetches each, and finds "
        "the same links five times."),
  ("ul", [
   "<strong>Drop the fragment.</strong> It never changes what the server returns.",
   "<strong>Drop known tracking parameters.</strong> The utm family, click identifiers, and "
   "whatever your own analytics adds.",
   "<strong>Sort remaining query parameters.</strong> <code>?a=1&amp;b=2</code> and "
   "<code>?b=2&amp;a=1</code> are the same page.",
   "<strong>Lowercase the host, keep the path's case.</strong> Hosts are case-insensitive and "
   "paths frequently are not.",
   "<strong>Resolve the trailing slash</strong> according to what your server actually does, "
   "which you can determine once by asking it.",
  ]),
  ("h2", "The four traps"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Calendars", "sub": ["next month, forever"], "icon": "calendar"},
      {"title": "Faceted filters", "sub": ["every combination"], "icon": "filter"},
      {"title": "Session parameters", "sub": ["a new URL each visit"], "icon": "key"},
      {"title": "Infinite pagination", "sub": ["page=9999 returns a page"], "icon": "retry"},
      {"title": "A page cap", "sub": ["because none of these is fully solved"], "icon": "stop"}],
    "title": "FOUR WAYS A CRAWL NEVER ENDS",
    "note": "The cap is not a fallback for bad rules. It is the acknowledgement that rules leak."}),
   "The four patterns that generate infinite URL space, and the cap that acknowledges no pattern "
   "list is complete.",
   "Four crawl traps and the page cap that bounds them",
   "A horizontal row of five boxes. Calendars: a link to next month, forever. Faceted filters: "
   "every combination of facets. Session parameters: a new URL on each visit. Infinite "
   "pagination: page equals nine thousand still returns a page. A page cap: because none of "
   "these is fully solved. A note says the cap is not a fallback for bad rules but the "
   "acknowledgement that rules leak."),
  ("p", "Each trap has a rule that mostly works &mdash; skip URLs with a date parameter beyond "
        "some horizon, cap the number of query parameters, drop session-looking parameters, stop "
        "paginating when a page has no new links. None of them is complete, and the fifth "
        "measure is the one that actually guarantees termination: a hard cap on pages fetched per "
        "run, with the cap reported when it is hit."),
  ("p", "Hitting the cap is information rather than a failure. \"Stopped at 5,000 pages\" on a "
        "site you believe has two thousand means something is generating URLs, and finding out "
        "what is usually worth more than the link report."),
  ("h3", "Record without following"),
  ("p", "A PDF, an image, an external link and a <code>mailto:</code> are all recorded as links "
        "to check and never fetched as pages to parse. That distinction keeps the crawl inside "
        "your own site while still checking everything that leaves it, which is where most "
        "breakage lives."),
  ("p", "Next: how a link gets checked without being rude about it."),
 ],
},
{
 "slug": "how-a-link-gets-checked-politely",
 "title": "How a link gets checked politely",
 "nav": "How it is checked",
 "read": 5, "words": 750,
 "desc": ("HEAD then GET, one request per unique URL, per-host rate limits, and the status codes "
          "that do not mean what they say."),
 "og": ("A link checker is a robot pointed at other people's servers. One request per unique "
        "URL, rate-limited per host, and a cache that means the second page linking there costs "
        "nothing."),
 "abstract": ("HEAD before GET, one request per unique URL with a shared cache, per-host rate "
              "limits, and the status codes that do not mean what they appear to."),
 "lede": ("Checking external links means pointing a robot at several hundred other people's "
          "servers every week. Doing that carelessly gets you blocked, which breaks the checker, "
          "and it is also just rude. This post is about doing it properly, and about the status "
          "codes that lie."),
 "tags": ["broken links", "HTTP", "rate limiting", "crawling", "politeness", "serverless"],
 "takeaways": [
  "One request per unique URL per run, with the result shared by every page linking to it.",
  "HEAD first, GET only if HEAD is refused. Many servers dislike HEAD.",
  "Rate limit per host, not globally. One slow host must not stall the run.",
  "403 and 429 usually mean 'not to a robot', not 'broken'.",
  "A soft 404 -- a 200 that says the page is gone -- needs its own check.",
 ],
 "blocks": [
  ("h2", "The request"),
  ("fig", ("chain", {
    "entry": {"title": "A unique URL", "sub": ["from the crawl"], "icon": "link"},
    "steps": [
      {"title": "In the cache?", "sub": ["this run"], "icon": "branch",
       "exit": {"title": "Reuse", "sub": ["a footer link is checked once"], "icon": "check",
                "label": "yes"}},
      {"title": "Host rate limit", "sub": ["wait if needed"], "icon": "clock"},
      {"title": "HEAD", "sub": ["cheapest possible"], "icon": "search",
       "exit": {"title": "405 or 501", "sub": ["try GET instead"], "icon": "retry",
                "label": "refused"}},
      {"title": "Interpret the status", "sub": ["not all failures are"], "icon": "filter"},
      {"title": "Cache the result", "sub": ["for every page linking here"], "icon": "database"}],
    "note": "A site-wide footer link is one request per run, not one per page."}),
   "How one URL is checked. The cache is the difference between a few thousand requests and a "
   "few hundred thousand.",
   "How a single link is checked politely",
   "A vertical chain of five steps entered by a box labelled A unique URL, from the crawl. Step "
   "one asks whether it is in the cache for this run; if so it exits to Reuse, so a footer link "
   "is checked once. Step two applies the per-host rate limit, waiting if needed. Step three "
   "sends a HEAD request as the cheapest option; a 405 or 501 exits to try GET instead. Step "
   "four interprets the status, since not all failures are failures. Step five caches the result "
   "for every page linking there. A note says a site-wide footer link is one request per run "
   "rather than one per page."),
  ("h3", "Rate limiting per host"),
  ("p", "A global rate limit is the obvious implementation and it has the wrong shape: it either "
        "hammers a single small host that happens to be linked forty times, or it slows the whole "
        "run to the speed of the slowest server."),
  ("p", "Per-host limits &mdash; say one request a second to any single host, with several hosts "
        "in flight &mdash; solve both. It also means one unresponsive server delays only its own "
        "links, and a timeout budget per host keeps a dead domain from consuming the run."),
  ("h2", "Status codes that lie"),
  ("table", ["Code", "Looks like", "Usually means"], [
   ["403", "Forbidden", "The server does not serve robots. Not broken."],
   ["429", "Too many requests", "You went too fast. Back off and retry."],
   ["405", "Method not allowed", "HEAD is refused. Try GET."],
   ["999", "Nonsense", "One large social network's way of saying no. Not broken."],
   ["503", "Unavailable", "Often temporary, sometimes a bot wall. Retry next run."],
   ["200", "Fine", "Sometimes a soft 404. Check the content."],
  ]),
  ("p", "The first four are the reason a naive checker produces a report full of links that are "
        "perfectly fine. A 403 from a site that blocks automated requests is not a broken link "
        "and reporting it teaches whoever reads the report that the report is wrong."),
  ("p", "So those codes are recorded as <code>unverifiable</code> rather than broken. They appear "
        "in a separate short section of the report, once, with an explanation &mdash; because a "
        "person checking one by hand is a perfectly reasonable resolution and telling them "
        "twenty times is not."),
  ("h3", "Soft 404s"),
  ("p", "A page that returns 200 and says \"this page no longer exists\" is broken in every way "
        "that matters to a reader and invisible to a status check. They are common on sites that "
        "have been migrated, where the new platform serves a friendly page instead of a 404."),
  ("fig", ("strip", {
    "stages": [
      {"title": "200 OK", "sub": ["looks fine"], "icon": "check"},
      {"title": "Body says gone", "sub": ["'page not found'"], "icon": "search"},
      {"title": "Or: very short", "sub": ["under a threshold"], "icon": "counter"},
      {"title": "Or: redirected", "sub": ["to the home page"], "icon": "retry"},
      {"title": "Soft 404", "sub": ["reported as broken"], "icon": "alarm"}],
    "title": "THREE SIGNS OF A SOFT 404",
    "note": "The third is the strongest: a redirect to the home page is almost always a dead page."}),
   "How a soft 404 is detected. A redirect to the site root is the most reliable of the three "
   "signals and the cheapest to check.",
   "Three ways to detect a soft 404 behind a 200 response",
   "A horizontal row of five boxes. 200 OK: looks fine. Body says gone: containing text like "
   "page not found. Or very short: under a length threshold. Or redirected: to the home page. "
   "Soft 404: reported as broken. A note says the third is the strongest signal, because a "
   "redirect to the home page is almost always a dead page."),
  ("p", "Checking for soft 404s means fetching the body rather than just a HEAD, which costs "
        "more. So it is done only for external links that have redirected, and for internal links "
        "always &mdash; where it is cheap and where a migrated site is most likely to have them."),
  ("p", "Next: the three-run rule, which is what keeps the report short."),
 ],
},
{
 "slug": "how-the-three-run-rule-works",
 "title": "How the three-run rule works",
 "nav": "How it confirms",
 "read": 5, "words": 730,
 "desc": ("Why a failure has to persist for three weeks, what that costs, and the one class of "
          "failure that skips it entirely."),
 "og": ("A single failed check means very little. Three consecutive weekly failures means "
        "something. The fortnight of delay is the price of a report people believe."),
 "abstract": ("Why a failure must persist across three weekly runs, what that delay costs, and "
              "the one class of failure that bypasses it entirely."),
 "lede": ("The three-run rule is the least sophisticated idea in this system and does more for "
          "the quality of the output than anything else in it. Most things that fail once are "
          "fine, and a report that includes them is a report that is wrong often enough to be "
          "discounted."),
 "tags": ["broken links", "false positives", "monitoring", "reporting", "site maintenance",
          "serverless"],
 "takeaways": [
  "A failure must appear in three consecutive weekly runs before it is reported.",
  "That removes the large majority of transient failures at a cost of two weeks.",
  "Internal 404s skip the rule, because your own site being down is a different alarm.",
  "A link that starts failing and then recovers is recorded as flaky, not forgotten.",
  "A link that disappears from the site is closed rather than counted as fixed.",
 ],
 "blocks": [
  ("h2", "Three runs"),
  ("fig", ("chain", {
    "entry": {"title": "A failed check", "sub": ["this week"], "icon": "alarm"},
    "steps": [
      {"title": "Internal 404?", "sub": ["your own site"], "icon": "branch",
       "exit": {"title": "Report now", "sub": ["skip the rule entirely"], "icon": "bell",
                "label": "yes"}},
      {"title": "Failed last week?", "icon": "branch",
       "exit": {"title": "Hold", "sub": ["strike one"], "icon": "clock", "label": "no"}},
      {"title": "And the week before?", "icon": "branch",
       "exit": {"title": "Hold", "sub": ["strike two"], "icon": "clock", "label": "no"}},
      {"title": "Three in a row", "sub": ["with the same status"], "icon": "counter"},
      {"title": "Report it", "sub": ["with the page and the traffic"], "icon": "report"}],
    "note": "Internal 404s skip everything. A broken link on your own site is your own bug."}),
   "The three-run rule and its one exception. An internal 404 is not a transient network "
   "condition; it is a page that is missing from a site you control.",
   "How the three-run confirmation rule works",
   "A vertical chain of five steps entered by a box labelled A failed check, this week. Step one "
   "asks whether it is an internal 404 on your own site; if so it exits to Report now, skipping "
   "the rule entirely. Step two asks whether it also failed last week; if not it exits to Hold, "
   "strike one. Step three asks whether it failed the week before that; if not it exits to Hold, "
   "strike two. Step four confirms three failures in a row with the same status. Step five "
   "reports it, with the page and the traffic. A note says internal 404s skip everything, "
   "because a broken link on your own site is your own bug."),
  ("h3", "What two weeks costs"),
  ("p", "It is worth being explicit: a link that genuinely breaks on the Monday after a run will "
        "not be reported for nearly three weeks. That is a real cost and it is the right trade "
        "for external links, where the alternative is a report containing dozens of sites that "
        "happened to be down for ten minutes."),
  ("p", "For internal links it is not the right trade at all, which is why they skip the rule. A "
        "404 on your own site is either a page you deleted or a link you typed wrong, and neither "
        "gets better by waiting a fortnight."),
  ("h3", "Same status, not just failing"),
  ("p", "Three failures in a row only counts when they are the same kind of failure. A URL that "
        "returns a timeout, then a 500, then a 403 is behaving oddly rather than being "
        "consistently gone, and it is more likely to be a struggling server than a dead page."),
  ("p", "That distinction is recorded: a link with three different failure modes across three "
        "runs goes into a small \"unstable\" list rather than the main report. In practice those "
        "are frequently the most interesting entries, because a site that is intermittently "
        "failing is a site that is about to disappear."),
  ("h2", "Flaky and disappeared"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Fails", "sub": ["run 1"], "icon": "alarm"},
      {"title": "Recovers", "sub": ["run 2"], "icon": "check"},
      {"title": "Fails again", "sub": ["run 3"], "icon": "retry"},
      {"title": "Flaky", "sub": ["counted, not reported"], "icon": "counter"},
      {"title": "Four times in ten", "sub": ["now it is reported"], "icon": "report"}],
    "title": "A LINK THAT KEEPS RECOVERING",
    "note": "Resetting the counter on every recovery means a genuinely flaky link is never reported."}),
   "Why recoveries do not simply reset the count. A link that fails four weeks out of ten is "
   "broken for a lot of readers and a naive three-in-a-row rule would never surface it.",
   "How an intermittently failing link is eventually reported",
   "A horizontal row of five boxes. Fails: on run one. Recovers: on run two. Fails again: on run "
   "three. Flaky: counted rather than reported. Four times in ten: now it is reported. A note "
   "says resetting the counter on every recovery means a genuinely flaky link is never reported."),
  ("p", "So there are two counters: consecutive failures, which drives the main report, and "
        "failures in the last ten runs, which catches the flaky ones. Four in ten is a reasonable "
        "threshold and it surfaces a category that a strict consecutive rule misses entirely."),
  ("h3", "Links that disappear"),
  ("p", "A broken link that stops appearing in the crawl has been removed from the site, which "
        "means somebody fixed it &mdash; or means the page containing it was deleted. Both are "
        "resolutions and neither should be counted as a fix in a way that implies somebody "
        "acted."),
  ("p", "So it closes as <code>gone</code> rather than <code>fixed</code>, with a note of which "
        "page it was on and whether that page still exists. The distinction matters for the one "
        "statistic worth watching, which Part 5 covers."),
  ("p", "Next: what the report says, and what it deliberately leaves out."),
 ],
},
{
 "slug": "how-the-link-report-is-ordered",
 "title": "How the link report is ordered",
 "nav": "How it is ordered",
 "read": 5, "words": 730,
 "desc": ("Grouping by page, ordering by traffic, the length limit, and the one number that says "
          "whether the site is getting better or worse."),
 "og": ("Six pages, twenty-two links, eleven thousand views. That is a Tuesday morning. Four "
        "hundred rows is not."),
 "abstract": ("Grouping by page, ordering by traffic, why the report has a hard length limit, "
              "and the one number that says whether the site is improving."),
 "lede": ("Everything up to here has been in service of one page of output. This post is about "
          "what goes on it, and rather more about what does not."),
 "tags": ["broken links", "reporting", "prioritisation", "site maintenance", "SEO", "serverless"],
 "takeaways": [
  "Grouped by page, ordered by that page's pageviews, capped at ten pages.",
  "Internal breakage is a separate, shorter, always-first section.",
  "Unverifiable links get one line, not one line each.",
  "The number to watch is broken links on the top twenty pages, and it should trend to zero.",
  "The full list is a link, never the message.",
 ],
 "blocks": [
  ("h2", "What the report says"),
  ("callout", "Weekly link report", [
   "<strong>Internal &mdash; 4 broken links across 3 pages.</strong> These are on your own site "
   "and are listed first regardless of traffic.",
   "<strong>/pricing &mdash; 6 links, 4,100 views/month.</strong> Four to a supplier site that "
   "moved, two to a PDF that no longer exists.",
   "<strong>/guides/getting-started &mdash; 5 links, 2,800 views/month.</strong>",
   "<strong>Four more pages</strong> with 1&ndash;3 links each, 400&ndash;900 views/month.",
   "<strong>102 further pages</strong> with broken links, 6 views/month or fewer between them. "
   "<em>Full list &rarr;</em>",
   "<strong>31 links could not be checked</strong> (403 or 429 &mdash; usually bot blocking). "
   "<em>List &rarr;</em>",
  ]),
  ("p", "Six lines. The first four are a morning's work and cover the pages nearly all of the "
        "site's readers see. The fifth exists so nobody thinks the report is hiding anything, and "
        "it is a link rather than three hundred rows."),
  ("h2", "Why cap the length"),
  ("fig", ("chain", {
    "entry": {"title": "347 broken links", "sub": ["confirmed"], "icon": "counter"},
    "steps": [
      {"title": "Group by page", "sub": ["112 pages"], "icon": "filter"},
      {"title": "Join to traffic", "sub": ["pageviews, last 30 days"], "icon": "chart",
       "side": {"title": "Analytics", "sub": ["per page"], "icon": "report"}},
      {"title": "Order by views", "sub": ["descending"], "icon": "search"},
      {"title": "Take ten", "sub": ["the rest is a link"], "icon": "stop"},
      {"title": "One page of output", "sub": ["actionable"], "icon": "check"}],
    "note": "Ten is not a limit on what is known. It is a limit on what is asked of somebody."}),
   "How three hundred and forty-seven findings become a page somebody reads. The cap is about "
   "the reader rather than the data.",
   "How the broken link report is grouped, ordered and capped",
   "A vertical chain of five steps entered by a box labelled 347 broken links, confirmed. Step "
   "one groups by page, giving one hundred and twelve pages. Step two joins to traffic, using "
   "pageviews over the last thirty days from analytics. Step three orders by views, descending. "
   "Step four takes ten, and the rest becomes a link. Step five is one page of output that is "
   "actionable. A note says ten is not a limit on what is known but a limit on what is asked of "
   "somebody."),
  ("p", "A report of ten items gets worked through. A report of a hundred and twelve gets skimmed "
        "and closed, and the ten most important items in it are never seen because they are "
        "interleaved with a hundred that do not matter."),
  ("h3", "Traffic is doing the heavy lifting"),
  ("p", "Without it, ordering has to fall back on something weak: the number of broken links per "
        "page, or how long they have been broken. Both correlate poorly with whether anybody "
        "cares. A page with eleven broken links and four views a year is worth nothing; a page "
        "with one and four thousand views a month is worth fixing this morning."),
  ("p", "Any analytics source works, and a rough one is fine. The ordering only needs to be "
        "approximately right, and the difference between the top page and the hundredth is "
        "usually three orders of magnitude, which no amount of measurement error will invert."),
  ("h2", "The number to watch"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Total broken", "sub": ["347, flat"], "icon": "counter"},
      {"title": "On the top 20 pages", "sub": ["22 -> 4"], "icon": "chart"},
      {"title": "That is the number", "sub": ["and it is falling"], "icon": "check"},
      {"title": "The long tail", "sub": ["stays, harmlessly"], "icon": "log"},
      {"title": "Zero is not the goal", "sub": ["on a site of 2,000 pages"], "icon": "search"}],
    "title": "THE ONLY TREND WORTH TRACKING",
    "note": "A total that never falls is fine. Breakage on pages people read should trend to zero."}),
   "The one metric worth watching. Total broken links on an eight-year-old site is a number that "
   "will never be zero and never should be a target.",
   "The one broken-link trend worth tracking",
   "A horizontal row of five boxes. Total broken: three hundred and forty-seven, flat. On the "
   "top twenty pages: down from twenty-two to four. That is the number: and it is falling. The "
   "long tail: stays, harmlessly. Zero is not the goal: on a site of two thousand pages. A note "
   "says a total that never falls is fine, and breakage on pages people read should trend to "
   "zero."),
  ("p", "Setting a target of zero broken links across two thousand pages is how this kind of "
        "project gets abandoned. The tail is old blog posts linking to sites that no longer exist, "
        "and no amount of work makes it stay fixed, because more of the web goes away every year."),
  ("p", "Broken links on the pages that actually get read is a number that can genuinely reach "
        "zero and stay there with about half an hour a month, and it is the one that corresponds "
        "to anybody's experience of the site."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="page crawled",
 volumes=[(2000, "2,000 pages"), (8000, "8,000 pages"), (40000, "40,000 pages")],
 read_each=0.0,
 msgs_each=0.002,
 lede=("A crawl is bandwidth and compute, both of which are cheap, and there is no model in this "
       "system at all. Two thousand pages weekly is a mature small-business site; forty thousand "
       "is four weekly crawls of a large one. Here is where each cent goes."),
 takeaway_extra=("No model, and outbound bandwidth is the only line that scales with site size."),
 risks=[
  "<strong>An unbounded crawl.</strong> A calendar widget or a faceted filter turns two thousand "
  "pages into two hundred thousand, and the Lambda time is the smallest part of that problem. "
  "The page cap is the control.",
  "<strong>Checking every link on every page.</strong> Without the per-run URL cache, a "
  "site-wide footer with twelve external links costs twenty-four thousand requests instead of "
  "twelve, and will get you blocked.",
  "<strong>Log retention left at never.</strong> A crawl produces a log line per page by "
  "default, which at eight thousand pages a week is the entire bill within a year.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. The cost is Lambda duration "
                "and outbound requests, and both are small enough that the fixed band dominates "
                "until the site is very large."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="bl",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the fan-out, and why the crawl is a state machine rather than a loop."),
 outside=[
  {"title": "Your site", "sub": ["and every linked host"], "icon": "browser"},
  {"title": "Analytics", "sub": ["pageviews per path"], "icon": "chart"},
  {"title": "SES outbound", "sub": ["the weekly report"], "icon": "email"}],
 inside=[
  {"title": "SQS + EventBridge", "sub": ["frontier queue,", "weekly trigger"], "icon": "queue"},
  {"title": "Lambda x3", "sub": ["crawl, check, report"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["links, runs"], "icon": "database"}],
 note="us-east-1. One account. No model, and no write access to anything it crawls.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Your site, together with every host it "
  "links to. Analytics, supplying pageviews per path. And SES outbound, carrying the weekly "
  "report. Inside the account, three groups. SQS carrying a frontier queue and EventBridge "
  "providing a weekly trigger. Three Lambda functions named crawl, check and report. And two "
  "DynamoDB tables named links and runs. A note gives the region as us-east-1, one account, no "
  "model, and no write access to anything it crawls."),
 functions=[
  ["<code>bl-crawl</code>", "SQS frontier queue",
   "Fetches one page, extracts links, enqueues new internal pages",
   "30s / 1024&nbsp;MB"],
  ["<code>bl-check</code>", "SQS check queue",
   "HEAD then GET per unique URL, with per-host rate limiting", "60s / 512&nbsp;MB"],
  ["<code>bl-report</code>", "EventBridge weekly",
   "Applies the three-run rule, joins traffic, builds the page", "60s / 1024&nbsp;MB"]],
 roles=[
  ["<code>bl-crawl-role</code>", "<code>dynamodb:PutItem</code>, <code>sqs:SendMessage</code>",
   "The links table; the frontier and check queues"],
  ["<code>bl-check-role</code>", "<code>dynamodb:UpdateItem</code>",
   "The links table only"],
  ["<code>bl-report-role</code>",
   "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>, "
   "<code>secretsmanager:GetSecretValue</code>",
   "Links and runs, read; one identity; the analytics credential"]],
 tables=[
  ("Table: links",
   "PK   url_hash          S   sha256 of the normalised URL\n"
   "     url               S   the normalised URL\n"
   "     internal          BOOL true\n"
   "     found_on          L   [normalised page URLs that link here]\n"
   "     last_status       S   200 | 404 | timeout | 403 | soft404\n"
   "     consecutive_fails N   3\n"
   "     fails_in_last_10  N   4\n"
   "     first_failed_run  S   2026-07-14\n"
   "     state             S   ok | failing | reported | gone | unverifiable\n"
   "     last_run          S   2026-07-28\n\n"
   "`found_on` is the field that makes the report groupable by page. It is a\n"
   "list because a URL in a footer appears on every page on the site."),
  ("Table: runs",
   "PK   run_id            S   2026-07-28\n"
   "     pages_crawled     N   1987\n"
   "     cap_hit           BOOL false   -- true is itself a finding\n"
   "     unique_urls       N   4412\n"
   "     requests_made     N   4412     -- should equal unique_urls, not links found\n"
   "     duration_s        N   412\n"
   "     broken_confirmed  N   347\n"
   "     top20_broken      N   4        -- the number worth trending\n\n"
   "`requests_made` equalling `unique_urls` is the assertion that the cache is\n"
   "working. If it drifts upward, a footer link is being checked per page.")],
 inbound=[
  "<strong>The crawl is a queue, not a loop.</strong> Each page is one SQS message and one "
  "invocation, which means the crawl parallelises, survives a failure on one page, and never "
  "hits a Lambda timeout on a large site.",
  "<strong>robots.txt is fetched once per run</strong> and obeyed on your own site. Disallowed "
  "paths are not crawled.",
  "<strong>Per-host rate limiting</strong> uses a small DynamoDB counter with a conditional "
  "write, so several concurrent checkers cannot collectively exceed one request a second to any "
  "single host.",
  "<strong>The user agent names the business</strong> and links to a page explaining what the "
  "crawler is. A blocked crawler is a broken crawler, and being identifiable is how you get "
  "unblocked."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Crawling, checking and ordering are all "
  "mechanical.",
  "<strong>The one plausible use</strong> would be judging whether a 200 response is a soft 404, "
  "and simple heuristics &mdash; a redirect to the root, a very short body, known phrases "
  "&mdash; do it well enough and for nothing.",
  "<strong>Suggesting replacement URLs</strong> is the other tempting use, and it is worse than "
  "it sounds: a plausible-looking wrong replacement inserted into a page is a more expensive "
  "error than the broken link was.",
  "<strong>The report wording is fixed.</strong> There is nothing per-finding to generate.",
  "<strong>The cost page assumes none</strong>, which is why there is no read band on it."],
 gotchas=[
  "Normalise before deduplicating. It is the difference between crawling two thousand pages and "
  "forty thousand.",
  "Cache check results per run. A site-wide footer link checked once per page will get you rate "
  "limited by somebody, deservedly.",
  "Treat 403 and 429 as unverifiable, not broken. Reporting them teaches the reader that the "
  "report is wrong.",
  "Skip the three-run rule for internal 404s. Your own missing page is not a transient network "
  "condition.",
  "Track broken links on the top twenty pages, not the total. The total on an old site never "
  "reaches zero and setting it as a target is how the whole effort gets abandoned."],
))
