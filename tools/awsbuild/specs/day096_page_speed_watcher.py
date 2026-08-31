"""Day 96 -- 2026-07-29 -- Page speed watcher."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "page-speed-watcher"
NAME = "Page speed watcher"

SPEC = {
 "slug": SLUG, "date": "2026-07-29", "name": NAME,
 "tagline": ("Measures the handful of pages that matter, on the same device profile every time, "
             "and tells you when a deploy made one slower -- with the resource that caused it "
             "named."),
 "lede": ("A small system that measures a short list of important pages on a fixed device and "
          "network profile, several times a run, and reports a regression only when it is "
          "larger than the noise. It names the resource that changed, and it never blocks a "
          "deploy. Seven posts on the same system -- one diagram at a time -- with a cost "
          "breakdown and an engineering reference at the end."),
 "keywords": ["page speed", "web performance", "Core Web Vitals", "monitoring", "regressions",
              "serverless"],
 "icons": ["clock", "chart", "alarm"],
 "faq": [
  ("What is a page speed watcher?",
   "A small serverless system that measures a fixed list of pages on a fixed device profile "
   "several times a run, compares against a rolling baseline, and reports a regression when the "
   "change is bigger than the measurement noise. It names what got heavier and does not block "
   "anything."),
  ("Why not just use a hosted speed tool?",
   "Plenty are good and this is a build-or-buy decision. What a small custom one gives you is "
   "your own page list, a baseline drawn from your own site rather than a global percentile, "
   "and enough runs per measurement to distinguish a regression from noise -- which is the "
   "thing most tools get wrong."),
  ("Does it fail a build?",
   "No. A page speed number is noisy enough that gating deploys on it produces false failures, "
   "and a check that fails wrongly gets bypassed within a month. It reports after the fact, "
   "with the deploy it correlates to."),
  ("What device profile does it use?",
   "One you choose and never change: a mid-range mobile on a throttled connection is the usual "
   "answer. The absolute number matters far less than measuring the same thing every time."),
  ("What does it cost to run?",
   "A few dollars a month for a handful of pages measured daily. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "page-speed-watcher-on-aws",
 "title": "A page speed watcher on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Measures a short list of pages on a fixed profile, several times a run, and reports "
          "a regression with the resource that caused it. AWS, about $4 a month."),
 "og": ("Page speed numbers are noisy. Measuring the same pages the same way many times is what "
        "turns them into something you can act on."),
 "abstract": ("The whole system on one page -- a measurer, a comparer and a reporter -- and the "
              "reason it takes several samples: one measurement of a web page tells you almost "
              "nothing."),
 "lede": ("Almost every page speed setup fails the same way. Somebody runs a tool, gets a score, "
          "shares it, and three weeks later runs it again and gets a different score. Nobody "
          "knows whether the site got slower or the measurement did, so nothing happens, and "
          "eventually the checking stops. This post walks through a small system built around "
          "the one property that fixes it: measuring the same thing, the same way, enough times "
          "to know what noise looks like."),
 "tags": ["page speed", "web performance", "Core Web Vitals", "monitoring", "regressions",
          "serverless"],
 "takeaways": [
  "A short list of pages, chosen deliberately. Not every page, and not the home page only.",
  "One device and network profile, fixed forever. Changing it invalidates the whole history.",
  "Several samples per run, because a single page load is not a measurement.",
  "A regression is reported only when it exceeds the noise the site's own history shows.",
  "Designed on AWS for about $4 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Your pages", "sub": ["a list of six or eight"], "icon": "browser"},
      {"title": "Deploy events", "sub": ["what shipped, when"], "icon": "code"},
      {"title": "Whoever owns the site", "sub": ["hears about regressions"], "icon": "person"}],
    "inside": [
      {"title": "Measurer", "sub": ["fixed profile,", "several samples"], "icon": "clock"},
      {"title": "Comparer", "sub": ["against the site's", "own noise"], "icon": "counter"},
      {"title": "Reporter", "sub": ["what got heavier,", "and after what"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "loads and timings"},
              {"from": 1, "to": 1, "label": "correlate to a deploy"},
              {"from": 2, "to": 2, "label": "a regression, explained", "up": True}],
    "note": "It never blocks a deploy. A noisy metric that gates releases gets bypassed."}),
   "Three things outside the account, three pieces inside it. The deploy feed is what turns "
   "\"this page got slower\" into \"this page got slower after Tuesday's release\", which is the "
   "difference between a fact and a lead.",
   "System: pages measured on a fixed profile, regressions reported",
   "Three boxes across the top sit outside the AWS account. On the left, Your pages: a "
   "deliberately short list of six or eight. In the middle, Deploy events: what shipped and "
   "when. On the right, Whoever owns the site: the person who hears about regressions. Each "
   "connects by an arrow to the AWS account container below. Loads and timings flow down into "
   "the account. Deploy events feed in so a change can be correlated. A regression, explained, "
   "goes back out. Inside the AWS account are three components in a row. On the left, the "
   "Measurer, using a fixed profile and taking several samples. In the middle, the Comparer, "
   "judging against the site's own noise. On the right, the Reporter, saying what got heavier "
   "and after what. A note at the bottom says it never blocks a deploy, because a noisy metric "
   "that gates releases gets bypassed."),
  ("h3", "A single page load is not a measurement"),
  ("p", "Load the same page ten times on the same connection and the numbers will differ by "
        "twenty per cent or more. Server warm-up, network variance, CDN cache state, a "
        "third-party script that is slow this minute. None of that is your site changing, and "
        "all of it looks exactly like your site changing if you measure once."),
  ("p", "So every run takes several samples of every page and keeps the median. That single "
        "decision is what makes everything downstream possible: with a median of nine samples "
        "you can say what normal variation looks like, and once you know that, you can say when "
        "something is outside it."),
  ("h3", "What runs daily (the inside)"),
  ("ul", [
   "<strong>The measurer.</strong> Loads each page on the list several times in a headless "
   "browser on a fixed CPU and network profile, and records the metrics plus the full resource "
   "list. Part 2 covers the profile and why it must never change.",
   "<strong>The comparer.</strong> Takes the median for each page and compares it against a "
   "rolling baseline of the last few weeks, using the spread of that baseline to decide what "
   "counts as a change. Part 3 is entirely about this.",
   "<strong>The reporter.</strong> When something regresses, works out what got heavier by "
   "diffing the resource lists, and correlates the timing against the deploy feed. The output is "
   "\"the hero image is now 1.4MB rather than 180KB\", not \"LCP increased\".",
  ]),
  ("h2", "One regression, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Measured", "sub": ["9 samples, fixed profile"], "icon": "clock"},
      {"title": "Median", "sub": ["one number per page"], "icon": "counter"},
      {"title": "Compared", "sub": ["to the last 21 days"], "icon": "chart"},
      {"title": "Outside the noise", "sub": ["not just higher"], "icon": "alarm"},
      {"title": "Explained", "sub": ["what changed, after what"], "icon": "report"}],
    "title": "ONE REGRESSION, END TO END",
    "note": "Steps two and four are the whole design. Everything else is a headless browser."}),
   "The same system as one line. Taking a median and comparing against the site's own spread are "
   "the two steps that separate this from a tool that reports a different score every week.",
   "One page speed regression from measurement to explanation, in five stages",
   "A horizontal row of five boxes joined by arrows. Measured: nine samples on a fixed profile. "
   "Median: one number per page. Compared: against the last twenty-one days. Outside the noise: "
   "not merely higher. Explained: what changed, and after what. A note says steps two and four "
   "are the whole design and everything else is a headless browser."),
  ("h2", "In plain words"),
  ("p", "The pricing page has had a largest-contentful-paint median between 1.8 and 2.2 seconds "
        "for three weeks, measured nine times a day on a throttled mid-range mobile profile. On "
        "Wednesday the median is 3.9 seconds. That is well outside the range the page has shown "
        "across sixty-three previous runs, so it is a regression rather than a bad day."),
  ("p", "The reporter diffs Wednesday's resource list against Tuesday's. One image on the page is "
        "now 1.4 megabytes where it was 180 kilobytes. The deploy feed shows a release at 09:12 "
        "on Wednesday, and the first slow run was 09:40. The message says all of that in three "
        "lines: the page, the number, the resource, and the release."),
  ("p", "Somebody looks and finds that a new hero image was uploaded through the CMS without "
        "being resized. It is a five-minute fix, and the value of the system is entirely in "
        "somebody finding out on Wednesday rather than in three months when a customer mentions "
        "the site feels slow on their phone."),
  ("callout", "Design rules that shaped every decision", [
   "One profile, forever. The absolute number is far less important than comparability.",
   "Several samples, always. A single load is not a measurement and treating it as one produces "
   "a tool nobody trusts.",
   "Compare against the site's own spread, not a fixed threshold. Every page has a different "
   "amount of natural variation.",
   "Name the resource, not the metric. \"LCP up 1.7s\" is a fact; \"the hero image is now "
   "1.4MB\" is a fix.",
   "Never block a deploy. A noisy gate is a gate people learn to bypass.",
   "A short page list. Eight pages measured properly beats four hundred measured once.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Web performance monitoring has a credibility problem, and it is self-inflicted. Tools "
        "report a score, the score moves for reasons unrelated to the site, and everybody learns "
        "to discount it. By the time something genuinely regresses, the signal has no audience."),
  ("p", "So this design spends nearly all of its effort on making the number trustworthy: a fixed "
        "profile, many samples, and a comparison that understands its own noise. The measuring is "
        "a headless browser and a library, which is the least interesting part, and the reporting "
        "is short because a trustworthy number does not need much explanation."),
  ("p", "The next four posts walk through each piece: how a page gets measured, how a regression "
        "is distinguished from noise, how a budget is set, and what the report says. One diagram "
        "per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-page-gets-measured",
 "title": "How a page gets measured",
 "nav": "How it is measured",
 "read": 5, "words": 760,
 "desc": ("The profile that must never change, how many samples is enough, and the four things "
          "that quietly make two runs incomparable."),
 "og": ("The absolute number barely matters and comparability is everything. Four things quietly "
        "break comparability and three of them are easy to miss."),
 "abstract": ("The device profile that must never change, how many samples is enough, and the "
              "four things that quietly make two runs incomparable."),
 "lede": ("Everything in this post is in service of one property: that a measurement taken today "
          "means the same thing as one taken in March. That sounds obvious and is surprisingly "
          "easy to lose, usually by accident and usually invisibly."),
 "tags": ["page speed", "measurement", "Lighthouse", "headless browsers", "methodology",
          "serverless"],
 "takeaways": [
  "One profile: a fixed CPU throttle, a fixed network shape, a fixed viewport.",
  "Nine samples per page per run is a good default; the median is what is kept.",
  "Cold and warm cache are different measurements. Pick one and say which.",
  "Four things break comparability: the profile, the region, the browser version, and third parties.",
  "Record the browser version with every run so a step change can be explained.",
 ],
 "blocks": [
  ("h2", "The profile"),
  ("pre", "device      mobile, 412x915, dpr 2.6\n"
          "cpu         4x slowdown        a mid-range phone, roughly\n"
          "network     1.6 Mbps down, 750 Kbps up, 150ms RTT\n"
          "cache       cold               every sample, a fresh profile\n"
          "region      eu-west-2          fixed; latency is part of the number\n"
          "samples     9                  median kept, all nine stored"),
  ("p", "None of those values is special and arguing about them is not worth much. What matters "
        "is writing them down once and never changing them, because the moment the profile "
        "changes, every historical measurement stops being comparable and the baseline has to "
        "start again."),
  ("p", "If the profile genuinely has to change &mdash; a decision that the mid-range phone of "
        "2026 is faster than the one you configured in 2024 &mdash; the honest handling is to "
        "start a new series rather than continuing the old one. The charts should show a break, "
        "not a smooth line through a methodology change."),
  ("h2", "How many samples"),
  ("fig", ("chain", {
    "entry": {"title": "One page", "sub": ["on the list"], "icon": "browser"},
    "steps": [
      {"title": "Fresh browser profile", "sub": ["cold cache, every time"], "icon": "retry"},
      {"title": "Load and measure", "sub": ["one sample"], "icon": "clock"},
      {"title": "Nine times?", "sub": ["not three, not one"], "icon": "branch",
       "exit": {"title": "Repeat", "sub": ["until nine"], "icon": "counter", "label": "no"}},
      {"title": "Take the median", "sub": ["and keep all nine"], "icon": "filter"},
      {"title": "Store with the resources", "sub": ["every request the page made"], "icon": "log"}],
    "note": "Keeping all nine is what lets you say later whether a run itself was unusual."}),
   "How one page is measured. Storing every sample rather than just the median is what makes it "
   "possible to distinguish a slow site from a bad run afterwards.",
   "How a single page is measured across nine samples",
   "A vertical chain of five steps entered by a box labelled One page, on the list. Step one "
   "starts a fresh browser profile with a cold cache, every time. Step two loads and measures, "
   "producing one sample. Step three asks whether nine samples have been taken, not three and "
   "not one; if not it exits to Repeat until nine. Step four takes the median and keeps all "
   "nine. Step five stores the result together with every request the page made. A note says "
   "keeping all nine is what lets you say later whether a run itself was unusual."),
  ("h3", "Why nine"),
  ("p", "Three samples gives a median that still moves around a lot. Five is noticeably better. "
        "Nine is where the median becomes stable enough that day-to-day movement is mostly the "
        "site rather than the measurement, and beyond about eleven the improvement is small "
        "relative to the extra minutes."),
  ("p", "Keeping all nine rather than only the median matters more than it looks. When a run "
        "looks odd, the spread within that run answers whether the site was slow or one sample "
        "was pathological &mdash; and a run where the spread itself is unusually wide is "
        "frequently a more interesting signal than the median."),
  ("h2", "Four ways comparability breaks"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Profile changed", "sub": ["obvious, and rare"], "icon": "form"},
      {"title": "Region changed", "sub": ["latency moved"], "icon": "map"},
      {"title": "Browser updated", "sub": ["a step in the chart"], "icon": "browser"},
      {"title": "A third party", "sub": ["their change, your number"], "icon": "external"},
      {"title": "Record all four", "sub": ["with every run"], "icon": "log"}],
    "title": "FOUR THINGS THAT MOVE THE NUMBER WITHOUT YOUR SITE CHANGING",
    "note": "The third and fourth are the ones that produce unexplainable step changes."}),
   "The four ways a measurement stops being comparable. Recording each of them with every run is "
   "what turns an unexplainable step in a chart into an obvious one.",
   "Four things that change a page speed number without the site changing",
   "A horizontal row of five boxes. Profile changed: obvious, and rare. Region changed: latency "
   "moved. Browser updated: producing a step in the chart. A third party: their change becomes "
   "your number. Record all four: with every run. A note says the third and fourth are the ones "
   "that produce unexplainable step changes."),
  ("h3", "The browser version"),
  ("p", "A headless browser that auto-updates will, once every few weeks, change how it measures "
        "or how fast it renders. The result is a step in the chart on a day when nobody deployed "
        "anything, which is exactly the kind of unexplainable event that erodes trust in a "
        "monitoring system."),
  ("p", "So the browser version is recorded with every run and pinned in the build. When it is "
        "deliberately upgraded, that is a recorded event and the report says so: \"browser "
        "updated on the 14th; a step change on that date is expected.\""),
  ("h3", "Third-party scripts"),
  ("p", "A page with an analytics tag, a chat widget and a font from somewhere else is measuring "
        "three other companies as well as itself. When one of them has a slow week, your number "
        "moves and your deploy log explains nothing."),
  ("p", "The resource list is what saves you here: the diff will show that the regression is "
        "entirely in a third-party request, and the report says so rather than implying somebody "
        "shipped something. It is still worth knowing &mdash; a chat widget that adds a second to "
        "your pricing page is a business decision &mdash; but it is a different conversation from "
        "a regression you caused."),
  ("p", "Next: how a regression is told apart from a bad day."),
 ],
},
{
 "slug": "how-a-speed-regression-is-detected",
 "title": "How a speed regression is detected",
 "nav": "How it is detected",
 "read": 5, "words": 750,
 "desc": ("Comparing against the page's own spread rather than a fixed threshold, why the "
          "baseline rolls, and the slow drift that no single comparison catches."),
 "og": ("Every page has a different amount of natural variation. Comparing against the page's "
        "own history is what makes one threshold work for all of them."),
 "abstract": ("Comparing against a page's own rolling spread rather than a fixed threshold, why "
              "the baseline rolls, and the slow drift no single comparison will ever catch."),
 "lede": ("A fixed threshold &mdash; alert if LCP goes above two and a half seconds &mdash; is "
          "the obvious approach and it is wrong for a specific reason: your pages are not equally "
          "variable, and a threshold tuned to the steadiest one will fire constantly on the "
          "noisiest."),
 "tags": ["page speed", "regression detection", "statistics", "monitoring", "baselines",
          "serverless"],
 "takeaways": [
  "Compare against the page's own rolling baseline, not a global threshold.",
  "The trigger is a median outside the baseline's spread, sustained for two runs.",
  "The baseline rolls, so a deliberate improvement becomes the new normal automatically.",
  "A rolling baseline cannot see slow drift, so a separate quarterly comparison does.",
  "A page that has never been measured has no baseline and reports nothing for three weeks.",
 ],
 "blocks": [
  ("h2", "The page's own spread"),
  ("fig", ("chain", {
    "entry": {"title": "Today's median", "sub": ["one page"], "icon": "counter"},
    "steps": [
      {"title": "Enough history?", "sub": ["21 runs minimum"], "icon": "branch",
       "exit": {"title": "No baseline yet", "sub": ["measure, report nothing"], "icon": "clock",
                "label": "no"}},
      {"title": "Build the baseline", "sub": ["median and spread", "of the last 21"], "icon": "chart",
       "side": {"title": "History", "sub": ["per page, per metric"], "icon": "database"}},
      {"title": "Outside the spread?", "sub": ["by a set multiple"], "icon": "branch",
       "exit": {"title": "Normal day", "sub": ["the usual outcome"], "icon": "check",
                "label": "no"}},
      {"title": "Again tomorrow?", "sub": ["two runs, not one"], "icon": "branch",
       "exit": {"title": "Hold", "sub": ["one bad day happens"], "icon": "retry", "label": "no"}},
      {"title": "A regression", "sub": ["explain it"], "icon": "alarm"}],
    "note": "Two consecutive runs outside the spread. One is a bad afternoon."}),
   "How a regression is confirmed. Requiring two consecutive runs costs a day of latency and "
   "removes nearly every false alarm.",
   "How a page speed regression is distinguished from normal variation",
   "A vertical chain of five steps entered by a box labelled Today's median, for one page. Step "
   "one asks whether there is enough history, with a minimum of twenty-one runs; if not it exits "
   "to No baseline yet, which measures and reports nothing. Step two builds the baseline from the "
   "median and spread of the last twenty-one runs, held per page and per metric. Step three asks "
   "whether today is outside the spread by a set multiple; if not it exits to Normal day, the "
   "usual outcome. Step four asks whether it is outside again tomorrow, requiring two runs rather "
   "than one; if not it exits to Hold, because one bad day happens. Step five is A regression, "
   "which gets explained. A note says two consecutive runs outside the spread, because one is a "
   "bad afternoon."),
  ("h3", "Why a multiple of the spread"),
  ("p", "A page whose median has sat between 1.8 and 2.2 seconds for three weeks has a spread of "
        "about 0.2 seconds, and 2.9 seconds is a long way outside it. A page that has ranged "
        "between 3.1 and 5.4 seconds &mdash; because it embeds a map, say &mdash; has a spread of "
        "over two seconds, and 5.6 is unremarkable."),
  ("p", "One fixed threshold cannot serve both. A multiple of each page's own spread serves both "
        "with a single setting, and it self-adjusts: a page that becomes more variable "
        "automatically becomes harder to alarm on, which is correct."),
  ("h3", "Why the baseline rolls"),
  ("p", "A rolling baseline of the last twenty-one runs means a deliberate improvement becomes "
        "the new normal within three weeks with nobody doing anything. Somebody optimises the "
        "pricing page from 2.0 to 1.3 seconds, and from then on the system is watching for "
        "regressions from 1.3."),
  ("p", "A fixed baseline would keep congratulating you on being under a target set a year ago, "
        "and would miss a regression from 1.3 back to 1.9 entirely, because 1.9 is still under "
        "the target."),
  ("h2", "The drift a rolling baseline cannot see"),
  ("fig", ("strip", {
    "stages": [
      {"title": "1.8s in January", "sub": ["baseline"], "icon": "clock"},
      {"title": "+40ms a month", "sub": ["never outside the spread"], "icon": "counter"},
      {"title": "No alarm, ever", "sub": ["correctly"], "icon": "check"},
      {"title": "2.3s by August", "sub": ["nobody noticed"], "icon": "alarm"},
      {"title": "Quarterly compare", "sub": ["this quarter vs last"], "icon": "chart"}],
    "title": "THE FAILURE MODE OF A ROLLING BASELINE",
    "note": "A rolling baseline follows drift by construction. That is a feature and a blind spot."}),
   "The one thing a rolling baseline structurally cannot detect, and the separate comparison that "
   "covers it.",
   "How slow drift escapes a rolling baseline",
   "A horizontal row of five boxes. One point eight seconds in January: the baseline. Plus forty "
   "milliseconds a month: never outside the spread. No alarm, ever: and correctly so. Two point "
   "three seconds by August: nobody noticed. Quarterly compare: this quarter against last. A "
   "note says a rolling baseline follows drift by construction, which is both a feature and a "
   "blind spot."),
  ("p", "Forty milliseconds a month is invisible to any comparison against the last three weeks, "
        "and it is exactly how sites get slow. It is not one bad deploy; it is eleven small ones, "
        "each of which was individually reasonable."),
  ("p", "So there is a second, much simpler comparison that runs once a quarter: this quarter's "
        "median against last quarter's, per page, with no cleverness at all. A page that is "
        "twenty per cent slower than three months ago appears there whether or not any single day "
        "ever triggered anything."),
  ("h3", "New pages"),
  ("p", "A page added to the list has no baseline and reports nothing for three weeks, which is "
        "worth saying explicitly in the report so its absence is not mistaken for good news. "
        "During those three weeks it is measured normally; it simply has nothing to be compared "
        "against yet."),
  ("p", "Next: budgets, which are the one place a fixed threshold does belong."),
 ],
},
{
 "slug": "how-a-performance-budget-is-set",
 "title": "How a performance budget is set",
 "nav": "How budgets work",
 "read": 5, "words": 730,
 "desc": ("Where a fixed threshold does belong, budgeting bytes rather than seconds, and why a "
          "budget is a conversation rather than a gate."),
 "og": ("Regressions are relative; budgets are absolute. Budget the thing you control -- bytes "
        "and requests -- rather than the thing you only influence."),
 "abstract": ("Where a fixed threshold genuinely belongs, why budgeting bytes beats budgeting "
              "seconds, and why a budget is a prompt for a conversation rather than a gate."),
 "lede": ("The last post argued against fixed thresholds and this one is about the place they "
          "belong. A regression is a relative question &mdash; is this worse than it was? A "
          "budget is an absolute one &mdash; is this acceptable at all? Both are worth asking and "
          "they are not the same question."),
 "tags": ["page speed", "performance budgets", "web performance", "planning", "monitoring",
          "serverless"],
 "takeaways": [
  "Budget bytes and requests, which you control, rather than seconds, which you influence.",
  "A budget is per page, because a pricing page and an interactive tool are not comparable.",
  "Breaching a budget is a monthly conversation, not an alarm and never a gate.",
  "Set the initial budget from where the page is now, plus a little.",
  "A page that has been over budget for six months has a wrong budget or a real problem.",
 ],
 "blocks": [
  ("h2", "Bytes, not seconds"),
  ("p", "Seconds depend on the device, the network, the CDN's mood and three other companies. "
        "Bytes and request counts depend on what you shipped. Budgeting the second kind gives you "
        "a number that is stable, attributable, and actionable by the person who caused it."),
  ("table", ["Budget", "Typical for a content page", "Why this one"], [
   ["Total transferred", "800&nbsp;KB", "The single best proxy for how a page feels on a phone"],
   ["JavaScript", "180&nbsp;KB", "The most expensive bytes; parsing costs more than downloading"],
   ["Images", "400&nbsp;KB", "The easiest to blow accidentally through a CMS"],
   ["Fonts", "100&nbsp;KB", "Two weights, subset. Four weights is a decision."],
   ["Requests", "45", "Catches the thing byte budgets miss: dozens of tiny files"],
   ["Third-party bytes", "150&nbsp;KB", "Separated, because it is somebody else's decision"],
  ]),
  ("p", "Separating third-party bytes is the row that produces the most useful conversations. A "
        "page that is over its total budget entirely because of a chat widget is not an "
        "engineering problem, and presenting it as one wastes everybody's time."),
  ("h2", "Setting the first one"),
  ("fig", ("chain", {
    "entry": {"title": "A page with no budget", "sub": ["and three weeks of data"], "icon": "browser"},
    "steps": [
      {"title": "Where is it now?", "sub": ["median bytes, 21 runs"], "icon": "counter"},
      {"title": "Is that acceptable?", "sub": ["a person decides"], "icon": "person",
       "exit": {"title": "Set below current", "sub": ["a stated intention"], "icon": "chart",
                "label": "no"}},
      {"title": "Set at current + 10%", "sub": ["room to work, not to drift"], "icon": "filter"},
      {"title": "Review quarterly", "sub": ["with the actuals"], "icon": "calendar"},
      {"title": "A budget", "sub": ["that means something"], "icon": "check"}],
    "note": "A budget set from an aspiration rather than a measurement is over on day one."}),
   "How a budget gets its first number. Starting from where the page actually is means the "
   "budget is meaningful immediately rather than being a permanently breached aspiration.",
   "How an initial performance budget is set for a page",
   "A vertical chain of five steps entered by a box labelled A page with no budget, and three "
   "weeks of data. Step one asks where it is now, using the median bytes over twenty-one runs. "
   "Step two asks whether that is acceptable, which a person decides; if not it exits to Set "
   "below current, which is a stated intention. Step three sets the budget at current plus ten "
   "per cent, giving room to work but not to drift. Step four reviews quarterly against the "
   "actuals. Step five is a budget that means something. A note says a budget set from an "
   "aspiration rather than a measurement is over on day one."),
  ("h3", "Current plus ten per cent"),
  ("p", "A budget set at an aspirational number is breached from the moment it is created, which "
        "makes it useless: everything is over budget, so being over budget carries no "
        "information. A budget set slightly above where the page actually is tells you the moment "
        "something meaningfully changes, which is what a budget is for."),
  ("p", "If the current state is genuinely unacceptable, setting the budget below it is a "
        "legitimate choice &mdash; but then it is a stated intention with a person attached, "
        "recorded as such, rather than a permanent red mark that everybody stops seeing."),
  ("h2", "What a breach does"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Over budget", "sub": ["one run"], "icon": "counter"},
      {"title": "Recorded", "sub": ["not alarmed"], "icon": "log"},
      {"title": "Still over", "sub": ["a week later"], "icon": "clock"},
      {"title": "In the monthly", "sub": ["with what pushed it over"], "icon": "report"},
      {"title": "A conversation", "sub": ["not a gate"], "icon": "team"}],
    "title": "A BUDGET BREACH IS A PROMPT",
    "note": "Gating a deploy on a byte budget produces a bypass flag within a month."}),
   "What happens when a budget is exceeded. Deliberately less than an alarm, because a byte "
   "budget is a planning tool rather than a correctness check.",
   "How a performance budget breach is handled",
   "A horizontal row of five boxes. Over budget: on one run. Recorded: rather than alarmed. Still "
   "over: a week later. In the monthly: with what pushed it over. A conversation: rather than a "
   "gate. A note says gating a deploy on a byte budget produces a bypass flag within a month."),
  ("p", "The temptation to gate is strong and the reasoning is sound &mdash; a budget you can "
        "exceed freely is not much of a budget. In practice, gating produces one of two outcomes: "
        "the budget is set loose enough to never fire, or it fires on a legitimate change at a "
        "bad moment and somebody adds a way to skip it. Neither is better than a monthly "
        "conversation with the numbers in front of it."),
  ("h3", "A permanently breached budget"),
  ("p", "A page that has been over budget every day for six months is telling you something, and "
        "it is one of two things: the budget was wrong, or there is a real problem nobody has "
        "prioritised. Both are worth resolving, and the resolution is either an edit or a piece "
        "of work &mdash; not another six months of a red row."),
  ("p", "The quarterly review exists mostly to force that: any budget breached in more than half "
        "the runs of a quarter is raised explicitly with the question of which of the two it is."),
  ("p", "Next: what the report says."),
 ],
},
{
 "slug": "how-the-speed-report-reads",
 "title": "How the speed report reads",
 "nav": "How it reads",
 "read": 5, "words": 720,
 "desc": ("Naming the resource rather than the metric, correlating to a deploy, and the two "
          "numbers worth putting in front of anybody."),
 "og": ("\"LCP up 1.7s\" is a fact. \"The hero image is now 1.4MB, after Wednesday's release\" is "
        "a fix somebody can make before lunch."),
 "abstract": ("Naming the resource rather than the metric, correlating a regression to a deploy, "
              "and the two numbers worth putting in front of anybody who is not an engineer."),
 "lede": ("The report has one job: turn a number that moved into a thing somebody can change. "
          "That means the resource diff matters far more than the metric, and the deploy "
          "correlation matters more than either."),
 "tags": ["page speed", "reporting", "web performance", "deployments", "monitoring", "serverless"],
 "takeaways": [
  "Lead with the resource that changed, not the metric that moved.",
  "Correlate to the deploy feed, and say plainly when nothing correlates.",
  "Separate third-party regressions, because they are somebody else's change.",
  "Two numbers for a non-engineer: the slowest important page, and whether it is moving.",
  "A monthly summary; alarms only for confirmed regressions.",
 ],
 "blocks": [
  ("h2", "What a regression message says"),
  ("callout", "Four lines", [
   "<strong>/pricing is 1.7s slower.</strong> LCP median 3.9s, was 2.0&ndash;2.2s across the "
   "last 21 runs.",
   "<strong>What changed:</strong> <code>hero-q3.jpg</code> is 1.4&nbsp;MB. The image it "
   "replaced was 180&nbsp;KB. Total page weight is up 1.2&nbsp;MB.",
   "<strong>When:</strong> first slow run 09:40 Wednesday. A release went out at 09:12.",
   "<strong>Also:</strong> the page is now over its total-bytes budget for the first time.",
   "<em>Nine samples per run; the full resource diff is attached.</em>",
  ]),
  ("p", "The second line is the one that gets acted on. Somebody reading \"LCP median 3.9s\" has "
        "to go and investigate; somebody reading \"hero-q3.jpg is 1.4MB\" already knows what to "
        "do and roughly how long it will take."),
  ("h2", "The resource diff"),
  ("fig", ("chain", {
    "entry": {"title": "A confirmed regression", "sub": ["one page"], "icon": "alarm"},
    "steps": [
      {"title": "Diff the resource lists", "sub": ["today vs baseline"], "icon": "filter",
       "side": {"title": "Stored per run", "sub": ["every request"], "icon": "database"}},
      {"title": "Anything much bigger?", "sub": ["by absolute bytes"], "icon": "branch",
       "exit": {"title": "Name it", "sub": ["usually one thing"], "icon": "search",
                "label": "yes"}},
      {"title": "Anything new?", "sub": ["a request that was not there"], "icon": "branch",
       "exit": {"title": "Name it", "sub": ["often a third party"], "icon": "external",
                "label": "yes"}},
      {"title": "Same bytes, slower?", "sub": ["a server or CDN change"], "icon": "clock"},
      {"title": "Say which", "sub": ["and correlate the deploy"], "icon": "report"}],
    "note": "The fourth branch is the awkward one: nothing got bigger and it still got slower."}),
   "How a regression gets its explanation. Three of the four outcomes name something concrete; "
   "the fourth is honest that the cause is not in the page.",
   "How a page speed regression is attributed to a cause",
   "A vertical chain of five steps entered by a box labelled A confirmed regression, on one page. "
   "Step one diffs the resource lists, today against the baseline, using every request stored per "
   "run. Step two asks whether anything is much bigger by absolute bytes; if so it exits to Name "
   "it, usually one thing. Step three asks whether anything is new, a request that was not there "
   "before; if so it exits to Name it, often a third party. Step four covers the case of the same "
   "bytes but slower, indicating a server or CDN change. Step five says which and correlates the "
   "deploy. A note says the fourth branch is the awkward one, where nothing got bigger and it "
   "still got slower."),
  ("h3", "When nothing got bigger"),
  ("p", "Same resources, same sizes, slower page. That is a server-side or network change: an "
        "origin that is responding more slowly, a CDN cache hit rate that dropped, a database "
        "query behind the page that got worse. The resource list cannot see any of it."),
  ("p", "The honest report says exactly that: \"page weight and request count are unchanged; the "
        "server's response time for the document is up 800ms.\" That is a different team's "
        "problem and pointing at it precisely is more useful than a vague slowdown."),
  ("h3", "When nothing correlates"),
  ("p", "A regression with no deploy near it is worth reporting as such. It is usually a content "
        "change through a CMS, which does not appear in a deploy feed, and \"no release "
        "correlates; the change is in an image, which suggests a content edit\" points somebody "
        "at the right system on the first try."),
  ("h2", "Two numbers for everybody else"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Slowest key page", "sub": ["/pricing, 2.1s"], "icon": "clock"},
      {"title": "Three months ago", "sub": ["1.9s"], "icon": "chart"},
      {"title": "Direction", "sub": ["slightly worse"], "icon": "counter"},
      {"title": "Regressions", "sub": ["1 this month, fixed"], "icon": "check"},
      {"title": "Over budget", "sub": ["0 pages"], "icon": "report"}],
    "title": "THE MONTHLY SUMMARY",
    "note": "Two of these are for engineers. The first three are for everybody else."}),
   "The monthly summary. The first three boxes are the version that means something to somebody "
   "who does not work on the site.",
   "The monthly page speed summary in five numbers",
   "A horizontal row of five boxes. Slowest key page: the pricing page at two point one seconds. "
   "Three months ago: one point nine seconds. Direction: slightly worse. Regressions: one this "
   "month, fixed. Over budget: no pages. A note says two of these are for engineers and the "
   "first three are for everybody else."),
  ("p", "The slowest important page and its direction over a quarter is the whole story for "
        "anybody who is not going to open a resource waterfall. It is two numbers, it is "
        "comparable across months because the profile never changes, and it answers the only "
        "question a non-engineer actually has, which is whether the site is getting better or "
        "worse."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="page load",
 volumes=[(1800, "8 pages daily"), (5400, "24 pages daily"), (16200, "72 pages daily")],
 read_each=0.0,
 msgs_each=0.01,
 extra=[("compute", "Lambda &mdash; headless browser time", "#ED7100", 0.00042, 0.0)],
 lede=("This is the most compute-heavy system in the series, because every measurement is a real "
       "browser loading a real page. Eight pages measured nine times a day is eighteen hundred "
       "page loads a month, each a few seconds of Lambda. Here is where each cent goes."),
 takeaway_extra=("Browser time is the whole bill. Nine samples is nine times the cost of one, "
                 "and it is what makes the numbers usable."),
 risks=[
  "<strong>Measuring too many pages.</strong> The cost is linear in pages times samples, and a "
  "list of eighty pages measured nine times daily is a genuinely noticeable bill for a report "
  "nobody can act on. Eight pages is not a limitation; it is the design.",
  "<strong>A browser that fails to close.</strong> A headless browser left running until the "
  "Lambda times out costs the full timeout every invocation. Always close in a finally block, "
  "and set the timeout to roughly twice the expected run.",
  "<strong>Storing full HAR files forever.</strong> A complete request trace per sample is "
  "megabytes. Store the resource summary always and the full trace only for runs that "
  "regressed.",
 ],
 per_unit_note=("The compute band is Lambda duration running a headless browser, at roughly two "
                "to four seconds per page load on a throttled profile. There is no model in this "
                "system, so there is no read line at all."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ps",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the browser packaging, and why there is no model in it."),
 outside=[
  {"title": "Your pages", "sub": ["loaded for real"], "icon": "browser"},
  {"title": "Deploy feed", "sub": ["webhook or S3 drop"], "icon": "code"},
  {"title": "SES outbound", "sub": ["regressions, monthly"], "icon": "email"}],
 inside=[
  {"title": "EventBridge + SQS", "sub": ["daily trigger,", "one page per message"], "icon": "queue"},
  {"title": "Lambda x3", "sub": ["measure, compare,", "report"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["runs, budgets"], "icon": "database"}],
 note="us-east-1. One account. A container image Lambda, because a browser does not fit a zip.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Your pages, loaded for real by a headless "
  "browser. The Deploy feed, arriving as a webhook or an S3 drop. And SES outbound, carrying "
  "regression messages and the monthly summary. Inside the account, three groups. EventBridge "
  "providing a daily trigger and SQS carrying one message per page. Three Lambda functions named "
  "measure, compare and report. And two DynamoDB tables named runs and budgets. A note gives the "
  "region as us-east-1, one account, and notes that measure is a container image Lambda because "
  "a browser does not fit in a zip package."),
 functions=[
  ["<code>ps-measure</code>", "SQS page queue",
   "Nine loads of one page on the fixed profile; stores medians and resources",
   "300s / 3008&nbsp;MB, container image"],
  ["<code>ps-compare</code>", "SQS measured queue",
   "Baseline, spread, two-run confirmation, budget check", "30s / 512&nbsp;MB"],
  ["<code>ps-report</code>", "SQS regression queue + EventBridge monthly",
   "Resource diff, deploy correlation, the monthly summary", "60s / 1024&nbsp;MB"]],
 roles=[
  ["<code>ps-measure-role</code>", "<code>dynamodb:PutItem</code>, <code>s3:PutObject</code>",
   "The runs table; the traces prefix"],
  ["<code>ps-compare-role</code>",
   "<code>dynamodb:Query</code>/<code>UpdateItem</code>, <code>sqs:SendMessage</code>",
   "Runs and budgets; the regression queue"],
  ["<code>ps-report-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "Runs, read; one verified identity"]],
 tables=[
  ("Table: runs",
   "PK   page              S   /pricing\n"
   "SK   run_at            S   2026-07-29T06:00:00Z\n"
   "     lcp_median        N   2.04     -- seconds\n"
   "     lcp_samples       L   all nine, so a run can be judged later\n"
   "     cls_median        N   0.03\n"
   "     tbt_median        N   180      -- milliseconds\n"
   "     bytes_total       N   742000\n"
   "     bytes_js          N   164000\n"
   "     bytes_third_party N   118000\n"
   "     requests          N   41\n"
   "     resources         L   [{url, type, bytes, ms}]  -- the diff source\n"
   "     browser_version   S   recorded so a step change is explainable\n"
   "     profile_id        S   v1  -- bumped only when the profile changes\n\n"
   "`profile_id` is what makes a methodology change visible. Comparisons never\n"
   "cross a profile boundary; the chart shows a break instead of a smooth lie."),
  ("Table: budgets",
   "PK   page              S   /pricing\n"
   "     bytes_total       N   800000\n"
   "     bytes_js          N   180000\n"
   "     bytes_images      N   400000\n"
   "     bytes_third_party N   150000\n"
   "     requests          N   45\n"
   "     set_at            S   2026-04-02\n"
   "     set_from          S   current+10% | intention\n"
   "     breached_runs_q   N   how many runs this quarter were over\n\n"
   "`breached_runs_q` over half the quarter's runs triggers the quarterly\n"
   "question: is the budget wrong, or is this a real problem nobody has done?")],
 inbound=[
  "<strong>The measure function is a container image Lambda</strong> at 3008&nbsp;MB. A headless "
  "browser does not fit in a zip package, and the memory setting is really a CPU setting &mdash; "
  "a browser on 512&nbsp;MB measures a slower page than the same page on 3008.",
  "<strong>One page per SQS message</strong>, so nine samples of one page fit comfortably inside "
  "a single invocation and a failure on one page does not lose the run.",
  "<strong>The deploy feed</strong> is a webhook writing to S3, or an S3 drop from CI. It needs "
  "only a timestamp and an identifier; the correlation is a time comparison.",
  "<strong>Nothing is fetched from a third-party performance API.</strong> The measurements are "
  "your own, which is what makes the history comparable."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Medians, spreads and resource diffs are "
  "arithmetic.",
  "<strong>The tempting use</strong> is generating a recommendation from a resource diff, and it "
  "is worse than the diff: \"hero-q3.jpg is 1.4MB\" is already the recommendation.",
  "<strong>The report wording is fixed</strong>, with the numbers substituted, which also means "
  "it says the same thing every time and gets read faster.",
  "<strong>Attribution is a comparison</strong> between two resource lists, not a judgement.",
  "<strong>The cost page assumes none</strong>, which is why the whole variable cost is browser "
  "time."],
 gotchas=[
  "Pin the browser version and record it. An auto-update produces a step change on a day nobody "
  "deployed, which is exactly how a monitor loses credibility.",
  "Bump profile_id when the profile changes, and never compare across it. A methodology change "
  "drawn as a smooth line is worse than no chart.",
  "Set Lambda memory high. On a browser workload memory is CPU, and a low setting measures your "
  "own throttling rather than the page.",
  "Close the browser in a finally block. A leaked browser costs the full function timeout on "
  "every invocation.",
  "Keep the page list short. Cost is linear in pages times samples, and a report covering eighty "
  "pages is one nobody reads anyway."],
))
