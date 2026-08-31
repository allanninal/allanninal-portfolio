"""Day 111 -- 2026-08-13 -- Win-back campaigner."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "win-back-campaigner"
NAME = "Win-back campaigner"

SPEC = {
 "slug": SLUG, "date": "2026-08-13", "name": NAME,
 "tagline": ("Contacts customers who have genuinely stopped buying -- after checking why they "
             "stopped, because a third of them left for a reason that a cheerful 'we miss you' "
             "email makes considerably worse."),
 "lede": ("A small system that works out who has actually lapsed rather than who is merely "
          "between purchases, checks each one's history before contacting them at all, sends one "
          "message that leads with the reason rather than the discount, and counts the result in "
          "a way that survives contact with the margin. Seven posts on the same system, one "
          "diagram at a time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["win-back", "customer retention", "lapsed customers", "email marketing", "CRM",
              "serverless"],
 "icons": ["person", "clock", "email"],
 "faq": [
  ("What is a win-back campaigner?",
   "A small serverless system that identifies customers who have genuinely stopped buying, "
   "excludes the ones who should not be contacted, and sends a single message with an offer "
   "chosen for the situation rather than a blanket discount."),
  ("How is lapsed defined?",
   "Per product, from that customer's own buying interval -- not a global ninety days. Somebody "
   "who buys once a year is not lapsed at four months, and somebody who bought weekly is lapsed "
   "at six."),
  ("Who does it refuse to contact?",
   "Anyone with an unresolved complaint, a recent refund, a closed business, a bereavement "
   "marker, or a withdrawal on record. The post on this is the important one."),
  ("Does it lead with a discount?",
   "No. A discount is the last option, and the measurement post explains why: most of it goes to "
   "people who were coming back anyway."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "win-back-campaigner-on-aws",
 "title": "A win-back campaigner on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Finds genuinely lapsed customers, checks why they left, sends one message, and counts "
          "the result honestly. AWS, about $2 a month."),
 "og": ("A cheerful 'we miss you' to somebody whose last order arrived broken is not a win-back. "
        "Checking why they stopped is most of the system."),
 "abstract": ("The whole system on one page -- define lapsed, check the history, send one message "
              "&mdash; and the check that removes about a third of the list."),
 "lede": ("The list of customers who have not bought in ninety days is easy to produce and mostly "
          "wrong. Some of them buy annually and are not lapsed. Some of them stopped because "
          "something went badly and nobody followed it up. A few have died. Sending all of them "
          "the same email is a thing many businesses do and none of them enjoy the consequences "
          "of."),
 "tags": ["win-back", "customer retention", "lapsed customers", "email marketing", "CRM",
          "serverless"],
 "takeaways": [
  "Lapsed is defined per customer per product, from their own interval.",
  "Check why they stopped before contacting them. About a third should not be contacted.",
  "One message, and the reason comes before the offer.",
  "A discount is the last lever, not the first.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Order history", "sub": ["per customer,", "per product"], "icon": "database"},
      {"title": "What happened since", "sub": ["complaints, refunds,", "withdrawals"], "icon": "doc"},
      {"title": "The customer", "sub": ["one message, or none"], "icon": "person"}],
    "inside": [
      {"title": "Lapse detector", "sub": ["their interval,", "not a global rule"], "icon": "clock"},
      {"title": "Suppression check", "sub": ["why did they stop?"], "icon": "shield"},
      {"title": "Sender", "sub": ["reason first,", "offer second"], "icon": "email"}],
    "edges": [{"from": 0, "to": 0, "label": "intervals"},
              {"from": 1, "to": 1, "label": "the reasons"},
              {"from": 2, "to": 2, "label": "one message, or none", "up": True}],
    "note": "The middle box removes about a third of the list, and those are the ones that matter."}),
   "Three things outside the account, three pieces inside it. The suppression check is the "
   "component that separates a win-back campaign from a complaint generator.",
   "System: lapsed customers detected, suppressed and contacted",
   "Three boxes across the top sit outside the AWS account. On the left, Order history per "
   "customer and per product. In the middle, What happened since: complaints, refunds and "
   "withdrawals. On the right, The customer, who receives one message or none. Each connects by "
   "an arrow to the AWS account container below. Intervals flow down into the account. The "
   "reasons feed in. One message, or none, goes back out. Inside the AWS account are three "
   "components in a row. On the left, the Lapse detector, using their own interval rather than a "
   "global rule. In the middle, the Suppression check, asking why they stopped. On the right, the "
   "Sender, putting the reason before the offer. A note at the bottom says the middle box removes "
   "about a third of the list, and those are the ones that matter."),
  ("h3", "The list everyone starts with"),
  ("p", "Every CRM will produce \"customers with no order in ninety days\" in one click, and it "
        "is the wrong list in three separate ways. It includes people whose normal buying cycle "
        "is longer than ninety days, who have not lapsed at all. It excludes people who bought "
        "weekly and stopped six weeks ago, who very much have. And it takes no account of why "
        "anybody stopped."),
  ("p", "That third one is the expensive mistake. A customer whose last delivery arrived damaged "
        "and whose complaint is still open receiving \"we miss you &mdash; here is 15% off\" is a "
        "specific and avoidable kind of insult, and it is what a ninety-day list guarantees will "
        "happen a few times per campaign."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The lapse detector.</strong> Learns each customer's own buying interval per product "
   "and flags when they are meaningfully past it. Part 2.",
   "<strong>The suppression check.</strong> Looks at what happened since the last order and "
   "removes anybody who should not be contacted. Part 3.",
   "<strong>The sender.</strong> One message, with the offer chosen from a ladder that starts "
   "well below a discount. Part 4.",
  ]),
  ("h2", "One customer, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Bought every 5 weeks", "sub": ["for 2 years"], "icon": "counter"},
      {"title": "Nothing for 14", "sub": ["nearly 3x their gap"], "icon": "clock"},
      {"title": "History checked", "sub": ["no complaint, no refund"], "icon": "shield"},
      {"title": "Offer chosen", "sub": ["a restock reminder"], "icon": "form"},
      {"title": "One message", "sub": ["no discount"], "icon": "email"}],
    "title": "ONE CUSTOMER, END TO END",
    "note": "Most win-backs need a reminder, not money. The ladder starts at the cheap end."}),
   "The same system as one line. The fourth box is where most implementations jump straight to a "
   "percentage off and give away margin they did not need to.",
   "One lapsed customer from detection to a single message",
   "A horizontal row of five boxes joined by arrows. Bought every five weeks for two years. "
   "Nothing for fourteen weeks, nearly three times their gap. History checked: no complaint, no "
   "refund. Offer chosen: a restock reminder. One message: no discount. A note says most "
   "win-backs need a reminder rather than money, and the ladder starts at the cheap end."),
  ("h2", "In plain words"),
  ("p", "A customer bought the same consumable every five weeks or so for two years, and then "
        "stopped. Fourteen weeks later the detector notices: that is nearly three times their own "
        "gap, which is a real signal, where fourteen weeks for an annual buyer would be nothing."),
  ("p", "The suppression check runs. No complaint on record, no refund, no delivery failure, no "
        "withdrawal, the account is not marked closed or deceased. So a message goes: \"You used "
        "to order the 5 litre every month or so and it has been a while &mdash; running low, or "
        "did you find something better? Either answer is useful.\""),
  ("p", "No discount. If they reply saying they switched supplier because of price, that is "
        "information worth more than the sale, and the discount conversation can happen with a "
        "person who now knows why. If they reply saying they forgot, the reminder was the entire "
        "intervention and it cost nothing."),
  ("callout", "Design rules that shaped every decision", [
   "Lapsed is relative to that customer's own interval, per product.",
   "Check why they stopped before deciding whether to contact them at all.",
   "One message. A sequence of three converts slightly better and costs the relationship.",
   "The offer ladder starts at a reminder and ends at a discount, not the other way round.",
   "Any reply from a person goes to a person. Never an automated follow-up.",
   "Never contact anyone marked deceased, closed, complained-about, or withdrawn.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Win-back campaigns have an unusual property: the cost of getting one wrong is much "
        "higher than the value of getting one right. A successful win-back recovers a customer "
        "worth a few hundred pounds. An insensitive message to somebody whose circumstances "
        "changed badly ends a relationship permanently and gets screenshotted."),
  ("p", "That asymmetry argues for a system that suppresses aggressively, sends rarely, and puts "
        "its effort into knowing who not to contact. Most of the engineering here is in the "
        "middle box for exactly that reason."),
  ("p", "The next four posts walk through each piece: how lapsed gets defined, how the "
        "suppression check works, how the offer is decided, and how a win-back is honestly "
        "counted. One diagram per post, a cost breakdown, and an engineering reference at the "
        "end."),
 ],
},
{
 "slug": "how-lapsed-gets-defined",
 "title": "How lapsed gets defined",
 "nav": "How lapsed is defined",
 "read": 5, "words": 740,
 "desc": ("Why a global ninety days is wrong in both directions, learning each customer's own "
          "interval, and the customers who never had one."),
 "og": ("Somebody who buys once a year is not lapsed at four months. Somebody who bought weekly "
        "is lapsed at six. One threshold cannot serve both."),
 "abstract": ("Why a single lapse threshold fails, how a per-customer per-product interval is "
              "derived, seasonal buying, and what to do about customers with too little history."),
 "lede": ("The definition of lapsed determines everything downstream, and the default definition "
          "&mdash; a fixed number of days for everybody &mdash; is wrong for most of the list in "
          "one direction or the other."),
 "tags": ["win-back", "segmentation", "customer intervals", "retention", "analytics", "serverless"],
 "takeaways": [
  "Use the customer's own median interval for that product, not a global number.",
  "Two and a half times their gap is a defensible line and is a judgement, not a law.",
  "Seasonal products need the season, not the interval.",
  "Fewer than three orders means no interval; those customers are handled separately or not at all.",
  "A customer who bought once is not a lapsed customer, and treating them as one is a category error.",
 ],
 "blocks": [
  ("h2", "One threshold, two failures"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Weekly buyer", "parts": [("gap", 7), ("wait", 83)]},
      {"label": "Monthly buyer", "parts": [("gap", 32), ("wait", 58)]},
      {"label": "Annual buyer", "parts": [("gap", 365), ("wait", 0)]}],
    "series": [("gap", "Their own buying interval, days", "#7AA116"),
               ("wait", "Extra days a 90-day rule makes you wait", "#DD344C")],
    "unit": "",
    "note": "The annual buyer is flagged at 90 days and has not lapsed at all. Wrong both ways."}),
   "Why a single threshold cannot work. The weekly buyer is left for nearly three months past "
   "the point they clearly stopped; the annual buyer is chased a quarter into a normal gap.",
   "How a fixed ninety-day lapse rule fails different buying frequencies",
   "A stacked bar chart with three bars measured in days. Two series: their own buying interval "
   "in green, and the extra days a ninety-day rule makes you wait in red. The weekly buyer has an "
   "interval of seven days and eighty-three extra days of waiting. The monthly buyer has an "
   "interval of thirty-two days and fifty-eight extra days. The annual buyer has an interval of "
   "three hundred and sixty-five days and no extra waiting, because ninety days is well inside "
   "their normal gap. A note says the annual buyer is flagged at ninety days and has not lapsed "
   "at all, so the rule is wrong in both directions."),
  ("h3", "The interval that matters is theirs"),
  ("p", "Take the median gap between that customer's orders of that product. Median rather than "
        "mean, because one long holiday gap distorts an average and does not distort a median. "
        "Per product rather than overall, because somebody who buys a consumable monthly and "
        "furniture every four years has two intervals and averaging them describes neither."),
  ("p", "Then lapsed is roughly two and a half times that median with no order. For the weekly "
        "buyer that is about eighteen days; for the annual buyer it is two and a half years. Both "
        "of those feel right to anybody who knows the customer, which is the test."),
  ("h3", "Where the multiplier comes from"),
  ("p", "It is a judgement, and it is worth saying so rather than dressing it up. Below about two "
        "times, you are contacting people who are merely a bit late and the message reads as "
        "pestering. Above about three, the relationship has cooled enough that a reminder no "
        "longer works and you need the harder conversation."),
  ("p", "Two and a half sits in the middle and should be adjustable per product category, with "
        "the value visible in the configuration rather than buried in code. Somebody will want to "
        "change it, and the argument about what it should be is a better argument to have "
        "explicitly."),
  ("h2", "The customers with no interval"),
  ("fig", ("chain", {
    "entry": {"title": "A customer to assess", "sub": ["with an order history"], "icon": "person"},
    "steps": [
      {"title": "Three or more orders?", "sub": ["of this product"], "icon": "branch",
       "exit": {"title": "No interval exists", "sub": ["do not infer one"], "icon": "question",
                "label": "no"}},
      {"title": "Is it seasonal?", "sub": ["by product, not customer"], "icon": "branch",
       "exit": {"title": "Use the season", "sub": ["lapsed after next season"], "icon": "clock",
                "label": "yes"}},
      {"title": "Median gap", "sub": ["not the mean"], "icon": "counter"},
      {"title": "Past 2.5x it?", "sub": ["with no order"], "icon": "branch",
       "exit": {"title": "Not yet", "sub": ["check again next week"], "icon": "clock",
                "label": "no"}},
      {"title": "Lapsed", "sub": ["hand to suppression"], "icon": "shield"}],
    "note": "One-time and two-time buyers are a different problem with a different message."}),
   "How lapse is decided for one customer. The first exit is the largest group in most businesses "
   "and the one that should not be run through this system at all.",
   "How a customer is assessed as lapsed against their own interval",
   "A vertical chain of five steps entered by a box labelled A customer to assess, with an order "
   "history. Step one asks whether there are three or more orders of this product; if not it "
   "exits to No interval exists, and does not infer one. Step two asks whether the product is "
   "seasonal, judged by product rather than by customer; if so it exits to Use the season, lapsed "
   "after the next season passes. Step three computes the median gap rather than the mean. Step "
   "four asks whether they are past two and a half times it with no order; if not it exits to Not "
   "yet, check again next week. Step five marks them lapsed and hands them to suppression. A note "
   "says one-time and two-time buyers are a different problem with a different message."),
  ("h3", "One-time buyers are not lapsed"),
  ("p", "In most businesses they are the largest group by a wide margin, and calling them lapsed "
        "is a category error with practical consequences: the message that works for a two-year "
        "customer who stopped is completely wrong for somebody who bought once eighteen months "
        "ago and may not remember doing it."),
  ("p", "The honest answer is that they are a different campaign, with a different message, and "
        "quite possibly not worth running at all. Excluding them keeps the win-back list small "
        "and its response rate high, which is what makes the whole thing worth doing."),
  ("h3", "Seasonal products"),
  ("p", "Somebody who buys garden furniture every May has an interval of a year, but they are not "
        "lapsed in February; they are waiting for spring. Seasonal products need the season as "
        "the unit: lapsed means the season came and went without an order."),
  ("p", "Seasonality is a property of the product, set once by somebody who knows the business, "
        "not something to be inferred from thin per-customer data. Two orders in two consecutive "
        "Mays is not enough evidence to conclude anything, and an inference engine confident "
        "enough to try will also be confident about noise."),
  ("p", "Next: whether to contact them at all."),
 ],
},
{
 "slug": "how-the-suppression-check-works",
 "title": "How the suppression check works",
 "nav": "How suppression works",
 "read": 6, "words": 780,
 "desc": ("The reasons somebody stopped that make contact a bad idea, the ones that make it "
          "harmful, and why this check runs before anything else."),
 "og": ("About a third of a lapsed list should not be contacted. Finding out why somebody left is "
        "the difference between a win-back and a complaint."),
 "abstract": ("The five suppression categories, why the check runs before segmentation rather "
              "than after, the bereavement and business-closure cases, and how a suppression is "
              "recorded."),
 "lede": ("This is the post that matters. Everything else is a scheduling problem; this is the "
          "part that determines whether the campaign is a modest revenue improvement or the "
          "reason somebody tells the story about your company at a dinner party."),
 "tags": ["win-back", "suppression", "customer care", "complaints", "ethics", "serverless"],
 "takeaways": [
  "Five categories: unresolved complaint, recent refund, withdrawal, closed, bereaved.",
  "The check runs before segmentation, so a suppressed customer is never scored or targeted.",
  "An unresolved complaint is a task for a person, not a suppression and nothing else.",
  "Bereavement and business closure markers are permanent and never expire.",
  "Every suppression is recorded with its reason, because the reason is the useful part.",
 ],
 "blocks": [
  ("h2", "The five categories"),
  ("fig", ("chain", {
    "entry": {"title": "A lapsed customer", "sub": ["past their interval"], "icon": "clock"},
    "steps": [
      {"title": "Open complaint?", "sub": ["or one closed badly"], "icon": "branch",
       "exit": {"title": "To a person", "sub": ["not to a campaign"], "icon": "person",
                "label": "yes"}},
      {"title": "Refund or failure?", "sub": ["in the last 2 orders"], "icon": "branch",
       "exit": {"title": "Suppress", "sub": ["fix that first"], "icon": "stop", "label": "yes"}},
      {"title": "Withdrawn contact?", "sub": ["ask the consent record"], "icon": "branch",
       "side": {"title": "Consent record", "sub": ["from Day 105"], "icon": "shield"},
       "exit": {"title": "Suppress", "sub": ["permanently"], "icon": "lock", "label": "yes"}},
      {"title": "Closed or bereaved?", "sub": ["a permanent marker"], "icon": "branch",
       "exit": {"title": "Suppress", "sub": ["forever, quietly"], "icon": "lock", "label": "yes"}},
      {"title": "Contactable", "sub": ["choose an offer"], "icon": "check"}],
    "note": "The first exit is not a suppression. It is a task, and somebody has to do it."}),
   "The suppression gates in order. The first one produces work rather than silence, which is the "
   "distinction most implementations miss.",
   "The five checks that decide whether a lapsed customer may be contacted",
   "A vertical chain of five steps entered by a box labelled A lapsed customer, past their "
   "interval. Step one asks whether there is an open complaint or one that closed badly; if so it "
   "exits to To a person, not to a campaign. Step two asks whether there was a refund or delivery "
   "failure in the last two orders; if so it exits to Suppress, and fix that first. Step three "
   "asks whether they have withdrawn contact, checking the consent record from Day 105; if so it "
   "exits to Suppress permanently. Step four asks whether the account is marked closed or "
   "bereaved, a permanent marker; if so it exits to Suppress forever, quietly. Step five marks "
   "them contactable and moves on to choosing an offer. A note says the first exit is not a "
   "suppression but a task, and somebody has to do it."),
  ("h3", "The complaint case produces work"),
  ("p", "A customer who lapsed after a complaint is the most valuable name on the list and the "
        "one that must never receive an automated message. They stopped for a reason you already "
        "know, it is written down, and a marketing email that ignores it confirms every "
        "assumption they made when they left."),
  ("p", "So that exit creates a task with the complaint attached: here is who, here is what "
        "happened, here is when. Somebody calls or writes personally. The conversion rate on that "
        "is far higher than any campaign and the volume is small enough that it is genuinely "
        "possible, which is the argument that gets it done."),
  ("h2", "The permanent markers"),
  ("callout", "Never expire, never override, never explain themselves", [
   "<strong>Deceased.</strong> Recorded when a family member tells you, or a delivery is "
   "returned with that reason. No campaign of any kind, ever.",
   "<strong>Business closed.</strong> Same treatment. A win-back to a dissolved company reaches "
   "whoever is winding it up.",
   "<strong>Withdrawn.</strong> They asked not to be contacted. This is the whole of it.",
   "<strong>Do not build an override.</strong> Not for a special campaign, not for a big "
   "customer, not for a one-off. The absence of the mechanism is the protection.",
   "<strong>Do not report the reason</strong> anywhere it will be read casually. The suppression "
   "list shows counts by category and the detail only to whoever needs it.",
  ]),
  ("p", "The bereavement case is worth being specific about because it is the one that produces "
        "the genuinely awful outcomes, and it is entirely preventable. The marker usually arrives "
        "informally &mdash; a phone call, a reply to a message, a returned parcel &mdash; and the "
        "system's only job is to make recording it easy and make honouring it automatic."),
  ("p", "Making it easy matters more than it sounds. If setting the marker requires a database "
        "change or a support ticket, it will not happen consistently, and the campaign will find "
        "the customer six weeks later. One field, one click, from wherever the person heard."),
  ("h2", "Before segmentation, not after"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Lapsed list", "sub": ["612 customers"], "icon": "counter"},
      {"title": "Suppression first", "sub": ["-198"], "icon": "shield"},
      {"title": "Contactable", "sub": ["414"], "icon": "person"},
      {"title": "Then segment", "sub": ["and choose offers"], "icon": "filter"},
      {"title": "Send", "sub": ["one each"], "icon": "email"}],
    "title": "THE ORDER MATTERS",
    "note": "Suppressed customers are never scored, never segmented, never in a target list."}),
   "Why suppression runs first. A suppressed customer that reaches the segmentation stage exists "
   "in a targeting list somewhere, and lists get exported.",
   "Why suppression runs before segmentation in a win-back campaign",
   "A horizontal row of five boxes. Lapsed list: six hundred and twelve customers. Suppression "
   "first: minus one hundred and ninety-eight. Contactable: four hundred and fourteen. Then "
   "segment, and choose offers. Send: one each. A note says suppressed customers are never "
   "scored, never segmented and never in a target list."),
  ("p", "Running the check last is the obvious implementation and it leaves suppressed customers "
        "sitting in intermediate lists that get exported, copied into spreadsheets, and used for "
        "something else six months later. Running it first means they never enter the pipeline at "
        "all."),
  ("h3", "Recording the reason"),
  ("p", "Every suppression stores which gate stopped it and when. That record does two jobs: it "
        "answers \"why did we not contact this customer\" instantly, and its distribution is a "
        "genuinely useful business signal."),
  ("p", "A campaign where a hundred and ninety-eight of six hundred and twelve are suppressed and "
        "seventy of those are unresolved complaints is not primarily telling you about "
        "win-backs. It is telling you there are seventy open complaints, which is a more "
        "important finding than anything the campaign will produce."),
  ("p", "Next: what to actually offer."),
 ],
},
{
 "slug": "how-the-offer-is-decided",
 "title": "How the offer is decided",
 "nav": "How the offer is decided",
 "read": 5, "words": 740,
 "desc": ("The ladder from a reminder to a discount, why most win-backs need no money at all, and "
          "what a reply is worth."),
 "og": ("Leading with a discount trains customers to lapse. The ladder starts with a question and "
        "ends with a percentage."),
 "abstract": ("The four rungs of the offer ladder, why a reminder converts a surprising share, "
              "what a discount actually costs, and why every reply goes to a person."),
 "lede": ("The default win-back offer is a percentage off, it is chosen because it is easy to "
          "configure, and it is usually both unnecessary and quietly expensive. The ladder starts "
          "somewhere much cheaper."),
 "tags": ["win-back", "offers", "discounts", "margin", "email", "serverless"],
 "takeaways": [
  "Rung one is a reminder with a question, and it converts more than people expect.",
  "Rung two is something useful that costs nothing: a guide, a reorder link, a slot.",
  "Rung three is a non-price sweetener: free delivery, a sample, priority.",
  "Rung four is a discount, and it is the last one for good reasons.",
  "Every reply goes to a person. A reply is worth more than the order.",
 ],
 "blocks": [
  ("h2", "The ladder"),
  ("table", ["Rung", "What it is", "Costs", "Use when"], [
   ["1. Reminder", "\"It has been a while &mdash; running low?\"", "Nothing",
    "Consumables, habitual purchases"],
   ["2. Useful thing", "A reorder link, a slot, a how-to", "Nothing",
    "Anything with friction to reordering"],
   ["3. Non-price", "Free delivery, a sample, priority booking", "A little",
    "Where price was probably not the reason"],
   ["4. Discount", "A percentage or an amount off", "Margin, and precedent",
    "Where you know price was the reason"],
  ]),
  ("p", "The last column is the one to read carefully. A discount is right when you have evidence "
        "that price was why they left &mdash; they said so, or a competitor undercut you visibly "
        "&mdash; and it is a guess in every other case. Guessing costs margin on everybody who "
        "would have come back for a reminder."),
  ("h3", "Rung one converts more than expected"),
  ("p", "A meaningful share of lapsed consumable customers simply forgot, changed a routine, or "
        "ran out at an inconvenient moment and bought something else once. For those people the "
        "reminder is the entire intervention and the discount is pure giveaway."),
  ("p", "The message that works is a question rather than a pitch: \"running low, or did you find "
        "something better?\" Both answers are useful, the second one is worth more than the "
        "order, and asking it is what distinguishes this from a promotional email."),
  ("h2", "What a discount actually costs"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Reminder only", "parts": [("recovered", 1840), ("given", 0)]},
      {"label": "15% to everyone", "parts": [("recovered", 2210), ("given", 1490)]},
      {"label": "Discount on reply only", "parts": [("recovered", 2090), ("given", 310)]}],
    "series": [("recovered", "Margin recovered", "#7AA116"),
               ("given", "Margin given away", "#DD344C")],
    "unit": "£",
    "note": "The middle bar recovers the most and keeps the least. The third is the design."}),
   "Three approaches on the same lapsed list. Discounting everybody buys a slightly better "
   "recovery rate with a lot of margin from people who needed no discount at all.",
   "Margin recovered against margin given away under three win-back offers",
   "A stacked bar chart with three bars in pounds. Two series: margin recovered in green, and "
   "margin given away in red. Reminder only recovers one thousand eight hundred and forty pounds "
   "and gives away nothing. Fifteen per cent to everyone recovers two thousand two hundred and "
   "ten and gives away one thousand four hundred and ninety. Discount on reply only recovers two "
   "thousand and ninety and gives away three hundred and ten. A note says the middle bar recovers "
   "the most and keeps the least, and the third is the design."),
  ("p", "The middle bar is what most win-back campaigns do, and on a recovery-rate dashboard it "
        "is the winner. The margin given away does not appear on that dashboard, which is how the "
        "practice survives."),
  ("p", "The third approach &mdash; send the reminder, and offer a discount only to people who "
        "reply saying price was the problem &mdash; recovers nearly as much and keeps almost all "
        "the margin, at the cost of needing a person to handle replies."),
  ("h3", "The precedent cost"),
  ("p", "There is a second cost that is harder to measure and worth naming: a customer who "
        "receives fifteen per cent off for lapsing has learned that lapsing is worth fifteen per "
        "cent. Businesses that run a discount-led win-back for a couple of years reliably notice "
        "their best customers developing a suspicious rhythm."),
  ("p", "That is not an argument against ever discounting. It is an argument for the discount "
        "being a response to a stated reason rather than an automatic consequence of not buying, "
        "which is a distinction the customer can feel."),
  ("h2", "Replies go to people"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A reply arrives", "sub": ["to the win-back"], "icon": "email"},
      {"title": "Never auto-answered", "sub": ["not once"], "icon": "stop"},
      {"title": "To a named person", "sub": ["with the history"], "icon": "person"},
      {"title": "They read the reason", "sub": ["price, service, moved on"], "icon": "search"},
      {"title": "That is the value", "sub": ["more than the sale"], "icon": "check"}],
    "title": "WHAT A REPLY IS WORTH",
    "note": "Twelve replies explaining why people left is a better output than nine orders."}),
   "Why the reply path is staffed. The stated reasons from lapsed customers are the hardest "
   "business information to obtain and this is the one moment they are volunteered.",
   "How a reply to a win-back message is handled",
   "A horizontal row of five boxes. A reply arrives to the win-back. Never auto-answered, not "
   "once. To a named person, with the history attached. They read the reason: price, service, or "
   "moved on. That is the value, more than the sale. A note says twelve replies explaining why "
   "people left is a better output than nine orders."),
  ("p", "This is also why the message is signed by a person with a working reply-to. A no-reply "
        "address on a win-back converts the one honest channel into a broadcast, and the "
        "information that would have told you why fourteen per cent of your customers left goes "
        "into a mailbox nobody reads."),
  ("p", "Next: counting what actually happened."),
 ],
},
{
 "slug": "how-a-win-back-is-honestly-counted",
 "title": "How a win-back is honestly counted",
 "nav": "How it is counted",
 "read": 5, "words": 730,
 "desc": ("The customers who were coming back anyway, the margin given to them, and the number "
          "that belongs next to the recovery rate."),
 "og": ("A recovery rate with no margin column is a number that only ever goes up. Put them "
        "side by side and the campaign gets designed differently."),
 "abstract": ("Why a raw recovery rate overstates, how to separate recovered revenue from margin "
              "given away, the attribution window, and what a good result looks like."),
 "lede": ("A win-back campaign will always report a recovery rate that looks fine, because some "
          "share of lapsed customers return regardless and every one of them lands in the numerator "
          "if nobody arranges otherwise."),
 "tags": ["win-back", "measurement", "margin", "attribution", "reporting", "serverless"],
 "takeaways": [
  "Some lapsed customers return on their own. Hold back a share and find out how many.",
  "Report margin recovered, not revenue recovered. They tell different stories.",
  "The attribution window should be one buying interval, not a fixed thirty days.",
  "Count the replies as an output in their own right.",
  "A campaign whose result is 'seventy open complaints' has still been worth running.",
 ],
 "blocks": [
  ("h2", "Revenue is the wrong number"),
  ("fig", ("chain", {
    "entry": {"title": "A campaign ends", "sub": ["414 messaged"], "icon": "email"},
    "steps": [
      {"title": "Orders in the window", "sub": ["say 47"], "icon": "counter"},
      {"title": "Minus the holdout rate", "sub": ["7 of 41 returned anyway"], "icon": "filter",
       "side": {"title": "Holdout", "sub": ["10%, never messaged"], "icon": "shield"}},
      {"title": "Incremental orders", "sub": ["47 - 17% of 414 = ~24"], "icon": "chart"},
      {"title": "Times margin", "sub": ["not revenue"], "icon": "money"},
      {"title": "Minus what was given", "sub": ["discounts, delivery"], "icon": "search"}],
    "note": "Half the headline orders were people who were coming back regardless."}),
   "How a recovery number becomes a real one. Each step removes something the raw count was "
   "quietly claiming credit for.",
   "How win-back results are computed from raw orders to net margin",
   "A vertical chain of five steps entered by a box labelled A campaign ends, four hundred and "
   "fourteen messaged. Step one counts orders in the window, say forty-seven. Step two subtracts "
   "the holdout rate, where seven of forty-one returned anyway, drawing on a side box labelled "
   "Holdout, ten per cent, never messaged. Step three computes incremental orders as forty-seven "
   "minus seventeen per cent of four hundred and fourteen, giving about twenty-four. Step four "
   "multiplies by margin rather than revenue. Step five subtracts what was given away in "
   "discounts and delivery. A note says half the headline orders were people who were coming back "
   "regardless."),
  ("h3", "Margin, not revenue"),
  ("p", "A win-back that recovers eleven thousand pounds of revenue at fifteen per cent off has "
        "recovered considerably less margin than the headline suggests, and on a low-margin "
        "product line it can recover almost none. Reporting revenue makes discount-led campaigns "
        "look best; reporting margin makes them look like what they are."),
  ("p", "The change is trivial &mdash; one column &mdash; and it reliably changes how the next "
        "campaign is designed, which is a good return on a column."),
  ("h3", "The window is theirs too"),
  ("p", "A thirty-day attribution window is the default and it has the same flaw as a ninety-day "
        "lapse rule: it fits one buying frequency. The window should be one of that customer's "
        "own intervals, so a monthly buyer is counted over a month and an annual buyer over a "
        "year."),
  ("p", "That does mean the annual segment's results are not known for a year, which is genuinely "
        "inconvenient and is the truth. Reporting them at thirty days would produce a number that "
        "means nothing, faster."),
  ("h2", "What a quarter looks like"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Lapsed", "sub": ["612"], "icon": "counter"},
      {"title": "Suppressed", "sub": ["198, incl. 70 complaints"], "icon": "shield"},
      {"title": "Messaged", "sub": ["373, holdout 41"], "icon": "email"},
      {"title": "Incremental", "sub": ["~24 orders"], "icon": "chart"},
      {"title": "Net margin", "sub": ["about £1,900"], "icon": "money"}],
    "title": "ONE QUARTER, HONESTLY",
    "note": "And 70 open complaints found, which is arguably the more valuable output."}),
   "A quarter reported end to end. The suppression count carries a finding that the campaign was "
   "not looking for and that outranks the revenue.",
   "One quarter of win-back activity reported honestly",
   "A horizontal row of five boxes. Lapsed: six hundred and twelve. Suppressed: one hundred and "
   "ninety-eight, including seventy open complaints. Messaged: three hundred and seventy-three, "
   "with a holdout of forty-one. Incremental: about twenty-four orders. Net margin: about one "
   "thousand nine hundred pounds. A note says seventy open complaints were found, which is "
   "arguably the more valuable output."),
  ("p", "Nineteen hundred pounds of net margin in a quarter is a modest, real result from a system "
        "that costs two dollars a month to run, and it is worth reporting as modest rather than "
        "inflating it to the eleven thousand of gross recovered revenue that the same quarter "
        "could also be described as."),
  ("h3", "The finding that was not the goal"),
  ("p", "Seventy unresolved complaints surfacing from a suppression check is the kind of result "
        "that justifies the whole exercise on its own. Those customers were lost for a reason "
        "somebody wrote down and nobody acted on, and the campaign is the first process that "
        "looked."),
  ("p", "It is worth putting that in the report explicitly rather than leaving it as a "
        "suppression count nobody reads. \"Seventy customers stopped buying after a complaint we "
        "have not resolved\" is a sentence that produces action; \"suppressed: 198\" is not."),
  ("h2", "The pressure that arrives at month four"),
  ("callout", "Three requests to expect, and the answers", [
   "<strong>\"Drop the holdout, we know it works.\"</strong> Knowing it still works next year "
   "requires it to keep running. Ten per cent is a cheap insurance premium.",
   "<strong>\"Send a second message to non-openers.\"</strong> Converts slightly, complains "
   "considerably, and it is the same argument as the second abandonment nudge.",
   "<strong>\"Lower the lapse multiplier to get more volume.\"</strong> That contacts people who "
   "are merely a bit late, and the response rate falls faster than the volume rises.",
   "<strong>\"Just discount everyone, it is simpler.\"</strong> It is, and the margin column "
   "shows what it costs.",
   "<strong>All four are reasonable-sounding</strong> and all four are answered by numbers the "
   "report already carries, which is the point of carrying them.",
  ]),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="lapsed customer",
 volumes=[(150, "150 lapsed"), (600, "600 lapsed"), (2500, "2,500 lapsed")],
 read_each=0.0,
 msgs_each=0.65,
 lede=("There is no model in this system and the send volume is a fraction of the list, because "
       "suppression removes about a third before anything is sent. Six hundred lapsed customers a "
       "quarter is a busy small retailer. Here is where each cent goes."),
 takeaway_extra=("Two thirds of the list gets a message; the rest are suppressed and cost "
                 "nothing to not contact."),
 risks=[
  "<strong>Recomputing every customer's interval nightly.</strong> Intervals move slowly. Once a "
  "week is plenty and cuts the compute by most of it.",
  "<strong>Scanning the whole order table.</strong> The detector queries by customer and product "
  "against an index; a scan across a few years of orders is the one line item here that can get "
  "genuinely expensive.",
  "<strong>Storing a full order history copy.</strong> This system reads the orders that already "
  "exist. A second copy is cost and a synchronisation problem.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. The messaging band assumes "
                "about two thirds of the lapsed list passes suppression."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="wb",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the suppression markers, and how the holdout is assigned."),
 outside=[
  {"title": "Orders", "sub": ["the existing table"], "icon": "database"},
  {"title": "Complaints and refunds", "sub": ["and the consent record"], "icon": "shield"},
  {"title": "SES outbound", "sub": ["one message each"], "icon": "email"}],
 inside=[
  {"title": "EventBridge weekly", "sub": ["intervals,", "then detection"], "icon": "clock"},
  {"title": "Lambda x3", "sub": ["intervals, detect, send"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["profiles, campaigns"], "icon": "database"}],
 note="us-east-1. One account. Suppression runs before segmentation; markers never expire.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Orders, from the existing table. "
  "Complaints and refunds, along with the consent record. And SES outbound, carrying one message "
  "each. Inside the account, three groups. EventBridge running weekly to compute intervals and "
  "then run detection. Three Lambda functions named intervals, detect and send. And two DynamoDB "
  "tables named profiles and campaigns. A note gives the region as us-east-1, one account, and "
  "states that suppression runs before segmentation and that markers never expire."),
 functions=[
  ["<code>wb-intervals</code>", "EventBridge, weekly",
   "Recomputes the median interval per customer per product", "300s / 1024&nbsp;MB"],
  ["<code>wb-detect</code>", "EventBridge, weekly",
   "Flags lapses, runs all five suppression gates, assigns the holdout", "300s / 1024&nbsp;MB"],
  ["<code>wb-send</code>", "SQS send queue",
   "Re-checks suppression, picks the offer rung, sends once", "15s / 512&nbsp;MB"]],
 roles=[
  ["<code>wb-intervals-role</code>", "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "Read-only on orders; writes profiles"],
  ["<code>wb-detect-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>sqs:SendMessage</code>",
   "Profiles and campaigns; the send queue"],
  ["<code>wb-send-role</code>", "<code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Campaigns; one verified identity"]],
 tables=[
  ("Table: profiles",
   "PK   customer_id       S\n"
   "SK   product_key       S   sku or category\n"
   "     orders            N   count; fewer than 3 means no interval\n"
   "     median_gap_days   N   median, not mean\n"
   "     last_order_at     S   2026-05-04\n"
   "     seasonal          BOOL set on the product, not inferred\n"
   "     lapsed_at         S   set when past 2.5x the gap\n\n"
   "One row per customer per product. A customer with two products has\n"
   "two intervals, and averaging them would describe neither."),
  ("Table: campaigns",
   "PK   campaign_id       S   2026Q3_winback\n"
   "SK   customer_id       S\n"
   "     state             S   suppressed | holdout | messaged\n"
   "     suppressed_by     S   complaint | refund | withdrawn | closed | bereaved\n"
   "     rung              N   1..4, which offer was used\n"
   "     given_away        N   discount or delivery value, in pence\n"
   "     replied           BOOL\n"
   "     ordered_at        S   within one of their intervals\n"
   "     margin            N   on the recovered order, not revenue\n\n"
   "`suppressed_by` is what turns a suppression count into the finding\n"
   "about seventy open complaints. Without it, it is just a number.")],
 inbound=[
  "<strong>Orders are read, never written.</strong> This system has no write access to the order "
  "table at all.",
  "<strong>Suppression markers come from wherever they are heard</strong> &mdash; support, "
  "delivery returns, a phone call. One field, one click, and it is honoured everywhere.",
  "<strong>The consent record is consulted at detection and again at send</strong>, so a "
  "withdrawal in between suppresses the queued message.",
  "<strong>Suppression runs before segmentation</strong>, so a suppressed customer never exists "
  "in a target list that somebody could export."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Intervals are a median, lapse is a "
  "comparison, and suppression is five lookups.",
  "<strong>The tempting use</strong> is scoring who is most likely to return, in order to message "
  "only them. That optimises the wrong thing and makes the holdout comparison meaningless.",
  "<strong>A second tempting use</strong> is generating the message per customer. The four rungs "
  "are four templates with the product name substituted, and a generated version reads as "
  "marketing in a message whose entire premise is that it is not.",
  "<strong>Classifying reply reasons</strong> is a defensible use, and keep the raw reply text: "
  "the specifics are the reason the reply was worth more than the order.",
  "<strong>The cost page assumes none</strong>, which is why messaging is the only variable "
  "band."],
 gotchas=[
  "Compute the median, not the mean. One long gap for a holiday moves a mean and does not move a "
  "median, and the mean version flags people who never lapsed.",
  "Run suppression before segmentation. Order matters here for a reason that only shows up when "
  "somebody exports an intermediate list.",
  "Never build an override for the permanent markers. The absence of the mechanism is the "
  "protection, and the request to add one always sounds reasonable.",
  "Assign the holdout at detection, never message it, and expect to defend it at month four.",
  "Report margin and what was given away in the same table as the recovery rate. A recovery rate "
  "alone only ever argues for a bigger discount."],
))
