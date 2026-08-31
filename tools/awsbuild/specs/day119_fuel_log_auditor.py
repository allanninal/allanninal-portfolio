"""Day 119 -- 2026-08-21 -- Fuel log auditor."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "fuel-log-auditor"
NAME = "Fuel log auditor"

SPEC = {
 "slug": SLUG, "date": "2026-08-21", "name": NAME,
 "tagline": ("Checks fuel records against the vehicles they belong to and finds the "
             "discrepancies, most of which turn out to be a mistyped odometer or the wrong van "
             "selected at the pump rather than anything worth accusing anybody of."),
 "lede": ("A small system that matches fuel transactions to vehicles, works out which numbers "
          "cannot be right, and raises a query rather than an allegation. The interesting "
          "findings are almost never theft: they are data errors, a vehicle whose economy is "
          "quietly degrading, and one van that nobody has noticed is doing twice the mileage of "
          "the rest. Seven posts on the same system, one diagram at a time, with a cost breakdown "
          "and an engineering reference at the end."),
 "keywords": ["fuel management", "fleet", "fuel cards", "vehicles", "data quality", "serverless"],
 "icons": ["truck", "gauge", "search"],
 "faq": [
  ("What is a fuel log auditor?",
   "A small serverless system that matches fuel card transactions to vehicles and odometer "
   "readings, identifies records that cannot be right, and raises queries with the driver before "
   "anything else."),
  ("Is this a fraud detection system?",
   "No, and framing it that way makes it worse. Most discrepancies are data errors, and a system "
   "that treats every one as suspicion damages a workforce to recover very little."),
  ("Why compare a vehicle only against itself?",
   "Because fuel economy varies enormously with load, route, weather and driver. A van against "
   "the fleet average tells you almost nothing; against its own history it tells you a lot."),
  ("What is the most common finding?",
   "A fill recorded against the wrong vehicle, usually two vans with adjacent numbers. It looks "
   "alarming on both records and is a data problem."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "fuel-log-auditor-on-aws",
 "title": "A fuel log auditor on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Matches fuel transactions to vehicles, finds impossible numbers, and raises queries "
          "rather than accusations. AWS, about $2 a month."),
 "og": ("Most fuel discrepancies are typing errors. Building this as a fraud system finds the "
        "same records and destroys the trust needed to resolve them."),
 "abstract": ("The whole system on one page -- match, check, query &mdash; and why the framing of "
              "the output determines whether it is useful or corrosive."),
 "lede": ("A fuel report shows van seven doing eleven miles to the gallon and van eight doing "
          "sixty-two. Nobody is stealing anything; somebody selected the wrong vehicle at the "
          "pump on Tuesday and the two records swapped a tankful. Finding that in a week rather "
          "than at year end is most of what a fuel audit is actually for."),
 "tags": ["fuel management", "fleet", "fuel cards", "vehicles", "data quality", "serverless"],
 "takeaways": [
  "Most discrepancies are data errors, not dishonesty. Build for that.",
  "Compare a vehicle against its own history, never against a fleet average.",
  "Some checks are arithmetic: a fill larger than the tank is not a judgement call.",
  "Raise a query with the driver first. It resolves most of them in one reply.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Fuel transactions", "sub": ["card provider,", "or receipts"], "icon": "money"},
      {"title": "Odometer readings", "sub": ["at the pump, or later"], "icon": "gauge"},
      {"title": "The driver", "sub": ["asked, not accused"], "icon": "person"}],
    "inside": [
      {"title": "Matcher", "sub": ["which vehicle,", "really?"], "icon": "search"},
      {"title": "Checks", "sub": ["impossible first,", "unusual second"], "icon": "filter"},
      {"title": "Query", "sub": ["a question,", "with the numbers"], "icon": "email"}],
    "edges": [{"from": 0, "to": 0, "label": "fills"},
              {"from": 1, "to": 1, "label": "distance"},
              {"from": 2, "to": 2, "label": "one question", "up": True}],
    "note": "The word on the right is 'query'. Everything about the design follows from that."}),
   "Three things outside the account, three pieces inside it. The output is a question rather "
   "than a finding, and that choice shapes every component.",
   "System: fuel transactions matched, checked and queried",
   "Three boxes across the top sit outside the AWS account. On the left, Fuel transactions from a "
   "card provider or from receipts. In the middle, Odometer readings taken at the pump or later. "
   "On the right, The driver, who is asked rather than accused. Each connects by an arrow to the "
   "AWS account container below. Fills flow down into the account. Distance feeds in. One "
   "question goes back out. Inside the AWS account are three components in a row. On the left, "
   "the Matcher, working out which vehicle it really was. In the middle, the Checks, running "
   "impossible tests first and unusual ones second. On the right, the Query, a question with the "
   "numbers attached. A note at the bottom says the word on the right is query, and everything "
   "about the design follows from that."),
  ("h3", "Not a fraud system"),
  ("p", "Fuel fraud exists and it is a smaller problem than the industry around detecting it "
        "suggests. In a typical small fleet the overwhelming majority of odd-looking records are "
        "a mistyped odometer, a fill recorded against the wrong vehicle, a jerry can for the "
        "mower, or a receipt that never got submitted."),
  ("p", "Building this as a fraud system finds exactly the same records and attaches a different "
        "meaning to them, and the cost of that is high: drivers who feel monitored stop "
        "volunteering the corrections that would resolve most of the queries in one sentence."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The matcher.</strong> Establishes which vehicle a transaction really belongs to, "
   "which is less obvious than it sounds. Part 2.",
   "<strong>The checks.</strong> Arithmetic impossibilities first, then deviations from the "
   "vehicle's own pattern. Parts 3 and 5.",
   "<strong>The query.</strong> One question to the driver, phrased as a question. Part 4.",
  ]),
  ("h2", "One discrepancy, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Van 7 fills 68L", "sub": ["tank is 60L"], "icon": "money"},
      {"title": "Impossible", "sub": ["arithmetic, not opinion"], "icon": "alarm"},
      {"title": "Query the driver", "sub": ["'was this two vehicles?'"], "icon": "email"},
      {"title": "Reply", "sub": ["'van 7 and the mower'"], "icon": "person"},
      {"title": "Resolved", "sub": ["split, and recorded"], "icon": "check"}],
    "title": "ONE DISCREPANCY, END TO END",
    "note": "Ninety seconds of somebody's time. The alternative is a year-end mystery."}),
   "The same system as one line. The third box is where a fraud-framed system would have gone "
   "somewhere much more expensive.",
   "One fuel discrepancy from detection to resolution",
   "A horizontal row of five boxes joined by arrows. Van seven fills sixty-eight litres when the "
   "tank is sixty. Impossible: arithmetic, not opinion. Query the driver: was this two vehicles? "
   "Reply: van seven and the mower. Resolved: split, and recorded. A note says it took ninety "
   "seconds of somebody's time, and the alternative is a year-end mystery."),
  ("h2", "In plain words"),
  ("p", "A transaction shows sixty-eight litres against van seven, whose tank holds sixty. That "
        "is not unusual, it is impossible, and the distinction matters: no interpretation is "
        "required and no judgement is being made about anybody."),
  ("p", "So the query is a question with the arithmetic in it: \"This fill was 68 litres and van "
        "7's tank is 60. Was some of it for something else?\" The driver replies that they filled "
        "the mower's can at the same time, which is entirely normal and was never recorded "
        "anywhere."),
  ("p", "The record is split, the mower gets a fuel record it never had before, and the next time "
        "it happens the system knows this is a thing that happens here. That last part &mdash; "
        "learning the legitimate patterns rather than flagging them forever &mdash; is what stops "
        "the query list becoming noise."),
  ("callout", "Design rules that shaped every decision", [
   "Separate impossible from unusual, and treat them completely differently.",
   "Compare a vehicle against its own history, never against a fleet average.",
   "Ask the driver first, always, and ask a question rather than stating a conclusion.",
   "Record the legitimate explanations so the same query is not raised twice.",
   "Never compute a per-driver league table. It measures routes, not people.",
   "The most valuable output is usually about a vehicle, not about a person.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Fuel is often one of the larger controllable costs in a small operation and the data is "
        "usually poor: odometer readings entered from memory, transactions matched to vehicles by "
        "a card number that gets swapped, and receipts that arrive in a carrier bag once a month."),
  ("p", "Cleaning that up produces two things worth having. The obvious one is an accurate cost "
        "per mile. The less obvious and usually larger one is early warning about vehicles: a van "
        "whose economy has fallen eight per cent over four months has something wrong with it, "
        "and that is visible in fuel data months before it is visible anywhere else."),
  ("p", "The next four posts walk through each piece: how a fill gets matched to a vehicle, why "
        "fuel economy only means something against itself, how a query gets raised without an "
        "accusation, and what the fuel data says about the vehicles. One diagram per post, a cost "
        "breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-fill-gets-matched-to-a-vehicle",
 "title": "How a fill gets matched to a vehicle",
 "nav": "How it is matched",
 "read": 5, "words": 740,
 "desc": ("Why the card number is not the vehicle, the odometer that gets typed wrong, and the "
          "swapped-vehicle pattern that shows up on two records at once."),
 "og": ("A fuel card is assigned to a vehicle right up until somebody takes the other van because "
        "theirs is being serviced."),
 "abstract": ("Why card-to-vehicle mapping drifts, how odometer readings get mistyped, the "
              "signature of a swapped pair, and what to do when the vehicle genuinely cannot be "
              "determined."),
 "lede": ("Every fuel record claims to belong to a vehicle and a meaningful minority of them are "
          "wrong, in ways that produce alarming numbers on two records simultaneously."),
 "tags": ["fuel management", "data quality", "fleet", "matching", "odometer", "serverless"],
 "takeaways": [
  "The card is assigned to a vehicle, and vehicles get swapped without the card moving.",
  "Odometer typos have recognisable shapes: transposed digits, dropped digits, a stuck value.",
  "A swapped pair shows up as one impossibly good record and one impossibly bad one.",
  "Where the vehicle cannot be determined, say so rather than guessing.",
  "Keep the raw transaction exactly as received, always.",
 ],
 "blocks": [
  ("h2", "The card is not the vehicle"),
  ("fig", ("chain", {
    "entry": {"title": "A fuel transaction", "sub": ["card, litres, time, site"], "icon": "money"},
    "steps": [
      {"title": "Card to vehicle", "sub": ["the assumed mapping"], "icon": "form"},
      {"title": "Odometer given?", "sub": ["at the pump"], "icon": "branch",
       "exit": {"title": "No distance check", "sub": ["flag as unverifiable"], "icon": "question",
                "label": "no"}},
      {"title": "Plausible against last?", "sub": ["forwards, and not absurd"], "icon": "branch",
       "exit": {"title": "Odometer query", "sub": ["a typo, usually"], "icon": "alarm",
                "label": "no"}},
      {"title": "Tank capacity check", "sub": ["arithmetic"], "icon": "counter"},
      {"title": "Matched", "sub": ["with a confidence"], "icon": "check"}],
    "note": "The mapping in the first box is an assumption, and it is wrong more often than "
            "anybody expects."}),
   "How a transaction becomes an attributed fill. The first box is the weakest link and is "
   "usually treated as ground truth.",
   "How a fuel transaction is matched to a vehicle",
   "A vertical chain of five steps entered by a box labelled A fuel transaction with card, "
   "litres, time and site. Step one maps card to vehicle using the assumed mapping. Step two asks "
   "whether an odometer reading was given at the pump; if not it exits to No distance check, "
   "flagged as unverifiable. Step three asks whether it is plausible against the last reading, "
   "moving forwards and not absurd; if not it exits to Odometer query, usually a typo. Step four "
   "runs the tank capacity check, which is arithmetic. Step five records it as matched with a "
   "confidence. A note says the mapping in the first box is an assumption and is wrong more often "
   "than anybody expects."),
  ("h3", "Why the mapping drifts"),
  ("p", "A van goes in for repair and the driver takes the spare, with their own card. A card is "
        "reissued and the new number is not updated. Two drivers swap vehicles for a week and "
        "nobody tells anybody. A card lives in the glovebox of a vehicle that has been sold."),
  ("p", "None of these are unusual and all of them produce fuel attributed to the wrong vehicle "
        "for a period. The system's job is to notice when the attributed vehicle stops making "
        "sense, and the strongest signal is the odometer moving in a way that vehicle could not "
        "have."),
  ("h2", "Odometer typos have shapes"),
  ("table", ["What happened", "What it looks like", "How it is caught"], [
   ["Transposed digits", "84,213 becomes 84,231", "A small backwards jump next time"],
   ["Dropped a digit", "84,213 becomes 8,421", "An enormous backwards jump"],
   ["Added a digit", "84,213 becomes 842,133", "An impossible distance in one fill"],
   ["Entered the trip meter", "84,213 becomes 312", "Value far below every previous reading"],
   ["Entered the litres", "84,213 becomes 54", "Two fields with suspiciously similar values"],
   ["Same as last time", "84,213 twice", "Zero distance with fuel purchased"],
  ]),
  ("p", "The last row is the most common and the least obviously wrong. Somebody who cannot see "
        "the dashboard reading enters what they entered last time, which produces a record "
        "showing fuel bought and no distance travelled, and averaged over a month it quietly "
        "ruins the economy figure for that vehicle."),
  ("p", "None of these need clever detection. They are arithmetic checks against the previous "
        "reading and they resolve with a one-line query: \"the odometer for van 4 on Tuesday "
        "reads lower than the week before &mdash; can you check?\""),
  ("h2", "The swapped pair"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Van 7, normally", "parts": [("mpg", 34)]},
      {"label": "Van 8, normally", "parts": [("mpg", 33)]},
      {"label": "Van 7, that week", "parts": [("mpg", 11)]},
      {"label": "Van 8, that week", "parts": [("mpg", 62)]}],
    "series": [("mpg", "Miles per gallon", "#8C4FFF")],
    "unit": "",
    "note": "One tank recorded against the wrong van. The pair moves in opposite directions."}),
   "The signature of a mis-recorded fill. Two vehicles departing from their own norms in opposite "
   "directions in the same week is almost never two problems.",
   "Two vans showing opposite fuel economy anomalies in the same week",
   "A bar chart with four bars showing miles per gallon. Van seven normally achieves thirty-four. "
   "Van eight normally achieves thirty-three. In the week in question van seven shows eleven and "
   "van eight shows sixty-two. A note says one tank was recorded against the wrong van, and the "
   "pair moves in opposite directions."),
  ("p", "This pattern is worth detecting explicitly because it is common, because it looks "
        "alarming on the bad half, and because a system that flags van seven alone sends somebody "
        "to have a conversation about a problem that does not exist."),
  ("p", "The check is simple: when a vehicle's economy is anomalously poor, look for another "
        "vehicle with an anomalously good week in the same period, and mention the possibility in "
        "the query. \"Van 7 and van 8 both look odd this week in opposite directions &mdash; was "
        "a fill recorded against the wrong one?\" resolves it immediately."),
  ("h3", "When the vehicle cannot be determined"),
  ("p", "Sometimes there is genuinely no way to know, particularly with receipts submitted late "
        "with no odometer. Those records are marked unattributed rather than assigned to the most "
        "likely vehicle, and they appear in the fleet total but in no vehicle's economy figure."),
  ("p", "Guessing pollutes exactly the data the system exists to produce. An unattributed record "
        "is honest and its count is itself a useful metric: a fleet where fifteen per cent of "
        "fuel cannot be attributed to a vehicle has a process problem worth more than any "
        "individual query."),
  ("p", "Next: what the economy figure actually means."),
 ],
},
{
 "slug": "why-fuel-economy-only-means-something-against-itself",
 "title": "Why fuel economy only means something against itself",
 "nav": "Against itself",
 "read": 5, "words": 730,
 "desc": ("What actually moves miles per gallon, why a fleet average is misleading, and how a "
          "vehicle's own baseline is built."),
 "og": ("Comparing two vans' fuel economy compares their routes, their loads and the season. It "
        "barely mentions the vehicles."),
 "abstract": ("The factors that dominate fuel economy, why cross-vehicle comparison is nearly "
              "meaningless, how a per-vehicle baseline is built, and how seasonality is handled."),
 "lede": ("Fuel economy is the obvious metric and it is a difficult one, because almost "
          "everything that moves it has nothing to do with the vehicle or the driver."),
 "tags": ["fuel management", "fuel economy", "baselines", "seasonality", "fleet", "serverless"],
 "takeaways": [
  "Load, route, season, traffic and idling dominate. The vehicle is a smaller factor.",
  "A fleet league table ranks routes, not vehicles or drivers.",
  "Build a baseline per vehicle over at least ten fills, and note it is approximate.",
  "Winter economy is worse for everybody; compare to the same season.",
  "A trend within one vehicle is the signal worth acting on.",
 ],
 "blocks": [
  ("h2", "What actually moves it"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Load", "parts": [("effect", 18)]},
      {"label": "Route type", "parts": [("effect", 22)]},
      {"label": "Season", "parts": [("effect", 12)]},
      {"label": "Driving style", "parts": [("effect", 10)]},
      {"label": "Vehicle condition", "parts": [("effect", 8)]}],
    "series": [("effect", "Typical swing in economy, %", "#ED7100")],
    "unit": "",
    "note": "The thing you want to measure is the smallest bar. Hence: compare against itself."}),
   "The approximate size of each influence on fuel economy. Vehicle condition is what the system "
   "can usefully detect and it is the smallest effect, which is why the noise has to be removed "
   "by comparing like with like.",
   "The typical influence of five factors on vehicle fuel economy",
   "A bar chart with five bars showing typical swing in economy as a percentage. Load: eighteen "
   "per cent. Route type: twenty-two per cent. Season: twelve per cent. Driving style: ten per "
   "cent. Vehicle condition: eight per cent. A note says the thing you want to measure is the "
   "smallest bar, hence comparing a vehicle against itself."),
  ("p", "Route type is the biggest single factor in most small fleets and the one that varies "
        "most between vehicles. A van doing urban multi-drop and a van doing motorway runs will "
        "differ by twenty per cent or more with nothing wrong with either of them."),
  ("p", "Which makes the league table that every fleet system produces &mdash; vehicles ranked by "
        "miles per gallon &mdash; a ranking of routes wearing the costume of a performance "
        "measure. It is worse than useless if anybody acts on it."),
  ("h2", "The per-vehicle baseline"),
  ("fig", ("chain", {
    "entry": {"title": "A vehicle", "sub": ["with some history"], "icon": "truck"},
    "steps": [
      {"title": "Ten clean fills?", "sub": ["matched, odometer good"], "icon": "branch",
       "exit": {"title": "No baseline yet", "sub": ["report the figures, no alerts"],
                "icon": "clock", "label": "no"}},
      {"title": "Median economy", "sub": ["not mean"], "icon": "counter"},
      {"title": "And its spread", "sub": ["how variable is normal?"], "icon": "chart"},
      {"title": "By season", "sub": ["if a year exists"], "icon": "clock",
       "side": {"title": "Winter", "sub": ["worse for everybody"], "icon": "gauge"}},
      {"title": "A baseline", "sub": ["with its sample size"], "icon": "check"}],
    "note": "A vehicle with a wide normal spread needs a wider band before anything is unusual."}),
   "How a vehicle's own baseline is built. The spread in the third box is as important as the "
   "central figure, because a multi-drop van is naturally more variable than a motorway one.",
   "How a per-vehicle fuel economy baseline is built",
   "A vertical chain of five steps entered by a box labelled A vehicle with some history. Step "
   "one asks whether there are ten clean fills, matched and with good odometer readings; if not "
   "it exits to No baseline yet, reporting the figures without alerts. Step two computes the "
   "median economy rather than the mean. Step three computes its spread, asking how variable is "
   "normal. Step four adjusts by season if a year of data exists, drawing on a side box noting "
   "winter is worse for everybody. Step five produces a baseline with its sample size. A note "
   "says a vehicle with a wide normal spread needs a wider band before anything is unusual."),
  ("h3", "Median, and per-fill is noisy"),
  ("p", "Individual fills are extremely noisy because tanks are never filled to the same level. A "
        "fill that stops at the first click and one that is topped to the neck differ by several "
        "litres, which on a sixty-litre tank moves the calculated economy substantially."),
  ("p", "So the working unit is a rolling window of several fills rather than a single one. That "
        "removes most of the fill-level noise and it means a genuine change takes a few weeks to "
        "confirm, which is an acceptable trade for a signal that is about slow degradation."),
  ("h3", "Season"),
  ("p", "Winter economy is worse for every vehicle: cold engines, heaters, lights, denser air, "
        "wetter roads. A ten per cent drop in November is normal and a system that alerts on it "
        "will alert on the entire fleet at once, which is how people learn to ignore it."),
  ("p", "With a year of data the comparison is against the same months last year. Without one, "
        "the comparison is against the rest of the fleet's movement in the same period, which is "
        "the one legitimate use of a cross-vehicle comparison: not levels, but changes."),
  ("h2", "The one honest cross-vehicle comparison"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Fleet drops 9%", "sub": ["November"], "icon": "chart"},
      {"title": "Van 3 drops 9%", "sub": ["normal"], "icon": "check"},
      {"title": "Van 4 drops 9%", "sub": ["normal"], "icon": "check"},
      {"title": "Van 5 drops 21%", "sub": ["not the season"], "icon": "alarm"},
      {"title": "Look at van 5", "sub": ["the only real signal"], "icon": "search"}],
    "title": "CHANGES, NOT LEVELS",
    "note": "Comparing levels ranks routes. Comparing changes finds the vehicle with a problem."}),
   "The legitimate use of the fleet as a comparison group. Nobody is compared on how efficient "
   "they are, only on how much they moved relative to everybody else.",
   "How comparing changes rather than levels identifies one vehicle with a problem",
   "A horizontal row of five boxes. Fleet drops nine per cent in November. Van three drops nine "
   "per cent: normal. Van four drops nine per cent: normal. Van five drops twenty-one per cent: "
   "not the season. Look at van five, the only real signal. A note says comparing levels ranks "
   "routes, and comparing changes finds the vehicle with a problem."),
  ("p", "This is the whole method in one picture. The fleet provides the control for whatever is "
        "happening in the world that month, each vehicle is measured against its own history, and "
        "what emerges is the vehicle that is behaving differently from itself for reasons the "
        "season does not explain."),
  ("p", "Next: how that becomes a conversation."),
 ],
},
{
 "slug": "how-a-query-gets-raised-without-an-accusation",
 "title": "How a query gets raised without an accusation",
 "nav": "How queries are raised",
 "read": 5, "words": 720,
 "desc": ("Asking the driver first, the wording that works, recording legitimate explanations, "
          "and the rare case that is genuinely serious."),
 "og": ("The same query sent as a question resolves in a sentence. Sent as a finding it produces "
        "a grievance and no information."),
 "abstract": ("Why the driver is asked first, the wording that gets a useful reply, why "
              "explanations must be recorded, and how the genuinely serious cases are handled "
              "differently."),
 "lede": ("How a query is worded determines whether you get the answer or a defence, and in a "
          "system where most anomalies have an innocent explanation, getting the answer is the "
          "entire point."),
 "tags": ["fuel management", "communication", "trust", "queries", "fleet", "serverless"],
 "takeaways": [
  "Ask the driver first, before anybody else sees it.",
  "State the numbers and ask an open question. Do not state a conclusion.",
  "Record the explanation so the same query is never raised twice.",
  "Batch queries weekly. A message per anomaly is harassment.",
  "The rare serious case goes to a person, off this system, immediately.",
 ],
 "blocks": [
  ("h2", "The wording"),
  ("callout", "Two versions of the same query", [
   "<strong>Wrong:</strong> \"Van 4 shows an unexplained 68 litre fill on Tuesday exceeding tank "
   "capacity. Please explain this discrepancy.\"",
   "<strong>Right:</strong> \"Van 4's fill on Tuesday was 68 litres and the tank holds 60. Was "
   "some of it for something else?\"",
   "<strong>The difference:</strong> the second one contains the likely answer and invites it.",
   "<strong>It also assumes competence.</strong> The driver knows what they filled; the system "
   "does not.",
   "<strong>Reply rate:</strong> the second version gets answered. The first gets escalated to a "
   "manager and takes a week.",
   "<strong>Same data, same query, same person.</strong> Only the sentence changed.",
  ]),
  ("p", "The word \"discrepancy\" is doing a lot of damage in the first version, as is "
        "\"unexplained\". Both frame the record as a problem attributable to the reader, which is "
        "not what the system knows and not usually what happened."),
  ("h2", "Batching"),
  ("fig", ("chain", {
    "entry": {"title": "Anomalies this week", "sub": ["across the fleet"], "icon": "counter"},
    "steps": [
      {"title": "Group by driver", "sub": ["not by anomaly"], "icon": "person"},
      {"title": "Already explained?", "sub": ["a known pattern"], "icon": "branch",
       "exit": {"title": "Do not ask again", "sub": ["the mower, every month"], "icon": "check",
                "label": "yes"}},
      {"title": "More than three?", "sub": ["for one person"], "icon": "branch",
       "exit": {"title": "A conversation", "sub": ["not a list of queries"], "icon": "email",
                "label": "yes"}},
      {"title": "One message", "sub": ["weekly, with all of them"], "icon": "email"},
      {"title": "Record the answers", "sub": ["against the records"], "icon": "database"}],
    "note": "The second exit is what keeps this from becoming a weekly irritation."}),
   "How queries are grouped and sent. Suppressing known explanations is what stops the same "
   "legitimate behaviour being questioned every month.",
   "How fuel queries are batched and sent to drivers",
   "A vertical chain of five steps entered by a box labelled Anomalies this week across the "
   "fleet. Step one groups by driver rather than by anomaly. Step two asks whether it has already "
   "been explained as a known pattern; if so it exits to Do not ask again, citing the mower every "
   "month. Step three asks whether there are more than three for one person; if so it exits to A "
   "conversation rather than a list of queries. Step four sends one message weekly with all of "
   "them. Step five records the answers against the records. A note says the second exit is what "
   "keeps this from becoming a weekly irritation."),
  ("h3", "Recording explanations"),
  ("p", "The single most important feature here. When a driver explains that the extra litres go "
        "in the mower can once a month, that explanation is attached to the pattern, and the "
        "query is not raised again next month."),
  ("p", "Without it the system asks the same question repeatedly, the driver correctly concludes "
        "that nobody is reading the answers, and the reply rate collapses. Every recurring query "
        "that is not suppressed after being explained is a small withdrawal from the account that "
        "makes the whole system work."),
  ("h3", "Three or more is a conversation"),
  ("p", "A weekly message with five queries in it reads as an accusation regardless of the "
        "wording. At that point the right action is a two-minute conversation, which usually "
        "reveals something structural: a vehicle that has been reassigned, a card that is being "
        "shared, a route that changed."),
  ("h2", "The rare serious case"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A clear pattern", "sub": ["repeated, deliberate"], "icon": "search"},
      {"title": "Off this system", "sub": ["immediately"], "icon": "stop"},
      {"title": "To a named person", "sub": ["with the raw records"], "icon": "person"},
      {"title": "No automated query", "sub": ["and no batch message"], "icon": "email"},
      {"title": "A process, not a tool", "sub": ["as it should be"], "icon": "doc"}],
    "title": "WHEN IT IS ACTUALLY SERIOUS",
    "note": "A tool that handles this badly is worse than one that does not handle it at all."}),
   "The exit path for the rare genuine case. It leaves the system entirely, which is the correct "
   "behaviour for something that affects somebody's employment.",
   "How a genuinely serious fuel finding is escalated off the system",
   "A horizontal row of five boxes. A clear pattern: repeated and deliberate. Off this system, "
   "immediately. To a named person, with the raw records. No automated query, and no batch "
   "message. A process, not a tool, as it should be. A note says a tool that handles this badly "
   "is worse than one that does not handle it at all."),
  ("p", "The important design point is that the system does not have a fraud workflow, a case "
        "file, or a status for suspicion. Those features invite use, and something that affects "
        "somebody's job should be handled by people with the raw evidence in front of them, not "
        "through a queue."),
  ("p", "What the system does provide is the underlying records, exportable and complete, so that "
        "whoever is handling it is working from facts rather than from a summary the tool "
        "generated."),
  ("h3", "No driver league tables"),
  ("p", "Worth stating as a rule because it will be requested. Ranking drivers by fuel economy "
        "ranks their routes, and publishing that ranking creates pressure to game the one thing "
        "drivers can control, which is the odometer reading they type at the pump."),
  ("p", "That is a genuinely bad outcome: it degrades the data the system depends on in order to "
        "produce a metric that was measuring routes anyway."),
  ("p", "Next: what the fuel data says about the vehicles."),
 ],
},
{
 "slug": "what-the-fuel-data-says-about-the-vehicles",
 "title": "What the fuel data says about the vehicles",
 "nav": "What it says about vehicles",
 "read": 5, "words": 710,
 "desc": ("Slow economy decline as an early maintenance signal, the vehicle doing twice the "
          "mileage, and cost per mile done honestly."),
 "og": ("A van whose economy has fallen eight per cent over four months has something wrong with "
        "it, and fuel data sees it before anything else does."),
 "abstract": ("How gradual economy decline predicts maintenance, the utilisation finding, how "
              "cost per mile should be computed, and what to report."),
 "lede": ("The queries are the visible output and the vehicle findings are the valuable one. Fuel "
          "consumption is a continuous measurement of how hard a vehicle is working to do the "
          "same job, which is as close to a health check as a fleet gets for free."),
 "tags": ["fuel management", "fleet", "maintenance", "cost per mile", "reporting", "serverless"],
 "takeaways": [
  "A sustained economy decline in one vehicle is a maintenance signal, not a driver signal.",
  "Utilisation findings are often larger than efficiency ones.",
  "Cost per mile needs unattributed fuel in it, or it is understated.",
  "Report per vehicle over time, never as a ranked table.",
  "The best outcome is a booked service, not a conversation with anybody.",
 ],
 "blocks": [
  ("h2", "Decline as an early warning"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Jan-Mar", "parts": [("mpg", 34.1)]},
      {"label": "Apr-Jun", "parts": [("mpg", 33.4)]},
      {"label": "Jul-Sep", "parts": [("mpg", 32.0)]},
      {"label": "Oct-Dec", "parts": [("mpg", 30.6)]}],
    "series": [("mpg", "Van 5, miles per gallon, seasonally adjusted", "#8C4FFF")],
    "unit": "",
    "note": "Ten per cent over a year, steadily. Nobody noticed from the driver's seat."}),
   "One vehicle over a year with the seasonal effect removed. A gradual decline of this shape is "
   "invisible day to day and is one of the clearer signals a fleet produces.",
   "One van's seasonally adjusted fuel economy declining over four quarters",
   "A bar chart with four bars showing van five's seasonally adjusted miles per gallon. January "
   "to March: thirty-four point one. April to June: thirty-three point four. July to September: "
   "thirty-two. October to December: thirty point six. A note says that is ten per cent over a "
   "year, steadily, and nobody noticed from the driver's seat."),
  ("p", "Ten per cent of a van's fuel bill is real money, and the causes are usually cheap: "
        "underinflated tyres, a clogged filter, a dragging brake, a sensor that has drifted. All "
        "of them are found at a service and none of them announce themselves."),
  ("p", "The output is therefore a maintenance booking rather than a conversation, which is worth "
        "emphasising because the instinct on seeing declining economy is to look at who has been "
        "driving it. In a fleet with stable driver assignments a slow decline in one vehicle is "
        "almost always the vehicle."),
  ("h2", "Utilisation"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Van 2", "sub": ["24,000 miles"], "icon": "truck", "label": "heavily used"},
      {"title": "Van 6", "sub": ["11,000 miles"], "icon": "truck", "label": "average"},
      {"title": "Van 9", "sub": ["2,400 miles"], "icon": "truck", "label": "barely used"}],
    "target": {"title": "Same fixed costs", "sub": ["insurance, tax,", "depreciation"],
               "icon": "money",
               "then": {"title": "Van 9's cost per mile", "sub": ["is ten times van 2's"],
                        "icon": "chart"}},
    "note": "The efficiency question is usually smaller than the do-we-need-it question."}),
   "Three vehicles by annual mileage. The largest saving available in most small fleets is not "
   "efficiency; it is a vehicle that is not needed.",
   "Three vans with very different annual mileages and the same fixed costs",
   "Three boxes stacked on the left. Van two: twenty-four thousand miles, labelled heavily used. "
   "Van six: eleven thousand miles, labelled average. Van nine: two thousand four hundred miles, "
   "labelled barely used. All three converge on Same fixed costs covering insurance, tax and "
   "depreciation, and that leads down to Van nine's cost per mile is ten times van two's. A note "
   "says the efficiency question is usually smaller than the do-we-need-it question."),
  ("p", "Fuel data reveals this almost as a side effect, because a vehicle that is barely being "
        "fuelled is barely being used. It is often a genuinely uncomfortable finding &mdash; the "
        "spare van that somebody insists is needed for peak weeks &mdash; and it is a question "
        "worth asking with numbers attached."),
  ("h3", "Cost per mile, honestly"),
  ("p", "Two things get left out and both understate it. Unattributed fuel is real fuel and it "
        "belongs in the fleet total even when it cannot be assigned to a vehicle. And fixed costs "
        "&mdash; insurance, tax, depreciation, the maintenance from Day 118 &mdash; are usually "
        "larger than fuel and are frequently reported separately."),
  ("p", "A cost per mile that includes only fuel is a number that makes every vehicle look cheap "
        "and makes the utilisation finding invisible, which is exactly the finding that matters "
        "most."),
  ("h2", "What the report says"),
  ("callout", "The quarterly page", [
   "<strong>Fuel purchased:</strong> &pound;18,400 across 214 transactions.",
   "<strong>Unattributed:</strong> &pound;900, 4.9%, down from 11% last quarter.",
   "<strong>Queries raised:</strong> 19. <strong>Answered:</strong> 17. <strong>Data errors "
   "corrected:</strong> 14 of those.",
   "<strong>Vehicles with a sustained decline:</strong> 1 &mdash; van 5, down 10% over the year, "
   "service booked.",
   "<strong>Utilisation:</strong> van 9 covered 2,400 miles at a fully-loaded cost of "
   "&pound;1.94 per mile.",
   "<strong>No driver rankings appear in this report,</strong> deliberately, and this line stays "
   "here so nobody adds one.",
  ]),
  ("p", "The third line is the honest summary of what this system mostly does: fourteen of "
        "nineteen queries were data errors. That is not a disappointing result, it is the "
        "expected one, and every one of those corrections improves the figures that produce the "
        "fourth and fifth lines."),
  ("p", "The second line is the process metric. Unattributed fuel falling from eleven per cent to "
        "five per cent means the matching and the queries are working, and it is the number that "
        "determines whether anything else on the page can be trusted."),
  ("h3", "The line that stays in the template"),
  ("p", "The last item is a small piece of institutional memory. Somebody will ask for a driver "
        "league table roughly once a year, and a line in the standing report explaining why there "
        "is not one answers the question before it is asked, with the reasoning already written "
        "down."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="transaction",
 volumes=[(150, "150 transactions"), (600, "600 transactions"), (2400, "2,400 transactions")],
 read_each=0.0,
 msgs_each=0.06,
 lede=("There is no model in this system where fuel data arrives as a file, and queries are "
       "batched weekly rather than sent per anomaly. Six hundred transactions a month is a fleet "
       "of about forty vehicles. Here is where each cent goes."),
 takeaway_extra=("Queries are weekly and batched per driver, which is why messaging barely "
                 "appears."),
 risks=[
  "<strong>Recomputing every baseline nightly.</strong> A baseline over ten fills moves slowly. "
  "Recompute on a new fill for that vehicle only.",
  "<strong>Reading receipt images that could be a data feed.</strong> Most card providers offer a "
  "file. Getting on it removes the only model cost in the system.",
  "<strong>Sending a message per anomaly.</strong> Not primarily a cost issue: it is how the "
  "reply rate goes to zero, after which the data stops improving.",
 ],
 per_unit_note=("There is no read line where transactions arrive as a file. Where receipts are "
                "photographed instead, add roughly one read per receipt."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="fl",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the check order, and how explanations are stored."),
 outside=[
  {"title": "Fuel card feed", "sub": ["daily file"], "icon": "money"},
  {"title": "Vehicle records", "sub": ["tanks, assignments"], "icon": "truck"},
  {"title": "Drivers", "sub": ["one weekly message"], "icon": "person"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["feed drop,", "weekly query batch"], "icon": "storage"},
  {"title": "Lambda x3", "sub": ["match, check, query"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["fills, baselines"], "icon": "database"}],
 note="us-east-1. One account. Raw transactions immutable; explanations suppress repeat queries.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The fuel card feed, arriving as a daily "
  "file. Vehicle records, holding tank sizes and assignments. And Drivers, who receive one weekly "
  "message. Inside the account, three groups. S3 receiving the feed drop alongside EventBridge "
  "running a weekly query batch. Three Lambda functions named match, check and query. And two "
  "DynamoDB tables named fills and baselines. A note gives the region as us-east-1, one account, "
  "and states that raw transactions are immutable and that explanations suppress repeat queries."),
 functions=[
  ["<code>fl-match</code>", "S3 put on the feed prefix",
   "Attributes each transaction to a vehicle; validates the odometer against the previous reading",
   "120s / 1024&nbsp;MB"],
  ["<code>fl-check</code>", "DynamoDB stream on fills",
   "Runs impossibility checks, then baseline deviation; looks for a swapped pair",
   "60s / 1024&nbsp;MB"],
  ["<code>fl-query</code>", "EventBridge, weekly",
   "Groups open anomalies by driver, suppresses explained patterns, sends one message",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>fl-match-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:PutItem</code>, <code>dynamodb:Query</code>",
   "The feed prefix; fills; read-only on vehicles"],
  ["<code>fl-check-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>", "Fills and baselines"],
  ["<code>fl-query-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Fills; one verified identity"]],
 tables=[
  ("Table: fills",
   "PK   vehicle_id        S   or 'unattributed'\n"
   "SK   filled_at         S\n"
   "     raw               M   the transaction exactly as received, never edited\n"
   "     card_id           S\n"
   "     litres            N\n"
   "     cost_pence        N\n"
   "     odometer          N   null if not given\n"
   "     odo_status        S   ok | backwards | implausible | absent | repeated\n"
   "     miles_since       N   null unless the previous odometer is usable\n"
   "     mpg               N   null on any of the above\n"
   "     anomaly           S   over_tank | odo | economy | swap_suspected\n"
   "     explanation       S   the driver's answer, verbatim\n"
   "     explained_pattern S   'mower can, monthly' -- suppresses future queries\n\n"
   "`raw` is kept because every downstream number is derived and the feed\n"
   "format changes without notice."),
  ("Table: baselines",
   "PK   vehicle_id        S\n"
   "     n_fills           N   fewer than 10 means no alerts at all\n"
   "     median_mpg        N\n"
   "     spread_mpg        N   a wide normal needs a wider band\n"
   "     by_quarter        M   {2025Q4: 31.2, ...} for seasonal comparison\n"
   "     fleet_delta       N   this quarter's fleet-wide movement, the control\n"
   "     updated_at        S\n\n"
   "The only cross-vehicle number here is `fleet_delta`, and it is a change\n"
   "rather than a level. Levels compare routes; changes compare vehicles.")],
 inbound=[
  "<strong>The card feed arrives daily</strong> as a file into S3. Receipts photographed by "
  "drivers are a secondary path and are the only place a model would be involved.",
  "<strong>Card-to-vehicle assignment is versioned with dates</strong>, so a reassignment does "
  "not retroactively rewrite three months of attribution.",
  "<strong>Impossibility checks run before deviation checks.</strong> An over-tank fill needs no "
  "baseline and can be queried immediately.",
  "<strong>Explanations suppress future queries</strong> on the same pattern. Without this the "
  "reply rate collapses within two months."],
 model_notes=[
  "<strong>There is usually no model in this system.</strong> Every check is arithmetic against a "
  "previous reading or a median.",
  "<strong>The one defensible use</strong> is reading a photographed receipt where no card feed "
  "exists, extracting litres, cost, date and site.",
  "<strong>The wrong use</strong> is scoring drivers or transactions for suspicion. Part 4 is "
  "about why a system that can express suspicion will be used to.",
  "<strong>Classifying free-text explanations</strong> into patterns is defensible, and the "
  "verbatim text is kept because the specifics are what suppress the next query correctly.",
  "<strong>The cost page assumes none</strong>, which is why the bill is almost entirely fixed."],
 gotchas=[
  "Version the card-to-vehicle mapping with dates. A reassignment applied retroactively rewrites "
  "months of attribution and destroys every baseline.",
  "Never compute miles per gallon when the odometer is absent or implausible. A null is correct; "
  "an interpolated figure quietly poisons the baseline.",
  "Store explanations against a pattern, not just against the one record. Asking the same "
  "question every month is how the reply rate reaches zero.",
  "Check for a swapped pair before querying a bad economy figure. Two vehicles anomalous in "
  "opposite directions in one week is one error, not two.",
  "Do not build a driver ranking, a suspicion score, or a case workflow. Features that can "
  "express an accusation will be used to make one."],
))
