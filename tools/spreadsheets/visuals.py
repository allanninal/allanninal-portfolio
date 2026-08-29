#!/usr/bin/env python3
"""Per-product diagrams.

Geometry comes from the shared engine in tools/fieldnotes/diagrams.py; palette.py
re-skins it green first. Nothing here writes SVG coordinates by hand — the boxes
are described as text and the engine lays them out, which is why a long label
cannot silently overflow its box on one page in twenty-one.

Two shapes, used the same way on every page:
  chain()  the sequence a number travels through, with fail_at on the step that
           goes wrong. This is "the problem".
  branch() one input sorted into outcomes. This is "what the workbook does
           instead".
"""
from palette import branch, chain

V = {}

V["construction-wip-schedule-workbook"] = {
    "problem": chain(
        "wip-p", "How a job's cost turns into revenue on the books, and where it breaks",
        "The cost-to-cost method. Every step is arithmetic until the last one, "
        "where a loss job needs a different rule and most templates do not have it.",
        [("Cost to date", "what you have spent"),
         ("Percent complete", "cost ÷ estimated cost"),
         ("Earned revenue", "contract × percent"),
         ("Gross profit", "earned − cost")],
        fail_at=2),
    "fix": branch(
        "wip-f", "A job is sorted by whether it is profitable or in a loss position",
        "The one rule the seven-column templates miss. A profitable job earns "
        "profit gradually; a loss job takes the whole loss the moment you see it.",
        ("Each job, every month", "profitable, or heading for a loss?"),
        [("Profitable job", "recognise profit in proportion to progress", "good"),
         ("Loss job", "recognise the FULL estimated loss now, not a share of it", "bad")]),
}

V["recipe-costing-menu-engineering"] = {
    "problem": chain(
        "rec-p", "How an ingredient's purchase price becomes a plate cost",
        "Buying price is not plate cost. The step in the middle is the one most "
        "costing sheets leave out, and it is the one that decides whether your "
        "food cost figure is real.",
        [("Purchase price", "what the invoice says"),
         ("Usable yield", "what survives trimming"),
         ("Cost per usable unit", "the real cost"),
         ("Plate cost", "everything on the dish")],
        fail_at=1),
    "fix": branch(
        "rec-f", "Every dish is sorted into one of four menu-engineering quadrants",
        "Once plate cost is right, each dish falls into one of four boxes — and "
        "each box has a different, obvious action.",
        ("Every dish on the menu", "how popular, how profitable?"),
        [("Star — popular and profitable", "protect it, never discount it", "good"),
         ("Plowhorse — popular, thin margin", "cut the cost or nudge the price", "plain"),
         ("Puzzle — profitable, nobody orders it", "move it, rename it, sell it", "plain"),
         ("Dog — neither", "cut it, or rebuild it from scratch", "bad")]),
}


# --------------------------------------------------------------------------- #
# The five bid calculators share a shape — the same two mistakes in the same two
# places — so the diagrams are generated per trade with that trade's own real
# burdened and break-even rates from trades/README.md.
# --------------------------------------------------------------------------- #

def _bid_diagrams(key, uid, trade, burdened, breakeven):
    return {
        "problem": chain(
            uid + "-p", f"How a {trade.lower()} bid is built, and the step that goes wrong",
            f"Everything is fine until the last step. Adding a percentage on top is a "
            f"markup, and a markup always produces a smaller margin than the one you "
            f"asked for.",
            [("Wage", "what you pay the crew"),
             ("Burdened hour", f"${burdened} with taxes and insurance"),
             ("Plus overhead", f"${breakeven} to break even"),
             ("Add a markup", "gives a smaller margin than you wanted")],
            fail_at=2),
        "fix": branch(
            uid + "-f", "Two ways to add margin to the same cost",
            "Same cost, same intended margin, two different arithmetic operations. "
            "Only one of them gives you the margin you asked for.",
            ("A job costing $10,000", "you want a 30% margin"),
            [("Divide by (1 - 0.30) = $14,286", "margin actually earned: 30.0%", "good"),
             ("Multiply by 1.30 = $13,000", "margin actually earned: 23.1%", "bad")]),
    }


for _key, _uid, _trade, _b, _be in [
    ("electrical-bid-calculator", "elec", "Electrical", "45.20", "87.84"),
    ("hvac-bid-calculator", "hvac", "HVAC", "44.33", "90.16"),
    ("roofing-bid-calculator", "roof", "Roofing", "48.98", "95.95"),
    ("concrete-bid-calculator", "conc", "Concrete", "42.54", "81.11"),
    ("landscaping-bid-calculator", "land", "Landscaping", "37.66", "66.60"),
]:
    V[_key] = _bid_diagrams(_key, _uid, _trade, _b, _be)


V["progress-billing-schedule-of-values"] = {
    "problem": chain(
        "bill-p", "How a payment application is built, and where retainage is deducted twice",
        "The last step is a subtraction, and what you subtract decides whether you get "
        "paid what you earned. Subtract the cheque and retainage comes off twice.",
        [("Work completed", "plus stored materials"),
         ("Less retainage", "what the customer holds back"),
         ("Total earned to date", "net of retainage"),
         ("Less previous", "the cheque? or prior earned-less-retainage?")],
        fail_at=2),
    "fix": branch(
        "bill-f", "Two candidates for the 'less previous certificates' line",
        "They give the same answer on a simple line, which is why the wrong one "
        "survives for years. They diverge the moment retainage or stored materials move.",
        ("Line 6 on last month's application", "which number goes here?"),
        [("Prior earned less prior retainage", "correct - derived, never typed", "good"),
         ("The cheque you actually received", "deducts retainage a second time", "bad")]),
}

V["construction-cash-flow-forecast"] = {
    "problem": chain(
        "cash-p", "The gap between paying for work and being paid for it",
        "Four steps, and money leaves at step one but does not come back until step "
        "four. Overlap several jobs and those gaps stack on top of each other.",
        [("You pay the crew", "this month"),
         ("You pay materials", "next month"),
         ("You invoice", "end of the month"),
         ("They pay you", "a month or two later, less retainage")],
        fail_at=2,
        loop=(3, 0, "the gap you have to fund")),
    "fix": branch(
        "cash-f", "What the model does when a month would close below the cash floor",
        "The facility is a hard ceiling on purpose. A model that borrows without limit "
        "hides the exact problem you built it to find.",
        ("A month closes short", "how much do you draw?"),
        [("Draw enough to hold the floor", "and repay any surplus above it", "good"),
         ("Facility exhausted", "balance pins, cash drops below the floor - the signal", "bad")]),
}

V["equipment-fleet-cost-per-hour"] = {
    "problem": chain(
        "fleet-p", "Why fewer hours make a machine cost more per hour",
        "The annual cost is the same either way. Only the number you divide it by "
        "changes, and that number is how much you actually used the machine.",
        [("$40,000 a year", "fixed, whether it moves or not"),
         ("Worked 2,000 hours", "$20 per hour"),
         ("Worked 500 hours", "$80 per hour"),
         ("Parked", "still depreciating, still insured")],
        fail_at=2),
    "fix": branch(
        "fleet-f", "Each machine is sorted by whether it clears its break-even hours",
        "Break-even is where owning and renting cost exactly the same. The workbook "
        "checks that identity holds to $0.0000 before it gives a verdict.",
        ("Each machine, per year", "above or below break-even hours?"),
        [("Above break-even", "owning is cheaper - keep it", "good"),
         ("Below break-even", "renting is cheaper - 3 of 8 machines, $43,010 a year", "bad")]),
}

V["certified-payroll-davis-bacon"] = {
    "problem": chain(
        "pay-p", "How a benefit plan becomes an hourly fringe credit",
        "The plan cost is a fact. The only choice is what you divide it by, and one "
        "of the two options is not a number of hours the plan paid for.",
        [("Annual plan cost", "$20,900 for the year"),
         ("Divide by hours", "but which hours?"),
         ("Hourly credit", "claimed against the fringe you owe"),
         ("Cash fringe", "the remainder, paid to the worker")],
        fail_at=1),
    "fix": branch(
        "pay-f", "The two divisors, and what each one produces",
        "The plan covers the whole year, so the whole year is the divisor. Anything "
        "narrower claims credit for money you did not spend.",
        ("$20,900 of benefits", "2,080 total hours, 760 on public work"),
        [("Divide by 2,080 total hours", "$10.05 per hour - correct", "good"),
         ("Divide by 760 Davis-Bacon hours", "$27.50 per hour - $9,653 of back wages", "bad")]),
}


# --------------------------------------------------------------------------- #
# Underwriting: one engine, five asset classes. Each page gets its own opening
# figures from underwriting/README.md, so the diagram is generated per asset.
# --------------------------------------------------------------------------- #

def _deal_diagrams(uid, lower, dscr, irr):
    return {
        "problem": chain(
            uid + "-p", f"How money flows through a {lower} deal to your return",
            "Every arrow is a subtraction, and every input feeding them is a guess. "
            "One set of guesses gives you one answer, which is the least useful "
            "answer there is.",
            [("Revenue", "what it brings in"),
             ("Net operating income", "less running costs"),
             ("Cash flow", f"less debt service - DSCR {dscr}"),
             ("Your return", f"levered IRR {irr}")],
            fail_at=2),
        "fix": branch(
            uid + "-f", "Reading a sensitivity grid instead of a single number",
            "Twenty-five real ten-year runs, two assumptions moving at once. The "
            "question is not which cell is best - it is how much of the grid you "
            "can live with.",
            ("The 5x5 sensitivity grid", "two assumptions, 25 outcomes"),
            [("Most of the grid clears your hurdle", "the deal survives being wrong", "good"),
             ("Only the centre clears it", "you are betting on your own assumptions", "bad")]),
    }


for _key, _uid, _low, _d, _i in [
    ("self-storage-underwriting-model", "stor", "self-storage", "1.60", "7.92%"),
    ("car-wash-underwriting-model", "wash", "car wash", "1.50", "10.71%"),
    ("rv-park-underwriting-model", "rvp", "RV park", "1.76", "7.02%"),
    ("mobile-home-park-underwriting-model", "mhp", "mobile home park", "1.58", "10.83%"),
    ("laundromat-underwriting-model", "laun", "laundromat", "2.06", "51.60%"),
]:
    V[_key] = _deal_diagrams(_uid, _low, _d, _i)


V["landed-cost-duty-calculator"] = {
    "problem": chain(
        "land-p", "How an invoice price becomes a true per-unit landed cost",
        "The supplier invoice is the first step, not the answer. Everything after "
        "it is your cost and appears on none of their paperwork.",
        [("Invoice price", "what the supplier charges"),
         ("Customs value", "FOB, or CIF with freight in it"),
         ("Duty and fees", "tariffs stacked on that value"),
         ("Landed per unit", "plus freight, split across SKUs")],
        fail_at=1),
    "fix": branch(
        "land-f", "What each of the two settings moves",
        "One changes the total you pay. The other changes which product carries "
        "it. Confusing them is how a dense cheap SKU ends up subsidised.",
        ("Two settings", "duty basis, and freight allocation"),
        [("FOB vs CIF changes the TOTAL", "+$2,513 duty, +17% on the sample", "bad"),
         ("Allocation changes the SPLIT", "SKU cost moves 4%, total identical", "good")]),
}

V["spc-control-chart-capability-workbook"] = {
    "problem": chain(
        "spc-p", "Where control limits come from, and where they must not come from",
        "The limits describe the process, so they have to be computed from the "
        "process. A limit drawn from a tolerance cannot detect a change inside "
        "that tolerance.",
        [("Measure the process", "subgroups over time"),
         ("Compute sigma", "from the data, not the spec"),
         ("Control limits", "plus and minus three sigma"),
         ("A rule fires", "something changed - go and look")],
        fail_at=1),
    "fix": branch(
        "spc-f", "The two sigmas, and which statistics use which",
        "Two different standard deviations, kept apart on purpose. The gap "
        "between the pairs is the drift, expressed as a number.",
        ("Two sigmas from the same data", "within-subgroup, and overall"),
        [("Within (R-bar/d2) -> Cp, Cpk", "1.832 / 1.695 - what it could do", "good"),
         ("Overall (STDEV) -> Pp, Ppk", "1.505 / 1.393 - what it actually did", "plain"),
         ("The 0.303 gap", "is the instability, not a rounding error", "bad")]),
}

V["design-of-experiments-workbook"] = {
    "problem": chain(
        "doe-p", "Why testing one factor at a time misses interactions",
        "Each factor is only ever measured at whatever the others happened to be "
        "set to. If the effect depends on that setting, the experiment cannot "
        "see it.",
        [("Four suspected factors", "temperature, time, amount, rest"),
         ("Change one, hold the rest", "at some fixed setting"),
         ("Measure the difference", "at that setting only"),
         ("Conclude it does not matter", "when it does, at other settings")],
        fail_at=2),
    "fix": branch(
        "doe-f", "How Lenth's method separates real effects from noise",
        "An unreplicated design has no spare degrees of freedom for an error "
        "term, so the noise is estimated from the small effects themselves - in "
        "two passes, so big effects cannot hide themselves.",
        ("15 estimated effects", "which are real?"),
        [("5 exceed the margin of error", "all 5 genuinely real - flagged", "good"),
         ("10 sit inside it", "all 10 genuinely inert - not flagged", "plain")]),
}

V["monte-carlo-simulation-workbook"] = {
    "problem": chain(
        "mc-p", "Why adding up best guesses understates the risk",
        "Twelve ranges collapsed into twelve points, then added. The result is "
        "roughly the middle, and tells you nothing about how far the far end is.",
        [("Twelve uncertain costs", "each really a range"),
         ("Take a best guess", "one number each"),
         ("Add them up", "highs and lows cancel"),
         ("One confident total", "with no tail, and no warning")],
        fail_at=2),
    "fix": branch(
        "mc-f", "Independent inputs against correlated ones",
        "This is the workbook's central claim, so the checker asserts it rather "
        "than assuming it: correlated inputs pile up where independent ones "
        "cancel.",
        ("1,000 trials, 12 inputs", "do they move together?"),
        [("Independent", "highs cancel lows - narrow, and wrong", "plain"),
         ("Correlated, as in reality", "1.59-1.64x wider - about 60% more spread", "bad")]),
}

V["federal-grant-budget-mtdc"] = {
    "problem": chain(
        "gra-p", "How a grant budget reaches its indirect recovery",
        "Three of these four steps are additions and one is a subtraction. The "
        "subtraction is the one every template gets wrong.",
        [("Total direct cost", "$1,757,415 on the sample"),
         ("Subtract exclusions", "equipment, subaward overage, and more"),
         ("MTDC base", "$1,370,415 - 78.0% of direct"),
         ("Apply the rate", "then cap it")],
        fail_at=1),
    "fix": branch(
        "gra-f", "How the subaward cap is consumed across the period of performance",
        "The cap covers the whole award, consumed in the order the money goes "
        "out. Applying it per year counts it once per year.",
        ("Each subaward", "how much counts toward MTDC?"),
        [("Per period of performance", "cap filled in spend order - correct", "good"),
         ("Per year", "counts the cap 3 times - $17,100 over-claimed", "bad")]),
}
