"""Day 91 -- 2026-07-24 -- Tip pool splitter."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "tip-pool-splitter"
NAME = "Tip pool splitter"

SPEC = {
 "slug": SLUG, "date": "2026-07-24", "name": NAME,
 "tagline": ("The pool is split by the rule everybody agreed, published the same week, with the "
             "arithmetic visible -- so nobody has to trust anybody about their own money."),
 "lede": ("A small system that collects what came into the tip pool, applies the split rule the "
          "team agreed, and publishes each person's share with the working shown. It never "
          "decides the rule, never moves money, and never rounds in the business's favour. "
          "Seven posts on the same system -- one diagram at a time -- with a cost breakdown and "
          "an engineering reference at the end."),
 "keywords": ["tips", "tronc", "hospitality", "payroll", "fairness", "serverless"],
 "icons": ["money", "counter", "team"],
 "faq": [
  ("What is a tip pool splitter?",
   "A small serverless system that takes what went into the tip pool for a period, applies the "
   "split rule the team agreed, and publishes each person's share with the arithmetic visible. "
   "It does not choose the rule and it does not pay anybody."),
  ("Does it decide how tips are shared?",
   "No. The rule is a decision for the people it affects, and in many places it has legal "
   "requirements attached. The system takes a rule that already exists, applies it identically "
   "every period, and shows its working."),
  ("Why publish the arithmetic?",
   "Because tips are the one part of pay that people genuinely do not trust, and the reason is "
   "almost never dishonesty -- it is that nobody can see the calculation. Showing hours, "
   "weights and the pool total removes the doubt at essentially no cost."),
  ("How are rounding differences handled?",
   "Rounding to the penny always leaves a remainder. It is distributed rather than kept, in a "
   "rotating order recorded in the period, so it never quietly accumulates anywhere."),
  ("What does it cost to run?",
   "A couple of dollars a month. It runs weekly over a few dozen rows. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "tip-pool-splitter-on-aws",
 "title": "A tip pool splitter on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 870,
 "desc": ("Collects the pool, applies the agreed split rule, and publishes each share with the "
          "working shown. AWS, about $2 a month."),
 "og": ("Tips are the part of pay people trust least, and the reason is that nobody can see the "
        "arithmetic. This publishes it."),
 "abstract": ("The whole system on one page -- a collector, a splitter and a publisher -- with "
              "the rule held outside it, because the rule is a decision the system has no "
              "business making."),
 "lede": ("Tips are the only part of somebody's pay they cannot check. The card machine total is "
          "not visible, the cash is counted by somebody else, the split is done in a back office "
          "on a Sunday, and what arrives is a number. Almost nobody is being cheated and almost "
          "everybody wonders. This post walks through a small system whose entire purpose is to "
          "make the arithmetic visible."),
 "tags": ["tips", "tronc", "hospitality", "payroll", "fairness", "serverless"],
 "takeaways": [
  "The rule lives outside the system. It is a decision for the people it affects.",
  "Three inputs: card tips, cash tips, and the hours worked in the period.",
  "Every share is published with its working: hours, weight, pool total, and the division.",
  "The rounding remainder is distributed in a rotating order, never retained.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "The pool", "sub": ["card and cash"], "icon": "money"},
      {"title": "The agreed rule", "sub": ["weights and hours"], "icon": "doc"},
      {"title": "Everyone", "sub": ["sees the working"], "icon": "team"}],
    "inside": [
      {"title": "Collector", "sub": ["what came in,", "and what hours"], "icon": "counter"},
      {"title": "Splitter", "sub": ["the rule, applied", "identically"], "icon": "filter"},
      {"title": "Publisher", "sub": ["shares plus", "the arithmetic"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "totals"},
              {"from": 1, "to": 1, "label": "how to divide it"},
              {"from": 2, "to": 2, "label": "shares, with working", "up": True}],
    "note": "The rule is not in here. Choosing it is a decision for the people it affects."}),
   "Three things outside the account, three pieces inside it. The rule being outside is not an "
   "implementation convenience &mdash; it is the point.",
   "System: a tip pool and a rule in, published shares out",
   "Three boxes across the top sit outside the AWS account. On the left, The pool: card and cash "
   "tips. In the middle, The agreed rule: the weights and the hours basis the team agreed. On "
   "the right, Everyone: the people who see the working. Each connects by an arrow to the AWS "
   "account container below. Totals flow down into the account. The rule feeds in how to divide "
   "it. Shares, with working, go back out. Inside the AWS account are three components in a row. "
   "On the left, the Collector, which records what came in and what hours were worked. In the "
   "middle, the Splitter, which applies the rule identically every period. On the right, the "
   "Publisher, which shows each share alongside its arithmetic. A note at the bottom says the "
   "rule is not in here, because choosing it is a decision for the people it affects."),
  ("h3", "The rule stays outside"),
  ("p", "It would be easy, and wrong, to build the rule into the system. Tip sharing is subject "
        "to law in many places, it is frequently the subject of a written policy, and it is "
        "always the subject of strong feelings. A system that encodes a rule invites the "
        "question \"who decided that?\", and the answer must never be \"the software\"."),
  ("p", "So the rule is a sheet: which roles are in the pool, what weight each carries, whether "
        "the basis is hours worked or shifts worked, and what happens to the rounding remainder. "
        "Changing it is a conversation and then an edit, in that order."),
  ("h3", "What runs each period (the inside)"),
  ("ul", [
   "<strong>The collector.</strong> Takes the card tips from the till or card report, the cash "
   "tips from a declared figure, and the hours from the rota or the timesheets. Three numbers "
   "per period plus a row per person. Part 2 covers where each comes from and which of them is "
   "genuinely hard.",
   "<strong>The splitter.</strong> Applies the rule. Multiply each person's hours by their "
   "role's weight, sum the weighted hours, divide the pool by the sum to get a rate, multiply "
   "back. It is four lines of arithmetic and the only interesting part is what happens to the "
   "pennies.",
   "<strong>The publisher.</strong> Shows each person their share and the arithmetic that "
   "produced it, plus the pool total and the total weighted hours, so the numbers can be checked "
   "against each other. That transparency is the entire product.",
  ]),
  ("h2", "One period, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Collected", "sub": ["card, cash, hours"], "icon": "money"},
      {"title": "Weighted", "sub": ["hours x role weight"], "icon": "counter"},
      {"title": "Rate", "sub": ["pool / weighted hours"], "icon": "filter"},
      {"title": "Shares", "sub": ["rate x each person"], "icon": "team"},
      {"title": "Published", "sub": ["with the working"], "icon": "report"}],
    "title": "ONE PERIOD, END TO END",
    "note": "Four multiplications and one division. The value is entirely in the last box."}),
   "The same system as one line. The arithmetic is trivial and doing it visibly, identically, "
   "every week is what changes anything.",
   "One tip pool period from collection to publication, in five stages",
   "A horizontal row of five boxes joined by arrows. Collected: card tips, cash tips and hours. "
   "Weighted: each person's hours multiplied by their role weight. Rate: the pool divided by the "
   "total weighted hours. Shares: the rate multiplied by each person's weighted hours. "
   "Published: with the working shown. A note says four multiplications and one division, and "
   "the value is entirely in the last box."),
  ("h2", "In plain words"),
  ("p", "A week ends. Card tips came to £642.30 and declared cash tips to £188.00, so the pool "
        "is £830.30. Eleven people worked, and the agreed rule weights front of house at 1.0, "
        "kitchen at 0.8 and supervisors at 1.2. Total weighted hours come to 318.4. That gives a "
        "rate of £2.6077 per weighted hour."),
  ("p", "Everybody gets a message on Monday: your share is £71.16, from 27.3 hours at weight "
        "1.0, at £2.6077 a weighted hour. The pool was £830.30 across 318.4 weighted hours. Two "
        "pence of rounding remainder went to the next two people in the rotation, and here is "
        "who. Nobody has to trust anybody, because every number in that message can be checked "
        "against every other one, and eleven people checking the same arithmetic is a much "
        "stronger control than one person doing it carefully."),
  ("callout", "Design rules that shaped every decision", [
   "The rule is not the system's. It lives in a sheet, it is somebody's decision, and the system "
   "applies it identically.",
   "Publish the working, always. A share without its arithmetic is a number you are asked to "
   "trust.",
   "Never round in the house's favour. The remainder is distributed, in a recorded rotation.",
   "The same rule for the whole period. A rule change takes effect next period, never "
   "retroactively.",
   "Cash is declared, not inferred. The system records what somebody said went in, and who said "
   "it.",
   "It never moves money. It produces a figure that payroll pays.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Almost every tip dispute is an information problem rather than an honesty problem. "
        "People cannot see the pool total, cannot see other people's hours, and cannot see the "
        "rule being applied, so a share that is lower than last week has no explanation and the "
        "mind supplies one."),
  ("p", "Publishing the arithmetic costs nothing and removes the whole category. It also has a "
        "second effect that is worth more than the first: when eleven people can see the pool "
        "total and the weighted hours, arithmetic errors get found within a day, by the people "
        "with the strongest incentive to find them."),
  ("p", "The next four posts walk through each piece: how the pool and hours are collected, how "
        "the split is computed, what happens to the rounding, and what publishing actually "
        "looks like. One diagram per post, a cost breakdown, and an engineering reference at the "
        "end."),
 ],
},
{
 "slug": "how-the-pool-and-hours-are-collected",
 "title": "How the pool and hours are collected",
 "nav": "How it is collected",
 "read": 5, "words": 760,
 "desc": ("Card tips from a report, cash tips from a declaration, hours from the rota -- and "
          "which of those three is genuinely hard."),
 "og": ("Card tips are a number in a report. Cash tips are a declaration by a person. Those two "
        "have completely different assurance levels and the system says which is which."),
 "abstract": ("Where each of the three inputs comes from, why cash is a declaration rather than "
              "a measurement, and why hours should come from the same source that pays people."),
 "lede": ("Two of the three inputs are easy and one is not, and pretending otherwise is how tip "
          "systems lose credibility. Card tips are a figure in a report. Hours are in the "
          "timesheet. Cash is somebody telling you a number, and the system should say so."),
 "tags": ["tips", "hospitality", "data collection", "payroll", "declarations", "serverless"],
 "takeaways": [
  "Card tips come from the card or till report, and are reconciled to the banking.",
  "Cash tips are a declaration: a number, a person, and a timestamp.",
  "Hours come from whatever pays people, so the two can never disagree.",
  "A period cannot be split until all three inputs are present.",
  "A late correction reopens the period rather than adjusting the next one.",
 ],
 "blocks": [
  ("h2", "Three inputs, three assurance levels"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Card tips", "sub": ["till or card report"], "icon": "money", "label": "measured"},
      {"title": "Cash tips", "sub": ["declared at close"], "icon": "person", "label": "declared"},
      {"title": "Hours", "sub": ["from payroll's source"], "icon": "clock", "label": "measured"}],
    "target": {"title": "A complete period", "sub": ["all three present,", "or no split"],
               "icon": "check",
               "then": {"title": "Splitter", "sub": ["the agreed rule"], "icon": "filter"}},
    "note": "The middle lane is a person's statement, and the record says whose."}),
   "The three inputs and where each comes from. The declared lane is labelled differently on "
   "purpose: it is the only one nobody can independently verify.",
   "Three tip pool inputs converging on a complete period",
   "Three boxes stacked on the left. Card tips, from the till or card report, labelled measured. "
   "Cash tips, declared at close, labelled declared. And Hours, from whatever source pays "
   "people, labelled measured. All three converge on A complete period, which requires all three "
   "present or there is no split. Below it, connected by a downward arrow, is the Splitter, "
   "applying the agreed rule. A note says the middle lane is a person's statement and the record "
   "says whose."),
  ("h3", "Card tips"),
  ("p", "A figure from the card processor or the till, for the period, and it should be "
        "reconciled to what actually reached the bank. That reconciliation is the one control "
        "worth having on this input, because a card tip figure that does not match the banking "
        "usually means a refund or a chargeback that reduced the pool after the fact."),
  ("p", "Service charge, where it exists, is separate from card tips and frequently has different "
        "rules attached. It is a separate input with its own line in the rule sheet, and "
        "conflating the two is the most common cause of a genuine dispute rather than a "
        "misunderstanding."),
  ("h3", "Cash tips are a declaration"),
  ("p", "Somebody counts what is in the jar and says a number. There is no way to verify it and "
        "the system should not pretend there is. So the record is explicit: the amount, who "
        "declared it, and when."),
  ("p", "Making the declarer visible is the whole control, and it is a mild one deliberately. "
        "The alternative &mdash; a cash count with a witness and a signature every night &mdash; "
        "is proportionate in some businesses and heavy-handed in most. Recording who said what, "
        "and publishing it with the split, is usually enough."),
  ("h3", "Hours come from payroll's source"),
  ("p", "Whatever pays people is what the split uses. If hours come from the rota and pay comes "
        "from timesheets, the two will differ &mdash; somebody stayed late, somebody left early "
        "&mdash; and a tip share computed on rostered hours when pay is computed on actual hours "
        "produces a discrepancy that nobody can explain."),
  ("h2", "Completeness"),
  ("fig", ("chain", {
    "entry": {"title": "Period ends", "sub": ["a date, from the sheet"], "icon": "calendar"},
    "steps": [
      {"title": "Card figure in?", "icon": "branch",
       "exit": {"title": "Wait, and chase", "sub": ["at 24 hours"], "icon": "clock", "label": "no"}},
      {"title": "Cash declared?", "icon": "branch",
       "exit": {"title": "Ask whoever closed", "sub": ["by name"], "icon": "person", "label": "no"}},
      {"title": "Hours final?", "sub": ["not a draft timesheet"], "icon": "branch",
       "exit": {"title": "Wait for payroll", "sub": ["never split a draft"], "icon": "stop",
                "label": "no"}},
      {"title": "Split and publish", "sub": ["same day"], "icon": "report"}],
    "note": "Splitting a draft timesheet produces a share that changes, which is worse than a delay."}),
   "Why a period waits for all three inputs. A published share that later changes does more "
   "damage than a share published two days late.",
   "How a period is checked for completeness before splitting",
   "A vertical chain of four steps entered by a box labelled Period ends, on a date from the "
   "sheet. Step one asks whether the card figure is in; if not it exits to Wait and chase at "
   "twenty-four hours. Step two asks whether cash has been declared; if not it exits to Ask "
   "whoever closed, by name. Step three asks whether the hours are final rather than a draft "
   "timesheet; if not it exits to Wait for payroll, because a draft is never split. Step four "
   "splits and publishes the same day. A note says splitting a draft timesheet produces a share "
   "that changes, which is worse than a delay."),
  ("h3", "Late corrections"),
  ("p", "A card refund lands after the split. A timesheet is corrected. Somebody remembers a "
        "cash tip that was not declared. All three happen, and the wrong response is to adjust "
        "the next period, because that produces a week where everybody's share is slightly off "
        "for a reason buried in a previous week."),
  ("p", "The right response is to reopen the period, recompute, and publish a correction that "
        "says what changed and why. It is more work to explain and much easier to check, and "
        "since the whole system exists to be checkable, that is the trade to make."),
  ("p", "Next: the arithmetic itself, and the rule sheet that drives it."),
 ],
},
{
 "slug": "how-the-split-is-computed",
 "title": "How the split is computed",
 "nav": "How it is computed",
 "read": 5, "words": 750,
 "desc": ("Weighted hours, the rate, and the four shapes of rule a small business actually uses "
          "-- plus the ones that produce arguments."),
 "og": ("Weighted hours and a single rate covers almost every real rule. The shapes that "
        "produce arguments are the ones with a threshold or a discretionary element in them."),
 "abstract": ("The weighted-hours arithmetic, the four rule shapes small businesses actually "
              "use, and the two shapes that reliably produce arguments."),
 "lede": ("The arithmetic is four lines and the rule shapes are where the interest is. Most "
          "small businesses use one of four, and two of the four generate almost all of the "
          "disputes &mdash; not because they are unfair, but because they are hard to check."),
 "tags": ["tips", "tronc", "fairness", "payroll", "arithmetic", "serverless"],
 "takeaways": [
  "Weighted hours and one rate covers most real rules in four lines of arithmetic.",
  "Four shapes: equal, hours-only, role-weighted, and points per shift.",
  "Two shapes cause arguments: anything with a threshold, and anything discretionary.",
  "A rule change takes effect next period and never retroactively.",
  "Every published share shows the rate, so any two people can check each other's.",
 ],
 "blocks": [
  ("h2", "The arithmetic"),
  ("pre", "for each person:\n"
          "    weighted[p] = hours[p] * weight[role[p]]\n"
          "\n"
          "total_weighted = sum(weighted)\n"
          "rate           = pool / total_weighted\n"
          "\n"
          "for each person:\n"
          "    share[p] = round(rate * weighted[p], 2)\n"
          "\n"
          "remainder = pool - sum(share)          # always a few pence\n"
          "distribute(remainder)                  # Part 4"),
  ("p", "That is the whole computation. Publishing <code>rate</code> alongside every share is "
        "what makes it checkable: any two people can multiply their own weighted hours by the "
        "same published rate and confirm they got the same answer from the same number."),
  ("h2", "Four rule shapes"),
  ("fig", ("chain", {
    "entry": {"title": "The pool", "sub": ["for one period"], "icon": "money"},
    "steps": [
      {"title": "Equal shares", "sub": ["everybody who worked"], "icon": "team",
       "exit": {"title": "Simple, and rare", "sub": ["ignores hours entirely"], "icon": "counter",
                "label": "shape 1"}},
      {"title": "Hours only", "sub": ["no role weights"], "icon": "clock",
       "exit": {"title": "Common, easy to check", "sub": ["weight = 1 for all"], "icon": "check",
                "label": "shape 2"}},
      {"title": "Role weighted", "sub": ["front, kitchen, supervisor"], "icon": "filter",
       "exit": {"title": "Most common", "sub": ["and still checkable"], "icon": "chart",
                "label": "shape 3"}},
      {"title": "Points per shift", "sub": ["not hours at all"], "icon": "calendar",
       "exit": {"title": "Works for fixed shifts", "sub": ["awkward for split hours"],
                "icon": "branch", "label": "shape 4"}},
      {"title": "Everything else", "sub": ["thresholds, discretion"], "icon": "alarm"}],
    "note": "The last box is where disputes come from, and it is a rule problem not a software one."}),
   "The four rule shapes and the residual category. All four of the named shapes are one "
   "multiplication and one division; the last one is not, and that is why it causes trouble.",
   "Four tip-split rule shapes and the residual category",
   "A vertical chain of five steps entered by a box labelled The pool, for one period. Step one "
   "is Equal shares for everybody who worked, described as simple and rare because it ignores "
   "hours entirely. Step two is Hours only with no role weights, common and easy to check, with "
   "every weight set to one. Step three is Role weighted across front of house, kitchen and "
   "supervisors, the most common and still checkable. Step four is Points per shift rather than "
   "hours, which works for fixed shifts and is awkward for split hours. Step five is Everything "
   "else, meaning thresholds and discretion. A note says the last box is where disputes come "
   "from and it is a rule problem rather than a software one."),
  ("h3", "Why thresholds cause arguments"),
  ("p", "A rule like \"anybody who worked more than sixteen hours this week gets a full share, "
        "otherwise a half share\" is easy to state and produces a cliff. Somebody on fifteen and "
        "a half hours gets half of what somebody on sixteen and a quarter gets, for half an hour "
        "of difference, and that is genuinely hard to accept even when everybody agreed the rule."),
  ("p", "The system will apply it faithfully and the publication will make the cliff extremely "
        "visible, which is either a feature or the beginning of a conversation about changing "
        "the rule. Both are better than the cliff being invisible."),
  ("h3", "Why discretion cannot be automated"),
  ("p", "\"The supervisor allocates a portion at their discretion\" is a legitimate rule in some "
        "places and it cannot be computed. The honest handling is to treat the discretionary "
        "portion as a separate, smaller pool with its own explicit allocation recorded per "
        "person, published alongside the computed split rather than mixed into it."),
  ("p", "Mixing them produces a share that cannot be checked, which defeats the purpose of the "
        "whole system. Keeping them separate means eleven people can verify the computed portion "
        "and see plainly that the other portion was somebody's judgement."),
  ("h2", "Rule changes"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Rule edited", "sub": ["in the sheet"], "icon": "doc"},
      {"title": "Effective from", "sub": ["a date, always future"], "icon": "calendar"},
      {"title": "This period", "sub": ["old rule, unchanged"], "icon": "lock"},
      {"title": "Next period", "sub": ["new rule"], "icon": "retry"},
      {"title": "Both recorded", "sub": ["on their own periods"], "icon": "log"}],
    "title": "A RULE CHANGE NEVER APPLIES BACKWARDS",
    "note": "Recomputing a published period under a new rule changes somebody's money after the fact."}),
   "How a rule change takes effect. Applying a new rule to a period that has already been "
   "published would change money people have already been told about.",
   "How a tip split rule change takes effect",
   "A horizontal row of five boxes. Rule edited: in the sheet. Effective from: a date that is "
   "always in the future. This period: the old rule, unchanged. Next period: the new rule. Both "
   "recorded: each on its own period. A note says recomputing a published period under a new "
   "rule changes somebody's money after the fact."),
  ("p", "Each period stores the rule it was computed under, which is the same discipline as the "
        "clause versions in the offer letter generator and the stamped rate in the mileage "
        "checker. It costs one field and it means a period from March can still be explained "
        "under March's rule."),
  ("p", "Next: the pennies."),
 ],
},
{
 "slug": "how-the-rounding-remainder-is-handled",
 "title": "How the rounding remainder is handled",
 "nav": "How rounding works",
 "read": 5, "words": 730,
 "desc": ("A few pence that have to go somewhere, why they must not go to the house, and the "
          "rotation that makes it demonstrably fair over time."),
 "og": ("A few pence a week is nothing and where they go is everything. The remainder is "
        "distributed in a recorded rotation, never retained."),
 "abstract": ("The few pence that rounding always leaves, why they must never go to the "
              "business, and the recorded rotation that makes their distribution demonstrably "
              "fair over a year."),
 "lede": ("This post is about two pence, and it matters out of all proportion to its value. Where "
          "the rounding remainder goes is the single clearest signal a business sends about "
          "whose money the tip pool is, and it costs about four pounds a year to get right."),
 "tags": ["tips", "rounding", "fairness", "payroll", "audit trail", "serverless"],
 "takeaways": [
  "Rounding to the penny always leaves a remainder. It has to go somewhere explicitly.",
  "It never goes to the business. Not once, not as a convention, not as a rounding policy.",
  "It is distributed a penny at a time, in a rotation recorded on the period.",
  "The rotation position carries forward, so over a year it is demonstrably even.",
  "The remainder and its recipients are published, because that is what makes it credible.",
 ],
 "blocks": [
  ("h2", "Where the pennies come from"),
  ("p", "A pool of £830.30 divided across 318.4 weighted hours gives a rate with more decimal "
        "places than money has. Multiply that back for eleven people, round each to the penny, "
        "and the shares will sum to something a few pence away from the pool. That difference "
        "is unavoidable, it is usually between one and ten pence, and it has to go somewhere."),
  ("fig", ("chain", {
    "entry": {"title": "Shares, rounded", "sub": ["sum != pool"], "icon": "counter"},
    "steps": [
      {"title": "Compute the remainder", "sub": ["pool minus the sum"], "icon": "filter"},
      {"title": "Who is next?", "sub": ["from the rotation"], "icon": "branch",
       "side": {"title": "Rotation position", "sub": ["carried between periods"], "icon": "retry"}},
      {"title": "One penny each", "sub": ["round the rotation"], "icon": "money"},
      {"title": "Advance the position", "sub": ["for next period"], "icon": "log"},
      {"title": "Publish who got them", "sub": ["by name, every time"], "icon": "report"}],
    "note": "Publishing the recipients is what stops this being something people wonder about."}),
   "How a few pence are distributed. Carrying the rotation position between periods is what "
   "makes the distribution even over a year rather than always favouring whoever is first "
   "alphabetically.",
   "How the rounding remainder is distributed",
   "A vertical chain of five steps entered by a box labelled Shares, rounded, whose sum does not "
   "equal the pool. Step one computes the remainder as the pool minus the sum of the shares. "
   "Step two asks who is next, taken from a rotation position carried between periods. Step "
   "three gives one penny each around the rotation. Step four advances the position for the next "
   "period. Step five publishes who got them, by name, every time. A note says publishing the "
   "recipients is what stops this being something people wonder about."),
  ("h3", "Why not to the business"),
  ("p", "The remainder is trivially small and retaining it is a policy choice about whose money "
        "the pool is. A business that rounds in its own favour every week has, over a year, kept "
        "about four pounds and told its staff something quite specific about the relationship."),
  ("p", "In several jurisdictions it is also not permitted, and in most of the rest it would be "
        "difficult to defend if anybody asked. The point is not the legal exposure &mdash; four "
        "pounds is not a legal exposure &mdash; it is that the alternative costs nothing and "
        "says the opposite thing."),
  ("h3", "Why not to the largest share"),
  ("p", "\"Give the remainder to whoever worked the most hours\" is tempting because it is one "
        "line of code and needs no state. It also gives the same person a few extra pence every "
        "week forever, which over a year is small and over a year is also visible, and the first "
        "person to notice will describe it as the system favouring the manager."),
  ("h2", "The rotation"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Week 1", "sub": ["2p: Ash, Rae"], "icon": "team"},
      {"title": "Week 2", "sub": ["3p: Sam, Kit, Jo"], "icon": "team"},
      {"title": "Week 3", "sub": ["1p: Lee"], "icon": "team"},
      {"title": "Week 4", "sub": ["2p: Ash, Rae"], "icon": "retry"},
      {"title": "Over a year", "sub": ["within a penny of even"], "icon": "check"}],
    "title": "THE ROTATION, OVER FOUR WEEKS",
    "note": "The position carries forward, so nobody is systematically first or last."}),
   "The rotation across four weeks. Carrying the position rather than restarting each period is "
   "what prevents a fixed order from advantaging the same people every time.",
   "How the rounding rotation distributes pennies over four weeks",
   "A horizontal row of five boxes. Week one: two pence, to Ash and Rae. Week two: three pence, "
   "to Sam, Kit and Jo. Week three: one penny, to Lee. Week four: two pence, back to Ash and "
   "Rae. Over a year: within a penny of even. A note says the position carries forward, so "
   "nobody is systematically first or last."),
  ("p", "The rotation order itself can be anything stable &mdash; alphabetical, by employee "
        "number, by start date &mdash; as long as it does not change between periods and the "
        "position carries forward. Restarting the rotation each period is the bug that makes "
        "this whole mechanism pointless, because whoever is first in the order gets a penny every "
        "single week."),
  ("h3", "Publishing it"),
  ("p", "The remainder line appears on every published split: \"3p of rounding went to Sam, Kit "
        "and Jo. Next period starts at Lee.\" It is one sentence, nobody will ever read it "
        "twice, and its presence is the reason nobody wonders."),
  ("p", "Next: what publishing actually looks like."),
 ],
},
{
 "slug": "how-a-split-gets-published",
 "title": "How a split gets published",
 "nav": "How it is published",
 "read": 5, "words": 740,
 "desc": ("What each person sees, what everybody sees, and the line between the two -- plus the "
          "correction that has to be as visible as the original."),
 "og": ("Your share with its arithmetic, plus the pool total and rate everybody can see. Other "
        "people's individual shares are not published, and the totals still make it checkable."),
 "abstract": ("What each person sees, what the whole team sees, why individual shares are not "
              "published, and why a correction has to be at least as visible as the original."),
 "lede": ("There is a line to draw between transparency and publishing everybody's pay, and it "
          "turns out to be drawable: the totals and the rate are enough to check the arithmetic "
          "without anybody's individual share being public."),
 "tags": ["tips", "transparency", "reporting", "payroll", "hospitality", "serverless"],
 "takeaways": [
  "Each person sees their own share and its full arithmetic.",
  "Everybody sees the pool, the total weighted hours, the rate and the remainder.",
  "Individual shares are not published, and the totals still make the split checkable.",
  "A correction is published as loudly as the original, with what changed.",
  "The period archive keeps the rule it was computed under.",
 ],
 "blocks": [
  ("h2", "Two audiences"),
  ("fig", ("system", {
    "outside": [
      {"title": "Each person", "sub": ["their own share"], "icon": "person"},
      {"title": "Everybody", "sub": ["the totals and rate"], "icon": "team"},
      {"title": "Payroll", "sub": ["a figure to pay"], "icon": "money"}],
    "inside": [
      {"title": "Personal view", "sub": ["hours, weight,", "rate, share"], "icon": "doc"},
      {"title": "Period summary", "sub": ["pool, weighted hours,", "rate, remainder"], "icon": "chart"},
      {"title": "Export", "sub": ["one line per person"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "their arithmetic", "up": True},
              {"from": 1, "to": 1, "label": "the shared numbers", "up": True},
              {"from": 2, "to": 2, "label": "the payable figures", "up": True}],
    "note": "The shared numbers make the split checkable without publishing anybody's share."}),
   "Who sees what. The middle box is the interesting one: publishing four aggregate numbers "
   "makes the whole calculation verifiable without exposing any individual's earnings.",
   "How a tip split is published to three audiences",
   "Three boxes across the top outside the AWS account. Each person, who sees their own share. "
   "Everybody, who sees the totals and the rate. And Payroll, which receives a figure to pay. "
   "Inside the account, three components. The Personal view, showing hours, weight, rate and "
   "share. The Period summary, showing the pool, the total weighted hours, the rate and the "
   "remainder. And the Export, one line per person. Arrows show each person receiving their own "
   "arithmetic, everybody receiving the shared numbers, and payroll receiving the payable "
   "figures. A note says the shared numbers make the split checkable without publishing "
   "anybody's share."),
  ("h3", "What one person sees"),
  ("callout", "Your share, week ending 26 July", [
   "<strong>£71.16</strong>",
   "27.3 hours &times; weight 1.0 = <strong>27.3 weighted hours</strong>",
   "Rate this week: <strong>£2.6077</strong> per weighted hour",
   "27.3 &times; £2.6077 = £71.19, rounded to £71.16 after the rounding step",
   "Pool: £830.30 (card £642.30, cash £188.00 declared by Ash at close on the 26th)",
   "Total weighted hours across everybody: 318.4",
   "Rounding: 2p went to Sam and Kit. Next period starts at Jo.",
  ]),
  ("p", "Seven lines, and every number in them can be checked against the others. The rate times "
        "the personal weighted hours gives the share. The pool divided by the total weighted "
        "hours gives the rate. Two people comparing notes get the same rate, which is the "
        "strongest possible confirmation that the same rule was applied to both of them."),
  ("h3", "Why individual shares are not published"),
  ("p", "Publishing everybody's share publishes everybody's hours, because the rate is public "
        "and the arithmetic is trivial to reverse. Hours are close enough to pay that many "
        "people would reasonably object, and in some contracts it is explicitly confidential."),
  ("p", "The totals achieve the goal without that. Anybody can verify that the rate is correct, "
        "that the pool is what was declared, and that their own share follows. What they cannot "
        "do is work out what a colleague earned, which is a line most people are content with."),
  ("h2", "Corrections"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Published", "sub": ["Monday"], "icon": "report"},
      {"title": "Card refund lands", "sub": ["Wednesday"], "icon": "alarm"},
      {"title": "Period reopened", "sub": ["and recomputed"], "icon": "retry"},
      {"title": "Republished", "sub": ["marked as a correction"], "icon": "email"},
      {"title": "Both kept", "sub": ["with what changed"], "icon": "log"}],
    "title": "A CORRECTION IS AS LOUD AS THE ORIGINAL",
    "note": "A quiet correction is indistinguishable from an error nobody admitted to."}),
   "How a correction is handled. Publishing it as prominently as the original is what stops a "
   "revised number looking like something that was hoped to go unnoticed.",
   "How a corrected tip split is republished",
   "A horizontal row of five boxes. Published: on Monday. Card refund lands: on Wednesday. "
   "Period reopened: and recomputed. Republished: marked clearly as a correction. Both kept: "
   "with a note of what changed. A note says a quiet correction is indistinguishable from an "
   "error nobody admitted to."),
  ("p", "The correction message says what changed and by how much, in the same place and the "
        "same way as the original. \"The pool fell by £18.40 because a card payment was refunded "
        "on Wednesday. Your share is £69.60, down £1.56.\" That sentence takes ten seconds to "
        "read and removes any possibility of somebody noticing a discrepancy later and drawing "
        "their own conclusion."),
  ("h3", "The archive"),
  ("p", "Every period keeps its pool, its rule, its rate, the hours it used, the shares it "
        "produced and who declared the cash. Twelve months of that is a complete answer to any "
        "question anybody will ever ask about tips, and it is a few kilobytes."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="period",
 volumes=[(4, "4 periods"), (13, "13 periods"), (52, "52 periods")],
 read_each=0.0002, msgs_each=14.0,
 lede=("This runs weekly over a few dozen rows and uses no model at all, so the entire variable "
       "cost is telling people their share. Four periods is a monthly split at one site; "
       "fifty-two is weekly across four sites. Here is where each cent goes."),
 takeaway_extra=("There is no model in this system at all. It is four multiplications and a "
                 "division, published."),
 risks=[
  "<strong>Emailing every person every period.</strong> That is the whole variable cost here: "
  "eleven people times fifty-two weeks is five hundred and seventy messages a year. Still cents, "
  "but it is the only line that scales at all.",
  "<strong>Recomputing published periods.</strong> Not a cost risk but the one that matters: a "
  "recompute triggered by a rule change would silently restate somebody's money.",
  "<strong>Log retention left at never.</strong> A weekly job producing almost nothing will "
  "still fill a log group forever without a retention setting.",
 ],
 per_unit_note=("The messaging band is the whole bill, because a period means one message per "
                "person. There is no read cost at all: nothing in this system calls a model."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="tp",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the decimal handling, and why there is no model anywhere in it."),
 outside=[
  {"title": "Card + hours", "sub": ["POS and payroll exports"], "icon": "money"},
  {"title": "Rule sheet", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["shares and summaries"], "icon": "email"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["exports,", "weekly schedule"], "icon": "bucket"},
  {"title": "Lambda x3", "sub": ["collect, split, publish"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["periods, rotation"], "icon": "database"}],
 note="us-east-1. One account. No model, and no path that moves money.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Card and hours, arriving as point-of-sale "
  "and payroll exports. The Rule sheet, read through the Google Sheets API read-only. And SES "
  "outbound, carrying shares and period summaries. Inside the account, three groups. S3 holding "
  "the exports and EventBridge carrying a weekly schedule. Three Lambda functions named collect, "
  "split and publish. And two DynamoDB tables named periods and rotation. A note gives the "
  "region as us-east-1, one account, with no model and no path that moves money."),
 functions=[
  ["<code>tp-collect</code>", "S3 ObjectCreated + Function URL",
   "Card figure, cash declaration, hours; completeness check", "20s / 512&nbsp;MB"],
  ["<code>tp-split</code>", "EventBridge weekly",
   "Weighted hours, rate, shares, remainder rotation", "20s / 512&nbsp;MB"],
  ["<code>tp-publish</code>", "SQS split queue",
   "Personal messages, the period summary, and the payroll export",
   "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>tp-collect-role</code>", "<code>s3:GetObject</code>, <code>dynamodb:UpdateItem</code>",
   "The exports prefix; the periods table"],
  ["<code>tp-split-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Periods and rotation; the Sheets credential only"],
  ["<code>tp-publish-role</code>", "<code>ses:SendEmail</code>, <code>s3:PutObject</code>",
   "One verified identity; the exports prefix"]],
 tables=[
  ("Table: periods",
   "PK   site              S   ashford\n"
   "SK   period_end        S   2026-07-26\n"
   "     state             S   collecting | split | published | corrected\n"
   "     card              N   642.30\n"
   "     cash              N   188.00\n"
   "     cash_declared_by  S   ash@example.com\n"
   "     cash_declared_at  S   2026-07-26T23:40:00Z\n"
   "     rule              M   the weights and basis, copied at split time\n"
   "     rate              S   \"2.6077\"   -- stored as a string, see below\n"
   "     shares            L   [{person, hours, weight, weighted, share}]\n"
   "     remainder         N   0.02\n"
   "     remainder_to      L   [sam@, kit@]\n"
   "     supersedes        S   a previous version, for a correction\n\n"
   "The rule is COPIED onto the period at split time. A later edit to the\n"
   "sheet cannot restate a published period."),
  ("Table: rotation",
   "PK   site              S   ashford\n"
   "     order             L   a stable list of people\n"
   "     position          N   4   -- carried between periods, never reset\n\n"
   "Resetting `position` each period is the bug that makes the rotation\n"
   "pointless: whoever is first in `order` would get a penny every week.")],
 inbound=[
  "<strong>Card and hours exports</strong> land in an S3 prefix from the point of sale and "
  "payroll. Both fire the same collect function.",
  "<strong>The cash declaration</strong> comes through a Function URL from a signed staff link, "
  "and records who declared it and when as first-class fields rather than metadata.",
  "<strong>Nothing is written back</strong> to payroll. The export is a file; paying people is "
  "payroll's job and this system has no credential for it.",
  "<strong>Personal share links</strong> are signed, scoped to one person and one period, and "
  "expire after ninety days."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Not in the request path, not in the "
  "reporting, not anywhere.",
  "<strong>That is worth stating explicitly</strong> in a series where most systems use one: "
  "this problem is arithmetic and a model would only add a way to be wrong about money.",
  "<strong>Use decimal arithmetic, not floats.</strong> Python's <code>Decimal</code> with an "
  "explicit context; the rate is stored as a string so it round-trips exactly.",
  "<strong>Round half up, not half even.</strong> Banker's rounding is correct in many contexts "
  "and surprising here, and surprise is the thing this system exists to remove.",
  "<strong>Compute the remainder from the pool</strong>, not by summing rounding errors. The "
  "two differ, and only the first is definitionally right."],
 gotchas=[
  "Use Decimal, never floats. A rate of 2.6077 in binary floating point will eventually produce "
  "a share that is a penny out and nobody will be able to explain why.",
  "Carry the rotation position between periods. Resetting it hands the same person a penny every "
  "week and makes the whole mechanism worse than useless.",
  "Copy the rule onto the period at split time. A sheet edit must never be able to restate a "
  "published period.",
  "Use final hours, not draft ones. A share that changes after publication costs more trust than "
  "a split published two days later.",
  "Never round in the house's favour, not even once, not even as a convention. It is four pounds "
  "a year and it is the loudest thing this system could say."],
))
