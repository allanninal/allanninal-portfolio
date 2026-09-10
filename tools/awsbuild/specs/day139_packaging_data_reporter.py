"""Day 139 -- 2026-09-10 -- Packaging data reporter."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "packaging-data-reporter"
NAME = "Packaging data reporter"

SPEC = {
 "slug": SLUG, "date": "2026-09-10", "name": NAME,
 "tagline": ("Works out which packaging is legally yours to report, what each item weighs when "
             "nobody can weigh 3,000 of them, and whether it ends up in a household bin or a "
             "trade one -- because only one of those two answers carries a fee."),
 "lede": ("A small system for any business that puts packaged goods on the market: the "
          "obligation established per item rather than assumed, weights sourced with the "
          "method recorded, the household split decided on evidence, and a submission that "
          "still makes sense seven years later. Seven posts on the same system, one diagram at "
          "a time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["packaging EPR", "producer responsibility", "packaging data", "recycling fees",
              "compliance", "serverless"],
 "icons": ["box", "counter", "report"],
 "faq": [
  ("Who has to report packaging data?",
   "Organisations above a turnover and a tonnage threshold that carry out one of a defined set "
   "of activities -- owning the brand, filling the packaging, importing it filled, supplying "
   "it filled, or selling it to the end consumer. Making the box is not on the list."),
  ("Why does household versus non-household matter so much?",
   "Because the disposal fees attach to household packaging. Two identical cases of the same "
   "product can carry very different costs depending on who bought them, and getting the split "
   "wrong is expensive in whichever direction it is wrong."),
  ("We have thousands of lines. How is anyone supposed to weigh them?",
   "You are not. You use supplier data where it exists, weigh a representative sample where it "
   "does not, and record which method produced every figure. The method is what makes the "
   "number defensible, not the precision."),
  ("How long do we have to keep the data?",
   "Seven years, and an auditor can ask for the working behind any line in it. The submission "
   "is a summary; the evidence is the deliverable."),
  ("What does it cost to run?",
   "A few dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "packaging-data-reporter-on-aws",
 "title": "A packaging data reporter on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Obligation established per item, weights sourced with their method, the household "
          "split decided on evidence, and seven years of working kept. AWS, about $3 a month."),
 "og": ("310 tonnes filed as household packaging that never went near a household. At the "
        "blended rate in this example that is 86,800 pounds of fees on the wrong side of a "
        "line."),
 "abstract": ("The whole system on one page -- obligation, weights, the household split and "
              "the submission -- and why the split rather than the total is where the money "
              "is."),
 "lede": ("A wholesaler with 3,140 lines filed its packaging data the way most businesses do: "
          "one person, one spreadsheet, six weeks, and a set of assumptions nobody wrote down. "
          "The following year somebody asked why bulk catering packs were being reported as "
          "household packaging. Nobody could answer, because the previous year's working no "
          "longer existed."),
 "tags": ["packaging EPR", "producer responsibility", "compliance", "waste", "reporting",
          "serverless"],
 "takeaways": [
  "The obligation attaches to an activity, not to whoever printed the box.",
  "Weights come from suppliers, scales or samples, and the method is part of the answer.",
  "Fees attach to the household portion, so the split is worth more than the total.",
  "Seven years of working has to survive, not just the numbers filed.",
  "Designed on AWS for about $3 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Product lines", "sub": ["what you sell, and", "how it is packed"], "icon": "box"},
      {"title": "Sales volumes", "sub": ["units shipped, and", "to whom"], "icon": "truck"},
      {"title": "The rules", "sub": ["thresholds, materials,", "fee bands"], "icon": "key"}],
    "inside": [
      {"title": "Obligation", "sub": ["which items are", "yours to report"], "icon": "check"},
      {"title": "Weight and material", "sub": ["per unit, with the", "method attached"], "icon": "counter"},
      {"title": "Split and submit", "sub": ["household or not,", "and the evidence"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "as the range changes"},
              {"from": 1, "to": 1, "label": "monthly"},
              {"from": 2, "to": 2, "label": "when they change", "up": True}],
    "note": "The middle column is the whole job. The sales data already exists and the rules "
            "are published; what is missing is a per-item weight nobody has ever recorded."}),
   "Three things outside the account, three pieces inside it. The second box is where six "
   "weeks of somebody's year currently goes.",
   "System: product lines, volumes and the rules joined into a packaging submission",
   "Three boxes across the top sit outside the AWS account. On the left, Product lines: what "
   "you sell and how it is packed. In the middle, Sales volumes: units shipped and to whom. On "
   "the right, The rules: thresholds, materials and fee bands. Each connects by an arrow to the "
   "AWS account container below, labelled as the range changes, monthly, and when they change. "
   "Inside the AWS account are three components in a row. Obligation: which items are yours to "
   "report. Weight and material: per unit, with the method attached. And Split and submit: "
   "household or not, and the evidence. A note says the middle column is the whole job, because "
   "the sales data already exists and the rules are published, and what is missing is a "
   "per-item weight nobody has ever recorded."),
  ("h3", "Why this is hard for a business that is otherwise well run"),
  ("p", "Because the data it needs has never been anybody's job. A wholesaler knows precisely "
        "how many units of each line it shipped, to whom, at what price, in what month. It has "
        "no idea what the outer case weighs empty, because there has never been a reason to "
        "know and the supplier who makes the case has never been asked."),
  ("p", "So the first submission is done by a person with a set of kitchen scales and a "
        "spreadsheet, working through the biggest lines and estimating the rest, and it takes "
        "six weeks. The second one is done the same way by somebody else, because the first "
        "person left and the working was in a tab called <em>final v4</em> that nobody can now "
        "interpret."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Obligation.</strong> Which packaging is legally yours to report, decided per item "
   "against a defined set of activities. Part 2.",
   "<strong>Weights.</strong> A per-unit weight for every component of every line, and the "
   "method that produced it. Part 3.",
   "<strong>The split.</strong> Household or non-household, decided on who actually bought it "
   "rather than on what it looks like. Part 4.",
   "<strong>The submission.</strong> The file that goes off, and the seven years of working "
   "that has to survive behind it. Part 5.",
  ]),
  ("h2", "One wholesaler, one reporting year"),
  ("fig", ("strip", {
    "stages": [
      {"title": "3,140 lines", "sub": ["each with its own", "packaging"], "icon": "box"},
      {"title": "1,880 tonnes", "sub": ["placed on the market", "in one year"], "icon": "truck"},
      {"title": "1,240 household", "sub": ["the only tonnes that", "carry a fee"], "icon": "money"},
      {"title": "640 non-household", "sub": ["reported, and", "charged nothing"], "icon": "check"},
      {"title": "310 on the wrong side", "sub": ["about GBP 86,800", "overpaid"], "icon": "alarm"}],
    "title": "ONE WHOLESALER, ONE REPORTING YEAR",
    "note": "The last box is not a penalty and not an underpayment. It is a fee paid on "
            "packaging that never went anywhere near a household bin."}),
   "The same year as one line. The first two boxes are what everybody measures; the third and "
   "fourth are where the money is decided.",
   "One wholesaler's reporting year from product lines to tonnes misclassified",
   "A horizontal row of five boxes joined by arrows. Three thousand one hundred and forty "
   "product lines, each with its own packaging. One thousand eight hundred and eighty tonnes "
   "placed on the market in one year. One thousand two hundred and forty tonnes classified as "
   "household, the only tonnes that carry a fee. Six hundred and forty tonnes non-household, "
   "reported and charged nothing. And three hundred and ten tonnes on the wrong side of the "
   "line, worth about eighty-six thousand eight hundred pounds overpaid. A note says the last "
   "box is not a penalty and not an underpayment, but a fee paid on packaging that never went "
   "anywhere near a household bin."),
  ("h2", "In plain words"),
  ("p", "Product lines arrive from wherever the range is managed, and each one is broken into "
        "packaging components: the primary pack the product sits in, the outer case, the pallet "
        "wrap, the label, the tray. Each component has a material and a weight, and getting "
        "those two fields for a few thousand lines is the bulk of the work in this whole "
        "domain."),
  ("p", "Before any of that matters, the system asks whether the item is yours to report at "
        "all. That is a question about activities rather than about ownership of the physical "
        "cardboard, and part two is entirely about it, because both wrong answers are "
        "expensive: reporting somebody else's packaging costs fees you do not owe, and not "
        "reporting your own is a compliance failure."),
  ("p", "Sales volumes come in monthly and multiply up. Units shipped times per-unit weight, "
        "summed by material, gives tonnage placed on the market, which is the headline number "
        "and the easy part. It is the easy part precisely because all the difficulty was moved "
        "upstream into establishing the per-unit weight once."),
  ("p", "Then each tonne is assigned to household or non-household, which decides whether it "
        "carries a disposal fee. This is decided on evidence about who bought it, held per "
        "line, because the same case of the same product is household packaging when a "
        "supermarket sells it and non-household when a catering wholesaler does."),
  ("callout", "Design rules that shaped every decision", [
   "Every weight carries the method that produced it, and its date.",
   "An estimate is a first-class value, not a missing value with a guess in it.",
   "The obligation is decided per item and records which activity triggered it.",
   "The household split is evidence, not a property of the product.",
   "A submitted figure is frozen. Later corrections are new versions, never edits.",
   "Everything is retained for seven years, including the working, not just the totals.",
  ]),
  ("h2", "What it does not do"),
  ("p", "It does not file the return. The submission route has its own portal and its own "
        "format and both change; this system produces the dataset that goes into it and the "
        "record of how every line was derived. That division has held up well in the other "
        "compliance systems in this series and it holds up here."),
  ("p", "It does not tell you whether you are obligated in the first place either. That is a "
        "question about your turnover, your group structure and your tonnage, and the answer "
        "changes the whole shape of what you have to do. The system computes both test figures "
        "and shows you where you sit; a person decides what that means."),
  ("p", "And it does not chase your suppliers, though it produces the list of who to chase and "
        "what each missing specification is worth in tonnage. That list turns out to be the "
        "most useful thing it makes in the first year, because the difference between a "
        "supplier-provided weight and a sampled one is the difference between a line an auditor "
        "skips and a line an auditor asks about."),
  ("p", "The next four posts walk through each piece: whose packaging it is, how to weigh what "
        "you cannot weigh, how the household split is decided, and what the submission and the "
        "audit behind it have to contain. One diagram per post, a cost breakdown, and an "
        "engineering reference at the end."),
 ],
},
]

SPEC["parts"].append(
{
 "slug": "whose-packaging-is-it-anyway",
 "title": "Whose packaging is it anyway",
 "nav": "The obligation",
 "read": 5, "words": 810,
 "desc": ("The activity test that decides which packaging is yours to report, why making the "
          "box is not on the list, and the two thresholds that decide which regime applies."),
 "og": ("The company that manufactured the cardboard has no obligation. The company whose "
        "brand is printed on it usually does, even if it never touched it."),
 "abstract": ("Deciding per item whether the reporting obligation attaches to you, under which "
              "activity, and how the turnover and tonnage thresholds set the regime."),
 "lede": ("The intuitive answer is that packaging belongs to whoever bought it, and the "
          "intuitive answer produces a submission that is wrong in both directions at once. "
          "The rule is about what you did with the packaged goods, not about who owns the "
          "cardboard."),
 "tags": ["packaging EPR", "producer responsibility", "obligation", "thresholds", "compliance",
          "serverless"],
 "takeaways": [
  "The obligation follows a defined activity: brand owner, filler, importer, distributor, seller.",
  "Manufacturing the packaging is not one of those activities.",
  "Imported filled packaging is yours even though somebody abroad specified it.",
  "Every item should be reported by exactly one organisation. Two is a cost.",
  "Turnover and tonnage together decide small, large, or not obligated at all.",
 ],
 "blocks": [
  ("h2", "The activity test, one item at a time"),
  ("fig", ("chain", {
    "entry": {"title": "A packaged item", "sub": ["that passed through", "your business"], "icon": "box"},
    "steps": [
      {"title": "Does it carry your brand?", "sub": ["own label, or your", "name on the pack"],
       "icon": "tag",
       "exit": {"title": "Yours", "sub": ["brand owner, even if", "a co-packer filled it"],
                "icon": "check", "label": "yes"}},
      {"title": "Did you import it filled?", "sub": ["brought into the UK", "with goods in it"],
       "icon": "truck",
       "exit": {"title": "Yours", "sub": ["importer, whoever", "specified the pack"],
                "icon": "check", "label": "yes"}},
      {"title": "Did you fill it?", "sub": ["packed the goods", "into the packaging"], "icon": "plug",
       "exit": {"title": "Yours", "sub": ["unless it carries", "somebody else's brand"],
                "icon": "check", "label": "yes"}},
      {"title": "Did you supply it on?", "sub": ["filled, to a business", "that sells it"], "icon": "cart",
       "exit": {"title": "Yours", "sub": ["distributor, for", "this item"], "icon": "check",
                "label": "yes"}},
      {"title": "Somebody else's", "sub": ["record who, and", "why it is not yours"], "icon": "doc"}],
    "note": "Every item ends up belonging to exactly one organisation. Two organisations "
            "reporting the same item is a fee paid twice; zero is a compliance failure."}),
   "Four questions and one default. The questions are in order for a reason: the first one "
   "that answers yes settles it.",
   "The activity test deciding whether a packaged item is yours to report",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled A "
   "packaged item that passed through your business. Does it carry your brand, meaning own "
   "label or your name on the pack, with a side exit reading yes: Yours as brand owner, even if "
   "a co-packer filled it. Did you import it filled, meaning brought into the UK with goods in "
   "it, with a side exit reading yes: Yours as importer, whoever specified the pack. Did you "
   "fill it, meaning packed the goods into the packaging, with a side exit reading yes: Yours, "
   "unless it carries somebody else's brand. Did you supply it on, filled, to a business that "
   "sells it, with a side exit reading yes: Yours as distributor for this item. The final step "
   "is Somebody else's, recording who and why it is not yours. A note says every item ends up "
   "belonging to exactly one organisation, that two organisations reporting the same item is a "
   "fee paid twice, and zero is a compliance failure."),
  ("h3", "Making the box is not on the list"),
  ("p", "The company that converts board into cases has no obligation for those cases. This "
        "surprises people every time, because it is the one organisation in the chain that "
        "genuinely decided what the packaging would be. The scheme is not trying to charge "
        "whoever created the material; it is trying to charge whoever put the packaged goods "
        "into the market that eventually has to dispose of them."),
  ("p", "Once you hold that in mind the rest of the list stops looking arbitrary. Brand owner, "
        "filler, importer, distributor, seller: these are the positions from which somebody "
        "decided that a product would reach a UK buyer in a particular pack. The converter "
        "made what they were asked for."),
  ("p", "The practical consequence is that a business can be obligated for packaging it has "
        "never specified, never seen a drawing of and cannot change. An importer bringing in "
        "goods over-packed by an overseas supplier owns that tonnage, and the only lever they "
        "have is the purchasing conversation. Several businesses discover the size of that "
        "lever the first time they measure."),
  ("h2", "Two numbers decide the regime"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Turnover", "sub": ["the group's, not just", "the company's"], "icon": "chart"},
      {"title": "Tonnage", "sub": ["packaging placed on", "the market"], "icon": "counter"},
      {"title": "Below both", "sub": ["no obligation,", "this year"], "icon": "check"},
      {"title": "Small producer", "sub": ["report once a year,", "less detail"], "icon": "doc"},
      {"title": "Large producer", "sub": ["report twice a year,", "and pay the fees"], "icon": "money"}],
    "title": "TWO TESTS, ANNUAL, BOTH EASY TO CROSS BY ACCIDENT",
    "note": "Turnover is measured for anybody who has ever looked at the accounts. Tonnage is "
            "the one nobody is measuring, which is why nobody sees the threshold coming."}),
   "Both tests have to be crossed to be obligated, and crossing the second pair moves you into "
   "a materially heavier regime.",
   "The turnover and tonnage thresholds deciding small, large or unobligated",
   "A horizontal row of five boxes joined by arrows. Turnover, measured for the group rather "
   "than just the company. Tonnage of packaging placed on the market. Below both, meaning no "
   "obligation this year. Small producer, reporting once a year with less detail. Large "
   "producer, reporting twice a year and paying the fees. A note says turnover is measured by "
   "anybody who has ever looked at the accounts, while tonnage is the one nobody is measuring, "
   "which is why nobody sees the threshold coming."),
  ("h3", "The thresholds are dated data, not constants"),
  ("p", "The current tests use a turnover figure and a tonnage figure, in two tiers, and both "
        "have moved before and will move again. So they live in a table with effective dates "
        "rather than in the code, and every assessment records which version of the thresholds "
        "it was made against."),
  ("p", "This is not over-engineering; it is the difference between a system that can explain "
        "why it said you were a small producer in one year and a large one the next, and a "
        "system whose behaviour changed when somebody edited a constant. The same principle "
        "applies to the material list and the fee bands, which change more often than the "
        "thresholds do."),
  ("h2", "Group structure is the quiet trap"),
  ("p", "The turnover test looks at the group, not the individual company. A business run "
        "through four small limited companies, each comfortably under the threshold, can be "
        "obligated on the aggregate and not realise it, because every internal conversation "
        "about turnover happens at company level."),
  ("p", "So the system holds the group relationship explicitly and computes both figures: what "
        "this company placed on the market, and what the group did. It also holds the "
        "intra-group transfers separately, because packaging moving from one company in the "
        "group to another has not been placed on the market at all and counting it inflates the "
        "tonnage on which everything else depends."),
  ("callout", "What the obligation record holds, per item", [
   "<strong>Activity.</strong> brand_owner | filler | importer | distributor | seller | none.",
   "<strong>Basis.</strong> What established it -- the label artwork, the import entry, the "
   "supply contract.",
   "<strong>Counterparty.</strong> Who holds it instead, where the answer is none.",
   "<strong>Nation.</strong> Where it was supplied, because the household reporting is split "
   "by nation.",
   "<strong>Intra-group.</strong> True where the movement never reached the market.",
   "<strong>Assessed under.</strong> The version of the rules that produced this answer.",
  ]),
  ("h2", "Why per item rather than per business"),
  ("p", "Because a real business occupies several of these positions at once. The same "
        "wholesaler is a brand owner for its own label, an importer for the continental lines "
        "it brings in directly, a distributor for the branded goods it buys in the UK and "
        "supplies to independents, and nothing at all for the goods it sells that were already "
        "reported upstream."),
  ("p", "A single business-level answer therefore cannot exist, and any spreadsheet that "
        "produces one has smoothed over the distinction that determines the tonnage. Deciding "
        "it per line costs one field and is the only version that can be checked."),
  ("p", "The next post is the number that decides everything downstream, and the reason the "
        "first submission takes six weeks: what does one of these actually weigh."),
 ],
})

SPEC["parts"].append(
{
 "slug": "weighing-what-you-cannot-weigh",
 "title": "Weighing what you cannot weigh",
 "nav": "Weights",
 "read": 5, "words": 820,
 "desc": ("Three ways a per-unit packaging weight gets established, why the method is part of "
          "the answer, and how a 40 gram error becomes 48 tonnes."),
 "og": ("An outer case recorded 40 grams light, across 1.2 million cases, is 48 tonnes of "
        "packaging that never existed."),
 "abstract": ("Sourcing a per-unit weight for every packaging component from supplier data, "
              "direct weighing or sampling, recording the method and date, and the errors that "
              "multiply."),
 "lede": ("Nobody can weigh three thousand product lines, and nobody is expected to. What is "
          "expected is that every number in the submission can say where it came from, and "
          "that turns an impossible measurement problem into an ordinary data problem."),
 "tags": ["packaging EPR", "packaging weights", "sampling", "supplier data", "compliance",
          "serverless"],
 "takeaways": [
  "Three sources: supplier specification, weighed in house, sampled and modelled.",
  "The method and the date travel with the weight. A bare number is not an answer.",
  "Weigh empty packaging. Subtracting product weight from a full case compounds two errors.",
  "Split composites by material. A card box with a plastic window is two lines.",
  "Small per-unit errors are large at volume, and they do not cancel out.",
 ],
 "blocks": [
  ("h2", "Three ways to get a weight"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Supplier specification", "sub": ["the drawing, or a", "written spec sheet"],
       "icon": "doc", "label": "best, if it exists"},
      {"title": "Weighed in house", "sub": ["empty packaging,", "on real scales"], "icon": "counter",
       "label": "slow, and exact"},
      {"title": "Sampled and modelled", "sub": ["a representative few,", "applied to the rest"],
       "icon": "chart", "label": "unavoidable"}],
    "target": {"title": "Per-unit weight", "sub": ["grams, by material,", "by component"], "icon": "box",
               "then": {"title": "Tonnage", "sub": ["units shipped times", "the weight"], "icon": "truck"}},
    "note": "All three are acceptable. What is not acceptable is a number that cannot say "
            "which of the three it is, and that is what most first submissions contain."}),
   "Three routes, one weight. The route is stored beside the number because it is the first "
   "thing an auditor asks and the last thing anybody records.",
   "Three sources for a per-unit packaging weight converging on a tonnage",
   "Three boxes on the left feed one box on the right. Supplier specification, from a drawing "
   "or a written spec sheet, described as best if it exists. Weighed in house, meaning empty "
   "packaging on real scales, described as slow and exact. Sampled and modelled, meaning a "
   "representative few applied to the rest, described as unavoidable. All three converge on "
   "Per-unit weight in grams, by material and by component, which feeds a box labelled Tonnage: "
   "units shipped times the weight. A note says all three are acceptable, that what is not "
   "acceptable is a number that cannot say which of the three it is, and that this is what most "
   "first submissions contain."),
  ("h3", "Empty, not full minus product"),
  ("p", "The shortcut everybody reaches for is to weigh a full case and subtract the declared "
        "net weight of the contents. It saves opening anything and it produces a figure that is "
        "wrong by the sum of two errors: the tolerance on the fill weight and whatever else is "
        "in the case that is neither product nor the component being measured."),
  ("p", "For a case of tinned goods that shortcut puts the tin weight into the cardboard line, "
        "which is not a small error and is in the wrong material entirely. Weighing the empty "
        "case takes thirty seconds more and produces a number that survives being questioned."),
  ("h2", "How the tonnage was established"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Supplier data", "parts": [("t", 1190)]},
      {"label": "Weighed in house", "parts": [("t", 405)]},
      {"label": "Sampled and modelled", "parts": [("t", 285)]}],
    "series": [("t", "Tonnes placed on the market, by how the weight was established",
                "#4A90D9")],
    "unit": "",
    "note": "The third bar is the one an auditor asks about first. It is also the one that "
            "shrinks every year, as suppliers answer."}),
   "The same 1,880 tonnes, grouped by where its weights came from. This chart is the honest "
   "summary of a submission's quality and it takes one query.",
   "Tonnes of packaging grouped by the method that established the weight",
   "Three vertical bars showing tonnes of packaging placed on the market grouped by how the "
   "weight was established. Supplier data accounts for one thousand one hundred and ninety "
   "tonnes. Weighed in house accounts for four hundred and five tonnes. Sampled and modelled "
   "accounts for two hundred and eighty-five tonnes. A note says the third bar is the one an "
   "auditor asks about first, and also the one that shrinks every year as suppliers answer."),
  ("h3", "The chase list falls out of this"),
  ("p", "Once weights carry their method, the system can rank suppliers by how much tonnage "
        "currently rests on an estimate. That list is short, it is ordered by something real, "
        "and sending it to purchasing is the single highest-value output of the first year of "
        "running this."),
  ("p", "It also reframes the conversation with the supplier. <em>Please send packaging "
        "specifications</em> gets ignored. <em>We are currently estimating 61 tonnes of your "
        "packaging because we do not have your spec sheets</em> does not, because it is "
        "specific and it implies somebody is counting."),
  ("h2", "Where the error goes"),
  ("p", "Per-unit weights are in grams and volumes are in millions, and that ratio is what "
        "makes small mistakes structural. An outer case recorded forty grams light, across one "
        "point two million cases in a year, is forty-eight tonnes of packaging that does not "
        "appear in the submission at all."),
  ("p", "The temptation is to assume errors cancel, and they do not, because they are not "
        "random. A business that estimates conservatively estimates conservatively everywhere, "
        "and a business that uses a nominal board weight from a catalogue uses the same "
        "catalogue for every line. Systematic method produces systematic error, in one "
        "direction, at scale."),
  ("p", "So sampling records what was sampled: how many units, when, the mean and the spread. "
        "A component whose sample spread is wide is flagged rather than averaged, because a "
        "wide spread usually means two different packs are being sold under one code, and that "
        "is a data problem rather than a measurement one."),
  ("callout", "What a weight record holds", [
   "<strong>Grams.</strong> Per unit of the component, empty.",
   "<strong>Material.</strong> From the fixed list, with composites split by material.",
   "<strong>Component.</strong> Primary, secondary, transit, or shipment.",
   "<strong>Method.</strong> supplier_spec | weighed | sampled, never blank.",
   "<strong>Sample detail.</strong> n, mean and spread, where the method is sampled.",
   "<strong>Established on.</strong> A date, because packaging changes and specs go stale.",
   "<strong>Evidence.</strong> The spec sheet, the weighing record, or the sample sheet.",
  ]),
  ("h2", "Composites and the material list"),
  ("p", "The material categories are fixed and their boundaries are not always intuitive. A "
        "card sleeve with a plastic window is two materials and reports as two lines. A "
        "fibre-based composite carton is its own category rather than paper. A steel lid on a "
        "glass jar is steel and glass, in the proportions they actually are."),
  ("p", "This is tedious and it is also where a surprising amount of tonnage moves between "
        "categories that are charged differently. The system therefore models a component as a "
        "list of material portions rather than as a single material, which costs one level of "
        "nesting and removes an entire class of argument."),
  ("p", "The next post is the field that decides whether any of this tonnage costs money: "
        "whether it ends up in a household bin or a trade one, and why that is a question about "
        "the buyer rather than about the pack."),
 ],
})

SPEC["parts"].append(
{
 "slug": "household-or-not-and-what-it-costs",
 "title": "Household or not, and why that field costs more than the rest of the file",
 "nav": "The split",
 "read": 5, "words": 810,
 "desc": ("Why the household split decides the fees, why it is a property of the sale rather "
          "than the product, and what evidence moves a tonne across the line."),
 "og": ("The same case of the same product is household packaging in a supermarket and "
        "non-household in a catering wholesaler. Classify the sale, not the SKU."),
 "abstract": ("Assigning each tonne to household or non-household on evidence about the buyer, "
              "the default that applies when there is none, and the nation split underneath "
              "it."),
 "lede": ("Everything up to this point produced a tonnage, and a tonnage on its own does not "
          "cost anything. This one field decides which of those tonnes carry a disposal fee, "
          "which makes it the most expensive column in the file by a wide margin."),
 "tags": ["packaging EPR", "household packaging", "disposal fees", "evidence", "compliance",
          "serverless"],
 "takeaways": [
  "Fees attach to the household portion. The non-household portion is reported and not charged.",
  "It is a property of the sale, not of the product. The same SKU splits both ways.",
  "The default is household, and the burden of showing otherwise sits with you.",
  "Trade-only pack formats evidence themselves. Everything else needs the buyer.",
  "Household tonnage is also split by nation, which the sales ledger already knows.",
 ],
 "blocks": [
  ("h2", "Classifying a sale, not a product"),
  ("fig", ("chain", {
    "entry": {"title": "A sales line", "sub": ["a product, a customer,", "a quantity"], "icon": "cart"},
    "steps": [
      {"title": "Sold to a consumer?", "sub": ["direct, or through", "a retailer"], "icon": "person",
       "exit": {"title": "Household", "sub": ["this tonnage", "carries a fee"], "icon": "money",
                "label": "yes"}},
      {"title": "Trade-only format?", "sub": ["a pack no household", "would ever buy"], "icon": "box",
       "exit": {"title": "Non-household", "sub": ["evidenced by the", "format itself"], "icon": "check",
                "label": "yes"}},
      {"title": "Evidence on the buyer?", "sub": ["customer type, channel,", "delivery address"],
       "icon": "search",
       "exit": {"title": "Non-household", "sub": ["evidenced by who", "bought it"], "icon": "check",
                "label": "yes"}},
      {"title": "Household by default", "sub": ["because you cannot", "show otherwise"], "icon": "alarm"}],
    "note": "The default costs money, and that is deliberate. The burden of showing that "
            "packaging is not household sits with the organisation reporting it."}),
   "Three questions and a default that is not free. Every line ends up classified, and the "
   "reason it was classified that way is stored with it.",
   "A sales line classified as household or non-household packaging",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled A "
   "sales line with a product, a customer and a quantity. Sold to a consumer, directly or "
   "through a retailer, with a side exit reading yes: Household, this tonnage carries a fee. "
   "Trade-only format, meaning a pack no household would ever buy, with a side exit reading "
   "yes: Non-household, evidenced by the format itself. Evidence on the buyer, from customer "
   "type, channel or delivery address, with a side exit reading yes: Non-household, evidenced "
   "by who bought it. The final step is Household by default, because you cannot show "
   "otherwise. A note says the default costs money and that this is deliberate, because the "
   "burden of showing that packaging is not household sits with the organisation reporting it."),
  ("h3", "Where the 310 tonnes came from"),
  ("p", "In the worked example the wholesaler classified by product code, which is the obvious "
        "way to do it and requires one decision per line rather than one per sale. Every code "
        "that had ever been sold to a consumer was marked household, and the bulk catering "
        "packs of those same products inherited the marking."),
  ("p", "Three hundred and ten tonnes of packaging that went out in six-kilogram catering packs "
        "to restaurants and schools was therefore reported as household. Nobody made a mistake; "
        "the model was one field too coarse. Classifying at the sales line instead costs nothing "
        "extra, because the sales ledger already knows who bought it."),
  ("h2", "Three piles, and the third is the argument"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Clearly household", "parts": [("t", 930)]},
      {"label": "Clearly not", "parts": [("t", 640)]},
      {"label": "Depends who bought it", "parts": [("t", 310)]}],
    "series": [("t", "Tonnes placed on the market", "#8C4FFF")],
    "unit": "",
    "note": "The third bar is 16 per cent of the tonnage and essentially all of the "
            "uncertainty. It is also the only bar that a sales ledger query can resolve."}),
   "The same 1,880 tonnes, grouped by how obvious the classification is. Two of these piles "
   "need no work at all.",
   "Tonnes grouped by whether the household classification is obvious",
   "Three vertical bars showing tonnes placed on the market grouped by how clear the "
   "classification is. Clearly household accounts for nine hundred and thirty tonnes. Clearly "
   "not household accounts for six hundred and forty tonnes. Depends who bought it accounts for "
   "three hundred and ten tonnes. A note says the third bar is sixteen per cent of the tonnage "
   "and essentially all of the uncertainty, and it is also the only bar a sales ledger query "
   "can resolve."),
  ("h3", "Do not over-correct"),
  ("p", "Having found three hundred and ten tonnes on the wrong side, the instinct is to go "
        "looking for more, and that instinct needs a limit. An unevidenced non-household claim "
        "is a different kind of error from an over-cautious household one: the first is found "
        "in an audit and reversed with consequences, the second only costs money."),
  ("p", "So the rule the system enforces is that non-household requires a stored reason and a "
        "stored piece of evidence, and household needs neither. That asymmetry mirrors where "
        "the burden actually sits, and it means the submission can be defended line by line "
        "rather than argued for in general terms."),
  ("h2", "Shipment packaging is household more often than people expect"),
  ("p", "The box an online order arrives in, the void fill inside it and the tape around it are "
        "packaging, they are supplied to whoever receives the parcel, and when that is a "
        "consumer at a home address they are household packaging. For a business with a "
        "direct-to-consumer channel this is often the fastest-growing line in the whole "
        "submission and the one least likely to be in the spreadsheet."),
  ("p", "It also has the useful property of being entirely within your control, unlike the "
        "primary pack that came from a supplier. A business that discovers its shipping "
        "cartons are a hundred and eighty tonnes a year has a purchasing decision in front of "
        "it with a number attached to it, which is more than most compliance exercises "
        "produce."),
  ("callout", "What moves a tonne to non-household", [
   "<strong>Customer type on the ledger.</strong> Trade account, with a company number.",
   "<strong>Channel.</strong> A wholesale or foodservice order route, coded at entry.",
   "<strong>Pack format.</strong> A catering size or a trade multipack, evidenced by the spec.",
   "<strong>Delivery address type.</strong> A business address, where you hold it.",
   "<strong>A contract.</strong> Supply agreements that state the end use.",
   "<strong>Nothing.</strong> In which case it stays household, and that is the correct answer.",
  ]),
  ("h2", "The nation split underneath"),
  ("p", "Household tonnage is also reported by nation, because the disposal it pays for is "
        "organised nation by nation. This sounds like an extra dimension of work and is "
        "usually not, because the sales ledger already carries a delivery postcode and the "
        "mapping is a lookup."),
  ("p", "Where it does bite is with a distributor whose customer is a national retailer's "
        "central warehouse. The goods go to one address in one nation and are then sold in "
        "four, and the reporter has to allocate on the best information available. The system's "
        "job there is to record the allocation basis rather than to pretend the postcode "
        "answered the question."),
  ("p", "The next post is what actually gets submitted, what has to survive behind it for seven "
        "years, and why the submission is the smaller half of the deliverable."),
 ],
})

SPEC["parts"].append(
{
 "slug": "the-submission-and-the-audit-behind-it",
 "title": "The submission, and the seven years behind it",
 "nav": "Submission",
 "read": 5, "words": 820,
 "desc": ("Freezing a reporting period, the reconciliation that catches errors before they are "
          "filed, and the evidence trail an audit walks four years later."),
 "og": ("The file that gets submitted is a few hundred rows. The thing you are actually "
        "producing is the seven years of working that sits behind it."),
 "abstract": ("Closing a reporting period: freezing the inputs, aggregating by material, "
              "nation and split, reconciling against the previous period, and assembling the "
              "evidence pack."),
 "lede": ("The submission itself is small enough to read on one screen, which is why every "
          "business treats it as the deliverable. The deliverable is the part nobody submits: "
          "the trail from any row in that file back to a weighing record made three years "
          "ago."),
 "tags": ["packaging EPR", "reporting", "audit", "evidence", "compliance", "serverless"],
 "takeaways": [
  "Freeze the inputs at period close. A submission built on moving data cannot be reproduced.",
  "Reconcile against the previous period before filing, not after somebody queries it.",
  "A correction is a new version with a reason, never an edit to the old one.",
  "Every submitted row traces to sales lines, weights, methods and documents.",
  "Seven years, and the people who did the work will have left.",
 ],
 "blocks": [
  ("h2", "Closing a reporting period"),
  ("fig", ("chain", {
    "entry": {"title": "Period close", "sub": ["the reporting window", "has ended"], "icon": "calendar"},
    "steps": [
      {"title": "Freeze the inputs", "sub": ["sales, weights, rules,", "all pinned"], "icon": "lock"},
      {"title": "Aggregate", "sub": ["by material, split,", "and nation"], "icon": "counter"},
      {"title": "Reconcile", "sub": ["against the previous", "period, line by line"], "icon": "chart",
       "exit": {"title": "Investigate", "sub": ["an unexplained move", "is a data error"], "icon": "alarm",
                "label": "> 10%"}},
      {"title": "Produce the file", "sub": ["the rows that go", "to the regulator"], "icon": "report"},
      {"title": "Write the pack", "sub": ["every row, and what", "is behind it"], "icon": "shield"}],
    "note": "The reconciliation step is the only one that catches errors before they are filed, "
            "and it is the one every manual process skips because there is nothing to compare "
            "against."}),
   "Five steps and one branch. The interesting one is the third, and it only works because the "
   "previous period was frozen rather than overwritten.",
   "A reporting period closed, reconciled and submitted",
   "A vertical chain inside an AWS account container, entered from a box on the left labelled "
   "Period close, the reporting window has ended. Freeze the inputs pins sales, weights and "
   "rules. Aggregate groups by material, split and nation. Reconcile compares against the "
   "previous period line by line, with a side exit reading greater than ten per cent: "
   "Investigate, because an unexplained move is a data error. Produce the file writes the rows "
   "that go to the regulator. Write the pack records every row and what is behind it. A note "
   "says the reconciliation step is the only one that catches errors before they are filed, and "
   "it is the one every manual process skips because there is nothing to compare against."),
  ("h3", "Why freezing matters more here than elsewhere"),
  ("p", "Packaging data has an unusual property: every input to it keeps changing after the "
        "period it describes. Suppliers send spec sheets late, which corrects a weight. Sales "
        "get credited, which changes a volume. Somebody reclassifies a customer, which moves a "
        "tonne across the household line."),
  ("p", "A system that recomputes the current answer from current data therefore produces a "
        "different figure for last year every time it is run, and none of those figures is the "
        "one that was submitted. Freezing at close, and treating later information as a new "
        "version with a reason, is what makes the question <em>what did we file, and why</em> "
        "answerable at all."),
  ("h2", "What an audit actually walks"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A row in the file", "sub": ["e.g. 214 tonnes", "of plastic, household"], "icon": "report"},
      {"title": "The sales lines", "sub": ["which shipments", "made it up"], "icon": "cart"},
      {"title": "The per-unit weight", "sub": ["grams, by component", "and material"], "icon": "counter"},
      {"title": "The method", "sub": ["supplier spec,", "weighed, or sampled"], "icon": "search"},
      {"title": "The document", "sub": ["the spec sheet or", "the sample record"], "icon": "doc"}],
    "title": "FIVE STEPS FROM A SUBMITTED NUMBER TO A PIECE OF PAPER",
    "note": "An auditor picks one row and walks this. If any step is missing the whole "
            "submission stops being evidence and becomes an assertion."}),
   "The trace, in the order it gets walked. Every arrow here is a stored link rather than "
   "somebody's memory of how the spreadsheet worked.",
   "The five step trace from a submitted tonnage back to a source document",
   "A horizontal row of five boxes joined by arrows. A row in the file, for example two hundred "
   "and fourteen tonnes of household plastic. The sales lines that made it up. The per-unit "
   "weight in grams, by component and material. The method, being supplier specification, "
   "weighed, or sampled. And the document, being the spec sheet or the sample record. A note "
   "says an auditor picks one row and walks this, and if any step is missing the whole "
   "submission stops being evidence and becomes an assertion."),
  ("h3", "The threat is turnover, not dishonesty"),
  ("p", "Nothing in the seven-year retention requirement assumes anybody is trying to cheat. It "
        "assumes that the person who weighed forty cases in a stockroom in March will not be "
        "there in four years, and that their spreadsheet will have been through two migrations "
        "and a rename."),
  ("p", "Which is why the evidence is written at the time the number is produced rather than "
        "assembled when it is requested. Assembling it later is not merely inconvenient; for a "
        "sampled weight it is impossible, because the forty cases are long gone and the only "
        "record that they were ever weighed is the record you did or did not make."),
  ("callout", "The sentence the evidence has to be able to write", [
   "This row reports 214 tonnes of household plastic for the second half of the year.",
   "It comes from 41,900 sales lines across 96 product codes.",
   "The largest, code 7714, contributed 38 tonnes from 1.9 million units.",
   "Its per-unit plastic weight is 20 grams, from the supplier specification dated 14 March.",
   "That specification is attached, and it superseded a sampled figure of 23 grams.",
   "The household classification came from the sales channel, which is a consumer retail one.",
  ]),
  ("h2", "Corrections are versions"),
  ("p", "A submission that turns out to be wrong is not edited. A new version is produced, "
        "carrying the same period, a reason, and the specific rows that moved. Both versions "
        "stay, and any report can be run as at either of them."),
  ("p", "This is the same append-only discipline the other compliance systems in this series "
        "use, and it earns its keep for the same reason. The question that gets asked in year "
        "four is never <em>what is the right number</em>. It is <em>why does this year's figure "
        "differ from last year's</em>, and that question is unanswerable if last year's figure "
        "was quietly improved."),
  ("h2", "Where this ends"),
  ("p", "The system does not make a business compliant, because most of what compliance "
        "requires here is measurement that somebody has to actually do. What it removes is the "
        "category of failure where the measurement was done and then lost: the weighing session "
        "whose results went into a tab, the classification decision nobody wrote a reason for, "
        "the year where the whole thing was rebuilt from scratch because the previous version "
        "could not be understood."),
  ("p", "It also turns a compliance cost into an operational input, which is the part worth "
        "copying. A ranked list of suppliers by estimated tonnage is a purchasing document. A "
        "number for your own shipping cartons is a packaging design brief. Neither of those "
        "exists in a business that files the return and closes the file."),
  ("p", "The next post prices it and the one after gives the service names, the tables and the "
        "IAM. The interesting thing about the cost is that the model reads specifications, "
        "which arrive when the range changes, while the tonnage arithmetic runs monthly over "
        "millions of units for essentially nothing."),
 ],
})

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="specification",
 volumes=[(40, "40 specs a month"), (180, "180 specs a month"), (600, "600 specs a month")],
 read_each=0.006,
 msgs_each=1.5,
 store_base=0.30,
 store_growth=0.0008,
 lede=("The model reads packaging specifications, and those arrive when the range changes or "
       "when a supplier finally answers. Everything per unit, per sales line and per month is "
       "arithmetic. A hundred and eighty specifications a month is a business actively "
       "clearing its estimate backlog. Here is where each cent goes."),
 takeaway_extra=("Storage is the line that grows here, because seven years of evidence is the "
                 "point of the system rather than a side effect."),
 risks=[
  "<strong>Running a model over the sales export.</strong> It is millions of fixed-header rows "
  "and it is by far the largest file in the system. Parse it; a model over it would cost more "
  "than the fees it is calculating.",
  "<strong>Re-reading every specification at every period close.</strong> A spec is read when "
  "it arrives and re-read when it is superseded. Twice a year is not an event that should "
  "touch the model at all.",
  "<strong>Never expiring the raw sales imports.</strong> The derived tonnage and its links "
  "must survive seven years. The hundred-million-row monthly export behind it does not, once "
  "it has been aggregated and reconciled.",
 ],
 per_unit_note=("Roughly one model call per packaging specification, against a mid-tier model. "
                "A spec sheet is a short document with a material, a weight and a component, "
                "sometimes in a table and sometimes in a sentence in an email. That is "
                "extraction with awkward formatting, which is not the same as difficulty, and "
                "a frontier model reads the same three fields for several times the price."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="pkg",
 lede=("The same system with the service names filled in: what reads a specification, what "
       "multiplies units by grams, what decides the household split, and where seven years of "
       "evidence sits."),
 outside=[
  {"title": "Range data", "sub": ["product lines and", "their components"], "icon": "box"},
  {"title": "Specifications", "sub": ["supplier sheets,", "drawings, emails"], "icon": "doc"},
  {"title": "Sales exports", "sub": ["units and customers,", "monthly"], "icon": "cart"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["imports and the", "period close"], "icon": "bucket"},
  {"title": "Lambda x5", "sub": ["spec, oblige, tonnage,", "split, submit"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["components, weights,", "periods"], "icon": "database"}],
 note="eu-west-2. One account. Specifications are read as they arrive; sales land monthly; the "
      "period close freezes everything and writes a version that is never edited afterwards.",
 region="eu-west-2",
 region_why=("London, because the scheme is a UK one and the nation split it reports on is a "
             "UK concept. Bedrock model availability is checked here rather than assumed; the "
             "specification read is the only step that would have to move, and every other "
             "step is multiplication."),
 diagram_desc=(
  "Three boxes across the top sit outside the AWS account. Range data covering product lines "
  "and their components. Specifications as supplier sheets, drawings and emails. And Sales "
  "exports carrying units and customers, monthly. Each connects to the AWS account container "
  "below. Inside are three components. S3 with EventBridge handling imports and the period "
  "close. Five Lambda functions covering spec, oblige, tonnage, split and submit. And three "
  "DynamoDB tables holding components, weights and periods. A note says eu-west-2, one account, "
  "specifications are read as they arrive, sales land monthly, and the period close freezes "
  "everything and writes a version that is never edited afterwards."),
 functions=[
  ["<code>pkg-spec</code>", "S3 put, specifications prefix",
   "Reads material, component and grams out of a supplier document", "60s / 1024MB"],
  ["<code>pkg-oblige</code>", "On range change",
   "Runs the activity test per line and records which activity applied", "120s / 1024MB"],
  ["<code>pkg-tonnage</code>", "Monthly, after the sales import",
   "Multiplies units by per-unit grams and sums by material", "600s / 3008MB"],
  ["<code>pkg-split</code>", "Step after tonnage",
   "Classifies each sales line household or not, with its evidence", "600s / 2048MB"],
  ["<code>pkg-submit</code>", "EventBridge, on period close",
   "Freezes inputs, reconciles, writes the file and the evidence pack", "900s / 3008MB"],
 ],
 roles=[
  ["<code>pkg-spec-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>s3:GetObject</code>, <code>dynamodb:PutItem</code>",
   "One model id; the specifications prefix; weights"],
  ["<code>pkg-oblige-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>",
   "components read and write. No access to sales at all"],
  ["<code>pkg-tonnage-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "The sales prefix; components and weights read; periods write"],
  ["<code>pkg-split-role</code>",
   "<code>s3:GetObject</code>, <code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "The sales prefix; components read; periods write"],
  ["<code>pkg-submit-role</code>",
   "<code>dynamodb:Query</code>, <code>s3:PutObject</code>, <code>ses:SendEmail</code>",
   "All three tables read; the submissions prefix write-once; one verified identity"],
 ],
 tables=[
  ("Table: components",
   "PK   org_id#product_code S\n"
   "SK   component_id        S   primary | secondary | transit | shipment + seq\n"
   "     materials           L   [{material, portion}] -- a list, not a field\n"
   "     activity            S   brand_owner | filler | importer | distributor |\n"
   "                             seller | none\n"
   "     activity_basis      S   what established it, and the document\n"
   "     counterparty        S   who reports it instead, when activity is none\n"
   "     intra_group         BOOL true where it never reached the market\n"
   "     assessed_under      S   the rules version that produced the activity\n\n"
   "materials is a list because a card sleeve with a plastic window is two\n"
   "materials in fixed proportions, and they are charged differently. A\n"
   "single material field forces a lie on every composite in the range."),
  ("Table: weights",
   "PK   org_id#product_code#component_id S\n"
   "SK   established_on                   S   append-only; newest wins\n"
   "     grams                            N   per unit, empty packaging\n"
   "     method                           S   supplier_spec | weighed | sampled\n"
   "     sample                           M   {n, mean, spread} when sampled\n"
   "     evidence_key                     S   the spec, the weighing or sample sheet\n"
   "     superseded_reason                S   why this replaced the previous figure\n\n"
   "Weights are versioned by date rather than overwritten, because a period\n"
   "already submitted used the figure that was current then. A supplier\n"
   "spec arriving in March does not retrospectively change last year's\n"
   "tonnage; it starts a new version and the reconciliation explains it."),
  ("Table: periods",
   "PK   org_id#period       S   e.g. 2026-H1\n"
   "SK   version#row_id      S   version 1 is never edited\n"
   "     material            S\n"
   "     split               S   household | non_household\n"
   "     nation              S   set on household rows only\n"
   "     tonnes              N\n"
   "     source_lines        N   how many sales lines contributed\n"
   "     weight_versions     L   the weight records this row multiplied\n"
   "     state               S   draft | frozen | submitted | superseded\n"
   "     variance_note       S   set where the reconciliation flagged a move\n\n"
   "weight_versions is what makes the audit trace in part 5 a query rather\n"
   "than an investigation. Without it, a submitted tonne can name the sales\n"
   "lines behind it but not the gram figure it was multiplied by, and the\n"
   "trail stops one step short of the document."),
  ],
 inbound=[
  "<strong>Sales exports are parsed, not read by a model.</strong> They are millions of "
  "fixed-header rows a month and they are the largest thing this system touches. A model over "
  "them would cost more than the fees being calculated.",
  "<strong>Specifications arrive by upload or mailbox</strong> and both land in the same "
  "function. A supplier's PDF drawing and a supplier's one-line email answer are the same "
  "document as far as extraction is concerned, and the email is more common.",
  "<strong>An incomplete specification produces a chase, not a guess.</strong> The missing "
  "field goes on a list ranked by the tonnage currently resting on an estimate, which is the "
  "most useful output of the first year.",
  "<strong>Nothing is submitted automatically.</strong> The close produces a file and a pack; "
  "a person files it, because a submission is a legal statement and pressing send is a "
  "decision."],
 model_notes=[
  "<strong>One call per specification document.</strong> Nothing per unit, per sales line, per "
  "product or per period. Tonnage is a multiplication and a sum.",
  "<strong>A mid-tier model.</strong> Material, component and grams out of a short document "
  "with unpredictable formatting is extraction, not reasoning.",
  "<strong>Units are extracted, never converted by the model.</strong> A spec quoting 0.021 kg "
  "comes back as 0.021 and kg, and the conversion happens in code. A model asked to normalise "
  "will occasionally move a decimal point, and a decimal point here is a factor of ten across "
  "a million units.",
  "<strong>Composites come back as a list.</strong> The prompt asks for material portions "
  "rather than a material, because the honest answer for half a range is two materials.",
  "<strong>Absent means null.</strong> A spec that does not state a weight must produce null, "
  "which routes the component to the chase list. A plausible number here is indistinguishable "
  "from a real one three years later."],
 gotchas=[
  "Classify the sale, not the product code. The same case is household packaging in a "
  "supermarket and non-household in a catering wholesaler, and a per-code field cannot hold "
  "both.",
  "Store the method with every weight. An estimate is perfectly acceptable and an estimate "
  "nobody labelled is not, and the difference only becomes visible in an audit.",
  "Weigh empty packaging rather than subtracting product weight from a full case. The shortcut "
  "puts the tin in the cardboard line.",
  "Model a component's materials as a list of portions. Composites are common, they are "
  "charged differently by material, and a single material field forces an error on every one "
  "of them.",
  "Freeze the period at close and version corrections. Every input to packaging data keeps "
  "changing after the period it describes, so a recomputed figure is never the one you filed.",
  "Reconcile against the previous period before filing. An unexplained ten per cent move is "
  "almost always a data error, and it is the only check available that does not need an "
  "auditor.",
 ],
))
