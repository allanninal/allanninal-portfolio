"""Day 126 -- 2026-08-28 -- Visitor check-in logger."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "visitor-checkin-logger"
NAME = "Visitor check-in logger"

SPEC = {
 "slug": SLUG, "date": "2026-08-28", "name": NAME,
 "tagline": ("Keeps an accurate list of who is in the building, which is a fire safety question "
             "rather than a security one -- and which means the hard part is not signing people "
             "in but getting them signed out."),
 "lede": ("A small system that records visitors arriving, works hard at recording them leaving, "
          "produces a roll call that can be read on a phone in a car park, and collects "
          "considerably less personal data than the paper book it replaces. Seven posts on the "
          "same system, one diagram at a time, with a cost breakdown and an engineering reference "
          "at the end."),
 "keywords": ["visitor management", "fire safety", "reception", "data minimisation", "facilities",
              "serverless"],
 "icons": ["person", "shield", "clock"],
 "faq": [
  ("What is a visitor check-in logger?",
   "A small serverless system that records who has entered a building and, more importantly, who "
   "has left, so that an accurate roll call exists during an evacuation."),
  ("Why is checking out harder than checking in?",
   "Because people are motivated to check in -- they want to be let through -- and have no reason "
   "at all to check out. Most visitor logs are wrong by mid-afternoon."),
  ("What data does it actually need?",
   "A name, who they are visiting, and a time. Almost everything else that visitor books collect "
   "is unnecessary and creates an obligation."),
  ("Should it take photographs?",
   "Only if there is a specific reason that has been thought about. A photograph of every visitor "
   "is a biometric dataset acquired without a purpose."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "visitor-checkin-logger-on-aws",
 "title": "A visitor check-in logger on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Records who is in the building, works at getting people signed out, and collects very "
          "little. AWS, about $2 a month."),
 "og": ("The purpose of a visitor log is a fire roll call. Every design decision follows from "
        "that and most visitor books fail it."),
 "abstract": ("The whole system on one page -- in, out, roll call &mdash; and why the check-out "
              "problem is the one worth engineering around."),
 "lede": ("The alarm goes at ten past three. Somebody carries the visitor book to the assembly "
          "point and reads out fourteen names. Nine of those people left before lunch and did not "
          "sign out, two are contractors who never signed in, and one name is illegible. That "
          "list is the reason the building is not being re-entered, and it is wrong."),
 "tags": ["visitor management", "fire safety", "reception", "data minimisation", "facilities",
          "serverless"],
 "takeaways": [
  "The roll call is the purpose. Design backwards from it.",
  "Checking out is the hard problem; checking in is nearly automatic.",
  "Collect a name, a host and a time. Very little else is needed.",
  "Delete on a short clock. A visitor log is not an archive.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "People arriving", "sub": ["visitors, contractors,", "deliveries"], "icon": "person"},
      {"title": "Their hosts", "sub": ["who is expecting them"], "icon": "email"},
      {"title": "The assembly point", "sub": ["a phone, outside,", "possibly raining"], "icon": "shield"}],
    "inside": [
      {"title": "Check in", "sub": ["thirty seconds,", "minimal data"], "icon": "form"},
      {"title": "Check out", "sub": ["the hard part"], "icon": "clock"},
      {"title": "Roll call", "sub": ["current, readable,", "offline"], "icon": "counter"}],
    "edges": [{"from": 0, "to": 0, "label": "arrivals"},
              {"from": 1, "to": 1, "label": "expected visits"},
              {"from": 2, "to": 2, "label": "who is inside", "up": True}],
    "note": "The third box is the product. The first two exist to make it accurate."}),
   "Three things outside the account, three pieces inside it. Everything is designed backwards "
   "from the roll call on the right.",
   "System: visitors checked in and out, producing a roll call",
   "Three boxes across the top sit outside the AWS account. On the left, People arriving: "
   "visitors, contractors and deliveries. In the middle, Their hosts, who are expecting them. On "
   "the right, The assembly point: a phone, outside, possibly raining. Each connects by an arrow "
   "to the AWS account container below. Arrivals flow down into the account. Expected visits feed "
   "in. Who is inside goes back out. Inside the AWS account are three components in a row. On the "
   "left, Check in: thirty seconds, minimal data. In the middle, Check out, the hard part. On the "
   "right, the Roll call: current, readable and offline. A note at the bottom says the third box "
   "is the product and the first two exist to make it accurate."),
  ("h3", "The purpose is the roll call"),
  ("p", "Visitor management systems are usually sold on security, and for most buildings that is "
        "not what they are for. A determined person is not stopped by a screen asking for their "
        "name, and the great majority of visitors are exactly who they say they are."),
  ("p", "What the log genuinely does is answer one question at one moment: who is inside this "
        "building right now? That question is asked during an evacuation, it has to be answered "
        "in a car park on a phone with no wifi, and the answer has to be right."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Check in.</strong> Fast, minimal, and it notifies the host. Parts 2 and 3.",
   "<strong>Check out.</strong> Several mechanisms, because one is never enough. Part 4.",
   "<strong>The roll call.</strong> Current, sorted usefully, and available when the network is "
   "not. Part 2.",
  ]),
  ("h2", "One visit, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Arrives 09:40", "sub": ["name, host, done"], "icon": "form"},
      {"title": "Host notified", "sub": ["immediately"], "icon": "email"},
      {"title": "On the roll call", "sub": ["from that second"], "icon": "shield"},
      {"title": "Leaves 11:20", "sub": ["taps out, or the host does"], "icon": "clock"},
      {"title": "Deleted in 30 days", "sub": ["name and all"], "icon": "stop"}],
    "title": "ONE VISIT, END TO END",
    "note": "Four of these five steps are easy. The fourth is the whole subject."}),
   "The same system as one line. The check-out step has several mechanisms behind it because no "
   "single one works reliably.",
   "One visitor from arrival through to record deletion",
   "A horizontal row of five boxes joined by arrows. Arrives at nine forty: name, host, done. "
   "Host notified immediately. On the roll call from that second. Leaves at eleven twenty: taps "
   "out, or the host does. Deleted in thirty days, name and all. A note says four of these five "
   "steps are easy and the fourth is the whole subject."),
  ("h2", "In plain words"),
  ("p", "Somebody arrives at twenty to ten. They type their name and choose who they are visiting "
        "from a list. That is the whole check-in: no company field, no car registration, no "
        "purpose of visit, no photograph. Their host gets a message saying they have arrived."),
  ("p", "From that moment they are on the roll call. If the alarm goes at ten past ten, the "
        "assembly point list has their name, their host's name, and the time they arrived."),
  ("p", "At twenty past eleven they leave. Ideally they tap out on the way past; if they do not, "
        "their host can check them out from a message; if neither happens, an automatic prompt "
        "goes to the host in the afternoon. Thirty days later the record is deleted, because a "
        "list of everybody who has visited the building is not something to keep indefinitely."),
  ("callout", "Design rules that shaped every decision", [
   "The roll call has to work offline, on a phone, outside.",
   "Collect the minimum: name, host, time. Justify anything else.",
   "Never collapse into a single check-out mechanism; use several.",
   "The roll call shows uncertainty rather than hiding it.",
   "Delete on a short clock, automatically.",
   "Nobody sees anybody else's name on the screen.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The paper visitor book has two well-known problems and one that gets less attention. It "
        "is not signed out, so it overstates who is present. It is illegible, so the roll call is "
        "read out as guesses. And it displays every previous visitor's name and their host to "
        "everybody who signs in, which is a disclosure nobody intended."),
  ("p", "All three are fixable cheaply, and the third one is fixed simply by using a screen that "
        "shows one person's entry at a time. That is worth doing on its own."),
  ("p", "The next four posts walk through each piece: what the log is actually for, how little "
        "you need to collect, why checking out is the hard part, and why contractors are a "
        "different problem. One diagram per post, a cost breakdown, and an engineering reference "
        "at the end."),
 ],
},
{
 "slug": "what-the-log-is-actually-for",
 "title": "What the log is actually for",
 "nav": "What it is for",
 "read": 5, "words": 740,
 "desc": ("The roll call at the assembly point, what it has to survive, and how uncertainty is "
          "shown."),
 "og": ("The roll call has to work with no power, no wifi, in the rain, read by somebody who is "
        "not the person who normally does it."),
 "abstract": ("What the roll call has to do, the conditions it operates under, how it is ordered, "
              "and why showing doubt is better than showing a clean list."),
 "lede": ("Designing backwards from the evacuation produces a different system from designing "
          "forwards from the reception desk, and almost every requirement worth having comes from "
          "that direction."),
 "tags": ["fire safety", "roll call", "visitor management", "resilience", "facilities",
          "serverless"],
 "takeaways": [
  "It must work with no network and no power in the building.",
  "Order by host, because hosts are the people who can confirm.",
  "Show the arrival time and the last confirmation, so age is visible.",
  "Mark uncertain entries rather than omitting or including them silently.",
  "Somebody other than the usual person will be reading it.",
 ],
 "blocks": [
  ("h2", "The conditions"),
  ("callout", "What the roll call has to survive", [
   "<strong>No mains power</strong> in the building, and possibly no wifi.",
   "<strong>Outside,</strong> in whatever the weather is doing, on a phone screen.",
   "<strong>Read by whoever is there,</strong> which may not be reception or the fire marshal.",
   "<strong>Under time pressure,</strong> with a fire service asking whether the building is "
   "clear.",
   "<strong>Possibly on more than one device,</strong> at more than one assembly point.",
   "<strong>Everything else about the system</strong> can fail gracefully. This cannot.",
  ]),
  ("p", "That list rules out a design where the roll call is a web page served from somewhere. It "
        "has to be cached on the devices that might need it, refreshed continuously while the "
        "network exists, and readable from that cache when it does not."),
  ("p", "It also rules out anything requiring a login at the point of use. Somebody standing in a "
        "car park does not have time to fail a password twice, and the roll call contains names "
        "and arrival times rather than anything sensitive."),
  ("h2", "How it is ordered"),
  ("fig", ("chain", {
    "entry": {"title": "The alarm goes", "sub": ["open the roll call"], "icon": "alarm"},
    "steps": [
      {"title": "Who is inside", "sub": ["checked in, not out"], "icon": "counter"},
      {"title": "Grouped by host", "sub": ["not alphabetically"], "icon": "person",
       "side": {"title": "Why", "sub": ["the host can confirm"], "icon": "check"}},
      {"title": "Certain first", "sub": ["arrived recently"], "icon": "clock"},
      {"title": "Then uncertain", "sub": ["here a long time,", "no confirmation"], "icon": "question"},
      {"title": "Tap to confirm", "sub": ["'this person is out'"], "icon": "form"}],
    "note": "Grouping by host turns one long list into several short ones somebody can answer."}),
   "How the roll call is presented. Grouping by host is the single most useful choice because it "
   "matches how the confirmation actually happens.",
   "How the fire roll call is ordered and confirmed",
   "A vertical chain of five steps entered by a box labelled The alarm goes, open the roll call. "
   "Step one lists who is inside, checked in and not out. Step two groups by host rather than "
   "alphabetically, with a side box explaining that the host can confirm. Step three shows "
   "certain entries first, those who arrived recently. Step four shows uncertain entries, people "
   "here a long time with no confirmation. Step five allows a tap to confirm that a person is "
   "out. A note says grouping by host turns one long list into several short ones somebody can "
   "answer."),
  ("h3", "Grouping by host"),
  ("p", "At an assembly point the useful question is not \"is Sarah Chen here?\" asked of a crowd; "
        "it is \"you had two visitors this morning, are they both out?\" asked of the person who "
        "was with them."),
  ("p", "So the list is grouped by host, hosts are listed by name, and each host's visitors sit "
        "under them. Somebody walks the assembly point asking four people about eleven visitors, "
        "rather than shouting eleven names."),
  ("h3", "Showing uncertainty"),
  ("p", "A visitor who checked in at nine and has not been confirmed since is more likely to have "
        "left than one who checked in twenty minutes ago. Sorting by arrival time and marking "
        "anybody over a few hours as unconfirmed gives the reader information they can act on."),
  ("p", "The alternative &mdash; a clean list of names with no indication of confidence &mdash; "
        "is worse in both directions. It sends people looking for somebody who left at eleven, "
        "and it gives false comfort about the accuracy of the rest."),
  ("h2", "What the list looks like"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "On the list", "parts": [("recent", 6), ("old", 8)]},
      {"label": "Actually inside", "parts": [("recent", 6), ("old", 1)]}],
    "series": [("recent", "Arrived in the last 2 hours", "#7AA116"),
               ("old", "Arrived longer ago, unconfirmed", "#ED7100")],
    "unit": "",
    "note": "Seven of the eight older entries had left. That is a normal afternoon."}),
   "A roll call against reality on a typical afternoon. The recent arrivals are reliable; the "
   "older unconfirmed ones are mostly people who have gone.",
   "A visitor roll call compared with who is actually in the building",
   "A stacked bar chart with two bars. Two series: arrived in the last two hours in green, and "
   "arrived longer ago and unconfirmed in orange. On the list: six recent and eight older. "
   "Actually inside: six recent and one older. A note says seven of the eight older entries had "
   "left, and that is a normal afternoon."),
  ("p", "That chart is why the check-out problem gets its own post. The system is accurate for "
        "the people who arrived recently and unreliable for everybody else, and both facts should "
        "be visible on the screen rather than averaged into one list."),
  ("h3", "More than one assembly point"),
  ("p", "Larger buildings have several, and the confirmations need to reconcile: somebody marked "
        "as out at the north point should disappear from the list at the south point within "
        "seconds, and if the network is down, both lists have to merge sensibly afterwards."),
  ("p", "The pragmatic version is that each device holds its own confirmations, they sync when "
        "they can, and a person confirmed out anywhere is out. It is not perfect and it is "
        "considerably better than two separate paper lists."),
  ("p", "Next: how little to collect."),
 ],
},
{
 "slug": "how-little-you-need-to-collect",
 "title": "How little you need to collect",
 "nav": "How little to collect",
 "read": 5, "words": 720,
 "desc": ("The fields a visitor book asks for, which of them have a purpose, and what "
          "photographing everybody actually creates."),
 "og": ("Car registration, company, purpose of visit, signature, photograph. Almost none of it "
        "serves the roll call, and all of it is a record you now hold."),
 "abstract": ("Which visitor fields have a genuine purpose, why the paper book discloses more "
              "than intended, what a photograph creates, and how long to keep anything."),
 "lede": ("Visitor books ask for a lot and almost none of it is used for anything, which is a "
          "reasonable definition of data you should not be collecting."),
 "tags": ["data minimisation", "privacy", "visitor management", "GDPR", "reception", "serverless"],
 "takeaways": [
  "Name, host, arrival time. Everything else needs a stated reason.",
  "The paper book's worst feature is showing everybody the previous entries.",
  "A photograph of every visitor is a biometric dataset with no purpose attached.",
  "Thirty days is a generous retention period for a roll call record.",
  "Ask for a mobile number only if you will use it, and say what for.",
 ],
 "blocks": [
  ("h2", "Field by field"),
  ("table", ["Field", "Used for what?", "Verdict"], [
   ["Name", "The roll call", "Necessary"],
   ["Host", "The roll call, and letting them know", "Necessary"],
   ["Arrival time", "Confidence in the roll call", "Necessary"],
   ["Company", "Nothing, usually", "Only if you have a reason"],
   ["Car registration", "Parking, if you manage it", "Only where parking is managed"],
   ["Purpose of visit", "Nothing", "Drop it"],
   ["Signature", "A ritual", "Drop it"],
   ["Photograph", "Identifying a visitor to staff", "Rarely justified; see below"],
  ]),
  ("p", "The middle rows are the interesting ones because they are collected almost universally "
        "and used almost never. Purpose of visit in particular is a field that people fill in "
        "with a single word and which nobody has ever read."),
  ("p", "The test for any field is straightforward: name the situation in which somebody looks at "
        "it. If the answer takes more than a moment to construct, the field should not exist."),
  ("h2", "What the paper book discloses"),
  ("fig", ("strip", {
    "stages": [
      {"title": "You sign in", "sub": ["on a page"], "icon": "form"},
      {"title": "You see 14 names", "sub": ["above yours"], "icon": "search"},
      {"title": "And their hosts", "sub": ["and their companies"], "icon": "person"},
      {"title": "A competitor visited", "sub": ["on Tuesday"], "icon": "alarm"},
      {"title": "Nobody intended this", "sub": ["and it happens daily"], "icon": "question"}],
    "title": "THE VISITOR BOOK'S QUIET PROBLEM",
    "note": "A screen showing one entry at a time fixes this at no cost."}),
   "The disclosure inherent in a shared paper book. It is unintentional, routine, and fixed for "
   "free by any screen-based check-in.",
   "How a paper visitor book discloses previous visitors to every new one",
   "A horizontal row of five boxes. You sign in on a page. You see fourteen names above yours. "
   "And their hosts, and their companies. A competitor visited on Tuesday. Nobody intended this, "
   "and it happens daily. A note says a screen showing one entry at a time fixes this at no cost."),
  ("p", "This is worth being explicit about because it is often the first genuine benefit of "
        "replacing the book, ahead of anything to do with the roll call. Who is meeting whom is "
        "frequently commercially sensitive and a shared page publishes it to everybody who walks "
        "in."),
  ("h2", "Photographs"),
  ("fig", ("chain", {
    "entry": {"title": "\"Take a photo of visitors\"", "sub": ["a common request"], "icon": "image"},
    "steps": [
      {"title": "What is it for?", "sub": ["specifically"], "icon": "branch",
       "exit": {"title": "Do not take it", "sub": ["no purpose, no photo"], "icon": "stop",
                "label": "unclear"}},
      {"title": "Badge identification?", "sub": ["a real reason, sometimes"], "icon": "form"},
      {"title": "Then keep it how long?", "sub": ["the visit, or forever?"], "icon": "clock",
       "exit": {"title": "The visit only", "sub": ["deleted at check-out"], "icon": "check",
                "label": "the visit"}},
      {"title": "Is it biometric?", "sub": ["if matched, yes"], "icon": "alarm"},
      {"title": "Do not match faces", "sub": ["a different obligation entirely"], "icon": "lock"}],
    "note": "A photograph on a badge for four hours is not the same as a face database."}),
   "How to decide about photographing visitors. The distinction in the last two boxes is the one "
   "that matters legally and practically.",
   "How to decide whether to photograph visitors and what to do with it",
   "A vertical chain of five steps entered by a box labelled Take a photo of visitors, a common "
   "request. Step one asks what it is for, specifically; if unclear it exits to Do not take it, "
   "no purpose no photo. Step two considers badge identification, which is a real reason "
   "sometimes. Step three asks how long to keep it, the visit or forever; the visit only exits to "
   "deleted at check-out. Step four asks whether it is biometric, which it is if matched. Step "
   "five says do not match faces, which is a different obligation entirely. A note says a "
   "photograph on a badge for four hours is not the same as a face database."),
  ("h3", "The distinction that matters"),
  ("p", "A photograph printed on a temporary badge and deleted when the visitor leaves has a "
        "clear purpose and a short life. A stored photograph of every visitor, retained and "
        "searchable, is a different thing with different obligations, and facial matching is "
        "different again and involves special category data in most regimes."),
  ("p", "Most buildings that ask for visitor photographs want the first one and end up building "
        "the second by default, because deletion is the step that gets left out."),
  ("h2", "Retention"),
  ("p", "The roll call needs today. An incident investigation might need last week. Almost "
        "nothing needs last year, and a visitor log going back several years is a list of who met "
        "whom that somebody will eventually ask about."),
  ("p", "Thirty days is generous and defensible for most buildings, with automatic deletion "
        "rather than a policy somebody is supposed to enact. Where a longer period is genuinely "
        "required &mdash; some regulated environments &mdash; it should be a stated period with a "
        "stated reason, not an absence of deletion."),
  ("h3", "Mobile numbers"),
  ("p", "Useful if you are going to use them: an evacuation message, a check-out prompt, a "
        "notification that their host is on their way down. Not useful as a field that exists "
        "because the form template had one."),
  ("p", "If it is collected, the screen should say what it is for in six words. That both "
        "justifies it and reminds whoever configured the system that it needs a justification."),
  ("p", "Next: the part that does not work."),
 ],
},
{
 "slug": "why-checking-out-is-the-hard-part",
 "title": "Why checking out is the hard part",
 "nav": "Checking out",
 "read": 5, "words": 730,
 "desc": ("The asymmetry of motivation, four mechanisms that each catch some people, and the "
          "end-of-day sweep."),
 "og": ("People check in because they want to get in. Nobody has ever wanted to check out."),
 "abstract": ("Why check-out fails, the four mechanisms that between them catch most people, why "
              "no single one is enough, and how the end of day is handled."),
 "lede": ("Every visitor management system solves check-in, because the visitor is motivated. "
          "Check-out has no such force behind it and needs to be engineered around rather than "
          "requested."),
 "tags": ["visitor management", "check-out", "fire safety", "interfaces", "reception",
          "serverless"],
 "takeaways": [
  "Nobody is motivated to check out. Asking harder does not work.",
  "Use four mechanisms; each catches a different group.",
  "The host is the most reliable single source and needs one tap.",
  "An end-of-day sweep closes the rest, marked as assumed rather than confirmed.",
  "Never auto-close during the day. That is the hour the alarm goes.",
 ],
 "blocks": [
  ("h2", "The asymmetry"),
  ("p", "A visitor checks in because a door is closed and a person is waiting to be told they "
        "have arrived. The incentive is immediate and personal. On the way out the door opens "
        "from the inside, the meeting is over, and the visitor is thinking about the train."),
  ("p", "No amount of signage changes that, and a system whose check-out relies on the visitor "
        "remembering is a system with an inaccurate roll call by mid-morning. So the design uses "
        "several mechanisms and expects each of them to work partially."),
  ("h2", "Four mechanisms"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Visitor taps out", "sub": ["a screen by the door"], "icon": "form",
       "label": "catches ~30%"},
      {"title": "Host checks them out", "sub": ["one tap from a message"], "icon": "person",
       "label": "catches ~45%"},
      {"title": "Badge returned", "sub": ["to a box or a reader"], "icon": "shield",
       "label": "catches ~15%"}],
    "target": {"title": "The rest", "sub": ["unconfirmed"], "icon": "question",
               "then": {"title": "End-of-day sweep", "sub": ["marked assumed, not confirmed"],
                        "icon": "clock"}},
    "note": "No single mechanism is close to sufficient. Together they get most of the way."}),
   "The four check-out paths and roughly what each catches. The design assumption is that all of "
   "them are partial.",
   "Four mechanisms for checking visitors out and their approximate coverage",
   "Three boxes stacked on the left. Visitor taps out at a screen by the door, labelled catches "
   "about thirty per cent. Host checks them out with one tap from a message, labelled catches "
   "about forty-five per cent. Badge returned to a box or a reader, labelled catches about "
   "fifteen per cent. All three converge on The rest, unconfirmed, and that leads down to an "
   "End-of-day sweep, marked assumed rather than confirmed. A note says no single mechanism is "
   "close to sufficient and together they get most of the way."),
  ("h3", "The host is the best source"),
  ("p", "The host knows the meeting ended, is at a desk, and has a phone. A message at a sensible "
        "interval &mdash; \"has Sarah Chen left?\" with two buttons &mdash; is answered a good "
        "proportion of the time, and it is the single highest-yield mechanism."),
  ("p", "The timing matters. Sending it as the meeting was scheduled to end is better than "
        "sending it two hours later, and asking once is better than asking three times. A host "
        "who is nagged stops answering."),
  ("h3", "The badge"),
  ("p", "A physical badge returned to a box is a genuine signal and it is worth capturing even "
        "crudely: a member of reception clearing the box twice a day and tapping the names is "
        "enough, and a reader is better if one exists."),
  ("p", "It is also the mechanism that produces the useful secondary metric: badges that never "
        "come back. A steady rate of unreturned badges is a small cost and a reminder that the "
        "roll call for those people was closed by assumption."),
  ("h2", "The end-of-day sweep"),
  ("fig", ("chain", {
    "entry": {"title": "End of the working day", "sub": ["a stated hour"], "icon": "clock"},
    "steps": [
      {"title": "Still checked in?", "sub": ["after all mechanisms"], "icon": "counter"},
      {"title": "Ask the host once", "sub": ["a final message"], "icon": "email",
       "exit": {"title": "Confirmed out", "sub": ["with a time"], "icon": "check",
                "label": "reply"}},
      {"title": "Any known to be here?", "sub": ["evening event, late meeting"], "icon": "branch",
       "exit": {"title": "Leave them on", "sub": ["genuinely present"], "icon": "person",
                "label": "yes"}},
      {"title": "Close as assumed", "sub": ["never as confirmed"], "icon": "filter"},
      {"title": "Count them", "sub": ["the accuracy metric"], "icon": "chart"}],
    "note": "The distinction in the fourth box is what keeps tomorrow's roll call honest."}),
   "How the day is closed out. Marking the swept records as assumed rather than confirmed is what "
   "makes the accuracy measurable.",
   "How remaining checked-in visitors are closed at the end of the day",
   "A vertical chain of five steps entered by a box labelled End of the working day, at a stated "
   "hour. Step one lists who is still checked in after all mechanisms. Step two asks the host "
   "once with a final message; a reply exits to Confirmed out, with a time. Step three asks "
   "whether any are known to be here for an evening event or late meeting; if so it exits to "
   "Leave them on, genuinely present. Step four closes the rest as assumed, never as confirmed. "
   "Step five counts them as the accuracy metric. A note says the distinction in the fourth box "
   "is what keeps tomorrow's roll call honest."),
  ("h3", "Never sweep during the day"),
  ("p", "The obvious optimisation is to auto-close visitors after three or four hours, and it is "
        "dangerous for exactly one reason: the alarm goes during the working day, and somebody "
        "auto-closed at two o'clock who is still in a meeting at half past two is invisible on "
        "the roll call."),
  ("p", "Marking them as unconfirmed on the roll call achieves the same reduction in noise "
        "without removing them, which is the correct trade for a safety list."),
  ("h2", "Measuring the accuracy"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Jan", "parts": [("conf", 61), ("assumed", 39)]},
      {"label": "Apr", "parts": [("conf", 74), ("assumed", 26)]},
      {"label": "Jul", "parts": [("conf", 81), ("assumed", 19)]}],
    "series": [("conf", "Confirmed check-outs, %", "#7AA116"),
               ("assumed", "Closed by the sweep, %", "#ED7100")],
    "unit": "",
    "note": "The green share is the only meaningful measure of whether the roll call works."}),
   "Confirmed against assumed check-outs over three quarters. Improving the green share is the "
   "whole goal, and it is only visible because the two are recorded differently.",
   "Confirmed versus swept visitor check-outs over three quarters",
   "A stacked bar chart with three bars in per cent. Two series: confirmed check-outs in green, "
   "and closed by the sweep in orange. January: sixty-one per cent confirmed and thirty-nine "
   "swept. April: seventy-four confirmed and twenty-six swept. July: eighty-one confirmed and "
   "nineteen swept. A note says the green share is the only meaningful measure of whether the "
   "roll call works."),
  ("p", "Improvements come from small things: moving the check-out screen to where people "
        "actually leave, changing when the host message is sent, putting the badge box somewhere "
        "on the way out rather than behind reception."),
  ("p", "None of them are clever and all of them are measurable, which is the point of "
        "distinguishing confirmed from assumed in the first place."),
  ("p", "Next: the people who are not visitors."),
 ],
},
{
 "slug": "contractors-are-a-different-problem",
 "title": "Contractors are a different problem",
 "nav": "Contractors",
 "read": 5, "words": 710,
 "desc": ("The people who come every day, what a site induction adds, and the deliveries that are "
          "not visits at all."),
 "og": ("A contractor who is here every day for six weeks should not be typing their name into a "
        "screen every morning, and they should still be on the roll call."),
 "abstract": ("Why contractors need a different flow, what a site induction record adds, how "
              "deliveries are handled, and the permit-to-work connection."),
 "lede": ("A visitor flow designed for somebody arriving once for a meeting is wrong for somebody "
          "who is here every day for two months, and the difference matters for the roll call as "
          "much as for the convenience."),
 "tags": ["contractors", "visitor management", "site induction", "deliveries", "facilities",
          "serverless"],
 "takeaways": [
  "Contractors need a fast repeat check-in, not the full visitor flow.",
  "Site induction is a record with an expiry, and it is worth holding.",
  "Deliveries are usually not visits and should not clutter the roll call.",
  "Out-of-hours work needs its own handling; the sweep would close it.",
  "Where permits to work exist, the check-in is the natural place to check them.",
 ],
 "blocks": [
  ("h2", "The repeat visitor"),
  ("fig", ("chain", {
    "entry": {"title": "Somebody arrives", "sub": ["at the screen"], "icon": "person"},
    "steps": [
      {"title": "Been here before?", "sub": ["by a code or a card"], "icon": "branch",
       "exit": {"title": "Full check-in", "sub": ["name and host"], "icon": "form",
                "label": "no"}},
      {"title": "Induction current?", "sub": ["if the site requires one"], "icon": "branch",
       "exit": {"title": "Redo it", "sub": ["before entry"], "icon": "alarm", "label": "no"}},
      {"title": "One tap", "sub": ["confirm and go"], "icon": "check"},
      {"title": "On the roll call", "sub": ["same as anybody"], "icon": "shield"},
      {"title": "Same check-out problem", "sub": ["and worse"], "icon": "clock",
       "side": {"title": "Why worse", "sub": ["no host expecting them"], "icon": "question"}}],
    "note": "The convenience is the point: a slow repeat check-in is one that gets skipped."}),
   "The contractor flow. Making the repeat case fast is what stops people walking past the screen "
   "entirely, which is the real risk.",
   "How a returning contractor checks in with fewer steps",
   "A vertical chain of five steps entered by a box labelled Somebody arrives at the screen. Step "
   "one asks whether they have been here before, identified by a code or a card; if not it exits "
   "to Full check-in with name and host. Step two asks whether their induction is current, if the "
   "site requires one; if not it exits to Redo it before entry. Step three takes one tap to "
   "confirm and go. Step four puts them on the roll call, the same as anybody. Step five notes "
   "the same check-out problem, and worse, with a side box explaining that there is no host "
   "expecting them. A note says the convenience is the point, because a slow repeat check-in is "
   "one that gets skipped."),
  ("h3", "Worse check-out"),
  ("p", "A contractor has no host waiting for a notification, which removes the most effective "
        "check-out mechanism from Part 4. They also frequently leave and return several times a "
        "day, which produces either a great deal of tapping or an inaccurate log."),
  ("p", "The pragmatic answer is a daily rather than per-entry model for on-site contractors: "
        "they check in for the day, and the person managing the works confirms at the end of the "
        "day who has left. That is less precise and considerably more accurate in practice."),
  ("h2", "Site induction"),
  ("callout", "What the induction record holds", [
   "<strong>Who</strong> was inducted, and by whom.",
   "<strong>When,</strong> and what version of the site rules it covered.",
   "<strong>An expiry,</strong> typically annual, after which it is not current.",
   "<strong>Any site-specific competencies</strong> that were checked.",
   "<strong>Not a copy of their qualifications</strong> unless there is a specific reason. "
   "Recording that they were seen is usually enough.",
   "<strong>The check-in is where it is enforced,</strong> because that is the only moment "
   "everybody passes through.",
  ]),
  ("p", "The fifth point is a data minimisation one that gets missed. Holding scans of every "
        "contractor's certificates creates a store of other people's personal documents with no "
        "clear owner. Recording that they were checked, by whom and when, achieves the same "
        "assurance with much less exposure."),
  ("h2", "Deliveries"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A driver arrives", "sub": ["two minutes at the door"], "icon": "truck"},
      {"title": "Not really a visit", "sub": ["never enters properly"], "icon": "question"},
      {"title": "On the roll call?", "sub": ["they would still be there"], "icon": "branch"},
      {"title": "A separate log", "sub": ["deliveries, not visitors"], "icon": "form"},
      {"title": "Roll call stays clean", "sub": ["and short"], "icon": "shield"}],
    "title": "DELIVERIES ARE NOT VISITS",
    "note": "Fifteen delivery entries a day would double the roll call and none of them are inside."}),
   "Why deliveries are logged separately. Including them makes the roll call longer and less "
   "accurate at the same time.",
   "Why deliveries are recorded separately from visitors",
   "A horizontal row of five boxes. A driver arrives: two minutes at the door. Not really a "
   "visit: they never enter properly. On the roll call? They would still be there. A separate "
   "log: deliveries, not visitors. Roll call stays clean, and short. A note says fifteen delivery "
   "entries a day would double the roll call and none of them are inside."),
  ("p", "A driver who comes into a goods area for two minutes is not somebody the fire marshal "
        "needs to account for, and the check-out mechanisms will never catch them. Logging "
        "deliveries separately &mdash; if at all &mdash; keeps the list that matters short."),
  ("p", "Where a driver genuinely enters the building for longer &mdash; an installation, a "
        "long unload &mdash; that is a visit and should be treated as one. The distinction is "
        "about time inside rather than about job title."),
  ("h3", "Out of hours"),
  ("p", "Somebody working on a Sunday, or overnight, would be closed by an end-of-day sweep "
        "designed for a nine-to-five building, which is exactly the situation where an accurate "
        "roll call matters most because there is nobody else around."),
  ("p", "Out-of-hours entries need a different sweep time and, ideally, a check-in that records "
        "an expected finish. It is a small amount of configuration and it covers the case where "
        "the consequence of getting it wrong is highest."),
  ("h3", "Permits to work"),
  ("p", "Where a site operates permits to work &mdash; hot work, confined spaces, electrical "
        "isolation &mdash; the check-in is the natural place to confirm one exists and is "
        "current, because it is the one moment everybody passes through."),
  ("p", "The system should check and record rather than issue. Permit issue is a safety process "
        "with a competent person at the centre of it, and this is a logger."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="visit",
 volumes=[(400, "400 visits"), (1500, "1,500 visits"), (6000, "6,000 visits")],
 read_each=0.0,
 msgs_each=1.6,
 lede=("There is no model in this system and the messaging is the workload: a host notification "
       "on arrival and a check-out prompt for most visits. Fifteen hundred visits a month is a "
       "busy office building. Here is where each cent goes."),
 takeaway_extra=("Notifications drive the bill; the records themselves are a few kilobytes each "
                 "and are deleted after thirty days."),
 risks=[
  "<strong>Repeated check-out prompts.</strong> Asking a host three times gets fewer answers than "
  "asking once, and costs three times as much.",
  "<strong>Storing photographs indefinitely.</strong> If photographs are taken at all, delete them "
  "at check-out. The retention is the whole difference in obligation.",
  "<strong>Never deleting visitor records.</strong> Not a meaningful storage cost, and a "
  "multi-year record of who met whom is a liability rather than an asset.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. Messaging is above one per "
                "visit because most visits produce both an arrival notification and a check-out "
                "prompt."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="vl",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the offline roll call, and the retention rule."),
 outside=[
  {"title": "The check-in screen", "sub": ["and a door screen"], "icon": "form"},
  {"title": "Hosts", "sub": ["notified, and asked"], "icon": "email"},
  {"title": "Roll call devices", "sub": ["cached, offline capable"], "icon": "shield"}],
 inside=[
  {"title": "API + EventBridge", "sub": ["check in and out,", "sweep and prompts"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["checkin, checkout, sweep"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["visits, people"], "icon": "database"}],
 note="us-east-1. One account. Visit records expire at 30 days by TTL; no sweep runs during the day.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The check-in screen and a door screen. "
  "Hosts, who are notified and asked. And Roll call devices, cached and offline capable. Inside "
  "the account, three groups. An API for check in and out alongside EventBridge running the sweep "
  "and prompts. Three Lambda functions named checkin, checkout and sweep. And two DynamoDB tables "
  "named visits and people. A note gives the region as us-east-1, one account, and states that "
  "visit records expire at thirty days by TTL and no sweep runs during the day."),
 functions=[
  ["<code>vl-checkin</code>", "API, from the screen",
   "Creates the visit, notifies the host, checks induction currency for known contractors",
   "10s / 512&nbsp;MB"],
  ["<code>vl-checkout</code>", "API, from any of the four mechanisms",
   "Closes the visit as confirmed, recording which mechanism did it", "10s / 512&nbsp;MB"],
  ["<code>vl-sweep</code>", "EventBridge, at the site's stated end of day",
   "Sends a final host prompt, then closes the rest as assumed; never runs mid-day",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>vl-checkin-role</code>",
   "<code>dynamodb:PutItem</code>, <code>dynamodb:GetItem</code>, <code>ses:SendEmail</code>",
   "Visits; read-only on people; one verified identity"],
  ["<code>vl-checkout-role</code>", "<code>dynamodb:UpdateItem</code>", "Visits only"],
  ["<code>vl-sweep-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Visits; one verified identity"]],
 tables=[
  ("Table: visits",
   "PK   site_id           S\n"
   "SK   checked_in_at#id  S   sorts the roll call by arrival naturally\n"
   "     name              S\n"
   "     host_id           S   the roll call groups on this\n"
   "     kind              S   visitor | contractor | delivery\n"
   "     checked_out_at    S\n"
   "     checkout_by       S   visitor | host | badge | sweep\n"
   "     confirmed         BOOL false when closed by the sweep\n"
   "     mobile            S   only if the site uses it, and says what for\n"
   "     ttl               N   epoch, +30 days\n\n"
   "`checkout_by` is what makes the confirmed-versus-assumed chart in\n"
   "Part 4 possible, and that chart is the only measure of accuracy."),
  ("Table: people",
   "PK   person_key        S   a code on a contractor card\n"
   "     display_name      S\n"
   "     kind              S   contractor | regular_visitor\n"
   "     inducted_at       S\n"
   "     induction_expires S   checked at every check-in\n"
   "     inducted_by       S   a person, recorded\n"
   "     rules_version     S   which site rules the induction covered\n\n"
   "Deliberately holds no certificate scans. Recording that competencies\n"
   "were checked, by whom and when, is the assurance; the documents are\n"
   "somebody else's personal data.")],
 inbound=[
  "<strong>Check-in is name and host and nothing else</strong> unless the site has stated a reason "
  "for another field.",
  "<strong>The roll call is pushed to devices and cached</strong>, refreshed while a network "
  "exists and readable when it does not. It requires no login at the point of use.",
  "<strong>Four check-out paths write the same record</strong> with different "
  "<code>checkout_by</code> values, so coverage per mechanism is measurable.",
  "<strong>The sweep time is per site</strong>, with a separate out-of-hours configuration, "
  "because a nine-to-five sweep would close a Sunday shift."],
 model_notes=[
  "<strong>There is no model in this system.</strong> It is a list with timestamps.",
  "<strong>The tempting use</strong> is predicting when a visitor has probably left. That is "
  "exactly what the assumed sweep does, and dressing it up as a prediction would let it run "
  "mid-day.",
  "<strong>The wrong use</strong> is facial recognition. It converts a visitor log into a "
  "biometric system with a different set of obligations and no additional safety benefit.",
  "<strong>A defensible use</strong> is matching a typed name against known contractors, so a "
  "regular does not create a new person record every visit.",
  "<strong>The cost page assumes none</strong>, which is why messaging is the whole variable."],
 gotchas=[
  "Never run the sweep during the working day. Auto-closing somebody at two o'clock removes them "
  "from the roll call at exactly the hour the alarm might go.",
  "Record which mechanism closed each visit. Without it, confirmed and assumed are "
  "indistinguishable and the roll call's accuracy cannot be measured or improved.",
  "Group the roll call by host, not alphabetically. It matches how confirmation actually happens "
  "at an assembly point.",
  "Cache the roll call on the devices. A web page is not available in a car park with the power "
  "off.",
  "Set a TTL on visit records from the first day. A multi-year log of who met whom is a liability "
  "nobody chose to create."],
))
