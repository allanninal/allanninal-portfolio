"""Day 130 -- 2026-09-01 -- Credit limit reviewer."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "credit-limit-reviewer"
NAME = "Credit limit reviewer"

SPEC = {
 "slug": SLUG, "date": "2026-09-01", "name": NAME,
 "tagline": ("Sets a trade credit limit from the application and the filed accounts, then keeps "
             "it honest by watching how the customer actually pays -- because the limit that was "
             "right in March is the one that loses you eleven thousand pounds in November."),
 "lede": ("A small system that reads a credit application, measures what you are really exposed "
          "to rather than what the invoice ledger says, revisits a limit when the customer's "
          "behaviour changes rather than on an annual calendar, and gets the answer to the person "
          "taking the order while they are still on the phone. Seven posts on the same system, "
          "one diagram at a time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["credit control", "trade credit", "credit limit", "accounts receivable",
              "risk", "serverless"],
 "icons": ["money", "chart", "shield"],
 "faq": [
  ("What is a credit limit reviewer?",
   "A small serverless system that sets a trade credit limit from the application and the filed "
   "accounts, tracks live exposure against it, and re-reviews the limit when the customer's own "
   "payment behaviour changes."),
  ("Why not just use a credit bureau score?",
   "Because a bureau tells you how a company pays the market and your own ledger tells you how it "
   "pays you, and those disagree more often than they agree. The bureau is the opening number; "
   "your ledger is the one that matters after the third invoice."),
  ("Why is exposure not just the unpaid invoices?",
   "Because an order accepted today and delivered on Thursday is money at risk from the moment "
   "you commit the stock, and it will not appear in the ledger for another week. Systems that "
   "count only posted invoices understate exposure by roughly a trading week."),
  ("Does the system refuse orders on its own?",
   "No. It produces a number and the reasons behind it. A human overrides it whenever they want, "
   "and the override is recorded with a name against it, which is what makes it a decision rather "
   "than a workaround."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "credit-limit-reviewer-on-aws",
 "title": "A credit limit reviewer on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 870,
 "desc": ("Sets a trade credit limit, tracks live exposure against it, and revisits it when "
          "behaviour changes. AWS, about $3 a month."),
 "og": ("Nobody loses money on the customer they refused. They lose it on the one whose limit "
        "was set correctly two years ago and never looked at again."),
 "abstract": ("The whole system on one page -- the application, live exposure, the review "
              "trigger -- and why the annual credit review is the wrong shape entirely."),
 "lede": ("A customer you have traded with for three years, always paid, never any trouble, goes "
          "quiet in October and stops answering the phone in November. The limit was eight "
          "thousand. The balance when they went under was nineteen, because the limit was a "
          "number in a field that nothing ever compared anything to."),
 "tags": ["credit control", "trade credit", "accounts receivable", "risk", "cash flow",
          "serverless"],
 "takeaways": [
  "A limit is a loss you have agreed to be able to survive, not a compliment.",
  "Exposure includes what you have committed, not just what you have invoiced.",
  "Your own ledger is a better predictor than any bureau score.",
  "Review on behaviour, not on the anniversary of the application.",
  "Designed on AWS for about $3 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "A new account", "sub": ["applying for terms"], "icon": "form"},
      {"title": "Your own ledger", "sub": ["invoices, payments,", "orders"], "icon": "money"},
      {"title": "Whoever takes the order", "sub": ["on the phone, now"], "icon": "person"}],
    "inside": [
      {"title": "The opening limit", "sub": ["application and", "filed accounts"], "icon": "doc"},
      {"title": "Live exposure", "sub": ["committed, not just", "invoiced"], "icon": "counter"},
      {"title": "Review and answer", "sub": ["on behaviour,", "in seconds"], "icon": "check"}],
    "edges": [{"from": 0, "to": 0, "label": "application"},
              {"from": 1, "to": 1, "label": "every order and payment"},
              {"from": 2, "to": 2, "label": "a number and a reason", "up": True}],
    "note": "The middle box is the one most businesses do not have, and it is the one that "
            "decides whether the other two matter."}),
   "Three things outside the account, three pieces inside it. The opening limit is the easy part; "
   "keeping it true is the system.",
   "System: credit applications assessed, exposure tracked, limits reviewed",
   "Three boxes across the top sit outside the AWS account. On the left, A new account applying "
   "for terms. In the middle, Your own ledger of invoices, payments and orders. On the right, "
   "Whoever takes the order, on the phone now. Each connects by an arrow to the AWS account "
   "container below. The application flows down into the account. Every order and payment feeds "
   "in. A number and a reason goes back out. Inside the AWS account are three components in a "
   "row. On the left, The opening limit, from the application and filed accounts. In the middle, "
   "Live exposure, counting what is committed rather than only what is invoiced. On the right, "
   "Review and answer, driven by behaviour and returned in seconds. A note says the middle box is "
   "the one most businesses do not have, and it is the one that decides whether the other two "
   "matter."),
  ("h3", "What a limit actually is"),
  ("p", "A credit limit is not a rating and it is not a statement about how much you like the "
        "customer. It is the largest amount you are willing to lose if they fail, expressed as a "
        "number you can check an order against before you ship it."),
  ("p", "That framing does most of the work. A customer who orders twelve hundred a month and "
        "always pays does not need a fifty thousand limit, and giving them one costs nothing "
        "until the month they order forty thousand of stock they cannot pay for."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The opening limit.</strong> Set once, from the application and whatever public "
   "record exists, and deliberately small. Part 2.",
   "<strong>Live exposure.</strong> What you are on the hook for right now, including the pallet "
   "on the van. Part 3.",
   "<strong>Review and answer.</strong> Revisiting the limit when something changes, and getting "
   "the result to the person who needs it. Parts 4 and 5.",
  ]),
  ("h2", "One customer, three years"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Applied", "sub": ["limit set at 3,000"], "icon": "form"},
      {"title": "Paid on time", "sub": ["11 months"], "icon": "check"},
      {"title": "Limit raised", "sub": ["to 8,000, on evidence"], "icon": "chart"},
      {"title": "Started paying late", "sub": ["47 days, then 61"], "icon": "clock"},
      {"title": "Limit held", "sub": ["before the order", "that would have hurt"], "icon": "shield"}],
    "title": "ONE CUSTOMER, THREE YEARS",
    "note": "The fourth box is the one nobody notices. It is also the only one that was ever a "
            "warning."}),
   "The same system as one line. The increase in the middle is earned; the hold at the end is the "
   "whole return on building this.",
   "One trade customer from application through to a held limit",
   "A horizontal row of five boxes joined by arrows. Applied, with the limit set at three "
   "thousand. Paid on time for eleven months. Limit raised to eight thousand, on evidence. "
   "Started paying late, at forty-seven days and then sixty-one. Limit held, before the order "
   "that would have hurt. A note says the fourth box is the one nobody notices and it is also the "
   "only one that was ever a warning."),
  ("h2", "In plain words"),
  ("p", "A company applies for a trade account. The application and the filed accounts are read "
        "once, a small opening limit is set, and the reasons for it are written down where "
        "somebody can find them in two years."),
  ("p", "From then on, every order and every payment updates one number: what you are exposed to "
        "right now. Not what has been invoiced, which lags reality by a week, but what you have "
        "committed -- accepted orders, picked stock, goods on the van, invoices raised and "
        "invoices not raised yet."),
  ("p", "When the customer's payment behaviour moves, the limit is re-examined. Not on the "
        "anniversary of the application, which is a date with no meaning, but when the average "
        "days-beyond-terms drifts, when an order is unusually large, or when something changes at "
        "Companies House."),
  ("p", "And when somebody is on the phone taking an order, the answer arrives in the order "
        "screen in under a second: how much room is left, and if there is not enough, what the "
        "options are. A refusal with an alternative is a sale on different terms; a refusal on "
        "its own is a lost customer."),
  ("callout", "Design rules that shaped every decision", [
   "The limit is what you can afford to lose, not what they can afford to owe.",
   "Exposure counts commitments, not just postings. The van is exposure.",
   "Your ledger beats any bureau score after the third invoice.",
   "Review on a behaviour change, never on a calendar.",
   "The system never refuses anything. It produces a number, and a person decides.",
   "Every override is recorded with a name and a reason, and both are visible later.",
  ]),
  ("h2", "What it does not do"),
  ("p", "It does not chase the money. Invoice chasing is a different system with a different "
        "rhythm, and merging them produces something that does neither well."),
  ("p", "It does not set prices, it does not approve orders, and it does not replace the "
        "conversation with a customer who is struggling. It measures, and it makes sure the "
        "measurement is in front of somebody at the moment they can act on it."),
  ("p", "The next four posts walk through each piece: how the opening limit gets set, why "
        "exposure is more than the unpaid invoices, what makes a limit worth revisiting, and how "
        "the answer reaches the sales floor. One diagram per post, a cost breakdown, and an "
        "engineering reference at the end."),
 ],
},
{
 "slug": "how-a-credit-limit-gets-set",
 "title": "How a credit limit gets set the first time",
 "nav": "Setting the limit",
 "read": 5, "words": 760,
 "desc": ("Reading the application, what filed accounts actually tell you, and why the first "
          "limit should be smaller than everybody wants it to be."),
 "og": ("Filed accounts are eleven months old and were prepared to minimise tax. They are the "
        "least current thing you will ever base a decision on."),
 "abstract": ("What goes on a credit application, what the filed accounts are worth, how trade "
              "references fail, and why the opening limit is deliberately small."),
 "lede": ("The first limit is set with almost no information, which is exactly why it should be "
          "small and why the system's real job starts on the second invoice."),
 "tags": ["credit control", "trade credit", "underwriting", "filed accounts", "onboarding",
          "serverless"],
 "takeaways": [
  "The application is a structured form, not a PDF somebody types up later.",
  "Filed accounts are old and optimised for tax; read them for shape, not health.",
  "Trade references are chosen by the applicant, so they are nearly worthless.",
  "Open small. The first three invoices are worth more than any document.",
  "Write down the reason for the number, because the next reviewer needs it.",
 ],
 "blocks": [
  ("h2", "What the application asks for"),
  ("fig", ("chain", {
    "entry": {"title": "Credit application", "sub": ["a form, not an email"], "icon": "form"},
    "steps": [
      {"title": "Identity", "sub": ["registered name, number,", "registered address"],
       "icon": "doc"},
      {"title": "The ask", "sub": ["how much, how often,", "what for"], "icon": "money",
       "side": {"title": "Most useful field", "sub": ["expected monthly spend"], "icon": "chart"}},
      {"title": "Public record", "sub": ["filed accounts,", "charges, officers"], "icon": "search"},
      {"title": "References", "sub": ["two trade, one bank"], "icon": "person",
       "side": {"title": "Weight applied", "sub": ["close to zero"], "icon": "filter"}},
      {"title": "One structured record", "sub": ["not a PDF in a folder"], "icon": "database"}],
    "note": "Everything above is available in ten minutes. It is worth roughly one month of "
            "trading history."}),
   "The intake, top to bottom. The most valuable field is the one asking what they expect to "
   "spend, because it is the number the limit gets compared against.",
   "How a credit application is broken into a structured record",
   "A vertical chain of five steps entered by a box labelled Credit application, a form rather "
   "than an email. Step one is Identity: registered name, number and registered address. Step two "
   "is The ask: how much, how often and what for, with a side box noting that the most useful "
   "field is expected monthly spend. Step three is Public record: filed accounts, charges and "
   "officers. Step four is References: two trade and one bank, with a side box noting that the "
   "weight applied is close to zero. Step five produces One structured record rather than a PDF "
   "in a folder. A note says everything above is available in ten minutes and is worth roughly "
   "one month of trading history."),
  ("h3", "Why the form matters more than it looks"),
  ("p", "A credit application that arrives as an email attachment and gets filed becomes "
        "unfindable within a quarter. The same information captured as fields becomes a record "
        "that a review can compare against three years later, which is the only moment it is "
        "genuinely useful."),
  ("p", "There is one model call in this system and this is where it earns its place: taking the "
        "PDF that a customer insists on sending and turning it into those fields, with anything "
        "it cannot find left explicitly null rather than guessed at."),
  ("h2", "What filed accounts are worth"),
  ("callout", "Read them for shape, not for health", [
   "<strong>They are old.</strong> A small company files up to nine months after its year end, so "
   "you are frequently reading something twenty-one months out of date.",
   "<strong>They are abridged.</strong> Small-company filings often show a balance sheet and "
   "little else. There is no profit figure to be reassured by.",
   "<strong>They were prepared to minimise tax</strong>, which is legitimate and which means a "
   "healthy business can look thin on paper.",
   "<strong>What is worth reading:</strong> net assets, whether they are negative, the trend "
   "across two filings, and whether anything is charged against the company.",
   "<strong>What is worth more:</strong> a filing that is late. It is the single most useful "
   "signal in the whole document, and it does not need reading to find.",
  ]),
  ("p", "A late filing does not mean a company is failing. It means the people running it are "
        "either very busy or not in control of their paperwork, and both of those correlate with "
        "how you will be paid."),
  ("h2", "Why references do not work"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Trade references", "sub": ["chosen by the applicant"], "icon": "person",
       "label": "selection bias"},
      {"title": "Bank reference", "sub": ["a paragraph of hedging"], "icon": "doc",
       "label": "says nothing"},
      {"title": "Bureau score", "sub": ["how they pay the market"], "icon": "chart",
       "label": "useful, generic"}],
    "target": {"title": "An opening limit", "sub": ["small, and stated"], "icon": "money",
               "then": {"title": "The first three invoices", "sub": ["worth more than", "all of it"],
                        "icon": "check"}},
    "note": "Nobody has ever supplied the reference of a supplier they are behind with."}),
   "Three inputs to the opening decision and their honest weights. The box underneath is what "
   "actually decides the limit, and it does not exist yet on day one.",
   "Three information sources for an opening credit limit",
   "Three boxes stacked on the left. Trade references, chosen by the applicant, labelled "
   "selection bias. Bank reference, a paragraph of hedging, labelled says nothing. And Bureau "
   "score, how they pay the market, labelled useful but generic. All three converge on An opening "
   "limit, small and stated, and that leads down to The first three invoices, worth more than all "
   "of it. A note says nobody has ever supplied the reference of a supplier they are behind with."),
  ("h3", "Open small on purpose"),
  ("p", "The opening limit should cover roughly one month of the spend the customer said they "
        "expect, rounded down. If they expect four thousand a month, three thousand is a sensible "
        "opening position and it is not an insult; it is the number you can review upwards in "
        "twelve weeks with evidence."),
  ("p", "The customer who objects strenuously to a small opening limit is providing information. "
        "A business with functioning cash flow can work inside three thousand pounds for a "
        "quarter, and one that genuinely cannot is telling you something the accounts did not."),
  ("h3", "Write down why"),
  ("p", "The reason for the number matters as much as the number. Three thousand because their "
        "stated spend was four and there is nothing adverse is a different starting point from "
        "three thousand because net assets are negative and we are proceeding cautiously."),
  ("p", "Two years later, somebody reviewing this account will find one of those two sentences "
        "and act completely differently depending on which. Storing the reason costs one text "
        "field."),
  ("p", "Next: what you are actually exposed to."),
 ],
},
{
 "slug": "why-exposure-is-more-than-the-invoices",
 "title": "Why exposure is more than the unpaid invoices",
 "nav": "Measuring exposure",
 "read": 6, "words": 780,
 "desc": ("Committed stock, goods in transit and unbilled deliveries -- the week of trading that "
          "never appears on the ledger."),
 "og": ("The pallet went out on Tuesday and gets invoiced on Friday. For three days it is worth "
        "nothing on every screen in the building."),
 "abstract": ("What a ledger balance leaves out, how to count committed exposure, why the gap is "
              "roughly a trading week, and what to do about disputed invoices."),
 "lede": ("Every business that has been caught by a customer failure discovered afterwards that "
          "the real number was larger than the one on the screen, and usually by about a week."),
 "tags": ["credit control", "exposure", "accounts receivable", "order to cash", "risk",
          "serverless"],
 "takeaways": [
  "The ledger balance is exposure minus everything that has not been billed yet.",
  "Accepted orders, picked stock and goods in transit are all money at risk.",
  "The gap is about one trading week, which is when failures happen.",
  "A disputed invoice is still exposure until it is credited.",
  "One number, recomputed on events, not a nightly batch.",
 ],
 "blocks": [
  ("h2", "What the ledger does not know"),
  ("fig", ("system", {
    "outside": [
      {"title": "Order accepted", "sub": ["stock committed"], "icon": "cart"},
      {"title": "Goods despatched", "sub": ["on the van"], "icon": "truck"},
      {"title": "Invoice raised", "sub": ["finally visible"], "icon": "doc"}],
    "inside": [
      {"title": "Counted by nobody", "sub": ["not on any screen"], "icon": "stop"},
      {"title": "Counted by nobody", "sub": ["still not on any screen"], "icon": "stop"},
      {"title": "Counted at last", "sub": ["the ledger wakes up"], "icon": "counter"}],
    "edges": [{"from": 0, "to": 0, "label": "day 0"},
              {"from": 1, "to": 1, "label": "day 2"},
              {"from": 2, "to": 2, "label": "day 5"}],
    "note": "Five days of exposure that every report in the business values at zero."}),
   "The order-to-cash sequence with the ledger's view underneath it. The first two columns are "
   "the ones that get people hurt.",
   "Where committed exposure is invisible to the invoice ledger",
   "Three boxes across the top outside the AWS account, forming a sequence. Order accepted, stock "
   "committed, on day zero. Goods despatched, on the van, on day two. Invoice raised, finally "
   "visible, on day five. Beneath each, inside the account, is what the ledger sees. For the "
   "first two, Counted by nobody, not on any screen. For the third, Counted at last, the ledger "
   "wakes up. A note says five days of exposure that every report in the business values at zero."),
  ("h3", "The commitment happens at acceptance"),
  ("p", "The moment you accept an order you have committed stock, allocated labour, and in many "
        "cases bought something specifically. If the customer fails on Wednesday, the order taken "
        "on Monday is a loss whether or not anybody has raised the paperwork."),
  ("p", "Which means exposure has to be counted from acceptance, not from invoicing. The billing "
        "run is an accounting event; it has nothing to do with when the money went at risk."),
  ("h2", "Counting it properly"),
  ("callout", "Everything that belongs in the number", [
   "<strong>Posted invoices, unpaid.</strong> The part everybody already counts.",
   "<strong>Delivered, not yet invoiced.</strong> Usually two to five days of trading.",
   "<strong>Accepted orders, not yet delivered.</strong> Committed the moment you said yes.",
   "<strong>Goods in transit</strong>, which is the same thing with a lorry attached and a longer "
   "tail on a three-day delivery.",
   "<strong>Less: payments received but unallocated.</strong> The money is in the bank; do not "
   "hold it against them because the cash posting is behind.",
   "<strong>Not less: disputed invoices.</strong> A dispute is a reason not to chase, not a "
   "reason to stop being owed.",
  ]),
  ("p", "The unallocated payments line is the one that causes arguments internally, and it is "
        "worth being firm about. A customer who paid on Friday should not be blocked on Monday "
        "because the remittance has not been matched yet. Blocking a paying customer is the most "
        "expensive false positive this system can produce."),
  ("h2", "Disputes are still exposure"),
  ("fig", ("chain", {
    "entry": {"title": "Invoice disputed", "sub": ["short delivery"], "icon": "alarm"},
    "steps": [
      {"title": "Chasing stops", "sub": ["correctly"], "icon": "stop"},
      {"title": "Exposure does not", "sub": ["you are still owed it"], "icon": "counter"},
      {"title": "Resolution or credit", "sub": ["one or the other"], "icon": "check",
       "side": {"title": "Not 'left open'", "sub": ["that is the failure mode"], "icon": "clock"}},
      {"title": "Exposure moves", "sub": ["only now"], "icon": "money"}],
    "note": "A dispute that stays open for four months is a credit note nobody wanted to write."}),
   "What a dispute changes and what it does not. Removing disputed value from exposure is how a "
   "limit quietly stops meaning anything.",
   "How a disputed invoice affects chasing and exposure differently",
   "A vertical chain of four steps entered by a box labelled Invoice disputed, short delivery. "
   "Step one, Chasing stops, correctly. Step two, Exposure does not, because you are still owed "
   "it. Step three, Resolution or credit, one or the other, with a side box noting that left open "
   "is the failure mode. Step four, Exposure moves, only now. A note says a dispute that stays "
   "open for four months is a credit note nobody wanted to write."),
  ("h3", "Recompute on events"),
  ("p", "Exposure is one number per customer, and it changes when something happens: an order is "
        "accepted, a delivery goes out, an invoice is raised, a payment lands, a credit is "
        "issued. That is a handful of events a day for a small business."),
  ("p", "Recomputing on those events rather than in a nightly batch means the number is right "
        "when somebody looks at it, which is invariably at four in the afternoon while a customer "
        "waits on the phone. A nightly figure is a figure from before this morning's orders."),
  ("h3", "The headroom number"),
  ("p", "What the sales floor needs is not exposure and not the limit; it is the difference. "
        "Headroom is the number that answers the actual question, which is whether this order can "
        "go on the account right now."),
  ("p", "Publishing headroom rather than exposure also stops a well-meant argument about which "
        "figure is correct. There is one number, it is derived, and it is either positive enough "
        "for the order or it is not."),
  ("p", "Next: when to look at the limit again."),
 ],
},
{
 "slug": "what-makes-a-limit-worth-revisiting",
 "title": "What makes a limit worth revisiting",
 "nav": "Reviewing it",
 "read": 6, "words": 790,
 "desc": ("Why annual reviews miss everything, which behaviour changes matter, and the signals "
          "that come out of your own ledger."),
 "og": ("The average customer who fails was paying you on time nine months earlier. The drift is "
        "the whole signal, and an annual review is designed to miss it."),
 "abstract": ("Why calendar reviews fail, the behavioural triggers worth watching, days beyond "
              "terms as the core metric, and when to reduce a limit rather than hold it."),
 "lede": ("An annual review means that for eleven months of the year, nothing is watching, and "
          "companies do not fail on the anniversary of their credit application."),
 "tags": ["credit control", "risk", "monitoring", "days beyond terms", "accounts receivable",
          "serverless"],
 "takeaways": [
  "Days beyond terms, trended, is the strongest signal you own.",
  "Review on events: a drift, a large order, a filing, an ownership change.",
  "A limit that is never approached should come down, quietly.",
  "Reductions are a conversation, not an email at 2am.",
  "The trigger list is short and it should stay short.",
 ],
 "blocks": [
  ("h2", "Why the annual review fails"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Month 1-9", "parts": [("n", 29)]},
      {"label": "Month 10", "parts": [("n", 38)]},
      {"label": "Month 11", "parts": [("n", 52)]},
      {"label": "Month 12", "parts": [("n", 71)]}],
    "series": [("n", "Average days to pay", "#4A90D9")],
    "unit": "",
    "note": "The review was scheduled for month 12. By then the question had answered itself."}),
   "One customer's payment behaviour in the year before they failed. Every bar after the first is "
   "a trigger; the calendar review arrives after the last one.",
   "Average days to pay across the year before a customer failure",
   "A bar chart with four bars showing average days to pay. Months one to nine: twenty-nine days. "
   "Month ten: thirty-eight days. Month eleven: fifty-two days. Month twelve: seventy-one days. A "
   "note says the review was scheduled for month twelve, by which time the question had answered "
   "itself."),
  ("p", "Nothing in that chart is subtle, and yet it is invisible to a business that looks at an "
        "account once a year and otherwise only notices whether today's payment arrived. The "
        "individual invoices were all eventually paid, which is exactly why nobody escalated."),
  ("h3", "Days beyond terms is the metric"),
  ("p", "Not whether an invoice is overdue today, which is noise, but the trend in how long the "
        "customer takes relative to the terms they agreed. A customer on thirty-day terms paying "
        "consistently at thirty-four is fine. The same customer moving from thirty-four to "
        "forty-eight over a quarter is the signal."),
  ("p", "It is also a metric you own outright. It needs no subscription, it is computed from your "
        "own ledger, and it describes how the customer treats you specifically rather than how "
        "they treat their largest supplier."),
  ("h2", "The trigger list"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Behaviour drift", "sub": ["DBT up 10 days", "over a quarter"], "icon": "chart",
       "label": "the important one"},
      {"title": "Unusual order", "sub": ["3x their normal"], "icon": "cart", "label": "size"},
      {"title": "Public record", "sub": ["late filing, charge,", "director change"], "icon": "doc",
       "label": "external"}],
    "target": {"title": "A review task", "sub": ["with the reason", "attached"], "icon": "form",
               "then": {"title": "Raise, hold, reduce", "sub": ["a person decides"],
                        "icon": "person"}},
    "note": "Three triggers, deliberately. A longer list produces a queue nobody works."}),
   "What causes a limit to be looked at again. The review arrives with its reason already stated, "
   "which is the difference between a task and a notification.",
   "Three triggers that queue a credit limit review",
   "Three boxes stacked on the left. Behaviour drift, days beyond terms up ten days over a "
   "quarter, labelled the important one. Unusual order, three times their normal, labelled size. "
   "And Public record: late filing, charge or director change, labelled external. All three "
   "converge on A review task with the reason attached, which leads down to Raise, hold or "
   "reduce, where a person decides. A note says three triggers deliberately, because a longer "
   "list produces a queue nobody works."),
  ("h3", "Keep the list short"),
  ("p", "It is tempting to add triggers: a returned direct debit, a change of address, a new "
        "email domain, a sudden gap in ordering. Each is individually defensible and together "
        "they produce forty tasks a week, which produces a queue that gets closed in bulk on a "
        "Friday afternoon without being read."),
  ("p", "Three triggers producing two or three real reviews a month is a system somebody actually "
        "works. That is worth more than a comprehensive one that gets ignored."),
  ("h2", "Reviewing downwards"),
  ("callout", "Three honest outcomes, and how each is delivered", [
   "<strong>Raise.</strong> Evidence-based, on request or on a large order, and the easiest "
   "conversation you will ever have.",
   "<strong>Hold.</strong> The most common outcome, and it needs no conversation at all -- but "
   "the reason still gets recorded.",
   "<strong>Reduce.</strong> Never by email, never automatically, and never as a surprise on the "
   "next order. Somebody rings them.",
   "<strong>The unused limit.</strong> A customer with a twenty thousand limit who has never "
   "exceeded two thousand should come down at the next natural moment. It costs nothing to them "
   "and removes a risk you were carrying for no return.",
   "<strong>The recorded reason is the deliverable</strong> in all four cases. The number without "
   "it is unusable at the next review.",
  ]),
  ("p", "Reducing a limit is the only genuinely difficult action in credit control, which is why "
        "most businesses never do it and simply carry limits that were set years ago against "
        "trading volumes that no longer exist."),
  ("p", "A quiet reduction of an unused limit is almost never noticed and almost never disputed. "
        "A reduction on a customer who is actively trading is a phone call, made before the "
        "system starts refusing things, by somebody who can explain it."),
  ("h3", "What automation must not do here"),
  ("p", "It must not send the reduction. A limit cut arriving as an automated email at two in the "
        "morning turns a manageable conversation into a relationship ending, and it will reach "
        "the customer's whole team before it reaches yours."),
  ("p", "The system's job is to notice, to assemble the evidence, and to put a task in front of a "
        "human with everything they need to make the call in four minutes rather than forty."),
  ("p", "Next: getting the answer to the person taking the order."),
 ],
},
{
 "slug": "how-a-credit-decision-reaches-the-sales-floor",
 "title": "How a credit decision reaches the sales floor",
 "nav": "Delivering the answer",
 "read": 5, "words": 750,
 "desc": ("Headroom at the point of order, refusals that come with an alternative, and why the "
          "override is a feature."),
 "og": ("A refusal without an alternative is a lost customer. A refusal with a proforma option is "
        "a sale on different terms."),
 "abstract": ("Delivering headroom where the order is taken, what a good refusal contains, why "
              "overrides must exist and be recorded, and what the monthly view should show."),
 "lede": ("Every part of this system is preparation for one moment: somebody is on the phone, the "
          "order is forty-two hundred, and the answer has to be right and immediate."),
 "tags": ["credit control", "sales", "order management", "workflow", "operations", "serverless"],
 "takeaways": [
  "Headroom belongs in the order screen, not in a report.",
  "A refusal must carry the alternative, or it is just a no.",
  "Overrides are legitimate. Unrecorded overrides are not.",
  "Show the reason and the date, always, on every answer.",
  "One monthly view: total exposure, by band, and what changed.",
 ],
 "blocks": [
  ("h2", "At the point of order"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Order keyed", "sub": ["£4,200"], "icon": "cart"},
      {"title": "Headroom checked", "sub": ["under a second"], "icon": "counter"},
      {"title": "£1,800 available", "sub": ["not enough"], "icon": "alarm"},
      {"title": "Options offered", "sub": ["part-ship, deposit,", "card"], "icon": "money"},
      {"title": "Sale, on terms", "sub": ["that suit both"], "icon": "check"}],
    "title": "THE THIRTY SECONDS THAT MATTER",
    "note": "The third box is where most systems stop, and it is the most expensive place to stop."}),
   "The moment the whole system exists for. Everything upstream is preparation for the fourth "
   "box, which is the one that keeps the customer.",
   "A credit check at the point of order, ending in options rather than a refusal",
   "A horizontal row of five boxes. Order keyed, four thousand two hundred pounds. Headroom "
   "checked, in under a second. One thousand eight hundred pounds available, not enough. Options "
   "offered: part-ship, deposit or card. Sale, on terms that suit both. A note says the third box "
   "is where most systems stop and it is the most expensive place to stop."),
  ("h3", "Under a second, or it will be bypassed"),
  ("p", "A credit check that takes eight seconds gets worked around within a fortnight. Somebody "
        "will start keying orders and checking afterwards, which is the same as not checking, and "
        "you will not find out until the quarter it matters."),
  ("p", "This is why exposure is a single stored number recomputed on events rather than a query "
        "that sums the ledger on demand. The read is one lookup, and the expensive part happened "
        "when the order was accepted, not when somebody asked."),
  ("h2", "What a good refusal contains"),
  ("callout", "Four things, every time", [
   "<strong>The headroom.</strong> Not 'declined' -- the actual number, so the person can see "
   "whether a part order fits.",
   "<strong>The reason.</strong> At limit, or overdue balance, or under review. These lead to "
   "completely different conversations.",
   "<strong>The alternative.</strong> Part-ship to the available value, take a deposit, take a "
   "card, or release on approval.",
   "<strong>Who can approve it.</strong> A named person, not 'contact accounts'. The order is "
   "waiting and the customer is listening.",
  ]),
  ("p", "The alternative is the part that pays for the system. A customer at their limit still "
        "wants the goods, and part-shipping to the available value while taking a card for the "
        "rest converts an argument into an order that is smaller but real."),
  ("h2", "Overrides are supposed to happen"),
  ("fig", ("chain", {
    "entry": {"title": "Order blocked", "sub": ["£4,200 vs £1,800"], "icon": "stop"},
    "steps": [
      {"title": "Somebody knows more", "sub": ["'their payment cleared", "this morning'"],
       "icon": "person"},
      {"title": "Override, with a reason", "sub": ["from a picklist"], "icon": "check",
       "side": {"title": "And a name", "sub": ["always"], "icon": "key"}},
      {"title": "Order proceeds", "sub": ["immediately"], "icon": "cart"},
      {"title": "It appears in the review", "sub": ["next time this", "account is looked at"],
       "icon": "report"}],
    "note": "An override rate of zero means the limits are too high, not that the process is "
            "working."}),
   "The override path, which exists deliberately. The fourth box is what makes it accountable "
   "without making it slow.",
   "How a credit override is recorded and surfaced later",
   "A vertical chain of four steps entered by a box labelled Order blocked, four thousand two "
   "hundred against one thousand eight hundred. Step one, Somebody knows more, quoting that their "
   "payment cleared this morning. Step two, Override with a reason from a picklist, with a side "
   "box noting And a name, always. Step three, Order proceeds immediately. Step four, It appears "
   "in the review next time this account is looked at. A note says an override rate of zero means "
   "the limits are too high rather than that the process is working."),
  ("h3", "Why blocking the override is worse"),
  ("p", "A system that cannot be overridden gets routed around entirely: orders go on a different "
        "account, or as cash sales, or on somebody's word to the warehouse. That is the same risk "
        "with none of the record."),
  ("p", "An override that takes four seconds and records who and why is a control. An override "
        "that requires a form and a manager's approval is an obstacle, and obstacles in a sales "
        "process lose to the phone call every time."),
  ("h2", "The monthly view"),
  ("p", "One page a month, and it is not a list of accounts. Total exposure, split into three "
        "bands -- comfortably inside limit, close to it, and over -- with what moved since last "
        "month and why."),
  ("p", "That page answers the only question the owner actually has, which is whether the amount "
        "of money out on trust is going up or down and which two customers are responsible for "
        "the change. A twelve-page aged debtor report answers a different question that nobody "
        "asked."),
  ("h3", "What this system does not replace"),
  ("p", "It does not replace ringing a customer who has gone quiet, and it does not replace "
        "knowing your trade. What it replaces is the situation where the number in front of the "
        "person taking the order is wrong, stale, or missing entirely."),
  ("p", "Everything else in credit control is judgement. This is just making sure the judgement "
        "is exercised against accurate figures at the moment it can still change the outcome."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="review",
 volumes=[(20, "20 reviews"), (80, "80 reviews"), (320, "320 reviews")],
 read_each=0.0031,
 msgs_each=1.6,
 lede=("The model runs once per credit application, not per order: the headroom check is a single "
       "key lookup and costs nothing. Eighty reviews a month is a business onboarding steadily "
       "and watching its ledger properly. Here is where each cent goes."),
 takeaway_extra=("The headroom check is a point read, so the order-taking path costs the same "
                 "whether you check ten orders a day or a thousand."),
 risks=[
  "<strong>Recomputing exposure by summing the ledger on every check.</strong> Store the number "
  "and move it on events; a full scan per order keyed is how a two-dollar system becomes a "
  "hundred-dollar one.",
  "<strong>Re-reading filed accounts on a schedule.</strong> They change once a year. Read them "
  "when the filing date moves, not every month.",
  "<strong>Alerting on every overdue invoice.</strong> That is invoice chasing, it belongs "
  "elsewhere, and routing it through here doubles the messaging for no decision.",
 ],
 per_unit_note=("The read is one call per credit application against a small model, extracting "
                "fields from a PDF the customer sent. Orders do not trigger a read at all -- the "
                "check at the point of order is a single-item lookup, which is why the volume "
                "that scales is reviews rather than sales."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="cl",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the event-sourced exposure figure, and the single model call."),
 outside=[
  {"title": "Applications", "sub": ["a form, plus the PDF", "they sent anyway"], "icon": "form"},
  {"title": "Order and ledger events", "sub": ["accepted, despatched,", "invoiced, paid"],
   "icon": "money"},
  {"title": "The order screen", "sub": ["asking for headroom"], "icon": "browser"}],
 inside=[
  {"title": "API Gateway + EventBridge", "sub": ["checks in,", "triggers on a schedule"],
   "icon": "gateway"},
  {"title": "Lambda x4", "sub": ["intake, expose,", "check, review"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["accounts, events"], "icon": "database"}],
 note="us-east-1. One account. Exposure is a stored figure moved by events, never a scan.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Applications, arriving as a form plus the "
  "PDF they sent anyway. Order and ledger events covering accepted, despatched, invoiced and "
  "paid. And The order screen, asking for headroom. Inside the account, three groups. API Gateway "
  "for checks coming in and EventBridge for scheduled triggers. Four Lambda functions named "
  "intake, expose, check and review. And two DynamoDB tables named accounts and events. A note "
  "gives the region as us-east-1, one account, and states that exposure is a stored figure moved "
  "by events rather than a scan."),
 functions=[
  ["<code>cl-intake</code>", "API, on application submitted",
   "Extracts fields from the application PDF; writes the account and the opening limit",
   "60s / 1024&nbsp;MB"],
  ["<code>cl-expose</code>", "EventBridge, on every order and ledger event",
   "Moves the stored exposure figure and appends the event; recomputes headroom",
   "10s / 512&nbsp;MB"],
  ["<code>cl-check</code>", "API, from the order screen",
   "Single-item read; returns headroom, reason and the available alternatives",
   "5s / 512&nbsp;MB"],
  ["<code>cl-review</code>", "EventBridge, daily",
   "Evaluates the three triggers; queues review tasks with the evidence attached",
   "120s / 512&nbsp;MB"]],
 roles=[
  ["<code>cl-intake-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "One model id; the applications prefix; accounts"],
  ["<code>cl-expose-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>dynamodb:PutItem</code>", "Accounts; events"],
  ["<code>cl-check-role</code>", "<code>dynamodb:GetItem</code>", "Accounts only, read"],
  ["<code>cl-review-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Events; accounts; one verified identity"]],
 tables=[
  ("Table: accounts",
   "PK   account_id        S\n"
   "SK   '#limit'          S   one item per account\n"
   "     legal_name        S   registered name, not the trading name\n"
   "     company_no        S\n"
   "     terms_days        N\n"
   "     limit_amount      N\n"
   "     limit_reason      S   free text, required, shown at the next review\n"
   "     limit_set_at      S\n"
   "     limit_set_by      S\n"
   "     exposure          N   the stored figure, moved by cl-expose\n"
   "     headroom          N   derived; written alongside so the check is one read\n"
   "     dbt_90            N   average days beyond terms, trailing 90 days\n"
   "     review_state      S   none | queued | in_progress\n\n"
   "The check path reads exactly this item and nothing else. That is\n"
   "deliberate: an eight-second check is a check that gets bypassed."),
  ("Table: events",
   "PK   account_id        S\n"
   "SK   occurred_at#id    S\n"
   "     kind              S   accepted | despatched | invoiced | paid |\n"
   "                           credited | disputed | override\n"
   "     amount            N   signed; the exposure delta this event applied\n"
   "     ref               S   order or invoice number\n"
   "     actor             S   set on override, and only on override\n"
   "     reason            S   picklist value on override; free text on dispute\n"
   "     ttl               N   24 months; the trend needs a year, not a decade\n\n"
   "Exposure is replayable from this table, which is how you prove the\n"
   "stored figure is right rather than hoping it is.")],
 inbound=[
  "<strong>Order events are the input, not invoices.</strong> Acceptance moves exposure; "
  "invoicing only changes which bucket it sits in.",
  "<strong>Unallocated payments reduce exposure immediately.</strong> Waiting for the cash "
  "posting blocks customers who have already paid, which is the worst error this system can make.",
  "<strong>Disputes set a flag, not a credit.</strong> Chasing stops; the exposure figure does "
  "not move until a credit note exists.",
  "<strong>The check endpoint is read-only</strong> and has no write permissions at all, so the "
  "busiest path in the system cannot corrupt anything."],
 model_notes=[
  "<strong>One call, at application time only.</strong> Extracting registered name, company "
  "number, requested terms and expected monthly spend from whatever the customer sent.",
  "<strong>A small, fast model.</strong> This is field extraction from a two-page document, not "
  "analysis, and a larger model produces identical fields at eight times the price.",
  "<strong>A JSON schema it must fill or leave null.</strong> A guessed company number is worse "
  "than an empty one, because somebody will act on it.",
  "<strong>It does not set the limit.</strong> The limit comes from a stated policy applied to "
  "extracted fields, so it can be explained to a customer who asks.",
  "<strong>It never reads the ledger.</strong> Payment behaviour is arithmetic, and arithmetic "
  "does not need a language model."],
 gotchas=[
  "Count exposure from order acceptance. The gap between acceptance and invoicing is about a "
  "trading week, and that week is when failures land.",
  "Store headroom next to the limit. Deriving it on demand is what makes the check slow enough "
  "to be bypassed.",
  "Never send a limit reduction automatically. Queue it for somebody who can pick up a phone, "
  "because the email version ends relationships.",
  "Record every override with a name and a reason from a picklist. Free text produces 'ok per "
  "Dave' four hundred times and no usable data.",
  "Give the trigger list three entries and defend it. Every added trigger costs you a percentage "
  "of the reviews that actually get worked."],
))
