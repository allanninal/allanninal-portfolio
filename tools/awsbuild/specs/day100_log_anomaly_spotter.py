"""Day 100 -- 2026-08-02 -- Log anomaly spotter."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "log-anomaly-spotter"
NAME = "Log anomaly spotter"

SPEC = {
 "slug": SLUG, "date": "2026-08-02", "name": NAME,
 "tagline": ("Collapses millions of log lines into a few hundred shapes, then tells you about "
             "the shape that is new or the one that has started happening far more -- rather "
             "than about the error you have been ignoring for two years."),
 "lede": ("A small system that turns log lines into fingerprints, counts each fingerprint per "
          "hour, and reports the ones that are new or that have moved far outside their own "
          "history. It never alerts on a threshold you would have to guess at, and it never "
          "wakes anybody. Seven posts on the same system -- one diagram at a time -- with a "
          "cost breakdown and an engineering reference at the end."),
 "keywords": ["logs", "anomaly detection", "observability", "CloudWatch", "errors", "serverless"],
 "icons": ["log", "search", "alarm"],
 "faq": [
  ("What is a log anomaly spotter?",
   "A small serverless system that reduces log lines to fingerprints -- the same message with "
   "different values collapses to one shape -- counts each shape per hour, and reports shapes "
   "that are new or that have moved far outside their own established pattern."),
  ("How is this different from an error alarm?",
   "An error alarm needs somebody to decide in advance which errors matter and at what rate. "
   "This needs no thresholds: it learns each shape's normal rate from its own history, so a new "
   "error is noticed on its first occurrence and a familiar one is not reported at all."),
  ("Does it page anybody?",
   "No. It produces an hourly digest and a daily summary. Anything that genuinely needs waking "
   "somebody should have a real alarm on a real signal, not a log heuristic."),
  ("What about the errors we already ignore?",
   "They become part of the baseline, which is the point. A stack trace that appears four "
   "hundred times an hour every hour is noise; the system reports it once, when it first "
   "appears, and then never again unless the rate changes."),
  ("What does it cost to run?",
   "A few dollars a month for a small system's logs. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "log-anomaly-spotter-on-aws",
 "title": "A log anomaly spotter on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Collapses log lines into shapes, counts each per hour, and reports the new ones and "
          "the ones that moved. No thresholds to guess. AWS, about $4 a month."),
 "og": ("Millions of lines collapse into a few hundred shapes. A new shape is interesting on its "
        "first occurrence; a familiar one is not interesting at all."),
 "abstract": ("The whole system on one page -- a fingerprinter, a counter and a comparer -- built "
              "so that nobody has to decide in advance which errors matter."),
 "lede": ("Every small system produces more log lines than anybody will read and a handful of "
          "them matter. The usual responses both fail: alarming on the word ERROR produces a "
          "channel full of the same four exceptions you decided months ago were fine, and "
          "alarming on nothing means the genuinely new failure appears at the same volume as "
          "everything else. This post walks through a small system that needs no threshold and "
          "no opinion about which errors are important."),
 "tags": ["logs", "anomaly detection", "observability", "CloudWatch", "errors", "serverless"],
 "takeaways": [
  "Lines become fingerprints: the same message with different values is one shape.",
  "Every shape gets an hourly count, and its own history is its baseline.",
  "Two findings: a shape nobody has seen before, and a shape far outside its own pattern.",
  "Nothing pages. An hourly digest and a daily summary, because logs are not an alarm signal.",
  "Designed on AWS for about $4 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Log groups", "sub": ["your functions and services"], "icon": "log"},
      {"title": "Known shapes", "sub": ["what has been seen"], "icon": "database"},
      {"title": "Whoever is on call", "sub": ["an hourly digest"], "icon": "person"}],
    "inside": [
      {"title": "Fingerprinter", "sub": ["lines to shapes,", "values stripped"], "icon": "filter"},
      {"title": "Counter", "sub": ["per shape,", "per hour"], "icon": "counter"},
      {"title": "Comparer", "sub": ["new, or far outside", "its own history"], "icon": "search"}],
    "edges": [{"from": 0, "to": 0, "label": "subscription filter"},
              {"from": 1, "to": 1, "label": "seen before?"},
              {"from": 2, "to": 2, "label": "a short digest", "up": True}],
    "note": "No thresholds anywhere. Each shape is measured against its own history."}),
   "Three things outside the account, three pieces inside it. The absence of thresholds is the "
   "design: nobody has to predict in advance which errors will matter.",
   "System: log lines fingerprinted, counted and compared to their own history",
   "Three boxes across the top sit outside the AWS account. On the left, Log groups: your "
   "functions and services. In the middle, Known shapes: the record of what has been seen before. "
   "On the right, Whoever is on call: the person who receives an hourly digest. Each connects by "
   "an arrow to the AWS account container below. Lines arrive through a subscription filter. The "
   "known shapes feed in the question of whether something has been seen before. A short digest "
   "goes back out. Inside the AWS account are three components in a row. On the left, the "
   "Fingerprinter, turning lines into shapes with values stripped. In the middle, the Counter, "
   "counting per shape per hour. On the right, the Comparer, looking for shapes that are new or "
   "far outside their own history. A note at the bottom says there are no thresholds anywhere and "
   "each shape is measured against its own history."),
  ("h3", "Shapes, not lines"),
  ("p", "Two log lines that differ only in an order id, a timestamp and a duration are the same "
        "event happening twice. Collapsing them into one shape is what turns a stream of millions "
        "into a set of a few hundred, and a set of a few hundred is small enough to reason about "
        "completely."),
  ("p", "That collapse is the whole idea. Once you have a bounded set of shapes with counts, the "
        "two interesting questions become trivial: which shapes are new, and which shapes are "
        "happening at a rate they have never happened at before. Neither requires anybody to have "
        "predicted anything."),
  ("h3", "What runs each hour (the inside)"),
  ("ul", [
   "<strong>The fingerprinter.</strong> Strips the variable parts of a line &mdash; numbers, "
   "identifiers, timestamps, paths, quoted strings &mdash; and hashes what is left. Part 2 is "
   "about doing that well enough that the same error always produces the same shape.",
   "<strong>The counter.</strong> One count per shape per hour, plus the first example line seen "
   "for that shape in that hour, so a report can show a real line rather than a fingerprint.",
   "<strong>The comparer.</strong> Two questions per shape. Is this shape new? And is this "
   "hour's count far outside what this shape usually does at this hour of the week? Part 4 "
   "covers why the hour of the week matters.",
  ]),
  ("h2", "One shape, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Lines arrive", "sub": ["millions"], "icon": "log"},
      {"title": "Fingerprinted", "sub": ["a few hundred shapes"], "icon": "filter"},
      {"title": "Counted", "sub": ["per shape, per hour"], "icon": "counter"},
      {"title": "Compared", "sub": ["new, or moved"], "icon": "search"},
      {"title": "Digested", "sub": ["a few lines an hour"], "icon": "report"}],
    "title": "ONE HOUR OF LOGS, END TO END",
    "note": "The second step is the whole reduction. Everything after it is arithmetic on hundreds."}),
   "The same system as one line. The reduction from millions to hundreds is what makes the rest "
   "possible; without it every subsequent step is a data engineering problem.",
   "One hour of logs from arrival to digest, in five stages",
   "A horizontal row of five boxes joined by arrows. Lines arrive: millions of them. "
   "Fingerprinted: into a few hundred shapes. Counted: per shape, per hour. Compared: for new "
   "shapes or moved ones. Digested: into a few lines an hour. A note says the second step is the "
   "whole reduction and everything after it is arithmetic on hundreds."),
  ("h2", "In plain words"),
  ("p", "A small system produces about two million log lines a week across a dozen functions. "
        "Fingerprinted, those collapse to about three hundred and forty distinct shapes. Most are "
        "routine: a request completed, a batch processed, a scheduled job started."),
  ("p", "About twenty are errors, and eleven of those have been happening steadily for months "
        "&mdash; a third-party timeout that retries successfully, a validation failure on badly "
        "formatted input, a warning from a library nobody can silence. Under an error-word alarm "
        "those eleven produce four hundred notifications a day and everybody has stopped looking."),
  ("p", "Here they produce nothing, because their rate is exactly what it always is. On Thursday "
        "a new shape appears &mdash; a serialisation error nobody has seen before &mdash; eleven "
        "times in one hour. It is in the digest within the hour with the first real line and the "
        "function it came from, and it is the only thing in the digest, because everything else "
        "is behaving normally. That is the difference between a log alarm and this."),
  ("callout", "Design rules that shaped every decision", [
   "No thresholds. Every shape is measured against its own history rather than a number "
   "somebody guessed.",
   "A new shape is interesting once. After it has been seen and not acted on, it becomes "
   "baseline like everything else.",
   "Never page. Logs are a diagnostic signal, not an alarm signal, and treating them as one "
   "produces a muted channel.",
   "Always show a real line. A fingerprint is not readable; the example line it came from is.",
   "Compare like hours. Three in the morning on a Sunday is not comparable with eleven on a "
   "Tuesday.",
   "Report absence too. A shape that always appears and has stopped is frequently the more "
   "urgent finding.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The reason log alerting fails is that it asks the wrong person at the wrong time. It "
        "asks somebody, in advance, to write down which strings matter and how often is too "
        "often &mdash; a prediction about failures that have not happened yet, made by somebody "
        "who does not yet know what they will look like."),
  ("p", "Measuring each shape against itself removes the prediction entirely. A new failure is "
        "interesting because it is new, not because somebody guessed its wording; and a familiar "
        "one is uninteresting because it is familiar, not because somebody remembered to filter "
        "it out."),
  ("p", "The next four posts walk through each piece: how a line becomes a shape, how a new shape "
        "is handled, how a rate change is judged, and what the digest says. One diagram per post, "
        "a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-log-line-becomes-a-shape",
 "title": "How a log line becomes a shape",
 "nav": "How shapes form",
 "read": 5, "words": 760,
 "desc": ("What gets stripped, what must not be, structured logs versus text, and the two "
          "failure modes of fingerprinting."),
 "og": ("Strip too little and every line is its own shape. Strip too much and two different "
        "errors collapse into one. The line between them is where the work is."),
 "abstract": ("What gets stripped from a line and what must not be, why structured logs make "
              "this nearly free, and the two opposite failure modes of fingerprinting."),
 "lede": ("Fingerprinting is the entire system and it fails in two opposite directions. Strip too "
          "little and every line is unique, so nothing ever has a history. Strip too much and two "
          "genuinely different errors become the same shape, so one of them can never be seen."),
 "tags": ["logs", "fingerprinting", "structured logging", "observability", "parsing", "serverless"],
 "takeaways": [
  "Strip numbers, identifiers, timestamps, paths, quoted values and stack line numbers.",
  "Never strip the exception type, the message text, or the function name.",
  "Structured logs make this nearly free: the fingerprint is the event name plus the level.",
  "Too many shapes means something variable is not being stripped.",
  "Too few means two different errors have collapsed, which is the dangerous direction.",
 ],
 "blocks": [
  ("h2", "What gets stripped"),
  ("pre", "before   Order 84412 failed after 1203ms: timeout contacting\n"
          "         https://api.example.com/v2/rates?zone=EU\n\n"
          "after    Order <N> failed after <N>ms: timeout contacting <URL>\n\n"
          "stripped numbers, identifiers, durations, URLs, quoted strings,\n"
          "         UUIDs, IP addresses, hex blobs, stack line numbers, dates\n\n"
          "kept     every word, the exception type, the function name, the level"),
  ("p", "The rule is that anything which varies between two occurrences of the same event is "
        "stripped and everything that identifies which event it is stays. Written down like that "
        "it is obvious; the difficulty is entirely in the long tail of things that vary and do "
        "not look like numbers."),
  ("h2", "The two failure modes"),
  ("fig", ("chain", {
    "entry": {"title": "A log line", "sub": ["raw"], "icon": "log"},
    "steps": [
      {"title": "Strip the variables", "sub": ["numbers, ids, paths"], "icon": "filter"},
      {"title": "Hash what is left", "sub": ["that is the shape"], "icon": "key"},
      {"title": "Too many shapes?", "sub": ["thousands, mostly seen once"], "icon": "branch",
       "exit": {"title": "Under-stripping", "sub": ["find what varies"], "icon": "search",
                "label": "yes"}},
      {"title": "Two errors, one shape?", "sub": ["harder to notice"], "icon": "branch",
       "exit": {"title": "Over-stripping", "sub": ["the dangerous one"], "icon": "alarm",
                "label": "yes"}},
      {"title": "A few hundred shapes", "sub": ["stable week to week"], "icon": "check"}],
    "note": "Under-stripping is loud and obvious. Over-stripping is silent, which is why it is worse."}),
   "The two ways fingerprinting fails. One produces an unusable pile of one-off shapes and "
   "announces itself; the other quietly makes an error invisible.",
   "The two failure modes of log fingerprinting",
   "A vertical chain of five steps entered by a box labelled A log line, raw. Step one strips the "
   "variables: numbers, identifiers and paths. Step two hashes what is left, which is the shape. "
   "Step three asks whether there are too many shapes, meaning thousands mostly seen once; if so "
   "it exits to Under-stripping and the task is to find what varies. Step four asks whether two "
   "different errors have become one shape, which is harder to notice; if so it exits to "
   "Over-stripping, the dangerous one. Step five is a few hundred shapes, stable week to week. A "
   "note says under-stripping is loud and obvious while over-stripping is silent, which is why it "
   "is worse."),
  ("h3", "Under-stripping announces itself"),
  ("p", "If something variable is not being stripped, the shape count explodes: thousands of "
        "shapes, almost all seen exactly once, and every hour brings hundreds of new ones. The "
        "digest becomes useless immediately and the cause is easy to find by looking at a "
        "handful of the one-off shapes and spotting what they have in common."),
  ("p", "Common culprits are session identifiers that do not look like UUIDs, hostnames with a "
        "generated suffix, and durations formatted as text rather than numbers &mdash; \"took 1.2 "
        "seconds\" survives a numeric strip if the number is spelled differently each time."),
  ("h3", "Over-stripping is silent"),
  ("p", "The worse direction. If the strip is aggressive enough that \"connection refused to the "
        "payment provider\" and \"connection refused to the mail provider\" produce the same "
        "shape, then a brand-new payment outage is indistinguishable from the mail warning that "
        "happens twice a day, and it will never be reported."),
  ("p", "The specific temptation is stripping quoted strings, which is usually right and "
        "occasionally catastrophic because the quoted string is the only thing distinguishing two "
        "errors. The compromise that works is stripping quoted values longer than a threshold and "
        "keeping short ones, since a short quoted string is usually a name and a long one is "
        "usually data."),
  ("h2", "Structured logs make this free"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Text logs", "sub": ["strip and hash"], "icon": "log"},
      {"title": "Fragile", "sub": ["a reworded message", "is a new shape"], "icon": "alarm"},
      {"title": "Structured logs", "sub": ["JSON with an event name"], "icon": "code"},
      {"title": "Fingerprint", "sub": ["event + level + source"], "icon": "key"},
      {"title": "Stable", "sub": ["wording can change freely"], "icon": "check"}],
    "title": "STRUCTURED LOGGING MAKES THIS TRIVIAL",
    "note": "If you control the logging, emit an event name. Everything here becomes a group-by."}),
   "Why structured logging changes this problem entirely. With an explicit event name the "
   "fingerprint stops being a heuristic and becomes a field.",
   "How structured logging simplifies log fingerprinting",
   "A horizontal row of five boxes. Text logs: stripped and hashed. Fragile: a reworded message "
   "becomes a new shape. Structured logs: JSON carrying an event name. Fingerprint: the event "
   "plus the level plus the source. Stable: the wording can change freely. A note says if you "
   "control the logging, emit an event name, and everything here becomes a group-by."),
  ("p", "This is worth acting on where you can. If the logs are yours, adding an "
        "<code>event</code> field with a stable identifier makes the fingerprint a field lookup "
        "rather than a heuristic, and it removes the entire class of problem where somebody "
        "improves an error message and the system reports a new shape."),
  ("p", "In practice most systems are mixed: your own functions log structured events and every "
        "library and runtime they use logs text. So the fingerprinter uses the event name when "
        "there is one and falls back to stripping when there is not, and the fallback is where "
        "all the care goes."),
  ("p", "Next: what happens when a shape is new."),
 ],
},
{
 "slug": "how-a-new-shape-is-handled",
 "title": "How a new shape is handled",
 "nav": "How new shapes work",
 "read": 5, "words": 740,
 "desc": ("Why a first occurrence is worth reporting, the warm-up period that stops the first "
          "week being useless, and what happens after a deploy."),
 "og": ("A shape nobody has ever seen is interesting on its first occurrence, which is the one "
        "thing a threshold-based alarm can never do."),
 "abstract": ("Why a first occurrence is worth reporting at all, the warm-up that stops the first "
              "week being noise, and how a deploy is handled without suppressing real findings."),
 "lede": ("Reporting a brand-new log shape on its first occurrence is the single most valuable "
          "thing this system does, and it is the thing a rate-based alarm structurally cannot do: "
          "one occurrence never exceeds any threshold."),
 "tags": ["logs", "anomaly detection", "deployments", "observability", "errors", "serverless"],
 "takeaways": [
  "A shape never seen before is reported on its first occurrence, at any count.",
  "The first two weeks are a warm-up: everything is new, so nothing is reported.",
  "After a deploy, new shapes are grouped and labelled rather than suppressed.",
  "A new shape stops being new after it has appeared in three separate hours.",
  "A shape that reappears after 60 days of absence is treated as new again.",
 ],
 "blocks": [
  ("h2", "First occurrence"),
  ("fig", ("chain", {
    "entry": {"title": "A shape this hour", "sub": ["with a count"], "icon": "counter"},
    "steps": [
      {"title": "Seen before?", "sub": ["ever"], "icon": "branch",
       "side": {"title": "Known shapes", "sub": ["with first and last seen"], "icon": "database"},
       "exit": {"title": "Known", "sub": ["go to the rate check"], "icon": "check",
                "label": "yes"}},
      {"title": "Still warming up?", "sub": ["first 14 days"], "icon": "branch",
       "exit": {"title": "Record only", "sub": ["everything is new"], "icon": "clock",
                "label": "yes"}},
      {"title": "A deploy in the last hour?", "sub": ["from the deploy feed"], "icon": "branch",
       "exit": {"title": "Group and label", "sub": ["'new since the release'"], "icon": "code",
                "label": "yes"}},
      {"title": "Report it", "sub": ["with a real example line"], "icon": "report"},
      {"title": "Mark as seen", "sub": ["new for three more hours"], "icon": "log"}],
    "note": "Deploys are labelled rather than suppressed. A deploy is when new errors appear."}),
   "How a new shape is handled. The deploy branch is the one worth getting right: grouping is "
   "useful and suppressing is exactly wrong.",
   "How a previously unseen log shape is handled",
   "A vertical chain of five steps entered by a box labelled A shape this hour, with a count. "
   "Step one asks whether it has been seen before, ever, against a known shapes table holding "
   "first and last seen; a known shape exits to the rate check. Step two asks whether the system "
   "is still warming up in its first fourteen days; if so it exits to Record only, because "
   "everything is new. Step three asks whether there was a deploy in the last hour according to "
   "the deploy feed; if so it exits to Group and label as new since the release. Step four "
   "reports it with a real example line. Step five marks it as seen, keeping it new for three "
   "more hours. A note says deploys are labelled rather than suppressed, because a deploy is when "
   "new errors appear."),
  ("h3", "The warm-up"),
  ("p", "On the first day, every shape is new and the digest would contain three hundred and "
        "forty entries. So the first fourteen days record shapes without reporting them, and the "
        "system says clearly that it is warming up and when it will start."),
  ("p", "Fourteen days is chosen to cover the weekly cycle twice, which matters because a "
        "substantial number of shapes only occur on a particular day &mdash; a Sunday batch job, "
        "a Monday morning report, a month-end process that will not appear at all in the first "
        "two weeks and will be reported as new when it does. That last case is worth expecting "
        "rather than being surprised by."),
  ("h3", "Deploys: label, do not suppress"),
  ("p", "The obvious handling is to suppress new shapes for an hour after a deploy, since a "
        "release naturally produces new log messages. It is also precisely backwards: a deploy is "
        "the single most likely moment for a genuinely new error to appear, and suppressing "
        "exactly then removes the system's best opportunity."),
  ("p", "So new shapes after a deploy are grouped under a heading &mdash; \"7 new shapes since "
        "release a3f21c\" &mdash; and reported together. A person scanning that sees six that are "
        "obviously new informational messages and one that is a stack trace, which is a much "
        "better outcome than either suppressing all seven or listing them individually."),
  ("h2", "When a shape stops being new"),
  ("fig", ("strip", {
    "stages": [
      {"title": "First seen", "sub": ["reported"], "icon": "alarm"},
      {"title": "Hour two", "sub": ["still labelled new"], "icon": "clock"},
      {"title": "Hour three", "sub": ["last time as new"], "icon": "retry"},
      {"title": "Now baseline", "sub": ["rate checks apply"], "icon": "counter"},
      {"title": "Absent 60 days", "sub": ["new again if it returns"], "icon": "search"}],
    "title": "THE LIFE OF A SHAPE",
    "note": "Three hours, not three occurrences. A burst in one hour is still one event."}),
   "How a shape transitions from new to baseline. Counting hours rather than occurrences means a "
   "single burst does not exhaust the new window.",
   "The lifecycle of a log shape from new to baseline",
   "A horizontal row of five boxes. First seen: reported. Hour two: still labelled new. Hour "
   "three: the last time it is treated as new. Now baseline: rate checks apply. Absent sixty "
   "days: it becomes new again if it returns. A note says three hours rather than three "
   "occurrences, because a burst in one hour is still one event."),
  ("p", "Counting hours rather than occurrences matters. A new shape that appears four hundred "
        "times in its first hour is one event, and treating it as three occurrences' worth of "
        "novelty would move it to baseline before anybody had seen it in the digest."),
  ("h3", "Reappearance after absence"),
  ("p", "A shape that has not been seen for sixty days and then returns is treated as new again, "
        "which catches a specific and common case: an error that was fixed months ago and has "
        "come back. Under a pure seen-before rule it would be recognised as familiar and never "
        "mentioned, which is the wrong answer for something that was absent for two months."),
  ("p", "Next: how a rate change is judged."),
 ],
},
{
 "slug": "how-a-log-rate-change-is-judged",
 "title": "How a log rate change is judged",
 "nav": "How rate is judged",
 "read": 5, "words": 750,
 "desc": ("Comparing an hour against the same hour of the week, the shapes that are too rare to "
          "judge, and the disappearance that matters more than any spike."),
 "og": ("Three in the morning on a Sunday is not comparable with eleven on a Tuesday. Comparing "
        "like hours is what makes a rate change mean something."),
 "abstract": ("Comparing an hour against the same hour of the week, the shapes too rare to judge "
              "at all, why proportion beats absolute count, and the disappearance that matters "
              "more than any spike."),
 "lede": ("A shape that appears eleven times at three on a Sunday morning and four hundred times "
          "at eleven on a Tuesday is behaving completely normally. Any comparison that ignores "
          "that will report a four-hundred-fold increase every Tuesday morning."),
 "tags": ["logs", "seasonality", "anomaly detection", "rate limiting", "observability",
          "serverless"],
 "takeaways": [
  "Compare an hour against the same hour of the week, across several weeks.",
  "Shapes seen fewer than a handful of times a week are too rare to judge on rate.",
  "Compare proportion of traffic as well as absolute count, because volume moves.",
  "A shape that always appears and has stopped is often the more urgent finding.",
  "One report per shape per day, however many hours it keeps being unusual.",
 ],
 "blocks": [
  ("h2", "Same hour of the week"),
  ("fig", ("chain", {
    "entry": {"title": "This hour's count", "sub": ["one shape"], "icon": "counter"},
    "steps": [
      {"title": "Rare shape?", "sub": ["under 20 a week"], "icon": "branch",
       "exit": {"title": "Only new-shape checks", "sub": ["rate is meaningless"], "icon": "stop",
                "label": "yes"}},
      {"title": "Same hour, last 4 weeks", "sub": ["Tuesday 11am vs Tuesday 11am"],
       "icon": "calendar",
       "side": {"title": "History", "sub": ["per shape, per hour slot"], "icon": "database"}},
      {"title": "Outside that range?", "sub": ["by a multiple"], "icon": "branch",
       "exit": {"title": "Normal", "sub": ["the usual outcome"], "icon": "check", "label": "no"}},
      {"title": "Proportion moved too?", "sub": ["or did all traffic rise?"], "icon": "branch",
       "exit": {"title": "Traffic, not the shape", "sub": ["note it, quietly"], "icon": "chart",
                "label": "no"}},
      {"title": "A real rate change", "sub": ["report once today"], "icon": "alarm"}],
    "note": "The fourth check stops a busy morning being reported as forty separate anomalies."}),
   "How a rate change is judged. The proportion check is what distinguishes a shape behaving "
   "differently from the whole system simply being busier.",
   "How a change in a log shape's rate is judged",
   "A vertical chain of five steps entered by a box labelled This hour's count, for one shape. "
   "Step one asks whether it is a rare shape seen under twenty times a week; if so it exits to "
   "Only new-shape checks, because rate is meaningless. Step two compares against the same hour "
   "over the last four weeks, Tuesday eleven against Tuesday eleven, using history held per shape "
   "per hour slot. Step three asks whether this hour is outside that range by a multiple; if not "
   "it exits to Normal, the usual outcome. Step four asks whether the proportion of total traffic "
   "moved too, or whether all traffic simply rose; if only volume rose it exits to Traffic rather "
   "than the shape, noted quietly. Step five is a real rate change, reported once today. A note "
   "says the fourth check stops a busy morning being reported as forty separate anomalies."),
  ("h3", "Rare shapes cannot be judged on rate"),
  ("p", "A shape that occurs three times one week and eleven the next has tripled, and that means "
        "nothing at all. Small counts move around by large multiples for entirely uninteresting "
        "reasons, and any rate rule applied to them produces constant noise."),
  ("p", "So shapes below a weekly floor are exempt from rate checking entirely. They are still "
        "covered by the new-shape rule, which is the useful check for something that rare: an "
        "error that happens three times a week is interesting the first time it appears and not "
        "particularly interesting thereafter."),
  ("h3", "Proportion, not just count"),
  ("p", "The check that saves the most false reports. On a morning when overall traffic doubles "
        "&mdash; a campaign, a news mention, a batch job &mdash; every shape's count doubles, and "
        "a pure count comparison reports forty simultaneous anomalies."),
  ("p", "Comparing each shape's share of total log volume as well as its absolute count separates "
        "the two: a shape whose count doubled while its share stayed constant is just busier, and "
        "one whose share also moved is genuinely behaving differently. The first gets one quiet "
        "note about traffic; the second gets reported."),
  ("h2", "Disappearance"),
  ("fig", ("strip", {
    "stages": [
      {"title": "'Batch completed'", "sub": ["every night, 400 times"], "icon": "check"},
      {"title": "Tonight", "sub": ["zero"], "icon": "alarm"},
      {"title": "No error logged", "sub": ["nothing failed loudly"], "icon": "search"},
      {"title": "The job did not run", "sub": ["or died silently"], "icon": "stop"},
      {"title": "Reported", "sub": ["as an absence"], "icon": "bell"}],
    "title": "THE SHAPE THAT STOPPED",
    "note": "Absence produces no log line, which is why nothing else will ever tell you."}),
   "The finding that only a system counting shapes can produce. Nothing logs the absence of a log "
   "line, so no error-based alerting will ever surface it.",
   "How a log shape that has stopped appearing is detected",
   "A horizontal row of five boxes. Batch completed: logged every night, four hundred times. "
   "Tonight: zero. No error logged: nothing failed loudly. The job did not run: or died silently. "
   "Reported: as an absence. A note says absence produces no log line, which is why nothing else "
   "will ever tell you."),
  ("p", "This is frequently the most valuable finding the system produces and it is invisible to "
        "every other kind of monitoring. A scheduled job that stops being scheduled, a consumer "
        "that stops consuming, a function that is no longer being invoked because a trigger was "
        "deleted &mdash; none of those produce an error, and all of them produce a shape that "
        "used to appear four hundred times and now appears zero times."),
  ("p", "The rule is deliberately conservative: a shape that has appeared in the same hour slot "
        "in each of the last four weeks, with a count above the rare floor, and appears zero "
        "times this week, is reported as an absence. That is narrow enough to almost never fire "
        "spuriously and it catches the case that matters."),
  ("h3", "Once per shape per day"),
  ("p", "A shape that is genuinely running at ten times its normal rate will be outside its range "
        "for every hour of the incident, and reporting it hourly turns one finding into twelve. "
        "So each shape is reported once a day, with the subsequent hours added to the same entry "
        "as a duration rather than as new findings."),
  ("p", "Next: what the digest says."),
 ],
},
{
 "slug": "how-the-log-digest-reads",
 "title": "How the log digest reads",
 "nav": "How it reads",
 "read": 5, "words": 720,
 "desc": ("An hourly digest that is usually empty, what an entry contains, and the daily summary "
          "that is the only place shape counts appear."),
 "og": ("An hourly digest that is empty most hours, and says so. The example line matters more "
        "than any count in it."),
 "abstract": ("The hourly digest that is usually empty, what a single entry contains, why the "
              "example line matters more than the count, and the daily summary."),
 "lede": ("The digest is short by construction and empty most hours, which is a property worth "
          "protecting. A channel that carries something every hour is a channel where an empty "
          "hour means nothing, and an empty hour is the most common true state of a small "
          "system."),
 "tags": ["logs", "reporting", "observability", "digests", "operations", "serverless"],
 "takeaways": [
  "Most hours the digest is empty and it is not sent at all.",
  "An entry is: the example line, the counts, the function, and why it is here.",
  "The example line is a real line, not a fingerprint, and it is the first thing shown.",
  "Two buttons: expected, and worth looking at. Both are recorded.",
  "The daily summary carries shape counts; the hourly digest never does.",
 ],
 "blocks": [
  ("h2", "An hour with something in it"),
  ("callout", "10:00&ndash;11:00", [
   "<strong>New shape &mdash; 11 occurrences, <code>order-worker</code></strong><br>"
   "<code>Order 84412 failed after 1203ms: serialisation error in line item 3</code><br>"
   "First seen 10:14. Not present in the previous 30 days.",
   "<strong>Rate change &mdash; <code>api</code></strong><br>"
   "<code>Retrying upstream request (attempt 2)</code><br>"
   "412 this hour, usually 20&ndash;40 at this hour on a Tuesday. Share of total logs up from "
   "0.4% to 6%.",
   "<em>Two buttons on each: expected &middot; worth looking at</em>",
  ]),
  ("p", "Two entries and that is the whole message. The example line comes first in each because "
        "it is the thing that lets somebody recognise the problem in a second; the counts and the "
        "history are context underneath it."),
  ("h3", "Why the real line goes first"),
  ("p", "A fingerprint is unreadable and a count is uninterpretable without knowing what is being "
        "counted. \"Shape a3f21c is up 10x\" requires a lookup before it means anything, and a "
        "digest that requires a lookup does not get read on a phone."),
  ("p", "The first real line seen for that shape in that hour costs one extra field to store and "
        "turns the entry into something a person understands immediately, including a person who "
        "has never heard of this system."),
  ("h2", "The empty hours"),
  ("fig", ("chain", {
    "entry": {"title": "The hourly run", "sub": ["every hour"], "icon": "clock"},
    "steps": [
      {"title": "Anything to report?", "icon": "branch",
       "exit": {"title": "Send nothing", "sub": ["most hours"], "icon": "check", "label": "no"}},
      {"title": "Build the entries", "sub": ["example line first"], "icon": "doc"},
      {"title": "More than five?", "sub": ["something is wrong"], "icon": "branch",
       "exit": {"title": "Send a summary", "sub": ["'23 anomalies -- see the daily'"],
                "icon": "alarm", "label": "yes"}},
      {"title": "Send the digest", "sub": ["two or three entries"], "icon": "email"},
      {"title": "Record the answers", "sub": ["expected, or not"], "icon": "log"}],
    "note": "A digest with 23 entries is not a digest. It is its own finding."}),
   "The hourly run and its two unusual paths: sending nothing, which is most hours, and refusing "
   "to send twenty-three entries, which is itself a signal.",
   "How the hourly log digest is assembled and sent",
   "A vertical chain of five steps entered by a box labelled The hourly run, every hour. Step one "
   "asks whether there is anything to report; no exits to Send nothing, which is most hours. Step "
   "two builds the entries with the example line first. Step three asks whether there are more "
   "than five, which means something is wrong; if so it exits to Send a summary saying "
   "twenty-three anomalies and pointing at the daily. Step four sends the digest with two or "
   "three entries. Step five records the answers, expected or not. A note says a digest with "
   "twenty-three entries is not a digest but its own finding."),
  ("h3", "Refusing to send a long digest"),
  ("p", "Twenty-three anomalous shapes in one hour is either a genuine major incident, in which "
        "case somebody already knows, or a problem with the system itself &mdash; a deploy that "
        "changed every log message, a fingerprinting change, a log group that started including "
        "something new."),
  ("p", "In both cases a list of twenty-three entries is the wrong output. So above a threshold "
        "the digest collapses to one line saying how many and pointing at the daily summary, "
        "which is both more readable and more accurate about what is actually being said."),
  ("h2", "The two buttons"),
  ("p", "\"Expected\" and \"worth looking at\", both recorded against the shape. Neither changes "
        "the system's behaviour automatically, and that restraint is deliberate: a shape marked "
        "expected once should not be permanently silenced, because the same shape at a hundred "
        "times the rate next month is a different event."),
  ("p", "What the answers do is accumulate. A shape marked expected on eight separate occasions "
        "is a shape whose rate check is set too tight, and that appears in the monthly review as "
        "a specific suggestion rather than as something somebody has to notice."),
  ("h2", "The daily summary"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Shapes seen", "sub": ["341"], "icon": "counter"},
      {"title": "New today", "sub": ["2"], "icon": "search"},
      {"title": "Rate changes", "sub": ["3"], "icon": "chart"},
      {"title": "Disappeared", "sub": ["1"], "icon": "alarm"},
      {"title": "Marked expected", "sub": ["4 of 6"], "icon": "check"}],
    "title": "THE DAILY SUMMARY",
    "note": "The last number is the tuning signal: four expected out of six is too tight."}),
   "The daily summary in five numbers. The ratio of findings marked expected is what says whether "
   "the thresholds need loosening.",
   "One day of log analysis summarised in five numbers",
   "A horizontal row of five boxes. Shapes seen: three hundred and forty-one. New today: two. "
   "Rate changes: three. Disappeared: one. Marked expected: four of six. A note says the last "
   "number is the tuning signal, and four expected out of six is too tight."),
  ("p", "Four findings out of six marked expected means two thirds of what the system reported "
        "was not worth reporting, and that is a bad ratio that will end with the digest being "
        "ignored. One or two out of six is healthy; the multiplier on the rate check is the knob "
        "that moves it."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="million lines",
 volumes=[(2, "2M lines"), (10, "10M lines"), (50, "50M lines")],
 read_each=0.0,
 msgs_each=30.0,
 extra=[("ingest", "CloudWatch Logs ingestion", "#DD344C", 0.50, 0.0)],
 lede=("The compute here is trivial and the log ingestion is not. Two million lines a week is a "
       "small serverless system with sensible logging; fifty million is one with debug logging "
       "left on. Here is where each cent goes."),
 takeaway_extra=("Log ingestion is the dominant cost and it is charged whether or not anything "
                 "reads the logs. This system makes them worth what you are already paying."),
 risks=[
  "<strong>Debug logging left on in production.</strong> The single largest cost risk here, and "
  "it is not caused by this system &mdash; it multiplies ingestion by ten or more and this "
  "system is what will finally make somebody notice.",
  "<strong>Fingerprinting every line in a Lambda.</strong> At fifty million lines a week, "
  "processing every line individually is real compute. Aggregate in the subscription filter's "
  "batch and fingerprint per batch.",
  "<strong>Log retention left at never.</strong> Storage compounds on top of ingestion, and "
  "logs older than a few weeks have no value to this system at all &mdash; the baselines only "
  "look back four weeks.",
 ],
 per_unit_note=("The ingestion band is what you already pay for having logs at all; it appears "
                "here because it dominates and because this system is frequently the thing that "
                "makes somebody look at it. The processing itself is a few cents."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="la",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the subscription path, and why there is no model in it."),
 outside=[
  {"title": "Log groups", "sub": ["subscription filters"], "icon": "log"},
  {"title": "Deploy feed", "sub": ["for labelling new shapes"], "icon": "code"},
  {"title": "SES outbound", "sub": ["hourly digest, daily"], "icon": "email"}],
 inside=[
  {"title": "Kinesis + EventBridge", "sub": ["log stream,", "hourly rollup"], "icon": "queue"},
  {"title": "Lambda x3", "sub": ["fingerprint, roll up,", "compare"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["shapes, counts"], "icon": "database"}],
 note="us-east-1. One account. No model; fingerprinting is regex and hashing.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Log groups, connected by subscription "
  "filters. The Deploy feed, used for labelling new shapes. And SES outbound, carrying the hourly "
  "digest and daily summary. Inside the account, three groups. Kinesis carrying the log stream "
  "and EventBridge providing an hourly rollup. Three Lambda functions named fingerprint, roll up "
  "and compare. And two DynamoDB tables named shapes and counts. A note gives the region as "
  "us-east-1, one account, and states there is no model, because fingerprinting is regular "
  "expressions and hashing."),
 functions=[
  ["<code>la-fingerprint</code>", "Kinesis, batched",
   "Strips variables, hashes, increments an in-memory tally per batch",
   "60s / 1024&nbsp;MB"],
  ["<code>la-rollup</code>", "EventBridge hourly",
   "Flushes tallies into hourly counts; records first example lines",
   "60s / 1024&nbsp;MB"],
  ["<code>la-compare</code>", "EventBridge hourly + daily",
   "New-shape and rate checks; builds and sends the digests", "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>la-fingerprint-role</code>",
   "<code>kinesis:GetRecords</code>, <code>dynamodb:UpdateItem</code>",
   "The log stream; the counts table"],
  ["<code>la-rollup-role</code>", "<code>dynamodb:UpdateItem</code>/<code>Query</code>",
   "Shapes and counts"],
  ["<code>la-compare-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "Shapes and counts, read; one verified identity"]],
 tables=[
  ("Table: shapes",
   "PK   shape             S   sha256 of the stripped line\n"
   "     example           S   a real line, the most recent one seen\n"
   "     source            S   which log group and function\n"
   "     level             S   ERROR | WARN | INFO\n"
   "     first_seen        S   2026-08-02T10:14:00Z\n"
   "     last_seen         S   2026-08-02T10:59:00Z\n"
   "     new_until         S   first_seen + 3 reporting hours\n"
   "     weekly_count      N   used for the rare-shape floor\n"
   "     marked_expected   N   how many times a person said 'expected'\n\n"
   "`marked_expected` accumulating is the tuning signal: a shape somebody has\n"
   "dismissed eight times has a rate check that is set too tight."),
  ("Table: counts",
   "PK   shape             S   sha256\n"
   "SK   hour              S   2026-08-02T10\n"
   "     count             N   412\n"
   "     share             N   0.06   -- proportion of all lines that hour\n"
   "     ttl               N   epoch, +35 days\n\n"
   "35 days is deliberate: the baseline compares against the same hour slot in\n"
   "the last four weeks, so nothing older than that is ever read. Keeping more\n"
   "would be storage nobody queries.")],
 inbound=[
  "<strong>CloudWatch subscription filters</strong> on each log group feed a single Kinesis "
  "stream. A filter pattern can pre-drop obvious noise before it is billed to this system, but "
  "not before CloudWatch ingestion, which has already been charged.",
  "<strong>Batches, not lines.</strong> The fingerprint function receives a batch of records and "
  "tallies in memory before one write, which is what makes fifty million lines a week affordable.",
  "<strong>The deploy feed</strong> is a timestamped identifier written to a small table, used "
  "only to group new shapes under a release heading.",
  "<strong>No model, no external calls.</strong> The entire pipeline is regex, hashing and "
  "counting, which is also why it can keep up with a Kinesis stream."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Fingerprinting is stripping and hashing, "
  "and the comparisons are arithmetic.",
  "<strong>The tempting use</strong> is asking a model to summarise a new stack trace, and it is "
  "worth resisting: the example line is already the summary, and a paraphrase adds a way to be "
  "misleading about an error.",
  "<strong>A second tempting use</strong> is clustering shapes semantically rather than "
  "structurally, which has the same problem as clustering search queries: the groups shift and "
  "the history stops being comparable.",
  "<strong>If you want one</strong>, use it interactively on a specific new shape rather than in "
  "the pipeline.",
  "<strong>The cost page assumes none</strong>, which is why ingestion dominates it entirely."],
 gotchas=[
  "Watch the shape count. Thousands of shapes mostly seen once means something variable is not "
  "being stripped; too few means two errors have collapsed, which is silent and worse.",
  "Do not suppress new shapes after a deploy. A deploy is exactly when new errors appear; group "
  "and label them instead.",
  "Compare like hours. A shape's Tuesday-morning rate has nothing to do with its Sunday-night "
  "rate, and ignoring that reports an anomaly every week.",
  "Check proportion as well as count, or a busy morning is reported as forty separate anomalies.",
  "Report disappearance. A shape that always appeared and has stopped is often the most urgent "
  "finding, and nothing else in your stack will ever tell you."],
))
