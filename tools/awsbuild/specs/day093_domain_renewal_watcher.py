"""Day 93 -- 2026-07-26 -- Domain renewal watcher."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "domain-renewal-watcher"
NAME = "Domain renewal watcher"

SPEC = {
 "slug": SLUG, "date": "2026-07-26", "name": NAME,
 "tagline": ("Every domain the business owns, who it is registered to, when it expires and "
             "which card pays for it -- checked weekly, so nothing lapses because a card "
             "expired."),
 "lede": ("A small system that keeps a register of every domain the business relies on, checks "
          "each one's real expiry from the registry rather than from an invoice, and escalates "
          "well before the date. It cannot renew anything, and the interesting part is the "
          "domains you forgot you had. Seven posts on the same system -- one diagram at a time "
          "-- with a cost breakdown and an engineering reference at the end."),
 "keywords": ["domains", "DNS", "renewals", "expiry", "infrastructure", "serverless"],
 "icons": ["dns", "calendar", "alarm"],
 "faq": [
  ("What is a domain renewal watcher?",
   "A small serverless system that holds a register of the domains a business depends on, "
   "checks each one's expiry against the registry itself rather than trusting a registrar "
   "email, and escalates in good time. It never renews anything -- that requires a payment "
   "credential it deliberately does not have."),
  ("Why not rely on registrar reminders?",
   "Because they go to whatever address was used when the domain was bought, which is "
   "frequently a person who has left or an inbox nobody reads. The most common cause of a "
   "lapsed domain is not that nobody was told; it is that the telling went somewhere dead."),
  ("Why check the registry rather than the registrar?",
   "Because the registrar's dashboard tells you what they believe, and the registry is what is "
   "actually true. Those differ when a renewal payment failed, when a transfer is in progress, "
   "or when a registrar's own records are stale."),
  ("What about the domains nobody remembers?",
   "That is the most valuable output. The register starts from the domains you know and grows "
   "from three discovery paths -- certificates, DNS records and card charges -- and the ones it "
   "finds are usually the ones nobody would have renewed."),
  ("What does it cost to run?",
   "Under a dollar a month. It checks a handful of domains weekly. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "domain-renewal-watcher-on-aws",
 "title": "A domain renewal watcher on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 870,
 "desc": ("Holds a register of every domain, checks the real expiry from the registry weekly, "
          "and escalates in good time. AWS, about $1 a month."),
 "og": ("The registrar tells you what it believes; the registry tells you what is true. This "
        "checks the second one and escalates to somebody who still works here."),
 "abstract": ("The whole system on one page -- a register, a registry check and an escalation -- "
              "plus the observation that a lapsed domain is almost always a routing failure "
              "rather than a knowledge failure."),
 "lede": ("A domain lapsing is one of the very few failures in a small business that takes the "
          "whole thing off the internet at once: the site, the email, the logins that use that "
          "email to reset. It happens to somebody every week, and almost never because nobody "
          "knew. It happens because the reminder went to a person who left in 2023, or the card "
          "on file expired, or the domain was registered by an agency who stopped invoicing. "
          "This post walks through a small system built around that."),
 "tags": ["domains", "DNS", "renewals", "infrastructure", "resilience", "serverless"],
 "takeaways": [
  "The expiry comes from the registry, not from a registrar email or dashboard.",
  "A domain register is a short list and almost nobody has one.",
  "Three discovery paths find the domains you forgot: certificates, DNS, and card charges.",
  "Escalation goes to people who currently work here, not to whoever bought the domain.",
  "Designed on AWS for about $1 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "The registries", "sub": ["RDAP, the truth"], "icon": "dns"},
      {"title": "Domain register", "sub": ["what you own, who owns it"], "icon": "doc"},
      {"title": "Whoever pays", "sub": ["and their manager"], "icon": "team"}],
    "inside": [
      {"title": "Checker", "sub": ["weekly, per domain,", "against the registry"], "icon": "search"},
      {"title": "Discovery", "sub": ["finds domains not", "on your list"], "icon": "filter"},
      {"title": "Escalator", "sub": ["90, 30, 7 days,", "then loudly"], "icon": "alarm"}],
    "edges": [{"from": 0, "to": 0, "label": "real expiry dates"},
              {"from": 1, "to": 1, "label": "what to check"},
              {"from": 2, "to": 2, "label": "renew this, by when", "up": True}],
    "note": "It cannot renew anything. That needs a payment credential it deliberately lacks."}),
   "Three things outside the account, three pieces inside it. Discovery sits in the middle "
   "because the domains that lapse are disproportionately the ones that were never on anybody's "
   "list.",
   "System: registries checked against a register, escalation out",
   "Three boxes across the top sit outside the AWS account. On the left, The registries: queried "
   "over RDAP, which is the authoritative source. In the middle, Domain register: what you own "
   "and who owns it internally. On the right, Whoever pays, and their manager. Each connects by "
   "an arrow to the AWS account container below. Real expiry dates flow down into the account. "
   "The register feeds in what to check. Renewal escalations go back out. Inside the AWS account "
   "are three components in a row. On the left, the Checker, which runs weekly per domain "
   "against the registry. In the middle, Discovery, which finds domains that are not on your "
   "list. On the right, the Escalator, which acts at ninety, thirty and seven days and then "
   "loudly. A note at the bottom says it cannot renew anything, because that needs a payment "
   "credential it deliberately lacks."),
  ("h3", "Why the registry rather than the registrar"),
  ("p", "A registrar's dashboard shows what the registrar believes about your domain. The "
        "registry &mdash; the organisation that actually runs the top-level domain &mdash; shows "
        "what is true. Those two agree almost all of the time, and the times they disagree are "
        "exactly the times you need to know."),
  ("p", "A renewal that was taken from an expired card shows as renewed in the registrar's "
        "billing view and unchanged at the registry. A transfer in progress can show a date at "
        "one and a different date at the other. A registrar that has been acquired frequently "
        "has stale records for months. Querying the registry directly, over RDAP, costs nothing "
        "and removes the whole class."),
  ("h3", "What runs weekly (the inside)"),
  ("ul", [
   "<strong>The checker.</strong> Queries the registry for each registered domain and records "
   "the expiry, the registrar, the nameservers and the status codes. Part 2 covers RDAP and what "
   "to do about the registries that do not offer it.",
   "<strong>Discovery.</strong> Looks for domains you depend on that are not in the register. "
   "Three sources, covered in Part 3, and between them they typically find two or three domains "
   "per business that nobody had written down.",
   "<strong>The escalator.</strong> Ninety days, thirty days, seven days, and then daily. It "
   "escalates to people from your staff list rather than to whatever address is on the "
   "registration, which is the single most important thing it does.",
  ]),
  ("h2", "One domain, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Registered", "sub": ["in your list"], "icon": "doc"},
      {"title": "Checked", "sub": ["weekly, at the registry"], "icon": "search"},
      {"title": "T-90", "sub": ["a quiet note"], "icon": "calendar"},
      {"title": "T-30", "sub": ["and their manager"], "icon": "bell"},
      {"title": "T-7", "sub": ["daily until it moves"], "icon": "alarm"}],
    "title": "ONE DOMAIN, END TO END",
    "note": "Ninety days is not early. Transfers and payment problems both take weeks."}),
   "The same system as one line. Starting at ninety days sounds excessive until a renewal fails "
   "and the fix turns out to involve a registrar support queue.",
   "One domain from register to renewal escalation, in five stages",
   "A horizontal row of five boxes joined by arrows. Registered: it is in your list. Checked: "
   "weekly, at the registry. T minus ninety: a quiet note. T minus thirty: the owner and their "
   "manager. T minus seven: daily until it moves. A note says ninety days is not early, because "
   "transfers and payment problems both take weeks."),
  ("h2", "In plain words"),
  ("p", "A business has eleven domains. Three are obvious: the main one, the .co.uk that "
        "redirects, and one for a product. Four more are found by discovery: two that were bought "
        "for campaigns years ago and still have MX records pointing at the mail provider, one "
        "that an agency registered and never transferred, and one that a former employee bought "
        "on a personal card and expensed."),
  ("p", "That last one is the interesting case. It is the domain used for a customer-facing "
        "portal. It was registered to a personal email that no longer exists, paid for with a "
        "card that was cancelled when the person left, and expires in five months. Every "
        "registrar reminder it will ever send is going to a dead address. Discovery finds it "
        "because it appears in a certificate transparency log for a hostname the business uses; "
        "the checker gets its real expiry from the registry; and at ninety days somebody who "
        "still works there is told, with enough time to transfer it rather than to argue about "
        "it during a redemption period."),
  ("callout", "Design rules that shaped every decision", [
   "Check the registry, not the registrar. One tells you the truth and the other tells you what "
   "it believes.",
   "Escalate to your staff list. The address on a registration is the least reliable place to "
   "send a warning.",
   "Ninety days is the first notice. Transfers, payment fixes and registrar support all take "
   "weeks.",
   "It cannot renew. A system that can spend money on a card needs a security posture this does "
   "not have.",
   "Discovery is a first-class feature. The domains that lapse are the ones nobody listed.",
   "Watch the status codes, not just the date. A domain can be locked, on hold or pending "
   "deletion well before it expires.",
  ]),
  ("h2", "Why this shape"),
  ("p", "The reason this is worth building rather than putting eleven dates in a calendar is that "
        "the dates are not the problem. The problem is that domains accumulate at the edges of a "
        "business &mdash; bought by agencies, by former staff, for campaigns &mdash; and the ones "
        "at the edges are both the least visible and the most likely to have a broken payment "
        "path attached."),
  ("p", "So the system spends about half its effort on discovery and about half on making sure "
        "the warning reaches somebody who exists. The actual date check is a weekly HTTP request "
        "per domain, and it is the least interesting part."),
  ("p", "The next four posts walk through each piece: how a registry lookup works, how domains "
        "get discovered, what the status codes mean, and how the escalation runs. One diagram "
        "per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-registry-lookup-works",
 "title": "How a registry lookup works",
 "nav": "How lookups work",
 "read": 5, "words": 760,
 "desc": ("RDAP rather than WHOIS, what a lookup actually returns, and what to do about the "
          "registries that still do not offer it."),
 "og": ("RDAP returns structured JSON where WHOIS returns free text that differs per registry. "
        "The fallback for the registries that lack it is honest rather than clever."),
 "abstract": ("Why RDAP rather than WHOIS, what a lookup returns, how the bootstrap works, and "
              "what to do about the registries that still do not offer it."),
 "lede": ("Looking up a domain's expiry date sounds like a solved problem and was, for about "
          "twenty years, a genuinely miserable one. RDAP fixed most of it, and this post is "
          "about using it properly and being honest about the parts it does not cover."),
 "tags": ["domains", "RDAP", "WHOIS", "DNS", "infrastructure", "serverless"],
 "takeaways": [
  "RDAP returns structured JSON. WHOIS returns free text that differs per registry.",
  "The bootstrap file maps a TLD to its RDAP server, and it is cached rather than fetched.",
  "A lookup returns the expiry, the registrar, the nameservers and the status codes.",
  "Some ccTLDs have no RDAP. Those are tracked from the invoice date and flagged as such.",
  "A failed lookup three weeks running is an alarm, not a gap in a chart.",
 ],
 "blocks": [
  ("h2", "What a lookup returns"),
  ("pre", "domain          example.com\n"
          "expiry          2027-03-14T09:00:00Z    the field everything depends on\n"
          "registrar       the sponsoring registrar, by name and IANA id\n"
          "nameservers     [ns1..., ns2...]        a change here is its own signal\n"
          "status          [clientTransferProhibited, ...]\n"
          "created         2011-06-02\n"
          "last_changed    2026-03-14              usually the last renewal\n"
          "source          rdap | invoice          how confident we are"),
  ("p", "The <code>source</code> field is the honest one. A date from RDAP is authoritative; a "
        "date carried over from an invoice because the registry offers no RDAP is a best "
        "estimate, and the register should say which it is holding rather than presenting both "
        "as facts."),
  ("h2", "The lookup"),
  ("fig", ("chain", {
    "entry": {"title": "A domain", "sub": ["from the register"], "icon": "dns"},
    "steps": [
      {"title": "Which RDAP server?", "sub": ["from the bootstrap"], "icon": "search",
       "side": {"title": "Bootstrap", "sub": ["TLD to server,", "cached weekly"], "icon": "database"},
       "exit": {"title": "No RDAP for this TLD", "sub": ["fall back to invoice"], "icon": "alarm",
                "label": "missing"}},
      {"title": "Query it", "sub": ["one HTTPS request"], "icon": "external",
       "exit": {"title": "Failed", "sub": ["retry; alarm at 3 weeks"], "icon": "retry",
                "label": "error"}},
      {"title": "Read the fields", "sub": ["expiry, status, ns"], "icon": "filter"},
      {"title": "Anything changed?", "sub": ["vs last week"], "icon": "branch",
       "exit": {"title": "Report the change", "sub": ["ns and status matter"], "icon": "bell",
                "label": "yes"}},
      {"title": "Store the snapshot", "sub": ["and the date"], "icon": "log"}],
    "note": "A repeated lookup failure is a finding. Registries do not usually go quiet for weeks."}),
   "One domain's weekly check. The change detection is worth as much as the expiry itself: "
   "nameservers changing without anybody expecting it is a much more urgent signal than a date "
   "six months out.",
   "How a domain is checked against its registry",
   "A vertical chain of five steps entered by a box labelled A domain, from the register. Step "
   "one asks which RDAP server, taken from the bootstrap file mapping top-level domains to "
   "servers and cached weekly; a missing entry exits to No RDAP for this TLD, falling back to "
   "the invoice date. Step two queries it with one HTTPS request; an error exits to Failed, "
   "which retries and alarms after three weeks. Step three reads the fields: expiry, status and "
   "nameservers. Step four asks whether anything changed against last week, and a change exits "
   "to Report the change, noting that nameservers and status matter. Step five stores the "
   "snapshot and the date. A note says a repeated lookup failure is a finding, because "
   "registries do not usually go quiet for weeks."),
  ("h3", "The bootstrap"),
  ("p", "IANA publishes a JSON file mapping every top-level domain to its RDAP service. Fetching "
        "it once a week and caching it is the whole of service discovery, and it removes the "
        "need for any per-registry configuration. A TLD that is not in the bootstrap has no RDAP "
        "service, which is information rather than an error."),
  ("h3", "The registries without RDAP"),
  ("p", "A shrinking number of country-code registries still offer only WHOIS, or only a web "
        "form, or nothing machine-readable at all. Parsing free-text WHOIS per registry is a "
        "maintenance burden out of all proportion to two domains, so the honest handling is to "
        "not try."),
  ("p", "Those domains carry a date taken from the renewal invoice, marked <code>source: "
        "invoice</code>, and the escalation for them starts earlier &mdash; a hundred and twenty "
        "days rather than ninety &mdash; because the date is less reliable and there is no "
        "independent way to confirm it. The register says so on the domain, so nobody mistakes a "
        "remembered date for a verified one."),
  ("h2", "Failure is a signal"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Week 1 fails", "sub": ["retry, say nothing"], "icon": "retry"},
      {"title": "Week 2 fails", "sub": ["still quiet"], "icon": "clock"},
      {"title": "Week 3 fails", "sub": ["alarm"], "icon": "alarm"},
      {"title": "Why it matters", "sub": ["a watcher that is not", "watching says nothing"],
       "icon": "search"},
      {"title": "Heartbeat", "sub": ["separate, per domain"], "icon": "check"}],
    "title": "A LOOKUP THAT KEEPS FAILING",
    "note": "The same failure mode as the tax rate watcher: silence looks exactly like all-clear."}),
   "Why repeated lookup failures alarm. This is the same trap as any watcher: the dangerous "
   "state is not an error, it is quiet.",
   "How repeated domain lookup failures are escalated",
   "A horizontal row of five boxes. Week one fails: retry and say nothing. Week two fails: still "
   "quiet. Week three fails: alarm. Why it matters: a watcher that is not watching says nothing. "
   "Heartbeat: separate, and per domain. A note says this is the same failure mode as the tax "
   "rate watcher, because silence looks exactly like all-clear."),
  ("p", "Three consecutive failures on one domain is worth a message, and a domain whose "
        "<code>last_checked</code> has not moved in three weeks is worth an alarm from a "
        "different function &mdash; because if the checker itself has stopped running, it will "
        "not be the thing that tells you."),
  ("p", "Next: how domains get discovered."),
 ],
},
{
 "slug": "how-forgotten-domains-get-discovered",
 "title": "How forgotten domains get discovered",
 "nav": "How discovery works",
 "read": 5, "words": 770,
 "desc": ("Three ways to find domains nobody wrote down -- certificate logs, your own DNS, and "
          "card charges -- and what to do with the ones you find."),
 "og": ("The domains that lapse are the ones nobody listed. Certificate transparency, your own "
        "DNS and the card statement between them find almost all of them."),
 "abstract": ("Three ways to find domains nobody wrote down -- certificate transparency logs, "
              "your own DNS zones, and card charges -- and what to do with each one found."),
 "lede": ("The domains that lapse are almost never the main one. They are the campaign domain "
          "from 2021 that still has an MX record, the one an agency bought, the one a former "
          "employee expensed. This post is about finding them before a renewal date does."),
 "tags": ["domains", "discovery", "certificate transparency", "DNS", "shadow IT", "serverless"],
 "takeaways": [
  "Three sources: certificate transparency, your own DNS, and card charges.",
  "Certificate logs are public and find any domain that has ever had a public certificate.",
  "Your own zones find domains you are pointing at things without owning the record of.",
  "Card charges find the registrar relationships nobody documented.",
  "A discovered domain is a question, never an automatic addition.",
 ],
 "blocks": [
  ("h2", "Three sources"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "Certificate logs", "sub": ["public, searchable"], "icon": "shield",
       "label": "public"},
      {"title": "Your own DNS", "sub": ["zones and records"], "icon": "dns", "label": "internal"},
      {"title": "Card charges", "sub": ["registrar names"], "icon": "money", "label": "billing"}],
    "target": {"title": "Candidate domains", "sub": ["not in the register"],
               "icon": "search",
               "then": {"title": "Ask a person", "sub": ["ours, or not?"], "icon": "person"}},
    "note": "None of these adds a domain automatically. A candidate is a question."}),
   "The three discovery sources. Each finds a different kind of forgotten domain, and between "
   "them they cover most of how domains go missing from a register.",
   "Three discovery sources converging on candidate domains",
   "Three boxes stacked on the left. Certificate logs, which are public and searchable, labelled "
   "public. Your own DNS zones and records, labelled internal. And Card charges showing "
   "registrar names, labelled billing. All three converge on Candidate domains not in the "
   "register. Below that, connected by a downward arrow, is Ask a person: is this ours or not? A "
   "note says none of these adds a domain automatically and a candidate is a question."),
  ("h3", "Certificate transparency"),
  ("p", "Every publicly trusted certificate issued since about 2018 is logged in a public, "
        "append-only, searchable set of logs. That means any hostname the business has ever put "
        "a certificate on is discoverable, by anybody, including you."),
  ("p", "Searching those logs for your organisation name and for known domains turns up "
        "subdomains and sibling domains routinely. It is particularly good at finding the "
        "agency-registered ones, because an agency that set up a site also set up a certificate, "
        "and the certificate is public whether or not the domain is on your list."),
  ("p", "It is worth being clear-eyed about the other side of that: the same search works for "
        "anybody, which is a reason to know what is in there rather than a reason not to look."),
  ("h3", "Your own DNS"),
  ("p", "The second source is inside your own infrastructure. A hosted zone for a domain you do "
        "not have in the register is a domain you are actively serving and not tracking. So is a "
        "CNAME in a zone you do control pointing at a hostname on a domain you do not."),
  ("p", "This one finds a specific and dangerous category: domains that other things depend on. A "
        "redirect that has been in place for four years, a mail routing record, an SPF include. "
        "Those lapse quietly and take something with them."),
  ("h3", "Card charges"),
  ("p", "If the subscription audit bot from Day 80 is running, it already knows about every "
        "recurring charge, and registrar charges are among the easiest to recognise. A charge to "
        "a registrar for an amount that looks like a domain renewal, with no corresponding "
        "domain in the register, is a strong candidate."),
  ("p", "It is also the only source that finds domains with no public presence at all &mdash; one "
        "bought defensively, one held for a project that never launched &mdash; which the other "
        "two sources cannot see by construction."),
  ("h2", "What happens to a candidate"),
  ("fig", ("chain", {
    "entry": {"title": "A candidate domain", "sub": ["found, not registered"], "icon": "search"},
    "steps": [
      {"title": "Look it up", "sub": ["registry, before asking"], "icon": "dns",
       "side": {"title": "RDAP", "sub": ["registrar, expiry"], "icon": "external"}},
      {"title": "Does anything depend on it?", "sub": ["MX, redirect, cert"], "icon": "branch",
       "exit": {"title": "Flag as load-bearing", "sub": ["ask urgently"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Ask a person", "sub": ["with what it points at"], "icon": "person",
       "exit": {"title": "Not ours", "sub": ["record, never ask again"], "icon": "stop",
                "label": "no"}},
      {"title": "Add to the register", "sub": ["with an internal owner"], "icon": "check"},
      {"title": "Now it is watched", "sub": ["like everything else"], "icon": "calendar"}],
    "note": "'Not ours' is recorded, so the same candidate is not raised every week forever."}),
   "What happens to a discovered domain. Looking it up before asking means the question carries "
   "the expiry and the registrar, which is usually enough for somebody to recognise it "
   "immediately.",
   "How a discovered candidate domain is confirmed or dismissed",
   "A vertical chain of five steps entered by a box labelled A candidate domain, found but not "
   "registered. Step one looks it up at the registry over RDAP before asking anybody, collecting "
   "the registrar and expiry. Step two asks whether anything depends on it, checking for MX "
   "records, redirects and certificates; if so it exits to Flag as load-bearing and asks "
   "urgently. Step three asks a person, showing what it points at; a negative exits to Not ours, "
   "which is recorded so it is never raised again. Step four adds it to the register with an "
   "internal owner. Step five is Now it is watched, like everything else. A note says not ours is "
   "recorded so the same candidate is not raised every week forever."),
  ("h3", "Why ask rather than add"),
  ("p", "Because discovery produces false positives with certainty. A certificate log search on "
        "your organisation name will find domains belonging to businesses with similar names, a "
        "customer's subdomain that you host, and a domain a partner set up that genuinely is not "
        "yours to renew."),
  ("p", "Adding those automatically produces a register with things in it that nobody can act "
        "on, and a register that people learn to ignore. So a candidate is a question with the "
        "evidence attached &mdash; \"found in a certificate issued for shop.example.net, "
        "registered at Registrar X, expires March, MX points at your mail provider\" &mdash; "
        "which is usually enough for somebody to answer in five seconds."),
  ("p", "Next: the status codes, which frequently matter more than the date."),
 ],
},
{
 "slug": "how-domain-status-codes-are-read",
 "title": "How domain status codes are read",
 "nav": "How status is read",
 "read": 5, "words": 750,
 "desc": ("The codes that mean trouble long before an expiry date, the ones that mean safety, "
          "and the nameserver change that is the loudest signal of all."),
 "og": ("A domain can be in redemption, pending delete, or on client hold with an expiry date "
        "months away. The status codes carry that and the date does not."),
 "abstract": ("The status codes that mean trouble long before an expiry date, the ones that mean "
              "the domain is protected, and why an unexpected nameserver change matters more "
              "than either."),
 "lede": ("An expiry date is a scheduled event and everything else the registry tells you is "
          "news. A domain can be suspended, in a redemption period, or pending deletion with an "
          "expiry date that is still months away, and a watcher that only reads the date will "
          "report all of those as fine."),
 "tags": ["domains", "EPP status codes", "DNS", "incident detection", "security", "serverless"],
 "takeaways": [
  "Status codes carry situations the expiry date cannot express.",
  "Three families: protective locks, registrar actions, and the deletion lifecycle.",
  "Missing protective locks on an important domain is a finding in itself.",
  "An unexpected nameserver change is the loudest signal the registry can give you.",
  "Every change is reported; only some changes are alarming.",
 ],
 "blocks": [
  ("h2", "Three families of code"),
  ("table", ["Family", "Examples", "What it means"], [
   ["Protective", "clientTransferProhibited, clientUpdateProhibited",
    "The domain is locked against transfer or change. You want these."],
   ["Registrar action", "clientHold, serverHold",
    "The registrar or registry has stopped resolving it. Usually payment or abuse."],
   ["Lifecycle", "redemptionPeriod, pendingDelete",
    "It has already expired and is on a clock. Days matter now, not months."],
  ]),
  ("p", "The lifecycle family is the one that catches people. A domain that expired last month is "
        "not gone &mdash; it goes through a redemption period during which it can usually be "
        "recovered for a fee, and then a pending-delete window after which it is released. A "
        "watcher that reports on expiry dates and stops reporting once a domain expires has gone "
        "quiet at precisely the point where a few days matter."),
  ("h2", "What each change triggers"),
  ("fig", ("chain", {
    "entry": {"title": "This week's status", "sub": ["from the registry"], "icon": "dns"},
    "steps": [
      {"title": "Changed from last week?", "icon": "branch",
       "exit": {"title": "Nothing to say", "sub": ["the usual outcome"], "icon": "check",
                "label": "no"}},
      {"title": "A hold appeared?", "sub": ["client or server"], "icon": "branch",
       "exit": {"title": "Alarm now", "sub": ["the domain is not resolving"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Lifecycle code?", "sub": ["redemption, pendingDelete"], "icon": "branch",
       "exit": {"title": "Alarm, with days left", "sub": ["and the recovery cost"],
                "icon": "clock", "label": "yes"}},
      {"title": "A lock disappeared?", "sub": ["transfer prohibition gone"], "icon": "branch",
       "exit": {"title": "Ask why", "sub": ["a transfer, or a mistake"], "icon": "search",
                "label": "yes"}},
      {"title": "Report the change", "sub": ["quietly, in the digest"], "icon": "log"}],
    "note": "A lock disappearing on a domain nobody is transferring is worth a phone call."}),
   "How a status change is handled. Three of the four branches alarm, which is unusual for this "
   "series and reflects that status codes only change when something has happened.",
   "How domain status code changes are triaged",
   "A vertical chain of five steps entered by a box labelled This week's status, from the "
   "registry. Step one asks whether it changed from last week; no exits to Nothing to say, the "
   "usual outcome. Step two asks whether a hold appeared, client or server; if so it exits to "
   "Alarm now, because the domain is not resolving. Step three asks whether a lifecycle code is "
   "present such as redemption period or pending delete; if so it exits to Alarm with the days "
   "left and the recovery cost. Step four asks whether a lock disappeared, such as a transfer "
   "prohibition; if so it exits to Ask why, since it is either a transfer or a mistake. Step "
   "five reports the change quietly in the digest. A note says a lock disappearing on a domain "
   "nobody is transferring is worth a phone call."),
  ("h3", "Missing locks"),
  ("p", "The protective codes are the ones you want present, and their absence on an important "
        "domain is a finding the register should raise once rather than an alarm it repeats. A "
        "domain without <code>clientTransferProhibited</code> can be transferred away with less "
        "friction than one that has it, and turning it on is a single setting in every registrar "
        "dashboard."),
  ("p", "So the weekly check includes a one-off note: \"example.com has no transfer lock. Most "
        "registrars offer this free.\" Once acknowledged, it is not raised again unless the "
        "situation changes."),
  ("h2", "Nameservers"),
  ("p", "Not a status code, and the loudest thing on the whole record. Nameservers change when "
        "somebody moves hosting, and they change when somebody has taken control of a domain. "
        "Both are rare, and the second is the reason this is checked weekly rather than "
        "monthly."),
  ("fig", ("strip", {
    "stages": [
      {"title": "NS changed", "sub": ["since last week"], "icon": "dns"},
      {"title": "Expected?", "sub": ["nobody said so"], "icon": "branch"},
      {"title": "Alarm", "sub": ["immediately, to two people"], "icon": "alarm"},
      {"title": "Both old and new", "sub": ["in the message"], "icon": "log"},
      {"title": "Usually", "sub": ["a migration nobody mentioned"], "icon": "check"}],
    "title": "AN UNEXPECTED NAMESERVER CHANGE",
    "note": "Nine times in ten it is a migration. The tenth is why it goes to two people."}),
   "How a nameserver change is handled. It is almost always benign and the response is sized for "
   "the case where it is not.",
   "How an unexpected nameserver change is escalated",
   "A horizontal row of five boxes. NS changed: since last week. Expected: nobody said so. "
   "Alarm: immediately, to two people. Both old and new: included in the message. Usually: a "
   "migration nobody mentioned. A note says nine times in ten it is a migration, and the tenth "
   "is why it goes to two people."),
  ("p", "Including both the old and new nameservers in the message is what makes it a "
        "ten-second triage. Somebody who moved the hosting recognises the new ones immediately; "
        "somebody who did not recognises that they do not, and that is exactly the distinction "
        "the message needs to support."),
  ("p", "Next: the escalation, and who it actually goes to."),
 ],
},
{
 "slug": "how-a-renewal-gets-escalated",
 "title": "How a renewal gets escalated",
 "nav": "How it escalates",
 "read": 5, "words": 740,
 "desc": ("Ninety, thirty, seven and daily -- to people who currently work here, with the card "
          "and the registrar in the message so the fix is possible."),
 "og": ("Escalating to the address on the registration is escalating to a former employee. The "
        "ladder here uses your staff list, and the message carries what somebody needs to "
        "actually fix it."),
 "abstract": ("The four-step escalation, why it uses your staff list rather than the "
              "registration contact, and what has to be in the message for somebody to act on "
              "it in five minutes."),
 "lede": ("Everything up to here has been about knowing. This post is about telling somebody who "
          "can do something, which is where domain renewal reminders overwhelmingly fail &mdash; "
          "not by not being sent, but by being sent to a mailbox that has not been opened since "
          "2023."),
 "tags": ["domains", "escalation", "renewals", "Amazon SES", "operations", "serverless"],
 "takeaways": [
  "Escalation uses your staff list, never the address on the registration.",
  "Ninety, thirty, seven days, then daily, and daily does not stop at expiry.",
  "The message carries the registrar, the account, the card and the internal owner.",
  "After expiry the message changes to the recovery clock and the redemption cost.",
  "One report a quarter lists everything, so the register is checked rather than trusted.",
 ],
 "blocks": [
  ("h2", "Who is told"),
  ("fig", ("system", {
    "outside": [
      {"title": "Internal owner", "sub": ["from your staff list"], "icon": "person"},
      {"title": "Their manager", "sub": ["at thirty days"], "icon": "team"},
      {"title": "Whoever runs IT", "sub": ["at seven, and after"], "icon": "shield"}],
    "inside": [
      {"title": "Ladder", "sub": ["90 / 30 / 7 / daily"], "icon": "clock"},
      {"title": "Message builder", "sub": ["registrar, account,", "card, owner"], "icon": "doc"},
      {"title": "After expiry", "sub": ["recovery clock,", "not silence"], "icon": "alarm"}],
    "edges": [{"from": 0, "to": 0, "label": "renew, or say who will", "up": True},
              {"from": 1, "to": 1, "label": "at thirty days", "up": True},
              {"from": 2, "to": 2, "label": "at seven, and after", "up": True}],
    "note": "The registration contact is never used. It is the least reliable address you have."}),
   "Who hears about an approaching renewal, and in what order. The registration contact appears "
   "nowhere in this diagram, which is the point.",
   "How a domain renewal escalation reaches people who currently work here",
   "Three boxes across the top outside the AWS account. The Internal owner, taken from your "
   "staff list. Their manager, brought in at thirty days. And Whoever runs IT, at seven days and "
   "afterwards. Inside the account, three components. The Ladder, running at ninety, thirty and "
   "seven days and then daily. The Message builder, which includes the registrar, the account, "
   "the card and the internal owner. And After expiry, which switches to a recovery clock rather "
   "than going silent. Arrows show each party being asked to renew or to say who will. A note "
   "says the registration contact is never used, because it is the least reliable address you "
   "have."),
  ("h3", "Why not the registration contact"),
  ("p", "Because it is a snapshot of who bought the domain, sometimes years ago, and it is the "
        "one address in the whole business that nobody updates. Every registrar in the world "
        "already sends reminders there, and the fact that domains still lapse is the evidence "
        "that it does not work."),
  ("p", "The internal owner comes from your own register and is a person who currently works "
        "here, checked against your staff list. A domain whose internal owner has left is itself "
        "a finding, raised immediately rather than at ninety days, because it will otherwise be "
        "discovered at ninety days when the message bounces."),
  ("h2", "What the message contains"),
  ("callout", "Everything needed to fix it in five minutes", [
   "<strong>The domain and the date.</strong> \"portal.example.com expires 14 March &mdash; 90 "
   "days.\"",
   "<strong>The registrar, by name,</strong> and the account identifier if the register has it. "
   "Knowing which of four registrars a domain is at saves ten minutes of looking.",
   "<strong>Which card pays for it,</strong> last four digits, from the subscription register. "
   "This is what catches the expired-card case before it becomes a failed renewal.",
   "<strong>What depends on it.</strong> \"MX records point here; the customer portal runs on "
   "it.\" A domain nobody can place gets ignored; one with consequences attached does not.",
   "<strong>Two buttons.</strong> \"Renewed\" and \"Somebody else is handling this &mdash; who?\"",
  ]),
  ("p", "The card detail is the most valuable line and it only exists if something knows about "
        "recurring charges. If the subscription audit bot is running, this is a lookup; if not, "
        "it is a field somebody fills in once. Either way, an expired card is the single most "
        "common way a renewal that everybody expected to happen does not."),
  ("h2", "After the date"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Expiry day", "sub": ["may still resolve"], "icon": "calendar"},
      {"title": "Grace", "sub": ["registrar-dependent"], "icon": "clock"},
      {"title": "Redemption", "sub": ["recoverable, for a fee"], "icon": "money"},
      {"title": "Pending delete", "sub": ["days, then gone"], "icon": "alarm"},
      {"title": "Daily throughout", "sub": ["with the cost and the days"], "icon": "bell"}],
    "title": "THE CLOCK AFTER EXPIRY",
    "note": "This is exactly where most watchers stop reporting, and where hours start mattering."}),
   "What happens after an expiry date passes. A watcher that treats expiry as the end of its job "
   "goes quiet at the point where the situation is recoverable and getting less so.",
   "The recovery clock after a domain expires",
   "A horizontal row of five boxes. Expiry day: the domain may still resolve. Grace: a "
   "registrar-dependent period. Redemption: recoverable, for a fee. Pending delete: days, then "
   "gone. Daily throughout: with the cost and the days remaining. A note says this is exactly "
   "where most watchers stop reporting, and where hours start mattering."),
  ("p", "The message changes tone entirely at that point, and it should: it carries how many days "
        "remain in the current phase, what the recovery fee will be, and what has already stopped "
        "working. \"portal.example.com expired 11 days ago. It is in redemption for 19 more days; "
        "recovery is about £80. Mail to that domain has been bouncing since Tuesday.\""),
  ("h3", "The quarterly review"),
  ("p", "One report a quarter listing every domain, its expiry, its registrar, its internal owner "
        "and its status. Not because anything is wrong, but because a register is only as good as "
        "the last time somebody looked at it, and a domain whose owner left or whose purpose "
        "nobody remembers is exactly what a quarterly read finds."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="lookup",
 volumes=[(50, "50 lookups"), (150, "150 lookups"), (600, "600 lookups")],
 read_each=0.0, msgs_each=0.15,
 lede=("This is the cheapest system in the whole series. Eleven domains checked weekly is fewer "
       "than fifty lookups a month, each one an HTTPS request that costs nothing, and there is "
       "no model anywhere in it. Here is where each cent goes."),
 takeaway_extra=("RDAP lookups are free HTTPS requests and there is no model at all, so this is "
                 "essentially a fixed-cost system."),
 risks=[
  "<strong>Fetching the bootstrap on every lookup.</strong> The IANA bootstrap file is a few "
  "hundred kilobytes and changes rarely. Fetching it per domain per week is wasteful and "
  "impolite; cache it weekly.",
  "<strong>Certificate log searches on every run.</strong> Discovery is a monthly job, not a "
  "weekly one. Domains do not appear that fast and the searches are the only meaningful "
  "outbound cost.",
  "<strong>Log retention left at never.</strong> With a bill this small the logs will be a "
  "hundred per cent of it within months.",
 ],
 per_unit_note=("There is no read line at all here: nothing in this system calls a model. The "
                "bill is the fixed band plus a handful of emails, which is why it comes in "
                "around a dollar."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="dr",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the RDAP path, and why there is no model in it."),
 outside=[
  {"title": "RDAP + CT logs", "sub": ["outbound HTTPS"], "icon": "dns"},
  {"title": "Domain register", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["escalation, digest"], "icon": "email"}],
 inside=[
  {"title": "EventBridge", "sub": ["weekly check,", "monthly discovery"], "icon": "clock"},
  {"title": "Lambda x3", "sub": ["check, discover,", "escalate"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["domains, snapshots"], "icon": "database"}],
 note="us-east-1. One account. Outbound HTTPS only; no credential can renew anything.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. RDAP and certificate transparency logs, "
  "reached over outbound HTTPS. The Domain register, read through the Google Sheets API "
  "read-only. And SES outbound, carrying escalations and the quarterly digest. Inside the "
  "account, three groups. EventBridge carrying a weekly check and a monthly discovery run. Three "
  "Lambda functions named check, discover and escalate. And two DynamoDB tables named domains "
  "and snapshots. A note gives the region as us-east-1, one account, outbound HTTPS only, and "
  "states that no credential in it can renew anything."),
 functions=[
  ["<code>dr-check</code>", "EventBridge weekly",
   "RDAP per domain; diffs expiry, status and nameservers", "120s / 512&nbsp;MB"],
  ["<code>dr-discover</code>", "EventBridge monthly",
   "Certificate logs, hosted zones, and registrar charges", "120s / 512&nbsp;MB"],
  ["<code>dr-escalate</code>", "EventBridge daily",
   "The ladder, the post-expiry clock, and the quarterly digest", "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>dr-check-role</code>",
   "<code>dynamodb:PutItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Domains and snapshots; the Sheets credential only"],
  ["<code>dr-discover-role</code>",
   "<code>route53:ListHostedZones</code>, <code>dynamodb:PutItem</code>",
   "Zones, read; the domains table"],
  ["<code>dr-escalate-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "Domains, read; one verified identity"]],
 tables=[
  ("Table: domains",
   "PK   domain            S   example.com\n"
   "     state             S   watched | candidate | not_ours\n"
   "     expiry            S   2027-03-14\n"
   "     source            S   rdap | invoice   -- how confident that date is\n"
   "     registrar         S   name and IANA id\n"
   "     registrar_account S   the login identifier, not a credential\n"
   "     pays_with         S   card ending 4417\n"
   "     internal_owner    S   a person on the staff list, checked\n"
   "     depends           L   [mx, portal, redirect]\n"
   "     nameservers       L   as last seen\n"
   "     status            L   EPP status codes as last seen\n"
   "     last_checked      S   2026-07-26T06:00:00Z\n"
   "     fail_count        N   consecutive lookup failures\n\n"
   "`last_checked` is what a separate heartbeat scans. A domain not checked in\n"
   "three weeks alarms whatever the rest of the system believes."),
  ("Table: snapshots",
   "PK   domain            S   example.com\n"
   "SK   checked_at        S   2026-07-26\n"
   "     rdap              S   the response, as received\n"
   "     ttl               N   epoch, +2 years\n\n"
   "Keeping the raw response means a nameserver change can be evidenced later\n"
   "rather than asserted, and a parsing change can be tested against history.")],
 inbound=[
  "<strong>Outbound HTTPS only.</strong> There is no inbound path at all except the signed "
  "acknowledgement links in escalation messages.",
  "<strong>The IANA bootstrap</strong> is fetched weekly and cached. Fetching it per lookup is "
  "both wasteful and impolite to a free public service.",
  "<strong>RDAP requests identify themselves</strong> with a user agent naming the business and "
  "a contact address, which is the norm for automated registry queries.",
  "<strong>No credential in this account can renew, transfer or modify a domain.</strong> The "
  "escalation tells a person to go and do it in the registrar's own dashboard."],
 model_notes=[
  "<strong>There is no model in this system.</strong> RDAP returns structured JSON and status "
  "codes are a fixed vocabulary.",
  "<strong>The one place a model would fit</strong> is parsing free-text WHOIS for the "
  "registries without RDAP, and the honest choice is to not track those from WHOIS at all.",
  "<strong>Those domains carry an invoice date</strong> marked as such, with a longer lead time, "
  "rather than a parsed date presented as authoritative.",
  "<strong>Discovery is search and set difference</strong>, not classification. A candidate is "
  "any domain found that is not in the register.",
  "<strong>This is worth noting</strong> because it is a system where adding a model would make "
  "everything less reliable and nothing faster."],
 gotchas=[
  "Query the registry, not the registrar. They disagree exactly when it matters: a failed "
  "renewal payment, a transfer in flight, an acquired registrar with stale records.",
  "Do not stop reporting at expiry. The redemption and pending-delete windows are where days "
  "matter, and it is where most watchers go quiet.",
  "Escalate to your staff list. The registration contact is the least reliable address in the "
  "business and every registrar already emails it.",
  "Cache the IANA bootstrap. Fetching it per domain per week is rude to a free service and "
  "gains nothing.",
  "Record which card pays for each domain. An expired card is the most common cause of a "
  "renewal everybody assumed had happened."],
))
