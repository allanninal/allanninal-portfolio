#!/usr/bin/env python3
"""Product articles, part B — the contractor cluster.

Five bid calculators, then the four workbooks that follow the same money through
a contracting business: estimate it (trades), claim it (billing), earn it (wip,
in products_a), collect it (cashflow), and pay for the iron (fleet). Plus
certified payroll, which is its own problem.

The five bid calculators share a skeleton, so they are built by a factory rather
than copied five times — but every number in each one is that trade's own, from
trades/README.md. Workers' compensation is $3.50 per $100 of payroll for an
electrician and $28.00 for a roofer, which is the entire reason this is five
products and not one, and it is why the pages read differently.
"""
from build_product import table
from visuals import V

# --------------------------------------------------------------------------- #
# The five bid calculators.
# Figures from trades/README.md — burdened and break-even hourly rates at the
# shipped defaults, verified by the 29-check run.
# --------------------------------------------------------------------------- #

TRADES = [
 {"key": "electrical-bid-calculator", "slug": "electrical-estimating-template",
  "trade": "Electrical", "lower": "electrical", "art": "an", "worker": "electricians", "items": 40, "waste": 10,
  "wc": "3.50", "burdened": "45.20", "breakeven": "87.84",
  "job": "a service upgrade or a house rewire",
  "wc_story": "Electrical work carries one of the lowest workers' compensation rates in "
              "construction — about $3.50 per $100 of payroll. That is the cheapest labour "
              "burden of the five trades this workbook family covers, and it is why an "
              "electrician can be competitive at an hourly rate a roofer would go broke on.",
  "waste_story": "Wire and conduit get cut to fit, so 10% waste is the default here — the "
                 "highest of the five, because offcuts are unavoidable.",
  "kw": ["electrical estimating template", "electrician bid calculator",
         "electrical contractor pricing spreadsheet", "electrical estimate excel",
         "electrician hourly rate calculator"]},
 {"key": "hvac-bid-calculator", "slug": "hvac-estimating-template",
  "trade": "HVAC", "lower": "HVAC", "art": "an", "worker": "HVAC technicians", "items": 39, "waste": 8,
  "wc": "5.00", "burdened": "44.33", "breakeven": "90.16",
  "job": "a system changeout or a ductwork run",
  "wc_story": "HVAC sits near the bottom of the workers' compensation range at about $5.00 "
              "per $100 of payroll — more than electrical, far less than roofing. The burden "
              "is manageable; what catches HVAC contractors out is equipment cost swinging "
              "faster than their price book.",
  "waste_story": "Duct and refrigerant line waste defaults to 8%.",
  "kw": ["HVAC estimating template", "HVAC bid calculator",
         "HVAC contractor pricing spreadsheet", "hvac estimate excel",
         "hvac labor rate calculator"]},
 {"key": "roofing-bid-calculator", "slug": "roofing-estimating-template",
  "trade": "Roofing", "lower": "roofing", "art": "a", "worker": "roofers", "items": 37, "waste": 12,
  "wc": "28.00", "burdened": "48.98", "breakeven": "95.95",
  "job": "a tear-off and re-roof",
  "wc_story": "This is the number that makes roofing different from every other trade. "
              "Workers' compensation runs about <strong>$28.00 per $100 of payroll</strong> — "
              "eight times what an electrician pays. On a $25 hourly wage that is $7 an hour "
              "of insurance before you have bought a single bundle of shingles. A generic "
              "construction estimating template that assumes a low burden will price your "
              "work below cost every single time.",
  "waste_story": "Roofing waste defaults to 12%, the highest here — hips, valleys and starter "
                 "course all eat material.",
  "kw": ["roofing estimating template", "roofing bid calculator",
         "roofing contractor pricing spreadsheet", "roof estimate excel",
         "roofing labor cost calculator"]},
 {"key": "concrete-bid-calculator", "slug": "concrete-estimating-template",
  "trade": "Concrete", "lower": "concrete", "art": "a", "worker": "concrete crews", "items": 38, "waste": 8,
  "wc": "12.00", "burdened": "42.54", "breakeven": "81.11",
  "job": "a driveway, slab or footing pour",
  "wc_story": "Concrete work carries a workers' compensation rate around $12.00 per $100 of "
              "payroll — roughly three times electrical. Not the worst in construction, but "
              "high enough that pricing off a generic template quietly costs you margin on "
              "every pour.",
  "waste_story": "Concrete waste defaults to 8%, which covers over-order and spillage on a "
                 "typical pour.",
  "kw": ["concrete estimating template", "concrete bid calculator",
         "concrete contractor pricing spreadsheet", "concrete estimate excel",
         "concrete cost per yard calculator"]},
 {"key": "landscaping-bid-calculator", "slug": "landscaping-estimating-template",
  "trade": "Landscaping", "lower": "landscaping", "art": "a", "worker": "landscaping crews", "items": 40, "waste": 8,
  "wc": "8.00", "burdened": "37.66", "breakeven": "66.60",
  "job": "a planting scheme, patio or irrigation run",
  "wc_story": "Landscaping carries a workers' compensation rate near $8.00 per $100 of "
              "payroll. Combined with lower wages than the mechanical trades, that gives the "
              "lowest burdened rate of the five — which is exactly why landscaping is so easy "
              "to underprice: the numbers look forgiving until overhead is added back.",
  "waste_story": "Plant and material waste defaults to 8%.",
  "kw": ["landscaping estimating template", "landscaping bid calculator",
         "landscape contractor pricing spreadsheet", "landscaping estimate excel",
         "landscaping job costing"]},
]

TRADE_TABS = {
 "Start Here": "What to fill in, in what order, and how to import the file into Google Sheets.",
 "Rates": "Your wages, payroll taxes, workers' comp, insurance and overhead. Fill this in once "
          "and every bid you ever write uses it.",
 "Price Book": "{items} {trade_lower} line items with material and labour, as national-average "
               "starting benchmarks you replace with your own.",
 "Estimate": "The job you are pricing. Pick line items, set quantities, and the labour hours "
             "and material add up.",
 "Bid Summary": "Cost, overhead, margin and the price. Shows in dollars what pricing by markup "
                "instead of margin would have cost you on this bid.",
 "Proposal": "A clean version to send the customer, without your cost build-up on it.",
 "Job Costing": "What you actually spent against what you bid, once the job is done.",
}


def _bid_calculator(t: dict) -> dict:
    trade = t["trade"]
    # Not trade.lower(): HVAC is an initialism and reads as "hvac work" otherwise.
    lower = t["lower"]
    art = t["art"]
    tabs = {k: v.format(items=t["items"], trade_lower=lower) for k, v in TRADE_TABS.items()}
    return {
    "key": t["key"],
    "slug": t["slug"],
    "group": "Construction and contracting",
    "category": f"{trade} estimating",
    "pill": "Calculator",
    "card_title": f"{trade} estimating template",
    "card_blurb": f"Burdened labour rate, overhead recovery and margin-not-markup pricing for "
                  f"{lower} work, with a {t['items']}-item price book and job costing.",

    "title": f"{trade} Estimating Template — Bid Calculator for Excel",
    "description": f"Price {lower} work off a burdened hourly rate and a real margin, not a "
                   f"markup. {t['items']}-item price book, proposal and job costing. Excel and "
                   f"Google Sheets.",
    "h1": f"what should you actually charge for {lower} work?",
    "lead": f"Two things sink {art} {lower} bid, and neither is the price book. The first is costing "
            f"an hour of labour at the wage instead of what the hour really costs you. The "
            f"second is adding a percentage on top and calling it your margin. This workbook "
            f"fixes both, then shows you the money the second mistake was taking.",
    "chips": [f"{t['items']} price-book items", "Proposal included"],
    "keywords": t["kw"],

    "short_answer": f"""<p>Charge enough to cover the <strong>burdened</strong> cost of an hour —
wage plus payroll taxes, workers' compensation, liability insurance and benefits, spread over only
the hours you can actually bill — then recover your overhead per hour, then add margin by
<em>dividing</em>, not multiplying.</p>
<p>At this workbook's shipped defaults {art} {lower} hour costs <strong>${t['burdened']}</strong>
burdened, and you need to charge <strong>${t['breakeven']}</strong> an hour just to break even
after overhead. Anything under that is losing money no matter how busy you are.</p>""",

    "problem_h": "Two ways a bid goes wrong before you write the price",
    "problem": f"""<p><strong>The first is the hour.</strong> Suppose you pay {t['worker']} $25 an
hour. That hour does not cost you $25. It costs $25 plus payroll taxes, plus workers'
compensation, plus general liability, plus any benefits. And you cannot bill every hour you pay
for &mdash; driving, quoting, loading the van, waiting on an inspection. So the real cost of a
<em>billable</em> hour is that whole burden divided by the share of hours you can actually
invoice.</p>
<p>{t['wc_story']}</p>
<p><strong>The second is the margin.</strong> You work out the job costs $10,000, you want 30%,
so you multiply by 1.30 and quote $13,000. That is not a 30% margin. It is 23.1%. The margin you
actually got is $3,000 out of $13,000, and $3,000 &divide; $13,000 = 23.1%.</p>
<p>To genuinely make 30% you have to <em>divide</em> by 0.70, which gives $14,286. The difference
on that one job is <strong>$1,286</strong>, and it is invisible, and it happens on every bid you
have ever written that way.</p>""",

    "cost_h": "What markup-instead-of-margin costs on one job",
    "cost_intro": """<p>Same job, same cost, same intention to make 30%. One arithmetic
choice.</p>""",
    "cost_table": table(
        "A $10,000 job, priced two ways, both aiming at 30%",
        ["", "Price quoted#", "Profit#", "Margin actually earned#", ""],
        [["Divide by (1 &minus; margin)", ("$14,286", "good"), ("$4,286", "good"),
          ("30.0%", "good"), "What you meant to do"],
         ["Multiply by (1 + margin)", ("$13,000", "bad"), ("$3,000", "bad"),
          ("23.1%", "bad"), "What most people do"]],
        foot=["Left on the table", ("$1,286", "bad"), ("$1,286", "bad"), ("6.9 pts", "bad"),
              "Every job, every year"]),
    "cost_after": f"""<p>Twenty jobs of that size a year is $25,720. The Bid Summary tab prints
that gap in dollars on every single bid, so you can see what the other way would have cost you
before you send it.</p>""",

    "why_h": f"Why {lower} needs its own workbook",
    "why": f"""<p>The arithmetic is the same in every trade. The <em>inputs</em> are not, and one
of them varies by nearly a factor of ten.</p>
<p>Workers' compensation is priced per $100 of payroll by trade classification, and it ranges from
about $3.50 for electrical to about $28.00 for roofing. {t['waste_story']} A single generic
construction estimating template has to pick one set of assumptions, and it will be wrong for four
trades out of five.</p>
<p>This edition ships with {lower}'s rate, {lower}'s waste factor and a {t['items']}-item
{lower} price book. Every one of those is an input you can change &mdash; but you start from the
right place instead of the average of five trades.</p>""",

    "howto_name": f"How to price {art} {lower} job properly",
    "howto_desc": f"Five steps from your wage bill to {art} {lower} bid that actually earns the "
                  f"margin you intended.",
    "steps": [
     {"h": "Work out what an hour really costs you",
      "plain": "Add payroll taxes, workers' compensation, liability insurance and benefits to the "
               "wage, then divide by the share of paid hours you can actually bill to a customer.",
      "body": f"""<p>Wage plus every payroll cost, divided by the proportion of hours you can
      invoice. At the shipped defaults that comes out at <strong>${t['burdened']}</strong> for
      {art} {lower} hour.</p>
      <p>The non-billable share is the part people leave out, and it is the part that decides the
      answer. If a quarter of your paid hours are not billable, your billable hours have to carry
      a third more cost each.</p>"""},
     {"h": "Recover your overhead per billable hour",
      "plain": "Divide your annual overhead — vehicles, insurance, office, tools, software — by "
               "the number of billable hours you expect in a year, and add that to every hour.",
      "body": f"""<p>Rent, vehicles, phones, software, the person answering the phone: none of it
      is on any single job, and all of it has to be paid by the jobs. Divide the annual total by
      your expected billable hours and add it on.</p>
      <p>Burdened cost plus overhead gives your break-even rate: <strong>${t['breakeven']}</strong>
      an hour at the defaults. Below that you are working for nothing, however full the diary
      is.</p>"""},
     {"h": "Build the job from the price book",
      "plain": "Select the line items the job needs and set quantities. Material and labour hours "
               "total automatically, with the waste factor applied to material.",
      "body": f"""<p>{t['items']} {lower} line items ship with the workbook, each carrying material
      cost and labour hours. Pick what the job needs, set the quantities, and the totals build
      themselves. Waste is applied to material at {t['waste']}%.</p>
      <p>Treat the shipped figures as <strong>starting benchmarks, not quotes</strong>. They are
      national averages. Your supplier and your market are not the national average, and the point
      of the price book is that you overwrite it with your own numbers.</p>"""},
     {"h": "Price by dividing, never by multiplying",
      "plain": "Divide total cost by one minus your margin, commission and fees combined. Do not "
               "multiply cost by one plus the margin.",
      "body": """<pre><code>price = cost / (1 - margin - commission - fees)</code></pre>
      <p>Commission and card fees belong inside that bracket, not bolted on afterwards. If a
      salesperson takes 5% and the card takes 3%, those come out of the top line, so they have to
      be divided out with the margin or they come out of your profit instead.</p>"""},
     {"h": "Cost the job when it is done",
      "plain": "Record actual hours and material against what you bid, so the next estimate is "
               "informed by the last one.",
      "body": """<p>The Job Costing tab puts actual against estimate line by line. This is the tab
      that makes the price book yours: after five jobs you know which items you consistently
      underestimate, and you fix them at the source.</p>"""},
    ],

    "inside_intro": f"""<p>Seven tabs. You fill in the Rates tab once and it drives every bid
after that. The price book ships with {t['items']} {lower} items so you are not starting from an
empty grid.</p>""",
    "tabs": tabs,
    "shot_tab": "Bid Summary",
    "shot_alt": f"The Bid Summary tab of the {lower} estimating template showing cost, overhead, "
                f"margin and the final price",
    "shot_note": "The line comparing margin pricing with markup pricing is on every bid, in "
                 "dollars.",

    "includes": [
     "One .xlsx file, seven tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
     f"A {t['items']}-item {lower} price book with material and labour",
     f"{trade}'s own workers' comp rate and waste factor, not a generic construction average",
     "A customer-facing proposal tab with your cost build-up hidden",
     "Job costing, so the price book improves with every job",
     "Free lifetime updates",
    ],
    "fine": "Price-book figures are national-average starting benchmarks, not quotes for your area.",

    "math_h": "The arithmetic, written out",
    "math": f"""<p>Three formulas. The third is the one that pays for the workbook.</p>
<pre><code>burdened hourly = (wage + taxes + workers comp + GL + benefits)
                  / (1 - non-billable share)

break-even rate = burdened hourly + (annual overhead / annual billable hours)

price           = cost / (1 - margin - commission - fees)</code></pre>
<p>At the shipped {lower} defaults: burdened <strong>${t['burdened']}</strong>, break-even
<strong>${t['breakeven']}</strong>.</p>
<p>Why the third one divides: margin is measured against the <em>price</em>, not the cost. If you
want margin <em>m</em>, then cost has to be the remaining (1 &minus; <em>m</em>) of the price, so
price = cost &divide; (1 &minus; <em>m</em>). Multiplying by (1 + <em>m</em>) measures the margin
against cost instead, which is markup, and markup is always a smaller percentage than the margin
it produces.</p>""",

    "proof": f"""<p>All five editions of this workbook are checked by the same script: 29 numeric
checks per book plus a scan for formula errors. <strong>Last run: 29/29 passing, 0 formula errors
in all five.</strong></p>
<p>Two real failures it has caught, both of which would have shipped silently:</p>
<ul>
<li><strong>Label cells beginning with <code>=</code></strong>. Excel and LibreOffice parse those as
formulas and show <code>#VALUE!</code> where a heading should be.</li>
<li><strong><code>#REF!</code> errors from price-book ranges</strong> that moved when the item count
changed &mdash; the kind of break that only appears on one tab and only after you have already sent
the bid.</li>
</ul>""",

    "versus_h": "Compared with the alternatives",
    "versus_table": table(
        "What else you could do instead",
        ["", "Cost#", "Burdened rate", "Margin done right", f"{trade} rates"],
        [["This workbook", ("$89", "good"), ("Yes", "good"), ("Yes, divides", "good"),
          ("Yes", "good")],
         ["A free estimating template", ("$0", ""), ("Rarely", "bad"),
          ("Almost never", "bad"), ("Generic", "bad")],
         ["Estimating software", "$100&ndash;$400 / month", ("Yes", "good"), ("Yes", "good"),
          ("Yes", "good")],
         ["Pricing off the last job", ("$0", ""), ("No", "bad"), ("No", "bad"), ("No", "bad")]],
    ),

    "faq": [
     ("What is a burdened labour rate?",
      "The full cost of one hour of someone's time, not just their wage. It adds payroll taxes, "
      "workers' compensation, liability insurance and benefits, then divides by the share of paid "
      f"hours you can actually bill. At this workbook's defaults {art} {lower} hour costs "
      f"${t['burdened']} burdened."),
     ("Why is margin not the same as markup?",
      "Markup is measured against your cost; margin is measured against your price. Adding 30% to "
      "a $10,000 cost gives $13,000, and $3,000 profit on $13,000 of revenue is a 23.1% margin, "
      "not 30%. To actually make 30% you divide by 0.70 and quote $14,286."),
     (f"Are the price-book figures real {lower} prices?",
      "They are national-average starting benchmarks, so the workbook is usable the moment you "
      "open it. They are not quotes for your area and are not represented as such. Replace them "
      "with your own supplier pricing as you go."),
     (f"Why is there a separate {lower} edition?",
      "Mostly workers' compensation, which is priced by trade classification and ranges from about "
      "$3.50 per $100 of payroll for electrical to about $28.00 for roofing. Waste factors and "
      "price books differ too. One generic template has to guess, and it guesses wrong for most "
      "trades."),
     ("Will it work in Google Sheets?",
      "Yes. Upload the .xlsx to Google Drive and open it with Google Sheets. There are no macros "
      "and no add-ins, so nothing is lost."),
     ("Can I use it on a Mac without Excel?",
      "Yes. Apple Numbers opens the file directly, and LibreOffice Calc is free and opens it too."),
     ("Can I send the estimate to a customer?",
      "Yes, that is what the Proposal tab is for. It shows the customer what they are buying "
      "without exposing your rates, overhead or margin."),
     ("Does it handle commission and card fees?",
      "Yes, and correctly — they go inside the divisor alongside margin, so they come out of the "
      "price rather than out of your profit."),
    ],
    "related": [
     ("construction-wip-schedule", "Construction WIP schedule — how much of the job you have earned"),
     ("progress-billing-schedule-of-values", "Progress billing — turning the work into an invoice"),
     ("equipment-cost-per-hour", "Equipment cost per hour — what the machines cost you"),
    ],
    }


PRODUCTS_B = [_bid_calculator(t) for t in TRADES] + [

# --------------------------------------------------------------------------- #
{
"key": "progress-billing-schedule-of-values",
"slug": "progress-billing-schedule-of-values",
"group": "Construction and contracting",
"category": "Construction billing",
"pill": "Workbook",
"card_title": "Progress billing and schedule of values",
"card_blurb": "Payment applications with retainage taken net of prior retainage, stored "
              "materials kept separate, and six checks before you submit.",

"title": "Progress Billing & Schedule of Values Template for Excel",
"description": "Build a payment application with the retainage line calculated net of prior "
               "retainage, stored materials separated, and six checks before submission.",
"h1": "the billing line that quietly under-invoices you every month",
"lead": "There is one line on a progress payment application that almost everyone fills in with "
        "the wrong number. It deducts your retainage twice. Each month looks internally "
        "consistent, so nothing ever flags it &mdash; you just get less money than you are owed, "
        "forever.",
"chips": ["6 pre-submission checks", "Change order log"],
"keywords": ["progress billing template", "schedule of values excel",
             "payment application spreadsheet", "construction retainage calculator",
             "contractor billing template", "schedule of values template"],

"short_answer": """<p>A progress billing application asks how much of each contract line you have
completed, adds any materials stored on site, subtracts retainage, and then subtracts what you have
already been paid for.</p>
<p>That last subtraction is where it goes wrong. The &ldquo;less previous certificates&rdquo; line
must be the <strong>prior period's total earned less prior retainage</strong> &mdash; not the
cheque you received, and not the prior net line. Using the cheque deducts retainage a second time
and under-bills you every single month.</p>""",

"problem_h": "Why the same money gets deducted twice",
"problem": """<p>Progress billing works like this. You have done 60% of a $100,000 contract line,
so you have earned $60,000. The customer holds back a percentage &mdash; call it 10% &mdash; as
<strong>retainage</strong>, money kept until the job is finished and signed off. So this month you
can invoice $54,000.</p>
<p>Next month you are at 75%. You have now earned $75,000, retainage is $7,500, so your total
invoiceable to date is $67,500. You have already been billed for some of that, so you subtract what
came before and bill the difference.</p>
<p>Subtract <em>what</em>, exactly? If you subtract the <strong>$54,000 cheque</strong>, you get
$13,500. If you subtract the <strong>prior earned-less-retainage</strong> figure &mdash; which is
also $54,000 &mdash; you get the same answer. On a simple line they agree, which is exactly why the
error survives.</p>
<p>They stop agreeing the moment retainage changes, or stored materials are involved, or a change
order lands mid-job. And when they diverge, the cheque figure is the one that is wrong, because it
has already had retainage taken out of it once.</p>""",

"cost_h": "What it costs on one application",
"cost_intro": """<p>The sample project in the workbook is a $2,931,300 contract. Here is the
retainage line calculated the correct way against the naive way, on a single month's
application.</p>""",
"cost_table": table(
    "Line 7, retainage, on the sample payment application",
    ["", "Retainage on this application#", "Effect on what you get paid"],
    [["Net of prior retainage &mdash; correct", ("$1,046,403", "good"),
      "You invoice everything you have earned this period."],
     ["Gross, ignoring prior retainage", ("$1,162,670", "bad"),
      "Retainage deducted a second time on money already held back."]],
    foot=["Under-billed by", ("$116,267", "bad"), "On one application"]),
"cost_after": """<p>$116,267 that you have earned, that the customer is not disputing, and that
you simply did not ask for. And because each month's application is internally consistent, no
review catches it &mdash; you would have to compare against a correctly built one to see it.</p>""",

"why_h": "The three rules the workbook enforces",
"why": """<p>Beyond that one line, two more rules decide whether an application survives
review.</p>
<p><strong>Stored materials are not completed work.</strong> They usually carry their own retainage
rate, and when the material is installed it moves out of stored and into completed &mdash; never
counted in both at once, which is an easy way to bill the same thing twice.</p>
<p><strong>Only approved change orders move the contract sum.</strong> Pending ones do not, however
confident you are. And every approved change order needs its own line on the schedule of values, or
there is nothing to bill against.</p>""",

"howto_name": "How to build a payment application that gets approved",
"howto_desc": "Five steps to a progress billing application with retainage handled correctly.",
"steps": [
 {"h": "Break the contract into a schedule of values",
  "plain": "List every scheduled item of work with its value. The total must equal the contract "
           "sum, including approved change orders.",
  "body": """<p>Every line of work, with the value assigned to it. The workbook checks that the
  total matches the contract sum to date &mdash; on the sample project both sides are $2,931,300 —
  and tells you if they diverge.</p>"""},
 {"h": "Record progress on each line",
  "plain": "Enter work completed this period and the total completed to date for every line.",
  "body": """<p>Previous periods plus this period gives total completed. The workbook will not let
  a line be billed beyond its scheduled value, which is one of the six controls.</p>"""},
 {"h": "Add stored materials separately",
  "plain": "Enter materials delivered but not yet installed on their own line, with their own "
           "retainage rate. Move them into completed work when they are installed.",
  "body": """<p>The sample application carries $46,370 of stored materials at its own rate. They
  are on the application, they are separated from completed work, and when they get installed they
  move across rather than being counted twice.</p>"""},
 {"h": "Take retainage net of what is already held",
  "plain": "Calculate retainage on the total earned to date, then subtract the retainage already "
           "held from previous applications rather than the payment you received.",
  "body": """<p>This is the rule the product exists for. The workbook derives the previous figure
  from prior completed plus prior stored, so it <strong>cannot be typed in wrong</strong>. You are
  not trusted with it, and neither am I.</p>"""},
 {"h": "Run the checks before you send it",
  "plain": "Verify the schedule of values totals to the contract sum, that no line is over-billed, "
           "that every approved change order has a line, and that the arithmetic identities hold.",
  "body": """<p>Six controls run automatically and produce one verdict. On the sample data it
  reads <code>READY TO SUBMIT</code>. If it does not, it names which control failed rather than
  leaving you to find it.</p>"""},
],

"inside_intro": """<p>Eight tabs, built around a $2.9M sample project with three approved change
orders and stored materials on site, so every rule is visibly exercised.</p>""",
"tabs": {
 "Start Here": "What to fill in, in what order, and how to import the file into Google Sheets.",
 "Schedule of Values": "Every scheduled item with its value. Checked against the contract sum.",
 "Application": "The payment application itself — completed, stored, retainage and the amount due.",
 "Summary": "The top-line figures for the period, in the order a reviewer reads them.",
 "Change Orders": "Approved and pending, kept apart. Only approved ones move the contract sum.",
 "Retainage": "What is held, on what, and at what rate — including a separate rate for stored "
              "materials.",
 "Checks": "Six controls that run before you submit, and one overall verdict.",
 "How It Works": "Every formula and every rule, written out.",
},
"shot_tab": "Application",
"shot_alt": "The Application tab of the progress billing workbook showing completed work, stored "
            "materials, retainage and the amount due this period",
"shot_note": "Line 7 is derived, not typed — which is the whole point.",

"includes": [
 "One .xlsx file, eight tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "A $2.9M sample project with change orders and stored materials already filled in",
 "Retainage taken net of prior retainage, derived so it cannot be mistyped",
 "Six pre-submission controls with a single clear verdict",
 "Free lifetime updates",
],
"fine": "Computes the figures a payment application needs. It is not a copy of any standard form.",

"math_h": "The arithmetic, written out",
"math": """<p>The application is a chain of subtractions, and each line depends on the one before
it.</p>
<pre><code>total completed and stored  = previous periods + this period + stored materials
retainage held to date      = (completed x rate) + (stored x stored rate)
total earned less retainage = total completed and stored - retainage held
less previous certificates  = PRIOR (total completed and stored - retainage held)
current payment due         = total earned less retainage - less previous certificates
balance to finish           = contract sum - total completed and stored</code></pre>
<p>Line 4 is the one that matters. It is the prior period's <em>line 3</em>, recomputed from prior
completed and prior stored &mdash; not the cheque, and not a number anyone types.</p>
<div class="callout callout--warn">
<div class="callout__title">On the standard industry forms</div>
<p>This workbook does not reproduce AIA Document G702 or G703, in whole or in part &mdash; no
layout, no wording, no facsimile. Those forms are copyrighted by the American Institute of
Architects and licensed separately. What this computes is the <em>figures</em> a payment
application requires, which you then transcribe onto whatever form your contract calls for.
Arithmetic is not copyrightable; forms are.</p>
</div>""",

"proof": """<p>Seventeen value checks plus the identities a payment application has to satisfy.
<strong>Last run: 0 mismatches, 0 property failures, 0 formula errors.</strong> Among them: the
schedule of values totals to the contract sum ($2,931,300 on both sides), line 6 equals line 4
minus 5, line 8 equals 6 minus 7, line 9 equals 3 minus 6, pending change orders are excluded from
the contract sum ($27,800 correctly left out), and every approved change order has its own schedule
line.</p>
<p>One bug worth describing, because it is a trap in any spreadsheet. The over-billing control was
written as <code>SUMPRODUCT(--(G &gt; C + 0.01))</code> and reported <strong>17 violations on clean
data</strong> — which turned out to be the 17 empty rows. A blank cell holding <code>""</code> is
<em>text</em>, and in a spreadsheet text compares greater than any number, so <code>"" &gt;
0.01</code> is TRUE. It is guarded with <code>ISNUMBER</code> now. If a check formula in any
spreadsheet ever reports an implausible count, look for this.</p>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "Retainage rule", "Stored materials", "Pre-submission checks"],
    [["This workbook", ("$89", "good"), ("Net of prior", "good"), ("Separated", "good"),
      ("Six", "good")],
     ["A free billing template", ("$0", ""), ("Usually gross", "bad"), ("Mixed in", "bad"),
      ("None", "bad")],
     ["Construction billing software", "$100&ndash;$400 / month", ("Correct", "good"),
      ("Yes", "good"), ("Yes", "good")],
     ["Rebuilding it each month", ("$0", ""), ("Whatever you remember", "bad"),
      ("Varies", "bad"), ("None", "bad")]],
),

"faq": [
 ("What is retainage?",
  "Money the customer holds back from each payment — often 5 or 10 percent — until the job is "
  "finished and signed off. You have earned it, but you do not get it yet."),
 ("What is the 'less previous certificates' line supposed to be?",
  "The prior period's total earned less prior retainage. Not the cheque you were paid, and not the "
  "prior net amount due. Using the cheque deducts retainage twice and under-bills you every month."),
 ("Does this include the AIA G702 and G703 forms?",
  "No. Those forms are copyrighted by the American Institute of Architects and licensed separately. "
  "This workbook computes the figures a payment application needs, which you transcribe onto "
  "whatever form your contract requires."),
 ("How are stored materials handled?",
  "On their own line, with their own retainage rate, and they move into completed work when they "
  "are installed rather than being counted in both places."),
 ("What about change orders?",
  "Approved ones move the contract sum and each gets its own schedule of values line. Pending ones "
  "are logged but excluded — on the sample project that is $27,800 correctly kept out."),
 ("Will it work in Google Sheets?",
  "Yes. Upload the .xlsx to Google Drive and open it with Google Sheets. No macros, no add-ins."),
 ("Can I use it on a Mac without Excel?",
  "Yes. Apple Numbers opens the file directly, and LibreOffice Calc is free."),
 ("What are the six checks?",
  "Schedule of values totals to the contract sum, no line billed past its scheduled value, every "
  "approved change order has a line, the arithmetic identities between lines hold, stored materials "
  "are present and separated, and pending change orders are excluded. They produce one verdict."),
],
"related": [
 ("construction-wip-schedule", "Construction WIP schedule — how much you have actually earned"),
 ("construction-cash-flow-forecast", "Cash flow forecast — when the invoice turns into money"),
 ("electrical-estimating-template", "Contractor bid calculators — pricing the job in the first place"),
],
},

# --------------------------------------------------------------------------- #
{
"key": "construction-cash-flow-forecast",
"slug": "construction-cash-flow-forecast",
"group": "Construction and contracting",
"category": "Construction finance",
"pill": "Forecast",
"card_title": "Construction cash flow forecast",
"card_blurb": "S-curve revenue, split collection lags, retainage release and a line of credit — "
              "to find the month you run out of money.",

"title": "Construction Cash Flow Forecast Template for Excel",
"description": "Forecast the peak funding need across staggered jobs, with S-curve revenue, "
               "collection lags, retainage release and a revolving line of credit.",
"h1": "profitable jobs can still run you out of money",
"lead": "Every job in this forecast makes money. All eight of them. And in month 19 the business "
        "is still $2.2 million in the hole, because you pay for work months before anyone pays "
        "you for it. Profit and cash are different questions, and only one of them can bankrupt "
        "you.",
"chips": ["30-month horizon", "Stress test"],
"keywords": ["construction cash flow forecast", "contractor cash flow template",
             "peak funding need", "construction line of credit calculator",
             "S-curve cash flow excel", "construction cash flow projection"],

"short_answer": """<p>A cash flow forecast works out, month by month, when money actually leaves
and arrives &mdash; not when it is earned. You pay wages this month, materials next month and
subcontractors the month after. The customer pays you a month or two after you invoice, and holds
retainage back for months after that.</p>
<p>The gap between those two timings is your <strong>peak funding need</strong>: the largest amount
you will ever be out of pocket. On the sample scenario &mdash; an $11M-a-year contractor running
eight profitable jobs &mdash; it is <strong>$2,218,817, in month 19</strong>.</p>""",

"problem_h": "Why a profitable business runs out of money",
"problem": """<p>Think about a single job. In month one you pay your crew. In month two you pay
for materials you ordered in month one. In month three the subcontractor's invoice falls due.</p>
<p>Meanwhile you invoice the customer at the end of month one. They pay in month two, or month
three. And they keep 10% back as retainage, which you might see six months after the job
finishes.</p>
<p>So the money goes out first and comes back later. Always. On one job that is a manageable dip.
Now start a second job before the first finishes, and a third, and a fourth &mdash; which is what
growing looks like &mdash; and the dips stack on top of each other.</p>
<p>This is why contractors fail in good years. Every job is profitable and the business still
cannot make payroll, because profit is a fact about the whole job and payroll is a fact about
Friday.</p>""",

"cost_h": "The sample scenario, and where it nearly breaks",
"cost_intro": """<p>Eight staggered jobs, $27.56M of contracts, $3.57M of gross profit. Every job
profitable. Here is what the cash position does anyway.</p>""",
"cost_table": table(
    "An $11M-a-year contractor, 30 months, all jobs profitable",
    ["", "Amount#", "What it means"],
    [["Gross profit across all eight jobs", ("$3,570,000", "good"),
      "The business is genuinely profitable."],
     ["Peak amount drawn on the credit line", ("$2,218,817", "bad"),
      "Month 19. The most you are ever out of pocket."],
     ["Facility available", "$2,500,000",
      "What the bank agreed to lend."],
     ["Headroom at the peak", ("$281,183", "bad"),
      "11% — the workbook flags this as TIGHT."]],
),
"cost_after": """<p>Eleven percent headroom on a facility, in a scenario where nothing has gone
wrong yet. One job slipping a month, or one owner paying late, and the line is exhausted. That is
the number you want to know <em>before</em> you sign the fifth job, and it is why the Stress Test
tab exists.</p>""",

"why_h": "The timing details that decide the answer",
"why": """<p>A forecast that averages everything into one lag gives a smooth, comfortable and
useless curve. The trough forms in the details.</p>
<p><strong>Costs are paid on three different timings.</strong> Labour in the month it happens
&mdash; payroll does not wait. Materials a month later. Subcontractors two months later. Average
those into one number and you flatten out exactly the part that hurts.</p>
<p><strong>Revenue follows an S-curve, not a straight line.</strong> Jobs start slowly, run hard
through the middle and taper. A straight line understates the middle of a job, which is precisely
where the cash trough forms.</p>
<p><strong>Retainage comes back as a lump, months later.</strong> Not as part of ordinary
collections. Treating it as a normal receivable makes the forecast look far healthier than it
is.</p>""",

"howto_name": "How to forecast construction cash flow",
"howto_desc": "Five steps to find the month your business needs the most money.",
"steps": [
 {"h": "Lay out the jobs on a timeline",
  "plain": "Enter each job's contract value, cost, start month and duration, so the model knows "
           "which jobs overlap.",
  "body": """<p>Eight jobs ship in the sample, deliberately staggered. Overlap is the whole point:
  one job at a time never breaks anyone.</p>"""},
 {"h": "Spread revenue along an S-curve",
  "plain": "Distribute each job's revenue across its duration using an S-curve rather than evenly, "
           "because jobs start slowly, peak in the middle and taper.",
  "body": """<pre><code>progress(t) = t^n / (t^n + (1-t)^n)</code></pre>
  <p><em>n</em> is an input. n=1 is a straight line, n=2 is a standard S-curve. The shape matters
  because a straight line understates the middle of the job, and the middle is where the trough
  is.</p>"""},
 {"h": "Set when the money actually arrives",
  "plain": "Enter the collection lag, split so that part of each invoice is paid on time and the "
           "rest a month later, and set when retainage is released.",
  "body": """<p>The split lag is there because real customers are not uniform &mdash; some pay on
  terms, some do not. Retainage is released separately, as one lump per job, months after
  completion.</p>"""},
 {"h": "Set when the money actually leaves",
  "plain": "Enter three separate payment timings: labour in the month it is worked, materials the "
           "following month, subcontractors two months later.",
  "body": """<p>Three timings, not one. This is the step that turns a comfortable forecast into an
  honest one.</p>"""},
 {"h": "Add the credit line and read the peak",
  "plain": "Set the facility size and minimum cash floor. The model draws only enough to hold the "
           "floor and repays surplus, so the peak drawn balance is your true funding need.",
  "body": """<p>The facility is a hard ceiling. If a scenario needs more, the balance pins at the
  limit and cash drops below the floor &mdash; which is the signal you want, rather than a model
  that silently borrows infinite money.</p>
  <p>Peak funding need is the peak <em>drawn balance</em>, not the lowest cash balance. Those
  differ, because a real operator holds cash at the minimum and borrows the rest.</p>"""},
],

"inside_intro": """<p>Eight tabs across a 30-month horizon. The sample is an $11M-a-year general
contractor with eight staggered jobs, sized so the credit line is genuinely tight.</p>""",
"tabs": {
 "Start Here": "What to fill in, in what order, and how to import the file into Google Sheets.",
 "Assumptions": "Collection lags, cost payment timings, retainage rate and release, S-curve shape, "
                "facility size and cash floor.",
 "Jobs": "Each job's contract value, cost, start month and duration.",
 "Revenue & Billing": "Revenue spread along the S-curve, and what gets invoiced each month.",
 "Costs & Payments": "Labour, material and subcontractor costs, each on their own payment timing.",
 "Cash Flow": "The month-by-month position, with credit line draws and repayments, and the peak "
              "funding need.",
 "Stress Test": "What happens when jobs slip, customers pay late, or costs run over.",
 "How It Works": "Every formula, including the S-curve and the credit line logic.",
},
"shot_tab": "Cash Flow",
"shot_alt": "The Cash Flow tab showing monthly opening balance, receipts, payments, line of credit "
            "draws and the peak funding need",
"shot_note": "Month 19 is the peak. Everything before it is the business quietly getting deeper in.",

"includes": [
 "One .xlsx file, eight tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "An eight-job, 30-month sample scenario already filled in",
 "Three separate cost payment timings and a split collection lag",
 "A revolving credit line with a hard ceiling, so over-runs show instead of hiding",
 "A stress test tab for slipping jobs and late payers",
 "Free lifetime updates",
],
"fine": "No subscription, no account, no macros.",

"math_h": "The arithmetic, written out",
"math": """<p>The cash flow itself is a roll-forward, and the identities are what make it
trustworthy.</p>
<pre><code>progress(t)  = t^n / (t^n + (1-t)^n)          # the S-curve
closing(m)   = opening(m) + net(m) + draw(m)
opening(m+1) = closing(m)
draw(m)      = enough to hold the cash floor, capped at the facility
peak need    = MAX(line of credit balance)</code></pre>
<p>One subtlety worth naming: <strong>peak funding need is the peak drawn balance</strong>, not the
lowest cash balance. They are different numbers, because the model keeps cash at the floor and
borrows the difference &mdash; which is what an operator actually does.</p>""",

"proof": """<p>The whole forecast is reimplemented in Python and diffed against the recalculated
workbook, and then the identities are asserted &mdash; a forecast that loses or invents money is
worse than no forecast. <strong>Last run: 0 numeric mismatches, 0 property failures, 0 formula
errors across all 30 months.</strong></p>
<ul>
<li>Closing equals opening plus net movement plus draws, every month</li>
<li>Next month's opening equals this month's closing, every month &mdash; no gaps in the chain</li>
<li>Collections plus retainage released equals total billed, to <strong>$0.00</strong></li>
<li>The credit line balance never goes negative and never exceeds the facility</li>
<li>Draws happen only when the month would otherwise close below the floor &mdash; no spurious
borrowing</li>
<li>All 8 jobs complete inside the horizon</li>
<li>Peak funding need equals the maximum drawn balance: $2,218,817 in month 19</li>
</ul>
<p>Worth noting how the workbook differs from the Python prototype: the prototype said $2,032,409.
The workbook says $2,218,817 because it <strong>charges interest on the drawn balance</strong> and
the prototype did not. The workbook is the more complete model.</p>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "Cost timings", "S-curve", "Credit line modelled"],
    [["This workbook", ("$99", "good"), ("Three, separate", "good"), ("Yes, tunable", "good"),
      ("Yes, with a ceiling", "good")],
     ["A free cash flow template", ("$0", ""), ("One average lag", "bad"), ("Straight line", "bad"),
      ("No", "bad")],
     ["Construction ERP", "$300&ndash;$1,000 / month", ("Yes", "good"), ("Yes", "good"),
      ("Yes", "good")],
     ["Your bank's forecast form", ("$0", ""), ("One lag", "bad"), ("No", "bad"), ("No", "bad")]],
),

"faq": [
 ("What is peak funding need?",
  "The largest amount you will ever be out of pocket across the forecast — the deepest point of "
  "the cash trough. It is what determines how big a credit line you need. On the sample scenario "
  "it is $2,218,817, in month 19."),
 ("How can profitable jobs cause a cash problem?",
  "Because you pay for work before you get paid for it. Wages go out weekly; customer payments "
  "arrive a month or two after invoicing; retainage arrives months after that. Overlap several "
  "jobs and those gaps stack up."),
 ("What is an S-curve and why does it matter?",
  "It is the shape of how a job actually consumes budget — slow at the start, fast in the middle, "
  "tapering at the end. A straight-line forecast understates the middle of a job, and the middle "
  "is exactly where the cash trough forms."),
 ("Why three separate cost payment timings?",
  "Because labour, materials and subcontractors are paid on completely different schedules. "
  "Payroll cannot wait; material invoices run about a month; subcontractors about two. Averaging "
  "them hides the part that hurts."),
 ("What does the stress test do?",
  "Pushes the scenario — jobs slipping, customers paying late, costs over-running — so you can see "
  "how much headroom you really have. The sample is deliberately tight at 11% so the stress test "
  "has something to break."),
 ("Will it work in Google Sheets?",
  "Yes. Upload the .xlsx to Google Drive and open it with Google Sheets. No macros or add-ins."),
 ("Can I use it on a Mac without Excel?",
  "Yes. Apple Numbers opens the file directly, and LibreOffice Calc is free."),
 ("How many jobs and months does it cover?",
  "Eight jobs across a 30-month horizon in the sample. You can change the jobs; the horizon is "
  "built into the model."),
],
"related": [
 ("construction-wip-schedule", "Construction WIP schedule — what you have earned, as opposed to collected"),
 ("progress-billing-schedule-of-values", "Progress billing — getting the invoice right in the first place"),
 ("equipment-cost-per-hour", "Equipment cost per hour — own or rent, and what it does to cash"),
],
},

# --------------------------------------------------------------------------- #
{
"key": "equipment-fleet-cost-per-hour",
"slug": "equipment-cost-per-hour",
"group": "Construction and contracting",
"category": "Equipment costing",
"pill": "Calculator",
"card_title": "Equipment cost per hour",
"card_blurb": "What each machine costs per hour owned versus rented, the break-even hours, and "
              "which machines you should not own at all.",

"title": "Equipment Cost Per Hour Calculator — Own vs Rent, Excel",
"description": "Work out the true hourly cost of owning a machine, the charge-out rate it needs, "
               "and the hours per year below which renting is cheaper.",
"h1": "the machine costs money on the days it sits still",
"lead": "A digger parked in the yard is still depreciating, still insured, still financed and "
        "still taxed. Those costs do not care how many hours it worked. Which means the fewer "
        "hours you use it, the more each of those hours costs &mdash; and below a certain point, "
        "renting is simply cheaper.",
"chips": ["8-machine sample fleet", "Own vs rent verdict"],
"keywords": ["equipment cost per hour calculator", "own vs rent equipment",
             "machine hourly rate calculator", "equipment charge out rate",
             "construction equipment cost spreadsheet", "equipment break even hours"],

"short_answer": """<p>A machine has two kinds of cost. <strong>Fixed</strong> costs &mdash;
depreciation, interest, insurance, tax, storage &mdash; happen every year whether it moves or not.
<strong>Operating</strong> costs &mdash; fuel, tyres, repairs &mdash; only happen when it works.</p>
<p>Divide the fixed cost by the hours you actually use it, add the operating cost per hour, and you
have the true hourly cost. Compare that against the rental rate and you get a break-even: the
number of hours a year below which owning the machine is the more expensive choice.</p>""",

"problem_h": "Why low hours make a machine expensive",
"problem": """<p>Say a machine costs you $40,000 a year to own before it turns a wheel &mdash;
depreciation, the loan, insurance, tax, somewhere to keep it.</p>
<p>Work it 2,000 hours a year and that is $20 an hour. Work it 500 hours and the same $40,000
becomes <strong>$80 an hour</strong>. The machine did not change. Your utilisation did.</p>
<p>This is why the machine you bought because &ldquo;we needed one on that job&rdquo; can be the
most expensive thing in the yard. It is not costing you anything visible &mdash; there is no
invoice for a parked digger &mdash; but the depreciation is happening regardless, and the hours it
is not working are hours that cost is not being spread over.</p>
<p>In the sample fleet, three machines out of eight fall below their break-even. The dozer runs 640
hours a year and costs <strong>$184 an hour owned</strong> against <strong>$111 an hour
rented</strong>.</p>""",

"cost_h": "The three machines that should not be owned",
"cost_intro": """<p>An eight-machine sample fleet, $1.59M of equipment. Five machines earn their
keep. Three do not, and the workbook says so.</p>""",
"cost_table": table(
    "Machines below their break-even hours in the sample fleet",
    ["Machine", "Hours per year#", "Cost per hour owned#", "Cost per hour rented#", "Verdict"],
    [["Dozer", ("640", ""), ("$184", "bad"), ("$111", "good"), ("RENT", "bad")],
     ["Telehandler", ("520", ""), ("&mdash;", ""), ("&mdash;", ""), ("RENT", "bad")],
     ["Roller", ("380", ""), ("&mdash;", ""), ("&mdash;", ""), ("RENT", "bad")]],
    foot=["Avoidable cost across the three", "", ("$43,010 / year", "bad"), "", ""]),
"cost_after": """<p>$43,010 a year, on three machines nobody thought were a problem, because a
parked machine never sends you a bill. The other five come out as OWN &mdash; this is not an
argument against owning equipment, it is an argument for knowing which ones.</p>""",

"why_h": "The modelling mistake I made first, and had to undo",
"why": """<p>My first version costed depreciation <em>per hour</em>. It seemed reasonable: more
hours, more wear, more depreciation.</p>
<p>It is wrong, and it broke the product. Costing depreciation per hour makes it a
<strong>variable</strong> cost that scales with use &mdash; which means the &ldquo;annual fixed
cost&rdquo; is no longer fixed, and the whole own-versus-rent comparison stops meaning anything.
The verifier caught it: at the computed break-even hours, owning and renting differed by up to
<strong>$5,192</strong> when by definition they should have been equal.</p>
<p>Depreciation is <strong>time-based</strong>. A machine loses value sitting in the yard. The
model was restructured so depreciation runs per year, interest uses life in years directly, and
repairs are direct per-hour inputs rather than factors on hourly depreciation. After that the
identity holds at <strong>$0.0000</strong> for every machine.</p>""",

"howto_name": "How to work out what a machine really costs per hour",
"howto_desc": "Five steps from purchase price to an own-or-rent verdict per machine.",
"steps": [
 {"h": "Work out the annual fixed cost",
  "plain": "Add depreciation per year, interest on the average investment, insurance, tax and "
           "storage. These happen whether the machine works or not.",
  "body": """<p>Depreciation is <strong>per year</strong>, not per hour: purchase price less
  residual, divided by life in years. Interest uses the average annual investment. Insurance, tax
  and storage are annual figures.</p>
  <p>Tyres and undercarriage are deliberately excluded from the depreciable base and costed over
  their own life instead &mdash; they wear out several times over a machine's life, so treating
  them as part of the machine understates both.</p>"""},
 {"h": "Work out the operating cost per hour",
  "plain": "Add fuel, lubricants, tyres or undercarriage wear, repairs and any ground engaging "
           "tools, as direct costs per working hour.",
  "body": """<p>All of these are per-hour by nature &mdash; they only happen when the machine
  runs. Repairs are entered as a direct $/hr input rather than derived as a factor on
  depreciation, because a machine does not wear faster per hour just because it works fewer
  hours.</p>"""},
 {"h": "Divide the fixed cost by the hours you actually use it",
  "plain": "Divide annual fixed cost by realistic annual hours, then add operating cost per hour "
           "to get the total cost per hour.",
  "body": """<p>Be honest about the hours. This is the input that decides the answer, and it is
  the one people inflate. The Utilisation tab shows the whole curve, so you can see how sharply
  the cost per hour climbs as hours fall.</p>"""},
 {"h": "Build the charge-out rate",
  "plain": "Add overhead recovery to the total cost per hour, then apply margin by dividing by "
           "one minus the margin.",
  "body": """<pre><code>rate = (cost per hour + overhead) / (1 - margin)</code></pre>
  <p>Margin divides, exactly as in the bid calculators. Multiplying gives you a smaller margin
  than you asked for.</p>"""},
 {"h": "Compare against renting, and only strip what a renter avoids",
  "plain": "Divide annual fixed cost by the rental rate less only the costs a renter avoids, to "
           "get the break-even hours per year.",
  "body": """<pre><code>break-even hours = fixed / (rental per hour - tyres - repairs - GET)</code></pre>
  <p>Fuel and lubricants are <em>not</em> subtracted. You buy those either way, whether the machine
  is yours or rented, so removing them would double-count and always flatter renting.</p>
  <p>Rental is priced by <strong>time</strong>: the effective rental rate is the monthly rate
  divided by the hours a rented machine really delivers in a month. That divisor is an input
  &mdash; 130 in the sample, not 173 &mdash; because it quietly decides the whole answer.</p>"""},
],

"inside_intro": """<p>Nine tabs around an eight-machine sample fleet worth $1.59M, tuned so the
answer is genuinely mixed: five machines to own, three to rent.</p>""",
"tabs": {
 "Start Here": "What to fill in, in what order, and how to import the file into Google Sheets.",
 "Rates": "Interest, insurance, tax, storage, fuel price, overhead and margin — set once.",
 "Fleet": "Your machines: purchase price, residual, life, annual hours and rental rates.",
 "Ownership Cost": "The annual fixed cost per machine — depreciation, interest, insurance, tax, "
                   "storage.",
 "Operating Cost": "Fuel, lubricants, tyres, repairs and ground engaging tools, per working hour.",
 "Rate Build-Up": "Cost per hour, plus overhead, plus margin, giving the rate to charge.",
 "Own vs Rent": "Break-even hours per machine and a verdict, machine by machine.",
 "Utilisation": "How cost per hour changes as annual hours change, across the whole fleet.",
 "How It Works": "Every formula, including why depreciation is time-based.",
},
"shot_tab": "Rate Build-Up",
"shot_alt": "The Rate Build-Up tab showing cost per hour, overhead and margin for each machine in "
            "the fleet",
"shot_note": "Operator wages are deliberately not in here — you pick either a labour rate or a "
             "machine rate and stay consistent.",

"includes": [
 "One .xlsx file, nine tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "An eight-machine sample fleet with a genuinely mixed own/rent answer",
 "Time-based depreciation, so the break-even actually balances",
 "Break-even hours and a verdict per machine",
 "A utilisation curve showing how fast low hours hurt",
 "Free lifetime updates",
],
"fine": "Operator wages are excluded by design, and it says so on Start Here.",

"math_h": "The arithmetic, written out",
"math": """<pre><code>annual fixed     = depreciation/yr + interest + insurance + tax + storage
fixed per hour   = annual fixed / annual hours
total per hour   = fixed per hour + operating per hour
charge-out rate  = (total per hour + overhead) / (1 - margin)
break-even hours = annual fixed / (rental/hr - tyres - repairs - GET)</code></pre>
<p>Two things in that last line are easy to get wrong and both always favour renting if you do.</p>
<p><strong>Only subtract what a renter genuinely avoids.</strong> Fuel and lubricants are bought
either way, so they cancel. Comparing a full ownership rate against a bare rental rate
double-counts them.</p>
<p><strong>Rental is priced by time, not by the hour.</strong> The effective rental rate is the
monthly rate divided by the hours a rented machine really delivers &mdash; 130 a month in the
sample, not the 173 that a full month of eight-hour days would suggest.</p>""",

"proof": """<p>The verifier reimplements the model in Python, recalculates the workbook, and
asserts the identity that <em>is</em> the product: <strong>at the computed break-even hours, the
annual cost of owning must equal the annual cost of renting</strong>. If those two are not equal at
the break-even, the verdict is guesswork.</p>
<p><strong>Last run: 0 numeric mismatches, 0 property failures, 0 formula errors. Worst gap at
break-even: $0.0000.</strong></p>
<ul>
<li>Depreciation per year &times; life in years equals the depreciable base &mdash; exact</li>
<li>Ownership per hour &times; hours equals annual fixed cost &mdash; exact</li>
<li>The utilisation grid matches fixed-per-hour plus operating &mdash; all 8 machines &times; 8
steps</li>
<li>Rate &times; (1 &minus; margin) equals cost plus overhead &mdash; margin divides, never
multiplies</li>
<li>Both OWN and RENT verdicts appear in the sample data &mdash; 5 and 3</li>
<li>The avoidable-cost figure matches: 3 machines, $43,010</li>
</ul>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "Depreciation", "Break-even balances", "Own/rent verdict"],
    [["This workbook", ("$89", "good"), ("Time-based", "good"), ("To $0.0000", "good"),
      ("Per machine", "good")],
     ["A free equipment cost sheet", ("$0", ""), ("Usually per hour", "bad"),
      ("Not checked", "bad"), ("No", "bad")],
     ["Fleet management software", "$200&ndash;$800 / month", ("Correct", "good"),
      ("Yes", "good"), ("Yes", "good")],
     ["The manufacturer's rate guide", ("$0", ""), ("Generic", "bad"), ("No", "bad"),
      ("No", "bad")]],
),

"faq": [
 ("Why is depreciation per year rather than per hour?",
  "Because a machine loses value sitting in the yard. Costing it per hour makes it a variable cost "
  "that scales with use, which means annual fixed cost is no longer fixed — and the own-versus-rent "
  "break-even stops balancing. I built it the wrong way first and the verifier caught it, with gaps "
  "up to $5,192."),
 ("What are break-even hours?",
  "The annual hours below which renting the machine costs less than owning it. Below the break-even "
  "the fixed costs are being spread over too few hours."),
 ("Why is fuel not subtracted in the break-even?",
  "Because you buy fuel whether the machine is yours or rented, so it cancels out. Subtracting it "
  "would double-count and make renting look better than it is."),
 ("Does it include the operator's wages?",
  "No, deliberately, and Start Here explains why. You either charge a labour rate or a machine rate; "
  "including wages in both is the most common way to double-charge a customer."),
 ("How many machines does it handle?",
  "Eight are filled in as a sample fleet worth $1.59M. You add rows the normal way."),
 ("Will it work in Google Sheets?",
  "Yes. Upload the .xlsx to Google Drive and open it with Google Sheets. No macros, no add-ins."),
 ("Can I use it on a Mac without Excel?",
  "Yes. Apple Numbers opens the file directly, and LibreOffice Calc is free."),
 ("How do I set the rental hours divisor?",
  "It is the hours a rented machine really delivers in a month, and it is an input because it "
  "quietly decides the whole answer. The sample uses 130 rather than a theoretical 173."),
],
"related": [
 ("construction-cash-flow-forecast", "Cash flow forecast — what buying the machine does to your cash"),
 ("construction-wip-schedule", "Construction WIP schedule — how much of each job you have earned"),
 ("electrical-estimating-template", "Contractor bid calculators — putting the machine rate into a bid"),
],
},

# --------------------------------------------------------------------------- #
{
"key": "certified-payroll-davis-bacon",
"slug": "certified-payroll-davis-bacon",
"group": "Construction and contracting",
"category": "Prevailing wage",
"pill": "Calculator",
"card_title": "Certified payroll and Davis-Bacon fringe",
"card_blurb": "Annualises the fringe credit over total annual hours, not Davis-Bacon hours — the "
              "error that creates back-wage liability.",

"title": "Certified Payroll & Davis-Bacon Fringe Calculator for Excel",
"description": "Annualise fringe benefit credits over total annual hours, handle overtime "
               "correctly, and lay the week out in WH-347 order. Excel and Google Sheets.",
"h1": "the fringe credit mistake that becomes back wages",
"lead": "If you work federally funded jobs, you can count the cost of benefits toward the wage you "
        "owe. But you have to divide that annual cost by <em>every</em> hour the employee worked "
        "&mdash; not just the hours on the public job. Divide by the wrong number and you underpay "
        "people, legally owe the difference, and find out at audit.",
"chips": ["WH-347 order", "6-employee sample crew"],
"keywords": ["certified payroll excel", "davis bacon fringe calculator",
             "prevailing wage fringe annualization", "WH-347 template",
             "certified payroll report spreadsheet", "davis bacon compliance"],

"short_answer": """<p>Under Davis-Bacon you owe a base hourly wage plus a fringe amount. You can
meet the fringe by paying cash, by providing benefits, or both. To work out how much hourly credit
a benefit plan is worth, divide the plan's <strong>annual cost</strong> by the employee's
<strong>total annual hours</strong> &mdash; public and private work combined.</p>
<p>Dividing by Davis-Bacon hours alone inflates the credit, so the cash fringe you pay is too
small, and the shortfall is back wages you owe. On this workbook's six-person sample crew that
error totals <strong>$31,543</strong>.</p>""",

"problem_h": "Why the divisor has to be every hour",
"problem": """<p>Here is the idea in ordinary terms. You pay $20,900 a year for someone's health
plan. That plan covers them for the whole year &mdash; all 2,080 hours they work, not just the
weeks they happen to be on a government job.</p>
<p>So the hourly value of that plan is $20,900 &divide; 2,080 = <strong>$10.05 an hour</strong>.
That is the credit you can take against the fringe you owe.</p>
<p>Now suppose only 760 of those hours were on the public job. If you divide by 760 instead, you
get $27.50 an hour of &ldquo;credit&rdquo;. But you did not spend $27.50 an hour on that person's
benefits. You spent $10.05. The extra $17.45 is imaginary.</p>
<p>And the imaginary part has a real consequence: you took credit for it, so you paid $17.45 an
hour less in cash fringe than you owed. Multiply by 760 hours and that is
<strong>$9,653</strong> of back wages for one employee.</p>
<p>There is a principle behind the rule, too. If you could divide by public hours only, the
government job would be paying for benefits the worker also enjoys on private work &mdash; which
is precisely the subsidy the rule exists to prevent.</p>""",

"cost_h": "The same crew, both ways",
"cost_intro": """<p>Six employees, real plan costs, real hour splits. The exposure column is what
you would owe in back wages.</p>""",
"cost_table": table(
    "Fringe credit per hour, annualised correctly and incorrectly",
    ["Employee", "Total hours#", "D-B hours#", "Plan cost / yr#", "Correct#", "If you divide "
     "by D-B hours#", "Back-wage exposure#"],
    [["R. Alvarez", "2,080", "760", "$20,900", ("$10.05", "good"), ("$27.50", "bad"),
      ("$9,653", "bad")],
     ["T. Nguyen", "2,080", "1,520", "$20,900", ("$10.05", "good"), ("$13.75", "bad"),
      ("$5,627", "bad")],
     ["K. Whitfield", "1,960", "540", "$13,600", ("$6.94", "good"), ("$25.19", "bad"),
      ("$3,624", "bad")],
     ["M. Okafor", "2,120", "1,840", "$12,000", ("$5.66", "good"), ("$6.52", "bad"),
      ("$1,585", "bad")],
     ["D. Brennan", "2,040", "620", "$18,900", ("$9.26", "good"), ("$30.48", "bad"),
      ("$6,284", "bad")],
     ["S. Petrov", "1,880", "410", "$20,900", ("$11.12", "good"), ("$50.98", "bad"),
      ("$4,770", "bad")]],
    foot=["Total exposure", "", "", "", "", "", ("$31,543", "bad")]),
"cost_after": """<p>Look at the pattern rather than the total. <strong>The smaller someone's
Davis-Bacon share of the year, the worse the error gets.</strong> S. Petrov worked only 22% of the
year on public work, and the wrong divisor inflates their credit by more than four times.</p>
<p>Which means the exposure is largest for exactly the employees you think about least &mdash; the
ones who only occasionally touch a federal job.</p>""",

"why_h": "The other rule people get wrong: overtime",
"why": """<p>Overtime on prevailing wage work has a rule that looks fiddly and is actually
simple.</p>
<p>The overtime premium applies to the <strong>base rate only</strong>. The fringe is never
multiplied by 1.5. You owe the fringe on every hour at its flat rate, including overtime hours,
because the fringe is a benefit cost and benefits do not accrue faster in hour 41.</p>
<p>Get that backwards and you overpay, which is at least not a liability &mdash; but combined with
an inflated fringe credit it can mask the underpayment underneath.</p>
<p>The workbook also handles <strong>split classifications</strong>: someone who works part of a
week as an electrician and part as an apprentice, at different determined rates.</p>""",

"howto_name": "How to calculate a Davis-Bacon fringe credit",
"howto_desc": "Five steps to a certified payroll that will survive an audit.",
"steps": [
 {"h": "Get the wage determination for the job",
  "plain": "Record the base rate and fringe rate for every classification on the contract.",
  "body": """<p>Every classification you will use, with its base and fringe. This is what you are
  measured against, and it is contract-specific.</p>"""},
 {"h": "Record total annual hours per employee, not just public hours",
  "plain": "For each employee, record all hours worked in the year across every job, and "
           "separately the hours on Davis-Bacon work.",
  "body": """<p>Both numbers, for everyone. The total is the divisor; the Davis-Bacon figure is
  what the credit gets applied to. Most compliance problems begin with nobody tracking the first
  one.</p>"""},
 {"h": "Annualise each benefit plan",
  "plain": "Divide the annual cost of each benefit plan by the employee's total annual hours to "
           "get the hourly credit.",
  "body": """<pre><code>hourly fringe credit = annual plan cost / TOTAL annual hours</code></pre>
  <p>Total. Not Davis-Bacon hours. This single line is the reason the workbook exists.</p>
  <p>Some defined-contribution pension plans with immediate vesting, and certain unfunded plans,
  are treated differently. If you think a plan qualifies for an exception, get that confirmed
  rather than assuming it &mdash; the general rule is annualisation and the exceptions are
  narrow.</p>"""},
 {"h": "Work out the cash fringe still owed",
  "plain": "Subtract the total hourly credit from the required fringe rate. Anything left over "
           "must be paid in cash. Credit is capped at the fringe you actually owe.",
  "body": """<p>You cannot claim more credit than the fringe you owe, so each employee's credit is
  capped at the required rate. The remainder is cash.</p>"""},
 {"h": "Apply overtime to the base rate only",
  "plain": "Multiply the base rate by 1.5 for overtime hours. Pay the fringe at its flat rate on "
           "every hour, including overtime hours.",
  "body": """<p>Premium on base, fringe flat. Then the Weekly Payroll and WH-347 Output tabs lay
  the week out in the order the form expects.</p>"""},
],

"inside_intro": """<p>Eight tabs, with a six-person crew filled in &mdash; deliberately including
people whose Davis-Bacon share ranges from 22% to 87% of the year, because that spread is where the
error lives.</p>""",
"tabs": {
 "Start Here": "What to fill in, in what order, and how to import the file into Google Sheets.",
 "Wage Determination": "Base and fringe rates for every classification on the contract.",
 "Employees": "Your crew, their classifications, and both hour totals — annual and Davis-Bacon.",
 "Annualization": "The calculation this workbook exists for: plan cost divided by total annual "
                  "hours, with the exposure if you got it wrong.",
 "Weekly Payroll": "The week being reported — hours by day, classification, gross pay and "
                   "deductions.",
 "WH-347 Output": "The same week laid out in the order the WH-347 form expects, ready to "
                  "transcribe.",
 "Checks": "Controls that run before you certify anything.",
 "How It Works": "Every rule and every formula, including the overtime treatment.",
},
"shot_tab": "Annualization",
"shot_alt": "The Annualization tab showing correct and incorrect fringe credits per employee with "
            "the resulting back-wage exposure",
"shot_note": "The exposure column is the credit you would wrongly have claimed, less the credit "
             "you were entitled to, multiplied by Davis-Bacon hours.",

"includes": [
 "One .xlsx file, eight tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "A six-person sample crew spanning a wide range of Davis-Bacon shares",
 "Annualisation done correctly, with the exposure of getting it wrong shown alongside",
 "Correct overtime treatment — premium on base, fringe flat",
 "Split classifications within a week",
 "Free lifetime updates",
],
"fine": "A calculation tool, not legal advice. It computes figures you transcribe onto the form.",

"math_h": "The arithmetic, written out",
"math": """<p>One line is the product. The rest follows from it.</p>
<pre><code>hourly fringe credit = annual plan cost / TOTAL annual hours worked

credit claimed       = MIN(hourly fringe credit, required fringe rate)
cash fringe owed     = required fringe rate - credit claimed
overtime pay         = base rate x 1.5        # fringe is NEVER x1.5
gross                = (base x hours) + (premium x OT hours) + (fringe x all hours)</code></pre>
<p>And the exposure calculation used in the table above:</p>
<pre><code>exposure = (wrong credit - right credit, each capped at the required fringe)
           x Davis-Bacon hours</code></pre>
<p>The capping matters. You cannot claim more credit than the fringe you owe, so an absurd
&ldquo;credit&rdquo; of $50.98 does not create $50.98 of exposure &mdash; it creates exposure up to
the fringe rate. The workbook caps it, which is why the numbers in that table are lower than a
naive subtraction would give.</p>""",

"proof": """<p>Every figure on this page comes from the workbook's own checker, which reimplements
the calculation in Python and diffs it against the recalculated file &mdash; including a separate
test for negative and edge-case inputs.</p>
<p>The seeded crew was built to exercise the range rather than to produce a dramatic total: hour
splits run from 410 Davis-Bacon hours out of 1,880 up to 1,840 out of 2,120, so you can see the
error growing as the public share shrinks. That relationship is the thing worth understanding, and
a tidier example would have hidden it.</p>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "Annualisation", "Overtime rule", "WH-347 order"],
    [["This workbook", ("$89", "good"), ("Total hours", "good"), ("Premium on base", "good"),
      ("Yes", "good")],
     ["A free certified payroll form", ("$0", ""), ("Not calculated", "bad"),
      ("Up to you", "bad"), ("Yes", "good")],
     ["Certified payroll software", "$50&ndash;$300 / month", ("Correct", "good"),
      ("Correct", "good"), ("Yes", "good")],
     ["Your payroll provider", "Varies", ("Often not", "bad"), ("Correct", "good"),
      ("Sometimes", "")]],
),

"faq": [
 ("What is annualisation?",
  "Working out the hourly value of a benefit plan by dividing its annual cost by the employee's "
  "total annual hours — every hour they worked, public and private. It is the general rule under "
  "Davis-Bacon, and the exceptions to it are narrow."),
 ("Why can't I divide by Davis-Bacon hours only?",
  "Because the plan covers the employee all year, not just on the public job. Dividing by public "
  "hours alone would mean the government contract is paying for benefits the worker also enjoys on "
  "private work — the exact subsidy the rule prevents. It also inflates your credit, so you underpay "
  "cash fringe and owe back wages."),
 ("How much can this cost?",
  "It scales inversely with the Davis-Bacon share of someone's year. On the sample crew the "
  "exposure ranges from $1,585 for someone who works 87% of the year on public jobs to $9,653 for "
  "someone at 37%. Across six people it totals $31,543."),
 ("Is the fringe multiplied by 1.5 on overtime?",
  "No. The overtime premium applies to the base rate only. The fringe is owed at its flat rate on "
  "every hour, including overtime hours."),
 ("Does it produce the WH-347 form itself?",
  "It produces the figures in the order the WH-347 expects, ready to transcribe. It is a "
  "calculation tool, not a copy of the government form."),
 ("Can it handle someone working two classifications in a week?",
  "Yes. Split classifications at different determined rates within the same week are supported."),
 ("Will it work in Google Sheets?",
  "Yes. Upload the .xlsx to Google Drive and open it with Google Sheets. No macros, no add-ins."),
 ("Is this legal advice?",
  "No. It is a calculator that applies the annualisation rule correctly. If you think one of your "
  "plans qualifies for an exception, confirm that with someone qualified rather than assuming it."),
],
"related": [
 ("progress-billing-schedule-of-values", "Progress billing — invoicing the job you are staffing"),
 ("electrical-estimating-template", "Contractor bid calculators — pricing prevailing wage labour"),
 ("construction-wip-schedule", "Construction WIP schedule — earned revenue across your jobs"),
],
},
]

for _p in PRODUCTS_B:
    _p.setdefault("diagram_problem", V[_p["key"]]["problem"])
    _p.setdefault("diagram_fix", V[_p["key"]]["fix"])
