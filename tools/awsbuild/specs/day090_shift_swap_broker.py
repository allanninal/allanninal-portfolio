"""Day 90 -- 2026-07-23 -- Shift swap broker."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "shift-swap-broker"
NAME = "Shift swap broker"

SPEC = {
 "slug": SLUG, "date": "2026-07-23", "name": NAME,
 "tagline": ("Somebody needs Thursday off, the system finds who can actually cover it, and a "
             "manager approves one message instead of refereeing a group chat."),
 "lede": ("A small system that takes a request to give up a shift, works out who is genuinely "
          "eligible to take it -- qualified, available, and not heading into overtime -- offers "
          "it to them, and puts one clean swap in front of a manager to approve. It never "
          "changes a rota on its own. Seven posts on the same system -- one diagram at a time "
          "-- with a cost breakdown and an engineering reference at the end."),
 "keywords": ["shift swaps", "rostering", "scheduling", "hospitality", "retail", "serverless"],
 "icons": ["calendar", "team", "check"],
 "faq": [
  ("What is a shift swap broker?",
   "A small serverless system that handles the swap request itself: somebody offers up a shift, "
   "it works out who is eligible to take it, offers it to them in a sensible order, and sends "
   "one approval request to a manager. The rota is only changed by the manager approving."),
  ("Why not just use the group chat?",
   "Because the group chat cannot check anything. It does not know who is qualified for that "
   "station, who is already on that day, who would go into overtime, or who has had four swaps "
   "this month. All of that gets discovered after the swap is agreed, which is when it becomes "
   "a manager's problem."),
  ("Does it change the rota automatically?",
   "No. It produces one approved-or-not decision for a manager, with the eligibility already "
   "checked. Approval writes the swap; nothing else does."),
  ("What stops one person doing all the swaps?",
   "A per-person cap in the rules sheet, counted over a rolling window. Somebody who has "
   "already taken four extra shifts this month stops being offered them, which protects both "
   "the business and them."),
  ("What does it cost to run?",
   "A couple of dollars a month even for a business running a few hundred shifts. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "shift-swap-broker-on-aws",
 "title": "A shift swap broker on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 880,
 "desc": ("Takes a shift somebody cannot work, finds who is genuinely eligible, offers it in "
          "order, and sends a manager one swap to approve. AWS, about $2 a month."),
 "og": ("The group chat cannot check qualifications, availability or overtime. This does all "
        "three before anybody agrees to anything."),
 "abstract": ("The whole system on one page -- an eligibility check, an offer loop and an "
              "approval -- built so a manager sees one clean swap rather than a negotiation."),
 "lede": ("Shift swapping in a small business happens in a group chat, and the group chat is "
          "genuinely quite good at the social part. What it cannot do is check anything. So the "
          "swap gets agreed by two people on Tuesday and a manager discovers on Thursday that "
          "the cover is not trained on the till, or is already on a double, or has just gone "
          "into overtime. This post walks through a small system that does the checking before "
          "anybody agrees to anything."),
 "tags": ["shift swaps", "rostering", "scheduling", "hospitality", "human in the loop",
          "serverless"],
 "takeaways": [
  "Eligibility is checked before an offer is made, not after a swap is agreed.",
  "Four checks: qualified, free, not into overtime, not over their swap cap.",
  "Offers go out in an order you set, not to everybody at once.",
  "A manager approves one clean swap. Nothing writes the rota except that approval.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "The rota", "sub": ["who is on, where"], "icon": "calendar"},
      {"title": "Rules", "sub": ["skills, caps, overtime"], "icon": "doc"},
      {"title": "Staff + manager", "sub": ["offered, then approved"], "icon": "team"}],
    "inside": [
      {"title": "Eligibility", "sub": ["four checks, before", "any offer goes out"], "icon": "filter"},
      {"title": "Offer loop", "sub": ["in order, with", "a time limit"], "icon": "clock"},
      {"title": "Approval", "sub": ["one swap, one tap,", "then the rota moves"], "icon": "check"}],
    "edges": [{"from": 0, "to": 0, "label": "shifts and cover"},
              {"from": 1, "to": 1, "label": "who may work what"},
              {"from": 2, "to": 2, "label": "one swap to approve", "up": True}],
    "note": "Nothing writes the rota except a manager approving. The system only proposes."}),
   "Three things outside the account, three pieces inside it. The eligibility box runs first, "
   "which is the whole difference between this and a group chat.",
   "System: a rota and rules in, one approvable swap out",
   "Three boxes across the top sit outside the AWS account. On the left, The rota: who is on and "
   "where. In the middle, Rules: the skills each station needs, the per-person swap caps and the "
   "overtime thresholds. On the right, Staff and manager: the people offered a shift and the "
   "person who approves. Each connects by an arrow to the AWS account container below. Shifts "
   "and cover flow down into the account. The rules feed in who may work what. One swap to "
   "approve goes back out. Inside the AWS account are three components in a row. On the left, "
   "Eligibility, running four checks before any offer goes out. In the middle, the Offer loop, "
   "which offers in order with a time limit. On the right, Approval, which turns one tap into a "
   "rota change. A note at the bottom says nothing writes the rota except a manager approving, "
   "and the system only proposes."),
  ("h3", "The four checks"),
  ("table", ["Check", "Reads", "Why it has to come first"], [
   ["Qualified", "The skills each station needs", "A swap onto a station somebody cannot work is not a swap"],
   ["Free", "The rota for that day and around it", "Already on, or on a rest day that would be broken"],
   ["Overtime", "Hours already rostered that week", "A swap that quietly costs time-and-a-half"],
   ["Swap cap", "Swaps taken in a rolling window", "One person absorbing every gap is a problem for them"],
  ]),
  ("p", "Every one of those is checkable in advance and none of them is checkable in a group "
        "chat. Doing them before the offer rather than after the agreement is the entire design, "
        "because a swap that gets agreed and then refused is worse for everybody than one that "
        "was never offered."),
  ("h3", "What runs on every request (the inside)"),
  ("ul", [
   "<strong>Eligibility.</strong> Runs the four checks against everybody and produces a short "
   "ordered list, usually three to six people. It is arithmetic against a rota and a rules "
   "sheet, and no model is involved anywhere in it.",
   "<strong>The offer loop.</strong> Offers the shift to the list in order, one or a few at a "
   "time, with a time limit. Offering to everybody at once produces a race and hurt feelings; "
   "offering one at a time takes too long. Part 4 covers the middle ground.",
   "<strong>Approval.</strong> Sends the manager one message: who is giving up what, who is "
   "taking it, and the sentence that matters &mdash; that all four checks passed, or which one "
   "was overridden. One tap writes the swap to the rota.",
  ]),
  ("h2", "One swap, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Offered up", "sub": ["I can't do Thursday"], "icon": "phone"},
      {"title": "Checked", "sub": ["who is actually eligible"], "icon": "filter"},
      {"title": "Offered out", "sub": ["in order, with a clock"], "icon": "clock"},
      {"title": "Taken", "sub": ["first to accept"], "icon": "check"},
      {"title": "Approved", "sub": ["one tap, rota moves"], "icon": "team"}],
    "title": "ONE SWAP, END TO END",
    "note": "The manager appears once, at the end, with nothing left to work out."}),
   "The same system as one line. A manager is involved exactly once, and by then every question "
   "they would have asked has already been answered.",
   "One shift swap from request to approved rota change, in five stages",
   "A horizontal row of five boxes joined by arrows. Offered up: somebody says they cannot do "
   "Thursday. Checked: the system works out who is actually eligible. Offered out: in order, "
   "with a clock. Taken: by the first person to accept. Approved: one tap, and the rota moves. A "
   "note says the manager appears once, at the end, with nothing left to work out."),
  ("h2", "In plain words"),
  ("p", "A supervisor cannot work Thursday evening and says so on Monday. The eligibility check "
        "runs: eleven people work that site, four are already on Thursday, two are not trained "
        "on the station, one would cross forty hours, and one has taken four extra shifts this "
        "month and is at their cap. That leaves three, ordered by who has taken the fewest extra "
        "shifts recently."),
  ("p", "The offer goes to those three with a four-hour window. The second one accepts within "
        "twenty minutes. The manager gets one message: \"Thursday 6&ndash;11, Ash giving up, "
        "Rae taking. Qualified, free, 31 hours before this, 3 swaps in the last 30 days. "
        "Approve?\" They tap approve on their phone and the rota updates. Total manager "
        "involvement: about eight seconds, and the alternative is a group chat they have to read "
        "and then check four things by hand."),
  ("callout", "Design rules that shaped every decision", [
   "Check before you offer. A swap that is agreed and then refused damages more than one that "
   "was never offered.",
   "Offer in an order, not to everybody. A free-for-all gives every shift to whoever has "
   "notifications on.",
   "The cap protects the person as much as the business. Somebody absorbing every gap is heading "
   "somewhere bad.",
   "Only approval writes the rota. The system proposes; a manager decides, always.",
   "An override is allowed and recorded. Sometimes the untrained person is the right answer and "
   "a manager knows why.",
   "Nobody is told who declined. A shift going to the third person on the list is not "
   "information anybody needs.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The group chat is not the problem; it is a reasonable place to ask a question. The "
        "problem is that the answer it produces is unverified, and verification is exactly the "
        "part a computer does well and a manager does slowly on a Thursday."),
  ("p", "So the design leaves the social part alone &mdash; people still know who covered for "
        "them, and can still ask each other directly &mdash; and inserts the four checks in "
        "front of the offer. A manager stops being the person who discovers problems and becomes "
        "the person who approves a decision that has already been checked."),
  ("p", "The next four posts walk through each piece: how a shift gets offered up, how "
        "eligibility is computed, how the offer loop works, and how an approval writes the rota. "
        "One diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-shift-gets-offered-up",
 "title": "How a shift gets offered up",
 "nav": "How it is offered up",
 "read": 5, "words": 760,
 "desc": ("Two taps to give up a shift, why a reason is optional, the cut-off before which a "
          "swap is a swap and after which it is an absence."),
 "og": ("Two taps, an optional reason, and a cut-off. After the cut-off it is not a swap request "
        "at all -- it is an absence, and it needs a different path."),
 "abstract": ("Two taps to give up a shift, why the reason is optional, and the cut-off that "
              "separates a swap request from an absence."),
 "lede": ("Giving up a shift has to be as easy as sending a message to the group, or people will "
          "send a message to the group. Everything in this step is in service of that, plus one "
          "genuinely important boundary: the point at which a request stops being a swap."),
 "tags": ["shift swaps", "rostering", "mobile forms", "absence", "scheduling", "serverless"],
 "takeaways": [
  "Two taps: pick the shift from your own rota, confirm.",
  "A reason is optional and never shown to colleagues, only to the manager.",
  "Before the cut-off it is a swap. After it, it is an absence and takes a different path.",
  "A shift can be withdrawn until somebody accepts it, and not after.",
  "Nobody can offer up somebody else's shift.",
 ],
 "blocks": [
  ("h2", "Two taps"),
  ("p", "The screen shows your own next fortnight from the rota. Tap a shift, confirm, done. "
        "There is no form, no reason required and no approval to make the request &mdash; asking "
        "to swap is not something anybody needs permission for."),
  ("fig", ("chain", {
    "entry": {"title": "Tap a shift", "sub": ["from your own rota"], "icon": "phone"},
    "steps": [
      {"title": "Is it yours?", "sub": ["from the rota, not the form"], "icon": "branch",
       "exit": {"title": "Refused", "sub": ["nobody offers up", "somebody else's shift"],
                "icon": "stop", "label": "no"}},
      {"title": "Before the cut-off?", "sub": ["e.g. 24 hours"], "icon": "branch",
       "side": {"title": "Rules sheet", "sub": ["the cut-off"], "icon": "doc"},
       "exit": {"title": "This is an absence", "sub": ["tell the manager directly"],
                "icon": "alarm", "label": "no"}},
      {"title": "Optional reason", "sub": ["manager only, never staff"], "icon": "form"},
      {"title": "Run eligibility", "sub": ["before anybody is told"], "icon": "filter"},
      {"title": "Offers go out", "sub": ["in order"], "icon": "clock"}],
    "note": "The cut-off is not bureaucracy. A swap and an absence need different responses."}),
   "How a shift is offered up. The cut-off check is the important one: past it, the honest "
   "answer is that this is no longer a swap and pretending otherwise wastes hours.",
   "How a shift is offered up for swapping",
   "A vertical chain of five steps entered by a box labelled Tap a shift, from your own rota. "
   "Step one asks whether it is yours, determined from the rota rather than from the form; if "
   "not it exits to Refused, because nobody offers up somebody else's shift. Step two asks "
   "whether it is before the cut-off, for example twenty-four hours, read from the rules sheet; "
   "if not it exits to This is an absence, which tells the manager directly. Step three offers "
   "an optional reason, visible to the manager and never to colleagues. Step four runs "
   "eligibility before anybody is told. Step five sends the offers out in order. A note says the "
   "cut-off is not bureaucracy, because a swap and an absence need different responses."),
  ("h3", "Why the reason is optional"),
  ("p", "Requiring a reason to swap a shift changes what the request is. It turns a peer "
        "arrangement into a permission request, and it invites a manager to evaluate reasons, "
        "which is a much worse job than evaluating swaps. Most people give one anyway, because "
        "it feels polite, and that is fine."),
  ("p", "When a reason is given it goes to the manager on the approval message and never to "
        "colleagues. \"Rae is covering Ash's Thursday\" is all anybody else needs, and it is "
        "also all anybody else is entitled to."),
  ("h2", "The cut-off"),
  ("p", "Somewhere between twelve and forty-eight hours before a shift, depending on your "
        "business, a swap request stops being a swap request. Not because of a rule, but because "
        "the process no longer fits: there is not time for an offer loop, the people who might "
        "cover are already at work or asleep, and what is actually happening is that somebody "
        "cannot come in."),
  ("fig", ("strip", {
    "stages": [
      {"title": "7 days out", "sub": ["ordinary swap"], "icon": "calendar"},
      {"title": "48 hours", "sub": ["still a swap"], "icon": "clock"},
      {"title": "The cut-off", "sub": ["24 hours, say"], "icon": "branch"},
      {"title": "Inside it", "sub": ["an absence, not a swap"], "icon": "alarm"},
      {"title": "Different path", "sub": ["straight to the manager"], "icon": "team"}],
    "title": "WHERE A SWAP BECOMES AN ABSENCE",
    "note": "Running an offer loop three hours before a shift wastes the three hours."}),
   "The boundary between a swap and an absence. Naming it explicitly prevents the failure where "
   "an offer loop is still running while a shift starts.",
   "The point at which a swap request becomes an absence",
   "A horizontal row of five boxes. Seven days out: an ordinary swap. Forty-eight hours: still a "
   "swap. The cut-off: twenty-four hours, say. Inside it: an absence rather than a swap. "
   "Different path: straight to the manager. A note says running an offer loop three hours "
   "before a shift wastes the three hours."),
  ("p", "Inside the cut-off, the app says so plainly and hands off: \"This is less than 24 hours "
        "away, so it goes straight to your manager rather than out for swaps.\" The manager gets "
        "a message immediately with the same eligibility list attached, so they can ring "
        "somebody rather than work out who to ring."),
  ("h2", "Withdrawing"),
  ("p", "A shift can be withdrawn until somebody accepts it, and not afterwards. That asymmetry "
        "is deliberate: a person who has accepted a shift has rearranged their day around it, "
        "and letting the original person take it back with a tap makes accepting a shift feel "
        "risky. After acceptance, a withdrawal is a conversation with the manager, which is "
        "correct because it is now two people's problem."),
  ("p", "Next: the four eligibility checks, in detail."),
 ],
},
{
 "slug": "how-eligibility-is-computed",
 "title": "How eligibility is computed",
 "nav": "How eligibility works",
 "read": 5, "words": 780,
 "desc": ("Qualified, free, overtime and cap -- what each one actually reads, and why the "
          "ordering of the resulting list matters more than the filtering."),
 "og": ("Four filters produce a short list. The order that list is in decides who actually gets "
        "the extra hours, which makes it the most consequential line of code here."),
 "abstract": ("What each of the four eligibility checks actually reads, and why the ordering of "
              "the surviving list matters more than the filtering does."),
 "lede": ("The filtering is straightforward and the ordering is not, because the order of the "
          "list is what determines who gets extra hours over a year. That is a distributional "
          "decision dressed as a sort key, and it is worth making deliberately."),
 "tags": ["shift swaps", "rostering", "fairness", "overtime", "scheduling", "serverless"],
 "takeaways": [
  "Qualified reads a skills matrix, not a job title.",
  "Free means not rostered and not breaking a rest rule, which is more than checking the day.",
  "Overtime is computed from the whole week, not the shift.",
  "The cap is a rolling window per person, and it protects them as much as the business.",
  "Ordering by fewest recent extra shifts is the fairest default and it is a choice.",
 ],
 "blocks": [
  ("h2", "The four filters"),
  ("fig", ("chain", {
    "entry": {"title": "Everyone at the site", "sub": ["the starting set"], "icon": "team"},
    "steps": [
      {"title": "Qualified for the station?", "sub": ["skills matrix"], "icon": "branch",
       "side": {"title": "Skills", "sub": ["person x station"], "icon": "chart"}},
      {"title": "Free, and legally free?", "sub": ["rostered, and rest rules"], "icon": "branch",
       "side": {"title": "The rota", "sub": ["the week either side"], "icon": "calendar"}},
      {"title": "Stays under overtime?", "sub": ["week total + this shift"], "icon": "branch",
       "side": {"title": "Rules", "sub": ["threshold per contract"], "icon": "doc"}},
      {"title": "Under their swap cap?", "sub": ["rolling 30 days"], "icon": "branch"},
      {"title": "A short ordered list", "sub": ["usually three to six"], "icon": "counter"}],
    "note": "All four are arithmetic. Nothing here involves judgement or a model."}),
   "The four filters in order. Each removes people for a different reason and each reads "
   "something the business already maintains.",
   "The four eligibility filters applied to a shift swap",
   "A vertical chain of five steps entered by a box labelled Everyone at the site, the starting "
   "set. Step one asks whether each person is qualified for the station, reading a skills matrix "
   "of person by station. Step two asks whether they are free and legally free, checking the "
   "rota for the week either side for both rostered shifts and rest rules. Step three asks "
   "whether they stay under the overtime threshold, adding this shift to their week total "
   "against a per-contract threshold from the rules. Step four asks whether they are under their "
   "swap cap over a rolling thirty days. Step five produces a short ordered list, usually three "
   "to six people. A note says all four are arithmetic and nothing here involves judgement or a "
   "model."),
  ("h3", "Qualified means a station, not a job title"),
  ("p", "Two people with the same title are frequently not interchangeable: one is trained on "
        "the coffee machine and one is not, one has the forklift ticket and one does not. So the "
        "skills matrix is per person per station, and a shift carries the station it covers "
        "rather than a role name."),
  ("p", "This is the check most likely to be missing when a business first builds something like "
        "this, because the rota shows names and times and not what each person is actually "
        "doing. Adding a station to each rota line is the prerequisite, and it is usually a "
        "morning's work that improves the rota independently."),
  ("h3", "Free means more than not rostered"),
  ("p", "Somebody with nothing on Thursday might still be ineligible: they finish at eleven on "
        "Wednesday and start at six on Friday, and taking a Thursday evening would break a rest "
        "rule. So the check reads the week either side, not the day, and the rest rules live in "
        "the sheet because they differ by contract and by jurisdiction."),
  ("h3", "The cap protects the person"),
  ("p", "The swap cap sounds like a control on the business and is mostly a control on "
        "enthusiasm. There is always somebody who takes every available shift, and left alone "
        "they will work six weeks straight and then either burn out or make a mistake. Four "
        "extra shifts in a rolling thirty days is a reasonable default and it should be visible "
        "to them: \"you are at your cap for the next nine days\" is a much better message than "
        "silence."),
  ("h2", "The ordering"),
  ("p", "After filtering there are usually three to six people, and the order they are offered "
        "in is the single most consequential decision in this system, because over a year it "
        "determines who gets extra hours and therefore extra money."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Fewest recent swaps", "sub": ["the default"], "icon": "counter"},
      {"title": "Nearest the site", "sub": ["for late shifts"], "icon": "map"},
      {"title": "Asked to be offered", "sub": ["an opt-in flag"], "icon": "check"},
      {"title": "Random", "sub": ["genuinely defensible"], "icon": "branch"},
      {"title": "Never seniority", "sub": ["or who asked last time"], "icon": "stop"}],
    "title": "FOUR WAYS TO ORDER, AND ONE NOT TO",
    "note": "Whichever you pick, publish it. An unexplained order is assumed to be favouritism."}),
   "The ordering options and the one to avoid. The real requirement is not that the order is "
   "optimal but that it is stated, because an unexplained order will be assumed to be unfair.",
   "Four ways to order the eligible list, and one to avoid",
   "A horizontal row of five boxes. Fewest recent swaps: the default. Nearest the site: useful "
   "for late shifts. Asked to be offered: an opt-in flag people can set. Random: genuinely "
   "defensible. Never seniority: nor who asked last time. A note says whichever you pick, "
   "publish it, because an unexplained order is assumed to be favouritism."),
  ("p", "Fewest recent extra shifts is the default because it self-corrects: somebody who takes "
        "a swap moves down the list, and the hours spread. Random is genuinely defensible and "
        "has the advantage of being obviously not favouritism. Seniority is the one to avoid, "
        "because extra hours are money and distributing money by seniority through a scheduling "
        "system is a decision somebody should make explicitly if they are going to make it at "
        "all."),
  ("p", "Next: how the offers actually go out."),
 ],
},
{
 "slug": "how-the-offer-loop-works",
 "title": "How the offer loop works",
 "nav": "How offers go out",
 "read": 5, "words": 760,
 "desc": ("Why not everybody at once, why not one at a time, the time limit, and what happens "
          "when the list runs out."),
 "og": ("Offering to everybody is a race; offering one at a time is too slow. Small batches "
        "with a clock is the middle ground, and the clock shrinks as the shift approaches."),
 "abstract": ("Why offers go out in small batches rather than to everybody or one at a time, how "
              "the time limit shrinks as the shift approaches, and what happens when the list "
              "runs out."),
 "lede": ("There are two obvious ways to run an offer loop and both are wrong. Sending to "
          "everybody at once produces a race that the person with notifications on always wins. "
          "Sending to one person at a time is fair and takes three days. This post is about the "
          "middle."),
 "tags": ["shift swaps", "notifications", "fairness", "scheduling", "Amazon SNS", "serverless"],
 "takeaways": [
  "Batches of two or three, in list order, with a time limit per batch.",
  "The time limit shrinks as the shift gets closer, from hours to minutes.",
  "First to accept wins within a batch, and a conditional write makes that safe.",
  "Nobody is told they were in a later batch, or that somebody declined.",
  "When the list runs out, the manager is told with the reason each person was excluded.",
 ],
 "blocks": [
  ("h2", "Batches with a clock"),
  ("fig", ("chain", {
    "entry": {"title": "An ordered list", "sub": ["three to six people"], "icon": "counter"},
    "steps": [
      {"title": "Offer to the first batch", "sub": ["two or three"], "icon": "phone",
       "side": {"title": "Time limit", "sub": ["from days-to-shift"], "icon": "clock"}},
      {"title": "Anyone accepted?", "sub": ["conditional write"], "icon": "branch",
       "exit": {"title": "Taken", "sub": ["close the others quietly"], "icon": "check",
                "label": "yes"}},
      {"title": "Limit expired?", "sub": ["and more people left"], "icon": "branch",
       "exit": {"title": "Next batch", "sub": ["same size, shorter clock"], "icon": "retry",
                "label": "yes"}},
      {"title": "List exhausted", "sub": ["nobody eligible left"], "icon": "alarm"},
      {"title": "Tell the manager", "sub": ["with why each was excluded"], "icon": "team"}],
    "note": "The last step is the useful one. 'Nobody available' is not an answer a manager can use."}),
   "The offer loop. The exhausted path is the one that earns its place: a manager needs to know "
   "why nobody was eligible, not merely that nobody was.",
   "How a shift offer is sent out in batches with a time limit",
   "A vertical chain of five steps entered by a box labelled An ordered list of three to six "
   "people. Step one offers to the first batch of two or three, with a time limit derived from "
   "how many days remain until the shift. Step two asks whether anyone accepted, decided by a "
   "conditional write; an acceptance exits to Taken, which quietly closes the other offers. Step "
   "three asks whether the limit expired with more people left, exiting to Next batch at the "
   "same size with a shorter clock. Step four is List exhausted, with nobody eligible left. Step "
   "five tells the manager, including why each person was excluded. A note says the last step is "
   "the useful one, because nobody available is not an answer a manager can use."),
  ("h3", "Why two or three"),
  ("p", "One at a time is fairest and far too slow: three people with a four-hour window each is "
        "half a day before the fourth is even asked. Everybody at once is instant and gives every "
        "shift to whoever happens to be looking at their phone, which over a year is a real and "
        "unfair distribution of money."),
  ("p", "Two or three at a time keeps the loop moving while preserving most of the ordering's "
        "effect. The people at the top of the list still get first refusal; they just get it "
        "alongside one or two others rather than alone."),
  ("h3", "The shrinking clock"),
  ("table", ["Days to the shift", "Window per batch", "Why"], [
   ["7 or more", "8 hours", "No urgency; let people see it when they wake up"],
   ["3 to 6", "4 hours", "Still comfortable, but the loop needs to finish"],
   ["2", "90 minutes", "Two batches will fit into a day"],
   ["1", "30 minutes", "Effectively the last chance before it becomes the manager's"],
  ]),
  ("p", "A fixed window fails at both ends: eight hours per batch a day before the shift means "
        "the loop is still running when the shift starts, and thirty minutes a week out is "
        "needlessly aggressive about a Thursday that is seven days away."),
  ("h2", "Winning a race safely"),
  ("p", "Two people in the same batch can accept within the same second, and exactly one has to "
        "win. That is a conditional write on the offer's state: the first accept sets it from "
        "<code>open</code> to <code>taken</code>, and the second finds it already taken and is "
        "shown that plainly rather than being told it succeeded."),
  ("p", "The message the loser sees matters: \"Rae got there first\" is honest and fine. \"You "
        "were not selected\" is not what happened and reads badly. It is one sentence and it is "
        "the difference between a system people use and one they resent."),
  ("h2", "When nobody takes it"),
  ("fig", ("strip", {
    "stages": [
      {"title": "11 at the site", "sub": ["the starting set"], "icon": "team"},
      {"title": "4 already on", "sub": ["not free"], "icon": "calendar"},
      {"title": "2 untrained", "sub": ["on that station"], "icon": "shield"},
      {"title": "2 into overtime", "sub": ["would cross 40h"], "icon": "money"},
      {"title": "3 asked, none took", "sub": ["manager's now"], "icon": "person"}],
    "title": "WHY NOBODY COVERED",
    "note": "A manager can act on this. 'No cover found' gives them nothing to work with."}),
   "What the manager is told when a swap fails. The breakdown is the difference between a "
   "dead end and a decision: two of those four numbers are things a manager can override.",
   "The breakdown a manager receives when nobody takes a shift",
   "A horizontal row of five boxes. Eleven at the site: the starting set. Four already on: not "
   "free. Two untrained: on that station. Two into overtime: would cross forty hours. Three "
   "asked, none took: so it is now the manager's. A note says a manager can act on this, whereas "
   "no cover found gives them nothing to work with."),
  ("p", "That breakdown is genuinely actionable. Two people excluded for overtime is a decision a "
        "manager can take &mdash; approve the overtime, or not. Two untrained on the station is a "
        "training gap that this exact situation will produce again next month. \"No cover found\" "
        "contains none of that."),
  ("p", "Next: what approval actually does."),
 ],
},
{
 "slug": "how-an-approval-writes-the-rota",
 "title": "How an approval writes the rota",
 "nav": "How approval works",
 "read": 5, "words": 740,
 "desc": ("One message, one tap, and the four things that change -- plus overrides, and the "
          "monthly report that shows whether the swap rules still fit."),
 "og": ("One tap writes four things: the rota, both people's hours, the swap counters, and the "
        "record. Overrides are allowed and recorded with a reason."),
 "abstract": ("What one approval actually changes, why an override is allowed and recorded, and "
              "the monthly report that says whether the swap rules still fit the business."),
 "lede": ("Approval is one tap and four writes, and the interesting part is what happens when a "
          "manager wants to approve something that failed a check &mdash; which is not a bug in "
          "the design but a feature of every real rota."),
 "tags": ["shift swaps", "rostering", "audit trail", "reporting", "DynamoDB", "serverless"],
 "takeaways": [
  "Approval writes the rota, both people's hours, the swap counters, and the record.",
  "A manager can override a failed check, and the override is recorded with a reason.",
  "An override is never silent. Both people are told which rule was set aside.",
  "The record keeps who gave up, who took, and why they were eligible at the time.",
  "One monthly number matters: how many swaps failed for lack of anybody eligible.",
 ],
 "blocks": [
  ("h2", "What one tap changes"),
  ("fig", ("chain", {
    "entry": {"title": "Approve tapped", "sub": ["signed, single-use"], "icon": "check"},
    "steps": [
      {"title": "Still open?", "sub": ["conditional write"], "icon": "branch",
       "side": {"title": "The swap", "sub": ["state = accepted"], "icon": "database"},
       "exit": {"title": "Already decided", "sub": ["show what happened"], "icon": "stop",
                "label": "second tap"}},
      {"title": "Write the rota", "sub": ["the shift changes hands"], "icon": "calendar"},
      {"title": "Move both hour totals", "sub": ["for overtime next time"], "icon": "counter"},
      {"title": "Increment the counters", "sub": ["the taker's swap count"], "icon": "log"},
      {"title": "Tell both people", "sub": ["and close the loop"], "icon": "email"}],
    "note": "The hour totals matter: without them, the next swap's overtime check is wrong."}),
   "The four writes behind one tap. Moving both hour totals is easy to forget and makes every "
   "subsequent overtime check wrong until somebody notices.",
   "What happens when a manager approves a shift swap",
   "A vertical chain of five steps entered by a box labelled Approve tapped, signed and "
   "single-use. Step one asks whether the swap is still open using a conditional write against "
   "its state; a second tap exits to Already decided, which shows what happened. Step two writes "
   "the rota so the shift changes hands. Step three moves both people's hour totals, which "
   "matters for the next overtime check. Step four increments the taker's swap counter. Step "
   "five tells both people and closes the loop. A note says the hour totals matter, because "
   "without them the next swap's overtime check is wrong."),
  ("h2", "Overrides"),
  ("p", "A manager will sometimes want to approve a swap that failed a check, and they are "
        "usually right. The untrained person is being trained on that station this week. The "
        "overtime is fine because a quiet week is coming. The cap can be stretched because "
        "somebody asked to work more."),
  ("ul", [
   "<strong>Overrides are allowed.</strong> A system that refuses a manager's judgement gets "
   "worked around within a month, and then the swaps happen in the group chat again with no "
   "record at all.",
   "<strong>They require a reason.</strong> One line, free text. Not a dropdown, because the "
   "reasons that matter are the ones nobody anticipated.",
   "<strong>Both people are told which rule was set aside.</strong> Somebody taking a shift they "
   "are not signed off on should know that, and so should the person handing it over.",
   "<strong>They are counted.</strong> Three overrides of the same check in a month is a rule "
   "that does not fit the business, and it should be changed rather than routinely ignored.",
  ]),
  ("h2", "The record"),
  ("table", ["Field", "Example", "Why"], [
   ["Shift", "Thu 24 Jul, 18:00&ndash;23:00, till 2", "What moved"],
   ["Gave up / took", "ash@ / rae@", "Who"],
   ["Eligibility at the time", "qualified, free, 31h, 3 swaps", "Why it was allowed then"],
   ["Approved by", "manager@", "Who decided"],
   ["Override", "none, or the rule and the reason", "What was set aside, if anything"],
   ["Offered to", "3 people, 2 batches", "How the loop ran, for the fairness report"],
  ]),
  ("p", "The eligibility snapshot is the field that earns its keep later. \"Rae was on 31 hours "
        "when this was approved\" answers, months afterwards, why a swap that looks wrong now was "
        "reasonable at the time &mdash; which is the same argument as the <code>basis</code> "
        "field in the purchase order approver, and for the same reason."),
  ("h2", "The monthly numbers"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Requested", "sub": ["34 swaps"], "icon": "phone"},
      {"title": "Covered", "sub": ["29"], "icon": "check"},
      {"title": "Nobody eligible", "sub": ["3"], "icon": "alarm"},
      {"title": "Overrides", "sub": ["2, both training"], "icon": "log"},
      {"title": "Spread", "sub": ["top taker: 5 of 29"], "icon": "counter"}],
    "title": "ONE MONTH OF SWAPS",
    "note": "The third number is a training gap. The fifth is whether the ordering is working."}),
   "A month of swaps in five numbers. The last two are the ones that lead to a change: a "
   "training gap, and whether extra hours are actually spreading.",
   "One month of shift swaps summarised in five numbers",
   "A horizontal row of five boxes. Requested: thirty-four swaps. Covered: twenty-nine. Nobody "
   "eligible: three. Overrides: two, both for training reasons. Spread: the top taker had five "
   "of the twenty-nine. A note says the third number is a training gap and the fifth is whether "
   "the ordering is working."),
  ("p", "Three swaps failing for lack of anybody eligible is almost always the same story: a "
        "station only two people are trained on. Training a third is a half-day and it removes "
        "the problem permanently, and the only reason it does not happen is that nobody counts "
        "how often it costs something."),
  ("p", "The spread number is the check on the ordering from Part 3. One person taking five of "
        "twenty-nine is healthy; one person taking eighteen means either the ordering is not "
        "working or a lot of people are ineligible, and both are worth looking at."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="swap",
 volumes=[(15, "15 swaps"), (40, "40 swaps"), (150, "150 swaps")],
 read_each=0.0002, msgs_each=4.5,
 extra=[("sms", "SNS SMS &mdash; offers to phones", "#DD344C", 0.0180, 0.0)],
 lede=("This system barely touches a model at all &mdash; eligibility is set arithmetic over a "
       "rota. What it does do is send a lot of messages, and if those messages are texts rather "
       "than push notifications they are the entire bill. Here is where each cent goes."),
 takeaway_extra=("SMS is the whole variable cost. Push notifications through a web app make this "
                 "system essentially free to run."),
 risks=[
  "<strong>SMS for everything.</strong> An offer loop that texts three people per batch across "
  "two batches is six messages per swap, and at a hundred and fifty swaps a month that is the "
  "dominant line. A web push, or email for anything more than a day out, removes most of it.",
  "<strong>Re-running eligibility on every batch.</strong> Compute the ordered list once when "
  "the shift is offered up, not per batch. Recomputing also risks the list changing mid-loop, "
  "which produces somebody being offered a shift and then silently dropped.",
  "<strong>Log retention left at never.</strong> A busy rota produces a lot of small events, and "
  "without a retention setting the logs will out-cost every other line.",
 ],
 per_unit_note=("The SMS band assumes texts to every offer recipient. A business whose staff use "
                "a saved home-screen link with web push pays essentially nothing for messaging, "
                "which takes the whole system to about a dollar a month."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ss",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the race condition, and why there is almost no model here."),
 outside=[
  {"title": "Rota + rules", "sub": ["Sheets API or rota app"], "icon": "calendar"},
  {"title": "Staff app", "sub": ["CloudFront + S3"], "icon": "phone"},
  {"title": "SNS + SES", "sub": ["offers, approvals"], "icon": "email"}],
 inside=[
  {"title": "EventBridge", "sub": ["batch timers,", "expiry sweep"], "icon": "clock"},
  {"title": "Lambda x4", "sub": ["offer, eligible,", "accept, approve"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["swaps, counters"], "icon": "database"}],
 note="us-east-1. One account. The rota is the source of truth and is written only on approval.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Rota and rules, read through the Google "
  "Sheets API or a rota application. The Staff app, served as static files from S3 behind "
  "CloudFront. And SNS with SES, carrying offers and approval requests. Inside the account, "
  "three groups. EventBridge carrying batch timers and an expiry sweep. Four Lambda functions "
  "named offer, eligible, accept and approve. And two DynamoDB tables named swaps and counters. "
  "A note gives the region as us-east-1, one account, and states that the rota is the source of "
  "truth and is written only on approval."),
 functions=[
  ["<code>ss-offer</code>", "Function URL",
   "Validates ownership and the cut-off; creates the swap", "10s / 512&nbsp;MB"],
  ["<code>ss-eligible</code>", "SQS swap queue",
   "The four filters and the ordering; sends the first batch", "20s / 512&nbsp;MB"],
  ["<code>ss-accept</code>", "Function URL",
   "Conditional write on the swap; closes the losing offers", "10s / 512&nbsp;MB"],
  ["<code>ss-approve</code>", "Function URL + EventBridge",
   "Writes the rota and the counters; runs the batch timers", "20s / 512&nbsp;MB"]],
 roles=[
  ["<code>ss-offer-role</code>", "<code>dynamodb:PutItem</code>, <code>sqs:SendMessage</code>",
   "The swaps table; the swap queue"],
  ["<code>ss-eligible-role</code>",
   "<code>dynamodb:Query</code>, <code>sns:Publish</code>, <code>secretsmanager:GetSecretValue</code>",
   "Counters, read; staff numbers only; the rota credential"],
  ["<code>ss-accept-role</code>", "<code>dynamodb:UpdateItem</code>",
   "The swaps table only"],
  ["<code>ss-approve-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>secretsmanager:GetSecretValue</code>, "
   "<code>ses:SendEmail</code>",
   "Swaps and counters; the rota credential; one identity"]],
 tables=[
  ("Table: swaps",
   "PK   swap_id           S   swp_2026_07_23_5e21\n"
   "     shift             M   {date, start, end, site, station}\n"
   "     giving_up         S   ash@example.com\n"
   "     taking            S   rae@example.com, or null\n"
   "     state             S   open | accepted | approved | expired | withdrawn\n"
   "     eligible          L   the ordered list, computed ONCE\n"
   "     batch             N   which batch is currently out\n"
   "     batch_expires     S   2026-07-23T16:00:00Z\n"
   "     snapshot          M   the taker's hours and swap count at approval\n"
   "     override          M   {rule, reason, by} or null\n\n"
   "The accept:\n"
   "  UpdateExpression:    SET taking = :who, #s = :accepted\n"
   "  ConditionExpression: #s = :open\n"
   "Two people accepting in the same second cannot both satisfy that."),
  ("Table: counters",
   "PK   person            S   rae@example.com\n"
   "     swaps_taken       L   [ISO dates, last 90 days]\n"
   "     hours_by_week     M   {2026-W30: 31.0, ...}\n\n"
   "`swaps_taken` is a list of dates rather than a count, so the rolling\n"
   "30-day window is computed rather than maintained -- which means it cannot\n"
   "drift and does not need a nightly reset job.")],
 inbound=[
  "The <strong>staff app</strong> is static files in S3 behind CloudFront, reached through a "
  "signed staff link. There is no login and no app store.",
  "<strong>Offer links</strong> are signed, scoped to one swap and one recipient, single-use, "
  "and expire with the batch window.",
  "<strong>The rota</strong> is read on every eligibility run and written only by "
  "<code>ss-approve</code>. No other function has the credential.",
  "<strong>SMS</strong> goes through SNS to numbers from the staff list only. A phone number in "
  "any request body is never a destination."],
 model_notes=[
  "<strong>There is no model in the request path.</strong> Eligibility is four filters over a "
  "rota and a skills matrix, which is set arithmetic.",
  "<strong>The one optional use</strong> is turning a free-text reason on an override into a "
  "category for the monthly report, and even that is better done with a short pick list.",
  "<strong>This is worth stating</strong> because it is the most obviously AI-shaped problem in "
  "the series &mdash; matching people to shifts &mdash; and it is completely solved by "
  "filtering and sorting.",
  "<strong>If you add one,</strong> add it to the ordering rather than the filtering, and be "
  "able to explain the order to somebody who got fewer hours than a colleague.",
  "<strong>The cost page assumes none</strong>, which is why the read band is nominal."],
 gotchas=[
  "Compute the eligible list once and store it. Recomputing per batch can silently drop somebody "
  "who was already offered the shift.",
  "Move both people's hour totals on approval. Forgetting the giver's makes every subsequent "
  "overtime check wrong in the safe-looking direction.",
  "Store swaps_taken as dates, not a count. A rolling window computed from dates cannot drift "
  "and needs no reset job.",
  "Tell the loser of a race what actually happened. \"Rae got there first\" is honest; \"you were "
  "not selected\" is not what occurred.",
  "Publish the ordering rule. Whatever it is, an unexplained order for who gets extra hours will "
  "be assumed to be favouritism."],
))
