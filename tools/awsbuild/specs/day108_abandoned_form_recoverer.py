"""Day 108 -- 2026-08-10 -- Abandoned form recoverer."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "abandoned-form-recoverer"
NAME = "Abandoned form recoverer"

SPEC = {
 "slug": SLUG, "date": "2026-08-10", "name": NAME,
 "tagline": ("Notices when somebody got most of the way through an enquiry and stopped, and "
             "sends one short message -- but only where they gave an address knowing what it "
             "was for, which is a much narrower case than it first appears."),
 "lede": ("A small system that detects an abandoned enquiry or booking form, works out whether "
          "there is any legitimate basis for contacting the person, and sends at most one short "
          "message offering to help. Most abandonments produce nothing, and the post explaining "
          "why is the important one. Seven posts on the same system -- one diagram at a time -- "
          "with a cost breakdown and an engineering reference at the end."),
 "keywords": ["form abandonment", "lead recovery", "consent", "conversion", "ecommerce",
              "serverless"],
 "icons": ["form", "clock", "email"],
 "faq": [
  ("What is an abandoned form recoverer?",
   "A small serverless system that notices when somebody entered enough of a form to be "
   "contactable and then stopped, and sends one short message where there is a legitimate basis "
   "for doing so. Where there is not, it records the abandonment and sends nothing."),
  ("Is emailing somebody who did not submit a form legitimate?",
   "Sometimes, and the post on this is the honest one. If they gave an address in a field "
   "labelled as being for a quote and stopped at the next step, contacting them about that quote "
   "is defensible. If they typed an address into a newsletter box and left, it is not."),
  ("How many messages does it send?",
   "One. Almost every abandonment recovery product sends three, and the second and third convert "
   "poorly and complain well. One message, and never a second."),
  ("Does it work?",
   "Modestly, and the measurement post is careful about it. A meaningful fraction of people who "
   "abandon come back on their own, so a naive comparison credits the message with recoveries "
   "that would have happened anyway."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "abandoned-form-recoverer-on-aws",
 "title": "An abandoned form recoverer on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Detects abandoned enquiry forms, checks whether contacting is legitimate, and sends "
          "at most one short message. AWS, about $2 a month."),
 "og": ("Most abandonments should produce nothing. The narrow case where a message is legitimate "
        "and welcome is what this system is for."),
 "abstract": ("The whole system on one page -- a detector, a basis check and a single message -- "
              "with the constraint that removes most of the volume and all of the risk."),
 "lede": ("Somebody starts a quote request, fills in three fields including their email, gets to "
          "the part asking for measurements, and stops. They may have gone to find a tape "
          "measure. They may have decided against it. Either way the business has an email "
          "address and no enquiry, and the obvious move &mdash; email them &mdash; is right in a "
          "narrower set of cases than most people assume. This post walks through a small system "
          "that finds that narrow case and stays inside it."),
 "tags": ["form abandonment", "lead recovery", "consent", "conversion", "ecommerce", "serverless"],
 "takeaways": [
  "Detection is easy; deciding whether to contact is the whole problem.",
  "The basis depends on what the field was labelled as being for, and what step they reached.",
  "One message, ever. Never a sequence.",
  "Most abandonments produce nothing and are recorded rather than actioned.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "A form in progress", "sub": ["partial entries"], "icon": "form"},
      {"title": "What the form said", "sub": ["labels and purpose"], "icon": "doc"},
      {"title": "The person", "sub": ["one message, at most"], "icon": "person"}],
    "inside": [
      {"title": "Detector", "sub": ["stopped, and got", "far enough"], "icon": "clock"},
      {"title": "Basis check", "sub": ["may we contact", "them at all?"], "icon": "shield"},
      {"title": "Sender", "sub": ["one short message,", "then never again"], "icon": "email"}],
    "edges": [{"from": 0, "to": 0, "label": "partial data"},
              {"from": 1, "to": 1, "label": "what they were told"},
              {"from": 2, "to": 2, "label": "one message, or none", "up": True}],
    "note": "The middle box stops most of them, and that is the system working correctly."}),
   "Three things outside the account, three pieces inside it. The basis check is the component "
   "that most implementations of this idea do not have at all.",
   "System: an abandoned form detected, a basis checked, one message sent",
   "Three boxes across the top sit outside the AWS account. On the left, A form in progress: "
   "partial entries. In the middle, What the form said: its labels and stated purpose. On the "
   "right, The person, who receives one message at most. Each connects by an arrow to the AWS "
   "account container below. Partial data flows down into the account. What they were told feeds "
   "in. One message, or none, goes back out. Inside the AWS account are three components in a "
   "row. On the left, the Detector, which establishes that somebody stopped and got far enough. "
   "In the middle, the Basis check, asking whether they may be contacted at all. On the right, "
   "the Sender, which sends one short message and then never again. A note at the bottom says the "
   "middle box stops most of them, and that is the system working correctly."),
  ("h3", "The uncomfortable part first"),
  ("p", "It is worth being direct about this before anything else, because most products in this "
        "category are not. Somebody who typed an email address into a form and did not submit it "
        "has not agreed to anything. Whether you may contact them depends entirely on what the "
        "form told them the address was for and how far through they got, and in a good number of "
        "cases the answer is that you may not."),
  ("p", "A quote form where the address field is labelled \"where should we send your quote?\" "
        "and they reached step four of five is one case. A newsletter box in a footer where "
        "somebody typed an address and navigated away is a completely different one, and treating "
        "them the same is how this category of tool earns its reputation."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The detector.</strong> Notices that a partially completed form has gone quiet, which "
   "needs less client-side machinery than people expect. Part 2 covers what is captured and, more "
   "importantly, what is not.",
   "<strong>The basis check.</strong> Decides whether there is a legitimate reason to contact "
   "this person about this form. Part 3 is the substantive post in this series.",
   "<strong>The sender.</strong> One message, short, referencing what they were doing, with an "
   "obvious way to say no and a link back to where they were. Part 4.",
  ]),
  ("h2", "One abandonment, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Started", "sub": ["a quote form"], "icon": "form"},
      {"title": "Stopped", "sub": ["at step 4 of 5"], "icon": "clock"},
      {"title": "Detected", "sub": ["after 30 minutes"], "icon": "search"},
      {"title": "Basis checked", "sub": ["labelled, far enough"], "icon": "shield"},
      {"title": "One message", "sub": ["at 2 hours"], "icon": "email"}],
    "title": "ONE ABANDONMENT, END TO END",
    "note": "The fourth box says no about two thirds of the time, which is correct."}),
   "The same system as one line. The rate at which the fourth step declines to send is the "
   "measure of whether the basis check is doing its job.",
   "One abandoned form from start to a single message, in five stages",
   "A horizontal row of five boxes joined by arrows. Started: a quote form. Stopped: at step four "
   "of five. Detected: after thirty minutes. Basis checked: the field was labelled and they got "
   "far enough. One message: sent at two hours. A note says the fourth box says no about two "
   "thirds of the time, which is correct."),
  ("h2", "In plain words"),
  ("p", "Somebody starts a quote form for a bathroom. They enter their name, their email under a "
        "field that says \"where should we send your quote?\", their postcode, and the room "
        "dimensions. The next step asks for photographs and they stop. Thirty minutes later the "
        "detector notices."),
  ("p", "The basis check runs: the address was given specifically for the purpose of receiving a "
        "quote, they completed four of five steps, and the form said clearly what would happen "
        "next. That is a defensible basis, so at two hours one message goes: \"You were most of "
        "the way through a bathroom quote &mdash; would you like me to pick it up from where you "
        "got to, or send what we have?\" with a link and an obvious way to say no."),
  ("p", "The same day somebody else types an email address into the newsletter box in the footer "
        "and closes the tab. That is also an abandonment, it is also detectable, and the basis "
        "check declines. Nothing is sent. It is recorded, it appears in the conversion analysis, "
        "and the person is never contacted &mdash; which is both the right answer and the one "
        "most tools in this category get wrong."),
  ("callout", "Design rules that shaped every decision", [
   "The basis check is the system. Detection without it is a way of emailing strangers.",
   "The field's label determines what the address may be used for. Not the business's intent.",
   "One message. Never two, never a sequence, whatever the conversion data says.",
   "Reference what they were doing, specifically. A generic nudge is worse than nothing.",
   "An obvious way to say no, and it works permanently across every form.",
   "Never capture what was typed into a sensitive field, even in progress.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Abandonment recovery has an unusually bad reputation for a category with a genuine use "
        "case, and the reason is that the products optimise for volume: capture every address, "
        "send three messages, measure conversion. That produces recoveries and complaints in a "
        "ratio that looks acceptable in a dashboard and does not look acceptable to the people "
        "receiving the third message."),
  ("p", "So this design inverts it. The detection is trivial, the basis check is strict enough to "
        "decline most abandonments, and the message is one. What is left is a genuinely useful "
        "thing for the narrow case where somebody was clearly trying to do business with you and "
        "got interrupted."),
  ("p", "The next four posts walk through each piece: how an abandonment is detected, how the "
        "basis is decided, what the message says, and how recovery is honestly measured. One "
        "diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-an-abandonment-is-detected",
 "title": "How an abandonment is detected",
 "nav": "How it is detected",
 "read": 5, "words": 740,
 "desc": ("What gets captured as somebody types, what deliberately does not, and how stopping is "
          "told apart from pausing."),
 "og": ("Capturing every keystroke is technically easy and is how this category gets its "
        "reputation. Capture completed fields at step boundaries, and never the sensitive ones."),
 "abstract": ("What is captured as a form is filled in, the fields that are never captured, how "
              "a pause is told from an abandonment, and the completion that arrives late."),
 "lede": ("Detecting an abandoned form is genuinely easy and the temptation is to capture "
          "everything as it is typed, which is both unnecessary and the reason people are wary of "
          "this category. Capturing less turns out to cost almost nothing in effectiveness."),
 "tags": ["form abandonment", "data minimisation", "detection", "privacy", "conversion",
          "serverless"],
 "takeaways": [
  "Capture at step boundaries, not on every keystroke.",
  "Never capture payment fields, passwords, or anything in a sensitive category.",
  "A pause is thirty minutes; an abandonment is a pause that did not resume.",
  "A late completion cancels everything, and the check runs immediately before sending.",
  "Partial data is deleted on a short clock whether or not a message was sent.",
 ],
 "blocks": [
  ("h2", "Capture at boundaries"),
  ("fig", ("chain", {
    "entry": {"title": "Somebody fills a form", "sub": ["step by step"], "icon": "form"},
    "steps": [
      {"title": "A step completes", "sub": ["not every keystroke"], "icon": "check"},
      {"title": "Is any field sensitive?", "sub": ["payment, health, password"], "icon": "branch",
       "exit": {"title": "Capture nothing from it", "sub": ["not even that it was filled"],
                "icon": "lock", "label": "yes"}},
      {"title": "Store the step", "sub": ["fields and values"], "icon": "database"},
      {"title": "Quiet for 30 minutes?", "sub": ["no further step"], "icon": "branch",
       "exit": {"title": "Still going", "sub": ["wait"], "icon": "clock", "label": "no"}},
      {"title": "An abandonment", "sub": ["hand to the basis check"], "icon": "search"}],
    "note": "Step boundaries capture almost everything a keystroke listener would, with far less."}),
   "How a partially completed form is captured. Recording at step boundaries rather than "
   "continuously is nearly as effective and avoids holding a keystroke log of somebody's "
   "half-typed thoughts.",
   "How an abandoned form is detected from step boundaries",
   "A vertical chain of five steps entered by a box labelled Somebody fills a form, step by step. "
   "Step one waits for a step to complete rather than watching every keystroke. Step two asks "
   "whether any field in it is sensitive, covering payment, health and password fields; if so it "
   "exits to Capture nothing from it, not even the fact it was filled. Step three stores the step "
   "with its fields and values. Step four asks whether the form has been quiet for thirty minutes "
   "with no further step; if not it exits to Still going and waits. Step five declares an "
   "abandonment and hands it to the basis check. A note says step boundaries capture almost "
   "everything a keystroke listener would, with far less."),
  ("h3", "What is never captured"),
  ("p", "Payment fields, obviously, and for a reason beyond taste: capturing them at all brings a "
        "checkout into a compliance scope it was carefully kept out of. The same applies to "
        "anything in a special category &mdash; health details on a clinic booking form, for "
        "instance &mdash; where partial capture creates an obligation the completed form would "
        "have handled properly."),
  ("p", "The rule is implemented as an explicit allow-list of fields that may be captured rather "
        "than a deny-list of fields that may not. A new field added to a form is not captured "
        "until somebody decides it should be, which is the correct default and the opposite of "
        "what most implementations do."),
  ("h3", "Pausing versus stopping"),
  ("p", "Thirty minutes of inactivity is a reasonable line and it is genuinely a guess. People go "
        "and find a tape measure, take a phone call, or get distracted, and a substantial number "
        "come back within the hour and finish."),
  ("p", "What matters more than the exact interval is that the completion check runs again "
        "immediately before the message is sent. Somebody who abandoned at two o'clock, was "
        "detected at half past, and completed the form at ten to four must not receive a message "
        "at four saying they did not finish."),
  ("h2", "The late completion"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Abandoned", "sub": ["14:00"], "icon": "clock"},
      {"title": "Detected", "sub": ["14:30"], "icon": "search"},
      {"title": "Message queued", "sub": ["for 16:00"], "icon": "email"},
      {"title": "They finish", "sub": ["15:50"], "icon": "check"},
      {"title": "Cancelled", "sub": ["checked at send time"], "icon": "stop"}],
    "title": "THE CHECK THAT RUNS TWICE",
    "note": "Sending a 'you did not finish' message to somebody who finished is the worst output."}),
   "Why completion is checked again at send time. It is a cheap check and its absence produces "
   "the single most embarrassing message this system could send.",
   "How a late form completion cancels a queued message",
   "A horizontal row of five boxes. Abandoned: at two o'clock. Detected: at half past two. "
   "Message queued: for four o'clock. They finish: at ten to four. Cancelled: because completion "
   "is checked at send time. A note says sending a you-did-not-finish message to somebody who "
   "finished is the worst output."),
  ("p", "The same check covers a second case that is easy to miss: somebody who abandoned one "
        "form and then submitted a different one, or rang up, or completed a purchase. Any "
        "conversion in the window cancels the message, and the check is against the customer "
        "rather than the specific form."),
  ("h3", "Deleting the partial data"),
  ("p", "Partial form data is deleted on a short clock &mdash; seven days is generous &mdash; "
        "whether or not a message was sent. There is no reason to keep a half-finished quote "
        "request indefinitely, and a table of them accumulating for years is a data question "
        "nobody wants to answer."),
  ("p", "What survives is the anonymous fact of the abandonment: which step, which form, no "
        "personal data. That is what the conversion analysis needs and it carries none of the "
        "obligations the partial data does."),
  ("p", "Next: whether you may contact them at all."),
 ],
},
{
 "slug": "how-the-basis-gets-decided",
 "title": "How the basis gets decided",
 "nav": "How the basis is decided",
 "read": 6, "words": 780,
 "desc": ("What the field label determines, how far through is far enough, the cases that are "
          "clearly fine and clearly not, and the ones that are genuinely arguable."),
 "og": ("The field label decides what an address may be used for, not the business's intent. "
        "That single principle removes most of the difficulty."),
 "abstract": ("Why the field's own label determines what the address may be used for, how far "
              "through counts as far enough, the clear cases at both ends, and how to handle the "
              "arguable middle."),
 "lede": ("This is the post that matters. Everything else in this system is plumbing, and this is "
          "the part that determines whether the thing you have built is useful or is a way of "
          "emailing people who did not ask to be emailed."),
 "tags": ["form abandonment", "consent", "legitimate interest", "GDPR", "ethics", "serverless"],
 "takeaways": [
  "The field label determines the purpose. \"Where shall we send your quote?\" is specific.",
  "How far through matters: somebody at step four of five was clearly transacting.",
  "Two clear ends: a labelled address deep in a transactional form, and a footer newsletter box.",
  "The arguable middle exists, and the honest handling is to decline it.",
  "Where a person is already a customer, the question is different and usually easier.",
 ],
 "blocks": [
  ("h2", "The label decides"),
  ("p", "The single most useful principle here: what an address may be used for is determined by "
        "what the person was told when they typed it, not by what the business would like to do "
        "with it. That is both the legal shape of it in most regimes and the shape most people "
        "would recognise as fair."),
  ("table", ["Field label", "What it permits", "Verdict"], [
   ["\"Where shall we send your quote?\"", "Sending them that quote", "Contactable about this"],
   ["\"Your email (so we can confirm the booking)\"", "Confirming that booking", "Contactable"],
   ["\"Email\" on a multi-step enquiry", "Responding to the enquiry", "Usually contactable"],
   ["\"Get our newsletter\"", "Sending the newsletter, if confirmed", "Not contactable about this"],
   ["\"Email\" in a footer box, no context", "Nothing, without a confirmation", "Not contactable"],
   ["A field they filled during checkout", "The transaction", "Contactable, narrowly"],
  ]),
  ("p", "The third row is the common case and the one worth thinking about. A bare \"Email\" "
        "field in the middle of a multi-step enquiry form carries its context from the form "
        "around it: somebody filling in a bathroom quote request understands what the address is "
        "for. A bare \"Email\" field in a footer carries no context at all."),
  ("h2", "How far through"),
  ("fig", ("chain", {
    "entry": {"title": "An abandonment", "sub": ["with an address"], "icon": "form"},
    "steps": [
      {"title": "Was the field labelled?", "sub": ["with a purpose"], "icon": "branch",
       "exit": {"title": "Do not contact", "sub": ["no stated purpose"], "icon": "stop",
                "label": "no"}},
      {"title": "Far enough through?", "sub": ["past the halfway step"], "icon": "branch",
       "exit": {"title": "Do not contact", "sub": ["they barely started"], "icon": "stop",
                "label": "no"}},
      {"title": "Already a customer?", "sub": ["an existing relationship"], "icon": "branch",
       "exit": {"title": "Contactable", "sub": ["a different and easier basis"], "icon": "check",
                "label": "yes"}},
      {"title": "Withdrawn before?", "sub": ["ask the consent keeper"], "icon": "branch",
       "side": {"title": "Consent record", "sub": ["from Day 105"], "icon": "shield"},
       "exit": {"title": "Do not contact", "sub": ["ever, for any reason"], "icon": "lock",
                "label": "yes"}},
      {"title": "One message is defensible", "sub": ["and one only"], "icon": "email"}],
    "note": "Four gates, three of which say no. Most abandonments do not reach the last box."}),
   "The basis check in full. Three of the four gates decline, which is why most abandonments "
   "produce nothing at all.",
   "How the basis for contacting an abandoner is decided",
   "A vertical chain of five steps entered by a box labelled An abandonment, with an address. "
   "Step one asks whether the field was labelled with a purpose; if not it exits to Do not "
   "contact, because there was no stated purpose. Step two asks whether they got far enough "
   "through, past the halfway step; if not it exits to Do not contact, because they barely "
   "started. Step three asks whether they are already a customer with an existing relationship; "
   "if so it exits to Contactable, on a different and easier basis. Step four asks whether they "
   "have withdrawn before, checking the consent record from Day 105; if so it exits to Do not "
   "contact, ever, for any reason. Step five concludes that one message is defensible, and one "
   "only. A note says four gates, three of which say no, and most abandonments do not reach the "
   "last box."),
  ("h3", "Past the halfway step"),
  ("p", "Somebody who entered their email on step one of five and stopped has expressed interest "
        "in the way that clicking a link expresses interest. Somebody who reached step four has "
        "spent several minutes providing specific information about a specific job, which is a "
        "materially different act."),
  ("p", "Halfway is a rule of thumb rather than a principle, and the useful version of it is: did "
        "they give you enough that a reply would be about their actual situation rather than a "
        "generic prompt? If the message can only say \"you started a form\", the basis is thin. "
        "If it can say \"you were most of the way through a quote for a bathroom in Ashford\", "
        "the person will recognise it as a continuation of something they were doing."),
  ("h3", "Existing customers"),
  ("p", "A much easier case and worth separating explicitly. Somebody who has bought from you "
        "before, abandoning a form on your site, is in an existing relationship and the question "
        "of whether you may email them about something they were evidently trying to do is not a "
        "difficult one."),
  ("p", "It is still one message, and it still respects any withdrawal. The difference is that "
        "the label and step-depth gates matter less, because the basis comes from the "
        "relationship rather than from the form."),
  ("h2", "The arguable middle, and what to do with it"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Clearly fine", "sub": ["labelled, deep, customer"], "icon": "check"},
      {"title": "Clearly not", "sub": ["footer box, one field"], "icon": "stop"},
      {"title": "Arguable", "sub": ["step 2 of 5, bare label"], "icon": "branch"},
      {"title": "The temptation", "sub": ["'we could justify it'"], "icon": "alarm"},
      {"title": "Decline it", "sub": ["and record why"], "icon": "shield"}],
    "title": "THE MIDDLE IS WHERE THE JUDGEMENT IS",
    "note": "\"We could probably justify it\" is the sentence to treat as a no."}),
   "The three bands and the rule for the middle one. The phrase in the note is a reliable signal "
   "that the answer should be no.",
   "The three bands of contact basis and how the middle is handled",
   "A horizontal row of five boxes. Clearly fine: a labelled field, deep in the form, an existing "
   "customer. Clearly not: a footer box with one field. Arguable: step two of five with a bare "
   "label. The temptation: the phrase we could justify it. Decline it: and record why. A note "
   "says we could probably justify it is the sentence to treat as a no."),
  ("p", "The arguable band is real and it is where every implementation of this drifts over time, "
        "one reasonable-sounding widening at a time. The practical defence is to make declining "
        "the default for the middle band and to require an explicit configuration change, with a "
        "recorded reason, to move a form out of it."),
  ("p", "That reason then sits in the configuration where whoever asks about it later can read "
        "it, which is a much better position than reconstructing a decision from a threshold "
        "somebody moved eighteen months ago."),
  ("p", "Next: what the one message says."),
 ],
},
{
 "slug": "how-the-one-message-is-written",
 "title": "How the one message is written",
 "nav": "How it is written",
 "read": 5, "words": 730,
 "desc": ("Referencing what they were actually doing, the timing, why there is never a second "
          "message, and the opt-out that works everywhere."),
 "og": ("A generic nudge is worse than nothing. The message has to be about the specific thing "
        "they were doing, which is why the basis check and the message are the same design."),
 "abstract": ("Why the message must reference the specific thing they were doing, the timing, why "
              "there is never a second message, and the opt-out that has to work across every "
              "form."),
 "lede": ("The message is short, specific, and singular, and each of those three does real work. "
          "A long one reads as marketing, a generic one reads as automated, and a second one "
          "reads as pursuit."),
 "tags": ["form abandonment", "email", "copywriting", "opt-out", "conversion", "serverless"],
 "takeaways": [
  "Reference the specific thing: the quote, the booking, the room, the date.",
  "Two hours is a reasonable delay; same-day always, next-day never.",
  "One message. The second converts poorly and generates most of the complaints.",
  "Reply-to a person, not a no-reply address. A good number of people just reply.",
  "The opt-out is permanent and applies to every form, not just this one.",
 ],
 "blocks": [
  ("h2", "What it says"),
  ("callout", "The whole message", [
   "<strong>Subject:</strong> Your bathroom quote &mdash; want me to pick it up?",
   "You got most of the way through a quote for a bathroom in Ashford earlier and stopped at the "
   "photos step.",
   "If it is easier, reply and tell me roughly what you are after and I will put something "
   "together &mdash; or <strong>carry on where you left off</strong>.",
   "If you have changed your mind that is completely fine, and you can <em>tell me not to "
   "follow up</em> and I will not.",
   "<strong>Signed by a person,</strong> with a reply-to that reaches them.",
  ]),
  ("p", "Four lines. The specificity in the first is what stops it reading as automated, and it "
        "is only possible because the basis check already established that they got far enough "
        "for there to be something specific to reference."),
  ("h3", "Reply-to a person"),
  ("p", "A meaningful proportion of the responses to this message are replies rather than clicks, "
        "and they are frequently the better outcome: somebody typing two sentences about what "
        "they want is a warmer lead than somebody returning to a form. A no-reply address throws "
        "all of that away and signals that the message was automated, which it was, and which the "
        "wording is otherwise working to avoid."),
  ("h2", "Timing"),
  ("fig", ("chain", {
    "entry": {"title": "Abandonment confirmed", "sub": ["basis checked"], "icon": "shield"},
    "steps": [
      {"title": "Wait two hours", "sub": ["from the last step"], "icon": "clock"},
      {"title": "Still not completed?", "sub": ["re-checked now"], "icon": "branch",
       "exit": {"title": "Cancel", "sub": ["they came back"], "icon": "stop", "label": "completed"}},
      {"title": "Within business hours?", "sub": ["their local time"], "icon": "branch",
       "exit": {"title": "Hold to the morning", "sub": ["never send at 3am"], "icon": "clock",
                "label": "no"}},
      {"title": "Still the same day?", "sub": ["or the next morning"], "icon": "branch",
       "exit": {"title": "Send nothing", "sub": ["the moment has passed"], "icon": "stop",
                "label": "no"}},
      {"title": "Send it", "sub": ["once, ever"], "icon": "email"}],
    "note": "A message that has slipped past the next morning should not be sent at all."}),
   "The timing gates. The last one is unusual and correct: a nudge about something somebody was "
   "doing on Tuesday is not useful on Thursday.",
   "How the timing of a single recovery message is decided",
   "A vertical chain of five steps entered by a box labelled Abandonment confirmed, with the "
   "basis checked. Step one waits two hours from the last completed step. Step two asks whether "
   "it is still not completed, re-checked now; a completion exits to Cancel because they came "
   "back. Step three asks whether it is within business hours in their local time; if not it "
   "exits to Hold to the morning, because nothing is sent at three in the morning. Step four asks "
   "whether it is still the same day or the next morning; if not it exits to Send nothing, "
   "because the moment has passed. Step five sends it, once, ever. A note says a message that has "
   "slipped past the next morning should not be sent at all."),
  ("h3", "Why two hours"),
  ("p", "Long enough that most people who were coming back have come back, which keeps the "
        "message from being irritating. Short enough that they still remember doing it, which is "
        "what makes the specific reference land."),
  ("p", "The expiry at the next morning is the unusual part and it is deliberate. The entire "
        "premise of the message is that it is a helpful continuation of something they were doing "
        "a couple of hours ago. Three days later it is not a continuation; it is a marketing "
        "message about a form, and the basis that justified it has largely evaporated."),
  ("h2", "Why never a second"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Message one", "sub": ["converts, modestly"], "icon": "email"},
      {"title": "Message two", "sub": ["converts far less"], "icon": "counter"},
      {"title": "Complaints", "sub": ["mostly from message two"], "icon": "alarm"},
      {"title": "Message three", "sub": ["converts near zero"], "icon": "stop"},
      {"title": "One, always", "sub": ["the whole difference"], "icon": "check"}],
    "title": "WHY THE SEQUENCE STOPS AT ONE",
    "note": "The second message is where this category earned its reputation."}),
   "The case for a single message. The conversion curve falls fast and the complaint curve does "
   "not, which makes the second message a bad trade even on its own terms.",
   "Why abandonment recovery stops at one message",
   "A horizontal row of five boxes. Message one: converts, modestly. Message two: converts far "
   "less. Complaints: mostly from message two. Message three: converts near zero. One, always: "
   "which is the whole difference. A note says the second message is where this category earned "
   "its reputation."),
  ("p", "The argument for a second message is always the marginal conversion, and it is real and "
        "small. What it leaves out is that the complaints, the spam reports and the "
        "\"how did you get my email\" replies come overwhelmingly from the second and third, and "
        "those costs are diffuse enough not to appear next to the conversion number."),
  ("h3", "The opt-out"),
  ("p", "One link, and it does something broader than it appears: it records a withdrawal for "
        "this purpose against that person, which the basis check reads on every future "
        "abandonment across every form. Somebody who says no once is never nudged about anything "
        "again."),
  ("p", "That is more than most implementations do, and it costs nothing because the consent "
        "record already exists. It is also the thing that makes the message honest: \"you can "
        "tell me not to follow up\" is only true if it applies to everything."),
  ("p", "Next: whether any of it works."),
 ],
},
{
 "slug": "how-recovery-is-honestly-measured",
 "title": "How recovery is honestly measured",
 "nav": "How it is measured",
 "read": 5, "words": 730,
 "desc": ("The people who would have come back anyway, the holdout that makes the number real, "
          "and what a modest honest result looks like."),
 "og": ("A good fraction of abandoners return on their own. Crediting the message with those is "
        "how this category reports numbers nobody can reproduce."),
 "abstract": ("Why a naive recovery rate overstates by a large factor, the holdout that makes the "
              "measurement real, what an honest result looks like, and the second number that "
              "matters more."),
 "lede": ("This category reports conversion rates that are wrong by a large factor, and the "
          "reason is simple enough that it is worth stating plainly: a substantial number of "
          "people who abandon a form come back and finish it without any prompting at all, and "
          "the naive measurement credits every one of them to the message."),
 "tags": ["form abandonment", "measurement", "holdout", "attribution", "conversion", "serverless"],
 "takeaways": [
  "Many abandoners return on their own. A naive rate credits the message with all of them.",
  "A holdout -- a share who are deliberately not messaged -- is the only honest measurement.",
  "Ten per cent is enough, and it costs a small number of recoveries to know the truth.",
  "An honest uplift is usually modest, and modest is still worth having.",
  "The complaint and opt-out rate belongs in the same report as the uplift.",
 ],
 "blocks": [
  ("h2", "The people who come back anyway"),
  ("fig", ("chain", {
    "entry": {"title": "100 abandonments", "sub": ["basis check passed"], "icon": "form"},
    "steps": [
      {"title": "Message 90", "sub": ["hold back 10"], "icon": "email",
       "side": {"title": "Holdout", "sub": ["random, and fixed"], "icon": "filter"}},
      {"title": "Messaged: how many returned?", "sub": ["say 18 of 90"], "icon": "counter"},
      {"title": "Holdout: how many returned?", "sub": ["say 1 of 10"], "icon": "search"},
      {"title": "Naive rate", "sub": ["20% -- and wrong"], "icon": "alarm"},
      {"title": "Real uplift", "sub": ["20% minus 10% = 10 points"], "icon": "chart"}],
    "note": "Half the naive number was people who were coming back regardless."}),
   "Why a holdout is the only honest measurement. The gap between the naive rate and the uplift "
   "is entirely people who needed no prompting.",
   "How a holdout group makes recovery measurement honest",
   "A vertical chain of five steps entered by a box labelled One hundred abandonments that passed "
   "the basis check. Step one messages ninety and holds back ten as a random, fixed holdout. Step "
   "two asks how many of the messaged returned, say eighteen of ninety. Step three asks how many "
   "of the holdout returned, say one of ten. Step four computes the naive rate at twenty per "
   "cent, which is wrong. Step five computes the real uplift as twenty per cent minus ten per "
   "cent, giving ten percentage points. A note says half the naive number was people who were "
   "coming back regardless."),
  ("h3", "Why a holdout rather than a before-and-after"),
  ("p", "The obvious alternative &mdash; compare the recovery rate before the system existed with "
        "after &mdash; is confounded by everything else that changed. Seasonality, a site "
        "redesign, a different mix of traffic. A holdout running concurrently is the only "
        "comparison where the two groups differ in one thing."),
  ("p", "Ten per cent is enough at typical volumes and it costs a small number of recoveries a "
        "month. It is worth paying: without it, nobody can say whether the system is doing "
        "anything, and a system nobody can evaluate tends to acquire a second message and then a "
        "third."),
  ("h3", "Keeping the holdout honest"),
  ("p", "The holdout has to be assigned randomly and permanently at the moment of abandonment, "
        "not chosen afterwards, and the assignment has to be recorded before the outcome is "
        "known. Assigning it retrospectively, or excluding holdout cases that look unusual, "
        "produces a number that is worse than not measuring."),
  ("p", "It also has to survive somebody wanting to switch it off. The pressure to message the "
        "holdout arrives about four months in, framed as \"we know it works now\", and the "
        "correct answer is that knowing it still works next year requires it to keep running."),
  ("h2", "What an honest number looks like"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Abandonments", "sub": ["310 this quarter"], "icon": "form"},
      {"title": "Basis passed", "sub": ["104"], "icon": "shield"},
      {"title": "Messaged", "sub": ["94"], "icon": "email"},
      {"title": "Uplift", "sub": ["9 percentage points"], "icon": "chart"},
      {"title": "Extra enquiries", "sub": ["about 8"], "icon": "check"}],
    "title": "ONE QUARTER, HONESTLY",
    "note": "Eight enquiries a quarter. Modest, real, and worth the two hours it took to build."}),
   "A quarter measured honestly. The number is smaller than the category usually reports and it "
   "is one somebody could reproduce.",
   "One quarter of form abandonment recovery measured honestly",
   "A horizontal row of five boxes. Abandonments: three hundred and ten this quarter. Basis "
   "passed: one hundred and four. Messaged: ninety-four. Uplift: nine percentage points. Extra "
   "enquiries: about eight. A note says eight enquiries a quarter is modest, real, and worth the "
   "two hours it took to build."),
  ("p", "Eight extra enquiries a quarter is a genuinely modest result and it is worth stating as "
        "such rather than dressing it up. For a business where an enquiry is worth a few hundred "
        "pounds, eight is a good return on a small system; for one where an enquiry is worth "
        "twenty, it probably is not worth building at all, and knowing that is useful."),
  ("p", "The drop from three hundred and ten abandonments to one hundred and four that pass the "
        "basis check is the other number worth looking at, and it is the system behaving "
        "correctly. Two thirds of abandonments are people who typed an address somewhere without "
        "context, and not contacting them is the point."),
  ("h2", "The number next to the uplift"),
  ("p", "The complaint and opt-out rate belongs in the same table, always, because the uplift on "
        "its own invites the obvious optimisation and the two numbers together do not."),
  ("callout", "Reported together, every quarter", [
   "<strong>Uplift:</strong> 9 percentage points against the holdout.",
   "<strong>Opt-outs:</strong> 3 of 94 messaged asked not to be followed up again.",
   "<strong>Complaints:</strong> 0 spam reports, 1 reply asking how we got their address.",
   "<strong>That last one matters</strong> even at a count of one. It means somebody did not "
   "recognise the context, which is a signal about the form rather than about them.",
   "<strong>If opt-outs exceed about 5%,</strong> the basis check is too loose and should be "
   "tightened rather than the wording softened.",
  ]),
  ("p", "That last rule is the one worth writing down somewhere durable. When a recovery message "
        "generates complaints, the instinct is to rewrite the message, and the message is almost "
        "never the problem. The problem is that it was sent to somebody who did not have enough "
        "context to recognise why, which is a basis question."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="abandonment",
 volumes=[(100, "100 abandonments"), (400, "400 abandonments"), (1500, "1,500 abandonments")],
 read_each=0.0,
 msgs_each=0.35,
 lede=("There is no model in this system and the message volume is low by design, because two "
       "thirds of abandonments produce nothing. Four hundred abandonments a month is a "
       "reasonably busy enquiry form. Here is where each cent goes."),
 takeaway_extra=("Only about a third of abandonments result in a message, which keeps the "
                 "messaging line small."),
 risks=[
  "<strong>Capturing on every keystroke.</strong> Not primarily a cost problem, though it is one "
  "at volume: a write per keystroke across a busy form is a lot of writes for data you delete in "
  "seven days.",
  "<strong>Never expiring partial data.</strong> A table of half-finished forms accumulating for "
  "years is a storage cost and a much larger data question. Seven days is generous.",
  "<strong>Log retention left at never.</strong> These logs contain partial form contents, which "
  "makes unbounded retention both a cost and a problem.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. The messaging band assumes "
                "roughly a third of abandonments pass the basis check, which matches what the "
                "gates in Part 3 actually do."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="af",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the capture allow-list, and the holdout assignment."),
 outside=[
  {"title": "The forms", "sub": ["step events by beacon"], "icon": "form"},
  {"title": "Consent record", "sub": ["from Day 105"], "icon": "shield"},
  {"title": "SES outbound", "sub": ["one message"], "icon": "email"}],
 inside=[
  {"title": "Function URL + EventBridge", "sub": ["step capture,", "detection sweep"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["capture, detect, send"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["sessions, outcomes"], "icon": "database"}],
 note="us-east-1. One account. Captured fields are an allow-list; partial data expires in 7 days.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The forms, sending step events by beacon. "
  "The Consent record from Day 105. And SES outbound, carrying one message. Inside the account, "
  "three groups. A Function URL for step capture and EventBridge running a detection sweep. Three "
  "Lambda functions named capture, detect and send. And two DynamoDB tables named sessions and "
  "outcomes. A note gives the region as us-east-1, one account, states that captured fields are "
  "an allow-list, and that partial data expires in seven days."),
 functions=[
  ["<code>af-capture</code>", "Function URL",
   "Accepts a step event; stores only allow-listed fields", "5s / 512&nbsp;MB"],
  ["<code>af-detect</code>", "EventBridge every 10 minutes",
   "Finds quiet sessions, runs the four basis gates, assigns the holdout",
   "30s / 512&nbsp;MB"],
  ["<code>af-send</code>", "SQS send queue",
   "Re-checks completion, checks hours, sends once, records the outcome",
   "15s / 512&nbsp;MB"]],
 roles=[
  ["<code>af-capture-role</code>", "<code>dynamodb:UpdateItem</code>",
   "The sessions table only"],
  ["<code>af-detect-role</code>",
   "<code>dynamodb:Query</code>, <code>sqs:SendMessage</code>, "
   "<code>secretsmanager:GetSecretValue</code>",
   "Sessions; the send queue; the consent resolver credential"],
  ["<code>af-send-role</code>", "<code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Sessions and outcomes; one verified identity"]],
 tables=[
  ("Table: sessions",
   "PK   session_id        S   a random id from the form, not a customer id\n"
   "     form_id           S   quote_bathroom\n"
   "     steps_done        N   4\n"
   "     steps_total       N   5\n"
   "     fields            M   allow-listed fields only\n"
   "     email             S   only if the field was on the allow-list\n"
   "     email_label       S   the label shown next to it, verbatim\n"
   "     last_step_at      S   2026-08-10T14:00:00Z\n"
   "     completed_at      S   set on submission; cancels everything\n"
   "     basis             S   ok | no_label | too_early | withdrawn | not_checked\n"
   "     holdout           BOOL assigned at detection, before the outcome\n"
   "     ttl               N   epoch, +7 days\n\n"
   "`email_label` is stored verbatim because the basis in Part 3 depends on\n"
   "what the person was actually shown, and form copy changes."),
  ("Table: outcomes",
   "PK   form_id           S   quote_bathroom\n"
   "SK   period_session    S   2026-Q3#session_id\n"
   "     holdout           BOOL\n"
   "     messaged          BOOL\n"
   "     returned          BOOL   -- did they complete within 7 days\n"
   "     opted_out         BOOL\n"
   "     complained        BOOL\n\n"
   "No personal data at all. This survives the 7-day expiry of the session\n"
   "and is what the holdout comparison is computed from.")],
 inbound=[
  "<strong>Step events arrive by beacon</strong> on step completion, not on input. There is no "
  "keystroke listener anywhere in the design.",
  "<strong>Captured fields are an allow-list</strong> defined per form. A field added to a form "
  "is not captured until somebody adds it, which is the correct default.",
  "<strong>Payment, password and special-category fields</strong> cannot be added to the "
  "allow-list; the capture function rejects them by name pattern as a second line of defence.",
  "<strong>The consent resolver is consulted</strong> before every send, so a withdrawal recorded "
  "anywhere in the business suppresses this message too."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Detection is a timestamp comparison and the "
  "basis check is four rules.",
  "<strong>The tempting use</strong> is generating the message, and it is the wrong one: the "
  "specificity comes from the captured fields, and a generated version reads as automated in "
  "exactly the way the wording is trying to avoid.",
  "<strong>The template carries the specifics</strong> &mdash; the form name, the step, the "
  "location &mdash; substituted from what was captured.",
  "<strong>A second tempting use</strong> is scoring how likely somebody is to convert, in order "
  "to message only the promising ones. That optimises the wrong thing and makes the holdout "
  "comparison invalid.",
  "<strong>The cost page assumes none</strong>, which is why messaging is the only variable "
  "band."],
 gotchas=[
  "Store the field label verbatim. The basis depends on what the person was shown, and form copy "
  "changes without anybody thinking about this system.",
  "Re-check completion at send time. Sending a you-did-not-finish message to somebody who "
  "finished is the worst possible output.",
  "Assign the holdout at detection, before the outcome is known, and never message it. "
  "Retrospective assignment produces a number worse than no number.",
  "Expire partial data on a short clock. A table of half-finished forms is a data question you "
  "did not intend to take on.",
  "When complaints appear, tighten the basis rather than softening the wording. The message is "
  "almost never the problem."],
))
