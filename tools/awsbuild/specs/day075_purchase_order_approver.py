"""Day 75 -- 2026-07-08 -- Purchase order approver."""

SPEC = {
 "slug": "purchase-order-approver",
 "date": "2026-07-08",
 "name": "Purchase order approver",
 "tagline": ("Somebody asks to buy something, and within a minute it is either approved "
             "against a budget that is actually current, or it is sitting in front of the "
             "one person who should decide."),
 "lede": ("A small system that takes purchase requests from wherever your team already "
          "sends them, checks each one against the budget and the spend limits you wrote "
          "down, approves the small routine ones, and puts everything else in front of a "
          "person with the numbers already gathered. It never spends money on its own, and "
          "it never approves anything above the line you set. Seven posts on the same "
          "system -- one diagram at a time -- with a cost breakdown and an engineering "
          "reference at the end."),
 "keywords": ["purchase orders", "spend approval", "budget control", "small business finance",
              "human in the loop", "AWS Bedrock", "serverless"],
 "icons": ["form", "filter", "money"],
 "faq": [
  ("What is a purchase order approver?",
   "A small serverless system that receives purchase requests, reads them into a consistent "
   "shape, checks each one against the budget line it belongs to and the spend limits you "
   "wrote down, and either approves the routine ones or routes the rest to a person with the "
   "budget position already attached. It never spends money by itself."),
  ("Does it approve spending on its own?",
   "Only below a line you set, and only when every check passes: the budget line exists, "
   "there is room in it, the vendor is known, and the request is not a duplicate. Anything "
   "over the line, anything with a missing field, and anything unusual goes to a human. If a "
   "check cannot be made, the answer is always to ask a person, never to guess."),
  ("Where does the budget come from?",
   "A sheet you already keep. The system reads it, so changing a limit or adding a budget "
   "line is an edit in a spreadsheet, not a deploy. The sheet is the source of truth; the "
   "system never invents a line that is not in it."),
  ("What stops the same request being approved twice?",
   "Every request gets a fingerprint built from the requester, the vendor, the amount and the "
   "day. The first write of that fingerprint wins; a second one is rejected by the database "
   "itself rather than by a check that can race. A resent email or a double-tapped form "
   "button lands on the same request, not a second one."),
  ("What does it cost to run?",
   "A few dollars a month at small-business volume. There is nothing always-on: the cost is "
   "one model read per request plus fractions of a cent for the queue, the table and the "
   "mail. See part six for the breakdown and how it scales."),
 ],
 "parts": [],
}


SPEC["parts"] = [
# ---------------------------------------------------------------- part 1 --
{
 "slug": "purchase-order-approver-on-aws",
 "title": "A purchase order approver on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 980,
 "desc": ("Takes purchase requests from email, a form or Slack, checks each against your "
          "budget sheet and spend limits, approves the small routine ones and puts the rest "
          "in front of a person. AWS, about $3 a month."),
 "og": ("Reads each purchase request, checks it against the budget line and the limits you "
        "wrote down, and either approves a small routine buy or routes it to a person with "
        "the numbers attached."),
 "abstract": ("The whole system on one page -- an intake, a checker and a router, plus the "
              "rule that keeps it safe: it can approve small routine spend, and everything "
              "else waits for a person."),
 "lede": ("Someone on your team needs to buy something. They email you. You are on a site "
          "visit, so the email waits. Two days later they buy it anyway on a personal card, "
          "and now you have a receipt to reimburse, no purchase order, and a budget line "
          "that quietly went over without anyone noticing until the month closed. This post "
          "walks through the design of a small system that takes the request wherever it "
          "arrives, checks it against the budget you already keep in a sheet, approves the "
          "routine small ones on the spot, and puts everything else in front of you with "
          "the numbers already gathered."),
 "tags": ["purchase orders", "spend approval", "budget control", "human in the loop",
          "serverless", "AWS Bedrock"],
 "takeaways": [
  "Three ways to ask: a reply-to inbox, a short form, and a Slack shortcut. All three land as the same request.",
  "Every request ends in one of three states: approved, waiting on a person, or returned for a missing detail.",
  "The budget lives in a sheet you already keep. Changing a limit is an edit, not a deploy.",
  "It can approve small routine spend only. Above your line, a person decides -- always.",
  "Designed on AWS for about $3 a month at typical small-business volume.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Purchase requests", "sub": ["inbox, form, Slack"], "icon": "inbox"},
      {"title": "Budget sheet", "sub": ["lines, limits, vendors"], "icon": "chart"},
      {"title": "Approver", "sub": ["decides anything big"], "icon": "person"}],
    "inside": [
      {"title": "Intake", "sub": ["one shape for", "every request"], "icon": "form"},
      {"title": "Checker", "sub": ["budget line, room,", "vendor, duplicates"], "icon": "model"},
      {"title": "Router", "sub": ["approve small,", "ask about the rest"], "icon": "filter"}],
    "edges": [{"from": 0, "to": 0, "label": "requests in"},
              {"from": 1, "to": 1, "label": "grounds every check"},
              {"from": 2, "to": 2, "label": "anything over the line", "up": True}],
    "note": "No money moves without a person above your limit -- the system only ever proposes."}),
   "Three things outside the account, three pieces inside it. Requests arrive from an inbox, "
   "a form and a Slack shortcut. The checker reads the budget sheet and lands on approve, ask "
   "or return. The router either issues the small routine ones or puts the rest in front of a human.",
   "System: three request sources, three pieces inside AWS",
   "Three boxes across the top sit outside the AWS account. On the left, Purchase requests: the "
   "three ways somebody asks to buy something, which are a reply-to inbox, a short web form, and "
   "a Slack shortcut. In the middle, Budget sheet: the spreadsheet the business already keeps, "
   "listing budget lines, the spend limit on each, the approved vendors and the auto-approve "
   "threshold. On the right, Approver: the person who decides anything above that threshold. "
   "Each connects by an arrow to the AWS account container below. Requests flow down into the "
   "account. The budget sheet feeds in and grounds every check. The approver receives anything "
   "over the line, with the budget position already attached. Inside the AWS account are three "
   "components in a row. On the left, the Intake, which receives requests from all three sources "
   "and turns each into one consistent shape: who asked, what for, which budget line, how much, "
   "and which vendor. In the middle, the Checker, which reads the request against the sheet and "
   "answers four questions: does that budget line exist, is there room in it, is the vendor "
   "known, and has this same request come through before. On the right, the Router, which either "
   "issues a purchase order for small routine spend or sends the request to the approver. Arrows "
   "flow left to right between them. A note at the bottom says no money moves without a person "
   "above your limit; the system only ever proposes."),
  ("h3", "What you set up once (the outside)"),
  ("ul", [
   "<strong>Purchase requests.</strong> Three ways to ask, all covered in Part 2. The first is "
   "an inbox -- somebody emails a dedicated address the way they already email you. The second "
   "is a short form on your intranet, five fields long. The third is a Slack shortcut for the "
   "people who live there. All three end up as the same record: who asked, what they want, "
   "which budget line it belongs to, how much, and which vendor.",
   "<strong>A budget sheet.</strong> One tab you almost certainly already keep. Each row is a "
   "budget line -- \"Workshop consumables\", \"Site fuel\", \"Software\" -- with the amount for "
   "the period, the amount committed so far, the people allowed to spend against it, and the "
   "auto-approve threshold for that line. A second tab lists approved vendors. The sheet is the "
   "source of truth. If a line is not in the sheet, the system will not invent it; it returns "
   "the request and asks which line it belongs to.",
   "<strong>An approver.</strong> The person who owns the money. They get a short message per "
   "request -- what, how much, which line, how much is left in that line after this, and "
   "whether this vendor has been used before -- with two buttons: approve and decline, plus a "
   "box to ask a question. They are not reading a form. They are reading a number and a name.",
  ]),
  ("h3", "What runs on every request (the inside)"),
  ("ul", [
   "<strong>The intake.</strong> Three sources feed one queue. An email is messy prose; a form "
   "is already structured; Slack is somewhere in between. The intake turns all three into the "
   "same five fields, and this is the one place a model earns its keep -- reading \"can I get "
   "another two boxes of the blue gloves from Medline, same as last time\" and coming back with "
   "a vendor, a quantity, and a best-guess budget line. If it cannot fill a field with "
   "confidence, it leaves the field empty rather than filling it in with something plausible.",
   "<strong>The checker.</strong> Runs once per request and asks four plain questions against "
   "the sheet, in order. Does this budget line exist? Is there room in it for this amount? Is "
   "this vendor on the approved list? Has this same request already come through today? Each "
   "answer is a yes or a no with the number that produced it, so the decision can be read back "
   "later. None of this is the model's job -- it is arithmetic against a sheet, and plain code "
   "does arithmetic more reliably than any model will.",
   "<strong>The router.</strong> Reads the four answers and picks one of three outcomes. All "
   "four yes and under the line's auto-approve threshold: issue the purchase order, write it "
   "to the ledger, tell the requester. All four yes but over the threshold: send it to the "
   "approver with the budget position attached. Any no: return it to the requester saying "
   "exactly which check failed and what would fix it. Nothing is ever silently dropped.",
  ]),
  ("h2", "One request, end to end"),
  ("p", "Here is the same system as a single line, which is how it actually feels to use."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Asked", "sub": ["email, form, Slack"], "icon": "inbox"},
      {"title": "Read", "sub": ["into five fields"], "icon": "model"},
      {"title": "Checked", "sub": ["line, room, vendor"], "icon": "filter"},
      {"title": "Decided", "sub": ["auto or a person"], "icon": "branch"},
      {"title": "Committed", "sub": ["PO out, line updated"], "icon": "money"}],
    "title": "ONE PURCHASE REQUEST, END TO END",
    "note": "Five stages. The fourth is the only one where a person is ever required."}),
   "The same system as one line. A request is asked for, read into a fixed shape, checked "
   "against the sheet, decided either automatically or by a person, and then committed -- which "
   "means a purchase order goes out and the budget line moves.",
   "One purchase request from arrival to commitment, in five stages",
   "A horizontal row of five boxes joined by arrows. First, Asked: the request arrives by "
   "email, form or Slack. Second, Read: the request is turned into five fields, which are "
   "requester, item, budget line, amount and vendor. Third, Checked: the budget line, the room "
   "left in it and the vendor are all verified against the sheet. Fourth, Decided: either the "
   "amount is under the auto-approve threshold and the system issues it, or a person decides. "
   "Fifth, Committed: the purchase order goes out and the committed column on the budget line "
   "moves. A note below says five stages, and the fourth is the only one where a person is ever "
   "required."),
  ("h2", "In plain words"),
  ("p", "Your workshop lead needs gloves. She emails the requests address: \"another two boxes "
        "of the blue nitriles from Medline please, same as last month, about 90 dollars\". The "
        "intake reads that into five fields: requester her, item two boxes of nitrile gloves, "
        "vendor Medline, amount 90 dollars, budget line Workshop consumables. The checker opens "
        "the sheet. Workshop consumables exists. It has 1,240 dollars left this quarter, so "
        "there is room. Medline is on the approved list. Nobody has asked for the same thing "
        "today. All four are yes, and 90 dollars is under the 250-dollar auto-approve line you "
        "set on that row. So the router issues the purchase order, emails it to Medline, "
        "replies to her with the PO number, and moves the committed column from 760 to 850. "
        "Total elapsed time: under a minute, and you never saw it."),
  ("p", "The following week she needs a replacement bench grinder, 640 dollars. Same three "
        "checks pass, but 640 is over the line. So instead of issuing it, the router sends you "
        "one message: what it is, who asked, which line, and the sentence that actually matters "
        "-- \"Workshop consumables has 1,150 left this quarter; this would leave 510.\" You tap "
        "approve on your phone at the traffic lights. The PO goes out. That is the whole "
        "difference between this system and an inbox: the inbox gives you a request, and this "
        "gives you a request and the consequence of saying yes to it."),
  ("callout", "Design rules that shaped every decision", [
   "A person decides anything above the line. The system can issue small routine spend and "
   "nothing else, and the line is a number you write in the sheet.",
   "The sheet is the source of truth. The system reads budget lines, limits and vendors from "
   "it and never invents one that is not there.",
   "Every answer ships with the number behind it. \"No room\" always comes with how much is "
   "left and how much was asked for.",
   "Empty beats plausible. When the intake cannot read a field confidently, it leaves it blank "
   "and asks, rather than guessing a budget line.",
   "One request, one purchase order. A fingerprint on requester, vendor, amount and day makes "
   "a resend land on the same request instead of a second one.",
   "Nothing is silently dropped. A failed check returns to the requester saying which check "
   "failed and what would fix it.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Most small teams run purchase approval one of two ways. Either everything goes through "
        "one person's inbox, which works until that person is on a roof or on a plane, and then "
        "the whole business waits on them for a 90-dollar box of gloves. Or there is no process "
        "at all, people buy what they need and hand in receipts, and the budget is a thing you "
        "discover at month end rather than something you steer. The first is a bottleneck; the "
        "second is not a system, it is a hope."),
  ("p", "The shape above keeps the budget where the business already keeps it -- a sheet -- but "
        "puts a small, fast, boring layer in front of it. The layer is allowed to do exactly one "
        "consequential thing on its own: issue small, routine, in-budget, known-vendor purchase "
        "orders. Everything else it turns into a one-tap decision with the number attached. It "
        "does not need to be clever to be worth having. It needs to be quick, honest about what "
        "it does not know, and completely unwilling to spend money above a line you drew."),
  ("p", "The next four posts walk through each piece in turn: how a purchase request arrives, "
        "how it gets checked against the budget, how an approval reaches the right person, and "
        "how the money actually gets committed. One diagram per post, a cost breakdown, and an "
        "engineering reference at the end."),
 ],
},
# ---------------------------------------------------------------- part 2 --
{
 "slug": "how-a-purchase-request-arrives",
 "title": "How a purchase request arrives",
 "nav": "How it arrives",
 "read": 6, "words": 940,
 "desc": ("Three ways to ask for a purchase -- an inbox, a five-field form and a Slack "
          "shortcut -- and how all three become one record with the same five fields, or "
          "come back asking for the one that is missing."),
 "og": ("An inbox, a short form and a Slack shortcut all land as the same request record. "
        "What the reader fills in, what it refuses to guess, and how a resent email lands on "
        "the same request instead of a second one."),
 "abstract": ("Three lanes feed one queue. Every request becomes the same five fields, the "
              "reader leaves blank what it cannot read confidently, and a fingerprint stops "
              "a resend becoming a second order."),
 "lede": ("The fastest way to kill a purchase process is to make people use a system they do "
          "not already live in. So this one does not pick a channel. It takes an email, a "
          "short web form, or a Slack shortcut, and turns all three into the same five "
          "fields. This post is about that conversion, and about the two things that make it "
          "trustworthy: it leaves a field blank rather than guessing, and it will not create "
          "a second request for the same ask."),
 "tags": ["purchase orders", "intake", "Amazon SES", "Amazon SQS", "idempotency", "serverless"],
 "takeaways": [
  "Three lanes -- an inbox, a five-field form, and a Slack shortcut -- all land as one request record.",
  "The record is always the same five fields: requester, item, budget line, amount, vendor.",
  "A field the reader cannot fill confidently stays blank. Blank is a question; a guess is a bug.",
  "A fingerprint on requester, vendor, amount and day makes a resent email land on the same request.",
  "Attachments -- a quote PDF, a screenshot of a cart -- are kept and shown to the approver.",
 ],
 "blocks": [
  ("h2", "Three ways in, one shape out"),
  ("p", "People ask for things the way they already talk. Forcing everyone through one form is "
        "how you end up with a form nobody uses and a purchase process that lives in your "
        "inbox anyway. So there are three lanes, and they all end in the same place."),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Reply-to inbox", "sub": ["plain email, any wording"], "icon": "email",
       "label": "prose"},
      {"title": "Five-field form", "sub": ["on the intranet"], "icon": "form", "label": "fields"},
      {"title": "Slack shortcut", "sub": ["/buy, in the channel"], "icon": "chat",
       "label": "modal"}],
    "target": {"title": "One request queue", "sub": ["every ask becomes", "the same record"],
               "icon": "queue",
               "then": {"title": "Reader", "sub": ["fills what it can,", "leaves the rest blank"],
                        "icon": "model"}},
    "note": "Whichever lane it came from, what leaves the queue looks identical."}),
   "Three lanes into one queue. An email, a form and a Slack shortcut all become the same "
   "request record before anything is checked, which is why the rest of the system only has "
   "to understand one shape.",
   "Three request lanes converging on one intake queue",
   "Three boxes stacked on the left, each an outside source. The first is a reply-to inbox: "
   "somebody emails a dedicated address in plain prose, worded however they like. The second is "
   "a five-field form on the company intranet, which arrives already structured. The third is a "
   "Slack shortcut, typed as slash-buy in a channel, which opens a small modal. Each has an "
   "arrow labelled with what it carries -- prose, fields, and modal respectively -- converging "
   "on a single box on the right, One request queue, where every ask becomes the same record. "
   "Below that queue, connected by a downward arrow, is the Reader, which fills in what it can "
   "read confidently and leaves the rest blank. A note says whichever lane it came from, what "
   "leaves the queue looks identical."),
  ("h3", "The five fields"),
  ("p", "Everything downstream -- the budget check, the approval message, the purchase order "
        "-- reads exactly five fields. Keeping the list this short is deliberate. Every extra "
        "field is another thing the reader can get wrong and another thing a requester can "
        "leave out."),
  ("ul", [
   "<strong>Requester.</strong> Who asked. From the email sender, the form session, or the "
   "Slack user. This one is never guessed -- it comes from the channel itself, which is also "
   "why a forwarded email is treated as a request from the forwarder, not the original sender.",
   "<strong>Item.</strong> What they want, in their words, trimmed to one line. \"Two boxes of "
   "blue nitrile gloves, size L.\" Not normalised, not looked up in a catalogue. The approver "
   "is a human and reads human sentences faster than SKUs.",
   "<strong>Budget line.</strong> Which row in the sheet this belongs to. This is the field "
   "the reader gets wrong most often, and so it is the field it is most willing to leave blank.",
   "<strong>Amount.</strong> The number, in your currency. If a quote PDF is attached the "
   "reader prefers the number on the quote over the number in the email body, because people "
   "round in prose and quotes do not.",
   "<strong>Vendor.</strong> Who it is being bought from. Matched against the approved-vendor "
   "tab by name, loosely -- \"Medline\", \"Medline Industries\" and \"medline.com\" are the "
   "same vendor -- but a name with no match stays as typed and becomes a question later.",
  ]),
  ("h2", "What happens to one email"),
  ("p", "The email lane is the messy one, so it is worth following end to end."),
  ("fig", ("chain", {
    "entry": {"title": "Email arrives", "sub": ["to the requests address"], "icon": "email"},
    "steps": [
      {"title": "Store the raw message", "sub": ["S3, with attachments"], "icon": "bucket"},
      {"title": "Seen this ask before?", "sub": ["requester + vendor +", "amount + day"],
       "icon": "branch",
       "side": {"title": "DynamoDB requests", "sub": ["conditional write"], "icon": "database"},
       "exit": {"title": "Same request", "sub": ["reply on the original"], "icon": "stop",
                "label": "duplicate"}},
      {"title": "Read into five fields", "sub": ["one Bedrock call"], "icon": "model",
       "side": {"title": "Vendor list", "sub": ["from the sheet"], "icon": "doc"}},
      {"title": "All five filled?", "icon": "branch",
       "exit": {"title": "Ask the requester", "sub": ["name the missing field"], "icon": "person",
                "label": "gap"}},
      {"title": "Hand to the checker", "sub": ["one complete request"], "icon": "queue"}],
    "note": "The duplicate test runs before the model, so a resent email never costs a second read."}),
   "One email, end to end. The raw message is kept, the duplicate test runs before any model "
   "call, the read fills what it can, and a missing field becomes a question rather than a guess.",
   "How one email becomes a complete purchase request",
   "A vertical chain of five steps inside the AWS account, entered from the left by a box "
   "labelled Email arrives, to the requests address. Step one, Store the raw message in S3 "
   "along with any attachments. Step two, Seen this ask before, which fingerprints the "
   "requester, vendor, amount and day and writes it conditionally to a DynamoDB requests table "
   "shown to the right; if that write is rejected the request is a duplicate and the branch "
   "exits to Same request, reply on the original. Step three, Read into five fields with a "
   "single Bedrock call, grounded by the vendor list read from the sheet. Step four, All five "
   "filled, which exits to Ask the requester, naming the missing field, if any field is blank. "
   "Step five, Hand to the checker as one complete request. A note says the duplicate test runs "
   "before the model, so a resent email never costs a second read."),
  ("h3", "Why the duplicate test comes first"),
  ("p", "People resend. They forward the same request to a second address in case the first "
        "one was missed, they reply \"any update?\" on the same thread, they tap the form "
        "submit button twice on a bad connection. Every one of those is the same ask, and every "
        "one of them would otherwise become a second purchase order."),
  ("p", "So before anything expensive or consequential happens, the intake builds a fingerprint "
        "-- the requester, the vendor as typed, the amount, and the calendar day -- and tries to "
        "write it to DynamoDB with a condition that the key does not already exist. The database "
        "decides, not a query-then-write in the function, because two copies of the same email "
        "arriving a second apart will both pass a query and both write. A conditional write "
        "cannot both succeed. The loser reads the winner's request id and replies on that "
        "thread instead."),
  ("p", "Putting the test before the model read has a second benefit: a resent email costs "
        "nothing. The read is the only line on the bill that scales with volume, so not paying "
        "it twice for the same ask matters more than it looks."),
  ("h2", "Blank beats plausible"),
  ("p", "The reader is allowed to say it does not know. If the email is \"can we get the thing "
        "we talked about\", the item field will be the sentence as typed, and the budget line "
        "and the amount will be empty. The system does not guess a budget line from the "
        "requester's department, and it does not guess an amount from last month's order. It "
        "replies: \"Which budget line, and roughly how much?\""),
  ("p", "This looks like a worse system on a demo and is a much better one in practice. A "
        "guessed budget line is a wrong number in a real budget, discovered at month end, "
        "after the money is gone. A blank field is a fifteen-second reply."),
  ("callout", "What the intake guarantees", [
   "Every request that reaches the checker has all five fields filled, or it never reached the "
   "checker.",
   "One ask produces one request record, even if the same email arrives four times.",
   "The original message and every attachment are kept, so the approver can open the quote.",
   "The requester always hears back -- a request id, a question, or a purchase order. Never silence.",
  ]),
  ("p", "Next: what the checker actually does with those five fields, and why none of it is the "
        "model's job."),
 ],
},
# ---------------------------------------------------------------- part 3 --
{
 "slug": "how-a-purchase-request-gets-checked",
 "title": "How a purchase request gets checked",
 "nav": "How it gets checked",
 "read": 6, "words": 930,
 "desc": ("Four plain questions against the budget sheet -- does the line exist, is there "
          "room, is the vendor known, is this a repeat -- and why every one of them is "
          "arithmetic rather than a model call."),
 "og": ("The checker asks four questions against your budget sheet and answers each with the "
        "number behind it. None of it is the model's job: it is arithmetic, and arithmetic "
        "should be code."),
 "abstract": ("Four questions in a fixed order: does the budget line exist, is there room in "
              "it, is the vendor approved, and is this a repeat of something already "
              "committed. Every answer carries the number that produced it."),
 "lede": ("The model read the request. From here on, nothing is a judgement call. The checker "
          "asks four questions with yes-or-no answers, in a fixed order, against a sheet the "
          "business already maintains -- and it attaches the number behind every answer, so a "
          "decision can be read back six months later without anybody guessing what the "
          "system was thinking."),
 "tags": ["purchase orders", "budget control", "spend limits", "DynamoDB", "deterministic checks",
          "serverless"],
 "takeaways": [
  "Four checks, always in the same order: line exists, room in it, vendor approved, not a repeat.",
  "Every check is plain arithmetic against the sheet. The model never decides whether to spend.",
  "\"No room\" always ships with two numbers: what is left, and what was asked for.",
  "Committed is not spent. The line moves when the purchase order is issued, not when it is paid.",
  "A failed check is a specific sentence back to the requester, never a generic rejection.",
 ],
 "blocks": [
  ("h2", "Four questions, in order"),
  ("p", "The order matters, because a later answer is meaningless if an earlier one failed. "
        "There is no point telling somebody there is no room in a budget line that does not "
        "exist."),
  ("fig", ("chain", {
    "entry": {"title": "Complete request", "sub": ["five fields, from Part 2"], "icon": "form"},
    "steps": [
      {"title": "Does the line exist?", "sub": ["match against the sheet"], "icon": "branch",
       "side": {"title": "Budget sheet", "sub": ["lines and limits"], "icon": "chart"},
       "exit": {"title": "Ask which line", "sub": ["list the options"], "icon": "person",
                "label": "no match"}},
      {"title": "Is there room?", "sub": ["limit minus committed"], "icon": "branch",
       "side": {"title": "DynamoDB ledger", "sub": ["committed to date"], "icon": "database"},
       "exit": {"title": "Over budget", "sub": ["send with the numbers"], "icon": "person",
                "label": "no room"}},
      {"title": "Vendor approved?", "sub": ["fuzzy name match"], "icon": "branch",
       "side": {"title": "Vendor tab", "sub": ["approved suppliers"], "icon": "doc"},
       "exit": {"title": "New vendor", "sub": ["needs a person"], "icon": "person",
                "label": "unknown"}},
      {"title": "Already committed?", "sub": ["same line, same week"], "icon": "branch",
       "exit": {"title": "Possible repeat", "sub": ["show both, ask"], "icon": "stop",
                "label": "similar"}},
      {"title": "Four yeses", "sub": ["hand to the router"], "icon": "check"}],
    "note": "Every exit is a sentence to a human, with the numbers attached. None of them is a dead end."}),
   "The four checks in order, each reading one source and each with its own exit. Nothing is "
   "rejected outright -- every failed check becomes a specific question to a specific person.",
   "The four budget checks, in the order they run",
   "A vertical chain of five steps inside the AWS account, entered from the left by a box "
   "labelled Complete request, five fields, from Part 2. Step one asks whether the budget line "
   "exists, matching against the budget sheet shown to the right; if there is no match it exits "
   "to Ask which line, listing the options. Step two asks whether there is room, computing the "
   "limit minus the committed total read from a DynamoDB ledger; if there is no room it exits "
   "to Over budget, sent to a person with the numbers. Step three asks whether the vendor is "
   "approved, matching loosely against the vendor tab; an unknown name exits to New vendor, "
   "which needs a person. Step four asks whether something very similar has already been "
   "committed on the same line this week, exiting to Possible repeat, which shows both and "
   "asks. Step five is Four yeses, which hands the request to the router. A note says every "
   "exit is a sentence to a human with the numbers attached, and none of them is a dead end."),
  ("h3", "Does the budget line exist?"),
  ("p", "The reader put a budget line in the record, or left it blank and the intake already "
        "asked. Either way, the checker now matches that string against the rows in the sheet. "
        "Exact match first, then a loose one -- \"workshop consumables\" finds \"Workshop "
        "Consumables\", and \"consumables\" finds it too if there is only one row containing "
        "the word. Two candidate rows is not a match; it is a question, and the requester gets "
        "both to pick from."),
  ("h3", "Is there room?"),
  ("p", "Room is <code>limit - committed - this request</code>. Three numbers, one subtraction. "
        "The limit comes from the sheet. The committed total comes from the ledger, not the "
        "sheet, because the sheet is edited by people and the ledger is written by the system. "
        "If they disagree, the ledger wins for the check and the disagreement is flagged."),
  ("p", "The word <em>committed</em> is doing real work there. A purchase order that has been "
        "issued but not yet invoiced is money that is already spoken for. A system that only "
        "counted paid invoices would happily approve four orders against a line with room for "
        "one, and all four would be perfectly correct at the moment they were approved."),
  ("h3", "Is the vendor approved?"),
  ("p", "Matched against the vendor tab by name, loosely enough to survive how people actually "
        "type: case, punctuation, a trailing \"Ltd\", a domain instead of a name. An unmatched "
        "vendor is never a rejection -- new suppliers are normal. It routes to a person with "
        "the name as typed and a note that this vendor is not on the list yet, and approving it "
        "adds the row."),
  ("h3", "Is this already committed?"),
  ("p", "This is the softest of the four and the only one that can be wrong in a useful "
        "direction. It looks for a commitment on the same budget line, to the same vendor, "
        "within the same week, for an amount within ten per cent. That is not proof of a "
        "duplicate -- weekly consumables orders look exactly like that -- so it never blocks. "
        "It attaches both records to the message and lets the person look."),
  ("h2", "The shape of an answer"),
  ("p", "Each check returns three things: the answer, the numbers behind it, and the sentence "
        "a human would write. That third one is why the approval message in Part 4 reads like "
        "a person wrote it without a model being involved at that stage."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Line", "sub": ["Workshop consumables"], "icon": "chart"},
      {"title": "Room", "sub": ["1,150 left, 640 asked"], "icon": "counter"},
      {"title": "Vendor", "sub": ["Medline, known"], "icon": "check"},
      {"title": "Repeat", "sub": ["nothing similar"], "icon": "search"},
      {"title": "Verdict", "sub": ["over the line, ask"], "icon": "branch"}],
    "title": "WHAT THE CHECKER HANDS ON",
    "note": "Four answers and their numbers. The verdict is arithmetic, not judgement."}),
   "The checker's output for one real request. Four answers, each carrying the number that "
   "produced it, and a verdict that follows from them mechanically.",
   "The five values the checker produces for one request",
   "A horizontal row of five boxes. Line: matched to Workshop consumables. Room: 1,150 left in "
   "the line against 640 asked for. Vendor: Medline, known. Repeat: nothing similar found. "
   "Verdict: over the auto-approve line, so ask a person. A note says four answers and their "
   "numbers, and that the verdict is arithmetic rather than judgement."),
  ("callout", "Why none of this is the model's job", [
   "Subtraction has one right answer. A model gets it right almost always, and almost always "
   "is the wrong reliability for money.",
   "A check has to be explainable in one sentence with a number in it. Code produces that for "
   "free; a model has to be asked for it and can be asked twice and answer differently.",
   "The rules change often -- a new limit, a new vendor, a new line. Those are edits in a "
   "sheet. Nothing about them should require touching a prompt.",
   "The model already did the only thing it is better at than code: turning a sentence a "
   "person typed into five fields.",
  ]),
  ("p", "Next: what happens when the answer is \"ask a person\" -- who gets asked, what they "
        "see, and what happens if they never reply."),
 ],
},
# ---------------------------------------------------------------- part 4 --
{
 "slug": "how-an-approval-reaches-the-right-person",
 "title": "How an approval reaches the right person",
 "nav": "How it reaches a person",
 "read": 6, "words": 910,
 "desc": ("Who gets asked, what the message actually says, why it fits on a phone screen, "
          "and what happens when nobody replies for three days."),
 "og": ("One message, one number that matters, two buttons. Who gets asked comes from the "
        "budget line, not a hierarchy -- and an unanswered request escalates rather than "
        "expiring."),
 "abstract": ("The approver comes from the budget line, not an org chart. The message leads "
              "with the consequence -- what is left after saying yes -- and an unanswered "
              "request escalates on a schedule rather than dying quietly."),
 "lede": ("A request that fails no check but sits above the auto-approve line has to reach a "
          "person, and reaching a person is where most approval systems quietly fail. They "
          "send a notification that is really a form, to a queue nobody opens, and three days "
          "later somebody buys the thing on a personal card anyway. This post is about making "
          "the ask small enough to answer at a set of traffic lights, and loud enough that "
          "silence is not an option."),
 "tags": ["purchase orders", "approvals", "Amazon SES", "escalation", "human in the loop",
          "serverless"],
 "takeaways": [
  "The approver comes from the budget line in the sheet, not from a reporting hierarchy.",
  "The message leads with the consequence: what this line has left after saying yes.",
  "Two buttons and a question box. No form, no login, nothing to open on a laptop.",
  "Approve links are single-use and expire. A forwarded email cannot approve anything.",
  "Silence escalates on a schedule -- a nudge, then a second approver, then the requester is told.",
 ],
 "blocks": [
  ("h2", "Who gets asked"),
  ("p", "The obvious answer is \"their manager\", and the obvious answer is wrong. The person "
        "who should decide is the person who owns the budget the money comes out of, and in a "
        "small business those two are often different people. The workshop lead reports to "
        "operations; the workshop consumables budget belongs to the owner. So the approver is "
        "a column in the sheet, next to the limit, and changing who approves what is an edit "
        "in a spreadsheet."),
  ("fig", ("system", {
    "outside": [
      {"title": "Budget sheet", "sub": ["line, limit, approver"], "icon": "chart"},
      {"title": "Approver", "sub": ["on a phone, usually"], "icon": "person"},
      {"title": "Requester", "sub": ["kept in the loop"], "icon": "team"}],
    "inside": [
      {"title": "Message builder", "sub": ["one screen,", "one number that matters"],
       "icon": "doc"},
      {"title": "Send and sign", "sub": ["single-use links,", "SES out"], "icon": "email"},
      {"title": "Escalator", "sub": ["nudge, second approver,", "tell the requester"],
       "icon": "clock"}],
    "edges": [{"from": 0, "to": 0, "label": "who owns this line"},
              {"from": 1, "to": 1, "label": "approve or decline", "up": True},
              {"from": 2, "to": 2, "label": "status, either way", "up": True}],
    "note": "Nothing here needs a login, an app, or a laptop -- which is the entire point."}),
   "Getting the decision to the person who owns the money. The sheet says who that is, the "
   "message builder makes the ask answerable on a phone, and the escalator makes sure silence "
   "does not become a decision by default.",
   "How an approval request reaches the person who owns the budget",
   "Three boxes across the top, outside the AWS account. The Budget sheet, which carries the "
   "budget line, its limit and the name of the person who approves against it. The Approver, "
   "who is usually reading on a phone. And the Requester, who is kept in the loop either way. "
   "Inside the AWS account, three components. The Message builder, which composes one screen "
   "with one number that matters. Send and sign, which mints single-use links and sends through "
   "Amazon SES. And the Escalator, which nudges, then tries a second approver, then tells the "
   "requester. Arrows show the sheet feeding in to say who owns the line, the approver sending "
   "back an approve or decline, and the requester receiving status either way. A note says "
   "nothing here needs a login, an app or a laptop, which is the entire point."),
  ("h2", "What the message says"),
  ("p", "Most approval emails are a summary of the request. This one is a summary of the "
        "consequence. The difference is one line, and it is the difference between a decision "
        "and a guess."),
  ("callout", "The whole message, in order", [
   "<strong>Line one.</strong> Who wants what, for how much. \"Dana wants a replacement bench "
   "grinder from Medline, $640.\"",
   "<strong>Line two.</strong> The number that decides it. \"Workshop consumables has $1,150 "
   "left this quarter. This would leave $510.\"",
   "<strong>Line three.</strong> Anything unusual, or nothing. \"Medline: 6 orders this year, "
   "all fine.\" Or: \"New vendor -- approving this adds them to the list.\"",
   "<strong>Two buttons.</strong> Approve. Decline. Both single-use, both expiring in 72 hours.",
   "<strong>One box.</strong> \"Ask Dana something\" -- a reply that goes back to the requester "
   "and keeps the request open.",
   "<strong>The attachment,</strong> if there was one. The quote PDF, the screenshot of the "
   "cart. One tap, no download.",
  ]),
  ("p", "That is the whole message. There is no line-item table, no request id in the subject, "
        "no \"click here to view in the portal\". A portal is a place you have to go; this has "
        "to work in the ninety seconds somebody has between two other things."),
  ("h2", "Why the links are single-use"),
  ("p", "The approve button is a URL, which means it is a bearer token, which means anybody "
        "holding it can spend money. Three rules keep that honest, and none of them requires "
        "the approver to log in to anything."),
  ("ul", [
   "<strong>Signed and scoped.</strong> The link carries the request id and an HMAC over it, "
   "signed with a key from Secrets Manager. It is valid for that one request and nothing else. "
   "A tampered id fails the signature and is discarded without a database read.",
   "<strong>Single-use.</strong> The first click writes the decision with a condition that the "
   "request is still pending. A second click -- a forwarded email, a double tap, a link "
   "preview fetching the URL -- finds it already decided and shows the decision instead of "
   "making a new one.",
   "<strong>Short-lived.</strong> 72 hours. After that the link is dead and the request has "
   "escalated anyway. An approval link found in an old inbox in six months is worth nothing.",
  ]),
  ("p", "It is worth being blunt about the trade-off: a signed link in an email is weaker than "
        "a login. What it buys is that the decision actually gets made, on a phone, in a minute, "
        "instead of waiting for somebody to be at a desk. For purchase amounts in the hundreds "
        "against a budget line with a hard ceiling, that trade is a good one. For amounts where "
        "it is not, the sheet has a second threshold above which the link only opens a page that "
        "requires a real sign-in."),
  ("h2", "What happens when nobody answers"),
  ("p", "Silence is the failure mode that matters, because silence looks exactly like a system "
        "that is working. So an unanswered request is a scheduled event, not a row that ages."),
  ("fig", ("chain", {
    "steps": [
      {"title": "Sent, waiting", "sub": ["timer set for 24h"], "icon": "clock"},
      {"title": "Still waiting?", "sub": ["at 24 hours"], "icon": "branch",
       "exit": {"title": "Nudge the approver", "sub": ["same message, shorter"], "icon": "bell",
                "label": "yes"}},
      {"title": "Still waiting?", "sub": ["at 48 hours"], "icon": "branch",
       "side": {"title": "Second approver", "sub": ["from the sheet"], "icon": "team"},
       "exit": {"title": "Ask them instead", "sub": ["first one CC'd"], "icon": "email",
                "label": "yes"}},
      {"title": "Still waiting?", "sub": ["at 72 hours"], "icon": "branch",
       "exit": {"title": "Tell the requester", "sub": ["with who to chase"], "icon": "person",
                "label": "yes"}},
      {"title": "Decided", "sub": ["logged with who and when"], "icon": "check"}],
    "note": "A request never expires. It gets louder until a person owns it."}),
   "The escalation ladder. Twenty-four hours buys a nudge, forty-eight brings in the second "
   "approver named in the sheet, and seventy-two tells the requester who to go and find.",
   "What happens to an approval request that nobody answers",
   "A vertical chain of five steps. First, Sent and waiting, with a timer set for twenty-four "
   "hours. Second, at twenty-four hours, still waiting, which exits to Nudge the approver with "
   "the same message written shorter. Third, at forty-eight hours, still waiting, which brings "
   "in the second approver named in the budget sheet and exits to Ask them instead, with the "
   "first approver copied in. Fourth, at seventy-two hours, still waiting, which exits to Tell "
   "the requester, including who to chase. Fifth, Decided, logged with who decided and when. A "
   "note says a request never expires; it gets louder until a person owns it."),
  ("p", "Next: what actually happens the moment somebody taps approve -- the purchase order, "
        "the ledger write, and the one ordering problem that makes this harder than it looks."),
 ],
},
# ---------------------------------------------------------------- part 5 --
{
 "slug": "how-the-money-gets-committed",
 "title": "How the money gets committed",
 "nav": "How money commits",
 "read": 6, "words": 920,
 "desc": ("What happens the moment somebody taps approve: the ledger write that must come "
          "first, the purchase order that goes out second, and why doing it in the other "
          "order eventually overspends a budget."),
 "og": ("Reserve first, send second. The ledger write is conditional and comes before the "
        "purchase order, because two approvals landing in the same second must not both find "
        "room in the same budget line."),
 "abstract": ("Reserve the money, then send the order. The ledger write is a conditional "
              "update that fails rather than overspends, and the purchase order is sent from "
              "a queue so a mail failure never leaves money reserved for nothing."),
 "lede": ("Somebody taps approve. What happens in the next two seconds is the only part of "
          "this system that can lose money, and it is worth slowing down for. There are two "
          "writes -- one to your budget ledger, one to the outside world -- and the order they "
          "happen in is the difference between a budget that holds and a budget that "
          "occasionally, quietly, does not."),
 "tags": ["purchase orders", "idempotency", "DynamoDB", "conditional writes", "Amazon SQS",
          "serverless"],
 "takeaways": [
  "Reserve the money first, send the purchase order second. Never the other way round.",
  "The ledger write is conditional on the room still being there, so two approvals in the same second cannot both win.",
  "The purchase order is sent from a queue, so a mail failure retries without re-reserving.",
  "If the send permanently fails, the reservation is released and a person is told.",
  "Every commitment carries the request id, so the ledger can be replayed against the requests.",
 ],
 "blocks": [
  ("h2", "The two writes, in order"),
  ("p", "The obvious order is: send the purchase order, then update the budget. It reads "
        "naturally and it is wrong. It means there is a window -- short, but real -- where the "
        "vendor has an order and your budget does not know about it. Do that on two requests "
        "that land in the same second against a line with room for one, and you have committed "
        "twice and reserved once."),
  ("fig", ("chain", {
    "entry": {"title": "Approve tapped", "sub": ["signed, single-use"], "icon": "check"},
    "steps": [
      {"title": "Still pending?", "sub": ["conditional status write"], "icon": "branch",
       "side": {"title": "DynamoDB requests", "sub": ["status = pending"], "icon": "database"},
       "exit": {"title": "Already decided", "sub": ["show the decision"], "icon": "stop",
                "label": "second tap"}},
      {"title": "Reserve the money", "sub": ["committed += amount"], "icon": "money",
       "side": {"title": "DynamoDB ledger", "sub": ["condition: room left"], "icon": "database"},
       "exit": {"title": "No room now", "sub": ["tell both, re-ask"], "icon": "person",
                "label": "raced"}},
      {"title": "Queue the order", "sub": ["one message, one PO"], "icon": "queue"},
      {"title": "Send the order", "sub": ["SES, with the PDF"], "icon": "email",
       "exit": {"title": "Release and tell", "sub": ["after retries fail"], "icon": "stop",
                "label": "undeliverable"}},
      {"title": "Committed", "sub": ["requester and approver told"], "icon": "check"}],
    "note": "The money is reserved before the outside world hears anything, and released if it never does."}),
   "What happens between the tap and the purchase order. The money is reserved with a "
   "conditional write before the order is queued, and the reservation is released if the order "
   "can never be delivered.",
   "The sequence from approve tapped to purchase order committed",
   "A vertical chain of five steps entered by a box labelled Approve tapped, signed and "
   "single-use. Step one asks whether the request is still pending, using a conditional status "
   "write against a DynamoDB requests table; a second tap exits to Already decided, which shows "
   "the existing decision. Step two reserves the money by adding the amount to the committed "
   "column, conditional on room still being left in the DynamoDB ledger; if two approvals raced "
   "it exits to No room now, which tells both people and re-asks. Step three queues the order "
   "as exactly one message. Step four sends the order through Amazon SES with the purchase "
   "order PDF attached; if delivery permanently fails after retries it exits to Release and "
   "tell, which gives the money back. Step five is Committed, with both the requester and the "
   "approver told. A note says the money is reserved before the outside world hears anything, "
   "and released if it never does."),
  ("h3", "Why the reservation is conditional"),
  ("p", "The ledger write is not \"add 640 to committed\". It is \"add 640 to committed, but "
        "only if committed is still what I read a moment ago and the result stays under the "
        "limit\". If two approvals land against the same line at once, one of those conditions "
        "fails and one write is rejected. The rejected one does not retry blindly -- it "
        "re-reads, discovers there is no longer room, and goes back to the approver with the "
        "new numbers."),
  ("p", "This is the whole reason the budget position lives in DynamoDB rather than in the "
        "sheet. A spreadsheet cannot refuse a write on a condition. It will happily let two "
        "people set the same cell to two different values, last one wins, and the number that "
        "survives is whichever request happened to be slower."),
  ("h3", "Why the order goes out from a queue"),
  ("p", "Sending mail fails for boring reasons: a vendor's mail server is down for ten minutes, "
        "a DNS lookup times out, SES throttles. None of those should undo an approval, and none "
        "of them should cause a second reservation when the retry succeeds. So the reservation "
        "is done, and then exactly one message goes on a queue. The sender reads it, builds the "
        "PDF, sends it. If that fails, the message returns to the queue and is tried again, and "
        "the money stays reserved the entire time because it was never the sender's job to "
        "reserve it."),
  ("p", "After the retries are exhausted the message lands in a dead-letter queue, and that is "
        "the one case where the reservation is undone: the money goes back to the line, and "
        "both the requester and the approver are told the order could not be delivered, with "
        "the vendor address that failed."),
  ("h2", "What a commitment record holds"),
  ("p", "The ledger is the thing you will be reading in nine months when somebody asks why a "
        "budget line looks the way it does. It is worth it holding enough to answer that "
        "without opening anything else."),
  ("table", ["Field", "Example", "Why it is there"], [
   ["<code>line</code>", "workshop-consumables", "Which budget the money came out of"],
   ["<code>request_id</code>", "req_2026_07_08_4f1a", "Links back to the ask, the email and the attachment"],
   ["<code>amount</code>", "640.00", "What was reserved, in your currency"],
   ["<code>vendor</code>", "Medline Industries", "As matched, not as typed"],
   ["<code>approved_by</code>", "dana@ / auto", "A person's address, or the word auto"],
   ["<code>approved_at</code>", "2026-07-08T09:14:02Z", "When, to the second"],
   ["<code>basis</code>", "limit 4,000, committed 2,850", "The numbers the decision was made against"],
   ["<code>po_number</code>", "PO-2026-0412", "What the vendor sees on the order"],
   ["<code>state</code>", "committed", "committed, released, or invoiced"],
  ]),
  ("p", "The <code>basis</code> field is the unusual one and the most useful. It records what "
        "the budget looked like at the moment of the decision, not what it looks like now. Six "
        "months later, when the line is over and somebody is working out how, the ledger can "
        "say exactly which approval was the one that should not have been made -- and it will "
        "usually turn out that every single one was reasonable given what was known at the "
        "time, which is a much more useful finding than a total."),
  ("h2", "Committed, then invoiced"),
  ("p", "A commitment is not a payment. When the invoice arrives -- which this system does not "
        "handle, because your accounting software already does -- somebody marks the "
        "commitment invoiced, and the ledger row moves state. Until then the money is reserved: "
        "not spendable by the next request, not yet paid, and visible as such."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Asked", "sub": ["request recorded"], "icon": "form"},
      {"title": "Approved", "sub": ["by a person or the line"], "icon": "check"},
      {"title": "Committed", "sub": ["money reserved"], "icon": "money"},
      {"title": "Ordered", "sub": ["PO with the vendor"], "icon": "truck"},
      {"title": "Invoiced", "sub": ["handed to accounts"], "icon": "doc"}],
    "title": "THE FIVE STATES OF ONE PURCHASE",
    "note": "This system owns the first four. The fifth belongs to your accounting software."}),
   "The five states a purchase moves through, and where this system's responsibility ends. It "
   "reserves and orders; it does not pay, and it does not try to.",
   "The five states of a purchase, from asked to invoiced",
   "A horizontal row of five boxes. Asked: the request is recorded. Approved: either by a "
   "person or automatically under the line. Committed: the money is reserved in the ledger. "
   "Ordered: the purchase order is with the vendor. Invoiced: the record is handed to "
   "accounts. A note says this system owns the first four states and the fifth belongs to the "
   "existing accounting software."),
  ("p", "Next: what all of this costs to run."),
 ],
},
# ---------------------------------------------------------------- part 6 --
{
 "slug": "what-the-purchase-order-approver-costs",
 "title": "What the purchase order approver costs",
 "nav": "What it costs",
 "read": 5, "words": 820,
 "desc": ("About $3 a month at small-business volume. Where every cent goes, which line "
          "grows with volume, and the three ways this bill could surprise you."),
 "og": ("One model read per request is the whole bill. Everything else -- the queue, the "
        "table, the mail, the storage -- rounds to nothing at small-business volume."),
 "abstract": ("A few dollars a month. One Bedrock read per request is the only line that "
              "grows; the queue, the table, the mail and the storage are rounding errors. "
              "Plus the three ways the bill could surprise you."),
 "lede": ("There is nothing always-on in this design, which is most of the answer. No server, "
          "no container waiting for traffic, no managed database with an hourly rate. You pay "
          "per request, and a small business does not make many purchase requests. Here is "
          "where each cent actually goes, and what happens to the bill when the business "
          "doubles."),
 "tags": ["AWS cost", "serverless pricing", "AWS Bedrock", "Lambda", "DynamoDB", "small business"],
 "takeaways": [
  "About $3 a month at 200 purchase requests. Roughly $9 at 1,000.",
  "One Bedrock read per request is the only line that scales. Everything else is rounding.",
  "Nothing is always-on, so a quiet month genuinely costs almost nothing.",
  "The duplicate test runs before the read, so resends are free.",
  "The three real risks: a retry loop, an attachment nobody expires, and a model that got swapped for a bigger one.",
 ],
 "blocks": [
  ("h2", "The bill at three volumes"),
  ("p", "These are US East prices at the time of writing, at three volumes that bracket most "
        "small businesses. A twenty-person firm that buys things properly runs somewhere near "
        "the middle bar."),
  ("fig", ("bars", {
    "tiers": [
      {"label": "80 requests", "parts": [("read", 0.62), ("mail", 0.12), ("store", 0.28),
                                          ("fixed", 0.86), ("other", 0.16)]},
      {"label": "200 requests", "parts": [("read", 1.55), ("mail", 0.30), ("store", 0.31),
                                           ("fixed", 0.86), ("other", 0.28)]},
      {"label": "1,000 requests", "parts": [("read", 7.75), ("mail", 1.50), ("store", 0.44),
                                             ("fixed", 0.86), ("other", 0.95)]}],
    "series": [("read", "Bedrock -- one read per request", "#01A88D"),
               ("mail", "SES -- asks, orders, receipts", "#E7157B"),
               ("store", "S3 + DynamoDB", "#7AA116"),
               ("fixed", "Fixed -- Secrets Manager, Budgets", "#FF9900"),
               ("other", "Lambda, SQS, CloudWatch", "#7D8CA3")],
    "note": "The read is the only bar that grows with the business. The orange band never moves."}),
   "The monthly bill at three volumes. The teal band -- one model read per request -- is the "
   "only part that grows; the orange fixed band is the same 86 cents whether you make eighty "
   "requests or a thousand.",
   "Monthly cost of the purchase order approver at three request volumes",
   "A stacked bar chart with three bars. The left bar represents eighty purchase requests a "
   "month and totals about one dollar ninety. The middle bar represents two hundred requests "
   "and totals about three dollars thirty. The right bar represents one thousand requests and "
   "totals about eleven dollars fifty. Each bar is stacked from five bands. The largest and "
   "fastest-growing is Bedrock, one read per request, shown in teal. Below it, SES for the "
   "asks, orders and receipts, in pink. Then S3 and DynamoDB storage in green. Then a fixed "
   "band in orange for Secrets Manager and AWS Budgets, which is eighty-six cents at every "
   "volume. Then a grey band for Lambda, SQS and CloudWatch. A note says the read is the only "
   "bar that grows with the business and the orange band never moves."),
  ("h2", "Line by line"),
  ("table", ["Line", "At 200 requests", "How it scales"], [
   ["Bedrock read", "$1.55", "Linear. One call per request, roughly 1,800 in and 200 out tokens."],
   ["SES", "$0.30", "Linear. About three messages per request: ask, order, receipt."],
   ["DynamoDB", "$0.19", "Linear, on-demand. A handful of writes and reads per request."],
   ["S3", "$0.12", "Grows with retained attachments, not with request rate."],
   ["Lambda", "$0.08", "Linear. Six short invocations per request, all well inside 512&nbsp;MB."],
   ["SQS", "$0.04", "Linear, and effectively free below a million messages."],
   ["CloudWatch", "$0.16", "Flat, if you set retention. Unbounded if you do not."],
   ["Secrets Manager", "$0.40", "Flat. One secret, $0.40 a month."],
   ["AWS Budgets", "$0.46", "Flat. Two budget actions, so you find out before the bill does."],
  ]),
  ("p", "The Bedrock line assumes one read per request against a small, fast model -- the "
        "cheapest one that can reliably turn a sentence into five fields, which is not a "
        "frontier model. Part 7 names the exact model id. Swapping it for something larger is "
        "the single fastest way to multiply this bill by ten for no measurable gain, because "
        "the task is extraction, not reasoning."),
  ("h2", "The three ways this bill surprises you"),
  ("p", "Every one of these has happened to somebody, and all three are cheap to prevent."),
  ("ul", [
   "<strong>A retry loop on the read.</strong> A malformed attachment makes the read throw, "
   "the function retries, the retry throws, and the queue redelivers. At three retries and no "
   "dead-letter queue that is one bad email costing you the same as a hundred good ones, every "
   "few minutes, until somebody notices. The fix is the dead-letter queue in Part 5 and a "
   "maximum receive count of three.",
   "<strong>Attachments nobody expires.</strong> Quote PDFs are small, and small times forever "
   "is not small. An S3 lifecycle rule that moves objects to Infrequent Access at 90 days and "
   "expires them at seven years -- or whatever your record-keeping obligation actually is -- "
   "keeps the storage line flat.",
   "<strong>Log retention left at never.</strong> CloudWatch defaults to keeping log groups "
   "forever. On a system this small the logs will eventually cost more than the compute. "
   "Thirty days of retention on every log group is a one-line change and the single highest-"
   "return cost setting in the whole design.",
  ]),
  ("h2", "What it costs when nothing happens"),
  ("p", "This matters more than the headline number for a seasonal business. In a month with "
        "zero purchase requests, the bill is the fixed band: Secrets Manager at forty cents, "
        "AWS Budgets at forty-six, and a few cents of storage. Call it a dollar. There is no "
        "instance to stop, no cluster to scale down, and nothing to remember to turn off."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Quiet month", "sub": ["~$1"], "icon": "clock"},
      {"title": "80 requests", "sub": ["~$2"], "icon": "form"},
      {"title": "200 requests", "sub": ["~$3"], "icon": "money"},
      {"title": "1,000 requests", "sub": ["~$12"], "icon": "counter"},
      {"title": "One bad loop", "sub": ["~$200"], "icon": "alarm"}],
    "title": "THE BILL, AT A GLANCE",
    "note": "Four of these are the design working. The fifth is a missing dead-letter queue."}),
   "The bill at a glance, including the one that is not a volume at all. A retry loop with no "
   "dead-letter queue costs more than every legitimate use of the system put together.",
   "The monthly bill at four request volumes plus one failure mode",
   "A horizontal row of five boxes. Quiet month, about one dollar. Eighty requests, about two "
   "dollars. Two hundred requests, about three dollars. One thousand requests, about twelve "
   "dollars. And one bad retry loop, about two hundred dollars. A note says four of these are "
   "the design working and the fifth is a missing dead-letter queue."),
  ("callout", "Set these on day one", [
   "A dead-letter queue on every SQS queue, with a maximum receive count of three.",
   "Thirty-day retention on every CloudWatch log group. There is no default that is safe.",
   "An S3 lifecycle rule on the attachment prefix, tiering at 90 days and expiring at your "
   "actual record-keeping horizon.",
   "Two AWS Budgets actions -- one that emails at half your expected spend, one that emails at "
   "double it. The second one is how you find out about a loop in an hour instead of a month.",
   "Provisioned concurrency: none. Nothing here is latency-sensitive enough to justify paying "
   "for a warm function.",
  ]),
  ("p", "Next: the same system drawn for engineers -- service names, resource identifiers, IAM "
        "scopes, table schemas and the model id."),
 ],
},
# ---------------------------------------------------------------- part 7 --
{
 "slug": "purchase-order-approver-engineering-reference",
 "title": "Engineering reference: the purchase order approver architecture",
 "nav": "Engineering reference",
 "read": 7, "words": 1050,
 "desc": ("The same system drawn for engineers: service names, region, the Lambda inventory, "
          "IAM scopes, DynamoDB schemas, the SES receipt rule set and the Bedrock model id."),
 "og": ("Service names, resource identifiers, table schemas, IAM scopes and the model id -- "
        "the purchase order approver as an engineer would need it to rebuild it."),
 "abstract": ("Same system, drawn purely for engineers. Service names, region, Lambda "
              "inventory, IAM scopes, the SES inbound rule set, the two DynamoDB schemas and "
              "the exact model id."),
 "lede": ("The first six posts are for the person deciding whether to build this. This one is "
          "for the person building it. Same system, no analogies: the services by name, the "
          "functions and what each is allowed to touch, the two tables and their keys, the "
          "inbound mail path, and the specific model. Nothing here is a secret and nothing "
          "here is load-bearing on a diagram."),
 "tags": ["AWS architecture", "Lambda", "DynamoDB", "Amazon SES", "IAM", "AWS Bedrock",
          "engineering reference"],
 "takeaways": [
  "Single region, single account. Every resource is regional; nothing is global except the IAM roles.",
  "Six Lambda functions, each with its own execution role. No shared role, no wildcards on resources.",
  "Two DynamoDB tables: requests (keyed by request id) and ledger (keyed by budget line and period).",
  "Inbound mail through an SES receipt rule set writing to S3, which is what triggers intake.",
  "One Bedrock model, called once per request, with a JSON schema it must fill or leave null.",
 ],
 "blocks": [
  ("h2", "The system, by service name"),
  ("fig", ("system", {
    "outside": [
      {"title": "SES inbound", "sub": ["MX on the requests domain"], "icon": "email"},
      {"title": "Sheets API", "sub": ["budget + vendor tabs"], "icon": "chart"},
      {"title": "SES outbound", "sub": ["asks, POs, receipts"], "icon": "email"}],
    "inside": [
      {"title": "S3 + SQS", "sub": ["raw mail, attachments,", "one request queue"],
       "icon": "bucket"},
      {"title": "Lambda x6", "sub": ["intake, read, check,", "route, commit, send"],
       "icon": "lambda"},
      {"title": "DynamoDB x2", "sub": ["requests, ledger"], "icon": "database"}],
    "edges": [{"from": 0, "to": 0, "label": "receipt rule -> S3"},
              {"from": 1, "to": 1, "label": "read-only, cached 5m"},
              {"from": 2, "to": 2, "label": "SendRawEmail", "up": True}],
    "note": "us-east-1. One account. Secrets Manager holds the sheet credential and the link-signing key."}),
   "The same three-part shape as Part 1, with the service names filled in. Inbound mail lands "
   "in S3 through an SES receipt rule, six Lambda functions do the work, and two DynamoDB "
   "tables hold every piece of state.",
   "The purchase order approver drawn with AWS service names",
   "Three boxes across the top outside the AWS account. SES inbound, with an MX record on the "
   "requests domain. The Google Sheets API, serving the budget and vendor tabs. And SES "
   "outbound, which carries the approval asks, the purchase orders and the receipts. Inside the "
   "account, three groups. S3 and SQS, holding raw mail, attachments and the single request "
   "queue. Six Lambda functions named intake, read, check, route, commit and send. And two "
   "DynamoDB tables, requests and ledger. Arrows show the SES receipt rule writing into S3, the "
   "sheet being read read-only with a five-minute cache, and SendRawEmail going back out. A "
   "note gives the region as us-east-1, one account, with Secrets Manager holding the sheet "
   "credential and the link-signing key."),
  ("h2", "Region and account"),
  ("ul", [
   "<strong>Region:</strong> <code>us-east-1</code>. Chosen because SES inbound receipt rules "
   "are only available in a subset of regions and this is the one with the widest Bedrock model "
   "availability. If your data has to stay elsewhere, check both constraints before moving: "
   "inbound SES is the binding one.",
   "<strong>Account:</strong> one. This is a small system and a separate account per "
   "environment costs more in wiring than it saves. A <code>dev</code> and a <code>prod</code> "
   "stack in the same account, with distinct resource prefixes, is the right size here.",
   "<strong>Everything is regional.</strong> The only global resources are the IAM roles and "
   "policies. There is no CloudFront, no global table and no cross-region replication, because "
   "nothing here has a latency or a durability requirement that would justify them.",
  ]),
  ("h2", "Lambda inventory"),
  ("table", ["Function", "Trigger", "Does", "Timeout / memory"], [
   ["<code>po-intake</code>", "S3 ObjectCreated + API Gateway + Slack",
    "Normalises all three lanes into one queue message", "10s / 512&nbsp;MB"],
   ["<code>po-read</code>", "SQS request queue",
    "Duplicate test, then one Bedrock call into the five fields", "30s / 1024&nbsp;MB"],
   ["<code>po-check</code>", "SQS checked queue",
    "The four budget checks against the sheet and the ledger", "10s / 512&nbsp;MB"],
   ["<code>po-route</code>", "SQS routed queue",
    "Auto-approve, ask a person, or return to the requester", "10s / 512&nbsp;MB"],
   ["<code>po-decide</code>", "Function URL",
    "Handles the signed approve/decline links; reserves the money", "10s / 512&nbsp;MB"],
   ["<code>po-send</code>", "SQS order queue",
    "Builds the PO PDF and sends it through SES", "30s / 1024&nbsp;MB"],
  ]),
  ("p", "Six functions rather than one is a deliberate choice, and the reason is not "
        "modularity. It is that <code>po-read</code> is the only one that needs Bedrock "
        "permissions and <code>po-decide</code> is the only one reachable from the public "
        "internet. Splitting them means the internet-facing function cannot call a model and "
        "the model-calling function cannot be reached from the internet, and neither of those "
        "is true if it is all one handler behind a router."),
  ("h2", "IAM, scoped"),
  ("table", ["Role", "Allowed", "On"], [
   ["<code>po-intake-role</code>", "<code>s3:GetObject</code>, <code>sqs:SendMessage</code>",
    "The mail prefix; the request queue only"],
   ["<code>po-read-role</code>",
    "<code>bedrock:InvokeModel</code>, <code>dynamodb:PutItem</code>, <code>sqs:*Message</code>",
    "One model arn; requests table; two queues"],
   ["<code>po-check-role</code>",
    "<code>dynamodb:GetItem</code>, <code>secretsmanager:GetSecretValue</code>",
    "Ledger table; the sheet credential only"],
   ["<code>po-route-role</code>", "<code>ses:SendEmail</code>, <code>sqs:SendMessage</code>",
    "One verified identity; the order queue"],
   ["<code>po-decide-role</code>",
    "<code>dynamodb:UpdateItem</code>, <code>secretsmanager:GetSecretValue</code>",
    "Requests and ledger; the signing key only"],
   ["<code>po-send-role</code>", "<code>ses:SendRawEmail</code>, <code>s3:GetObject</code>",
    "One identity; the attachment prefix"],
  ]),
  ("p", "No role has a <code>Resource: \"*\"</code> on anything that writes. The two "
        "<code>GetSecretValue</code> grants name a single secret arn each, which is why there "
        "are two secrets rather than one JSON blob with both values in it: a single secret "
        "would mean the checker could read the link-signing key, and it has no business "
        "knowing it."),
  ("h2", "DynamoDB schemas"),
  ("h3", "Table: requests"),
  ("pre", "PK   request_id        S   req_2026_07_08_4f1a\n"
          "     status            S   pending | approved | declined | returned\n"
          "     fingerprint       S   sha256(requester|vendor|amount|day)\n"
          "     requester         S   dana@example.com\n"
          "     item              S   Replacement bench grinder\n"
          "     line              S   workshop-consumables\n"
          "     amount            N   640.00\n"
          "     vendor            S   Medline Industries\n"
          "     raw_key           S   s3://po-mail/2026/07/08/4f1a.eml\n"
          "     decided_by        S   owner@example.com | auto\n"
          "     decided_at        S   2026-07-08T09:14:02Z\n"
          "     ttl               N   epoch, +7 years\n\n"
          "GSI  fingerprint-index   PK fingerprint    -- the duplicate test\n"
          "GSI  status-index        PK status, SK created_at  -- the escalator's sweep"),
  ("h3", "Table: ledger"),
  ("pre", "PK   line              S   workshop-consumables\n"
          "SK   period            S   2026-Q3\n"
          "     limit             N   4000.00\n"
          "     committed         N   2850.00\n"
          "     invoiced          N   1900.00\n"
          "     approver          S   owner@example.com\n"
          "     second_approver   S   ops@example.com\n"
          "     auto_below        N   250.00\n"
          "     updated_at        S   2026-07-08T09:14:02Z\n\n"
          "The reservation write:\n"
          "  UpdateExpression:    SET committed = committed + :amt\n"
          "  ConditionExpression: committed = :seen AND committed + :amt <= #limit"),
  ("p", "That condition expression is the entire concurrency story. Two approvals racing "
        "against the same line cannot both satisfy <code>committed = :seen</code>, so exactly "
        "one wins and the other is rejected with "
        "<code>ConditionalCheckFailedException</code>, which the caller turns into the "
        "\"no room now\" path from Part 5 rather than into a retry."),
  ("h2", "Inbound mail"),
  ("ul", [
   "An SES <strong>receipt rule set</strong> on the requests domain, with one rule: recipient "
   "<code>buy@</code>, actions <code>S3</code> then <code>Stop</code>.",
   "The S3 action writes to <code>po-mail/</code> with a KMS key, which is what fires "
   "<code>po-intake</code>. There is no SNS hop; the object creation event is enough.",
   "<strong>Spam and virus verdicts</strong> are on the SES headers written into the object. "
   "<code>po-intake</code> reads them and drops anything failing either, before any parsing.",
   "<strong>SPF and DKIM</strong> on the outbound identity, plus a DMARC record. Purchase "
   "orders that fail authentication get filed as junk by the vendor, which looks exactly like "
   "the system not working.",
  ]),
  ("h2", "The model call"),
  ("ul", [
   "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock. "
   "The task is extraction from a short email, which is what a small fast model is for.",
   "<strong>Called once</strong> per request, after the duplicate test, never in a loop and "
   "never for a retry that has already read the same message.",
   "<strong>Output is a JSON schema</strong> with five fields, every one nullable. Null is a "
   "first-class answer and is what produces the \"which budget line?\" reply rather than a "
   "guess.",
   "<strong>Grounded</strong> with the budget line names and the vendor list in the prompt, "
   "read from the sheet through a five-minute cache. The model picks from a list; it does not "
   "invent a line.",
   "<strong>No tools, no chaining.</strong> One call in, one JSON out. Everything "
   "consequential after that point is code.",
  ]),
  ("callout", "Things worth knowing before you build it", [
   "SES inbound receipt rules exist in only a few regions. Pick the region for that constraint "
   "first, then check Bedrock model availability in it.",
   "A new SES identity is in the sandbox. Purchase orders to a real vendor need production "
   "access, which is a support request and takes a day or two.",
   "Function URLs are public by default. <code>po-decide</code> must do its own HMAC check on "
   "the first line of the handler, before any parsing and before any database read.",
   "DynamoDB on-demand is the right mode here and provisioned is not. The traffic is bursty, "
   "tiny, and completely unpredictable.",
   "Set the ledger period key to whatever your budget period actually is. Quarters are the "
   "common case; a business running annual budgets should not be pretending otherwise in a "
   "sort key.",
  ]),
  ("p", "That is the whole system. Seven posts, one diagram at a time, and nothing in it that "
        "needs a server."),
 ],
},
]
