"""Day 94 -- 2026-07-27 -- DNS change auditor."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "dns-change-auditor"
NAME = "DNS change auditor"

SPEC = {
 "slug": SLUG, "date": "2026-07-27", "name": NAME,
 "tagline": ("Every DNS record is snapshotted hourly, every change is shown as a diff to "
             "somebody who can say whether it was meant, and the records that must never move "
             "are checked separately."),
 "lede": ("A small system that takes an hourly snapshot of every DNS zone the business relies "
          "on, shows each change as a plain diff, and asks one person whether it was intended. "
          "It watches the mail records with particular care, because those break quietly and "
          "expensively. It cannot change a record. Seven posts on the same system -- one "
          "diagram at a time -- with a cost breakdown and an engineering reference at the end."),
 "keywords": ["DNS", "change auditing", "SPF", "DMARC", "infrastructure", "serverless"],
 "icons": ["dns", "search", "shield"],
 "faq": [
  ("What is a DNS change auditor?",
   "A small serverless system that snapshots your DNS zones hourly, diffs each snapshot against "
   "the last, and puts unexpected changes in front of a person. It is read-only: it cannot "
   "create, change or delete a record."),
  ("Why watch DNS at all?",
   "Because a DNS change is the fastest way to break something completely and the slowest thing "
   "to notice. A wrong MX record loses mail silently. A removed SPF include makes your invoices "
   "arrive in junk folders. Neither produces an error anybody sees."),
  ("Does it stop somebody making a change?",
   "No, and it should not. Changes are legitimate and frequent. What it does is make every one "
   "of them visible within the hour to somebody who can say whether it was meant, which is what "
   "does not currently happen."),
  ("What are critical records?",
   "The handful you nominate that should essentially never change: the apex A record, the MX "
   "records, the SPF and DMARC records, and the nameservers. Those get a stricter path: any "
   "change alarms immediately rather than appearing in a digest."),
  ("What does it cost to run?",
   "Around a dollar a month. It is a few DNS queries an hour. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "dns-change-auditor-on-aws",
 "title": "A DNS change auditor on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 870,
 "desc": ("Snapshots every zone hourly, diffs each change, and asks one person whether it was "
          "meant. Critical records alarm immediately. AWS, about $1 a month."),
 "og": ("A DNS change is the fastest way to break something completely and the slowest thing to "
        "notice. This makes every change visible within the hour."),
 "abstract": ("The whole system on one page -- a snapshotter, a differ and a confirmer -- and "
              "the split between records that appear in a digest and records that alarm."),
 "lede": ("DNS is the only part of a small business's infrastructure where one wrong character "
          "takes everything down and nothing anywhere reports an error. The site is fine, the "
          "server is fine, the monitoring is green, and mail has been going to a hostname that "
          "no longer exists for eleven days. Nobody did anything reckless; somebody tidied up a "
          "record that turned out to matter. This post walks through a small system that makes "
          "every change visible within the hour."),
 "tags": ["DNS", "change auditing", "SPF", "email deliverability", "infrastructure", "serverless"],
 "takeaways": [
  "An hourly snapshot of every record in every zone you rely on.",
  "Every change is shown as a diff, in plain terms, to one nominated person.",
  "Critical records -- apex, MX, SPF, DMARC, NS -- alarm immediately rather than in a digest.",
  "It is read-only. There is no credential in it that can change a record.",
  "Designed on AWS for about $1 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Your zones", "sub": ["wherever they are hosted"], "icon": "dns"},
      {"title": "Critical list", "sub": ["what must never move"], "icon": "shield"},
      {"title": "Whoever owns DNS", "sub": ["confirms or investigates"], "icon": "person"}],
    "inside": [
      {"title": "Snapshotter", "sub": ["hourly, every record,", "resolver not API"], "icon": "search"},
      {"title": "Differ", "sub": ["what changed,", "in plain words"], "icon": "filter"},
      {"title": "Confirmer", "sub": ["digest, or alarm,", "depending"], "icon": "bell"}],
    "edges": [{"from": 0, "to": 0, "label": "records, as resolved"},
              {"from": 1, "to": 1, "label": "which ones alarm"},
              {"from": 2, "to": 2, "label": "was this meant?", "up": True}],
    "note": "Read-only, always. Nothing in this account can change a DNS record."}),
   "Three things outside the account, three pieces inside it. The critical list in the middle is "
   "what separates a change that waits for a digest from one that rings a phone.",
   "System: zones snapshotted hourly, changes confirmed by a person",
   "Three boxes across the top sit outside the AWS account. On the left, Your zones: wherever "
   "they happen to be hosted. In the middle, Critical list: the records that must never move. On "
   "the right, Whoever owns DNS: the person who confirms a change or investigates it. Each "
   "connects by an arrow to the AWS account container below. Records as resolved flow down into "
   "the account. The critical list feeds in which records alarm. A question, was this meant, "
   "goes back out. Inside the AWS account are three components in a row. On the left, the "
   "Snapshotter, running hourly over every record, using a resolver rather than a provider API. "
   "In the middle, the Differ, which describes what changed in plain words. On the right, the "
   "Confirmer, which sends a digest or an alarm depending on what moved. A note at the bottom "
   "says the system is read-only and nothing in the account can change a DNS record."),
  ("h3", "Resolve, do not read the API"),
  ("p", "The obvious implementation reads your DNS provider's API and diffs the zone file. It is "
        "easier, it gives you the TTLs and the comments, and it answers a slightly different "
        "question from the one that matters."),
  ("p", "What matters is what the world sees. A zone can be correct in a provider's console and "
        "wrong in resolution &mdash; a delegation that was never updated, a second provider still "
        "authoritative from a migration two years ago, a record shadowed by a wildcard. Resolving "
        "the records the way a mail server or a browser would is the only check that catches "
        "those, and it works identically regardless of who hosts the zone."),
  ("h3", "What runs hourly (the inside)"),
  ("ul", [
   "<strong>The snapshotter.</strong> Queries every record type you care about for every name "
   "you have listed, from a resolver, and stores the answers. Part 2 covers what to query when "
   "you do not have a zone file to enumerate from.",
   "<strong>The differ.</strong> Compares this hour with last hour and describes the difference "
   "in terms a person can act on. \"The MX record now points at mail.oldhost.example\" rather "
   "than a unified diff of two text blobs.",
   "<strong>The confirmer.</strong> Routes it. A change to an ordinary record goes into a daily "
   "digest with a one-tap \"that was me\". A change to anything on the critical list alarms "
   "immediately, to two people.",
  ]),
  ("h2", "One change, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Snapshot", "sub": ["every hour"], "icon": "search"},
      {"title": "Diff", "sub": ["against last hour"], "icon": "filter"},
      {"title": "Critical?", "sub": ["apex, MX, SPF, NS"], "icon": "branch"},
      {"title": "Alarm or digest", "sub": ["minutes, or tomorrow"], "icon": "bell"},
      {"title": "Confirmed", "sub": ["that was me, or not"], "icon": "check"}],
    "title": "ONE DNS CHANGE, END TO END",
    "note": "Most changes are somebody's work. The point is that all of them are seen."}),
   "The same system as one line. Nearly every change is legitimate, and the value is in the "
   "small number that are not being visible within the hour rather than in eleven days.",
   "One DNS change from snapshot to confirmation, in five stages",
   "A horizontal row of five boxes joined by arrows. Snapshot: every hour. Diff: against last "
   "hour. Critical: is it the apex, MX, SPF or nameservers. Alarm or digest: within minutes, or "
   "tomorrow. Confirmed: that was me, or not. A note says most changes are somebody's work and "
   "the point is that all of them are seen."),
  ("h2", "In plain words"),
  ("p", "A developer is setting up a staging environment and adds a few records. Along the way "
        "they tidy what looks like a stale TXT record with a lot of odd syntax in it. It was the "
        "SPF record."),
  ("p", "Nothing breaks. The site is fine, mail still sends, and the monitoring stays green, "
        "because SPF failure does not stop mail leaving &mdash; it changes what receiving servers "
        "do with it. Over the following fortnight, an increasing proportion of the business's "
        "invoices and quotes land in junk folders, and the only symptom is customers saying they "
        "never got it. That is a genuinely difficult thing to diagnose from the outside and a "
        "trivial one to diagnose from a diff."),
  ("p", "With this system the change is detected within the hour, it is on the critical list, and "
        "two people get a message: \"TXT at example.com changed. Removed: v=spf1 include:... "
        "~all. Nothing replaced it.\" The developer says \"that was me, I thought it was stale\", "
        "puts it back, and the whole incident is eleven minutes long instead of a fortnight."),
  ("callout", "Design rules that shaped every decision", [
   "Resolve rather than read an API. What the world sees is the only thing that matters.",
   "Read-only, permanently. A system that can change DNS to fix DNS is a much more dangerous "
   "object.",
   "Describe changes in plain words. A unified diff of two zone files is not something somebody "
   "reads at nine on a Tuesday.",
   "Critical records alarm; everything else digests. Alarming on every CNAME trains people to "
   "ignore alarms.",
   "\"That was me\" is one tap and is the expected answer. This is an audit trail, not an "
   "approval process.",
   "Snapshot from more than one resolver. Propagation and split-horizon both produce false "
   "changes.",
  ]),
  ("h2", "Why this shape"),
  ("p", "DNS changes are frequent, legitimate, and made by people who are usually right. A "
        "system that tried to gate them would be worked around within a week and would deserve "
        "to be. The gap is not control; it is that nobody currently knows a change happened "
        "unless they made it."),
  ("p", "So this does exactly one thing: it makes every change visible, quickly, to one person "
        "who can recognise their own work in two seconds and will notice immediately when "
        "something is not their work. That is a much weaker control than approval and it catches "
        "the cases that actually happen."),
  ("p", "The next four posts walk through each piece: how a zone gets enumerated and snapshotted, "
        "how a diff is described, why mail records get their own treatment, and how confirmation "
        "works. One diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-a-zone-gets-snapshotted",
 "title": "How a zone gets snapshotted",
 "nav": "How it snapshots",
 "read": 5, "words": 770,
 "desc": ("Enumerating names when you cannot list a zone, which record types matter, and why "
          "two resolvers are better than one."),
 "og": ("You usually cannot enumerate a zone from outside, so the name list comes from four "
        "places you already have. Two resolvers stop propagation looking like a change."),
 "abstract": ("How to build the list of names to check when you cannot enumerate a zone, which "
              "record types are worth querying, and why two resolvers matter."),
 "lede": ("There is an awkward fact at the centre of this design: from outside, you generally "
          "cannot list what is in a DNS zone. You can only ask about names you already know. So "
          "the first job is knowing which names to ask about, and it turns out you have four "
          "sources for that."),
 "tags": ["DNS", "enumeration", "resolvers", "monitoring", "infrastructure", "serverless"],
 "takeaways": [
  "You cannot enumerate a zone from outside. The name list is assembled from four sources.",
  "Certificate transparency is the best single source of hostnames you actually use.",
  "Query a fixed set of record types per name, not everything.",
  "Two resolvers, and a change is only a change when both agree.",
  "A name that stops resolving is as important as one that changes.",
 ],
 "blocks": [
  ("h2", "Building the name list"),
  ("fig", ("chain", {
    "entry": {"title": "A domain", "sub": ["from the register"], "icon": "dns"},
    "steps": [
      {"title": "Provider API, if you have one", "sub": ["the complete list"], "icon": "external",
       "exit": {"title": "Done", "sub": ["enumerate directly"], "icon": "check",
                "label": "available"}},
      {"title": "Certificate logs", "sub": ["every hostname with a cert"], "icon": "shield"},
      {"title": "Your own config", "sub": ["what your apps refer to"], "icon": "code"},
      {"title": "The obvious names", "sub": ["apex, www, mail, and the", "well-known TXT names"],
       "icon": "doc"},
      {"title": "A name list", "sub": ["usually 20 to 60"], "icon": "counter"}],
    "note": "The list is a superset. A name that has never resolved is checked and stays absent."}),
   "How the list of names to snapshot is built. Where a provider API exists it is the complete "
   "answer; where it does not, three sources between them cover almost everything that matters.",
   "How the list of DNS names to snapshot is assembled",
   "A vertical chain of five steps entered by a box labelled A domain, from the register. Step "
   "one asks whether a provider API is available giving the complete list; if so it exits to "
   "Done and enumerates directly. Step two adds names from certificate transparency logs, "
   "covering every hostname that has had a certificate. Step three adds names from your own "
   "application configuration. Step four adds the obvious names: the apex, www, mail, and the "
   "well-known TXT names. Step five produces a name list, usually twenty to sixty entries. A "
   "note says the list is a superset, and a name that has never resolved is checked and stays "
   "absent."),
  ("h3", "Where a provider API exists, use it"),
  ("p", "If your zones are in Route 53, or any provider with a list-records API, that is the "
        "complete answer and the enumeration problem disappears. Read the zone, snapshot every "
        "record, done. Most small businesses have at least one zone like this and at least one "
        "that is somewhere else entirely."),
  ("p", "Even then, the resolved check is still worth running alongside it, because a zone that "
        "is correct in the provider and not authoritative in the real world is precisely the "
        "failure the API view cannot show you."),
  ("h3", "The obvious names"),
  ("p", "A fixed list that costs nothing to check and catches a surprising amount: the apex, "
        "<code>www</code>, <code>mail</code>, <code>autodiscover</code>, "
        "<code>_dmarc</code>, <code>_domainkey</code> and the selectors your mail provider uses, "
        "and <code>_acme-challenge</code>. The last one is worth watching for an unusual reason: "
        "a validation record that has been left in place long after a certificate was issued is "
        "an untidiness, and one that appears when nobody is issuing a certificate is not."),
  ("h2", "Which record types"),
  ("table", ["Type", "Why", "Where"], [
   ["A / AAAA", "Where a name points", "Every name"],
   ["CNAME", "What a name aliases", "Every name"],
   ["MX", "Where mail goes", "Apex and any mail subdomain"],
   ["TXT", "SPF, DMARC, verification tokens", "Apex, _dmarc, selectors"],
   ["NS", "Who is authoritative", "Apex and any delegated subdomain"],
   ["CAA", "Who may issue certificates", "Apex"],
  ]),
  ("p", "CAA is the one most people leave out and it is cheap to include. A CAA record that "
        "changes, or one that disappears, changes who is allowed to issue a certificate for your "
        "domain, and that is worth a message."),
  ("h2", "Two resolvers"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Resolver A", "sub": ["says X"], "icon": "dns"},
      {"title": "Resolver B", "sub": ["says Y"], "icon": "dns"},
      {"title": "Disagree", "sub": ["mid-propagation"], "icon": "clock"},
      {"title": "Wait an hour", "sub": ["check again"], "icon": "retry"},
      {"title": "Both agree", "sub": ["now it is a change"], "icon": "check"}],
    "title": "WHY TWO RESOLVERS",
    "note": "A single resolver mid-propagation reports a change, then reports it back again."}),
   "Why the snapshot uses two independent resolvers. Propagation makes a single resolver report "
   "a change and then un-report it, which is exactly how people learn to ignore a monitor.",
   "Why DNS snapshots are taken from two resolvers",
   "A horizontal row of five boxes. Resolver A says X. Resolver B says Y. Disagree: the zone is "
   "mid-propagation. Wait an hour: and check again. Both agree: now it is a change. A note says "
   "a single resolver mid-propagation reports a change and then reports it back again."),
  ("p", "Requiring both resolvers to agree before calling something a change removes almost all "
        "propagation noise at the cost of one extra query per name and up to an hour of delay. "
        "For a critical record that delay is unwelcome, so critical records use a third resolver "
        "and alarm on two out of three &mdash; faster, and still not fooled by one stale cache."),
  ("h3", "Disappearance"),
  ("p", "A name that resolved yesterday and does not today is a change, and it is one that a "
        "naive diff on record contents will miss entirely. It is also, in practice, more likely "
        "to be a real problem than a modification: records get deleted during tidy-ups far more "
        "often than they get maliciously edited."),
  ("p", "Next: how a change gets described."),
 ],
},
{
 "slug": "how-a-dns-change-gets-described",
 "title": "How a DNS change gets described",
 "nav": "How it is described",
 "read": 5, "words": 750,
 "desc": ("Turning a record diff into a sentence somebody will read, why the consequence matters "
          "more than the syntax, and the changes that are worth explaining."),
 "og": ("A unified diff of two zone files is not something anybody reads on a Tuesday. The "
        "message says what changed and what it means."),
 "abstract": ("Turning a record diff into a sentence somebody will actually read, why the "
              "consequence belongs in the message, and the specific changes worth explaining."),
 "lede": ("The difference between a DNS monitor people act on and one they filter is entirely in "
          "the wording of the message. A diff is correct and unreadable. A sentence with the "
          "consequence in it gets answered in ten seconds."),
 "tags": ["DNS", "notifications", "diffs", "AWS Bedrock", "operations", "serverless"],
 "takeaways": [
  "The message names the record, the old value, the new value, and the consequence.",
  "The consequence comes from a fixed table, not from a model.",
  "A model is used for one thing: describing an SPF or DMARC change in plain words.",
  "Additions, modifications and deletions read differently and should.",
  "A change with no known consequence says so rather than inventing one.",
 ],
 "blocks": [
  ("h2", "Four lines"),
  ("callout", "What a change message says", [
   "<strong>The record.</strong> \"MX at example.com\"",
   "<strong>Was.</strong> \"10 mail.provider.example\"",
   "<strong>Now.</strong> \"10 mail.oldhost.example\"",
   "<strong>Which means.</strong> \"Incoming mail for example.com now goes to "
   "mail.oldhost.example. If that host is not accepting mail, messages will bounce or be lost.\"",
   "<strong>Two buttons.</strong> \"That was me\" and \"Not me &mdash; investigate\".",
  ]),
  ("p", "The fourth line is the one that changes behaviour. A person reading the first three "
        "lines has to know what an MX record does to know whether to care; a person reading the "
        "fourth does not. And the people most likely to be reading this message at nine on a "
        "Tuesday are exactly the people who half-remember."),
  ("h2", "Consequences come from a table"),
  ("fig", ("chain", {
    "entry": {"title": "A confirmed change", "sub": ["record, old, new"], "icon": "filter"},
    "steps": [
      {"title": "Known record type?", "sub": ["MX, NS, apex A, CAA"], "icon": "branch",
       "side": {"title": "Consequence table", "sub": ["one sentence each"], "icon": "doc"},
       "exit": {"title": "Use the sentence", "sub": ["fixed, never generated"], "icon": "check",
                "label": "yes"}},
      {"title": "SPF or DMARC?", "sub": ["syntax people cannot read"], "icon": "branch",
       "exit": {"title": "One Bedrock call", "sub": ["explain the difference"], "icon": "model",
                "label": "yes"}},
      {"title": "Anything else", "sub": ["a CNAME, a TXT token"], "icon": "search"},
      {"title": "Say so plainly", "sub": ["'we don't know what this", "one is for'"], "icon": "chat"}],
    "note": "The model is used on exactly two record types, because their syntax is genuinely opaque."}),
   "How a change gets its explanation. Almost every record type has one fixed sentence; the two "
   "that do not are the ones whose syntax nobody can read at a glance.",
   "How a DNS change is turned into a readable explanation",
   "A vertical chain of four steps entered by a box labelled A confirmed change, carrying the "
   "record, the old value and the new. Step one asks whether it is a known record type such as "
   "MX, NS, an apex A record or CAA, checking a consequence table with one sentence each; a hit "
   "exits to Use the sentence, which is fixed and never generated. Step two asks whether it is "
   "SPF or DMARC, whose syntax people cannot read; if so it exits to One Bedrock call to explain "
   "the difference. Step three covers anything else, such as a CNAME or a TXT token. Step four "
   "says so plainly: we do not know what this one is for. A note says the model is used on "
   "exactly two record types because their syntax is genuinely opaque."),
  ("h3", "Why fixed sentences"),
  ("p", "An MX change means the same thing every time and the sentence explaining it can be "
        "written once, carefully, by somebody who knows what they are talking about. Generating "
        "it produces a slightly different sentence each time, occasionally a wrong one, and "
        "always a more expensive one."),
  ("p", "The consequence table has perhaps a dozen entries and covers the record types where a "
        "change has a predictable effect. It is a sheet, so somebody who thinks a sentence is "
        "unclear can improve it without touching any code."),
  ("h3", "Why SPF and DMARC are different"),
  ("p", "Because the change is inside a string, and the string is genuinely unreadable. \"v=spf1 "
        "include:_spf.provider.example include:mail.other.example ~all\" becoming the same string "
        "with one include missing is a diff that a person can see and cannot interpret at a "
        "glance."),
  ("p", "So those two get one model call, given both strings and asked what the practical "
        "difference is: \"mail sent through Other Mail Provider will no longer pass SPF.\" That "
        "is a sentence with a consequence in it, and it is the kind of thing a model is genuinely "
        "good at that a lookup table cannot do."),
  ("h2", "Three shapes of change"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Added", "sub": ["usually fine"], "icon": "check"},
      {"title": "Modified", "sub": ["show both values"], "icon": "retry"},
      {"title": "Deleted", "sub": ["the dangerous one"], "icon": "alarm"},
      {"title": "Stopped resolving", "sub": ["not the same as deleted"], "icon": "search"},
      {"title": "Reappeared", "sub": ["worth a sentence"], "icon": "bell"}],
    "title": "FIVE THINGS THAT COUNT AS A CHANGE",
    "note": "Deletion and non-resolution look identical to a diff and are different problems."}),
   "The five shapes of change and why they read differently. A record that stopped resolving "
   "without being deleted is a delegation or propagation problem rather than an edit.",
   "Five kinds of DNS change and how each is treated",
   "A horizontal row of five boxes. Added: usually fine. Modified: show both values. Deleted: the "
   "dangerous one. Stopped resolving: which is not the same as deleted. Reappeared: worth a "
   "sentence. A note says deletion and non-resolution look identical to a diff and are different "
   "problems."),
  ("p", "Distinguishing deletion from non-resolution needs the provider API where one exists: a "
        "record that is still in the zone but no longer resolving is a delegation problem, and "
        "one that has gone from the zone is an edit. Where there is no API, the message says "
        "which it cannot tell &mdash; \"stopped resolving; we cannot see the zone to say whether "
        "it was removed\" &mdash; because that distinction changes who you go and talk to."),
  ("p", "Next: the mail records, which get their own post for good reason."),
 ],
},
{
 "slug": "how-mail-records-get-watched",
 "title": "How mail records get watched",
 "nav": "How mail is watched",
 "read": 5, "words": 760,
 "desc": ("MX, SPF, DKIM and DMARC -- why each breaks silently, what a change to each actually "
          "does, and the one check that is not a diff at all."),
 "og": ("Mail records break without producing an error. A wrong MX loses mail; a broken SPF "
        "sends your invoices to junk. Both are invisible from inside the business."),
 "abstract": ("Why the four mail records break silently, what a change to each actually does, "
              "and the one mail check that is not a diff at all."),
 "lede": ("Mail records deserve their own post because they share a property that makes them "
          "uniquely dangerous: breaking them produces no error anywhere you can see. Everything "
          "still sends. Nothing logs a failure. The only symptom is customers not replying, and "
          "that takes weeks to notice and is nearly impossible to attribute."),
 "tags": ["DNS", "SPF", "DKIM", "DMARC", "email deliverability", "serverless"],
 "takeaways": [
  "Four records, four different silent failures.",
  "MX: mail stops arriving, and senders may not get a bounce for days.",
  "SPF: your mail still sends and increasingly lands in junk.",
  "DKIM: signatures stop verifying, usually after a provider key rotation.",
  "DMARC is the one that tells you the others are broken, if you read the reports.",
 ],
 "blocks": [
  ("h2", "Four silent failures"),
  ("table", ["Record", "If it breaks", "How you find out today"], [
   ["MX", "Incoming mail bounces or vanishes",
    "A customer says they emailed you, days later"],
   ["SPF", "Your outgoing mail is treated as suspicious",
    "Invoices are 'never received', over weeks"],
   ["DKIM", "Signatures fail; the same as SPF but harder to spot",
    "Same as SPF, and usually blamed on SPF"],
   ["DMARC", "Nothing immediately; you lose your reporting",
    "You do not"],
  ]),
  ("p", "The third column is the argument for the whole system. Every one of those failures is "
        "currently discovered by a customer, indirectly, after enough time has passed that the "
        "cause is no longer obvious. A change detected within the hour with a sentence explaining "
        "it removes all four."),
  ("h2", "What each change means"),
  ("fig", ("chain", {
    "entry": {"title": "A mail record changed", "sub": ["MX, SPF, DKIM or DMARC"], "icon": "email"},
    "steps": [
      {"title": "MX?", "sub": ["incoming mail"], "icon": "branch",
       "exit": {"title": "Alarm, both people", "sub": ["mail may be lost now"], "icon": "alarm",
                "label": "yes"}},
      {"title": "SPF?", "sub": ["outgoing reputation"], "icon": "branch",
       "exit": {"title": "Alarm, with the diff", "sub": ["which sender lost cover"],
                "icon": "shield", "label": "yes"}},
      {"title": "DKIM selector?", "sub": ["provider key"], "icon": "branch",
       "exit": {"title": "Check it verifies", "sub": ["not just that it changed"], "icon": "key",
                "label": "yes"}},
      {"title": "DMARC?", "sub": ["policy and reporting"], "icon": "branch",
       "exit": {"title": "Alarm on policy weakening", "sub": ["reject to none is a big change"],
                "icon": "alarm", "label": "yes"}},
      {"title": "Recorded", "sub": ["and in the digest"], "icon": "log"}],
    "note": "DKIM is the one where changing is normal. What matters is whether it still verifies."}),
   "How each mail record change is handled. DKIM is the exception: rotation is routine, so the "
   "check is functional rather than a diff.",
   "How changes to the four mail records are handled",
   "A vertical chain of five steps entered by a box labelled A mail record changed, being MX, "
   "SPF, DKIM or DMARC. Step one asks whether it is MX, affecting incoming mail; if so it exits "
   "to Alarm to both people, because mail may be lost now. Step two asks whether it is SPF, "
   "affecting outgoing reputation; if so it exits to Alarm with the diff, naming which sender "
   "lost cover. Step three asks whether it is a DKIM selector, which is a provider key; if so it "
   "exits to Check it verifies, rather than merely noting that it changed. Step four asks "
   "whether it is DMARC, covering policy and reporting; if so it exits to Alarm on policy "
   "weakening, noting that reject to none is a big change. Step five records it and includes it "
   "in the digest. A note says DKIM is the one where changing is normal, and what matters is "
   "whether it still verifies."),
  ("h3", "SPF: which sender lost cover"),
  ("p", "An SPF record is a list of who is allowed to send as you, and the useful description of "
        "a change is not the string diff but the answer to \"which of our senders is no longer "
        "covered?\" A removed include is usually a whole mail provider, and naming it is what "
        "makes the message actionable."),
  ("p", "There is a second SPF failure worth watching that is not a change at all: the lookup "
        "limit. SPF permits a bounded number of DNS lookups when evaluating a record, and a "
        "business that has accumulated includes over the years can cross it. When that happens "
        "the record stops working entirely, without anybody having edited it, because a provider "
        "added an include inside their own include."),
  ("h3", "DKIM: changing is normal"),
  ("p", "Mail providers rotate DKIM keys, sometimes automatically, and a selector record changing "
        "is routine rather than alarming. Treating every rotation as an incident is how this "
        "particular check gets muted."),
  ("p", "So the DKIM check is functional: take the selector, fetch the key, and confirm it is "
        "well-formed and of a sane length. A rotation that produces a valid key is a digest line. "
        "A selector that stops resolving, or returns something malformed, is an alarm &mdash; and "
        "that is the actual failure mode, usually caused by a provider migration where the new "
        "selector was never added."),
  ("h2", "The check that is not a diff"),
  ("fig", ("strip", {
    "stages": [
      {"title": "SPF lookups", "sub": ["count them, weekly"], "icon": "counter"},
      {"title": "At 8 of 10", "sub": ["warn"], "icon": "bell"},
      {"title": "At 10", "sub": ["the record fails entirely"], "icon": "alarm"},
      {"title": "Nobody edited it", "sub": ["a provider grew theirs"], "icon": "search"},
      {"title": "No diff would catch it", "sub": ["which is the point"], "icon": "shield"}],
    "title": "THE SPF LOOKUP LIMIT",
    "note": "A record that has not changed can stop working. Counting is the only way to see it."}),
   "The one mail check that a change auditor would otherwise miss completely: a record that is "
   "byte-identical to last week and has stopped being valid.",
   "How the SPF lookup limit is monitored",
   "A horizontal row of five boxes. SPF lookups: counted weekly. At eight of ten: warn. At ten: "
   "the record fails entirely. Nobody edited it: a provider grew their own include. No diff "
   "would catch it: which is the point. A note says a record that has not changed can stop "
   "working, and counting is the only way to see it."),
  ("p", "Counting SPF lookups means resolving the record and recursively following every "
        "<code>include</code>, <code>a</code>, <code>mx</code> and <code>redirect</code> in it, "
        "which is a dozen lines of code and the single most valuable non-diff check in the whole "
        "system. It catches a failure that has no author and no event."),
  ("p", "Next: how confirmation works, and what the digest looks like."),
 ],
},
{
 "slug": "how-a-dns-change-gets-confirmed",
 "title": "How a DNS change gets confirmed",
 "nav": "How it is confirmed",
 "read": 5, "words": 730,
 "desc": ("One tap to say it was you, the daily digest for everything else, and the one number "
          "that says whether the critical list is set right."),
 "og": ("\"That was me\" is the expected answer and should take one tap. Everything else is a "
        "daily digest, because alarming on every CNAME trains people to ignore alarms."),
 "abstract": ("The one-tap confirmation, the daily digest for everything else, what an "
              "unconfirmed change escalates to, and the number that says whether the critical "
              "list is right."),
 "lede": ("The last piece is the cheapest and it determines whether any of the rest gets read. "
          "This is an audit trail rather than an approval process, so confirming a change has to "
          "cost about two seconds, and the answer is nearly always yes."),
 "tags": ["DNS", "auditing", "notifications", "operations", "reporting", "serverless"],
 "takeaways": [
  "\"That was me\" is one tap and is the expected answer.",
  "Ordinary changes go into a daily digest, not an alarm.",
  "An unconfirmed critical change escalates within hours, to a second person.",
  "Confirmation is recorded, so the log answers who knew about what and when.",
  "If more than a couple of changes a month alarm, the critical list is too broad.",
 ],
 "blocks": [
  ("h2", "Two channels"),
  ("fig", ("system", {
    "outside": [
      {"title": "Whoever owns DNS", "sub": ["confirms"], "icon": "person"},
      {"title": "A second person", "sub": ["only if unconfirmed"], "icon": "team"},
      {"title": "The log", "sub": ["every change, forever"], "icon": "log"}],
    "inside": [
      {"title": "Alarm path", "sub": ["critical records,", "within minutes"], "icon": "alarm"},
      {"title": "Digest path", "sub": ["everything else,", "once a day"], "icon": "report"},
      {"title": "Escalator", "sub": ["unconfirmed critical,", "after four hours"], "icon": "clock"}],
    "edges": [{"from": 0, "to": 0, "label": "that was me", "up": True},
              {"from": 1, "to": 1, "label": "after four hours", "up": True},
              {"from": 2, "to": 2, "label": "everything, confirmed or not", "up": True}],
    "note": "The log records every change whether or not anybody confirmed it."}),
   "The two notification channels and the escalation between them. Everything reaches the log "
   "regardless; the channels only decide how quickly a person is asked.",
   "How DNS changes are confirmed through two channels",
   "Three boxes across the top outside the AWS account. Whoever owns DNS, who confirms. A second "
   "person, involved only if a change is unconfirmed. And the log, which records every change "
   "forever. Inside the account, three components. The Alarm path, for critical records, within "
   "minutes. The Digest path, for everything else, once a day. And the Escalator, for an "
   "unconfirmed critical change after four hours. Arrows show the owner replying that was me, a "
   "second person being reached after four hours, and everything reaching the log whether "
   "confirmed or not. A note says the log records every change whether or not anybody confirmed "
   "it."),
  ("h3", "The daily digest"),
  ("callout", "Yesterday's changes", [
   "<strong>3 changes, all in staging.example.com.</strong> Added: api-v2, worker-2. Modified: "
   "api CNAME now points at the new load balancer.",
   "<strong>1 change at example.com.</strong> TXT <code>_acme-challenge</code> removed &mdash; "
   "this usually follows a certificate being issued.",
   "<strong>SPF lookups: 7 of 10.</strong> Unchanged from last week.",
   "<strong>Nothing on the critical list changed.</strong>",
   "<em>One tap: all of these were expected.</em>",
  ]),
  ("p", "Four lines and one button. The last line is the one that gets read and it is the only "
        "one that matters on a normal day &mdash; and its absence on an abnormal day is far more "
        "noticeable than any amount of red."),
  ("h3", "Why not alarm on everything"),
  ("p", "Because a business doing ordinary work generates several DNS changes a week and none of "
        "them is an emergency. Alarming on all of them produces a channel people mute within a "
        "fortnight, and a muted channel does not carry the MX change either."),
  ("h2", "Unconfirmed critical changes"),
  ("p", "The interesting case is a critical record changing and nobody saying it was them. That "
        "is not necessarily bad &mdash; the person who did it may be driving &mdash; but it is "
        "the exact shape of the situation the system exists for."),
  ("fig", ("strip", {
    "stages": [
      {"title": "MX changed", "sub": ["alarm sent"], "icon": "alarm"},
      {"title": "No confirmation", "sub": ["after 4 hours"], "icon": "clock"},
      {"title": "Second person", "sub": ["with the diff"], "icon": "team"},
      {"title": "Still nothing", "sub": ["after 8 hours"], "icon": "bell"},
      {"title": "Everyone on the list", "sub": ["with what it points at now"], "icon": "shield"}],
    "title": "AN UNCONFIRMED CRITICAL CHANGE",
    "note": "Usually somebody was busy. The ladder is sized for the time it is not."}),
   "What happens when a critical change goes unconfirmed. The ladder is short because the "
   "situations it is sized for are measured in hours.",
   "How an unconfirmed critical DNS change escalates",
   "A horizontal row of five boxes. MX changed: an alarm is sent. No confirmation: after four "
   "hours. Second person: told, with the diff. Still nothing: after eight hours. Everyone on the "
   "list: told, with what the record points at now. A note says usually somebody was busy, and "
   "the ladder is sized for the time it is not."),
  ("h2", "Is the critical list right"),
  ("p", "One number tells you: how many alarms fired last month. The target is one or two. Zero "
        "for several months running probably means the list is too narrow &mdash; a business "
        "genuinely does change its DNS &mdash; and more than about four a month means it is too "
        "broad and the alarms are becoming routine."),
  ("p", "The most common over-inclusion is putting every A record on the critical list. The apex "
        "matters; <code>staging-api-3</code> does not, and including it means somebody gets a "
        "phone alert every time a developer does their job."),
  ("h3", "What the log answers"),
  ("p", "Every change, its diff, when it was seen, who confirmed it, and when. Twelve months of "
        "that answers a question that is otherwise unanswerable: \"when did this record become "
        "wrong, and did anybody know?\" It is a few thousand small rows and it costs nothing."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="check hour",
 volumes=[(720, "720 hours"), (2160, "3 zones hourly"), (7200, "10 zones hourly")],
 read_each=0.00002, msgs_each=0.03,
 lede=("Hourly DNS queries are free and there is almost no model use, so this is a fixed-cost "
       "system with a rounding error attached. Seven hundred and twenty check-hours is one zone "
       "checked every hour for a month. Here is where each cent goes."),
 takeaway_extra=("DNS queries cost nothing and the model runs only on SPF and DMARC changes, "
                 "which happen a few times a year."),
 risks=[
  "<strong>Running every minute instead of every hour.</strong> Tempting, and it multiplies the "
  "Lambda invocations by sixty for a detection improvement measured against DNS TTLs that are "
  "usually an hour anyway.",
  "<strong>Snapshotting the full response every hour.</strong> Store a hash and keep the full "
  "response only when it changes. An unchanged zone should cost one small item, not one per "
  "hour.",
  "<strong>Log retention left at never.</strong> An hourly job across ten zones produces a "
  "steady trickle of log lines that will out-cost every other line within months.",
 ],
 per_unit_note=("The read line is nominal: a model is called only when an SPF or DMARC record "
                "changes, which for most businesses is a handful of times a year."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="da",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the resolver discipline, and the read-only posture."),
 outside=[
  {"title": "Public resolvers", "sub": ["two, plus one for critical"], "icon": "dns"},
  {"title": "Name list", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "SNS + SES", "sub": ["alarms and the digest"], "icon": "email"}],
 inside=[
  {"title": "EventBridge", "sub": ["hourly snapshot,", "daily digest"], "icon": "clock"},
  {"title": "Lambda x3", "sub": ["snapshot, diff,", "notify"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["current, changes"], "icon": "database"}],
 note="us-east-1. One account. No credential in it can create, change or delete a DNS record.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Public resolvers, two of them plus a "
  "third for critical records. The Name list, read through the Google Sheets API read-only. And "
  "SNS with SES, carrying alarms and the daily digest. Inside the account, three groups. "
  "EventBridge carrying an hourly snapshot and a daily digest schedule. Three Lambda functions "
  "named snapshot, diff and notify. And two DynamoDB tables named current and changes. A note "
  "gives the region as us-east-1, one account, and states that no credential in it can create, "
  "change or delete a DNS record."),
 functions=[
  ["<code>da-snapshot</code>", "EventBridge hourly",
   "Resolves every name and type from two resolvers; hashes the result",
   "120s / 512&nbsp;MB"],
  ["<code>da-diff</code>", "SQS snapshot queue",
   "Compares with current; classifies and describes each change", "30s / 512&nbsp;MB"],
  ["<code>da-notify</code>", "SQS change queue + EventBridge daily",
   "Alarms on critical, digests the rest, runs the escalation", "20s / 512&nbsp;MB"]],
 roles=[
  ["<code>da-snapshot-role</code>",
   "<code>dynamodb:GetItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "The current table, read; the Sheets credential only"],
  ["<code>da-diff-role</code>",
   "<code>dynamodb:PutItem</code>, <code>bedrock:InvokeModel</code>",
   "Current and changes; one model arn"],
  ["<code>da-notify-role</code>", "<code>sns:Publish</code>, <code>ses:SendEmail</code>",
   "The operations topic; one verified identity"]],
 tables=[
  ("Table: current",
   "PK   name              S   example.com\n"
   "SK   rrtype            S   MX\n"
   "     values            L   sorted, so ordering is not a diff\n"
   "     digest            S   sha256 of the sorted values\n"
   "     critical          BOOL true\n"
   "     resolvers_agree   BOOL true\n"
   "     last_seen         S   2026-07-27T14:00:00Z\n"
   "     spf_lookups       N   only on the apex TXT: 7\n\n"
   "Values are SORTED before hashing. Two MX records returned in a different\n"
   "order by a resolver is not a change, and un-sorted comparison would report\n"
   "one every few hours."),
  ("Table: changes",
   "PK   name_rrtype       S   example.com#MX\n"
   "SK   seen_at           S   2026-07-27T14:00:00Z\n"
   "     kind              S   added | modified | deleted | unresolvable | reappeared\n"
   "     old               L   the previous values\n"
   "     new               L   the current values\n"
   "     consequence       S   from the table, or from the model for SPF/DMARC\n"
   "     critical          BOOL true\n"
   "     confirmed_by      S   who said it was them\n"
   "     confirmed_at      S   when\n"
   "     escalated_to      L   [who, when]\n"
   "     ttl               N   epoch, +3 years")],
 inbound=[
  "<strong>Outbound DNS only</strong>, plus the signed confirmation links. There is no inbound "
  "path of any kind.",
  "<strong>Two resolvers</strong> for ordinary records and three for critical ones, so a stale "
  "cache cannot manufacture a change or delay a real one.",
  "<strong>DNS over HTTPS</strong> to public resolvers, rather than UDP, so the whole thing works "
  "from a Lambda with no VPC and no NAT gateway. That last detail is worth more than it sounds: "
  "a NAT gateway would cost thirty times the rest of this system.",
  "<strong>Nothing in the account has a Route 53 write permission</strong>, and a read permission "
  "only where a provider API is used for enumeration."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock, "
  "used only to describe the practical difference between two SPF or DMARC strings.",
  "<strong>Every other record type</strong> uses a fixed sentence from the consequence table, "
  "which is a sheet somebody can improve without a deploy.",
  "<strong>Called a handful of times a year.</strong> SPF and DMARC records change rarely, which "
  "is exactly why a change to one matters.",
  "<strong>Output is a JSON schema</strong> with one sentence and a nullable named sender. A null "
  "produces the diff with no interpretation rather than a guess.",
  "<strong>It is never asked whether a change is bad.</strong> That is the question a person "
  "answers by recognising their own work or not."],
 gotchas=[
  "Sort record values before hashing. Resolvers return multi-value records in varying order and "
  "an unsorted comparison reports a change every few hours.",
  "Use DNS over HTTPS from Lambda. Doing UDP DNS properly means a VPC and a NAT gateway, which "
  "would cost thirty times the entire rest of this system.",
  "Require two resolvers to agree. A single resolver mid-propagation reports a change and then "
  "reports it back, which is how a monitor gets muted.",
  "Count SPF lookups. It is the one failure with no author and no event, and no diff will ever "
  "catch it.",
  "Keep the critical list short. Putting every A record on it means an alert every time a "
  "developer does their job."],
))
