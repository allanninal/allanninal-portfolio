"""Day 99 -- 2026-08-01 -- Form spam filter."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "form-spam-filter"
NAME = "Form spam filter"

SPEC = {
 "slug": SLUG, "date": "2026-08-01", "name": NAME,
 "tagline": ("Stops the bot submissions without a CAPTCHA, keeps every borderline one where a "
             "person can find it, and never silently deletes a real enquiry -- because a lost "
             "lead costs more than a hundred spam messages."),
 "lede": ("A small system that scores contact form submissions using cheap structural signals "
          "first and a model only for the genuinely ambiguous ones, sends the obvious enquiries "
          "straight through, and holds the rest where somebody can see them. It never deletes "
          "anything. Seven posts on the same system -- one diagram at a time -- with a cost "
          "breakdown and an engineering reference at the end."),
 "keywords": ["form spam", "lead capture", "CAPTCHA", "honeypot", "filtering", "serverless"],
 "icons": ["form", "filter", "shield"],
 "faq": [
  ("What is a form spam filter?",
   "A small serverless system that scores contact form submissions, delivers the obvious "
   "enquiries immediately, holds the ambiguous ones in a review queue, and never deletes "
   "anything. It is asymmetric on purpose: a missed lead costs far more than a spam message."),
  ("Why not a CAPTCHA?",
   "Because a CAPTCHA taxes every genuine visitor to stop a problem caused by a small number of "
   "bots, and the measurable drop in form completions is usually larger than the spam volume. "
   "The structural signals in this design catch most bots and cost a visitor nothing."),
  ("Does it delete spam?",
   "No. Everything is retained, in one of three places. Obvious spam goes to a quarantine "
   "nobody reads day to day but which can be searched when somebody says they submitted a form "
   "and heard nothing."),
  ("How much does it use a model?",
   "Only for the middle band. The cheap signals classify the large majority for free, and the "
   "model sees perhaps one submission in ten -- which keeps it affordable and keeps the "
   "decisions mostly deterministic."),
  ("What does it cost to run?",
   "A couple of dollars a month for a few hundred submissions. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "form-spam-filter-on-aws",
 "title": "A form spam filter on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Scores submissions with cheap structural signals first, holds the ambiguous ones for "
          "a person, and never deletes anything. AWS, about $2 a month."),
 "og": ("A lost lead costs more than a hundred spam messages. Every decision in this design "
        "follows from that asymmetry."),
 "abstract": ("The whole system on one page -- cheap signals, a narrow model band and three "
              "destinations -- with the cost asymmetry that shapes every threshold."),
 "lede": ("A contact form with no protection fills with rubbish, and the usual response is a "
          "CAPTCHA. That trades a visible cost on every genuine visitor against an invisible one "
          "on nobody, and the measurable drop in completions is frequently worse than the spam. "
          "This post walks through a small system that gets most of the benefit without asking "
          "your customers to identify traffic lights."),
 "tags": ["form spam", "lead capture", "CAPTCHA", "honeypot", "filtering", "serverless"],
 "takeaways": [
  "A missed lead costs far more than a spam message. Every threshold follows from that.",
  "Cheap structural signals classify most submissions for free, before any model runs.",
  "Three destinations: inbox, review queue, quarantine. Nothing is deleted.",
  "No CAPTCHA. The visible cost falls on genuine visitors and the spam adapts anyway.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "The form", "sub": ["no CAPTCHA"], "icon": "form"},
      {"title": "Signals", "sub": ["honeypot, timing,", "structure"], "icon": "shield"},
      {"title": "Whoever answers", "sub": ["inbox, plus a queue"], "icon": "person"}],
    "inside": [
      {"title": "Cheap scorer", "sub": ["free signals,", "most decided here"], "icon": "filter"},
      {"title": "Model band", "sub": ["only the ambiguous", "middle"], "icon": "model"},
      {"title": "Router", "sub": ["inbox, review,", "quarantine"], "icon": "branch"}],
    "edges": [{"from": 0, "to": 0, "label": "submissions"},
              {"from": 1, "to": 1, "label": "structural evidence"},
              {"from": 2, "to": 2, "label": "one of three places", "up": True}],
    "note": "Nothing is deleted. The worst outcome for a real enquiry is a two-hour delay."}),
   "Three things outside the account, three pieces inside it. The narrow model band in the middle "
   "is what keeps this both cheap and mostly deterministic.",
   "System: submissions scored cheaply, routed to one of three places",
   "Three boxes across the top sit outside the AWS account. On the left, The form, with no "
   "CAPTCHA. In the middle, Signals: the honeypot, timing and structural evidence collected with "
   "the submission. On the right, Whoever answers: their inbox plus a review queue. Each connects "
   "by an arrow to the AWS account container below. Submissions flow down into the account. "
   "Structural evidence feeds in. Each submission goes back out to one of three places. Inside "
   "the AWS account are three components in a row. On the left, the Cheap scorer, using free "
   "signals, where most submissions are decided. In the middle, the Model band, used only for the "
   "ambiguous middle. On the right, the Router, sending to the inbox, the review queue or "
   "quarantine. A note at the bottom says nothing is deleted and the worst outcome for a real "
   "enquiry is a two-hour delay."),
  ("h3", "The asymmetry"),
  ("p", "A small business's contact form produces perhaps forty genuine enquiries a month and "
        "four hundred spam messages. The genuine ones are worth, on average, a meaningful "
        "fraction of a job. The spam costs about four seconds each to delete."),
  ("p", "So the arithmetic is not close: deleting one real enquiry to save four hundred deletions "
        "is a bad trade by an enormous margin. Every threshold in this system is set from that, "
        "which is why the aggressive-looking decision &mdash; quarantine &mdash; still keeps "
        "everything and is searchable."),
  ("h3", "What runs on every submission (the inside)"),
  ("ul", [
   "<strong>The cheap scorer.</strong> Half a dozen structural signals that cost nothing: a "
   "honeypot field, how long the form was open, whether the message contains links, whether the "
   "fields were filled in a plausible order. Part 2 covers each and how much each is worth.",
   "<strong>The model band.</strong> For the submissions the cheap signals cannot place, one "
   "call asking a narrow question: is this a person describing a need, or a template? Part 3 is "
   "about keeping that band small.",
   "<strong>The router.</strong> Three destinations. Confident enquiry goes to the inbox "
   "immediately. Ambiguous goes to a review queue that somebody glances at twice a day. "
   "Confident spam goes to quarantine, retained and searchable.",
  ]),
  ("h2", "One submission, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Submitted", "sub": ["no CAPTCHA"], "icon": "form"},
      {"title": "Cheap signals", "sub": ["~85% decided"], "icon": "filter"},
      {"title": "Model", "sub": ["the other 15%"], "icon": "model"},
      {"title": "Routed", "sub": ["one of three places"], "icon": "branch"},
      {"title": "Answered", "sub": ["or found later"], "icon": "person"}],
    "title": "ONE SUBMISSION, END TO END",
    "note": "The second box is where the cost savings and most of the accuracy both come from."}),
   "The same system as one line. Deciding most submissions with free signals is what makes the "
   "model band affordable enough to be careful in.",
   "One form submission from arrival to answer, in five stages",
   "A horizontal row of five boxes joined by arrows. Submitted: with no CAPTCHA. Cheap signals: "
   "about eighty-five per cent are decided here. Model: the remaining fifteen per cent. Routed: "
   "to one of three places. Answered: or found later. A note says the second box is where the "
   "cost savings and most of the accuracy both come from."),
  ("h2", "In plain words"),
  ("p", "Somebody fills in the contact form asking about a bathroom. They took ninety seconds, "
        "left the hidden field empty, filled the fields in a sensible order, and wrote three "
        "sentences with no links in them. Every cheap signal says person, so it goes straight to "
        "the inbox with no model call and no delay."),
  ("p", "A minute later a bot submits. It filled the hidden field, completed the form in under a "
        "second, and the message is two hundred words with four links about search engine "
        "optimisation services. Every cheap signal says bot, so it goes to quarantine, again "
        "without a model call."),
  ("p", "The interesting one arrives on Tuesday: two lines, no links, a plausible name, a "
        "free-mail address, filled in eleven seconds. It might be somebody in a hurry on a phone "
        "or it might be a better bot. The cheap signals genuinely cannot say, so one model call "
        "asks whether it reads like somebody describing a specific need. It says probably, with "
        "middling confidence, so it goes to the review queue &mdash; and somebody glancing at "
        "that queue after lunch spends two seconds deciding it is a real job."),
  ("callout", "Design rules that shaped every decision", [
   "Never delete. Quarantine is retained and searchable, because \"I filled in your form and "
   "heard nothing\" is a conversation that happens.",
   "No CAPTCHA. The cost falls entirely on genuine visitors and bots solve them anyway.",
   "Cheap signals first, always. They are free, deterministic, and decide most submissions.",
   "Keep the model band narrow. It is the expensive part and the least predictable part.",
   "When uncertain, hold rather than drop. A two-hour delay is a much cheaper error than a lost "
   "lead.",
   "Every decision is recorded with the signals behind it, so the thresholds can be tuned from "
   "evidence.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Spam filtering has a well-known failure mode: it works, everybody stops thinking about "
        "it, and six months later somebody discovers a folder of real enquiries. The reason is "
        "always the same &mdash; a filter confident enough to delete, and nobody watching the "
        "false positive rate because false positives are invisible by construction."),
  ("p", "So this design refuses the deletion. Everything is kept, the ambiguous band goes to a "
        "human queue rather than a coin flip, and the quarantine is searchable by name and email "
        "so that the one conversation that reveals a false positive can actually be resolved. It "
        "is a slightly worse filter and a considerably better business decision."),
  ("p", "The next four posts walk through each piece: the cheap signals, the model band, how a "
        "borderline reaches a person, and how the thresholds get tuned. One diagram per post, a "
        "cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-the-cheap-signals-work",
 "title": "How the cheap signals work",
 "nav": "How signals work",
 "read": 5, "words": 760,
 "desc": ("Six structural signals that cost nothing, how much each is actually worth, and the "
          "two that people implement wrongly."),
 "og": ("A honeypot, a timer and four structural checks decide most submissions for free. Two of "
        "them are implemented wrongly almost everywhere."),
 "abstract": ("Six structural signals that cost nothing to collect, what each is actually worth, "
              "and the two that are commonly implemented in a way that catches real people."),
 "lede": ("The cheap signals do most of the work, and they are cheap in two senses: they cost "
          "nothing to compute and they cost the visitor nothing. Two of the six are frequently "
          "implemented in a way that quietly rejects real people, which is worth being careful "
          "about."),
 "tags": ["form spam", "honeypot", "bot detection", "web forms", "accessibility", "serverless"],
 "takeaways": [
  "Six signals: honeypot, fill time, field order, link count, field consistency, and repetition.",
  "The honeypot must be hidden accessibly, or screen reader users fill it in.",
  "Fill time needs a floor and no ceiling. A slow submission is not suspicious.",
  "Link count is the strongest single content signal and needs no model.",
  "Repetition across submissions catches the bots that beat everything else.",
 ],
 "blocks": [
  ("h2", "The six"),
  ("table", ["Signal", "What it catches", "Worth"], [
   ["Honeypot filled", "Naive bots that fill every field", "Very strong; near-certain spam"],
   ["Fill time under 2s", "Automated submission", "Strong, with a floor only"],
   ["Field order", "Scripted fills that do not tab naturally", "Moderate"],
   ["Links in the message", "Almost all commercial spam", "Strong"],
   ["Field inconsistency", "A name in the phone field, etc.", "Moderate"],
   ["Repetition", "The same body from many addresses", "Very strong, and slow to trigger"],
  ]),
  ("p", "Between them these classify the large majority of submissions confidently in one "
        "direction or the other, at a computational cost of essentially zero and a visitor cost "
        "of exactly zero."),
  ("h2", "The two that go wrong"),
  ("fig", ("chain", {
    "entry": {"title": "A submission", "sub": ["with its signals"], "icon": "form"},
    "steps": [
      {"title": "Honeypot filled?", "sub": ["and hidden how?"], "icon": "branch",
       "side": {"title": "Hidden with CSS", "sub": ["never with an", "aria-hidden trick"],
                "icon": "shield"},
       "exit": {"title": "Almost certainly a bot", "sub": ["quarantine"], "icon": "stop",
                "label": "filled"}},
      {"title": "Filled in under 2s?", "sub": ["a floor, not a window"], "icon": "branch",
       "exit": {"title": "Strong spam signal", "sub": ["combine, do not decide"], "icon": "counter",
                "label": "yes"}},
      {"title": "Links in the body?", "sub": ["count them"], "icon": "branch",
       "exit": {"title": "Strong spam signal", "sub": ["two or more"], "icon": "link",
                "label": "yes"}},
      {"title": "Combine the score", "sub": ["weighted, not counted"], "icon": "filter"},
      {"title": "Confident, or not", "sub": ["the model band is what is left"], "icon": "branch"}],
    "note": "Only the honeypot decides alone. Everything else contributes to a score."}),
   "How the cheap signals combine. Only one of them is trusted on its own, and the rest "
   "contribute weight rather than making decisions.",
   "How the six cheap spam signals are combined",
   "A vertical chain of five steps entered by a box labelled A submission, with its signals. Step "
   "one asks whether the honeypot was filled, and how it was hidden, noting it must be hidden "
   "with CSS and never with an aria-hidden trick; filled exits to Almost certainly a bot, sent to "
   "quarantine. Step two asks whether it was filled in under two seconds, using a floor rather "
   "than a window; yes exits to a strong spam signal that combines rather than decides. Step "
   "three asks whether there are links in the body, counting them; two or more exits to another "
   "strong spam signal. Step four combines the score, weighted rather than counted. Step five is "
   "confident or not, and what is left is the model band. A note says only the honeypot decides "
   "alone and everything else contributes to a score."),
  ("h3", "The honeypot and screen readers"),
  ("p", "A honeypot is a form field that is invisible to people and visible to naive bots. The "
        "common implementation hides it with <code>display: none</code>, which is fine, or with "
        "<code>type=\"hidden\"</code>, which most bots skip, or by positioning it off-screen "
        "without hiding it from assistive technology &mdash; which is where it goes wrong."),
  ("p", "A screen reader user encountering an off-screen labelled field will fill it in, because "
        "it is announced as a form field like any other. They then get silently classified as a "
        "bot, and there is no way for them to know. The fix is one attribute: hide it from the "
        "accessibility tree as well as visually, and label it something that discourages "
        "autofill."),
  ("h3", "Fill time needs a floor and no ceiling"),
  ("p", "Under two seconds is essentially impossible for a person typing a message and is a "
        "strong bot signal. The tempting mirror &mdash; treating a very long fill time as "
        "suspicious &mdash; is wrong, because a real person opens the form, gets distracted, "
        "comes back forty minutes later and submits."),
  ("p", "So the check is a floor only. Any ceiling at all will misclassify somebody's genuine "
        "enquiry, and a business that has ever had a customer fill in a form while on the phone "
        "to somebody has already seen the case."),
  ("h2", "Repetition"),
  ("fig", ("strip", {
    "stages": [
      {"title": "One submission", "sub": ["nothing unusual"], "icon": "form"},
      {"title": "Same body", "sub": ["different name, address"], "icon": "search"},
      {"title": "Third time", "sub": ["within a week"], "icon": "counter"},
      {"title": "Fingerprint", "sub": ["normalised body hash"], "icon": "key"},
      {"title": "All three quarantined", "sub": ["including retrospectively"], "icon": "retry"}],
    "title": "REPETITION CATCHES THE GOOD BOTS",
    "note": "A bot good enough to beat every other signal still sends the same message twice."}),
   "The signal that catches sophisticated bots. Anything that passes the structural checks is "
   "usually running at volume, and volume is itself detectable.",
   "How repeated message bodies are detected across submissions",
   "A horizontal row of five boxes. One submission: nothing unusual. Same body: with a different "
   "name and address. Third time: within a week. Fingerprint: a normalised body hash. All three "
   "quarantined: including retrospectively. A note says a bot good enough to beat every other "
   "signal still sends the same message twice."),
  ("p", "The retrospective part matters. When the third copy of a message arrives and reveals the "
        "pattern, the first two have already gone to somebody's inbox. Moving them to quarantine "
        "and telling the recipient which ones moved is better than leaving them, and it is the "
        "one case where the system reclassifies something after delivery."),
  ("p", "Normalising the body before hashing &mdash; lowercasing, stripping punctuation and "
        "whitespace, removing the parts that vary like a name or a URL &mdash; is what makes this "
        "work against bots that template their messages."),
  ("p", "Next: the narrow model band."),
 ],
},
{
 "slug": "how-the-model-band-stays-narrow",
 "title": "How the model band stays narrow",
 "nav": "How the band works",
 "read": 5, "words": 740,
 "desc": ("What the model is asked, why it is asked about only one submission in ten, and the "
          "question it is deliberately not asked."),
 "og": ("One narrow question about one submission in ten. The band is small on purpose, because "
        "a deterministic decision is worth more than a marginally better one."),
 "abstract": ("What the model is actually asked, why only about one submission in ten reaches "
              "it, the question it is deliberately not asked, and what it does with the answer."),
 "lede": ("It would be straightforward to send every submission to a model and get a slightly "
          "better classifier. It would also cost ten times as much, make every decision "
          "unpredictable, and remove the ability to explain why something was filtered. The band "
          "is narrow on purpose."),
 "tags": ["form spam", "AWS Bedrock", "classification", "cost control", "determinism",
          "serverless"],
 "takeaways": [
  "About one submission in ten reaches the model; the rest are decided for free.",
  "One question: does this read like a person describing a specific need?",
  "It is never asked whether to deliver. That decision belongs to the router and the thresholds.",
  "Its answer moves a score; it does not set an outcome.",
  "A model failure degrades to the review queue, never to quarantine.",
 ],
 "blocks": [
  ("h2", "Who reaches the model"),
  ("fig", ("chain", {
    "entry": {"title": "A cheap score", "sub": ["from Part 2"], "icon": "counter"},
    "steps": [
      {"title": "Confidently spam?", "sub": ["honeypot, or a high score"], "icon": "branch",
       "exit": {"title": "Quarantine", "sub": ["no model call"], "icon": "stop", "label": "yes"}},
      {"title": "Confidently a person?", "sub": ["clean on every signal"], "icon": "branch",
       "exit": {"title": "Inbox", "sub": ["no model call"], "icon": "check", "label": "yes"}},
      {"title": "The middle", "sub": ["about 1 in 10"], "icon": "filter"},
      {"title": "One question", "sub": ["is this a person", "with a specific need?"], "icon": "model",
       "exit": {"title": "Model failed", "sub": ["review queue, always"], "icon": "person",
                "label": "error"}},
      {"title": "Adjust the score", "sub": ["then route"], "icon": "branch"}],
    "note": "A model error routes to a human, never to quarantine. Failure must not lose a lead."}),
   "Who actually reaches the model. Both confident paths avoid it entirely, and its failure mode "
   "is deliberately the safe direction.",
   "How submissions are selected for a model call",
   "A vertical chain of five steps entered by a box labelled A cheap score, from Part 2. Step one "
   "asks whether it is confidently spam, meaning the honeypot was filled or the score is high; "
   "yes exits to Quarantine with no model call. Step two asks whether it is confidently a person, "
   "clean on every signal; yes exits to the Inbox with no model call. Step three is the middle, "
   "about one submission in ten. Step four asks one question: is this a person with a specific "
   "need; a model error exits to the review queue, always. Step five adjusts the score and then "
   "routes. A note says a model error routes to a human and never to quarantine, because failure "
   "must not lose a lead."),
  ("h3", "The question"),
  ("p", "Narrow and specific: does this read like a person describing a particular need, or like "
        "a template sent to many recipients? That is a genuinely hard question for a rule and an "
        "easy one for a model, and it is the only thing it is asked."),
  ("p", "The prompt carries the message body and nothing else &mdash; not the name, not the email "
        "address, not the IP or the country. Those are all things a rule can weigh, and including "
        "them in a model prompt invites it to form views about people based on where they are or "
        "what their address looks like, which is both unfair and unreliable."),
  ("h3", "The question it is not asked"),
  ("p", "It is never asked whether to deliver the submission. That sounds like a distinction "
        "without a difference and it is the whole design: a model that returns \"deliver\" or "
        "\"filter\" has made a business decision, and the thresholds that turn evidence into a "
        "decision are then invisible and untunable."),
  ("p", "A model that returns \"this reads specific, confidence 0.7\" contributes evidence, and "
        "the routing rule that turns 0.7 into a destination is a number in a config that somebody "
        "can change when the review queue gets too long."),
  ("h2", "Failing safe"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Model times out", "sub": ["or throttles"], "icon": "alarm"},
      {"title": "No score", "sub": ["nothing to combine"], "icon": "search"},
      {"title": "Do not guess", "sub": ["either direction"], "icon": "stop"},
      {"title": "Review queue", "sub": ["a person decides"], "icon": "person"},
      {"title": "Cost", "sub": ["a two-hour delay"], "icon": "clock"}],
    "title": "WHAT HAPPENS WHEN THE MODEL FAILS",
    "note": "Defaulting to quarantine on error would lose leads during a Bedrock incident."}),
   "The failure path. Choosing the human queue rather than either automatic outcome means a "
   "provider incident costs a delay rather than a lead.",
   "How a model failure is handled in the spam filter",
   "A horizontal row of five boxes. Model times out: or is throttled. No score: there is nothing "
   "to combine. Do not guess: in either direction. Review queue: a person decides. Cost: a "
   "two-hour delay. A note says defaulting to quarantine on error would lose leads during a "
   "Bedrock incident."),
  ("p", "The tempting shortcut is to default to the cheap score alone when the model is "
        "unavailable, and that is exactly wrong for the submissions in this band: they reached "
        "the model precisely because the cheap score could not place them. Falling back to it is "
        "falling back to the thing that already said it did not know."),
  ("h3", "What it costs to keep the band narrow"),
  ("p", "About one submission in ten reaching a model means a business with four hundred and "
        "forty submissions a month makes forty-four calls, which is a few cents. Sending all four "
        "hundred and forty would be a few tens of cents &mdash; still trivial in absolute terms, "
        "and it would make ninety per cent of the decisions less predictable for no measurable "
        "gain in accuracy, because those ninety per cent were already unambiguous."),
  ("p", "The reason to keep the band narrow is not the money. It is that a filter whose decisions "
        "are mostly deterministic can be explained, tested and tuned, and one whose decisions all "
        "come from a model cannot."),
  ("p", "Next: what happens to the ambiguous ones."),
 ],
},
{
 "slug": "how-a-borderline-reaches-a-person",
 "title": "How a borderline reaches a person",
 "nav": "How review works",
 "read": 5, "words": 730,
 "desc": ("The review queue that takes ninety seconds a day, why it is a queue rather than a "
          "folder, and the quarantine search that resolves the awkward conversation."),
 "og": ("A review queue only works if it takes ninety seconds. Twelve items with the reason "
        "shown, two buttons each, twice a day."),
 "abstract": ("The review queue that has to take ninety seconds a day, why it is a queue rather "
              "than a folder, and the quarantine search that resolves the conversation every "
              "business eventually has."),
 "lede": ("A review queue is the part of this design most likely to be abandoned, and it is "
          "abandoned for a completely predictable reason: it takes too long. Everything here is "
          "about the ninety seconds."),
 "tags": ["form spam", "review queues", "triage", "lead capture", "operations", "serverless"],
 "takeaways": [
  "The queue is a batched message twice a day, not a place somebody has to visit.",
  "Each item shows the message and the reason it is held, not a score.",
  "Two buttons: it is real, or it is spam. Nothing else.",
  "An unreviewed item is delivered after four hours rather than held indefinitely.",
  "Quarantine is searchable by name and address, which is what resolves the awkward call.",
 ],
 "blocks": [
  ("h2", "Twice a day, ninety seconds"),
  ("fig", ("chain", {
    "entry": {"title": "A held submission", "sub": ["from the model band"], "icon": "filter"},
    "steps": [
      {"title": "Wait for the batch", "sub": ["11am and 4pm"], "icon": "clock",
       "exit": {"title": "Four hours passed?", "sub": ["deliver it anyway"], "icon": "retry",
                "label": "timeout"}},
      {"title": "One message", "sub": ["all held items"], "icon": "email"},
      {"title": "Message and reason", "sub": ["not a score"], "icon": "doc"},
      {"title": "Two buttons each", "sub": ["real, or spam"], "icon": "branch"},
      {"title": "Routed and recorded", "sub": ["the answer tunes the filter"], "icon": "log"}],
    "note": "The timeout is the safety net: an unreviewed enquiry is delivered, not lost."}),
   "How held submissions reach a person. The four-hour timeout means the review queue failing is "
   "a source of spam rather than a source of lost leads.",
   "How a held form submission reaches a person for review",
   "A vertical chain of five steps entered by a box labelled A held submission, from the model "
   "band. Step one waits for the batch at eleven in the morning and four in the afternoon; if "
   "four hours pass first it exits to deliver it anyway. Step two sends one message containing "
   "all held items. Step three shows the message and the reason it is held, rather than a score. "
   "Step four gives two buttons on each item: real, or spam. Step five routes and records, and "
   "the answer tunes the filter. A note says the timeout is the safety net, because an unreviewed "
   "enquiry is delivered rather than lost."),
  ("h3", "Why batched"),
  ("p", "A held submission that generates its own notification produces eight interruptions a day "
        "and gets muted. One message at eleven and one at four contains everything, takes ninety "
        "seconds, and is a thing somebody actually does."),
  ("p", "The four-hour timeout underneath it is what makes the batching safe. If nobody opens the "
        "eleven o'clock message, its items are delivered to the inbox at three regardless. The "
        "failure mode of the review queue is therefore some spam getting through, which is the "
        "cheap error."),
  ("h3", "The reason, not the score"),
  ("p", "\"Held because: no links, but submitted in 11 seconds and the message is two lines\" is "
        "something a person can weigh in a second. \"Spam score 0.62\" is not, and it also invites "
        "somebody to start reasoning about the number rather than reading the message."),
  ("h2", "The quarantine search"),
  ("p", "Every business running a contact form eventually gets the phone call: I filled in your "
        "form last week and never heard back. Without a searchable quarantine that conversation "
        "has no resolution and ends with an apology and a suspicion."),
  ("fig", ("strip", {
    "stages": [
      {"title": "'I filled in your form'", "sub": ["last Tuesday"], "icon": "phone"},
      {"title": "Search quarantine", "sub": ["by name or address"], "icon": "search"},
      {"title": "Found it", "sub": ["with why it was held"], "icon": "doc"},
      {"title": "Deliver it now", "sub": ["and mark it real"], "icon": "check"},
      {"title": "The filter learns", "sub": ["that pattern loosens"], "icon": "retry"}],
    "title": "THE CONVERSATION THAT REVEALS A FALSE POSITIVE",
    "note": "False positives are invisible by construction. This is the only way you find them."}),
   "The one path by which a false positive becomes visible. Without a searchable quarantine there "
   "is no way to discover that the filter is wrong.",
   "How a quarantined genuine enquiry is found and recovered",
   "A horizontal row of five boxes. Somebody says they filled in your form last Tuesday. Search "
   "quarantine: by name or address. Found it: with the reason it was held. Deliver it now: and "
   "mark it real. The filter learns: that pattern loosens. A note says false positives are "
   "invisible by construction and this is the only way you find them."),
  ("p", "That last box is the reason to record it rather than just fix the individual case. A "
        "quarantined message marked real afterwards is the single most valuable training signal "
        "the system produces, because it is a confirmed false positive with the signals that "
        "caused it attached."),
  ("h3", "How long quarantine is kept"),
  ("p", "Ninety days is a reasonable default and it should be a deliberate decision rather than a "
        "forever. The messages are small, but a quarantine that is never emptied is a growing "
        "store of unsolicited content that somebody eventually has to think about under a "
        "retention policy."),
  ("p", "Anything marked real is moved out of quarantine and kept with the genuine enquiries, so "
        "the expiry only ever removes things a person confirmed were spam or never looked at."),
  ("p", "Next: how the thresholds get tuned."),
 ],
},
{
 "slug": "how-the-filter-stays-tuned",
 "title": "How the filter stays tuned",
 "nav": "How it stays tuned",
 "read": 5, "words": 720,
 "desc": ("The two error rates, why only one of them is measurable, and the monthly numbers that "
          "say whether the thresholds need moving."),
 "og": ("False positives are invisible by construction, so the filter is tuned by watching the "
        "review queue rather than by watching accuracy."),
 "abstract": ("Why only one of the two error rates is measurable, what the review queue's size "
              "tells you, and the monthly numbers that say whether the thresholds need moving."),
 "lede": ("A spam filter's accuracy cannot be measured, and understanding why is what makes it "
          "possible to tune one honestly. You can count what you caught. You cannot count what "
          "you wrongly caught, because nobody tells you."),
 "tags": ["form spam", "tuning", "false positives", "metrics", "reporting", "serverless"],
 "takeaways": [
  "False negatives are visible: spam in the inbox. False positives are not.",
  "The review queue's size is the best available proxy for whether thresholds are right.",
  "A confirmed false positive is the most valuable signal available and is rare.",
  "Tune towards a review queue of about ten items a day, not towards accuracy.",
  "Never tighten a threshold without checking what it would have caught historically.",
 ],
 "blocks": [
  ("h2", "Only one error is visible"),
  ("fig", ("chain", {
    "entry": {"title": "Two kinds of error", "sub": ["not symmetric"], "icon": "branch"},
    "steps": [
      {"title": "Spam in the inbox", "sub": ["somebody sees it"], "icon": "alarm",
       "exit": {"title": "Countable", "sub": ["one tap to report"], "icon": "counter",
                "label": "visible"}},
      {"title": "Real in quarantine", "sub": ["nobody sees it"], "icon": "stop",
       "exit": {"title": "Invisible", "sub": ["unless somebody rings"], "icon": "phone",
                "label": "hidden"}},
      {"title": "So do not tune on accuracy", "sub": ["you cannot measure it"], "icon": "search"},
      {"title": "Tune on queue size", "sub": ["a measurable proxy"], "icon": "chart"},
      {"title": "And on confirmed misses", "sub": ["rare and decisive"], "icon": "key"}],
    "note": "Any claim about this filter's accuracy is a claim about the half you can see."}),
   "The asymmetry that governs tuning. One error type announces itself and the other does not, so "
   "the tuning target has to be something other than accuracy.",
   "Why only one of a spam filter's two error types is measurable",
   "A vertical chain of five steps entered by a box labelled Two kinds of error, not symmetric. "
   "Step one is spam in the inbox, which somebody sees; it exits to Countable, needing one tap to "
   "report. Step two is a real enquiry in quarantine, which nobody sees; it exits to Invisible, "
   "unless somebody rings. Step three concludes: do not tune on accuracy, because you cannot "
   "measure it. Step four tunes on queue size, a measurable proxy. Step five also tunes on "
   "confirmed misses, which are rare and decisive. A note says any claim about this filter's "
   "accuracy is a claim about the half you can see."),
  ("h3", "Tuning on the queue"),
  ("p", "The review queue is the tuning instrument. Too long and somebody stops reading it, which "
        "means the four-hour timeout starts delivering everything and the filter has "
        "effectively stopped. Too short and the thresholds are confident about things they should "
        "not be, which is where invisible false positives live."),
  ("p", "About ten items a day is the target. That is ninety seconds of somebody's attention, "
        "twice a day, and it is a band wide enough that genuinely ambiguous submissions land in "
        "it rather than being decided by a threshold."),
  ("h2", "The monthly numbers"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Submissions", "sub": ["441"], "icon": "form"},
      {"title": "To the inbox", "sub": ["38"], "icon": "check"},
      {"title": "Reviewed", "sub": ["61, of which 9 real"], "icon": "person"},
      {"title": "Quarantined", "sub": ["342"], "icon": "stop"},
      {"title": "Reported as spam", "sub": ["2, from the inbox"], "icon": "alarm"}],
    "title": "ONE MONTH OF A CONTACT FORM",
    "note": "The third number is the one to steer by. Two per day reviewed is about right."}),
   "A month of submissions in five numbers. The reviewed count and the proportion of it that "
   "turns out to be real are what indicate whether the middle band is set correctly.",
   "One month of form submissions summarised in five numbers",
   "A horizontal row of five boxes. Submissions: four hundred and forty-one. To the inbox: "
   "thirty-eight. Reviewed: sixty-one, of which nine were real. Quarantined: three hundred and "
   "forty-two. Reported as spam: two, from the inbox. A note says the third number is the one to "
   "steer by, and about two a day reviewed is right."),
  ("p", "Nine real submissions out of sixty-one reviewed is a healthy band: it means the middle "
        "genuinely contains a mix, which is what a middle should contain. If it were sixty out of "
        "sixty-one, the band is catching things the cheap signals should have passed; if it were "
        "one, the band is catching things they should have quarantined."),
  ("h3", "Two reported from the inbox"),
  ("p", "That is the visible error rate and it is deliberately not zero. A filter tuned to let "
        "nothing through is tuned tightly enough to be quarantining real enquiries, and two "
        "obvious spam messages a month reaching an inbox is a much cheaper cost than whatever "
        "tightening would be required to remove them."),
  ("h2", "Changing a threshold"),
  ("callout", "Before tightening anything", [
   "<strong>Replay it.</strong> Every submission and its signals are stored, so a proposed "
   "threshold can be run over the last three months before it goes live.",
   "<strong>Look at what it would have caught.</strong> Not the count &mdash; the actual "
   "messages. A tightening that would have quarantined two real enquiries is not worth the "
   "eleven spam it also catches.",
   "<strong>Change one thing.</strong> Two threshold changes at once means the next month's "
   "numbers cannot attribute the difference.",
   "<strong>Write down why.</strong> Six months later, \"why is the fill-time floor three "
   "seconds\" is a question somebody will ask, and the answer should not be lost.",
  ]),
  ("p", "The replay is what makes tuning safe, and it is only possible because every submission "
        "is retained with its signals. That is the same structural decision as keeping raw rows in "
        "the search reporter and storing every sample in the speed watcher: keep the input, and "
        "changing the processing becomes cheap and reversible."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="submission",
 volumes=[(150, "150 submissions"), (450, "450 submissions"), (2000, "2,000 submissions")],
 read_each=0.0004, msgs_each=0.3,
 lede=("Only about one submission in ten reaches a model, which is what keeps this cheap even "
       "when the spam volume is high. Four hundred and fifty submissions a month is a small "
       "business with a busy contact form. Here is where each cent goes."),
 takeaway_extra=("Nine in ten submissions are decided by free structural signals and never touch "
                 "a model."),
 risks=[
  "<strong>Sending everything to the model.</strong> Ten times the read cost for no measurable "
  "accuracy gain, because the nine in ten were already unambiguous, and it makes every decision "
  "unexplainable.",
  "<strong>Retrying a model call on a bot flood.</strong> A spam wave of ten thousand "
  "submissions in an hour, each retried three times, is the one way this bill becomes "
  "interesting. Rate-limit the model band per hour and route the overflow to review.",
  "<strong>Log retention left at never.</strong> Every submission logs its signals, and at "
  "volume that is the largest line within a year.",
 ],
 per_unit_note=("The read cost is one small call on roughly one submission in ten, with a short "
                "prompt carrying only the message body. Everything else on this bill is the "
                "fixed band."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="fs",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the one table, the signal collection, and the narrow model band."),
 outside=[
  {"title": "The form", "sub": ["CloudFront + S3"], "icon": "form"},
  {"title": "Thresholds", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["enquiries, review batch"], "icon": "email"}],
 inside=[
  {"title": "Function URL + SQS", "sub": ["submit,", "one scoring queue"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["submit, score, review"], "icon": "lambda"},
  {"title": "DynamoDB x1", "sub": ["submissions"], "icon": "database"}],
 note="us-east-1. One account. Nothing in this system deletes a submission.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The form, served as static files from S3 "
  "behind CloudFront. Thresholds, read through the Google Sheets API read-only. And SES "
  "outbound, carrying delivered enquiries and the review batch. Inside the account, three "
  "groups. A Function URL for submissions and SQS carrying one scoring queue. Three Lambda "
  "functions named submit, score and review. And a single DynamoDB table named submissions. A "
  "note gives the region as us-east-1, one account, and states that nothing in this system "
  "deletes a submission."),
 functions=[
  ["<code>fs-submit</code>", "Function URL",
   "Accepts the post, captures the signals, enqueues; always returns success",
   "10s / 512&nbsp;MB"],
  ["<code>fs-score</code>", "SQS scoring queue",
   "Cheap signals, then one Bedrock call for the middle band only", "20s / 512&nbsp;MB"],
  ["<code>fs-review</code>", "EventBridge 11am/4pm + Function URL",
   "Builds the review batch; handles the two buttons; the 4-hour timeout",
   "20s / 512&nbsp;MB"]],
 roles=[
  ["<code>fs-submit-role</code>", "<code>dynamodb:PutItem</code>, <code>sqs:SendMessage</code>",
   "The submissions table; the scoring queue"],
  ["<code>fs-score-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>dynamodb:UpdateItem</code>, "
   "<code>ses:SendEmail</code>",
   "One model arn; submissions; one verified identity"],
  ["<code>fs-review-role</code>",
   "<code>dynamodb:Query</code>/<code>UpdateItem</code>, <code>ses:SendEmail</code>",
   "Submissions; one verified identity"]],
 tables=[
  ("Table: submissions",
   "PK   submission_id     S   sub_2026_08_01_7f2a\n"
   "     received_at       S   2026-08-01T10:14:02Z\n"
   "     fields            M   {name, email, phone, message}\n"
   "     signals           M   {honeypot, fill_ms, field_order, links,\n"
   "                            consistency, body_hash}\n"
   "     cheap_score       N   0.62\n"
   "     model_called      BOOL true\n"
   "     model_specific    N   0.71   -- null if not called\n"
   "     destination       S   inbox | review | quarantine\n"
   "     reviewed_as       S   real | spam  -- set by a person\n"
   "     delivered_at      S   set when it reaches the inbox\n"
   "     ttl               N   quarantine: +90 days; real: none\n\n"
   "GSI  body-hash-index     PK body_hash      -- the repetition check\n"
   "GSI  destination-index   PK destination, SK received_at  -- the review batch\n"
   "GSI  email-index         PK email          -- the quarantine search\n\n"
   "Every submission is stored with its signals, which is what makes threshold\n"
   "replay possible: a proposed change can be run over three months of real\n"
   "traffic before it goes live.")],
 inbound=[
  "The <strong>form</strong> is static files in S3 behind CloudFront, posting to a Function URL. "
  "There is no CAPTCHA and no third-party script.",
  "<strong>The honeypot field</strong> is hidden with CSS and removed from the accessibility "
  "tree, with <code>autocomplete=\"off\"</code> and a name browsers will not autofill. Getting "
  "this wrong silently classifies screen reader users as bots.",
  "<strong>Fill time</strong> is measured from a timestamp written into the page at render, "
  "signed so it cannot be forged, with a floor and deliberately no ceiling.",
  "<strong>The endpoint always returns success</strong>, whatever the classification. Telling a "
  "bot it was filtered is telling a bot how to adapt, and telling a person their genuine enquiry "
  "was rejected is worse."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "asked one question about roughly one submission in ten.",
  "<strong>The prompt carries the message body only.</strong> Not the name, the address, the IP "
  "or the country &mdash; those are rule inputs, and putting them in a model prompt invites "
  "judgements about people based on where they are.",
  "<strong>Output is a JSON schema</strong> with a specificity score and a confidence. It never "
  "returns a destination, because the mapping from evidence to outcome is a business threshold.",
  "<strong>A model failure routes to review</strong>, never to quarantine. The band exists "
  "because the cheap signals could not decide, so falling back to them is falling back to a "
  "shrug.",
  "<strong>The band is rate-limited per hour.</strong> A spam flood must not become a Bedrock "
  "bill; overflow goes to review, which is the safe direction."],
 gotchas=[
  "Hide the honeypot from assistive technology, not just visually. An off-screen labelled field "
  "gets filled in by screen reader users and silently classifies them as bots.",
  "Put a floor on fill time and no ceiling. Somebody opens the form, takes a phone call, and "
  "submits forty minutes later.",
  "Always return success to the submitter. A rejection message teaches bots and insults people.",
  "Never delete. The searchable quarantine is the only way a false positive ever becomes visible.",
  "Store every signal with every submission. Threshold changes should be replayed against three "
  "months of real traffic before they go live, and that is only possible if the inputs were "
  "kept."],
))
