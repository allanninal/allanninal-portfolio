"""Day 124 -- 2026-08-26 -- Allergen checker."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "allergen-checker"
NAME = "Allergen checker"

SPEC = {
 "slug": SLUG, "date": "2026-08-26", "name": NAME,
 "tagline": ("Tracks what every ingredient declares, notices when a supplier quietly reformulates "
             "something, and is explicit about the large category of things it cannot know -- "
             "because a system that says a dish is safe is making a promise it cannot keep."),
 "lede": ("A small system that holds allergen declarations against ingredients, rolls them up to "
          "dishes, catches supplier specification changes, and flags substitutions. It never "
          "declares anything safe. What it produces is an accurate, current, dated statement of "
          "what is declared and what is unknown, so that the conversation between a customer and "
          "a member of staff is based on something real. Seven posts on the same system, one "
          "diagram at a time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["allergens", "food safety", "labelling", "hospitality", "compliance", "serverless"],
 "icons": ["shield", "form", "alarm"],
 "faq": [
  ("What is an allergen checker?",
   "A small serverless system that stores allergen declarations against ingredients, rolls them up "
   "to dishes, and flags when a supplier specification or a substitution changes what a dish "
   "contains."),
  ("Does it say whether a dish is safe?",
   "No, and that is the most important design decision in it. It reports what is declared and "
   "what is unknown. Safety involves cross-contamination and judgement that no data can capture."),
  ("What is the biggest real-world risk?",
   "A supplier reformulating an ingredient without anybody noticing. The recipe did not change, "
   "the dish did, and there is no event in most systems that catches it."),
  ("How does it treat unknown ingredients?",
   "As unknown, prominently, and never as absent. An ingredient with no current specification "
   "makes every dish containing it incomplete rather than clear."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "allergen-checker-on-aws",
 "title": "An allergen checker on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Tracks allergen declarations, catches supplier changes and substitutions, and never "
          "declares a dish safe. AWS, about $2 a month."),
 "og": ("A system that outputs 'safe' has made a promise about a kitchen it cannot see. What it "
        "can honestly produce is 'declared' and 'unknown'."),
 "abstract": ("The whole system on one page -- declare, roll up, watch &mdash; and the deliberate "
              "refusal to produce a safety verdict."),
 "lede": ("A recipe has not changed in two years. Last month the supplier of one ingredient "
          "reformulated it and the new specification includes mustard. Nothing in the kitchen "
          "changed, nothing in the recipe changed, and the dish now contains an allergen it did "
          "not contain before. There is no event anywhere that catches this, which is what this "
          "post is about."),
 "tags": ["allergens", "food safety", "labelling", "hospitality", "compliance", "serverless"],
 "takeaways": [
  "Unknown is never treated as absent. It is reported as unknown, prominently.",
  "Supplier specification changes are the largest real risk and need an explicit check.",
  "The system reports what is declared; it never declares a dish safe.",
  "A substitution changes the allergen profile and must be caught before service.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Supplier specs", "sub": ["what each ingredient", "declares"], "icon": "doc"},
      {"title": "Recipes", "sub": ["and substitutions"], "icon": "form"},
      {"title": "Whoever is asked", "sub": ["by a customer"], "icon": "person"}],
    "inside": [
      {"title": "Declarations", "sub": ["contains, may contain,", "unknown"], "icon": "shield"},
      {"title": "Roll-up", "sub": ["ingredient to dish,", "dated"], "icon": "filter"},
      {"title": "Change watch", "sub": ["specs and", "substitutions"], "icon": "alarm"}],
    "edges": [{"from": 0, "to": 0, "label": "specifications"},
              {"from": 1, "to": 1, "label": "what is in what"},
              {"from": 2, "to": 2, "label": "declared and unknown", "up": True}],
    "note": "The output has two lists. There is no third list called 'safe'."}),
   "Three things outside the account, three pieces inside it. The output is deliberately two "
   "lists rather than a verdict.",
   "System: allergen declarations rolled up to dishes with changes watched",
   "Three boxes across the top sit outside the AWS account. On the left, Supplier specs, holding "
   "what each ingredient declares. In the middle, Recipes and substitutions. On the right, "
   "Whoever is asked by a customer. Each connects by an arrow to the AWS account container below. "
   "Specifications flow down into the account. What is in what feeds in. Declared and unknown go "
   "back out. Inside the AWS account are three components in a row. On the left, Declarations, "
   "covering contains, may contain and unknown. In the middle, the Roll-up from ingredient to "
   "dish, dated. On the right, Change watch, following specifications and substitutions. A note "
   "at the bottom says the output has two lists, and there is no third list called safe."),
  ("h3", "What this system is not"),
  ("p", "It is not a safety decision. Whether a particular dish is appropriate for a particular "
        "person depends on the severity of their allergy, on what else is being prepared on the "
        "same surfaces, on whether the fryer is shared, and on a hundred things that exist in a "
        "kitchen and not in a database."),
  ("p", "What a data system can genuinely do is make sure that the declared information is "
        "accurate and current, that gaps in it are visible rather than silent, and that a change "
        "somewhere in the supply chain does not go unnoticed for a year. That is a narrower claim "
        "and it is a real one."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>Declarations.</strong> What each ingredient states, in three categories rather than "
   "two. Part 2.",
   "<strong>The roll-up.</strong> Combining ingredient declarations into a dish-level statement "
   "with a date. Part 2.",
   "<strong>Change watch.</strong> Supplier reformulations and kitchen substitutions, which are "
   "the two ways a dish changes without anybody deciding it should. Parts 3 and 5.",
  ]),
  ("h2", "One change, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "New spec arrives", "sub": ["same product code"], "icon": "doc"},
      {"title": "Compared", "sub": ["mustard added"], "icon": "search"},
      {"title": "9 dishes affected", "sub": ["listed by name"], "icon": "form"},
      {"title": "Flagged, not fixed", "sub": ["a person reviews"], "icon": "alarm"},
      {"title": "Menu updated", "sub": ["with a date"], "icon": "check"}],
    "title": "ONE SUPPLIER CHANGE, END TO END",
    "note": "Without the second box this change is invisible until somebody reacts to it."}),
   "The same system as one line. The comparison in the second box is the entire mechanism, and it "
   "only works if specifications are stored rather than read once.",
   "One supplier specification change traced through to affected dishes",
   "A horizontal row of five boxes joined by arrows. New spec arrives, same product code. "
   "Compared: mustard added. Nine dishes affected, listed by name. Flagged, not fixed: a person "
   "reviews. Menu updated, with a date. A note says without the second box this change is "
   "invisible until somebody reacts to it."),
  ("h2", "In plain words"),
  ("p", "A supplier sends an updated specification for a stock base. The product code is the same "
        "and the delivery looks identical. The system compares the new declaration against the "
        "stored one and finds that mustard has been added to the formulation."),
  ("p", "Nine dishes use that stock base. All nine are flagged, by name, with the ingredient that "
        "caused it and the date the specification changed. Nothing is automatically corrected: "
        "the menu, the allergen matrix and the staff briefing are all things a person updates, "
        "and the flag stays open until they do."),
  ("p", "The important property is that this is an event. In most kitchens a reformulation "
        "produces no event at all &mdash; the specification arrives in an email, or does not "
        "arrive, and the dish quietly contains something it did not contain last month."),
  ("callout", "Design rules that shaped every decision", [
   "Three states per allergen per ingredient: contains, may contain, unknown. Never two.",
   "Unknown is prominent. It is not absence and must never render as a blank.",
   "Every specification is stored with its date, so a change can be detected.",
   "The system flags; a person updates the menu and the briefing.",
   "It never outputs a safety verdict for a person.",
   "A substitution changes the dish and must be recorded before service.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Allergen management fails in two characteristic ways, and neither is a failure of "
        "intention. The first is that the information goes stale: a matrix produced accurately in "
        "March describes a menu that has changed by September. The second is that unknowns are "
        "rendered as absences, so a gap in the data looks exactly like a confirmed negative."),
  ("p", "Both are addressable by a small system that stores declarations with dates, compares "
        "them when they change, and refuses to collapse three states into two. Neither requires "
        "sophistication and both are difficult to maintain by hand across a menu of any size."),
  ("p", "The next four posts walk through each piece: how an ingredient declares what it "
        "contains, what happens when a supplier changes a recipe, why the system never says safe, "
        "and how a substitution gets caught. One diagram per post, a cost breakdown, and an "
        "engineering reference at the end."),
 ],
},
{
 "slug": "how-an-ingredient-declares-what-it-contains",
 "title": "How an ingredient declares what it contains",
 "nav": "How ingredients declare",
 "read": 5, "words": 750,
 "desc": ("Three states rather than two, what 'may contain' actually means, compound ingredients, "
          "and rolling up to a dish."),
 "og": ("A blank cell in an allergen matrix means either 'confirmed absent' or 'nobody checked', "
        "and those are not the same thing at all."),
 "abstract": ("Why three states are required, how may-contain is handled, compound ingredients "
              "and their nested declarations, and how a dish-level statement is assembled."),
 "lede": ("The single most consequential decision in an allergen data model is how many states an "
          "allergen can be in, and the common answer of two is wrong in a way that is genuinely "
          "dangerous."),
 "tags": ["allergens", "data model", "labelling", "food safety", "records", "serverless"],
 "takeaways": [
  "Three states: contains, may contain, unknown. A blank is never a negative.",
  "'May contain' is a manufacturer's precautionary statement, not a maybe.",
  "Compound ingredients nest; the declaration has to follow the tree down.",
  "A dish rolls up to the strongest state present across its ingredients.",
  "One unknown ingredient makes the dish's statement incomplete, and it should say so.",
 ],
 "blocks": [
  ("h2", "Three states"),
  ("table", ["State", "What it means", "How it renders"], [
   ["Contains", "The specification declares this allergen", "Named, unambiguously"],
   ["May contain", "A precautionary statement from the manufacturer",
    "Named, distinctly from contains"],
   ["Unknown", "No current specification, or it does not address this allergen",
    "Named as unknown, never blank"],
   ["Does not contain", "A current specification explicitly excludes it", "Blank is acceptable"],
  ]),
  ("p", "The fourth row is the only one where a blank is honest, and it requires a current "
        "specification that actually addresses the allergen. An ingredient whose specification "
        "predates the current allergen labelling requirements, or which simply does not mention "
        "celery, is unknown for celery rather than free of it."),
  ("p", "That distinction produces more unknowns than most people expect when a system is first "
        "populated, and that is the system working. A matrix that was all blanks and is now "
        "thirty per cent unknown has not got worse; it has become honest, and the unknowns are a "
        "work list."),
  ("h2", "May contain is not a maybe"),
  ("p", "\"May contain nuts\" is a statement by a manufacturer that their process cannot exclude "
        "cross-contamination. It is not uncertainty about the recipe and it is not something a "
        "kitchen can resolve by asking. It carries forward to any dish using that ingredient and "
        "it must be reported as what it is."),
  ("p", "Collapsing it into either contains or does not contain loses real information in both "
        "directions: treating it as contains removes dishes unnecessarily, and treating it as "
        "absent removes a warning the manufacturer thought was necessary."),
  ("h2", "Compound ingredients"),
  ("fig", ("chain", {
    "entry": {"title": "A dish", "sub": ["with a recipe"], "icon": "form"},
    "steps": [
      {"title": "Each recipe line", "sub": ["ingredient and quantity"], "icon": "counter"},
      {"title": "Is it compound?", "sub": ["a sauce, a base, a mix"], "icon": "branch",
       "exit": {"title": "Recurse into it", "sub": ["its own ingredients"], "icon": "route",
                "label": "yes"}},
      {"title": "Current spec?", "sub": ["dated, and recent"], "icon": "branch",
       "exit": {"title": "Unknown for all 14", "sub": ["not absent"], "icon": "question",
                "label": "no"}},
      {"title": "Take its declarations", "sub": ["contains, may contain"], "icon": "shield"},
      {"title": "Roll up to the dish", "sub": ["strongest state wins"], "icon": "filter"}],
    "note": "The recursion is where hand-maintained matrices break down on any real menu."}),
   "How a dish-level declaration is assembled. Compound ingredients nesting several levels deep "
   "is normal and is where manual maintenance becomes impractical.",
   "How allergen declarations roll up from ingredients to a dish",
   "A vertical chain of five steps entered by a box labelled A dish with a recipe. Step one takes "
   "each recipe line with its ingredient and quantity. Step two asks whether it is compound, such "
   "as a sauce, a base or a mix; if so it exits to Recurse into it, following its own "
   "ingredients. Step three asks whether there is a current specification, dated and recent; if "
   "not it exits to Unknown for all fourteen, not absent. Step four takes its declarations for "
   "contains and may contain. Step five rolls up to the dish, with the strongest state winning. A "
   "note says the recursion is where hand-maintained matrices break down on any real menu."),
  ("h3", "How deep it goes"),
  ("p", "A dish uses a sauce; the sauce uses a stock base; the stock base uses a seasoning blend; "
        "the seasoning blend contains an anti-caking agent. Four levels is not unusual and the "
        "allergen can be at the bottom."),
  ("p", "Maintaining that by hand across forty dishes is possible in principle and does not "
        "survive a supplier change, which is precisely the situation where accuracy matters most. "
        "The recursion is the part of this system that is genuinely hard to do without software."),
  ("h2", "The dish-level statement"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Contains", "parts": [("n", 3)]},
      {"label": "May contain", "parts": [("n", 2)]},
      {"label": "Unknown", "parts": [("n", 4)]},
      {"label": "Not present", "parts": [("n", 5)]}],
    "series": [("n", "Allergens in each state for one dish", "#8C4FFF")],
    "unit": "",
    "note": "Four unknowns is a work list, not a result. It renders as prominently as 'contains'."}),
   "One dish's fourteen allergens sorted into four states. The unknown column is the one that "
   "drives action, and hiding it would make the other three look complete.",
   "One dish's allergens sorted into four declaration states",
   "A bar chart with four bars showing the number of allergens in each state for one dish. "
   "Contains: three. May contain: two. Unknown: four. Not present: five. A note says four "
   "unknowns is a work list rather than a result, and it renders as prominently as contains."),
  ("p", "A dish with any unknowns has an incomplete statement, and that fact belongs at the top "
        "of it rather than in a footnote. A member of staff answering a question needs to know "
        "immediately whether they are working from complete information."),
  ("h3", "Chasing the unknowns"),
  ("p", "The unknown list is the system's main ongoing output. Each one is a specification to "
        "request from a supplier, and requesting them is straightforward: most suppliers have the "
        "document and will send it."),
  ("p", "Ranking by how many dishes an unknown ingredient affects makes the chasing efficient. "
        "One missing specification on a widely-used stock base can be responsible for half the "
        "unknowns on a menu, and one email resolves it."),
  ("p", "Next: the change nobody sees."),
 ],
},
{
 "slug": "what-happens-when-a-supplier-changes-a-recipe",
 "title": "What happens when a supplier changes a recipe",
 "nav": "Supplier changes",
 "read": 5, "words": 730,
 "desc": ("The reformulation with the same product code, why storing specs matters, and the "
          "expiry that forces a recheck."),
 "og": ("The recipe did not change and the dish did. There is no event in most kitchens that "
        "catches that."),
 "abstract": ("How reformulations happen without any visible signal, why specifications must be "
              "stored and compared, how specification age is handled, and what the flag does."),
 "lede": ("This is the failure mode that keeps people awake, and it is entirely invisible to a "
          "process that checks allergens when a recipe is written."),
 "tags": ["allergens", "suppliers", "change detection", "food safety", "specifications",
          "serverless"],
 "takeaways": [
  "A product code staying the same does not mean the product did.",
  "Store every specification version; comparison is only possible against a stored one.",
  "Specifications expire. An old one becomes unknown rather than staying valid.",
  "Flag the affected dishes by name, and keep the flag open until a person clears it.",
  "A supplier switch is the same event and is more common than a reformulation.",
 ],
 "blocks": [
  ("h2", "How it happens"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Same product code", "sub": ["same order, same price"], "icon": "form"},
      {"title": "Reformulated", "sub": ["by the manufacturer"], "icon": "gear"},
      {"title": "New spec issued", "sub": ["by email, or not"], "icon": "doc"},
      {"title": "Delivery looks identical", "sub": ["nobody notices"], "icon": "truck"},
      {"title": "The dish changed", "sub": ["with no event"], "icon": "alarm"}],
    "title": "THE CHANGE WITH NO SIGNAL",
    "note": "Every step here is normal commercial behaviour. None of it is anybody's failure."}),
   "How a dish acquires an allergen without anybody deciding. Nothing in this sequence is "
   "unusual, which is why it needs a system rather than vigilance.",
   "How a supplier reformulation changes a dish with no visible signal",
   "A horizontal row of five boxes. Same product code: same order, same price. Reformulated by "
   "the manufacturer. New spec issued by email, or not. Delivery looks identical and nobody "
   "notices. The dish changed, with no event. A note says every step here is normal commercial "
   "behaviour and none of it is anybody's failure."),
  ("h3", "Why the product code stays"),
  ("p", "Changing a product code has commercial costs: catalogues, customer ordering systems, "
        "shelf labels. A manufacturer improving a formulation, changing a supplier of their own, "
        "or reducing a cost will frequently keep the code and issue an updated specification."),
  ("p", "That is entirely legitimate and it means the code cannot be used as a proxy for the "
        "product being unchanged. The specification document is the thing that changes, and it "
        "has to be compared rather than filed."),
  ("h2", "Comparing"),
  ("fig", ("chain", {
    "entry": {"title": "A specification arrives", "sub": ["for a known ingredient"], "icon": "doc"},
    "steps": [
      {"title": "Any stored version?", "sub": ["for this ingredient"], "icon": "branch",
       "exit": {"title": "First one", "sub": ["store it, no comparison"], "icon": "database",
                "label": "no"}},
      {"title": "Compare all 14", "sub": ["state by state"], "icon": "filter"},
      {"title": "Anything added?", "sub": ["contains or may contain"], "icon": "branch",
       "exit": {"title": "Anything removed?", "sub": ["also worth flagging"], "icon": "branch",
                "label": "no"}},
      {"title": "Which dishes?", "sub": ["through the recursion"], "icon": "route"},
      {"title": "Flag them by name", "sub": ["open until cleared"], "icon": "alarm"}],
    "note": "Removals are flagged too: a dish that was excluded may now be available."}),
   "How a new specification is processed. Comparison against a stored version is the whole "
   "mechanism, which is why specifications are versioned rather than replaced.",
   "How an arriving specification is compared with the stored version",
   "A vertical chain of five steps entered by a box labelled A specification arrives for a known "
   "ingredient. Step one asks whether any stored version exists for this ingredient; if not it "
   "exits to First one, stored with no comparison. Step two compares all fourteen allergens state "
   "by state. Step three asks whether anything was added under contains or may contain; if not it "
   "exits to a further check for anything removed, which is also worth flagging. Step four "
   "identifies which dishes are affected through the recursion. Step five flags them by name, "
   "open until cleared. A note says removals are flagged too, because a dish that was excluded "
   "may now be available."),
  ("h3", "Removals matter too"),
  ("p", "A reformulation that removes an allergen is good news and it is also a change that "
        "should be reviewed rather than applied silently. It may mean a dish can be offered to "
        "people it previously could not, which is worth acting on deliberately."),
  ("p", "It also occasionally means the specification is less complete rather than the product "
        "being different, which is exactly the sort of thing a person should look at."),
  ("h2", "Specifications expire"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "0-12 months", "parts": [("ok", 61)]},
      {"label": "12-24 months", "parts": [("ok", 24), ("stale", 0)]},
      {"label": "Over 24 months", "parts": [("stale", 19)]},
      {"label": "None held", "parts": [("stale", 14)]}],
    "series": [("ok", "Ingredients with a current spec", "#7AA116"),
               ("stale", "Treated as unknown", "#ED7100")],
    "unit": "",
    "note": "Thirty-three ingredients are unknown. That number is the system's main work list."}),
   "The age profile of a menu's ingredient specifications. Anything beyond the expiry becomes "
   "unknown, which converts a silent risk into a task.",
   "The age profile of ingredient specifications across a menu",
   "A stacked bar chart with four bars. Two series: ingredients with a current specification in "
   "green, and those treated as unknown in orange. Zero to twelve months: sixty-one current. "
   "Twelve to twenty-four months: twenty-four current. Over twenty-four months: nineteen treated "
   "as unknown. None held: fourteen treated as unknown. A note says thirty-three ingredients are "
   "unknown and that number is the system's main work list."),
  ("p", "Expiry is a deliberate discomfort. A specification from three years ago may well still "
        "be accurate, and there is no way to know, so treating it as unknown is the honest "
        "position and it produces a steady, manageable stream of requests to suppliers."),
  ("p", "The expiry period is a judgement, set once, visible in configuration. Two years is "
        "defensible for a stable ingredient; a shorter period is appropriate for anything "
        "manufactured to a formulation that changes."),
  ("h3", "Supplier switches"),
  ("p", "More common than reformulations and structurally identical: the same ingredient, a "
        "different manufacturer, a different specification. Where the purchasing system records "
        "which supplier delivered, the check happens automatically; where it does not, a delivery "
        "from a new supplier is a manual event that has to be entered."),
  ("p", "This is also the point where the yield finding from Day 123 and this one meet: a "
        "supplier switch changes cost and allergens at the same time, and only one of those is "
        "usually noticed."),
  ("p", "Next: what the system will not tell you."),
 ],
},
{
 "slug": "why-the-system-never-says-safe",
 "title": "Why the system never says safe",
 "nav": "Why never 'safe'",
 "read": 5, "words": 720,
 "desc": ("Cross-contamination, severity, and the conversation the system exists to support "
          "rather than replace."),
 "og": ("Declared ingredients are one part of the question. The shared fryer, the same board and "
        "the severity of one person's allergy are the rest of it."),
 "abstract": ("What a data system genuinely cannot know, why a green tick is the wrong output, "
              "how the information supports a conversation, and what the interface should show."),
 "lede": ("This is the design decision that everything else in the system exists to support, and "
          "it is the one that will be argued with, because a green tick is exactly what everybody "
          "wants."),
 "tags": ["allergens", "food safety", "interfaces", "risk", "hospitality", "serverless"],
 "takeaways": [
  "Cross-contamination is a kitchen fact and is not in any database.",
  "Severity varies by person and changes what counts as acceptable.",
  "Output declared and unknown, and let a person handle the rest.",
  "A green tick would be trusted more than it deserves, which is the harm.",
  "The interface should make the conversation easier, not shorter.",
 ],
 "blocks": [
  ("h2", "What is not in the data"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Declared ingredients", "sub": ["this system knows"], "icon": "shield",
       "label": "in the data"},
      {"title": "Cross-contamination", "sub": ["shared fryer, boards,", "airborne flour"],
       "icon": "alarm", "label": "not in the data"},
      {"title": "This person's severity", "sub": ["trace, or a lot"], "icon": "person",
       "label": "not in the data"}],
    "target": {"title": "The actual question", "sub": ["can this person eat this?"],
               "icon": "question",
               "then": {"title": "A person answers it", "sub": ["with the data to hand"],
                        "icon": "check"}},
    "note": "Two of the three inputs are outside any system. Hence no verdict."}),
   "The three inputs to the real question and where each lives. A system holding one of the three "
   "should not be answering the question.",
   "Three inputs to an allergen question and which are available in data",
   "Three boxes stacked on the left. Declared ingredients, which this system knows, labelled in "
   "the data. Cross-contamination from a shared fryer, boards or airborne flour, labelled not in "
   "the data. And This person's severity, whether trace or a large amount, labelled not in the "
   "data. All three converge on The actual question: can this person eat this? And that leads "
   "down to A person answers it, with the data to hand. A note says two of the three inputs are "
   "outside any system, hence no verdict."),
  ("h3", "Cross-contamination"),
  ("p", "A dish whose ingredients contain no gluten, prepared on a board that had bread on it, "
        "in a kitchen where flour is in the air, cooked in a fryer shared with battered fish, is "
        "not a gluten-free dish. None of that is in a specification and none of it can be."),
  ("p", "Some kitchens have separate equipment and procedures for this and some do not, and that "
        "is a matter of physical arrangement and training. A system can record what a kitchen "
        "claims about its procedures, and a claim is not the same as a measurement."),
  ("h3", "Severity"),
  ("p", "For one person an allergen means discomfort; for another a trace is a medical emergency. "
        "The same dish with the same \"may contain\" statement is a reasonable choice for one and "
        "an unacceptable risk for the other, and neither the system nor the menu knows which "
        "person is asking."),
  ("h2", "Why a green tick is harmful"),
  ("callout", "The specific problem with a safety verdict", [
   "<strong>It will be trusted</strong> more than the underlying data justifies. That is what a "
   "tick does.",
   "<strong>It ends the conversation</strong> that should be happening between the customer and "
   "the kitchen.",
   "<strong>It cannot express severity</strong>, so it is either too cautious for most people or "
   "not cautious enough for some.",
   "<strong>It hides the unknowns.</strong> A dish with four unknown allergens can only honestly "
   "produce a question mark.",
   "<strong>It moves responsibility</strong> to a system that cannot hold it.",
   "<strong>The alternative costs nothing:</strong> show what is declared, show what is unknown, "
   "and let a person talk to a person.",
  ]),
  ("p", "The last line is the practical point. Refusing to produce a verdict does not make the "
        "system less useful; it makes it useful in a different way, by ensuring that whoever is "
        "having the conversation has current, complete, honestly-caveated information in front of "
        "them."),
  ("h2", "What the interface shows"),
  ("fig", ("chain", {
    "entry": {"title": "A customer asks", "sub": ["about a dish"], "icon": "person"},
    "steps": [
      {"title": "Contains", "sub": ["named, first"], "icon": "shield"},
      {"title": "May contain", "sub": ["named, distinctly"], "icon": "alarm"},
      {"title": "Unknown", "sub": ["named, prominently"], "icon": "question"},
      {"title": "Kitchen note", "sub": ["shared fryer, etc"], "icon": "doc"},
      {"title": "'Please check with", "sub": ["the kitchen'"], "icon": "email"}],
    "note": "Five things, no verdict. The last line is not a disclaimer; it is the instruction."}),
   "What a member of staff sees when a question is asked. Every element is a fact and none of "
   "them is a conclusion.",
   "What an allergen lookup shows when a customer asks about a dish",
   "A vertical chain of five steps entered by a box labelled A customer asks about a dish. Step "
   "one shows Contains, named first. Step two shows May contain, named distinctly. Step three "
   "shows Unknown, named prominently. Step four shows a Kitchen note covering things like a "
   "shared fryer. Step five says please check with the kitchen. A note says five things and no "
   "verdict, and the last line is not a disclaimer but the instruction."),
  ("h3", "The kitchen note"),
  ("p", "A short, honest, per-site statement about the kitchen's actual arrangements: whether "
        "there is a shared fryer, whether flour is used in the same space, whether separate "
        "equipment exists for particular allergens."),
  ("p", "It is written once by whoever runs the kitchen, reviewed when the kitchen changes, and "
        "it is the most useful single sentence in the whole interface because it addresses the "
        "part the specifications cannot."),
  ("h3", "Making the conversation easier"),
  ("p", "The measure of success here is not that fewer questions get asked. It is that when a "
        "question is asked, the person answering has accurate current information, knows which "
        "parts of it are incomplete, and is not guessing."),
  ("p", "A system that reduced the number of conversations would be doing harm. One that makes "
        "each conversation better informed is doing the whole of what software can honestly do "
        "here."),
  ("p", "Next: the substitution nobody recorded."),
 ],
},
{
 "slug": "how-a-substitution-gets-caught",
 "title": "How a substitution gets caught",
 "nav": "How substitutions are caught",
 "read": 5, "words": 720,
 "desc": ("The stand-in ingredient, the delivery that was short, and why a substitution has to be "
          "recorded before service rather than after."),
 "og": ("The supplier was out of one thing and sent another. The dish is the same on the menu and "
        "different on the plate."),
 "abstract": ("How substitutions arise, why they are the second largest risk, how they are "
              "recorded at receipt, and what the pre-service check looks like."),
 "lede": ("A substitution is a supplier or a kitchen deciding, reasonably and at short notice, "
          "that one thing will do instead of another. It is normal, it is frequent, and it "
          "changes the allergen profile of everything it touches."),
 "tags": ["allergens", "substitutions", "kitchen", "goods receipt", "food safety", "serverless"],
 "takeaways": [
  "Substitutions come from the supplier and from the kitchen; both change the dish.",
  "The receiving step is where a supplier substitution can be caught.",
  "A kitchen substitution needs a way to record it in seconds, or it will not be recorded.",
  "The pre-service check is a short list of what is different today.",
  "A substitution that adds an allergen should stop the dish being sold until reviewed.",
 ],
 "blocks": [
  ("h2", "Two sources"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Supplier substitution", "sub": ["out of stock,", "sent an alternative"],
       "icon": "truck", "label": "caught at receipt"},
      {"title": "Kitchen substitution", "sub": ["we ran out,", "used something else"],
       "icon": "person", "label": "caught only if recorded"},
      {"title": "Recipe deviation", "sub": ["a different method", "on the day"], "icon": "form",
       "label": "hardest of all"}],
    "target": {"title": "The dish changed", "sub": ["and the menu did not"], "icon": "alarm",
               "then": {"title": "Pre-service check", "sub": ["what is different today?"],
                        "icon": "check"}},
    "note": "The second lane is the common one and it depends entirely on ease of recording."}),
   "Three ways a dish differs from its recipe on a given day. Only the first has a natural "
   "capture point; the other two depend on how easy recording is.",
   "Three sources of substitution that change a dish's allergens",
   "Three boxes stacked on the left. Supplier substitution, where they were out of stock and sent "
   "an alternative, labelled caught at receipt. Kitchen substitution, where we ran out and used "
   "something else, labelled caught only if recorded. And Recipe deviation, a different method on "
   "the day, labelled hardest of all. All three converge on The dish changed and the menu did "
   "not, and that leads down to a Pre-service check asking what is different today. A note says "
   "the second lane is the common one and it depends entirely on ease of recording."),
  ("h3", "At receipt"),
  ("p", "This connects directly to the packing slip checker from Day 114. A substituted product "
        "code is already flagged there for quantity and suitability reasons; the allergen check "
        "is the same event with an additional consequence."),
  ("p", "The receiving person does not need to know anything about allergens. They record that a "
        "substitution happened, which the system already asks them to do, and the allergen "
        "comparison runs automatically against the substitute's specification if one is held, or "
        "flags it as unknown if not."),
  ("h2", "Recording a kitchen substitution"),
  ("fig", ("chain", {
    "entry": {"title": "We have run out", "sub": ["mid-service, often"], "icon": "storage"},
    "steps": [
      {"title": "Substitute chosen", "sub": ["by whoever is cooking"], "icon": "person"},
      {"title": "Two taps to record", "sub": ["dish, and what instead"], "icon": "form",
       "side": {"title": "If it takes longer", "sub": ["it will not happen"], "icon": "clock"}},
      {"title": "Allergen delta", "sub": ["computed immediately"], "icon": "filter"},
      {"title": "Anything added?", "sub": ["contains or may contain"], "icon": "branch",
       "exit": {"title": "Note it and carry on", "sub": ["no allergen change"], "icon": "check",
                "label": "no"}},
      {"title": "Stop selling it", "sub": ["until somebody reviews"], "icon": "stop"}],
    "note": "The last box is severe on purpose, and it is why the recording has to take seconds."}),
   "How a kitchen substitution is captured and assessed. The two-tap requirement is a design "
   "constraint rather than a preference: anything slower is not used during service.",
   "How a kitchen substitution is recorded and checked for allergen changes",
   "A vertical chain of five steps entered by a box labelled We have run out, often mid-service. "
   "Step one records the substitute chosen by whoever is cooking. Step two takes two taps to "
   "record: the dish, and what was used instead, with a side box noting that if it takes longer "
   "it will not happen. Step three computes the allergen delta immediately. Step four asks "
   "whether anything was added under contains or may contain; if not it exits to Note it and "
   "carry on, with no allergen change. Step five stops the dish being sold until somebody "
   "reviews. A note says the last box is severe on purpose, and it is why the recording has to "
   "take seconds."),
  ("h3", "Two taps, or it does not happen"),
  ("p", "This is the same constraint as the receiving doorway in Day 114 and it is more acute. A "
        "substitution decision is made in the middle of a service by somebody with both hands "
        "occupied, and any recording mechanism that takes more than a few seconds will be skipped "
        "entirely."),
  ("p", "Which means the design has to be a short list of the dishes on today's menu, a short "
        "list of plausible substitutes for the ingredient that ran out, and nothing else. No free "
        "text, no reason field, no confirmation dialogue."),
  ("h2", "Stopping a dish"),
  ("p", "Stopping the sale of a dish because a substitution added an allergen is a strong action "
        "and it is the correct one, because the alternative is selling a dish whose printed "
        "allergen information is now wrong."),
  ("p", "The review is quick: somebody looks at what changed, decides whether the dish can be "
        "sold with amended information communicated to staff, and clears it. That takes a couple "
        "of minutes and it is the difference between a controlled change and an undocumented "
        "one."),
  ("h2", "The pre-service check"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Before service", "sub": ["two minutes"], "icon": "clock"},
      {"title": "What is different", "sub": ["today, versus the menu"], "icon": "search"},
      {"title": "Usually nothing", "sub": ["and that is stated"], "icon": "check"},
      {"title": "Sometimes 2 dishes", "sub": ["named, with the change"], "icon": "alarm"},
      {"title": "Briefed", "sub": ["everybody on the floor"], "icon": "person"}],
    "title": "THE TWO MINUTES THAT MATTER",
    "note": "Explicitly saying 'nothing has changed today' is what makes the exceptions land."}),
   "The daily briefing output. Stating that nothing has changed on most days is what gives the "
   "occasional exception its weight.",
   "The pre-service allergen briefing produced each day",
   "A horizontal row of five boxes. Before service: two minutes. What is different today versus "
   "the menu. Usually nothing, and that is stated. Sometimes two dishes, named with the change. "
   "Briefed: everybody on the floor. A note says explicitly saying nothing has changed today is "
   "what makes the exceptions land."),
  ("p", "The value of a briefing that usually says nothing is easy to underestimate. A daily "
        "statement establishes that the check happened, which means the day it says something the "
        "statement carries weight, and staff have a habit of hearing it."),
  ("h3", "What this connects to"),
  ("p", "Every substitution recorded here is also a cost event for Day 123, a receipt event for "
        "Day 114, and occasionally a supplier finding for Day 113. Recording it once and letting "
        "several systems read it is the case for keeping these things as events rather than as "
        "notes in separate places."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="ingredient",
 volumes=[(120, "120 ingredients"), (400, "400 ingredients"), (1500, "1,500 ingredients")],
 read_each=0.5,
 msgs_each=0.05,
 lede=("The only model call is reading a specification document, and those arrive a few times a "
       "week rather than daily. Four hundred ingredients is a substantial menu across a few "
       "sites. Here is where each cent goes."),
 takeaway_extra=("Specification reading is the only variable, and it falls as suppliers move to "
                 "structured data."),
 risks=[
  "<strong>Re-reading a specification on every roll-up.</strong> The declaration is extracted "
  "once per document version and cached against its hash.",
  "<strong>Recursing the full recipe tree on every lookup.</strong> Roll-ups are computed when "
  "something changes and stored, not derived at the moment a customer asks.",
  "<strong>Storing only the latest specification.</strong> Not a cost problem: it makes change "
  "detection impossible, which is the main thing this system does.",
 ],
 per_unit_note=("The read band is specification documents rather than ingredients; it is "
                "expressed per ingredient for comparability. Messaging is the daily briefing and "
                "change flags."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="al",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the three-state model, and how roll-ups are stored."),
 outside=[
  {"title": "Specifications", "sub": ["file or scan"], "icon": "doc"},
  {"title": "Recipes", "sub": ["and substitutions"], "icon": "form"},
  {"title": "The floor", "sub": ["lookups and briefings"], "icon": "person"}],
 inside=[
  {"title": "S3 + API", "sub": ["specs,", "substitution capture"], "icon": "storage"},
  {"title": "Lambda x3", "sub": ["ingest, rollup, watch"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["ingredients, dishes"], "icon": "database"}],
 note="us-east-1. One account. Specifications versioned; unknown is a stored state, never a null.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Specifications arriving as a file or a "
  "scan. Recipes and substitutions. And The floor, performing lookups and receiving briefings. "
  "Inside the account, three groups. S3 holding specifications alongside an API for substitution "
  "capture. Three Lambda functions named ingest, rollup and watch. And two DynamoDB tables named "
  "ingredients and dishes. A note gives the region as us-east-1, one account, and states that "
  "specifications are versioned and unknown is a stored state rather than a null."),
 functions=[
  ["<code>al-ingest</code>", "S3 put on the specs prefix",
   "Extracts declarations for all 14 allergens; compares against the stored version; versions it",
   "180s / 1024&nbsp;MB"],
  ["<code>al-rollup</code>", "DynamoDB stream on ingredients",
   "Recurses the recipe tree; recomputes every affected dish's three-state declaration",
   "120s / 1024&nbsp;MB"],
  ["<code>al-watch</code>", "API and EventBridge daily",
   "Records substitutions, computes the delta, stops affected dishes, emits the pre-service "
   "briefing", "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>al-ingest-role</code>",
   "<code>s3:GetObject</code>, <code>bedrock:InvokeModel</code>, <code>dynamodb:PutItem</code>",
   "The specs prefix; one model id; ingredients"],
  ["<code>al-rollup-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>", "Both tables"],
  ["<code>al-watch-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Both tables; one verified identity"]],
 tables=[
  ("Table: ingredients",
   "PK   ingredient_id     S   stock_base_brown\n"
   "SK   spec_version      S   2026-06-14#sha256-prefix\n"
   "     supplier          S\n"
   "     product_code      S   unchanged across reformulations\n"
   "     declarations      M   {gluten: contains, mustard: may_contain,\n"
   "                            celery: unknown, ...} -- all 14, always\n"
   "     spec_dated        S   the date on the document, not on receipt\n"
   "     spec_key          S   s3 key of the original\n"
   "     superseded_at     S   set when a newer version arrives\n"
   "     is_compound       BOOL and if so, its own recipe id\n\n"
   "Every version is kept. Comparison against the previous version is the\n"
   "entire supplier-change mechanism, and it needs both to exist."),
  ("Table: dishes",
   "PK   dish_id           S\n"
   "     recipe_version    S\n"
   "     rolled_up         M   {gluten: contains, celery: unknown, ...}\n"
   "     unknown_count     N   surfaced at the top of every lookup\n"
   "     unknown_because   L   [{allergen, ingredient, reason}]\n"
   "     rolled_up_at      S\n"
   "     kitchen_note      S   shared fryer, flour in the air -- per site\n"
   "     stopped           BOOL set by a substitution that added an allergen\n"
   "     stopped_reason    S\n"
   "     substitutions     L   [{date, replaced, with, delta, by}]\n\n"
   "`unknown_because` names the ingredient and the reason, so the unknown\n"
   "list is a work list rather than a warning.")],
 inbound=[
  "<strong>Specifications arrive by email or upload</strong> into S3 and are versioned by content "
  "hash. A re-sent identical document does not create a version.",
  "<strong>Every allergen is stored explicitly for every ingredient.</strong> There is no null "
  "and no absent key; a missing declaration is the string <code>unknown</code>.",
  "<strong>Substitution capture is two taps</strong> from a short list. Anything slower is not "
  "used during service, which means it does not exist.",
  "<strong>Roll-ups are computed on change and stored</strong>, so a lookup during service is a "
  "single read and never a recursion."],
 model_notes=[
  "<strong>One read per specification document.</strong> Extracting the declared state of all "
  "fourteen allergens.",
  "<strong>It must return unknown, not infer.</strong> The prompt is explicit that an allergen "
  "the document does not address is unknown, and inference is a failure.",
  "<strong>It never rolls up.</strong> Combining ingredient declarations into a dish is "
  "deterministic code, because the same inputs must always give the same answer.",
  "<strong>It never produces a verdict.</strong> Part 4 is entirely about why there is no safety "
  "output anywhere in this system.",
  "<strong>Structured specifications skip the model</strong>, which over time is the majority."],
 gotchas=[
  "Store unknown as a value, never as a missing key. A null renders as a blank and a blank reads "
  "as a confirmed negative.",
  "Keep every specification version. Change detection compares against the previous one, and "
  "overwriting removes the only mechanism that catches a reformulation.",
  "Expire old specifications into unknown. A three-year-old document may be accurate and there is "
  "no way to know.",
  "Compute roll-ups on change and store them. A recursion at lookup time is slow at exactly the "
  "moment somebody is waiting at a table.",
  "Do not add a safe indicator, a green tick, or a suitability score, however often it is "
  "requested. Cross-contamination and severity are not in this data."],
))
