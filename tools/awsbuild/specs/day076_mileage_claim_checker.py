"""Day 76 -- 2026-07-09 -- Mileage claim checker."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "mileage-claim-checker"
NAME = "Mileage claim checker"

SPEC = {
 "slug": SLUG, "date": "2026-07-09", "name": NAME,
 "tagline": ("Somebody claims 84 miles to a customer site. The system checks that the trip "
             "happened, that the distance is roughly right, and that it has not been claimed "
             "before -- then pays it or asks one specific question."),
 "lede": ("A small system that takes mileage claims from a phone, checks each one against the "
          "route it says it drove and the trips already claimed that month, pays the ordinary "
          "ones straight through, and puts the odd ones in front of a person with the map "
          "already drawn. It never accuses anybody of anything. It asks a question with a "
          "number in it. Seven posts on the same system -- one diagram at a time -- with a "
          "cost breakdown and an engineering reference at the end."),
 "keywords": ["mileage claims", "expense checking", "field staff", "reimbursement",
              "human in the loop", "serverless"],
 "icons": ["phone", "map", "money"],
 "faq": [
  ("What is a mileage claim checker?",
   "A small serverless system that takes mileage claims from field staff, works out the "
   "expected distance between the addresses claimed, compares it with what was claimed, checks "
   "the trip has not already been paid, and either approves it or asks the claimant one "
   "specific question. A person decides anything the checks flag."),
  ("Does it accuse people of fraud?",
   "No, and the design goes out of its way not to. Almost every odd claim is a typo, a "
   "round-trip counted once, or a detour that really happened. The system asks a neutral "
   "question with the numbers in it -- \"this looks like 41 miles, you claimed 84; was this a "
   "return trip?\" -- and a yes closes it."),
  ("How does it know how far the trip should have been?",
   "It calls a routing service once per claim with the two addresses and stores the answer. "
   "That distance is a reference, not a rule: a tolerance band around it is what decides "
   "whether a claim is ordinary. Roadworks, school runs and site diversions are exactly why "
   "the band is wide."),
  ("What stops the same trip being claimed twice?",
   "Every claim gets a fingerprint from the claimant, the date, and the two addresses rounded "
   "to a small grid. The first write of that fingerprint wins by a conditional write, so a "
   "resubmitted claim lands on the original rather than becoming a second payment."),
  ("What does it cost to run?",
   "A few dollars a month at small-business volume, plus whatever your routing provider "
   "charges per lookup. There is nothing always-on. See part six for the breakdown."),
 ],
}

SPEC["parts"] = [
{
 "slug": "mileage-claim-checker-on-aws",
 "title": "A mileage claim checker on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 950,
 "desc": ("Takes mileage claims from a phone, checks the distance against the route, catches "
          "repeats, pays the ordinary ones and asks one question about the rest. AWS, about "
          "$4 a month."),
 "og": ("Checks each mileage claim against the route it says it drove and the trips already "
        "paid this month, then pays it or asks one specific question with the numbers in it."),
 "abstract": ("The whole system on one page -- a claim intake, a distance check and a router "
              "-- plus the rule that keeps it humane: it asks questions, it never accuses."),
 "lede": ("Mileage is the expense line nobody wants to police. The amounts are small, the "
          "claims are frequent, and checking one properly means opening a map, typing two "
          "addresses, and comparing a number to a number -- for four dollars. So nobody checks "
          "them, and the line quietly grows, and the one person who is rounding up never finds "
          "out that anyone noticed. This post walks through a small system that does the "
          "boring comparison on every claim, pays the ordinary ones without anyone looking, "
          "and turns the odd ones into a single neutral question."),
 "tags": ["mileage claims", "expenses", "field staff", "reimbursement", "human in the loop",
          "serverless"],
 "takeaways": [
  "One way to claim: a phone form with the date, two addresses and a reason. Three taps.",
  "Every claim ends in one of three states: paid, asked about, or waiting on a person.",
  "The expected distance comes from a routing lookup, and it is a reference, not a rule.",
  "The tolerance band is yours, in a sheet. Wide by default, because real driving is untidy.",
  "Designed on AWS for about $4 a month at typical small-business volume.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Claim from a phone", "sub": ["date, two addresses"], "icon": "phone"},
      {"title": "Routing service", "sub": ["expected distance"], "icon": "map"},
      {"title": "Approver", "sub": ["sees only the odd ones"], "icon": "person"}],
    "inside": [
      {"title": "Intake", "sub": ["one claim record,", "addresses cleaned"], "icon": "form"},
      {"title": "Checker", "sub": ["distance, repeats,", "monthly pattern"], "icon": "filter"},
      {"title": "Router", "sub": ["pay, ask, or", "send to a person"], "icon": "branch"}],
    "edges": [{"from": 0, "to": 0, "label": "claims in"},
              {"from": 1, "to": 1, "label": "expected miles"},
              {"from": 2, "to": 2, "label": "only the odd ones", "up": True}],
    "note": "Most claims are ordinary and nobody sees them. That is the point."}),
   "Three things outside the account, three pieces inside it. Claims arrive from a phone form, "
   "a routing service supplies the expected distance, and only the claims that fall outside "
   "the band ever reach a person.",
   "System: a phone claim, a routing lookup, three pieces inside AWS",
   "Three boxes across the top sit outside the AWS account. On the left, Claim from a phone: a "
   "short form with the date and two addresses. In the middle, Routing service: an external "
   "API that returns the expected driving distance between two addresses. On the right, "
   "Approver: the person who sees only the claims that fall outside the tolerance band. Each "
   "connects by an arrow to the AWS account container below. Claims flow down into the "
   "account. The routing service supplies the expected mileage. The approver receives only the "
   "odd ones. Inside the AWS account are three components in a row. On the left, the Intake, "
   "which turns each submission into one claim record with the addresses cleaned and "
   "normalised. In the middle, the Checker, which compares the claimed distance with the "
   "expected one, looks for the same trip already claimed, and looks at the claimant's pattern "
   "for the month. On the right, the Router, which pays the ordinary ones, asks a single "
   "question about the borderline ones, and sends the rest to a person. A note at the bottom "
   "says most claims are ordinary and nobody sees them, and that this is the point."),
  ("h3", "What you set up once (the outside)"),
  ("ul", [
   "<strong>A claim form.</strong> Three taps on a phone: the date, where from, where to, and "
   "a one-line reason. Covered in Part 2. No app to install &mdash; a web form on a saved "
   "home-screen link, because the alternative is a photo of a handwritten sheet at month end.",
   "<strong>A routing lookup.</strong> Any provider that turns two addresses into a driving "
   "distance. This is the only paid third party in the design, it is called at most once per "
   "claim, and the answer is cached forever against that address pair, because the distance "
   "between two fixed places does not change.",
   "<strong>A tolerance sheet.</strong> One tab: the band around the expected distance that "
   "counts as ordinary, the monthly total above which a person always looks, and the "
   "per-mile rate. The band is deliberately wide &mdash; a default of plus fifty per cent "
   "&mdash; because real trips include getting lost, roadworks, and dropping something off on "
   "the way.",
  ]),
  ("h3", "What runs on every claim (the inside)"),
  ("ul", [
   "<strong>The intake.</strong> Cleans the two addresses into something a routing service "
   "will accept, which is most of the work. \"the Henderson site\" is not an address; the "
   "intake matches it against the customer list first, and only asks the claimant if it "
   "genuinely cannot resolve it. It also assigns the claim a fingerprint so a resubmission "
   "cannot become a second payment.",
   "<strong>The checker.</strong> Three comparisons, none of them clever. Is the claimed "
   "distance inside the band around the expected one? Has this same trip already been claimed "
   "this month? Is this claimant's month unusual against their own history &mdash; not against "
   "anybody else's? The third is the one that catches real problems, and it is also the one "
   "most likely to be wrong, so it never blocks a payment on its own.",
   "<strong>The router.</strong> Inside the band and not a repeat: pay it, log it, tell "
   "nobody. Outside the band: reply to the claimant with the two numbers and one question. "
   "Repeat, or a month well outside their pattern: send it to a person with both claims side "
   "by side. Nothing is rejected by the system, ever.",
  ]),
  ("h2", "One claim, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Claimed", "sub": ["three taps, a phone"], "icon": "phone"},
      {"title": "Resolved", "sub": ["two real addresses"], "icon": "map"},
      {"title": "Compared", "sub": ["claimed vs expected"], "icon": "counter"},
      {"title": "Decided", "sub": ["pay, ask, or escalate"], "icon": "branch"},
      {"title": "Paid", "sub": ["and on the month's total"], "icon": "money"}],
    "title": "ONE MILEAGE CLAIM, END TO END",
    "note": "Four of the five stages happen without anybody being interrupted."}),
   "The same system as one line. A claim is made, the addresses are resolved, the distance is "
   "compared, a decision is taken, and the money moves &mdash; usually without anyone looking.",
   "One mileage claim from submission to payment, in five stages",
   "A horizontal row of five boxes joined by arrows. Claimed: three taps on a phone form. "
   "Resolved: the two addresses are turned into real, routable addresses. Compared: the "
   "claimed distance is set against the expected one. Decided: pay, ask a question, or "
   "escalate to a person. Paid: the amount is approved and added to the claimant's monthly "
   "total. A note says four of the five stages happen without anybody being interrupted."),
  ("h2", "In plain words"),
  ("p", "Your engineer finishes at a customer in Ashford and drives to one in Maidstone. That "
        "evening he opens the saved link on his phone, taps today's date, picks both sites "
        "from the recent list, types \"call-out, boiler\", and submits. The intake resolves "
        "both sites to their postcodes from the customer list. The routing lookup says 27 "
        "miles. He claimed 29. The band is plus or minus fifty per cent, so 29 is comfortably "
        "ordinary. It is paid, added to his month, and nobody is told. Elapsed time: about "
        "eleven seconds, and he is the only person who spent any of it."),
  ("p", "The following week he claims 84 miles for a trip the routing service thinks is 41. "
        "That is outside the band, so instead of paying or refusing, the system replies: "
        "\"This route looks like about 41 miles and you claimed 84 &mdash; was this a return "
        "trip?\" He taps yes. It is paid. The entire exchange took him four seconds and it "
        "never reached you. That is the difference between a checker and an audit: the checker "
        "asks the question the auditor would have asked, immediately, of the one person who "
        "already knows the answer."),
  ("callout", "Design rules that shaped every decision", [
   "It asks, it does not accuse. Every out-of-band claim gets a neutral question with both "
   "numbers in it, and a one-tap answer that closes it.",
   "The expected distance is a reference, not a rule. Real driving is untidy and the band is "
   "wide by default.",
   "Compare a person against their own history, never against a colleague's. Rounds are "
   "different, patches are different, lives are different.",
   "One trip, one payment. A fingerprint on claimant, date and both endpoints makes a "
   "resubmission land on the original claim.",
   "The routing answer is cached forever. Two fixed addresses do not move, and paying twice "
   "for the same lookup is just waste.",
   "Nothing is ever rejected by the system. The worst outcome is a person looking at it.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The two usual approaches both fail in the same way. Either nobody checks, and the "
        "line grows until somebody notices at year end and then everybody gets a stern email "
        "including the twelve people who were scrupulous. Or somebody checks all of them, "
        "which costs more in their time than the entire mileage budget and makes every "
        "claimant feel suspected."),
  ("p", "The shape above does the arithmetic on every single claim, which no human will, and "
        "then does almost nothing with the result. Ninety per cent of claims are paid silently. "
        "Most of the rest are closed by the claimant in one tap. What reaches you is the "
        "handful that are genuinely worth two minutes &mdash; and it reaches you with the map "
        "already drawn and both numbers on the screen."),
  ("p", "The next four posts walk through each piece: how a claim arrives, how the distance "
        "gets checked, how a question reaches the claimant, and how a payment gets recorded. "
        "One diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-mileage-claim-arrives",
 "title": "How a mileage claim arrives",
 "nav": "How it arrives",
 "read": 6, "words": 900,
 "desc": ("A three-tap phone form, why there is no app, how \"the Henderson site\" becomes a "
          "postcode, and the fingerprint that stops a resubmitted claim becoming a second "
          "payment."),
 "og": ("One lane, deliberately. A phone form with a recent-sites list, address resolution "
        "against the customer record, and a conditional write that makes resubmission safe."),
 "abstract": ("One lane, on purpose: a phone form with three taps. How a site name becomes a "
              "routable address, what happens when it cannot, and the fingerprint that makes "
              "a resubmitted claim land on the original."),
 "lede": ("The last system had three ways in. This one has exactly one, and the reason is "
          "worth stating plainly: mileage is claimed by people standing next to a van at six "
          "in the evening. Anything that needs a laptop will be done at month end from memory, "
          "and a claim from memory is a guess. So the entire intake design is in service of "
          "one number: how many seconds it takes to file a claim on a phone."),
 "tags": ["mileage claims", "mobile forms", "address resolution", "idempotency", "DynamoDB",
          "serverless"],
 "takeaways": [
  "One lane: a web form on a home-screen link. No app, no store, no login screen.",
  "Three taps, because the recent-sites list covers most trips and the date defaults to today.",
  "Site names resolve against the customer list before any routing call is made.",
  "An address that cannot be resolved is a question, not a rejection.",
  "A fingerprint on claimant, date and both endpoints makes a resubmission safe.",
 ],
 "blocks": [
  ("h2", "One lane, on purpose"),
  ("p", "Every extra channel is another shape to parse and another way for the same trip to be "
        "claimed twice. Mileage does not need an email lane: nobody writes prose about a "
        "journey. It needs the shortest possible path from standing beside a van to a submitted "
        "claim."),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Recent sites", "sub": ["last 10, one tap each"], "icon": "map", "label": "tap"},
      {"title": "Customer search", "sub": ["type three letters"], "icon": "search",
       "label": "pick"},
      {"title": "Free text", "sub": ["an address, typed"], "icon": "form", "label": "type"}],
    "target": {"title": "One claim record", "sub": ["date, from, to,", "reason, claimant"],
               "icon": "database",
               "then": {"title": "Resolver", "sub": ["to postcodes, or a question"],
                        "icon": "model"}},
    "note": "Three ways to name a place, one shape of claim. The first covers most trips."}),
   "The form's three ways to name a place, all producing the same claim record. The recent-"
   "sites list is not a convenience feature; it is what makes the whole thing a three-tap job.",
   "Three ways to name a place, converging on one claim record",
   "Three boxes stacked on the left. Recent sites: the claimant's last ten destinations, one "
   "tap each. Customer search: type three letters and pick from the customer list. Free text: "
   "an address typed in full. Each has an arrow labelled tap, pick and type respectively, "
   "converging on One claim record on the right, holding the date, the from, the to, the "
   "reason and the claimant. Below it, connected by a downward arrow, is the Resolver, which "
   "turns each end into a postcode or raises a question. A note says three ways to name a "
   "place, one shape of claim, and that the first covers most trips."),
  ("h3", "Why the recent list matters more than it looks"),
  ("p", "Field staff visit the same places. A plumber's ten most recent destinations cover "
        "perhaps seventy per cent of next week's trips, and a maintenance engineer on a "
        "contract round is closer to ninety. So the form opens with those ten as buttons, "
        "sorted by how recently they were used, and the common case is: tap yesterday's site, "
        "tap today's, tap submit."),
  ("p", "That is not a nicety. A claim filed the same evening is a claim filed from the odometer "
        "and the day, which is accurate. A claim filed on the 31st for the whole month is filed "
        "from a diary and a memory, which is not. Most of what a mileage checker catches is not "
        "dishonesty; it is the accumulated drift of people reconstructing four weeks of driving "
        "on a Sunday night."),
  ("h2", "Turning a place into an address"),
  ("p", "The routing service needs something routable. People type \"Henderson\", \"the "
        "Henderson site\", \"Henderson Ltd, unit 4\", and occasionally just \"job 4471\". "
        "Resolution runs in a fixed order, and it stops at the first confident answer."),
  ("fig", ("chain", {
    "entry": {"title": "Claim submitted", "sub": ["from the phone form"], "icon": "phone"},
    "steps": [
      {"title": "Seen this trip?", "sub": ["claimant + date + ends"], "icon": "branch",
       "side": {"title": "DynamoDB claims", "sub": ["conditional write"], "icon": "database"},
       "exit": {"title": "Same claim", "sub": ["show the original"], "icon": "stop",
                "label": "resubmit"}},
      {"title": "Known place?", "sub": ["customer list, job list"], "icon": "search",
       "side": {"title": "Customer records", "sub": ["names and postcodes"], "icon": "doc"}},
      {"title": "Still ambiguous?", "sub": ["two candidates or none"], "icon": "branch",
       "exit": {"title": "Ask the claimant", "sub": ["pick from a short list"], "icon": "person",
                "label": "unclear"}},
      {"title": "Cached distance?", "sub": ["this pair, ever"], "icon": "branch",
       "side": {"title": "DynamoDB routes", "sub": ["address pair -> miles"], "icon": "database"},
       "exit": {"title": "Routing lookup", "sub": ["one call, then cached"], "icon": "external",
                "label": "miss"}},
      {"title": "Hand to the checker", "sub": ["claimed and expected"], "icon": "queue"}],
    "note": "The duplicate test is first and the routing lookup is last, so a resubmission costs nothing."}),
   "One claim, end to end. The duplicate test runs before anything is spent, place names are "
   "resolved against records you already keep, and the paid routing lookup only happens on a "
   "genuinely new address pair.",
   "How a submitted claim becomes a checked pair of distances",
   "A vertical chain of five steps inside the AWS account, entered from a box labelled Claim "
   "submitted from the phone form. Step one asks whether this trip has been seen before, "
   "fingerprinting the claimant, the date and both endpoints and writing conditionally to a "
   "DynamoDB claims table; a resubmission exits to Same claim, which shows the original. Step "
   "two asks whether each end is a known place, matching against customer and job records. "
   "Step three asks whether anything is still ambiguous, exiting to Ask the claimant with a "
   "short list to pick from. Step four asks whether the distance for this address pair is "
   "already cached in a DynamoDB routes table; a miss exits to a single Routing lookup which "
   "is then cached. Step five hands the claimed and expected distances to the checker. A note "
   "says the duplicate test is first and the routing lookup last, so a resubmission costs "
   "nothing."),
  ("h3", "Why the routing lookup is last"),
  ("p", "It is the only line on the bill that is charged by a third party, and it is the only "
        "step that can be skipped entirely. The distance between two fixed postcodes is a "
        "constant, so the first time anyone claims Ashford to Maidstone it costs one lookup, "
        "and every claim for that pair afterwards costs nothing forever. On a business with a "
        "regular round, the cache hit rate settles above ninety per cent within a month."),
  ("p", "Putting the duplicate test first has the same shape of benefit. A claimant who taps "
        "submit twice on a bad signal generates two requests, and the second must not pay for "
        "a routing lookup, let alone create a second claim."),
  ("h2", "What the resolver refuses to guess"),
  ("ul", [
   "<strong>Two candidates is not a match.</strong> If \"Henderson\" matches both Henderson "
   "Plant and Henderson Motors, the claimant gets both as buttons. Picking the wrong one "
   "produces a wrong distance, which produces a wrong question, which wastes everybody's time.",
   "<strong>A postcode from a job number is fine.</strong> If the reason field contains a job "
   "reference and that job has a site address, that is a confident match, and it is the one "
   "case where the system fills something in that the claimant did not type.",
   "<strong>A home address is never inferred.</strong> Home-to-first-site is a policy question "
   "with tax consequences, and the sheet decides whether it counts. The system never quietly "
   "adds or removes it.",
   "<strong>A place that resolves to nothing stays as typed.</strong> The claim is still made, "
   "still recorded, and simply goes to a person &mdash; because a claim that cannot be "
   "auto-checked is not a suspicious claim, it is an unusual address.",
  ]),
  ("p", "Next: the three comparisons the checker actually makes, and why the third one never "
        "blocks a payment on its own."),
 ],
},
{
 "slug": "how-a-mileage-claim-gets-checked",
 "title": "How a mileage claim gets checked",
 "nav": "How it gets checked",
 "read": 6, "words": 920,
 "desc": ("Three comparisons -- the distance band, the repeat test, and the claimant's own "
          "monthly pattern -- and why the third one never blocks a payment by itself."),
 "og": ("A wide band around the expected distance, a repeat test on the trip, and a pattern "
        "check against the claimant's own history. Two of the three can pay a claim; only a "
        "person can stop one."),
 "abstract": ("A wide band around the expected distance, a repeat test on the same trip, and "
              "a comparison against the claimant's own months. The third never blocks a "
              "payment on its own, and the reason is the whole design."),
 "lede": ("The checker has one job and one temptation. The job is to compare a claimed number "
          "with an expected one and notice when they are far apart. The temptation is to get "
          "clever &mdash; to score claimants, to build a model of normal driving, to flag "
          "people. This post is mostly about the three comparisons it does make, and partly "
          "about the ones it deliberately does not."),
 "tags": ["mileage claims", "tolerance bands", "anomaly detection", "fairness", "DynamoDB",
          "serverless"],
 "takeaways": [
  "The band is wide -- plus fifty per cent by default -- because real driving includes detours.",
  "A repeat is the same claimant, same day, same two endpoints on a small grid.",
  "The pattern check compares a person with their own history, never with a colleague's.",
  "Only two checks can pay a claim. None of them can refuse one; that is a person's job.",
  "Every answer carries its numbers, so the question the claimant sees writes itself.",
 ],
 "blocks": [
  ("h2", "Three comparisons, in order"),
  ("fig", ("chain", {
    "entry": {"title": "Resolved claim", "sub": ["claimed and expected"], "icon": "map"},
    "steps": [
      {"title": "Inside the band?", "sub": ["expected +/- tolerance"], "icon": "branch",
       "side": {"title": "Tolerance sheet", "sub": ["band, caps, rate"], "icon": "chart"},
       "exit": {"title": "Ask the claimant", "sub": ["both numbers, one question"],
                "icon": "person", "label": "outside"}},
      {"title": "Claimed before?", "sub": ["same day, same ends"], "icon": "branch",
       "side": {"title": "DynamoDB claims", "sub": ["fingerprint index"], "icon": "database"},
       "exit": {"title": "Show both", "sub": ["person decides"], "icon": "stop",
                "label": "repeat"}},
      {"title": "Usual for them?", "sub": ["vs their own months"], "icon": "counter",
       "exit": {"title": "Flag, do not block", "sub": ["pay, and note it"], "icon": "bell",
                "label": "unusual"}},
      {"title": "Ordinary claim", "sub": ["pay it, tell nobody"], "icon": "check"}],
    "note": "The first two can send a claim to a human. The third can only add a note to it."}),
   "The three comparisons in order. The distance band and the repeat test can each route a "
   "claim to a person; the pattern check can only annotate one, and that asymmetry is "
   "deliberate.",
   "The three checks a mileage claim passes through",
   "A vertical chain of four steps entered by a box labelled Resolved claim, carrying both the "
   "claimed and expected distances. Step one asks whether the claim is inside the tolerance "
   "band read from the tolerance sheet; if outside it exits to Ask the claimant, sending both "
   "numbers and one question. Step two asks whether the same trip has been claimed before on "
   "the same day, using a fingerprint index on the DynamoDB claims table; a repeat exits to "
   "Show both, where a person decides. Step three asks whether the claim is usual for this "
   "claimant against their own previous months; an unusual result exits to Flag but do not "
   "block, which pays the claim and adds a note. Step four is Ordinary claim, paid without "
   "telling anyone. A note says the first two checks can send a claim to a human and the third "
   "can only add a note."),
  ("h3", "The band, and why it is so wide"),
  ("p", "The default tolerance is plus fifty per cent and minus twenty. That sounds absurdly "
        "loose until you drive for a living. A return trip claimed as one leg doubles the "
        "number. A closed motorway junction adds nine miles. Picking up a part on the way adds "
        "six. Dropping a colleague home adds four. None of those is a false claim, and a band "
        "tight enough to catch the one dishonest claim would generate a question on a third of "
        "the honest ones."),
  ("p", "A checker that asks too many questions gets ignored, and an ignored checker is worse "
        "than no checker because it also carries the implication that everybody is being "
        "watched. The band is set so that a normal month produces zero questions for a normal "
        "claimant. If it produces more than about one question per person per month, the band "
        "is wrong, and the sheet is where you widen it."),
  ("h3", "What counts as a repeat"),
  ("p", "Same claimant, same date, and both endpoints falling in the same small grid square. "
        "The grid matters: \"Unit 4 Henderson\" and \"Henderson Plant, Ashford\" are the same "
        "place typed two ways, and comparing raw strings would miss it while comparing exact "
        "coordinates would too. Rounding to roughly a hundred metres makes them equal without "
        "making genuinely different sites on one industrial estate equal."),
  ("p", "A repeat never auto-refuses. Legitimate repeats exist &mdash; two separate call-outs "
        "to the same site in one day is an ordinary Tuesday for a plumber. So both claims go to "
        "a person, side by side, with their two reason lines, and \"yes, twice\" takes one tap."),
  ("h2", "The pattern check, and its limits"),
  ("p", "The third comparison is the only one with any statistics in it, and it is deliberately "
        "the weakest. It takes the claimant's total for the month and compares it with their "
        "own previous months &mdash; not with the team's, not with a per-role average, not with "
        "anything that would let one person's territory make another look bad."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Their months", "sub": ["last six, same person"], "icon": "chart"},
      {"title": "This month", "sub": ["running total"], "icon": "counter"},
      {"title": "Gap", "sub": ["how far outside"], "icon": "search"},
      {"title": "Note", "sub": ["attached, not acted on"], "icon": "log"},
      {"title": "Month end", "sub": ["one summary, one person"], "icon": "report"}],
    "title": "WHAT THE PATTERN CHECK ACTUALLY DOES",
    "note": "It never stops a payment. It writes a line that a person reads once a month."}),
   "The pattern check's whole output is a note and a monthly summary. Nothing about it is "
   "allowed to hold up a payment to somebody who drove somewhere for you.",
   "What the pattern check produces, in five stages",
   "A horizontal row of five boxes. Their months: the claimant's own last six months. This "
   "month: their running total. Gap: how far outside their own range this month is. Note: the "
   "finding is attached to the claim rather than acted on. Month end: one summary read by one "
   "person. A note says it never stops a payment and only writes a line that a person reads "
   "once a month."),
  ("p", "The reason for that restraint is simple. A month that is double the usual is almost "
        "always a real cause &mdash; a big job the other side of the county, cover for somebody "
        "on leave, a fortnight of emergency call-outs. Holding up somebody's four hundred "
        "pounds of legitimate mileage while a manager works that out is a bad trade against the "
        "rare month where the number is wrong. Pay it, note it, and let the summary do its work "
        "in a meeting rather than in a payment queue."),
  ("callout", "What the checker deliberately does not do", [
   "It does not score claimants. There is no trust rating, no history multiplier, and nothing "
   "that makes last month's question affect this month's claim.",
   "It does not compare people with each other. Territories, rounds and job types are not "
   "comparable and pretending otherwise punishes whoever has the worst patch.",
   "It does not read GPS. If you already track vehicles, that is a better source and a "
   "different system with a different consent conversation attached to it.",
   "It does not refuse anything. The strongest thing it can do is put a claim in front of a "
   "person with the numbers already on the screen.",
  ]),
  ("p", "Next: what the question to the claimant actually looks like, and why it has to be "
        "answerable in one tap."),
 ],
},
{
 "slug": "how-a-question-reaches-the-claimant",
 "title": "How a question reaches the claimant",
 "nav": "How it asks",
 "read": 5, "words": 880,
 "desc": ("One message, both numbers, three buttons. Why the question goes to the claimant "
          "before it goes to a manager, and what happens when nobody answers."),
 "og": ("The claimant is asked first, not the manager. One message with both numbers and "
        "three one-tap answers closes almost every out-of-band claim without anyone else "
        "being involved."),
 "abstract": ("The claimant is asked first, not the manager. One message, both numbers, three "
              "buttons -- return trip, detour, or a typo -- and only silence escalates."),
 "lede": ("Every expense system eventually has to ask somebody a question, and almost all of "
          "them ask the wrong person. They route the odd claim to a manager, who does not know "
          "why the trip was long, who then asks the claimant, who answers, who tells the "
          "manager, who approves it. Three people, two days. The person who knows the answer "
          "was in the loop the whole time and was asked last. This post is about asking them "
          "first."),
 "tags": ["mileage claims", "notifications", "Amazon SES", "escalation", "human in the loop",
          "serverless"],
 "takeaways": [
  "The claimant is asked first. A manager only sees a claim if the claimant does not answer.",
  "The message carries both numbers and the route, so the question answers itself half the time.",
  "Three buttons cover almost everything: return trip, detour, or I typed it wrong.",
  "\"I typed it wrong\" corrects the claim rather than rejecting it. Nobody is made to refile.",
  "Silence escalates on a schedule: a nudge at 48 hours, a manager at five days.",
 ],
 "blocks": [
  ("h2", "Ask the person who knows"),
  ("fig", ("system", {
    "outside": [
      {"title": "Claimant", "sub": ["knows why it was long"], "icon": "person"},
      {"title": "Route map", "sub": ["static image, one call"], "icon": "map"},
      {"title": "Manager", "sub": ["only after silence"], "icon": "team"}],
    "inside": [
      {"title": "Question builder", "sub": ["both numbers,", "three answers"], "icon": "doc"},
      {"title": "Send and sign", "sub": ["single-use links,", "SES out"], "icon": "email"},
      {"title": "Escalator", "sub": ["nudge, then a manager"], "icon": "clock"}],
    "edges": [{"from": 0, "to": 0, "label": "one tap back", "up": True},
              {"from": 1, "to": 1, "label": "the drawn route"},
              {"from": 2, "to": 2, "label": "only if unanswered", "up": True}],
    "note": "Most out-of-band claims are closed by the claimant in under ten seconds."}),
   "Who gets asked, and in what order. The claimant is the first and usually the only person "
   "involved; the manager exists in this diagram mainly as the thing that happens when nobody "
   "replies.",
   "How a question about a mileage claim reaches the person who can answer it",
   "Three boxes across the top outside the AWS account. The Claimant, who knows why the trip "
   "was long. A Route map, a static image fetched with one call. And the Manager, who is "
   "involved only after silence. Inside the account, three components. The Question builder, "
   "which composes a message with both numbers and three possible answers. Send and sign, "
   "which mints single-use links and sends through Amazon SES. And the Escalator, which nudges "
   "and then brings in a manager. Arrows show the claimant answering with one tap, the route "
   "map feeding in, and the manager being reached only if the claim is unanswered. A note says "
   "most out-of-band claims are closed by the claimant in under ten seconds."),
  ("h2", "What the message says"),
  ("callout", "The whole message, in order", [
   "<strong>Line one.</strong> The trip, plainly. \"Tuesday 14th, Ashford to Maidstone, "
   "call-out.\"",
   "<strong>Line two.</strong> Both numbers, in that order. \"This route looks like about 41 "
   "miles. You claimed 84.\"",
   "<strong>The map.</strong> A small static image of the route, so the question is often "
   "answered by looking rather than thinking.",
   "<strong>Three buttons.</strong> \"It was a return trip.\" \"There was a detour &mdash; "
   "here's why.\" \"I typed it wrong &mdash; it was ___.\"",
   "<strong>Nothing else.</strong> No claim reference in the subject line, no portal link, no "
   "policy reminder, and no sentence containing the word compliance.",
  ]),
  ("p", "The tone is doing real work there. \"This route looks like about 41 miles\" concedes "
        "that the system might be wrong, which it often is. \"Your claim exceeds the permitted "
        "variance\" does not, and the difference in how people respond to those two sentences "
        "over a year is larger than anything else in this design."),
  ("h3", "The three buttons, and why they are those three"),
  ("ul", [
   "<strong>Return trip.</strong> By some distance the most common cause. One tap doubles the "
   "expected distance, re-runs the band, and pays it. No manager, no note, no record that "
   "anything was ever odd.",
   "<strong>Detour, with a reason.</strong> Opens a one-line box. The reason is stored on the "
   "claim and the claim is paid immediately &mdash; the reason is for the record, not for "
   "approval. A person who has to wait for their detour to be approved will stop mentioning "
   "detours.",
   "<strong>I typed it wrong.</strong> Opens a number box, pre-filled with the expected "
   "distance. The claim is corrected in place and paid. Nobody is made to delete and refile, "
   "because refiling is how claims get abandoned and abandoned claims become resentment.",
  ]),
  ("h2", "What happens when nobody answers"),
  ("p", "Silence is the interesting case, and it is almost never dishonesty. It is a phone in "
        "a van, a person on annual leave, an email address that goes to a device nobody opens. "
        "So the escalation is slow, and it never turns into an accusation."),
  ("fig", ("chain", {
    "steps": [
      {"title": "Asked, waiting", "sub": ["timer set for 48h"], "icon": "clock"},
      {"title": "Still waiting?", "sub": ["at 48 hours"], "icon": "branch",
       "exit": {"title": "Nudge by SMS", "sub": ["one line, same links"], "icon": "phone",
                "label": "yes"}},
      {"title": "Still waiting?", "sub": ["at five days"], "icon": "branch",
       "side": {"title": "Their manager", "sub": ["from the staff sheet"], "icon": "team"},
       "exit": {"title": "Ask the manager", "sub": ["claimant CC'd"], "icon": "email",
                "label": "yes"}},
      {"title": "Still waiting?", "sub": ["at month end"], "icon": "branch",
       "exit": {"title": "Carry it forward", "sub": ["never expire a claim"], "icon": "log",
                "label": "yes"}},
      {"title": "Answered", "sub": ["paid, corrected or noted"], "icon": "check"}],
    "note": "An unanswered claim is carried, never cancelled. People are owed money for driving."}),
   "The escalation ladder. Two days buys an SMS nudge, five days brings in a manager, and month "
   "end carries the claim forward rather than cancelling it.",
   "What happens to a mileage question that nobody answers",
   "A vertical chain of five steps. First, Asked and waiting, with a timer set for forty-eight "
   "hours. Second, at forty-eight hours, still waiting, exiting to Nudge by SMS with one line "
   "and the same links. Third, at five days, still waiting, which pulls the claimant's manager "
   "from the staff sheet and exits to Ask the manager with the claimant copied in. Fourth, at "
   "month end, still waiting, which exits to Carry it forward, because a claim is never "
   "expired. Fifth, Answered, meaning paid, corrected or noted. A note says an unanswered claim "
   "is carried and never cancelled, because people are owed money for driving."),
  ("p", "That last step matters more than it looks. Plenty of expense systems expire unanswered "
        "claims at period end, on the reasonable-sounding grounds that the books have to close. "
        "What that actually does is take money off somebody who drove eighty miles for you and "
        "did not check an email. The claim is carried, it appears on the next month, and it "
        "keeps appearing until a human resolves it in one direction or the other."),
  ("p", "Next: what happens when a claim is finally approved &mdash; the payment record, the "
        "monthly total, and the one report that makes this worth running."),
 ],
},
{
 "slug": "how-a-mileage-payment-gets-recorded",
 "title": "How a mileage payment gets recorded",
 "nav": "How it pays",
 "read": 5, "words": 860,
 "desc": ("The payment record, the running monthly total, the export your payroll actually "
          "wants, and the one report that makes the whole system worth running."),
 "og": ("What a paid claim leaves behind: an immutable record with the numbers the decision "
        "was made against, a running monthly total, and a payroll export that is one file."),
 "abstract": ("What a paid claim leaves behind: an immutable record holding the numbers the "
              "decision was made against, a running monthly total per claimant, and a one-file "
              "payroll export."),
 "lede": ("This system does not move money. It decides what is owed and writes it down, and "
          "then hands a file to whatever already pays people. That boundary is deliberate: "
          "payroll is a solved problem with regulatory weight attached to it, and the fastest "
          "way to make a small useful system into a large frightening one is to have it touch "
          "a bank account."),
 "tags": ["mileage claims", "payroll export", "DynamoDB", "audit trail", "reporting",
          "serverless"],
 "takeaways": [
  "The system decides what is owed. Payroll pays it. That boundary never moves.",
  "Every payment record stores the numbers the decision was made against, not just the outcome.",
  "The monthly total is a conditional increment, so two claims landing together cannot both win.",
  "The payroll export is one CSV per period, regenerable, and identical every time.",
  "The month-end report is three numbers and a list, and it is the reason to run any of this.",
 ],
 "blocks": [
  ("h2", "What a paid claim leaves behind"),
  ("fig", ("chain", {
    "entry": {"title": "Claim approved", "sub": ["auto, or by a person"], "icon": "check"},
    "steps": [
      {"title": "Still unpaid?", "sub": ["conditional status write"], "icon": "branch",
       "side": {"title": "DynamoDB claims", "sub": ["status = open"], "icon": "database"},
       "exit": {"title": "Already paid", "sub": ["show the record"], "icon": "stop",
                "label": "second tap"}},
      {"title": "Write the payment", "sub": ["miles, rate, basis"], "icon": "money",
       "side": {"title": "Rate from the sheet", "sub": ["at the claim date"], "icon": "chart"}},
      {"title": "Add to the month", "sub": ["claimant + period"], "icon": "counter",
       "side": {"title": "DynamoDB totals", "sub": ["conditional increment"], "icon": "database"}},
      {"title": "Tell the claimant", "sub": ["amount and when"], "icon": "email"},
      {"title": "In the next export", "sub": ["one CSV, one period"], "icon": "report"}],
    "note": "The rate is stamped at the claim date, so a rate change never rewrites history."}),
   "What happens after approval. The payment is written once, the monthly total moves under a "
   "condition, and the claim joins the next payroll export.",
   "The sequence from an approved claim to a payroll line",
   "A vertical chain of five steps entered by a box labelled Claim approved, either "
   "automatically or by a person. Step one asks whether the claim is still unpaid using a "
   "conditional status write against the DynamoDB claims table; a second tap exits to Already "
   "paid, which shows the record. Step two writes the payment, capturing the miles, the rate "
   "read from the sheet as at the claim date, and the basis. Step three adds the amount to the "
   "claimant's monthly total with a conditional increment on a DynamoDB totals table. Step four "
   "tells the claimant the amount and when they will see it. Step five includes the claim in "
   "the next export, one CSV per period. A note says the rate is stamped at the claim date so a "
   "rate change never rewrites history."),
  ("h3", "Why the rate is stamped, not looked up"),
  ("p", "Mileage rates change, usually in April, usually with a week's notice. A system that "
        "computes the amount at export time by reading today's rate will quietly restate every "
        "unpaid claim from before the change, and the first anyone knows about it is a claimant "
        "who is nine pounds short. So the rate is read once, at approval, and written into the "
        "payment record next to the miles."),
  ("p", "The same reasoning applies to the tolerance band and the caps. The <code>basis</code> "
        "field stores what the rules were when the decision was made. It is three extra fields "
        "and it is the difference between an audit trail and a list of outcomes."),
  ("h2", "The payment record"),
  ("table", ["Field", "Example", "Why it is there"], [
   ["<code>claim_id</code>", "clm_2026_07_09_a3d1", "Links to the submission and any question asked"],
   ["<code>claimant</code>", "sam@example.com", "Who is owed"],
   ["<code>trip_date</code>", "2026-07-07", "Not the claim date; the driving date"],
   ["<code>miles</code>", "84.0", "As finally agreed, after any correction"],
   ["<code>rate</code>", "0.45", "Stamped at approval, never re-read"],
   ["<code>amount</code>", "37.80", "miles x rate, computed once"],
   ["<code>basis</code>", "expected 41, band +50%, return trip", "Why this was allowed"],
   ["<code>resolved_by</code>", "claimant / auto / manager", "Who closed it, if anyone had to"],
   ["<code>period</code>", "2026-07", "Which export it belongs to"],
   ["<code>state</code>", "payable", "payable, exported, or reversed"],
  ]),
  ("h2", "The export"),
  ("p", "One CSV per period, with one row per payable claim and a column layout your payroll "
        "software already accepts. It is generated on demand rather than on a schedule, and "
        "generating it twice produces a byte-identical file, because the period boundary is a "
        "date and not \"everything since I last ran this\"."),
  ("p", "Once a period is exported, its claims move to <code>exported</code> and become "
        "read-only. A claim that arrives late for a closed period does not reopen it; it lands "
        "in the current period with its true trip date, which is what every payroll system "
        "expects anyway."),
  ("h2", "The report that justifies the whole thing"),
  ("p", "Everything above is plumbing. This is the output that makes it worth building."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Claimed", "sub": ["4,180 miles"], "icon": "counter"},
      {"title": "Paid", "sub": ["£1,881"], "icon": "money"},
      {"title": "Asked about", "sub": ["11 claims"], "icon": "bell"},
      {"title": "Corrected", "sub": ["4, by claimants"], "icon": "check"},
      {"title": "Needed you", "sub": ["1"], "icon": "person"}],
    "title": "ONE MONTH, IN FIVE NUMBERS",
    "note": "The last number is the one to watch. If it grows, widen the band."}),
   "A month of mileage in five numbers. The interesting one is the last: how many claims "
   "actually needed a manager, out of everything that was claimed.",
   "One month of mileage claims summarised in five numbers",
   "A horizontal row of five boxes. Claimed: four thousand one hundred and eighty miles. Paid: "
   "one thousand eight hundred and eighty-one pounds. Asked about: eleven claims. Corrected: "
   "four, by the claimants themselves. Needed you: one. A note says the last number is the one "
   "to watch, and that if it grows the tolerance band should be widened."),
  ("p", "Four numbers describe the money and one describes your time. A month where eleven "
        "claims were queried, four were corrected by the person who made them, and exactly one "
        "reached a manager is a system doing its job. A month where thirty were queried is a "
        "band that is too tight, and the fix is an edit in a sheet rather than a conversation "
        "with anybody."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="claim",
 volumes=[(60, "60 claims"), (250, "250 claims"), (1200, "1,200 claims")],
 read_each=0.0062, msgs_each=2.0,
 extra=[("route", "Routing lookups &mdash; cache misses only", "#4A90D9", 0.0018, 0.0)],
 lede=("There is nothing always-on in this design, which is most of the answer. The one "
       "unusual line is the routing provider, and it is unusual in a good way: it is charged "
       "per lookup, the answers are cached forever, and on a business with a regular round the "
       "cache hit rate settles above ninety per cent within a month. Here is where each cent "
       "actually goes."),
 takeaway_extra=("Routing lookups are cached forever per address pair, so the third month "
                 "costs less than the first."),
 risks=[
  "<strong>A retry loop on the read.</strong> A malformed submission makes the function throw, "
  "the retry throws, and the queue redelivers. Without a dead-letter queue that is one bad "
  "claim costing more than a hundred good ones, every few minutes, until somebody notices. A "
  "maximum receive count of three fixes it permanently.",
  "<strong>An uncached routing call.</strong> If the cache key is built from the raw address "
  "string rather than the resolved coordinates, every variation of how somebody types a site "
  "name is a fresh paid lookup. Key the cache on the rounded coordinate pair and the hit rate "
  "goes from about forty per cent to above ninety.",
  "<strong>Log retention left at never.</strong> CloudWatch keeps log groups forever by "
  "default. On a system this small the logs will eventually cost more than the compute. Thirty "
  "days of retention is a one-line change and the highest-return cost setting here.",
 ],
 per_unit_note=("The routing line is the one that is not AWS. It is charged per lookup by "
                "whichever provider you use, and it only bills on a cache miss &mdash; a new "
                "pair of endpoints nobody has driven between before. A settled round produces "
                "very few of those."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="mc",
 lede=("The first six posts are for the person deciding whether to build this. This one is "
       "for the person building it. Same system, no analogies: the services by name, the "
       "functions and what each is allowed to touch, the three tables and their keys, the "
       "routing cache, and the specific model."),
 outside=[
  {"title": "Phone form", "sub": ["CloudFront + S3"], "icon": "phone"},
  {"title": "Routing API", "sub": ["distance for a pair"], "icon": "map"},
  {"title": "SES outbound", "sub": ["questions, receipts"], "icon": "email"}],
 inside=[
  {"title": "API + SQS", "sub": ["Function URL,", "one claim queue"], "icon": "gateway"},
  {"title": "Lambda x5", "sub": ["intake, resolve, check,", "ask, pay"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["claims, routes, totals"], "icon": "database"}],
 note="us-east-1. One account. Secrets Manager holds the routing key and the link-signing key.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The Phone form, served as static files "
  "from S3 behind CloudFront. The Routing API, an external service returning a driving "
  "distance for a pair of coordinates. And SES outbound, carrying the questions and the "
  "receipts. Inside the account, three groups. A Function URL and a single claim queue. Five "
  "Lambda functions named intake, resolve, check, ask and pay. And three DynamoDB tables named "
  "claims, routes and totals. A note gives the region as us-east-1, one account, with Secrets "
  "Manager holding the routing provider key and the link-signing key."),
 functions=[
  ["<code>mc-intake</code>", "Function URL",
   "Validates the submission, fingerprints it, enqueues one claim", "10s / 512&nbsp;MB"],
  ["<code>mc-resolve</code>", "SQS claim queue",
   "Resolves both ends to coordinates; one routing call on a cache miss", "20s / 512&nbsp;MB"],
  ["<code>mc-check</code>", "SQS resolved queue",
   "Band, repeat and pattern comparisons", "10s / 512&nbsp;MB"],
  ["<code>mc-ask</code>", "SQS question queue + EventBridge",
   "Builds and sends the question; runs the escalation sweep", "15s / 512&nbsp;MB"],
  ["<code>mc-pay</code>", "Function URL + SQS",
   "Handles the signed answer links; writes the payment and the total", "10s / 512&nbsp;MB"]],
 roles=[
  ["<code>mc-intake-role</code>", "<code>dynamodb:PutItem</code>, <code>sqs:SendMessage</code>",
   "Claims table; the claim queue only"],
  ["<code>mc-resolve-role</code>",
   "<code>dynamodb:GetItem</code>/<code>PutItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Routes table; the routing key only"],
  ["<code>mc-check-role</code>", "<code>dynamodb:Query</code>, <code>sqs:SendMessage</code>",
   "Claims and totals; two queues"],
  ["<code>mc-ask-role</code>", "<code>ses:SendEmail</code>, <code>sns:Publish</code>",
   "One verified identity; SMS to staff numbers only"],
  ["<code>mc-pay-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Claims and totals; the signing key only"]],
 tables=[
  ("Table: claims",
   "PK   claim_id          S   clm_2026_07_09_a3d1\n"
   "     status            S   open | asked | payable | exported\n"
   "     fingerprint       S   sha256(claimant|trip_date|from_cell|to_cell)\n"
   "     claimant          S   sam@example.com\n"
   "     trip_date         S   2026-07-07\n"
   "     from_cell         S   geohash7 of the origin\n"
   "     to_cell           S   geohash7 of the destination\n"
   "     miles_claimed     N   84.0\n"
   "     miles_expected    N   41.2\n"
   "     basis             S   expected 41.2, band +50%, return trip\n"
   "     ttl               N   epoch, +7 years\n\n"
   "GSI  fingerprint-index   PK fingerprint          -- the repeat test\n"
   "GSI  status-index        PK status, SK asked_at  -- the escalation sweep"),
  ("Table: routes",
   "PK   pair              S   geohash7|geohash7, lexically sorted\n"
   "     miles             N   41.2\n"
   "     provider          S   which service answered\n"
   "     fetched_at        S   2026-07-09T18:02:11Z\n\n"
   "Sorting the two cells lexically means A-to-B and B-to-A share one cache\n"
   "entry, which roughly halves the lookups on any out-and-back round."),
  ("Table: totals",
   "PK   claimant          S   sam@example.com\n"
   "SK   period            S   2026-07\n"
   "     miles             N   412.0\n"
   "     amount            N   185.40\n"
   "     claims            N   9\n\n"
   "The increment:\n"
   "  UpdateExpression:    SET miles = miles + :m, amount = amount + :a\n"
   "  ConditionExpression: attribute_not_exists(exported_at)")],
 inbound=[
  "The <strong>phone form</strong> is static files in S3 behind CloudFront, with an origin "
  "access control. There is no login: the link carries a signed staff token, minted once when "
  "somebody is added to the staff sheet, and it is the only credential a driver ever handles.",
  "<strong>Function URLs</strong> are public by default. Both <code>mc-intake</code> and "
  "<code>mc-pay</code> verify an HMAC on the first line of the handler, before parsing and "
  "before any database read.",
  "<strong>Answer links</strong> in the question email are signed, scoped to one claim, "
  "single-use by conditional write, and expire after fourteen days &mdash; longer than the "
  "approval links elsewhere on this site, because drivers take holidays.",
  "<strong>SMS nudges</strong> go through SNS to numbers from the staff sheet only. There is "
  "no path by which a number in a claim body becomes a destination."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "used only for resolving a typed place name against the customer and job lists. Everything "
  "numeric is code.",
  "<strong>Called at most once</strong> per claim, and not at all when both ends came from the "
  "recent list or the customer search &mdash; which is most claims.",
  "<strong>Output is a JSON schema</strong> with a customer id, a job id and a confidence, all "
  "nullable. Null produces the short pick-list the claimant sees; it never produces a guess.",
  "<strong>Grounded</strong> with the claimant's own recent sites and the active customer list, "
  "so the model chooses from a list rather than inventing an address.",
  "<strong>No tools, no chaining.</strong> One call in, one JSON out."],
 gotchas=[
  "Geohash precision is the whole repeat test. Seven characters is roughly 150 metres, which "
  "merges two spellings of one site without merging two units on one estate. Six is too "
  "coarse and eight is too fine.",
  "Sort the two cells before building the routes key, or every out-and-back trip pays for two "
  "lookups.",
  "Home-to-site mileage has tax consequences that differ by country. Put the rule in the sheet "
  "and never in code, because the person who knows the rule is your accountant.",
  "A new SES identity is in the sandbox. Question emails to real staff need production access, "
  "which is a support request.",
  "Stamp the rate on the payment record. A rate change in April will otherwise silently "
  "restate every unpaid claim from March."],
))
