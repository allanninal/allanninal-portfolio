"""Day 132 -- 2026-09-03 -- Lost property matcher."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "lost-property-matcher"
NAME = "Lost property matcher"

SPEC = {
 "slug": SLUG, "date": "2026-09-03", "name": NAME,
 "tagline": ("Logs a found item in ninety seconds, matches a vague claim against it without ever "
             "showing the claimant what you have, gets it back to the right person, and disposes "
             "of the rest on a policy instead of when the cupboard overflows."),
 "lede": ("A small system for anywhere the public leaves things behind: a photograph and three "
          "fields at the moment of finding, structural matching of claims that arrive days later "
          "and describe the item badly, an ownership test that does not hand the answer to the "
          "claimant, and a retention policy that ends in a recorded outcome rather than a bin "
          "bag. Seven posts on the same system, one diagram at a time, with a cost breakdown and "
          "an engineering reference at the end."),
 "keywords": ["lost property", "hospitality", "venue operations", "matching", "retention",
              "serverless"],
 "icons": ["box", "search", "person"],
 "faq": [
  ("What is a lost property matcher?",
   "A small serverless system that records found items at the moment they are found, matches "
   "incoming claims against them on structure rather than description, and drives each item to a "
   "recorded outcome: returned, disposed of, or donated."),
  ("Why not just let claimants look through photos?",
   "Because it removes the only ownership test you have. Once somebody has seen the item, they "
   "can describe it perfectly, and you have no way of telling an owner from an opportunist."),
  ("How long should items be kept?",
   "By category, not uniformly: perishables the same day, ordinary items around a month, "
   "valuables and identity documents considerably longer with a recorded chain of custody. The "
   "specific periods are a policy decision; having them written down is the part that matters."),
  ("What about a found phone or laptop?",
   "Log it, do not open it, and charge it only if that is how you will reach the owner through a "
   "lock screen message. The contents are somebody else's data and the safest position is that "
   "nobody in your business has looked at them."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "lost-property-matcher-on-aws",
 "title": "A lost property matcher on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Ninety-second logging, structural matching, an ownership test, and a retention policy "
          "with an ending. AWS, about $2 a month."),
 "og": ("The cupboard is not a system. It is a place where things go until somebody decides "
        "nobody is coming back for them, which nobody ever decides."),
 "abstract": ("The whole system on one page -- logging, matching, return, disposal -- and why "
              "the ninety seconds at the start determines whether any of the rest works."),
 "lede": ("There is a cupboard behind reception with four umbrellas, a child's coat, two phone "
          "chargers, a set of car keys and a laptop. Nobody knows when the laptop arrived. "
          "Somebody rang about a laptop in March and was told there was nothing. It was in the "
          "cupboard."),
 "tags": ["lost property", "hospitality", "venue operations", "customer service", "retention",
          "serverless"],
 "takeaways": [
  "If logging takes more than ninety seconds it does not happen.",
  "Match on structure -- where, when, category -- not on adjectives.",
  "Never show the item first. The description is your only ownership test.",
  "Every item ends in a recorded outcome, including the ones nobody claims.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Whoever finds it", "sub": ["mid-shift, hands full"], "icon": "person"},
      {"title": "Whoever lost it", "sub": ["ringing on Thursday", "about Saturday"], "icon": "phone"},
      {"title": "The cupboard", "sub": ["and the day it", "has to be emptied"], "icon": "box"}],
    "inside": [
      {"title": "The item record", "sub": ["photo, place, time,", "category"], "icon": "image"},
      {"title": "Claim and match", "sub": ["structure first,", "then a person"], "icon": "search"},
      {"title": "Outcome", "sub": ["returned, donated,", "disposed of"], "icon": "check"}],
    "edges": [{"from": 0, "to": 0, "label": "90 seconds, on a phone"},
              {"from": 1, "to": 1, "label": "a vague description"},
              {"from": 2, "to": 2, "label": "an ending, on a date", "up": True}],
    "note": "The left-hand arrow is the whole system. Everything downstream is worthless if that "
            "step is skipped."}),
   "Three things outside the account, three pieces inside it. The finder is the only user who "
   "cannot be asked for more effort.",
   "System: found items logged, claims matched, outcomes recorded",
   "Three boxes across the top sit outside the AWS account. On the left, Whoever finds it, "
   "mid-shift with their hands full. In the middle, Whoever lost it, ringing on Thursday about "
   "Saturday. On the right, The cupboard, and the day it has to be emptied. Each connects by an "
   "arrow to the AWS account container below. Logging takes ninety seconds on a phone. A vague "
   "description comes in. An ending on a date goes back out. Inside the AWS account are three "
   "components in a row. On the left, The item record: photo, place, time and category. In the "
   "middle, Claim and match, structure first and then a person. On the right, Outcome: returned, "
   "donated or disposed of. A note says the left-hand arrow is the whole system and everything "
   "downstream is worthless if that step is skipped."),
  ("h3", "Why the cupboard fails"),
  ("p", "A cupboard has no index, no dates and no memory. Its only query is a person opening the "
        "door and looking, which works for umbrellas and fails completely for the thing somebody "
        "actually cares about, because that item arrived four weeks ago and is at the back."),
  ("p", "It also has no ending. Nothing in a cupboard is ever disposed of on a date; it is "
        "disposed of when the cupboard is full, which means the valuable items that should be "
        "kept longest are thrown out alongside the umbrellas at exactly the wrong moment."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The item record.</strong> One photograph and three fields, captured where the item "
   "was found. Part 2.",
   "<strong>Claim and match.</strong> Structural matching against a description that will be "
   "wrong in at least one detail. Part 3.",
   "<strong>Return and disposal.</strong> Proving ownership, getting it back, and ending the "
   "items nobody comes for. Parts 4 and 5.",
  ]),
  ("h2", "One jacket, five weeks"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Found Saturday", "sub": ["bar area, 23:40"], "icon": "box"},
      {"title": "Logged in 80s", "sub": ["photo and three taps"], "icon": "image"},
      {"title": "Claimed Thursday", "sub": ["'a dark coat,", "maybe navy'"], "icon": "phone"},
      {"title": "Matched", "sub": ["place and night,", "not the colour"], "icon": "search"},
      {"title": "Returned Friday", "sub": ["after one question"], "icon": "check"}],
    "title": "ONE JACKET, FIVE DAYS",
    "note": "The colour was wrong in the claim and it did not matter. Almost nobody remembers a "
            "colour correctly."}),
   "The same system as one line. The match is made on where and when, which the claimant "
   "remembers, rather than on what, which they do not.",
   "One found jacket from discovery through to being returned",
   "A horizontal row of five boxes joined by arrows. Found Saturday, bar area, twenty-three "
   "forty. Logged in eighty seconds with a photo and three taps. Claimed Thursday, described as a "
   "dark coat, maybe navy. Matched on place and night rather than the colour. Returned Friday "
   "after one question. A note says the colour was wrong in the claim and it did not matter, "
   "because almost nobody remembers a colour correctly."),
  ("h2", "In plain words"),
  ("p", "Somebody clearing tables finds a jacket. They photograph it on their phone, tap a "
        "category, tap where they are, and put it in the cupboard with a printed label. The whole "
        "interaction is under ninety seconds and it is the only part of this system that has a "
        "hard time budget."),
  ("p", "Five days later somebody rings, or fills in a form, describing a dark coat they think "
        "they left in the bar on Saturday. They are wrong about the colour and roughly right "
        "about everything else, which is the normal case."),
  ("p", "The match is made on the parts of the claim that are reliable -- roughly when, roughly "
        "where, what kind of thing it is -- and produces a short list for a human. Nobody is "
        "shown a photograph, because the description is the only ownership test that exists and "
        "showing the item destroys it."),
  ("p", "One question settles it: something about the item that an owner knows and a chancer "
        "does not. Then it is collected or posted, and the record closes with who took it and "
        "when. Everything unclaimed reaches its retention date and gets an outcome, which is a "
        "line in a record rather than a bin bag."),
  ("callout", "Design rules that shaped every decision", [
   "Ninety seconds to log, on a phone, one-handed, or it will not happen.",
   "Structure over adjectives: where and when beat colour and brand every time.",
   "Never show the item to the claimant before they have described it.",
   "One ownership question, asked openly, decided by a person.",
   "Retention is by category, on a date, and it ends in a recorded outcome.",
   "Do not look inside anything. A found device is somebody else's data.",
  ]),
  ("h2", "What it does not do"),
  ("p", "It does not decide who owns anything. Every actual return is authorised by a person, "
        "because the cost of being wrong is handing a stranger somebody's passport and there is "
        "no confidence score that justifies automating that."),
  ("p", "It does not identify items from photographs, either. A photograph is for the person "
        "confirming a match at the counter, not for a classifier, and building this around image "
        "recognition adds cost and failure modes to a problem that is mostly about dates and "
        "places."),
  ("p", "The next four posts walk through each piece: how a found item gets logged, how a claim "
        "gets matched to it, how it gets back to its owner, and what happens to everything nobody "
        "comes for. One diagram per post, a cost breakdown, and an engineering reference at the "
        "end."),
 ],
},
{
 "slug": "how-a-found-item-gets-logged",
 "title": "How a found item gets logged in ninety seconds",
 "nav": "Logging the item",
 "read": 5, "words": 740,
 "desc": ("The time budget that decides everything, three fields instead of eleven, and why the "
          "category list is short on purpose."),
 "og": ("A form with eleven fields does not get a careful answer. It gets an item left on the "
        "back counter for somebody else to deal with."),
 "abstract": ("Why the logging step has a hard time budget, the three fields that matter, "
              "controlled categories instead of free text, and what to do about high-value finds."),
 "lede": ("Everything downstream in this system depends on a record existing, and the record is "
          "created by somebody who is mid-shift, holding a tray, and has no interest in your "
          "software."),
 "tags": ["lost property", "operations", "mobile capture", "forms", "hospitality", "serverless"],
 "takeaways": [
  "Three fields and a photo. Everything else is derived or optional.",
  "Where and when are the fields that make matching work.",
  "Categories come from a short list; free text does not match.",
  "Print a label at the point of logging, or the record and the item separate.",
  "Valuables take a different path, immediately, with a second person.",
 ],
 "blocks": [
  ("h2", "The time budget"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "3 fields + photo", "parts": [("n", 94)]},
      {"label": "6 fields", "parts": [("n", 71)]},
      {"label": "11 fields + form", "parts": [("n", 34)]}],
    "series": [("n", "Items actually logged, %", "#01A88D")],
    "unit": "",
    "note": "The unlogged items do not vanish. They go in the cupboard with no record, which is "
            "worse than not having the system."}),
   "What each additional field costs in compliance. This is the only design decision in the whole "
   "system that changes the outcome by a factor of three.",
   "Proportion of found items logged against the size of the logging form",
   "A bar chart with three bars showing the percentage of items actually logged. Three fields "
   "plus a photo: ninety-four percent. Six fields: seventy-one percent. Eleven fields plus a "
   "form: thirty-four percent. A note says the unlogged items do not vanish; they go in the "
   "cupboard with no record, which is worse than not having the system."),
  ("p", "This is not a claim about laziness. Somebody clearing a function room at midnight has a "
        "job that is not this, and a system that costs them four minutes per umbrella is a system "
        "they will route around by putting the umbrella on a shelf."),
  ("h3", "The three fields"),
  ("ul", [
   "<strong>Category</strong>, from a list of about twelve. Not a description.",
   "<strong>Where</strong>, from your own zone list -- bar, function room, car park, room 214. "
   "Tapped, never typed.",
   "<strong>When</strong>, which is now, defaulted, and correctable to 'earlier today' in one "
   "tap.",
   "<strong>And a photograph</strong>, which is not a field so much as the whole record. It "
   "carries the colour, the brand, the condition and the size without anybody describing any of "
   "them.",
  ]),
  ("h2", "Why the category list is short"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Free text", "sub": ["'blk northface", "jkt L'"], "icon": "form",
       "label": "unsearchable"},
      {"title": "A long taxonomy", "sub": ["four levels,", "eighty leaves"], "icon": "branch",
       "label": "unused"},
      {"title": "Twelve categories", "sub": ["one tap"], "icon": "filter", "label": "works"}],
    "target": {"title": "Matchable records", "sub": ["consistent across", "every finder"],
               "icon": "database",
               "then": {"title": "The photo carries", "sub": ["everything else"], "icon": "image"}},
    "note": "The detail lives in the photograph. The category only has to narrow the search."}),
   "Three ways of describing a found item. The short list wins because it is the only one that "
   "produces the same word from two different people looking at the same jacket.",
   "Three approaches to categorising found property",
   "Three boxes stacked on the left. Free text, such as an abbreviated black jacket entry, "
   "labelled unsearchable. A long taxonomy with four levels and eighty leaves, labelled unused. "
   "And Twelve categories, one tap, labelled works. All three converge on Matchable records, "
   "consistent across every finder, which leads down to The photo carries everything else. A note "
   "says the detail lives in the photograph and the category only has to narrow the search."),
  ("h3", "Zones, not addresses"),
  ("p", "Where an item was found is the strongest matching signal you have, and it only works if "
        "the same place is recorded the same way every time. A list of zones specific to your "
        "site -- the ones staff already say out loud -- beats a text box or a map pin."),
  ("p", "The zone list is also the thing that makes a vague claim workable. Somebody who says "
        "'the upstairs bar, I think' has just eliminated ninety percent of your inventory without "
        "knowing anything about their own item."),
  ("h2", "The label is not optional"),
  ("p", "A record without a physical label on the item is half a system. Somebody will find the "
        "jacket in the cupboard and have no way of knowing which of four jacket records it "
        "belongs to, and at that point the photograph is doing work it should not have to."),
  ("p", "A short code on a sticker, printed or handwritten from the screen, is enough. It is the "
        "join between the thing and the record, and it costs three seconds at the moment when "
        "everything else is already open."),
  ("h2", "Valuables leave the path"),
  ("callout", "What gets treated differently, immediately", [
   "<strong>Cash</strong> -- counted by two people, recorded to the note, and stored separately. "
   "The record says who counted it.",
   "<strong>Identity documents</strong> -- passports, driving licences, immigration papers. Often "
   "returned to the issuing body rather than held, and never posted casually.",
   "<strong>Bank cards</strong> -- destroyed or returned to the bank; the guidance is on the card "
   "itself and it is not 'hold for a month'.",
   "<strong>Devices</strong> -- logged, not opened, and stored where they cannot be casually "
   "picked up. A lock screen message is the only acceptable way to look for an owner.",
   "<strong>Medication, and anything hazardous</strong> -- not held at all. There is a disposal "
   "route and it is not the cupboard.",
  ]),
  ("p", "These are policy decisions and they vary by jurisdiction and by what kind of business "
        "you are. The system's contribution is small and specific: the category picked at logging "
        "time sends the item down the right path immediately, rather than after somebody notices "
        "in three weeks."),
  ("p", "Next: matching a claim to it."),
 ],
},
{
 "slug": "how-a-claim-gets-matched-to-an-item",
 "title": "How a claim gets matched to an item",
 "nav": "Matching a claim",
 "read": 6, "words": 780,
 "desc": ("Why descriptions are unreliable, matching on the facts people do remember, and the "
          "shortlist that goes to a person."),
 "og": ("People remember where they were and roughly when. They do not remember what colour their "
        "own umbrella is, and they will tell you confidently anyway."),
 "abstract": ("Which parts of a claim are reliable, structural matching on zone and time, why the "
              "model normalises rather than decides, and what the shortlist is for."),
 "lede": ("A claim is a description of something the claimant is not looking at, recalled several "
          "days later, and it will be wrong in at least one detail that feels certain to them."),
 "tags": ["lost property", "matching", "search", "customer service", "operations", "serverless"],
 "takeaways": [
  "Zone and date are reliable. Colour, brand and size are not.",
  "Match structurally first; text is a tie-breaker, never the filter.",
  "The model normalises the claim into fields. It does not decide.",
  "Return a shortlist to a person, never a single confident answer.",
  "No match today is a subscription, not a rejection.",
 ],
 "blocks": [
  ("h2", "What a claimant actually knows"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Where", "parts": [("n", 88)]},
      {"label": "Which day", "parts": [("n", 79)]},
      {"label": "Category", "parts": [("n", 92)]},
      {"label": "Colour", "parts": [("n", 54)]},
      {"label": "Brand", "parts": [("n", 31)]}],
    "series": [("n", "Recalled correctly, %", "#4A90D9")],
    "unit": "",
    "note": "The three tall bars are the entire matching strategy. The two short ones are what "
            "most systems search on."}),
   "How reliable each part of a claim is. Building the match on the left-hand bars is the "
   "difference between finding things and telling people you have nothing.",
   "Reliability of different details in a lost property claim",
   "A bar chart with five bars showing how often each detail is recalled correctly. Where: "
   "eighty-eight percent. Which day: seventy-nine percent. Category: ninety-two percent. Colour: "
   "fifty-four percent. Brand: thirty-one percent. A note says the three tall bars are the entire "
   "matching strategy and the two short ones are what most systems search on."),
  ("p", "Colour is the striking one. Roughly half of people describe their own coat as a colour "
        "it is not, which is unsurprising the moment you consider how rarely anybody looks at "
        "their own coat, and completely fatal to a system that filters on it."),
  ("h3", "Structure first, text last"),
  ("p", "The match runs on the fields that survive memory: a zone or its neighbours, a date "
        "window of a day either side, and a category. That produces a handful of candidates from "
        "a cupboard of two hundred items."),
  ("p", "Free text then ranks that handful rather than filtering it. A claim mentioning a "
        "particular badge or a torn pocket promotes the item that has one, but the absence of a "
        "match on wording never removes a candidate, because the claimant's wording was never "
        "reliable in the first place."),
  ("h2", "Where the model earns its place"),
  ("fig", ("chain", {
    "entry": {"title": "A claim, however", "sub": ["it arrives: form,", "email, phone note"],
              "icon": "inbox"},
    "steps": [
      {"title": "Normalise", "sub": ["free text into", "the same fields"], "icon": "form",
       "side": {"title": "One model call", "sub": ["extraction only"], "icon": "model"}},
      {"title": "Structural query", "sub": ["zone, date window,", "category"], "icon": "search"},
      {"title": "Rank on detail", "sub": ["distinctive words,", "not colour"], "icon": "filter"},
      {"title": "Shortlist to a person", "sub": ["three to five items"], "icon": "person"}],
    "note": "The model turns prose into fields. Every decision after that is a query, and the "
            "last one is a human."}),
   "How a claim in any format becomes a shortlist. The model does the one job models are reliably "
   "good at and nothing else.",
   "How a lost property claim is normalised and matched",
   "A vertical chain of four steps entered by a box labelled A claim, however it arrives: form, "
   "email or phone note. Step one, Normalise free text into the same fields, with a side box "
   "noting one model call for extraction only. Step two, Structural query on zone, date window "
   "and category. Step three, Rank on detail, using distinctive words rather than colour. Step "
   "four, Shortlist to a person, three to five items. A note says the model turns prose into "
   "fields, every decision after that is a query, and the last one is a human."),
  ("h3", "Why the model does not decide"),
  ("p", "A model asked whether a claim matches an item will produce a confident answer and a "
        "score, and the score will be well calibrated for umbrellas and badly calibrated for the "
        "one case that matters, which is two similar black holdalls found on the same night."),
  ("p", "Normalising a description into fields is a different job: it is extraction, it is "
        "checkable, and when it is wrong the error is visible rather than buried inside a "
        "judgement. That distinction is worth holding onto in every system in this series, and it "
        "is unusually clear here."),
  ("h2", "The shortlist"),
  ("callout", "What goes to the person handling the claim", [
   "<strong>Three to five candidates</strong>, ordered, with the photograph visible to staff "
   "only.",
   "<strong>Why each one is a candidate</strong> -- same zone, one day out, same category -- "
   "rather than a percentage.",
   "<strong>What the claim said that does not match</strong>, stated plainly. A colour mismatch "
   "is information, not a disqualification.",
   "<strong>An ownership question</strong> suggested from the item record: what is in the pocket, "
   "what the keyring has on it, what the lock screen shows.",
   "<strong>And no automatic release</strong>, ever. The screen ends in a person deciding.",
  ]),
  ("p", "Showing why an item is a candidate matters more than ordering them well. Staff make the "
        "final call in fifteen seconds when they can see that the item was found in the right "
        "place on the right night, and they make it badly when all they have is a ranked list "
        "with no reasoning."),
  ("h2", "When there is no match"),
  ("p", "Most claims match nothing, because most lost things are genuinely lost somewhere else. "
        "The response to that should not be a dead end: the claim stays open, and new items "
        "logged over the following weeks are checked against it automatically."),
  ("p", "That is where a surprising number of returns come from. An item found on Tuesday and "
        "logged on Wednesday matching a claim from the previous Saturday is a common pattern, and "
        "it only works if claims persist instead of being answered once and closed."),
  ("h3", "Closing a claim honestly"),
  ("p", "A claim that has matched nothing for the full retention period should be closed with a "
        "message that says so plainly. Leaving it silently open is worse than a clear 'we did not "
        "find it', because the claimant is still hoping."),
  ("p", "Next: getting the item back to its owner."),
 ],
},
{
 "slug": "how-an-item-gets-back-to-its-owner",
 "title": "How an item gets back to its owner",
 "nav": "Proving and returning",
 "read": 6, "words": 770,
 "desc": ("The ownership question, why you never show the item first, posting things safely, and "
          "the record that closes it."),
 "og": ("Ask what is in the pocket. Do not ask them to confirm it is a black jacket, because you "
        "just told them it was."),
 "abstract": ("Testing ownership without leaking the answer, collection and postage, chain of "
              "custody for valuables, and what the closing record has to contain."),
 "lede": ("The return is the only irreversible step in the system, which is why it is the one step "
          "that is deliberately not automated at any point."),
 "tags": ["lost property", "verification", "customer service", "logistics", "operations",
          "serverless"],
 "takeaways": [
  "Ask an open question the owner can answer and a stranger cannot.",
  "Never confirm details before they have offered them.",
  "Posting is fine, paid by the claimant, tracked, and never for valuables.",
  "Record who collected, when, and who authorised it.",
  "A wrong release is a data breach as often as it is a lost jacket.",
 ],
 "blocks": [
  ("h2", "The ownership question"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "'Is it a black coat?'", "sub": ["you just told them"], "icon": "chat",
       "label": "useless"},
      {"title": "Show the photo", "sub": ["then ask"], "icon": "image", "label": "worse"},
      {"title": "'What is in the", "sub": ["pockets?'"], "icon": "key", "label": "the test"}],
    "target": {"title": "An answer only the", "sub": ["owner would give"], "icon": "check",
               "then": {"title": "A person releases it", "sub": ["and is recorded"],
                        "icon": "person"}},
    "note": "The whole verification budget is one open question. Spend it well."}),
   "Three ways of asking, two of which hand over the answer. The third costs nothing and is the "
   "only ownership evidence you will ever have.",
   "Three ways of testing ownership of a found item",
   "Three boxes stacked on the left. Asking is it a black coat, labelled useless because you just "
   "told them. Showing the photo and then asking, labelled worse. And asking what is in the "
   "pockets, labelled the test. All three converge on An answer only the owner would give, which "
   "leads down to A person releases it and is recorded. A note says the whole verification budget "
   "is one open question, so spend it well."),
  ("h3", "Open, specific, and from the record"),
  ("p", "The best questions come from the item itself and are recorded at logging time: what is "
        "on the keyring, what the initials are, what is in the side pocket, what the lock screen "
        "photograph shows. One of them is enough."),
  ("p", "It has to be open. 'Does it have a red keyring?' is a yes-or-no question with a "
        "fifty-percent guess rate and it gives away the answer to the next person who tries. "
        "'What is on the keyring?' cannot be guessed and costs the genuine owner nothing."),
  ("h3", "When the owner genuinely cannot answer"),
  ("p", "People do forget what is in their own pockets, and a genuine owner who cannot answer the "
        "first question is common rather than suspicious. The fallback is a second question, then "
        "a judgement by a person, and for low-value items the judgement should lean towards "
        "returning it."),
  ("p", "For a passport or a laptop it should lean the other way, and the honest position to take "
        "with the claimant is that the item will be held until they can identify it or produce "
        "proof of purchase. That is an unsatisfying conversation and it is much better than the "
        "alternative."),
  ("h2", "Collection and postage"),
  ("callout", "The practical rules that avoid arguments", [
   "<strong>Collection in person</strong> is the default and the only option for anything of "
   "value.",
   "<strong>Postage is paid by the claimant</strong>, up front, through a payment link. A "
   "business that posts things for free posts a great many things.",
   "<strong>Tracked, always</strong>, because an untracked parcel that does not arrive becomes "
   "your problem and there is no way to resolve it.",
   "<strong>Never post cash, cards or identity documents.</strong> There is no version of this "
   "that ends well.",
   "<strong>Somebody collecting on behalf of the owner</strong> brings the answer to the "
   "ownership question and their own name goes in the record.",
  ]),
  ("p", "Charging for postage is not mean, and framing it as recovering the cost of the label is "
        "enough for almost everybody. The businesses that struggle with this are the ones that "
        "never decided, so each case is negotiated individually by whoever answers the phone."),
  ("h2", "The record that closes it"),
  ("fig", ("chain", {
    "entry": {"title": "Ownership satisfied", "sub": ["one open question"], "icon": "check"},
    "steps": [
      {"title": "Released to", "sub": ["a name, typed in"], "icon": "person"},
      {"title": "By", "sub": ["the staff member,", "from their login"], "icon": "key"},
      {"title": "When and how", "sub": ["collected or posted,", "with a tracking number"],
       "icon": "truck"},
      {"title": "Item closed", "sub": ["outcome: returned"], "icon": "archive"}],
    "note": "Four fields. They are the difference between a system and a cupboard with an app "
            "attached."}),
   "The closing record. None of it is interesting until the day somebody asks what happened to a "
   "specific item, and on that day it is the only thing that matters.",
   "The chain of custody recorded when an item is returned",
   "A vertical chain of four steps entered by a box labelled Ownership satisfied, one open "
   "question. Step one, Released to a name, typed in. Step two, By the staff member, from their "
   "login. Step three, When and how: collected or posted, with a tracking number. Step four, Item "
   "closed with the outcome recorded as returned. A note says four fields, and they are the "
   "difference between a system and a cupboard with an app attached."),
  ("h3", "Why this is a data question too"),
  ("p", "Handing the wrong person a coat is a small problem. Handing the wrong person a phone, a "
        "laptop bag or a wallet is a personal data incident involving somebody who is not your "
        "customer and did not consent to any of it."),
  ("p", "That reframing is useful internally, because it moves the ownership question from "
        "'being careful about umbrellas' to something the business already has a policy about, "
        "and it explains why the process does not get relaxed at the end of a long shift."),
  ("h3", "Tell the claimant either way"),
  ("p", "The claim that ends in a return should close with a confirmation, and the claim that "
        "ends in nothing should close with a message too. Both are one line, both are automatic, "
        "and the second one is the one that stops people ringing back three times."),
  ("p", "Next: everything nobody comes for."),
 ],
},
{
 "slug": "what-happens-to-what-is-never-claimed",
 "title": "What happens to what is never claimed",
 "nav": "Retention and disposal",
 "read": 5, "words": 740,
 "desc": ("Retention by category, disposal that is a decision rather than a bin bag, and why "
          "staff keeping items is a policy problem."),
 "og": ("Ninety percent of found items are never claimed. Deciding what happens to them is the "
        "part of the system nobody designs, and the part that eventually causes the argument."),
 "abstract": ("Setting retention periods by category, the disposal routes and their pitfalls, why "
              "staff taking items needs an explicit rule, and what the disposal record proves."),
 "lede": ("Most of what is found is never claimed, so the disposal path is the busiest route "
          "through this system and it is the one that usually does not exist."),
 "tags": ["lost property", "retention", "policy", "disposal", "operations", "serverless"],
 "takeaways": [
  "Retention periods are per category, and they are a written decision.",
  "Disposal happens on a date, in batches, authorised by a person.",
  "Charity is the best default; staff keeping items needs an explicit rule.",
  "Record the outcome for everything, including the umbrellas.",
  "The disposal log is what protects you when somebody comes back in a year.",
 ],
 "blocks": [
  ("h2", "Retention by category"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Perishables", "sub": ["same day"], "icon": "stop"},
      {"title": "Everyday items", "sub": ["about a month"], "icon": "box"},
      {"title": "Clothing", "sub": ["a month or two"], "icon": "tag"},
      {"title": "Devices, valuables", "sub": ["considerably longer"], "icon": "lock"},
      {"title": "Cash, documents", "sub": ["longest, with a", "custody record"], "icon": "shield"}],
    "title": "HOW LONG THINGS ARE KEPT",
    "note": "The specific periods are yours to set. Having them written down is the part that "
            "matters."}),
   "Retention as a gradient rather than one number. A single uniform period is either wasteful at "
   "one end or indefensible at the other.",
   "Retention periods for found property by category",
   "A horizontal row of five boxes. Perishables, same day. Everyday items, about a month. "
   "Clothing, a month or two. Devices and valuables, considerably longer. Cash and documents, "
   "longest, with a custody record. A note says the specific periods are yours to set and having "
   "them written down is the part that matters."),
  ("p", "One uniform retention period is the common approach and it is wrong in both directions. "
        "Thirty days is far too long for a half-eaten cake and far too short for a passport, and "
        "the compromise value is simply wrong for everything."),
  ("h3", "The periods are a policy, not a calculation"),
  ("p", "What the right period is depends on where you are, what kind of business you run, and in "
        "some cases on statute -- transport operators and some public venues have specific "
        "obligations that a hotel does not."),
  ("p", "This system does not know any of that and should not pretend to. What it does is hold "
        "the number you decided, apply it per category, and make the date arrive as a task rather "
        "than as a realisation."),
  ("h2", "Disposal is a decision"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Charity", "sub": ["clothing, bags,", "usable items"], "icon": "team",
       "label": "the default"},
      {"title": "Recycled or binned", "sub": ["damaged, worthless"], "icon": "stop",
       "label": "honest"},
      {"title": "Staff", "sub": ["only with an", "explicit policy"], "icon": "person",
       "label": "handle carefully"}],
    "target": {"title": "A batch, authorised", "sub": ["by a named person,", "on a date"],
               "icon": "check",
               "then": {"title": "Outcome recorded", "sub": ["per item, forever"], "icon": "archive"}},
    "note": "The routes matter less than the fact that one was chosen and written down."}),
   "Three disposal routes converging on one authorised batch. The record underneath is what makes "
   "this defensible a year later.",
   "Three disposal routes for unclaimed property",
   "Three boxes stacked on the left. Charity, for clothing, bags and usable items, labelled the "
   "default. Recycled or binned, for damaged or worthless items, labelled honest. And Staff, only "
   "with an explicit policy, labelled handle carefully. All three converge on A batch, authorised "
   "by a named person on a date, which leads down to Outcome recorded per item, forever. A note "
   "says the routes matter less than the fact that one was chosen and written down."),
  ("h3", "The staff question"),
  ("p", "Letting staff keep unclaimed items is common, popular, and creates an incentive nobody "
        "wants to think about: the person who logs an item is the person who benefits if it is "
        "never claimed. Most people are honest and the incentive is still a bad idea."),
  ("p", "If you allow it, the rule needs to be explicit -- which categories, after what period, "
        "approved by somebody other than the finder, and recorded like any other outcome. A "
        "written rule removes the ambiguity that turns an ordinary practice into an accusation."),
  ("h2", "What the log is for"),
  ("callout", "What every disposed item leaves behind", [
   "<strong>The item record</strong>, with its photograph, intact.",
   "<strong>The retention period applied</strong>, and the date it ended.",
   "<strong>The route</strong> -- charity, recycled, destroyed, retained by staff.",
   "<strong>Who authorised the batch</strong>, by name.",
   "<strong>And nothing gets deleted.</strong> Storage is pennies and the record is the only "
   "answer you will have in fourteen months.",
  ]),
  ("p", "The scenario this protects against is specific and it does happen: somebody rings a year "
        "later about a valuable item, having been told at the time that nothing was found, and "
        "wants to know what happened to it."),
  ("p", "With a log, that is a two-minute answer: it was found, it was held for the stated period, "
        "nobody claimed it, and it went to a named charity on a specific date. Without one, it is "
        "an accusation nobody can answer either way, which is the worst possible position for "
        "everybody involved."),
  ("h3", "The number worth watching"),
  ("p", "One figure is worth putting on a monthly page: the proportion of logged items that reach "
        "a recorded outcome of returned. It is usually low, it varies enormously by category, and "
        "it is the only measure of whether any of this is working."),
  ("p", "If it moves from one in twenty to one in six after this system exists, that is several "
        "hundred people a year who got their things back. That is the entire justification, and "
        "it is a better one than the cupboard being tidier."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="claim",
 volumes=[(60, "60 claims"), (240, "240 claims"), (900, "900 claims")],
 read_each=0.0014,
 msgs_each=3.4,
 lede=("The model runs once per claim, not per item: logging is a form with a picklist and a "
       "photograph. Two hundred and forty claims a month is a busy venue. Here is where each cent "
       "goes."),
 store_base=0.34,
 store_growth=0.00022,
 takeaway_extra=("Photographs are the only storage that grows, and resizing on upload keeps even "
                 "a busy year under a dollar."),
 risks=[
  "<strong>Storing photographs at full phone resolution.</strong> Resize on upload. A staff "
  "member confirming a match needs to recognise a jacket, not read a care label.",
  "<strong>Running image recognition on every item.</strong> It is not what makes the match work, "
  "and it turns a two-dollar system into a forty-dollar one for a ranking that zone and date "
  "already produce.",
  "<strong>Re-running open claims against the whole inventory nightly.</strong> Check new items "
  "against open claims, which is a handful of comparisons, not the cross product.",
 ],
 per_unit_note=("The read is one call per claim against a small model, turning whatever somebody "
                "wrote or dictated into the same four fields. Logging an item never calls a "
                "model: it is three taps and a photograph, and the ninety-second budget is the "
                "reason the system works at all."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="lp",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the matching query, and the single model call."),
 outside=[
  {"title": "Finders", "sub": ["a phone, mid-shift"], "icon": "phone"},
  {"title": "Claimants", "sub": ["a form, an email,", "a call taken by staff"], "icon": "inbox"},
  {"title": "Staff at the counter", "sub": ["deciding, and", "recorded"], "icon": "person"}],
 inside=[
  {"title": "API Gateway + S3", "sub": ["logging, photos,", "claim intake"], "icon": "gateway"},
  {"title": "Lambda x4", "sub": ["log, claim,", "match, retire"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["items, claims"], "icon": "database"}],
 note="us-east-1. One account. Photographs are staff-only; no claimant is ever served an image.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Finders, using a phone mid-shift. "
  "Claimants, arriving by form, email or a call taken by staff. And Staff at the counter, "
  "deciding and being recorded. Inside the account, three groups. API Gateway and S3 for logging, "
  "photos and claim intake. Four Lambda functions named log, claim, match and retire. And two "
  "DynamoDB tables named items and claims. A note gives the region as us-east-1, one account, and "
  "states that photographs are staff-only and no claimant is ever served an image."),
 functions=[
  ["<code>lp-log</code>", "API, from the finder's phone",
   "Writes the item, stores the resized photograph, returns the short label code",
   "10s / 512&nbsp;MB"],
  ["<code>lp-claim</code>", "API and SES inbound",
   "One model call; normalises any claim format into zone, date window, category and detail",
   "30s / 1024&nbsp;MB"],
  ["<code>lp-match</code>", "On new claim, and on every new item",
   "Structural query, then ranking; writes the shortlist with the reason for each candidate",
   "30s / 512&nbsp;MB"],
  ["<code>lp-retire</code>", "EventBridge, daily",
   "Applies retention by category, queues disposal batches, closes claims that timed out",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>lp-log-role</code>", "<code>dynamodb:PutItem</code>, <code>s3:PutObject</code>",
   "Items; the photos prefix"],
  ["<code>lp-claim-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>dynamodb:PutItem</code>", "One model id; claims"],
  ["<code>lp-match-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>", "Items read; claims write"],
  ["<code>lp-retire-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Both tables; one verified identity"]],
 tables=[
  ("Table: items",
   "PK   zone              S   the matching partition, deliberately\n"
   "SK   found_at#item_id  S   so a date window is a range query\n"
   "     category          S   from a list of twelve\n"
   "     photo_key         S   resized on upload; staff-only access\n"
   "     label_code        S   the sticker on the physical item\n"
   "     found_by          S\n"
   "     detail            S   optional; the ownership question lives here\n"
   "     handling          S   normal | valuable | document | hazard\n"
   "     retain_until      S   set at write time from category\n"
   "     state             S   held | released | disposed\n"
   "     released_to       S   a typed name\n"
   "     released_by       S   the staff login\n"
   "     released_how      S   collected | posted#<tracking>\n"
   "     outcome           S   returned | charity | recycled | destroyed | staff\n\n"
   "Partitioning on zone is what makes the match one query per\n"
   "neighbouring zone rather than a scan of the cupboard."),
  ("Table: claims",
   "PK   claim_id          S\n"
   "SK   '#claim'          S\n"
   "     zone              S   normalised to the zone list, or null\n"
   "     lost_from         S   date window start\n"
   "     lost_to           S   date window end\n"
   "     category          S\n"
   "     detail            S   raw words, kept for ranking\n"
   "     contact           S\n"
   "     state             S   open | matched | closed_returned | closed_nothing\n"
   "     shortlist         L   [{item_id, reason}] -- reason, never a score\n"
   "     expires_at        S   the day the claimant is told plainly\n\n"
   "Claims stay open and are re-checked against every new item until\n"
   "they expire. A large share of returns come from that path.")],
 inbound=[
  "<strong>Claims arrive in three formats</strong> -- a web form, an email, and a note typed by "
  "whoever answered the phone. All three land in the same normalising function.",
  "<strong>Photographs are never served to claimants.</strong> The signed URL is issued to a "
  "staff session only, which is the technical half of the ownership rule.",
  "<strong>New items are matched against open claims</strong>, not just the other way round. That "
  "path produces returns that would otherwise be missed entirely.",
  "<strong>Nothing is deleted.</strong> Items move to a disposed state with an outcome; the "
  "record and its photograph stay, because the question always comes later than you expect."],
 model_notes=[
  "<strong>One call, per claim.</strong> Free text into zone, date window, category and "
  "distinctive detail, with anything absent left null.",
  "<strong>A small, fast model.</strong> This is normalisation of a short paragraph, and a larger "
  "model produces the same four fields.",
  "<strong>It never scores a match.</strong> The candidate list comes from a query and the "
  "decision comes from a person, because the failure case is handing a stranger somebody's "
  "belongings.",
  "<strong>It never looks at a photograph.</strong> Image recognition is the expensive way to "
  "reproduce information the zone and date already gave you.",
  "<strong>Colour is captured but never filtered on</strong>, because roughly half of claimants "
  "get their own item's colour wrong."],
 gotchas=[
  "Hold the logging step to ninety seconds. Every field you add costs you a percentage of the "
  "items that get logged at all, and an unlogged item is worse than no system.",
  "Partition items by zone and range on the found date. Matching then costs three queries instead "
  "of a scan, which is what keeps the counter interaction under a second.",
  "Never serve an item photograph to a claimant. Once they have seen it, they can describe it, "
  "and your only ownership test is gone.",
  "Set retain_until at write time from the category. Computing retention at disposal time means "
  "the policy change quietly reapplies itself to items already held.",
  "Keep claims open and re-check them against new items. The item found on Tuesday matching "
  "Saturday's claim is one of the most common successful paths in the whole system."],
))
