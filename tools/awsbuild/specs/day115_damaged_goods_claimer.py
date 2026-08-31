"""Day 115 -- 2026-08-17 -- Damaged goods claimer."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "damaged-goods-claimer"
NAME = "Damaged goods claimer"

SPEC = {
 "slug": SLUG, "date": "2026-08-17", "name": NAME,
 "tagline": ("Captures the evidence for a damage claim in the two minutes before the packaging "
             "goes in the bin, works out which deadline applies, and is honest about which claims "
             "are not worth filing."),
 "lede": ("A small system for the unglamorous business of claiming for goods that arrive broken. "
          "The packaging is the evidence and it gets thrown away within the hour; the deadline "
          "runs from delivery rather than from discovery; and a good proportion of claims cost "
          "more to file than they recover, which is a finding rather than a failure. Seven posts "
          "on the same system, one diagram at a time, with a cost breakdown and an engineering "
          "reference at the end."),
 "keywords": ["damage claims", "carriers", "freight", "evidence", "logistics", "serverless"],
 "icons": ["truck", "image", "money"],
 "faq": [
  ("What is a damaged goods claimer?",
   "A small serverless system that captures photographic evidence at delivery, tracks the "
   "applicable claim deadline, assembles the claim pack, and reports which claims are worth "
   "filing."),
  ("Why does the packaging matter so much?",
   "Because it is the only evidence of how the damage happened. A carrier's first question is "
   "whether the outer packaging was damaged, and by the time anybody asks, it is usually in a "
   "skip."),
  ("What is concealed damage?",
   "Damage found after delivery, once the packaging is opened. It has a much shorter deadline and "
   "a much weaker position, and the post on it explains what actually helps."),
  ("Does it file claims automatically?",
   "No. A claim is a formal assertion about facts and it is signed by a person. The system "
   "assembles it and tracks the deadline."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "damaged-goods-claimer-on-aws",
 "title": "A damaged goods claimer on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Captures damage evidence at delivery, tracks the deadline, assembles the claim, and "
          "says which are worth filing. AWS, about $2 a month."),
 "og": ("The packaging is the evidence and it is in the bin within the hour. Everything else in a "
        "damage claim is recoverable; that is not."),
 "abstract": ("The whole system on one page -- capture, deadline, decide &mdash; and the two "
              "minutes that determine whether a claim can be made at all."),
 "lede": ("A crate arrives with a corner stoved in. Somebody photographs the broken item, throws "
          "the crate in the skip because it is taking up space, and files a claim three days "
          "later. The carrier asks whether the outer packaging was damaged. Nobody can say, and "
          "the claim is declined. This post walks through a small system designed around those "
          "two minutes."),
 "tags": ["damage claims", "carriers", "freight", "evidence", "logistics", "serverless"],
 "takeaways": [
  "Photograph the packaging before the contents, and keep the packaging until the claim closes.",
  "The deadline usually runs from delivery, not from when the damage was found.",
  "Concealed damage has a shorter clock and a weaker position; both are worth knowing at the door.",
  "Many claims cost more to file than they recover. Knowing which is a real output.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "A damaged delivery", "sub": ["and its packaging"], "icon": "truck"},
      {"title": "Carrier terms", "sub": ["windows and limits"], "icon": "doc"},
      {"title": "Whoever files", "sub": ["a person, always"], "icon": "person"}],
    "inside": [
      {"title": "Evidence capture", "sub": ["packaging first,", "then contents"], "icon": "image"},
      {"title": "Deadline clock", "sub": ["from delivery,", "per carrier"], "icon": "clock"},
      {"title": "Claim assembler", "sub": ["pack, value,", "worth filing?"], "icon": "money"}],
    "edges": [{"from": 0, "to": 0, "label": "photographs"},
              {"from": 1, "to": 1, "label": "the applicable window"},
              {"from": 2, "to": 2, "label": "a pack, and a recommendation", "up": True}],
    "note": "The first box has about two minutes. Everything else has days."}),
   "Three things outside the account, three pieces inside it. The asymmetry in the note is the "
   "reason the design looks the way it does.",
   "System: damage evidence captured, deadlines tracked, claims assembled",
   "Three boxes across the top sit outside the AWS account. On the left, A damaged delivery and "
   "its packaging. In the middle, Carrier terms, with their windows and limits. On the right, "
   "Whoever files, always a person. Each connects by an arrow to the AWS account container below. "
   "Photographs flow down into the account. The applicable window feeds in. A pack and a "
   "recommendation go back out. Inside the AWS account are three components in a row. On the "
   "left, Evidence capture, taking the packaging first and then the contents. In the middle, the "
   "Deadline clock, running from delivery and configured per carrier. On the right, the Claim "
   "assembler, producing the pack, the value, and whether it is worth filing. A note at the "
   "bottom says the first box has about two minutes and everything else has days."),
  ("h3", "The packaging is the case"),
  ("p", "Every damage claim turns on the same question: was the damage visible from outside, and "
        "did anybody note it at delivery? A photograph of a broken item establishes that it is "
        "broken. A photograph of a crushed crate with the carrier's label in frame establishes "
        "how and when it got that way."),
  ("p", "The packaging is also the thing most likely to be gone. It is bulky, it is in the way, "
        "and disposing of it is the natural next action after unpacking. A system that does "
        "nothing else but reliably produce the sentence \"keep the packaging until this closes\" "
        "would earn its cost."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Evidence capture.</strong> A fixed photograph sequence at the door and a hold on the "
   "packaging. Part 2.",
   "<strong>The deadline clock.</strong> Which window applies, from when, per carrier and per "
   "damage type. Part 3.",
   "<strong>The claim assembler.</strong> Builds the pack, computes the value, and says whether "
   "filing is worth the effort. Parts 4 and 5.",
  ]),
  ("h2", "One claim, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Damage seen", "sub": ["at delivery"], "icon": "search"},
      {"title": "5 photographs", "sub": ["packaging first"], "icon": "image"},
      {"title": "Note annotated", "sub": ["before signing"], "icon": "doc"},
      {"title": "Deadline set", "sub": ["7 days, this carrier"], "icon": "clock"},
      {"title": "Filed day 2", "sub": ["£680, with the pack"], "icon": "money"}],
    "title": "ONE CLAIM, END TO END",
    "note": "Seven days sounds generous and is four working days over a bank holiday weekend."}),
   "The same system as one line. The note is the reason the deadline is computed rather than "
   "remembered.",
   "One damage claim from discovery at delivery to filing",
   "A horizontal row of five boxes joined by arrows. Damage seen: at delivery. Five photographs: "
   "packaging first. Note annotated: before signing. Deadline set: seven days for this carrier. "
   "Filed day two: six hundred and eighty pounds, with the pack. A note says seven days sounds "
   "generous and is four working days over a bank holiday weekend."),
  ("h2", "In plain words"),
  ("p", "A pallet arrives and one corner is visibly crushed. The person receiving opens the app, "
        "which walks them through five photographs in a fixed order: the pallet as delivered on "
        "the vehicle, the damaged corner with the carrier label readable, the packaging opened, "
        "the damaged item, and the item's own label."),
  ("p", "The system generates the wording for the delivery note &mdash; damage noted before "
        "signature, which is the difference between a claim and an argument &mdash; and puts a "
        "hold on the packaging: a printed label saying do not dispose until this claim closes, "
        "with the reference."),
  ("p", "Behind that, the clock starts. This carrier's terms give seven days from delivery for "
        "visible damage, which the system converts into an actual date. The claim pack assembles "
        "itself from the photographs, the delivery note, the invoice and the purchase order, and "
        "somebody files it on day two after checking that the value is worth the twenty minutes."),
  ("callout", "Design rules that shaped every decision", [
   "Photograph the packaging before the contents, in a fixed order, every time.",
   "Hold the packaging physically, with a label, until the claim resolves.",
   "The deadline runs from delivery unless the carrier's terms say otherwise.",
   "Note the damage on the delivery note before signing, always.",
   "A claim is filed by a person. The system assembles and reminds.",
   "Say when a claim is not worth filing. That is a useful answer.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Damage claims fail for procedural reasons far more often than for factual ones. The "
        "goods were genuinely damaged, the carrier genuinely damaged them, and the claim is "
        "declined because it was filed on day nine, or because the delivery note was signed "
        "clean, or because nobody can produce a photograph of the outer packaging."),
  ("p", "All three of those are preventable by a system that does very little except at exactly "
        "the right moments: a fixed photograph sequence at the door, a computed date, and a label "
        "on a crate. The clever parts of this problem are not where the value is."),
  ("p", "The next four posts walk through each piece: how the evidence gets captured, how the "
        "deadline is worked out, which claims are worth filing, and what the claims add up to. "
        "One diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-the-evidence-gets-captured",
 "title": "How the evidence gets captured",
 "nav": "How evidence is captured",
 "read": 5, "words": 750,
 "desc": ("The fixed photograph sequence, why the packaging is held, and the delivery note "
          "wording that keeps a claim alive."),
 "og": ("Five photographs in a fixed order beats any number taken thoughtfully, because nobody is "
        "thoughtful with a driver waiting."),
 "abstract": ("The five-photograph sequence and why the order matters, the physical hold on the "
              "packaging, the delivery note annotation, and what to do when the driver will not "
              "wait."),
 "lede": ("The evidence for a damage claim exists for about an hour and then most of it is gone. "
          "Capturing it is not difficult; it is a matter of doing a fixed short thing at a moment "
          "when nobody has decided yet whether it matters."),
 "tags": ["damage claims", "evidence", "photography", "logistics", "documentation", "serverless"],
 "takeaways": [
  "Five photographs, always the same five, always in the same order.",
  "The carrier's label must be readable in at least one of them.",
  "Put a physical hold label on the packaging with the claim reference.",
  "Annotate the delivery note before signing; the wording is generated.",
  "If the driver will not wait, photograph and write 'unexamined -- driver would not wait'.",
 ],
 "blocks": [
  ("h2", "The five photographs"),
  ("fig", ("chain", {
    "entry": {"title": "Damage noticed", "sub": ["at the door"], "icon": "search"},
    "steps": [
      {"title": "1. As delivered", "sub": ["on the vehicle if possible"], "icon": "truck"},
      {"title": "2. The damage, wide", "sub": ["with the carrier label"], "icon": "image"},
      {"title": "3. Packaging opened", "sub": ["showing how it sat"], "icon": "doc"},
      {"title": "4. The item damaged", "sub": ["close"], "icon": "search"},
      {"title": "5. The item's label", "sub": ["code and batch"], "icon": "form"}],
    "note": "One and two are the ones that win claims. Four is the one everybody takes first."}),
   "The fixed sequence. It is prescriptive on purpose: a person under time pressure should be "
   "following steps rather than deciding what will matter later.",
   "The five photographs taken in order when damage is found",
   "A vertical chain of five steps entered by a box labelled Damage noticed at the door. Step "
   "one: as delivered, on the vehicle if possible. Step two: the damage, wide, with the carrier "
   "label in frame. Step three: packaging opened, showing how the item sat inside. Step four: the "
   "item damaged, close up. Step five: the item's own label, showing code and batch. A note says "
   "photographs one and two are the ones that win claims, and four is the one everybody takes "
   "first."),
  ("h3", "Why on the vehicle"),
  ("p", "A photograph of the pallet still on the tail lift, damaged, is close to unanswerable. It "
        "establishes the state of the goods before they entered your building, which is the "
        "single fact every carrier dispute is about."),
  ("p", "It is often not possible &mdash; the driver has already unloaded, it is raining, the bay "
        "is full &mdash; and the sequence handles that by allowing a skip with a recorded reason "
        "rather than by leaving the step out. \"Not photographed on vehicle: already unloaded\" "
        "is itself a useful line in a claim."),
  ("h3", "The carrier label in frame"),
  ("p", "This is the small detail that converts a photograph of a broken thing into a photograph "
        "of a specific carrier's broken thing on a specific date. The app prompts for it "
        "explicitly rather than hoping, because it is exactly the sort of thing that is obvious "
        "afterwards and invisible at the time."),
  ("h2", "Holding the packaging"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Claim opened", "sub": ["reference generated"], "icon": "doc"},
      {"title": "Label printed", "sub": ["'DO NOT DISPOSE'"], "icon": "form"},
      {"title": "On the packaging", "sub": ["and the pallet"], "icon": "truck"},
      {"title": "Held", "sub": ["until the claim closes"], "icon": "lock"},
      {"title": "Released", "sub": ["automatically, on close"], "icon": "check"}],
    "title": "THE CHEAPEST PART OF THE SYSTEM",
    "note": "A printed label on a crate is the highest-value component here by a wide margin."}),
   "The physical hold. It is a printed sticker and it prevents the single most common reason a "
   "claim collapses.",
   "How damaged packaging is held until a claim resolves",
   "A horizontal row of five boxes. Claim opened: reference generated. Label printed: do not "
   "dispose. On the packaging, and on the pallet. Held until the claim closes. Released "
   "automatically on close. A note says a printed label on a crate is the highest-value component "
   "here by a wide margin."),
  ("p", "Carriers frequently want to inspect, and they want to inspect the packaging rather than "
        "the item. A claim where the response is \"we disposed of it\" is a claim that is over, "
        "regardless of how good the photographs were."),
  ("p", "The release step matters too. Without it, damaged packaging accumulates indefinitely "
        "because nobody is sure whether it is still needed, and after a while people start "
        "throwing it away on judgement, which is where the discipline breaks down."),
  ("h2", "The delivery note"),
  ("callout", "The generated wording, and what each part does", [
   "<strong>\"Damage noted at delivery before signature.\"</strong> Establishes the sequence, "
   "which is what a clean signature otherwise destroys.",
   "<strong>\"1 of 4 pallets, outer packaging crushed at one corner.\"</strong> Specific and "
   "checkable.",
   "<strong>\"Contents examined: 3 units of BRG-4MM damaged.\"</strong> Or, if not examined, say "
   "so explicitly.",
   "<strong>\"Photographed. Packaging retained.\"</strong> Tells the carrier the evidence exists.",
   "<strong>\"Signed subject to the above.\"</strong> The phrase that keeps the claim alive.",
   "<strong>Driver receives the same words</strong> on their copy, which is what stops it being "
   "your unilateral note.",
  ]),
  ("p", "Nobody composes this in a doorway. The system produces it from the photographs and the "
        "counts already entered, the person reads it, and it goes on both copies. That is the "
        "entire mechanism and it is the difference between most successful and most failed "
        "claims."),
  ("h3", "When the driver will not wait"),
  ("p", "It happens, and the answer is not to give up on the paperwork. Photograph what is "
        "visible, write \"received unexamined &mdash; driver would not wait for inspection\" on "
        "the note, sign that, and record the time. That phrase preserves a great deal more "
        "position than a clean signature does."),
  ("p", "It is also worth counting how often it happens, per carrier and per driver, because a "
        "carrier whose drivers routinely refuse to wait is making a choice that has a cost, and "
        "the count is the evidence for that conversation."),
  ("p", "Next: how long you have."),
 ],
},
{
 "slug": "how-the-deadline-is-worked-out",
 "title": "How the deadline is worked out",
 "nav": "How the deadline works",
 "read": 5, "words": 730,
 "desc": ("Windows that run from delivery, concealed damage and its shorter clock, and the "
          "reminders that go out before the last day."),
 "og": ("The clock starts when the goods arrive, not when you find the damage. That single fact "
        "kills more claims than any other."),
 "abstract": ("Why the window runs from delivery, how concealed damage is handled, how carrier "
              "terms are configured, and the reminder schedule that actually gets claims filed."),
 "lede": ("Claim windows are short, they are measured from a date nobody thinks about, and they "
          "are different for every carrier. That combination is why so many valid claims are "
          "filed too late."),
 "tags": ["damage claims", "deadlines", "carriers", "concealed damage", "logistics", "serverless"],
 "takeaways": [
  "The window runs from delivery in almost every carrier's terms.",
  "Concealed damage has a shorter window and a much weaker position.",
  "Carrier terms are configuration, entered once, with a note of where they came from.",
  "Working days and public holidays matter when the window is three days.",
  "Reminders go out at half the window and at two days remaining, to a named person.",
 ],
 "blocks": [
  ("h2", "From delivery, not discovery"),
  ("fig", ("chain", {
    "entry": {"title": "Damage exists", "sub": ["found at some point"], "icon": "search"},
    "steps": [
      {"title": "Found at delivery?", "sub": ["before signing"], "icon": "branch",
       "exit": {"title": "Concealed damage", "sub": ["shorter clock, weaker case"],
                "icon": "alarm", "label": "no"}},
      {"title": "Which carrier?", "sub": ["their terms, configured"], "icon": "truck"},
      {"title": "Window from delivery", "sub": ["3, 7 or 14 days"], "icon": "clock"},
      {"title": "In working days?", "sub": ["most are"], "icon": "branch",
       "exit": {"title": "Calendar days", "sub": ["much tighter"], "icon": "alarm",
                "label": "no"}},
      {"title": "A date, on the claim", "sub": ["not a duration"], "icon": "form"}],
    "note": "Store a date. A duration requires somebody to do arithmetic under pressure."}),
   "How the deadline is computed. The last box is the small design decision that makes the "
   "reminders possible.",
   "How a damage claim deadline is computed from the carrier's terms",
   "A vertical chain of five steps entered by a box labelled Damage exists, found at some point. "
   "Step one asks whether it was found at delivery, before signing; if not it exits to Concealed "
   "damage, with a shorter clock and a weaker case. Step two identifies the carrier and their "
   "configured terms. Step three sets the window from delivery, typically three, seven or "
   "fourteen days. Step four asks whether it is measured in working days, which most are; if not "
   "it exits to Calendar days, which is much tighter. Step five records a date on the claim "
   "rather than a duration. A note says to store a date, because a duration requires somebody to "
   "do arithmetic under pressure."),
  ("h3", "Concealed damage"),
  ("p", "Damage found after the delivery note was signed clean is a materially different "
        "situation. The window is usually shorter &mdash; often three days rather than seven "
        "&mdash; and the carrier's starting position is that the goods were fine when they "
        "handed them over, which the signature supports."),
  ("p", "What helps: photographing the packaging still sealed or as it was found, opening it in a "
        "way that preserves how the item sat inside, and reporting the same day. What does not "
        "help is anything about how obviously the damage must have happened in transit, which is "
        "an argument rather than evidence."),
  ("p", "The honest framing is that concealed damage claims succeed less often, and the system "
        "says so at the point somebody is deciding whether to spend twenty minutes on one. That "
        "is more useful than treating every claim as equally likely."),
  ("h2", "Three days is not three days"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Delivered Tuesday", "parts": [("work", 3), ("lost", 0)]},
      {"label": "Delivered Thursday", "parts": [("work", 3), ("lost", 2)]},
      {"label": "Thursday, bank holiday", "parts": [("work", 3), ("lost", 3)]}],
    "series": [("work", "Working days in the window", "#7AA116"),
               ("lost", "Calendar days that are not working days", "#DD344C")],
    "unit": "",
    "note": "The same three-day window is three days or six depending on the delivery date."}),
   "Why the deadline is computed rather than counted on fingers. A Thursday delivery before a "
   "bank holiday leaves the same window spanning nearly a week of calendar time.",
   "How the same three-day claim window spans different calendar periods",
   "A stacked bar chart with three bars measured in days. Two series: working days in the window "
   "in green, and calendar days that are not working days in red. Delivered Tuesday: three "
   "working days and no lost days. Delivered Thursday: three working days plus two non-working "
   "days. Delivered Thursday before a bank holiday: three working days plus three non-working "
   "days. A note says the same three-day window is three days or six depending on the delivery "
   "date."),
  ("p", "The practical consequence is that a person estimating \"we have until about Monday\" is "
        "sometimes right and sometimes two days out, and the two-days-out case is the one where "
        "the claim is lost. Computing the date once, at the point the claim opens, removes the "
        "estimation entirely."),
  ("h3", "Carrier terms as configuration"),
  ("p", "Each carrier gets a small record: the visible damage window, the concealed damage "
        "window, whether they are working or calendar days, the liability cap, and a note saying "
        "which version of their terms it came from and when it was checked."),
  ("p", "That last field is the one that stops the configuration quietly going stale. Terms "
        "change, and a window that was seven days in 2024 and is now five will produce late "
        "claims that look like process failures."),
  ("h2", "Reminders that work"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Claim opened", "sub": ["deadline computed"], "icon": "clock"},
      {"title": "Halfway", "sub": ["one reminder"], "icon": "email"},
      {"title": "2 days left", "sub": ["to a named person"], "icon": "person"},
      {"title": "Last day", "sub": ["and their manager"], "icon": "alarm"},
      {"title": "Missed", "sub": ["recorded, with the value"], "icon": "search"}],
    "title": "THE REMINDER LADDER",
    "note": "The last box exists so that missed deadlines are a number rather than an anecdote."}),
   "The reminder schedule. Escalating to a second person on the last day is the step that "
   "converts most nearly-missed claims into filed ones.",
   "The reminder ladder for an approaching claim deadline",
   "A horizontal row of five boxes. Claim opened: deadline computed. Halfway: one reminder. Two "
   "days left: to a named person. Last day: and their manager. Missed: recorded, with the value. "
   "A note says the last box exists so that missed deadlines are a number rather than an "
   "anecdote."),
  ("p", "Recording the missed ones with their value is the part that changes behaviour. \"We "
        "missed the deadline on four claims worth eleven hundred pounds last quarter\" is a "
        "sentence that produces a process change; the same four claims individually forgotten "
        "produce nothing."),
  ("p", "Next: which of them are worth filing at all."),
 ],
},
{
 "slug": "which-claims-are-worth-filing",
 "title": "Which claims are worth filing",
 "nav": "Which are worth filing",
 "read": 5, "words": 730,
 "desc": ("The time a claim takes, the liability caps that make some of them pointless, and why "
          "filing everything is not the answer."),
 "og": ("A twenty-minute claim for forty pounds against a carrier who caps liability at their "
        "freight charge is not diligence, it is a hobby."),
 "abstract": ("What a claim actually costs in time, how liability caps change the arithmetic, why "
              "some small claims are still worth filing, and how the recommendation is made."),
 "lede": ("The instinct is that every valid claim should be filed, and it is wrong in a way worth "
          "being precise about, because the effort that goes into unwinnable small claims is "
          "effort not spent on the ones that would have paid."),
 "tags": ["damage claims", "cost benefit", "liability", "carriers", "decisions", "serverless"],
 "takeaways": [
  "A claim is roughly twenty minutes plus whatever the follow-up costs.",
  "Liability caps are often per-kilo or per-consignment and can be well below the goods' value.",
  "Below a threshold, log the damage and do not file. Record that decision.",
  "Some small claims are still worth filing as evidence of a pattern.",
  "The system recommends; a person decides, in about ten seconds.",
 ],
 "blocks": [
  ("h2", "What a claim costs"),
  ("table", ["Step", "Time", "Notes"], [
   ["Assembling the pack", "2 minutes", "Automated here; 20 minutes without a system"],
   ["Checking and filing", "10 minutes", "Portal or form, per carrier"],
   ["First chase", "5 minutes", "Needed on most claims"],
   ["Second chase or dispute", "20&ndash;60 minutes", "Needed on maybe a third"],
   ["Total, typical", "~20 minutes", "Rising sharply if it is disputed"],
  ]),
  ("p", "Twenty minutes of somebody's attention is not free, and the fourth row is the one that "
        "makes small claims a bad trade: a disputed forty-pound claim can absorb an hour, and the "
        "dispute rate is higher on small claims because the carrier's incentive to resolve "
        "quickly is lower."),
  ("h2", "Liability caps"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Pallet, 400kg", "parts": [("cap", 520), ("uncovered", 0)]},
      {"label": "Small parcel, 2kg", "parts": [("cap", 26), ("uncovered", 274)]},
      {"label": "Light, high value", "parts": [("cap", 13), ("uncovered", 1187)]}],
    "series": [("cap", "Recoverable under the carrier's cap, £", "#7AA116"),
               ("uncovered", "Value above the cap, £", "#DD344C")],
    "unit": "£",
    "note": "A weight-based cap is unrelated to what is in the box. The third bar is common."}),
   "Three consignments against a typical per-kilo liability cap. The third case &mdash; light, "
   "valuable goods &mdash; is where the standard cap recovers almost nothing.",
   "Recoverable value against liability caps for three consignment types",
   "A stacked bar chart with three bars in pounds. Two series: recoverable under the carrier's "
   "cap in green, and value above the cap in red. A four hundred kilogram pallet has a cap of "
   "five hundred and twenty pounds and nothing above it. A two kilogram small parcel has a cap of "
   "twenty-six pounds and two hundred and seventy-four pounds above it. A light, high value "
   "consignment has a cap of thirteen pounds and one thousand one hundred and eighty-seven pounds "
   "above it. A note says a weight-based cap is unrelated to what is in the box, and the third "
   "bar is common."),
  ("p", "Knowing the cap before filing changes the decision entirely, and it also changes an "
        "earlier decision: consignments where the cap is far below the value are the ones to "
        "insure separately or to declare, and the pattern report in the next post makes that "
        "visible."),
  ("p", "The cap is per carrier and per service, configured alongside the deadline windows. It is "
        "twenty minutes of reading terms once and it prevents a recurring waste of effort."),
  ("h2", "The recommendation"),
  ("fig", ("chain", {
    "entry": {"title": "A damage record", "sub": ["evidence captured"], "icon": "image"},
    "steps": [
      {"title": "Recoverable value", "sub": ["after the cap"], "icon": "money"},
      {"title": "Under £50?", "sub": ["after the cap"], "icon": "branch",
       "exit": {"title": "Log, do not file", "sub": ["unless it is a pattern"], "icon": "database",
                "label": "yes"}},
      {"title": "Concealed?", "sub": ["weaker case"], "icon": "branch",
       "exit": {"title": "File if over £200", "sub": ["a higher bar"], "icon": "branch",
                "label": "yes"}},
      {"title": "Evidence complete?", "sub": ["packaging photographed?"], "icon": "branch",
       "exit": {"title": "File anyway, note the gap", "sub": ["and fix the process"],
                "icon": "alarm", "label": "no"}},
      {"title": "File it", "sub": ["pack ready, deadline set"], "icon": "check"}],
    "note": "Thresholds are configuration. What matters is that a decision is made and recorded."}),
   "How the recommendation is produced. It is four rules over two numbers, and its value is "
   "entirely in being applied consistently rather than by mood.",
   "How the system decides whether to recommend filing a claim",
   "A vertical chain of five steps entered by a box labelled A damage record with evidence "
   "captured. Step one computes the recoverable value after the cap. Step two asks whether it is "
   "under fifty pounds after the cap; if so it exits to Log, do not file, unless it is a pattern. "
   "Step three asks whether the damage was concealed, which is a weaker case; if so it exits to "
   "File if over two hundred pounds, a higher bar. Step four asks whether the evidence is "
   "complete, in particular whether the packaging was photographed; if not it exits to File "
   "anyway, note the gap, and fix the process. Step five files it, with the pack ready and the "
   "deadline set. A note says thresholds are configuration, and what matters is that a decision "
   "is made and recorded."),
  ("h3", "Log, do not file"),
  ("p", "A damage record that is logged but not filed is not a failure. It is a recorded event "
        "that costs nothing, feeds the pattern analysis, and provides the count when somebody "
        "eventually needs to say \"this carrier has damaged fourteen consignments this year\"."),
  ("p", "The decision is recorded with its reason, so that a year later nobody has to wonder "
        "whether the small claims were missed or declined. \"Not filed: recoverable value £22 "
        "after cap\" is an answer."),
  ("h3", "The exception for patterns"),
  ("p", "A small claim that would normally be logged should be filed when it is the third of its "
        "kind from the same carrier on the same route, because at that point the value of the "
        "claim is not the money. It is the record of having formally raised it, which is what "
        "makes a subsequent conversation about the route possible."),
  ("p", "So the threshold rule has one override: if this is the third similar incident in a "
        "quarter, file it regardless of value and say so in the claim. That is a rule the system "
        "can apply and a person would not remember to."),
  ("p", "Next: what the claims add up to."),
 ],
},
{
 "slug": "what-the-claims-add-up-to",
 "title": "What the claims add up to",
 "nav": "What they add up to",
 "read": 5, "words": 720,
 "desc": ("The route, the packaging and the carrier that cause most of it, and the finding that "
          "usually beats every claim put together."),
 "og": ("Most damage is concentrated in a small number of causes, and the fix is usually cheaper "
        "than a year of claims."),
 "abstract": ("How damage records aggregate by carrier, route and packaging, why the packaging "
              "finding is usually the largest, and what to report."),
 "lede": ("Claims recover some of the money. The aggregate record is what stops the damage "
          "happening, and it is worth considerably more than the claims are."),
 "tags": ["damage claims", "patterns", "packaging", "carriers", "reporting", "serverless"],
 "takeaways": [
  "Group by carrier, by route, by packaging type, and by which supplier packed it.",
  "The packaging grouping usually finds the largest single cause.",
  "Include logged-but-not-filed damage in the analysis; it is most of the volume.",
  "Report damage rate per hundred consignments, not raw counts.",
  "The output is usually a packaging change or a route change, not a carrier change.",
 ],
 "blocks": [
  ("h2", "Four groupings"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "By carrier", "sub": ["rate per 100 consignments"], "icon": "truck",
       "label": "the obvious one"},
      {"title": "By route or depot", "sub": ["often one transfer point"], "icon": "map",
       "label": "surprisingly sharp"},
      {"title": "By packaging", "sub": ["how the supplier packed it"], "icon": "form",
       "label": "usually the largest"}],
    "target": {"title": "A quarterly view", "sub": ["filed and logged together"], "icon": "chart",
               "then": {"title": "Usually a packaging fix", "sub": ["cheaper than the claims"],
                        "icon": "check"}},
    "note": "Changing carrier is the response people reach for and rarely the one that helps."}),
   "The groupings and where they lead. The packaging lane is the one that produces a fix rather "
   "than a negotiation.",
   "Three ways damage records are grouped and what they usually show",
   "Three boxes stacked on the left. By carrier: rate per hundred consignments, labelled the "
   "obvious one. By route or depot: often one transfer point, labelled surprisingly sharp. By "
   "packaging: how the supplier packed it, labelled usually the largest. All three converge on A "
   "quarterly view with filed and logged damage together, and that leads down to Usually a "
   "packaging fix, cheaper than the claims. A note says changing carrier is the response people "
   "reach for and rarely the one that helps."),
  ("h3", "Why packaging wins"),
  ("p", "Carriers handle a great many consignments and their damage rates are broadly similar, "
        "because they are all doing roughly the same thing with roughly the same equipment. What "
        "differs enormously is how well things are packed, and that is largely determined by the "
        "supplier who packed them."),
  ("p", "A product that arrives damaged from one supplier and never from another, shipped by the "
        "same carrier on the same route, is a packaging finding with a name attached. That "
        "conversation &mdash; with the supplier, about corner protection or a stronger carton "
        "&mdash; is usually cheap and permanent, where a carrier negotiation is neither."),
  ("h2", "Rates, not counts"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Carrier A", "parts": [("damaged", 14)]},
      {"label": "Carrier B", "parts": [("damaged", 9)]},
      {"label": "Carrier A, per 100", "parts": [("rate", 1.2)]},
      {"label": "Carrier B, per 100", "parts": [("rate", 4.5)]}],
    "series": [("damaged", "Damaged consignments, count", "#ED7100"),
               ("rate", "Damaged per 100 consignments", "#DD344C")],
    "unit": "",
    "note": "A has more incidents and a quarter of the rate. Counts point at the wrong carrier."}),
   "The same two carriers by count and by rate. Reporting counts systematically blames whoever "
   "you use the most.",
   "Two carriers compared by damage count and by damage rate",
   "A bar chart with four bars. Two series: damaged consignments as a count in orange, and "
   "damaged per hundred consignments in red. Carrier A has fourteen damaged consignments; Carrier "
   "B has nine. Expressed as a rate, Carrier A is one point two per hundred and Carrier B is four "
   "point five per hundred. A note says A has more incidents and a quarter of the rate, so counts "
   "point at the wrong carrier."),
  ("p", "This is a small reporting decision with a real consequence, because the carrier you use "
        "most will always have the most incidents and will always look worst on a count. Several "
        "carrier relationships have been damaged by a chart that was arithmetic rather than "
        "evidence."),
  ("h3", "Include the logged ones"),
  ("p", "Damage that was recorded but not claimed is most of the volume, and leaving it out of "
        "the analysis means the pattern report describes only the expensive incidents. The cheap "
        "ones are where the frequency signal lives."),
  ("p", "It also keeps the report honest about the total: \"£4,100 claimed, £1,900 recovered, and "
        "a further £2,600 of damage logged and not claimed\" describes the actual cost of damage, "
        "where the claim figures alone describe about a third of it."),
  ("h2", "What the report says"),
  ("callout", "The quarterly page", [
   "<strong>Damage recorded:</strong> 41 consignments, total value &pound;6,700.",
   "<strong>Claimed:</strong> 18, value &pound;4,100. <strong>Recovered:</strong> &pound;1,900 so "
   "far, 3 still open.",
   "<strong>Not claimed:</strong> 23, value &pound;2,600, mostly below the cap threshold.",
   "<strong>Largest cause:</strong> one supplier's cartons on one product &mdash; 11 incidents, "
   "&pound;2,900.",
   "<strong>By carrier, per 100 consignments:</strong> A 1.2, B 4.5, C 0.9.",
   "<strong>Deadlines missed:</strong> 2, value &pound;480. Both concealed damage found late.",
  ]),
  ("p", "The fourth line is what the system is for. Eleven incidents on one product from one "
        "supplier is a specific, fixable thing worth almost three thousand pounds a quarter, and "
        "it is invisible without an aggregate view of individually forgettable events."),
  ("p", "The last line is the honest one. Missed deadlines are process failures, they have a "
        "value, and putting them in the same report as the recoveries is what keeps the process "
        "from quietly degrading."),
  ("h3", "The response is rarely a new carrier"),
  ("p", "Switching carrier is disruptive, the replacement's damage rate is unknown until you have "
        "a year of data, and the cause was frequently not the carrier. The findings that "
        "reliably pay are packaging changes, declaring value on the light expensive "
        "consignments, and occasionally avoiding one depot."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="damage record",
 volumes=[(15, "15 records"), (50, "50 records"), (200, "200 records")],
 read_each=0.0,
 msgs_each=1.1,
 lede=("Damage is rare relative to deliveries, and the storage is photographs. Fifty damage "
       "records a month is a business receiving a great deal of freight. Here is where each cent "
       "goes."),
 takeaway_extra=("Photographs dominate storage; the reminder ladder dominates messaging, at "
                 "several messages per claim."),
 risks=[
  "<strong>Keeping full-resolution photographs indefinitely.</strong> Five per record at phone "
  "resolution. Resize on upload and expire to Infrequent Access after the claim closes.",
  "<strong>Reminding daily.</strong> The ladder is three messages, not one a day. Daily reminders "
  "get filtered and then the deadline is missed anyway.",
  "<strong>Storing claim packs as generated PDFs forever.</strong> Regenerate on demand from the "
  "photographs and records; the pack is a view, not an artefact.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. Messaging is the reminder "
                "ladder plus the carrier notification, which is why it is above one per record."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="dg",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the carrier configuration, and the deadline computation."),
 outside=[
  {"title": "The receiving device", "sub": ["five photographs"], "icon": "image"},
  {"title": "Carrier terms", "sub": ["windows and caps"], "icon": "doc"},
  {"title": "Whoever files", "sub": ["and gets reminded"], "icon": "person"}],
 inside=[
  {"title": "S3 + API", "sub": ["photographs,", "capture endpoint"], "icon": "storage"},
  {"title": "Lambda x3", "sub": ["capture, remind, aggregate"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["claims, carriers"], "icon": "database"}],
 note="us-east-1. One account. Deadlines stored as dates; packaging holds released on close.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The receiving device, sending five "
  "photographs. Carrier terms, with their windows and caps. And Whoever files, who also gets "
  "reminded. Inside the account, three groups. S3 holding photographs alongside an API providing "
  "a capture endpoint. Three Lambda functions named capture, remind and aggregate. And two "
  "DynamoDB tables named claims and carriers. A note gives the region as us-east-1, one account, "
  "and states that deadlines are stored as dates and packaging holds are released on close."),
 functions=[
  ["<code>dg-capture</code>", "API, from the device",
   "Stores photographs, computes the deadline, generates the note wording and the hold label",
   "30s / 1024&nbsp;MB"],
  ["<code>dg-remind</code>", "EventBridge, daily",
   "Runs the reminder ladder; records missed deadlines with their value", "60s / 512&nbsp;MB"],
  ["<code>dg-aggregate</code>", "EventBridge, weekly",
   "Groups by carrier, route, packaging and supplier; computes rates per 100 consignments",
   "120s / 1024&nbsp;MB"]],
 roles=[
  ["<code>dg-capture-role</code>",
   "<code>s3:PutObject</code>, <code>dynamodb:PutItem</code>, <code>dynamodb:GetItem</code>",
   "The photographs prefix; claims; read-only on carriers"],
  ["<code>dg-remind-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Claims; one verified identity"],
  ["<code>dg-aggregate-role</code>", "<code>dynamodb:Query</code>",
   "Read-only across both tables"]],
 tables=[
  ("Table: claims",
   "PK   claim_ref         S   DG-2026-0184 -- printed on the hold label\n"
   "     carrier           S\n"
   "     service           S   the cap depends on this, not just the carrier\n"
   "     delivered_at      S   the clock starts here\n"
   "     found_at          S   equal to delivered_at, or concealed\n"
   "     concealed         BOOL\n"
   "     deadline          S   a date, computed once\n"
   "     photos            L   5 s3 keys, in the fixed order\n"
   "     note_annotated    BOOL signed subject to the note?\n"
   "     goods_value       N\n"
   "     cap_value         N   recoverable after the carrier's cap\n"
   "     decision          S   file | log | filed | recovered | declined | missed\n"
   "     decision_reason   S   required when the decision is log\n"
   "     packaging_held    BOOL cleared when the claim closes\n\n"
   "`decision_reason` is what makes 'we did not claim for this' an answer\n"
   "rather than a gap, a year later."),
  ("Table: carriers",
   "PK   carrier#service   S   palletline#economy\n"
   "     visible_days      N   7\n"
   "     concealed_days    N   3\n"
   "     working_days      BOOL true for most\n"
   "     cap_basis         S   per_kg | per_consignment | declared\n"
   "     cap_rate_pence    N\n"
   "     terms_version     S   'Nov 2025 conditions'\n"
   "     terms_checked_at  S   2026-04-02\n\n"
   "`terms_checked_at` is the field that stops this configuration quietly\n"
   "going stale and producing late claims that look like process failures.")],
 inbound=[
  "<strong>Capture happens on the device</strong> in a fixed five-photograph sequence, with a "
  "skip that records a reason rather than silently omitting a step.",
  "<strong>The deadline is computed at capture</strong> and stored as a date, using the carrier's "
  "working-day setting and a public holiday calendar.",
  "<strong>The hold label prints immediately</strong> with the claim reference, because the "
  "packaging decision happens within the hour.",
  "<strong>Logged-but-not-filed records</strong> use the same table and appear in every "
  "aggregation. They are most of the volume."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Deadlines are date arithmetic, the cap is a "
  "lookup, and the recommendation is four rules.",
  "<strong>The tempting use</strong> is assessing damage severity from the photographs. The "
  "carrier will form their own view, and an automated severity score adds nothing to the claim.",
  "<strong>The wrong use</strong> is drafting the claim narrative. A claim is a formal assertion "
  "about facts and its wording should be a template a person checked.",
  "<strong>Classifying damage type</strong> from a short picklist at capture is better than "
  "inferring it, and it is one tap.",
  "<strong>The cost page assumes none</strong>, which is why messaging and storage are the only "
  "variable bands."],
 gotchas=[
  "Store the deadline as a date, not a duration. Arithmetic under pressure over a bank holiday is "
  "how valid claims get filed late.",
  "Print the hold label at capture. The packaging decision happens within the hour and no email "
  "reaches anybody in time.",
  "Key the carrier configuration on carrier and service. Caps differ by service, and using the "
  "carrier alone produces a recoverable value that is wrong.",
  "Include logged-not-filed records in every aggregation. They are most of the volume and all of "
  "the frequency signal.",
  "Report damage per hundred consignments, never as a count. A count always blames whoever you "
  "ship with most."],
))
