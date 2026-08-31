"""Day 118 -- 2026-08-20 -- Equipment maintenance scheduler."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "equipment-maintenance-scheduler"
NAME = "Equipment maintenance scheduler"

SPEC = {
 "slug": SLUG, "date": "2026-08-20", "name": NAME,
 "tagline": ("Schedules servicing against how much a machine has actually been used rather than "
             "what month it is, makes deferring a job an explicit recorded decision, and keeps "
             "the inspections that cannot be deferred somewhere they cannot be missed."),
 "lede": ("A small system that tracks running hours, decides when each machine is due, and "
          "handles the thing every maintenance system pretends does not happen: jobs get put off, "
          "usually for good reasons, and the deferral is where the risk accumulates. Seven posts "
          "on the same system, one diagram at a time, with a cost breakdown and an engineering "
          "reference at the end."),
 "keywords": ["maintenance", "preventive maintenance", "equipment", "compliance", "scheduling",
              "serverless"],
 "icons": ["gear", "clock", "check"],
 "faq": [
  ("What is an equipment maintenance scheduler?",
   "A small serverless system that tracks equipment usage, works out what is due, records "
   "deferrals explicitly, and keeps statutory inspections separate from discretionary servicing."),
  ("Why schedule on running hours instead of months?",
   "Because a machine that ran four hundred hours needs the same attention as one that ran four "
   "hundred hours, regardless of whether that took two months or eight."),
  ("Is deferring maintenance always bad?",
   "No, and pretending otherwise is why deferrals get hidden. The post on this argues for making "
   "deferral a first-class recorded decision with a name on it."),
  ("What is a statutory inspection?",
   "An inspection required by regulation rather than by the manufacturer -- lifting equipment, "
   "pressure systems, electrical testing. They cannot be deferred and are handled separately."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "equipment-maintenance-scheduler-on-aws",
 "title": "An equipment maintenance scheduler on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Schedules servicing on usage, records deferrals explicitly, and protects the "
          "statutory inspections. AWS, about $2 a month."),
 "og": ("Every maintenance system assumes jobs get done when scheduled. The interesting design "
        "is what happens when they do not."),
 "abstract": ("The whole system on one page -- usage, due, deferred &mdash; and the deliberate "
              "decision to treat deferral as normal rather than as an exception."),
 "lede": ("The service was due in March. March was the busiest month of the year, so it slipped "
          "to April, and April slipped to May because the part was on back order, and in June the "
          "bearing failed during a production run. Nobody made a bad decision at any point; there "
          "was simply no place where the accumulated slippage was visible. This post walks "
          "through a small system built around that."),
 "tags": ["maintenance", "preventive maintenance", "equipment", "compliance", "scheduling",
          "serverless"],
 "takeaways": [
  "Schedule on running hours where they exist, on calendar where they do not.",
  "Deferral is normal and must be recorded with a reason and a name.",
  "Statutory inspections are a separate track and cannot be deferred at all.",
  "Over-maintenance is a real cost, and intervention itself causes failures.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "The machines", "sub": ["hours, cycles,", "or nothing at all"], "icon": "gear"},
      {"title": "Schedules", "sub": ["manufacturer,", "and statutory"], "icon": "doc"},
      {"title": "Whoever does the work", "sub": ["and whoever defers it"], "icon": "person"}],
    "inside": [
      {"title": "Usage tracker", "sub": ["hours since last,", "not months"], "icon": "counter"},
      {"title": "Due list", "sub": ["what, when,", "and how urgently"], "icon": "clock"},
      {"title": "Deferral record", "sub": ["who, why,", "and until when"], "icon": "database"}],
    "edges": [{"from": 0, "to": 0, "label": "readings"},
              {"from": 1, "to": 1, "label": "intervals and rules"},
              {"from": 2, "to": 2, "label": "a short list, and a debt", "up": True}],
    "note": "The third box exists because the first two are the easy part."}),
   "Three things outside the account, three pieces inside it. Most maintenance systems build the "
   "first two and treat the third as an edge case, which is backwards.",
   "System: equipment usage tracked, jobs scheduled, deferrals recorded",
   "Three boxes across the top sit outside the AWS account. On the left, The machines, reporting "
   "hours, cycles, or nothing at all. In the middle, Schedules from the manufacturer and from "
   "statute. On the right, Whoever does the work, and whoever defers it. Each connects by an "
   "arrow to the AWS account container below. Readings flow down into the account. Intervals and "
   "rules feed in. A short list, and a debt, go back out. Inside the AWS account are three "
   "components in a row. On the left, the Usage tracker, counting hours since last service rather "
   "than months. In the middle, the Due list, showing what, when and how urgently. On the right, "
   "the Deferral record, capturing who, why and until when. A note at the bottom says the third "
   "box exists because the first two are the easy part."),
  ("h3", "Deferral is the design problem"),
  ("p", "Every maintenance system schedules jobs. The ones that fail in practice fail because "
        "reality intervenes: the machine is needed, the engineer is ill, the part has not arrived, "
        "the job is genuinely less urgent than the thing it would displace."),
  ("p", "When there is no way to record that, the job simply stays overdue, the overdue list grows "
        "until it is meaningless, and everybody starts ignoring it. Making deferral a real action "
        "with a reason and a new date keeps the list short enough to be believed, and turns the "
        "accumulated slippage into something visible."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The usage tracker.</strong> Records running hours or cycles and works out how much "
   "each machine has done since it was last serviced. Part 2.",
   "<strong>The due list.</strong> A short, ordered list of what needs doing, with its urgency "
   "and its consequence. Part 2.",
   "<strong>The deferral record.</strong> Who moved a job, why, until when, and what the "
   "cumulative picture looks like. Parts 3, 4 and 5.",
  ]),
  ("h2", "One machine, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Serviced at 4,200h", "sub": ["interval 500h"], "icon": "gear"},
      {"title": "Now at 4,640h", "sub": ["88% through"], "icon": "counter"},
      {"title": "Due", "sub": ["appears at 90%"], "icon": "clock"},
      {"title": "Deferred", "sub": ["+2 weeks, part on order"], "icon": "doc"},
      {"title": "Visible as debt", "sub": ["until it is done"], "icon": "alarm"}],
    "title": "ONE MACHINE, END TO END",
    "note": "The fourth box is a legitimate decision. The fifth is what stops it becoming three."}),
   "The same system as one line. The deferral in the fourth box is fine; the mechanism in the "
   "fifth is what keeps it from repeating quietly.",
   "One machine from service due through to a recorded deferral",
   "A horizontal row of five boxes joined by arrows. Serviced at four thousand two hundred hours, "
   "with a five hundred hour interval. Now at four thousand six hundred and forty hours, eighty-"
   "eight per cent through. Due: appears at ninety per cent. Deferred: two weeks, part on order. "
   "Visible as debt until it is done. A note says the fourth box is a legitimate decision, and "
   "the fifth is what stops it becoming three."),
  ("h2", "In plain words"),
  ("p", "A machine was last serviced at four thousand two hundred running hours and the interval "
        "is five hundred hours. It has now done four hundred and forty since, which is eighty-"
        "eight per cent of the way. At ninety per cent it appears on the due list, which is early "
        "enough to arrange and late enough not to clutter."),
  ("p", "The part needed is on back order, so the job is deferred by two weeks with that reason "
        "and the name of whoever decided. It stays on the list, marked deferred rather than "
        "overdue, and the reason is visible next to it."),
  ("p", "If it is deferred again the system says so explicitly: second deferral, now at a hundred "
        "and twelve per cent of interval. A third deferral triggers a different conversation. "
        "Nothing is blocked, nothing is automated, and the accumulated position is impossible to "
        "lose track of."),
  ("callout", "Design rules that shaped every decision", [
   "Usage where it exists, calendar where it does not, and say which is being used.",
   "Deferral is a recorded action with a reason, a name and a new date.",
   "Statutory inspections are a separate track with no deferral action at all.",
   "The due list is short. Anything longer than a day's work is not a list, it is a backlog.",
   "Never auto-close a job. A completed job is somebody saying they did it.",
   "Record the parts needed with the job, because parts are why most deferrals happen.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Maintenance software is usually built around the work order and treats scheduling as "
        "arithmetic. That is the wrong emphasis for a small operation, where the arithmetic is "
        "trivial and the actual difficulty is that there are more jobs than hours and somebody "
        "has to choose."),
  ("p", "So this design puts its weight on making that choice visible: what is due, what has been "
        "put off, how far past due things are, and which machine keeps appearing. The scheduling "
        "is the easy half and it is not where the failures come from."),
  ("p", "The next four posts walk through each piece: how the interval gets decided, how a "
        "deferral gets recorded, which jobs cannot be deferred, and what the history tells you. "
        "One diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-the-interval-gets-decided",
 "title": "How the interval gets decided",
 "nav": "How the interval works",
 "read": 5, "words": 740,
 "desc": ("Running hours against calendar months, machines that count nothing, and why "
          "over-maintenance is a real cost."),
 "og": ("A machine that ran four hundred hours needs a service, whether that took two months or "
        "eight. The calendar is a proxy for usage and often a poor one."),
 "abstract": ("Why usage beats calendar, how to handle equipment that reports nothing, the "
              "whichever-comes-first rule, and the case against servicing too often."),
 "lede": ("Most maintenance is scheduled monthly because months are easy to put in a spreadsheet, "
          "and for equipment whose use varies that produces both unnecessary servicing and missed "
          "servicing at the same time."),
 "tags": ["maintenance", "intervals", "usage", "scheduling", "equipment", "serverless"],
 "takeaways": [
  "Running hours or cycles beat calendar months wherever the machine counts them.",
  "Whichever comes first: some things degrade with time even when idle.",
  "Machines that count nothing get a proxy -- output, shifts run, or a manual reading.",
  "Servicing too often costs money and introduces failures of its own.",
  "Say on every job which basis it was scheduled on.",
 ],
 "blocks": [
  ("h2", "Usage against calendar"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Machine A, busy", "parts": [("used", 620), ("idle", 0)]},
      {"label": "Machine B, average", "parts": [("used", 410), ("idle", 0)]},
      {"label": "Machine C, spare", "parts": [("used", 95), ("idle", 0)]}],
    "series": [("used", "Running hours in six months", "#ED7100"),
               ("idle", "", "#7D8CA3")],
    "unit": "",
    "note": "On a six-month schedule all three get one service. A needs two; C needs none."}),
   "Three identical machines over the same six months. A calendar schedule treats them the same "
   "and is wrong about two of them in opposite directions.",
   "Running hours over six months for three identical machines",
   "A bar chart with three bars showing running hours over six months. Machine A, busy: six "
   "hundred and twenty hours. Machine B, average: four hundred and ten hours. Machine C, a spare: "
   "ninety-five hours. A note says on a six-month schedule all three get one service, while A "
   "needs two and C needs none."),
  ("p", "Machine C is the interesting case. Servicing it on the calendar means paying for work "
        "that is not needed, and every intervention carries a small risk of introducing a problem "
        "that was not there. Servicing lightly-used equipment on schedule is not caution; it is "
        "cost with a failure mode attached."),
  ("h3", "Whichever comes first"),
  ("p", "Usage alone is not sufficient either, because some things degrade with time regardless: "
        "rubber perishes, oil oxidises, seals dry out, batteries self-discharge. The practical "
        "rule is an interval in hours and a maximum in months, whichever arrives first."),
  ("p", "Machine C then gets serviced annually rather than never, on the calendar limit, and the "
        "job record says which limit triggered it. That distinction is worth keeping because a "
        "machine that is always triggered on calendar is a machine you may not need."),
  ("h2", "Machines that count nothing"),
  ("fig", ("chain", {
    "entry": {"title": "A machine to schedule", "sub": ["what does it report?"], "icon": "gear"},
    "steps": [
      {"title": "An hour meter?", "sub": ["most plant has one"], "icon": "branch",
       "exit": {"title": "Read it", "sub": ["automatically or weekly"], "icon": "counter",
                "label": "yes"}},
      {"title": "A cycle counter?", "sub": ["presses, doors, pumps"], "icon": "branch",
       "exit": {"title": "Use cycles", "sub": ["often better than hours"], "icon": "counter",
                "label": "yes"}},
      {"title": "A proxy available?", "sub": ["output, shifts, distance"], "icon": "branch",
       "exit": {"title": "Use it, and say so", "sub": ["approximate, not fake"], "icon": "search",
                "label": "yes"}},
      {"title": "Calendar only", "sub": ["with a stated assumption"], "icon": "clock"},
      {"title": "Record the basis", "sub": ["on every scheduled job"], "icon": "doc"}],
    "note": "A proxy that is honest about being a proxy beats a precise number that is invented."}),
   "How the scheduling basis is chosen per machine. The last box is what stops a proxy quietly "
   "becoming treated as a measurement.",
   "How the scheduling basis is chosen for a piece of equipment",
   "A vertical chain of five steps entered by a box labelled A machine to schedule, asking what "
   "it reports. Step one asks whether there is an hour meter, which most plant has; if so it "
   "exits to Read it, automatically or weekly. Step two asks whether there is a cycle counter for "
   "presses, doors or pumps; if so it exits to Use cycles, often better than hours. Step three "
   "asks whether a proxy is available such as output, shifts or distance; if so it exits to Use "
   "it and say so, approximate rather than fake. Step four falls back to calendar only, with a "
   "stated assumption. Step five records the basis on every scheduled job. A note says a proxy "
   "that is honest about being a proxy beats a precise number that is invented."),
  ("h3", "Cycles beat hours sometimes"),
  ("p", "For anything that starts and stops &mdash; a press, a compressor, a door, a pump &mdash; "
        "the wear is in the cycles rather than the hours. A compressor running continuously for "
        "eight hours does less damage to itself than one starting forty times in the same period."),
  ("p", "Where both are available, the interval should be on whichever the manufacturer specifies "
        "and the other recorded alongside, because the ratio between them is itself diagnostic. A "
        "compressor whose cycles per hour have doubled has a leak somewhere."),
  ("h2", "Over-maintenance is real"),
  ("callout", "The costs of servicing too often", [
   "<strong>The direct cost:</strong> parts and labour for work that was not needed.",
   "<strong>The downtime:</strong> a machine stopped for a service it did not need is a machine "
   "stopped.",
   "<strong>Intervention failures:</strong> a proportion of failures happen shortly after "
   "maintenance, because somebody was inside the machine.",
   "<strong>The crying wolf effect:</strong> a schedule full of unnecessary jobs teaches people "
   "that the schedule is negotiable.",
   "<strong>The right response</strong> is to lengthen intervals where the evidence supports it, "
   "recorded as a deliberate change with a reason.",
   "<strong>Not</strong> to quietly skip jobs, which produces the same saving and none of the "
   "knowledge.",
  ]),
  ("p", "The third line is the one people find counter-intuitive and it is well established. "
        "Opening a machine up, disturbing settled assemblies and reassembling them introduces a "
        "small failure rate, which is why the interval should be as long as the evidence "
        "supports rather than as short as caution suggests."),
  ("p", "This is also the argument for recording completed jobs with what was found. A service "
        "where nothing needed replacing, three times running, is evidence that the interval could "
        "be longer, and that evidence only exists if somebody wrote down that nothing was wrong."),
  ("p", "Next: what happens when a job gets put off."),
 ],
},
{
 "slug": "how-a-deferral-gets-recorded",
 "title": "How a deferral gets recorded",
 "nav": "How deferral works",
 "read": 6, "words": 770,
 "desc": ("Why deferral is normal, what a deferral record contains, and what happens on the "
          "second and third one."),
 "og": ("A maintenance system with no deferral button does not have fewer deferrals. It has "
        "invisible ones."),
 "abstract": ("Why deferral must be a first-class action, what the record contains, how repeated "
              "deferrals escalate, and how the accumulated debt is reported."),
 "lede": ("This is the post that matters. A scheduler that only knows done and overdue will show "
          "an overdue list of forty items within six months, at which point it has stopped being "
          "information."),
 "tags": ["maintenance", "deferral", "risk", "operations", "records", "serverless"],
 "takeaways": [
  "Deferral is a button, not a failure. Without one, jobs go overdue and stay there.",
  "A deferral needs a reason, a name and a new date. All three.",
  "The second deferral of the same job is a different event and is shown as one.",
  "Percentage past interval is more useful than days overdue.",
  "Report the total deferred, not just the count. It is a debt.",
 ],
 "blocks": [
  ("h2", "The deferral record"),
  ("fig", ("chain", {
    "entry": {"title": "A due job", "sub": ["cannot be done now"], "icon": "clock"},
    "steps": [
      {"title": "Is it statutory?", "sub": ["checked first"], "icon": "branch",
       "exit": {"title": "No deferral available", "sub": ["a different conversation"],
                "icon": "lock", "label": "yes"}},
      {"title": "Reason", "sub": ["from a short list,", "plus free text"], "icon": "doc"},
      {"title": "New date", "sub": ["not 'later'"], "icon": "clock"},
      {"title": "Whose decision?", "sub": ["a named person"], "icon": "person"},
      {"title": "How many times now?", "sub": ["shown on the record"], "icon": "counter",
       "side": {"title": "Third deferral", "sub": ["escalates"], "icon": "alarm"}}],
    "note": "Requiring a date is what stops deferral becoming an indefinite postponement."}),
   "What a deferral requires. Each field removes a way for a deferred job to disappear.",
   "How a maintenance job deferral is recorded",
   "A vertical chain of five steps entered by a box labelled A due job that cannot be done now. "
   "Step one asks whether it is statutory, checked first; if so it exits to No deferral available, "
   "which is a different conversation. Step two records a reason from a short list plus free text. "
   "Step three requires a new date, not simply later. Step four records whose decision it was, a "
   "named person. Step five shows how many times it has now been deferred, with a side box noting "
   "that a third deferral escalates. A note says requiring a date is what stops deferral becoming "
   "an indefinite postponement."),
  ("h3", "Reasons from a short list"),
  ("p", "Five or six options cover almost everything: part not available, machine in use, no "
        "engineer available, weather, waiting on a third party, deprioritised. A short list makes "
        "the aggregate analysis possible, and the free text next to it captures the specifics."),
  ("p", "The distribution of those reasons over a year is one of the more useful outputs of the "
        "whole system. If half of all deferrals are parts availability, the fix is a stock policy "
        "rather than a scheduling change, and that is not obvious from any individual deferral."),
  ("h2", "Percentage, not days"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Pump, 14 days over", "parts": [("pct", 104)]},
      {"label": "Press, 14 days over", "parts": [("pct", 131)]},
      {"label": "Chiller, 40 days over", "parts": [("pct", 108)]}],
    "series": [("pct", "Percentage of interval used", "#DD344C")],
    "unit": "",
    "note": "Days overdue ranks these wrongly. The press is the urgent one, at 131%."}),
   "Three overdue jobs measured two ways. Days overdue puts the chiller at the top; percentage of "
   "interval used correctly puts the press there.",
   "Three overdue maintenance jobs measured as a percentage of interval",
   "A bar chart with three bars showing the percentage of the service interval used. A pump "
   "fourteen days over is at one hundred and four per cent. A press fourteen days over is at one "
   "hundred and thirty-one per cent. A chiller forty days over is at one hundred and eight per "
   "cent. A note says days overdue ranks these wrongly, and the press is the urgent one at one "
   "hundred and thirty-one per cent."),
  ("p", "The press is fourteen days over and thirty-one per cent past its interval because it is "
        "in heavy use; the chiller is forty days over and barely past interval because it has "
        "hardly run. Sorting the overdue list by days produces exactly the wrong order of work."),
  ("p", "This is a small change to a sort key and it changes which machine gets attention on a "
        "busy Tuesday, which over a year is most of what a maintenance system is for."),
  ("h2", "The second and third deferral"),
  ("callout", "What changes each time", [
   "<strong>First deferral:</strong> recorded, shown as deferred rather than overdue, no fuss.",
   "<strong>Second deferral:</strong> the record shows both reasons and the original due date. "
   "Still routine.",
   "<strong>Third deferral:</strong> goes to whoever owns the equipment, not just the maintenance "
   "list, with the full history.",
   "<strong>Beyond that:</strong> the job appears on the monthly report by name, every month, "
   "until it is closed.",
   "<strong>Nothing is ever blocked.</strong> The escalation is visibility, not permission.",
   "<strong>Because the alternative</strong> is that people stop recording deferrals and go back "
   "to silently skipping.",
  ]),
  ("p", "That last point is the design principle behind the whole feature. Any mechanism that "
        "makes deferring painful will be routed around, and a routed-around deferral is invisible, "
        "which is the situation the system exists to prevent. Escalating visibility is the only "
        "pressure that does not create an incentive to hide."),
  ("h3", "Deferral is not always wrong"),
  ("p", "A machine that is about to be replaced, a service that would displace a job with a "
        "genuine deadline, a part that will arrive in a week &mdash; deferring in those cases is "
        "correct, and a system that treats every deferral as a failure is asking people to lie "
        "about their reasoning."),
  ("p", "What matters is that somebody looked at it and decided, and that the decision is "
        "attached to a name. The failure mode is not deferral; it is drift."),
  ("h2", "The debt"),
  ("fig", ("strip", {
    "stages": [
      {"title": "9 jobs deferred", "sub": ["this quarter"], "icon": "counter"},
      {"title": "Not a count", "sub": ["a total"], "icon": "chart"},
      {"title": "37 machine-weeks", "sub": ["past interval"], "icon": "clock"},
      {"title": "Trending up", "sub": ["from 22 last quarter"], "icon": "alarm"},
      {"title": "That is the number", "sub": ["to put in front of people"], "icon": "doc"}],
    "title": "DEFERRAL AS A DEBT",
    "note": "Nine deferrals sounds manageable. Thirty-seven machine-weeks does not."}),
   "How deferrals aggregate. Expressing the total as accumulated time past interval turns a list "
   "of individually reasonable decisions into a number somebody has to answer for.",
   "How deferred maintenance is reported as an accumulated debt",
   "A horizontal row of five boxes. Nine jobs deferred this quarter. Not a count, a total. "
   "Thirty-seven machine-weeks past interval. Trending up, from twenty-two last quarter. That is "
   "the number to put in front of people. A note says nine deferrals sounds manageable and "
   "thirty-seven machine-weeks does not."),
  ("p", "The trend is the part that produces action. Any single quarter's deferrals look "
        "defensible, and a debt that has grown from twenty-two to thirty-seven machine-weeks in "
        "three months is a resourcing conversation with evidence in it."),
  ("p", "Next: the jobs that cannot be deferred at all."),
 ],
},
{
 "slug": "which-jobs-cannot-be-deferred",
 "title": "Which jobs cannot be deferred",
 "nav": "The ones that cannot",
 "read": 5, "words": 720,
 "desc": ("Statutory inspections, why they need a separate track, and the certificate that has to "
          "be findable."),
 "og": ("Mixing statutory inspections into a general maintenance list is how one of them gets "
        "deferred by somebody who did not know they could not."),
 "abstract": ("What makes an inspection statutory, why it needs its own track with no deferral "
              "path, how certificates are stored, and the equipment that must stop."),
 "lede": ("Some inspections are not the manufacturer's advice; they are legal requirements with "
          "dates, and the consequence of missing one is not a broken machine but an unusable one "
          "and a difficult conversation."),
 "tags": ["maintenance", "compliance", "statutory inspection", "certificates", "safety",
          "serverless"],
 "takeaways": [
  "Statutory inspections go in a separate track with no deferral action available.",
  "The interval is set by regulation, not by the manufacturer or by usage.",
  "The certificate is the artefact; store it with the record and make it findable.",
  "Equipment past its inspection date should be marked out of service, not just overdue.",
  "Warn at ninety days, not at seven. Inspectors need booking.",
 ],
 "blocks": [
  ("h2", "A separate track"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Manufacturer schedule", "sub": ["oil, filters, belts"], "icon": "gear",
       "label": "deferrable"},
      {"title": "Condition-based", "sub": ["found on inspection"], "icon": "search",
       "label": "deferrable"},
      {"title": "Statutory", "sub": ["LOLER, pressure,", "electrical"], "icon": "shield",
       "label": "not deferrable"}],
    "target": {"title": "Two different lists", "sub": ["never merged"], "icon": "doc",
               "then": {"title": "Different rules", "sub": ["and different consequences"],
                        "icon": "lock"}},
    "note": "One list with a flag on some items is how the flag gets missed at half past four."}),
   "Why statutory work is kept physically separate rather than flagged within one list. The "
   "separation is the safeguard.",
   "Three types of maintenance work and how statutory work is separated",
   "Three boxes stacked on the left. Manufacturer schedule, covering oil, filters and belts, "
   "labelled deferrable. Condition-based work found on inspection, labelled deferrable. And "
   "Statutory work covering lifting equipment, pressure systems and electrical testing, labelled "
   "not deferrable. All three converge on Two different lists, never merged, and that leads down "
   "to Different rules and different consequences. A note says one list with a flag on some items "
   "is how the flag gets missed at half past four."),
  ("h3", "Why not just a flag"),
  ("p", "A single list with a do-not-defer flag works until somebody is working through forty "
        "items at the end of a difficult week. Two separate lists, with the statutory one much "
        "shorter and reviewed differently, means the mistake is structurally harder to make."),
  ("p", "It also matches how the work is actually organised. Statutory inspections are usually "
        "done by an external inspector on a booked date, which is a different kind of planning "
        "from an internal service, and combining them makes both harder to see."),
  ("h2", "Ninety days, not seven"),
  ("fig", ("chain", {
    "entry": {"title": "An inspection due date", "sub": ["from the last certificate"],
              "icon": "doc"},
    "steps": [
      {"title": "90 days out", "sub": ["book the inspector"], "icon": "email"},
      {"title": "60 days out", "sub": ["booked?"], "icon": "branch",
       "exit": {"title": "Chase", "sub": ["some are booked months ahead"], "icon": "alarm",
                "label": "no"}},
      {"title": "14 days out", "sub": ["prepare access"], "icon": "person"},
      {"title": "Date passed?", "sub": ["no certificate"], "icon": "branch",
       "exit": {"title": "Mark out of service", "sub": ["not merely overdue"], "icon": "lock",
                "label": "yes"}},
      {"title": "Certificate stored", "sub": ["next date computed from it"], "icon": "check"}],
    "note": "The fourth exit is the one that matters. Overdue is a status; out of service is a fact."}),
   "The statutory reminder ladder. It starts far earlier than a maintenance reminder because "
   "booking an external inspector has its own lead time.",
   "How a statutory inspection date is managed from ninety days out",
   "A vertical chain of five steps entered by a box labelled An inspection due date, taken from "
   "the last certificate. Step one, ninety days out, books the inspector. Step two, sixty days "
   "out, asks whether it is booked; if not it exits to Chase, noting some are booked months "
   "ahead. Step three, fourteen days out, prepares access. Step four asks whether the date has "
   "passed with no certificate; if so it exits to Mark out of service, not merely overdue. Step "
   "five stores the certificate and computes the next date from it. A note says the fourth exit "
   "is the one that matters, because overdue is a status and out of service is a fact."),
  ("h3", "Out of service means something"),
  ("p", "Equipment whose statutory inspection has lapsed should not be used, and the system's "
        "role is to make that unambiguous rather than to enforce it, which it cannot. A status "
        "that reads out of service, visible wherever the equipment is booked or assigned, is "
        "considerably harder to overlook than a red row on a maintenance list."),
  ("p", "It is also the honest position. A lifting accessory past its thorough examination date "
        "is not slightly overdue; it is equipment that should not be in use, and softening that "
        "in the interface serves nobody."),
  ("h2", "The certificate"),
  ("callout", "What gets stored, and why", [
   "<strong>The certificate itself,</strong> as a file, immutably, with the equipment record.",
   "<strong>The inspector and their body,</strong> because that is asked about.",
   "<strong>The date of the examination,</strong> which is not always the date on the "
   "certificate.",
   "<strong>Any defects noted,</strong> as their own records, because those become jobs.",
   "<strong>The next due date,</strong> computed from the examination, not from when the "
   "paperwork arrived.",
   "<strong>Findable in ten seconds,</strong> because the moment somebody needs it is not a "
   "relaxed one.",
  ]),
  ("p", "The last line is the practical test. A certificate stored in an email folder, a shared "
        "drive and a filing cabinet is a certificate that does not exist when an inspector asks "
        "for it on a Tuesday morning."),
  ("h3", "Defects become jobs"),
  ("p", "An inspection that finds a defect produces two things: a certificate with a condition on "
        "it, and a piece of work. Those need to become real records rather than a note in a PDF "
        "that somebody reads once."),
  ("p", "Defects with a stated timescale &mdash; remedy within twenty-eight days is common "
        "&mdash; inherit that timescale as a hard date and go into the statutory track rather "
        "than the general one, because they carry the same consequence."),
  ("p", "Next: what the history tells you."),
 ],
},
{
 "slug": "what-the-history-tells-you",
 "title": "What the history tells you",
 "nav": "What the history says",
 "read": 5, "words": 720,
 "desc": ("The machine that keeps appearing, intervals that are too short, and the deferral "
          "reasons that point at something else entirely."),
 "og": ("Three services in a row where nothing needed replacing is evidence that the interval is "
        "too short, and it only exists if somebody wrote down that nothing was wrong."),
 "abstract": ("How completed job records inform interval changes, which machine dominates the "
              "cost, what deferral reasons reveal, and what to report."),
 "lede": ("A year of maintenance records is the best available evidence about which equipment is "
          "worth keeping and which intervals are wrong, and it is almost always thrown away as "
          "closed work orders."),
 "tags": ["maintenance", "analytics", "intervals", "equipment", "reporting", "serverless"],
 "takeaways": [
  "Record what was found, including nothing. Nothing is the finding that changes intervals.",
  "Cost and downtime by machine identifies the one worth replacing.",
  "Deferral reasons in aggregate usually point at parts or people, not at scheduling.",
  "Failures shortly after a service are worth counting separately.",
  "Interval changes are deliberate, recorded decisions with the evidence attached.",
 ],
 "blocks": [
  ("h2", "Nothing is a finding"),
  ("fig", ("chain", {
    "entry": {"title": "A completed service", "sub": ["what was found?"], "icon": "check"},
    "steps": [
      {"title": "Anything replaced?", "sub": ["parts, or none"], "icon": "branch",
       "exit": {"title": "Record 'nothing found'", "sub": ["explicitly"], "icon": "doc",
                "label": "no"}},
      {"title": "How many times running?", "sub": ["nothing found"], "icon": "counter"},
      {"title": "Three in a row?", "sub": ["same machine, same job"], "icon": "branch",
       "exit": {"title": "Carry on", "sub": ["not enough evidence"], "icon": "clock",
                "label": "no"}},
      {"title": "Propose a longer interval", "sub": ["with the evidence"], "icon": "chart"},
      {"title": "A person decides", "sub": ["and it is recorded"], "icon": "person"}],
    "note": "This only works if 'nothing needed doing' is a recordable outcome, which it rarely is."}),
   "How intervals get lengthened on evidence. The first exit is the one most maintenance systems "
   "make impossible to record.",
   "How three uneventful services lead to a proposed interval change",
   "A vertical chain of five steps entered by a box labelled A completed service, asking what was "
   "found. Step one asks whether anything was replaced, parts or none; if none it exits to Record "
   "nothing found, explicitly. Step two counts how many times running nothing has been found. "
   "Step three asks whether it is three in a row for the same machine and job; if not it exits to "
   "Carry on, not enough evidence. Step four proposes a longer interval with the evidence "
   "attached. Step five has a person decide, and it is recorded. A note says this only works if "
   "nothing needed doing is a recordable outcome, which it rarely is."),
  ("h3", "The recording problem"),
  ("p", "Most maintenance systems offer completed and not completed. A service where the engineer "
        "checked everything and replaced nothing is recorded identically to one where they "
        "replaced a worn belt, which throws away the single most useful signal about whether the "
        "interval is right."),
  ("p", "Adding one field &mdash; what was replaced, with an explicit none option &mdash; makes "
        "interval optimisation possible. It is the cheapest improvement available to most "
        "maintenance operations."),
  ("h2", "The machine that keeps appearing"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Press 1", "parts": [("planned", 1200), ("unplanned", 400)]},
      {"label": "Press 2", "parts": [("planned", 1150), ("unplanned", 380)]},
      {"label": "Press 3", "parts": [("planned", 1300), ("unplanned", 4900)]},
      {"label": "Press 4", "parts": [("planned", 1180), ("unplanned", 520)]}],
    "series": [("planned", "Planned maintenance cost, £/year", "#7AA116"),
               ("unplanned", "Unplanned repairs and downtime, £/year", "#DD344C")],
    "unit": "£",
    "note": "Press 3 costs more in breakdowns than the other three combined."}),
   "Four identical machines over a year. The planned cost is nearly the same for all of them; the "
   "unplanned cost identifies the one that should be replaced.",
   "Planned and unplanned maintenance costs for four identical presses",
   "A stacked bar chart with four bars in pounds per year. Two series: planned maintenance cost "
   "in green, and unplanned repairs and downtime in red. Press 1 costs one thousand two hundred "
   "planned and four hundred unplanned. Press 2 costs one thousand one hundred and fifty planned "
   "and three hundred and eighty unplanned. Press 3 costs one thousand three hundred planned and "
   "four thousand nine hundred unplanned. Press 4 costs one thousand one hundred and eighty "
   "planned and five hundred and twenty unplanned. A note says Press 3 costs more in breakdowns "
   "than the other three combined."),
  ("p", "This chart is the business case for a replacement, and it is only possible because "
        "unplanned work was recorded against the machine rather than as a general repair cost. "
        "That linkage is worth insisting on."),
  ("p", "The downtime cost is the harder half and is usually the larger one. Even a rough figure "
        "&mdash; hours stopped multiplied by a stated hourly value &mdash; makes the comparison "
        "possible, with the assumption written down so it can be argued about."),
  ("h3", "Failures after a service"),
  ("p", "Worth counting separately, because a cluster of them means the maintenance itself is "
        "introducing problems: a procedure that is wrong, a part that is not the right one, or "
        "reassembly that is not being checked."),
  ("p", "It is an uncomfortable number to look at and it points at fixable things. A machine that "
        "fails within a week of a service twice in a year is telling you about the service, not "
        "about the machine."),
  ("h2", "What the report says"),
  ("callout", "The quarterly page", [
   "<strong>Jobs due:</strong> 84. <strong>Completed on time:</strong> 61. "
   "<strong>Deferred:</strong> 19. <strong>Overdue, not deferred:</strong> 4.",
   "<strong>Deferral debt:</strong> 37 machine-weeks past interval, up from 22.",
   "<strong>Top deferral reason:</strong> part not available, 11 of 19.",
   "<strong>Statutory:</strong> 6 due, 6 completed, 0 lapsed. This line must always read zero.",
   "<strong>Unplanned cost by machine:</strong> Press 3 accounts for 61% of all unplanned work.",
   "<strong>Interval changes proposed:</strong> 2, both lengthened, both with three clean "
   "services behind them.",
  ]),
  ("p", "The third line is the one that changes something outside maintenance. Eleven deferrals "
        "for missing parts is a stock-holding decision, and it is invisible until the deferral "
        "reasons are counted."),
  ("p", "The fourth line is the one that should never be interesting. A statutory line that ever "
        "reads anything other than zero lapsed is the most important thing on the page, and "
        "putting it there every quarter is how it stays that way."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="asset",
 volumes=[(40, "40 assets"), (150, "150 assets"), (600, "600 assets")],
 read_each=0.0,
 msgs_each=0.35,
 lede=("There is no model in this system and the volumes are small: a hundred and fifty assets "
       "producing a few hundred jobs a year is a substantial workshop or a small factory. Here is "
       "where each cent goes."),
 takeaway_extra=("Reminders and the statutory ladder are the messaging; everything else is "
                 "effectively fixed."),
 risks=[
  "<strong>Polling hour meters continuously.</strong> Running hours change slowly. A reading every "
  "few hours is more than enough for a five-hundred-hour interval.",
  "<strong>Storing certificates in a database field.</strong> They belong in object storage with "
  "a pointer, and they need to outlive the equipment.",
  "<strong>Daily reminders on overdue jobs.</strong> Escalating visibility works; daily nagging "
  "gets filtered and then the escalation is invisible too.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. Messaging covers due "
                "reminders and the statutory ladder, which starts ninety days out."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="em",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the two tracks, and how deferrals are stored."),
 outside=[
  {"title": "Hour meters", "sub": ["and manual readings"], "icon": "gauge"},
  {"title": "Schedules", "sub": ["manufacturer and statutory"], "icon": "doc"},
  {"title": "Certificates", "sub": ["stored immutably"], "icon": "shield"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["certificates,", "nightly due pass"], "icon": "storage"},
  {"title": "Lambda x3", "sub": ["usage, schedule, remind"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["assets, jobs"], "icon": "database"}],
 note="us-east-1. One account. Statutory jobs have no deferral path in any code path or role.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Hour meters and manual readings. "
  "Schedules, from the manufacturer and from statute. And Certificates, stored immutably. Inside "
  "the account, three groups. S3 holding certificates alongside EventBridge running a nightly due "
  "pass. Three Lambda functions named usage, schedule and remind. And two DynamoDB tables named "
  "assets and jobs. A note gives the region as us-east-1, one account, and states that statutory "
  "jobs have no deferral path in any code path or role."),
 functions=[
  ["<code>em-usage</code>", "IoT rule or manual API",
   "Appends a usage reading; updates hours since last service", "10s / 512&nbsp;MB"],
  ["<code>em-schedule</code>", "EventBridge, nightly",
   "Computes percentage of interval used on both bases; opens jobs at 90%",
   "120s / 1024&nbsp;MB"],
  ["<code>em-remind</code>", "EventBridge, nightly",
   "Runs the statutory ladder from 90 days out; escalates third deferrals; marks lapsed assets "
   "out of service", "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>em-usage-role</code>", "<code>dynamodb:UpdateItem</code>", "Assets only"],
  ["<code>em-schedule-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>", "Assets; creates jobs"],
  ["<code>em-remind-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Both tables; one verified identity"]],
 tables=[
  ("Table: assets",
   "PK   asset_id          S   press_3\n"
   "     basis             S   hours | cycles | proxy | calendar\n"
   "     interval_units    N   500\n"
   "     interval_months   N   12    -- whichever comes first\n"
   "     units_now         N   4640\n"
   "     units_at_service  N   4200\n"
   "     last_service_at   S\n"
   "     status            S   in_service | out_of_service\n"
   "     out_of_service_by S   statutory_lapse | withdrawn\n\n"
   "`basis` appears on every job created, so a proxy-scheduled job is never\n"
   "mistaken for one scheduled on a measurement."),
  ("Table: jobs",
   "PK   asset_id          S\n"
   "SK   job_id            S   due_at#type\n"
   "     track             S   routine | statutory   -- never merged in a query\n"
   "     due_at            S\n"
   "     due_units         N   4700\n"
   "     pct_of_interval   N   131   -- the sort key people should use\n"
   "     deferrals         L   [{at, reason, note, new_date, by}]\n"
   "     completed_at      S\n"
   "     found             S   replaced parts, or the literal string 'nothing'\n"
   "     certificate_key   S   statutory jobs only; s3 key\n\n"
   "`deferrals` is a list, not a rescheduled due date. The original date and\n"
   "every subsequent reason survive, which is the whole of Part 3.")],
 inbound=[
  "<strong>Hour meters report periodically</strong> where they can; where they cannot, a weekly "
  "manual reading is entered and recorded as manual.",
  "<strong>Jobs open at ninety per cent of interval</strong>, on whichever basis applies, which "
  "is early enough to arrange and late enough not to clutter.",
  "<strong>Statutory dates come from the last certificate's examination date</strong>, not from "
  "when the paperwork arrived.",
  "<strong>Certificates are written once</strong> to S3 with object lock and never replaced. A "
  "reissued certificate is a new object."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Everything is counters, intervals and "
  "dates.",
  "<strong>The tempting use</strong> is failure prediction from usage patterns. At the scale of a "
  "small operation there is not enough failure data to learn anything a longer interval and a "
  "condition check would not tell you.",
  "<strong>A defensible use</strong> is extracting the examination date and any defects from a "
  "scanned certificate, with the file kept as the record.",
  "<strong>The wrong use</strong> is deciding whether a deferral is acceptable. That is a "
  "judgement with a name attached, which is the point of Part 3.",
  "<strong>The cost page assumes none</strong>, which is why the bill is almost entirely fixed."],
 gotchas=[
  "Store deferrals as a list, never by moving the due date. Rescheduling destroys the evidence "
  "that a job has been put off three times.",
  "Sort overdue work by percentage of interval, not days overdue. Days overdue reliably ranks "
  "lightly-used equipment above heavily-used equipment.",
  "Keep statutory jobs in a separate track with no deferral path in the code, not a flag on a "
  "shared list.",
  "Make 'nothing found' a recordable completion outcome. Without it, no interval can ever be "
  "lengthened on evidence.",
  "Compute the next statutory date from the examination date on the certificate, not from when "
  "the certificate arrived."],
))
