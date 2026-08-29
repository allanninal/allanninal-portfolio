#!/usr/bin/env python3
"""Product articles, part A.

Every page is written the same way and for the same two readers at once.

Above the `.depth` line it has to make sense to someone who has never heard the
words on it — the problem told as something that happens to people, a diagram, a
table of what the mistake costs. Below it are the formulas, the verifier result
and the comparison, because the person actually spending $59-$119 is a
controller or a chef or a quality engineer who will not buy on a story.

Every figure quoted here is traceable to a verify_math.py run in
~/Projects/gumroad-products/<line>/README.md. Nothing is illustrative. If a
number here cannot be found there, it should not be here.
"""
from build_product import table
from visuals import V

PRODUCTS_A = [

# --------------------------------------------------------------------------- #
{
"key": "construction-wip-schedule-workbook",
"slug": "construction-wip-schedule",
"group": "Construction and contracting",
"category": "Construction finance",
"pill": "Workbook",
"card_title": "Construction WIP schedule",
"card_blurb": "Percentage of completion with the loss rule most templates get wrong, "
              "plus fade analysis, income-statement tie-out and bonding ratios.",

"title": "Construction WIP Schedule Template for Excel and Sheets",
"description": "A WIP schedule that recognises the full loss on a loss job, ties to the "
               "income statement, and shows gross profit fade. Excel and Google Sheets.",
"h1": "the construction WIP schedule, explained simply",
"lead": "A WIP schedule answers one question: <em>you are halfway through a job — how much "
        "have you actually earned?</em> Get it right and your bank, your bonding agent and "
        "your accountant all trust your numbers. Get it wrong and you find out in the worst "
        "possible month.",
"chips": ["12 sample jobs", "Ties to your P&L"],
"keywords": ["construction WIP schedule", "work in progress schedule excel",
             "percentage of completion template", "WIP schedule template",
             "gross profit fade analysis", "over billing under billing",
             "construction bonding capacity", "contractor WIP report"],

"short_answer": """<p>A WIP (work-in-progress) schedule works out how much of each job you have
<strong>earned</strong> so far, which is almost never the same as how much you have
<strong>billed</strong>. You divide what a job has cost you so far by what you expect it to cost
in total. That gives you a percent. You have earned that percent of the contract.</p>
<p>The one place it stops being simple: if a job is going to lose money, you must record the
<strong>whole</strong> loss straight away — not the share of it matching your progress. This
workbook does that, and it checks that its own totals match your profit and loss statement.</p>""",

"problem_h": "What a WIP schedule is, in plain words",
"problem": """<p>Imagine you agree to paint a fence for $100. You think it will cost you $60 in
paint and time. You are halfway done and you have spent $30.</p>
<p>How much have you earned? Not $100 — you have not finished. Not $0 — you have done real work.
You have spent half of what you expected to spend, so you are half done, so you have earned
<strong>$50</strong>.</p>
<p>That is the whole idea. Cost is the measuring stick, because cost is the thing you can count.
Now do it for twelve jobs at once, every month, with money going out and invoices going in at
different times, and you need a schedule instead of a paragraph.</p>
<p>The second thing it tells you is whether you have billed ahead of the work or behind it. If you
have earned $50 and billed $70, you are <strong>over-billed</strong> by $20 — that $20 is not
profit, it is money you owe in work. If you billed $40, you are <strong>under-billed</strong> by
$10, and you have quietly lent the customer $10.</p>""",

"cost_h": "The mistake that costs the most",
"cost_intro": """<p>One job in the sample data is going to lose money. Harbor Point Parking Deck:
the contract is worth $3,480,000, and it is now going to cost $3,595,000. That is a
<strong>$115,000 loss</strong>, and the job is 88% complete.</p>
<p>Almost every free seven-column template will spread that loss across the job like it spreads
profit — 88% of it now, the rest later. That is the wrong rule. The moment you can see a job will
lose money, the entire loss belongs in this period.</p>""",
"cost_table": table(
    "Harbor Point Parking Deck — the same job, two rules",
    ["", "Loss recognised now#", "Still to come#", "Is it right?"],
    [["The rule: full loss immediately",
      ("&minus;$115,000", "good"), ("$0", "good"),
      "Correct. You know about the loss now, so you report it now."],
     ["What a prorated template does",
      ("&minus;$101,200", "bad"), ("&minus;$13,800", "bad"),
      "Wrong. It hides $13,800 of a loss you already know about."]],
    foot=["Overstatement, one job", ("$13,800", "bad"), "", "On a portfolio of 12 jobs"]),
"cost_after": """<p>$13,800 on one job sounds survivable. The problem is what it does to
everything downstream: your gross profit is too high, so your income statement is too high, so the
bonding capacity you calculate off that equity is too high — and you bid work on the strength of a
number that was never real.</p>""",

"why_h": "Why this one rule is the whole product",
"why": """<p>The arithmetic in a WIP schedule is genuinely easy. Divide, multiply, subtract. If
that were all of it, a free template would be fine and this page would not exist.</p>
<p>What is hard is that a loss job follows a different rule from a profitable one, and a
spreadsheet has to decide which is which on every job, every month, without you remembering to
check. That is the branch below, and it is the thing a seven-column template does not have.</p>""",

"howto_name": "How to build a WIP schedule that reconciles",
"howto_desc": "Five steps to produce a work-in-progress schedule that ties to the income "
              "statement and handles loss jobs correctly.",
"steps": [
 {"h": "Write down what each job is worth now",
  "plain": "Record the original contract plus approved change orders. This is the revised "
           "contract value, and it is what the job will pay you if nothing else changes.",
  "body": """<p>Original contract, plus every approved change order. Not the ones you have asked
  for &mdash; the ones that have been signed. That total is the <strong>revised contract</strong>,
  and everything else on the schedule is measured against it.</p>"""},
 {"h": "Write down two cost estimates, not one",
  "plain": "Record what you thought the job would cost when you signed it, and what you think it "
           "will cost now. Keep both. The gap between them is the early warning.",
  "body": """<p>This is the step people skip, and it is the one that pays for the workbook. Keep
  the estimate <strong>at award</strong> in its own column and never overwrite it. Keep your
  estimate <strong>now</strong> beside it.</p>
  <p>If you only keep one, you have thrown away the only record of what you believed when you
  signed, and you can never see a job slowly getting worse.</p>"""},
 {"h": "Work out how far along each job is",
  "plain": "Divide cost to date by the current total estimated cost. Cap the answer at 100 "
           "percent. A job that has spent more than its estimate is not 108 percent complete.",
  "body": """<p>Cost to date &divide; estimated cost now = percent complete.</p>
  <p><strong>Cap it at 100%.</strong> If a job has spent 108% of its estimate, that does not mean
  it is 108% built. It means the estimate is stale. The workbook caps it and the Fade Analysis tab
  is where that stale estimate shows up.</p>"""},
 {"h": "Turn the percent into earned revenue, then check for a loss",
  "plain": "Multiply the revised contract by the percent complete to get earned revenue. Then "
           "check whether estimated cost now exceeds the contract. If it does, recognise the "
           "entire loss immediately rather than a proportion of it.",
  "body": """<p>Revised contract &times; percent complete = <strong>earned revenue</strong>.
  Earned revenue &minus; cost to date = gross profit.</p>
  <p>Then the test that matters: is estimated cost now greater than the revised contract? If yes,
  this job is in a loss position, and the full loss goes in this period. The workbook applies that
  automatically and counts the loss jobs at the top of the schedule so you cannot miss one.</p>"""},
 {"h": "Make it tie to your profit and loss statement",
  "plain": "Add up revenue and cost across all jobs for the period and compare the totals to the "
           "income statement. If they do not match within a dollar, the schedule is not finished.",
  "body": """<p>A WIP that produces plausible numbers and does not reconcile is worth nothing. The
  Tie-Out tab compares period revenue and period cost against your P&amp;L and
  <strong>refuses to print &ldquo;reconciled&rdquo; unless both variances are under $1</strong>. If
  they are not, it names the three usual causes rather than leaving you to hunt.</p>"""},
],

"inside_intro": """<p>Eight tabs. You type into two of them. The sample data is a realistic
twelve-job contractor &mdash; $55.2M of revised contracts, $30.3M earned, $24.9M of backlog &mdash;
so you can see every tab working before you put your own jobs in.</p>""",
"tabs": {
 "Start Here": "What to fill in, in what order, and how to import the file into Google Sheets.",
 "Contracts": "Your job list. Contract value, change orders, both cost estimates, cost to date, "
              "billed to date. This is the tab you type into.",
 "WIP Schedule": "The schedule itself. Percent complete, earned revenue, gross profit, and the "
                 "over-billed and under-billed split for every job.",
 "Roll-Forward": "This month against last month, so you can see what actually moved rather than "
                 "just where things stand.",
 "Fade Analysis": "Compares the gross profit you expected at award with what you expect now, job "
                  "by job. This is where a job going quietly wrong becomes visible.",
 "Tie-Out": "Checks the schedule against your income statement and refuses to say reconciled if "
            "either variance is over $1.",
 "Bonding": "Working capital and equity, and the indicative multiples a surety looks at.",
 "How It Works": "Every formula on the schedule, written out and explained.",
},
"shot_tab": "WIP Schedule",
"shot_alt": "The WIP Schedule tab showing twelve construction jobs with percent complete, earned "
            "revenue, over-billed and under-billed columns",
"shot_note": "Harbor Point Parking Deck is the loss job — its gross profit shows the full "
             "&minus;$115,000, and the panel on the right counts it.",

"includes": [
 "One .xlsx file, eight tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "Twelve jobs of realistic sample data so you can see it working before you touch it",
 "Loss jobs handled correctly and counted for you",
 "A tie-out that will not lie to you about reconciling",
 "Free lifetime updates",
],
"fine": "No subscription, no account, no macros.",

"math_h": "The arithmetic, written out",
"math": """<p>Five lines. Written out so you can check the workbook rather than trust it.</p>
<pre><code>percent complete   = MIN(1, cost to date / estimated cost now)
earned revenue     = revised contract * percent complete
gross profit       = earned revenue - cost to date
over-billed        = MAX(0, billed to date - earned revenue)
under-billed       = MAX(0, earned revenue - billed to date)</code></pre>
<p>And the rule that is not in that list, because it is a condition rather than a formula:</p>
<pre><code>if estimated cost now &gt; revised contract:
    gross profit = revised contract - estimated cost now     # the FULL loss, now</code></pre>
<p>Two details worth naming. <strong>Over-billed and under-billed are never netted</strong> at job
level &mdash; they are two different lines on a balance sheet, one a liability and one an asset, so
every job shows a figure in one column and a zero in the other. And <strong>percent complete is
capped</strong>, which is the <code>MIN(1, &hellip;)</code> above.</p>""",

"proof": """<p>I do not trust a spreadsheet because it looks right. Every workbook in this line has
a checker next to it that reimplements the whole thing from scratch in Python, recalculates the
real file in LibreOffice, and compares the two. For this one it also asserts eight
<em>identities</em> &mdash; things that must be true of any correct WIP, and that would be false of
a broken one:</p>
<ul>
<li>Period revenue across all jobs equals income-statement revenue</li>
<li>Period cost equals cost of revenue</li>
<li>Total over-billings minus under-billings equals total billed minus total earned</li>
<li>No job is both over-billed and under-billed</li>
<li>Every loss job carries its full estimated loss</li>
<li>No job exceeds 100% complete</li>
<li>Earned plus backlog equals the revised contract, per job and in total</li>
<li>There is real fade in the sample data &mdash; a fade analysis with nothing fading is untested</li>
</ul>
<p><strong>Last run: 0 numeric mismatches, 0 property failures, 0 formula errors.</strong> The
sample portfolio fades 2.5 points, from 17.33% gross margin at award to 14.81% now, across 8 of the
12 jobs &mdash; enough to trip the workbook's systematic-fade verdict, which is the point of
shipping data that is not tidy.</p>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "Loss jobs", "Ties to the P&L", "Fade analysis"],
    [["This workbook", ("$119", "good"), ("Full loss, automatically", "good"),
      ("Yes, refuses to fake it", "good"), ("Yes", "good")],
     ["A free seven-column template", ("$0", ""), ("Prorated — wrong", "bad"),
      ("No", "bad"), ("No", "bad")],
     ["Construction accounting software", "$200&ndash;$600 / month",
      ("Correct", "good"), ("Yes", "good"), ("Usually", "good")],
     ["Your accountant builds it", "$1,500&ndash;$5,000 once",
      ("Correct", "good"), ("Yes", "good"), ("If you ask", "")]],
),

"faq": [
 ("What is a WIP schedule in simple terms?",
  "It is a table that works out how much of each job you have actually earned so far, based on "
  "how much of the expected cost you have spent. It also shows whether you have invoiced more "
  "than you have earned, or less."),
 ("Why does a loss job get treated differently?",
  "Because a loss is not something you earn gradually. As soon as you can see that a job will "
  "cost more than it pays, that whole loss is a fact you already know, so accounting rules say "
  "you report all of it now. Profit is different: you only earn that as you do the work."),
 ("Does this reproduce a specific accounting form?",
  "No. It produces the figures a WIP schedule needs, in the layout a surety and a bank expect to "
  "see. It is not a facsimile of any copyrighted form."),
 ("Will it work in Google Sheets?",
  "Yes. Upload the .xlsx to Google Drive and open it with Google Sheets. Every formula in this "
  "workbook uses ordinary functions, so nothing is lost in the conversion."),
 ("Can I use it on a Mac without Excel?",
  "Yes. Apple Numbers opens the .xlsx directly, and LibreOffice Calc is free and opens it too. "
  "LibreOffice is what I use to recalculate the file when I check the maths."),
 ("How many jobs does it handle?",
  "It ships sized for a contractor running a couple of dozen jobs at once, with twelve filled in "
  "as an example. You add rows the normal way; the formulas copy down."),
 ("Do I need to know accounting to use it?",
  "You need to know your own job costs. The workbook explains every rule it applies on the How It "
  "Works tab, in the same plain terms as this page."),
 ("What are the bonding multiples?",
  "Indicative planning figures — roughly 10 times working capital for a single job and 20 times "
  "in aggregate. They are labelled as indicative everywhere they appear. Your surety sets your "
  "real capacity, not a spreadsheet."),
],
"related": [
 ("progress-billing-schedule-of-values", "Progress billing and schedule of values — the invoice side of the same jobs"),
 ("construction-cash-flow-forecast", "Construction cash flow forecast — when the money actually arrives"),
 ("equipment-cost-per-hour", "Equipment cost per hour — what the iron costs you, standing still or working"),
],
},

# --------------------------------------------------------------------------- #
{
"key": "recipe-costing-menu-engineering",
"slug": "recipe-costing-menu-engineering",
"group": "Food and hospitality",
"category": "Restaurant costing",
"pill": "Workbook",
"card_title": "Recipe costing and menu engineering",
"card_blurb": "Yield-adjusted plate costs, sub-recipes, food cost percentage and the "
              "Star/Plowhorse/Puzzle/Dog menu matrix.",

"title": "Recipe Costing Spreadsheet — Plate Cost, Yield and Menu Matrix",
"description": "Cost a plate properly using yield-adjusted ingredient costs, then sort the menu "
               "into stars, plowhorses, puzzles and dogs. Excel and Google Sheets.",
"h1": "how much does that dish actually cost you?",
"lead": "Most costing sheets take the price on the invoice and treat it as the cost of what lands "
        "on the plate. It never is. Once you account for what gets trimmed away, some dishes turn "
        "out to cost a third more than you thought &mdash; and they are usually the popular ones.",
"chips": ["12 plate recipes", "Menu matrix"],
"keywords": ["recipe costing spreadsheet", "food cost calculator excel",
             "plate cost template", "menu engineering matrix", "yield percentage food cost",
             "restaurant food cost percentage", "menu costing google sheets"],

"short_answer": """<p>To cost a dish properly you need three numbers per ingredient: what you paid,
how much of it is actually usable after trimming, and how much of that usable amount goes on the
plate. Skip the middle one and every dish involving something you peel, trim or bone comes out too
cheap.</p>
<p>This workbook does that calculation for every ingredient, builds it up through sub-recipes into
plate costs, and then sorts your menu into four groups by how popular and how profitable each dish
is &mdash; so you know which to protect, which to reprice and which to cut.</p>""",

"problem_h": "The carrot problem",
"problem": """<p>You buy a kilo of carrots for $2. You peel them and cut the ends off. About 800
grams is left.</p>
<p>So the carrot you actually cook with did not cost $2 a kilo. It cost <strong>$2.50</strong> a
kilo, because you paid for 1000 grams and can only use 800. That extra 25% is real money and it
never appears on any invoice.</p>
<p>Now do that for a whole beef short rib, where you might lose 40% to bone and trim. Or a whole
fish. Or herbs. The dishes with the most trimming are usually the ones you charge most for, so the
error lands exactly where it hurts.</p>
<p>Most free costing sheets have a column for what you paid and a column for how much you use.
They do not have a column for <strong>how much survives</strong>. Without it, every one of those
dishes is undercosted, and the food cost percentage you report to yourself is fiction.</p>""",

"cost_h": "What the missing column does to one dish",
"cost_intro": """<p>Take a plate using 200g of trimmed carrot, bought at $2.00 a kilo with a 80%
usable yield. Here is the same dish costed with and without the yield step.</p>""",
"cost_table": table(
    "200g of prepared carrot on the plate",
    ["", "Cost per usable kg#", "Cost on the plate#", "What it does to your menu"],
    [["With yield accounted for", ("$2.50", "good"), ("$0.50", "good"),
      "The real number. Price from here."],
     ["Invoice price used directly", ("$2.00", "bad"), ("$0.40", "bad"),
      "20% light on this ingredient alone."]],
    foot=["Understated by", ("$0.50/kg", "bad"), ("$0.10", "bad"),
          "On every plate, every service"]),
"cost_after": """<p>Ten cents a plate. Two hundred covers a week. That is one ingredient on one
dish, and it is roughly $1,000 a year of margin you believed you had and did not. A plate has ten
or fifteen ingredients.</p>""",

"why_h": "Why costing and menu design are the same job",
"why": """<p>Getting plate cost right is only worth doing if you then <em>do</em> something with
it. That something is menu engineering, and it is simpler than it sounds: every dish is either
popular or not, and either profitable or not. Two questions, four possible answers.</p>
<p>Each of those four has one obvious action, and they are completely different actions. The
danger is discounting a Star or leaving a Dog on the menu for years because nobody ever put the two
numbers side by side.</p>""",

"howto_name": "How to cost a plate and read your menu",
"howto_desc": "Five steps from an invoice price to knowing which dishes to protect, reprice or "
              "cut.",
"steps": [
 {"h": "List what you buy and what you pay",
  "plain": "Enter each ingredient with its pack size and purchase price, so the sheet can work "
           "out a price per gram or per millilitre.",
  "body": """<p>Pack size and price as they appear on the invoice. The workbook converts to a
  common unit for you, which is where a lot of hand-built sheets quietly go wrong &mdash; mixing
  price-per-kilo with grams-per-portion and losing a factor of a thousand.</p>"""},
 {"h": "Add the yield percentage",
  "plain": "For each ingredient, record what percentage is still usable after peeling, trimming "
           "or boning. This converts purchase price into cost per usable unit.",
  "body": """<p>This is the column that does the work. Weigh it once: buy it, prep it as you
  normally would, weigh what is left. Whole vegetables tend to land between 70% and 90%; bone-in
  meat and whole fish go a lot lower. Anything you use straight from the packet is 100%.</p>
  <p>Cost per usable unit = purchase price &divide; yield. Everything downstream uses that number,
  never the invoice price.</p>"""},
 {"h": "Build your preps once, use them everywhere",
  "plain": "Cost sauces, stocks and other preparations as sub-recipes, then use them as "
           "ingredients in the dishes that contain them.",
  "body": """<p>Your demi-glace is not an ingredient you buy, it is one you make. Cost it once as
  a sub-recipe and every dish that uses it picks up the right cost. Change the price of one thing
  in it and every affected plate updates.</p>"""},
 {"h": "Cost the plate and set the price",
  "plain": "Add up the ingredient costs for the dish to get plate cost, then compare against the "
           "selling price to get food cost percentage and contribution margin.",
  "body": """<p>Plate cost against menu price gives you two figures, and they answer different
  questions. <strong>Food cost percentage</strong> tells you whether the dish is priced sensibly.
  <strong>Contribution margin</strong> &mdash; price minus cost, in money &mdash; tells you what
  the dish actually contributes when someone orders it.</p>
  <p>A dish can look bad on percentage and be excellent on margin. The Price Finder tab works
  backwards: tell it the food cost percentage you want and it gives you the price.</p>"""},
 {"h": "Sort the menu into four groups",
  "plain": "Compare each dish on popularity and contribution margin against the menu average to "
           "classify it as a star, plowhorse, puzzle or dog, then act on the classification.",
  "body": """<p>Above average on both is a <strong>Star</strong> &mdash; protect it. Popular but
  thin is a <strong>Plowhorse</strong> &mdash; take cost out or nudge the price. Profitable but
  ignored is a <strong>Puzzle</strong> &mdash; a selling problem, not a kitchen one. Neither is a
  <strong>Dog</strong>. The workbook does the classification from your actual sales mix.</p>"""},
],

"inside_intro": """<p>Eight tabs, seeded with a working bistro so nothing is empty when you open
it. Eight sub-recipes and twelve plated dishes, fully costed.</p>""",
"tabs": {
 "Start Here": "What to fill in and in what order, plus how to import the file into Google Sheets.",
 "Ingredients": "Everything you buy, with pack size, price and the yield percentage that turns "
                "purchase price into cost per usable unit.",
 "Sub-Recipes": "Stocks, sauces and preps costed once, so the dishes that use them stay correct.",
 "Recipes": "The plates. Each one built from ingredients and sub-recipes, giving plate cost.",
 "Menu": "Selling price, food cost percentage and contribution margin for every dish.",
 "Menu Engineering": "Sorts the menu into stars, plowhorses, puzzles and dogs using your sales mix.",
 "Price Finder": "Works backwards — name the food cost percentage you want, get the price.",
 "How It Works": "Every formula, written out, including how yield feeds through the whole chain.",
},
"shot_tab": "Menu Engineering",
"shot_alt": "The Menu Engineering tab classifying each dish as a star, plowhorse, puzzle or dog "
            "based on popularity and contribution margin",
"shot_note": "Each dish is placed against the menu averages, so the classification moves as your "
             "sales mix does.",

"includes": [
 "One .xlsx file, eight tabs, works in Excel, Google Sheets, Numbers and LibreOffice",
 "A fully costed sample bistro — 8 sub-recipes and 12 plates",
 "Yield percentage built into every ingredient, not bolted on",
 "Price Finder — name your target food cost, get the price",
 "Free lifetime updates",
],
"fine": "No subscription, no account, no macros.",

"math_h": "The arithmetic, written out",
"math": """<p>The whole chain is four lines, and the first one is the one that matters.</p>
<pre><code>cost per usable unit = purchase price / pack size / yield %
ingredient cost      = quantity on the plate * cost per usable unit
plate cost           = SUM(ingredient costs) + SUM(sub-recipe portions)
food cost %          = plate cost / selling price
contribution margin  = selling price - plate cost</code></pre>
<p>A sub-recipe is the same calculation one level down: cost the batch, divide by the yield of the
batch, and you have a cost per portion that behaves exactly like an ingredient.</p>
<p>The menu matrix then compares each dish against two averages:</p>
<pre><code>popular    = share of covers &gt;= average share
profitable = contribution margin &gt;= average contribution margin</code></pre>
<p>Note it uses <strong>contribution margin</strong>, not food cost percentage, for the profit
axis. Sorting on percentage pushes you toward cheap dishes with great percentages that make very
little money per cover.</p>""",

"proof": """<p>The whole costing chain is reimplemented from scratch in Python, the real workbook
is recalculated in LibreOffice, and the two are compared to nine decimal places &mdash; every
ingredient's cost per usable unit, every prep, every plate, every contribution margin, every
menu-mix share and every quadrant classification.</p>
<p><strong>Last run: 0 mismatches, 0 property failures, 0 formula errors.</strong></p>
<p>That matters more here than it looks. Yield sits at the bottom of a chain: an ingredient feeds a
sub-recipe, which feeds a plate, which feeds the menu matrix. A rounding error or an inverted
division at the bottom does not announce itself &mdash; it just quietly moves a dish into the wrong
quadrant and you act on it.</p>""",

"versus_h": "Compared with the alternatives",
"versus_table": table(
    "What else you could do instead",
    ["", "Cost#", "Yield column", "Sub-recipes", "Menu matrix"],
    [["This workbook", ("$59", "good"), ("Yes", "good"), ("Yes, two levels", "good"),
      ("Yes", "good")],
     ["A free costing sheet", ("$0", ""), ("Almost never", "bad"), ("Rarely", "bad"),
      ("No", "bad")],
     ["Restaurant costing platform", "$70&ndash;$200 / month", ("Yes", "good"),
      ("Yes", "good"), ("Usually", "good")],
     ["Back of an envelope", ("$0", ""), ("No", "bad"), ("No", "bad"), ("No", "bad")]],
),

"faq": [
 ("What is yield percentage?",
  "The share of what you buy that you can actually cook with, after peeling, trimming or boning. "
  "If a kilo of carrots gives you 800 grams of usable carrot, the yield is 80 percent, and the "
  "real cost is your purchase price divided by 0.8."),
 ("How do I find the yield for an ingredient?",
  "Weigh it. Buy it, prep it the way you normally would, weigh what is left, divide. Do it once "
  "per ingredient and it stays true until your supplier or your prep changes."),
 ("What is the difference between food cost percentage and contribution margin?",
  "Food cost percentage is cost divided by price, and it tells you whether a dish is priced "
  "sensibly. Contribution margin is price minus cost in money, and it tells you what the dish "
  "actually earns when someone orders it. You need both, and the menu matrix uses margin."),
 ("Will it work in Google Sheets?",
  "Yes. Upload the .xlsx to Google Drive and open it with Google Sheets. Nothing in this workbook "
  "is Excel-only."),
 ("Can I use it on a Mac without Excel?",
  "Yes. Apple Numbers opens the file directly, and LibreOffice Calc is free and opens it too."),
 ("How many dishes does it hold?",
  "Twelve plates and eight sub-recipes are filled in as a worked example. You add rows the normal "
  "way and the formulas copy down."),
 ("Does it handle sauces and stocks I make myself?",
  "Yes, that is what the Sub-Recipes tab is for. Cost a batch once and every dish that uses it "
  "picks up the right per-portion cost automatically."),
 ("Do I need to be good at spreadsheets?",
  "No. You type into the Ingredients, Recipes and Menu tabs. Everything else calculates. The How "
  "It Works tab explains each formula if you want to check it."),
],
"related": [
 ("landed-cost-duty-calculator", "Landed cost calculator — what imported goods really cost you"),
 ("construction-wip-schedule", "Construction WIP schedule — the same idea applied to jobs"),
],
},
]

for _p in PRODUCTS_A:
    _p.setdefault("diagram_problem", V[_p["key"]]["problem"])
    _p.setdefault("diagram_fix", V[_p["key"]]["fix"])
