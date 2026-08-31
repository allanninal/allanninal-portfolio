"""Day 122 -- 2026-08-24 -- Stock transfer planner."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "stock-transfer-planner"
NAME = "Stock transfer planner"

SPEC = {
 "slug": SLUG, "date": "2026-08-24", "name": NAME,
 "tagline": ("Works out which stock is worth moving between sites -- which is far fewer transfers "
             "than the imbalance suggests, because most of them cost more than the imbalance they "
             "fix and some of them create a stockout at the other end."),
 "lede": ("A small system that spots stock sitting in the wrong branch, checks whether moving it "
          "is actually worth the cost, protects the site it would come from, and waits for a "
          "vehicle that is going there anyway. It also handles the thing most stock systems get "
          "wrong: goods that have left one place and not arrived at the other. Seven posts on "
          "the same system, one diagram at a time, with a cost breakdown and an engineering "
          "reference at the end."),
 "keywords": ["stock transfer", "inventory", "multi-site", "logistics", "replenishment",
              "serverless"],
 "icons": ["storage", "truck", "scale"],
 "faq": [
  ("What is a stock transfer planner?",
   "A small serverless system that identifies stock imbalances between sites, tests whether a "
   "transfer is economically worthwhile, checks it will not cause a shortage at the source, and "
   "proposes it on an existing vehicle movement where possible."),
  ("Why are most transfers not worth it?",
   "Because the cost of picking, packing, moving and receiving is often larger than the margin on "
   "the units being moved, particularly for low-value items."),
  ("What is a ping-pong transfer?",
   "Stock moved from A to B and then back again a few weeks later, usually because both transfers "
   "were triggered by a low stock level rather than by real demand."),
  ("Why does in-transit stock matter?",
   "Because it is simultaneously not at the source and not yet at the destination, and systems "
   "that do not model it either lose it or count it twice."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "stock-transfer-planner-on-aws",
 "title": "A stock transfer planner on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Finds stock imbalances, tests whether moving is worth it, protects the source, and "
          "batches onto existing movements. AWS, about $2 a month."),
 "og": ("Most stock imbalances should be left alone. The transfer costs more than the imbalance "
        "and the arithmetic is not close."),
 "abstract": ("The whole system on one page -- imbalance, worth it, batch &mdash; and the test "
              "that removes most of the proposed transfers before anybody moves anything."),
 "lede": ("Branch three has forty of something that has not sold in two months. Branch one sold "
          "out of it last week. The obvious answer is to move some, and for a fourteen-pound item "
          "with a four-pound margin, a van trip and two people's time makes that a way of "
          "converting stock into a smaller amount of stock somewhere else. This post walks "
          "through a small system that does the arithmetic first."),
 "tags": ["stock transfer", "inventory", "multi-site", "logistics", "replenishment", "serverless"],
 "takeaways": [
  "Test the economics before proposing a transfer. Most fail.",
  "Real demand at the destination, not merely a low stock level.",
  "Never leave the source below its own reorder point.",
  "Wait for a vehicle that is going there anyway; it changes the arithmetic entirely.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Stock by site", "sub": ["and what sells", "where"], "icon": "storage"},
      {"title": "Vehicle movements", "sub": ["already happening"], "icon": "truck"},
      {"title": "Whoever picks", "sub": ["gets a short list"], "icon": "person"}],
    "inside": [
      {"title": "Imbalance", "sub": ["surplus here,", "demand there"], "icon": "scale"},
      {"title": "Worth it?", "sub": ["margin against", "the cost of moving"], "icon": "money"},
      {"title": "When and how", "sub": ["on a van that is", "going anyway"], "icon": "route"}],
    "edges": [{"from": 0, "to": 0, "label": "levels and sales"},
              {"from": 1, "to": 1, "label": "the schedule"},
              {"from": 2, "to": 2, "label": "a few transfers", "up": True}],
    "note": "The middle box rejects most of what the first box finds, and that is correct."}),
   "Three things outside the account, three pieces inside it. The imbalance detection is easy; "
   "the economic test is what makes the output usable.",
   "System: stock imbalances tested for worth and batched onto movements",
   "Three boxes across the top sit outside the AWS account. On the left, Stock by site, with what "
   "sells where. In the middle, Vehicle movements that are already happening. On the right, "
   "Whoever picks, who gets a short list. Each connects by an arrow to the AWS account container "
   "below. Levels and sales flow down into the account. The schedule feeds in. A few transfers go "
   "back out. Inside the AWS account are three components in a row. On the left, Imbalance, "
   "finding surplus here and demand there. In the middle, Worth it, weighing margin against the "
   "cost of moving. On the right, When and how, placing it on a van that is going anyway. A note "
   "at the bottom says the middle box rejects most of what the first box finds, and that is "
   "correct."),
  ("h3", "The cost of moving a box"),
  ("p", "Picking it at one end, packing it, paperwork, the vehicle, receiving and putting it away "
        "at the other end. For a dedicated trip that is tens of pounds before anybody counts the "
        "vehicle; on a movement that was happening anyway it is the picking and receiving, which "
        "is still several pounds of somebody's time."),
  ("p", "Against that sits the benefit, which is not the value of the stock. It is the margin on "
        "the sales that would otherwise be lost, discounted by the probability those sales "
        "actually happen and by whether the item would have sold at the source eventually anyway."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Imbalance detection.</strong> Finds stock that is in the wrong place relative to where "
   "it sells. Part 2.",
   "<strong>The economic test.</strong> Decides whether moving it is worth more than leaving it, "
   "and protects the source. Parts 2 and 3.",
   "<strong>Batching.</strong> Holds proposed transfers until a vehicle is going that way. Part 4.",
  ]),
  ("h2", "One transfer, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Branch 3 has 40", "sub": ["selling 1 a month"], "icon": "storage"},
      {"title": "Branch 1 sells 9", "sub": ["a month, has 2"], "icon": "chart"},
      {"title": "Worth it?", "sub": ["£28 margin vs £9 cost"], "icon": "money"},
      {"title": "Source protected", "sub": ["keep 6 at branch 3"], "icon": "shield"},
      {"title": "On Thursday's van", "sub": ["going there anyway"], "icon": "truck"}],
    "title": "ONE TRANSFER, END TO END",
    "note": "The same transfer on a dedicated trip costs £40 and does not happen."}),
   "The same system as one line. The note is the whole reason the batching step exists.",
   "One stock transfer from imbalance detection to a batched movement",
   "A horizontal row of five boxes joined by arrows. Branch three has forty, selling one a month. "
   "Branch one sells nine a month and has two. Worth it: twenty-eight pounds of margin against "
   "nine pounds of cost. Source protected: keep six at branch three. On Thursday's van, going "
   "there anyway. A note says the same transfer on a dedicated trip costs forty pounds and does "
   "not happen."),
  ("h2", "In plain words"),
  ("p", "Branch three has forty units of an item and sells about one a month, so it is holding "
        "more than three years of cover. Branch one sells nine a month and has two left, which is "
        "about a week."),
  ("p", "Moving twenty-two units protects roughly two and a half months of sales at branch one. "
        "At a margin of a few pounds each and a realistic probability that most of those sales "
        "would otherwise be lost, the benefit is around twenty-eight pounds. Picking and "
        "receiving on an existing movement costs about nine, so it clears."),
  ("p", "The source keeps six units, which is six months of its own demand, so branch three is "
        "not left unable to sell the item to the occasional customer who wants it. And it goes on "
        "Thursday's van, which is already making that trip, rather than on a dedicated journey "
        "that would have made the whole thing uneconomic."),
  ("callout", "Design rules that shaped every decision", [
   "Compare the margin protected against the full cost of moving, both ends.",
   "Demand at the destination means sales history, not a low stock number.",
   "Never take the source below its own cover requirement.",
   "Batch onto existing movements; a dedicated trip needs a much larger benefit.",
   "Track in-transit explicitly. Stock in a van is at neither end.",
   "Detect and block ping-pong: the same item moving back within a quarter.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Multi-site stock imbalance is genuinely expensive and the standard response makes it "
        "worse: a report of imbalances, generated weekly, which somebody works through by moving "
        "things. That produces a great deal of van time and picking labour, a fair number of "
        "transfers that reverse themselves, and stock that is temporarily missing."),
  ("p", "The version that works rejects most of the list. What is left is a small number of "
        "transfers that clearly pay, that do not hurt the source, and that ride on movements "
        "already scheduled. The value is as much in what it declines to propose as in what it "
        "proposes."),
  ("p", "The next four posts walk through each piece: when a transfer is actually worth it, how "
        "the source gets protected, how transfers get batched onto movements that already happen, "
        "and what in-transit stock does to your numbers. One diagram per post, a cost breakdown, "
        "and an engineering reference at the end."),
 ],
},
{
 "slug": "when-a-transfer-is-actually-worth-it",
 "title": "When a transfer is actually worth it",
 "nav": "When it is worth it",
 "read": 5, "words": 750,
 "desc": ("The arithmetic on both sides, why the stock value is the wrong benefit, and the "
          "transfers that reverse themselves."),
 "og": ("The benefit of a transfer is not the value of the stock. It is the margin on sales that "
        "would otherwise be lost, which is a much smaller number."),
 "abstract": ("What a transfer actually costs at both ends, how the benefit should be computed, "
              "why low value items rarely qualify, and how ping-pong transfers are prevented."),
 "lede": ("The arithmetic is straightforward and it is almost never done, which is why stock "
          "transfer is one of the more reliable ways for a multi-site business to spend money "
          "without noticing."),
 "tags": ["stock transfer", "economics", "inventory", "margin", "operations", "serverless"],
 "takeaways": [
  "Cost is picking, packing, transport share, receiving and putting away. All five.",
  "Benefit is margin on sales protected, discounted by whether they would happen anyway.",
  "Low-value, low-margin items essentially never qualify.",
  "A transfer that would reverse within a quarter should not happen at all.",
  "State the arithmetic on every proposal so it can be argued with.",
 ],
 "blocks": [
  ("h2", "Both sides of the sum"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Cost, dedicated trip", "parts": [("pick", 4), ("pack", 2), ("move", 32),
                                                   ("recv", 4)]},
      {"label": "Cost, on a movement", "parts": [("pick", 4), ("pack", 2), ("move", 1),
                                                  ("recv", 4)]},
      {"label": "Benefit", "parts": [("ben", 28)]}],
    "series": [("pick", "Picking", "#ED7100"),
               ("pack", "Packing and paperwork", "#E7157B"),
               ("move", "Transport share", "#8C4FFF"),
               ("recv", "Receiving and putting away", "#DD344C"),
               ("ben", "Margin protected", "#7AA116")],
    "unit": "£",
    "note": "The same transfer fails on a dedicated trip and clears on Thursday's van."}),
   "One transfer costed two ways against its benefit. Transport is the swing factor and it is "
   "almost entirely a scheduling question.",
   "The cost of one stock transfer on a dedicated trip and on an existing movement",
   "A stacked bar chart with three bars in pounds. Five series: picking in orange, packing and "
   "paperwork in pink, transport share in purple, receiving and putting away in red, and margin "
   "protected in green. Cost on a dedicated trip: four pounds picking, two packing, thirty-two "
   "transport and four receiving. Cost on an existing movement: four picking, two packing, one "
   "transport and four receiving. Benefit: twenty-eight pounds of margin protected. A note says "
   "the same transfer fails on a dedicated trip and clears on Thursday's van."),
  ("h3", "The four fixed costs"),
  ("p", "Picking, packing, receiving and putting away are labour and they do not scale down. "
        "Moving one unit costs almost the same as moving twenty, which has a direct consequence: "
        "small transfers are almost never worth it and the system should propose meaningful "
        "quantities or nothing."),
  ("p", "The figures do not need to be precise. Somebody estimating that a pick takes five "
        "minutes and receiving takes five minutes, at a stated hourly cost, produces numbers good "
        "enough to separate the transfers that obviously pay from the ones that obviously do not, "
        "which is most of them."),
  ("h2", "The benefit is not the stock value"),
  ("p", "This is the error that makes almost every transfer look worthwhile. Moving twenty-two "
        "units of a fourteen-pound item is not a three-hundred-pound benefit; the stock is worth "
        "the same wherever it sits."),
  ("p", "The benefit is the margin on sales that would otherwise not happen, and it needs two "
        "discounts applied to it."),
  ("fig", ("chain", {
    "entry": {"title": "Units to move", "sub": ["22"], "icon": "storage"},
    "steps": [
      {"title": "Sales protected", "sub": ["how many would be lost?"], "icon": "chart"},
      {"title": "Times margin", "sub": ["not selling price"], "icon": "money"},
      {"title": "Discount: substitution", "sub": ["would they buy something else?"],
       "icon": "filter", "side": {"title": "Often yes", "sub": ["a similar product"],
                                  "icon": "form"}},
      {"title": "Discount: it sells anyway", "sub": ["eventually, at source"], "icon": "clock"},
      {"title": "The real benefit", "sub": ["usually much smaller"], "icon": "counter"}],
    "note": "Both discounts are judgements. State them; do not bury them in a coefficient."}),
   "How the benefit of a transfer is computed. The two discounts are where an apparently large "
   "benefit becomes a modest one.",
   "How the real benefit of a stock transfer is calculated",
   "A vertical chain of five steps entered by a box labelled Units to move, twenty-two. Step one "
   "asks how many sales would be lost, giving sales protected. Step two multiplies by margin "
   "rather than selling price. Step three discounts for substitution, asking whether customers "
   "would buy something else, with a side box saying often yes, a similar product. Step four "
   "discounts for the stock selling anyway, eventually, at the source. Step five gives the real "
   "benefit, usually much smaller. A note says both discounts are judgements, so state them "
   "rather than burying them in a coefficient."),
  ("h3", "Substitution matters most"),
  ("p", "In a business where products have close substitutes, a stockout frequently costs nothing "
        "at all: the customer buys the next size, the other colour, or the equivalent brand. In a "
        "business where they do not, a stockout is a lost sale and sometimes a lost customer."),
  ("p", "That is a judgement about the product range and it should be set per category by "
        "somebody who knows it, visible in configuration. A single global substitution assumption "
        "will be wrong for half the range in one direction or the other."),
  ("h2", "Ping-pong"),
  ("fig", ("strip", {
    "stages": [
      {"title": "March: A to B", "sub": ["B was low"], "icon": "truck"},
      {"title": "B sells 3", "sub": ["not 9 as expected"], "icon": "chart"},
      {"title": "May: A is low", "sub": ["A sold through"], "icon": "storage"},
      {"title": "May: B to A", "sub": ["the same units"], "icon": "truck"},
      {"title": "Cost: £18", "sub": ["benefit: nothing"], "icon": "alarm"}],
    "title": "THE TRANSFER THAT REVERSED",
    "note": "Both transfers were justified on the day. Together they were pure cost."}),
   "A ping-pong transfer. Each leg passed the test on its own and the pair achieved nothing, which "
   "is why the check has to look backwards.",
   "A stock transfer that reversed itself within two months",
   "A horizontal row of five boxes. March: A to B, because B was low. B sells three, not the nine "
   "expected. May: A is low, having sold through. May: B to A, the same units. Cost: eighteen "
   "pounds, benefit: nothing. A note says both transfers were justified on the day and together "
   "they were pure cost."),
  ("p", "The prevention is simple: before proposing a transfer, check whether the same item moved "
        "in the opposite direction between the same two sites within the last quarter. If it did, "
        "either the demand estimate at one end is wrong or the item is being managed by stock "
        "level rather than by sales, and both are worth investigating rather than transferring "
        "again."),
  ("p", "It is worth counting reversed transfers as a metric. A business where ten per cent of "
        "transfers reverse within a quarter has a demand estimation problem that is costing more "
        "than the imbalances are."),
  ("p", "Next: not breaking the site it came from."),
 ],
},
{
 "slug": "how-the-source-gets-protected",
 "title": "How the source gets protected",
 "nav": "Protecting the source",
 "read": 5, "words": 720,
 "desc": ("Cover at the source, the slow-selling item that still needs one on the shelf, and the "
          "transfer that creates the next stockout."),
 "og": ("A transfer that fixes a shortage at one branch by creating one at another has moved the "
        "problem and paid for the privilege."),
 "abstract": ("Why the source needs its own cover rule, the difference between surplus and "
              "display stock, how transfers are sized, and the site that is always the donor."),
 "lede": ("The easiest way to make a transfer planner harmful is to let it optimise the "
          "destination without any constraint on the source, at which point it will steadily "
          "strip the quiet branches."),
 "tags": ["stock transfer", "inventory", "safety stock", "multi-site", "retail", "serverless"],
 "takeaways": [
  "The source keeps its own cover, computed from its own demand.",
  "A slow-selling item still needs one on the shelf if it is displayed.",
  "Size the transfer from the surplus above cover, not from the destination's need.",
  "Watch for a site that is always the donor; it is usually a symptom.",
  "A site with zero of something it displays is a different problem from a stockout.",
 ],
 "blocks": [
  ("h2", "Cover at both ends"),
  ("fig", ("chain", {
    "entry": {"title": "A candidate transfer", "sub": ["A has surplus, B needs it"],
              "icon": "scale"},
    "steps": [
      {"title": "A's own cover", "sub": ["weeks of its own demand"], "icon": "shield"},
      {"title": "Plus display minimum", "sub": ["if it is on a shelf"], "icon": "storage",
       "side": {"title": "Often one or two", "sub": ["regardless of demand"], "icon": "form"}},
      {"title": "Surplus above that", "sub": ["the movable quantity"], "icon": "counter"},
      {"title": "Enough to be worth it?", "sub": ["fixed costs do not scale"], "icon": "branch",
       "exit": {"title": "No transfer", "sub": ["too small to pay"], "icon": "stop",
                "label": "no"}},
      {"title": "Move the smaller of", "sub": ["surplus, or B's need"], "icon": "truck"}],
    "note": "The display minimum is the rule people forget, and customers notice it immediately."}),
   "How the movable quantity is determined. The source's requirements are computed first and the "
   "destination gets what is left over.",
   "How the quantity available to transfer from a source site is determined",
   "A vertical chain of five steps entered by a box labelled A candidate transfer, where A has "
   "surplus and B needs it. Step one computes A's own cover in weeks of its own demand. Step two "
   "adds the display minimum if the item is on a shelf, with a side box noting it is often one or "
   "two regardless of demand. Step three computes the surplus above that, giving the movable "
   "quantity. Step four asks whether it is enough to be worth it, since fixed costs do not scale; "
   "if not it exits to No transfer, too small to pay. Step five moves the smaller of the surplus "
   "or B's need. A note says the display minimum is the rule people forget, and customers notice "
   "it immediately."),
  ("h3", "Cover is per site"),
  ("p", "The source's cover requirement comes from its own demand and its own replenishment lead "
        "time, exactly as it would if no transfer were being considered. A branch selling one a "
        "month with a four-week supplier lead time needs a couple in stock; a branch selling nine "
        "a month needs considerably more."),
  ("p", "Using a single company-wide minimum produces the wrong answer at both ends: it strips "
        "the busy branches too far and leaves too much at the quiet ones, which is the imbalance "
        "the system is supposed to be reducing."),
  ("h3", "Display stock is not surplus"),
  ("p", "An item that sits on a shelf where customers can see it needs at least one there, even "
        "if it sells twice a year. A transfer that takes the last one leaves a gap on a shelf and "
        "removes the only way anybody discovers the product exists."),
  ("p", "This is a rule that any experienced retailer states immediately and that essentially no "
        "automated system implements, because it is a merchandising fact rather than an inventory "
        "one. One field per product, set once."),
  ("h2", "The permanent donor"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Branch 1", "parts": [("out", 4), ("inn", 31)]},
      {"label": "Branch 2", "parts": [("out", 12), ("inn", 14)]},
      {"label": "Branch 3", "parts": [("out", 38), ("inn", 3)]},
      {"label": "Branch 4", "parts": [("out", 9), ("inn", 16)]}],
    "series": [("out", "Transfers out, this year", "#ED7100"),
               ("inn", "Transfers in, this year", "#7AA116")],
    "unit": "",
    "note": "Branch 3 gives and does not receive. Its buying is wrong, not its stock."}),
   "A year of transfers by branch. A site that is consistently the donor is usually being "
   "over-ordered rather than being a useful reservoir.",
   "Transfers in and out of four branches over a year",
   "A stacked bar chart with four bars. Two series: transfers out this year in orange, and "
   "transfers in in green. Branch one: four out and thirty-one in. Branch two: twelve out and "
   "fourteen in. Branch three: thirty-eight out and three in. Branch four: nine out and sixteen "
   "in. A note says branch three gives and does not receive, so its buying is wrong rather than "
   "its stock."),
  ("p", "This pattern is a genuinely useful finding and it is invisible when transfers are looked "
        "at one at a time. A branch that is permanently the donor is receiving stock it does not "
        "sell, and the fix is in whatever decides how much it gets, not in moving things "
        "afterwards."),
  ("p", "Transfers in that case are the symptom management: real money spent every month to "
        "correct a purchasing allocation that could be corrected once. Putting the chart in front "
        "of whoever sets allocations is worth more than any individual transfer."),
  ("h3", "Zero is not always a stockout"),
  ("p", "A site with none of a product it never sells and does not display is fine, and flagging "
        "it as a stockout produces a stream of transfer proposals for things nobody wants there. "
        "The distinction is whether the site ranges the product, which is a decision somebody "
        "made, not something to infer from a stock level."),
  ("p", "Ranging is one flag per product per site and it removes a large amount of noise. Without "
        "it, the imbalance detector treats every product as if every site should carry it."),
  ("p", "Next: waiting for a van."),
 ],
},
{
 "slug": "how-transfers-get-batched",
 "title": "How transfers get batched onto movements that already happen",
 "nav": "How they get batched",
 "read": 5, "words": 720,
 "desc": ("Holding a proposal until a vehicle is going that way, how long is too long to wait, "
          "and the transfers that justify their own trip."),
 "og": ("Transport is the swing factor in almost every transfer decision, and it is nearly free "
        "on a van that is already making the journey."),
 "abstract": ("Why batching changes the economics, how long a proposal can wait, how a full "
              "movement is assembled, and when a dedicated trip is justified."),
 "lede": ("The single change that makes stock transfer worthwhile in most businesses is not "
          "better detection; it is waiting until Thursday."),
 "tags": ["stock transfer", "logistics", "batching", "scheduling", "transport", "serverless"],
 "takeaways": [
  "A proposal waits for a scheduled movement rather than triggering one.",
  "Set a maximum wait; beyond it the benefit has decayed and the proposal expires.",
  "Assemble the whole load for a movement at once, so picking is one trip round the racking.",
  "A dedicated trip needs a benefit several times larger, and sometimes that exists.",
  "Urgent transfers bypass all of this, and should be counted.",
 ],
 "blocks": [
  ("h2", "Waiting for a van"),
  ("fig", ("chain", {
    "entry": {"title": "A transfer clears", "sub": ["on the economics"], "icon": "check"},
    "steps": [
      {"title": "Movement scheduled?", "sub": ["A to B, next 10 days"], "icon": "branch",
       "exit": {"title": "Hold", "sub": ["recheck daily"], "icon": "clock", "label": "no"}},
      {"title": "Space on it?", "sub": ["volume and weight"], "icon": "branch",
       "exit": {"title": "Next one", "sub": ["or split it"], "icon": "truck", "label": "no"}},
      {"title": "Still needed?", "sub": ["B may have sold out", "or been replenished"],
       "icon": "branch",
       "exit": {"title": "Cancel", "sub": ["quietly"], "icon": "stop", "label": "no"}},
      {"title": "Add to the load", "sub": ["with everything else going"], "icon": "storage"},
      {"title": "One pick list", "sub": ["for the whole movement"], "icon": "form"}],
    "note": "The third gate matters: a proposal made nine days ago may have been overtaken."}),
   "How a proposal becomes a picked transfer. Rechecking at the point of picking prevents the most "
   "common form of wasted movement.",
   "How a transfer proposal is attached to a scheduled vehicle movement",
   "A vertical chain of five steps entered by a box labelled A transfer clears on the economics. "
   "Step one asks whether a movement from A to B is scheduled in the next ten days; if not it "
   "exits to Hold, rechecking daily. Step two asks whether there is space on it by volume and "
   "weight; if not it exits to Next one, or split it. Step three asks whether it is still needed, "
   "since B may have sold out or been replenished; if not it exits to Cancel, quietly. Step four "
   "adds it to the load with everything else going. Step five produces one pick list for the "
   "whole movement. A note says the third gate matters, because a proposal made nine days ago may "
   "have been overtaken."),
  ("h3", "One pick list per movement"),
  ("p", "This is where a second saving hides. Twelve separate transfers picked individually is "
        "twelve trips round the warehouse; the same twelve as one consolidated pick list, ordered "
        "by location, is one trip and perhaps a third of the labour."),
  ("p", "Which changes the economics again, and in the right direction: the per-transfer picking "
        "cost falls as the batch grows, so a set of marginal transfers can become collectively "
        "worthwhile when none of them would be individually. The economic test therefore runs "
        "against the batch as well as the item."),
  ("h2", "How long to wait"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Wait 0 days", "parts": [("ben", 28), ("cost", 42)]},
      {"label": "Wait 4 days", "parts": [("ben", 24), ("cost", 11)]},
      {"label": "Wait 11 days", "parts": [("ben", 14), ("cost", 11)]},
      {"label": "Wait 25 days", "parts": [("ben", 4), ("cost", 11)]}],
    "series": [("ben", "Benefit remaining, £", "#7AA116"),
               ("cost", "Cost of the transfer, £", "#DD344C")],
    "unit": "£",
    "note": "Waiting saves transport and spends benefit. Four days is the sweet spot here."}),
   "The trade between waiting and acting. Benefit decays because the destination either loses the "
   "sales or gets replenished normally, so an indefinite hold is not free.",
   "How the benefit and cost of a transfer change with waiting time",
   "A stacked bar chart with four bars in pounds. Two series: benefit remaining in green, and "
   "cost of the transfer in red. Waiting zero days: twenty-eight pounds of benefit against "
   "forty-two pounds of cost. Waiting four days: twenty-four against eleven. Waiting eleven days: "
   "fourteen against eleven. Waiting twenty-five days: four against eleven. A note says waiting "
   "saves transport and spends benefit, and four days is the sweet spot here."),
  ("p", "The decay is real and has two causes. The destination may lose the sales it was going to "
        "protect, and it may get replenished from the supplier in the normal course, at which "
        "point the transfer is unnecessary."),
  ("p", "So proposals expire. A maximum hold of around the destination's own replenishment lead "
        "time is a defensible default: beyond that, the normal supply chain will have solved it "
        "and the transfer is redundant."),
  ("h3", "When a dedicated trip is justified"),
  ("p", "Occasionally the benefit is large enough: a high-value item, a customer waiting, a "
        "seasonal peak where the sales genuinely will not happen otherwise. Those exist and the "
        "system should be able to say so, with the arithmetic showing why this one clears a much "
        "higher bar."),
  ("p", "The bar should be several times the transfer cost rather than merely above it, because "
        "the estimates on the benefit side are soft and a dedicated trip commits real money "
        "against a soft number."),
  ("h2", "Urgent transfers"),
  ("callout", "The ones that bypass everything", [
   "<strong>A customer is waiting</strong> and the sale is confirmed. Move it.",
   "<strong>A production line is stopped.</strong> Move it.",
   "<strong>These do not need an economic test</strong> because the benefit is known and large.",
   "<strong>They do need recording as urgent</strong>, separately from planned transfers.",
   "<strong>Because the count is a signal:</strong> a lot of urgent transfers means the planned "
   "ones are not happening, or the stock allocation is wrong.",
   "<strong>Never make the urgent path harder</strong> than picking up the phone. It will simply "
   "be routed around.",
  ]),
  ("p", "The counting point is the useful one. Urgent transfers are expensive &mdash; they are "
        "dedicated trips by definition &mdash; and a business running twenty a month is spending "
        "significantly on something that a better allocation would largely remove."),
  ("p", "Next: where the stock actually is while it is moving."),
 ],
},
{
 "slug": "what-in-transit-stock-does-to-your-numbers",
 "title": "What in-transit stock does to your numbers",
 "nav": "In-transit stock",
 "read": 5, "words": 710,
 "desc": ("Stock that is at neither end, the double count, the disappearance, and how a transfer "
          "is closed."),
 "og": ("Stock in a van belongs to neither site. Systems that cannot express that either lose it "
        "or count it twice, and both happen."),
 "abstract": ("Why in-transit needs to be a real state, the two failure modes of not modelling "
              "it, how transfers are confirmed at both ends, and the stock that never arrives."),
 "lede": ("A transfer takes a day or a week, and during that time the stock is somewhere that "
          "most inventory systems have no way of describing, which produces two opposite and "
          "equally annoying errors."),
 "tags": ["stock transfer", "inventory accuracy", "in-transit", "reconciliation", "stock control",
          "serverless"],
 "takeaways": [
  "In-transit is a real location with a real balance, not a gap between two sites.",
  "Deduct at despatch, add at receipt, and never both at once or neither.",
  "A transfer open longer than expected is an exception worth chasing.",
  "Confirm the quantity at the receiving end; discrepancies happen.",
  "Reconcile in-transit monthly. It should be nearly empty.",
 ],
 "blocks": [
  ("h2", "Two failure modes"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Deduct at receipt only", "sub": ["A still shows it"], "icon": "storage",
       "label": "double count"},
      {"title": "Deduct at despatch only", "sub": ["B does not have it yet"], "icon": "question",
       "label": "disappeared"},
      {"title": "In-transit location", "sub": ["a real balance"], "icon": "truck",
       "label": "correct"}],
    "target": {"title": "The stock exists", "sub": ["somewhere, always"], "icon": "check",
               "then": {"title": "And can be counted", "sub": ["at any moment"], "icon": "counter"}},
    "note": "The first two are the common implementations and both produce phantom stock."}),
   "Three ways of handling stock that has left one site and not reached another. Only the third "
   "keeps the total correct at every instant.",
   "Three ways of accounting for stock in transit between sites",
   "Three boxes stacked on the left. Deduct at receipt only, where A still shows it, labelled "
   "double count. Deduct at despatch only, where B does not have it yet, labelled disappeared. "
   "And In-transit location, holding a real balance, labelled correct. All three converge on The "
   "stock exists somewhere, always, and that leads down to And can be counted at any moment. A "
   "note says the first two are the common implementations and both produce phantom stock."),
  ("h3", "The double count"),
  ("p", "Deducting only at receipt means the source shows stock it no longer physically has. "
        "Somebody at the source promises it to a customer, goes to pick it, and it is in a van "
        "eighty miles away. That is a customer-facing failure caused entirely by an accounting "
        "choice."),
  ("h3", "The disappearance"),
  ("p", "Deducting at despatch with nowhere to put it means the stock does not exist anywhere "
        "for the duration. The company-wide total is wrong, and a stock valuation run during that "
        "window under-reports. Over a month with regular transfers, some quantity is permanently "
        "in flight and permanently missing from the total."),
  ("h2", "Open and close"),
  ("fig", ("chain", {
    "entry": {"title": "A transfer is picked", "sub": ["at the source"], "icon": "storage"},
    "steps": [
      {"title": "Deduct from source", "sub": ["and add to in-transit"], "icon": "truck"},
      {"title": "Expected arrival", "sub": ["from the movement"], "icon": "clock"},
      {"title": "Received?", "sub": ["confirmed, with a count"], "icon": "branch",
       "exit": {"title": "Chase it", "sub": ["after the expected date"], "icon": "alarm",
                "label": "no"}},
      {"title": "Count matches?", "sub": ["despatched against received"], "icon": "branch",
       "exit": {"title": "Discrepancy", "sub": ["recorded, both ends notified"], "icon": "search",
                "label": "no"}},
      {"title": "Close the transfer", "sub": ["in-transit returns to zero"], "icon": "check"}],
    "note": "The fourth gate is the same three-way match as goods receipt, at a smaller scale."}),
   "The lifecycle of one transfer. Confirming a count at the receiving end catches the same class "
   "of error as receiving from a supplier.",
   "How a stock transfer moves through in-transit and closes",
   "A vertical chain of five steps entered by a box labelled A transfer is picked at the source. "
   "Step one deducts from the source and adds to in-transit. Step two sets an expected arrival "
   "from the movement. Step three asks whether it has been received, confirmed with a count; if "
   "not it exits to Chase it, after the expected date. Step four asks whether the count matches "
   "despatched against received; if not it exits to Discrepancy, recorded with both ends "
   "notified. Step five closes the transfer and in-transit returns to zero. A note says the "
   "fourth gate is the same three-way match as goods receipt, at a smaller scale."),
  ("h3", "Counting at the receiving end"),
  ("p", "It is tempting to skip, because it is internal stock moving between your own sites and "
        "nobody is trying to short you. The reason to do it anyway is that picking errors happen "
        "at the same rate internally as anywhere else, and an unconfirmed transfer means a "
        "discrepancy surfaces months later in a stock count with no way to trace it."),
  ("p", "A count at receipt turns that into a same-week question with two named people who can "
        "both remember the box."),
  ("h2", "The monthly reconciliation"),
  ("fig", ("strip", {
    "stages": [
      {"title": "In-transit balance", "sub": ["month end"], "icon": "truck"},
      {"title": "Should be small", "sub": ["a day or two of flow"], "icon": "counter"},
      {"title": "Anything old?", "sub": ["over 14 days"], "icon": "search"},
      {"title": "Chase or write off", "sub": ["with a decision"], "icon": "person"},
      {"title": "Back to near zero", "sub": ["every month"], "icon": "check"}],
    "title": "IN-TRANSIT SHOULD BE NEARLY EMPTY",
    "note": "A growing in-transit balance is transfers that were never confirmed, not stock."}),
   "The monthly check. A rising in-transit balance is a process failure rather than an inventory "
   "position, and it is easy to miss because nobody owns that location.",
   "How the in-transit balance is reconciled monthly",
   "A horizontal row of five boxes. In-transit balance at month end. Should be small, a day or "
   "two of flow. Anything old, over fourteen days? Chase or write off, with a decision. Back to "
   "near zero, every month. A note says a growing in-transit balance is transfers that were never "
   "confirmed, rather than stock."),
  ("p", "In practice the ageing in-transit balance is almost always paperwork: the stock arrived "
        "and nobody confirmed it. Which is worth knowing, because it means the receiving site has "
        "physical stock its system does not know about, and that surfaces as a positive variance "
        "at the next count."),
  ("h3", "The stock that genuinely did not arrive"),
  ("p", "Rare and it happens: a box left on a van, delivered to the wrong site, or picked and "
        "never loaded. The trace is short because both ends are yours, and the resolution is "
        "usually finding it somewhere."),
  ("p", "What matters is that it is a recorded event with a decision at the end, rather than a "
        "line that ages quietly until somebody writes off the whole in-transit balance at year "
        "end without looking at what was in it."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="SKU-site pair",
 volumes=[(20000, "20,000 pairs"), (80000, "80,000 pairs"), (300000, "300,000 pairs")],
 read_each=0.0,
 msgs_each=0.0,
 lede=("There is no model in this system and the volume is the nightly imbalance scan: five "
       "thousand products across sixteen sites is eighty thousand pairs. Here is where each cent "
       "goes."),
 takeaway_extra=("The nightly scan is the whole variable cost, and it is compute rather than "
                 "storage."),
 risks=[
  "<strong>Scanning every pair every night.</strong> Only products whose stock or sales changed "
  "need re-evaluating, which is a small fraction on any given day.",
  "<strong>Recomputing demand history per pair per night.</strong> Weekly demand rates move "
  "slowly. Compute them once a week and cache.",
  "<strong>Storing a proposal per pair.</strong> Only proposals that clear the economic test are "
  "worth writing; the rejected ones are a count, not a record.",
 ],
 per_unit_note=("There is no read line and no messaging line: the output is a pick list, not an "
                "email. Compute for the nightly scan is the entire variable cost."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="st",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the in-transit location, and the economic test."),
 outside=[
  {"title": "Stock and sales", "sub": ["per site, read only"], "icon": "storage"},
  {"title": "Vehicle schedule", "sub": ["planned movements"], "icon": "truck"},
  {"title": "Pick lists", "sub": ["one per movement"], "icon": "form"}],
 inside=[
  {"title": "EventBridge nightly", "sub": ["scan, then", "batch at cut-off"], "icon": "clock"},
  {"title": "Lambda x3", "sub": ["scan, evaluate, batch"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["proposals, transfers"], "icon": "database"}],
 note="us-east-1. One account. In-transit is a site id like any other, with a real balance.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Stock and sales per site, read only. The "
  "vehicle schedule of planned movements. And Pick lists, one per movement. Inside the account, "
  "three groups. EventBridge running a nightly scan and a batch at cut-off. Three Lambda "
  "functions named scan, evaluate and batch. And two DynamoDB tables named proposals and "
  "transfers. A note gives the region as us-east-1, one account, and states that in-transit is a "
  "site id like any other, with a real balance."),
 functions=[
  ["<code>st-scan</code>", "EventBridge, nightly",
   "Finds imbalances among pairs whose stock or sales changed; applies ranging and cover rules",
   "300s / 2048&nbsp;MB"],
  ["<code>st-evaluate</code>", "DynamoDB stream on proposals",
   "Runs the economic test, the ping-pong check and the source protection rule",
   "60s / 1024&nbsp;MB"],
  ["<code>st-batch</code>", "EventBridge, at each movement cut-off",
   "Rechecks need, assembles the load, emits one consolidated pick list",
   "120s / 1024&nbsp;MB"]],
 roles=[
  ["<code>st-scan-role</code>", "<code>dynamodb:Query</code>, <code>dynamodb:PutItem</code>",
   "Read-only on stock and sales; writes proposals"],
  ["<code>st-evaluate-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>", "Proposals and transfers"],
  ["<code>st-batch-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>s3:PutObject</code>",
   "Both tables; the pick list prefix"]],
 tables=[
  ("Table: proposals",
   "PK   sku               S\n"
   "SK   from#to#made_on   S   br3#br1#2026-08-24\n"
   "     qty               N   the smaller of surplus and need\n"
   "     benefit_pence     N   margin protected, after both discounts\n"
   "     cost_pence        N   pick + pack + transport share + receive\n"
   "     on_movement       BOOL true if a scheduled movement exists\n"
   "     source_cover_wks  N   what A keeps, after the transfer\n"
   "     expires_at        S   B's own replenishment lead time\n"
   "     rejected_reason   S   too_small | ping_pong | source_cover | uneconomic\n\n"
   "Rejected proposals are counted, not stored. The reason distribution is\n"
   "the useful output: mostly `uneconomic` means the detector is too loose."),
  ("Table: transfers",
   "PK   transfer_id       S\n"
   "     sku               S\n"
   "     from_site         S\n"
   "     to_site           S\n"
   "     qty_despatched    N\n"
   "     qty_received      N   confirmed at the far end, not assumed\n"
   "     despatched_at     S   stock moves to site id 'in_transit' here\n"
   "     expected_at       S\n"
   "     received_at       S   stock moves to to_site here\n"
   "     urgent            BOOL bypassed the economic test\n"
   "     discrepancy       N   despatched minus received, if non-zero\n\n"
   "`in_transit` is an ordinary site id, so the company-wide total is\n"
   "correct at every instant and the balance can be reconciled monthly.")],
 inbound=[
  "<strong>Stock and sales are read, never written.</strong> This system proposes; the stock "
  "system records the movement.",
  "<strong>Ranging and display minimums are per product per site</strong>, set by somebody who "
  "knows the range. Without them the scan proposes transfers for products the site never sells.",
  "<strong>The vehicle schedule is an input</strong>, not something this system creates. A "
  "transfer never triggers a journey.",
  "<strong>Need is rechecked at the movement cut-off</strong>, because a proposal made nine days "
  "ago may have been overtaken by a normal replenishment."],
 model_notes=[
  "<strong>There is no model in this system.</strong> The imbalance test is a comparison of cover "
  "weeks and the economic test is arithmetic.",
  "<strong>The tempting use</strong> is demand forecasting per site per product. At single-site "
  "granularity most products sell in ones and a trailing rate is as good as anything.",
  "<strong>A second tempting use</strong> is estimating substitution probability. It is a "
  "judgement about the range, better set per category by a person and visible in configuration.",
  "<strong>Explainability matters here</strong> because somebody is being asked to spend twenty "
  "minutes picking. The arithmetic goes on the proposal.",
  "<strong>The cost page assumes none</strong>, which is why the scan is the only variable."],
 gotchas=[
  "Model in-transit as a real location. Deducting at despatch with nowhere to put it makes stock "
  "vanish; deducting at receipt promises stock that is in a van.",
  "Compute the benefit from margin protected, not stock value. Stock value makes every transfer "
  "look worthwhile and none of them are.",
  "Check for a reverse transfer within the last quarter before proposing. Both legs of a "
  "ping-pong pass the test individually.",
  "Keep a display minimum per product per site. A transfer that takes the last one off a shelf is "
  "a merchandising failure no inventory rule will catch.",
  "Recheck need at the cut-off, not only when the proposal is made. Normal replenishment "
  "frequently solves it in the intervening week."],
))
