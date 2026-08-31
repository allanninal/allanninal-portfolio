"""Day 101 -- 2026-08-03 -- Cost anomaly alerter."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "cost-anomaly-alerter"
NAME = "Cost anomaly alerter"

SPEC = {
 "slug": SLUG, "date": "2026-08-03", "name": NAME,
 "tagline": ("Tells you a cloud bill is running away on the day it starts rather than on the "
             "first of next month -- with the service, the resource and the change that caused "
             "it already worked out."),
 "lede": ("A small system that reads yesterday's cloud spend, compares each service against what "
          "it normally does, and reports the ones that moved with the specific resource named. "
          "It cannot stop anything, and the design is honest about why that is the right choice. "
          "Seven posts on the same system -- one diagram at a time -- with a cost breakdown and "
          "an engineering reference at the end."),
 "keywords": ["cloud cost", "FinOps", "AWS billing", "anomaly detection", "budgets", "serverless"],
 "icons": ["money", "chart", "alarm"],
 "faq": [
  ("What is a cost anomaly alerter?",
   "A small serverless system that reads daily cloud spend by service and resource, compares "
   "each line against its own recent pattern, and reports movement with the resource named. It "
   "reports; it never stops or deletes anything."),
  ("Why not just use a budget alert?",
   "A budget alert fires when a monthly total crosses a line, which is usually around the 24th "
   "and always too late. This compares daily, per service, so a runaway is visible on day one "
   "when it has cost a fortieth of what it will."),
  ("Can it stop a runaway resource?",
   "No, deliberately. A system with permission to delete or stop resources in response to a "
   "metric is a system that can take your production environment down because of a "
   "misattributed cost line. It tells a person, quickly."),
  ("Why is the data a day late?",
   "Because cloud billing data is. There is a faster signal for a few services, and for "
   "everything else a day is the floor. The design assumes it rather than pretending otherwise."),
  ("What does it cost to run?",
   "Under a dollar a month, which is a pleasing property for a cost monitor. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "cost-anomaly-alerter-on-aws",
 "title": "A cost anomaly alerter on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Reads daily spend by service and resource, compares each against its own pattern, and "
          "names what moved. AWS, under $1 a month."),
 "og": ("A monthly budget alert fires on the 24th. A daily comparison per service catches the "
        "same runaway on day one, at a fortieth of the cost."),
 "abstract": ("The whole system on one page -- a daily fetch, a per-service comparison and an "
              "attribution step -- plus the deliberate decision not to give it the ability to "
              "stop anything."),
 "lede": ("Cloud bills go wrong in a particular shape. Nothing happens for months, then one "
          "change &mdash; a recursive trigger, a log group with no retention, a NAT gateway "
          "somebody added for one thing &mdash; starts costing forty pounds a day, and the first "
          "anybody knows is the invoice on the third of next month. By then it has cost twelve "
          "hundred pounds and it is still running. This post walks through a small system that "
          "notices on day one."),
 "tags": ["cloud cost", "FinOps", "AWS billing", "anomaly detection", "budgets", "serverless"],
 "takeaways": [
  "Daily comparison per service, not a monthly total against a budget.",
  "Each service is compared against its own recent pattern, so no thresholds are guessed.",
  "The report names the resource, not just the service, which is what makes it actionable.",
  "It cannot stop or delete anything, and that is a deliberate safety decision.",
  "Designed on AWS for under $1 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Cost data", "sub": ["daily, by service"], "icon": "money"},
      {"title": "Resource tags", "sub": ["what belongs to what"], "icon": "tag"},
      {"title": "Whoever pays", "sub": ["and whoever built it"], "icon": "team"}],
    "inside": [
      {"title": "Fetcher", "sub": ["yesterday, by service", "and by resource"], "icon": "database"},
      {"title": "Comparer", "sub": ["each line against", "its own pattern"], "icon": "counter"},
      {"title": "Attributor", "sub": ["which resource,", "and what changed"], "icon": "search"}],
    "edges": [{"from": 0, "to": 0, "label": "yesterday's spend"},
              {"from": 1, "to": 1, "label": "who owns what"},
              {"from": 2, "to": 2, "label": "the resource, named", "up": True}],
    "note": "No permission to stop, delete or scale anything. It tells a person, fast."}),
   "Three things outside the account, three pieces inside it. The note at the bottom is a "
   "capability decision rather than a limitation, and Part 5 argues for it.",
   "System: daily cost data compared per service and attributed to resources",
   "Three boxes across the top sit outside the AWS account. On the left, Cost data: daily, by "
   "service. In the middle, Resource tags: the record of what belongs to what. On the right, "
   "Whoever pays and whoever built it. Each connects by an arrow to the AWS account container "
   "below. Yesterday's spend flows down into the account. Tags feed in who owns what. The named "
   "resource goes back out. Inside the AWS account are three components in a row. On the left, "
   "the Fetcher, which pulls yesterday by service and by resource. In the middle, the Comparer, "
   "which measures each line against its own pattern. On the right, the Attributor, which works "
   "out which resource and what changed. A note at the bottom says the system has no permission "
   "to stop, delete or scale anything, and tells a person fast instead."),
  ("h3", "Daily, per service"),
  ("p", "A monthly budget alert is a single number crossing a single line, and by construction it "
        "fires late: a runaway that starts on the 2nd will not push the month over budget until "
        "somewhere around the 24th, by which point it has cost twenty-two days of whatever it "
        "costs."),
  ("p", "Comparing each service daily against its own recent daily spend catches the same event "
        "on the second or third day, when it has cost two or three days. That is the entire "
        "value proposition, and it needs no budget, no forecast and no threshold &mdash; only the "
        "observation that this service does not normally cost this."),
  ("h3", "What runs daily (the inside)"),
  ("ul", [
   "<strong>The fetcher.</strong> Pulls yesterday's cost grouped by service, and separately by "
   "resource where the data supports it. Part 2 covers the delay, the granularity, and the "
   "services where resource-level attribution is not available.",
   "<strong>The comparer.</strong> Each service against its own last few weeks, with the same "
   "day-of-week awareness as the log spotter, because weekend spend genuinely differs. Part 3 "
   "covers the two shapes a cost anomaly takes.",
   "<strong>The attributor.</strong> Turns \"Lambda is up £31\" into \"the "
   "<code>image-resize</code> function ran 400,000 times yesterday against a normal 2,000\", "
   "which is the difference between a number and a cause.",
  ]),
  ("h2", "One anomaly, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Yesterday's spend", "sub": ["by service"], "icon": "money"},
      {"title": "Compared", "sub": ["to its own 28 days"], "icon": "chart"},
      {"title": "One service moved", "sub": ["Lambda, +£31"], "icon": "alarm"},
      {"title": "Attributed", "sub": ["one function, 200x invocations"], "icon": "search"},
      {"title": "Told", "sub": ["with the projection"], "icon": "report"}],
    "title": "ONE COST ANOMALY, END TO END",
    "note": "The fourth box is what turns a bill into a bug report."}),
   "The same system as one line. Attribution is what changes the message from a finance "
   "observation into something an engineer can act on immediately.",
   "One cost anomaly from daily data to an attributed report, in five stages",
   "A horizontal row of five boxes joined by arrows. Yesterday's spend: by service. Compared: "
   "against its own twenty-eight days. One service moved: Lambda, up thirty-one pounds. "
   "Attributed: one function running two hundred times its normal invocations. Told: with the "
   "projection. A note says the fourth box is what turns a bill into a bug report."),
  ("h2", "In plain words"),
  ("p", "A small business's AWS bill runs at about eleven pounds a day, and Lambda is normally "
        "about ninety pence of that. On Tuesday Lambda is thirty-two pounds. Nothing else moved."),
  ("p", "The attributor looks at the resource-level data and finds one function, "
        "<code>image-resize</code>, with four hundred thousand invocations against a normal two "
        "thousand. It also notices that the function writes to the same S3 prefix that triggers "
        "it &mdash; which the message states as a fact rather than a diagnosis, but which is "
        "enough for anybody who has seen a recursive trigger before."),
  ("p", "The message goes out on Wednesday morning: \"Lambda £32 yesterday, normally £0.90. One "
        "function, <code>image-resize</code>, 400k invocations against a normal 2k. At this rate "
        "the month will be about £960 rather than £330.\" That is fixed before lunch and it has "
        "cost about sixty pounds. The version of this story without the system ends on the third "
        "of next month and costs nine hundred."),
  ("callout", "Design rules that shaped every decision", [
   "Compare daily, per service, against each service's own history. No budgets, no thresholds.",
   "Always attribute. A service name is a question; a resource name is an answer.",
   "Project the month. The daily number is small and the projection is what gets attention.",
   "It cannot stop anything. A cost metric is not a safe trigger for deleting infrastructure.",
   "Tell the person who built it as well as the person who pays for it.",
   "Report a fall as well as a rise. A service that stopped costing anything usually stopped "
   "working.",
  ]),
  ("h2", "Why this shape"),
  ("p", "AWS has a native anomaly detection service and it is good; for many businesses that plus "
        "a budget is genuinely enough. The reason to build something small alongside it is the "
        "attribution and the wording: a native alert tells you a service moved, and the thing "
        "somebody needs is which resource and what to do about it."),
  ("p", "So this design spends almost nothing on detection &mdash; a per-service comparison is a "
        "dozen lines &mdash; and almost everything on turning a detection into a sentence with a "
        "resource name and a monthly projection in it. That sentence is what gets the problem "
        "fixed the same morning."),
  ("p", "The next four posts walk through each piece: how the cost data arrives, how an anomaly "
        "is judged, how it gets attributed to a resource, and why the system cannot act. One "
        "diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-cost-data-arrives",
 "title": "How cost data arrives",
 "nav": "How data arrives",
 "read": 5, "words": 750,
 "desc": ("The delay you cannot avoid, the two granularities available, the services where "
          "resource attribution does not exist, and the faster signals worth adding."),
 "og": ("Billing data is a day late and there is no way round it. What you can do is add faster "
        "proxy signals for the services that run away fastest."),
 "abstract": ("The unavoidable billing delay, the two granularities available, the services where "
              "resource-level attribution simply does not exist, and the faster proxy signals "
              "worth adding alongside."),
 "lede": ("Cost data is a day late and sometimes two, and every design in this space has to start "
          "by accepting that. What is worth knowing is exactly how late, what granularity you can "
          "get, and which faster signals exist for the handful of services that can run away "
          "faster than a day."),
 "tags": ["cloud cost", "AWS billing", "Cost Explorer", "CUR", "data collection", "serverless"],
 "takeaways": [
  "Billing data settles about 24 hours behind, and some lines take longer.",
  "Two sources: a daily API for service totals, and detailed reports for resource level.",
  "Some services have no resource-level attribution at all, and the report says so.",
  "Yesterday's figure can still change; re-fetch the last three days each run.",
  "For the fastest-moving services, a usage metric is a same-hour proxy worth adding.",
 ],
 "blocks": [
  ("h2", "The delay"),
  ("fig", ("chain", {
    "entry": {"title": "The daily run", "sub": ["09:00"], "icon": "clock"},
    "steps": [
      {"title": "Fetch the last 3 days", "sub": ["not just yesterday"], "icon": "database",
       "side": {"title": "Cost API", "sub": ["by service, daily"], "icon": "money"}},
      {"title": "Any day changed?", "sub": ["restatements happen"], "icon": "branch",
       "exit": {"title": "Update the history", "sub": ["and re-compare"], "icon": "retry",
                "label": "yes"}},
      {"title": "Resource level available?", "sub": ["per service"], "icon": "branch",
       "exit": {"title": "Service level only", "sub": ["say so in the report"], "icon": "alarm",
                "label": "no"}},
      {"title": "Fetch by resource", "sub": ["for the services that support it"], "icon": "search"},
      {"title": "Ready to compare", "sub": ["one day, two granularities"], "icon": "check"}],
    "note": "Re-fetching three days is what stops a restated figure producing a phantom anomaly."}),
   "The daily fetch. Re-reading the previous three days rather than only yesterday is what keeps "
   "the history honest as billing figures settle.",
   "How daily cost data is fetched and reconciled",
   "A vertical chain of five steps entered by a box labelled The daily run at nine in the "
   "morning. Step one fetches the last three days rather than just yesterday, from the cost API "
   "by service and daily. Step two asks whether any day changed, since restatements happen; if so "
   "it exits to Update the history and re-compare. Step three asks whether resource-level data is "
   "available for each service; if not it exits to Service level only, and the report says so. "
   "Step four fetches by resource for the services that support it. Step five is Ready to "
   "compare, with one day at two granularities. A note says re-fetching three days is what stops "
   "a restated figure producing a phantom anomaly."),
  ("h3", "Why three days"),
  ("p", "Yesterday's figure is provisional. Some usage is reported late, some is reallocated "
        "between services, and credits and discounts land afterwards. A figure fetched on "
        "Wednesday for Tuesday can be meaningfully different when fetched again on Friday."),
  ("p", "So each run re-fetches the last three days and updates the history rather than only "
        "appending. Without that, a day that was restated upwards stays in the baseline at its "
        "provisional value, and the baseline slowly drifts away from what the bill actually says."),
  ("h2", "Two granularities"),
  ("table", ["Level", "What you get", "Latency"], [
   ["Service, daily", "Total per service per day", "About 24 hours"],
   ["Resource, daily", "Per function, bucket, table, instance", "24&ndash;48 hours, and not for everything"],
   ["Usage metrics", "Invocations, requests, GB stored", "Minutes"],
  ]),
  ("p", "The third row is the interesting one. Usage metrics are not cost data, they are "
        "available almost immediately, and for the services that can run away fastest they are a "
        "very good proxy. A Lambda function running four hundred thousand times in an hour is "
        "visible in metrics within minutes and in cost data tomorrow."),
  ("h3", "Where resource attribution does not exist"),
  ("p", "Several services report only at the account level, or aggregate resources in ways that "
        "make attribution impossible. Data transfer is the classic example: a large egress charge "
        "is real, attributable to nothing specific in the billing data, and frequently the "
        "hardest anomaly to chase."),
  ("p", "The honest handling is to say so in the report rather than to guess. \"Data transfer up "
        "£18; this service does not report at resource level, so the likely candidates by volume "
        "are these three buckets\" is more useful than either silence or a confident wrong "
        "attribution."),
  ("h2", "The fast proxies"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Lambda invocations", "sub": ["minutes"], "icon": "lambda"},
      {"title": "S3 request count", "sub": ["minutes"], "icon": "bucket"},
      {"title": "NAT bytes", "sub": ["minutes"], "icon": "network"},
      {"title": "Cost data", "sub": ["tomorrow"], "icon": "money"},
      {"title": "Both", "sub": ["fast signal, slow truth"], "icon": "check"}],
    "title": "THREE METRICS THAT MOVE BEFORE THE BILL DOES",
    "note": "These three cover almost every runaway that can cost real money inside a day."}),
   "The three usage metrics worth watching alongside the billing data. All three are available in "
   "minutes and all three precede the cost lines that most often run away.",
   "Three usage metrics that move before cost data does",
   "A horizontal row of five boxes. Lambda invocations: available in minutes. S3 request count: "
   "minutes. NAT gateway bytes: minutes. Cost data: tomorrow. Both: a fast signal and a slow "
   "truth. A note says these three cover almost every runaway that can cost real money inside a "
   "day."),
  ("p", "Adding those three as separate hourly checks, compared against their own patterns exactly "
        "like the cost lines, turns a one-day detection into a one-hour one for the three "
        "services that most often produce a genuinely expensive surprise. They are not cost data "
        "and the report says so &mdash; \"invocations are 200x normal; the cost impact will "
        "appear tomorrow\" &mdash; which is both honest and completely actionable."),
  ("p", "Next: how an anomaly is judged."),
 ],
},
{
 "slug": "how-a-cost-anomaly-is-judged",
 "title": "How a cost anomaly is judged",
 "nav": "How it is judged",
 "read": 5, "words": 740,
 "desc": ("Two shapes of cost anomaly, why absolute pounds gate everything, and the new service "
          "that has no history at all."),
 "og": ("A step change and a ramp need different detection. And a hundredfold increase on four "
        "pence is still four pence."),
 "abstract": ("The two shapes a cost anomaly takes, why absolute money gates every relative "
              "comparison, how a new service with no history is handled, and the fall that "
              "matters."),
 "lede": ("Cost anomalies come in two shapes and most detection only catches one. A step change "
          "is obvious the next morning. A ramp &mdash; something growing ten per cent a day "
          "&mdash; never triggers a day-on-day comparison and is how the genuinely expensive "
          "surprises happen."),
 "tags": ["cloud cost", "anomaly detection", "FinOps", "thresholds", "monitoring", "serverless"],
 "takeaways": [
  "Two shapes: a step change, and a ramp that no daily comparison will catch.",
  "Absolute money gates everything. A 100x increase on four pence is four pence.",
  "A new service with no history is reported once, on its first day of spend.",
  "Weekend and weekday spend differ, so compare like days.",
  "A service that stopped costing anything usually stopped working.",
 ],
 "blocks": [
  ("h2", "Two shapes"),
  ("fig", ("chain", {
    "entry": {"title": "A service, yesterday", "sub": ["with a figure"], "icon": "money"},
    "steps": [
      {"title": "Over the money floor?", "sub": ["e.g. £5 of movement"], "icon": "branch",
       "exit": {"title": "Ignore", "sub": ["however large the multiple"], "icon": "stop",
                "label": "no"}},
      {"title": "Any history?", "sub": ["14 days minimum"], "icon": "branch",
       "exit": {"title": "New service", "sub": ["report once, on day one"], "icon": "bell",
                "label": "no"}},
      {"title": "Step change?", "sub": ["vs the same weekday"], "icon": "branch",
       "exit": {"title": "Report it", "sub": ["and attribute"], "icon": "alarm", "label": "yes"}},
      {"title": "Ramping?", "sub": ["7-day trend vs the 21 before"], "icon": "branch",
       "exit": {"title": "Report the trend", "sub": ["with the projection"], "icon": "chart",
                "label": "yes"}},
      {"title": "Normal", "sub": ["most services, most days"], "icon": "check"}],
    "note": "The ramp check is the one most implementations omit, and it is where the money is."}),
   "How a service's daily figure is judged. The two detection shapes catch different failures and "
   "the second one is the expensive one.",
   "How a daily cost figure is judged for anomalies",
   "A vertical chain of five steps entered by a box labelled A service, yesterday, with a figure. "
   "Step one asks whether the movement is over the money floor, for example five pounds; if not "
   "it exits to Ignore, however large the multiple. Step two asks whether there is any history, "
   "with fourteen days minimum; if not it exits to New service, reported once on day one. Step "
   "three asks whether it is a step change against the same weekday; if so it exits to Report it "
   "and attribute. Step four asks whether it is ramping, comparing the last seven days against "
   "the twenty-one before; if so it exits to Report the trend with a projection. Step five is "
   "Normal, which is most services on most days. A note says the ramp check is the one most "
   "implementations omit and it is where the money is."),
  ("h3", "The ramp"),
  ("p", "A service growing eight per cent a day never triggers a day-on-day comparison: today is "
        "always within a sensible band of yesterday. After a month it costs ten times what it "
        "did, and every individual day looked fine."),
  ("p", "The usual causes are storage that is never expired, a log group filling up, a table "
        "growing without a TTL, or a workload that genuinely is growing and nobody has noticed how "
        "fast. All of them are cheap to fix early and expensive to discover late."),
  ("p", "The check is deliberately simple: the last seven days' average against the twenty-one "
        "before it. A twenty-five per cent increase between those two windows is a ramp, and the "
        "report carries the projection rather than the percentage, because \"on this trend the "
        "month will be £430 rather than £180\" is what gets attention."),
  ("h3", "The money floor"),
  ("p", "The single most important guard. Relative comparisons on small numbers are meaningless: "
        "a service that cost four pence yesterday and four pounds today has increased a "
        "hundredfold and is not worth a message."),
  ("p", "So a movement must exceed an absolute amount before any relative test applies. Five "
        "pounds a day is a reasonable floor for a business whose bill is eleven pounds a day, and "
        "it should be set as a fraction of the total bill rather than as a fixed number, so it "
        "scales without anybody remembering to change it."),
  ("h2", "New services and falls"),
  ("fig", ("strip", {
    "stages": [
      {"title": "New service appears", "sub": ["no history"], "icon": "search"},
      {"title": "Report once", "sub": ["'this is new'"], "icon": "bell"},
      {"title": "14 days later", "sub": ["it has a baseline"], "icon": "calendar"},
      {"title": "A service falls to zero", "sub": ["was £6 a day"], "icon": "alarm"},
      {"title": "Usually something broke", "sub": ["not a saving"], "icon": "stop"}],
    "title": "TWO CASES THAT ARE NOT SPIKES",
    "note": "A service that stopped costing money has usually stopped doing its job."}),
   "Two findings that a spike detector misses entirely. The fall is the one people are surprised "
   "to see reported and it is frequently the more urgent of the two.",
   "Two cost findings that are not spikes",
   "A horizontal row of five boxes. New service appears: with no history. Report once: saying "
   "this is new. Fourteen days later: it has a baseline. A service falls to zero: having been six "
   "pounds a day. Usually something broke: rather than a saving. A note says a service that "
   "stopped costing money has usually stopped doing its job."),
  ("p", "The new-service report is worth having because a service appearing on the bill for the "
        "first time is frequently somebody trying something, and the useful moment to ask whether "
        "it is going to stay is the day it appears rather than the month it becomes significant."),
  ("p", "The fall is the one that surprises people in a cost alerter and it earns its place. A "
        "service that was costing six pounds a day and is now costing nothing has almost never "
        "become efficient overnight. A queue with no messages, a function with no invocations, a "
        "database with no reads &mdash; each of those is a saving on the bill and an outage in "
        "the business."),
  ("p", "Next: attribution."),
 ],
},
{
 "slug": "how-a-cost-spike-gets-attributed",
 "title": "How a cost spike gets attributed",
 "nav": "How it is attributed",
 "read": 5, "words": 740,
 "desc": ("From a service name to a resource name to a change, the four usual causes, and what "
          "to do when attribution is impossible."),
 "og": ("\"Lambda is up £31\" is a question. \"image-resize ran 400,000 times against a normal "
        "2,000\" is a bug report."),
 "abstract": ("Getting from a service name to a resource to a change, the four causes that "
              "account for most spikes, and how to be useful when attribution is genuinely "
              "impossible."),
 "lede": ("This is the step that decides whether the message gets acted on this morning or added "
          "to a list. A service name is a place to start looking. A resource name with a usage "
          "figure next to it is frequently the whole diagnosis."),
 "tags": ["cloud cost", "attribution", "tagging", "FinOps", "diagnosis", "serverless"],
 "takeaways": [
  "Three levels: service, resource, and the usage number that explains it.",
  "Four causes account for most spikes: volume, retention, a new resource, and recursion.",
  "Tags turn a resource name into an owner, which is who should be told.",
  "Where attribution is impossible, list the candidates by size rather than guessing.",
  "Correlate against deploys and infrastructure changes, and state it as correlation.",
 ],
 "blocks": [
  ("h2", "Service to resource to cause"),
  ("fig", ("chain", {
    "entry": {"title": "A service moved", "sub": ["Lambda, +£31"], "icon": "alarm"},
    "steps": [
      {"title": "Resource-level data?", "sub": ["for this service"], "icon": "branch",
       "side": {"title": "Detailed costs", "sub": ["per resource, daily"], "icon": "database"},
       "exit": {"title": "List candidates", "sub": ["by size, and say why"], "icon": "search",
                "label": "no"}},
      {"title": "Which resource?", "sub": ["usually one, sometimes two"], "icon": "filter"},
      {"title": "Which usage metric moved?", "sub": ["invocations, GB, requests"], "icon": "counter",
       "side": {"title": "CloudWatch", "sub": ["the same day"], "icon": "monitor"}},
      {"title": "Who owns it?", "sub": ["from the tags"], "icon": "team",
       "exit": {"title": "Untagged", "sub": ["itself a finding"], "icon": "alarm",
                "label": "no tag"}},
      {"title": "One sentence", "sub": ["resource, number, owner"], "icon": "report"}],
    "note": "The usage metric is what turns 'this is expensive' into 'this is running 200x'."}),
   "How a service-level movement becomes a specific diagnosis. The usage metric in step three is "
   "what makes the message a bug report rather than an observation.",
   "How a cost spike is attributed to a specific resource",
   "A vertical chain of five steps entered by a box labelled A service moved, Lambda up "
   "thirty-one pounds. Step one asks whether resource-level data exists for this service, using "
   "detailed daily costs per resource; if not it exits to List candidates by size and say why. "
   "Step two identifies which resource, usually one and sometimes two. Step three asks which "
   "usage metric moved, such as invocations, gigabytes or requests, read from CloudWatch for the "
   "same day. Step four asks who owns it, taken from the tags; an untagged resource exits to "
   "Untagged, which is itself a finding. Step five produces one sentence naming the resource, the "
   "number and the owner. A note says the usage metric is what turns this is expensive into this "
   "is running two hundred times normal."),
  ("h2", "The four usual causes"),
  ("table", ["Cause", "Looks like", "Typical fix"], [
   ["Volume", "Usage metric up sharply, unit cost unchanged",
    "Find what is calling it; often a retry loop or a recursion"],
   ["Retention", "Storage growing steadily; a ramp, not a step",
    "A lifecycle rule or a log retention setting that was never set"],
   ["New resource", "A resource that did not exist last week",
    "Usually deliberate; the question is whether it was expected to cost this"],
   ["Recursion", "A function or queue triggering itself",
    "Almost always a trigger scoped too broadly; the most expensive of the four"],
  ]),
  ("p", "Recursion deserves its own row because it is the one that produces genuinely alarming "
        "numbers in hours rather than days. The signature is unmistakable once you know it: "
        "invocations and writes both far outside normal, on a resource whose trigger points at "
        "somewhere the resource itself writes."),
  ("p", "The system does not claim that diagnosis &mdash; it does not know the trigger "
        "configuration &mdash; but it can state both facts side by side, and anybody who has seen "
        "one before recognises it immediately from that."),
  ("h2", "Tags, and untagged resources"),
  ("p", "A resource name tells an engineer what to look at. A tag tells the system who to tell, "
        "which matters because the person who pays the bill and the person who can fix the "
        "resource are usually different people."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Resource named", "sub": ["image-resize"], "icon": "search"},
      {"title": "Owner tag", "sub": ["team or person"], "icon": "team"},
      {"title": "Both told", "sub": ["payer and builder"], "icon": "email"},
      {"title": "No owner tag", "sub": ["nobody to tell"], "icon": "alarm"},
      {"title": "Untagged spend", "sub": ["reported monthly as a share"], "icon": "chart"}],
    "title": "TAGS DECIDE WHO HEARS ABOUT IT",
    "note": "Untagged spend as a percentage is the one FinOps metric worth tracking here."}),
   "Why tags matter for a cost alerter specifically: they are the difference between telling "
   "somebody and telling the right somebody.",
   "How resource tags determine who is told about a cost anomaly",
   "A horizontal row of five boxes. Resource named: image-resize. Owner tag: a team or a person. "
   "Both told: the payer and the builder. No owner tag: there is nobody to tell. Untagged spend: "
   "reported monthly as a share. A note says untagged spend as a percentage is the one FinOps "
   "metric worth tracking here."),
  ("p", "Reporting untagged spend as a monthly percentage is a small addition with a large effect. "
        "A business where sixty per cent of spend is untagged cannot route any cost finding to "
        "anybody, and watching that number fall is a more useful project than any individual "
        "anomaly."),
  ("h3", "When attribution is impossible"),
  ("p", "Data transfer, support charges, and a handful of services report at a level that makes "
        "resource attribution genuinely unavailable. The useful output there is a ranked list of "
        "candidates with the reason: \"data transfer up £18; no resource attribution available "
        "for this line. The three largest egress sources by volume yesterday were these buckets.\""),
  ("p", "That is honest about the uncertainty and still points somebody at three things to check "
        "rather than at the whole account, which is most of the value attribution provides."),
  ("p", "Next: why the system cannot act."),
 ],
},
{
 "slug": "why-the-alerter-cannot-act",
 "title": "Why the alerter cannot act",
 "nav": "Why it cannot act",
 "read": 5, "words": 730,
 "desc": ("The argument against automatic remediation, the one exception worth considering, and "
          "what the message contains instead."),
 "og": ("A system that can delete infrastructure in response to a cost metric can take "
        "production down because of a misattributed line. The answer is a fast message, not a "
        "fast action."),
 "abstract": ("The argument against automatic remediation, the one narrow exception worth "
              "considering, what the message contains instead, and the monthly numbers."),
 "lede": ("The obvious next feature, requested within a week of this system existing, is for it "
          "to stop the runaway rather than telling somebody about it. It is a reasonable request "
          "with a bad answer, and the reasoning is worth setting out properly rather than "
          "asserting."),
 "tags": ["cloud cost", "automation", "safety", "blast radius", "operations", "serverless"],
 "takeaways": [
  "A cost signal is a lagging, aggregated, occasionally misattributed metric.",
  "Acting on it means giving a system permission to delete production infrastructure.",
  "The failure mode is asymmetric: a wrong action costs far more than a delayed fix.",
  "The one defensible exception is a hard concurrency cap set in advance, not in response.",
  "What the message carries instead: the projection, the resource, and the likely fix.",
 ],
 "blocks": [
  ("h2", "Three properties of the signal"),
  ("fig", ("chain", {
    "entry": {"title": "Should it act?", "sub": ["the obvious request"], "icon": "branch"},
    "steps": [
      {"title": "Is the signal timely?", "sub": ["a day late"], "icon": "clock",
       "exit": {"title": "No", "sub": ["acting on stale data"], "icon": "stop", "label": "no"}},
      {"title": "Is it precise?", "sub": ["aggregated, sometimes wrong"], "icon": "search",
       "exit": {"title": "No", "sub": ["misattribution happens"], "icon": "stop", "label": "no"}},
      {"title": "Is the action safe?", "sub": ["stop, delete, scale down"], "icon": "alarm",
       "exit": {"title": "No", "sub": ["that is production"], "icon": "stop", "label": "no"}},
      {"title": "So: tell a person", "sub": ["fast, and with the diagnosis"], "icon": "person"},
      {"title": "Speed is in the message", "sub": ["not the action"], "icon": "email"}],
    "note": "Every one of the three has to be yes for automatic action, and none of them is."}),
   "The three properties an automation would need and does not have. The conclusion is not "
   "caution for its own sake; it follows from what the signal actually is.",
   "Why a cost anomaly is not a safe trigger for automatic action",
   "A vertical chain of five steps entered by a box labelled Should it act, the obvious request. "
   "Step one asks whether the signal is timely, and it is a day late, so the answer exits to No, "
   "because acting on stale data. Step two asks whether it is precise, and it is aggregated and "
   "sometimes wrong, exiting to No because misattribution happens. Step three asks whether the "
   "action is safe, covering stop, delete and scale down, and exits to No because that is "
   "production. Step four concludes: tell a person, fast, and with the diagnosis. Step five notes "
   "that speed is in the message rather than the action. A note says every one of the three would "
   "have to be yes for automatic action and none of them is."),
  ("h3", "The asymmetry"),
  ("p", "A runaway that is fixed four hours later than it could have been costs a few more hours "
        "of whatever it costs, which is usually tens of pounds. A system that stops the wrong "
        "resource because a cost line was misattributed takes a production service down for as "
        "long as it takes somebody to work out what happened."),
  ("p", "Those two are not comparable, and the comparison does not become closer as the bill gets "
        "bigger &mdash; a business with a larger bill also has a more expensive outage. The "
        "arithmetic points the same way at every scale."),
  ("h3", "The one defensible exception"),
  ("p", "A concurrency cap set in advance, as a permanent configuration rather than as a "
        "response. A Lambda function whose reserved concurrency is capped at fifty cannot run "
        "four hundred thousand times an hour whatever goes wrong, and the cap was set on a "
        "quiet Tuesday by somebody thinking about the function rather than by an alerter at "
        "three in the morning."),
  ("p", "That is genuinely worth doing and it is not this system doing it. It is a standing "
        "design decision that limits the blast radius of every future mistake, and the useful "
        "thing this system can contribute is a monthly note about which functions have no cap and "
        "how much they could theoretically cost."),
  ("h2", "What the message carries instead"),
  ("callout", "Four lines, sent by 09:15", [
   "<strong>Lambda, £32 yesterday.</strong> Normally £0.90 on a Tuesday.",
   "<strong>One function:</strong> <code>image-resize</code>, 400,000 invocations against a "
   "normal 2,000. It writes to the same S3 prefix that triggers it.",
   "<strong>On this rate</strong> the month will be about £960 rather than £330.",
   "<strong>It is still running.</strong> Invocations in the last hour: 16,800.",
   "<em>To: the account owner and the team tagged on the function.</em>",
  ]),
  ("p", "The fourth line is the one that produces action within minutes rather than within the "
        "day. Cost data is a day late, but the usage metric is current, and saying plainly that "
        "the thing is happening right now converts a finance message into an incident."),
  ("h2", "The monthly numbers"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Spend", "sub": ["£340, +4%"], "icon": "money"},
      {"title": "Anomalies", "sub": ["2, both fixed"], "icon": "alarm"},
      {"title": "Caught early", "sub": ["saved ~£1,100"], "icon": "chart"},
      {"title": "Untagged", "sub": ["12% of spend"], "icon": "tag"},
      {"title": "Uncapped functions", "sub": ["4"], "icon": "search"}],
    "title": "ONE MONTH OF COST WATCHING",
    "note": "The third number is an estimate and should be labelled as one. It is still the point."}),
   "A month of cost watching in five numbers. The saving estimate is the one that justifies the "
   "system and the one to be careful about claiming precisely.",
   "One month of cost anomaly detection summarised in five numbers",
   "A horizontal row of five boxes. Spend: three hundred and forty pounds, up four per cent. "
   "Anomalies: two, both fixed. Caught early: an estimated saving of about eleven hundred pounds. "
   "Untagged: twelve per cent of spend. Uncapped functions: four. A note says the third number is "
   "an estimate and should be labelled as one, and that it is still the point."),
  ("p", "The saving figure is a projection of what the anomaly would have cost if it had run to "
        "the end of the month, minus what it did cost. It is an estimate, it should be presented "
        "as one, and it is also the only number that makes the case for keeping a cost monitor "
        "running in a month where nothing went wrong."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="daily run",
 volumes=[(30, "30 runs"), (90, "3 accounts"), (300, "10 accounts")],
 read_each=0.0,
 msgs_each=0.4,
 extra=[("api", "Cost Explorer API requests", "#4A90D9", 0.01, 0.0)],
 lede=("A cost monitor that costs real money would be embarrassing, and this one does not: it "
       "makes a handful of API calls once a day. Thirty runs is one account watched daily. Here "
       "is where each cent goes."),
 takeaway_extra=("The Cost Explorer API is charged per request, which is the only unusual line "
                 "and is still pennies at one run a day."),
 risks=[
  "<strong>Querying Cost Explorer per service per day.</strong> The API charges per request, and "
  "a loop that asks separately for each of thirty services on each of three days is ninety "
  "requests a day rather than three. Group the query.",
  "<strong>Hourly cost queries.</strong> Tempting for faster detection and the wrong solution: "
  "the data does not update hourly, so it is ninety-six times the API cost for no additional "
  "signal. Use usage metrics for speed instead.",
  "<strong>Log retention left at never.</strong> With a bill this small, unbounded logs will be "
  "the majority of it within months.",
 ],
 per_unit_note=("The Cost Explorer API is one of the few AWS APIs charged per request. At one "
                "grouped query per day per account it is a few pence a month; at one query per "
                "service per day it is not."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ca",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the read-only posture, and the permissions it deliberately lacks."),
 outside=[
  {"title": "Cost Explorer", "sub": ["daily, grouped"], "icon": "money"},
  {"title": "CloudWatch metrics", "sub": ["the fast proxies"], "icon": "monitor"},
  {"title": "SES outbound", "sub": ["anomalies, monthly"], "icon": "email"}],
 inside=[
  {"title": "EventBridge", "sub": ["daily cost,", "hourly usage"], "icon": "clock"},
  {"title": "Lambda x3", "sub": ["fetch, compare,", "attribute"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["daily, resources"], "icon": "database"}],
 note="us-east-1. One account. No permission to stop, delete, scale or modify anything.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Cost Explorer, queried daily with grouped "
  "requests. CloudWatch metrics, supplying the fast usage proxies. And SES outbound, carrying "
  "anomaly messages and the monthly summary. Inside the account, three groups. EventBridge "
  "carrying a daily cost schedule and an hourly usage schedule. Three Lambda functions named "
  "fetch, compare and attribute. And two DynamoDB tables named daily and resources. A note gives "
  "the region as us-east-1, one account, and states there is no permission to stop, delete, "
  "scale or modify anything."),
 functions=[
  ["<code>ca-fetch</code>", "EventBridge daily 09:00",
   "One grouped Cost Explorer query for the last three days", "60s / 512&nbsp;MB"],
  ["<code>ca-compare</code>", "SQS fetched queue",
   "Money floor, step and ramp checks, new services and falls", "30s / 512&nbsp;MB"],
  ["<code>ca-attribute</code>", "SQS anomaly queue + EventBridge hourly",
   "Resource level, usage metrics, tags; the fast proxy checks", "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>ca-fetch-role</code>", "<code>ce:GetCostAndUsage</code>, <code>dynamodb:PutItem</code>",
   "Cost Explorer, read; the daily table"],
  ["<code>ca-compare-role</code>", "<code>dynamodb:Query</code>, <code>sqs:SendMessage</code>",
   "The daily table; the anomaly queue"],
  ["<code>ca-attribute-role</code>",
   "<code>ce:GetCostAndUsageWithResources</code>, <code>cloudwatch:GetMetricData</code>, "
   "<code>tag:GetResources</code>, <code>ses:SendEmail</code>",
   "Read-only across all three; one verified identity"]],
 tables=[
  ("Table: daily",
   "PK   service           S   AWSLambda\n"
   "SK   date              S   2026-08-02\n"
   "     amount            N   32.14\n"
   "     amount_provisional BOOL false  -- true until it has settled 3 days\n"
   "     day_of_week       N   2\n"
   "     first_seen        BOOL false   -- true on a service's first day\n"
   "     ttl               N   epoch, +120 days\n\n"
   "120 days is chosen for the ramp check, which compares a 7-day window\n"
   "against the 21 before it and wants a quarter of context around that."),
  ("Table: resources",
   "PK   service_date      S   AWSLambda#2026-08-02\n"
   "SK   resource          S   arn:...:function:image-resize\n"
   "     amount            N   31.02\n"
   "     usage_metric      S   Invocations\n"
   "     usage_value       N   400218\n"
   "     usage_normal      N   2010\n"
   "     tags              M   {owner: platform, env: prod}\n"
   "     untagged          BOOL false\n\n"
   "`usage_normal` is what makes the message a bug report. Without it the\n"
   "sentence is 'this function cost £31', which is an observation.")],
 inbound=[
  "<strong>One grouped Cost Explorer query per run</strong>, not one per service. The API is "
  "charged per request and a per-service loop multiplies the bill by thirty for identical data.",
  "<strong>Resource-level costs</strong> come from a separate, more expensive call made only for "
  "the services that actually moved &mdash; typically zero or one per day.",
  "<strong>Usage metrics</strong> are read hourly for three services only: Lambda invocations, "
  "S3 requests and NAT gateway bytes. Those three cover almost every runaway that can matter "
  "inside a day.",
  "<strong>No write permission anywhere.</strong> The execution roles have no "
  "<code>lambda:Delete</code>, no <code>ec2:Stop</code>, no <code>s3:Delete</code>. That is "
  "enforced by the policy rather than by the code not calling them."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Comparisons, projections and attribution "
  "are arithmetic and lookups.",
  "<strong>The tempting use</strong> is generating an explanation of a spike, which would produce "
  "a confident guess about a cause the data does not contain.",
  "<strong>The message is a template</strong> with the resource, the usage figures and the "
  "projection substituted, which also means it reads the same every time and gets scanned "
  "quickly.",
  "<strong>Stating two facts side by side</strong> &mdash; the invocation count and that the "
  "function writes where it is triggered from &mdash; lets a person recognise recursion without "
  "the system claiming it.",
  "<strong>The cost page assumes none</strong>, which is why the API requests are the only "
  "unusual line."],
 gotchas=[
  "Group the Cost Explorer query. It is charged per request, and a per-service loop is thirty "
  "times the cost for the same answer.",
  "Re-fetch the last three days. Yesterday's figure is provisional and a restatement will "
  "otherwise leave a wrong number in the baseline forever.",
  "Add the ramp check. A step change is easy and the expensive surprises are almost always "
  "something growing eight per cent a day that never trips a day-on-day comparison.",
  "Put a money floor in front of every relative test. A hundredfold increase on four pence is "
  "four pence.",
  "Do not grant write permissions, and say why in the policy. The next person to work on this "
  "will want to add remediation, and the reasoning should be somewhere they will find it."],
))
