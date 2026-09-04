"""Day 131 -- 2026-09-02 -- Rebate claim tracker."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "rebate-claim-tracker"
NAME = "Rebate claim tracker"

SPEC = {
 "slug": SLUG, "date": "2026-09-02", "name": NAME,
 "tagline": ("Turns supplier rebate agreements into rules, measures your actual buying against "
             "them as it happens, and claims before the window shuts -- because a rebate you "
             "earned and did not claim is the cheapest money you will ever fail to collect."),
 "lede": ("A small system that reads the rebate terms out of a supplier agreement, accrues what "
          "you are owed as the purchases happen rather than discovering it at year end, tells you "
          "when you are one pallet short of a tier that pays retrospectively, and files the claim "
          "with evidence before the window closes. Seven posts on the same system, one diagram at "
          "a time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["supplier rebates", "trade terms", "purchasing", "accruals", "margin",
              "serverless"],
 "icons": ["money", "doc", "calendar"],
 "faq": [
  ("What is a rebate claim tracker?",
   "A small serverless system that holds supplier rebate terms as machine-readable rules, accrues "
   "earned rebate against live purchase data, and produces claims with evidence before each "
   "agreement's claim window closes."),
  ("Why do businesses miss rebates they have earned?",
   "Because the terms live in a PDF attached to an email from two years ago, the person who "
   "negotiated them has left, and nobody is measuring purchases against tiers until somebody "
   "asks at year end -- by which time several claim windows have closed."),
  ("What is a tier cliff?",
   "A retrospective tier pays a higher percentage on everything you bought in the period, not "
   "just the amount above the threshold. Being two percent short of one is expensive, and being "
   "two percent over it is worth far more than the extra purchase cost."),
  ("Why will the supplier's figure differ from mine?",
   "Almost always because of definitions: returns, credits, freight lines, promotional stock and "
   "excluded ranges. The gap is a vocabulary problem rather than an arithmetic one, and it is why "
   "a claim needs the line detail attached."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "rebate-claim-tracker-on-aws",
 "title": "A rebate claim tracker on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Reads rebate terms into rules, accrues against live purchases, and claims before the "
          "window shuts. AWS, about $3 a month."),
 "og": ("The rebate was earned in March, the window closed in July, and nobody knew either "
        "sentence was true until the following February."),
 "abstract": ("The whole system on one page -- the agreement as a rule, the live accrual, the "
              "claim -- and why this money is the easiest margin in the business to lose."),
 "lede": ("Somewhere in an inbox is a PDF that says you get two and a half percent back on "
          "everything you buy from a supplier above ninety thousand a year, rising to four "
          "percent above a hundred and forty. You bought a hundred and thirty-eight thousand. "
          "Nobody noticed until March, and the claim window closed in January."),
 "tags": ["supplier rebates", "trade terms", "purchasing", "margin", "working capital",
          "serverless"],
 "takeaways": [
  "Rebate terms belong in a rule, not in a PDF nobody opens.",
  "Accrue as you buy; year-end discovery is how windows get missed.",
  "Retrospective tiers pay on everything, so the last pallet is the valuable one.",
  "Your figure and the supplier's will differ, and the difference is definitional.",
  "Designed on AWS for about $3 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Supplier agreements", "sub": ["PDFs, and their", "annual amendments"], "icon": "doc"},
      {"title": "Your purchase ledger", "sub": ["invoices, credits,", "returns"], "icon": "money"},
      {"title": "Whoever buys", "sub": ["deciding this week's", "order"], "icon": "person"}],
    "inside": [
      {"title": "Terms as rules", "sub": ["tiers, dates,", "exclusions"], "icon": "form"},
      {"title": "Live accrual", "sub": ["earned so far,", "against each tier"], "icon": "counter"},
      {"title": "Claims and windows", "sub": ["with evidence,", "before they shut"], "icon": "calendar"}],
    "edges": [{"from": 0, "to": 0, "label": "read once, per amendment"},
              {"from": 1, "to": 1, "label": "every purchase line"},
              {"from": 2, "to": 2, "label": "where you stand, now", "up": True}],
    "note": "The arrow going back up is worth more than the claim itself: it changes what you buy "
            "while you can still buy it."}),
   "Three things outside the account, three pieces inside it. The claim is the visible output; "
   "the feedback to the buyer is where the money actually is.",
   "System: rebate agreements read into rules, accrued, and claimed",
   "Three boxes across the top sit outside the AWS account. On the left, Supplier agreements, "
   "PDFs and their annual amendments. In the middle, Your purchase ledger of invoices, credits "
   "and returns. On the right, Whoever buys, deciding this week's order. Each connects by an "
   "arrow to the AWS account container below. The agreements are read once per amendment. Every "
   "purchase line feeds in. Where you stand now goes back out. Inside the AWS account are three "
   "components in a row. On the left, Terms as rules covering tiers, dates and exclusions. In the "
   "middle, Live accrual showing what is earned so far against each tier. On the right, Claims "
   "and windows, with evidence, before they shut. A note says the arrow going back up is worth "
   "more than the claim itself because it changes what you buy while you can still buy it."),
  ("h3", "Why this money goes missing"),
  ("p", "Rebate income is not invoiced to you and it does not appear on a statement. Nothing "
        "arrives to remind you it exists. It is the only significant sum in a small business that "
        "has to be actively gone and got, and the only person who knows the terms is usually the "
        "one who negotiated them."),
  ("p", "When that person changes role, the terms become a document in a folder, the accrual "
        "becomes a guess at year end, and two or three claims a year quietly expire. None of that "
        "shows up as a loss anywhere, which is precisely why it persists."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Terms as rules.</strong> The agreement, once, turned into tiers, dates and "
   "exclusions a machine can evaluate. Part 2.",
   "<strong>Live accrual.</strong> What you have earned so far, updated as purchases land, with "
   "the tier you are closest to. Part 3.",
   "<strong>Claims and windows.</strong> What a claim has to contain to survive scrutiny, and "
   "how a window stops being missed. Parts 4 and 5.",
  ]),
  ("h2", "One agreement, one year"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Agreement signed", "sub": ["3 tiers, 90-day", "claim window"], "icon": "doc"},
      {"title": "Accruing", "sub": ["£1,840 earned", "by June"], "icon": "counter"},
      {"title": "One pallet short", "sub": ["flagged in October"], "icon": "alarm"},
      {"title": "Tier hit", "sub": ["4% on the whole year"], "icon": "chart"},
      {"title": "Claimed in day 12", "sub": ["not day 94"], "icon": "check"}],
    "title": "ONE AGREEMENT, ONE YEAR",
    "note": "The third box paid for the entire system, and it is the only one that had to happen "
            "at a particular moment."}),
   "The same system as one line. The alert in October is the part that cannot be done "
   "retrospectively, which is why it is the part worth automating.",
   "One supplier rebate agreement across a year, from signing to claim",
   "A horizontal row of five boxes joined by arrows. Agreement signed, three tiers and a "
   "ninety-day claim window. Accruing, one thousand eight hundred and forty pounds earned by "
   "June. One pallet short, flagged in October. Tier hit, four percent on the whole year. Claimed "
   "on day twelve rather than day ninety-four. A note says the third box paid for the entire "
   "system and it is the only one that had to happen at a particular moment."),
  ("h2", "In plain words"),
  ("p", "A supplier agreement arrives as a PDF. It is read once -- properly, by a model, into "
        "structured fields -- and becomes a rule: these product ranges, this period, these tiers, "
        "this claim window, these exclusions. The PDF is kept, because a claim sometimes needs "
        "the original wording, but nothing downstream reads it again."),
  ("p", "From then on, every purchase invoice line is matched against the rules it might count "
        "towards. A line can count towards more than one agreement, and frequently does. The "
        "accrual moves as the lines land, so the number is current rather than annual."),
  ("p", "In October, when the system can see that you are four thousand pounds of purchases short "
        "of a tier that pays retrospectively on the whole year, it says so to the person placing "
        "orders. That is a purchasing decision with about six weeks of runway, and it is the "
        "single most valuable output here."),
  ("p", "At period end the claim is assembled with the line detail behind it, submitted inside the "
        "window rather than near the end of it, and then chased -- because a submitted claim and "
        "a received credit note are separated by roughly two months and one forgotten email."),
  ("callout", "Design rules that shaped every decision", [
   "The agreement is read once and becomes a rule. Nothing downstream re-reads a PDF.",
   "Accrue on purchase lines, not on supplier statements. Their statement arrives too late to "
   "act on.",
   "A retrospective tier pays on everything, so proximity to a threshold is an alert, not a note.",
   "Every accrual has to be explainable down to the invoice lines that produced it.",
   "The claim window is a date with a countdown, not a field in a document.",
   "Chase the credit note, not the claim. Submission is the halfway point.",
  ]),
  ("h2", "What it does not do"),
  ("p", "It does not negotiate, it does not tell you whether the terms are good, and it does not "
        "buy anything. Deciding to spend four thousand pounds in November to earn six is a "
        "judgement about stock, cash and shelf life that only the buyer can make."),
  ("p", "It also does not replace the supplier relationship. When your figure and theirs differ "
        "by nine hundred pounds, the resolution is a phone call. What the system does is make "
        "sure you arrive at that call with the line detail rather than with a number you cannot "
        "explain."),
  ("p", "The next four posts walk through each piece: how an agreement becomes a rule, why an "
        "accrual is not a claim, what a claim needs to survive scrutiny, and how a window stops "
        "being missed. One diagram per post, a cost breakdown, and an engineering reference at "
        "the end."),
 ],
},
{
 "slug": "how-a-rebate-agreement-becomes-a-rule",
 "title": "How a rebate agreement becomes a rule",
 "nav": "Terms as rules",
 "read": 5, "words": 760,
 "desc": ("Reading the terms once, the five fields that matter, and why exclusions are the part "
          "that gets missed."),
 "og": ("Every rebate dispute you will ever have is about the word 'qualifying'. It is worth "
        "getting that definition out of the PDF on day one."),
 "abstract": ("Extracting rebate terms into structured rules, the five fields that decide "
              "everything, why exclusions are the expensive omission, and what to do about "
              "amendments."),
 "lede": ("A rebate agreement is three pages of which about eleven lines matter, and the eleven "
          "lines are never in the same place twice."),
 "tags": ["supplier rebates", "contracts", "document extraction", "purchasing", "rules",
          "serverless"],
 "takeaways": [
  "Five fields decide a rebate: basis, tiers, period, window, exclusions.",
  "Retrospective or incremental is the single most important distinction.",
  "Exclusions are where the arguments come from, so extract them explicitly.",
  "An amendment is a new version, not an edit. Keep both.",
  "Anything the model cannot find stays null and gets asked about.",
 ],
 "blocks": [
  ("h2", "The five fields"),
  ("fig", ("chain", {
    "entry": {"title": "The agreement PDF", "sub": ["three pages,", "eleven useful lines"],
              "icon": "doc"},
    "steps": [
      {"title": "Basis", "sub": ["spend, units,", "or growth"], "icon": "counter"},
      {"title": "Tiers", "sub": ["threshold and rate"], "icon": "chart",
       "side": {"title": "And the flag", "sub": ["retrospective or", "incremental"],
                "icon": "branch"}},
      {"title": "Period", "sub": ["calendar, financial,", "or rolling"], "icon": "calendar"},
      {"title": "Claim window", "sub": ["days after period end"], "icon": "clock"},
      {"title": "Exclusions", "sub": ["the expensive field"], "icon": "filter"}],
    "note": "Everything else in the document is boilerplate that has never once affected a claim."}),
   "The extraction, top to bottom. The side box on tiers is the difference between a rebate worth "
   "four hundred pounds and one worth four thousand.",
   "How a rebate agreement is reduced to five structured fields",
   "A vertical chain of five steps entered by a box labelled The agreement PDF, three pages with "
   "eleven useful lines. Step one is Basis: spend, units or growth. Step two is Tiers, threshold "
   "and rate, with a side box for the flag marking retrospective or incremental. Step three is "
   "Period: calendar, financial or rolling. Step four is Claim window, days after period end. "
   "Step five is Exclusions, the expensive field. A note says everything else in the document is "
   "boilerplate that has never once affected a claim."),
  ("h3", "Retrospective versus incremental"),
  ("p", "An incremental tier pays the higher rate only on the spend above the threshold. A "
        "retrospective tier pays it on everything from the first pound. The wording is often no "
        "more explicit than 'on total qualifying purchases', and the difference at a hundred and "
        "forty thousand pounds of spend is several thousand pounds."),
  ("p", "It also completely changes the behaviour of the system. Under an incremental tier, being "
        "just short of a threshold costs you almost nothing. Under a retrospective one, the last "
        "four thousand pounds of purchases earns a return of over a hundred percent, and that is "
        "worth interrupting somebody about."),
  ("h2", "Exclusions are the expensive field"),
  ("callout", "What 'qualifying purchases' usually excludes", [
   "<strong>Freight and delivery lines.</strong> Almost universally excluded, and almost never "
   "stripped out of the figure people quote.",
   "<strong>Promotional and deal stock</strong> already bought at a discount, which is the "
   "exclusion that causes the largest gaps.",
   "<strong>Specific ranges</strong> -- third-party brands the supplier distributes but does not "
   "own, and clearance lines.",
   "<strong>Credits and returns</strong>, which reduce the figure, and sometimes only if returned "
   "within the period.",
   "<strong>Anything unpaid at period end</strong>, in about a third of agreements. This one "
   "quietly links your rebate to your own payment behaviour.",
  ]),
  ("p", "Getting the exclusions out of the document on day one is what makes your accrual match "
        "the supplier's figure at claim time. A system that accrues on gross spend will be over "
        "by five to twelve percent every single time, and every claim becomes a negotiation you "
        "start from a weak position."),
  ("h3", "One model call, per document"),
  ("p", "This is the natural place for a model: pulling eleven specific facts out of prose that "
        "no two suppliers write the same way. It runs once per agreement and once per amendment, "
        "which is a handful of times a year, not per transaction."),
  ("p", "What it must not do is infer. If the document does not say whether the tiers are "
        "retrospective, the field stays null and somebody is asked -- because the guess is wrong "
        "half the time and the consequence is an accrual that is wrong by a factor of four."),
  ("h2", "Amendments are versions"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Annual renewal", "sub": ["new rates,", "same structure"], "icon": "calendar",
       "label": "expected"},
      {"title": "Mid-year letter", "sub": ["'with effect from", "1 July'"], "icon": "email",
       "label": "the awkward one"},
      {"title": "Verbal agreement", "sub": ["confirmed by email"], "icon": "chat",
       "label": "still a version"}],
    "target": {"title": "A new rule version", "sub": ["effective from a date"], "icon": "form",
               "then": {"title": "Both versions kept", "sub": ["the period spans", "the change"],
                        "icon": "archive"}},
    "note": "A mid-year change means one period evaluated under two rules. Overwriting the old "
            "one loses half the year."}),
   "Three ways terms change, all producing the same thing: a dated version. The box underneath is "
   "the reason you never edit a rule in place.",
   "How rebate agreement changes become dated rule versions",
   "Three boxes stacked on the left. Annual renewal, new rates and the same structure, labelled "
   "expected. Mid-year letter, with effect from the first of July, labelled the awkward one. And "
   "Verbal agreement confirmed by email, labelled still a version. All three converge on A new "
   "rule version, effective from a date, which leads down to Both versions kept, because the "
   "period spans the change. A note says a mid-year change means one period evaluated under two "
   "rules, and overwriting the old one loses half the year."),
  ("h3", "Why the original stays"),
  ("p", "The extracted rule is what the system evaluates, but a disputed claim is settled by "
        "reading the actual sentence. Keeping the source document alongside the rule, with the "
        "page the terms came from, turns a two-week email exchange into a two-minute one."),
  ("p", "It also gives you a way to check the extraction later. A rule that has been quietly wrong "
        "for eight months is worse than no rule, and the only way to catch it is being able to "
        "put the two side by side."),
  ("p", "Next: what an accrual actually is."),
 ],
},
{
 "slug": "why-an-accrual-is-not-a-claim",
 "title": "Why an accrual is not a claim",
 "nav": "The live accrual",
 "read": 6, "words": 780,
 "desc": ("Earning as you buy, the danger of accruing what you will not hit, and the tier alert "
          "that has to arrive early."),
 "og": ("Four thousand pounds of purchases earning six thousand pounds of rebate is a decision "
        "somebody has to make in October. In February it is a story."),
 "abstract": ("Accruing on purchase lines, why over-accrual hurts, how proximity to a "
              "retrospective tier becomes an alert, and the difference between earned, claimed "
              "and received."),
 "lede": ("An accrual is your best current estimate of money you have earned and do not yet have, "
          "which makes it useful, and makes it dangerous if you treat it as certain."),
 "tags": ["supplier rebates", "accruals", "purchasing", "margin", "forecasting", "serverless"],
 "takeaways": [
  "Accrue on invoice lines, applying the exclusions, not on gross spend.",
  "Only accrue the tier you are confidently going to reach.",
  "Proximity to a retrospective tier is an alert with a deadline.",
  "Earned, claimed and received are three different numbers. Keep all three.",
  "A line can qualify for two agreements at once, and often does.",
 ],
 "blocks": [
  ("h2", "Where the number comes from"),
  ("fig", ("chain", {
    "entry": {"title": "Purchase invoice", "sub": ["fourteen lines"], "icon": "doc"},
    "steps": [
      {"title": "Match to agreements", "sub": ["one line can count", "towards two"], "icon": "branch"},
      {"title": "Apply exclusions", "sub": ["freight, deal stock,", "excluded ranges"],
       "icon": "filter", "side": {"title": "Typically removes", "sub": ["5-12% of the total"],
                                  "icon": "counter"}},
      {"title": "Add to the period", "sub": ["against the right", "rule version"], "icon": "calendar"},
      {"title": "Re-evaluate tiers", "sub": ["and the distance", "to the next one"], "icon": "chart"},
      {"title": "One accrual per", "sub": ["agreement-period"], "icon": "money"}],
    "note": "Every step is arithmetic. The only judgement in the whole chain is which tier you "
            "believe you will reach."}),
   "How a purchase invoice moves the accrual. The exclusions step is the one that keeps your "
   "figure and the supplier's within arguing distance of each other.",
   "How a purchase invoice line becomes part of a rebate accrual",
   "A vertical chain of five steps entered by a box labelled Purchase invoice, fourteen lines. "
   "Step one, Match to agreements, noting one line can count towards two. Step two, Apply "
   "exclusions covering freight, deal stock and excluded ranges, with a side box noting this "
   "typically removes five to twelve percent of the total. Step three, Add to the period against "
   "the right rule version. Step four, Re-evaluate tiers and the distance to the next one. Step "
   "five, One accrual per agreement-period. A note says every step is arithmetic and the only "
   "judgement in the chain is which tier you believe you will reach."),
  ("h3", "Lines, not totals"),
  ("p", "Accruing from an invoice total is quick and it is wrong. The exclusions apply at line "
        "level, one invoice frequently contains lines belonging to two different agreements, and "
        "at claim time the supplier will want the lines anyway."),
  ("p", "Doing it at line level from the start costs nothing extra -- the lines are already in the "
        "purchase ledger -- and means the claim is a query rather than a reconstruction."),
  ("h2", "Do not accrue what you will not hit"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Accrue at top tier", "parts": [("n", 5600)]},
      {"label": "Accrue at achieved", "parts": [("n", 3450)]},
      {"label": "Actually received", "parts": [("n", 3450)]}],
    "series": [("n", "Rebate value, £", "#7AA116")],
    "unit": "",
    "note": "The first bar is a promise to your own management accounts that somebody has to "
            "break in January."}),
   "The cost of optimistic accrual. The gap is not a rounding error; it is margin reported in one "
   "month and reversed in another.",
   "Optimistic rebate accrual against the amount actually received",
   "A bar chart with three bars showing rebate value in pounds. Accrue at top tier: five thousand "
   "six hundred. Accrue at achieved: three thousand four hundred and fifty. Actually received: "
   "three thousand four hundred and fifty. A note says the first bar is a promise to your own "
   "management accounts that somebody has to break in January."),
  ("p", "The rule that works is to accrue at the tier you have already achieved, and to show the "
        "next tier separately as an opportunity rather than as income. Two numbers, clearly "
        "labelled, and only one of them goes anywhere near the management accounts."),
  ("p", "This matters more than it sounds. Rebate accrued optimistically inflates reported margin "
        "for most of the year and then gets reversed in a single month, which makes that month "
        "look like a trading problem when it is a bookkeeping one."),
  ("h2", "The alert that has a deadline"),
  ("callout", "What the tier alert has to say", [
   "<strong>How far short you are</strong>, in the basis the agreement uses -- pounds, units or "
   "growth percentage, not a percentage of a percentage.",
   "<strong>What it is worth</strong>, which under a retrospective tier is the uplift on the "
   "whole period, not on the shortfall.",
   "<strong>How long is left</strong>, in weeks, against a period end date.",
   "<strong>What that means in stock</strong>: roughly what you would have to buy, in terms a "
   "buyer recognises.",
   "<strong>And the honest caveat</strong>: that stock has to be sellable, or the rebate is a "
   "discount on inventory you did not want.",
  ]),
  ("p", "Timing is everything with this alert. Six to eight weeks before period end is actionable. "
        "Two weeks before is a panic buy at the wrong price, and after period end it is a story "
        "about money you did not get."),
  ("h3", "Three numbers, not one"),
  ("p", "Earned is what the rules say you have accrued. Claimed is what you have submitted. "
        "Received is what has arrived as a credit note or a payment. They are three different "
        "numbers and the gaps between them are where the work is."),
  ("p", "Most businesses that track rebates at all track the first one and assume the other two "
        "follow. The gap between claimed and received is typically the largest of the three, "
        "because a submitted claim sits in a supplier's queue behaving exactly like an unchased "
        "invoice."),
  ("p", "Next: what a claim has to contain."),
 ],
},
{
 "slug": "what-a-claim-needs-to-survive-scrutiny",
 "title": "What a claim needs to survive scrutiny",
 "nav": "Making the claim",
 "read": 6, "words": 780,
 "desc": ("Evidence at line level, why your figure and theirs disagree, and how the difference "
          "gets settled without a fight."),
 "og": ("Your figure and their figure will differ. It is almost never arithmetic; it is almost "
        "always the definition of 'qualifying'."),
 "abstract": ("What a defensible claim contains, why the supplier's figure differs, how to "
              "reconcile without escalating, and the difference between a credit note and a "
              "deduction."),
 "lede": ("A claim that is a number in an email gets queried. A claim that is a number with the "
          "lines behind it gets paid, and usually without anybody reading the lines."),
 "tags": ["supplier rebates", "claims", "reconciliation", "evidence", "purchasing", "serverless"],
 "takeaways": [
  "Submit the line detail even though nobody asked for it.",
  "Expect a difference, and expect it to be about definitions.",
  "Reconcile before submitting, not after being queried.",
  "A credit note is cleaner than a deduction. Take the credit note.",
  "Submitted is halfway. Chase to received.",
 ],
 "blocks": [
  ("h2", "What goes in the claim"),
  ("fig", ("system", {
    "outside": [
      {"title": "The rule version", "sub": ["that applied,", "with dates"], "icon": "form"},
      {"title": "The qualifying lines", "sub": ["invoice, date,", "value"], "icon": "doc"},
      {"title": "The arithmetic", "sub": ["tier, rate,", "amount"], "icon": "counter"}],
    "inside": [
      {"title": "One claim document", "sub": ["their format,", "if they have one"], "icon": "report"},
      {"title": "Evidence attached", "sub": ["the lines, as a file"], "icon": "archive"},
      {"title": "Submitted and dated", "sub": ["with a chase clock", "started"], "icon": "clock"}],
    "edges": [{"from": 0, "to": 0, "label": "under these terms"},
              {"from": 1, "to": 1, "label": "on this evidence"},
              {"from": 2, "to": 2, "label": "for this amount", "up": True}],
    "note": "The evidence is rarely opened. Attaching it is what stops the query being raised at "
            "all."}),
   "The three things a claim is built from and what leaves the building. The middle box costs "
   "almost nothing to produce and removes most of the back-and-forth.",
   "The components of a defensible supplier rebate claim",
   "Three boxes across the top outside the AWS account. The rule version that applied, with "
   "dates. The qualifying lines, with invoice, date and value. And The arithmetic: tier, rate and "
   "amount. Each connects by an arrow to the AWS account container below, labelled under these "
   "terms, on this evidence, and for this amount. Inside the account are three components. One "
   "claim document in the supplier's format if they have one. Evidence attached, the lines as a "
   "file. And Submitted and dated, with a chase clock started. A note says the evidence is rarely "
   "opened and attaching it is what stops the query being raised at all."),
  ("h3", "Their format, if they have one"),
  ("p", "Larger suppliers have a portal or a template, and a claim submitted any other way joins "
        "a queue that is measured in months. It is worth the twenty minutes of finding out what "
        "the format is, once, and storing it against the agreement."),
  ("p", "Smaller suppliers have no format at all, and for them a one-page statement with a "
        "spreadsheet attached is more than they normally receive. Both cases are handled by the "
        "same rule field: how this supplier wants to be claimed from."),
  ("h2", "Why the figures differ"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Your gross", "parts": [("n", 148200)]},
      {"label": "After exclusions", "parts": [("n", 139400)]},
      {"label": "Their figure", "parts": [("n", 137900)]}],
    "series": [("n", "Qualifying spend, £", "#8C4FFF")],
    "unit": "",
    "note": "The remaining £1,500 is two credit notes they applied in a different period. That is "
            "a five-minute conversation, if you have the lines."}),
   "Three views of the same year's purchases. The first gap is your own exclusions; the second is "
   "timing, and it is small enough to settle by email.",
   "Gross purchases against qualifying spend and the supplier's figure",
   "A bar chart with three bars showing qualifying spend in pounds. Your gross: one hundred and "
   "forty-eight thousand two hundred. After exclusions: one hundred and thirty-nine thousand four "
   "hundred. Their figure: one hundred and thirty-seven thousand nine hundred. A note says the "
   "remaining fifteen hundred pounds is two credit notes they applied in a different period, "
   "which is a five-minute conversation if you have the lines."),
  ("p", "A business that claims on gross spend arrives at that conversation ten thousand pounds "
        "apart from the supplier and looks either careless or opportunistic. A business that has "
        "already applied the exclusions arrives fifteen hundred apart, which reads as two "
        "competent parties with a timing difference."),
  ("h3", "Reconcile before you submit"),
  ("p", "If the supplier publishes a statement of your purchases, compare it to your own figure "
        "before the claim goes out rather than after it comes back. The differences are almost "
        "always the same handful: a credit posted in the wrong period, a delivery invoiced after "
        "period end, one range you thought qualified and does not."),
  ("p", "Each of those is resolvable in one email when you raise it. Each of them is an argument "
        "when they raise it, because by then you have asserted a number you cannot support."),
  ("h2", "Credit note, not deduction"),
  ("callout", "Two ways to get paid, and why one is much better", [
   "<strong>A credit note</strong> is issued by the supplier, references your claim, and settles "
   "cleanly against your account.",
   "<strong>A deduction</strong> is you short-paying an invoice by the rebate amount and telling "
   "them why.",
   "<strong>Deductions feel faster</strong> and are, for about six weeks, until their credit "
   "control system treats you as being in arrears.",
   "<strong>Then it becomes two problems</strong>: an unresolved rebate and a payment dispute, "
   "and they are now handled by different people who do not talk.",
   "<strong>Take the credit note</strong>, and chase it like an invoice. It is the same money "
   "with none of the second problem.",
  ]),
  ("p", "The exception is a supplier who has ignored three claims and two chases, where a "
        "deduction with a clear explanation is a legitimate escalation. That is a decision by a "
        "person, taken deliberately, and it should never be something the system does on its own."),
  ("h3", "The claim is not the end"),
  ("p", "The average gap between a submitted rebate claim and a received credit note is measured "
        "in months, and the most common reason for a claim never being paid is that nobody "
        "followed it up after the first submission."),
  ("p", "Which is why the claim record carries a chase clock from the day it is submitted, exactly "
        "like an unpaid invoice, and why the reporting counts received rather than claimed."),
  ("p", "Next: making sure the window never closes on you."),
 ],
},
{
 "slug": "how-a-claim-window-gets-caught-in-time",
 "title": "How a claim window gets caught in time",
 "nav": "Windows and deadlines",
 "read": 5, "words": 750,
 "desc": ("Deadlines that come from documents nobody opens, the two-reminder pattern, and the "
          "annual sweep that finds what you forgot you had."),
 "og": ("A ninety-day claim window is not ninety days of opportunity. It is one date, and the "
        "eighty-nine days before it are when nobody thinks about it."),
 "abstract": ("Where claim deadlines come from, why two reminders work and daily ones do not, "
              "handling agreements you did not know existed, and what the annual sweep is for."),
 "lede": ("Missing a claim window is the purest loss in this whole area: the money was earned, "
          "the entitlement was real, and it evaporated because of a date."),
 "tags": ["supplier rebates", "deadlines", "reminders", "operations", "purchasing", "serverless"],
 "takeaways": [
  "The window is a date on the rule, with a countdown, not a paragraph in a PDF.",
  "Two reminders: one with time to prepare, one before it shuts.",
  "Aim for early in the window; late claims get queried more.",
  "Sweep the purchase ledger annually for suppliers with no agreement on file.",
  "A closed window is recorded as a loss, with a number.",
 ],
 "blocks": [
  ("h2", "Where the deadline lives"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "In the PDF", "sub": ["'within 90 days of", "period end'"], "icon": "doc",
       "label": "unfindable"},
      {"title": "In somebody's head", "sub": ["the person who", "negotiated it"], "icon": "person",
       "label": "leaves"},
      {"title": "On the rule", "sub": ["as a date, with", "a countdown"], "icon": "calendar",
       "label": "works"}],
    "target": {"title": "Two reminders", "sub": ["day 5 and day 60"], "icon": "bell",
               "then": {"title": "A claim, early", "sub": ["not on day 88"], "icon": "check"}},
    "note": "The same fact in three places. Only one of them survives a change of staff."}),
   "Three homes for a claim deadline. The system is not doing anything clever here; it is holding "
   "a date somewhere that does not depend on anybody remembering.",
   "Three places a rebate claim deadline can live",
   "Three boxes stacked on the left. In the PDF, within ninety days of period end, labelled "
   "unfindable. In somebody's head, the person who negotiated it, labelled leaves. And On the "
   "rule, as a date with a countdown, labelled works. All three converge on Two reminders, on day "
   "five and day sixty, which leads down to A claim, early, rather than on day eighty-eight. A "
   "note says the same fact in three places, and only one of them survives a change of staff."),
  ("h3", "Two reminders, not seven"),
  ("p", "The first arrives a few days after period end, when the ledger has settled and there is "
        "ample time to reconcile with the supplier before claiming. That is the one that produces "
        "a good claim."),
  ("p", "The second arrives with about a month left and is worded differently, because by then "
        "the question is not 'shall we prepare this' but 'this is going to expire'. Everything in "
        "between is noise that trains people to ignore the second one."),
  ("h2", "Early claims get queried less"),
  ("p", "A claim submitted in the first fortnight of a window arrives at a supplier who has just "
        "closed the period, has the data to hand, and has not yet received the other four hundred "
        "claims. The same claim on day eighty-five arrives into a backlog and gets scrutinised as "
        "part of clearing it."),
  ("p", "There is nothing formal about this and no supplier will admit to it, but the pattern is "
        "consistent enough to be worth designing around. Early is cheaper than late, in queries "
        "and in the time between claiming and being paid."),
  ("h2", "The agreements you do not know about"),
  ("fig", ("chain", {
    "entry": {"title": "Annual sweep", "sub": ["once a year,", "an afternoon"], "icon": "search"},
    "steps": [
      {"title": "Rank suppliers by spend", "sub": ["from the purchase", "ledger"], "icon": "chart"},
      {"title": "Which have a rule?", "sub": ["match by supplier"], "icon": "filter",
       "side": {"title": "The gap list", "sub": ["usually 4 to 9", "suppliers"], "icon": "report"}},
      {"title": "Ask each one", "sub": ["'what are our", "trade terms?'"], "icon": "email"},
      {"title": "Two answers", "sub": ["'none', or a PDF", "you never had"], "icon": "doc"}],
    "note": "Businesses that do this for the first time usually find at least one agreement they "
            "had entirely forgotten."}),
   "The sweep that finds entitlements nobody knew existed. It is a query against your own ledger "
   "and it takes an afternoon a year.",
   "An annual sweep for suppliers with significant spend and no rebate agreement",
   "A vertical chain of four steps entered by a box labelled Annual sweep, once a year, an "
   "afternoon. Step one, Rank suppliers by spend from the purchase ledger. Step two, Which have a "
   "rule, matched by supplier, with a side box labelled The gap list, usually four to nine "
   "suppliers. Step three, Ask each one what our trade terms are. Step four, Two answers: none, "
   "or a PDF you never had. A note says businesses doing this for the first time usually find at "
   "least one agreement they had entirely forgotten."),
  ("h3", "Asking is not embarrassing"),
  ("p", "Sending a supplier you spend sixty thousand a year with an email asking what your trade "
        "terms are is a completely normal thing to do, and the worst realistic outcome is that "
        "they say there is no rebate arrangement."),
  ("p", "The more common outcome is a reply attaching terms that were agreed with somebody who "
        "left in 2023, which is a document worth several thousand pounds a year that was sitting "
        "in a filing cabinet at the other end."),
  ("h2", "Record the misses"),
  ("callout", "What a closed window should leave behind", [
   "<strong>The agreement and the period</strong> it applied to.",
   "<strong>The amount</strong> that was accrued and not claimed, as a number.",
   "<strong>The date it closed</strong>, and what the last reminder was.",
   "<strong>Why</strong>, in one sentence, even if the sentence is 'nobody picked it up'.",
   "<strong>And it stays visible</strong>, because a total of missed rebate over two years is the "
   "only argument that reliably gets this work prioritised.",
  ]),
  ("p", "The instinct is to quietly delete a missed claim, because it is embarrassing and there "
        "is nothing to be done about it. That instinct is exactly why the same thing happens the "
        "following year."),
  ("h3", "What this system is really for"),
  ("p", "Almost nothing here is difficult. Rebate terms are simple arithmetic, the data is "
        "already in the purchase ledger, and the deadlines are printed in the agreements."),
  ("p", "The reason the money goes missing is that no single person is responsible for a set of "
        "facts spread across three inboxes, a finance system and one person's memory. Putting "
        "those facts in one place, with dates attached, is the entire intervention."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="agreement",
 volumes=[(10, "10 agreements"), (40, "40 agreements"), (150, "150 agreements")],
 read_each=0.0041,
 msgs_each=2.2,
 lede=("The model runs once per agreement and once per amendment -- a handful of times a year, "
       "not per purchase line. Forty agreements is a business with real trade terms across its "
       "supply base. Here is where each cent goes."),
 takeaway_extra=("Purchase lines are matched with arithmetic, not with a model, so the accrual "
                 "path stays free however much you buy."),
 risks=[
  "<strong>Re-reading every agreement on a schedule.</strong> They change once a year. Read on "
  "upload, not on a nightly job that quietly costs more than the rebates.",
  "<strong>Storing the full purchase ledger.</strong> Keep the qualifying lines and the totals; "
  "the ledger already lives in your finance system and does not need a second home.",
  "<strong>A reminder per agreement per day.</strong> Two reminders per window is the design. "
  "Daily mail is how the second one gets filtered.",
 ],
 per_unit_note=("The read is one call per agreement document against a small model, pulling five "
                "structured fields out of prose. Purchase lines never touch a model: matching a "
                "line to a rule is a comparison, and the moment you use a model for it you have "
                "made a cheap system expensive and a deterministic one unpredictable."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="rb",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, versioned rules, and the one model call."),
 outside=[
  {"title": "Agreements", "sub": ["PDFs and", "amendment letters"], "icon": "doc"},
  {"title": "Purchase lines", "sub": ["from the finance", "system, nightly"], "icon": "money"},
  {"title": "Buyer and finance", "sub": ["alerts, claims,", "the miss log"], "icon": "person"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["uploads,", "period clocks"], "icon": "bucket"},
  {"title": "Lambda x4", "sub": ["extract, accrue,", "alert, claim"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["rules, accruals"], "icon": "database"}],
 note="us-east-1. One account. Rules are versioned and never edited in place.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Agreements, arriving as PDFs and amendment "
  "letters. Purchase lines, from the finance system nightly. And Buyer and finance, receiving "
  "alerts, claims and the miss log. Inside the account, three groups. S3 for uploads and "
  "EventBridge for period clocks. Four Lambda functions named extract, accrue, alert and claim. "
  "And two DynamoDB tables named rules and accruals. A note gives the region as us-east-1, one "
  "account, and states that rules are versioned and never edited in place."),
 functions=[
  ["<code>rb-extract</code>", "S3 upload of an agreement or amendment",
   "One model call; writes a new dated rule version with the source page references",
   "60s / 1024&nbsp;MB"],
  ["<code>rb-accrue</code>", "EventBridge, nightly, after the ledger feed",
   "Matches lines to rules, applies exclusions, moves accruals, recomputes tier distance",
   "300s / 1024&nbsp;MB"],
  ["<code>rb-alert</code>", "EventBridge, weekly",
   "Raises tier-proximity alerts with weeks remaining and the value of the uplift",
   "60s / 512&nbsp;MB"],
  ["<code>rb-claim</code>", "EventBridge, daily; API on submit",
   "Fires the two window reminders, assembles the claim and its line evidence, chases to received",
   "120s / 1024&nbsp;MB"]],
 roles=[
  ["<code>rb-extract-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "One model id; the agreements prefix; rules"],
  ["<code>rb-accrue-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>", "Rules read; accruals write"],
  ["<code>rb-alert-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "Accruals; one verified identity"],
  ["<code>rb-claim-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>s3:PutObject</code>, <code>ses:SendEmail</code>",
   "Accruals; the claims prefix; one verified identity"]],
 tables=[
  ("Table: rules",
   "PK   supplier_id       S\n"
   "SK   effective_from#v  S   versions, never edited in place\n"
   "     basis             S   spend | units | growth\n"
   "     tiers             L   [{threshold, rate}], ascending\n"
   "     retrospective     BOOL null until somebody confirms it\n"
   "     period            S   calendar | financial | rolling-12\n"
   "     period_end        S\n"
   "     window_days       N   days after period end to claim\n"
   "     exclusions        L   freight | deal | range:<code> | unpaid\n"
   "     claim_format      S   portal | template | email\n"
   "     source_key        S   the original PDF in S3\n"
   "     source_pages      L   where each field was found, for disputes\n\n"
   "retrospective is deliberately nullable. A guess here is wrong half\n"
   "the time and changes the accrual by a factor of four."),
  ("Table: accruals",
   "PK   supplier_id#period S\n"
   "SK   '#state' | line#id S   one state item, one item per qualifying line\n"
   "     qualifying_total   N   state item; after exclusions\n"
   "     tier_achieved      N   index into the rule's tiers\n"
   "     earned             N   at the achieved tier only\n"
   "     next_tier_gap      N   what the alert is built from\n"
   "     claimed_at         S\n"
   "     claimed_amount     N\n"
   "     received_at        S   the number that actually counts\n"
   "     received_amount    N\n"
   "     window_closes      S\n"
   "     missed_amount      N   set when a window closes unclaimed\n"
   "     missed_reason      S   required, even if it is 'nobody picked it up'\n\n"
   "earned, claimed_amount and received_amount are three separate fields\n"
   "on purpose. Collapsing them is how a claim stops being followed up.")],
 inbound=[
  "<strong>Purchase lines arrive nightly</strong> as a feed from the finance system. This is not "
  "a real-time system and pretending otherwise adds a integration for no decision.",
  "<strong>Agreements arrive by upload</strong>, which is the only manual step and the only one "
  "worth keeping manual.",
  "<strong>Alerts go to the buyer</strong>, claims and windows go to finance. They are different "
  "people with different deadlines and merging the mail loses both.",
  "<strong>The miss log is never purged.</strong> A running total of unclaimed rebate is the only "
  "thing that reliably gets this work resourced."],
 model_notes=[
  "<strong>One call per agreement document.</strong> Five fields out of three pages of prose that "
  "no two suppliers write the same way.",
  "<strong>A small, fast model.</strong> This is extraction from a short document; a frontier "
  "model returns the same five fields for eight times the money.",
  "<strong>Nulls are required, not tolerated.</strong> A missing retrospective flag becomes a "
  "question to a human, never an inference.",
  "<strong>Page references come back with the fields</strong>, so a disputed term can be checked "
  "against the original sentence in seconds.",
  "<strong>Nothing else calls a model.</strong> Matching lines, applying exclusions and computing "
  "tiers is arithmetic, and arithmetic that can be checked by hand is worth more here than "
  "anything a model could add."],
 gotchas=[
  "Version rules by effective date and never edit one. A mid-year amendment means a single period "
  "evaluated under two rules, and an in-place edit silently loses half the year.",
  "Apply exclusions at line level from day one. Accruing on gross spend puts you ten thousand "
  "pounds apart from the supplier at claim time and makes every claim a negotiation.",
  "Accrue only the tier already achieved. Optimistic accrual inflates margin all year and "
  "reverses in one month that then looks like a trading problem.",
  "Send the tier alert six to eight weeks out. Two weeks out it produces a panic buy at the wrong "
  "price, which is worse than missing the tier.",
  "Track received, not claimed. A submitted claim behaves exactly like an unpaid invoice and dies "
  "the same way, quietly, in somebody else's queue."],
))
