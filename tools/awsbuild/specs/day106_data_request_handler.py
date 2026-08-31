"""Day 106 -- 2026-08-08 -- Data request handler."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "data-request-handler"
NAME = "Data request handler"

SPEC = {
 "slug": SLUG, "date": "2026-08-08", "name": NAME,
 "tagline": ("Recognises a data request the day it arrives, starts the clock, gathers from every "
             "system that holds anything, and hands a person a package to review -- rather than "
             "somebody finding the email three weeks in."),
 "lede": ("A small system that spots a subject access or deletion request in an ordinary inbox, "
          "records the statutory clock, verifies who is asking, gathers what every system holds, "
          "and puts a package in front of a person to check before anything is sent. It never "
          "releases or deletes anything unreviewed. Seven posts on the same system -- one "
          "diagram at a time -- with a cost breakdown and an engineering reference at the end."),
 "keywords": ["subject access request", "GDPR", "data deletion", "compliance", "privacy",
              "serverless"],
 "icons": ["shield", "clock", "doc"],
 "faq": [
  ("What is a data request handler?",
   "A small serverless system that recognises a data subject request in an ordinary inbox, "
   "starts the statutory clock, verifies the requester, gathers what each system holds, and "
   "presents a package for a person to review. A person sends it; the system never does."),
  ("Why does recognising it matter so much?",
   "Because the clock starts when the request arrives, not when somebody notices it. A request "
   "worded as an ordinary complaint that sits unread for three weeks has consumed most of the "
   "response period before anybody has started."),
  ("Does it delete data automatically?",
   "No. It produces a deletion plan naming every record in every system, and a person executes "
   "it. Automatic deletion across systems on the basis of an email is not a risk worth taking."),
  ("How does it verify who is asking?",
   "Proportionately. An email from the address already on the account is usually sufficient; a "
   "request from an unknown address for somebody else's data needs more. Over-verifying is "
   "itself a way of obstructing a request."),
  ("What does it cost to run?",
   "A couple of dollars a month. Request volume is low even where it feels high. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "data-request-handler-on-aws",
 "title": "A data request handler on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Recognises a data request on arrival, starts the clock, gathers from every system, "
          "and hands a person a package to review. AWS, about $2 a month."),
 "og": ("The clock starts when the request arrives, not when somebody notices it. Recognising "
        "one on day zero is most of the value."),
 "abstract": ("The whole system on one page -- a recogniser, a gatherer and a reviewer -- built "
              "around the fact that the deadline runs from arrival."),
 "lede": ("A subject access request rarely arrives labelled as one. It arrives as an angry email "
          "that ends \"and send me everything you have on me\", in an inbox that gets forty "
          "messages a day, and it sits there. Three weeks later somebody notices, and a "
          "thirty-day statutory window has nine days left in it and nobody has started gathering "
          "anything. This post walks through a small system whose most valuable single feature "
          "is noticing on day zero."),
 "tags": ["subject access request", "GDPR", "data deletion", "compliance", "privacy", "serverless"],
 "takeaways": [
  "The clock starts on arrival. Recognising a request the same day is most of the value.",
  "Requests arrive worded as complaints, not as legal notices, and both count.",
  "Gathering is per system and each system is asked once, with a record of what it returned.",
  "A person reviews every package before it leaves, and executes every deletion.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "An ordinary inbox", "sub": ["where requests arrive"], "icon": "inbox"},
      {"title": "Your systems", "sub": ["each holding something"], "icon": "database"},
      {"title": "Whoever handles it", "sub": ["reviews and sends"], "icon": "person"}],
    "inside": [
      {"title": "Recogniser", "sub": ["is this a request?", "start the clock"], "icon": "search"},
      {"title": "Gatherer", "sub": ["ask every system,", "record what came back"], "icon": "filter"},
      {"title": "Reviewer", "sub": ["a package, checked", "before it goes"], "icon": "doc"}],
    "edges": [{"from": 0, "to": 0, "label": "messages"},
              {"from": 1, "to": 1, "label": "what each holds"},
              {"from": 2, "to": 2, "label": "a package to review", "up": True}],
    "note": "Nothing is released or deleted without a person. The system prepares; a person acts."}),
   "Three things outside the account, three pieces inside it. The recogniser is doing the "
   "highest-value work, because everything downstream is only useful if it starts on time.",
   "System: a request recognised, data gathered, a package reviewed",
   "Three boxes across the top sit outside the AWS account. On the left, An ordinary inbox where "
   "requests arrive. In the middle, Your systems, each holding something. On the right, Whoever "
   "handles it: the person who reviews and sends. Each connects by an arrow to the AWS account "
   "container below. Messages flow down into the account. Each system reports what it holds. A "
   "package to review goes back out. Inside the AWS account are three components in a row. On the "
   "left, the Recogniser, which asks whether this is a request and starts the clock. In the "
   "middle, the Gatherer, which asks every system and records what came back. On the right, the "
   "Reviewer, which produces a package checked before it goes. A note at the bottom says nothing "
   "is released or deleted without a person; the system prepares and a person acts."),
  ("h3", "The clock starts on arrival"),
  ("p", "This is the fact the whole design turns on. Response deadlines run from when the request "
        "was received, not from when it was recognised, opened or forwarded to the right person. "
        "A request that sits unread for three weeks has already consumed most of its window."),
  ("p", "So the most valuable thing this system does is notice, on the day, in an inbox where "
        "nobody was looking for one. Everything after that &mdash; the gathering, the package, "
        "the review &mdash; is useful and would be manageable by hand if somebody had three "
        "weeks. The three weeks is what gets lost."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The recogniser.</strong> Reads inbound mail and asks one narrow question: is somebody "
   "asking for their data, or asking for it to be deleted? Part 2 covers the wording it has to "
   "catch and the wording it must not over-catch.",
   "<strong>The gatherer.</strong> Asks each system what it holds about this person, records the "
   "answer including \"nothing\", and assembles it. Part 3 is about the systems that cannot be "
   "asked programmatically, which is most of them.",
   "<strong>The reviewer.</strong> Presents the package with everything that would be sent, "
   "highlights what needs redacting, and requires a person to release it. Part 4.",
  ]),
  ("h2", "One request, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Arrives", "sub": ["worded as a complaint"], "icon": "inbox"},
      {"title": "Recognised", "sub": ["clock starts, day zero"], "icon": "clock"},
      {"title": "Verified", "sub": ["proportionately"], "icon": "shield"},
      {"title": "Gathered", "sub": ["every system asked"], "icon": "filter"},
      {"title": "Reviewed and sent", "sub": ["by a person"], "icon": "person"}],
    "title": "ONE REQUEST, END TO END",
    "note": "The second box is worth more than the other four put together."}),
   "The same system as one line. Recognition on day zero is what turns a panicked scramble into "
   "an ordinary task with weeks of margin.",
   "One data request from arrival to sent package, in five stages",
   "A horizontal row of five boxes joined by arrows. Arrives: worded as a complaint. Recognised: "
   "the clock starts on day zero. Verified: proportionately. Gathered: every system asked. "
   "Reviewed and sent: by a person. A note says the second box is worth more than the other four "
   "put together."),
  ("h2", "In plain words"),
  ("p", "An email arrives on the 8th complaining about a delivery, and the last line says "
        "\"please also send me a copy of all the personal data you hold about me and then delete "
        "my account\". That is two requests in a sentence at the end of a complaint, and in an "
        "ordinary inbox it is genuinely easy to miss."),
  ("p", "The recogniser catches both, records the arrival date as day zero, and tells whoever "
        "handles these within the hour. Verification is straightforward: the email came from the "
        "address on the account. The gatherer asks the six systems that hold anything, five "
        "answer within seconds, and the sixth &mdash; a booking tool with no export API &mdash; "
        "becomes a task for a person with three days on it."),
  ("p", "By the 11th the package is assembled: the order history, the messages, the account "
        "record, the support tickets, and a note that the marketing tool holds only an email "
        "address and a subscription state. Somebody spends twenty minutes reviewing it, redacts "
        "two lines of an internal note that mention another customer, and sends it on the 12th "
        "&mdash; four days in, with the deletion scheduled separately once the access request is "
        "satisfied."),
  ("callout", "Design rules that shaped every decision", [
   "The clock starts on arrival. Everything is measured from that date, not from recognition.",
   "Recognise generously and confirm cheaply. A false positive costs one clarifying question.",
   "Ask every system, and record \"nothing\" as an answer. An unasked system is not the same as "
   "an empty one.",
   "Verify proportionately. Over-verification is a recognised way of obstructing a request.",
   "A person reviews and releases. Nothing leaves and nothing is deleted automatically.",
   "Deletion is a plan a person executes, with the record of what was deleted kept.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Businesses that get these wrong almost never do so out of unwillingness. They do it "
        "because a request arrived worded as something else, went unnoticed, and by the time "
        "somebody was looking at it the remaining time was not enough to ask six systems and "
        "review the answers properly."),
  ("p", "So the design spends its effort on the two places time is lost: recognition, which is "
        "one model call on inbound mail, and gathering, which is a fan-out that would otherwise "
        "be somebody emailing colleagues. The review is deliberately manual because it is the "
        "part where judgement is genuinely required and where an error is expensive."),
  ("p", "The next four posts walk through each piece: how a request is recognised, how the "
        "requester is verified, how the data is gathered, and how the package is reviewed and "
        "delivered. One diagram per post, a cost breakdown, and an engineering reference at the "
        "end."),
 ],
},
{
 "slug": "how-a-data-request-gets-recognised",
 "title": "How a data request gets recognised",
 "nav": "How it is recognised",
 "read": 5, "words": 750,
 "desc": ("The wording that counts, the wording that does not, why recognising generously is "
          "correct, and the request that arrives by post."),
 "og": ("A request does not have to say GDPR, or subject access, or anything legal at all. "
        "\"Send me everything you have on me\" is a request."),
 "abstract": ("What wording counts as a request, why generous recognition with a cheap "
              "confirmation is the right trade, the requests that are not requests, and the "
              "channels other than email."),
 "lede": ("Nobody writes \"I am exercising my right of access under Article 15\". They write "
          "\"what information do you actually have about me\", usually while annoyed about "
          "something else, and a system that only recognises the formal wording will recognise "
          "almost nothing."),
 "tags": ["subject access request", "GDPR", "classification", "AWS Bedrock", "inbound mail",
          "serverless"],
 "takeaways": [
  "No formal wording is required, and almost nobody uses it.",
  "Recognise generously; a false positive costs one clarifying question.",
  "Four kinds: access, deletion, correction, and objection to processing.",
  "\"Delete my account\" is usually not a deletion request, and asking is how you find out.",
  "Requests arrive by post, by phone and in person, and those need a manual entry path.",
 ],
 "blocks": [
  ("h2", "What counts"),
  ("table", ["What somebody writes", "What it is", "Recognised?"], [
   ["\"Send me all the data you hold on me\"", "An access request", "Yes"],
   ["\"What information do you have about me?\"", "An access request", "Yes"],
   ["\"Delete everything you have about me\"", "A deletion request", "Yes"],
   ["\"Please close my account\"", "Probably not a deletion request", "Ask"],
   ["\"Stop emailing me\"", "A marketing withdrawal, not a data request", "No"],
   ["\"Why do you have my phone number?\"", "Possibly an access request", "Ask"],
  ]),
  ("p", "The fourth and sixth rows are why the system asks rather than deciding. Closing an "
        "account and erasing all personal data are different things with very different "
        "consequences, and a substantial proportion of people who say the first do not mean the "
        "second. One clarifying question resolves it and takes a day off nothing."),
  ("h2", "Recognise generously"),
  ("fig", ("chain", {
    "entry": {"title": "Inbound message", "sub": ["any inbox"], "icon": "inbox"},
    "steps": [
      {"title": "Cheap filters first", "sub": ["auto-reply, bulk"], "icon": "filter",
       "exit": {"title": "Ignore", "sub": ["no model call"], "icon": "stop", "label": "yes"}},
      {"title": "Could this be a request?", "sub": ["one Bedrock call"], "icon": "model",
       "exit": {"title": "Not a request", "sub": ["most messages"], "icon": "check",
                "label": "no"}},
      {"title": "Which kind?", "sub": ["access, delete, correct,", "object"], "icon": "branch",
       "exit": {"title": "Ambiguous", "sub": ["ask one question"], "icon": "chat",
                "label": "unclear"}},
      {"title": "Record day zero", "sub": ["the arrival timestamp"], "icon": "clock",
       "side": {"title": "Requests table", "sub": ["the clock lives here"], "icon": "database"}},
      {"title": "Tell whoever handles it", "sub": ["within the hour"], "icon": "bell"}],
    "note": "Day zero is the arrival timestamp, not the recognition timestamp. Always."}),
   "How a request is recognised. The distinction in the note is the one that matters legally and "
   "is the easiest to get wrong in a schema.",
   "How an inbound message is recognised as a data request",
   "A vertical chain of five steps entered by a box labelled Inbound message, from any inbox. "
   "Step one applies cheap filters first for auto-replies and bulk mail; a hit exits to Ignore "
   "with no model call. Step two asks whether this could be a request, with a single Bedrock "
   "call; no exits to Not a request, which is most messages. Step three asks which kind: access, "
   "delete, correct or object; unclear exits to Ambiguous, which asks one question. Step four "
   "records day zero as the arrival timestamp in a requests table where the clock lives. Step "
   "five tells whoever handles it within the hour. A note says day zero is the arrival timestamp "
   "and not the recognition timestamp, always."),
  ("h3", "Why generous"),
  ("p", "The two errors are not symmetric. A false positive means somebody asks a customer "
        "\"just to check &mdash; are you asking for a copy of your data?\" and gets told no, "
        "which costs one email and reads as attentive. A false negative means a statutory "
        "deadline passes without anybody knowing there was one."),
  ("p", "So the threshold is set low and the confirmation is cheap. In practice the system flags "
        "perhaps three messages a month in a small business, one of which is a genuine request "
        "and two of which are resolved by asking."),
  ("h3", "Day zero versus recognition"),
  ("p", "Two timestamps, and a schema with only one of them is a schema that will eventually "
        "report a deadline wrongly. The arrival timestamp is what the deadline runs from. The "
        "recognition timestamp is how you measure whether the recogniser is working."),
  ("p", "Keeping both also produces the single most useful operational number in the system: the "
        "gap between them. A median gap of under an hour means the recogniser is doing its job; a "
        "gap of eleven days on one request means something arrived in an inbox that is not being "
        "watched."),
  ("h2", "The channels that are not email"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Email", "sub": ["recognised automatically"], "icon": "email"},
      {"title": "Web form", "sub": ["explicit, easiest"], "icon": "form"},
      {"title": "By post", "sub": ["somebody types it in"], "icon": "doc"},
      {"title": "By phone", "sub": ["logged, with the date"], "icon": "phone"},
      {"title": "In person", "sub": ["same manual path"], "icon": "person"}],
    "title": "A REQUEST DOES NOT HAVE TO ARRIVE BY EMAIL",
    "note": "The manual path exists so the clock is recorded correctly, not so it is convenient."}),
   "The channels a request can arrive through. The manual entry path is not a convenience "
   "feature; it exists so that a request made by phone gets the same clock as one made by email.",
   "Five channels a data request can arrive through",
   "A horizontal row of five boxes. Email: recognised automatically. Web form: explicit and "
   "easiest. By post: somebody types it in. By phone: logged with the date. In person: the same "
   "manual path. A note says the manual path exists so the clock is recorded correctly rather "
   "than so it is convenient."),
  ("p", "The manual entry form asks for one thing that is easy to get wrong: the date the request "
        "was made, not the date it was entered. Somebody typing up a letter that arrived on "
        "Tuesday on the following Monday must record Tuesday, and the form defaults to today with "
        "a prompt rather than silently accepting it."),
  ("p", "Next: verifying who is asking."),
 ],
},
{
 "slug": "how-a-requester-gets-verified",
 "title": "How a requester gets verified",
 "nav": "How it verifies",
 "read": 5, "words": 740,
 "desc": ("Proportionate verification, why over-verifying is itself a problem, and the requests "
          "made on somebody else's behalf."),
 "og": ("Demanding photo ID for a request from the email address already on the account is not "
        "diligence; it is friction, and it is a recognised way of obstructing a request."),
 "abstract": ("What proportionate verification means, the three tiers of confidence, why "
              "over-verification is itself a failure, and how third-party requests are handled."),
 "lede": ("Verification is where these processes most often go wrong in both directions. Too "
          "little and you send somebody's data to a stranger. Too much and you have built an "
          "obstacle course, which is a documented tactic and reads exactly like one."),
 "tags": ["subject access request", "identity verification", "GDPR", "proportionality", "privacy",
          "serverless"],
 "takeaways": [
  "Three tiers: already-authenticated, matching contact details, and unknown.",
  "An email from the address on the account is usually sufficient on its own.",
  "Never ask for photo ID by default. It is disproportionate and it is a red flag.",
  "A request on somebody else's behalf needs authority, which is a different check.",
  "Whatever is asked for is deleted once verification is complete.",
 ],
 "blocks": [
  ("h2", "Three tiers"),
  ("fig", ("chain", {
    "entry": {"title": "A recognised request", "sub": ["clock running"], "icon": "clock"},
    "steps": [
      {"title": "Already authenticated?", "sub": ["logged in, or a signed link"],
       "icon": "branch",
       "exit": {"title": "Verified", "sub": ["nothing more needed"], "icon": "check",
                "label": "yes"}},
      {"title": "From an address we hold?", "sub": ["on their own account"], "icon": "branch",
       "exit": {"title": "Verified", "sub": ["for their own data"], "icon": "check",
                "label": "yes"}},
      {"title": "For their own data?", "sub": ["or somebody else's"], "icon": "branch",
       "exit": {"title": "Authority needed", "sub": ["a different question"], "icon": "team",
                "label": "somebody else"}},
      {"title": "Ask one thing", "sub": ["something only they would know"], "icon": "chat"},
      {"title": "Verified, and the clock", "sub": ["paused while asking"], "icon": "shield"}],
    "note": "Two of the three tiers need nothing. The third asks one question, not for documents."}),
   "How verification is decided. Most requests clear at the first or second tier, which is the "
   "correct outcome rather than a shortcut.",
   "How a data requester is verified proportionately",
   "A vertical chain of five steps entered by a box labelled A recognised request, with the clock "
   "running. Step one asks whether they are already authenticated, either logged in or arriving "
   "through a signed link; if so it exits to Verified with nothing more needed. Step two asks "
   "whether the message came from an address held on their own account; if so it exits to "
   "Verified for their own data. Step three asks whether the request is for their own data or "
   "somebody else's; somebody else exits to Authority needed, which is a different question. Step "
   "four asks one thing that only they would know. Step five is Verified, with the clock paused "
   "while asking. A note says two of the three tiers need nothing and the third asks one question "
   "rather than for documents."),
  ("h3", "Why photo ID is the wrong default"),
  ("p", "Asking for a passport scan in response to a request from the email address already on "
        "the account achieves nothing protective &mdash; anybody with access to that mailbox can "
        "already reset the password &mdash; and it does three bad things. It adds friction that "
        "deters legitimate requests, it collects a highly sensitive document you now have to "
        "store and delete, and it looks precisely like obstruction to anybody assessing your "
        "process."),
  ("p", "Where identity genuinely is uncertain, one question about something only the account "
        "holder would know &mdash; a recent order number, the delivery address on file &mdash; is "
        "both more proportionate and more effective."),
  ("h3", "Pausing the clock"),
  ("p", "Where verification genuinely is needed, the period spent waiting for the answer does not "
        "count against the response deadline in most regimes, and the system records the pause "
        "explicitly with its start and end. That is worth building because the alternative is "
        "somebody reconstructing it afterwards from an email thread."),
  ("p", "It is also worth being disciplined about: pausing the clock for a verification question "
        "that was not necessary is exactly the pattern that gets characterised as obstruction, "
        "and a system that logs every pause makes that visible to whoever reviews it."),
  ("h2", "Requests on somebody else's behalf"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A solicitor", "sub": ["for their client"], "icon": "doc"},
      {"title": "A parent", "sub": ["for a child"], "icon": "team"},
      {"title": "A representative", "sub": ["with authority"], "icon": "person"},
      {"title": "Check authority", "sub": ["not identity"], "icon": "shield"},
      {"title": "Then verify the subject", "sub": ["as normal"], "icon": "check"}],
    "title": "A THIRD-PARTY REQUEST IS TWO CHECKS",
    "note": "Authority to ask, and the identity of the person the data is about. Different questions."}),
   "Why a third-party request needs two separate checks. Conflating them is how a request is "
   "either wrongly refused or wrongly fulfilled.",
   "How a data request made on somebody else's behalf is verified",
   "A horizontal row of five boxes. A solicitor: acting for their client. A parent: for a child. "
   "A representative: with authority. Check authority: which is not the same as identity. Then "
   "verify the subject: as normal. A note says authority to ask and the identity of the person "
   "the data is about are different questions."),
  ("p", "These are uncommon and they are the ones most likely to be mishandled, because the "
        "instinct is to verify the person who sent the email. That is the wrong check: a "
        "solicitor's identity is not in question, their authority to act is, and that is "
        "established by a letter of authority rather than by anything about them."),
  ("p", "The system's contribution here is modest and useful: recognise that the requester and "
        "the subject are different people, flag it as a third-party request, and present the "
        "handler with the two questions separately rather than one merged one."),
  ("h3", "Deleting what verification collected"),
  ("p", "Anything gathered for verification &mdash; a document, an answer, a scan somebody sent "
        "unprompted &mdash; is deleted once the request is closed, and that deletion is recorded. "
        "It is a small discipline and it prevents the specific irony of a data protection process "
        "accumulating a folder of identity documents."),
  ("p", "Next: gathering the data."),
 ],
},
{
 "slug": "how-the-data-gets-gathered",
 "title": "How the data gets gathered",
 "nav": "How it is gathered",
 "read": 5, "words": 750,
 "desc": ("Asking every system rather than the obvious ones, recording nothing as an answer, and "
          "the systems that need a person."),
 "og": ("An unasked system is not the same as an empty one. Recording \"nothing held\" as an "
        "explicit answer is what makes the package defensible."),
 "abstract": ("Why every system is asked rather than the obvious ones, why \"nothing\" is "
              "recorded as an answer, the register that makes this possible, and the systems "
              "that need a person."),
 "lede": ("Gathering looks like the bulk of the work and is mostly a fan-out. The part that "
          "actually determines whether the response is complete is knowing what to ask, which "
          "means having written down every system that holds anything about a person &mdash; and "
          "almost nobody has."),
 "tags": ["subject access request", "data mapping", "GDPR", "integration", "completeness",
          "serverless"],
 "takeaways": [
  "The system register is the product. Everything else is a fan-out over it.",
  "Ask every system, including the ones you expect to hold nothing.",
  "Record \"nothing held\" explicitly; an unasked system is not an empty one.",
  "Systems with no export API get a dated task for a named person.",
  "Backups and logs hold personal data and are frequently forgotten.",
 ],
 "blocks": [
  ("h2", "The register"),
  ("p", "One row per system that could hold anything about a person: what it holds, how to ask "
        "it, who owns it, and whether the ask is automatic or manual. Building it is a couple of "
        "hours of asking around, and it is the entire difference between a response that is "
        "complete and one that is merely plausible."),
  ("table", ["System", "Holds", "Ask"], [
   ["E-commerce", "Orders, addresses, payment references", "API"],
   ["Email marketing", "Address, subscription state, opens", "API"],
   ["Helpdesk", "Tickets, conversations, internal notes", "API"],
   ["Accounting", "Invoices, payment records", "Manual export"],
   ["Booking tool", "Appointments, notes", "Manual"],
   ["Shared drive", "Whatever somebody filed there", "Search, manual"],
   ["Backups", "Everything, historically", "Documented, not searched"],
  ]),
  ("p", "The last two rows are the ones that get left out and both matter. A shared drive with a "
        "folder of customer correspondence is holding personal data whether or not anybody thinks "
        "of it as a system, and backups hold everything that was ever deleted, which is a fact "
        "that has to be stated rather than searched."),
  ("h2", "Asking"),
  ("fig", ("chain", {
    "entry": {"title": "A verified request", "sub": ["clock running"], "icon": "shield"},
    "steps": [
      {"title": "Fan out to every system", "sub": ["from the register"], "icon": "filter",
       "side": {"title": "System register", "sub": ["every one, always"], "icon": "doc"}},
      {"title": "Automatic?", "sub": ["an API exists"], "icon": "branch",
       "exit": {"title": "A dated task", "sub": ["to a named person"], "icon": "person",
                "label": "no"}},
      {"title": "Fetch what it holds", "sub": ["by every identifier"], "icon": "database"},
      {"title": "Anything found?", "icon": "branch",
       "exit": {"title": "Record 'nothing held'", "sub": ["an answer, not a gap"], "icon": "check",
                "label": "no"}},
      {"title": "Add to the package", "sub": ["with its source"], "icon": "log"}],
    "note": "Every system produces an answer, including nothing. A missing answer is not one."}),
   "How the gathering runs. The explicit nothing-held record is what lets the package say it is "
   "complete rather than hoping.",
   "How data is gathered from every system for a request",
   "A vertical chain of five steps entered by a box labelled A verified request, with the clock "
   "running. Step one fans out to every system from the register, always all of them. Step two "
   "asks whether the system can be asked automatically because an API exists; if not it exits to "
   "A dated task assigned to a named person. Step three fetches what it holds, searching by every "
   "identifier. Step four asks whether anything was found; nothing exits to Record nothing held, "
   "which is an answer rather than a gap. Step five adds it to the package with its source. A "
   "note says every system produces an answer including nothing, and a missing answer is not one."),
  ("h3", "By every identifier"),
  ("p", "A person is in different systems under different keys: an email address in one, a "
        "customer number in another, a phone number in a third, and quite possibly a second email "
        "address they used once. Searching each system by only the identifier the request arrived "
        "with will miss data that is genuinely held."),
  ("p", "So the gather step starts by assembling every identifier known for that person &mdash; "
        "from the matching work in the duplicate merger, if that exists &mdash; and searches each "
        "system by all of them. It is the difference between a response that is complete and one "
        "that is complete for one email address."),
  ("h3", "Nothing held is an answer"),
  ("p", "Recording an explicit \"asked, holds nothing\" per system is what lets the package say, "
        "credibly, that these seven systems were checked and three of them hold nothing. Without "
        "it the package contains four sections and no evidence that the other three were "
        "considered at all."),
  ("p", "It also catches the specific failure where a system's API silently returns empty because "
        "the query was wrong: a system that returns nothing for every request, month after "
        "month, in a business with customers, is worth checking rather than trusting."),
  ("h2", "The manual ones"),
  ("fig", ("strip", {
    "stages": [
      {"title": "No API", "sub": ["about half of them"], "icon": "stop"},
      {"title": "A dated task", "sub": ["to a named person"], "icon": "person"},
      {"title": "Due in 3 days", "sub": ["well inside the clock"], "icon": "clock"},
      {"title": "They attach it", "sub": ["or say nothing held"], "icon": "doc"},
      {"title": "Same record", "sub": ["as an automatic answer"], "icon": "check"}],
    "title": "HALF OF EVERY REGISTER IS MANUAL",
    "note": "Giving them three days of a thirty-day clock is what keeps the review unhurried."}),
   "How manual systems are handled. Setting internal deadlines well inside the statutory one is "
   "what preserves time for the review, which is where errors are expensive.",
   "How systems without an export API are handled in a data request",
   "A horizontal row of five boxes. No API: about half of them. A dated task: to a named person. "
   "Due in three days: well inside the clock. They attach it: or say nothing held. Same record: as "
   "an automatic answer. A note says giving them three days of a thirty-day clock is what keeps "
   "the review unhurried."),
  ("p", "Three days is deliberately aggressive against a thirty-day statutory window, and the "
        "reason is that the review in Part 5 is the part that needs unhurried attention. A "
        "package assembled on day four leaves three weeks of margin; one assembled on day "
        "twenty-four leaves a rushed review, which is exactly when something that should have "
        "been redacted is not."),
  ("p", "Next: the review and the package."),
 ],
},
{
 "slug": "how-a-package-gets-reviewed",
 "title": "How a package gets reviewed",
 "nav": "How it is reviewed",
 "read": 5, "words": 740,
 "desc": ("What has to be redacted and why, the deletion plan that is executed rather than "
          "automatic, and the numbers that show whether the process is under control."),
 "og": ("Third-party data, internal notes about other people, and anything that would reveal "
        "somebody else. The review is the only step where judgement is genuinely required."),
 "abstract": ("What has to be redacted before a package leaves, why deletion is a plan a person "
              "executes, what the response letter says, and the numbers worth watching."),
 "lede": ("The review is the only part of this system that genuinely requires a person, and it is "
          "the part where the whole thing can go wrong in a way nothing else can fix: a package "
          "sent containing somebody else's personal data is a breach caused by responding to a "
          "request about privacy."),
 "tags": ["subject access request", "redaction", "GDPR", "deletion", "reporting", "serverless"],
 "takeaways": [
  "Third-party personal data comes out. That is the main reason a person reviews.",
  "Internal notes are usually disclosable and frequently uncomfortable, which is not a reason to withhold.",
  "Deletion is a plan naming every record, executed by a person, and recorded.",
  "The response says what was found, what was withheld and why, and what happens next.",
  "The number to watch is days used, and it should be well under the limit.",
 ],
 "blocks": [
  ("h2", "What comes out"),
  ("fig", ("chain", {
    "entry": {"title": "The assembled package", "sub": ["everything held"], "icon": "doc"},
    "steps": [
      {"title": "Third-party data?", "sub": ["another person named"], "icon": "branch",
       "exit": {"title": "Redact", "sub": ["and note that you did"], "icon": "lock",
                "label": "yes"}},
      {"title": "Would it reveal somebody?", "sub": ["even without a name"], "icon": "branch",
       "exit": {"title": "Consider carefully", "sub": ["a judgement, recorded"], "icon": "person",
                "label": "maybe"}},
      {"title": "An internal note about them?", "sub": ["uncomfortable but theirs"], "icon": "branch",
       "exit": {"title": "Usually include it", "sub": ["awkward is not exempt"], "icon": "check",
                "label": "yes"}},
      {"title": "Legally privileged?", "sub": ["genuinely, not conveniently"], "icon": "branch",
       "exit": {"title": "Withhold and say so", "sub": ["with the reason"], "icon": "shield",
                "label": "yes"}},
      {"title": "Release", "sub": ["with a covering note"], "icon": "email"}],
    "note": "Every withholding is recorded with a reason. Silent omission is the thing to avoid."}),
   "What the review is actually deciding. Three of the four branches lead to inclusion or a "
   "recorded decision, which is the correct balance.",
   "How a data request package is reviewed before release",
   "A vertical chain of five steps entered by a box labelled The assembled package, containing "
   "everything held. Step one asks whether there is third-party data naming another person; if so "
   "it exits to Redact and note that you did. Step two asks whether something would reveal "
   "somebody even without a name; a maybe exits to Consider carefully, as a recorded judgement. "
   "Step three asks whether there is an internal note about the requester, uncomfortable but "
   "theirs; if so it exits to Usually include it, because awkward is not exempt. Step four asks "
   "whether anything is genuinely legally privileged rather than conveniently so; if so it exits "
   "to Withhold and say so, with the reason. Step five releases with a covering note. A note says "
   "every withholding is recorded with a reason and silent omission is the thing to avoid."),
  ("h3", "Internal notes"),
  ("p", "The most common source of discomfort and the one where the answer is usually clear. A "
        "support note saying \"customer was extremely rude on the phone\" is personal data about "
        "that customer, they are generally entitled to it, and finding it embarrassing is not an "
        "exemption."),
  ("p", "The useful side effect is cultural rather than technical: businesses that run this "
        "process for a while write internal notes differently, because everybody understands that "
        "the customer may read them. That is a better outcome than any redaction policy."),
  ("h3", "Third-party data"),
  ("p", "The genuine reason a person reviews. A message thread where two customers were both "
        "discussed, a delivery note listing a neighbour who took the parcel, an internal note "
        "naming another employee &mdash; all of those contain somebody else's personal data, and "
        "sending them is a breach committed while responding to a privacy request."),
  ("p", "The redaction is recorded rather than silent: \"parts of two messages have been redacted "
        "because they contain information about another person\" is a sentence the response "
        "letter carries, and it is both more honest and more defensible than a package with "
        "unexplained gaps."),
  ("h2", "Deletion is a plan"),
  ("fig", ("strip", {
    "stages": [
      {"title": "The plan", "sub": ["every record, every system"], "icon": "doc"},
      {"title": "What must be kept", "sub": ["invoices, suppression"], "icon": "lock"},
      {"title": "Executed by a person", "sub": ["system by system"], "icon": "person"},
      {"title": "Confirmed", "sub": ["read back where possible"], "icon": "check"},
      {"title": "Recorded", "sub": ["what went, what stayed, why"], "icon": "log"}],
    "title": "DELETION IS NOT A BUTTON",
    "note": "The second box is where most of the thinking is: some things genuinely must be kept."}),
   "How a deletion request is executed. The plan is generated; the execution is human, and the "
   "record of what was kept is as important as the record of what went.",
   "How a deletion request is planned and executed",
   "A horizontal row of five boxes. The plan: every record in every system. What must be kept: "
   "invoices and suppression records. Executed by a person: system by system. Confirmed: read back "
   "where possible. Recorded: what went, what stayed, and why. A note says the second box is where "
   "most of the thinking is, because some things genuinely must be kept."),
  ("p", "The retention exceptions are the substantive part. Invoices usually have to be kept for "
        "tax purposes for years. The suppression record from the consent keeper has to survive or "
        "the person will be emailed again. Neither of those is a refusal to delete; both are "
        "specific, statable reasons that belong in the response."),
  ("h2", "The response and the numbers"),
  ("callout", "What the response letter says", [
   "<strong>What we found,</strong> listed by source, in plain terms.",
   "<strong>What we checked and found nothing in,</strong> named, so the scope is visible.",
   "<strong>What we redacted and why</strong> &mdash; not what it said, but that it was removed "
   "and the reason.",
   "<strong>What we are keeping and why,</strong> for a deletion request, with the specific "
   "obligation.",
   "<strong>What happens next,</strong> and how to complain if they are unhappy with the "
   "response.",
  ]),
  ("fig", ("strip", {
    "stages": [
      {"title": "Requests", "sub": ["6 this year"], "icon": "inbox"},
      {"title": "Median recognition", "sub": ["under an hour"], "icon": "clock"},
      {"title": "Median days used", "sub": ["9 of 30"], "icon": "counter"},
      {"title": "Late", "sub": ["0"], "icon": "check"},
      {"title": "Systems with no API", "sub": ["5 of 11"], "icon": "alarm"}],
    "title": "ONE YEAR OF REQUESTS",
    "note": "The last number is the one to work on. It is what makes the middle number nine."}),
   "A year of requests in five numbers. The manual-system count is the lever: reducing it is what "
   "reduces days used, which is what preserves review time.",
   "One year of data requests summarised in five numbers",
   "A horizontal row of five boxes. Requests: six this year. Median recognition: under an hour. "
   "Median days used: nine of thirty. Late: none. Systems with no API: five of eleven. A note says "
   "the last number is the one to work on, because it is what makes the middle number nine."),
  ("p", "Days used is the headline and nine out of thirty is comfortable. The interesting "
        "relationship is with the last number: each manual system adds days, and a business that "
        "moves two of those five onto an export path will see the median drop by several days "
        "without anybody trying harder."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="message screened",
 volumes=[(2000, "2,000 messages"), (8000, "8,000 messages"), (30000, "30,000 messages")],
 read_each=0.0006, msgs_each=0.02,
 lede=("The cost here is screening inbound mail rather than handling requests, because requests "
       "are rare and messages are not. Eight thousand messages a month is a busy small-business "
       "inbox. Here is where each cent goes."),
 takeaway_extra=("Cheap filters remove auto-replies and bulk mail before any model call, which is "
                 "most of the volume."),
 risks=[
  "<strong>Screening every message with a model.</strong> Auto-replies, bulk mail and internal "
  "threads are a large fraction of an inbox and can be excluded structurally for nothing.",
  "<strong>Storing gathered packages indefinitely.</strong> A package contains everything you "
  "hold about a person, which is the last thing to keep a spare copy of. Delete it a set period "
  "after the response is sent.",
  "<strong>Log retention left at never.</strong> Logs from a system that reads inbound mail are "
  "exactly the logs you least want kept forever, quite apart from the cost.",
 ],
 per_unit_note=("The read cost is one short model call per message that survives the cheap "
                "filters, which is a minority of an inbox. Handling an actual request costs "
                "almost nothing because there are so few of them."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="dr2",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the two timestamps, and the deletion of the package itself."),
 outside=[
  {"title": "SES inbound", "sub": ["the monitored inboxes"], "icon": "email"},
  {"title": "Your systems", "sub": ["from the register"], "icon": "database"},
  {"title": "SES outbound", "sub": ["the response"], "icon": "email"}],
 inside=[
  {"title": "S3 + SQS", "sub": ["packages,", "one request queue"], "icon": "bucket"},
  {"title": "Lambda x3", "sub": ["recognise, gather,", "review"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["requests, sources"], "icon": "database"}],
 note="us-east-1. One account. The package is deleted a set period after the response is sent.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. SES inbound, receiving mail from the "
  "monitored inboxes. Your systems, listed in the register. And SES outbound, carrying the "
  "response. Inside the account, three groups. S3 holding assembled packages and SQS carrying one "
  "request queue. Three Lambda functions named recognise, gather and review. And two DynamoDB "
  "tables named requests and sources. A note gives the region as us-east-1, one account, and "
  "states that the package is deleted a set period after the response is sent."),
 functions=[
  ["<code>dr-recognise</code>", "S3 ObjectCreated (SES)",
   "Cheap filters, one Bedrock call, records both timestamps", "20s / 512&nbsp;MB"],
  ["<code>dr-gather</code>", "SQS request queue",
   "Fans out to every source; records nothing-held explicitly", "300s / 1024&nbsp;MB"],
  ["<code>dr-review</code>", "Function URL",
   "Serves the review, records redactions, releases the package", "30s / 1024&nbsp;MB"]],
 roles=[
  ["<code>dr-recognise-role</code>",
   "<code>s3:GetObject</code>, <code>bedrock:InvokeModel</code>, <code>dynamodb:PutItem</code>",
   "The mail prefix; one model arn; the requests table"],
  ["<code>dr-gather-role</code>",
   "<code>secretsmanager:GetSecretValue</code>, <code>s3:PutObject</code>",
   "One secret per source system; the packages prefix"],
  ["<code>dr-review-role</code>",
   "<code>s3:GetObject</code>/<code>DeleteObject</code>, <code>ses:SendRawEmail</code>",
   "The packages prefix; one verified identity"]],
 tables=[
  ("Table: requests",
   "PK   request_id        S   req_2026_08_08_b4e1\n"
   "     received_at       S   2026-08-08T09:12:00Z   -- the clock runs from HERE\n"
   "     recognised_at     S   2026-08-08T09:47:00Z   -- how well the recogniser works\n"
   "     kind              S   access | deletion | correction | objection\n"
   "     subject           S   the person the data is about\n"
   "     requester         S   usually the same; different for third-party\n"
   "     verification      S   authenticated | address_on_file | asked | pending\n"
   "     clock_paused      L   [{from, to, reason}]\n"
   "     due_at            S   computed from received_at plus pauses\n"
   "     package_key       S   s3://packages/req_...  -- deleted after response\n"
   "     redactions        L   [{source, reason}]\n"
   "     withheld          L   [{item, basis}]\n"
   "     responded_at      S   when a person released it\n\n"
   "Two timestamps, always. A schema with only one will eventually compute a\n"
   "deadline from the wrong date."),
  ("Table: sources",
   "PK   request_id        S   req_2026_08_08_b4e1\n"
   "SK   system            S   helpdesk\n"
   "     method            S   api | manual\n"
   "     asked_at          S   2026-08-08T09:48:00Z\n"
   "     answered_at       S   2026-08-08T09:48:04Z\n"
   "     result            S   found | nothing_held | failed\n"
   "     item_count        N   14\n"
   "     assigned_to       S   for manual sources\n\n"
   "`nothing_held` is a first-class result. A row missing entirely means the\n"
   "system was never asked, which is a different and worse thing.")],
 inbound=[
  "<strong>SES receipt rules</strong> on the monitored addresses write to S3, and the S3 event "
  "fires recognition. More than one inbox is normal: sales, support and info all receive these.",
  "<strong>The manual entry form</strong> is a Function URL behind a signed staff link, and its "
  "date field defaults to today with an explicit prompt to change it if the request arrived "
  "earlier.",
  "<strong>Each source system has its own secret</strong>, read only by <code>dr-gather</code>, "
  "and read-only scopes wherever the system offers them.",
  "<strong>The package is deleted</strong> a configured period after the response is sent. It is "
  "a complete copy of everything you hold about one person and there is no reason to keep a "
  "second one."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "asked one narrow question about whether a message is a data request and which kind.",
  "<strong>Cheap filters run first.</strong> Auto-replies, bulk mail and internal senders are "
  "excluded structurally, which removes most of an inbox before any model call.",
  "<strong>Output is a JSON schema</strong> with a kind and a confidence, both nullable. Low "
  "confidence produces the clarifying question rather than a decision.",
  "<strong>It never reads the gathered data.</strong> The model sees inbound messages only; the "
  "package is never sent to a model, which would be a strange thing to do with somebody's "
  "complete personal data.",
  "<strong>Redaction is human.</strong> Identifying third-party data is a judgement with a breach "
  "on the other side of getting it wrong."],
 gotchas=[
  "Record both received_at and recognised_at. The clock runs from arrival, and a schema with one "
  "timestamp will eventually compute a deadline from the wrong date.",
  "Search every system by every identifier you hold for that person, not just the address the "
  "request came from.",
  "Record nothing_held explicitly. A missing source row means the system was never asked, which "
  "is completely different.",
  "Do not ask for identity documents by default. It is disproportionate, it collects sensitive "
  "data you then have to delete, and it reads as obstruction.",
  "Delete the assembled package after responding. It is the single most sensitive object the "
  "business will ever hold about one person."],
))
