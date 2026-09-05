"""Day 134 -- 2026-09-05 -- Card fee auditor."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "card-fee-auditor"
NAME = "Card fee auditor"

SPEC = {
 "slug": SLUG, "date": "2026-09-05", "name": NAME,
 "tagline": ("Works out what you actually pay to take a card payment, finds the transactions that "
             "cost four times what they should have, separates the fees your provider controls "
             "from the ones they do not, and gives you the two numbers you need before anybody "
             "quotes you a better rate."),
 "lede": ("A small system for anybody who takes card payments: a monthly statement read into "
          "individual fees, an effective rate computed per transaction rather than quoted, the "
          "downgraded transactions identified by why they downgraded, and a comparison that "
          "survives contact with a salesperson. Seven posts on the same system, one diagram at a "
          "time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["card fees", "merchant services", "interchange", "payment processing",
              "effective rate", "serverless"],
 "icons": ["money", "chart", "doc"],
 "faq": [
  ("What is an effective rate?",
   "Total fees divided by total card turnover, as a percentage. It is the only number that "
   "compares two providers honestly, and it is never the number on the front of the quote."),
  ("Why is my effective rate higher than the rate I was quoted?",
   "Because the quoted rate covers one card type presented one way. Corporate cards, overseas "
   "cards and keyed-in transactions all cost more, and the quote is the floor rather than the "
   "average."),
  ("What is a downgrade?",
   "A transaction that failed to qualify for the rate you expected and was charged at a higher "
   "one -- usually because data was missing, the card was corporate, or authorisation and "
   "settlement did not match."),
  ("Can I actually reduce these fees?",
   "Some of them. Interchange is set by the card schemes and no provider can discount it. The "
   "acquirer margin is negotiable, and the downgrades are usually fixable at the terminal."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "card-fee-auditor-on-aws",
 "title": "A card fee auditor on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Statements read into individual fees, an effective rate per transaction, downgrades "
          "explained, and a comparison that holds. AWS, about $2 a month."),
 "og": ("You were quoted 1.4%. You are paying 2.31%. Both numbers are true, and only one of them "
        "appears anywhere in your accounts."),
 "abstract": ("The whole system on one page -- the statement, the transactions, the effective rate "
              "and the downgrades -- and why the rate you were quoted was never going to be the "
              "rate you pay."),
 "lede": ("The merchant services bill is about nine hundred pounds a month. It arrives as a "
          "fourteen-page PDF with roughly forty distinct fee types on it. It is coded to one "
          "nominal ledger line and approved by somebody who has never read past page two. "
          "Nobody in the business can tell you what percentage of turnover it represents."),
 "tags": ["card fees", "merchant services", "payments", "cost control", "interchange",
          "serverless"],
 "takeaways": [
  "The effective rate is total fees over total turnover. Compute it, never quote it.",
  "Interchange is not negotiable. The acquirer margin is. Separate them.",
  "Downgrades have causes, and most causes are fixable at the terminal.",
  "A blended quote hides which transactions are expensive. IC++ shows you.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "The statement", "sub": ["monthly, fourteen", "pages, unread"], "icon": "doc"},
      {"title": "The transactions", "sub": ["from the till or", "the gateway"], "icon": "cart"},
      {"title": "The contract", "sub": ["a rate, and what", "it applies to"], "icon": "key"}],
    "inside": [
      {"title": "Fees, itemised", "sub": ["forty types, each", "with a basis"], "icon": "money"},
      {"title": "Rate per sale", "sub": ["cost joined to", "the transaction"], "icon": "chart"},
      {"title": "The three answers", "sub": ["effective rate, margin,", "downgrades"], "icon": "target"}],
    "edges": [{"from": 0, "to": 0, "label": "monthly"},
              {"from": 1, "to": 1, "label": "daily"},
              {"from": 2, "to": 2, "label": "once", "up": True}],
    "note": "The statement says what you were charged. The transactions say what you sold. Almost "
            "nobody joins the two, and the join is the entire system."}),
   "Three things outside the account, three pieces inside it. The information all exists; it has "
   "never been put in the same place.",
   "System: statement, transactions and contract joined into an effective rate",
   "Three boxes across the top sit outside the AWS account. On the left, The statement, monthly, "
   "fourteen pages, unread. In the middle, The transactions, from the till or the gateway. On the "
   "right, The contract, a rate and what it applies to. Each connects by an arrow to the AWS "
   "account container below, monthly, daily and once respectively. Inside the AWS account are "
   "three components in a row. On the left, Fees itemised: forty types, each with a basis. In the "
   "middle, Rate per sale: cost joined to the transaction. On the right, The three answers: "
   "effective rate, margin and downgrades. A note says the statement says what you were charged "
   "and the transactions say what you sold, almost nobody joins the two, and the join is the "
   "entire system."),
  ("h3", "Why nobody notices"),
  ("p", "A card fee is never large enough to query on its own. Eleven pence on a nine pound sale "
        "is beneath anybody's threshold for an argument, and the aggregate of those elevenpences "
        "is the second or third largest controllable cost in a lot of retail businesses."),
  ("p", "The statement is also genuinely hard to read, and not by accident. Fees appear as "
        "abbreviations, some are per transaction and some are percentages, some are charged "
        "monthly and some annually, and the total at the bottom reconciles to the bank without "
        "explaining itself. Reading it takes an afternoon, so it happens once, at the point of "
        "switching, and then never again."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Fees, itemised.</strong> The statement broken into individual fees, each with what it "
   "was charged on. Part 2.",
   "<strong>Rate per sale.</strong> Fees joined to the transactions that caused them, which is "
   "what makes an average meaningful. Part 3.",
   "<strong>The three answers.</strong> The effective rate, the part of it your provider "
   "controls, and the transactions that cost more than they should. Parts 4 and 5.",
  ]),
  ("h2", "One month, one account"),
  ("fig", ("strip", {
    "stages": [
      {"title": "£38,900 taken", "sub": ["2,140 card", "transactions"], "icon": "cart"},
      {"title": "£899 in fees", "sub": ["41 distinct fee", "types"], "icon": "money"},
      {"title": "2.31% effective", "sub": ["against 1.4%", "quoted"], "icon": "chart"},
      {"title": "0.79% is margin", "sub": ["the negotiable", "part"], "icon": "target"},
      {"title": "116 downgrades", "sub": ["£71, mostly", "keyed-in"], "icon": "alarm"}],
    "title": "ONE MONTH, ONE MERCHANT ACCOUNT",
    "note": "The third box is the number nobody has. The fourth and fifth are the only two you "
            "can do anything about."}),
   "The same system as one line. The effective rate is the diagnosis; the margin and the "
   "downgrades are the two things that respond to action.",
   "One merchant account over one month, from turnover to downgrades",
   "A horizontal row of five boxes joined by arrows. Thirty-eight thousand nine hundred pounds "
   "taken across two thousand one hundred and forty card transactions. Eight hundred and "
   "ninety-nine pounds in fees across forty-one distinct fee types. An effective rate of 2.31 "
   "percent against 1.4 percent quoted. Of that, 0.79 percent is acquirer margin, the negotiable "
   "part. And one hundred and sixteen downgraded transactions costing seventy-one pounds, mostly "
   "keyed-in. A note says the third box is the number nobody has, and the fourth and fifth are "
   "the only two you can do anything about."),
  ("h2", "In plain words"),
  ("p", "The contract is read once into a quoted rate and, crucially, a description of what that "
        "rate applies to. Almost every quote in this industry is a floor rather than an average: "
        "it is the price of a UK consumer debit card, inserted into a terminal, with the "
        "cardholder present. Every departure from that costs more."),
  ("p", "Each month the statement is read into individual fees. There are usually between thirty "
        "and fifty, and each one is tagged with what it was charged on -- a count of "
        "transactions, a percentage of value, or a flat monthly amount -- and with which of three "
        "categories it belongs to."),
  ("p", "Those three categories are the whole point. Interchange goes to the bank that issued the "
        "customer's card and is set by Visa and Mastercard; it is identical whoever processes your "
        "payments. Scheme fees go to Visa and Mastercard themselves. The acquirer margin is what "
        "your provider keeps, and it is the only part anybody can negotiate."),
  ("p", "Then the transaction export is joined to the fees, which turns a monthly average into a "
        "cost per sale, and makes it possible to say that the eleven percent of transactions "
        "taken over the phone are carrying twenty-six percent of the fees."),
  ("callout", "Design rules that shaped every decision", [
   "The effective rate is computed from totals, never quoted from a contract.",
   "Interchange, scheme fees and acquirer margin are separated before anything is compared.",
   "Authorisation fees on declined transactions count. They are real and they are invisible.",
   "The card number is dropped at ingest. Card type and entry mode are what matter.",
   "A fee the system cannot categorise is a question for a human, not a guess.",
   "No rate is reported on a partial month.",
  ]),
  ("h2", "What it does not do"),
  ("p", "It does not switch your provider, it does not talk to your acquirer, and it does not "
        "touch the payment flow -- there is nothing in this system that could decline a sale. It "
        "reads two files and one contract and produces three numbers."),
  ("p", "It also does not tell you that your provider is overcharging you. Quite often they are "
        "not, and the gap between the quoted rate and the effective rate is almost entirely "
        "interchange on a card mix nobody chose. Knowing that is worth as much as finding an "
        "overcharge, and it stops you switching to an identical deal."),
  ("p", "The next four posts walk through each piece: how a statement becomes forty itemised "
        "fees, how the effective rate is actually computed, why some transactions cost four times "
        "what others do, and how to compare two providers without being lied to. One diagram per "
        "post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-statement-becomes-forty-fees",
 "title": "How a statement becomes forty itemised fees",
 "nav": "Reading the statement",
 "read": 5, "words": 780,
 "desc": ("Fourteen pages into individual fees, the three categories that decide everything, and "
          "the fees that are not in your contract at all."),
 "og": ("Forty-one fee types on one statement. Nine of them do not appear in the contract you "
        "signed, and one of those nine is the third largest line."),
 "abstract": ("Extracting itemised fees from a hostile document, classifying each as interchange, "
              "scheme or margin, and treating unmatched fees as questions."),
 "lede": ("A merchant statement is the least readable document a small business receives, and it "
          "is not readable by accident. Turning it into forty rows with a category each is the "
          "step everything else depends on."),
 "tags": ["card fees", "merchant services", "interchange", "statements", "extraction",
          "serverless"],
 "takeaways": [
  "Every fee gets a basis: per transaction, percentage of value, or monthly.",
  "Every fee gets a category: interchange, scheme, acquirer margin, or fixed.",
  "Interchange cannot be discounted by anybody. Say so, loudly.",
  "A fee not in the contract is a question, not an error.",
  "Extract once, then query the fees. Never re-read the PDF.",
 ],
 "blocks": [
  ("h2", "One document, three destinations"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Interchange", "sub": ["to the issuing bank,", "set by the schemes"],
       "icon": "money"},
      {"title": "Scheme fees", "sub": ["to Visa and", "Mastercard"], "icon": "network"},
      {"title": "Acquirer margin", "sub": ["what your provider", "keeps"], "icon": "target"},
      {"title": "Fixed monthly", "sub": ["terminal, PCI,", "gateway, minimum"], "icon": "gear"}],
    "target": {"title": "One statement total", "sub": ["reconciled to", "the bank"], "icon": "doc"},
    "note": "Four kinds of money on one line. Only two of the four respond to negotiation, and "
            "the statement is arranged so you cannot tell them apart."}),
   "Every fee on the statement belongs to one of four groups. Which group it is in decides whether "
   "there is anything you can do about it.",
   "Four fee categories converging on a single statement total",
   "Four routes on the left converge on one target on the right. The routes are Interchange, to "
   "the issuing bank and set by the schemes. Scheme fees, to Visa and Mastercard. Acquirer "
   "margin, what your provider keeps. And Fixed monthly, covering terminal rental, PCI, gateway "
   "and the minimum charge. All four arrive at One statement total, reconciled to the bank. A note "
   "says four kinds of money on one line, only two of the four respond to negotiation, and the "
   "statement is arranged so you cannot tell them apart."),
  ("h3", "Why the categories matter more than the amounts"),
  ("p", "If your effective rate is 2.31% and 1.34 points of that is interchange, then a competitor "
        "offering you 1.9% is either mispricing the deal or is not describing the same card mix. "
        "Interchange is a regulated pass-through in the UK and EU and a scheme-set one elsewhere; "
        "nobody discounts it, because nobody owns it."),
  ("p", "That single distinction changes what a good outcome looks like. A provider who cannot "
        "move your effective rate below 2.1% may still be worth pressing for a better margin, and "
        "a provider promising 1.6% is telling you something about their assumptions rather than "
        "about your business."),
  ("h3", "The fees that are not in your contract"),
  ("p", "Every statement carries a handful of fees that appear nowhere in the agreement you "
        "signed. Some are legitimate pass-throughs introduced after signing. Some are the result "
        "of a scheme fee change that got applied with a margin on top. And some are simply "
        "wrong -- a PCI non-compliance charge still being levied two years after you became "
        "compliant is the most common single error in this whole area."),
  ("p", "The system does not decide which is which. It matches every fee against the rate card "
        "and puts the unmatched ones in a list with their amounts, which is the difference "
        "between a suspicion and an email."),
  ("h2", "What extraction has to survive"),
  ("fig", ("chain", {
    "entry": {"title": "Statement lands", "sub": ["upload or", "mailbox"], "icon": "inbox"},
    "steps": [
      {"title": "Multi-page, multi-column", "sub": ["often a scan of", "a print"], "icon": "doc"},
      {"title": "Abbreviated codes", "sub": ["'MSC', 'IC DR CR',", "'NON-SEC SURCH'"], "icon": "code"},
      {"title": "Mixed bases", "sub": ["per txn, percent,", "monthly, annual"], "icon": "filter"},
      {"title": "Forty rows out", "sub": ["each with basis", "and category"], "icon": "database"}],
    "note": "The total at the bottom reconciles to the bank. Nothing above it explains itself, "
            "which is why this is the one place a capable model earns its cost."}),
   "The extraction step is the only genuinely hard engineering in the system, because the input is "
   "adversarial by design.",
   "A statement moving through extraction into forty categorised rows",
   "A chain beginning with Statement lands, by upload or mailbox. It passes through four stages. "
   "Multi-page and multi-column, often a scan of a print. Abbreviated codes such as MSC, IC DR CR "
   "and NON-SEC SURCH. Mixed bases: per transaction, percentage, monthly and annual. And finally "
   "forty rows out, each with a basis and a category. A note says the total at the bottom "
   "reconciles to the bank, nothing above it explains itself, and this is the one place a capable "
   "model earns its cost."),
  ("h3", "Extract once"),
  ("p", "The PDF is the source of record and it is read exactly once, into forty rows in a table. "
        "Every subsequent question -- what did interchange cost, which fees changed since March, "
        "what is the margin as a percentage -- is a query against those rows."),
  ("p", "This matters for cost, but it matters more for consistency. A number that came from a "
        "second reading of the same document is a number that can disagree with the first, and a "
        "report that contradicts last month's report is a report nobody trusts again."),
 ],
},
{
 "slug": "the-effective-rate",
 "title": "The effective rate, and why it is not what you were quoted",
 "nav": "The effective rate",
 "read": 5, "words": 760,
 "desc": ("Total fees over total turnover, what belongs in the numerator, and the two numbers to "
          "carry into any conversation about switching."),
 "og": ("Both numbers are true. 1.4% is the price of one kind of transaction; 2.31% is the price "
        "of your actual business."),
 "abstract": ("Computing an effective rate that survives scrutiny, what has to be included, and "
              "separating the negotiable part from the pass-through."),
 "lede": ("The effective rate is the simplest arithmetic in this series and the most commonly got "
          "wrong, almost always by leaving things out of the numerator."),
 "tags": ["card fees", "effective rate", "merchant services", "cost control", "benchmarking",
          "serverless"],
 "takeaways": [
  "Total fees over total card turnover. Everything the provider charged goes on top.",
  "Include terminal rental, PCI, gateway and the monthly minimum.",
  "Include authorisation fees on declined transactions. They have no sale to sit against.",
  "Report the margin separately. It is the only number you can move.",
  "Never compute a rate on a partial month.",
 ],
 "blocks": [
  ("h2", "What goes in the numerator"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Quoted", "parts": [("ic", 0.0), ("scheme", 0.0), ("margin", 1.40),
                                    ("fixed", 0.0), ("auth", 0.0)]},
      {"label": "Card fees only", "parts": [("ic", 1.34), ("scheme", 0.11), ("margin", 0.42),
                                            ("fixed", 0.0), ("auth", 0.0)]},
      {"label": "Effective", "parts": [("ic", 1.34), ("scheme", 0.11), ("margin", 0.42),
                                       ("fixed", 0.35), ("auth", 0.09)]}],
    "series": [("ic", "Interchange", "#64748b"), ("scheme", "Scheme fees", "#8b5cf6"),
               ("margin", "Acquirer margin", "#ef4444"), ("fixed", "Fixed monthly", "#f59e0b"),
               ("auth", "Auth fees, incl. declines", "#3b82f6")],
    "unit": "",
    "note": "Three ways of stating the same month, as a percentage of turnover. The quote on the "
            "left is not dishonest; it is answering a narrower question."}),
   "The left bar is the quote. The middle bar is what most people compute. The right bar is what "
   "you actually pay, and the gap between the middle and the right is the part that gets left out.",
   "Quoted rate, card fees only, and the full effective rate compared",
   "Three stacked bars showing percentage of turnover. The first, Quoted, is a single band of 1.40 "
   "percent acquirer margin. The second, Card fees only, stacks 1.34 percent interchange, 0.11 "
   "percent scheme fees and 0.42 percent acquirer margin. The third, Effective, adds 0.35 percent "
   "fixed monthly costs and 0.09 percent authorisation fees including declines on top of the same "
   "three bands. A note says these are three ways of stating the same month as a percentage of "
   "turnover, and the quote on the left is not dishonest, it is answering a narrower question."),
  ("h3", "The things most often left out"),
  ("ul", [
   "<strong>Terminal rental and PCI charges.</strong> They are fixed monthly costs of taking "
   "cards. On a quiet month they can be a third of the bill.",
   "<strong>The monthly minimum service charge.</strong> If turnover falls below the threshold you "
   "pay the minimum, and the effective rate that month is far higher than any quoted figure.",
   "<strong>Authorisation fees on declines.</strong> Charged per attempt, whatever the outcome, "
   "and they sit against no sale at all. On a subscription or a hotel book this is material.",
   "<strong>Chargeback and retrieval fees.</strong> Small, occasional, and they belong in the "
   "total because you paid them to take cards.",
  ]),
  ("h3", "The two numbers to carry"),
  ("p", "Every conversation about switching should start from two figures: the effective rate, and "
        "the acquirer margin as a share of it. The first tells you what card acceptance costs your "
        "business. The second tells you how much of that any provider could possibly change."),
  ("p", "In the example above the effective rate is 2.31% and the margin is 0.42 points of it. A "
        "provider who halves their margin saves you 0.21 points -- about eighty pounds a month on "
        "thirty-nine thousand of turnover. That is worth having and it is not the thousand pounds "
        "a switching pitch will imply."),
  ("h2", "Why partial months lie"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Day 12", "sub": ["fixed costs charged,", "turnover partial"], "icon": "clock"},
      {"title": "Rate looks 4.1%", "sub": ["mathematically", "true"], "icon": "alarm"},
      {"title": "Month closes", "sub": ["turnover catches", "the fixed costs"], "icon": "calendar"},
      {"title": "Rate is 2.31%", "sub": ["the number to", "act on"], "icon": "check"}],
    "title": "THE SAME MONTH, TWICE",
    "note": "Fixed monthly fees land at once and turnover arrives gradually. Any rate computed "
            "before the close is wrong in a direction that causes panic."}),
   "This is the single most common way a fee analysis embarrasses itself, and the fix is to refuse "
   "to report until the month is closed.",
   "The same month measured mid-month and after close",
   "A horizontal row of four boxes joined by arrows. Day twelve, with fixed costs charged and "
   "turnover partial. Rate looks 4.1 percent, mathematically true. Month closes and turnover "
   "catches the fixed costs. Rate is 2.31 percent, the number to act on. A note says fixed "
   "monthly fees land at once while turnover arrives gradually, so any rate computed before the "
   "close is wrong in a direction that causes panic."),
  ("p", "The report therefore fires on the monthly close and not on upload. It is a small "
        "constraint that removes an entire class of false alarm, and it is the reason the "
        "scheduling in part seven looks the way it does."),
 ],
},
{
 "slug": "why-some-transactions-cost-four-times-more",
 "title": "Why some transactions cost four times more",
 "nav": "Downgrades",
 "read": 5, "words": 790,
 "desc": ("Corporate cards, overseas cards, keyed-in sales and missing data -- the four reasons a "
          "transaction costs more than you expected, and which of them you can fix."),
 "og": ("Eleven percent of the transactions were taken over the phone. They carried twenty-six "
        "percent of the fees."),
 "abstract": ("Joining fees to transactions, identifying downgrades by cause, and separating the "
              "causes you can change from the customers you cannot."),
 "lede": ("A monthly average hides the fact that your card fees are not evenly distributed. Some "
          "transactions cost four times what others do, for four reasons, and two of the four are "
          "fixable this week."),
 "tags": ["card fees", "downgrades", "interchange", "payments", "operations", "serverless"],
 "takeaways": [
  "Corporate and commercial cards cost multiples of consumer debit. Nothing fixes that.",
  "Overseas-issued cards carry higher interchange. Nothing fixes that either.",
  "Keyed-in and card-not-present sales cost more. That one is often fixable.",
  "Missing data downgrades are a terminal configuration problem, not a pricing one.",
  "Rank causes by total cost, not by count.",
 ],
 "blocks": [
  ("h2", "Four causes, two of them yours"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Corporate card", "sub": ["higher interchange,", "not fixable"], "icon": "shield"},
      {"title": "Overseas issued", "sub": ["higher interchange,", "not fixable"], "icon": "map"},
      {"title": "Keyed in", "sub": ["cardholder not", "present -- fixable"], "icon": "phone"},
      {"title": "Data missing", "sub": ["terminal config", "-- fixable"], "icon": "gear"}],
    "target": {"title": "Charged above the", "sub": ["expected rate"], "icon": "alarm"},
    "note": "The first two are your customers and are not a problem to solve. The second two are "
            "your process, and they are where the recoverable money is."}),
   "Every downgraded transaction has one of four causes. Sorting them this way turns a fee problem "
   "into an operations problem, which is a much easier thing to act on.",
   "Four downgrade causes converging on a higher-than-expected charge",
   "Four routes on the left converge on one target on the right. Corporate card, higher "
   "interchange, not fixable. Overseas issued, higher interchange, not fixable. Keyed in, "
   "cardholder not present, fixable. And Data missing, a terminal configuration issue, fixable. "
   "All four arrive at Charged above the expected rate. A note says the first two are your "
   "customers and not a problem to solve, while the second two are your process and are where the "
   "recoverable money is."),
  ("h3", "The join that makes this visible"),
  ("p", "None of this can be seen on the statement, which reports fees in aggregate by type. It "
        "becomes visible only when the fees are joined to the transaction export, because the "
        "export carries the two fields that explain almost everything: the card type and the entry "
        "mode."),
  ("p", "Joined, the answer is usually blunt. Eleven percent of transactions taken over the phone "
        "carrying twenty-six percent of the fees is a real result from a real business, and the "
        "response to it is not a call to the acquirer. It is a payment link sent by text instead "
        "of reading a card number aloud."),
  ("h3", "Rank by cost, not by count"),
  ("p", "There will usually be more corporate-card downgrades than keyed-in ones, and they will "
        "matter less, because a corporate card on a nine pound sale costs pennies more while a "
        "keyed-in transaction on a four hundred pound sale costs several pounds more."),
  ("p", "So the report ranks causes by the total extra paid, and the count sits beside it as "
        "context. That ordering is the difference between a list that gets acted on and a list "
        "that gets filed."),
  ("h2", "What a fix looks like"),
  ("fig", ("chain", {
    "entry": {"title": "116 downgrades", "sub": ["£71 extra,", "one month"], "icon": "alarm"},
    "steps": [
      {"title": "Ranked by cost", "sub": ["keyed-in first,", "not corporate"], "icon": "chart"},
      {"title": "One process change", "sub": ["payment link", "instead of phone"], "icon": "link"},
      {"title": "Measured next month", "sub": ["same report,", "same arithmetic"], "icon": "calendar",
       "exit": {"title": "Or it did not work", "sub": ["which is also", "an answer"], "icon": "question"}},
      {"title": "£44 of £71 gone", "sub": ["the rest is your", "customer mix"], "icon": "check"}],
    "note": "The point of measuring monthly with identical arithmetic is that a change either "
            "shows up or it does not, and both outcomes are useful."}),
   "The loop is deliberately dull: rank, change one thing, measure the same way next month. Most "
   "of the remaining cost after that is customer mix, and knowing that is when you stop.",
   "A downgrade cost being ranked, addressed and remeasured",
   "A chain beginning with 116 downgrades costing seventy-one pounds extra in one month. It passes "
   "through Ranked by cost, keyed-in first rather than corporate. Then One process change, a "
   "payment link instead of a phone call. Then Measured next month with the same report and the "
   "same arithmetic, which has a branch marked Or it did not work, which is also an answer. And "
   "finally forty-four pounds of the seventy-one gone, with the rest being customer mix. A note "
   "says the point of measuring monthly with identical arithmetic is that a change either shows up "
   "or it does not, and both outcomes are useful."),
 ],
},
{
 "slug": "comparing-two-providers-honestly",
 "title": "Comparing two providers without being lied to",
 "nav": "Comparing quotes",
 "read": 5, "words": 770,
 "desc": ("Blended against IC++, the four questions that make a quote comparable, and the notice "
          "period that decides whether you have a choice at all."),
 "og": ("A quote you cannot restate as an effective rate on your own card mix is not a quote. It "
        "is a number."),
 "abstract": ("Making two offers comparable, why interchange-plus-plus is more honest than "
              "blended, and the contract fields that matter more than the rate."),
 "lede": ("Every merchant services quote is constructed to be incomparable with every other one. "
          "Four questions and your own effective rate make them comparable anyway."),
 "tags": ["card fees", "merchant services", "contracts", "negotiation", "procurement",
          "serverless"],
 "takeaways": [
  "Ask what card mix the quote assumes. If the answer is vague, the quote is vague.",
  "Blended pricing hides which transactions are expensive. IC++ cannot.",
  "Get every fixed monthly fee in writing, including the minimum charge.",
  "The notice period decides whether you can act on any of this.",
  "Restate every quote as an effective rate on your own last twelve months.",
 ],
 "blocks": [
  ("h2", "Blended against interchange-plus-plus"),
  ("fig", ("system", {
    "outside": [
      {"title": "Blended quote", "sub": ["one rate for", "everything"], "icon": "money"},
      {"title": "IC++ quote", "sub": ["interchange + scheme", "+ your margin"], "icon": "chart"},
      {"title": "Your card mix", "sub": ["from the last", "twelve months"], "icon": "cart"}],
    "inside": [
      {"title": "Restate both", "sub": ["as an effective", "rate"], "icon": "target"},
      {"title": "On your data", "sub": ["not on a", "worked example"], "icon": "database"},
      {"title": "One number each", "sub": ["now comparable"], "icon": "check"}],
    "edges": [{"from": 0, "to": 0, "label": "as offered"},
              {"from": 1, "to": 1, "label": "as offered"},
              {"from": 2, "to": 2, "label": "the denominator", "up": True}],
    "note": "Two quotes and your own transactions. Without the third input the first two cannot be "
            "compared, which is the entire reason quotes are structured the way they are."}),
   "A blended rate and an IC++ rate are not the same kind of object. Your own card mix is what "
   "converts both into a number you can put side by side.",
   "Two quote structures restated against your own card mix",
   "Three boxes across the top outside the AWS account. A Blended quote, one rate for everything. "
   "An IC++ quote, interchange plus scheme fees plus your margin. And Your card mix, from the last "
   "twelve months. The first two connect as offered; the third is labelled the denominator. Inside "
   "the account, three components. Restate both as an effective rate. On your data, not on a "
   "worked example. And One number each, now comparable. A note says two quotes and your own "
   "transactions, and that without the third input the first two cannot be compared, which is the "
   "entire reason quotes are structured the way they are."),
  ("h3", "Why IC++ is the more honest structure"),
  ("p", "Under interchange-plus-plus the statement shows interchange at cost, scheme fees at cost, "
        "and the provider's margin as a separate line. You can see all three. Under blended "
        "pricing you get one rate covering everything, which means the provider absorbs the "
        "variation -- and prices that risk into the rate."),
  ("p", "Blended is not a scam and for a very small merchant with a simple card mix it can be "
        "cheaper. But it is unauditable by construction: if you cannot see interchange, you cannot "
        "know whether a rate increase came from the schemes or from your provider deciding to take "
        "more."),
  ("h3", "The four questions"),
  ("ul", [
   "<strong>What card mix does this rate assume?</strong> Consumer debit, chip and PIN, "
   "UK-issued? Then say what happens to corporate, overseas and keyed-in.",
   "<strong>Is this blended or IC++?</strong> And if blended, what happens when interchange "
   "changes -- who absorbs it?",
   "<strong>What are the fixed monthly fees?</strong> All of them: terminal, gateway, PCI, "
   "minimum service charge, statement fee.",
   "<strong>What is the term and the notice period?</strong> This is the answer that decides "
   "whether the other three matter.",
  ]),
  ("h2", "The field that decides everything"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Term ends", "sub": ["the date everybody", "remembers"], "icon": "calendar"},
      {"title": "Minus notice", "sub": ["three to six", "months"], "icon": "clock"},
      {"title": "Minus a tender", "sub": ["six weeks to", "compare properly"], "icon": "doc"},
      {"title": "Decide here", "sub": ["months before you", "expected to"], "icon": "target"}],
    "title": "WORKING BACKWARDS FROM THE TERM END",
    "note": "Miss this date and the contract rolls, usually for another year, at whatever rate it "
            "rolls at. It is the most expensive field in the agreement."}),
   "The rate is what everybody negotiates and the notice period is what determines whether you "
   "ever get to. It is stored as a precomputed date for exactly that reason.",
   "Working backwards from the contract term end to the decision date",
   "A horizontal row of four boxes joined by arrows. Term ends, the date everybody remembers. "
   "Minus notice, three to six months. Minus a tender, six weeks to compare properly. Decide "
   "here, months before you expected to. A note says missing this date means the contract rolls, "
   "usually for another year, at whatever rate it rolls at, and that it is the most expensive "
   "field in the agreement."),
  ("p", "That is why the accounts table in part seven stores <code>notice_by</code> as its own "
        "field rather than deriving it. It is the one date in this entire system that has to fire "
        "whether or not anybody ever opens the record again."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="merchant account",
 volumes=[(2, "2 accounts"), (9, "9 accounts"), (30, "30 accounts")],
 read_each=0.042,
 msgs_each=4.0,
 store_base=0.30,
 store_growth=0.0009,
 lede=("The model runs once per statement, which is once per merchant account per month. A "
       "fourteen-page itemised PDF is the most expensive read in this series and it is still "
       "four cents. Nine accounts is a small group of sites or a franchisee. Here is where each "
       "cent goes."),
 takeaway_extra=("Transaction files are parsed without a model at all, so the cost scales with "
                 "statements rather than with sales volume."),
 risks=[
  "<strong>Sending transaction files through a model.</strong> They are CSV with a fixed header. "
  "Parse them; a model here would cost more than the fees you are auditing.",
  "<strong>Re-reading the statement to answer a new question.</strong> Extract once into fees and "
  "query the fees. The PDF is the source, not the working set.",
  "<strong>Storing card numbers because the export contains them.</strong> Drop the PAN at "
  "ingest. You need the card type and the entry mode, and nothing that puts you in scope.",
 ],
 per_unit_note=("One call per statement against a capable model, because merchant statements are "
                "the worst documents in this entire series: multi-column, abbreviated, "
                "inconsistent month to month, and frequently a scan of a print. This is a place "
                "where paying for a better model is straightforwardly correct, and it is still "
                "under five cents per account per month."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="cf",
 lede=("The same system with the service names filled in: what reads the statement, what joins "
       "it to the transactions, and where the two tables sit."),
 outside=[
  {"title": "Statements", "sub": ["monthly PDF,", "sometimes scanned"], "icon": "doc"},
  {"title": "Transaction export", "sub": ["CSV, daily or", "monthly"], "icon": "cart"},
  {"title": "The contract", "sub": ["rate card and", "what it covers"], "icon": "key"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["uploads and the", "monthly close"], "icon": "bucket"},
  {"title": "Lambda x4", "sub": ["terms, statement,", "join, report"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["accounts, fees"], "icon": "database"}],
 note="us-east-1. One account. Statements are read once per month; transactions are parsed "
      "without a model.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Statements, a monthly PDF and sometimes a "
  "scan. Transaction export, CSV, daily or monthly. And The contract, a rate card and what it "
  "covers. Inside the account, three groups. S3 and EventBridge for uploads and the monthly "
  "close. Four Lambda functions named terms, statement, join and report. And two DynamoDB tables "
  "named accounts and fees. A note gives the region as us-east-1, one account, and states that "
  "statements are read once per month and transactions are parsed without a model."),
 functions=[
  ["<code>cf-terms</code>", "S3 upload of a contract or rate change letter",
   "One model call; writes the quoted rate, what it applies to, the pricing model and the notice "
   "period", "60s / 1024&nbsp;MB"],
  ["<code>cf-statement</code>", "S3 upload of a statement",
   "One model call to itemised fees; classifies each as interchange, scheme or acquirer margin",
   "120s / 2048&nbsp;MB"],
  ["<code>cf-join</code>", "S3 upload of a transaction export",
   "Parses CSV without a model, drops the PAN, joins fees to transactions, flags downgrades",
   "60s / 1024&nbsp;MB"],
  ["<code>cf-report</code>", "EventBridge, after the monthly close",
   "Computes the effective rate and the margin, ranks downgrade causes, mails the three numbers",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>cf-terms-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "One model id; the contracts prefix; accounts"],
  ["<code>cf-statement-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "One model id; the statements prefix; fees"],
  ["<code>cf-join-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>",
   "The exports prefix; both tables"],
  ["<code>cf-report-role</code>",
   "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "Both tables; one verified identity"]],
 tables=[
  ("Table: accounts",
   "PK   account_id        S\n"
   "SK   '#terms'          S   one item per merchant account\n"
   "     pricing_model     S   blended | ic_plus | ic_plus_plus\n"
   "     quoted_rate       N   the number on the front of the quote\n"
   "     quoted_applies_to S   the card type and entry mode it assumes\n"
   "     auth_fee          N   per authorisation, charged whatever the outcome\n"
   "     monthly_fixed     M   terminal rental, PCI, gateway, minimum charge\n"
   "     notice_months     N\n"
   "     notice_by         S   precomputed, because it is the only date that matters\n\n"
   "quoted_applies_to is stored as text because the honest answer is\n"
   "usually a sentence: consumer debit, chip and PIN, UK-issued."),
  ("Table: fees",
   "PK   account_id#period S\n"
   "SK   fee_code          S   one item per distinct fee on the statement\n"
   "     category          S   interchange | scheme | acquirer | fixed\n"
   "     basis             S   per_txn | pct_of_value | monthly | annual\n"
   "     amount            N\n"
   "     txn_count         N   what it was charged on, where the statement says\n"
   "     value_charged     N\n"
   "     matched_rate      N   from the contract, or null if the fee is not in it\n"
   "     downgrade_reason  S   corporate | international | keyed | data_missing | none\n\n"
   "category is the field the whole page turns on: interchange cannot be\n"
   "negotiated, acquirer margin can, and mixing them makes every\n"
   "comparison meaningless."),
  ],
 inbound=[
  "<strong>Statements arrive by upload or by mailbox</strong> and both land in the same function. "
  "Nothing depends on an acquirer portal that could change or be withdrawn.",
  "<strong>Transaction exports are parsed, not read by a model.</strong> They are fixed-header "
  "CSV, they are large, and a model would be both slower and less accurate than a parser.",
  "<strong>The PAN is dropped at ingest.</strong> The card type and entry mode are what the "
  "analysis needs; keeping the number would put this system in PCI scope for no benefit.",
  "<strong>The report waits for the monthly close</strong>, because an effective rate computed on "
  "a partial month is the number that starts an argument you then lose."],
 model_notes=[
  "<strong>Two calls, both per document.</strong> One per contract or rate change letter, one per "
  "statement. Nothing per transaction.",
  "<strong>A capable model for statements</strong>, deliberately. These are the worst documents "
  "in the series -- multi-column, abbreviated, often scanned -- and cheap extraction produces "
  "confidently wrong fee bases.",
  "<strong>A JSON schema with nulls allowed.</strong> A fee the model cannot categorise becomes a "
  "question for a human rather than a guess, because guessing interchange as margin inverts the "
  "conclusion.",
  "<strong>The rate arithmetic is arithmetic.</strong> Total fees over total value, per category. "
  "No model is asked to compute or judge a percentage.",
  "<strong>Downgrade causes come from the transaction data</strong>, not from the model. The "
  "statement rarely says why; the card type and entry mode do."],
 gotchas=[
  "Compute the effective rate, never quote it. Total fees over total card turnover, including "
  "every monthly fixed cost, is the only figure that compares two providers.",
  "Separate interchange from acquirer margin before comparing anything. Interchange is set by the "
  "schemes and identical whoever you use; a provider discounting it is discounting nothing.",
  "Include authorisation fees on declined transactions. They are charged on the attempt, they do "
  "not appear against any sale, and on a high-decline book they are material.",
  "Read the minimum monthly service charge. On a quiet month it is the whole bill, and it is the "
  "fee most often left out of a comparison.",
  "Drop the card number at ingest. Nothing in this system needs it, and keeping it changes what "
  "compliance regime the system sits in."],
))
