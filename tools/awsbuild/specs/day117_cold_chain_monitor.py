"""Day 117 -- 2026-08-19 -- Cold chain monitor."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "cold-chain-monitor"
NAME = "Cold chain monitor"

SPEC = {
 "slug": SLUG, "date": "2026-08-19", "name": NAME,
 "tagline": ("Watches chilled and frozen storage, tells a brief door-open spike apart from a "
             "failing compressor, treats missing data as a breach rather than as good news, and "
             "never decides on its own what happens to the stock."),
 "lede": ("A small system that records temperature properly, distinguishes an excursion from a "
          "breach, catches the sensor that has quietly stopped working, and produces a "
          "tamper-evident record. It deliberately does not decide whether stock is safe, because "
          "that decision belongs to a person and needs to be signed. Seven posts on the same "
          "system, one diagram at a time, with a cost breakdown and an engineering reference at "
          "the end."),
 "keywords": ["cold chain", "temperature monitoring", "food safety", "sensors", "compliance",
              "serverless"],
 "icons": ["gauge", "alarm", "shield"],
 "faq": [
  ("What is a cold chain monitor?",
   "A small serverless system that records temperature readings from chilled and frozen storage, "
   "detects genuine breaches, catches failing sensors, and keeps a tamper-evident record for "
   "inspection."),
  ("What is the difference between an excursion and a breach?",
   "An excursion is a temperature going out of range, which happens whenever a door opens. A "
   "breach is an excursion that lasted long enough to matter, and the post on this covers how "
   "that line is drawn."),
  ("What happens if the sensor stops sending data?",
   "It is treated as a breach, not as everything being fine. Missing data is the most common "
   "failure and the most commonly mishandled."),
  ("Does it decide whether stock is safe?",
   "No. It presents the evidence and a person decides and signs. That separation is deliberate "
   "and is the subject of part five."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "cold-chain-monitor-on-aws",
 "title": "A cold chain monitor on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Records temperatures, separates excursions from breaches, catches failing sensors, and "
          "leaves the stock decision to a person. AWS, about $3 a month."),
 "og": ("No data is not good data. A cold chain system that goes quiet when the sensor dies is "
        "reporting success by not looking."),
 "abstract": ("The whole system on one page -- record, judge, escalate &mdash; and the fail-closed "
              "rule that separates a useful monitor from a decorative one."),
 "lede": ("A freezer alarm goes off at ten past three in the morning. Somebody silences it from "
          "their phone because the last four were door-open spikes during the evening restock. "
          "This one was the compressor. By seven the contents are at minus four and the question "
          "is what to do with eleven thousand pounds of stock and no record of exactly what "
          "happened when."),
 "tags": ["cold chain", "temperature monitoring", "food safety", "sensors", "compliance",
          "serverless"],
 "takeaways": [
  "An excursion is normal; a breach is an excursion with duration. Alarm on the second.",
  "Missing data is a breach. Silence must never read as compliance.",
  "A sensor that has failed often looks better than one that is working.",
  "The system never decides whether stock is safe. It produces the evidence.",
  "Designed on AWS for about $3 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Sensors", "sub": ["in each unit,", "reporting or not"], "icon": "gauge"},
      {"title": "The unit's rules", "sub": ["range, and how long", "out of it is allowed"],
       "icon": "doc"},
      {"title": "Whoever is on call", "sub": ["and whoever signs"], "icon": "person"}],
    "inside": [
      {"title": "Recorder", "sub": ["readings, and", "the gaps between"], "icon": "database"},
      {"title": "Judge", "sub": ["excursion, or", "breach?"], "icon": "filter"},
      {"title": "Escalator", "sub": ["until somebody", "acknowledges"], "icon": "alarm"}],
    "edges": [{"from": 0, "to": 0, "label": "readings, or silence"},
              {"from": 1, "to": 1, "label": "limits per unit"},
              {"from": 2, "to": 2, "label": "an alarm that does not stop", "up": True}],
    "note": "The recorder's second job -- noticing gaps -- is the one that catches dead sensors."}),
   "Three things outside the account, three pieces inside it. The escalator on the right does not "
   "give up, which is a deliberate departure from how most alerting works.",
   "System: temperature readings recorded, judged and escalated",
   "Three boxes across the top sit outside the AWS account. On the left, Sensors in each unit, "
   "reporting or not. In the middle, The unit's rules: its range, and how long out of it is "
   "allowed. On the right, Whoever is on call, and whoever signs. Each connects by an arrow to "
   "the AWS account container below. Readings, or silence, flow down into the account. Limits per "
   "unit feed in. An alarm that does not stop goes back out. Inside the AWS account are three "
   "components in a row. On the left, the Recorder, capturing readings and the gaps between them. "
   "In the middle, the Judge, deciding excursion or breach. On the right, the Escalator, "
   "continuing until somebody acknowledges. A note at the bottom says the recorder's second job, "
   "noticing gaps, is the one that catches dead sensors."),
  ("h3", "The rule that shapes everything"),
  ("p", "Fail closed. A sensor that has stopped reporting is treated exactly as if it were "
        "reporting a breach, because from a food safety point of view those two situations are "
        "identical: nobody knows what the temperature is."),
  ("p", "This sounds obvious and is the opposite of how most monitoring is built. The default "
        "behaviour of almost every alerting system is to alarm on bad values and stay silent on "
        "no values, which means the most complete failure produces the calmest dashboard."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The recorder.</strong> Takes readings at a fixed interval and treats a missed "
   "interval as an event in its own right. Part 2.",
   "<strong>The judge.</strong> Distinguishes a door-open excursion from a genuine breach, using "
   "duration rather than a single reading. Part 3.",
   "<strong>The escalator.</strong> Keeps going until a person acknowledges, and catches the "
   "sensor that is lying. Parts 4 and 5.",
  ]),
  ("h2", "One night, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "18:40 door open", "sub": ["+2C for 4 min"], "icon": "clock"},
      {"title": "Excursion", "sub": ["logged, no alarm"], "icon": "check"},
      {"title": "02:10 rising", "sub": ["and not returning"], "icon": "gauge"},
      {"title": "02:22 breach", "sub": ["12 min out of range"], "icon": "alarm"},
      {"title": "Escalated", "sub": ["until acknowledged"], "icon": "person"}],
    "title": "ONE NIGHT, END TO END",
    "note": "The first two boxes are why the fourth one gets taken seriously."}),
   "The same night as one line. Not alarming at half past six is what makes the alarm at twenty "
   "past two credible.",
   "One night of temperature monitoring from a door-open spike to a real breach",
   "A horizontal row of five boxes joined by arrows. Eighteen forty, door open: two degrees above "
   "range for four minutes. Excursion: logged, no alarm. Two ten, rising and not returning. Two "
   "twenty-two, breach: twelve minutes out of range. Escalated until acknowledged. A note says "
   "the first two boxes are why the fourth one gets taken seriously."),
  ("h2", "In plain words"),
  ("p", "At twenty to seven in the evening somebody opens the walk-in to restock. The temperature "
        "rises two degrees over four minutes and comes back down. That is an excursion, it is "
        "entirely normal, and it is recorded and not alarmed on."),
  ("p", "At ten past two in the morning the temperature starts rising with nobody near it. Twelve "
        "minutes later it is still out of range and still climbing, which crosses the breach rule "
        "for this unit: out of range for more than ten consecutive minutes."),
  ("p", "The alarm goes to the person on call. It repeats. If it is not acknowledged in fifteen "
        "minutes it goes to a second person, and then to a third, and it does not stop. When "
        "somebody does acknowledge, they get the last six hours of readings on a chart, not just "
        "the current number, because what has been happening matters more than what is happening."),
  ("callout", "Design rules that shaped every decision", [
   "Fail closed. Missing data is a breach.",
   "Alarm on duration out of range, never on a single reading.",
   "Every alarm carries the recent history, not just the current value.",
   "Escalate to a second and third person. An unacknowledged alarm is not handled.",
   "Records are append-only and timestamped at the sensor, for inspection.",
   "The system never says whether stock is safe. A person decides and signs.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Temperature monitoring is a solved problem in the sense that the sensors are cheap and "
        "the arithmetic is trivial, and it fails constantly in practice for reasons that are "
        "entirely about human behaviour: too many false alarms, so alarms get silenced; a sensor "
        "dies and nothing notices; the record turns out to be a spreadsheet somebody filled in "
        "from memory."),
  ("p", "So the design spends its effort on being believed. Not alarming on door openings, "
        "alarming loudly on silence, escalating rather than giving up, and keeping a record that "
        "cannot be quietly adjusted."),
  ("p", "The next four posts walk through each piece: how a reading becomes a record, how an "
        "excursion is told from a breach, how a broken sensor is caught, and who decides what "
        "happens to the stock. One diagram per post, a cost breakdown, and an engineering "
        "reference at the end."),
 ],
},
{
 "slug": "how-a-reading-becomes-a-record",
 "title": "How a reading becomes a record",
 "nav": "How it is recorded",
 "read": 5, "words": 740,
 "desc": ("Sampling intervals, timestamps at the sensor, missing readings as events, and why the "
          "record has to be append-only."),
 "og": ("A gap in the record is data. Storing only the readings that arrived produces a chart "
        "with no holes and no meaning."),
 "abstract": ("How often to sample, why the sensor's own clock matters, how missing readings are "
              "recorded as events, and why the store is append-only."),
 "lede": ("Recording temperature is the part everyone assumes is trivial, and the decisions made "
          "here determine whether the record is any use in an investigation six months later."),
 "tags": ["cold chain", "sensors", "data recording", "compliance", "audit", "serverless"],
 "takeaways": [
  "Sample every few minutes. Hourly readings cannot tell a door opening from a failure.",
  "Timestamp at the sensor and record the arrival time separately.",
  "A missing reading is written as a gap record, not left as an absence.",
  "The store is append-only; corrections are new records with a reason.",
  "Keep readings at full resolution for the period an inspector might ask about.",
 ],
 "blocks": [
  ("h2", "How often"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Every 60 min", "parts": [("useful", 1), ("blind", 59)]},
      {"label": "Every 15 min", "parts": [("useful", 1), ("blind", 14)]},
      {"label": "Every 5 min", "parts": [("useful", 1), ("blind", 4)]},
      {"label": "Every 2 min", "parts": [("useful", 1), ("blind", 1)]}],
    "series": [("useful", "The reading, minutes", "#7AA116"),
               ("blind", "Minutes you cannot see, per reading", "#DD344C")],
    "unit": "",
    "note": "A ten-minute breach rule needs sampling well under ten minutes to be enforceable."}),
   "Four sampling intervals and what each leaves invisible. A breach rule measured in minutes "
   "cannot be applied to readings taken in hours.",
   "How sampling interval determines the blind period between temperature readings",
   "A stacked bar chart with four bars measured in minutes. Two series: the reading itself in "
   "green, and minutes you cannot see per reading in red. Every sixty minutes leaves fifty-nine "
   "minutes blind. Every fifteen minutes leaves fourteen. Every five minutes leaves four. Every "
   "two minutes leaves one. A note says a ten-minute breach rule needs sampling well under ten "
   "minutes to be enforceable."),
  ("p", "Five minutes is a reasonable default for most chilled and frozen storage. It is frequent "
        "enough to make a ten-minute breach rule meaningful, infrequent enough that battery life "
        "and data volume stay sensible, and it captures door openings as the short events they "
        "are rather than as mysterious single spikes."),
  ("p", "Transport is a different case and usually wants longer intervals for battery reasons, "
        "with the trade-off stated explicitly rather than absorbed: at fifteen-minute sampling, a "
        "ten-minute breach rule cannot be enforced and the rule should change to match."),
  ("h3", "Two timestamps"),
  ("p", "The sensor's own clock says when the reading was taken; the arrival time says when it "
        "reached the system. They differ, sometimes by hours when a device has been out of range "
        "and buffers its readings, and conflating them produces a record that says a freezer was "
        "fine at a time when nobody actually knew."),
  ("p", "Both are stored. The chart is drawn on sensor time, because that is when the temperature "
        "was what it was. The alarm logic runs on arrival time, because you cannot alarm on "
        "something you have not received."),
  ("h2", "Gaps are records"),
  ("fig", ("chain", {
    "entry": {"title": "A reading is due", "sub": ["every 5 minutes"], "icon": "clock"},
    "steps": [
      {"title": "Did it arrive?", "sub": ["within the grace period"], "icon": "branch",
       "exit": {"title": "Write a gap record", "sub": ["missing, not absent"], "icon": "question",
                "label": "no"}},
      {"title": "Plausible value?", "sub": ["within the sensor's range"], "icon": "branch",
       "exit": {"title": "Write it, flagged", "sub": ["never discard a reading"], "icon": "alarm",
                "label": "no"}},
      {"title": "Append it", "sub": ["both timestamps"], "icon": "database"},
      {"title": "Gaps accumulating?", "sub": ["3 in a row"], "icon": "branch",
       "exit": {"title": "Treat as a breach", "sub": ["fail closed"], "icon": "shield",
                "label": "yes"}},
      {"title": "Normal", "sub": ["carry on"], "icon": "check"}],
    "note": "A discarded implausible reading is a decision nobody can review later."}),
   "How each expected reading is handled, including the ones that do not arrive. Writing gaps "
   "explicitly is what makes the record answerable.",
   "How a temperature reading, or its absence, becomes a record",
   "A vertical chain of five steps entered by a box labelled A reading is due, every five "
   "minutes. Step one asks whether it arrived within the grace period; if not it exits to Write a "
   "gap record, marking it missing rather than absent. Step two asks whether the value is "
   "plausible, within the sensor's range; if not it exits to Write it, flagged, and never "
   "discards a reading. Step three appends it with both timestamps. Step four asks whether gaps "
   "are accumulating, three in a row; if so it exits to Treat as a breach, failing closed. Step "
   "five records it as normal and carries on. A note says a discarded implausible reading is a "
   "decision nobody can review later."),
  ("h3", "Never discard"),
  ("p", "An implausible reading &mdash; minus two hundred degrees, or a value the sensor cannot "
        "physically produce &mdash; is stored with a flag rather than dropped. It is evidence "
        "about the sensor, and a series of them is the clearest possible sign that a device is "
        "failing."),
  ("p", "Systems that filter these out silently produce clean-looking charts from equipment that "
        "is disintegrating, which is exactly backwards."),
  ("h2", "Append-only"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A reading", "sub": ["written once"], "icon": "database"},
      {"title": "Wrong?", "sub": ["a calibration error"], "icon": "search"},
      {"title": "Never edited", "sub": ["not once"], "icon": "lock"},
      {"title": "A correction record", "sub": ["with a reason and a name"], "icon": "doc"},
      {"title": "Both visible", "sub": ["on the chart and the export"], "icon": "chart"}],
    "title": "WHY NOTHING IS EVER EDITED",
    "note": "A temperature record that can be edited is a temperature record nobody has to believe."}),
   "How corrections work. The original and the correction both survive, which is what makes the "
   "record usable as evidence.",
   "Why temperature records are corrected by addition rather than editing",
   "A horizontal row of five boxes. A reading: written once. Wrong, due to a calibration error. "
   "Never edited, not once. A correction record, with a reason and a name. Both visible on the "
   "chart and in the export. A note says a temperature record that can be edited is a temperature "
   "record nobody has to believe."),
  ("p", "This matters most in the situation it is designed for: an investigation where the "
        "question is what the temperature was and who knew. A store where records can be updated "
        "invites the question of whether they were, and there is no way to answer it after the "
        "fact."),
  ("h3", "How long to keep it"),
  ("p", "At full resolution for at least as long as the goods have shelf life, and in practice "
        "for a year or two, because the question usually arrives long after the event. The data "
        "is tiny &mdash; a few readings per unit per hour &mdash; and the storage cost of keeping "
        "everything is negligible next to the cost of not having it once."),
  ("p", "Next: telling a spike from a failure."),
 ],
},
{
 "slug": "how-an-excursion-is-told-from-a-breach",
 "title": "How an excursion is told from a breach",
 "nav": "Excursion or breach",
 "read": 6, "words": 770,
 "desc": ("Duration rather than a single reading, cumulative time out of range, and the alarm "
          "that gets taken seriously because it is rare."),
 "og": ("Alarm on every door opening and every alarm gets silenced. The rule has to be duration, "
        "not threshold."),
 "abstract": ("Why a single reading out of range means nothing, how duration rules are set, why "
              "cumulative time matters as well as consecutive, and the case for a small number of "
              "loud alarms."),
 "lede": ("Every chilled unit goes out of range several times a day, because people open doors. A "
          "monitoring system that treats each of those as a failure produces an alarm nobody "
          "believes within about a week."),
 "tags": ["cold chain", "alarms", "thresholds", "food safety", "alerting", "serverless"],
 "takeaways": [
  "A single reading out of range is not an event. Duration is.",
  "Consecutive time out of range triggers the alarm; cumulative time triggers a review.",
  "Different units get different rules; a walk-in is not a display fridge.",
  "The alarm carries the last few hours, because trajectory is the diagnosis.",
  "Fewer, louder alarms beat more, softer ones. Every time.",
 ],
 "blocks": [
  ("h2", "Two clocks"),
  ("fig", ("chain", {
    "entry": {"title": "A reading out of range", "sub": ["above or below"], "icon": "gauge"},
    "steps": [
      {"title": "Start the consecutive clock", "sub": ["if not already running"], "icon": "clock"},
      {"title": "Back in range?", "sub": ["next reading"], "icon": "branch",
       "exit": {"title": "Excursion closed", "sub": ["logged, added to cumulative"],
                "icon": "check", "label": "yes"}},
      {"title": "Past the limit?", "sub": ["10 min for this unit"], "icon": "branch",
       "exit": {"title": "Still watching", "sub": ["no alarm yet"], "icon": "search",
                "label": "no"}},
      {"title": "Breach", "sub": ["alarm, and escalate"], "icon": "alarm"},
      {"title": "Cumulative today?", "sub": ["over 45 min?"], "icon": "branch",
       "side": {"title": "A separate rule", "sub": ["many small excursions"], "icon": "counter"},
       "exit": {"title": "Review flag", "sub": ["not an alarm"], "icon": "doc", "label": "yes"}}],
    "note": "Consecutive time wakes somebody up. Cumulative time appears in the morning."}),
   "The two duration rules and their different consequences. Separating them is what lets the "
   "system catch a door left ajar all afternoon without alarming at three in the morning.",
   "How consecutive and cumulative time out of range are judged separately",
   "A vertical chain of five steps entered by a box labelled A reading out of range, above or "
   "below. Step one starts the consecutive clock if it is not already running. Step two asks "
   "whether the next reading is back in range; if so it exits to Excursion closed, logged and "
   "added to the cumulative total. Step three asks whether it is past the limit, ten minutes for "
   "this unit; if not it exits to Still watching, with no alarm yet. Step four declares a breach, "
   "alarms and escalates. Step five asks whether cumulative time today is over forty-five "
   "minutes, drawing on a side box describing it as a separate rule for many small excursions; if "
   "so it exits to a Review flag rather than an alarm. A note says consecutive time wakes somebody "
   "up and cumulative time appears in the morning."),
  ("h3", "Why cumulative matters too"),
  ("p", "A door propped open for two minutes every ten minutes all afternoon never triggers a "
        "consecutive rule and does real damage. It is a common and genuinely bad pattern &mdash; "
        "usually somebody restocking with the door wedged &mdash; and only a cumulative measure "
        "catches it."),
  ("p", "It is a review flag rather than an alarm because the right response is a conversation "
        "the next morning, not a call at four in the afternoon. Matching the urgency of the "
        "response to the urgency of the problem is what keeps both channels credible."),
  ("h2", "Different units, different rules"),
  ("table", ["Unit", "Range", "Breach after", "Why"], [
   ["Walk-in freezer", "&minus;22 to &minus;16&nbsp;&deg;C", "20 minutes",
    "Large thermal mass; slow to change either way"],
   ["Under-counter fridge", "1 to 5&nbsp;&deg;C", "10 minutes", "Small; warms quickly"],
   ["Open display chiller", "1 to 7&nbsp;&deg;C", "20 minutes",
    "Constantly disturbed; a tight rule is unworkable"],
   ["Vaccine fridge", "2 to 8&nbsp;&deg;C", "5 minutes", "The stock is not replaceable"],
   ["Delivery vehicle", "&minus;20 to &minus;15&nbsp;&deg;C", "30 minutes",
    "Doors open at every drop"],
  ]),
  ("p", "The fourth row is the useful contrast. The rule is not about the physics of the unit; it "
        "is about what is in it and what happens if you are wrong. A vaccine fridge gets a tight "
        "rule because the consequence of a missed breach is severe and irreversible."),
  ("p", "Every one of these numbers is a judgement that belongs to whoever is responsible for the "
        "stock, written in configuration where they can see it, not embedded in code. The system "
        "applies rules; it does not choose them."),
  ("h2", "Fewer, louder"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Threshold alarms", "parts": [("real", 3), ("false", 214)]},
      {"label": "Duration rules", "parts": [("real", 3), ("false", 4)]}],
    "series": [("real", "Real breaches in the month", "#DD344C"),
               ("false", "Alarms that were door openings", "#7D8CA3")],
    "unit": "",
    "note": "Same three breaches. One of these systems still gets answered at 3am."}),
   "A month of alarms under two rule designs. The three that matter are identical; what differs "
   "is whether anybody is still listening when they fire.",
   "A month of cold chain alarms under threshold rules versus duration rules",
   "A stacked bar chart with two bars. Two series: real breaches in the month in red, and alarms "
   "that were door openings in grey. Threshold alarms produce three real breaches and two hundred "
   "and fourteen door openings. Duration rules produce three real breaches and four false alarms. "
   "A note says the same three breaches appear in both, and only one of these systems still gets "
   "answered at three in the morning."),
  ("p", "This chart is the entire argument of the post. Alarm fatigue is not a failure of "
        "discipline by the person on call; it is the predictable result of a system that cried "
        "wolf two hundred times and then once did not."),
  ("h3", "The alarm carries history"),
  ("p", "A message saying \"freezer 2 is at minus nine\" is much less useful than one showing the "
        "last six hours. Was it minus eighteen an hour ago and rising steadily, which is a "
        "compressor? Or has it been hovering around minus fifteen all evening, which is a door "
        "seal?"),
  ("p", "The trajectory determines what somebody does when they get out of bed, and including it "
        "in the alarm itself &mdash; a small chart, not a link to a dashboard behind a login "
        "&mdash; is the difference between a useful alarm and one that requires a laptop."),
  ("p", "Next: the sensor that is lying."),
 ],
},
{
 "slug": "how-a-broken-sensor-is-caught",
 "title": "How a broken sensor is caught",
 "nav": "Catching a broken sensor",
 "read": 5, "words": 730,
 "desc": ("The flat line that looks perfect, drift, calibration, and comparing a unit against "
          "itself."),
 "og": ("A sensor reporting exactly the same value for eleven hours is not a well-controlled "
        "fridge. Real temperature is noisy."),
 "abstract": ("Why a suspiciously stable reading is a failure signal, how drift is detected "
              "without a reference, the calibration schedule, and comparing units against their "
              "own history."),
 "lede": ("The worst failure in temperature monitoring is not a sensor that stops. It is a sensor "
          "that keeps reporting a plausible, reassuring number that has nothing to do with the "
          "temperature."),
 "tags": ["cold chain", "sensors", "calibration", "drift", "monitoring", "serverless"],
 "takeaways": [
  "Real temperature is noisy. A perfectly flat line is a broken sensor.",
  "Drift is caught by comparing a unit against its own recent behaviour, not against a standard.",
  "A second sensor in one unit is cheap and settles most arguments.",
  "Calibration is scheduled, recorded, and the certificate is stored with the readings.",
  "Battery and signal quality are readings too, and they warn before the failure.",
 ],
 "blocks": [
  ("h2", "The flat line"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Working sensor", "sub": ["-18.2, -18.4, -18.1"], "icon": "gauge"},
      {"title": "Noise is normal", "sub": ["compressor cycles"], "icon": "chart"},
      {"title": "Suspicious", "sub": ["-18.0, -18.0, -18.0"], "icon": "question"},
      {"title": "11 hours identical", "sub": ["to the decimal"], "icon": "alarm"},
      {"title": "It is stuck", "sub": ["not stable"], "icon": "stop"}],
    "title": "THE MOST DANGEROUS READING",
    "note": "Every threshold rule in the world says this fridge is fine."}),
   "How a stuck sensor presents. It passes every range check, produces a beautiful chart, and is "
   "reporting nothing at all.",
   "How a stuck temperature sensor looks compared with a working one",
   "A horizontal row of five boxes. Working sensor: minus eighteen point two, minus eighteen "
   "point four, minus eighteen point one. Noise is normal, from compressor cycles. Suspicious: "
   "minus eighteen point zero, repeated exactly. Eleven hours identical, to the decimal. It is "
   "stuck, not stable. A note says every threshold rule in the world says this fridge is fine."),
  ("p", "The check is straightforward once you know to look for it: if the variance across a "
        "window is essentially zero, something is wrong. A working refrigeration unit cycles, and "
        "the sensor sees the cycling."),
  ("p", "The threshold needs a little care because some sensors report to whole degrees, in which "
        "case identical consecutive readings are normal. The rule is really about the absence of "
        "any variation over a period long enough that a compressor must have cycled several "
        "times."),
  ("h2", "Drift, with nothing to compare against"),
  ("fig", ("chain", {
    "entry": {"title": "Is this sensor honest?", "sub": ["no reference available"], "icon": "gauge"},
    "steps": [
      {"title": "Compare to its own past", "sub": ["same unit, same season"], "icon": "search"},
      {"title": "Baseline shifted?", "sub": ["a degree over months"], "icon": "branch",
       "exit": {"title": "Probably fine", "sub": ["keep watching"], "icon": "check",
                "label": "no"}},
      {"title": "Did anything change?", "sub": ["new door seal, new load"], "icon": "branch",
       "exit": {"title": "Explained", "sub": ["annotate it"], "icon": "doc", "label": "yes"}},
      {"title": "Second sensor agrees?", "sub": ["if there is one"], "icon": "branch",
       "side": {"title": "Why two", "sub": ["it settles arguments"], "icon": "shield"},
       "exit": {"title": "The unit changed", "sub": ["not the sensor"], "icon": "truck",
                "label": "yes"}},
      {"title": "Suspect drift", "sub": ["calibrate or replace"], "icon": "alarm"}],
    "note": "Without a second sensor, the last two boxes are a guess. They are inexpensive."}),
   "How drift is investigated when there is no reference thermometer. The second sensor turns the "
   "final step from an inference into a measurement.",
   "How sensor drift is detected without a calibration reference",
   "A vertical chain of five steps entered by a box labelled Is this sensor honest, with no "
   "reference available. Step one compares it to its own past, same unit and same season. Step "
   "two asks whether the baseline has shifted by a degree over months; if not it exits to "
   "Probably fine, keep watching. Step three asks whether anything changed, such as a new door "
   "seal or a new load pattern; if so it exits to Explained, annotate it. Step four asks whether "
   "a second sensor agrees, drawing on a side box explaining that two sensors settle arguments; "
   "if it agrees, it exits to The unit changed, not the sensor. Step five suspects drift and "
   "recommends calibration or replacement. A note says without a second sensor the last two boxes "
   "are a guess, and second sensors are inexpensive."),
  ("h3", "Two sensors per critical unit"),
  ("p", "The cost of a second sensor is trivial next to the cost of one ambiguous incident, and "
        "it converts an entire class of unanswerable question into an answerable one. When two "
        "sensors in one unit disagree by more than a degree, that is a finding in itself and it "
        "is worth alarming on."),
  ("p", "They should be placed differently &mdash; one near the door, one at the back &mdash; "
        "which also produces genuinely useful information about how evenly the unit is "
        "performing. A walk-in that is three degrees warmer at the front has a problem that a "
        "single well-placed sensor will never reveal."),
  ("h2", "Calibration"),
  ("callout", "What the schedule looks like", [
   "<strong>Annually at minimum,</strong> and more often where the stock justifies it.",
   "<strong>Recorded in the same system</strong> as the readings, with the date, the reference "
   "used, and the offset found.",
   "<strong>The certificate is stored</strong> alongside, because the question is always asked "
   "later.",
   "<strong>A due date that is passed</strong> is an alarm, not a note. An uncalibrated sensor is "
   "an unverified record.",
   "<strong>The offset is never applied retrospectively</strong> to old readings. It is recorded, "
   "and the readings stand as they were taken.",
   "<strong>Ice point checks</strong> are cheap, take ten minutes, and catch gross errors between "
   "calibrations.",
  ]),
  ("p", "The fifth line is the one that surprises people. When calibration reveals a sensor was "
        "reading half a degree low, the temptation is to correct the historical record. The "
        "correct behaviour is to record the finding and leave the readings alone, because the "
        "record is of what was observed and the offset is a separate, later fact."),
  ("h3", "Battery and signal are readings too"),
  ("p", "A wireless sensor reports its battery level and signal strength alongside the "
        "temperature, and both degrade before they fail. A battery warning three weeks in advance "
        "is a maintenance task; the same battery failing at two in the morning is a gap in the "
        "record and a breach."),
  ("p", "Treating those as first-class readings, with their own thresholds and their own place in "
        "the daily check, converts most sensor failures from incidents into scheduled work."),
  ("p", "Next: who decides what happens to the stock."),
 ],
},
{
 "slug": "who-decides-what-happens-to-the-stock",
 "title": "Who decides what happens to the stock",
 "nav": "Who decides",
 "read": 5, "words": 720,
 "desc": ("Why the system presents evidence and never a verdict, what the decision record "
          "contains, and the report that inspectors actually want."),
 "og": ("A system that says 'stock is safe' has made a judgement it cannot be accountable for. It "
        "presents the evidence; a person signs."),
 "abstract": ("Why the disposal decision stays with a named person, what evidence the decision "
              "needs, how the decision is recorded, and what a good inspection export looks like."),
 "lede": ("At the end of a breach somebody has to decide whether the stock is usable, and that is "
          "the one thing in this entire system that must not be automated, for reasons that are "
          "as much about accountability as about safety."),
 "tags": ["cold chain", "decisions", "food safety", "records", "compliance", "serverless"],
 "takeaways": [
  "The system presents the evidence; a named person decides and signs.",
  "The decision record includes the chart, the duration, the product and the reasoning.",
  "Record disposals and releases with equal care. A release is also a decision.",
  "The inspection export is a document, not a dashboard login.",
  "Count breaches by unit over time; the repeat offender is usually one appliance.",
 ],
 "blocks": [
  ("h2", "What the system hands over"),
  ("callout", "The evidence pack for one breach", [
   "<strong>The chart:</strong> twelve hours either side, at full resolution, on sensor time.",
   "<strong>The numbers:</strong> peak temperature, time out of range, time above each of the "
   "relevant thresholds.",
   "<strong>What was in it:</strong> the stock in that unit at that time, if the system knows.",
   "<strong>The alarm history:</strong> when it fired, when it was acknowledged, by whom.",
   "<strong>Sensor status:</strong> last calibration, battery, whether a second sensor agreed.",
   "<strong>No recommendation.</strong> Not even a colour-coded one.",
  ]),
  ("p", "The last line is deliberate and is the point of the post. A system that displays a green "
        "tick saying stock is fine has made a food safety judgement, and when that judgement is "
        "wrong there is nobody who made it. Presenting the same evidence with no verdict puts the "
        "decision where the responsibility already is."),
  ("h3", "The release is a decision too"),
  ("p", "Deciding that stock is fine after a breach is exactly as consequential as deciding to "
        "throw it away, and it is usually recorded far less carefully because nothing visible "
        "happens. That asymmetry is where problems hide."),
  ("p", "So both outcomes produce the same record: who decided, when, on what evidence, and why. "
        "\"Peak minus nine for eighteen minutes, product is a sealed frozen good with a "
        "documented tolerance, released\" is a defensible sentence. Nothing at all is not."),
  ("h2", "The decision record"),
  ("fig", ("chain", {
    "entry": {"title": "A breach has ended", "sub": ["evidence assembled"], "icon": "shield"},
    "steps": [
      {"title": "Who is deciding?", "sub": ["a named person"], "icon": "person"},
      {"title": "They see the pack", "sub": ["chart, numbers, stock"], "icon": "chart"},
      {"title": "Decision", "sub": ["dispose, release, or test"], "icon": "branch",
       "exit": {"title": "Send for testing", "sub": ["a real third option"], "icon": "search",
                "label": "unsure"}},
      {"title": "Reason recorded", "sub": ["in their words"], "icon": "doc"},
      {"title": "Signed and closed", "sub": ["append-only, like everything"], "icon": "lock"}],
    "note": "The third option exists because forcing a binary choice produces bad releases."}),
   "How a breach is closed out. Offering testing as an explicit third option removes the pressure "
   "that produces optimistic releases.",
   "How a decision about stock after a temperature breach is recorded",
   "A vertical chain of five steps entered by a box labelled A breach has ended, evidence "
   "assembled. Step one identifies who is deciding, a named person. Step two shows them the pack "
   "with the chart, numbers and stock. Step three records the decision: dispose, release, or "
   "test; an unsure answer exits to Send for testing, described as a real third option. Step four "
   "records the reason in their words. Step five signs and closes it, append-only like everything "
   "else. A note says the third option exists because forcing a binary choice produces bad "
   "releases."),
  ("h3", "In their words"),
  ("p", "The reason is free text and it should be, because the reasoning is specific to the "
        "product and the situation and a dropdown cannot hold it. It is also the part that is "
        "genuinely useful a year later, when the same question arises and somebody wants to know "
        "how it was handled last time."),
  ("h2", "The inspection export"),
  ("fig", ("strip", {
    "stages": [
      {"title": "An inspector asks", "sub": ["for a date range"], "icon": "person"},
      {"title": "One document", "sub": ["not a login"], "icon": "doc"},
      {"title": "Every reading", "sub": ["and every gap"], "icon": "database"},
      {"title": "Every breach", "sub": ["and its decision"], "icon": "shield"},
      {"title": "Calibration records", "sub": ["attached"], "icon": "check"}],
    "title": "WHAT AN INSPECTION ACTUALLY NEEDS",
    "note": "A dashboard is not a record. A document with everything in it is."}),
   "The export. Producing it as a single self-contained document rather than access to a system "
   "is what makes an inspection short.",
   "What a cold chain inspection export contains",
   "A horizontal row of five boxes. An inspector asks for a date range. One document, not a "
   "login. Every reading, and every gap. Every breach, and its decision. Calibration records "
   "attached. A note says a dashboard is not a record, and a document with everything in it is."),
  ("p", "The gaps matter here more than anywhere else. An export showing continuous readings with "
        "silent holes in it invites the question of what was happening during them; one that "
        "shows explicit gap records with their duration answers the question before it is asked."),
  ("h3", "The repeat offender"),
  ("p", "Counting breaches per unit over a year almost always produces the same finding: one "
        "appliance accounts for a large share of them. It is old, or it is in a warm corner, or "
        "its door seal has been marginal for two years."),
  ("p", "That is a maintenance or replacement decision with a number attached, and it is "
        "invisible when breaches are handled individually. \"This unit has breached fourteen times "
        "this year and the others have breached three times between them\" is the sentence that "
        "gets a replacement approved."),
  ("h3", "What this system does not do"),
  ("p", "It does not judge stock, it does not silence its own alarms, it does not edit its "
        "records, and it does not stop escalating because it is late. Each of those absences is a "
        "feature somebody will eventually ask for, and each of them would convert a record that "
        "can be relied on into one that cannot."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="sensor",
 volumes=[(6, "6 sensors"), (20, "20 sensors"), (80, "80 sensors")],
 read_each=0.0,
 msgs_each=0.0,
 lede=("There is no model in this system and almost nothing is sent. The volume is readings: a "
       "sensor at five-minute intervals produces about nine thousand a month. Twenty sensors is a "
       "restaurant group or a small distribution site. Here is where each cent goes."),
 takeaway_extra=("Readings are the entire variable cost, and they are cheap even at eighty "
                 "sensors."),
 risks=[
  "<strong>One write per reading, forever.</strong> Batch readings per sensor per hour into a "
  "single item and the write count drops by an order of magnitude.",
  "<strong>Never expiring at full resolution.</strong> Keep full resolution for two years, then "
  "roll up to per-hour minimum, maximum and mean. Do not delete breach windows.",
  "<strong>Alarm delivery over a single channel.</strong> Not a cost problem, but an SMS bill is "
  "cheaper than a freezer of stock, and email alone will not wake anybody.",
 ],
 per_unit_note=("There is no read line and effectively no messaging line: alarms are rare by "
                "design. Reading writes and their storage are the whole bill."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="cc",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the fail-closed sweep, and the append-only record."),
 outside=[
  {"title": "Sensors", "sub": ["MQTT or HTTP,", "every 5 minutes"], "icon": "gauge"},
  {"title": "On-call rota", "sub": ["three people deep"], "icon": "person"},
  {"title": "Inspection export", "sub": ["one document"], "icon": "doc"}],
 inside=[
  {"title": "IoT Core + EventBridge", "sub": ["ingest,", "5-minute sweep"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["ingest, judge, escalate"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["readings, events"], "icon": "database"}],
 note="us-east-1. One account. Fail closed: a missed sweep is a breach, not an absence.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Sensors, reporting over MQTT or HTTP every "
  "five minutes. The on-call rota, three people deep. And the Inspection export, produced as one "
  "document. Inside the account, three groups. IoT Core handling ingest and EventBridge running a "
  "five-minute sweep. Three Lambda functions named ingest, judge and escalate. And two DynamoDB "
  "tables named readings and events. A note gives the region as us-east-1, one account, and "
  "states that the system fails closed: a missed sweep is a breach, not an absence."),
 functions=[
  ["<code>cc-ingest</code>", "IoT rule",
   "Appends the reading with both timestamps; flags implausible values without discarding them",
   "5s / 512&nbsp;MB"],
  ["<code>cc-judge</code>", "EventBridge, every 5 minutes",
   "Checks every sensor for a due reading; runs the consecutive and cumulative rules; opens "
   "breaches", "60s / 1024&nbsp;MB"],
  ["<code>cc-escalate</code>", "EventBridge, every minute while a breach is open",
   "Repeats and escalates until acknowledged; never stops on its own", "15s / 512&nbsp;MB"]],
 roles=[
  ["<code>cc-ingest-role</code>", "<code>dynamodb:PutItem</code>", "Readings only; no update, no "
   "delete"],
  ["<code>cc-judge-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>", "Readings; appends to events"],
  ["<code>cc-escalate-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>, <code>sns:Publish</code>, "
   "<code>ses:SendEmail</code>",
   "Events; one topic; one verified identity"]],
 tables=[
  ("Table: readings",
   "PK   sensor_id         S\n"
   "SK   taken_at          S   the sensor's own clock\n"
   "     received_at       S   when it reached us; often differs\n"
   "     celsius           N   null on a gap record\n"
   "     kind              S   reading | gap | implausible | correction\n"
   "     battery_pct       N\n"
   "     rssi              N\n"
   "     note              S   set on correction records only, with a name\n\n"
   "No update path exists in any role. A correction is a new item of kind\n"
   "`correction` referencing the original, and both appear on every chart."),
  ("Table: events",
   "PK   unit_id           S   walkin_2\n"
   "SK   opened_at         S\n"
   "     kind              S   excursion | breach | gap_breach | sensor_stuck\n"
   "                           | drift_suspected | calibration_due\n"
   "     closed_at         S\n"
   "     peak_celsius      N\n"
   "     minutes_out       N   consecutive\n"
   "     cumulative_today  N   minutes, for the review rule\n"
   "     acknowledged_by   S   a named person, and when\n"
   "     decision          S   dispose | release | testing\n"
   "     decided_by        S   a named person\n"
   "     reason            S   free text, in their words\n\n"
   "A release is recorded as carefully as a disposal. The asymmetry in how\n"
   "carefully those two get written down is where problems hide.")],
 inbound=[
  "<strong>Sensors report every five minutes</strong> over IoT Core. Devices that buffer during "
  "signal loss send batches, which is why both timestamps are stored.",
  "<strong>The judge sweeps every sensor every five minutes</strong> rather than reacting to "
  "arrivals, because the whole point is to notice what did not arrive.",
  "<strong>Unit rules are configuration</strong> &mdash; range, consecutive limit, cumulative "
  "limit &mdash; owned by whoever is responsible for the stock, not by the code.",
  "<strong>Escalation runs until acknowledged.</strong> There is no maximum number of attempts "
  "and no automatic close."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Everything here is comparisons and "
  "durations, which is the correct level of sophistication for a safety record.",
  "<strong>The tempting use</strong> is predicting failures from the temperature curve. Battery "
  "level, door-open frequency and compressor cycle time already say it more directly.",
  "<strong>The wrong use</strong> is any judgement about whether stock is safe. Part 5 is entirely "
  "about why that decision needs a person's name on it.",
  "<strong>Summarising a breach for the record</strong> is defensible, and the summary sits "
  "alongside the readings rather than replacing them.",
  "<strong>The cost page assumes none</strong>, which is why reading writes are the whole bill."],
 gotchas=[
  "Fail closed on missing data. The default behaviour of most alerting is to stay quiet when "
  "nothing arrives, which makes total failure look like perfect health.",
  "Alarm on duration, never on a single reading. Two hundred door-opening alarms a month is how "
  "the one that matters gets silenced.",
  "Check for zero variance. A stuck sensor passes every range check and produces the most "
  "reassuring chart in the building.",
  "Give the readings table no update or delete path in any role. An editable temperature record "
  "is not a record.",
  "Record releases as carefully as disposals, with a name and a reason. Nothing visible happens "
  "on a release, which is exactly why it gets written down badly."],
))
