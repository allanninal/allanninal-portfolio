"""Day 120 -- 2026-08-22 -- Utility meter reader."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "utility-meter-reader"
NAME = "Utility meter reader"

SPEC = {
 "slug": SLUG, "date": "2026-08-22", "name": NAME,
 "tagline": ("Turns meter readings into numbers you can actually use -- separating estimated "
             "bills from real ones, watching what is still running at three in the morning, and "
             "adjusting gas for the weather so two winters can be compared at all."),
 "lede": ("A small system that collects meter readings, works out which of them are estimates, "
          "measures the overnight baseload that reveals what is left on, normalises gas against "
          "the weather, and checks whether the changes anybody made actually saved anything. "
          "Seven posts on the same system, one diagram at a time, with a cost breakdown and an "
          "engineering reference at the end."),
 "keywords": ["energy monitoring", "utilities", "baseload", "degree days", "cost reduction",
              "serverless"],
 "icons": ["gauge", "chart", "search"],
 "faq": [
  ("What is a utility meter reader?",
   "A small serverless system that collects electricity, gas and water readings, distinguishes "
   "estimates from actual readings, and produces findings about what is consuming energy and "
   "whether changes worked."),
  ("Why do estimated bills matter so much?",
   "Because an estimate followed by a real reading produces a catch-up that looks like a "
   "consumption spike in the month it lands, which sends people looking for a problem that "
   "happened months earlier."),
  ("What is baseload?",
   "What is being consumed when nothing should be running -- typically the small hours. It is the "
   "single most informative number in the data and usually the cheapest thing to reduce."),
  ("Why does gas need weather data?",
   "Because gas consumption is dominated by how cold it was. Comparing this January to last "
   "January without adjusting for temperature compares two winters, not two buildings."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "utility-meter-reader-on-aws",
 "title": "A utility meter reader on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Collects meter readings, separates estimates from actuals, measures baseload, and "
          "checks whether savings were real. AWS, about $2 a month."),
 "og": ("The most informative number in a building's energy data is what it uses at three in the "
        "morning, and almost nobody looks at it."),
 "abstract": ("The whole system on one page -- collect, normalise, compare &mdash; and the two "
              "adjustments without which none of the numbers mean anything."),
 "lede": ("The electricity bill jumps forty per cent in March and somebody spends a fortnight "
          "looking for what changed. Nothing changed in March. The previous four bills were "
          "estimates and this one was a real reading, so March is carrying the difference for "
          "four months of under-estimation. This post walks through a small system that would "
          "have said so in a sentence."),
 "tags": ["energy monitoring", "utilities", "baseload", "degree days", "cost reduction",
          "serverless"],
 "takeaways": [
  "Estimated readings must be marked and never compared against actual ones.",
  "Overnight baseload is the most useful single number and the cheapest to reduce.",
  "Gas consumption has to be weather-normalised before any comparison means anything.",
  "A saving is not real until it has been verified against the meter.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Meters and bills", "sub": ["half-hourly, or", "monthly estimates"],
       "icon": "gauge"},
      {"title": "The weather", "sub": ["degree days"], "icon": "clock"},
      {"title": "Whoever pays it", "sub": ["wants findings,", "not a dashboard"], "icon": "person"}],
    "inside": [
      {"title": "Collector", "sub": ["reading, or", "estimate -- marked"], "icon": "database"},
      {"title": "Normaliser", "sub": ["weather, and", "days in the period"], "icon": "filter"},
      {"title": "Findings", "sub": ["baseload, drift,", "did it work?"], "icon": "search"}],
    "edges": [{"from": 0, "to": 0, "label": "readings"},
              {"from": 1, "to": 1, "label": "temperature"},
              {"from": 2, "to": 2, "label": "a few specific things", "up": True}],
    "note": "Both adjustments in the middle box are required before any comparison is honest."}),
   "Three things outside the account, three pieces inside it. The middle box is unglamorous and "
   "is what separates a real comparison from an apparent one.",
   "System: meter readings collected, normalised and turned into findings",
   "Three boxes across the top sit outside the AWS account. On the left, Meters and bills, "
   "providing half-hourly data or monthly estimates. In the middle, The weather, providing degree "
   "days. On the right, Whoever pays it, who wants findings rather than a dashboard. Each "
   "connects by an arrow to the AWS account container below. Readings flow down into the account. "
   "Temperature feeds in. A few specific things go back out. Inside the AWS account are three "
   "components in a row. On the left, the Collector, marking each value as a reading or an "
   "estimate. In the middle, the Normaliser, adjusting for weather and for days in the period. On "
   "the right, Findings, covering baseload, drift and whether a change worked. A note at the "
   "bottom says both adjustments in the middle box are required before any comparison is honest."),
  ("h3", "Two adjustments, or nothing works"),
  ("p", "The first is estimates. A bill labelled as an estimate is a guess by the supplier based "
        "on history, and the moment a real reading arrives the difference lands in one period. "
        "Comparing periods without knowing which were estimated produces spikes and troughs that "
        "correspond to nothing that happened in the building."),
  ("p", "The second is time and weather. February has fewer days than January, and last January "
        "may have been three degrees colder than this one. Comparing raw totals across periods "
        "measures the calendar and the weather considerably more than it measures the building."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The collector.</strong> Takes readings from whatever source exists and records "
   "whether each is actual or estimated. Part 2.",
   "<strong>The normaliser.</strong> Adjusts for days in the period and, for gas, for how cold it "
   "was. Part 4.",
   "<strong>The findings.</strong> Baseload, drift, and whether a change actually saved anything. "
   "Parts 3 and 5.",
  ]),
  ("h2", "One finding, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Half-hourly data", "sub": ["electricity"], "icon": "gauge"},
      {"title": "03:00 average", "sub": ["18 kW, every night"], "icon": "clock"},
      {"title": "Should be ~4 kW", "sub": ["fridges and servers"], "icon": "question"},
      {"title": "Traced", "sub": ["compressor, 24h timer"], "icon": "search"},
      {"title": "Verified", "sub": ["baseload now 5 kW"], "icon": "check"}],
    "title": "ONE FINDING, END TO END",
    "note": "Fourteen kilowatts, every hour of every night, for about four years."}),
   "The same system as one line. The last box is the one most energy projects skip, and without "
   "it nobody knows whether the fix worked.",
   "One baseload finding from detection to verified saving",
   "A horizontal row of five boxes joined by arrows. Half-hourly data for electricity. Three "
   "o'clock average: eighteen kilowatts, every night. Should be about four kilowatts, for fridges "
   "and servers. Traced: a compressor on a twenty-four hour timer. Verified: baseload now five "
   "kilowatts. A note says fourteen kilowatts, every hour of every night, for about four years."),
  ("h2", "In plain words"),
  ("p", "Half-hourly electricity data shows the site drawing eighteen kilowatts at three in the "
        "morning, every night, including weekends and the Christmas shutdown. Somebody who knows "
        "the building says it should be about four: refrigeration, a couple of servers, emergency "
        "lighting."),
  ("p", "Fourteen kilowatts of unexplained overnight draw is roughly a hundred and twenty "
        "thousand kilowatt-hours a year, which is a substantial bill. Tracing it takes an "
        "afternoon with a clamp meter and finds an air compressor whose timer was set to "
        "twenty-four hours during a maintenance visit in 2022 and never set back."),
  ("p", "The timer is changed, and the crucial step is the last one: two weeks later the "
        "overnight baseload is measured again and is five kilowatts. The saving is verified "
        "against the meter rather than calculated from a specification, which is the difference "
        "between a real saving and one that exists in a spreadsheet."),
  ("callout", "Design rules that shaped every decision", [
   "Mark every value as actual or estimated, and never compare across the two.",
   "Normalise for days in the period, always, and for weather where it applies.",
   "Baseload is measured over a window of nights, not from one night.",
   "A saving is unverified until the meter shows it.",
   "Never act on the building automatically. Produce findings.",
   "Say which meter and which period every number came from.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Energy management at small scale suffers from a specific problem: the data is available "
        "and nobody has time to look at it, so the analysis happens once, in a burst, when a bill "
        "is alarming. That is exactly the wrong moment, because the alarming bill is usually a "
        "billing artefact and the real waste is a steady drip nobody has ever noticed."),
  ("p", "So the design does the small number of things that reliably find money &mdash; baseload, "
        "weather-normalised comparison, verification &mdash; on a schedule, and stays quiet the "
        "rest of the time. There is no dashboard, because a dashboard is a thing nobody opens."),
  ("p", "The next four posts walk through each piece: how a reading becomes a usable number, what "
        "the overnight baseload tells you, why gas needs the weather, and how a finding becomes a "
        "verified saving. One diagram per post, a cost breakdown, and an engineering reference at "
        "the end."),
 ],
},
{
 "slug": "how-a-reading-becomes-a-number-you-can-use",
 "title": "How a reading becomes a number you can use",
 "nav": "How readings work",
 "read": 5, "words": 740,
 "desc": ("Estimates and the catch-up bill, resolution and what it lets you see, and the meter "
          "that was replaced."),
 "og": ("An estimated bill is a guess. Four of them followed by a real reading produce a spike "
        "that corresponds to nothing at all."),
 "abstract": ("How estimated readings distort a series, why resolution determines what can be "
              "found, how meter changes and resets are handled, and normalising for period "
              "length."),
 "lede": ("Meter data looks like the most trustworthy data a business has, and it arrives with "
          "several ways of being quietly wrong that produce confident-looking charts of nothing."),
 "tags": ["energy monitoring", "meter readings", "estimates", "data quality", "utilities",
          "serverless"],
 "takeaways": [
  "Every value is actual, estimated or derived, and the three are never mixed in a comparison.",
  "A catch-up after estimates should be spread back, and shown as spread.",
  "Half-hourly data finds baseload; monthly data cannot.",
  "Meter replacements reset the register and need explicit handling.",
  "Always divide by days in the period before comparing anything.",
 ],
 "blocks": [
  ("h2", "The catch-up"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Nov (est)", "parts": [("billed", 4200), ("catchup", 0)]},
      {"label": "Dec (est)", "parts": [("billed", 4200), ("catchup", 0)]},
      {"label": "Jan (est)", "parts": [("billed", 4300), ("catchup", 0)]},
      {"label": "Feb (est)", "parts": [("billed", 4300), ("catchup", 0)]},
      {"label": "Mar (actual)", "parts": [("billed", 4400), ("catchup", 5600)]}],
    "series": [("billed", "Consumption billed, kWh", "#7AA116"),
               ("catchup", "Catch-up from four under-estimates", "#DD344C")],
    "unit": "",
    "note": "Nothing happened in March. The red band belongs to November through February."}),
   "Five months of billing where four were estimated. The March bar is the one somebody "
   "investigates and it is the only one that is correct.",
   "Four estimated months followed by a catch-up on the actual reading",
   "A stacked bar chart with five bars in kilowatt-hours. Two series: consumption billed in "
   "green, and catch-up from four under-estimates in red. November, December, January and "
   "February are each estimated at between four thousand two hundred and four thousand three "
   "hundred with no catch-up. March, an actual reading, shows four thousand four hundred billed "
   "plus a catch-up of five thousand six hundred. A note says nothing happened in March, and the "
   "red band belongs to November through February."),
  ("p", "The system's job here is not to fix the billing; it is to stop the chart lying. When an "
        "actual reading follows estimates, the difference is spread back across the estimated "
        "periods proportionally, and every one of those periods is marked as derived rather than "
        "measured."),
  ("p", "That produces a series that is approximately right everywhere instead of exactly wrong "
        "in one place, and it stops the recurring investigation into a month where nothing "
        "happened."),
  ("h3", "Three kinds of value"),
  ("p", "Actual is a real meter reading. Estimated is the supplier's guess. Derived is what the "
        "system computed by spreading a catch-up back. All three are useful and mixing them "
        "silently is what produces nonsense."),
  ("p", "The rule that follows: any comparison between periods states how much of each period was "
        "actual. \"January against last January\" is a different claim when one is fully metered "
        "and the other is eighty per cent estimate, and saying so takes one line."),
  ("h2", "Resolution decides what you can find"),
  ("table", ["Data available", "What you can see", "What you cannot"], [
   ["Annual bill", "Whether it went up", "Anything actionable"],
   ["Monthly bill", "Seasonal shape, big changes", "Baseload, schedules, spikes"],
   ["Daily reading", "Weekends against weekdays, shutdowns", "What runs overnight"],
   ["Half-hourly", "Baseload, start-up, timers, peak demand", "Which circuit it is"],
   ["Sub-metered", "Which circuit or area", "Which individual machine"],
  ]),
  ("p", "The jump from monthly to half-hourly is where almost all the value is, and for "
        "electricity it is usually available already: most commercial supplies are half-hourly "
        "metered and the data can be requested from the supplier or the data collector at no "
        "cost."),
  ("p", "That request is frequently the single highest-value action in an energy project, and it "
        "is an email. A business paying for half-hourly metering and looking at monthly bills is "
        "the common case."),
  ("h2", "Meters that change"),
  ("fig", ("chain", {
    "entry": {"title": "A new reading", "sub": ["from a meter"], "icon": "gauge"},
    "steps": [
      {"title": "Lower than the last?", "sub": ["registers go up"], "icon": "branch",
       "exit": {"title": "Meter change or rollover", "sub": ["never a negative period"],
                "icon": "alarm", "label": "yes"}},
      {"title": "Same meter serial?", "sub": ["it is on the bill"], "icon": "branch",
       "exit": {"title": "New meter", "sub": ["close the old series"], "icon": "doc",
                "label": "no"}},
      {"title": "Period length", "sub": ["days between readings"], "icon": "clock"},
      {"title": "Per-day figure", "sub": ["the only comparable one"], "icon": "counter"},
      {"title": "Stored with its type", "sub": ["actual, estimated, derived"], "icon": "database"}],
    "note": "A meter change mid-year is the most common cause of an impossible-looking series."}),
   "How a raw reading becomes a comparable number. The first two gates catch the discontinuities "
   "that otherwise produce enormous or negative consumption.",
   "How a meter reading is validated and normalised",
   "A vertical chain of five steps entered by a box labelled A new reading from a meter. Step one "
   "asks whether it is lower than the last, since registers go up; if so it exits to Meter change "
   "or rollover, and never records a negative period. Step two asks whether the meter serial is "
   "the same, which appears on the bill; if not it exits to New meter, closing the old series. "
   "Step three computes the period length in days between readings. Step four computes a per-day "
   "figure, the only comparable one. Step five stores it with its type: actual, estimated or "
   "derived. A note says a meter change mid-year is the most common cause of an "
   "impossible-looking series."),
  ("h3", "Per day, always"),
  ("p", "The cheapest correction available and the most frequently omitted. A 28-day February "
        "against a 31-day January is ten per cent lower before anything else is considered, and a "
        "quarterly bill covering 89 days against one covering 93 is four per cent."),
  ("p", "Everything downstream works in units per day, and the totals are reconstructed only for "
        "reporting the actual bill. It removes an entire class of false movement at no cost."),
  ("p", "Next: what is running when nothing should be."),
 ],
},
{
 "slug": "what-the-overnight-baseload-tells-you",
 "title": "What the overnight baseload tells you",
 "nav": "The overnight baseload",
 "read": 5, "words": 740,
 "desc": ("The number nobody looks at, what it should be, how to trace what it is, and the water "
          "version which is a leak."),
 "og": ("An empty building drawing eighteen kilowatts is paying for something. It is usually one "
        "thing and it has usually been running for years."),
 "abstract": ("Why the small hours are the most informative period, how to work out what baseload "
              "should be, how it is traced, and why a non-zero water baseload is always a leak."),
 "lede": ("The single most useful thing to know about a building's energy use is what it consumes "
          "when nobody is in it, because everything drawing power at three in the morning is "
          "drawing it for a reason somebody chose or forgot."),
 "tags": ["baseload", "energy monitoring", "leaks", "waste", "utilities", "serverless"],
 "takeaways": [
  "Take the minimum sustained draw across several nights, not one night's average.",
  "Work out what it should be from what genuinely must run.",
  "The gap is almost always one or two things, not many small ones.",
  "Weekends and shutdowns are the best evidence available.",
  "A water baseload above zero is a leak, with no exceptions worth arguing about.",
 ],
 "blocks": [
  ("h2", "Measuring it properly"),
  ("fig", ("chain", {
    "entry": {"title": "Half-hourly data", "sub": ["several weeks"], "icon": "gauge"},
    "steps": [
      {"title": "Take the quiet hours", "sub": ["02:00 to 04:00"], "icon": "clock"},
      {"title": "Across many nights", "sub": ["not one"], "icon": "counter",
       "side": {"title": "Why", "sub": ["one night can be odd"], "icon": "search"}},
      {"title": "The minimum sustained", "sub": ["not the average"], "icon": "filter"},
      {"title": "Compare to shutdown", "sub": ["Christmas, bank holidays"], "icon": "chart"},
      {"title": "The baseload", "sub": ["and what it should be"], "icon": "question"}],
    "note": "A shutdown week is a free experiment somebody already ran for you."}),
   "How baseload is measured. The fourth box is the highest-value comparison available and it "
   "costs nothing because the data already exists.",
   "How overnight baseload is measured from half-hourly data",
   "A vertical chain of five steps entered by a box labelled Half-hourly data over several weeks. "
   "Step one takes the quiet hours, two in the morning to four. Step two looks across many nights "
   "rather than one, with a side box explaining that one night can be odd. Step three takes the "
   "minimum sustained draw rather than the average. Step four compares against shutdown periods "
   "such as Christmas and bank holidays. Step five produces the baseload and the question of what "
   "it should be. A note says a shutdown week is a free experiment somebody already ran for you."),
  ("h3", "The shutdown week"),
  ("p", "A building closed for a week over Christmas provides the closest thing to a controlled "
        "experiment available: everything discretionary is off, and whatever is still drawing "
        "power is either necessary or forgotten."),
  ("p", "Comparing the shutdown baseload to the ordinary overnight baseload separates the two "
        "categories immediately. Anything drawing power on both is permanent and worth "
        "understanding; anything drawing power on ordinary nights and not during shutdown is "
        "something that gets switched off when somebody remembers."),
  ("h2", "What it should be"),
  ("callout", "Working out the expected baseload", [
   "<strong>List what genuinely must run:</strong> refrigeration, servers, emergency lighting, "
   "security, frost protection.",
   "<strong>Estimate each</strong> from its rating and duty cycle. Rough is fine; the gaps that "
   "matter are large.",
   "<strong>Add ten per cent</strong> for standby loads across the building.",
   "<strong>Compare to measured.</strong> A measured figure within a third of expected is "
   "unremarkable.",
   "<strong>A measured figure at twice expected</strong> is one or two specific things, not a "
   "hundred small ones.",
   "<strong>This is a half-hour exercise</strong> with somebody who knows the building, done "
   "once.",
  ]),
  ("p", "The fifth line is the practically important one and it surprises people. Large "
        "unexplained baseloads are almost never the accumulation of many small oversights; they "
        "are a compressor, a chiller, a pump, an air handling unit, or a heater, running when it "
        "should not be."),
  ("p", "Which makes the tracing exercise tractable. One afternoon, a clamp meter, and switching "
        "things off one at a time is usually enough, and the alternative &mdash; a full survey "
        "&mdash; is rarely necessary."),
  ("h2", "The shapes worth recognising"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Expected", "parts": [("need", 4)]},
      {"label": "Always-on excess", "parts": [("need", 4), ("waste", 14)]},
      {"label": "Timer wrong", "parts": [("need", 4), ("waste", 9)]},
      {"label": "After the fix", "parts": [("need", 5)]}],
    "series": [("need", "Genuinely needed, kW", "#7AA116"),
               ("waste", "Unexplained overnight draw, kW", "#DD344C")],
    "unit": "",
    "note": "The fourth bar is measured, two weeks later. Without it, the saving is a claim."}),
   "Baseload before and after a fix. The fourth bar is the verification step from Part 5 and it "
   "is what turns an estimate into a number.",
   "Overnight baseload before and after fixing an always-on load",
   "A stacked bar chart with four bars in kilowatts. Two series: genuinely needed load in green, "
   "and unexplained overnight draw in red. Expected: four kilowatts needed. Always-on excess: "
   "four needed plus fourteen unexplained. Timer wrong: four needed plus nine unexplained. After "
   "the fix: five kilowatts, all needed. A note says the fourth bar is measured two weeks later, "
   "and without it the saving is a claim."),
  ("h3", "Water baseload is a leak"),
  ("p", "For water the analysis is simpler and the conclusion is stronger. A building with nobody "
        "in it should use no water at all, so any sustained overnight flow is a leak, a running "
        "overflow, or a urinal flushing on a timer nobody has adjusted."),
  ("p", "There is no benign explanation for continuous overnight water flow, which makes this the "
        "clearest finding the whole system produces. A small continuous flow &mdash; a trickle "
        "&mdash; adds up to a startling annual volume and is completely invisible on a quarterly "
        "bill."),
  ("h3", "Gas overnight"),
  ("p", "Gas baseload is more nuanced because frost protection and hot water recirculation are "
        "legitimate. The useful comparison is summer nights: a building using meaningful gas "
        "overnight in July has heating running that should not be, or a hot water system with no "
        "time control."),
  ("p", "Next: why the winter comparison needs the weather."),
 ],
},
{
 "slug": "why-gas-needs-the-weather",
 "title": "Why gas needs the weather",
 "nav": "Gas and the weather",
 "read": 5, "words": 720,
 "desc": ("Degree days, comparing two winters honestly, and the fabric change that shows up as a "
          "changed slope."),
 "og": ("Gas use went down twelve per cent. It was a mild winter. Those are the same sentence "
        "until somebody does the arithmetic."),
 "abstract": ("What degree days are and why they work, how a normalised comparison is built, what "
              "a changed relationship between temperature and gas means, and the limits of the "
              "method."),
 "lede": ("Heating fuel consumption is dominated by how cold it was, to the point where a "
          "year-on-year comparison of raw gas use is mostly a comparison of two winters."),
 "tags": ["degree days", "gas", "weather normalisation", "heating", "energy monitoring",
          "serverless"],
 "takeaways": [
  "Degree days measure how much heating the weather demanded.",
  "Gas per degree day is the comparable number; raw gas is not.",
  "A change in the slope means the building or its controls changed.",
  "The intercept is the non-heating gas: hot water and catering.",
  "Free public weather data is good enough; a nearby station is fine.",
 ],
 "blocks": [
  ("h2", "What a degree day is"),
  ("p", "A simple idea: for each day, take how far the average outdoor temperature fell below a "
        "base &mdash; usually around fifteen and a half degrees, the point at which a typical "
        "building needs heating &mdash; and add it up. A day averaging ten degrees contributes "
        "five and a half degree days; a day averaging eighteen contributes none."),
  ("p", "Sum those over a month and you have a single number describing how much heating the "
        "weather demanded. Divide the month's gas by it and you have a figure that can be "
        "compared across months and years, because the weather has been divided out."),
  ("h2", "Two winters"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Last Jan, raw", "parts": [("gas", 48000)]},
      {"label": "This Jan, raw", "parts": [("gas", 42200)]},
      {"label": "Last Jan, per DD", "parts": [("norm", 132)]},
      {"label": "This Jan, per DD", "parts": [("norm", 141)]}],
    "series": [("gas", "Gas used, kWh", "#8C4FFF"),
               ("norm", "kWh per degree day", "#DD344C")],
    "unit": "",
    "note": "Raw use fell 12%. Adjusted for weather it rose 7%. The mild winter hid a problem."}),
   "The same two months measured two ways. The raw comparison says the building improved; the "
   "normalised one says it got worse and the weather was doing the work.",
   "Two Januaries compared raw and normalised for degree days",
   "A bar chart with four bars. Two series: gas used in kilowatt-hours in purple, and kilowatt-"
   "hours per degree day in red. Last January raw: forty-eight thousand kilowatt-hours. This "
   "January raw: forty-two thousand two hundred. Last January per degree day: one hundred and "
   "thirty-two. This January per degree day: one hundred and forty-one. A note says raw use fell "
   "twelve per cent while adjusted for weather it rose seven per cent, and the mild winter hid a "
   "problem."),
  ("p", "This is the most common way an energy problem goes unnoticed for a year. A mild winter "
        "produces a lower bill, everybody is pleased, and a heating system that has developed a "
        "fault or a control that has been overridden is invisible until a cold winter arrives and "
        "the bill is startling."),
  ("p", "The normalised figure catches it in the mild year, which is the only useful time to "
        "catch it."),
  ("h2", "The slope and the intercept"),
  ("fig", ("chain", {
    "entry": {"title": "Monthly gas and degree days", "sub": ["a year or more"], "icon": "chart"},
    "steps": [
      {"title": "Plot one against the other", "sub": ["it is close to a line"], "icon": "search"},
      {"title": "The slope", "sub": ["kWh per degree day"], "icon": "gauge",
       "side": {"title": "This is", "sub": ["heat loss and controls"], "icon": "doc"}},
      {"title": "The intercept", "sub": ["gas at zero degree days"], "icon": "counter",
       "side": {"title": "This is", "sub": ["hot water, catering"], "icon": "doc"}},
      {"title": "Compare to last year", "sub": ["both numbers"], "icon": "clock"},
      {"title": "Which one moved?", "sub": ["they mean different things"], "icon": "branch"}],
    "note": "A higher intercept is a hot water problem. A steeper slope is a heating one."}),
   "The two numbers that come out of a degree-day analysis and what each one means. Separating "
   "them tells you which system to look at.",
   "How the slope and intercept of a gas against degree days line are read",
   "A vertical chain of five steps entered by a box labelled Monthly gas and degree days over a "
   "year or more. Step one plots one against the other, noting it is close to a line. Step two "
   "identifies the slope, kilowatt-hours per degree day, with a side box saying this is heat loss "
   "and controls. Step three identifies the intercept, gas at zero degree days, with a side box "
   "saying this is hot water and catering. Step four compares both numbers to last year. Step "
   "five asks which one moved, since they mean different things. A note says a higher intercept "
   "is a hot water problem and a steeper slope is a heating one."),
  ("h3", "Reading the two"),
  ("p", "A steeper slope means the building is losing more heat per degree of cold, or the "
        "heating is running harder than it needs to. Insulation does not get worse quickly, so a "
        "steepening slope usually means controls: a thermostat moved, a compensation curve "
        "changed, a valve stuck open."),
  ("p", "A higher intercept means more gas is being used regardless of the weather, which is hot "
        "water, catering, or heating that runs in summer. That is a different investigation and "
        "often an easier one."),
  ("h3", "Where to get the weather"),
  ("p", "Public weather data from a station within a reasonable distance is more than good "
        "enough. The method is not sensitive to a degree of difference, and the alternative "
        "&mdash; an on-site weather station &mdash; adds precision to the smallest source of "
        "error in the analysis."),
  ("h2", "Limits worth stating"),
  ("callout", "Where degree days stop working", [
   "<strong>Buildings with high internal gains</strong> &mdash; a busy kitchen, a server room "
   "&mdash; heat themselves, and the base temperature is lower than the standard one.",
   "<strong>Cooling</strong> needs cooling degree days, which are a separate calculation and "
   "usually matter for electricity rather than gas.",
   "<strong>Occupancy changes</strong> break the comparison entirely. A building at half capacity "
   "is a different building.",
   "<strong>Process gas</strong> &mdash; an oven, a furnace &mdash; has nothing to do with the "
   "weather and should be sub-metered out if it is significant.",
   "<strong>A year is the minimum</strong> for a useful slope. Three months of data produces a "
   "line and no confidence.",
   "<strong>Say the base temperature</strong> used, on every report. It is an assumption and "
   "people should be able to argue with it.",
  ]),
  ("p", "The occupancy point is worth watching for, because it is the one that produces the "
        "wrong conclusion most convincingly. A normalised figure that improved after half the "
        "staff started working from home has measured the occupancy change, and reporting it as "
        "an efficiency improvement is a mistake that will be repeated at the next comparison."),
  ("p", "Next: turning a finding into a saving that is real."),
 ],
},
{
 "slug": "how-a-finding-becomes-a-saving",
 "title": "How a finding becomes a saving",
 "nav": "How savings get verified",
 "read": 5, "words": 710,
 "desc": ("Measuring before and after, the fix that did not work, and why claimed savings from "
          "specifications should be ignored."),
 "og": ("Half of implemented energy savings do not show up on the meter. Verifying is cheap and "
        "almost nobody does it."),
 "abstract": ("Why savings must be verified against the meter, how the before-and-after "
              "measurement is set up, the common reasons a fix does not work, and how savings are "
              "reported."),
 "lede": ("The gap between an energy saving on paper and one on the meter is large, "
          "well-documented, and mostly closed by the cheapest possible intervention: measuring "
          "afterwards."),
 "tags": ["energy monitoring", "verification", "savings", "measurement", "utilities",
          "serverless"],
 "takeaways": [
  "Measure for two weeks before and two weeks after, at the same resolution.",
  "Compare like periods: same days of week, weather-normalised where relevant.",
  "A fix that shows nothing on the meter did not work, whatever the specification says.",
  "Common causes: it was reversed, it was partial, or something else grew.",
  "Report verified savings only, and report the unverified ones as unverified.",
 ],
 "blocks": [
  ("h2", "Before and after"),
  ("fig", ("chain", {
    "entry": {"title": "A change is planned", "sub": ["a timer, a control, a unit"],
              "icon": "gear"},
    "steps": [
      {"title": "Measure before", "sub": ["two weeks, same resolution"], "icon": "gauge"},
      {"title": "Record the date", "sub": ["exactly when it changed"], "icon": "clock"},
      {"title": "Wait two weeks", "sub": ["settle, then measure"], "icon": "clock"},
      {"title": "Like for like?", "sub": ["days, weather, occupancy"], "icon": "branch",
       "exit": {"title": "Adjust or wait", "sub": ["a bank holiday ruins a fortnight"],
                "icon": "alarm", "label": "no"}},
      {"title": "Saving, measured", "sub": ["or: it did not work"], "icon": "check"}],
    "note": "The second box is the one that gets forgotten and it makes the rest impossible."}),
   "The verification sequence. Recording the exact change date is trivial and is the step whose "
   "absence makes a before-and-after comparison unanswerable.",
   "How an energy saving is verified against the meter",
   "A vertical chain of five steps entered by a box labelled A change is planned, whether a "
   "timer, a control or a unit. Step one measures before, for two weeks at the same resolution. "
   "Step two records the date, exactly when it changed. Step three waits two weeks to settle, "
   "then measures. Step four asks whether the comparison is like for like on days, weather and "
   "occupancy; if not it exits to Adjust or wait, noting that a bank holiday ruins a fortnight. "
   "Step five produces a measured saving, or the conclusion that it did not work. A note says the "
   "second box is the one that gets forgotten and it makes the rest impossible."),
  ("h3", "The date matters more than it seems"),
  ("p", "\"We changed the timers some time in April\" makes verification impossible, because the "
        "before and after periods cannot be defined. A recorded date, to the day, costs nothing "
        "and is the difference between a measurable change and an anecdote."),
  ("p", "It is worth keeping a simple log of every change made to the building's energy-consuming "
        "equipment, with dates. Over a couple of years that log explains most of the movement in "
        "the data and it is the first thing anybody wants when a number moves unexpectedly."),
  ("h2", "When it did not work"),
  ("callout", "Why a fix shows nothing on the meter", [
   "<strong>It was reversed.</strong> Somebody found the compressor off, assumed it was a fault, "
   "and put the timer back. This is the most common one.",
   "<strong>It was partial.</strong> Three of five units were changed, and the specification "
   "assumed five.",
   "<strong>Something else grew</strong> at the same time and absorbed the saving.",
   "<strong>The load moved.</strong> Turning off a heater means a different heater runs longer.",
   "<strong>The saving was never there.</strong> The specification was a manufacturer's figure "
   "under ideal conditions.",
   "<strong>All five are worth knowing about,</strong> and none of them are visible without "
   "measuring.",
  ]),
  ("p", "The first is worth designing against. A change that somebody can reverse without knowing "
        "why it was made will eventually be reversed, so a label on the equipment saying what was "
        "changed, when and who to ask is a genuinely effective intervention."),
  ("h2", "Reporting savings honestly"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Claimed on paper", "parts": [("saving", 14200)]},
      {"label": "Verified on meter", "parts": [("saving", 8600)]},
      {"label": "Unverified", "parts": [("unver", 5600)]}],
    "series": [("saving", "Verified annual saving, £", "#7AA116"),
               ("unver", "Claimed but not visible on the meter, £", "#7D8CA3")],
    "unit": "£",
    "note": "The grey bar is not a failure. It is the part nobody had measured."}),
   "A year of energy work reported honestly. The gap between claimed and verified is normal and "
   "reporting it is what makes the verified figure believable.",
   "Claimed against verified annual energy savings",
   "A bar chart with three bars in pounds. Two series: verified annual saving in green, and "
   "claimed but not visible on the meter in grey. Claimed on paper: fourteen thousand two "
   "hundred. Verified on meter: eight thousand six hundred. Unverified: five thousand six "
   "hundred. A note says the grey bar is not a failure, it is the part nobody had measured."),
  ("p", "Reporting the gap rather than hiding it has a useful effect: it makes the verified "
        "number credible. An energy report claiming fourteen thousand pounds of savings against a "
        "bill that did not move by fourteen thousand pounds is a report nobody believes the "
        "next time."),
  ("h3", "The annual reconciliation"),
  ("p", "Once a year, compare the sum of verified savings against the actual change in the "
        "weather-normalised bill. They will not match exactly and the difference is informative: "
        "consistently larger actual reductions mean something good is happening that nobody has "
        "attributed, and consistently smaller means savings are being counted that are not there."),
  ("p", "That reconciliation is the honest close of the loop, and it is the number worth putting "
        "at the top of an annual energy report: not what was claimed, but what the meter says the "
        "building did, adjusted for the weather."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="meter",
 volumes=[(4, "4 meters"), (15, "15 meters"), (60, "60 meters")],
 read_each=0.0,
 msgs_each=0.9,
 lede=("There is no model in this system and the data is small: a half-hourly meter produces "
       "about seventeen hundred readings a month. Fifteen meters is several sites or one site "
       "with sub-metering. Here is where each cent goes."),
 takeaway_extra=("The whole bill is effectively fixed; half-hourly data across sixty meters is "
                 "still a trivial volume."),
 risks=[
  "<strong>Storing one item per half-hourly reading.</strong> Batch a day per meter into one "
  "item and the write count falls by nearly fifty times.",
  "<strong>Fetching weather data per reading.</strong> Degree days are one value per day per "
  "location. Fetch once daily and cache.",
  "<strong>Building a live dashboard.</strong> Not a cost problem so much as a waste: nobody "
  "opens it, and the findings are what matter.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. Messaging is a monthly "
                "findings summary per meter group, not per reading."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="um",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the reading types, and how baseload is computed."),
 outside=[
  {"title": "Meter data", "sub": ["half-hourly feed,", "or bills"], "icon": "gauge"},
  {"title": "Weather data", "sub": ["a public source"], "icon": "clock"},
  {"title": "A monthly summary", "sub": ["findings, not charts"], "icon": "doc"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["feed drop,", "daily and monthly"], "icon": "storage"},
  {"title": "Lambda x3", "sub": ["ingest, normalise, analyse"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["readings, meters"], "icon": "database"}],
 note="us-east-1. One account. Readings batched by day per meter; estimates never silently mixed.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Meter data, arriving as a half-hourly feed "
  "or as bills. Weather data from a public source. And A monthly summary of findings rather than "
  "charts. Inside the account, three groups. S3 receiving the feed drop alongside EventBridge "
  "running daily and monthly passes. Three Lambda functions named ingest, normalise and analyse. "
  "And two DynamoDB tables named readings and meters. A note gives the region as us-east-1, one "
  "account, and states that readings are batched by day per meter and estimates are never "
  "silently mixed."),
 functions=[
  ["<code>um-ingest</code>", "S3 put, or API for manual readings",
   "Validates against the previous register; detects meter changes; marks the reading type",
   "120s / 1024&nbsp;MB"],
  ["<code>um-normalise</code>", "EventBridge, daily",
   "Fetches degree days; computes per-day and per-degree-day figures; spreads catch-ups back",
   "60s / 1024&nbsp;MB"],
  ["<code>um-analyse</code>", "EventBridge, monthly",
   "Computes baseload, slope and intercept, verifies open savings, sends the findings summary",
   "300s / 1024&nbsp;MB"]],
 roles=[
  ["<code>um-ingest-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:PutItem</code>, <code>dynamodb:Query</code>",
   "The feed prefix; readings; read-only on meters"],
  ["<code>um-normalise-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>", "Both tables"],
  ["<code>um-analyse-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Both tables; one verified identity"]],
 tables=[
  ("Table: readings",
   "PK   meter_id          S\n"
   "SK   date              S   2026-08-22 -- one item per meter per day\n"
   "     halfhourly        L   48 values, or null for billed meters\n"
   "     total             N   the day's consumption\n"
   "     kind              S   actual | estimated | derived\n"
   "     derived_from      S   set when a catch-up was spread back\n"
   "     degree_days       N   for the site's weather location\n"
   "     per_day           N   total / days in period, for billed meters\n"
   "     baseload_kw       N   minimum sustained draw, 02:00-04:00\n\n"
   "One item per meter per day rather than per reading. Forty-eight values\n"
   "in a list is one write instead of forty-eight."),
  ("Table: meters",
   "PK   meter_id          S\n"
   "     serial            S   changes when the meter is replaced\n"
   "     utility           S   electricity | gas | water\n"
   "     resolution        S   halfhourly | daily | billed\n"
   "     expected_baseload N   from the half-hour exercise in Part 3\n"
   "     base_temp_c       N   15.5 by default; stated on every report\n"
   "     slope             N   kWh per degree day, current\n"
   "     intercept         N   non-heating gas\n"
   "     changes           L   [{date, what, by}] -- the change log\n\n"
   "`changes` is the log that makes before-and-after verification possible.\n"
   "Without a date to the day, no saving can be measured.")],
 inbound=[
  "<strong>Half-hourly data comes from the supplier or data collector</strong>, usually as a "
  "daily file. Requesting it is often the single highest-value action available.",
  "<strong>Billed meters are entered manually</strong> or parsed from the bill, always with the "
  "estimate flag from the bill itself.",
  "<strong>Degree days are computed daily</strong> from a public weather source for each site's "
  "location, cached, and never re-fetched per reading.",
  "<strong>A meter serial change closes the old series</strong> and opens a new one. The two are "
  "never concatenated into a single register."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Baseload is a minimum, normalisation is "
  "division, and the slope is a straight line fit.",
  "<strong>The tempting use</strong> is disaggregating loads from the half-hourly curve. It is "
  "genuinely interesting and an afternoon with a clamp meter answers it better and cheaply.",
  "<strong>A defensible use</strong> is reading a scanned bill to extract the reading, the "
  "estimate flag and the period.",
  "<strong>The wrong use</strong> is generating explanations for movements. A movement with an "
  "invented explanation stops anybody looking for the real one.",
  "<strong>The cost page assumes none</strong>, which is why the bill is fixed."],
 gotchas=[
  "Mark every value actual, estimated or derived, and never compare across the three without "
  "saying so. This single field prevents the most common false alarm.",
  "Divide by days in the period before any comparison. A 28-day month against a 31-day month is "
  "ten per cent lower for no reason.",
  "Take the minimum sustained draw for baseload, not the average. An average over the small hours "
  "includes whatever cycled on during them.",
  "Keep a change log with exact dates. Verification is impossible without knowing the day "
  "something changed.",
  "State the base temperature on every degree-day report. It is an assumption and a building with "
  "high internal gains needs a different one."],
))
