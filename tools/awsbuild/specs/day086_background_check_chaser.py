"""Day 86 -- 2026-07-19 -- Background check chaser."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "background-check-chaser"
NAME = "Background check chaser"

SPEC = {
 "slug": SLUG, "date": "2026-07-19", "name": NAME,
 "tagline": ("A new starter's checks -- references, right to work, the disclosure -- get "
             "tracked as three separate clocks, each chased at whoever is actually holding it "
             "up, so day one is not a surprise."),
 "lede": ("A small system that tracks the pre-employment checks for each new starter as "
          "separate items with separate owners, works out which one is genuinely blocking a "
          "start date, and chases the person who can move it. It never stores a check result "
          "and never decides whether somebody can start. Seven posts on the same system -- one "
          "diagram at a time -- with a cost breakdown and an engineering reference at the end."),
 "keywords": ["onboarding", "pre-employment checks", "references", "right to work", "hiring",
              "serverless"],
 "icons": ["check", "clock", "team"],
 "faq": [
  ("What is a background check chaser?",
   "A small serverless system that tracks each pre-employment check for a new starter as its "
   "own item with its own owner and expected duration, and chases whoever is holding one up. "
   "It tracks status only -- never a result -- and a person decides whether somebody starts."),
  ("Does it store check results?",
   "No, and that is a deliberate architectural boundary. It records that a check is "
   "outstanding, chased, or complete. What a disclosure actually said lives wherever your HR "
   "records live, under whatever controls apply to it, and never passes through this system."),
  ("Why track checks separately rather than as one onboarding status?",
   "Because they have different owners and wildly different durations. A reference is a "
   "referee's problem and takes days; a disclosure is an agency's and takes weeks. A single "
   "amber status tells you nothing about which one to chase or who to chase."),
  ("Can it stop somebody starting?",
   "No. It reports which checks are outstanding against a start date and how likely each is to "
   "land in time. Whether somebody starts is a judgement with legal and commercial weight, and "
   "it belongs to a person."),
  ("What does it cost to run?",
   "A couple of dollars a month. Hiring volume in a small business is low. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "background-check-chaser-on-aws",
 "title": "A background check chaser on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 900,
 "desc": ("Tracks each pre-employment check as its own clock with its own owner, and chases "
          "whoever is actually holding up a start date. AWS, about $2 a month."),
 "og": ("Three checks, three clocks, three owners. The system chases the one that is genuinely "
        "blocking the start date, at the person who can move it."),
 "abstract": ("The whole system on one page -- a tracker, a predictor and a chaser -- plus the "
              "boundary that keeps it simple: it holds statuses, never results."),
 "lede": ("Somebody accepts a job and a start date is agreed. Between those two things sit "
          "three or four checks, each owned by a different person, each with a different "
          "duration, and none of them visible in one place. Two weeks before the start date "
          "somebody asks how onboarding is going, gets a confident answer, and discovers on the "
          "Friday that one reference has not replied since the original request. This post "
          "walks through a small system that turns that into three clocks anybody can read."),
 "tags": ["onboarding", "pre-employment checks", "references", "hiring", "human in the loop",
          "serverless"],
 "takeaways": [
  "Each check is its own item, with its own owner and its own expected duration.",
  "The system holds statuses only. Results live in HR records and never pass through it.",
  "Chasing goes to whoever is actually holding it up, which is often not the candidate.",
  "The useful output is one sentence: which check will not land before the start date.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Checks", "sub": ["referees, agency,", "the candidate"], "icon": "team"},
      {"title": "Check list", "sub": ["types, owners,", "usual durations"], "icon": "doc"},
      {"title": "Whoever hires", "sub": ["one sentence per starter"], "icon": "person"}],
    "inside": [
      {"title": "Tracker", "sub": ["one item per check,", "status only"], "icon": "check"},
      {"title": "Predictor", "sub": ["will it land before", "the start date?"], "icon": "counter"},
      {"title": "Chaser", "sub": ["whoever is holding", "this one up"], "icon": "bell"}],
    "edges": [{"from": 0, "to": 0, "label": "status updates"},
              {"from": 1, "to": 1, "label": "durations"},
              {"from": 2, "to": 2, "label": "what will be late", "up": True}],
    "note": "No check result ever enters this system. It knows outstanding, chased, done."}),
   "Three things outside the account, three pieces inside it. The boundary at the bottom is the "
   "important one: statuses in, statuses out, and nothing sensitive in between.",
   "System: check statuses in, a start-date prediction out",
   "Three boxes across the top sit outside the AWS account. On the left, Checks: the referees, "
   "the screening agency and the candidate, who between them own the outstanding items. In the "
   "middle, Check list: the types of check your business runs, who owns each and how long each "
   "usually takes. On the right, Whoever hires: the person who receives one sentence per "
   "starter. Each connects by an arrow to the AWS account container below. Status updates flow "
   "down into the account. The check list feeds in expected durations. A prediction of what "
   "will be late goes back out. Inside the AWS account are three components in a row. On the "
   "left, the Tracker, holding one item per check with a status and nothing else. In the "
   "middle, the Predictor, which asks whether each check will land before the start date. On "
   "the right, the Chaser, which contacts whoever is actually holding a check up. A note at the "
   "bottom says no check result ever enters this system, which knows only outstanding, chased "
   "and done."),
  ("h3", "The boundary"),
  ("p", "It is worth stating the design's most important constraint before anything else: this "
        "system never sees a check result. Not a disclosure certificate, not a reference's "
        "content, not a right-to-work document. It knows that a check exists, who owns it, when "
        "it was requested, and whether it has come back."),
  ("p", "That is not squeamishness; it is what keeps the system small enough to be worth "
        "building. The moment it holds a disclosure result it acquires a retention policy, a "
        "legal basis, an access control model, a subject access request path and a "
        "conversation with your insurer. Statuses have none of that, and statuses are where all "
        "the useful chasing lives."),
  ("h3", "What runs on every starter (the inside)"),
  ("ul", [
   "<strong>The tracker.</strong> Creates one item per required check when a starter is added, "
   "from the check list for that role. Each item has an owner, a requested date, an expected "
   "duration and a status. That is the whole model, and its simplicity is the point.",
   "<strong>The predictor.</strong> Compares each outstanding item's expected completion "
   "against the start date. The output is not a percentage; it is one of three words &mdash; "
   "comfortable, tight, or will not make it &mdash; because a hiring manager needs to act on it "
   "rather than interpret it.",
   "<strong>The chaser.</strong> Contacts the owner of the specific item. A reference that has "
   "not come back is chased at the referee, not the candidate. A disclosure sitting with an "
   "agency is chased at the agency. Getting that right is most of the value, because chasing "
   "the candidate about something they cannot influence is both useless and unpleasant.",
  ]),
  ("h2", "One starter, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Offer accepted", "sub": ["start date set"], "icon": "check"},
      {"title": "Checks created", "sub": ["four items, four owners"], "icon": "form"},
      {"title": "Predicted", "sub": ["three fine, one tight"], "icon": "counter"},
      {"title": "Chased", "sub": ["at the referee"], "icon": "bell"},
      {"title": "Clear", "sub": ["or a decision to make"], "icon": "person"}],
    "title": "ONE STARTER, END TO END",
    "note": "The fifth box is a person's decision. The system never makes it."}),
   "The same system as one line. Every stage except the last is bookkeeping; the last is "
   "deliberately left to a human.",
   "One new starter from offer to clearance, in five stages",
   "A horizontal row of five boxes joined by arrows. Offer accepted: a start date is set. Checks "
   "created: four items with four owners. Predicted: three are comfortable and one is tight. "
   "Chased: at the referee who is holding it up. Clear: or a decision for a person to make. A "
   "note says the fifth box is a person's decision and the system never makes it."),
  ("h2", "In plain words"),
  ("p", "An offer is accepted on the 2nd with a start date of the 28th. Four checks are created "
        "from the list for that role: two references, a right-to-work verification and a "
        "standard disclosure. The references are owned by the referees, the right to work by the "
        "candidate, and the disclosure by the agency. Expected durations are five days, five "
        "days, two days and eighteen days respectively."),
  ("p", "By the 12th, the right to work is done and one reference has come back. The disclosure "
        "was submitted on the 4th so it is due around the 22nd, which is comfortable. The second "
        "reference has had no reply in ten days against a five-day expectation, so the predictor "
        "marks it tight and the chaser emails the referee directly &mdash; not the candidate, "
        "who has no way to make their old manager answer an email. On the 16th the hiring "
        "manager gets one sentence: \"One item at risk for K. Osei starting the 28th: reference "
        "from Ashford Ltd, requested 2nd, no reply, chased twice.\" That sentence is the entire "
        "product, and it arrives twelve days before it would otherwise have become a problem."),
  ("callout", "Design rules that shaped every decision", [
   "Statuses only, never results. Holding a disclosure result would cost more in policy than "
   "the whole system saves.",
   "One item per check, with its own owner. A single onboarding status hides which of four "
   "things is late and who can fix it.",
   "Chase the person who can move it. Chasing a candidate about an agency's backlog is useless "
   "and makes their first impression of you a nag.",
   "Predict in words, not percentages. Comfortable, tight, or will not make it &mdash; because "
   "the reader has to act, not interpret.",
   "The start date is a fact about a plan, not a deadline the system enforces. It never blocks "
   "anything.",
   "A check that comes back is closed by a person, because \"came back\" and \"is satisfactory\" "
   "are different statements.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Pre-employment checks fail as a process for a specific and slightly unfair reason: the "
        "person with the most incentive to chase them &mdash; the candidate &mdash; is the "
        "person with the least ability to do so. They cannot make a referee reply, cannot "
        "escalate inside a screening agency, and are reluctant to nag anybody while they are "
        "still being onboarded."),
  ("p", "So the design moves the chasing to the one party who can actually address each item, "
        "and it does so without asking anybody at your end to keep a mental model of four "
        "parallel clocks. The output is deliberately tiny: a sentence naming the item that will "
        "not land, twelve days before it becomes a Friday afternoon problem."),
  ("p", "The next four posts walk through each piece: how a starter's checks get created, how "
        "an update arrives without a result attached, how the prediction works, and how the "
        "chasing picks its target. One diagram per post, a cost breakdown, and an engineering "
        "reference at the end."),
 ],
},
{
 "slug": "how-a-starters-checks-get-created",
 "title": "How a starter's checks get created",
 "nav": "How checks are created",
 "read": 5, "words": 800,
 "desc": ("One offer produces four items with four owners, why the check list is per role, and "
          "the checks that must not be created until a later step."),
 "og": ("An offer becomes four independent items with four owners. Which checks apply comes "
        "from the role, and some of them must not exist yet."),
 "abstract": ("How one accepted offer becomes four independent items with four owners, why the "
              "list is per role rather than per company, and the checks that deliberately are "
              "not created on day one."),
 "lede": ("Almost all of the value in this system comes from a decision made in the first "
          "second of a starter's existence: how many things to track, and who owns each. Get "
          "that wrong and everything downstream is chasing the wrong person about the wrong "
          "item."),
 "tags": ["onboarding", "pre-employment checks", "hiring", "role requirements", "DynamoDB",
          "serverless"],
 "takeaways": [
  "The checks come from the role, not from the company. A driver needs things an office hire does not.",
  "Each item gets exactly one owner, and the owner is whoever can make it move.",
  "Some checks must not be created on day one; they depend on an earlier one completing.",
  "The expected duration is a property of the check type, revised from your own history.",
  "A starter with no start date yet is tracked, but nothing is predicted or chased.",
 ],
 "blocks": [
  ("h2", "The check list, per role"),
  ("table", ["Check", "Owner", "Usual duration", "Applies to"], [
   ["Reference 1", "The referee", "5 days", "Everyone"],
   ["Reference 2", "The referee", "5 days", "Everyone"],
   ["Right to work", "The candidate", "2 days", "Everyone"],
   ["Standard disclosure", "The screening agency", "18 days", "Roles with a requirement"],
   ["Licence check", "The candidate", "3 days", "Drivers"],
   ["Medical", "The clinic", "21 days", "Drivers, some site roles"],
   ["Professional registration", "The candidate", "4 days", "Regulated roles"],
  ]),
  ("p", "The owner column is the one that matters and the one most systems get wrong by "
        "defaulting everything to the candidate. A reference is owned by the referee: they are "
        "the only party who can produce it. Recording that means chasing lands where it can do "
        "something, which is covered in Part 5."),
  ("h2", "Creating the items"),
  ("fig", ("chain", {
    "entry": {"title": "Offer accepted", "sub": ["role and start date"], "icon": "check"},
    "steps": [
      {"title": "Which checks apply?", "sub": ["from the role"], "icon": "filter",
       "side": {"title": "Check list", "sub": ["per role, per type"], "icon": "doc"}},
      {"title": "Who owns each?", "sub": ["referee, candidate, agency"], "icon": "team",
       "exit": {"title": "Ask for a referee", "sub": ["candidate supplies"], "icon": "person",
                "label": "unknown"}},
      {"title": "Can it start now?", "sub": ["some depend on others"], "icon": "branch",
       "exit": {"title": "Hold it", "sub": ["created, not started"], "icon": "clock",
                "label": "blocked"}},
      {"title": "Request and record", "sub": ["date requested, expected"], "icon": "log",
       "side": {"title": "DynamoDB checks", "sub": ["one item each"], "icon": "database"}},
      {"title": "Clocks running", "sub": ["independently"], "icon": "counter"}],
    "note": "Held items exist from day one, so the plan is honest about what has not started."}),
   "How an accepted offer becomes a set of independent items. Items that cannot start yet are "
   "created and held rather than being invisible, so the plan reflects the whole sequence.",
   "How a new starter's checks are created as separate tracked items",
   "A vertical chain of five steps entered by a box labelled Offer accepted, carrying a role and "
   "a start date. Step one asks which checks apply, taken from the check list per role and per "
   "type. Step two asks who owns each, being the referee, the candidate or the agency; an "
   "unknown owner exits to Ask for a referee, which the candidate supplies. Step three asks "
   "whether each check can start now, since some depend on others; a blocked check exits to Hold "
   "it, created but not started. Step four requests and records each check with its requested "
   "and expected dates in a DynamoDB checks table, one item each. Step five is Clocks running, "
   "independently. A note says held items exist from day one so that the plan is honest about "
   "what has not started."),
  ("h3", "Checks that must wait"),
  ("p", "Some checks cannot be requested until another has completed, and creating them as "
        "running clocks on day one produces a plan that is quietly wrong. A disclosure usually "
        "cannot be submitted until identity has been verified. A medical is often only booked "
        "once an offer is unconditional."),
  ("p", "So those items are created immediately and held. They appear in the plan with a "
        "dependency &mdash; \"disclosure: waiting on identity verification\" &mdash; and their "
        "clock starts when the blocker clears. The predictor accounts for both durations, which "
        "is what makes it possible to say on day one that a twenty-eight-day start date is "
        "already unrealistic."),
  ("h3", "Where a referee comes from"),
  ("p", "Almost the only thing the candidate is asked for directly, and it is worth asking for "
        "it well: a name, a relationship and an email address, twice. The most common cause of a "
        "late reference is not a slow referee; it is a reference request sent to a shared "
        "recruitment address at a company where nobody owns it. A named individual with a direct "
        "address halves the typical turnaround."),
  ("h2", "Expected durations"),
  ("p", "The duration on each check type starts as a guess and should be replaced by your own "
        "history within a few months. The system records how long each completed check actually "
        "took, and the median for a type is a far better expectation than anything an agency's "
        "brochure claims."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Reference", "sub": ["median 6 days"], "icon": "email"},
      {"title": "Right to work", "sub": ["median 1 day"], "icon": "doc"},
      {"title": "Disclosure", "sub": ["median 22 days"], "icon": "shield"},
      {"title": "Medical", "sub": ["median 26 days"], "icon": "clock"},
      {"title": "Slowest wins", "sub": ["the start date follows it"], "icon": "counter"}],
    "title": "YOUR OWN DURATIONS, NOT THE BROCHURE'S",
    "note": "The last box is the whole planning insight: the slowest check sets the earliest start."}),
   "Real durations from your own completed checks. The last box is the fact that makes offer "
   "conversations honest: the earliest realistic start is set by the slowest item.",
   "Median durations for four check types, and what they imply",
   "A horizontal row of five boxes. Reference: median six days. Right to work: median one day. "
   "Disclosure: median twenty-two days. Medical: median twenty-six days. Slowest wins: the start "
   "date follows the slowest check. A note says the last box is the whole planning insight, "
   "because the slowest check sets the earliest realistic start."),
  ("p", "That last observation is worth acting on before any chasing happens. If your medical "
        "median is twenty-six days and somebody agrees a three-week start date for a driver, no "
        "amount of chasing will fix it, and the honest thing is to say so on the day the offer "
        "is accepted rather than on the Friday before."),
  ("p", "Next: how a status update arrives without dragging a result along with it."),
 ],
},
{
 "slug": "how-a-check-update-arrives",
 "title": "How a check update arrives",
 "nav": "How updates arrive",
 "read": 5, "words": 790,
 "desc": ("Three ways a check comes back, why the system reads a status and deliberately not "
          "the attachment, and how a person closes an item."),
 "og": ("A reply arrives with a reference attached. The system reads that it arrived and files "
        "the attachment somewhere it never looks -- because status is all it should ever hold."),
 "abstract": ("Three ways a check comes back, why the attachment is filed somewhere the system "
              "never reads, and why an item is closed by a person rather than by an arrival."),
 "lede": ("This post is mostly about something the system does not do. A reference reply arrives "
          "as an email with a PDF attached, and the interesting engineering decision is to read "
          "the fact of it and nothing else."),
 "tags": ["onboarding", "pre-employment checks", "data minimisation", "SES inbound", "privacy",
          "serverless"],
 "takeaways": [
  "Three lanes: an email reply, a form the owner fills in, and a manual mark-complete.",
  "The system records that a check came back. It does not read what it said.",
  "Attachments are handed straight to HR storage and never enter this system's buckets.",
  "\"Arrived\" and \"satisfactory\" are different, and only a person can set the second.",
  "An update against an unknown check is a question, never a new item.",
 ],
 "blocks": [
  ("h2", "Three lanes"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Email reply", "sub": ["referee, agency"], "icon": "email", "label": "arrived"},
      {"title": "A short form", "sub": ["one link per check"], "icon": "form", "label": "status"},
      {"title": "Marked by hand", "sub": ["HR knows it landed"], "icon": "person",
       "label": "manual"}],
    "target": {"title": "One status change", "sub": ["outstanding to", "arrived"],
               "icon": "check",
               "then": {"title": "Closed by a person", "sub": ["arrived is not satisfactory"],
                        "icon": "team"}},
    "note": "Whatever the lane, only a status moves. The content goes elsewhere entirely."}),
   "Three ways a check comes back and one thing that changes as a result. The second box "
   "underneath is the important one: arrival and acceptance are separate events with separate "
   "actors.",
   "Three update lanes converging on one status change",
   "Three boxes stacked on the left. Email reply, from a referee or an agency, labelled arrived. "
   "A short form, one link per check, labelled status. And Marked by hand, when HR knows "
   "something landed, labelled manual. All three converge on One status change, moving an item "
   "from outstanding to arrived. Below it, connected by a downward arrow, is Closed by a person, "
   "noting that arrived is not the same as satisfactory. A note says whatever the lane, only a "
   "status moves and the content goes elsewhere entirely."),
  ("h2", "What happens to the attachment"),
  ("p", "A reference reply arrives at a monitored address with a PDF attached. The system needs "
        "to know that it arrived. It does not need, and must not have, the contents."),
  ("fig", ("chain", {
    "entry": {"title": "Reply arrives", "sub": ["with an attachment"], "icon": "email"},
    "steps": [
      {"title": "Which check?", "sub": ["thread, or the token"], "icon": "search",
       "side": {"title": "DynamoDB checks", "sub": ["outstanding items"], "icon": "database"},
       "exit": {"title": "Ask HR", "sub": ["never guess a match"], "icon": "person",
                "label": "no match"}},
      {"title": "Forward the whole thing", "sub": ["to HR storage, untouched"], "icon": "external"},
      {"title": "Record: arrived", "sub": ["date and lane only"], "icon": "log"},
      {"title": "Delete the copy", "sub": ["nothing retained here"], "icon": "stop"},
      {"title": "Tell HR to review", "sub": ["a person closes it"], "icon": "team"}],
    "note": "Step four is the whole privacy design: the content passes through and is not kept."}),
   "What happens to a reply with a reference attached. The system is a relay for the content and "
   "a record for the status, and it keeps only the second.",
   "How a check reply is handled without retaining its content",
   "A vertical chain of five steps entered by a box labelled Reply arrives, with an attachment. "
   "Step one asks which check it belongs to, matched by mail thread or by a token in the "
   "request, against the outstanding items in a DynamoDB checks table; no match exits to Ask HR, "
   "because a match is never guessed. Step two forwards the whole message to HR storage "
   "untouched. Step three records only that it arrived, with the date and the lane. Step four "
   "deletes the copy, retaining nothing here. Step five tells HR to review, since a person "
   "closes the item. A note says step four is the whole privacy design: the content passes "
   "through and is not kept."),
  ("h3", "Why relay rather than store"),
  ("p", "Storing a reference or a disclosure would give this system a data class it is not built "
        "for. It would need retention rules, access controls tied to HR roles, a deletion path "
        "for subject access requests, and a place in whatever record of processing your business "
        "keeps. All of that is real work, and none of it makes the chasing any better."),
  ("p", "Relaying costs one forward and one delete, and it means the honest answer to \"what "
        "does this system hold about candidates\" is: their name, their start date, and a list "
        "of check statuses. That is a sentence you can say to anybody."),
  ("h2", "Arrived is not satisfactory"),
  ("p", "The status a reply produces is <em>arrived</em>, and the item stays open. Somebody in "
        "HR reads the reference and closes it, which is a second status of <em>cleared</em> or "
        "<em>needs a conversation</em>. Collapsing those into one status would be a small "
        "simplification with a large failure mode: a reference that arrived and raised a concern "
        "would show as green."),
  ("ul", [
   "<strong>Outstanding.</strong> Requested, nothing back.",
   "<strong>Chased.</strong> Requested, chased at least once, nothing back. Tracked separately "
   "because it changes the prediction.",
   "<strong>Arrived.</strong> Something came back and is with HR. The clock stops; the item is "
   "not closed.",
   "<strong>Cleared.</strong> A person has read it and is satisfied. Only a person sets this.",
   "<strong>Needs a conversation.</strong> A person has read it and it is not straightforward. "
   "The system does not know why and does not ask.",
   "<strong>Withdrawn.</strong> The check is no longer required, usually because the offer "
   "changed. Recorded rather than deleted.",
  ]),
  ("h3", "An update with no matching check"),
  ("p", "A reply that cannot be matched to an outstanding item is not silently discarded and is "
        "not used to create one. It goes to HR with the message intact and a note saying it "
        "could not be matched. In practice it is usually a referee replying to a request for a "
        "different candidate, or a reply landing after an item was already closed by hand, and "
        "both of those are worth a human glance."),
  ("p", "Next: how the prediction works, and why it speaks in three words."),
 ],
},
{
 "slug": "how-the-start-date-prediction-works",
 "title": "How the start date prediction works",
 "nav": "How it predicts",
 "read": 5, "words": 790,
 "desc": ("Three words rather than a percentage, how a chased item is treated differently from "
          "a fresh one, and the dependency arithmetic that makes a day-one warning possible."),
 "og": ("Comfortable, tight, or will not make it. Three words a hiring manager can act on, "
        "computed from your own durations and the dependencies between checks."),
 "abstract": ("Why the prediction is three words rather than a percentage, how a chased item is "
              "treated differently from a fresh one, and the dependency arithmetic that makes a "
              "day-one warning possible."),
 "lede": ("The prediction is the smallest piece of arithmetic in this series and the part people "
          "want to over-engineer. It resists a model, resists a probability, and resists a "
          "dashboard, and the reason is that its entire audience is one busy person who needs to "
          "decide whether to move a start date."),
 "tags": ["onboarding", "pre-employment checks", "forecasting", "hiring", "reporting",
          "serverless"],
 "takeaways": [
  "Three outcomes: comfortable, tight, will not make it. No percentages.",
  "Expected completion is the request date plus your own median for that check type.",
  "A chased item that has not moved gets its expectation extended, not reset.",
  "Held items add their blocker's remaining time to their own duration.",
  "The day-one prediction is the most valuable one, because the start date can still move.",
 ],
 "blocks": [
  ("h2", "Three words"),
  ("fig", ("chain", {
    "entry": {"title": "An outstanding check", "sub": ["and a start date"], "icon": "clock"},
    "steps": [
      {"title": "Expected completion", "sub": ["requested + median"], "icon": "counter",
       "side": {"title": "Your own history", "sub": ["median per type"], "icon": "chart"}},
      {"title": "Blocked by another?", "sub": ["add its remaining time"], "icon": "branch",
       "exit": {"title": "Chain the durations", "sub": ["both, in sequence"], "icon": "filter",
                "label": "yes"}},
      {"title": "Chased and still silent?", "sub": ["extend, do not reset"], "icon": "branch",
       "exit": {"title": "Add the chase lag", "sub": ["from your history"], "icon": "retry",
                "label": "yes"}},
      {"title": "Compare with the start date", "icon": "search"},
      {"title": "One of three words", "sub": ["comfortable / tight /", "will not make it"],
       "icon": "check"}],
    "note": "No probability. A hiring manager needs to act, and 68% is not an action."}),
   "How each outstanding check gets its one-word verdict. The chase-lag step matters: a chased "
   "item that is still silent is slower than a fresh one, not faster.",
   "How an outstanding check is predicted against a start date",
   "A vertical chain of five steps entered by a box labelled An outstanding check, together with "
   "a start date. Step one computes expected completion as the request date plus your own median "
   "for that check type, read from your own history. Step two asks whether it is blocked by "
   "another check; if so it exits to Chain the durations, adding both in sequence. Step three "
   "asks whether it has been chased and is still silent; if so it exits to Add the chase lag, "
   "taken from your history. Step four compares the result with the start date. Step five "
   "produces one of three words: comfortable, tight, or will not make it. A note says there is "
   "no probability, because a hiring manager needs to act and sixty-eight per cent is not an "
   "action."),
  ("h3", "Why not a percentage"),
  ("p", "A percentage invites interpretation, and interpretation is exactly what the reader has "
        "no time for. \"Seventy-two per cent likely to complete before the start date\" requires "
        "somebody to decide what to do at seventy-two, and different people will decide "
        "differently on different days."),
  ("p", "Three words remove that. Comfortable means do nothing. Tight means chase it today. Will "
        "not make it means have a conversation about the start date this week. The thresholds "
        "that produce those words live in the check list, so if your business wants tight to "
        "start earlier that is an edit rather than an argument."),
  ("h3", "The chase lag"),
  ("p", "The subtle bit. A reference requested nine days ago with a five-day median is late, and "
        "the naive response is to expect it tomorrow. But a check that has already blown through "
        "its median and been chased once is empirically much slower than a fresh one &mdash; the "
        "referee is on leave, the address is wrong, the agency has a backlog."),
  ("p", "So a chased item's expectation is extended by the median time from first chase to "
        "arrival, taken from your own completed checks. In practice that is usually another week "
        "or more, and it is what turns a cheerful \"due tomorrow\" into an honest \"this will not "
        "make the 28th\"."),
  ("h2", "The day-one prediction"),
  ("p", "The most valuable output of this system arrives on the day the offer is accepted, "
        "before anything has been chased, when the start date is still a proposal rather than a "
        "commitment."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Offer accepted", "sub": ["start proposed: 21 days"], "icon": "check"},
      {"title": "Medical", "sub": ["median 26 days"], "icon": "clock"},
      {"title": "Depends on", "sub": ["offer unconditional: +3"], "icon": "branch"},
      {"title": "Earliest realistic", "sub": ["29 days"], "icon": "counter"},
      {"title": "Said on day one", "sub": ["not on the Friday"], "icon": "email"}],
    "title": "THE MOST USEFUL SENTENCE THE SYSTEM WRITES",
    "note": "Nobody chased anything wrong here. The date was never achievable."}),
   "The day-one arithmetic. This is the one case where the system prevents a problem rather than "
   "surfacing one, and it costs nothing but a subtraction.",
   "How a start date is checked for realism on the day an offer is accepted",
   "A horizontal row of five boxes. Offer accepted: a start date twenty-one days out is "
   "proposed. Medical: median twenty-six days. Depends on: the offer becoming unconditional, "
   "adding three days. Earliest realistic: twenty-nine days. Said on day one: rather than on the "
   "Friday before. A note says nobody chased anything wrong here and the date was never "
   "achievable."),
  ("p", "There is no cleverness in that calculation at all. It is one addition and one "
        "comparison, and the only reason it is not done routinely by hand is that it requires "
        "knowing your own median durations, which nobody records. The system records them as a "
        "by-product of doing everything else."),
  ("callout", "What the prediction is careful about", [
   "It never predicts a result, only an arrival. Whether a check comes back clear is not "
   "something it knows or should guess at.",
   "It uses your medians, not the provider's stated turnaround. Those differ, consistently, in "
   "one direction.",
   "It extends rather than resets on a chase. A silent chased item is slower than a fresh one.",
   "It says nothing about the candidate. A slow reference is a fact about a referee.",
  ]),
  ("p", "Next: how the chasing picks who to contact."),
 ],
},
{
 "slug": "how-the-chasing-picks-its-target",
 "title": "How the chasing picks its target",
 "nav": "How it picks a target",
 "read": 5, "words": 790,
 "desc": ("Chasing the referee rather than the candidate, what a good reference chase actually "
          "says, and the escalation that goes sideways rather than up."),
 "og": ("A reference chase sent to the candidate cannot work. Chasing the party who can move an "
        "item -- and escalating sideways to a second referee rather than upward -- is the whole "
        "design."),
 "abstract": ("Why chasing the referee beats chasing the candidate, what a good reference chase "
              "says, and the escalation that goes sideways to an alternative rather than "
              "upward to a manager."),
 "lede": ("This is the part that makes the system worth having rather than merely tidy. Chasing "
          "is easy to do and almost always aimed at the wrong person, which converts a process "
          "problem into a relationship problem with somebody who has not started yet."),
 "tags": ["onboarding", "pre-employment checks", "references", "escalation", "Amazon SES",
          "serverless"],
 "takeaways": [
  "Chase the party who owns the item, which for a reference is the referee.",
  "A reference chase is short, names the candidate, and makes replying trivially easy.",
  "Escalation goes sideways -- to an alternative referee -- before it goes anywhere else.",
  "The candidate is told what is happening, but is never the target of a chase they cannot act on.",
  "An agency is chased with the reference number, because that is the only thing they can act on.",
 ],
 "blocks": [
  ("h2", "Who owns which item"),
  ("fig", ("system", {
    "outside": [
      {"title": "The referee", "sub": ["owns a reference"], "icon": "person"},
      {"title": "The agency", "sub": ["owns a disclosure"], "icon": "external"},
      {"title": "The candidate", "sub": ["owns their own documents"], "icon": "team"}],
    "inside": [
      {"title": "Owner lookup", "sub": ["per item, from", "the check list"], "icon": "filter"},
      {"title": "Chase builder", "sub": ["short, specific,", "easy to answer"], "icon": "doc"},
      {"title": "Sideways escalation", "sub": ["a second referee,", "not a manager"], "icon": "retry"}],
    "edges": [{"from": 0, "to": 0, "label": "the reference", "up": True},
              {"from": 1, "to": 1, "label": "the certificate", "up": True},
              {"from": 2, "to": 2, "label": "their documents", "up": True}],
    "note": "The candidate is kept informed and is never chased about somebody else's item."}),
   "Who gets chased about what. The candidate appears in this diagram as an owner of their own "
   "documents only, which is the entire point.",
   "How chasing is routed to the party who owns each check",
   "Three boxes across the top outside the AWS account. The referee, who owns a reference. The "
   "agency, which owns a disclosure. And the candidate, who owns their own documents. Inside the "
   "account, three components. Owner lookup, which finds the owner per item from the check list. "
   "Chase builder, which writes something short, specific and easy to answer. And Sideways "
   "escalation, which goes to a second referee rather than to a manager. Arrows show each party "
   "returning what only they can produce. A note says the candidate is kept informed and is "
   "never chased about somebody else's item."),
  ("h3", "What a reference chase says"),
  ("callout", "Four lines, and no more", [
   "<strong>Line one.</strong> Who and why. \"We asked you for a reference for Kwame Osei on 2 "
   "July.\"",
   "<strong>Line two.</strong> What is needed. \"Three questions, about two minutes.\"",
   "<strong>Line three.</strong> One link, going straight to a form with the candidate's details "
   "already filled in. No login.",
   "<strong>Line four.</strong> An out. \"If you are not the right person, reply and tell us who "
   "is.\"",
   "<strong>Nothing else.</strong> No deadline framed as urgency, no company boilerplate, no "
   "compliance language, and no chasing tone. A referee is doing you a favour.",
  ]),
  ("p", "The fourth line earns its place surprisingly often. A large proportion of unanswered "
        "reference requests are sitting with somebody who left, moved team, or was never the "
        "right contact, and giving them a one-line way to say so is faster than any number of "
        "reminders to a person who cannot help."),
  ("h2", "Sideways, not upward"),
  ("p", "The instinct with an unresponsive referee is to escalate: chase harder, involve the "
        "candidate, tell a manager. All three make things worse. The referee does not work for "
        "you, the candidate cannot compel them, and nobody at your end has any leverage."),
  ("fig", ("chain", {
    "entry": {"title": "Reference not back", "sub": ["past the median"], "icon": "clock"},
    "steps": [
      {"title": "Chase the referee", "sub": ["short, one link"], "icon": "email",
       "exit": {"title": "Replied", "sub": ["item arrives"], "icon": "check", "label": "yes"}},
      {"title": "Still silent?", "sub": ["after 5 days"], "icon": "branch",
       "exit": {"title": "Try a second address", "sub": ["if the candidate has one"],
                "icon": "search", "label": "yes"}},
      {"title": "Still silent?", "sub": ["after 5 more"], "icon": "branch",
       "side": {"title": "The candidate", "sub": ["asked for an alternative"], "icon": "person"},
       "exit": {"title": "New referee", "sub": ["a fresh item, fresh clock"], "icon": "retry",
                "label": "yes"}},
      {"title": "Tell whoever hires", "sub": ["with the dates"], "icon": "team"}],
    "note": "The third step replaces the item rather than pushing harder on a dead one."}),
   "The escalation ladder for an unresponsive referee. The useful move is to replace the item, "
   "which resets the clock honestly rather than pretending a silent request is nearly done.",
   "How an unanswered reference request is escalated sideways",
   "A vertical chain of four steps entered by a box labelled Reference not back, past the "
   "median. Step one chases the referee with something short carrying one link; a reply exits to "
   "Replied and the item arrives. Step two asks whether it is still silent after five days, "
   "exiting to Try a second address if the candidate supplied one. Step three asks again after "
   "five more days, involving the candidate to ask for an alternative referee, and exits to New "
   "referee, which is a fresh item with a fresh clock. Step four tells whoever is hiring, with "
   "the dates. A note says the third step replaces the item rather than pushing harder on a dead "
   "one."),
  ("p", "Asking the candidate for an alternative referee is the one moment they are involved, "
        "and the framing matters: it is not \"your referee is not replying, sort it out\", it is "
        "\"we have not been able to reach X &mdash; is there somebody else who could speak to "
        "that role?\" The first version makes their new employer's onboarding feel like a "
        "problem they caused. The second is a normal request."),
  ("h2", "Chasing an agency"),
  ("p", "Different in tone and much simpler. An agency has a case reference and a queue, and the "
        "only thing that moves either is a specific enquiry quoting the reference. So an agency "
        "chase is one line with the reference number and the submission date, sent to whatever "
        "address they publish, and repeated at a cadence that matches their stated turnaround "
        "rather than your impatience."),
  ("p", "The one genuinely useful escalation with an agency is the median: \"submitted on the "
        "4th; your published turnaround is fourteen days and our last six have averaged "
        "twenty-two.\" That is a factual sentence, it is frequently news to the person reading "
        "it, and it is only available because the system has been recording durations all along."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="check",
 volumes=[(12, "12 checks"), (40, "40 checks"), (150, "150 checks")],
 read_each=0.0014, msgs_each=3.4,
 lede=("Hiring volume in a small business is low and the model barely features: this system is "
       "almost entirely email and a scheduled sweep. Twelve checks a month is roughly three "
       "starters. Here is where each cent goes."),
 takeaway_extra=("Messaging is the largest variable line here, because chasing is the whole "
                 "product -- and email at this volume is still fractions of a cent."),
 risks=[
  "<strong>Storing what you relayed.</strong> The privacy design depends on the copy being "
  "deleted after forwarding. A bucket that quietly retains reference PDFs turns a status "
  "tracker into a system with a retention policy and a legal basis to document.",
  "<strong>Chasing on a fixed cadence rather than the owner's.</strong> Emailing an agency "
  "every two days against a fourteen-day turnaround is noise that gets you filtered, and being "
  "filtered by a screening agency is genuinely expensive.",
  "<strong>Log retention left at never.</strong> This system does very little most days and "
  "will otherwise be almost entirely a CloudWatch bill within a year.",
 ],
 per_unit_note=("The model is barely used here &mdash; only to match an inbound reply to an "
                "outstanding item where the thread headers do not settle it. Most updates cost "
                "nothing at all."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="bc",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the one table, the relay path, and the deliberately small data model."),
 outside=[
  {"title": "SES inbound", "sub": ["a monitored address"], "icon": "email"},
  {"title": "Check list", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "HR storage", "sub": ["where content goes"], "icon": "external"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["transient relay,", "daily sweep"], "icon": "bucket"},
  {"title": "Lambda x3", "sub": ["create, update, chase"], "icon": "lambda"},
  {"title": "DynamoDB x1", "sub": ["checks"], "icon": "database"}],
 note="us-east-1. One account. One table, statuses only. No check result is ever stored.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. SES inbound, receiving mail at a "
  "monitored address. The Check list, read through the Google Sheets API read-only. And HR "
  "storage, which is where any content is forwarded. Inside the account, three groups. S3 used "
  "only as a transient relay, and EventBridge carrying a daily sweep. Three Lambda functions "
  "named create, update and chase. And a single DynamoDB table named checks. A note gives the "
  "region as us-east-1, one account, one table holding statuses only, and states that no check "
  "result is ever stored."),
 functions=[
  ["<code>bc-create</code>", "Function URL",
   "Builds the check items for a starter from the role's list", "10s / 512&nbsp;MB"],
  ["<code>bc-update</code>", "S3 ObjectCreated (SES)",
   "Matches a reply to an item, relays the content, deletes the copy",
   "30s / 1024&nbsp;MB"],
  ["<code>bc-chase</code>", "EventBridge daily",
   "Predicts, chases the owner, escalates sideways, sends the summary",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>bc-create-role</code>",
   "<code>dynamodb:PutItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "The checks table; the Sheets credential only"],
  ["<code>bc-update-role</code>",
   "<code>s3:GetObject</code>/<code>DeleteObject</code>, <code>ses:SendRawEmail</code>",
   "The relay prefix; one verified identity"],
  ["<code>bc-chase-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "The checks table; one verified identity"]],
 tables=[
  ("Table: checks",
   "PK   starter_id        S   st_2026_07_02_9a11\n"
   "SK   check_id          S   reference#1\n"
   "     type              S   reference | right_to_work | disclosure | medical\n"
   "     owner_kind        S   referee | candidate | agency | clinic\n"
   "     owner_contact     S   an address, not a name\n"
   "     status            S   held | outstanding | chased | arrived |\n"
   "                           cleared | conversation | withdrawn\n"
   "     depends_on        S   another check_id, or null\n"
   "     requested_at      S   2026-07-02\n"
   "     expected_days     N   5\n"
   "     chased_at         L   [ISO timestamps]\n"
   "     arrived_at        S   set by the relay, not by a person\n"
   "     closed_by         S   set only by a person\n"
   "     ttl               N   epoch, +2 years\n\n"
   "There is no field on this item for a check RESULT, and adding one changes\n"
   "what the system is. Content is relayed to HR storage and deleted.\n\n"
   "GSI  status-index        PK status, SK requested_at   -- the daily sweep")],
 inbound=[
  "An SES <strong>receipt rule set</strong> on the monitored address writes the whole message "
  "to a short-lived S3 prefix with a one-day lifecycle rule as a backstop.",
  "<strong>The relay deletes its own copy</strong> after forwarding to HR storage. The "
  "lifecycle rule exists only in case the delete fails.",
  "<strong>Matching</strong> uses <code>In-Reply-To</code> first, then a token in the reference "
  "form link, and asks a human third. It never matches on candidate name alone.",
  "<strong>Reference forms</strong> are signed, scoped to one check, single-use, and expire "
  "sixty days after the request."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "used only when thread headers and tokens both fail to match a reply to an item.",
  "<strong>It is given the subject line and the first few lines of the body</strong>, never the "
  "attachment and never the full message.",
  "<strong>Output is a JSON schema</strong> with a candidate check id and a confidence. Below "
  "the floor it returns null and the message goes to a human.",
  "<strong>It never reads a result.</strong> The prompt is a matching task, and the content that "
  "would let it form a view on a reference is not in the prompt.",
  "<strong>Most updates never reach it</strong> because a threaded reply or a form token settles "
  "the match for free."],
 gotchas=[
  "Do not add a result field. It is the one change that turns this from a small tracker into a "
  "system with a legal basis, a retention schedule and a subject access path.",
  "Delete the relay copy in code, and keep the lifecycle rule as a backstop rather than as the "
  "mechanism.",
  "Chase at the owner's cadence, not yours. An agency chased every two days against a "
  "fourteen-day turnaround will filter you.",
  "Escalate sideways. Replacing an unresponsive referee resets the clock honestly; pushing "
  "harder on a dead request does not.",
  "Compute medians from your own completed checks. Published turnarounds are consistently "
  "optimistic, and the difference is the whole planning error."],
))
