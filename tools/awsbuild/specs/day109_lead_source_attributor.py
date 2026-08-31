"""Day 109 -- 2026-08-11 -- Lead source attributor."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "lead-source-attributor"
NAME = "Lead source attributor"

SPEC = {
 "slug": SLUG, "date": "2026-08-11", "name": NAME,
 "tagline": ("Works out where an enquiry actually came from, keeps the whole path rather than "
             "one label, and reports the uncertainty instead of hiding it behind a confident "
             "pie chart."),
 "lede": ("A small system that captures where each enquiry came from, stitches together the "
          "touches that led to it, assigns credit under a stated rule, and &mdash; the part most "
          "attribution tools skip &mdash; reports how much of the total it could not attribute "
          "at all. Seven posts on the same system, one diagram at a time, with a cost breakdown "
          "and an engineering reference at the end."),
 "keywords": ["attribution", "lead source", "marketing analytics", "UTM", "reporting",
              "serverless"],
 "icons": ["route", "chart", "search"],
 "faq": [
  ("What is a lead source attributor?",
   "A small serverless system that records where enquiries came from, links repeat visits from "
   "the same person, applies a stated credit rule, and reports the result with its unknown "
   "share visible."),
  ("Why not just use the last click?",
   "You can, and for many businesses it is the right choice. The problem is not that last-click "
   "is wrong; it is that nobody says they are using it, so the report reads as truth rather than "
   "as one rule among several."),
  ("How much of a typical report is unattributable?",
   "Commonly a quarter to a half, and the post on this is blunt about it. Direct traffic, "
   "word of mouth, blocked tracking and phone calls are all real sources that leave no trace."),
  ("Does this replace an analytics product?",
   "No. It answers one question -- where did this enquiry come from -- and stores the answer next "
   "to the enquiry, which analytics products are surprisingly bad at."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "lead-source-attributor-on-aws",
 "title": "A lead source attributor on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Captures where enquiries came from, stitches the touches, applies a stated credit "
          "rule, and shows the unknown share. AWS, about $2 a month."),
 "og": ("Every attribution report is a choice of rule. A report that does not say which rule it "
        "used is not a measurement, it is a decoration."),
 "abstract": ("The whole system on one page -- capture, stitch, credit and report -- and the "
              "single decision that determines whether the output is trustworthy."),
 "lede": ("Somebody asks which of the marketing spend is working. The answer that comes back is a "
          "pie chart, and the pie chart is wrong in a specific way: it shows a hundred per cent "
          "of enquiries divided between sources, when in reality a large share came from "
          "somewhere nobody can see. This post walks through a small system that answers the "
          "question and shows its working."),
 "tags": ["attribution", "lead source", "marketing analytics", "UTM", "reporting", "serverless"],
 "takeaways": [
  "Capture the whole path, not one label. The rule is applied at report time, not at capture.",
  "Stitching repeat visits is where most of the accuracy comes from.",
  "State the credit rule on the report itself. Last click is fine; hiding it is not.",
  "The unattributable share is a headline number, not a footnote.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Visitors", "sub": ["with a referrer,", "or without"], "icon": "person"},
      {"title": "Enquiries", "sub": ["forms, calls, email"], "icon": "form"},
      {"title": "Whoever asks", "sub": ["'what is working?'"], "icon": "chart"}],
    "inside": [
      {"title": "Capture", "sub": ["every touch,", "not just the last"], "icon": "route"},
      {"title": "Stitch", "sub": ["same person,", "different visits"], "icon": "link"},
      {"title": "Credit + report", "sub": ["a stated rule,", "with its unknowns"], "icon": "chart"}],
    "edges": [{"from": 0, "to": 0, "label": "touches"},
              {"from": 1, "to": 1, "label": "an enquiry arrives"},
              {"from": 2, "to": 2, "label": "a report with error bars", "up": True}],
    "note": "The credit rule lives in the report, not in the data. That is the whole design."}),
   "Three things outside the account, three pieces inside it. Keeping the rule out of the stored "
   "data is what lets the same enquiries be re-reported under a different rule later.",
   "System: touches captured, stitched, credited and reported",
   "Three boxes across the top sit outside the AWS account. On the left, Visitors, with a "
   "referrer or without one. In the middle, Enquiries arriving by form, call or email. On the "
   "right, Whoever asks what is working. Each connects by an arrow to the AWS account container "
   "below. Touches flow down into the account. An enquiry arrives. A report with error bars goes "
   "back out. Inside the AWS account are three components in a row. On the left, Capture, which "
   "records every touch rather than just the last. In the middle, Stitch, which links the same "
   "person across different visits. On the right, Credit and report, applying a stated rule and "
   "showing its unknowns. A note at the bottom says the credit rule lives in the report, not in "
   "the data, and that is the whole design."),
  ("h3", "The one decision that matters"),
  ("p", "Most attribution setups collapse the path to a single source at the moment the enquiry "
        "arrives: a <code>source</code> column on the lead record, filled from whatever the last "
        "referrer was. It is simple, it is what every CRM does by default, and it destroys "
        "information irreversibly. Once the column says \"google\", nobody can ever ask what "
        "happened before that."),
  ("p", "Storing the path instead &mdash; every touch, in order, with timestamps &mdash; costs "
        "almost nothing and means the credit rule becomes a reporting choice. The same quarter "
        "can be reported last-click and first-click side by side, which is far more informative "
        "than either alone, and is impossible if the data was flattened at capture."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Capture.</strong> Records each arrival with its referrer, campaign parameters and "
   "landing page. Part 2 covers what is captured and what genuinely cannot be.",
   "<strong>Stitch.</strong> Links visits from the same person across sessions and devices, which "
   "is where most of the real accuracy lives. Part 3.",
   "<strong>Credit and report.</strong> Applies a named rule and publishes the result with its "
   "unattributable share in the headline. Parts 4 and 5.",
  ]),
  ("h2", "One enquiry, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Podcast mention", "sub": ["day 1, no link"], "icon": "audio"},
      {"title": "Searched the name", "sub": ["day 1, organic"], "icon": "search"},
      {"title": "Came back direct", "sub": ["day 9, typed it in"], "icon": "route"},
      {"title": "Clicked an ad", "sub": ["day 11, retargeting"], "icon": "target"},
      {"title": "Enquired", "sub": ["day 11"], "icon": "form"}],
    "title": "ONE ENQUIRY, FIVE TOUCHES",
    "note": "Last click credits the retargeting ad. The podcast is invisible and did the work."}),
   "A realistic path. Every rule gets this one wrong in a different direction, which is the "
   "argument for reporting more than one.",
   "One enquiry arriving after five separate touches",
   "A horizontal row of five boxes joined by arrows. Podcast mention: day one, with no link. "
   "Searched the name: day one, organic. Came back direct: day nine, typed the address in. "
   "Clicked an ad: day eleven, retargeting. Enquired: day eleven. A note says last click credits "
   "the retargeting ad, while the podcast is invisible and did the work."),
  ("h2", "In plain words"),
  ("p", "Somebody hears the business mentioned on a podcast. There is no link and no tracking; "
        "they search the name and land on the site. Nine days later they come back by typing the "
        "address directly. Two days after that a retargeting ad catches them, they click it, and "
        "they fill in the enquiry form."),
  ("p", "Under last click, the retargeting ad gets the credit, and the ad platform will report it "
        "confidently. Under first click, organic search gets it. The podcast, which is the actual "
        "reason any of this happened, appears nowhere under any rule, because it left no trace at "
        "all."),
  ("p", "What this system does is store all four touches, report the last-click and first-click "
        "views next to each other, and put a line at the top saying that thirty-eight per cent of "
        "the quarter's enquiries had no identifiable first source. That last line is the most "
        "honest thing on the page, and it is the one every commercial tool leaves off."),
  ("callout", "Design rules that shaped every decision", [
   "Store the path. Never collapse it to one source at capture time.",
   "The credit rule is named on every report. \"Last click\" printed at the top, always.",
   "The unattributable share is a headline number, next to the totals.",
   "Stitching is best-effort and its confidence is recorded with it.",
   "Never build a cross-site profile. This links a person to their own visits, nothing more.",
   "A source that cannot be measured is not a source that does not work.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Attribution has an unusual failure mode: the output is always plausible. A pie chart of "
        "sources looks the same whether it was built from complete data or from the forty per "
        "cent that happened to be traceable, and nobody looking at it can tell which. Budgets get "
        "moved on the strength of it."),
  ("p", "So the design is built around making the uncertainty impossible to lose. The path is "
        "kept so rules can be compared, the rule is named so the number has a definition, and the "
        "unknown share sits in the headline so it cannot quietly become zero."),
  ("p", "The next four posts walk through each piece: how a touch is captured, how visits get "
        "stitched, how credit is assigned, and what the report actually says. One diagram per "
        "post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-touch-gets-captured",
 "title": "How a touch gets captured",
 "nav": "How it is captured",
 "read": 5, "words": 740,
 "desc": ("What a referrer tells you, what campaign parameters tell you, what direct traffic "
          "hides, and the touches that never reach the site at all."),
 "og": ("Direct traffic is not a source. It is a bucket of everything that did not announce "
        "itself, and treating it as a source is the first mistake."),
 "abstract": ("What is recorded on each arrival, why the referrer is less reliable than it looks, "
              "what direct traffic actually contains, and the offline touches nothing can see."),
 "lede": ("Capture is the easy part of attribution and it is still where the errors start, "
          "because the fields that look authoritative are not, and the biggest bucket in every "
          "report is not a source at all."),
 "tags": ["attribution", "UTM", "referrer", "tracking", "analytics", "serverless"],
 "takeaways": [
  "Record referrer, campaign parameters, landing page and timestamp -- all four, every time.",
  "The referrer is missing or stripped far more often than people expect.",
  "Direct is a bucket, not a source. Naming it honestly changes how it is read.",
  "Tag your own campaigns properly; it is the only signal you fully control.",
  "Some touches never reach the site, and no amount of engineering will capture them.",
 ],
 "blocks": [
  ("h2", "What gets recorded"),
  ("fig", ("chain", {
    "entry": {"title": "Somebody arrives", "sub": ["on any page"], "icon": "person"},
    "steps": [
      {"title": "Campaign parameters?", "sub": ["utm_source and friends"], "icon": "branch",
       "exit": {"title": "Trust them", "sub": ["you set them"], "icon": "check", "label": "yes"}},
      {"title": "A referrer header?", "sub": ["often stripped"], "icon": "branch",
       "exit": {"title": "Direct", "sub": ["a bucket, not a source"], "icon": "question",
                "label": "no"}},
      {"title": "Is it a search engine?", "sub": ["by domain"], "icon": "branch",
       "exit": {"title": "Organic search", "sub": ["term almost never given"], "icon": "search",
                "label": "yes"}},
      {"title": "Record the touch", "sub": ["referrer, landing, time"], "icon": "database"},
      {"title": "Attach to a visitor", "sub": ["for stitching later"], "icon": "link"}],
    "note": "Every branch here loses information. The design records which branch it took."}),
   "How one arrival becomes one stored touch. The branch taken is recorded alongside the touch, "
   "so a report can distinguish a confident source from a guessed one.",
   "How a single arrival is captured as an attribution touch",
   "A vertical chain of five steps entered by a box labelled Somebody arrives on any page. Step "
   "one asks whether campaign parameters such as utm_source are present; if so it exits to Trust "
   "them, because you set them. Step two asks whether a referrer header is present, noting it is "
   "often stripped; if not it exits to Direct, described as a bucket rather than a source. Step "
   "three asks whether the referrer is a search engine, matched by domain; if so it exits to "
   "Organic search, noting the search term is almost never given. Step four records the touch "
   "with its referrer, landing page and time. Step five attaches it to a visitor for stitching "
   "later. A note says every branch here loses information, and the design records which branch "
   "it took."),
  ("h3", "The referrer is weaker than it looks"),
  ("p", "A referrer header arrives on a good deal less traffic than people assume. Links from "
        "apps frequently carry none. Messaging apps, email clients and PDF readers usually strip "
        "it. Privacy settings in mainstream browsers trim it to the bare domain or remove it. A "
        "link somebody sent a friend on WhatsApp arrives looking exactly like direct traffic."),
  ("p", "This matters more than a missing field usually would, because the missing cases are not "
        "random. Word-of-mouth referrals &mdash; the source most businesses most want to measure "
        "&mdash; are precisely the ones that arrive with no referrer, which biases every report "
        "against the thing that is working best."),
  ("h3", "What direct actually contains"),
  ("callout", "Everything that ends up in \"direct\"", [
   "Somebody typing the address, which is what the label implies and is the smallest part of it.",
   "A link from a messaging app, an email client, or a document.",
   "A bookmark, an autocomplete, a link somebody was given verbally.",
   "Traffic where the referrer was stripped by a privacy setting.",
   "An app-to-browser handoff that dropped the header.",
   "<strong>Rename it.</strong> Calling this column \"unattributed\" rather than \"direct\" "
   "changes how every reader interprets the report, at no engineering cost.",
  ]),
  ("h2", "The touches that never arrive"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A recommendation", "sub": ["in a conversation"], "icon": "person"},
      {"title": "A podcast mention", "sub": ["no link at all"], "icon": "audio"},
      {"title": "A print ad", "sub": ["read on a train"], "icon": "doc"},
      {"title": "A phone call", "sub": ["never touched the site"], "icon": "phone"},
      {"title": "Invisible", "sub": ["and often decisive"], "icon": "question"}],
    "title": "WHAT NO SYSTEM CAN CAPTURE",
    "note": "The correct response is to ask people, not to build more tracking."}),
   "The permanent blind spot. It is not an engineering gap, and the tooling response to it is the "
   "wrong response.",
   "The marketing touches that no tracking system can capture",
   "A horizontal row of five boxes. A recommendation in a conversation. A podcast mention with no "
   "link at all. A print ad read on a train. A phone call that never touched the site. Invisible, "
   "and often decisive. A note says the correct response is to ask people, not to build more "
   "tracking."),
  ("p", "The single highest-value thing to add to this system is not a tracking improvement. It "
        "is a field on the enquiry form asking how they heard about you, free text, optional. The "
        "answers are messy, a third of people skip it, and it still reveals more about the "
        "invisible sources than any amount of instrumentation."),
  ("p", "Those answers are stored as a separate touch with a distinct type, so the report can say "
        "\"twelve people mentioned the podcast\" alongside \"the podcast generated zero traceable "
        "clicks\". Both are true and only the second one shows up in an ad platform."),
  ("h3", "Tag your own campaigns"),
  ("p", "Campaign parameters are the one signal fully under your control, and they are worth "
        "being disciplined about: a consistent source, medium and campaign on every link you "
        "publish, including the ones in email footers and social profiles that nobody thinks of "
        "as campaigns."),
  ("p", "The common failure is inconsistency &mdash; <code>facebook</code>, <code>FB</code> and "
        "<code>fb-ads</code> in the same report as three different sources. Normalising at "
        "capture is a twenty-line lookup table and it prevents a quarter of the confusion in "
        "every attribution report ever produced."),
  ("p", "Next: linking the visits that belong together."),
 ],
},
{
 "slug": "how-visits-get-stitched",
 "title": "How visits get stitched",
 "nav": "How they are stitched",
 "read": 5, "words": 750,
 "desc": ("Linking the same person across sessions and devices, how confident each link is, and "
          "the line this system does not cross."),
 "og": ("Stitching is where the accuracy is, and it is also where attribution quietly turns into "
        "surveillance. The line is: link a person to their own visits, never across sites."),
 "abstract": ("How repeat visits get linked, why the enquiry itself is the strongest signal, how "
              "confidence is recorded, and the identity work this system deliberately refuses."),
 "lede": ("A first-time visitor who enquires immediately is easy. Almost nobody does that. The "
          "accuracy in attribution comes from correctly linking the visit where somebody enquired "
          "to the four earlier visits where they were deciding, and that is a harder problem than "
          "the capture step by a wide margin."),
 "tags": ["attribution", "identity", "sessions", "privacy", "analytics", "serverless"],
 "takeaways": [
  "A first-party cookie links visits on one device. That covers most of the value.",
  "The enquiry itself is the strongest stitch: an email address links devices retroactively.",
  "Record how a link was made, so a weak stitch can be excluded from a strict report.",
  "Never buy or join third-party identity data. The line is firm and worth stating.",
  "Unstitched visits stay unstitched rather than being guessed into a plausible path.",
 ],
 "blocks": [
  ("h2", "Three ways a link gets made"),
  ("fig", ("chain", {
    "entry": {"title": "A new touch", "sub": ["someone arriving"], "icon": "route"},
    "steps": [
      {"title": "A visitor id already?", "sub": ["first-party, this device"], "icon": "branch",
       "exit": {"title": "Strong link", "sub": ["same device, certain"], "icon": "check",
                "label": "yes"}},
      {"title": "Did they enquire?", "sub": ["giving an email"], "icon": "branch",
       "exit": {"title": "Retroactive link", "sub": ["merges other devices"], "icon": "link",
                "label": "yes"}},
      {"title": "A one-time link token?", "sub": ["from an email we sent"], "icon": "branch",
       "exit": {"title": "Strong link", "sub": ["we know who we sent it to"], "icon": "check",
                "label": "yes"}},
      {"title": "Leave it unstitched", "sub": ["a standalone touch"], "icon": "question"},
      {"title": "Record the confidence", "sub": ["with the link"], "icon": "database"}],
    "note": "There is no fourth branch that guesses. Unstitched stays unstitched."}),
   "The three stitching signals, in order of strength. The absence of a probabilistic fallback is "
   "a deliberate choice rather than an omission.",
   "How visits from the same person are linked together",
   "A vertical chain of five steps entered by a box labelled A new touch, someone arriving. Step "
   "one asks whether a visitor id already exists, first-party and on this device; if so it exits "
   "to Strong link, same device, certain. Step two asks whether they enquired, giving an email "
   "address; if so it exits to Retroactive link, which merges other devices. Step three asks "
   "whether a one-time link token from an email we sent is present; if so it exits to Strong "
   "link, because we know who we sent it to. Step four leaves it unstitched as a standalone "
   "touch. Step five records the confidence alongside the link. A note says there is no fourth "
   "branch that guesses, and unstitched stays unstitched."),
  ("h3", "The enquiry is the strongest signal"),
  ("p", "When somebody finally fills in the form and gives an email address, that address links "
        "backwards to every earlier visit on that device, and forwards to any other device where "
        "the same address has been used. It is the highest-quality identity signal in the system "
        "and it arrives at the end, which means stitching has to be able to run retroactively "
        "over touches already stored."),
  ("p", "That has a practical consequence worth planning for: the attribution of an enquiry can "
        "change after it is recorded. Somebody enquires on their phone, and a week later logs in "
        "on a laptop where they had visited three times from a newsletter. The path grows, and "
        "the report for that quarter should reflect it. Reports are therefore computed on demand "
        "from the stored path rather than frozen at enquiry time."),
  ("h3", "Recording confidence"),
  ("p", "Each link carries how it was made &mdash; same-device cookie, email match, token from a "
        "sent message &mdash; and reports can be run at different strictness levels. A strict "
        "report uses only same-device and token links; a looser one includes email matches across "
        "devices."),
  ("p", "The gap between the two is itself informative. If the strict and loose reports say "
        "roughly the same thing, the stitching is not doing much work and the result is robust. "
        "If they diverge sharply, the answer depends on identity assumptions and should be "
        "presented as a range."),
  ("h2", "The line this does not cross"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Own visits", "sub": ["linked -- fine"], "icon": "check"},
      {"title": "Own emails", "sub": ["linked -- fine"], "icon": "check"},
      {"title": "Bought identity graph", "sub": ["refused"], "icon": "stop"},
      {"title": "Fingerprinting", "sub": ["refused"], "icon": "stop"},
      {"title": "Cross-site tracking", "sub": ["refused"], "icon": "lock"}],
    "title": "WHAT THIS SYSTEM REFUSES TO DO",
    "note": "The refused three would improve the numbers. That is not a sufficient argument."}),
   "The boundary, stated plainly. Everything on the right would raise the stitch rate, which is "
   "exactly why the line has to be drawn on something other than accuracy.",
   "The identity techniques this attribution system refuses to use",
   "A horizontal row of five boxes. Own visits: linked, which is fine. Own emails: linked, which "
   "is fine. Bought identity graph: refused. Fingerprinting: refused. Cross-site tracking: "
   "refused. A note says the refused three would improve the numbers, and that is not a "
   "sufficient argument."),
  ("p", "Fingerprinting deserves a specific mention because it is technically available, it "
        "genuinely works, and it is presented in vendor material as a neutral fallback for when "
        "cookies are unavailable. It is not neutral: it exists to identify people who have "
        "configured their browser to make that harder, which is a fairly direct way of overriding "
        "a stated preference."),
  ("p", "The practical cost of refusing all three is a lower stitch rate and a larger unattributed "
        "column, which the report shows honestly. That is a better position than a complete-"
        "looking report built on data whose provenance nobody in the business could explain."),
  ("h3", "What unstitched costs"),
  ("p", "At typical volumes, somewhere between a fifth and a third of touches never get linked to "
        "an enquiry. They sit in the store as standalone arrivals and contribute to the "
        "denominator without contributing to any path."),
  ("p", "That is not waste; it is the measurement. A source that generates a lot of unstitched "
        "traffic and few enquiries is telling you something, and averaging it away into an "
        "attributed-only report is how a channel keeps a budget it has not earned."),
  ("p", "Next: assigning the credit."),
 ],
},
{
 "slug": "how-credit-gets-assigned",
 "title": "How credit gets assigned",
 "nav": "How credit is assigned",
 "read": 5, "words": 750,
 "desc": ("Four rules, what each one is good for, why running two is better than picking one, "
          "and the rule nobody should use."),
 "og": ("There is no correct attribution rule. There is a rule you chose, and a report that says "
        "which one it was."),
 "abstract": ("The four common credit rules and what each is actually good for, why reporting two "
              "beats picking one, and the case against the rule that looks most sophisticated."),
 "lede": ("Every argument about attribution rules is really an argument about which "
          "oversimplification to accept, and it goes better when everyone involved knows that. "
          "There is no rule that recovers the truth from the data, because the truth &mdash; why "
          "somebody actually decided &mdash; was never in the data."),
 "tags": ["attribution", "last click", "first click", "modelling", "reporting", "serverless"],
 "takeaways": [
  "Last click is defensible and simple, and undervalues everything that creates awareness.",
  "First click values discovery and ignores everything that closed the deal.",
  "Reporting both, side by side, is more useful than either and takes no extra work.",
  "Linear and time-decay look fairer and mostly move the confusion around.",
  "Algorithmic attribution on small volumes is a confident number with nothing behind it.",
 ],
 "blocks": [
  ("h2", "The four rules"),
  ("table", ["Rule", "Gives credit to", "Good for", "Blind to"], [
   ["Last click", "The final touch", "Closing channels, ad spend decisions",
    "Everything that created the demand"],
   ["First click", "The first known touch", "Discovery channels, content, SEO",
    "Everything that converted it"],
   ["Linear", "All touches equally", "Long considered purchases", "Which touch mattered"],
   ["Time decay", "Recent touches more", "Short sales cycles", "Early awareness, mostly"],
  ]),
  ("p", "None of these is a model of how people decide. They are conventions for dividing a "
        "number, and their value lies almost entirely in being stated. A last-click report "
        "labelled \"last click\" is a useful instrument; the same report labelled \"lead sources\" "
        "is a source of bad decisions."),
  ("h2", "Run two, not one"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Last click", "parts": [("paid", 75), ("retarget", 49), ("organic", 31),
                                         ("referral", 20), ("other", 46)]},
      {"label": "First click", "parts": [("paid", 24), ("retarget", 3), ("organic", 69),
                                          ("referral", 42), ("other", 83)]}],
    "series": [("paid", "Paid search", "#ED7100"),
               ("retarget", "Retargeting", "#E7157B"),
               ("organic", "Organic search", "#7AA116"),
               ("referral", "Referral and social", "#8C4FFF"),
               ("other", "Everything else known", "#7D8CA3")],
    "unit": "",
    "note": "Same 221 enquiries, same data, two rules. The disagreement is the finding."}),
   "The same quarter under two rules. Paid search takes a third of the credit on last click and "
   "a tenth on first click; organic does the reverse. A single-rule report deletes that "
   "disagreement entirely.",
   "The same quarter reported under two attribution rules side by side",
   "A stacked bar chart with two bars, each totalling two hundred and twenty-one enquiries. Five "
   "series: Paid search in orange, Retargeting in pink, Organic search in green, Referral and "
   "social in purple, and Everything else known in grey. The left bar, Last click, shows paid "
   "search at seventy-five, retargeting at forty-nine, organic search at thirty-one, referral and "
   "social at twenty, and everything else at forty-six. The right bar, First click, shows paid "
   "search at twenty-four, retargeting at three, organic search at sixty-nine, referral and "
   "social at forty-two, and everything else at eighty-three. A note says same two hundred and "
   "twenty-one enquiries, same data, two rules, and the disagreement is the finding."),
  ("p", "Reading the two bars together gives the analysis neither gives alone: paid search closes "
        "and rarely starts, organic starts and rarely closes, and cutting either one damages the "
        "other. That costs nothing extra to produce, because the path is already stored and both "
        "rules run over the same rows at report time."),
  ("p", "It also changes the conversation from \"which channel wins\" to \"which channel does "
        "what\", which is the question somebody actually wanted answered."),
  ("h3", "The classic mistake it prevents"),
  ("p", "A last-click report shows organic search at fourteen per cent and paid search at "
        "thirty-four, so the content budget gets cut and the ad budget grows. Six months later "
        "the ads perform worse and nobody connects the two, because the mechanism &mdash; the "
        "content was creating the demand the ads were harvesting &mdash; is invisible in "
        "last-click and obvious in the pair."),
  ("h2", "The rule that looks most sophisticated"),
  ("fig", ("chain", {
    "entry": {"title": "\"Use algorithmic attribution\"", "sub": ["data-driven, it says"],
              "icon": "model"},
    "steps": [
      {"title": "How many conversions?", "sub": ["per month"], "icon": "counter"},
      {"title": "Fewer than a few hundred?", "sub": ["most businesses"], "icon": "branch",
       "exit": {"title": "Not enough data", "sub": ["the model fits noise"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Can you explain a change?", "sub": ["when a number moves"], "icon": "branch",
       "exit": {"title": "Unexplainable", "sub": ["and budgets move on it"], "icon": "question",
                "label": "no"}},
      {"title": "Does it see offline touches?", "sub": ["the podcast"], "icon": "branch",
       "exit": {"title": "No", "sub": ["same blind spot, more confidence"], "icon": "stop",
                "label": "no"}},
      {"title": "Use the simple rules", "sub": ["and say which"], "icon": "check"}],
    "note": "A sophisticated method on thin data produces a precise number, not an accurate one."}),
   "Why algorithmic attribution is usually the wrong choice at small scale. Each gate is a "
   "practical question rather than a theoretical objection.",
   "Why algorithmic attribution usually fails at small volumes",
   "A vertical chain of five steps entered by a box labelled Use algorithmic attribution, "
   "data-driven, it says. Step one asks how many conversions there are per month. Step two asks "
   "whether it is fewer than a few hundred, which covers most businesses; if so it exits to Not "
   "enough data, because the model fits noise. Step three asks whether you can explain a change "
   "when a number moves; if not it exits to Unexplainable, and budgets move on it. Step four asks "
   "whether it sees offline touches such as the podcast; if not it exits to No, the same blind "
   "spot with more confidence. Step five recommends using the simple rules and saying which. A "
   "note says a sophisticated method on thin data produces a precise number, not an accurate one."),
  ("p", "The specific problem with algorithmic attribution at small volume is not that the "
        "mathematics is wrong. It is that it produces a number nobody in the business can "
        "interrogate, over data with the same blind spots as everything else, and the "
        "unexplainability makes it harder rather than easier to notice when it has gone wrong."),
  ("p", "A last-click number that somebody disagrees with can be argued about productively, "
        "because everyone knows what it means. That is an underrated property."),
  ("h3", "Where the rule lives"),
  ("p", "In the report, never in the stored data. A stored <code>attributed_source</code> field "
        "is the thing that makes all of this impossible later, because the moment it exists "
        "something starts reading it, and then the rule cannot be changed without changing "
        "history."),
  ("p", "Next: what the report actually says."),
 ],
},
{
 "slug": "how-the-report-shows-its-uncertainty",
 "title": "How the report shows its uncertainty",
 "nav": "How it is reported",
 "read": 5, "words": 730,
 "desc": ("The unattributed share in the headline, the ranges rather than points, and the "
          "sentence that belongs on every attribution report."),
 "og": ("A pie chart that adds to a hundred per cent is claiming to know where every enquiry "
        "came from. It does not."),
 "abstract": ("Why the unattributed share belongs in the headline, how to present two rules "
              "without confusing the reader, and the standing caveat every report should carry."),
 "lede": ("The report is where all of this either becomes useful or becomes another confident "
          "chart. The difference is almost entirely presentational, which is frustrating and also "
          "means it is cheap to get right."),
 "tags": ["attribution", "reporting", "uncertainty", "dashboards", "analytics", "serverless"],
 "takeaways": [
  "Put the unattributed share in the headline, not in a footnote or a slice.",
  "Never draw a pie chart. It forces the total to a hundred per cent by construction.",
  "Show both rules as a range where they disagree.",
  "Report volumes alongside percentages; small denominators make dramatic swings.",
  "Carry the same standing caveat every time so it cannot quietly disappear.",
 ],
 "blocks": [
  ("h2", "What the headline says"),
  ("callout", "The top of the report, every quarter", [
   "<strong>256 enquiries this quarter.</strong>",
   "<strong>97 (38%) could not be attributed to any source.</strong> No referrer, no campaign "
   "tag, no earlier visit.",
   "<strong>159 have at least one known touch.</strong> The percentages below are shares of "
   "those 159, not of 256.",
   "<strong>Rule: last click, with first click shown alongside.</strong>",
   "<strong>Where the two rules disagree by more than 10 points,</strong> both numbers are shown "
   "rather than one.",
  ]),
  ("p", "Five lines, and they change how every number underneath is read. The third is the one "
        "that does the most work: making the denominator explicit stops a reader from mentally "
        "converting \"paid search: 34%\" into \"a third of our business comes from paid search\", "
        "which is not what it says."),
  ("h2", "Why not a pie chart"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Q1 -- 234", "parts": [("unattributed", 88), ("paid", 71), ("organic", 34),
                                        ("referral", 22), ("other", 19)]},
      {"label": "Q2 -- 248", "parts": [("unattributed", 94), ("paid", 66), ("organic", 41),
                                        ("referral", 26), ("other", 21)]},
      {"label": "Q3 -- 256", "parts": [("unattributed", 97), ("paid", 75), ("organic", 31),
                                        ("referral", 29), ("other", 24)]}],
    "series": [("unattributed", "Unattributed -- no source at all", "#7D8CA3"),
               ("paid", "Paid search", "#ED7100"),
               ("organic", "Organic search", "#7AA116"),
               ("referral", "Referral and social", "#8C4FFF"),
               ("other", "Everything else known", "#01A88D")],
    "unit": "",
    "note": "The grey band is the biggest one. On a pie chart it is a slice like any other."}),
   "Three quarters of enquiries with the unattributed share drawn as a first-class band rather "
   "than left out of the picture. Its size relative to everything else is the single most "
   "important thing on the chart.",
   "Enquiries by source over three quarters with unattributed shown as a band",
   "A stacked bar chart with three bars, one per quarter, counted in enquiries. Five series: "
   "Unattributed with no source at all in grey, Paid search in orange, Organic search in green, "
   "Referral and social in purple, and Everything else known in teal. Q1 totals two hundred and "
   "thirty-four, with unattributed at eighty-eight, paid search at seventy-one, organic search at "
   "thirty-four, referral and social at twenty-two, and everything else at nineteen. Q2 totals "
   "two hundred and forty-eight, with unattributed at ninety-four, paid search at sixty-six, "
   "organic search at forty-one, referral and social at twenty-six, and everything else at "
   "twenty-one. Q3 totals two hundred and fifty-six, with unattributed at ninety-seven, paid "
   "search at seventy-five, organic search at thirty-one, referral and social at twenty-nine, and "
   "everything else at twenty-four. A note says the grey band is the biggest one, and on a pie "
   "chart it is a slice like any other."),
  ("p", "A pie chart is structurally unable to represent this honestly. It divides a whole, so "
        "the unattributed share becomes just another slice competing for attention, and if "
        "somebody removes it &mdash; which somebody always does, because it is not a source "
        "&mdash; the remaining slices silently inflate to fill the space."),
  ("p", "Bars keep the magnitudes visible and keep the counts on the axis, which matters because "
        "a channel going from four enquiries to eight is a hundred per cent increase and also "
        "four enquiries."),
  ("h2", "Showing disagreement as a range"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Organic", "sub": ["14% or 31%"], "icon": "search"},
      {"title": "Paid search", "sub": ["34% or 11%"], "icon": "target"},
      {"title": "Referral", "sub": ["9% or 19%"], "icon": "link"},
      {"title": "Read as a range", "sub": ["not a point"], "icon": "chart"},
      {"title": "The width", "sub": ["is the finding"], "icon": "search"}],
    "title": "WHERE THE TWO RULES DISAGREE",
    "note": "A wide range means the channel's role depends on where in the path you look."}),
   "The disagreement presented as a range rather than resolved by picking a winner. Channels with "
   "wide ranges behave differently at different points in the path.",
   "Attribution results shown as ranges where two rules disagree",
   "A horizontal row of five boxes. Organic: fourteen per cent or thirty-one per cent. Paid "
   "search: thirty-four per cent or eleven per cent. Referral: nine per cent or nineteen per "
   "cent. Read as a range, not a point. The width is the finding. A note says a wide range means "
   "the channel's role depends on where in the path you look."),
  ("p", "The instinct on seeing two numbers is to ask which is right, and the answer is neither, "
        "which is unsatisfying and true. The productive version of the question is what the "
        "channel is doing: a channel that is high on first click and low on last click is "
        "starting conversations, and cutting it will show up somewhere else two quarters later."),
  ("h3", "Volumes next to percentages"),
  ("p", "Always both. A percentage on a base of eleven enquiries swings wildly for reasons that "
        "have nothing to do with marketing, and a quarterly report full of percentages invites "
        "people to read noise as trend."),
  ("p", "The practical rule is to grey out or annotate any figure computed on fewer than about "
        "twenty enquiries. It stops the smallest, noisiest categories from producing the most "
        "dramatic-looking movements on the page."),
  ("h2", "The standing caveat"),
  ("callout", "Printed at the bottom of every report", [
   "<strong>This report shows where enquiries came from as far as we can see it.</strong>",
   "<strong>It cannot see:</strong> recommendations, conversations, podcasts and print, phone "
   "enquiries that never touched the site, and anyone whose browser withheld the referrer.",
   "<strong>Those are real sources.</strong> Their absence from this report is a limit of the "
   "measurement, not evidence they do not work.",
   "<strong>The 'how did you hear about us' answers</strong> are reported separately and are the "
   "only view we have of them.",
   "<strong>Do not cut a channel</strong> on the strength of this report alone.",
  ]),
  ("p", "It reads as boilerplate and that is exactly why it works. It stays on the page every "
        "quarter, so the day somebody proposes cutting the thing that generates all the "
        "word-of-mouth, the objection is already printed underneath the chart they are pointing "
        "at."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="touch",
 volumes=[(20000, "20,000 touches"), (80000, "80,000 touches"), (300000, "300,000 touches")],
 read_each=0.0,
 msgs_each=0.0,
 lede=("Touches are cheap and numerous; enquiries are few. This is a write-heavy, model-free "
       "system, so the cost is almost entirely storage and writes. Eighty thousand touches a "
       "month is a reasonably busy small site. Here is where each cent goes."),
 takeaway_extra=("Touch writes dominate. Reports are computed on demand and are a rounding error "
                 "next to them."),
 risks=[
  "<strong>Writing a row per page view.</strong> This system records arrivals, not page views. "
  "Recording every navigation multiplies the write volume by ten for no attribution value.",
  "<strong>Never expiring touches.</strong> Touches older than the longest realistic sales cycle "
  "contribute nothing to any report. Eighteen months is generous for most businesses.",
  "<strong>Recomputing reports on a schedule.</strong> Nobody reads a dashboard hourly. Compute "
  "on request and cache for a day.",
 ],
 per_unit_note=("There is no read line and no messaging line: nothing here calls a model and "
                "nothing sends email. The variable cost is writes and the storage they "
                "accumulate."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ls",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the normalisation table, and how the report is computed."),
 outside=[
  {"title": "Site pages", "sub": ["a beacon on arrival"], "icon": "route"},
  {"title": "Enquiry forms", "sub": ["and the CRM"], "icon": "form"},
  {"title": "The report", "sub": ["on request"], "icon": "chart"}],
 inside=[
  {"title": "Function URL + API", "sub": ["touch intake,", "report request"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["capture, stitch, report"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["touches, identities"], "icon": "database"}],
 note="us-east-1. One account. Touches expire at 18 months; no third-party identity data, ever.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Site pages, sending a beacon on arrival. "
  "Enquiry forms and the CRM. And The report, produced on request. Inside the account, three "
  "groups. A Function URL for touch intake and an API for report requests. Three Lambda functions "
  "named capture, stitch and report. And two DynamoDB tables named touches and identities. A note "
  "gives the region as us-east-1, one account, states that touches expire at eighteen months, and "
  "that no third-party identity data is used, ever."),
 functions=[
  ["<code>ls-capture</code>", "Function URL",
   "Normalises the source, writes one touch, sets the first-party id", "5s / 512&nbsp;MB"],
  ["<code>ls-stitch</code>", "DynamoDB stream on enquiries",
   "Merges identities on an email match; rewrites the identity index", "60s / 1024&nbsp;MB"],
  ["<code>ls-report</code>", "API, cached one day",
   "Walks paths, applies both rules, computes the unattributed share",
   "120s / 1024&nbsp;MB"]],
 roles=[
  ["<code>ls-capture-role</code>", "<code>dynamodb:PutItem</code>", "The touches table only"],
  ["<code>ls-stitch-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>",
   "Touches and identities"],
  ["<code>ls-report-role</code>", "<code>dynamodb:Query</code>",
   "Read-only across both tables"]],
 tables=[
  ("Table: touches",
   "PK   visitor_id        S   first-party, this device\n"
   "SK   at                S   2026-08-11T09:14:02Z\n"
   "     source            S   normalised: google | facebook | podcast_x\n"
   "     medium            S   organic | cpc | referral | direct | asked\n"
   "     campaign          S   from utm_campaign, if given\n"
   "     referrer_host     S   verbatim, before normalisation\n"
   "     landing           S   /pricing\n"
   "     how_detected      S   utm | referrer | none\n"
   "     ttl               N   epoch, +18 months\n\n"
   "`how_detected` is what lets a strict report exclude guessed sources.\n"
   "`medium=asked` is the free-text 'how did you hear about us' answer,\n"
   "stored as a touch so it appears in the same path."),
  ("Table: identities",
   "PK   identity_key      S   email hash, or the visitor id itself\n"
   "SK   visitor_id        S   one row per linked device\n"
   "     linked_by         S   cookie | email | token\n"
   "     linked_at         S   2026-08-11T09:20:00Z\n"
   "     enquiry_id        S   set on the row that enquired\n\n"
   "Merges are additive and never delete a visitor id, so a report can be\n"
   "recomputed at any strictness level from the same rows.")],
 inbound=[
  "<strong>One beacon per arrival</strong>, not per page view. An arrival is a session start or a "
  "referrer change.",
  "<strong>Source normalisation is a static table</strong> mapping the many spellings of each "
  "channel to one key. It is the highest-value twenty lines in the system.",
  "<strong>The enquiry write triggers stitching</strong> through a DynamoDB stream, so "
  "attribution improves retroactively as identity information arrives.",
  "<strong>Reports are computed on request</strong> and cached for a day. Nothing is precomputed "
  "and no source is ever written back onto the enquiry record."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Capture is a lookup, stitching is an exact "
  "match, and the rules are arithmetic.",
  "<strong>The tempting use</strong> is classifying free-text 'how did you hear about us' answers "
  "into channels, and it is defensible &mdash; but keep the raw text, because the "
  "classification loses exactly the specifics that make those answers valuable.",
  "<strong>The wrong use</strong> is algorithmic attribution, for the reasons in Part 4: at these "
  "volumes it produces an unexplainable number over data with the same blind spots.",
  "<strong>A second wrong use</strong> is inferring a probable source for unattributed enquiries. "
  "That converts an honest unknown into a confident guess, which is the failure this system "
  "exists to prevent.",
  "<strong>The cost page assumes none</strong>, which is why writes are the only variable band."],
 gotchas=[
  "Normalise sources at capture. Three spellings of one channel is the most common reason an "
  "attribution report is quietly wrong.",
  "Never write an attributed source onto the enquiry record. Something will read it, and then the "
  "rule can no longer be changed.",
  "Make stitching additive. A merge that deletes visitor ids makes strict-mode reports impossible "
  "to recompute.",
  "Store the raw referrer host as well as the normalised source, so a normalisation mistake can "
  "be fixed retrospectively.",
  "Put the unattributed share in the report generator itself, not in the dashboard template. If "
  "it lives in the template, someone will remove it."],
))
