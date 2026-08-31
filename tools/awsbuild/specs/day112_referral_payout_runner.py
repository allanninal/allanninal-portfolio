"""Day 112 -- 2026-08-14 -- Referral payout runner."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "referral-payout-runner"
NAME = "Referral payout runner"

SPEC = {
 "slug": SLUG, "date": "2026-08-14", "name": NAME,
 "tagline": ("Works out which referrals have actually been earned, pays them on a stated day "
             "under the rules that were published when the referral was made, and shows every "
             "person exactly what they were paid for and what was held."),
 "lede": ("A small system that records referrals, decides when each one becomes payable, holds "
          "the ones that look wrong without silently swallowing them, and produces a statement "
          "somebody can argue with. The hard part is not the arithmetic; it is that every "
          "decision here is about somebody else's money. Seven posts on the same system, one "
          "diagram at a time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["referral programme", "affiliate payouts", "commission", "fraud", "disputes",
              "serverless"],
 "icons": ["person", "money", "check"],
 "faq": [
  ("What is a referral payout runner?",
   "A small serverless system that tracks referrals, decides when each becomes payable under the "
   "rules in force at the time, holds suspicious ones for review, and pays the rest on a stated "
   "schedule with an itemised statement."),
  ("When does a referral become payable?",
   "Not at signup. After the referred customer's refund window closes and any qualifying "
   "condition is met, because paying earlier means clawing money back, which is worse."),
  ("What happens if the rules change?",
   "Referrals are paid under the rules published when they were made. The rule version is stamped "
   "on every referral and the system can never apply a newer rule retroactively."),
  ("How does it handle suspected fraud?",
   "It holds, tells the person it is holding and why, and gives them a way to respond. Silent "
   "withholding is what kills referral programmes."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "referral-payout-runner-on-aws",
 "title": "A referral payout runner on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Records referrals, decides when each is earned, holds the suspicious ones openly, and "
          "pays on a stated day. AWS, about $2 a month."),
 "og": ("Every decision in this system is about somebody else's money, which changes what counts "
        "as an acceptable failure mode."),
 "abstract": ("The whole system on one page -- record, qualify, pay -- and the stamped rule "
              "version that keeps a rule change from rewriting what people were promised."),
 "lede": ("Referral programmes fail in a predictable way. Somebody refers three friends, sees "
          "nothing appear for two months, asks, gets a vague answer, and tells everyone the "
          "programme does not pay. The money was usually fine; the visibility was not. This post "
          "walks through a small system built around that failure rather than around the "
          "arithmetic."),
 "tags": ["referral programme", "affiliate payouts", "commission", "fraud", "disputes",
          "serverless"],
 "takeaways": [
  "A referral is stamped with the rule version in force when it was made.",
  "Payable means earned, not signed up. Pay after the refund window, not before.",
  "A held referral is visible to the person it belongs to, with a reason.",
  "Every payout comes with an itemised statement somebody can dispute.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Referrers", "sub": ["with a link", "and a statement"], "icon": "person"},
      {"title": "Orders and refunds", "sub": ["the existing systems"], "icon": "database"},
      {"title": "Payments out", "sub": ["on a stated day"], "icon": "money"}],
    "inside": [
      {"title": "Recorder", "sub": ["referral + the rule", "version at the time"], "icon": "doc"},
      {"title": "Qualifier", "sub": ["earned yet?", "held? why?"], "icon": "check"},
      {"title": "Runner", "sub": ["one run,", "one statement each"], "icon": "money"}],
    "edges": [{"from": 0, "to": 0, "label": "referrals"},
              {"from": 1, "to": 1, "label": "what happened"},
              {"from": 2, "to": 2, "label": "payments and statements", "up": True}],
    "note": "The recorder stamps the rules. Nothing downstream can apply a newer version."}),
   "Three things outside the account, three pieces inside it. The stamp in the first box is what "
   "makes the whole thing defensible when the programme terms change.",
   "System: referrals recorded, qualified and paid",
   "Three boxes across the top sit outside the AWS account. On the left, Referrers, who have a "
   "link and receive a statement. In the middle, Orders and refunds, from the existing systems. "
   "On the right, Payments out, on a stated day. Each connects by an arrow to the AWS account "
   "container below. Referrals flow down into the account. What happened feeds in. Payments and "
   "statements go back out. Inside the AWS account are three components in a row. On the left, "
   "the Recorder, storing the referral together with the rule version in force at the time. In "
   "the middle, the Qualifier, asking whether it is earned yet and, if held, why. On the right, "
   "the Runner, producing one run and one statement each. A note at the bottom says the recorder "
   "stamps the rules, and nothing downstream can apply a newer version."),
  ("h3", "The stamp is the whole design"),
  ("p", "Referral terms change. The commission goes from twenty pounds to fifteen, a product gets "
        "excluded, a minimum order value appears. Every one of those changes is legitimate, and "
        "every one of them creates the same question: what happens to the referral somebody made "
        "last week under the old terms?"),
  ("p", "The answer has to be that it pays under the old terms, and the only way to guarantee "
        "that is to write the rule version onto the referral when it is created and to have no "
        "code path anywhere that reads the current rules for an existing referral. It is a small "
        "amount of engineering that prevents the single most damaging kind of dispute."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The recorder.</strong> Captures the referral, who made it, when, and which published "
   "rule version applies. Part 2.",
   "<strong>The qualifier.</strong> Decides when a referral has actually been earned, and holds "
   "the ones that need a person. Parts 3 and 4.",
   "<strong>The runner.</strong> Pays on a stated day and produces a statement per person, "
   "including the held items. Part 5.",
  ]),
  ("h2", "One referral, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Referral made", "sub": ["rules v4 stamped"], "icon": "person"},
      {"title": "They order", "sub": ["day 3"], "icon": "form"},
      {"title": "Refund window", "sub": ["closes day 17"], "icon": "clock"},
      {"title": "Payable", "sub": ["£20, under v4"], "icon": "check"},
      {"title": "Paid", "sub": ["next run, with a statement"], "icon": "money"}],
    "title": "ONE REFERRAL, END TO END",
    "note": "Rules v5 arrived on day 9 and made no difference to this one. That is the point."}),
   "The same system as one line. The note is the behaviour that makes the programme trustworthy "
   "and it costs one stored field.",
   "One referral from creation through to payment",
   "A horizontal row of five boxes joined by arrows. Referral made: rules version four stamped. "
   "They order: on day three. Refund window: closes on day seventeen. Payable: twenty pounds, "
   "under version four. Paid: on the next run, with a statement. A note says rules version five "
   "arrived on day nine and made no difference to this one, and that is the point."),
  ("h2", "In plain words"),
  ("p", "Somebody shares their link. A friend clicks it and orders three days later. The referral "
        "was recorded when the link was clicked, stamped with rules version four, which said "
        "twenty pounds on any order over fifty."),
  ("p", "On day nine the business drops the commission to fifteen pounds. Version five is "
        "published, dated, and applies to referrals made from that point. This referral was made "
        "under version four, so it stays at twenty."),
  ("p", "On day seventeen the refund window closes with no refund, and the referral becomes "
        "payable. On the next payout run it is paid, and the referrer gets a statement that says: "
        "one referral, ordered 3 August, qualified 17 August, twenty pounds, rules v4. If they "
        "had a second referral being held, that would be on the same statement with the reason "
        "next to it."),
  ("callout", "Design rules that shaped every decision", [
   "Stamp the rule version at creation. Never read current rules for an old referral.",
   "Payable means the money is safe, not that somebody signed up.",
   "A hold is always visible to the person, with a reason and a way to respond.",
   "Every payout produces an itemised statement, including zero-payment runs.",
   "The event log is append-only. A referral's history is never rewritten.",
   "No automatic clawback from a future payout without telling the person first.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The distinguishing feature of this system compared to most of the others in this series "
        "is that its outputs are other people's money, and people notice money. A scheduling "
        "system that is wrong once a month is annoying; a payout system that is wrong once a "
        "month generates a permanent reputation."),
  ("p", "That pushes the design towards conservatism in the payment direction and openness in the "
        "information direction: pay later than feels good, hold when unsure, and tell people "
        "everything about both. Almost every complaint about a referral programme is about "
        "silence rather than about the amount."),
  ("p", "The next four posts walk through each piece: how a referral is recorded, when it becomes "
        "payable, how fraud is handled without punishing everyone, and how a disputed payout gets "
        "resolved. One diagram per post, a cost breakdown, and an engineering reference at the "
        "end."),
 ],
},
{
 "slug": "how-a-referral-gets-recorded",
 "title": "How a referral gets recorded",
 "nav": "How it is recorded",
 "read": 5, "words": 740,
 "desc": ("What counts as the referral moment, the rule stamp, the attribution window, and the "
          "two people claiming the same referral."),
 "og": ("Record the referral at the click, not at the order. The gap between them is where every "
        "dispute lives."),
 "abstract": ("When a referral is created, why the rule version is stamped at that moment, how "
              "long a referral stays live, and how competing claims are resolved."),
 "lede": ("The referral is created before anybody knows whether it will be worth anything, which "
          "is the awkward property that shapes the whole record: you have to write it down at the "
          "moment it happens and then wait to find out if it mattered."),
 "tags": ["referral programme", "attribution", "rules versioning", "audit", "records",
          "serverless"],
 "takeaways": [
  "The referral is created at the click, with the rule version and timestamp.",
  "The attribution window is published, finite, and applies from the click.",
  "First click wins, and the rule is stated in the terms rather than assumed.",
  "Self-referral is detected at recording, not at payout.",
  "The record is append-only; a referral is corrected by a new event, never an edit.",
 ],
 "blocks": [
  ("h2", "The moment of record"),
  ("fig", ("chain", {
    "entry": {"title": "Somebody clicks a link", "sub": ["a referrer's code"], "icon": "route"},
    "steps": [
      {"title": "Is the code live?", "sub": ["not suspended"], "icon": "branch",
       "exit": {"title": "No referral", "sub": ["and the visit is normal"], "icon": "stop",
                "label": "no"}},
      {"title": "Already referred?", "sub": ["by anyone, in window"], "icon": "branch",
       "exit": {"title": "First click keeps it", "sub": ["stated in the terms"], "icon": "check",
                "label": "yes"}},
      {"title": "Same person?", "sub": ["referrer and referred"], "icon": "branch",
       "exit": {"title": "Self-referral", "sub": ["recorded, never payable"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Create the referral", "sub": ["pending"], "icon": "doc"},
      {"title": "Stamp the rule version", "sub": ["v4, published 12 Jul"], "icon": "lock"}],
    "note": "Everything after this reads the stamp. Nothing reads the current rules."}),
   "How a click becomes a recorded referral. The last box is the one that prevents the worst "
   "class of dispute two months later.",
   "How a referral link click becomes a recorded referral",
   "A vertical chain of five steps entered by a box labelled Somebody clicks a link carrying a "
   "referrer's code. Step one asks whether the code is live and not suspended; if not it exits to "
   "No referral, and the visit is treated as normal. Step two asks whether this person has "
   "already been referred by anyone within the window; if so it exits to First click keeps it, as "
   "stated in the terms. Step three asks whether the referrer and the referred person are the "
   "same; if so it exits to Self-referral, recorded but never payable. Step four creates the "
   "referral in a pending state. Step five stamps the rule version, version four published on the "
   "twelfth of July. A note says everything after this reads the stamp, and nothing reads the "
   "current rules."),
  ("h3", "Why first click and not last"),
  ("p", "Two people can plausibly refer the same customer, and whichever rule you choose will "
        "occasionally feel unfair to somebody. First click is the better default for a referral "
        "programme &mdash; unlike advertising attribution &mdash; because the referral is a "
        "personal act and the first person to make it did the work of the recommendation."),
  ("p", "What matters more than the choice is that it is written in the published terms in one "
        "sentence, so the conversation with the second referrer is about a rule they agreed to "
        "rather than about a decision somebody appears to have made about them."),
  ("h3", "The window is published"),
  ("p", "A referral does not last forever. Thirty, sixty or ninety days from the click is "
        "typical, and the number matters less than it being stated and applied consistently. An "
        "unpublished window is discovered by referrers exactly once, at the moment they find out "
        "they were not paid."),
  ("p", "The window runs from the click, not from the signup, and it is stamped alongside the "
        "rule version so that shortening it later cannot retroactively expire referrals that were "
        "still live under the old terms."),
  ("h2", "Append-only, always"),
  ("fig", ("strip", {
    "stages": [
      {"title": "created", "sub": ["3 Aug, v4"], "icon": "doc"},
      {"title": "order_linked", "sub": ["6 Aug, £120"], "icon": "form"},
      {"title": "held", "sub": ["7 Aug, address match"], "icon": "alarm"},
      {"title": "released", "sub": ["9 Aug, by name"], "icon": "person"},
      {"title": "paid", "sub": ["1 Sep, run 2026-09"], "icon": "money"}],
    "title": "ONE REFERRAL'S EVENT LOG",
    "note": "Five rows, none of them edited. The state is derived, never stored as the truth."}),
   "A referral's full history as events. Deriving the state from the log rather than storing it "
   "means the answer to \"why is this held\" always exists.",
   "The append-only event log of a single referral",
   "A horizontal row of five boxes. Created: third of August, rules version four. Order linked: "
   "sixth of August, one hundred and twenty pounds. Held: seventh of August, address match. "
   "Released: ninth of August, by a named person. Paid: first of September, in the September run. "
   "A note says five rows, none of them edited, and the state is derived rather than stored as "
   "the truth."),
  ("p", "The temptation is a status column that gets updated. It works until somebody asks why a "
        "referral that was held in August was paid in September, and the answer is a value that "
        "was overwritten and a timestamp that says only when it last changed."),
  ("p", "Events cost slightly more storage and remove an entire class of unanswerable question. "
        "For a system handling other people's money that is not a close call."),
  ("h3", "Self-referral at recording"),
  ("p", "Catching the obvious cases &mdash; same account, same email, same payment method "
        "&mdash; at the moment of recording is better than catching them at payout, because the "
        "record then says self-referral from the start rather than looking like a payment that "
        "was withheld."),
  ("p", "It also means the referrer finds out immediately if they misunderstood the programme, "
        "which for a good proportion of them is exactly what happened. Somebody ordering through "
        "their own link is more often confused than dishonest."),
  ("p", "Next: when a referral becomes payable."),
 ],
},
{
 "slug": "when-a-referral-becomes-payable",
 "title": "When a referral becomes payable",
 "nav": "When it is payable",
 "read": 5, "words": 740,
 "desc": ("Why signup is the wrong trigger, the refund window, the qualifying condition, and "
          "clawback done properly."),
 "og": ("Paying at signup means clawing money back later. Taking money back from somebody who "
        "already spent it is worse than paying them slowly."),
 "abstract": ("Why payability waits for the refund window, what a qualifying condition should "
              "and should not be, how a payout run works, and how clawback is handled without "
              "surprising anybody."),
 "lede": ("The pressure is always to pay quickly, because a fast payout is a better experience "
          "and referrers ask for it. The reason to resist is that money paid on a referral that "
          "later refunds has to come back from somebody who has already spent it."),
 "tags": ["referral programme", "payouts", "refunds", "clawback", "commission", "serverless"],
 "takeaways": [
  "Payable means the refund window has closed and the order stands.",
  "The qualifying condition should be about the order, not about the referred person's behaviour.",
  "A stated payout day beats a fast one. Predictability is what people actually want.",
  "Clawback is announced before it happens, never taken silently from a future run.",
  "A zero-payment run still produces a statement.",
 ],
 "blocks": [
  ("h2", "The wait"),
  ("fig", ("chain", {
    "entry": {"title": "An order is linked", "sub": ["to a live referral"], "icon": "form"},
    "steps": [
      {"title": "Meets the condition?", "sub": ["from the stamped rules"], "icon": "branch",
       "exit": {"title": "Not qualifying", "sub": ["stated on the statement"], "icon": "stop",
                "label": "no"}},
      {"title": "Refund window open?", "sub": ["usually 14 days"], "icon": "branch",
       "exit": {"title": "Wait", "sub": ["visible as pending"], "icon": "clock", "label": "yes"}},
      {"title": "Refunded or charged back?", "sub": ["check at close"], "icon": "branch",
       "exit": {"title": "Not payable", "sub": ["with the reason"], "icon": "stop",
                "label": "yes"}},
      {"title": "Any hold on it?", "sub": ["fraud or dispute"], "icon": "branch",
       "exit": {"title": "Held", "sub": ["shown, with a reason"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Payable", "sub": ["in the next run"], "icon": "check"}],
    "note": "Every exit shows on the referrer's statement. None of them are silent."}),
   "The four gates between an order and a payment. The note is the property that separates this "
   "from most programmes.",
   "How an order linked to a referral becomes a payable amount",
   "A vertical chain of five steps entered by a box labelled An order is linked to a live "
   "referral. Step one asks whether it meets the qualifying condition from the stamped rules; if "
   "not it exits to Not qualifying, stated on the statement. Step two asks whether the refund "
   "window is still open, usually fourteen days; if so it exits to Wait, visible as pending. Step "
   "three asks whether it was refunded or charged back, checked at the window's close; if so it "
   "exits to Not payable, with the reason. Step four asks whether there is any hold on it for "
   "fraud or dispute; if so it exits to Held, shown with a reason. Step five marks it payable in "
   "the next run. A note says every exit shows on the referrer's statement, and none of them are "
   "silent."),
  ("h3", "Pending is a state people can see"),
  ("p", "The waiting period is not a problem as long as it is visible. A referrer who can see "
        "\"1 referral pending, payable 17 August\" is content; the same referrer seeing nothing at "
        "all for two weeks concludes the programme does not work and stops referring."),
  ("p", "That is the entire difference between a well-regarded referral programme and a badly "
        "regarded one with identical terms, and it is a display concern rather than a payment "
        "concern."),
  ("h3", "Qualifying conditions"),
  ("p", "A minimum order value is a reasonable condition. A first-order-only rule is reasonable. "
        "\"The referred customer must remain active for ninety days\" is not, because it makes "
        "the referrer's payment depend on someone else's behaviour that they cannot influence and "
        "cannot see."),
  ("p", "The test is whether the referrer could have known, at the moment they made the referral, "
        "whether the condition would be met. Conditions that fail that test produce disputes that "
        "are impossible to resolve well, because the referrer is right to be annoyed."),
  ("h2", "The run"),
  ("fig", ("strip", {
    "stages": [
      {"title": "1st of the month", "sub": ["stated in the terms"], "icon": "clock"},
      {"title": "Everything payable", "sub": ["as of the 1st"], "icon": "check"},
      {"title": "Minimum met?", "sub": ["£10 or carry over"], "icon": "branch"},
      {"title": "Pay", "sub": ["one transfer each"], "icon": "money"},
      {"title": "Statement", "sub": ["to everyone, even £0"], "icon": "doc"}],
    "title": "THE MONTHLY RUN",
    "note": "The last box goes to everyone with activity, including people who were paid nothing."}),
   "One payout run. Sending a statement to people who were paid nothing is the unusual step and "
   "is where most of the trust is earned.",
   "How a monthly referral payout run works",
   "A horizontal row of five boxes. First of the month: stated in the terms. Everything payable "
   "as of the first. Minimum met: ten pounds, or carry over. Pay: one transfer each. Statement: "
   "to everyone, even at zero. A note says the last box goes to everyone with activity, including "
   "people who were paid nothing."),
  ("p", "The zero-payment statement is worth the effort it sounds like it costs, which is almost "
        "none since the statement is generated anyway. \"Two referrals pending, one held pending "
        "review, nothing payable this month\" answers the question the person was about to email "
        "about."),
  ("h3", "The minimum payout"),
  ("p", "A minimum exists because transfers cost money, and it is fine as long as the balance "
        "carries over visibly and the person can see how close they are. A minimum that silently "
        "holds four pounds indefinitely looks exactly like not being paid."),
  ("h2", "Clawback, done properly"),
  ("callout", "When a paid referral turns out to be refunded", [
   "<strong>It happens</strong> &mdash; a chargeback lands three months later, outside every "
   "window.",
   "<strong>Do not deduct it silently</strong> from the next run. A statement that is smaller "
   "than expected with no explanation is the worst possible version of this.",
   "<strong>Tell them first,</strong> with the referral, the order, the date and the reason, "
   "before anything is deducted.",
   "<strong>Deduct from future earnings,</strong> never by demanding money back, unless the "
   "amounts are large enough to justify a conversation.",
   "<strong>Below a threshold, absorb it.</strong> Reclaiming eight pounds from somebody who "
   "recommended you costs more than eight pounds.",
  ]),
  ("p", "That last rule is worth stating explicitly in the terms, because it converts an "
        "unavoidable irritation into a visible piece of generosity at negligible cost. The "
        "referrals large enough to be worth reclaiming are rare and are worth a phone call."),
  ("p", "Next: fraud, without punishing everybody else."),
 ],
},
{
 "slug": "how-fraud-is-handled-without-punishing-everyone",
 "title": "How fraud is handled without punishing everyone",
 "nav": "How fraud is handled",
 "read": 6, "words": 770,
 "desc": ("The patterns worth catching, the cost of a false positive, why a hold is always "
          "visible, and the rules that quietly destroy a programme."),
 "og": ("A fraud rule that holds one legitimate referral in twenty will cost more in lost "
        "referrers than the fraud it prevents."),
 "abstract": ("Which fraud patterns are worth detecting, why the false-positive cost dominates, "
              "how a hold is communicated, and the aggressive rules that look prudent and are "
              "not."),
 "lede": ("Referral fraud is real, mostly small, and much less expensive than the standard "
          "response to it. The interesting design question is not how to catch more of it; it is "
          "how to catch it without making honest referrers feel accused."),
 "tags": ["referral programme", "fraud", "false positives", "trust", "reviews", "serverless"],
 "takeaways": [
  "Three patterns are worth catching: self-referral rings, bulk signups, and stolen codes.",
  "A false positive costs a referrer permanently. Weight it accordingly.",
  "A hold is always shown to the person, with the reason, and with a way to respond.",
  "Never suspend an account on an automated signal alone.",
  "Track the false-positive rate as a headline number, not the catch rate.",
 ],
 "blocks": [
  ("h2", "What is worth catching"),
  ("table", ["Pattern", "What it looks like", "Worth catching?"], [
   ["Self-referral", "Same person, second account", "Yes -- caught at recording"],
   ["Referral ring", "A small group referring each other in a loop", "Yes -- clear and rare"],
   ["Bulk fake signups", "40 referrals in an hour, no orders", "Yes -- and obvious"],
   ["Stolen or scraped codes", "One code used from many countries at once", "Yes"],
   ["Incentivised sharing", "Posting the link on a deals forum", "Usually not fraud"],
   ["Referring family", "Same surname, same address", "Almost never fraud"],
  ]),
  ("p", "The bottom two rows are where programmes go wrong. Same-address referrals are "
        "overwhelmingly people recommending things to the people they live with, which is the "
        "most natural referral there is, and a rule that blocks them is blocking the intended "
        "behaviour of the programme."),
  ("h2", "The asymmetry"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Loose rules", "parts": [("fraud", 340), ("lost", 120)]},
      {"label": "Balanced", "parts": [("fraud", 140), ("lost", 380)]},
      {"label": "Aggressive", "parts": [("fraud", 40), ("lost", 2100)]}],
    "series": [("fraud", "Fraud paid out, £/quarter", "#DD344C"),
               ("lost", "Value of referrers who quit after a false hold", "#ED7100")],
    "unit": "£",
    "note": "The aggressive column stops almost all the fraud and costs five times as much."}),
   "The trade at three settings. The right-hand bar is the one that feels prudent in a meeting "
   "and is the most expensive option on the chart.",
   "Fraud prevented against referrers lost, at three rule strictness settings",
   "A stacked bar chart with three bars in pounds per quarter. Two series: fraud paid out in red, "
   "and the value of referrers who quit after a false hold in orange. Loose rules pay out three "
   "hundred and forty pounds of fraud and lose one hundred and twenty pounds of referrers. "
   "Balanced pays out one hundred and forty and loses three hundred and eighty. Aggressive pays "
   "out forty and loses two thousand one hundred. A note says the aggressive column stops almost "
   "all the fraud and costs five times as much."),
  ("p", "The reason the aggressive setting keeps getting chosen is that the red bar is measured "
        "and the orange one is not. Fraud paid out appears in a report; referrers who quietly "
        "stopped referring after being told their referral was under review do not appear "
        "anywhere at all."),
  ("p", "Making the orange bar visible requires only counting held referrals that were later "
        "released, and tracking whether those people ever referred again. It is a small piece of "
        "instrumentation that changes which setting people choose."),
  ("h2", "A hold is a conversation"),
  ("fig", ("chain", {
    "entry": {"title": "A signal fires", "sub": ["ring, bulk, or code"], "icon": "alarm"},
    "steps": [
      {"title": "Hold the payment", "sub": ["not the account"], "icon": "clock"},
      {"title": "Tell the referrer", "sub": ["same day, plainly"], "icon": "email"},
      {"title": "Say what triggered it", "sub": ["specifically"], "icon": "doc"},
      {"title": "A person reviews", "sub": ["within 5 working days"], "icon": "person"},
      {"title": "Release or decline", "sub": ["with a reason either way"], "icon": "check"}],
    "note": "Holding the payment is proportionate. Suspending the account is not."}),
   "What happens after a fraud signal. Every box exists to keep a legitimate referrer from "
   "experiencing this as an accusation.",
   "How a suspected fraudulent referral is held and reviewed",
   "A vertical chain of five steps entered by a box labelled A signal fires for a ring, bulk "
   "signups or a stolen code. Step one holds the payment, not the account. Step two tells the "
   "referrer the same day, plainly. Step three says specifically what triggered it. Step four has "
   "a person review it within five working days. Step five releases or declines, with a reason "
   "either way. A note says holding the payment is proportionate, and suspending the account is "
   "not."),
  ("h3", "Say what triggered it"),
  ("p", "\"Your referral is under review\" is the message that makes people angry, because it "
        "reads as an accusation with no content. \"We hold referrals when several accounts sign "
        "up from one address in a short period &mdash; this happens legitimately with families "
        "and shared houses, and a person will look at it this week\" is the same hold and a "
        "completely different experience."),
  ("p", "The second version is longer, it is a template, and writing it once removes most of the "
        "support load that fraud holds generate."),
  ("h3", "Five working days, and it means it"),
  ("p", "A review queue with no service level becomes a place referrals go to be forgotten, which "
        "is functionally identical to not paying. The deadline needs to be stated to the referrer "
        "and monitored, and a queue older than the deadline should be an alert somebody sees."),
  ("h2", "The rules that quietly kill a programme"),
  ("callout", "Four prudent-sounding rules to avoid", [
   "<strong>\"Hold anything from a shared IP address.\"</strong> That is every office, every "
   "student house, and most mobile networks.",
   "<strong>\"Hold same-surname referrals.\"</strong> Recommending something to your family is "
   "the programme working.",
   "<strong>\"Suspend the code after any signal.\"</strong> The referrer finds out when their "
   "next recommendation silently fails to register.",
   "<strong>\"Require the referred customer to confirm.\"</strong> Adds friction to the one "
   "moment the programme depends on, to prevent a rare problem.",
   "<strong>Each of these gets proposed</strong> after a single incident, and each costs more "
   "every quarter than the incident cost once.",
  ]),
  ("p", "The pattern is that fraud incidents are memorable and specific, while the cost of "
        "over-blocking is diffuse and invisible. Writing the four rules down as known bad ideas, "
        "before the incident happens, is a cheap way of having the argument in advance."),
  ("p", "Next: what happens when somebody disagrees."),
 ],
},
{
 "slug": "how-a-disputed-payout-gets-resolved",
 "title": "How a disputed payout gets resolved",
 "nav": "How disputes are resolved",
 "read": 5, "words": 720,
 "desc": ("The statement that answers most disputes before they happen, the three that remain, "
          "and why the event log settles them in minutes."),
 "og": ("Most referral disputes are questions. A statement that answers the question is cheaper "
        "than a support process that resolves the dispute."),
 "abstract": ("Why a good statement prevents most disputes, the three kinds that still arrive, "
              "how the event log resolves them, and what to do when the system was wrong."),
 "lede": ("Every referral programme generates disputes, and almost all of them are people asking "
          "a reasonable question in an annoyed tone because they could not find the answer "
          "themselves."),
 "tags": ["referral programme", "disputes", "support", "statements", "trust", "serverless"],
 "takeaways": [
  "A statement that shows pending and held items prevents most disputes entirely.",
  "Three real dispute types remain: missing referral, wrong amount, and a contested hold.",
  "The event log answers all three in minutes because nothing was overwritten.",
  "When the system was wrong, pay and say so plainly. Do not explain the mechanism.",
  "Track disputes by type; a spike in one of them is a bug report.",
 ],
 "blocks": [
  ("h2", "The statement does most of the work"),
  ("callout", "What a monthly statement shows", [
   "<strong>Paid this run:</strong> each referral, the order date, the qualify date, the amount, "
   "and which rule version it was paid under.",
   "<strong>Pending:</strong> each one, with the date it becomes payable.",
   "<strong>Held:</strong> each one, with the reason in plain words and who to reply to.",
   "<strong>Not qualifying:</strong> each one, with which condition it missed.",
   "<strong>Carried over:</strong> the balance below the minimum, and how much more is needed.",
   "<strong>Every line links</strong> to the referral's history, so \"why\" is one click and not "
   "an email.",
  ]),
  ("p", "The fourth section is the one most programmes omit and the one that prevents the most "
        "arguments. A referral that did not qualify simply vanishes in most systems, so the "
        "referrer knows only that somebody they referred bought something and they were not paid, "
        "which is exactly the shape of a grievance."),
  ("h2", "The three that still arrive"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "\"My referral is missing\"", "sub": ["they ordered, I saw it"], "icon": "question",
       "label": "most common"},
      {"title": "\"The amount is wrong\"", "sub": ["I expected 20, got 15"], "icon": "money",
       "label": "usually a rule change"},
      {"title": "\"Why is mine held?\"", "sub": ["I did nothing wrong"], "icon": "alarm",
       "label": "usually correct"}],
    "target": {"title": "The event log", "sub": ["every state change,", "with its cause"],
               "icon": "doc",
               "then": {"title": "Answered in minutes", "sub": ["with dates and reasons"],
                        "icon": "check"}},
    "note": "All three are answerable from the log because nothing in it was ever overwritten."}),
   "The three real dispute types and where they get resolved. The append-only log from Part 2 is "
   "what makes each of these a two-minute answer rather than an investigation.",
   "Three kinds of referral dispute resolved from the event log",
   "Three boxes stacked on the left. My referral is missing, they ordered and I saw it, labelled "
   "most common. The amount is wrong, I expected twenty and got fifteen, labelled usually a rule "
   "change. Why is mine held, I did nothing wrong, labelled usually correct. All three converge "
   "on The event log, which holds every state change with its cause, and that leads down to "
   "Answered in minutes, with dates and reasons. A note says all three are answerable from the "
   "log because nothing in it was ever overwritten."),
  ("h3", "The missing referral"),
  ("p", "Usually one of three things: the person ordered without clicking the link, the "
        "attribution window had expired, or somebody else's click came first. All three are "
        "visible in the log, and all three are explicable in a sentence."),
  ("p", "The first is the awkward one, because the referrer genuinely did the work and the system "
        "genuinely cannot see it. A programme that never pays those loses referrers; a programme "
        "with a small discretionary budget for exactly this case keeps them, and the budget is "
        "smaller than the alternative."),
  ("h3", "The wrong amount"),
  ("p", "Almost always a rule change, and almost always the referrer remembering the older, "
        "better terms. The stamped version resolves it immediately: this referral was made on the "
        "third under version four and was paid under version four; the one you are thinking of "
        "was made on the twentieth, under version five."),
  ("p", "Without the stamp this dispute is unresolvable, because the only available answer is "
        "\"the current rules say fifteen\", which does not address what was asked."),
  ("h2", "When the system was wrong"),
  ("fig", ("strip", {
    "stages": [
      {"title": "They were right", "sub": ["it was our bug"], "icon": "search"},
      {"title": "Pay it", "sub": ["immediately, off-cycle"], "icon": "money"},
      {"title": "Say so plainly", "sub": ["'we got this wrong'"], "icon": "email"},
      {"title": "No mechanism talk", "sub": ["they do not care"], "icon": "stop"},
      {"title": "Find the others", "sub": ["the same bug hit more"], "icon": "counter"}],
    "title": "WHEN THE ANSWER IS THAT WE WERE WRONG",
    "note": "The last box is the one people skip, and it is the one that matters most."}),
   "The correction path. The fifth box turns one apology into a fixed problem, and it is easy "
   "because the event log makes the affected set queryable.",
   "What happens when a referral dispute reveals a system error",
   "A horizontal row of five boxes. They were right: it was our bug. Pay it: immediately and "
   "off-cycle. Say so plainly: we got this wrong. No mechanism talk: they do not care. Find the "
   "others: the same bug hit more people. A note says the last box is the one people skip, and it "
   "is the one that matters most."),
  ("p", "The fourth box deserves a note. The instinct when a system was wrong is to explain the "
        "mechanism, partly to demonstrate that it was a reasonable failure. The person waiting to "
        "be paid does not want the mechanism; a short acknowledgement, the money, and a note that "
        "it is fixed lands considerably better."),
  ("h3", "Disputes as a signal"),
  ("p", "Categorise every dispute by type and count them monthly. A stable low rate is normal. A "
        "spike in \"missing referral\" is a tracking bug; a spike in \"why is mine held\" means a "
        "fraud rule was tightened and nobody weighed the orange bar; a spike in \"wrong amount\" "
        "means a rule change went out without being explained."),
  ("p", "Each of those is a specific, actionable finding that arrives free with a support process "
        "that was happening anyway, and none of them are visible if disputes are handled "
        "individually and not counted."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="referral",
 volumes=[(200, "200 referrals"), (800, "800 referrals"), (3000, "3,000 referrals")],
 read_each=0.0,
 msgs_each=0.4,
 lede=("There is no model in this system and the messaging is one statement per active referrer "
       "per month plus hold notices. Eight hundred referrals a month is a programme that is "
       "genuinely working. Here is where each cent goes."),
 takeaway_extra=("Statements, not referrals, drive the messaging line, and there are far fewer "
                 "referrers than referrals."),
 risks=[
  "<strong>Storing state instead of events and then rebuilding history.</strong> Not a running "
  "cost so much as an unbounded one-off when somebody has to reconstruct six months of decisions.",
  "<strong>Running the qualifier continuously.</strong> Referrals become payable on a date. A "
  "daily sweep is sufficient and a per-minute one is not more correct.",
  "<strong>Per-referral payment transfers.</strong> The transfer fee usually exceeds the "
  "arithmetic cost of the entire system. Batch into one transfer per person per run.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. The messaging band covers "
                "monthly statements and hold notices, not one message per referral."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="rp",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the event model, and the rule versioning."),
 outside=[
  {"title": "Referral links", "sub": ["clicks and signups"], "icon": "route"},
  {"title": "Orders and refunds", "sub": ["read only"], "icon": "database"},
  {"title": "Payments and email", "sub": ["transfers, statements"], "icon": "money"}],
 inside=[
  {"title": "Function URL + EventBridge", "sub": ["click intake,", "daily qualify"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["record, qualify, run"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["events, rules"], "icon": "database"}],
 note="us-east-1. One account. Events are append-only; rule versions are immutable once published.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Referral links, producing clicks and "
  "signups. Orders and refunds, read only. And Payments and email, covering transfers and "
  "statements. Inside the account, three groups. A Function URL for click intake and EventBridge "
  "running a daily qualify pass. Three Lambda functions named record, qualify and run. And two "
  "DynamoDB tables named events and rules. A note gives the region as us-east-1, one account, and "
  "states that events are append-only and rule versions are immutable once published."),
 functions=[
  ["<code>rp-record</code>", "Function URL",
   "Creates a referral, stamps the rule version, checks self-referral", "5s / 512&nbsp;MB"],
  ["<code>rp-qualify</code>", "EventBridge, daily",
   "Links orders, closes refund windows, applies holds, marks payable", "300s / 1024&nbsp;MB"],
  ["<code>rp-run</code>", "EventBridge, monthly",
   "Batches payable amounts per person, initiates transfers, sends statements",
   "300s / 1024&nbsp;MB"]],
 roles=[
  ["<code>rp-record-role</code>", "<code>dynamodb:PutItem</code>, <code>dynamodb:GetItem</code>",
   "Events; read-only on rules"],
  ["<code>rp-qualify-role</code>", "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "Events; read-only on the order table"],
  ["<code>rp-run-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>, <code>ses:SendEmail</code>, "
   "<code>secretsmanager:GetSecretValue</code>",
   "Events; one verified identity; the payment provider credential"]],
 tables=[
  ("Table: events",
   "PK   referral_id       S\n"
   "SK   seq               N   1, 2, 3 -- never reused, never edited\n"
   "     type              S   created | order_linked | held | released\n"
   "                           | qualified | paid | clawed_back | declined\n"
   "     at                S   2026-08-03T11:02:00Z\n"
   "     actor             S   system | a named person\n"
   "     reason            S   free text; required on held and declined\n"
   "     amount_pence      N   on qualified, paid and clawed_back\n"
   "     rules_version     S   on created only; read by everything after\n\n"
   "GSI1: referrer_id + at  -- builds one person's statement in one query.\n"
   "There is no status attribute anywhere. State is folded from the events."),
  ("Table: rules",
   "PK   version           S   v4\n"
   "     published_at      S   2026-07-12\n"
   "     amount_pence      N   2000\n"
   "     min_order_pence   N   5000\n"
   "     window_days       N   60\n"
   "     refund_days       N   14\n"
   "     excluded_skus     L\n"
   "     superseded_at     S   set when v5 publishes; the row never changes otherwise\n\n"
   "Writes are create-only. There is no update path to this table in any\n"
   "role, which is what makes 'paid under v4' a fact rather than a claim.")],
 inbound=[
  "<strong>Clicks arrive at a Function URL</strong> which sets a first-party cookie and writes "
  "the created event with the current rule version.",
  "<strong>Orders are read, never written.</strong> The qualifier matches orders to live "
  "referrals; it has no write access to the order table.",
  "<strong>Refunds and chargebacks</strong> arrive on the same daily pass and produce "
  "<code>clawed_back</code> or <code>declined</code> events rather than deletions.",
  "<strong>A hold requires a reason string.</strong> The write is rejected without one, which is "
  "how the referrer-facing message is guaranteed to have content."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Qualification is dates and thresholds; the "
  "fraud signals are counting rules over a window.",
  "<strong>The tempting use</strong> is scoring referrals for fraud risk. At these volumes it "
  "produces an unexplainable hold, and Part 5 is entirely about why every hold needs a reason a "
  "person can read.",
  "<strong>A second tempting use</strong> is drafting the hold notice. The four templates are "
  "better, because the wording of an accusation is not somewhere to introduce variation.",
  "<strong>Classifying inbound disputes</strong> by type is defensible and useful, and the count "
  "by type is the signal described in Part 5.",
  "<strong>The cost page assumes none</strong>, which is why messaging is the only variable "
  "band."],
 gotchas=[
  "Give the rules table no update path in any IAM role. A rule version that can be edited after "
  "publication is not a stamp, it is a suggestion.",
  "Fold state from events; never store a status attribute. The moment one exists, something "
  "writes to it and the log stops being the truth.",
  "Require a reason on every hold and decline at the write layer. A reason field that is optional "
  "is empty exactly when it matters.",
  "Batch transfers per person per run. Per-referral transfers cost more in fees than the entire "
  "rest of the system.",
  "Send the statement even when the payment is zero. That statement prevents more support load "
  "than any other single thing here."],
))
