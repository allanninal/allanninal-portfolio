"""Day 136 -- 2026-09-07 -- Gift Aid claimer."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "gift-aid-claimer"
NAME = "Gift Aid claimer"

SPEC = {
 "slug": SLUG, "date": "2026-09-07", "name": NAME,
 "tagline": ("Works out which donations you can actually claim Gift Aid on, which ones only "
             "qualify under the small-donations scheme, and which ones are worth nothing "
             "because nobody holds the paperwork -- and keeps the evidence in a shape that "
             "survives an audit four years later."),
 "lede": ("A small system for any charity that takes donations: declarations captured and "
          "dated, every donation sorted into the route it actually qualifies for, a claim "
          "built against the schemes' own caps, and an evidence file that outlives the claim "
          "by six years. Seven posts on the same system, one diagram at a time, with a cost "
          "breakdown and an engineering reference at the end."),
 "keywords": ["Gift Aid", "GASDS", "charity finance", "HMRC", "declarations",
              "serverless"],
 "icons": ["money", "doc", "shield"],
 "faq": [
  ("What is Gift Aid worth?",
   "Twenty-five pence for every pound donated. The charity reclaims the basic-rate tax the "
   "donor already paid, so a ten pound gift becomes twelve fifty at no cost to the donor."),
  ("Why can't I claim on every donation?",
   "Because a claim needs a declaration from that donor that was in force when the donation "
   "was made, and the donor has to have paid at least as much tax as every charity will "
   "reclaim on their giving that year. No declaration, no claim."),
  ("What is the small donations scheme?",
   "A separate route for small cash and contactless gifts where chasing a declaration is not "
   "realistic. It pays the same twenty-five per cent, needs no declaration, and is capped -- "
   "including a cap tied to how much ordinary Gift Aid you claimed."),
  ("What happens if a claim turns out to be wrong?",
   "HMRC takes it back, with interest, and can look at the four years before it. That is why "
   "the evidence file is the deliverable rather than the claim."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "gift-aid-claimer-on-aws",
 "title": "A Gift Aid claimer on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Declarations dated, donations routed, claims built against the caps, and an "
          "evidence file that outlives them. AWS, about $2 a month."),
 "og": ("The charity left 8,925 pounds unclaimed last year. Every penny of it was donated by "
        "someone who would happily have signed the form."),
 "abstract": ("The whole system on one page -- declarations, donations, routing and evidence "
              "-- and why the money you lose to Gift Aid is lost to paperwork rather than to "
              "tax."),
 "lede": ("The finance trustee reports that the charity claimed thirty-five thousand seven "
          "hundred pounds of Gift Aid last year, which sounds like a job well done. It took "
          "an afternoon with the donation export to work out that another eight thousand nine "
          "hundred and twenty-five was available and went unclaimed, and that not one pound of "
          "it was refused by HMRC. Nobody asked."),
 "tags": ["Gift Aid", "GASDS", "charity", "HMRC", "compliance", "serverless"],
 "takeaways": [
  "A donation is claimable or not at the moment it is made, not when you notice.",
  "A declaration must be in force on the donation date. Signed later covers later.",
  "Small cash gifts have their own route, and it is capped by your ordinary claim.",
  "The claim is easy. The evidence that survives an audit is the system.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Declarations", "sub": ["forms, web, verbal --", "each with a date"], "icon": "doc"},
      {"title": "Donations", "sub": ["bank, card, cash,", "contactless"], "icon": "money"},
      {"title": "The schemes", "sub": ["rates, limits and", "the matching rule"], "icon": "key"}],
    "inside": [
      {"title": "Donor record", "sub": ["who signed what,", "and from when"], "icon": "person"},
      {"title": "Routing", "sub": ["Gift Aid, small", "donations, neither"], "icon": "branch"},
      {"title": "Claim and evidence", "sub": ["what was claimed,", "and on what basis"], "icon": "shield"}],
    "edges": [{"from": 0, "to": 0, "label": "once per donor"},
              {"from": 1, "to": 1, "label": "continuous"},
              {"from": 2, "to": 2, "label": "rarely", "up": True}],
    "note": "The middle box is the whole job. Everything either side of it already exists in "
            "the charity somewhere, usually in two systems that have never been joined."}),
   "Three things outside the account, three pieces inside it. The routing in the middle is "
   "where the money is won or lost.",
   "System: declarations, donations and scheme rules joined into a claim",
   "Three boxes across the top sit outside the AWS account. On the left, Declarations from "
   "forms, web and verbal, each with a date. In the middle, Donations from bank, card, cash "
   "and contactless. On the right, The schemes: rates, limits and the matching rule. Each "
   "connects by an arrow to the AWS account container below, labelled once per donor, "
   "continuous, and rarely. Inside the AWS account are three components in a row. Donor "
   "record: who signed what, and from when. Routing: Gift Aid, small donations, or neither. "
   "And Claim and evidence: what was claimed and on what basis. A note says the middle box is "
   "the whole job, and everything either side of it already exists in the charity somewhere, "
   "usually in two systems that have never been joined."),
  ("h3", "Why the money goes missing"),
  ("p", "Gift Aid is not difficult in the way tax is difficult. The rate is twenty-five per "
        "cent, it applies to almost every donation from a UK taxpayer, and HMRC pays it "
        "without argument. What it needs is a piece of evidence that existed at the moment "
        "the donation was made, and charities are organised around receiving money rather "
        "than around dating paperwork."),
  ("p", "So the donation arrives in one system and the declaration sits in another, and "
        "nothing joins them until somebody exports both to a spreadsheet once a year. By then "
        "the donor who gave forty pounds in March and never signed anything is a name on a "
        "list that nobody is going to phone."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Donor record.</strong> Every declaration with the date it took effect and what it "
   "covers. Part 2.",
   "<strong>Routing.</strong> Each donation matched to a donor and a scheme, or to neither, "
   "with the reason recorded. Part 3.",
   "<strong>The claim.</strong> Built against the schemes' own limits, including the one that "
   "ties small donations to ordinary Gift Aid. Part 4.",
   "<strong>Evidence.</strong> The file that has to still make sense when somebody asks about "
   "it four years later. Part 5.",
  ]),
  ("h2", "One charity, one year"),
  ("fig", ("strip", {
    "stages": [
      {"title": "4,120 donations", "sub": ["GBP 186,400", "received"], "icon": "money"},
      {"title": "2,905 covered", "sub": ["a declaration was", "in force"], "icon": "doc"},
      {"title": "GBP 35,700", "sub": ["claimed as", "Gift Aid"], "icon": "check"},
      {"title": "640 small gifts", "sub": ["GBP 1,975 under the", "small-donations route"], "icon": "counter"},
      {"title": "GBP 8,925 lost", "sub": ["575 donations, no", "declaration"], "icon": "alarm"}],
    "title": "ONE SMALL CHARITY, ONE FINANCIAL YEAR",
    "note": "The last box is not a tax outcome. It is 575 people who gave money and were "
            "never asked to tick a box."}),
   "The same system as one line. The first four boxes are the job working; the fifth is the "
   "one the annual spreadsheet never produces.",
   "One charity's year from donations received to Gift Aid unclaimed",
   "A horizontal row of five boxes joined by arrows. Four thousand one hundred and twenty "
   "donations totalling one hundred and eighty-six thousand four hundred pounds received. Two "
   "thousand nine hundred and five covered by a declaration in force. Thirty-five thousand "
   "seven hundred pounds claimed as Gift Aid. Six hundred and forty small gifts yielding one "
   "thousand nine hundred and seventy-five pounds under the small-donations route. And eight "
   "thousand nine hundred and twenty-five pounds lost across five hundred and seventy-five "
   "donations with no declaration. A note says the last box is not a tax outcome but five "
   "hundred and seventy-five people who gave money and were never asked to tick a box."),
  ("h2", "In plain words"),
  ("p", "Declarations are read once each, into a record that says who the donor is, when the "
        "declaration took effect, and whether it covers past donations as well as future "
        "ones. That last field matters more than it looks, and part two is about it."),
  ("p", "Donations arrive continuously from wherever the charity takes money, and each one is "
        "matched to a donor. A donation with no matching donor is not an error; it is a cash "
        "gift in a bucket, and it may still be worth something under the small-donations "
        "route."),
  ("p", "Then each donation is routed. Ordinary Gift Aid if a declaration was in force on the "
        "day it was given. The small-donations scheme if it is small, in cash or contactless, "
        "and within that scheme's annual allowance. Neither, if it is a large donation from "
        "somebody who never signed &mdash; and that case is counted and reported rather than "
        "dropped, because it is the number that changes what the charity does next year."),
  ("p", "The claim is then arithmetic against published limits, and the evidence file is "
        "assembled at the same time rather than reconstructed later."),
  ("callout", "Design rules that shaped every decision", [
   "A donation's eligibility is decided by the state of the world on its own date.",
   "A declaration signed today does not retroactively cover March unless it says so.",
   "An unclaimable donation is counted and reported, never silently skipped.",
   "The small-donations route is checked against the ordinary claim, not just its own cap.",
   "Nothing is claimed on a donor flagged as not a UK taxpayer.",
   "The evidence is written when the claim is made, because it cannot be rebuilt.",
  ]),
  ("h2", "What it does not do"),
  ("p", "It does not file the claim. HMRC has its own route for that and it changes; this "
        "system produces the schedule that goes into it and the record of why each line is "
        "there. It does not chase donors either, though it produces the list of people worth "
        "chasing, ranked by what their missing declaration is worth."),
  ("p", "It also does not decide whether a donor has paid enough tax. That is a fact about "
        "the donor's own affairs which the charity cannot see and is not required to verify; "
        "what the charity must do is hold a declaration in which the donor confirms it, and "
        "act on it if they later say otherwise. The system records the confirmation and the "
        "date it was given."),
  ("p", "The next four posts walk through each piece: how a declaration is captured and why "
        "its date decides everything, how a donation is routed, how the claim is built "
        "against the caps, and what the evidence has to contain. One diagram per post, a cost "
        "breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "the-date-on-the-declaration",
 "title": "The date on the declaration decides everything",
 "nav": "Declarations",
 "read": 5, "words": 800,
 "desc": ("Three ways a declaration arrives, why the date it took effect is the only field "
          "that matters, and what a retrospective declaration does and does not cover."),
 "og": ("A declaration signed in June does not make a March donation claimable. Unless it "
        "says it does, and most of them do not."),
 "abstract": ("Capturing declarations from paper, web and verbal routes into a record with an "
              "effective date and an explicit statement of what it covers."),
 "lede": ("Every part of Gift Aid that goes wrong goes wrong here. Not because declarations "
          "are hard to collect, but because a declaration is a statement with a date on it "
          "and charities store it as a tick."),
 "tags": ["Gift Aid", "declarations", "HMRC", "compliance", "extraction", "serverless"],
 "takeaways": [
  "Store the effective date, not just the fact of a declaration.",
  "A declaration can cover the past, but only if its wording says so.",
  "A verbal declaration needs a written confirmation sent to the donor.",
  "Cancellation is a date too, and it ends coverage from that date.",
  "One donor can have several declarations. Keep them all.",
 ],
 "blocks": [
  ("h2", "Three ways a declaration arrives"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "A paper form", "sub": ["signed and dated,", "usually by hand"],
       "icon": "doc", "label": "scan or photo"},
      {"title": "A web form", "sub": ["timestamped by", "the server"], "icon": "browser",
       "label": "direct"},
      {"title": "Said out loud", "sub": ["on the phone or", "at the door"], "icon": "phone",
       "label": "needs written confirmation"}],
    "target": {"title": "Donor record", "sub": ["donor, effective date,", "what it covers"],
               "icon": "person",
               "then": {"title": "Coverage window", "sub": ["from this date until", "cancelled"],
                        "icon": "calendar"}},
    "note": "The third route is the one people forget has an extra step: a verbal declaration "
            "is only valid once the charity has sent the donor a written record of it."}),
   "Three routes, one record. What comes out is not a flag on a donor; it is a window of "
   "time with a beginning.",
   "Three routes for a Gift Aid declaration converging on one donor record",
   "Three boxes on the left feed one box on the right. A paper form, signed and dated usually "
   "by hand, arrives by scan or photo. A web form is timestamped by the server and arrives "
   "directly. A declaration said out loud on the phone or at the door needs written "
   "confirmation. All three converge on the Donor record holding donor, effective date and "
   "what it covers, which feeds a box labelled Coverage window: from this date until "
   "cancelled. A note says the third route is the one people forget has an extra step, "
   "because a verbal declaration is only valid once the charity has sent the donor a written "
   "record of it."),
  ("h3", "Why a tick is not enough"),
  ("p", "A donor record that says <code>gift_aid: true</code> answers the wrong question. The "
        "question is not whether this donor has ever signed a declaration; it is whether a "
        "declaration was in force on the day of this particular donation. Those are the same "
        "thing only for donors who signed before they ever gave, which is a minority."),
  ("p", "The failure is quiet and it goes in the expensive direction. A charity that collects "
        "declarations at its Christmas appeal and then claims on the whole year has claimed "
        "on donations that were not covered, and that is the case HMRC takes back with "
        "interest. The opposite mistake &mdash; not claiming on covered donations &mdash; only "
        "costs money."),
  ("h2", "What a declaration actually says"),
  ("fig", ("chain", {
    "entry": {"title": "Declaration", "sub": ["however it", "arrived"], "icon": "doc"},
    "steps": [
      {"title": "Identify the donor", "sub": ["name and a home", "address"], "icon": "person",
       "exit": {"title": "Ask", "sub": ["no address means", "no claim"], "icon": "alarm",
                "label": "incomplete"}},
      {"title": "Read the effective date", "sub": ["signed, or the date", "it names"], "icon": "calendar"},
      {"title": "Read the scope", "sub": ["future only, or the", "past four years too"], "icon": "search"},
      {"title": "Record the confirmation", "sub": ["donor confirms they", "pay enough tax"], "icon": "check"},
      {"title": "Open the window", "sub": ["coverage runs from", "here"], "icon": "flow"}],
    "note": "The third step is the one that pays. A declaration whose wording covers the "
            "previous four years turns donations you had written off back into claims."}),
   "Five steps and one stop. A declaration without a home address is not a valid declaration, "
   "and it is better to find that out on the day than in an audit.",
   "A declaration read into a dated coverage window",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled "
   "Declaration, however it arrived. Identify the donor captures a name and a home address, "
   "with a side exit reading incomplete: Ask, because no address means no claim. Read the "
   "effective date takes the date signed or the date it names. Read the scope records whether "
   "it covers future donations only or the past four years too. Record the confirmation "
   "stores the donor's statement that they pay enough tax. Open the window starts coverage "
   "from that point. A note says the third step is the one that pays, because a declaration "
   "whose wording covers the previous four years turns donations you had written off back "
   "into claims."),
  ("h3", "Retrospective declarations are the cheapest money in the system"),
  ("p", "A declaration can be worded to cover donations already made, going back four years. "
        "Most standard forms do exactly this and most charities do not notice, because the "
        "donor record has no field for it. Adding one field and re-running the routing over "
        "the past four years is, for a lot of charities, the largest single Gift Aid win "
        "available to them, and it costs a query."),
  ("p", "It is also the one place where the honest answer is the profitable one. The wording "
        "either covers the past or it does not, it is written on the form, and reading it is "
        "cheaper than guessing in either direction."),
  ("callout", "The five fields, and why each one is there", [
   "<strong>Donor identity.</strong> Name and a home address. HMRC matches on these.",
   "<strong>Effective date.</strong> The day coverage begins. Not the day you filed it.",
   "<strong>Scope.</strong> Future only, or the previous four years as well.",
   "<strong>Tax confirmation.</strong> The donor's own statement, and when they made it.",
   "<strong>Cancellation date.</strong> Null until it is not. Coverage ends here.",
  ]),
  ("h2", "One donor, several declarations"),
  ("p", "People sign again. They sign at an event having already signed online, or they "
        "cancel and later re-start. The record is therefore a list, not a flag, and coverage "
        "on any given date is a question you ask the list rather than a column you read."),
  ("p", "This costs almost nothing to build and it is the difference between a system that "
        "can answer <em>was this donation covered</em> and one that can only answer <em>is "
        "this donor signed up</em>. The second question is the one that produces a claim you "
        "later have to repay."),
 ],
},
{
 "slug": "routing-a-donation",
 "title": "Routing a donation: Gift Aid, small donations, or neither",
 "nav": "Routing",
 "read": 5, "words": 810,
 "desc": ("How each donation is sorted into the scheme it qualifies for, and why the "
          "unclaimable pile is the most useful output."),
 "og": ("575 donations worth 8,925 pounds in Gift Aid went unclaimed. The system's job is to "
        "produce that number, not to hide it."),
 "abstract": ("Matching donations to donors and dates, sorting them into the two schemes and "
              "a residual pile, and reporting the residual as a finding rather than a gap."),
 "lede": ("Every donation is worth twenty-five per cent more or it is not, and the difference "
          "is decided by facts that were all true on the day it arrived. Routing is the step "
          "that asks the question while the answer is still knowable."),
 "tags": ["Gift Aid", "GASDS", "routing", "donations", "charity", "serverless"],
 "takeaways": [
  "Match on the donation date against the coverage window, not on donor status.",
  "Cash in a bucket has no donor and may still be claimable another way.",
  "Over thirty pounds and no declaration is worth nothing. Count it anyway.",
  "Record the reason on every unclaimable donation.",
  "The unclaimable list, ranked by value, is next year's fundraising plan.",
 ],
 "blocks": [
  ("h2", "One donation, three possible answers"),
  ("fig", ("chain", {
    "entry": {"title": "A donation", "sub": ["amount, date,", "method"], "icon": "money"},
    "steps": [
      {"title": "Match a donor", "sub": ["by reference, or", "not at all"], "icon": "person"},
      {"title": "Was it covered?", "sub": ["a window open on", "this date"], "icon": "calendar",
       "exit": {"title": "Gift Aid", "sub": ["claim 25% on", "this donation"], "icon": "check",
                "label": "yes"}},
      {"title": "Small and in cash?", "sub": ["30 pounds or less,", "cash or contactless"],
       "icon": "counter",
       "exit": {"title": "Small donations", "sub": ["no declaration", "needed"], "icon": "counter",
                "label": "yes"}},
      {"title": "Neither", "sub": ["record the reason,", "and the value"], "icon": "alarm"}],
    "note": "The last box is not a failure branch. It is the output that tells a charity "
            "which donors to ask, and it is ranked by what the answer would be worth."}),
   "Four steps and two ways out early. A donation leaves this chain labelled, and the label "
   "is what the claim is built from.",
   "A donation routed into Gift Aid, small donations, or neither",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled "
   "A donation with amount, date and method. Match a donor tries by reference or not at all. "
   "Was it covered checks for a coverage window open on this date, with a side exit reading "
   "yes: Gift Aid, claim twenty-five per cent on this donation. Small and in cash checks for "
   "thirty pounds or less in cash or contactless, with a side exit reading yes: Small "
   "donations, no declaration needed. Neither records the reason and the value. A note says "
   "the last box is not a failure branch but the output that tells a charity which donors to "
   "ask, ranked by what the answer would be worth."),
  ("h3", "Matching a donor is the boring hard part"),
  ("p", "A bank transfer carries a reference the donor typed. A card payment carries whatever "
        "the gateway passed through. A standing order carries the same reference for eleven "
        "years and then changes when the donor's bank migrates. None of this is difficult; it "
        "is just work, and it is where a routing system earns its keep or quietly does not."),
  ("p", "Where a match is uncertain the donation goes to a human rather than to a scheme. A "
        "wrongly matched donation claimed against somebody else's declaration is the exact "
        "shape of error that turns into a repayment, and the cost of asking is one line on a "
        "list."),
  ("h2", "Where the money actually went"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Gift Aid", "parts": [("v", 35700)]},
      {"label": "Small donations", "parts": [("v", 1975)]},
      {"label": "Unclaimed", "parts": [("v", 8925)]}],
    "series": [("v", "Value of the tax reclaim", "#4A90D9")],
    "unit": "GBP ",
    "note": "The third bar is a fifth of the first. It is also the only one of the three that "
            "can be changed by a phone call."}),
   "The same year in money rather than in counts. Nothing about the third bar is a tax "
   "decision.",
   "Gift Aid claimed, small donations claimed, and Gift Aid unclaimed",
   "Three vertical bars. Gift Aid at thirty-five thousand seven hundred pounds. Small "
   "donations at one thousand nine hundred and seventy-five pounds. Unclaimed at eight "
   "thousand nine hundred and twenty-five pounds. A note says the third bar is a fifth of the "
   "first, and it is the only one of the three that can be changed by a phone call."),
  ("h3", "Why count what you cannot claim"),
  ("p", "Because the number is actionable and nothing else in the finance pack is. A charity "
        "that knows it lost eight thousand nine hundred and twenty-five pounds to missing "
        "declarations, and can see which fifty donors account for most of it, has a task with "
        "a value attached. A charity that only knows what it claimed has a number to feel "
        "good about."),
  ("p", "It also changes the design of the donation form, which is usually where the problem "
        "starts. Most of the unclaimable pile in the worked example came through a single "
        "route that never asked the question, and that is a five-minute fix that nobody makes "
        "until somebody counts."),
  ("h2", "The reason field"),
  ("p", "Every unclaimable donation carries a reason: no declaration, declaration started "
        "later, donor cancelled, donor not a UK taxpayer, over the small-donation limit, or "
        "no donor identified. Six values, and they lead to completely different actions."),
  ("p", "A pile of donations marked <em>declaration started later</em> is worth a letter "
        "asking whether the donor is willing to sign a form covering the previous four years. "
        "A pile marked <em>donor not a UK taxpayer</em> is worth nothing and should never be "
        "asked again. Collapsing both into <em>not claimable</em> loses the difference."),
 ],
},
{
 "slug": "building-the-claim",
 "title": "Building the claim, and the cap that catches people out",
 "nav": "The claim",
 "read": 5, "words": 790,
 "desc": ("Turning routed donations into a claim, the small-donations allowance, and the "
          "matching rule that ties one scheme to the other."),
 "og": ("The small-donations scheme is capped at ten times your ordinary Gift Aid claim. Claim "
        "nothing the normal way and the easy money disappears too."),
 "abstract": ("Assembling a claim from routed donations against each scheme's published "
              "limits, including the matching rule between them."),
 "lede": ("Once every donation is labelled, the claim is arithmetic. The part worth knowing "
          "is that the two schemes are not independent: the one that needs no paperwork is "
          "limited by the one that does."),
 "tags": ["Gift Aid", "GASDS", "HMRC", "limits", "charity", "serverless"],
 "takeaways": [
  "The claim is a sum. Getting there was the work.",
  "The small-donations allowance is annual and does not roll over.",
  "That allowance is also capped at ten times the ordinary Gift Aid claimed.",
  "Claim within four years of the end of the accounting period.",
  "Never claim a partial period. Wait for the close.",
 ],
 "blocks": [
  ("h2", "The two schemes are not independent"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Gift Aid claimed", "sub": ["GBP 35,700 from", "2,905 donations"], "icon": "check"},
      {"title": "Matching rule", "sub": ["small route capped at", "10x that"], "icon": "link"},
      {"title": "Headroom", "sub": ["GBP 357,000 of small", "donations allowed"], "icon": "flow"},
      {"title": "Annual allowance", "sub": ["the scheme's own", "yearly ceiling"], "icon": "stop"},
      {"title": "Claimed", "sub": ["GBP 1,975 on", "GBP 7,900"], "icon": "money"}],
    "title": "WHY THE EASY MONEY DEPENDS ON THE HARD MONEY",
    "note": "Here the matching rule binds on nothing, because ordinary Gift Aid is large. For "
            "a charity that claims almost none, it is the binding constraint."}),
   "Five boxes, and the second is the one nobody expects. A charity with no declarations "
   "cannot fall back on the scheme that needs none.",
   "How the small-donations route is limited by the ordinary Gift Aid claim",
   "A horizontal row of five boxes joined by arrows. Gift Aid claimed, thirty-five thousand "
   "seven hundred pounds from two thousand nine hundred and five donations. Matching rule: "
   "the small route is capped at ten times that. Headroom: three hundred and fifty-seven "
   "thousand pounds of small donations allowed. Annual allowance: the scheme's own yearly "
   "ceiling. Claimed: one thousand nine hundred and seventy-five pounds on seven thousand "
   "nine hundred. A note says the matching rule binds on nothing here because ordinary Gift "
   "Aid is large, but for a charity that claims almost none it is the binding constraint."),
  ("h3", "What the arithmetic actually is"),
  ("p", "Gift Aid is the basic rate reclaimed on the gross equivalent of the donation, which "
        "works out at twenty-five pence per pound given. There is no tapering, no threshold "
        "and no discretion. Every routed donation contributes its amount times a quarter, and "
        "the claim is the sum."),
  ("p", "The small-donations route pays the same rate on donations that qualified for it, up "
        "to an annual allowance, and that allowance does not carry forward. A charity sitting "
        "on a large cash income and a thin declaration file will hit both the allowance and "
        "the matching rule, and it is worth knowing which one bit first, because they have "
        "different fixes."),
  ("h2", "Timing"),
  ("fig", ("chain", {
    "entry": {"title": "Period close", "sub": ["the accounting", "year ends"], "icon": "calendar"},
    "steps": [
      {"title": "Freeze the routing", "sub": ["no late declarations", "change this run"], "icon": "lock"},
      {"title": "Sum by scheme", "sub": ["ordinary, then", "small donations"], "icon": "counter"},
      {"title": "Apply the caps", "sub": ["allowance, then the", "matching rule"], "icon": "filter"},
      {"title": "Produce the schedule", "sub": ["one line per donation", "or aggregate"], "icon": "report"},
      {"title": "Write the evidence", "sub": ["before anything is", "submitted"], "icon": "archive"}],
    "note": "Freezing first is what makes the claim reproducible. A declaration that arrives "
            "the next morning belongs to the next run, not this one."}),
   "Five steps in a fixed order. The freeze is not bureaucracy; it is what lets somebody "
   "re-run this in four years and get the same answer.",
   "Building a claim after the accounting period closes",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled "
   "Period close, the accounting year ends. Freeze the routing means no late declarations "
   "change this run. Sum by scheme totals ordinary Gift Aid then small donations. Apply the "
   "caps applies the allowance then the matching rule. Produce the schedule gives one line "
   "per donation or an aggregate. Write the evidence happens before anything is submitted. A "
   "note says freezing first is what makes the claim reproducible, and a declaration arriving "
   "the next morning belongs to the next run rather than this one."),
  ("h3", "Four years, and why you should not use them"),
  ("p", "A claim can be made up to four years after the end of the accounting period it "
        "relates to, which is generous and is mostly there for exactly the case this system "
        "is designed to prevent. It is worth using once, deliberately, when a charity first "
        "builds this and discovers what it has been missing."),
  ("p", "After that it should never be needed. A claim made annually against a frozen routing "
        "is a twenty-minute job; a four-year catch-up is an archaeology project, and the "
        "records that make it possible are exactly the records that decay."),
  ("callout", "What the claim run has to produce", [
   "<strong>The schedule.</strong> What is being claimed, by scheme and by donation.",
   "<strong>The caps applied.</strong> Which limit bound, and by how much.",
   "<strong>The excluded.</strong> Every donation not claimed, with its reason.",
   "<strong>The frozen inputs.</strong> Declarations and donations exactly as they stood.",
   "<strong>A re-runnable query.</strong> Same inputs, same answer, four years later.",
  ]),
 ],
},
{
 "slug": "evidence-that-outlives-the-claim",
 "title": "The evidence has to outlive the claim by six years",
 "nav": "Evidence",
 "read": 5, "words": 800,
 "desc": ("What an audit asks for, why it cannot be reconstructed afterwards, and how to "
          "store it so it is still an answer in 2032."),
 "og": ("HMRC does not ask whether you claimed correctly. It asks you to show that you did, "
        "for a donation somebody made four years ago."),
 "abstract": ("Assembling and retaining the record that supports each claimed donation, and "
              "the design consequences of a six-year retention duty."),
 "lede": ("The claim is money in the bank within a few weeks. The obligation it creates lasts "
          "years, and it is an obligation to produce evidence rather than to have been "
          "right."),
 "tags": ["Gift Aid", "HMRC", "audit", "records", "retention", "serverless"],
 "takeaways": [
  "Keep the declaration, not a note that one existed.",
  "Freeze the donation record as it was when claimed.",
  "Store the reason for every exclusion as well as every inclusion.",
  "Six years after the end of the accounting period, not six years from now.",
  "Cancellation and correction are events to keep, not edits to make.",
 ],
 "blocks": [
  ("h2", "What an audit actually asks"),
  ("fig", ("system", {
    "outside": [
      {"title": "A question", "sub": ["about one donation,", "years later"], "icon": "search"},
      {"title": "The claim", "sub": ["what was submitted", "and when"], "icon": "report"},
      {"title": "The rules then", "sub": ["rates and limits as", "they stood"], "icon": "key"}],
    "inside": [
      {"title": "The declaration", "sub": ["the actual document,", "not a flag"], "icon": "doc"},
      {"title": "The donation", "sub": ["frozen as it was", "when claimed"], "icon": "money"},
      {"title": "The reasoning", "sub": ["why this one", "qualified"], "icon": "check"}],
    "edges": [{"from": 0, "to": 0, "label": "asks"},
              {"from": 1, "to": 1, "label": "identifies"},
              {"from": 2, "to": 2, "label": "governs", "up": True}],
    "note": "None of the three boxes inside can be produced later from a live system, because "
            "a live system has moved on. They are written at claim time or not at all."}),
   "Three inputs to an audit and three things it needs to see. The system's job is that all "
   "three still exist and still line up.",
   "What an audit asks for and what has to already exist",
   "Three boxes across the top sit outside the AWS account. A question about one donation "
   "years later. The claim: what was submitted and when. And The rules then: rates and limits "
   "as they stood. Each connects by an arrow to the AWS account container below, labelled "
   "asks, identifies and governs. Inside are three components. The declaration, meaning the "
   "actual document rather than a flag. The donation, frozen as it was when claimed. And The "
   "reasoning: why this one qualified. A note says none of the three boxes inside can be "
   "produced later from a live system because a live system has moved on, so they are written "
   "at claim time or not at all."),
  ("h3", "A flag is not evidence"),
  ("p", "The single most common shape of failure is a donor record with a Gift Aid box ticked "
        "and no document behind it. It is enough to build a claim from and not enough to "
        "defend one, and the gap between those two states is invisible until somebody asks."),
  ("p", "So the declaration itself is kept: the scan, the web submission with its timestamp, "
        "or the written confirmation sent after a verbal declaration. It is a small file, "
        "there is one per donor rather than one per donation, and it is the cheapest thing in "
        "the system to store and the most expensive to be missing."),
  ("h2", "Six years, counted from the right place"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Donation", "sub": ["the money", "arrives"], "icon": "money"},
      {"title": "Period close", "sub": ["the accounting", "year ends"], "icon": "calendar"},
      {"title": "Claim", "sub": ["submitted and", "paid"], "icon": "check"},
      {"title": "Retention runs", "sub": ["six years from the", "period end"], "icon": "archive"},
      {"title": "Then delete", "sub": ["and record that", "you did"], "icon": "stop"}],
    "title": "THE CLOCK STARTS AT THE PERIOD END, NOT THE DONATION",
    "note": "A donation in the first month of a financial year is held nearly seven years. "
            "Getting the start date wrong deletes evidence while it is still required."}),
   "Five stages, and the fourth is longer than people assume. The clock does not start when "
   "the money arrives.",
   "Retention measured from the end of the accounting period",
   "A horizontal row of five boxes joined by arrows. Donation, the money arrives. Period "
   "close, the accounting year ends. Claim, submitted and paid. Retention runs six years from "
   "the period end. Then delete, and record that you did. A note says a donation in the first "
   "month of a financial year is held nearly seven years, and getting the start date wrong "
   "deletes evidence while it is still required."),
  ("h3", "Corrections are events"),
  ("p", "A donor cancels. A declaration turns out to have the wrong address. A donation is "
        "refunded. Each of these changes what should have been claimed, and each is a new "
        "fact with its own date rather than a reason to edit an old one."),
  ("p", "Keeping them as events costs nothing and makes the difference between a system that "
        "can say <em>this was correct when claimed and changed in March</em> and one that can "
        "only say <em>this is wrong now</em>. The first is a conversation with HMRC. The "
        "second is a repayment."),
  ("callout", "The sentence the evidence has to be able to write", [
   "This donation of 40 pounds was received on 12 March.",
   "It was matched to a donor whose declaration took effect on 3 February.",
   "That declaration is attached, with the home address HMRC matches on.",
   "It was claimed in the schedule submitted on 30 June, line 1,844.",
   "The declaration was cancelled on 9 September, which is after this donation.",
  ]),
  ("h2", "Where this ends"),
  ("p", "The system does not make the charity compliant, because compliance is a thing people "
        "do rather than a thing software has. What it does is make the compliant answer the "
        "cheap one: the declaration is already stored, the routing already has a reason "
        "against every donation, and the claim already froze its own inputs."),
  ("p", "The next post prices it and the one after gives the service names, the tables and "
        "the IAM. The interesting thing about the cost is that almost none of it scales with "
        "donations, because the expensive step happens once per donor rather than once per "
        "gift."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="charity",
 volumes=[(1, "1 charity"), (6, "6 charities"), (20, "20 charities")],
 read_each=0.09,
 msgs_each=3.0,
 store_base=0.32,
 store_growth=0.0012,
 lede=("The model runs once per declaration, not once per donation. A charity collecting a "
       "few hundred new declarations a year is a few cents; the donation file is parsed. Six "
       "charities is a small federation or a diocese sharing one deployment. Here is where "
       "each cent goes."),
 takeaway_extra=("Nothing runs per donation, so a charity that doubles its income does not "
                 "double its bill."),
 risks=[
  "<strong>Running a model over the donation export.</strong> It is fixed-header CSV and it is "
  "the largest file here. Parse it; a model would cost more than the Gift Aid on it.",
  "<strong>Re-reading declarations to answer a routing question.</strong> Extract once into a "
  "coverage window and query the window.",
  "<strong>Storing declaration scans at full resolution for seven years.</strong> Keep the "
  "original until the claim is filed, then a downsized copy with the evidence.",
 ],
 per_unit_note=("Roughly one model call per new declaration, against a mid-tier model. A "
                "declaration is a short document with five fields and a date, and the date is "
                "the only one that is ever ambiguous. This is not a place where a frontier "
                "model earns its price, and the volume is a few hundred a year rather than a "
                "few thousand a day."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ga",
 lede=("The same system with the service names filled in: what reads a declaration, what "
       "routes a donation, what builds the claim, and where the evidence sits."),
 outside=[
  {"title": "Declarations", "sub": ["scans, web posts,", "confirmations"], "icon": "doc"},
  {"title": "Donation exports", "sub": ["CSV from the bank", "and the gateway"], "icon": "money"},
  {"title": "Scheme rules", "sub": ["rates, limits,", "dated"], "icon": "key"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["uploads and the", "period close"], "icon": "bucket"},
  {"title": "Lambda x4", "sub": ["declare, route,", "claim, evidence"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["donors, donations,", "claims"], "icon": "database"}],
 note="eu-west-2. One account. Declarations arrive all year; donations load nightly; the "
      "claim runs once per accounting period and freezes its inputs.",
 region="eu-west-2",
 region_why=("London, because the donor addresses in a declaration are personal data belonging "
             "to UK residents and there is no reason to move them. Bedrock model availability "
             "is checked here rather than assumed; if the model needed is not present, the "
             "extraction step is the only part that would move."),
 diagram_desc=(
  "Three boxes across the top sit outside the AWS account. Declarations as scans, web posts "
  "and confirmations. Donation exports as CSV from the bank and the gateway. And Scheme "
  "rules: rates and limits, dated. Each connects to the AWS account container below. Inside "
  "are three components. S3 with EventBridge handling uploads and the period close. Four "
  "Lambda functions covering declare, route, claim and evidence. And three DynamoDB tables "
  "holding donors, donations and claims. A note says eu-west-2, one account, declarations "
  "arrive all year, donations load nightly, and the claim runs once per accounting period and "
  "freezes its inputs."),
 functions=[
  ["<code>ga-declare</code>", "S3 put, declarations prefix",
   "Reads a declaration into a donor and a dated coverage window", "60s / 1024MB"],
  ["<code>ga-route</code>", "Nightly, after the donation load",
   "Matches each donation to a donor and labels it with a scheme", "120s / 1024MB"],
  ["<code>ga-claim</code>", "EventBridge, on period close",
   "Freezes the routing, applies the caps, produces the schedule", "300s / 2048MB"],
  ["<code>ga-evidence</code>", "Step after claim",
   "Writes declarations, frozen donations and reasoning into one object", "300s / 2048MB"],
 ],
 roles=[
  ["<code>ga-declare-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "One model id; the declarations prefix; donors"],
  ["<code>ga-route-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>",
   "The donations prefix; donors read; donations write"],
  ["<code>ga-claim-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "donors and donations read; claims write"],
  ["<code>ga-evidence-role</code>",
   "<code>dynamodb:Query</code>, <code>s3:PutObject</code>, <code>ses:SendEmail</code>",
   "All three tables read; the evidence prefix write-once; one verified identity"],
 ],
 tables=[
  ("Table: donors",
   "PK   charity_id#donor_id S\n"
   "SK   'decl#' + effective S   one item per declaration, newest last\n"
   "     effective_from      S   the date coverage begins\n"
   "     covers_past         BOOL whether the wording reaches back four years\n"
   "     cancelled_on        S   null until it is not\n"
   "     home_address        S   HMRC matches on this; no address, no claim\n"
   "     source              S   paper | web | verbal\n"
   "     confirmed_taxpayer  BOOL the donor's own statement\n"
   "     evidence_key        S   the document itself, not a flag\n\n"
   "A donor is a LIST of declarations, not a boolean. Coverage on a given\n"
   "date is a question asked of the list; a single gift_aid flag answers a\n"
   "different question and is the most common cause of an over-claim."),
  ("Table: donations",
   "PK   charity_id#period   S\n"
   "SK   donation_id         S\n"
   "     donated_on          S   the date every decision turns on\n"
   "     amount              N\n"
   "     method              S   bank | card | cash | contactless\n"
   "     donor_id            S   null for a bucket collection\n"
   "     route               S   gift_aid | small_donations | none\n"
   "     reason              S   set only when route is none\n"
   "     claim_id            S   set when a claim freezes this row\n\n"
   "reason takes six values and they lead to different actions: no\n"
   "declaration, declaration started later, donor cancelled, not a UK\n"
   "taxpayer, over the small-donation limit, no donor identified.\n"
   "Collapsing them into 'not claimable' throws away the only actionable\n"
   "output this system produces."),
  ("Table: claims",
   "PK   charity_id          S\n"
   "SK   period#claim_id     S   claims are never overwritten\n"
   "     submitted_on        S\n"
   "     gift_aid_donations  N\n"
   "     gift_aid_value      N\n"
   "     small_donations     N\n"
   "     small_value         N\n"
   "     binding_cap         S   allowance | matching | none\n"
   "     excluded_count      N   reported as prominently as the claim\n"
   "     excluded_value      N\n"
   "     evidence_key        S\n\n"
   "binding_cap records WHICH limit bound rather than that one did. The\n"
   "annual allowance and the matching rule have completely different fixes,\n"
   "and a claim that just says 'capped' cannot tell a charity which one it\n"
   "is looking at."),
  ],
 inbound=[
  "<strong>Declarations arrive by upload or mailbox</strong> and both land in the same "
  "function. A photograph of a signed form and a web submission are the same document here.",
  "<strong>Donation exports are parsed, not read by a model.</strong> They are fixed-header "
  "CSV, they are the largest files in the system, and a model would be slower and less "
  "accurate than a parser.",
  "<strong>An uncertain donor match goes to a human.</strong> A donation claimed against "
  "somebody else's declaration is the error that becomes a repayment, and asking costs one "
  "line on a list.",
  "<strong>The claim waits for the period close</strong>, and freezes its inputs before it "
  "sums anything. A declaration arriving the next morning belongs to the next run."],
 model_notes=[
  "<strong>One call per declaration.</strong> Nothing per donation, per claim or per donor "
  "lookup. The bill does not move when donations do.",
  "<strong>A mid-tier model.</strong> A declaration has five fields and the only ambiguous one "
  "is the date; a frontier model buys nothing here.",
  "<strong>Dates come back as strings in a stated format</strong>, never parsed by the model "
  "into a guess. A UK form writes 03/02 and the difference between February and March is a "
  "claim.",
  "<strong>Scope is extracted, not assumed.</strong> Whether the wording covers the previous "
  "four years is a field on the record, because it is the single largest recoverable amount "
  "in most charities.",
  "<strong>No model touches routing or arithmetic.</strong> Both have to be re-runnable and "
  "explainable years later, and both are a query and a multiplication."],
 gotchas=[
  "Store the declaration's effective date, not a boolean. Coverage is a window with a "
  "beginning, and a donation is claimable or not according to where its own date falls.",
  "Read whether the wording covers the previous four years. Most standard forms do, most "
  "charities have no field for it, and re-running the routing over that period is usually the "
  "largest single win available.",
  "Keep the document, not a note that one exists. A ticked box builds a claim and does not "
  "defend one, and the difference is invisible until somebody asks.",
  "Record which cap bound the small-donations claim. The annual allowance and the matching "
  "rule against ordinary Gift Aid have different fixes.",
  "Count the retention from the end of the accounting period, not from the donation. A gift "
  "in the first month of a year is held nearly seven years.",
  "Report the excluded donations and their value beside the claim. It is the only number in "
  "the pack that a phone call can change.",
 ],
))
