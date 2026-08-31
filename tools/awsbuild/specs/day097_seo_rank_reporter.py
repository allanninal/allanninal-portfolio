"""Day 97 -- 2026-07-30 -- Search rank reporter."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "seo-rank-reporter"
NAME = "Search rank reporter"

SPEC = {
 "slug": SLUG, "date": "2026-07-30", "name": NAME,
 "tagline": ("Reports where you actually rank for the queries that bring in work, grouped so "
             "that a hundred query rows become six themes, with the pages responsible named."),
 "lede": ("A small system that reads your own search performance data, groups queries into the "
          "themes your business actually cares about, and reports movement that is large enough "
          "to mean something. It never guesses at rankings and it never claims a cause it "
          "cannot see. Seven posts on the same system -- one diagram at a time -- with a cost "
          "breakdown and an engineering reference at the end."),
 "keywords": ["SEO", "search rankings", "Search Console", "reporting", "marketing", "serverless"],
 "icons": ["search", "chart", "report"],
 "faq": [
  ("What is a search rank reporter?",
   "A small serverless system that reads your own search performance data, groups thousands of "
   "query rows into a handful of themes, and reports movement large enough to be real. It works "
   "from your own measured data rather than from simulated searches."),
  ("Why not scrape search results?",
   "Because scraped positions are personalised, localised, and against most search engines' "
   "terms. Your own performance data is the average position real people saw, which is both more "
   "accurate and not a rule you are breaking."),
  ("Why group queries?",
   "Because a report with nine hundred query rows is unreadable and mostly noise. Six themes "
   "that map to what the business sells are a report somebody reads, and the queries are still "
   "there underneath."),
  ("Does it say why something moved?",
   "It says what correlates: a page that changed, a page that was added, a competitor appearing. "
   "It does not claim causation, because search movement has causes no data you hold can see."),
  ("What does it cost to run?",
   "Around a dollar a month. It reads an API weekly. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "seo-rank-reporter-on-aws",
 "title": "A search rank reporter on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Groups thousands of query rows into six themes, reports movement big enough to mean "
          "something, and names the pages responsible. AWS, about $1 a month."),
 "og": ("Nine hundred query rows is not a report. Six themes that map to what the business "
        "sells, with the pages responsible named, is."),
 "abstract": ("The whole system on one page -- a fetcher, a grouper and a reporter -- built "
              "around the fact that the raw data is far too granular to act on."),
 "lede": ("Search data has the opposite problem from most business data: there is too much of it "
          "and it is too detailed. Nine hundred query rows a week, most of them with four "
          "impressions, all of them moving up and down for reasons nobody can see. It is "
          "genuinely informative and completely unreadable, so it gets exported to a spreadsheet "
          "once and never looked at again. This post walks through a small system that turns it "
          "into six lines."),
 "tags": ["SEO", "search rankings", "Search Console", "reporting", "marketing", "serverless"],
 "takeaways": [
  "It reads your own performance data. Nothing is scraped and nothing is simulated.",
  "Queries are grouped into themes you define, so the report matches how you think.",
  "Movement is reported only when the query group has enough volume for it to be real.",
  "The report names the page responsible, because that is what somebody can change.",
  "Designed on AWS for about $1 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Search performance", "sub": ["your own data, by API"], "icon": "search"},
      {"title": "Theme rules", "sub": ["queries to themes"], "icon": "doc"},
      {"title": "Whoever owns the site", "sub": ["six lines a week"], "icon": "person"}],
    "inside": [
      {"title": "Fetcher", "sub": ["weekly, query by page,", "stored raw"], "icon": "database"},
      {"title": "Grouper", "sub": ["900 rows into", "six themes"], "icon": "filter"},
      {"title": "Reporter", "sub": ["movement worth", "reading, with pages"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "impressions, clicks, position"},
              {"from": 1, "to": 1, "label": "what counts as what"},
              {"from": 2, "to": 2, "label": "six lines and the pages", "up": True}],
    "note": "Everything reported is measured. Nothing here estimates a ranking."}),
   "Three things outside the account, three pieces inside it. The theme rules in the middle are "
   "the only part that requires judgement, and they are a sheet.",
   "System: search performance data grouped into themes and reported",
   "Three boxes across the top sit outside the AWS account. On the left, Search performance: your "
   "own data, read through an API. In the middle, Theme rules: the mapping from queries to "
   "themes. On the right, Whoever owns the site: the person who receives six lines a week. Each "
   "connects by an arrow to the AWS account container below. Impressions, clicks and position "
   "flow down into the account. The theme rules feed in what counts as what. Six lines and the "
   "pages responsible go back out. Inside the AWS account are three components in a row. On the "
   "left, the Fetcher, running weekly, pulling data by query and by page and storing it raw. In "
   "the middle, the Grouper, turning nine hundred rows into six themes. On the right, the "
   "Reporter, surfacing movement worth reading together with the pages. A note at the bottom "
   "says everything reported is measured and nothing here estimates a ranking."),
  ("h3", "Measured, not simulated"),
  ("p", "There is an entire industry built on typing your keywords into a search engine from a "
        "datacentre and recording what comes back. It produces a number, and the number is not "
        "what your customers saw: results are personalised, localised, device-dependent and "
        "increasingly assembled per query."),
  ("p", "Your own performance data is the average position across the impressions that actually "
        "happened, to real people, in the places they were. It is the better number by some "
        "distance, it costs nothing, and getting it does not involve breaking anybody's terms of "
        "service."),
  ("h3", "What runs weekly (the inside)"),
  ("ul", [
   "<strong>The fetcher.</strong> Pulls last week's data by query and by page, and stores it raw "
   "before anything is done to it. Part 2 covers the sampling and the delay, both of which "
   "surprise people.",
   "<strong>The grouper.</strong> Maps query rows onto themes using rules you write. Part 3 is "
   "about why the rules are yours rather than generated, and why grouping is the whole product.",
   "<strong>The reporter.</strong> Compares this period with the last, decides what movement is "
   "large enough to be real given the volume behind it, and names the pages that carry each "
   "theme.",
  ]),
  ("h2", "One theme, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Fetched", "sub": ["900 query rows"], "icon": "database"},
      {"title": "Grouped", "sub": ["into 6 themes"], "icon": "filter"},
      {"title": "Compared", "sub": ["to the last 8 weeks"], "icon": "chart"},
      {"title": "Volume check", "sub": ["is the move real?"], "icon": "counter"},
      {"title": "Reported", "sub": ["with the pages"], "icon": "report"}],
    "title": "ONE WEEK, END TO END",
    "note": "The fourth step removes most of what a raw export would have shown you."}),
   "The same system as one line. The volume check is what stops a theme with eleven impressions "
   "appearing next to one with four thousand.",
   "One week of search data from fetch to report, in five stages",
   "A horizontal row of five boxes joined by arrows. Fetched: nine hundred query rows. Grouped: "
   "into six themes. Compared: against the last eight weeks. Volume check: is the movement real. "
   "Reported: with the pages responsible. A note says the fourth step removes most of what a raw "
   "export would have shown you."),
  ("h2", "In plain words"),
  ("p", "A plumbing firm's site gets about nine hundred distinct search queries a week. Grouped, "
        "they fall into six themes that match what the business actually does: emergency "
        "callouts, boiler installation, bathroom fitting, commercial contracts, the company name, "
        "and everything else."),
  ("p", "This week, emergency callouts is down. Average position has gone from 4.1 to 7.8 and "
        "clicks are down sixty per cent, on four thousand impressions &mdash; which is far too "
        "much volume for that to be noise. The theme is carried almost entirely by one page, and "
        "the report says so: \"emergency callouts: position 4.1 to 7.8, clicks down 60%, on "
        "4,100 impressions. 92% of this theme lands on /emergency-plumber.\""),
  ("p", "That is a report somebody acts on within the hour, and it takes about nine seconds to "
        "read. The raw export containing the same information is a hundred and forty rows of "
        "queries containing the word emergency, each with its own small movement, and it "
        "communicates none of it."),
  ("callout", "Design rules that shaped every decision", [
   "Use measured data, never simulated positions. Scraped rankings are a different and worse "
   "number.",
   "Group by theme, always. Query-level reporting is unreadable and mostly noise.",
   "Volume gates everything. A move on eleven impressions is not a move.",
   "Name the page, not the query. Pages are what somebody can change.",
   "Correlate, never claim causation. Search movement has causes no data you hold can see.",
   "Report the same six themes every week, so the report is comparable rather than a fresh "
   "surprise.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The data is already available, free, and accurate. The reason nobody uses it is entirely "
        "about granularity: it arrives at the level of individual queries, and businesses think "
        "at the level of what they sell. Every intermediate tool tries to bridge that with "
        "dashboards, and dashboards have the same problem as spreadsheets &mdash; somebody has to "
        "go and look."),
  ("p", "So this design does one transformation, weekly, and pushes six lines. The transformation "
        "is grouping, the gate is volume, and the addition is naming the page. None of it is "
        "sophisticated and all of it is the difference between data that exists and data that "
        "gets used."),
  ("p", "The next four posts walk through each piece: how the data is fetched, how queries are "
        "grouped, how a real movement is told from noise, and what the report says. One diagram "
        "per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-search-data-gets-fetched",
 "title": "How search data gets fetched",
 "nav": "How it is fetched",
 "read": 5, "words": 750,
 "desc": ("The reporting delay, the row limits that quietly truncate your data, and why the raw "
          "response is stored before anything is done to it."),
 "og": ("Search performance data arrives days late, is sampled, and is truncated by row limits "
        "you did not set. All three are manageable and all three surprise people."),
 "abstract": ("The reporting delay, the row limits that quietly truncate a fetch, the "
              "long-tail queries that are withheld entirely, and why the raw response is stored "
              "first."),
 "lede": ("Fetching search performance data is an API call, and there are three properties of "
          "that data that catch everybody out the first time. None is a problem once you know "
          "about it, and all three will make your numbers wrong if you do not."),
 "tags": ["SEO", "Search Console", "APIs", "data collection", "sampling", "serverless"],
 "takeaways": [
  "The data lags by two to three days. A weekly fetch must not ask for yesterday.",
  "Row limits truncate silently. Paginate, and check whether you hit the limit.",
  "Long-tail and rare queries are withheld entirely, so totals will not reconcile.",
  "Fetch by query and by page separately; the combination is not always available.",
  "Store the raw response before grouping, so a rule change can be applied to history.",
 ],
 "blocks": [
  ("h2", "Three properties that surprise people"),
  ("fig", ("chain", {
    "entry": {"title": "Weekly fetch", "sub": ["for a completed week"], "icon": "clock"},
    "steps": [
      {"title": "Is the data settled?", "sub": ["allow three days"], "icon": "branch",
       "exit": {"title": "Wait", "sub": ["numbers still moving"], "icon": "retry",
                "label": "no"}},
      {"title": "Fetch by query", "sub": ["paginated"], "icon": "search",
       "side": {"title": "Row limit", "sub": ["25,000 per request"], "icon": "counter"}},
      {"title": "Hit the limit?", "sub": ["check, do not assume"], "icon": "branch",
       "exit": {"title": "Paginate again", "sub": ["until short"], "icon": "retry",
                "label": "yes"}},
      {"title": "Fetch by page", "sub": ["a separate request"], "icon": "browser"},
      {"title": "Store raw", "sub": ["before any grouping"], "icon": "database"}],
    "note": "A response exactly at the row limit is almost certainly truncated, not complete."}),
   "How one week is fetched. The truncation check is the one most implementations skip, and it "
   "silently loses the long tail that grouping most depends on.",
   "How a week of search performance data is fetched",
   "A vertical chain of five steps entered by a box labelled Weekly fetch, for a completed week. "
   "Step one asks whether the data is settled, allowing three days; if not it exits to Wait, "
   "because the numbers are still moving. Step two fetches by query, paginated, against a row "
   "limit of twenty-five thousand per request. Step three asks whether the limit was hit, "
   "checking rather than assuming; if so it exits to Paginate again until a short page returns. "
   "Step four fetches by page as a separate request. Step five stores the raw response before any "
   "grouping. A note says a response exactly at the row limit is almost certainly truncated "
   "rather than complete."),
  ("h3", "The delay"),
  ("p", "Search performance data is not final when it first appears. Numbers for the last two or "
        "three days keep moving as data is processed, and a fetch that includes yesterday will "
        "produce a figure that is different if you run the same fetch again on Friday."),
  ("p", "That produces the specific and maddening failure where a weekly report contradicts "
        "itself: this week's number for last week is not the number you reported last week. So "
        "the fetch always asks for a week that ended at least three days ago, and the report says "
        "which week it covers."),
  ("h3", "Row limits"),
  ("p", "A request returns at most a fixed number of rows, and there is no flag in the response "
        "saying \"there was more\". A response containing exactly the limit is almost certainly "
        "truncated; one containing fewer is complete. Checking that and paginating is three lines "
        "and its absence silently discards the long tail, which for a site with any content is "
        "most of the queries."),
  ("h3", "Withheld queries"),
  ("p", "Rare queries are not returned at all, for privacy reasons that are entirely reasonable. "
        "The practical consequence is that summing the query rows gives a smaller total than the "
        "site-level total, sometimes much smaller."),
  ("p", "That is not an error to be reconciled away. The report states both numbers when they "
        "differ materially, because a business whose long tail is forty per cent of its "
        "impressions should know that its themed report covers sixty per cent of reality."),
  ("h2", "Store raw first"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Raw stored", "sub": ["every row, as returned"], "icon": "database"},
      {"title": "Rules change", "sub": ["a new theme added"], "icon": "doc"},
      {"title": "Regroup history", "sub": ["all of it"], "icon": "retry"},
      {"title": "Comparable", "sub": ["new theme, old data"], "icon": "chart"},
      {"title": "Without raw", "sub": ["the new theme starts at zero"], "icon": "alarm"}],
    "title": "WHY THE RAW RESPONSE IS KEPT",
    "note": "Theme rules change constantly. Keeping raw means history changes with them."}),
   "Why raw rows are stored before grouping. Theme rules get refined every few weeks, and each "
   "refinement is worthless if it cannot be applied backwards.",
   "Why raw search rows are stored before grouping",
   "A horizontal row of five boxes. Raw stored: every row, as returned. Rules change: a new theme "
   "is added. Regroup history: all of it. Comparable: the new theme has old data behind it. "
   "Without raw: the new theme starts at zero. A note says theme rules change constantly, and "
   "keeping raw means history changes with them."),
  ("p", "This is the single most valuable structural decision in the system and it costs a few "
        "megabytes a year. Theme rules get refined constantly &mdash; a new service line, a "
        "realisation that two themes should be one &mdash; and a system that only stores grouped "
        "totals has to start each new theme from the day it was created."),
  ("p", "With raw rows kept, adding a theme in August produces eight months of history for it "
        "immediately, which is the difference between a rule change being cheap and being a "
        "decision."),
  ("p", "Next: how the grouping works."),
 ],
},
{
 "slug": "how-queries-get-grouped",
 "title": "How queries get grouped",
 "nav": "How grouping works",
 "read": 5, "words": 760,
 "desc": ("Rules you write rather than clusters a machine finds, the order they apply in, and "
          "why the unmatched bucket is the most useful one."),
 "og": ("Automatic clustering produces different groups every run, which makes trends "
        "impossible. Rules you wrote produce the same groups forever."),
 "abstract": ("Why grouping rules are written rather than discovered, the order they apply in, "
              "the brand and competitor themes that need special handling, and why the unmatched "
              "bucket is the most useful output."),
 "lede": ("Grouping is where this system earns its keep and where the temptation to be clever is "
          "strongest. Automatic clustering is available, it works reasonably well, and it is the "
          "wrong choice for a reason that has nothing to do with quality."),
 "tags": ["SEO", "query grouping", "taxonomy", "reporting", "marketing", "serverless"],
 "takeaways": [
  "Rules you write, applied in order, first match wins.",
  "Automatic clustering produces different groups each run, which destroys trends.",
  "Brand queries are always their own theme and never mixed with anything.",
  "Competitor-name queries are worth their own theme and are frequently forgotten.",
  "The unmatched bucket is where next quarter's themes come from.",
 ],
 "blocks": [
  ("h2", "Rules, not clusters"),
  ("p", "A model can look at nine hundred queries and produce sensible groups. Run it again next "
        "week on a slightly different nine hundred and it will produce sensible groups that are "
        "not quite the same, and now this week's \"emergency work\" theme contains a different "
        "set of queries from last week's."),
  ("p", "Every trend built on that is meaningless, and the failure is invisible: the numbers look "
        "plausible and simply are not comparable. Rules written by a person produce the same "
        "groups forever, which is worth far more than the marginal improvement in grouping "
        "quality."),
  ("fig", ("chain", {
    "entry": {"title": "A query row", "sub": ["from the raw store"], "icon": "search"},
    "steps": [
      {"title": "Brand terms?", "sub": ["your name, misspellings"], "icon": "branch",
       "exit": {"title": "Brand", "sub": ["always first, always alone"], "icon": "tag",
                "label": "yes"}},
      {"title": "Competitor name?", "sub": ["a list you keep"], "icon": "branch",
       "exit": {"title": "Competitor", "sub": ["its own theme"], "icon": "team", "label": "yes"}},
      {"title": "Any theme rule?", "sub": ["in order, first match"], "icon": "filter",
       "side": {"title": "Theme rules", "sub": ["yours, ordered"], "icon": "doc"},
       "exit": {"title": "That theme", "sub": ["and stop"], "icon": "check", "label": "match"}},
      {"title": "Unmatched", "sub": ["a real bucket, not a bin"], "icon": "counter"},
      {"title": "Totals per theme", "sub": ["impressions, clicks,", "weighted position"],
       "icon": "chart"}],
    "note": "Brand first, always. Brand queries would otherwise contaminate every other theme."}),
   "How one query row finds its theme. Brand and competitor checks run before any content rule, "
   "because a brand query containing a service word would otherwise inflate that service.",
   "How a search query is assigned to a theme",
   "A vertical chain of five steps entered by a box labelled A query row, from the raw store. "
   "Step one asks whether it contains brand terms including your name and its misspellings; if so "
   "it exits to Brand, always first and always alone. Step two asks whether it contains a "
   "competitor name from a list you keep; if so it exits to Competitor, which is its own theme. "
   "Step three applies the theme rules in order with first match winning; a match exits to that "
   "theme and stops. Step four is Unmatched, which is a real bucket rather than a bin. Step five "
   "computes totals per theme: impressions, clicks and weighted position. A note says brand goes "
   "first always, because brand queries would otherwise contaminate every other theme."),
  ("h3", "Why brand goes first"),
  ("p", "A query like \"acme plumbing emergency\" contains a service word and is a brand query: "
        "somebody already knows who you are. Counting it in the emergency theme inflates that "
        "theme with traffic that was never competitive, and worse, makes the theme look healthy "
        "while the non-brand part of it declines."),
  ("p", "Separating brand out is the single most important grouping decision, and the difference "
        "it makes to a report is large: it is common for a business's apparently strong "
        "performance in a service theme to be almost entirely people searching for it by name."),
  ("h3", "Competitor queries"),
  ("p", "Queries containing a competitor's name that landed on your site are a small, interesting "
        "theme that almost nobody tracks. They are usually comparison searches, they convert "
        "unusually well, and a change in them is a genuine market signal rather than a ranking "
        "one."),
  ("h2", "Weighted position"),
  ("p", "The arithmetic detail that matters most: a theme's position is the impression-weighted "
        "average of its queries, not the simple average. A theme containing one query at position "
        "2 with four thousand impressions and forty queries at position 40 with two impressions "
        "each has a real position near 2, and a simple average would report 39."),
  ("h2", "The unmatched bucket"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Unmatched", "sub": ["18% of impressions"], "icon": "counter"},
      {"title": "Read the top 20", "sub": ["once a quarter"], "icon": "search"},
      {"title": "A pattern", "sub": ["'heat pump' x40"], "icon": "chart"},
      {"title": "New theme", "sub": ["added to the rules"], "icon": "doc"},
      {"title": "Regrouped", "sub": ["with all history"], "icon": "retry"}],
    "title": "WHERE NEW THEMES COME FROM",
    "note": "A growing unmatched bucket is the most useful signal in the whole system."}),
   "What the unmatched bucket is for. It is not a failure of the rules; it is the queue of things "
   "the business is starting to be found for.",
   "How the unmatched query bucket produces new themes",
   "A horizontal row of five boxes. Unmatched: eighteen per cent of impressions. Read the top "
   "twenty: once a quarter. A pattern: the phrase heat pump appearing forty times. New theme: "
   "added to the rules. Regrouped: with all history. A note says a growing unmatched bucket is "
   "the most useful signal in the whole system."),
  ("p", "An unmatched bucket that is growing means the site is being found for things the rules "
        "do not know about, and that is frequently the earliest signal a business gets that "
        "demand is shifting. Reading its top twenty queries once a quarter takes five minutes and "
        "is the highest-value five minutes in this entire system."),
  ("p", "Next: how a movement is told apart from noise."),
 ],
},
{
 "slug": "how-a-ranking-change-is-judged",
 "title": "How a ranking change is judged",
 "nav": "How change is judged",
 "read": 5, "words": 740,
 "desc": ("Why impressions gate everything, the seasonality that fools every week-on-week "
          "comparison, and the difference between a ranking change and a demand change."),
 "og": ("A position change on eleven impressions is nothing. And a theme can fall in clicks "
        "while ranking identically, because demand moved rather than you did."),
 "abstract": ("Why impressions gate every comparison, the seasonality that fools week-on-week "
              "reporting, and the crucial difference between a ranking change and a demand "
              "change."),
 "lede": ("There are two ways to be wrong about a search report and most reports manage both. "
          "One is treating a movement on tiny volume as meaningful. The other is treating a fall "
          "in clicks as a ranking problem when the ranking did not move at all and fewer people "
          "were searching."),
 "tags": ["SEO", "seasonality", "statistics", "reporting", "search demand", "serverless"],
 "takeaways": [
  "Impressions gate everything. Below a floor, nothing is reported however dramatic.",
  "Compare against the same weeks last year, not just last week, wherever there is a year of data.",
  "Position moving and clicks moving are different findings and are reported separately.",
  "A theme can lose clicks while ranking identically. That is demand, not ranking.",
  "A theme can gain impressions while losing position, which is usually a good thing.",
 ],
 "blocks": [
  ("h2", "Volume gates everything"),
  ("fig", ("chain", {
    "entry": {"title": "A theme, this week", "sub": ["against the baseline"], "icon": "chart"},
    "steps": [
      {"title": "Enough impressions?", "sub": ["a floor you set"], "icon": "branch",
       "exit": {"title": "Not reported", "sub": ["however dramatic"], "icon": "stop",
                "label": "no"}},
      {"title": "Position moved?", "sub": ["weighted, vs 8 weeks"], "icon": "branch",
       "exit": {"title": "A ranking finding", "sub": ["name the pages"], "icon": "search",
                "label": "yes"}},
      {"title": "Impressions moved?", "sub": ["position steady"], "icon": "branch",
       "exit": {"title": "A demand finding", "sub": ["not your doing"], "icon": "counter",
                "label": "yes"}},
      {"title": "Clicks moved only?", "sub": ["position and impressions steady"],
       "icon": "branch",
       "exit": {"title": "A snippet finding", "sub": ["title or description"], "icon": "doc",
                "label": "yes"}},
      {"title": "Nothing to report", "sub": ["most themes, most weeks"], "icon": "check"}],
    "note": "Three different findings with three different responses. Most reports conflate them."}),
   "How a theme's movement is classified. The three branches lead to completely different "
   "actions, and a report that reduces them to one number cannot tell you which you are looking "
   "at.",
   "How a change in a search theme is classified",
   "A vertical chain of five steps entered by a box labelled A theme, this week, against the "
   "baseline. Step one asks whether there are enough impressions against a floor you set; if not "
   "it exits to Not reported, however dramatic the change looks. Step two asks whether the "
   "weighted position moved against the last eight weeks; if so it exits to A ranking finding, "
   "naming the pages. Step three asks whether impressions moved while position stayed steady; if "
   "so it exits to A demand finding, which is not your doing. Step four asks whether only clicks "
   "moved while position and impressions stayed steady; if so it exits to A snippet finding, "
   "concerning the title or description. Step five is Nothing to report, which is most themes in "
   "most weeks. A note says these are three different findings with three different responses, "
   "and most reports conflate them."),
  ("h3", "The three findings"),
  ("table", ["What moved", "What it means", "What to do"], [
   ["Position", "Your ranking changed", "Look at the page and what else ranks now"],
   ["Impressions, position steady", "Demand changed", "Nothing, or plan for a season"],
   ["Clicks only", "Your snippet is less appealing", "Rewrite the title or description"],
  ]),
  ("p", "The third one is the most actionable and the least reported. A theme whose position and "
        "impressions are unchanged but whose clicks have fallen twenty per cent is telling you "
        "that the same people are seeing you in the same place and choosing something else. That "
        "is a title tag, and it is a twenty-minute fix with a measurable result."),
  ("h2", "Seasonality"),
  ("p", "Week-on-week comparison is fooled by seasonality with complete reliability. A plumbing "
        "firm's emergency callout theme triples in a cold snap and halves in July, and neither "
        "has anything to do with the site."),
  ("fig", ("strip", {
    "stages": [
      {"title": "vs last week", "sub": ["down 40%"], "icon": "alarm"},
      {"title": "vs 8 weeks", "sub": ["down 35%"], "icon": "chart"},
      {"title": "vs same week last year", "sub": ["up 4%"], "icon": "calendar"},
      {"title": "Position", "sub": ["unchanged"], "icon": "check"},
      {"title": "Verdict", "sub": ["it is July"], "icon": "search"}],
    "title": "THREE COMPARISONS, THREE ANSWERS",
    "note": "Only the third one is any use for a seasonal business, and most reports omit it."}),
   "Why a single comparison window misleads. The same data supports three different conclusions "
   "depending on what it is compared against.",
   "How three different comparison windows produce three different answers",
   "A horizontal row of five boxes. Against last week: down forty per cent. Against eight weeks: "
   "down thirty-five per cent. Against the same week last year: up four per cent. Position: "
   "unchanged. Verdict: it is July. A note says only the third comparison is any use for a "
   "seasonal business and most reports omit it."),
  ("p", "So where a year of history exists, the year-on-year comparison is the headline and the "
        "week-on-week is context. Where it does not, the report says so &mdash; \"no comparable "
        "period last year\" &mdash; rather than presenting a week-on-week figure as though it "
        "meant the same thing."),
  ("h3", "Position falling while impressions rise"),
  ("p", "The comparison that looks alarming and usually is not. A theme that starts ranking for a "
        "much wider set of queries will show more impressions and a worse average position, "
        "because the new queries are ones you rank badly for and did not appear for at all "
        "before."),
  ("p", "That is normally good: more impressions and more clicks with a worse average position "
        "means you are reaching more people. The report says so explicitly when it sees that "
        "pattern, because the naive reading is that something broke."),
  ("p", "Next: what the report says."),
 ],
},
{
 "slug": "how-the-ranking-report-reads",
 "title": "How the ranking report reads",
 "nav": "How it reads",
 "read": 5, "words": 720,
 "desc": ("Six themes every week whether or not they moved, the pages named, and what the report "
          "refuses to claim."),
 "og": ("The same six themes every week, in the same order, whether or not they moved. "
        "Comparability beats novelty in a weekly report."),
 "abstract": ("Why the same six themes appear every week in the same order, how pages are named, "
              "and the causal claims the report refuses to make."),
 "lede": ("A weekly report that shows different things each week cannot be skimmed, and a report "
          "that cannot be skimmed does not get read for long. This one shows the same six lines "
          "in the same order, forever, and that consistency is most of why it survives."),
 "tags": ["SEO", "reporting", "marketing", "attribution", "search", "serverless"],
 "takeaways": [
  "The same six themes, in the same order, every week.",
  "Each line: position, clicks, impressions, and the direction against last year.",
  "The page carrying each theme is named, with what share of it lands there.",
  "Correlations are stated as correlations. The report never claims a cause.",
  "One monthly addition: the top twenty unmatched queries.",
 ],
 "blocks": [
  ("h2", "The weekly page"),
  ("callout", "Week ending 26 July", [
   "<strong>Emergency callouts</strong> &mdash; pos 7.8 (was 4.1), 340 clicks (&minus;60%), "
   "4,100 impressions. <em>92% lands on /emergency-plumber.</em>",
   "<strong>Boiler installation</strong> &mdash; pos 6.2 (steady), 210 clicks (&minus;4%), 2,900 "
   "impressions. Year on year: +8%.",
   "<strong>Bathroom fitting</strong> &mdash; pos 11.4 (was 12.1), 88 clicks (+12%), 1,600 "
   "impressions.",
   "<strong>Commercial</strong> &mdash; pos 9.0 (steady), 41 clicks, 640 impressions. Below the "
   "volume floor for movement.",
   "<strong>Brand</strong> &mdash; pos 1.1, 520 clicks, 700 impressions. Steady.",
   "<strong>Unmatched</strong> &mdash; 18% of impressions. Top queries listed monthly.",
  ]),
  ("p", "Six lines, the same six, in the same order. The first one is the finding this week and "
        "it is obvious at a glance precisely because the other five look like they always do. A "
        "report that only showed movement would have shown one line, and a reader would have no "
        "idea whether the other five were fine or missing."),
  ("h3", "Naming the page"),
  ("p", "The page carrying a theme is what somebody can actually change, and the share matters as "
        "much as the name. \"92% lands on /emergency-plumber\" says the theme has one page and "
        "the finding is about that page. A theme spread across nine pages at eleven per cent each "
        "is a different situation entirely and the report says that too."),
  ("fig", ("chain", {
    "entry": {"title": "A theme with movement", "sub": ["confirmed"], "icon": "chart"},
    "steps": [
      {"title": "Which pages carry it?", "sub": ["from the by-page fetch"], "icon": "browser",
       "side": {"title": "Page data", "sub": ["clicks per page"], "icon": "database"}},
      {"title": "Concentrated?", "sub": ["one page over 70%"], "icon": "branch",
       "exit": {"title": "Name that page", "sub": ["the finding is about it"], "icon": "search",
                "label": "yes"}},
      {"title": "Spread?", "sub": ["no page over 30%"], "icon": "branch",
       "exit": {"title": "Say it is spread", "sub": ["a site-wide movement"], "icon": "filter",
                "label": "yes"}},
      {"title": "Did a page change?", "sub": ["from the deploy or CMS feed"], "icon": "code"},
      {"title": "State the correlation", "sub": ["never the cause"], "icon": "report"}],
    "note": "A concentrated theme and a spread one need completely different responses."}),
   "How a theme's movement is attributed to pages. Concentration is the first question, because "
   "it determines whether this is a page problem or a site problem.",
   "How a search theme's movement is attributed to pages",
   "A vertical chain of five steps entered by a box labelled A theme with movement, confirmed. "
   "Step one asks which pages carry it, using the by-page fetch and clicks per page. Step two "
   "asks whether it is concentrated, meaning one page carries over seventy per cent; if so it "
   "exits to Name that page, since the finding is about it. Step three asks whether it is spread, "
   "with no page over thirty per cent; if so it exits to Say it is spread, indicating a site-wide "
   "movement. Step four asks whether a page changed, using the deploy or CMS feed. Step five "
   "states the correlation and never the cause. A note says a concentrated theme and a spread one "
   "need completely different responses."),
  ("h2", "What it refuses to claim"),
  ("callout", "Correlation, stated as correlation", [
   "<strong>It says:</strong> \"/emergency-plumber was edited on the 21st. The position change "
   "first appears in the week beginning the 20th.\"",
   "<strong>It does not say:</strong> \"the edit on the 21st caused the drop.\"",
   "<strong>Why:</strong> search rankings move for reasons entirely invisible from your side "
   "&mdash; a competitor's change, an algorithm update, a new result format. Claiming causation "
   "from a timestamp is how businesses spend a fortnight reverting an edit that was fine.",
   "<strong>What it will say:</strong> \"nothing changed on this page in the last 60 days\", "
   "which is genuinely informative and rules something out.",
  ]),
  ("p", "That restraint is not pedantry. A confident wrong cause is worse than no cause at all, "
        "because somebody acts on it. Presenting a timing correlation as a timing correlation lets "
        "a person weigh it against everything else they know, which is what they are for."),
  ("h2", "The monthly addition"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Weekly", "sub": ["six themes"], "icon": "report"},
      {"title": "Monthly", "sub": ["plus unmatched top 20"], "icon": "search"},
      {"title": "Quarterly", "sub": ["plus year-on-year"], "icon": "calendar"},
      {"title": "Never", "sub": ["a query-level export"], "icon": "stop"},
      {"title": "Available", "sub": ["as a link, always"], "icon": "link"}],
    "title": "THREE CADENCES, AND ONE THING THAT NEVER APPEARS",
    "note": "The raw data is one link away and is never the message."}),
   "The three reporting cadences. The raw query-level data remains available and deliberately "
   "never arrives in an inbox.",
   "The three search reporting cadences and what each adds",
   "A horizontal row of five boxes. Weekly: six themes. Monthly: plus the top twenty unmatched "
   "queries. Quarterly: plus year-on-year comparison. Never: a query-level export. Available: as "
   "a link, always. A note says the raw data is one link away and is never the message."),
  ("p", "The unmatched top twenty is a monthly rather than weekly item because it changes slowly "
        "and reading it takes five minutes of genuine attention rather than nine seconds of "
        "skimming. Putting it in the weekly report would mean it was skimmed, which would waste "
        "the most valuable thing in the system."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="weekly fetch",
 volumes=[(4, "4 fetches"), (12, "3 sites weekly"), (52, "13 sites weekly")],
 read_each=0.0,
 msgs_each=1.2,
 lede=("This reads an API once a week and does arithmetic on a few thousand rows, which makes it "
       "the cheapest system in the series alongside the domain watcher. Four fetches is one site "
       "reported weekly. Here is where each cent goes."),
 takeaway_extra=("No model, and the API is free. The bill is the fixed band plus a few emails."),
 risks=[
  "<strong>Fetching daily instead of weekly.</strong> The data lags by days and is noisy at daily "
  "granularity, so daily fetching multiplies the storage and produces a worse signal.",
  "<strong>Storing grouped totals only.</strong> Not a cost risk but the expensive mistake: a "
  "theme rule change then cannot be applied to history, and every rule refinement starts a new "
  "series from zero.",
  "<strong>Log retention left at never.</strong> A weekly job that produces almost nothing will "
  "still be entirely a CloudWatch bill within a year.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model, deliberately. The API is free "
                "within generous quotas and the whole variable cost is a handful of emails."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="sr",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the fetch discipline, and why grouping is rules rather than a model."),
 outside=[
  {"title": "Search API", "sub": ["your own property"], "icon": "search"},
  {"title": "Theme rules", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["the weekly report"], "icon": "email"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["raw rows,", "weekly schedule"], "icon": "bucket"},
  {"title": "Lambda x3", "sub": ["fetch, group, report"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["themes, history"], "icon": "database"}],
 note="us-east-1. One account. Read-only against the search property; nothing is scraped.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The Search API for your own verified "
  "property. The Theme rules, read through the Google Sheets API read-only. And SES outbound, "
  "carrying the weekly report. Inside the account, three groups. S3 holding the raw rows and "
  "EventBridge providing a weekly schedule. Three Lambda functions named fetch, group and "
  "report. And two DynamoDB tables named themes and history. A note gives the region as "
  "us-east-1, one account, read-only against the search property, and states that nothing is "
  "scraped."),
 functions=[
  ["<code>sr-fetch</code>", "EventBridge weekly",
   "Paginated fetch by query and by page; writes raw rows to S3", "120s / 1024&nbsp;MB"],
  ["<code>sr-group</code>", "S3 ObjectCreated",
   "Applies the ordered rules; writes themed totals", "60s / 1024&nbsp;MB"],
  ["<code>sr-report</code>", "EventBridge weekly + monthly",
   "Comparisons, page attribution, the report page", "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>sr-fetch-role</code>",
   "<code>s3:PutObject</code>, <code>secretsmanager:GetSecretValue</code>",
   "The raw prefix; the search API credential only"],
  ["<code>sr-group-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:PutItem</code>, "
   "<code>secretsmanager:GetSecretValue</code>",
   "The raw prefix; the history table; the Sheets credential"],
  ["<code>sr-report-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "History, read; one verified identity"]],
 tables=[
  ("Table: history",
   "PK   theme             S   emergency-callouts\n"
   "SK   week_ending       S   2026-07-26\n"
   "     impressions       N   4100\n"
   "     clicks            N   340\n"
   "     position          N   7.8    -- impression-weighted, never a simple mean\n"
   "     pages             L   [{page, clicks, share}]\n"
   "     rules_version     S   v7     -- which rule set produced this row\n\n"
   "`rules_version` is what makes a regroup honest: a row grouped under v7 and\n"
   "one grouped under v4 are not directly comparable, and the report says so\n"
   "if a comparison would cross a version boundary."),
  ("Table: themes",
   "PK   theme             S   emergency-callouts\n"
   "     label             S   Emergency callouts\n"
   "     order             N   1      -- the report order, fixed\n"
   "     patterns          L   ordered match rules\n"
   "     volume_floor      N   500    -- impressions below which nothing is reported\n"
   "     kind              S   service | brand | competitor | unmatched\n\n"
   "Brand and competitor themes are matched BEFORE any service theme, which is\n"
   "enforced by `kind` rather than by rule ordering, so a rule edit cannot\n"
   "accidentally let a brand query into a service theme.")],
 inbound=[
  "<strong>Read-only against the search property.</strong> The credential has no write scope and "
  "there is nothing in the API to write anyway.",
  "<strong>Nothing is scraped.</strong> No simulated searches, no proxy fleet, no positions from "
  "a datacentre &mdash; all of which produce a worse number and most of which breach somebody's "
  "terms.",
  "<strong>Raw rows land in S3</strong> before anything is grouped, and the S3 event is what "
  "fires grouping. That means a regroup of history is the same code path as a fresh fetch.",
  "<strong>The fetch always asks for a completed week</strong> ending at least three days ago, "
  "because recent data is still moving."],
 model_notes=[
  "<strong>There is no model in this system, and that is the design.</strong> Automatic query "
  "clustering is the obvious use and it is the wrong one.",
  "<strong>Clusters shift between runs.</strong> Same site, slightly different queries, slightly "
  "different groups &mdash; and every trend built on them is quietly meaningless.",
  "<strong>Rules are stable by construction.</strong> The same rule set produces the same groups "
  "forever, which is what makes an eight-week comparison mean anything.",
  "<strong>If you want help writing rules</strong>, use a model interactively, once, on the "
  "unmatched bucket. Then write the rules down and let the code apply them.",
  "<strong>The cost page assumes none</strong>, which is why there is no read band."],
 gotchas=[
  "Store raw rows, not grouped totals. Every theme rule refinement is worthless if it cannot be "
  "applied to history.",
  "Weight position by impressions. A simple mean across queries reports a theme that ranks second "
  "as ranking thirty-ninth.",
  "Match brand before anything else. Brand queries containing a service word will otherwise "
  "inflate that service and mask a real decline.",
  "Check for row-limit truncation. A response exactly at the limit is almost certainly cut off, "
  "and the long tail is where the interesting queries are.",
  "Never claim a cause. State that a page changed on a date and let a person weigh it; a "
  "confident wrong cause costs a fortnight of reverting something that was fine."],
))
