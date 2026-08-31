"""Day 105 -- 2026-08-07 -- Consent preference keeper."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "consent-preference-keeper"
NAME = "Consent preference keeper"

SPEC = {
 "slug": SLUG, "date": "2026-08-07", "name": NAME,
 "tagline": ("One place that knows what each person agreed to and when, that every sending "
             "system asks before it sends, and that can still answer the question two years "
             "after somebody asks it."),
 "lede": ("A small system that records every consent and withdrawal as an immutable event, "
          "answers a single question -- may we send this to this person -- for every sending "
          "system in the business, and keeps the evidence of how each answer came to be. It "
          "never infers consent. Seven posts on the same system -- one diagram at a time -- with "
          "a cost breakdown and an engineering reference at the end."),
 "keywords": ["consent", "marketing preferences", "GDPR", "opt-out", "compliance", "serverless"],
 "icons": ["shield", "lock", "check"],
 "faq": [
  ("What is a consent preference keeper?",
   "A small serverless system that holds one authoritative record of what each person has agreed "
   "to receive, records every change as an immutable event with its evidence, and answers a "
   "single yes-or-no question for every system that sends anything."),
  ("Why not just a flag on the customer record?",
   "Because a flag answers what is true now and loses how it became true. The question that gets "
   "asked is \"why did you email me\", eighteen months later, and only an event history can "
   "answer it."),
  ("Does it stop systems sending?",
   "It answers a question; it cannot intercept a send. The discipline that makes it work is that "
   "every sending system asks first, and that a failure to reach it means do not send."),
  ("What happens on a withdrawal?",
   "It takes effect immediately in the record and is pushed to every downstream system that "
   "holds its own copy. The push is best-effort and is verified, because a suppression that "
   "silently failed is the failure that matters."),
  ("What does it cost to run?",
   "A couple of dollars a month even at high query volume. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "consent-preference-keeper-on-aws",
 "title": "A consent preference keeper on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("One authoritative record of what each person agreed to, asked before every send, with "
          "the evidence kept. AWS, about $2 a month."),
 "og": ("A flag tells you what is true now. The question people actually ask is why you emailed "
        "them, eighteen months later, and only an event history answers it."),
 "abstract": ("The whole system on one page -- an event log, a resolver and a propagator -- built "
              "so that the answer and the reason for it survive together."),
 "lede": ("Marketing consent goes wrong in small businesses in a specific and expensive way. "
          "There are four systems that can send something &mdash; the newsletter tool, the "
          "e-commerce platform, the booking system, somebody's mail merge &mdash; and each holds "
          "its own opinion about who is subscribed. Somebody unsubscribes from one and keeps "
          "hearing from two others. This post walks through a small system that gives all four "
          "the same answer."),
 "tags": ["consent", "marketing preferences", "GDPR", "opt-out", "compliance", "serverless"],
 "takeaways": [
  "One authoritative record, and every sending system asks it rather than holding an opinion.",
  "Every change is an immutable event with its evidence, not an updated flag.",
  "Consent is per purpose. Agreeing to order updates is not agreeing to a newsletter.",
  "A withdrawal takes effect immediately and is pushed to every downstream copy.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Where consent happens", "sub": ["forms, checkout,", "unsubscribe links"],
       "icon": "form"},
      {"title": "Sending systems", "sub": ["all of them, always asking"], "icon": "email"},
      {"title": "Whoever is asked", "sub": ["'why did you email me?'"], "icon": "person"}],
    "inside": [
      {"title": "Event log", "sub": ["immutable, with", "the evidence"], "icon": "log"},
      {"title": "Resolver", "sub": ["one question:", "may we send this?"], "icon": "filter"},
      {"title": "Propagator", "sub": ["push withdrawals,", "and verify them"], "icon": "retry"}],
    "edges": [{"from": 0, "to": 0, "label": "a consent event"},
              {"from": 1, "to": 1, "label": "may we send?"},
              {"from": 2, "to": 2, "label": "the evidence", "up": True}],
    "note": "It cannot intercept a send. Every sending system has to ask, and unreachable means no."}),
   "Three things outside the account, three pieces inside it. The system is advisory by "
   "construction, which makes the discipline in the sending systems the load-bearing part.",
   "System: consent events recorded, resolved and propagated",
   "Three boxes across the top sit outside the AWS account. On the left, Where consent happens: "
   "forms, checkout and unsubscribe links. In the middle, Sending systems: all of them, always "
   "asking. On the right, Whoever is asked the question why did you email me. Each connects by an "
   "arrow to the AWS account container below. A consent event flows down into the account. "
   "Sending systems ask whether they may send. The evidence goes back out. Inside the AWS account "
   "are three components in a row. On the left, the Event log, immutable and holding the "
   "evidence. In the middle, the Resolver, answering one question: may we send this. On the "
   "right, the Propagator, which pushes withdrawals and verifies them. A note at the bottom says "
   "it cannot intercept a send, so every sending system has to ask, and unreachable means no."),
  ("h3", "Events, not a flag"),
  ("p", "A boolean on a customer record answers what is true now and destroys everything about "
        "how it became true. That is fine until somebody asks why they received an email, which "
        "in this domain is not a support question but a regulatory one, and the answer has to be "
        "specific: on this date, through this form, with this wording, they agreed to this."),
  ("p", "So every change is an append-only event carrying its evidence: the source, the exact "
        "wording shown, the page, the timestamp and whatever identifier proves it was them. The "
        "current state is computed from the events rather than stored, which means the two can "
        "never disagree."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The event log.</strong> Append-only, one row per consent or withdrawal, with the "
   "evidence attached. Part 2 covers what evidence has to be captured for it to be worth "
   "anything.",
   "<strong>The resolver.</strong> Answers one question &mdash; may we send this purpose to this "
   "person &mdash; from the events, with a heavy cache because it is asked constantly. Part 3.",
   "<strong>The propagator.</strong> A withdrawal is only real when every system that could send "
   "knows about it. Part 4 is about pushing that out and, more importantly, verifying it "
   "arrived.",
  ]),
  ("h2", "One withdrawal, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Unsubscribe clicked", "sub": ["in one email"], "icon": "link"},
      {"title": "Event recorded", "sub": ["with the evidence"], "icon": "log"},
      {"title": "State recomputed", "sub": ["immediately"], "icon": "filter"},
      {"title": "Pushed", "sub": ["to four systems"], "icon": "retry"},
      {"title": "Verified", "sub": ["all four confirmed"], "icon": "check"}],
    "title": "ONE WITHDRAWAL, END TO END",
    "note": "The fifth box is the one that is usually missing, and it is where the failures are."}),
   "The same system as one line. Verification of the push is the step most implementations omit, "
   "and a silently failed suppression is exactly the failure that produces a complaint.",
   "One consent withdrawal from click to verified suppression, in five stages",
   "A horizontal row of five boxes joined by arrows. Unsubscribe clicked: in one email. Event "
   "recorded: with the evidence. State recomputed: immediately. Pushed: to four systems. "
   "Verified: all four confirmed. A note says the fifth box is the one that is usually missing "
   "and it is where the failures are."),
  ("h2", "In plain words"),
  ("p", "Somebody clicks unsubscribe in a newsletter. The link records a withdrawal event for the "
        "marketing purpose, with the campaign it came from, the timestamp and the signed token "
        "that proves it was that recipient. Their state for marketing becomes withdrawn "
        "immediately."),
  ("p", "The propagator then pushes that to the four systems that hold their own lists: the "
        "newsletter tool, the e-commerce platform, the booking system and the CRM. Three confirm "
        "within seconds. The fourth &mdash; the booking system, whose API is slow &mdash; is "
        "retried and confirms four minutes later. All four are recorded as confirmed with "
        "timestamps."),
  ("p", "Fourteen months later that person emails asking why they were contacted about a special "
        "offer. The answer takes about ten seconds to produce: they withdrew from marketing on "
        "the 7th of August 2026, the send in question was an order-related notification under a "
        "different purpose they have not withdrawn from, and here is the exact wording they "
        "agreed to when they placed the order. That is a completely different conversation from "
        "the one that starts with somebody checking a flag."),
  ("callout", "Design rules that shaped every decision", [
   "Events, never a flag. The current state is computed and the history is the point.",
   "Consent is per purpose. Order updates, marketing and service messages are different "
   "questions.",
   "Never infer consent. A purchase is not agreement to a newsletter, however convenient that "
   "would be.",
   "Withdrawal is immediate and pushed, and the push is verified rather than assumed.",
   "Unreachable means do not send. A resolver that is down must fail closed.",
   "The evidence is captured at the moment, not reconstructed later. Wording changes.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Consent management platforms exist and are good, and for a business of any size they are "
        "usually the right answer. The reason to build a small one is that most small businesses "
        "will not buy one and will instead keep four independent lists, which produces the "
        "specific failure this system exists to prevent: somebody unsubscribing and still hearing "
        "from you."),
  ("p", "So the design is deliberately small enough to actually get built: one table of events, "
        "one question, and a push. It does not manage cookie consent, it does not produce a "
        "compliance dashboard, and it does not try to be a customer data platform. It answers one "
        "question consistently and keeps the evidence."),
  ("p", "The next four posts walk through each piece: how an event is recorded, how the answer is "
        "resolved, how a withdrawal propagates, and what the evidence has to look like. One "
        "diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-consent-event-gets-recorded",
 "title": "How a consent event gets recorded",
 "nav": "How events record",
 "read": 5, "words": 750,
 "desc": ("What has to be captured at the moment, why the wording is stored rather than "
          "referenced, and the purposes that need to be separate."),
 "og": ("Storing a reference to the consent wording is worthless once the page changes. Store "
        "the wording itself, at the moment."),
 "abstract": ("What evidence has to be captured at the moment of consent, why the exact wording "
              "is stored rather than referenced, and how purposes are chosen."),
 "lede": ("The evidence is only worth anything if it was captured at the time, and the specific "
          "thing that gets lost is the wording. A record saying somebody agreed on the sign-up "
          "form is worth very little once the sign-up form has been rewritten twice."),
 "tags": ["consent", "evidence", "GDPR", "audit trail", "forms", "serverless"],
 "takeaways": [
  "Store the exact wording shown, not a reference to a page that will change.",
  "Capture the source, the timestamp, the purpose and proof it was that person.",
  "Purposes are few and separate: three or four, not fifteen.",
  "A double opt-in produces two events, and the second is the one that counts.",
  "Never write an event on behalf of somebody. Every event has a real action behind it.",
 ],
 "blocks": [
  ("h2", "What one event holds"),
  ("pre", "person        a stable identifier -- not just an email address\n"
          "purpose       marketing | service | orders | research\n"
          "state         granted | withdrawn\n"
          "at            2026-08-07T10:14:02Z\n"
          "source        checkout_form | preference_centre | unsubscribe_link |\n"
          "              staff_entry | import\n"
          "wording       the exact text shown, verbatim, stored inline\n"
          "page          the URL, for context only\n"
          "proof         signed token, session id, or a staff member's name\n"
          "channel       email | sms | post"),
  ("p", "The <code>wording</code> field is the one that matters and the one most often "
        "implemented as a reference to a version number or a page. Both are worthless in "
        "practice: version numbers get reused, and pages get rewritten without anybody thinking "
        "about the consent record. A few hundred bytes of verbatim text per event removes the "
        "whole problem."),
  ("h2", "Recording it"),
  ("fig", ("chain", {
    "entry": {"title": "Somebody acts", "sub": ["ticks, clicks, or asks"], "icon": "form"},
    "steps": [
      {"title": "Is there a real action?", "sub": ["not an inference"], "icon": "branch",
       "exit": {"title": "Do not record", "sub": ["a purchase is not consent"], "icon": "stop",
                "label": "no"}},
      {"title": "Capture the wording", "sub": ["as shown, verbatim"], "icon": "doc"},
      {"title": "Capture the proof", "sub": ["token, session, or a name"], "icon": "key"},
      {"title": "Append the event", "sub": ["never update"], "icon": "log",
       "side": {"title": "Event log", "sub": ["append-only"], "icon": "database"}},
      {"title": "Invalidate the cache", "sub": ["state changes now"], "icon": "retry"}],
    "note": "The first branch is the important one. Convenience is where consent records go wrong."}),
   "How one event is recorded. The refusal at the first step is what keeps the record honest, and "
   "it is the step under the most pressure from people who want a bigger list.",
   "How a consent event is captured and recorded",
   "A vertical chain of five steps entered by a box labelled Somebody acts, by ticking, clicking "
   "or asking. Step one asks whether there is a real action rather than an inference; if not it "
   "exits to Do not record, noting that a purchase is not consent. Step two captures the wording "
   "exactly as shown, verbatim. Step three captures the proof: a token, a session, or a staff "
   "member's name. Step four appends the event to an append-only event log and never updates. "
   "Step five invalidates the cache, because the state changes now. A note says the first branch "
   "is the important one, because convenience is where consent records go wrong."),
  ("h3", "Never infer"),
  ("p", "The pressure to infer is constant and always framed as reasonable. They bought "
        "something, so they must want to hear about similar things. They filled in a contact "
        "form, so they are interested. They are an existing customer, so a newsletter is fine."),
  ("p", "Each of those may be lawful under some basis in some jurisdiction and none of them is "
        "consent, and a system that records them as consent produces a log that cannot be trusted "
        "for the things that genuinely were. If a different lawful basis applies, that is a "
        "separate field with a separate name &mdash; not a consent event with a shrug behind it."),
  ("h2", "How many purposes"),
  ("table", ["Purpose", "Covers", "Typical basis"], [
   ["Orders", "Confirmations, dispatch, delivery", "Necessary for the contract, not consent"],
   ["Service", "Outages, changes to terms, safety", "Legitimate interest, usually"],
   ["Marketing", "Newsletters, offers, campaigns", "Consent"],
   ["Research", "Surveys, feedback requests", "Consent, usually separate"],
  ]),
  ("p", "Four is about right. Fifteen granular purposes produce a preference centre nobody "
        "completes and a resolver nobody can reason about; one combined purpose produces the "
        "failure where withdrawing from marketing stops order confirmations."),
  ("p", "The first two rows are worth noting: they are not consent at all, and recording them in "
        "the same system with an explicit basis field is better than pretending they are, because "
        "the sending systems still need to ask the same question and get a correct answer."),
  ("h2", "Double opt-in"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Form submitted", "sub": ["event: requested"], "icon": "form"},
      {"title": "Confirmation sent", "sub": ["one email"], "icon": "email"},
      {"title": "Link clicked", "sub": ["event: granted"], "icon": "check"},
      {"title": "Both kept", "sub": ["the pair is the evidence"], "icon": "log"},
      {"title": "Never clicked", "sub": ["not consent, and it expires"], "icon": "clock"}],
    "title": "DOUBLE OPT-IN IS TWO EVENTS",
    "note": "The unclicked case is the common one and it must not resolve to granted."}),
   "How a double opt-in is recorded. Two events rather than one, and the unconfirmed state is a "
   "real state rather than a pending version of granted.",
   "How a double opt-in produces two consent events",
   "A horizontal row of five boxes. Form submitted: an event recording requested. Confirmation "
   "sent: one email. Link clicked: an event recording granted. Both kept: the pair together is "
   "the evidence. Never clicked: which is not consent and expires. A note says the unclicked case "
   "is the common one and must not resolve to granted."),
  ("p", "The pair is stronger evidence than either event alone: a request from a form plus a "
        "confirmation click from an address that received an email is close to conclusive that "
        "the person controlling that address agreed."),
  ("p", "The unconfirmed request expiring rather than lingering matters, because a "
        "months-old unconfirmed request sitting in the log is exactly the thing that somebody "
        "later resolves as \"they did sign up\" when they did not."),
  ("p", "Next: answering the question."),
 ],
},
{
 "slug": "how-a-send-decision-is-resolved",
 "title": "How a send decision is resolved",
 "nav": "How it resolves",
 "read": 5, "words": 740,
 "desc": ("One question, one answer, computed from the events -- plus the caching that makes it "
          "fast and the failure mode that has to be closed."),
 "og": ("May we send this purpose to this person. One question, answered from events, cached "
        "hard -- and when the resolver is unreachable the answer is no."),
 "abstract": ("The single question the resolver answers, how it is computed from events, the "
              "caching that makes it viable at volume, and why it must fail closed."),
 "lede": ("The resolver has one job and its interface is deliberately tiny: given a person, a "
          "purpose and a channel, may we send. Everything about the design is in service of that "
          "being fast, consistent and safe when it breaks."),
 "tags": ["consent", "APIs", "caching", "fail closed", "compliance", "serverless"],
 "takeaways": [
  "One question: person, purpose, channel, and a yes or no.",
  "The answer is computed from the latest event per purpose, with no ambiguity.",
  "Cached aggressively, and invalidated the instant an event is written.",
  "Unreachable means no. A resolver that fails open is worse than no resolver.",
  "Bulk resolution exists for campaigns, and returns the same answers.",
 ],
 "blocks": [
  ("h2", "One question"),
  ("fig", ("chain", {
    "entry": {"title": "May we send?", "sub": ["person, purpose, channel"], "icon": "search"},
    "steps": [
      {"title": "In the cache?", "icon": "branch",
       "side": {"title": "Cache", "sub": ["invalidated on write"], "icon": "database"},
       "exit": {"title": "Answer", "sub": ["sub-millisecond"], "icon": "check", "label": "yes"}},
      {"title": "Latest event for this purpose", "sub": ["by timestamp"], "icon": "log",
       "exit": {"title": "No event at all", "sub": ["the answer is no"], "icon": "stop",
                "label": "none"}},
      {"title": "Granted?", "icon": "branch",
       "exit": {"title": "No", "sub": ["withdrawn, or requested only"], "icon": "stop",
                "label": "no"}},
      {"title": "Channel allowed?", "sub": ["email, sms, post"], "icon": "branch",
       "exit": {"title": "No", "sub": ["consent is per channel too"], "icon": "stop",
                "label": "no"}},
      {"title": "Yes", "sub": ["cache it"], "icon": "check"}],
    "note": "Absence of an event is a no. Silence has never been consent."}),
   "How the question is answered. Four of the five outcomes are no, which is the correct shape "
   "for a consent check.",
   "How a send decision is resolved from consent events",
   "A vertical chain of five steps entered by a box labelled May we send, carrying a person, a "
   "purpose and a channel. Step one asks whether it is in the cache, which is invalidated on "
   "write; a hit exits to Answer in under a millisecond. Step two finds the latest event for this "
   "purpose by timestamp; no event at all exits to the answer no. Step three asks whether it is "
   "granted; not granted exits to No, covering withdrawn or requested-only. Step four asks "
   "whether the channel is allowed, across email, SMS and post; if not it exits to No, because "
   "consent is per channel too. Step five is Yes, which is then cached. A note says absence of an "
   "event is a no, because silence has never been consent."),
  ("h3", "Absence is a no"),
  ("p", "A person with no consent event for a purpose has not consented to it, and the resolver "
        "says no. That sounds obvious and is worth stating because the alternative implementation "
        "&mdash; defaulting to yes for anybody not explicitly suppressed &mdash; is exactly how "
        "most legacy mailing lists work and is the thing this system replaces."),
  ("h3", "Per channel as well as per purpose"),
  ("p", "Somebody can reasonably agree to marketing by email and not by SMS, and a great many "
        "people feel differently about the two. Making channel part of the question rather than "
        "part of the purpose keeps the purpose list short while still supporting that, and it "
        "means adding a channel later does not require re-consenting anybody."),
  ("h2", "Caching"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Asked constantly", "sub": ["every send, every campaign"], "icon": "counter"},
      {"title": "Changes rarely", "sub": ["a few events a day"], "icon": "clock"},
      {"title": "Cache hard", "sub": ["hours, not seconds"], "icon": "database"},
      {"title": "Invalidate on write", "sub": ["not by expiry"], "icon": "retry"},
      {"title": "Withdrawal is instant", "sub": ["which is the requirement"], "icon": "check"}],
    "title": "READ CONSTANTLY, WRITTEN RARELY",
    "note": "Invalidating on write rather than expiring is what makes a long cache safe here."}),
   "The access pattern that makes aggressive caching both possible and safe. The requirement is "
   "that a withdrawal is immediate, and invalidation gives you that without a short TTL.",
   "Why consent answers can be cached aggressively",
   "A horizontal row of five boxes. Asked constantly: on every send and every campaign. Changes "
   "rarely: a few events a day. Cache hard: for hours rather than seconds. Invalidate on write: "
   "rather than by expiry. Withdrawal is instant: which is the requirement. A note says "
   "invalidating on write rather than expiring is what makes a long cache safe here."),
  ("p", "A short TTL is the instinctive answer and it gets the requirement wrong in both "
        "directions: five minutes is both far too much latency on a withdrawal and far too much "
        "load for data that changes twice a day. Invalidating the specific person's entry when an "
        "event is written gives a genuinely instant withdrawal and lets everything else be cached "
        "for hours."),
  ("h2", "Failing closed"),
  ("p", "If the resolver cannot be reached, the sending system must not send. That is "
        "uncomfortable &mdash; it means a resolver outage stops a campaign &mdash; and it is not "
        "close to a difficult decision."),
  ("callout", "Why fail closed is the only option", [
   "<strong>Failing open sends to people who withdrew.</strong> That is the exact harm the system "
   "exists to prevent, and it happens at campaign scale rather than one message at a time.",
   "<strong>Failing closed delays a campaign.</strong> Nobody has ever been harmed by a "
   "newsletter arriving on Thursday instead of Wednesday.",
   "<strong>It has to be the default in the client.</strong> A sending system that treats a "
   "timeout as permission has failed open regardless of what the resolver intended.",
   "<strong>And it has to be tested.</strong> Point a sending system at a dead resolver and "
   "confirm it sends nothing. It is a five-minute test that most implementations have never run.",
  ]),
  ("h3", "Bulk resolution"),
  ("p", "A campaign to twelve thousand people should not make twelve thousand calls. A bulk "
        "endpoint that takes a list and returns the allowed subset is the same logic with the "
        "same cache, and it is worth building early because the alternative is somebody exporting "
        "a list once and using it for three campaigns."),
  ("p", "The bulk response is deliberately the allowed subset rather than a per-person verdict "
        "list, which makes the wrong usage awkward: you cannot accidentally send to somebody who "
        "was not returned."),
  ("p", "Next: making a withdrawal real everywhere."),
 ],
},
{
 "slug": "how-a-withdrawal-propagates",
 "title": "How a withdrawal propagates",
 "nav": "How it propagates",
 "read": 5, "words": 740,
 "desc": ("Pushing a suppression to every system that holds a copy, verifying it landed, and the "
          "systems that cannot be pushed to."),
 "og": ("A withdrawal recorded and not propagated is a withdrawal that did not happen, as far as "
        "the person still receiving emails is concerned."),
 "abstract": ("Pushing a suppression to every downstream copy, why verification matters more "
              "than the push, and what to do about systems that cannot be pushed to at all."),
 "lede": ("The resolver being right is necessary and not sufficient, because several systems in "
          "any real business hold their own list and send from it. A withdrawal that is recorded "
          "correctly and not pushed is, from the recipient's point of view, no withdrawal at "
          "all."),
 "tags": ["consent", "suppression", "integration", "verification", "compliance", "serverless"],
 "takeaways": [
  "Every system that holds its own list gets the withdrawal pushed to it.",
  "The push is verified by reading back, not assumed from a success response.",
  "A system that cannot be pushed to gets a task for a person, on a clock.",
  "Unverified suppressions after 24 hours are escalated as a real finding.",
  "A quarterly reconciliation compares every list against the authoritative state.",
 ],
 "blocks": [
  ("h2", "Push, then verify"),
  ("fig", ("chain", {
    "entry": {"title": "A withdrawal event", "sub": ["recorded"], "icon": "log"},
    "steps": [
      {"title": "Which systems hold a copy?", "sub": ["from the register"], "icon": "filter",
       "side": {"title": "System register", "sub": ["push method each"], "icon": "doc"}},
      {"title": "Push the suppression", "sub": ["per system, retried"], "icon": "retry",
       "exit": {"title": "No API", "sub": ["a task for a person"], "icon": "person",
                "label": "manual"}},
      {"title": "Read it back", "sub": ["does it show suppressed?"], "icon": "search",
       "exit": {"title": "Not confirmed", "sub": ["retry, then escalate"], "icon": "alarm",
                "label": "no"}},
      {"title": "Record confirmed", "sub": ["with a timestamp, per system"], "icon": "check"},
      {"title": "All systems confirmed", "sub": ["now it is real"], "icon": "shield"}],
    "note": "Reading back is the step that catches the API that returns 200 and does nothing."}),
   "How a withdrawal reaches every system. The read-back is the difference between believing a "
   "suppression happened and knowing it did.",
   "How a consent withdrawal is pushed to downstream systems and verified",
   "A vertical chain of five steps entered by a box labelled A withdrawal event, recorded. Step "
   "one asks which systems hold a copy, from a register that records a push method for each. Step "
   "two pushes the suppression per system with retries; a system with no API exits to a task for "
   "a person. Step three reads it back to check whether it now shows as suppressed; not confirmed "
   "exits to retry and then escalate. Step four records confirmation with a timestamp per system. "
   "Step five is All systems confirmed, at which point it is real. A note says reading back is "
   "the step that catches the API that returns two hundred and does nothing."),
  ("h3", "Why read back"),
  ("p", "A suppression API returning success means the request was accepted, which is not the "
        "same as the person being suppressed. In practice several common platforms will accept a "
        "suppression against an address that is not in the list they will actually send from, "
        "accept one with a subtly different email casing, or queue it behind a sync that runs "
        "hourly."),
  ("p", "Reading the person's status back a few seconds later catches all of those, costs one "
        "extra call per suppression per system, and converts \"we sent the suppression\" into "
        "\"the suppression is in place\", which is the claim that has to be true."),
  ("h3", "Systems with no API"),
  ("p", "Every small business has one: a tool with no programmatic suppression, a spreadsheet "
        "somebody mail-merges from, a partner who sends on your behalf. Those cannot be pushed to "
        "and pretending they can be is worse than admitting it."),
  ("p", "So the register records the push method per system, and a manual one produces a dated "
        "task for a named person with the specific address and a link. It is on the same clock as "
        "every other system: unconfirmed after twenty-four hours is escalated."),
  ("h2", "The twenty-four hour rule"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Withdrawal recorded", "sub": ["state is immediate"], "icon": "log"},
      {"title": "Pushed", "sub": ["4 systems"], "icon": "retry"},
      {"title": "3 confirmed", "sub": ["within seconds"], "icon": "check"},
      {"title": "1 unconfirmed", "sub": ["after 24 hours"], "icon": "alarm"},
      {"title": "Escalated", "sub": ["as a compliance finding"], "icon": "shield"}],
    "title": "AN UNCONFIRMED SUPPRESSION",
    "note": "This is the finding that matters. Everything else in the system is bookkeeping."}),
   "What happens when a suppression cannot be confirmed. This is the one thing in the system that "
   "escalates as a genuine finding rather than a task.",
   "How an unconfirmed suppression is escalated",
   "A horizontal row of five boxes. Withdrawal recorded: the state is immediate. Pushed: to four "
   "systems. Three confirmed: within seconds. One unconfirmed: after twenty-four hours. "
   "Escalated: as a compliance finding. A note says this is the finding that matters and "
   "everything else in the system is bookkeeping."),
  ("p", "Twenty-four hours is chosen because it is well inside any reasonable expectation and "
        "because most transient failures resolve within minutes. A suppression still unconfirmed "
        "the next day is not a transient failure; it is a system that is going to keep sending."),
  ("h2", "Quarterly reconciliation"),
  ("p", "The push handles changes. It does not handle the list that drifted for reasons nobody "
        "saw: an import that added people, a sync from an old backup, a system that was "
        "re-connected and re-populated from stale data."),
  ("p", "So once a quarter, every system's full list is pulled and compared against the "
        "authoritative state. Anybody present in a downstream list who should be suppressed is a "
        "finding, and the count of those over time is the honest measure of whether the "
        "propagation is actually working."),
  ("p", "In practice the first reconciliation always finds something, usually in the system that "
        "was connected last, and finding it that way is much better than finding it because "
        "somebody complained."),
  ("p", "Next: what the evidence has to look like."),
 ],
},
{
 "slug": "how-consent-evidence-holds-up",
 "title": "How consent evidence holds up",
 "nav": "How evidence holds",
 "read": 5, "words": 730,
 "desc": ("Answering \"why did you email me\" two years later, what makes an answer credible, "
          "and the retention decision that is genuinely difficult."),
 "og": ("The question arrives eighteen months later and the answer has to be specific: this "
        "date, this wording, this proof. A flag cannot produce it."),
 "abstract": ("What answering a challenge actually requires, what makes an evidence record "
              "credible, the genuinely difficult retention question, and the numbers worth "
              "watching."),
 "lede": ("Everything in this system exists for a conversation that happens rarely and matters "
          "disproportionately: somebody asks why they were contacted, and the quality of the "
          "answer determines whether it ends there."),
 "tags": ["consent", "evidence", "GDPR", "retention", "reporting", "serverless"],
 "takeaways": [
  "The answer names a date, a source, the exact wording, and what proves it was them.",
  "It is produced in seconds, from one query, by whoever answers the email.",
  "Retention of consent evidence outlives the consent itself, and that is deliberate.",
  "Deleting a person's data and keeping the record that they withdrew are both required.",
  "The number to watch is unconfirmed suppressions, not consent rate.",
 ],
 "blocks": [
  ("h2", "What an answer looks like"),
  ("callout", "\"Why are you emailing me?\"", [
   "<strong>You subscribed on 14 March 2025</strong> through the newsletter form on our pricing "
   "page.",
   "<strong>The wording you agreed to was:</strong> \"Email me occasional product news and "
   "offers. You can unsubscribe at any time.\"",
   "<strong>You confirmed it</strong> by clicking the link in a confirmation email sent to this "
   "address on the same day.",
   "<strong>You have not withdrawn</strong> from marketing since. Your last change was on 14 "
   "March 2025.",
   "<strong>If you would like to stop,</strong> here is the link &mdash; it takes effect "
   "immediately across everything we use.",
  ]),
  ("p", "That is producible in about ten seconds by whoever is answering the email, from one "
        "query, and it ends the conversation in the large majority of cases. The version without "
        "this system &mdash; \"our records show you are subscribed\" &mdash; does not, and "
        "escalates at a meaningfully higher rate."),
  ("h2", "What makes it credible"),
  ("fig", ("chain", {
    "entry": {"title": "A challenge", "sub": ["'why did you email me'"], "icon": "chat"},
    "steps": [
      {"title": "Find the events", "sub": ["one query, by person"], "icon": "search",
       "side": {"title": "Event log", "sub": ["append-only"], "icon": "database"}},
      {"title": "Is there wording?", "sub": ["verbatim, from then"], "icon": "branch",
       "exit": {"title": "Weak answer", "sub": ["a date and a source only"], "icon": "alarm",
                "label": "no"}},
      {"title": "Is there proof?", "sub": ["a token, a confirmation"], "icon": "branch",
       "exit": {"title": "Weaker still", "sub": ["say so honestly"], "icon": "stop",
                "label": "no"}},
      {"title": "Compose the answer", "sub": ["date, wording, proof"], "icon": "doc"},
      {"title": "Offer the withdrawal", "sub": ["always, in the same reply"], "icon": "shield"}],
    "note": "The last step matters. An answer that defends without offering an exit reads badly."}),
   "How a challenge is answered. The two branches downward are what an imported or legacy consent "
   "produces, and being honest about them is better than dressing them up.",
   "How a consent challenge is answered from the event log",
   "A vertical chain of five steps entered by a box labelled A challenge, asking why did you "
   "email me. Step one finds the events with one query by person against the append-only event "
   "log. Step two asks whether there is wording, verbatim from the time; if not it exits to Weak "
   "answer, offering only a date and a source. Step three asks whether there is proof such as a "
   "token or a confirmation; if not it exits to Weaker still, and says so honestly. Step four "
   "composes the answer with the date, the wording and the proof. Step five offers the withdrawal "
   "link, always, in the same reply. A note says the last step matters, because an answer that "
   "defends without offering an exit reads badly."),
  ("h3", "Imported consent"),
  ("p", "Every business that adopts a system like this has a pile of existing subscribers whose "
        "consent predates it, and those produce the weak answer: a date, maybe a source, no "
        "wording, no proof."),
  ("p", "The honest handling is to mark those events explicitly as imported, with whatever "
        "provenance exists, and to know that the answer for those people is weaker. Some "
        "businesses respond by re-permissioning the imported list, which costs subscribers and "
        "produces a list where every remaining person has a strong record. That is a commercial "
        "decision rather than a technical one, and the system's job is to make the distinction "
        "visible enough that somebody can make it."),
  ("h2", "The retention question"),
  ("fig", ("strip", {
    "stages": [
      {"title": "They withdraw", "sub": ["and ask for deletion"], "icon": "person"},
      {"title": "Delete their data", "sub": ["as required"], "icon": "stop"},
      {"title": "Keep the withdrawal", "sub": ["or you will email them again"], "icon": "shield"},
      {"title": "A suppression record", "sub": ["minimal, and separate"], "icon": "lock"},
      {"title": "Both obligations met", "sub": ["and they conflict"], "icon": "check"}],
    "title": "THE GENUINELY DIFFICULT ONE",
    "note": "Deleting the record that somebody opted out is how they get contacted again."}),
   "The retention conflict that has no clean answer. Both obligations are real and they point in "
   "opposite directions.",
   "Why a withdrawal record is kept even after data deletion",
   "A horizontal row of five boxes. They withdraw: and ask for deletion. Delete their data: as "
   "required. Keep the withdrawal: or you will email them again. A suppression record: minimal, "
   "and held separately. Both obligations met: and they conflict. A note says deleting the record "
   "that somebody opted out is how they get contacted again."),
  ("p", "This is the one place in the whole series where the right answer is genuinely contested "
        "and depends on jurisdiction. The common resolution is a minimal suppression record "
        "&mdash; a hash of the address and the fact of withdrawal, nothing else &mdash; retained "
        "separately from everything else, on the basis that it exists solely to honour the "
        "withdrawal."),
  ("p", "What the system can do is make that record genuinely minimal and genuinely separate, so "
        "that whoever has to defend the decision has something defensible to point at rather than "
        "a full customer record that was supposed to be deleted."),
  ("h2", "The numbers"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Events", "sub": ["412 this quarter"], "icon": "log"},
      {"title": "Withdrawals", "sub": ["87"], "icon": "stop"},
      {"title": "Confirmed everywhere", "sub": ["86"], "icon": "check"},
      {"title": "Unconfirmed", "sub": ["1, escalated"], "icon": "alarm"},
      {"title": "Reconciliation gaps", "sub": ["0"], "icon": "shield"}],
    "title": "ONE QUARTER OF CONSENT",
    "note": "The fourth and fifth are the only ones that require anybody to do anything."}),
   "A quarter of consent activity in five numbers. Only the last two describe a problem; the "
   "first three are the system working.",
   "One quarter of consent management summarised in five numbers",
   "A horizontal row of five boxes. Events: four hundred and twelve this quarter. Withdrawals: "
   "eighty-seven. Confirmed everywhere: eighty-six. Unconfirmed: one, escalated. Reconciliation "
   "gaps: zero. A note says the fourth and fifth are the only ones that require anybody to do "
   "anything."),
  ("p", "Consent rate is deliberately not on that list. It is a marketing metric and putting it "
        "in a compliance report creates a quiet pressure to make the wording less clear, which is "
        "precisely the thing that makes the evidence weaker later."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="thousand resolutions",
 volumes=[(50, "50k resolutions"), (200, "200k resolutions"), (1000, "1M resolutions")],
 read_each=0.0,
 msgs_each=0.05,
 lede=("The resolver is asked constantly and the answer is cached, which makes this cheap at "
       "almost any volume. Fifty thousand resolutions a month is a business sending a few "
       "campaigns and a lot of transactional mail. Here is where each cent goes."),
 takeaway_extra=("Cache invalidation on write rather than a short TTL is what keeps a million "
                 "resolutions a month affordable."),
 risks=[
  "<strong>A short cache TTL instead of invalidation.</strong> A five-minute TTL at a million "
  "resolutions a month means most queries hit the table, which multiplies the read cost and "
  "still gives a worse withdrawal latency than invalidation.",
  "<strong>Per-person resolution during a campaign.</strong> Twelve thousand individual calls "
  "where one bulk call would do. Build the bulk endpoint before the first campaign, not after.",
  "<strong>Log retention left at never.</strong> A resolver logging every query at a million a "
  "month is by a wide margin the largest line on this bill.",
 ],
 per_unit_note=("There is no model and no third-party API. The cost is DynamoDB reads on cache "
                "misses plus Lambda duration, both of which are tiny per resolution."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="cp",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the immutability guarantee, and the fail-closed contract."),
 outside=[
  {"title": "Consent points", "sub": ["forms, links, staff"], "icon": "form"},
  {"title": "Sending systems", "sub": ["ask before every send"], "icon": "email"},
  {"title": "Downstream lists", "sub": ["pushed and verified"], "icon": "external"}],
 inside=[
  {"title": "Function URL", "sub": ["record, resolve,", "resolve-bulk"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["record, resolve,", "propagate"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["events, state"], "icon": "database"}],
 note="us-east-1. One account. The events table has no update or delete path in any role.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Consent points, meaning forms, unsubscribe "
  "links and staff entry. Sending systems, which ask before every send. And Downstream lists, "
  "which are pushed to and verified. Inside the account, three groups. A Function URL exposing "
  "record, resolve and resolve-bulk. Three Lambda functions named record, resolve and propagate. "
  "And two DynamoDB tables named events and state. A note gives the region as us-east-1, one "
  "account, and states that the events table has no update or delete path in any role."),
 functions=[
  ["<code>cp-record</code>", "Function URL",
   "Appends an event with its evidence; invalidates the cached state",
   "10s / 512&nbsp;MB"],
  ["<code>cp-resolve</code>", "Function URL",
   "Single and bulk resolution from the state table", "5s / 512&nbsp;MB"],
  ["<code>cp-propagate</code>", "SQS withdrawal queue + EventBridge",
   "Pushes suppressions, reads them back, escalates at 24h, quarterly reconcile",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>cp-record-role</code>",
   "<code>dynamodb:PutItem</code> (events), <code>dynamodb:UpdateItem</code> (state)",
   "PutItem only on events &mdash; no UpdateItem, no DeleteItem"],
  ["<code>cp-resolve-role</code>", "<code>dynamodb:GetItem</code>/<code>BatchGetItem</code>",
   "The state table, read only"],
  ["<code>cp-propagate-role</code>",
   "<code>secretsmanager:GetSecretValue</code>, <code>dynamodb:UpdateItem</code> (state)",
   "One secret per downstream system; the state table"]],
 tables=[
  ("Table: events",
   "PK   person            S   a stable id, not an email address\n"
   "SK   at_purpose        S   2026-08-07T10:14:02Z#marketing\n"
   "     state             S   granted | withdrawn | requested\n"
   "     purpose           S   marketing | service | orders | research\n"
   "     channel           S   email | sms | post | all\n"
   "     source            S   checkout_form | preference_centre |\n"
   "                           unsubscribe_link | staff_entry | import\n"
   "     wording           S   the exact text shown, verbatim, inline\n"
   "     proof             S   signed token, session id, or a staff name\n"
   "     page              S   context only\n\n"
   "APPEND ONLY. No role in this account has UpdateItem or DeleteItem on this\n"
   "table, which makes immutability a policy fact rather than a convention.\n"
   "A correction is a new event, never an edit."),
  ("Table: state",
   "PK   person            S   the same stable id\n"
   "SK   purpose_channel   S   marketing#email\n"
   "     allowed           BOOL false\n"
   "     since             S   2026-08-07T10:14:02Z\n"
   "     from_event        S   the event SK that produced this\n"
   "     downstream        M   {mailchimp: confirmed_at, crm: confirmed_at, ...}\n"
   "     unconfirmed_since S   set when a push has not been verified\n\n"
   "This is a cache, derived entirely from events. It can be rebuilt from the\n"
   "event log at any time, and the rebuild is a useful thing to run after any\n"
   "change to how state is computed.")],
 inbound=[
  "<strong>Unsubscribe links carry a signed token</strong> identifying the person, the purpose "
  "and the campaign. It is single-use for recording but the page remains usable, so a second "
  "click shows the current state rather than an error.",
  "<strong>The resolve endpoint has a hard latency budget</strong> and sending systems are "
  "configured to treat a timeout as no. That client-side default is where fail-closed actually "
  "lives.",
  "<strong>Bulk resolution returns the allowed subset</strong>, not a verdict per person, so a "
  "caller cannot accidentally iterate over the ones that were excluded.",
  "<strong>Each downstream system has its own secret</strong> and its own entry in the register "
  "recording whether it can be pushed to at all."],
 model_notes=[
  "<strong>There is no model in this system, and there should never be one.</strong> Every "
  "decision here is a lookup over an event log.",
  "<strong>The one place somebody will suggest one</strong> is interpreting a free-text "
  "unsubscribe request in a reply email, and even there a keyword match plus a human is the "
  "right answer.",
  "<strong>Consent is not a probabilistic question.</strong> A resolver that is ninety-nine per "
  "cent accurate is one that contacts a hundred people who withdrew, per ten thousand sends.",
  "<strong>Determinism is the product.</strong> The same person and purpose must produce the same "
  "answer every time, and be explainable from the events that produced it.",
  "<strong>The cost page assumes none</strong>, which is why this is one of the cheapest systems "
  "in the series."],
 gotchas=[
  "Deny UpdateItem and DeleteItem on the events table in the IAM policy. Immutability enforced by "
  "convention is immutability that will eventually be broken by a migration script.",
  "Store the wording verbatim. A reference to a page or a version number is worthless once the "
  "page is rewritten, which is the whole point of keeping evidence.",
  "Invalidate the cache on write rather than using a short TTL. It gives an instant withdrawal "
  "and a long cache at the same time.",
  "Read suppressions back from every downstream system. An API returning success is not the same "
  "as a person being suppressed.",
  "Test that a dead resolver stops sends. Fail-closed lives in the client's timeout handling, and "
  "almost nobody has actually verified it."],
))
