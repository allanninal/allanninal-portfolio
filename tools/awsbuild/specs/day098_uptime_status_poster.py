"""Day 98 -- 2026-07-31 -- Uptime status poster."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "uptime-status-poster"
NAME = "Uptime status poster"

SPEC = {
 "slug": SLUG, "date": "2026-07-31", "name": NAME,
 "tagline": ("Checks the things customers actually use, from more than one place, and publishes "
             "a status page that stays up when your site does not -- because the whole point is "
             "being readable during an outage."),
 "lede": ("A small system that checks the handful of journeys customers depend on, from several "
          "regions, and publishes a status page hosted somewhere entirely separate from the "
          "thing it reports on. It drafts an incident and a person publishes it. Seven posts on "
          "the same system -- one diagram at a time -- with a cost breakdown and an engineering "
          "reference at the end."),
 "keywords": ["uptime", "status page", "monitoring", "incidents", "availability", "serverless"],
 "icons": ["monitor", "browser", "alarm"],
 "faq": [
  ("What is an uptime status poster?",
   "A small serverless system that checks customer-facing journeys from several regions, decides "
   "when something is genuinely down, and publishes a public status page. The page is hosted "
   "independently of the thing it monitors, so it survives the outage it exists to describe."),
  ("Why not just ping the home page?",
   "Because a home page that returns 200 while checkout is broken is the exact failure a status "
   "page needs to catch. Checking the journeys customers use -- log in, search, check out -- is "
   "more work and is the only version that means anything."),
  ("Does it publish automatically?",
   "It publishes the automated check status automatically. It drafts the human-readable incident "
   "and a person publishes that, because the sentence customers read during an outage is a "
   "commercial communication, not a monitoring output."),
  ("Why check from several regions?",
   "Because a single checker cannot tell your outage from its own. Two of three regions "
   "disagreeing with the third is a network problem; three of three agreeing is your problem."),
  ("What does it cost to run?",
   "A couple of dollars a month for a handful of journeys checked every minute. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "uptime-status-poster-on-aws",
 "title": "An uptime status poster on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Checks the journeys customers use from several regions and publishes a status page "
          "hosted independently of your site. AWS, about $3 a month."),
 "og": ("A status page that goes down with your site is worse than no status page. This one is "
        "hosted somewhere entirely separate and checks journeys rather than pings."),
 "abstract": ("The whole system on one page -- multi-region checks, a decider and an "
              "independently hosted page -- built around the one property that matters: it works "
              "when nothing else does."),
 "lede": ("There are two ways a status page fails and most small businesses manage both. It goes "
          "down with the thing it monitors, so during the one hour it exists for it shows "
          "nothing. And it reports that the server is responding while customers cannot check "
          "out, because it pings a home page. This post walks through a small system built to "
          "avoid exactly those two things."),
 "tags": ["uptime", "status page", "monitoring", "incidents", "availability", "serverless"],
 "takeaways": [
  "Check journeys, not hosts. A 200 from the home page says almost nothing.",
  "Check from three regions, and require agreement before calling anything down.",
  "The status page is hosted on infrastructure that shares nothing with your site.",
  "Automated status publishes itself; the human incident note is drafted and published by a person.",
  "Designed on AWS for about $3 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Your journeys", "sub": ["log in, search,", "check out"], "icon": "browser"},
      {"title": "Three regions", "sub": ["checking independently"], "icon": "cdn"},
      {"title": "Customers + you", "sub": ["read the page,", "publish the note"], "icon": "team"}],
    "inside": [
      {"title": "Checkers", "sub": ["one per region,", "every minute"], "icon": "monitor"},
      {"title": "Decider", "sub": ["agreement, then", "consecutive failures"], "icon": "filter"},
      {"title": "Publisher", "sub": ["a static page,", "on separate infrastructure"], "icon": "cloud"}],
    "edges": [{"from": 0, "to": 0, "label": "real requests"},
              {"from": 1, "to": 1, "label": "three opinions"},
              {"from": 2, "to": 2, "label": "status, and a note", "up": True}],
    "note": "Nothing in the publishing path depends on anything the checks are checking."}),
   "Three things outside the account, three pieces inside it. The note at the bottom is the "
   "entire architectural requirement, and it constrains where every piece can live.",
   "System: journeys checked from three regions, status published independently",
   "Three boxes across the top sit outside the AWS account. On the left, Your journeys: log in, "
   "search and check out. In the middle, Three regions checking independently. On the right, "
   "Customers and you: the people who read the page and publish the note. Each connects by an "
   "arrow to the AWS account container below. Real requests flow down into the account. Three "
   "regional opinions feed in. Status and a note go back out. Inside the AWS account are three "
   "components in a row. On the left, the Checkers, one per region running every minute. In the "
   "middle, the Decider, which requires agreement and then consecutive failures. On the right, "
   "the Publisher, which writes a static page on separate infrastructure. A note at the bottom "
   "says nothing in the publishing path depends on anything the checks are checking."),
  ("h3", "The independence requirement"),
  ("p", "A status page that lives on the same server, behind the same load balancer, in the same "
        "region, on the same DNS as your product is not a status page. It is a second copy of "
        "the thing that is broken."),
  ("p", "So the requirement is stated as a rule rather than a preference: the publishing path "
        "shares nothing with the monitored path. Different region. Different bucket. Ideally a "
        "different domain or at minimum a subdomain whose DNS could survive the main zone being "
        "the problem. Part 4 works through what that means concretely and where the honest "
        "compromises are."),
  ("h3", "What runs every minute (the inside)"),
  ("ul", [
   "<strong>The checkers.</strong> One per region, running the journeys as real requests: a "
   "login that authenticates, a search that returns results, a checkout that reaches the payment "
   "step. Part 2 covers what a journey check is and what it must not do.",
   "<strong>The decider.</strong> Takes three regional opinions and decides. Agreement first, "
   "then consecutive failures, then a state change. Part 3 is entirely about not calling an "
   "outage because one region had a bad minute.",
   "<strong>The publisher.</strong> Writes a static page to a bucket in a different region "
   "behind its own distribution. The page is plain HTML with no JavaScript, because a status "
   "page has to render on a phone on a train.",
  ]),
  ("h2", "One incident, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Checked", "sub": ["3 regions, every minute"], "icon": "monitor"},
      {"title": "Two fail", "sub": ["one region still fine"], "icon": "branch"},
      {"title": "All three fail", "sub": ["twice running"], "icon": "alarm"},
      {"title": "Published", "sub": ["status changes itself"], "icon": "cloud"},
      {"title": "Note added", "sub": ["by a person"], "icon": "person"}],
    "title": "ONE INCIDENT, END TO END",
    "note": "Steps two and three are about three minutes apart. That is the deliberate delay."}),
   "The same system as one line. The gap between the first failure and publishing is the price "
   "of not publishing an outage that was a network blip.",
   "One incident from first failed check to published note, in five stages",
   "A horizontal row of five boxes joined by arrows. Checked: three regions, every minute. Two "
   "fail: one region still reports fine. All three fail: twice running. Published: the status "
   "changes itself. Note added: by a person. A note says steps two and three are about three "
   "minutes apart, and that is the deliberate delay."),
  ("h2", "In plain words"),
  ("p", "At 14:06 the checkout journey fails from Ireland and Frankfurt. London still succeeds, "
        "so nothing is published: two out of three is a disagreement, and disagreement usually "
        "means a network problem between a checker and you rather than an outage."),
  ("p", "At 14:07 London fails too. All three agree, but one round of agreement is not enough. "
        "At 14:08 all three fail again, and the status page changes to \"Checkout: degraded\" "
        "automatically. Total elapsed time from the first symptom: two minutes."),
  ("p", "At the same moment a message goes to whoever is on call with a drafted note: "
        "\"Checkout is currently failing. We are looking into it.\" They read it, agree, and tap "
        "publish, and now the status page says something a customer can understand rather than "
        "just a red dot. The whole sequence took four minutes and the customer emailing to ask "
        "whether it is just them has somewhere to look."),
  ("callout", "Design rules that shaped every decision", [
   "The publishing path shares nothing with the monitored path. That constrains everything else.",
   "Check journeys, not hosts. A working home page is not evidence of a working business.",
   "Require agreement across regions. One checker cannot distinguish your outage from its own.",
   "Two consecutive agreeing failures. One is a blip and publishing it is worse than waiting.",
   "The status changes itself; the sentence customers read is published by a person.",
   "The page is static HTML, no JavaScript. It has to render badly on a bad connection.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Uptime monitoring is a solved problem with a dozen good hosted options, and for most "
        "businesses buying one is the right answer. The reason to build a small one is the status "
        "page rather than the monitoring: a hosted checker tells you, and a status page tells "
        "your customers, and the second is the thing that reduces support load during an outage."),
  ("p", "So the design puts almost all of its care into the publishing path being independent and "
        "the page being readable, and treats the checking itself as the straightforward part. "
        "That is the opposite emphasis from most monitoring tools, and it follows directly from "
        "asking what the thing is for."),
  ("p", "The next four posts walk through each piece: what a journey check actually does, how a "
        "check becomes an outage, how the page is served independently, and how an incident gets "
        "closed. One diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-journey-check-works",
 "title": "How a journey check works",
 "nav": "How checks work",
 "read": 5, "words": 760,
 "desc": ("What a journey check does that a ping does not, the four journeys worth checking, and "
          "the rules that stop a check causing damage."),
 "og": ("A journey check logs in, searches and reaches checkout. Which means it needs rules "
        "about what it must never do -- like completing a purchase every minute."),
 "abstract": ("What a journey check does that a ping does not, the four journeys worth checking, "
              "and the rules that stop a monitoring check causing damage of its own."),
 "lede": ("A ping tells you a server answered. A journey check tells you a customer could have "
          "done the thing they came to do. The second is much more useful and much more "
          "dangerous, because it involves actually doing things on your production system every "
          "minute forever."),
 "tags": ["uptime", "synthetic monitoring", "journeys", "testing", "safety", "serverless"],
 "takeaways": [
  "A journey check performs a real sequence and asserts on content, not just status codes.",
  "Four journeys is usually enough: home, search, log in, and reach checkout.",
  "A check account is a real account, marked as one, excluded from analytics and reporting.",
  "The check never completes a purchase, sends a message or writes customer data.",
  "Timing is recorded but a slow journey is not a down journey.",
 ],
 "blocks": [
  ("h2", "What a check asserts"),
  ("pre", "journey     checkout\n"
          "steps       GET  /                  200, contains 'Add to basket'\n"
          "            POST /basket/add        302 or 200\n"
          "            GET  /basket            200, contains the item name\n"
          "            GET  /checkout          200, contains 'Payment'\n"
          "stop        before submitting payment -- always\n"
          "assert      content, not just status\n"
          "timeout     8s per step, 30s total\n"
          "record      per-step timing, every run"),
  ("p", "The content assertions are what make this different from a ping. A checkout page that "
        "returns 200 and renders an error message is broken, and only a content assertion sees "
        "that. Asserting on a specific string is brittle in a useful way: when somebody changes "
        "the wording, the check fails, somebody updates it, and the check stays honest."),
  ("h2", "The four journeys"),
  ("fig", ("chain", {
    "entry": {"title": "Which journeys?", "sub": ["not every page"], "icon": "browser"},
    "steps": [
      {"title": "Home loads", "sub": ["the cheapest signal"], "icon": "check"},
      {"title": "Search returns results", "sub": ["exercises the database"], "icon": "search"},
      {"title": "Login succeeds", "sub": ["exercises auth and session"], "icon": "lock"},
      {"title": "Checkout reaches payment", "sub": ["and stops there"], "icon": "money"},
      {"title": "Four checks, three regions", "sub": ["twelve runs a minute"], "icon": "counter"}],
    "note": "Each journey exercises a different subsystem. That is how four is enough."}),
   "The four journeys and why each one earns its place. Together they cover the web tier, the "
   "database, authentication and the payment integration.",
   "The four customer journeys worth checking",
   "A vertical chain of five steps entered by a box labelled Which journeys, and not every page. "
   "Step one is Home loads, the cheapest signal. Step two is Search returns results, which "
   "exercises the database. Step three is Login succeeds, which exercises authentication and "
   "session handling. Step four is Checkout reaches payment, and stops there. Step five notes "
   "four checks across three regions, giving twelve runs a minute. A note says each journey "
   "exercises a different subsystem, which is how four is enough."),
  ("p", "The value is in the coverage rather than the count. Home loading proves the web tier and "
        "the CDN. Search proves the database is answering. Login proves authentication and "
        "sessions. Checkout proves the payment integration is reachable. A failure in any one of "
        "them points at a different part of the system, which is most of the diagnostic value."),
  ("h2", "Rules that stop a check causing damage"),
  ("callout", "What a check must never do", [
   "<strong>Never complete a purchase.</strong> It stops at the payment step. A check that "
   "completes an order every minute creates 1,440 orders a day and a genuinely awkward "
   "conversation with accounts.",
   "<strong>Never send a message.</strong> No password resets, no contact form submissions, no "
   "SMS. Every one of those reaches a real system with a real cost.",
   "<strong>Never write customer data.</strong> The check account's basket is emptied at the "
   "start of each run rather than the end, so a failed run does not leave state behind.",
   "<strong>Never be counted.</strong> The check account is flagged, its user agent is "
   "identifiable, and analytics, revenue reporting and recommendation systems all exclude it.",
   "<strong>Never hold a lock.</strong> If the checkout reserves stock, the check uses an item "
   "with a stock level that is deliberately enormous.",
  ]),
  ("p", "The analytics exclusion is the one most often forgotten and it distorts more than people "
        "expect. Twelve runs a minute is seventeen thousand sessions a day, and a small "
        "business's traffic figures, conversion rate and most-viewed-product report are all "
        "meaningfully wrong if those are included."),
  ("h2", "Slow is not down"),
  ("fig", ("strip", {
    "stages": [
      {"title": "800ms", "sub": ["normal"], "icon": "clock"},
      {"title": "3s", "sub": ["slow, recorded"], "icon": "counter"},
      {"title": "8s", "sub": ["step timeout: failed"], "icon": "alarm"},
      {"title": "Degraded", "sub": ["a separate state"], "icon": "branch"},
      {"title": "Down", "sub": ["only when it fails"], "icon": "stop"}],
    "title": "SLOW AND DOWN ARE DIFFERENT STATES",
    "note": "A status page with only up and down cannot describe the most common bad afternoon."}),
   "Why timing produces its own state. Most bad afternoons are not outages, and a page that can "
   "only say up or down has to lie about them in one direction.",
   "How response time maps to status states",
   "A horizontal row of five boxes. Eight hundred milliseconds: normal. Three seconds: slow, and "
   "recorded. Eight seconds: the step timeout, so the check has failed. Degraded: a separate "
   "state. Down: only when a check actually fails. A note says a status page with only up and "
   "down cannot describe the most common bad afternoon."),
  ("p", "A journey that succeeds in three seconds when it usually takes eight hundred milliseconds "
        "is not down and is not fine. That state is <code>degraded</code>, it appears on the "
        "status page in its own colour, and it is reported separately &mdash; because \"the site "
        "is slow\" is the most common customer complaint and a status page that says everything "
        "is operational during it is actively unhelpful."),
  ("p", "Next: how three regional opinions become one decision."),
 ],
},
{
 "slug": "how-a-check-becomes-an-outage",
 "title": "How a check becomes an outage",
 "nav": "How it decides",
 "read": 5, "words": 750,
 "desc": ("Three regions, what agreement means, why two consecutive rounds and not one, and the "
          "case where the checkers are the problem."),
 "og": ("One checker cannot distinguish your outage from its own. Three can, and the rule for "
        "combining them is where most false alarms come from."),
 "abstract": ("What agreement across three regions means, why two consecutive rounds rather than "
              "one, how partial failure is expressed, and the case where the checkers themselves "
              "are the problem."),
 "lede": ("A single checker reporting a failure has told you one of two things and cannot say "
          "which: either your site is down, or the path between that checker and your site is. "
          "Those need completely different responses and telling them apart is what the third "
          "region is for."),
 "tags": ["uptime", "consensus", "false positives", "monitoring", "incidents", "serverless"],
 "takeaways": [
  "Three regions, and a journey is down only when all three agree.",
  "Two of three is a network finding, recorded and not published.",
  "Two consecutive agreeing rounds before a state change. One round is a blip.",
  "Recovery needs only one agreeing round, because being wrong about up is cheaper.",
  "If all journeys fail from all regions at once, suspect the checkers before the site.",
 ],
 "blocks": [
  ("h2", "Agreement"),
  ("fig", ("chain", {
    "entry": {"title": "Three results", "sub": ["one journey, one minute"], "icon": "monitor"},
    "steps": [
      {"title": "All three fail?", "icon": "branch",
       "exit": {"title": "One or two fail", "sub": ["record as a network finding"],
                "icon": "log", "label": "partial"}},
      {"title": "Also last round?", "sub": ["two consecutive"], "icon": "branch",
       "exit": {"title": "Hold", "sub": ["one round is a blip"], "icon": "clock", "label": "no"}},
      {"title": "All journeys, all regions?", "sub": ["everything at once"], "icon": "branch",
       "exit": {"title": "Suspect the checkers", "sub": ["alarm differently"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Change the status", "sub": ["published automatically"], "icon": "cloud"},
      {"title": "Draft the note", "sub": ["for a person to publish"], "icon": "person"}],
    "note": "The third branch is the one people leave out and then get woken by at 3am."}),
   "How three results become one decision. The everything-at-once branch is the check on the "
   "checkers, and it is what stops a monitoring failure being reported as a total outage.",
   "How three regional check results become an outage decision",
   "A vertical chain of five steps entered by a box labelled Three results, for one journey in "
   "one minute. Step one asks whether all three failed; one or two failing exits to record it as "
   "a network finding. Step two asks whether they also failed last round, requiring two "
   "consecutive; if not it exits to Hold, because one round is a blip. Step three asks whether "
   "all journeys are failing from all regions at once; if so it exits to Suspect the checkers "
   "and alarms differently. Step four changes the status, published automatically. Step five "
   "drafts the note for a person to publish. A note says the third branch is the one people "
   "leave out and then get woken by at three in the morning."),
  ("h3", "Two of three is information"),
  ("p", "A journey that fails from two regions and succeeds from a third is almost never your "
        "site being down. It is usually a network path problem, occasionally a CDN edge having a "
        "bad time, and once in a while a genuine regional problem in your own infrastructure."),
  ("p", "None of those is a status page event and all of them are worth recording. So a partial "
        "failure is written to the history with which regions disagreed, and a pattern of the "
        "same region disagreeing repeatedly is raised weekly &mdash; because that is either a "
        "checker with a problem or a real geographic issue, and both are worth knowing without "
        "either being an outage."),
  ("h3", "Two rounds down, one round up"),
  ("p", "The asymmetry is deliberate. Publishing an outage that was not one costs credibility and "
        "generates support contacts, so it is worth a minute of delay to be sure. Publishing a "
        "recovery that turns out to be premature costs very little &mdash; the status goes back "
        "down a minute later and the incident note explains it."),
  ("p", "So going down needs two consecutive agreeing rounds and coming back up needs one. In "
        "practice that means an outage is published about two minutes after it starts and marked "
        "resolved about one minute after it ends, which is the right way round."),
  ("h2", "When the checkers are the problem"),
  ("fig", ("strip", {
    "stages": [
      {"title": "All 4 journeys", "sub": ["failing"], "icon": "alarm"},
      {"title": "All 3 regions", "sub": ["at the same minute"], "icon": "cdn"},
      {"title": "Suspicious", "sub": ["real outages are messier"], "icon": "search"},
      {"title": "Check the checker", "sub": ["credentials, quota, deploy"], "icon": "code"},
      {"title": "Different alarm", "sub": ["'monitoring may be broken'"], "icon": "bell"}],
    "title": "TOTAL FAILURE IS USUALLY YOUR MONITORING",
    "note": "Genuine total outages exist. They are rarer than expired check credentials."}),
   "The pattern that suggests the monitoring rather than the site. Simultaneous total failure "
   "across every journey and every region is a shape real outages rarely have.",
   "Why simultaneous total failure suggests a monitoring problem",
   "A horizontal row of five boxes. All four journeys: failing. All three regions: at the same "
   "minute. Suspicious: real outages are messier. Check the checker: credentials, quota, a "
   "deploy. Different alarm: saying monitoring may be broken. A note says genuine total outages "
   "exist but are rarer than expired check credentials."),
  ("p", "The most common causes are mundane: the check account's password expired, an API key "
        "rotated, a deploy changed the string the assertion looks for, or the checkers were "
        "themselves deployed with a bug. Every one of those looks exactly like a total outage and "
        "none of them is."),
  ("p", "So that pattern raises a distinct alarm with different wording &mdash; \"all checks "
        "failing from all regions; this may be a monitoring problem\" &mdash; and it does not "
        "automatically publish a total outage to the status page. A person confirms before "
        "telling every customer the business is down."),
  ("p", "Next: how the page is served independently."),
 ],
},
{
 "slug": "how-the-status-page-stays-up",
 "title": "How the status page stays up",
 "nav": "How it stays up",
 "read": 5, "words": 740,
 "desc": ("Sharing nothing with the monitored system, the DNS problem nobody solves properly, "
          "and why the page is plain HTML with no JavaScript."),
 "og": ("A status page on the same DNS, region and account as your product is a second copy of "
        "the broken thing. Independence is a rule, and it has one honest compromise in it."),
 "abstract": ("What sharing nothing actually means, the DNS dependency nobody fully escapes, why "
              "the page is plain HTML, and how it degrades when even the publisher fails."),
 "lede": ("This is the post that justifies building rather than buying. Every hosted status page "
          "gets independence right by construction; a homegrown one gets it right only if "
          "somebody thought about it, and it is easy to build one that shares four separate "
          "dependencies with the thing it monitors."),
 "tags": ["status page", "resilience", "CloudFront", "DNS", "static hosting", "serverless"],
 "takeaways": [
  "Different region, different bucket, different distribution, different account if you can.",
  "DNS is the dependency you cannot fully escape, and the mitigation is a second name.",
  "Plain HTML, no JavaScript, no fonts, no analytics. It has to render on a bad connection.",
  "The page is written on every state change and on a heartbeat, so staleness is visible.",
  "If publishing fails, the last page stays up and says when it was written.",
 ],
 "blocks": [
  ("h2", "What independence means"),
  ("table", ["Dependency", "The mistake", "The fix"], [
   ["Region", "Same region as the app", "A different region, chosen deliberately"],
   ["Account", "Same AWS account", "A second account, if you have one"],
   ["Distribution", "Same CloudFront as the site", "Its own distribution and bucket"],
   ["DNS", "Same hosted zone as the app", "A separate zone, ideally a separate registrar"],
   ["Build path", "Deployed by the same pipeline", "Written by a Lambda, not a deploy"],
   ["The page itself", "Renders by calling an API", "Static HTML with the status baked in"],
  ]),
  ("p", "The last row is the one that most often goes wrong in a homegrown status page. A page "
        "that loads and then fetches the current status from an API is only as available as that "
        "API, which is frequently the thing that is down. The status has to be in the HTML, "
        "written at the moment it changed."),
  ("h2", "The DNS problem"),
  ("fig", ("chain", {
    "entry": {"title": "A customer types", "sub": ["status.example.com"], "icon": "browser"},
    "steps": [
      {"title": "Resolve the name", "sub": ["needs DNS to work"], "icon": "dns",
       "exit": {"title": "Your zone is the problem", "sub": ["nothing resolves"], "icon": "alarm",
                "label": "zone down"}},
      {"title": "Reach the distribution", "sub": ["separate from the app"], "icon": "cdn"},
      {"title": "Fetch static HTML", "sub": ["no API, no JavaScript"], "icon": "doc"},
      {"title": "Render", "sub": ["on a bad connection"], "icon": "phone"},
      {"title": "A working status page", "sub": ["during an outage"], "icon": "check"}],
    "note": "The first exit is the honest compromise: a shared zone is a shared fate."}),
   "The path a customer takes to your status page during an outage, and the one dependency that "
   "cannot be fully removed without a second domain.",
   "How a customer reaches the status page during an outage",
   "A vertical chain of five steps entered by a box labelled A customer types "
   "status.example.com. Step one resolves the name, which needs DNS to work; if your zone is the "
   "problem it exits to an alarm where nothing resolves. Step two reaches the distribution, which "
   "is separate from the application. Step three fetches static HTML with no API and no "
   "JavaScript. Step four renders on a bad connection. Step five is a working status page during "
   "an outage. A note says the first exit is the honest compromise, because a shared zone is a "
   "shared fate."),
  ("h3", "The honest compromise"),
  ("p", "If your status page is a subdomain of your main domain and the main zone has a problem, "
        "the status page is unreachable. That is a real dependency and the full fix is a second "
        "domain at a second registrar, which most small businesses will reasonably decide is more "
        "than they want to maintain."),
  ("p", "The middle position is worth knowing: a separate hosted zone for the status subdomain, "
        "delegated from the main zone. It does not survive the parent zone being deleted or the "
        "registrar suspending the domain, and it does survive the far more common case of "
        "somebody breaking a record in the main zone. That is most of the benefit for a "
        "twenty-minute setup."),
  ("h3", "Why no JavaScript"),
  ("p", "Because the people reading a status page during an outage are disproportionately on "
        "phones, on poor connections, in a hurry. A page that is fourteen kilobytes of HTML and "
        "inline CSS renders instantly on anything; the same page with a framework, a font and an "
        "analytics tag does not, and the failure is invisible to whoever built it on a desk "
        "connection."),
  ("h2", "When publishing itself fails"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Status changes", "sub": ["page written"], "icon": "cloud"},
      {"title": "Heartbeat write", "sub": ["every 5 minutes"], "icon": "clock"},
      {"title": "Publisher fails", "sub": ["page stops updating"], "icon": "alarm"},
      {"title": "Page says when", "sub": ["'as of 14:02'"], "icon": "doc"},
      {"title": "A reader can tell", "sub": ["stale, not wrong"], "icon": "check"}],
    "title": "A STALE PAGE THAT ADMITS IT",
    "note": "A page saying 'all operational' with no timestamp is the worst possible failure."}),
   "How the page fails safely. The timestamp is what turns a stale page from a lie into a "
   "readable signal.",
   "How the status page behaves when publishing fails",
   "A horizontal row of five boxes. Status changes: the page is written. Heartbeat write: every "
   "five minutes. Publisher fails: the page stops updating. Page says when: showing as of "
   "fourteen oh two. A reader can tell: it is stale rather than wrong. A note says a page saying "
   "all operational with no timestamp is the worst possible failure."),
  ("p", "Writing the page on a heartbeat as well as on state change is what makes the timestamp "
        "meaningful. A page that only rewrites when something changes will legitimately show a "
        "timestamp from three days ago, which is indistinguishable from a broken publisher."),
  ("p", "With a five-minute heartbeat, a timestamp more than about ten minutes old means the "
        "publisher has stopped, and a reader who notices that has learned something true. It is a "
        "small piece of honesty that costs one scheduled invocation."),
  ("p", "Next: the incident note, and closing it."),
 ],
},
{
 "slug": "how-an-incident-gets-closed",
 "title": "How an incident gets closed",
 "nav": "How it closes",
 "read": 5, "words": 730,
 "desc": ("The note a person writes, the updates during an outage, what a resolution says, and "
          "the monthly numbers that are actually worth publishing."),
 "og": ("The automated status is a colour. The sentence customers read is a commercial "
        "communication and belongs to a person."),
 "abstract": ("The drafted note a person publishes, the update cadence during an outage, what a "
              "resolution has to say, and the monthly figures worth putting on the page."),
 "lede": ("The automated part of this system produces a colour. Everything customers actually "
          "value about a status page is the sentence next to it, and that sentence is a "
          "commercial communication written under pressure &mdash; which is exactly why it is "
          "drafted in advance and published by a person."),
 "tags": ["status page", "incidents", "communication", "reporting", "operations", "serverless"],
 "takeaways": [
  "The status changes automatically; the note is drafted and published by a person.",
  "Three drafts exist in advance, so nobody writes prose during an incident.",
  "Updates on a fixed cadence even when there is nothing new, because silence reads as worse.",
  "A resolution says what was affected, for how long, and whether anything needs redoing.",
  "Publish uptime monthly per journey. A single site-wide figure hides the checkout outage.",
 ],
 "blocks": [
  ("h2", "Drafts written in advance"),
  ("p", "Nobody writes well at 14:08 with a broken checkout and a phone ringing. So the three "
        "notes that cover almost every incident are written calmly in advance, stored, and "
        "presented for one-tap publication with the affected journey filled in."),
  ("callout", "The three drafts", [
   "<strong>Investigating.</strong> \"We are aware that {journey} is not working correctly and "
   "are investigating. We will update this page within 30 minutes.\"",
   "<strong>Identified.</strong> \"We have identified the cause of the problem with {journey} "
   "and are working on a fix. We will update this page within 30 minutes.\"",
   "<strong>Resolved.</strong> \"{journey} is working normally again. The problem lasted from "
   "{start} to {end}. {impact}\"",
   "<strong>Nothing else is templated.</strong> Anything more specific is written in the moment, "
   "because a specific claim made from a template is how a status page says something wrong.",
  ]),
  ("p", "The thirty-minute promise in the first two is load-bearing and it is a commitment the "
        "system then enforces: a reminder fires at twenty-five minutes so that the promise is "
        "kept even when the incident is absorbing everybody."),
  ("h2", "Updating when there is nothing to say"),
  ("fig", ("chain", {
    "entry": {"title": "An open incident", "sub": ["published"], "icon": "alarm"},
    "steps": [
      {"title": "25 minutes elapsed", "sub": ["since the last update"], "icon": "clock"},
      {"title": "Anything new?", "icon": "branch",
       "exit": {"title": "Post it", "sub": ["specific, written now"], "icon": "chat",
                "label": "yes"}},
      {"title": "Post anyway", "sub": ["'still working on it'"], "icon": "bell"},
      {"title": "Repeat every 30", "sub": ["until resolved"], "icon": "retry"},
      {"title": "Resolved", "sub": ["with the impact"], "icon": "check"}],
    "note": "Silence during an outage reads as worse than the outage. An empty update is not empty."}),
   "The update cadence during an open incident. Posting nothing new is still worth posting, "
   "because the alternative is read as nobody being on it.",
   "How updates are posted during an open incident",
   "A vertical chain of five steps entered by a box labelled An open incident, published. Step "
   "one waits twenty-five minutes since the last update. Step two asks whether there is anything "
   "new; if so it exits to Post it, specific and written in the moment. Step three posts anyway, "
   "saying still working on it. Step four repeats every thirty minutes until resolved. Step five "
   "is Resolved, with the impact stated. A note says silence during an outage reads as worse than "
   "the outage, and an empty update is not empty."),
  ("h3", "The resolution note"),
  ("p", "The one that matters commercially, and it has to answer three questions a customer "
        "actually has: what was affected, for how long, and is there anything they need to do."),
  ("p", "The third is the one most status pages omit and the one that generates support contacts. "
        "\"Orders placed between 14:06 and 14:31 may not have gone through; please check your "
        "order history or contact us\" prevents a hundred emails. \"The issue has been resolved\" "
        "generates them."),
  ("h2", "Monthly numbers"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Home", "sub": ["100%"], "icon": "check"},
      {"title": "Search", "sub": ["99.98%"], "icon": "search"},
      {"title": "Login", "sub": ["99.99%"], "icon": "lock"},
      {"title": "Checkout", "sub": ["99.41%"], "icon": "money"},
      {"title": "Site-wide", "sub": ["would say 99.85%"], "icon": "alarm"}],
    "title": "PER-JOURNEY UPTIME, NOT ONE NUMBER",
    "note": "The single site-wide figure hides the only outage that cost anybody money."}),
   "Why uptime is published per journey. A blended figure averages the journey that matters "
   "against three that were fine, and reports a good month.",
   "Monthly uptime published per journey rather than as one figure",
   "A horizontal row of five boxes. Home: one hundred per cent. Search: ninety-nine point nine "
   "eight per cent. Login: ninety-nine point nine nine per cent. Checkout: ninety-nine point four "
   "one per cent. Site-wide: would say ninety-nine point eight five per cent. A note says the "
   "single site-wide figure hides the only outage that cost anybody money."),
  ("p", "Publishing four numbers instead of one is slightly more embarrassing and much more "
        "honest. The checkout figure is the one a customer cares about, and averaging it against "
        "three journeys that were fine produces a headline that is technically true and "
        "practically misleading."),
  ("h3", "What not to publish"),
  ("p", "Response times, error rates and internal component status all belong on an internal "
        "dashboard rather than a public page. A status page has one audience with one question: "
        "can I do the thing I came to do. Adding graphs invites a reader to interpret data they "
        "have no context for, and during an incident that produces speculation rather than "
        "patience."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="check",
 volumes=[(500000, "4 journeys, 3 regions"), (1000000, "8 journeys, 3 regions"),
          (2000000, "8 journeys, 6 regions")],
 read_each=0.0,
 msgs_each=0.00002,
 lede=("Checking four journeys from three regions every minute is about five hundred thousand "
       "invocations a month, which sounds enormous and costs very little because each one is "
       "short. Here is where each cent goes."),
 takeaway_extra=("Half a million short invocations a month is a few dollars. Frequency is cheap; "
                 "journey count is what costs."),
 risks=[
  "<strong>Checking every thirty seconds.</strong> Doubles the bill for a detection improvement "
  "smaller than the two-round confirmation delay already imposes. A minute is the right "
  "interval.",
  "<strong>Full page loads instead of HTTP requests.</strong> A headless browser per check is "
  "the page speed watcher's cost profile applied to something running every minute, which is a "
  "hundred times the bill for no additional signal.",
  "<strong>Log retention left at never.</strong> Half a million invocations a month with default "
  "logging is by far the largest line on this bill within weeks.",
 ],
 per_unit_note=("Each check is an HTTP sequence rather than a browser load, which is what keeps "
                "this affordable at a one-minute interval. There is no model anywhere in the "
                "system."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="up",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the multi-region layout, and the independence rules that constrain all of it."),
 outside=[
  {"title": "Your journeys", "sub": ["real HTTP sequences"], "icon": "browser"},
  {"title": "Status readers", "sub": ["customers, during an outage"], "icon": "team"},
  {"title": "SNS + SES", "sub": ["on-call, and drafts"], "icon": "email"}],
 inside=[
  {"title": "3 regions", "sub": ["EventBridge + Lambda,", "one stack each"], "icon": "cdn"},
  {"title": "Decider + publisher", "sub": ["in a fourth region"], "icon": "lambda"},
  {"title": "S3 + CloudFront", "sub": ["separate bucket,", "separate distribution"], "icon": "cloud"}],
 note="Four regions. The publishing path shares no region, bucket or zone with the monitored app.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Your journeys, exercised as real HTTP "
  "sequences. Status readers, meaning customers during an outage. And SNS with SES, carrying "
  "on-call alerts and drafted notes. Inside the account, three groups. Three regions, each "
  "running an EventBridge rule and a Lambda in its own stack. A decider and publisher in a "
  "fourth region. And S3 with CloudFront, using a separate bucket and a separate distribution. A "
  "note says four regions in total, and that the publishing path shares no region, bucket or "
  "hosted zone with the monitored application."),
 functions=[
  ["<code>up-check</code> (x3)", "EventBridge, 1 minute, per region",
   "Runs every journey as an HTTP sequence; writes one result row",
   "30s / 512&nbsp;MB, one per region"],
  ["<code>up-decide</code>", "EventBridge, 1 minute, fourth region",
   "Reads the three regions, applies agreement and consecutive rules",
   "15s / 512&nbsp;MB"],
  ["<code>up-publish</code>", "SQS state-change queue + EventBridge 5 min",
   "Renders static HTML to the status bucket; the heartbeat write",
   "15s / 512&nbsp;MB"]],
 roles=[
  ["<code>up-check-role</code>",
   "<code>dynamodb:PutItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "The results table; the check-account credential only"],
  ["<code>up-decide-role</code>",
   "<code>dynamodb:Query</code>/<code>UpdateItem</code>, <code>sns:Publish</code>",
   "Results and state; the on-call topic"],
  ["<code>up-publish-role</code>", "<code>s3:PutObject</code>, <code>dynamodb:GetItem</code>",
   "The status bucket only; the state table, read"]],
 tables=[
  ("Table: results",
   "PK   journey_region    S   checkout#eu-west-1\n"
   "SK   checked_at        S   2026-07-31T14:06:00Z\n"
   "     ok                BOOL false\n"
   "     failed_step       S   GET /checkout\n"
   "     status_code       N   503\n"
   "     assertion_failed  S   expected 'Payment'\n"
   "     ms_total          N   8021\n"
   "     ms_by_step        L   per-step timings\n"
   "     ttl               N   epoch, +90 days\n\n"
   "The results table is regional-write, central-read. Each region writes only\n"
   "its own rows, which means a region losing DynamoDB access degrades the\n"
   "quorum to two rather than breaking the decider."),
  ("Table: state",
   "PK   journey           S   checkout\n"
   "     status            S   operational | degraded | down\n"
   "     since             S   2026-07-31T14:08:00Z\n"
   "     consecutive_fail  N   2\n"
   "     incident_id       S   inc_2026_07_31_a1\n"
   "     note_published    S   the text a person published\n"
   "     last_update_at    S   drives the 30-minute promise\n"
   "     monthly_uptime    M   {2026-07: 99.41}\n\n"
   "`last_update_at` is what fires the 25-minute reminder. The promise made in\n"
   "the first note is enforced by the system rather than by somebody's memory.")],
 inbound=[
  "<strong>Three regional stacks</strong>, identical, deployed separately. Each has its own "
  "EventBridge rule so a regional control-plane problem takes out one opinion rather than all "
  "three.",
  "<strong>The decider runs in a fourth region</strong>, so it does not share a fate with any "
  "single checker.",
  "<strong>The status bucket and distribution</strong> are in a different region again, with "
  "their own origin access control, and are written only by <code>up-publish</code>.",
  "<strong>The status subdomain has its own hosted zone</strong>, delegated from the main zone. "
  "It survives a broken record in the parent and not a deleted parent, and that limitation is "
  "worth stating rather than glossing."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Agreement, consecutive counting and uptime "
  "arithmetic are all mechanical.",
  "<strong>The incident notes are templates</strong> written in advance by a person, because "
  "prose written under pressure by anything is where status pages say something wrong.",
  "<strong>Generating an incident note</strong> is the obvious use and the worst idea in the "
  "series: a plausible sentence about the cause of an outage, published to customers, before "
  "anybody knows the cause.",
  "<strong>The three drafts cover almost everything</strong>, and anything more specific is "
  "written by a person in the moment.",
  "<strong>The cost page assumes none</strong>, which is why there is no read band."],
 gotchas=[
  "Bake the status into the HTML. A page that fetches its status from an API is only as available "
  "as that API, which is frequently the thing that is down.",
  "Write on a heartbeat as well as on change, and show the timestamp. A stale page that admits it "
  "is honest; one that silently says all operational is the worst failure available.",
  "Exclude the check account from analytics. Twelve runs a minute is seventeen thousand sessions "
  "a day and it will quietly ruin your conversion rate.",
  "Stop checkout before payment. A check that completes an order every minute creates 1,440 "
  "orders a day.",
  "Alarm differently when everything fails at once. It is usually an expired check credential, "
  "and publishing a total outage to every customer because of one is an expensive mistake."],
))
