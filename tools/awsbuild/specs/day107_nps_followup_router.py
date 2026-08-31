"""Day 107 -- 2026-08-09 -- Feedback follow-up router."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "nps-followup-router"
NAME = "Feedback follow-up router"

SPEC = {
 "slug": SLUG, "date": "2026-08-09", "name": NAME,
 "tagline": ("An unhappy score reaches somebody who can do something about it within the hour, "
             "with the order and the history attached -- because a survey nobody acts on trains "
             "customers not to answer."),
 "lede": ("A small system that takes a satisfaction score and its comment, routes the unhappy "
          "ones to a person within the hour with the context already gathered, groups the rest "
          "into themes, and measures whether following up actually changed anything. It never "
          "replies on anybody's behalf. Seven posts on the same system -- one diagram at a time "
          "-- with a cost breakdown and an engineering reference at the end."),
 "keywords": ["customer feedback", "NPS", "surveys", "customer service", "retention", "serverless"],
 "icons": ["chat", "filter", "person"],
 "faq": [
  ("What is a feedback follow-up router?",
   "A small serverless system that routes each survey response by what it says: unhappy scores "
   "reach a person within the hour with the order history attached, and the rest are grouped "
   "into themes. It routes and gathers context; a person writes every reply."),
  ("Why does speed matter so much?",
   "Because a complaint answered within an hour reads as attentiveness and the same complaint "
   "answered in four days reads as indifference. The content of the reply matters less than most "
   "people expect and the delay matters more."),
  ("Does it write the reply?",
   "No. A generated apology to somebody who is already annoyed is worse than a short human one, "
   "and it is usually obvious. It gathers the context so a person can write three honest "
   "sentences in ninety seconds."),
  ("What about people who leave a low score and no comment?",
   "They get the same follow-up, and it is the more valuable one: a score with no comment is a "
   "person who could not be bothered to explain, and asking one specific question converts a "
   "surprising number of them."),
  ("What does it cost to run?",
   "A couple of dollars a month at a few hundred responses. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "nps-followup-router-on-aws",
 "title": "A feedback follow-up router on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 850,
 "desc": ("Routes unhappy scores to a person within the hour with the context attached, and "
          "groups the rest into themes. AWS, about $2 a month."),
 "og": ("A complaint answered in an hour reads as attentiveness; the same words four days later "
        "read as indifference. Speed is the product."),
 "abstract": ("The whole system on one page -- a receiver, a router and a theme grouper -- built "
              "on the observation that response time matters more than response wording."),
 "lede": ("Most small businesses that run a satisfaction survey do the hard part &mdash; asking "
          "&mdash; and then do nothing with the answers. The scores go into a spreadsheet, "
          "somebody looks at the average once a quarter, and the person who scored two out of "
          "ten and wrote a paragraph about a missed delivery hears nothing at all. This post "
          "walks through a small system whose only real job is making sure that person hears "
          "something within the hour."),
 "tags": ["customer feedback", "NPS", "surveys", "customer service", "retention", "serverless"],
 "takeaways": [
  "An unhappy score reaches a person within the hour, with the order and history attached.",
  "Speed matters more than wording. A fast short reply beats a slow considered one.",
  "The rest are grouped into themes on a fixed list, so trends mean something.",
  "It never writes the reply. A generated apology is worse than a short human one.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Survey responses", "sub": ["a score and maybe a comment"], "icon": "chat"},
      {"title": "Order history", "sub": ["what happened to them"], "icon": "cart"},
      {"title": "Whoever can fix it", "sub": ["within the hour"], "icon": "person"}],
    "inside": [
      {"title": "Receiver", "sub": ["score, comment,", "and who"], "icon": "form"},
      {"title": "Router", "sub": ["unhappy now,", "the rest to themes"], "icon": "filter"},
      {"title": "Context gatherer", "sub": ["the last order,", "any open ticket"], "icon": "search"}],
    "edges": [{"from": 0, "to": 0, "label": "responses"},
              {"from": 1, "to": 1, "label": "what happened"},
              {"from": 2, "to": 2, "label": "a person, with context", "up": True}],
    "note": "It gathers and routes. Every word sent to a customer is written by a person."}),
   "Three things outside the account, three pieces inside it. The context gatherer is what turns "
   "a ninety-second reply into a good one rather than a generic one.",
   "System: survey responses routed to a person with context attached",
   "Three boxes across the top sit outside the AWS account. On the left, Survey responses: a score "
   "and maybe a comment. In the middle, Order history: what actually happened to that customer. "
   "On the right, Whoever can fix it, reached within the hour. Each connects by an arrow to the "
   "AWS account container below. Responses flow down into the account. The order history feeds in "
   "what happened. A person receives the response with context. Inside the AWS account are three "
   "components in a row. On the left, the Receiver, capturing the score, the comment and who. In "
   "the middle, the Router, sending unhappy responses now and the rest to themes. On the right, "
   "the Context gatherer, pulling the last order and any open ticket. A note at the bottom says "
   "it gathers and routes, and every word sent to a customer is written by a person."),
  ("h3", "Speed over wording"),
  ("p", "The observation this design rests on is that response time dominates almost everything "
        "else about a follow-up. Three honest sentences within an hour of a complaint produce a "
        "materially different outcome from a carefully composed paragraph four days later, and "
        "the difference is not close."),
  ("p", "So the design optimises entirely for the hour: the routing is immediate, the context is "
        "pre-gathered so nobody has to go looking, and the reply is short because it is written "
        "by somebody who has ninety seconds rather than an afternoon."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The receiver.</strong> Takes responses from wherever the survey runs, matches them to "
   "a customer, and records the score and comment. Part 2 covers matching and the responses that "
   "arrive anonymously.",
   "<strong>The router.</strong> Decides urgency from the score first and the comment second, and "
   "sends the urgent ones immediately. Part 3 is about why the score alone is not enough.",
   "<strong>The context gatherer.</strong> Attaches the last order, the delivery outcome, any "
   "open ticket and whether they have complained before. Part 4 is entirely about this, because "
   "it is what makes a fast reply a good one.",
  ]),
  ("h2", "One response, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Submitted", "sub": ["3/10, one sentence"], "icon": "chat"},
      {"title": "Matched", "sub": ["to a customer"], "icon": "link"},
      {"title": "Routed", "sub": ["urgent, within minutes"], "icon": "filter"},
      {"title": "Context attached", "sub": ["order, delivery, history"], "icon": "search"},
      {"title": "Replied", "sub": ["by a person, in 90 seconds"], "icon": "person"}],
    "title": "ONE UNHAPPY RESPONSE, END TO END",
    "note": "About forty minutes from submission to reply, of which ninety seconds is a person."}),
   "The same system as one line. Almost all of the elapsed time is somebody getting to their "
   "phone; almost none of it is the system.",
   "One unhappy survey response from submission to reply, in five stages",
   "A horizontal row of five boxes joined by arrows. Submitted: three out of ten with one "
   "sentence. Matched: to a customer. Routed: as urgent, within minutes. Context attached: the "
   "order, the delivery and the history. Replied: by a person, in ninety seconds. A note says "
   "about forty minutes from submission to reply, of which ninety seconds is a person."),
  ("h2", "In plain words"),
  ("p", "A customer scores three out of ten and writes \"turned up two days late and nobody told "
        "me\". The receiver matches it to their order from the survey token. The router sees a "
        "low score and routes it immediately. The gatherer attaches the order, the tracking "
        "history showing a two-day carrier delay, the fact that no delay notification was sent, "
        "and that this is their fourth order and their first complaint."),
  ("p", "Somebody gets that on their phone eleven minutes later, and the useful part is that they "
        "do not have to look anything up. They can see the delay was real, that the customer is "
        "right that nobody told them, and that this is a good customer having a bad experience. "
        "The reply takes ninety seconds and says so."),
  ("p", "The theme grouping records it as a delivery-communication issue. Eleven of those in a "
        "month is a different finding from eleven scattered complaints, and it points at "
        "something fixable: the carrier reports delays and nothing forwards them to the "
        "customer."),
  ("callout", "Design rules that shaped every decision", [
   "Route unhappy responses within the hour. Everything else in the design is subordinate to "
   "that.",
   "Attach the context. A reply written without looking anything up is what makes ninety seconds "
   "enough.",
   "Never generate the reply. A generated apology to an annoyed person is transparent and makes "
   "it worse.",
   "Follow up on low scores with no comment. They are the more valuable ones.",
   "Group into themes from a fixed list, so a trend across months means something.",
   "Measure whether following up changed anything, not how many follow-ups happened.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Survey tools mostly stop at collection and reporting, which is the easy half. The half "
        "that changes anything is the follow-up, and it fails for a mundane reason: the person "
        "who should reply does not see the response until somebody exports a spreadsheet, and by "
        "then the moment has passed."),
  ("p", "So this design does almost nothing clever and spends everything on the two things that "
        "actually determine the outcome: getting the response in front of somebody fast, and "
        "putting enough context next to it that replying well takes ninety seconds instead of "
        "ten minutes of looking things up."),
  ("p", "The next four posts walk through each piece: how responses arrive and get matched, how "
        "routing decides urgency, what context gets attached, and how themes and outcomes are "
        "measured. One diagram per post, a cost breakdown, and an engineering reference at the "
        "end."),
 ],
},
{
 "slug": "how-a-response-arrives-and-matches",
 "title": "How a response arrives and matches",
 "nav": "How it arrives",
 "read": 5, "words": 740,
 "desc": ("Tokenised survey links, matching a response to an order rather than a person, and "
          "what to do with anonymous ones."),
 "og": ("A response matched to a person is useful. A response matched to a specific order is "
        "actionable, because you know what they are talking about."),
 "abstract": ("Why survey links carry an order token rather than a customer id, how anonymous "
              "responses are handled, and the timing of the ask itself."),
 "lede": ("Almost all of the value in a satisfaction response comes from knowing what it is "
          "about, and that is a property of how the survey was sent rather than anything you can "
          "recover afterwards."),
 "tags": ["customer feedback", "surveys", "tokens", "matching", "timing", "serverless"],
 "takeaways": [
  "The survey link carries an order token, not just a customer identifier.",
  "That means a response arrives already attached to a specific transaction.",
  "Anonymous responses are kept and counted but cannot be followed up, and that is stated.",
  "Ask once per order, not on a schedule, and never twice about the same thing.",
  "The timing of the ask changes the score more than most people expect.",
 ],
 "blocks": [
  ("h2", "Token the order, not the person"),
  ("fig", ("chain", {
    "entry": {"title": "An order completes", "sub": ["delivered, or the job done"], "icon": "cart"},
    "steps": [
      {"title": "Wait the right interval", "sub": ["from the ask rules"], "icon": "clock",
       "side": {"title": "Ask rules", "sub": ["per order type"], "icon": "doc"}},
      {"title": "Asked about this order?", "sub": ["ever"], "icon": "branch",
       "exit": {"title": "Do not ask again", "sub": ["one ask per order"], "icon": "stop",
                "label": "yes"}},
      {"title": "Asked recently at all?", "sub": ["frequency cap"], "icon": "branch",
       "exit": {"title": "Skip this one", "sub": ["survey fatigue is real"], "icon": "clock",
                "label": "yes"}},
      {"title": "Send with an order token", "sub": ["signed, single-use"], "icon": "link"},
      {"title": "A response, already attached", "sub": ["to a specific order"], "icon": "check"}],
    "note": "One ask per order and a cap per person. Both are needed; either alone is not enough."}),
   "How a survey gets sent so that its response is useful. The token carrying the order is what "
   "makes every downstream step possible without asking the customer what they mean.",
   "How a survey is sent with an order token attached",
   "A vertical chain of five steps entered by a box labelled An order completes, meaning delivered "
   "or the job done. Step one waits the right interval, taken from ask rules held per order type. "
   "Step two asks whether this order has been asked about before, ever; if so it exits to Do not "
   "ask again, because it is one ask per order. Step three asks whether this person has been asked "
   "recently at all, against a frequency cap; if so it exits to Skip this one, because survey "
   "fatigue is real. Step four sends the survey with a signed single-use order token. Step five "
   "receives a response that is already attached to a specific order. A note says one ask per "
   "order and a cap per person are both needed, because either alone is not enough."),
  ("h3", "Why the order and not the customer"),
  ("p", "A response attached to a customer tells you somebody is unhappy. A response attached to "
        "an order tells you which experience they are unhappy about, which is the difference "
        "between a reply that asks what went wrong and a reply that already knows."),
  ("p", "For a customer with one order the distinction is academic. For a repeat customer it is "
        "the whole thing: \"sorry to hear that, can you tell me more?\" reads very differently "
        "from \"I can see the 14th arrived two days late &mdash; that is on us.\""),
  ("h3", "Two caps, both needed"),
  ("p", "One ask per order prevents asking twice about the same experience, which is annoying and "
        "produces contradictory data. A frequency cap per person prevents a customer who orders "
        "weekly being surveyed weekly, which is how a business trains its best customers to "
        "ignore its emails."),
  ("p", "Neither cap on its own is sufficient, and the frequency cap is the one usually missing. "
        "Sixty days is a reasonable default: a customer is asked about at most one order every "
        "two months regardless of how often they buy."),
  ("h2", "Timing the ask"),
  ("table", ["Order type", "Ask after", "Why"], [
   ["Delivered goods", "2 days after delivery", "Long enough to have opened it"],
   ["A service visit", "Same day, that evening", "While it is fresh and specific"],
   ["A long project", "At completion, then never", "Mid-project surveys measure mood"],
   ["A subscription", "Never per order", "Ask twice a year instead"],
  ]),
  ("p", "Asking too early produces a score about the ordering experience; asking too late "
        "produces a score about how they feel in general. Neither is what the survey is for, and "
        "the interval is worth setting per order type rather than globally."),
  ("h2", "Anonymous responses"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A response", "sub": ["no token"], "icon": "chat"},
      {"title": "From a widget", "sub": ["or a shared link"], "icon": "browser"},
      {"title": "Cannot follow up", "sub": ["nobody to reply to"], "icon": "stop"},
      {"title": "Still counted", "sub": ["in the themes"], "icon": "chart"},
      {"title": "Reported separately", "sub": ["so the rate is honest"], "icon": "report"}],
    "title": "THE RESPONSE WITH NOBODY ATTACHED",
    "note": "Counting anonymous responses in the same average as tokenised ones flatters or "
            "distorts, usually the latter."}),
   "How anonymous responses are handled. They are real feedback and they cannot be followed up, "
   "and reporting them separately is what keeps both numbers meaningful.",
   "How an anonymous survey response is handled",
   "A horizontal row of five boxes. A response: with no token. From a widget: or a shared link. "
   "Cannot follow up: there is nobody to reply to. Still counted: in the themes. Reported "
   "separately: so the response rate is honest. A note says counting anonymous responses in the "
   "same average as tokenised ones flatters or distorts, usually the latter."),
  ("p", "Anonymous responses skew low, consistently, because somebody moved enough to seek out a "
        "feedback widget is more often unhappy than the average recipient of a survey email. "
        "Blending them into one score produces a number that moves for reasons nothing to do with "
        "the business."),
  ("p", "Next: deciding urgency."),
 ],
},
{
 "slug": "how-urgency-gets-decided",
 "title": "How urgency gets decided",
 "nav": "How urgency works",
 "read": 5, "words": 740,
 "desc": ("Why the score alone is not enough, the comments that escalate regardless, and who "
          "gets routed to."),
 "og": ("A nine out of ten with a comment describing an injury is not a happy response. The score "
        "sets the default and the comment can override it."),
 "abstract": ("Why the score alone is insufficient, the comment patterns that escalate "
              "regardless of score, who each band routes to, and the response that needs "
              "somebody senior."),
 "lede": ("Routing on the score alone is nearly right and fails in the cases that matter most. "
          "People give a seven and describe something serious; people give a two because the "
          "packaging was ugly. The score is a good default and a bad decision."),
 "tags": ["customer feedback", "routing", "escalation", "AWS Bedrock", "customer service",
          "serverless"],
 "takeaways": [
  "The score sets the default band; the comment can escalate but rarely de-escalates.",
  "Four patterns escalate regardless of score: safety, legal, data, and a threat to leave.",
  "Low score with no comment is followed up, and the ask is one specific question.",
  "Routing is to a person, never to a shared inbox.",
  "A repeat complainer is routed to somebody more senior, not filtered out.",
 ],
 "blocks": [
  ("h2", "Score first, comment second"),
  ("fig", ("chain", {
    "entry": {"title": "A response", "sub": ["score and comment"], "icon": "chat"},
    "steps": [
      {"title": "Anything serious in it?", "sub": ["safety, legal, data,", "leaving"],
       "icon": "branch",
       "exit": {"title": "Escalate now", "sub": ["whatever the score"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Low score?", "sub": ["below the line you set"], "icon": "branch",
       "exit": {"title": "Route within the hour", "sub": ["with context"], "icon": "person",
                "label": "yes"}},
      {"title": "Middling with a comment?", "sub": ["a specific complaint"], "icon": "branch",
       "exit": {"title": "Route today", "sub": ["less urgent, still routed"], "icon": "email",
                "label": "yes"}},
      {"title": "High score with a comment?", "icon": "branch",
       "exit": {"title": "Worth reading", "sub": ["the weekly digest"], "icon": "report",
                "label": "yes"}},
      {"title": "A score and nothing else", "sub": ["counted, not routed"], "icon": "counter"}],
    "note": "The first branch runs before the score is even looked at. That ordering is the point."}),
   "How urgency is decided. Checking for serious content before looking at the score is what "
   "catches the response that is polite about something that is not.",
   "How a survey response's urgency is decided",
   "A vertical chain of five steps entered by a box labelled A response, carrying a score and a "
   "comment. Step one asks whether there is anything serious in it, covering safety, legal, data "
   "and a threat to leave; if so it exits to Escalate now, whatever the score. Step two asks "
   "whether the score is low, below a line you set; if so it exits to Route within the hour with "
   "context. Step three asks whether it is a middling score with a specific complaint; if so it "
   "exits to Route today, less urgent but still routed. Step four asks whether it is a high score "
   "with a comment; if so it exits to Worth reading in the weekly digest. Step five is a score "
   "and nothing else, which is counted rather than routed. A note says the first branch runs "
   "before the score is even looked at, and that ordering is the point."),
  ("h3", "The four that escalate regardless"),
  ("table", ["Pattern", "Example", "Goes to"], [
   ["Safety", "\"the fitting came loose and could have hurt somebody\"", "Immediately, and to a manager"],
   ["Legal", "\"I have spoken to a solicitor\"", "Immediately, and to the owner"],
   ["Data", "\"you sent me somebody else's invoice\"", "Immediately, and to whoever handles data"],
   ["Leaving", "\"we will be going elsewhere\"", "Within the hour, to whoever owns the account"],
  ]),
  ("p", "All four appear at every score. Somebody who is generally happy with a business will "
        "score it eight and mention in passing that a fitting came loose, and a router that reads "
        "the eight and files it as a promoter has missed the only response that week that "
        "genuinely mattered."),
  ("h3", "The low score with no comment"),
  ("p", "The most under-used response in any survey. A two with no explanation is a person who "
        "was annoyed enough to score and not annoyed enough to write, and the conventional "
        "handling is to count them and move on."),
  ("p", "They are worth following up specifically, and the ask matters: not \"can you tell us "
        "more\" but one specific question derived from the order. \"I can see this was delivered "
        "two days later than we said &mdash; was that it?\" converts at a much higher rate "
        "because it costs the recipient a yes rather than an essay."),
  ("h2", "Who it goes to"),
  ("fig", ("strip", {
    "stages": [
      {"title": "A named person", "sub": ["never a shared inbox"], "icon": "person"},
      {"title": "Who owns the account", "sub": ["if there is one"], "icon": "team"},
      {"title": "Or who is on today", "sub": ["from a rota"], "icon": "calendar"},
      {"title": "Repeat complainer", "sub": ["more senior, not filtered"], "icon": "alarm"},
      {"title": "Acknowledged", "sub": ["or it re-routes in 60 minutes"], "icon": "clock"}],
    "title": "ROUTING TO A PERSON",
    "note": "A shared inbox is a place responses go to wait for somebody else to handle them."}),
   "Who a routed response reaches. Named people with an acknowledgement timeout is what makes the "
   "hour real rather than aspirational.",
   "How a routed survey response reaches a specific person",
   "A horizontal row of five boxes. A named person: never a shared inbox. Who owns the account: if "
   "there is one. Or who is on today: taken from a rota. Repeat complainer: routed to somebody "
   "more senior rather than filtered out. Acknowledged: or it re-routes after sixty minutes. A "
   "note says a shared inbox is a place responses go to wait for somebody else to handle them."),
  ("p", "The acknowledgement timeout is what makes the hour a real commitment. A response sent to "
        "a named person who does not tap acknowledge within sixty minutes re-routes to the next "
        "person on the rota, which means the hour holds even when somebody is driving."),
  ("h3", "The repeat complainer"),
  ("p", "Somebody on their fourth low score in six months is the case where every instinct is "
        "wrong. Filtering them out is the obvious move and it is how a business loses a customer "
        "who has been telling them something for six months."),
  ("p", "So a repeat pattern routes upward rather than being suppressed, with the history "
        "attached, and the framing is explicit: this is the fourth time, here are the previous "
        "three, and they are still buying from us. That is a conversation somebody senior should "
        "have, and it is a different conversation from the individual complaint."),
  ("p", "Next: the context that makes a fast reply a good one."),
 ],
},
{
 "slug": "how-the-context-gets-attached",
 "title": "How the context gets attached",
 "nav": "How context attaches",
 "read": 5, "words": 730,
 "desc": ("The five things that turn a ninety-second reply into a good one, and the one piece of "
          "context that changes what somebody says."),
 "og": ("The reply takes ninety seconds because nobody has to look anything up. Five pieces of "
        "context, gathered before the person opens it."),
 "abstract": ("The five pieces of context that make a fast reply a good one, why the delivery "
              "outcome matters most, and the history that changes the tone of what somebody "
              "writes."),
 "lede": ("The ninety-second reply is only possible because everything somebody would have gone "
          "looking for is already on the screen. This post is about what those things are, and "
          "the surprising one is not the order."),
 "tags": ["customer feedback", "context", "customer service", "integration", "operations",
          "serverless"],
 "takeaways": [
  "Five things: the order, what actually happened to it, open tickets, their history, and value.",
  "What happened to the delivery matters more than the order itself.",
  "Whether they have complained before changes what somebody writes, and it should.",
  "Never show a customer lifetime value figure to the person replying.",
  "Missing context is stated rather than left blank, so nothing is assumed.",
 ],
 "blocks": [
  ("h2", "The five"),
  ("fig", ("chain", {
    "entry": {"title": "A routed response", "sub": ["with an order token"], "icon": "filter"},
    "steps": [
      {"title": "The order", "sub": ["what they bought, when"], "icon": "cart",
       "side": {"title": "Commerce", "sub": ["one lookup"], "icon": "database"}},
      {"title": "What happened to it", "sub": ["tracking, delays,", "what we told them"],
       "icon": "truck"},
      {"title": "Open tickets", "sub": ["are we already talking?"], "icon": "chat",
       "side": {"title": "Helpdesk", "sub": ["by customer"], "icon": "external"}},
      {"title": "Their history", "sub": ["orders, and prior scores"], "icon": "counter"},
      {"title": "One screen", "sub": ["nothing to look up"], "icon": "doc"}],
    "note": "The second box is the one that most often contains the answer to the complaint."}),
   "The five lookups that run before a person sees the response. The delivery history is the one "
   "that most often turns a complaint into an obvious apology.",
   "How context is gathered before a survey response reaches a person",
   "A vertical chain of five steps entered by a box labelled A routed response, with an order "
   "token. Step one fetches the order: what they bought and when, from the commerce system in one "
   "lookup. Step two fetches what happened to it: tracking, delays, and what we told them. Step "
   "three fetches open tickets, asking whether we are already talking to them, from the helpdesk "
   "by customer. Step four fetches their history: orders and prior scores. Step five presents one "
   "screen with nothing left to look up. A note says the second box is the one that most often "
   "contains the answer to the complaint."),
  ("h3", "What happened, not what was ordered"),
  ("p", "The order tells you what they bought. What happened to it &mdash; the carrier scans, the "
        "delay, whether a notification was sent &mdash; tells you whether their complaint is "
        "justified, and it usually is."),
  ("p", "That distinction is what lets somebody write \"you are right, it was two days late and "
        "we should have told you\" in ninety seconds instead of writing something noncommittal "
        "because they do not know. And a noncommittal reply to a specific complaint is close to "
        "useless."),
  ("h3", "Are we already talking to them"),
  ("p", "The open-ticket check prevents the specific embarrassment of somebody sending a fresh "
        "\"sorry to hear that, what happened?\" to a customer who is already three messages into "
        "a conversation with a colleague about exactly this."),
  ("p", "Where a ticket is open, the response is routed to whoever is handling it rather than to "
        "the rota, and it appears as an addition to that conversation rather than as a new one. "
        "That is a small piece of plumbing that prevents a genuinely annoying customer "
        "experience."),
  ("h2", "The context that is deliberately absent"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Order count", "sub": ["shown"], "icon": "counter"},
      {"title": "Prior scores", "sub": ["shown"], "icon": "chart"},
      {"title": "Open tickets", "sub": ["shown"], "icon": "chat"},
      {"title": "Lifetime value", "sub": ["not shown"], "icon": "stop"},
      {"title": "Why", "sub": ["it changes the reply"], "icon": "person"}],
    "title": "ONE THING THAT IS NOT ON THE SCREEN",
    "note": "Showing a value figure produces better replies to richer customers, visibly."}),
   "The context deliberately withheld from the person replying. Order count conveys loyalty "
   "without conveying a number that changes how somebody treats an individual.",
   "The one piece of customer context deliberately not shown",
   "A horizontal row of five boxes. Order count: shown. Prior scores: shown. Open tickets: shown. "
   "Lifetime value: not shown. Why: it changes the reply. A note says showing a value figure "
   "produces better replies to richer customers, visibly."),
  ("p", "This is a deliberate choice and it is worth defending. A person who can see that this "
        "customer has spent four thousand pounds and that one has spent forty will, entirely "
        "unconsciously, write a warmer reply to the first. Customers notice that over time, and "
        "the ones who notice are the ones who spent forty."),
  ("p", "Order count conveys most of what is useful &mdash; a fourth-time customer is different "
        "from a first-time one &mdash; without attaching a figure that invites triage. It is a "
        "small restraint with a compounding effect."),
  ("h3", "Stating what is missing"),
  ("p", "Where a lookup fails or a system has nothing, the screen says so rather than showing a "
        "blank. \"No tracking data available for this order\" is different from an empty "
        "tracking section, and somebody writing a reply in ninety seconds will read an empty "
        "section as nothing happened."),
  ("p", "Next: themes, and whether any of this changes anything."),
 ],
},
{
 "slug": "how-the-signal-stays-honest",
 "title": "How the signal stays honest",
 "nav": "How it stays honest",
 "read": 5, "words": 730,
 "desc": ("Grouping into fixed themes, the response rate that decides whether the score means "
          "anything, and measuring whether following up actually worked."),
 "og": ("The score is the least interesting number. Response rate decides whether it means "
        "anything, and the recovery rate decides whether following up is worth doing."),
 "abstract": ("Grouping responses into fixed themes, why response rate governs whether the score "
              "means anything, the measurement that shows whether following up works, and the "
              "pressure to game it."),
 "lede": ("A satisfaction score is the number everybody reports and the least useful thing this "
          "system produces. Two other numbers determine whether it means anything at all, and a "
          "third determines whether the follow-up is worth the effort."),
 "tags": ["customer feedback", "NPS", "metrics", "reporting", "retention", "serverless"],
 "takeaways": [
  "Group into a fixed theme list, for the same reason as search queries: comparability.",
  "Response rate governs everything. A score from 4% of customers describes those 4%.",
  "Measure recovery: did the people you followed up with buy again?",
  "Report the theme counts, not just the score. Themes are what somebody can fix.",
  "Resist tying the score to anybody's pay, or the ask itself will be gamed.",
 ],
 "blocks": [
  ("h2", "Fixed themes"),
  ("p", "The same argument as the search rank reporter: a model asked to cluster comments will "
        "produce sensible groups that differ slightly between runs, and every trend built on them "
        "is meaningless. A fixed list &mdash; delivery, product quality, communication, price, "
        "staff, website &mdash; produces the same groups forever."),
  ("p", "Six or seven themes is right. The model's job is classification into that list or into "
        "unmatched, and a growing unmatched bucket is the signal that the list needs a new entry, "
        "reviewed quarterly."),
  ("h2", "Response rate governs everything"),
  ("fig", ("chain", {
    "entry": {"title": "A reported score", "sub": ["say 8.1"], "icon": "chart"},
    "steps": [
      {"title": "From what response rate?", "icon": "branch",
       "exit": {"title": "Under 10%", "sub": ["it describes the 10%"], "icon": "alarm",
                "label": "low"}},
      {"title": "Who did not answer?", "sub": ["systematically different?"], "icon": "search"},
      {"title": "Anonymous mixed in?", "sub": ["they skew low"], "icon": "branch",
       "exit": {"title": "Report separately", "sub": ["two numbers"], "icon": "filter",
                "label": "yes"}},
      {"title": "Enough responses this period?", "sub": ["a floor"], "icon": "branch",
       "exit": {"title": "Do not report a change", "sub": ["say the volume"], "icon": "stop",
                "label": "no"}},
      {"title": "A score worth quoting", "sub": ["with its rate beside it"], "icon": "check"}],
    "note": "The score is never reported without the response rate next to it. Ever."}),
   "Why a score is never quoted alone. Each of these checks is a way the headline number can be "
   "true and misleading at the same time.",
   "How a satisfaction score is qualified before being reported",
   "A vertical chain of five steps entered by a box labelled A reported score, say eight point "
   "one. Step one asks what response rate it came from; under ten per cent exits to a note that "
   "it describes only that ten per cent. Step two asks who did not answer and whether they are "
   "systematically different. Step three asks whether anonymous responses are mixed in, since "
   "they skew low; if so it exits to Report separately as two numbers. Step four asks whether "
   "there were enough responses this period against a floor; if not it exits to Do not report a "
   "change and state the volume instead. Step five is a score worth quoting, with its rate beside "
   "it. A note says the score is never reported without the response rate next to it, ever."),
  ("h3", "Who does not answer"),
  ("p", "The people who ignore a satisfaction survey are not a random sample. They skew towards "
        "the mildly satisfied &mdash; nothing went wrong, nothing was memorable &mdash; and away "
        "from both extremes. A score built from the people who did answer is a score of the "
        "people who felt something."),
  ("p", "That does not make it useless; it makes it a different measurement from the one people "
        "assume. Reporting the rate next to the score is the whole mitigation, and it costs one "
        "extra number."),
  ("h2", "Does following up work"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Unhappy responses", "sub": ["31 this quarter"], "icon": "chat"},
      {"title": "Followed up", "sub": ["29 within the hour"], "icon": "person"},
      {"title": "Ordered again", "sub": ["17"], "icon": "cart"},
      {"title": "Unhappy, not followed up", "sub": ["2, both by accident"], "icon": "alarm"},
      {"title": "Ordered again", "sub": ["0"], "icon": "counter"}],
    "title": "THE ONLY MEASUREMENT THAT JUSTIFIES ANY OF THIS",
    "note": "Small numbers, and it is still the number to watch. Recovery, not response count."}),
   "The measurement that decides whether the follow-up is worth doing. It is a small sample and "
   "it is the right question, which most feedback reporting never asks.",
   "Whether following up on unhappy responses changes behaviour",
   "A horizontal row of five boxes. Unhappy responses: thirty-one this quarter. Followed up: "
   "twenty-nine within the hour. Ordered again: seventeen. Unhappy and not followed up: two, both "
   "by accident. Ordered again: none. A note says the numbers are small and it is still the number "
   "to watch, because recovery matters rather than response count."),
  ("p", "The comparison is imperfect &mdash; two is not a control group &mdash; and it is the "
        "right question, which is more than most feedback reporting manages. Seventeen of "
        "twenty-nine unhappy customers ordering again is a recovery rate, and it is the number "
        "that justifies somebody's ninety seconds."),
  ("p", "Over a year the sample gets large enough to mean something, and the trend within it is "
        "more informative than the level: a recovery rate that falls after somebody changed how "
        "replies are written is a real finding."),
  ("h2", "The pressure to game it"),
  ("callout", "What happens when the score becomes a target", [
   "<strong>The ask gets selective.</strong> Surveys stop going to orders that went badly, which "
   "is the easiest and most invisible manipulation available.",
   "<strong>The wording gets leading.</strong> \"We hope you were happy with your order &mdash; "
   "how did we do?\" scores measurably higher than a neutral ask.",
   "<strong>The timing moves.</strong> Asking immediately after a pleasant interaction rather "
   "than after the outcome is known.",
   "<strong>The counter-measure</strong> is to report the ask rate alongside the score: how many "
   "eligible orders were surveyed. A score that rose while the ask rate fell is not a score that "
   "rose.",
  ]),
  ("p", "This is the strongest argument against tying the score to anybody's pay or targets, and "
        "it is worth making explicitly to whoever suggests it. The measurement is only useful "
        "while nobody has a reason to move it, and it is very easy to move in ways that leave no "
        "trace in the score itself."),
  ("p", "Reporting the ask rate is the cheapest available defence: it makes the most common "
        "manipulation visible in the same table as the number it was meant to improve."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="response",
 volumes=[(60, "60 responses"), (250, "250 responses"), (1000, "1,000 responses")],
 read_each=0.0009, msgs_each=2.4,
 lede=("The model is used once per response with a comment, for theme classification and the "
       "serious-content check. Two hundred and fifty responses a month is a business surveying a "
       "few thousand orders a year. Here is where each cent goes."),
 takeaway_extra=("Responses with no comment skip the model entirely, and they are a large "
                 "fraction of the total."),
 risks=[
  "<strong>Surveying every order with no frequency cap.</strong> Not a cost problem so much as a "
  "list-destruction problem: a weekly customer surveyed weekly stops opening your email "
  "entirely.",
  "<strong>Re-classifying on every report run.</strong> Themes are assigned once per response and "
  "stored. Re-running classification at report time multiplies the cost and makes trends "
  "unstable.",
  "<strong>Log retention left at never.</strong> Survey comments are customer content, and "
  "unbounded logs of them are both a cost and a data question.",
 ],
 per_unit_note=("One model call per response that has a comment, doing two things at once: theme "
                "classification and the serious-content check. Scores with no comment cost "
                "nothing."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="fr",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the routing timeout, and the single model call."),
 outside=[
  {"title": "Survey responses", "sub": ["webhook or Function URL"], "icon": "chat"},
  {"title": "Commerce + helpdesk", "sub": ["context lookups"], "icon": "database"},
  {"title": "SNS + SES", "sub": ["routing, digests"], "icon": "email"}],
 inside=[
  {"title": "SQS + EventBridge", "sub": ["response queue,", "ask scheduler"], "icon": "queue"},
  {"title": "Lambda x4", "sub": ["ask, receive,", "route, report"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["responses, asks"], "icon": "database"}],
 note="us-east-1. One account. No reply to a customer is ever generated or sent by this system.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Survey responses, arriving by webhook or "
  "Function URL. Commerce and helpdesk systems, used for context lookups. And SNS with SES, "
  "carrying routing messages and digests. Inside the account, three groups. SQS carrying a "
  "response queue and EventBridge running the ask scheduler. Four Lambda functions named ask, "
  "receive, route and report. And two DynamoDB tables named responses and asks. A note gives the "
  "region as us-east-1, one account, and states that no reply to a customer is ever generated or "
  "sent by this system."),
 functions=[
  ["<code>fr-ask</code>", "EventBridge hourly",
   "Finds eligible orders, applies both caps, sends tokenised surveys",
   "60s / 512&nbsp;MB"],
  ["<code>fr-receive</code>", "Function URL",
   "Validates the token, records score and comment, enqueues", "10s / 512&nbsp;MB"],
  ["<code>fr-route</code>", "SQS response queue",
   "One Bedrock call, context fan-out, routing with a 60-minute timeout",
   "30s / 1024&nbsp;MB"],
  ["<code>fr-report</code>", "EventBridge weekly + quarterly",
   "Theme counts, response and ask rates, recovery measurement", "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>fr-ask-role</code>",
   "<code>dynamodb:Query</code>/<code>PutItem</code>, <code>ses:SendEmail</code>",
   "The asks table; one verified identity"],
  ["<code>fr-receive-role</code>",
   "<code>dynamodb:PutItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Responses; the token signing key only"],
  ["<code>fr-route-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>secretsmanager:GetSecretValue</code>, "
   "<code>sns:Publish</code>",
   "One model arn; commerce and helpdesk read credentials; the staff topic"],
  ["<code>fr-report-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "Responses and asks, read; one verified identity"]],
 tables=[
  ("Table: responses",
   "PK   response_id       S   rsp_2026_08_09_d21f\n"
   "     order_id          S   from the token, not from the customer\n"
   "     customer          S   or 'anonymous'\n"
   "     score             N   3\n"
   "     comment           S   verbatim\n"
   "     theme             S   delivery | quality | communication | price |\n"
   "                           staff | website | unmatched\n"
   "     serious           S   safety | legal | data | leaving | none\n"
   "     routed_to         S   a named person\n"
   "     routed_at         S   2026-08-09T10:14:00Z\n"
   "     acknowledged_at   S   or null; null at +60m re-routes\n"
   "     replied_at        S   set by the person, one tap\n"
   "     ordered_again_at  S   filled in later, for the recovery measure\n\n"
   "`ordered_again_at` is written by a monthly backfill, and it is the only\n"
   "field that measures whether any of this worked."),
  ("Table: asks",
   "PK   customer          S   the customer identifier\n"
   "SK   order_id          S   the order asked about\n"
   "     asked_at          S   2026-08-07T09:00:00Z\n"
   "     token             S   hash of the signed token\n"
   "     responded         BOOL false\n\n"
   "Two caps enforced from one table: one row per order prevents asking twice\n"
   "about the same thing, and a query by customer with a date bound enforces\n"
   "the per-person frequency cap.")],
 inbound=[
  "<strong>Survey links carry a signed order token</strong>, single-use for recording, so a "
  "response arrives already attached to a specific transaction rather than to a customer.",
  "<strong>The receive endpoint always returns success</strong>, including for an invalid or "
  "reused token, and records the anomaly. A customer who clicks twice should not see an error "
  "page.",
  "<strong>Routing uses SNS to a person's own endpoint</strong>, never a shared inbox, with a "
  "sixty-minute acknowledgement timeout that re-routes to the next person on the rota.",
  "<strong>Context lookups are read-only</strong> against commerce and helpdesk, with separate "
  "credentials, and a failed lookup renders as an explicit note rather than a blank section."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "doing two things in one call: classifying into your fixed theme list and flagging serious "
  "content.",
  "<strong>Called once per response with a comment.</strong> A score with no comment never "
  "reaches it.",
  "<strong>Grounded</strong> with your theme list, so it returns one of your labels or unmatched "
  "and never invents a theme.",
  "<strong>It never drafts a reply.</strong> A generated apology to somebody who is already "
  "annoyed is transparent and makes the situation worse, which is a rare case of the obvious "
  "feature being clearly wrong.",
  "<strong>The serious-content check errs upward.</strong> A false escalation costs somebody two "
  "minutes; a missed safety comment does not."],
 gotchas=[
  "Token the order, not the customer. It is the difference between a reply that asks what "
  "happened and one that already knows.",
  "Enforce both caps. One ask per order and a per-person frequency cap; either alone leaves a "
  "failure mode open.",
  "Check for serious content before looking at the score. The eight out of ten mentioning an "
  "injury is the response that matters most that week.",
  "Route to a named person with an acknowledgement timeout. A shared inbox is where responses go "
  "to wait for somebody else.",
  "Report the ask rate next to the score. It is the cheapest defence against the most common way "
  "a satisfaction number gets improved without anything improving."],
))
