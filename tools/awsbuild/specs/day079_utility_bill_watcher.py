"""Day 79 -- 2026-07-12 -- Utility bill watcher."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "utility-bill-watcher"
NAME = "Utility bill watcher"

SPEC = {
 "slug": SLUG, "date": "2026-07-12", "name": NAME,
 "tagline": ("Every electricity, gas, water and waste bill gets read as it arrives, compared "
             "with the same month last year and with the rate you actually agreed, and only "
             "the ones that moved get mentioned."),
 "lede": ("A small system that reads each utility bill for each site as it arrives, pulls out "
          "the usage, the unit rate and the standing charge, and compares all three against "
          "your own history and your contracted rate. A bill that behaved gets filed silently. "
          "A bill that did not gets one message saying which of the three moved and by how "
          "much. Seven posts on the same system -- one diagram at a time -- with a cost "
          "breakdown and an engineering reference at the end."),
 "keywords": ["utility bills", "energy costs", "cost control", "multi-site", "AWS Textract",
              "serverless"],
 "icons": ["doc", "chart", "alarm"],
 "faq": [
  ("What is a utility bill watcher?",
   "A small serverless system that reads every utility bill as it arrives, extracts the usage, "
   "the unit rate and the standing charge, and compares each against your own history for that "
   "meter and against the rate you contracted. Bills that behave are filed without a word; "
   "bills that moved produce one message naming what changed."),
  ("Why compare three things rather than just the total?",
   "Because the total tells you nothing about what to do. A bill that doubled because usage "
   "doubled is an operational problem -- something is running that should not be. A bill that "
   "doubled because the unit rate moved is a contract problem. The response is completely "
   "different, and a total cannot tell them apart."),
  ("Does it need a supplier API?",
   "No. Bills arrive the way they already arrive -- a PDF attached to an email, or a portal "
   "download dropped into a folder. Textract reads them, and the extraction is grounded by the "
   "meter list you keep, so a model matches to a known meter rather than inventing one."),
  ("What about estimated readings?",
   "They are detected and handled separately. An estimated bill is compared but never used to "
   "update the baseline, because a run of estimates followed by a real reading produces a "
   "catch-up bill that would otherwise look like a crisis."),
  ("What does it cost to run?",
   "A few dollars a month even across a dozen sites. Nothing is always-on. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "utility-bill-watcher-on-aws",
 "title": "A utility bill watcher on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 930,
 "desc": ("Reads every utility bill as it arrives, compares usage, unit rate and standing "
          "charge against your history and your contract, and mentions only what moved. AWS, "
          "about $3 a month."),
 "og": ("Three numbers per bill -- usage, unit rate, standing charge -- each compared against "
        "your own history and your contracted rate. Only the ones that moved get mentioned."),
 "abstract": ("The whole system on one page -- a reader, a comparer and a reporter -- and the "
              "decision that makes it useful: compare three numbers separately rather than "
              "one total."),
 "lede": ("Utility bills are the classic small-business blind spot: too small to justify "
          "attention individually, too numerous to check, and just variable enough that a bad "
          "one looks like a normal one. A cafe with three sites gets roughly a hundred and "
          "forty utility bills a year. Nobody reads a hundred and forty bills. So the tariff "
          "that rolled onto a variable rate in March gets noticed in September, and the "
          "freezer that has been running with a failing door seal since April never gets "
          "noticed at all. This post walks through a small system that reads all of them."),
 "tags": ["utility bills", "energy costs", "cost control", "multi-site", "human in the loop",
          "serverless"],
 "takeaways": [
  "Bills arrive the way they already do: a PDF in an email, or a portal download in a folder.",
  "Three numbers are pulled from each: usage, unit rate, and standing charge.",
  "Each is compared separately -- against the same period last year and against your contract.",
  "Only a bill where something moved produces a message. Most produce nothing.",
  "Designed on AWS for about $3 a month across a dozen sites.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Bills", "sub": ["email PDF or folder"], "icon": "doc"},
      {"title": "Meter list", "sub": ["sites, rates, contracts"], "icon": "chart"},
      {"title": "Whoever pays", "sub": ["hears only what moved"], "icon": "person"}],
    "inside": [
      {"title": "Reader", "sub": ["usage, unit rate,", "standing charge"], "icon": "ocr"},
      {"title": "Comparer", "sub": ["vs last year,", "vs the contract"], "icon": "counter"},
      {"title": "Reporter", "sub": ["name what moved,", "and by how much"], "icon": "alarm"}],
    "edges": [{"from": 0, "to": 0, "label": "bills in"},
              {"from": 1, "to": 1, "label": "which meter, what rate"},
              {"from": 2, "to": 2, "label": "only what moved", "up": True}],
    "note": "A bill that behaved is filed and never mentioned. That is most of them."}),
   "Three things outside the account, three pieces inside it. Bills arrive however they "
   "already do, the meter list says which meter and what rate was agreed, and only movement "
   "produces a message.",
   "System: bills in, meter list as reference, three pieces inside AWS",
   "Three boxes across the top sit outside the AWS account. On the left, Bills: arriving as a "
   "PDF attached to an email or as a portal download dropped in a folder. In the middle, Meter "
   "list: the sites, the meter numbers, the contracted unit rates and the contract end dates. "
   "On the right, Whoever pays: the person who hears only about bills where something moved. "
   "Each connects by an arrow to the AWS account container below. Bills flow down into the "
   "account. The meter list feeds in to say which meter a bill belongs to and what rate was "
   "agreed. Inside the AWS account are three components in a row. On the left, the Reader, "
   "which pulls the usage, the unit rate and the standing charge out of each bill. In the "
   "middle, the Comparer, which sets each of those three against the same period last year and "
   "against the contracted rate. On the right, the Reporter, which names what moved and by how "
   "much. A note at the bottom says a bill that behaved is filed and never mentioned, and that "
   "this is most of them."),
  ("h3", "What you set up once (the outside)"),
  ("ul", [
   "<strong>A place for bills to land.</strong> A dedicated address that suppliers already "
   "email, or a folder that a portal download gets dropped into. Both are covered in Part 2. "
   "Nobody changes how bills arrive; that is the whole point.",
   "<strong>A meter list.</strong> One tab: each meter number, which site it belongs to, what "
   "it supplies, the contracted unit rate and standing charge, and when the contract ends. "
   "Most small businesses do not have this written down anywhere, and building it is genuinely "
   "the hardest part of the project &mdash; and worth doing even if you build nothing else.",
   "<strong>A tolerance line.</strong> How far a number has to move before it is worth "
   "mentioning. Usage swings with weather and trade, so the default is generous: twenty-five "
   "per cent against the same period last year. Rates are different &mdash; a unit rate that "
   "differs from the contract at all is worth a message, because it is either an error or a "
   "contract that rolled over.",
  ]),
  ("h3", "What runs on every bill (the inside)"),
  ("ul", [
   "<strong>The reader.</strong> Turns a PDF into three numbers plus the meter number and the "
   "period. Utility bills are visually chaotic and vary wildly between suppliers, so this is "
   "where Textract and a model earn their keep &mdash; but the meter number is matched against "
   "your list rather than trusted from the page, and a number the reader is not confident about "
   "is left null.",
   "<strong>The comparer.</strong> Three comparisons, each against two references. Usage "
   "against the same period last year for that meter, and against the previous period. Unit "
   "rate against the contract. Standing charge against the contract. Each comparison is a "
   "subtraction, and each carries the two numbers that produced it.",
   "<strong>The reporter.</strong> Builds a message only when something moved past its "
   "tolerance, and the message says which of the three moved. That distinction is the entire "
   "value: \"usage up 40% on last July\" sends somebody to look at a freezer, and \"unit rate "
   "up 62% against contract\" sends somebody to phone a supplier. Those are different days.",
  ]),
  ("h2", "One bill, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Arrived", "sub": ["PDF, any supplier"], "icon": "doc"},
      {"title": "Read", "sub": ["3 numbers, 1 meter"], "icon": "ocr"},
      {"title": "Matched", "sub": ["to a meter you know"], "icon": "search"},
      {"title": "Compared", "sub": ["history and contract"], "icon": "counter"},
      {"title": "Filed", "sub": ["or one message"], "icon": "check"}],
    "title": "ONE UTILITY BILL, END TO END",
    "note": "Four of the five stages are silent. The fifth usually is too."}),
   "The same system as one line. The output of most bills is a row in a history table and "
   "nothing else at all.",
   "One utility bill from arrival to filing, in five stages",
   "A horizontal row of five boxes joined by arrows. Arrived: a PDF from any supplier. Read: "
   "three numbers and one meter number extracted. Matched: to a meter on your own list. "
   "Compared: against history and against the contract. Filed: silently, or with one message. "
   "A note says four of the five stages are silent and the fifth usually is too."),
  ("h2", "In plain words"),
  ("p", "The electricity bill for your Hitchin site arrives on the 12th. The reader pulls out "
        "4,180 kWh, a unit rate of 24.1p and a standing charge of 48p a day, on meter "
        "1200034557. That meter is on your list, it is Hitchin, and the contract says 24.1p "
        "until November. Usage last July on the same meter was 3,980 kWh, so this is five per "
        "cent up &mdash; well inside the band. Every number behaves. The bill is filed, the "
        "history row is written, and nobody hears anything."),
  ("p", "The August bill for the same meter comes in at 6,240 kWh. Same rate, same standing "
        "charge, but usage is up fifty-seven per cent on last August. One message goes out: "
        "\"Hitchin electricity: usage 6,240 kWh, up 57% on Aug 2025 (3,970). Rate and standing "
        "charge unchanged.\" That sentence is doing something specific &mdash; it has already "
        "ruled out the two commercial explanations, so the person reading it knows immediately "
        "that something at the site is drawing power. It turned out to be a walk-in fridge with "
        "a door that was not sealing, which had been running flat out since the middle of "
        "July."),
  ("callout", "Design rules that shaped every decision", [
   "Three numbers, compared separately. A total cannot distinguish an operational problem from "
   "a contract problem, and those need different people.",
   "The meter list is the source of truth. A bill for a meter that is not on the list is a "
   "question, not a new meter.",
   "Compare against the same period last year, not last month. Utilities are seasonal and "
   "month-on-month comparison generates constant noise.",
   "An estimated reading is compared but never becomes the baseline. A run of estimates "
   "followed by a real reading produces a catch-up that would look like a crisis.",
   "Rate tolerance is near zero. Usage moves for a hundred honest reasons; a unit rate that "
   "differs from the contract does not.",
   "Nothing is ever paid, disputed or cancelled by the system. It reads and it tells you.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The reason nobody checks utility bills is not laziness; it is that checking one "
        "properly requires last year's bill for the same meter, the contract, and ten minutes. "
        "Multiply by four utilities and three sites and it is a day a month for a saving that "
        "is usually zero. So it does not happen, and the two things that would have been caught "
        "&mdash; the tariff that rolled onto a variable rate and the equipment that started "
        "drawing double &mdash; both run for months."),
  ("p", "The shape above makes that ten minutes cost nothing and applies it to every bill. It "
        "spends most of its effort on the boring half, which is matching a bill to the right "
        "meter and reading three numbers off a page that a different supplier lays out "
        "differently every time. The interesting half &mdash; the comparison &mdash; is three "
        "subtractions."),
  ("p", "The next four posts walk through each piece: how a bill arrives and gets read, how it "
        "gets matched to a meter, how a change gets reported, and how the history builds into "
        "something worth looking at. One diagram per post, a cost breakdown, and an engineering "
        "reference at the end."),
 ],
},
{
 "slug": "how-a-utility-bill-gets-read",
 "title": "How a utility bill gets read",
 "nav": "How it is read",
 "read": 6, "words": 900,
 "desc": ("Two lanes in, Textract on a page that every supplier lays out differently, and the "
          "three numbers plus a meter number that come out -- or do not."),
 "og": ("Utility bills are visually chaotic and vary by supplier. What makes extraction safe "
        "is that the meter number is matched to your list and unreadable numbers stay null."),
 "abstract": ("Two lanes in, and a page that every supplier lays out differently. What makes "
              "extraction safe is that the meter number is matched against your own list and "
              "an unreadable figure stays null."),
 "lede": ("A utility bill is one of the least standardised documents in ordinary business "
          "life. Two suppliers of the same commodity will put the usage in different units, "
          "the rate on a different page, and the standing charge inside a table that is only a "
          "table visually. This post is about pulling four reliable values out of that, and "
          "about being honest when it cannot."),
 "tags": ["utility bills", "Amazon Textract", "document extraction", "AWS Bedrock", "SES inbound",
          "serverless"],
 "takeaways": [
  "Two lanes: a supplier email with a PDF attached, and a folder for portal downloads.",
  "Textract does the layout; the model does the interpretation; neither picks the meter.",
  "The meter number is matched against your list, never trusted from the page alone.",
  "A number the reader is not confident about stays null and produces a question.",
  "Units are normalised on the way in, because kWh, therms and cubic metres all show up.",
 ],
 "blocks": [
  ("h2", "Two lanes in"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Supplier email", "sub": ["PDF attached"], "icon": "email", "label": "attach"},
      {"title": "Portal download", "sub": ["dropped in a folder"], "icon": "bucket",
       "label": "file"},
      {"title": "Photo of a paper bill", "sub": ["the last few suppliers"], "icon": "image",
       "label": "image"}],
    "target": {"title": "One bill record", "sub": ["meter, period, usage,", "rate, standing"],
               "icon": "database",
               "then": {"title": "Comparer", "sub": ["history and contract"], "icon": "counter"}},
    "note": "Every lane ends in the same five fields, or in a question about the one that is missing."}),
   "Three ways a bill turns up and one record shape. The photo lane exists because a small "
   "number of suppliers still post paper, and excluding them would leave a permanent hole in "
   "the history.",
   "Three bill lanes converging on one bill record",
   "Three boxes stacked on the left. Supplier email, with a PDF attached. Portal download, "
   "dropped into a folder. And Photo of a paper bill, for the last few suppliers who still "
   "post. Their arrows are labelled attach, file and image, converging on One bill record "
   "holding the meter, the period, the usage, the unit rate and the standing charge. Below it, "
   "connected by a downward arrow, is the Comparer, which checks against history and the "
   "contract. A note says every lane ends in the same five fields, or in a question about the "
   "one that is missing."),
  ("h2", "What comes out of the page"),
  ("pre", "meter          1200034557        matched to your list, not trusted from the page\n"
          "period_start   2026-06-11\n"
          "period_end     2026-07-10\n"
          "usage          4180.0            normalised to the meter's own unit\n"
          "unit           kWh               from the meter list, not the bill\n"
          "unit_rate      0.241             per unit, excluding tax\n"
          "standing       0.48              per day, excluding tax\n"
          "estimated      false             read off the bill's own wording\n"
          "total          1128.44           used as a checksum, never as an input"),
  ("h3", "The total is a checksum, not an input"),
  ("p", "Every bill states its own total, and that total should equal usage times rate plus "
        "standing charge times days, plus tax. Recomputing it from the extracted numbers and "
        "comparing is the cheapest possible check on the whole extraction. If they agree to "
        "within a penny or two, all four numbers are almost certainly right. If they do not, "
        "something was misread, and the system knows that before it produces a comparison."),
  ("p", "This is the same trick as the count sheet's written total in the cash reconciler, and "
        "it works for the same reason: the document contains a redundant derived value that a "
        "human already relies on. Using it costs nothing and removes almost every category of "
        "silent extraction error."),
  ("h2", "The read, step by step"),
  ("fig", ("chain", {
    "entry": {"title": "Bill lands", "sub": ["any of three lanes"], "icon": "doc"},
    "steps": [
      {"title": "Store the original", "sub": ["S3, kept for the record"], "icon": "bucket"},
      {"title": "Seen this bill?", "sub": ["supplier + meter + period"], "icon": "branch",
       "side": {"title": "DynamoDB bills", "sub": ["conditional write"], "icon": "database"},
       "exit": {"title": "Same bill", "sub": ["file the copy, stop"], "icon": "stop",
                "label": "duplicate"}},
      {"title": "Pull the layout", "sub": ["Textract forms + tables"], "icon": "ocr"},
      {"title": "Read the five fields", "sub": ["one Bedrock call"], "icon": "model",
       "side": {"title": "Meter list", "sub": ["meters and units"], "icon": "chart"}},
      {"title": "Total reconciles?", "sub": ["usage x rate + standing"], "icon": "branch",
       "exit": {"title": "Ask a human", "sub": ["attach the page"], "icon": "person",
                "label": "mismatch"}},
      {"title": "Hand to the comparer", "sub": ["five clean fields"], "icon": "queue"}],
    "note": "The duplicate test is before Textract, because suppliers resend bills constantly."}),
   "One bill, end to end. The duplicate test runs before any paid extraction, and the bill's "
   "own stated total is used to check the read before anything is compared.",
   "How a utility bill PDF becomes five clean fields",
   "A vertical chain of six steps inside the AWS account, entered by a box labelled Bill lands, "
   "from any of three lanes. Step one stores the original in S3 for the record. Step two asks "
   "whether this bill has been seen, fingerprinting supplier, meter and period and writing "
   "conditionally to a DynamoDB bills table; a duplicate exits to Same bill, which files the "
   "copy and stops. Step three pulls the layout with Amazon Textract forms and tables. Step "
   "four reads the five fields with a single Bedrock call, grounded by the meter list so meters "
   "and units come from a known set. Step five checks whether the bill's own stated total "
   "reconciles with usage times rate plus standing charge, exiting to Ask a human with the page "
   "attached if it does not. Step six hands five clean fields to the comparer. A note says the "
   "duplicate test runs before Textract because suppliers resend bills constantly."),
  ("h3", "Why suppliers resending matters"),
  ("p", "Utility suppliers resend bills a lot: a reminder with the original attached, a "
        "corrected version, a copy to a second address, a statement that includes last month's "
        "bill as a page. Without a duplicate test in front of the expensive part, a business "
        "with a chatty supplier pays to extract the same bill five times and, worse, may write "
        "the same usage into history five times."),
  ("p", "The fingerprint is supplier, meter and billing period &mdash; not the file, because the "
        "same bill regenerated as a PDF is byte-different. A second copy of a bill already on "
        "record is filed alongside the original and goes no further."),
  ("h2", "Units, and the small disaster they cause"),
  ("ul", [
   "<strong>Gas arrives in at least three units.</strong> Cubic metres on the meter, kWh on the "
   "bill, and therms on some older accounts. A year-on-year comparison that silently mixes them "
   "produces a ten-fold change out of nothing.",
   "<strong>The unit comes from your meter list, not the bill.</strong> The bill is read for a "
   "number; the meter list says what that number is measured in. If a bill states a unit that "
   "disagrees with the list, that is a question, and it is usually a supplier changing how they "
   "present the same meter.",
   "<strong>Water is billed on estimated consumption more often than anything else.</strong> "
   "The estimated flag matters most here, and missing it makes a whole year of water history "
   "meaningless.",
   "<strong>Rates are stored excluding tax.</strong> Bills present rates inclusive and "
   "exclusive inconsistently, and comparing an inclusive rate against an exclusive contract "
   "produces a false alarm every single month.",
  ]),
  ("p", "Next: how a bill gets matched to the right meter, and what happens when it cannot."),
 ],
},
{
 "slug": "how-a-bill-gets-matched-to-a-meter",
 "title": "How a bill gets matched to a meter",
 "nav": "How it is matched",
 "read": 5, "words": 850,
 "desc": ("Why the meter number on the page is a hint rather than an answer, the three-step "
          "match, and what a bill for an unknown meter actually means."),
 "og": ("The meter number on the page is a hint. Matching happens against your own list, and "
        "an unmatched bill is far more often a meter you forgot than a mistake."),
 "abstract": ("The meter number on the page is a hint, not an answer. A three-step match "
              "against your own list, and what an unmatched bill usually turns out to be."),
 "lede": ("This is the shortest post in the series and the one that catches the most money. "
          "Matching a bill to a meter sounds like a lookup, and mostly it is. The interesting "
          "cases are the ones where it fails, because a utility bill that does not match any "
          "meter you know about is almost never an error &mdash; it is usually a supply you "
          "have been paying for and forgot you had."),
 "tags": ["utility bills", "meter matching", "multi-site", "cost control", "DynamoDB",
          "serverless"],
 "takeaways": [
  "The meter number is matched against your list; it is never trusted straight off the page.",
  "Three steps: exact meter number, then supplier account, then site plus utility plus period.",
  "An unmatched bill is a question to a person, and it is often a supply nobody remembered.",
  "A meter that stops producing bills is a louder signal than any single bill.",
  "Matching is recorded, so a supplier reformatting their bill does not silently break history.",
 ],
 "blocks": [
  ("h2", "The three-step match"),
  ("fig", ("chain", {
    "entry": {"title": "Read bill", "sub": ["five fields, one hint"], "icon": "doc"},
    "steps": [
      {"title": "Meter number exact?", "sub": ["digits only, normalised"], "icon": "branch",
       "side": {"title": "Meter list", "sub": ["your own tab"], "icon": "chart"},
       "exit": {"title": "Matched", "sub": ["the usual outcome"], "icon": "check",
                "label": "hit"}},
      {"title": "Supplier account?", "sub": ["account number on the bill"], "icon": "branch",
       "exit": {"title": "Matched", "sub": ["record the new meter format"], "icon": "check",
                "label": "hit"}},
      {"title": "Site + utility + period?", "sub": ["one candidate only"], "icon": "branch",
       "exit": {"title": "Matched, provisionally", "sub": ["ask a human to confirm"],
                "icon": "person", "label": "one"}},
      {"title": "Unmatched", "sub": ["a bill for something", "not on your list"], "icon": "alarm"}],
    "note": "The last box is the interesting one. It usually means a supply nobody remembered."}),
   "Matching in three steps, with a deliberate fourth outcome. An unmatched bill is not a "
   "failure of the system; it is the system finding something.",
   "The three-step match from a bill to a meter on your list",
   "A vertical chain of four steps entered by a box labelled Read bill, carrying five fields "
   "and one meter-number hint. Step one asks whether the meter number matches exactly, "
   "normalised to digits only, against the meter list; a hit exits to Matched, the usual "
   "outcome. Step two asks whether the supplier account number matches, and a hit exits to "
   "Matched while recording the new meter-number format. Step three asks whether the site, "
   "utility and period identify exactly one candidate; one candidate exits to Matched "
   "provisionally, with a human asked to confirm. Step four is Unmatched, a bill for something "
   "not on your list. A note says the last box is the interesting one and usually means a "
   "supply nobody remembered."),
  ("h3", "Why exact matching needs normalising"),
  ("p", "The same meter appears as <code>1200034557</code>, <code>12 0003 4557</code>, "
        "<code>MPAN 1200034557</code> and occasionally with a leading profile class that is "
        "part of a different identifier entirely. Stripping everything but digits and comparing "
        "suffixes handles almost all of it. What it does not handle is a supplier who renumbers "
        "on migration, which is why step two exists."),
  ("h3", "The provisional match"),
  ("p", "Step three is the one that needs care. If a bill is for electricity, at a site you can "
        "identify from the address, for a period where you have exactly one electricity meter "
        "at that site with no bill yet, it is almost certainly that meter. Almost certainly is "
        "not certainly, so the match is made provisionally, the comparison runs, and a person "
        "is asked to confirm before the bill updates the baseline history."),
  ("h2", "What an unmatched bill usually is"),
  ("ul", [
   "<strong>A supply nobody remembered.</strong> An outside light circuit on its own meter, a "
   "water supply to a yard tap, a gas meter for a boiler in a unit you sublet. These get paid "
   "by direct debit for years. Finding one is frequently the single largest saving this whole "
   "system produces.",
   "<strong>A property you no longer occupy.</strong> The second most common, and the most "
   "expensive. A supply at a former site that was never closed keeps billing standing charges "
   "indefinitely.",
   "<strong>A genuinely new meter.</strong> A new site, a split supply, a replaced meter with a "
   "new number. Confirming it adds a row to the list, which is a fifteen-second job that "
   "somebody has to actually do.",
   "<strong>Somebody else's bill.</strong> Rare, but it happens, particularly in shared "
   "buildings. Worth catching before it is paid.",
  ]),
  ("h2", "The bill that never arrives"),
  ("p", "Matching has a mirror image that most systems miss entirely: a meter on your list that "
        "has stopped producing bills. That is a louder signal than almost any single bill, and "
        "it takes a scheduled sweep rather than a reaction to an arrival."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Expected cadence", "sub": ["from the last 6 bills"], "icon": "calendar"},
      {"title": "Overdue", "sub": ["1.5x the usual gap"], "icon": "clock"},
      {"title": "Check the folder", "sub": ["and the spam quarantine"], "icon": "search"},
      {"title": "Ask", "sub": ["one message per meter"], "icon": "bell"},
      {"title": "Catch-up expected", "sub": ["do not treat as a spike"], "icon": "chart"}],
    "title": "A METER THAT STOPPED BILLING",
    "note": "A missing bill becomes a catch-up bill, and a catch-up bill is not a usage spike."}),
   "The sweep for meters that have gone quiet. The last stage matters: when the missing bills "
   "eventually arrive as one catch-up, that is not a spike and must not be reported as one.",
   "How a meter that has stopped producing bills is detected",
   "A horizontal row of five boxes. Expected cadence: derived from the last six bills for that "
   "meter. Overdue: no bill for one and a half times the usual gap. Check the folder: including "
   "the spam quarantine. Ask: one message per meter. Catch-up expected: the eventual bill "
   "should not be treated as a usage spike. A note says a missing bill becomes a catch-up bill "
   "and a catch-up bill is not a usage spike."),
  ("p", "The last stage is a small piece of state that saves a lot of noise. Once a meter is "
        "flagged overdue, the comparer knows that the next bill for it may cover a longer "
        "period, and it compares on a per-day basis rather than a per-bill one. Without that, "
        "every supplier billing hiccup produces a false alarm two months later."),
  ("p", "Next: what the message says when something has genuinely moved."),
 ],
},
{
 "slug": "how-a-change-gets-reported",
 "title": "How a change gets reported",
 "nav": "How it reports",
 "read": 5, "words": 830,
 "desc": ("One message per bill, naming which of the three numbers moved and by how much -- "
          "and why the distinction between usage, rate and standing charge is the whole "
          "message."),
 "og": ("Usage moved, rate moved, or standing charge moved. Each sends a different person to "
        "do a different thing, and saying which is the entire content of the message."),
 "abstract": ("One message per bill, naming which of the three numbers moved. Usage sends "
              "somebody to a site, rate sends somebody to a phone, and saying which is the "
              "whole value of the message."),
 "lede": ("Most cost-monitoring tools report that a bill went up. That is the least useful "
          "possible sentence, because the person reading it now has to do the work of finding "
          "out why, which is the work they did not have time for in the first place. This "
          "system's messages start from the answer."),
 "tags": ["utility bills", "notifications", "cost control", "Amazon SES", "reporting",
          "serverless"],
 "takeaways": [
  "The message names which of the three numbers moved, and says the other two did not.",
  "Usage movement is an operational message; rate movement is a commercial one.",
  "Comparison is against the same period last year, normalised per day.",
  "Contract end dates produce their own message, ninety days out, before anything moves.",
  "A message carries a one-tap \"expected, this is why\" that suppresses the same finding.",
 ],
 "blocks": [
  ("h2", "Three different messages"),
  ("fig", ("system", {
    "outside": [
      {"title": "Site manager", "sub": ["usage questions"], "icon": "person"},
      {"title": "Whoever buys", "sub": ["rate questions"], "icon": "money"},
      {"title": "History", "sub": ["everything, always"], "icon": "chart"}],
    "inside": [
      {"title": "Usage compare", "sub": ["per day, vs last year"], "icon": "counter"},
      {"title": "Rate compare", "sub": ["vs the contract"], "icon": "filter"},
      {"title": "Message builder", "sub": ["names what moved,", "and what did not"], "icon": "doc"}],
    "edges": [{"from": 0, "to": 0, "label": "usage up 57%", "up": True},
              {"from": 1, "to": 1, "label": "rate off contract", "up": True},
              {"from": 2, "to": 2, "label": "every bill, moved or not", "up": True}],
    "note": "Two of these go to different people. Getting that right is most of the design."}),
   "Who hears what. A usage message and a rate message go to different people and cause "
   "different actions, so the system routes them separately rather than sending one person "
   "everything.",
   "How a utility bill change is reported, and to whom",
   "Three boxes across the top outside the AWS account. Site manager, who fields usage "
   "questions. Whoever buys, who fields rate questions. And History, which receives every bill "
   "whether or not anything moved. Inside the account, three components. Usage compare, which "
   "works per day against the same period last year. Rate compare, which works against the "
   "contract. And the Message builder, which names what moved and explicitly says what did not. "
   "Arrows show usage findings going to the site manager, rate findings going to whoever buys, "
   "and every bill going to history regardless. A note says two of these go to different people "
   "and getting that right is most of the design."),
  ("h3", "The usage message"),
  ("callout", "What it says, in order", [
   "<strong>Which meter, in words.</strong> \"Hitchin electricity.\"",
   "<strong>The number and the comparison.</strong> \"6,240 kWh this period, up 57% on the same "
   "period last year (3,970).\"",
   "<strong>What did not move.</strong> \"Unit rate and standing charge are unchanged and match "
   "the contract.\" This sentence is the point &mdash; it converts a cost question into a site "
   "question.",
   "<strong>The per-day figure.</strong> \"201 kWh a day against 128 last year.\" Billing "
   "periods vary by several days and comparing totals without normalising produces regular "
   "false alarms.",
   "<strong>One button.</strong> \"Expected &mdash; here's why\", which records a reason and "
   "suppresses the same finding for that meter for a period.",
  ]),
  ("h3", "The rate message"),
  ("p", "Shorter and more urgent, because the action is a phone call and the clock is running. "
        "\"Hitchin electricity: unit rate 39.2p against a contracted 24.1p. The contract on "
        "record ended 30 June.\" There is no ambiguity about what happened and no investigation "
        "to do; a fixed-term contract ended and the supply rolled onto a variable rate, which "
        "is the single most expensive thing that routinely happens to a small business's energy "
        "bill and the single easiest to miss."),
  ("h2", "The message that arrives before anything moves"),
  ("p", "The best version of the rate message is the one sent ninety days before the contract "
        "ends, when there is still time to do something. It needs no bill at all &mdash; just "
        "the meter list and a scheduled sweep."),
  ("fig", ("strip", {
    "stages": [
      {"title": "T-90 days", "sub": ["contract end approaching"], "icon": "calendar"},
      {"title": "What you pay now", "sub": ["from the last bill"], "icon": "money"},
      {"title": "Annual usage", "sub": ["from your own history"], "icon": "chart"},
      {"title": "One message", "sub": ["to whoever buys"], "icon": "email"},
      {"title": "T-30 reminder", "sub": ["if nothing changed"], "icon": "bell"}],
    "title": "THE CONTRACT-END MESSAGE",
    "note": "It carries your annual usage, which is the number a broker will ask for first."}),
   "The contract-end sweep. It is the only message this system sends that is not caused by a "
   "bill, and it is probably the one that saves the most money.",
   "How an approaching contract end is reported ninety days out",
   "A horizontal row of five boxes. T minus ninety days: a contract end is approaching. What "
   "you pay now: taken from the last bill. Annual usage: taken from your own history. One "
   "message: sent to whoever buys energy. T minus thirty reminder: sent if nothing has changed. "
   "A note says the message carries your annual usage, which is the number a broker will ask "
   "for first."),
  ("p", "Attaching the annual usage figure is a small thing that removes a real obstacle. The "
        "first question any energy broker asks is how much you use, and the reason renewals get "
        "left is that finding out means digging out twelve bills. Having it in the message "
        "turns a two-hour job into a five-minute one, which is the difference between it "
        "happening and not."),
  ("p", "Next: what the accumulated history is actually for."),
 ],
},
{
 "slug": "how-the-utility-history-builds",
 "title": "How the utility history builds",
 "nav": "How history builds",
 "read": 5, "words": 820,
 "desc": ("The row every bill writes, why estimated readings never become the baseline, and "
          "the three things a couple of years of clean history lets you do that you cannot do "
          "otherwise."),
 "og": ("Two years of clean per-meter history is the real output. It makes renewals, "
        "site comparisons and equipment faults visible in a way no single bill ever is."),
 "abstract": ("The row every bill writes, why an estimated reading never becomes the baseline, "
              "and the three things clean per-meter history makes possible that no single bill "
              "ever can."),
 "lede": ("The messages are the visible part and the history is the valuable part. A couple of "
          "years of per-meter, per-day, unit-normalised usage is a thing almost no small "
          "business has, and it is what turns three separate cost questions from guesswork "
          "into arithmetic."),
 "tags": ["utility bills", "energy history", "reporting", "DynamoDB", "cost control",
          "serverless"],
 "takeaways": [
  "Every bill writes one history row, whether or not anything moved.",
  "Usage is stored per day as well as per period, because billing periods are not equal.",
  "An estimated reading is stored and flagged, but never used as a year-on-year baseline.",
  "A catch-up bill after a run of estimates is spread across the days it covers.",
  "Two years of this makes renewals, site comparison and fault detection arithmetic rather than guesswork.",
 ],
 "blocks": [
  ("h2", "The history row"),
  ("table", ["Field", "Example", "Why it is there"], [
   ["<code>meter</code>", "1200034557", "The partition; everything is per meter"],
   ["<code>period_end</code>", "2026-07-10", "The sort key, so a range query is a period"],
   ["<code>days</code>", "30", "Billing periods are not equal months"],
   ["<code>usage</code>", "4180.0", "In the meter's own unit, from the meter list"],
   ["<code>usage_per_day</code>", "139.3", "What every comparison actually uses"],
   ["<code>unit_rate</code>", "0.241", "Excluding tax, always"],
   ["<code>standing</code>", "0.48", "Per day, excluding tax"],
   ["<code>estimated</code>", "false", "Whether this reading was estimated"],
   ["<code>baseline_ok</code>", "true", "Whether it may be used as a year-on-year reference"],
   ["<code>bill_key</code>", "s3://bills/2026/07/...", "The original page, for when somebody asks"],
  ]),
  ("h3", "Why estimated readings are quarantined"),
  ("p", "An estimated bill is a supplier's guess, usually based on the same period last year, "
        "which makes it circular as a comparison reference. Worse, estimates run in sequences: "
        "three or four estimated periods followed by an actual reading that corrects all of "
        "them at once. That correcting bill can be double a normal one and is not a usage spike "
        "at all."),
  ("p", "So estimated bills are stored, flagged, and given <code>baseline_ok: false</code>. "
        "They are compared &mdash; a wildly wrong estimate is worth knowing about &mdash; but "
        "they are never the reference another period is measured against, and a catch-up "
        "reading is spread evenly across the days the estimates covered before per-day figures "
        "are recomputed."),
  ("h2", "Three things clean history makes possible"),
  ("fig", ("chain", {
    "entry": {"title": "Two years of rows", "sub": ["per meter, per day"], "icon": "chart"},
    "steps": [
      {"title": "Renewal quotes", "sub": ["annual usage, instantly"], "icon": "money",
       "side": {"title": "Contract end sweep", "sub": ["from the meter list"], "icon": "calendar"}},
      {"title": "Site comparison", "sub": ["per square metre,", "per cover, per unit"],
       "icon": "counter",
       "side": {"title": "Site facts", "sub": ["area, covers, hours"], "icon": "doc"}},
      {"title": "Fault detection", "sub": ["a step change that", "does not go back"], "icon": "alarm"},
      {"title": "One page a quarter", "sub": ["what changed, per site"], "icon": "report"}],
    "note": "None of these is possible from a pile of PDFs, and all three are arithmetic once the rows exist."}),
   "What the history is for. Each of these is a straightforward query over the rows and "
   "completely impractical over a folder of PDFs.",
   "Three uses of accumulated utility history",
   "A vertical chain of four steps entered by a box labelled Two years of rows, per meter and "
   "per day. Step one is Renewal quotes, which gets annual usage instantly, supported by the "
   "contract end sweep reading the meter list. Step two is Site comparison, expressing usage "
   "per square metre, per cover or per unit produced, supported by site facts such as area, "
   "covers and opening hours. Step three is Fault detection, looking for a step change that "
   "never goes back down. Step four is One page a quarter, showing what changed per site. A "
   "note says none of these is possible from a pile of PDFs and all three are arithmetic once "
   "the rows exist."),
  ("h3", "Site comparison, and its one trap"),
  ("p", "Comparing sites is the most requested and most misused output. Raw usage per site tells "
        "you which site is biggest, which you already knew. Usage per square metre, per opening "
        "hour, or per cover served is the number with information in it, and it needs facts "
        "about the site that the bills do not contain. That is three columns on the meter list "
        "tab and it is worth adding."),
  ("p", "The trap is comparing sites with different equipment. A site with a kitchen and a site "
        "without are not comparable on any normalisation, and a league table that puts them next "
        "to each other produces a manager defending their numbers rather than looking at them. "
        "Compare a site with itself over time first; compare it with others only where the "
        "equipment genuinely matches."),
  ("h3", "Fault detection"),
  ("p", "The signature of failing equipment is specific and easy to query for: a step change in "
        "per-day usage that persists rather than reverting. A cold snap raises usage and then it "
        "comes back down. A fridge seal that has failed raises it and it stays raised. Two "
        "consecutive periods more than a threshold above the seasonally adjusted expectation, "
        "with no corresponding change at other sites, is worth a look."),
  ("callout", "What the history is not for", [
   "It is not a forecast. Two years is enough to compare and not enough to predict, and a "
   "confident forecast from this data would be a fiction.",
   "It is not a carbon report. Converting usage to emissions needs factors that change annually "
   "and vary by supplier, and getting it wrong in a public claim is worse than not doing it.",
   "It is not a substitute for a meter. If a site genuinely needs half-hourly data to manage a "
   "process, buy the monitoring; a monthly bill will never tell you when something switched on.",
   "It is not evidence in a dispute on its own. It tells you a bill looks wrong, which is the "
   "start of a conversation with a supplier, not the end of one.",
  ]),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="bill",
 volumes=[(24, "24 bills"), (60, "60 bills"), (200, "200 bills")],
 read_each=0.0046, msgs_each=0.6,
 extra=[("ocr", "Textract &mdash; every bill page", "#8C4FFF", 0.0052, 0.0)],
 lede=("A single-site business gets about two dozen utility bills a year; a dozen sites across "
       "four utilities gets a couple of hundred. Either way this is the cheapest system in the "
       "series to run, because the volume is tiny and nothing is always-on. Here is where each "
       "cent goes."),
 takeaway_extra=("Volume is genuinely tiny -- a dozen sites is a couple of hundred bills a "
                 "year, not a month."),
 risks=[
  "<strong>Re-reading resent bills.</strong> Suppliers resend constantly &mdash; reminders with "
  "the original attached, corrected copies, statements containing last month's bill as a page. "
  "Without the duplicate test in front of Textract you pay to extract the same bill five times.",
  "<strong>A retry loop on an unparseable PDF.</strong> Some supplier PDFs are a single "
  "scanned image at low resolution, and Textract will return very little. A dead-letter queue "
  "with a maximum receive count of three turns that into one flagged bill instead of an "
  "infinite loop.",
  "<strong>Log retention left at never.</strong> With volume this low the logs will "
  "comfortably out-cost the compute within a year. Thirty days of retention is the highest-"
  "return setting here by a wide margin.",
 ],
 per_unit_note=("Textract is the largest per-bill line because utility bills run to several "
                "pages and the layout has to be extracted from all of them. It is still "
                "fractions of a cent, and the volume is a couple of hundred a year rather than "
                "a couple of hundred a month."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ub",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions "
       "and what each is allowed to touch, the two tables, the scheduled sweeps, and the "
       "specific model."),
 outside=[
  {"title": "SES inbound", "sub": ["supplier email + PDF"], "icon": "email"},
  {"title": "Meter list", "sub": ["Sheets API, read-only"], "icon": "chart"},
  {"title": "SES outbound", "sub": ["findings, renewals"], "icon": "email"}],
 inside=[
  {"title": "S3 + SQS", "sub": ["bill PDFs,", "one bill queue"], "icon": "bucket"},
  {"title": "Lambda x4", "sub": ["intake, read,", "compare, sweep"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["bills, history"], "icon": "database"}],
 note="us-east-1. One account. Two scheduled sweeps: overdue meters and contract ends.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. SES inbound, receiving supplier email "
  "with PDFs attached. The Meter list, read through the Google Sheets API read-only. And SES "
  "outbound, carrying the findings and the renewal messages. Inside the account, three groups. "
  "S3 holding the bill PDFs and SQS carrying one bill queue. Four Lambda functions named "
  "intake, read, compare and sweep. And two DynamoDB tables named bills and history. A note "
  "gives the region as us-east-1, one account, and notes two scheduled sweeps: one for overdue "
  "meters and one for approaching contract ends."),
 functions=[
  ["<code>ub-intake</code>", "SES receipt rule + S3 ObjectCreated",
   "Stores the PDF, fingerprints the bill, enqueues one message", "10s / 512&nbsp;MB"],
  ["<code>ub-read</code>", "SQS bill queue",
   "Textract, then one Bedrock call into five fields plus the total check",
   "120s / 1024&nbsp;MB"],
  ["<code>ub-compare</code>", "SQS read queue",
   "Meter match, three comparisons, history write", "10s / 512&nbsp;MB"],
  ["<code>ub-sweep</code>", "EventBridge daily",
   "Overdue meters and contract ends at T-90 and T-30", "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>ub-intake-role</code>", "<code>s3:PutObject</code>, <code>sqs:SendMessage</code>",
   "The bills prefix; the bill queue only"],
  ["<code>ub-read-role</code>",
   "<code>textract:AnalyzeDocument</code>, <code>bedrock:InvokeModel</code>",
   "The bills prefix; one model arn"],
  ["<code>ub-compare-role</code>",
   "<code>dynamodb:PutItem</code>/<code>Query</code>, <code>secretsmanager:GetSecretValue</code>",
   "Bills and history; the Sheets credential only"],
  ["<code>ub-sweep-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "History, read; one verified identity"]],
 tables=[
  ("Table: bills",
   "PK   fingerprint       S   sha256(supplier|meter|period_start|period_end)\n"
   "     meter             S   1200034557\n"
   "     supplier          S   as printed, normalised\n"
   "     state             S   read | matched | unmatched | queried\n"
   "     fields            M   {usage, unit_rate, standing, estimated, total}\n"
   "     total_check       S   ok | mismatch\n"
   "     pdf_key           S   s3://bills/2026/07/...\n"
   "     ttl               N   epoch, +7 years\n\n"
   "The fingerprint is the partition key, so a resent bill is rejected by the\n"
   "conditional write rather than by a query that can race."),
  ("Table: history",
   "PK   meter             S   1200034557\n"
   "SK   period_end        S   2026-07-10\n"
   "     days              N   30\n"
   "     usage             N   4180.0\n"
   "     usage_per_day     N   139.3\n"
   "     unit_rate         N   0.241\n"
   "     standing          N   0.48\n"
   "     estimated         BOOL false\n"
   "     baseline_ok       BOOL true\n\n"
   "A year-on-year comparison is a single Query with a SK BETWEEN over the\n"
   "same window last year, filtered to baseline_ok. No scan, ever.")],
 inbound=[
  "An SES <strong>receipt rule set</strong> on the bills domain writes the whole message to S3, "
  "attachments included. The S3 event is what fires the intake; there is no SNS hop.",
  "<strong>Portal downloads</strong> go to a second S3 prefix that a person or a small sync "
  "drops files into. Both prefixes fire the same intake function.",
  "<strong>Spam and virus verdicts</strong> are on the SES headers written into the object, and "
  "the intake drops anything failing either before parsing.",
  "<strong>Suppression links</strong> in a finding message are signed, scoped to one meter and "
  "one finding shape, and expire after sixty days."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock. "
  "The task is picking five values out of a Textract layout, which is extraction.",
  "<strong>Called once</strong> per new bill, after the duplicate test, never on a resend.",
  "<strong>Output is a JSON schema</strong> with every field nullable. A null usage produces a "
  "question with the page attached; it never produces a zero.",
  "<strong>Grounded</strong> with your meter numbers and their units, so the model matches to a "
  "known meter rather than reporting whatever string looks most like an identifier.",
  "<strong>The total check is code.</strong> Recomputing usage times rate plus standing charge "
  "times days and comparing with the printed total is arithmetic, and arithmetic should not go "
  "near a model."],
 gotchas=[
  "Store rates excluding tax and be strict about it. Comparing an inclusive rate against an "
  "exclusive contract produces a false alarm every single month.",
  "Take the unit from your meter list, not from the bill. Gas appears in cubic metres, kWh and "
  "therms, and a silent unit change makes a year of history meaningless.",
  "Normalise to per-day before comparing. Billing periods vary by several days and comparing "
  "raw totals generates constant noise.",
  "Quarantine estimated readings from the baseline, and spread a catch-up bill across the days "
  "it covers before recomputing per-day figures.",
  "Building the meter list is the hard part and it is not a software problem. Expect to find at "
  "least one supply nobody remembered, which is usually where the project pays for itself."],
))
