"""Day 116 -- 2026-08-18 -- Delivery exception handler."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "delivery-exception-handler"
NAME = "Delivery exception handler"

SPEC = {
 "slug": SLUG, "date": "2026-08-18", "name": NAME,
 "tagline": ("Notices that a delivery has gone wrong before the customer tells you, which is "
             "harder than it sounds because carrier tracking statuses lie in predictable ways and "
             "the strongest signal is the absence of one."),
 "lede": ("A small system that watches outbound deliveries, works out which ones have genuinely "
          "gone wrong, decides which of those need somebody to act today, and tells the customer "
          "only what is actually known. The most useful signal in the whole system is a shipment "
          "that has not been scanned for four days, and no status code says that. Seven posts on "
          "the same system, one diagram at a time, with a cost breakdown and an engineering "
          "reference at the end."),
 "keywords": ["delivery exceptions", "carrier tracking", "ecommerce", "customer service",
              "logistics", "serverless"],
 "icons": ["truck", "alarm", "email"],
 "faq": [
  ("What is a delivery exception handler?",
   "A small serverless system that monitors outbound shipments, detects the ones that have gone "
   "wrong, triages them by what they actually need, and contacts the customer with what is "
   "known rather than what is hoped."),
  ("Why not just watch the carrier's exception statuses?",
   "Because they are unreliable in specific directions. An attempted delivery status is sometimes "
   "a driver who ran out of time, and a shipment genuinely lost in a depot usually carries no "
   "exception status at all."),
  ("What is the strongest signal that something is wrong?",
   "Silence. A shipment with no scan for several days is the most reliable indicator of a real "
   "problem, and it is the one no carrier reports."),
  ("Should you contact customers proactively?",
   "Yes, for the exceptions that will not resolve themselves, and with a specific caveat: never "
   "give a new delivery date you do not have. The post on this covers why."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "delivery-exception-handler-on-aws",
 "title": "A delivery exception handler on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Detects deliveries that have gone wrong, triages them, and tells customers only what "
          "is known. AWS, about $2 a month."),
 "og": ("The strongest signal that a parcel is lost is that nothing has happened to it for four "
        "days, and no carrier has a status code for that."),
 "abstract": ("The whole system on one page -- detect, triage, tell &mdash; and why the absence "
              "of a tracking event beats every exception code the carrier provides."),
 "lede": ("A customer emails on Thursday asking where their order is. Tracking says \"in "
          "transit\", which it has said since Saturday. Nobody looked, because nothing flagged "
          "it: there is no exception status, no failed delivery, no problem at all according to "
          "the carrier. The parcel has been sitting behind a roller door in a depot for five "
          "days. This post walks through a small system that notices on Tuesday."),
 "tags": ["delivery exceptions", "carrier tracking", "ecommerce", "customer service", "logistics",
          "serverless"],
 "takeaways": [
  "Silence is the signal. No scan for several days beats any exception code.",
  "Carrier statuses are unreliable in known directions and need translating.",
  "Triage matters: most exceptions resolve themselves and a few need action today.",
  "Never give a customer a delivery date you do not have.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Carrier tracking", "sub": ["events, and gaps"], "icon": "truck"},
      {"title": "The orders", "sub": ["what was promised"], "icon": "form"},
      {"title": "The customer", "sub": ["told what is known"], "icon": "person"}],
    "inside": [
      {"title": "Watcher", "sub": ["events and silence,", "both"], "icon": "search"},
      {"title": "Triage", "sub": ["will this fix", "itself?"], "icon": "filter"},
      {"title": "Contact", "sub": ["facts only,", "no invented dates"], "icon": "email"}],
    "edges": [{"from": 0, "to": 0, "label": "scans, or none"},
              {"from": 1, "to": 1, "label": "promised dates"},
              {"from": 2, "to": 2, "label": "one honest message", "up": True}],
    "note": "The watcher's most valuable input is the event that did not arrive."}),
   "Three things outside the account, three pieces inside it. The first box is doing something "
   "unusual: watching for nothing happening.",
   "System: delivery exceptions detected, triaged and communicated",
   "Three boxes across the top sit outside the AWS account. On the left, Carrier tracking, "
   "providing events and gaps. In the middle, The orders, holding what was promised. On the "
   "right, The customer, who is told what is known. Each connects by an arrow to the AWS account "
   "container below. Scans, or the absence of them, flow down into the account. Promised dates "
   "feed in. One honest message goes back out. Inside the AWS account are three components in a "
   "row. On the left, the Watcher, following events and silence both. In the middle, Triage, "
   "asking whether this will fix itself. On the right, Contact, sending facts only with no "
   "invented dates. A note at the bottom says the watcher's most valuable input is the event that "
   "did not arrive."),
  ("h3", "Why carrier statuses are not enough"),
  ("p", "Every carrier provides exception codes and they are genuinely useful for the cases they "
        "cover: address not found, refused, damaged in transit. The problem is what they do not "
        "cover, and the specific ways they mislead."),
  ("p", "\"Attempted delivery, nobody home\" is sometimes exactly that and is sometimes a driver "
        "who ran out of hours and needed to close the round. A parcel mis-sorted to the wrong "
        "depot generates no exception at all; it simply stops moving. And a shipment that was "
        "never actually collected shows as despatched forever, because the first scan never "
        "happened."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The watcher.</strong> Ingests tracking events and, more importantly, notices when "
   "they stop. Part 2.",
   "<strong>Triage.</strong> Sorts exceptions into the ones that fix themselves and the ones that "
   "need somebody today. Part 3.",
   "<strong>Contact.</strong> Tells the customer what is known, in the cases where telling them "
   "helps. Part 4.",
  ]),
  ("h2", "One exception, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Despatched", "sub": ["Friday"], "icon": "truck"},
      {"title": "Last scan", "sub": ["Saturday, in transit"], "icon": "search"},
      {"title": "Silence", "sub": ["Sun, Mon, Tue"], "icon": "clock"},
      {"title": "Flagged Tuesday", "sub": ["3 working days"], "icon": "alarm"},
      {"title": "Traced, told", "sub": ["before they asked"], "icon": "email"}],
    "title": "ONE EXCEPTION, END TO END",
    "note": "The carrier reported no problem at any point. The gap was the whole signal."}),
   "The same system as one line. Every stage after the second is driven by something not "
   "happening, which is why it needs a system rather than a dashboard.",
   "One stuck shipment detected from a gap in tracking events",
   "A horizontal row of five boxes joined by arrows. Despatched: Friday. Last scan: Saturday, in "
   "transit. Silence: Sunday, Monday, Tuesday. Flagged Tuesday: three working days. Traced and "
   "told: before they asked. A note says the carrier reported no problem at any point, and the "
   "gap was the whole signal."),
  ("h2", "In plain words"),
  ("p", "An order goes out on Friday. It is scanned into the network on Saturday morning and then "
        "nothing happens. Sunday is not a working day, Monday passes with no scan, Tuesday "
        "passes with no scan."),
  ("p", "On Tuesday afternoon the watcher flags it: three working days since the last event, "
        "against a service where the typical gap between scans is under a day. That threshold is "
        "not a guess &mdash; it comes from the carrier's own observed behaviour on that service, "
        "which the system has been measuring."),
  ("p", "Somebody raises a trace with the carrier on Tuesday and emails the customer: your parcel "
        "has not moved since Saturday, we have asked the carrier to find it, we will tell you "
        "tomorrow what they say. No new delivery date, because there is not one. That message is "
        "the entire product, and it lands two days before the customer would have written in "
        "annoyed."),
  ("callout", "Design rules that shaped every decision", [
   "Watch for silence, not just for exception codes.",
   "Thresholds come from each carrier and service's observed behaviour, not from a guess.",
   "Triage before contact. Most exceptions resolve themselves within a day.",
   "Never state a delivery date that is not a fact.",
   "One message per exception, and a follow-up only when something actually changed.",
   "Record which exceptions resolved on their own, so the thresholds can be tuned.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The failure mode this replaces is not that nobody cares about late deliveries; it is "
        "that nothing surfaces them until a customer does. Support then spends its time reacting "
        "to people who are already annoyed, on parcels that have been stuck for days, with no "
        "information beyond the tracking page the customer has already read."),
  ("p", "Shifting that by two days changes the interaction completely. The same problem, "
        "communicated first and honestly, generates a fraction of the support load and a "
        "different customer reaction, without any improvement in the actual delivery "
        "performance."),
  ("p", "The next four posts walk through each piece: how an exception is detected, what each "
        "kind actually needs, how the customer gets told, and what the exceptions reveal in "
        "aggregate. One diagram per post, a cost breakdown, and an engineering reference at the "
        "end."),
 ],
},
{
 "slug": "how-an-exception-is-detected",
 "title": "How an exception is detected",
 "nav": "How it is detected",
 "read": 5, "words": 750,
 "desc": ("Translating carrier statuses, measuring the normal gap between scans, and flagging the "
          "shipments that have gone quiet."),
 "og": ("Learn what a normal scan gap looks like for each carrier and service, and a shipment "
        "that exceeds it is a better signal than anything in the status field."),
 "abstract": ("How carrier statuses are normalised, why the gap between scans is measured per "
              "service, how the silence threshold is derived, and the shipment that never got a "
              "first scan."),
 "lede": ("Detection has two halves. Reading the exception codes is the easy half and catches the "
          "obvious cases. Noticing that nothing has happened is the half that catches the "
          "expensive ones."),
 "tags": ["carrier tracking", "detection", "logistics", "thresholds", "monitoring", "serverless"],
 "takeaways": [
  "Normalise carrier statuses into a small set of meanings; the raw codes differ wildly.",
  "Measure the typical gap between scans per carrier and service, from your own shipments.",
  "Flag at roughly three times the typical gap, in working days.",
  "The never-scanned shipment is a separate and common case.",
  "Keep the raw status alongside the normalised one, always.",
 ],
 "blocks": [
  ("h2", "Two detectors"),
  ("fig", ("chain", {
    "entry": {"title": "A tracking update", "sub": ["or the lack of one"], "icon": "truck"},
    "steps": [
      {"title": "An event arrived?", "sub": ["any scan at all"], "icon": "branch",
       "exit": {"title": "Check the gap", "sub": ["against this service's normal"],
                "icon": "clock", "label": "no"}},
      {"title": "Normalise the status", "sub": ["30+ codes to 8 meanings"], "icon": "filter"},
      {"title": "An exception meaning?", "sub": ["refused, address, damaged"], "icon": "branch",
       "exit": {"title": "Normal progress", "sub": ["record and move on"], "icon": "check",
                "label": "no"}},
      {"title": "Raise an exception", "sub": ["with the raw code kept"], "icon": "alarm"},
      {"title": "To triage", "sub": ["what does it need?"], "icon": "search"}],
    "note": "The first exit is the important one and it runs on a schedule, not on an event."}),
   "The two detection paths. One reacts to events; the other reacts to their absence and is where "
   "the value is.",
   "How a delivery exception is detected from events or from silence",
   "A vertical chain of five steps entered by a box labelled A tracking update, or the lack of "
   "one. Step one asks whether an event arrived at all; if not it exits to Check the gap against "
   "this service's normal. Step two normalises the status, mapping thirty or more codes to eight "
   "meanings. Step three asks whether it is an exception meaning such as refused, address problem "
   "or damaged; if not it exits to Normal progress, recorded and moved on. Step four raises an "
   "exception with the raw code kept. Step five passes it to triage to decide what it needs. A "
   "note says the first exit is the important one and runs on a schedule rather than on an event."),
  ("h3", "Normalising statuses"),
  ("p", "Carriers use dozens of status codes and no two use the same vocabulary. Mapping them to "
        "a small set &mdash; collected, in transit, out for delivery, delivered, attempted, "
        "address problem, refused, held &mdash; is unglamorous configuration work that makes "
        "everything downstream possible."),
  ("p", "Keep the raw code and text next to the normalised meaning, always. The mapping will be "
        "wrong sometimes, new codes appear, and a normalised value with no original is a fact you "
        "cannot check."),
  ("h2", "What normal looks like"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Next-day parcel", "parts": [("typical", 8), ("flag", 16)]},
      {"label": "Economy parcel", "parts": [("typical", 20), ("flag", 40)]},
      {"label": "Pallet freight", "parts": [("typical", 30), ("flag", 66)]}],
    "series": [("typical", "Typical gap between scans, hours", "#7AA116"),
               ("flag", "Additional hours before flagging", "#ED7100")],
    "unit": "",
    "note": "One threshold across all services either floods you or catches nothing."}),
   "Three services with very different normal behaviour. A single silence threshold cannot serve "
   "all three, which is why it is derived per service from your own shipment history.",
   "Typical gaps between tracking scans for three delivery services",
   "A stacked bar chart with three bars measured in hours. Two series: the typical gap between "
   "scans in green, and the additional hours before flagging in orange. A next-day parcel has a "
   "typical gap of eight hours and flags after a further sixteen. An economy parcel has a typical "
   "gap of twenty hours and flags after a further forty. Pallet freight has a typical gap of "
   "thirty hours and flags after a further sixty-six. A note says one threshold across all "
   "services either floods you or catches nothing."),
  ("p", "The numbers come from your own delivered shipments: take the gaps between consecutive "
        "scans on everything that arrived fine, and the flag threshold is roughly three times the "
        "typical one. That is a crude rule and it works considerably better than a number "
        "somebody chose."),
  ("p", "It also self-corrects. When a carrier changes their scanning practice &mdash; fewer "
        "intermediate scans is a common cost saving &mdash; the observed gaps widen and the "
        "threshold follows, instead of producing a wave of false exceptions that trains everybody "
        "to ignore them."),
  ("h3", "Working days, again"),
  ("p", "A gap over a weekend is not a gap. Every threshold here is in working hours against the "
        "carrier's own operating pattern, including the Saturday services that do scan and the "
        "ones that do not."),
  ("h2", "The shipment that never started"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Label printed", "sub": ["Monday"], "icon": "form"},
      {"title": "Marked despatched", "sub": ["in our system"], "icon": "check"},
      {"title": "Never scanned", "sub": ["no collection event"], "icon": "question"},
      {"title": "Still on a shelf", "sub": ["or in the wrong cage"], "icon": "storage"},
      {"title": "Flagged at 24h", "sub": ["a tighter rule"], "icon": "alarm"}],
    "title": "THE MOST COMMON EXCEPTION",
    "note": "It is entirely an internal failure and it is invisible without this check."}),
   "The never-collected shipment. It is the single most common real exception in most businesses "
   "and it has no carrier status at all, because the carrier has never seen it.",
   "A shipment that was marked despatched but never collected",
   "A horizontal row of five boxes. Label printed: Monday. Marked despatched in our system. Never "
   "scanned: no collection event. Still on a shelf, or in the wrong cage. Flagged at twenty-four "
   "hours: a tighter rule. A note says it is entirely an internal failure and is invisible "
   "without this check."),
  ("p", "This case deserves its own tighter threshold, because a parcel with no first scan after "
        "a day is almost always sitting somewhere in your own building. It is also the cheapest "
        "exception to fix, since the goods are within reach."),
  ("p", "It is worth counting separately for the same reason. A steady rate of never-collected "
        "shipments is a warehouse process problem wearing a carrier problem's clothes, and "
        "attributing it correctly is the first step to fixing it."),
  ("p", "Next: what each exception actually needs."),
 ],
},
{
 "slug": "what-each-exception-actually-needs",
 "title": "What each exception actually needs",
 "nav": "What each one needs",
 "read": 5, "words": 740,
 "desc": ("The ones that fix themselves, the ones that need action today, and the triage that "
          "keeps a queue from becoming noise."),
 "og": ("Most exceptions resolve themselves within a day. Acting on all of them is how a good "
        "signal becomes an ignored inbox."),
 "abstract": ("How exceptions are sorted by what they need, which categories self-resolve, the "
              "ones that need action within the hour, and why the queue must stay short."),
 "lede": ("An exception queue that contains everything unusual is a queue nobody works. The "
          "triage step exists to make it short enough that the items in it get acted on the same "
          "day."),
 "tags": ["delivery exceptions", "triage", "operations", "customer service", "queues",
          "serverless"],
 "takeaways": [
  "First attempted delivery resolves itself most of the time. Wait one cycle.",
  "Address problems and refusals need somebody today; the carrier is holding stock.",
  "A stuck shipment needs a trace raised, and traces have their own deadlines.",
  "Never-collected needs a warehouse check, not a carrier call.",
  "Keep the queue short enough to clear daily, or it stops being worked at all.",
 ],
 "blocks": [
  ("h2", "Four categories"),
  ("table", ["Exception", "Self-resolves?", "Action", "When"], [
   ["First attempted delivery", "Usually", "None; wait for the next attempt", "Next cycle"],
   ["Second attempted delivery", "No", "Contact the customer to arrange", "Same day"],
   ["Address problem", "Never", "Correct the address with the carrier", "Within hours"],
   ["Refused by recipient", "Never", "Find out why; it is often the wrong item", "Same day"],
   ["No scan, over threshold", "Sometimes", "Raise a trace", "Same day"],
   ["Never collected", "No", "Check the warehouse", "Within hours"],
   ["Damaged in transit", "No", "Replace, then claim", "Same day"],
  ]),
  ("p", "The first row is the one that determines whether this system is usable. First failed "
        "delivery attempts are common and most of them succeed on the next attempt without "
        "anybody doing anything. Treating them as exceptions requiring action produces a queue "
        "several times larger than the one that matters."),
  ("h2", "The queue has to stay short"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "All anomalies", "parts": [("act", 12), ("noise", 96)]},
      {"label": "After triage", "parts": [("act", 12), ("noise", 4)]}],
    "series": [("act", "Need action today", "#DD344C"),
               ("noise", "Will resolve without us", "#7D8CA3")],
    "unit": "",
    "note": "Same twelve real problems. One of these queues gets worked and one does not."}),
   "The effect of triage on a day's queue. The twelve items needing action are identical in both; "
   "only one version of the queue is short enough that somebody clears it.",
   "A day's exception queue before and after triage",
   "A stacked bar chart with two bars. Two series: items needing action today in red, and items "
   "that will resolve without intervention in grey. All anomalies: twelve needing action and "
   "ninety-six that will resolve themselves. After triage: twelve needing action and four "
   "remaining. A note says the same twelve real problems appear in both, and one of these queues "
   "gets worked while the other does not."),
  ("p", "This is the whole argument for triage and it is worth being explicit about, because the "
        "instinct when building a monitoring system is that more visibility is better. Beyond a "
        "certain queue length the visibility becomes zero, all at once, when the person "
        "responsible stops opening it."),
  ("h3", "Waiting is an action"),
  ("p", "Items that are expected to self-resolve are not discarded; they are held with a recheck "
        "time. A first attempted delivery is rechecked after the next delivery cycle, and if it "
        "attempted again and failed again, it comes back into the queue as a second attempt, "
        "which is a different category with a different action."),
  ("p", "That distinction is easy to build and easy to get wrong. Dropping self-resolving "
        "exceptions entirely means the second failure looks like the first one, and the customer "
        "waits another cycle for no reason."),
  ("h2", "Address problems are urgent"),
  ("fig", ("chain", {
    "entry": {"title": "Address problem", "sub": ["carrier cannot deliver"], "icon": "alarm"},
    "steps": [
      {"title": "Do we have a better one?", "sub": ["check the order history"], "icon": "branch",
       "exit": {"title": "Ask the customer", "sub": ["by whatever reaches them"], "icon": "email",
                "label": "no"}},
      {"title": "Correct it with the carrier", "sub": ["their window is short"], "icon": "truck"},
      {"title": "Held how long?", "sub": ["usually 3-5 days"], "icon": "clock"},
      {"title": "Past the hold window?", "sub": ["it returns to sender"], "icon": "branch",
       "exit": {"title": "Reship, do not wait", "sub": ["the return takes a week"],
                "icon": "check", "label": "yes"}},
      {"title": "Redelivery arranged", "sub": ["customer told"], "icon": "email"}],
    "note": "The hold window is short and unforgiving. After it, everything takes another week."}),
   "Why address problems are treated as urgent. The carrier's holding period is the constraint, "
   "and missing it converts a one-day fix into a two-week round trip.",
   "How an address problem exception is resolved before the carrier's hold expires",
   "A vertical chain of five steps entered by a box labelled Address problem, the carrier cannot "
   "deliver. Step one asks whether we have a better address in the order history; if not it exits "
   "to Ask the customer by whatever reaches them. Step two corrects it with the carrier, whose "
   "window is short. Step three asks how long it is held, usually three to five days. Step four "
   "asks whether it is past the hold window, after which it returns to sender; if so it exits to "
   "Reship, do not wait, because the return takes a week. Step five arranges redelivery and tells "
   "the customer. A note says the hold window is short and unforgiving, and after it everything "
   "takes another week."),
  ("p", "The fourth box is the judgement that most businesses get wrong by default. Waiting for a "
        "parcel to come back so it can be sent out again is intuitive and adds seven to ten days "
        "to a customer's wait. Reshipping immediately and dealing with the return separately is "
        "almost always cheaper once the support time and the goodwill are counted."),
  ("h3", "Refusals are usually information"),
  ("p", "A refused delivery is rarely somebody who changed their mind at the door. It is usually "
        "the wrong item, an unexpected charge, a duplicate they already received, or a delivery "
        "to a business that has no record of ordering it."),
  ("p", "So the action is to find out which, and the finding frequently belongs somewhere else "
        "entirely &mdash; a picking error, a duplicate order, a customs charge nobody warned "
        "about. Treating refusals as a delivery problem misses that most of them are not."),
  ("p", "Next: telling the customer."),
 ],
},
{
 "slug": "how-the-customer-gets-told",
 "title": "How the customer gets told",
 "nav": "How the customer is told",
 "read": 5, "words": 730,
 "desc": ("Why proactive contact works, the delivery date you must not invent, and the follow-up "
          "that only goes when something changed."),
 "og": ("A promised new date that slips is worse than no date at all. Say what you know and what "
        "you are doing about it."),
 "abstract": ("Why contacting first changes the interaction, the wording that works, why an "
              "invented delivery date is the worst possible move, and when not to contact at all."),
 "lede": ("The message is short, factual, and contains one thing most delivery updates do not: an "
          "admission that the next date is not known. That single omission is what makes it "
          "trustworthy."),
 "tags": ["customer service", "communication", "delivery exceptions", "expectations", "ecommerce",
          "serverless"],
 "takeaways": [
  "Contacting first turns an angry inbound into a neutral outbound.",
  "Say what happened, what you are doing, and when you will next say something.",
  "Never state a delivery date that is not a fact. \"We do not know yet\" is acceptable.",
  "Follow up only when something changed, and always at the time you said.",
  "Do not contact for exceptions that will resolve before the message is read.",
 ],
 "blocks": [
  ("h2", "The message"),
  ("callout", "The whole thing, four lines", [
   "<strong>What happened:</strong> \"Your parcel has not moved since Saturday. That usually "
   "means it has been mis-sorted somewhere in the network.\"",
   "<strong>What we are doing:</strong> \"We have asked the carrier to locate it, which they aim "
   "to do within two working days.\"",
   "<strong>What we do not know:</strong> \"We cannot give you a delivery date until they come "
   "back to us.\"",
   "<strong>When you will hear:</strong> \"I will email you on Thursday either way, even if there "
   "is no news.\"",
   "<strong>Signed by a person,</strong> with a reply-to that reaches them.",
   "<strong>No apology paragraph,</strong> no discount, no unprompted compensation. Those come "
   "later if it is warranted.",
  ]),
  ("p", "The third line is the one that feels wrong to write and is the reason the message works. "
        "Every customer has received a delivery update containing a confident new date that then "
        "passed with nothing arriving, and the effect of that is considerably worse than "
        "uncertainty stated plainly."),
  ("h3", "The date you must not invent"),
  ("p", "The pressure to give a date comes from wanting to be helpful, and from support systems "
        "with a field labelled \"new expected delivery\". Filling that field with an estimate "
        "converts a manageable problem into a broken promise the moment it slips, which for a "
        "genuinely lost parcel is most of the time."),
  ("p", "The honest alternative costs nothing: name the carrier's own service level for the "
        "trace, and commit to a communication date rather than a delivery date. \"I will tell you "
        "on Thursday\" is a promise you control entirely."),
  ("h2", "When not to contact"),
  ("fig", ("chain", {
    "entry": {"title": "An exception, triaged", "sub": ["needs action"], "icon": "alarm"},
    "steps": [
      {"title": "Will it resolve today?", "sub": ["first attempt, held for pickup"],
       "icon": "branch",
       "exit": {"title": "Do not contact", "sub": ["the carrier already did"], "icon": "stop",
                "label": "yes"}},
      {"title": "Does the carrier notify?", "sub": ["most do, for attempts"], "icon": "branch",
       "exit": {"title": "Do not duplicate", "sub": ["two messages is worse than one"],
                "icon": "stop", "label": "yes"}},
      {"title": "Do we know something", "sub": ["they cannot see?"], "icon": "branch",
       "exit": {"title": "Wait until we do", "sub": ["a message with no content"],
                "icon": "clock", "label": "no"}},
      {"title": "Contact them", "sub": ["once, with the four lines"], "icon": "email"},
      {"title": "Follow up when promised", "sub": ["even with no news"], "icon": "check"}],
    "note": "Three gates before contacting. A message that adds nothing costs trust."}),
   "When proactive contact helps and when it does not. The third gate is the one that keeps the "
   "message meaningful.",
   "The three checks before proactively contacting a customer about a delivery",
   "A vertical chain of five steps entered by a box labelled An exception, triaged and needing "
   "action. Step one asks whether it will resolve today, as with a first attempt or a parcel held "
   "for pickup; if so it exits to Do not contact, because the carrier already did. Step two asks "
   "whether the carrier notifies the customer, which most do for attempts; if so it exits to Do "
   "not duplicate, because two messages is worse than one. Step three asks whether we know "
   "something they cannot see; if not it exits to Wait until we do, since it would be a message "
   "with no content. Step four contacts them once, with the four lines. Step five follows up when "
   "promised, even with no news. A note says three gates fire before contacting, and a message "
   "that adds nothing costs trust."),
  ("h3", "The follow-up with no news"),
  ("p", "This is the step that is always cut and is the one customers remember. An email on "
        "Thursday saying the carrier has not come back yet, we have chased them, and we will "
        "write again on Monday, is more reassuring than silence followed by good news."),
  ("p", "It is also cheap, because the system already knows what was promised and to whom. The "
        "reason it gets cut is that it feels like admitting failure, which it is, and the "
        "alternative is a customer who assumes they have been forgotten, which they have."),
  ("h2", "What this does to support volume"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Reactive", "parts": [("inbound", 84), ("outbound", 0)]},
      {"label": "Proactive", "parts": [("inbound", 19), ("outbound", 61)]}],
    "series": [("inbound", "Customer contacts us, annoyed", "#DD344C"),
               ("outbound", "We contact first, neutral", "#7AA116")],
    "unit": "",
    "note": "Roughly the same conversations. Very different starting temperature."}),
   "A quarter of delivery exceptions handled two ways. The total volume barely moves; what changes "
   "is who started the conversation and in what mood.",
   "Inbound versus outbound delivery contacts under reactive and proactive handling",
   "A stacked bar chart with two bars. Two series: the customer contacting us annoyed in red, and "
   "us contacting first in a neutral tone in green. Reactive handling produces eighty-four "
   "inbound contacts and no outbound. Proactive handling produces nineteen inbound and sixty-one "
   "outbound. A note says these are roughly the same conversations with a very different starting "
   "temperature."),
  ("p", "The honest reading of that chart is that proactive contact does not reduce the work by "
        "much. What it changes is that the work happens on your schedule, with information "
        "already gathered, in a conversation that starts neutral rather than at a complaint."),
  ("p", "It also moves the work earlier, which for the genuinely lost parcels means the trace is "
        "raised while the carrier can still find it, rather than eight days later when the answer "
        "is a write-off."),
  ("p", "Next: what the exceptions reveal."),
 ],
},
{
 "slug": "what-the-exceptions-reveal",
 "title": "What the exceptions reveal",
 "nav": "What they reveal",
 "read": 5, "words": 710,
 "desc": ("Address quality, one depot, one service, and the internal failures that were being "
          "counted as carrier problems."),
 "og": ("A quarter of delivery exceptions usually turn out to be things that happened before the "
        "parcel left the building."),
 "abstract": ("How exceptions aggregate by cause, why address quality is the largest fixable "
              "category, the depot finding, and separating internal failures from carrier ones."),
 "lede": ("Handled individually, delivery exceptions are a cost. Counted properly, they are the "
          "clearest available picture of where a fulfilment operation is actually failing."),
 "tags": ["delivery exceptions", "patterns", "addresses", "reporting", "operations", "serverless"],
 "takeaways": [
  "Separate internal causes from carrier causes before reporting anything.",
  "Address quality is usually the largest single fixable cause.",
  "Exceptions cluster by depot and postcode more sharply than by carrier.",
  "Report rate per thousand shipments, not counts.",
  "The never-collected count is a warehouse metric wearing a carrier's uniform.",
 ],
 "blocks": [
  ("h2", "Whose failure was it"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Ours, before despatch", "sub": ["never collected,", "wrong item"], "icon": "storage",
       "label": "about a quarter"},
      {"title": "The customer's data", "sub": ["address, phone,", "access notes"], "icon": "form",
       "label": "about a third"},
      {"title": "The carrier's", "sub": ["mis-sort, damage,", "missed round"], "icon": "truck",
       "label": "the rest"}],
    "target": {"title": "One exception report", "sub": ["split by cause"], "icon": "chart",
               "then": {"title": "Two thirds are ours", "sub": ["to fix, not to negotiate"],
                        "icon": "check"}},
    "note": "Reported together, they all look like carrier problems. They are mostly not."}),
   "The three sources of delivery exceptions. Splitting them is the difference between a carrier "
   "negotiation and a fixable internal problem.",
   "Three sources of delivery exceptions and their approximate shares",
   "Three boxes stacked on the left. Ours, before despatch, covering never collected and wrong "
   "item, labelled about a quarter. The customer's data, covering address, phone and access "
   "notes, labelled about a third. And The carrier's, covering mis-sorts, damage and missed "
   "rounds, labelled the rest. All three converge on One exception report split by cause, and "
   "that leads down to Two thirds are ours, to fix rather than to negotiate. A note says reported "
   "together they all look like carrier problems, and they are mostly not."),
  ("h3", "Address quality"),
  ("p", "The largest single fixable category in most businesses, and it is fixable at the point "
        "of order rather than at the point of delivery. Flats without a number, business "
        "addresses with no company name, postcodes that do not match the street, and phone "
        "numbers that were never asked for."),
  ("p", "The exception data points precisely at which of those matter. If failed deliveries "
        "cluster on addresses with no second line, adding a prompt at checkout for flat and unit "
        "numbers is a half-day of work that removes a recurring cost permanently."),
  ("h2", "Depots, not carriers"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Carrier overall", "parts": [("rate", 3.1)]},
      {"label": "Depot: north", "parts": [("rate", 2.4)]},
      {"label": "Depot: central", "parts": [("rate", 2.8)]},
      {"label": "Depot: one site", "parts": [("rate", 11.6)]}],
    "series": [("rate", "Exceptions per 1,000 shipments", "#ED7100")],
    "unit": "",
    "note": "The carrier's overall rate is fine. One depot is four times everything else."}),
   "The same carrier broken down by delivery depot. An acceptable overall rate can hide a single "
   "site that is producing most of the problems.",
   "Delivery exception rates for one carrier broken down by depot",
   "A bar chart with four bars showing exceptions per thousand shipments. The carrier overall is "
   "three point one. The north depot is two point four. The central depot is two point eight. One "
   "particular site is eleven point six. A note says the carrier's overall rate is fine and one "
   "depot is four times everything else."),
  ("p", "This finding is actionable in a way a carrier-level number is not. Carriers know which "
        "of their sites are struggling, and a conversation that names one depot with a rate and a "
        "sample size gets a specific response, where \"your service has been poor\" gets a "
        "general one."),
  ("p", "In some cases the answer is to route deliveries for those postcodes through a different "
        "service, which is a decision that only becomes visible once the data is cut this way."),
  ("h3", "Rates, not counts"),
  ("p", "As with damage claims, counts blame whoever you use most and whichever region you sell "
        "into most. Exceptions per thousand shipments, computed per carrier, per service and per "
        "depot, is the only version of this report that supports a decision."),
  ("h2", "What the report says"),
  ("callout", "The monthly page", [
   "<strong>Shipments:</strong> 4,180. <strong>Exceptions:</strong> 61, a rate of 14.6 per "
   "thousand.",
   "<strong>Internal, before despatch:</strong> 16 &mdash; 11 never collected, 5 wrong item.",
   "<strong>Address or contact data:</strong> 22 &mdash; 14 of them flats with no unit number.",
   "<strong>Carrier:</strong> 23, of which 14 were one depot.",
   "<strong>Resolved without customer contact:</strong> 38. <strong>Contacted first:</strong> 19. "
   "<strong>Customer contacted us first:</strong> 4.",
   "<strong>Average days from exception to resolution:</strong> 2.8, against 6.1 before this "
   "existed.",
  ]),
  ("p", "The third line is the one that produces a change. Fourteen failed deliveries in a month "
        "to flats with no unit number is a checkout form problem with a number attached, and it "
        "is not something anybody would have guessed from handling the exceptions one at a time."),
  ("p", "The last line is the honest measure of whether the system is working. Not how many "
        "exceptions there are &mdash; that is mostly outside your control &mdash; but how long "
        "they stay unresolved, which is entirely within it."),
  ("h3", "The uncomfortable finding"),
  ("p", "Most businesses running this analysis for the first time find that a substantial "
        "minority of what they had been treating as carrier failures happened in their own "
        "warehouse. That is unwelcome and it is the most valuable thing in the report, because "
        "internal problems can be fixed without anybody's cooperation."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="shipment",
 volumes=[(1000, "1,000 shipments"), (4000, "4,000 shipments"), (15000, "15,000 shipments")],
 read_each=0.0,
 msgs_each=0.02,
 lede=("There is no model in this system, exceptions are a small fraction of shipments, and "
       "tracking events are the volume. Four thousand shipments a month is a healthy small "
       "retailer. Here is where each cent goes."),
 takeaway_extra=("Tracking event writes dominate; messages are sent on about one shipment in "
                 "seventy."),
 risks=[
  "<strong>Polling every shipment every hour.</strong> Poll on a schedule proportional to the "
  "service's typical scan gap, and stop polling once delivered.",
  "<strong>Never expiring tracking events.</strong> Events on delivered shipments are useful for "
  "computing the gap thresholds and then not at all. Ninety days is plenty.",
  "<strong>Storing every webhook payload verbatim.</strong> Keep the raw status and text; the "
  "full payload is mostly carrier boilerplate repeated on every event.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. The messaging band is per "
                "shipment, not per exception, which is why it looks small."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="de",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the status normalisation, and how the silence sweep works."),
 outside=[
  {"title": "Carrier APIs", "sub": ["webhooks and polling"], "icon": "truck"},
  {"title": "The order system", "sub": ["read only"], "icon": "database"},
  {"title": "SES and the queue", "sub": ["customers, and staff"], "icon": "email"}],
 inside=[
  {"title": "Function URL + EventBridge", "sub": ["webhooks,", "hourly silence sweep"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["ingest, sweep, notify"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["shipments, exceptions"], "icon": "database"}],
 note="us-east-1. One account. Thresholds derived weekly from delivered shipments' own scan gaps.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Carrier APIs, providing webhooks and "
  "polling. The order system, read only. And SES and the queue, reaching customers and staff. "
  "Inside the account, three groups. A Function URL for webhooks and EventBridge running an "
  "hourly silence sweep. Three Lambda functions named ingest, sweep and notify. And two DynamoDB "
  "tables named shipments and exceptions. A note gives the region as us-east-1, one account, and "
  "states that thresholds are derived weekly from delivered shipments' own scan gaps."),
 functions=[
  ["<code>de-ingest</code>", "Function URL, carrier webhooks",
   "Normalises the status, updates last_event_at, raises event-based exceptions",
   "10s / 512&nbsp;MB"],
  ["<code>de-sweep</code>", "EventBridge, hourly",
   "Finds shipments past their silence threshold; runs triage; sets recheck times",
   "300s / 1024&nbsp;MB"],
  ["<code>de-notify</code>", "SQS",
   "Sends the four-line message and the promised follow-up, even with no news",
   "15s / 512&nbsp;MB"]],
 roles=[
  ["<code>de-ingest-role</code>", "<code>dynamodb:UpdateItem</code>, <code>dynamodb:PutItem</code>",
   "Shipments and exceptions"],
  ["<code>de-sweep-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>sqs:SendMessage</code>",
   "Both tables; the notify queue"],
  ["<code>de-notify-role</code>", "<code>ses:SendEmail</code>, <code>dynamodb:UpdateItem</code>",
   "One verified identity; exceptions"]],
 tables=[
  ("Table: shipments",
   "PK   tracking_ref      S\n"
   "     order_id          S\n"
   "     carrier           S\n"
   "     service           S   the threshold is keyed on carrier#service\n"
   "     despatched_at     S\n"
   "     last_event_at     S   the field the silence sweep queries\n"
   "     last_status_raw   S   the carrier's own code and text, kept\n"
   "     last_status       S   normalised: in_transit | attempted | address | ...\n"
   "     delivered_at      S   set once; the sweep stops looking\n"
   "     ttl               N   epoch, +90 days after delivery\n\n"
   "GSI1: last_status + last_event_at  -- the silence sweep is one query\n"
   "per active status band, not a scan across every shipment."),
  ("Table: exceptions",
   "PK   tracking_ref      S\n"
   "SK   raised_at         S\n"
   "     kind              S   silence | attempted | address | refused\n"
   "                           | never_collected | damaged\n"
   "     cause             S   internal | customer_data | carrier\n"
   "     recheck_at        S   set for self-resolving kinds\n"
   "     contacted_at      S   null if we deliberately did not contact\n"
   "     promised_update   S   the date we said we would write again\n"
   "     resolved_at       S\n"
   "     resolution        S   delivered | reshipped | refunded | traced_lost\n\n"
   "`cause` is assigned at triage and is what makes the aggregate report\n"
   "separate internal failures from carrier ones.")],
 inbound=[
  "<strong>Webhooks where available, polling where not.</strong> Poll intervals are proportional "
  "to the service's typical scan gap and stop entirely once delivered.",
  "<strong>The silence sweep is a GSI query</strong>, not a scan. Shipments are indexed by status "
  "and last event time, so the sweep touches only what could be overdue.",
  "<strong>Thresholds are recomputed weekly</strong> from the observed scan gaps on delivered "
  "shipments, per carrier and service, so a carrier changing their scanning practice does not "
  "produce a wave of false exceptions.",
  "<strong>Order data is read, never written.</strong> This system has no write access to the "
  "order system."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Status normalisation is a mapping table and "
  "detection is a timestamp comparison.",
  "<strong>The tempting use</strong> is predicting which shipments will fail. It would produce a "
  "score over the same data the thresholds already use, with less explainability.",
  "<strong>A second tempting use</strong> is drafting the customer message. The four lines are a "
  "template with two substitutions, and Part 4 is about why the wording should not vary.",
  "<strong>Classifying free-text carrier notes</strong> into causes is defensible where a carrier "
  "sends prose rather than codes, and the raw text is kept beside it.",
  "<strong>The cost page assumes none</strong>, which is why tracking writes are the only "
  "meaningful variable."],
 gotchas=[
  "Derive silence thresholds from your own delivered shipments per carrier and service. A single "
  "global threshold either floods the queue or catches nothing.",
  "Keep the raw carrier status next to the normalised one. New codes appear and the mapping will "
  "be wrong sometimes.",
  "Give never-collected a tighter threshold and its own category. It is usually the most common "
  "exception and it is entirely internal.",
  "Hold self-resolving exceptions with a recheck time rather than discarding them, or the second "
  "failed attempt looks like the first.",
  "Never write a predicted delivery date into a customer message. A promised communication date "
  "is a promise you control."],
))
