"""Day 81 -- 2026-07-14 -- Invoice dispute triager."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "invoice-dispute-triager"
NAME = "Invoice dispute triager"

SPEC = {
 "slug": SLUG, "date": "2026-07-14", "name": NAME,
 "tagline": ("When a customer says an invoice is wrong, the system works out which of the six "
             "things they usually mean, gathers the evidence for that one, and hands a person "
             "a decision instead of a thread."),
 "lede": ("A small system that reads incoming disputes about invoices, classifies each into "
          "one of a small fixed set of reasons, pulls together the specific evidence that "
          "reason needs, and puts a decision in front of a human with everything already "
          "attached. It never issues a credit note and never argues with anybody. Seven posts "
          "on the same system -- one diagram at a time -- with a cost breakdown and an "
          "engineering reference at the end."),
 "keywords": ["invoice disputes", "accounts receivable", "credit notes", "customer service",
              "human in the loop", "serverless"],
 "icons": ["email", "search", "money"],
 "faq": [
  ("What is an invoice dispute triager?",
   "A small serverless system that reads emails and portal messages saying an invoice is "
   "wrong, works out which of a handful of standard reasons is being claimed, gathers the "
   "records that bear on that reason, and hands a person a decision with the evidence "
   "attached. It never issues a credit note by itself."),
  ("Why classify rather than just forward?",
   "Because the evidence needed is completely different per reason. A quantity dispute needs "
   "the delivery note; a price dispute needs the quote; a duplicate claim needs the payment "
   "history. Classifying first means the evidence is already gathered when a person opens it, "
   "which is the difference between a two-minute decision and a two-day thread."),
  ("Does it pause the invoice?",
   "It flags it as disputed and stops any automatic chasing, which matters -- nothing damages "
   "a customer relationship faster than a dunning reminder sent while a genuine dispute is "
   "open. It does not change the amount owed; only a person does that."),
  ("What if the dispute is not really about the invoice?",
   "That is common and it is one of the classifications. \"We are unhappy with the work\" is "
   "not an invoice error, and routing it to accounts is how it becomes one. It goes to whoever "
   "owns the relationship instead."),
  ("What does it cost to run?",
   "A few dollars a month. Dispute volume is low even in businesses that feel like they have a "
   "lot of them. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "invoice-dispute-triager-on-aws",
 "title": "An invoice dispute triager on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 920,
 "desc": ("Classifies each dispute into one of six standard reasons, gathers the evidence that "
          "reason needs, pauses chasing, and hands a person a decision. AWS, about $3 a month."),
 "og": ("Six standard reasons, and each needs different evidence. Classifying first means the "
        "delivery note or the quote is already attached when a person opens the dispute."),
 "abstract": ("The whole system on one page -- a classifier, a gatherer and a router -- plus "
              "the thing that makes it worth building: the evidence is assembled before a "
              "human is involved."),
 "lede": ("A customer says an invoice is wrong. What happens next in most small businesses is a "
          "thread: somebody in accounts asks what specifically is wrong, the customer replies "
          "three days later, accounts asks operations for the delivery note, operations finds "
          "it a day later, accounts replies, and eleven days after the original email an "
          "invoice that was correct all along gets paid. Meanwhile the automated reminder has "
          "gone out twice. This post walks through a small system that does the gathering "
          "first."),
 "tags": ["invoice disputes", "accounts receivable", "customer service", "credit control",
          "human in the loop", "serverless"],
 "takeaways": [
  "Six standard reasons cover almost every dispute, and each needs different evidence.",
  "The evidence is gathered before a human opens it, not after.",
  "A dispute pauses automatic chasing immediately. Nothing sours a customer faster.",
  "Not every dispute is about the invoice. \"Unhappy with the work\" goes to the relationship owner.",
  "Designed on AWS for about $3 a month at typical small-business volume.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Customer message", "sub": ["email or portal"], "icon": "email"},
      {"title": "Your records", "sub": ["invoices, notes, quotes"], "icon": "doc"},
      {"title": "Whoever decides", "sub": ["accounts or the owner"], "icon": "person"}],
    "inside": [
      {"title": "Classifier", "sub": ["which of six", "reasons is claimed"], "icon": "model"},
      {"title": "Gatherer", "sub": ["the evidence that", "reason needs"], "icon": "search"},
      {"title": "Router", "sub": ["pause chasing,", "hand over a decision"], "icon": "filter"}],
    "edges": [{"from": 0, "to": 0, "label": "disputes in"},
              {"from": 1, "to": 1, "label": "the evidence"},
              {"from": 2, "to": 2, "label": "one decision, ready", "up": True}],
    "note": "No credit note is ever issued by the system. It assembles; a person decides."}),
   "Three things outside the account, three pieces inside it. A dispute arrives, the classifier "
   "works out what is being claimed, the gatherer fetches exactly the records that claim needs, "
   "and a person gets a decision rather than a thread.",
   "System: a dispute in, evidence gathered, a decision out",
   "Three boxes across the top sit outside the AWS account. On the left, Customer message: a "
   "dispute arriving by email or through a portal. In the middle, Your records: the invoices, "
   "delivery notes, quotes and payment history the business already holds. On the right, "
   "Whoever decides: accounts, or the owner of the relationship. Each connects by an arrow to "
   "the AWS account container below. Disputes flow down into the account. The records feed in "
   "as evidence. A ready-made decision goes back out. Inside the AWS account are three "
   "components in a row. On the left, the Classifier, which works out which of six standard "
   "reasons is being claimed. In the middle, the Gatherer, which fetches exactly the evidence "
   "that reason needs. On the right, the Router, which pauses automatic chasing and hands over "
   "a decision. A note at the bottom says no credit note is ever issued by the system; it "
   "assembles and a person decides."),
  ("h3", "The six reasons"),
  ("table", ["Reason", "What the customer means", "What it needs"], [
   ["Quantity", "We did not receive that many", "The delivery note, signed"],
   ["Price", "That is not what we agreed", "The quote or the price list on that date"],
   ["Duplicate", "We have already paid this", "The payment history and the other invoice"],
   ["Never ordered", "We did not order this at all", "The purchase order or the job record"],
   ["Wrong entity", "This should go to our other company", "The account setup and the contract"],
   ["Not the invoice", "We are unhappy with the work", "Nothing &mdash; it goes to a person, not accounts"],
  ]),
  ("p", "Those six cover the overwhelming majority of disputes in a small business, and the "
        "important property of the list is that the evidence column is completely different for "
        "each. That is the whole reason classifying is worth doing: it turns \"find out what "
        "they mean, then find the relevant paperwork\" into one automatic step."),
  ("h3", "What runs on every dispute (the inside)"),
  ("ul", [
   "<strong>The classifier.</strong> Reads the message and picks one of the six, or says it "
   "cannot tell. This is the one place a model earns its keep &mdash; customers do not write "
   "\"I am raising a quantity dispute\", they write \"only 6 of the 10 turned up\". It also "
   "extracts the invoice number, which is usually in the message and occasionally is not.",
   "<strong>The gatherer.</strong> Fetches exactly what the reason needs. For quantity, the "
   "delivery note and the picking record. For price, the quote and the price list as it stood "
   "on the invoice date. For duplicate, every payment against that customer in the period plus "
   "any invoice with a similar total. Nothing else, because a decision buried in twelve "
   "attachments is not a decision.",
   "<strong>The router.</strong> Flags the invoice as disputed so the chaser stops, and sends "
   "the assembled decision to the right person. Five of the six go to accounts. The sixth "
   "&mdash; the one that is not really about the invoice &mdash; goes to whoever owns the "
   "relationship, which is the single most valuable routing decision the system makes.",
  ]),
  ("h2", "One dispute, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Received", "sub": ["a customer email"], "icon": "email"},
      {"title": "Classified", "sub": ["one of six reasons"], "icon": "model"},
      {"title": "Paused", "sub": ["chasing stops now"], "icon": "stop"},
      {"title": "Gathered", "sub": ["just the right evidence"], "icon": "search"},
      {"title": "Decided", "sub": ["by a person, quickly"], "icon": "person"}],
    "title": "ONE DISPUTE, END TO END",
    "note": "The third stage happens within seconds and prevents most of the damage."}),
   "The same system as one line. Pausing the chaser is third rather than last on purpose: it is "
   "the step that has to happen immediately, before anything is understood.",
   "One invoice dispute from arrival to decision, in five stages",
   "A horizontal row of five boxes joined by arrows. Received: a customer email arrives. "
   "Classified: matched to one of six reasons. Paused: automatic chasing stops immediately. "
   "Gathered: exactly the evidence that reason needs is assembled. Decided: a person makes the "
   "call quickly. A note says the third stage happens within seconds and prevents most of the "
   "damage."),
  ("h2", "In plain words"),
  ("p", "A customer emails: \"Invoice 4412 &mdash; we only got 6 of the pallets, not 10.\" The "
        "classifier reads that as a quantity dispute on invoice 4412. Within seconds the "
        "invoice is flagged disputed, so the reminder scheduled for Friday does not go. The "
        "gatherer pulls the delivery note for that invoice, which is signed, and the picking "
        "record, which says 10 pallets loaded on two vehicles. It attaches both, plus the "
        "photograph of the signed POD, and sends one message to accounts: quantity dispute, "
        "invoice 4412, POD signed for 10, second vehicle delivered 14:20."),
  ("p", "Somebody in accounts opens that, sees a signed delivery note for ten, and replies to "
        "the customer with the POD attached in under two minutes. Nine times out of ten the "
        "reply comes back \"ah, the second load came separately, sorry\", and the invoice is "
        "paid. The tenth time it turns out the second vehicle went to the wrong site, which is "
        "an operational problem the business genuinely needed to know about &mdash; and it now "
        "knows about it on the same day rather than in eleven."),
  ("callout", "Design rules that shaped every decision", [
   "Pause the chaser first, understand second. A dunning reminder during a genuine dispute does "
   "more damage than any invoice error.",
   "Gather narrowly. The evidence for the claimed reason and nothing else; twelve attachments "
   "is not a decision.",
   "The system never issues a credit note, never adjusts an amount, and never replies to the "
   "customer on its own.",
   "\"Not about the invoice\" is a first-class classification, and routing it away from accounts "
   "is the highest-value thing the system does.",
   "An unclassifiable dispute goes to a person with the raw message. Guessing a reason gathers "
   "the wrong evidence, which is worse than gathering none.",
   "Every decision is recorded against the customer, because the same dispute reason recurring "
   "is a process problem rather than a customer problem.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Disputes are expensive out of all proportion to their number. A business raising four "
        "hundred invoices a month might see fifteen disputes, and those fifteen will consume "
        "more accounts time than the other three hundred and eighty-five combined &mdash; not "
        "because they are hard, but because each one is a multi-day thread with waiting in it. "
        "The waiting is the cost, and almost all of it is waiting for information that already "
        "exists somewhere in the business."),
  ("p", "So the design front-loads the gathering. It accepts that a model will occasionally "
        "classify wrongly, which costs one round trip, in exchange for the far larger saving of "
        "having the right paperwork attached the first time in the other ninety per cent. And "
        "it does the one thing that has to be instant &mdash; stopping the chaser &mdash; "
        "before it tries to understand anything."),
  ("p", "The next four posts walk through each piece: how a dispute is recognised, how it gets "
        "classified, how the evidence is gathered, and how a decision gets recorded. One "
        "diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-dispute-gets-recognised",
 "title": "How a dispute gets recognised",
 "nav": "How it is recognised",
 "read": 5, "words": 840,
 "desc": ("Telling a dispute apart from a question, a payment remittance and an out-of-office "
          "-- and why stopping the chaser happens before anything is understood."),
 "og": ("Most mail to an accounts inbox is not a dispute. Recognising one -- and stopping the "
        "chaser within seconds of doing so -- comes before any classification."),
 "abstract": ("Telling a dispute apart from a question, a remittance and an auto-reply, "
              "finding the invoice number, and stopping the chaser before anything else "
              "happens."),
 "lede": ("An accounts inbox is mostly not disputes. It is remittance advices, out-of-office "
          "replies, requests for a copy invoice, and people asking when something is due. "
          "Treating all of it as a dispute would pause half your ledger; treating none of it as "
          "a dispute is the current situation. This post is about the line between them, and "
          "about the one action that has to happen the instant the line is crossed."),
 "tags": ["invoice disputes", "email triage", "SES inbound", "dunning", "accounts receivable",
          "serverless"],
 "takeaways": [
  "Most accounts mail is not a dispute. The first job is telling them apart.",
  "The chaser is paused the moment a message is judged a dispute, before it is classified.",
  "The invoice number is found in the body, the subject, the thread, or by asking.",
  "A remittance or an auto-reply is recognised and ignored without a model call.",
  "A dispute on a paid invoice is a different and more urgent thing.",
 ],
 "blocks": [
  ("h2", "What arrives at an accounts inbox"),
  ("fig", ("chain", {
    "entry": {"title": "Message arrives", "sub": ["accounts inbox"], "icon": "inbox"},
    "steps": [
      {"title": "Auto-reply?", "sub": ["headers, not wording"], "icon": "branch",
       "exit": {"title": "Ignore", "sub": ["no model call"], "icon": "stop", "label": "yes"}},
      {"title": "Remittance?", "sub": ["amounts and refs only"], "icon": "branch",
       "exit": {"title": "File it", "sub": ["match to payments"], "icon": "money",
                "label": "yes"}},
      {"title": "About an invoice?", "sub": ["a number, or a thread"], "icon": "branch",
       "side": {"title": "Invoice records", "sub": ["numbers and totals"], "icon": "database"},
       "exit": {"title": "General enquiry", "sub": ["to the inbox owner"], "icon": "person",
                "label": "no"}},
      {"title": "Is it a complaint?", "sub": ["one Bedrock call"], "icon": "model",
       "exit": {"title": "Question, not dispute", "sub": ["answer it, do not pause"],
                "icon": "chat", "label": "no"}},
      {"title": "Pause the chaser", "sub": ["immediately, before", "anything else"], "icon": "stop"},
      {"title": "Hand to the classifier", "sub": ["with the invoice"], "icon": "queue"}],
    "note": "Three of the four filters cost nothing. Only the last one calls a model."}),
   "How a dispute is separated from everything else that arrives. The cheap structural filters "
   "run first, and the chaser is stopped the moment the answer is yes.",
   "How an incoming message is recognised as an invoice dispute",
   "A vertical chain of six steps inside the AWS account, entered by a box labelled Message "
   "arrives at the accounts inbox. Step one asks whether it is an auto-reply, judged from mail "
   "headers rather than wording; if so it exits to Ignore with no model call. Step two asks "
   "whether it is a remittance advice, recognisable from amounts and references only; if so it "
   "exits to File it and match to payments. Step three asks whether it is about an invoice, "
   "found by a number or by the thread, checking against invoice records; if not it exits to "
   "General enquiry, sent to the inbox owner. Step four asks whether it is a complaint, using a "
   "single Bedrock call; if not it exits to Question, not dispute, which is answered without "
   "pausing anything. Step five pauses the chaser immediately, before anything else. Step six "
   "hands the message to the classifier with the invoice attached. A note says three of the "
   "four filters cost nothing and only the last one calls a model."),
  ("h3", "Why the cheap filters come first"),
  ("p", "Auto-replies are identifiable from headers with complete certainty &mdash; "
        "<code>Auto-Submitted</code>, <code>X-Autoreply</code>, a precedence of bulk. There is "
        "no reason to ask a model whether an out-of-office is a dispute, and a business with "
        "one chatty customer on annual leave can generate dozens of them."),
  ("p", "Remittance advices are nearly as easy: a message that is mostly a table of invoice "
        "numbers and amounts, with a total, and no sentences. They are frequent, they are "
        "structurally distinctive, and misclassifying one as a dispute would pause several "
        "invoices that have just been paid."),
  ("h2", "Finding the invoice"),
  ("ul", [
   "<strong>In the body.</strong> The common case. An invoice number in a recognisable format, "
   "matched against invoices for that customer &mdash; not against all invoices, because "
   "customer-scoped matching removes almost every false positive.",
   "<strong>In the subject or the thread.</strong> A reply to the original invoice email "
   "carries the number in the subject or in the quoted text. Threading by "
   "<code>In-Reply-To</code> is more reliable than any parsing.",
   "<strong>By amount.</strong> \"Your invoice for £3,240 is wrong\" identifies an invoice "
   "uniquely often enough to be worth trying, but only when exactly one invoice for that "
   "customer matches. Two candidates is not a match.",
   "<strong>By asking.</strong> If none of the above works, the dispute is still real and the "
   "chaser for that customer is paused across the board until it is resolved &mdash; which is "
   "cautious, and correct, because chasing a customer who is currently disputing something is "
   "the exact failure this system exists to prevent.",
  ]),
  ("h2", "Pausing the chaser"),
  ("p", "This happens before classification, before gathering, and before any human sees "
        "anything. It is a single conditional write setting a disputed flag on the invoice, and "
        "whatever sends your payment reminders checks that flag. If your reminders are sent by "
        "a person, the pause is a line on a list they check; if they are automated, it is a "
        "field."),
  ("p", "It is worth being explicit about why this is first. A dunning email that arrives while "
        "a customer is waiting for a reply about a genuine problem does more relationship damage "
        "than the original error, and it is the one part of the whole sequence that is "
        "irreversible &mdash; you cannot unsend it. Everything else in this system can afford "
        "to take thirty seconds. This cannot."),
  ("h3", "A dispute on an already-paid invoice"),
  ("p", "Rarer and more urgent. It usually means either a duplicate payment, which the customer "
        "wants back, or a genuine service failure that has escalated after the money went. "
        "Either way the chaser is irrelevant and the routing is different: it goes straight to "
        "whoever owns the relationship rather than into the accounts queue, and it is marked "
        "so."),
  ("p", "Next: how a recognised dispute gets sorted into one of the six reasons."),
 ],
},
{
 "slug": "how-a-dispute-gets-classified",
 "title": "How a dispute gets classified",
 "nav": "How it is classified",
 "read": 5, "words": 830,
 "desc": ("Six reasons, one model call, and why \"I cannot tell\" is a better answer than a "
          "confident wrong one -- because a wrong class gathers the wrong evidence."),
 "og": ("Six classes, one model call, and a deliberate escape hatch. A confidently wrong class "
        "gathers the wrong evidence, which is worse than gathering none."),
 "abstract": ("Six classes, one model call, and a deliberate escape hatch -- because a "
              "confidently wrong class gathers the wrong paperwork, which is worse than "
              "gathering none at all."),
 "lede": ("Classification is the only genuinely model-shaped task in this system, and it is a "
          "narrow one: read a customer's sentence and say which of six things they mean. The "
          "interesting design question is not how to make it accurate. It is what to do when it "
          "is not."),
 "tags": ["invoice disputes", "AWS Bedrock", "classification", "accounts receivable",
          "human in the loop", "serverless"],
 "takeaways": [
  "Six classes, plus \"cannot tell\", which is a normal and useful outcome.",
  "A dispute can carry two reasons, and the message says so rather than picking one.",
  "The model gets the invoice lines in the prompt, so a quantity claim can be checked for plausibility.",
  "A low-confidence class gathers nothing and hands over the raw message.",
  "Every classification is stored with the message, so accuracy can be measured rather than assumed.",
 ],
 "blocks": [
  ("h2", "One call, seven possible answers"),
  ("fig", ("chain", {
    "entry": {"title": "Recognised dispute", "sub": ["with the invoice"], "icon": "email"},
    "steps": [
      {"title": "Classify", "sub": ["one Bedrock call"], "icon": "model",
       "side": {"title": "The invoice lines", "sub": ["in the prompt"], "icon": "doc"}},
      {"title": "Confident enough?", "sub": ["the floor is yours"], "icon": "branch",
       "exit": {"title": "Hand over raw", "sub": ["no evidence gathered"], "icon": "person",
                "label": "no"}},
      {"title": "One reason or two?", "icon": "branch",
       "exit": {"title": "Gather for both", "sub": ["say so in the message"], "icon": "search",
                "label": "two"}},
      {"title": "About the invoice?", "sub": ["or about the work"], "icon": "branch",
       "exit": {"title": "To the relationship owner", "sub": ["not to accounts"], "icon": "team",
                "label": "the work"}},
      {"title": "To the gatherer", "sub": ["with one reason"], "icon": "queue"}],
    "note": "Every exit is a real destination. None of them is a rejection."}),
   "Classification and its four outcomes. The escape hatches are as important as the happy "
   "path, because acting confidently on a wrong class wastes more time than not classifying.",
   "How a dispute is classified into one of six reasons",
   "A vertical chain of five steps entered by a box labelled Recognised dispute, carrying the "
   "invoice. Step one classifies with a single Bedrock call, grounded by the invoice lines "
   "included in the prompt. Step two asks whether the classification is confident enough "
   "against a floor you set; if not it exits to Hand over raw, with no evidence gathered. Step "
   "three asks whether one reason or two were claimed; two exits to Gather for both, saying so "
   "in the message. Step four asks whether the dispute is about the invoice or about the work; "
   "the work exits to the relationship owner rather than accounts. Step five hands one reason "
   "to the gatherer. A note says every exit is a real destination and none of them is a "
   "rejection."),
  ("h3", "Why the invoice lines go in the prompt"),
  ("p", "\"We only got 6, not 10\" is ambiguous without the invoice. Six of what? If the "
        "invoice has one line for 10 pallets, it is a quantity dispute on that line. If it has "
        "four lines and one of them is for 10 boxes of something, it is a quantity dispute on "
        "that line specifically, and knowing which line matters enormously for what evidence "
        "gets pulled."),
  ("p", "So the prompt includes the invoice lines, and the output includes which line is being "
        "disputed where it can be determined. That is not the model doing arithmetic &mdash; it "
        "is the model matching a customer's phrasing to a line description, which is precisely "
        "what it is good at."),
  ("h3", "Two reasons at once"),
  ("p", "Disputes are frequently compound: \"we only got 6, and the price is higher than the "
        "quote anyway\". The temptation is to pick the dominant one, and it is a mistake, "
        "because resolving the quantity issue and leaving the price issue produces a second "
        "dispute a week later that looks like the first one was handled badly."),
  ("p", "So a dispute can carry up to two reasons, evidence is gathered for both, and the "
        "message says so plainly at the top: \"two issues raised\". Beyond two, the system stops "
        "classifying and hands the message over raw, because a message with three distinct "
        "complaints in it is a conversation rather than a dispute."),
  ("h2", "The confidence floor"),
  ("p", "Below the floor, nothing is gathered and the raw message goes to a person with a note "
        "saying the system could not tell what was being claimed. That feels like a failure and "
        "is the correct behaviour, for a specific reason: gathering the wrong evidence is worse "
        "than gathering none."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Right class", "sub": ["evidence attached"], "icon": "check"},
      {"title": "No class", "sub": ["raw message, honest"], "icon": "person"},
      {"title": "Wrong class", "sub": ["wrong paperwork"], "icon": "alarm"},
      {"title": "Cost of wrong", "sub": ["two round trips"], "icon": "retry"},
      {"title": "Cost of none", "sub": ["one round trip"], "icon": "clock"}],
    "title": "WHY \"I CANNOT TELL\" BEATS A GUESS",
    "note": "A wrong class costs more than no class, so the floor is set high rather than low."}),
   "The asymmetry that sets the confidence floor. Being wrong costs a person time twice; being "
   "honest costs it once.",
   "Why an uncertain classification is handed over rather than guessed",
   "A horizontal row of five boxes. Right class: the evidence is attached and the decision is "
   "quick. No class: the raw message is handed over honestly. Wrong class: the wrong paperwork "
   "is attached. Cost of wrong: two round trips, because the person must first realise the "
   "evidence is irrelevant. Cost of none: one round trip. A note says a wrong class costs more "
   "than no class, so the floor is set high rather than low."),
  ("h3", "Measuring it"),
  ("p", "Every classification is stored alongside the raw message and, once a person has "
        "resolved the dispute, alongside what the reason actually turned out to be. That is a "
        "labelled dataset that accumulates for free, and after a few months it answers a "
        "question most people guess at: how often is this thing right?"),
  ("p", "In practice the answer tends to be that quantity, duplicate and price classify very "
        "reliably, \"never ordered\" and \"wrong entity\" are frequently confused with each "
        "other, and \"not about the invoice\" is the one worth watching, because misrouting one "
        "of those into an accounts queue is how a service complaint sits unanswered for a week."),
  ("p", "Next: what the gatherer actually fetches for each reason."),
 ],
},
{
 "slug": "how-the-evidence-gets-gathered",
 "title": "How the evidence gets gathered",
 "nav": "How evidence is gathered",
 "read": 5, "words": 850,
 "desc": ("What gets pulled for each of the six reasons, why narrow beats complete, and the "
          "one-screen summary that turns a folder of documents into a decision."),
 "og": ("Different evidence per reason, deliberately narrow, and a one-screen summary that "
        "states the answer rather than presenting a folder."),
 "abstract": ("What gets pulled for each reason, why narrow beats complete, and the one-screen "
              "summary that turns a set of documents into an actual decision."),
 "lede": ("This is the part that saves the days. Everything else is routing; this is the "
          "system going and finding the delivery note so that a person does not have to ask "
          "operations for it and wait until tomorrow."),
 "tags": ["invoice disputes", "evidence gathering", "accounts receivable", "S3", "reporting",
          "serverless"],
 "takeaways": [
  "Each reason pulls a different, short list of documents. Narrow is the design goal.",
  "The summary states the answer, not the documents: \"POD signed for 10\", not \"POD attached\".",
  "Where the evidence contradicts the customer, it says so plainly and still asks a human.",
  "Where the evidence supports the customer, it says that too, which is the useful half.",
  "Missing evidence is a finding: an unsigned delivery note is worth knowing about immediately.",
 ],
 "blocks": [
  ("h2", "What each reason pulls"),
  ("table", ["Reason", "Gathered", "The one-line answer it produces"], [
   ["Quantity", "Delivery note, picking record, any POD image",
    "\"POD signed for 10 by J. Reed, 14:20, second vehicle.\""],
   ["Price", "The quote, the price list on the invoice date, prior invoices",
    "\"Quoted at £320/unit on 2 June; invoiced at £320.\""],
   ["Duplicate", "Payments in the period, invoices with a similar total",
    "\"No payment received. Invoice 4390 is £3,240 for a different job.\""],
   ["Never ordered", "The purchase order, the job record, who requested it",
    "\"Requested by email from p.hart@ on 12 May; PO 8841.\""],
   ["Wrong entity", "Account setup, the contract, the last six invoices",
    "\"Account is set to Acme Ltd; last six invoices billed the same way.\""],
   ["Not the invoice", "Nothing",
    "\"This is about the work, not the bill &mdash; sent to Dan.\""],
  ]),
  ("p", "The third column is the point. A system that attaches five documents has moved the "
        "reading job from operations to accounts. A system that states the answer in one line "
        "and attaches the document that proves it has actually done the work."),
  ("h2", "Narrow on purpose"),
  ("fig", ("chain", {
    "entry": {"title": "Classified dispute", "sub": ["one reason, one line"], "icon": "filter"},
    "steps": [
      {"title": "Fetch for this reason", "sub": ["three documents, not twelve"], "icon": "search",
       "side": {"title": "Records", "sub": ["S3 and the ledger"], "icon": "bucket"}},
      {"title": "Anything missing?", "icon": "branch",
       "exit": {"title": "Say what is missing", "sub": ["itself a finding"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Compare with the claim", "sub": ["plain arithmetic"], "icon": "counter"},
      {"title": "Write the one-liner", "sub": ["the answer, not the files"], "icon": "doc"},
      {"title": "One screen to a person", "sub": ["decision, then evidence"], "icon": "person"}],
    "note": "The comparison is arithmetic. The model is not asked whether the customer is right."}),
   "Gathering, comparing and summarising. The model classified; from here everything is lookup "
   "and subtraction, and the human gets an answer rather than a folder.",
   "How evidence is gathered and turned into a one-screen decision",
   "A vertical chain of five steps entered by a box labelled Classified dispute, carrying one "
   "reason and one invoice line. Step one fetches the documents for that reason from S3 and the "
   "ledger, three documents rather than twelve. Step two asks whether anything is missing, "
   "exiting to Say what is missing, which is itself a finding. Step three compares the evidence "
   "with the claim using plain arithmetic. Step four writes the one-liner, which is the answer "
   "rather than a list of files. Step five sends one screen to a person, with the decision "
   "first and the evidence below it. A note says the comparison is arithmetic and the model is "
   "never asked whether the customer is right."),
  ("h3", "Missing evidence is a finding"),
  ("p", "A quantity dispute where no signed delivery note can be found is not a gathering "
        "failure. It is the single most important thing the system can tell you, because it "
        "means you cannot substantiate the delivery &mdash; and that is true whether or not the "
        "customer is right on this occasion."),
  ("p", "So a missing document is stated first, in plain terms: \"No signed POD on file for "
        "invoice 4412.\" That sentence changes both the response to this dispute and, if it "
        "appears repeatedly, a process in the warehouse. Systems that quietly return what they "
        "found and omit what they did not are hiding the more useful half."),
  ("h3", "Saying when the customer is right"),
  ("p", "About a third of the time the evidence supports the customer, and the summary has to "
        "say so as plainly as it says the reverse. \"Quote dated 2 June is £280/unit; invoiced "
        "at £320\" is a sentence that costs the business money, and burying it under an "
        "attachment would be a design choice about whose interests the system serves."),
  ("p", "It still goes to a person rather than triggering an automatic credit note, for the "
        "same reason everything else in this series does: the evidence may be complete and the "
        "situation may still have context in it that no record holds. But it goes to a person "
        "with the answer already written."),
  ("h2", "The one screen"),
  ("callout", "What a person sees, in order", [
   "<strong>The verdict line.</strong> \"POD signed for 10 by J. Reed at 14:20. Second vehicle "
   "delivered separately.\"",
   "<strong>The claim, quoted.</strong> The customer's own sentence, verbatim, so nothing is "
   "lost in paraphrase.",
   "<strong>Two buttons.</strong> \"Reply with the evidence\" and \"Raise a credit note\", both "
   "of which open a draft rather than doing anything.",
   "<strong>The documents,</strong> below the fold. Present, one tap away, and not the first "
   "thing on the screen.",
   "<strong>The history line.</strong> \"3rd quantity dispute from this customer this year; the "
   "previous two were both second-vehicle deliveries.\" That sentence solves the underlying "
   "problem rather than this instance of it.",
  ]),
  ("p", "Next: what happens to the decision, and the report that turns fifteen disputes a month "
        "into a process change."),
 ],
},
{
 "slug": "how-a-dispute-decision-gets-recorded",
 "title": "How a dispute decision gets recorded",
 "nav": "How it is recorded",
 "read": 5, "words": 820,
 "desc": ("Resuming the chaser, the record a resolved dispute leaves, and the monthly report "
          "that turns individual disputes into one fixable process problem."),
 "og": ("A resolved dispute leaves a record with the reason, the outcome and the elapsed time "
        "-- and the monthly report turns fifteen individual disputes into one fixable cause."),
 "abstract": ("Resuming the chaser correctly, the record a resolved dispute leaves, and the "
              "monthly report that turns fifteen individual disputes into one process problem "
              "worth fixing."),
 "lede": ("Individually, a dispute is an annoyance to be cleared. In aggregate, fifteen "
          "disputes a month are a description of exactly what is wrong with how the business "
          "delivers and bills, written by your customers, for free. This post is about "
          "capturing enough on the way past to read that."),
 "tags": ["invoice disputes", "accounts receivable", "reporting", "DynamoDB", "process improvement",
          "serverless"],
 "takeaways": [
  "Resuming the chaser is a decision, not an automatic consequence of closing a dispute.",
  "A resolved dispute records the reason, the outcome, the elapsed time and who decided.",
  "Outcome and reason are separate: a quantity dispute can end in a credit note or in a POD.",
  "The monthly report groups by reason and by customer, which are different questions.",
  "One recurring reason is a process problem. One recurring customer is a relationship problem.",
 ],
 "blocks": [
  ("h2", "Resuming the chaser"),
  ("p", "Closing a dispute does not automatically restart payment reminders, and the "
        "distinction matters. A dispute resolved in the customer's favour ends with a credit "
        "note and a new balance, which should be chased on its own schedule. A dispute resolved "
        "against the customer ends with an invoice that has now been outstanding for two weeks "
        "longer, and immediately firing an overdue reminder at somebody you have just told they "
        "were wrong is a poor sequence of events."),
  ("ul", [
   "<strong>Upheld, credit note raised.</strong> The original invoice is settled by the credit "
   "note; any remaining balance restarts chasing from the resolution date, not the original due "
   "date.",
   "<strong>Not upheld, evidence sent.</strong> Chasing resumes, but the first reminder is "
   "delayed by a grace period from the sheet &mdash; a week is typical &mdash; because the "
   "customer needs time to act on the reply.",
   "<strong>Partially upheld.</strong> The most common outcome in practice. A partial credit "
   "note, a new balance, and the grace period applies.",
   "<strong>Withdrawn.</strong> The customer says never mind. Chasing resumes at the original "
   "schedule, because nothing about the invoice changed.",
  ]),
  ("h2", "The record"),
  ("table", ["Field", "Example", "Why it is there"], [
   ["<code>invoice</code>", "4412", "What was disputed"],
   ["<code>customer</code>", "acme-ltd", "The other grouping that matters"],
   ["<code>reason</code>", "quantity", "What was claimed"],
   ["<code>reason_actual</code>", "quantity", "What it turned out to be, for measuring the classifier"],
   ["<code>outcome</code>", "not_upheld", "upheld, not_upheld, partial, withdrawn"],
   ["<code>value</code>", "0.00", "The credit note amount, if any"],
   ["<code>opened</code>", "2026-07-14T09:12:00Z", "When the message arrived"],
   ["<code>closed</code>", "2026-07-14T11:40:00Z", "When a person decided"],
   ["<code>decided_by</code>", "accounts@example.com", "Who"],
   ["<code>evidence_gap</code>", "none", "Or what could not be found, which is the useful one"],
  ]),
  ("p", "<code>reason</code> and <code>reason_actual</code> being separate is what makes the "
        "classifier measurable. <code>outcome</code> and <code>reason</code> being separate is "
        "what makes the report useful, because \"quantity disputes\" and \"disputes we lost\" "
        "are different populations and conflating them hides both."),
  ("h2", "The monthly report"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Disputes", "sub": ["15 this month"], "icon": "email"},
      {"title": "Top reason", "sub": ["quantity, 8"], "icon": "counter"},
      {"title": "Upheld", "sub": ["4, £1,180"], "icon": "money"},
      {"title": "Median time", "sub": ["3.1 hours"], "icon": "clock"},
      {"title": "Evidence gaps", "sub": ["2 missing PODs"], "icon": "alarm"}],
    "title": "ONE MONTH OF DISPUTES",
    "note": "The second number names a process. The fifth names one you did not know you had."}),
   "A month of disputes in five numbers. The top-reason count and the evidence gaps are the two "
   "that lead to a change rather than to a task.",
   "One month of invoice disputes summarised in five numbers",
   "A horizontal row of five boxes. Disputes: fifteen this month. Top reason: quantity, with "
   "eight of them. Upheld: four, worth one thousand one hundred and eighty pounds in credit "
   "notes. Median time: three point one hours from arrival to decision. Evidence gaps: two "
   "missing proofs of delivery. A note says the second number names a process and the fifth "
   "names one you did not know you had."),
  ("h3", "Grouping by reason versus by customer"),
  ("p", "These answer different questions and both are worth having. Eight quantity disputes in "
        "a month, from six different customers, is a delivery process problem &mdash; almost "
        "certainly split loads being invoiced as one and delivered as two. Fixing it is a change "
        "to how deliveries are documented, and it removes eight disputes a month permanently."),
  ("p", "Eight disputes in a month from one customer, across four different reasons, is not a "
        "process problem at all. It is a relationship that has gone wrong, or a customer with a "
        "cash flow problem using disputes to delay payment, and neither of those is fixed by "
        "improving delivery notes. Reading a single combined list makes both of these invisible."),
  ("h3", "Median time, and why median"),
  ("p", "The mean is useless here because one dispute that took eleven days while somebody was "
        "on leave dominates fourteen that took two hours. The median describes the ordinary "
        "case, which is what the system was built to improve. Watching it fall from days to "
        "hours in the first month is the clearest evidence the thing is working."),
  ("callout", "What the report deliberately does not include", [
   "Anything per-employee. Who handled a dispute is recorded for audit and never aggregated "
   "into a per-person statistic.",
   "A total value of disputes raised. Only upheld value is real money; disputed value is a "
   "number that makes the situation look worse than it is.",
   "Any customer scoring or risk rating. The system records what happened; deciding what a "
   "pattern of disputes means about a customer is a judgement with commercial context in it.",
   "A forecast. Fifteen a month is not a rate you can extrapolate from, and presenting it as "
   "one invites decisions it cannot support.",
  ]),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="dispute",
 volumes=[(10, "10 disputes"), (40, "40 disputes"), (150, "150 disputes")],
 read_each=0.0072, msgs_each=2.2,
 lede=("Dispute volume is low even in businesses that feel overwhelmed by them &mdash; fifteen "
       "a month is a normal figure for a firm raising four hundred invoices. The bill reflects "
       "that: this is one of the cheapest systems in the series to run, and the value is "
       "entirely in the hours it gives back rather than in anything it costs. Here is where "
       "each cent goes."),
 risks=[
  "<strong>Classifying every inbox message.</strong> If the cheap structural filters are "
  "skipped and every message that arrives gets a model call, a single customer's out-of-office "
  "loop can cost more in a week than a year of real disputes. Auto-reply and remittance "
  "detection are free and must come first.",
  "<strong>A retry loop on a malformed attachment.</strong> A dispute email carrying a "
  "corrupted PDF makes the function throw, and without a dead-letter queue the queue "
  "redelivers indefinitely. Maximum receive count of three.",
  "<strong>Log retention left at never.</strong> At this volume the logs will out-cost "
  "everything else within months. Thirty days of retention is the whole fix.",
 ],
 per_unit_note=("The read cost per dispute is higher than in most systems here because the "
                "prompt carries the invoice lines as well as the customer message. That is the "
                "right trade: it is what lets the classifier identify which line is being "
                "disputed, which is what makes the gathering narrow."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="id",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the inbound mail path, and the single model call."),
 outside=[
  {"title": "SES inbound", "sub": ["the accounts address"], "icon": "email"},
  {"title": "Your records", "sub": ["ledger API, S3 documents"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["decisions, drafts"], "icon": "email"}],
 inside=[
  {"title": "S3 + SQS", "sub": ["raw mail,", "one dispute queue"], "icon": "bucket"},
  {"title": "Lambda x4", "sub": ["recognise, classify,", "gather, record"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["disputes, invoices"], "icon": "database"}],
 note="us-east-1. One account. The disputed flag is the only thing written outside this system.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. SES inbound, receiving mail sent to the "
  "accounts address. Your records, meaning the ledger API and the documents held in S3. And SES "
  "outbound, carrying the decision screens and the reply drafts. Inside the account, three "
  "groups. S3 holding the raw mail and SQS carrying one dispute queue. Four Lambda functions "
  "named recognise, classify, gather and record. And two DynamoDB tables named disputes and "
  "invoices. A note gives the region as us-east-1, one account, and states that the disputed "
  "flag is the only thing this system writes outside itself."),
 functions=[
  ["<code>id-recognise</code>", "S3 ObjectCreated",
   "Header filters, remittance detection, invoice match, pauses the chaser",
   "10s / 512&nbsp;MB"],
  ["<code>id-classify</code>", "SQS dispute queue",
   "One Bedrock call into a reason, a line and a confidence", "20s / 1024&nbsp;MB"],
  ["<code>id-gather</code>", "SQS classified queue",
   "Fetches the evidence for that reason and writes the one-liner", "30s / 1024&nbsp;MB"],
  ["<code>id-record</code>", "Function URL",
   "Handles the signed decision links; resumes chasing on the right schedule",
   "10s / 512&nbsp;MB"]],
 roles=[
  ["<code>id-recognise-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:UpdateItem</code>",
   "The mail prefix; the invoices table disputed flag only"],
  ["<code>id-classify-role</code>", "<code>bedrock:InvokeModel</code>, <code>sqs:SendMessage</code>",
   "One model arn; the classified queue"],
  ["<code>id-gather-role</code>", "<code>s3:GetObject</code>, <code>ses:SendRawEmail</code>",
   "The documents prefix; one verified identity"],
  ["<code>id-record-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Disputes and invoices; the signing key only"]],
 tables=[
  ("Table: disputes",
   "PK   dispute_id        S   dsp_2026_07_14_9c2b\n"
   "     invoice           S   4412\n"
   "     customer          S   acme-ltd\n"
   "     state             S   open | gathered | decided\n"
   "     reason            S   quantity | price | duplicate | not_ordered |\n"
   "                           wrong_entity | not_invoice | unknown\n"
   "     reason_actual     S   set when a person decides\n"
   "     confidence        N   0.91\n"
   "     line              S   which invoice line, where determinable\n"
   "     evidence          L   [{kind, s3_key, one_liner}]\n"
   "     evidence_gap      S   none | no_signed_pod | no_quote_on_file\n"
   "     outcome           S   upheld | not_upheld | partial | withdrawn\n"
   "     opened / closed   S   ISO timestamps\n"
   "     ttl               N   epoch, +7 years\n\n"
   "GSI  customer-index      PK customer, SK opened   -- the per-customer view"),
  ("Table: invoices",
   "PK   invoice           S   4412\n"
   "     customer          S   acme-ltd\n"
   "     total             N   3240.00\n"
   "     lines             L   [{description, qty, unit_price}]\n"
   "     disputed          BOOL true      -- what the chaser reads\n"
   "     dispute_id        S   dsp_2026_07_14_9c2b\n"
   "     chase_from        S   2026-07-21    -- the grace period after a decision\n\n"
   "This table is a projection of your real ledger, not a replacement for it.\n"
   "The only field this system writes is `disputed` and `chase_from`.")],
 inbound=[
  "An SES <strong>receipt rule set</strong> on the accounts address writes the whole message to "
  "S3 with attachments. The S3 event fires <code>id-recognise</code> directly.",
  "<strong>Header filters run before anything else.</strong> <code>Auto-Submitted</code>, "
  "<code>X-Autoreply</code> and a bulk precedence are all discarded without a model call.",
  "<strong>Threading</strong> uses <code>In-Reply-To</code> and <code>References</code> to find "
  "the invoice, which is more reliable than parsing a number out of a body.",
  "<strong>Decision links</strong> are signed, scoped to one dispute, single-use, and expire "
  "after thirty days."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock. "
  "The task is classifying a short customer message into one of six labels.",
  "<strong>Called once</strong> per recognised dispute, after every free structural filter has "
  "run, and never on an auto-reply or a remittance.",
  "<strong>Output is a JSON schema</strong> with a reason, an optional second reason, an "
  "optional invoice line, and a confidence. Every field is nullable and a null reason is the "
  "hand-over-raw path.",
  "<strong>Grounded</strong> with the invoice lines, so the model can identify which line is "
  "being disputed rather than only what kind of complaint it is.",
  "<strong>Nothing about the evidence touches a model.</strong> Comparing a claimed quantity "
  "with a signed delivery note is a lookup and a comparison, and both should be code."],
 gotchas=[
  "Pause the chaser before classifying, not after. It is the only irreversible step in the "
  "sequence and it has to happen within seconds.",
  "Match invoice numbers within the customer, not globally. Customer-scoped matching removes "
  "almost every false positive at no cost.",
  "Set the confidence floor high. A wrong class attaches the wrong paperwork and costs two "
  "round trips; an honest unknown costs one.",
  "Keep `outcome` and `reason` as separate fields. Conflating them makes the monthly report "
  "unable to answer either question it exists to answer.",
  "Do not resume chasing automatically on close. A reminder fired at somebody you have just "
  "told they were wrong is a worse outcome than a week of delay."],
))
