"""Day 103 -- 2026-08-05 -- Duplicate contact merger."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "duplicate-contact-merger"
NAME = "Duplicate contact merger"

SPEC = {
 "slug": SLUG, "date": "2026-08-05", "name": NAME,
 "tagline": ("Finds the four records that are all the same customer, shows a person exactly what "
             "would change, and merges only what they confirm -- with every merge reversible for "
             "as long as it matters."),
 "lede": ("A small system that finds probable duplicate contacts, scores each pair against "
          "evidence rather than a similarity score, proposes a merge showing precisely which "
          "field wins, and keeps enough to undo it. It merges nothing automatically above the "
          "certain band. Seven posts on the same system -- one diagram at a time -- with a cost "
          "breakdown and an engineering reference at the end."),
 "keywords": ["duplicates", "CRM", "data quality", "record linkage", "merging", "serverless"],
 "icons": ["team", "search", "retry"],
 "faq": [
  ("What is a duplicate contact merger?",
   "A small serverless system that finds records likely to be the same person or company, scores "
   "each candidate pair, proposes a merge showing what would change, and executes only what a "
   "person confirms -- keeping enough history to reverse it."),
  ("Does it merge automatically?",
   "Only in a narrow certain band: an exact match on a strong identifier with no conflicting "
   "data. Everything else is proposed to a person, because a wrong merge is much harder to "
   "explain to a customer than a duplicate."),
  ("Why is a wrong merge worse than a duplicate?",
   "A duplicate means somebody gets two emails. A wrong merge means one customer's order history "
   "is attached to another customer's record, which is a data protection problem as well as an "
   "embarrassing one."),
  ("Can a merge be undone?",
   "Yes, for a retention window you set. The system stores both original records in full, so "
   "reversing is restoring rather than reconstructing. After the window it becomes irreversible "
   "and the report says which merges have passed it."),
  ("What does it cost to run?",
   "A few dollars a month for a database of tens of thousands of contacts. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "duplicate-contact-merger-on-aws",
 "title": "A duplicate contact merger on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Finds probable duplicates, shows exactly what a merge would change, and executes only "
          "what a person confirms. Reversible. AWS, about $3 a month."),
 "og": ("A duplicate means somebody gets two emails. A wrong merge attaches one customer's "
        "history to another. Every threshold here follows from that."),
 "abstract": ("The whole system on one page -- a blocker, a scorer and a proposer -- with the "
              "asymmetry that makes automatic merging almost always the wrong choice."),
 "lede": ("Every contact database has duplicates and everybody knows it. What stops anybody "
          "fixing them is not finding them &mdash; a similarity search finds too many &mdash; it "
          "is that merging is destructive, the tools present it as a bulk operation, and one "
          "wrong merge is much worse than a hundred duplicates. This post walks through a small "
          "system built entirely around that asymmetry."),
 "tags": ["duplicates", "CRM", "data quality", "record linkage", "merging", "serverless"],
 "takeaways": [
  "Comparing every record with every other is impossible; blocking makes it tractable.",
  "Pairs are scored on evidence, not on a single similarity number.",
  "Only an exact strong-identifier match with no conflicts merges automatically.",
  "Every proposal shows field by field what would change and what would be lost.",
  "Designed on AWS for about $3 a month at tens of thousands of contacts.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Contact records", "sub": ["your CRM or database"], "icon": "team"},
      {"title": "Field rules", "sub": ["which field wins"], "icon": "doc"},
      {"title": "Whoever owns the data", "sub": ["confirms each merge"], "icon": "person"}],
    "inside": [
      {"title": "Blocker", "sub": ["candidate pairs,", "not every pair"], "icon": "filter"},
      {"title": "Scorer", "sub": ["evidence for,", "evidence against"], "icon": "counter"},
      {"title": "Proposer", "sub": ["what changes,", "what is lost"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "records"},
              {"from": 1, "to": 1, "label": "which value wins"},
              {"from": 2, "to": 2, "label": "a merge to confirm", "up": True}],
    "note": "Both originals are kept in full, so every merge can be reversed."}),
   "Three things outside the account, three pieces inside it. The scorer weighing evidence "
   "against as well as for is what separates this from a similarity search.",
   "System: contact records blocked, scored and proposed for merging",
   "Three boxes across the top sit outside the AWS account. On the left, Contact records: your "
   "CRM or database. In the middle, Field rules: which field wins in a merge. On the right, "
   "Whoever owns the data: the person who confirms each merge. Each connects by an arrow to the "
   "AWS account container below. Records flow down into the account. The field rules feed in "
   "which value wins. A merge to confirm goes back out. Inside the AWS account are three "
   "components in a row. On the left, the Blocker, which produces candidate pairs rather than "
   "every pair. In the middle, the Scorer, weighing evidence for and evidence against. On the "
   "right, the Proposer, showing what changes and what is lost. A note at the bottom says both "
   "originals are kept in full, so every merge can be reversed."),
  ("h3", "The asymmetry"),
  ("p", "A duplicate contact costs somebody two emails and a slightly wrong count. A wrong merge "
        "takes two customers' records &mdash; their orders, their notes, their communication "
        "history, possibly their addresses &mdash; and combines them irreversibly into one. The "
        "customer who rings to ask why they can see somebody else's order is not having a data "
        "quality conversation."),
  ("p", "So the thresholds are set from that: automatic merging is reserved for cases where the "
        "evidence is effectively conclusive, and everything else is a proposal that takes a "
        "person about four seconds to confirm."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The blocker.</strong> Ten thousand contacts is fifty million pairs, which cannot be "
   "compared. Blocking reduces that to a few thousand plausible pairs using cheap keys. Part 2 is "
   "about doing that without missing real duplicates.",
   "<strong>The scorer.</strong> Weighs specific evidence rather than computing a single "
   "similarity. Two records sharing a phone number is strong; two records sharing a surname is "
   "nearly nothing. Part 3 covers what counts and what argues against.",
   "<strong>The proposer.</strong> Builds the merged record according to the field rules and "
   "shows it side by side with both originals, with anything that would be lost highlighted. "
   "Part 4.",
  ]),
  ("h2", "One pair, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Blocked", "sub": ["a plausible pair"], "icon": "filter"},
      {"title": "Scored", "sub": ["evidence both ways"], "icon": "counter"},
      {"title": "Proposed", "sub": ["field by field"], "icon": "doc"},
      {"title": "Confirmed", "sub": ["by a person"], "icon": "person"},
      {"title": "Merged", "sub": ["and reversible"], "icon": "retry"}],
    "title": "ONE DUPLICATE PAIR, END TO END",
    "note": "The fifth box is not the end. A merge stays undoable for as long as you set."}),
   "The same system as one line. The reversibility in the last stage is what makes confirming a "
   "merge a low-stakes decision rather than a permanent one.",
   "One duplicate pair from detection to reversible merge, in five stages",
   "A horizontal row of five boxes joined by arrows. Blocked: identified as a plausible pair. "
   "Scored: with evidence both ways. Proposed: field by field. Confirmed: by a person. Merged: "
   "and reversible. A note says the fifth box is not the end, because a merge stays undoable for "
   "as long as you set."),
  ("h2", "In plain words"),
  ("p", "A business has about fourteen thousand contacts accumulated from a website form, an "
        "e-commerce platform, an old spreadsheet import and years of manual entry. Blocking "
        "produces about nineteen hundred candidate pairs."),
  ("p", "Of those, four hundred and ten share an exact email address with no conflicting data, "
        "which is conclusive: those merge automatically. About six hundred score high enough to "
        "propose &mdash; same phone number and same surname, or same address and same first name "
        "&mdash; and each is a four-second confirmation. The remaining nine hundred score too low "
        "to be worth anybody's time and are recorded rather than shown."),
  ("p", "The interesting ones are in the proposals. Two records with the same phone number, same "
        "surname, different first names and different email addresses are a household rather than "
        "a duplicate, and a person spots that instantly from the side-by-side view. A similarity "
        "score would have put them at 0.88 and a bulk merge tool would have combined a married "
        "couple into one customer."),
  ("callout", "Design rules that shaped every decision", [
   "A wrong merge is much worse than a duplicate. Every threshold follows from that.",
   "Score evidence, not similarity. Two records sharing a rare phone number is not the same as "
   "sharing a common surname.",
   "Weigh evidence against as well as for. Different first names on a shared address is a "
   "household.",
   "Automatic merging only on a conclusive identifier with no conflicts.",
   "Show what would be lost, not just what would be kept. That is where the mistakes are visible.",
   "Keep both originals in full, so undo is a restore rather than a reconstruction.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Deduplication tools mostly present a slider: raise it to merge fewer things, lower it to "
        "merge more. That framing hides the actual decision, which is not how similar two records "
        "are but what evidence exists that they are the same entity &mdash; and those are "
        "genuinely different questions."),
  ("p", "So this design shows the evidence rather than the score, keeps the automatic band narrow "
        "enough to be uncontroversial, and makes confirming a proposal cheap enough that a person "
        "in the loop is not a bottleneck. Six hundred four-second confirmations is forty minutes, "
        "which is an afternoon's work once and a handful a week thereafter."),
  ("p", "The next four posts walk through each piece: how candidate pairs are found, how a pair is "
        "scored, what a merge proposal shows, and how a merge is reversed. One diagram per post, "
        "a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-candidate-pairs-get-found",
 "title": "How candidate pairs get found",
 "nav": "How pairs are found",
 "read": 5, "words": 750,
 "desc": ("Why comparing everything is impossible, the four blocking keys worth using, and the "
          "duplicates that blocking will miss."),
 "og": ("Ten thousand contacts is fifty million pairs. Blocking makes it a few thousand, and the "
        "art is in not throwing away the real duplicates."),
 "abstract": ("Why every-pair comparison is impossible at any real scale, the four blocking keys "
              "worth using, why multiple keys beat one good one, and the duplicates blocking "
              "will still miss."),
 "lede": ("The first problem in deduplication is arithmetic. Fourteen thousand contacts produce "
          "just under a hundred million pairs, and no amount of cheap comparison makes that "
          "tractable on a schedule. Blocking is how everybody solves it, and the whole skill is "
          "in not discarding the pairs that mattered."),
 "tags": ["duplicates", "blocking", "record linkage", "scaling", "data quality", "serverless"],
 "takeaways": [
  "Fourteen thousand contacts is a hundred million pairs. Blocking is not optional.",
  "Four keys: normalised email, normalised phone, postcode plus surname, and a name fingerprint.",
  "Use several keys and take the union. One key always misses a category.",
  "A key that produces huge blocks is worse than useless; cap block size and report it.",
  "Blocking misses genuine duplicates, and the report says which categories it cannot see.",
 ],
 "blocks": [
  ("h2", "Four keys"),
  ("table", ["Key", "Catches", "Misses"], [
   ["Normalised email", "The same address written differently", "Anyone with two addresses"],
   ["Normalised phone", "The same number with different formatting", "Anyone with two numbers"],
   ["Postcode + surname", "Household and repeat customers", "House moves"],
   ["Name fingerprint", "Typos and transpositions", "Name changes"],
  ]),
  ("p", "Each key catches a category and misses a different one, which is why the answer is to "
        "run all four and take the union of the pairs they produce. Any single key, however "
        "clever, has a category it structurally cannot see."),
  ("h2", "How blocking runs"),
  ("fig", ("chain", {
    "entry": {"title": "All contacts", "sub": ["14,000"], "icon": "team"},
    "steps": [
      {"title": "Compute four keys", "sub": ["per record"], "icon": "key"},
      {"title": "Group by each key", "sub": ["records sharing a key"], "icon": "filter",
       "side": {"title": "Blocks", "sub": ["usually 2-4 records"], "icon": "database"}},
      {"title": "Block too large?", "sub": ["over 30 records"], "icon": "branch",
       "exit": {"title": "Drop it, and report", "sub": ["a useless key value"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Pairs within blocks", "sub": ["union across keys"], "icon": "counter"},
      {"title": "~1,900 candidate pairs", "sub": ["from 98 million"], "icon": "check"}],
    "note": "A block of 400 records sharing a key is a bad key value, not 80,000 real candidates."}),
   "How blocking reduces the problem. The oversized-block check is what stops one degenerate key "
   "value reintroducing the quadratic explosion.",
   "How candidate duplicate pairs are found by blocking",
   "A vertical chain of five steps entered by a box labelled All contacts, fourteen thousand of "
   "them. Step one computes four keys per record. Step two groups by each key, forming blocks "
   "that usually contain two to four records. Step three asks whether a block is too large, over "
   "thirty records; if so it exits to Drop it and report, because it is a useless key value. Step "
   "four forms pairs within blocks and takes the union across keys. Step five yields about "
   "nineteen hundred candidate pairs from ninety-eight million possible ones. A note says a block "
   "of four hundred records sharing a key is a bad key value rather than eighty thousand real "
   "candidates."),
  ("h3", "Oversized blocks"),
  ("p", "Every blocking scheme produces degenerate values. A normalised phone key will find four "
        "hundred records sharing the business's own phone number, because somebody entered it as "
        "a placeholder. A postcode key will find every record at a large office building."),
  ("p", "A block of four hundred records generates eighty thousand pairs on its own, which "
        "reintroduces exactly the problem blocking solved. So blocks above a size cap are dropped "
        "and reported, and the report is genuinely useful: a key value shared by four hundred "
        "records is almost always a data quality problem worth fixing at source."),
  ("h3", "Normalisation matters more than the key"),
  ("p", "A phone key that does not strip formatting finds nothing: <code>07700 900123</code> and "
        "<code>+447700900123</code> are the same number and different strings. The same is true of "
        "email with dots and plus-addressing, and of postcodes with and without a space."),
  ("p", "Getting normalisation right is most of what makes blocking work, and it is worth being "
        "conservative: normalising too aggressively creates false blocks, but under-normalising "
        "silently misses whole categories with no symptom at all."),
  ("h2", "What blocking misses"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Two addresses", "sub": ["no shared email"], "icon": "email"},
      {"title": "Two numbers", "sub": ["no shared phone"], "icon": "phone"},
      {"title": "Moved house", "sub": ["no shared postcode"], "icon": "map"},
      {"title": "Changed name", "sub": ["no shared fingerprint"], "icon": "person"},
      {"title": "Invisible", "sub": ["and the report says so"], "icon": "alarm"}],
    "title": "THE DUPLICATE BLOCKING CANNOT SEE",
    "note": "Four keys and all four differ. Naming the limitation is better than implying coverage."}),
   "The category blocking structurally cannot find. Stating it is what stops a deduplication "
   "report being read as a claim that the database is now clean.",
   "The duplicate that blocking cannot find",
   "A horizontal row of five boxes. Two addresses: no shared email. Two numbers: no shared phone. "
   "Moved house: no shared postcode. Changed name: no shared fingerprint. Invisible: and the "
   "report says so. A note says four keys and all four differ, and naming the limitation is "
   "better than implying coverage."),
  ("p", "A person who changed their name, moved house, and uses a different email and phone from "
        "the one on their old record is genuinely undetectable by any blocking scheme, and "
        "pretending otherwise is how a deduplication project gets declared complete."),
  ("p", "The honest handling is a line in the report: \"this finds duplicates sharing at least one "
        "of email, phone, postcode with surname, or a name fingerprint. Records sharing none of "
        "those are not detectable and are not counted anywhere in this report.\" That is one "
        "sentence and it keeps everybody's expectations calibrated."),
  ("p", "Next: scoring a pair."),
 ],
},
{
 "slug": "how-a-pair-gets-scored",
 "title": "How a pair gets scored",
 "nav": "How pairs are scored",
 "read": 5, "words": 750,
 "desc": ("Evidence for and evidence against, why rarity matters more than agreement, and the "
          "three signals that argue a pair is not a duplicate."),
 "og": ("Two records sharing a rare surname is evidence. Two sharing a common one is nearly "
        "nothing. And different first names on a shared address is evidence against."),
 "abstract": ("Why evidence beats similarity, how rarity weights agreement, the three signals "
              "that argue actively against a merge, and the narrow band that merges "
              "automatically."),
 "lede": ("A similarity score answers the wrong question. Two records can be ninety per cent "
          "similar and obviously different people, and eighty per cent similar and certainly the "
          "same person. What matters is what agrees, how unlikely that agreement is by chance, "
          "and what disagrees."),
 "tags": ["duplicates", "record linkage", "scoring", "probability", "data quality", "serverless"],
 "takeaways": [
  "Agreement on a rare value is strong evidence; on a common one it is nearly none.",
  "Three signals argue against: different first names, conflicting strong identifiers, and explicit separation.",
  "The score is a sum of evidence, and the report shows the terms rather than the total.",
  "Automatic merging needs a conclusive identifier and zero evidence against.",
  "A pair marked not-a-duplicate is remembered forever and never proposed again.",
 ],
 "blocks": [
  ("h2", "Rarity, not agreement"),
  ("p", "Two records with the surname Smith agreeing tells you almost nothing; two with an unusual "
        "surname agreeing is meaningful. The same applies to first names, postcodes, and company "
        "names. Weighting agreement by how rare the value is in your own database is the single "
        "change that most improves scoring, and it costs one count query per value."),
  ("table", ["Agreement", "Weight if rare", "Weight if common"], [
   ["Email, exact", "Conclusive", "Conclusive &mdash; email is always rare"],
   ["Phone, normalised", "Strong", "Weak if it is the company's own number"],
   ["Surname", "Moderate", "Nearly none"],
   ["Postcode", "Moderate", "Weak in a dense postcode"],
   ["Company name", "Strong", "Weak for a common trading name"],
  ]),
  ("p", "The second column is the interesting one. A phone number is normally a strong signal and "
        "becomes worthless when four hundred records share it, and the same computation that "
        "flagged that as an oversized block also tells the scorer to discount it."),
  ("h2", "Evidence against"),
  ("fig", ("chain", {
    "entry": {"title": "A candidate pair", "sub": ["from blocking"], "icon": "filter"},
    "steps": [
      {"title": "Sum the evidence for", "sub": ["weighted by rarity"], "icon": "counter"},
      {"title": "Different first names?", "sub": ["on a shared address"], "icon": "branch",
       "exit": {"title": "Strong evidence against", "sub": ["a household"], "icon": "team",
                "label": "yes"}},
      {"title": "Conflicting identifiers?", "sub": ["two different tax refs"], "icon": "branch",
       "exit": {"title": "Conclusive against", "sub": ["never propose"], "icon": "stop",
                "label": "yes"}},
      {"title": "Marked separate before?", "sub": ["by a person"], "icon": "branch",
       "side": {"title": "Not-a-duplicate list", "sub": ["permanent"], "icon": "database"},
       "exit": {"title": "Never propose again", "sub": ["remember the answer"], "icon": "check",
                "label": "yes"}},
      {"title": "A score, with its terms", "sub": ["for and against"], "icon": "report"}],
    "note": "Evidence against is not a lower score. Conflicting identifiers block a merge outright."}),
   "How a pair is scored. The against-branches are not negative weights but hard blocks, because "
   "some evidence is conclusive in the other direction.",
   "How a candidate duplicate pair is scored for and against",
   "A vertical chain of five steps entered by a box labelled A candidate pair, from blocking. "
   "Step one sums the evidence for, weighted by rarity. Step two asks whether the first names "
   "differ on a shared address; if so it exits to Strong evidence against, indicating a "
   "household. Step three asks whether there are conflicting strong identifiers such as two "
   "different tax references; if so it exits to Conclusive against and never proposes the pair. "
   "Step four asks whether a person has previously marked them separate, checking a permanent "
   "not-a-duplicate list; if so it exits to Never propose again. Step five produces a score with "
   "its terms, for and against. A note says evidence against is not a lower score, because "
   "conflicting identifiers block a merge outright."),
  ("h3", "Households"),
  ("p", "The most common false positive in any consumer database. Two people at the same address "
        "with the same surname, the same landline, and often the same email domain are frequently "
        "a couple, and every similarity measure scores them very highly."),
  ("p", "Different first names is the signal that separates them, and it needs to be strong "
        "enough to override a high agreement score rather than being one term among many. A pair "
        "agreeing on address, surname and phone but disagreeing on first name is a household "
        "until proven otherwise, and proposing it as a merge wastes somebody's attention every "
        "single time."),
  ("h3", "Remembering a no"),
  ("p", "The most important small feature in the whole system. A pair a person has looked at and "
        "declared separate must never be proposed again, ever, and that record has to survive "
        "re-imports, re-runs and schema changes."),
  ("p", "Without it, the same six hundred rejected pairs reappear in every run and the review "
        "becomes something people stop doing within two rounds. The not-a-duplicate list is keyed "
        "on both record identifiers and is the one piece of state that is never expired."),
  ("h2", "The automatic band"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Exact email", "sub": ["conclusive"], "icon": "email"},
      {"title": "No conflicts", "sub": ["nothing argues against"], "icon": "check"},
      {"title": "No manual data", "sub": ["nothing to lose"], "icon": "doc"},
      {"title": "Merge automatically", "sub": ["and log it"], "icon": "retry"},
      {"title": "Everything else", "sub": ["a person, four seconds"], "icon": "person"}],
    "title": "THE NARROW AUTOMATIC BAND",
    "note": "All three conditions, not any of them. The band is small on purpose."}),
   "The only case that merges without a person. All three conditions must hold, which keeps the "
   "band narrow enough that automatic merging is uncontroversial.",
   "The three conditions required for an automatic merge",
   "A horizontal row of five boxes. Exact email: conclusive. No conflicts: nothing argues against. "
   "No manual data: nothing would be lost. Merge automatically: and log it. Everything else: a "
   "person, taking four seconds. A note says all three conditions must hold rather than any of "
   "them, and the band is small on purpose."),
  ("p", "The third condition is the one that gets left out and matters most. Two records with the "
        "same email address where one has free-text notes somebody typed are not a safe automatic "
        "merge, because the merge rules have to decide what happens to those notes and that "
        "decision benefits from a person seeing it."),
  ("p", "Next: what a proposal actually shows."),
 ],
},
{
 "slug": "how-a-merge-gets-proposed",
 "title": "How a merge gets proposed",
 "nav": "How it is proposed",
 "read": 5, "words": 740,
 "desc": ("Field-by-field, what wins and why, showing what would be lost, and the related records "
          "that make a merge more than a record edit."),
 "og": ("Showing the merged result is not enough. Showing what would be lost is where somebody "
        "spots the mistake."),
 "abstract": ("What a proposal shows field by field, the rules that decide which value wins, why "
              "showing losses matters more than showing the result, and the related records a "
              "merge has to move."),
 "lede": ("A merge proposal that shows the resulting record looks complete and hides the only "
          "thing worth looking at. Everything that makes a merge dangerous is in what disappears, "
          "and a person scanning a proposal for four seconds will see it only if it is on the "
          "screen."),
 "tags": ["duplicates", "merging", "data quality", "CRM", "review", "serverless"],
 "takeaways": [
  "Show three columns: record A, record B, and the result.",
  "Field rules decide the default; most-complete and most-recent cover nearly everything.",
  "Anything that would be lost is highlighted, including free text and tags.",
  "Related records -- orders, notes, messages -- move, and the count is shown.",
  "One button to confirm, one to reject, one to keep both values where the system supports it.",
 ],
 "blocks": [
  ("h2", "Three columns"),
  ("callout", "What a proposal shows", [
   "<strong>Name.</strong> A: J Reed &middot; B: Jonathan Reed &middot; <strong>Result: Jonathan "
   "Reed</strong> <em>(most complete)</em>",
   "<strong>Email.</strong> A: j.reed@old.example &middot; B: jonathan@new.example &middot; "
   "<strong>Result: jonathan@new.example</strong> <em>(most recent; the other is kept as an "
   "alternate)</em>",
   "<strong>Phone.</strong> A: 07700 900123 &middot; B: <em>empty</em> &middot; <strong>Result: "
   "07700 900123</strong>",
   "<strong>Notes.</strong> A: <em>\"prefers email, no calls before 10\"</em> &middot; B: "
   "<em>empty</em> &middot; <strong>Result: kept</strong>",
   "<strong>Would be lost:</strong> nothing.",
   "<strong>Related:</strong> 4 orders and 11 messages from A move to the merged record.",
  ]),
  ("p", "The fifth line is the one that changes behaviour. In this example it says nothing, which "
        "is a two-word confirmation that the merge is safe. When it says \"A's address, A's "
        "company name, and a note from 2024\", somebody stops and reads."),
  ("h2", "Which value wins"),
  ("fig", ("chain", {
    "entry": {"title": "One field, two values", "sub": ["A and B"], "icon": "doc"},
    "steps": [
      {"title": "One empty?", "icon": "branch",
       "exit": {"title": "The other wins", "sub": ["most of the cases"], "icon": "check",
                "label": "yes"}},
      {"title": "Identical?", "icon": "branch",
       "exit": {"title": "No decision needed", "sub": ["and it is evidence"], "icon": "link",
                "label": "yes"}},
      {"title": "A rule for this field?", "sub": ["most complete, most recent"], "icon": "filter",
       "side": {"title": "Field rules", "sub": ["one per field"], "icon": "chart"}},
      {"title": "Can both be kept?", "sub": ["alternates, tags, notes"], "icon": "branch",
       "exit": {"title": "Keep both", "sub": ["nothing is lost"], "icon": "retry",
                "label": "yes"}},
      {"title": "One wins, one is lost", "sub": ["highlight it"], "icon": "alarm"}],
    "note": "Most fields never reach the last step. The ones that do are what a person checks."}),
   "How each field's value is decided. The keep-both branch is worth implementing wherever the "
   "target system allows it, because it removes the loss entirely.",
   "How a merge decides which value wins for each field",
   "A vertical chain of five steps entered by a box labelled One field, two values, A and B. Step "
   "one asks whether one is empty; if so the other wins, which covers most cases. Step two asks "
   "whether they are identical; if so no decision is needed and it counts as evidence. Step three "
   "applies the rule for that field from a one-per-field rule set, such as most complete or most "
   "recent. Step four asks whether both can be kept, as alternates, tags or appended notes; if so "
   "it exits to Keep both, so nothing is lost. Step five is one wins and one is lost, which is "
   "highlighted. A note says most fields never reach the last step and the ones that do are what "
   "a person checks."),
  ("h3", "Keep both wherever possible"),
  ("p", "A surprising number of fields do not actually require a choice. Two email addresses can "
        "usually be a primary and an alternate. Two phone numbers can be mobile and landline. "
        "Tags are a union. Notes can be appended with a dated separator rather than one "
        "overwriting the other."),
  ("p", "Every field moved from \"one wins\" to \"keep both\" removes a loss and therefore removes "
        "a reason for somebody to hesitate over a proposal. It is worth going through the field "
        "list once specifically looking for these."),
  ("h2", "Related records"),
  ("p", "A merge is not a record edit. Orders, messages, notes, invoices and appointments all "
        "point at one of the two records, and a merge has to move them &mdash; which is the part "
        "that makes a wrong merge genuinely hard to unpick."),
  ("fig", ("strip", {
    "stages": [
      {"title": "The record", "sub": ["one row"], "icon": "person"},
      {"title": "Orders", "sub": ["4 move"], "icon": "cart"},
      {"title": "Messages", "sub": ["11 move"], "icon": "email"},
      {"title": "Notes", "sub": ["2 move"], "icon": "doc"},
      {"title": "All counted", "sub": ["and all reversible"], "icon": "retry"}],
    "title": "A MERGE MOVES MORE THAN A ROW",
    "note": "Showing the counts is what makes the scale of the change visible before confirming."}),
   "What a merge actually moves. The counts on the proposal are what tell somebody whether this "
   "is a trivial merge or a consequential one.",
   "The related records a contact merge has to move",
   "A horizontal row of five boxes. The record: one row. Orders: four move. Messages: eleven "
   "move. Notes: two move. All counted: and all reversible. A note says showing the counts is "
   "what makes the scale of the change visible before confirming."),
  ("p", "The counts also do useful work as evidence. A candidate pair where one record has four "
        "orders and eleven messages and the other has nothing at all is very likely a genuine "
        "duplicate created by a form submission. A pair where both have substantial history is "
        "worth more scrutiny, because two active customers with overlapping details are more "
        "often two customers."),
  ("p", "Next: undoing one."),
 ],
},
{
 "slug": "how-a-merge-gets-undone",
 "title": "How a merge gets undone",
 "nav": "How it is undone",
 "read": 5, "words": 730,
 "desc": ("What has to be stored to reverse a merge, how long to keep it, what cannot be undone, "
          "and the monthly numbers."),
 "og": ("Undo is only possible if both originals were stored in full. Reconstructing a merged "
        "record from a diff is how an undo produces a third wrong record."),
 "abstract": ("What has to be stored to make a merge reversible, how long to keep it, the changes "
              "that genuinely cannot be undone, and the numbers worth watching."),
 "lede": ("Reversibility is what makes confirming a merge a four-second decision rather than a "
          "careful one, and it is only real if the right things were stored beforehand. An undo "
          "built from a diff produces a third record that matches neither original."),
 "tags": ["duplicates", "undo", "audit trail", "data quality", "reporting", "serverless"],
 "takeaways": [
  "Store both original records in full, plus every related-record move.",
  "Undo restores; it never reconstructs. A diff is not enough.",
  "Anything that happened after the merge stays with the record it was created on.",
  "Ninety days is a sensible window, and the report says what has passed it.",
  "The number to watch is undos as a share of merges; it should be very low and not zero.",
 ],
 "blocks": [
  ("h2", "What has to be stored"),
  ("fig", ("chain", {
    "entry": {"title": "A confirmed merge", "sub": ["about to run"], "icon": "check"},
    "steps": [
      {"title": "Snapshot both records", "sub": ["complete, not a diff"], "icon": "database"},
      {"title": "List every related move", "sub": ["ids, both directions"], "icon": "log"},
      {"title": "Perform the merge", "sub": ["record, then relations"], "icon": "retry"},
      {"title": "Store the undo bundle", "sub": ["snapshots plus moves"], "icon": "bucket"},
      {"title": "Merged, reversibly", "sub": ["for the window"], "icon": "clock"}],
    "note": "Snapshot before, not after. A merge that fails halfway needs the same bundle."}),
   "What is captured before a merge runs. The bundle is written before the change rather than "
   "after it, which also makes a partial failure recoverable.",
   "How a merge is made reversible before it runs",
   "A vertical chain of five steps entered by a box labelled A confirmed merge, about to run. "
   "Step one snapshots both records completely, not as a diff. Step two lists every related "
   "record move with its identifiers in both directions. Step three performs the merge, the "
   "record first and then the relations. Step four stores the undo bundle of snapshots plus "
   "moves. Step five is Merged, reversibly, for the window. A note says snapshot before rather "
   "than after, because a merge that fails halfway needs the same bundle."),
  ("h3", "Snapshots, not diffs"),
  ("p", "A diff is smaller and it is not enough. Reversing from a diff requires the current state "
        "to be exactly what the merge produced, and by the time somebody wants an undo, somebody "
        "else has usually edited the merged record. Applying a reverse diff to a changed record "
        "produces a third state that never existed."),
  ("p", "Storing both records in full means undo is a restore: put record A back as it was, put "
        "record B back as it was, and move the related records back to whichever they came from. "
        "That is unambiguous regardless of what happened in between."),
  ("h2", "What cannot be undone"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Merged", "sub": ["Monday"], "icon": "retry"},
      {"title": "Order placed", "sub": ["Tuesday, on the merged record"], "icon": "cart"},
      {"title": "Undo requested", "sub": ["Wednesday"], "icon": "search"},
      {"title": "Which record?", "sub": ["it belongs to neither"], "icon": "branch"},
      {"title": "Stays put, flagged", "sub": ["a person decides"], "icon": "person"}],
    "title": "THE THING AN UNDO CANNOT DECIDE",
    "note": "Anything created after the merge has no original owner. It stays and is flagged."}),
   "The one case an undo cannot resolve on its own. Records created after the merge belong to "
   "neither original and need a person's judgement.",
   "What happens to records created after a merge when it is undone",
   "A horizontal row of five boxes. Merged: on Monday. Order placed: on Tuesday, against the "
   "merged record. Undo requested: on Wednesday. Which record: it belongs to neither original. "
   "Stays put, flagged: and a person decides. A note says anything created after the merge has no "
   "original owner, so it stays and is flagged."),
  ("p", "This is genuinely undecidable by the system and the honest handling is to say so: the "
        "undo restores both records, moves back everything that was moved, leaves anything "
        "created afterwards on whichever record survived, and reports exactly what it left "
        "behind. A person then spends thirty seconds deciding where the Tuesday order belongs."),
  ("h3", "The window"),
  ("p", "Ninety days is a reasonable default. Undo bundles are small but not nothing, and the "
        "practical observation is that almost every undo request comes within a fortnight &mdash; "
        "somebody notices the merged record looks wrong the next time they open it."),
  ("p", "What matters more than the exact number is that the report says which merges have passed "
        "the window, so \"can we undo the merge from March\" has an answer before somebody starts "
        "looking for it."),
  ("h2", "The numbers"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Proposed", "sub": ["58 this month"], "icon": "report"},
      {"title": "Confirmed", "sub": ["41"], "icon": "check"},
      {"title": "Rejected", "sub": ["17, remembered"], "icon": "stop"},
      {"title": "Automatic", "sub": ["9, conclusive"], "icon": "retry"},
      {"title": "Undone", "sub": ["1"], "icon": "alarm"}],
    "title": "ONE MONTH OF MERGING",
    "note": "One undo in fifty merges is about right. Zero for months means the band is too tight."}),
   "A month of merging in five numbers. The undo count is the calibration signal and it should be "
   "low rather than absent.",
   "One month of duplicate merging summarised in five numbers",
   "A horizontal row of five boxes. Proposed: fifty-eight this month. Confirmed: forty-one. "
   "Rejected: seventeen, and remembered. Automatic: nine, all conclusive. Undone: one. A note says "
   "one undo in fifty merges is about right, and zero for months means the band is too tight."),
  ("p", "The rejection count is the more useful tuning signal. Seventeen rejections out of "
        "fifty-eight proposals means about thirty per cent of what the scorer proposes is wrong, "
        "which is high but not alarming for a system where rejecting costs four seconds. Fifty "
        "per cent would mean the threshold is too low; five per cent would suggest it is too high "
        "and real duplicates are being scored below the proposal line."),
  ("p", "A zero undo rate sustained over months is worth noticing rather than celebrating: it "
        "usually means the automatic band is set so conservatively that almost nothing merges "
        "without a person, which is safe and may be leaving obvious duplicates in place."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="thousand contacts",
 volumes=[(14, "14k contacts"), (50, "50k contacts"), (200, "200k contacts")],
 read_each=0.0,
 msgs_each=0.3,
 extra=[("compute", "Lambda &mdash; blocking and scoring", "#ED7100", 0.012, 0.0)],
 lede=("The whole database is re-blocked and re-scored weekly, so the cost scales with contact "
       "count rather than with duplicates found. Fourteen thousand contacts is a small business "
       "with several years of accumulation. Here is where each cent goes."),
 takeaway_extra=("No model. The cost is compute over the whole database once a week, and it "
                 "scales linearly rather than quadratically because of blocking."),
 risks=[
  "<strong>Skipping the block size cap.</strong> One degenerate key value &mdash; four hundred "
  "records sharing the company's own phone number &mdash; produces eighty thousand pairs on its "
  "own and turns a linear job back into a quadratic one.",
  "<strong>Re-proposing rejected pairs.</strong> Not a cost risk but the one that kills the "
  "system: the same six hundred rejections every week means nobody opens the review after the "
  "second round.",
  "<strong>Log retention left at never.</strong> A weekly job over the whole database logs a lot "
  "if it logs per pair. Log per run, not per comparison.",
 ],
 per_unit_note=("The compute band is Lambda time to compute keys, build blocks and score pairs "
                "across the whole database. There is no model anywhere in this system: matching "
                "is exact comparison and weighted evidence."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="dm",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the three tables, the merge transaction, and the undo bundle."),
 outside=[
  {"title": "Contact source", "sub": ["CRM API, read and write"], "icon": "team"},
  {"title": "Field rules", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["proposals, monthly"], "icon": "email"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["undo bundles,", "weekly run"], "icon": "bucket"},
  {"title": "Lambda x3", "sub": ["block, score, merge"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["pairs, decisions,", "merges"], "icon": "database"}],
 note="us-east-1. One account. The only write to the CRM is a merge a person confirmed.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Contact source, a CRM API read and "
  "written. Field rules, read through the Google Sheets API read-only. And SES outbound, carrying "
  "merge proposals and the monthly summary. Inside the account, three groups. S3 holding undo "
  "bundles and EventBridge providing a weekly run. Three Lambda functions named block, score and "
  "merge. And three DynamoDB tables named pairs, decisions and merges. A note gives the region as "
  "us-east-1, one account, and states that the only write to the CRM is a merge a person "
  "confirmed."),
 functions=[
  ["<code>dm-block</code>", "EventBridge weekly",
   "Computes four keys per record, forms blocks, caps oversized ones",
   "300s / 3008&nbsp;MB"],
  ["<code>dm-score</code>", "SQS block queue",
   "Rarity-weighted evidence for and against; writes candidate pairs",
   "60s / 1024&nbsp;MB"],
  ["<code>dm-merge</code>", "Function URL",
   "Builds the proposal; on confirmation writes the undo bundle then merges",
   "60s / 1024&nbsp;MB"]],
 roles=[
  ["<code>dm-block-role</code>",
   "<code>secretsmanager:GetSecretValue</code>, <code>dynamodb:PutItem</code>",
   "The CRM read credential; the pairs table"],
  ["<code>dm-score-role</code>", "<code>dynamodb:Query</code>/<code>UpdateItem</code>",
   "Pairs and decisions"],
  ["<code>dm-merge-role</code>",
   "<code>s3:PutObject</code>, <code>secretsmanager:GetSecretValue</code>, "
   "<code>dynamodb:PutItem</code>",
   "The undo prefix; the CRM write credential; the merges table"]],
 tables=[
  ("Table: pairs",
   "PK   pair_key          S   min(id_a,id_b)#max(id_a,id_b)\n"
   "     score             N   4.8\n"
   "     terms             L   [{field, agreed, rarity, weight}]\n"
   "     against           L   [{reason, strength}]\n"
   "     band              S   automatic | propose | record_only\n"
   "     blocked_by        L   which keys produced this pair\n"
   "     ttl               N   epoch, +30 days\n\n"
   "The pair key is order-independent, so A-B and B-A are one row. Getting that\n"
   "wrong doubles every count and proposes each pair twice."),
  ("Table: decisions",
   "PK   pair_key          S   min#max\n"
   "     decision          S   merged | not_a_duplicate\n"
   "     decided_by        S   a person, or 'automatic'\n"
   "     decided_at        S   2026-08-05T11:02:00Z\n\n"
   "No TTL, ever. A pair somebody has declared separate must never be proposed\n"
   "again -- that is the single feature that keeps the review worth opening."),
  ("Table: merges",
   "PK   merge_id          S   mrg_2026_08_05_c41a\n"
   "     kept_id           S   the surviving record\n"
   "     merged_id         S   the record that was absorbed\n"
   "     bundle_key        S   s3://undo/mrg_....json\n"
   "     moved             L   [{type, id, from, to}]\n"
   "     undoable_until    S   2026-11-03\n"
   "     undone_at         S   or null\n\n"
   "`moved` is the complete list of related records repointed, in both\n"
   "directions, which is what makes an undo a restore rather than a guess.")],
 inbound=[
  "<strong>The CRM read credential and the write credential are separate secrets.</strong> Only "
  "<code>dm-merge</code> can read the write credential, and only on a confirmed proposal.",
  "<strong>Confirmation links</strong> are signed, scoped to one pair, single-use, and expire "
  "after thirty days &mdash; the same window as the pairs table, so a stale link cannot act on a "
  "recomputed pair.",
  "<strong>The undo bundle is written before the merge</strong>, not after. A merge that fails "
  "part way through leaves related records split across both, and the bundle is what puts them "
  "back.",
  "<strong>Merges are serialised per record.</strong> Two proposals involving the same record "
  "cannot execute concurrently; a conditional write on the record id enforces it."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Blocking is key computation, scoring is "
  "weighted evidence, and both need to be identical between runs.",
  "<strong>An embedding-based similarity</strong> is the obvious alternative and it produces the "
  "thing this design specifically avoids: a single opaque number instead of visible evidence.",
  "<strong>The proposal has to be explainable</strong> in the four seconds somebody spends on it, "
  "and \"same phone, same rare surname, different first name\" is explainable in a way that 0.88 "
  "is not.",
  "<strong>Rarity weighting</strong> gives most of what a learned model would, from a count query "
  "over your own data, and it is stable between runs.",
  "<strong>The cost page assumes none</strong>, which is why compute is the only variable band."],
 gotchas=[
  "Make the pair key order-independent. A-B and B-A as separate rows doubles every count and "
  "proposes each pair twice.",
  "Cap block sizes. One placeholder phone number shared by four hundred records reintroduces the "
  "quadratic problem blocking exists to solve.",
  "Never expire the not-a-duplicate decisions. Re-proposing rejected pairs is what makes people "
  "stop opening the review.",
  "Store full snapshots, not diffs. An undo applied to a record somebody has since edited must "
  "restore, not reconstruct.",
  "Write the undo bundle before the merge runs, so a partial failure is recoverable with the same "
  "mechanism."],
))
