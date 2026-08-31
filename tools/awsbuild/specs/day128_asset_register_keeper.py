"""Day 128 -- 2026-08-30 -- Asset register keeper."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "asset-register-keeper"
NAME = "Asset register keeper"

SPEC = {
 "slug": SLUG, "date": "2026-08-30", "name": NAME,
 "tagline": ("Keeps a record of what the business owns that is still true a year later -- which "
             "means solving disposal rather than acquisition, because every register drifts in "
             "the same direction and for the same reason."),
 "lede": ("A small system that records assets, handles the step everybody skips, and verifies "
          "itself by sampling rather than by an annual audit nobody has time for. The interesting "
          "part is that an asset register serves four different purposes that want different "
          "things, and most registers fail because nobody decided which one they were building. "
          "Seven posts on the same system, one diagram at a time, with a cost breakdown and an "
          "engineering reference at the end."),
 "keywords": ["asset register", "fixed assets", "inventory", "insurance", "depreciation",
              "serverless"],
 "icons": ["storage", "form", "check"],
 "faq": [
  ("What is an asset register keeper?",
   "A small serverless system that records what a business owns, tracks where it is, handles "
   "disposals properly, and verifies itself through periodic sampling."),
  ("Why do asset registers go wrong?",
   "Because things are added and never removed. Acquisition has a natural trigger -- an invoice "
   "-- and disposal has none, so the register grows away from reality in one direction."),
  ("What is the register for?",
   "Four things that want different data: insurance, accounting, replacement planning and knowing "
   "where things are. The post on this argues for deciding which before designing anything."),
  ("Do you need a full annual audit?",
   "No, and it is usually what kills the register. Sampling a portion each month produces better "
   "information and actually happens."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "asset-register-keeper-on-aws",
 "title": "An asset register keeper on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Records assets, handles disposals, and verifies by sampling rather than by an annual "
          "audit. AWS, about $2 a month."),
 "og": ("Every asset register is accurate on the day it is created and drifts in exactly one "
        "direction afterwards."),
 "abstract": ("The whole system on one page -- add, move, dispose &mdash; and why the third one "
              "is the only difficult part."),
 "lede": ("The register lists four hundred and eleven items. A walk round the building finds "
          "three hundred and forty of them, twelve things that are not on it at all, and a "
          "storeroom of equipment that was replaced in 2021 and never removed from anything. "
          "Nobody has done anything wrong; there is simply no moment at which disposal gets "
          "recorded."),
 "tags": ["asset register", "fixed assets", "inventory", "insurance", "depreciation", "serverless"],
 "takeaways": [
  "Registers drift because acquisition has a trigger and disposal has none.",
  "Decide which of the four purposes you are serving before choosing fields.",
  "Verify by sampling continuously, not by auditing annually.",
  "A physical label on the thing is unglamorous and is most of the solution.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Purchases", "sub": ["invoices, over", "a threshold"], "icon": "doc"},
      {"title": "The things", "sub": ["with labels on"], "icon": "storage"},
      {"title": "Whoever asks", "sub": ["insurance, finance,", "or 'where is it?'"], "icon": "person"}],
    "inside": [
      {"title": "Add", "sub": ["nearly automatic"], "icon": "form"},
      {"title": "Move and dispose", "sub": ["the hard part"], "icon": "route"},
      {"title": "Verify", "sub": ["by sampling,", "continuously"], "icon": "check"}],
    "edges": [{"from": 0, "to": 0, "label": "acquisitions"},
              {"from": 1, "to": 1, "label": "labels scanned"},
              {"from": 2, "to": 2, "label": "a register that is true", "up": True}],
    "note": "The middle box is where every register in the world fails."}),
   "Three things outside the account, three pieces inside it. Adding assets is easy and is not "
   "where registers go wrong.",
   "System: assets added, moved, disposed and verified",
   "Three boxes across the top sit outside the AWS account. On the left, Purchases: invoices over "
   "a threshold. In the middle, The things themselves, with labels on. On the right, Whoever "
   "asks: insurance, finance, or somebody wanting to know where something is. Each connects by an "
   "arrow to the AWS account container below. Acquisitions flow down into the account. Labels "
   "scanned feed in. A register that is true goes back out. Inside the AWS account are three "
   "components in a row. On the left, Add, which is nearly automatic. In the middle, Move and "
   "dispose, the hard part. On the right, Verify, by sampling continuously. A note at the bottom "
   "says the middle box is where every register in the world fails."),
  ("h3", "The asymmetry"),
  ("p", "Buying something produces an invoice, a payment, a delivery and a person who wanted it. "
        "There are several natural moments at which it can be added to a register and at least "
        "one of them usually happens."),
  ("p", "Disposing of something produces nothing. A laptop goes in a cupboard, a machine is taken "
        "away by a scrap merchant, a monitor stops working and is put in a skip. None of those "
        "events touches finance, none of them generates a document, and none of them causes "
        "anybody to open the register."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Add.</strong> Driven from purchasing above a threshold, with a label printed. Part 3.",
   "<strong>Move and dispose.</strong> Making both take seconds, because anything slower does not "
   "happen. Part 3.",
   "<strong>Verify.</strong> Sampling a portion continuously so that drift is measured rather "
   "than discovered. Part 4.",
  ]),
  ("h2", "One asset, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Invoice over £500", "sub": ["flagged"], "icon": "doc"},
      {"title": "Label printed", "sub": ["and stuck on"], "icon": "form"},
      {"title": "Scanned into a room", "sub": ["one tap"], "icon": "storage"},
      {"title": "Moved twice", "sub": ["scanned each time"], "icon": "route"},
      {"title": "Disposed 2029", "sub": ["scanned out, with a reason"], "icon": "check"}],
    "title": "ONE ASSET, END TO END",
    "note": "Every step is a scan. Typing anything at any point is where this breaks."}),
   "The same asset as one line. The whole lifecycle is barcode scans because a register "
   "maintained by typing is a register that is not maintained.",
   "One asset from purchase through to disposal",
   "A horizontal row of five boxes joined by arrows. Invoice over five hundred pounds, flagged. "
   "Label printed and stuck on. Scanned into a room, one tap. Moved twice, scanned each time. "
   "Disposed in 2029, scanned out with a reason. A note says every step is a scan, and typing "
   "anything at any point is where this breaks."),
  ("h2", "In plain words"),
  ("p", "An invoice comes in for a piece of equipment above the threshold. It is flagged, a label "
        "with a code is printed, and somebody sticks it on the thing when it arrives and scans it "
        "into a location. That takes about twenty seconds and it is the whole acquisition "
        "process."),
  ("p", "Over the next few years it moves twice, and each time somebody scans the label and picks "
        "a new location from a short list. In 2029 it is replaced, and whoever removes it scans "
        "it and picks a disposal reason: scrapped, sold, traded in, stolen, lost."),
  ("p", "Meanwhile, every month a handful of assets are sampled: a list of twenty appears on "
        "somebody's phone, they go and look, and they confirm or correct. That is the "
        "verification, and it produces a measured accuracy figure rather than an annual "
        "surprise."),
  ("callout", "Design rules that shaped every decision", [
   "Decide the purpose first; the fields follow from it.",
   "Disposal must be as easy as acquisition, or the register only grows.",
   "Physical labels on things. There is no software substitute.",
   "Sample continuously; never plan an annual full count.",
   "Record the accuracy figure and watch it, rather than assuming.",
   "A missing asset is a state, not a deletion.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Asset registers are usually built as a finance artefact and then asked to do three other "
        "jobs badly. The result is a spreadsheet with a purchase price, a depreciation "
        "calculation, a serial number and a location field that has said \"main office\" for six "
        "years."),
  ("p", "Deciding which purpose dominates, and being explicit that the others are secondary, "
        "produces a register that is genuinely useful for one thing rather than nominally useful "
        "for four."),
  ("p", "The next four posts walk through each piece: what the register is actually for, how "
        "things get onto it and off it, how it gets verified without a full audit, and what a "
        "good register tells you. One diagram per post, a cost breakdown, and an engineering "
        "reference at the end."),
 ],
},
{
 "slug": "what-the-register-is-actually-for",
 "title": "What the register is actually for",
 "nav": "What it is for",
 "read": 5, "words": 740,
 "desc": ("Four purposes that want different data, the threshold question, and choosing before "
          "designing."),
 "og": ("Insurance wants replacement cost, finance wants purchase price, operations wants "
        "location. One field cannot be all three."),
 "abstract": ("The four purposes an asset register serves, what each one needs, why they conflict, "
              "and how the capitalisation threshold should be set."),
 "lede": ("Almost every failed asset register failed because nobody chose between four "
          "incompatible jobs, and the fields ended up serving all of them approximately."),
 "tags": ["asset register", "insurance", "accounting", "purpose", "facilities", "serverless"],
 "takeaways": [
  "Four purposes: insurance, accounting, replacement planning, and finding things.",
  "Each wants a different value and a different level of detail.",
  "Choose the dominant one and be explicit that the others are secondary.",
  "The capitalisation threshold is an accounting question that should not set the register's.",
  "Some things belong on the register and not in the accounts, and vice versa.",
 ],
 "blocks": [
  ("h2", "Four jobs"),
  ("table", ["Purpose", "Wants", "Detail needed"], [
   ["Insurance", "Replacement cost today, and location", "Enough to make a claim"],
   ["Accounting", "Purchase price, date, depreciation method", "Enough for the accounts"],
   ["Replacement planning", "Age, condition, expected life", "Enough to forecast spend"],
   ["Finding things", "Where it is, right now", "Enough to walk to it"],
  ]),
  ("p", "The values conflict directly. A machine bought for eleven thousand pounds in 2019 has a "
        "book value of about four thousand, a replacement cost of maybe sixteen thousand, and a "
        "resale value of two. All three are correct answers to different questions and a single "
        "value field will hold whichever one the person entering it thought of."),
  ("p", "The detail conflicts too. Insurance is content with a category and a count for small "
        "items; operations needs to know which desk. Recording desk-level detail for insurance "
        "purposes is effort spent on a requirement nobody has."),
  ("h2", "Choosing"),
  ("fig", ("chain", {
    "entry": {"title": "Why are we building this?", "sub": ["answer honestly"], "icon": "question"},
    "steps": [
      {"title": "A claim was hard?", "sub": ["insurance leads"], "icon": "branch",
       "exit": {"title": "Replacement cost", "sub": ["and photographs"], "icon": "image",
                "label": "yes"}},
      {"title": "The auditor asked?", "sub": ["accounting leads"], "icon": "branch",
       "exit": {"title": "Purchase and depreciation", "sub": ["and disposal dates"], "icon": "money",
                "label": "yes"}},
      {"title": "Capital budgeting?", "sub": ["planning leads"], "icon": "branch",
       "exit": {"title": "Age and condition", "sub": ["and expected life"], "icon": "clock",
                "label": "yes"}},
      {"title": "Things go missing?", "sub": ["operations leads"], "icon": "branch",
       "exit": {"title": "Location and custodian", "sub": ["updated often"], "icon": "person",
                "label": "yes"}},
      {"title": "The others are secondary", "sub": ["and say so"], "icon": "doc"}],
    "note": "Most registers answer 'all four' and therefore serve none of them well."}),
   "How the dominant purpose is chosen. The honest answer to the first question usually points at "
   "one of the four, and the rest follows from it.",
   "How the dominant purpose of an asset register is chosen",
   "A vertical chain of five steps entered by a box labelled Why are we building this, answered "
   "honestly. Step one asks whether a claim was hard, meaning insurance leads; if so it exits to "
   "Replacement cost and photographs. Step two asks whether the auditor asked, meaning accounting "
   "leads; if so it exits to Purchase and depreciation, and disposal dates. Step three asks "
   "whether it is for capital budgeting, meaning planning leads; if so it exits to Age and "
   "condition, and expected life. Step four asks whether things go missing, meaning operations "
   "leads; if so it exits to Location and custodian, updated often. Step five states that the "
   "others are secondary, and says so. A note says most registers answer all four and therefore "
   "serve none of them well."),
  ("h3", "Secondary is not absent"),
  ("p", "Choosing insurance as the dominant purpose does not mean the accounting fields are "
        "omitted; it means they are filled at a lower standard and nobody is surprised when they "
        "are approximate."),
  ("p", "Being explicit about that prevents the recurring conversation where somebody discovers "
        "the depreciation is wrong on a register that was never intended to drive the accounts."),
  ("h2", "The threshold"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Everything", "parts": [("items", 4100), ("value", 0)]},
      {"label": "Over £100", "parts": [("items", 890), ("value", 0)]},
      {"label": "Over £500", "parts": [("items", 411), ("value", 0)]},
      {"label": "Over £2,000", "parts": [("items", 96), ("value", 0)]}],
    "series": [("items", "Items on the register", "#8C4FFF"),
               ("value", "", "#7D8CA3")],
    "unit": "",
    "note": "The £500 register covers 94% of the value with a tenth of the items."}),
   "Register size at four thresholds. The value covered rises far more slowly than the item count "
   "does, which is the argument for a higher threshold than instinct suggests.",
   "The number of items on an asset register at four value thresholds",
   "A bar chart with four bars showing items on the register. Everything: four thousand one "
   "hundred. Over one hundred pounds: eight hundred and ninety. Over five hundred pounds: four "
   "hundred and eleven. Over two thousand pounds: ninety-six. A note says the five hundred pound "
   "register covers ninety-four per cent of the value with a tenth of the items."),
  ("p", "A register with four thousand items is one that nobody maintains, and an unmaintained "
        "register is worth less than a smaller accurate one. The threshold should be set at the "
        "point where the maintenance effort is sustainable, which is usually higher than the "
        "accounting capitalisation threshold."),
  ("p", "That is worth stating because the two get conflated. The accounts capitalise above a "
        "figure set by policy; the register tracks what is worth tracking, and there is no reason "
        "those numbers have to match."),
  ("h3", "Things that break the threshold"),
  ("p", "Two categories go on the register regardless of value. Anything attractive to steal "
        "&mdash; laptops, phones, power tools &mdash; because tracking them is the point. And "
        "anything with a statutory inspection from Day 118, because the certificate needs to "
        "attach to a recorded item."),
  ("p", "Conversely some expensive things do not belong: software licences, leased equipment that "
        "somebody else owns, and consumable stock which belongs in the inventory system rather "
        "than the asset register."),
  ("p", "Next: on and off."),
 ],
},
{
 "slug": "how-things-get-onto-it-and-off-it",
 "title": "How things get onto it and off it",
 "nav": "On and off",
 "read": 5, "words": 730,
 "desc": ("The invoice trigger, the label, why disposal has no natural moment, and how to create "
          "one."),
 "og": ("A register only ever grows unless somebody deliberately builds the moment at which "
        "things come off it."),
 "abstract": ("How acquisitions are captured from purchasing, why physical labels matter, the "
              "absence of a disposal trigger, and the moments where one can be created."),
 "lede": ("Acquisition solves itself if you attach it to purchasing. Disposal has to be invented, "
          "because nothing in the natural course of throwing something away involves a "
          "register."),
 "tags": ["asset register", "disposal", "labelling", "purchasing", "process", "serverless"],
 "takeaways": [
  "Trigger acquisition from the invoice, above the threshold.",
  "Print the label at that moment; a label applied later is a label never applied.",
  "Disposal has no natural trigger, so attach it to something that does happen.",
  "The replacement purchase is the best available disposal trigger.",
  "Never delete a disposed asset; mark it, with a reason and a date.",
 ],
 "blocks": [
  ("h2", "Acquisition is easy"),
  ("fig", ("chain", {
    "entry": {"title": "An invoice", "sub": ["from purchasing"], "icon": "doc"},
    "steps": [
      {"title": "Over the threshold?", "sub": ["per line"], "icon": "branch",
       "exit": {"title": "Not an asset", "sub": ["nothing happens"], "icon": "stop",
                "label": "no"}},
      {"title": "On the exclusion list?", "sub": ["licences, leases, stock"], "icon": "branch",
       "exit": {"title": "Not an asset", "sub": ["a different system"], "icon": "filter",
                "label": "yes"}},
      {"title": "Create the record", "sub": ["price, date, supplier"], "icon": "database"},
      {"title": "Print a label", "sub": ["now, not later"], "icon": "form"},
      {"title": "Scanned into place", "sub": ["when it arrives"], "icon": "storage"}],
    "note": "The label printing at step four is the difference between a register and a list."}),
   "How an asset is added. The label is printed as part of the purchasing flow rather than as a "
   "separate task, because a separate task does not happen.",
   "How a purchase becomes a labelled asset on the register",
   "A vertical chain of five steps entered by a box labelled An invoice from purchasing. Step one "
   "asks whether each line is over the threshold; if not it exits to Not an asset, nothing "
   "happens. Step two asks whether it is on the exclusion list of licences, leases and stock; if "
   "so it exits to Not an asset, a different system. Step three creates the record with price, "
   "date and supplier. Step four prints a label, now rather than later. Step five scans it into "
   "place when it arrives. A note says the label printing at step four is the difference between "
   "a register and a list."),
  ("h3", "The label is the system"),
  ("p", "A register entry with no corresponding label on the physical object is a row in a "
        "spreadsheet that can never be verified. Somebody looking at a machine cannot tell which "
        "row it is, and somebody looking at a row cannot find the machine."),
  ("p", "The label needs to be durable enough for the environment &mdash; a paper sticker on a "
        "workshop machine lasts about four months &mdash; and it needs a human-readable code as "
        "well as a barcode, because barcodes get damaged and people read numbers over the phone."),
  ("h2", "Disposal has no moment"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "It broke", "sub": ["and went in a skip"], "icon": "stop",
       "label": "no document"},
      {"title": "It was replaced", "sub": ["old one in a cupboard"], "icon": "storage",
       "label": "no document"},
      {"title": "It was sold", "sub": ["or traded in"], "icon": "money",
       "label": "sometimes a document"}],
    "target": {"title": "The register", "sub": ["still says we have it"], "icon": "question",
               "then": {"title": "For years", "sub": ["and it accumulates"], "icon": "chart"}},
    "note": "Two of the three most common disposals generate nothing at all."}),
   "The three ways things leave and how little evidence they produce. Only one of them touches a "
   "system anybody looks at.",
   "Three ways assets are disposed of and the documents they produce",
   "Three boxes stacked on the left. It broke and went in a skip, labelled no document. It was "
   "replaced and the old one went in a cupboard, labelled no document. It was sold or traded in, "
   "labelled sometimes a document. All three converge on The register, which still says we have "
   "it, and that leads down to For years, and it accumulates. A note says two of the three most "
   "common disposals generate nothing at all."),
  ("h3", "Creating a trigger"),
  ("p", "The most reliable available trigger is the replacement purchase. When something is "
        "bought that replaces an existing asset, the purchasing flow can ask one question: which "
        "one does this replace? A dropdown of plausible candidates, one tap, and the old asset "
        "moves to awaiting disposal."),
  ("p", "That catches a large share of disposals because most things are replaced rather than "
        "simply removed, and it attaches the question to a moment that definitely happens."),
  ("h3", "The other triggers"),
  ("callout", "Where else disposal can be caught", [
   "<strong>The replacement purchase.</strong> The best one, and it catches most of it.",
   "<strong>A skip or waste collection.</strong> Whoever books it can be asked what is going in "
   "it.",
   "<strong>The verification sample.</strong> An asset that cannot be found three times running "
   "is probably gone.",
   "<strong>A person leaving.</strong> The equipment assigned to them has to go somewhere, and "
   "that is a natural moment.",
   "<strong>An IT refresh.</strong> Bulk disposals, and the easiest to record because they are "
   "planned.",
   "<strong>None of these is complete.</strong> Together they get most of the way, which is the "
   "same pattern as visitor check-out.",
  ]),
  ("p", "The third one is worth building deliberately. An asset that the sampling process cannot "
        "find repeatedly is evidence, and after a stated number of attempts it should move to a "
        "presumed-disposed state with a person confirming rather than sitting on the register "
        "indefinitely."),
  ("h2", "Never delete"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Disposed", "sub": ["marked, not deleted"], "icon": "check"},
      {"title": "With a reason", "sub": ["scrapped, sold, stolen"], "icon": "form"},
      {"title": "And a date", "sub": ["for the accounts"], "icon": "clock"},
      {"title": "And a person", "sub": ["who says so"], "icon": "person"},
      {"title": "Still queryable", "sub": ["'what did we scrap in 2027?'"], "icon": "search"}],
    "title": "DISPOSAL IS A STATE",
    "note": "Deleting the row loses the accounting event and the pattern it belongs to."}),
   "How a disposal is recorded. Keeping the record is what allows disposal patterns to be "
   "analysed and what satisfies the accounting requirement.",
   "How an asset disposal is recorded as a state rather than a deletion",
   "A horizontal row of five boxes. Disposed: marked, not deleted. With a reason: scrapped, sold "
   "or stolen. And a date, for the accounts. And a person who says so. Still queryable: what did "
   "we scrap in 2027? A note says deleting the row loses the accounting event and the pattern it "
   "belongs to."),
  ("p", "The reason field is more useful than it looks. A category of equipment being scrapped "
        "consistently earlier than its expected life is a purchasing finding, and a rising count "
        "of stolen is a security one. Neither is visible if disposals are deletions."),
  ("p", "Next: knowing whether it is true."),
 ],
},
{
 "slug": "how-it-gets-verified-without-a-full-audit",
 "title": "How it gets verified without a full audit",
 "nav": "How it is verified",
 "read": 5, "words": 720,
 "desc": ("Why the annual count never happens, sampling continuously, and measuring accuracy as a "
          "number."),
 "og": ("An annual full asset count is planned every year and completed about one year in four. "
        "Twenty a month gets done."),
 "abstract": ("Why full audits fail, how continuous sampling works, how the sample is chosen, and "
              "what the accuracy figure is used for."),
 "lede": ("The plan is always a full count once a year, and the outcome is always that it happens "
          "twice and then stops, at which point nobody knows how accurate the register is."),
 "tags": ["asset register", "verification", "sampling", "audit", "accuracy", "serverless"],
 "takeaways": [
  "A full annual count is planned every year and rarely completed.",
  "Twenty assets a month gets done and covers a substantial register annually.",
  "Weight the sample: high value, high mobility and never-verified first.",
  "Publish the accuracy figure; it is the only measure of whether this works.",
  "Not found is a state with a count, not an immediate write-off.",
 ],
 "blocks": [
  ("h2", "Why the full count fails"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Full count planned", "parts": [("done", 0), ("planned", 411)]},
      {"label": "Actually counted", "parts": [("done", 130), ("planned", 281)]},
      {"label": "Sampling, per year", "parts": [("done", 240), ("planned", 171)]}],
    "series": [("done", "Assets actually verified", "#7AA116"),
               ("planned", "Intended and not done", "#7D8CA3")],
    "unit": "",
    "note": "The sampling approach verifies more, and it verifies the important ones first."}),
   "Three approaches to verification over a year. The full count starts well and stops; sampling "
   "continues and covers more.",
   "Assets verified under a full count and under continuous sampling",
   "A stacked bar chart with three bars. Two series: assets actually verified in green, and "
   "intended but not done in grey. Full count planned: none verified and four hundred and eleven "
   "intended. Actually counted: one hundred and thirty verified and two hundred and eighty-one "
   "not done. Sampling over a year: two hundred and forty verified and one hundred and "
   "seventy-one not reached. A note says the sampling approach verifies more and verifies the "
   "important ones first."),
  ("p", "The full count fails for the obvious reason: it is a day's work for several people, it "
        "is nobody's priority, and it is scheduled for a month that turns out to be busy. Two "
        "years running it slips and then it stops being scheduled."),
  ("p", "Twenty assets a month is twenty minutes with a phone and it survives being busy, which "
        "is the property that matters."),
  ("h2", "Choosing the sample"),
  ("fig", ("chain", {
    "entry": {"title": "Twenty this month", "sub": ["which twenty?"], "icon": "counter"},
    "steps": [
      {"title": "Never verified", "sub": ["always first"], "icon": "question"},
      {"title": "High value", "sub": ["weighted heavily"], "icon": "money"},
      {"title": "Mobile", "sub": ["laptops, tools"], "icon": "route",
       "side": {"title": "Why", "sub": ["they move, so they drift"], "icon": "search"}},
      {"title": "Oldest verification", "sub": ["fill the rest"], "icon": "clock"},
      {"title": "A list on a phone", "sub": ["with locations"], "icon": "form"}],
    "note": "Weighting beats randomness here; the register is not uniformly likely to be wrong."}),
   "How the monthly sample is chosen. Deliberate weighting finds more errors than a random sample "
   "of the same size.",
   "How a monthly asset verification sample is chosen",
   "A vertical chain of five steps entered by a box labelled Twenty this month, asking which "
   "twenty. Step one takes never-verified assets, always first. Step two weights high value "
   "heavily. Step three includes mobile items such as laptops and tools, with a side box "
   "explaining that they move so they drift. Step four fills the rest with the oldest "
   "verifications. Step five produces a list on a phone with locations. A note says weighting "
   "beats randomness here, because the register is not uniformly likely to be wrong."),
  ("h3", "What the check involves"),
  ("p", "Go to the recorded location, find the label, scan it, and answer one question: is it "
        "here and does it look like what the record says? If yes, tap and move on. If it is "
        "somewhere else, scan it wherever it is and the location updates. If it cannot be found, "
        "record that."),
  ("p", "The whole interaction is a scan and a tap, and if it involves anything more it will stop "
        "happening within two months."),
  ("h2", "The accuracy figure"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Q1", "parts": [("ok", 71), ("moved", 18), ("gone", 11)]},
      {"label": "Q2", "parts": [("ok", 79), ("moved", 15), ("gone", 6)]},
      {"label": "Q3", "parts": [("ok", 86), ("moved", 11), ("gone", 3)]}],
    "series": [("ok", "Found where recorded, %", "#7AA116"),
               ("moved", "Found elsewhere", "#ED7100"),
               ("gone", "Not found", "#DD344C")],
    "unit": "",
    "note": "This number is the only honest answer to 'is the register any good?'"}),
   "Three quarters of sampling results. The trend is what matters, and the register's credibility "
   "depends on this figure being published rather than assumed.",
   "Asset verification results over three quarters",
   "A stacked bar chart with three bars in per cent. Three series: found where recorded in green, "
   "found elsewhere in orange, and not found in red. Q1: seventy-one per cent found where "
   "recorded, eighteen elsewhere, eleven not found. Q2: seventy-nine, fifteen and six. Q3: "
   "eighty-six, eleven and three. A note says this number is the only honest answer to whether "
   "the register is any good."),
  ("p", "Publishing it does two things. It tells anybody relying on the register how much to rely "
        "on it, and it turns register maintenance from an act of faith into something with a "
        "measurable outcome that improves."),
  ("p", "The improvement in that chart came from the label printing moving into purchasing and "
        "the replacement-purchase disposal question, both of which are small changes whose effect "
        "is only visible because the accuracy was being measured."),
  ("h3", "Not found is not gone"),
  ("p", "An asset that cannot be found on one attempt is usually somewhere else, being used by "
        "somebody, or out for repair. Marking it not found and re-sampling it the following month "
        "resolves most of them."),
  ("p", "After a stated number of attempts &mdash; three is reasonable &mdash; it moves to "
        "presumed disposed, which requires a person to confirm and which produces the accounting "
        "event. That is a slow enough process to avoid writing off things that were merely on "
        "somebody's desk."),
  ("p", "Next: what a good register is good for."),
 ],
},
{
 "slug": "what-a-good-register-tells-you",
 "title": "What a good register tells you",
 "nav": "What it tells you",
 "read": 5, "words": 710,
 "desc": ("Replacement spend that can be forecast, the insurance claim that goes smoothly, and "
          "the equipment nobody uses."),
 "og": ("A register accurate enough to trust turns capital spending from a series of surprises "
        "into a schedule."),
 "abstract": ("What an accurate register enables: replacement forecasting, faster claims, and "
              "finding equipment that is not being used."),
 "lede": ("The register is maintained for one of the four purposes in Part 2, and once it is "
          "accurate it starts answering questions nobody built it for, which is the payoff for "
          "the discipline."),
 "tags": ["asset register", "capital planning", "insurance", "utilisation", "reporting",
          "serverless"],
 "takeaways": [
  "Age plus expected life gives a replacement forecast years ahead.",
  "A claim with photographs, serials and a verification date settles far faster.",
  "Assets that never move and are never used are candidates for disposal.",
  "Disposal reasons in aggregate are a purchasing signal.",
  "Connect it to maintenance: the machine costing the most is on both registers.",
 ],
 "blocks": [
  ("h2", "Replacement forecasting"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "2027", "parts": [("due", 18000)]},
      {"label": "2028", "parts": [("due", 12000)]},
      {"label": "2029", "parts": [("due", 61000)]},
      {"label": "2030", "parts": [("due", 9000)]}],
    "series": [("due", "Assets reaching expected life, replacement cost £", "#8C4FFF")],
    "unit": "£",
    "note": "2029 is a problem worth knowing about in 2027, not in 2029."}),
   "Replacement spend forecast from age and expected life. The lumpy year is the finding, and "
   "smoothing it requires three years of notice.",
   "Forecast replacement spend over four years from asset ages",
   "A bar chart with four bars showing assets reaching expected life, at replacement cost in "
   "pounds. 2027: eighteen thousand. 2028: twelve thousand. 2029: sixty-one thousand. 2030: nine "
   "thousand. A note says 2029 is a problem worth knowing about in 2027 rather than in 2029."),
  ("p", "The spike happens because things bought at the same time reach the end of their life at "
        "the same time, which is extremely common: a refit, a move, a growth phase. Knowing about "
        "it two years ahead allows some of it to be brought forward or deferred deliberately."),
  ("p", "The forecast needs an expected life per asset category, which is a judgement entered "
        "once and refined by what actually happens. The disposal records from Part 3 provide "
        "that: things scrapped consistently at six years against an assumed eight is a correction "
        "to make."),
  ("h2", "The claim"),
  ("callout", "What makes an insurance claim go smoothly", [
   "<strong>A list</strong> of what was in the affected area, with serial numbers.",
   "<strong>Photographs</strong> taken at acquisition or at verification, showing the item "
   "intact.",
   "<strong>Purchase evidence:</strong> supplier, date, price.",
   "<strong>A verification date</strong> showing somebody confirmed it was there recently.",
   "<strong>Replacement cost</strong> rather than book value, kept roughly current.",
   "<strong>All of this exists already</strong> if the register is maintained, and none of it can "
   "be assembled afterwards.",
  ]),
  ("p", "The fourth item is the one that surprises people and it does real work. A register entry "
        "verified six weeks before a fire is considerably more persuasive than one last touched "
        "in 2019, and it costs nothing extra because the verification was happening anyway."),
  ("h2", "The equipment nobody uses"),
  ("fig", ("chain", {
    "entry": {"title": "An accurate register", "sub": ["with locations"], "icon": "storage"},
    "steps": [
      {"title": "Never moved", "sub": ["in three years"], "icon": "clock"},
      {"title": "In a store room", "sub": ["not in use"], "icon": "route"},
      {"title": "Any maintenance?", "sub": ["from Day 118"], "icon": "branch",
       "exit": {"title": "It is in use", "sub": ["just stationary"], "icon": "check",
                "label": "yes"}},
      {"title": "Ask whose it is", "sub": ["somebody usually knows"], "icon": "person"},
      {"title": "Sell, redeploy, or scrap", "sub": ["a decision"], "icon": "money"}],
    "note": "Most organisations find several thousand pounds of this the first time they look."}),
   "How idle equipment is identified. It requires an accurate location history, which is why this "
   "only becomes possible once the register is being maintained.",
   "How unused equipment is identified from an asset register",
   "A vertical chain of five steps entered by a box labelled An accurate register with locations. "
   "Step one finds assets never moved in three years. Step two checks whether they are in a store "
   "room rather than in use. Step three asks whether there has been any maintenance, drawing on "
   "Day 118; if so it exits to It is in use, just stationary. Step four asks whose it is, since "
   "somebody usually knows. Step five decides to sell, redeploy or scrap. A note says most "
   "organisations find several thousand pounds of this the first time they look."),
  ("p", "The third gate matters because plenty of valuable equipment sits still: a machine that "
        "has been in the same bay for eleven years is not idle. Cross-referencing against "
        "maintenance records separates stationary from unused."),
  ("h3", "Disposal reasons as a signal"),
  ("p", "Aggregating the disposal reasons from Part 3 over a couple of years produces a "
        "purchasing finding that is otherwise invisible: a category of equipment that is "
        "consistently scrapped early, a brand that is scrapped rather than sold, a rising count "
        "of items recorded as stolen."),
  ("p", "None of those questions can be asked of a register where disposal means deleting the "
        "row, which is the practical argument for the design decision in Part 3."),
  ("h2", "Where this connects"),
  ("p", "The asset register is the spine that several of the other systems in this series hang "
        "off. Maintenance schedules attach to assets. Statutory inspection certificates attach to "
        "assets. Equipment replacement decisions use the unplanned cost per machine from Day 118 "
        "and the age from here."),
  ("p", "Which is an argument for getting the identifier right and using it everywhere: one code "
        "on one label that the maintenance system, the register and the certificates all "
        "reference. That single decision saves a great deal of reconciliation later."),
  ("h3", "The honest summary"),
  ("p", "An asset register is a maintenance obligation rather than a project. It becomes valuable "
        "at the point where somebody trusts it, that trust comes from the published accuracy "
        "figure, and the accuracy figure comes from twenty minutes a month."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="asset",
 volumes=[(150, "150 assets"), (600, "600 assets"), (2500, "2,500 assets")],
 read_each=0.0,
 msgs_each=0.08,
 lede=("There is no model in this system and the activity is low: a few acquisitions a month, a "
       "sample of twenty, and the occasional move. Six hundred assets is a substantial small "
       "business. Here is where each cent goes."),
 takeaway_extra=("Photographs at acquisition are the only storage that grows, and they are worth "
                 "the space for the claim."),
 risks=[
  "<strong>Storing photographs at full resolution.</strong> Resize on upload; a claim needs to "
  "show the item, not its serial number at ten megapixels.",
  "<strong>Recomputing depreciation nightly.</strong> It changes monthly at most and only matters "
  "when somebody asks.",
  "<strong>Tracking below the threshold.</strong> Four thousand items instead of four hundred is "
  "ten times the maintenance for six per cent more value.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. Messaging is the monthly "
                "sample list and disposal confirmations."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ar",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the state model, and the sampling weights."),
 outside=[
  {"title": "Purchasing", "sub": ["invoices, read only"], "icon": "doc"},
  {"title": "A phone", "sub": ["scanning labels"], "icon": "form"},
  {"title": "Labels", "sub": ["printed at acquisition"], "icon": "storage"}],
 inside=[
  {"title": "API + EventBridge", "sub": ["scans,", "monthly sample"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["acquire, scan, sample"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["assets, movements"], "icon": "database"}],
 note="us-east-1. One account. Disposal is a state, never a deletion; movements are append-only.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Purchasing, providing invoices read only. "
  "A phone, scanning labels. And Labels, printed at acquisition. Inside the account, three "
  "groups. An API for scans and EventBridge running the monthly sample. Three Lambda functions "
  "named acquire, scan and sample. And two DynamoDB tables named assets and movements. A note "
  "gives the region as us-east-1, one account, and states that disposal is a state rather than a "
  "deletion and movements are append-only."),
 functions=[
  ["<code>ar-acquire</code>", "Purchasing event or API",
   "Creates the asset above the threshold, applies exclusions, queues a label print",
   "30s / 512&nbsp;MB"],
  ["<code>ar-scan</code>", "API, from the phone",
   "Records a movement or a verification; updates location; handles disposal scans",
   "10s / 512&nbsp;MB"],
  ["<code>ar-sample</code>", "EventBridge, monthly",
   "Chooses the weighted sample, sends the list, escalates repeatedly-not-found assets",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>ar-acquire-role</code>",
   "<code>dynamodb:PutItem</code>, <code>sqs:SendMessage</code>", "Assets; the label print queue"],
  ["<code>ar-scan-role</code>", "<code>dynamodb:UpdateItem</code>, <code>dynamodb:PutItem</code>",
   "Assets; appends to movements"],
  ["<code>ar-sample-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Both tables; one verified identity"]],
 tables=[
  ("Table: assets",
   "PK   asset_id          S   the code on the label\n"
   "     description       S\n"
   "     category          S   drives expected life\n"
   "     serial            S\n"
   "     purchase_pence    N\n"
   "     purchased_at      S\n"
   "     replacement_pence N   kept roughly current, for insurance\n"
   "     expected_life_yrs N   from the category, refined by disposals\n"
   "     location          S\n"
   "     custodian         S   where it matters\n"
   "     state             S   in_use | awaiting_disposal | disposed\n"
   "                           | not_found | presumed_disposed\n"
   "     disposal_reason   S   scrapped | sold | traded | stolen | lost\n"
   "     disposed_at       S\n"
   "     last_verified_at  S   the field the insurance claim leans on\n"
   "     not_found_count   N   three consecutive triggers presumed_disposed\n"
   "     photos            L\n\n"
   "There is no delete path in any role. A disposed asset stays, which is\n"
   "what makes the disposal-reason analysis possible."),
  ("Table: movements",
   "PK   asset_id          S\n"
   "SK   at                S\n"
   "     kind              S   placed | moved | verified | not_found | disposed\n"
   "     from_location     S\n"
   "     to_location       S\n"
   "     by                S   a person, always\n\n"
   "Append-only. The location on the asset is derived from the latest\n"
   "movement, and 'never moved in three years' comes from this table.")],
 inbound=[
  "<strong>Acquisitions are triggered from purchasing</strong> above a threshold, with an "
  "exclusion list for licences, leases and stock.",
  "<strong>The label print is queued at acquisition</strong>, not left as a task. A label applied "
  "later is a label never applied.",
  "<strong>Every scan is a movement record</strong> with a person attached, and the current "
  "location is derived rather than overwritten.",
  "<strong>The replacement-purchase question</strong> is asked in the purchasing flow: which "
  "asset does this replace? It is the best available disposal trigger."],
 model_notes=[
  "<strong>There is no model in this system.</strong> It is a table with a state machine and a "
  "weighted sample.",
  "<strong>The tempting use</strong> is matching invoice lines to asset categories "
  "automatically. A supplier and a description mapping table does it more predictably.",
  "<strong>A defensible use</strong> is reading a serial number from a photograph at acquisition, "
  "which saves typing a long alphanumeric string.",
  "<strong>The wrong use</strong> is inferring disposal from inactivity. Part 4 escalates through "
  "three failed verifications and a person's confirmation instead, which is slow on purpose.",
  "<strong>The cost page assumes none</strong>, which is why the bill is fixed."],
 gotchas=[
  "Print the label as part of acquisition. A register entry with no physical label can never be "
  "verified in either direction.",
  "Give the assets table no delete path. Disposal is a state, and deleting it loses the "
  "accounting event and the pattern.",
  "Set the threshold higher than instinct suggests. Four thousand items is a register nobody "
  "maintains; four hundred is one that stays true.",
  "Sample twenty a month rather than planning an annual count. The annual count is planned every "
  "year and completed about one year in four.",
  "Publish the accuracy figure. It is the only honest answer to whether anybody should rely on "
  "the register, and it is what makes improvements visible."],
))
