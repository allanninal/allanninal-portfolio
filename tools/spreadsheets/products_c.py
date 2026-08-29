#!/usr/bin/env python3
"""Product articles, part C — deal analysis, importing, statistics and grants.

The five underwriting models are built by a factory for the same reason as the
bid calculators: one engine, five asset classes. But the opening figures are
each deal's own, from underwriting/README.md, and they differ enough to change
what each page is about. Self-storage at a 7.92% levered IRR and a laundromat at
51.60% are not the same investment story, and the pages do not pretend they are.
"""
from build_product import table
from visuals import V

# --------------------------------------------------------------------------- #
# Underwriting models. Opening figures at the shipped defaults, from the 24
# checks per model (120 total) in underwriting/verify_math.py.
# --------------------------------------------------------------------------- #

ASSETS = [
 {"key": "self-storage-underwriting-model", "slug": "self-storage-underwriting-model",
  "asset": "Self-Storage", "lower": "self-storage facility", "plural": "self-storage facilities",
  "going_in": "6.76% cap", "dscr": "1.60", "irr": "7.92%", "multiple": "1.42x",
  "exit": "Cap rate", "exit_lower": "an exit cap rate",
  "revenue": "unit mix by size, occupancy, street rate and the gap between street and in-place rents",
  "story": "Storage lands at a 7.92% levered IRR here, and that is not a flaw in the model — it "
           "is the arithmetic of buying at a 6.76% cap and exiting at a slightly higher one. The "
           "seed deal is underwritten conservatively on purpose, with the exit cap set above the "
           "going-in cap. A model that shows you 20% on default assumptions is selling you "
           "something.",
  "kw": ["self storage underwriting model", "self storage financial model excel",
         "storage facility proforma", "self storage deal analyzer",
         "self storage irr calculator"]},
 {"key": "car-wash-underwriting-model", "slug": "car-wash-underwriting-model",
  "asset": "Car Wash", "lower": "express tunnel car wash", "plural": "car washes",
  "going_in": "8.48% cap", "dscr": "1.50", "irr": "10.71%", "multiple": "1.59x",
  "exit": "Cap rate", "exit_lower": "an exit cap rate",
  "revenue": "cars per day, average ticket, the mix between retail washes and unlimited "
             "memberships, and member churn",
  "story": "A car wash is closer to an operating business than a piece of real estate, and the "
           "membership base is most of the value. The revenue build makes you state cars per day, "
           "ticket, member count and churn separately, because a deal that works at 1,200 cars a "
           "day and 40% membership does not work at 900 and 20%.",
  "kw": ["car wash underwriting model", "car wash financial model excel",
         "express tunnel car wash proforma", "car wash deal analyzer",
         "car wash investment calculator"]},
 {"key": "rv-park-underwriting-model", "slug": "rv-park-underwriting-model",
  "asset": "RV Park", "lower": "RV park or campground", "plural": "RV parks",
  "going_in": "8.01% cap", "dscr": "1.76", "irr": "7.02%", "multiple": "1.36x",
  "exit": "Cap rate", "exit_lower": "an exit cap rate",
  "revenue": "nightly, weekly and monthly site rates, seasonal occupancy, and ancillary income "
             "from stores, laundry and utilities",
  "story": "RV parks have the widest seasonality of anything in this family, and the model makes "
           "you say so rather than assuming a flat year. The seed deal shows the highest DSCR "
           "here at 1.76 and the lowest IRR at 7.02% — safe debt coverage and modest returns, "
           "which is an honest picture of a conservatively bought park.",
  "kw": ["rv park underwriting model", "campground financial model excel",
         "rv park proforma", "rv park deal analyzer", "campground investment calculator"]},
 {"key": "mobile-home-park-underwriting-model", "slug": "mobile-home-park-underwriting-model",
  "asset": "Mobile Home Park", "lower": "mobile home park", "plural": "mobile home parks",
  "going_in": "7.06% cap", "dscr": "1.58", "irr": "10.83%", "multiple": "1.89x",
  "exit": "Cap rate", "exit_lower": "an exit cap rate",
  "revenue": "lot rent, park-owned versus tenant-owned homes, occupancy, and how utilities are "
             "billed back",
  "story": "The strongest equity multiple of the four cap-rate deals at 1.89x, and it comes from "
           "lot rent being unusually durable. The model separates park-owned homes from "
           "tenant-owned lots because they are different businesses with different expense "
           "loads bolted together, and blending them flatters the deal.",
  "kw": ["mobile home park underwriting model", "mhp financial model excel",
         "mobile home park proforma", "mobile home park deal analyzer",
         "lot rent investment calculator"]},
 {"key": "laundromat-underwriting-model", "slug": "laundromat-underwriting-model",
  "asset": "Laundromat", "lower": "laundromat", "plural": "laundromats",
  "going_in": "3.52x EBITDA", "dscr": "2.06", "irr": "51.60%", "multiple": "4.11x",
  "exit": "EBITDA multiple", "exit_lower": "an EBITDA multiple",
  "revenue": "turns per machine per day, vend price by machine size, wash-dry-fold, and "
             "ancillary vending",
  "story": "This one is different from the other four and the difference matters. A laundromat "
           "is bought as a <em>business</em> on an EBITDA multiple, not as real estate on a cap "
           "rate — and the polarity is opposite: a higher multiple is a <em>better</em> exit, "
           "where a higher cap rate is a worse one. The seed deal shows a 51.60% levered IRR, "
           "which is the real arithmetic of an 85% SBA-levered buy on $178,000 of equity. High, "
           "and correspondingly fragile. The sensitivity grid is where you find out how fragile.",
  "kw": ["laundromat underwriting model", "laundromat financial model excel",
         "laundromat business valuation", "coin laundry deal analyzer",
         "laundromat sde multiple calculator"]},
]

ASSET_TABS = {
 "Start Here": "What to fill in, in what order, and how to import the file into Google Sheets.",
 "Assumptions": "Purchase price, closing costs, loan terms, growth rates, exit assumptions and "
                "hold period. Everything the deal hinges on, in one place.",
 "Revenue": "The revenue build — {revenue}.",
 "Operating Expenses": "Every expense line, with price-based costs like management fees and card "
                       "processing set as a percentage of effective gross income so they scale.",
 "Debt Schedule": "Real amortisation with interest-only years, built with CUMPRINC and CUMIPMT "
                  "rather than a running subtraction.",
 "Proforma": "The ten-year projection — revenue, expenses, net operating income, debt service "
             "and cash flow.",
 "Returns": "Levered and unlevered IRR, equity multiple, DSCR by year, and the exit.",
 "Sensitivity": "A 5x5 grid backed by 25 genuine ten-year cash flow runs, not an approximation.",
}


def _underwriting(a: dict) -> dict:
    asset, lower = a["asset"], a["lower"]
    tabs = {k: v.format(revenue=a["revenue"]) for k, v in ASSET_TABS.items()}
    cap_or_mult = ("exit cap rate" if a["exit"] == "Cap rate" else "exit EBITDA multiple")
    return {
    "key": a["key"],
    "slug": a["slug"],
    "group": "Property and deal analysis",
    "category": f"{asset} underwriting",
    "pill": "Model",
    "card_title": f"{asset} underwriting model",
    "card_blurb": f"Ten-year proforma for a {lower} with real amortisation, levered and unlevered "
                  f"IRR, DSCR and a 5x5 sensitivity grid.",

    "title": f"{asset} Underwriting Model — IRR, DSCR & Sensitivity"[:65],
    "description": f"Ten-year {lower} proforma with real amortisation, levered and unlevered "
                   f"IRR, DSCR by year and a 25-run sensitivity grid. Excel and Sheets.",
    "h1": f"is this {lower} actually a good deal?",
    "lead": f"You are about to spend somewhere between half a million and ten million dollars. "
            f"The seller has a spreadsheet and it says yes. This is the one you build yourself, "
            f"before you believe theirs &mdash; ten years, real debt, and a grid showing what "
            f"happens when two assumptions move at once.",
    "chips": [f"{a['dscr']} DSCR year 1", f"{a['irr']} levered IRR"],
    "keywords": a["kw"],

    "short_answer": f"""<p>Underwriting a {lower} means projecting what it will earn, subtracting
what it costs to run and what the loan costs, and then asking what return that leaves on the money
you actually put in.</p>
<p>Three numbers decide it. <strong>DSCR</strong> is whether the income covers the loan payment
&mdash; below about 1.25 and a lender says no. <strong>IRR</strong> is your annualised return over
the hold. <strong>Equity multiple</strong> is how many times your money comes back. At this
model's shipped assumptions the sample deal runs a <strong>{a['dscr']} DSCR</strong>, a
<strong>{a['irr']} levered IRR</strong> and a <strong>{a['multiple']} equity multiple</strong>.</p>""",

    "problem_h": "What underwriting actually means",
    "problem": f"""<p>Buying a {lower} is buying a stream of future money. Underwriting is working
out what that stream is worth, and whether the price is sensible.</p>
<p>In plain steps: how much will it bring in, what does it cost to run, what is left over, how
much of that goes to the bank, and what does that leave you? Then: what is it worth when you
sell?</p>
<p>The part people get wrong is not the arithmetic. It is that a single answer is worthless. Every
one of those inputs is a guess. Change occupancy by three points and the whole thing moves. So the
useful question is never &ldquo;what is the return&rdquo; &mdash; it is <em>&ldquo;across the
range of things that could plausibly happen, how often does this still work?&rdquo;</em></p>
<p>That is what the sensitivity grid is for, and it is why it is built out of 25 real ten-year
cash flow runs rather than an approximation.</p>""",

    "cost_h": "Where the sample deal lands",
    "cost_intro": f"""<p>The seed deal is underwritten <strong>conservatively</strong> &mdash;
exit assumptions set less favourably than going-in &mdash; so the returns read realistic rather
than promotional.</p>""",
    "cost_table": table(
        f"The shipped {lower} deal, at its default assumptions",
        ["Measure", "Value#", "What it tells you"],
        [["Going-in", (a["going_in"], ""), "What you are paying, relative to current income."],
         ["DSCR, year 1", (a["dscr"], "good"),
          "Income divided by loan payment. Lenders generally want 1.25 or better."],
         ["Levered IRR", (a["irr"], "good"),
          "Annualised return on the equity you put in, after debt."],
         ["Equity multiple", (a["multiple"], "good"),
          "How many times your money comes back over the hold."],
         ["Exit method", (a["exit"], ""),
          f"The deal is sold on {a['exit_lower']}."]],
    ),
    "cost_after": f"""<p>{a['story']}</p>""",

    "why_h": "Four modelling decisions that change the answer",
    "why": """<p><strong>Exit uses forward net operating income, not trailing.</strong> A buyer is
purchasing the next twelve months of income, not the last twelve. Forward NOI is the larger number,
so this produces a higher exit value than trailing would &mdash; by roughly one year of growth. The
honest way to be conservative is a worse exit assumption, not a trailing NOI.</p>
<p><strong>Reserves sit below the NOI line.</strong> Lenders capitalise NOI before reserves, so
reserves never touch valuation &mdash; but they absolutely hit cash flow and IRR. Both figures are
shown, and they differ.</p>
<p><strong>Price-based costs scale with revenue.</strong> Management fees and card processing are
percentages of effective gross income, not fixed dollars, so they move when the revenue
assumption moves.</p>
<p><strong>Debt is modelled properly.</strong> CUMPRINC and CUMIPMT with interest-only years, not
a running subtraction &mdash; so changing the rate, the amortisation period or the IO term
reprices every year at once instead of needing the schedule rebuilt.</p>""",

    "howto_name": f"How to underwrite a {lower}",
    "howto_desc": f"Five steps from asking price to a defensible view on whether the {lower} deal "
                  f"works.",
    "steps": [
     {"h": "Build the revenue from its drivers",
      "plain": f"Enter the underlying drivers of income rather than a single revenue figure, so "
               f"the model reacts when your assumptions change.",
      "body": f"""<p>The revenue build asks for {a['revenue']}. Entering one revenue number
      instead means the sensitivity grid has nothing to move, which defeats the point of building
      a model at all.</p>"""},
     {"h": "Enter the operating expenses honestly",
      "plain": "List every expense line, setting management fees and processing costs as a "
               "percentage of effective gross income so they scale with revenue.",
      "body": """<p>The expenses the seller's spreadsheet forgets are usually management, capital
      reserves and the real cost of insurance. Price-based costs are entered as percentages so
      that a revenue change carries through them properly.</p>"""},
     {"h": "Model the debt with real amortisation",
      "plain": "Enter the loan amount, rate, amortisation period and any interest-only years. "
               "Principal and interest are calculated per year, not approximated.",
      "body": """<p>Built on CUMPRINC and CUMIPMT against a closed-form balance. Change the rate
      and every one of the ten years reprices immediately, which is what makes rate sensitivity
      meaningful rather than decorative.</p>"""},
     {"h": "Set the exit, and be pessimistic about it",
      "plain": f"Set the {cap_or_mult} and selling costs. Use forward net operating income, and "
               f"set the exit less favourably than the going-in assumption.",
      "body": f"""<p>Exit is where a model most easily lies to you, because it is the furthest
      out and the least knowable. The seed deals here set the exit less favourably than going-in,
      which is why the returns look ordinary rather than exciting.</p>"""},
     {"h": "Read the grid, not the single number",
      "plain": "Move two assumptions at once across the 5x5 sensitivity grid and look at how much "
               "of it still clears your required return and DSCR.",
      "body": """<p>Twenty-five genuine ten-year IRR runs, not an interpolation. The centre cell
      reproduces the Returns tab exactly &mdash; that is asserted by the checker, so if the grid
      engine and the main model ever drift apart, it fails loudly.</p>
      <p>What you are looking for is not the best cell. It is how much of the grid you can live
      with.</p>"""},
    ],

    "inside_intro": f"""<p>Eight tabs, seeded with a complete {lower} deal so every tab is working
the moment you open it. Change the assumptions and the whole ten years reprices.</p>""",
    "tabs": tabs,
    "shot_tab": "Returns",
    "shot_alt": f"The Returns tab of the {lower} underwriting model showing levered and unlevered "
                f"IRR, equity multiple and DSCR by year",
    "shot_note": "Levered and unlevered are both shown, because the gap between them is how much "
                 "of the return is coming from the loan rather than the asset.",

    "includes": [
     "One .xlsx file, eight tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
     f"A complete {lower} deal already modelled, conservatively",
     "Real amortisation with interest-only support, via CUMPRINC and CUMIPMT",
     "Levered and unlevered IRR, equity multiple and DSCR by year",
     "A 5x5 sensitivity grid backed by 25 genuine ten-year runs",
     "Free lifetime updates",
    ],
    "fine": "The seed deal is an example, not a recommendation, and not investment advice.",

    "math_h": "The arithmetic, written out",
    "math": f"""<pre><code>effective gross income = potential revenue - vacancy and credit loss
net operating income   = effective gross income - operating expenses
                         (reserves sit BELOW this line)
cash flow after debt   = NOI - reserves - debt service
DSCR                   = NOI / debt service
exit value             = forward NOI / exit cap        # or EBITDA x exit multiple
levered IRR            = IRR(equity out, annual cash flow, net sale proceeds)</code></pre>
<p>Two notes on the exit. It uses <strong>forward</strong> NOI &mdash; year N+1 &mdash; because
that is what a buyer is purchasing. And the two exit methods have <em>opposite polarity</em>: a
higher cap rate is a worse exit, while a higher EBITDA multiple is a better one. The checker
asserts the grid moves the right way for the method in use, which caught a real bug where the
assertion had assumed cap-rate semantics for the laundromat.</p>""",

    "proof": """<p>Every deal in this family is reimplemented from scratch in Python &mdash;
including a bisection IRR and a closed-form amortisation balance &mdash; then the shipped workbook
is recalculated in LibreOffice and the two are diffed. <strong>24 checks per model, 120 across the
five. Last run: 0 mismatches, 0 formula errors.</strong></p>
<p>Two assertions go beyond matching values, because a decorative feature passes a value check:</p>
<ul>
<li><strong>The sensitivity grid's centre cell must reproduce the Returns tab's levered IRR
exactly.</strong> The grid is a separate 25-column engine; if it ever drifts from the main model,
this is what fails first.</li>
<li><strong>The grid must move in the correct direction</strong> for its exit method &mdash; and
the two methods are opposite. This check caught a genuine bug where the test assumed cap-rate
polarity on the EBITDA-multiple deal.</li>
</ul>""",

    "versus_h": "Compared with the alternatives",
    "versus_table": table(
        "What else you could do instead",
        ["", "Cost#", "Real amortisation", "Sensitivity", "Built for this asset"],
        [["This model", ("$99", "good"), ("CUMPRINC/CUMIPMT", "good"),
          ("25 real runs", "good"), ("Yes", "good")],
         ["A free proforma template", ("$0", ""), ("Often approximated", "bad"),
          ("None", "bad"), ("Generic", "bad")],
         ["The seller's spreadsheet", ("$0", ""), ("Varies", ""), ("None", "bad"),
          ("Optimistic", "bad")],
         ["An analyst builds it", "$2,000&ndash;$10,000", ("Yes", "good"), ("Yes", "good"),
          ("Yes", "good")]],
    ),

    "faq": [
     ("What is DSCR?",
      "Debt service coverage ratio — net operating income divided by the annual loan payment. It "
      "answers whether the property earns enough to pay the bank. Lenders generally want 1.25 or "
      f"better; the sample deal here runs {a['dscr']} in year one."),
     ("What is the difference between levered and unlevered IRR?",
      "Unlevered IRR is the return the asset produces on its own. Levered IRR is the return on the "
      "cash you actually put in, after borrowing. The gap between them tells you how much of your "
      "return is coming from the loan rather than the property."),
     ("Why does the model use forward NOI at exit?",
      "Because a buyer is paying for the next twelve months of income, not the last twelve. Forward "
      "NOI is the larger number, so this gives a higher exit than trailing NOI would. If you want to "
      "be conservative, do it with a worse exit assumption rather than a trailing NOI."),
     ("Why is the sensitivity grid 25 separate runs?",
      "Because Excel Data Tables do not exist in Google Sheets, and a two-way IRR has no closed "
      "form. Each cell is a genuine ten-year IRR calculation, which is also why the workbook stays "
      "portable."),
     (f"Why is the sample {lower} return not higher?",
      "Because the seed deal is deliberately underwritten conservatively, with the exit set less "
      "favourably than the going-in assumption. A model that shows a large return on its default "
      "settings is selling you optimism."),
     ("Can I change the hold period?",
      "The model runs a ten-year proforma. You can read returns at earlier exits from the "
      "proforma, and the exit assumptions are inputs."),
     ("Will it work in Google Sheets?",
      "Yes. Upload the .xlsx to Google Drive and open it with Google Sheets. It uses IRR, CUMPRINC "
      "and CUMIPMT, all of which Sheets supports."),
     ("Can I use it on a Mac without Excel?",
      "Yes. Apple Numbers has IRR, CUMPRINC and CUMIPMT, and LibreOffice Calc is free and opens "
      "the file directly."),
    ],
    "related": [(o["slug"], f"{o['asset']} underwriting model — the same engine, {o['lower']} "
                            f"assumptions")
                for o in ASSETS if o["key"] != a["key"]][:3],
    }


PRODUCTS_C = [_underwriting(a) for a in ASSETS] + [

# --------------------------------------------------------------------------- #
{
"key": "landed-cost-duty-calculator",
"slug": "landed-cost-duty-calculator",
"group": "Importing and pricing",
"category": "Import costing",
"pill": "Calculator",
"card_title": "Landed cost and import duty calculator",
"card_blurb": "Multi-currency landed cost with FOB/CIF duty basis, stacked tariffs, freight "
              "allocated across SKUs, and break-even repricing.",

"title": "Landed Cost Calculator — Import Duty & Freight, Excel",
"description": "Work out true per-unit landed cost with FOB or CIF duty basis, stacked tariffs, "
               "MPF and HMF, and freight allocated across SKUs. Excel and Google Sheets.",
"h1": "the price on the invoice is not what it costs you",
"lead": "By the time a container reaches your warehouse it has picked up freight, duty, tariffs, "
        "customs fees, insurance and an exchange rate that moved. Landed cost is what the thing "
        "<em>actually</em> cost. Price off the invoice figure instead and you can sell out an "
        "entire shipment at a loss.",
"chips": ["40 SKUs", "4 allocation bases"],
"keywords": ["landed cost calculator", "import duty calculator excel",
             "landed cost spreadsheet", "freight allocation by sku",
             "tariff calculator excel", "import cost per unit calculator"],

"short_answer": """<p>Landed cost is the unit price plus every cost of getting the goods to you:
freight, insurance, duty, tariffs, customs fees and any currency spread. You add all of that up,
spread the shipment-level costs across the individual products, and divide by units.</p>
<p>Two choices change the answer more than anything else. Whether duty is assessed on
<strong>FOB</strong> or <strong>CIF</strong> value &mdash; that alone moves the duty by $2,513, or
17%, on the sample shipment. And what basis you use to spread the freight across your products,
which moves individual SKU costs by 4% without changing the shipment total at all.</p>""",

"problem_h": "Where the extra cost comes from",
"problem": """<p>You buy 5,000 units at $3 each. That is $15,000. Simple.</p>
<p>Except: the ocean freight is billed for the whole container, not per product. The duty depends
on which country you are in and what the item is classified as. There might be an extra tariff on
top of the normal one. Customs charges a processing fee with a minimum and a maximum. There is a
harbour fee if it came by sea. You paid in dollars but your bank gave you a worse rate than the
one you looked up.</p>
<p>None of that is on the supplier's invoice. All of it is your cost.</p>
<p>And here is the part that bites: those costs are for the whole shipment, but you need to know
what each <em>product</em> cost, because you price products, not containers. So you have to split
them &mdash; and how you split them decides which of your products look profitable.</p>""",

"cost_h": "Two settings, and what each one moves",
"cost_intro": """<p>The workbook was tested under four combinations of its two most consequential
settings, because a model that is only right on its defaults is not right. Here is what each one
actually moves.</p>""",
"cost_table": table(
    "The sample shipment under four configurations",
    ["Duty basis", "Freight allocated by", "Total duty#", "Total landed#", "Landed per unit#"],
    [["FOB", "Volume (CBM)", ("$14,977", "good"), "$67,771", "$4.4007"],
     ["CIF", "Volume (CBM)", ("$17,490", "bad"), "$70,318", "$4.5661"],
     ["FOB", "Value", ("$14,977", "good"), "$67,771", "$4.4007"],
     ["FOB", "Weight", ("$14,977", "good"), "$67,771", "$4.4007"]],
    foot=["FOB vs CIF moves duty by", "", ("$2,513 (+17%)", "bad"), "", ""]),
"cost_after": """<p>Read the pattern. <strong>The duty basis changes the total</strong> &mdash;
$2,513 more duty on CIF, because CIF includes the freight and insurance in the value being taxed.
<strong>The allocation basis does not change the total at all</strong> &mdash; the last three rows
are identical to the cent.</p>
<p>But allocation changes which SKU carries what. SKU1's unit cost swings <strong>$0.176, about
4%</strong>, between allocating by value and allocating by weight. That is the correct signature
for an allocation: it redistributes cost, it never creates or destroys it.</p>
<p>Which matters because ocean freight is bought by <em>volume</em>. Allocate it by value instead
and every dense, cheap product on the container is quietly subsidised by your expensive ones.</p>""",

"why_h": "Why the duty basis is a toggle and not a setting I picked",
"why": """<p>The United States assesses duty on <strong>FOB</strong> transaction value &mdash;
international freight and insurance are not dutiable. Most other countries assess on
<strong>CIF</strong>, where they are.</p>
<p>Hardcoding either one would be wrong for roughly half the people using the workbook, so it is a
toggle, defaulting to FOB.</p>
<p>The other thing worth knowing: <strong>tariffs stack additively on customs value, never on each
other.</strong> A 9.8% base rate plus a 25% additional tariff is 34.8% of customs value &mdash; not
37.3%, which is what you get if you compound them. Each programme gets its own column so you can
see what is being applied.</p>""",

"howto_name": "How to calculate landed cost per unit",
"howto_desc": "Five steps from a supplier invoice to a defensible per-unit cost and a price.",
"steps": [
 {"h": "Enter the shipment and the exchange rate you actually got",
  "plain": "Record the supplier invoice in its original currency and the rate your bank gave you, "
           "including the spread, not the mid-market rate.",
  "body": """<p>The rate you looked up online is not the rate you got. The spread is real money and
  it belongs in the cost."""},
 {"h": "Choose the customs valuation basis",
  "plain": "Set duty to be assessed on FOB or CIF value depending on the destination country. FOB "
           "excludes international freight and insurance; CIF includes them.",
  "body": """<p>US: FOB. Most elsewhere: CIF. On the sample shipment this one toggle moves the duty
  by $2,513, so it is worth being sure which one applies to you.</p>"""},
 {"h": "Enter each duty and tariff programme separately",
  "plain": "Give the base duty rate and any additional tariff programmes their own columns. They "
           "stack additively on the customs value, never on each other.",
  "body": """<p>9.8% + 25% = 34.8% of customs value. Not 37.3%.</p>
  <p>Duty rates here are <strong>inputs, never lookups</strong>. The Duty Reference tab feeds
  nothing into the calculation, deliberately: a stale rate applied automatically is worse than a
  blank cell, because it looks authoritative.</p>"""},
 {"h": "Allocate freight and shipment costs across SKUs",
  "plain": "Choose whether to spread freight by value, weight, volume or unit count, and apply it "
           "to every SKU on the shipment.",
  "body": """<p>Match the basis to how the cost is actually incurred. Ocean freight is bought by
  volume, so allocating by volume is usually right. Allocating by value overcharges dense cheap
  SKUs and undercharges light expensive ones.</p>
  <p>Customs processing fees are computed on total customs value and then allocated by share &mdash;
  the processing fee is clamped to its per-entry minimum and maximum, and zeroed on informal
  entries. The harbour fee applies to ocean shipments only.</p>"""},
 {"h": "Reprice from the landed cost",
  "plain": "Set your target margin and channel fees, and calculate the selling price by dividing "
           "landed cost by one minus the fees and margin.",
  "body": """<pre><code>price = (landed cost + per-unit costs) / (1 - fee% - margin%)</code></pre>
  <p>Margin divides, not multiplies &mdash; the same discipline as the bid calculators. Channel
  fees go inside the bracket, which is what makes the Repricing tab work equally for a marketplace,
  a storefront or wholesale.</p>"""},
],

"inside_intro": """<p>Seven tabs across a 40-SKU sample shipment, with every toggle already
exercised so you can see what each one does before you enter your own.</p>""",
"tabs": {
 "Start Here": "What to fill in, in what order, and how to import the file into Google Sheets.",
 "Shipment": "The container: supplier invoice, currency and rate, freight, insurance, and the "
             "FOB/CIF toggle.",
 "SKUs": "Up to 40 products with unit cost, quantity, weight, volume and duty classification.",
 "Landed Cost": "The full build-up per SKU — duty, tariffs, fees and allocated freight — giving "
                "true per-unit cost.",
 "Repricing": "What you need to charge, given landed cost, channel fees and your target margin.",
 "Scenario": "Change the duty basis or the allocation method and see every SKU move at once.",
 "Duty Reference": "Illustrative rates and classifications, feeding nothing — a reference you "
                   "read, not a lookup the model trusts.",
},
"shot_tab": "Landed Cost",
"shot_alt": "The Landed Cost tab showing per-SKU duty, tariffs, allocated freight and true "
            "per-unit cost across the shipment",
"shot_note": "Every shipment-level cost is allocated down to the SKU, because you price products "
             "rather than containers.",

"includes": [
 "One .xlsx file, seven tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "A 40-SKU sample shipment already costed",
 "FOB and CIF customs valuation as a toggle, not a hardcoded assumption",
 "Stacked tariff programmes, each in its own column",
 "Four freight allocation bases — value, weight, volume, units",
 "Break-even repricing with channel fees handled correctly",
 "Free lifetime updates",
],
"fine": "Duty rates, HTS codes and fee thresholds are illustrative starting values, not current law.",

"math_h": "The arithmetic, written out",
"math": """<pre><code>customs value  = FOB value              # or FOB + freight + insurance, if CIF
duty           = customs value x (base rate + tariff 1 + tariff 2 + ...)
processing fee = MIN(MAX(customs value x rate, minimum), maximum)
harbour fee    = customs value x rate    # ocean shipments only
allocated cost = shipment cost x (SKU basis / total basis)
landed / unit  = (unit cost + duty + fees + allocated freight) / units
price          = (landed + per-unit costs) / (1 - fee% - margin%)</code></pre>
<p>Note the tariff line adds the rates together before multiplying. That is what
&ldquo;additively&rdquo; means, and it is the difference between 34.8% and 37.3%.</p>
<div class="callout callout--warn">
<div class="callout__title">On the duty rates in the file</div>
<p>The HTS codes, duty rates, exchange rates and fee thresholds shipped with this workbook are
<strong>illustrative starting values, not current law</strong>. Tariff programmes changed
repeatedly through 2025 and 2026. They are flagged as illustrative on Start Here and in red on the
Duty Reference tab. This is a costing tool, not customs advice, and classification is out of
scope &mdash; get your rates from your broker or the current tariff schedule and type them
in.</p>
</div>""",

"proof": """<p>The whole shipment is reimplemented in Python from the definitions, the workbook is
recalculated in LibreOffice, and the two are diffed &mdash; under four configurations rather than
one. <strong>17 checks &times; 4 configurations = 68, plus 2 behavioural assertions. Last run: 0
mismatches, 0 formula errors.</strong></p>
<p>The two behavioural assertions exist because a toggle that does nothing passes every value
check:</p>
<ul>
<li><strong>FOB versus CIF must actually move the duty.</strong> It does &mdash; by $2,513, or 17%,
on the sample shipment.</li>
<li><strong>The allocation basis must move per-SKU cost while leaving the shipment total
untouched.</strong> It does &mdash; SKU1's unit cost swings $0.176 between value and weight
allocation, and the shipment total is identical to the cent. That combination is the signature of
a correct allocation.</li>
</ul>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "FOB/CIF toggle", "Stacked tariffs", "Freight allocation"],
    [["This workbook", ("$79", "good"), ("Yes", "good"), ("Separate columns", "good"),
      ("Four bases", "good")],
     ["A free landed cost sheet", ("$0", ""), ("Hardcoded", "bad"), ("One rate", "bad"),
      ("By value only", "bad")],
     ["Your freight forwarder's quote", ("$0", ""), ("N/A", ""), ("N/A", ""),
      ("Not per SKU", "bad")],
     ["Supply chain software", "$200&ndash;$1,000 / month", ("Yes", "good"), ("Yes", "good"),
      ("Yes", "good")]],
),

"faq": [
 ("What is landed cost?",
  "The total cost of getting a product to your warehouse — unit price plus freight, insurance, "
  "duty, tariffs, customs fees and currency spread — divided by units. It is what the product "
  "actually cost you, as opposed to what the supplier invoiced."),
 ("What is the difference between FOB and CIF for duty?",
  "FOB assesses duty on the goods value alone. CIF assesses it on goods plus international freight "
  "and insurance, so the taxable value is larger. The United States uses FOB; most other countries "
  "use CIF. On the sample shipment the difference is $2,513 of duty, or 17 percent."),
 ("Do tariffs compound on top of each other?",
  "No. They stack additively on the customs value. A 9.8 percent base rate plus a 25 percent "
  "additional tariff is 34.8 percent of customs value, not 37.3 percent."),
 ("How should I allocate freight across products?",
  "Match the basis to how the cost is incurred. Ocean freight is bought by volume, so allocating "
  "by volume is usually right. Allocating by value silently overcharges dense cheap products."),
 ("Are the duty rates in the file current?",
  "No, and they are labelled as illustrative on Start Here and in red on the Duty Reference tab. "
  "Tariff programmes changed repeatedly through 2025 and 2026. Get your rates from your broker or "
  "the current schedule and enter them — the workbook treats rates as inputs, never lookups."),
 ("Does it handle multiple currencies?",
  "Yes, including the spread your bank actually charged rather than the mid-market rate."),
 ("Will it work in Google Sheets?",
  "Yes. Upload the .xlsx to Google Drive and open it with Google Sheets. No macros, no add-ins."),
 ("Can I use it on a Mac without Excel?",
  "Yes. Apple Numbers opens the file directly, and LibreOffice Calc is free."),
],
"related": [
 ("recipe-costing-menu-engineering", "Recipe costing — the same idea applied to what goes on a plate"),
 ("construction-cash-flow-forecast", "Cash flow forecast — when the money for a shipment leaves"),
],
},

# --------------------------------------------------------------------------- #
{
"key": "spc-control-chart-capability-workbook",
"slug": "spc-control-chart-cpk-workbook",
"group": "Manufacturing and quality",
"category": "Statistical process control",
"pill": "Workbook",
"card_title": "SPC control charts and process capability",
"card_blurb": "Xbar-R, I-MR and p-charts with Western Electric rules, Cp/Cpk/Pp/Ppk, and a full "
              "AIAG Gage R&R study.",

"title": "SPC Control Chart & Cpk Workbook for Excel — No Add-In",
"description": "Xbar-R, I-MR and p-charts with Western Electric rules, Cp/Cpk/Pp/Ppk with PPM, "
               "and an AIAG Gage R&R study. Excel and Google Sheets, no add-in.",
"h1": "control limits do not come from your tolerance",
"lead": "This is the most common mistake in statistical process control, and it hides problems "
        "rather than finding them. Control limits describe what your process <em>is</em> doing. "
        "Specification limits describe what you <em>want</em> it to do. Draw the first from the "
        "second and the chart can never tell you anything you did not already assume.",
"chips": ["Gage R&R included", "No add-in"],
"keywords": ["spc control chart excel", "cpk calculator excel", "process capability template",
             "gage r&r spreadsheet", "xbar r chart template",
             "western electric rules excel"],

"short_answer": """<p>A control chart plots your measurements over time with limits at plus and
minus three standard deviations of <em>the process itself</em>. Points outside those limits, or
patterns inside them, mean something has changed.</p>
<p>Those limits must be calculated from your data, never from your tolerance. And before you trust
any of it, you have to know your measurement system is not the thing producing the variation
&mdash; which is what a Gage R&amp;R study is for, and why it comes first.</p>""",

"problem_h": "Two limits that sound the same and are not",
"problem": """<p>Imagine you are cutting parts that need to be 10mm, and the customer will accept
anything between 9.5mm and 10.5mm. Those two numbers are your <strong>specification
limits</strong>. They are a requirement.</p>
<p>Now measure what your machine actually produces. Perhaps it runs at 10.02mm with a spread of
about 0.02mm either side. That spread is your <strong>control limits</strong>. They are an
observation.</p>
<p>Here is why confusing them is dangerous. Your tolerance is wide &mdash; a full millimetre. Your
process is tight. If you draw the chart lines at 9.5 and 10.5, the machine could drift from 10.02
to 10.3, which is a completely different machine behaving in a completely different way, and
<strong>your chart would show nothing at all</strong>, because 10.3 is still inside the tolerance.</p>
<p>You would find out when the drift finally crossed the spec line &mdash; by which point you have
been making parts that are getting worse for weeks, and you have no idea when it started.</p>
<p>The whole value of a control chart is that it catches change <em>before</em> it becomes a
defect. Drawing the limits from the tolerance throws that away and leaves you with a very
expensive go/no-go gauge.</p>""",

"cost_h": "The other separation people collapse",
"cost_intro": """<p>There are two standard deviations in capability analysis, they are different
numbers, and the gap between them is information rather than noise. Cp and Cpk use
<strong>within-subgroup</strong> sigma; Pp and Ppk use <strong>overall</strong> sigma.</p>""",
"cost_table": table(
    "The shipped sample data, both ways",
    ["Statistic", "Value#", "Which sigma", "What it tells you"],
    [["Sigma within (R&#772;/d&#8322;)", ("0.005458", ""), "Within subgroups",
      "How tightly the machine holds over a short run."],
     ["Sigma overall", ("0.006644", ""), "All the data",
      "How tightly it holds across the whole period, drift included."],
     ["Cp / Cpk", ("1.832 / 1.695", "good"), "Within",
      "Capability — what the process could do if it stayed put."],
     ["Pp / Ppk", ("1.505 / 1.393", ""), "Overall",
      "Performance — what it actually did."]],
    foot=["Cpk &minus; Ppk gap", ("0.303", "bad"), "", "The drift, expressed as a number"]),
"cost_after": """<p>That 0.303 gap <em>is</em> the instability. A workbook that computes one sigma
and uses it for all four statistics makes Cp equal Pp and the gap disappear &mdash; which does not
mean the process is stable, only that you can no longer see that it is not.</p>""",

"why_h": "Why Gage R&R has to come first",
"why": """<p>Before any of this means anything, you need to know that the variation you are
charting is coming from the <em>process</em> and not from the <em>measuring</em>.</p>
<p>If two operators measure the same part and get different answers, or the same operator gets a
different answer twice, then some of the spread on your chart is your gauge, not your machine. A
Gage R&amp;R study separates the two.</p>
<p>This workbook uses the AIAG average-and-range method with the published K1, K2 and K3 constants
&mdash; which is why it is fixed at 10 parts, 3 operators and 3 trials. On the shipped data %GRR
comes out at <strong>12.32%</strong> with <strong>11 distinct categories</strong>, which is an
acceptable measurement system. The study is deliberately seeded with real operator bias so you can
see the method detect something.</p>""",

"howto_name": "How to run an SPC study that means something",
"howto_desc": "Five steps from a measurement system study to a defensible capability number.",
"steps": [
 {"h": "Prove the gauge before you trust the data",
  "plain": "Run a Gage R&R study with 10 parts, 3 operators and 3 trials, and check that "
           "measurement variation is a small share of total variation.",
  "body": """<p>Ten parts, three operators, three trials each. Look at %GRR and the number of
  distinct categories. If the gauge is a large share of your variation, everything downstream is
  measuring your measuring.</p>"""},
 {"h": "Pick the right chart for your data",
  "plain": "Use Xbar-R for measurements taken in subgroups, I-MR for individual measurements, and "
           "a p-chart for pass/fail proportions.",
  "body": """<p>Subgroups of parts measured together: Xbar-R. One measurement at a time: I-MR.
  Counting defectives out of a batch: p-chart. All three are in the workbook and all three carry
  their own rules.</p>"""},
 {"h": "Calculate the limits from your data, never your tolerance",
  "plain": "Compute control limits from the observed process variation using the standard "
           "constants. Do not derive them from specification limits.",
  "body": """<p>Nothing in this workbook can compute a control limit from a spec limit &mdash;
  there is no path from one to the other, on purpose.</p>
  <p>The constants are a <strong>visible lookup table</strong> rather than magic numbers. d&#8322;
  is the expected range of n standard normal deviates; A&#8322; = 3/(d&#8322;&radic;n);
  D&#8323; = 0 below n=7, which is why small-subgroup R charts have no lower limit.</p>"""},
 {"h": "Apply the rules, each in its own column",
  "plain": "Test each of the Western Electric rules separately so you can see which pattern fired, "
           "not just that something did.",
  "body": """<p>Five rules, five columns. <em>Which</em> rule fired tells you what kind of cause to
  go looking for &mdash; a single point beyond three sigma is a different investigation from nine
  points on one side of the centre line. A combined flag throws that away.</p>"""},
 {"h": "Only then calculate capability",
  "plain": "Confirm the process is in control, then compute Cp and Cpk from within-subgroup sigma "
           "and Pp and Ppk from overall sigma.",
  "body": """<p>Capability on an out-of-control process is a meaningless number, because there is
  no single process to be capable. The Capability tab checks stability first and says so.</p>
  <p>Keep the two sigmas separate. The gap between the pairs is the drift, and it is the most
  useful thing on the tab.</p>"""},
],

"inside_intro": """<p>Eight tabs. The sample data is deliberately imperfect: the Xbar-R run shifts
over its last eight subgroups, the I-MR series has a special-cause spike, one p-chart lot is out of
control, and the Gage R&amp;R has genuine operator bias. A clean demo would teach you nothing about
whether the rules work.</p>""",
"tabs": {
 "Start Here": "What to fill in, in what order, and how to import the file into Google Sheets.",
 "Constants": "d2, A2, D3, D4 and the Gage R&R K factors, as a visible table rather than magic "
              "numbers.",
 "Xbar-R": "Subgroup averages and ranges, with control limits and five Western Electric rules, "
           "each in its own column.",
 "I-MR": "Individuals and moving range, for when you measure one at a time.",
 "p-Chart": "Proportion defective, with limits that change as lot size changes.",
 "Capability": "Cp, Cpk, Pp, Ppk and PPM — with a stability check first, because capability on an "
               "unstable process is meaningless.",
 "Gage R&R": "The full AIAG average-and-range study: 10 parts, 3 operators, 3 trials, %GRR and "
             "distinct categories.",
 "How It Works": "Every statistic, defined and derived.",
},
"shot_tab": "Capability",
"shot_alt": "The Capability tab showing Cp, Cpk, Pp and Ppk calculated from separate within and "
            "overall sigma, with PPM",
"shot_note": "Cp and Cpk sit above Pp and Ppk here, which is what a drifting process looks like.",

"includes": [
 "One .xlsx file, eight tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "Three chart types with five Western Electric rules, each rule in its own column",
 "Cp, Cpk, Pp and Ppk from properly separated sigmas, plus PPM",
 "A complete AIAG average-and-range Gage R&R study",
 "Deliberately imperfect sample data, so you can watch the rules fire",
 "Free lifetime updates",
],
"fine": "No add-in and no macros — which is what makes it work in Google Sheets and Numbers too.",

"math_h": "The arithmetic, written out",
"math": """<pre><code>sigma within  = R-bar / d2                  # from subgroup ranges
sigma overall = STDEV(all measurements)

Cp  = (USL - LSL) / (6 x sigma within)
Cpk = MIN(USL - mean, mean - LSL) / (3 x sigma within)
Pp  = (USL - LSL) / (6 x sigma overall)
Ppk = MIN(USL - mean, mean - LSL) / (3 x sigma overall)

Xbar chart limits = X-double-bar +/- A2 x R-bar
R chart limits    = D3 x R-bar, D4 x R-bar</code></pre>
<p>Cp and Pp measure spread against tolerance. Cpk and Ppk add centring &mdash; they use the
<em>nearer</em> specification limit, so a process can have excellent Cp and poor Cpk simply by
sitting off target.</p>
<p>And note what is <em>not</em> in these formulas: no specification limit appears anywhere in a
control limit. USL and LSL only ever show up in capability.</p>""",

"proof": """<p>Thirty numeric checks and seven property assertions. Every statistic is
reimplemented in Python from its definition, the workbook is recalculated in LibreOffice, and the
two are diffed to 1e-9. <strong>Last run: 0 mismatches, 0 property failures, 0 formula
errors.</strong></p>
<p>Value matching is not sufficient here, so it also asserts things that must be true of correct
SPC:</p>
<ul>
<li>Sigma within must be <em>less</em> than sigma overall on drifting data, and the two must not be
identical &mdash; which catches the conflation this page is about</li>
<li>Cp &gt; Pp and Cpk &gt; Ppk must hold when the process drifts</li>
<li><strong>Every chart's rules must actually fire.</strong> A rule that never triggers is
indistinguishable from a broken one</li>
</ul>
<p>That last assertion earned its place. The Xbar-R status column is column T, but two KPI
counters, the Capability tab's stability check <em>and</em> the verifier were all reading column S
&mdash; which never contains a signal. The chart silently reported zero out-of-control points on
data with <strong>twelve genuine violations</strong>, and the Capability tab would have declared an
unstable process stable. The checker now asserts the signal count is greater than zero.</p>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "Separate sigmas", "Gage R&R", "Rules itemised"],
    [["This workbook", ("$79", "good"), ("Yes", "good"), ("Full AIAG study", "good"),
      ("Five columns", "good")],
     ["A free SPC template", ("$0", ""), ("Usually one sigma", "bad"), ("No", "bad"),
      ("One flag", "bad")],
     ["Minitab", "~$2,000 / year", ("Yes", "good"), ("Yes", "good"), ("Yes", "good")],
     ["Your customer's supplied form", ("$0", ""), ("Varies", ""), ("No", "bad"),
      ("No", "bad")]],
),

"faq": [
 ("Why can't control limits come from specification limits?",
  "Because they answer different questions. Control limits describe what your process is doing; "
  "specification limits describe what you want. If your tolerance is wider than your process, "
  "limits drawn from the tolerance will not react to a real drift until it has already become a "
  "defect — which is exactly the warning a control chart exists to give."),
 ("What is the difference between Cpk and Ppk?",
  "Cpk uses within-subgroup sigma and describes what the process could do if it held still. Ppk "
  "uses overall sigma and describes what it actually did. The gap between them is the drift. On "
  "the sample data that gap is 0.303."),
 ("What is Gage R&R?",
  "A study that works out how much of the variation you are seeing comes from your measurement "
  "system rather than your process. Ten parts, three operators, three trials. If the gauge is a "
  "large share of the total, your control chart is partly charting your gauge."),
 ("Does it need an add-in?",
  "No. Everything is native spreadsheet formulas, which is why it works identically in Excel, "
  "Google Sheets, Numbers and LibreOffice."),
 ("Why is Gage R&R fixed at 10 parts, 3 operators and 3 trials?",
  "Because it uses the AIAG average-and-range method with the published K1, K2 and K3 constants, "
  "and those constants are defined for that study size."),
 ("Why are the Western Electric rules in separate columns?",
  "Because which rule fired tells you what kind of cause to look for. A point beyond three sigma "
  "is a different investigation from nine points on one side of the centre line."),
 ("Is the sample data clean?",
  "Deliberately not. The Xbar-R run shifts over its last eight subgroups, the I-MR series has a "
  "spike, one p-chart lot is out of control, and the Gage R&R has real operator bias. You need to "
  "see the rules fire to trust them."),
 ("Will it work in Google Sheets?",
  "Yes. It uses STDEV and NORMSDIST, both of which Sheets and Numbers support."),
],
"related": [
 ("design-of-experiments-excel", "Design of experiments — finding which factors actually matter"),
 ("monte-carlo-simulation-excel", "Monte Carlo simulation — modelling variation forwards"),
],
},

# --------------------------------------------------------------------------- #
{
"key": "design-of-experiments-workbook",
"slug": "design-of-experiments-excel",
"group": "Manufacturing and quality",
"category": "Experimental design",
"pill": "Workbook",
"card_title": "Design of experiments",
"card_blurb": "A full 2^4 factorial with effects, ANOVA, a normal plot, Lenth's method and a "
              "curvature test from centre points.",

"title": "Design of Experiments Workbook — 2^4 Factorial in Excel",
"description": "A full 2^4 factorial with effects, sums of squares, normal plot, Lenth's PSE, "
               "ANOVA and a curvature test. Excel and Google Sheets, no add-in.",
"h1": "changing one thing at a time is the slow way to be wrong",
"lead": "If four things might affect your process, testing them one at a time takes longer, tells "
        "you less, and cannot see interactions at all &mdash; which is a problem, because "
        "interactions are usually where the answer is. Sixteen well-chosen runs beat sixty-four "
        "careless ones.",
"chips": ["16 runs + 4 centre points", "Lenth's method"],
"keywords": ["design of experiments excel", "2^4 factorial template",
             "doe spreadsheet", "factorial design excel", "lenth's method",
             "anova excel template"],

"short_answer": """<p>A factorial design tests every combination of your factors at once instead
of one at a time. Four factors at two levels each is 16 runs, and from those you can measure all
four main effects <em>and</em> all eleven interactions.</p>
<p>The one-at-a-time approach cannot do that at any sample size. If temperature only matters when
pressure is high, changing temperature at low pressure tells you temperature does not matter
&mdash; and you would be wrong, permanently.</p>""",

"problem_h": "Why one factor at a time cannot work",
"problem": """<p>Suppose you are baking something and you want to know what makes it come out
right. You suspect four things matter: temperature, time, how much yeast, and how long it rests.</p>
<p>The natural approach is to change one and hold the rest still. Temperature up, everything else
fixed &mdash; better or worse? Then time. Then yeast. Then rest.</p>
<p>Two problems. First, you are spending all your runs learning about one factor at a time, so you
need a lot of them.</p>
<p>Second, and much worse: <strong>you can only ever see each factor at whatever settings the
others happened to be on.</strong> If more yeast only helps when the dough rests longer, and you
tested yeast at a short rest, your experiment says yeast does not matter. That conclusion is wrong,
it is confident, and nothing in your data will tell you so.</p>
<p>A factorial design tests every combination. Every factor is measured across the full range of
every other factor, so an interaction shows up as an interaction instead of hiding as noise.</p>""",

"cost_h": "Does it actually recover the truth?",
"cost_intro": """<p>This is testable in a way most spreadsheets never are. The sample data is
generated from a <strong>known model</strong>, so you can check whether the arithmetic recovers the
effects that were deliberately put in.</p>""",
"cost_table": table(
    "True effect versus what the workbook recovers",
    ["Term", "True effect#", "Recovered#", "Detected by Lenth's method"],
    [["A", ("21.6", ""), ("21.88", "good"), ("Yes", "good")],
     ["C", ("9.8", ""), ("9.28", "good"), ("Yes", "good")],
     ["D", ("14.6", ""), ("15.07", "good"), ("Yes", "good")],
     ["AC", ("&minus;18.8", ""), ("&minus;17.68", "good"), ("Yes", "good")],
     ["AD", ("16.6", ""), ("16.72", "good"), ("Yes", "good")],
     ["B", ("0.8", ""), ("0.05", "good"), ("No — correctly", "good")]],
    foot=["Lenth's method flags", "5 real", "5 of 5", "and 0 of the 10 inert terms"]),
"cost_after": """<p>Note the last row. Factor B genuinely does nothing, the workbook recovers it as
approximately nothing, and Lenth's method correctly declines to flag it. A method that finds
everything is as useless as one that finds nothing &mdash; <strong>five out of five real effects
and zero out of ten false positives</strong> is what a working method looks like.</p>
<p>Note also that two of the five real effects are <em>interactions</em> (AC and AD), and AC is
negative. One-factor-at-a-time cannot find either.</p>""",

"why_h": "Lenth's method, and why unreplicated designs need it",
"why": """<p>An unreplicated 2&#8308; has 16 runs and 15 effects to estimate. That uses up every
degree of freedom, so there is nothing left over to estimate the noise with &mdash; which means no
standard significance test works.</p>
<p>Lenth's method solves it by assuming most effects are inert, and using the size of the small
effects to estimate the noise. It runs in two passes so that large real effects cannot inflate the
noise estimate and hide themselves:</p>
<pre><code>s0  = 1.5 x median|effect|
PSE = 1.5 x median{ |effect| : |effect| &lt; 2.5 x s0 }</code></pre>
<p>It is the correct tool for this design and it is almost completely absent from spreadsheet
templates, which is a large part of why this workbook exists. Both the margin of error and the
simultaneous margin of error are reported &mdash; 1.446 and 2.935 on the shipped data.</p>
<p>The four <strong>centre points</strong> do a second job: they test for <em>curvature</em>. If
the middle of your design space sits off the plane the corners define, a straight-line model is the
wrong shape and you need a response surface design instead. On the shipped data curvature is not
significant (F = 0.013), which is correct, because the data was generated from a linear-plus-
interaction model.</p>""",

"howto_name": "How to run a 2^4 factorial experiment",
"howto_desc": "Five steps from four suspected factors to a prediction model you can trust.",
"steps": [
 {"h": "Choose four factors and two levels each",
  "plain": "Pick the four things you think matter and a low and high setting for each, far enough "
           "apart to produce a real difference.",
  "body": """<p>Set the levels wide enough that a real effect will show, but inside the range you
  would actually run. Too narrow and everything looks inert; too wide and you learn about a process
  you never operate.</p>"""},
 {"h": "Run all sixteen combinations in random order",
  "plain": "Run every combination of the four factors. Randomise the run order rather than working "
           "through the standard order.",
  "body": """<p>This matters more than it sounds. In standard order the last factor changes exactly
  once, halfway through &mdash; so anything that drifts over the session (a warming machine, a
  tiring operator, a settling batch) maps directly onto that factor and looks exactly like a real
  effect.</p>
  <p>There is a run-order column, and Start Here is emphatic about it.</p>"""},
 {"h": "Add four centre points",
  "plain": "Run four more trials with every factor at its midpoint, to estimate pure error and "
           "test whether the response is curved.",
  "body": """<p>Two jobs. They give you pure error, which the ANOVA needs. And they test curvature:
  if the middle sits off the plane the corners define, the model is the wrong shape.</p>"""},
 {"h": "Compute the effects, and keep effect and coefficient apart",
  "plain": "Calculate the effect and the coefficient for all fifteen terms as separate columns. "
           "The effect is twice the coefficient.",
  "body": """<p><code>effect = 2 x coefficient</code>. Conflating them puts every prediction out by
  a factor of two, and it is silent when it happens &mdash; the model still looks reasonable, it is
  just wrong. Both are labelled columns here.</p>"""},
 {"h": "Separate signal from noise, then build the model",
  "plain": "Use the normal probability plot and Lenth's method to identify the real effects, pool "
           "the rest into the error term, and build a prediction model from what survives.",
  "body": """<p>Real effects fall off the line on a normal plot; inert ones sit on it. Lenth's
  method gives you the same answer numerically.</p>
  <p>The error term is <strong>built openly</strong>: pooled higher-order terms plus pure error
  from the centre points, with each component shown in the ANOVA table so it can be audited rather
  than taken on trust. There is a per-term pooling switch, so you decide what goes into error.</p>"""},
],

"inside_intro": """<p>Seven tabs. The response data is generated from a known model, which is what
makes the recovery table above possible &mdash; you can verify the workbook finds the right answer
because the right answer is known.</p>""",
"tabs": {
 "Start Here": "What to fill in, in what order, why run order matters, and how to import into "
               "Google Sheets.",
 "Design": "The 16-run design matrix in standard order, plus a run-order column and four centre "
           "points.",
 "Effects": "Contrast, effect, coefficient, sum of squares and percent of variation for all 15 "
            "terms, with a per-term pooling switch.",
 "ANOVA": "The analysis of variance, with the error term built openly from pooled terms and pure "
          "error.",
 "Normal Plot": "The normal probability plot of effects, plus Lenth's PSE with both margins of "
                "error.",
 "Model": "The fitted prediction equation from whichever terms you kept.",
 "How It Works": "Every calculation, including the two-pass Lenth procedure.",
},
"shot_tab": "Effects",
"shot_alt": "The Effects tab showing contrast, effect, coefficient, sum of squares and percent of "
            "variation for all fifteen terms",
"shot_note": "Effect and coefficient are separate columns because conflating them halves every "
             "prediction.",

"includes": [
 "One .xlsx file, seven tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "A complete 2^4 design with 16 runs and 4 centre points",
 "All 15 effects with a per-term pooling switch",
 "Lenth's PSE — the correct test for an unreplicated design, and rare in templates",
 "A curvature test that tells you when a linear model is the wrong shape",
 "Free lifetime updates",
],
"fine": "No add-in and no macros. The Analysis ToolPak is not required.",

"math_h": "The arithmetic, written out",
"math": """<pre><code>contrast    = sum of (sign x response) across all 16 runs
effect      = contrast / 8            # for a 2^4
coefficient = effect / 2
SS          = contrast^2 / 16

s0          = 1.5 x median|effect|
PSE         = 1.5 x median{ |effect| : |effect| &lt; 2.5 x s0 }
ME          = t(0.975, d) x PSE
SME         = t(gamma, d) x PSE

curvature F = (mean of corners - mean of centre points)^2 scaled / pure error</code></pre>
<p>The two-pass structure in Lenth's method is the point of it. The first pass gets a rough scale
from all the effects; the second recomputes it using only effects small enough to plausibly be
noise. Without that second pass, a few large real effects inflate the noise estimate enough to
hide themselves.</p>""",

"proof": """<p>The checker does two different things, because a workbook can be perfectly
self-consistent and still wrong. It reimplements every calculation independently in Python and
diffs. And because the response data is generated from a known model, it also checks that the
arithmetic <em>recovers that model</em>.</p>
<p><strong>Last run: 0 numeric mismatches, 0 property failures, 0 formula errors.</strong></p>
<ul>
<li>effect = 2 &times; coefficient, for all 15 terms</li>
<li>The 15 sums of squares add <em>exactly</em> to the factorial total (16 runs = 1 df mean + 15 df
effects)</li>
<li>The design is <strong>orthogonal</strong> &mdash; all 105 column pairs have zero dot
product</li>
<li>Lenth's method flags all 5 real effects and zero of the 10 inert ones (ME 1.446, SME 2.935)</li>
<li>Curvature is <em>not</em> significant (F = 0.013) on data generated from a linear-plus-
interaction model &mdash; a curvature test that fires on linear data is broken</li>
</ul>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "Interactions", "Lenth's method", "Curvature test"],
    [["This workbook", ("$69", "good"), ("All 11", "good"), ("Yes", "good"), ("Yes", "good")],
     ["One factor at a time", ("$0", ""), ("None — cannot see them", "bad"), ("N/A", "bad"),
      ("No", "bad")],
     ["Minitab / JMP", "$2,000+ / year", ("Yes", "good"), ("Yes", "good"), ("Yes", "good")],
     ["A free DOE template", ("$0", ""), ("Sometimes", ""), ("Almost never", "bad"),
      ("Rarely", "bad")]],
),

"faq": [
 ("What is a 2^4 factorial design?",
  "An experiment testing four factors at two levels each — every combination, so 16 runs. From "
  "those you get all four main effects and all eleven interactions."),
 ("Why not change one factor at a time?",
  "Because it needs more runs and it cannot detect interactions at all. If factor A only matters "
  "when factor B is high, testing A at low B tells you A does not matter — a confident, wrong "
  "answer your data will never contradict."),
 ("What is Lenth's method for?",
  "An unreplicated 16-run design spends every degree of freedom estimating its 15 effects, leaving "
  "nothing to estimate noise with. Lenth's method estimates the noise from the size of the small "
  "effects instead, in two passes so that large real effects cannot hide themselves."),
 ("What are the centre points for?",
  "Two things: they give you pure error for the ANOVA, and they test for curvature. If the middle "
  "of the design space sits off the plane the corners define, a linear model is the wrong shape."),
 ("Why does run order matter so much?",
  "In standard order the last factor changes exactly once, halfway through. Anything drifting over "
  "the session maps straight onto that factor and looks like a real effect. Randomise, and use the "
  "run-order column."),
 ("Does it need the Analysis ToolPak?",
  "No. Everything is native formulas, which is why it works in Google Sheets and Numbers as well."),
 ("How do I know the maths is right?",
  "The sample response data is generated from a known model, so the workbook's answers can be "
  "checked against the truth. It recovers all five real effects and correctly finds nothing in the "
  "inert factor."),
 ("Will it work in Google Sheets?",
  "Yes. It uses FDIST, TINV and NORMSINV, all of which Google Sheets and Apple Numbers support."),
],
"related": [
 ("spc-control-chart-cpk-workbook", "SPC and process capability — watching the process you just improved"),
 ("monte-carlo-simulation-excel", "Monte Carlo simulation — propagating variation forwards"),
],
},

# --------------------------------------------------------------------------- #
{
"key": "monte-carlo-simulation-workbook",
"slug": "monte-carlo-simulation-excel",
"group": "Manufacturing and quality",
"category": "Risk analysis",
"pill": "Simulator",
"card_title": "Monte Carlo simulation",
"card_blurb": "A working simulation engine in native formulas — 12 variables, 1,000 trials, five "
              "distributions and correlated inputs. No add-in.",

"title": "Monte Carlo Simulation in Excel — No Add-In Required",
"description": "A working Monte Carlo engine in native spreadsheet formulas: 12 variables, 1,000 "
               "trials, five distributions, correlated inputs, percentiles and sensitivity.",
"h1": "one number is the least useful answer to a question about risk",
"lead": "A single-figure estimate is a guess wearing a suit. A simulation runs the whole thing a "
        "thousand times with every uncertain input varying the way it really varies, and gives you "
        "the shape of what could happen &mdash; including the tail, which is the part that "
        "actually hurts.",
"chips": ["1,000 trials", "Correlated inputs"],
"keywords": ["monte carlo simulation excel", "monte carlo spreadsheet no add-in",
             "risk analysis excel template", "monte carlo cost estimate",
             "probabilistic estimate spreadsheet", "correlated random variables excel"],

"short_answer": """<p>Monte Carlo simulation means running a calculation many times, each time
drawing every uncertain input at random from a range you specify, and collecting all the answers.
Instead of one number you get a distribution &mdash; and from that you can say things like
&ldquo;there is an 80% chance this comes in under budget&rdquo;.</p>
<p>This workbook does it in ordinary spreadsheet formulas: 12 variables, 1,000 trials, five
distributions, and correlation between inputs. No add-in, which is why it also works in Google
Sheets and Numbers.</p>""",

"problem_h": "Why the single number is always optimistic",
"problem": """<p>You are estimating a project. Twelve cost items. For each one you write down your
best guess, you add them up, and you get a total.</p>
<p>The trouble is that each of those guesses is a range, not a number, and the ranges are not
symmetric. Things can go a bit better than expected. They can go <em>enormously</em> worse. Adding
up twelve best guesses gives you a total that is roughly the middle, which sounds fine until you
notice you have no idea how far the far end is.</p>
<p>And there is a second problem that is easy to miss. Those twelve items are not independent. If
steel gets expensive, several of them get expensive together. If the schedule slips, several costs
rise at once.</p>
<p>Adding up independent best guesses lets the highs and lows cancel each other out, which makes
the total look far more predictable than it is. <strong>Correlated inputs do not cancel</strong>
&mdash; they pile up.</p>""",

"cost_h": "How much correlation actually matters",
"cost_intro": """<p>This is the workbook's central claim, so it is asserted by the checker rather
than assumed. If you sum inputs that move together, the spread of the total is wider than the
independent sum would predict.</p>""",
"cost_table": table(
    "Observed spread of the total against the independent-sum prediction",
    ["", "What it assumes", "Spread of the total"],
    [["Independent sum", "Every input varies on its own",
      "sqrt(sum of the individual variances)"],
     ["This simulation, correlated", "Inputs move together, as they really do",
      ("1.59 to 1.64 times wider", "bad")]],
    foot=["Understated by", "if you ignore correlation", ("about 60%", "bad")]),
"cost_after": """<p>Roughly 60% more spread than an independent model predicts. That gap sits
entirely in the tail &mdash; which is the region you built the model to understand. An estimate
that ignores correlation is not slightly optimistic; it is confidently wrong about exactly the
scenario you are trying to protect against.</p>""",

"why_h": "How it works without an add-in",
"why": """<p>The whole thing rests on <strong>inverse-transform sampling</strong>. Every
distribution has an inverse cumulative function; feed it a uniform random number between 0 and 1
and out comes a draw from that distribution. One formula per draw, and
<code>RAND()</code> supplies the uniform number. That is why no add-in is needed.</p>
<p>Correlation uses a <strong>single-factor Gaussian copula</strong>, which is a fancy name for a
simple trick:</p>
<pre><code>Z_i = rho x Z + sqrt(1 - rho^2) x NORMSINV(RAND())
U_i = NORMSDIST(Z_i)</code></pre>
<p>Every variable shares a common factor Z, and takes its own independent part alongside it. Z_i is
standard normal by construction, so U_i stays uniform &mdash; which means <em>every marginal
distribution is preserved exactly</em> and only the joint behaviour changes. Set rho to zero and
you get independent sampling back.</p>
<p>The percentiles come from <code>PERCENTILE()</code> over the real trials, never from a normal
approximation. The sum of skewed, correlated inputs is itself skewed, and fitting a normal curve to
it would understate precisely the tail you care about.</p>""",

"howto_name": "How to run a Monte Carlo simulation in a spreadsheet",
"howto_desc": "Five steps from twelve uncertain inputs to a probability you can act on.",
"steps": [
 {"h": "Describe each input as a range, not a number",
  "plain": "For every uncertain variable, choose a distribution and its parameters instead of a "
           "single best guess.",
  "body": """<p>Five distributions are available. <strong>Triangular</strong> when you know the
  minimum, most likely and maximum &mdash; the usual choice for cost and duration estimates.
  <strong>Uniform</strong> when anything in a range is equally likely. <strong>Normal</strong> for
  measurement-like variation. <strong>Lognormal</strong> when something cannot go below zero and
  has a long upper tail. <strong>Fixed</strong> for things that genuinely do not vary.</p>"""},
 {"h": "Set the correlation",
  "plain": "Give each variable a correlation to the shared factor, so that inputs which move "
           "together in reality move together in the model.",
  "body": """<p>Zero means independent. Higher values tie the variable more tightly to the common
  factor. This is the step most spreadsheet simulations skip, and it is worth about 60% of the
  spread of your total.</p>"""},
 {"h": "Run the trials",
  "plain": "The workbook draws 1,000 independent scenarios, each one a complete set of inputs and "
           "the resulting total.",
  "body": """<p>Every draw is a real cell you can inspect. Nothing is hidden inside an add-in, so
  if you want to know where a number came from you can follow it.</p>
  <p><code>RAND()</code> is volatile, so pressing F9 reruns the entire simulation. That is a
  feature: run it several times and see whether your conclusion is stable.</p>"""},
 {"h": "Read the percentiles, not the mean",
  "plain": "Use the percentile table and the S-curve to answer questions about probability, rather "
           "than reading the average.",
  "body": """<p>The mean is the least interesting output. What you want is P80: the figure you have
  an 80% chance of coming in under. That is what you budget to.</p>
  <p>The standard error of the mean is shown too, so you can judge whether 1,000 trials was enough
  rather than assuming it.</p>"""},
 {"h": "Find out which input is driving the spread",
  "plain": "Use the sensitivity ranking to see which variables contribute most of the variation in "
           "the total, then go and reduce the uncertainty in those.",
  "body": """<p>Usually two or three inputs dominate. Those are where more research actually pays;
  tightening your estimate of a variable that contributes 2% of the variance is wasted effort.</p>
  <p>To freeze a run for comparison, paste values into the Compare tab &mdash; otherwise the next
  recalculation replaces it.</p>"""},
],

"inside_intro": """<p>Eight tabs. Every random draw is a visible cell, which is unusual: most
simulation tools are a black box with a button.</p>""",
"tabs": {
 "Start Here": "What to fill in, how to freeze a run, and how to import into Google Sheets.",
 "Variables": "Your 12 inputs, each with a distribution, its parameters and a correlation.",
 "Trials": "1,000 rows of actual draws. Every random number is a cell you can inspect.",
 "Results": "Mean, standard deviation, percentiles, the S-curve, and the probability of coming in "
            "under a threshold you set.",
 "Sensitivity": "Which inputs contribute most of the variation in the total.",
 "Compare": "Paste a frozen run here to compare scenarios side by side.",
 "Presets": "Ready-made setups for common estimating situations.",
 "How It Works": "The sampling method, the copula, and why percentiles come from the real trials.",
},
"shot_tab": "Results",
"shot_alt": "The Results tab showing mean, standard deviation, percentiles, an S-curve and the "
            "probability of coming in under a threshold",
"shot_note": "Percentiles come from PERCENTILE() over the real trials, never from a fitted normal "
             "curve.",

"includes": [
 "One .xlsx file, eight tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "12 variables, 1,000 trials, five distributions",
 "Correlated inputs via a single-factor Gaussian copula",
 "Every draw visible as a real cell — no black box",
 "Sensitivity ranking, S-curve and a Compare tab for frozen runs",
 "Free lifetime updates",
],
"fine": "RAND() is volatile, so F9 reruns the simulation. Start Here explains how to freeze a run.",

"math_h": "The arithmetic, written out",
"math": """<pre><code>draw            = INVERSE_CDF(distribution, U)      # inverse-transform sampling
U               = RAND(), clamped to [1e-6, 1 - 1e-6]

Z_i             = rho x Z + SQRT(1 - rho^2) x NORMSINV(RAND())
U_i             = NORMSDIST(Z_i)                    # single-factor Gaussian copula

P80             = PERCENTILE(all trial totals, 0.8)
standard error  = STDEV(totals) / SQRT(trials)</code></pre>
<p><strong>U is clamped</strong> away from 0 and 1 so the normal inverses stay finite at the
extremes &mdash; without it a single draw at exactly 0 produces an infinity that poisons the whole
run.</p>
<p>And the copula construction is what keeps this honest: because Z_i is standard normal by
construction, U_i is uniform, so each variable's own distribution is <em>exactly</em> preserved. The
correlation changes how variables move together and nothing else.</p>""",

"proof": """<p>A stochastic model cannot be checked by matching values, so this one is checked by
asserting the properties that must hold for a <em>correct</em> sampler and would fail for a broken
one. The workbook is recalculated in LibreOffice with real draws.</p>
<p><strong>Last three independent runs: 0 statistical failures, 0 formula errors.</strong></p>
<ul>
<li>Every marginal matches theory &mdash; mean within five standard errors, standard deviation
within 18%, for all 12 variables across triangular, uniform, normal and lognormal. A mis-transcribed
inverse CDF fails here immediately</li>
<li>Hard bounds hold: triangular draws never escape [min, max], lognormal never goes negative</li>
<li>The shared factor Z is standard normal (mean ~0, sd ~1)</li>
<li><strong>Correlation actually bites</strong> &mdash; the observed spread of the total exceeds the
independent-sum prediction, by a ratio of 1.59 to 1.64</li>
<li>Percentiles are monotonic, and the sheet's P50 matches the empirical median</li>
<li>The histogram accounts for every single trial</li>
<li>The top sensitivity driver is genuinely among the highest-variance inputs</li>
</ul>
<p>That histogram assertion caught a real bug. The bins were defined as <code>&gt; lo</code> and
<code>&lt;= hi</code>, which silently drops any trial sitting exactly on a boundary &mdash;
including the minimum. Three trials in a thousand were vanishing. The bins now tile
<code>[lo, hi)</code> with the last one closed.</p>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "Add-in needed", "Correlation", "Works in Sheets"],
    [["This workbook", ("$69", "good"), ("No", "good"), ("Yes, copula", "good"),
      ("Yes", "good")],
     ["@RISK / Crystal Ball", "~$500+", ("Yes", "bad"), ("Yes", "good"), ("No", "bad")],
     ["A three-point estimate", ("$0", ""), ("No", "good"), ("No", "bad"), ("Yes", "good")],
     ["A free simulation template", ("$0", ""), ("Sometimes", ""), ("Almost never", "bad"),
      ("Varies", "")]],
),

"faq": [
 ("What is Monte Carlo simulation?",
  "Running a calculation many times, drawing each uncertain input at random from a range you "
  "specify, and collecting the results. Instead of one estimate you get a distribution, so you can "
  "answer questions like 'what figure am I 80 percent likely to come in under'."),
 ("Does it need an add-in like @RISK or Crystal Ball?",
  "No. It uses inverse-transform sampling on RAND(), which is ordinary spreadsheet arithmetic. That "
  "is why it also works in Google Sheets, Numbers and LibreOffice."),
 ("Why does correlation matter so much?",
  "Because correlated inputs do not cancel each other out. If several costs rise together, the "
  "total is far more variable than an independent model predicts. Here the observed spread runs "
  "1.59 to 1.64 times the independent-sum prediction — about 60 percent more."),
 ("Which distribution should I use?",
  "Triangular when you know minimum, most likely and maximum — the usual choice for cost and "
  "duration. Uniform when anything in the range is equally likely. Normal for measurement-like "
  "variation. Lognormal when a value cannot go below zero but has a long upper tail."),
 ("Why does the answer change every time I edit a cell?",
  "RAND() is volatile, so any recalculation reruns the whole simulation. That is deliberate — press "
  "F9 a few times to see whether your conclusion is stable. To freeze a run, paste values into the "
  "Compare tab."),
 ("Is 1,000 trials enough?",
  "Usually, for planning decisions. The workbook shows the standard error of the mean so you can "
  "judge it rather than guess."),
 ("Why not just fit a normal curve to the total?",
  "Because the sum of skewed correlated inputs is itself skewed. A normal fit understates exactly "
  "the upper tail you built the model to understand. Percentiles here come from the real trials."),
 ("Will it work in Google Sheets?",
  "Yes. It uses RAND, NORMSINV, NORMSDIST and PERCENTILE, all of which Sheets and Numbers support."),
],
"related": [
 ("design-of-experiments-excel", "Design of experiments — finding which inputs matter at all"),
 ("spc-control-chart-cpk-workbook", "SPC and process capability — measuring variation as it happens"),
 ("construction-cash-flow-forecast", "Cash flow forecast — a deterministic model worth stressing"),
],
},

# --------------------------------------------------------------------------- #
{
"key": "federal-grant-budget-mtdc",
"slug": "federal-grant-budget-mtdc",
"group": "Grants and compliance",
"category": "Grant budgeting",
"pill": "Calculator",
"card_title": "Federal grant budget and MTDC",
"card_blurb": "Builds the MTDC base properly — subaward cap per period not per year, equipment "
              "tested per unit, caps applied as margins.",

"title": "Federal Grant Budget & MTDC Indirect Cost Calculator, Excel",
"description": "Build the MTDC base correctly: subaward cap per period of performance, equipment "
               "tested per unit, and caps applied as margins. De minimis versus NICRA.",
"h1": "MTDC is a subtraction, and that is where budgets go wrong",
"lead": "Almost every grant budget template adds costs up. The hard part of a federal budget is "
        "the <em>taking away</em> &mdash; working out which costs are excluded from the base your "
        "indirect rate applies to. Get the subtraction wrong and you either leave money behind or "
        "claim money that comes back at audit.",
"chips": ["3-year award", "De minimis vs NICRA"],
"keywords": ["MTDC calculator", "federal grant budget template",
             "modified total direct cost excel", "indirect cost rate calculator",
             "de minimis indirect rate", "subaward cap MTDC"],

"short_answer": """<p>Modified Total Direct Cost is your total direct costs <em>minus</em> certain
categories: equipment, capital expenditure, patient care, rental costs, tuition remission,
scholarships, participant support &mdash; and the portion of each subaward above a cap. Your
indirect rate applies only to what is left.</p>
<p>Three parts are consistently done wrong. The subaward cap runs <strong>per period of
performance, not per year</strong>. Equipment is tested against the capitalisation floor
<strong>per unit, not per line</strong>. And a cap expressed as a percentage of <em>total</em> cost
is a <strong>margin, not a markup</strong>.</p>""",

"problem_h": "Why a subtraction is harder than an addition",
"problem": """<p>Grant budgets have two layers. <strong>Direct costs</strong> are the things you
can point at &mdash; salaries, travel, supplies. <strong>Indirect costs</strong> are the share of
keeping the lights on that this project ought to carry, and you recover them by applying a
percentage rate.</p>
<p>A percentage of what, though? Not of everything. If it were, an organisation could inflate its
indirect recovery just by buying an expensive machine or passing a large chunk of the work to
somebody else &mdash; neither of which creates much administrative burden for them.</p>
<p>So the rules define a smaller base: total direct cost, <em>minus</em> the categories that would
distort it. That is MTDC, and it is a subtraction.</p>
<p>Subtractions are harder to get right than additions, because every excluded category has its own
rule, and none of them are obvious. A template that adds a budget up cannot tell you it got the
base wrong &mdash; it will produce a confident, tidy, incorrect number.</p>""",

"cost_h": "Three errors, and what each one actually costs",
"cost_intro": """<p>On the seeded three-year award &mdash; $1,757,415 of total direct cost, a
$1,370,415 MTDC base &mdash; here is what each of the three common errors does. Note that they do
not all point the same way.</p>""",
"cost_table": table(
    "The three errors, priced through the cap",
    ["Error", "Base moves by#", "Recovery moves by#", "Which direction"],
    [["Subaward cap applied per year instead of per period", ("+$114,000", "bad"),
      ("+$17,100", "bad"), ("OVER-CLAIM — comes back at audit", "bad")],
     ["Equipment tested by line total instead of per unit", ("&minus;$8,160", "bad"),
      ("&minus;$1,224", "bad"), ("Money left on the table", "bad")],
     ["Still using the pre-2024 $25,000 subaward cap", ("&minus;$75,000", "bad"),
      ("&minus;$11,250", "bad"), ("Money left on the table", "bad")]],
),
"cost_after": """<p>The first one is the dangerous one. It <em>increases</em> your recovery, which
means nothing in your own review will flag it &mdash; you get more money and everything looks
fine, until an audit takes it back.</p>
<p>The other two cost you money quietly. Twelve tablets at $680 each are an $8,160 line, but
equipment is tested <strong>per unit</strong> against the capitalisation floor, and $680 is well
under it &mdash; so they are supplies, and they <em>stay in the base</em>. Treating the line total
as equipment removes $8,160 you were entitled to claim on.</p>""",

"why_h": "Why the subaward cap is the hard one",
"why": """<p>Only the first slice of each subaward counts toward MTDC. The rest is excluded. The
part people get wrong is <em>when</em> that slice is consumed.</p>
<p>The cap runs across the <strong>whole period of performance</strong>, not per year. It is
consumed in the order the money goes out:</p>
<pre><code>in base, year y = MAX(0, MIN(spend in year y,
                             cap - everything spent in earlier years))</code></pre>
<p>So a subaward spending $80,000 in year one has already used the whole cap; nothing in years two
or three counts. Apply the cap per year and you count it three times over.</p>
<p>The three subawards in the sample data cross the cap in three different years, deliberately, so
the fill is genuinely exercised rather than accidentally correct:</p>""",

"howto_name": "How to build the MTDC base correctly",
"howto_desc": "Five steps to a grant budget whose indirect recovery survives review.",
"steps": [
 {"h": "Add up the total direct cost",
  "plain": "List every direct cost across the whole period of performance — personnel, fringe, "
           "travel, supplies, equipment, subawards and everything else.",
  "body": """<p>Everything first, categorised. On the sample award this comes to $1,757,415.</p>"""},
 {"h": "Test equipment per unit, not per line",
  "plain": "Compare each item's per-unit acquisition cost against the capitalisation threshold. "
           "Items below it are supplies and stay in the base.",
  "body": """<p>Twelve tablets at $680 are an $8,160 budget line and they are <strong>not</strong>
  equipment. The regulation tests per-unit acquisition cost against the capitalisation floor, so
  they are supplies and they stay in the MTDC base.</p>
  <p>Getting this wrong removes $8,160 from your base and $1,224 from your recovery, for
  nothing.</p>"""},
 {"h": "Fill each subaward's cap across the whole period",
  "plain": "For each subaward, count spending toward the cap in the order it occurs across all "
           "years, and exclude everything above the cap.",
  "body": """<pre><code>in base, year y = MAX(0, MIN(spend_y, cap - spent in earlier years))</code></pre>
  <p>Per period of performance, not per year. The workbook also checks the year-by-year fill against
  a closed form &mdash; the total in base must equal MIN(total spend, cap) &mdash; so the
  arithmetic is verified two independent ways.</p>"""},
 {"h": "Subtract the other excluded categories",
  "plain": "Remove capital expenditure, patient care, rental costs, tuition remission, "
           "scholarships and participant support from the base.",
  "body": """<p>Each has its own definition and each is a straight exclusion. On the sample award
  the exclusions total $387,000, leaving an MTDC base of $1,370,415 &mdash; 78.0% of total direct
  cost.</p>"""},
 {"h": "Apply the rate, and handle any cap as a margin",
  "plain": "Multiply the base by your indirect rate. If a funder caps indirect as a percentage of "
           "total cost rather than direct cost, divide rather than multiply.",
  "body": """<pre><code>% of DIRECT cost -> allowed = rate x direct
% of TOTAL cost  -> allowed = direct x rate / (1 - rate)</code></pre>
  <p>12% of total cost is 13.6% of direct cost. This is the same margin-versus-markup shape that
  appears in the bid calculators and in recipe costing, and it turns up a third time in cost share:
  <code>federal x r/(1-r)</code>, not <code>federal x r</code>.</p>"""},
],

"inside_intro": """<p>Ten tabs &mdash; the most of anything here, because the exclusions each need
their own working. Seeded with a three-year award whose three subawards cross the cap in three
different years.</p>""",
"tabs": {
 "Start Here": "What to fill in, in what order, and how to import the file into Google Sheets.",
 "Setup": "Period of performance, indirect rate, subaward cap and capitalisation threshold — all "
          "inputs, because all three moved in 2024.",
 "Personnel": "Salaries and fringe by person and by year.",
 "Non-Personnel": "Travel, supplies, equipment and everything else, with equipment tested per unit.",
 "Subawards": "Each subaward, with the cap filled in the order the money goes out across the whole "
              "period.",
 "Budget by Year": "The full budget with the MTDC base and indirect recovery calculated per year.",
 "Indirect Comparison": "De minimis against a negotiated rate, with any cap applied — so you can "
                        "see what negotiating is actually worth.",
 "Cost Share": "Matching requirements, including caps expressed on total rather than federal cost.",
 "Checks": "Independent verification of the base, the cap fills and the totals.",
 "How It Works": "Every exclusion rule and every formula, written out.",
},
"shot_tab": "Budget by Year",
"shot_alt": "The Budget by Year tab showing direct costs, MTDC exclusions, the resulting base and "
            "indirect recovery for each year of the award",
"shot_note": "The MTDC base is 78.0% of total direct cost here — $387,000 is excluded.",

"includes": [
 "One .xlsx file, ten tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "A three-year sample award with subawards crossing the cap in three different years",
 "Subaward cap filled per period of performance, verified two independent ways",
 "Equipment tested per unit against the capitalisation floor",
 "De minimis versus negotiated rate comparison, with caps applied as margins",
 "Thresholds as inputs, because all three changed in 2024",
 "Free lifetime updates",
],
"fine": "A budgeting tool, not compliance advice. Confirm current thresholds for your award.",

"math_h": "The arithmetic, written out",
"math": """<pre><code>MTDC = total direct cost
     - equipment, capital expenditure, patient care, rental,
       tuition remission, scholarships, participant support
     - the portion of EACH subaward above the cap

subaward in base, year y = MAX(0, MIN(spend_y, cap - spent in earlier years))
    # verified against the closed form: total = MIN(total spend, cap)

indirect computed = MTDC x rate
allowed, % of direct = rate x direct
allowed, % of TOTAL  = direct x rate / (1 - rate)
recovered = MIN(computed, allowed)</code></pre>
<p>One more subtlety, in how the workbook prices an error. It computes</p>
<pre><code>MIN(rate x (base + delta), allowed) - MIN(rate x base, allowed)</code></pre>
<p>rather than <code>rate x delta</code>. That matters because if the cap is already binding, an
error that moves your base correctly shows as worth <em>nothing</em> &mdash; the cap eats it. A
naive calculation would tell you a mistake cost you money when it did not.</p>""",

"proof": """<p>The clearest demonstration is the de minimis versus negotiated rate comparison on
the seeded award, because it shows the cap doing its work.</p>
<div class="tbl"><table><caption>What negotiating a rate is actually worth on this award</caption>
<thead><tr><th>Rate</th><th class="num">Computed</th><th class="num">Cap allows</th>
<th class="num">Recovered</th><th class="num">Unrecovered</th></tr></thead>
<tbody>
<tr><td>De minimis 15%</td><td class="num">$205,562</td><td class="num">$239,648</td>
<td class="num good">$205,562</td><td class="num">$0</td></tr>
<tr><td>Negotiated 28%</td><td class="num">$383,716</td><td class="num">$239,648</td>
<td class="num good">$239,648</td><td class="num bad">$144,069</td></tr>
</tbody></table></div>
<p>The rate gap suggests negotiating is worth $178,154. It is actually worth
<strong>$34,085</strong>, because the cap eats the rest. That is the kind of thing a budget
template that only adds up cannot tell you, and it is a decision that costs real staff time to get
wrong.</p>
<p>The seed data is tuned so the cap binds for the negotiated rate but <em>not</em> for de minimis,
which means MTDC accuracy still drives money on the shipped figures &mdash; if the cap bound in
both cases, the whole subtraction would be academic and the workbook would be untested.</p>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "Subaward cap", "Equipment test", "Cap as margin"],
    [["This workbook", ("$89", "good"), ("Per period", "good"), ("Per unit", "good"),
      ("Yes", "good")],
     ["A funder's budget form", ("$0", ""), ("Not calculated", "bad"), ("Up to you", "bad"),
      ("No", "bad")],
     ["A free grant budget template", ("$0", ""), ("Usually per year", "bad"),
      ("By line", "bad"), ("No", "bad")],
     ["Your grants office", "Staff time", ("Correct", "good"), ("Correct", "good"),
      ("Correct", "good")]],
),

"faq": [
 ("What is MTDC?",
  "Modified Total Direct Cost — your total direct costs minus equipment, capital expenditure, "
  "patient care, rental costs, tuition remission, scholarships, participant support, and the "
  "portion of each subaward above a cap. Your indirect rate applies only to that base."),
 ("Is the subaward cap per year or for the whole award?",
  "For the whole period of performance, consumed in the order the money goes out. Applying it per "
  "year counts it multiple times and over-claims — on the sample award that is $114,000 of extra "
  "base and $17,100 of recovery that comes back at audit."),
 ("How is equipment tested?",
  "Per unit, against the capitalisation threshold. Twelve tablets at $680 are an $8,160 line but "
  "each unit is well below the floor, so they are supplies and stay in the base."),
 ("What is the difference between a cap on direct cost and a cap on total cost?",
  "A cap expressed as a percentage of total cost is a margin, not a markup. Allowed indirect is "
  "direct x rate / (1 - rate), not rate x direct. Twelve percent of total is 13.6 percent of direct."),
 ("Is negotiating a rate worth it?",
  "Less than the rate gap suggests, if a cap binds. On the sample award moving from 15 percent de "
  "minimis to 28 percent negotiated looks like $178,154 but is actually worth $34,085, because the "
  "cap absorbs the rest."),
 ("Why are the thresholds inputs rather than built in?",
  "Because all three of them moved with the 2024 Uniform Guidance revision. A hardcoded threshold "
  "is a silent error the moment the rules change, so they are inputs you set."),
 ("Will it work in Google Sheets?",
  "Yes. Upload the .xlsx to Google Drive and open it with Google Sheets. No macros, no add-ins."),
 ("Is this compliance advice?",
  "No. It is a calculator that applies the MTDC rules correctly. Confirm the current thresholds and "
  "your own negotiated rate agreement for your specific award."),
],
"related": [
 ("certified-payroll-davis-bacon", "Certified payroll — another set of federal rules with real exposure"),
 ("construction-cash-flow-forecast", "Cash flow forecast — when funded work actually pays"),
],
},
]

for _p in PRODUCTS_C:
    _p.setdefault("diagram_problem", V[_p["key"]]["problem"])
    _p.setdefault("diagram_fix", V[_p["key"]]["fix"])
