"""Day 138 -- 2026-09-09 -- Late payment interest claimer."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "late-payment-interest-claimer"
NAME = "Late payment interest claimer"

SPEC = {
 "slug": SLUG, "date": "2026-09-09", "name": NAME,
 "tagline": ("Works out the day each commercial invoice actually became late, the interest "
             "rate that was fixed on it at that moment, and the fixed sum owed on top -- then "
             "keeps the whole calculation in a shape you can put in front of the customer, or "
             "quietly never send."),
 "lede": ("A small system for any business that invoices other businesses: the due date "
          "established from the terms rather than assumed, the statutory rate pinned to the "
          "reference date it was fixed on, interest accrued daily, and the fixed compensation "
          "that is usually worth more than the interest. Seven posts on the same system, one "
          "diagram at a time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["late payment", "statutory interest", "commercial debt", "cash flow",
              "credit control", "serverless"],
 "icons": ["money", "clock", "chart"],
 "faq": [
  ("Can I really charge interest without agreeing it first?",
   "For business-to-business debts, yes. Where the contract is silent, a statutory right "
   "applies and it does not need the customer's agreement. Where the contract does provide a "
   "remedy, that one applies instead, as long as it is a substantial one."),
  ("What is the rate?",
   "Base rate plus eight per cent. The part people get wrong is which base rate: it is the one "
   "in force on the reference date at the start of the six-month period in which the debt "
   "became late, and it is then fixed for the whole life of that debt."),
  ("What is the fixed sum?",
   "A flat amount per late invoice, on a three-band scale by invoice size, on top of the "
   "interest. On small invoices it is usually worth several times the interest, which is why "
   "it is the line most often left on the table."),
  ("Can I claim on invoices that have already been paid?",
   "Yes. The entitlement arose when the invoice became late and it does not disappear when the "
   "principal is settled. It is an ordinary contract debt with the usual six-year window."),
  ("What does it cost to run?",
   "A few dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "late-payment-interest-claimer-on-aws",
 "title": "A late payment interest claimer on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Due dates established, the rate pinned to its reference date, interest accrued "
          "daily and the fixed sum added. AWS, about $4 a month."),
 "og": ("412 invoices paid late, 35,680 pounds of entitlement, and not one line of it on any "
        "ledger. The interest was the smaller half."),
 "abstract": ("The whole system on one page -- due dates, the rate, interest, the fixed sum "
              "and what you do with the number -- and why the largest part of the entitlement "
              "sits on invoices that have already been paid."),
 "lede": ("A fabrication workshop with eleven staff spent an afternoon working out what it was "
          "owed for being paid late over one financial year. The interest came to nine "
          "thousand pounds, which was more than expected. The fixed compensation came to "
          "twenty-six thousand, which nobody in the room had heard of."),
 "tags": ["late payment", "statutory interest", "credit control", "cash flow", "B2B",
          "serverless"],
 "takeaways": [
  "A debt becomes late on a date the contract decides, or on a statutory default if it is silent.",
  "The rate is fixed once, at the reference date, and does not move afterwards.",
  "There is a fixed sum per late invoice on top of the interest, and on small invoices it dominates.",
  "The entitlement survives payment of the principal, for six years.",
  "Designed on AWS for about $4 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Invoices", "sub": ["raised, and what", "each one was for"], "icon": "doc"},
      {"title": "Payments", "sub": ["when the money", "actually arrived"], "icon": "money"},
      {"title": "Terms and rates", "sub": ["what was agreed,", "and the base rate"], "icon": "key"}],
    "inside": [
      {"title": "Due date", "sub": ["established, with", "the reason"], "icon": "calendar"},
      {"title": "The clock", "sub": ["days late, at a", "fixed rate"], "icon": "clock"},
      {"title": "Entitlement", "sub": ["interest, fixed sum,", "costs"], "icon": "chart"}],
    "edges": [{"from": 0, "to": 0, "label": "as they are raised"},
              {"from": 1, "to": 1, "label": "as they clear"},
              {"from": 2, "to": 2, "label": "twice a year", "up": True}],
    "note": "The middle box is the whole job. Both sides of it already exist in the accounting "
            "system; what is missing is the date arithmetic between them."}),
   "Three things outside the account, three pieces inside it. Everything hard is in the first "
   "box, and everything valuable is in the third.",
   "System: invoices, payments and terms joined into an entitlement",
   "Three boxes across the top sit outside the AWS account. On the left, Invoices as raised and "
   "what each one was for. In the middle, Payments and when the money actually arrived. On the "
   "right, Terms and rates: what was agreed, and the base rate. Each connects by an arrow to "
   "the AWS account container below, labelled as they are raised, as they clear, and twice a "
   "year. Inside the AWS account are three components in a row. Due date, established with the "
   "reason. The clock, counting days late at a fixed rate. And Entitlement, covering interest, "
   "the fixed sum and costs. A note says the middle box is the whole job, because both sides of "
   "it already exist in the accounting system and what is missing is the date arithmetic "
   "between them."),
  ("h3", "Why nobody claims it"),
  ("p", "Not because they do not want the money. Because the calculation is fiddly in a way "
        "that resists being done once: every invoice has its own due date, its own rate fixed "
        "on its own reference date, its own number of days late and its own compensation band. "
        "Doing that for one invoice takes ten minutes. Doing it for four hundred and twelve is "
        "a project nobody authorises."),
  ("p", "So the entitlement accrues and nothing records it, and by the time somebody thinks "
        "about it the invoices have been paid, the relationship has moved on and the whole "
        "thing feels like ancient history. It is not ancient history. It is an ordinary debt "
        "with six years on the clock, and the arithmetic that felt impossible by hand is a "
        "loop."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The due date.</strong> When this particular invoice actually became late, "
   "established from the terms rather than assumed to be thirty days. Part 2.",
   "<strong>The rate.</strong> Base rate plus eight, pinned to the reference date it was fixed "
   "on, and never moved afterwards. Part 3.",
   "<strong>The entitlement.</strong> Daily interest, the fixed sum for the band, and "
   "reasonable recovery costs above it. Part 4.",
   "<strong>What you do with it.</strong> Which of these numbers is a letter, which is a "
   "negotiating position, and which is a note to self. Part 5.",
  ]),
  ("h2", "One workshop, one financial year"),
  ("fig", ("strip", {
    "stages": [
      {"title": "1,180 invoices", "sub": ["raised in one", "financial year"], "icon": "doc"},
      {"title": "412 paid late", "sub": ["by 23 days on", "average"], "icon": "clock"},
      {"title": "GBP 9,060", "sub": ["statutory interest", "at base plus 8%"], "icon": "chart"},
      {"title": "GBP 26,620", "sub": ["fixed compensation,", "one sum per invoice"], "icon": "money"},
      {"title": "GBP 35,680", "sub": ["entitlement, none of", "it ever claimed"], "icon": "alarm"}],
    "title": "ONE ELEVEN-PERSON WORKSHOP, ONE YEAR",
    "note": "The surprise is the fourth box. On invoices of a few thousand pounds the fixed sum "
            "is worth about three times the interest, and it is the line nobody has heard of."}),
   "The same year as one line. Two of these numbers are widely known and the third is worth "
   "more than both.",
   "One business's year from invoices raised to entitlement never claimed",
   "A horizontal row of five boxes joined by arrows. One thousand one hundred and eighty "
   "invoices raised in one financial year. Four hundred and twelve paid late, by twenty-three "
   "days on average. Nine thousand and sixty pounds of statutory interest at base rate plus "
   "eight per cent. Twenty-six thousand six hundred and twenty pounds of fixed compensation, "
   "one sum per invoice. And thirty-five thousand six hundred and eighty pounds of entitlement, "
   "none of it ever claimed. A note says the surprise is the fourth box, because on invoices of "
   "a few thousand pounds the fixed sum is worth about three times the interest and it is the "
   "line nobody has heard of."),
  ("h2", "In plain words"),
  ("p", "Invoices come in from the accounting system as they are raised, each with a customer, "
        "an amount, a date and whatever payment terms were attached to it. The first job is to "
        "turn that into a due date that can be defended, which is less obvious than it sounds "
        "and is the whole of part two."),
  ("p", "Payments come in as they clear. An invoice with a payment on or before its due date "
        "leaves the system immediately and is never thought about again. An invoice without one "
        "starts a clock, and that clock keeps running whether or not anybody looks at it."),
  ("p", "The rate is pinned at the moment the clock starts. This is the detail that most "
        "spreadsheet attempts get wrong, because it feels natural to apply today's rate to "
        "everything, and the actual rule fixes a rate for a whole six-month reference period "
        "and then leaves it alone for the life of the debt. Part three is entirely about that."),
  ("p", "Then the entitlement is three lines rather than one: interest accruing daily, a fixed "
        "sum determined by the size of the invoice, and any reasonable costs of recovery above "
        "that fixed sum. They are three separate rights with three separate rules and adding "
        "them up is the easy part."),
  ("callout", "Design rules that shaped every decision", [
   "Every due date records how it was derived, not just what it is.",
   "The rate is written onto the debt when it becomes late, and never recomputed.",
   "Interest accrues daily and is stored as a daily amount, not a running total.",
   "Payment of the principal closes the invoice and does not close the entitlement.",
   "Nothing is ever sent automatically. The system calculates; a person decides.",
   "Every figure can name the invoice, the date and the rate it came from.",
  ]),
  ("h2", "What it does not do"),
  ("p", "It does not chase invoices. That is a different system with a different rhythm, and "
        "most businesses already have one. This runs behind it and records what the chasing "
        "was worth, which is a question credit control never gets asked."),
  ("p", "It does not send anything on its own either. The number this system produces is "
        "commercially loaded in a way that a dunning email is not: claiming it against a "
        "customer you want to keep is a decision, claiming it against one who has just gone "
        "quiet is a different decision, and no rules engine should be making either. Part five "
        "is about that, and the design follows from it."),
  ("p", "And it does not give legal advice. It implements a published set of rules, records "
        "which version it applied and shows its working, so that the number in front of you is "
        "one you can check rather than one you have to trust. When there is a contractual "
        "remedy that displaces the statutory one, the system says so and stops calculating "
        "rather than guessing."),
  ("p", "The next four posts walk through each piece: when an invoice actually became late, "
        "which rate was fixed on it and when, what the three components of the entitlement are, "
        "and what to do with a number you may well decide not to send. One diagram per post, a "
        "cost breakdown, and an engineering reference at the end."),
 ],
},
]

SPEC["parts"].append(
{
 "slug": "when-an-invoice-actually-becomes-late",
 "title": "When an invoice actually becomes late",
 "nav": "The due date",
 "read": 5, "words": 810,
 "desc": ("Three places a due date comes from, the statutory default and its two-sided test, "
          "and why thirty days from the invoice date is usually the wrong answer."),
 "og": ("Thirty days from the invoice date is the answer everybody uses and it is wrong in "
        "both directions -- sometimes by a week, sometimes by a month."),
 "abstract": ("Establishing a defensible due date for each invoice from the contract, the "
              "invoice terms or the statutory default, and recording which one applied."),
 "lede": ("Everything downstream is arithmetic on one date, so this is the only part of the "
          "system where being approximately right is worthless. An interest claim that starts "
          "from the wrong day is not a slightly wrong claim; it is a claim the customer gets "
          "to reject on a technicality."),
 "tags": ["late payment", "payment terms", "due date", "contracts", "credit control",
          "serverless"],
 "takeaways": [
  "An agreed date in the contract beats everything else, if there really is one.",
  "Terms printed on your own invoice are not automatically agreed terms.",
  "With nothing agreed, the default runs from the later of delivery and receipt of the invoice.",
  "Payment terms beyond 60 days are open to challenge as grossly unfair.",
  "Record which route produced the date, and the evidence behind it.",
 ],
 "blocks": [
  ("h2", "Three places a due date comes from"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "An agreed date", "sub": ["in a contract both", "sides signed"], "icon": "doc",
       "label": "strongest"},
      {"title": "Your invoice terms", "sub": ["printed, but were", "they ever agreed?"],
       "icon": "form", "label": "check"},
      {"title": "Nothing agreed", "sub": ["no contract, no", "accepted terms"], "icon": "search",
       "label": "statutory default"}],
    "target": {"title": "Due date", "sub": ["the day, and how", "it was derived"], "icon": "calendar",
               "then": {"title": "Late from", "sub": ["the next day, and", "the clock starts"],
                        "icon": "clock"}},
    "note": "The middle lane is where most businesses think they are and the right-hand lane "
            "is where most of them actually are, and the two produce different dates."}),
   "Three routes, one date. Which route you took is stored, because it is the first thing a "
   "customer's finance department will question.",
   "Three sources for a payment due date converging on one date",
   "Three boxes on the left feed one box on the right. An agreed date in a contract both sides "
   "signed, described as strongest. Your invoice terms, printed but not necessarily ever "
   "agreed, marked check. Nothing agreed, meaning no contract and no accepted terms, in which "
   "case the statutory default applies. All three converge on Due date, holding the day and how "
   "it was derived, which feeds a box labelled Late from: the next day, and the clock starts. A "
   "note says the middle lane is where most businesses think they are and the right-hand lane "
   "is where most of them actually are, and the two produce different dates."),
  ("h3", "Printed terms are not agreed terms"),
  ("p", "Almost every invoice in the country says something like <em>payment due within 30 "
        "days</em> along the bottom. That line is a statement of what the supplier would like. "
        "It becomes a term of the contract if the customer agreed to it &mdash; in a signed "
        "agreement, in an accepted quotation, in a purchase order that incorporates it &mdash; "
        "and not otherwise."),
  ("p", "This is not a reason to panic, because the statutory default is usually similar and "
        "occasionally better. It is a reason to store which one you are relying on. A business "
        "that claims interest from day 31 on the basis of its own footer, against a customer "
        "who never accepted the footer, has picked the weakest of the three available "
        "arguments for no reason."),
  ("h2", "The default has two sides"),
  ("fig", ("chain", {
    "entry": {"title": "No agreed date", "sub": ["nothing signed,", "nothing accepted"], "icon": "search"},
    "steps": [
      {"title": "Date of performance", "sub": ["goods delivered or", "service completed"],
       "icon": "truck"},
      {"title": "Date of notice", "sub": ["the day they received", "the invoice"], "icon": "inbox",
       "exit": {"title": "Find it", "sub": ["a send log, a portal", "receipt, a signature"],
                "icon": "alarm", "label": "unevidenced"}},
      {"title": "Take the later", "sub": ["of those two dates,", "not the earlier"], "icon": "branch"},
      {"title": "Add the days", "sub": ["30 unless a valid", "term says otherwise"], "icon": "calendar"},
      {"title": "Late from the next day", "sub": ["and the rate is", "fixed here"], "icon": "clock"}],
    "note": "Both dates are needed. An invoice sent before delivery does not start the clock, "
            "and delivery without an invoice does not start it either."}),
   "Five steps and one hold. The third step is where the intuitive answer and the correct "
   "answer diverge.",
   "The statutory default due date derived from delivery and notice",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled No "
   "agreed date, nothing signed and nothing accepted. Date of performance is when goods were "
   "delivered or the service completed. Date of notice is the day the customer received the "
   "invoice, with a side exit reading unevidenced: Find it, from a send log, a portal receipt or "
   "a signature. Take the later of those two dates, not the earlier. Add the days, thirty unless "
   "a valid term says otherwise. Late from the next day, and the rate is fixed here. A note says "
   "both dates are needed, because an invoice sent before delivery does not start the clock and "
   "delivery without an invoice does not start it either."),
  ("h3", "Why the later of the two"),
  ("p", "Because the customer cannot reasonably be expected to pay for something they have not "
        "received, and cannot reasonably be expected to pay an amount they have not been told. "
        "Both conditions have to be satisfied before the countdown makes sense, so the clock "
        "starts from whichever happened second."),
  ("p", "In practice this cuts both ways and businesses rarely notice either. An invoice raised "
        "on the first of the month for work finished on the twentieth is late from the "
        "twentieth plus thirty, not the first plus thirty, and the supplier has been "
        "under-claiming by nineteen days. An invoice emailed to an address nobody reads, "
        "chased in week six and acknowledged in week seven, has a notice date in week seven, "
        "and the supplier who claims from week five is over-claiming."),
  ("p", "Storing both dates separately is therefore not bookkeeping fussiness. It is the "
        "difference between a claim that survives being questioned and one that gets withdrawn "
        "in the first phone call."),
  ("callout", "What the due date record holds", [
   "<strong>The date.</strong> The last day payment could arrive without being late.",
   "<strong>Basis.</strong> agreed | invoice_terms | statutory_default.",
   "<strong>Performance date.</strong> When the goods or the work were actually delivered.",
   "<strong>Notice date.</strong> When the customer received the invoice, with evidence.",
   "<strong>Verification period.</strong> Any agreed window to check conformity, and its length.",
   "<strong>Challengeable.</strong> Set where the agreed terms run beyond 60 days.",
  ]),
  ("h2", "Two edges worth handling"),
  ("p", "The first is a verification or acceptance period: a term giving the customer time to "
        "check that what arrived conforms to what was ordered before the payment clock starts. "
        "These are legitimate and common in manufacturing, and they push the due date out. They "
        "are also capped, and an unusually long one is itself open to challenge, so the system "
        "stores the length rather than silently absorbing it into the due date."),
  ("p", "The second is long payment terms. Where terms extend well beyond sixty days there is "
        "a route to argue they are grossly unfair to the supplier and should not stand. Whether "
        "to run that argument against a customer worth a third of your turnover is emphatically "
        "not a decision for software, so the system flags the invoice and moves on. The flag is "
        "useful precisely because nobody currently counts how many of these there are."),
  ("p", "The next post is the rate. It is a single number, it applies to the whole life of a "
        "debt, and the date it was fixed on is not the date you would guess."),
 ],
})

SPEC["parts"].append(
{
 "slug": "the-rate-and-the-date-it-was-fixed",
 "title": "The rate, and the date it was fixed on",
 "nav": "The rate",
 "read": 5, "words": 800,
 "desc": ("Base rate plus eight, which base rate, why it is pinned at a reference date, and "
          "why one ledger can carry four different rates at once."),
 "og": ("The rate is not today's. It is the one in force at the reference date for the "
        "half-year in which the debt went late, and then it never moves again."),
 "abstract": ("How the statutory rate is determined and frozen: the two reference dates a "
              "year, the pinning rule, simple daily accrual, and when a contractual remedy "
              "displaces the statutory one."),
 "lede": ("This is the smallest rule in the system and the one most reliably got wrong, "
          "because the wrong answer is the intuitive one. Applying today's rate to an old debt "
          "feels obviously right and is obviously wrong the moment you write down why the "
          "rule exists."),
 "tags": ["statutory interest", "base rate", "late payment", "credit control", "arithmetic",
          "serverless"],
 "takeaways": [
  "The rate is base rate plus eight percentage points.",
  "The base rate is the one in force at the reference date, not today's.",
  "There are two reference dates a year and each governs the following six months.",
  "Once a debt is late, its rate is fixed for the life of the debt.",
  "A substantial contractual remedy displaces the statutory rate entirely.",
 ],
 "blocks": [
  ("h2", "How a rate gets pinned to a debt"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Reference date", "sub": ["31 December, or", "30 June"], "icon": "calendar"},
      {"title": "Base rate that day", "sub": ["whatever it was,", "recorded once"], "icon": "chart"},
      {"title": "Plus eight points", "sub": ["that is the rate for", "the half-year"], "icon": "counter"},
      {"title": "A debt goes late", "sub": ["inside that", "half-year"], "icon": "clock"},
      {"title": "Pinned", "sub": ["that rate, for the", "life of the debt"], "icon": "lock"}],
    "title": "TWO DATES A YEAR DECIDE EVERY RATE",
    "note": "A base rate change in March does not touch a debt that went late in February. It "
            "does not touch one that went late in April either."}),
   "Five boxes, and the last one is the rule people miss. The rate attaches to the debt, not "
   "to the calendar.",
   "How the statutory interest rate is fixed at a reference date and pinned to a debt",
   "A horizontal row of five boxes joined by arrows. Reference date, being the thirty-first of "
   "December or the thirtieth of June. Base rate that day, whatever it was, recorded once. Plus "
   "eight percentage points, which is the rate for the half-year. A debt goes late inside that "
   "half-year. Pinned: that rate applies for the life of the debt. A note says a base rate "
   "change in March does not touch a debt that went late in February, and does not touch one "
   "that went late in April either."),
  ("h3", "Why it works that way"),
  ("p", "Because a debt that is chased for three years across five base rate movements would "
        "otherwise need a rate schedule rather than a rate, and every claim would become a "
        "piecewise calculation that neither side could check. Fixing the rate at the start "
        "makes the entitlement a single multiplication that anybody can verify with a "
        "calculator."),
  ("p", "The cost of that simplicity is that the fixing happens twice a year rather than "
        "continuously, so the rate on a debt can be materially different from the rate on an "
        "otherwise identical debt that went late eight weeks later. That is not an anomaly to "
        "be smoothed over; it is the rule working, and the system stores the reference date "
        "alongside the rate so the difference explains itself."),
  ("h2", "The same invoice, three rates"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Pinned at 8.75%", "parts": [("int", 104)]},
      {"label": "Pinned at 12.25%", "parts": [("int", 145)]},
      {"label": "Pinned at 13.25%", "parts": [("int", 157)]}],
    "series": [("int", "Interest on one 4,800 invoice paid 90 days late", "#01A88D")],
    "unit": "GBP ",
    "note": "Same customer, same invoice, same ninety days. The only difference is which "
            "half-year the debt went late in."}),
   "One invoice, three possible rates, fifty per cent between the ends. This is why the "
   "reference date is stored on the debt rather than looked up when somebody asks.",
   "Interest on the same invoice at three different pinned statutory rates",
   "Three vertical bars showing the interest owed on a single four thousand eight hundred "
   "pound invoice paid ninety days late. Pinned at eight point seven five per cent, about one "
   "hundred and four pounds. Pinned at twelve point two five per cent, about one hundred and "
   "forty-five pounds. Pinned at thirteen point two five per cent, about one hundred and "
   "fifty-seven pounds. A note says it is the same customer, the same invoice and the same "
   "ninety days, and the only difference is which half-year the debt went late in."),
  ("h3", "One ledger, several rates"),
  ("p", "The immediate consequence is that a business chasing two years of late invoices holds "
        "four different rates at once, and there is no single number to put at the top of the "
        "statement. Spreadsheets deal with this by picking one, which is where most of the "
        "errors in hand-built claims come from."),
  ("p", "The system deals with it by writing the rate onto the debt at the moment it becomes "
        "late, as a stored number rather than a lookup. That makes the calculation stable "
        "&mdash; re-running the report next year produces the same figure &mdash; and it means "
        "a rate table that gains a new row every six months never rewrites history."),
  ("h2", "Simple, daily, and not compound"),
  ("p", "Statutory interest is simple interest. It does not compound, it does not capitalise "
        "at the year end, and there is no facility for adding it to the principal and charging "
        "interest on the total. Every attempt to make the number bigger this way makes the "
        "claim weaker."),
  ("p", "It accrues daily, so the natural stored form is a daily amount: principal multiplied "
        "by the pinned rate, divided by 365. Everything downstream &mdash; the balance today, "
        "the balance at settlement, the balance in a letter dated next Tuesday &mdash; is that "
        "daily amount multiplied by a number of days. Storing a running total instead means "
        "recomputing every open debt every night for no benefit."),
  ("callout", "What the rate record holds", [
   "<strong>Reference date.</strong> 31 December or 30 June, and which one applied.",
   "<strong>Base rate.</strong> The figure in force on that date, stored not looked up.",
   "<strong>Statutory rate.</strong> Base plus eight, computed once.",
   "<strong>Daily amount.</strong> Principal times rate over 365, to the penny.",
   "<strong>Contractual override.</strong> Set where the contract provides its own remedy.",
   "<strong>Currency.</strong> Because a debt in another currency is a different question.",
  ]),
  ("h2", "When the contract has its own remedy"),
  ("p", "If the contract sets out its own remedy for late payment, and that remedy is a "
        "substantial one rather than a token, it displaces the statutory right. A contract "
        "specifying four per cent over base is a real remedy and the calculation follows it. A "
        "contract specifying interest at half a per cent a year is not a remedy, it is an "
        "attempt to switch the statutory one off, and it does not succeed."),
  ("p", "Deciding which side of that line a particular clause falls on is a judgement, not a "
        "calculation, so the system does not make it. Where a contractual remedy exists it "
        "records the clause, flags the invoice for a human, and calculates both figures so "
        "that whoever makes the call can see what is at stake before making it."),
  ("p", "The next post adds the two components that sit alongside the interest, one of which "
        "is usually worth more than it."),
 ],
})

SPEC["parts"].append(
{
 "slug": "interest-compensation-and-costs",
 "title": "Interest, compensation and costs: three claims, not one",
 "nav": "The entitlement",
 "read": 5, "words": 810,
 "desc": ("The daily interest, the fixed sum per invoice, the recovery costs above it, and "
          "why the middle one is the largest on most small invoices."),
 "og": ("On an 800 pound invoice the fixed sum is worth 149 days of interest. On an 18,000 "
        "pound one it is worth 17. Nobody's spreadsheet models that."),
 "abstract": ("The three components of a late payment entitlement, how they scale differently "
              "with invoice size, and how part payments and credit notes change the "
              "arithmetic."),
 "lede": ("Interest is the part everybody knows about and, for a business that raises a lot of "
          "modestly sized invoices, it is the smallest of the three. The one worth the most is "
          "a flat figure per invoice that has nothing to do with how late the payment was."),
 "tags": ["late payment", "compensation", "recovery costs", "credit control", "B2B",
          "serverless"],
 "takeaways": [
  "Three separate entitlements: daily interest, a fixed sum, and costs above the fixed sum.",
  "The fixed sum is per invoice and banded by invoice size, not by lateness.",
  "On small invoices the fixed sum dominates and is claimed on day one.",
  "Recovery costs are claimable only to the extent they exceed the fixed sum.",
  "A part payment reduces the principal from that day, and interest follows it down.",
 ],
 "blocks": [
  ("h2", "One late invoice, three lines"),
  ("fig", ("chain", {
    "entry": {"title": "A late invoice", "sub": ["past its due date,", "with a pinned rate"], "icon": "doc"},
    "steps": [
      {"title": "Count the days", "sub": ["from late-from to", "paid, or to today"], "icon": "clock"},
      {"title": "Interest", "sub": ["daily amount times", "days late"], "icon": "chart"},
      {"title": "Fixed sum", "sub": ["one per invoice,", "banded by size"], "icon": "money"},
      {"title": "Recovery costs", "sub": ["only the part above", "the fixed sum"], "icon": "counter",
       "exit": {"title": "Usually nothing", "sub": ["internal chasing", "does not count"], "icon": "stop",
                "label": "none incurred"}},
      {"title": "Total", "sub": ["three lines, each", "shown separately"], "icon": "report"}],
    "note": "The three lines stay separate all the way to the letter. A customer will concede "
            "one and argue about another, and a single merged figure loses that."}),
   "Five steps and one common exit. Keeping the components apart is worth more than the "
   "arithmetic that joins them.",
   "A late invoice turned into three separate entitlements",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled A "
   "late invoice, past its due date with a pinned rate. Count the days runs from the late-from "
   "date to payment, or to today. Interest is the daily amount times the days late. Fixed sum "
   "is one per invoice, banded by size. Recovery costs cover only the part above the fixed sum, "
   "with a side exit reading none incurred: Usually nothing, because internal chasing does not "
   "count. Total shows three lines, each separately. A note says the three lines stay separate "
   "all the way to the letter, because a customer will concede one and argue about another, and "
   "a single merged figure loses that."),
  ("h3", "The fixed sum is not proportional to anything"),
  ("p", "It is a flat amount per late invoice, on a three-band scale by the size of the "
        "invoice: a smaller sum under a thousand pounds, a middle one up to just under ten "
        "thousand, a larger one at ten thousand and above. It does not scale with how late the "
        "payment was and it is not charged per week or per chase. One invoice, one sum, "
        "available the moment the invoice is late."),
  ("p", "Which means that for a business raising a lot of invoices of a few thousand pounds "
        "each, the entitlement is dominated by a number that has nothing to do with interest "
        "rates at all. It is also the part that is easiest to calculate and hardest to argue "
        "with, because there is no judgement in it: the invoice was either late or it was not, "
        "and it was either above or below a threshold."),
  ("h2", "How the two components scale"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "GBP 800 invoice", "parts": [("int", 8), ("fix", 40)]},
      {"label": "GBP 4,800 invoice", "parts": [("int", 48), ("fix", 70)]},
      {"label": "GBP 18,000 invoice", "parts": [("int", 181), ("fix", 100)]}],
    "series": [("int", "Interest, 30 days late at 12.25%", "#01A88D"),
               ("fix", "Fixed sum for the band", "#FF9900")],
    "unit": "GBP ",
    "note": "All three are thirty days late. The orange band barely moves; the teal one grows "
            "with the invoice and with every extra day."}),
   "Three invoice sizes, the same thirty days late. On the smallest the fixed sum is five "
   "times the interest; on the largest it is a third of it.",
   "Interest and fixed compensation on three invoice sizes at thirty days late",
   "Three vertical stacked bars, each showing the entitlement on an invoice thirty days late at "
   "twelve point two five per cent, split into interest in teal and the fixed sum for the band "
   "in orange. An eight hundred pound invoice yields about eight pounds of interest and forty "
   "pounds fixed, totalling forty-eight. A four thousand eight hundred pound invoice yields "
   "about forty-eight pounds of interest and seventy pounds fixed, totalling one hundred and "
   "eighteen. An eighteen thousand pound invoice yields about one hundred and eighty-one pounds "
   "of interest and one hundred pounds fixed, totalling two hundred and eighty-one. A note says "
   "all three are thirty days late, the orange band barely moves, and the teal one grows with "
   "the invoice and with every extra day."),
  ("h3", "The break-even, in days"),
  ("p", "The clearest way to hold this is to ask how many days of interest the fixed sum is "
        "worth. On an eight hundred pound invoice it is a hundred and forty-nine days. On a "
        "four thousand eight hundred pound invoice it is forty-four. On an eighteen thousand "
        "pound invoice it is seventeen."),
  ("p", "So for a small supplier chasing modest invoices that are usually a few weeks late, "
        "essentially the whole entitlement is the fixed sum, and the interest is a rounding "
        "error on top of it. That inverts the intuition the words carry &mdash; interest sounds "
        "like the main event and compensation sounds like a formality &mdash; and it changes "
        "which number is worth the effort of calculating carefully."),
  ("h2", "Costs above the fixed sum"),
  ("p", "The third component is the reasonable cost of recovering the debt, claimable to the "
        "extent it goes beyond the fixed sum rather than in addition to it. If a debt collection "
        "agency charged two hundred pounds and the fixed sum was seventy, the additional claim "
        "is a hundred and thirty."),
  ("p", "The thing suppliers most want to claim here &mdash; their own time spent chasing "
        "&mdash; is the thing least likely to succeed. It is internal, it is hard to evidence, "
        "and it is what the fixed sum is there to represent. The system therefore only counts "
        "costs that have an invoice behind them from somebody else, which is a narrow rule "
        "that keeps the claim clean."),
  ("callout", "The events that change an entitlement after it starts", [
   "<strong>Part payment.</strong> Principal drops from that date. The daily amount is "
   "recalculated and a new segment starts; earlier days keep the old figure.",
   "<strong>Credit note.</strong> Reduces the debt, sometimes from the original date. Interest "
   "on the credited part unwinds with it.",
   "<strong>Payment in full.</strong> Stops the interest clock. It does not stop the "
   "entitlement, which is now a separate debt.",
   "<strong>Dispute raised.</strong> Does not stop the clock by itself, but it is recorded, "
   "because it changes what you do next.",
   "<strong>Six years.</strong> The claim is time-limited from when the entitlement arose. The "
   "system tracks the expiry per invoice.",
  ]),
  ("h2", "Segments, not a single sum"),
  ("p", "Because part payments and credit notes change the principal mid-life, interest is "
        "stored as a series of segments rather than one figure: from this date to that date, "
        "this principal, this daily amount. The total is the sum of the segments and every "
        "segment names the event that ended the previous one."),
  ("p", "That is more structure than a spreadsheet would use and it is the reason the number "
        "survives contact with a customer's accounts payable team. When they say they paid "
        "half of it in April, the answer is already in the record rather than being a "
        "recalculation done under pressure with somebody on the phone."),
  ("p", "The next post is the part the arithmetic cannot answer: which of these numbers you "
        "actually send, to whom, and when."),
 ],
})

SPEC["parts"].append(
{
 "slug": "claiming-it-without-losing-the-customer",
 "title": "Claiming it, waiving it, or just knowing it",
 "nav": "What you do with it",
 "read": 5, "words": 820,
 "desc": ("The commercial decision the arithmetic cannot make: when to claim, when to waive "
          "visibly, and why most of the value is in never sending it at all."),
 "og": ("One customer, 74 late invoices, 7,570 pounds of entitlement. The right move was not "
        "to invoice it. It was to say the number out loud at the renewal."),
 "abstract": ("Deciding what to do with a calculated entitlement: the branch that ends in a "
              "demand, the branch that ends in a visible concession, and the one that ends in "
              "a pricing conversation."),
 "lede": ("Everything up to here was arithmetic with a defensible answer. This part has no "
          "defensible answer, which is exactly why the system stops at the number and hands "
          "it to a person."),
 "tags": ["late payment", "credit control", "customer relationships", "pricing", "evidence",
          "serverless"],
 "takeaways": [
  "Most entitlements should never be invoiced. Almost all of them should be known.",
  "A waiver shown on the statement is worth more than a claim nobody sends.",
  "A customer who has stopped trading is the one case where claiming costs nothing.",
  "The number belongs in the renewal conversation, not in the dunning sequence.",
  "Never automate the send. Automate the calculation and the evidence.",
 ],
 "blocks": [
  ("h2", "What happens to a calculated entitlement"),
  ("fig", ("chain", {
    "entry": {"title": "An entitlement", "sub": ["calculated, with", "its working"], "icon": "chart"},
    "steps": [
      {"title": "Still claimable?", "sub": ["within six years of", "when it arose"], "icon": "calendar",
       "exit": {"title": "Archive it", "sub": ["record the number,", "and stop"], "icon": "archive",
                "label": "expired"}},
      {"title": "Customer still trading?", "sub": ["or insolvent, or", "simply gone"], "icon": "search",
       "exit": {"title": "Claim it", "sub": ["there is no", "relationship to lose"], "icon": "money",
                "label": "gone"}},
      {"title": "Live dispute?", "sub": ["about the goods or", "the work itself"], "icon": "alarm",
       "exit": {"title": "Hold", "sub": ["settle the dispute", "before the interest"], "icon": "stop",
                "label": "yes"}},
      {"title": "Worth keeping?", "sub": ["usually yes, and", "that is fine"], "icon": "person",
       "exit": {"title": "Waive it visibly", "sub": ["shown, then", "credited to nil"], "icon": "check",
                "label": "yes"}},
      {"title": "Show it, do not charge it", "sub": ["accrued on the", "statement, uninvoiced"],
       "icon": "report"}],
    "note": "Exactly one branch ends in a demand, and it is the branch where the relationship "
            "has already ended. Everything else ends in a number somebody can see."}),
   "Five questions, four ways out. The default at the bottom is the one most businesses should "
   "be doing and almost none are.",
   "A calculated entitlement routed to a claim, a waiver, a hold or a statement line",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled An "
   "entitlement, calculated with its working. Still claimable checks it is within six years of "
   "when it arose, with a side exit reading expired: Archive it, record the number and stop. "
   "Customer still trading checks whether they are insolvent or simply gone, with a side exit "
   "reading gone: Claim it, since there is no relationship to lose. Live dispute checks for an "
   "argument about the goods or the work itself, with a side exit reading yes: Hold, settle the "
   "dispute before the interest. Worth keeping asks whether the customer is worth keeping, "
   "usually yes, with a side exit reading yes: Waive it visibly, shown and then credited to nil. "
   "The final step is Show it, do not charge it: accrued on the statement and uninvoiced. A note "
   "says exactly one branch ends in a demand, and it is the branch where the relationship has "
   "already ended."),
  ("h3", "The visible waiver"),
  ("p", "The strongest thing most businesses can do with this number is put it on the statement "
        "and then credit it to nil in the line underneath. <em>Late payment compensation "
        "accrued: 340.00. Waived as a gesture of goodwill: -340.00.</em> Nothing is charged, "
        "nothing is demanded, and the customer's finance team now knows a real figure that was "
        "previously invisible."),
  ("p", "This works because the awkwardness of the conversation was never really about the "
        "money. It was about being the supplier who sends a demand. A waiver is not a demand. "
        "It is a fact, presented, with a concession attached, and it costs you exactly nothing "
        "because you were never going to collect it anyway."),
  ("p", "It also gives you something real to trade at renewal, which the same number sitting in "
        "a spreadsheet does not. A supplier who has visibly waived four thousand pounds over "
        "two years is in a different negotiating position from one who has silently absorbed "
        "it."),
  ("h2", "What the number is actually for"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A price signal", "sub": ["this customer costs", "more to serve"], "icon": "tag"},
      {"title": "A terms review", "sub": ["30 days is not", "working here"], "icon": "doc"},
      {"title": "A credit limit", "sub": ["exposure measured,", "not guessed"], "icon": "shield"},
      {"title": "A concession", "sub": ["waived visibly, and", "tradeable"], "icon": "check"},
      {"title": "Occasionally, a claim", "sub": ["when there is nothing", "left to protect"], "icon": "money"}],
    "title": "FIVE USES, AND ONLY THE LAST ONE IS A DEMAND",
    "note": "A business that only ever uses the fifth has built a debt collection tool. The "
            "first four are where the money is."}),
   "The same number, five jobs. Four of them never involve contacting the customer about it at "
   "all.",
   "Five uses for a calculated late payment entitlement",
   "A horizontal row of five boxes joined by arrows. A price signal, meaning this customer "
   "costs more to serve. A terms review, since thirty days is not working here. A credit limit, "
   "with exposure measured rather than guessed. A concession, waived visibly and tradeable. And "
   "occasionally a claim, when there is nothing left to protect. A note says a business that "
   "only ever uses the fifth has built a debt collection tool, and the first four are where the "
   "money is."),
  ("h3", "Concentration is the useful finding"),
  ("p", "In the worked example the thirty-five thousand six hundred and eighty pounds was not "
        "spread evenly. Nine customers accounted for twenty-four thousand three hundred of it, "
        "and a single customer &mdash; seventy-four late invoices, thirty-one days late on "
        "average &mdash; accounted for seven thousand five hundred and seventy on their own."),
  ("p", "That customer was not a bad customer. They were a large one with a slow purchase "
        "ledger and a payment run on the twenty-eighth, and the workshop had been quoting them "
        "the same prices as everybody else for four years. The seven and a half thousand pounds "
        "was never going to be invoiced. It was worth knowing because it was, in effect, an "
        "unpriced financing service, and the next quotation could price it."),
  ("callout", "The sentence the evidence has to be able to write", [
   "Invoice 41,207 for 3,140.00 was for work completed on 4 March.",
   "The invoice was received by the customer on 6 March, per the send log.",
   "With no agreed terms, it became late on 6 April.",
   "The rate pinned at that date was 12.25%, being base plus eight at the 31 December "
   "reference date.",
   "It was paid on 9 May, 33 days late, accruing 34.79 of interest.",
   "A fixed sum of 70.00 applied, giving 104.79, which was shown and waived on the May "
   "statement.",
  ]),
  ("h2", "Where this ends"),
  ("p", "The system does not get anybody paid faster on its own. What it removes is the "
        "category of loss where nobody decided anything &mdash; the entitlement that accrued "
        "for six years and expired, the customer whose slowness was never priced, the fixed sum "
        "that nobody in the business had heard of."),
  ("p", "It also puts the decision where it belongs. Software is good at establishing that an "
        "invoice became late on the sixth of April at a rate of twelve and a quarter per cent, "
        "and extraordinarily bad at knowing whether the customer's finance director is about to "
        "put a much larger contract out to tender. Calculating is automated; sending is not, "
        "and no configuration flag makes it so."),
  ("p", "The next post prices it and the one after gives the service names, the tables and the "
        "IAM. The interesting thing about the cost is that the model reads agreements, which "
        "arrive a few times a year, while the arithmetic runs nightly for free."),
 ],
})

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="agreement",
 volumes=[(40, "40 customers"), (200, "200 customers"), (800, "800 customers")],
 read_each=0.014,
 msgs_each=3.0,
 store_base=0.28,
 store_growth=0.0003,
 lede=("The model reads agreements, and a business signs those a few times a year per "
       "customer at most. Everything that happens per invoice, per payment and per night is "
       "arithmetic against a table. Here is where each cent goes."),
 takeaway_extra=("The bill tracks customers, not invoices. Ten thousand invoices a month cost "
                 "the same as one hundred."),
 risks=[
  "<strong>Re-reading every agreement on every nightly run.</strong> Terms change when "
  "somebody signs something. Extract once per version and re-read on change.",
  "<strong>Recomputing every open debt every night.</strong> Store the daily amount and "
  "multiply by days. A nightly full recalculation over six years of history is the one way to "
  "make this expensive.",
  "<strong>Keeping every accounting export forever.</strong> Keep the derived debt record, "
  "which is small and has to last six years, and expire the raw exports once reconciled.",
 ],
 per_unit_note=("Roughly one model call per customer agreement version, against a mid-tier "
                "model. The extraction is narrow: the payment terms, any verification period, "
                "any contractual late payment remedy, and the clause each came from. Length is "
                "not difficulty, and a frontier model finds the same four clauses for several "
                "times the price."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="lpi",
 lede=("The same system with the service names filled in: what reads an agreement, what "
       "establishes a due date, what accrues interest nightly, and where the evidence sits."),
 outside=[
  {"title": "Ledger exports", "sub": ["invoices and payments,", "nightly"], "icon": "money"},
  {"title": "Agreements", "sub": ["contracts, POs,", "accepted quotes"], "icon": "doc"},
  {"title": "Base rates", "sub": ["two reference dates", "a year"], "icon": "chart"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["imports and the", "nightly accrual"], "icon": "bucket"},
  {"title": "Lambda x4", "sub": ["terms, due, accrue,", "pack"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["customers, debts,", "segments"], "icon": "database"}],
 note="eu-west-2. One account. Agreements are read on change; the ledger lands nightly; "
      "interest is a multiplication rather than a recalculation; nothing is ever sent to a "
      "customer without a person pressing something.",
 region="eu-west-2",
 region_why=("London, because this is UK commercial debt and the statutory scheme it "
             "implements is a UK one, so there is no case for the data being anywhere else. "
             "Bedrock model availability is checked here rather than assumed; the agreement "
             "read is the only step that would move, and it is the only step that is not "
             "arithmetic."),
 diagram_desc=(
  "Three boxes across the top sit outside the AWS account. Ledger exports carrying invoices and "
  "payments, nightly. Agreements as contracts, purchase orders and accepted quotes. And Base "
  "rates, at two reference dates a year. Each connects to the AWS account container below. "
  "Inside are three components. S3 with EventBridge handling imports and the nightly accrual. "
  "Four Lambda functions covering terms, due, accrue and pack. And three DynamoDB tables "
  "holding customers, debts and segments. A note says eu-west-2, one account, agreements are "
  "read on change, the ledger lands nightly, interest is a multiplication rather than a "
  "recalculation, and nothing is ever sent to a customer without a person pressing something."),
 functions=[
  ["<code>lpi-terms</code>", "S3 put, agreements prefix",
   "Reads payment terms, verification period and any contractual remedy", "60s / 1024MB"],
  ["<code>lpi-due</code>", "Nightly, after the ledger import",
   "Establishes a due date per invoice and records which basis produced it", "180s / 1024MB"],
  ["<code>lpi-accrue</code>", "Nightly, after lpi-due",
   "Opens, closes and splits interest segments on payments and credits", "300s / 1024MB"],
  ["<code>lpi-pack</code>", "On request, per customer",
   "Assembles the working, the three lines and the evidence into one object", "300s / 2048MB"],
 ],
 roles=[
  ["<code>lpi-terms-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "One model id; the agreements prefix; customers"],
  ["<code>lpi-due-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>",
   "The ledger prefix; customers read; debts write"],
  ["<code>lpi-accrue-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "debts read; segments append. No update, no delete"],
  ["<code>lpi-pack-role</code>",
   "<code>dynamodb:Query</code>, <code>s3:PutObject</code>, <code>ses:SendEmail</code>",
   "All three tables read; the evidence prefix write-once; one verified identity, internal "
   "recipients only"],
 ],
 tables=[
  ("Table: customers",
   "PK   org_id#customer_id   S\n"
   "SK   'terms#' + effective S   one item per agreement version\n"
   "     basis                S   agreed | invoice_terms | statutory_default\n"
   "     days                 N   the agreed period, null on the default\n"
   "     verification_days    N   an acceptance window, if there is one\n"
   "     contract_remedy      M   {rate, clause, substantial: BOOL|null}\n"
   "     challengeable        BOOL set where the agreed period exceeds 60 days\n"
   "     evidence_key         S   the agreement, and the page the clause is on\n\n"
   "contract_remedy.substantial is deliberately three-valued. A clause that\n"
   "exists is not the same as a clause that displaces the statutory right,\n"
   "and null means a human has not yet decided. The accrual job treats null\n"
   "as 'calculate both and flag', never as 'assume statutory'."),
  ("Table: debts",
   "PK   org_id#customer_id   S\n"
   "SK   invoice_id           S\n"
   "     performance_date     S   delivered or completed\n"
   "     notice_date          S   when they received the invoice\n"
   "     notice_evidence      S   send log id, portal receipt, signature\n"
   "     due_date             S\n"
   "     due_basis            S   which of the three routes produced it\n"
   "     late_from            S   the day after due_date\n"
   "     reference_date       S   31-12 or 30-06, whichever governed\n"
   "     base_rate            N   the figure on that date, stored not looked up\n"
   "     statutory_rate       N   base_rate + 8\n"
   "     fixed_sum            N   banded by the original invoice amount\n"
   "     recovery_costs       N   only what exceeds fixed_sum, with an invoice\n"
   "     claim_expires_on     S   six years from when the entitlement arose\n"
   "     disposition          S   open | shown | waived | claimed | archived\n\n"
   "base_rate is stored rather than joined to a rate table. A stored rate\n"
   "makes last year's report reproducible; a join makes it change quietly\n"
   "the next time the table gains a row."),
  ("Table: segments",
   "PK   org_id#customer_id#invoice_id S\n"
   "SK   from_date                     S   append-only\n"
   "     to_date                       S   null while the segment is open\n"
   "     principal                     N   the balance during this segment\n"
   "     daily_amount                  N   principal * rate / 365, to the penny\n"
   "     ended_by                      S   part_payment | credit_note | paid |\n"
   "                                       still_open\n"
   "     event_ref                     S   the ledger line that ended it\n\n"
   "Interest is the sum of segments, never a stored running total. A part\n"
   "payment closes one segment and opens another, so the arithmetic for any\n"
   "past date stays correct without a recalculation, and 'you paid half in\n"
   "April' is answered from the record rather than from a spreadsheet."),
  ],
 inbound=[
  "<strong>Ledger exports are parsed, not read by a model.</strong> They are fixed-header CSV "
  "from the accounting system, they are the largest files here, and a model would occasionally "
  "invent a payment date.",
  "<strong>Agreements are read once per version.</strong> A new contract is a new item under "
  "the same customer, never an edit, so a due date established last year still knows which "
  "terms produced it.",
  "<strong>Base rates are entered twice a year and stored on the debt.</strong> Two rows a "
  "year is not a data feed. Someone types it, someone else checks it, and every debt that goes "
  "late afterwards copies it.",
  "<strong>Nothing leaves the account addressed to a customer.</strong> SES sends internal "
  "packs to internal recipients. The letter, if there ever is one, is written by a person in "
  "whatever they already use."],
 model_notes=[
  "<strong>One call per agreement version.</strong> Nothing per invoice, per payment, per "
  "night or per pack. All of those are arithmetic.",
  "<strong>A mid-tier model.</strong> Four clauses out of a long document is an extraction "
  "task, not a reasoning one.",
  "<strong>Every term comes back with its clause, verbatim.</strong> A due date that is "
  "questioned is settled by reading the clause, and a field without a quotation cannot do "
  "that.",
  "<strong>Absent means null.</strong> No payment term found must produce null, which routes "
  "the invoice to the statutory default. A model that helpfully answers 'probably 30 days' has "
  "produced the same number by a route that cannot be defended.",
  "<strong>No model touches the rate, the interest, the fixed sum or the dates.</strong> Every "
  "one of them has to reproduce exactly, years later, in front of somebody who disagrees."],
 gotchas=[
  "Store the notice date and the performance date separately. The default due date runs from "
  "the later of the two, and a system holding only the invoice date cannot compute it in "
  "either direction.",
  "Pin the rate when the debt goes late and store it. Looking it up at report time means last "
  "year's figures change the next time the rate table gains a row.",
  "Do not compound. Statutory interest is simple, and adding it to the principal weakens the "
  "claim for the sake of a few pounds.",
  "The fixed sum is per invoice, once, and banded by the invoice amount. Charging it per chase "
  "or per month is the fastest way to have the whole claim dismissed.",
  "Claim recovery costs only above the fixed sum, and only where a third party invoiced you. "
  "Internal chasing time is what the fixed sum represents.",
  "Track the six-year expiry per invoice, and archive rather than delete when it passes. An "
  "entitlement that quietly disappears from the report is indistinguishable from one that was "
  "never calculated.",
 ],
))
