"""Day 85 -- 2026-07-18 -- Certification expiry tracker."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "certification-expiry-tracker"
NAME = "Certification expiry tracker"

SPEC = {
 "slug": SLUG, "date": "2026-07-18", "name": NAME,
 "tagline": ("Every ticket, licence and certificate your people hold gets read once, dated, "
             "and chased before it lapses -- so nobody turns up to a site on Monday unable to "
             "work."),
 "lede": ("A small system that holds the expiry date of every certificate, licence and ticket "
          "your staff need, reads new ones from a photograph, and starts chasing the right "
          "person at the right lead time for that kind of renewal. It cannot book a course and "
          "never claims somebody is qualified. Seven posts on the same system -- one diagram "
          "at a time -- with a cost breakdown and an engineering reference at the end."),
 "keywords": ["certifications", "compliance", "staff tickets", "expiry tracking", "field service",
              "serverless"],
 "icons": ["shield", "calendar", "team"],
 "faq": [
  ("What is a certification expiry tracker?",
   "A small serverless system that records every certificate, licence and ticket your staff "
   "hold, extracts the expiry date from a photograph of the card, and chases renewal at a lead "
   "time appropriate to that certification. It records what it was shown; it never asserts that "
   "somebody is qualified."),
  ("Why not just a spreadsheet with dates?",
   "A spreadsheet is exactly the right data model and it is the reminder side that fails. "
   "Nobody opens it on the right Tuesday, and a certificate that expires quietly is found out "
   "at a site gate. This adds the chasing, and the reading, to the spreadsheet you already "
   "should have."),
  ("Why different lead times?",
   "Because renewals take wildly different amounts of time. A first-aid certificate is a "
   "one-day course you can book next week; a medical for a vocational licence can take three "
   "months. A single thirty-day reminder is useless for one and premature for the other."),
  ("Does it prove somebody is qualified?",
   "No, and it says so. It records a photograph of a card and a date read from it. Verifying a "
   "certification against the awarding body is a different job with a different level of "
   "assurance, and pretending otherwise would be worse than not tracking at all."),
  ("What does it cost to run?",
   "A couple of dollars a month for a workforce of any size a small business has. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "certification-expiry-tracker-on-aws",
 "title": "A certification expiry tracker on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 900,
 "desc": ("Reads a photograph of a ticket, records the expiry, and chases the renewal at a "
          "lead time that fits that certification. AWS, about $2 a month."),
 "og": ("Every ticket read once from a photograph, dated, and chased at a lead time that fits "
        "how long that particular renewal actually takes."),
 "abstract": ("The whole system on one page -- a reader, a register and a chaser -- and the "
              "detail that makes it work: the lead time belongs to the certification, not to "
              "the calendar."),
 "lede": ("A qualification lapsing is one of the few small-business problems that is both "
          "entirely predictable and routinely disastrous. The date was known two years in "
          "advance. Nobody was watching it. On Monday somebody drives to a site, cannot get "
          "through the gate, and a day of work evaporates for a certificate that costs ninety "
          "pounds and takes a morning. This post walks through a small system whose whole job "
          "is to make that Monday impossible."),
 "tags": ["certifications", "compliance", "staff tickets", "expiry tracking", "field service",
          "serverless"],
 "takeaways": [
  "One action to register a ticket: photograph the card. The date is read from it.",
  "Lead times belong to the certification, not the calendar. Three months for some, three weeks for others.",
  "Chasing escalates: the holder, then their manager, then whoever schedules work.",
  "An expired ticket does not disappear. It stays visible and loud until it is replaced.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Card photo", "sub": ["taken by the holder"], "icon": "image"},
      {"title": "Certification list", "sub": ["types and lead times"], "icon": "doc"},
      {"title": "Holder + manager", "sub": ["chased in that order"], "icon": "team"}],
    "inside": [
      {"title": "Reader", "sub": ["type, holder,", "expiry, number"], "icon": "ocr"},
      {"title": "Register", "sub": ["one row per person", "per certification"], "icon": "database"},
      {"title": "Chaser", "sub": ["at the lead time", "for that type"], "icon": "calendar"}],
    "edges": [{"from": 0, "to": 0, "label": "photographs"},
              {"from": 1, "to": 1, "label": "lead times"},
              {"from": 2, "to": 2, "label": "renew this, by when", "up": True}],
    "note": "It records what it was shown. It never asserts that anyone is qualified."}),
   "Three things outside the account, three pieces inside it. The certification list is what "
   "makes the chasing sensible: it holds how long each kind of renewal actually takes.",
   "System: a card photograph in, a dated register, renewal chasing out",
   "Three boxes across the top sit outside the AWS account. On the left, Card photo: taken by "
   "the person who holds the certificate. In the middle, Certification list: the types of "
   "certification your business needs and the lead time each renewal requires. On the right, "
   "Holder and manager: the people chased, in that order. Each connects by an arrow to the AWS "
   "account container below. Photographs flow down into the account. The certification list "
   "feeds in lead times. A renewal request goes back out. Inside the AWS account are three "
   "components in a row. On the left, the Reader, which pulls the certification type, the "
   "holder, the expiry date and the certificate number from the photograph. In the middle, the "
   "Register, holding one row per person per certification. On the right, the Chaser, which "
   "starts at the lead time appropriate to that type. A note at the bottom says it records what "
   "it was shown and never asserts that anyone is qualified."),
  ("h3", "What you set up once (the outside)"),
  ("ul", [
   "<strong>A certification list.</strong> The kinds of ticket your business actually needs, "
   "each with the lead time its renewal takes and who at your end owns it. This is a short list "
   "&mdash; most businesses need eight to fifteen types &mdash; and getting the lead times "
   "roughly right is the single decision that determines whether the system works.",
   "<strong>A way to photograph a card.</strong> A link on a phone. Somebody starts, or renews, "
   "and takes a picture of the card. Covered in Part 2. No typing, because a system that asks a "
   "site electrician to type a fourteen-digit registration number will contain about half the "
   "certificates it should.",
   "<strong>A staff list with managers.</strong> Who holds what, and who to escalate to. Most "
   "businesses have this; the system reads it rather than owning it.",
  ]),
  ("h3", "What runs on every ticket (the inside)"),
  ("ul", [
   "<strong>The reader.</strong> Pulls four things off a photograph of a card: the type, the "
   "holder's name, the expiry date and the certificate number. Cards are wildly inconsistent "
   "&mdash; different awarding bodies, different layouts, dates in three formats &mdash; so the "
   "type is matched against your list rather than read freely, and an unreadable expiry is a "
   "question rather than a guess.",
   "<strong>The register.</strong> One row per person per certification, holding the current "
   "card, its expiry, its number and the photograph. A renewal replaces the row's dates and "
   "keeps the old card in the history, because \"was this person certified on the 14th of "
   "March\" is a question that gets asked after an incident.",
   "<strong>The chaser.</strong> Works backwards from the expiry by the lead time for that "
   "type, then escalates on a schedule. Most of the design is here, because the difficulty is "
   "not knowing the date &mdash; it is getting somebody to act far enough ahead.",
  ]),
  ("h2", "One certificate, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Photographed", "sub": ["by the holder"], "icon": "image"},
      {"title": "Read", "sub": ["type, name, expiry"], "icon": "ocr"},
      {"title": "Registered", "sub": ["one row, dated"], "icon": "database"},
      {"title": "Chased", "sub": ["at the right lead time"], "icon": "calendar"},
      {"title": "Replaced", "sub": ["new card, old kept"], "icon": "check"}],
    "title": "ONE CERTIFICATE, END TO END",
    "note": "The fourth stage may be a year and a half after the third. That is the point."}),
   "The same system as one line. The gap between registering a card and chasing it is often "
   "years, which is exactly why a human process fails at it.",
   "One certificate from photograph to renewal, in five stages",
   "A horizontal row of five boxes joined by arrows. Photographed: by the person who holds it. "
   "Read: the type, name and expiry are extracted. Registered: one dated row. Chased: starting "
   "at the lead time for that type. Replaced: a new card is registered and the old one is kept. "
   "A note says the fourth stage may be a year and a half after the third, and that this is the "
   "point."),
  ("h2", "In plain words"),
  ("p", "A new site operative joins in March 2025. On his first morning he photographs three "
        "cards: a CSCS-style site card expiring May 2027, a first-aid certificate expiring "
        "September 2026, and an abrasive wheels ticket expiring March 2028. The reader gets "
        "all three, matches each type against your list, and writes three register rows. Total "
        "elapsed effort: about forty seconds, on his first morning, when he has the cards in "
        "his wallet anyway."),
  ("p", "Eighteen months pass. In June 2026 the chaser looks at the first-aid certificate, "
        "which expires in September and whose lead time is set at ninety days because getting "
        "onto a course near you takes a while. It messages him: first aid expires 12 September, "
        "here is what you need, please book it. He does not reply. Two weeks later it messages "
        "his supervisor as well. The course happens in August, he photographs the new card, and "
        "the register updates. The alternative version of this story ends with him being turned "
        "away from a site in September and a day of work lost, and the only difference between "
        "the two is that somebody was watching a date."),
  ("callout", "Design rules that shaped every decision", [
   "The lead time belongs to the certification. A medical takes months and a toolbox talk takes "
   "a week, and one reminder schedule cannot serve both.",
   "One action to register: photograph the card. Any typing at all and the register will be "
   "incomplete, which is worse than not having one.",
   "It records; it does not verify. A photograph of a card is evidence of a card, not proof of "
   "a qualification, and the system says so.",
   "An expired ticket stays visible. It does not archive itself, go grey, or drop off a list.",
   "Escalate to a person, never to a group. A message to a team address is a message to nobody.",
   "Keep the old card. \"Were they certified on the day of the incident\" is the question that "
   "eventually gets asked.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Every business with certified staff already knows the dates. They are in a "
        "spreadsheet, or in a folder of scans, or in the HR system. The data is not the problem. "
        "The problem is that acting on a date eighteen months out requires somebody to open the "
        "spreadsheet on the correct Tuesday, and nobody does that, and the failure is silent "
        "until a gate."),
  ("p", "So the design puts nearly all of its weight on the chasing and the lead times, and "
        "almost none on the register, which is a table anybody could build. Reading the card "
        "from a photograph exists purely to make registration cheap enough that the register is "
        "actually complete &mdash; because a tracker that knows about eleven of your fourteen "
        "certifications gives you confidence about the three it will not save you from."),
  ("p", "The next four posts walk through each piece: how a card gets read, how the register "
        "handles renewals and history, how the chasing escalates, and what the compliance view "
        "shows. One diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-certificate-gets-read",
 "title": "How a certificate gets read",
 "nav": "How it is read",
 "read": 5, "words": 820,
 "desc": ("Reading a laminated card photographed at arm's length, why the type is matched "
          "rather than read, and the three date formats that cause every error."),
 "og": ("Cards vary by awarding body and dates appear in three formats. Matching the type "
        "against your own list and refusing to guess a date is what makes the read safe."),
 "abstract": ("Reading a laminated card photographed at arm's length, why the certification "
              "type is matched rather than read freely, and the date ambiguity that causes "
              "almost every error."),
 "lede": ("A certification card is a small laminated rectangle with a logo, a name, a number "
          "and one or two dates on it, photographed at an angle with a flash reflecting off the "
          "lamination. It is a much easier document than a till receipt and it has one nasty "
          "trap in it, which is that the most important field is a date and dates are "
          "ambiguous."),
 "tags": ["certifications", "Amazon Textract", "OCR", "date parsing", "compliance", "serverless"],
 "takeaways": [
  "The certification type is matched against your list, never read freely off the card.",
  "A card with two dates needs both: issued and expires, and telling them apart matters.",
  "An ambiguous date is a question with the crop attached, never a best guess.",
  "The holder's name is matched to the staff list, so a mistyped name cannot create a person.",
  "Both sides of the card are captured, because the expiry is often on the back.",
 ],
 "blocks": [
  ("h2", "What comes off a card"),
  ("pre", "type          first-aid-at-work     matched to your list, not read freely\n"
          "holder        matched to staff list, or a question\n"
          "number        as printed, kept verbatim\n"
          "issued        2023-09-12\n"
          "expires       2026-09-12            the field everything depends on\n"
          "awarding_body as printed, for the record\n"
          "confidence    per field, 0.0-1.0"),
  ("h2", "The read"),
  ("fig", ("chain", {
    "entry": {"title": "Card photographed", "sub": ["front, then back"], "icon": "image"},
    "steps": [
      {"title": "Both sides captured?", "sub": ["expiry is often on the back"], "icon": "branch",
       "exit": {"title": "Ask for the back", "sub": ["one more tap"], "icon": "phone",
                "label": "one side"}},
      {"title": "Pull the text", "sub": ["Textract"], "icon": "ocr"},
      {"title": "Which certification?", "sub": ["match to your list"], "icon": "model",
       "side": {"title": "Certification list", "sub": ["types and aliases"], "icon": "doc"},
       "exit": {"title": "Ask which type", "sub": ["short pick list"], "icon": "person",
                "label": "no match"}},
      {"title": "Date unambiguous?", "sub": ["format, and which is which"], "icon": "branch",
       "exit": {"title": "Ask about the date", "sub": ["show the crop"], "icon": "person",
                "label": "unclear"}},
      {"title": "Write the register row", "sub": ["with the photographs"], "icon": "database"}],
    "note": "Two questions are possible and both are one tap. Neither is a guess."}),
   "One card, end to end. The two exits are the only places a person is involved, and both take "
   "one tap because the person is holding the card.",
   "How a photographed certification card becomes a register row",
   "A vertical chain of five steps inside the AWS account, entered by a box labelled Card "
   "photographed, front then back. Step one asks whether both sides were captured, since the "
   "expiry is often on the back; a single side exits to Ask for the back, one more tap. Step two "
   "pulls the text with Amazon Textract. Step three asks which certification it is, matching "
   "against the certification list with its aliases; no match exits to Ask which type with a "
   "short pick list. Step four asks whether the date is unambiguous, both in format and in which "
   "date is which; unclear exits to Ask about the date with the crop shown. Step five writes the "
   "register row with the photographs attached. A note says two questions are possible, both are "
   "one tap, and neither is a guess."),
  ("h3", "Matching the type rather than reading it"),
  ("p", "The same qualification is printed a dozen ways by different awarding bodies, and the "
        "card frequently names a scheme rather than a skill. Asking a model to read a "
        "certification type off a card produces a free-text string, and free-text strings do not "
        "group, which means your register ends up with nine spellings of the same ticket and no "
        "way to answer \"who has first aid\"."),
  ("p", "So the certification list carries aliases, and the model's job is to pick one of your "
        "types or none. A card that matches nothing is a question with a short pick list, and "
        "the answer adds an alias &mdash; so the second person with that card is read "
        "automatically."),
  ("h3", "The date problem"),
  ("ul", [
   "<strong>Format ambiguity.</strong> 09/12/2026 is September or December depending on which "
   "side of the Atlantic printed it. Where the day is above twelve there is no ambiguity; where "
   "it is not, the answer comes from the awarding body's convention if the list knows it, and "
   "from a question if it does not.",
   "<strong>Which date is which.</strong> Most cards carry two. Usually the later one is the "
   "expiry, and usually is not good enough &mdash; some cards show a training date and a "
   "much later review date that is not an expiry at all. Labels are read where they exist.",
   "<strong>Cards with no expiry.</strong> Some qualifications do not expire, and their register "
   "rows carry no date and are never chased. Recording that explicitly is much better than an "
   "empty field that looks like a failed read.",
   "<strong>Month-only expiry.</strong> Plenty of cards show 09/2026 and expire at the end of "
   "that month. Treating that as the first of the month costs somebody a month of validity, so "
   "it resolves to the last day.",
  ]),
  ("h2", "Names"),
  ("p", "The holder's name is matched against your staff list rather than taken from the card, "
        "for the same reason the type is: a free-text name creates duplicate people. \"J Reed\", "
        "\"John Reed\" and \"Jonathan Reed\" are one person, and a register that thinks they are "
        "three cannot answer any question correctly."),
  ("p", "A card whose name matches nobody on the staff list is not registered against a guess. "
        "It becomes a question to whoever uploaded it, which is usually resolved instantly "
        "&mdash; it is normally either a new starter not yet on the list, or a card belonging to "
        "somebody else that was photographed by mistake, and both of those are worth catching."),
  ("callout", "What the reader will not do", [
   "It will not create a certification type. An unmatched card is a question, and the answer "
   "adds an alias to a type you already recognise.",
   "It will not create a person. A name that matches nobody is a question, because the "
   "alternative is a register full of ghosts.",
   "It will not guess an ambiguous date. A wrong expiry is worse than no expiry: it produces "
   "confidence rather than a gap.",
   "It will not read a card as valid. It reads a card as saying something; whether the "
   "qualification is live with the awarding body is a separate question the system does not "
   "answer.",
  ]),
  ("p", "Next: how the register handles renewals, history and the question that gets asked after "
        "an incident."),
 ],
},
{
 "slug": "how-the-certification-register-holds-history",
 "title": "How the certification register holds history",
 "nav": "How history is held",
 "read": 5, "words": 800,
 "desc": ("A renewal is a new card, not an edit -- and why \"were they certified on the 14th of "
          "March\" is the question the register is really built to answer."),
 "og": ("A renewal appends rather than overwrites, because the question that eventually gets "
        "asked is not who is certified now but who was certified on a particular day."),
 "abstract": ("Why a renewal appends rather than overwrites, how a gap between cards is "
              "recorded honestly, and the after-the-fact question the register is really built "
              "to answer."),
 "lede": ("A certification register looks like a table of who currently holds what, and if you "
          "build it that way you will have built the wrong thing. The question that eventually "
          "gets asked, sometimes by somebody with a clipboard and sometimes by a solicitor, is "
          "not who is certified today. It is who was certified on a specific day eighteen "
          "months ago."),
 "tags": ["certifications", "audit trail", "DynamoDB", "compliance", "record keeping",
          "serverless"],
 "takeaways": [
  "A renewal appends a card; it never overwrites the previous one.",
  "The current state is derived from the cards, so it cannot disagree with the history.",
  "A gap between an expiry and the next card is recorded as a gap, not smoothed over.",
  "The photograph is kept with each card, because a date without its evidence is an assertion.",
  "\"Who was certified on this date\" is a single query, which is the point of the shape.",
 ],
 "blocks": [
  ("h2", "Cards, not rows"),
  ("fig", ("chain", {
    "entry": {"title": "A new card", "sub": ["read and matched"], "icon": "image"},
    "steps": [
      {"title": "Append the card", "sub": ["person + type + issued"], "icon": "log",
       "side": {"title": "DynamoDB cards", "sub": ["append-only"], "icon": "database"}},
      {"title": "Overlaps the previous?", "sub": ["issued before it expired"], "icon": "branch",
       "exit": {"title": "Clean renewal", "sub": ["no gap"], "icon": "check", "label": "yes"}},
      {"title": "Record the gap", "sub": ["dates, and how long"], "icon": "alarm"},
      {"title": "Recompute current", "sub": ["from the cards"], "icon": "counter"}],
    "note": "The gap is a fact about the past. Overwriting it would delete the only record of it."}),
   "How a renewal is recorded. The gap between an expired card and its replacement is a real "
   "fact that a state-based register silently erases.",
   "How a renewed certification card is recorded",
   "A vertical chain of four steps entered by a box labelled A new card, read and matched. Step "
   "one appends the card to an append-only DynamoDB cards table, keyed on person, type and "
   "issue date. Step two asks whether it overlaps the previous card, meaning it was issued "
   "before the old one expired; if so it exits to Clean renewal, with no gap. Step three records "
   "the gap, with its dates and length. Step four recomputes the current state from the cards. A "
   "note says the gap is a fact about the past and overwriting it would delete the only record "
   "of it."),
  ("h3", "Why the current state is derived"),
  ("p", "The register stores cards and computes \"currently valid\" from them, rather than "
        "storing a status that gets updated. That means the two can never disagree, which is the "
        "usual failure of a status column: something goes wrong in one code path, the status "
        "says valid, the cards say expired, and the status is what the dashboard shows."),
  ("p", "Recomputation is cheap here. A person holds perhaps a dozen certifications with a "
        "handful of cards each, so \"what does this person currently hold\" is a query over "
        "maybe forty items."),
  ("h2", "Gaps"),
  ("p", "A gap between one card expiring and the next being issued is common, usually short, and "
        "usually nobody's fault &mdash; a course was full, a card took three weeks to arrive. It "
        "is also the single most important thing the register can tell you afterwards, and a "
        "state-based register erases it completely."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Card A", "sub": ["expires 12 Sep"], "icon": "shield"},
      {"title": "Gap", "sub": ["19 days"], "icon": "alarm"},
      {"title": "Card B", "sub": ["issued 1 Oct"], "icon": "shield"},
      {"title": "Recorded", "sub": ["as a gap, permanently"], "icon": "log"},
      {"title": "Answerable", "sub": ["'on 20 Sep?' -- no"], "icon": "search"}],
    "title": "A GAP IS A FACT, NOT A GLITCH",
    "note": "A register that overwrote card A could not answer the last box at all."}),
   "What a gap looks like in the register. The last box is the whole reason for the append-only "
   "shape.",
   "How a gap between two certification cards is recorded",
   "A horizontal row of five boxes. Card A: expires the twelfth of September. Gap: nineteen "
   "days. Card B: issued the first of October. Recorded: the gap is stored permanently. "
   "Answerable: the question was this person certified on the twentieth of September has the "
   "answer no. A note says a register that overwrote card A could not answer the last box at "
   "all."),
  ("h3", "What a gap does and does not trigger"),
  ("p", "A gap that has already happened does not generate an alert, because alerting somebody "
        "about a situation that resolved three weeks ago is noise. It is recorded, it appears in "
        "the compliance view as a historical gap, and it feeds one useful statistic: how often "
        "renewals are late, which is the measure of whether the lead times in your certification "
        "list are set correctly."),
  ("p", "A gap that is happening right now is a different matter entirely, and it is the "
        "loudest thing the system does. Part 4 covers it."),
  ("h2", "The photograph"),
  ("p", "Every card keeps its photograph, and this matters more than it looks. An expiry date in "
        "a table is an assertion by whoever typed it; an expiry date next to a photograph of the "
        "card it was read from is evidence. When somebody asks to see proof of certification "
        "&mdash; a client, an auditor, an insurer &mdash; the answer is the card, not the "
        "spreadsheet."),
  ("callout", "The card row", [
   "<strong>Person and type</strong>, both matched to your own lists, never free text.",
   "<strong>Issued and expires</strong>, with the expiry nullable for qualifications that do "
   "not expire.",
   "<strong>Number and awarding body</strong>, verbatim as printed.",
   "<strong>The photographs</strong>, front and back, unmodified.",
   "<strong>Who registered it and when</strong>, which is usually the holder on their phone.",
   "<strong>Never deleted.</strong> A card registered in error is superseded by a correction "
   "row, and both stay.",
  ]),
  ("p", "Next: the chasing, which is where the lead times earn their keep."),
 ],
},
{
 "slug": "how-a-renewal-gets-chased",
 "title": "How a renewal gets chased",
 "nav": "How it is chased",
 "read": 6, "words": 850,
 "desc": ("Working backwards from the expiry by a lead time that fits the certification, the "
          "escalation ladder, and what happens on the day a ticket actually lapses."),
 "og": ("A ninety-day lead time for a course that is hard to book and twenty-one days for one "
        "that is not. The escalation ladder, and the one thing that happens on expiry day."),
 "abstract": ("Working backwards from the expiry by a lead time that fits the certification, "
              "the four-step escalation ladder, and what happens on the day a ticket actually "
              "lapses."),
 "lede": ("Everything else in this system is bookkeeping. This is the part that prevents the "
          "Monday at the gate, and it rests almost entirely on one number per certification "
          "type: how long the renewal actually takes to arrange."),
 "tags": ["certifications", "reminders", "escalation", "compliance", "Amazon SES", "serverless"],
 "takeaways": [
  "The lead time is a property of the certification, and setting it right is most of the work.",
  "Four steps: the holder, the holder again, the manager, and whoever schedules the work.",
  "A booked course pauses the chasing; it does not stop it.",
  "On expiry day the person is marked as not currently holding it, loudly and visibly.",
  "An expired ticket keeps chasing forever. It never times out and never goes quiet.",
 ],
 "blocks": [
  ("h2", "Lead time, not a fixed reminder"),
  ("table", ["Certification", "Typical lead time", "Why"], [
   ["Vocational medical", "120 days", "Appointment availability, then processing"],
   ["Site safety card", "90 days", "Test centre availability plus card delivery"],
   ["First aid at work", "90 days", "Course dates near you are sparse"],
   ["Abrasive wheels", "30 days", "Half-day course, widely available"],
   ["Manual handling", "21 days", "Often delivered in house"],
   ["Insurance-mandated refresher", "60 days", "Certificate must be with the insurer before renewal"],
  ]),
  ("p", "Those numbers are the whole system. A thirty-day reminder on a certification with a "
        "hundred-and-twenty-day lead time is a reminder that arrives ninety days too late to "
        "help, and a ninety-day reminder on a half-day course is one that gets ignored and then "
        "forgotten. Neither of those is fixed by better message wording."),
  ("h2", "The ladder"),
  ("fig", ("chain", {
    "entry": {"title": "Expiry minus lead time", "sub": ["per certification"], "icon": "calendar"},
    "steps": [
      {"title": "Tell the holder", "sub": ["what, when, how to book"], "icon": "person",
       "exit": {"title": "Booked", "sub": ["pause until the date"], "icon": "check",
                "label": "replies"}},
      {"title": "Still nothing?", "sub": ["after 14 days"], "icon": "branch",
       "exit": {"title": "Tell them again", "sub": ["shorter, with the date"], "icon": "bell",
                "label": "yes"}},
      {"title": "Still nothing?", "sub": ["at half the lead time"], "icon": "branch",
       "side": {"title": "Their manager", "sub": ["from the staff list"], "icon": "team"},
       "exit": {"title": "Tell the manager", "sub": ["holder copied in"], "icon": "email",
                "label": "yes"}},
      {"title": "Still nothing?", "sub": ["at 14 days out"], "icon": "branch",
       "side": {"title": "Whoever schedules", "sub": ["work planning"], "icon": "calendar"},
       "exit": {"title": "Tell scheduling", "sub": ["so work can move"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Expiry day", "sub": ["marked not current,", "visibly"], "icon": "stop"}],
    "note": "The fourth step is the one that saves the day: work gets rescheduled before the gate."}),
   "The escalation ladder, keyed off the lead time rather than the calendar. The step that "
   "actually prevents lost work is the fourth, because it reaches somebody who can move a job.",
   "The four-step escalation for an approaching certification expiry",
   "A vertical chain of five steps entered by a box labelled Expiry minus lead time, computed "
   "per certification. Step one tells the holder what is expiring, when, and how to book; a "
   "reply that it is booked exits to Booked, which pauses until the course date. Step two asks "
   "whether there has still been nothing after fourteen days, exiting to Tell them again, "
   "shorter and with the date. Step three asks again at half the lead time, pulling the "
   "holder's manager from the staff list and exiting to Tell the manager with the holder copied "
   "in. Step four asks again at fourteen days out, pulling whoever does work planning and "
   "exiting to Tell scheduling so that work can be moved. Step five is Expiry day, where the "
   "person is marked as not current, visibly. A note says the fourth step is the one that saves "
   "the day, because work gets rescheduled before the gate."),
  ("h3", "Booking pauses rather than stops"),
  ("p", "\"I've booked it for the 14th\" is the answer everybody wants, and it is not the end of "
        "the story. Courses get cancelled, people miss them, and cards take weeks to arrive "
        "afterwards. So a booking records a date and suppresses chasing until a few days after "
        "it, at which point the system asks a single question: did it happen, and do you have "
        "the card?"),
  ("p", "If the answer is yes, a photograph closes it. If there is no answer, the ladder resumes "
        "from wherever it had reached, which is usually quite far along by then. The failure "
        "mode this prevents is the one that catches most businesses: a booking is treated as a "
        "resolution, everybody relaxes, and the card never arrives."),
  ("h2", "Expiry day"),
  ("p", "On the day, the person is marked as not currently holding that certification. Not "
        "expired-soon, not amber &mdash; not holding it. That distinction is the point of the "
        "whole system, because the alternative language lets people keep working on the "
        "assumption that a certificate is basically fine."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Marked not current", "sub": ["on the day, at 00:01"], "icon": "stop"},
      {"title": "Holder told", "sub": ["plainly"], "icon": "person"},
      {"title": "Manager told", "sub": ["and scheduling"], "icon": "team"},
      {"title": "Stays visible", "sub": ["no archiving, no grey"], "icon": "alarm"},
      {"title": "Chases forever", "sub": ["weekly until replaced"], "icon": "retry"}],
    "title": "WHAT HAPPENS ON EXPIRY DAY",
    "note": "Nothing here times out. A lapsed ticket is louder next month than it is today."}),
   "Expiry day, and afterwards. The unusual property is that the chasing never stops: a lapsed "
   "certification is the one thing in this series with no expiry on its own alert.",
   "What happens on the day a certification expires",
   "A horizontal row of five boxes. Marked not current: on the day, at one minute past midnight. "
   "Holder told: plainly. Manager told: and whoever schedules work. Stays visible: no archiving "
   "and no greying out. Chases forever: weekly until it is replaced. A note says nothing here "
   "times out and a lapsed ticket is louder next month than it is today."),
  ("p", "The forever part is deliberate and is the opposite of how most alerting works. Every "
        "other reminder in this series eventually escalates and then rests. A lapsed "
        "certification does not, because the situation it describes does not improve with time "
        "&mdash; it gets worse, and a system that goes quiet about it after a fortnight is "
        "actively misleading."),
  ("callout", "Getting the lead times right", [
   "Start from how long the renewal took last time. The register knows: it has the gap "
   "statistics from Part 3.",
   "Add the card delivery time, not just the course. A ticket that arrives three weeks after "
   "the assessment needs three weeks more lead.",
   "Ask the person who books them. They know which courses are hard to get near you, and that "
   "knowledge is not written anywhere.",
   "Revise annually. A lead time that produced two late renewals last year is too short, and "
   "the fix is a number in a sheet.",
  ]),
  ("p", "Next: the compliance view, and the one question it is built to answer quickly."),
 ],
},
{
 "slug": "how-the-compliance-view-answers",
 "title": "How the compliance view answers",
 "nav": "How it answers",
 "read": 5, "words": 790,
 "desc": ("Two questions a compliance view has to answer fast -- can this crew do this job, and "
          "who was certified on this date -- and what it deliberately does not claim."),
 "og": ("Two questions, asked in very different circumstances: can this crew do this job today, "
        "and who was certified on a specific day. Both are one query if the register is shaped "
        "right."),
 "abstract": ("The two questions a compliance view has to answer fast, the honesty line it does "
              "not cross, and the one statistic that says whether the lead times are set "
              "right."),
 "lede": ("A certification register gets read in two very different circumstances. One is "
          "planning a job on a Thursday afternoon. The other is an investigation. They want "
          "different things, and a view built for the first is nearly useless for the second."),
 "tags": ["certifications", "compliance", "reporting", "audit", "field service", "serverless"],
 "takeaways": [
  "Question one: can this crew do this job today? Answered as a list of who is missing what.",
  "Question two: who was certified on this date? Answered from the cards, not from status.",
  "The view never says somebody is qualified. It says what card it was shown and when.",
  "Historical gaps are visible, because hiding them is how a register becomes untrustworthy.",
  "One statistic matters: how many renewals were late. It tells you whether the lead times fit.",
 ],
 "blocks": [
  ("h2", "Question one: can this crew do this job"),
  ("p", "Asked on a Thursday, about next Tuesday, by somebody planning work. The useful answer "
        "is not a list of everybody's certifications; it is the short list of what is missing."),
  ("fig", ("chain", {
    "entry": {"title": "A job", "sub": ["date, site, crew"], "icon": "calendar"},
    "steps": [
      {"title": "What does it need?", "sub": ["from the job type"], "icon": "doc",
       "side": {"title": "Job requirements", "sub": ["a short list per type"], "icon": "chart"}},
      {"title": "Who is on it?", "sub": ["the crew for that day"], "icon": "team"},
      {"title": "Valid on that date?", "sub": ["not today -- that date"], "icon": "branch",
       "side": {"title": "The cards", "sub": ["issued and expires"], "icon": "database"}},
      {"title": "The missing list", "sub": ["who, what, expires when"], "icon": "alarm"}],
    "note": "Checked against the job date, not today. A ticket expiring Monday fails a Tuesday job."}),
   "How a crew is checked against a job. The date the check runs against is the job date, which "
   "sounds obvious and is the thing most implementations get wrong.",
   "How a crew is checked against a job's certification requirements",
   "A vertical chain of four steps entered by a box labelled A job, carrying a date, a site and "
   "a crew. Step one asks what the job needs, taken from the job type against a short list of "
   "requirements per type. Step two asks who is on it, meaning the crew assigned for that day. "
   "Step three asks whether each required certification is valid on that date rather than today, "
   "checking the cards for their issue and expiry dates. Step four produces the missing list, "
   "naming who, what and when it expires. A note says the check runs against the job date rather "
   "than today, because a ticket expiring Monday fails a Tuesday job."),
  ("p", "Checking against the job date rather than today is the single most common bug in "
        "systems like this, and it fails in exactly the direction that hurts: a card that is "
        "valid on Thursday when you check and expires on Monday shows green, and the job is on "
        "Tuesday."),
  ("h2", "Question two: who was certified on this date"),
  ("p", "Asked in a very different room, usually after something has gone wrong, and the answer "
        "has to come from the cards rather than from any current-status field. The register's "
        "append-only shape from Part 3 is what makes this a single query rather than an "
        "archaeology project."),
  ("p", "The answer format matters too. It is not \"yes\" or \"no\" &mdash; it is the card: type, "
        "number, awarding body, issued and expiry dates, and the photograph. That is what the "
        "person asking actually wants, and providing a bare yes would require them to ask a "
        "second question anyway."),
  ("h2", "The honesty line"),
  ("callout", "What the view says, and does not", [
   "<strong>It says:</strong> \"On 14 March 2026, we held a photograph of a first aid at work "
   "card for J. Reed, number 4471-882, issued 12 September 2023, expiring 12 September 2026.\"",
   "<strong>It does not say:</strong> \"J. Reed was qualified in first aid on 14 March 2026.\"",
   "<strong>Why the difference matters:</strong> a card can be revoked, suspended, or forged, "
   "and none of those are visible in a photograph. The system's assurance level is exactly "
   "\"we were shown this\", and stating more than that is a claim you cannot support.",
   "<strong>Where more is needed,</strong> the awarding body's own register is the answer, and "
   "the card number in this register is what you look up. The system's job is to make sure you "
   "know the number and the date.",
  ]),
  ("h2", "The one statistic"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Tracked", "sub": ["61 certifications"], "icon": "shield"},
      {"title": "Current", "sub": ["59"], "icon": "check"},
      {"title": "In chase", "sub": ["7"], "icon": "bell"},
      {"title": "Lapsed", "sub": ["2"], "icon": "alarm"},
      {"title": "Late last year", "sub": ["5 of 24 renewals"], "icon": "counter"}],
    "title": "THE COMPLIANCE VIEW, IN FIVE NUMBERS",
    "note": "The last number is about your lead times, not about your people."}),
   "The compliance view in five numbers. The last one is the only one that tells you to change "
   "something about the system rather than about a person.",
   "A certification register summarised in five numbers",
   "A horizontal row of five boxes. Tracked: sixty-one certifications. Current: fifty-nine. In "
   "chase: seven approaching expiry. Lapsed: two. Late last year: five of twenty-four renewals "
   "were late. A note says the last number is about your lead times rather than about your "
   "people."),
  ("p", "Five late renewals out of twenty-four means roughly one lead time in five is set too "
        "short, and the register can name which certifications they were. Fixing that is an edit "
        "to a sheet and it removes a category of problem permanently, which is a better return "
        "than any amount of reminding people harder."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="card",
 volumes=[(20, "20 cards"), (60, "60 cards"), (200, "200 cards")],
 read_each=0.0031, msgs_each=1.6,
 extra=[("ocr", "Textract &mdash; both sides of each card", "#8C4FFF", 0.0026, 0.0)],
 lede=("Card registration is bursty and rare: a workforce of thirty registers most of its "
       "certifications in the first fortnight and then perhaps two or three a month forever "
       "after. The ongoing cost is almost entirely the chasing, which is email. Here is where "
       "each cent goes."),
 takeaway_extra=("Registration is a one-off burst. After the first month the only recurring "
                 "cost is the chasing, which is email."),
 risks=[
  "<strong>Re-reading on every retry.</strong> A card photographed in poor light may fail and be "
  "redelivered; keying the read cache on the image digest means a retry is free.",
  "<strong>Chasing a lapsed ticket weekly, forever, by SMS.</strong> Email is free at these "
  "volumes and SMS is not. A ticket that has been lapsed for eight months and is chased weekly "
  "by text is a small but permanent bill for no additional effect.",
  "<strong>Log retention left at never.</strong> This system does very little most days and "
  "will otherwise be almost entirely a CloudWatch bill within a year.",
 ],
 per_unit_note=("Textract runs on both sides of each card, which is why it is the largest "
                "per-card line. It is still under a cent, and it only happens once per card "
                "rather than once per reminder."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ce",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the schedule, and the one model call."),
 outside=[
  {"title": "Capture page", "sub": ["CloudFront + S3"], "icon": "phone"},
  {"title": "Staff + cert lists", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["chases, escalations"], "icon": "email"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["card photos,", "daily sweep"], "icon": "bucket"},
  {"title": "Lambda x3", "sub": ["read, chase, view"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["cards, chases"], "icon": "database"}],
 note="us-east-1. One account. No integration with any awarding body's register.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The Capture page, served as static files "
  "from S3 behind CloudFront. The Staff and certification lists, read through the Google Sheets "
  "API read-only. And SES outbound, carrying the chases and escalations. Inside the account, "
  "three groups. S3 holding card photographs and EventBridge carrying a daily sweep. Three "
  "Lambda functions named read, chase and view. And two DynamoDB tables named cards and chases. "
  "A note gives the region as us-east-1, one account, and states there is no integration with "
  "any awarding body's register."),
 functions=[
  ["<code>ce-read</code>", "S3 ObjectCreated",
   "Textract on both sides, then one Bedrock call; writes the card", "60s / 1024&nbsp;MB"],
  ["<code>ce-chase</code>", "EventBridge daily",
   "Walks the ladder for every card in its lead-time window", "60s / 512&nbsp;MB"],
  ["<code>ce-view</code>", "Function URL",
   "Crew-against-job checks and the point-in-time query", "15s / 512&nbsp;MB"]],
 roles=[
  ["<code>ce-read-role</code>",
   "<code>textract:AnalyzeDocument</code>, <code>bedrock:InvokeModel</code>, "
   "<code>dynamodb:PutItem</code>",
   "The photos prefix; one model arn; the cards table"],
  ["<code>ce-chase-role</code>",
   "<code>dynamodb:Query</code>/<code>UpdateItem</code>, <code>ses:SendEmail</code>",
   "Cards and chases; one verified identity"],
  ["<code>ce-view-role</code>", "<code>dynamodb:Query</code>, <code>s3:GetObject</code>",
   "Cards, read; the photos prefix, read"]],
 tables=[
  ("Table: cards",
   "PK   person            S   j.reed@example.com\n"
   "SK   type_issued       S   first-aid-at-work#2023-09-12\n"
   "     expires           S   2026-09-12   -- null if it does not expire\n"
   "     number            S   4471-882\n"
   "     awarding_body     S   as printed\n"
   "     photo_keys        L   [front, back]\n"
   "     registered_by     S   j.reed@example.com\n"
   "     superseded_by     S   another SK, for a correction\n\n"
   "Append-only. Current state is computed from these rows and never stored,\n"
   "so a status field cannot drift away from the evidence.\n\n"
   "GSI  expiry-index        PK type, SK expires   -- the daily chase sweep"),
  ("Table: chases",
   "PK   person_type       S   j.reed@example.com#first-aid-at-work\n"
   "     expires           S   2026-09-12\n"
   "     lead_days         N   90\n"
   "     stage             S   holder | holder2 | manager | scheduling | lapsed\n"
   "     last_sent         S   2026-06-14T08:00:00Z\n"
   "     booked_for        S   2026-08-20, or null\n"
   "     lapsed_since      S   set on expiry day, never cleared until replaced\n\n"
   "A lapsed row keeps chasing weekly with no end condition other than a new\n"
   "card being registered. It is the only alert in this series that never rests.")],
 inbound=[
  "The <strong>capture page</strong> is static files in S3 behind CloudFront with an origin "
  "access control, reached through a signed staff link minted when somebody joins the staff "
  "list.",
  "<strong>Photos upload with a presigned PUT</strong>, front and back, so a phone on a site "
  "connection is not holding a Lambda open.",
  "<strong>Booking confirmation links</strong> are signed, scoped to one chase, and expire "
  "after the course date plus a fortnight.",
  "<strong>Nothing is fetched from an awarding body.</strong> Their registers are not open APIs "
  "and scraping them would create an assurance claim the system cannot honestly make."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "used to pick a certification type from your list and to identify which date on the card is "
  "the expiry.",
  "<strong>Called once</strong> per card, keyed on the image digest so a retry is free.",
  "<strong>Grounded</strong> with your certification types and their aliases, and with the "
  "staff list, so neither a type nor a person can be invented.",
  "<strong>Output is a JSON schema</strong> with type, holder, number, issued and expires, all "
  "nullable. A null expiry with an explicit does-not-expire flag is different from a failed "
  "read, and the schema distinguishes them.",
  "<strong>Dates are returned as read,</strong> with the ambiguity flagged rather than "
  "resolved. Resolving an ambiguous date silently is how somebody loses three months of "
  "validity."],
 gotchas=[
  "Check validity against the job date, not today. It is the most common bug in this kind of "
  "system and it fails in the direction that costs a day of work.",
  "Capture both sides. On a large minority of cards the expiry is on the back, and a system "
  "that accepts one photograph will have a register full of null dates.",
  "Set lead times from how long renewals actually took, which the register knows once it has a "
  "year of gap statistics.",
  "Never let a lapsed chase time out. It is the one alert here that should get louder rather "
  "than quieter.",
  "Do not claim qualification. Record what card you were shown and when; anything stronger is a "
  "claim you cannot support from a photograph."],
))
