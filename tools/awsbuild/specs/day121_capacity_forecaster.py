"""Day 121 -- 2026-08-23 -- Capacity forecaster."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "capacity-forecaster"
NAME = "Capacity forecaster"

SPEC = {
 "slug": SLUG, "date": "2026-08-23", "name": NAME,
 "tagline": ("Forecasts whether there will be enough people, machines or hours to meet demand -- "
             "far enough ahead to do something about it, against the capacity you actually have "
             "rather than the one on paper."),
 "lede": ("A small system that measures real capacity, forecasts demand against it, and answers "
          "the only question that matters: will we be short, and is there still time to fix it? A "
          "forecast with a shorter horizon than your hiring lead time is decoration, and the "
          "post on that is the important one. Seven posts on the same system, one diagram at a "
          "time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["capacity planning", "forecasting", "operations", "bottlenecks", "scheduling",
              "serverless"],
 "icons": ["chart", "counter", "clock"],
 "faq": [
  ("What is a capacity forecaster?",
   "A small serverless system that measures actual available capacity, projects demand against "
   "it, and flags where a shortfall is coming while there is still time to act."),
  ("Why is paper capacity wrong?",
   "Because it assumes full attendance, no breakdowns, no setup time and no rework. Real "
   "available capacity is typically a good deal lower and the gap is measurable."),
  ("Why forecast the peak instead of the average?",
   "Because you do not run out of capacity on an average week. The average tells you whether the "
   "business is viable; the peak tells you when you will fail to deliver."),
  ("How far ahead should a forecast run?",
   "At least as far as the lead time to add capacity. A four-week forecast in a business where "
   "hiring takes twelve weeks cannot change any decision."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "capacity-forecaster-on-aws",
 "title": "A capacity forecaster on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Measures real capacity, forecasts demand against it, and flags shortfalls while there "
          "is still time. AWS, about $2 a month."),
 "og": ("A forecast that arrives after the point where you could have done something is a "
        "description, not a forecast."),
 "abstract": ("The whole system on one page -- capacity, demand, gap &mdash; and the lead time "
              "that determines whether any of it is useful."),
 "lede": ("In November somebody notices that January is going to be difficult. The busy period "
          "runs from the middle of January, hiring and training a fitter takes ten weeks, and "
          "November plus ten weeks is the end of January. The problem was visible in the order "
          "book in August. This post walks through a small system that would have said so then."),
 "tags": ["capacity planning", "forecasting", "operations", "bottlenecks", "scheduling",
          "serverless"],
 "takeaways": [
  "Measure the capacity you have, not the one on the org chart.",
  "Forecast the peak, not the average. You do not run out on an average week.",
  "The horizon must exceed the lead time to add capacity, or nothing can change.",
  "Record every forecast so it can be scored against what happened.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "What we can do", "sub": ["hours actually", "available"], "icon": "counter"},
      {"title": "What is coming", "sub": ["orders, bookings,", "seasonality"], "icon": "form"},
      {"title": "Whoever can act", "sub": ["with enough notice"], "icon": "person"}],
    "inside": [
      {"title": "Capacity", "sub": ["measured, not", "assumed"], "icon": "gauge"},
      {"title": "Demand", "sub": ["with a range,", "not a number"], "icon": "chart"},
      {"title": "The gap", "sub": ["when, how big,", "how confident"], "icon": "search"}],
    "edges": [{"from": 0, "to": 0, "label": "actual output"},
              {"from": 1, "to": 1, "label": "the pipeline"},
              {"from": 2, "to": 2, "label": "a dated warning", "up": True}],
    "note": "The output is a date and a size. Anything vaguer than that cannot be acted on."}),
   "Three things outside the account, three pieces inside it. The output on the right is "
   "deliberately narrow: a week, a shortfall, and a confidence.",
   "System: capacity measured, demand forecast, the gap reported",
   "Three boxes across the top sit outside the AWS account. On the left, What we can do: hours "
   "actually available. In the middle, What is coming: orders, bookings and seasonality. On the "
   "right, Whoever can act, with enough notice. Each connects by an arrow to the AWS account "
   "container below. Actual output flows down into the account. The pipeline feeds in. A dated "
   "warning goes back out. Inside the AWS account are three components in a row. On the left, "
   "Capacity, measured rather than assumed. In the middle, Demand, expressed as a range rather "
   "than a number. On the right, The gap: when, how big and how confident. A note at the bottom "
   "says the output is a date and a size, and anything vaguer than that cannot be acted on."),
  ("h3", "Two things most forecasts get wrong"),
  ("p", "The first is using paper capacity. Six fitters at forty hours is two hundred and forty "
        "hours, and the real figure after holiday, sickness, training, setup, rework and the "
        "meeting on Thursday is a good deal lower. Forecasting demand against a number that has "
        "never been achieved produces a forecast that says everything is fine right up until it "
        "is not."),
  ("p", "The second is forecasting the average. An average week has enough capacity in almost "
        "every business that is still trading. The weeks that matter are the busy ones, and a "
        "forecast of the mean says nothing about them."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Capacity.</strong> Measures what was actually produced or delivered per period, "
   "rather than what should have been. Part 2.",
   "<strong>Demand.</strong> Projects the pipeline forward with a range, including the "
   "seasonality that is usually the whole story. Part 3.",
   "<strong>The gap.</strong> Where the two cross, how far ahead, and whether that is enough "
   "notice. Parts 4 and 5.",
  ]),
  ("h2", "One shortfall, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Real capacity", "sub": ["182 hrs/week, measured"], "icon": "gauge"},
      {"title": "Demand rising", "sub": ["from the order book"], "icon": "chart"},
      {"title": "Crosses in week 4", "sub": ["of January"], "icon": "alarm"},
      {"title": "Flagged in August", "sub": ["22 weeks ahead"], "icon": "clock"},
      {"title": "Lead time 10 weeks", "sub": ["still actionable"], "icon": "check"}],
    "title": "ONE SHORTFALL, END TO END",
    "note": "The fifth box is the test. A warning inside the lead time is just bad news."}),
   "The same system as one line. The comparison in the last box is what distinguishes a forecast "
   "from a report.",
   "One capacity shortfall detected twenty-two weeks ahead",
   "A horizontal row of five boxes joined by arrows. Real capacity: one hundred and eighty-two "
   "hours a week, measured. Demand rising, from the order book. Crosses in week four of January. "
   "Flagged in August, twenty-two weeks ahead. Lead time ten weeks: still actionable. A note says "
   "the fifth box is the test, and a warning inside the lead time is just bad news."),
  ("h2", "In plain words"),
  ("p", "The workshop's paper capacity is two hundred and forty hours a week. Measured over a "
        "year, actual productive output averages a hundred and eighty-two, and the difference is "
        "holiday, sickness, setup between jobs, and rework. A hundred and eighty-two is the "
        "number to forecast against."),
  ("p", "The order book, projected forward with the seasonal pattern from the last three years, "
        "crosses that line in the fourth week of January and stays above it for six weeks. The "
        "shortfall peaks at about forty hours a week."),
  ("p", "That finding lands in August, twenty-two weeks ahead. Hiring and training a fitter takes "
        "ten weeks, so there is time to hire, or to book contract capacity, or to talk to two "
        "customers about moving delivery dates. Any of those is a decision; the forecast just "
        "makes sure it is a decision rather than a discovery."),
  ("callout", "Design rules that shaped every decision", [
   "Capacity is measured from output, not calculated from headcount.",
   "Demand is a range, and the range widens with distance.",
   "The horizon is set by the longest lead time to add capacity.",
   "Every forecast is stored so it can be scored against what happened.",
   "Never propose the action. Report the gap and the date.",
   "Say the confidence, and say what would change the answer.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Capacity forecasting has a reputation for being either trivial or impossible, and both "
        "reputations come from the same source: a forecast that is not tied to a decision. A "
        "chart of projected utilisation with no date, no lead time and no confidence is a thing "
        "people look at and nod about."),
  ("p", "The version that works answers one question with three numbers: which week, how short, "
        "and how sure. Everything in this design is oriented at producing those three, early "
        "enough for them to matter."),
  ("p", "The next four posts walk through each piece: how real capacity gets measured, why the "
        "peak matters more than the average, how far ahead is worth forecasting, and how a "
        "forecast gets scored afterwards. One diagram per post, a cost breakdown, and an "
        "engineering reference at the end."),
 ],
},
{
 "slug": "how-the-real-capacity-gets-measured",
 "title": "How the real capacity gets measured",
 "nav": "How capacity is measured",
 "read": 5, "words": 750,
 "desc": ("Paper hours against delivered hours, what the gap is made of, and the bottleneck that "
          "moves."),
 "og": ("Six people at forty hours is not two hundred and forty hours of output, and the gap is "
        "measurable rather than arguable."),
 "abstract": ("Why capacity must be measured from output, what accounts for the gap between paper "
              "and actual, how the bottleneck is identified, and why it moves."),
 "lede": ("The number everybody uses for capacity is headcount multiplied by hours, and it has "
          "never once been achieved. Measuring what actually gets delivered is both easy and "
          "uncomfortable."),
 "tags": ["capacity planning", "measurement", "bottlenecks", "operations", "utilisation",
          "serverless"],
 "takeaways": [
  "Measure delivered output per period over a year; that is your capacity.",
  "The gap is holiday, sickness, setup, rework and everything unbookable.",
  "Do not try to eliminate the gap in the forecast. Forecast against reality.",
  "Identify the bottleneck by which stage has the least headroom.",
  "The bottleneck moves with the product mix, so re-check it.",
 ],
 "blocks": [
  ("h2", "Where the hours go"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Paper", "parts": [("out", 240)]},
      {"label": "Measured", "parts": [("out", 182), ("hol", 22), ("set", 20), ("rew", 16)]}],
    "series": [("out", "Delivered productive hours", "#7AA116"),
               ("hol", "Holiday, sickness, training", "#8C4FFF"),
               ("set", "Setup, changeover, waiting", "#ED7100"),
               ("rew", "Rework and unbooked time", "#DD344C")],
    "unit": "",
    "note": "The green bar is your capacity. The other three are real and are not going away."}),
   "Paper capacity against measured capacity for the same team. The three coloured bands are the "
   "difference and each of them is a normal part of operating.",
   "Paper capacity against measured capacity for one team",
   "A stacked bar chart with two bars in hours per week. Four series: delivered productive hours "
   "in green, holiday sickness and training in purple, setup changeover and waiting in orange, "
   "and rework and unbooked time in red. Paper capacity is two hundred and forty hours, all "
   "counted as delivered. Measured capacity is one hundred and eighty-two delivered, plus "
   "twenty-two hours of holiday and sickness, twenty hours of setup, and sixteen hours of rework. "
   "A note says the green bar is your capacity, and the other three are real and are not going "
   "away."),
  ("p", "The temptation on seeing that chart is to treat the coloured bands as waste to be "
        "eliminated, and some of it is. But the forecast has to be built on what actually "
        "happens, not on what would happen after an improvement programme that has not been done."),
  ("p", "The two questions are separate and both worth asking. What will we deliver next January "
        "uses a hundred and eighty-two. Whether a hundred and eighty-two could be a hundred and "
        "ninety-five is an improvement project with its own timescale and its own uncertainty."),
  ("h3", "Measuring output, not effort"),
  ("p", "Capacity is measured in whatever unit the business already tracks: jobs completed, "
        "hours billed, units produced, appointments delivered. The important property is that it "
        "comes from something already recorded rather than from a new timekeeping exercise "
        "nobody will sustain."),
  ("p", "A year of that data, expressed per week, gives both the average and the spread, and the "
        "spread matters as much as the level. A team that delivers between a hundred and sixty "
        "and two hundred hours depending on the week is planning against a different number from "
        "one that reliably delivers a hundred and eighty-two."),
  ("h2", "The bottleneck"),
  ("fig", ("chain", {
    "entry": {"title": "The work has stages", "sub": ["quote, build, test, ship"], "icon": "route"},
    "steps": [
      {"title": "Capacity at each", "sub": ["measured separately"], "icon": "counter"},
      {"title": "Demand at each", "sub": ["not the same everywhere"], "icon": "chart"},
      {"title": "Least headroom?", "sub": ["that is the constraint"], "icon": "branch"},
      {"title": "Forecast against it", "sub": ["the others do not bind"], "icon": "search"},
      {"title": "Re-check quarterly", "sub": ["it moves"], "icon": "clock",
       "side": {"title": "Why", "sub": ["the product mix changes"], "icon": "form"}}],
    "note": "Adding capacity anywhere except the constraint changes nothing at all."}),
   "How the constraint is identified. The last box is the one that gets skipped, and a "
   "bottleneck analysis from two years ago is often describing a stage that is no longer the "
   "problem.",
   "How the constraining stage in a process is identified",
   "A vertical chain of five steps entered by a box labelled The work has stages: quote, build, "
   "test and ship. Step one measures capacity at each stage separately. Step two measures demand "
   "at each, which is not the same everywhere. Step three asks which has the least headroom, and "
   "that is the constraint. Step four forecasts against it, since the others do not bind. Step "
   "five re-checks quarterly because it moves, with a side box explaining that the product mix "
   "changes. A note says adding capacity anywhere except the constraint changes nothing at all."),
  ("h3", "The bottleneck moves"),
  ("p", "This is the part that makes capacity forecasting harder than it looks. A workshop "
        "constrained by fitting hours becomes constrained by testing when the product mix shifts "
        "towards something that needs more testing, and the forecast built against fitting hours "
        "stops predicting anything."),
  ("p", "The practical response is to forecast against every stage rather than only the current "
        "constraint, and to report which one binds first. That is barely more work and it catches "
        "the case where a stage that has never been a problem becomes one."),
  ("h3", "Capacity that is not people"),
  ("p", "The same method applies to machines, vehicles, rooms, bays and ovens, and for those the "
        "gap between paper and actual has different components: breakdowns, changeover, cleaning, "
        "and maintenance from Day 118. A machine available a hundred and sixty-eight hours a week "
        "on paper is available considerably fewer in practice, and the deferred maintenance debt "
        "is one of the reasons."),
  ("p", "Where the constraint is a machine, the lead time to add capacity is a purchase and an "
        "installation rather than a hire, which is usually longer, which makes the horizon "
        "question in Part 4 more acute rather than less."),
  ("p", "Next: why the average is the wrong thing to forecast."),
 ],
},
{
 "slug": "why-the-peak-matters-more-than-the-average",
 "title": "Why the peak matters more than the average",
 "nav": "Peak, not average",
 "read": 5, "words": 730,
 "desc": ("Where a business actually runs out, forecasting a range rather than a line, and the "
          "week that breaks everything."),
 "og": ("Nobody fails to deliver on an average week. The forecast has to be about the weeks that "
        "are not average."),
 "abstract": ("Why average utilisation hides shortfalls, how a range is produced instead of a "
              "point, why seasonality usually dominates, and how the peak is expressed."),
 "lede": ("A business running at seventy per cent average utilisation sounds comfortable and "
          "misses deliveries eight weeks a year, because the seventy per cent is made of "
          "forty-per-cent weeks and hundred-and-twenty-per-cent weeks."),
 "tags": ["capacity planning", "forecasting", "peaks", "seasonality", "uncertainty", "serverless"],
 "takeaways": [
  "Average utilisation of seventy per cent routinely contains weeks above a hundred.",
  "Forecast a range: a likely case and a busy case, both dated.",
  "Seasonality usually explains more than trend at a one-year horizon.",
  "Work that can be moved between weeks softens a peak; work that cannot does not.",
  "Express the answer as weeks over capacity, not as average utilisation.",
 ],
 "blocks": [
  ("h2", "The average hides it"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Wk 1", "parts": [("used", 120)]},
      {"label": "Wk 2", "parts": [("used", 168)]},
      {"label": "Wk 3", "parts": [("used", 210)]},
      {"label": "Wk 4", "parts": [("used", 196)]},
      {"label": "Wk 5", "parts": [("used", 142)]}],
    "series": [("used", "Hours of demand against 182 available", "#8C4FFF")],
    "unit": "",
    "note": "Average 167 against 182 available. Two of the five weeks were impossible."}),
   "Five weeks whose average looks comfortable. Weeks three and four exceeded capacity and the "
   "average conceals both.",
   "Five weeks of demand against a fixed weekly capacity",
   "A bar chart with five bars showing hours of demand against one hundred and eighty-two "
   "available. Week one: one hundred and twenty. Week two: one hundred and sixty-eight. Week "
   "three: two hundred and ten. Week four: one hundred and ninety-six. Week five: one hundred and "
   "forty-two. A note says the average is one hundred and sixty-seven against one hundred and "
   "eighty-two available, and two of the five weeks were impossible."),
  ("p", "The reporting consequence is direct: the headline number should be weeks over capacity, "
        "not average utilisation. \"Two of the next twelve weeks are above capacity, peaking at "
        "fifteen per cent over in week three\" is actionable. \"Utilisation is projected at "
        "ninety-two per cent\" is not."),
  ("h3", "Some work moves and some does not"),
  ("p", "A peak matters less when the work can be pulled forward or pushed back. Stock production "
        "can be built early; a booked installation on a customer's site cannot. The forecast is "
        "considerably more useful when it distinguishes the two."),
  ("p", "The practical version is to tag demand as fixed or movable at whatever granularity "
        "already exists, and report the peak twice: as booked, and after smoothing the movable "
        "work across adjacent weeks. The gap between those two numbers is the value of being able "
        "to reschedule."),
  ("h2", "A range, not a line"),
  ("fig", ("chain", {
    "entry": {"title": "Known work", "sub": ["confirmed orders"], "icon": "form"},
    "steps": [
      {"title": "Plus likely conversions", "sub": ["quotes, at their rate"], "icon": "counter"},
      {"title": "Plus the usual late arrivals", "sub": ["from history"], "icon": "chart",
       "side": {"title": "How much", "sub": ["measure it, do not guess"], "icon": "search"}},
      {"title": "Apply seasonality", "sub": ["from three years"], "icon": "clock"},
      {"title": "Likely and busy cases", "sub": ["two lines, not one"], "icon": "branch"},
      {"title": "Widen with distance", "sub": ["week 20 is vaguer than week 4"], "icon": "filter"}],
    "note": "The second box is the one people leave out, and it is often a third of the work."}),
   "How a demand range is built. Late-arriving work is a measurable quantity in most businesses "
   "and omitting it produces a forecast that is consistently low.",
   "How a demand forecast range is constructed",
   "A vertical chain of five steps entered by a box labelled Known work, confirmed orders. Step "
   "one adds likely conversions from quotes at their historical rate. Step two adds the usual "
   "late arrivals from history, with a side box saying to measure it rather than guess. Step "
   "three applies seasonality from three years of data. Step four produces likely and busy cases, "
   "two lines rather than one. Step five widens the range with distance, since week twenty is "
   "vaguer than week four. A note says the second box is the one people leave out and it is often "
   "a third of the work."),
  ("h3", "Late arrivals are measurable"),
  ("p", "Every business has work that arrives inside the forecast horizon and was not in the "
        "order book when the forecast was made: repeat customers, urgent jobs, warranty work. In "
        "many operations it is twenty to forty per cent of the total and it is entirely "
        "predictable in aggregate."),
  ("p", "Measuring it is straightforward: for a given past week, compare what was in the order "
        "book four weeks earlier with what was actually delivered. The difference, averaged over a "
        "year, is the uplift to apply. It is one of those quantities that everybody knows exists "
        "and nobody has quantified."),
  ("h3", "Seasonality beats trend"),
  ("p", "At a horizon of a year or less, the seasonal pattern usually explains far more variation "
        "than any growth trend, and it is easier to estimate: three years of weekly data gives a "
        "seasonal shape that is more reliable than an extrapolated trend line."),
  ("p", "A forecast that applies a growth percentage to a flat baseline will systematically miss "
        "the weeks that matter, because the weeks that matter are seasonal peaks rather than a "
        "gradual rise."),
  ("h2", "How to state it"),
  ("callout", "The output, in four lines", [
   "<strong>Weeks above capacity:</strong> 3 of the next 26, all in January.",
   "<strong>Peak shortfall:</strong> 40 hours in week 4 of January, likely case; 68 hours in the "
   "busy case.",
   "<strong>After smoothing movable work:</strong> peak falls to 22 hours, still over.",
   "<strong>Confidence:</strong> based on 3 years of seasonal data and a measured 27% late-arrival "
   "uplift.",
   "<strong>Weeks of notice:</strong> 22. <strong>Lead time to add capacity:</strong> 10.",
   "<strong>No recommendation.</strong> Hiring, contracting and rescheduling are commercial "
   "choices.",
  ]),
  ("p", "The fifth line is what turns this into a decision rather than a chart. Twenty-two weeks "
        "of notice against a ten-week lead time means there is a real choice available, and the "
        "same finding at eight weeks of notice would be a different conversation entirely."),
  ("p", "Next: how far ahead is worth forecasting."),
 ],
},
{
 "slug": "how-far-ahead-is-worth-forecasting",
 "title": "How far ahead is worth forecasting",
 "nav": "How far ahead",
 "read": 5, "words": 720,
 "desc": ("Lead time as the minimum horizon, the point where the forecast stops meaning anything, "
          "and the forecast that arrives too late."),
 "og": ("A four-week forecast in a business where hiring takes twelve weeks tells you about a "
        "problem you can no longer prevent."),
 "abstract": ("Why lead time sets the minimum horizon, the different lead times for different "
              "responses, where a forecast stops being informative, and reporting the notice "
              "period alongside the shortfall."),
 "lede": ("The horizon is the design decision that determines whether a capacity forecast changes "
          "anything, and it is usually set by whatever the reporting tool defaults to."),
 "tags": ["capacity planning", "lead time", "horizon", "decisions", "forecasting", "serverless"],
 "takeaways": [
  "The minimum horizon is the longest lead time to add capacity, plus decision time.",
  "Different responses have different lead times; report against the relevant one.",
  "Beyond a certain distance the range is so wide it stops being informative -- say so.",
  "Report weeks of notice next to every shortfall.",
  "A forecast inside the lead time is still useful, for a different set of actions.",
 ],
 "blocks": [
  ("h2", "Lead time sets the horizon"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Overtime", "parts": [("lead", 1)]},
      {"label": "Agency staff", "parts": [("lead", 3)]},
      {"label": "Subcontract", "parts": [("lead", 4)]},
      {"label": "Hire and train", "parts": [("lead", 10)]},
      {"label": "Buy a machine", "parts": [("lead", 20)]}],
    "series": [("lead", "Weeks from decision to available capacity", "#ED7100")],
    "unit": "",
    "note": "The horizon has to exceed the longest option you want to keep open."}),
   "Five ways of adding capacity and how long each takes. A forecast horizon shorter than one of "
   "these removes that option before anybody has considered it.",
   "Lead times in weeks for five ways of adding capacity",
   "A bar chart with five bars showing weeks from decision to available capacity. Overtime: one "
   "week. Agency staff: three weeks. Subcontract: four weeks. Hire and train: ten weeks. Buy a "
   "machine: twenty weeks. A note says the horizon has to exceed the longest option you want to "
   "keep open."),
  ("p", "The chart makes the design decision obvious. A twenty-six week horizon keeps every "
        "option available; a twelve-week horizon quietly removes machine purchase from the set of "
        "possible responses; a four-week horizon leaves overtime and agency staff, which are the "
        "two most expensive options per hour."),
  ("p", "That is worth stating explicitly because it is a cost consequence of a reporting choice. "
        "Businesses that forecast short systematically pay peak rates for capacity they could "
        "have arranged more cheaply with notice."),
  ("h3", "Decision time is part of it"),
  ("p", "The lead time to hire is ten weeks after somebody decides to hire, and deciding takes "
        "time: a conversation, a budget approval, a job description. Adding two to four weeks of "
        "decision time to every lead time is realistic and is what makes the difference between a "
        "warning that is actionable and one that is theoretically actionable."),
  ("h2", "Where it stops meaning anything"),
  ("fig", ("chain", {
    "entry": {"title": "How far out?", "sub": ["week by week"], "icon": "clock"},
    "steps": [
      {"title": "Order book coverage", "sub": ["how much is booked?"], "icon": "counter"},
      {"title": "Below about a third?", "sub": ["mostly extrapolation"], "icon": "branch",
       "exit": {"title": "Still forecast it", "sub": ["with a wide range"], "icon": "chart",
                "label": "no"}},
      {"title": "Range wider than capacity?", "sub": ["the answer is 'maybe'"], "icon": "branch",
       "exit": {"title": "Useful", "sub": ["report it"], "icon": "check", "label": "no"}},
      {"title": "Say so plainly", "sub": ["'we cannot tell yet'"], "icon": "doc"},
      {"title": "Revisit when booked", "sub": ["coverage grows weekly"], "icon": "search"}],
    "note": "A forecast whose range spans both sides of capacity has not answered the question."}),
   "How the useful end of the horizon is determined. The test in the third box is the honest one: "
   "if the range straddles capacity, the forecast has not said anything.",
   "How the useful limit of a capacity forecast horizon is determined",
   "A vertical chain of five steps entered by a box labelled How far out, considered week by "
   "week. Step one measures order book coverage, asking how much is booked. Step two asks whether "
   "it is below about a third, meaning mostly extrapolation; if not it exits to Still forecast "
   "it, with a wide range. Step three asks whether the range is wider than capacity, so the "
   "answer is maybe; if not it exits to Useful, report it. Step four says so plainly: we cannot "
   "tell yet. Step five revisits when booked, since coverage grows weekly. A note says a forecast "
   "whose range spans both sides of capacity has not answered the question."),
  ("h3", "Saying 'we cannot tell yet'"),
  ("p", "This is a legitimate and underused output. A forecast for week thirty-eight that ranges "
        "from sixty per cent to a hundred and forty per cent of capacity has not answered "
        "anything, and presenting it as a line at a hundred per cent is worse than saying so."),
  ("p", "It also has an action attached: the week to look again. Order book coverage grows "
        "steadily, and the useful statement is \"we will be able to answer this in about six "
        "weeks\", which is itself a plan."),
  ("h2", "Notice period on every shortfall"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Shortfall in wk 26", "sub": ["40 hours"], "icon": "alarm"},
      {"title": "Notice: 22 weeks", "sub": ["from today"], "icon": "clock"},
      {"title": "Hire: 10 weeks", "sub": ["plus 3 to decide"], "icon": "person"},
      {"title": "9 weeks of slack", "sub": ["a real choice"], "icon": "check"},
      {"title": "Report all four", "sub": ["not just the first"], "icon": "doc"}],
    "title": "THE FOUR NUMBERS",
    "note": "Only the fourth one tells anybody whether this is a decision or an announcement."}),
   "The four numbers that belong together. Reporting the shortfall alone leaves the reader to do "
   "the arithmetic that determines whether it matters.",
   "The four numbers reported with every forecast capacity shortfall",
   "A horizontal row of five boxes. Shortfall in week twenty-six: forty hours. Notice: twenty-two "
   "weeks from today. Hire: ten weeks, plus three to decide. Nine weeks of slack: a real choice. "
   "Report all four, not just the first. A note says only the fourth one tells anybody whether "
   "this is a decision or an announcement."),
  ("h3", "Inside the lead time"),
  ("p", "A shortfall discovered with less notice than the lead time is still worth reporting; it "
        "just changes which options are available. Overtime, rescheduling, subcontracting and "
        "talking to customers about dates all have short lead times and all are more expensive or "
        "more painful than planning ahead."),
  ("p", "Reporting the slack as negative &mdash; \"shortfall in six weeks, hiring takes thirteen, "
        "six weeks short of the lead time\" &mdash; makes that explicit and stops the conversation "
        "starting with a suggestion that cannot work."),
  ("p", "Next: finding out whether the forecast was any good."),
 ],
},
{
 "slug": "how-a-forecast-gets-scored-afterwards",
 "title": "How a forecast gets scored afterwards",
 "nav": "How it gets scored",
 "read": 5, "words": 720,
 "desc": ("Recording every forecast, comparing it to what happened, and the bias that only shows "
          "up over a year."),
 "og": ("Almost nobody records what they forecast, which means almost nobody knows whether their "
        "forecasts are any good."),
 "abstract": ("Why forecasts must be stored as they were made, how they are scored against "
              "outcomes, the systematic biases that emerge, and what to do about them."),
 "lede": ("A forecast that is never compared to what happened is an opinion that was written "
          "down, and the difference between the two is a year of quiet learning that nobody "
          "collects."),
 "tags": ["forecasting", "measurement", "bias", "accuracy", "capacity planning", "serverless"],
 "takeaways": [
  "Store every forecast at the moment it was made, immutably.",
  "Score by horizon: a four-week forecast and a twenty-week one are different skills.",
  "Systematic bias is more useful to know about than random error.",
  "The forecast that changed a decision cannot be scored fairly, and say so.",
  "Correct the bias in the method, not by adjusting individual forecasts.",
 ],
 "blocks": [
  ("h2", "Store it as it was"),
  ("fig", ("chain", {
    "entry": {"title": "A forecast is produced", "sub": ["weekly"], "icon": "chart"},
    "steps": [
      {"title": "Write it down", "sub": ["every week, every horizon"], "icon": "database"},
      {"title": "Never update it", "sub": ["append a new one instead"], "icon": "lock"},
      {"title": "Wait", "sub": ["until the week arrives"], "icon": "clock"},
      {"title": "Record what happened", "sub": ["actual demand and output"], "icon": "counter"},
      {"title": "Score by horizon", "sub": ["4 weeks out, 12, 26"], "icon": "search"}],
    "note": "The second box is the whole discipline. A revised forecast is a different forecast."}),
   "How forecasts become scoreable. Storing the forecast as it was made, rather than the latest "
   "version, is the only step that requires any discipline.",
   "How a forecast is stored so it can be scored later",
   "A vertical chain of five steps entered by a box labelled A forecast is produced, weekly. Step "
   "one writes it down, every week and every horizon. Step two never updates it, appending a new "
   "one instead. Step three waits until the week arrives. Step four records what happened, actual "
   "demand and output. Step five scores by horizon: four weeks out, twelve, and twenty-six. A "
   "note says the second box is the whole discipline, and a revised forecast is a different "
   "forecast."),
  ("h3", "By horizon, always"),
  ("p", "Forecasting four weeks ahead and twenty-six weeks ahead are different tasks with "
        "different error rates, and combining them into one accuracy figure produces a number "
        "that describes neither."),
  ("p", "Scored separately, the pattern is usually clear: near-term forecasts are good because "
        "the order book covers most of the demand, and long-term forecasts are good or bad "
        "depending on how well the seasonal pattern holds. Knowing which is which tells you where "
        "to spend effort."),
  ("h2", "Bias beats noise"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "4 weeks out", "parts": [("bias", 2), ("noise", 6)]},
      {"label": "12 weeks out", "parts": [("bias", 9), ("noise", 11)]},
      {"label": "26 weeks out", "parts": [("bias", 14), ("noise", 19)]}],
    "series": [("bias", "Systematic under-forecast, %", "#DD344C"),
               ("noise", "Random error, %", "#7D8CA3")],
    "unit": "",
    "note": "The red band is fixable. The grey band mostly is not."}),
   "A year of forecasts scored by horizon. The systematic component is the one worth acting on "
   "and it is invisible in a single forecast.",
   "Systematic bias and random error in forecasts at three horizons",
   "A stacked bar chart with three bars in per cent. Two series: systematic under-forecast in "
   "red, and random error in grey. Four weeks out shows two per cent bias and six per cent noise. "
   "Twelve weeks out shows nine per cent bias and eleven per cent noise. Twenty-six weeks out "
   "shows fourteen per cent bias and nineteen per cent noise. A note says the red band is fixable "
   "and the grey band mostly is not."),
  ("p", "A consistent under-forecast at longer horizons is the most common finding and it usually "
        "has one cause: the late-arriving work from Part 3 is being underestimated, because the "
        "uplift was set from intuition rather than measured."),
  ("p", "That is a correctable method problem. Adjusting the uplift and watching the bias fall "
        "over the next two quarters is a satisfying and unusual thing to be able to do, and it is "
        "only possible because the forecasts were stored."),
  ("h3", "Correct the method, not the forecast"),
  ("p", "The wrong response to a known bias is for whoever reads the forecast to mentally add "
        "fifteen per cent, because that adjustment is undocumented, inconsistent, and disappears "
        "when the person does. The right response is to change the uplift in the method and "
        "record why."),
  ("h2", "The forecast that changed the outcome"),
  ("callout", "Why some forecasts cannot be scored fairly", [
   "<strong>The forecast said January would be 40 hours short.</strong>",
   "<strong>So two people were hired</strong> and two deliveries were rescheduled.",
   "<strong>January was fine.</strong> The forecast was wrong, by any naive scoring.",
   "<strong>It was also correct</strong> and it worked, which is the entire purpose.",
   "<strong>Record the actions taken</strong> against the forecast, so this case is visible "
   "rather than counted as an error.",
   "<strong>Score demand, not the shortfall.</strong> Demand is largely unaffected by your "
   "response; capacity is not.",
  ]),
  ("p", "The last line is the practical resolution. Forecast accuracy should be measured on the "
        "demand side, where the forecast does not usually influence the outcome, and the capacity "
        "side should be recorded as a decision log rather than scored."),
  ("p", "Without that separation a forecasting system that is working well appears to be "
        "performing badly, which is a reliable way for it to be abandoned."),
  ("h2", "What the annual review says"),
  ("callout", "Once a year, half a page", [
   "<strong>Forecasts made:</strong> 52, each covering 26 weeks.",
   "<strong>Demand accuracy at 4 weeks:</strong> within 8% on 46 of 52.",
   "<strong>Demand accuracy at 26 weeks:</strong> within 20% on 31 of 52.",
   "<strong>Systematic bias:</strong> under-forecasting by 9% at 12 weeks, corrected in June by "
   "raising the late-arrival uplift from 20% to 27%.",
   "<strong>Shortfalls predicted:</strong> 6. <strong>Acted on:</strong> 5. <strong>Occurred "
   "anyway:</strong> 1.",
   "<strong>Shortfalls that occurred with no warning:</strong> 2, both from a customer bringing a "
   "project forward.",
  ]),
  ("p", "The last line is the most valuable one on the page and the least comfortable. Shortfalls "
        "that arrived with no warning are what the system exists to prevent, and two of them in a "
        "year with an identified common cause is a finding about the order book rather than about "
        "the forecast."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="forecast run",
 volumes=[(4, "4 runs"), (20, "20 runs"), (80, "80 runs")],
 read_each=0.0,
 msgs_each=1.0,
 lede=("There is no model in this system and the volumes are tiny: a weekly run per production "
       "area is twenty runs a month for a business with several. Here is where each cent goes."),
 takeaway_extra=("Storing every forecast at every horizon is the only growing line, and it is "
                 "kilobytes."),
 risks=[
  "<strong>Storing only the latest forecast.</strong> Not a cost problem: it makes the entire "
  "scoring exercise in Part 5 impossible, which is where the improvement comes from.",
  "<strong>Recomputing on every order change.</strong> A forecast is a weekly artefact. "
  "Recomputing continuously produces a number that moves for no decidable reason.",
  "<strong>Building a live utilisation dashboard.</strong> The output is a dated warning, not a "
  "gauge. A gauge invites watching rather than deciding.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. Messaging is one summary per "
                "run, which is why it sits at one per unit."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="cf",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the immutable forecast record, and how capacity is derived."),
 outside=[
  {"title": "Output records", "sub": ["what was delivered"], "icon": "counter"},
  {"title": "The order book", "sub": ["and quotes"], "icon": "form"},
  {"title": "A weekly summary", "sub": ["dated warnings"], "icon": "doc"}],
 inside=[
  {"title": "EventBridge weekly", "sub": ["capacity, then", "forecast, then score"], "icon": "clock"},
  {"title": "Lambda x3", "sub": ["capacity, forecast, score"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["forecasts, actuals"], "icon": "database"}],
 note="us-east-1. One account. Forecasts are immutable once written; scoring compares to actuals.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Output records, showing what was "
  "delivered. The order book and quotes. And A weekly summary carrying dated warnings. Inside the "
  "account, three groups. EventBridge running weekly to compute capacity, then the forecast, then "
  "scoring. Three Lambda functions named capacity, forecast and score. And two DynamoDB tables "
  "named forecasts and actuals. A note gives the region as us-east-1, one account, and states "
  "that forecasts are immutable once written and scoring compares them to actuals."),
 functions=[
  ["<code>cf-capacity</code>", "EventBridge, weekly",
   "Derives measured capacity per stage from delivered output over the trailing year",
   "120s / 1024&nbsp;MB"],
  ["<code>cf-forecast</code>", "EventBridge, weekly",
   "Projects demand with seasonality and the late-arrival uplift; writes an immutable forecast "
   "for every horizon", "300s / 1024&nbsp;MB"],
  ["<code>cf-score</code>", "EventBridge, weekly",
   "Compares forecasts whose target week has arrived against actuals; updates bias by horizon",
   "120s / 1024&nbsp;MB"]],
 roles=[
  ["<code>cf-capacity-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "Read-only on output records; writes actuals"],
  ["<code>cf-forecast-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>, <code>ses:SendEmail</code>",
   "Both tables, put only on forecasts; one verified identity"],
  ["<code>cf-score-role</code>", "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>",
   "Both tables"]],
 tables=[
  ("Table: forecasts",
   "PK   made_on           S   2026-08-23 -- the date it was produced\n"
   "SK   stage#target_week S   fitting#2027-W04\n"
   "     horizon_weeks     N   22\n"
   "     demand_likely     N   210\n"
   "     demand_busy       N   238\n"
   "     capacity          N   182 -- measured, at the time\n"
   "     movable_hours     N   18  -- work that could shift week\n"
   "     uplift_used       N   0.27 -- the late-arrival factor in force\n"
   "     actions_taken     L   [{date, what, by}] -- appended later\n\n"
   "No update path except appending to `actions_taken`. A revised forecast\n"
   "is a new item with a later `made_on`, never an edit to this one."),
  ("Table: actuals",
   "PK   stage             S   fitting\n"
   "SK   week              S   2027-W04\n"
   "     demand_actual     N   what was genuinely required\n"
   "     delivered         N   what was produced\n"
   "     capacity_actual   N   what was available that week\n"
   "     shortfall         N   demand minus capacity, if positive\n"
   "     warned            BOOL was there a forecast that saw this?\n\n"
   "`warned` is how the 'shortfalls that occurred with no warning' line in\n"
   "the annual review gets computed, which is the most useful line on it.")],
 inbound=[
  "<strong>Output records are read, never written.</strong> Capacity comes from whatever the "
  "business already records as delivered work.",
  "<strong>The late-arrival uplift is measured</strong>, not configured by opinion: compare each "
  "past week's order book at four weeks out against what was actually delivered.",
  "<strong>Seasonality comes from three years of weekly actuals</strong> where they exist, and "
  "the forecast says so where they do not.",
  "<strong>Every horizon is written every week.</strong> Twenty-six items per stage per week is "
  "trivial storage and is what makes scoring by horizon possible."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Seasonality is an index from historical "
  "weeks and the uplift is a measured ratio.",
  "<strong>The tempting use</strong> is a time-series model. At weekly granularity with three "
  "years of history, a seasonal index plus a measured uplift is competitive and explainable.",
  "<strong>Explainability is the point.</strong> Somebody is going to be asked to hire two people "
  "on the strength of this, and \"the model says so\" is not sufficient.",
  "<strong>A defensible use</strong> is classifying free-text order descriptions into stages "
  "where the order system does not do it.",
  "<strong>The cost page assumes none</strong>, which is why the bill is fixed."],
 gotchas=[
  "Write forecasts immutably at every horizon, every week. Storing only the latest one makes "
  "scoring impossible and the scoring is where the method improves.",
  "Measure capacity from delivered output, never from headcount times hours. The paper figure has "
  "never been achieved and forecasting against it hides every shortfall.",
  "Score demand accuracy, not shortfall accuracy. A shortfall that was averted by acting on the "
  "forecast will otherwise be counted as a forecasting error.",
  "Report weeks of notice alongside every shortfall. Without it nobody can tell whether the "
  "warning is a decision or an announcement.",
  "Re-check which stage is the constraint at least quarterly. A bottleneck analysis from two "
  "years ago is often describing a stage that is no longer binding."],
))
