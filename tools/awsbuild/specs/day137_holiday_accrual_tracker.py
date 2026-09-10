"""Day 137 -- 2026-09-08 -- Holiday accrual tracker."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "holiday-accrual-tracker"
NAME = "Holiday accrual tracker"

SPEC = {
 "slug": SLUG, "date": "2026-09-08", "name": NAME,
 "tagline": ("Works out how much paid holiday every worker has actually accrued when the "
             "hours are irregular, keeps the balance moving as leave is booked and carried "
             "over, and can say on any date what the business owes if that person walks out "
             "of it."),
 "lede": ("A small system for any employer with staff who do not work the same week twice: "
          "hours in, entitlement accrued, leave deducted, carry-over applied under the rule "
          "that allows it, and a balance that is defensible on the day somebody leaves. Seven "
          "posts on the same system, one diagram at a time, with a cost breakdown and an "
          "engineering reference at the end."),
 "keywords": ["holiday accrual", "irregular hours", "part-year workers", "12.07 per cent",
              "leave year", "serverless"],
 "icons": ["calendar", "counter", "team"],
 "faq": [
  ("Why can't I just give everyone the same number of days?",
   "Because a day means nothing to somebody whose shifts are four hours long one week and "
   "eleven the next. For irregular-hours and part-year workers the entitlement is accrued in "
   "hours, as a percentage of the hours actually worked in each pay period."),
  ("Where does 12.07% come from?",
   "It is 5.6 weeks of statutory leave divided by the 46.4 working weeks that remain once you "
   "take that leave out of the year. It is the same entitlement as everybody else's, expressed "
   "as a rate rather than a number of days."),
  ("Can holiday be carried into the next year?",
   "Some of it, in defined circumstances -- sickness, family leave, or where the employer "
   "never gave a real opportunity to take it. Each route carries a different amount for a "
   "different length of time, and the difference matters when somebody leaves."),
  ("What happens on the last day?",
   "Accrued and untaken leave is paid. It is one of the few payroll numbers a former employee "
   "will check, and one of the easiest to get wrong by a year of arithmetic."),
  ("What does it cost to run?",
   "A few dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "holiday-accrual-tracker-on-aws",
 "title": "A holiday accrual tracker on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Hours in, entitlement accrued, leave deducted, carry-over applied, and a balance "
          "that survives the last day. AWS, about $3 a month."),
 "og": ("769 hours of holiday nobody could account for. Not stolen, not refused -- just never "
        "counted, because the rota system and the payroll system have never spoken."),
 "abstract": ("The whole system on one page -- hours, accrual, bookings, carry-over and the "
              "leaving balance -- and why irregular hours turn a simple entitlement into an "
              "unbooked liability."),
 "lede": ("The owner of a small care agency asked a reasonable question: how many days holiday "
          "does Marta have left. Nobody could answer it. The rota lives in one app, the "
          "timesheets in another, and holiday is a shared spreadsheet somebody set up in 2023 "
          "with a column per person and no formula in it. Marta has worked there four years."),
 "tags": ["holiday accrual", "irregular hours", "payroll", "HR", "compliance", "serverless"],
 "takeaways": [
  "For irregular hours, entitlement accrues from hours worked, not from days on a calendar.",
  "The accrual happens every pay period, whether or not anybody records it.",
  "Untracked accrual does not disappear. It becomes a liability nobody has booked.",
  "The balance has to be answerable on any date, not just at year end.",
  "Designed on AWS for about $3 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Hours worked", "sub": ["rota, timesheets,", "clock-ins"], "icon": "clock"},
      {"title": "Leave requests", "sub": ["booked, cancelled,", "and taken"], "icon": "calendar"},
      {"title": "The rules", "sub": ["statutory minimum,", "contract, carry-over"], "icon": "key"}],
    "inside": [
      {"title": "Accrual ledger", "sub": ["hours earned, one", "line per period"], "icon": "counter"},
      {"title": "Balance", "sub": ["earned minus taken,", "on any date"], "icon": "chart"},
      {"title": "Liability and payout", "sub": ["what is owed, and", "to whom"], "icon": "money"}],
    "edges": [{"from": 0, "to": 0, "label": "every pay period"},
              {"from": 1, "to": 1, "label": "as they happen"},
              {"from": 2, "to": 2, "label": "once a leave year", "up": True}],
    "note": "The middle column is the whole job. The hours already exist and the rules are "
            "published; what is missing everywhere is the ledger that joins them."}),
   "Three things outside the account, three pieces inside it. The ledger in the middle is the "
   "artefact almost nobody has.",
   "System: hours, leave and the rules joined into an accrual ledger",
   "Three boxes across the top sit outside the AWS account. On the left, Hours worked from "
   "rota, timesheets and clock-ins. In the middle, Leave requests booked, cancelled and taken. "
   "On the right, The rules: statutory minimum, contract and carry-over. Each connects by an "
   "arrow to the AWS account container below, labelled every pay period, as they happen, and "
   "once a leave year. Inside the AWS account are three components in a row. Accrual ledger: "
   "hours earned, one line per period. Balance: earned minus taken, on any date. And Liability "
   "and payout: what is owed and to whom. A note says the middle column is the whole job, "
   "because the hours already exist and the rules are published, and what is missing "
   "everywhere is the ledger that joins them."),
  ("h3", "Why the hours go missing"),
  ("p", "Holiday for a fixed five-day week is easy enough that nobody builds a system for it. "
        "Twenty-eight days, count them down, done. The trouble starts the moment a business "
        "has staff who work four hours on Tuesday, eleven on Saturday and nothing at all in "
        "February, because a day is no longer a unit of anything."),
  ("p", "For those workers the entitlement is a rate rather than a number: a percentage of the "
        "hours actually worked in each pay period, accruing continuously. That is a perfectly "
        "workable rule, and it has one operational consequence that catches every business "
        "that meets it for the first time. The entitlement accrues whether or not anybody "
        "writes it down. It does not wait for a spreadsheet."),
  ("p", "So the accrual runs quietly for four years while the shared sheet records only the "
        "leave that was taken, and the difference between the two sits on the books as nothing "
        "at all until somebody resigns and asks to be paid for it."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The leave year.</strong> Which twelve months a balance belongs to, and where that "
   "boundary comes from when nobody wrote it down. Part 2.",
   "<strong>Accrual.</strong> Hours worked in a pay period turned into hours of entitlement, "
   "one immutable line at a time. Part 3.",
   "<strong>Bookings and carry-over.</strong> Leave deducted as it is taken, and the three "
   "quite different reasons a balance is allowed to cross the year boundary. Part 4.",
   "<strong>The last day.</strong> What is owed when somebody leaves, and the evidence that "
   "makes the number stand up. Part 5.",
  ]),
  ("h2", "One employer, one leave year"),
  ("fig", ("strip", {
    "stages": [
      {"title": "46 staff", "sub": ["31 of them on", "irregular hours"], "icon": "team"},
      {"title": "41,000 hours", "sub": ["worked by those 31", "in one leave year"], "icon": "clock"},
      {"title": "4,949 hours", "sub": ["accrued at", "12.07%"], "icon": "counter"},
      {"title": "4,180 taken", "sub": ["booked, taken and", "deducted"], "icon": "calendar"},
      {"title": "769 hours left", "sub": ["about GBP 9,700", "unaccounted for"], "icon": "alarm"}],
    "title": "ONE CARE AGENCY, ONE LEAVE YEAR",
    "note": "The last box is not a dispute. It is a real entitlement on one side and an "
            "unbooked liability on the other, and nobody has written it down anywhere."}),
   "The same system as one line. The first four boxes are ordinary operations; the fifth is "
   "the number that only appears when somebody works it out.",
   "One employer's leave year from hours worked to hours unaccounted for",
   "A horizontal row of five boxes joined by arrows. Forty-six staff, thirty-one of them on "
   "irregular hours. Forty-one thousand hours worked by those thirty-one in one leave year. "
   "Four thousand nine hundred and forty-nine hours accrued at twelve point zero seven per "
   "cent. Four thousand one hundred and eighty hours booked, taken and deducted. And seven "
   "hundred and sixty-nine hours left, worth about nine thousand seven hundred pounds, "
   "unaccounted for. A note says the last box is not a dispute but a real entitlement on one "
   "side and an unbooked liability on the other, written down nowhere."),
  ("h2", "In plain words"),
  ("p", "Every pay period, the hours each worker actually worked are read from wherever they "
        "already live &mdash; a rota export, a timesheet, a clock-in feed &mdash; and turned "
        "into hours of entitlement at the applicable rate. That produces one ledger line per "
        "worker per period, and those lines are never edited afterwards. If a period is later "
        "corrected, the correction is another line."),
  ("p", "Leave requests come in from wherever the business already takes them, and a booking "
        "that is actually taken becomes a negative line in the same ledger. Booked-but-not-yet"
        "-taken is tracked separately, because a request in September for next March is not a "
        "deduction yet and treating it as one produces a balance that goes backwards when "
        "somebody cancels."),
  ("p", "At the leave year boundary the system does the one piece of genuine reasoning in it: "
        "it decides how much of an unused balance is allowed to cross into the next year, "
        "under which of the three rules, and for how long the carried amount survives. That is "
        "part four, and it is where most manual processes simply zero the column and hope."),
  ("p", "And on any date, for any worker, the system can produce a balance with the arithmetic "
        "attached: this many hours accrued from these periods, this many taken on these dates, "
        "this much carried in under this rule, leaving this. That sentence is the deliverable. "
        "The number on its own is worth very little when somebody disagrees with it."),
  ("callout", "Design rules that shaped every decision", [
   "The ledger is append-only. A correction is a new line, never an edit.",
   "Accrual is calculated from hours worked, never from hours rostered.",
   "A booking is not a deduction until the leave has actually been taken.",
   "Carry-over records which rule allowed it, not just that some was allowed.",
   "Every balance can name the lines it came from.",
   "The system never rounds a balance in the employer's favour.",
  ]),
  ("h2", "What it does not do"),
  ("p", "It does not run payroll. It produces the hours and the rate that payroll needs, and "
        "it reconciles against what payroll actually paid, but the payment itself belongs "
        "somewhere that already handles tax codes and national insurance and is regulated for "
        "it."),
  ("p", "It does not approve leave either. Whether Marta can have the first week of August off "
        "is a staffing decision made by somebody who knows who else is away, and the system's "
        "only contribution is telling them the balance is sufficient. Approval workflows are a "
        "different product and every business already has one, even if it is a group chat."),
  ("p", "It also does not give legal advice. It implements a set of rules that are written "
        "down and dated, records which version of them it applied, and shows its working. When "
        "the rules change &mdash; and this area changes every few years &mdash; the old "
        "calculations remain correct for the periods they were made in, which is the whole "
        "reason the ledger is append-only."),
  ("p", "The next four posts walk through each piece: what a leave year actually is and where "
        "the boundary comes from, how hours become entitlement, how bookings and carry-over "
        "move the balance, and what is owed on the last day. One diagram per post, a cost "
        "breakdown, and an engineering reference at the end."),
 ],
},
]

SPEC["parts"].append(
{
 "slug": "what-a-leave-year-actually-is",
 "title": "What a leave year actually is, and why yours might be 46 of them",
 "nav": "The leave year",
 "read": 5, "words": 800,
 "desc": ("Where the leave year boundary comes from, what happens when nobody ever set one, "
          "and the two pots of entitlement hiding inside a single year."),
 "og": ("If the contract never named a leave year, each worker gets their own, starting on "
        "the anniversary of the day they joined. Forty-six staff, forty-six year ends."),
 "abstract": ("Establishing the twelve-month window an entitlement belongs to, the "
              "per-worker default that applies when no window was ever agreed, and the split "
              "between the four-week and 1.6-week pots."),
 "lede": ("A balance is meaningless without a window. Every hour of holiday belongs to a "
          "particular twelve months, and almost every argument about holiday turns out, on "
          "inspection, to be an argument about which twelve months a particular hour belonged "
          "to."),
 "tags": ["leave year", "holiday accrual", "employment contract", "HR", "compliance",
          "serverless"],
 "takeaways": [
  "A leave year is whatever the contract says. That is the first place to look.",
  "With nothing agreed, it defaults to the anniversary of each worker's start date.",
  "That default gives a business as many year ends as it has workers.",
  "The 5.6 weeks is really two pots with different pay and carry-over rules.",
  "Record which boundary applies to whom, and where you got it from.",
 ],
 "blocks": [
  ("h2", "Where the boundary comes from"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "The contract", "sub": ["names a leave year", "explicitly"], "icon": "doc",
       "label": "read it"},
      {"title": "A written policy", "sub": ["handbook, offer letter,", "or a signed variation"],
       "icon": "form", "label": "read it too"},
      {"title": "Nobody said", "sub": ["no document names", "a leave year"], "icon": "search",
       "label": "the default applies"}],
    "target": {"title": "Leave year boundary", "sub": ["a start date, and", "where it came from"],
               "icon": "calendar",
               "then": {"title": "Entitlement window", "sub": ["the twelve months a", "balance belongs to"],
                        "icon": "counter"}},
    "note": "The third lane is the common one and it is the expensive one, because the default "
            "is per-worker rather than per-business."}),
   "Three routes to one boundary. Which route you took is recorded, because the third one "
   "produces a different answer for every member of staff.",
   "Three sources for a leave year boundary converging on one entitlement window",
   "Three boxes on the left feed one box on the right. The contract names a leave year "
   "explicitly, and the instruction is to read it. A written policy in a handbook, offer "
   "letter or signed variation, and the instruction is to read it too. Nobody said, meaning no "
   "document names a leave year, in which case the default applies. All three converge on "
   "Leave year boundary, holding a start date and where it came from, which feeds a box "
   "labelled Entitlement window: the twelve months a balance belongs to. A note says the third "
   "lane is the common one and the expensive one, because the default is per-worker rather "
   "than per-business."),
  ("h3", "The default is per-person, and that is the problem"),
  ("p", "Where no leave year has been agreed in writing, each worker's own runs from the "
        "anniversary of the day they started. This is a sensible rule &mdash; it guarantees "
        "everybody gets a full twelve months to use a full year's entitlement &mdash; and it "
        "quietly means a business of forty-six people that never wrote anything down has "
        "forty-six year ends scattered across the calendar."),
  ("p", "Nobody administers that by hand, so what actually happens is that the business "
        "invents a single year end, usually the one the accounts run to, and applies it to "
        "everybody. That is fine right up until somebody who joined in November leaves in "
        "September, at which point the balance they are owed and the balance in the "
        "spreadsheet are calculated over two different periods and disagree."),
  ("p", "The fix is not clever. It is to record the boundary per worker, along with the "
        "document it came from, and to set a proper contractual leave year for new starters so "
        "the population of per-person years stops growing. The system can hold both at once, "
        "which is what a business in this position actually needs."),
  ("h2", "The two pots inside one year"),
  ("fig", ("strip", {
    "stages": [
      {"title": "5.6 weeks", "sub": ["the statutory", "minimum"], "icon": "calendar"},
      {"title": "4 weeks", "sub": ["paid at normal", "remuneration"], "icon": "money"},
      {"title": "1.6 weeks", "sub": ["paid at basic", "contractual pay"], "icon": "money"},
      {"title": "Anything more", "sub": ["contractual extra,", "employer's own rules"], "icon": "tag"},
      {"title": "Different rules", "sub": ["pay, carry-over and", "what survives a year"], "icon": "branch"}],
    "title": "ONE ENTITLEMENT, THREE LAYERS",
    "note": "The layers are paid differently and carry over differently. A single balance "
            "column cannot represent any of that."}),
   "The statutory minimum is not one thing. It is two pots with different pay rules stacked "
   "on top of each other, plus whatever the employer adds voluntarily.",
   "The 5.6 week statutory minimum split into a four week pot, a 1.6 week pot and contractual extra",
   "A horizontal row of five boxes joined by arrows. Five point six weeks, the statutory "
   "minimum. Four weeks, paid at normal remuneration. One point six weeks, paid at basic "
   "contractual pay. Anything more, being contractual extra under the employer's own rules. "
   "And Different rules, covering pay, carry-over and what survives a year. A note says the "
   "layers are paid differently and carry over differently, and a single balance column cannot "
   "represent any of that."),
  ("h3", "Why the split is worth carrying in the data"),
  ("p", "Normal remuneration means what the worker normally earns, which for a lot of "
        "irregular-hours staff includes regular overtime, shift premiums and commission. Basic "
        "contractual pay means the contractual rate. For a warehouse worker who does six hours "
        "of Saturday overtime most weeks, those two numbers are not close, and four weeks of "
        "the year are paid at the higher one."),
  ("p", "Businesses that pay everything at basic underpay, and businesses that pay everything "
        "at normal overpay, and neither of them finds out until an employment tribunal or an "
        "accountant does the multiplication. The system carries the split because carrying it "
        "costs one field and reconstructing it later costs a year of payslips."),
  ("p", "The carry-over rules differ across the same boundary, which part four covers. It is "
        "enough here to note that the pots are not interchangeable, and that when leave is "
        "taken the system has to decide which pot it came out of. It takes it from the pot "
        "that expires first, which is the answer that leaves the worker best off and is "
        "therefore the safe default."),
  ("callout", "What the leave year record holds", [
   "<strong>Start date.</strong> The day the window opens for this worker.",
   "<strong>Source.</strong> Contract, policy, or the statutory default.",
   "<strong>Evidence.</strong> A link to the document, not a note that one exists.",
   "<strong>Entitlement basis.</strong> Statutory minimum, or a contractual figure above it.",
   "<strong>Pot split.</strong> How much of the entitlement sits in each layer.",
   "<strong>Superseded by.</strong> Set when a new contract moves the boundary.",
  ]),
  ("h2", "Moving a leave year"),
  ("p", "Businesses do consolidate onto a single leave year, and it is a good idea. The "
        "mechanics are the part that goes wrong: the transition produces a short year for most "
        "people, that short year still has to carry a proportionate entitlement, and the "
        "entitlement already accrued in the part-year cannot be reduced by the change."),
  ("p", "So a move is recorded as two windows rather than as an edit to one. The old window "
        "closes on the day of the change with whatever it accrued, and a new window opens the "
        "next day. The balance carried across is a normal carry-over event with a reason of "
        "<code>leave_year_moved</code>, which means the audit trail explains itself without "
        "anybody remembering what happened in 2026."),
  ("p", "The next post is the arithmetic: how a set of hours in a pay period becomes a number "
        "of hours of entitlement, and why that calculation has to run on the hours actually "
        "worked rather than the hours somebody was scheduled for."),
 ],
})

SPEC["parts"].append(
{
 "slug": "accruing-holiday-on-irregular-hours",
 "title": "Accruing holiday on irregular hours: where 12.07% comes from",
 "nav": "Accrual",
 "read": 5, "words": 810,
 "desc": ("Turning the hours actually worked in a pay period into hours of entitlement, the "
          "absences that still accrue, and why rounding has a direction."),
 "og": ("5.6 weeks of leave divided by the 46.4 working weeks left over is 12.07%. It is not a "
        "concession or a formula somebody invented -- it is the same entitlement, restated."),
 "abstract": ("The accrual calculation for irregular-hours and part-year workers: hours worked "
              "in a period, the average that covers protected absence, the rate, and one "
              "immutable ledger line per period."),
 "lede": ("This is the arithmetic, and it is genuinely small. What makes it worth a post is "
          "that three of the four inputs are things businesses routinely get from the wrong "
          "system, and each wrong input fails silently in the same direction."),
 "tags": ["holiday accrual", "irregular hours", "12.07 per cent", "payroll", "timesheets",
          "serverless"],
 "takeaways": [
  "12.07% is 5.6 weeks divided by the 46.4 weeks that are left once you remove them.",
  "Accrue on hours worked, not hours rostered. A cancelled shift accrues nothing.",
  "Protected absence still accrues, at an average of the previous 52 paid weeks.",
  "Round up, to the nearest part-hour. Never round down.",
  "One ledger line per worker per period, written once and never edited.",
 ],
 "blocks": [
  ("h2", "One pay period, one ledger line"),
  ("fig", ("chain", {
    "entry": {"title": "A pay period", "sub": ["closed, with hours", "attached"], "icon": "clock"},
    "steps": [
      {"title": "Read hours worked", "sub": ["from the timesheet,", "not the rota"], "icon": "form",
       "exit": {"title": "Hold", "sub": ["no timesheet means", "no accrual yet"], "icon": "alarm",
                "label": "missing"}},
      {"title": "Add covered absence", "sub": ["sick and family leave,", "at the 52-week average"],
       "icon": "shield"},
      {"title": "Apply the rate", "sub": ["12.07%, or the", "contractual rate"], "icon": "counter"},
      {"title": "Round upward", "sub": ["to the nearest", "part-hour"], "icon": "check"},
      {"title": "Write the line", "sub": ["append-only, with", "its inputs"], "icon": "database"}],
    "note": "The second step is the one everybody omits. A worker on maternity leave or "
            "long-term sick keeps accruing, and zero hours worked does not mean zero accrued."}),
   "Five steps and one hold. Nothing here is difficult; the value is that it runs every period "
   "without anybody remembering to do it.",
   "A pay period turned into one line of accrued entitlement",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled A "
   "pay period, closed with hours attached. Read hours worked takes them from the timesheet "
   "rather than the rota, with a side exit reading missing: Hold, because no timesheet means "
   "no accrual yet. Add covered absence brings in sick and family leave at the fifty-two week "
   "average. Apply the rate uses twelve point zero seven per cent or the contractual rate. "
   "Round upward goes to the nearest part-hour. Write the line appends it with its inputs. A "
   "note says the second step is the one everybody omits, because a worker on maternity leave "
   "or long-term sick keeps accruing and zero hours worked does not mean zero accrued."),
  ("h3", "Where the number comes from"),
  ("p", "A year has 52 weeks. The statutory minimum is 5.6 weeks of paid leave. If you take "
        "those 5.6 weeks out, 46.4 weeks are left, and those are the weeks in which the worker "
        "is actually at work earning the leave. Divide 5.6 by 46.4 and you get 0.1207, which "
        "is where 12.07 per cent comes from."),
  ("p", "It is worth saying plainly because it is often presented as a rule of thumb or a "
        "generosity, and it is neither. It is the identical entitlement everybody else gets, "
        "expressed as a rate so that it can be applied to hours instead of to days. A worker "
        "who accrues at 12.07 per cent over a full year of ordinary hours ends up with exactly "
        "5.6 weeks."),
  ("p", "If the contract is more generous than the statutory minimum, the rate goes up "
        "correspondingly and the system stores the rate per worker rather than as a constant. "
        "This costs nothing and it is the difference between a system that can handle the one "
        "long-serving manager on 30 days and one that quietly underpays her."),
  ("h2", "Rostered is not worked"),
  ("p", "The single most common data error here is accruing on the rota. The rota is available, "
        "it is tidy, it is in one system, and it is wrong. Shifts get cancelled the night "
        "before, swapped, cut short when a client goes into hospital, or extended by two hours "
        "because the relief did not turn up."),
  ("p", "Accruing on the rota overstates entitlement in a business where shifts get cancelled "
        "and understates it in one where they overrun, and in both cases the ledger stops "
        "reconciling with payroll, which is the only external check the system has. The rule "
        "is to accrue on the same hours the worker was paid for, from the same source payroll "
        "used, so that the two can be compared."),
  ("h2", "Three workers, one leave year"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Term-time cook", "parts": [("taken", 118), ("owed", 47)]},
      {"label": "Bank carer", "parts": [("taken", 62), ("owed", 143)]},
      {"label": "Weekend driver", "parts": [("taken", 74), ("owed", 12)]}],
    "series": [("taken", "Hours of leave taken", "#7AA116"),
               ("owed", "Accrued and still untaken", "#DD344C")],
    "unit": "",
    "note": "Same employer, same leave year, same rule. The middle bar is the one that turns "
            "into a payment somebody has not budgeted for."}),
   "Hours accrued in one leave year for three working patterns, split by what was actually "
   "taken. The red band is the liability.",
   "Hours accrued and taken for three irregular-hours workers over one leave year",
   "Three vertical stacked bars, each showing hours of holiday accrued in a leave year split "
   "into hours taken in green and hours accrued but still untaken in red. A term-time cook "
   "accrued about one hundred and sixty-five hours, of which one hundred and eighteen were "
   "taken and forty-seven remain. A bank carer accrued about two hundred and five hours, of "
   "which only sixty-two were taken and one hundred and forty-three remain. A weekend driver "
   "accrued about eighty-six hours, of which seventy-four were taken and twelve remain. A note "
   "says it is the same employer, leave year and rule in all three cases, and the middle bar "
   "is the one that turns into a payment somebody has not budgeted for."),
  ("h3", "Why the bank carer looks like that"),
  ("p", "Because bank staff are called when somebody else is off, and the times when somebody "
        "else is off are exactly the times a bank worker cannot take leave. The pattern is "
        "structural rather than personal, it shows up in every business that keeps a flexible "
        "pool, and it is invisible in a system that only records leave taken."),
  ("p", "That is the argument for the ledger in one sentence. A business that can see the "
        "middle bar in month four has options: it can encourage leave, it can plan the cash, it "
        "can look at whether the pool is being used the way it was meant to be. A business "
        "that sees it on somebody's last day has a bill."),
  ("callout", "The four inputs, and how each one goes wrong", [
   "<strong>Hours worked.</strong> Taken from the rota instead of the timesheet.",
   "<strong>Covered absence.</strong> Omitted entirely, so long-term sick accrues nothing.",
   "<strong>The rate.</strong> Hard-coded at 12.07% for a worker whose contract says more.",
   "<strong>The period.</strong> Attributed to the wrong leave year at the boundary.",
  ]),
  ("h2", "Rounding has a direction"),
  ("p", "Accrual produces awkward numbers &mdash; 12.07 per cent of 37 hours and 40 minutes is "
        "not going to land on anything tidy &mdash; so something has to round. The rule the "
        "system follows is to round up, to the nearest part-hour, every time."),
  ("p", "This is not generosity, it is risk management. Rounding down accrual, in one "
        "direction, across every period, across every irregular-hours worker, for four years, "
        "compounds into a systematic underpayment that is indefensible precisely because it is "
        "systematic. The cost of rounding the other way is a few minutes per worker per year. "
        "The next post is what happens to those hours at the year end."),
 ],
})

SPEC["parts"].append(
{
 "slug": "booking-time-off-and-carrying-it-over",
 "title": "Booking time off, and the three reasons a balance survives the year",
 "nav": "Bookings and carry-over",
 "read": 5, "words": 800,
 "desc": ("Why a booking is not a deduction, which pot leave comes out of, and the three "
          "distinct routes by which an unused balance is allowed to cross into the next year."),
 "og": ("Most manual holiday processes zero the column on 31 March. Three separate rules say "
        "some of that balance was never theirs to zero."),
 "abstract": ("The lifecycle of a leave booking from request to deduction, and the three "
              "carry-over routes -- sickness, family leave and employer failure -- each with "
              "its own amount and its own expiry."),
 "lede": ("A balance moves for two reasons: leave is taken, or a year ends. The first is "
          "simpler than most systems make it and the second is more complicated than most "
          "spreadsheets admit, and both failures point the same way."),
 "tags": ["carry-over", "holiday booking", "leave year", "HR", "compliance", "serverless"],
 "takeaways": [
  "A request reserves. Only leave actually taken deducts.",
  "Deduct from the pot that expires first, which is the answer that favours the worker.",
  "Sickness carry-over is capped and expires 18 months after the year it accrued in.",
  "Family leave carries the whole entitlement into the following year.",
  "Where the employer never gave a real chance to take it, the balance keeps accumulating.",
 ],
 "blocks": [
  ("h2", "A request is not a deduction"),
  ("fig", ("chain", {
    "entry": {"title": "A leave request", "sub": ["dates, hours,", "and a worker"], "icon": "calendar"},
    "steps": [
      {"title": "Check the balance", "sub": ["projected to the", "requested dates"], "icon": "chart",
       "exit": {"title": "Tell them", "sub": ["with the number,", "not just a no"], "icon": "stop",
                "label": "insufficient"}},
      {"title": "Reserve it", "sub": ["visible, but not", "yet deducted"], "icon": "lock",
       "exit": {"title": "Release", "sub": ["reservation removed,", "balance restored"], "icon": "retry",
                "label": "cancelled"}},
      {"title": "The dates pass", "sub": ["the leave was", "actually taken"], "icon": "clock"},
      {"title": "Deduct", "sub": ["from the pot that", "expires first"], "icon": "counter"},
      {"title": "Write the line", "sub": ["negative, with the", "pot it came from"], "icon": "database"}],
    "note": "Deducting at request time makes the balance go backwards when somebody cancels, "
            "and a balance that goes backwards is a balance nobody trusts."}),
   "Five steps and two ways out. The distinction between reserved and deducted is the whole "
   "reason the projected balance can be trusted.",
   "A leave request moving from reservation to deduction",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled A "
   "leave request with dates, hours and a worker. Check the balance projects it forward to the "
   "requested dates, with a side exit reading insufficient: Tell them, with the number rather "
   "than just a no. Reserve it makes the request visible but not yet deducted, with a side exit "
   "reading cancelled: Release, the reservation removed and the balance restored. The dates "
   "pass, meaning the leave was actually taken. Deduct takes it from the pot that expires "
   "first. Write the line appends a negative entry recording the pot it came from. A note says "
   "deducting at request time makes the balance go backwards when somebody cancels, and a "
   "balance that goes backwards is a balance nobody trusts."),
  ("h3", "Projected, not current"),
  ("p", "The number a worker needs when they are booking August in February is not their "
        "balance today. It is what their balance will be in August, given the accrual they are "
        "expected to earn between now and then and the leave they have already reserved. Those "
        "are different numbers and the second is the useful one."),
  ("p", "The projection is deliberately conservative: it accrues forward at the average of the "
        "last complete quarter rather than the best one, and it treats every existing "
        "reservation as if it will be taken. A worker told they can book and then told later "
        "that they cannot has been failed by the system, and the failure is expensive in a way "
        "that does not appear on any ledger."),
  ("h2", "Three reasons a balance crosses the year end"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Sickness", "sub": ["could not take it", "because they were ill"],
       "icon": "shield", "label": "capped, 18 months"},
      {"title": "Family leave", "sub": ["maternity, adoption,", "shared parental"],
       "icon": "person", "label": "the whole entitlement"},
      {"title": "Employer failure", "sub": ["never told, never", "given the chance"],
       "icon": "alarm", "label": "accumulates"}],
    "target": {"title": "Carried balance", "sub": ["amount, reason,", "and expiry"], "icon": "counter",
               "then": {"title": "Next leave year", "sub": ["opens holding the", "carried hours"],
                        "icon": "calendar"}},
    "note": "Three routes, three different amounts, three different expiries. A single "
            "carry_over field cannot tell them apart, and they are settled very differently."}),
   "Three quite separate rules that happen to have the same effect on a balance. Which one "
   "applied is recorded, because it determines when the hours die.",
   "Three carry-over routes converging on one carried balance",
   "Three boxes on the left feed one box on the right. Sickness, where the worker could not "
   "take leave because they were ill, is capped and lasts eighteen months. Family leave "
   "covering maternity, adoption and shared parental leave carries the whole entitlement. "
   "Employer failure, where the worker was never told about the entitlement or never given the "
   "chance to take it, accumulates. All three converge on Carried balance holding an amount, a "
   "reason and an expiry, which feeds a box labelled Next leave year, opening with the carried "
   "hours in it. A note says three routes mean three different amounts and three different "
   "expiries, that a single carry-over field cannot tell them apart, and that they are settled "
   "very differently."),
  ("h3", "The third route is the one that surprises people"),
  ("p", "The first two are foreseeable: somebody was off sick, or somebody was on maternity "
        "leave, and in both cases the business knows it happened. The third is different, "
        "because it is a finding about the employer's own conduct, and no employer files that "
        "finding against themselves in advance."),
  ("p", "The substance of it is straightforward. If a worker was never told what they were "
        "entitled to, or was never realistically able to take it, or was never warned that it "
        "would be lost at the year end, then it is not lost at the year end. It keeps rolling "
        "forward. For a business with a pool of bank staff who have never been sent a balance "
        "in their lives, that is not a hypothetical."),
  ("p", "Which is, in a sense, the strongest argument for building this at all. A system that "
        "sends every worker their balance and a note saying what happens to it at the year end "
        "does not only produce a tidier ledger. It converts an open-ended accumulating "
        "liability into an ordinary one that expires on schedule."),
  ("callout", "What a carry-over line records", [
   "<strong>Amount.</strong> In hours, from the closing balance of the year it accrued in.",
   "<strong>Reason.</strong> Sickness, family leave, employer failure, agreement, or a moved "
   "leave year.",
   "<strong>Source year.</strong> Which window it was earned in. Not the one it lands in.",
   "<strong>Pot.</strong> Which of the layers it came from, because they expire differently.",
   "<strong>Expires on.</strong> A date, computed at the time, never recomputed later.",
   "<strong>Evidence.</strong> What supports it -- the sickness record, the leave dates, the "
   "notice that was or was not sent.",
  ]),
  ("h2", "Which pot leave comes out of"),
  ("p", "When a worker takes a week off, the system has to decide whether that week came out "
        "of carried hours from last year, this year's four-week pot, this year's 1.6 weeks, or "
        "contractual extra. Nothing tells it, so it needs a rule, and the rule is to spend the "
        "hours that expire soonest."),
  ("p", "That is the answer that leaves the worker with the most usable entitlement at the end "
        "of the year, which makes it both the fair default and the defensible one. It is also "
        "the answer that minimises the carried balance, which is what the finance side wants, "
        "so this is a rare case where nobody has to lose an argument."),
  ("p", "The next post is the last day: what is owed when somebody leaves mid-year, why it is "
        "the number former employees check most carefully, and what the record has to contain "
        "for the answer to hold up."),
 ],
})

SPEC["parts"].append(
{
 "slug": "what-is-owed-on-the-last-day",
 "title": "What is owed on the last day, and how to be sure of it",
 "nav": "The last day",
 "read": 5, "words": 820,
 "desc": ("The leaving calculation: the final part-period, the carried hours, the rate a "
          "week's pay is worked out at, and the record that makes the number defensible."),
 "og": ("The leaving payment is the one payroll number a former employee will check line by "
        "line, months later, with nothing else to do."),
 "abstract": ("Settling an accrual balance on termination: closing the final period, valuing "
              "the hours at the reference-period rate, the limits on recovering overtaken "
              "leave, and the evidence pack."),
 "lede": ("Every other number this system produces is provisional. This one is final, it is "
          "paid, and it is checked by somebody who has just stopped being busy. It is worth "
          "getting the design right for this case alone."),
 "tags": ["final pay", "holiday pay", "termination", "payroll", "evidence", "serverless"],
 "takeaways": [
  "Accrue the final part-period. Leaving on the 9th still earns the hours worked to the 9th.",
  "Carried hours are owed too. They are accrued and untaken like any other.",
  "Overtaken leave can only be recovered if a written term says so.",
  "Value the hours on a 52-week average of weeks with pay, looking back up to 104.",
  "Attach the working. The number without it is an assertion.",
 ],
 "blocks": [
  ("h2", "The leaving calculation"),
  ("fig", ("chain", {
    "entry": {"title": "A leaving date", "sub": ["confirmed, with a", "final timesheet"], "icon": "clock"},
    "steps": [
      {"title": "Close the part-period", "sub": ["hours worked up to", "and including the last day"],
       "icon": "form"},
      {"title": "Sum the entitlement", "sub": ["this year's accrual", "plus carried hours"],
       "icon": "counter"},
      {"title": "Subtract what was taken", "sub": ["deducted lines only,", "not reservations"],
       "icon": "calendar",
       "exit": {"title": "Check the contract", "sub": ["recoverable only if a", "written term says so"],
                "icon": "doc", "label": "negative"}},
      {"title": "Value the hours", "sub": ["52-week average of", "weeks with pay"], "icon": "money"},
      {"title": "Pay and file", "sub": ["the payment, and", "the working behind it"], "icon": "shield"}],
    "note": "The third step is the only one that can go negative, and a negative balance is "
            "not automatically a debt. Most contracts are silent, and silence means it is not "
            "recoverable."}),
   "Five steps and one branch. The branch is the one businesses assume goes their way and "
   "usually does not.",
   "A leaving date turned into a final holiday payment",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled A "
   "leaving date, confirmed with a final timesheet. Close the part-period counts hours worked "
   "up to and including the last day. Sum the entitlement adds this year's accrual to carried "
   "hours. Subtract what was taken uses deducted lines only, not reservations, with a side exit "
   "reading negative: Check the contract, since overtaken leave is recoverable only if a "
   "written term says so. Value the hours uses a fifty-two week average of weeks with pay. Pay "
   "and file records the payment and the working behind it. A note says the third step is the "
   "only one that can go negative, that a negative balance is not automatically a debt, and "
   "that most contracts are silent, which means it is not recoverable."),
  ("h3", "The final part-period"),
  ("p", "Somebody who leaves on the ninth of the month has worked whatever they worked between "
        "the first and the ninth, and that accrues like any other hours. It is a small number "
        "and it is omitted constantly, because the accrual job runs on closed pay periods and "
        "the last period never closes normally."),
  ("p", "So the leaving event closes it early rather than skipping it. This matters more than "
        "the amount, because a leaver who spots that their final fortnight accrued nothing has "
        "a reason to check everything else, and everything else is four years long."),
  ("h2", "One leaver, one calculation"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Joined 12 Nov", "sub": ["so the leave year", "runs from then"], "icon": "person"},
      {"title": "1,417 hours", "sub": ["worked since the", "year opened"], "icon": "clock"},
      {"title": "171.0 accrued", "sub": ["at 12.07%,", "rounded up"], "icon": "counter"},
      {"title": "104 taken", "sub": ["five bookings, all", "deducted"], "icon": "calendar"},
      {"title": "67 hours paid", "sub": ["at GBP 12.94,", "about GBP 867"], "icon": "money"}],
    "title": "ONE LEAVER, FIVE NUMBERS AND WHERE EACH CAME FROM",
    "note": "Every box names its source. That is the difference between a payment and a "
            "payment somebody can check."}),
   "The whole leaving calculation as one line. None of the arithmetic is hard; all of it has "
   "to be attributable.",
   "A leaver's final holiday payment in five steps",
   "A horizontal row of five boxes joined by arrows. Joined on the twelfth of November, so the "
   "leave year runs from then. One thousand four hundred and seventeen hours worked since the "
   "year opened. One hundred and seventy-one hours accrued at twelve point zero seven per cent, "
   "rounded up. One hundred and four hours taken across five bookings, all deducted. Sixty-seven "
   "hours paid at twelve pounds ninety-four an hour, about eight hundred and sixty-seven "
   "pounds. A note says every box names its source, which is the difference between a payment "
   "and a payment somebody can check."),
  ("h3", "The rate is its own calculation"),
  ("p", "The hours are only half the answer. What they are worth is a week's pay, and for "
        "somebody whose pay varies that means an average over the last 52 weeks in which they "
        "were actually paid something, ignoring the weeks with no pay and looking back as far "
        "as 104 weeks to find 52 that count."),
  ("p", "Skipping the unpaid weeks is the part that gets missed, and it always goes the same "
        "way. A bank worker who did nothing for eleven weeks over the summer has those weeks "
        "excluded from the average, not counted as zeroes. Counting them as zeroes drags the "
        "rate down for exactly the workers whose pay is most variable."),
  ("p", "The four-week pot is valued at normal remuneration, which brings in regular overtime "
        "and commission, and the remainder at basic contractual pay. The system already knows "
        "which pot each remaining hour sits in, from part two, which is why that split was "
        "carried in the data rather than reconstructed here under time pressure."),
  ("callout", "The sentence the evidence has to be able to write", [
   "This worker's leave year opened on 12 November, under the statutory default.",
   "They worked 1,417 recorded hours in it, from 34 closed pay periods and one part-period.",
   "That accrued 171.0 hours at 12.07%, rounded up in each period.",
   "They took 104 hours across five bookings, on these dates.",
   "67 hours remained, valued at 12.94 an hour from a 52-week reference period.",
   "The payment of 866.98 was made in the final payroll run on this date.",
  ]),
  ("h2", "Where this ends"),
  ("p", "The system does not stop a business getting holiday wrong, because most of the ways "
        "of getting it wrong are decisions people make. What it removes is the category of "
        "error where nobody decided anything &mdash; the accrual that ran for four years while "
        "the only record of it was a spreadsheet column, the carried hours that were zeroed "
        "because zeroing was the default, the final fortnight that accrued nothing because the "
        "job only ran on closed periods."),
  ("p", "It also makes the honest answer the cheap one, which is the pattern worth copying out "
        "of this design more than any of the arithmetic. Sending every worker their balance "
        "each month is a small feature that happens to close the open-ended carry-over route "
        "in part four. The compliance outcome falls out of the operational one."),
  ("p", "The next post prices it and the one after gives the service names, the tables and the "
        "IAM. The interesting thing about the cost is that the expensive step runs once per "
        "contract rather than once per shift, so a business that doubles its rota does not "
        "double its bill."),
 ],
})

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="worker",
 volumes=[(25, "25 workers"), (120, "120 workers"), (400, "400 workers")],
 read_each=0.012,
 msgs_each=3.0,
 store_base=0.30,
 store_growth=0.0004,
 lede=("The model reads contracts, and a business hires far less often than it runs payroll. "
       "Everything that happens per shift, per period and per booking is arithmetic against a "
       "table. Here is where each cent goes."),
 takeaway_extra=("The bill tracks headcount, not hours. Doubling the rota does not move it."),
 risks=[
  "<strong>Re-reading every contract on every payroll run.</strong> A contract changes when "
  "somebody signs a new one. Extract once, store the terms, and re-read on a version change.",
  "<strong>Recomputing the whole history every night.</strong> The ledger is append-only "
  "precisely so that a balance is a sum over new lines, not a replay of four years.",
  "<strong>Keeping every timesheet import forever at full fidelity.</strong> Keep the derived "
  "ledger line, which is small and permanent, and expire the raw import once it has been "
  "reconciled.",
 ],
 per_unit_note=("Roughly one model call per employment contract, against a mid-tier model. A "
                "contract is long but the extraction is narrow: the leave year, the "
                "entitlement, the rate, and whether there is a written term about recovering "
                "overtaken leave. That is four fields and a quotation for each, which is not "
                "a job that improves with a frontier model."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="hol",
 lede=("The same system with the service names filled in: what reads a contract, what accrues "
       "a period, what moves a balance across a year end, and what settles a leaver."),
 outside=[
  {"title": "Timesheets", "sub": ["CSV or API, once", "a pay period"], "icon": "clock"},
  {"title": "Contracts", "sub": ["PDFs, on hire and", "on variation"], "icon": "doc"},
  {"title": "Leave requests", "sub": ["from whatever the", "business uses"], "icon": "calendar"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["imports and the", "period close"], "icon": "bucket"},
  {"title": "Lambda x5", "sub": ["contract, accrue, book,", "close, leaver"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["workers, ledger,", "bookings"], "icon": "database"}],
 note="eu-west-2. One account. Contracts are read on change; timesheets land each pay period; "
      "the year-end close is a scheduled job that writes carry-over lines and nothing else.",
 region="eu-west-2",
 region_why=("London, because this is employment data about UK workers and there is no reason "
             "for it to leave. Bedrock model availability is checked here rather than assumed; "
             "the contract read is the only step that would have to move if the model needed "
             "were not present, and it is the only step that is not arithmetic."),
 diagram_desc=(
  "Three boxes across the top sit outside the AWS account. Timesheets arriving as CSV or by "
  "API once a pay period. Contracts as PDFs, on hire and on variation. And Leave requests from "
  "whatever the business already uses. Each connects to the AWS account container below. "
  "Inside are three components. S3 with EventBridge handling imports and the period close. "
  "Five Lambda functions covering contract, accrue, book, close and leaver. And three DynamoDB "
  "tables holding workers, the ledger and bookings. A note says eu-west-2, one account, "
  "contracts are read on change, timesheets land each pay period, and the year-end close is a "
  "scheduled job that writes carry-over lines and nothing else."),
 functions=[
  ["<code>hol-contract</code>", "S3 put, contracts prefix",
   "Reads leave year, entitlement, rate and any recovery term", "60s / 1024MB"],
  ["<code>hol-accrue</code>", "EventBridge, on pay period close",
   "Turns hours worked into one append-only ledger line per worker", "300s / 1024MB"],
  ["<code>hol-book</code>", "API Gateway, leave request events",
   "Reserves, releases and deducts against the pot expiring first", "30s / 512MB"],
  ["<code>hol-close</code>", "EventBridge, per leave year boundary",
   "Applies carry-over with a reason and a computed expiry", "300s / 2048MB"],
  ["<code>hol-leaver</code>", "Termination event",
   "Closes the part-period, values the balance, writes the evidence", "300s / 2048MB"],
 ],
 roles=[
  ["<code>hol-contract-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:UpdateItem</code>",
   "One model id; the contracts prefix; workers"],
  ["<code>hol-accrue-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "The timesheets prefix; workers read; ledger write, no update"],
  ["<code>hol-book-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>, <code>dynamodb:UpdateItem</code>",
   "ledger read and append; bookings read and write"],
  ["<code>hol-close-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "ledger read; ledger append. No delete on anything, ever"],
  ["<code>hol-leaver-role</code>",
   "<code>dynamodb:Query</code>, <code>s3:PutObject</code>, <code>ses:SendEmail</code>",
   "All three tables read; the evidence prefix write-once; one verified identity"],
 ],
 tables=[
  ("Table: workers",
   "PK   employer_id#worker_id S\n"
   "SK   'terms#' + effective  S   one item per contract version\n"
   "     leave_year_start      S   MM-DD, or the hire anniversary\n"
   "     leave_year_source     S   contract | policy | statutory_default\n"
   "     accrual_rate          N   0.1207 unless the contract is better\n"
   "     pot_split             M   {four_week, remainder, contractual}\n"
   "     recovery_term         BOOL a written term allowing deduction on leaving\n"
   "     evidence_key          S   the contract itself, not a summary\n\n"
   "leave_year_source is stored because the statutory default is per-worker\n"
   "and the other two are per-business. A system that only stores the date\n"
   "cannot tell you which of its 46 year ends it invented."),
  ("Table: ledger",
   "PK   employer_id#worker_id S\n"
   "SK   period_end#seq        S   append-only; seq disambiguates corrections\n"
   "     kind                  S   accrual | deduction | carry_in | carry_out |\n"
   "                               adjustment | payout\n"
   "     hours                 N   signed\n"
   "     pot                   S   four_week | remainder | contractual\n"
   "     leave_year            S   the window this line belongs to\n"
   "     expires_on            S   set on carry_in lines only\n"
   "     reason                S   sickness | family_leave | employer_failure |\n"
   "                               agreement | leave_year_moved\n"
   "     inputs                M   hours worked, rate, rounding, source file\n\n"
   "Nothing in this table is ever updated or deleted. A correction is an\n"
   "adjustment line carrying the same period_end and a later seq, so the\n"
   "balance as at any past date is still recoverable."),
  ("Table: bookings",
   "PK   employer_id#worker_id S\n"
   "SK   booking_id            S\n"
   "     from_date             S\n"
   "     to_date               S\n"
   "     hours                 N\n"
   "     state                 S   requested | reserved | taken | cancelled\n"
   "     deducted_seq          S   the ledger line, set when state becomes taken\n\n"
   "state and deducted_seq together are the invariant: a booking in state\n"
   "taken must name a ledger line, and a ledger deduction must name a\n"
   "booking. A nightly check that both directions hold is four lines of\n"
   "code and catches every partial write this system can produce."),
  ],
 inbound=[
  "<strong>Timesheets are parsed, not read by a model.</strong> They are the largest files "
  "here and they are fixed-header exports from payroll or a rota tool. A model would be slower "
  "and would occasionally invent an hour.",
  "<strong>Contracts are read once per version.</strong> A variation is a new item under the "
  "same worker, never an edit, so a balance calculated last March still knows which terms "
  "applied then.",
  "<strong>Leave requests arrive over an API</strong> and the reservation is a conditional "
  "write. Two managers approving the same week is a condition failure rather than a lock.",
  "<strong>Balances go out monthly by SES</strong>, to every worker, with what expires and "
  "when. This is the operational feature that closes the employer-failure carry-over route."],
 model_notes=[
  "<strong>One call per contract version.</strong> Nothing per shift, per period, per booking "
  "or per balance query. All of those are arithmetic.",
  "<strong>A mid-tier model.</strong> The extraction is four fields and a quotation for each, "
  "out of a long document. Length is not the same as difficulty.",
  "<strong>Every extracted term comes back with the clause it came from</strong>, verbatim and "
  "with a page reference, because a disputed balance is settled by reading the clause rather "
  "than by trusting the field.",
  "<strong>Absent means null, never a default.</strong> A contract that says nothing about "
  "recovering overtaken leave must produce null, not false and certainly not true. Null is the "
  "answer that stops the leaver job making a deduction.",
  "<strong>No model touches accrual, deduction, carry-over or the payout.</strong> Every one "
  "of them has to be re-runnable years later and explainable to somebody who disagrees with "
  "the result."],
 gotchas=[
  "Accrue on hours paid, from the same source payroll used. It is the only external check this "
  "system has, and it stops being a check the moment the two read different files.",
  "Keep protected absence accruing. A worker on maternity leave or long-term sick works zero "
  "hours and accrues at the 52-week average, and omitting that is the largest single "
  "underpayment this design can produce.",
  "Round accrual up, in every period, per worker. A rounding rule that favours the employer is "
  "indefensible exactly because it is consistent.",
  "Store the pot each hour sits in. Four weeks are valued at normal remuneration and the rest "
  "at basic pay, and reconstructing the split at termination means reading two years of "
  "payslips under time pressure.",
  "Compute carry-over expiry at the time of carrying and store the date. Recomputing it later "
  "against whatever the rules say then is how a balance silently changes.",
  "Send the balance out monthly. It is a small feature that converts an open-ended liability "
  "into one that expires on schedule.",
 ],
))
