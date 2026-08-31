"""Day 127 -- 2026-08-29 -- Parking permit issuer."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "parking-permit-issuer"
NAME = "Parking permit issuer"

SPEC = {
 "slug": SLUG, "date": "2026-08-29", "name": NAME,
 "tagline": ("Issues more permits than there are spaces, on purpose, and works out the right "
             "ratio from what actually happens -- because the hard parts of parking are the "
             "allocation rule and the enforcement, and neither of them is a technical problem."),
 "lede": ("A small system that decides how many permits to issue against a fixed number of "
          "spaces, applies an allocation rule that people can live with, reclaims permits nobody "
          "uses, and handles the part that damages relationships. Parking is the smallest system "
          "in this series and produces more complaints than all the others combined. Seven posts "
          "on the same system, one diagram at a time, with a cost breakdown and an engineering "
          "reference at the end."),
 "keywords": ["parking", "permits", "allocation", "facilities", "workplace", "serverless"],
 "icons": ["route", "form", "scale"],
 "faq": [
  ("What is a parking permit issuer?",
   "A small serverless system that manages permits against a fixed number of spaces, applies a "
   "stated allocation rule, tracks usage, and reclaims permits that are not being used."),
  ("Why issue more permits than spaces?",
   "Because on any given day a substantial share of permit holders are not driving in. "
   "Issuing one permit per space wastes a good deal of the car park."),
  ("How is allocation decided?",
   "By a rule that is published before anybody applies. The post on this compares four rules and "
   "argues that stating the rule matters more than which one you pick."),
  ("Are accessible spaces part of this?",
   "No. Accessible bays are allocated on need and are outside the ratio and the ballot entirely."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "parking-permit-issuer-on-aws",
 "title": "A parking permit issuer on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Manages permits against spaces, applies a published allocation rule, and reclaims "
          "unused permits. AWS, about $2 a month."),
 "og": ("Parking generates more complaints per pound of value than any other facilities system, "
        "and almost all of it is about fairness rather than spaces."),
 "abstract": ("The whole system on one page -- ratio, allocation, reclaim &mdash; and why the "
              "published rule matters more than the rule itself."),
 "lede": ("Sixty spaces, two hundred and forty staff, and a car park that is full by twenty past "
          "eight and half empty by three. Every proposal to fix it produces a stronger reaction "
          "than any other facilities decision, and the reason is that parking is one of the few "
          "workplace resources where the allocation is visible to everybody every morning."),
 "tags": ["parking", "permits", "allocation", "facilities", "workplace", "serverless"],
 "takeaways": [
  "Over-issue deliberately, at a ratio derived from measured occupancy.",
  "Publish the allocation rule before applications open. Which rule matters less than that.",
  "Reclaim permits that go unused; they are the main source of new capacity.",
  "Accessible bays are allocated on need and sit outside all of this.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "The car park", "sub": ["a fixed number", "of spaces"], "icon": "route"},
      {"title": "Applications", "sub": ["more than spaces"], "icon": "form"},
      {"title": "Permit holders", "sub": ["and everybody else"], "icon": "person"}],
    "inside": [
      {"title": "The ratio", "sub": ["permits per space,", "from measurement"], "icon": "counter"},
      {"title": "Allocation", "sub": ["a published rule"], "icon": "scale"},
      {"title": "Reclaim", "sub": ["permits nobody uses"], "icon": "filter"}],
    "edges": [{"from": 0, "to": 0, "label": "occupancy"},
              {"from": 1, "to": 1, "label": "who applied"},
              {"from": 2, "to": 2, "label": "permits, and a waiting list", "up": True}],
    "note": "None of these three is a technical problem. All of them benefit from being written down."}),
   "Three things outside the account, three pieces inside it. The engineering is trivial; the "
   "value is in making each decision explicit and consistent.",
   "System: permits issued against spaces, allocated and reclaimed",
   "Three boxes across the top sit outside the AWS account. On the left, The car park with a "
   "fixed number of spaces. In the middle, Applications, more than there are spaces. On the "
   "right, Permit holders and everybody else. Each connects by an arrow to the AWS account "
   "container below. Occupancy flows down into the account. Who applied feeds in. Permits and a "
   "waiting list go back out. Inside the AWS account are three components in a row. On the left, "
   "The ratio: permits per space, derived from measurement. In the middle, Allocation by a "
   "published rule. On the right, Reclaim of permits nobody uses. A note at the bottom says none "
   "of these three is a technical problem and all of them benefit from being written down."),
  ("h3", "Why this is hard"),
  ("p", "Not technically. A permit is a row in a table and a car park has a number of spaces in "
        "it. The difficulty is entirely that parking allocation is a visible distribution of a "
        "scarce good among colleagues, and any rule produces people who did not get one and can "
        "see who did."),
  ("p", "Which means the design goal is not optimality; it is defensibility. A rule that is "
        "published before applications open, applied consistently, and shown to have been applied "
        "consistently, produces far less trouble than a better rule applied opaquely."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The ratio.</strong> How many permits to issue per space, derived from measured "
   "occupancy rather than guessed. Part 2.",
   "<strong>Allocation.</strong> The published rule, applied and recorded. Part 3.",
   "<strong>Reclaim.</strong> Finding permits that are not being used and returning them to the "
   "pool. Part 4.",
  ]),
  ("h2", "One year, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "60 spaces", "sub": ["measured occupancy 71%"], "icon": "route"},
      {"title": "Ratio 1.35", "sub": ["81 permits"], "icon": "counter"},
      {"title": "Rule published", "sub": ["before applications"], "icon": "doc"},
      {"title": "137 apply", "sub": ["81 allocated, 56 waiting"], "icon": "form"},
      {"title": "9 reclaimed", "sub": ["by March"], "icon": "filter"}],
    "title": "ONE YEAR, END TO END",
    "note": "The reclaimed nine are the single largest source of new permits all year."}),
   "The same system as one line. The last box produces more capacity than anything else available "
   "and costs nothing.",
   "One year of parking permit allocation in five stages",
   "A horizontal row of five boxes joined by arrows. Sixty spaces with measured occupancy at "
   "seventy-one per cent. Ratio one point three five, giving eighty-one permits. Rule published "
   "before applications. One hundred and thirty-seven apply: eighty-one allocated and fifty-six "
   "waiting. Nine reclaimed by March. A note says the reclaimed nine are the single largest "
   "source of new permits all year."),
  ("h2", "In plain words"),
  ("p", "Sixty spaces. Counting cars at ten in the morning for a month shows the car park "
        "averaging seventy-one per cent full when permits were issued one per space, which means "
        "roughly three in ten permit holders were not there on any given day."),
  ("p", "So eighty-one permits are issued against sixty spaces, a ratio of one point three five. "
        "That is deliberately conservative &mdash; the arithmetic would support more &mdash; "
        "because being turned away when you have a permit is a much worse experience than not "
        "having one."),
  ("p", "A hundred and thirty-seven people apply. The rule was published two weeks before "
        "applications opened, it is applied, eighty-one people get permits and fifty-six go on a "
        "waiting list with their position visible. By March, nine permits have been reclaimed "
        "from people who used them fewer than four times, and nine people move off the list."),
  ("callout", "Design rules that shaped every decision", [
   "Derive the ratio from measured occupancy, and re-derive it annually.",
   "Publish the allocation rule before applications open. Every time.",
   "Show waiting list position; an invisible list is assumed to be fixed.",
   "Reclaim on measured usage, with warning, and a way to explain.",
   "Accessible bays are outside the ratio, the ballot and the reclaim.",
   "Never enforce automatically. Every enforcement action goes through a person.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The value of a system here is almost entirely in consistency and visibility. A "
        "spreadsheet managed by one person produces the same allocations and produces them in a "
        "way nobody can check, which is what generates the belief that permits are given out on "
        "the basis of who asks loudest."),
  ("p", "Everything in this design is oriented at making the process checkable: a stated rule, a "
        "recorded application of it, a visible waiting list, and usage data that makes reclaim a "
        "fact rather than a judgement."),
  ("p", "The next four posts walk through each piece: how many permits for how many spaces, how "
        "allocation gets decided, what happens to a permit nobody uses, and why enforcement is "
        "the hard part. One diagram per post, a cost breakdown, and an engineering reference at "
        "the end."),
 ],
},
{
 "slug": "how-many-permits-for-how-many-spaces",
 "title": "How many permits for how many spaces",
 "nav": "How many permits",
 "read": 5, "words": 730,
 "desc": ("Measuring occupancy, choosing a ratio, and why being turned away is much worse than "
          "not having a permit."),
 "og": ("Issuing one permit per space wastes about thirty per cent of a car park. Issuing too "
        "many produces the worst experience available."),
 "abstract": ("How occupancy is measured cheaply, how a ratio is derived, why the cost is "
              "asymmetric, and how the ratio is revised."),
 "lede": ("The arithmetic supports over-issuing and the arithmetic is not the whole story, "
          "because the two failure modes are not equally bad."),
 "tags": ["parking", "capacity", "occupancy", "ratios", "facilities", "serverless"],
 "takeaways": [
  "Measure occupancy before deciding anything; counting is enough.",
  "Peak day matters more than average day.",
  "Being turned away with a valid permit is far worse than not having one.",
  "Start conservative and increase the ratio on evidence.",
  "Re-derive annually; working patterns move.",
 ],
 "blocks": [
  ("h2", "Measuring occupancy"),
  ("fig", ("chain", {
    "entry": {"title": "Before deciding anything", "sub": ["measure"], "icon": "search"},
    "steps": [
      {"title": "Count cars", "sub": ["10:00, every working day"], "icon": "counter",
       "side": {"title": "How", "sub": ["a person, a phone,", "thirty seconds"], "icon": "person"}},
      {"title": "For a month", "sub": ["four weeks minimum"], "icon": "clock"},
      {"title": "Average and peak", "sub": ["both matter"], "icon": "chart"},
      {"title": "Any pattern?", "sub": ["Tuesdays, month end"], "icon": "branch"},
      {"title": "A ratio", "sub": ["conservative at first"], "icon": "scale"}],
    "note": "Thirty seconds a day for a month is the entire data collection exercise."}),
   "How the ratio is established. The measurement is deliberately crude because a crude "
   "measurement is one that actually gets done.",
   "How car park occupancy is measured before setting a permit ratio",
   "A vertical chain of five steps entered by a box labelled Before deciding anything, measure. "
   "Step one counts cars at ten in the morning every working day, with a side box saying it takes "
   "a person, a phone and thirty seconds. Step two continues for a month, four weeks minimum. "
   "Step three computes average and peak, both of which matter. Step four looks for any pattern "
   "such as Tuesdays or month end. Step five produces a ratio, conservative at first. A note says "
   "thirty seconds a day for a month is the entire data collection exercise."),
  ("h3", "Peak, not average"),
  ("p", "The same argument as the capacity forecaster in Day 121. A car park that averages "
        "seventy-one per cent occupancy and hits ninety-four per cent on Tuesdays is full on "
        "Tuesdays, and the ratio has to be set against the day people actually come in."),
  ("p", "Hybrid working has made this sharper. A building where most people come in on Tuesday "
        "and Wednesday has a peak that is very different from its average, and a ratio derived "
        "from the average produces a car park that overflows twice a week."),
  ("h2", "The asymmetry"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "No permit", "parts": [("cost", 3)]},
      {"label": "Permit, space free", "parts": [("cost", 0)]},
      {"label": "Permit, turned away", "parts": [("cost", 9)]}],
    "series": [("cost", "Relative annoyance, roughly", "#DD344C")],
    "unit": "",
    "note": "Somebody who drove in on the strength of a permit has no alternative at 08:40."}),
   "The three outcomes and their relative cost. The asymmetry between not having a permit and "
   "being turned away with one is the argument for a conservative ratio.",
   "The relative cost of three parking outcomes",
   "A bar chart with three bars showing relative annoyance. No permit: three. Permit with a space "
   "free: zero. Permit but turned away: nine. A note says somebody who drove in on the strength "
   "of a permit has no alternative at twenty to nine."),
  ("p", "Somebody without a permit plans around it: public transport, a different arrival time, a "
        "paid car park. Somebody with a permit who arrives to a full car park has made a decision "
        "based on it and is now looking for street parking while late for something."),
  ("p", "Which is why the ratio should be conservative even where the occupancy data supports "
        "more. A car park that is occasionally ninety-five per cent full is working; one that "
        "turns people away weekly has broken the promise the permit represented."),
  ("h2", "Starting conservative"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Year 1: 1.35", "parts": [("full", 2), ("space", 58)]},
      {"label": "Year 2: 1.50", "parts": [("full", 5), ("space", 55)]},
      {"label": "Year 3: 1.65", "parts": [("full", 14), ("space", 46)]}],
    "series": [("full", "Days full, per quarter", "#DD344C"),
               ("space", "Days with space", "#7AA116")],
    "unit": "",
    "note": "Year three is where it starts to hurt. Year two was the right answer."}),
   "Three years of increasing the ratio on evidence. The point at which days-full rises sharply "
   "is the point to stop, and it is only findable by moving gradually.",
   "Days the car park was full at three different permit ratios",
   "A stacked bar chart with three bars showing days per quarter. Two series: days full in red, "
   "and days with space in green. Year one at a ratio of one point three five: two days full and "
   "fifty-eight with space. Year two at one point five: five days full and fifty-five with space. "
   "Year three at one point six five: fourteen days full and forty-six with space. A note says "
   "year three is where it starts to hurt and year two was the right answer."),
  ("p", "Moving the ratio gradually and measuring the days-full count is a straightforward way to "
        "find the right level, and it has the useful property of being explicable: the ratio went "
        "up because there was space, and it will come back down if there is not."),
  ("p", "It also means the ratio is a thing the organisation has evidence about, which converts "
        "an argument about fairness into a question about a number."),
  ("h3", "Re-deriving annually"),
  ("p", "Working patterns move, headcount moves, public transport changes, and a ratio set three "
        "years ago is describing a different building. Re-measuring for a month once a year is a "
        "small exercise and it prevents a ratio quietly becoming wrong."),
  ("h3", "What is not in the ratio"),
  ("p", "Accessible bays, visitor spaces, and any operational vehicles are outside the pool "
        "entirely. They are not permits, they are not allocated by the rule, and counting them "
        "in the ratio produces both a wrong ratio and an unpleasant conversation."),
  ("p", "Next: who gets one."),
 ],
},
{
 "slug": "how-allocation-gets-decided",
 "title": "How allocation gets decided without a riot",
 "nav": "How allocation works",
 "read": 6, "words": 760,
 "desc": ("Four rules, what each one rewards, why publishing beats optimising, and the waiting "
          "list."),
 "og": ("Which allocation rule you choose matters less than publishing it two weeks before "
        "applications open."),
 "abstract": ("Four allocation rules and what each rewards, why the published rule matters more "
              "than the choice, how a waiting list is run, and the exceptions that are not "
              "exceptions."),
 "lede": ("There is no allocation rule that everybody thinks is fair, and there is a large "
          "difference between a rule people disagree with and a rule people cannot see."),
 "tags": ["parking", "allocation", "fairness", "policy", "workplace", "serverless"],
 "takeaways": [
  "Four common rules; each rewards something different and none is neutral.",
  "Publishing the rule in advance matters more than which one it is.",
  "Show the waiting list position; an invisible list is assumed to be rigged.",
  "Accessible need is not an exception to the rule; it sits outside it.",
  "Record every allocation decision against the rule that produced it.",
 ],
 "blocks": [
  ("h2", "Four rules"),
  ("table", ["Rule", "Rewards", "Complaint it generates"], [
   ["Distance from public transport", "People with no alternative",
    "\"I live further away but have a station\""],
   ["Ballot", "Nobody; it is random", "\"I have been here twelve years\""],
   ["Seniority or length of service", "Tenure", "\"I need it and they do not\""],
   ["First come, first served", "Speed of response, and whoever was told first",
    "\"I did not know applications opened\""],
   ["Need, assessed", "Genuine circumstances", "\"Who decides what counts as need?\""],
  ]),
  ("p", "Each of these is defensible and each produces a specific complaint, and the complaints "
        "are predictable enough to be worth reading before choosing. The distance rule is the "
        "most common and produces the most edge cases; the ballot is the most obviously fair and "
        "the most resented by long-serving staff."),
  ("p", "A combination is usually what happens in practice: a small number allocated on assessed "
        "need, the rest by distance or ballot, with a stated proportion for each. That is fine as "
        "long as the proportions are published too."),
  ("h2", "Publishing beats optimising"),
  ("fig", ("chain", {
    "entry": {"title": "Permits to allocate", "sub": ["81 of them"], "icon": "form"},
    "steps": [
      {"title": "Publish the rule", "sub": ["2 weeks before applying"], "icon": "doc",
       "side": {"title": "Including", "sub": ["the tie-break"], "icon": "search"}},
      {"title": "Applications open", "sub": ["a stated window"], "icon": "clock"},
      {"title": "Apply the rule", "sub": ["mechanically"], "icon": "scale"},
      {"title": "Record why each", "sub": ["against the rule"], "icon": "database"},
      {"title": "Publish the outcome", "sub": ["counts, not names"], "icon": "chart"}],
    "note": "Every step here is about being checkable, and none of it is about optimality."}),
   "The allocation process. Each step exists to make the outcome defensible rather than better.",
   "How parking permits are allocated under a published rule",
   "A vertical chain of five steps entered by a box labelled Permits to allocate, eighty-one of "
   "them. Step one publishes the rule two weeks before applying, with a side box noting it "
   "includes the tie-break. Step two opens applications for a stated window. Step three applies "
   "the rule mechanically. Step four records why each decision was made against the rule. Step "
   "five publishes the outcome as counts rather than names. A note says every step here is about "
   "being checkable and none of it is about optimality."),
  ("h3", "The tie-break"),
  ("p", "The rule needs one and it needs to be published with the rule, because the tie-break is "
        "where a mechanical process becomes a judgement if it has not been decided in advance. "
        "Two people equidistant from the office, applying on the same day, need a stated way of "
        "being separated."),
  ("p", "A random tie-break is the honest answer and it should be described as random rather than "
        "dressed up. \"Ties are resolved by a draw\" is something people accept; a tie resolved "
        "by something unstated is not."),
  ("h3", "Publishing the outcome"),
  ("p", "Counts, not names: how many applied, how many were allocated, the distance threshold "
        "that resulted, the number allocated on assessed need. That lets anybody check that the "
        "rule produced the outcome without publishing who parks where."),
  ("p", "It also removes the most common suspicion, which is that more permits were issued than "
        "were announced."),
  ("h2", "The waiting list"),
  ("fig", ("strip", {
    "stages": [
      {"title": "56 on the list", "sub": ["ordered by the rule"], "icon": "counter"},
      {"title": "Position visible", "sub": ["to each person"], "icon": "person"},
      {"title": "Movement visible", "sub": ["'you were 34, now 27'"], "icon": "chart"},
      {"title": "Offers in order", "sub": ["recorded"], "icon": "form"},
      {"title": "Declines keep position", "sub": ["or go to the back?", "state it"], "icon": "branch"}],
    "title": "THE LIST HAS TO BE VISIBLE",
    "note": "An invisible waiting list is universally assumed not to move at all."}),
   "How the waiting list works. Visibility of position and movement is what stops the list being "
   "assumed to be decorative.",
   "How a parking permit waiting list is run and shown",
   "A horizontal row of five boxes. Fifty-six on the list, ordered by the rule. Position visible "
   "to each person. Movement visible: you were thirty-four, now twenty-seven. Offers in order, "
   "recorded. Declines keep position, or go to the back? State it. A note says an invisible "
   "waiting list is universally assumed not to move at all."),
  ("p", "The last box is a real decision that has to be made in advance. Somebody offered a "
        "permit in November who does not want one until they move house in March: do they keep "
        "their position or go to the back? Both are defensible and only one of them can be the "
        "rule."),
  ("h2", "What is not an exception"),
  ("callout", "Sitting outside the rule entirely", [
   "<strong>Accessible bays</strong> are allocated on need, are not in the permit pool, and are "
   "not subject to the ratio.",
   "<strong>Temporary need</strong> &mdash; an injury, a medical course of treatment, a pregnancy "
   "&mdash; gets a temporary permit outside the allocation, with an end date.",
   "<strong>Operational vehicles</strong> are not permits.",
   "<strong>Visitors</strong> have their own spaces and their own process.",
   "<strong>These are not exceptions to the rule.</strong> They are outside it, and describing "
   "them that way removes the sense that exceptions are being made.",
   "<strong>Temporary permits have end dates</strong> that are enforced, kindly, with a reminder "
   "and a way to extend.",
  ]),
  ("p", "The framing in the fifth line does real work. \"An exception was made for X\" invites "
        "the question of why not for me; \"accessible bays are allocated on need and are not part "
        "of the permit scheme\" is a description of a different thing."),
  ("p", "Next: the permits nobody uses."),
 ],
},
{
 "slug": "what-happens-to-a-permit-nobody-uses",
 "title": "What happens to a permit nobody uses",
 "nav": "Unused permits",
 "read": 5, "words": 710,
 "desc": ("Measuring usage without surveillance, the warning, the explanation, and where new "
          "capacity actually comes from."),
 "og": ("The largest source of parking capacity in most organisations is the permits held by "
        "people who stopped driving in eight months ago."),
 "abstract": ("How usage is measured proportionately, the warning and explanation process, what "
              "counts as a good reason, and why this beats any other capacity measure."),
 "lede": ("Circumstances change, people move house, start cycling, or change their working "
          "pattern, and a permit issued two years ago on the basis of a situation that no longer "
          "exists is capacity sitting idle."),
 "tags": ["parking", "utilisation", "permits", "fairness", "facilities", "serverless"],
 "takeaways": [
  "Measure usage crudely; a rough count is enough and needs no surveillance.",
  "Warn, explain, then reclaim. Never reclaim without a conversation.",
  "Reasons that are good: illness, leave, a working pattern that changed temporarily.",
  "Reclaimed permits are the largest source of capacity available.",
  "An annual reapplication achieves much of this with less machinery.",
 ],
 "blocks": [
  ("h2", "Measuring usage proportionately"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Barrier or fob logs", "sub": ["if they already exist"], "icon": "form",
       "label": "free"},
      {"title": "Periodic spot checks", "sub": ["which permits are here"], "icon": "search",
       "label": "cheap"},
      {"title": "Self-declared", "sub": ["'do you still need it?'"], "icon": "person",
       "label": "surprisingly effective"}],
    "target": {"title": "Enough to identify", "sub": ["permits used almost never"], "icon": "chart",
               "then": {"title": "Not enough to track", "sub": ["anybody's movements"],
                        "icon": "shield"}},
    "note": "The goal is finding the unused, not building a record of who came in when."}),
   "Three ways of measuring permit usage and the deliberate limit on all of them. The distinction "
   "in the last box shapes which method to prefer.",
   "Three ways of measuring parking permit usage",
   "Three boxes stacked on the left. Barrier or fob logs, if they already exist, labelled free. "
   "Periodic spot checks of which permits are present, labelled cheap. And Self-declared, asking "
   "whether somebody still needs it, labelled surprisingly effective. All three converge on "
   "Enough to identify permits used almost never, and that leads down to Not enough to track "
   "anybody's movements. A note says the goal is finding the unused rather than building a record "
   "of who came in when."),
  ("h3", "Just asking works"),
  ("p", "An annual message saying \"you have a parking permit; do you still need it?\" with two "
        "buttons reclaims a meaningful number with no measurement at all. People who have started "
        "cycling or moved closer are frequently happy to release it, and nobody had ever asked."),
  ("p", "It is worth doing before building any usage tracking, because it is free, it is not "
        "surveillance, and it may solve most of the problem. If it does, the tracking is "
        "unnecessary."),
  ("h3", "If usage is tracked"),
  ("p", "Aggregate is enough: a count of days used per quarter per permit. There is no need to "
        "store which days, and storing which days creates a record of somebody's attendance "
        "pattern that was collected for parking and will eventually be asked for by somebody "
        "else."),
  ("p", "That restraint is worth building in deliberately: count and discard rather than store "
        "and count. It is barely more work and it removes an entire category of future question."),
  ("h2", "Warn, explain, reclaim"),
  ("fig", ("chain", {
    "entry": {"title": "A permit used 3 days", "sub": ["in a quarter"], "icon": "counter"},
    "steps": [
      {"title": "A message, not a decision", "sub": ["'we noticed, is it still needed?'"],
       "icon": "email"},
      {"title": "Any reply?", "sub": ["two weeks"], "icon": "branch",
       "exit": {"title": "Second message", "sub": ["and a person follows up"], "icon": "person",
                "label": "no"}},
      {"title": "A reason given?", "sub": ["illness, leave, pattern"], "icon": "branch",
       "exit": {"title": "Keep it", "sub": ["review next quarter"], "icon": "check",
                "label": "yes"}},
      {"title": "Released willingly?", "sub": ["most are"], "icon": "branch",
       "exit": {"title": "Straight to the list", "sub": ["thank them"], "icon": "form",
                "label": "yes"}},
      {"title": "Reclaim, with notice", "sub": ["and a right to reapply"], "icon": "filter"}],
    "note": "Most permits are released voluntarily at the first message. The rest need a person."}),
   "The reclaim process. Four opportunities to resolve it without anybody having something taken "
   "away, which is what makes the last step survivable.",
   "How an unused parking permit is reclaimed",
   "A vertical chain of five steps entered by a box labelled A permit used three days in a "
   "quarter. Step one sends a message rather than a decision: we noticed, is it still needed? "
   "Step two asks whether there was any reply within two weeks; if not it exits to Second "
   "message, and a person follows up. Step three asks whether a reason was given such as illness, "
   "leave or a changed pattern; if so it exits to Keep it, review next quarter. Step four asks "
   "whether it was released willingly, as most are; if so it exits to Straight to the list, thank "
   "them. Step five reclaims with notice and a right to reapply. A note says most permits are "
   "released voluntarily at the first message and the rest need a person."),
  ("h3", "Reasons that are good"),
  ("p", "Long-term sickness, parental leave, a secondment, a temporary change in working pattern, "
        "a period of working from home for a reason. All of these are situations where somebody "
        "will need the permit again and taking it away is both unkind and pointless."),
  ("p", "The review-next-quarter outcome handles them properly: the permit is retained, the "
        "situation is noted, and it is looked at again rather than either forgotten or removed."),
  ("h2", "Where capacity comes from"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Reclaimed permits", "parts": [("n", 9)]},
      {"label": "Raised the ratio", "parts": [("n", 6)]},
      {"label": "Restriped the car park", "parts": [("n", 3)]},
      {"label": "New spaces built", "parts": [("n", 0)]}],
    "series": [("n", "Additional permits made available this year", "#7AA116"),],
    "unit": "",
    "note": "The cheapest option is also the largest, and it needs no capital at all."}),
   "Where a year's additional permits came from. Reclaim outperforms every other option and costs "
   "nothing.",
   "Sources of additional parking permits over one year",
   "A bar chart with four bars showing additional permits made available. Reclaimed permits: "
   "nine. Raised the ratio: six. Restriped the car park: three. New spaces built: none. A note "
   "says the cheapest option is also the largest and it needs no capital at all."),
  ("p", "Restriping is worth mentioning because it occasionally produces real gains &mdash; a car "
        "park laid out for larger vehicles, or with awkward corners, can sometimes yield a few "
        "more bays &mdash; and it is a one-off with a modest cost."),
  ("p", "Building new spaces is generally not available, is expensive where it is, and takes long "
        "enough that the working pattern will have changed before it opens."),
  ("h3", "The simpler alternative"),
  ("p", "Annual reapplication achieves much of what reclaim does with less machinery: everybody "
        "reapplies each year, the rule is applied afresh, and permits that are no longer needed "
        "simply are not applied for."),
  ("p", "It is more disruptive &mdash; everybody faces uncertainty annually &mdash; and it is "
        "considerably simpler, and for a small organisation it is probably the better answer. "
        "Worth deciding deliberately rather than defaulting to the more complex option."),
  ("p", "Next: the part that damages relationships."),
 ],
},
{
 "slug": "why-enforcement-is-the-hard-part",
 "title": "Why enforcement is the hard part",
 "nav": "Why enforcement is hard",
 "read": 5, "words": 700,
 "desc": ("What enforcement costs socially, why it should be slow, and what to think about before "
          "installing cameras."),
 "og": ("Every enforcement action is a colleague being told off in a car park, and the "
        "proportionate response is almost always slower than the available one."),
 "abstract": ("Why enforcement damages more than it recovers, how a graduated response works, "
              "what number plate recognition actually creates, and why a person is always in the "
              "loop."),
 "lede": ("A permit system without enforcement gradually stops meaning anything, and enforcement "
          "is where a mildly annoying facilities process becomes a genuinely unpleasant one."),
 "tags": ["parking", "enforcement", "ANPR", "privacy", "workplace", "serverless"],
 "takeaways": [
  "Most unauthorised parking is a one-off with a reason.",
  "Graduated response: notice, then conversation, then something formal. Slowly.",
  "Never an automatic penalty. A person decides every time.",
  "Number plate recognition creates a movement record; decide about that explicitly.",
  "Measure whether enforcement is needed before building any of it.",
 ],
 "blocks": [
  ("h2", "What is actually happening"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "One-off, a reason", "parts": [("n", 34)]},
      {"label": "Did not know the rules", "parts": [("n", 11)]},
      {"label": "Visitor, wrong bay", "parts": [("n", 9)]},
      {"label": "Repeatedly, no permit", "parts": [("n", 3)]}],
    "series": [("n", "Incidents in a quarter", "#ED7100")],
    "unit": "",
    "note": "Three people are the actual problem. An enforcement regime hits all fifty-seven."}),
   "A quarter of unauthorised parking by cause. Designing enforcement for the last bar and "
   "applying it to all four is how a parking policy becomes notorious.",
   "Causes of unauthorised parking incidents over one quarter",
   "A bar chart with four bars showing incidents in a quarter. One-off with a reason: thirty-"
   "four. Did not know the rules: eleven. Visitor in the wrong bay: nine. Repeatedly with no "
   "permit: three. A note says three people are the actual problem and an enforcement regime hits "
   "all fifty-seven."),
  ("p", "The first bar is people with a genuine one-off reason: a hospital appointment, a heavy "
        "delivery to carry, a car that would not start on the usual route. Those are not "
        "violations in any meaningful sense and treating them as such is where the resentment "
        "comes from."),
  ("p", "The last bar is the actual problem, it is small, and it is almost always known to "
        "everybody already. A conversation resolves most of it and does not require any system."),
  ("h2", "Graduated, and slow"),
  ("fig", ("chain", {
    "entry": {"title": "A car without a permit", "sub": ["in a permit bay"], "icon": "route"},
    "steps": [
      {"title": "First time?", "sub": ["check the record"], "icon": "branch",
       "exit": {"title": "A note on the screen", "sub": ["polite, explaining"], "icon": "doc",
                "label": "yes"}},
      {"title": "Second or third?", "sub": ["within a quarter"], "icon": "branch",
       "exit": {"title": "An email", "sub": ["from a person, asking"], "icon": "email",
                "label": "yes"}},
      {"title": "Repeated after that?", "sub": ["and no explanation"], "icon": "branch",
       "exit": {"title": "A conversation", "sub": ["face to face"], "icon": "person",
                "label": "yes"}},
      {"title": "Still repeated?", "sub": ["deliberately"], "icon": "branch"},
      {"title": "Something formal", "sub": ["a person decides, always"], "icon": "shield"}],
    "note": "Four steps before anything formal. Almost nothing reaches the fifth box."}),
   "The graduated response. Its slowness is the design: almost every case resolves in the first "
   "two boxes and never becomes a confrontation.",
   "The graduated response to unauthorised parking",
   "A vertical chain of five steps entered by a box labelled A car without a permit in a permit "
   "bay. Step one asks whether it is the first time, checking the record; if so it exits to A "
   "note on the screen, polite and explaining. Step two asks whether it is the second or third "
   "within a quarter; if so it exits to An email from a person, asking. Step three asks whether "
   "it is repeated after that with no explanation; if so it exits to A conversation, face to "
   "face. Step four asks whether it is still repeated, deliberately. Step five leads to something "
   "formal, with a person deciding, always. A note says four steps happen before anything formal "
   "and almost nothing reaches the fifth box."),
  ("h3", "No automatic penalties"),
  ("p", "A system that issues a charge automatically will issue one to somebody who was bringing "
        "a colleague to hospital, and the cost of that single event exceeds the entire value of "
        "the enforcement regime."),
  ("p", "Every action beyond a polite note goes through a person who can see the context, and "
        "that person needs to be someone with the standing to decide not to act."),
  ("h2", "Before installing cameras"),
  ("callout", "What number plate recognition actually creates", [
   "<strong>A record of when each employee arrived and left,</strong> every day, indefinitely.",
   "<strong>That record will be requested</strong> for something other than parking. Attendance, "
   "an investigation, a dispute.",
   "<strong>It is personal data</strong> about staff, collected for one purpose, and using it for "
   "another needs care.",
   "<strong>The parking problem it solves</strong> is three people a quarter.",
   "<strong>If it goes in anyway:</strong> a short retention, a stated purpose, and an explicit "
   "rule about who can query it and for what.",
   "<strong>Ask first whether the problem</strong> justifies the record. Frequently it does not.",
  ]),
  ("p", "The second line is the one to think hardest about. A system installed for parking "
        "enforcement becomes an attendance record the first time somebody senior asks a question "
        "it can answer, and there is rarely a mechanism in place to refuse."),
  ("h2", "Measuring whether it is needed"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Count incidents", "sub": ["for a month, by hand"], "icon": "counter"},
      {"title": "How many repeat?", "sub": ["usually very few"], "icon": "search"},
      {"title": "Talk to those people", "sub": ["it usually works"], "icon": "person"},
      {"title": "Recount", "sub": ["a month later"], "icon": "chart"},
      {"title": "Probably solved", "sub": ["with no system at all"], "icon": "check"}],
    "title": "TRY THIS FIRST",
    "note": "Most workplace parking enforcement problems are three conversations."}),
   "The cheapest available approach, and the one to exhaust before building anything. It "
   "frequently works.",
   "How to test whether parking enforcement is needed before building it",
   "A horizontal row of five boxes. Count incidents for a month, by hand. How many repeat? "
   "Usually very few. Talk to those people: it usually works. Recount a month later. Probably "
   "solved, with no system at all. A note says most workplace parking enforcement problems are "
   "three conversations."),
  ("p", "This is genuinely the recommendation. The enforcement machinery is the most expensive "
        "part of a parking system in social terms and frequently addresses a problem that a small "
        "number of conversations would have resolved permanently."),
  ("h3", "What the permit system contributes"),
  ("p", "A record of who holds a permit and for which vehicle, so that a question can be answered "
        "quickly and correctly. That is nearly all of it, and it is the part worth building."),
  ("p", "The rest &mdash; detection, escalation, penalties &mdash; should be added only if "
        "counting shows a problem that conversation did not solve, which in most workplaces it "
        "will not."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="permit",
 volumes=[(60, "60 permits"), (200, "200 permits"), (800, "800 permits")],
 read_each=0.0,
 msgs_each=0.6,
 lede=("There is no model in this system and almost nothing happens on most days: an allocation "
       "round once a year and a usage review each quarter. Two hundred permits is a large site. "
       "Here is where each cent goes."),
 takeaway_extra=("Messaging is annual allocation plus quarterly usage reviews, averaged across "
                 "the year."),
 risks=[
  "<strong>Storing every barrier event indefinitely.</strong> Aggregate to a count per permit per "
  "quarter and discard the detail; the detail is an attendance record.",
  "<strong>Running an allocation pass continuously.</strong> It is an annual event with a "
  "waiting list in between.",
  "<strong>Building enforcement machinery first.</strong> Not a cloud cost, and the largest cost "
  "in the whole project. Part 5 covers it.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. Messaging is the allocation "
                "round, waiting list movements and quarterly usage prompts."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="pp",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the allocation record, and the usage aggregation."),
 outside=[
  {"title": "Applications", "sub": ["a form, annually"], "icon": "form"},
  {"title": "Usage signal", "sub": ["barrier, spot check,", "or just asking"], "icon": "route"},
  {"title": "Permit holders", "sub": ["and the waiting list"], "icon": "person"}],
 inside=[
  {"title": "API + EventBridge", "sub": ["applications,", "quarterly review"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["allocate, usage, review"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["permits, applications"], "icon": "database"}],
 note="us-east-1. One account. Usage stored as counts per quarter; individual events discarded.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Applications, submitted through a form "
  "annually. A Usage signal from a barrier, a spot check, or simply asking. And Permit holders "
  "and the waiting list. Inside the account, three groups. An API for applications and "
  "EventBridge running the quarterly review. Three Lambda functions named allocate, usage and "
  "review. And two DynamoDB tables named permits and applications. A note gives the region as "
  "us-east-1, one account, and states that usage is stored as counts per quarter with individual "
  "events discarded."),
 functions=[
  ["<code>pp-allocate</code>", "API, once per allocation round",
   "Applies the published rule, records the reason per decision, builds the ordered waiting list",
   "120s / 1024&nbsp;MB"],
  ["<code>pp-usage</code>", "API or scheduled import",
   "Increments a per-permit per-quarter counter; never stores the individual event",
   "10s / 512&nbsp;MB"],
  ["<code>pp-review</code>", "EventBridge, quarterly",
   "Finds low-usage permits, sends the first message, tracks replies through the reclaim ladder",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>pp-allocate-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>, <code>ses:SendEmail</code>",
   "Both tables; one verified identity"],
  ["<code>pp-usage-role</code>", "<code>dynamodb:UpdateItem</code>",
   "Permits only, and only the counter attribute"],
  ["<code>pp-review-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Permits; one verified identity"]],
 tables=[
  ("Table: permits",
   "PK   permit_id         S\n"
   "     person_id         S\n"
   "     vehicles          L   registrations; people change cars\n"
   "     issued_at         S\n"
   "     expires_at        S   annual, or the temporary end date\n"
   "     kind              S   standard | temporary_need | accessible\n"
   "     allocated_by_rule S   'distance, 6.2km, above the 4.8km threshold'\n"
   "     usage             M   {2026Q3: 41, 2026Q4: 3} -- counts only\n"
   "     review_state      S   none | asked | reason_given | releasing\n"
   "     review_reason     S   the reason they gave, verbatim\n\n"
   "`usage` holds counts, never dates. Storing which days somebody drove in\n"
   "creates an attendance record collected for a different purpose."),
  ("Table: applications",
   "PK   round_id          S   2026\n"
   "SK   person_id         S\n"
   "     applied_at        S\n"
   "     distance_km       N   or whatever the published rule uses\n"
   "     declared_need     S   free text, assessed by a person\n"
   "     outcome           S   allocated | waiting | declined\n"
   "     rule_version      S   the exact rule text published for this round\n"
   "     tie_break_draw    N   recorded, because ties must be explicable\n"
   "     list_position     N   shown to the applicant, and it moves\n\n"
   "`rule_version` stores the published text, so a decision can always be\n"
   "checked against the rule that was actually in force.")],
 inbound=[
  "<strong>Applications open for a stated window</strong> after the rule is published, and the "
  "rule text is stored with the round rather than referenced.",
  "<strong>Usage arrives as increments</strong>, from whatever signal exists. The API accepts a "
  "permit and a date and stores only a counter.",
  "<strong>Accessible and temporary permits</strong> are a different kind and are excluded from "
  "the ratio, the ballot and the reclaim review.",
  "<strong>Waiting list position is computed from the stored ordering</strong> and shown to each "
  "applicant, including when it moves."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Allocation is sorting and the reclaim "
  "ladder is four states.",
  "<strong>The tempting use</strong> is assessing declared need from free text. That is a "
  "judgement about somebody's circumstances and it belongs to a person who can ask a follow-up "
  "question.",
  "<strong>The wrong use</strong> is number plate recognition and any inference from it. Part 5 "
  "covers what that record becomes.",
  "<strong>A defensible use</strong> is normalising vehicle registrations typed in different "
  "formats, which is a small annoyance solved more cheaply by a regular expression.",
  "<strong>The cost page assumes none</strong>, which is why messaging is the only variable."],
 gotchas=[
  "Store the published rule text with the allocation round. A decision that cannot be checked "
  "against the rule in force at the time is not defensible.",
  "Store usage as counts, never as dated events. The dated version is an attendance record and "
  "somebody will eventually ask to use it that way.",
  "Show waiting list position and its movement. An invisible list is universally assumed not to "
  "move.",
  "Keep accessible and temporary permits outside the ratio and the review. Including them "
  "produces both wrong arithmetic and an unpleasant conversation.",
  "Put a person in front of every enforcement action beyond a polite note. One automatic penalty "
  "issued to somebody at a hospital appointment outweighs the whole regime."],
))
