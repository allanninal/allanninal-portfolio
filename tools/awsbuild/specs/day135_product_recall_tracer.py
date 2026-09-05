"""Day 135 -- 2026-09-06 -- Product recall tracer."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "product-recall-tracer"
NAME = "Product recall tracer"

SPEC = {
 "slug": SLUG, "date": "2026-09-06", "name": NAME,
 "tagline": ("Turns a recall notice into three lists -- what is still on your shelves, who you "
             "can actually name as having bought it, and what you can prove to an inspector -- "
             "and makes the difference between pulling sixty units and pulling four thousand."),
 "lede": ("A small system for anybody who sells physical goods: batch codes captured at goods-in, "
          "a recall notice read into the products and batches it actually names, a trace forward "
          "into stock and sales, and an honest count of the customers you cannot identify. Seven "
          "posts on the same system, one diagram at a time, with a cost breakdown and an "
          "engineering reference at the end."),
 "keywords": ["product recall", "batch traceability", "lot codes", "food safety",
              "withdrawal", "serverless"],
 "icons": ["box", "search", "shield"],
 "faq": [
  ("What is the difference between a withdrawal and a recall?",
   "A withdrawal removes stock before it reaches the consumer. A recall asks for it back after it "
   "already has. The trace is the same; the second one needs a customer list and the first one "
   "does not."),
  ("What does one step back, one step forward mean?",
   "You must be able to name who supplied you and who you supplied. It is the traceability "
   "standard in EU and UK food law, and it deliberately stops at your business customers -- "
   "individual consumers are not covered by it."),
  ("Why can I only identify some of the customers?",
   "Because a cash sale is anonymous by design. Online orders, accounts and loyalty scans carry a "
   "name; the rest do not, and any system that claims otherwise is guessing."),
  ("Do I need this if I only sell a handful of lines?",
   "The number of lines is not what decides it. Whether you wrote the batch code down at goods-in "
   "is what decides it, and that takes the same fifteen seconds however small you are."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "product-recall-tracer-on-aws",
 "title": "A product recall tracer on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Batch codes captured at goods-in, a notice read into batches, a trace into stock and "
          "sales, and an honest unmatched count. AWS, about $2 a month."),
 "og": ("The notice named four batch codes. Without them you do not recall sixty units, you "
        "recall four thousand -- and that decision was made months ago at goods-in."),
 "abstract": ("The whole system on one page -- goods-in, the notice, the forward trace and the "
              "evidence file -- and why the cost of a recall is set by a record you either made "
              "or did not make at delivery."),
 "lede": ("The notice arrives on a Tuesday afternoon. One product, four batch codes, a date "
          "range. Somebody walks the shelves with a printout. Two hours later the honest answer "
          "is that nobody can tell which of the units on the shelf came from those batches, so "
          "everything of that line goes in the skip, and the customer notice has to say "
          "everything too."),
 "tags": ["product recall", "traceability", "batch codes", "food safety", "stock control",
          "serverless"],
 "takeaways": [
  "A recall costs what your records let it cost. The expensive part is not finding stock.",
  "Batch capture happens at goods-in or it never happens at all.",
  "One step back and one step forward is the legal floor, not the useful answer.",
  "Count the customers you cannot name. That number is the point, not an embarrassment.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Deliveries", "sub": ["notes, labels,", "batch codes"], "icon": "truck"},
      {"title": "The notice", "sub": ["one product, four", "batch codes"], "icon": "alarm"},
      {"title": "Sales", "sub": ["tills, orders,", "accounts"], "icon": "cart"}],
    "inside": [
      {"title": "Batch register", "sub": ["what arrived, when,", "from whom"], "icon": "box"},
      {"title": "Forward trace", "sub": ["stock on hand,", "units sold"], "icon": "search"},
      {"title": "Three lists", "sub": ["quarantine, notify,", "cannot name"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "each delivery"},
              {"from": 1, "to": 1, "label": "rare"},
              {"from": 2, "to": 2, "label": "continuous", "up": True}],
    "note": "The notice is the cheap part and it arrives complete. The batch register is the "
            "expensive part and it has to already exist on the day the notice lands."}),
   "Three things outside the account, three pieces inside it. Only one of the three inputs is "
   "urgent, and it is the one you cannot prepare for.",
   "System: deliveries, a recall notice and sales joined into three lists",
   "Three boxes across the top sit outside the AWS account. On the left, Deliveries: notes, "
   "labels and batch codes. In the middle, The notice: one product, four batch codes. On the "
   "right, Sales: tills, orders and accounts. Each connects by an arrow to the AWS account "
   "container below, labelled each delivery, rare, and continuous respectively. Inside the AWS "
   "account are three components in a row. On the left, Batch register: what arrived, when, and "
   "from whom. In the middle, Forward trace: stock on hand and units sold. On the right, Three "
   "lists: quarantine, notify, and cannot name. A note says the notice is the cheap part and "
   "arrives complete, while the batch register is the expensive part and has to already exist on "
   "the day the notice lands."),
  ("h3", "Why the notice is never the hard part"),
  ("p", "Recall notices are unusually good documents. They are written to be acted on by "
        "strangers under time pressure, so they name the product, the pack size, the batch or lot "
        "codes, the best-before dates and the reason, in roughly that order, and they are "
        "published in a consistent format. Reading one is a solved problem."),
  ("p", "The hard part is on your side of the counter. The notice says <em>batch L4127</em>. Your "
        "stock system says you have forty-one of that product. It does not say which batch they "
        "came from, because nothing ever asked. So the question the notice poses is one your "
        "records were never built to answer, and the only safe answer is the widest one."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Batch register.</strong> Every delivery line recorded with its batch code, its "
   "supplier and its date, in about fifteen seconds. Part 2.",
   "<strong>The notice, read.</strong> A recall notice turned into the exact products, batches "
   "and date ranges it names, and nothing wider. Part 3.",
   "<strong>Forward trace.</strong> Those batches followed into what is still on the shelf and "
   "what has already left. Part 4.",
   "<strong>Three lists.</strong> Quarantine, notify, and the honest count of people you cannot "
   "identify -- plus the file you hand an inspector. Part 5.",
  ]),
  ("h2", "One notice, one small chain"),
  ("fig", ("strip", {
    "stages": [
      {"title": "1 notice", "sub": ["4 batch codes,", "one product"], "icon": "alarm"},
      {"title": "2,180 received", "sub": ["across the", "date window"], "icon": "truck"},
      {"title": "61 in stock", "sub": ["3 sites,", "quarantined"], "icon": "box"},
      {"title": "704 sold", "sub": ["from those", "batches"], "icon": "cart"},
      {"title": "208 nameable", "sub": ["496 cannot", "be identified"], "icon": "person"}],
    "title": "ONE NOTICE, THREE SITES, ONE WEEK",
    "note": "Without batch codes at goods-in, the third box reads 2,180 and the fifth reads "
            "everyone. That is the whole value of the system, and it is decided at delivery."}),
   "The same system as one line. Every number narrows except the last one, which is the number "
   "most systems refuse to report.",
   "One recall notice traced from delivery through stock to customers",
   "A horizontal row of five boxes joined by arrows. One notice naming four batch codes on one "
   "product. Two thousand one hundred and eighty units received across the date window. "
   "Sixty-one units still in stock across three sites, quarantined. Seven hundred and four units "
   "sold from those batches. Two hundred and eight of those buyers can be named and four hundred "
   "and ninety-six cannot be identified. A note says that without batch codes at goods-in the "
   "third box would read two thousand one hundred and eighty and the fifth would read everyone, "
   "which is the whole value of the system and is decided at delivery."),
  ("h2", "In plain words"),
  ("p", "At goods-in, each delivery line is recorded with three things that stock systems "
        "routinely throw away: the batch or lot code printed on the case, the supplier it came "
        "from, and the date it arrived. That is the one-step-back half of traceability, and it "
        "is the half almost everybody already has on paper somewhere and nowhere in a database."),
  ("p", "Sales are joined to batches by the oldest rule in stock control: first in, first out. "
        "This is an assumption, not an observation, and the system says so on every report it "
        "produces. Where a site scans a batch code at the till the assumption is replaced by a "
        "fact, and where it does not, the trace is a defensible estimate with its own confidence "
        "attached."),
  ("p", "When a notice arrives it is read into a structured claim: these product identifiers, "
        "these batch codes, this date range, this reason. Then that claim is run against the "
        "batch register in both directions -- forward into stock and sales, backward into which "
        "supplier and which delivery -- and three lists come out."),
  ("p", "The third list is the one that makes this system honest. Most retail sales are "
        "anonymous, and a recall system that only reports the customers it found is quietly "
        "reporting a fraction as if it were a total. This one reports both numbers, because the "
        "gap between them decides whether you also need a notice at the door."),
  ("callout", "Design rules that shaped every decision", [
   "The batch code is captured at goods-in or the system admits it does not know.",
   "First-in-first-out is an assumption and is labelled as one on every output.",
   "The unmatched customer count is reported as prominently as the matched one.",
   "A notice is read into codes, never into a product name alone.",
   "Nothing is deleted after a recall. The evidence file is the deliverable.",
   "The system quarantines on paper; a human moves the stock.",
  ]),
  ("h2", "What it does not do"),
  ("p", "It does not decide whether to recall. That is a judgement about safety made by people "
        "with a duty to make it, and often it has already been made by somebody else and sent to "
        "you. It does not contact your customers either; it produces the list and the wording, "
        "and a person sends it."),
  ("p", "It also does not pretend to trace a cash sale. If somebody paid with coins and took the "
        "item away, that unit is in the fifth box and no amount of engineering moves it into the "
        "fourth. The value of saying so plainly is that it turns a vague worry into a number you "
        "can put in a public notice."),
  ("p", "The next four posts walk through each piece: how fifteen seconds at goods-in decides "
        "what a recall costs, how a notice becomes a set of codes, how the forward trace works "
        "and where it is honest about guessing, and what the evidence file has to contain. One "
        "diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "fifteen-seconds-at-goods-in",
 "title": "The fifteen seconds at goods-in that decide what a recall costs",
 "nav": "Capturing the batch",
 "read": 5, "words": 800,
 "desc": ("Three ways a batch code arrives, why none of them is a keyboard, and what to store "
          "the moment a pallet lands."),
 "og": ("The batch code is printed on every case you receive. It is captured almost nowhere, and "
        "recreating it later is impossible rather than expensive."),
 "abstract": ("Capturing lot codes at delivery from a note, a label photo or a supplier feed, and "
              "why this is the only step in the system that cannot be done retrospectively."),
 "lede": ("Everything else in this system can be built after the notice arrives. This part "
          "cannot. A batch code that was not written down at delivery is not recoverable from "
          "anywhere, at any price, and that single fact is what makes goods-in the whole "
          "design."),
 "tags": ["product recall", "traceability", "goods-in", "batch codes", "extraction",
          "serverless"],
 "takeaways": [
  "Batch codes arrive three ways and a keyboard is the worst of them.",
  "Store supplier, batch, quantity and date together or the row is not traceability.",
  "A photograph of the case label is a legitimate primary record.",
  "Best-before is not a batch code, but it is often the only code there is.",
  "Unreadable is a state to record, not a failure to hide.",
 ],
 "blocks": [
  ("h2", "Three ways a code arrives"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "The delivery note", "sub": ["batch column, often", "handwritten"],
       "icon": "doc", "label": "photo or scan"},
      {"title": "The case label", "sub": ["printed lot code", "and best-before"],
       "icon": "image", "label": "phone photo"},
      {"title": "A supplier feed", "sub": ["despatch advice,", "rare but exact"],
       "icon": "plug", "label": "file or API"}],
    "target": {"title": "Batch register", "sub": ["supplier, batch, qty,", "date, site"],
               "icon": "box",
               "then": {"title": "Confidence recorded", "sub": ["scanned, read,", "or assumed"],
                        "icon": "check"}},
    "note": "Three routes, one row. The third is the only exact one and the fewest suppliers "
            "offer it, so the design has to be good at the first two."}),
   "Whatever the route, the same five fields come out, plus an honest note about how they were "
   "obtained.",
   "Three routes for a batch code converging on one register",
   "Three boxes on the left feed one box on the right. The delivery note, with a batch column "
   "often handwritten, arrives by photo or scan. The case label, with a printed lot code and "
   "best-before, arrives by phone photo. A supplier feed, a despatch advice that is rare but "
   "exact, arrives by file or API. All three converge on the Batch register, holding supplier, "
   "batch, quantity, date and site, which in turn feeds a box labelled Confidence recorded: "
   "scanned, read, or assumed. A note says three routes produce one row, the third is the only "
   "exact one and the fewest suppliers offer it, so the design has to be good at the first two."),
  ("h3", "Why not just type it"),
  ("p", "Because a batch code is a string with no meaning and no checksum, typed by somebody "
        "holding a scanner in the other hand, in a cold room, against a clock. The error rate is "
        "high and, worse, the errors are silent: <code>L4127</code> entered as <code>L4l27</code> "
        "does not fail, it just quietly stops matching the notice that arrives four months later."),
  ("p", "A photograph does not have that failure mode. It is wrong or it is unreadable, and both "
        "of those are states the system can record and a person can resolve. The image is also "
        "the evidence: when an inspector asks how you know that pallet was batch L4127, a picture "
        "of the case is a better answer than a database field."),
  ("h2", "What a traceable row actually contains"),
  ("fig", ("chain", {
    "entry": {"title": "Delivery", "sub": ["pallet at the", "back door"], "icon": "truck"},
    "steps": [
      {"title": "Capture", "sub": ["note, label or", "feed"], "icon": "image",
       "side": {"title": "S3", "sub": ["the photograph", "is the evidence"], "icon": "bucket"}},
      {"title": "Read the codes", "sub": ["batch, best-before,", "quantity"], "icon": "ocr"},
      {"title": "Match the product", "sub": ["to your own", "line codes"], "icon": "search",
       "exit": {"title": "Ask a human", "sub": ["a new supplier", "description"], "icon": "person",
                "label": "no match"}},
      {"title": "Write the row", "sub": ["supplier, batch,", "qty, date, site"], "icon": "box"},
      {"title": "Open the balance", "sub": ["units remaining", "in this batch"], "icon": "counter"}],
    "note": "The last step is what makes the register usable years later: a batch is not an "
            "event, it is a balance that draws down as things sell."}),
   "Five steps, one of which can stop and ask. Matching a supplier's description to your own "
   "product code is the step that fails, and it fails quietly if you let it.",
   "Goods-in from pallet to an open batch balance",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled "
   "Delivery, a pallet at the back door. Capture takes the note, label or feed and sends photos "
   "to S3 as a side output. Read the codes extracts batch, best-before and quantity. Match the "
   "product maps the supplier description to your own line codes and has a side exit reading no "
   "match, ask. Write the row stores supplier, batch, quantity, date and site. Open the balance "
   "records units remaining in this batch. A note says the last step is what makes the register "
   "usable years later, because a batch is not an event but a balance that draws down as things "
   "sell."),
  ("h3", "Best-before is not a batch code, and often it is all you have"),
  ("p", "Plenty of suppliers print no lot code at all, or print one that is really a date in "
        "disguise. Recall notices know this, which is why they usually name both: a batch code "
        "<em>and</em> a best-before date, sometimes as alternatives. So the register stores both, "
        "keeps them distinct, and never derives one from the other."),
  ("p", "The temptation is to normalise -- to turn <code>23/156</code> and "
        "<code>L23-156</code> and <code>156/23</code> into one canonical form. Resist it at "
        "ingest. Store the string exactly as printed, and do the fuzzy comparison at trace time "
        "where a human can see what matched what. A normaliser that silently merges two real "
        "batches is worse than no normaliser."),
  ("callout", "The five fields, and why each one is there", [
   "<strong>Supplier.</strong> One step back. Also the only route to the rest of the batch.",
   "<strong>Batch code, verbatim.</strong> Exactly as printed, including the parts that look "
   "like noise.",
   "<strong>Best-before.</strong> Separate field. Half of all notices name it instead.",
   "<strong>Quantity and site.</strong> Turns the batch into a balance you can draw down.",
   "<strong>Confidence.</strong> Scanned, read from a photo, or assumed. Changes what you can "
   "claim later.",
  ]),
  ("h2", "The cost of skipping it"),
  ("p", "Fifteen seconds a delivery line, at a hundred lines a week, is about twenty minutes. "
        "The comparison is not against zero, because without it a recall means pulling every unit "
        "of the line and writing to every customer who ever bought it -- and doing that once "
        "costs more than a year of the twenty minutes."),
  ("p", "There is a second cost that is easier to miss. A business that cannot bound a recall "
        "also cannot defend itself against one. If you can show that only four hundred and "
        "ninety-six units of the affected batches ever left your building, that is the size of "
        "the problem. If you cannot, the size of the problem is whatever anybody claims."),
 ],
},
{
 "slug": "reading-a-recall-notice",
 "title": "Turning a recall notice into codes, not a product name",
 "nav": "Reading the notice",
 "read": 5, "words": 780,
 "desc": ("What a notice actually specifies, why matching on a product name is dangerous, and "
          "how to widen a trace deliberately rather than by accident."),
 "og": ("Two of the four batch codes on the notice matched nothing we had ever received. That is "
        "information, not an error."),
 "abstract": ("Reading a published recall notice into product identifiers, batch codes, dates and "
              "a reason, and keeping the trace exactly as wide as the notice makes it."),
 "lede": ("A recall notice is one of the few documents in this series written specifically to be "
          "acted on quickly by somebody who has never seen it before. It is structured, it is "
          "consistent, and it names codes. The risk is not reading it wrongly; it is reading it "
          "more loosely than it was written."),
 "tags": ["product recall", "notices", "batch codes", "extraction", "food safety",
          "serverless"],
 "takeaways": [
  "Match on codes. A product name matches things the notice never named.",
  "A batch code that matches nothing you received is a useful negative result.",
  "Store the notice, its source and its date. The trace is only as good as its claim.",
  "Widen a trace deliberately, with a reason attached.",
  "Withdrawal or recall changes what you produce, not how you trace.",
 ],
 "blocks": [
  ("h2", "What a notice actually specifies"),
  ("fig", ("chain", {
    "entry": {"title": "Notice", "sub": ["agency alert or", "supplier email"], "icon": "alarm"},
    "steps": [
      {"title": "Identify", "sub": ["product, pack size,", "brand"], "icon": "tag"},
      {"title": "Extract codes", "sub": ["batch codes and", "best-before dates"], "icon": "ocr"},
      {"title": "Bound the window", "sub": ["from and to, or", "explicitly open"], "icon": "calendar"},
      {"title": "Classify", "sub": ["withdrawal or recall,", "and the hazard"], "icon": "shield"},
      {"title": "Store the claim", "sub": ["with source and", "received time"], "icon": "archive",
       "exit": {"title": "Ask a human", "sub": ["a notice naming", "no codes"], "icon": "person",
                "label": "no codes"}}],
    "note": "The last step is the one people skip. A trace you cannot attribute to a specific "
            "notice is a trace you cannot defend six months later."}),
   "Five steps and one escape hatch. A notice with no codes at all is a real thing and it needs a "
   "human, not a wider guess.",
   "A recall notice read into a structured claim",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled "
   "Notice, an agency alert or supplier email. Identify captures product, pack size and brand. "
   "Extract codes takes batch codes and best-before dates. Bound the window records a from and "
   "to, or explicitly marks it open. Classify records whether this is a withdrawal or a recall "
   "and what the hazard is. Store the claim keeps the source and received time, with a side exit "
   "reading no codes, ask. A note says the last step is the one people skip, and that a trace you "
   "cannot attribute to a specific notice is one you cannot defend six months later."),
  ("h3", "Why not match on the product name"),
  ("p", "Because the notice names a product and a set of batches, and those are different "
        "statements. Matching on the name alone recalls every batch of that line you hold, which "
        "is the outcome the whole system exists to avoid. It is also, quietly, the outcome most "
        "spreadsheets produce, because a name is the only field they can join on."),
  ("p", "There is a subtler version of the same error. Supplier product descriptions drift: "
        "<em>Own Brand Hummus 200g</em> becomes <em>Houmous Classic 200g</em> after a packaging "
        "change, and a name match now returns two products where the notice named one. Codes do "
        "not drift, which is the entire reason to prefer them."),
  ("h2", "When the codes match nothing"),
  ("p", "Two of the four batch codes in the worked example matched nothing in the register. The "
        "instinct is to treat that as a failure of the trace. It is not. It means those batches "
        "went somewhere else, and the correct output is a documented negative: we received none "
        "of L4129 or L4130, here is the register query that says so, here is the date it ran."),
  ("p", "A documented negative is worth having for the same reason the positive is. It is the "
        "difference between telling an inspector that you checked and telling them that you "
        "believe you were not affected."),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Code matches a batch", "sub": ["trace forward,", "normal path"],
       "icon": "check", "label": "most"},
      {"title": "Code matches nothing", "sub": ["record a documented", "negative"],
       "icon": "search", "label": "common"},
      {"title": "Notice names no code", "sub": ["widen by product,", "with a reason"],
       "icon": "branch", "label": "rare"}],
    "target": {"title": "Trace scope", "sub": ["exactly what will", "be searched"],
               "icon": "target",
               "then": {"title": "Scope is stored", "sub": ["and never widened", "silently"],
                        "icon": "lock"}},
    "note": "Widening is allowed. Widening without recording that you widened, and why, is what "
            "turns a defensible trace into an assertion."}),
   "Three outcomes, one scope. The third is legitimate and rare, and it is the only one that "
   "should ever produce a name-based search.",
   "Three notice outcomes converging on a recorded trace scope",
   "Three boxes on the left feed one box on the right. Code matches a batch leads to a normal "
   "forward trace and is the most common. Code matches nothing records a documented negative and "
   "is common. Notice names no code widens the search by product with a reason attached and is "
   "rare. All three converge on Trace scope, holding exactly what will be searched, which feeds a "
   "box labelled Scope is stored and never widened silently. A note says widening is allowed, but "
   "widening without recording that you widened, and why, turns a defensible trace into an "
   "assertion."),
  ("h3", "Withdrawal or recall"),
  ("p", "The classification does not change the trace at all. Both need the same query against "
        "the same register. What it changes is which of the three lists matter: a withdrawal is "
        "about stock you still hold, so the quarantine list is the deliverable and the customer "
        "list may be empty. A recall is about units that already left, so the second and third "
        "lists become the work."),
  ("p", "Keeping the two words distinct is worth the small effort, because the language ends up "
        "in your customer communication. Telling people you have recalled something you merely "
        "withdrew invites them to check a cupboard that was never at risk, and it spends trust "
        "you will want later."),
 ],
},
{
 "slug": "tracing-forward-honestly",
 "title": "Tracing forward, and being honest about the guess",
 "nav": "The forward trace",
 "read": 5, "words": 810,
 "desc": ("Following a batch into stock and into sales, why first-in-first-out is an assumption, "
          "and how to label a trace you cannot fully prove."),
 "og": ("Sixty-one units on the shelf are a fact. Seven hundred and four units sold are an "
        "inference, and the report says which is which."),
 "abstract": ("Running a bounded scope against the batch register to produce stock and sales "
              "lists, with the first-in-first-out assumption made explicit on every row."),
 "lede": ("The forward trace is the part everybody pictures when they imagine this system, and "
          "it is the easiest part to build and the easiest to overstate. Half of what it produces "
          "is observed and half is inferred, and a report that does not separate the two is worth "
          "less than one that reports less."),
 "tags": ["product recall", "traceability", "stock control", "FIFO", "inference",
          "serverless"],
 "takeaways": [
  "Stock on hand is observed. Units sold from a batch is usually inferred.",
  "First-in-first-out is the inference. Name it on the report.",
  "A scanned batch at the till replaces the inference with a fact.",
  "Overlapping batches on one shelf are normal and break clean arithmetic.",
  "Report a range when you have one, not a midpoint.",
 ],
 "blocks": [
  ("h2", "Two questions, two kinds of answer"),
  ("fig", ("system", {
    "outside": [
      {"title": "Trace scope", "sub": ["products, batches,", "dates"], "icon": "target"},
      {"title": "Stock counts", "sub": ["by site, as", "counted"], "icon": "box"},
      {"title": "Sales lines", "sub": ["date, site, qty,", "sometimes batch"], "icon": "cart"}],
    "inside": [
      {"title": "On hand", "sub": ["observed where", "batch was scanned"], "icon": "check"},
      {"title": "Drawn down", "sub": ["inferred by", "first-in-first-out"], "icon": "flow"},
      {"title": "Two lists, labelled", "sub": ["fact and", "inference"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "the claim"},
              {"from": 1, "to": 1, "label": "counted"},
              {"from": 2, "to": 2, "label": "inferred", "up": True}],
    "note": "The middle box is the only place a guess is made, and it is the box the whole "
            "report has to be honest about."}),
   "Three inputs, two answers, one of which is an estimate. Keeping them in separate boxes on the "
   "diagram is the same discipline as keeping them in separate columns on the report.",
   "The forward trace separating observed stock from inferred sales",
   "Three boxes across the top sit outside the AWS account. On the left, Trace scope: products, "
   "batches and dates. In the middle, Stock counts by site, as counted. On the right, Sales "
   "lines, holding date, site, quantity and sometimes a batch. Each connects to the AWS account "
   "container below, labelled the claim, counted, and inferred. Inside are three components. On "
   "hand, observed where the batch was scanned. Drawn down, inferred by first-in-first-out. And "
   "Two lists, labelled fact and inference. A note says the middle box is the only place a guess "
   "is made, and it is the box the whole report has to be honest about."),
  ("h3", "Why first-in-first-out is only an assumption"),
  ("p", "The register knows two thousand one hundred and eighty units of the affected batches "
        "arrived between the fourth and the eleventh, and it knows how many units of that line "
        "sold each day since. It does not know that the units which sold on the twelfth were the "
        "ones that arrived on the fourth. It assumes it, because stock rotation is supposed to "
        "work that way and mostly does."),
  ("p", "Mostly is the operative word. A case pushed to the back of a shelf, a second delivery "
        "stacked in front of the first, a site that received from two depots in the same week -- "
        "each of these breaks the assumption in a direction the arithmetic cannot see. The result "
        "is not wrong so much as unfalsifiable, and the honest response is a range."),
  ("h2", "Where the guess disappears"),
  ("fig", ("strip", {
    "stages": [
      {"title": "No batch capture", "sub": ["whole line is", "in scope"], "icon": "stop"},
      {"title": "Batch at goods-in", "sub": ["window bounded,", "FIFO inferred"], "icon": "box"},
      {"title": "Batch at pick", "sub": ["exact for online", "and wholesale"], "icon": "search"},
      {"title": "Batch at till", "sub": ["exact for every", "sale"], "icon": "check"}],
    "title": "FOUR LEVELS OF TRACEABILITY, LEFT TO RIGHT",
    "note": "Most businesses can reach the second in a week and the third in a month. The fourth "
            "needs the code on a barcode, which is somebody else's decision."}),
   "Each step right replaces an inference with an observation, and the second step is the one "
   "that moves a recall from the whole line to a bounded window.",
   "Four levels of batch traceability from none to scanned at the till",
   "A horizontal row of four boxes joined by arrows. No batch capture means the whole line is in "
   "scope. Batch at goods-in bounds the window and infers by first-in-first-out. Batch at pick is "
   "exact for online and wholesale orders. Batch at till is exact for every sale. A note says "
   "most businesses can reach the second level in a week and the third in a month, while the "
   "fourth needs the code on a barcode, which is somebody else's decision."),
  ("h3", "Wholesale is easy and it matters most"),
  ("p", "If you sold cases on to another business, that transaction has a name, an address and an "
        "order number attached to it, and picking is usually done from a specific pallet. This is "
        "the one-step-forward half of the legal standard and it is the half that is genuinely "
        "achievable, because your customer is a company rather than a member of the public."),
  ("p", "It also matters more, because those cases were broken down and sold again. One wholesale "
        "line in the affected batches can represent more end consumers than every direct sale you "
        "made that week, which is why the trace ranks by units rather than by lines."),
  ("callout", "What each row on the report has to carry", [
   "<strong>Observed or inferred.</strong> Never blend them into one count.",
   "<strong>The basis.</strong> Scanned at till, picked from pallet, or FIFO estimate.",
   "<strong>A range where there is one.</strong> Between 640 and 770 beats a confident 704.",
   "<strong>Site and date.</strong> Because the quarantine is physical and somebody has to walk "
   "to it.",
   "<strong>The query that produced it.</strong> Re-runnable, months later, unchanged.",
  ]),
  ("h2", "Quarantine is a human action"),
  ("p", "The system marks sixty-one units as in scope at three sites. It does not move them, "
        "because it cannot, and a stock system that decrements a balance without anybody touching "
        "the shelf produces the worst possible outcome: a record saying the affected stock is "
        "isolated and a shelf on which it is still for sale."),
  ("p", "So the quarantine list is a task with a person and a timestamp against it. Counted, "
        "moved, confirmed. The gap between the list being produced and the last site confirming "
        "is itself a number worth keeping, because it is the honest measure of how long you were "
        "still selling it."),
 ],
},
{
 "slug": "the-list-you-cannot-make",
 "title": "The customer list you cannot make, and what to do instead",
 "nav": "Customers and evidence",
 "read": 5, "words": 820,
 "desc": ("Matching sales to nameable customers, reporting the ones you cannot name, and the "
          "evidence file that has to survive the recall by years."),
 "og": ("We could name 208 of 704 buyers. The remaining 496 are why the notice goes on the door "
        "as well as in the inbox."),
 "abstract": ("Turning traced sales into a contactable list, quantifying the unmatched remainder "
              "honestly, and assembling an evidence pack that reconstructs the whole decision."),
 "lede": ("This is the part where a recall system either tells the truth or flatters you. Every "
          "sale traced in the last post has to be turned into somebody you can contact, and for "
          "most retail businesses the majority cannot be, by design and quite properly."),
 "tags": ["product recall", "customer notification", "evidence", "data protection",
          "food safety", "serverless"],
 "takeaways": [
  "Report matched and unmatched as one sentence. Never publish just the matched count.",
  "A high unmatched share is the trigger for a public notice, not a failure.",
  "Contact the wholesale customers first. They multiply.",
  "The evidence file is the deliverable that outlives the recall.",
  "Do not build a customer identity graph to solve a recall.",
 ],
 "blocks": [
  ("h2", "From traced sales to people"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Wholesale orders", "sub": ["named account,", "exact quantity"],
       "icon": "truck", "label": "contact first"},
      {"title": "Online orders", "sub": ["address and", "email on file"], "icon": "browser",
       "label": "contact"},
      {"title": "Loyalty or account", "sub": ["scanned at the", "till"], "icon": "person",
       "label": "contact"},
      {"title": "Anonymous sales", "sub": ["cash or card,", "no identity"], "icon": "cart",
       "label": "cannot contact"}],
    "target": {"title": "Two numbers", "sub": ["208 nameable,", "496 not"], "icon": "report",
               "then": {"title": "Both are published", "sub": ["internally and to", "the regulator"],
                        "icon": "shield"}},
    "note": "The fourth route is not a gap to be closed. It is a property of selling things to "
            "the public, and the system's job is to size it."}),
   "Four routes, two numbers. Three of them produce a contactable person and the fourth produces "
   "a count, which is exactly as useful in the decision that follows.",
   "Four sales channels resolving into matched and unmatched counts",
   "Four boxes on the left feed one box on the right. Wholesale orders have a named account and "
   "exact quantity and are contacted first. Online orders have an address and email on file. "
   "Loyalty or account sales were scanned at the till. Anonymous sales, cash or card with no "
   "identity, cannot be contacted. All four converge on Two numbers: two hundred and eight "
   "nameable, four hundred and ninety-six not, which feeds a box labelled Both are published, "
   "internally and to the regulator. A note says the fourth route is not a gap to be closed but a "
   "property of selling things to the public, and the system's job is to size it."),
  ("h3", "Why the unmatched number is the useful one"),
  ("p", "If you can name six hundred and eighty of seven hundred and four buyers, an email does "
        "the job. If you can name two hundred and eight, an email reaches under a third of the "
        "people holding the product and the rest of the work has to happen somewhere else: a "
        "notice at the door, a post, a line to the agency, possibly press. The unmatched count is "
        "what makes that call, and it is the number a system optimised to look capable would bury."),
  ("p", "It also stops a bad instinct. Faced with a low match rate, the tempting fix is to build "
        "an identity graph -- join card tokens, match postcodes, infer households -- and "
        "retrofit names onto anonymous sales. That is a large amount of engineering, a "
        "substantial new data protection problem, and it produces probabilistic identifications "
        "on which you would then base a safety notice. The notice at the door is better in every "
        "dimension."),
  ("h2", "The evidence file"),
  ("fig", ("chain", {
    "entry": {"title": "Trace complete", "sub": ["three lists", "produced"], "icon": "check"},
    "steps": [
      {"title": "Freeze the inputs", "sub": ["notice, register,", "sales as they were"],
       "icon": "archive"},
      {"title": "Record the queries", "sub": ["re-runnable, with", "their results"], "icon": "code"},
      {"title": "Log the actions", "sub": ["quarantined, sent,", "posted, by whom"], "icon": "log"},
      {"title": "Attach the negatives", "sub": ["batches checked", "and not held"], "icon": "search"},
      {"title": "Seal and retain", "sub": ["years, not", "weeks"], "icon": "lock"}],
    "note": "Everything here is written during the recall, because none of it can be reconstructed "
            "afterwards and all of it is what an inspector asks for."}),
   "Five steps, all of them cheap at the time and impossible later. The fourth is the one people "
   "leave out and the one that proves you looked.",
   "Assembling a recall evidence file that survives the recall",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled "
   "Trace complete, three lists produced. Freeze the inputs stores the notice, register and sales "
   "exactly as they were. Record the queries keeps them re-runnable with their results. Log the "
   "actions records what was quarantined, sent and posted, and by whom. Attach the negatives "
   "records the batches checked and not held. Seal and retain keeps it for years, not weeks. A "
   "note says everything here is written during the recall, because none of it can be "
   "reconstructed afterwards and all of it is what an inspector asks for."),
  ("h3", "What retention actually means here"),
  ("p", "The stock and sales data behind a trace has its own retention rules and they are "
        "usually shorter than the period in which somebody might ask you about a recall. Freezing "
        "the inputs at trace time is what resolves that: you are not keeping five years of "
        "transactions on the off chance, you are keeping the specific slice that a specific "
        "notice caused you to look at."),
  ("p", "That slice is small. In the worked example the frozen evidence is a few thousand rows "
        "and eleven photographs. It is the cheapest thing in the entire system to store and the "
        "most expensive thing to be missing."),
  ("callout", "The sentence the report has to be able to write", [
   "We received 2,180 units of the named batches between 4 and 11 March.",
   "61 remain, at three sites, quarantined and confirmed by 17:40 the same day.",
   "704 were sold. 208 buyers are named and have been contacted.",
   "496 cannot be identified, so a notice is at the door and on the website.",
   "Two of the four named batches were never received; the query that shows it is attached.",
  ]),
  ("h2", "Where this ends"),
  ("p", "The system does not close the recall, because closing it is a judgement about whether "
        "enough has been done and by whom. What it does is make that judgement possible: a "
        "bounded scope, a labelled trace, two honest numbers, and a file that will still make "
        "sense to somebody who was not there."),
  ("p", "The next post prices it, and the one after gives the service names, the tables and the "
        "IAM. The interesting thing about the cost is how little of it scales with sales: the "
        "model reads deliveries and notices, and both of those are rare compared with the number "
        "of things you sell."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="site",
 volumes=[(3, "3 sites"), (12, "12 sites"), (40, "40 sites")],
 read_each=0.31,
 msgs_each=2.0,
 store_base=0.34,
 store_growth=0.0021,
 lede=("The model runs on deliveries and on notices, and both are rare. A site taking a hundred "
       "delivery lines a week is the driver here; recall notices are a handful a year and cost "
       "nothing worth counting. Twelve sites is a small chain. Here is where each cent goes."),
 takeaway_extra=("Nothing in this system runs per sale, so the bill is flat against turnover and "
                 "rises only with how much stock you take in."),
 risks=[
  "<strong>Running a model over the sales export.</strong> It is fixed-header CSV and it is the "
  "largest file in the system. Parse it; a model here would cost more than every other line "
  "combined.",
  "<strong>Storing every delivery photograph at full resolution forever.</strong> Keep the "
  "original until the batch balance closes, then keep a downsized copy with the evidence.",
  "<strong>Re-tracing to answer a follow-up question.</strong> Freeze the trace, then query the "
  "frozen result. Re-running against live stock a week later gives a different answer and "
  "destroys the audit trail.",
 ],
 per_unit_note=("Roughly one model call per delivery, against a mid-tier model, because a "
                "delivery note is a short document with a small number of fields and a "
                "photograph of a case label is mostly optical character recognition. Notices are "
                "read with a capable model because there are almost none of them and getting a "
                "batch code wrong is the one error the whole system cannot absorb."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="rt",
 lede=("The same system with the service names filled in: what reads a delivery, what reads a "
       "notice, what runs the trace, and where the register and the evidence sit."),
 outside=[
  {"title": "Delivery capture", "sub": ["photos from a", "phone"], "icon": "image"},
  {"title": "Recall notices", "sub": ["agency feed or", "mailbox"], "icon": "alarm"},
  {"title": "Stock and sales", "sub": ["CSV exports,", "nightly"], "icon": "cart"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["uploads, feeds and", "the nightly load"], "icon": "bucket"},
  {"title": "Lambda x5", "sub": ["goods-in, notice, trace,", "match, evidence"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["batches, notices,", "traces"], "icon": "database"}],
 note="us-east-1. One account. Deliveries arrive all day; notices are rare and urgent; the "
      "sales load is nightly and never on the critical path of a trace.",
 diagram_desc=(
  "Three boxes across the top sit outside the AWS account. Delivery capture, photos from a phone. "
  "Recall notices, from an agency feed or a mailbox. Stock and sales, CSV exports arriving "
  "nightly. Each connects to the AWS account container below. Inside are three components. S3 "
  "with EventBridge handling uploads, feeds and the nightly load. Five Lambda functions covering "
  "goods-in, notice, trace, match and evidence. And three DynamoDB tables holding batches, "
  "notices and traces. A note says us-east-1, one account, deliveries arrive all day, notices are "
  "rare and urgent, and the sales load is nightly and never on the critical path of a trace."),
 functions=[
  ["<code>rt-goods-in</code>", "S3 put, delivery prefix",
   "Reads a note or label photo into batch rows; opens a balance", "60s / 1024MB"],
  ["<code>rt-notice</code>", "SES inbound or feed poll",
   "Reads a notice into products, batch codes, dates and hazard", "60s / 1024MB"],
  ["<code>rt-trace</code>", "API, on demand",
   "Runs a stored scope against batches, stock and sales", "120s / 1024MB"],
  ["<code>rt-match</code>", "Step after trace",
   "Resolves traced sales to nameable customers; counts the rest", "120s / 1024MB"],
  ["<code>rt-evidence</code>", "Step after match",
   "Freezes inputs, queries, results and negatives into one object", "300s / 2048MB"],
 ],
 roles=[
  ["<code>rt-goods-in-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "One model id; the deliveries prefix; batches"],
  ["<code>rt-notice-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "One model id; the notices prefix; notices"],
  ["<code>rt-trace-role</code>",
   "<code>dynamodb:Query</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "batches and notices read; traces write; the sales prefix"],
  ["<code>rt-evidence-role</code>",
   "<code>dynamodb:Query</code>, <code>s3:PutObject</code>, <code>ses:SendEmail</code>",
   "All three tables read; the evidence prefix write-once; one verified identity"],
 ],
 tables=[
  ("Table: batches",
   "PK   site#product_code S\n"
   "SK   batch_code        S   verbatim, exactly as printed\n"
   "     best_before       S   separate field, never derived from the batch\n"
   "     supplier_id       S   one step back\n"
   "     received_on       S   ISO date\n"
   "     qty_received      N\n"
   "     qty_remaining     N   drawn down; a batch is a balance, not an event\n"
   "     confidence        S   scanned | read | assumed\n"
   "     evidence_key      S   the photograph the code came from\n\n"
   "batch_code is stored verbatim and never normalised at ingest. Two real\n"
   "batches merged by a tidy-up are unrecoverable; a fuzzy match at trace\n"
   "time is reversible and a human can see what it did."),
  ("Table: notices",
   "PK   notice_id         S\n"
   "SK   '#claim'          S   one item per notice\n"
   "     source            S   agency | supplier | internal\n"
   "     received_at       S\n"
   "     action            S   withdrawal | recall\n"
   "     hazard            S   free text, from the notice\n"
   "     product_codes     L\n"
   "     batch_codes       L   what the notice actually named\n"
   "     best_befores      L   often named instead of a batch\n"
   "     window_from       S   null means explicitly open\n"
   "     window_to         S\n"
   "     widened_reason    S   set only when the scope is broader than the codes\n\n"
   "widened_reason is null on a normal trace. A non-null value is the record\n"
   "that somebody deliberately searched wider than the notice specified."),
  ("Table: traces",
   "PK   notice_id         S\n"
   "SK   trace_id          S   one item per run; runs are never overwritten\n"
   "     ran_at            S\n"
   "     qty_received      N\n"
   "     qty_on_hand       N   observed\n"
   "     qty_sold_est      N   inferred\n"
   "     qty_sold_low      N   the range, where FIFO leaves one\n"
   "     qty_sold_high     N\n"
   "     basis             S   scanned | picked | fifo\n"
   "     matched_customers N\n"
   "     unmatched_units   N   reported as prominently as the matched count\n"
   "     negatives         L   batch codes checked and not held\n"
   "     evidence_key      S\n\n"
   "qty_on_hand and qty_sold_est are deliberately separate fields with\n"
   "separate names. Summing them into one 'affected' number is the error the\n"
   "whole table exists to prevent."),
  ],
 inbound=[
  "<strong>Deliveries arrive as photographs</strong> from whatever phone is at the back door. "
  "There is no app to install and no terminal to buy, because the step has to survive a busy "
  "morning or it will not happen at all.",
  "<strong>Notices arrive by mailbox or feed</strong> and both land in the same function. A "
  "supplier email and an agency alert are the same document for our purposes.",
  "<strong>Stock and sales are parsed, not read by a model.</strong> They are fixed-header CSV "
  "and they are the largest files in the system.",
  "<strong>A trace runs on demand and is never scheduled.</strong> It is caused by a notice, it "
  "is frozen when it finishes, and a follow-up question is answered from the frozen result rather "
  "than by running it again."],
 model_notes=[
  "<strong>One call per delivery, one per notice.</strong> Nothing per unit, per sale or per "
  "customer. The bill does not move when trade does.",
  "<strong>A mid-tier model for deliveries.</strong> A delivery note is short and structured and "
  "a case label is mostly character recognition; paying for a frontier model here buys nothing.",
  "<strong>A capable model for notices</strong>, because there are a handful a year and a batch "
  "code read wrongly is the one error nothing downstream can catch.",
  "<strong>Codes come back as strings, never as numbers.</strong> <code>0041</code> parsed as an "
  "integer is <code>41</code>, and it will match nothing for the rest of the system's life.",
  "<strong>No model touches the trace.</strong> The forward trace is a query and an assumption, "
  "both of which have to be re-runnable and explainable years later."],
 gotchas=[
  "Store the batch code verbatim. Normalising at ingest can merge two real batches, and that is "
  "not recoverable; compare fuzzily at trace time where a person can see the match.",
  "Keep best-before in its own field. Roughly half of published notices name a date rather than a "
  "lot code, and deriving one from the other loses both.",
  "Never sum on-hand and sold into a single affected figure. One is counted and the other is "
  "inferred, and the sum inherits the weaker claim without saying so.",
  "Report the unmatched customer count everywhere the matched count appears. The ratio between "
  "them is what decides whether a public notice is required.",
  "Freeze the trace. Re-running against live stock a week later produces a different answer to "
  "the same question, which is exactly what an audit trail exists to prevent.",
  "Do not build an identity graph to raise the match rate. It is a large new data protection "
  "surface, and a probabilistic identification is a poor basis for a safety notice.",
 ],
))
