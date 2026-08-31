"""Day 129 -- 2026-08-31 -- Incident postmortem collector."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "incident-postmortem-collector"
NAME = "Incident postmortem collector"

SPEC = {
 "slug": SLUG, "date": "2026-08-31", "name": NAME,
 "tagline": ("Captures the timeline while it is still recoverable, resists the urge to name one "
             "root cause, tracks the actions that come out of it, and makes old postmortems "
             "findable -- because the value is entirely in the reading, and nobody reads them."),
 "lede": ("A small system that assembles an incident timeline from what actually happened, holds "
          "a write-up that describes contributing conditions rather than a single cause, follows "
          "the action items to closure or to an honest abandonment, and surfaces relevant past "
          "incidents when a new one starts. Seven posts on the same system, one diagram at a "
          "time, with a cost breakdown and an engineering reference at the end."),
 "keywords": ["postmortem", "incident review", "blameless", "reliability", "learning",
              "serverless"],
 "icons": ["doc", "clock", "search"],
 "faq": [
  ("What is an incident postmortem collector?",
   "A small serverless system that captures incident timelines while they are fresh, holds the "
   "write-up, tracks the resulting actions, and makes past incidents findable when they are "
   "relevant."),
  ("Why not identify a root cause?",
   "Because incidents rarely have one. A single named cause is usually the last thing that "
   "changed, and stopping there hides the conditions that let it become an incident."),
  ("What happens to postmortem action items?",
   "In most organisations, nothing, which is why they get their own post. An action nobody "
   "intends to do should be closed as declined rather than left open forever."),
  ("Who is a postmortem written for?",
   "The people who were not there, including people who join in two years. That audience changes "
   "how it should be written."),
  ("What does it cost to run?",
   "A couple of dollars a month. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "incident-postmortem-collector-on-aws",
 "title": "An incident postmortem collector on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Captures timelines while fresh, holds the write-up, tracks the actions, and surfaces "
          "old incidents when relevant. AWS, about $2 a month."),
 "og": ("A postmortem nobody reads again is a document that cost four hours and taught one "
        "person something they already knew."),
 "abstract": ("The whole system on one page -- timeline, write-up, actions &mdash; and the "
              "observation that the value of a postmortem is realised entirely on re-reading."),
 "lede": ("Something broke on a Tuesday, four people spent two hours fixing it, somebody wrote it "
          "up on Thursday from memory, and the document went into a folder. Eleven months later "
          "something similar happens and nobody remembers the first one existed. The write-up was "
          "not the problem; nothing was ever going to bring it back at the moment it mattered."),
 "tags": ["postmortem", "incident review", "blameless", "reliability", "learning", "serverless"],
 "takeaways": [
  "Capture the timeline during the incident; memory degrades within hours.",
  "Contributing conditions, not a single root cause.",
  "Track actions to closure or to an honest declined.",
  "Surface relevant past incidents when a new one starts. That is the payoff.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "An incident", "sub": ["happening now"], "icon": "alarm"},
      {"title": "The people in it", "sub": ["busy, and later,", "tired"], "icon": "person"},
      {"title": "Everybody else", "sub": ["now, and in two years"], "icon": "search"}],
    "inside": [
      {"title": "Timeline", "sub": ["captured live,", "not remembered"], "icon": "clock"},
      {"title": "Write-up", "sub": ["conditions, not", "a single cause"], "icon": "doc"},
      {"title": "Actions and recall", "sub": ["followed, and", "found again"], "icon": "check"}],
    "edges": [{"from": 0, "to": 0, "label": "events as they happen"},
              {"from": 1, "to": 1, "label": "what they knew, when"},
              {"from": 2, "to": 2, "label": "a document that resurfaces", "up": True}],
    "note": "The last four words are the point. Everything before them is preparation."}),
   "Three things outside the account, three pieces inside it. The value is created on the right, "
   "months after the incident.",
   "System: incident timelines captured, written up, and resurfaced",
   "Three boxes across the top sit outside the AWS account. On the left, An incident happening "
   "now. In the middle, The people in it, busy and later tired. On the right, Everybody else, now "
   "and in two years. Each connects by an arrow to the AWS account container below. Events as "
   "they happen flow down into the account. What they knew and when feeds in. A document that "
   "resurfaces goes back out. Inside the AWS account are three components in a row. On the left, "
   "the Timeline, captured live rather than remembered. In the middle, the Write-up, describing "
   "conditions rather than a single cause. On the right, Actions and recall, followed and found "
   "again. A note at the bottom says the last four words are the point and everything before them "
   "is preparation."),
  ("h3", "The value is in the reading"),
  ("p", "Writing a postmortem teaches the author something and occasionally teaches the people "
        "who attend the review. That is a modest return on several hours of work by several "
        "people, and it is the entire return most organisations get."),
  ("p", "The larger return comes when somebody encounters a similar situation later and finds the "
        "earlier write-up. That happens by accident or not at all, unless something makes it "
        "happen, which is the third component and the one that is usually missing."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The timeline.</strong> Captured during, because it cannot be reconstructed "
   "afterwards. Part 2.",
   "<strong>The write-up.</strong> Structured around contributing conditions rather than a cause. "
   "Part 3.",
   "<strong>Actions and recall.</strong> Following the actions honestly, and putting old "
   "incidents in front of people at the moment they are relevant. Parts 4 and 5.",
  ]),
  ("h2", "One incident, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Declared 14:02", "sub": ["a channel opens"], "icon": "alarm"},
      {"title": "Timeline builds", "sub": ["as people talk"], "icon": "clock"},
      {"title": "Resolved 16:10", "sub": ["timeline already exists"], "icon": "check"},
      {"title": "Written up Thursday", "sub": ["from the timeline"], "icon": "doc"},
      {"title": "Resurfaced in June", "sub": ["when it nearly recurred"], "icon": "search"}],
    "title": "ONE INCIDENT, END TO END",
    "note": "The fifth box is where the four hours spent on the fourth box gets paid back."}),
   "The same system as one line. Everything is preparation for a moment nine months later.",
   "One incident from declaration through to being resurfaced later",
   "A horizontal row of five boxes joined by arrows. Declared at two minutes past two: a channel "
   "opens. Timeline builds as people talk. Resolved at ten past four: the timeline already "
   "exists. Written up on Thursday, from the timeline. Resurfaced in June, when it nearly "
   "recurred. A note says the fifth box is where the four hours spent on the fourth box gets paid "
   "back."),
  ("h2", "In plain words"),
  ("p", "Somebody declares an incident at two minutes past two. A channel opens and from that "
        "moment everything said in it is timestamped and kept. People are not asked to write a "
        "timeline; they are asked to work, and the timeline is a by-product of them talking to "
        "each other."),
  ("p", "It resolves at ten past four. On Thursday somebody writes it up, and the hardest part "
        "&mdash; what happened when, and what people believed at the time &mdash; is already "
        "there, with timestamps, rather than being reconstructed from four people's memories of a "
        "stressful afternoon."),
  ("p", "Three actions come out of it. Two are done within a month. The third is closed as "
        "declined in July with a stated reason, which is a better outcome than it sitting open "
        "for three years. And in June, when a similar alert fires, the earlier write-up appears "
        "next to it automatically."),
  ("callout", "Design rules that shaped every decision", [
   "Capture the timeline during, never after. Memory is the problem.",
   "Contributing conditions, plural. No single root cause field.",
   "No names in the causal chain. Roles and systems, not people.",
   "Every action has an owner, a date and an honest end state.",
   "Old incidents surface automatically when something similar happens.",
   "A near miss is worth writing up and almost never is.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Postmortem practice fails in three well-known ways. The timeline is written from memory "
        "and is therefore wrong in the specific places that matter. The analysis stops at the "
        "last thing that changed. And the actions accumulate unclosed until nobody believes the "
        "process produces anything."),
  ("p", "None of those are solved by a better template. They are solved by capturing at the right "
        "moment, structuring the write-up so that a single cause is not the obvious answer, and "
        "treating an action item as something with an end state rather than a wish."),
  ("p", "The next four posts walk through each piece: how the timeline gets assembled while it is "
        "fresh, why there is rarely one root cause, what happens to the action items, and how old "
        "postmortems get read again. One diagram per post, a cost breakdown, and an engineering "
        "reference at the end."),
 ],
},
{
 "slug": "how-the-timeline-gets-assembled",
 "title": "How the timeline gets assembled while it is fresh",
 "nav": "How the timeline is built",
 "read": 5, "words": 740,
 "desc": ("Why memory fails in specific ways, capturing as a by-product, and recording what people "
          "believed rather than what was true."),
 "og": ("Nobody remembers what they believed at 14:20. They remember what turned out to be true, "
        "which is a different and much less useful thing."),
 "abstract": ("How memory distorts an incident timeline, capturing events as a by-product of "
              "working, why beliefs matter more than facts, and what to capture automatically."),
 "lede": ("The timeline is the part of a postmortem that cannot be recovered later, and it is the "
          "part most processes leave until later."),
 "tags": ["postmortem", "timelines", "memory", "incident response", "capture", "serverless"],
 "takeaways": [
  "Hindsight rewrites memory towards what turned out to be true.",
  "Capture as a by-product of the work: the channel is the timeline.",
  "Record what people believed at the time, explicitly.",
  "Automatic events -- alerts, deploys, restarts -- go in with timestamps.",
  "One prompt at resolution catches what the channel missed.",
 ],
 "blocks": [
  ("h2", "How memory fails"),
  ("fig", ("chain", {
    "entry": {"title": "Writing up on Thursday", "sub": ["about Tuesday"], "icon": "doc"},
    "steps": [
      {"title": "You know the answer now", "sub": ["you did not then"], "icon": "search"},
      {"title": "So the wrong paths vanish", "sub": ["'we quickly identified...'"],
       "icon": "filter", "side": {"title": "But", "sub": ["40 minutes were spent there"],
                                  "icon": "clock"}},
      {"title": "And the times compress", "sub": ["two hours feels like one"], "icon": "clock"},
      {"title": "And the order shifts", "sub": ["towards a clean story"], "icon": "route"},
      {"title": "A tidy, false timeline", "sub": ["nobody lied"], "icon": "question"}],
    "note": "Every one of these is automatic and unconscious. Effort does not fix it."}),
   "How an accurate memory becomes an inaccurate timeline. None of it is dishonesty and none of "
   "it is avoidable by trying harder.",
   "How hindsight distorts a remembered incident timeline",
   "A vertical chain of five steps entered by a box labelled Writing up on Thursday about "
   "Tuesday. Step one notes that you know the answer now and did not then. Step two says the "
   "wrong paths vanish, phrased as we quickly identified, with a side box noting that forty "
   "minutes were spent there. Step three says the times compress, so two hours feels like one. "
   "Step four says the order shifts towards a clean story. Step five produces a tidy, false "
   "timeline, and nobody lied. A note says every one of these is automatic and unconscious, and "
   "effort does not fix it."),
  ("h3", "The wrong paths matter most"),
  ("p", "Forty minutes spent investigating a component that turned out to be fine is the most "
        "useful information in the whole incident, because it says something about what the "
        "system looks like from the outside during a failure."),
  ("p", "It is also the first thing hindsight deletes. The write-up says the cause was identified "
        "at twenty past two, and the forty minutes before it disappear, taking with them the "
        "finding that a misleading dashboard sent four people in the wrong direction."),
  ("h2", "Capture as a by-product"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Ask people to log", "sub": ["during the incident"], "icon": "form",
       "label": "does not happen"},
      {"title": "Reconstruct after", "sub": ["from memory"], "icon": "question",
       "label": "distorted"},
      {"title": "Use what they said", "sub": ["in the channel, timestamped"], "icon": "email",
       "label": "free and accurate"}],
    "target": {"title": "A raw timeline", "sub": ["before anybody writes"], "icon": "clock",
               "then": {"title": "Edited down later", "sub": ["removing, not recalling"],
                        "icon": "doc"}},
    "note": "Editing a real record down is a different task from remembering, and a much easier one."}),
   "Three ways of getting a timeline. Only the third produces an accurate one and it costs "
   "nothing during the incident.",
   "Three approaches to building an incident timeline",
   "Three boxes stacked on the left. Ask people to log during the incident, labelled does not "
   "happen. Reconstruct after from memory, labelled distorted. And Use what they said in the "
   "channel, timestamped, labelled free and accurate. All three converge on A raw timeline before "
   "anybody writes, and that leads down to Edited down later, removing rather than recalling. A "
   "note says editing a real record down is a different task from remembering and a much easier "
   "one."),
  ("h3", "The channel is the timeline"),
  ("p", "People in an incident talk to each other, and that conversation is already timestamped, "
        "already contains what they were trying, and already records the wrong turns. Treating it "
        "as the raw material rather than asking anybody for anything extra is the whole "
        "mechanism."),
  ("p", "The write-up then becomes an editing task: take four hundred messages, keep thirty, add "
        "structure. That is achievable on a Thursday afternoon in a way that reconstruction is "
        "not."),
  ("h2", "Beliefs, not facts"),
  ("callout", "The two columns that make a timeline useful", [
   "<strong>14:02</strong> &mdash; Alert fires. <em>Believed: a database problem, because that "
   "alert has meant that twice before.</em>",
   "<strong>14:11</strong> &mdash; Database checked, healthy. <em>Believed: probably the network "
   "then.</em>",
   "<strong>14:24</strong> &mdash; Network fine. <em>Believed: nobody has a hypothesis.</em>",
   "<strong>14:38</strong> &mdash; Someone mentions the deploy at 13:50. <em>Believed: possibly "
   "related.</em>",
   "<strong>14:52</strong> &mdash; Rolled back. Recovery begins.",
   "<strong>The italics are the postmortem.</strong> Without them this is a list of times.",
  ]),
  ("p", "The belief column is what turns a timeline into something you can learn from. The gap "
        "between 14:02 and 14:38 is not incompetence; it is a system whose failure signature "
        "pointed confidently at the wrong component, and that is a fixable thing."),
  ("p", "Capturing beliefs requires a small nudge during the incident: a prompt in the channel "
        "every so often asking what people currently think is happening. It is cheap and it "
        "produces the most valuable rows in the eventual document."),
  ("h2", "Automatic events"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Alerts", "sub": ["fired and resolved"], "icon": "alarm"},
      {"title": "Deploys", "sub": ["and rollbacks"], "icon": "route"},
      {"title": "Restarts", "sub": ["and scaling events"], "icon": "gear"},
      {"title": "Config changes", "sub": ["with who"], "icon": "form"},
      {"title": "Interleaved", "sub": ["with what people said"], "icon": "clock"}],
    "title": "WHAT GOES IN WITHOUT ANYBODY TYPING",
    "note": "The deploy at 13:50 was in the timeline before anybody thought to look for it."}),
   "The events that can be collected automatically. Interleaving them with the conversation is "
   "what makes the connection visible.",
   "Automatic events collected into an incident timeline",
   "A horizontal row of five boxes. Alerts, fired and resolved. Deploys and rollbacks. Restarts "
   "and scaling events. Config changes, with who made them. Interleaved with what people said. A "
   "note says the deploy at thirteen fifty was in the timeline before anybody thought to look for "
   "it."),
  ("p", "The value is in the interleaving. A deploy at ten to two sitting in a deployment log is "
        "information nobody connects; the same deploy appearing twelve minutes before the alert "
        "in a single timeline is the connection making itself."),
  ("h3", "One prompt at resolution"),
  ("p", "When the incident closes, a single prompt to everybody involved: anything the channel "
        "missed? Something you tried privately, a phone call, a thing you noticed and did not "
        "mention. Two minutes, while it is still fresh, and it catches the material that was "
        "never written down."),
  ("p", "Next: what caused it."),
 ],
},
{
 "slug": "why-there-is-rarely-one-root-cause",
 "title": "Why there is rarely one root cause",
 "nav": "On root causes",
 "read": 6, "words": 760,
 "desc": ("The last change is not the cause, contributing conditions, and why a single cause field "
          "produces shallow analysis."),
 "og": ("The deploy triggered it. It became a two-hour incident because of four other things, and "
        "those are the ones worth fixing."),
 "abstract": ("Why a single root cause is usually the trigger rather than the cause, how "
              "contributing conditions are identified, why blame is an analytical failure as well "
              "as a cultural one, and what the write-up should contain."),
 "lede": ("A root cause field on a postmortem template produces a shallow answer every time, "
          "because there is always a last thing that changed and writing it down feels like "
          "completing the analysis."),
 "tags": ["postmortem", "root cause", "blameless", "analysis", "reliability", "serverless"],
 "takeaways": [
  "The trigger is the last thing that changed. The causes are what made it an incident.",
  "Ask what made it possible, what made it worse, and what delayed detection.",
  "No names in the causal chain. A person's action is a system that allowed it.",
  "'Human error' is where analysis stops rather than where it should.",
  "A write-up with one cause and one action is usually incomplete.",
 ],
 "blocks": [
  ("h2", "Trigger against causes"),
  ("fig", ("chain", {
    "entry": {"title": "The deploy at 13:50", "sub": ["the trigger"], "icon": "route"},
    "steps": [
      {"title": "What made it possible?", "sub": ["a config with no validation"], "icon": "search"},
      {"title": "What made it worse?", "sub": ["no gradual rollout"], "icon": "alarm"},
      {"title": "What delayed detection?", "sub": ["the alert pointed elsewhere"], "icon": "clock"},
      {"title": "What delayed recovery?", "sub": ["rollback needed an approval"], "icon": "lock"},
      {"title": "Four conditions", "sub": ["and one trigger"], "icon": "doc"}],
    "note": "Fixing the trigger prevents this incident. Fixing the conditions prevents a class."}),
   "The four questions that replace a root cause field. Each one produces a different and "
   "independently fixable finding.",
   "How contributing conditions are identified rather than a single root cause",
   "A vertical chain of five steps entered by a box labelled The deploy at thirteen fifty, the "
   "trigger. Step one asks what made it possible: a config with no validation. Step two asks what "
   "made it worse: no gradual rollout. Step three asks what delayed detection: the alert pointed "
   "elsewhere. Step four asks what delayed recovery: the rollback needed an approval. Step five "
   "concludes with four conditions and one trigger. A note says fixing the trigger prevents this "
   "incident while fixing the conditions prevents a class."),
  ("h3", "Why the distinction matters"),
  ("p", "The trigger is specific and will not recur in the same form. Somebody will not make that "
        "exact configuration mistake again, and a postmortem whose only action is \"be more "
        "careful with that config\" has prevented one incident."),
  ("p", "The conditions are general. A config path with no validation will admit a different "
        "mistake next time. An alert that points at the wrong component will mislead a different "
        "team. A rollback that needs an approval will be slow in every future incident."),
  ("h2", "The write-up structure"),
  ("callout", "Sections that produce a useful document", [
   "<strong>What happened,</strong> in two sentences, for somebody who was not there.",
   "<strong>Impact:</strong> who was affected, how, and for how long. Specific.",
   "<strong>Timeline,</strong> with the belief column from Part 2.",
   "<strong>Contributing conditions,</strong> plural, each independently stated.",
   "<strong>What went well.</strong> Genuinely, and it is not padding: the things that limited "
   "the damage are worth protecting.",
   "<strong>Actions,</strong> each tied to a condition rather than to the trigger.",
   "<strong>No section called root cause,</strong> because the field creates the answer.",
  ]),
  ("p", "The fifth section is skipped in most templates and it earns its place. An incident that "
        "was detected in four minutes because somebody had built a good alert last year is "
        "telling you something about what to keep doing, and the alert's author will otherwise "
        "never hear about it."),
  ("h2", "Blame is an analytical failure"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "'Human error'", "parts": [("found", 1)]},
      {"label": "Conditions analysis", "parts": [("found", 4)]}],
    "series": [("found", "Independently fixable findings", "#7AA116")],
    "unit": "",
    "note": "Blame is not just unkind. It stops the analysis at the first plausible answer."}),
   "The same incident analysed two ways. Attributing it to a person's mistake yields one finding "
   "and it is not actionable.",
   "Findings produced by blaming human error versus analysing conditions",
   "A bar chart with two bars showing independently fixable findings. Human error: one. "
   "Conditions analysis: four. A note says blame is not just unkind, it stops the analysis at the "
   "first plausible answer."),
  ("p", "The cultural argument for blameless postmortems is well made and there is a second "
        "argument that persuades different people: blame produces worse analysis. \"Somebody "
        "typed the wrong value\" is a complete-sounding explanation that generates one action, "
        "and the action is a reminder."),
  ("p", "\"A production configuration change was possible without validation, review or a gradual "
        "rollout\" describes the same event and generates three actions, none of which depend on "
        "anybody being more careful."),
  ("h3", "No names in the causal chain"),
  ("p", "A practical rule that is easy to apply: names appear in the timeline where they are "
        "needed for clarity, and never in the contributing conditions. Where a person's action is "
        "part of the story, the condition is stated as the system that permitted it."),
  ("p", "This is not a euphemism. It is the more accurate statement, because the same action "
        "taken by anybody else would have had the same effect, which means the action is not what "
        "distinguishes this incident."),
  ("h2", "How deep to go"),
  ("fig", ("strip", {
    "stages": [
      {"title": "One level", "sub": ["the deploy"], "icon": "route"},
      {"title": "Two levels", "sub": ["no validation"], "icon": "search"},
      {"title": "Three levels", "sub": ["why no validation?"], "icon": "question"},
      {"title": "Four levels", "sub": ["a decision in 2023"], "icon": "clock"},
      {"title": "Stop when actionable", "sub": ["not when profound"], "icon": "check"}],
    "title": "HOW FAR TO KEEP ASKING",
    "note": "It is always possible to go one level deeper and reach something nobody can act on."}),
   "How deep an analysis should go. The stopping condition is actionability rather than "
   "philosophical completeness.",
   "How many levels deep to analyse an incident's causes",
   "A horizontal row of five boxes. One level: the deploy. Two levels: no validation. Three "
   "levels: why no validation. Four levels: a decision made in 2023. Stop when actionable, not "
   "when profound. A note says it is always possible to go one level deeper and reach something "
   "nobody can act on."),
  ("p", "There is a failure mode at the other end from blame, which is an analysis that arrives "
        "at organisational culture, resourcing decisions from three years ago, or the general "
        "difficulty of distributed systems. All true, and none of it produces anything anybody "
        "can do on Monday."),
  ("p", "The stopping rule is practical: keep asking until each condition has an action somebody "
        "could actually take, and then stop. If a level produces no actionable finding, the "
        "previous level was the right depth."),
  ("p", "Next: what happens to those actions."),
 ],
},
{
 "slug": "what-happens-to-the-action-items",
 "title": "What happens to the action items",
 "nav": "The action items",
 "read": 5, "words": 730,
 "desc": ("The graveyard of open actions, why declining is a legitimate outcome, and what an "
          "unclosed list does to the process."),
 "og": ("A postmortem process with forty open actions from the last two years has taught "
        "everybody that postmortems do not lead anywhere."),
 "abstract": ("Why postmortem actions go unclosed, why declining is a legitimate and useful "
              "outcome, how many actions is right, and what the open count does to participation."),
 "lede": ("This is the post that decides whether the whole practice survives, because a process "
          "whose outputs visibly go nowhere stops attracting anybody's effort within about a "
          "year."),
 "tags": ["postmortem", "action items", "follow-through", "process", "reliability", "serverless"],
 "takeaways": [
  "Most postmortem actions are never done and never closed.",
  "Declined is a legitimate end state and is better than open forever.",
  "Three actions that get done beat nine that do not.",
  "Every action needs an owner who agreed to it, in the room.",
  "Publish the open count; it is the health metric for the whole practice.",
 ],
 "blocks": [
  ("h2", "The graveyard"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "Year 1", "parts": [("done", 14), ("open", 9)]},
      {"label": "Year 2", "parts": [("done", 11), ("open", 22)]},
      {"label": "Year 3", "parts": [("done", 8), ("open", 41)]}],
    "series": [("done", "Actions completed", "#7AA116"),
               ("open", "Actions still open", "#DD344C")],
    "unit": "",
    "note": "By year three, participation in postmortems has usually collapsed too."}),
   "Three years of postmortem actions in a typical organisation. The growing red column is what "
   "people see, and it is what they conclude the process produces.",
   "Postmortem actions completed and left open over three years",
   "A stacked bar chart with three bars. Two series: actions completed in green, and actions "
   "still open in red. Year one: fourteen completed and nine open. Year two: eleven completed and "
   "twenty-two open. Year three: eight completed and forty-one open. A note says by year three, "
   "participation in postmortems has usually collapsed too."),
  ("p", "The causal link between the two is direct. People spend four hours on a review, three "
        "actions come out of it, none of them happen, and the next time an incident occurs the "
        "review is shorter and less honest because everybody knows what it produces."),
  ("h2", "Declining is legitimate"),
  ("fig", ("chain", {
    "entry": {"title": "An action, 90 days old", "sub": ["not started"], "icon": "clock"},
    "steps": [
      {"title": "Ask the owner", "sub": ["once, plainly"], "icon": "email"},
      {"title": "Still going to do it?", "sub": ["honestly"], "icon": "branch",
       "exit": {"title": "A new date", "sub": ["and that is fine"], "icon": "check",
                "label": "yes"}},
      {"title": "Priorities changed?", "sub": ["usually"], "icon": "branch",
       "exit": {"title": "Close as declined", "sub": ["with the reason"], "icon": "doc",
                "label": "yes"}},
      {"title": "Still important?", "sub": ["but nobody has time"], "icon": "branch",
       "exit": {"title": "Escalate once", "sub": ["a decision, either way"], "icon": "person",
                "label": "yes"}},
      {"title": "Closed, one way or another", "sub": ["nothing stays open"], "icon": "check"}],
    "note": "Declining an action is a decision. Leaving it open is an absence of one."}),
   "How an ageing action is resolved. Every path ends in a closed state, which is what keeps the "
   "open list meaningful.",
   "How an ageing postmortem action item is resolved",
   "A vertical chain of five steps entered by a box labelled An action, ninety days old and not "
   "started. Step one asks the owner, once and plainly. Step two asks whether they are still "
   "going to do it, honestly; a yes exits to A new date, and that is fine. Step three asks "
   "whether priorities changed, which they usually have; if so it exits to Close as declined, "
   "with the reason. Step four asks whether it is still important but nobody has time; if so it "
   "exits to Escalate once, for a decision either way. Step five closes it one way or another, "
   "with nothing staying open. A note says declining an action is a decision and leaving it open "
   "is an absence of one."),
  ("h3", "Why declining is better than open"),
  ("p", "An action declined with a reason is information: we decided this risk was acceptable, on "
        "this date, for this reason. If the incident recurs, that decision is on the record and "
        "can be revisited with evidence."),
  ("p", "The same action left open for three years contains no decision, no information, and no "
        "protection. It is worse in every respect except that nobody had to say no."),
  ("h2", "How many actions"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "9 actions", "parts": [("done", 2), ("not", 7)]},
      {"label": "5 actions", "parts": [("done", 3), ("not", 2)]},
      {"label": "3 actions", "parts": [("done", 3), ("not", 0)]}],
    "series": [("done", "Completed within 90 days", "#7AA116"),
               ("not", "Not completed", "#7D8CA3")],
    "unit": "",
    "note": "Three actions produce more change than nine. This is consistent and unintuitive."}),
   "Completion rates against the number of actions per postmortem. Fewer actions produce more "
   "completed work, not less.",
   "How many postmortem actions get completed at three different list lengths",
   "A stacked bar chart with three bars. Two series: completed within ninety days in green, and "
   "not completed in grey. Nine actions: two completed and seven not. Five actions: three "
   "completed and two not. Three actions: three completed and none outstanding. A note says three "
   "actions produce more change than nine, which is consistent and unintuitive."),
  ("p", "The mechanism is straightforward: a list of nine has no ordering that anybody believes, "
        "so none of them is the next thing to do. A list of three is a list somebody can hold and "
        "act on."),
  ("p", "The discipline is at the end of the review: of these eight things we could do, which "
        "three actually matter? The other five are written into the document as considered and "
        "not chosen, which preserves the thinking without creating an obligation."),
  ("h3", "An owner who agreed"),
  ("p", "An action assigned to somebody who was not in the room is an action that will not "
        "happen, and assigning work to a team rather than a person is the same thing with extra "
        "steps."),
  ("p", "The owner should be present, should say yes, and should give a date they believe. A date "
        "chosen to end the meeting is worse than no date because it produces a false sense of "
        "commitment that expires quietly."),
  ("h2", "The health metric"),
  ("p", "The single number worth publishing is the count of actions open beyond their date. Not "
        "how many postmortems were written, not how many incidents there were, and not the "
        "completion percentage, which can be gamed by writing fewer actions."),
  ("p", "An open-and-overdue count that stays under about five is a practice that works. One that "
        "grows every quarter is telling you, well in advance, that the postmortem process is "
        "about to stop being taken seriously."),
  ("p", "Next: reading them again."),
 ],
},
{
 "slug": "how-old-postmortems-get-read-again",
 "title": "How old postmortems get read again",
 "nav": "Reading them again",
 "read": 5, "words": 720,
 "desc": ("Surfacing an old incident at the moment it is relevant, the near miss nobody writes up, "
          "and the recurring pattern nobody sees."),
 "og": ("A postmortem is worth something when it appears in front of somebody who is about to "
        "repeat it, which does not happen by itself."),
 "abstract": ("How past incidents are surfaced automatically, what makes two incidents similar, "
              "the near miss that never gets written, and the recurrence pattern only visible in "
              "aggregate."),
 "lede": ("This is the last post in this series and it is about the part of postmortem practice "
          "that almost nobody builds, which is a shame because it is where the entire return "
          "sits."),
 "tags": ["postmortem", "search", "learning", "near miss", "patterns", "serverless"],
 "takeaways": [
  "Surface old incidents automatically when a new one starts.",
  "Match on the systems involved and the alert, not on the words in the write-up.",
  "The near miss is the cheapest possible incident to learn from and is rarely recorded.",
  "Count recurrences by contributing condition, not by incident.",
  "An annual read-through of the year's incidents finds things no individual review did.",
 ],
 "blocks": [
  ("h2", "Surfacing at the right moment"),
  ("fig", ("chain", {
    "entry": {"title": "An incident is declared", "sub": ["right now"], "icon": "alarm"},
    "steps": [
      {"title": "Which systems?", "sub": ["from the declaration"], "icon": "route"},
      {"title": "Which alert fired?", "sub": ["the signature"], "icon": "search"},
      {"title": "Any past match?", "sub": ["same systems or alert"], "icon": "branch",
       "exit": {"title": "Nothing to show", "sub": ["stay quiet"], "icon": "check", "label": "no"}},
      {"title": "Post the summaries", "sub": ["into the channel, now"], "icon": "doc"},
      {"title": "Including the actions", "sub": ["especially the declined ones"], "icon": "form"}],
    "note": "The last box is uncomfortable and is frequently the most useful thing on the screen."}),
   "How past incidents reach the people handling a new one. Posting into the channel at "
   "declaration is the only moment anybody will read them.",
   "How relevant past incidents are surfaced during a new one",
   "A vertical chain of five steps entered by a box labelled An incident is declared, right now. "
   "Step one identifies which systems, from the declaration. Step two identifies which alert "
   "fired, the signature. Step three asks whether there is any past match on the same systems or "
   "alert; if not it exits to Nothing to show, stay quiet. Step four posts the summaries into the "
   "channel, now. Step five includes the actions, especially the declined ones. A note says the "
   "last box is uncomfortable and is frequently the most useful thing on the screen."),
  ("h3", "The declined action"),
  ("p", "When an incident recurs and the earlier postmortem contains an action that was declined "
        "as not worth doing, that is exactly the information the current responders need, and it "
        "is precisely what a well-run process would prefer not to display."),
  ("p", "Showing it anyway is what makes the declining decision honest. A risk accepted with a "
        "stated reason is a defensible decision; the same risk accepted and then quietly hidden "
        "when it materialises is not."),
  ("h3", "Matching on structure, not words"),
  ("p", "Full text search over postmortems works badly, because the words describing an incident "
        "are written after the fact and vary enormously. Matching on which systems were involved "
        "and which alert fired is cruder and considerably more effective."),
  ("p", "That requires the declaration to capture the systems, which is one field at the moment an "
        "incident opens. It is the smallest possible ask at the busiest possible time, which is "
        "why it is a picklist and not free text."),
  ("h2", "The near miss"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Nearly an incident", "sub": ["caught in time"], "icon": "alarm"},
      {"title": "Everyone relieved", "sub": ["and moves on"], "icon": "person"},
      {"title": "Nothing written", "sub": ["there was no impact"], "icon": "question"},
      {"title": "Same conditions", "sub": ["as a real one"], "icon": "search"},
      {"title": "And it was free", "sub": ["nobody was affected"], "icon": "check"}],
    "title": "THE CHEAPEST LESSON AVAILABLE",
    "note": "A near miss teaches the same thing as an incident and costs nothing to have had."}),
   "Why near misses are worth writing up. They contain the same contributing conditions as a real "
   "incident with none of the damage.",
   "Why a near miss is worth writing up despite having no impact",
   "A horizontal row of five boxes. Nearly an incident, caught in time. Everyone relieved and "
   "moves on. Nothing written, because there was no impact. Same conditions as a real one. And it "
   "was free, because nobody was affected. A note says a near miss teaches the same thing as an "
   "incident and costs nothing to have had."),
  ("p", "The barrier is that a near miss has no natural trigger for a review: nothing broke, "
        "nobody was paged for long, and writing it up feels like manufacturing work."),
  ("p", "A short form &mdash; what nearly happened, what caught it, what would have happened if it "
        "had not &mdash; is ten minutes and produces most of the value of a full postmortem. "
        "Making it explicitly short is what gets it filled in."),
  ("h2", "Patterns across incidents"),
  ("fig", ("bars", {
    "tiers": [
      {"label": "No gradual rollout", "parts": [("n", 7)]},
      {"label": "Alert pointed wrong", "parts": [("n", 5)]},
      {"label": "Rollback needed approval", "parts": [("n", 4)]},
      {"label": "Config unvalidated", "parts": [("n", 3)]}],
    "series": [("n", "Incidents this condition contributed to, per year", "#ED7100")],
    "unit": "",
    "note": "No single postmortem showed this. It is only visible by counting conditions."}),
   "A year of contributing conditions counted across all incidents. Each individual postmortem "
   "mentioned its condition once; only the aggregate shows which ones recur.",
   "Contributing conditions counted across a year of incidents",
   "A bar chart with four bars showing incidents each condition contributed to per year. No "
   "gradual rollout: seven. Alert pointed at the wrong component: five. Rollback needed an "
   "approval: four. Config unvalidated: three. A note says no single postmortem showed this, and "
   "it is only visible by counting conditions."),
  ("p", "This is the argument for tagging contributing conditions with a controlled vocabulary "
        "rather than leaving them as prose. It is slightly more work per postmortem and it is the "
        "only way this chart exists."),
  ("p", "Seven incidents in a year sharing one condition is a prioritisation argument that no "
        "individual review could have made, and it points at work that would have prevented seven "
        "incidents rather than one."),
  ("h3", "The annual read-through"),
  ("p", "Once a year, somebody reads all of the year's postmortems in one sitting. It takes an "
        "afternoon, it is not enjoyable, and it reliably produces two or three findings that no "
        "individual review contained."),
  ("p", "It is also the only realistic way to notice that the same three sentences appear in six "
        "documents, which is the strongest available signal about where to spend effort."),
  ("h3", "What this system does not do"),
  ("p", "It does not write the postmortem, it does not identify causes, and it does not decide "
        "which actions matter. Those are the parts that require somebody who understands what "
        "happened, and a generated write-up would be plausible, fluent, and would remove the "
        "thinking that is the entire point of the exercise."),
  ("p", "What it does is capture what would otherwise be lost, keep the actions honest, and put "
        "the right old document in front of the right person at the right moment. That is enough."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="incident",
 volumes=[(4, "4 incidents"), (15, "15 incidents"), (60, "60 incidents")],
 read_each=0.0,
 msgs_each=2.5,
 lede=("There is no model in this system and incidents are rare: fifteen a month is a busy "
       "engineering organisation. The messaging is action reminders rather than incident traffic. "
       "Here is where each cent goes."),
 takeaway_extra=("Action chasing dominates the messaging, and it is the part that keeps the "
                 "practice alive."),
 risks=[
  "<strong>Storing every channel message forever.</strong> Keep the raw channel for the write-up "
  "period, then keep only the edited timeline and expire the rest.",
  "<strong>Daily action reminders.</strong> A nudge at thirty and ninety days works; a daily one "
  "gets filtered and then the ninety-day one is filtered too.",
  "<strong>Full text search over write-ups.</strong> Not primarily a cost issue: matching on "
  "systems and alerts is cheaper and works considerably better.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model, deliberately. Messaging is "
                "above two per incident because it covers action reminders over the following "
                "months."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ip",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the timeline capture, and the condition vocabulary."),
 outside=[
  {"title": "The incident channel", "sub": ["messages, timestamped"], "icon": "email"},
  {"title": "Automatic events", "sub": ["alerts, deploys,", "config changes"], "icon": "alarm"},
  {"title": "People", "sub": ["writing, and reading", "two years later"], "icon": "person"}],
 inside=[
  {"title": "Function URL + EventBridge", "sub": ["capture,", "action chasing"], "icon": "gateway"},
  {"title": "Lambda x3", "sub": ["capture, publish, chase"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["incidents, actions"], "icon": "database"}],
 note="us-east-1. One account. Raw channel expires after write-up; the edited timeline does not.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. The incident channel, providing timestamped "
  "messages. Automatic events covering alerts, deploys and config changes. And People, writing now "
  "and reading two years later. Inside the account, three groups. A Function URL for capture and "
  "EventBridge for action chasing. Three Lambda functions named capture, publish and chase. And "
  "two DynamoDB tables named incidents and actions. A note gives the region as us-east-1, one "
  "account, and states that the raw channel expires after write-up while the edited timeline does "
  "not."),
 functions=[
  ["<code>ip-capture</code>", "Function URL, from the channel and event sources",
   "Appends timestamped entries; posts matching past incidents when one is declared",
   "10s / 512&nbsp;MB"],
  ["<code>ip-publish</code>", "API, when the write-up is finalised",
   "Stores the edited timeline and conditions; expires the raw channel; creates the actions",
   "60s / 1024&nbsp;MB"],
  ["<code>ip-chase</code>", "EventBridge, weekly",
   "Nudges owners at 30 and 90 days; escalates once; reports the open-and-overdue count",
   "60s / 512&nbsp;MB"]],
 roles=[
  ["<code>ip-capture-role</code>",
   "<code>dynamodb:PutItem</code>, <code>dynamodb:Query</code>", "Incidents; read for matching"],
  ["<code>ip-publish-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>dynamodb:PutItem</code>", "Both tables"],
  ["<code>ip-chase-role</code>",
   "<code>dynamodb:Query</code>, <code>dynamodb:UpdateItem</code>, <code>ses:SendEmail</code>",
   "Actions; one verified identity"]],
 tables=[
  ("Table: incidents",
   "PK   incident_id       S\n"
   "SK   entry_at          S   one item per timeline entry\n"
   "     kind              S   message | alert | deploy | config | belief\n"
   "     text              S\n"
   "     who               S   in the timeline only, never in conditions\n"
   "     kept              BOOL survives the edit; the rest expires\n"
   "     ttl               N   set on unkept entries at publish time\n\n"
   "Metadata item (SK = '#meta'):\n"
   "     systems           L   picklist at declaration; drives matching\n"
   "     alert_signature   S   drives matching\n"
   "     impact            S   who, how, how long\n"
   "     conditions        L   from a controlled vocabulary\n"
   "     went_well         L\n"
   "     near_miss         BOOL a short form, not a full write-up"),
  ("Table: actions",
   "PK   incident_id       S\n"
   "SK   action_id         S\n"
   "     text              S\n"
   "     condition         S   which contributing condition it addresses\n"
   "     owner             S   a person who was in the room and said yes\n"
   "     due               S   a date they believed\n"
   "     state             S   open | done | declined | escalated\n"
   "     declined_reason   S   required when declined; shown on recurrence\n"
   "     closed_at         S\n\n"
   "There is no path that leaves an action open indefinitely: the chase\n"
   "function moves everything to done, declined or escalated.")],
 inbound=[
  "<strong>The channel is the timeline.</strong> Nobody is asked to log anything during an "
  "incident; messages are captured as they are sent.",
  "<strong>Automatic events are interleaved</strong> with the conversation, so a deploy twelve "
  "minutes before an alert is visible without anybody looking for it.",
  "<strong>Systems are a picklist at declaration</strong>, one field, because it is the basis for "
  "matching and free text does not match.",
  "<strong>Conditions come from a controlled vocabulary</strong>, extensible but curated. It is "
  "the only way the recurrence chart in Part 5 exists."],
 model_notes=[
  "<strong>There is no model in this system, deliberately.</strong> This is the one place in this "
  "series where the absence is a value judgement rather than a cost one.",
  "<strong>The tempting use</strong> is drafting the write-up from the channel. It would produce "
  "a fluent, plausible document and remove the thinking that is the entire purpose.",
  "<strong>A second tempting use</strong> is identifying causes. Naming a cause is the analysis, "
  "and outsourcing it produces a confident answer nobody argued with.",
  "<strong>The narrowest defensible use</strong> is suggesting which past incidents might be "
  "related, alongside the structural matching, with the match reason shown.",
  "<strong>The cost page assumes none</strong>, which is why messaging is the whole variable."],
 gotchas=[
  "Capture the timeline during the incident. It is the one part that cannot be reconstructed, and "
  "hindsight deletes exactly the parts that matter.",
  "Do not put a root cause field on the template. The field creates the answer, and the answer it "
  "creates is the last thing that changed.",
  "Close every action, including as declined with a reason. An open list that grows teaches "
  "everybody that postmortems produce nothing.",
  "Match past incidents on systems and alerts rather than on text. Write-up wording varies too "
  "much for search to work.",
  "Show the declined actions when an incident recurs. It is uncomfortable and it is what makes "
  "declining an honest decision rather than a quiet one."],
))
