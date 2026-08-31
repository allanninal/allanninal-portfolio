"""Day 104 -- 2026-08-06 -- Address verifier."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "address-verifier"
NAME = "Address verifier"

SPEC = {
 "slug": SLUG, "date": "2026-08-06", "name": NAME,
 "tagline": ("Catches the address that will fail delivery while the customer is still on the "
             "page, suggests the correction rather than rejecting them, and never refuses an "
             "address a person insists is real."),
 "lede": ("A small system that checks a delivery address as it is entered, suggests a correction "
          "where one is obvious, and lets the customer proceed either way. It also re-checks the "
          "addresses already in the database, because most of the failures are already there. "
          "Seven posts on the same system -- one diagram at a time -- with a cost breakdown and "
          "an engineering reference at the end."),
 "keywords": ["address validation", "delivery", "checkout", "data quality", "ecommerce",
              "serverless"],
 "icons": ["map", "check", "truck"],
 "faq": [
  ("What is an address verifier?",
   "A small serverless system that checks an address against a postal reference file as it is "
   "entered, suggests a correction where one is clear, and records what the customer chose. It "
   "never blocks a customer from proceeding."),
  ("Why not just reject bad addresses?",
   "Because the reference file is not complete. New builds, sub-divided properties, farms and "
   "rural addresses are routinely absent, and rejecting them turns a delivery risk into a lost "
   "order. Suggesting beats blocking every time."),
  ("Does it fix addresses automatically?",
   "Only formatting -- capitalisation, a missing postcode space. Anything that changes what the "
   "address means is offered as a suggestion the customer accepts or declines."),
  ("What about the addresses already in the database?",
   "Those are where most failed deliveries come from, and they are checked in the background at "
   "a slow rate. A customer whose stored address no longer verifies is asked at their next "
   "order rather than being contacted out of the blue."),
  ("What does it cost to run?",
   "A few dollars a month plus the reference lookups, which are the only third-party charge. "
   "See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "address-verifier-on-aws",
 "title": "An address verifier on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Checks an address as it is typed, suggests a correction, and never blocks the "
          "customer. Also re-checks the ones already stored. AWS, about $4 a month."),
 "og": ("Rejecting an address the reference file does not know about turns a delivery risk into "
        "a lost order. Suggest, record what they chose, and let them through."),
 "abstract": ("The whole system on one page -- a checker, a suggester and a background sweep -- "
              "built on the observation that the reference file is authoritative and not "
              "complete."),
 "lede": ("A failed delivery costs the carrier charge, the re-send, the customer service "
          "exchange and a decent chance of the order being cancelled, and almost all of them "
          "trace back to an address that was wrong when it was typed. The obvious fix is to "
          "validate at checkout and refuse bad ones, and that turns a delivery problem into an "
          "abandoned basket. This post walks through a small system that suggests rather than "
          "refuses."),
 "tags": ["address validation", "delivery", "checkout", "data quality", "ecommerce", "serverless"],
 "takeaways": [
  "The reference file is authoritative and incomplete. Both halves matter.",
  "Suggest a correction; never block. A refused address is a lost order.",
  "Only formatting is corrected silently. Anything that changes meaning is offered.",
  "Most failed deliveries come from addresses already stored, so those get swept too.",
  "Designed on AWS for about $4 a month plus reference lookups.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "The checkout", "sub": ["an address being typed"], "icon": "browser"},
      {"title": "Reference file", "sub": ["postal data, by lookup"], "icon": "map"},
      {"title": "The customer", "sub": ["accepts, or insists"], "icon": "person"}],
    "inside": [
      {"title": "Checker", "sub": ["normalise, then look up"], "icon": "search"},
      {"title": "Suggester", "sub": ["one correction,", "never a list of ten"], "icon": "filter"},
      {"title": "Recorder", "sub": ["what was offered,", "what was chosen"], "icon": "log"}],
    "edges": [{"from": 0, "to": 0, "label": "an address"},
              {"from": 1, "to": 1, "label": "does it exist?"},
              {"from": 2, "to": 2, "label": "a suggestion, not a block", "up": True}],
    "note": "Nothing here can prevent an order. The worst outcome is a suggestion declined."}),
   "Three things outside the account, three pieces inside it. The note at the bottom is the "
   "commercial constraint that shapes every other decision.",
   "System: an address checked against a reference file, a correction suggested",
   "Three boxes across the top sit outside the AWS account. On the left, The checkout: an address "
   "being typed. In the middle, Reference file: postal data accessed by lookup. On the right, The "
   "customer: who accepts a suggestion or insists on what they typed. Each connects by an arrow "
   "to the AWS account container below. An address flows down into the account. The reference "
   "file answers whether it exists. A suggestion, not a block, goes back out. Inside the AWS "
   "account are three components in a row. On the left, the Checker, which normalises and then "
   "looks up. In the middle, the Suggester, which offers one correction rather than a list of "
   "ten. On the right, the Recorder, which stores what was offered and what was chosen. A note at "
   "the bottom says nothing here can prevent an order, and the worst outcome is a suggestion "
   "declined."),
  ("h3", "Authoritative and incomplete"),
  ("p", "A postal reference file is the best available description of which addresses exist, and "
        "it is not a complete one. New developments take months to appear. A house divided into "
        "two flats may exist as one entry. Farms, rural properties and anything with a name "
        "rather than a number are routinely represented differently from how the occupant writes "
        "them."),
  ("p", "So a lookup that returns nothing means one of two things: the address is wrong, or the "
        "address is fine and the file does not have it. The system genuinely cannot tell which, "
        "and every design decision here follows from taking that seriously rather than treating "
        "a miss as a rejection."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The checker.</strong> Normalises what was typed, looks it up, and classifies the "
   "result into one of four outcomes rather than a yes or a no. Part 2 covers the four and why a "
   "boolean is not enough.",
   "<strong>The suggester.</strong> Where the file has an obvious near-match, offers it as one "
   "suggestion with the difference highlighted. Part 3 is about offering one rather than a list "
   "and about what counts as obvious.",
   "<strong>The recorder.</strong> Stores what was typed, what was offered and what was chosen. "
   "That third field is what makes the whole thing improvable, and it is the one most "
   "implementations omit.",
  ]),
  ("h2", "One address, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Typed", "sub": ["at checkout"], "icon": "browser"},
      {"title": "Normalised", "sub": ["case, spacing, order"], "icon": "filter"},
      {"title": "Looked up", "sub": ["one of four outcomes"], "icon": "map"},
      {"title": "Suggested", "sub": ["or accepted as typed"], "icon": "check"},
      {"title": "Recorded", "sub": ["offered, and chosen"], "icon": "log"}],
    "title": "ONE ADDRESS, END TO END",
    "note": "About 200 milliseconds, and the customer never waits for it."}),
   "The same system as one line. It runs while somebody is still filling in the next field, which "
   "is what makes suggesting viable at all.",
   "One address from typing to recorded choice, in five stages",
   "A horizontal row of five boxes joined by arrows. Typed: at checkout. Normalised: for case, "
   "spacing and field order. Looked up: producing one of four outcomes. Suggested: or accepted as "
   "typed. Recorded: both what was offered and what was chosen. A note says about two hundred "
   "milliseconds, and the customer never waits for it."),
  ("h2", "In plain words"),
  ("p", "Somebody types \"14 chestnut rd, ashford, kent, tn24 8ql\". The checker normalises the "
        "case and the postcode spacing and looks it up. The reference file has 14 Chestnut Road "
        "at that postcode, so the address exists and the only differences are formatting. It is "
        "silently tidied and nothing is shown."),
  ("p", "The next customer types the same street with postcode TN24 8QC. That postcode is a "
        "different street entirely, and the reference file has no number 14 on it. But the "
        "address they typed matches Chestnut Road exactly, and Chestnut Road has one postcode. So "
        "the suggester offers: \"Did you mean TN24 8QL?\" with the change highlighted. They tap "
        "yes and the delivery arrives."),
  ("p", "The third customer types an address in a development finished six weeks ago. The "
        "reference file has never heard of it, and there is no near-match to suggest. The system "
        "shows nothing at all, the order proceeds exactly as it would have, and the address is "
        "recorded as unverified &mdash; which is a fact the warehouse can see if it wants to, and "
        "not an obstacle."),
  ("callout", "Design rules that shaped every decision", [
   "Never block. A refused address is a lost order and the reference file is not complete enough "
   "to justify it.",
   "Correct formatting silently; suggest anything that changes meaning.",
   "One suggestion, not a list. A picker with ten options is a worse experience than typing it "
   "again.",
   "Record what was offered and what was chosen. Declined suggestions are the tuning signal.",
   "Sweep the stored addresses too. Most failed deliveries come from data that predates any "
   "validation.",
   "An unverified address is a flag, not an error. Plenty of real addresses are unverifiable.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Address validation products mostly optimise for the checkout moment and treat the result "
        "as binary, which produces two bad outcomes: real customers at real addresses being "
        "refused, and the far larger pool of already-stored bad addresses going untouched because "
        "the product only runs at entry."),
  ("p", "So this design does the entry check gently and spends equal effort on the background "
        "sweep, because a business that has been trading five years has vastly more bad addresses "
        "in its database than it will collect at checkout this month. Fixing those is where the "
        "failed deliveries actually go away."),
  ("p", "The next four posts walk through each piece: how an address is checked, how a suggestion "
        "is made, what happens to an address that cannot be verified, and how the stored ones get "
        "swept. One diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-an-address-gets-checked",
 "title": "How an address gets checked",
 "nav": "How it is checked",
 "read": 5, "words": 750,
 "desc": ("Normalising before looking up, the four outcomes a check can produce, and why a "
          "boolean answer throws away the useful part."),
 "og": ("A check that returns valid or invalid throws away the distinction that matters: an "
        "address the file does not know is not the same as one that is wrong."),
 "abstract": ("What normalisation has to do before a lookup, the four outcomes a check produces, "
              "why a boolean is not enough, and the caching that keeps this affordable."),
 "lede": ("Most of the work in checking an address happens before the lookup, and most of the "
          "value is in refusing to collapse the answer into a yes or a no."),
 "tags": ["address validation", "normalisation", "postal data", "caching", "APIs", "serverless"],
 "takeaways": [
  "Normalise case, spacing, abbreviations and field order before any lookup.",
  "Four outcomes: exact, formatting-only difference, near-match, and not found.",
  "Not found is not invalid. The distinction is the whole system.",
  "Cache by normalised address; the same addresses recur constantly.",
  "A lookup failure is not a validation failure and must never block anything.",
 ],
 "blocks": [
  ("h2", "Normalise first"),
  ("pre", "typed        14 chestnut rd, ashford, kent, tn248ql\n\n"
          "normalised   line1:     14 Chestnut Road\n"
          "             town:      Ashford\n"
          "             county:    Kent          (dropped for lookup)\n"
          "             postcode:  TN24 8QL\n\n"
          "changes      case, 'rd' expanded, postcode spaced,\n"
          "             county ignored (it is not part of the identity)"),
  ("p", "The county line is worth noting. In many postal systems it is decorative &mdash; the "
        "postcode identifies the delivery point completely &mdash; and including it in a lookup "
        "produces misses when somebody writes a historic county name. Dropping it for the lookup "
        "and preserving it in what is stored is the right handling."),
  ("h2", "Four outcomes"),
  ("fig", ("chain", {
    "entry": {"title": "A normalised address", "sub": ["ready to look up"], "icon": "filter"},
    "steps": [
      {"title": "In the cache?", "sub": ["normalised form"], "icon": "branch",
       "side": {"title": "Lookup cache", "sub": ["addresses recur"], "icon": "database"},
       "exit": {"title": "Reuse", "sub": ["no charge"], "icon": "check", "label": "yes"}},
      {"title": "Look it up", "sub": ["one reference call"], "icon": "map",
       "exit": {"title": "Lookup failed", "sub": ["proceed, mark unchecked"], "icon": "alarm",
                "label": "error"}},
      {"title": "Exact match?", "icon": "branch",
       "exit": {"title": "Verified", "sub": ["tidy formatting silently"], "icon": "check",
                "label": "yes"}},
      {"title": "One close match?", "sub": ["a single obvious candidate"], "icon": "branch",
       "exit": {"title": "Suggest it", "sub": ["with the difference shown"], "icon": "search",
                "label": "yes"}},
      {"title": "Not found", "sub": ["proceed, mark unverified"], "icon": "alarm"}],
    "note": "Two of the five exits proceed silently. None of them stops the customer."}),
   "How a check runs and where it can end. The lookup-failed path is worth building explicitly: a "
   "third-party outage must not become a checkout outage.",
   "How a normalised address is checked against the reference file",
   "A vertical chain of five steps entered by a box labelled A normalised address, ready to look "
   "up. Step one asks whether it is in the cache in its normalised form, since addresses recur; a "
   "hit exits to Reuse with no charge. Step two looks it up with one reference call; an error "
   "exits to Lookup failed, which proceeds and marks the address unchecked. Step three asks "
   "whether it is an exact match; if so it exits to Verified and tidies formatting silently. Step "
   "four asks whether there is one close match, a single obvious candidate; if so it exits to "
   "Suggest it with the difference shown. Step five is Not found, which proceeds and marks the "
   "address unverified. A note says two of the five exits proceed silently and none of them stops "
   "the customer."),
  ("h3", "Not found is not invalid"),
  ("p", "This is the distinction the whole system rests on and the one a boolean destroys. An "
        "address the reference file does not contain might be wrong, and might be a house built "
        "last year, a converted barn, a flat above a shop that has never been separately "
        "registered, or an address written the way the occupant writes it rather than the way the "
        "file records it."),
  ("p", "Storing four outcomes rather than two means the warehouse can treat an unverified "
        "address differently from a verified one without anybody having been refused, and it "
        "means the background sweep can distinguish addresses worth asking about from addresses "
        "that simply are not in the file."),
  ("h3", "Lookup failure is a fifth case"),
  ("p", "The reference service will occasionally be slow or unavailable, and the correct "
        "behaviour is completely uncontroversial: proceed, record the address as unchecked, and "
        "let the sweep pick it up later. A checkout that fails because a validation API timed out "
        "is a self-inflicted outage, and it is a surprisingly common one."),
  ("h2", "Caching"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Normalised key", "sub": ["not the raw string"], "icon": "key"},
      {"title": "Same address again", "sub": ["repeat customers"], "icon": "retry"},
      {"title": "Cache hit", "sub": ["no charge"], "icon": "check"},
      {"title": "Typical hit rate", "sub": ["60-80%"], "icon": "counter"},
      {"title": "Expire slowly", "sub": ["addresses barely change"], "icon": "clock"}],
    "title": "WHY CACHING WORKS SO WELL HERE",
    "note": "The same addresses recur constantly: repeat customers, households, and offices."}),
   "Why an address cache is unusually effective. Addresses recur far more than most lookup keys "
   "and they change almost never.",
   "Why caching address lookups is unusually effective",
   "A horizontal row of five boxes. Normalised key: not the raw string. Same address again: from "
   "repeat customers. Cache hit: with no charge. Typical hit rate: sixty to eighty per cent. "
   "Expire slowly: because addresses barely change. A note says the same addresses recur "
   "constantly, from repeat customers, households and offices."),
  ("p", "Keying the cache on the normalised address rather than the raw string is what produces "
        "the high hit rate: three customers typing the same address three different ways all hit "
        "one cache entry. Keying on the raw string would produce a hit rate near zero and pay for "
        "the same lookup repeatedly."),
  ("p", "A twelve-month expiry is generous and appropriate. Addresses do change &mdash; "
        "renumbering, postcode boundary changes &mdash; but rarely enough that a year-old cached "
        "answer is almost always still right, and the sweep in Part 5 catches the ones that are "
        "not."),
  ("p", "Next: making a suggestion."),
 ],
},
{
 "slug": "how-a-correction-gets-suggested",
 "title": "How a correction gets suggested",
 "nav": "How it suggests",
 "read": 5, "words": 740,
 "desc": ("One suggestion rather than a list, what counts as obvious enough to offer, and why "
          "the difference has to be visible."),
 "og": ("A dropdown of ten near-matches is a worse experience than typing the address again. One "
        "suggestion, with the difference highlighted, or nothing."),
 "abstract": ("Why one suggestion beats a list, the threshold for offering anything at all, why "
              "the specific difference must be visible, and how a declined suggestion is "
              "handled."),
 "lede": ("The suggestion is the only moment this system is visible to a customer, and it has "
          "about two seconds of their attention. Everything here is about spending those two "
          "seconds well, which mostly means offering one thing rather than several."),
 "tags": ["address validation", "checkout", "user experience", "suggestions", "conversion",
          "serverless"],
 "takeaways": [
  "One suggestion or none. A list of candidates is worse than no help at all.",
  "Offer only when there is a single clear candidate; ambiguity means say nothing.",
  "Show the specific difference, not two full addresses to compare.",
  "Declining is one tap and is never questioned.",
  "A declined suggestion is recorded, and repeated declines mean the rule is wrong.",
 ],
 "blocks": [
  ("h2", "One, or none"),
  ("fig", ("chain", {
    "entry": {"title": "A near match exists", "sub": ["from the lookup"], "icon": "search"},
    "steps": [
      {"title": "How many candidates?", "sub": ["from the reference"], "icon": "branch",
       "exit": {"title": "Say nothing", "sub": ["ambiguity helps nobody"], "icon": "stop",
                "label": "two or more"}},
      {"title": "Close enough?", "sub": ["one field, small change"], "icon": "branch",
       "exit": {"title": "Say nothing", "sub": ["too different to be a typo"], "icon": "stop",
                "label": "no"}},
      {"title": "Build the difference", "sub": ["what exactly changes"], "icon": "filter"},
      {"title": "Offer it", "sub": ["one line, two buttons"], "icon": "chat"},
      {"title": "Record both", "sub": ["offered, and the answer"], "icon": "log"}],
    "note": "Two of the three exits are silence. Suggesting badly is worse than not suggesting."}),
   "When a suggestion is offered at all. Both silent exits are common, and choosing silence over "
   "an uncertain suggestion is what keeps the ones that are shown trusted.",
   "How a correction is decided and offered",
   "A vertical chain of five steps entered by a box labelled A near match exists, from the "
   "lookup. Step one asks how many candidates the reference returned; two or more exits to Say "
   "nothing, because ambiguity helps nobody. Step two asks whether it is close enough, meaning "
   "one field with a small change; if not it exits to Say nothing, because it is too different to "
   "be a typo. Step three builds the difference, working out what exactly changes. Step four "
   "offers it as one line with two buttons. Step five records both what was offered and the "
   "answer. A note says two of the three exits are silence, and suggesting badly is worse than "
   "not suggesting."),
  ("h3", "Why not a list"),
  ("p", "The instinct with several candidates is to show them and let the customer pick, and it "
        "produces a measurably worse outcome than showing nothing. A dropdown of ten similar "
        "addresses at checkout is a cognitive task at exactly the wrong moment, and a meaningful "
        "proportion of people will pick the wrong one because it looks close enough."),
  ("p", "A wrong address chosen from a picker is worse than the wrong address they typed, because "
        "it now looks verified. So the rule is one candidate or silence, and silence is the "
        "common case."),
  ("h3", "Close enough"),
  ("table", ["Difference", "Offer it?", "Why"], [
   ["Postcode, one character", "Yes", "The classic typo; the rest of the address confirms it"],
   ["Street type (Road vs Street)", "Yes", "Only if one street exists at that postcode"],
   ["House number, one digit", "No", "14 and 24 are both real houses"],
   ["A missing flat number", "No", "The system does not know which flat"],
   ["Town name", "Yes", "The postcode is authoritative; the town is a label"],
   ["Two fields at once", "No", "That is not a typo, it is a different address"],
  ]),
  ("p", "The house number row is the important one. A one-digit difference looks like the most "
        "obvious typo in the world and is the most dangerous suggestion available, because both "
        "numbers usually exist and both have somebody living in them. Suggesting a different "
        "house number sends a parcel to a real person who did not order it."),
  ("h2", "Showing the difference"),
  ("callout", "What the customer sees", [
   "<strong>Did you mean TN24 8QL?</strong>",
   "You entered TN24 8Q<strong>C</strong> &mdash; we have 14 Chestnut Road as TN24 "
   "8Q<strong>L</strong>.",
   "<strong>Use TN24 8QL</strong> &middot; <em>Keep what I entered</em>",
   "<strong>Nothing else.</strong> No full address comparison, no confidence score, no "
   "explanation of what a reference file is.",
  ]),
  ("p", "Highlighting the single changed character is what makes this a two-second decision. "
        "Showing two complete addresses side by side and asking somebody to spot the difference "
        "is the same information presented as a puzzle, and puzzles at checkout cost orders."),
  ("h3", "Declining is never questioned"),
  ("p", "\"Keep what I entered\" takes one tap, produces no warning, no second confirmation and "
        "no red text. The customer knows where they live and the reference file does not always. "
        "A system that argues with somebody about their own address is both wrong and "
        "infuriating."),
  ("h2", "Declines are the tuning signal"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Suggestion offered", "sub": ["a specific change"], "icon": "chat"},
      {"title": "Declined", "sub": ["by this customer"], "icon": "stop"},
      {"title": "And by others", "sub": ["same suggestion, 6 times"], "icon": "counter"},
      {"title": "The rule is wrong", "sub": ["not the customers"], "icon": "search"},
      {"title": "Stop offering it", "sub": ["for that address"], "icon": "check"}],
    "title": "A SUGGESTION EVERYBODY DECLINES",
    "note": "Six people insisting on the same address is not six mistakes."}),
   "What repeated declines mean. A suggestion nobody accepts is a fact about the reference data "
   "rather than about the customers.",
   "How repeatedly declined suggestions are handled",
   "A horizontal row of five boxes. Suggestion offered: a specific change. Declined: by this "
   "customer. And by others: the same suggestion, six times. The rule is wrong: not the "
   "customers. Stop offering it: for that address. A note says six people insisting on the same "
   "address is not six mistakes."),
  ("p", "This happens most often where the reference file records an address differently from how "
        "residents write it &mdash; a development with a name the file does not use, a building "
        "split into units the file records as one. Six declines is conclusive, and suppressing "
        "that specific suggestion is both correct and something no third-party validator will do "
        "for you."),
  ("p", "Next: the address that cannot be verified at all."),
 ],
},
{
 "slug": "how-an-unverified-address-is-handled",
 "title": "How an unverified address is handled",
 "nav": "How unverified works",
 "read": 5, "words": 730,
 "desc": ("What happens after checkout to an address the file does not know, who sees the flag, "
          "and the one intervention worth making."),
 "og": ("An unverified address is a fact for the warehouse, not an obstacle for the customer. "
        "The intervention that works happens after the order, not during it."),
 "abstract": ("What an unverified flag is for, who sees it and when, the single intervention "
              "worth making after the order, and the addresses that are permanently "
              "unverifiable."),
 "lede": ("Having decided not to block anybody, the question becomes what to do with the "
          "knowledge that an address probably will not deliver. The answer is not at checkout, "
          "and it is not to the customer."),
 "tags": ["address validation", "fulfilment", "delivery", "operations", "customer service",
          "serverless"],
 "takeaways": [
  "The flag travels with the order to fulfilment, not to the customer at checkout.",
  "One intervention: a short message before dispatch, only for high-value or fragile orders.",
  "The carrier's own validation is a second opinion worth capturing.",
  "Some addresses are permanently unverifiable and should be marked so, once.",
  "A delivery that succeeds to an unverified address verifies it better than any file.",
 ],
 "blocks": [
  ("h2", "Who sees it, and when"),
  ("fig", ("chain", {
    "entry": {"title": "An unverified address", "sub": ["order placed"], "icon": "alarm"},
    "steps": [
      {"title": "Tell the customer now?", "sub": ["at checkout"], "icon": "branch",
       "exit": {"title": "No", "sub": ["it costs orders and", "helps nobody"], "icon": "stop",
                "label": "never"}},
      {"title": "Flag on the order", "sub": ["visible in fulfilment"], "icon": "log"},
      {"title": "High value or fragile?", "sub": ["from the order"], "icon": "branch",
       "exit": {"title": "One message", "sub": ["before dispatch, friendly"], "icon": "email",
                "label": "yes"}},
      {"title": "Dispatch normally", "sub": ["most orders"], "icon": "truck"},
      {"title": "Delivered?", "sub": ["the real verification"], "icon": "check",
       "exit": {"title": "Mark verified by delivery", "sub": ["better than the file"],
                "icon": "map", "label": "yes"}}],
    "note": "The last step is the strongest signal available and almost nobody records it."}),
   "What happens to an unverified address after checkout. The final step is the one worth "
   "building: a successful delivery is better evidence than any reference file.",
   "How an unverified address is handled after an order is placed",
   "A vertical chain of five steps entered by a box labelled An unverified address, with an order "
   "placed. Step one asks whether to tell the customer now, at checkout; the answer is never, "
   "because it costs orders and helps nobody. Step two flags the order so it is visible in "
   "fulfilment. Step three asks whether the order is high value or fragile; if so it exits to One "
   "message sent before dispatch, phrased in a friendly way. Step four dispatches normally, which "
   "is most orders. Step five asks whether it was delivered, which is the real verification; a "
   "successful delivery exits to Mark verified by delivery, which is better than the file. A note "
   "says the last step is the strongest signal available and almost nobody records it."),
  ("h3", "Never at checkout"),
  ("p", "Telling somebody at checkout that their address could not be verified achieves two "
        "things and both are bad. It makes a proportion of people abandon, because a warning "
        "during payment reads as something being wrong. And it gives them no useful action, "
        "because they already believe their address is correct and it usually is."),
  ("h3", "The one intervention"),
  ("p", "For a high-value or fragile order to an unverified address, one short message before "
        "dispatch is worth it, and the wording matters enormously. Not \"your address could not "
        "be validated\" but \"we want to make sure this arrives &mdash; is this right?\" with the "
        "address shown as they typed it and one button to confirm."),
  ("p", "That converts at a high rate because it reads as care rather than doubt, and it catches "
        "the genuine errors in exactly the population where a failed delivery is most expensive. "
        "For an ordinary low-value order it is not worth the message."),
  ("h2", "Permanently unverifiable"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Not in the file", "sub": ["checked twice"], "icon": "search"},
      {"title": "Delivered fine", "sub": ["twice"], "icon": "truck"},
      {"title": "Conclusion", "sub": ["the file is wrong"], "icon": "check"},
      {"title": "Mark permanent", "sub": ["stop re-checking"], "icon": "lock"},
      {"title": "Never asked again", "sub": ["about this address"], "icon": "retry"}],
    "title": "AN ADDRESS THE FILE WILL NEVER HAVE",
    "note": "Two successful deliveries settle it. Continuing to flag it is just noise."}),
   "How an address earns permanent status. Two successful deliveries are conclusive evidence "
   "against the reference file, and continuing to treat it as suspect wastes attention.",
   "How a permanently unverifiable address is settled",
   "A horizontal row of five boxes. Not in the file: checked twice. Delivered fine: twice. "
   "Conclusion: the file is wrong. Mark permanent: and stop re-checking. Never asked again: about "
   "this address. A note says two successful deliveries settle it and continuing to flag it is "
   "just noise."),
  ("p", "This matters more than it sounds for businesses with rural or agricultural customers, "
        "where a substantial minority of addresses will never appear in a reference file in the "
        "form the occupant uses. Without a permanent marker those customers are flagged on every "
        "single order forever, and the flag stops meaning anything."),
  ("h3", "The carrier's opinion"),
  ("p", "Most carriers run their own address validation at booking and return a result, and it is "
        "a genuinely useful second opinion because their data and the postal reference file are "
        "not identical. Capturing it costs nothing beyond reading a field that is already in the "
        "response."),
  ("p", "The interesting case is disagreement: the reference file has no record and the carrier "
        "accepts it happily, or the reverse. Recording both and comparing them over a few hundred "
        "orders tells you which source to trust for your particular customer base, which is a "
        "much better answer than picking one on principle."),
  ("p", "Next: the addresses already in the database."),
 ],
},
{
 "slug": "how-stored-addresses-get-swept",
 "title": "How stored addresses get swept",
 "nav": "How stored ones sweep",
 "read": 5, "words": 730,
 "desc": ("Where most failed deliveries actually come from, sweeping without contacting anybody, "
          "and the numbers that say whether it is working."),
 "og": ("A business trading five years has far more bad addresses in its database than it will "
        "collect this month. That is where the failed deliveries are."),
 "abstract": ("Why the stored addresses matter more than the ones being typed, how to sweep them "
              "without contacting anybody out of the blue, and the numbers worth watching."),
 "lede": ("Validation at checkout only ever improves addresses collected from today onwards, and "
          "a business that has been trading for years has a database full of addresses collected "
          "before anybody thought about it. That is where the failed deliveries are."),
 "tags": ["address validation", "data quality", "backfill", "delivery", "reporting", "serverless"],
 "takeaways": [
  "Sweep the existing database slowly in the background; that is where the failures are.",
  "Never contact a customer about a stored address out of the blue.",
  "Ask at the next natural moment: their next order, at the address step.",
  "Sweep by likelihood of use, not alphabetically. Recent customers first.",
  "The number that matters is failed deliveries, not addresses verified.",
 ],
 "blocks": [
  ("h2", "Where the failures are"),
  ("fig", ("chain", {
    "entry": {"title": "The stored database", "sub": ["years of addresses"], "icon": "database"},
    "steps": [
      {"title": "Order by likely use", "sub": ["recent customers first"], "icon": "filter"},
      {"title": "Check at a slow rate", "sub": ["a few hundred a day"], "icon": "clock",
       "side": {"title": "Cache", "sub": ["most are hits"], "icon": "check"}},
      {"title": "Verified?", "icon": "branch",
       "exit": {"title": "Record and move on", "sub": ["most of them"], "icon": "log",
                "label": "yes"}},
      {"title": "Contact them?", "sub": ["out of the blue"], "icon": "branch",
       "exit": {"title": "No", "sub": ["wait for a natural moment"], "icon": "stop",
                "label": "never"}},
      {"title": "Flag for next time", "sub": ["asked at their next order"], "icon": "bell"}],
    "note": "A slow rate is deliberate: this is a backfill, not an incident."}),
   "How the existing database is swept. The deliberate slowness and the refusal to contact "
   "anybody are what make this safe to run against a customer database.",
   "How stored addresses are swept in the background",
   "A vertical chain of five steps entered by a box labelled The stored database, holding years "
   "of addresses. Step one orders by likely use, putting recent customers first. Step two checks "
   "at a slow rate of a few hundred a day, with most hitting the cache. Step three asks whether "
   "the address verified; most do, and those exit to Record and move on. Step four asks whether "
   "to contact the customer out of the blue; the answer is never, and it exits to wait for a "
   "natural moment. Step five flags the address to be asked about at their next order. A note "
   "says the slow rate is deliberate, because this is a backfill rather than an incident."),
  ("h3", "Never contact out of the blue"),
  ("p", "The tempting action on discovering four hundred unverified stored addresses is to email "
        "those customers and ask them to confirm. It is a bad idea for reasons that are obvious "
        "in hindsight: most of the addresses are fine, the email reads as either a phishing "
        "attempt or a sign of disorganisation, and the response rate on a request with no benefit "
        "to the recipient is very low."),
  ("p", "Asking at the next order costs nothing, arrives at a moment when the customer is already "
        "thinking about where the parcel goes, and converts at a completely different rate. The "
        "cost is patience: a customer who does not order again is never asked, which is fine, "
        "because they were never going to receive a delivery either."),
  ("h3", "Order by likely use"),
  ("p", "Sweeping alphabetically or by identifier spends the same effort on a customer who "
        "ordered last week and one who ordered once in 2019. Ordering by recency of activity "
        "means the addresses most likely to be used next are checked first, which front-loads "
        "essentially all of the value."),
  ("p", "It also matters for the ask: a flag on a recent customer's address will be acted on "
        "within weeks, and one on a dormant customer may never be. Doing the recent ones first "
        "means the flags that get resolved are created first."),
  ("h2", "The numbers"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Addresses", "sub": ["11,400 stored"], "icon": "database"},
      {"title": "Swept", "sub": ["9,100 so far"], "icon": "search"},
      {"title": "Unverified", "sub": ["640"], "icon": "alarm"},
      {"title": "Asked at reorder", "sub": ["81, of which 62 fixed"], "icon": "person"},
      {"title": "Failed deliveries", "sub": ["14 -> 4 a month"], "icon": "truck"}],
    "title": "SIX MONTHS OF SWEEPING",
    "note": "The last number is the only one that matters. The others explain it."}),
   "Six months of sweeping in five numbers. Only the last one is an outcome; the rest are "
   "activity, and reporting activity as achievement is the standard failure of a data quality "
   "project.",
   "Six months of address sweeping summarised in five numbers",
   "A horizontal row of five boxes. Addresses: eleven thousand four hundred stored. Swept: nine "
   "thousand one hundred so far. Unverified: six hundred and forty. Asked at reorder: eighty-one, "
   "of which sixty-two were fixed. Failed deliveries: down from fourteen to four a month. A note "
   "says the last number is the only one that matters and the others explain it."),
  ("p", "Reporting the failed delivery count rather than the verification count is the discipline "
        "that keeps this honest. Nine thousand addresses verified is activity; ten fewer failed "
        "deliveries a month is an outcome, and it is what justifies the reference lookups on the "
        "bill."),
  ("h3", "When to stop"),
  ("p", "A sweep is finite. Once the database has been through once, the ongoing work is small: "
        "new addresses are checked at entry, changed addresses are re-checked, and everything "
        "else is already known. Running the full sweep repeatedly costs lookups for almost no "
        "additional finding."),
  ("p", "The sensible ongoing cadence is to re-check an address when it is about to be used for a "
        "delivery and its last check is more than a year old, which is a small number per day and "
        "catches the genuine changes &mdash; renumbering, postcode boundary moves &mdash; without "
        "re-sweeping eleven thousand records every quarter."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="lookup",
 volumes=[(2000, "2,000 lookups"), (8000, "8,000 lookups"), (30000, "30,000 lookups")],
 read_each=0.0,
 msgs_each=0.02,
 extra=[("ref", "Reference lookups &mdash; cache misses only", "#4A90D9", 0.0040, 0.0)],
 lede=("The AWS side of this is almost free and the reference lookups are not, which makes the "
       "cache the most important cost decision in the design. Eight thousand lookups a month is "
       "a busy small e-commerce business including its background sweep. Here is where each cent "
       "goes."),
 takeaway_extra=("The reference lookups are the whole bill, and a 70% cache hit rate cuts them "
                 "by 70%."),
 risks=[
  "<strong>Caching on the raw string.</strong> The single most expensive mistake available here: "
  "three spellings of one address become three paid lookups, and the hit rate collapses from "
  "seventy per cent to near zero.",
  "<strong>Sweeping the whole database repeatedly.</strong> A full re-sweep every quarter is "
  "eleven thousand lookups for almost no new finding. Re-check on use, not on a schedule.",
  "<strong>Log retention left at never.</strong> Address lookups log per request and the volume "
  "is high enough that unbounded retention becomes the second-largest line.",
 ],
 per_unit_note=("Reference lookups are charged per query by whichever provider you use and only "
                "bill on a cache miss. The AWS compute is a few cents; the provider is the bill."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="av",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the latency budget, and the failure behaviour that matters most."),
 outside=[
  {"title": "Checkout", "sub": ["a Function URL call"], "icon": "browser"},
  {"title": "Reference API", "sub": ["postal data provider"], "icon": "map"},
  {"title": "Order system", "sub": ["receives the flag"], "icon": "cart"}],
 inside=[
  {"title": "Function URL + EventBridge", "sub": ["live check,", "nightly sweep"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["check, sweep, report"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["cache, addresses"], "icon": "database"}],
 note="us-east-1. One account. A lookup failure never blocks a checkout, by design and by test.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Checkout, which calls a Function URL. The "
  "Reference API from a postal data provider. And the Order system, which receives the "
  "verification flag. Inside the account, three groups. A Function URL for live checks and "
  "EventBridge for the nightly sweep. Three Lambda functions named check, sweep and report. And "
  "two DynamoDB tables named cache and addresses. A note gives the region as us-east-1, one "
  "account, and states that a lookup failure never blocks a checkout, by design and by test."),
 functions=[
  ["<code>av-check</code>", "Function URL",
   "Normalise, cache lookup, reference call, classify; hard 800ms budget",
   "5s / 512&nbsp;MB"],
  ["<code>av-sweep</code>", "EventBridge nightly",
   "Re-checks stored addresses by recency, at a capped rate", "300s / 512&nbsp;MB"],
  ["<code>av-report</code>", "EventBridge monthly",
   "Decline patterns, failed delivery correlation, the summary", "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>av-check-role</code>",
   "<code>dynamodb:GetItem</code>/<code>PutItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "The cache table; the reference API credential only"],
  ["<code>av-sweep-role</code>", "<code>dynamodb:Query</code>/<code>UpdateItem</code>",
   "Cache and addresses"],
  ["<code>av-report-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "Addresses, read; one verified identity"]],
 tables=[
  ("Table: cache",
   "PK   normalised        S   14 chestnut road|ashford|tn24 8ql\n"
   "     outcome           S   verified | formatting | near_match | not_found\n"
   "     canonical         M   the reference file's own form, if matched\n"
   "     suggestion        M   the near match, if there was exactly one\n"
   "     looked_up_at      S   2026-08-06T10:14:00Z\n"
   "     ttl               N   epoch, +12 months\n\n"
   "The key is the NORMALISED address, not what was typed. Keying on the raw\n"
   "string drops the hit rate from about 70% to near zero and pays for the\n"
   "same lookup repeatedly."),
  ("Table: addresses",
   "PK   address_id        S   the order or customer address identifier\n"
   "     typed             M   exactly as the customer entered it\n"
   "     stored            M   what was saved, after any accepted suggestion\n"
   "     outcome           S   verified | formatting | near_match | not_found | unchecked\n"
   "     suggestion_shown  M   what was offered, or null\n"
   "     suggestion_taken  BOOL or null\n"
   "     carrier_verdict   S   what the carrier said at booking, if known\n"
   "     delivered_ok      N   how many successful deliveries here\n"
   "     permanent         BOOL true once delivered twice while unverified\n"
   "     last_checked      S   drives the re-check-on-use rule\n\n"
   "`suggestion_shown` with `suggestion_taken` false, repeated across customers,\n"
   "is what identifies a suggestion rule that is wrong about a real address.")],
 inbound=[
  "<strong>The checkout calls a Function URL</strong> with an 800&nbsp;ms client-side timeout. "
  "If it does not answer in time the checkout proceeds and the address is recorded as unchecked.",
  "<strong>That timeout behaviour is a test</strong>, not a comment. The single most important "
  "property of this system is that it cannot break a checkout, and the way to be sure is to "
  "assert it.",
  "<strong>The reference credential</strong> lives in its own secret and is read only by "
  "<code>av-check</code>. The sweep uses the same function rather than holding its own copy.",
  "<strong>The sweep is rate-capped</strong> per hour, both to control provider spend and "
  "because a backfill hammering a third-party API is a good way to be rate limited during a busy "
  "checkout hour."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Normalisation is rules, lookup is an API, "
  "and the suggestion logic is a comparison.",
  "<strong>The tempting use</strong> is parsing a free-text address into fields, which a model "
  "does well &mdash; and most reference APIs already offer a parsing endpoint that is cheaper "
  "and deterministic.",
  "<strong>Determinism matters here</strong> because the same address must produce the same "
  "normalised cache key every time, and a model that phrases one differently on Tuesday breaks "
  "the cache.",
  "<strong>If you do parse with a model</strong>, cache the parse by input string so it is "
  "called once per distinct input, ever.",
  "<strong>The cost page assumes none</strong>, which is why reference lookups are the only "
  "variable band."],
 gotchas=[
  "Cache on the normalised address, never the raw string. It is the difference between a 70% hit "
  "rate and a 5% one.",
  "Never suggest a different house number. Both numbers usually exist, and a suggestion that "
  "sends a parcel to a real stranger is worse than the original typo.",
  "Never block, and test that you cannot. A validation timeout that fails a checkout is a "
  "self-inflicted outage.",
  "Record what was offered and what was chosen. Repeated declines of the same suggestion mean "
  "the reference data is wrong about a real address.",
  "Report failed deliveries, not addresses verified. One is an outcome and the other is "
  "activity."],
))
