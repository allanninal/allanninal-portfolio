"""Day 88 -- 2026-07-21 -- Exit interview collector."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "exit-interview-collector"
NAME = "Exit interview collector"

SPEC = {
 "slug": SLUG, "date": "2026-07-21", "name": NAME,
 "tagline": ("The honest answer arrives six weeks after somebody leaves, not on their last "
             "afternoon -- so this asks twice, and reports themes across people rather than "
             "quotes from one."),
 "lede": ("A small system that asks a leaver the same short set of questions twice -- once "
          "before they go and once six weeks later -- keeps the answers separate from the "
          "person, and only reports a theme once several people have said the same thing. It "
          "never shows a single response to a manager. Seven posts on the same system -- one "
          "diagram at a time -- with a cost breakdown and an engineering reference at the end."),
 "keywords": ["exit interviews", "staff retention", "feedback", "anonymity", "HR",
              "serverless"],
 "icons": ["chat", "clock", "chart"],
 "faq": [
  ("What is an exit interview collector?",
   "A small serverless system that asks leavers a short set of questions twice -- on the way "
   "out and again six weeks later -- and reports themes across several people rather than "
   "individual responses. A manager never sees one person's answers."),
  ("Why ask twice?",
   "Because the answer on the last afternoon is filtered through wanting a reference and not "
   "wanting a scene. Six weeks later, in a new job, the same person will tell you what actually "
   "happened. The second response is consistently more useful and it is the one almost nobody "
   "collects."),
  ("How is it anonymous if you know who left?",
   "Honestly: with a small team it cannot be fully anonymous, and the system says so rather "
   "than pretending. What it does is hold responses separately from identities, and refuse to "
   "surface anything until several people have said something similar -- so a report is about a "
   "pattern, never about a person."),
  ("Can a manager see what their own leaver said?",
   "No. That is the one hard rule. A system that can be asked what one person said is a system "
   "people answer carefully, and carefully-answered exit interviews are worthless."),
  ("What does it cost to run?",
   "A couple of dollars a month. Leaver volume is low. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "exit-interview-collector-on-aws",
 "title": "An exit interview collector on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 880,
 "desc": ("Asks leavers the same questions twice, six weeks apart, keeps answers separate from "
          "people, and reports only themes. AWS, about $2 a month."),
 "og": ("The useful answer comes six weeks after somebody leaves, not on their last afternoon. "
        "This asks twice and reports patterns rather than quotes."),
 "abstract": ("The whole system on one page -- a two-stage asker, a separated store and a theme "
              "reporter -- built around one observation: the honest answer arrives late."),
 "lede": ("Exit interviews are almost universally done and almost universally useless, and the "
          "reason is timing. The conversation happens on somebody's last afternoon, with a "
          "reference outstanding and a leaving card being passed around, and what comes out is "
          "\"a great opportunity came up\". Six weeks later the same person, settled somewhere "
          "else, will tell you exactly what happened &mdash; and nobody ever asks. This post "
          "walks through a small system built entirely around that gap."),
 "tags": ["exit interviews", "staff retention", "feedback", "anonymity", "HR", "serverless"],
 "takeaways": [
  "The same short questionnaire twice: at exit, and again six weeks later.",
  "The second response is the useful one, and it is the one almost nobody collects.",
  "Answers are stored apart from identities and joined only in aggregate.",
  "Nothing surfaces until several people have said something similar.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Leaver", "sub": ["asked twice"], "icon": "person"},
      {"title": "Question set", "sub": ["six, unchanged"], "icon": "doc"},
      {"title": "Whoever owns retention", "sub": ["sees themes only"], "icon": "team"}],
    "inside": [
      {"title": "Asker", "sub": ["at exit, and", "again at six weeks"], "icon": "clock"},
      {"title": "Separated store", "sub": ["responses apart", "from identities"], "icon": "lock"},
      {"title": "Theme reporter", "sub": ["only when several", "people agree"], "icon": "chart"}],
    "edges": [{"from": 0, "to": 0, "label": "answers"},
              {"from": 1, "to": 1, "label": "the questions"},
              {"from": 2, "to": 2, "label": "patterns, never quotes", "up": True}],
    "note": "No path exists by which a manager can read one person's answers. That is the design."}),
   "Three things outside the account, three pieces inside it. The middle box is not storage in "
   "the ordinary sense: it is the separation that makes honest answers possible.",
   "System: a leaver asked twice, themes reported, individuals never",
   "Three boxes across the top sit outside the AWS account. On the left, Leaver: the person "
   "leaving, asked twice. In the middle, Question set: six questions that never change. On the "
   "right, Whoever owns retention: the person who sees themes only. Each connects by an arrow to "
   "the AWS account container below. Answers flow down into the account. The question set feeds "
   "in. Patterns, never quotes, go back out. Inside the AWS account are three components in a "
   "row. On the left, the Asker, which asks at exit and again at six weeks. In the middle, the "
   "Separated store, which holds responses apart from identities. On the right, the Theme "
   "reporter, which surfaces something only when several people agree. A note at the bottom says "
   "no path exists by which a manager can read one person's answers, and that this is the "
   "design."),
  ("h3", "The six questions"),
  ("ol", [
   "What made you start looking?",
   "What would have made you stay?",
   "How was the work itself, day to day?",
   "How was your relationship with your manager?",
   "Was there anything you wanted to raise while you were here and did not?",
   "Would you recommend working here to a friend?",
  ]),
  ("p", "Six, short, and identical both times. The temptation is to add a rating scale, a "
        "department-specific section and a free-text box for anything else, and the result is a "
        "questionnaire that takes fifteen minutes and gets abandoned. The fifth question is the "
        "one that consistently produces the most useful answer and the one most exit interviews "
        "do not ask."),
  ("h3", "What runs on every leaver (the inside)"),
  ("ul", [
   "<strong>The asker.</strong> Sends a link on the last day and another six weeks later. The "
   "second is sent to a personal address, collected on the way out, because a work address will "
   "have been disabled and that is why almost nobody manages the follow-up.",
   "<strong>The separated store.</strong> Responses go in one table, identities in another, "
   "with no field joining them that any query in the system uses. Part 3 is entirely about "
   "this, because it is easy to claim and easy to get subtly wrong.",
   "<strong>The theme reporter.</strong> Groups answers into recurring themes and reports a "
   "theme only once several people have raised it. It never quotes. Part 5 covers why a quote is "
   "identifying even when a name is not attached.",
  ]),
  ("h2", "One leaver, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Notice given", "sub": ["a leaving date"], "icon": "calendar"},
      {"title": "Asked", "sub": ["on the last day"], "icon": "chat"},
      {"title": "Asked again", "sub": ["six weeks later"], "icon": "clock"},
      {"title": "Separated", "sub": ["answers, not people"], "icon": "lock"},
      {"title": "Themed", "sub": ["when several agree"], "icon": "chart"}],
    "title": "ONE LEAVER, END TO END",
    "note": "The third box is what almost nobody does, and it is where the value is."}),
   "The same system as one line. The six-week follow-up is the only unusual step and it is the "
   "one that produces the answers worth having.",
   "One leaver from notice to reported theme, in five stages",
   "A horizontal row of five boxes joined by arrows. Notice given: a leaving date is set. Asked: "
   "on the last day. Asked again: six weeks later. Separated: answers are stored apart from "
   "people. Themed: reported when several people agree. A note says the third box is what almost "
   "nobody does and it is where the value is."),
  ("h2", "In plain words"),
  ("p", "Somebody resigns in June with a leaving date of the 10th of July. On the 10th they get "
        "a link to six questions, and they answer them: a great opportunity, nothing really, the "
        "work was fine, my manager was fine, no, probably yes. That is a perfectly ordinary exit "
        "interview and it contains no information at all."),
  ("p", "On the 21st of August, six weeks on, they get the same six questions at the personal "
        "address they gave on the way out. They are three weeks into a new job and have no "
        "outstanding reference. This time: I started looking after the rota changed in "
        "February; a conversation about the rota would have kept me; the work was good; my "
        "manager was fine but had no say in the rota; yes, I raised it twice and nothing "
        "happened; no. That is a completely different set of answers and every one of them is "
        "actionable."),
  ("p", "Nothing is reported yet. Two months later a third person says something similar about "
        "the same rota change, and the theme reporter surfaces it: three of the last seven "
        "leavers mentioned scheduling, two said they raised it and nothing happened. That "
        "sentence is the product, and it took no interviews, no consultant, and about four "
        "seconds of compute."),
  ("callout", "Design rules that shaped every decision", [
   "Ask twice, and mean it. The second response is the useful one and it needs a personal "
   "address collected while somebody is still there.",
   "The same six questions both times. Comparing the two answers to the same question is where "
   "the insight lives.",
   "Responses are stored apart from identities, with no join any query uses.",
   "Nothing surfaces below a threshold of several people. One person's answer is a confidence, "
   "not a finding.",
   "Never quote. A verbatim sentence identifies its author in a small team more reliably than a "
   "name would.",
   "Be honest about anonymity. With eleven staff, nothing is truly anonymous, and claiming "
   "otherwise is worse than saying so.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The standard exit interview fails for a structural reason that no amount of better "
        "questions will fix: the person answering has three live incentives to be diplomatic. "
        "They want a reference, they may need to come back, and they do not want their last "
        "memory of the place to be an argument. Six weeks later, all three have gone."),
  ("p", "So the design spends its effort on two things: getting the second response at all, "
        "which is mostly about collecting a personal address before somebody's account is "
        "disabled, and making the reporting safe enough that people believe answering honestly "
        "carries no risk. Everything else is a form and a table."),
  ("p", "The next four posts walk through each piece: how the two asks are timed, how the "
        "separation actually works, how themes get found, and what the report says. One diagram "
        "per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-the-two-asks-are-timed",
 "title": "How the two asks are timed",
 "nav": "How asks are timed",
 "read": 5, "words": 770,
 "desc": ("Getting a personal address before the account is disabled, why six weeks and not "
          "three, and what to do when the first ask is ignored."),
 "og": ("The follow-up fails for one banal reason: nobody collected a personal address. Getting "
        "that on the way out is most of the engineering."),
 "abstract": ("Collecting a personal address before the account is disabled, why six weeks "
              "rather than three, and what happens when the first ask is ignored."),
 "lede": ("The whole system rests on a message arriving six weeks after somebody has left, and "
          "that fails for a completely banal reason: their work address stopped working on their "
          "last day and nobody thought to ask for another one. This post is mostly about "
          "solving that."),
 "tags": ["exit interviews", "HR", "scheduling", "email", "retention", "serverless"],
 "takeaways": [
  "The personal address is collected on the last day, as part of the first ask.",
  "Six weeks is chosen because it is past the new-job honeymoon and before memory fades.",
  "An ignored first ask does not cancel the second. They are independent.",
  "One reminder each, and then silence. A leaver owes you nothing.",
  "The ask says plainly what happens to the answers, because that determines the answers.",
 ],
 "blocks": [
  ("h2", "Collecting the address"),
  ("fig", ("chain", {
    "entry": {"title": "Leaving date set", "sub": ["from HR"], "icon": "calendar"},
    "steps": [
      {"title": "Ask on the last day", "sub": ["six questions,", "plus one field"], "icon": "chat"},
      {"title": "Personal address given?", "icon": "branch",
       "side": {"title": "The one field", "sub": ["optional, explained"], "icon": "email"},
       "exit": {"title": "No follow-up possible", "sub": ["recorded honestly"], "icon": "stop",
                "label": "no"}},
      {"title": "Schedule at +6 weeks", "sub": ["one event, dated"], "icon": "clock"},
      {"title": "Ask again", "sub": ["same six questions"], "icon": "retry"},
      {"title": "Two responses", "sub": ["comparable, by design"], "icon": "counter"}],
    "note": "The exit branch is common and is recorded rather than hidden. It is the coverage number."}),
   "How the follow-up becomes possible. The single optional field on the first form determines "
   "whether the more valuable second response can ever be collected.",
   "How the six-week follow-up is made possible on the last day",
   "A vertical chain of five steps entered by a box labelled Leaving date set, from HR. Step one "
   "asks on the last day, with six questions plus one extra field. Step two asks whether a "
   "personal address was given, that field being optional and explained; if not it exits to No "
   "follow-up possible, recorded honestly. Step three schedules the second ask at six weeks as "
   "one dated event. Step four asks again with the same six questions. Step five yields two "
   "responses that are comparable by design. A note says the exit branch is common, is recorded "
   "rather than hidden, and is the coverage number."),
  ("h3", "How the field is worded"),
  ("p", "\"If you are happy to, leave a personal email address. We will ask you the same six "
        "questions again in six weeks, when you have some distance from this. Nobody here will "
        "see either set of answers on their own.\" That is the whole explanation, and it belongs "
        "on the form rather than in a policy document nobody opens."),
  ("p", "Roughly half of leavers give one, which is enough. The half who do not are not a "
        "failure; they are a coverage statistic that the report states plainly, because a themes "
        "report drawn from half your leavers should say so."),
  ("h2", "Why six weeks"),
  ("ul", [
   "<strong>Three weeks is too soon.</strong> The new job is still new, everything is still "
   "better, and the answers are coloured by relief rather than reflection.",
   "<strong>Six weeks is past the honeymoon.</strong> The new place has revealed its own "
   "problems, which makes the comparison honest in both directions &mdash; people quite often "
   "say the old job was better at something.",
   "<strong>Three months is too late.</strong> Specific memories fade into general impressions, "
   "and \"the rota changed in February and nobody consulted us\" becomes \"communication was "
   "poor\", which is not actionable.",
   "<strong>It is a setting.</strong> Six weeks is a default that has worked; it lives in a "
   "sheet, and a business with a longer notice culture may want eight.",
  ]),
  ("h2", "What happens when nobody answers"),
  ("p", "One reminder per ask, five days later, and then nothing. A leaver has no obligation to "
        "you and a third message is a nuisance from a place they have left."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Ask 1 ignored", "sub": ["no answer"], "icon": "stop"},
      {"title": "Ask 2 still sent", "sub": ["independent"], "icon": "retry"},
      {"title": "Ask 2 answered", "sub": ["it happens often"], "icon": "check"},
      {"title": "One reminder each", "sub": ["then silence"], "icon": "bell"},
      {"title": "Coverage recorded", "sub": ["stated in the report"], "icon": "counter"}],
    "title": "THE TWO ASKS ARE INDEPENDENT",
    "note": "A leaver who ignored the last-day form frequently answers the one six weeks later."}),
   "Why the two asks do not depend on each other. Treating the first as a prerequisite would "
   "discard the more valuable response from exactly the people least willing to talk on their "
   "last day.",
   "Why the exit ask and the six-week ask are independent",
   "A horizontal row of five boxes. Ask one ignored: no answer. Ask two still sent: the two are "
   "independent. Ask two answered: which happens often. One reminder each: then silence. "
   "Coverage recorded: and stated in the report. A note says a leaver who ignored the last-day "
   "form frequently answers the one six weeks later."),
  ("p", "That independence is a small implementation detail with a real effect. The people least "
        "willing to fill in a form on their last afternoon are frequently the people with the "
        "most to say, and a design that treats the first response as a prerequisite for the "
        "second loses exactly them."),
  ("p", "Next: how the answers are kept apart from the people who gave them."),
 ],
},
{
 "slug": "how-answers-stay-separate-from-people",
 "title": "How answers stay separate from people",
 "nav": "How it separates",
 "read": 5, "words": 790,
 "desc": ("Two tables with no usable join, why the link token is one-way, and being honest that "
          "with eleven staff nothing is truly anonymous."),
 "og": ("Two tables, no usable join, and a one-way token. Plus the honest admission that in a "
        "team of eleven, anonymity is a promise nobody can keep."),
 "abstract": ("Two tables with no join any query uses, a one-way token, what a leak would "
              "actually expose, and the honest admission that a small team cannot be truly "
              "anonymous."),
 "lede": ("This is the part that determines whether anybody answers honestly, and it is easy to "
          "claim and easy to get subtly wrong. The claim being made is specific and limited, and "
          "worth stating precisely rather than as a reassuring adjective."),
 "tags": ["exit interviews", "anonymity", "data separation", "DynamoDB", "privacy", "serverless"],
 "takeaways": [
  "Two tables: leavers, and responses. No query in the system joins them.",
  "The token linking a response to an ask is one-way and is not stored on the leaver.",
  "The pair of responses from one person is linkable to each other, and to nobody.",
  "What a leak would expose is stated plainly, because vague reassurance is not a control.",
  "In a team of eleven, anonymity is not achievable and the system says so.",
 ],
 "blocks": [
  ("h2", "Two tables"),
  ("fig", ("chain", {
    "entry": {"title": "A leaver", "sub": ["name, dates, address"], "icon": "person"},
    "steps": [
      {"title": "Mint a response token", "sub": ["random, not derived"], "icon": "key",
       "side": {"title": "Leavers table", "sub": ["stores the token", "hash, not the token"],
                "icon": "database"}},
      {"title": "Send the link", "sub": ["token in the URL"], "icon": "email"},
      {"title": "Answers come back", "sub": ["keyed by token"], "icon": "chat",
       "side": {"title": "Responses table", "sub": ["no name, no email,", "no leaving date"],
                "icon": "lock"}},
      {"title": "Aggregate only", "sub": ["counts and themes"], "icon": "chart"}],
    "note": "The token is random. Knowing a leaver tells you nothing about which responses are theirs."}),
   "How the two tables stay apart. The token is random rather than derived, which is the "
   "difference between a separation and the appearance of one.",
   "How exit responses are stored separately from leaver identities",
   "A vertical chain of four steps entered by a box labelled A leaver, holding a name, dates and "
   "an address. Step one mints a response token that is random rather than derived, storing only "
   "its hash on the leavers table. Step two sends the link with the token in the URL. Step three "
   "receives the answers keyed by token into a responses table that holds no name, no email and "
   "no leaving date. Step four aggregates only, producing counts and themes. A note says the "
   "token is random, so knowing a leaver tells you nothing about which responses are theirs."),
  ("h3", "Why random rather than derived"),
  ("p", "A token derived from an identity &mdash; a hash of the email address, say &mdash; feels "
        "clean and defeats the whole purpose. Anybody holding the list of leavers can compute the "
        "same hash and look up the responses. The separation is only real if the mapping cannot "
        "be recomputed, which means the token is random and the leaver row holds a hash of it "
        "rather than the token itself."),
  ("p", "The consequence is that once a link is sent, nobody at your end can determine whose "
        "responses are whose. That includes whoever built the system, which is the property that "
        "makes the claim credible."),
  ("h3", "What is linkable"),
  ("p", "The two responses from one person are linkable to each other, because both asks use the "
        "same token. That is deliberate and it is what makes the comparison in Part 4 possible. "
        "They are not linkable to a name, a role, a department, a manager or a leaving date."),
  ("p", "The leaving date is worth calling out. It is enormously tempting to store it on the "
        "response &mdash; it would let you trend feedback over time &mdash; and in a business "
        "with a handful of leavers a quarter it is very nearly an identity. So responses carry "
        "only the quarter they were collected in, and even that is only used once the quarter has "
        "several responses in it."),
  ("h2", "Being honest about the limits"),
  ("callout", "What this system does and does not promise", [
   "<strong>It promises:</strong> nobody at your business can look up what one named person "
   "said, including whoever administers the system.",
   "<strong>It promises:</strong> no single response is ever shown to anybody, in any report, in "
   "any form.",
   "<strong>It does not promise anonymity.</strong> With eleven staff and two leavers this "
   "quarter, a theme about the warehouse rota is attributable by anybody who was there.",
   "<strong>It says so on the form.</strong> \"We cannot promise you cannot be identified from "
   "what you say. We can promise nobody here will be shown your answers on their own.\"",
   "<strong>A leak would expose:</strong> a set of responses with no names attached, and a "
   "separate list of who left. Joining them would require the tokens, which are not stored.",
  ]),
  ("p", "That third bullet is uncomfortable and belongs on the form. Systems that promise "
        "anonymity they cannot deliver get one round of honest answers, and then somebody works "
        "out who said what, and the well is poisoned for years. Promising less and delivering it "
        "is the only version that survives."),
  ("h2", "Deletion"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Leaver row", "sub": ["deleted at 12 months"], "icon": "person"},
      {"title": "Token hash", "sub": ["goes with it"], "icon": "key"},
      {"title": "Responses", "sub": ["kept, unlinkable"], "icon": "chat"},
      {"title": "Themes", "sub": ["still work"], "icon": "chart"},
      {"title": "Nothing to join", "sub": ["permanently"], "icon": "lock"}],
    "title": "WHAT DELETION LEAVES",
    "note": "After twelve months the separation is not a policy any more; it is arithmetic."}),
   "What is deleted and what remains. Removing the leaver row makes the separation permanent "
   "rather than procedural, and the themes keep working because they never used identities.",
   "What remains after a leaver record is deleted",
   "A horizontal row of five boxes. Leaver row: deleted at twelve months. Token hash: goes with "
   "it. Responses: kept, and now unlinkable. Themes: still work. Nothing to join: permanently. A "
   "note says after twelve months the separation is not a policy any more but arithmetic."),
  ("p", "Deleting the leaver row at twelve months costs nothing &mdash; the responses do not need "
        "it and the themes never used it &mdash; and it converts the separation from something "
        "enforced by code into something enforced by the absence of data. That is a much stronger "
        "position to be in if anybody ever asks."),
  ("p", "Next: how the answers become themes."),
 ],
},
{
 "slug": "how-themes-get-found",
 "title": "How themes get found",
 "nav": "How themes are found",
 "read": 5, "words": 780,
 "desc": ("Grouping free-text answers into recurring themes, the threshold below which nothing "
          "is reported, and the comparison between the two responses that nobody else has."),
 "og": ("Themes across leavers rather than quotes from one. Plus the comparison only this "
        "design can make: what the same person said on the last day versus six weeks later."),
 "abstract": ("Grouping free-text answers into recurring themes, the threshold below which "
              "nothing is reported at all, and the comparison between a person's two responses "
              "that no ordinary exit process can make."),
 "lede": ("Six free-text answers from each of a handful of leavers is not much data, which is "
          "both the constraint and the reason this works. There is no statistics here; there is "
          "grouping, a threshold, and one comparison that is unique to asking twice."),
 "tags": ["exit interviews", "AWS Bedrock", "thematic analysis", "retention", "reporting",
          "serverless"],
 "takeaways": [
  "Themes come from a fixed list you maintain, not from free clustering.",
  "Nothing is reported below three people. Two is a coincidence.",
  "A theme carries a count and a direction, never a quote.",
  "The comparison between ask one and ask two is the finding nobody else has.",
  "An answer that matches no theme is counted as unmatched, which is itself a signal.",
 ],
 "blocks": [
  ("h2", "A fixed theme list"),
  ("p", "The instinct is to let a model cluster free text and name the clusters. It produces "
        "different groupings every time it runs, which makes trends impossible, and it "
        "occasionally names a cluster in a way that is effectively a quote."),
  ("p", "So the themes are a list you maintain &mdash; pay, scheduling, workload, management, "
        "progression, environment, commute, a better offer &mdash; and the model's job is "
        "classification into that list, or none. Same input, same output, every time, and trends "
        "over quarters mean something."),
  ("fig", ("chain", {
    "entry": {"title": "Six answers", "sub": ["one response"], "icon": "chat"},
    "steps": [
      {"title": "Classify each answer", "sub": ["one Bedrock call"], "icon": "model",
       "side": {"title": "Theme list", "sub": ["yours, fixed"], "icon": "doc"}},
      {"title": "Any themes matched?", "icon": "branch",
       "exit": {"title": "Count as unmatched", "sub": ["a signal in itself"], "icon": "search",
                "label": "none"}},
      {"title": "Increment the counts", "sub": ["per theme, per quarter"], "icon": "counter",
       "side": {"title": "Aggregate table", "sub": ["counts only"], "icon": "database"}},
      {"title": "Three or more people?", "sub": ["across the window"], "icon": "branch",
       "exit": {"title": "Hold it", "sub": ["not yet a theme"], "icon": "clock", "label": "no"}},
      {"title": "Reportable", "sub": ["a count and a direction"], "icon": "chart"}],
    "note": "The text is never stored on the aggregate. Only counts cross into the report."}),
   "How six free-text answers become a countable theme. The last step is a threshold, not a "
   "statistic: three people is the point at which something stops being one person's experience.",
   "How free-text exit answers become reportable themes",
   "A vertical chain of five steps entered by a box labelled Six answers, from one response. "
   "Step one classifies each answer with a single Bedrock call against your own fixed theme "
   "list. Step two asks whether any themes matched; none exits to Count as unmatched, which is a "
   "signal in itself. Step three increments the counts per theme per quarter in an aggregate "
   "table holding counts only. Step four asks whether three or more people have raised it across "
   "the window; fewer exits to Hold it, not yet a theme. Step five is Reportable, carrying a "
   "count and a direction. A note says the text is never stored on the aggregate and only counts "
   "cross into the report."),
  ("h3", "Three, not two"),
  ("p", "Two people mentioning scheduling in a quarter is a coincidence in a small business, and "
        "reporting it produces a manager who can name both of them. Three is the smallest number "
        "at which a pattern is more likely than a coincidence and at which attribution starts to "
        "get genuinely difficult."),
  ("p", "The threshold is a setting, and the honest guidance is that raising it is safer than "
        "lowering it. A business with forty leavers a year could reasonably use five."),
  ("h3", "Unmatched answers"),
  ("p", "An answer that matches no theme is counted as unmatched rather than discarded, and a "
        "rising unmatched count is one of the more useful signals the system produces: it means "
        "people are leaving for reasons your theme list does not contain. Reviewing the unmatched "
        "answers &mdash; which requires somebody senior reading raw text, deliberately and "
        "rarely &mdash; is how the theme list gets updated."),
  ("h2", "The comparison nobody else has"),
  ("p", "Because the same person answers the same six questions twice, the system can do "
        "something no ordinary exit process can: compare them."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Ask 1 themes", "sub": ["better offer: 6"], "icon": "chat"},
      {"title": "Ask 2 themes", "sub": ["better offer: 2"], "icon": "clock"},
      {"title": "What replaced it", "sub": ["scheduling: 4"], "icon": "search"},
      {"title": "The gap", "sub": ["what people would not say"], "icon": "counter"},
      {"title": "Reported", "sub": ["as a gap, not a quote"], "icon": "chart"}],
    "title": "WHAT CHANGES BETWEEN THE TWO ASKS",
    "note": "The gap is the whole argument for asking twice, and it is measurable."}),
   "The difference between the two rounds of answers. The shift from a better offer to something "
   "specific is the measurable form of the thing everybody suspects about exit interviews.",
   "How the two rounds of answers differ, and what that reveals",
   "A horizontal row of five boxes. Ask one themes: a better offer, mentioned six times. Ask two "
   "themes: a better offer, mentioned twice. What replaced it: scheduling, four times. The gap: "
   "what people would not say on their last day. Reported: as a gap rather than a quote. A note "
   "says the gap is the whole argument for asking twice and it is measurable."),
  ("p", "That shift &mdash; six people citing a better offer on the way out, two of them still "
        "saying it six weeks later, and scheduling appearing in its place &mdash; is the single "
        "most persuasive output this system produces, because it is the measurable version of "
        "something everybody already suspects about exit interviews and nobody has ever been able "
        "to demonstrate."),
  ("p", "Next: what the report says, and everything it refuses to say."),
 ],
},
{
 "slug": "how-the-retention-report-reads",
 "title": "How the retention report reads",
 "nav": "How it reads",
 "read": 5, "words": 760,
 "desc": ("Counts and directions, no quotes, and the coverage line that stops the report being "
          "over-read -- plus why a quarterly cadence beats a live dashboard."),
 "og": ("Counts, directions and a coverage line. No quotes, no departments, no dashboard -- "
        "because each of those is a way of identifying somebody."),
 "abstract": ("Counts and directions rather than quotes, the coverage line that stops the report "
              "being over-read, and why a quarterly cadence is safer than a live dashboard."),
 "lede": ("The report is short, boring, and carefully stripped of everything that would make it "
          "more interesting, because every one of those things is a way of identifying somebody. "
          "What is left is still enough to change how a business runs."),
 "tags": ["exit interviews", "reporting", "retention", "anonymity", "HR", "serverless"],
 "takeaways": [
  "Counts and directions only. No quotes, ever, however anonymised they look.",
  "No department, role or manager breakdown. In a small business those are names.",
  "A coverage line at the top, so the report is not read as more than it is.",
  "Quarterly, not live. A dashboard updating after one response is a name with a delay.",
  "The unmatched count is reported, because it says the theme list is out of date.",
 ],
 "blocks": [
  ("h2", "What the page says"),
  ("callout", "Q3 2026 &mdash; leavers", [
   "<strong>Coverage.</strong> 7 leavers. 5 answered at exit, 4 answered at six weeks, 3 "
   "answered both.",
   "<strong>Scheduling &mdash; 4 people, rising.</strong> Up from 1 last quarter. Two said they "
   "raised it while employed.",
   "<strong>Progression &mdash; 3 people, flat.</strong> Same as the last two quarters.",
   "<strong>A better offer &mdash; 5 at exit, 2 at six weeks.</strong> The gap is the largest "
   "recorded so far.",
   "<strong>Unmatched &mdash; 3 answers.</strong> Above the usual 1. Worth a read of the theme "
   "list.",
   "<em>No individual response is shown. Themes need three people before they appear.</em>",
  ]),
  ("p", "Five lines and a footer. The coverage line is first because it determines how much "
        "weight the rest deserves: three people answering both asks out of seven leavers is a "
        "real signal and a small one, and putting that at the top stops the report being quoted "
        "in a board meeting as though it were a survey."),
  ("h2", "Everything it refuses to include"),
  ("fig", ("chain", {
    "entry": {"title": "A tempting addition", "sub": ["asked for regularly"], "icon": "chat"},
    "steps": [
      {"title": "A representative quote", "sub": ["'just one, anonymised'"], "icon": "branch",
       "exit": {"title": "Refused", "sub": ["a sentence is a fingerprint"], "icon": "stop",
                "label": "no"}},
      {"title": "Breakdown by department", "sub": ["'to target the fix'"], "icon": "branch",
       "exit": {"title": "Refused", "sub": ["a department of four is four names"],
                "icon": "stop", "label": "no"}},
      {"title": "Breakdown by manager", "sub": ["'for their development'"], "icon": "branch",
       "exit": {"title": "Refused", "sub": ["this is the one people ask for"], "icon": "stop",
                "label": "no"}},
      {"title": "A live dashboard", "sub": ["'so we see it sooner'"], "icon": "branch",
       "exit": {"title": "Refused", "sub": ["a count that moves is a person"], "icon": "stop",
                "label": "no"}},
      {"title": "Counts and directions", "sub": ["what is left"], "icon": "chart"}],
    "note": "Each of these is a reasonable request and each is a way to identify somebody."}),
   "The four additions that get requested and are refused. None of them is unreasonable and all "
   "four defeat the property the whole system depends on.",
   "Four report features that are deliberately refused",
   "A vertical chain of five steps entered by a box labelled A tempting addition, asked for "
   "regularly. Step one is a representative quote, described as just one and anonymised; it "
   "exits to Refused, because a sentence is a fingerprint. Step two is a breakdown by "
   "department, to target the fix; refused, because a department of four is four names. Step "
   "three is a breakdown by manager, framed as for their development; refused, and noted as the "
   "one people ask for. Step four is a live dashboard, so it is seen sooner; refused, because a "
   "count that moves is a person. Step five is Counts and directions, which is what remains. A "
   "note says each of these is a reasonable request and each is a way to identify somebody."),
  ("h3", "Why a quote is worse than a name"),
  ("p", "A quote is presented as the safe compromise: no name attached, just what somebody "
        "actually said. In a business of thirty people, a sentence about a specific incident, in "
        "somebody's own phrasing, identifies them more reliably than a name would &mdash; because "
        "everybody knows who was involved, and now they also know what that person said about "
        "it. There is no way to anonymise a quote that survives contact with colleagues."),
  ("h3", "Why the manager breakdown is the one people ask for"),
  ("p", "And it is the one that must never exist, for a reason that has nothing to do with "
        "protecting managers. The moment a report can show what a manager's leavers said, "
        "everybody in the business understands that answering honestly is an accusation against a "
        "named person. Answers become diplomatic within one quarter and the system produces "
        "nothing useful ever again."),
  ("p", "The thing to do with a scheduling theme is fix the scheduling. If the fix requires "
        "knowing where, that is a conversation somebody has with people who still work there, "
        "which is a better conversation anyway."),
  ("h2", "Why quarterly"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Live count", "sub": ["moves on one answer"], "icon": "alarm"},
      {"title": "Who left", "sub": ["everybody knows"], "icon": "team"},
      {"title": "The join", "sub": ["is trivial"], "icon": "search"},
      {"title": "Quarterly", "sub": ["several people at once"], "icon": "calendar"},
      {"title": "Safe", "sub": ["and still timely enough"], "icon": "check"}],
    "title": "WHY THERE IS NO DASHBOARD",
    "note": "A live count and a known leaving date are the same thing as a name."}),
   "Why the report is quarterly rather than live. A count that moves the week somebody left is "
   "attributable by anyone who noticed they left.",
   "Why exit themes are reported quarterly rather than on a live dashboard",
   "A horizontal row of five boxes. Live count: moves on a single answer. Who left: everybody "
   "knows. The join: is trivial. Quarterly: several people are reported at once. Safe: and still "
   "timely enough. A note says a live count and a known leaving date are the same thing as a "
   "name."),
  ("p", "A quarter is late enough that several responses are pooled and early enough that a "
        "rising theme can still be acted on within the same year. It is not a compromise on "
        "speed so much as a recognition that this data is about patterns, and a pattern that is "
        "only visible within a week is not a pattern."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="response",
 volumes=[(4, "4 responses"), (14, "14 responses"), (50, "50 responses")],
 read_each=0.0019, msgs_each=2.0,
 lede=("Leaver volume is low and each leaver produces at most two responses, so this is the "
       "smallest workload in the series. Fourteen responses a quarter is a business of perhaps "
       "eighty people with ordinary turnover. Here is where each cent goes."),
 takeaway_extra=("At most two model calls per leaver, ever. There is no ongoing processing at "
                 "all between quarters."),
 risks=[
  "<strong>Re-classifying on every report run.</strong> Classification happens once per response "
  "and the result is stored as counts. Re-running the model at report time to regenerate themes "
  "would multiply the cost and, worse, would make trends unstable.",
  "<strong>Storing the raw text on the aggregate.</strong> Not a cost risk but the one that "
  "matters: an aggregate table that carries the original sentences is one query away from being "
  "a quote generator.",
  "<strong>Log retention left at never.</strong> This system runs a few times a quarter. Without "
  "a retention setting, logs will be the entire bill, and exit-interview logs are exactly the "
  "logs you least want kept indefinitely.",
 ],
 per_unit_note=("One model call per response, ever. A leaver who answers both asks costs two "
                "calls in total and then nothing for the rest of the system's life."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ei",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two deliberately unjoined tables, and the narrow model call."),
 outside=[
  {"title": "Question form", "sub": ["CloudFront + S3"], "icon": "form"},
  {"title": "Theme list", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["asks, reminders"], "icon": "email"}],
 inside=[
  {"title": "EventBridge", "sub": ["the six-week timer,", "the quarterly report"], "icon": "clock"},
  {"title": "Lambda x3", "sub": ["ask, classify, report"], "icon": "lambda"},
  {"title": "DynamoDB x3", "sub": ["leavers, responses,", "aggregates"], "icon": "database"}],
 note="us-east-1. One account. No query in this system joins leavers to responses.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The Question form, served as static files "
  "from S3 behind CloudFront. The Theme list, read through the Google Sheets API read-only. And "
  "SES outbound, carrying the asks and reminders. Inside the account, three groups. EventBridge "
  "carrying the six-week timer and the quarterly report schedule. Three Lambda functions named "
  "ask, classify and report. And three DynamoDB tables named leavers, responses and aggregates. "
  "A note gives the region as us-east-1, one account, and states that no query in this system "
  "joins leavers to responses."),
 functions=[
  ["<code>ei-ask</code>", "Function URL + EventBridge daily",
   "Mints tokens, sends both asks and their reminders", "15s / 512&nbsp;MB"],
  ["<code>ei-classify</code>", "Function URL",
   "Accepts a response by token; one Bedrock call into themes", "20s / 512&nbsp;MB"],
  ["<code>ei-report</code>", "EventBridge quarterly",
   "Applies the threshold and sends the themes page", "20s / 512&nbsp;MB"]],
 roles=[
  ["<code>ei-ask-role</code>",
   "<code>dynamodb:PutItem</code> (leavers), <code>ses:SendEmail</code>",
   "The leavers table; one verified identity"],
  ["<code>ei-classify-role</code>",
   "<code>bedrock:InvokeModel</code>, <code>dynamodb:PutItem</code>",
   "One model arn; responses and aggregates &mdash; no read on leavers at all"],
  ["<code>ei-report-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "The aggregates table only; one verified identity"]],
 tables=[
  ("Table: leavers",
   "PK   leaver_id         S   lv_2026_07_21_7b3d\n"
   "     name              S   for the ask only\n"
   "     work_email        S   for ask one\n"
   "     personal_email    S   for ask two, if given\n"
   "     leaving_date      S   2026-07-10\n"
   "     token_hash        S   sha256 of the response token\n"
   "     ask2_due          S   2026-08-21\n"
   "     ttl               N   epoch, +12 months\n\n"
   "The token itself is NEVER stored. Only its hash, and only here -- which\n"
   "means the mapping cannot be recomputed from either side."),
  ("Table: responses",
   "PK   token             S   the random token, from the link\n"
   "SK   round             S   exit | followup\n"
   "     answers           L   six free-text answers\n"
   "     quarter           S   2026-Q3   -- the coarsest useful time key\n"
   "     ttl               N   epoch, +3 years\n\n"
   "No name, no email, no role, no manager, no leaving date. The quarter is\n"
   "the only temporal field and it is only reported once several responses\n"
   "share it."),
  ("Table: aggregates",
   "PK   quarter           S   2026-Q3\n"
   "SK   theme             S   scheduling | progression | unmatched | ...\n"
   "     exit_count        N   how many raised it at exit\n"
   "     followup_count    N   how many raised it at six weeks\n"
   "     people            N   distinct tokens, for the threshold\n\n"
   "This is the only table the report function can read. It contains counts\n"
   "and no text, so there is no code path from a report to a sentence.")],
 inbound=[
  "The <strong>question form</strong> is static files in S3 behind CloudFront. The token in the "
  "URL is the only credential and there is no login.",
  "<strong>Tokens are random</strong>, 128 bits, minted once per leaver and used for both asks "
  "so the two responses are linkable to each other and to nothing else.",
  "<strong>The classify function cannot read the leavers table.</strong> Its IAM role has no "
  "permission on it, which makes the separation an access-control fact rather than a convention.",
  "<strong>The report function can read only the aggregates table</strong>, which holds no text. "
  "There is no permission by which a report could contain a quote."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "classifying six short answers into your fixed theme list.",
  "<strong>Called once per response</strong>, at submission, never again. Themes are stored as "
  "counts and the report never re-runs classification.",
  "<strong>Grounded</strong> with your theme list, so the output is one of your labels or none. "
  "It never names a theme of its own.",
  "<strong>Output is a JSON schema</strong> of theme labels only. The model is not asked to "
  "summarise, quote or characterise anything.",
  "<strong>Unmatched is a first-class output.</strong> A rising unmatched count is how the theme "
  "list gets updated, and forcing a match would hide that."],
 gotchas=[
  "Mint the token randomly. A token derived from an email address makes the whole separation "
  "recomputable by anybody holding the leaver list.",
  "Deny the classify role any access to the leavers table. A convention that the code does not "
  "join them is much weaker than a policy that says it cannot.",
  "Keep the raw answers off the aggregate table. It is the only thing standing between the "
  "report and a quote.",
  "Collect the personal address on the last day. It is the single point of failure for the more "
  "valuable second response.",
  "Say on the form what you can and cannot promise. Over-promising anonymity buys one round of "
  "honest answers and poisons the well afterwards."],
))
