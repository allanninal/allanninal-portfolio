"""Day 78 -- 2026-07-11 -- Cash drawer reconciler."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "cash-drawer-reconciler"
NAME = "Cash drawer reconciler"

SPEC = {
 "slug": SLUG, "date": "2026-07-11", "name": NAME,
 "tagline": ("At close, somebody photographs the count sheet and the till report. Two minutes "
             "later the variance is worked out, explained where it can be, and only the ones "
             "worth a conversation reach anybody."),
 "lede": ("A small system that takes the end-of-shift count and the till report, works out the "
          "variance, tries to explain it from the day's own records -- a refund, a no-sale, a "
          "float change, a tip-out -- and surfaces only what is left. It never accuses anybody "
          "of anything and it never looks at one person in isolation. Seven posts on the same "
          "system -- one diagram at a time -- with a cost breakdown and an engineering "
          "reference at the end."),
 "keywords": ["cash reconciliation", "till variance", "retail operations", "hospitality",
              "human in the loop", "serverless"],
 "icons": ["money", "counter", "search"],
 "faq": [
  ("What is a cash drawer reconciler?",
   "A small serverless system that compares the counted cash at the end of a shift with what "
   "the till says should be there, works out the variance, and tries to explain it from the "
   "day's own records before telling anybody. Only unexplained variance above a threshold you "
   "set reaches a person."),
  ("Does it accuse staff of taking money?",
   "No, and the design is built to avoid it. Almost all variance is a mis-keyed refund, a "
   "float that was changed and not recorded, or a note miscounted at eleven at night. The "
   "system explains what it can, aggregates over time rather than reacting to single shifts, "
   "and phrases everything as a question about a till, not a person."),
  ("What does it compare against?",
   "The till or point-of-sale report for the same shift, the day's refunds and no-sales, the "
   "recorded float, and any tip-out or safe drop logged during the shift. All of those already "
   "exist; the system just puts them in one place."),
  ("What if the count sheet is handwritten?",
   "That is the normal case. A photo of the count sheet is a first-class input: Textract pulls "
   "the denomination grid and anything the reader cannot read confidently becomes a question "
   "with the crop attached, never a guessed number."),
  ("What does it cost to run?",
   "A few dollars a month for a handful of tills. Nothing is always-on. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "cash-drawer-reconciler-on-aws",
 "title": "A cash drawer reconciler on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 940,
 "desc": ("Compares the end-of-shift count with the till report, explains the variance from "
          "the day's own records, and surfaces only what is left. AWS, about $3 a month."),
 "og": ("Takes the count sheet and the till report, works out the variance, explains what it "
        "can from refunds, no-sales and float changes, and only then tells a person."),
 "abstract": ("The whole system on one page -- a reader, an explainer and a surfacer -- plus "
              "the rule that keeps it decent: it explains before it reports, and it never "
              "looks at one shift in isolation."),
 "lede": ("Cash variance is the most emotionally loaded number in a small business. It is "
          "usually four pounds, it is almost always somebody misreading a twenty at eleven at "
          "night, and it is nonetheless the number that quietly changes how a manager feels "
          "about a member of staff. The reason it does that is not the money. It is that "
          "nobody has time to work out where four pounds went, so the variance is recorded, "
          "unexplained, over and over, until it becomes a pattern in somebody's head. This "
          "post walks through a small system that does the working-out."),
 "tags": ["cash reconciliation", "till variance", "retail", "hospitality", "human in the loop",
          "serverless"],
 "takeaways": [
  "Two inputs at close: a photo of the count sheet and the till report for the same shift.",
  "The variance is explained from the day's own records before anybody is told about it.",
  "Only unexplained variance above a threshold you set ever reaches a person.",
  "Nothing is reported on a single shift. The unit of attention is a till over a fortnight.",
  "Designed on AWS for about $3 a month for a handful of tills.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Close-of-shift count", "sub": ["photo of the sheet"], "icon": "image"},
      {"title": "Till report", "sub": ["POS export or email"], "icon": "money"},
      {"title": "Manager", "sub": ["sees patterns, not shifts"], "icon": "person"}],
    "inside": [
      {"title": "Reader", "sub": ["count and takings", "into one shift record"], "icon": "ocr"},
      {"title": "Explainer", "sub": ["refunds, no-sales,", "float, drops"], "icon": "search"},
      {"title": "Surfacer", "sub": ["what is left,", "over time"], "icon": "chart"}],
    "edges": [{"from": 0, "to": 0, "label": "counted cash"},
              {"from": 1, "to": 1, "label": "expected cash"},
              {"from": 2, "to": 2, "label": "only what persists", "up": True}],
    "note": "A four-pound variance on a Tuesday is noise. Four pounds every Tuesday is a finding."}),
   "Two inputs, three pieces, and one deliberate delay. Nothing about a single shift is "
   "reported; the surfacer only speaks when a pattern survives across a fortnight.",
   "System: a count sheet and a till report, three pieces inside AWS",
   "Three boxes across the top sit outside the AWS account. On the left, Close-of-shift count: "
   "a photograph of the handwritten count sheet. In the middle, Till report: the point-of-sale "
   "export or emailed summary for the same shift. On the right, Manager: the person who sees "
   "patterns rather than individual shifts. Each connects by an arrow to the AWS account "
   "container below. The count supplies the cash actually there; the till report supplies what "
   "should have been there. Inside the AWS account are three components in a row. On the left, "
   "the Reader, which turns the count and the takings into one shift record. In the middle, the "
   "Explainer, which tries to account for the difference using the day's refunds, no-sales, "
   "float changes and safe drops. On the right, the Surfacer, which holds what is left and only "
   "reports when it persists. A note at the bottom says a four-pound variance on a Tuesday is "
   "noise and four pounds every Tuesday is a finding."),
  ("h3", "What you set up once (the outside)"),
  ("ul", [
   "<strong>A count sheet.</strong> Whatever you already use &mdash; a denomination grid on "
   "paper is the common case and works fine. It is photographed at close and that is the whole "
   "submission. Covered in Part 2.",
   "<strong>A till report.</strong> Most points of sale can email or export an end-of-shift "
   "summary. That summary is the source for expected cash, card totals, refunds and no-sales. "
   "If yours only prints, a photo of the printout works exactly like the count sheet does.",
   "<strong>A thresholds tab.</strong> One sheet: the variance below which nothing is ever "
   "said, the number of shifts a pattern has to survive before it is surfaced, and the float "
   "each till is supposed to start with. Setting the first two too tight is the main way this "
   "kind of system goes wrong.",
  ]),
  ("h3", "What runs at every close (the inside)"),
  ("ul", [
   "<strong>The reader.</strong> Turns a photographed denomination grid into a total, and the "
   "till report into expected cash, refunds and no-sales. A digit it cannot read confidently is "
   "marked unreadable and asked about rather than guessed, because a misread five is a "
   "forty-five pound variance out of nothing.",
   "<strong>The explainer.</strong> Takes the raw difference and works through the day's own "
   "records looking for it: a refund given in cash but rung as card, a no-sale near the "
   "variance amount, a float that was topped up and not recorded, a safe drop logged after the "
   "count. Most variance is explained here and never becomes a variance at all.",
   "<strong>The surfacer.</strong> Holds what is left. It does not report a shift. It watches "
   "the residual variance per till over a rolling window, and speaks only when the pattern "
   "clears a threshold &mdash; consistently short, consistently over, or a single amount large "
   "enough that waiting would be silly.",
  ]),
  ("h2", "One close, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Counted", "sub": ["photo at close"], "icon": "image"},
      {"title": "Compared", "sub": ["counted vs expected"], "icon": "counter"},
      {"title": "Explained", "sub": ["refunds, no-sales, float"], "icon": "search"},
      {"title": "Residual", "sub": ["what is genuinely left"], "icon": "filter"},
      {"title": "Watched", "sub": ["over a fortnight"], "icon": "chart"}],
    "title": "ONE CLOSE, END TO END",
    "note": "Only the fifth stage ever produces a message, and usually it does not."}),
   "The same system as one line. The unusual part is the last stage: the output of a close is "
   "not a report, it is a data point in a window.",
   "One end-of-shift close, in five stages",
   "A horizontal row of five boxes joined by arrows. Counted: a photo taken at close. Compared: "
   "the counted cash set against the expected cash. Explained: the difference is attributed to "
   "refunds, no-sales and float changes where possible. Residual: what is genuinely left over. "
   "Watched: the residual is tracked over a fortnight. A note says only the fifth stage ever "
   "produces a message, and usually it does not."),
  ("h2", "In plain words"),
  ("p", "Your evening supervisor closes till two at eleven. She photographs the count sheet and "
        "the till printout. The reader makes the count £412.50 and the expected cash £429.00, a "
        "variance of £16.50 short. Before anybody sees that number, the explainer opens the "
        "day's records: there is a refund at 18:42 for £16.50, rung as card, and the note on it "
        "says \"gave cash\". That accounts for the whole variance. The shift is recorded as "
        "explained, the residual is zero, and nobody is told anything at all."),
  ("p", "The following Thursday the same till is £6.20 short with nothing to explain it. That "
        "is a data point, not an event, and nobody hears about it. Three Thursdays later the "
        "surfacer notices that till two is short on Thursday evenings and not on any other "
        "shift, by between five and eight pounds, four times running. That is when it says "
        "something &mdash; and what it says is \"till 2, Thursday evenings, consistently £5-8 "
        "short over four shifts\", which is a question about a shift pattern rather than an "
        "allegation about a person. Nine times out of ten the answer turns out to be the "
        "Thursday delivery driver being paid in cash out of the till."),
  ("callout", "Design rules that shaped every decision", [
   "Explain before you report. Most variance has a cause sitting in the day's own records, and "
   "finding it is the entire job.",
   "Never report a single shift. The unit of attention is a till over a window, because one "
   "shift is almost pure noise.",
   "Talk about tills and shift patterns, not people. The system does not know who was on, and "
   "deliberately does not ask.",
   "An unreadable digit is a question, not a number. A misread five becomes a forty-five pound "
   "phantom variance and destroys trust in the whole thing.",
   "The thresholds are yours, in a sheet. Set them loose; a system that flags every four pounds "
   "gets switched off within a month.",
   "Over is as interesting as short. A till that is consistently over is usually a pricing or "
   "keying problem and costs you customers rather than cash.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The two common approaches both do harm. One is to record variance in a book and never "
        "look at it, which means real problems run for months and everybody knows the book is "
        "theatre. The other is to review it nightly, which means somebody in authority looks at "
        "a four-pound difference every day with no time to investigate it, and forms an "
        "impression instead. The second is worse, because impressions formed from unexplained "
        "numbers are almost impossible to dislodge and are frequently about the wrong person."),
  ("p", "The shape above puts the effort where it is cheap &mdash; the explaining, which is "
        "tedious lookup work a computer is good at &mdash; and puts a deliberate delay where "
        "the harm is. Nothing is said until a pattern survives a window. In exchange for "
        "learning about a genuine problem a fortnight later than you might have, you stop "
        "having a hundred and four unexplained conversations a year."),
  ("p", "The next four posts walk through each piece: how a close gets recorded, how a variance "
        "gets explained, how a pattern gets surfaced, and how a finding gets closed. One "
        "diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-close-gets-recorded",
 "title": "How a close gets recorded",
 "nav": "How a close is recorded",
 "read": 6, "words": 890,
 "desc": ("A photo of the count sheet, a till report from wherever it comes from, and how the "
          "two get matched to the same shift without anybody typing a reference."),
 "og": ("Two inputs that arrive separately and must be paired: a photographed denomination "
        "grid and a till report. How they get matched, and what happens when only one turns "
        "up."),
 "abstract": ("Two inputs that arrive separately and must be paired -- a photographed count "
              "sheet and a till report. How they get matched to one shift, and what happens "
              "when only one of them shows up."),
 "lede": ("This is the only system in this series with two inputs that arrive independently, "
          "minutes or hours apart, from different sources, with no shared identifier between "
          "them. Getting them paired without asking a supervisor to type a shift reference at "
          "eleven at night is most of the engineering, and it is worth doing properly, because "
          "the alternative is the thing everybody does: a spreadsheet, filled in on Sunday, "
          "from memory."),
 "tags": ["cash reconciliation", "Amazon Textract", "OCR", "record matching", "DynamoDB",
          "serverless"],
 "takeaways": [
  "Two inputs, arriving separately: a photographed count sheet and a till report.",
  "They are paired on till, date and shift window -- never on a reference somebody has to type.",
  "A close with only one half is held, not discarded, and chased the next morning.",
  "Unreadable denominations produce a question with the crop attached, never a guess.",
  "The denomination breakdown is kept, not just the total, because it is what explains a miscount.",
 ],
 "blocks": [
  ("h2", "Two inputs, one shift"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Count sheet photo", "sub": ["denomination grid"], "icon": "image",
       "label": "counted"},
      {"title": "POS export", "sub": ["emailed at close"], "icon": "money", "label": "expected"},
      {"title": "Printout photo", "sub": ["if the POS only prints"], "icon": "phone",
       "label": "expected"}],
    "target": {"title": "One shift record", "sub": ["till, date, window,", "counted, expected"],
               "icon": "database",
               "then": {"title": "Explainer", "sub": ["once both halves land"], "icon": "search"}},
    "note": "Matched on till, date and window. Nobody types a reference at eleven at night."}),
   "The two halves of a close and the three ways they arrive. Pairing is done on facts the "
   "inputs already carry, because any scheme that needs a typed reference will be skipped.",
   "Two independent inputs converging on one shift record",
   "Three boxes stacked on the left. Count sheet photo, carrying the denomination grid and "
   "labelled counted. POS export, emailed at close and labelled expected. And Printout photo, "
   "for a point of sale that only prints, also labelled expected. All three converge on One "
   "shift record on the right, holding the till, the date, the shift window, the counted total "
   "and the expected total. Below it, connected by a downward arrow, is the Explainer, which "
   "runs once both halves have landed. A note says the halves are matched on till, date and "
   "window, and that nobody types a reference at eleven at night."),
  ("h3", "How the halves get paired"),
  ("p", "Three facts are available without asking anybody for anything: which till, which date, "
        "and roughly what time. The till comes from the photo itself in most shops &mdash; the "
        "count sheet has a till number on it, or the photo came from a device assigned to a "
        "till. The date and time come from the upload. The till report carries all three "
        "explicitly."),
  ("p", "So the pairing rule is: same till, same business date, and shift windows that overlap. "
        "The business date is not the calendar date, which matters enormously in hospitality "
        "&mdash; a close at 01:20 belongs to the previous day, and getting that wrong makes "
        "every Friday night look like a Saturday morning with no takings. The business-day "
        "cutover is a number in the thresholds sheet."),
  ("h2", "Reading a denomination grid"),
  ("fig", ("chain", {
    "entry": {"title": "Count photo", "sub": ["taken at close"], "icon": "image"},
    "steps": [
      {"title": "Store the original", "sub": ["S3, kept as evidence"], "icon": "bucket"},
      {"title": "This close before?", "sub": ["till + business date"], "icon": "branch",
       "side": {"title": "DynamoDB shifts", "sub": ["draft, replaceable"], "icon": "database"},
       "exit": {"title": "Replace the draft", "sub": ["recount, not a second"], "icon": "retry",
                "label": "recount"}},
      {"title": "Pull the grid", "sub": ["Textract tables"], "icon": "ocr"},
      {"title": "Read denominations", "sub": ["count x value per row"], "icon": "model"},
      {"title": "Rows sum to the total?", "sub": ["the written total"], "icon": "branch",
       "exit": {"title": "Ask about the sheet", "sub": ["show the crop"], "icon": "person",
                "label": "mismatch"}},
      {"title": "Wait for the other half", "sub": ["or chase it in the morning"], "icon": "clock"}],
    "note": "The written total is a checksum. If the rows do not sum to it, the read is wrong, not the count."}),
   "Reading the count sheet. The written grand total is used as a checksum on the machine read, "
   "which catches almost every OCR error before it becomes a phantom variance.",
   "How a photographed count sheet becomes a counted total",
   "A vertical chain of six steps inside the AWS account, entered by a box labelled Count "
   "photo, taken at close. Step one stores the original in S3 as evidence. Step two asks "
   "whether this close has been submitted before, keyed on till and business date against a "
   "DynamoDB shifts table; a recount exits to Replace the draft rather than creating a second "
   "close. Step three pulls the grid with Amazon Textract table extraction. Step four reads the "
   "denominations, multiplying the count by the value on each row. Step five checks whether the "
   "rows sum to the total written on the sheet, exiting to Ask about the sheet with the crop "
   "shown if they do not. Step six waits for the other half of the close, or chases it in the "
   "morning. A note says the written total is a checksum, and that if the rows do not sum to it "
   "the read is wrong rather than the count."),
  ("h3", "The written total as a checksum"),
  ("p", "This is the single most valuable trick in the design and it costs nothing. Every count "
        "sheet has a grand total written at the bottom by the person who counted. The machine "
        "read produces its own total from the denomination rows. If those two agree, the read "
        "is almost certainly right. If they disagree, something was misread &mdash; and "
        "crucially, the system now knows that before producing a variance."),
  ("p", "Without it, a misread \"3\" in the twenties row as \"8\" produces a hundred-pound "
        "variance that looks exactly like a serious problem, and the first person to see it is "
        "a manager. With it, the same misread produces a question to the supervisor with the "
        "crop of the twenties row attached, and it is resolved in four seconds by the person "
        "who wrote it."),
  ("h2", "When only one half arrives"),
  ("ul", [
   "<strong>Count but no till report.</strong> Usually a POS export that failed to send. The "
   "shift is held as incomplete, and if the report has not arrived by the next morning's "
   "opening the supervisor is asked for a photo of the printout. Nothing is computed from a "
   "half.",
   "<strong>Till report but no count.</strong> Usually somebody forgot to photograph the sheet "
   "before going home. Held the same way, chased the same way, and never inferred &mdash; a "
   "count is the one number in this system that cannot be reconstructed.",
   "<strong>Neither, on a day the till was open.</strong> The most important case, and the "
   "easiest to miss. The thresholds sheet knows which tills trade on which days; a trading day "
   "with no close at all is chased in the morning, because a missing close is a much bigger "
   "signal than any variance.",
   "<strong>Two counts, one report.</strong> A recount. The second replaces the first as a "
   "draft, both photos are kept, and the fact that a recount happened is recorded &mdash; it is "
   "occasionally the interesting part.",
  ]),
  ("p", "Next: what the explainer does with the difference before anybody hears about it."),
 ],
},
{
 "slug": "how-a-variance-gets-explained",
 "title": "How a variance gets explained",
 "nav": "How it is explained",
 "read": 6, "words": 910,
 "desc": ("Working through the day's own records for the missing money -- cash refunds rung as "
          "card, no-sales, float changes, safe drops and tip-outs -- before anybody is told a "
          "number."),
 "og": ("Most variance is already explained by the day's own records. Five lookups, run in "
        "order of likelihood, before any number reaches a person."),
 "abstract": ("Five lookups run in order of likelihood -- cash refunds rung as card, no-sales, "
              "float changes, safe drops and tip-outs -- most of which explain the whole "
              "variance before anybody is told a number."),
 "lede": ("This is the part that everybody skips, because doing it by hand takes fifteen "
          "minutes per shift and there is a queue at the door. It is also the part that turns "
          "an accusation into an explanation. The explainer's job is to spend those fifteen "
          "minutes, on every single shift, in about eight hundred milliseconds."),
 "tags": ["cash reconciliation", "till variance", "refunds", "float management", "retail",
          "serverless"],
 "takeaways": [
  "Five lookups, run in order of how often each one turns out to be the answer.",
  "A cash refund rung as card is the single most common cause, by a wide margin.",
  "An explanation must match on both amount and direction, within a small tolerance.",
  "Partial explanations are kept. Explaining £16.50 of a £22 variance is most of the work.",
  "The explainer never invents a cause. Unexplained is a legitimate and common outcome.",
 ],
 "blocks": [
  ("h2", "Five lookups, in order"),
  ("fig", ("chain", {
    "entry": {"title": "Raw variance", "sub": ["counted minus expected"], "icon": "counter"},
    "steps": [
      {"title": "Cash refund, card key?", "sub": ["amount and direction"], "icon": "branch",
       "side": {"title": "Refunds that shift", "sub": ["from the POS report"], "icon": "money"},
       "exit": {"title": "Explained", "sub": ["note the refund id"], "icon": "check",
                "label": "match"}},
      {"title": "No-sale near the amount?", "sub": ["within tolerance"], "icon": "branch",
       "side": {"title": "No-sale log", "sub": ["time and drawer"], "icon": "log"},
       "exit": {"title": "Likely explained", "sub": ["flag as probable"], "icon": "search",
                "label": "close"}},
      {"title": "Float changed?", "sub": ["opening vs expected"], "icon": "branch",
       "side": {"title": "Float record", "sub": ["from the thresholds tab"], "icon": "doc"},
       "exit": {"title": "Explained", "sub": ["record the new float"], "icon": "check",
                "label": "differs"}},
      {"title": "Safe drop after count?", "sub": ["timestamp order"], "icon": "branch",
       "side": {"title": "Drop log", "sub": ["amount and time"], "icon": "lock"},
       "exit": {"title": "Explained", "sub": ["ordering, not loss"], "icon": "check",
                "label": "after"}},
      {"title": "Tip-out taken?", "sub": ["hospitality only"], "icon": "branch",
       "exit": {"title": "Explained", "sub": ["and paid, not lost"], "icon": "check",
                "label": "logged"}},
      {"title": "Residual variance", "sub": ["what is genuinely left"], "icon": "filter"}],
    "note": "Order matters: the first lookup explains more shifts than the other four combined."}),
   "The five explanations, tried in order of how often each one is the answer. Anything left "
   "after all five is the residual, and only the residual is ever watched.",
   "The five lookups that try to explain a cash variance",
   "A vertical chain of six steps entered by a box labelled Raw variance, meaning counted minus "
   "expected. Step one asks whether a cash refund was rung as card, matching on amount and "
   "direction against the shift's refunds from the point-of-sale report; a match exits to "
   "Explained, noting the refund id. Step two asks whether a no-sale happened near the "
   "variance amount, checking the no-sale log for time and drawer; a close match exits to "
   "Likely explained, flagged as probable. Step three asks whether the float was changed, "
   "comparing the opening float with the expected one from the thresholds tab; a difference "
   "exits to Explained, recording the new float. Step four asks whether a safe drop happened "
   "after the count, comparing timestamps; a drop after the count exits to Explained, since it "
   "is an ordering problem rather than a loss. Step five asks whether a tip-out was taken, "
   "which applies in hospitality only; a logged tip-out exits to Explained. Step six is the "
   "Residual variance, what is genuinely left. A note says order matters, and the first lookup "
   "explains more shifts than the other four combined."),
  ("h3", "Cash refunds rung as card"),
  ("p", "This is the answer more often than everything else put together, and the reason is "
        "mundane. A customer returns something, the member of staff refunds them in cash "
        "because that is what the customer wants, and rings it through as a card refund because "
        "that is what the original sale was. The till now believes there is money in the drawer "
        "that somebody handed over an hour ago."),
  ("p", "Matching is on amount and direction: a variance short by exactly the value of a card "
        "refund from the same shift is that refund, with very high confidence. The system notes "
        "the refund id in the explanation, which has a useful side effect &mdash; the same "
        "refund id appearing in explanations week after week is a training signal about one "
        "till or one procedure."),
  ("h3", "Why tolerances differ by lookup"),
  ("ul", [
   "<strong>Refunds: exact.</strong> A refund is a specific number that appeared in a specific "
   "report. If the variance is not that number to the penny, this is not the explanation, and "
   "loosening it here would explain away real problems.",
   "<strong>No-sales: loose.</strong> A no-sale is a drawer opening with no transaction, and "
   "the system never knows what was taken out or put in. A no-sale close in time to a variance "
   "of a plausible size is evidence, not proof, and it is recorded as probable rather than "
   "explained.",
   "<strong>Float changes: exact.</strong> The float is a number somebody wrote down. Either it "
   "differs from expected by the variance amount or it does not.",
   "<strong>Safe drops: exact, with a time test.</strong> A drop is an amount and a timestamp. "
   "The interesting case is a drop recorded after the count time, which is not a loss at all "
   "&mdash; it is two records made in the wrong order, and it is common at the end of a busy "
   "shift.",
  ]),
  ("h2", "Partial explanations count"),
  ("p", "A £22 variance with a £16.50 cash-refund match is not unexplained. It is £16.50 "
        "explained and £5.50 residual, and the residual is what goes into the window. Systems "
        "that treat explanation as all-or-nothing throw away most of their own work and end up "
        "watching noise."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Raw", "sub": ["£22.00 short"], "icon": "counter"},
      {"title": "Refund", "sub": ["-£16.50 explained"], "icon": "money"},
      {"title": "No-sale", "sub": ["none near it"], "icon": "search"},
      {"title": "Float", "sub": ["as expected"], "icon": "doc"},
      {"title": "Residual", "sub": ["£5.50, into the window"], "icon": "filter"}],
    "title": "ONE VARIANCE, EXPLAINED IN PARTS",
    "note": "Three quarters of it had a cause sitting in the day's own records."}),
   "One shift's variance worked through the five lookups. Most of it is explained; the small "
   "remainder is the only number that goes anywhere.",
   "A single cash variance explained in parts",
   "A horizontal row of five boxes. Raw: twenty-two pounds short. Refund: sixteen pounds fifty "
   "of that is explained by a cash refund rung as card. No-sale: none near the amount. Float: "
   "as expected. Residual: five pounds fifty, which goes into the watching window. A note says "
   "three quarters of it had a cause sitting in the day's own records."),
  ("callout", "What the explainer will not do", [
   "It does not invent a cause. Unexplained is a normal, frequent, completely acceptable "
   "outcome, and pretending otherwise is how a reconciliation system starts lying.",
   "It does not chain explanations. Two refunds that happen to sum to the variance is a "
   "coincidence at small amounts, and treating it as an explanation would hide real losses.",
   "It does not look at who was on shift. It has no staff data and does not request any, which "
   "removes an entire category of misuse.",
   "It does not adjust the till. The variance is a fact about a shift and stays recorded even "
   "once it is fully explained.",
  ]),
  ("p", "Next: what happens to the residual, and the window that decides whether anybody hears "
        "about it."),
 ],
},
{
 "slug": "how-a-cash-pattern-gets-surfaced",
 "title": "How a cash pattern gets surfaced",
 "nav": "How a pattern surfaces",
 "read": 5, "words": 870,
 "desc": ("The rolling window, the three patterns worth reporting, why a single shift never "
          "triggers anything, and the one case that skips the window entirely."),
 "og": ("A rolling window over residual variance per till. Three patterns are worth reporting; "
        "single shifts never are; and exactly one case skips the window."),
 "abstract": ("A rolling window over residual variance per till and shift slot. Three patterns "
              "are worth a message, single shifts never are, and exactly one case skips the "
              "window entirely."),
 "lede": ("Everything so far has been about getting an honest residual number. This post is "
          "about the discipline of not doing anything with it. A single shift's residual "
          "variance carries almost no information: the distribution of honest miscounts at "
          "eleven at night is wide, and any threshold tight enough to catch a real problem in "
          "one shift will fire constantly on nothing."),
 "tags": ["cash reconciliation", "anomaly detection", "reporting", "retail operations",
          "serverless"],
 "takeaways": [
  "Nothing is reported on a single shift, with exactly one exception.",
  "The window is per till and per shift slot, because Thursday evening is a different animal from Monday morning.",
  "Three patterns are worth a message: consistently short, consistently over, and rising spread.",
  "Consistently over matters as much as short; it is usually a pricing or keying problem.",
  "The exception is a residual so large that waiting would be absurd, and that threshold is yours.",
 ],
 "blocks": [
  ("h2", "The window"),
  ("p", "The unit of attention is a till and a shift slot &mdash; till 2, Thursday evening "
        "&mdash; over a rolling number of occurrences rather than a number of days. That "
        "distinction matters for anywhere that does not trade the same hours every day. Four "
        "Thursday evenings is four data points whether they took a fortnight or a month."),
  ("fig", ("chain", {
    "entry": {"title": "Residual variance", "sub": ["one shift"], "icon": "filter"},
    "steps": [
      {"title": "Big enough alone?", "sub": ["the skip-the-window line"], "icon": "branch",
       "side": {"title": "Thresholds tab", "sub": ["yours, in a sheet"], "icon": "doc"},
       "exit": {"title": "Tell somebody now", "sub": ["one shift, one message"], "icon": "alarm",
                "label": "over"}},
      {"title": "Add to the window", "sub": ["till + shift slot"], "icon": "counter",
       "side": {"title": "DynamoDB windows", "sub": ["last N occurrences"], "icon": "database"}},
      {"title": "Consistently short?", "sub": ["N of the last M"], "icon": "branch",
       "exit": {"title": "Surface the pattern", "sub": ["till and slot, not a person"],
                "icon": "report", "label": "yes"}},
      {"title": "Consistently over?", "sub": ["same test, other way"], "icon": "branch",
       "exit": {"title": "Surface the pattern", "sub": ["usually pricing"], "icon": "report",
                "label": "yes"}},
      {"title": "Spread widening?", "sub": ["variance of the variance"], "icon": "branch",
       "exit": {"title": "Surface quietly", "sub": ["in the monthly summary"], "icon": "chart",
                "label": "yes"}},
      {"title": "Nothing to say", "sub": ["the usual outcome"], "icon": "check"}],
    "note": "Four of the five exits are rare. The last step is what happens on almost every shift."}),
   "What happens to a residual. One escape hatch for genuinely large amounts, then a window, "
   "then three pattern tests, and then the outcome that occurs almost every time: nothing.",
   "How a residual variance becomes a pattern worth reporting",
   "A vertical chain of six steps entered by a box labelled Residual variance for one shift. "
   "Step one asks whether it is big enough on its own to skip the window, reading the line from "
   "the thresholds tab; if it is over, it exits to Tell somebody now, one shift and one "
   "message. Step two adds the residual to the window for that till and shift slot, held in a "
   "DynamoDB windows table covering the last N occurrences. Step three asks whether the till is "
   "consistently short, N of the last M, exiting to Surface the pattern, described by till and "
   "slot rather than by person. Step four asks the same question the other way for consistently "
   "over, which is usually a pricing problem. Step five asks whether the spread is widening, "
   "exiting to Surface quietly in the monthly summary. Step six is Nothing to say, the usual "
   "outcome. A note says four of the five exits are rare and the last step is what happens on "
   "almost every shift."),
  ("h3", "Consistently short"),
  ("p", "N of the last M occurrences short by more than the noise threshold, in the same "
        "direction. Four of the last five is a reasonable default. The message names the till "
        "and the slot, gives the amounts, and says nothing else &mdash; because at this point "
        "the system genuinely does not know whether the cause is theft, a recurring cash "
        "payment nobody wrote down, a float that was permanently changed, or a scale that "
        "weighs light."),
  ("h3", "Consistently over"),
  ("p", "The same test in the other direction, and the one that most systems ignore entirely. A "
        "till that is regularly over is not a happy accident: it usually means customers are "
        "being overcharged, or a keying habit is producing sales at the wrong price, or "
        "somebody is short-changing people. It costs you customers rather than cash, which is "
        "worse, and it is invisible to anybody who only looks for shortages."),
  ("h3", "Widening spread"),
  ("p", "The subtlest of the three: the average residual is fine but the swing is growing. That "
        "usually means the counting itself has got sloppy &mdash; a new person, a rushed close, "
        "a broken note counter. It never generates a message on its own, because it is weak "
        "evidence, but it appears in the monthly summary where a manager can put it next to "
        "everything else they know."),
  ("h2", "What the message actually says"),
  ("callout", "The whole message, in order", [
   "<strong>Line one.</strong> The till and the slot. \"Till 2, Thursday evenings.\"",
   "<strong>Line two.</strong> The pattern, with the numbers. \"Short by £5&ndash;8 on four of "
   "the last five, after refunds and no-sales were accounted for.\"",
   "<strong>Line three.</strong> What was already ruled out. \"No matching refunds, no-sales or "
   "float changes on any of the four.\"",
   "<strong>One button.</strong> \"I know why &mdash; here's what it is\", which records a "
   "cause against that till and slot and stops the pattern being reported again.",
   "<strong>No names.</strong> The system does not hold who was on shift, so it cannot name "
   "anybody even if asked. That is a design choice, not an oversight.",
  ]),
  ("p", "The absence of names is worth defending. It would be easy to join the shift record "
        "against a rota and produce a per-person variance report, and every business that has "
        "ever built one has regretted it. The number is dominated by which till somebody works, "
        "how busy their shifts are and how often they handle refunds, none of which is about "
        "them. A per-till pattern points a manager at a real question. A per-person league table "
        "points them at the person who works the busiest till."),
  ("p", "Next: what happens to a surfaced pattern &mdash; how it gets closed, and what the "
        "monthly summary is actually for."),
 ],
},
{
 "slug": "how-a-cash-finding-gets-closed",
 "title": "How a cash finding gets closed",
 "nav": "How a finding closes",
 "read": 5, "words": 840,
 "desc": ("Recording a cause against a till and slot, why a closed finding suppresses future "
          "reports, the monthly summary, and the two numbers that say whether the thresholds "
          "are right."),
 "og": ("A finding is closed by recording a cause, which suppresses the same pattern until it "
        "changes. The monthly summary is two numbers about the money and two about the "
        "thresholds."),
 "abstract": ("A finding closes by recording a cause, which suppresses that pattern until it "
              "changes shape. The monthly summary carries two numbers about the money and two "
              "about whether the thresholds are set right."),
 "lede": ("A surfaced pattern is a question, and questions need answers or they come back "
          "every week until somebody mutes the whole system. This post is about closing the "
          "loop: recording what the cause turned out to be, using that to suppress the same "
          "message, and reading the monthly summary that tells you whether any of the "
          "thresholds are set anywhere near right."),
 "tags": ["cash reconciliation", "reporting", "operations", "DynamoDB", "retail", "serverless"],
 "takeaways": [
  "A finding closes by recording a cause, in free text, against a till and slot.",
  "A recorded cause suppresses the same pattern until the pattern changes shape.",
  "Suppressions expire. A cause recorded in March stops suppressing by summer.",
  "The monthly summary is four numbers: two about money, two about the thresholds.",
  "If nothing is ever surfaced, the thresholds are too loose -- and that is also a finding.",
 ],
 "blocks": [
  ("h2", "Recording a cause"),
  ("p", "The one button on a surfaced pattern opens a free-text line. Not a dropdown: the "
        "useful causes are always the ones nobody anticipated, and a dropdown of six options "
        "produces six months of \"Other\"."),
  ("table", ["Field", "Example", "Why it is there"], [
   ["<code>till</code>", "till-2", "Which drawer"],
   ["<code>slot</code>", "thu-evening", "Which shift pattern, not which person"],
   ["<code>pattern</code>", "short 5-8 on 4 of 5", "What was reported"],
   ["<code>cause</code>", "Thursday bakery delivery paid cash from the drawer", "In their words"],
   ["<code>action</code>", "petty cash tin from 1 Aug", "What changed, if anything"],
   ["<code>recorded_by</code>", "manager@example.com", "Who answered"],
   ["<code>suppress_until</code>", "2026-10-11", "When this stops muting the pattern"],
   ["<code>shape</code>", "short|5.00|8.00|thu-evening", "What it suppresses, exactly"],
  ]),
  ("p", "The <code>shape</code> field is what makes suppression safe. A recorded cause "
        "suppresses <em>that</em> pattern &mdash; same till, same slot, same direction, similar "
        "magnitude. If till 2 starts being short by thirty pounds on Thursday evenings, that is "
        "a different shape and it surfaces immediately, cause on record or not. Suppressing by "
        "till alone would be how a genuine problem hides behind a bakery delivery."),
  ("h3", "Why suppressions expire"),
  ("p", "The cause recorded in March is often no longer true in July. The delivery driver "
        "changed, the petty cash tin was introduced, the till was moved. A suppression that "
        "never expires quietly turns into a permanent blind spot, and the blind spots "
        "accumulate one at a time until the system reports nothing at all. Ninety days is a "
        "reasonable default and it lives in the thresholds sheet."),
  ("h2", "The monthly summary"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Closes", "sub": ["112 shifts"], "icon": "clock"},
      {"title": "Explained", "sub": ["£418 of £491"], "icon": "search"},
      {"title": "Residual", "sub": ["£73 net"], "icon": "money"},
      {"title": "Surfaced", "sub": ["2 patterns"], "icon": "report"},
      {"title": "Still open", "sub": ["0"], "icon": "check"}],
    "title": "ONE MONTH, IN FIVE NUMBERS",
    "note": "The second number is the system's actual output. The fourth says if the thresholds fit."}),
   "A month of closes in five numbers. The explained figure is the one that justifies the "
   "system; the surfaced count is the one that tells you whether the thresholds need moving.",
   "One month of cash reconciliation in five numbers",
   "A horizontal row of five boxes. Closes: one hundred and twelve shifts. Explained: four "
   "hundred and eighteen pounds of four hundred and ninety-one pounds of raw variance. "
   "Residual: seventy-three pounds net. Surfaced: two patterns. Still open: zero. A note says "
   "the second number is the system's actual output and the fourth says whether the thresholds "
   "fit."),
  ("ul", [
   "<strong>Explained versus raw</strong> is the number that justifies the whole project. "
   "Eighty-five per cent of gross variance having a documented cause is a different operational "
   "reality from a variance book full of unexplained figures, and it is the number to put in "
   "front of whoever asked what this was for.",
   "<strong>Net residual</strong> matters more than gross. A month that is seventy-three pounds "
   "net across a hundred and twelve closes is noise. The same month with four hundred pounds "
   "short and three hundred and thirty over is not noise at all &mdash; it is two problems "
   "cancelling each other out in a total.",
   "<strong>Patterns surfaced</strong> calibrates the thresholds. Zero for three months running "
   "means they are too loose and the system is decorative. More than a handful a month means "
   "they are too tight and people are learning to dismiss it.",
   "<strong>Still open</strong> is the only one that is about people rather than money. A "
   "surfaced pattern nobody has answered in a month means the messages are going somewhere "
   "nobody reads.",
  ]),
  ("h2", "The case for reporting nothing"),
  ("p", "It is worth saying plainly that the best possible month for this system is one where "
        "it sends no messages at all &mdash; a hundred and twelve closes read, every variance "
        "either explained or too small to matter, and nobody's evening interrupted. That is not "
        "the system failing to find anything. It is the system doing the fifteen minutes of "
        "lookup work per shift that nobody was ever going to do, and correctly concluding that "
        "there was nothing there."),
  ("p", "The value in those months is not the messages that were not sent. It is that the "
        "variance book now has causes in it, that the numbers are computed the same way every "
        "time by something that is not tired, and that when a real pattern does appear, it "
        "appears against three months of quiet rather than three months of noise."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="close",
 volumes=[(60, "60 closes"), (180, "180 closes"), (600, "600 closes")],
 read_each=0.0034, msgs_each=0.4,
 extra=[("ocr", "Textract &mdash; count sheets and printouts", "#8C4FFF", 0.0038, 0.0)],
 lede=("A shop with two tills trading six days a week makes about fifty closes a month; a "
       "small chain with five sites makes a few hundred. Nothing here is always-on, and the "
       "messaging line is unusually small because the whole design is about not sending "
       "messages. Here is where each cent goes."),
 takeaway_extra=("The messaging line is tiny on purpose: a good month sends almost no mail at "
                 "all."),
 risks=[
  "<strong>A retry loop on an unreadable photo.</strong> A dark or angled count sheet makes "
  "Textract return nothing useful, the function throws, and the queue redelivers. Without a "
  "dead-letter queue that is one bad photo costing more than a month of good ones. A maximum "
  "receive count of three fixes it.",
  "<strong>Re-reading on every recount.</strong> A supervisor recounting and rephotographing "
  "three times pays for three full reads unless the cache is keyed on the image digest rather "
  "than the shift id.",
  "<strong>Keeping every photo forever.</strong> Count sheets are small but a hundred and "
  "twelve a month for seven years is not. An S3 lifecycle rule tiering at ninety days and "
  "expiring at your actual record-keeping horizon keeps the storage line flat.",
 ],
 per_unit_note=("The Textract line is the biggest per-close cost here, because most closes "
                "involve two photographs rather than one &mdash; the count sheet and, where the "
                "point of sale only prints, the till printout. A POS that emails its export "
                "halves it."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="cd",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions "
       "and what each is allowed to touch, the three tables, and the specific model."),
 outside=[
  {"title": "Photo upload", "sub": ["count sheet, printout"], "icon": "image"},
  {"title": "POS export", "sub": ["SES inbound or S3 drop"], "icon": "money"},
  {"title": "SES outbound", "sub": ["questions, summaries"], "icon": "email"}],
 inside=[
  {"title": "S3 + SQS", "sub": ["originals,", "one shift queue"], "icon": "bucket"},
  {"title": "Lambda x5", "sub": ["intake, read, explain,", "window, report"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["shifts, windows, causes"], "icon": "database"}],
 note="us-east-1. One account. Secrets Manager holds the POS credential and the signing key.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Photo upload, covering the count sheet "
  "and any till printout. POS export, arriving either through SES inbound or as a direct S3 "
  "drop. And SES outbound, carrying the questions and the monthly summary. Inside the account, "
  "three groups. S3 holding the original photographs and SQS carrying one shift queue. Five "
  "Lambda functions named intake, read, explain, window and report. And three DynamoDB tables "
  "named shifts, windows and causes. A note gives the region as us-east-1, one account, with "
  "Secrets Manager holding the point-of-sale credential and the link-signing key."),
 functions=[
  ["<code>cd-intake</code>", "S3 ObjectCreated + SES inbound",
   "Pairs the two halves on till, business date and window", "10s / 512&nbsp;MB"],
  ["<code>cd-read</code>", "SQS shift queue",
   "Textract on photos, then one Bedrock call into denominations", "60s / 1024&nbsp;MB"],
  ["<code>cd-explain</code>", "SQS read queue",
   "The five lookups against refunds, no-sales, float and drops", "10s / 512&nbsp;MB"],
  ["<code>cd-window</code>", "SQS residual queue",
   "Updates the rolling window and runs the three pattern tests", "10s / 512&nbsp;MB"],
  ["<code>cd-report</code>", "EventBridge monthly + Function URL",
   "Builds the summary; handles the signed cause-recording links", "30s / 1024&nbsp;MB"]],
 roles=[
  ["<code>cd-intake-role</code>", "<code>s3:GetObject</code>, <code>sqs:SendMessage</code>",
   "The uploads prefix; the shift queue only"],
  ["<code>cd-read-role</code>",
   "<code>textract:AnalyzeDocument</code>, <code>bedrock:InvokeModel</code>",
   "The uploads prefix; one model arn"],
  ["<code>cd-explain-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Shifts table; the POS credential only"],
  ["<code>cd-window-role</code>", "<code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Windows and causes; one verified identity"],
  ["<code>cd-report-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "All three tables, read; one verified identity"]],
 tables=[
  ("Table: shifts",
   "PK   till              S   till-2\n"
   "SK   business_date     S   2026-07-11\n"
   "     state             S   half | complete | explained | held\n"
   "     counted           N   412.50\n"
   "     expected          N   429.00\n"
   "     denominations     L   [{value, count, confidence}]\n"
   "     written_total     N   412.50   -- the checksum from the sheet\n"
   "     explanations      L   [{kind, amount, ref, confidence}]\n"
   "     residual          N   5.50\n"
   "     photo_keys        L   [s3 keys, kept as evidence]\n"
   "     ttl               N   epoch, +7 years\n\n"
   "The business date is NOT the calendar date. A 01:20 close belongs to the\n"
   "previous trading day, and the cutover hour lives in the thresholds tab."),
  ("Table: windows",
   "PK   till_slot         S   till-2|thu-evening\n"
   "     residuals         L   last M occurrences, newest first\n"
   "     short_count       N   how many of the last M were short\n"
   "     over_count        N   how many were over\n"
   "     spread            N   standard deviation of the window\n"
   "     last_surfaced     S   2026-07-11T23:14:02Z"),
  ("Table: causes",
   "PK   till_slot         S   till-2|thu-evening\n"
   "SK   recorded_at       S   2026-07-11T23:20:00Z\n"
   "     shape             S   short|5.00|8.00|thu-evening\n"
   "     cause             S   free text, in their words\n"
   "     action            S   what changed, if anything\n"
   "     recorded_by       S   manager@example.com\n"
   "     suppress_until    S   2026-10-11\n\n"
   "Suppression matches on shape, not on till. A pattern of a different\n"
   "magnitude or direction surfaces immediately regardless of any cause.")],
 inbound=[
  "<strong>Photo uploads</strong> go straight to S3 with a presigned PUT from a small static "
  "page, so a phone on a shop connection is not holding a Lambda open while it uploads.",
  "<strong>POS exports</strong> arrive either through an SES receipt rule writing to S3, or as "
  "a direct S3 drop if the point of sale can be pointed at a bucket. Both fire the same "
  "intake.",
  "<strong>Cause-recording links</strong> in a surfaced pattern are signed, scoped to one "
  "pattern, single-use, and expire after thirty days.",
  "<strong>No staff identifiers</strong> enter the system at any point. There is no rota "
  "integration, and adding one would change what this system is."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "used to turn a Textract table into denomination rows. That is extraction.",
  "<strong>Called once</strong> per photograph, keyed on the image digest, so a recount of the "
  "same photo does not pay again.",
  "<strong>Output is a JSON schema</strong> with a denomination array and a per-row confidence, "
  "plus the written grand total as a separate field so it can be used as a checksum.",
  "<strong>Grounded</strong> with the denominations in circulation for your currency, so the "
  "model matches rows to a fixed list rather than inventing a value.",
  "<strong>Nothing about the explaining</strong> touches a model. Matching a variance to a "
  "refund is a comparison, and comparisons should be code."],
 gotchas=[
  "Get the business-day cutover right before anything else. In hospitality a close after "
  "midnight belongs to the previous day, and getting it wrong makes every late-trading Friday "
  "look like a Saturday with no takings.",
  "Use the written grand total as a checksum on the machine read. It costs nothing and it "
  "removes almost every phantom variance.",
  "Do not join to a rota. The temptation is enormous and the resulting per-person report is "
  "dominated by which till somebody works rather than anything about them.",
  "Suppress on pattern shape, not on till. A cause recorded for a five-pound Thursday shortfall "
  "must not hide a thirty-pound one.",
  "Expire suppressions. A cause recorded in March is usually not true by July, and permanent "
  "suppressions accumulate into a system that reports nothing."],
))
