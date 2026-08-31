"""Day 83 -- 2026-07-16 -- Petty cash tracker."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "petty-cash-tracker"
NAME = "Petty cash tracker"

SPEC = {
 "slug": SLUG, "date": "2026-07-16", "name": NAME,
 "tagline": ("The tin balances itself. Every spend is a photo of a receipt, every top-up is a "
             "line, and the running balance is right at four in the afternoon rather than "
             "roughly right at month end."),
 "lede": ("A small system that keeps a petty cash float honest without turning it into "
          "paperwork. Somebody photographs a receipt as they put it in the tin, the system "
          "reads it, updates the balance, and says nothing. When the count does not match, it "
          "says so on the day rather than four weeks later. Seven posts on the same system -- "
          "one diagram at a time -- with a cost breakdown and an engineering reference at the "
          "end."),
 "keywords": ["petty cash", "float management", "receipts", "small business bookkeeping",
              "human in the loop", "serverless"],
 "icons": ["image", "counter", "money"],
 "faq": [
  ("What is a petty cash tracker?",
   "A small serverless system that keeps a running balance for a cash float. Each spend is a "
   "photographed receipt, each top-up is a recorded line, and a periodic count is compared "
   "against the expected balance. It never moves money and never accuses anybody; it tells you "
   "on the day that a count did not match."),
  ("Why photograph receipts rather than just record amounts?",
   "Because the receipt is the accounting record and the amount is only half of it. The photo "
   "gives you the vendor, the date, the tax treatment and the evidence, all of which your "
   "bookkeeper needs and none of which survives being typed as a number."),
  ("What happens when the count is short?",
   "The system says so on the day it is counted, with the transactions since the last count "
   "listed. Most shortfalls are a receipt that was never photographed, which is a two-minute "
   "fix while it is still findable in a pocket."),
  ("Does it work with more than one tin?",
   "Yes, and it is designed for it. Each float is separate with its own balance, its own "
   "custodian and its own count cadence, because a site tin and an office tin behave nothing "
   "alike."),
  ("What does it cost to run?",
   "A couple of dollars a month. Petty cash volume is low and nothing is always-on. See part "
   "six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "petty-cash-tracker-on-aws",
 "title": "A petty cash tracker on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 900,
 "desc": ("Reads each receipt as it goes into the tin, keeps a running balance, and tells you "
          "on the day a count does not match. AWS, about $2 a month."),
 "og": ("Every spend is a photographed receipt, every top-up is a line, and the running "
        "balance is right today rather than roughly right at month end."),
 "abstract": ("The whole system on one page -- a reader, a ledger and a reconciler -- and the "
              "constraint that makes it survivable: it must be faster than not using it."),
 "lede": ("Petty cash is the smallest accounting problem in a business and generates a "
          "wildly disproportionate amount of irritation. The tin is short by fourteen pounds. "
          "There are two receipts in it with no date. Somebody definitely bought milk. The "
          "reconciliation happens at month end, when none of that is recoverable, and the "
          "difference gets written off with a small note that quietly implies something about "
          "somebody. This post walks through a small system that makes the tin balance itself, "
          "on the condition that using it is faster than not."),
 "tags": ["petty cash", "receipts", "bookkeeping", "float management", "human in the loop",
          "serverless"],
 "takeaways": [
  "One action per spend: photograph the receipt. That is the entire user interface.",
  "The balance is live, so a mismatch is found on the day rather than at month end.",
  "Each float is separate, with its own custodian, balance and count cadence.",
  "A receipt the reader cannot read is a question, not a guessed number.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Receipt photo", "sub": ["taken at the tin"], "icon": "image"},
      {"title": "Top-ups", "sub": ["cash put in"], "icon": "money"},
      {"title": "Custodian", "sub": ["counts, and is told"], "icon": "person"}],
    "inside": [
      {"title": "Reader", "sub": ["amount, vendor, date"], "icon": "ocr"},
      {"title": "Ledger", "sub": ["one running balance", "per float"], "icon": "database"},
      {"title": "Reconciler", "sub": ["count vs expected,", "on the day"], "icon": "counter"}],
    "edges": [{"from": 0, "to": 0, "label": "spends"},
              {"from": 1, "to": 1, "label": "additions"},
              {"from": 2, "to": 2, "label": "only when it differs", "up": True}],
    "note": "One action per spend. If it takes longer than not doing it, nobody will do it."}),
   "Three things outside the account, three pieces inside it. The design constraint that shapes "
   "everything is at the bottom: the system has to be faster than the alternative, which is "
   "putting a receipt in a tin and forgetting.",
   "System: receipts and top-ups in, a live balance, a reconciliation out",
   "Three boxes across the top sit outside the AWS account. On the left, Receipt photo: taken "
   "at the tin as the receipt goes in. In the middle, Top-ups: cash put into the float. On the "
   "right, Custodian: the person who counts the tin and is told when it does not match. Each "
   "connects by an arrow to the AWS account container below. Spends and additions flow down "
   "into the account. A message goes back out only when a count differs from the expected "
   "balance. Inside the AWS account are three components in a row. On the left, the Reader, "
   "which pulls the amount, vendor and date from the photograph. In the middle, the Ledger, "
   "which keeps one running balance per float. On the right, the Reconciler, which compares a "
   "count against the expected balance on the day it is made. A note at the bottom says one "
   "action per spend, and that if it takes longer than not doing it nobody will do it."),
  ("h3", "The one constraint"),
  ("p", "Every petty cash system that has ever failed has failed for the same reason: it asked "
        "for more effort than the alternative. The alternative is putting a receipt in a tin, "
        "which takes one second and requires no thought. Anything that asks somebody standing "
        "in a shop doorway to categorise a spend, pick a cost code or type an amount will be "
        "skipped, and a petty cash system that is skipped half the time is worse than no system "
        "because the balance is now confidently wrong."),
  ("p", "So the interface is: photograph the receipt. Put the receipt in the tin as usual. That "
        "is all. Everything else &mdash; the amount, the vendor, the date, the category, which "
        "float it came from &mdash; is the system's problem."),
  ("h3", "What runs on every receipt (the inside)"),
  ("ul", [
   "<strong>The reader.</strong> Pulls the total, the vendor and the date off a photograph of "
   "a till receipt, which is a genuinely hard document &mdash; thermal paper, faded, creased, "
   "photographed at an angle in bad light. Where it cannot read the total confidently it asks, "
   "which is a two-second reply while the person is still holding the receipt.",
   "<strong>The ledger.</strong> One running balance per float, moved by a conditional write so "
   "two people spending at the same time cannot both compute from the same starting figure. "
   "Every movement records who, what, when and which receipt.",
   "<strong>The reconciler.</strong> Compares a physical count against the expected balance. "
   "Runs when somebody counts, which the system prompts for on a cadence. A match is silent. A "
   "mismatch lists every movement since the last count, which is almost always where the answer "
   "is.",
  ]),
  ("h2", "One spend, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Bought", "sub": ["milk, £3.40"], "icon": "cart"},
      {"title": "Photographed", "sub": ["one tap"], "icon": "image"},
      {"title": "Read", "sub": ["amount, vendor, date"], "icon": "ocr"},
      {"title": "Deducted", "sub": ["balance now £46.60"], "icon": "counter"},
      {"title": "Silent", "sub": ["nobody is told"], "icon": "check"}],
    "title": "ONE PETTY CASH SPEND, END TO END",
    "note": "The whole interaction is the second box. Everything else happens without anybody."}),
   "The same system as one line. Only one of the five stages involves a person, and it takes a "
   "second.",
   "One petty cash spend from purchase to recorded balance, in five stages",
   "A horizontal row of five boxes joined by arrows. Bought: milk, three pounds forty. "
   "Photographed: one tap. Read: the amount, vendor and date are extracted. Deducted: the "
   "balance moves to forty-six pounds sixty. Silent: nobody is told. A note says the whole "
   "interaction is the second box and everything else happens without anybody."),
  ("h2", "In plain words"),
  ("p", "Your office manager buys milk and biscuits on the way in, £8.20. She photographs the "
        "receipt at the tin and drops it in. The reader gets £8.20 from a supermarket on "
        "today's date. The ledger moves the office float from £54.80 to £46.60. Nobody hears "
        "anything. Three more spends happen that week the same way."),
  ("p", "On Friday the system prompts her to count, which it does weekly for that float. She "
        "counts £42.60. Expected is £46.60. Four pounds short, and instead of that being a "
        "month-end mystery it is a message the same afternoon listing the four movements since "
        "the last count. She looks at the tin, finds a parking receipt for £4.00 sitting under "
        "the tray that never got photographed, takes the photo, and the float balances. Total "
        "time spent: ninety seconds, on the day, by the person who was there."),
  ("callout", "Design rules that shaped every decision", [
   "One action per spend, and it has to be faster than not doing it. Everything else is the "
   "system's problem.",
   "Never guess an amount. A receipt the reader cannot read confidently becomes a question, "
   "because a guessed total is a balance that is wrong in a way nobody will find.",
   "Count often and cheaply. A weekly count that takes a minute beats a monthly one that takes "
   "an hour and cannot be resolved.",
   "A mismatch lists the movements, not a person. The answer is almost always a missing "
   "receipt, and the list is where it is found.",
   "Each float is separate. A site tin and an office tin have different custodians, cadences "
   "and normal behaviour.",
   "The system never moves money and never authorises a spend. It records and it reconciles.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Petty cash reconciliation fails at month end for a structural reason: by then the "
        "information that would resolve a difference has evaporated. Nobody remembers what "
        "they bought on the 9th, the receipt that fell behind the drawer is gone, and the "
        "person who could have said \"oh, that was the taxi\" has had three hundred other "
        "thoughts since."),
  ("p", "Moving the reconciliation to weekly, and making it cost a minute, changes the "
        "economics completely. A four-pound difference found on Friday is nearly always "
        "resolvable, because the receipt is still physically nearby and the memory is still "
        "there. The same four pounds found on the 31st is a write-off with a note attached."),
  ("p", "The next four posts walk through each piece: how a receipt gets captured, how the "
        "balance stays right under concurrency, how a count works, and how the month gets "
        "closed for the bookkeeper. One diagram per post, a cost breakdown, and an engineering "
        "reference at the end."),
 ],
},
{
 "slug": "how-a-petty-cash-receipt-gets-captured",
 "title": "How a petty cash receipt gets captured",
 "nav": "How it is captured",
 "read": 5, "words": 830,
 "desc": ("Photographing a thermal till receipt in bad light, what the reader refuses to guess, "
          "and how a float gets picked without anybody choosing one."),
 "og": ("Till receipts are the hardest document in this series to read. What makes it safe is "
        "that unreadable is an answer and the float is inferred rather than chosen."),
 "abstract": ("Reading a creased thermal receipt photographed in bad light, what the reader "
              "refuses to guess, and how the right float gets picked without anybody having to "
              "choose one."),
 "lede": ("A till receipt photographed on a phone in a shop doorway is the worst input in this "
          "entire series. Thermal paper fades, curls and reflects; the total is often not the "
          "largest number on the page; and half of them have been in a pocket. This post is "
          "about getting a reliable number out of that, and about the fields where the honest "
          "answer is a question."),
 "tags": ["petty cash", "Amazon Textract", "OCR", "receipts", "mobile capture", "serverless"],
 "takeaways": [
  "One screen: take a photo. No amount field, no category, no float picker.",
  "The float is inferred from who took the photo, and confirmed only when ambiguous.",
  "The total is the one field that is never guessed. Everything else can be filled in later.",
  "A blurred or partial photo is rejected immediately, while the receipt is still in hand.",
  "The photo is the accounting record and is kept for as long as your obligation runs.",
 ],
 "blocks": [
  ("h2", "One screen"),
  ("p", "The capture screen has a camera button and nothing else. No amount field, because "
        "typing an amount is the thing the photo exists to avoid. No category, because "
        "categorising is a bookkeeping decision that a bookkeeper makes faster and better at "
        "month end. No float picker, because the answer is nearly always inferable."),
  ("fig", ("chain", {
    "entry": {"title": "Photo taken", "sub": ["at the tin"], "icon": "image"},
    "steps": [
      {"title": "Usable photo?", "sub": ["blur, edges, glare"], "icon": "branch",
       "exit": {"title": "Retake now", "sub": ["while it is in hand"], "icon": "retry",
                "label": "no"}},
      {"title": "Which float?", "sub": ["from the photographer"], "icon": "branch",
       "side": {"title": "Custodian list", "sub": ["person to float"], "icon": "team"},
       "exit": {"title": "Ask which tin", "sub": ["two buttons"], "icon": "person",
                "label": "several"}},
      {"title": "Pull the text", "sub": ["Textract"], "icon": "ocr"},
      {"title": "Find the total", "sub": ["one Bedrock call"], "icon": "model",
       "exit": {"title": "Ask the amount", "sub": ["show the crop"], "icon": "person",
                "label": "unsure"}},
      {"title": "Deduct from the float", "sub": ["conditional write"], "icon": "counter"}],
    "note": "The first check happens on the phone, before upload, so a retake costs nothing."}),
   "One receipt, end to end. The usability check runs on the device before anything is "
   "uploaded, because a retake is trivial while the receipt is in your hand and impossible an "
   "hour later.",
   "How a photographed receipt becomes a deduction from a float",
   "A vertical chain of five steps entered by a box labelled Photo taken at the tin. Step one "
   "asks whether the photo is usable, checking blur, edges and glare; if not it exits to Retake "
   "now, while the receipt is still in hand. Step two asks which float it belongs to, inferred "
   "from the photographer using the custodian list; somebody who holds several floats exits to "
   "Ask which tin, with two buttons. Step three pulls the text with Amazon Textract. Step four "
   "finds the total with a single Bedrock call, exiting to Ask the amount with the crop shown "
   "if it is unsure. Step five deducts from the float with a conditional write. A note says the "
   "first check happens on the phone before upload, so a retake costs nothing."),
  ("h3", "The on-device check"),
  ("p", "A blur and edge check in the browser before upload is a few lines of canvas work and "
        "it removes most of the failure cases downstream. More importantly it removes them at "
        "the only moment they are cheap to fix. A rejected photo two seconds after it is taken "
        "is a retake; the same rejection three minutes later, after the receipt has gone in the "
        "tin and the person has walked away, is a question that will not get answered."),
  ("h3", "Inferring the float"),
  ("p", "Most people have access to exactly one tin, so the float is simply looked up from who "
        "took the photo. The custodian list maps people to floats, and the common case needs no "
        "input at all. Somebody with access to two &mdash; a manager who covers the office and "
        "the workshop &mdash; gets two buttons, which is one tap and only appears for the "
        "handful of people it applies to."),
  ("h2", "What the reader will and will not guess"),
  ("table", ["Field", "If unclear", "Why"], [
   ["Total", "Ask, with the crop", "A wrong total is a wrong balance nobody will trace"],
   ["Vendor", "Leave null", "The bookkeeper can read the photo at month end"],
   ["Date", "Use the photo date", "A receipt is photographed the same day in practice"],
   ["Tax", "Leave null", "Tax treatment is a bookkeeping judgement, not an extraction"],
   ["Category", "Never attempted", "Categorising is done once, at month end, by one person"],
  ]),
  ("p", "The asymmetry there is deliberate. The total is the only field that affects the "
        "balance, so it is the only one worth interrupting somebody for. Everything else can be "
        "null, because the photograph itself carries the information and a bookkeeper reading "
        "forty receipts at month end will fill them in far faster than forty people "
        "interrupted individually."),
  ("h3", "Why the total is hard"),
  ("p", "On a supermarket receipt the total is not the largest number, is frequently below a "
        "subtotal and a discount line, and sits above a cash-tendered figure and a change "
        "figure that look exactly like it. \"£20.00\" and \"£11.80\" and \"£8.20\" all appear "
        "in the same block and only one is the spend."),
  ("p", "The model is given the Textract layout and asked specifically for the amount paid, "
        "with the instruction that a cash-tendered line and a change line are not it. Where the "
        "block is ambiguous it returns null and the question shows the crop of that block, which "
        "a human resolves instantly because they were there."),
  ("callout", "What is kept, and for how long", [
   "The original photograph, unmodified, because it is the accounting record and a re-encoded "
   "copy is a worse one.",
   "The Textract output, so a re-read later never needs a second paid extraction.",
   "The extracted fields and who confirmed any of them.",
   "All of it for as long as your record-keeping obligation runs, then deleted by a lifecycle "
   "rule rather than by anybody remembering.",
  ]),
  ("p", "Next: how the balance stays right when two people spend at once."),
 ],
},
{
 "slug": "how-the-float-balance-stays-right",
 "title": "How the float balance stays right",
 "nav": "How the balance holds",
 "read": 5, "words": 810,
 "desc": ("Two people spending at the same time, the conditional increment that stops them "
          "both computing from the same figure, and why the balance is derived rather than "
          "stored."),
 "og": ("Two people spending at once is the whole concurrency story, and the answer is a "
        "conditional increment rather than a read-modify-write."),
 "abstract": ("Two people spending at once, the conditional increment that prevents them both "
              "computing from the same starting figure, and why the balance is both stored and "
              "derivable."),
 "lede": ("A petty cash balance looks like the simplest possible piece of state and contains "
          "the one bug that makes these systems untrustworthy. Two people photograph receipts "
          "within the same second, both functions read a balance of £54.80, both subtract, and "
          "the tin is now recorded as £46.60 when it should be £38.40. Nobody notices until the "
          "count, and then the count is what gets doubted."),
 "tags": ["petty cash", "DynamoDB", "conditional writes", "concurrency", "ledger", "serverless"],
 "takeaways": [
  "The balance moves by a conditional increment, never by a read, subtract and write.",
  "Every movement is an immutable row; the balance is a convenience, not the truth.",
  "The balance can always be rebuilt from the movements, and is, after any correction.",
  "A correction is a new row, never an edit. Editing history is how a float stops being evidence.",
  "A negative balance is allowed and flagged, because tins do go overdrawn.",
 ],
 "blocks": [
  ("h2", "Movements are the truth"),
  ("p", "The design keeps two things: an append-only list of movements, and a balance. The "
        "movements are the record; the balance exists so that a phone can show a number without "
        "summing four hundred rows. If they ever disagree, the movements win and the balance is "
        "rebuilt."),
  ("fig", ("chain", {
    "entry": {"title": "A spend or a top-up", "sub": ["amount and float"], "icon": "money"},
    "steps": [
      {"title": "Write the movement", "sub": ["append-only, with the receipt"], "icon": "log",
       "side": {"title": "DynamoDB movements", "sub": ["never updated"], "icon": "database"}},
      {"title": "Move the balance", "sub": ["ADD, not SET"], "icon": "counter",
       "side": {"title": "DynamoDB floats", "sub": ["atomic increment"], "icon": "database"}},
      {"title": "Below zero?", "sub": ["it happens"], "icon": "branch",
       "exit": {"title": "Flag, do not block", "sub": ["tell the custodian"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Balance updated", "sub": ["shown on the phone"], "icon": "check"}],
    "note": "ADD is atomic. Two spends in the same second both apply, in whatever order."}),
   "How a movement is recorded. The atomic increment is the whole concurrency story: two "
   "functions can both apply their own delta without either needing to know what the other read.",
   "How a spend moves the float balance safely",
   "A vertical chain of four steps entered by a box labelled A spend or a top-up, carrying an "
   "amount and a float. Step one writes the movement to an append-only DynamoDB movements "
   "table, together with the receipt reference, and never updates it. Step two moves the "
   "balance on a DynamoDB floats table using an atomic ADD rather than a SET. Step three asks "
   "whether the balance has gone below zero, which does happen, and exits to Flag but do not "
   "block, telling the custodian. Step four is Balance updated, shown on the phone. A note says "
   "ADD is atomic, so two spends in the same second both apply in whatever order they arrive."),
  ("h3", "ADD rather than SET"),
  ("p", "The bug is in the read. A function that reads £54.80, subtracts £8.20 and writes "
        "£46.60 has embedded an assumption about what the balance was, and that assumption is "
        "wrong the moment somebody else writes in between. Two of those and one spend "
        "disappears."),
  ("p", "An atomic increment carries no assumption. Each function says \"reduce this by 8.20\" "
        "and \"reduce this by 12.00\", and the database applies both in some order, arriving at "
        "the right answer either way. It is one line of difference in the update expression and "
        "it is the difference between a balance you can trust and one you cannot."),
  ("h3", "Why movements are immutable"),
  ("p", "Because the moment a movement can be edited, the float stops being evidence. A "
        "corrected amount that overwrites the original leaves no trace that anything was "
        "corrected, which is precisely the situation an audit is designed to detect. So a "
        "correction is a new row of type <code>adjustment</code>, referencing the row it "
        "corrects, with a reason and a name."),
  ("p", "That produces a slightly longer ledger and a completely defensible one. The balance "
        "after a correction is recomputed by summing the movements rather than by patching the "
        "stored figure, which is the one place the system deliberately does the expensive thing."),
  ("h2", "Overdrawn floats"),
  ("p", "A tin going below zero sounds impossible and happens regularly: somebody pays out of "
        "their own pocket intending to reimburse from the tin later, a top-up is recorded a day "
        "after it physically happened, or a spend is photographed twice. The system allows it, "
        "flags it, and tells the custodian &mdash; because blocking the write would mean "
        "refusing to record a spend that has already occurred, which loses information in "
        "exchange for tidiness."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Spend", "sub": ["£12.00"], "icon": "cart"},
      {"title": "Balance", "sub": ["-£3.40"], "icon": "alarm"},
      {"title": "Flagged", "sub": ["custodian told"], "icon": "bell"},
      {"title": "Top-up", "sub": ["£50 recorded"], "icon": "money"},
      {"title": "Clear", "sub": ["£46.60"], "icon": "check"}],
    "title": "AN OVERDRAWN TIN RESOLVES ITSELF",
    "note": "Refusing the write would have lost a real spend in exchange for a tidier number."}),
   "What happens when a float goes below zero. Recording the truth and flagging it is better "
   "than refusing to record something that has already happened.",
   "How an overdrawn petty cash float resolves",
   "A horizontal row of five boxes. Spend: twelve pounds. Balance: minus three pounds forty. "
   "Flagged: the custodian is told. Top-up: fifty pounds is recorded. Clear: the balance is "
   "forty-six pounds sixty. A note says refusing the write would have lost a real spend in "
   "exchange for a tidier number."),
  ("callout", "The movement row", [
   "<strong>Type</strong> &mdash; spend, top-up, adjustment, or count.",
   "<strong>Amount</strong>, signed, so summing the column is the balance with no case analysis.",
   "<strong>Receipt reference</strong>, for a spend, pointing at the stored photograph.",
   "<strong>Who and when</strong>, always, including for a system-generated row.",
   "<strong>Corrects</strong>, for an adjustment, naming the row it fixes and why.",
   "<strong>Never a delete.</strong> There is no code path in the system that removes a "
   "movement row.",
  ]),
  ("p", "Next: what a count actually does, and why weekly beats monthly."),
 ],
},
{
 "slug": "how-a-petty-cash-count-works",
 "title": "How a petty cash count works",
 "nav": "How a count works",
 "read": 5, "words": 800,
 "desc": ("Counting a tin in under a minute, what a mismatch message contains, why the count "
          "is a movement, and the cadence that makes differences resolvable."),
 "og": ("A weekly count that takes a minute beats a monthly one that takes an hour and cannot "
        "be resolved. The mismatch message lists movements, never people."),
 "abstract": ("Counting a tin in under a minute, why the count is itself a movement, what a "
              "mismatch message contains, and the cadence that keeps differences resolvable."),
 "lede": ("The count is where the system earns its keep, and the only variable that really "
          "matters is how often it happens. A difference found within a week is nearly always "
          "explainable; the same difference found after four weeks is a write-off. Everything "
          "in this post is in service of making a count cheap enough to do weekly."),
 "tags": ["petty cash", "reconciliation", "cash counting", "float management", "reporting",
          "serverless"],
 "takeaways": [
  "A count is one number typed by the custodian, and it takes under a minute.",
  "The count is recorded as a movement, so the ledger holds every reconciliation.",
  "A match is completely silent. A mismatch lists the movements since the last count.",
  "A mismatch never names a person, because the answer is almost always a missing receipt.",
  "Weekly is the default. Monthly is where these systems go to fail.",
 ],
 "blocks": [
  ("h2", "What counting looks like"),
  ("p", "The system prompts the custodian on the cadence set for that float. The screen shows "
        "one field and one button: how much is in the tin. It deliberately does not show the "
        "expected balance beforehand, because a number on the screen while somebody is counting "
        "is an anchor, and anchored counts agree with the system far more often than "
        "independent ones do."),
  ("fig", ("chain", {
    "entry": {"title": "Count prompt", "sub": ["on the float's cadence"], "icon": "clock"},
    "steps": [
      {"title": "Custodian types the total", "sub": ["expected is hidden"], "icon": "counter"},
      {"title": "Record the count", "sub": ["as a movement"], "icon": "log",
       "side": {"title": "DynamoDB movements", "sub": ["append-only"], "icon": "database"}},
      {"title": "Matches expected?", "sub": ["to the penny"], "icon": "branch",
       "exit": {"title": "Silent", "sub": ["the usual outcome"], "icon": "check",
                "label": "yes"}},
      {"title": "List the movements", "sub": ["since the last count"], "icon": "search"},
      {"title": "One message", "sub": ["difference and the list"], "icon": "email"}],
    "note": "The expected figure is hidden while counting. A number on screen anchors the count."}),
   "What happens when somebody counts. Hiding the expected figure until after the count is "
   "submitted is a small choice with a large effect on how honest the reconciliation is.",
   "How a petty cash count is taken and reconciled",
   "A vertical chain of five steps entered by a box labelled Count prompt, sent on the float's "
   "own cadence. Step one has the custodian type the total, with the expected figure hidden. "
   "Step two records the count as a movement in the append-only DynamoDB movements table. Step "
   "three asks whether it matches the expected balance to the penny, exiting to Silent, the "
   "usual outcome. Step four lists the movements since the last count. Step five sends one "
   "message with the difference and the list. A note says the expected figure is hidden while "
   "counting because a number on screen anchors the count."),
  ("h3", "Why the count is a movement"),
  ("p", "Recording the count in the same append-only ledger as spends and top-ups means the "
        "ledger answers a question it otherwise could not: when was this float last verified, "
        "and by whom? A float whose last count was eleven weeks ago is a different risk from "
        "one counted on Friday, and that fact should live in the same place as everything else "
        "rather than in a separate table nobody joins to."),
  ("p", "It also means a count can be superseded. A recount five minutes after a miscount is a "
        "second count movement, both are kept, and the reconciliation uses the latest. Editing "
        "the first would violate the same rule that keeps spends immutable."),
  ("h2", "The mismatch message"),
  ("callout", "What it says, in order", [
   "<strong>The difference.</strong> \"Office tin: counted £42.60, expected £46.60. Short by "
   "£4.00.\"",
   "<strong>Since the last count.</strong> Every movement, with date, amount, vendor and a "
   "thumbnail of the receipt. Usually four to ten lines.",
   "<strong>The prompt.</strong> \"Most differences are a receipt that was not photographed. "
   "Is there one in the tin that is not on this list?\"",
   "<strong>Two buttons.</strong> \"Found it &mdash; here's the photo\" and \"No, record the "
   "difference\".",
   "<strong>No names.</strong> The movements carry who photographed each receipt, and the "
   "message does not lead with that, because leading with it changes what the message is.",
  ]),
  ("p", "The prompt line is doing most of the work. In practice the single most common cause of "
        "a shortfall is a receipt that went into the tin without being photographed, and saying "
        "so plainly in the message directs the person to look in exactly the right place. A "
        "message that only reports the difference sends them to think about people instead."),
  ("h3", "Recording an unresolved difference"),
  ("p", "Sometimes the money is genuinely gone and no receipt turns up. That is recorded as an "
        "adjustment movement with a reason, which brings the balance back in line and leaves a "
        "permanent, visible record of the write-off. That record is the useful part: three "
        "unexplained shortfalls in a quarter on the same tin is a pattern worth a conversation, "
        "and it is only visible because each one was written down rather than absorbed."),
  ("h2", "Cadence"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Daily", "sub": ["high-turnover site tin"], "icon": "clock"},
      {"title": "Weekly", "sub": ["the sensible default"], "icon": "calendar"},
      {"title": "Monthly", "sub": ["differences unresolvable"], "icon": "alarm"},
      {"title": "On top-up", "sub": ["always, whatever else"], "icon": "money"},
      {"title": "On handover", "sub": ["custodian changes"], "icon": "team"}],
    "title": "WHEN TO COUNT",
    "note": "The last two are not cadences. They are events where a count is non-negotiable."}),
   "When a float should be counted. The two event-driven counts matter more than the cadence: "
   "a top-up and a change of custodian both need a verified starting point.",
   "Five occasions for counting a petty cash float",
   "A horizontal row of five boxes. Daily: for a high-turnover site tin. Weekly: the sensible "
   "default. Monthly: differences become unresolvable. On top-up: always, whatever the cadence. "
   "On handover: whenever the custodian changes. A note says the last two are not cadences but "
   "events where a count is non-negotiable."),
  ("p", "The handover count is the one most businesses skip and most regret. A custodian who "
        "hands over an uncounted tin inherits every unexplained difference in it, and so does "
        "the person taking over. Counting at handover takes a minute and draws a line that both "
        "people can point at."),
  ("p", "Next: what the month end looks like for whoever does the books."),
 ],
},
{
 "slug": "how-the-petty-cash-month-closes",
 "title": "How the petty cash month closes",
 "nav": "How the month closes",
 "read": 5, "words": 790,
 "desc": ("What the bookkeeper gets, why categorising happens once at the end rather than at "
          "every spend, and the export that makes a tin a single journal line."),
 "og": ("Categorising forty receipts at once takes a bookkeeper ten minutes. Categorising them "
        "one at a time takes forty people forty interruptions and produces worse answers."),
 "abstract": ("What the bookkeeper receives, why categorising happens once at month end rather "
              "than at every spend, and the export that turns a tin into a single journal "
              "line."),
 "lede": ("Everything so far has been for the people who spend the cash. This post is for the "
          "person who has to turn it into bookkeeping, and it rests on one claim: doing the "
          "categorisation once, at the end, by one person, is both faster and more accurate "
          "than doing it forty times at the point of spend."),
 "tags": ["petty cash", "bookkeeping", "month end", "export", "reporting", "serverless"],
 "takeaways": [
  "Categorising happens once, at month end, by the person who knows the chart of accounts.",
  "The bookkeeper gets one screen: every receipt, its photo, and a category dropdown.",
  "Previous categorisations pre-fill by vendor, so the second month is much faster than the first.",
  "The export is one journal per float per period, and it balances by construction.",
  "An uncategorised receipt blocks the export, which is the one hard rule at month end.",
 ],
 "blocks": [
  ("h2", "Why categorise at the end"),
  ("p", "The argument for categorising at the point of spend is that the person knows what they "
        "bought. That is true and it is not the constraint. The constraints are that they do "
        "not know your chart of accounts, they are standing in a shop, and they will pick "
        "whichever option is first in the list about a third of the time."),
  ("p", "A bookkeeper looking at forty receipts in one sitting has the chart of accounts in "
        "their head, can see patterns across the month, and takes about ten minutes. Forty "
        "people interrupted individually take forty interruptions and produce a set of "
        "categories that has to be corrected anyway. The photo carries everything needed to "
        "decide, so nothing is lost by waiting."),
  ("fig", ("system", {
    "outside": [
      {"title": "Bookkeeper", "sub": ["one sitting, one screen"], "icon": "person"},
      {"title": "Chart of accounts", "sub": ["your own codes"], "icon": "doc"},
      {"title": "Accounting system", "sub": ["receives a journal"], "icon": "money"}],
    "inside": [
      {"title": "Month view", "sub": ["every receipt,", "photo and amount"], "icon": "report"},
      {"title": "Pre-fill", "sub": ["by vendor, from", "last month"], "icon": "search"},
      {"title": "Journal builder", "sub": ["one journal per", "float per period"], "icon": "filter"}],
    "edges": [{"from": 0, "to": 0, "label": "categories", "up": True},
              {"from": 1, "to": 1, "label": "the codes"},
              {"from": 2, "to": 2, "label": "a balanced journal", "up": True}],
    "note": "The pre-fill is why the second month takes four minutes rather than ten."}),
   "The month-end path. The pre-fill by vendor is the part that compounds: after two or three "
   "months most receipts arrive already categorised correctly.",
   "How a petty cash month is categorised and exported",
   "Three boxes across the top outside the AWS account. The Bookkeeper, working in one sitting "
   "on one screen. The Chart of accounts, holding your own codes. And the Accounting system, "
   "which receives a journal. Inside the account, three components. The Month view, showing "
   "every receipt with its photograph and amount. Pre-fill, which suggests a category by vendor "
   "based on previous months. And the Journal builder, which produces one journal per float per "
   "period. Arrows show the bookkeeper supplying categories, the chart of accounts supplying "
   "the codes, and a balanced journal going to the accounting system. A note says the pre-fill "
   "is why the second month takes four minutes rather than ten."),
  ("h3", "The month view"),
  ("p", "One scrollable list. Each row is a receipt: the photograph as a thumbnail that expands, "
        "the amount, the date, the vendor if it was read, who photographed it, and a category "
        "dropdown. Rows where the vendor has been categorised before arrive pre-filled and "
        "highlighted, which the bookkeeper scans rather than sets."),
  ("p", "The pre-fill is by vendor and float together, not by vendor alone. The same "
        "supermarket is kitchen supplies from the office tin and site consumables from the van "
        "tin, and treating those as the same is how a pre-fill becomes something that has to be "
        "double-checked rather than something that saves time."),
  ("h2", "The journal"),
  ("pre", "Petty cash — Office tin — July 2026\n\n"
          "  Kitchen supplies          42.80  Dr\n"
          "  Postage                   18.60  Dr\n"
          "  Travel                    31.00  Dr\n"
          "  Sundry                     9.40  Dr\n"
          "  Petty cash (float)               101.80  Cr\n"
          "                           ------  ------\n"
          "                           101.80  101.80\n\n"
          "Top-ups in period are a separate journal: bank Cr, float Dr.\n"
          "A count adjustment posts to the difference account named in the sheet."),
  ("p", "It balances by construction, because the credit side is the sum of the debits rather "
        "than a separately computed figure. That sounds obvious and is the difference between a "
        "journal that imports cleanly and one that produces a suspense entry every month."),
  ("h3", "The one hard rule"),
  ("p", "An uncategorised receipt blocks the export. This is the only place in the entire system "
        "where something is blocked rather than flagged, and it earns the exception because the "
        "alternative &mdash; exporting it to a sundry or suspense code &mdash; is how petty cash "
        "ends up as a single unhelpful line that grows every month and gets queried at year end."),
  ("h2", "What the period leaves behind"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Receipts", "sub": ["38 photographed"], "icon": "image"},
      {"title": "Spent", "sub": ["£101.80"], "icon": "money"},
      {"title": "Counts", "sub": ["4, all matched"], "icon": "check"},
      {"title": "Adjustments", "sub": ["0"], "icon": "log"},
      {"title": "Categorising", "sub": ["6 minutes"], "icon": "clock"}],
    "title": "ONE MONTH OF ONE TIN",
    "note": "The third and fourth numbers are the control. The fifth is why anybody keeps using it."}),
   "A month of one float in five numbers. The count and adjustment figures are the assurance; "
   "the categorising time is what determines whether the system is still in use next year.",
   "One month of a petty cash float summarised in five numbers",
   "A horizontal row of five boxes. Receipts: thirty-eight photographed. Spent: one hundred and "
   "one pounds eighty. Counts: four, all matched. Adjustments: none. Categorising: six minutes. "
   "A note says the third and fourth numbers are the control and the fifth is why anybody keeps "
   "using it."),
  ("p", "That last number is the one to watch over a year. A month-end that takes six minutes "
        "stays done. One that creeps up to forty because the pre-fill is not working or "
        "receipts are arriving unread will quietly stop happening, and the first sign will be a "
        "tin that has not been counted since March."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="receipt",
 volumes=[(40, "40 receipts"), (120, "120 receipts"), (400, "400 receipts")],
 read_each=0.0026, msgs_each=0.3,
 extra=[("ocr", "Textract &mdash; every receipt photo", "#8C4FFF", 0.0015, 0.0)],
 lede=("Petty cash volume is genuinely small &mdash; a busy office tin sees perhaps forty "
       "receipts a month, and four tins across a business is a few hundred. Nothing is "
       "always-on and the messaging line is almost nothing, because a matching count is "
       "silent. Here is where each cent goes."),
 takeaway_extra=("Storage grows with retained photographs rather than with throughput, and a "
                 "lifecycle rule keeps it flat."),
 risks=[
  "<strong>Re-reading on every retry.</strong> A photo that fails once and is redelivered "
  "should not pay for Textract and a model call again. Key the read cache on the image digest "
  "so a retry is free.",
  "<strong>Full-resolution photographs kept forever.</strong> Phone cameras produce several "
  "megabytes per receipt, and a few hundred a month for seven years is real storage. Store a "
  "downscaled legible copy alongside the original and expire the original at your record-"
  "keeping horizon.",
  "<strong>Log retention left at never.</strong> At this volume the logs will out-cost every "
  "other line within a year. Thirty days of retention is the whole fix.",
 ],
 per_unit_note=("Textract and the model together come to well under a cent per receipt, which "
                "is the entire variable cost of the system. Everything else on the bill is the "
                "fixed band."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="pc",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the concurrency story, and the one model call."),
 outside=[
  {"title": "Capture page", "sub": ["CloudFront + S3"], "icon": "phone"},
  {"title": "Custodian list", "sub": ["Sheets API, read-only"], "icon": "team"},
  {"title": "SES outbound", "sub": ["counts, mismatches"], "icon": "email"}],
 inside=[
  {"title": "S3 + SQS", "sub": ["receipt photos,", "one receipt queue"], "icon": "bucket"},
  {"title": "Lambda x4", "sub": ["capture, read,", "count, close"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["floats, movements"], "icon": "database"}],
 note="us-east-1. One account. No path in this system moves money or authorises a spend.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The Capture page, served as static files "
  "from S3 behind CloudFront. The Custodian list, read through the Google Sheets API read-only. "
  "And SES outbound, carrying count prompts and mismatch messages. Inside the account, three "
  "groups. S3 holding receipt photographs and SQS carrying one receipt queue. Four Lambda "
  "functions named capture, read, count and close. And two DynamoDB tables named floats and "
  "movements. A note gives the region as us-east-1, one account, and states that no path in "
  "this system moves money or authorises a spend."),
 functions=[
  ["<code>pc-capture</code>", "Function URL",
   "Mints a presigned PUT, resolves the float from the photographer", "10s / 512&nbsp;MB"],
  ["<code>pc-read</code>", "S3 ObjectCreated",
   "Textract, then one Bedrock call for the total; writes the movement",
   "60s / 1024&nbsp;MB"],
  ["<code>pc-count</code>", "EventBridge + Function URL",
   "Prompts on cadence; records a count and reconciles it", "15s / 512&nbsp;MB"],
  ["<code>pc-close</code>", "Function URL",
   "Serves the month view and builds the journal export", "30s / 1024&nbsp;MB"]],
 roles=[
  ["<code>pc-capture-role</code>", "<code>s3:PutObject</code>, <code>dynamodb:GetItem</code>",
   "The photos prefix; the floats table, read"],
  ["<code>pc-read-role</code>",
   "<code>textract:AnalyzeExpense</code>, <code>bedrock:InvokeModel</code>, "
   "<code>dynamodb:UpdateItem</code>",
   "The photos prefix; one model arn; floats and movements"],
  ["<code>pc-count-role</code>",
   "<code>dynamodb:Query</code>/<code>PutItem</code>, <code>ses:SendEmail</code>",
   "Movements; one verified identity"],
  ["<code>pc-close-role</code>", "<code>dynamodb:Query</code>, <code>s3:PutObject</code>",
   "Movements, read; the exports prefix"]],
 tables=[
  ("Table: floats",
   "PK   float_id          S   office-tin\n"
   "     label             S   Office tin\n"
   "     balance           N   46.60\n"
   "     custodian         S   sam@example.com\n"
   "     count_cadence     S   weekly | daily | monthly\n"
   "     last_counted      S   2026-07-10\n"
   "     difference_code   S   the account an adjustment posts to\n\n"
   "The balance move:\n"
   "  UpdateExpression: ADD balance :delta\n"
   "Never SET. Two spends in the same second must both apply."),
  ("Table: movements",
   "PK   float_id          S   office-tin\n"
   "SK   moved_at          S   2026-07-16T09:14:02Z#mv_4f1a\n"
   "     type              S   spend | topup | adjustment | count\n"
   "     amount            N   -8.20   (signed; summing the column is the balance)\n"
   "     photo_key         S   s3://petty/2026/07/....jpg\n"
   "     vendor            S   or null\n"
   "     category          S   set at month end, not at capture\n"
   "     by                S   sam@example.com\n"
   "     corrects          S   another SK, for an adjustment\n"
   "     ttl               N   epoch, +7 years\n\n"
   "Append-only. There is no code path in this system that deletes or\n"
   "updates a movement row; a correction is a new row of type adjustment.")],
 inbound=[
  "The <strong>capture page</strong> is static files in S3 behind CloudFront with an origin "
  "access control. The link carries a signed staff token minted when somebody is added to the "
  "custodian list.",
  "<strong>Photos upload with a presigned PUT</strong> straight to S3, so a phone on a poor "
  "connection is not holding a Lambda open. The S3 event is what fires the read.",
  "<strong>The blur and edge check runs on the device</strong> before upload, because a retake "
  "is trivial while the receipt is in hand and impossible an hour later.",
  "<strong>Count links</strong> in a prompt are signed, scoped to one float and one count "
  "window, and expire after seven days."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "asked for the amount actually paid from a Textract expense analysis.",
  "<strong>Called once</strong> per photograph, keyed on the image digest, so a retry or a "
  "re-read never pays twice.",
  "<strong>The prompt is explicit</strong> that a cash-tendered line and a change line are not "
  "the total, which is the single most common extraction error on a till receipt.",
  "<strong>Output is a JSON schema</strong> with total, vendor and date, all nullable. A null "
  "total produces a question with the crop; it never produces a zero or a best guess.",
  "<strong>Category is never attempted.</strong> Categorising is a bookkeeping judgement made "
  "once a month by one person with the chart of accounts in front of them."],
 gotchas=[
  "Use ADD, not SET, on the balance. It is one word and it is the difference between a float "
  "you can trust and one where a busy afternoon silently loses a spend.",
  "Hide the expected balance while somebody is counting. A number on the screen anchors the "
  "count and the reconciliation stops being independent.",
  "Never delete a movement. A correction is a new row referencing the old one, or the float "
  "stops being evidence.",
  "Store a downscaled legible copy alongside the original photograph, and expire the original "
  "on a lifecycle rule at your actual record-keeping horizon.",
  "Block the export on an uncategorised receipt. It is the only hard block in the system and "
  "it prevents petty cash becoming one growing suspense line."],
))
