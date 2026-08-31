"""Day 84 -- 2026-07-17 -- Budget variance reporter."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "budget-variance-reporter"
NAME = "Budget variance reporter"

SPEC = {
 "slug": SLUG, "date": "2026-07-17", "name": NAME,
 "tagline": ("Each month, the three or four budget lines that actually moved get explained "
             "from the transactions behind them -- so the review is a decision rather than a "
             "hunt through a spreadsheet."),
 "lede": ("A small system that compares actuals against budget each month, works out which "
          "variances are real rather than timing, pulls the transactions behind each one, and "
          "produces a short report naming the three or four that matter. It never adjusts a "
          "budget and never explains a number away. Seven posts on the same system -- one "
          "diagram at a time -- with a cost breakdown and an engineering reference at the end."),
 "keywords": ["budget variance", "management accounts", "financial reporting", "cost control",
              "human in the loop", "serverless"],
 "icons": ["chart", "search", "report"],
 "faq": [
  ("What is a budget variance reporter?",
   "A small serverless system that compares each month's actuals against budget, separates "
   "real variances from timing differences, pulls the transactions behind the ones that "
   "matter, and produces a short report. It reports; it never adjusts a budget or "
   "reclassifies a transaction."),
  ("Why not just read the management accounts?",
   "Because a management accounts pack is forty lines and most of them are noise. The work is "
   "not producing the numbers -- your accounting software already does that -- it is working "
   "out which three or four of the forty deserve a conversation, and why."),
  ("What is a timing difference?",
   "A variance caused by when something was posted rather than by anything real: an invoice "
   "that arrived a week late, a quarterly payment landing in a different month than budgeted, "
   "an accrual reversing. They look identical to real overspend in a single month and resolve "
   "themselves over two or three."),
  ("Does it need our accounting system's API?",
   "It needs a nominal transaction export per period, which every accounting package can "
   "produce on a schedule. An API is nicer; a scheduled CSV works."),
  ("What does it cost to run?",
   "A couple of dollars a month. It runs once a period over a few thousand rows. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "budget-variance-reporter-on-aws",
 "title": "A budget variance reporter on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 910,
 "desc": ("Compares actuals against budget, separates real variance from timing, and reports "
          "the three or four lines that matter with the transactions behind them. AWS, about "
          "$2 a month."),
 "og": ("Forty budget lines, three that matter. The work is not producing the numbers -- it is "
        "separating real variance from timing and pulling the transactions behind what is left."),
 "abstract": ("The whole system on one page -- a comparer, a timing filter and a reporter -- "
              "plus the observation that makes it useful: most variance is timing, and timing "
              "resolves itself."),
 "lede": ("Every business that budgets produces a monthly pack showing budget, actual and "
          "variance across forty-odd lines, and every business that produces one knows the "
          "same thing: almost nobody reads it properly. Not because it is uninteresting, but "
          "because forty numbers with no indication of which three matter is not information, "
          "it is a search task. This post walks through a small system that does the searching."),
 "tags": ["budget variance", "management accounts", "financial reporting", "cost control",
          "human in the loop", "serverless"],
 "takeaways": [
  "One input: a nominal transaction export per period.",
  "Most variance is timing. Separating it out is the single highest-value step.",
  "Only three or four lines are reported, with the transactions behind each one.",
  "It never adjusts a budget, reclassifies a transaction or explains a number away.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Actuals", "sub": ["nominal export, monthly"], "icon": "money"},
      {"title": "Budget", "sub": ["a sheet, by line and month"], "icon": "chart"},
      {"title": "Whoever reviews", "sub": ["three or four lines"], "icon": "person"}],
    "inside": [
      {"title": "Comparer", "sub": ["line by line,", "month and year to date"], "icon": "counter"},
      {"title": "Timing filter", "sub": ["is it real, or", "just when it landed"], "icon": "filter"},
      {"title": "Reporter", "sub": ["the few that matter,", "with the transactions"],
       "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "transactions"},
              {"from": 1, "to": 1, "label": "what was expected"},
              {"from": 2, "to": 2, "label": "a short report", "up": True}],
    "note": "The middle box is the whole value. Everything else is subtraction."}),
   "Two inputs, three pieces. The comparer is arithmetic anyone could do; the timing filter is "
   "the part that turns forty variances into three worth discussing.",
   "System: actuals and budget in, a short variance report out",
   "Three boxes across the top sit outside the AWS account. On the left, Actuals: the nominal "
   "transaction export produced monthly. In the middle, Budget: a sheet holding the budget by "
   "line and by month. On the right, Whoever reviews: the person who receives three or four "
   "lines rather than forty. Each connects by an arrow to the AWS account container below. "
   "Transactions flow down into the account. The budget feeds in as what was expected. A short "
   "report goes back out. Inside the AWS account are three components in a row. On the left, "
   "the Comparer, which works line by line for the month and year to date. In the middle, the "
   "Timing filter, which asks whether a variance is real or just a matter of when something "
   "landed. On the right, the Reporter, which surfaces the few that matter with the "
   "transactions behind them. A note at the bottom says the middle box is the whole value and "
   "everything else is subtraction."),
  ("h3", "What you set up once (the outside)"),
  ("ul", [
   "<strong>An actuals export.</strong> A nominal transaction listing per period from whatever "
   "you use &mdash; account code, date, amount, description, source document. Every accounting "
   "package can produce this on a schedule, and the transaction level matters: a trial balance "
   "alone gives you the variance but not the reason.",
   "<strong>A budget sheet.</strong> One row per account code, one column per month. Most small "
   "businesses budget annually and divide by twelve, which is exactly the practice that "
   "generates most of the false variances this system exists to filter. Part 3 is about doing "
   "better than that cheaply.",
   "<strong>Two thresholds.</strong> The percentage and the absolute amount a variance has to "
   "clear before it is worth reporting. Both are needed: a forty per cent overspend on a "
   "sixty-pound line is noise, and a three per cent overspend on a payroll line is not.",
  ]),
  ("h3", "What runs each period (the inside)"),
  ("ul", [
   "<strong>The comparer.</strong> Budget minus actual, per line, for the month and for the "
   "year to date. Both matter and they frequently disagree: a line can be twenty per cent over "
   "for the month and on budget for the year, which is a timing story, and the reverse, which "
   "is a trend nobody has noticed.",
   "<strong>The timing filter.</strong> Asks whether each variance is explained by when things "
   "landed rather than by what happened. Four tests, covered in Part 4, and between them they "
   "usually remove two thirds of the lines that clear the thresholds.",
   "<strong>The reporter.</strong> Takes what survives, pulls the transactions that make up "
   "each variance, and writes a short report. The transactions are the point: \"repairs over by "
   "£2,400\" is a question, and \"repairs over by £2,400, of which £2,150 is one invoice for "
   "the compressor\" is an answer.",
  ]),
  ("h2", "One period, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Exported", "sub": ["nominal transactions"], "icon": "money"},
      {"title": "Compared", "sub": ["40 lines, 11 over"], "icon": "counter"},
      {"title": "Filtered", "sub": ["7 are timing"], "icon": "filter"},
      {"title": "Explained", "sub": ["transactions pulled"], "icon": "search"},
      {"title": "Reported", "sub": ["4 lines, one page"], "icon": "report"}],
    "title": "ONE PERIOD, END TO END",
    "note": "Forty lines in, four out. The third stage is where most of them go."}),
   "The same system as one line. The interesting number is the drop from eleven to four, which "
   "is entirely the timing filter's work.",
   "One reporting period from export to report, in five stages",
   "A horizontal row of five boxes joined by arrows. Exported: the nominal transactions arrive. "
   "Compared: forty lines, of which eleven are over threshold. Filtered: seven of those are "
   "timing differences. Explained: the transactions behind the rest are pulled. Reported: four "
   "lines on one page. A note says forty lines in, four out, and the third stage is where most "
   "of them go."),
  ("h2", "In plain words"),
  ("p", "July closes. The export lands on the 4th. Forty account lines, of which eleven are "
        "outside the thresholds. The timing filter looks at each: insurance is over by the full "
        "annual premium because it was budgeted in August and paid in July &mdash; timing. "
        "Subcontractors is under by nine thousand because two invoices have not arrived yet, "
        "which the filter knows because the same two suppliers invoice every month and did not "
        "this month &mdash; timing. Seven of the eleven go the same way."),
  ("p", "Four survive. Repairs is over by £2,400, and the transactions show £2,150 of that is "
        "one compressor invoice. Fuel is over by eleven per cent for the third consecutive "
        "month, which is the only line in the report with no single transaction behind it and "
        "is therefore the interesting one. Two others are similar. The report is one page, "
        "arrives on the 5th, and gets read &mdash; because four lines with reasons attached is "
        "a conversation and forty lines with variances is a spreadsheet."),
  ("callout", "Design rules that shaped every decision", [
   "Report few things. A report with forty lines on it is a spreadsheet, and spreadsheets do "
   "not get read.",
   "Separate timing from real. Most variance is timing, and reporting it trains people to "
   "ignore the report.",
   "Always attach the transactions. A variance without its transactions is a question; with "
   "them it is usually an answer.",
   "Month and year to date, always both. They disagree constantly and the disagreement is the "
   "signal.",
   "It never changes a number. No reclassification, no accrual, no budget adjustment. Those are "
   "an accountant's decisions.",
   "A line with no single transaction behind it is more interesting than one with a big invoice "
   "in it, and the report should say so.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The management accounts problem is not a data problem. The numbers are correct, "
        "produced on time, and complete. The problem is that a forty-line variance table has no "
        "priority in it, and constructing that priority takes an hour of somebody's judgement "
        "every month &mdash; which means it happens for three months after somebody insists on "
        "it and then stops."),
  ("p", "So the design spends nothing on presentation and everything on selection. It knows "
        "which of the forty lines are worth a sentence, it knows why, and it can show the "
        "transactions. That is the hour, done in four seconds, on the fifth of every month, "
        "forever."),
  ("p", "The next four posts walk through each piece: how the period data arrives, how the "
        "budget gets shaped, how timing gets filtered out, and what the report says. One "
        "diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-the-period-data-arrives",
 "title": "How the period data arrives",
 "nav": "How data arrives",
 "read": 5, "words": 800,
 "desc": ("A nominal transaction export rather than a trial balance, why the transaction level "
          "is non-negotiable, and how a restated period is absorbed without corrupting "
          "history."),
 "og": ("A trial balance gives you the variance and not the reason. The transaction level is "
        "what makes a variance explainable, and restatements have to be a fact of life."),
 "abstract": ("Why the transaction level is non-negotiable, what a period export has to "
              "contain, and how a restated period is absorbed without corrupting the history "
              "you already reported."),
 "lede": ("This system will only ever be as good as what it is fed, and there is one input "
          "decision that determines whether it is useful or merely arithmetic: whether you give "
          "it a trial balance or the transactions behind it."),
 "tags": ["budget variance", "management accounts", "data import", "accounting", "idempotency",
          "serverless"],
 "takeaways": [
  "A trial balance gives you the variance; only transactions give you the reason.",
  "The minimum row is code, date, amount, description and source document.",
  "Periods get restated after they close, and the system has to absorb that.",
  "A restated period is re-imported whole, never patched, and the report is regenerable.",
  "The import is idempotent, so a re-sent export changes nothing.",
 ],
 "blocks": [
  ("h2", "Transactions, not balances"),
  ("p", "A trial balance tells you repairs was £2,400 over budget. The transactions tell you "
        "£2,150 of that was one compressor. Those two facts lead to entirely different "
        "conversations, and only the second one is worth having."),
  ("pre", "code         6210            the nominal account\n"
          "date         2026-07-11      the posting date\n"
          "amount       2150.00         signed\n"
          "description  Compressor repair -- unit 2\n"
          "source       PINV-4471       the purchase invoice reference\n"
          "supplier     Ashford Plant   where available\n"
          "period       2026-07         which period it was posted into"),
  ("p", "The <code>period</code> field being separate from the <code>date</code> is not "
        "pedantry. A transaction dated 28 June and posted into July is exactly the kind of thing "
        "that produces a false variance in both months, and having both fields is what lets the "
        "timing filter recognise it."),
  ("h2", "The import"),
  ("fig", ("chain", {
    "entry": {"title": "Export lands", "sub": ["scheduled CSV or API"], "icon": "money"},
    "steps": [
      {"title": "Store the file", "sub": ["S3, as received"], "icon": "bucket"},
      {"title": "Which period?", "sub": ["from the file, not the date"], "icon": "branch",
       "exit": {"title": "Ask", "sub": ["never assume a period"], "icon": "person",
                "label": "unclear"}},
      {"title": "Seen this period?", "sub": ["already imported"], "icon": "branch",
       "side": {"title": "DynamoDB periods", "sub": ["import history"], "icon": "database"},
       "exit": {"title": "Restatement", "sub": ["replace whole, keep both"], "icon": "retry",
                "label": "yes"}},
      {"title": "Load the transactions", "sub": ["one row each"], "icon": "log"},
      {"title": "Ready to compare", "sub": ["a complete period"], "icon": "check"}],
    "note": "A period is replaced whole or not at all. Patching an import is how ledgers drift."}),
   "How a period export is imported. The restatement path is the one that matters: periods get "
   "reopened and re-closed routinely, and a system that cannot absorb that will be wrong within "
   "two months.",
   "How a nominal transaction export is imported",
   "A vertical chain of five steps entered by a box labelled Export lands, as a scheduled CSV "
   "or through an API. Step one stores the file in S3 exactly as received. Step two asks which "
   "period it covers, taken from the file rather than inferred from dates; if unclear it exits "
   "to Ask, because a period is never assumed. Step three asks whether this period has already "
   "been imported, checking a DynamoDB periods table; if so it exits to Restatement, which "
   "replaces the period whole while keeping both versions. Step four loads the transactions, "
   "one row each. Step five is Ready to compare, a complete period. A note says a period is "
   "replaced whole or not at all, because patching an import is how ledgers drift."),
  ("h3", "Restatements"),
  ("p", "Periods are reopened. An accrual is corrected, a misposting is fixed, a late invoice "
        "is dated back. In a small business this happens to roughly one period in three, and it "
        "usually happens after a report has already gone out."),
  ("p", "So a re-import of a period already imported is a restatement, not an error. The whole "
        "period is replaced &mdash; every transaction, not a diff &mdash; and both versions are "
        "kept. The report for that period is regenerated, and it says at the top that it is a "
        "restatement with the date of the original. That last sentence is what stops two "
        "different versions of July circulating with no way to tell them apart."),
  ("h3", "Why replace whole"),
  ("p", "Patching an import &mdash; applying only the rows that changed &mdash; requires "
        "knowing which rows changed, and accounting exports rarely carry stable row "
        "identifiers. Two imports of the same period with a corrected misposting will differ in "
        "ways that are hard to diff correctly, and a wrong diff produces a ledger that is subtly "
        "wrong in a way nobody will find. Replacing whole is boring, obviously correct, and "
        "costs nothing at these volumes."),
  ("h2", "Idempotency"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Same file twice", "sub": ["identical digest"], "icon": "retry"},
      {"title": "Nothing happens", "sub": ["no re-import"], "icon": "check"},
      {"title": "Changed file", "sub": ["different digest"], "icon": "search"},
      {"title": "Restatement", "sub": ["replace, keep both"], "icon": "log"},
      {"title": "Report regenerated", "sub": ["and labelled as such"], "icon": "report"}],
    "title": "RE-SENDING AN EXPORT",
    "note": "The digest decides. An identical file is not a restatement; it is a duplicate."}),
   "What happens when an export is sent twice. The file digest separates a harmless duplicate "
   "from a genuine restatement, and only the second one regenerates anything.",
   "How a re-sent period export is handled",
   "A horizontal row of five boxes. Same file twice: the digest is identical. Nothing happens: "
   "there is no re-import. Changed file: a different digest. Restatement: the period is replaced "
   "and both versions are kept. Report regenerated: and labelled as a restatement. A note says "
   "the digest decides, and an identical file is a duplicate rather than a restatement."),
  ("p", "Next: how a budget gets shaped so that it does not manufacture variances all by "
        "itself."),
 ],
},
{
 "slug": "how-the-budget-gets-shaped",
 "title": "How the budget gets shaped",
 "nav": "How it is shaped",
 "read": 5, "words": 810,
 "desc": ("Why dividing an annual budget by twelve manufactures variances, three cheap ways to "
          "shape a line, and the lines where flat really is right."),
 "og": ("An annual budget divided by twelve manufactures a variance every month for anything "
        "seasonal or annually billed. Three cheap ways to shape a line properly."),
 "abstract": ("Why dividing an annual budget by twelve manufactures variances, three cheap ways "
              "to shape a line so it does not, and the lines where flat genuinely is right."),
 "lede": ("Most of the false variances in a monthly pack are not caused by the business. They "
          "are caused by the budget, specifically by the near-universal practice of taking an "
          "annual number and dividing it by twelve. This post is about fixing that without "
          "turning budgeting into a project."),
 "tags": ["budget variance", "budgeting", "seasonality", "management accounts", "reporting",
          "serverless"],
 "takeaways": [
  "A flat twelfth is right for very few lines and wrong for most of the interesting ones.",
  "Three shapes cover almost everything: flat, seasonal, and calendar-fixed.",
  "Last year's actuals are the cheapest seasonal shape available and are usually good enough.",
  "A calendar-fixed line -- insurance, an annual licence -- goes in the month it is due.",
  "Reshaping a budget is not rebudgeting: the annual total never changes.",
 ],
 "blocks": [
  ("h2", "Why a flat twelfth manufactures variances"),
  ("p", "Take an insurance line budgeted at twelve thousand a year, paid annually in August. A "
        "flat twelfth budgets a thousand a month. Eleven months of the year that line is a "
        "thousand under budget, and in August it is eleven thousand over. Twelve false "
        "variances from a line that was budgeted correctly and paid exactly as expected."),
  ("p", "Now do that for the annual licence, the quarterly rates, the seasonal energy bill, the "
        "summer wage costs at a seaside business and the January quiet month, and a substantial "
        "fraction of your monthly variance table is describing the shape of your budget rather "
        "than anything about your business."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Flat", "sub": ["rent, subscriptions"], "icon": "counter"},
      {"title": "Seasonal", "sub": ["last year's shape"], "icon": "chart"},
      {"title": "Calendar-fixed", "sub": ["due in one month"], "icon": "calendar"},
      {"title": "Volume-linked", "sub": ["moves with a driver"], "icon": "search"},
      {"title": "Annual total", "sub": ["unchanged by all of this"], "icon": "check"}],
    "title": "FOUR SHAPES, ONE UNCHANGED TOTAL",
    "note": "Reshaping is not rebudgeting. The year's number is the same either way."}),
   "The four budget shapes and the thing they have in common: none of them changes the annual "
   "figure, which is what makes reshaping an easy conversation to have.",
   "Four ways to shape a budget line across a year",
   "A horizontal row of five boxes. Flat: right for rent and subscriptions. Seasonal: taking "
   "last year's shape. Calendar-fixed: the whole amount falls in the month it is due. "
   "Volume-linked: the line moves with a business driver. Annual total: unchanged by any of "
   "this. A note says reshaping is not rebudgeting, because the year's number is the same "
   "either way."),
  ("h3", "Flat, and where it is genuinely right"),
  ("p", "Rent, monthly subscriptions, a salaried payroll with no seasonal element, a fixed "
        "service contract. These are genuinely equal every month and a twelfth is correct. It is "
        "worth marking them explicitly as flat rather than leaving them as the default, because "
        "a line that is flat by decision behaves differently in the timing filter from one that "
        "is flat because nobody thought about it."),
  ("h3", "Seasonal, from last year"),
  ("p", "The cheapest useful seasonal shape is last year's actuals for the same line, expressed "
        "as twelve percentages summing to one hundred, applied to this year's annual budget. It "
        "requires no judgement, no forecasting and no meeting. It is wrong in the specific "
        "months where last year was unusual, and it is dramatically better than a twelfth for "
        "anything with a season in it."),
  ("p", "The system can propose these automatically from the prior year's imported data, which "
        "turns budget shaping from a task into a review: here are twelve lines whose shape "
        "differs materially from flat, here is last year's shape, accept or edit."),
  ("h3", "Calendar-fixed"),
  ("p", "Insurance in August, the annual licence in March, rates in four instalments. The whole "
        "amount goes in the month it is due. This is the single highest-value change to make and "
        "it takes about ten minutes for a typical small business, because there are usually only "
        "five or six such lines and everybody knows which they are."),
  ("h2", "Volume-linked lines"),
  ("p", "The fourth shape is different in kind and worth the extra effort on two or three lines "
        "only. A line like packaging or card fees does not have a monthly shape; it has a "
        "relationship to a driver, usually sales or units. Budgeting it as a rate rather than an "
        "amount means the variance answers a better question."),
  ("fig", ("chain", {
    "entry": {"title": "A volume-linked line", "sub": ["card fees"], "icon": "money"},
    "steps": [
      {"title": "Budget as a rate", "sub": ["1.4% of card sales"], "icon": "counter",
       "side": {"title": "Budget sheet", "sub": ["rate, not amount"], "icon": "chart"}},
      {"title": "Read the driver", "sub": ["actual card sales"], "icon": "search",
       "side": {"title": "The same export", "sub": ["a revenue code"], "icon": "log"}},
      {"title": "Expected = rate x driver", "sub": ["computed monthly"], "icon": "filter"},
      {"title": "Variance is the rate", "sub": ["not the volume"], "icon": "check"}],
    "note": "Now 'fees over budget' means the rate moved, not that you sold more."}),
   "How a volume-linked line is budgeted. The result is a variance that means something "
   "specific: the rate changed, rather than the business was busier than expected.",
   "How a volume-linked budget line is computed and compared",
   "A vertical chain of four steps entered by a box labelled A volume-linked line, using card "
   "fees as the example. Step one budgets it as a rate, one point four per cent of card sales, "
   "read from the budget sheet as a rate rather than an amount. Step two reads the driver, which "
   "is actual card sales taken from a revenue code in the same export. Step three computes the "
   "expected figure as rate times driver, monthly. Step four notes that the variance is now "
   "about the rate rather than the volume. A note says fees over budget now means the rate "
   "moved rather than that you sold more."),
  ("p", "Two or three lines treated this way is worth it; twenty is a modelling exercise that "
        "will not be maintained. The candidates are the ones where somebody has said \"well, of "
        "course it is over, we were busier\" more than once."),
  ("callout", "What reshaping is not", [
   "It is not rebudgeting. The annual total for every line is unchanged, which is why this does "
   "not need a board conversation.",
   "It is not forecasting. Reshaping distributes a number you already agreed; forecasting "
   "changes it.",
   "It is not a one-off. Calendar-fixed dates move, seasons shift, and a fifteen-minute review "
   "at the start of each year keeps it honest.",
   "It is not the system's decision. The shapes are proposed and a person accepts them, because "
   "a budget shape is a statement about the business.",
  ]),
  ("p", "Next: the timing filter, which is where most of the remaining variance goes."),
 ],
},
{
 "slug": "how-timing-gets-filtered-out",
 "title": "How timing gets filtered out",
 "nav": "How timing is filtered",
 "read": 6, "words": 860,
 "desc": ("Four tests that separate a real variance from a difference in when something landed "
          "-- and why a filtered variance is shown as filtered rather than hidden."),
 "og": ("Four tests separate real variance from timing: the missing regular, the early arrival, "
        "the year-to-date check and the reversal. Between them they remove two thirds of the "
        "lines."),
 "abstract": ("Four tests that separate a real variance from a difference in when something "
              "landed, and why a filtered variance is shown as filtered rather than hidden "
              "altogether."),
 "lede": ("This is the part that makes the report short enough to read. Without it, a variance "
          "report is a list of lines that are over or under, most of which will be fine next "
          "month, and a reader who learns that within two months stops reading."),
 "tags": ["budget variance", "timing differences", "management accounts", "accruals",
          "reporting", "serverless"],
 "takeaways": [
  "Four tests: the missing regular, the early arrival, the year-to-date check, and the reversal.",
  "Between them they typically remove two thirds of the lines that clear the thresholds.",
  "A filtered variance is listed as filtered, in one line, never silently dropped.",
  "The year-to-date test is the strongest and the simplest: is the year still on budget?",
  "A variance filtered three months running is promoted, because a consistent filter is a finding.",
 ],
 "blocks": [
  ("h2", "The four tests"),
  ("fig", ("chain", {
    "entry": {"title": "A variance over threshold", "sub": ["month, one line"], "icon": "counter"},
    "steps": [
      {"title": "A regular is missing?", "sub": ["bills monthly,", "not this month"],
       "icon": "branch",
       "side": {"title": "Transaction history", "sub": ["last 12 periods"], "icon": "log"},
       "exit": {"title": "Timing", "sub": ["invoice not in yet"], "icon": "clock",
                "label": "yes"}},
      {"title": "Something arrived early?", "sub": ["budgeted for later"], "icon": "branch",
       "side": {"title": "Budget shape", "sub": ["calendar-fixed lines"], "icon": "calendar"},
       "exit": {"title": "Timing", "sub": ["next month will be under"], "icon": "clock",
                "label": "yes"}},
      {"title": "Year to date on budget?", "sub": ["within threshold"], "icon": "branch",
       "exit": {"title": "Timing", "sub": ["the year is fine"], "icon": "clock", "label": "yes"}},
      {"title": "A reversal?", "sub": ["accrual, credit note"], "icon": "branch",
       "exit": {"title": "Timing", "sub": ["a correction landing"], "icon": "clock",
                "label": "yes"}},
      {"title": "A real variance", "sub": ["pull the transactions"], "icon": "search"}],
    "note": "Every exit is listed in the report as filtered, with one line saying why."}),
   "The four timing tests in order of how often each one is the answer. Nothing is hidden: a "
   "filtered line appears in the report as filtered, with its reason.",
   "The four tests that separate timing differences from real variance",
   "A vertical chain of five steps entered by a box labelled A variance over threshold, for one "
   "line in one month. Step one asks whether a regular transaction is missing, checking the last "
   "twelve periods of transaction history to see whether a supplier who bills monthly did not "
   "this month; if so it exits to Timing, because the invoice is not in yet. Step two asks "
   "whether something arrived early against the budget shape for calendar-fixed lines; if so it "
   "exits to Timing, noting that next month will be under. Step three asks whether the year to "
   "date is within threshold; if so it exits to Timing, because the year is fine. Step four asks "
   "whether the movement is a reversal such as an accrual or a credit note; if so it exits to "
   "Timing as a correction landing. Step five is A real variance, where the transactions are "
   "pulled. A note says every exit is listed in the report as filtered, with one line saying "
   "why."),
  ("h3", "The missing regular"),
  ("p", "The most common cause of an underspend and the easiest to detect. A supplier who has "
        "invoiced in eleven of the last twelve periods, for a similar amount, and did not this "
        "period, is almost certainly late rather than absent. The line is under budget by "
        "roughly their usual amount, and it will be over by the same amount next month."),
  ("p", "The test is simply: are there suppliers on this account code with a monthly cadence who "
        "are missing this period, and does their usual total account for most of the variance? "
        "If yes, timing, and the report says which supplier."),
  ("h3", "The early arrival"),
  ("p", "The mirror image, and it only works because of the budget shaping from Part 3. A "
        "calendar-fixed line budgeted for August that gets paid in July produces a large July "
        "overspend and a large August underspend. Knowing the line is calendar-fixed and knowing "
        "which month it was due turns that from two anomalies into one recognisable event."),
  ("h3", "Year to date"),
  ("p", "The strongest test and the simplest. A line that is twenty per cent over for the month "
        "and within two per cent for the year has almost certainly just moved money between "
        "months. It is worth one line in the report and no attention."),
  ("p", "The one caveat is that this test weakens as the year progresses. In month eleven, a "
        "year-to-date figure is so large that a substantial monthly variance barely moves it, so "
        "the threshold for this test tightens over the year rather than staying fixed."),
  ("h3", "Reversals"),
  ("p", "An accrual posted last month and reversed this month, a credit note against a prior "
        "period's invoice, a misposting corrected. All of them produce a variance in a month "
        "where nothing happened, and all of them are identifiable from the transaction "
        "descriptions and the paired amounts."),
  ("h2", "Filtered, not hidden"),
  ("p", "Every filtered variance appears in the report, in a single line at the bottom, with its "
        "reason. This is a small thing and it is the difference between a report people trust "
        "and one they suspect."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Over threshold", "sub": ["11 lines"], "icon": "counter"},
      {"title": "Missing regular", "sub": ["3 filtered"], "icon": "clock"},
      {"title": "Early arrival", "sub": ["2 filtered"], "icon": "calendar"},
      {"title": "YTD fine", "sub": ["2 filtered"], "icon": "check"},
      {"title": "Reported", "sub": ["4 lines"], "icon": "report"}],
    "title": "ELEVEN LINES BECOME FOUR",
    "note": "The seven filtered lines are listed at the bottom of the report, with reasons."}),
   "The filter's arithmetic for one month. The seven that were removed are still on the page, "
   "which is what lets a reader disagree with the filter rather than distrust it.",
   "How eleven over-threshold variances become four reported ones",
   "A horizontal row of five boxes. Over threshold: eleven lines. Missing regular: three "
   "filtered. Early arrival: two filtered. Year to date fine: two filtered. Reported: four "
   "lines. A note says the seven filtered lines are listed at the bottom of the report with "
   "reasons."),
  ("h3", "Promotion after three months"),
  ("p", "A variance that is filtered as timing three months running is not timing. A supplier "
        "who has been late three months in a row has changed their billing, or has stopped "
        "supplying, or is disputing something. A line whose year to date has been fine three "
        "months running while every month is over is a trend that the year-to-date test is "
        "hiding."),
  ("p", "So a filter reason that repeats is escalated: the line moves into the reported section "
        "with a note saying it has been filtered three times and why that is now itself the "
        "finding. It is the one place where the system overrides its own rule, and it exists "
        "because the most dangerous thing a filter can do is be consistently right about "
        "something that is quietly becoming wrong."),
  ("p", "Next: what the report actually says."),
 ],
},
{
 "slug": "how-the-variance-report-reads",
 "title": "How the variance report reads",
 "nav": "How it reads",
 "read": 5, "words": 800,
 "desc": ("One page, four lines, transactions under each -- and the one variance type that "
          "matters most because it has no single transaction behind it."),
 "og": ("One page, four lines, transactions under each. The most interesting variance is the "
        "one with no big invoice behind it, because that is a rate change rather than an event."),
 "abstract": ("One page, four lines, the transactions under each -- and why the most "
              "interesting variance is the one with no single transaction behind it."),
 "lede": ("Everything else in this system exists so that this page can be short. A variance "
          "report that fits on a screen, has reasons attached, and can be read in ninety seconds "
          "is a different object from a management accounts pack, and it gets used differently."),
 "tags": ["budget variance", "reporting", "management accounts", "Amazon SES", "cost control",
          "serverless"],
 "takeaways": [
  "One page. Four lines is typical, seven is a bad month, twelve means the thresholds are wrong.",
  "Each line: the number, the year-to-date position, and the transactions behind it.",
  "The most interesting line is the one with no single transaction behind it.",
  "Filtered variances are listed at the bottom in one line each, with reasons.",
  "The report is regenerable and a restated period says so at the top.",
 ],
 "blocks": [
  ("h2", "What the page looks like"),
  ("callout", "July 2026 &mdash; four lines", [
   "<strong>Repairs &amp; maintenance &mdash; £2,400 over (£6,400 v £4,000).</strong> Year to "
   "date £1,900 over. One invoice: Ashford Plant, £2,150, compressor repair unit 2.",
   "<strong>Fuel &mdash; £1,180 over (11%).</strong> Year to date £3,900 over. No single "
   "transaction &mdash; 34 fuel card entries, average up 9% on last quarter. <em>Third "
   "consecutive month.</em>",
   "<strong>Subcontractors &mdash; £4,200 under.</strong> Year to date £600 over. Two suppliers "
   "who invoice monthly have not this month, worth about £5,100 between them.",
   "<strong>Card fees &mdash; £310 over on a rate basis.</strong> Budgeted 1.4% of card sales; "
   "actual 1.62%. Volume is on budget; the rate moved.",
   "<em>Filtered as timing: insurance (paid July, budgeted August), rates (quarterly instalment "
   "landed), stationery (YTD within 3%), accruals reversal on wages, three others &mdash; "
   "listed below.</em>",
  ]),
  ("p", "Four lines, each with its number, its year-to-date position, and its explanation. The "
        "third one is included even though the filter would have removed it, because it "
        "illustrates the point: subcontractors is under for the month and over for the year, "
        "which is a fact worth one sentence rather than an omission."),
  ("h2", "The line with no transaction behind it"),
  ("p", "Fuel is the interesting one and the report says so with the italic note. A variance "
        "explained by one large invoice is an event: it happened, somebody decided it, and it "
        "will not recur. A variance made of thirty-four small transactions with no single cause "
        "is a rate change, and rate changes compound."),
  ("fig", ("chain", {
    "entry": {"title": "A real variance", "sub": ["over threshold, not timing"], "icon": "counter"},
    "steps": [
      {"title": "Pull the transactions", "sub": ["this line, this period"], "icon": "search",
       "side": {"title": "Transaction rows", "sub": ["the imported period"], "icon": "log"}},
      {"title": "One dominant item?", "sub": ["over half the variance"], "icon": "branch",
       "exit": {"title": "Name it", "sub": ["an event, not a trend"], "icon": "doc",
                "label": "yes"}},
      {"title": "Spread across many?", "sub": ["no single cause"], "icon": "branch",
       "exit": {"title": "Flag a rate change", "sub": ["compare with last quarter"],
                "icon": "alarm", "label": "yes"}},
      {"title": "A few mid-sized items", "sub": ["list the top three"], "icon": "report"}],
    "note": "An event is a decision somebody made. A rate change is one nobody made."}),
   "How a real variance gets its explanation. The distinction between an event and a rate change "
   "is the most useful thing the report says, and it comes straight from the shape of the "
   "transactions.",
   "How a real variance is explained from its transactions",
   "A vertical chain of four steps entered by a box labelled A real variance, over threshold and "
   "not filtered as timing. Step one pulls the transactions for that line in that period from "
   "the imported rows. Step two asks whether one dominant item accounts for over half the "
   "variance; if so it exits to Name it, which is an event rather than a trend. Step three asks "
   "whether the variance is spread across many transactions with no single cause; if so it exits "
   "to Flag a rate change, comparing with the prior quarter. Step four handles a few mid-sized "
   "items by listing the top three. A note says an event is a decision somebody made and a rate "
   "change is one nobody made."),
  ("h2", "How many lines is right"),
  ("ul", [
   "<strong>Three or four</strong> is a healthy month and is what the thresholds should be tuned "
   "to produce.",
   "<strong>Seven or eight</strong> is a genuinely eventful month, and the report will be read "
   "carefully because it is unusual.",
   "<strong>Twelve or more, repeatedly,</strong> means the thresholds are too tight or the "
   "budget shaping has not been done. Fix the inputs rather than reading a longer report.",
   "<strong>Zero, repeatedly,</strong> is worse than twelve. It means the thresholds are so "
   "loose that a real problem would pass through, and the report is decorative.",
  ]),
  ("h3", "Restatements at the top"),
  ("p", "A report for a period that has been restated says so in its first line, with the date "
        "of the original and a note of which lines changed. Without that, two versions of July "
        "circulate and the person reading the second one has no way to know it supersedes the "
        "first, which is a reliable way to have a meeting about the wrong numbers."),
  ("h2", "What the report is not for"),
  ("callout", "Deliberately absent", [
   "A forecast. This report describes what happened; extrapolating from it is a separate "
   "exercise with different assumptions.",
   "Any commentary on whether a variance is acceptable. That is management's judgement and the "
   "system has no business supplying it.",
   "Departmental or per-person attribution. Account codes are not people, and a variance report "
   "that names individuals stops being read honestly.",
   "A running total of variances. Summing overspends and underspends produces a number that "
   "means nothing and looks meaningful.",
  ]),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="period",
 volumes=[(12, "12 periods"), (24, "24 periods"), (60, "60 periods")],
 read_each=0.021, msgs_each=1.0,
 lede=("This system runs once a period over a few thousand rows, which makes it the smallest "
       "workload in the series by some distance. Twelve periods a year for one entity is twelve "
       "runs; a group with five entities is sixty. Here is where each cent goes."),
 takeaway_extra=("A period is a few thousand rows and the system runs monthly, so the annual "
                 "bill is smaller than most single subscriptions it might find."),
 risks=[
  "<strong>Re-running on every restatement.</strong> Restatements are normal, but a system that "
  "re-imports and re-analyses on every identical re-send pays repeatedly for nothing. The file "
  "digest check is what prevents it.",
  "<strong>Sending the whole period to the model.</strong> The model is only needed to write the "
  "explanation sentences for the three or four surviving lines, not to read thousands of "
  "transactions. Feeding it the period is a hundredfold cost increase for no gain.",
  "<strong>Log retention left at never.</strong> This system runs twelve times a year and will "
  "otherwise be almost entirely a CloudWatch bill within eighteen months.",
 ],
 per_unit_note=("The read cost per period is higher than elsewhere in this series because the "
                "prompt carries the surviving variance lines and their transactions. It is still "
                "about two cents, and it runs once a month."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="bv",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the import discipline, and where the model is and is not used."),
 outside=[
  {"title": "Actuals export", "sub": ["scheduled CSV or API"], "icon": "money"},
  {"title": "Budget sheet", "sub": ["Sheets API, read-only"], "icon": "chart"},
  {"title": "SES outbound", "sub": ["the monthly report"], "icon": "email"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["exports,", "monthly schedule"], "icon": "bucket"},
  {"title": "Lambda x3", "sub": ["import, analyse,", "report"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["periods, lines"], "icon": "database"}],
 note="us-east-1. One account. Read-only against the ledger; nothing is ever written back.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The Actuals export, arriving as a "
  "scheduled CSV or through an API. The Budget sheet, read through the Google Sheets API "
  "read-only. And SES outbound, carrying the monthly report. Inside the account, three groups. "
  "S3 holding the exports and EventBridge carrying a monthly schedule. Three Lambda functions "
  "named import, analyse and report. And two DynamoDB tables named periods and lines. A note "
  "gives the region as us-east-1, one account, and states the system is read-only against the "
  "ledger and never writes anything back."),
 functions=[
  ["<code>bv-import</code>", "S3 ObjectCreated",
   "Digest check, period identification, whole-period replace", "120s / 1024&nbsp;MB"],
  ["<code>bv-analyse</code>", "SQS period queue",
   "Comparison, the four timing tests, transaction attribution", "60s / 1024&nbsp;MB"],
  ["<code>bv-report</code>", "EventBridge monthly + SQS",
   "One Bedrock call for the explanation sentences; sends the page", "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>bv-import-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:BatchWriteItem</code>",
   "The exports prefix; the periods table"],
  ["<code>bv-analyse-role</code>",
   "<code>dynamodb:Query</code>/<code>PutItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Periods and lines; the Sheets credential only"],
  ["<code>bv-report-role</code>", "<code>bedrock:InvokeModel</code>, <code>ses:SendEmail</code>",
   "One model arn; one verified identity"]],
 tables=[
  ("Table: periods",
   "PK   entity            S   main\n"
   "SK   period            S   2026-07#v2\n"
   "     file_digest       S   sha256 of the export as received\n"
   "     imported_at       S   2026-08-04T06:10:00Z\n"
   "     restatement_of    S   2026-07#v1, or null\n"
   "     row_count         N   3412\n"
   "     transactions      S   s3://exports/2026-07-v2.csv\n\n"
   "A version suffix on the sort key is what makes restatements cheap: the\n"
   "previous version is never deleted and the report can name what changed."),
  ("Table: lines",
   "PK   entity_period     S   main#2026-07#v2\n"
   "SK   code              S   6210\n"
   "     name              S   Repairs & maintenance\n"
   "     budget            N   4000.00\n"
   "     actual            N   6400.00\n"
   "     variance          N   2400.00\n"
   "     ytd_budget        N   28000.00\n"
   "     ytd_actual        N   29900.00\n"
   "     shape             S   flat | seasonal | calendar | rate\n"
   "     verdict           S   reported | timing\n"
   "     timing_reason     S   missing_regular | early | ytd_ok | reversal\n"
   "     filtered_run      N   how many consecutive periods filtered\n"
   "     top_items         L   [{supplier, amount, description}]\n\n"
   "`filtered_run` is what promotes a variance explained away three months in\n"
   "a row. A consistent filter is itself a finding.")],
 inbound=[
  "<strong>Exports</strong> land in an S3 prefix, either dropped by a scheduled job in the "
  "accounting package or written by a small sync. The S3 event fires the import.",
  "<strong>The digest check comes first.</strong> An identical file is a duplicate and does "
  "nothing; a different file for a period already imported is a restatement.",
  "<strong>A period is replaced whole.</strong> There is no patch path, because accounting "
  "exports rarely carry stable row identifiers and a wrong diff is worse than a slow rewrite.",
  "<strong>Nothing is written back</strong> to the ledger, ever. The system has no credential "
  "with write access to the accounting package."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "used only to turn a variance and its top transactions into one readable sentence.",
  "<strong>Called once per period</strong>, with the three or four surviving lines. It never "
  "sees the full transaction set.",
  "<strong>It does not decide anything.</strong> The comparison, the four timing tests and the "
  "attribution are all arithmetic, computed before the model is involved.",
  "<strong>Output is a JSON schema</strong> with one sentence per line, constrained to state "
  "only what is in the numbers it was given.",
  "<strong>No commentary.</strong> The prompt explicitly forbids judgement about whether a "
  "variance is acceptable, which is management's call and not a model's."],
 gotchas=[
  "Insist on transaction-level data. A trial balance gives you the variance and none of the "
  "reason, and the reason is the whole product.",
  "Shape the budget before tuning the thresholds. Most false variances come from a flat twelfth "
  "and no threshold setting will fix that.",
  "Tighten the year-to-date test as the year progresses. In month eleven a large monthly "
  "variance barely moves the year-to-date figure and the test stops working.",
  "List filtered variances rather than hiding them. A reader who cannot see what was removed "
  "will not trust what was kept.",
  "Promote a variance filtered three times running. A consistently correct filter is the most "
  "dangerous thing in the system."],
))
