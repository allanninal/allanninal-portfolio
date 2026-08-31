"""Day 80 -- 2026-07-13 -- Subscription audit bot."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "subscription-audit-bot"
NAME = "Subscription audit bot"

SPEC = {
 "slug": SLUG, "date": "2026-07-13", "name": NAME,
 "tagline": ("Every recurring charge on the company card gets recognised, matched to an owner "
             "and a purpose, and questioned once a year -- so the tool nobody has opened since "
             "March stops renewing quietly."),
 "lede": ("A small system that watches the card and bank feed for recurring charges, groups "
          "them into subscriptions, works out who owns each one and what it is for, and asks "
          "that person a single question before each renewal. It cannot cancel anything and "
          "does not try. Seven posts on the same system -- one diagram at a time -- with a "
          "cost breakdown and an engineering reference at the end."),
 "keywords": ["SaaS spend", "subscription management", "recurring charges", "cost control",
              "human in the loop", "serverless"],
 "icons": ["money", "search", "calendar"],
 "faq": [
  ("What is a subscription audit bot?",
   "A small serverless system that reads your card and bank feed, spots the charges that "
   "repeat, groups them into subscriptions with an owner and a purpose, and asks the owner one "
   "question shortly before each renewal. It never cancels anything; it makes the decision "
   "visible while there is still time to make it."),
  ("Why not just look at the card statement?",
   "Because a statement is a flat list of charges and a subscription is a pattern across "
   "months. A £14 charge in March means nothing; the same £14 charge in twelve consecutive "
   "months from a merchant nobody recognises is £168 a year and a question. Spotting the "
   "pattern is the work."),
  ("How does it know who owns a subscription?",
   "Three ways, in order: an owner tab you fill in as things are found, the person whose card "
   "it is on, and -- if neither is available -- it asks. An unowned subscription is the most "
   "common finding in the first month and the most valuable one."),
  ("Can it cancel anything?",
   "No. It has no credentials to any of these services and deliberately never will. Its whole "
   "output is a question to a person before a renewal, and a record of what they said."),
  ("What does it cost to run?",
   "A few dollars a month. The volume is a few hundred transactions a month, which is nothing. "
   "See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "subscription-audit-bot-on-aws",
 "title": "A subscription audit bot on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 940,
 "desc": ("Finds recurring charges in the card feed, groups them into subscriptions with an "
          "owner and a purpose, and asks one question before each renewal. AWS, about $3 a "
          "month."),
 "og": ("Spots the charges that repeat, groups them into subscriptions, works out who owns "
        "each one, and asks that person a single question before the next renewal."),
 "abstract": ("The whole system on one page -- a grouper, an attributor and an asker -- plus "
              "the constraint that keeps it safe: it holds no credentials and can cancel "
              "nothing."),
 "lede": ("Every business past about eight people has a number it cannot state: what it spends "
          "on software a year. Not because the charges are hidden &mdash; they are all on the "
          "card statement &mdash; but because a statement is a flat list of hundreds of "
          "charges and a subscription is a pattern across months. The £14 that appears every "
          "month from a merchant nobody recognises is £168 a year, and there are usually eleven "
          "of them. This post walks through a small system that finds the patterns and asks "
          "one question about each of them, once a year, before it renews."),
 "tags": ["SaaS spend", "subscription management", "cost control", "recurring charges",
          "human in the loop", "serverless"],
 "takeaways": [
  "One input: the card and bank feed you already export or already get emailed.",
  "Charges are grouped into subscriptions by merchant, amount and interval -- not by name alone.",
  "Every subscription gets an owner and a purpose, or the lack of one becomes a question.",
  "The only action is a question before a renewal. It holds no credentials and cancels nothing.",
  "Designed on AWS for about $3 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Card + bank feed", "sub": ["export or emailed CSV"], "icon": "money"},
      {"title": "Owner tab", "sub": ["who owns what, why"], "icon": "doc"},
      {"title": "Owners", "sub": ["one question a year"], "icon": "team"}],
    "inside": [
      {"title": "Grouper", "sub": ["charges into", "subscriptions"], "icon": "search"},
      {"title": "Attributor", "sub": ["owner, purpose,", "annual cost"], "icon": "filter"},
      {"title": "Asker", "sub": ["before renewal,", "once"], "icon": "calendar"}],
    "edges": [{"from": 0, "to": 0, "label": "transactions in"},
              {"from": 1, "to": 1, "label": "who owns what"},
              {"from": 2, "to": 2, "label": "keep or drop?", "up": True}],
    "note": "No credentials to any of these services, ever. The only output is a question."}),
   "One input, three pieces, and a hard boundary. The system reads a transaction feed and "
   "sends questions; it never holds a login to anything it is auditing.",
   "System: a card feed in, three pieces inside AWS, questions out",
   "Three boxes across the top sit outside the AWS account. On the left, Card and bank feed: "
   "the export or emailed CSV the business already receives. In the middle, Owner tab: the "
   "sheet recording who owns each subscription and why. On the right, Owners: the people who "
   "get one question a year. Each connects by an arrow to the AWS account container below. "
   "Transactions flow down into the account. The owner tab feeds in to say who owns what. The "
   "owners receive a keep-or-drop question. Inside the AWS account are three components in a "
   "row. On the left, the Grouper, which turns individual charges into subscriptions. In the "
   "middle, the Attributor, which attaches an owner, a purpose and an annual cost to each. On "
   "the right, the Asker, which sends a single question before each renewal. A note at the "
   "bottom says the system holds no credentials to any of these services and its only output is "
   "a question."),
  ("h3", "What you set up once (the outside)"),
  ("ul", [
   "<strong>A transaction feed.</strong> Whatever you already have: a monthly CSV export from "
   "the bank, a card provider that emails statements, or an Open Banking feed if you have one. "
   "Covered in Part 2. It needs the date, the amount, the merchant string and the card, and "
   "nothing else.",
   "<strong>An owner tab.</strong> Starts empty. As subscriptions are found, somebody writes "
   "down who owns each one and what it is for, in a sentence. Filling this in for the first "
   "time is a couple of hours of archaeology and it is the most valuable couple of hours in "
   "the whole project.",
   "<strong>A question window.</strong> How long before a renewal to ask, and how often to ask "
   "about the same subscription. Thirty days before an annual renewal is the useful default; "
   "monthly subscriptions get asked about once a year rather than twelve times, which is the "
   "single most important setting in the system.",
  ]),
  ("h3", "What runs on every feed (the inside)"),
  ("ul", [
   "<strong>The grouper.</strong> Reads the transactions and finds the ones that repeat. This "
   "is harder than it sounds: merchant strings vary between charges, amounts change with "
   "seat counts and currency, and intervals drift by days. Part 3 is entirely about this.",
   "<strong>The attributor.</strong> Attaches three things to each subscription: an owner, a "
   "purpose, and the true annual cost. The annual cost is the number that changes minds &mdash; "
   "\"£14 a month\" and \"£168 a year\" are the same fact and produce different decisions.",
   "<strong>The asker.</strong> Sends one message to the owner before a renewal, with the "
   "annual figure, what they said last time, and three buttons. It asks once per subscription "
   "per year, which is what makes it survivable. A system that asks about eleven subscriptions "
   "every month gets filtered to a folder in six weeks.",
  ]),
  ("h2", "One subscription, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Charged", "sub": ["£14, a merchant"], "icon": "money"},
      {"title": "Grouped", "sub": ["seen it 11 times"], "icon": "search"},
      {"title": "Named", "sub": ["what it actually is"], "icon": "tag"},
      {"title": "Owned", "sub": ["a person and a purpose"], "icon": "person"},
      {"title": "Asked", "sub": ["30 days before renewal"], "icon": "calendar"}],
    "title": "ONE SUBSCRIPTION, END TO END",
    "note": "The third and fourth stages are where a line on a statement becomes a decision."}),
   "The same system as one line. The transition that matters is from a charge to a named thing "
   "with an owner &mdash; everything before that is bookkeeping and everything after is a "
   "decision.",
   "One subscription from first charge to renewal question, in five stages",
   "A horizontal row of five boxes joined by arrows. Charged: fourteen pounds to some merchant. "
   "Grouped: the same charge has been seen eleven times. Named: worked out to be an actual "
   "product. Owned: attached to a person and a purpose. Asked: a question sent thirty days "
   "before the renewal. A note says the third and fourth stages are where a line on a statement "
   "becomes a decision."),
  ("h2", "In plain words"),
  ("p", "There is a £14.40 charge on the company card every month from \"SP * PROJTOOL\". Ten "
        "months of them. Nobody at the company can tell you what it is from the statement line, "
        "and nobody has ever had a reason to try, because £14.40 is beneath the threshold at "
        "which anybody investigates anything. The grouper spots the repetition, the attributor "
        "works out from the merchant string and a lookup that it is a project management tool, "
        "and finds no owner for it in the tab. So it asks the person whose card it is: "
        "\"£14.40/month, £172.80 a year, going to PROJTOOL since September. Who owns this and "
        "what is it for?\""),
  ("p", "The answer, roughly forty per cent of the time in the first pass, is \"I have no idea, "
        "I think that was for the website rebuild\". The rebuild finished in February. That is "
        "£172.80 a year that stops, and it stopped because somebody was asked a question about "
        "a named thing with an annual figure attached, rather than shown a statement line. "
        "There are usually between six and fifteen of these in a business that has been running "
        "five years, and finding them all in the first month is what pays for the project "
        "roughly two hundred times over."),
  ("callout", "Design rules that shaped every decision", [
   "It holds no credentials. Not to the bank beyond a read-only feed, and to none of the "
   "services it audits. It cannot cancel and will never be able to.",
   "Ask once a year, not once a month. A system that asks eleven questions a month gets "
   "filtered, and a filtered system finds nothing.",
   "Always state the annual figure. Fourteen pounds a month and a hundred and sixty-eight "
   "pounds a year are the same fact and produce different decisions.",
   "An unowned subscription is a finding, not an error. It is usually the most valuable output "
   "of the entire system.",
   "Group on behaviour, not on merchant name. Merchant strings are inconsistent and amounts "
   "change; the pattern is the interval.",
   "\"Keep\" is a first-class answer and is recorded. The next question a year later says what "
   "was decided last time.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The usual approaches are an annual spreadsheet exercise, which happens once and then "
        "does not, or a SaaS-management platform, which wants admin credentials to your "
        "identity provider and costs more than several of the subscriptions it will find. Both "
        "fail for the same underlying reason: the work is not finding the charges, which are "
        "all right there on the statement. The work is turning a repeated charge into a named "
        "thing with an owner, and then asking that owner at the one moment in the year when the "
        "answer can change anything."),
  ("p", "So the design does almost nothing except that. It reads a feed you already get, it "
        "does the pattern-matching nobody has time for, and it converts each pattern into "
        "exactly one well-timed question. It cannot act, which is not a limitation &mdash; it "
        "is what makes it safe to point at every card in the business."),
  ("p", "The next four posts walk through each piece: how the feed arrives, how charges get "
        "grouped, how a subscription gets an owner, and how the renewal question works. One "
        "diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-the-transaction-feed-arrives",
 "title": "How the transaction feed arrives",
 "nav": "How the feed arrives",
 "read": 5, "words": 840,
 "desc": ("Three ways a card feed turns up, why a read-only feed is the hard boundary, and "
          "how re-uploading last month's export does not double every charge."),
 "og": ("Three lanes for a transaction feed, one hard boundary -- read-only, always -- and a "
        "line-level fingerprint so a re-uploaded export cannot double anything."),
 "abstract": ("Three lanes for a transaction feed and one hard boundary: read-only, always. "
              "Plus the line-level fingerprint that makes re-uploading an overlapping export "
              "harmless."),
 "lede": ("This system reads money movements, which makes the intake the part worth being "
          "careful about. Everything here is designed around one rule that never bends: "
          "whatever the feed is, it is read-only, and the system holds nothing that could move "
          "money or change a subscription."),
 "tags": ["subscription management", "bank feeds", "CSV import", "idempotency", "least privilege",
          "serverless"],
 "takeaways": [
  "Three lanes: a CSV drop, an emailed statement, and a read-only Open Banking feed.",
  "Read-only is a hard boundary. No payment scope, no admin credentials to anything.",
  "Every line gets a fingerprint, so overlapping exports cannot double a charge.",
  "The merchant string is kept raw as well as cleaned, because cleaning loses information.",
  "Foreign-currency charges keep both amounts; grouping needs the billed one.",
 ],
 "blocks": [
  ("h2", "Three lanes, one boundary"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "CSV drop", "sub": ["monthly export"], "icon": "chart", "label": "file"},
      {"title": "Emailed statement", "sub": ["from the card provider"], "icon": "email",
       "label": "attach"},
      {"title": "Open Banking feed", "sub": ["read-only scope"], "icon": "link", "label": "api"}],
    "target": {"title": "One transaction row", "sub": ["date, amount, merchant,", "card, currency"],
               "icon": "database",
               "then": {"title": "Grouper", "sub": ["find what repeats"], "icon": "search"}},
    "note": "Whatever the lane, the scope is read. Nothing here can move money."}),
   "Three ways a feed arrives and one row shape. The Open Banking lane is the only one with a "
   "credential attached, and its scope is read-only by design and by grant.",
   "Three transaction feed lanes converging on one row shape",
   "Three boxes stacked on the left. CSV drop, a monthly export placed in a folder. Emailed "
   "statement, arriving as an attachment from the card provider. And Open Banking feed, an API "
   "with a read-only scope. Their arrows are labelled file, attach and api, converging on One "
   "transaction row holding the date, the amount, the merchant string, the card and the "
   "currency. Below it, connected by a downward arrow, is the Grouper, which finds what "
   "repeats. A note says whatever the lane, the scope is read, and nothing here can move money."),
  ("h3", "Why read-only is stated so heavily"),
  ("p", "Because the obvious next feature is not read-only. Once a system can see that a "
        "subscription should be cancelled, the natural request is for it to cancel it, and that "
        "requires either payment-level access to the card or admin credentials to a dozen "
        "third-party services. Either turns a small useful tool into a serious piece of "
        "security surface for a saving that a person can realise in ninety seconds by clicking "
        "cancel themselves."),
  ("p", "So the boundary is stated in the design rather than left as an implementation detail. "
        "The IAM roles in Part 7 have no write path to anything financial, the Open Banking "
        "grant requests only the transactions scope, and there is no credential store for the "
        "audited services because there is nothing to store."),
  ("h2", "The row, and the fingerprint"),
  ("pre", "date         2026-07-02\n"
          "amount       14.40           in the billed currency\n"
          "currency     GBP\n"
          "orig_amount  17.99           if the charge was in another currency\n"
          "orig_ccy     USD\n"
          "merchant_raw SP * PROJTOOL   exactly as it appeared\n"
          "merchant     projtool        cleaned, for grouping\n"
          "card         ****4417\n"
          "fingerprint  sha256(date|amount|merchant_raw|card)"),
  ("p", "The fingerprint is the whole answer to overlapping exports, which happen constantly. "
        "Somebody re-downloads a statement to check something and drops it in the folder. A "
        "monthly export includes three days of the previous month. An Open Banking feed "
        "backfills. All three would otherwise double charges and destroy the grouping, because "
        "a subscription that appears to be charged twice a month is a different pattern."),
  ("h3", "Why the raw merchant string is kept"),
  ("p", "Cleaning a merchant string loses information, and sometimes the lost information is "
        "the answer. <code>SP * PROJTOOL</code> cleans to <code>projtool</code>, which is "
        "right and useful for grouping. But <code>SP *</code> is a payment-processor prefix, "
        "and knowing that the charge went through that processor is occasionally the only way "
        "to work out what a merchant actually is. So both are stored, grouping uses the clean "
        "one, and the question sent to a human quotes the raw one &mdash; because that is what "
        "they will recognise from their own statement."),
  ("h2", "Foreign currency, and why it matters here"),
  ("ul", [
   "<strong>Group on the original amount, not the billed one.</strong> A $17.99 subscription "
   "bills at £14.40 one month and £14.02 the next because the rate moved. Grouping on the "
   "billed figure sees two different subscriptions; grouping on the original sees one.",
   "<strong>Report the billed amount.</strong> The annual figure in the question is what "
   "actually left the account, because that is the number the owner is being asked to justify.",
   "<strong>A currency change is a signal.</strong> A subscription that stops being billed in "
   "dollars and starts being billed in pounds usually means the provider opened a local entity "
   "&mdash; and frequently means the price changed at the same time.",
   "<strong>Never guess a rate.</strong> If the export does not carry the original amount, the "
   "system uses the billed amount with a wider grouping tolerance rather than inventing a "
   "conversion.",
  ]),
  ("p", "Next: how a set of similar-looking charges becomes one subscription."),
 ],
},
{
 "slug": "how-charges-become-a-subscription",
 "title": "How charges become a subscription",
 "nav": "How grouping works",
 "read": 6, "words": 900,
 "desc": ("Grouping on interval rather than name, the four patterns worth recognising, why "
          "annual subscriptions are the hard case, and what a broken pattern usually means."),
 "og": ("Merchant names lie and amounts drift, so grouping is done on interval. Four patterns "
        "cover almost everything, and annual subscriptions are the hard and valuable case."),
 "abstract": ("Merchant names are inconsistent and amounts drift, so grouping happens on "
              "interval. Four patterns cover almost everything, and the annual one is both the "
              "hardest to spot and the most worth spotting."),
 "lede": ("This is the only genuinely interesting algorithm in the series, and it is still not "
          "very interesting &mdash; which is the point. Finding subscriptions in a transaction "
          "feed is a clustering problem that people reach for machine learning to solve and "
          "that is better solved by noticing that subscriptions are, by definition, charges "
          "that happen at regular intervals."),
 "tags": ["subscription management", "pattern detection", "recurring charges", "DynamoDB",
          "cost control", "serverless"],
 "takeaways": [
  "Grouping is on interval regularity, not merchant name similarity.",
  "Four patterns: monthly, annual, quarterly, and per-seat monthly with a drifting amount.",
  "Annual subscriptions need two years of feed to see, and they are the expensive ones.",
  "A pattern that breaks is a finding: a price rise, a cancellation, or a failed payment.",
  "Two charges is a coincidence. Three at a regular interval is a subscription.",
 ],
 "blocks": [
  ("h2", "Group on interval, not on name"),
  ("p", "The instinct is to group by merchant: put all the charges from the same place together "
        "and see which repeat. It works badly, because merchant strings for the same service "
        "vary between charges &mdash; a processor prefix appears and disappears, a city is "
        "appended, a reference number is included. Meanwhile genuinely different things share a "
        "merchant, because one payment processor fronts hundreds of small services."),
  ("fig", ("chain", {
    "entry": {"title": "All transactions", "sub": ["24 months if you have it"], "icon": "money"},
    "steps": [
      {"title": "Bucket by cleaned merchant", "sub": ["a rough first pass"], "icon": "search"},
      {"title": "Within a bucket, by amount", "sub": ["exact, then +/- 15%"], "icon": "filter"},
      {"title": "Intervals regular?", "sub": ["gaps within a few days"], "icon": "branch",
       "exit": {"title": "Not a subscription", "sub": ["leave it alone"], "icon": "stop",
                "label": "irregular"}},
      {"title": "Three or more?", "sub": ["two is a coincidence"], "icon": "branch",
       "exit": {"title": "Watch it", "sub": ["not enough yet"], "icon": "clock",
                "label": "two"}},
      {"title": "A subscription", "sub": ["interval, amount,", "next expected date"],
       "icon": "calendar"}],
    "note": "Everything here is arithmetic on dates. No model is involved in finding a subscription."}),
   "How a set of charges becomes a subscription. Bucketing by merchant is only a first pass; "
   "the actual test is whether the gaps between charges are regular.",
   "How repeated charges are grouped into a subscription",
   "A vertical chain of five steps entered by a box labelled All transactions, covering "
   "twenty-four months if available. Step one buckets by cleaned merchant name as a rough "
   "first pass. Step two subdivides within a bucket by amount, exactly first and then within "
   "fifteen per cent. Step three asks whether the intervals are regular, with gaps within a few "
   "days of each other; irregular charges exit to Not a subscription and are left alone. Step "
   "four asks whether there are three or more charges, since two is a coincidence; two exits to "
   "Watch it, as not enough yet. Step five declares a subscription with its interval, amount "
   "and next expected date. A note says everything here is arithmetic on dates and no model is "
   "involved in finding a subscription."),
  ("h2", "The four patterns"),
  ("table", ["Pattern", "Looks like", "Why it needs its own handling"], [
   ["Monthly", "Same amount, gaps of 28&ndash;31 days",
    "The easy case. Three charges is enough to be confident."],
   ["Annual", "Same amount, gaps of 360&ndash;370 days",
    "Needs two years of feed to see three charges. Usually the largest amounts."],
   ["Quarterly", "Same amount, gaps of 88&ndash;95 days",
    "Easily mistaken for irregular spending on a short feed."],
   ["Per-seat monthly", "Monthly gaps, amount rising in steps",
    "Amount changes as headcount changes, so exact-amount grouping misses it entirely."],
  ]),
  ("h3", "Why annual is the hard and valuable case"),
  ("p", "Annual subscriptions are where the money is &mdash; they are typically five to ten "
        "times the value of a monthly one and are exactly the ones nobody remembers. They are "
        "also the hardest to detect, because seeing three charges takes two years of "
        "transaction history, and most businesses can only export twelve or eighteen months."),
  ("p", "So annual gets a relaxed rule: two charges roughly a year apart, from the same "
        "merchant, for the same amount, is treated as a probable annual subscription rather "
        "than waiting for a third. It is flagged as probable in the question, which is honest "
        "and costs nothing &mdash; \"this looks like an annual subscription, renewing about the "
        "14th of next month\" is a perfectly actionable sentence even when the system is only "
        "reasonably sure."),
  ("h2", "When a pattern breaks"),
  ("p", "A subscription that stops behaving is at least as interesting as one that starts, and "
        "there are three cases worth telling apart."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Amount rose", "sub": ["a price increase"], "icon": "money"},
      {"title": "Charge missing", "sub": ["cancelled, or failed"], "icon": "alarm"},
      {"title": "Interval halved", "sub": ["moved to monthly"], "icon": "clock"},
      {"title": "New merchant", "sub": ["provider renamed"], "icon": "tag"},
      {"title": "One question", "sub": ["with what changed"], "icon": "bell"}],
    "title": "FOUR WAYS A SUBSCRIPTION CHANGES",
    "note": "A missing charge is the ambiguous one: a cancellation and a failed payment look identical."}),
   "The four ways an established subscription stops behaving, and why the missing charge needs "
   "a question rather than an assumption.",
   "Four ways an established subscription changes, and the resulting question",
   "A horizontal row of five boxes. Amount rose: a price increase. Charge missing: either a "
   "cancellation or a failed payment. Interval halved: the subscription moved from annual to "
   "monthly. New merchant: the provider renamed or moved processor. One question: sent with a "
   "description of what changed. A note says a missing charge is the ambiguous one, because a "
   "cancellation and a failed payment look identical from a transaction feed."),
  ("ul", [
   "<strong>A price rise</strong> is the most common and the most quietly expensive. Software "
   "prices rise annually and nobody notices a monthly charge moving from £14.40 to £17.20. "
   "Stated as \"up 19%, £33.60 a year more\", it is a decision.",
   "<strong>A missing charge</strong> is genuinely ambiguous. Somebody cancelled it, or the "
   "card expired and the payment failed. Those need completely different responses, and the "
   "feed cannot tell them apart, so it asks: \"no charge from PROJTOOL this month &mdash; did "
   "we cancel, or has the payment failed?\"",
   "<strong>An interval change</strong> almost always means somebody switched from annual to "
   "monthly billing, which usually costs about twenty per cent more per year. Worth a sentence.",
   "<strong>A new merchant string</strong> for the same amount and interval is a rename, and "
   "recognising it as the same subscription rather than a new one preserves the history and "
   "the owner.",
  ]),
  ("p", "Next: how a subscription gets an owner and a purpose, which is where the money actually "
        "gets saved."),
 ],
},
{
 "slug": "how-a-subscription-gets-an-owner",
 "title": "How a subscription gets an owner",
 "nav": "How it gets an owner",
 "read": 5, "words": 860,
 "desc": ("Three ways to attribute a subscription, why an unowned one is the most valuable "
          "finding, and how the merchant string becomes an actual product name."),
 "og": ("An unowned subscription is not a failure of the system; it is usually the finding "
        "that pays for it. Three ways to attribute one, and how a merchant string becomes a "
        "product name."),
 "abstract": ("Three ways to attribute a subscription, how a merchant string becomes an actual "
              "product name, and why an unowned subscription is the most valuable output the "
              "system has."),
 "lede": ("Everything up to here has been mechanical. This is the part with judgement in it, "
          "and it is also the part that produces the money. A charge with no owner is not a "
          "bug in the data; it is very often a real thing that nobody has been responsible for "
          "in three years, and finding it is the point of the exercise."),
 "tags": ["subscription management", "cost control", "AWS Bedrock", "attribution",
          "human in the loop", "serverless"],
 "takeaways": [
  "Three ways to attribute: the owner tab, the cardholder, and asking.",
  "The merchant string is resolved to a product name so the question is answerable.",
  "An unowned subscription is a finding, and usually the most valuable one.",
  "The annual figure is attached to everything, always. It is what changes decisions.",
  "A resolved owner is written back to the tab, so the archaeology only happens once.",
 ],
 "blocks": [
  ("h2", "Three ways to find an owner"),
  ("fig", ("chain", {
    "entry": {"title": "A subscription", "sub": ["merchant, amount, interval"], "icon": "calendar"},
    "steps": [
      {"title": "In the owner tab?", "sub": ["matched on merchant"], "icon": "branch",
       "side": {"title": "Owner tab", "sub": ["filled in over time"], "icon": "doc"},
       "exit": {"title": "Owned", "sub": ["name and purpose"], "icon": "check", "label": "yes"}},
      {"title": "Whose card is it?", "sub": ["from the card list"], "icon": "branch",
       "side": {"title": "Card list", "sub": ["card to person"], "icon": "money"},
       "exit": {"title": "Provisionally owned", "sub": ["ask them to confirm"], "icon": "person",
                "label": "known card"}},
      {"title": "What is the merchant?", "sub": ["one Bedrock call"], "icon": "model",
       "side": {"title": "Known merchants", "sub": ["seen before, resolved"], "icon": "database"}},
      {"title": "Unowned", "sub": ["a real finding,", "with an annual figure"], "icon": "alarm"}],
    "note": "The last box is not an error state. It is what the first pass mostly produces."}),
   "Attribution in three steps with a deliberate fourth outcome. Unowned is the expected result "
   "of a first pass and the reason the system is worth running.",
   "How a subscription is attributed to an owner",
   "A vertical chain of four steps entered by a box labelled A subscription, carrying merchant, "
   "amount and interval. Step one asks whether it is in the owner tab, matched on merchant; a "
   "hit exits to Owned, with a name and a purpose. Step two asks whose card it is, using the "
   "card list mapping cards to people; a known card exits to Provisionally owned, with the "
   "cardholder asked to confirm. Step three asks what the merchant actually is, using a single "
   "Bedrock call grounded by a table of merchants already resolved. Step four is Unowned, a "
   "real finding carrying an annual figure. A note says the last box is not an error state and "
   "is what the first pass mostly produces."),
  ("h3", "Turning a merchant string into a product"),
  ("p", "\"SP * PROJTOOL\", \"FS *NOTIONLABS\", \"PADDLE.NET* ACME\" and \"STRIPE *CO 4471\" "
        "are all real shapes of statement line, and the last one is genuinely unresolvable "
        "&mdash; it tells you a payment processor and a reference and nothing else. Resolution "
        "goes in three steps: an exact match against merchants already resolved for this "
        "business, a match against a small built-in list of common processor prefixes and "
        "well-known services, and then one model call with the raw string."),
  ("p", "The model's job is narrow: given a statement descriptor, name the likely product and "
        "say how confident it is. It is grounded with the merchants this business has already "
        "resolved, so the second occurrence of anything is free and certain. Where it cannot "
        "name a product, it says so, and the question to a human quotes the raw descriptor "
        "&mdash; which is fine, because a person looking at \"STRIPE *CO 4471\" on their own "
        "card statement often recognises it instantly from context the system does not have."),
  ("h2", "Why unowned is the valuable outcome"),
  ("p", "In a first pass over two years of feed at a business of about thirty people, a typical "
        "result is forty to sixty distinct subscriptions, of which somewhere between a quarter "
        "and a half have no identifiable owner. That is not a data quality problem. Those are "
        "real recurring payments that no living person is responsible for."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Found", "sub": ["52 subscriptions"], "icon": "search"},
      {"title": "Owned already", "sub": ["18"], "icon": "check"},
      {"title": "Cardholder knew", "sub": ["21"], "icon": "person"},
      {"title": "Nobody knew", "sub": ["13"], "icon": "alarm"},
      {"title": "Stopped", "sub": ["9, £4,100/yr"], "icon": "money"}],
    "title": "A TYPICAL FIRST PASS",
    "note": "The fourth number is the finding. The fifth is why anybody builds this."}),
   "What a first pass over two years of transactions typically produces. The thirteen nobody "
   "recognised are the reason the system exists.",
   "The result of a typical first subscription audit pass",
   "A horizontal row of five boxes. Found: fifty-two subscriptions. Owned already: eighteen "
   "were in the owner tab. Cardholder knew: twenty-one were recognised by whoever's card they "
   "were on. Nobody knew: thirteen had no identifiable owner. Stopped: nine were cancelled, "
   "worth four thousand one hundred pounds a year. A note says the fourth number is the finding "
   "and the fifth is why anybody builds this."),
  ("h3", "The annual figure, everywhere"),
  ("p", "Every subscription carries an annual cost from the moment it is recognised, and every "
        "message states it. This is the smallest change in the whole design with the largest "
        "effect on outcomes. \"£14.40 a month\" reads as trivial and gets a shrug. \"£172.80 a "
        "year\" reads as a number and gets a decision. They are the same fact."),
  ("p", "For a probable annual subscription seen only twice, the annual figure is simply the "
        "charge. For a per-seat subscription with a drifting amount, it is twelve times the most "
        "recent charge, stated as \"about\", with the trend noted if it has risen more than ten "
        "per cent over the year &mdash; because a per-seat tool growing with headcount is a "
        "completely different conversation from one that is not."),
  ("callout", "Writing the answer back", [
   "Every confirmed owner and purpose is written back to the owner tab, so the same archaeology "
   "never happens twice.",
   "Every resolved merchant string is written to the known-merchants table, so the second "
   "occurrence costs no model call and carries no uncertainty.",
   "A \"nobody knows\" answer is also written down, with the date. A subscription that has been "
   "unowned for two consecutive years and is still being paid is its own kind of finding.",
   "The tab is the record, not the database. If this system is switched off tomorrow, the "
   "useful output -- a list of what you pay for and why -- survives in a spreadsheet.",
  ]),
  ("p", "Next: the renewal question itself, and why asking once a year is the whole design."),
 ],
},
{
 "slug": "how-the-renewal-question-works",
 "title": "How the renewal question works",
 "nav": "How it asks",
 "read": 5, "words": 830,
 "desc": ("One question per subscription per year, timed to land before the renewal, with "
          "what was said last time -- and why asking more often destroys the system."),
 "og": ("Once a year, thirty days before renewal, with last year's answer quoted. Asking more "
        "often is the single fastest way to make this system worthless."),
 "abstract": ("One question per subscription per year, timed to land thirty days before the "
              "renewal, quoting what was said last time -- and why asking more often destroys "
              "the whole thing."),
 "lede": ("The temptation with a system that can see every recurring charge is to report on all "
          "of them, regularly. That instinct is exactly wrong, and resisting it is the "
          "difference between a tool people act on and a monthly email that goes to a folder. "
          "This post is about restraint as a design feature."),
 "tags": ["subscription management", "notifications", "Amazon SES", "cost control", "scheduling",
          "serverless"],
 "takeaways": [
  "One question per subscription per year, whatever its billing interval.",
  "Timed for thirty days before renewal, because that is when the answer can change something.",
  "The message quotes last year's answer, which makes \"keep\" a real decision rather than inertia.",
  "Three buttons: keep, drop, and I do not know what this is.",
  "A monthly digest exists but carries only what changed -- never the full list.",
 ],
 "blocks": [
  ("h2", "Once a year, thirty days out"),
  ("fig", ("system", {
    "outside": [
      {"title": "Owner", "sub": ["one question a year"], "icon": "person"},
      {"title": "Whoever pays", "sub": ["a monthly digest"], "icon": "money"},
      {"title": "Owner tab", "sub": ["answers written back"], "icon": "doc"}],
    "inside": [
      {"title": "Scheduler", "sub": ["next renewal,", "minus 30 days"], "icon": "clock"},
      {"title": "Question builder", "sub": ["annual figure,", "last year's answer"], "icon": "email"},
      {"title": "Recorder", "sub": ["what was decided,", "and when"], "icon": "log"}],
    "edges": [{"from": 0, "to": 0, "label": "keep / drop / unknown", "up": True},
              {"from": 1, "to": 1, "label": "only what changed", "up": True},
              {"from": 2, "to": 2, "label": "written back", "up": True}],
    "note": "A monthly subscription is asked about once a year, not twelve times."}),
   "The asking machinery. The scheduler is the whole system's restraint mechanism: it fires on "
   "renewal dates, not on a reporting cadence.",
   "How a renewal question is scheduled, sent and recorded",
   "Three boxes across the top outside the AWS account. The Owner, who gets one question a "
   "year. Whoever pays, who gets a monthly digest. And the Owner tab, where answers are written "
   "back. Inside the account, three components. The Scheduler, which fires thirty days before "
   "the next expected renewal. The Question builder, which composes the annual figure and last "
   "year's answer. And the Recorder, which stores what was decided and when. Arrows show the "
   "owner replying keep, drop or unknown, whoever pays receiving only what changed, and answers "
   "being written back to the tab. A note says a monthly subscription is asked about once a "
   "year, not twelve times."),
  ("h3", "Why thirty days"),
  ("p", "Close enough to the renewal that the decision is live, far enough out that cancelling "
        "is still possible without arguing about a refund. Many annual software contracts have "
        "a notice period of exactly thirty days, which is not a coincidence &mdash; asking on "
        "the renewal date is asking after the deadline, and asking three months out gets "
        "\"remind me nearer the time\", which nobody ever does."),
  ("p", "For a monthly subscription there is no meaningful renewal date, so the anniversary of "
        "the first charge is used. It is arbitrary, and being arbitrary is fine; what matters "
        "is that it happens once a year on a predictable date rather than every month."),
  ("h2", "What the message says"),
  ("callout", "The whole message, in order", [
   "<strong>Line one.</strong> The product and the annual cost. \"PROJTOOL &mdash; £172.80 a "
   "year (£14.40/month), on the card ending 4417.\"",
   "<strong>Line two.</strong> How long, and the trend. \"Charged since September 2024. Up 19% "
   "on last year.\"",
   "<strong>Line three, if there is one.</strong> What was said last time. \"Last July you said: "
   "keep &mdash; used for the client portal project.\"",
   "<strong>Three buttons.</strong> \"Keep it\" &middot; \"We should drop this\" &middot; \"I "
   "don't know what this is\".",
   "<strong>The raw statement line,</strong> in small text at the bottom. It is often what makes "
   "somebody recognise it.",
  ]),
  ("h3", "Quoting last year's answer"),
  ("p", "This is the line that does the most work and is easiest to leave out. A bare renewal "
        "question invites the path of least resistance, which is \"keep\". The same question "
        "with \"last July you said: keep &mdash; used for the client portal project\" underneath "
        "it invites a second thought, because the client portal project finished in November. "
        "It costs one extra sentence and it converts inertia into a decision roughly one time in "
        "five."),
  ("h3", "The third button"),
  ("p", "\"I don't know what this is\" has to be there and has to be as prominent as the other "
        "two. Without it, a person who does not recognise a charge will pick \"keep\", because "
        "picking \"drop\" on something you cannot identify feels risky. With it, the "
        "subscription moves to unowned, goes into the monthly digest, and gets in front of "
        "somebody else &mdash; which is exactly the right outcome and is unreachable from a "
        "two-button design."),
  ("h2", "The monthly digest, and what is not in it"),
  ("p", "Whoever pays the bills gets one message a month, and it deliberately does not contain "
        "the list of subscriptions. It contains only changes: new subscriptions detected, price "
        "rises, subscriptions that stopped charging, and anything currently unowned."),
  ("fig", ("strip", {
    "stages": [
      {"title": "New", "sub": ["2 detected"], "icon": "tag"},
      {"title": "Price rises", "sub": ["3, +£410/yr"], "icon": "money"},
      {"title": "Stopped", "sub": ["1, check if intended"], "icon": "stop"},
      {"title": "Unowned", "sub": ["4 still open"], "icon": "alarm"},
      {"title": "Total", "sub": ["£31,400/yr, +2%"], "icon": "chart"}],
    "title": "THE MONTHLY DIGEST",
    "note": "Five lines. The full list of 52 subscriptions is a link, not the message."}),
   "The monthly digest: only what changed, plus one running total. The full inventory is "
   "available and is deliberately not the message.",
   "The five lines of the monthly subscription digest",
   "A horizontal row of five boxes. New: two subscriptions detected. Price rises: three, worth "
   "four hundred and ten pounds a year more. Stopped: one, worth checking whether it was "
   "intended. Unowned: four still open. Total: thirty-one thousand four hundred pounds a year, "
   "up two per cent. A note says five lines, and that the full list of fifty-two subscriptions "
   "is a link rather than the message."),
  ("p", "The running total is the one thing that is not a change, and it earns its place because "
        "it is the number the business could not previously state. Watching it move two per cent "
        "in a month is a different relationship with software spend from discovering it once a "
        "year during budgeting."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="merchant",
 volumes=[(40, "40 new merchants"), (120, "120 new merchants"), (400, "400 new merchants")],
 read_each=0.0021, msgs_each=1.2,
 lede=("This is the cheapest system in the series, and the reason is structural: the model is "
       "only ever asked about a merchant string it has not seen before. After the first pass "
       "resolves a business's forty-odd merchants, the ongoing cost is a handful of new ones a "
       "month. Here is where each cent goes."),
 takeaway_extra=("The model only runs on merchant strings never seen before, so the second "
                 "month costs a fraction of the first."),
 risks=[
  "<strong>Re-resolving known merchants.</strong> If the known-merchants cache is keyed on the "
  "raw descriptor rather than the cleaned one, every trivial variation of the same string is a "
  "fresh model call. Key it on the cleaned merchant and the first pass is the only expensive "
  "one.",
  "<strong>Re-ingesting overlapping exports.</strong> Without the line fingerprint, "
  "re-uploading a statement doubles charges, which breaks grouping and can produce a flurry of "
  "false new-subscription alerts.",
  "<strong>Log retention left at never.</strong> With a few hundred transactions a month the "
  "logs will out-cost everything else within a year. Thirty days of retention is the whole fix.",
 ],
 per_unit_note=("The volume unit here is deliberately unusual: it is new merchant strings, not "
                "transactions. Transactions are free to process; only an unrecognised merchant "
                "costs a model call, and a settled business produces very few of those."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="sa",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the three tables, the scheduled sweeps, and the one place a model is used."),
 outside=[
  {"title": "Transaction feed", "sub": ["CSV, email, or API"], "icon": "money"},
  {"title": "Owner tab", "sub": ["Sheets API, read-write"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["questions, digest"], "icon": "email"}],
 inside=[
  {"title": "S3 + SQS", "sub": ["feeds,", "one merchant queue"], "icon": "bucket"},
  {"title": "Lambda x4", "sub": ["ingest, group,", "attribute, ask"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["txns, subs, merchants"], "icon": "database"}],
 note="us-east-1. One account. No credential to any audited service exists anywhere in it.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Transaction feed, arriving as a CSV "
  "drop, an emailed statement or a read-only API. The Owner tab, read and written through the "
  "Google Sheets API. And SES outbound, carrying the renewal questions and the monthly digest. "
  "Inside the account, three groups. S3 holding the raw feeds and SQS carrying one merchant "
  "queue. Four Lambda functions named ingest, group, attribute and ask. And three DynamoDB "
  "tables named txns, subs and merchants. A note gives the region as us-east-1, one account, "
  "and states that no credential to any audited service exists anywhere in it."),
 functions=[
  ["<code>sa-ingest</code>", "S3 ObjectCreated + SES inbound",
   "Parses the feed, fingerprints each line, writes txns", "60s / 1024&nbsp;MB"],
  ["<code>sa-group</code>", "EventBridge daily",
   "Rebuilds subscription groups from the txn history", "120s / 1024&nbsp;MB"],
  ["<code>sa-attribute</code>", "SQS merchant queue",
   "Owner lookup, cardholder fallback, one Bedrock call on new merchants",
   "20s / 512&nbsp;MB"],
  ["<code>sa-ask</code>", "EventBridge daily + Function URL",
   "Renewal questions, the monthly digest, and the signed answer links",
   "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>sa-ingest-role</code>", "<code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "The feeds prefix; the txns table only"],
  ["<code>sa-group-role</code>", "<code>dynamodb:Query</code>/<code>PutItem</code>",
   "Txns, read; subs, write"],
  ["<code>sa-attribute-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>secretsmanager:GetSecretValue</code>",
   "One model arn; the Sheets credential only"],
  ["<code>sa-ask-role</code>", "<code>ses:SendEmail</code>, <code>dynamodb:UpdateItem</code>",
   "One verified identity; subs table"]],
 tables=[
  ("Table: txns",
   "PK   fingerprint       S   sha256(date|amount|merchant_raw|card)\n"
   "     date              S   2026-07-02\n"
   "     amount            N   14.40\n"
   "     currency          S   GBP\n"
   "     orig_amount       N   17.99\n"
   "     orig_ccy          S   USD\n"
   "     merchant_raw      S   SP * PROJTOOL\n"
   "     merchant          S   projtool\n"
   "     card              S   ****4417\n"
   "     ttl               N   epoch, +7 years\n\n"
   "GSI  merchant-index      PK merchant, SK date   -- the grouping query"),
  ("Table: subs",
   "PK   sub_id            S   projtool|14.40|monthly\n"
   "     merchant          S   projtool\n"
   "     product           S   ProjTool (project management)\n"
   "     interval          S   monthly | quarterly | annual\n"
   "     amount            N   14.40\n"
   "     annual            N   172.80\n"
   "     first_seen        S   2024-09-14\n"
   "     next_expected     S   2026-08-02\n"
   "     owner             S   or null, which is the finding\n"
   "     purpose           S   free text, from the owner\n"
   "     last_answer       S   keep | drop | unknown\n"
   "     last_asked        S   2025-07-05\n\n"
   "GSI  ask-index           PK owner, SK next_expected   -- the renewal sweep"),
  ("Table: merchants",
   "PK   merchant          S   projtool\n"
   "     product           S   ProjTool (project management)\n"
   "     confidence        N   0.92\n"
   "     resolved_by       S   model | human | builtin\n"
   "     resolved_at       S   2026-07-13T09:00:00Z\n\n"
   "Every resolution is cached here forever. The model is only ever called\n"
   "for a cleaned merchant string that has no row in this table.")],
 inbound=[
  "<strong>CSV drops</strong> go to an S3 prefix. <strong>Emailed statements</strong> arrive "
  "through an SES receipt rule writing to the same prefix. Both fire the same ingest.",
  "<strong>Open Banking</strong>, where used, is granted the transactions scope only. There is "
  "no payment scope, no standing order scope, and no way to add one without a new consent flow.",
  "<strong>Answer links</strong> in a renewal question are signed, scoped to one subscription, "
  "single-use, and expire after forty-five days.",
  "<strong>No credential</strong> to any audited service is stored anywhere. There is no "
  "secret for ProjTool because the system has no reason to log in to ProjTool."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "used only to turn a card-statement descriptor into a likely product name.",
  "<strong>Called once per unseen merchant,</strong> ever. A row in the merchants table means "
  "the model is never asked again about that string.",
  "<strong>Output is a JSON schema</strong> with a product name, a category and a confidence, "
  "all nullable. A null product produces a question quoting the raw descriptor, which a human "
  "often recognises instantly.",
  "<strong>Grounded</strong> with the merchants this business has already resolved, so "
  "variations of a known string resolve consistently.",
  "<strong>Nothing about grouping touches a model.</strong> Finding a subscription is date "
  "arithmetic, and date arithmetic should be code."],
 gotchas=[
  "Group on the original currency amount where the feed carries it, or every foreign-currency "
  "subscription splits into a dozen groups as the exchange rate moves.",
  "Two charges is a coincidence and three is a subscription -- except for annual, where "
  "waiting for a third means waiting two years. Treat two annual charges as probable and say "
  "so in the message.",
  "Ask once a year, not once a interval. This is the setting people change first and regret, "
  "because a monthly email about eleven subscriptions is filtered within six weeks.",
  "Write resolved owners back to the sheet. If this system is switched off, the useful output "
  "should survive in a spreadsheet.",
  "Never add a write scope. The first feature request will be automatic cancellation, and "
  "granting it turns a small tool into serious security surface for a saving a human can "
  "realise in ninety seconds."],
))
