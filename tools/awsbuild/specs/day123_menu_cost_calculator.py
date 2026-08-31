"""Day 123 -- 2026-08-25 -- Menu cost calculator."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "menu-cost-calculator"
NAME = "Menu cost calculator"

SPEC = {
 "slug": SLUG, "date": "2026-08-25", "name": NAME,
 "tagline": ("Works out what a dish actually costs to put on a plate -- after trim, after waste, "
             "at this week's prices rather than the ones from when the recipe was written, and "
             "with portion size treated as the variable it really is."),
 "lede": ("A small system that turns purchase prices into plate costs, stamps every costing with "
          "the date and prices it used, and reports dish profitability in a way that does not "
          "lead straight to the classic mistake of removing the dish that sells everything else. "
          "Seven posts on the same system, one diagram at a time, with a cost breakdown and an "
          "engineering reference at the end."),
 "keywords": ["food cost", "menu engineering", "hospitality", "gross profit", "recipe costing",
              "serverless"],
 "icons": ["form", "money", "scale"],
 "faq": [
  ("What is a menu cost calculator?",
   "A small serverless system that converts ingredient purchase prices into cost per portion "
   "using measured yields, tracks price changes over time, and reports dish-level profitability."),
  ("What is yield and why does it matter?",
   "The proportion of what you buy that reaches the plate. Buying ten kilos of beef and serving "
   "six point eight means the plate cost is nearly fifty per cent higher than the purchase price "
   "suggests."),
  ("Why do costings need a date?",
   "Because ingredient prices change weekly. A costing without the date and prices it used cannot "
   "be checked, reproduced, or compared to a later one."),
  ("What moves food cost more, prices or portions?",
   "Portions, in most kitchens, and by a wide margin. The post on this shows why a twelve per "
   "cent portion drift outweighs a normal year of price movement."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "menu-cost-calculator-on-aws",
 "title": "A menu cost calculator on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Turns purchase prices into plate costs using real yields, stamps every costing, and "
          "reports profitability honestly. AWS, about $2 a month."),
 "og": ("The recipe says 180g of beef. You bought it at £11 a kilo. The plate cost is not "
        "£1.98, and the gap is the whole subject."),
 "abstract": ("The whole system on one page -- yield, price, portion &mdash; and the three "
              "adjustments between a purchase price and what a dish actually costs."),
 "lede": ("A dish is costed once, when the menu is written, using the prices from that week and "
          "the weights from the recipe. Eighteen months later beef has moved, the portion has "
          "crept, and nobody has recosted anything because recosting forty dishes by hand is a "
          "day's work. The gross profit has fallen four points and the reason is invisible."),
 "tags": ["food cost", "menu engineering", "hospitality", "gross profit", "recipe costing",
          "serverless"],
 "takeaways": [
  "Yield turns purchase price into usable price, and it is often a large adjustment.",
  "Every costing is stamped with the date and the exact prices used.",
  "Portion variance usually moves food cost more than ingredient prices do.",
  "Report cash margin alongside gross profit percentage, always.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Invoices", "sub": ["this week's prices"], "icon": "doc"},
      {"title": "Recipes", "sub": ["and measured yields"], "icon": "form"},
      {"title": "Whoever prices", "sub": ["the menu"], "icon": "person"}],
    "inside": [
      {"title": "Usable cost", "sub": ["purchase price", "adjusted for yield"], "icon": "scale"},
      {"title": "Plate cost", "sub": ["per portion,", "stamped with a date"], "icon": "money"},
      {"title": "Report", "sub": ["margin and %,", "and what sells"], "icon": "chart"}],
    "edges": [{"from": 0, "to": 0, "label": "prices"},
              {"from": 1, "to": 1, "label": "quantities and yields"},
              {"from": 2, "to": 2, "label": "costs, dated", "up": True}],
    "note": "The first box is where most of the error in hand-costing lives."}),
   "Three things outside the account, three pieces inside it. The yield adjustment in the first "
   "box is the one most hand-written costings omit entirely.",
   "System: purchase prices turned into dated plate costs",
   "Three boxes across the top sit outside the AWS account. On the left, Invoices carrying this "
   "week's prices. In the middle, Recipes and measured yields. On the right, Whoever prices the "
   "menu. Each connects by an arrow to the AWS account container below. Prices flow down into the "
   "account. Quantities and yields feed in. Costs, dated, go back out. Inside the AWS account are "
   "three components in a row. On the left, Usable cost, the purchase price adjusted for yield. "
   "In the middle, Plate cost per portion, stamped with a date. On the right, the Report, showing "
   "margin and percentage alongside what sells. A note at the bottom says the first box is where "
   "most of the error in hand-costing lives."),
  ("h3", "Three adjustments"),
  ("p", "Between the invoice and the plate there are three things that move the number, and "
        "hand-written costings typically include one of them."),
  ("ul", [
   "<strong>Yield.</strong> A whole beef fillet loses weight to trim; potatoes lose weight to "
   "peeling; a lettuce loses its outer leaves. The usable kilo costs more than the purchased "
   "kilo.",
   "<strong>Cooking loss.</strong> Meat loses weight in the pan, sauces reduce. A hundred and "
   "eighty grams on the plate is more than a hundred and eighty grams raw.",
   "<strong>Waste and trim value.</strong> Some trim becomes stock or staff food and has value; "
   "most is a cost. The treatment should be stated rather than assumed.",
  ]),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Usable cost.</strong> Applies measured yields to purchase prices, per ingredient. "
   "Part 2.",
   "<strong>Plate cost.</strong> Assembles a dish from its recipe at a point in time, stamped. "
   "Part 3.",
   "<strong>The report.</strong> Dish-level profitability, with the two numbers that have to "
   "appear together. Parts 4 and 5.",
  ]),
  ("h2", "One dish, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Beef at £11.00/kg", "sub": ["as purchased"], "icon": "doc"},
      {"title": "Yield 68%", "sub": ["usable: £16.18/kg"], "icon": "scale"},
      {"title": "180g on the plate", "sub": ["= £2.91"], "icon": "form"},
      {"title": "Plus the rest", "sub": ["= £4.62 total"], "icon": "money"},
      {"title": "Sells at £19.50", "sub": ["GP 76%, margin £14.88"], "icon": "chart"}],
    "title": "ONE DISH, END TO END",
    "note": "Costed on purchase price alone it looks like £3.68. That is a 20% error."}),
   "The same dish as one line. The yield step in the second box is worth nearly a pound on this "
   "plate and is the step most often skipped.",
   "One dish costed from purchase price through yield to plate cost",
   "A horizontal row of five boxes joined by arrows. Beef at eleven pounds a kilo as purchased. "
   "Yield sixty-eight per cent, giving a usable price of sixteen pounds eighteen a kilo. One "
   "hundred and eighty grams on the plate equals two pounds ninety-one. Plus the rest equals four "
   "pounds sixty-two total. Sells at nineteen pounds fifty, a gross profit of seventy-six per "
   "cent and a margin of fourteen pounds eighty-eight. A note says costed on purchase price alone "
   "it looks like three pounds sixty-eight, which is a twenty per cent error."),
  ("h2", "In plain words"),
  ("p", "Beef comes in at eleven pounds a kilo. The kitchen weighed a delivery, trimmed it, and "
        "weighed what was usable: sixty-eight per cent. So the usable cost is eleven divided by "
        "nought point six eight, which is sixteen pounds eighteen a kilo."),
  ("p", "A hundred and eighty grams on the plate costs two pounds ninety-one at that rate, "
        "against one pound ninety-eight if you use the purchase price. Add the potatoes, the "
        "sauce, the garnish and their own yields and the dish costs four pounds sixty-two."),
  ("p", "At nineteen fifty it makes fourteen pounds eighty-eight and runs at seventy-six per cent "
        "gross profit. Both of those numbers matter and the last post is about why reporting only "
        "one of them leads to bad menu decisions."),
  ("callout", "Design rules that shaped every decision", [
   "Yields are measured in the kitchen, not taken from a book.",
   "Every costing stores the exact prices used and the date.",
   "Recipes are versioned; changing a recipe does not rewrite history.",
   "Report cash margin and percentage together, always.",
   "Never automatically change a menu price.",
   "Say when a costing is stale, rather than quietly using old prices.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Recipe costing is done once and then not again, because doing it by hand is slow and "
        "the result goes out of date within a month. The consequence is that most kitchens are "
        "operating on costings that were correct at some point in the past and have drifted by an "
        "unknown amount."),
  ("p", "Automating the arithmetic is not the hard part. The parts that matter are getting yields "
        "measured once properly, keeping the price history so a change can be attributed, and "
        "presenting the result in a way that does not encourage the two classic errors: chasing "
        "gross profit percentage, and removing dishes that look unprofitable."),
  ("p", "The next four posts walk through each piece: how yield turns purchase price into plate "
        "cost, why prices need a date stamped on them, why portion size moves more than price "
        "does, and how to read a dish profitability report without getting it wrong. One diagram "
        "per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-yield-turns-purchase-price-into-plate-cost",
 "title": "How yield turns purchase price into plate cost",
 "nav": "How yield works",
 "read": 5, "words": 740,
 "desc": ("Measuring yield rather than looking it up, cooking loss, and what happens to the trim."),
 "og": ("A published yield table describes somebody else's butcher. Weighing it once in your own "
        "kitchen takes twenty minutes and is worth more."),
 "abstract": ("How to measure yield properly, why published figures mislead, how cooking loss "
              "compounds with trim loss, and how to treat trim that has value."),
 "lede": ("Yield is the largest single correction between an invoice and a plate, it varies by "
          "supplier and by season, and it is almost always taken from a table somebody found "
          "rather than from a scale."),
 "tags": ["food cost", "yield", "kitchen", "recipe costing", "hospitality", "serverless"],
 "takeaways": [
  "Measure yield in your own kitchen, three times, and average it.",
  "Yield varies by supplier and by season; re-measure when either changes.",
  "Trim loss and cooking loss compound; apply both.",
  "Trim with a use has a value and should be credited, with the assumption stated.",
  "A yield below expectation is a supplier finding, not just a costing input.",
 ],
 "blocks": [
  ("h2", "Measuring it"),
  ("fig", ("chain", {
    "entry": {"title": "A delivery arrives", "sub": ["weigh it as received"], "icon": "storage"},
    "steps": [
      {"title": "Weigh gross", "sub": ["before anything"], "icon": "scale"},
      {"title": "Prepare as normal", "sub": ["the same person, the same way"], "icon": "person"},
      {"title": "Weigh usable", "sub": ["what reaches the line"], "icon": "counter"},
      {"title": "Weigh usable trim", "sub": ["bones, offcuts for stock"], "icon": "form",
       "side": {"title": "Credited", "sub": ["at a stated value"], "icon": "money"}},
      {"title": "Yield, and a date", "sub": ["repeat three times"], "icon": "check"}],
    "note": "Three measurements, twenty minutes total. It is the highest-value data in the system."}),
   "How a yield is established. It is a kitchen exercise rather than a data exercise, and it only "
   "has to be done once per ingredient per supplier.",
   "How an ingredient yield is measured in the kitchen",
   "A vertical chain of five steps entered by a box labelled A delivery arrives, weigh it as "
   "received. Step one weighs gross, before anything. Step two prepares it as normal, by the same "
   "person in the same way. Step three weighs the usable portion that reaches the line. Step four "
   "weighs usable trim such as bones and offcuts for stock, with a side box saying it is credited "
   "at a stated value. Step five records the yield with a date, repeating three times. A note "
   "says three measurements take twenty minutes in total and it is the highest-value data in the "
   "system."),
  ("h3", "Why not a published table"),
  ("p", "Published yields describe an average specification prepared by an average person. Your "
        "supplier's trim specification, your chef's preferences and your portioning all differ, "
        "and the spread between kitchens on the same ingredient is wide enough to move a dish "
        "cost by twenty per cent."),
  ("p", "The table is a reasonable starting point for a dish that has never been made. It should "
        "be replaced by a measurement the first time the ingredient is actually prepared, and "
        "flagged as unmeasured until then so nobody mistakes it for a fact."),
  ("h3", "It changes"),
  ("p", "A different supplier, a different specification, a seasonal change in size &mdash; all "
        "move yield. Small root vegetables have worse yield than large ones because peeling loss "
        "is proportional to surface area, which is why winter costings on some vegetables are "
        "genuinely different from summer ones."),
  ("p", "Re-measuring quarterly on the top ten ingredients by spend covers most of the exposure "
        "and is an hour a quarter."),
  ("h2", "Two losses, compounded"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Purchased", "parts": [("usable", 1000)]},
      {"label": "After trim (68%)", "parts": [("usable", 680), ("lost", 320)]},
      {"label": "After cooking (82%)", "parts": [("usable", 558), ("lost", 442)]}],
    "series": [("usable", "Grams reaching the plate", "#7AA116"),
               ("lost", "Grams lost", "#DD344C")],
    "unit": "",
    "note": "A kilo bought becomes 558g served. The effective cost is 79% higher, not 47%."}),
   "Trim loss and cooking loss applied in sequence. Applying only one of them is the common error "
   "and it understates the cost substantially.",
   "How trim loss and cooking loss compound on one kilogram of an ingredient",
   "A stacked bar chart with three bars in grams. Two series: grams reaching the plate in green, "
   "and grams lost in red. Purchased: one thousand grams. After trim at sixty-eight per cent: six "
   "hundred and eighty usable, three hundred and twenty lost. After cooking at eighty-two per "
   "cent: five hundred and fifty-eight usable, four hundred and forty-two lost. A note says a "
   "kilo bought becomes five hundred and fifty-eight grams served, so the effective cost is "
   "seventy-nine per cent higher rather than forty-seven."),
  ("p", "Which of the two applies depends on how the recipe states its quantities. A recipe "
        "written in cooked weight on the plate needs both; one written in prepared raw weight "
        "needs only the trim yield."),
  ("p", "That distinction has to be explicit per recipe line, because getting it wrong in either "
        "direction produces a cost that is out by twenty per cent and looks entirely plausible."),
  ("h2", "Trim that has value"),
  ("callout", "How to treat the offcuts", [
   "<strong>Bones and trim that become stock</strong> have a real value: what you would otherwise "
   "buy.",
   "<strong>Credit them at that replacement value,</strong> not at the purchase price of the "
   "original ingredient.",
   "<strong>Only if they are actually used.</strong> Trim that is thrown away when the stock pot "
   "is full is a cost.",
   "<strong>State the assumption</strong> on the costing, because it is a judgement and it can be "
   "generous.",
   "<strong>Staff food is a cost,</strong> and belongs in its own line rather than hidden in "
   "yield.",
   "<strong>When in doubt, do not credit it.</strong> An uncredited yield is conservative and an "
   "over-credited one silently improves every dish on the menu.",
  ]),
  ("p", "The last line is worth holding to. Yield credits are the easiest place for optimism to "
        "enter a costing model, and once it is there it improves every dish by a few per cent in "
        "a way nobody can see."),
  ("h3", "Yield as a supplier signal"),
  ("p", "A yield that drops from sixty-eight to sixty-one per cent on the same ingredient is a "
        "supplier telling you something: a change in specification, more fat, more trim, smaller "
        "units. The price per kilo may not have moved at all while the cost per plate went up "
        "eleven per cent."),
  ("p", "That is a genuinely useful finding and it is invisible without measured yields. It is "
        "also a specific, evidenced conversation with the supplier rather than a general "
        "complaint about quality."),
  ("p", "Next: why a costing needs a date."),
 ],
},
{
 "slug": "why-prices-need-a-date-stamped-on-them",
 "title": "Why prices need a date stamped on them",
 "nav": "Prices and dates",
 "read": 5, "words": 720,
 "desc": ("Costings that go stale, attributing a change to a cause, and versioned recipes."),
 "og": ("A dish cost with no date attached cannot be checked, reproduced, or compared to "
        "anything, which makes it an opinion."),
 "abstract": ("Why every costing stores the prices it used, how a change is attributed to price "
              "or recipe, why recipes are versioned, and how staleness is surfaced."),
 "lede": ("The difference between a costing system that is useful for two months and one that is "
          "useful for years is a stored date and a stored set of prices."),
 "tags": ["food cost", "price tracking", "versioning", "records", "hospitality", "serverless"],
 "takeaways": [
  "Store the price of every ingredient used, not a reference to the current price.",
  "That is what lets a cost change be attributed to a specific ingredient.",
  "Recipes are versioned; a recipe change is a new version, not an edit.",
  "Surface staleness: a costing older than a month should say so.",
  "Weighted average purchase price beats the latest invoice.",
 ],
 "blocks": [
  ("h2", "Stamped, not referenced"),
  ("fig", ("chain", {
    "entry": {"title": "Cost a dish", "sub": ["today"], "icon": "form"},
    "steps": [
      {"title": "Recipe version", "sub": ["the one in use now"], "icon": "doc"},
      {"title": "Each ingredient price", "sub": ["copied in, not linked"], "icon": "money"},
      {"title": "Each yield used", "sub": ["copied in too"], "icon": "scale"},
      {"title": "The plate cost", "sub": ["computed once"], "icon": "counter"},
      {"title": "Stored immutably", "sub": ["with the date"], "icon": "lock"}],
    "note": "Copy the inputs in. A costing that recomputes itself has no history at all."}),
   "How a costing is stored. Copying the inputs rather than referencing them is what makes two "
   "costings comparable months apart.",
   "How a dish costing is computed and stored immutably",
   "A vertical chain of five steps entered by a box labelled Cost a dish, today. Step one records "
   "the recipe version in use now. Step two copies in each ingredient price rather than linking "
   "to it. Step three copies in each yield used. Step four computes the plate cost once. Step "
   "five stores it immutably with the date. A note says to copy the inputs in, because a costing "
   "that recomputes itself has no history at all."),
  ("h3", "What this buys you"),
  ("p", "Two costings of the same dish, three months apart, with all their inputs stored, can be "
        "diffed. The dish went from four sixty-two to five oh eight, and eighty per cent of that "
        "is the beef price, twelve per cent is the cream, and the rest is rounding."),
  ("p", "Without stored inputs the only available statement is that the dish costs more, which "
        "everybody already knew. The attribution is the useful part and it costs nothing except "
        "storing a few numbers."),
  ("h2", "Attributing a change"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Beef", "parts": [("chg", 31)]},
      {"label": "Cream", "parts": [("chg", 7)]},
      {"label": "Potatoes", "parts": [("chg", 4)]},
      {"label": "Yield change", "parts": [("chg", 9)]},
      {"label": "Recipe change", "parts": [("chg", -5)]}],
    "series": [("chg", "Contribution to cost change, pence", "#ED7100")],
    "unit": "",
    "note": "Forty-six pence of movement, explained line by line. Beef is two thirds of it."}),
   "One dish's cost change decomposed. The yield line is included because a yield movement is "
   "just as real as a price movement and is usually ignored.",
   "What drove one dish's cost change, broken down by ingredient",
   "A bar chart with five bars showing contribution to cost change in pence. Beef: thirty-one "
   "pence. Cream: seven pence. Potatoes: four pence. Yield change: nine pence. Recipe change: "
   "minus five pence. A note says forty-six pence of movement explained line by line, and beef is "
   "two thirds of it."),
  ("p", "That decomposition answers the only question worth asking when a food cost percentage "
        "moves: what changed? Without it the response is a general instruction to watch costs, "
        "which nobody can act on."),
  ("p", "It also identifies where to spend effort. A dish whose cost is dominated by one "
        "ingredient is a dish whose profitability depends on one supplier negotiation, which is "
        "worth knowing before the negotiation."),
  ("h3", "Weighted average, not latest"),
  ("p", "Using the most recent invoice price makes costings jump around with delivery timing and "
        "makes a promotional price look like the new normal. A weighted average over the last few "
        "deliveries is more stable and is closer to what the kitchen is actually consuming."),
  ("p", "The exception is a genuine step change &mdash; a new contract, a supplier switch &mdash; "
        "where the average lags reality for several weeks. Flagging a price that has moved more "
        "than a threshold from the average, so somebody can decide, handles that without needing "
        "cleverness."),
  ("h2", "Versioned recipes"),
  ("callout", "Why a recipe change is a new version", [
   "<strong>The portion went from 180g to 200g.</strong> That is a different dish, costed "
   "differently.",
   "<strong>Editing the recipe in place</strong> makes every historical costing wrong and "
   "unexplainable.",
   "<strong>A new version</strong> keeps both, and the costing history shows exactly when the "
   "change happened.",
   "<strong>Sales data joins to the version,</strong> so a margin change can be traced to a "
   "recipe change rather than blamed on prices.",
   "<strong>The old version stays</strong> because the menu may go back to it seasonally.",
   "<strong>One field, one discipline,</strong> and it makes the whole history usable.",
  ]),
  ("h3", "Surfacing staleness"),
  ("p", "A costing more than a month old should say so wherever it appears, because a menu "
        "priced from a stale costing is the failure mode this system exists to prevent, and it "
        "recurs quietly."),
  ("p", "Recosting is cheap once the prices are flowing in, so the practical answer is to recost "
        "everything weekly and keep every version. Storage is trivial and the history is the "
        "asset."),
  ("p", "Next: the variable that moves more than price does."),
 ],
},
{
 "slug": "why-portion-size-moves-more-than-price-does",
 "title": "Why portion size moves more than price does",
 "nav": "Portion, not price",
 "read": 5, "words": 720,
 "desc": ("Portion drift, what it costs, why measuring it is the only fix, and the theoretical "
          "against actual comparison."),
 "og": ("A twelve per cent portion drift costs more than a normal year of ingredient inflation, "
        "and nobody is looking at it."),
 "abstract": ("How portion drift happens, its size relative to price movement, why the theoretical "
              "against actual usage comparison is the only way to see it, and what to do about "
              "it."),
 "lede": ("Everybody watches ingredient prices, which move a few per cent a year and are outside "
          "your control. Almost nobody watches portion size, which moves more, is entirely within "
          "your control, and does not appear on any invoice."),
 "tags": ["food cost", "portion control", "variance", "kitchen", "gross profit", "serverless"],
 "takeaways": [
  "Portion drift is gradual, unintentional, and larger than annual price movement.",
  "The only way to see it is theoretical usage against actual usage.",
  "Compute theoretical from dishes sold times recipe quantities.",
  "The gap is portion drift, waste, and theft, in roughly that order of size.",
  "Scales on the line are the fix, and they need a reason to be used.",
 ],
 "blocks": [
  ("h2", "The relative sizes"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Ingredient prices", "parts": [("eff", 4)]},
      {"label": "Yield change", "parts": [("eff", 3)]},
      {"label": "Portion drift", "parts": [("eff", 12)]},
      {"label": "Waste", "parts": [("eff", 5)]}],
    "series": [("eff", "Effect on food cost over a year, %", "#DD344C")],
    "unit": "",
    "note": "The one everybody watches is the smallest and the least controllable."}),
   "Four influences on food cost over a year. Portion drift is the largest, is invisible on any "
   "invoice, and is the only one fully within the kitchen's control.",
   "Four influences on annual food cost compared",
   "A bar chart with four bars showing effect on food cost over a year as a percentage. "
   "Ingredient prices: four per cent. Yield change: three per cent. Portion drift: twelve per "
   "cent. Waste: five per cent. A note says the one everybody watches is the smallest and the "
   "least controllable."),
  ("p", "Portion drift happens for entirely reasonable reasons. A busy service, a chef being "
        "generous, a new person who has never seen the intended portion, a plate that looks empty "
        "with the correct amount on it. None of them is a decision and together they are the "
        "largest single line on that chart."),
  ("h2", "Theoretical against actual"),
  ("fig", ("chain", {
    "entry": {"title": "A month of sales", "sub": ["by dish"], "icon": "chart"},
    "steps": [
      {"title": "Times recipe quantity", "sub": ["per ingredient"], "icon": "counter"},
      {"title": "Theoretical usage", "sub": ["what should have been used"], "icon": "form"},
      {"title": "Actual usage", "sub": ["opening + purchases - closing"], "icon": "storage"},
      {"title": "The gap", "sub": ["per ingredient"], "icon": "search"},
      {"title": "Rank by value", "sub": ["not by percentage"], "icon": "money"}],
    "note": "This calculation is the only way portion drift becomes visible. It needs a stock count."}),
   "How portion drift is measured. It requires a stock count, which is the reason most kitchens "
   "never see the number.",
   "How theoretical ingredient usage is compared with actual usage",
   "A vertical chain of five steps entered by a box labelled A month of sales by dish. Step one "
   "multiplies by recipe quantity per ingredient. Step two produces theoretical usage, what "
   "should have been used. Step three computes actual usage as opening stock plus purchases minus "
   "closing stock. Step four takes the gap per ingredient. Step five ranks by value rather than "
   "by percentage. A note says this calculation is the only way portion drift becomes visible and "
   "it needs a stock count."),
  ("h3", "It needs a stock count"),
  ("p", "There is no way round this. Actual usage can only be computed from opening stock, "
        "purchases and closing stock, which means counting the kitchen. Monthly is enough for the "
        "high-value ingredients, and counting only the top twenty by spend captures most of the "
        "value at a fraction of the effort."),
  ("p", "That partial count is worth stating as an option, because a full kitchen count is a "
        "half-day and a top-twenty count is forty minutes. The forty-minute version finds nearly "
        "all the money."),
  ("h3", "Rank by value"),
  ("p", "A twenty per cent variance on herbs is a few pounds; a six per cent variance on beef is "
        "several hundred. Ranking the gap by percentage puts the cheap ingredients at the top and "
        "sends people to investigate the wrong things."),
  ("h2", "What the gap is made of"),
  ("callout", "In roughly descending order", [
   "<strong>Portion drift.</strong> Usually the largest, and entirely fixable with scales and a "
   "reason to use them.",
   "<strong>Waste.</strong> Spoilage, over-production, dropped plates, returns. Some of it is "
   "unavoidable.",
   "<strong>Staff food.</strong> Real consumption that belongs in its own line, not in variance.",
   "<strong>Recipe inaccuracy.</strong> The written recipe does not match what is actually made.",
   "<strong>Count errors.</strong> Particularly on part-used containers and on anything measured "
   "by eye.",
   "<strong>Theft.</strong> Real, and usually smaller than the first two, and worth investigating "
   "only after they have been ruled out.",
  ]),
  ("p", "The order matters because the instinct on seeing a variance is to reach for the last "
        "item. In most kitchens the first two account for the great majority of it, and starting "
        "there is both more productive and considerably less damaging."),
  ("p", "The fourth item is worth checking early and is easy to miss: a recipe that says a "
        "hundred and eighty grams when the kitchen has always served two hundred produces a "
        "permanent eleven per cent variance that is a documentation problem rather than a control "
        "one."),
  ("h2", "Fixing it"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Scales on the line", "sub": ["for the top 5 dishes"], "icon": "scale"},
      {"title": "A reason to use them", "sub": ["the number, shared"], "icon": "chart"},
      {"title": "Recount in a month", "sub": ["same method"], "icon": "counter"},
      {"title": "Gap 12% to 4%", "sub": ["measured, not claimed"], "icon": "check"},
      {"title": "It drifts back", "sub": ["so measure quarterly"], "icon": "clock"}],
    "title": "PORTION CONTROL, MEASURED",
    "note": "The last box is the honest one. This is maintenance, not a project."}),
   "How portion drift is corrected and verified. The last box is the part that gets left out of "
   "most improvement stories.",
   "How portion drift is reduced and then re-measured",
   "A horizontal row of five boxes. Scales on the line for the top five dishes. A reason to use "
   "them: the number, shared. Recount in a month, same method. Gap falls from twelve per cent to "
   "four: measured, not claimed. It drifts back, so measure quarterly. A note says the last box "
   "is the honest one, and this is maintenance rather than a project."),
  ("p", "Sharing the number with the kitchen is the part that works. A variance figure presented "
        "as a problem to be solved by the people portioning, with the value attached, gets a "
        "better response than an instruction to be careful, and the recount a month later is what "
        "makes it real."),
  ("p", "Next: reading the profitability report."),
 ],
},
{
 "slug": "how-to-read-a-dish-profitability-report",
 "title": "How to read a dish profitability report without getting it wrong",
 "nav": "Reading the report",
 "read": 5, "words": 720,
 "desc": ("Percentage against cash, popularity against margin, and the dish that sells everything "
          "else."),
 "og": ("Chasing gross profit percentage sells more coffee and less steak, and the cash in the "
        "till goes down."),
 "abstract": ("Why percentage and cash margin must appear together, how popularity interacts with "
              "margin, the dishes that exist for other reasons, and what to actually change."),
 "lede": ("A dish profitability report is the most misread document in hospitality, and the two "
          "classic errors both come from looking at one number in isolation."),
 "tags": ["menu engineering", "gross profit", "margin", "reporting", "hospitality", "serverless"],
 "takeaways": [
  "Percentage and cash margin together, never one alone.",
  "Multiply margin by units sold; that is what pays the rent.",
  "Some dishes exist to bring people in or to complete a menu.",
  "Change the recipe or the price before removing a dish.",
  "A dish selling twice a week is a data question, not a profitability one.",
 ],
 "blocks": [
  ("h2", "The two-number rule"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Coffee", "parts": [("gp", 89)]},
      {"label": "Steak", "parts": [("gp", 68)]},
      {"label": "Coffee, cash", "parts": [("cash", 265)]},
      {"label": "Steak, cash", "parts": [("cash", 1330)]}],
    "series": [("gp", "Gross profit, %", "#8C4FFF"),
               ("cash", "Cash margin per week, £", "#7AA116")],
    "unit": "",
    "note": "Coffee wins on percentage. Steak pays five times more of the rent."}),
   "Two items compared on percentage and on cash. A menu managed on percentage alone systematically "
   "promotes the wrong things.",
   "Coffee and steak compared by gross profit percentage and by weekly cash margin",
   "A bar chart with four bars. Two series: gross profit as a percentage in purple, and cash "
   "margin per week in pounds in green. Coffee: eighty-nine per cent gross profit. Steak: "
   "sixty-eight per cent. Coffee cash margin: two hundred and sixty-five pounds a week. Steak "
   "cash margin: one thousand three hundred and thirty pounds a week. A note says coffee wins on "
   "percentage while steak pays five times more of the rent."),
  ("p", "The percentage is useful for comparing similar items and for spotting a dish whose cost "
        "has drifted. It is actively misleading as a menu management tool, because a business "
        "pays its rent in pounds rather than in percentages."),
  ("p", "So every line carries both, and the report is sorted by total cash margin: margin per "
        "dish multiplied by how many sell. That ordering answers the question most people are "
        "actually asking."),
  ("h2", "Popularity and margin together"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Sells well, good margin", "sub": ["protect it"], "icon": "check",
       "label": "leave alone"},
      {"title": "Sells well, poor margin", "sub": ["fix the recipe or price"], "icon": "money",
       "label": "the opportunity"},
      {"title": "Sells badly, good margin", "sub": ["promote it, or move it"], "icon": "chart",
       "label": "presentation"}],
    "target": {"title": "Sells badly, poor margin", "sub": ["the only removal candidate"],
               "icon": "question",
               "then": {"title": "And even then", "sub": ["check what it is for"],
                        "icon": "search"}},
    "note": "The second lane is where nearly all the money is, and it is the least acted on."}),
   "The four quadrants and what each one calls for. Only one of them is a candidate for removal, "
   "and even that one needs a question asked first.",
   "Four combinations of dish popularity and margin and what each needs",
   "Three boxes stacked on the left. Sells well with good margin, labelled leave alone: protect "
   "it. Sells well with poor margin, labelled the opportunity: fix the recipe or the price. Sells "
   "badly with good margin, labelled presentation: promote it or move it on the menu. All three "
   "converge on Sells badly with poor margin, the only removal candidate, and that leads down to "
   "And even then, check what it is for. A note says the second lane is where nearly all the "
   "money is and it is the least acted on."),
  ("h3", "The second lane"),
  ("p", "A popular dish with a poor margin is the single largest opportunity on most menus, "
        "because a small change is multiplied by a large number of covers. Twenty pence off the "
        "cost of something that sells forty times a week is four hundred pounds a year from one "
        "adjustment."),
  ("p", "The changes available are a smaller portion of the expensive component, a different "
        "supplier for it, a garnish that adds perceived value cheaply, or a price rise. All four "
        "are less drastic than removing a dish people evidently want."),
  ("h2", "Dishes that exist for other reasons"),
  ("callout", "Before removing anything, ask what it is for", [
   "<strong>The signature dish</strong> that people come for and then bring three friends who "
   "order other things.",
   "<strong>The menu completer:</strong> the vegetarian option, the children's option, the thing "
   "that means a group of six can all eat here.",
   "<strong>The anchor:</strong> the expensive item that makes everything else look reasonable, "
   "and which does not need to sell much.",
   "<strong>The one that uses the trim</strong> from something else, and whose removal makes "
   "another dish more expensive.",
   "<strong>The staff favourite</strong> is not a business reason, and it is worth saying so "
   "plainly.",
   "<strong>None of these are visible in the numbers,</strong> which is why the report proposes "
   "nothing.",
  ]),
  ("p", "The fourth item is the one a costing system can actually help with, and it is worth "
        "checking automatically: removing a dish that consumes the trim from another ingredient "
        "changes the yield credit on that ingredient and makes the other dish more expensive. "
        "That interaction is invisible unless something is looking for it."),
  ("h2", "The dish that sells twice a week"),
  ("fig", ("strip", {
    "stages": [
      {"title": "2 sales a week", "sub": ["8 in the month"], "icon": "counter"},
      {"title": "Margin looks bad", "sub": ["on 8 data points"], "icon": "question"},
      {"title": "Or looks great", "sub": ["equally likely"], "icon": "chart"},
      {"title": "Neither is evidence", "sub": ["say so"], "icon": "alarm"},
      {"title": "Grey it out", "sub": ["below 20 sales"], "icon": "filter"}],
    "title": "SMALL NUMBERS",
    "note": "The most dramatic movements on any menu report are always the least-sold dishes."}),
   "Why low-volume dishes are annotated rather than ranked. The same statistical caution as "
   "everywhere else in this series, applied to a menu.",
   "Why dishes with few sales are excluded from profitability rankings",
   "A horizontal row of five boxes. Two sales a week, eight in the month. Margin looks bad, on "
   "eight data points. Or looks great, equally likely. Neither is evidence, so say so. Grey it "
   "out, below twenty sales. A note says the most dramatic movements on any menu report are "
   "always the least-sold dishes."),
  ("p", "Greying out or annotating low-volume lines stops the report from generating a monthly "
        "conversation about a dish whose numbers are noise, which is otherwise where a good deal "
        "of the attention goes."),
  ("h3", "What the system does not do"),
  ("p", "It does not recommend a price, it does not recommend removing anything, and it does not "
        "compute an optimal menu. Those all require knowing what dishes are for, what the "
        "competition charges, and what the room will bear, none of which are in the data."),
  ("p", "What it does is make the arithmetic correct and current, decompose every change, and put "
        "the two numbers that matter next to each other. The decisions stay with whoever knows "
        "the restaurant."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="dish",
 volumes=[(40, "40 dishes"), (120, "120 dishes"), (500, "500 dishes")],
 read_each=0.4,
 msgs_each=0.0,
 lede=("The only model call is reading an invoice, and costings recompute weekly across the whole "
       "menu. A hundred and twenty dishes is a substantial menu or several sites. Here is where "
       "each cent goes."),
 takeaway_extra=("Invoice reading is the only variable; recosting every dish weekly is a rounding "
                 "error."),
 risks=[
  "<strong>Reading invoices that arrive as a file.</strong> Many suppliers provide structured "
  "data. Parsing it removes the only model cost in the system.",
  "<strong>Recosting on every price change.</strong> Weekly is enough, and it produces a clean "
  "series that can be compared.",
  "<strong>Storing costings without pruning.</strong> Weekly costings for five hundred dishes is "
  "tiny, but keep full detail for two years and roll up beyond that.",
 ],
 per_unit_note=("The read band is invoice lines rather than dishes; it is expressed per dish here "
                "for comparability. Nothing is emailed, so there is no messaging line."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="mc",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the stamped costing, and the yield model."),
 outside=[
  {"title": "Supplier invoices", "sub": ["file or scan"], "icon": "doc"},
  {"title": "Recipes and yields", "sub": ["versioned"], "icon": "form"},
  {"title": "Sales by dish", "sub": ["from the till"], "icon": "chart"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["invoices,", "weekly recost"], "icon": "storage"},
  {"title": "Lambda x3", "sub": ["prices, cost, report"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["ingredients, costings"], "icon": "database"}],
 note="us-east-1. One account. Costings copy their inputs in; recipes are versioned, never edited.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Supplier invoices, arriving as a file or a "
  "scan. Recipes and yields, versioned. And Sales by dish, from the till. Inside the account, "
  "three groups. S3 receiving invoices alongside EventBridge running a weekly recost. Three "
  "Lambda functions named prices, cost and report. And two DynamoDB tables named ingredients and "
  "costings. A note gives the region as us-east-1, one account, and states that costings copy "
  "their inputs in and recipes are versioned rather than edited."),
 functions=[
  ["<code>mc-prices</code>", "S3 put on the invoices prefix",
   "Extracts lines from a structured file, or reads a scan; updates the weighted average price",
   "180s / 1024&nbsp;MB"],
  ["<code>mc-cost</code>", "EventBridge, weekly",
   "Recosts every dish at current prices and yields; writes an immutable costing per dish",
   "300s / 1024&nbsp;MB"],
  ["<code>mc-report</code>", "EventBridge, monthly",
   "Joins costings to sales; decomposes cost changes; computes theoretical against actual usage",
   "300s / 1024&nbsp;MB"]],
 roles=[
  ["<code>mc-prices-role</code>",
   "<code>s3:GetObject</code>, <code>bedrock:InvokeModel</code>, <code>dynamodb:UpdateItem</code>",
   "The invoices prefix; one model id; ingredients"],
  ["<code>mc-cost-role</code>", "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "Ingredients; put only on costings"],
  ["<code>mc-report-role</code>", "<code>dynamodb:Query</code>", "Read-only across both tables"]],
 tables=[
  ("Table: ingredients",
   "PK   ingredient_id     S   beef_fillet\n"
   "     unit              S   kg\n"
   "     price_pence       N   weighted average of recent deliveries\n"
   "     price_latest      N   most recent invoice, for the step-change flag\n"
   "     trim_yield        N   0.68 -- measured, with a date\n"
   "     cook_yield        N   0.82 -- applied only where the recipe says cooked\n"
   "     yield_measured_at S   null means it came from a table, not a scale\n"
   "     trim_credit_pence N   0 unless the offcuts are genuinely used\n"
   "     supplier          S   yields are per supplier, not per ingredient\n\n"
   "`yield_measured_at` being null is surfaced on every costing that uses\n"
   "it, so a book figure is never mistaken for a measurement."),
  ("Table: costings",
   "PK   dish_id           S\n"
   "SK   costed_on         S   2026-08-25 -- weekly, immutable\n"
   "     recipe_version    S   v4\n"
   "     lines             L   [{ingredient, qty, unit, price_used,\n"
   "                             yield_used, basis: raw|cooked, cost}]\n"
   "     plate_cost_pence  N\n"
   "     menu_price_pence  N\n"
   "     gp_pct            N\n"
   "     margin_pence      N   reported next to gp_pct, always\n"
   "     stale             BOOL true if any input is over 30 days old\n\n"
   "`lines` copies price_used and yield_used in rather than referencing\n"
   "them. That copy is what makes two costings comparable months apart.")],
 inbound=[
  "<strong>Structured invoice files are parsed directly.</strong> Only scans reach the model, and "
  "moving a supplier onto a file removes that cost permanently.",
  "<strong>Prices are a weighted average</strong> over recent deliveries, with a flag when the "
  "latest invoice diverges enough to suggest a step change.",
  "<strong>Yields are per ingredient per supplier</strong>, with the measurement date. A supplier "
  "change invalidates the yield.",
  "<strong>Recipes are versioned.</strong> A portion change is a new version, so sales and "
  "costings both join to the version that was actually in use."],
 model_notes=[
  "<strong>One read per scanned invoice.</strong> Extracting supplier, date, lines, quantities, "
  "units and prices.",
  "<strong>It never estimates a yield.</strong> An unmeasured yield is flagged on every costing "
  "that depends on it, which is what gets it measured.",
  "<strong>It never suggests a price.</strong> Menu pricing needs the room, the competition and "
  "what the dish is for, none of which are in this data.",
  "<strong>Unit conversion is code, not a model.</strong> Cases to kilos, litres to millilitres: "
  "a lookup that must be right rather than probably right.",
  "<strong>The cost page assumes one read per invoice</strong>, which falls as suppliers move to "
  "files."],
 gotchas=[
  "Copy prices and yields into the costing rather than referencing them. A costing that recomputes "
  "itself has no history and no attribution.",
  "Apply cooking loss only where the recipe quantity is a cooked weight. Applying both losses to "
  "a raw-weight recipe overstates the cost by around twenty per cent.",
  "Keep yields per supplier and re-measure when the supplier changes. A specification change is a "
  "real cost movement with no price movement attached.",
  "Report cash margin next to gross profit percentage everywhere. A menu managed on percentage "
  "promotes coffee over steak.",
  "Grey out dishes below about twenty sales in the period. The most dramatic lines on any menu "
  "report are always the least-sold ones."],
))
