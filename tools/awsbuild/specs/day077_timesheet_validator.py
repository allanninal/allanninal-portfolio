"""Day 77 -- 2026-07-10 -- Timesheet validator."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "timesheet-validator"
NAME = "Timesheet validator"

SPEC = {
 "slug": SLUG, "date": "2026-07-10", "name": NAME,
 "tagline": ("Timesheets get checked the moment they are submitted rather than the night "
             "before payroll -- so the missing Thursday is a question on Friday, not a "
             "scramble on the 28th."),
 "lede": ("A small system that reads each timesheet as it arrives, checks it against the "
          "roster, the job records and the rules that actually matter, and asks the person "
          "who filled it in about anything odd -- immediately, while they still remember the "
          "week. Payroll opens on the 28th to a set of sheets that are already right. Seven "
          "posts on the same system -- one diagram at a time -- with a cost breakdown and an "
          "engineering reference at the end."),
 "keywords": ["timesheets", "payroll", "rostering", "hours validation", "human in the loop",
              "serverless"],
 "icons": ["clock", "filter", "team"],
 "faq": [
  ("What is a timesheet validator?",
   "A small serverless system that checks each timesheet when it is submitted rather than at "
   "payroll time. It compares the hours claimed against the roster and the job records, "
   "applies the break and overtime rules you wrote down, and asks the person who submitted it "
   "about anything that does not line up. A person approves; the system only ever asks."),
  ("Does it change anybody's hours?",
   "Never on its own. The only way a number changes is that the person who submitted it "
   "changes it, or a manager overrides it and the override is recorded with their name on it. "
   "The system's output is a question and a flag, not an edit."),
  ("What does it check against?",
   "Three things: the roster, which says who was expected where; the job records, which say "
   "what work was actually logged; and a rules tab holding the break, overtime and maximum-day "
   "rules for your business. All three are things a small business already keeps."),
  ("What happens if somebody forgets a day?",
   "It is caught the moment the sheet is submitted, which is usually Friday afternoon rather "
   "than the 28th. The person gets one message naming the day and what the roster expected, "
   "and a one-tap way to fill it or confirm they were off."),
  ("What does it cost to run?",
   "A few dollars a month at small-business volume. Nothing is always-on. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "timesheet-validator-on-aws",
 "title": "A timesheet validator on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 950,
 "desc": ("Checks each timesheet as it is submitted against the roster, the job records and "
          "your break and overtime rules, and asks the submitter about anything odd. AWS, "
          "about $3 a month."),
 "og": ("Reads each timesheet on submission, compares it with the roster and the job log, "
        "applies your break and overtime rules, and asks the person who filled it in about "
        "anything that does not line up."),
 "abstract": ("The whole system on one page -- a reader, a comparer and an asker -- and the "
              "one decision that makes it work: check on Friday, not on the 28th."),
 "lede": ("Payroll week has a particular texture in a small business. Somebody prints the "
          "timesheets. Three are missing. Two have a Thursday with no hours on it. One says "
          "fourteen hours on a day the roster says was a half shift. Now it is the 28th, the "
          "people who could explain any of that have gone home, and payroll is Friday. The "
          "problem is not that the sheets are wrong. It is that nobody looked at them for "
          "three weeks. This post walks through a small system that looks at every sheet the "
          "minute it arrives."),
 "tags": ["timesheets", "payroll", "rostering", "overtime", "human in the loop", "serverless"],
 "takeaways": [
  "Sheets are checked on submission, not at payroll. The gap between error and question is minutes.",
  "Three sources to check against: the roster, the job log, and a rules tab you already keep.",
  "Every sheet ends in one of three states: clean, asked about, or waiting on a manager.",
  "The system never edits an hour. It asks the person, or it flags it for someone with authority.",
  "Designed on AWS for about $3 a month at typical small-business volume.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Timesheets", "sub": ["app, form, or photo"], "icon": "clock"},
      {"title": "Roster + jobs", "sub": ["who was on, what ran"], "icon": "calendar"},
      {"title": "Manager", "sub": ["sees only the odd ones"], "icon": "team"}],
    "inside": [
      {"title": "Reader", "sub": ["one row per day,", "whatever came in"], "icon": "ocr"},
      {"title": "Comparer", "sub": ["roster, jobs,", "break and OT rules"], "icon": "filter"},
      {"title": "Asker", "sub": ["one question to the", "person who knows"], "icon": "bell"}],
    "edges": [{"from": 0, "to": 0, "label": "sheets in"},
              {"from": 1, "to": 1, "label": "what was expected"},
              {"from": 2, "to": 2, "label": "only what needs authority", "up": True}],
    "note": "A clean sheet is never mentioned to anybody. That is most of them."}),
   "Three things outside the account, three pieces inside it. Sheets arrive however people "
   "already submit them, the roster and the job log say what was expected, and only what "
   "genuinely needs authority reaches a manager.",
   "System: timesheets in, roster and jobs as reference, three pieces inside AWS",
   "Three boxes across the top sit outside the AWS account. On the left, Timesheets: submitted "
   "through an app, a form, or as a photo of a paper sheet. In the middle, Roster and jobs: the "
   "records saying who was expected on which shift and what work was actually logged. On the "
   "right, Manager: the person who sees only the sheets that need authority. Each connects by "
   "an arrow to the AWS account container below. Sheets flow down into the account. The roster "
   "and job records feed in to say what was expected. The manager receives only what needs "
   "authority. Inside the AWS account are three components in a row. On the left, the Reader, "
   "which turns whatever arrived into one row per day. In the middle, the Comparer, which sets "
   "those rows against the roster and the job log and applies the break and overtime rules. On "
   "the right, the Asker, which sends one question to the person who filled the sheet in. "
   "Arrows flow left to right. A note at the bottom says a clean sheet is never mentioned to "
   "anybody, and that this is most of them."),
  ("h3", "What you set up once (the outside)"),
  ("ul", [
   "<strong>A way to submit.</strong> Whatever people already use. A web form for most, a "
   "photo of a paper sheet for the ones who will never use a form, and a spreadsheet upload "
   "for a supervisor who collects a crew's hours. All three are covered in Part 2, and all "
   "three become the same thing: one row per person per day.",
   "<strong>A roster.</strong> Who was expected, when, and where. Most small businesses have "
   "this somewhere &mdash; a shared calendar, a scheduling app, a whiteboard photographed on "
   "Monday. It does not need to be authoritative. It needs to be roughly right, because its "
   "only job is to notice that Thursday is blank on a sheet for somebody who was rostered on "
   "Thursday.",
   "<strong>A rules tab.</strong> One sheet holding the things a payroll clerk carries in "
   "their head: the unpaid break after six hours, the point where overtime starts, the maximum "
   "day nobody should be working past without a conversation, the rounding rule. Writing them "
   "down once is most of the value of this project, independent of any code.",
  ]),
  ("h3", "What runs on every sheet (the inside)"),
  ("ul", [
   "<strong>The reader.</strong> Turns whatever arrived into rows. A form is already rows. A "
   "spreadsheet is nearly rows. A photo of a paper sheet is the hard case, and it is the one "
   "place a model earns its keep: reading a handwritten grid into start times, finish times "
   "and a job reference, and marking anything it could not read confidently as unreadable "
   "rather than as a number.",
   "<strong>The comparer.</strong> Five checks against the three sources, all arithmetic. Does "
   "every rostered day have hours? Does every day with hours have a job, or a reason it does "
   "not? Do the breaks satisfy the rule? Is any day longer than the maximum? Does the week's "
   "total cross the overtime threshold, and if so has the sheet marked it as overtime?",
   "<strong>The asker.</strong> Turns a failed check into one message to the person who "
   "submitted it, with the day named and the discrepancy stated. Almost all of them are "
   "closable in one tap. The few that are not &mdash; an override, an unusual overtime week, a "
   "day past the maximum &mdash; go to a manager, because those need authority rather than "
   "memory.",
  ]),
  ("h2", "One sheet, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Submitted", "sub": ["Friday afternoon"], "icon": "clock"},
      {"title": "Read", "sub": ["one row per day"], "icon": "ocr"},
      {"title": "Compared", "sub": ["roster, jobs, rules"], "icon": "filter"},
      {"title": "Asked", "sub": ["if anything is odd"], "icon": "bell"},
      {"title": "Clean", "sub": ["ready for the 28th"], "icon": "check"}],
    "title": "ONE TIMESHEET, END TO END",
    "note": "The whole loop closes on Friday. Payroll week has nothing left to discover."}),
   "The same system as one line. The important property is not any single step; it is that all "
   "five happen on the day the sheet is submitted rather than three weeks later.",
   "One timesheet from submission to clean, in five stages",
   "A horizontal row of five boxes joined by arrows. Submitted: on Friday afternoon. Read: "
   "turned into one row per day. Compared: set against the roster, the job log and the rules. "
   "Asked: a question goes back if anything is odd. Clean: the sheet is ready for the 28th. A "
   "note says the whole loop closes on Friday and payroll week has nothing left to discover."),
  ("h2", "In plain words"),
  ("p", "Your site supervisor submits her week on Friday at four. The reader turns it into five "
        "rows. The comparer opens the roster: she was on Monday to Friday, and there are five "
        "rows, so nothing is missing. Four of the five days have a job reference that matches a "
        "job that ran that day. Tuesday says nine and a half hours with a thirty-minute break, "
        "and the rule says a break of thirty after six hours, so that is fine. The week totals "
        "44 hours against a 40-hour threshold, and the sheet has marked four hours as overtime. "
        "Everything lines up. The sheet is marked clean, and nobody hears anything."),
  ("p", "Her colleague submits at the same time with Thursday blank. The roster says he was on. "
        "Twenty seconds later he gets one message: \"Thursday 9th is blank and the roster had "
        "you on the Aldershot job &mdash; hours, or were you off?\" Two buttons: \"I worked, "
        "here are the hours\" and \"I was off\". He taps the first, types 7 to 3.30, and the "
        "sheet is clean before he has left the car park. On the 28th, payroll opens twenty-two "
        "sheets and every one of them is right, which is a completely different week from the "
        "one that starts with printing them out and finding three gaps."),
  ("callout", "Design rules that shaped every decision", [
   "Check on submission, never at payroll. The value is entirely in the gap between the error "
   "and the question, and that gap should be minutes.",
   "The system never edits an hour. It asks the person who wrote it, or it flags for someone "
   "with the authority to change it.",
   "Unreadable is a legitimate answer. A handwritten 7 that might be a 1 is marked unreadable "
   "and asked about; it is never resolved by guessing.",
   "The roster is a hint, not a law. People swap shifts. A mismatch is a question, not a "
   "correction.",
   "The rules live in a sheet. Changing the overtime threshold is an edit, not a deploy.",
   "A clean sheet generates no message to anybody, ever. Most sheets are clean.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Nearly every timesheet problem is a timing problem wearing a data costume. The "
        "information needed to fix a blank Thursday exists in one person's head on Friday and "
        "has largely evaporated by the 28th. A validator that runs at payroll time is therefore "
        "solving the problem at the worst possible moment: maximum cost to fix, minimum memory "
        "available, and a deadline."),
  ("p", "So the design puts almost nothing clever in the checks and everything into when they "
        "run. Five arithmetic comparisons against records you already keep, executed within a "
        "minute of submission, closing the loop with the one person who can answer. The result "
        "is not a smarter payroll process. It is a payroll process with nothing in it to "
        "discover."),
  ("p", "The next four posts walk through each piece: how a timesheet arrives, how it gets "
        "compared, how a question reaches the person who filled it in, and how a week gets "
        "closed. One diagram per post, a cost breakdown, and an engineering reference at the "
        "end."),
 ],
},
{
 "slug": "how-a-timesheet-arrives",
 "title": "How a timesheet arrives",
 "nav": "How it arrives",
 "read": 6, "words": 910,
 "desc": ("A web form, a spreadsheet upload and a photo of a paper sheet, and how all three "
          "become one row per person per day -- including what the reader refuses to guess."),
 "og": ("Three lanes into one row-per-day shape. The photo lane is the hard one, and the rule "
        "that makes it safe is that unreadable is an answer."),
 "abstract": ("Three lanes: a form, a spreadsheet upload, and a photo of a paper sheet. All "
              "become one row per person per day, and anything the reader cannot read "
              "confidently is marked unreadable rather than guessed."),
 "lede": ("There is always somebody who will not use the form. On a site crew it might be most "
          "of them. Any timesheet system that only accepts its own input format ends up with a "
          "supervisor transcribing paper into it on a Sunday, which is the original problem "
          "with an app bolted on. So this one takes a photo of a paper sheet as a first-class "
          "input, and this post is mostly about making that safe."),
 "tags": ["timesheets", "Amazon Textract", "OCR", "data intake", "idempotency", "serverless"],
 "takeaways": [
  "Three lanes: a web form, a spreadsheet upload, and a photo of a paper grid.",
  "All three produce the same thing: one row per person per day, with a source recorded.",
  "A digit the reader is not sure about is marked unreadable, never rounded to a guess.",
  "A supervisor's crew upload becomes many people's rows, each independently checkable.",
  "A resubmitted week replaces the previous draft rather than creating a second one.",
 ],
 "blocks": [
  ("h2", "Three lanes, one row shape"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Web form", "sub": ["one person, one week"], "icon": "form", "label": "rows"},
      {"title": "Crew spreadsheet", "sub": ["a supervisor's upload"], "icon": "chart",
       "label": "grid"},
      {"title": "Photo of paper", "sub": ["a handwritten sheet"], "icon": "image",
       "label": "image"}],
    "target": {"title": "One row per day", "sub": ["person, date, start,", "finish, break, job"],
               "icon": "database",
               "then": {"title": "Comparer", "sub": ["roster, jobs, rules"], "icon": "filter"}},
    "note": "The row shape is the contract. Nothing downstream knows which lane it came from."}),
   "Three ways to submit, one row shape. Everything after this point works on rows, which is "
   "why adding a fourth lane later costs nothing.",
   "Three timesheet lanes converging on one row-per-day shape",
   "Three boxes stacked on the left. Web form: one person submitting one week. Crew "
   "spreadsheet: a supervisor uploading a grid for several people. Photo of paper: a "
   "handwritten sheet photographed on a phone. Their arrows are labelled rows, grid and image, "
   "converging on One row per day on the right, holding person, date, start, finish, break and "
   "job. Below it, connected by a downward arrow, is the Comparer, which checks against the "
   "roster, the jobs and the rules. A note says the row shape is the contract and nothing "
   "downstream knows which lane a row came from."),
  ("h3", "The row"),
  ("pre", "person     sam@example.com      from the submitter, never inferred\n"
          "date       2026-07-09           the working day, not the submission day\n"
          "start      07:00                24-hour, local\n"
          "finish     15:30\n"
          "break_min  30\n"
          "job        J-4471               or null, with a reason\n"
          "source     form | sheet | photo\n"
          "confidence 1.0 | 0.0-1.0        below the floor means unreadable"),
  ("p", "The <code>confidence</code> field only ever moves off 1.0 in the photo lane, and it is "
        "the field that makes that lane safe. A form submission is what somebody typed; there "
        "is nothing to be unsure about. A photograph of a biro 7 that might be a 1 is exactly "
        "the situation where a system should say so."),
  ("h2", "The photo lane, in detail"),
  ("fig", ("chain", {
    "entry": {"title": "Photo uploaded", "sub": ["from a phone"], "icon": "image"},
    "steps": [
      {"title": "Store the original", "sub": ["S3, kept for the record"], "icon": "bucket"},
      {"title": "This week before?", "sub": ["person + week ending"], "icon": "branch",
       "side": {"title": "DynamoDB sheets", "sub": ["draft, replaceable"], "icon": "database"},
       "exit": {"title": "Replace the draft", "sub": ["not a second sheet"], "icon": "retry",
                "label": "resubmit"}},
      {"title": "Pull the grid", "sub": ["Textract tables"], "icon": "ocr"},
      {"title": "Read into rows", "sub": ["one Bedrock call"], "icon": "model",
       "side": {"title": "Roster for the week", "sub": ["names and dates"], "icon": "calendar"}},
      {"title": "Anything unreadable?", "icon": "branch",
       "exit": {"title": "Ask about that cell", "sub": ["show the crop"], "icon": "person",
                "label": "low confidence"}},
      {"title": "Hand to the comparer", "sub": ["rows, with sources"], "icon": "queue"}],
    "note": "The crop of the actual cell goes in the question. People recognise their own handwriting."}),
   "A photographed paper sheet, end to end. Textract finds the grid, the model reads it into "
   "rows grounded by the roster, and any cell it is unsure about becomes a question with the "
   "original crop attached.",
   "How a photographed paper timesheet becomes rows",
   "A vertical chain of six steps inside the AWS account, entered by a box labelled Photo "
   "uploaded from a phone. Step one stores the original in S3 for the record. Step two asks "
   "whether this person's week has been submitted before, checking a DynamoDB sheets table; a "
   "resubmission exits to Replace the draft rather than creating a second sheet. Step three "
   "pulls the grid using Amazon Textract table extraction. Step four reads the grid into rows "
   "with a single Bedrock call, grounded by the roster for that week so names and dates come "
   "from a list. Step five asks whether anything was unreadable, exiting to Ask about that "
   "cell, showing the crop of the original. Step six hands the rows to the comparer with their "
   "sources recorded. A note says the crop of the actual cell goes in the question because "
   "people recognise their own handwriting."),
  ("h3", "Why the roster grounds the read"),
  ("p", "A handwritten timesheet has names down one side and dates across the top, both in "
        "handwriting, both frequently abbreviated. \"S Patel\" and \"Sam P\" and \"SP\" are the "
        "same person; \"9/7\" is the ninth of July or the seventh of September depending on "
        "which side of the Atlantic wrote it. Asking a model to resolve those from the image "
        "alone is asking for a confident wrong answer."),
  ("p", "So the roster for that week goes in the prompt: these are the people, these are the "
        "dates. The model matches to a list rather than generating. A name it cannot match to "
        "somebody on the roster is not a new employee &mdash; it is an unreadable cell, and it "
        "goes back as a question with the crop attached."),
  ("h2", "The crew spreadsheet lane"),
  ("p", "A supervisor with a crew of eight is the case that breaks most timesheet apps, because "
        "the app models one person submitting for themselves. Here the upload simply produces "
        "eight people's rows at once, each of which is then an ordinary row with an ordinary "
        "provenance."),
  ("ul", [
   "<strong>Each person's rows are checked independently.</strong> A gap on one crew member's "
   "Wednesday is that person's question, not the supervisor's, and it goes to them.",
   "<strong>The supervisor gets a summary, not the questions.</strong> \"Uploaded 8 people, 39 "
   "rows, 2 questions sent.\" They do not become the routing layer for their own crew.",
   "<strong>A person who is not on the roster is flagged, not created.</strong> An unexpected "
   "name in a crew sheet is usually somebody covering, and it needs a manager rather than an "
   "automatic new record.",
   "<strong>The upload is replaceable.</strong> Reuploading a corrected sheet replaces the "
   "draft rows for that week, keyed on the supervisor and the week ending, rather than doubling "
   "everybody's hours.",
  ]),
  ("callout", "What the reader refuses to do", [
   "It does not round an unreadable digit to the nearest plausible one. Unreadable is an "
   "answer, and it produces a question with the crop attached.",
   "It does not infer a job reference from who the person is or what they usually do.",
   "It does not create a person. A name that is not on the roster is a flag for a manager.",
   "It does not carry hours forward from last week to fill a gap, even when last week is "
   "identical. That is the single most tempting and most dangerous shortcut available here.",
  ]),
  ("p", "Next: the five comparisons the rows are put through, and which of them can close a "
        "sheet on their own."),
 ],
},
{
 "slug": "how-a-timesheet-gets-compared",
 "title": "How a timesheet gets compared",
 "nav": "How it is compared",
 "read": 6, "words": 900,
 "desc": ("Five checks against the roster, the job log and your rules tab -- missing days, "
          "unmatched jobs, breaks, day length and the overtime threshold -- and which of them "
          "can close a sheet alone."),
 "og": ("Five arithmetic checks against records you already keep. Three can be closed by the "
        "person who submitted the sheet; two need a manager, and the split is deliberate."),
 "abstract": ("Five checks: missing days, unmatched jobs, break rules, day length and the "
              "overtime threshold. Three can be closed by the submitter; two need somebody "
              "with authority, and the split is the whole design."),
 "lede": ("None of these five checks is interesting on its own. Any of them could be done by a "
          "careful person with the roster open, and that is precisely the point &mdash; they "
          "are exactly the checks nobody does, on every sheet, every week, because doing them "
          "properly is twenty minutes of tedium per person. What matters is which of them the "
          "submitter can settle and which of them require somebody with authority."),
 "tags": ["timesheets", "overtime rules", "break rules", "payroll", "rostering", "serverless"],
 "takeaways": [
  "Five checks: missing day, unmatched job, break rule, day length, overtime threshold.",
  "Three are closable by the submitter. Two need a manager, because they cost money or carry risk.",
  "Every check reads a rule from the sheet, so changing a threshold is an edit, not a deploy.",
  "A day past the maximum is always a manager question, even when the person confirms it.",
  "The comparer never edits. Its entire output is a state and a list of questions.",
 ],
 "blocks": [
  ("h2", "The five checks"),
  ("fig", ("chain", {
    "entry": {"title": "Rows for a week", "sub": ["from Part 2"], "icon": "clock"},
    "steps": [
      {"title": "Every rostered day?", "sub": ["gaps against the roster"], "icon": "branch",
       "side": {"title": "Roster", "sub": ["who was on when"], "icon": "calendar"},
       "exit": {"title": "Ask the submitter", "sub": ["name the day"], "icon": "person",
                "label": "gap"}},
      {"title": "Job on every day?", "sub": ["or a stated reason"], "icon": "branch",
       "side": {"title": "Job log", "sub": ["what ran that day"], "icon": "log"},
       "exit": {"title": "Ask which job", "sub": ["short pick list"], "icon": "person",
                "label": "unmatched"}},
      {"title": "Breaks satisfied?", "sub": ["rule from the sheet"], "icon": "branch",
       "side": {"title": "Rules tab", "sub": ["breaks, OT, max day"], "icon": "doc"},
       "exit": {"title": "Ask about the break", "sub": ["one day at a time"], "icon": "person",
                "label": "short"}},
      {"title": "Day within the max?", "icon": "branch",
       "exit": {"title": "Manager decides", "sub": ["risk, not memory"], "icon": "team",
                "label": "over"}},
      {"title": "Overtime declared?", "sub": ["week total vs threshold"], "icon": "counter",
       "exit": {"title": "Manager approves", "sub": ["it costs money"], "icon": "money",
                "label": "undeclared"}},
      {"title": "Clean sheet", "sub": ["nobody is told"], "icon": "check"}],
    "note": "The first three go to the person. The last two go to somebody with authority."}),
   "The five checks in order, with the three that the submitter can close and the two that need "
   "authority. The split is not about difficulty; it is about who is allowed to decide.",
   "The five checks a week of timesheet rows passes through",
   "A vertical chain of six steps entered by a box labelled Rows for a week, from Part 2. Step "
   "one asks whether every rostered day has hours, comparing against the Roster; a gap exits to "
   "Ask the submitter, naming the day. Step two asks whether every day has a job or a stated "
   "reason, comparing against the Job log; an unmatched day exits to Ask which job with a short "
   "pick list. Step three asks whether the breaks satisfy the rule read from the Rules tab; a "
   "short break exits to Ask about the break, one day at a time. Step four asks whether each "
   "day is within the maximum length; a day over exits to Manager decides, because it is risk "
   "rather than memory. Step five asks whether overtime has been declared, comparing the week "
   "total against the threshold; undeclared overtime exits to Manager approves, because it "
   "costs money. Step six is Clean sheet, with nobody told. A note says the first three go to "
   "the person and the last two go to somebody with authority."),
  ("h3", "Missing days"),
  ("p", "The roster says who was expected. A rostered day with no row is the single most common "
        "finding and the single easiest to fix, provided you ask on Friday. It is also the "
        "check most likely to be wrong, because people swap shifts and the roster is often a "
        "week behind reality. So it is phrased as a question and never as a correction: "
        "\"Thursday is blank and the roster had you on &mdash; hours, or were you off?\""),
  ("h3", "Unmatched jobs"),
  ("p", "Every day with hours should point at something: a job, a site, a cost code, or an "
        "explicit reason like training or holiday. This is the check that pays for the system "
        "in businesses that bill time, because an unmatched day is an hour that was worked and "
        "will never be invoiced. The pick list comes from the jobs that actually ran that day, "
        "which is usually three or four options rather than a search."),
  ("h3", "Breaks, and why they are a rule and not a policy"),
  ("p", "The break rule is somewhere between a legal obligation and a house rule depending on "
        "where you are, and it changes. It lives in the sheet as two numbers &mdash; after how "
        "many hours, and how long &mdash; and the check is a subtraction. Getting it wrong is "
        "not a rounding error; in several jurisdictions it is a fine, which is why it is worth "
        "checking on every day of every sheet rather than on the ones somebody happens to look "
        "at."),
  ("h2", "The two that need authority"),
  ("p", "The split between what the submitter can close and what a manager must see is the most "
        "consequential decision in this design, and it is not about trust."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Missing day", "sub": ["submitter closes"], "icon": "person"},
      {"title": "Unmatched job", "sub": ["submitter closes"], "icon": "person"},
      {"title": "Short break", "sub": ["submitter closes"], "icon": "person"},
      {"title": "Long day", "sub": ["manager: risk"], "icon": "team"},
      {"title": "Overtime", "sub": ["manager: cost"], "icon": "money"}],
    "title": "WHO CLOSES WHAT, AND WHY",
    "note": "Three are memory questions. Two are decisions with consequences attached."}),
   "Which findings the submitter can settle and which need a manager. The first three are "
   "questions about what happened; the last two are decisions about risk and money.",
   "The five findings split by who is allowed to close them",
   "A horizontal row of five boxes. Missing day: the submitter closes it. Unmatched job: the "
   "submitter closes it. Short break: the submitter closes it. Long day: a manager, because it "
   "is a risk question. Overtime: a manager, because it costs money. A note says three are "
   "memory questions and two are decisions with consequences attached."),
  ("p", "A missing Thursday, an unmatched job and a short break are all questions about what "
        "happened. The person who was there knows, nobody else does, and their answer is the "
        "correct one. Routing those to a manager adds a day of delay and produces a worse "
        "answer, because the manager will just ask them."),
  ("p", "A fourteen-hour day and an undeclared overtime week are different in kind. The person "
        "confirming \"yes, I worked fourteen hours\" does not settle anything &mdash; it "
        "confirms the number and raises the actual question, which is whether that should have "
        "happened and who is paying for it. Those two carry a cost or a liability, so they need "
        "somebody who can accept one."),
  ("callout", "What the comparer never does", [
   "It never edits an hour. Its entire output is a sheet state and a list of questions.",
   "It never applies a rounding rule silently. If your rules tab rounds to the nearest quarter "
   "hour, the rounded and unrounded values are both stored and both visible.",
   "It never compares one person's week with another's. A long week is a fact about a week, "
   "not evidence about a person.",
   "It never treats a roster mismatch as an error. Shifts get swapped constantly and the "
   "roster is usually the thing that is out of date.",
  ]),
  ("p", "Next: what the question to the submitter looks like, and how a week gets closed."),
 ],
},
{
 "slug": "how-a-timesheet-question-gets-answered",
 "title": "How a timesheet question gets answered",
 "nav": "How it is answered",
 "read": 5, "words": 870,
 "desc": ("One message per sheet rather than one per finding, why it goes out on Friday "
          "afternoon, the one-tap answers, and what happens when a week is never answered."),
 "og": ("One message per sheet, not one per finding. Sent while the week is still fresh, "
        "answerable in a car park, and escalating on a schedule rather than expiring."),
 "abstract": ("One message per sheet rather than one per finding, sent while the week is still "
              "fresh. One-tap answers for the common cases, and an escalation ladder that "
              "carries a week forward rather than expiring it."),
 "lede": ("A validator that sends five separate emails about one week has not saved anybody "
          "anything; it has moved the tedium from a payroll clerk to twenty-two people. So the "
          "asker batches, waits a few minutes for a sheet to settle, and sends one message "
          "with every question about that week in it. This post is about the shape of that "
          "message and about what happens when it is ignored."),
 "tags": ["timesheets", "notifications", "Amazon SES", "escalation", "payroll", "serverless"],
 "takeaways": [
  "One message per sheet per week, never one per finding.",
  "Sent a few minutes after submission, so it lands while the person is still at work.",
  "Every finding has a one-tap answer, and the common answer is first.",
  "Answering a question re-runs the checks, so a fix can reveal the next thing cleanly.",
  "An unanswered week escalates to a manager and is carried forward, never silently dropped.",
 ],
 "blocks": [
  ("h2", "One message, all the questions"),
  ("fig", ("system", {
    "outside": [
      {"title": "Submitter", "sub": ["still at work, usually"], "icon": "person"},
      {"title": "Manager", "sub": ["cost and risk only"], "icon": "team"},
      {"title": "Payroll", "sub": ["reads the state, not the mail"], "icon": "report"}],
    "inside": [
      {"title": "Batcher", "sub": ["waits, then sends", "one message"], "icon": "queue"},
      {"title": "Question builder", "sub": ["one card per finding,", "common answer first"],
       "icon": "doc"},
      {"title": "Escalator", "sub": ["nudge, manager,", "carry forward"], "icon": "clock"}],
    "edges": [{"from": 0, "to": 0, "label": "one tap back", "up": True},
              {"from": 1, "to": 1, "label": "cost and risk", "up": True},
              {"from": 2, "to": 2, "label": "state per sheet", "up": True}],
    "note": "Payroll never reads an email. It reads whether every sheet is clean."}),
   "Who hears what. The submitter gets one batched message, the manager gets only the two "
   "findings that need authority, and payroll reads a state rather than a mailbox.",
   "How a timesheet question reaches the person who can answer it",
   "Three boxes across the top outside the AWS account. The Submitter, who is usually still at "
   "work. The Manager, who receives only the cost and risk findings. And Payroll, which reads "
   "the state of each sheet rather than any email. Inside the account, three components. The "
   "Batcher, which waits a few minutes for a sheet to settle and then sends one message. The "
   "Question builder, which makes one card per finding with the most likely answer first. And "
   "the Escalator, which nudges, brings in a manager and carries an unanswered week forward. "
   "Arrows show the submitter answering with one tap, the manager receiving cost and risk "
   "items, and payroll reading a per-sheet state. A note says payroll never reads an email; it "
   "reads whether every sheet is clean."),
  ("h3", "Why it waits"),
  ("p", "Somebody filling in a form will often submit, realise Wednesday is wrong, and resubmit "
        "ninety seconds later. Sending a question in between is how a system teaches people to "
        "ignore it. So the batcher holds a submitted sheet for a few minutes, and a "
        "resubmission inside that window replaces the draft and resets the timer. The message "
        "that eventually goes out is about the sheet as it finally stands."),
  ("h2", "What the message looks like"),
  ("callout", "One card per finding, and nothing else", [
   "<strong>Thursday 9 July is blank.</strong> The roster had you on the Aldershot job. "
   "&rarr; <em>I worked, here are the hours</em> &middot; <em>I was off</em>",
   "<strong>Tuesday has no job.</strong> Three jobs ran that day. "
   "&rarr; <em>J-4471</em> &middot; <em>J-4480</em> &middot; <em>J-4492</em> &middot; "
   "<em>Something else</em>",
   "<strong>Monday shows 9 hours with a 15-minute break.</strong> The rule is 30 after six. "
   "&rarr; <em>The break was 30</em> &middot; <em>It really was 15</em>",
   "<strong>Nothing else in the message.</strong> No sheet total, no policy text, no link to a "
   "portal, and no sentence beginning \"Please be advised\".",
  ]),
  ("p", "The order of the answers matters. \"I worked, here are the hours\" is first because it "
        "is right about eight times out of ten, and a person scanning on a phone taps the first "
        "plausible button. Putting \"I was off\" first would produce a measurable number of "
        "people accidentally giving away a day's pay, which is the kind of bug that does not "
        "show up in testing."),
  ("h3", "Answering re-runs the checks"),
  ("p", "Filling in Thursday can create a new finding &mdash; the week now crosses the overtime "
        "threshold, or Thursday itself has no job. So an answer does not close a finding; it "
        "updates the rows and re-runs the comparer. If new findings appear, they are batched "
        "and sent as a second message, which is the one case where somebody gets two messages "
        "about one week and it is unavoidable."),
  ("h2", "When a week is never answered"),
  ("fig", ("chain", {
    "steps": [
      {"title": "Asked, waiting", "sub": ["Friday afternoon"], "icon": "clock"},
      {"title": "Still open?", "sub": ["Monday morning"], "icon": "branch",
       "exit": {"title": "Nudge", "sub": ["same questions, shorter"], "icon": "bell",
                "label": "yes"}},
      {"title": "Still open?", "sub": ["Wednesday"], "icon": "branch",
       "side": {"title": "Their manager", "sub": ["from the roster"], "icon": "team"},
       "exit": {"title": "Manager is told", "sub": ["with the questions"], "icon": "email",
                "label": "yes"}},
      {"title": "Still open?", "sub": ["payroll cut-off"], "icon": "branch",
       "exit": {"title": "Pay what is known", "sub": ["carry the rest forward"], "icon": "money",
                "label": "yes"}},
      {"title": "Week closed", "sub": ["state and history kept"], "icon": "check"}],
    "note": "An unanswered day is never paid as zero. It is carried, and it stays visible."}),
   "The escalation ladder for an unanswered week. The important step is the last one: at "
   "payroll cut-off the known hours are paid and the open questions are carried, rather than "
   "the gaps being treated as zeros.",
   "What happens to a timesheet week nobody answers",
   "A vertical chain of five steps. First, Asked and waiting, from Friday afternoon. Second, on "
   "Monday morning, still open, exiting to a Nudge with the same questions written shorter. "
   "Third, on Wednesday, still open, which pulls the person's manager from the roster and exits "
   "to Manager is told, with the questions included. Fourth, at the payroll cut-off, still "
   "open, exiting to Pay what is known and carry the rest forward. Fifth, Week closed, with the "
   "state and history kept. A note says an unanswered day is never paid as zero; it is carried "
   "and stays visible."),
  ("p", "That last step is the one worth arguing about, and the argument is short. A blank "
        "Thursday at payroll cut-off has two possible meanings: the person did not work, or the "
        "person did not answer an email. Paying zero assumes the first. Carrying it assumes "
        "nothing, pays the twenty-eight hours that are not in dispute, and leaves a visible "
        "item that somebody will resolve in the first week of the next month &mdash; by which "
        "point the roster, the job log and a colleague's memory are all still available."),
  ("p", "Next: what a closed week actually produces, and the one report worth reading."),
 ],
},
{
 "slug": "how-a-payroll-week-gets-closed",
 "title": "How a payroll week gets closed",
 "nav": "How a week closes",
 "read": 5, "words": 850,
 "desc": ("What a clean sheet leaves behind, how the period export is built, why an override "
          "is recorded rather than applied, and the one report that says whether any of this "
          "is working."),
 "og": ("A closed week leaves an immutable record with the rules it was judged against, a "
        "regenerable export, and a five-number report that tells you whether the rules "
        "themselves need changing."),
 "abstract": ("What a closed week leaves behind: an immutable record carrying the rules it was "
              "judged against, a regenerable period export, overrides stored with a name on "
              "them, and a five-number report."),
 "lede": ("Everything so far has been about making a sheet correct before anybody needs it. "
          "This post is about what happens at the end &mdash; the record that gets written, "
          "the file payroll actually consumes, and the one report that tells you whether your "
          "rules are set anywhere near right."),
 "tags": ["timesheets", "payroll export", "audit trail", "DynamoDB", "reporting", "serverless"],
 "takeaways": [
  "The system decides what is correct. Payroll pays it. That boundary never moves.",
  "Every closed sheet stores the rules it was judged against, not just the outcome.",
  "An override is recorded with a name and a reason; the original number is never overwritten.",
  "The export is one file per period, regenerable, and byte-identical every time.",
  "If more than about one sheet in ten needs a question, the rules are wrong, not the people.",
 ],
 "blocks": [
  ("h2", "What a closed week holds"),
  ("table", ["Field", "Example", "Why it is there"], [
   ["<code>person</code>", "sam@example.com", "Who the week belongs to"],
   ["<code>week_ending</code>", "2026-07-12", "The period key, always a Sunday"],
   ["<code>hours</code>", "44.0", "Total, after any answered corrections"],
   ["<code>overtime</code>", "4.0", "Split out, because it is paid differently"],
   ["<code>rules</code>", "break 30/6h, OT>40, max 12h", "What it was judged against, stamped"],
   ["<code>findings</code>", "1 gap (answered), 1 OT (approved)", "What was asked and by whom"],
   ["<code>overrides</code>", "none", "Any manual change, with a name and a reason"],
   ["<code>closed_by</code>", "auto / manager@", "Who closed it"],
   ["<code>source</code>", "form / photo / sheet", "Which lane it came in through"],
   ["<code>state</code>", "clean / carried / exported", "Where it is in the period"],
  ]),
  ("p", "The <code>rules</code> field is the one that is easy to leave out and painful to add "
        "later. Overtime thresholds and break rules change, sometimes mid-period, sometimes "
        "retroactively. A sheet that stores only its outcome cannot tell you why a week in May "
        "was clean under one rule and would not be under today's. A sheet that stamps its rules "
        "can, and that is the difference between a record and a number."),
  ("h2", "Overrides"),
  ("p", "Sometimes a manager just needs to change a number: a day was logged against the wrong "
        "job and the person has left, a break was genuinely missed and is being paid, an "
        "agreement was reached that the system knows nothing about. Overrides exist, and they "
        "are additive rather than destructive."),
  ("ul", [
   "<strong>The original stays.</strong> An override writes a new value alongside the "
   "submitted one; it does not replace it. Both are exported, and the export column payroll "
   "reads is the effective value.",
   "<strong>A name and a reason are required.</strong> Not a dropdown of four reasons &mdash; "
   "a free-text line, because the useful reasons are always the ones nobody anticipated.",
   "<strong>An override is a finding.</strong> It appears in the month-end report, counted "
   "separately, because a rising override count is the clearest possible signal that a rule in "
   "the sheet no longer matches how the business actually runs.",
   "<strong>Nobody can override their own week.</strong> The one hard permission rule in the "
   "system, and the only reason it needs a notion of who a manager is at all.",
  ]),
  ("h2", "The export"),
  ("fig", ("chain", {
    "entry": {"title": "Period cut-off", "sub": ["a date, not a button"], "icon": "calendar"},
    "steps": [
      {"title": "Sheets in the period", "sub": ["by week ending"], "icon": "search",
       "side": {"title": "DynamoDB sheets", "sub": ["period index"], "icon": "database"}},
      {"title": "Any still open?", "icon": "branch",
       "exit": {"title": "Carry forward", "sub": ["known hours pay now"], "icon": "retry",
                "label": "open"}},
      {"title": "Apply overrides", "sub": ["effective value per row"], "icon": "filter"},
      {"title": "Write the file", "sub": ["one CSV, sorted"], "icon": "report"},
      {"title": "Mark exported", "sub": ["sheets become read-only"], "icon": "lock"}],
    "note": "Regenerating an export produces a byte-identical file. The period is a date, not a cursor."}),
   "How the period file is built. The period boundary is a date rather than \"everything since "
   "last time\", which is why running the export twice cannot produce two different files.",
   "How a payroll period export is built and frozen",
   "A vertical chain of five steps entered by a box labelled Period cut-off, which is a date "
   "rather than a button. Step one selects the sheets in the period by week ending, using a "
   "period index on the DynamoDB sheets table. Step two asks whether any are still open, "
   "exiting to Carry forward, where the known hours are paid now. Step three applies overrides "
   "to produce an effective value per row. Step four writes the file as one sorted CSV. Step "
   "five marks the sheets exported, making them read-only. A note says regenerating an export "
   "produces a byte-identical file because the period is a date and not a cursor."),
  ("h2", "The report that tells you if this is working"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Sheets", "sub": ["88 submitted"], "icon": "clock"},
      {"title": "Clean first time", "sub": ["79"], "icon": "check"},
      {"title": "Asked", "sub": ["9 sheets"], "icon": "bell"},
      {"title": "Needed a manager", "sub": ["3"], "icon": "team"},
      {"title": "Overrides", "sub": ["1"], "icon": "log"}],
    "title": "ONE PERIOD, IN FIVE NUMBERS",
    "note": "The third number is about your rules. The fifth is about whether they still fit."}),
   "A month in five numbers. Read the third and fifth together: a lot of questions means the "
   "rules are too tight, and a lot of overrides means they no longer describe the business.",
   "One payroll period summarised in five numbers",
   "A horizontal row of five boxes. Sheets: eighty-eight submitted. Clean first time: "
   "seventy-nine. Asked: nine sheets generated a question. Needed a manager: three. Overrides: "
   "one. A note says the third number is about your rules and the fifth is about whether they "
   "still fit."),
  ("p", "Nine questions out of eighty-eight sheets is a system doing its job. Thirty would mean "
        "a rule is wrong &mdash; most often a break rule that does not match how people "
        "actually take breaks, or an overtime threshold set at the contracted hours rather than "
        "the point where overtime is genuinely payable. The fix is an edit in the rules tab, "
        "and the next period will show it."),
  ("p", "A rising override count is the more interesting signal, because it means managers are "
        "routinely working around the rules rather than fixing them. One a month is normal. "
        "Eight a month means the rules tab describes a business that no longer exists, and "
        "somebody should spend twenty minutes on it."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="sheet",
 volumes=[(40, "40 sheets"), (200, "200 sheets"), (900, "900 sheets")],
 read_each=0.0041, msgs_each=1.4,
 extra=[("ocr", "Textract &mdash; photographed sheets only", "#8C4FFF", 0.0021, 0.0)],
 lede=("Nothing here is always-on, so the bill is almost entirely per-sheet. The one line "
       "worth watching is Textract, and it only bills on the photo lane &mdash; a business "
       "where everybody uses the form pays nothing for it at all. Here is where each cent "
       "goes."),
 takeaway_extra=("Textract only bills on photographed sheets. A team that uses the form pays "
                 "nothing for it."),
 risks=[
  "<strong>A retry loop on the read.</strong> A photo that Textract cannot parse makes the "
  "function throw, the retry throws, and the queue redelivers. Without a dead-letter queue "
  "that is one bad photo costing more than a hundred good sheets. A maximum receive count of "
  "three fixes it.",
  "<strong>Re-reading on every resubmission.</strong> If the draft-replacement logic re-runs "
  "Textract and the model on an unchanged image, a person correcting one cell four times pays "
  "for four full reads. Key the read cache on the image digest, not the sheet id.",
  "<strong>Log retention left at never.</strong> CloudWatch keeps log groups forever by "
  "default, and on a system this small the logs will eventually cost more than the compute. "
  "Thirty days is a one-line change.",
 ],
 per_unit_note=("The Textract line assumes roughly a third of sheets arrive as photographs, "
                "which is typical for a mixed office-and-site workforce and pessimistic for an "
                "office-only one. Businesses where everybody uses the form can delete that "
                "band entirely."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ts",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions "
       "and what each is allowed to touch, the two tables and their keys, and the specific "
       "model."),
 outside=[
  {"title": "Submission", "sub": ["form, upload, photo"], "icon": "form"},
  {"title": "Roster + jobs", "sub": ["Sheets API, read-only"], "icon": "calendar"},
  {"title": "SES outbound", "sub": ["questions, summaries"], "icon": "email"}],
 inside=[
  {"title": "S3 + SQS", "sub": ["originals,", "one sheet queue"], "icon": "bucket"},
  {"title": "Lambda x5", "sub": ["intake, read, compare,", "ask, close"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["sheets, findings"], "icon": "database"}],
 note="us-east-1. One account. Secrets Manager holds the Sheets credential and the signing key.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Submission, covering the web form, the "
  "spreadsheet upload and the photographed sheet. Roster and jobs, read through the Google "
  "Sheets API read-only. And SES outbound, carrying the questions and the summaries. Inside "
  "the account, three groups. S3 holding the original submissions and SQS carrying one sheet "
  "queue. Five Lambda functions named intake, read, compare, ask and close. And two DynamoDB "
  "tables named sheets and findings. A note gives the region as us-east-1, one account, with "
  "Secrets Manager holding the Sheets credential and the link-signing key."),
 functions=[
  ["<code>ts-intake</code>", "S3 ObjectCreated + Function URL",
   "Normalises all three lanes, replaces any draft for the week", "10s / 512&nbsp;MB"],
  ["<code>ts-read</code>", "SQS sheet queue",
   "Textract on photos, then one Bedrock call into rows", "60s / 1024&nbsp;MB"],
  ["<code>ts-compare</code>", "SQS read queue",
   "The five checks against roster, jobs and rules", "10s / 512&nbsp;MB"],
  ["<code>ts-ask</code>", "EventBridge + SQS",
   "Batches findings into one message; runs the escalation sweep", "15s / 512&nbsp;MB"],
  ["<code>ts-close</code>", "Function URL + EventBridge",
   "Handles signed answers; builds the period export", "30s / 1024&nbsp;MB"]],
 roles=[
  ["<code>ts-intake-role</code>", "<code>s3:GetObject</code>, <code>sqs:SendMessage</code>",
   "The submissions prefix; the sheet queue only"],
  ["<code>ts-read-role</code>",
   "<code>textract:AnalyzeDocument</code>, <code>bedrock:InvokeModel</code>",
   "The submissions prefix; one model arn"],
  ["<code>ts-compare-role</code>",
   "<code>dynamodb:PutItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Sheets and findings; the Sheets credential only"],
  ["<code>ts-ask-role</code>", "<code>ses:SendEmail</code>, <code>dynamodb:Query</code>",
   "One verified identity; the findings status index"],
  ["<code>ts-close-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>s3:PutObject</code>",
   "Sheets and findings; the exports prefix"]],
 tables=[
  ("Table: sheets",
   "PK   person            S   sam@example.com\n"
   "SK   week_ending       S   2026-07-12\n"
   "     state             S   draft | asked | clean | carried | exported\n"
   "     source            S   form | sheet | photo\n"
   "     image_digest      S   sha256 of the original, for the read cache\n"
   "     rows              L   [{date, start, finish, break_min, job, confidence}]\n"
   "     hours             N   44.0\n"
   "     overtime          N   4.0\n"
   "     rules             S   break 30/6h, OT>40, max 12h\n"
   "     overrides         L   [{field, from, to, by, reason, at}]\n"
   "     ttl               N   epoch, +7 years\n\n"
   "GSI  period-index        PK week_ending, SK state   -- the export sweep"),
  ("Table: findings",
   "PK   sheet_key         S   person|week_ending\n"
   "SK   finding_id        S   gap#2026-07-09\n"
   "     kind              S   gap | job | break | long_day | overtime\n"
   "     owner             S   submitter | manager\n"
   "     detail            S   Thursday 9 July is blank; roster had Aldershot\n"
   "     state             S   open | answered | overridden\n"
   "     answered_by       S   sam@example.com\n"
   "     answered_at       S   2026-07-10T16:04:11Z\n\n"
   "GSI  open-index          PK state, SK created_at    -- the escalation sweep")],
 inbound=[
  "The <strong>web form</strong> is static files in S3 behind CloudFront with an origin access "
  "control. There is no login: the link carries a signed staff token minted when somebody is "
  "added to the roster.",
  "<strong>Photo uploads</strong> go straight to S3 with a presigned PUT, so a phone on a "
  "site connection is not holding a Lambda open while it uploads.",
  "<strong>Answer links</strong> are signed, scoped to one finding, single-use by conditional "
  "write, and expire after fourteen days.",
  "<strong>Function URLs</strong> are public by default. Both <code>ts-intake</code> and "
  "<code>ts-close</code> verify an HMAC on the first line of the handler."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock. "
  "The task is turning a Textract table into rows, which is extraction.",
  "<strong>Called once</strong> per photographed sheet, keyed on the image digest, so "
  "correcting one cell and resubmitting the same image does not pay again.",
  "<strong>Not called at all</strong> for the form and spreadsheet lanes. Those are already "
  "rows and a model would only add a way to be wrong.",
  "<strong>Output is a JSON schema</strong> with a row array and a per-cell confidence. A "
  "confidence below the floor becomes an unreadable-cell question with the crop attached.",
  "<strong>Grounded</strong> with the roster names and the dates in that week, so people and "
  "days are matched against a list rather than generated."],
 gotchas=[
  "Textract's table extraction is much better on a flat, well-lit sheet than on a photo taken "
  "at an angle in a van. A one-line hint in the form about laying the sheet flat is worth more "
  "than any prompt engineering.",
  "Key the read cache on the image digest and not the sheet id, or every resubmission pays for "
  "a full re-read.",
  "Week ending must be a fixed day of the week, chosen once. Mixing Sunday and Saturday week "
  "endings across a workforce makes the period index useless.",
  "Nobody can override their own week. It is the only permission rule here, and it is the "
  "reason the system needs to know who reports to whom at all.",
  "Stamp the rules on the sheet at close. A threshold change in the rules tab will otherwise "
  "silently restate every past period."],
))
