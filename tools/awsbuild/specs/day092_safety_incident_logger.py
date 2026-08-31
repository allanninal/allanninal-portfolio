"""Day 92 -- 2026-07-25 -- Safety incident logger."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "safety-incident-logger"
NAME = "Safety incident logger"

SPEC = {
 "slug": SLUG, "date": "2026-07-25", "name": NAME,
 "tagline": ("Reporting a near miss takes forty seconds on a phone, the report reaches somebody "
             "the same hour, and the ones that repeat get counted -- because the near miss you "
             "never hear about is the accident you will."),
 "lede": ("A small system that makes reporting a near miss or an injury fast enough that people "
          "actually do it, routes each report to whoever needs it within the hour, tracks the "
          "actions that came out of it, and counts what recurs. It never assesses blame and "
          "never closes an action on anybody's behalf. Seven posts on the same system -- one "
          "diagram at a time -- with a cost breakdown and an engineering reference at the end."),
 "keywords": ["safety", "near miss", "incident reporting", "health and safety", "field service",
              "serverless"],
 "icons": ["alarm", "phone", "chart"],
 "faq": [
  ("What is a safety incident logger?",
   "A small serverless system for reporting near misses and injuries from a phone in under a "
   "minute, routing each report to the right person the same hour, tracking the actions that "
   "follow, and counting what recurs. It records; it does not investigate and it does not "
   "assign blame."),
  ("Why focus on near misses rather than accidents?",
   "Because accidents get reported anyway -- somebody is hurt and there is a process. Near "
   "misses are the ones nobody logs, and they are the same event with a different ending. A "
   "business that hears about near misses gets to fix things before somebody is hurt."),
  ("Does it decide how serious something is?",
   "It proposes a severity from what was described, and a person confirms it. The proposal "
   "exists so that a serious report is routed within minutes rather than waiting for somebody "
   "to triage a queue, and the confirmation exists because severity is a judgement."),
  ("Is a report anonymous?",
   "It can be, and the choice is the reporter's, made per report. An anonymous report is routed "
   "and counted like any other; what it cannot do is have follow-up questions asked, and the "
   "form says so before somebody chooses."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "safety-incident-logger-on-aws",
 "title": "A safety incident logger on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 880,
 "desc": ("Reporting a near miss takes forty seconds on a phone, the report is routed within "
          "the hour, and what recurs gets counted. AWS, about $2 a month."),
 "og": ("The near miss you never hear about is the accident you will. This makes reporting one "
        "faster than not reporting it."),
 "abstract": ("The whole system on one page -- a forty-second report, a router and a counter -- "
              "built around the only metric that matters: how many reports you get."),
 "lede": ("Every business with a workshop, a van or a kitchen has a near-miss reporting process, "
          "and almost all of them receive about four reports a year. Not because four things "
          "happened, but because reporting one means finding a form, filling in eleven fields, "
          "and handing it to somebody who might ask what you were doing. So the pallet that "
          "nearly fell gets mentioned to a colleague and nowhere else, and six months later it "
          "falls on somebody. This post walks through a small system designed around a single "
          "number: how many reports you get."),
 "tags": ["safety", "near miss", "incident reporting", "health and safety", "human in the loop",
          "serverless"],
 "takeaways": [
  "One screen, forty seconds: what happened, where, and a photo if there is one.",
  "Severity is proposed by the system and confirmed by a person, so serious ones route fast.",
  "Anonymous is the reporter's choice per report, and the trade-off is stated on the form.",
  "Actions are tracked separately from reports, because a closed report with an open action is a lie.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Whoever saw it", "sub": ["on a phone, now"], "icon": "phone"},
      {"title": "Routing rules", "sub": ["who hears what,", "how fast"], "icon": "doc"},
      {"title": "Whoever acts", "sub": ["and closes actions"], "icon": "team"}],
    "inside": [
      {"title": "Intake", "sub": ["forty seconds,", "one screen"], "icon": "form"},
      {"title": "Triage", "sub": ["proposed severity,", "confirmed by a person"], "icon": "filter"},
      {"title": "Actions", "sub": ["tracked apart from", "the report"], "icon": "check"}],
    "edges": [{"from": 0, "to": 0, "label": "reports"},
              {"from": 1, "to": 1, "label": "who and how fast"},
              {"from": 2, "to": 2, "label": "route, then chase", "up": True}],
    "note": "The only metric that matters is how many reports arrive. Everything is built for that."}),
   "Three things outside the account, three pieces inside it. Every design decision downstream "
   "is subordinate to the note at the bottom: a system that receives no reports is worth "
   "nothing however good its triage is.",
   "System: a phone report in, routing and action tracking out",
   "Three boxes across the top sit outside the AWS account. On the left, Whoever saw it: "
   "reporting from a phone, immediately. In the middle, Routing rules: who hears about what, and "
   "how quickly. On the right, Whoever acts: the people who take and close actions. Each "
   "connects by an arrow to the AWS account container below. Reports flow down into the account. "
   "The routing rules feed in who and how fast. Routing and chasing go back out. Inside the AWS "
   "account are three components in a row. On the left, the Intake, which is forty seconds on "
   "one screen. In the middle, Triage, which proposes a severity that a person confirms. On the "
   "right, Actions, tracked separately from the report itself. A note at the bottom says the "
   "only metric that matters is how many reports arrive, and everything is built for that."),
  ("h3", "Everything is subordinate to the report count"),
  ("p", "A near-miss system that receives four reports a year is not a system; it is a folder. "
        "So every design decision here is checked against one question: does this make reporting "
        "faster or slower? A dropdown of incident categories makes triage easier and reporting "
        "slower, so there is no dropdown. A required location field makes analysis better and "
        "reporting slower, so location is prefilled from the phone and editable."),
  ("p", "The target is a report in under a minute from opening the link, and forty seconds is "
        "achievable: a sentence, a photo, and send. Everything else &mdash; category, severity, "
        "root cause, the actions &mdash; is done afterwards, by somebody whose job it is, from "
        "what was described."),
  ("h3", "What runs on every report (the inside)"),
  ("ul", [
   "<strong>The intake.</strong> One screen. What happened, in your words. Where, prefilled. A "
   "photo if there is one. A choice about anonymity. Send. Part 2 is entirely about keeping it "
   "that short.",
   "<strong>The triage.</strong> Reads the description and proposes a severity and a category. "
   "The proposal is not a decision &mdash; it routes the report, and a person confirms or "
   "changes it. Getting a serious report to somebody in four minutes rather than four hours is "
   "the whole reason this step is automated at all.",
   "<strong>Actions.</strong> An incident produces zero or more actions, each with an owner and "
   "a date, tracked separately from the report. A report is closed when it has been reviewed; an "
   "action is closed when the thing is fixed, and conflating those is how businesses end up with "
   "tidy incident logs and unchanged workshops.",
  ]),
  ("h2", "One report, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Reported", "sub": ["40 seconds"], "icon": "phone"},
      {"title": "Routed", "sub": ["within the hour"], "icon": "bell"},
      {"title": "Confirmed", "sub": ["severity by a person"], "icon": "check"},
      {"title": "Actions", "sub": ["owned and dated"], "icon": "team"},
      {"title": "Counted", "sub": ["and watched for repeats"], "icon": "chart"}],
    "title": "ONE REPORT, END TO END",
    "note": "The last box is where a near-miss log stops being paperwork."}),
   "The same system as one line. The counting at the end is what turns a pile of individually "
   "unremarkable reports into a specific thing worth fixing.",
   "One safety report from phone to counted pattern, in five stages",
   "A horizontal row of five boxes joined by arrows. Reported: forty seconds on a phone. Routed: "
   "within the hour. Confirmed: the severity is set by a person. Actions: owned and dated. "
   "Counted: and watched for repeats. A note says the last box is where a near-miss log stops "
   "being paperwork."),
  ("h2", "In plain words"),
  ("p", "A fitter is walking through the yard and a stack of pallets shifts as a forklift passes. "
        "Nobody is hurt and nothing falls. Under the old process he would mention it to somebody "
        "at lunch. Under this one he stops walking, opens the saved link, types \"pallets by the "
        "roller door moved when the forklift went past, stack looks too high\", takes one photo, "
        "and sends. Thirty-eight seconds."),
  ("p", "The triage reads that as a near miss involving stored materials and vehicle movement, "
        "proposes medium severity, and routes it to the site manager within the hour. She "
        "confirms the severity, looks at the photo, and creates one action: restack and mark a "
        "maximum height, owned by the yard supervisor, due Friday. It is done on Thursday."),
  ("p", "Four months later the counter notices that this is the third report mentioning the "
        "roller door area and the second involving that forklift route. That is a different kind "
        "of finding from any individual report &mdash; none of the three was serious, and "
        "together they describe a place where something is going to happen. Nobody would have "
        "spotted it from three pieces of paper in a folder."),
  ("callout", "Design rules that shaped every decision", [
   "Optimise for the number of reports. Every field added is a report not made.",
   "Severity is proposed for routing and confirmed by a person. The proposal never closes "
   "anything.",
   "Anonymity is the reporter's choice, per report, with the trade-off stated before they choose.",
   "Actions are tracked separately from reports. A reviewed report with an unfixed hazard is not "
   "closed.",
   "Never record fault. The system captures what happened and what was done, and has no field "
   "for whose fault it was.",
   "Count locations and equipment, not people. The pattern that matters is where and what, not "
   "who.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Near-miss reporting fails for reasons that are entirely about friction and slightly "
        "about fear. The friction is a form; the fear is that reporting something will turn into "
        "a conversation about what you were doing at the time. Both are solvable and neither is "
        "solved by encouraging people to report more."),
  ("p", "So the form is forty seconds, anonymity is genuinely available, and there is no field "
        "anywhere in the system for fault. What is left is a description, a place, and a photo "
        "&mdash; which turns out to be everything you need to fix a stack of pallets, and "
        "everything you need to notice that the roller door has come up three times."),
  ("p", "The next four posts walk through each piece: how a report gets made in forty seconds, "
        "how triage routes it, how actions are tracked, and what the counting finds. One diagram "
        "per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-report-takes-forty-seconds",
 "title": "How a report takes forty seconds",
 "nav": "How it is reported",
 "read": 5, "words": 760,
 "desc": ("One screen, three inputs, everything else inferred -- and the anonymity choice that "
          "has to be made before the description is typed, not after."),
 "og": ("Every field on the form is a report not made. Three inputs, everything else inferred, "
        "and the anonymity choice offered before somebody types rather than after."),
 "abstract": ("One screen with three inputs, what is inferred rather than asked, and why the "
              "anonymity choice must be offered before somebody types rather than after."),
 "lede": ("There is a straightforward relationship between the number of fields on a safety form "
          "and the number of reports a business receives, and it is not a gentle one. This post "
          "is about getting to three."),
 "tags": ["safety", "mobile forms", "near miss", "anonymity", "reporting", "serverless"],
 "takeaways": [
  "Three inputs: what happened, a photo if there is one, and the anonymity choice.",
  "Location, time, site and reporter are inferred, and all are editable.",
  "The anonymity choice is offered first, because it changes what people write.",
  "There is no category dropdown. Categorising is done afterwards from the description.",
  "A report can be sent with no photo and no location. Neither is required.",
 ],
 "blocks": [
  ("h2", "Three inputs"),
  ("fig", ("chain", {
    "entry": {"title": "Tap the saved link", "sub": ["home screen"], "icon": "phone"},
    "steps": [
      {"title": "Name or anonymous?", "sub": ["asked first, always"], "icon": "branch",
       "exit": {"title": "Anonymous", "sub": ["no follow-up possible,", "and it says so"],
                "icon": "lock", "label": "chosen"}},
      {"title": "What happened?", "sub": ["one box, your words"], "icon": "chat"},
      {"title": "A photo?", "sub": ["optional, one tap"], "icon": "image"},
      {"title": "Infer the rest", "sub": ["time, place, site"], "icon": "map",
       "side": {"title": "Site boundaries", "sub": ["from the sites sheet"], "icon": "doc"}},
      {"title": "Sent", "sub": ["about forty seconds"], "icon": "check"}],
    "note": "Anonymity is asked before the description, because it changes what people write."}),
   "The whole reporting flow. Asking about anonymity first is a small ordering decision that "
   "materially changes the content of the reports you receive.",
   "How a safety report is made in forty seconds",
   "A vertical chain of five steps entered by a box labelled Tap the saved link on the home "
   "screen. Step one asks name or anonymous, always first; choosing anonymous exits to a state "
   "where no follow-up is possible, and the form says so. Step two asks what happened, in one "
   "box, in the reporter's own words. Step three offers a photo, optional and one tap. Step four "
   "infers the rest: the time, the place and the site, using site boundaries from the sites "
   "sheet. Step five is Sent, in about forty seconds. A note says anonymity is asked before the "
   "description because it changes what people write."),
  ("h3", "Why anonymity comes first"),
  ("p", "If somebody types a description and is then asked whether to attach their name, they "
        "have already written it as a named person. Asking first means an anonymous report is "
        "written as an anonymous report, which is frequently a different and more useful "
        "document &mdash; particularly when what somebody wants to say involves how a job is "
        "usually done rather than a one-off."),
  ("p", "The trade-off is stated in one line where the choice is made: \"Anonymous means we "
        "cannot ask you anything about it.\" That is genuine and it is the whole cost, and most "
        "people who choose anonymity have understood it and chosen it anyway."),
  ("h3", "What is inferred"),
  ("table", ["Field", "Inferred from", "Editable?"], [
   ["Time", "Now", "Yes &mdash; \"this happened yesterday\" is common"],
   ["Location", "The phone, if permitted", "Yes, and it can be typed instead"],
   ["Site", "Which site boundary the location falls in", "Yes, and it is a short pick list"],
   ["Reporter", "The signed staff link", "Only by choosing anonymous"],
   ["Category", "The description, afterwards", "By whoever triages, not the reporter"],
   ["Severity", "The description, afterwards", "By whoever triages, not the reporter"],
  ]),
  ("p", "The last two rows are the important ones. Asking a reporter to categorise an incident "
        "makes them think about how the business classifies things instead of about what "
        "happened, and asking them to rate severity invites them to talk themselves out of "
        "reporting: \"it was only a near miss\" is how a near miss goes unreported."),
  ("h2", "No dropdowns"),
  ("p", "The strongest temptation in this design is a category list, because it makes everything "
        "downstream easier. It is also the single most effective way to reduce your report count, "
        "for a reason that is easy to miss: a person standing in a yard with a phone who cannot "
        "see a category that fits will assume the system is not for this and stop."),
  ("fig", ("strip", {
    "stages": [
      {"title": "11 fields", "sub": ["~4 reports a year"], "icon": "form"},
      {"title": "6 fields", "sub": ["maybe 20"], "icon": "counter"},
      {"title": "3 inputs", "sub": ["hundreds"], "icon": "phone"},
      {"title": "Categorised after", "sub": ["by one person"], "icon": "filter"},
      {"title": "Same analysis", "sub": ["far more data"], "icon": "chart"}],
    "title": "FIELDS VERSUS REPORTS",
    "note": "Categorising afterwards costs one person a few minutes a week and multiplies the input."}),
   "The trade the whole design is built on. Everything a dropdown would have captured can be "
   "recovered from the description afterwards, and the description only exists if the form was "
   "short enough to fill in.",
   "How the number of form fields affects the number of safety reports",
   "A horizontal row of five boxes. Eleven fields: about four reports a year. Six fields: maybe "
   "twenty. Three inputs: hundreds. Categorised after: by one person. Same analysis: with far "
   "more data. A note says categorising afterwards costs one person a few minutes a week and "
   "multiplies the input."),
  ("h3", "The photo"),
  ("p", "Optional, and it does more work than any field would. A photograph of a stack of pallets "
        "carries the height, the position, the surroundings and the lighting, none of which "
        "anybody would have typed. It also makes the report concrete for whoever reads it, which "
        "measurably changes how quickly an action gets created."),
  ("p", "It uploads with a presigned PUT straight to S3, so a phone on a yard connection is not "
        "holding anything open, and the report is submitted whether or not the upload has "
        "finished. A report that fails because a photo did not upload is a report lost."),
  ("p", "Next: how triage routes it."),
 ],
},
{
 "slug": "how-a-report-gets-triaged",
 "title": "How a report gets triaged",
 "nav": "How it is triaged",
 "read": 5, "words": 770,
 "desc": ("A proposed severity that routes within minutes, a confirmation that a person owns, "
          "and the one class of report that skips everything."),
 "og": ("The proposal exists to route, not to decide. A serious report reaching somebody in four "
        "minutes instead of four hours is the entire justification for automating this step."),
 "abstract": ("Why severity is proposed rather than decided, how routing speed depends on it, "
              "the confirmation a person owns, and the one class of report that bypasses "
              "everything."),
 "lede": ("Triage is the only place in this system where a model does anything, and its job is "
          "narrow: get a serious report in front of somebody in minutes rather than hours. It "
          "does not decide anything, and the design goes to some trouble to make sure it "
          "cannot."),
 "tags": ["safety", "triage", "AWS Bedrock", "routing", "escalation", "serverless"],
 "takeaways": [
  "Severity is proposed to route the report, and confirmed by a person afterwards.",
  "Routing speed is set by the proposal: minutes for high, the same hour for medium.",
  "An injury or anything involving a vehicle skips triage and routes immediately.",
  "The proposal errs upward. Over-routing costs somebody a minute; under-routing costs more.",
  "The confirmed severity is what everything downstream counts, never the proposal.",
 ],
 "blocks": [
  ("h2", "Propose, then route, then confirm"),
  ("fig", ("chain", {
    "entry": {"title": "A report", "sub": ["description and photo"], "icon": "chat"},
    "steps": [
      {"title": "Injury or vehicle?", "sub": ["keyword, not model"], "icon": "branch",
       "exit": {"title": "Route now", "sub": ["skip everything else"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Propose severity", "sub": ["one Bedrock call"], "icon": "model",
       "side": {"title": "Severity guide", "sub": ["your own wording"], "icon": "doc"}},
      {"title": "Route by proposal", "sub": ["minutes, or the hour"], "icon": "bell",
       "side": {"title": "Routing rules", "sub": ["who, and how fast"], "icon": "team"}},
      {"title": "A person confirms", "sub": ["or changes it"], "icon": "check"},
      {"title": "Confirmed severity", "sub": ["what everything counts"], "icon": "counter"}],
    "note": "The first check is keywords on purpose: an injury must not wait for a model call."}),
   "How a report is triaged. The keyword check in front is deliberate belt-and-braces: the "
   "highest-consequence reports do not depend on a model call succeeding.",
   "How a safety report is triaged and routed",
   "A vertical chain of five steps entered by a box labelled A report, with a description and a "
   "photo. Step one asks whether it involves an injury or a vehicle, judged by keywords rather "
   "than by a model; if so it exits to Route now, skipping everything else. Step two proposes a "
   "severity with a single Bedrock call, grounded by your own severity guide. Step three routes "
   "by that proposal, within minutes or within the hour, using the routing rules for who and how "
   "fast. Step four has a person confirm or change it. Step five is the Confirmed severity, "
   "which is what everything downstream counts. A note says the first check is keywords on "
   "purpose, because an injury must not wait for a model call."),
  ("h3", "Why keywords in front of the model"),
  ("p", "A report containing \"cut his hand\" or \"the van hit\" must route immediately, and it "
        "must route even if Bedrock is having a bad afternoon. So a small keyword list runs first "
        "&mdash; injury words, vehicle words, words like ambulance and hospital &mdash; and any "
        "hit routes at the highest urgency without waiting for anything."),
  ("p", "It will over-trigger occasionally. \"Nearly cut my hand\" is a near miss and will be "
        "routed as though somebody were injured, which costs a manager thirty seconds. That is a "
        "good trade and it is the trade to make consistently: the cost of over-routing is a "
        "minute of somebody's attention and the cost of under-routing is not."),
  ("h3", "What the proposal is for"),
  ("p", "Not to classify the incident &mdash; a person does that. Its only purpose is to decide "
        "how fast the report needs to reach somebody, which is a question that has to be answered "
        "before a person can look at it, or there is no point answering it at all."),
  ("table", ["Proposed", "Routes", "To whom"], [
   ["High", "Immediately, phone and email", "Site manager and the safety lead"],
   ["Medium", "Within the hour, email", "Site manager"],
   ["Low", "In the daily digest", "Site manager"],
   ["Unclear", "Within the hour, as medium", "Site manager, flagged as unclear"],
  ]),
  ("p", "Unclear routes as medium rather than low, which is the same erring-upward principle. A "
        "report the model could not place is more likely to be unusual than trivial, and unusual "
        "is worth an hour of somebody's attention."),
  ("h2", "The confirmation"),
  ("p", "Whoever the report routed to sets the real severity, and it is one tap on the routing "
        "message. That confirmed value is what every count, report and trend in the system uses. "
        "The proposal is kept alongside it, and the difference between the two is quietly one of "
        "the more useful things the system records."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Proposed high", "sub": ["confirmed high: 41"], "icon": "check"},
      {"title": "Proposed high", "sub": ["confirmed lower: 9"], "icon": "branch"},
      {"title": "Proposed low", "sub": ["confirmed higher: 2"], "icon": "alarm"},
      {"title": "The 2 matter", "sub": ["under-routed"], "icon": "search"},
      {"title": "Adjust the guide", "sub": ["not the model"], "icon": "doc"}],
    "title": "PROPOSAL VERSUS CONFIRMATION",
    "note": "Nine over-routes are fine. Two under-routes are a change to the severity guide."}),
   "What the gap between proposal and confirmation tells you. The asymmetry is the point: "
   "over-routing is noise and under-routing is a miss.",
   "How proposed and confirmed severities compare over a period",
   "A horizontal row of five boxes. Proposed high and confirmed high: forty-one. Proposed high "
   "but confirmed lower: nine. Proposed low but confirmed higher: two. The two matter: those "
   "were under-routed. Adjust the guide: rather than the model. A note says nine over-routes are "
   "fine and two under-routes are a change to the severity guide."),
  ("p", "Two under-routes in a period is a prompt to look at what they described and add that "
        "wording to the severity guide, which is a sheet rather than a prompt in code. The "
        "guide is written in your own terms &mdash; \"anything involving working at height is at "
        "least medium\" &mdash; and it grounds the proposal, so improving it is a five-minute "
        "edit by somebody who knows the business rather than a prompt-engineering exercise."),
  ("p", "Next: the actions, which are where an incident log stops being paperwork."),
 ],
},
{
 "slug": "how-safety-actions-get-tracked",
 "title": "How safety actions get tracked",
 "nav": "How actions are tracked",
 "read": 5, "words": 750,
 "desc": ("Why an action is not the same object as a report, the two states people conflate, and "
          "what happens to an action nobody closes."),
 "og": ("A reviewed report and a fixed hazard are different things. Conflating them produces a "
        "tidy incident log and an unchanged workshop."),
 "abstract": ("Why an action is a separate object from a report, the two states that get "
              "conflated, and what happens to an action nobody closes."),
 "lede": ("This is the part that separates a safety system from a filing system. A report being "
          "dealt with and a hazard being fixed are different events, they happen at different "
          "times, and a system with one status field for both will show green while the pallets "
          "are still stacked too high."),
 "tags": ["safety", "actions", "accountability", "escalation", "record keeping", "serverless"],
 "takeaways": [
  "A report is reviewed. An action is completed. Two objects, two states.",
  "An action has one owner, one date, and one sentence describing the change.",
  "A report can be closed with open actions, and the actions keep chasing.",
  "An overdue action escalates upward, unlike most chasing in this series.",
  "An action closed without a change described is refused.",
 ],
 "blocks": [
  ("h2", "Two objects"),
  ("fig", ("chain", {
    "entry": {"title": "A confirmed report", "sub": ["severity set"], "icon": "check"},
    "steps": [
      {"title": "Review it", "sub": ["a person reads it"], "icon": "person"},
      {"title": "Any actions?", "sub": ["zero or more"], "icon": "branch",
       "exit": {"title": "Close the report", "sub": ["nothing to change"], "icon": "log",
                "label": "none"}},
      {"title": "Create each action", "sub": ["owner, date, change"], "icon": "form",
       "side": {"title": "Actions table", "sub": ["separate object"], "icon": "database"}},
      {"title": "Close the report", "sub": ["even with actions open"], "icon": "check"},
      {"title": "Chase the actions", "sub": ["independently, upward"], "icon": "alarm"}],
    "note": "Closing the report does not close the actions. That separation is the whole point."}),
   "How a report becomes actions. The report closes when somebody has dealt with it; the actions "
   "close when the world has changed, and those are rarely the same day.",
   "How safety actions are created and tracked separately from reports",
   "A vertical chain of five steps entered by a box labelled A confirmed report, with its "
   "severity set. Step one is Review it, where a person reads it. Step two asks whether there are "
   "any actions, zero or more; none exits to Close the report, because there is nothing to "
   "change. Step three creates each action with an owner, a date and a described change, written "
   "to a separate actions table. Step four closes the report, even with actions still open. Step "
   "five chases the actions independently and upward. A note says closing the report does not "
   "close the actions, and that separation is the whole point."),
  ("h3", "Why a report can close with actions open"),
  ("p", "Because they measure different things. \"Has somebody looked at this and decided what to "
        "do?\" should be answered within a day or two, and a queue of unreviewed reports is a "
        "genuine problem. \"Has the thing been fixed?\" might reasonably take three weeks if it "
        "involves ordering racking."),
  ("p", "A single status makes one of those two numbers meaningless. Either reports stay open for "
        "weeks and the review backlog is invisible, or they close on review and the outstanding "
        "hazards are invisible. Two objects, two counts, and both are visible."),
  ("h2", "What an action requires"),
  ("ul", [
   "<strong>One owner, a person.</strong> Not a team and not a role. An action owned by "
   "\"maintenance\" is owned by nobody, and it will still be open in November.",
   "<strong>One date.</strong> When it will be done, set by the owner or by whoever created it "
   "and agreed. A date that has been moved twice is itself a signal.",
   "<strong>One sentence describing the change.</strong> \"Restack pallets and mark a maximum "
   "height by the roller door\" &mdash; not \"review stacking\". An action that cannot be "
   "described as a change is not an action, it is an intention.",
   "<strong>Nothing else.</strong> No priority field, no percentage complete, no sub-tasks. This "
   "is not a project tracker and every field added makes an action less likely to be created.",
  ]),
  ("h3", "Closing an action"),
  ("p", "One tap, and a required sentence: what changed. \"Restacked to two high, floor marked, "
        "supervisor briefed.\" The sentence is required and the tap alone is refused, for a "
        "specific reason: an action closed with no description is indistinguishable from an "
        "action closed to clear a list, and six months later nobody can tell which happened."),
  ("h2", "Escalating upward"),
  ("p", "Almost every chase in this series escalates sideways or stops. This one escalates "
        "upward, and it is the one place that is right, because an overdue safety action is "
        "exactly the situation where somebody with more authority needs to know."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Due date", "sub": ["owner reminded"], "icon": "bell"},
      {"title": "+7 days", "sub": ["their manager"], "icon": "team"},
      {"title": "+21 days", "sub": ["the safety lead"], "icon": "shield"},
      {"title": "+45 days", "sub": ["whoever runs the business"], "icon": "person"},
      {"title": "Never expires", "sub": ["until the change is described"], "icon": "retry"}],
    "title": "AN OVERDUE ACTION GETS LOUDER",
    "note": "The only alert in this series besides a lapsed certification that never rests."}),
   "The escalation ladder for an overdue safety action. Like a lapsed certification, it never "
   "stops, because the underlying situation does not improve on its own.",
   "How an overdue safety action escalates",
   "A horizontal row of five boxes. Due date: the owner is reminded. Plus seven days: their "
   "manager is told. Plus twenty-one days: the safety lead. Plus forty-five days: whoever runs "
   "the business. Never expires: until the change is described. A note says this is the only "
   "alert in this series besides a lapsed certification that never rests."),
  ("p", "The forty-five-day step is deliberately uncomfortable and it is rarely reached. Its "
        "existence is most of its value: an action that has been open for six weeks is going to "
        "be discussed by somebody who can allocate money to it, and everybody in the chain knows "
        "that from the day it was created."),
  ("p", "Next: what the counting finds."),
 ],
},
{
 "slug": "how-safety-patterns-get-counted",
 "title": "How safety patterns get counted",
 "nav": "How patterns count",
 "read": 5, "words": 740,
 "desc": ("Counting places and equipment rather than people, the three patterns worth "
          "surfacing, and the one number that says whether the system is working."),
 "og": ("Count where and what, never who. Three reports about a roller door is a finding; three "
        "reports involving one person is a management conversation the system must not start."),
 "abstract": ("Counting places and equipment rather than people, the three patterns worth "
              "surfacing, and the single number that says whether the whole system is working."),
 "lede": ("A single near miss is usually unremarkable, which is why they get mentioned at lunch "
          "and forgotten. Three near misses in the same corner of a yard are a specific thing "
          "that is going to happen, and nothing except counting will ever find them."),
 "tags": ["safety", "pattern detection", "reporting", "health and safety", "operations",
          "serverless"],
 "takeaways": [
  "Count locations, equipment and activities. Never count people.",
  "Three patterns: a recurring place, a recurring piece of equipment, a recurring activity.",
  "The threshold is three within a rolling quarter, and it is deliberately low.",
  "A pattern is reported with the reports attached, so somebody can read them together.",
  "The one number that matters is the report count itself, and it should be going up.",
 ],
 "blocks": [
  ("h2", "Places and things, never people"),
  ("p", "Every report carries a location, and most carry an implied piece of equipment or an "
        "activity. Those three dimensions are what get counted, and there is deliberately no "
        "code path that counts by reporter or by anybody named in a description."),
  ("p", "The reason is not squeamishness. A count by person answers a question nobody should be "
        "asking of near-miss data: near misses are reported by the people who are paying "
        "attention, so a per-person count mostly identifies your most safety-conscious staff and "
        "makes them look like a problem. It is exactly backwards, and once anybody notices the "
        "count exists, reporting stops."),
  ("fig", ("chain", {
    "entry": {"title": "A confirmed report", "sub": ["with location"], "icon": "check"},
    "steps": [
      {"title": "Which place?", "sub": ["site zone, from the map"], "icon": "map",
       "side": {"title": "Zones", "sub": ["a dozen per site"], "icon": "doc"}},
      {"title": "Which equipment?", "sub": ["from the description"], "icon": "model"},
      {"title": "Which activity?", "sub": ["loading, working at height"], "icon": "filter"},
      {"title": "Increment three counters", "sub": ["rolling quarter"], "icon": "counter",
       "side": {"title": "Counters", "sub": ["place, kit, activity"], "icon": "database"}},
      {"title": "Any at three?", "sub": ["surface with the reports"], "icon": "alarm"}],
    "note": "There is no fourth counter. Counting by person is not a feature that was left out."}),
   "The three dimensions counted from each report. The absence of a fourth is a design decision "
   "rather than an omission, and it is worth stating in the documentation people read.",
   "How safety patterns are counted across three dimensions",
   "A vertical chain of five steps entered by a box labelled A confirmed report, with a "
   "location. Step one asks which place, resolving to a site zone from the map using a dozen "
   "zones per site. Step two asks which equipment, taken from the description. Step three asks "
   "which activity, such as loading or working at height. Step four increments three counters "
   "over a rolling quarter, for place, equipment and activity. Step five asks whether any has "
   "reached three, and surfaces it with the reports attached. A note says there is no fourth "
   "counter, and counting by person is not a feature that was left out."),
  ("h3", "Zones rather than coordinates"),
  ("p", "A location from a phone is a point, and points do not group. Two reports about the same "
        "corner of a yard will be twenty metres apart and count as two different places. So each "
        "site is divided into a dozen named zones &mdash; the roller door, the loading bay, the "
        "mezzanine, the wash bay &mdash; and reports resolve to a zone."),
  ("p", "A dozen is about right. Three zones per site is too coarse to be actionable and fifty is "
        "too fine to ever reach a threshold. Naming them the way people already refer to them is "
        "what makes the resulting report readable by somebody who works there."),
  ("h2", "Three, and why so low"),
  ("p", "Three reports on the same zone, piece of equipment or activity within a rolling quarter "
        "surfaces a pattern. That is a low threshold on purpose, because the cost of a false "
        "pattern is somebody spending ten minutes reading three reports and concluding they are "
        "unrelated, and the cost of a missed one is not comparable."),
  ("p", "The pattern is reported with all three reports attached in full, because the value is "
        "almost never in the count. It is in a person reading three descriptions together and "
        "seeing the thing that connects them, which is frequently not what the counter grouped "
        "them by."),
  ("h2", "The number that matters"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Reports", "sub": ["61 this quarter"], "icon": "phone"},
      {"title": "Up from", "sub": ["44 last quarter"], "icon": "chart"},
      {"title": "Actions created", "sub": ["23"], "icon": "form"},
      {"title": "Actions closed", "sub": ["19"], "icon": "check"},
      {"title": "Patterns found", "sub": ["2"], "icon": "search"}],
    "title": "ONE QUARTER OF SAFETY REPORTING",
    "note": "The first number going up is good news, and it is the opposite of how it reads."}),
   "A quarter of safety reporting in five numbers. The counter-intuitive one is first: a rising "
   "report count is the system working, not the site getting more dangerous.",
   "One quarter of safety reporting summarised in five numbers",
   "A horizontal row of five boxes. Reports: sixty-one this quarter. Up from: forty-four last "
   "quarter. Actions created: twenty-three. Actions closed: nineteen. Patterns found: two. A "
   "note says the first number going up is good news, and that this is the opposite of how it "
   "reads."),
  ("p", "This is the one statistic in the entire series that has to be explained before it is "
        "published, because a rising number of safety reports reads like a deteriorating site "
        "and is almost always the opposite. Near misses were always happening; a quarter with "
        "sixty-one reports and one with four differ in how many were written down."),
  ("p", "So the report says so, every quarter, in a line above the number: \"Reports rising is "
        "the system working. What we are watching is the gap between actions created and actions "
        "closed, and the patterns.\" Four reports a quarter is not a safe business; it is a "
        "business that does not know."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="report",
 volumes=[(20, "20 reports"), (60, "60 reports"), (250, "250 reports")],
 read_each=0.0022, msgs_each=2.6,
 lede=("A business reporting properly generates far more of these than one that is not, which is "
       "the point and also the only thing that scales the bill. Sixty reports a month across a "
       "few sites is a healthy reporting culture. Here is where each cent goes."),
 takeaway_extra=("A rising bill here means a rising report count, which is the outcome the "
                 "system is built to produce."),
 risks=[
  "<strong>Photos kept at full resolution forever.</strong> A yard photo is several megabytes "
  "and safety records are kept for years. Store a downscaled legible copy and expire the "
  "original at your actual retention horizon.",
  "<strong>SMS on every high-severity route.</strong> Correct, and worth capping: a keyword "
  "false positive that texts three people costs little, and a loop that does it repeatedly does "
  "not. A maximum receive count of three on the queue.",
  "<strong>Log retention left at never.</strong> Incident-adjacent logs are the ones you least "
  "want kept indefinitely, quite apart from the cost.",
 ],
 per_unit_note=("The read is one model call per report to propose a severity and pick out the "
                "equipment and activity. Reports that trip the injury or vehicle keywords route "
                "before that call and are cheaper still."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="si",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the three tables, the routing path, and the one model call."),
 outside=[
  {"title": "Report page", "sub": ["CloudFront + S3"], "icon": "phone"},
  {"title": "Zones + routing", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "SNS + SES", "sub": ["routing, escalation"], "icon": "email"}],
 inside=[
  {"title": "S3 + SQS", "sub": ["photos,", "one report queue"], "icon": "bucket"},
  {"title": "Lambda x4", "sub": ["report, triage,", "action, count"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["reports, actions,", "counters"], "icon": "database"}],
 note="us-east-1. One account. No field anywhere in it records fault.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The Report page, served as static files "
  "from S3 behind CloudFront. Zones and routing rules, read through the Google Sheets API "
  "read-only. And SNS with SES, carrying routing and escalation messages. Inside the account, "
  "three groups. S3 holding photographs and SQS carrying one report queue. Four Lambda functions "
  "named report, triage, action and count. And three DynamoDB tables named reports, actions and "
  "counters. A note gives the region as us-east-1, one account, and states that no field "
  "anywhere in it records fault."),
 functions=[
  ["<code>si-report</code>", "Function URL",
   "Accepts the report, resolves the zone, enqueues; never blocks on a photo",
   "10s / 512&nbsp;MB"],
  ["<code>si-triage</code>", "SQS report queue",
   "Keyword check, then one Bedrock call; routes by proposal", "20s / 512&nbsp;MB"],
  ["<code>si-action</code>", "Function URL + EventBridge daily",
   "Creates and closes actions; runs the upward escalation", "15s / 512&nbsp;MB"],
  ["<code>si-count</code>", "SQS confirmed queue + EventBridge quarterly",
   "Increments the three counters; surfaces patterns; quarterly report",
   "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>si-report-role</code>", "<code>s3:PutObject</code>, <code>sqs:SendMessage</code>",
   "The photos prefix; the report queue only"],
  ["<code>si-triage-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>sns:Publish</code>, <code>ses:SendEmail</code>",
   "One model arn; staff numbers only; one identity"],
  ["<code>si-action-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Reports and actions; one verified identity"],
  ["<code>si-count-role</code>", "<code>dynamodb:UpdateItem</code>/<code>Query</code>",
   "Counters; reports, read"]],
 tables=[
  ("Table: reports",
   "PK   report_id         S   inc_2026_07_25_2f9c\n"
   "     reported_at       S   2026-07-25T14:02:11Z\n"
   "     happened_at       S   editable; defaults to reported_at\n"
   "     site              S   ashford\n"
   "     zone              S   roller-door\n"
   "     description       S   in the reporter's own words\n"
   "     photo_keys        L   [s3 keys]\n"
   "     reporter          S   an address, or the literal 'anonymous'\n"
   "     severity_proposed S   high | medium | low | unclear\n"
   "     severity          S   set by a person; what everything counts\n"
   "     equipment         S   from the description\n"
   "     activity          S   from the description\n"
   "     state             S   new | routed | reviewed\n"
   "     ttl               N   epoch, +7 years\n\n"
   "There is no `fault`, `blame` or `at_fault_person` field, and adding one\n"
   "would change what this system is."),
  ("Table: actions",
   "PK   report_id         S   inc_2026_07_25_2f9c\n"
   "SK   action_id         S   act_1\n"
   "     change            S   Restack pallets, mark a maximum height\n"
   "     owner             S   a person, never a team\n"
   "     due               S   2026-07-31\n"
   "     state             S   open | done\n"
   "     closed_change     S   REQUIRED to close: what actually changed\n"
   "     escalated_to      L   [who, when]\n\n"
   "GSI  open-index          PK state, SK due   -- the daily escalation sweep"),
  ("Table: counters",
   "PK   dimension         S   zone | equipment | activity\n"
   "SK   key_quarter       S   roller-door#2026-Q3\n"
   "     count             N   3\n"
   "     report_ids        L   the reports behind the count\n\n"
   "Three dimensions. There is no `reporter` dimension, deliberately: near\n"
   "misses are reported by the people paying attention, so counting by person\n"
   "identifies your best staff and looks like the opposite.")],
 inbound=[
  "The <strong>report page</strong> is static files in S3 behind CloudFront, reached through a "
  "signed staff link saved to a home screen.",
  "<strong>Photos upload with a presigned PUT</strong> and the report submits independently. A "
  "report must never fail because a photo did not finish uploading on a yard connection.",
  "<strong>Anonymous reports</strong> carry the literal string rather than a null, so no code "
  "path can mistake a missing reporter for an unset field.",
  "<strong>Action links</strong> are signed, scoped to one action, and do not expire &mdash; an "
  "open safety action should still be closeable in six months."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "proposing a severity and extracting the equipment and activity from a short description.",
  "<strong>Keywords run first.</strong> Injury and vehicle words route immediately without "
  "waiting for the model, so the highest-consequence path does not depend on it.",
  "<strong>Grounded</strong> with your own severity guide, written in your terms, so improving "
  "the proposal is a sheet edit rather than prompt engineering.",
  "<strong>Output is a JSON schema</strong> with severity, equipment and activity, all nullable. "
  "A null severity routes as medium, not low.",
  "<strong>It never proposes fault, cause or a person.</strong> The schema has no field for any "
  "of them."],
 gotchas=[
  "Run the injury and vehicle keyword check before the model call. Over-triggering costs thirty "
  "seconds; a serious report waiting on a slow model call costs more.",
  "Resolve locations to named zones. Raw coordinates never group, so patterns never reach a "
  "threshold.",
  "Require a description to close an action. A one-tap close is indistinguishable from clearing "
  "a list.",
  "Never add a per-person counter. It identifies your most attentive staff and ends reporting "
  "within a quarter.",
  "Explain the rising report count wherever it is published. It reads like bad news and is the "
  "single clearest sign the system is working."],
))
