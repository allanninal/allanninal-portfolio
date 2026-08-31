"""Day 110 -- 2026-08-12 -- Quote comparer."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "quote-comparer"
NAME = "Quote comparer"

SPEC = {
 "slug": SLUG, "date": "2026-08-12", "name": NAME,
 "tagline": ("Puts three supplier quotes for the same job side by side, shows what each one "
             "leaves out, and refuses to name a winner -- because the cheapest quote is almost "
             "always cheapest for a reason nobody has read yet."),
 "lede": ("A small system that reads the quotes arriving as PDFs and email attachments, lines "
          "them up against each other, and makes the differences visible: what is included, what "
          "is quietly excluded, and which numbers cannot honestly be compared at all. It never "
          "picks. Seven posts on the same system, one diagram at a time, with a cost breakdown "
          "and an engineering reference at the end."),
 "keywords": ["quote comparison", "procurement", "document extraction", "suppliers", "purchasing",
              "serverless"],
 "icons": ["doc", "scale", "search"],
 "faq": [
  ("What is a quote comparer?",
   "A small serverless system that reads supplier quotes for the same job, normalises them into "
   "comparable line items, and presents the differences -- including the exclusions -- without "
   "recommending one."),
  ("Why not just compare the totals?",
   "Because the totals describe different jobs. One quote includes making good and waste removal, "
   "another does not, and the gap between them is usually larger than the gap in price."),
  ("Does it choose the best quote?",
   "No, and that is a deliberate design decision rather than a limitation. It surfaces the "
   "differences and the person who knows the job decides."),
  ("What happens when a quote cannot be compared?",
   "It is marked not comparable, with the reason. That is a more useful output than a number "
   "produced by guessing at what a vague line item covers."),
  ("What does it cost to run?",
   "A few dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "quote-comparer-on-aws",
 "title": "A quote comparer on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Reads supplier quotes, lines them up, shows what each excludes, and never names a "
          "winner. AWS, about $3 a month."),
 "og": ("The cheapest quote is usually cheapest because it excludes something. Finding what, "
        "not ranking totals, is the job."),
 "abstract": ("The whole system on one page -- read, normalise, compare -- and why the component "
              "that picks a winner was deliberately never built."),
 "lede": ("Three quotes come in for the same bathroom refit: eleven thousand, thirteen and a "
          "half, and fourteen two. The eleven looks like the obvious answer for about a minute, "
          "until somebody notices it does not mention removing the old suite, tiling, or making "
          "good afterwards. This post walks through a small system that finds that in the first "
          "minute rather than the third week."),
 "tags": ["quote comparison", "procurement", "document extraction", "suppliers", "purchasing",
          "serverless"],
 "takeaways": [
  "Compare line items and exclusions, not totals. The totals describe different jobs.",
  "Every extracted number keeps a pointer back to where it came from in the document.",
  "Units have to be normalised before anything can be compared at all.",
  "The system never recommends. It surfaces differences and stops.",
  "Designed on AWS for about $3 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Quotes arrive", "sub": ["PDF, email, photo"], "icon": "doc"},
      {"title": "What was asked for", "sub": ["the original spec"], "icon": "form"},
      {"title": "Whoever decides", "sub": ["reads a comparison"], "icon": "person"}],
    "inside": [
      {"title": "Reader", "sub": ["lines, units,", "where each came from"], "icon": "search"},
      {"title": "Normaliser", "sub": ["same units,", "same scope"], "icon": "filter"},
      {"title": "Comparer", "sub": ["differences and gaps,", "no winner"], "icon": "scale"}],
    "edges": [{"from": 0, "to": 0, "label": "documents"},
              {"from": 1, "to": 1, "label": "the scope"},
              {"from": 2, "to": 2, "label": "a comparison", "up": True}],
    "note": "There is no fourth box that ranks them. That absence is the design."}),
   "Three things outside the account, three pieces inside it. What is missing on the right &mdash; "
   "a scoring or ranking component &mdash; was considered and deliberately left out.",
   "System: quotes read, normalised and compared without ranking",
   "Three boxes across the top sit outside the AWS account. On the left, Quotes arrive as PDF, "
   "email or photo. In the middle, What was asked for: the original spec. On the right, Whoever "
   "decides, who reads a comparison. Each connects by an arrow to the AWS account container "
   "below. Documents flow down into the account. The scope feeds in. A comparison goes back out. "
   "Inside the AWS account are three components in a row. On the left, the Reader, extracting "
   "lines, units and where each came from. In the middle, the Normaliser, putting everything in "
   "the same units and the same scope. On the right, the Comparer, showing differences and gaps "
   "with no winner. A note at the bottom says there is no fourth box that ranks them, and that "
   "absence is the design."),
  ("h3", "Why there is no ranking step"),
  ("p", "It is the first thing anyone asks for and it is the wrong thing to build. A ranking "
        "requires weighing price against scope against risk against how much you trust the "
        "supplier, and three of those four are not in the documents. A system that ranks anyway "
        "is applying weights somebody invented, invisibly, to a decision worth thousands."),
  ("p", "The version that helps is the one that makes the differences unmissable in ninety "
        "seconds instead of a fortnight. Everyone who has compared quotes by hand knows the "
        "failure mode is not bad judgement; it is missing the line on page four that says "
        "\"excludes disconnection of existing services\"."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The reader.</strong> Pulls line items, quantities, units and totals out of whatever "
   "arrived, keeping a pointer back to the page and line each came from. Part 2.",
   "<strong>The normaliser.</strong> Converts units, aligns line items to the requested scope, "
   "and identifies what each quote does not cover. Part 3.",
   "<strong>The comparer.</strong> Produces the side-by-side, with the exclusions given the same "
   "visual weight as the prices. Parts 4 and 5.",
  ]),
  ("h2", "Three quotes, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Three PDFs", "sub": ["11.0k, 13.5k, 14.2k"], "icon": "doc"},
      {"title": "Read", "sub": ["47 line items"], "icon": "search"},
      {"title": "Normalised", "sub": ["per m2, per unit"], "icon": "filter"},
      {"title": "Gaps found", "sub": ["cheapest excludes 4"], "icon": "alarm"},
      {"title": "Compared", "sub": ["the person decides"], "icon": "scale"}],
    "title": "THREE QUOTES, END TO END",
    "note": "The fourth box is the whole value. The fifth is a table anybody could have drawn."}),
   "The same system as one line. Everything before the fourth box is preparation for the one "
   "output that changes a decision.",
   "Three supplier quotes read, normalised and compared in five stages",
   "A horizontal row of five boxes joined by arrows. Three PDFs: at eleven thousand, thirteen and "
   "a half thousand, and fourteen thousand two hundred. Read: forty-seven line items. Normalised: "
   "per square metre and per unit. Gaps found: the cheapest excludes four items. Compared: the "
   "person decides. A note says the fourth box is the whole value, and the fifth is a table "
   "anybody could have drawn."),
  ("h2", "In plain words"),
  ("p", "Three builders quote for the same bathroom. The first is eleven thousand and reads as a "
        "single page: supply and fit, one number. The second is thirteen and a half over four "
        "pages with twenty-two line items. The third is fourteen two, similar detail, plus a page "
        "of terms."),
  ("p", "The system reads all three, converts the tiling from \"the bathroom\" to eleven square "
        "metres using the spec, and lines up what each covers. Then it produces the finding: the "
        "cheapest quote does not mention removing the existing suite, does not include waste "
        "disposal, does not include making good the walls, and its terms make the customer "
        "responsible for materials delivery."),
  ("p", "It does not say the eleven thousand quote is worse. It might be a perfectly good "
        "arrangement with a builder who assumed those things were understood, and it is now a "
        "conversation with a specific list of four questions rather than a number that looked "
        "cheap. That conversation is the output."),
  ("callout", "Design rules that shaped every decision", [
   "Never rank. Surface the differences and stop.",
   "Every number keeps a pointer to the page and line it was read from.",
   "An exclusion is a finding with the same weight as a price.",
   "A line that cannot be normalised is reported as not comparable, never estimated.",
   "Nothing is inferred about what a supplier \"probably\" includes.",
   "The original documents are always one click away from every number.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Comparing quotes is a task people are already reasonably good at and have no time for. "
        "The mistakes are not analytical; they are attentional, and they happen on page four of "
        "the third document at half past five. That is a very different problem from the one an "
        "automated scoring tool solves."),
  ("p", "So the design puts almost all of its effort into extraction fidelity and exclusion "
        "detection, and none into judgement. It is a system for making sure nobody misses "
        "anything, run by somebody who already knows what matters."),
  ("p", "The next four posts walk through each piece: how a quote gets read, how quotes are made "
        "comparable, how the comparison is presented, and what happens when a quote cannot be "
        "compared at all. One diagram per post, a cost breakdown, and an engineering reference at "
        "the end."),
 ],
},
{
 "slug": "how-a-quote-gets-read",
 "title": "How a quote gets read",
 "nav": "How it is read",
 "read": 5, "words": 750,
 "desc": ("Extracting line items from documents that share no format, keeping provenance on every "
          "number, and what happens to the ones it cannot read."),
 "og": ("A number with no pointer back to the page it came from is a number nobody can check, "
        "which makes it worse than no number."),
 "abstract": ("How line items are pulled from documents with no shared structure, why every value "
              "keeps a page and line reference, and how unreadable quotes are handled."),
 "lede": ("Supplier quotes have no shared format at all. One is a spreadsheet export, one is a "
          "PDF from an accounting package, one is a photograph of a handwritten sheet, and one is "
          "four sentences in the body of an email. The reader has to cope with all of them and be "
          "checkable afterwards."),
 "tags": ["document extraction", "OCR", "provenance", "procurement", "quotes", "serverless"],
 "takeaways": [
  "Every extracted value stores the page, the line and the raw text it came from.",
  "The raw text is kept verbatim, not just the parsed number.",
  "Quantities and units are extracted separately; a number without a unit is incomplete.",
  "Terms pages are read too. That is where the exclusions usually live.",
  "An unreadable quote is flagged for a person, never partially guessed at.",
 ],
 "blocks": [
  ("h2", "One document to line items"),
  ("fig", ("chain", {
    "entry": {"title": "A quote arrives", "sub": ["PDF, image, email body"], "icon": "doc"},
    "steps": [
      {"title": "Is there a text layer?", "sub": ["most PDFs have one"], "icon": "branch",
       "exit": {"title": "OCR the pages", "sub": ["and mark it OCR-derived"], "icon": "image",
                "label": "no"}},
      {"title": "Find the line items", "sub": ["table or prose"], "icon": "search"},
      {"title": "Each has a unit?", "sub": ["m2, each, day, sum"], "icon": "branch",
       "exit": {"title": "Flag as unclear", "sub": ["do not assume"], "icon": "question",
                "label": "no"}},
      {"title": "Read the terms pages", "sub": ["exclusions live here"], "icon": "doc"},
      {"title": "Store with provenance", "sub": ["page, line, raw text"], "icon": "database"}],
    "note": "OCR-derived values are marked, because a person checking should know which they are."}),
   "How one document becomes a set of checkable line items. The provenance in the last box is "
   "what makes every later number defensible.",
   "How a supplier quote is read into line items with provenance",
   "A vertical chain of five steps entered by a box labelled A quote arrives as a PDF, image or "
   "email body. Step one asks whether there is a text layer, noting most PDFs have one; if not it "
   "exits to OCR the pages and mark it OCR-derived. Step two finds the line items, whether in a "
   "table or in prose. Step three asks whether each has a unit such as square metres, each, day "
   "or sum; if not it exits to Flag as unclear, and does not assume. Step four reads the terms "
   "pages, where exclusions live. Step five stores everything with provenance: page, line and raw "
   "text. A note says OCR-derived values are marked, because a person checking should know which "
   "they are."),
  ("h3", "Provenance on everything"),
  ("p", "Every stored value carries three things beyond the value itself: which page it was on, "
        "which line, and the raw text as it appeared. That last one matters more than it sounds. "
        "\"Tiling &mdash; 11m2 &mdash; &pound;840\" parses cleanly; \"Tiling to splashback area "
        "only, POA\" does not, and the difference is invisible once both have been reduced to a "
        "row in a table."),
  ("p", "The practical payoff is that the comparison can render every figure as a link back to "
        "the page it came from. Somebody querying a number resolves it in five seconds instead of "
        "reopening three PDFs, and that turns out to be the difference between a comparison "
        "people trust and one they redo by hand."),
  ("h3", "The terms pages"),
  ("p", "The exclusions are almost never in the line items. They are in the paragraph after the "
        "total, or on a separate terms page, or in a single sentence like \"price assumes clear "
        "access and existing services in working order\". Reading only the priced table is the "
        "single most common way an automated comparison goes wrong."),
  ("p", "So the terms text is extracted as its own object, associated with the quote rather than "
        "with any line, and every sentence containing an exclusionary construction is kept "
        "verbatim for the normaliser to work on. No summarising at this stage; the wording is the "
        "evidence."),
  ("h2", "When it cannot read something"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Photo at an angle", "sub": ["half legible"], "icon": "image"},
      {"title": "Handwritten total", "sub": ["8 or 3?"], "icon": "question"},
      {"title": "Do not guess", "sub": ["ever"], "icon": "stop"},
      {"title": "Flag the quote", "sub": ["with the region"], "icon": "alarm"},
      {"title": "A person reads it", "sub": ["30 seconds"], "icon": "person"}],
    "title": "THE ONE THING IT MUST NOT DO",
    "note": "A confidently wrong total in a comparison is worse than no comparison."}),
   "The refusal path. A person spending thirty seconds on an ambiguous figure is cheap; a wrong "
   "figure that nobody questions is not.",
   "How an unreadable value is escalated rather than guessed",
   "A horizontal row of five boxes. Photo at an angle: half legible. Handwritten total: is it an "
   "eight or a three? Do not guess: ever. Flag the quote, with the region highlighted. A person "
   "reads it: thirty seconds. A note says a confidently wrong total in a comparison is worse than "
   "no comparison."),
  ("p", "The flag is specific: it names the page, crops the region, and states what was "
        "ambiguous. \"Could not read quote 3\" is an unhelpful message that gets ignored; \"page "
        "2, line 7 &mdash; is this &pound;830 or &pound;530?\" gets answered immediately."),
  ("h3", "Keeping the original"),
  ("p", "The source document is stored unmodified alongside the extraction, permanently for as "
        "long as the quote is live and for a period after the job. Extraction improves, formats "
        "change, and a disagreement six months later is settled by the original rather than by "
        "the parse."),
  ("p", "Next: making three quotes comparable."),
 ],
},
{
 "slug": "how-quotes-get-made-comparable",
 "title": "How quotes get made comparable",
 "nav": "How they are made comparable",
 "read": 6, "words": 780,
 "desc": ("Aligning line items to a scope, converting units, and the exclusion detection that is "
          "the point of the whole exercise."),
 "og": ("You cannot compare a quote against another quote. You compare each one against what you "
        "asked for, and the gaps are the answer."),
 "abstract": ("Why quotes are aligned to the requested scope rather than to each other, how units "
              "are converted, how exclusions are detected, and the assumptions that hide inside a "
              "price."),
 "lede": ("The instinct is to line the three quotes up against each other, and it does not work, "
          "because they have different numbers of lines describing different groupings of work. "
          "The trick is to compare each one against the thing you asked for, separately, and then "
          "compare the results."),
 "tags": ["procurement", "normalisation", "scope", "exclusions", "quotes", "serverless"],
 "takeaways": [
  "Align each quote to the requested scope, not to the other quotes.",
  "Every scope item ends up included, excluded, or unclear -- never silently absent.",
  "Unit conversion needs the spec's quantities; a quote saying \"the bathroom\" is not a number.",
  "Exclusions come from three places: stated, implied by omission, and buried in terms.",
  "An assumption in a quote is a price condition, and it belongs in the comparison.",
 ],
 "blocks": [
  ("h2", "Compare against the ask, not each other"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Quote A -- 1 line", "sub": ["supply and fit"], "icon": "doc",
       "label": "sparse"},
      {"title": "Quote B -- 22 lines", "sub": ["itemised"], "icon": "doc", "label": "detailed"},
      {"title": "Quote C -- 14 lines", "sub": ["plus 2 terms pages"], "icon": "doc",
       "label": "detailed"}],
    "target": {"title": "The requested scope", "sub": ["9 items, from the spec"], "icon": "form",
               "then": {"title": "Three alignments", "sub": ["each scope item resolved"],
                        "icon": "scale"}},
    "note": "Nine rows, three columns, every cell filled. Nothing is left implicit."}),
   "Why alignment runs through the scope. Three quotes with one, twenty-two and fourteen lines "
   "have no common structure; the requested scope does.",
   "Three differently structured quotes aligned against one requested scope",
   "Three boxes stacked on the left. Quote A with one line, supply and fit, labelled sparse. "
   "Quote B with twenty-two itemised lines, labelled detailed. Quote C with fourteen lines plus "
   "two terms pages, labelled detailed. All three converge on The requested scope, which has nine "
   "items taken from the spec, and that leads down to Three alignments, with each scope item "
   "resolved. A note says nine rows, three columns, every cell filled, and nothing is left "
   "implicit."),
  ("h3", "Three outcomes per cell, never two"),
  ("p", "For each scope item and each quote, the answer is included, excluded, or unclear. The "
        "third one is essential and is what most comparison spreadsheets lack: a blank cell means "
        "either \"they did not include it\" or \"nobody knows\", and treating those as the same "
        "thing produces confident conclusions from missing information."),
  ("table", ["Scope item", "Quote A", "Quote B", "Quote C"], [
   ["Remove existing suite", "Unclear &mdash; not mentioned", "Included &mdash; p1 l3",
    "Included &mdash; p1 l2"],
   ["Tiling, 11m&sup2;", "Included &mdash; in \"fit\"", "Included &mdash; p2 l9",
    "Included &mdash; p1 l7"],
   ["Waste removal", "Excluded &mdash; terms, p1",
    "Included &mdash; p3 l4", "Unclear &mdash; not mentioned"],
   ["Making good walls", "Unclear &mdash; not mentioned", "Included &mdash; p3 l1",
    "Excluded &mdash; terms, p5"],
   ["Electrical certificate", "Unclear", "Excluded &mdash; p4 l2", "Included &mdash; p2 l11"],
  ]),
  ("p", "That table is the product. It took the reader and the normaliser to produce and anyone "
        "can act on it: three specific questions for quote A, one for quote C, and a clear "
        "picture that quote B is the one being compared against."),
  ("h3", "Units need the spec"),
  ("p", "A quote saying \"tiling &mdash; the bathroom &mdash; &pound;840\" has no unit price "
        "until something supplies the eleven square metres, and that something is the original "
        "spec rather than the quote. This is why the requested scope is an input to the system "
        "rather than something inferred from the documents."),
  ("p", "Where the spec does not give a quantity, the unit price is left uncomputed rather than "
        "estimated. A per-square-metre figure derived from a guessed area is precisely the kind "
        "of number that gets quoted back in a negotiation and cannot be defended."),
  ("h2", "Where exclusions hide"),
  ("fig", ("chain", {
    "entry": {"title": "A quote, fully read", "sub": ["lines and terms"], "icon": "doc"},
    "steps": [
      {"title": "Stated exclusions", "sub": ["'excludes...'"], "icon": "search",
       "side": {"title": "Easy", "sub": ["and rare"], "icon": "check"}},
      {"title": "Scope items absent", "sub": ["asked for, not mentioned"], "icon": "question",
       "side": {"title": "Unclear", "sub": ["not excluded"], "icon": "alarm"}},
      {"title": "Conditional prices", "sub": ["'assumes clear access'"], "icon": "branch"},
      {"title": "Provisional sums", "sub": ["'allow 400 for tiles'"], "icon": "money"},
      {"title": "All four, in the table", "sub": ["with their wording"], "icon": "scale"}],
    "note": "The second and fourth are where a cheap quote usually turns out not to be."}),
   "The four kinds of exclusion, in the order they are easy to miss. Provisional sums in "
   "particular read as included and are not.",
   "The four places exclusions hide in a supplier quote",
   "A vertical chain of five steps entered by a box labelled A quote, fully read, with lines and "
   "terms. Step one finds stated exclusions, phrased as excludes something, with a side note "
   "saying these are easy and rare. Step two finds scope items that are absent, asked for but not "
   "mentioned, with a side note saying these are unclear rather than excluded. Step three finds "
   "conditional prices, such as assumes clear access. Step four finds provisional sums, such as "
   "allow four hundred for tiles. Step five puts all four in the table with their wording. A note "
   "says the second and fourth are where a cheap quote usually turns out not to be."),
  ("h3", "Provisional sums deserve their own treatment"),
  ("p", "\"Allow &pound;400 for tiles\" is not a price; it is a placeholder that will become "
        "whatever the tiles cost. A quote containing three provisional sums has a total that "
        "means considerably less than a quote with none, and comparing the two totals directly is "
        "the mistake the whole system exists to prevent."),
  ("p", "So provisional sums are pulled out and shown as a separate figure: firm price, "
        "provisional sums, and total. Two quotes at thirteen thousand where one has two hundred "
        "provisional and the other has two thousand eight hundred are not the same quote, and "
        "that is visible at a glance rather than on the fourth read."),
  ("h3", "Assumptions are price conditions"),
  ("p", "\"Assumes existing pipework is sound\" and \"assumes clear access from the road\" are "
        "conditions on the price, and they are the mechanism by which a quote becomes a different "
        "number once work starts. They belong in the comparison as their own row, phrased in the "
        "supplier's words."),
  ("p", "Next: what the comparison looks like."),
 ],
},
{
 "slug": "how-the-comparison-is-presented",
 "title": "How the comparison is presented",
 "nav": "How it is presented",
 "read": 5, "words": 740,
 "desc": ("Why the exclusions go above the prices, how the totals are shown honestly, and the "
          "recommendation that is deliberately missing."),
 "og": ("Put the prices at the top and everyone reads the prices. The layout is the argument."),
 "abstract": ("Why the exclusion table comes before the prices, how totals are presented with "
              "their provisional content visible, and why no recommendation appears anywhere."),
 "lede": ("Everything up to here is preparation. The presentation is where a comparison either "
          "changes a decision or gets skimmed for the smallest number, and the difference is "
          "almost entirely about what appears first."),
 "tags": ["procurement", "reporting", "decisions", "presentation", "quotes", "serverless"],
 "takeaways": [
  "Exclusions and unclears go above the prices, always.",
  "Show firm price and provisional sums separately, never just the total.",
  "Attach the questions each quote raises, phrased ready to send.",
  "Every figure links back to the page it came from.",
  "No recommendation, no score, no star rating anywhere on the page.",
 ],
 "blocks": [
  ("h2", "What comes first"),
  ("callout", "The order on the page, top to bottom", [
   "<strong>1. What is unclear.</strong> Every scope item nobody can resolve from the documents, "
   "per quote, as a question ready to ask.",
   "<strong>2. What is excluded.</strong> Stated exclusions and conditions, in the supplier's own "
   "wording.",
   "<strong>3. Provisional sums.</strong> Per quote, totalled separately.",
   "<strong>4. The scope table.</strong> Nine rows, three columns, every cell resolved.",
   "<strong>5. The prices.</strong> Last, and split into firm and provisional.",
   "<strong>No recommendation</strong> anywhere, and no ordering of the columns by price.",
  ]),
  ("p", "Putting the prices last is a small decision that does most of the work. Anybody who "
        "wants the numbers scrolls to them in a second, and on the way past they have seen that "
        "the cheapest quote has four unresolved items. Putting them first means many people never "
        "read anything else, which is the behaviour every comparison spreadsheet in the world "
        "produces."),
  ("h2", "Showing the totals honestly"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Quote A", "parts": [("firm", 11000), ("prov", 0), ("gap", 2400)]},
      {"label": "Quote B", "parts": [("firm", 13100), ("prov", 400), ("gap", 0)]},
      {"label": "Quote C", "parts": [("firm", 12800), ("prov", 1400), ("gap", 600)]}],
    "series": [("firm", "Firm price, as quoted", "#7AA116"),
               ("prov", "Provisional sums", "#ED7100"),
               ("gap", "Excluded or unclear -- estimated by us, not quoted", "#DD344C")],
    "unit": "£",
    "note": "The red band is our estimate of the gap, labelled as ours. It is not part of the quote."}),
   "The three quotes with what they do not cover added on. The red band is explicitly the "
   "reader's own estimate rather than anything the supplier said, and it is labelled that way "
   "everywhere it appears.",
   "Three quotes shown as firm price, provisional sums and the estimated gap",
   "A stacked bar chart with three bars in pounds. Three series: Firm price as quoted in green, "
   "Provisional sums in orange, and Excluded or unclear, estimated by us and not quoted, in red. "
   "Quote A shows eleven thousand firm, no provisional sums, and a red gap of two thousand four "
   "hundred. Quote B shows thirteen thousand one hundred firm, four hundred provisional, and no "
   "gap. Quote C shows twelve thousand eight hundred firm, one thousand four hundred provisional, "
   "and a six hundred gap. A note says the red band is our estimate of the gap, labelled as ours, "
   "and is not part of the quote."),
  ("p", "This is the one place the system does something that looks like judgement, and it is "
        "worth being careful about. The red band is a rough cost for the excluded items, and it "
        "is shown because the alternative &mdash; three bars of eleven, thirteen and twelve eight "
        "&mdash; is actively misleading."),
  ("p", "The safeguards are that it is a different colour, labelled as an estimate by us rather "
        "than a quoted figure, and excluded from every total that gets quoted anywhere else. It "
        "answers \"roughly how big is the gap\" and nothing more."),
  ("h3", "The questions, ready to send"),
  ("p", "Each unclear cell generates a question in plain language, grouped by supplier: \"Does "
        "your price include removing the existing suite and disposing of it? Does it include "
        "making good the walls after removal?\" Copy, paste, send."),
  ("p", "That is a surprisingly large part of the value. The reason unclear items stay unclear is "
        "not that nobody wants to ask; it is that writing three separate emails is a twenty-"
        "minute job at the end of a day when the quotes are already late."),
  ("h2", "The recommendation that is not there"),
  ("fig", ("strip", {
    "stages": [
      {"title": "It could rank", "sub": ["the data is there"], "icon": "chart"},
      {"title": "On what weights?", "sub": ["price vs risk vs trust"], "icon": "branch"},
      {"title": "Two are not in", "sub": ["the documents"], "icon": "question"},
      {"title": "So it does not", "sub": ["rank at all"], "icon": "stop"},
      {"title": "The gaps are the output", "sub": ["a person decides"], "icon": "person"}],
    "title": "WHY THERE IS NO RECOMMENDED QUOTE",
    "note": "A ranking would apply invisible weights to a decision worth thousands."}),
   "The reasoning behind the missing feature. It is technically easy and it would make the output "
   "less useful, which is an unusual combination worth stating explicitly.",
   "Why the quote comparer does not recommend a winner",
   "A horizontal row of five boxes. It could rank: the data is there. On what weights: price "
   "versus risk versus trust. Two are not in the documents. So it does not rank at all. The gaps "
   "are the output, and a person decides. A note says a ranking would apply invisible weights to "
   "a decision worth thousands."),
  ("p", "The pressure to add it never goes away, and the useful counter is to ask what the "
        "ranking would be used for. If the answer is \"to pick without reading\", the ranking is "
        "the problem. If the answer is \"to sort the list\", sorting by firm price is available "
        "and honest, and does not pretend to be a judgement."),
  ("p", "Next: what happens when a quote will not compare at all."),
 ],
},
{
 "slug": "when-a-quote-cannot-be-compared",
 "title": "When a quote cannot be compared",
 "nav": "When it cannot compare",
 "read": 5, "words": 720,
 "desc": ("Quotes for a different job, quotes with one number, quotes that arrived after the "
          "decision, and why 'not comparable' is a good answer."),
 "og": ("Not comparable is a finding. Forcing a number onto it is how a comparison becomes "
        "confidently wrong."),
 "abstract": ("The four situations where comparison genuinely fails, what the system says "
              "instead, and why that output is more useful than a forced number."),
 "lede": ("A meaningful share of quotes cannot be compared to the others in any honest way, and "
          "what the system does in those cases determines whether anybody trusts it in the cases "
          "where it can."),
 "tags": ["procurement", "edge cases", "refusal", "quotes", "decisions", "serverless"],
 "takeaways": [
  "A quote for a different scope is not a cheaper quote; it is a different job.",
  "A single-number quote can be listed but not aligned, and the report says so.",
  "Different payment terms change the real cost and are shown rather than folded in.",
  "A quote that arrives after a decision is still recorded, for the next time.",
  "Refusing to compare is a result, and it is stated as one.",
 ],
 "blocks": [
  ("h2", "The four cases"),
  ("fig", ("chain", {
    "entry": {"title": "A quote to compare", "sub": ["read and normalised"], "icon": "doc"},
    "steps": [
      {"title": "Same scope?", "sub": ["or a different job"], "icon": "branch",
       "exit": {"title": "Different job", "sub": ["shown separately"], "icon": "stop",
                "label": "no"}},
      {"title": "Any line detail?", "sub": ["or one number"], "icon": "branch",
       "exit": {"title": "Cannot align", "sub": ["listed, not compared"], "icon": "question",
                "label": "no"}},
      {"title": "Comparable terms?", "sub": ["payment, timing"], "icon": "branch",
       "exit": {"title": "Shown as a difference", "sub": ["never folded into price"],
                "icon": "alarm", "label": "no"}},
      {"title": "Still current?", "sub": ["quotes expire"], "icon": "branch",
       "exit": {"title": "Marked expired", "sub": ["kept for reference"], "icon": "clock",
                "label": "no"}},
      {"title": "Compare it", "sub": ["fully aligned"], "icon": "scale"}],
    "note": "Each exit is a stated outcome on the report, not a quiet omission."}),
   "The four ways a quote drops out of the comparison. Every exit produces visible output; none "
   "of them silently removes a quote from the page.",
   "The four cases where a quote cannot be compared to the others",
   "A vertical chain of five steps entered by a box labelled A quote to compare, read and "
   "normalised. Step one asks whether it is the same scope or a different job; if different it "
   "exits to Different job, shown separately. Step two asks whether there is any line detail or "
   "just one number; if just one number it exits to Cannot align, listed but not compared. Step "
   "three asks whether the terms are comparable in payment and timing; if not it exits to Shown "
   "as a difference, never folded into price. Step four asks whether it is still current, since "
   "quotes expire; if not it exits to Marked expired, kept for reference. Step five compares it, "
   "fully aligned. A note says each exit is a stated outcome on the report, not a quiet "
   "omission."),
  ("h3", "The different-job case"),
  ("p", "This is the most valuable refusal and the easiest to get wrong. A builder who quotes "
        "eight thousand for the bathroom because they have proposed keeping the existing layout "
        "has not undercut anybody; they have answered a different question, and possibly a better "
        "one."),
  ("p", "Presenting that as the cheapest option in a price column is a serious distortion. "
        "Presenting it in its own section headed \"proposes a different approach\", with what "
        "differs listed, turns it into the useful thing it might actually be."),
  ("h3", "Payment terms are cost"),
  ("p", "Fifty per cent up front against staged payments on completion of each phase is a real "
        "difference in cash flow and in risk, and there is no defensible exchange rate between "
        "them and price. The system shows the terms as their own row and leaves the weighing to "
        "the person, which is the same principle as the missing recommendation."),
  ("p", "The same applies to timing. A quote that can start in three weeks and one that can start "
        "in three months are not competing on price at all if the bathroom is currently unusable."),
  ("h2", "What 'not comparable' looks like"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Quote D", "sub": ["one number, 9.2k"], "icon": "doc"},
      {"title": "No line detail", "sub": ["nothing to align"], "icon": "question"},
      {"title": "Not comparable", "sub": ["stated plainly"], "icon": "stop"},
      {"title": "Still listed", "sub": ["with its total"], "icon": "scale"},
      {"title": "One question", "sub": ["'can you itemise?'"], "icon": "email"}],
    "title": "A QUOTE THAT WILL NOT ALIGN",
    "note": "Listed, not hidden. The reader can see it exists and see why it is not in the table."}),
   "How an unalignable quote appears. It stays on the page with its total and its reason, because "
   "removing it would misrepresent the field of options.",
   "How a quote with no line detail is presented as not comparable",
   "A horizontal row of five boxes. Quote D: one number, nine thousand two hundred. No line "
   "detail: nothing to align. Not comparable: stated plainly. Still listed, with its total. One "
   "question: can you itemise? A note says it is listed rather than hidden, so the reader can see "
   "it exists and see why it is not in the table."),
  ("p", "The temptation is to drop unalignable quotes so the table looks clean, and it produces a "
        "page that misrepresents what was received. Somebody looking at three neat columns has no "
        "way of knowing a fourth supplier quoted nine two."),
  ("h3", "Expired quotes are kept"),
  ("p", "Quotes have validity periods and they run out, usually while somebody is deciding. An "
        "expired quote is marked rather than deleted, because it is the best available evidence "
        "of what that supplier charges and it is the starting point for the next conversation."),
  ("p", "Over a couple of years this accumulates into something more useful than any individual "
        "comparison: a record of what each supplier quoted for what, with their exclusions, which "
        "makes the fourth job easier than the first."),
  ("h2", "Refusal as a result"),
  ("p", "The theme across all of this is that the system's outputs include \"I cannot answer "
        "that\", and it says so in the same place and with the same prominence as the answers it "
        "can give. That is what makes the answers worth anything."),
  ("p", "A comparison tool that always produces a clean table teaches people to trust clean "
        "tables. One that occasionally says \"these two cannot be compared, here is why\" teaches "
        "people to read the reason, which is the habit that actually protects the decision."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="quote",
 volumes=[(20, "20 quotes"), (60, "60 quotes"), (250, "250 quotes")],
 read_each=2.2,
 msgs_each=0.0,
 lede=("Quotes are low volume and each one is a multi-page document, so the read is the whole "
       "bill. Sixty quotes a month is a busy small builder or a procurement function at a "
       "twenty-person company. Here is where each cent goes."),
 takeaway_extra=("Document reads dominate completely. Everything else is under a dollar at every "
                 "volume."),
 risks=[
  "<strong>Re-reading a document on every comparison.</strong> The extraction is cached against "
  "the document hash. Without that, one quote compared four times costs four reads.",
  "<strong>OCR on documents that have a text layer.</strong> Checking first is one line and "
  "removes most of the OCR bill.",
  "<strong>Storing originals in Standard forever.</strong> Quotes are read once and then rarely. "
  "A lifecycle rule to Infrequent Access after ninety days is worth setting on day one.",
 ],
 per_unit_note=("There is no messaging line: the comparison is a page, not an email. The read "
                "band assumes a multi-page document and the terms pages, which is where the "
                "tokens go."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="qc",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the provenance record, and where the model is and is not used."),
 outside=[
  {"title": "Quote documents", "sub": ["email and upload"], "icon": "doc"},
  {"title": "The requested scope", "sub": ["entered once per job"], "icon": "form"},
  {"title": "The comparison page", "sub": ["read by a person"], "icon": "scale"}],
 inside=[
  {"title": "S3 + Textract", "sub": ["originals,", "text and layout"], "icon": "storage"},
  {"title": "Lambda x3", "sub": ["read, align, render"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["quotes, jobs"], "icon": "database"}],
 note="us-east-1. One account. Originals kept immutable; extractions cached by document hash.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Quote documents arriving by email and "
  "upload. The requested scope, entered once per job. And The comparison page, read by a person. "
  "Inside the account, three groups. S3 holding originals with Textract producing text and "
  "layout. Three Lambda functions named read, align and render. And two DynamoDB tables named "
  "quotes and jobs. A note gives the region as us-east-1, one account, and states that originals "
  "are kept immutable and extractions are cached by document hash."),
 functions=[
  ["<code>qc-read</code>", "S3 put on the originals bucket",
   "Textract, then one model call per document to structure lines and terms",
   "300s / 2048&nbsp;MB"],
  ["<code>qc-align</code>", "DynamoDB stream on quotes",
   "Aligns each quote to the job scope; classifies every cell as included, excluded or unclear",
   "60s / 1024&nbsp;MB"],
  ["<code>qc-render</code>", "API, on request",
   "Builds the comparison page and the per-supplier questions", "30s / 1024&nbsp;MB"]],
 roles=[
  ["<code>qc-read-role</code>",
   "<code>s3:GetObject</code>, <code>textract:*Document*</code>, "
   "<code>bedrock:InvokeModel</code>, <code>dynamodb:PutItem</code>",
   "The originals bucket; one model id; the quotes table"],
  ["<code>qc-align-role</code>", "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>",
   "Quotes and jobs"],
  ["<code>qc-render-role</code>", "<code>dynamodb:Query</code>, <code>s3:GetObject</code>",
   "Read-only; presigned links back to the original pages"]],
 tables=[
  ("Table: quotes",
   "PK   job_id            S   bathroom_ashford_2026_08\n"
   "SK   quote_id          S   supplier#received_at\n"
   "     supplier          S   as it appears on the document\n"
   "     doc_key           S   s3 key of the original, immutable\n"
   "     doc_hash          S   sha256; the extraction cache key\n"
   "     ocr_derived       BOOL true if there was no text layer\n"
   "     lines             L   [{text, qty, unit, amount, page, line}]\n"
   "     terms             L   [{sentence, page}] -- verbatim, unsummarised\n"
   "     provisional       N   total of provisional sums\n"
   "     firm              N   total excluding provisional sums\n"
   "     valid_until       S   from the document, if stated\n"
   "     status            S   comparable | different_scope | no_detail | expired\n\n"
   "`lines` keeps page and line on every entry. That is what makes each\n"
   "figure on the comparison page a link back to where it came from."),
  ("Table: jobs",
   "PK   job_id            S   bathroom_ashford_2026_08\n"
   "     scope             L   [{item, qty, unit}] -- 9 rows, entered once\n"
   "     alignment         M   {quote_id: {item: included|excluded|unclear}}\n"
   "     evidence          M   {quote_id: {item: {page, line, text}}}\n"
   "     questions         M   {quote_id: [question strings]}\n\n"
   "`evidence` exists so that 'included' is never an unsupported claim:\n"
   "every positive cell names the line that justifies it.")],
 inbound=[
  "<strong>Documents arrive by email or upload</strong> and land in S3 unmodified. Nothing writes "
  "back to the originals bucket.",
  "<strong>Extraction is cached by document hash</strong>, so re-comparing a job never re-reads a "
  "document that has not changed.",
  "<strong>The job scope is entered by a person</strong>, once. It is the only place quantities "
  "come from, which is why unit prices are never guessed.",
  "<strong>Textract runs first</strong> and the model works on its output rather than on raw "
  "pixels, which keeps the read cost and the error rate down."],
 model_notes=[
  "<strong>One read per document.</strong> Structuring lines, units and terms sentences out of "
  "Textract output.",
  "<strong>It never compares.</strong> Alignment and classification are rules over the structured "
  "output, so the same quote produces the same table every time.",
  "<strong>It never estimates a missing quantity.</strong> A line with no unit is returned as "
  "unclear, and the prompt is explicit that guessing is a failure.",
  "<strong>It never summarises the terms.</strong> Terms sentences are extracted verbatim, "
  "because the wording is the evidence and a paraphrase is not.",
  "<strong>Provenance is required output.</strong> A line item returned without a page and line "
  "is rejected and re-requested rather than stored."],
 gotchas=[
  "Cache on the document hash, not on the quote id. The same supplier re-sending a corrected PDF "
  "must re-read; a second comparison of the same file must not.",
  "Keep the terms sentences verbatim. The moment they are summarised, the exclusion detection "
  "becomes unarguable in exactly the situation where somebody wants to argue about it.",
  "Separate firm and provisional totals in the data model, not in the template. A single total "
  "field will end up quoted somewhere.",
  "Never delete an unalignable quote from the job. A clean table that omits a supplier "
  "misrepresents what was received.",
  "Label the estimated-gap band as an estimate everywhere it appears, and exclude it from every "
  "field named total."],
))
