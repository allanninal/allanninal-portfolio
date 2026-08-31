"""Day 113 -- 2026-08-15 -- Supplier lead time watcher."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "supplier-lead-time-watcher"
NAME = "Supplier lead time watcher"

SPEC = {
 "slug": SLUG, "date": "2026-08-15", "name": NAME,
 "tagline": ("Measures how long each supplier actually takes rather than how long they say they "
             "take, separates their delay from yours, and notices the slow drift that nobody "
             "sees until something runs out."),
 "lede": ("A small system that records when each purchase order was raised, approved, sent, "
          "acknowledged and received, works out the real distribution of lead times per supplier "
          "and product, and flags the gradual slippage that a promised lead time hides. It never "
          "switches supplier; it produces the evidence for a conversation. Seven posts on the "
          "same system, one diagram at a time, with a cost breakdown and an engineering reference "
          "at the end."),
 "keywords": ["lead time", "suppliers", "procurement", "stockouts", "inventory", "serverless"],
 "icons": ["truck", "clock", "chart"],
 "faq": [
  ("What is a supplier lead time watcher?",
   "A small serverless system that measures observed lead times from your own purchase order and "
   "receipt records, reports them as a distribution rather than an average, and flags suppliers "
   "whose times are drifting."),
  ("Why not just use the supplier's quoted lead time?",
   "Because it is a promise rather than a measurement, and reordering against it means running "
   "out whenever they are slower than usual, which is roughly half the time."),
  ("Why is an average the wrong number?",
   "Reordering on the average lead time produces a stockout on about half of orders. The number "
   "you want is a high percentile, and the post on this explains which."),
  ("Does it include our own delays?",
   "It measures them separately, which is the honest part. A week sitting in an approval queue is "
   "not the supplier's fault and should not appear in their number."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "supplier-lead-time-watcher-on-aws",
 "title": "A supplier lead time watcher on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Measures real supplier lead times, separates internal delay from external, and flags "
          "slippage before it causes a stockout. AWS, about $2 a month."),
 "og": ("The quoted lead time is a promise. The observed one is a distribution. Reordering "
        "against the promise is how businesses run out of things."),
 "abstract": ("The whole system on one page -- timestamps, distribution, drift -- and why the "
              "supplier's own number is the wrong input."),
 "lede": ("A supplier says five working days. The last eleven orders took four, five, five, six, "
          "five, nine, six, seven, twelve, eight and nine. Nobody noticed the second half of that "
          "list, the reorder point is still set for five days, and in about six weeks something "
          "is going to run out on a Friday. This post walks through a small system that notices "
          "on order seven."),
 "tags": ["lead time", "suppliers", "procurement", "stockouts", "inventory", "serverless"],
 "takeaways": [
  "Measure lead time from your own records, never from the supplier's quote.",
  "Separate internal delay (approval, sending) from external (supplier to door).",
  "Report a distribution and a high percentile, not an average.",
  "Drift matters more than any single late order.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Purchase orders", "sub": ["raised, approved, sent"], "icon": "doc"},
      {"title": "Goods received", "sub": ["dates and quantities"], "icon": "truck"},
      {"title": "Whoever reorders", "sub": ["needs a number"], "icon": "person"}],
    "inside": [
      {"title": "Clock", "sub": ["five timestamps,", "not two"], "icon": "clock"},
      {"title": "Distribution", "sub": ["per supplier,", "per product"], "icon": "chart"},
      {"title": "Drift watch", "sub": ["slow change,", "not one late order"], "icon": "search"}],
    "edges": [{"from": 0, "to": 0, "label": "PO timestamps"},
              {"from": 1, "to": 1, "label": "receipt dates"},
              {"from": 2, "to": 2, "label": "a percentile and a trend", "up": True}],
    "note": "Five timestamps rather than two is what separates their delay from ours."}),
   "Three things outside the account, three pieces inside it. The first box is the one that makes "
   "every later number attributable to somebody.",
   "System: purchase order timestamps turned into lead time distributions",
   "Three boxes across the top sit outside the AWS account. On the left, Purchase orders, with "
   "the dates they were raised, approved and sent. In the middle, Goods received, with dates and "
   "quantities. On the right, Whoever reorders, who needs a number. Each connects by an arrow to "
   "the AWS account container below. Purchase order timestamps flow down into the account. "
   "Receipt dates feed in. A percentile and a trend go back out. Inside the AWS account are three "
   "components in a row. On the left, the Clock, recording five timestamps rather than two. In "
   "the middle, the Distribution, computed per supplier and per product. On the right, the Drift "
   "watch, looking for slow change rather than one late order. A note at the bottom says five "
   "timestamps rather than two is what separates their delay from ours."),
  ("h3", "The number nobody should use"),
  ("p", "Every supplier has a quoted lead time, it appears on their website and in their terms, "
        "and it is a commercial statement rather than a measurement. It usually describes their "
        "best case, or their case in a normal month, or what they said three years ago when the "
        "relationship started."),
  ("p", "Meanwhile the business already has the real data: a purchase order with a date on it and "
        "a delivery note with a date on it, for every order ever placed. Nobody has ever "
        "subtracted one from the other systematically, and that subtraction is most of this "
        "system."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The clock.</strong> Records the five points in a purchase order's life and computes "
   "the segments between them. Part 2.",
   "<strong>The distribution.</strong> Builds the observed spread per supplier and product and "
   "reports the percentile that matters. Part 3.",
   "<strong>The drift watch.</strong> Detects gradual slippage against a small number of "
   "observations. Part 4.",
  ]),
  ("h2", "One purchase order, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Raised", "sub": ["1 Aug"], "icon": "form"},
      {"title": "Approved", "sub": ["5 Aug -- 4 days, ours"], "icon": "check"},
      {"title": "Sent", "sub": ["5 Aug"], "icon": "email"},
      {"title": "Acknowledged", "sub": ["6 Aug"], "icon": "doc"},
      {"title": "Received", "sub": ["14 Aug -- 9 days, theirs"], "icon": "truck"}],
    "title": "ONE PURCHASE ORDER, FIVE TIMESTAMPS",
    "note": "Thirteen days door to door. Four of them were us. That distinction is the system."}),
   "The same purchase order as one line. Without the middle three timestamps, this order is "
   "simply thirteen days late against a five-day promise, and the conversation goes badly.",
   "One purchase order measured at five points from raising to receipt",
   "A horizontal row of five boxes joined by arrows. Raised: first of August. Approved: fifth of "
   "August, four days, ours. Sent: fifth of August. Acknowledged: sixth of August. Received: "
   "fourteenth of August, nine days, theirs. A note says thirteen days door to door, four of them "
   "were us, and that distinction is the system."),
  ("h2", "In plain words"),
  ("p", "Somebody raises a purchase order on the first. It waits four days for approval because "
        "the person who signs is away. It goes to the supplier on the fifth, they acknowledge it "
        "on the sixth, and the goods arrive on the fourteenth."),
  ("p", "Thirteen days from raising to receiving. Nine from sending to receiving. Eight from "
        "acknowledgement to receiving. Which of those is the supplier's lead time depends on what "
        "you are going to do with the number, and having all three is what lets you answer both "
        "questions: how long does the supplier take, and how long does it take us to get "
        "something."),
  ("p", "The reorder point needs the thirteen, because that is reality. The supplier conversation "
        "needs the nine, because that is theirs. Conflating the two produces either a supplier "
        "meeting where you are wrong about the facts, or a reorder point that assumes approval is "
        "instantaneous."),
  ("callout", "Design rules that shaped every decision", [
   "Measure from your own records. The quoted lead time is an input to nothing.",
   "Five timestamps, so internal and external delay are separable.",
   "Working days, not calendar days, and the supplier's calendar where it differs.",
   "Report a percentile with the distribution beside it, never an average alone.",
   "Never automatically change a supplier or a reorder point. Produce evidence.",
   "Say the sample size next to every number. Four orders is not a distribution.",
 ]),
  ("h2", "Why this shape"),
  ("p", "Lead time problems are slow. A supplier does not go from five days to twelve overnight; "
        "they drift over a couple of quarters as their own supply chain tightens, and every "
        "individual order looks like a one-off. The failure is entirely one of memory, which is "
        "what makes it a good fit for a small system and a bad fit for a person."),
  ("p", "So the design is heavily weighted towards recording carefully and comparing over time, "
        "and deliberately does nothing automatic at the other end. A supplier relationship is not "
        "something to adjust with a threshold."),
  ("p", "The next four posts walk through each piece: how lead time actually gets measured, why "
        "the average is the wrong number, how slippage gets caught, and how it turns into a "
        "conversation. One diagram per post, a cost breakdown, and an engineering reference at "
        "the end."),
 ],
},
{
 "slug": "how-lead-time-actually-gets-measured",
 "title": "How lead time actually gets measured",
 "nav": "How it is measured",
 "read": 5, "words": 740,
 "desc": ("Where the clock starts and stops, separating internal delay, partial deliveries, and "
          "the calendar problem."),
 "og": ("A week in an approval queue is not the supplier's lead time. Measuring it as theirs "
        "makes every supplier conversation start from a false premise."),
 "abstract": ("The five timestamps and what each segment means, how partial deliveries are "
              "handled, why working days need the supplier's calendar, and the orders that must "
              "be excluded."),
 "lede": ("Lead time sounds like one number and is at least three, and the arguments about "
          "supplier performance are usually two people confidently quoting different segments of "
          "the same period."),
 "tags": ["lead time", "measurement", "purchase orders", "procurement", "logistics", "serverless"],
 "takeaways": [
  "Five timestamps: raised, approved, sent, acknowledged, received.",
  "The supplier's segment starts at sending, or at acknowledgement if you want to be generous.",
  "A partial delivery is measured to the point the order was usable, and the rule is stated.",
  "Working days need the supplier's calendar, not yours, when they are in another country.",
  "Exclude the orders that were never comparable: expedited, backordered, or changed mid-flight.",
 ],
 "blocks": [
  ("h2", "Five points and four segments"),
  ("fig", ("chain", {
    "entry": {"title": "A purchase order", "sub": ["through its life"], "icon": "doc"},
    "steps": [
      {"title": "Raised to approved", "sub": ["ours, entirely"], "icon": "clock",
       "side": {"title": "Internal", "sub": ["fixable by us"], "icon": "person"}},
      {"title": "Approved to sent", "sub": ["ours, and usually zero"], "icon": "clock"},
      {"title": "Sent to acknowledged", "sub": ["theirs -- responsiveness"], "icon": "email",
       "side": {"title": "A leading signal", "sub": ["it slips first"], "icon": "alarm"}},
      {"title": "Acknowledged to received", "sub": ["theirs -- fulfilment"], "icon": "truck"},
      {"title": "Raised to received", "sub": ["what stock planning needs"], "icon": "chart"}],
    "note": "The third segment slips before the fourth does, which makes it the early warning."}),
   "The four segments of a purchase order's life. The third one is the most useful and the one "
   "nobody records.",
   "The five purchase order timestamps and the four segments between them",
   "A vertical chain of five steps entered by a box labelled A purchase order through its life. "
   "Step one, raised to approved, is entirely ours, with a side note saying it is internal and "
   "fixable by us. Step two, approved to sent, is also ours and usually zero. Step three, sent to "
   "acknowledged, is theirs and measures responsiveness, with a side note saying it is a leading "
   "signal that slips first. Step four, acknowledged to received, is theirs and measures "
   "fulfilment. Step five, raised to received, is what stock planning needs. A note says the "
   "third segment slips before the fourth does, which makes it the early warning."),
  ("h3", "Acknowledgement is the early warning"),
  ("p", "A supplier under pressure gets slower at replying before they get slower at delivering, "
        "because the reply is what a stretched person deprioritises first. An order that used to "
        "be acknowledged the same day and now takes three is telling you something several weeks "
        "before the deliveries start slipping."),
  ("p", "It is also the cheapest timestamp to capture, because it is an email arriving. Most "
        "businesses have it and nobody records it."),
  ("h3", "Which segment is 'the' lead time"),
  ("p", "For talking to the supplier: sent to received, because that is the period they control. "
        "Using raised-to-received in that conversation means opening with a number that includes "
        "four days of your own approval queue, and the meeting is then about that."),
  ("p", "For setting a reorder point: raised to received, because the shelf does not care whose "
        "fault the delay was. Two numbers, two purposes, and confusing them is the most common "
        "error in this area."),
  ("h2", "The awkward cases"),
  ("table", ["Case", "How it is measured", "Why"], [
   ["Partial delivery", "To the date the ordered quantity was complete",
    "A tenth of an order arriving on time is not on time"],
   ["Substitution accepted", "Measured, and flagged as substituted",
    "It counts, but it is not the same product"],
   ["Backordered at their end", "Excluded from the distribution, counted separately",
    "It is a stock failure, not a lead time"],
   ["We expedited it", "Excluded", "It does not describe normal ordering"],
   ["We changed the order", "Clock restarts at the change", "It became a different order"],
   ["Damaged, replaced", "To the replacement's arrival", "The usable goods arrived then"],
  ]),
  ("p", "The exclusions matter as much as the measurements, because a distribution polluted with "
        "expedited orders looks better than reality and a distribution polluted with backorders "
        "looks worse. Both errors produce a number that fails at the moment somebody relies on "
        "it."),
  ("p", "What matters most is that the rules are written down and applied the same way every "
        "time. A supplier disputing a number is a productive conversation when the rule is "
        "stated, and an unwinnable one when it is not."),
  ("h2", "Calendars"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Sent Thursday", "sub": ["18:40"], "icon": "email"},
      {"title": "Their Friday", "sub": ["a public holiday"], "icon": "clock"},
      {"title": "Weekend", "sub": ["theirs, not ours"], "icon": "stop"},
      {"title": "Arrives Wednesday", "sub": ["6 calendar days"], "icon": "truck"},
      {"title": "2 working days", "sub": ["by their calendar"], "icon": "check"}],
    "title": "THE SAME ORDER, TWO ANSWERS",
    "note": "Six days looks bad. Two is what actually happened, and they will say so."}),
   "Why the supplier's calendar is needed. Counting in calendar days produces numbers that "
   "collapse the first time a supplier is asked to explain them.",
   "How a supplier's working calendar changes a measured lead time",
   "A horizontal row of five boxes. Sent Thursday at eighteen forty. Their Friday: a public "
   "holiday. Weekend: theirs, not ours. Arrives Wednesday: six calendar days. Two working days by "
   "their calendar. A note says six days looks bad, two is what actually happened, and they will "
   "say so."),
  ("p", "This sounds pedantic and it is the difference between a supplier review that lands and "
        "one where the supplier is correct and you are not. Their public holidays are a short "
        "list, entered once per supplier, and it removes an entire category of wrong number."),
  ("p", "The same applies to cut-off times. An order sent at twenty to seven on a Thursday was "
        "sent on Friday from the supplier's point of view, and a cut-off recorded per supplier "
        "makes that automatic rather than something somebody remembers to allow for."),
  ("p", "Next: which number to actually use."),
 ],
},
{
 "slug": "why-the-average-is-the-wrong-number",
 "title": "Why the average is the wrong number",
 "nav": "Why not the average",
 "read": 5, "words": 750,
 "desc": ("What reordering on the mean actually guarantees, which percentile to use instead, and "
          "why variance costs more than length."),
 "og": ("Reorder on the average lead time and you will run out on about half of orders. That is "
        "not a risk, it is arithmetic."),
 "abstract": ("Why an average lead time produces stockouts by construction, how to pick a "
              "percentile, why a long consistent supplier beats a short erratic one, and how to "
              "report the spread."),
 "lede": ("An average lead time is the number every system reports and it has a property nobody "
          "states out loud: half of all orders take longer than it. Setting a reorder point "
          "against it is a decision to run out roughly half the time."),
 "tags": ["lead time", "percentiles", "variance", "inventory", "statistics", "serverless"],
 "takeaways": [
  "The average is exceeded on about half of orders, by definition.",
  "Use a high percentile -- the 90th is a reasonable default for most goods.",
  "Variance costs more than length. A consistent 12 days beats an erratic 5-to-15.",
  "Report the spread next to the number, always.",
  "Say the sample size. Six orders does not have a 90th percentile worth the name.",
 ],
 "blocks": [
  ("h2", "What the average guarantees"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Reorder at the mean", "parts": [("ok", 52), ("out", 48)]},
      {"label": "Reorder at p75", "parts": [("ok", 76), ("out", 24)]},
      {"label": "Reorder at p90", "parts": [("ok", 91), ("out", 9)]},
      {"label": "Reorder at p95", "parts": [("ok", 96), ("out", 4)]}],
    "series": [("ok", "Orders that arrived in time, %", "#7AA116"),
               ("out", "Orders that arrived late, %", "#DD344C")],
    "unit": "",
    "note": "The first bar is what most reorder points are set to. It is a coin flip."}),
   "Four reorder points against the same supplier's real distribution. Moving from the mean to "
   "the ninetieth percentile costs a few days of extra stock and removes four fifths of the "
   "stockouts.",
   "Stockout rates at four different reorder point percentiles",
   "A stacked bar chart with four bars in per cent. Two series: orders that arrived in time in "
   "green, and orders that arrived late in red. Reordering at the mean gives fifty-two per cent "
   "in time and forty-eight per cent late. At the seventy-fifth percentile, seventy-six in time "
   "and twenty-four late. At the ninetieth, ninety-one in time and nine late. At the "
   "ninety-fifth, ninety-six in time and four late. A note says the first bar is what most "
   "reorder points are set to, and it is a coin flip."),
  ("h3", "Which percentile"),
  ("p", "The ninetieth is a sensible default and the right answer depends on what running out "
        "costs. For a cheap consumable with a substitute available, the seventy-fifth is fine and "
        "carrying less stock is worth the occasional gap. For the one component that stops a "
        "production line, the ninety-fifth or higher is cheap insurance."),
  ("p", "The useful framing when somebody has to choose is not statistical: how many times a year "
        "are you willing to run out of this, and what happens when you do? Twelve orders a year "
        "at the ninetieth percentile means running out about once a year, which is a sentence "
        "anybody can have an opinion about."),
  ("h2", "Variance costs more than length"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Supplier A", "sub": ["5 to 15 days, mean 9"], "icon": "truck", "label": "erratic"},
      {"title": "Supplier B", "sub": ["11 to 13 days, mean 12"], "icon": "truck",
       "label": "consistent"},
      {"title": "The reorder point", "sub": ["set at p90 for each"], "icon": "chart",
       "label": "what it costs"}],
    "target": {"title": "A holds more stock", "sub": ["p90 is 15 days,", "against B's 13"],
               "icon": "storage",
               "then": {"title": "The slower supplier", "sub": ["is the cheaper one"],
                        "icon": "money"}},
    "note": "A is three days faster on average and needs two more days of stock. Spread wins."}),
   "Two suppliers where the faster one costs more to buy from. The comparison people make is "
   "means; the comparison that matters is the high percentile.",
   "Why an erratic fast supplier costs more than a consistent slow one",
   "Three boxes stacked on the left. Supplier A, five to fifteen days with a mean of nine, "
   "labelled erratic. Supplier B, eleven to thirteen days with a mean of twelve, labelled "
   "consistent. And The reorder point, set at the ninetieth percentile for each, labelled what it "
   "costs. All three converge on A holds more stock, because A's ninetieth percentile is fifteen "
   "days against B's thirteen, and that leads down to The slower supplier is the cheaper one. A "
   "note says A is three days faster on average and needs two more days of stock, so spread wins."),
  ("p", "This is the finding that changes decisions, and it is invisible in every report that "
        "shows an average. Supplier A looks better on any dashboard comparing mean lead times and "
        "is more expensive to work with, because the stock you have to hold to absorb their "
        "unpredictability costs real money and warehouse space."),
  ("p", "The practical output is to report mean, ninetieth percentile and range together for "
        "every supplier, and to let the person doing the comparison see all three. It takes no "
        "more space than the average alone."),
  ("h3", "Reporting the spread"),
  ("p", "The compact form that works is the range with the count: \"9 days typical, 15 at the "
        "90th, range 5&ndash;15, from 22 orders\". Four pieces of information, one line, and it "
        "cannot be misread as a promise."),
  ("p", "The count at the end is doing real work. It is the difference between a number somebody "
        "should act on and a number that describes four orders and a coincidence."),
  ("h2", "Small samples"),
  ("fig", ("strip", {
    "stages": [
      {"title": "3 orders", "sub": ["no distribution"], "icon": "question"},
      {"title": "8 orders", "sub": ["a range, not a p90"], "icon": "counter"},
      {"title": "20 orders", "sub": ["p90 is meaningful"], "icon": "chart"},
      {"title": "Say which", "sub": ["on every number"], "icon": "doc"},
      {"title": "Use the worst", "sub": ["when n is small"], "icon": "shield"}],
    "title": "HOW MUCH HISTORY YOU NEED",
    "note": "Below about ten orders, the longest one you have seen is a better planning number."}),
   "What each sample size supports. The last box is the practical rule for the many suppliers you "
   "order from four times a year.",
   "How sample size determines which lead time number can be used",
   "A horizontal row of five boxes. Three orders: no distribution. Eight orders: a range, not a "
   "ninetieth percentile. Twenty orders: the ninetieth percentile is meaningful. Say which, on "
   "every number. Use the worst, when the sample is small. A note says below about ten orders, "
   "the longest one you have seen is a better planning number."),
  ("p", "Using the observed maximum for small samples is crude and it is honest, which beats a "
        "percentile computed from six data points and presented with the same confidence as one "
        "computed from sixty."),
  ("p", "It also degrades gracefully: as orders accumulate the number moves from the maximum to a "
        "real percentile, and it moves in the direction of holding less stock, which is the safe "
        "direction to be wrong in while you are learning."),
  ("p", "Next: catching the slide."),
 ],
},
{
 "slug": "how-slippage-gets-caught",
 "title": "How slippage gets caught",
 "nav": "How slippage is caught",
 "read": 5, "words": 730,
 "desc": ("Comparing recent orders against the established distribution, why one late order is "
          "not a signal, and the alert that is worth sending."),
 "og": ("One late order is noise. Four of the last six above the old ninetieth percentile is a "
        "supplier whose situation changed."),
 "abstract": ("How gradual drift is detected against a baseline, why single-order alerts train "
              "people to ignore alerts, what the acknowledgement segment shows first, and the "
              "seasonal confounder."),
 "lede": ("Slippage is the failure this system exists for. A single late delivery is visible to "
          "anybody; a supplier moving from six days to eleven over five months is visible to "
          "nobody, because every individual order was only a day or two worse than the last."),
 "tags": ["lead time", "drift detection", "alerts", "suppliers", "monitoring", "serverless"],
 "takeaways": [
  "Compare the recent window against the established baseline, not against the quote.",
  "One late order is never an alert. Several above the old p90 is.",
  "The acknowledgement segment drifts first and is the earliest usable signal.",
  "Check for a seasonal explanation before raising it as a change.",
  "The alert names the numbers and the orders, so the conversation starts with evidence.",
 ],
 "blocks": [
  ("h2", "Recent against baseline"),
  ("fig", ("chain", {
    "entry": {"title": "A delivery is received", "sub": ["lead time computed"], "icon": "truck"},
    "steps": [
      {"title": "Enough baseline?", "sub": ["12+ prior orders"], "icon": "branch",
       "exit": {"title": "Just record it", "sub": ["no comparison yet"], "icon": "database",
                "label": "no"}},
      {"title": "Above the old p90?", "sub": ["from the baseline period"], "icon": "branch",
       "exit": {"title": "Normal", "sub": ["nothing to say"], "icon": "check", "label": "no"}},
      {"title": "How many of the last 6?", "sub": ["also above it"], "icon": "counter"},
      {"title": "Three or more?", "sub": ["a pattern, not an event"], "icon": "branch",
       "exit": {"title": "Note it", "sub": ["watch, do not alert"], "icon": "search",
                "label": "no"}},
      {"title": "Seasonal?", "sub": ["same weeks last year"], "icon": "branch",
       "side": {"title": "Last year", "sub": ["same period"], "icon": "clock"},
       "exit": {"title": "Expected", "sub": ["annotated, not alerted"], "icon": "check",
                "label": "yes"}}],
    "note": "Four gates before anybody is told. An alert that fires on one late order is ignored."}),
   "How a drift alert is decided. Each gate removes a category of false alarm that would otherwise "
   "teach people to skip the email.",
   "How supplier lead time slippage is detected against a baseline",
   "A vertical chain of five steps entered by a box labelled A delivery is received and its lead "
   "time computed. Step one asks whether there is enough baseline, twelve or more prior orders; "
   "if not it exits to Just record it, with no comparison yet. Step two asks whether it is above "
   "the old ninetieth percentile from the baseline period; if not it exits to Normal, nothing to "
   "say. Step three counts how many of the last six were also above it. Step four asks whether "
   "that is three or more, a pattern rather than an event; if not it exits to Note it, watch but "
   "do not alert. Step five asks whether it is seasonal by comparing the same weeks last year, "
   "drawing on a side box for last year's same period; if so it exits to Expected, annotated "
   "rather than alerted. A note says four gates fire before anybody is told, and an alert that "
   "fires on one late order is ignored."),
  ("h3", "Why the baseline is frozen"),
  ("p", "The comparison has to be against a fixed earlier period rather than a rolling window, "
        "because a rolling window absorbs the drift. A supplier sliding from six days to eleven "
        "over five months never looks unusual against their own last three months, which is "
        "precisely the failure mode this is supposed to catch."),
  ("p", "So the baseline is the distribution from a stated earlier period &mdash; the previous "
        "twelve months, or the twelve months before the drift was last acknowledged &mdash; and "
        "it is re-based deliberately by a person rather than automatically."),
  ("h2", "The signal that arrives first"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Jan-Mar", "parts": [("ack", 1), ("fulfil", 5)]},
      {"label": "Apr-Jun", "parts": [("ack", 2), ("fulfil", 5)]},
      {"label": "Jul-Sep", "parts": [("ack", 4), ("fulfil", 6)]},
      {"label": "Oct-Dec", "parts": [("ack", 4), ("fulfil", 9)]}],
    "series": [("ack", "Sent to acknowledged, days", "#ED7100"),
               ("fulfil", "Acknowledged to received, days", "#8C4FFF")],
    "unit": "",
    "note": "The orange band doubled two quarters before the purple one moved at all."}),
   "One supplier over a year, split into the two segments they control. The acknowledgement delay "
   "is the leading indicator and it is free to measure.",
   "A supplier's acknowledgement and fulfilment delays over four quarters",
   "A stacked bar chart with four bars measured in days. Two series: sent to acknowledged in "
   "orange, and acknowledged to received in purple. January to March shows one day to acknowledge "
   "and five to fulfil. April to June shows two and five. July to September shows four and six. "
   "October to December shows four and nine. A note says the orange band doubled two quarters "
   "before the purple one moved at all."),
  ("p", "A supplier taking four days to acknowledge an order when they used to take one is "
        "usually short-staffed, and short-staffed becomes late deliveries a quarter or two later. "
        "It is the cheapest early warning available and it comes from an email timestamp."),
  ("p", "It is also a much easier conversation to open. \"We have noticed acknowledgements taking "
        "longer &mdash; is everything all right at your end?\" is a supportive question that "
        "often produces useful information, where \"you have been late four times\" is an "
        "accusation that produces a defence."),
  ("h3", "The seasonal check"),
  ("p", "A lot of apparent drift is the same slowdown that happened last year. Checking the "
        "equivalent weeks in the previous year before alerting removes the most common false "
        "positive, and where there is no previous year the alert says so rather than pretending "
        "to have checked."),
  ("h2", "What the alert says"),
  ("callout", "The whole notification", [
   "<strong>Supplier:</strong> Hartley Components. <strong>Product:</strong> 4mm bearing "
   "housing.",
   "<strong>Baseline:</strong> 6 days typical, 8 at the 90th, from 31 orders across 2025.",
   "<strong>Last six orders:</strong> 8, 11, 9, 12, 9, 13 days. Four above the old 90th.",
   "<strong>Acknowledgement:</strong> also up, from 1 day to 4.",
   "<strong>Not seasonal:</strong> the same weeks last year averaged 6 days.",
   "<strong>Effect if unchanged:</strong> the reorder point for this part should move from 8 days "
   "to 13.",
  ]),
  ("p", "Six lines, all of them facts, and the last one is the sentence that makes it actionable. "
        "An alert that reports a change without saying what it means for what somebody has to do "
        "gets filed rather than acted on."),
  ("p", "Note what the alert does not do: it does not change the reorder point, it does not "
        "suggest a different supplier, and it does not assign a rating. Those are all decisions, "
        "and the next post is about why they stay with a person."),
  ("p", "Next: turning a number into a conversation."),
 ],
},
{
 "slug": "how-it-turns-into-a-conversation",
 "title": "How it turns into a conversation",
 "nav": "How it becomes a conversation",
 "read": 5, "words": 720,
 "desc": ("Why nothing is automated at this end, the supplier scorecard problem, and showing your "
          "own delay first."),
 "og": ("Opening a supplier review by admitting your own four-day approval queue changes the "
        "entire meeting. The data supports it either way."),
 "abstract": ("Why no supplier decision is automated, what a scorecard does to a relationship, "
              "why showing internal delay first works, and the annual review this makes possible."),
 "lede": ("Everything up to here is measurement, and measurement is the easy half. What a "
          "business does with an accurate lead time number determines whether the supplier "
          "relationship gets better or gets formal, and those are very different outcomes."),
 "tags": ["suppliers", "relationships", "procurement", "scorecards", "reviews", "serverless"],
 "takeaways": [
  "Nothing about a supplier changes automatically. The system produces evidence, not decisions.",
  "Show your own internal delay first and the conversation changes shape.",
  "A scorecard with a grade produces defensiveness; a distribution produces explanations.",
  "Ask what changed before asserting that something did.",
  "The best output is often a changed reorder point, not a changed supplier.",
 ],
 "blocks": [
  ("h2", "Nothing is automatic"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Drift detected", "sub": ["with evidence"], "icon": "search"},
      {"title": "No auto-reorder change", "sub": ["a person decides"], "icon": "stop"},
      {"title": "No auto-switch", "sub": ["obviously"], "icon": "stop"},
      {"title": "No rating", "sub": ["no A to F grade"], "icon": "stop"},
      {"title": "A conversation", "sub": ["with numbers in it"], "icon": "person"}],
    "title": "WHAT THE SYSTEM DOES NOT DO",
    "note": "Three refusals and one output. The refusals are what make the output credible."}),
   "The deliberate limits. Each of the three middle boxes is a feature somebody will request and "
   "each would make the system worse.",
   "The three supplier actions this system deliberately does not automate",
   "A horizontal row of five boxes. Drift detected, with evidence. No automatic reorder point "
   "change: a person decides. No automatic supplier switch, obviously. No rating: no A to F "
   "grade. A conversation, with numbers in it. A note says three refusals and one output, and the "
   "refusals are what make the output credible."),
  ("h3", "Why not change the reorder point automatically"),
  ("p", "It looks like the obvious win and it is the one to resist hardest, because a reorder "
        "point that moves on its own means the amount of cash tied up in stock moves on its own. "
        "A quiet three-day increase across forty products is a significant working capital change "
        "that nobody approved."),
  ("p", "The system proposes it &mdash; \"this should move from 8 days to 13\" &mdash; and "
        "somebody accepts it in one click. That is nearly as fast and it leaves a decision with a "
        "name on it."),
  ("h2", "Show your own delay first"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "As usually presented", "parts": [("theirs", 13)]},
      {"label": "As measured", "parts": [("ours", 4), ("theirs", 9)]}],
    "series": [("ours", "Our approval queue, days", "#ED7100"),
               ("theirs", "Supplier, sent to received", "#8C4FFF")],
    "unit": "",
    "note": "The left bar is the number that gets quoted in meetings. It is not true."}),
   "The same thirteen days, presented two ways. Walking into a supplier review with the left bar "
   "is how a review becomes an argument about facts.",
   "A thirteen day lead time shown as one number and as its two parts",
   "A bar chart with two bars measured in days. Two series: our approval queue in orange, and the "
   "supplier's sent-to-received period in purple. The first bar, as usually presented, shows "
   "thirteen days all attributed to the supplier. The second bar, as measured, shows four days of "
   "our approval queue and nine days of supplier time. A note says the left bar is the number "
   "that gets quoted in meetings, and it is not true."),
  ("p", "Opening a supplier review with \"our approval process is adding four days and we are "
        "fixing that\" does two things. It establishes that the numbers are honest, which makes "
        "the rest of them harder to dispute, and it changes the register of the meeting from "
        "complaint to shared problem."),
  ("p", "It is also frequently the more valuable finding. Four days of internal queue on every "
        "order is entirely within your control and is often larger than the supplier drift that "
        "prompted the analysis."),
  ("h3", "The scorecard problem"),
  ("p", "Supplier scorecards with letter grades are common and they reliably produce the same "
        "response: the supplier optimises for the grade. Lead time is easy to improve by quoting "
        "longer and delivering to the quote, which improves the score and makes the actual "
        "situation slightly worse."),
  ("p", "A distribution does not have that property, because there is no target to hit. \"Your "
        "typical is nine days and your worst quarter was thirteen\" is a description, and the "
        "natural response to a description is an explanation rather than a countermeasure."),
  ("h2", "Ask what changed"),
  ("callout", "How the conversation opens", [
   "<strong>\"Our numbers show your lead times moved from about six days to about eleven over "
   "this year.\"</strong> State it, with the count of orders behind it.",
   "<strong>\"Four days of the total is our approval queue, and we are dealing with that.\"</strong> "
   "Before anything else.",
   "<strong>\"Has something changed at your end?\"</strong> A question, and a genuine one.",
   "<strong>Then listen.</strong> The answer is frequently a specific thing &mdash; a supplier of "
   "theirs, a machine, a person who left &mdash; and frequently temporary.",
   "<strong>Agree what to plan for,</strong> not what to promise. A supplier who says eleven days "
   "honestly is more useful than one who says six and means it.",
  ]),
  ("p", "That last point is the one worth carrying away. The goal of the conversation is not to "
        "get the lead time back down; it is to find out what number to plan against. A supplier "
        "who tells you the truth about eleven days lets you set a reorder point that works, which "
        "is worth more than a promise of six that fails a third of the time."),
  ("h3", "The annual review this makes possible"),
  ("p", "Once a couple of years of this exists, the yearly supplier conversation becomes a "
        "different thing: here is every order, here is the distribution, here is how it moved, "
        "here is what we plan against. Most businesses cannot have that conversation because "
        "nobody wrote the dates down."),
  ("p", "It also makes the occasional decision to change supplier defensible, which is the only "
        "context in which that decision should ever be made from this data &mdash; slowly, with "
        "two years of evidence, by a person who knows what else the relationship is worth."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="purchase order",
 volumes=[(80, "80 orders"), (300, "300 orders"), (1200, "1,200 orders")],
 read_each=0.0,
 msgs_each=0.08,
 lede=("There is no model in this system and almost nothing is sent: a drift alert fires for a "
       "supplier a few times a year, not per order. Three hundred purchase orders a month is a "
       "busy small manufacturer. Here is where each cent goes."),
 takeaway_extra=("Alerts are rare by design, so messaging barely registers at any volume."),
 risks=[
  "<strong>Recomputing every distribution nightly.</strong> A distribution changes when an order "
  "is received. Compute on receipt, not on a schedule.",
  "<strong>Alerting on single late orders.</strong> Not a cost problem but the reason a system "
  "like this gets muted, after which it costs the same and does nothing.",
  "<strong>Copying the purchase order table.</strong> This reads records that already exist. A "
  "second copy is cost plus a synchronisation problem.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. The messaging band assumes a "
                "handful of drift alerts a month across the whole supplier base."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="lt",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the calendar handling, and how the baseline is frozen."),
 outside=[
  {"title": "Purchase orders", "sub": ["five timestamps"], "icon": "doc"},
  {"title": "Goods receipts", "sub": ["dates and quantities"], "icon": "truck"},
  {"title": "Alerts and reports", "sub": ["a few a month"], "icon": "chart"}],
 inside=[
  {"title": "EventBridge + API", "sub": ["on receipt,", "report on request"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["measure, distribute, watch"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["observations, baselines"], "icon": "database"}],
 note="us-east-1. One account. Baselines are frozen and re-based only by a named person.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Purchase orders, carrying five timestamps. "
  "Goods receipts, with dates and quantities. And Alerts and reports, a few a month. Inside the "
  "account, three groups. EventBridge firing on receipt and an API serving reports on request. "
  "Three Lambda functions named measure, distribute and watch. And two DynamoDB tables named "
  "observations and baselines. A note gives the region as us-east-1, one account, and states that "
  "baselines are frozen and re-based only by a named person."),
 functions=[
  ["<code>lt-measure</code>", "Goods receipt event",
   "Computes the four segments in the supplier's working days; applies exclusion rules",
   "30s / 512&nbsp;MB"],
  ["<code>lt-distribute</code>", "DynamoDB stream on observations",
   "Rebuilds the current distribution for that supplier and product", "60s / 1024&nbsp;MB"],
  ["<code>lt-watch</code>", "DynamoDB stream on observations",
   "Runs the four drift gates against the frozen baseline; sends at most one alert per "
   "supplier-product per month", "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>lt-measure-role</code>", "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "Read-only on purchase orders; writes observations"],
  ["<code>lt-distribute-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>",
   "Observations and baselines"],
  ["<code>lt-watch-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "Read-only; one verified identity"]],
 tables=[
  ("Table: observations",
   "PK   supplier#sku      S   hartley#brg-4mm\n"
   "SK   received_at       S   2026-08-14\n"
   "     raised_at         S   2026-08-01\n"
   "     approved_at       S   2026-08-05\n"
   "     sent_at           S   2026-08-05T18:40:00Z\n"
   "     acknowledged_at   S   2026-08-06\n"
   "     internal_days     N   4    -- raised to sent\n"
   "     ack_days          N   1    -- sent to acknowledged\n"
   "     fulfil_days       N   8    -- acknowledged to received\n"
   "     total_days        N   13   -- raised to received\n"
   "     excluded          S   null | expedited | backorder | amended\n"
   "     partial           BOOL true if measured to completion of quantity\n\n"
   "All day counts are the supplier's working days, using their calendar\n"
   "and cut-off. `excluded` rows are stored and left out of distributions."),
  ("Table: baselines",
   "PK   supplier#sku      S\n"
   "     period            S   2025-01-01..2025-12-31 -- frozen, stated\n"
   "     n                 N   31\n"
   "     median_days       N   6\n"
   "     p90_days          N   8\n"
   "     min_days          N   4\n"
   "     max_days          N   11\n"
   "     ack_median_days   N   1\n"
   "     rebased_by        S   a named person\n"
   "     rebased_at        S\n\n"
   "A rolling baseline would absorb the drift it exists to detect, which\n"
   "is why re-basing is a deliberate act with a name attached.")],
 inbound=[
  "<strong>Purchase orders are read, never written.</strong> This system has no write access to "
  "the purchasing system at all.",
  "<strong>Acknowledgement timestamps</strong> come from the supplier's reply landing in a "
  "mailbox. It is the cheapest signal here and the most useful.",
  "<strong>Supplier calendars and cut-offs</strong> are per-supplier configuration, entered once. "
  "Without them, every measurement is disputable.",
  "<strong>Exclusion rules run at measurement time</strong> and store the reason, so a "
  "distribution can always be explained by pointing at what was left out."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Everything here is date arithmetic and "
  "percentiles over small samples.",
  "<strong>The tempting use</strong> is forecasting the next lead time. At twenty observations "
  "per supplier-product, a forecast adds confidence and no information over the observed "
  "percentile.",
  "<strong>A second tempting use</strong> is classifying why a supplier slipped. The answer comes "
  "from asking them, and Part 5 is about why that conversation is the output.",
  "<strong>Reading acknowledgement emails</strong> to extract a promised date is a defensible "
  "use, and the promised date is stored as a separate field from the observed one, never merged.",
  "<strong>The cost page assumes none</strong>, which is why the whole bill is fixed."],
 gotchas=[
  "Freeze the baseline. A rolling comparison window makes slow drift invisible, which is the one "
  "failure this system exists to prevent.",
  "Use the supplier's working calendar and cut-off time. Otherwise the first supplier who "
  "disputes a number will be right.",
  "Store excluded observations rather than discarding them. \"Why is this order not in the "
  "figures\" needs an answer.",
  "Report the sample count next to every percentile. A p90 from six orders and one from sixty "
  "look identical on a dashboard and mean different things.",
  "Propose reorder point changes; never apply them. A silent working capital change across forty "
  "products is nobody's decision."],
))
