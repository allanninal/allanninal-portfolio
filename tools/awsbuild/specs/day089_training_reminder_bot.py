"""Day 89 -- 2026-07-22 -- Training reminder bot."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "training-reminder-bot"
NAME = "Training reminder bot"

SPEC = {
 "slug": SLUG, "date": "2026-07-22", "name": NAME,
 "tagline": ("Required training gets assigned when somebody's role says it should, chased when "
             "it is not done, and reported as a gap the week it appears rather than at audit."),
 "lede": ("A small system that works out which training each person needs from their role, "
          "assigns it when they join or when the role changes, chases what is outstanding, and "
          "reports the gap while it is still small. It never marks anything complete on "
          "somebody's behalf. Seven posts on the same system -- one diagram at a time -- with a "
          "cost breakdown and an engineering reference at the end."),
 "keywords": ["training", "compliance", "onboarding", "staff development", "record keeping",
              "serverless"],
 "icons": ["team", "check", "calendar"],
 "faq": [
  ("What is a training reminder bot?",
   "A small serverless system that derives each person's required training from their role, "
   "assigns it on joining or on a role change, chases what is outstanding, and reports gaps "
   "weekly. It records completions that somebody confirms; it never marks anything complete "
   "itself."),
  ("Does it deliver the training?",
   "No. It has no opinion about how training is delivered -- a course, a video, a toolbox talk, "
   "a conversation. It tracks that a requirement exists, that it was assigned, and that "
   "somebody confirmed it was done."),
  ("What happens when a role changes?",
   "The requirements are recomputed. New requirements are assigned; ones no longer needed are "
   "marked not-required rather than deleted, because the record of what somebody completed "
   "still matters after they move."),
  ("Does it handle refresher training?",
   "Yes, and that is most of the ongoing value. A completion with a validity period generates "
   "the next assignment automatically, so annual refreshers do not depend on anybody remembering "
   "a date."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "training-reminder-bot-on-aws",
 "title": "A training reminder bot on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 870,
 "desc": ("Derives required training from each role, assigns it on joining or a role change, "
          "chases what is outstanding, and reports gaps weekly. AWS, about $2 a month."),
 "og": ("Requirements come from the role, assignments come from the requirements, and refreshers "
        "generate themselves from completions with a validity period."),
 "abstract": ("The whole system on one page -- a requirements engine, an assigner and a chaser "
              "-- built so that a role change and a refresher both happen without anybody "
              "remembering."),
 "lede": ("Required training is a problem that looks solved and is not. Somebody keeps a "
          "spreadsheet, everybody does their induction, and then two years pass. In that time "
          "four people changed roles, six refreshers came due, and two new starters joined "
          "during a busy month. Nobody was negligent; the spreadsheet just has no way to notice "
          "any of that. This post walks through a small system that derives the requirements "
          "rather than storing them."),
 "tags": ["training", "compliance", "onboarding", "staff development", "human in the loop",
          "serverless"],
 "takeaways": [
  "Requirements are derived from the role, so a role change recomputes them automatically.",
  "A completion with a validity period generates its own next assignment.",
  "The system tracks that training happened. It has no opinion about how it was delivered.",
  "Nothing is marked complete by the system. A person confirms, and it is recorded who.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Staff and roles", "sub": ["who does what"], "icon": "team"},
      {"title": "Requirements", "sub": ["role to training,", "with validity"], "icon": "doc"},
      {"title": "People and managers", "sub": ["assigned and chased"], "icon": "person"}],
    "inside": [
      {"title": "Requirements engine", "sub": ["role in,", "training list out"], "icon": "filter"},
      {"title": "Assigner", "sub": ["on join, on change,", "on expiry"], "icon": "calendar"},
      {"title": "Chaser", "sub": ["outstanding, then", "the weekly gap"], "icon": "bell"}],
    "edges": [{"from": 0, "to": 0, "label": "who holds which role"},
              {"from": 1, "to": 1, "label": "what each role needs"},
              {"from": 2, "to": 2, "label": "assignments and chases", "up": True}],
    "note": "Requirements are derived, never stored per person. That is what makes changes free."}),
   "Three things outside the account, three pieces inside it. Deriving requirements rather than "
   "storing them per person is the decision that makes role changes and new requirements "
   "propagate without anybody doing anything.",
   "System: roles and requirements in, assignments and chases out",
   "Three boxes across the top sit outside the AWS account. On the left, Staff and roles: who "
   "does what. In the middle, Requirements: the mapping from role to training, each with a "
   "validity period. On the right, People and managers: who gets assigned and chased. Each "
   "connects by an arrow to the AWS account container below. Who holds which role flows down "
   "into the account. The requirements feed in what each role needs. Assignments and chases go "
   "back out. Inside the AWS account are three components in a row. On the left, the "
   "Requirements engine, which takes a role and produces a training list. In the middle, the "
   "Assigner, which acts on joining, on a role change and on expiry. On the right, the Chaser, "
   "which handles what is outstanding and produces the weekly gap report. A note at the bottom "
   "says requirements are derived and never stored per person, which is what makes changes free."),
  ("h3", "Derived, not stored"),
  ("p", "The obvious model is a list per person of what they need. It works on the day it is "
        "built and decays from then on, because when a requirement is added to a role, somebody "
        "has to go and add it to every person in that role, and that is exactly the step that "
        "does not happen."),
  ("p", "So requirements live once, against roles, and a person's list is computed. Adding "
        "manual handling to the warehouse role assigns it to everybody in the warehouse that "
        "afternoon. Moving somebody from warehouse to delivery recomputes both lists. Neither "
        "requires anybody to remember anything, and that is nearly the whole value."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The requirements engine.</strong> Takes a person's role, plus any site or "
   "equipment attributes, and produces their required training list. It runs on a schedule as "
   "well as on change, so a requirement added in the sheet takes effect without a deploy or a "
   "trigger.",
   "<strong>The assigner.</strong> Creates an assignment when a requirement appears that has no "
   "valid completion. Three causes: somebody joined, somebody's role changed, or a completion "
   "expired. The third is most of them after the first year.",
   "<strong>The chaser.</strong> Nudges the person, then their manager, then reports the gap "
   "weekly. It is deliberately gentle about individual chasing and quite direct about the "
   "aggregate, because a training gap is a management problem rather than a personal failing.",
  ]),
  ("h2", "One requirement, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Role held", "sub": ["warehouse operative"], "icon": "team"},
      {"title": "Requirement", "sub": ["manual handling, 3yr"], "icon": "doc"},
      {"title": "Assigned", "sub": ["no valid completion"], "icon": "calendar"},
      {"title": "Completed", "sub": ["confirmed by a person"], "icon": "check"},
      {"title": "Re-assigned", "sub": ["in three years, automatically"], "icon": "retry"}],
    "title": "ONE REQUIREMENT, END TO END",
    "note": "The fifth box needs nobody to remember anything, which is the entire product."}),
   "The same system as one line. The loop closes on itself: a completion with a validity period "
   "schedules its own successor.",
   "One training requirement from role to refresher, in five stages",
   "A horizontal row of five boxes joined by arrows. Role held: warehouse operative. "
   "Requirement: manual handling, valid three years. Assigned: because there is no valid "
   "completion. Completed: confirmed by a person. Re-assigned: in three years, automatically. A "
   "note says the fifth box needs nobody to remember anything, which is the entire product."),
  ("h2", "In plain words"),
  ("p", "A new warehouse operative joins in March. The requirements engine reads their role and "
        "produces four requirements: manual handling, fire safety, the site induction and "
        "abrasive wheels. None has a valid completion, so four assignments are created on their "
        "first day, each with a due date from the requirement's own grace period &mdash; the "
        "induction is due day one, manual handling within two weeks, abrasive wheels within a "
        "month."),
  ("p", "Three of the four are done in the first fortnight and their supervisor confirms each "
        "one. Abrasive wheels is not, because the course is monthly and the next one is the 14th. "
        "The chaser nudges at the due date, then tells the supervisor at a week over, and the "
        "person appears in the weekly gap report until it is done. Two years and eleven months "
        "later, the manual handling completion approaches its three-year validity, an assignment "
        "appears, and the whole cycle repeats without a single human having thought about a date."),
  ("callout", "Design rules that shaped every decision", [
   "Derive requirements from roles. A stored per-person list is correct on the day it is written "
   "and decays from then on.",
   "A completion with a validity period schedules its own successor. Refreshers must not depend "
   "on memory.",
   "Never mark anything complete automatically. A completion is a claim somebody makes, and the "
   "record says who made it.",
   "Chase people gently and report the aggregate directly. A training gap is a management "
   "problem.",
   "A requirement removed from a role becomes not-required, not deleted. Past completions still "
   "matter.",
   "Grace periods belong to the requirement. An induction is due on day one; a course that runs "
   "monthly is not.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Training tracking is one of those problems where the data is easy and the maintenance "
        "is everything. Any spreadsheet can record who did what. The difficulty is that the "
        "right answer changes constantly for reasons nobody notices &mdash; a role changes, a "
        "requirement is added, three years pass &mdash; and each of those changes requires "
        "somebody to go and update rows by hand."),
  ("p", "So the design removes the per-person list entirely. There is a role-to-training "
        "mapping, a set of completions, and everything else is computed on a schedule. The "
        "system has almost no state of its own, which is why it is still correct two years after "
        "anybody last thought about it."),
  ("p", "The next four posts walk through each piece: how requirements are derived, how "
        "assignments are created, how completions get recorded, and what the gap report shows. "
        "One diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-training-requirements-are-derived",
 "title": "How training requirements are derived",
 "nav": "How requirements derive",
 "read": 5, "words": 770,
 "desc": ("Role plus attributes rather than role alone, why a person-level override is still "
          "needed, and what happens when a requirement is removed."),
 "og": ("Requirements come from a role plus attributes -- the site, the equipment, the shift -- "
        "because role alone puts the same training on people who do very different jobs."),
 "abstract": ("Why requirements come from a role plus attributes rather than a role alone, the "
              "person-level override that is still necessary, and what happens when a "
              "requirement is removed."),
 "lede": ("A role-to-training mapping is the right idea and slightly too simple on its own. Two "
          "people with the same job title at two sites frequently need different training, and a "
          "system that cannot express that gets worked around with a manual list, which is the "
          "thing it was built to avoid."),
 "tags": ["training", "compliance", "role requirements", "data modelling", "HR", "serverless"],
 "takeaways": [
  "Requirements attach to a role plus attributes: site, equipment, shift, driving.",
  "Person-level additions exist and are recorded with a reason, because reality has exceptions.",
  "A person-level removal does not exist. Exceptions add, never subtract.",
  "A requirement removed from a role marks assignments not-required and keeps completions.",
  "The engine runs on a schedule as well as on change, so a sheet edit takes effect the same day.",
 ],
 "blocks": [
  ("h2", "Role plus attributes"),
  ("table", ["Attribute", "Example", "What it adds"], [
   ["Role", "Warehouse operative", "The base list: manual handling, fire, induction"],
   ["Site", "Ashford depot", "Site induction, and the fuel bay awareness talk"],
   ["Equipment", "Counterbalance forklift", "The forklift ticket and its refresher"],
   ["Driving", "Company vehicle", "Driver awareness, licence check"],
   ["Shift", "Nights", "Lone working, and the different first-aid arrangement"],
   ["Responsibility", "First aider", "The first-aid qualification and its three-year refresher"],
  ]),
  ("p", "Six attributes covers essentially every case in a small business, and none of them is "
        "exotic &mdash; every one is something the business already knows about a person. The "
        "combination is what produces the list, so a warehouse operative on nights at Ashford who "
        "drives a forklift gets a materially different list from the same job title on days at "
        "another site, without anybody maintaining two roles."),
  ("h2", "The engine"),
  ("fig", ("chain", {
    "entry": {"title": "A person", "sub": ["role and attributes"], "icon": "person"},
    "steps": [
      {"title": "Base list from the role", "sub": ["the common case"], "icon": "filter",
       "side": {"title": "Requirements sheet", "sub": ["role to training"], "icon": "doc"}},
      {"title": "Add per attribute", "sub": ["site, kit, shift"], "icon": "counter"},
      {"title": "Add person-level extras", "sub": ["with a reason"], "icon": "form",
       "side": {"title": "Exceptions", "sub": ["additions only"], "icon": "log"}},
      {"title": "Subtract valid completions", "sub": ["not yet expired"], "icon": "check",
       "side": {"title": "Completions", "sub": ["with validity dates"], "icon": "database"}},
      {"title": "What is outstanding", "sub": ["the assignment list"], "icon": "calendar"}],
    "note": "Run on every change and nightly, so a sheet edit propagates without a trigger."}),
   "How a person's outstanding training is computed. Nothing is stored per person except "
   "completions and additive exceptions; the list itself is derived every time.",
   "How a person's required training list is derived",
   "A vertical chain of five steps entered by a box labelled A person, carrying a role and "
   "attributes. Step one takes the base list from the role using the requirements sheet mapping "
   "roles to training. Step two adds per attribute, covering site, equipment and shift. Step "
   "three adds any person-level extras, each recorded with a reason, from an additions-only "
   "exceptions list. Step four subtracts completions that are valid and not yet expired, read "
   "from the completions table with their validity dates. Step five produces what is "
   "outstanding, which is the assignment list. A note says the engine runs on every change and "
   "nightly, so a sheet edit propagates without a trigger."),
  ("h3", "Exceptions add, never subtract"),
  ("p", "Person-level additions are necessary: somebody is designated a fire marshal, somebody "
        "is being trained into a new role, somebody had an incident and additional training was "
        "agreed. All of those are real and none of them fits a role mapping."),
  ("p", "Person-level removals do not exist, and the omission is deliberate. \"This person does "
        "not need the manual handling that everybody else in their role needs\" is either a "
        "mistake in the role mapping or a decision that ought to be visible, and both are better "
        "handled by changing the mapping or changing the attributes than by a quiet exception "
        "that nobody reviews."),
  ("p", "The one legitimate-looking case &mdash; somebody holds an equivalent qualification from "
        "elsewhere &mdash; is handled as a completion rather than an exception. Record the "
        "external qualification with its expiry, and the requirement is satisfied through the "
        "normal path with a proper record of why."),
  ("h2", "Removing a requirement"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Removed from the role", "sub": ["a sheet edit"], "icon": "doc"},
      {"title": "Outstanding ones", "sub": ["marked not-required"], "icon": "stop"},
      {"title": "Chasing stops", "sub": ["same day"], "icon": "bell"},
      {"title": "Completions kept", "sub": ["they still happened"], "icon": "check"},
      {"title": "History intact", "sub": ["and explainable"], "icon": "log"}],
    "title": "WHAT REMOVING A REQUIREMENT DOES",
    "note": "Deleting the completions would erase the record of training that genuinely happened."}),
   "What happens when a requirement is dropped from a role. Outstanding assignments stop; "
   "completed ones stay, because they describe something that actually occurred.",
   "What happens when a training requirement is removed from a role",
   "A horizontal row of five boxes. Removed from the role: by a sheet edit. Outstanding ones: "
   "marked not-required. Chasing stops: the same day. Completions kept: because they still "
   "happened. History intact: and explainable. A note says deleting the completions would erase "
   "the record of training that genuinely happened."),
  ("p", "Marking outstanding assignments not-required rather than deleting them matters for the "
        "gap report: a sudden drop in outstanding training should be explainable, and \"eleven "
        "assignments became not-required on the 4th because the requirement was dropped\" is a "
        "much better answer than a chart that quietly improved."),
  ("p", "Next: how assignments get created and dated."),
 ],
},
{
 "slug": "how-a-training-assignment-is-created",
 "title": "How a training assignment is created",
 "nav": "How it is assigned",
 "read": 5, "words": 760,
 "desc": ("Three causes -- joining, a role change, an expiry -- the grace period that belongs to "
          "the requirement, and why the first week of a new job should not contain nine "
          "assignments."),
 "og": ("Three causes and one design rule: the grace period belongs to the requirement, so an "
        "induction is due on day one and a monthly course is not."),
 "abstract": ("The three causes of an assignment, why the grace period belongs to the "
              "requirement rather than to the person, and how a new starter's first week avoids "
              "becoming a wall of overdue items."),
 "lede": ("Creating an assignment is trivial. Dating it is not, and getting the dates wrong is "
          "how a training system becomes a permanent list of overdue items that everybody learns "
          "to ignore within a month."),
 "tags": ["training", "onboarding", "scheduling", "compliance", "reminders", "serverless"],
 "takeaways": [
  "Three causes: somebody joined, a role changed, or a completion expired.",
  "The grace period belongs to the requirement, not to a global setting.",
  "A new starter's assignments are staggered, because nine due on day one is nine ignored.",
  "An expiry assignment is created before the expiry, not after it.",
  "An assignment is never created for training with a valid completion, which sounds obvious and is where duplicates come from.",
 ],
 "blocks": [
  ("h2", "Three causes"),
  ("fig", ("chain", {
    "entry": {"title": "The nightly run", "sub": ["and every change"], "icon": "clock"},
    "steps": [
      {"title": "New person?", "sub": ["no completions at all"], "icon": "branch",
       "exit": {"title": "Stagger the list", "sub": ["by requirement priority"], "icon": "calendar",
                "label": "yes"}},
      {"title": "Role or attribute changed?", "sub": ["list differs from before"], "icon": "branch",
       "exit": {"title": "Assign the difference", "sub": ["only the new ones"], "icon": "form",
                "label": "yes"}},
      {"title": "Completion expiring?", "sub": ["inside its lead time"], "icon": "branch",
       "side": {"title": "Completions", "sub": ["validity dates"], "icon": "database"},
       "exit": {"title": "Assign the refresher", "sub": ["before it lapses"], "icon": "retry",
                "label": "yes"}},
      {"title": "Nothing to do", "sub": ["most people, most nights"], "icon": "check"}],
    "note": "The third cause is the one that keeps working two years after anybody looked."}),
   "The three ways an assignment comes into existence. The expiry path is the one that makes the "
   "system worth keeping after the first year, when everybody has done everything once.",
   "The three causes of a new training assignment",
   "A vertical chain of four steps entered by a box labelled The nightly run, and every change. "
   "Step one asks whether this is a new person with no completions at all; if so it exits to "
   "Stagger the list, ordered by requirement priority. Step two asks whether a role or attribute "
   "changed so that the derived list differs from before; if so it exits to Assign the "
   "difference, meaning only the new items. Step three asks whether a completion is expiring "
   "inside its lead time, reading validity dates from the completions table; if so it exits to "
   "Assign the refresher, before it lapses. Step four is Nothing to do, which is most people on "
   "most nights. A note says the third cause is the one that keeps working two years after "
   "anybody looked."),
  ("h2", "Grace periods belong to the requirement"),
  ("table", ["Requirement", "Grace", "Why"], [
   ["Site induction", "Day one", "Nobody works on site without it"],
   ["Fire safety briefing", "3 days", "Delivered in house, no scheduling constraint"],
   ["Manual handling", "14 days", "Delivered in house but needs a group"],
   ["Abrasive wheels", "30 days", "External course, runs monthly"],
   ["First aid at work", "90 days", "External course, sparse dates"],
   ["Annual refresher", "30 days before expiry", "Assigned early so it can be booked"],
  ]),
  ("p", "A single global grace period &mdash; \"all training due within 30 days\" &mdash; is "
        "wrong in both directions simultaneously. It lets somebody work on site for a month "
        "without an induction, and it marks a first-aid course overdue when the next available "
        "date is six weeks away. Both errors teach people to disregard the due date."),
  ("h2", "Staggering a new starter"),
  ("p", "A new warehouse operative with nine requirements and no completions would, naively, "
        "receive nine assignments on their first morning. Seven of them will be overdue by "
        "Friday, the list will be red, and the new starter's first impression of the system is "
        "that it is decorative."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Day one", "sub": ["induction only"], "icon": "shield"},
      {"title": "Week one", "sub": ["fire, manual handling"], "icon": "form"},
      {"title": "Month one", "sub": ["abrasive wheels"], "icon": "calendar"},
      {"title": "Month three", "sub": ["first aid, if designated"], "icon": "check"},
      {"title": "Never all at once", "sub": ["and never all red"], "icon": "counter"}],
    "title": "A NEW STARTER'S FIRST QUARTER",
    "note": "Nine assignments on day one is nine ignored assignments by Friday."}),
   "How a new starter's requirements are spread out. The ordering comes from each requirement's "
   "own grace period, so nothing needs a separate onboarding schedule.",
   "How a new starter's training assignments are staggered over a quarter",
   "A horizontal row of five boxes. Day one: the induction only. Week one: fire safety and "
   "manual handling. Month one: abrasive wheels. Month three: first aid, if designated. Never "
   "all at once: and never all red. A note says nine assignments on day one is nine ignored "
   "assignments by Friday."),
  ("p", "The staggering is not a separate feature; it falls out of the grace periods already "
        "being per requirement. That is worth noticing, because it means there is no onboarding "
        "schedule to maintain separately from the requirements themselves."),
  ("h3", "The duplicate that catches everybody"),
  ("p", "The one implementation bug worth naming: creating an assignment for a requirement that "
        "already has a valid completion. It happens when the completion check uses the completion "
        "date rather than the validity end, or when a role change recomputes the whole list "
        "rather than the difference. The symptom is somebody being asked to redo training they "
        "did last month, and it destroys confidence in the system faster than anything else it "
        "could do."),
  ("p", "Next: how a completion gets recorded."),
 ],
},
{
 "slug": "how-a-completion-gets-recorded",
 "title": "How a completion gets recorded",
 "nav": "How completions record",
 "read": 5, "words": 750,
 "desc": ("Who is allowed to confirm, why the system never marks anything itself, external "
          "qualifications, and what evidence is and is not kept."),
 "og": ("A completion is a claim somebody makes, and the record says who made it. The system "
        "never marks anything complete on anybody's behalf."),
 "abstract": ("Who may confirm a completion, why the system never marks anything itself, how an "
              "external qualification satisfies a requirement, and what evidence is kept."),
 "lede": ("A completion is the one write in this system that carries any weight, and the design "
          "question is not how to record it but who is allowed to and what that record has to "
          "contain to still be worth something in three years."),
 "tags": ["training", "compliance", "record keeping", "audit", "evidence", "serverless"],
 "takeaways": [
  "Nobody confirms their own completion. It is the one permission rule in the system.",
  "The record says who confirmed, when, and how the training was delivered.",
  "An external qualification is recorded as a completion with its own expiry, not as an exception.",
  "Evidence is optional and, when supplied, is a link rather than a stored document.",
  "A completion is never edited. A correction is a new record superseding the old one.",
 ],
 "blocks": [
  ("h2", "Who confirms"),
  ("fig", ("chain", {
    "entry": {"title": "Training happened", "sub": ["somehow"], "icon": "team"},
    "steps": [
      {"title": "Who is confirming?", "sub": ["never the person themselves"], "icon": "branch",
       "side": {"title": "Staff list", "sub": ["manager, trainer"], "icon": "doc"},
       "exit": {"title": "Refused", "sub": ["self-confirmation"], "icon": "stop",
                "label": "the same person"}},
      {"title": "How was it delivered?", "sub": ["course, in house,", "external cert"],
       "icon": "form"},
      {"title": "Compute the validity", "sub": ["from the requirement"], "icon": "counter",
       "side": {"title": "Requirements", "sub": ["validity period"], "icon": "chart"}},
      {"title": "Write the completion", "sub": ["append-only"], "icon": "log",
       "side": {"title": "Completions", "sub": ["never edited"], "icon": "database"}},
      {"title": "Schedule the refresher", "sub": ["at expiry minus lead"], "icon": "retry"}],
    "note": "The last step is why this system still works in year three."}),
   "How a completion is recorded. The self-confirmation refusal is the only permission rule "
   "here, and the refresher scheduling is what makes the record self-maintaining.",
   "How a training completion is confirmed and recorded",
   "A vertical chain of five steps entered by a box labelled Training happened, somehow. Step "
   "one asks who is confirming, checking the staff list for a manager or trainer, and never the "
   "person themselves; a self-confirmation exits to Refused. Step two asks how it was delivered, "
   "as a course, in house, or an external certificate. Step three computes the validity from the "
   "requirement's own validity period. Step four writes the completion to an append-only "
   "completions table that is never edited. Step five schedules the refresher at expiry minus "
   "the lead time. A note says the last step is why this system still works in year three."),
  ("h3", "Why no self-confirmation"),
  ("p", "Not because people are dishonest &mdash; overwhelmingly they are not &mdash; but "
        "because a training record where anybody can mark their own training complete is worth "
        "nothing to an insurer, an auditor or a client asking for evidence. The whole value of "
        "the record is that somebody other than the beneficiary attested to it."),
  ("p", "The rule is enforced by comparing the confirming address with the subject's, which is "
        "crude and sufficient. In practice a supervisor confirms for their team, a trainer "
        "confirms for a session, and both are recorded by name."),
  ("h2", "External qualifications"),
  ("p", "Somebody arrives already holding a first-aid certificate. That should satisfy the "
        "requirement, and the wrong way to do it is a person-level exception saying they do not "
        "need it. The right way is a completion of type <code>external</code> with the "
        "certificate's own expiry date rather than the requirement's default validity."),
  ("p", "That distinction matters in three years: an exception says nothing about when it stops "
        "being true, whereas an external completion carrying the certificate's real expiry will "
        "generate a refresher assignment on the right date, exactly like an internal one."),
  ("h2", "Evidence"),
  ("fig", ("strip", {
    "stages": [
      {"title": "In house", "sub": ["who trained, who attended"], "icon": "team"},
      {"title": "External course", "sub": ["provider and date"], "icon": "external"},
      {"title": "Certificate", "sub": ["a link, not a copy"], "icon": "link"},
      {"title": "Toolbox talk", "sub": ["topic and attendees"], "icon": "chat"},
      {"title": "Enough to stand up", "sub": ["without being a document store"], "icon": "check"}],
    "title": "WHAT A COMPLETION RECORDS",
    "note": "A link to wherever the certificate already lives beats a second copy of it here."}),
   "What each kind of completion carries. The system records enough to be evidence and "
   "deliberately does not become a document store.",
   "What a training completion record contains for four delivery types",
   "A horizontal row of five boxes. In house: who trained and who attended. External course: the "
   "provider and the date. Certificate: a link rather than a copy. Toolbox talk: the topic and "
   "the attendees. Enough to stand up: without being a document store. A note says a link to "
   "wherever the certificate already lives beats a second copy of it here."),
  ("p", "Keeping a link rather than a copy is a deliberate limitation. Certificates already live "
        "somewhere &mdash; the certification tracker from Day 85, a shared drive, the provider's "
        "own portal &mdash; and a second copy here would need its own retention policy for no "
        "additional assurance."),
  ("h3", "Corrections"),
  ("p", "A completion recorded against the wrong person, or with the wrong date, is corrected by "
        "a new record that supersedes it, and both stay. Editing in place would produce a "
        "training record that cannot be relied on, which is the only thing this system produces."),
  ("p", "Next: the gap report, and why it is about roles rather than people."),
 ],
},
{
 "slug": "how-the-training-gap-reads",
 "title": "How the training gap reads",
 "nav": "How the gap reads",
 "read": 5, "words": 750,
 "desc": ("A weekly report by requirement rather than by person, the one number that matters, "
          "and why an overdue list sorted by name is the wrong shape."),
 "og": ("Sorted by requirement, not by person. Eleven people missing one thing is a scheduling "
        "problem; one person missing eleven things is a different conversation entirely."),
 "abstract": ("A weekly report organised by requirement rather than by person, the single number "
              "worth watching, and why an overdue list sorted by name produces the wrong "
              "response."),
 "lede": ("The obvious report is a list of overdue training with names against it. It is easy to "
          "produce, it feels like accountability, and it consistently produces the wrong action "
          "&mdash; because almost every training gap in a small business is a scheduling problem "
          "wearing an individual's name."),
 "tags": ["training", "reporting", "compliance", "management", "operations", "serverless"],
 "takeaways": [
  "Sorted by requirement first, not by person. The gap is usually one course, not one employee.",
  "The number that matters is people-days of exposure, not a count of overdue items.",
  "A person appearing across many requirements is the one case worth naming, and it is rare.",
  "Not-required items are shown separately so a drop in the gap is always explainable.",
  "Weekly, because a training gap that is three weeks old was avoidable at one week.",
 ],
 "blocks": [
  ("h2", "By requirement, not by person"),
  ("callout", "This week's gap", [
   "<strong>Abrasive wheels &mdash; 6 people, oldest 23 days.</strong> Next course 14 August. "
   "All six are waiting on the same date.",
   "<strong>Manual handling &mdash; 2 people, oldest 9 days.</strong> Delivered in house; needs "
   "a session booking.",
   "<strong>Site induction &mdash; 1 person, 2 days.</strong> New starter at Ashford, due "
   "immediately.",
   "<strong>Expiring within 30 days &mdash; 4 people, 3 requirements.</strong> None assigned yet "
   "because they are inside their lead time.",
   "<em>Not-required this week: 11 items, because forklift refresher was dropped from the "
   "warehouse role on the 4th.</em>",
  ]),
  ("p", "Reading that, the action is obvious and it is not about any individual: book an abrasive "
        "wheels course, book a manual handling session, and do the induction today. Six people "
        "waiting on one external course date is a procurement task, and no amount of chasing six "
        "individuals will move it."),
  ("h2", "The number that matters"),
  ("fig", ("chain", {
    "entry": {"title": "Outstanding assignments", "sub": ["with due dates"], "icon": "calendar"},
    "steps": [
      {"title": "Days overdue each", "sub": ["not a count of items"], "icon": "counter"},
      {"title": "Weight by requirement", "sub": ["induction != refresher"], "icon": "filter",
       "side": {"title": "Requirements", "sub": ["a criticality field"], "icon": "chart"}},
      {"title": "People-days of exposure", "sub": ["one number"], "icon": "search"},
      {"title": "Trend it weekly", "sub": ["direction, not level"], "icon": "report"}],
    "note": "Eleven items one day overdue is nothing. One induction three weeks overdue is not."}),
   "How the gap is measured. Counting overdue items treats a three-week-old site induction as "
   "equivalent to a refresher that became due yesterday, and they are not remotely equivalent.",
   "How the training gap is measured as people-days of exposure",
   "A vertical chain of four steps entered by a box labelled Outstanding assignments, with due "
   "dates. Step one computes days overdue for each rather than a count of items. Step two "
   "weights by requirement, since an induction is not a refresher, using a criticality field on "
   "the requirements. Step three produces people-days of exposure as one number. Step four "
   "trends it weekly, watching direction rather than level. A note says eleven items one day "
   "overdue is nothing, and one induction three weeks overdue is not."),
  ("p", "People-days of exposure is a single number that behaves sensibly: it rises quickly when "
        "something critical is overdue, it barely moves for a batch of refreshers that became due "
        "this morning, and it falls to zero when the gap closes. A count of overdue items does "
        "none of those things."),
  ("h3", "The one time a person is named"),
  ("p", "A person appearing across four or more requirements is the single case where naming an "
        "individual is the right response, and it is rare. It almost never means somebody is "
        "avoiding training; it usually means they joined during a busy month, or changed role and "
        "nobody ran an induction, or work a shift pattern that has never coincided with a course."),
  ("p", "So the report names them once, at the bottom, phrased as a question about circumstances "
        "rather than compliance: \"J. Reed has four outstanding &mdash; nights at Ashford since "
        "April, no sessions have run on that shift.\" That sentence produces a different "
        "conversation from a red row on a list."),
  ("h2", "Explaining a drop"),
  ("p", "The not-required line exists because a gap that improves for the wrong reason is worse "
        "than a gap that does not improve. Eleven items disappearing because a requirement was "
        "dropped looks identical, on a chart, to eleven people completing their training."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Gap falls", "sub": ["by 11 items"], "icon": "counter"},
      {"title": "Why?", "sub": ["two possible reasons"], "icon": "branch"},
      {"title": "Completed", "sub": ["good"], "icon": "check"},
      {"title": "Not-required", "sub": ["a decision, not progress"], "icon": "stop"},
      {"title": "Report says which", "sub": ["always"], "icon": "report"}],
    "title": "WHY THE GAP CHANGED",
    "note": "A chart that improves for two different reasons is a chart nobody should trust."}),
   "Why every change in the gap is attributed. Improvement by decision and improvement by "
   "completion look identical on a chart and mean completely different things.",
   "Why a fall in the training gap is always explained",
   "A horizontal row of five boxes. Gap falls: by eleven items. Why: two possible reasons. "
   "Completed: which is good. Not-required: which is a decision rather than progress. Report says "
   "which: always. A note says a chart that improves for two different reasons is a chart nobody "
   "should trust."),
  ("h3", "Why weekly"),
  ("p", "Because the actions the report produces &mdash; book a course, run a session, do an "
        "induction &mdash; take about a week to arrange, and a gap noticed at one week is closed "
        "at three. A monthly report notices the same gap at four weeks and closes it at seven, "
        "which is a month of exposure for no reason at all."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="assignment",
 volumes=[(30, "30 assignments"), (100, "100 assignments"), (400, "400 assignments")],
 read_each=0.0004, msgs_each=1.8,
 lede=("This system barely uses a model at all &mdash; everything in it is set arithmetic over "
       "a few hundred rows, run nightly. The bill is dominated by email and by the fixed band. "
       "Here is where each cent goes."),
 takeaway_extra=("There is almost no model use here. Deriving a required-training list is set "
                 "arithmetic, and set arithmetic should be code."),
 risks=[
  "<strong>Recomputing everything on every change.</strong> A nightly full recompute over a few "
  "hundred people is fine; the same recompute fired on every attribute edit during a busy HR "
  "afternoon is not, and it will also send duplicate assignments.",
  "<strong>Assignment duplicates from a bad completion check.</strong> Checking the completion "
  "date instead of the validity end creates a fresh assignment for training somebody did last "
  "month, which is the fastest way to lose people's trust in the system.",
  "<strong>Log retention left at never.</strong> A nightly job producing nothing most nights "
  "will still fill a log group forever without a retention setting.",
 ],
 per_unit_note=("The read cost here is nominal: a model is used only to match an externally "
                "worded qualification name against your requirement list, which happens a "
                "handful of times a year."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="tb",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the nightly recompute, and the one place a model appears."),
 outside=[
  {"title": "Staff + requirements", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "Confirm page", "sub": ["CloudFront + S3"], "icon": "form"},
  {"title": "SES outbound", "sub": ["assignments, gap report"], "icon": "email"}],
 inside=[
  {"title": "EventBridge", "sub": ["nightly recompute,", "weekly report"], "icon": "clock"},
  {"title": "Lambda x3", "sub": ["derive, chase, confirm"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["assignments, completions"], "icon": "database"}],
 note="us-east-1. One account. Requirements live in a sheet, never in the database.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Staff and requirements, read through the "
  "Google Sheets API read-only. The Confirm page, served as static files from S3 behind "
  "CloudFront. And SES outbound, carrying assignments and the weekly gap report. Inside the "
  "account, three groups. EventBridge carrying a nightly recompute and a weekly report schedule. "
  "Three Lambda functions named derive, chase and confirm. And two DynamoDB tables named "
  "assignments and completions. A note gives the region as us-east-1, one account, and states "
  "that requirements live in a sheet rather than in the database."),
 functions=[
  ["<code>tb-derive</code>", "EventBridge nightly",
   "Recomputes every person's list; assigns the difference", "120s / 1024&nbsp;MB"],
  ["<code>tb-chase</code>", "EventBridge daily + weekly",
   "Nudges, escalates, and builds the weekly gap report", "60s / 512&nbsp;MB"],
  ["<code>tb-confirm</code>", "Function URL",
   "Records a completion; refuses self-confirmation", "15s / 512&nbsp;MB"]],
 roles=[
  ["<code>tb-derive-role</code>",
   "<code>dynamodb:Query</code>/<code>PutItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Assignments and completions; the Sheets credential only"],
  ["<code>tb-chase-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "Assignments, read; one verified identity"],
  ["<code>tb-confirm-role</code>",
   "<code>dynamodb:PutItem</code>, <code>bedrock:InvokeModel</code>",
   "Completions; one model arn"]],
 tables=[
  ("Table: assignments",
   "PK   person            S   j.reed@example.com\n"
   "SK   requirement       S   abrasive-wheels\n"
   "     state             S   open | done | not_required\n"
   "     cause             S   joined | role_change | expiry\n"
   "     assigned_at       S   2026-07-22\n"
   "     due_at            S   2026-08-21   -- assigned_at + the requirement's grace\n"
   "     chased_at         L   [ISO timestamps]\n"
   "     closed_by         S   the completion id, or the not_required reason\n\n"
   "One row per person per requirement. The derive function computes the set\n"
   "each night and only writes the DIFFERENCE, which is what prevents\n"
   "duplicate assignments on an unchanged list.\n\n"
   "GSI  requirement-index   PK requirement, SK due_at  -- the gap report, by course"),
  ("Table: completions",
   "PK   person            S   j.reed@example.com\n"
   "SK   completed_at      S   2026-05-14#cmp_9a2f\n"
   "     requirement       S   manual-handling\n"
   "     delivery          S   in_house | external_course | external_cert | toolbox\n"
   "     valid_until       S   2029-05-14   -- from the requirement, or the cert's own date\n"
   "     confirmed_by      S   supervisor@example.com   -- never the subject\n"
   "     evidence_url      S   a link, not a stored document\n"
   "     supersedes        S   another SK, for a correction\n\n"
   "Append-only. `valid_until` is what the derive function subtracts against,\n"
   "NOT completed_at -- using the wrong one is the duplicate-assignment bug.")],
 inbound=[
  "The <strong>confirm page</strong> is static files in S3 behind CloudFront, reached through a "
  "signed link in the assignment message.",
  "<strong>Self-confirmation is refused</strong> by comparing the confirming identity with the "
  "subject on the first line of the handler, before any write.",
  "<strong>Assignment links</strong> are signed, scoped to one person and one requirement, and "
  "expire ninety days after the due date.",
  "<strong>Nothing is written back</strong> to the staff or requirements sheets. They are read "
  "and never modified."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "used only to match an externally worded qualification name against your requirement list.",
  "<strong>Called a handful of times a year</strong>, when somebody records an external "
  "certificate whose title does not exactly match a requirement.",
  "<strong>Grounded</strong> with your requirement names and aliases, so it picks one of yours "
  "or none.",
  "<strong>Output is a JSON schema</strong> with a requirement id and a confidence, both "
  "nullable. A null goes to a person with a pick list.",
  "<strong>Nothing else touches a model.</strong> Deriving a required-training list is set "
  "arithmetic, and set arithmetic should be code."],
 gotchas=[
  "Subtract on `valid_until`, not on `completed_at`. Getting this wrong asks people to redo "
  "training they did last month and destroys trust in the system immediately.",
  "Write only the difference on the nightly recompute. A full rewrite will re-send assignment "
  "messages for everything, every night.",
  "Put the grace period on the requirement. One global due window is wrong in both directions at "
  "once.",
  "Record an equivalent external qualification as a completion with its own expiry, never as a "
  "person-level exception. An exception has no end date.",
  "Report the gap by requirement, not by person. Six people waiting on one course date is a "
  "procurement task, and chasing six individuals will not move it."],
))
