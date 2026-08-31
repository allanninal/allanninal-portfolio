"""Day 87 -- 2026-07-20 -- Offer letter generator."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "offer-letter-generator"
NAME = "Offer letter generator"

SPEC = {
 "slug": SLUG, "date": "2026-07-20", "name": NAME,
 "tagline": ("An offer is agreed in a conversation and a correct letter exists ten minutes "
             "later -- from your own approved template, with the terms that were actually "
             "agreed, and nothing invented."),
 "lede": ("A small system that turns an agreed offer into a letter from your own approved "
          "template: the terms come from a short form, the wording comes from the template, and "
          "anything that does not fit a template clause stops and asks. It never invents a "
          "term and never sends without a person reading it. Seven posts on the same system -- "
          "one diagram at a time -- with a cost breakdown and an engineering reference at the "
          "end."),
 "keywords": ["offer letters", "hiring", "employment contracts", "document generation",
              "human in the loop", "serverless"],
 "icons": ["doc", "form", "check"],
 "faq": [
  ("What is an offer letter generator?",
   "A small serverless system that fills your own approved offer template from a short form of "
   "agreed terms, flags anything the template does not cover, and puts a draft in front of a "
   "person to send. It never writes contractual wording of its own."),
  ("Does a model write the letter?",
   "No. The wording is your template, approved by whoever approves such things. A model is used "
   "in exactly one place: reading a free-text note about what was agreed and turning it into "
   "form fields, which a person then checks."),
  ("What happens with an unusual term?",
   "It stops. A term with no matching template clause -- an unusual notice period, a bespoke "
   "bonus, a relocation arrangement -- is flagged and the draft is marked as needing a clause "
   "somebody writes. The system never improvises contractual language."),
  ("Does it send the offer?",
   "No. It produces a draft and tells the hiring manager it is ready. Sending an offer is a "
   "decision with legal weight, and the send button belongs to a person."),
  ("What does it cost to run?",
   "A couple of dollars a month. Offer volume is low even in a business that is growing. See "
   "part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "offer-letter-generator-on-aws",
 "title": "An offer letter generator on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 880,
 "desc": ("Fills your approved offer template from the terms that were agreed, flags anything "
          "it does not cover, and hands a person a draft to send. AWS, about $2 a month."),
 "og": ("Your template, your clauses, the terms that were actually agreed -- and a hard stop "
        "on anything the template does not cover."),
 "abstract": ("The whole system on one page -- a terms form, a clause matcher and a drafter -- "
              "with one hard rule: it never writes contractual wording."),
 "lede": ("The gap between agreeing an offer and sending the letter is where small businesses "
          "lose candidates. Not because the letter is hard, but because it needs somebody with "
          "the template, the right numbers and half an hour, and those three things rarely "
          "coincide on the day the conversation happened. Four days later the candidate has had "
          "another offer in writing. This post walks through a small system that closes that "
          "gap to about ten minutes without letting anything improvise a contract."),
 "tags": ["offer letters", "hiring", "employment contracts", "document generation",
          "human in the loop", "serverless"],
 "takeaways": [
  "The wording is always your approved template. Nothing generates contractual language.",
  "The terms come from a short form, or from a note that a model turns into form fields.",
  "A term with no matching template clause stops the draft and asks for one.",
  "The output is a draft plus a diff against the standard template, so review is quick.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Agreed terms", "sub": ["a form, or a note"], "icon": "form"},
      {"title": "Your templates", "sub": ["approved clauses"], "icon": "doc"},
      {"title": "Hiring manager", "sub": ["reads, then sends"], "icon": "person"}],
    "inside": [
      {"title": "Terms reader", "sub": ["a note into fields,", "or straight from a form"],
       "icon": "model"},
      {"title": "Clause matcher", "sub": ["every term to an", "approved clause"], "icon": "filter"},
      {"title": "Drafter", "sub": ["the letter, plus a diff", "against standard"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "what was agreed"},
              {"from": 1, "to": 1, "label": "the wording"},
              {"from": 2, "to": 2, "label": "a draft to review", "up": True}],
    "note": "No clause is ever written by the system. Unmatched terms stop the draft."}),
   "Three things outside the account, three pieces inside it. The clause matcher is the safety "
   "mechanism: every term in the letter has to map to wording somebody approved.",
   "System: agreed terms in, an approved-template draft out",
   "Three boxes across the top sit outside the AWS account. On the left, Agreed terms: arriving "
   "as a short form or as a free-text note. In the middle, Your templates: the approved clauses "
   "your business uses. On the right, Hiring manager: the person who reads the draft and sends "
   "it. Each connects by an arrow to the AWS account container below. What was agreed flows "
   "down into the account. The templates feed in the wording. A draft to review goes back out. "
   "Inside the AWS account are three components in a row. On the left, the Terms reader, which "
   "turns a note into fields or takes them straight from a form. In the middle, the Clause "
   "matcher, which maps every term to an approved clause. On the right, the Drafter, which "
   "produces the letter plus a diff against the standard template. A note at the bottom says no "
   "clause is ever written by the system, and unmatched terms stop the draft."),
  ("h3", "What you set up once (the outside)"),
  ("ul", [
   "<strong>Your templates.</strong> The offer letter you already use, broken into clauses, "
   "with the variable bits marked. Most businesses have two or three variants &mdash; salaried, "
   "hourly, fixed term &mdash; and doing this once is a morning's work with whoever approved "
   "the original wording.",
   "<strong>A clause library.</strong> The optional bits: probation lengths, notice periods, "
   "car allowances, bonus structures, relocation. Each one is approved wording with variables. "
   "The library is what determines which offers the system can produce without stopping.",
   "<strong>A terms form.</strong> Eight or nine fields: name, role, start date, salary or rate, "
   "hours, probation, notice, and anything else. Covered in Part 2, along with the note lane for "
   "people who would rather forward the email where it was agreed.",
  ]),
  ("h3", "What runs on every offer (the inside)"),
  ("ul", [
   "<strong>The terms reader.</strong> If a form was filled in, this does nothing. If somebody "
   "forwarded \"agreed with Kwame: 38k, starts 28th, 3 month probation, standard notice\", the "
   "reader turns that into fields and shows them for confirmation. It is the only place a model "
   "appears, and its output is checked by a person before anything is drafted.",
   "<strong>The clause matcher.</strong> Takes each term and finds the approved clause that "
   "expresses it. A three-month probation matches the probation clause with a variable filled. "
   "A four-day week matches the part-time hours clause. A term with no match does not get "
   "improvised wording &mdash; it stops the draft and says which term needs a clause.",
   "<strong>The drafter.</strong> Assembles the letter and produces two things: the document, "
   "and a diff against the standard template showing exactly which clauses differ and how. The "
   "diff is what makes review take two minutes rather than fifteen, because the reviewer reads "
   "the differences rather than the whole letter.",
  ]),
  ("h2", "One offer, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Agreed", "sub": ["in a conversation"], "icon": "chat"},
      {"title": "Captured", "sub": ["form or note"], "icon": "form"},
      {"title": "Matched", "sub": ["every term to a clause"], "icon": "filter"},
      {"title": "Drafted", "sub": ["letter plus diff"], "icon": "doc"},
      {"title": "Sent", "sub": ["by a person"], "icon": "person"}],
    "title": "ONE OFFER, END TO END",
    "note": "About ten minutes, of which nine are somebody reading the diff."}),
   "The same system as one line. The time saved is not in the drafting; it is in never having to "
   "find the template, the last similar letter, or the right numbers.",
   "One offer from agreement to sent letter, in five stages",
   "A horizontal row of five boxes joined by arrows. Agreed: in a conversation. Captured: by "
   "form or note. Matched: every term to an approved clause. Drafted: the letter plus a diff. "
   "Sent: by a person. A note says about ten minutes, of which nine are somebody reading the "
   "diff."),
  ("h2", "In plain words"),
  ("p", "A hiring manager finishes a call at 11:40 having agreed an offer. They open the form on "
        "their phone: name, role, £38,000, starts the 28th, three-month probation, "
        "one-month notice, standard everything else. The clause matcher finds an approved clause "
        "for every one of those. The drafter assembles the letter from the salaried template and "
        "produces a diff showing two differences from standard: the probation is three months "
        "rather than six, and the start date is inside the usual notice window."),
  ("p", "At 11:52 whoever approves offers gets a message with the draft and those two lines. "
        "They read two differences rather than a four-page letter, agree with both, and send it. "
        "The candidate has a written offer before lunch on the day they agreed it, which is the "
        "single most effective thing a small business can do to stop losing people to larger "
        "employers with faster HR functions."),
  ("callout", "Design rules that shaped every decision", [
   "The system never writes contractual wording. Every sentence in the letter came from a "
   "template somebody approved.",
   "An unmatched term stops the draft. Improvising a clause is the one failure that could cost "
   "real money.",
   "Show a diff, not a document. Reviewing two differences is quick; reviewing four pages is "
   "not, and the second one does not actually happen.",
   "The model reads, it does not write. Its only job is turning a note into fields somebody then "
   "confirms.",
   "Nothing is sent by the system. A draft is ready; a person sends it.",
   "Every sent offer keeps the exact document and the clause versions it used, because contract "
   "wording changes and letters get read back years later.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The temptation with document generation and a capable model is to let it write the "
        "letter. It would do a plausible job, and plausible is exactly the wrong standard for a "
        "document that forms part of an employment contract. A clause that reads well and "
        "differs subtly from the one your solicitor approved is a liability that will not be "
        "noticed until it matters."),
  ("p", "So the design confines generation entirely to assembly, and puts the model somewhere "
        "genuinely useful and completely safe: reading a hurried note into structured fields "
        "that a human confirms before anything is produced. The letter itself is your wording, "
        "every time, with variables filled in."),
  ("p", "The next four posts walk through each piece: how the terms get captured, how clauses "
        "get matched, what happens to an unusual term, and what a sent offer leaves behind. One "
        "diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-the-agreed-terms-get-captured",
 "title": "How the agreed terms get captured",
 "nav": "How terms are captured",
 "read": 5, "words": 780,
 "desc": ("A nine-field form, a note lane for people who will not use it, and the fields that "
          "must never be inferred from anything."),
 "og": ("Two lanes: a nine-field form, and a forwarded note that a model turns into the same "
        "nine fields for a person to confirm. Some fields are never inferred."),
 "abstract": ("A nine-field form, a note lane for the people who will never use a form, and the "
              "small set of fields that must never be inferred from anything at all."),
 "lede": ("The capture step decides whether this system gets used at 11:40 on the day or at 9am "
          "three days later, which is the entire difference between it working and not. So there "
          "are two lanes, and the second one exists purely because some people will always "
          "forward an email rather than fill in a form."),
 "tags": ["offer letters", "hiring", "forms", "AWS Bedrock", "data entry", "serverless"],
 "takeaways": [
  "Nine fields, chosen because they are what actually varies between offers.",
  "The note lane accepts a forwarded email and produces the same nine fields to confirm.",
  "Salary, start date and role are never inferred from a previous offer or a job advert.",
  "Every field the reader filled from a note is shown differently from one that was typed.",
  "A confirmed set of terms is immutable; a change produces a new version.",
 ],
 "blocks": [
  ("h2", "Nine fields"),
  ("pre", "candidate      Kwame Osei              name as it goes on the letter\n"
          "role           Field service engineer   the title, exactly\n"
          "basis          salaried | hourly | fixed_term\n"
          "pay            38000                    per year, or per hour\n"
          "hours          37.5                     per week\n"
          "start_date     2026-08-28\n"
          "probation      3 months                 from the clause library's options\n"
          "notice         1 month                  likewise\n"
          "extras         car allowance            zero or more library clauses"),
  ("p", "Nine because that is what genuinely varies. Everything else in an offer letter &mdash; "
        "holiday, pension, place of work, the pre-employment conditions &mdash; is either "
        "identical across offers or determined by the basis, and putting it on the form makes "
        "the form long enough that people go back to writing letters by hand."),
  ("h2", "Two lanes"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "The form", "sub": ["nine fields, on a phone"], "icon": "form", "label": "typed"},
      {"title": "A forwarded note", "sub": ["the email where it", "was agreed"], "icon": "email",
       "label": "prose"},
      {"title": "A voice note", "sub": ["transcribed first"], "icon": "voice", "label": "spoken"}],
    "target": {"title": "Nine confirmed fields", "sub": ["shown for a check,", "then frozen"],
               "icon": "check",
               "then": {"title": "Clause matcher", "sub": ["term by term"], "icon": "filter"}},
    "note": "Everything ends at the same confirmation screen. Nothing drafts from an unconfirmed field."}),
   "Three ways to capture an offer and one confirmation gate. The gate is what makes the note "
   "lane safe: nothing is drafted from a field the reader inferred until a person has seen it.",
   "Three capture lanes converging on nine confirmed fields",
   "Three boxes stacked on the left. The form, nine fields filled in on a phone, labelled typed. "
   "A forwarded note, being the email where the offer was agreed, labelled prose. And a voice "
   "note, transcribed first, labelled spoken. All three converge on Nine confirmed fields, shown "
   "for a check and then frozen. Below that, connected by a downward arrow, is the Clause "
   "matcher, which works term by term. A note says everything ends at the same confirmation "
   "screen and nothing drafts from an unconfirmed field."),
  ("h3", "The confirmation screen"),
  ("p", "Whichever lane was used, the nine fields are shown before anything is drafted, and "
        "fields the reader inferred are visually distinct from fields somebody typed. That "
        "distinction matters: a person scanning a confirmation screen will read a highlighted "
        "field and skim a plain one, and the highlighted ones are exactly where an error would "
        "be."),
  ("p", "The screen also shows what the reader could not fill. A note that says \"agreed the "
        "usual\" leaves probation and notice blank, which are then two taps from the library's "
        "options rather than a guess about what usual means for this role."),
  ("h2", "Fields that are never inferred"),
  ("ul", [
   "<strong>Pay.</strong> Never taken from the job advert, the salary band, or a previous offer "
   "for the same role. If the note does not state a number, the field is blank. A letter with "
   "the wrong salary in it is the single worst output this system could produce.",
   "<strong>Start date.</strong> Never computed from a notice period or assumed to be the "
   "first of a month. Dates get discussed and changed, and inferring one produces a letter "
   "that contradicts a conversation.",
   "<strong>Role title.</strong> Taken as agreed rather than normalised to whatever the job "
   "advert said. The title on the letter is the title, and tidying it is not the system's "
   "business.",
   "<strong>Anything in extras.</strong> A car allowance is either mentioned or it is not. "
   "Inferring one from the role would be inventing a term.",
  ]),
  ("h2", "Versions"),
  ("p", "A confirmed set of terms is frozen. Offers get renegotiated &mdash; a candidate comes "
        "back on salary, a start date moves &mdash; and the natural implementation is to edit "
        "the fields and redraft. That loses the fact that a different letter went out first, "
        "which matters if the two ever have to be compared."),
  ("fig", ("strip", {
    "stages": [
      {"title": "v1 confirmed", "sub": ["£38,000, 28 Aug"], "icon": "check"},
      {"title": "v1 sent", "sub": ["document kept"], "icon": "doc"},
      {"title": "Renegotiated", "sub": ["£40,000"], "icon": "chat"},
      {"title": "v2 confirmed", "sub": ["a new version"], "icon": "retry"},
      {"title": "Both kept", "sub": ["with what changed"], "icon": "log"}],
    "title": "AN OFFER THAT CHANGED",
    "note": "Editing v1 would have deleted the only record that a different letter was sent."}),
   "How a renegotiated offer is recorded. Versioning costs nothing and preserves the fact that "
   "an earlier letter exists in somebody's inbox.",
   "How a renegotiated offer produces a second version",
   "A horizontal row of five boxes. Version one confirmed: thirty-eight thousand, starting the "
   "twenty-eighth of August. Version one sent: the document is kept. Renegotiated: forty "
   "thousand. Version two confirmed: a new version rather than an edit. Both kept: with a record "
   "of what changed. A note says editing version one would have deleted the only record that a "
   "different letter was sent."),
  ("p", "Next: how each term finds its approved clause."),
 ],
},
{
 "slug": "how-a-term-finds-its-clause",
 "title": "How a term finds its clause",
 "nav": "How clauses match",
 "read": 5, "words": 790,
 "desc": ("Mapping nine fields onto approved wording, why the library is a small set of exact "
          "options rather than free values, and the variables that are safe to fill."),
 "og": ("A clause library of exact options rather than free values is what makes matching "
        "deterministic. Only a small set of variables is ever substituted."),
 "abstract": ("How nine fields map onto approved wording, why the clause library holds a small "
              "set of exact options rather than free values, and which variables are safe to "
              "substitute."),
 "lede": ("Clause matching sounds like the interesting part and is deliberately the dullest. "
          "Everything here is a lookup, and the design work went into shaping the library so "
          "that a lookup is sufficient."),
 "tags": ["offer letters", "document generation", "templates", "employment contracts",
          "compliance", "serverless"],
 "takeaways": [
  "The library holds options, not ranges. Three months and six months are two clauses.",
  "Only three kinds of variable are ever substituted: a name, a number and a date.",
  "A clause carries its own version, and a sent letter records which versions it used.",
  "Ordering is fixed by the template, not by the order terms were captured.",
  "A clause that has never been used is flagged annually, because unused clauses go stale.",
 ],
 "blocks": [
  ("h2", "Options, not ranges"),
  ("p", "The instinct when building a clause library is to write one probation clause with the "
        "length as a variable. It is tempting, it is fewer clauses, and it lets somebody type "
        "\"seven weeks\" and get a letter."),
  ("p", "The alternative is to hold a small set of exact options &mdash; no probation, three "
        "months, six months &mdash; each as its own approved clause. It is slightly more to "
        "maintain and it removes an entire category of problem: nobody can produce a letter with "
        "a probation length that has never been approved, because there is no clause for it. A "
        "seven-week probation stops the draft, which is exactly what should happen the first "
        "time anybody agrees one."),
  ("fig", ("chain", {
    "entry": {"title": "Nine confirmed terms", "sub": ["from Part 2"], "icon": "check"},
    "steps": [
      {"title": "Pick the base template", "sub": ["from the basis"], "icon": "doc",
       "side": {"title": "Templates", "sub": ["salaried, hourly, fixed"], "icon": "chart"}},
      {"title": "Match each term", "sub": ["to an exact option"], "icon": "filter",
       "side": {"title": "Clause library", "sub": ["approved wording"], "icon": "database"},
       "exit": {"title": "No clause exists", "sub": ["stop, and ask for one"], "icon": "stop",
                "label": "unmatched"}},
      {"title": "Fill the variables", "sub": ["name, number, date"], "icon": "form"},
      {"title": "Order by the template", "sub": ["not by capture order"], "icon": "log"},
      {"title": "Assemble", "sub": ["and diff against standard"], "icon": "report"}],
    "note": "Every path either finds approved wording or stops. There is no third option."}),
   "How terms become a letter. The single exit is the whole safety story: an unmatched term "
   "cannot produce improvised wording because there is no code path that writes any.",
   "How confirmed terms are matched to approved clauses",
   "A vertical chain of five steps entered by a box labelled Nine confirmed terms, from Part 2. "
   "Step one picks the base template from the employment basis, choosing between salaried, "
   "hourly and fixed-term. Step two matches each term to an exact option in the clause library "
   "of approved wording; an unmatched term exits to No clause exists, which stops and asks for "
   "one. Step three fills the variables, being a name, a number and a date. Step four orders the "
   "clauses by the template rather than by the order the terms were captured. Step five "
   "assembles the letter and diffs it against standard. A note says every path either finds "
   "approved wording or stops, and there is no third option."),
  ("h2", "The three safe variables"),
  ("table", ["Variable", "Example", "Why it is safe"], [
   ["A name", "Kwame Osei", "Substituting a name cannot change what a clause means"],
   ["A number", "38,000", "Formatted, never rounded or interpreted"],
   ["A date", "28 August 2026", "Formatted long-hand, never computed from another date"],
  ]),
  ("p", "That is the complete list. Anything else &mdash; a duration, a condition, a job "
        "description &mdash; is part of the clause rather than a variable in it, which means "
        "changing it means choosing a different approved clause. This is more restrictive than "
        "most templating systems and it is the restriction that makes the output trustworthy."),
  ("h3", "Numbers are formatted, not interpreted"),
  ("p", "A salary of 38000 becomes \"£38,000\" and never \"£38,000 per annum (thirty-eight "
        "thousand pounds)\" unless the approved clause says so. An hourly rate of 14.5 becomes "
        "\"£14.50\" and never \"£14.50 per hour, approximately £28,275 per year\", because that "
        "second figure is a calculation with assumptions in it and it does not belong in a "
        "letter unless somebody approved the assumption."),
  ("h2", "Clause versions"),
  ("p", "Contract wording changes: a solicitor revises a notice clause, legislation moves, the "
        "business changes its probation policy. A sent letter has to record which version of "
        "each clause it used, because the letter that went out in March is the contract, not "
        "whatever the library says today."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Clause v2", "sub": ["approved Jan 2026"], "icon": "doc"},
      {"title": "Letter sent", "sub": ["records v2"], "icon": "email"},
      {"title": "Clause v3", "sub": ["approved Jun 2026"], "icon": "retry"},
      {"title": "The letter", "sub": ["still says v2"], "icon": "log"},
      {"title": "Answerable", "sub": ["what did we agree?"], "icon": "search"}],
    "title": "WHY CLAUSES CARRY VERSIONS",
    "note": "Without this, re-rendering an old offer would silently apply today's wording."}),
   "Why every clause carries a version and every sent letter records the ones it used. "
   "Re-rendering an old offer from today's library would produce a document that never existed.",
   "Why clause versions are recorded on every sent offer",
   "A horizontal row of five boxes. Clause version two: approved in January 2026. Letter sent: "
   "records version two. Clause version three: approved in June 2026. The letter: still says "
   "version two. Answerable: the question what did we agree can be answered exactly. A note "
   "says without this, re-rendering an old offer would silently apply today's wording."),
  ("h3", "Unused clauses"),
  ("p", "A clause nobody has used in a year is either obsolete or is quietly wrong in a way that "
        "makes people avoid it, and both are worth knowing. The system lists unused clauses once "
        "a year alongside the ones used most, which is a five-minute review that keeps the "
        "library from accumulating dead wording nobody dares delete."),
  ("p", "Next: what happens when a term has no clause at all."),
 ],
},
{
 "slug": "how-an-unusual-term-stops-the-draft",
 "title": "How an unusual term stops the draft",
 "nav": "How it stops",
 "read": 5, "words": 770,
 "desc": ("Why an unmatched term is a hard stop rather than a warning, what the request for a "
          "clause looks like, and how a new clause enters the library."),
 "og": ("An unmatched term produces no letter at all. The request that goes out asks for "
        "approved wording, and approving it once makes every future offer faster."),
 "abstract": ("Why an unmatched term is a hard stop rather than a warning, what the request for "
              "new wording looks like, and how an approved clause enters the library "
              "permanently."),
 "lede": ("This is the only hard stop in the whole series. Everywhere else, a system that cannot "
          "proceed flags something and carries on with what it can. Here it produces nothing at "
          "all, and the reason is that a partial offer letter is more dangerous than no offer "
          "letter."),
 "tags": ["offer letters", "employment contracts", "governance", "clause library", "compliance",
          "serverless"],
 "takeaways": [
  "An unmatched term produces no document at all, not a document with a gap in it.",
  "The request names the term, quotes what was agreed, and asks for wording.",
  "Approved wording enters the library as a versioned clause, so it is instant next time.",
  "The person who approves clauses is not the person who agrees offers, and that separation matters.",
  "Repeatedly requested clauses are the clearest signal that the library is out of date.",
 ],
 "blocks": [
  ("h2", "Why a hard stop"),
  ("p", "The soft option is to produce the letter with a placeholder: \"[relocation terms to be "
        "inserted]\". It seems helpful and it is how offer letters go out with square brackets "
        "in them, which happens more often than anybody admits and reads exactly as unserious as "
        "it sounds."),
  ("p", "The worse version is a letter that simply omits the unmatched term. The candidate "
        "agreed a relocation contribution in a conversation, the letter does not mention it, and "
        "nobody notices until they ask about it three months in. At that point the written "
        "contract does not include a term that was genuinely agreed, and unpicking that is "
        "expensive in a way no software saving justifies."),
  ("fig", ("chain", {
    "entry": {"title": "An unmatched term", "sub": ["no approved clause"], "icon": "alarm"},
    "steps": [
      {"title": "Stop the draft", "sub": ["produce nothing"], "icon": "stop"},
      {"title": "Tell the hiring manager", "sub": ["which term, and why"], "icon": "person"},
      {"title": "Ask for wording", "sub": ["from whoever approves"], "icon": "email",
       "side": {"title": "Clause owner", "sub": ["not the hiring manager"], "icon": "team"}},
      {"title": "Add to the library", "sub": ["versioned, dated"], "icon": "database"},
      {"title": "Draft resumes", "sub": ["automatically"], "icon": "check"}],
    "note": "Next time this term appears, none of these steps happen. That is the compounding bit."}),
   "What an unmatched term triggers. The value is in the last box: a clause approved once makes "
   "every subsequent offer with that term instant.",
   "What happens when a term has no approved clause",
   "A vertical chain of five steps entered by a box labelled An unmatched term, with no approved "
   "clause. Step one stops the draft and produces nothing. Step two tells the hiring manager "
   "which term and why. Step three asks for wording from whoever approves clauses, who is not "
   "the hiring manager. Step four adds the approved wording to the library, versioned and dated. "
   "Step five resumes the draft automatically. A note says next time this term appears none of "
   "these steps happen, which is the compounding bit."),
  ("h2", "What the request says"),
  ("callout", "Four lines to the clause owner", [
   "<strong>Line one.</strong> The term, as agreed. \"Relocation contribution of £2,000, payable "
   "after three months.\"",
   "<strong>Line two.</strong> Who agreed it and with whom, so there is context rather than an "
   "abstract request.",
   "<strong>Line three.</strong> The nearest existing clause, if there is one. \"Closest we have "
   "is the relocation clause used in 2024, which was a fixed sum payable on the start date.\"",
   "<strong>Line four.</strong> What is blocked. \"One offer is waiting on this &mdash; K. Osei, "
   "agreed today, start date 28 August.\"",
   "<strong>One box.</strong> Paste the wording. That is the whole interaction.",
  ]),
  ("p", "The third line does most of the work. Somebody being asked to write a clause from "
        "nothing will take a week; somebody being shown the closest existing clause and asked "
        "whether a variant is acceptable will usually reply the same day, because the task has "
        "become a comparison rather than a composition."),
  ("h2", "Who approves clauses"),
  ("p", "Deliberately not the hiring manager. The whole safety property of this system rests on "
        "the letter containing only approved wording, and if the person who agreed the terms can "
        "also approve the wording for them then approval means nothing."),
  ("p", "In a small business this is usually the owner or whoever holds the relationship with "
        "your employment solicitor. It does not have to be a formal role; it has to be a "
        "different person, and the system enforces that by refusing to accept a clause approved "
        "by the same address that submitted the terms."),
  ("h2", "Repeated requests are a signal"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Requested", "sub": ["4-day week, 3 times"], "icon": "counter"},
      {"title": "Approved each time", "sub": ["slightly differently"], "icon": "alarm"},
      {"title": "The signal", "sub": ["this is now standard"], "icon": "search"},
      {"title": "Add it properly", "sub": ["one approved option"], "icon": "check"},
      {"title": "Never asked again", "sub": ["and consistent"], "icon": "log"}],
    "title": "THE SAME REQUEST, THREE TIMES",
    "note": "Three ad-hoc approvals is three slightly different clauses in three contracts."}),
   "What a repeated clause request means. The second box is the real risk: ad-hoc approvals of "
   "the same thing produce inconsistent contracts.",
   "What it means when the same clause is requested repeatedly",
   "A horizontal row of five boxes. Requested: a four-day week clause, three times. Approved "
   "each time: slightly differently on each occasion. The signal: this arrangement is now "
   "standard. Add it properly: as one approved option. Never asked again: and consistent from "
   "then on. A note says three ad-hoc approvals is three slightly different clauses in three "
   "contracts."),
  ("p", "That inconsistency is the quiet cost of not having a library at all, and it is invisible "
        "until somebody compares two employees' contracts. Counting requests makes it visible "
        "the third time rather than the thirtieth."),
  ("p", "Next: what a sent offer leaves behind."),
 ],
},
{
 "slug": "how-a-sent-offer-is-recorded",
 "title": "How a sent offer is recorded",
 "nav": "How it is recorded",
 "read": 5, "words": 760,
 "desc": ("The document, the clause versions, the acceptance, and the handover to onboarding "
          "-- plus the one report that says whether the library is keeping up."),
 "og": ("A sent offer keeps the exact document, the clause versions it used, and the "
        "acceptance -- then hands the start date to onboarding without anybody retyping it."),
 "abstract": ("What a sent offer keeps, how acceptance is recorded, the handover to onboarding, "
              "and the one report that says whether the clause library is keeping up with the "
              "business."),
 "lede": ("An offer letter is a document that gets read back years later, usually at an "
          "inconvenient moment. What gets stored at the point of sending determines whether that "
          "reading is a two-minute lookup or an afternoon in an email archive."),
 "tags": ["offer letters", "record keeping", "onboarding", "reporting", "DynamoDB", "serverless"],
 "takeaways": [
  "The exact PDF is kept, not the ability to re-render it.",
  "The clause versions used are recorded, so the letter can be explained as well as produced.",
  "Acceptance is recorded as an event with a date, however it arrived.",
  "The start date and role hand straight to onboarding, with nobody retyping anything.",
  "One report matters: how often the library needed a new clause.",
 ],
 "blocks": [
  ("h2", "Keep the document, not the recipe"),
  ("p", "The tempting economy is to store the terms and the template versions and re-render the "
        "letter when needed. It saves a small amount of storage and it is wrong, because "
        "rendering is code and code changes: a formatting fix eighteen months from now would "
        "silently produce a document that differs from the one somebody signed."),
  ("p", "So the PDF as sent is stored, unmodified, and it is the record. The terms and clause "
        "versions are stored alongside it to explain it, not to reproduce it."),
  ("table", ["Kept", "Why"], [
   ["The PDF as sent", "It is the document. Nothing regenerates it."],
   ["The nine terms, versioned", "What was agreed, and what changed if it was renegotiated"],
   ["Clause ids and versions", "Lets somebody explain any sentence in the letter"],
   ["Who drafted and who sent", "Two different people, both recorded"],
   ["The covering email", "Offers are frequently qualified in the email body"],
   ["Acceptance, with a date", "However it arrived: a reply, a signature, a phone call logged"],
  ]),
  ("p", "The covering email is the one most systems forget, and it matters because a substantial "
        "proportion of offers are qualified in the body of the message rather than in the "
        "attachment &mdash; \"as discussed, we can review the rate at six months\". That "
        "sentence is part of what was communicated and it belongs with the letter."),
  ("h2", "Acceptance"),
  ("fig", ("chain", {
    "entry": {"title": "Offer sent", "sub": ["by a person"], "icon": "email"},
    "steps": [
      {"title": "Reply, signature, or call", "sub": ["three ways in"], "icon": "inbox",
       "exit": {"title": "Declined", "sub": ["recorded, with a reason if given"], "icon": "stop",
                "label": "no"}},
      {"title": "Record the acceptance", "sub": ["date and route"], "icon": "check",
       "side": {"title": "DynamoDB offers", "sub": ["immutable event"], "icon": "database"}},
      {"title": "Hand to onboarding", "sub": ["name, role, start date"], "icon": "link",
       "side": {"title": "Check chaser", "sub": ["from Day 86"], "icon": "team"}},
      {"title": "Nothing retyped", "sub": ["the same terms all the way"], "icon": "log"}],
    "note": "The handover is the point. Retyping a start date is where onboarding starts going wrong."}),
   "What happens when an offer is accepted. The handover to onboarding carries the same terms "
   "that were in the letter, which removes the most common source of a wrong start date.",
   "How an accepted offer is recorded and handed to onboarding",
   "A vertical chain of four steps entered by a box labelled Offer sent, by a person. Step one "
   "covers the three ways a response arrives: a reply, a signature, or a logged phone call; a "
   "decline exits to Declined, recorded with a reason if one was given. Step two records the "
   "acceptance with its date and route as an immutable event in a DynamoDB offers table. Step "
   "three hands the name, role and start date to onboarding, specifically to the background "
   "check chaser from Day 86. Step four notes that nothing is retyped and the same terms carry "
   "all the way through. A note says the handover is the point, because retyping a start date is "
   "where onboarding starts going wrong."),
  ("p", "That handover is worth more than it looks. The most common onboarding error in small "
        "businesses is a start date that differs between the offer letter, the HR record and the "
        "payroll setup, because it was typed three times. Passing it once removes the "
        "possibility."),
  ("h3", "Declines"),
  ("p", "Recorded, with a reason if the candidate volunteered one, and never chased. A declined "
        "offer is a complete outcome, and the only useful thing to do with it is count it: three "
        "declines on salary in a quarter is a market signal, and it is only visible if declines "
        "are recorded rather than deleted."),
  ("h2", "The report"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Offers", "sub": ["14 this quarter"], "icon": "doc"},
      {"title": "Median time", "sub": ["agreed to sent: 3h"], "icon": "clock"},
      {"title": "Accepted", "sub": ["11"], "icon": "check"},
      {"title": "New clauses", "sub": ["3 requested"], "icon": "alarm"},
      {"title": "Library age", "sub": ["oldest clause: 3 years"], "icon": "log"}],
    "title": "ONE QUARTER OF OFFERS",
    "note": "The fourth number says whether the library still describes how you hire."}),
   "A quarter of offers in five numbers. The clause-request count is the one that tells you "
   "something you did not already know.",
   "One quarter of offer letters summarised in five numbers",
   "A horizontal row of five boxes. Offers: fourteen this quarter. Median time: three hours from "
   "agreement to letter sent. Accepted: eleven. New clauses: three were requested. Library age: "
   "the oldest clause is three years old. A note says the fourth number tells you whether the "
   "library still describes how you hire."),
  ("p", "Three new clauses in fourteen offers means roughly one offer in five is doing something "
        "the library does not cover, which is high and usually means the business has started "
        "hiring differently &mdash; more part-time, more fixed-term, more flexible arrangements "
        "&mdash; without the paperwork catching up. That is a genuinely useful thing to learn "
        "from a document generator."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="offer",
 volumes=[(4, "4 offers"), (14, "14 offers"), (50, "50 offers")],
 read_each=0.0026, msgs_each=2.5,
 lede=("Offer volume is low even in a business that is growing quickly, and the model runs only "
       "on the note lane. Four offers a month is a healthy small business hiring steadily; fifty "
       "is a company several times larger than this design is aimed at. Here is where each cent "
       "goes."),
 takeaway_extra=("The model only runs on the note lane, so a team that uses the form pays "
                 "nothing for it at all."),
 risks=[
  "<strong>Storing renders rather than documents.</strong> Not a cost risk but the one worth "
  "repeating: re-rendering an old offer with today's code produces a document nobody signed.",
  "<strong>Re-reading a resent note.</strong> A forwarded email thread that grows with each "
  "reply will be re-read on every arrival unless the read is keyed on the confirmed terms rather "
  "than the message.",
  "<strong>Log retention left at never.</strong> At four offers a month the logs will be the "
  "entire bill within a year without a retention setting.",
 ],
 per_unit_note=("The messaging line is the largest variable cost here, because an offer involves "
                "several messages: the draft to the approver, the letter to the candidate, and "
                "any clause request. All of it is still fractions of a cent."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ol",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the document store, and the single narrow model call."),
 outside=[
  {"title": "Terms capture", "sub": ["form, or SES inbound"], "icon": "form"},
  {"title": "Clause library", "sub": ["S3, versioned"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["drafts, requests"], "icon": "email"}],
 inside=[
  {"title": "S3 + SQS", "sub": ["templates, sent PDFs,", "one draft queue"], "icon": "bucket"},
  {"title": "Lambda x3", "sub": ["capture, assemble,", "record"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["offers, clauses"], "icon": "database"}],
 note="us-east-1. One account. Sent documents are immutable and versioned in S3.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Terms capture, arriving through a form or "
  "through SES inbound as a forwarded note. The Clause library, stored versioned in S3. And SES "
  "outbound, carrying drafts and clause requests. Inside the account, three groups. S3 holding "
  "templates and sent PDFs, and SQS carrying one draft queue. Three Lambda functions named "
  "capture, assemble and record. And two DynamoDB tables named offers and clauses. A note gives "
  "the region as us-east-1, one account, and states that sent documents are immutable and "
  "versioned in S3."),
 functions=[
  ["<code>ol-capture</code>", "Function URL + S3 (SES)",
   "Nine fields from a form, or one Bedrock call on a note", "20s / 512&nbsp;MB"],
  ["<code>ol-assemble</code>", "SQS draft queue",
   "Clause matching, variable substitution, PDF and diff", "60s / 1024&nbsp;MB"],
  ["<code>ol-record</code>", "Function URL",
   "Stores the sent PDF, records acceptance, hands to onboarding", "20s / 512&nbsp;MB"]],
 roles=[
  ["<code>ol-capture-role</code>", "<code>bedrock:InvokeModel</code>, <code>sqs:SendMessage</code>",
   "One model arn; the draft queue"],
  ["<code>ol-assemble-role</code>",
   "<code>s3:GetObject</code>/<code>PutObject</code>, <code>dynamodb:GetItem</code>",
   "Templates and drafts prefixes; the clauses table, read"],
  ["<code>ol-record-role</code>",
   "<code>s3:PutObject</code>, <code>dynamodb:PutItem</code>, <code>ses:SendEmail</code>",
   "The sent prefix, write-once; the offers table; one identity"]],
 tables=[
  ("Table: offers",
   "PK   offer_id          S   ofr_2026_07_20_3c8e\n"
   "SK   version           S   v1 | v2\n"
   "     candidate         S   Kwame Osei\n"
   "     role              S   Field service engineer\n"
   "     basis             S   salaried | hourly | fixed_term\n"
   "     terms             M   the nine confirmed fields\n"
   "     clause_versions   L   [{clause_id, version}]\n"
   "     state             S   drafted | sent | accepted | declined | superseded\n"
   "     pdf_key           S   s3://offers-sent/ofr_.../v1.pdf   (write-once)\n"
   "     covering_email    S   s3 key of the message as sent\n"
   "     drafted_by        S   hiring manager\n"
   "     sent_by           S   whoever approves\n"
   "     accepted_at       S   with the route it arrived by\n\n"
   "Versions are appended. A renegotiated offer is v2 and v1 stays, because\n"
   "v1 is sitting in somebody's inbox whatever the database thinks."),
  ("Table: clauses",
   "PK   clause_id         S   probation-3-months\n"
   "SK   version           S   v2\n"
   "     body              S   the approved wording, with variable markers\n"
   "     variables         L   [name | number | date]\n"
   "     approved_by       S   not the person who submits terms\n"
   "     approved_at       S   2026-01-14\n"
   "     last_used         S   2026-07-20\n"
   "     use_count         N   41\n\n"
   "`last_used` drives the annual stale-clause review. A clause nobody has\n"
   "used in a year is either obsolete or quietly wrong.")],
 inbound=[
  "The <strong>terms form</strong> is static files in S3 behind CloudFront, reached through a "
  "signed link. Nine fields, no login.",
  "<strong>Forwarded notes</strong> arrive through an SES receipt rule writing to S3. The read "
  "produces the same nine fields and always routes to the same confirmation screen.",
  "<strong>Sent PDFs</strong> go to a bucket with object lock in governance mode. A sent offer "
  "is not something that should be quietly replaceable.",
  "<strong>Clause approval links</strong> are signed, scoped to one request, and refuse a "
  "submission from the same address that captured the terms."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "used only to turn a free-text note into the nine fields.",
  "<strong>It never writes wording.</strong> There is no code path in which model output reaches "
  "a document; its output populates a confirmation form.",
  "<strong>Output is a JSON schema</strong> with all nine fields nullable. Pay, start date and "
  "role are refused rather than inferred where the note does not state them.",
  "<strong>Grounded</strong> with the clause library's option lists, so probation and notice come "
  "back as one of your approved options or as null.",
  "<strong>Not called at all</strong> when the form lane was used, which is most of the time once "
  "people get used to it."],
 gotchas=[
  "Store the PDF as sent, with object lock. Re-rendering is the one shortcut here that produces "
  "a document nobody signed.",
  "Hold clause options rather than free values. It is more clauses to maintain and it makes an "
  "unapproved probation length impossible rather than merely unlikely.",
  "Keep the covering email. Offers are frequently qualified in the message body rather than the "
  "attachment.",
  "Refuse a clause approved by the person who submitted the terms. Without that separation the "
  "approval step is decorative.",
  "Hand the start date to onboarding rather than retyping it. Three copies of a date is where "
  "onboarding errors come from."],
))
