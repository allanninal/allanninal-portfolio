"""Day 114 -- 2026-08-16 -- Packing slip checker."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "packing-slip-checker"
NAME = "Packing slip checker"

SPEC = {
 "slug": SLUG, "date": "2026-08-16", "name": NAME,
 "tagline": ("Compares what was ordered, what the delivery note claims, and what is actually in "
             "the boxes -- and makes recording the difference possible for somebody standing in "
             "a doorway holding a phone."),
 "lede": ("A small system that checks three documents that should agree and usually do not: the "
          "purchase order, the packing slip, and the physical count. The engineering is "
          "straightforward; the design problem is that the only moment a discrepancy can be "
          "recorded is the moment nobody has time. Seven posts on the same system, one diagram at "
          "a time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["goods receipt", "three-way match", "packing slip", "warehouse", "procurement",
              "serverless"],
 "icons": ["truck", "check", "doc"],
 "faq": [
  ("What is a packing slip checker?",
   "A small serverless system that compares a purchase order, the supplier's packing slip and the "
   "physical count at receipt, and records any discrepancy at the moment it can still be proved."),
  ("Why not just check the packing slip against the order?",
   "Because the packing slip is a claim about what was sent. It agreeing with the order tells you "
   "nothing about what is in the boxes, which is the only thing that matters."),
  ("What happens when something is short?",
   "It is recorded with evidence at receipt, the delivery note is annotated before signing, and "
   "the supplier is told the same day. The post on this covers why the order matters."),
  ("Does it automatically raise claims or reject deliveries?",
   "No. It records what was found and tells the right people. A rejection is a commercial "
   "decision and a claim is an assertion of fact."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "packing-slip-checker-on-aws",
 "title": "A packing slip checker on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Compares order, packing slip and physical count at the door, and records discrepancies "
          "while they can still be proved. AWS, about $2 a month."),
 "og": ("The packing slip is a claim about what was sent. Checking it against the order is not a "
        "check, it is two documents agreeing with each other."),
 "abstract": ("The whole system on one page -- three documents, one comparison, one moment "
              "&mdash; and why the receiving doorway is the hardest interface in the design."),
 "lede": ("A pallet arrives. The driver wants a signature. The delivery note says twelve boxes "
          "and there are twelve boxes, so somebody signs, and eleven days later it turns out one "
          "of the boxes contained forty units instead of sixty. At that point the supplier's "
          "position is that a signed delivery note says it was all there. This post walks through "
          "a small system built entirely around that ninety seconds at the door."),
 "tags": ["goods receipt", "three-way match", "packing slip", "warehouse", "procurement",
          "serverless"],
 "takeaways": [
  "Three documents, not two: the order, the slip, and what is physically there.",
  "The only moment a discrepancy can be proved is before the delivery note is signed.",
  "The receiving interface has about ninety seconds and one hand available.",
  "Nothing is auto-rejected and no claim is auto-filed.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "The purchase order", "sub": ["what we asked for"], "icon": "form"},
      {"title": "The packing slip", "sub": ["what they claim", "they sent"], "icon": "doc"},
      {"title": "The person receiving", "sub": ["holding a phone,", "and a pen"], "icon": "person"}],
    "inside": [
      {"title": "Matcher", "sub": ["order against slip,", "before arrival"], "icon": "check"},
      {"title": "Receiving view", "sub": ["what to count,", "and nothing else"], "icon": "search"},
      {"title": "Recorder", "sub": ["discrepancy,", "evidence, timestamp"], "icon": "database"}],
    "edges": [{"from": 0, "to": 0, "label": "expected lines"},
              {"from": 1, "to": 1, "label": "claimed lines"},
              {"from": 2, "to": 2, "label": "a short list to check", "up": True}],
    "note": "The middle box is the whole product. Everything else exists to make it short."}),
   "Three things outside the account, three pieces inside it. The receiving view is where this "
   "system succeeds or fails, and its only job is to be short.",
   "System: order, packing slip and physical count compared at receipt",
   "Three boxes across the top sit outside the AWS account. On the left, The purchase order: what "
   "we asked for. In the middle, The packing slip: what they claim they sent. On the right, The "
   "person receiving, holding a phone and a pen. Each connects by an arrow to the AWS account "
   "container below. Expected lines flow down into the account. Claimed lines feed in. A short "
   "list to check goes back out. Inside the AWS account are three components in a row. On the "
   "left, the Matcher, comparing order against slip before arrival. In the middle, the Receiving "
   "view, showing what to count and nothing else. On the right, the Recorder, capturing the "
   "discrepancy, the evidence and the timestamp. A note at the bottom says the middle box is the "
   "whole product, and everything else exists to make it short."),
  ("h3", "Two documents agreeing is not a check"),
  ("p", "The standard implementation compares the packing slip to the purchase order and reports "
        "a match. It is easy, it produces a green tick, and it verifies nothing: both documents "
        "were produced by people looking at the same order, and neither of them has been inside "
        "the boxes."),
  ("p", "The check that matters is the physical count, and it is expensive in the only currency "
        "the receiving bay has, which is attention. So the entire job of the first two components "
        "is to work out the shortest possible list of things a person actually needs to open and "
        "count, and then get out of the way."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The matcher.</strong> Compares the order and the slip in advance and works out what "
   "needs physically checking. Part 2.",
   "<strong>The receiving view.</strong> The ninety-second interface: a short list, a way to say "
   "\"not what it says\", and a camera. Part 3.",
   "<strong>The recorder.</strong> Captures the discrepancy with evidence and a timestamp before "
   "anybody signs. Parts 4 and 5.",
  ]),
  ("h2", "One delivery, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Slip received", "sub": ["ahead of the van"], "icon": "doc"},
      {"title": "Matched", "sub": ["2 lines differ"], "icon": "check"},
      {"title": "Check list", "sub": ["open 3 of 12 boxes"], "icon": "search"},
      {"title": "Counted", "sub": ["one short by 20"], "icon": "counter"},
      {"title": "Annotated, then signed", "sub": ["in that order"], "icon": "person"}],
    "title": "ONE DELIVERY, END TO END",
    "note": "The last box's order is the difference between a claim and a disagreement."}),
   "The same system as one line. Three boxes opened instead of twelve, and the signature happens "
   "after the annotation rather than before it.",
   "One delivery from packing slip to an annotated signature",
   "A horizontal row of five boxes joined by arrows. Slip received: ahead of the van. Matched: "
   "two lines differ. Check list: open three of twelve boxes. Counted: one short by twenty. "
   "Annotated, then signed: in that order. A note says the last box's order is the difference "
   "between a claim and a disagreement."),
  ("h2", "In plain words"),
  ("p", "The supplier emails a packing slip the day before. The matcher reads it and compares it "
        "with the purchase order: ten of the twelve lines match exactly, one is short by twenty "
        "units according to the slip itself, and one is a substituted product code."),
  ("p", "When the pallet arrives, the person receiving does not see twelve lines. They see three: "
        "check the box with the short line, check the box with the substitution, and spot-check "
        "one line at random. Everything else is accepted on the slip, which is a deliberate and "
        "stated risk rather than an oversight."),
  ("p", "The short line turns out to be short by forty rather than twenty. They tap the line, "
        "enter forty, photograph the open box and the label, and the system produces the wording "
        "to write on the delivery note. Then they sign, with that annotation on it, and the "
        "driver takes their copy of the same words."),
  ("callout", "Design rules that shaped every decision", [
   "Never present twelve lines to somebody with ninety seconds. Present the ones that matter.",
   "Annotate the delivery note before signing. Afterwards is a different legal position.",
   "A photograph with the label in frame is worth more than any number of typed notes.",
   "Nothing is auto-rejected. Refusing a delivery is a commercial decision.",
   "Record what was seen, not what it means. Interpretation comes later, from a person.",
   "Accepting a line on the slip is a stated decision, recorded as one.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Goods receipt errors are usually blamed on carelessness in the warehouse, and the "
        "diagnosis is almost always wrong. The person receiving is doing an unpaid documentary "
        "task, under time pressure, with a driver waiting, using a system designed by somebody "
        "sitting down."),
  ("p", "So the design treats the ninety seconds as the binding constraint and spends everything "
        "it has &mdash; pre-matching, prioritisation, one-handed interaction, photographs instead "
        "of typing &mdash; on making that window productive. The rest is bookkeeping."),
  ("p", "The next four posts walk through each piece: how the three documents get compared, how a "
        "discrepancy is recorded at the door, what happens to over- and under-shipments, and how "
        "individual discrepancies become a pattern worth acting on. One diagram per post, a cost "
        "breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-the-three-documents-get-compared",
 "title": "How the three documents get compared",
 "nav": "How they are compared",
 "read": 5, "words": 740,
 "desc": ("The pre-arrival match, choosing what needs physical checking, and the risk that is "
          "accepted deliberately rather than by accident."),
 "og": ("You cannot count everything. Choosing what to count, and recording that choice, is "
        "different from not counting."),
 "abstract": ("How the order and slip are matched before the delivery arrives, how the physical "
              "check list is chosen, and why accepting the rest on trust has to be an explicit "
              "decision."),
 "lede": ("The comparison happens twice: once on paper, the day before, and once in the doorway. "
          "The first one is easy and its entire purpose is to make the second one short."),
 "tags": ["three-way match", "goods receipt", "sampling", "risk", "procurement", "serverless"],
 "takeaways": [
  "Match the order and slip on arrival of the slip, not of the goods.",
  "Every slip-versus-order difference goes on the check list automatically.",
  "Add a rotating spot-check so trusted lines are not permanently unverified.",
  "High-value and historically-problematic lines are always checked.",
  "Lines accepted without counting are recorded as accepted, not as verified.",
 ],
 "blocks": [
  ("h2", "The paper match, in advance"),
  ("fig", ("chain", {
    "entry": {"title": "A packing slip arrives", "sub": ["usually by email"], "icon": "doc"},
    "steps": [
      {"title": "Find the order", "sub": ["by PO number or lines"], "icon": "search",
       "exit": {"title": "No order found", "sub": ["a person looks, now"], "icon": "alarm",
                "label": "fail"}},
      {"title": "Line by line", "sub": ["code, quantity, unit"], "icon": "check"},
      {"title": "Any difference?", "sub": ["short, extra, substituted"], "icon": "branch",
       "exit": {"title": "On the check list", "sub": ["always"], "icon": "form", "label": "yes"}},
      {"title": "High value or history?", "sub": ["per line"], "icon": "branch",
       "exit": {"title": "On the check list", "sub": ["always"], "icon": "form", "label": "yes"}},
      {"title": "Add one spot-check", "sub": ["rotating, at random"], "icon": "filter"}],
    "note": "Three reasons a line gets counted. Everything else is accepted, and recorded as such."}),
   "How the physical check list is built. The last box is what stops the well-behaved lines from "
   "becoming permanently unexamined.",
   "How the physical check list is chosen before a delivery arrives",
   "A vertical chain of five steps entered by a box labelled A packing slip arrives, usually by "
   "email. Step one finds the order by purchase order number or by lines; a failure exits to No "
   "order found, and a person looks at it now. Step two compares line by line on code, quantity "
   "and unit. Step three asks whether there is any difference, whether short, extra or "
   "substituted; if so it exits to On the check list, always. Step four asks whether the line is "
   "high value or has a history of problems; if so it also exits to On the check list. Step five "
   "adds one rotating spot-check at random. A note says there are three reasons a line gets "
   "counted, and everything else is accepted and recorded as such."),
  ("h3", "Why the slip has to arrive first"),
  ("p", "If the packing slip only appears on the pallet, all of this has to happen in the "
        "doorway, and it will not. Getting suppliers to email the slip when they despatch is a "
        "small ask that most will agree to, and it converts a ninety-second problem into a "
        "next-day one."),
  ("p", "Where a supplier will not or cannot, the fallback is photographing the slip on arrival "
        "and running the match while the driver waits, which works and is worse. It is worth "
        "spending a phone call per supplier to avoid."),
  ("h3", "The spot-check is not optional"),
  ("p", "Without it, a supplier whose slips always match the order is never physically counted "
        "again, which is exactly the situation in which a quiet shortage would go unnoticed for a "
        "year. One rotating line per delivery costs almost nothing and means every line gets "
        "counted a few times a year."),
  ("p", "It should genuinely rotate rather than being random each time, so that coverage is "
        "guaranteed rather than probable. A line that has not been physically counted in six "
        "months goes to the top of the rotation."),
  ("h2", "Accepted is not verified"),
  ("fig", ("strip", {
    "stages": [
      {"title": "12 lines on the slip", "sub": ["all plausible"], "icon": "doc"},
      {"title": "3 counted", "sub": ["verified"], "icon": "check"},
      {"title": "9 not counted", "sub": ["accepted"], "icon": "form"},
      {"title": "Both recorded", "sub": ["as what they are"], "icon": "database"},
      {"title": "Later dispute", "sub": ["we know which was which"], "icon": "search"}],
    "title": "TWO DIFFERENT WORDS",
    "note": "A system that records everything as 'received' cannot answer the only useful question."}),
   "Why the distinction is stored. Six weeks later, whether a line was counted or accepted is the "
   "first question anybody asks, and most systems cannot answer it.",
   "Why counted and accepted lines are recorded differently",
   "A horizontal row of five boxes. Twelve lines on the slip, all plausible. Three counted: "
   "verified. Nine not counted: accepted. Both recorded as what they are. Later dispute: we know "
   "which was which. A note says a system that records everything as received cannot answer the "
   "only useful question."),
  ("p", "This is a small data modelling decision with a large downstream effect. When a shortage "
        "surfaces in a stock count two months later, the immediate question is whether that line "
        "was ever physically counted at receipt, and \"received: yes\" does not answer it."),
  ("p", "It also makes the accepted risk visible in aggregate. A supplier where ninety per cent "
        "of lines are accepted on the slip is a supplier you are trusting a great deal, which may "
        "be entirely reasonable and should at least be a known fact."),
  ("h3", "Substitutions"),
  ("p", "A substituted product code is always on the check list, because a substitution is a "
        "decision somebody at the supplier made on your behalf and it may or may not be "
        "acceptable. The check is not just quantity; it is whether the thing that arrived is "
        "usable for what it was ordered for."),
  ("p", "That question cannot be answered by the system and should not be attempted. The line "
        "goes on the list flagged as a substitution, the person looks at it, and the answer is "
        "recorded as their judgement."),
  ("p", "Next: the ninety seconds."),
 ],
},
{
 "slug": "how-a-discrepancy-gets-recorded-at-the-door",
 "title": "How a discrepancy gets recorded at the door",
 "nav": "How it is recorded",
 "read": 6, "words": 770,
 "desc": ("The ninety-second interface, why photographs beat typing, and the annotation that has "
          "to happen before the signature."),
 "og": ("Signing first and reporting later is the most common receiving mistake, and it "
        "surrenders the position before anybody knows there is one."),
 "abstract": ("The constraints of the receiving doorway, what the interface must and must not "
              "ask for, why the delivery note is annotated before signing, and what the driver "
              "gets."),
 "lede": ("Everything else in this system is preparation for an interaction that lasts about a "
          "minute and a half, happens standing up, and competes with a driver who has eleven more "
          "drops. Designing for that is a different discipline from designing for a desk."),
 "tags": ["goods receipt", "mobile interfaces", "evidence", "warehouse", "documentation",
          "serverless"],
 "takeaways": [
  "One hand, gloves on, poor signal, and a driver waiting. Those are the constraints.",
  "Photographs, not typing. A picture with the label in frame is the strongest evidence.",
  "Annotate the delivery note before signing, and give the driver the same words.",
  "The system generates the annotation wording so nobody has to compose it.",
  "It works offline and syncs later, because the loading bay has no signal.",
 ],
 "blocks": [
  ("h2", "The constraints"),
  ("callout", "What the receiving doorway is actually like", [
   "<strong>About ninety seconds</strong> before the driver starts asking.",
   "<strong>One hand free.</strong> The other is holding a clipboard, a box, or a door.",
   "<strong>Gloves, cold, and often rain.</strong> Small touch targets do not work.",
   "<strong>Little or no mobile signal.</strong> Loading bays are the worst coverage in any "
   "building.",
   "<strong>The person is not a data entry clerk.</strong> They are doing this between two other "
   "jobs.",
   "<strong>Any friction</strong> results in everything being marked as received correctly, which "
   "is the failure this system exists to prevent.",
  ]),
  ("p", "That last line is the one to keep in view. The alternative to a good receiving interface "
        "is not a slower receiving process; it is a receiving process where every delivery is "
        "recorded as perfect, because that is the one button anybody has time to press."),
  ("h2", "What it asks for"),
  ("fig", ("chain", {
    "entry": {"title": "Delivery arrives", "sub": ["scan the PO barcode"], "icon": "truck"},
    "steps": [
      {"title": "Three lines to check", "sub": ["not twelve"], "icon": "form"},
      {"title": "Each: as claimed?", "sub": ["one big yes, one big no"], "icon": "branch",
       "exit": {"title": "Count it", "sub": ["number pad, that is all"], "icon": "counter",
                "label": "no"}},
      {"title": "Photograph", "sub": ["box, label, contents"], "icon": "image"},
      {"title": "Annotation generated", "sub": ["read it to the driver"], "icon": "doc"},
      {"title": "Sign, with it written on", "sub": ["both copies"], "icon": "person"}],
    "note": "No free text anywhere. Typing on a phone in a loading bay does not happen."}),
   "The whole receiving interaction. Every step is one tap or one photograph, and nothing "
   "requires composing a sentence.",
   "The five steps of recording a delivery at the door",
   "A vertical chain of five steps entered by a box labelled Delivery arrives, scan the purchase "
   "order barcode. Step one shows three lines to check, not twelve. Step two asks for each "
   "whether it is as claimed, with one big yes and one big no; a no exits to Count it, offering a "
   "number pad and nothing else. Step three takes a photograph of the box, the label and the "
   "contents. Step four generates the annotation and prompts the person to read it to the driver. "
   "Step five signs, with it written on both copies. A note says there is no free text anywhere, "
   "because typing on a phone in a loading bay does not happen."),
  ("h3", "Photographs are the evidence"),
  ("p", "A photograph of an open box with the product label, the packing slip and the visible "
        "shortfall in one frame is worth more in a supplier dispute than any amount of typed "
        "description, and it takes two seconds rather than two minutes."),
  ("p", "The system prompts for what to include rather than trusting somebody to think of it: "
        "one wide shot showing the pallet or box as delivered, one close shot with the label "
        "readable. Two photographs, a fixed order, no decisions."),
  ("h3", "No free text"),
  ("p", "Every free text field in a receiving app is empty in production. The information they "
        "were meant to capture is either derivable &mdash; which line, how many &mdash; or is "
        "better captured as a photograph."),
  ("p", "The one exception is a voice note, which some people will use and most will not, and "
        "which is cheap to offer as an optional extra rather than a required field. It is "
        "transcribed later, at a desk, by somebody with time."),
  ("h2", "Annotate, then sign"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Discrepancy found", "sub": ["short by 40"], "icon": "search"},
      {"title": "Wording generated", "sub": ["'2 of 12 boxes...'"], "icon": "doc"},
      {"title": "Written on the note", "sub": ["both copies"], "icon": "form"},
      {"title": "Driver sees it", "sub": ["and takes a copy"], "icon": "person"},
      {"title": "Then signed", "sub": ["as annotated"], "icon": "check"}],
    "title": "THE ORDER THAT MATTERS",
    "note": "Sign first and report later, and the signed clean note is what gets quoted back."}),
   "The sequence at the point of signature. Reversing these five boxes is the most common and "
   "most expensive receiving error there is.",
   "Why a delivery note is annotated before it is signed",
   "A horizontal row of five boxes. Discrepancy found: short by forty. Wording generated: two of "
   "twelve boxes, and so on. Written on the note: both copies. Driver sees it and takes a copy. "
   "Then signed, as annotated. A note says signing first and reporting later means the signed "
   "clean note is what gets quoted back."),
  ("p", "The generated wording matters because composing it is exactly the thing nobody will do "
        "under time pressure. \"Received 12 boxes. Box 7 opened at delivery: 40 units of "
        "BRG-4MM, packing slip states 60. Photographed. Signed subject to this note.\" is a "
        "sentence the system can produce and the person can copy."),
  ("p", "Giving the driver a copy with the same annotation is the step that makes it stick. A "
        "note on your copy only is a note the carrier has never seen."),
  ("h3", "Offline first"),
  ("p", "The interface has to work with no signal and sync when it gets one, because loading bays "
        "are consistently the worst-covered part of any building. Photographs and counts are held "
        "on the device and pushed when the person walks back inside."),
  ("p", "Everything the interface needs &mdash; the check list, the expected quantities &mdash; "
        "is downloaded when the slip is matched the day before, so nothing at the door depends on "
        "a network round trip."),
  ("p", "Next: what happens to the discrepancy."),
 ],
},
{
 "slug": "what-happens-to-over-and-under-shipments",
 "title": "What happens to over and under shipments",
 "nav": "Over and under shipments",
 "read": 5, "words": 730,
 "desc": ("Shortages and the same-day rule, over-shipments and who owns them, and why nothing is "
          "auto-rejected."),
 "og": ("An over-shipment is not a windfall and not a problem. It is somebody else's goods in "
        "your building until you say otherwise."),
 "abstract": ("How a shortage is escalated the same day, what to do with goods you did not order, "
              "why rejections stay with a person, and how the invoice ends up matching."),
 "lede": ("The two directions are not symmetrical. A shortage is a claim you have to make quickly "
          "with evidence; an over-shipment is a liability that arrives looking like a bonus."),
 "tags": ["goods receipt", "shortages", "over-shipment", "disputes", "invoicing", "serverless"],
 "takeaways": [
  "A shortage is reported to the supplier the same day, in writing, with the photographs.",
  "An over-shipment is reported too. Quietly keeping it is a decision somebody will regret.",
  "Nothing is auto-rejected. Refusing a delivery has commercial consequences.",
  "The receipt record drives the invoice match, so a shortage cannot be quietly paid for.",
  "Both directions produce the same record type, so both show up in the pattern analysis.",
 ],
 "blocks": [
  ("h2", "Shortages: the same day"),
  ("fig", ("chain", {
    "entry": {"title": "A shortage recorded", "sub": ["counted, photographed"], "icon": "counter"},
    "steps": [
      {"title": "Annotated note?", "sub": ["signed subject to it"], "icon": "branch",
       "exit": {"title": "Weaker position", "sub": ["still report it, today"], "icon": "alarm",
                "label": "no"}},
      {"title": "Notify the supplier", "sub": ["same day, in writing"], "icon": "email"},
      {"title": "Attach the evidence", "sub": ["both photographs"], "icon": "image"},
      {"title": "Hold the invoice line", "sub": ["not the whole invoice"], "icon": "money"},
      {"title": "Track to resolution", "sub": ["credit, or a redelivery"], "icon": "check"}],
    "note": "Same day matters more than perfect wording. Most supplier terms are short."}),
   "What follows a recorded shortage. The fourth box is the one that keeps a shortage from being "
   "silently paid for three weeks later.",
   "How a recorded shortage is escalated to the supplier",
   "A vertical chain of five steps entered by a box labelled A shortage recorded, counted and "
   "photographed. Step one asks whether the delivery note was annotated and signed subject to it; "
   "if not it exits to Weaker position, still report it today. Step two notifies the supplier the "
   "same day, in writing. Step three attaches the evidence, both photographs. Step four holds the "
   "invoice line, not the whole invoice. Step five tracks it to resolution, either a credit or a "
   "redelivery. A note says the same day matters more than perfect wording, because most supplier "
   "terms are short."),
  ("h3", "Hold the line, not the invoice"),
  ("p", "Holding an entire invoice because one line was short is a common response and it makes "
        "an enemy of the supplier's accounts department, who did not send the wrong quantity and "
        "cannot fix it. Holding the disputed line and paying the rest keeps the argument where it "
        "belongs."),
  ("p", "This requires the receipt record to feed the invoice match, which is the main integration "
        "in this system and is worth doing properly. If the receipt says forty and the invoice "
        "says sixty, that should be a flag rather than something somebody notices."),
  ("h2", "Over-shipments"),
  ("callout", "Goods you did not order, in your building", [
   "<strong>You do not own them.</strong> In most jurisdictions and most supplier terms, they are "
   "still the supplier's goods.",
   "<strong>Tell them the same day,</strong> exactly as with a shortage, with a photograph.",
   "<strong>Do not use them.</strong> Consuming goods you were sent by mistake makes a "
   "conversation into a liability.",
   "<strong>Store them separately</strong> and mark them, so they cannot be picked into an order.",
   "<strong>Ask what they want done:</strong> collection, return, or an invoice you can accept.",
   "<strong>Set a limit</strong> beyond which nobody has to store them indefinitely, and say so "
   "in the notification.",
  ]),
  ("p", "The temptation to say nothing is real and the arithmetic is against it. Free stock is "
        "worth its value once; a supplier discovering a pattern of unreported over-shipments "
        "costs the relationship, and stock that appears in the system without a receipt makes "
        "every subsequent stock count harder to trust."),
  ("h3", "Why they happen"),
  ("p", "Over-shipments cluster around the same causes as shortages &mdash; a picking error, a "
        "unit-of-measure confusion, a duplicated line &mdash; and treating them as the same "
        "record type means both show up in the pattern analysis. A supplier who is over-shipping "
        "twice a month is making the same kind of mistake as one who is under-shipping, and it is "
        "the same conversation."),
  ("h2", "Why nothing is auto-rejected"),
  ("fig", ("strip", {
    "stages": [
      {"title": "20% short", "sub": ["a rule could reject"], "icon": "counter"},
      {"title": "But: is it urgent?", "sub": ["a line stops without it"], "icon": "branch"},
      {"title": "But: partial helps?", "sub": ["usually yes"], "icon": "branch"},
      {"title": "But: return costs?", "sub": ["and goodwill"], "icon": "money"},
      {"title": "A person decides", "sub": ["in about a minute"], "icon": "person"}],
    "title": "WHY THERE IS NO AUTO-REJECT",
    "note": "The rule would be right sometimes and expensive the rest of the time."}),
   "The reasoning behind another deliberately missing feature. Every question in the middle three "
   "boxes is commercial and none of them are in the delivery data.",
   "Why a short delivery is never automatically rejected",
   "A horizontal row of five boxes. Twenty per cent short: a rule could reject it. But is it "
   "urgent, with a line stopping without it? But does a partial delivery help, which it usually "
   "does? But what do returns cost, in money and goodwill? A person decides, in about a minute. A "
   "note says the rule would be right sometimes and expensive the rest of the time."),
  ("p", "The receiving person is also the wrong person to make that call, which is why the "
        "interface never offers a reject button. They record what arrived; somebody with the "
        "commercial context decides what to do about it, usually within the hour and with the "
        "photographs in front of them."),
  ("h3", "The one exception"),
  ("p", "Goods that are obviously unsafe or wrong &mdash; the wrong chemical, a broken pallet "
        "that cannot be moved safely &mdash; are refused at the door on the person's judgement, "
        "and the system's job is to record that quickly rather than to have an opinion about it."),
  ("p", "Next: what the discrepancies add up to."),
 ],
},
{
 "slug": "how-discrepancies-become-a-pattern",
 "title": "How discrepancies become a pattern",
 "nav": "How patterns emerge",
 "read": 5, "words": 720,
 "desc": ("The supplier who is always short by a little, the product that is always miscounted, "
          "and the report that is worth reading."),
 "og": ("One shortage is an error. The same supplier short on the same product eleven times in a "
        "year is a business arrangement nobody agreed to."),
 "abstract": ("How individual discrepancies aggregate into supplier, product and unit-of-measure "
              "findings, what the recurring cases usually turn out to be, and what to report."),
 "lede": ("Individual discrepancies get resolved and forgotten, which is fine for each one and "
          "terrible in aggregate, because the recurring ones are where all the money is."),
 "tags": ["goods receipt", "patterns", "suppliers", "reporting", "analytics", "serverless"],
 "takeaways": [
  "Group by supplier, by product, and by unit of measure. The third one finds the most.",
  "A supplier consistently short by a small percentage is usually a systematic cause.",
  "Track the acceptance rate too: lines never counted cannot show up as discrepancies.",
  "Report the value, not the count. Eleven small shortages may matter less than one large.",
  "The output is a supplier conversation, not a scorecard.",
 ],
 "blocks": [
  ("h2", "Three groupings"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "By supplier", "sub": ["who is short, how often"], "icon": "truck",
       "label": "obvious"},
      {"title": "By product", "sub": ["one item, many suppliers"], "icon": "form",
       "label": "often packaging"},
      {"title": "By unit of measure", "sub": ["boxes vs units"], "icon": "counter",
       "label": "finds the most"}],
    "target": {"title": "A quarterly view", "sub": ["counts and value"], "icon": "chart",
               "then": {"title": "One conversation each", "sub": ["with evidence attached"],
                        "icon": "person"}},
    "note": "The third lane is unglamorous and repeatedly turns out to be the largest cause."}),
   "The three ways discrepancies are grouped. The unit-of-measure grouping is the one nobody "
   "thinks to build and the one that finds systematic errors.",
   "Three ways goods receipt discrepancies are grouped for analysis",
   "Three boxes stacked on the left. By supplier: who is short and how often, labelled obvious. By "
   "product: one item across many suppliers, labelled often packaging. By unit of measure: boxes "
   "versus units, labelled finds the most. All three converge on A quarterly view with counts and "
   "value, and that leads down to One conversation each, with evidence attached. A note says the "
   "third lane is unglamorous and repeatedly turns out to be the largest cause."),
  ("h3", "Unit of measure is where the money is"),
  ("p", "The classic case: the order says sixty units, the supplier's system holds the product in "
        "boxes of twelve, and somebody enters five. Five boxes is sixty units and everything is "
        "correct. Then the packaging changes to boxes of ten and nobody updates the mapping, and "
        "every order is short by ten units from that day onwards until somebody counts."),
  ("p", "That error is invisible to a supplier-level analysis, because the supplier is only short "
        "on one product. It is invisible to a product-level analysis if the product comes from "
        "several suppliers. It shows up immediately when discrepancies are grouped by the unit "
        "mapping in use."),
  ("h2", "The acceptance rate belongs in the report"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Supplier A", "parts": [("counted", 62), ("accepted", 38)]},
      {"label": "Supplier B", "parts": [("counted", 24), ("accepted", 76)]},
      {"label": "Supplier C", "parts": [("counted", 11), ("accepted", 89)]}],
    "series": [("counted", "Lines physically counted, %", "#7AA116"),
               ("accepted", "Lines accepted on the slip, %", "#7D8CA3")],
    "unit": "",
    "note": "Supplier C has almost no discrepancies. Almost nothing from them has been counted."}),
   "Why the discrepancy report needs the acceptance rate beside it. A supplier with a clean record "
   "and an eighty-nine per cent acceptance rate has a clean record for a reason that is not about "
   "their accuracy.",
   "The proportion of lines physically counted for three suppliers",
   "A stacked bar chart with three bars in per cent. Two series: lines physically counted in "
   "green, and lines accepted on the slip in grey. Supplier A shows sixty-two per cent counted "
   "and thirty-eight accepted. Supplier B shows twenty-four counted and seventy-six accepted. "
   "Supplier C shows eleven counted and eighty-nine accepted. A note says Supplier C has almost "
   "no discrepancies, and almost nothing from them has been counted."),
  ("p", "This is the correction that keeps the whole report honest. Discrepancy counts are counts "
        "of things that were looked for, and a supplier who is rarely checked will always look "
        "reliable. The rotating spot-check from Part 2 exists partly to keep this from getting "
        "extreme, and the acceptance rate is how you know whether it is working."),
  ("h3", "Value, not count"),
  ("p", "Eleven shortages of two units each on a cheap consumable is worth less attention than "
        "one shortage of four units on something expensive, and a report ordered by count puts "
        "them the wrong way round."),
  ("p", "Ordering by value also makes the report shorter, which is the property that determines "
        "whether anybody reads it. Three lines with money attached beats forty lines with counts."),
  ("h2", "What the report says"),
  ("callout", "The quarterly page", [
   "<strong>Total value of discrepancies:</strong> &pound;4,180 across 34 deliveries, of which "
   "&pound;3,020 recovered.",
   "<strong>Largest single cause:</strong> a unit-of-measure mapping on one product, 9 "
   "occurrences, &pound;1,340.",
   "<strong>By supplier:</strong> three named, with counts, values and their acceptance rates.",
   "<strong>Acceptance rate overall:</strong> 71% of lines were not physically counted.",
   "<strong>Over-shipments:</strong> 6, value &pound;510, all reported and 4 collected.",
   "<strong>Unresolved after 60 days:</strong> 2, both with the same supplier.",
  ]),
  ("p", "The second line is the one that pays for the system. A mapping error found in a "
        "quarterly report and fixed in five minutes was quietly costing more per year than the "
        "entire rest of the discrepancy list."),
  ("p", "The last line matters too, and it is the one most reports omit. Discrepancies that were "
        "raised and never resolved are the ones that get written off, and they are invisible "
        "unless something is counting how long they have been open."),
  ("h3", "A conversation, not a scorecard"),
  ("p", "As with lead times, the output is evidence for a conversation rather than a grade. "
        "\"Nine of the last thirty deliveries were short on this one product, here are the "
        "photographs, we think it is the box size mapping\" is a productive opening. A supplier "
        "accuracy percentage is not, because there is nothing in it to discuss."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="delivery",
 volumes=[(120, "120 deliveries"), (450, "450 deliveries"), (1800, "1,800 deliveries")],
 read_each=0.9,
 msgs_each=0.12,
 lede=("The only model call is reading a packing slip, and photographs are the main storage cost. "
       "Four hundred and fifty deliveries a month is a busy trade counter or a small distributor. "
       "Here is where each cent goes."),
 takeaway_extra=("Photograph storage grows steadily and is the line item to set a lifecycle rule "
                 "on from day one."),
 risks=[
  "<strong>Storing full-resolution photographs forever.</strong> Two per discrepancy at phone "
  "resolution adds up. Resize on upload and move to Infrequent Access after ninety days.",
  "<strong>Reading slips that arrive as structured data.</strong> Suppliers who send a file "
  "should be parsed, not read by a model. Check the format before spending a read.",
  "<strong>Photographing every delivery rather than every discrepancy.</strong> A photograph of a "
  "correct delivery proves nothing and costs the same as one that proves something.",
 ],
 per_unit_note=("The read band is one packing slip per delivery. Messaging covers supplier "
                "notifications on discrepancies only, which is a small fraction of deliveries."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ps",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the offline sync, and where the model is used."),
 outside=[
  {"title": "Packing slips", "sub": ["email, ahead of the van"], "icon": "doc"},
  {"title": "The receiving device", "sub": ["offline capable"], "icon": "person"},
  {"title": "Purchasing and invoicing", "sub": ["read and flag"], "icon": "money"}],
 inside=[
  {"title": "S3 + API", "sub": ["slips, photographs,", "sync endpoint"], "icon": "storage"},
  {"title": "Lambda x3", "sub": ["match, receive, aggregate"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["receipts, discrepancies"], "icon": "database"}],
 note="us-east-1. One account. The device works offline; counts and photographs sync on return.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Packing slips arriving by email ahead of "
  "the van. The receiving device, which is offline capable. And Purchasing and invoicing, which "
  "read records and receive flags. Inside the account, three groups. S3 holding slips and "
  "photographs alongside an API providing a sync endpoint. Three Lambda functions named match, "
  "receive and aggregate. And two DynamoDB tables named receipts and discrepancies. A note gives "
  "the region as us-east-1, one account, and states that the device works offline and that counts "
  "and photographs sync on return."),
 functions=[
  ["<code>ps-match</code>", "S3 put on the slips prefix",
   "Reads the slip, matches it to a purchase order, builds the check list",
   "120s / 1024&nbsp;MB"],
  ["<code>ps-receive</code>", "API, from the device",
   "Accepts counts and photographs, generates the annotation wording, records the receipt",
   "30s / 1024&nbsp;MB"],
  ["<code>ps-aggregate</code>", "EventBridge, weekly",
   "Groups discrepancies by supplier, product and unit mapping; computes acceptance rates",
   "120s / 1024&nbsp;MB"]],
 roles=[
  ["<code>ps-match-role</code>",
   "<code>s3:GetObject</code>, <code>bedrock:InvokeModel</code>, <code>dynamodb:PutItem</code>, "
   "<code>dynamodb:Query</code>",
   "The slips prefix; one model id; receipts; read-only on purchase orders"],
  ["<code>ps-receive-role</code>",
   "<code>s3:PutObject</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "The photographs prefix; receipts and discrepancies; one verified identity"],
  ["<code>ps-aggregate-role</code>", "<code>dynamodb:Query</code>",
   "Read-only across both tables"]],
 tables=[
  ("Table: receipts",
   "PK   po_number         S\n"
   "SK   line_no           N\n"
   "     sku               S\n"
   "     ordered_qty       N\n"
   "     slip_qty          N   what the packing slip claimed\n"
   "     counted_qty       N   null if not counted\n"
   "     status            S   counted | accepted | substituted\n"
   "     unit_mapping      S   'box of 12' -- the mapping in force at the time\n"
   "     photos            L   s3 keys, wide and close\n"
   "     received_at       S\n"
   "     annotated         BOOL true if written on the note before signing\n"
   "     received_by       S   a named person\n\n"
   "`status` distinguishes counted from accepted. A single 'received' value\n"
   "cannot answer the first question anybody asks two months later."),
  ("Table: discrepancies",
   "PK   supplier          S\n"
   "SK   found_at#po#line  S\n"
   "     kind              S   short | over | substituted | wrong_item\n"
   "     sku               S\n"
   "     expected          N\n"
   "     found             N\n"
   "     value_pence       N\n"
   "     unit_mapping      S   copied, so a later mapping change cannot rewrite history\n"
   "     notified_at       S   same day, or the reason it was not\n"
   "     resolved_at       S   credit or redelivery\n"
   "     resolution        S\n\n"
   "Over-shipments are the same record type as shortages, so both appear\n"
   "in the same pattern analysis. They usually share a cause.")],
 inbound=[
  "<strong>Slips arrive by email</strong> into an S3 prefix. Suppliers who send structured files "
  "are parsed directly; only unstructured slips reach the model.",
  "<strong>The device downloads the check list</strong> when the match completes, so nothing at "
  "the door needs a network round trip.",
  "<strong>Counts and photographs queue locally</strong> and sync when signal returns. The sync "
  "is idempotent on a device-generated id.",
  "<strong>The receipt record feeds the invoice match</strong>, so a held line cannot be quietly "
  "paid. That integration is the main one worth doing properly."],
 model_notes=[
  "<strong>One read per unstructured packing slip.</strong> Extracting product codes, quantities "
  "and units into lines.",
  "<strong>It never decides the check list.</strong> That is three rules: any difference, high "
  "value or history, plus the rotation.",
  "<strong>It never interprets a substitution.</strong> Whether a substituted product is "
  "acceptable is a judgement recorded against a person's name.",
  "<strong>The annotation wording is a template</strong>, not generated. A sentence written on a "
  "legal document is not a place for variation.",
  "<strong>Structured slips skip the model entirely,</strong> which over time is most of them and "
  "most of the bill."],
 gotchas=[
  "Record counted and accepted as different statuses. It is one field and it answers the "
  "question every dispute starts with.",
  "Copy the unit mapping onto the discrepancy record. A mapping corrected next month must not "
  "retroactively make old discrepancies disappear.",
  "Make the device work offline before anything else. A receiving app that needs signal in a "
  "loading bay is a receiving app that records everything as correct.",
  "Generate the annotation wording and show it before the signature step, not after. The order is "
  "the whole point.",
  "Put the acceptance rate on the discrepancy report. Without it, the least-checked supplier "
  "always looks like the best one."],
))
