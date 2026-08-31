"""Day 125 -- 2026-08-27 -- Housekeeping dispatcher."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "housekeeping-dispatcher"
NAME = "Housekeeping dispatcher"

SPEC = {
 "slug": SLUG, "date": "2026-08-27", "name": NAME,
 "tagline": ("Decides which rooms get cleaned in what order -- balancing arriving guests against "
             "walking distance against who has had the difficult rooms all week, and never "
             "sending anybody into a room where somebody is still asleep."),
 "lede": ("A small system that turns a list of rooms into a sensible order of work for each "
          "person, respects do-not-disturb absolutely, keeps the walking down, shares the hard "
          "rooms out, and leaves the decision that a room is ready with the person who looked at "
          "it. Seven posts on the same system, one diagram at a time, with a cost breakdown and "
          "an engineering reference at the end."),
 "keywords": ["housekeeping", "hotel operations", "dispatch", "scheduling", "hospitality",
              "serverless"],
 "icons": ["person", "route", "check"],
 "faq": [
  ("What is a housekeeping dispatcher?",
   "A small serverless system that assigns rooms to housekeepers in an order that reflects "
   "arrival times, walking distance, do-not-disturb status and a fair share of the difficult "
   "rooms."),
  ("Why does the route matter?",
   "Because walking between floors is unpaid, unproductive time, and a strictly priority-ordered "
   "list can send somebody up and down four times in a morning."),
  ("What happens to a do-not-disturb room?",
   "Nothing. It is deferred and re-offered later, and there is no override in the system. The "
   "escalation is a person knocking at a stated hour, not a dispatch."),
  ("Does the system mark rooms ready?",
   "No. A person says a room is ready, and inspection is a separate state from cleaned. The post "
   "on this explains why conflating them is a problem."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "housekeeping-dispatcher-on-aws",
 "title": "A housekeeping dispatcher on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Assigns rooms in a sensible order, respects do-not-disturb, keeps the walking down, "
          "and shares the hard rooms. AWS, about $2 a month."),
 "og": ("A perfectly prioritised room list that sends somebody up and down four floors has "
        "optimised the wrong thing."),
 "abstract": ("The whole system on one page -- priority, route, fairness &mdash; and the three "
              "constraints that pull against each other."),
 "lede": ("The list is produced by priority: eleven rooms with guests arriving early, sorted by "
          "arrival time. It sends one housekeeper from the fourth floor to the first, back to the "
          "third, then the second, then the fourth again. About forty minutes of the morning "
          "disappears into a lift. This post walks through a small system that trades a little "
          "priority for a lot of walking."),
 "tags": ["housekeeping", "hotel operations", "dispatch", "scheduling", "hospitality",
          "serverless"],
 "takeaways": [
  "Priority and route pull against each other; the answer is a compromise, not either one.",
  "Do-not-disturb is absolute. There is no override in the system.",
  "Share the difficult rooms out, or the same person gets them every week.",
  "Cleaned and inspected are different states and a person sets both.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Room status", "sub": ["occupied, checkout,", "do not disturb"], "icon": "storage"},
      {"title": "Arrivals", "sub": ["and their times"], "icon": "clock"},
      {"title": "Housekeepers", "sub": ["with a phone"], "icon": "person"}],
    "inside": [
      {"title": "Priority", "sub": ["who needs it,", "and when"], "icon": "counter"},
      {"title": "Route", "sub": ["a floor at a time,", "mostly"], "icon": "route"},
      {"title": "Fairness", "sub": ["over weeks,", "not one day"], "icon": "scale"}],
    "edges": [{"from": 0, "to": 0, "label": "statuses"},
              {"from": 1, "to": 1, "label": "arrival times"},
              {"from": 2, "to": 2, "label": "a list, in order", "up": True}],
    "note": "Three constraints that disagree. The design is about how they are traded."}),
   "Three things outside the account, three pieces inside it. None of the three inside boxes wins "
   "outright, and the interesting part is the trade between them.",
   "System: room priority, route and fairness combined into a work list",
   "Three boxes across the top sit outside the AWS account. On the left, Room status: occupied, "
   "checkout, do not disturb. In the middle, Arrivals and their times. On the right, "
   "Housekeepers, each with a phone. Each connects by an arrow to the AWS account container "
   "below. Statuses flow down into the account. Arrival times feed in. A list, in order, goes "
   "back out. Inside the AWS account are three components in a row. On the left, Priority: who "
   "needs it and when. In the middle, Route: a floor at a time, mostly. On the right, Fairness, "
   "measured over weeks rather than one day. A note at the bottom says three constraints that "
   "disagree, and the design is about how they are traded."),
  ("h3", "Three constraints that disagree"),
  ("p", "Priority says clean the room whose guest arrives at two o'clock. Route says clean the "
        "room next door to the one you have just finished. Fairness says the person who did all "
        "the checkouts yesterday should not do them all again today."),
  ("p", "Any system that optimises one of these produces something the housekeeping team will "
        "quietly ignore, and the version that gets used is a compromise that is explicitly a "
        "compromise: mostly route, with priority overriding it where the timing genuinely "
        "requires, and fairness applied when the day's work is allocated rather than within it."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Priority.</strong> Which rooms need to be ready and by when, which is not the same as "
   "which rooms are dirty. Part 2.",
   "<strong>Route.</strong> Ordering the work so the walking is manageable. Part 3.",
   "<strong>Fairness.</strong> Sharing the difficult and the easy over a period. Part 4.",
  ]),
  ("h2", "One morning, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "34 rooms", "sub": ["18 checkouts"], "icon": "storage"},
      {"title": "6 early arrivals", "sub": ["prioritised"], "icon": "clock"},
      {"title": "3 do not disturb", "sub": ["deferred, not skipped"], "icon": "stop"},
      {"title": "Allocated", "sub": ["by floor, then priority"], "icon": "route"},
      {"title": "Balanced", "sub": ["over the week"], "icon": "scale"}],
    "title": "ONE MORNING, END TO END",
    "note": "The third box is not a problem to be solved. It is a rule with no exceptions."}),
   "The same system as one line. The do-not-disturb rooms come back later in the day rather than "
   "being escalated.",
   "One morning of housekeeping allocation in five stages",
   "A horizontal row of five boxes joined by arrows. Thirty-four rooms, eighteen checkouts. Six "
   "early arrivals, prioritised. Three do not disturb, deferred rather than skipped. Allocated by "
   "floor, then priority. Balanced over the week. A note says the third box is not a problem to "
   "be solved but a rule with no exceptions."),
  ("h2", "In plain words"),
  ("p", "Thirty-four rooms need attention: eighteen are checkouts and need a full clean, sixteen "
        "are stayovers. Six guests are arriving before three o'clock and their rooms are "
        "prioritised over the rest."),
  ("p", "Three rooms have do-not-disturb on. They are removed from the morning list entirely, "
        "re-offered at midday, and if they are still showing do-not-disturb at four, a person "
        "makes contact according to whatever the hotel's policy is. The system's involvement ends "
        "at flagging it."),
  ("p", "The remaining rooms are allocated by floor, so each housekeeper works a contiguous "
        "block, with the early-arrival rooms pulled forward within their block. Over the week the "
        "allocation rotates, so the same person does not always get the floor with the family "
        "rooms."),
  ("callout", "Design rules that shaped every decision", [
   "Route first, priority second, except where a genuine deadline requires otherwise.",
   "Do not disturb has no override anywhere in the system.",
   "Fairness is measured over weeks and includes room difficulty, not just room count.",
   "Cleaned and inspected are separate states, both set by a person.",
   "Record how long rooms actually take, so the difficult ones are known.",
   "Never allocate more than the day can hold; an impossible list is ignored entirely.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Housekeeping allocation is usually done on paper by a supervisor who knows the building, "
        "and it is generally done well. The reason to build anything is not that the supervisor "
        "is wrong; it is that the knowledge lives in one person's head, the fairness is hard to "
        "track over weeks, and nobody has ever measured how long the rooms actually take."),
  ("p", "So the system encodes what the good supervisor already does, makes the fairness visible "
        "over a longer period than anybody can hold, and collects timing data that turns "
        "\"room 214 is a nightmare\" into a number."),
  ("p", "The next four posts walk through each piece: how rooms get prioritised, why the route "
        "matters as much as the order, how the work gets shared out fairly, and what ready "
        "actually means. One diagram per post, a cost breakdown, and an engineering reference at "
        "the end."),
 ],
},
{
 "slug": "how-rooms-get-prioritised",
 "title": "How rooms get prioritised",
 "nav": "How rooms are prioritised",
 "read": 5, "words": 740,
 "desc": ("Arrivals against stayovers, the room nobody is waiting for, and do-not-disturb as an "
          "absolute."),
 "og": ("A dirty room with nobody arriving until Thursday is not urgent, however dirty it is."),
 "abstract": ("What actually makes a room urgent, how arrival times drive the order, why "
              "stayovers are different work, and how do-not-disturb is handled without an "
              "override."),
 "lede": ("The instinct is to prioritise by how much cleaning a room needs, and the right answer "
          "is to prioritise by when somebody needs it, which produces a substantially different "
          "list."),
 "tags": ["housekeeping", "prioritisation", "hotel operations", "arrivals", "scheduling",
          "serverless"],
 "takeaways": [
  "Urgency comes from arrival time, not from how dirty the room is.",
  "A checkout with no arrival today can wait until tomorrow.",
  "Stayovers are shorter work and slot around the checkouts.",
  "Do-not-disturb removes a room from dispatch entirely, with no override.",
  "Rooms with a specific request attached need their own flag.",
 ],
 "blocks": [
  ("h2", "What makes a room urgent"),
  ("fig", ("chain", {
    "entry": {"title": "A room needs attention", "sub": ["checkout or stayover"], "icon": "storage"},
    "steps": [
      {"title": "Do not disturb?", "sub": ["checked first, always"], "icon": "branch",
       "exit": {"title": "Removed from dispatch", "sub": ["re-offered later"], "icon": "stop",
                "label": "yes"}},
      {"title": "Arriving guest today?", "sub": ["and at what time"], "icon": "branch",
       "exit": {"title": "Low priority", "sub": ["do it when convenient"], "icon": "clock",
                "label": "no"}},
      {"title": "Before 15:00?", "sub": ["early arrival"], "icon": "branch",
       "exit": {"title": "Standard", "sub": ["ready by check-in"], "icon": "check",
                "label": "no"}},
      {"title": "Any special request?", "sub": ["cot, accessibility, allergy"], "icon": "form"},
      {"title": "Priority, with a time", "sub": ["not a rank"], "icon": "counter"}],
    "note": "The first gate runs before everything else, and its exit has no path back in."}),
   "How a room's urgency is determined. Do-not-disturb is checked before anything else so it can "
   "never be traded against a priority.",
   "How a room's cleaning priority is determined",
   "A vertical chain of five steps entered by a box labelled A room needs attention, whether "
   "checkout or stayover. Step one asks whether do not disturb is set, checked first always; if "
   "so it exits to Removed from dispatch, re-offered later. Step two asks whether a guest is "
   "arriving today and at what time; if not it exits to Low priority, do it when convenient. Step "
   "three asks whether the arrival is before three o'clock, an early arrival; if not it exits to "
   "Standard, ready by check-in. Step four notes any special request such as a cot, accessibility "
   "or an allergy. Step five produces a priority with a time rather than a rank. A note says the "
   "first gate runs before everything else and its exit has no path back in."),
  ("h3", "A time, not a rank"),
  ("p", "Ranking rooms one to thirty-four produces a list that is meaningless the moment anything "
        "changes. A required-by time is stable, survives reallocation, and lets a housekeeper "
        "make a sensible local decision: this room is needed by one o'clock and it is eleven, so "
        "there is time to do the two next door first."),
  ("p", "It also degrades gracefully when the day goes wrong. A list of times makes it obvious "
        "which rooms are now at risk; a rank ordering does not."),
  ("h3", "The room nobody is waiting for"),
  ("p", "A checkout with no arrival for three days is genuinely not urgent, and treating it as "
        "urgent because it is dirty consumes the morning that the six early arrivals needed."),
  ("p", "Those rooms are still on the list, at low priority, and they act as the buffer: when a "
        "day runs short they are the ones that move to tomorrow, deliberately and visibly, rather "
        "than something being dropped at random."),
  ("h2", "Stayovers are different work"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Checkout, standard", "parts": [("mins", 32)]},
      {"label": "Checkout, family", "parts": [("mins", 48)]},
      {"label": "Stayover", "parts": [("mins", 14)]},
      {"label": "Refresh only", "parts": [("mins", 7)]}],
    "series": [("mins", "Measured minutes, median", "#8C4FFF")],
    "unit": "",
    "note": "Measured, not assumed. Most rotas are built on one figure for every room."}),
   "Four kinds of room work with their measured durations. Planning a day on a single average "
   "figure produces a list that is impossible on some days and light on others.",
   "Median measured cleaning times for four kinds of room work",
   "A bar chart with four bars showing median measured minutes. Checkout, standard: thirty-two. "
   "Checkout, family: forty-eight. Stayover: fourteen. Refresh only: seven. A note says these are "
   "measured rather than assumed, and most rotas are built on one figure for every room."),
  ("p", "The gap between fourteen and forty-eight minutes is the reason a day allocated by room "
        "count is unfair and frequently impossible. Eighteen checkouts is a very different day "
        "from eighteen stayovers, and a rota built on rooms per person cannot express that."),
  ("p", "Measuring is straightforward: the housekeeper marks start and finish, which they are "
        "already doing to report a room as cleaned. A few weeks of that produces medians per room "
        "type and eventually per room."),
  ("h2", "Do not disturb"),
  ("callout", "Why there is no override", [
   "<strong>The sign means what it says.</strong> Somebody is asleep, unwell, working, or wants "
   "privacy.",
   "<strong>An override would be used.</strong> Not maliciously, but on a busy day with a "
   "supervisor under pressure, which is exactly when it should not be.",
   "<strong>The room is deferred,</strong> re-offered at a stated time, and deferred again if "
   "still set.",
   "<strong>After a policy threshold</strong> &mdash; often a stated number of hours, or a "
   "welfare check &mdash; a person makes contact.",
   "<strong>That is a human process,</strong> written down by the hotel, and the system's job is "
   "to flag it and record what happened.",
   "<strong>Recording matters:</strong> a room not entered for two days is a welfare question, "
   "and the system should be able to say so.",
  ]),
  ("p", "The last line is the one worth building for. A room with do-not-disturb set continuously "
        "is occasionally a serious situation, and the count of hours since anybody has been in "
        "the room is a number the system can produce and a person can act on."),
  ("h3", "Special requests"),
  ("p", "A cot to be set up, an accessible room to be checked, a guest with an allergy who has "
        "asked for a particular cleaning product. These are not priority in the timing sense; "
        "they are additional work that has to reach the right room."),
  ("p", "They travel with the room rather than with the priority, and they should appear on the "
        "housekeeper's list for that room rather than in a separate briefing that may not reach "
        "the person who actually cleans it."),
  ("p", "Next: the walking."),
 ],
},
{
 "slug": "why-the-route-matters-as-much-as-the-order",
 "title": "Why the route matters as much as the order",
 "nav": "Route and order",
 "read": 5, "words": 720,
 "desc": ("The cost of a lift journey, contiguous blocks, and how much priority is worth trading."),
 "og": ("Forty minutes of a morning in a lift is more than an hour of cleaning lost across a "
        "team, and no rota shows it."),
 "abstract": ("How much walking a priority-ordered list costs, why contiguous blocks work, how "
              "much priority is worth trading, and the trolley constraint nobody models."),
 "lede": ("Housekeeping software tends to optimise the order of rooms and ignore the distance "
          "between them, which produces lists that look excellent and take twenty per cent longer "
          "to work through."),
 "tags": ["housekeeping", "routing", "efficiency", "hotel operations", "scheduling", "serverless"],
 "takeaways": [
  "A floor change costs several minutes each time, and they add up fast.",
  "Allocate contiguous blocks and order within them.",
  "Trading a little priority for a lot of route is almost always right.",
  "The trolley is a constraint: restocking is a journey too.",
  "Measure the walking by counting floor changes; it is the easiest proxy.",
 ],
 "blocks": [
  ("h2", "What the walking costs"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Strict priority", "parts": [("clean", 402), ("move", 88)]},
      {"label": "Route first", "parts": [("clean", 402), ("move", 31)]}],
    "series": [("clean", "Minutes cleaning", "#7AA116"),
               ("move", "Minutes moving between rooms", "#DD344C")],
    "unit": "",
    "note": "Same rooms, same work. Fifty-seven minutes of one person's morning."}),
   "One housekeeper's morning under two orderings. The cleaning time is identical; the difference "
   "is entirely movement.",
   "One housekeeper's morning under strict priority and route-first ordering",
   "A stacked bar chart with two bars in minutes. Two series: minutes cleaning in green, and "
   "minutes moving between rooms in red. Strict priority: four hundred and two minutes cleaning "
   "and eighty-eight moving. Route first: four hundred and two cleaning and thirty-one moving. A "
   "note says same rooms, same work, and fifty-seven minutes of one person's morning."),
  ("p", "Across a team of six that is most of a person-day a week, and it appears nowhere: the "
        "rooms all got cleaned, everybody worked their hours, and the difference is absorbed as "
        "the day running late."),
  ("h3", "Floor changes as the measure"),
  ("p", "Counting floor changes is a good enough proxy for the walking and it needs no floor "
        "plan, no distances and no modelling. A list that involves three floor changes is "
        "considerably better than one involving nine, and that comparison is available "
        "immediately."),
  ("p", "Within a floor, ordering by room number is usually close enough. Corridors are linear, "
        "room numbers follow them, and the marginal gain from anything cleverer is small compared "
        "to the effort of maintaining a floor plan."),
  ("h2", "Blocks, then order"),
  ("fig", ("chain", {
    "entry": {"title": "The day's rooms", "sub": ["with required-by times"], "icon": "storage"},
    "steps": [
      {"title": "Group by floor", "sub": ["and wing where relevant"], "icon": "route"},
      {"title": "Allocate whole blocks", "sub": ["one person, one area"], "icon": "person"},
      {"title": "Order within the block", "sub": ["by required-by time"], "icon": "clock"},
      {"title": "Any room at risk?", "sub": ["cannot be done in time"], "icon": "branch",
       "exit": {"title": "Move that one room", "sub": ["not the whole plan"], "icon": "filter",
                "label": "yes"}},
      {"title": "A list per person", "sub": ["contiguous, timed"], "icon": "form"}],
    "note": "Priority moves individual rooms; it does not reorder the whole day."}),
   "How the two constraints are combined. Priority acts as an exception mechanism rather than as "
   "the primary sort, which is the whole trick.",
   "How rooms are grouped into blocks and ordered within them",
   "A vertical chain of five steps entered by a box labelled The day's rooms with required-by "
   "times. Step one groups by floor, and by wing where relevant. Step two allocates whole blocks, "
   "one person to one area. Step three orders within the block by required-by time. Step four "
   "asks whether any room is at risk of not being done in time; if so it exits to Move that one "
   "room rather than the whole plan. Step five produces a list per person, contiguous and timed. "
   "A note says priority moves individual rooms and does not reorder the whole day."),
  ("h3", "How much priority to trade"),
  ("p", "The practical rule is that a room should only break the route if it would otherwise miss "
        "its required-by time. A room needed by one o'clock that would be reached at half past "
        "twelve on the route order does not need to be pulled forward, and pulling it forward "
        "costs a floor change for no benefit."),
  ("p", "That single rule removes most of the conflict between the two constraints, because most "
        "of the time the route order is already good enough for the deadlines."),
  ("h2", "The trolley"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A trolley holds", "sub": ["about 12 rooms"], "icon": "storage"},
      {"title": "Then a restock", "sub": ["8 minutes, to the store"], "icon": "clock"},
      {"title": "Where is the store?", "sub": ["one floor, usually"], "icon": "route"},
      {"title": "Plan the break", "sub": ["not mid-corridor"], "icon": "form"},
      {"title": "Or a second trolley", "sub": ["cheaper than the walking"], "icon": "check"}],
    "title": "THE CONSTRAINT NOBODY MODELS",
    "note": "Two restocks a shift at eight minutes each is another sixteen minutes per person."}),
   "The trolley capacity constraint. It is invisible in every allocation system and it produces a "
   "predictable journey a couple of times a shift.",
   "How trolley capacity creates additional journeys during a shift",
   "A horizontal row of five boxes. A trolley holds about twelve rooms. Then a restock: eight "
   "minutes, to the store. Where is the store: one floor, usually. Plan the break, not "
   "mid-corridor. Or a second trolley, cheaper than the walking. A note says two restocks a shift "
   "at eight minutes each is another sixteen minutes per person."),
  ("p", "Knowing roughly how many rooms a trolley covers lets the list be broken at a sensible "
        "point &mdash; at the end of a corridor, near the store, between blocks &mdash; rather "
        "than wherever the supplies happen to run out."),
  ("p", "It also quantifies an easy decision. If restocking costs sixteen minutes per person per "
        "shift across six people, a second trolley or a satellite store on another floor pays for "
        "itself quickly, and that is an argument with a number in it."),
  ("h3", "What not to build"),
  ("p", "A full routing optimiser with floor plans, distances and travel-time matrices is "
        "available and is not worth it. The gain over floor blocks and room number ordering is "
        "small, and the maintenance cost of keeping a floor plan current through refurbishments "
        "is real."),
  ("p", "Next: sharing the work out."),
 ],
},
{
 "slug": "how-the-work-gets-shared-out-fairly",
 "title": "How the work gets shared out fairly",
 "nav": "Sharing the work",
 "read": 5, "words": 720,
 "desc": ("Rooms against minutes, the person who always gets the checkouts, and balancing over "
          "weeks rather than days."),
 "og": ("Equal room counts are not equal work. Eighteen checkouts and eighteen stayovers differ "
        "by about five hours."),
 "abstract": ("Why room count is the wrong unit, how difficulty is measured, why fairness is a "
              "weekly rather than daily property, and how the rotation is made visible."),
 "lede": ("Fairness in housekeeping allocation is usually attempted by giving everybody the same "
          "number of rooms, which is a reasonable idea that produces an unfair result almost every "
          "day."),
 "tags": ["housekeeping", "fairness", "workload", "rotas", "hotel operations", "serverless"],
 "takeaways": [
  "Allocate by measured minutes, not by room count.",
  "Some rooms are consistently harder; measure which and share them.",
  "Balance over a week or a month; a single day cannot be fair.",
  "Make the balance visible to the team, or it is not believed.",
  "Never allocate a day that cannot be completed. It gets ignored wholesale.",
 ],
 "blocks": [
  ("h2", "Rooms against minutes"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "A: 14 rooms", "parts": [("mins", 388)]},
      {"label": "B: 14 rooms", "parts": [("mins", 232)]},
      {"label": "C: 14 rooms", "parts": [("mins", 301)]}],
    "series": [("mins", "Measured minutes of work allocated", "#ED7100")],
    "unit": "",
    "note": "Identical room counts. Two and a half hours between the heaviest and lightest."}),
   "Three housekeepers with the same number of rooms. The workload difference is a full "
   "afternoon and it is entirely invisible on a rota that counts rooms.",
   "Three housekeepers with equal room counts and unequal workloads",
   "A bar chart with three bars showing measured minutes of work allocated. Housekeeper A with "
   "fourteen rooms: three hundred and eighty-eight minutes. Housekeeper B with fourteen rooms: "
   "two hundred and thirty-two minutes. Housekeeper C with fourteen rooms: three hundred and one "
   "minutes. A note says identical room counts with two and a half hours between the heaviest and "
   "lightest."),
  ("p", "That difference is felt every day by the person on the left, is invisible to whoever "
        "made the rota, and is the single most common source of resentment in a housekeeping "
        "team. It is also entirely fixable with data that the team is already generating."),
  ("h3", "Measuring difficulty"),
  ("p", "The timing data from Part 2 gives a median per room type and, given enough observations, "
        "per room. Some rooms are consistently slower for structural reasons: an awkward layout, "
        "a bath instead of a shower, a corner room with more surfaces, the family suite."),
  ("p", "Those figures should be per room and per housekeeper-independent, which means using the "
        "median across everybody rather than any individual's times. Otherwise a faster worker "
        "makes a room look easy and then gets allocated it permanently."),
  ("h2", "Fairness is weekly"),
  ("fig", ("chain", {
    "entry": {"title": "Today's rooms", "sub": ["with measured minutes"], "icon": "counter"},
    "steps": [
      {"title": "Equal minutes today?", "sub": ["rarely possible"], "icon": "branch",
       "exit": {"title": "Close enough", "sub": ["within 10%"], "icon": "check", "label": "yes"}},
      {"title": "Who is behind?", "sub": ["over the last 4 weeks"], "icon": "scale",
       "side": {"title": "Running total", "sub": ["minutes, and hard rooms"], "icon": "chart"}},
      {"title": "Give them the lighter", "sub": ["block today"], "icon": "person"},
      {"title": "Rotate the floors", "sub": ["so nobody owns one"], "icon": "route"},
      {"title": "Show the balance", "sub": ["to everybody"], "icon": "doc"}],
    "note": "The last box is what makes it fair rather than merely balanced."}),
   "How the allocation is balanced. The running total over weeks is what allows a heavy day to be "
   "acceptable, and publishing it is what makes the system trusted.",
   "How housekeeping workload is balanced across a team over weeks",
   "A vertical chain of five steps entered by a box labelled Today's rooms with measured minutes. "
   "Step one asks whether equal minutes today is achievable, which is rarely possible; if so it "
   "exits to Close enough, within ten per cent. Step two asks who is behind over the last four "
   "weeks, drawing on a side box showing a running total of minutes and hard rooms. Step three "
   "gives them the lighter block today. Step four rotates the floors so nobody owns one. Step "
   "five shows the balance to everybody. A note says the last box is what makes it fair rather "
   "than merely balanced."),
  ("h3", "Publishing the balance"),
  ("p", "A running total that only the supervisor can see is a fairness claim rather than a "
        "fairness mechanism. Showing each person their own four-week total against the team "
        "average converts an argument about today into a conversation about a number everybody "
        "can check."),
  ("p", "It also surfaces genuine differences honestly. Somebody working part time has a lower "
        "total and should; somebody on lighter duties for a medical reason has a lower total and "
        "should; both are visible and neither is a secret being kept."),
  ("h3", "Rotating the floors"),
  ("p", "Beyond minutes there is a qualitative fairness: the floor with the function room and the "
        "constant traffic, the floor with the family rooms, the top floor with the difficult "
        "lift. Rotating whole blocks weekly handles it without needing anybody to quantify how "
        "unpleasant a floor is."),
  ("h2", "The impossible day"),
  ("fig", ("strip", {
    "stages": [
      {"title": "34 rooms", "sub": ["1,090 minutes of work"], "icon": "counter"},
      {"title": "5 people", "sub": ["7 hours each = 2,100"], "icon": "person"},
      {"title": "Fits", "sub": ["with room to spare"], "icon": "check"},
      {"title": "But 41 rooms", "sub": ["would not"], "icon": "alarm"},
      {"title": "Say so before", "sub": ["not at four o'clock"], "icon": "email"}],
    "title": "SAYING IT WILL NOT FIT",
    "note": "An impossible list is not worked through; it is abandoned and improvised around."}),
   "The capacity check. Producing a list that cannot be completed causes the whole allocation to "
   "be ignored, which is worse than allocating less.",
   "How a day's workload is checked against available hours",
   "A horizontal row of five boxes. Thirty-four rooms: one thousand and ninety minutes of work. "
   "Five people at seven hours each: two thousand one hundred minutes. Fits, with room to spare. "
   "But forty-one rooms would not. Say so before, not at four o'clock. A note says an impossible "
   "list is not worked through but abandoned and improvised around."),
  ("p", "Naming the shortfall in the morning gives the options: agree which low-priority rooms "
        "move to tomorrow, call somebody in, or accept later check-in times for specific rooms. "
        "All three are decisions. Discovering it at four o'clock is not."),
  ("p", "The low-priority checkouts from Part 2 are the natural buffer, and moving them "
        "explicitly is much better than the alternative, which is somebody choosing at speed and "
        "occasionally choosing a room with a guest arriving."),
  ("p", "Next: what ready actually means."),
 ],
},
{
 "slug": "what-ready-actually-means",
 "title": "What ready actually means, and who says it",
 "nav": "What ready means",
 "read": 5, "words": 710,
 "desc": ("Cleaned against inspected, why a person sets both, and the maintenance issue found "
          "mid-clean."),
 "og": ("A room that has been cleaned is not necessarily a room that can be sold. Two states, two "
        "people, and a reason."),
 "abstract": ("Why cleaned and inspected are separate states, who sets each, how maintenance "
              "issues are captured, and what happens when reception needs a room that is not "
              "ready."),
 "lede": ("The final state of every room in this system is set by a person looking at it, and "
          "resisting the temptation to infer it is what makes the whole thing trustworthy to "
          "reception."),
 "tags": ["housekeeping", "quality", "inspection", "hotel operations", "maintenance", "serverless"],
 "takeaways": [
  "Cleaned and inspected are different states with different meanings.",
  "Neither is ever set automatically, by a timer or by anything else.",
  "A maintenance issue found mid-clean is a different workflow and needs one tap.",
  "Reception sees the state and the time it was set, not a prediction.",
  "Inspection rates can fall over time; measure them.",
 ],
 "blocks": [
  ("h2", "Two states"),
  ("table", ["State", "Set by", "Means"], [
   ["Dirty", "Checkout, or the day rolling over", "Needs attention"],
   ["In progress", "The housekeeper starting", "Somebody is in there"],
   ["Cleaned", "The housekeeper finishing", "The work is done, in their judgement"],
   ["Inspected", "A supervisor, or a sampled check", "Verified, and sellable"],
   ["Out of order", "Anybody who finds a fault", "Not sellable until fixed"],
  ]),
  ("p", "The distinction between cleaned and inspected matters most at the moment reception is "
        "under pressure. A guest is waiting, a room shows cleaned but not inspected, and somebody "
        "has to decide whether to give it out. That is a judgement, and it is only possible if "
        "the two states are separate."),
  ("p", "Collapsing them into one loses that option in both directions: either every room waits "
        "for an inspection that may be twenty minutes away, or no room is ever verified."),
  ("h3", "Never inferred"),
  ("p", "A room does not become cleaned because a timer expired, because the housekeeper's list "
        "moved on, or because the average clean time has passed. It becomes cleaned when somebody "
        "says it is."),
  ("p", "This sounds obvious and the pressure to infer it is real, because housekeepers forget to "
        "mark rooms and reception wants current information. The correct fix is making the "
        "marking take one tap, not guessing."),
  ("h2", "The maintenance issue"),
  ("fig", ("chain", {
    "entry": {"title": "Something is wrong", "sub": ["found mid-clean"], "icon": "search"},
    "steps": [
      {"title": "One tap to report", "sub": ["from the room list"], "icon": "form"},
      {"title": "Photograph optional", "sub": ["usually taken"], "icon": "image"},
      {"title": "Can the room be sold?", "sub": ["the housekeeper decides"], "icon": "branch",
       "exit": {"title": "Out of order", "sub": ["reception sees it now"], "icon": "stop",
                "label": "no"}},
      {"title": "Cleaned, with a note", "sub": ["sellable, but flagged"], "icon": "check"},
      {"title": "To maintenance", "sub": ["as a job, not a note"], "icon": "gear"}],
    "note": "The third gate is a judgement and the housekeeper is the person who can make it."}),
   "How a fault found during cleaning is handled. The judgement about sellability sits with the "
   "person standing in the room, which is the only place it can sit.",
   "How a maintenance issue found during cleaning is reported",
   "A vertical chain of five steps entered by a box labelled Something is wrong, found mid-clean. "
   "Step one takes one tap to report from the room list. Step two takes an optional photograph, "
   "usually taken. Step three asks whether the room can be sold, with the housekeeper deciding; "
   "if not it exits to Out of order, which reception sees immediately. Step four marks it cleaned "
   "with a note, sellable but flagged. Step five sends it to maintenance as a job rather than a "
   "note. A note says the third gate is a judgement and the housekeeper is the person who can "
   "make it."),
  ("h3", "A job, not a note"),
  ("p", "Maintenance issues reported as free text in a housekeeping system go nowhere. Creating "
        "an actual job, in whatever the maintenance process is, is what makes the report worth "
        "making, and a housekeeper who reports three things that are never fixed stops "
        "reporting."),
  ("p", "This is the same principle as the deferral record in Day 118: the reporting mechanism "
        "only survives if the reports visibly lead somewhere."),
  ("h2", "What reception sees"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Room 214", "sub": ["cleaned 11:42"], "icon": "storage"},
      {"title": "Not yet inspected", "sub": ["stated plainly"], "icon": "search"},
      {"title": "No prediction", "sub": ["no 'ready in 10 mins'"], "icon": "stop"},
      {"title": "One flagged issue", "sub": ["shower pressure"], "icon": "alarm"},
      {"title": "Reception decides", "sub": ["with the facts"], "icon": "person"}],
    "title": "WHAT THE FRONT DESK SEES",
    "note": "A predicted ready time will be quoted to a guest and then missed."}),
   "The room state as reception sees it. Every element is an observed fact with a timestamp, and "
   "there is no estimate anywhere.",
   "What reception sees about a room's readiness state",
   "A horizontal row of five boxes. Room two one four: cleaned at eleven forty-two. Not yet "
   "inspected, stated plainly. No prediction, and no ready in ten minutes. One flagged issue: "
   "shower pressure. Reception decides, with the facts. A note says a predicted ready time will "
   "be quoted to a guest and then missed."),
  ("p", "The absence of a prediction is the same principle as the delivery exception handler in "
        "Day 116: an estimated time will be passed on to a guest as a promise, and a promise "
        "based on an average is broken often enough to be worse than the honest answer."),
  ("h3", "Measuring inspection"),
  ("p", "Inspection rates fall over time, quietly, because inspecting is the thing that gets "
        "dropped on a busy day. A hotel that believes it inspects every room and actually "
        "inspects sixty per cent of them has a quality process that exists mainly in a policy "
        "document."),
  ("p", "Counting is free once the states are separate: what proportion of rooms went from "
        "cleaned to inspected, and how long the gap was. Both numbers are worth putting in front "
        "of somebody monthly."),
  ("h3", "What this system does not do"),
  ("p", "It does not set states automatically, it does not predict ready times, it does not "
        "override do-not-disturb, and it does not rank people by speed. The last one is worth "
        "stating: the timing data exists to allocate work fairly, and turning it into a "
        "productivity ranking would make everybody stop marking rooms accurately, which destroys "
        "the data the fairness depends on."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="room-day",
 volumes=[(1500, "1,500 room-days"), (6000, "6,000 room-days"), (24000, "24,000 room-days")],
 read_each=0.0,
 msgs_each=0.0,
 lede=("There is no model in this system and nothing is emailed: the output is a list on a phone. "
       "Six thousand room-days a month is a two-hundred-room hotel. Here is where each cent goes."),
 takeaway_extra=("State changes and the morning allocation are the whole workload, and both are "
                 "trivial at hotel scale."),
 risks=[
  "<strong>Polling for room status from the device.</strong> Push the allocation once and let "
  "state changes flow the other way; a phone polling every ten seconds across a team is the only "
  "way to make this expensive.",
  "<strong>Storing every state transition forever.</strong> The timing data is valuable for a "
  "year and not after. Roll up to per-room medians and expire the transitions.",
  "<strong>Reallocating continuously through the day.</strong> Allocate in the morning and adjust "
  "by exception; a list that changes under somebody is not usable.",
 ],
 per_unit_note=("There is no read line and no messaging line. Compute for the morning allocation "
                "and writes for state changes are the entire variable cost."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="hk",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the allocation pass, and the state model."),
 outside=[
  {"title": "The PMS", "sub": ["arrivals, checkouts,", "read only"], "icon": "database"},
  {"title": "Housekeeper phones", "sub": ["list and state changes"], "icon": "person"},
  {"title": "Reception", "sub": ["room states, live"], "icon": "form"}],
 inside=[
  {"title": "API + EventBridge", "sub": ["state changes,", "morning allocation"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["allocate, state, balance"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["rooms, workload"], "icon": "database"}],
 note="us-east-1. One account. No state is ever set by a timer; do-not-disturb has no override.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The property management system providing "
  "arrivals and checkouts, read only. Housekeeper phones, receiving the list and sending state "
  "changes. And Reception, seeing room states live. Inside the account, three groups. An API for "
  "state changes and EventBridge running the morning allocation. Three Lambda functions named "
  "allocate, state and balance. And two DynamoDB tables named rooms and workload. A note gives "
  "the region as us-east-1, one account, and states that no state is ever set by a timer and "
  "do-not-disturb has no override."),
 functions=[
  ["<code>hk-allocate</code>", "EventBridge, each morning",
   "Groups by floor, allocates blocks by measured minutes against the four-week balance, orders "
   "by required-by time", "120s / 1024&nbsp;MB"],
  ["<code>hk-state</code>", "API, from the phones",
   "Records state transitions with a person and a timestamp; creates maintenance jobs",
   "10s / 512&nbsp;MB"],
  ["<code>hk-balance</code>", "EventBridge, nightly",
   "Updates per-room median durations and each person's running workload total",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>hk-allocate-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>",
   "Read-only on the PMS mirror; both tables"],
  ["<code>hk-state-role</code>", "<code>dynamodb:UpdateItem</code>, <code>sqs:SendMessage</code>",
   "Rooms; the maintenance queue"],
  ["<code>hk-balance-role</code>", "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>",
   "Both tables"]],
 tables=[
  ("Table: rooms",
   "PK   room_id           S   214\n"
   "     floor             N   2\n"
   "     state             S   dirty | in_progress | cleaned | inspected | ooo\n"
   "     state_set_by      S   a person, always; never a timer\n"
   "     state_set_at      S\n"
   "     dnd_since         S   set from the door or the PMS; no override exists\n"
   "     hours_unentered   N   computed; a welfare signal past a threshold\n"
   "     required_by       S   from the arrival, or null\n"
   "     work_type         S   checkout | stayover | refresh\n"
   "     median_minutes    N   across all housekeepers, not one\n"
   "     requests          L   cot, accessibility, allergy\n"
   "     flags             L   [{issue, photo_key, at, by}]\n\n"
   "`median_minutes` is deliberately person-independent. Using an\n"
   "individual's times makes a fast worker permanently own the hard rooms."),
  ("Table: workload",
   "PK   person_id         S\n"
   "SK   date              S\n"
   "     minutes_allocated N\n"
   "     minutes_actual    N   from the state transitions\n"
   "     rooms             N   recorded, but not the allocation unit\n"
   "     hard_rooms        N   count above a difficulty threshold\n"
   "     floor             N   for the rotation\n"
   "     rolling_28d       N   the number the balance is computed on\n\n"
   "`rolling_28d` is shown to each person. A fairness total that only a\n"
   "supervisor can see is a claim rather than a mechanism.")],
 inbound=[
  "<strong>Arrivals, checkouts and do-not-disturb come from the property management system</strong>, "
  "read only. This system writes nothing back to it.",
  "<strong>State changes come from the phones</strong>, one tap, always carrying the person and "
  "the time. There is no path that sets a state without a person.",
  "<strong>Allocation runs once in the morning</strong> and adjusts by exception. A list that "
  "reorders itself under somebody is not usable.",
  "<strong>Maintenance flags create jobs</strong> in whatever the maintenance process is, not "
  "notes in this system. A report that goes nowhere stops being made."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Allocation is grouping and sorting; "
  "difficulty is a median.",
  "<strong>The tempting use</strong> is predicting when a room will be ready. Part 5 is about why "
  "no prediction appears anywhere: it will be quoted to a guest as a promise.",
  "<strong>A second tempting use</strong> is scoring housekeeper productivity. It would make "
  "everybody mark rooms inaccurately, which destroys the timing data the fairness depends on.",
  "<strong>A defensible use</strong> is classifying photographed maintenance issues into trades, "
  "so the job reaches the right person.",
  "<strong>The cost page assumes none</strong>, which is why the bill is fixed."],
 gotchas=[
  "Allocate by measured minutes, never by room count. Fourteen checkouts and fourteen stayovers "
  "differ by about two and a half hours.",
  "Group by floor before applying priority. A strictly priority-ordered list costs the better "
  "part of an hour per person in movement.",
  "Give do-not-disturb no override in any code path. On a busy day an override exists to be used, "
  "which is exactly when it should not be.",
  "Never set a state from a timer or an inference. One tap from a person, or the state does not "
  "change.",
  "Publish the rolling workload balance to the team. A fairness figure only the supervisor sees "
  "does not produce the trust the system depends on."],
))
