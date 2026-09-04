"""Day 133 -- 2026-09-04 -- Waste collection verifier."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "waste-collection-verifier"
NAME = "Waste collection verifier"

SPEC = {
 "slug": SLUG, "date": "2026-09-04", "name": NAME,
 "tagline": ("Counts the collections you actually got against the ones you are paying for, proves "
             "a missed lift at the moment it is missed, checks the invoice against the contract "
             "line by line, and tells you when your bins are the wrong size -- which is where the "
             "real money is."),
 "lede": ("A small system for anybody with a commercial waste contract: an expected schedule "
          "derived from the contract, evidence captured on the morning a collection does not "
          "happen, an invoice reconciled against agreed rates rather than glanced at, and fill "
          "data that turns 'we have always had four bins' into a decision. Seven posts on the "
          "same system, one diagram at a time, with a cost breakdown and an engineering reference "
          "at the end."),
 "keywords": ["waste management", "commercial waste", "facilities", "contract compliance",
              "invoice reconciliation", "serverless"],
 "icons": ["truck", "doc", "chart"],
 "faq": [
  ("What is a waste collection verifier?",
   "A small serverless system that holds your waste contract as a schedule and a rate card, "
   "records whether each expected collection actually happened, reconciles the invoice against "
   "those two things, and pursues credits for what did not."),
  ("Why do missed collections go unclaimed?",
   "Because the evidence has to exist on the morning it happens, and by the time the invoice "
   "arrives five weeks later nobody can say with any confidence which Tuesday it was."),
  ("What is a contamination charge?",
   "A surcharge applied when a recycling load is judged to contain the wrong material. It is "
   "often legitimate, it is sometimes applied to the wrong customer, and it is nearly always "
   "challengeable if you ask for the evidence within the window."),
  ("Where does the real saving come from?",
   "Not from credits. From right-sizing: collecting a half-full bin twice a week is a standing "
   "cost that fill data makes visible, and changing frequency or container size is worth more "
   "than every missed-collection credit you will ever claim."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "waste-collection-verifier-on-aws",
 "title": "A waste collection verifier on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Expected collections against actual ones, evidence on the day, invoices reconciled, "
          "and bins right-sized. AWS, about $2 a month."),
 "og": ("You are billed for a hundred and four collections a year. Nobody in the building could "
        "tell you how many you got, which is why the answer is never a hundred and four."),
 "abstract": ("The whole system on one page -- the expected schedule, the evidence, the invoice, "
              "the fill data -- and why the last of those is worth more than the other three."),
 "lede": ("The waste invoice is about four hundred pounds a month, it has arrived every month for "
          "six years, and it is approved by somebody who has never seen the contract. Two of the "
          "four bins are collected half empty. One collection in nine does not happen. Both of "
          "those facts are invisible and both of them are paid for."),
 "tags": ["waste management", "facilities", "commercial waste", "cost control", "contracts",
          "serverless"],
 "takeaways": [
  "You cannot claim a missed collection you cannot prove on the day.",
  "The invoice has lines the contract does not mention. Check them.",
  "Contamination charges are challengeable, inside a window.",
  "Right-sizing beats credits by an order of magnitude.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "The contract", "sub": ["schedule, rates,", "renewal date"], "icon": "doc"},
      {"title": "The bin store", "sub": ["what happened,", "on the morning"], "icon": "truck"},
      {"title": "The invoice", "sub": ["monthly, itemised,", "unread"], "icon": "money"}],
    "inside": [
      {"title": "Expected", "sub": ["what you are", "paying for"], "icon": "calendar"},
      {"title": "Actual", "sub": ["with evidence,", "timestamped"], "icon": "image"},
      {"title": "The difference", "sub": ["credits, challenges,", "and the resize"], "icon": "chart"}],
    "edges": [{"from": 0, "to": 0, "label": "once, per contract"},
              {"from": 1, "to": 1, "label": "every collection day"},
              {"from": 2, "to": 2, "label": "line by line", "up": True}],
    "note": "Three sources that have never been compared to each other. That comparison is the "
            "entire system."}),
   "Three things outside the account, three pieces inside it. Nobody is missing information here; "
   "it is in three places and nothing joins them.",
   "System: expected collections, actual collections, and the invoice compared",
   "Three boxes across the top sit outside the AWS account. On the left, The contract, with its "
   "schedule, rates and renewal date. In the middle, The bin store, recording what happened on "
   "the morning. On the right, The invoice, monthly, itemised and unread. Each connects by an "
   "arrow to the AWS account container below. The contract is read once. The bin store reports "
   "every collection day. The invoice is checked line by line. Inside the AWS account are three "
   "components in a row. On the left, Expected: what you are paying for. In the middle, Actual, "
   "with timestamped evidence. On the right, The difference: credits, challenges and the resize. "
   "A note says three sources that have never been compared to each other, and that comparison is "
   "the entire system."),
  ("h3", "Why nobody notices"),
  ("p", "A missed bin collection is annoying for about two hours and then it is solved by the "
        "next collection. Nobody escalates it, because the operational problem goes away on its "
        "own, and the commercial problem -- that you paid for it -- surfaces five weeks later on "
        "a line item nobody reads."),
  ("p", "The same is true of every other discrepancy here. Each individual instance is too small "
        "to chase, and the aggregate is several thousand pounds a year. That is the exact shape "
        "of problem that a cheap system is good at and a person is not."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Expected.</strong> The contract as a schedule and a rate card, so there is something "
   "to compare against. Parts 2 and 3.",
   "<strong>Actual.</strong> Evidence captured on the morning, which is the only moment it "
   "exists. Part 2.",
   "<strong>The difference.</strong> Credits, contamination challenges, and the fill data that "
   "changes the contract itself. Parts 4 and 5.",
  ]),
  ("h2", "One month, one site"),
  ("fig", ("strip", {
    "stages": [
      {"title": "22 expected", "sub": ["from the contract"], "icon": "calendar"},
      {"title": "20 happened", "sub": ["2 with evidence", "of a miss"], "icon": "image"},
      {"title": "Invoice: 22 lifts", "sub": ["plus 3 lines", "nobody recognises"], "icon": "money"},
      {"title": "£186 recovered", "sub": ["credits and one", "wrong charge"], "icon": "check"},
      {"title": "£340 a month saved", "sub": ["by resizing"], "icon": "chart"}],
    "title": "ONE MONTH, ONE SITE",
    "note": "The fourth box is what everybody expects from this. The fifth box is why it is worth "
            "building."}),
   "The same system as one line. Recovering credits pays for the effort; the resize at the end is "
   "the actual return.",
   "One site over one month, from expected collections to a resized contract",
   "A horizontal row of five boxes joined by arrows. Twenty-two expected, from the contract. "
   "Twenty happened, with two carrying evidence of a miss. Invoice shows twenty-two lifts plus "
   "three lines nobody recognises. One hundred and eighty-six pounds recovered in credits and one "
   "wrong charge. Three hundred and forty pounds a month saved by resizing. A note says the "
   "fourth box is what everybody expects from this and the fifth box is why it is worth building."),
  ("h2", "In plain words"),
  ("p", "The contract is read once into two things: a schedule of what should happen and a rate "
        "card of what each thing should cost. That is the only reference point in the entire "
        "arrangement, and in most businesses it exists only as a PDF nobody has opened since "
        "signing."),
  ("p", "On each collection morning, whoever opens up records what they see: bins emptied, bins "
        "still full, a photograph if something is wrong. It takes fifteen seconds and it is the "
        "only moment at which evidence of a missed collection can exist."),
  ("p", "When the invoice arrives it is read line by line against the rate card. Lifts you did "
        "not get, rates that are not the agreed rates, escalations applied early, and charges "
        "with names that do not appear in the contract at all."),
  ("p", "And underneath all of that, the fill levels accumulate quietly for a few months until "
        "there is enough evidence to say something useful: that the general waste bin is "
        "collected twice a week at sixty percent full, and that one of those two collections is "
        "paying for air."),
  ("callout", "Design rules that shaped every decision", [
   "Evidence is captured on the day or it does not exist.",
   "The contract becomes a schedule and a rate card, not a stored PDF.",
   "Every invoice line is matched to a rate. Unmatched lines are questions.",
   "Challenge inside the window, because outside it there is no mechanism.",
   "Fill data is worth more than credits, and it takes three months to earn.",
   "The renewal date is a diary entry with months of notice, not a surprise.",
  ]),
  ("h2", "What it does not do"),
  ("p", "It does not weigh anything, it does not put sensors in bins, and it does not need a "
        "single piece of hardware. A person glancing at a bin store and tapping one of three "
        "buttons produces data that is good enough for every decision in this system."),
  ("p", "It also does not replace the relationship with the waste contractor, most of whom are "
        "reasonable when presented with specifics. What it changes is that you arrive with a date "
        "and a photograph rather than an impression that collections have been unreliable lately."),
  ("p", "The next four posts walk through each piece: how a missed collection gets proved, why "
        "the invoice never matches the contract, how a contamination charge gets challenged, and "
        "what the fill levels say about the contract itself. One diagram per post, a cost "
        "breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-missed-collection-gets-proved",
 "title": "How a missed collection gets proved",
 "nav": "Proving the miss",
 "read": 5, "words": 740,
 "desc": ("Fifteen seconds on the morning, why a photograph is the whole case, and the reporting "
          "window nobody knows about."),
 "og": ("By the time the invoice arrives, the bin has been emptied twice. There is no evidence "
        "left and no way to create any."),
 "abstract": ("Capturing evidence at the only moment it exists, the three-button morning check, "
              "reporting windows, and why partial collections need their own answer."),
 "lede": ("A missed collection is provable for about six hours and unprovable forever afterwards, "
          "which is why the entire design of this part is about the morning."),
 "tags": ["waste management", "facilities", "evidence", "operations", "contracts", "serverless"],
 "takeaways": [
  "Three buttons and an optional photo, at opening. Fifteen seconds.",
  "The photograph carries the date, the bin and the fill level at once.",
  "Most contracts have a 24 or 48 hour reporting window. Miss it and there is no claim.",
  "Partial collections are common and need their own button.",
  "Report on the day, then reconcile at invoice time. Two separate acts.",
 ],
 "blocks": [
  ("h2", "The morning check"),
  ("fig", ("chain", {
    "entry": {"title": "Opening up", "sub": ["walks past the", "bin store anyway"], "icon": "person"},
    "steps": [
      {"title": "All collected", "sub": ["one tap, done"], "icon": "check"},
      {"title": "Something missed", "sub": ["which bin, one tap"], "icon": "alarm",
       "side": {"title": "Photo prompted", "sub": ["automatically"], "icon": "image"}},
      {"title": "Partially emptied", "sub": ["the third button"], "icon": "filter"},
      {"title": "Fill level, roughly", "sub": ["low, half, full,", "overflowing"], "icon": "counter"},
      {"title": "Fifteen seconds", "sub": ["total"], "icon": "clock"}],
    "note": "Anything longer than this competes with opening the building, and loses."}),
   "The capture, top to bottom. The fill level in step four costs nothing extra on a morning when "
   "everything went fine, and it becomes the most valuable data in the system.",
   "The fifteen-second morning check at a bin store",
   "A vertical chain of five steps entered by a box labelled Opening up, walking past the bin "
   "store anyway. Step one, All collected, one tap and done. Step two, Something missed, "
   "recording which bin with one tap, with a side box noting a photo is prompted automatically. "
   "Step three, Partially emptied, the third button. Step four, Fill level roughly: low, half, "
   "full or overflowing. Step five, Fifteen seconds total. A note says anything longer than this "
   "competes with opening the building and loses."),
  ("h3", "The photograph is the case"),
  ("p", "A photograph of a full bin, taken at seven in the morning, timestamped, is a complete "
        "and unarguable piece of evidence. It shows the bin, the date, the fact that it was "
        "presented, and the fill level in one artefact that took four seconds to produce."),
  ("p", "Nothing else you can do later comes close. A note saying 'general waste not collected' "
        "written on a Tuesday is a claim; the same note with the photograph is a credit."),
  ("h2", "The window nobody knows about"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Reported same day", "parts": [("n", 91)]},
      {"label": "Within 48 hours", "parts": [("n", 73)]},
      {"label": "At invoice time", "parts": [("n", 12)]}],
    "series": [("n", "Missed collections credited, %", "#7AA116")],
    "unit": "",
    "note": "The contract usually says 24 or 48 hours. Almost nobody in the building knows that."}),
   "How the chance of a credit collapses with time. The cliff between the second and third bars "
   "is a contractual clause, not a negotiation.",
   "Proportion of missed collections credited by how quickly they were reported",
   "A bar chart with three bars showing the percentage of missed collections that were credited. "
   "Reported same day: ninety-one percent. Within forty-eight hours: seventy-three percent. At "
   "invoice time: twelve percent. A note says the contract usually specifies twenty-four or "
   "forty-eight hours and almost nobody in the building knows that."),
  ("p", "This single clause explains why businesses that are certain they are being let down "
        "recover almost nothing. Reporting at invoice time is outside the window in most "
        "contracts, so the contractor's answer is procedurally correct and the money is gone."),
  ("h3", "Report immediately, reconcile later"),
  ("p", "These are two separate acts and conflating them is the mistake. The report goes to the "
        "contractor on the morning, through whatever channel the contract specifies, and it is "
        "about getting the bin emptied."),
  ("p", "The reconciliation happens weeks later against the invoice, and it is about the money. "
        "The report is what makes the reconciliation possible; without a reference number from "
        "the day, the invoice conversation has nowhere to start."),
  ("h2", "Partial collections"),
  ("callout", "The cases the two-button version misses", [
   "<strong>Three bins out, two emptied.</strong> Common, and it is a partial failure that gets "
   "reported as success.",
   "<strong>Emptied but not returned</strong> -- the bin ends up in the wrong place, or on the "
   "street, which is a separate problem with the local authority attached.",
   "<strong>Collected but overflowing anyway</strong>, which is not a failure at all. It is the "
   "resize signal from Part 5 arriving early.",
   "<strong>Contractor could not access</strong> -- blocked by a delivery vehicle, gate locked. "
   "Legitimate, and it needs recording as such or it becomes a disputed credit.",
   "<strong>Collected early or late</strong>, which matters only if it is chronic, and which the "
   "timestamps show without anybody keeping notes.",
  ]),
  ("p", "The access case is the one worth being scrupulous about. Recording your own failures "
        "honestly costs you a small number of credits and buys you a great deal of credibility "
        "when you dispute something the contractor got wrong."),
  ("h3", "One number a month"),
  ("p", "The reporting output is not a dashboard. It is one line: expected twenty-two, got "
        "twenty, two reported and referenced, credit expected. Anybody can read that in three "
        "seconds and it is enough to know whether to look further."),
  ("p", "Next: the invoice."),
 ],
},
{
 "slug": "why-a-waste-invoice-never-matches-the-contract",
 "title": "Why a waste invoice never matches the contract",
 "nav": "Reading the invoice",
 "read": 6, "words": 790,
 "desc": ("Rate cards, lines that appear from nowhere, mid-term escalations, and the reconciliation "
          "that takes four minutes once it is automatic."),
 "og": ("An invoice line called 'environmental compliance levy' is either in your contract or it "
        "is not. In six years, nobody has looked."),
 "abstract": ("Turning a contract into a rate card, matching every invoice line to a rate, the "
              "surcharges worth questioning, and how price escalation clauses actually work."),
 "lede": ("A commercial waste invoice is a fixed charge, a variable charge, and between three and "
          "nine other lines whose names change from month to month."),
 "tags": ["waste management", "invoice reconciliation", "contracts", "cost control", "facilities",
          "serverless"],
 "takeaways": [
  "The contract becomes a rate card: every chargeable thing, with its agreed price.",
  "Every invoice line matches a rate or becomes a question.",
  "Surcharges are legitimate, negotiable, or wrong, and you cannot tell without asking.",
  "Escalation clauses have a date and a cap. Both get exceeded.",
  "One model read per invoice; everything after it is arithmetic.",
 ],
 "blocks": [
  ("h2", "The rate card"),
  ("fig", ("system", {
    "outside": [
      {"title": "The contract PDF", "sub": ["signed, filed,", "never reopened"], "icon": "doc"},
      {"title": "The schedule", "sub": ["which bins,", "which days"], "icon": "calendar"},
      {"title": "The invoice", "sub": ["arriving monthly"], "icon": "money"}],
    "inside": [
      {"title": "Rates", "sub": ["per lift, per tonne,", "per container"], "icon": "form"},
      {"title": "Expected charges", "sub": ["what this month", "should cost"], "icon": "counter"},
      {"title": "Line by line", "sub": ["matched, or", "questioned"], "icon": "filter"}],
    "edges": [{"from": 0, "to": 0, "label": "read once"},
              {"from": 1, "to": 1, "label": "expected"},
              {"from": 2, "to": 2, "label": "actual, compared", "up": True}],
    "note": "An invoice line with no matching rate is not necessarily wrong. It is necessarily a "
            "question."}),
   "The contract becoming something an invoice can be checked against. Most businesses have the "
   "left-hand box and none of the others.",
   "How a waste contract becomes a rate card for checking invoices",
   "Three boxes across the top outside the AWS account. The contract PDF, signed, filed and never "
   "reopened. The schedule, showing which bins on which days. And The invoice, arriving monthly. "
   "Each connects by an arrow to the AWS account container below, labelled read once, expected, "
   "and actual compared. Inside the account are three components. Rates, per lift, per tonne and "
   "per container. Expected charges, what this month should cost. And Line by line, matched or "
   "questioned. A note says an invoice line with no matching rate is not necessarily wrong, but "
   "it is necessarily a question."),
  ("h3", "What the rate card contains"),
  ("ul", [
   "<strong>The standing charge</strong>, per container per period, which is most of the bill and "
   "the least examined part of it.",
   "<strong>The lift rate</strong>, per collection, and whether it is included in the standing "
   "charge or additional.",
   "<strong>Weight rates</strong> where the contract is weight-based, with the included tonnage "
   "if there is one.",
   "<strong>Named surcharges</strong> that the contract does allow: contamination, overweight, "
   "return visits, container replacement.",
   "<strong>The escalation clause</strong> -- when the price can rise, by how much, and against "
   "what index.",
  ]),
  ("h2", "The lines that appear from nowhere"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "In the rate card", "sub": ["at the agreed price"], "icon": "check",
       "label": "pay it"},
      {"title": "In the rate card", "sub": ["at a different price"], "icon": "alarm",
       "label": "query it"},
      {"title": "Not in it at all", "sub": ["'compliance levy',", "'carbon charge'"],
       "icon": "search", "label": "ask what it is"}],
    "target": {"title": "One monthly query", "sub": ["with line references"], "icon": "email",
               "then": {"title": "Credit, explanation,", "sub": ["or a contract variation"],
                        "icon": "doc"}},
    "note": "Three outcomes and all three are fine. Silence is the only bad one, and it is the "
            "default."}),
   "What happens to each invoice line. The third lane is where the surprises live, and asking "
   "about them is a normal commercial conversation rather than a dispute.",
   "Three outcomes for a line on a waste invoice",
   "Three boxes stacked on the left. In the rate card at the agreed price, labelled pay it. In "
   "the rate card at a different price, labelled query it. And Not in it at all, such as a "
   "compliance levy or carbon charge, labelled ask what it is. All three converge on One monthly "
   "query with line references, which leads down to Credit, explanation, or a contract variation. "
   "A note says three outcomes and all three are fine, and silence is the only bad one and it is "
   "the default."),
  ("h3", "New charges are usually legitimate and sometimes not"),
  ("p", "Waste contractors face genuine cost changes -- disposal gate fees, landfill tax, fuel -- "
        "and passing them on is often explicitly permitted. A new line is not evidence of "
        "anything on its own."),
  ("p", "What is worth knowing is which clause allows it, because that clause usually contains a "
        "cap, a notice period, or a restriction to actual documented cost increases. A charge "
        "that turns out not to be permitted is normally credited without argument once you cite "
        "the clause, and never mentioned again if you do not."),
  ("h2", "Escalation clauses"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Signed rate", "parts": [("n", 412)]},
      {"label": "Year 2, as agreed", "parts": [("n", 432)]},
      {"label": "Year 2, as invoiced", "parts": [("n", 498)]},
      {"label": "Year 3, as invoiced", "parts": [("n", 574)]}],
    "series": [("n", "Monthly standing charge, £", "#E7157B")],
    "unit": "",
    "note": "Nothing here is dramatic month to month. Over three years it is a thirty-nine "
            "percent increase nobody agreed to."}),
   "An escalation clause applied generously. Each individual rise is small enough to approve "
   "without thinking, which is exactly why the comparison has to be against the signed rate.",
   "Contracted price escalation against what was actually invoiced",
   "A bar chart with four bars showing the monthly standing charge in pounds. Signed rate: four "
   "hundred and twelve. Year two as agreed: four hundred and thirty-two. Year two as invoiced: "
   "four hundred and ninety-eight. Year three as invoiced: five hundred and seventy-four. A note "
   "says nothing here is dramatic month to month, and over three years it is a thirty-nine "
   "percent increase nobody agreed to."),
  ("p", "The mechanism is always the same. A price rise arrives as a letter, it is filed, and the "
        "invoice quietly reflects it from the following month. Nobody compares it to what the "
        "contract permits, because the contract is a PDF and the letter is an email and they have "
        "never been in the same place."),
  ("h3", "Where the model runs"),
  ("p", "One call per invoice, turning a scanned or emailed document into lines with a "
        "description, a quantity, a unit rate and a total. That is a genuinely hard document "
        "problem and a good use of the tool."),
  ("p", "Everything after that is arithmetic against the rate card, and it stays arithmetic on "
        "purpose. A discrepancy has to be explainable to a contractor in one sentence, and 'the "
        "model thought this looked unusual' is not that sentence."),
  ("p", "Next: challenging a contamination charge."),
 ],
},
{
 "slug": "how-a-contamination-charge-gets-challenged",
 "title": "How a contamination charge gets challenged",
 "nav": "Challenging charges",
 "read": 6, "words": 770,
 "desc": ("Asking for the evidence, the window that applies to you as well, and the fixes that "
          "stop the charge recurring."),
 "og": ("Ask for the photograph, the weight and the time. A charge that cannot produce all three "
        "does not usually survive being asked about."),
 "abstract": ("What a contamination charge is, the evidence a contractor should hold, how to "
              "challenge inside the window, and the operational fixes that actually stop it."),
 "lede": ("Contamination charges are the largest variable line on most recycling contracts and "
          "the least examined, because the implication is that it was your fault and nobody "
          "enjoys arguing about that."),
 "tags": ["waste management", "recycling", "disputes", "evidence", "facilities", "serverless"],
 "takeaways": [
  "Ask for photograph, weight and timestamp. Politely, every time.",
  "Challenge windows are short and they bind you, not them.",
  "Some charges are for other people's bins. It happens more than you would think.",
  "A recurring charge is an operational problem, not a billing one.",
  "Track the rate, not the incidents. The rate is what changes.",
 ],
 "blocks": [
  ("h2", "What the charge is"),
  ("p", "A recycling load that contains the wrong material is worth less or nothing, and may have "
        "to be re-sorted or sent to general waste at a higher disposal cost. The surcharge is real "
        "and it is usually permitted by the contract."),
  ("p", "It is also applied by a driver or a sorting facility making a rapid judgement, sometimes "
        "about a bin that is not clearly yours, and recorded in a system you cannot see. All "
        "three of those are reasons to ask rather than reasons to be suspicious."),
  ("h2", "The three things to ask for"),
  ("fig", ("chain", {
    "entry": {"title": "Contamination charge", "sub": ["£85 on the invoice"], "icon": "alarm"},
    "steps": [
      {"title": "The photograph", "sub": ["of the load,", "at the point of"], "icon": "image"},
      {"title": "The timestamp", "sub": ["and which collection"], "icon": "clock",
       "side": {"title": "Cross-check", "sub": ["your own morning", "record"], "icon": "check"}},
      {"title": "The weight", "sub": ["and the disposal", "route used"], "icon": "counter"},
      {"title": "One of three answers", "sub": ["valid, wrong bin,", "or nothing"], "icon": "branch"}],
    "note": "Asking is not an accusation. It is what a customer with a rate card does every month."}),
   "The challenge, top to bottom. Most of its value is in the side box: your own record of that "
   "morning either supports the charge or contradicts it.",
   "How a contamination charge is challenged with evidence",
   "A vertical chain of four steps entered by a box labelled Contamination charge, eighty-five "
   "pounds on the invoice. Step one, The photograph of the load at the point of collection. Step "
   "two, The timestamp and which collection, with a side box for cross-checking your own morning "
   "record. Step three, The weight and the disposal route used. Step four, One of three answers: "
   "valid, wrong bin, or nothing. A note says asking is not an accusation, it is what a customer "
   "with a rate card does every month."),
  ("h3", "The wrong-bin case"),
  ("p", "Shared bin stores, unlocked yards and neighbouring businesses produce a steady trickle of "
        "charges that belong to somebody else. The contractor is not being dishonest; the driver "
        "recorded a contaminated bin at an address, and the address has four tenants."),
  ("p", "Your own morning record is what resolves it. A photograph of your bin at seven, clean, "
        "on the day of a collection charged as contaminated at eleven, is a complete answer and "
        "it took four seconds to create."),
  ("h2", "The window binds you"),
  ("callout", "The practical timetable of a challenge", [
   "<strong>The charge appears</strong> on an invoice, typically for a collection three to six "
   "weeks earlier.",
   "<strong>The challenge window</strong> is usually fourteen or thirty days from the invoice "
   "date, and it is in the contract rather than on the invoice.",
   "<strong>Evidence retention</strong> at the contractor's end is often ninety days, so a "
   "challenge raised four months later cannot be answered even in good faith.",
   "<strong>Which means the invoice has to be read on arrival</strong>, not when somebody has "
   "time, and that is the whole argument for automating the comparison.",
   "<strong>And a challenge should be one email</strong>, with the invoice line, the date, the "
   "photograph and a specific question.",
  ]),
  ("p", "Almost every failed challenge fails on timing rather than on merit. An invoice that sits "
        "in an approvals queue for five weeks and then gets paid has closed its own window, and "
        "no amount of being right afterwards reopens it."),
  ("h2", "When the charge is fair"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "One-off", "sub": ["a bag in the", "wrong bin"], "icon": "box", "label": "accept it"},
      {"title": "Recurring, one bin", "sub": ["always the same", "container"], "icon": "retry",
       "label": "signage, position"},
      {"title": "Recurring, one shift", "sub": ["always the same", "day of the week"],
       "icon": "team", "label": "training"}],
    "target": {"title": "The fix is operational", "sub": ["not commercial"], "icon": "tag",
               "then": {"title": "Charges stop", "sub": ["within two months"], "icon": "check"}},
    "note": "A charge you keep paying and challenging is a process problem wearing an invoice."}),
   "Three patterns behind contamination charges. Only the first one is genuinely random, and the "
   "other two are fixed inside the building rather than on the phone.",
   "Three patterns of recurring contamination charges and their fixes",
   "Three boxes stacked on the left. One-off, a bag in the wrong bin, labelled accept it. "
   "Recurring on one bin, always the same container, labelled signage and position. And Recurring "
   "on one shift, always the same day of the week, labelled training. All three converge on The "
   "fix is operational rather than commercial, which leads down to Charges stop within two "
   "months. A note says a charge you keep paying and challenging is a process problem wearing an "
   "invoice."),
  ("h3", "The day-of-week pattern"),
  ("p", "The most useful thing this system produces about contamination is not the challenge, it "
        "is the pattern. Charges clustering on Tuesdays, or on one container, is information that "
        "no single invoice contains and that only exists because somebody kept the dates."),
  ("p", "That pattern usually points at one shift, one new starter, or one bin positioned next to "
        "a door where people put things down. All three are fixed in an afternoon and none of "
        "them are visible from the invoice."),
  ("h3", "Track the rate"),
  ("p", "The number worth reporting is the proportion of collections that attract a charge, not "
        "the count. A count goes up when you grow, which makes an improving situation look like a "
        "worsening one and eventually makes everybody stop looking at it."),
  ("p", "Next: what the bins have been telling you all along."),
 ],
},
{
 "slug": "what-fill-levels-say-about-the-contract",
 "title": "What fill levels say about the contract",
 "nav": "Right-sizing",
 "read": 6, "words": 780,
 "desc": ("Three months of one-tap data, the half-empty bin nobody costs, and the renewal date "
          "that arrives with notice."),
 "og": ("Every credit you will ever claim is worth less than one bin you did not need collecting "
        "twice a week."),
 "abstract": ("Using accumulated fill data to change frequency and container size, the seasonal "
              "trap, negotiating with evidence, and putting the renewal date somewhere it cannot "
              "be missed."),
 "lede": ("The credits are satisfying and small. The money is in the standing charge, and the only "
          "way to argue about a standing charge is with three months of evidence about how full "
          "the bins actually were."),
 "tags": ["waste management", "cost control", "facilities", "contracts", "procurement",
          "serverless"],
 "takeaways": [
  "Three months of one-tap fill levels is enough to act on.",
  "A bin collected at sixty percent is a frequency decision, not a fact of nature.",
  "Check the seasonal pattern before cutting, or you will reinstate it in November.",
  "Take the evidence to the incumbent first. It is usually cheaper than switching.",
  "The renewal date needs six months of notice, not six weeks.",
 ],
 "blocks": [
  ("h2", "What three months of taps produces"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "General waste", "parts": [("n", 58)]},
      {"label": "Mixed recycling", "parts": [("n", 91)]},
      {"label": "Cardboard", "parts": [("n", 44)]},
      {"label": "Glass", "parts": [("n", 37)]}],
    "series": [("n", "Average fill at collection, %", "#01A88D")],
    "unit": "",
    "note": "Two of these are collected too often and one is collected too rarely. None of it was "
            "visible before somebody started tapping a button."}),
   "Average fill at the moment of collection, per stream. The recycling bin at ninety-one percent "
   "is as much of a finding as the glass bin at thirty-seven.",
   "Average fill level at collection across four waste streams",
   "A bar chart with four bars showing average fill at collection as a percentage. General waste: "
   "fifty-eight. Mixed recycling: ninety-one. Cardboard: forty-four. Glass: thirty-seven. A note "
   "says two of these are collected too often and one is collected too rarely, and none of it was "
   "visible before somebody started tapping a button."),
  ("p", "The glass bin at thirty-seven percent is being collected weekly and could go fortnightly. "
        "The cardboard bin is a smaller container. The recycling bin at ninety-one percent is "
        "about to start overflowing and cause exactly the contamination charges from Part 4."),
  ("h3", "Under-servicing is a finding too"),
  ("p", "It is tempting to treat this purely as a cost-cutting exercise, but the bin that is "
        "always nearly full is generating overflow, side waste charges, and contamination as "
        "people cram things in. Adding a collection there can reduce the total bill."),
  ("p", "That also makes the conversation with the contractor a genuine negotiation rather than a "
        "demand. Proposing to drop one glass collection and add one recycling collection is a "
        "much easier discussion than asking for a reduction."),
  ("h2", "The seasonal trap"),
  ("fig", ("chain", {
    "entry": {"title": "Three months of data", "sub": ["taken in spring"], "icon": "chart"},
    "steps": [
      {"title": "Cut a collection", "sub": ["it was 40% full"], "icon": "filter"},
      {"title": "Fine for months", "sub": ["genuine saving"], "icon": "check"},
      {"title": "November arrives", "sub": ["volume doubles"], "icon": "alarm",
       "side": {"title": "Overflow charges", "sub": ["and side waste"], "icon": "money"}},
      {"title": "Reinstated, at a", "sub": ["worse rate"], "icon": "retry"}],
    "note": "Twelve months of data, or cut against the busiest month you have measured. Not the "
            "average."}),
   "How a correct decision on the data available becomes an expensive one. The fix costs nothing: "
   "cut against your peak rather than your mean.",
   "How a seasonal pattern undermines a collection frequency reduction",
   "A vertical chain of four steps entered by a box labelled Three months of data taken in "
   "spring. Step one, Cut a collection because it was forty percent full. Step two, Fine for "
   "months, a genuine saving. Step three, November arrives and volume doubles, with a side box "
   "noting overflow charges and side waste. Step four, Reinstated at a worse rate. A note says "
   "use twelve months of data, or cut against the busiest month you have measured, not the "
   "average."),
  ("h3", "Cut against the peak"),
  ("p", "Most businesses know their own seasonality perfectly well and simply do not apply it "
        "here. A hospitality site in February and the same site in December are different "
        "operations, and a contract sized for February is one that fails at the worst possible "
        "time of year."),
  ("p", "Where twelve months of data does not exist yet, the honest approach is to size against "
        "the fullest month you have measured and revisit once a year of data exists. That is "
        "slower and it does not produce a decision you have to reverse."),
  ("h2", "The renewal date"),
  ("callout", "Why waste contracts renew themselves", [
   "<strong>Long initial terms</strong>, frequently three years, sometimes five.",
   "<strong>Automatic renewal</strong> unless notice is given in a specific window before the "
   "end date.",
   "<strong>Notice windows measured in months</strong>, and often requiring written notice by a "
   "specific method.",
   "<strong>Which means the decision point</strong> is six to nine months before the date anybody "
   "has in their head.",
   "<strong>And that date lives in a PDF</strong>, in the same folder as the schedule and the "
   "rate card, unread since the day it was signed.",
  ]),
  ("p", "This is the single highest-value field extracted from the contract, and it is one date. "
        "Everything else in this system saves you tens or hundreds of pounds a month; missing a "
        "notice window commits you to another three years of a rate you had evidence to "
        "renegotiate."),
  ("h3", "Take it to the incumbent first"),
  ("p", "With three months of fill data, a record of missed collections and a list of queried "
        "charges, the conversation with your existing contractor is straightforward and usually "
        "productive. They would rather adjust a schedule than lose a site, and switching has real "
        "costs in container swaps and disruption."),
  ("p", "Getting a competitive quote is still worth doing, and having the evidence makes the "
        "quotes comparable for the first time -- because you can ask everybody to price the same "
        "measured volumes rather than the same guess."),
  ("h3", "What this system is really for"),
  ("p", "None of this is complicated. Someone taps a button in the morning, an invoice gets read "
        "properly, and a date sits in a diary."),
  ("p", "The reason it does not happen is that the contract, the collections and the invoice live "
        "in three different places and belong to three different people. Joining them is the "
        "whole intervention, and the fill data that falls out of it is worth more than everything "
        "else put together."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="site",
 volumes=[(3, "3 sites"), (12, "12 sites"), (45, "45 sites")],
 read_each=0.035,
 msgs_each=6.0,
 store_base=0.30,
 store_growth=0.0008,
 lede=("The model runs once per invoice, which is once per site per month: a long itemised "
       "document is the most expensive read in this series and it is still pennies. Twelve sites "
       "is a small multi-site operator. Here is where each cent goes."),
 takeaway_extra=("Morning checks and photographs are free at any volume; the read scales with "
                 "sites, not with collections."),
 risks=[
  "<strong>Storing every morning photograph at full resolution forever.</strong> Resize on "
  "upload, and expire the clean-collection photos after the challenge window closes. Keep the "
  "disputed ones.",
  "<strong>Re-reading the contract on a schedule.</strong> It changes when a variation letter "
  "arrives, which is a document event, not a monthly one.",
  "<strong>A notification per collection.</strong> The morning check is silent when everything is "
  "fine. Only exceptions generate mail, or the exceptions stop being read.",
 ],
 per_unit_note=("The read is one call per invoice against a capable model, because an itemised "
                "waste invoice is a genuinely awkward document: multi-page, inconsistent between "
                "months, and often a scan. This is one of the few places in this series where "
                "paying for a better model is defensible, and it is still under four cents."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="wc",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the expected-versus-actual join, and the one model call per invoice."),
 outside=[
  {"title": "Contracts", "sub": ["and variation", "letters"], "icon": "doc"},
  {"title": "The morning check", "sub": ["three buttons,", "one photo"], "icon": "phone"},
  {"title": "Invoices", "sub": ["monthly, itemised,", "often scanned"], "icon": "money"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["uploads, schedules,", "windows"], "icon": "bucket"},
  {"title": "Lambda x4", "sub": ["terms, check,", "invoice, pursue"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["sites, events"], "icon": "database"}],
 note="us-east-1. One account. Expected collections are generated ahead; actuals arrive against "
      "them.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Contracts and variation letters. The "
  "morning check, three buttons and one photo. And Invoices, monthly, itemised and often scanned. "
  "Inside the account, three groups. S3 and EventBridge for uploads, schedules and windows. Four "
  "Lambda functions named terms, check, invoice and pursue. And two DynamoDB tables named sites "
  "and events. A note gives the region as us-east-1, one account, and states that expected "
  "collections are generated ahead and actuals arrive against them."),
 functions=[
  ["<code>wc-terms</code>", "S3 upload of a contract or variation",
   "One model call; writes the schedule, the rate card, the windows and the renewal date",
   "60s / 1024&nbsp;MB"],
  ["<code>wc-check</code>", "API, from the morning check",
   "Marks each expected collection done, missed or partial; stores the resized photograph",
   "10s / 512&nbsp;MB"],
  ["<code>wc-invoice</code>", "S3 upload of an invoice",
   "One model call to line items; matches every line to a rate; opens queries for the rest",
   "120s / 2048&nbsp;MB"],
  ["<code>wc-pursue</code>", "EventBridge, daily",
   "Fires reporting and challenge windows, chases credits, and warns on the renewal notice date",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>wc-terms-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "One model id; the contracts prefix; sites"],
  ["<code>wc-check-role</code>", "<code>dynamodb:UpdateItem</code>, <code>s3:PutObject</code>",
   "Events; the evidence prefix"],
  ["<code>wc-invoice-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:Query</code>, "
   "<code>dynamodb:PutItem</code>", "One model id; the invoices prefix; both tables"],
  ["<code>wc-pursue-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Events; one verified identity"]],
 tables=[
  ("Table: sites",
   "PK   site_id           S\n"
   "SK   '#terms'          S   one item per site\n"
   "     containers        L   [{stream, size, count, days}]\n"
   "     rates             M   standing, lift, per_tonne, named surcharges\n"
   "     escalation        M   {window, cap, index}\n"
   "     report_window_h   N   hours to report a miss -- usually 24 or 48\n"
   "     challenge_days    N   days to challenge an invoice line\n"
   "     term_end          S\n"
   "     notice_months     N   the field that decides whether you have a choice\n"
   "     notice_by         S   term_end minus notice_months, precomputed\n"
   "     source_key        S   the contract PDF\n\n"
   "notice_by is stored rather than derived, because it is the one date\n"
   "that has to fire even if nobody ever opens this record again."),
  ("Table: events",
   "PK   site_id#period    S\n"
   "SK   due_at#stream     S   one item per expected collection\n"
   "     expected          BOOL generated ahead from the schedule\n"
   "     state             S   done | missed | partial | no_access\n"
   "     fill              S   low | half | full | overflow\n"
   "     photo_key         S   only on exceptions, and on a sample\n"
   "     reported_at       S   inside report_window_h, or the claim is dead\n"
   "     report_ref        S   the contractor's reference\n"
   "     charged           N   from the invoice line that matched\n"
   "     credit_expected   N\n"
   "     credit_received   N\n"
   "     query_state       S   none | raised | answered | credited | rejected\n\n"
   "Expected collections are written ahead of time. A missing actual is\n"
   "then a row that stayed in expected state, not an absence of data.")],
 inbound=[
  "<strong>Expected collections are generated forward</strong> from the schedule, monthly. "
  "Detecting a miss becomes a query for rows nobody updated, which is far more reliable than "
  "inferring absence.",
  "<strong>The morning check is one request</strong> and is silent when everything is normal. "
  "Notifications only ever come from exceptions.",
  "<strong>Photographs are kept on exceptions</strong> and on a small random sample of normal "
  "days, which is what makes a challenge credible.",
  "<strong>Invoices arrive by upload or by mailbox</strong>, and both land in the same function. "
  "Nothing here depends on a contractor portal or an integration that could be withdrawn."],
 model_notes=[
  "<strong>Two calls, both per document.</strong> One per contract or variation letter, one per "
  "invoice. Nothing per collection.",
  "<strong>A more capable model for invoices</strong>, deliberately. Multi-page scanned itemised "
  "documents are where cheap extraction quietly produces wrong quantities.",
  "<strong>A JSON schema, with nulls allowed.</strong> A missing notice period becomes a question "
  "to a human, because guessing that field can cost three years.",
  "<strong>Reconciliation is arithmetic</strong>, not a model judgement. Every discrepancy has to "
  "be stateable to a contractor in one sentence with a line reference.",
  "<strong>No image model on the evidence photographs.</strong> They are for a human at the point "
  "of dispute, and a fill level from a tap is more reliable than one from a picture of a bin."],
 gotchas=[
  "Generate expected collections ahead of time. Detecting a miss as a row that never got updated "
  "is reliable; inferring it from the absence of a record is not.",
  "Store the notice date, not just the term end. The decision point is six to nine months before "
  "the date everybody has in their head, and it is the most expensive field in the contract.",
  "Report misses within the contractual window, which is usually 24 or 48 hours. Almost every "
  "failed credit claim failed on timing rather than on merit.",
  "Cut collections against your busiest measured month, never the average. A frequency reduction "
  "reversed in November is reinstated at a worse rate.",
  "Keep the exception photographs and expire the rest. The evidence that matters is small, and "
  "keeping everything at full resolution is the only way to make this system cost real money."],
))
