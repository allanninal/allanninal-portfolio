"""Day 102 -- 2026-08-04 -- Access review reporter."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "access-review-reporter"
NAME = "Access review reporter"

SPEC = {
 "slug": SLUG, "date": "2026-08-04", "name": NAME,
 "tagline": ("Lists who can get into what across every system the business uses, asks one owner "
             "per system a short question twice a year, and catches the leaver whose account is "
             "still live the week they go."),
 "lede": ("A small system that collects the user list from every service the business pays for, "
          "attaches an owner to each service, runs a short review twice a year, and checks "
          "continuously for accounts belonging to people who have left. It cannot remove access, "
          "and it says so. Seven posts on the same system -- one diagram at a time -- with a cost "
          "breakdown and an engineering reference at the end."),
 "keywords": ["access review", "offboarding", "SaaS", "security", "compliance", "serverless"],
 "icons": ["lock", "team", "report"],
 "faq": [
  ("What is an access review reporter?",
   "A small serverless system that collects who has access to which services, matches those "
   "accounts against your current staff list, runs a periodic review with the owner of each "
   "service, and flags leavers continuously. It reports; removing access is done by a person in "
   "the service itself."),
  ("Why not remove access automatically?",
   "Because the account lists it reads are incomplete and occasionally wrong, and revoking the "
   "wrong access breaks somebody's day at best. The valuable and safe part is knowing; the "
   "removal is thirty seconds of somebody's time once they do."),
  ("What about services with no API?",
   "Most small businesses have several. Those are handled as manual entries reviewed on the "
   "same cadence, marked clearly as unverified, and the report says how much of the estate is "
   "in that category."),
  ("Is this the same as the subscription audit bot?",
   "They overlap deliberately. That one finds what you pay for; this one finds who can get into "
   "it. A service that appears in one and not the other is interesting in both directions."),
  ("What does it cost to run?",
   "Around a dollar a month. It polls a handful of APIs weekly. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "access-review-reporter-on-aws",
 "title": "An access review reporter on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 860,
 "desc": ("Collects who can access what, matches it against your staff list, runs a short review "
          "twice a year, and catches leavers weekly. AWS, about $1 a month."),
 "og": ("The account nobody removed belongs to somebody who left in March. Matching account "
        "lists against a staff list is a weekly query and almost nobody runs it."),
 "abstract": ("The whole system on one page -- a collector, a matcher and a reviewer -- plus the "
              "continuous leaver check that is worth more than the periodic review."),
 "lede": ("Every business past about fifteen people has accounts it does not know about: the "
          "designer who left in March whose file storage login still works, the shared account "
          "three people use, the contractor added to something in 2023. None of it is "
          "negligence; it is that nobody has ever assembled the list, because assembling it "
          "means logging into eleven admin panels. This post walks through a small system that "
          "assembles it weekly."),
 "tags": ["access review", "offboarding", "SaaS", "security", "compliance", "serverless"],
 "takeaways": [
  "One user list per service, collected weekly where an API exists and manually where it does not.",
  "Every account is matched against the current staff list, which is the whole leaver check.",
  "Each service has one named owner, and the review asks them rather than everybody.",
  "It cannot remove access. Knowing is the hard part; removing is thirty seconds.",
  "Designed on AWS for about $1 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Your services", "sub": ["user lists, by API"], "icon": "external"},
      {"title": "Staff list", "sub": ["who works here now"], "icon": "team"},
      {"title": "Service owners", "sub": ["one each, asked twice a year"], "icon": "person"}],
    "inside": [
      {"title": "Collector", "sub": ["weekly, per service,", "stored as a snapshot"], "icon": "database"},
      {"title": "Matcher", "sub": ["accounts to people,", "or to nobody"], "icon": "filter"},
      {"title": "Reviewer", "sub": ["leavers now,", "the rest twice a year"], "icon": "report"}],
    "edges": [{"from": 0, "to": 0, "label": "who has an account"},
              {"from": 1, "to": 1, "label": "who works here"},
              {"from": 2, "to": 2, "label": "keep or remove?", "up": True}],
    "note": "It never removes access. It produces a list and a person acts on it."}),
   "Three things outside the account, three pieces inside it. The matcher in the middle is the "
   "whole system: an account that matches nobody on the staff list is the finding.",
   "System: service user lists matched against the staff list",
   "Three boxes across the top sit outside the AWS account. On the left, Your services: their "
   "user lists, read by API. In the middle, Staff list: who works here now. On the right, Service "
   "owners: one per service, asked twice a year. Each connects by an arrow to the AWS account "
   "container below. Who has an account flows down into the account. The staff list feeds in who "
   "works here. A keep-or-remove question goes back out. Inside the AWS account are three "
   "components in a row. On the left, the Collector, running weekly per service and storing a "
   "snapshot. In the middle, the Matcher, mapping accounts to people or to nobody. On the right, "
   "the Reviewer, handling leavers immediately and the rest twice a year. A note at the bottom "
   "says it never removes access; it produces a list and a person acts on it."),
  ("h3", "Two different jobs"),
  ("p", "There are two things people mean by access review and they need completely different "
        "cadences. One is \"has anybody kept access they should not have\", which is a leaver "
        "question and needs to run weekly. The other is \"does everybody still need what they "
        "have\", which is a judgement question and cannot usefully be asked more than twice a "
        "year without becoming a rubber stamp."),
  ("p", "Conflating them produces the standard failure: a quarterly review where somebody "
        "approves four hundred rows in six minutes, which satisfies an auditor and catches "
        "nothing. Separating them means the automated half runs constantly and the human half is "
        "short enough to be done properly."),
  ("h3", "What runs (the inside)"),
  ("ul", [
   "<strong>The collector.</strong> Pulls the user list from each service that has an API, "
   "weekly, and stores it as a dated snapshot. Part 2 covers the services with no API, which in "
   "a small business is usually about half of them.",
   "<strong>The matcher.</strong> Maps each account to a person on the staff list, or to nobody. "
   "Part 3 is about why that matching is harder than it sounds and what to do about shared "
   "accounts.",
   "<strong>The reviewer.</strong> Two outputs on two cadences: an immediate leaver report, and a "
   "twice-yearly review where each owner sees only their own service. Parts 4 and 5.",
  ]),
  ("h2", "One account, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Collected", "sub": ["weekly, per service"], "icon": "database"},
      {"title": "Matched", "sub": ["to a person, or not"], "icon": "filter"},
      {"title": "No match", "sub": ["they left in March"], "icon": "alarm"},
      {"title": "Reported", "sub": ["to the service owner"], "icon": "email"},
      {"title": "Removed", "sub": ["by a person, in the service"], "icon": "person"}],
    "title": "ONE STALE ACCOUNT, END TO END",
    "note": "Steps one to four are a weekly query. Step five is thirty seconds nobody had prompted."}),
   "The same system as one line. Everything except the last step is automatic, and the last step "
   "is trivial once somebody knows to do it.",
   "One stale account from collection to removal, in five stages",
   "A horizontal row of five boxes joined by arrows. Collected: weekly, per service. Matched: to "
   "a person, or not. No match: they left in March. Reported: to the service owner. Removed: by a "
   "person, in the service itself. A note says steps one to four are a weekly query and step five "
   "is thirty seconds nobody had prompted."),
  ("h2", "In plain words"),
  ("p", "A business of about thirty people pays for fourteen services. Nine have an API that will "
        "list users; five do not. The first collection produces two hundred and eleven accounts "
        "across the nine, which is already more than anybody expected for thirty people."),
  ("p", "Matching against the staff list, one hundred and seventy-two belong to current staff, "
        "twenty-two are shared or service accounts, and seventeen match nobody. Of those "
        "seventeen: eight are former employees, four are contractors whose engagement ended, "
        "three are test accounts somebody created, and two are people who joined under one email "
        "address and now use another."),
  ("p", "That first report is the valuable one and it takes an afternoon to work through. After "
        "that the weekly run finds one or two a month &mdash; usually somebody who left last week "
        "and whose file storage was missed &mdash; and each takes about a minute. The twice-yearly "
        "review is a separate, much shorter conversation about whether current staff still need "
        "what they have."),
  ("callout", "Design rules that shaped every decision", [
   "Leavers weekly, entitlements twice a year. They are different questions with different "
   "cadences.",
   "One owner per service, and the review asks only them about only their service.",
   "It never removes access. An incomplete account list is a bad basis for revocation.",
   "Services with no API are tracked as unverified and counted, rather than left out.",
   "A shared account is a finding in itself and is never matched to a person.",
   "Every snapshot is kept, so \"who had access on this date\" is answerable.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Access review is a compliance exercise in most businesses and a genuinely useful control "
        "in very few, and the difference is entirely whether the list is real. A review that asks "
        "somebody to approve a list assembled by hand six weeks ago is theatre; a review of a "
        "list collected on Monday is a control."),
  ("p", "So this design spends almost everything on collection and matching, and almost nothing "
        "on the review workflow. There is no approval chain, no evidence pack and no attestation "
        "record beyond who answered what and when &mdash; because the auditor's question and the "
        "security question have the same answer, and only one of them requires ceremony."),
  ("p", "The next four posts walk through each piece: how the lists are collected, how accounts "
        "are matched to people, how the twice-yearly review runs, and how leavers are caught. One "
        "diagram per post, a cost breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-access-lists-get-collected",
 "title": "How access lists get collected",
 "nav": "How lists are collected",
 "read": 5, "words": 750,
 "desc": ("Reading user lists from the services that offer one, handling the half that do not, "
          "and the credential problem that makes this awkward."),
 "og": ("Half the services a small business uses cannot list their users programmatically. "
        "Pretending otherwise is how an access review covers sixty per cent of the estate and "
        "claims to cover all of it."),
 "abstract": ("Reading user lists where an API exists, handling the roughly half that do not "
              "offer one, the credential problem that makes this awkward, and why unverified "
              "services are counted rather than omitted."),
 "lede": ("The uncomfortable fact at the centre of this system is that a substantial fraction of "
          "the services a small business uses will not tell you who has access, and the ones "
          "that will require an admin credential to ask. Both are manageable and neither should "
          "be glossed over."),
 "tags": ["access review", "SaaS APIs", "credentials", "least privilege", "coverage",
          "serverless"],
 "takeaways": [
  "Three tiers: an API, an export somebody drops in, and a manual list.",
  "Each service's credential is read-only where the service supports it, and separate always.",
  "A manual entry is marked unverified, dated, and counted in the coverage figure.",
  "Coverage is reported as a percentage of spend, not of services.",
  "Every collection is a dated snapshot, never an overwrite.",
 ],
 "blocks": [
  ("h2", "Three tiers"),
  ("fig", ("lanes", {
    "routes": [
      {"title": "API", "sub": ["weekly, automatic"], "icon": "link", "label": "verified"},
      {"title": "Export", "sub": ["a CSV somebody drops"], "icon": "bucket", "label": "verified"},
      {"title": "Manual list", "sub": ["typed, and dated"], "icon": "form", "label": "unverified"}],
    "target": {"title": "One account list", "sub": ["per service,", "with a tier"],
               "icon": "database",
               "then": {"title": "Matcher", "sub": ["against the staff list"], "icon": "filter"}},
    "note": "The tier travels with the data. A report that mixes them without saying so is lying."}),
   "The three ways a user list arrives and the tier that travels with it. Keeping the "
   "distinction visible is what stops the review claiming more assurance than it has.",
   "Three tiers of access list collection converging on one account list",
   "Three boxes stacked on the left. API: collected weekly and automatically, labelled verified. "
   "Export: a CSV somebody drops into a folder, also labelled verified. Manual list: typed and "
   "dated, labelled unverified. All three converge on One account list per service, carrying its "
   "tier. Below it, connected by a downward arrow, is the Matcher, which works against the staff "
   "list. A note says the tier travels with the data, and a report that mixes them without saying "
   "so is lying."),
  ("h3", "The export tier"),
  ("p", "Between a full API and nothing there is a large middle: services whose admin panel has a "
        "download-users button but no programmatic access. Those are worth treating as verified "
        "rather than manual, because the list is machine-generated and complete &mdash; it just "
        "needs a person to press a button."),
  ("p", "The practical handling is a monthly reminder to whoever owns that service, with a folder "
        "to drop the CSV into and a note of how old the current one is. An export that is four "
        "months old is reported as such, which is honest and also tends to produce a fresh one."),
  ("h2", "The credential problem"),
  ("fig", ("chain", {
    "entry": {"title": "A service with an API", "sub": ["that lists users"], "icon": "external"},
    "steps": [
      {"title": "Read-only scope?", "sub": ["for user listing"], "icon": "branch",
       "exit": {"title": "Admin credential needed", "sub": ["record that it is"], "icon": "alarm",
                "label": "no"}},
      {"title": "Own credential", "sub": ["not a person's login"], "icon": "key",
       "side": {"title": "Secrets Manager", "sub": ["one secret each"], "icon": "lock"}},
      {"title": "Fetch the list", "sub": ["weekly"], "icon": "database"},
      {"title": "Store a snapshot", "sub": ["dated, never overwritten"], "icon": "log"},
      {"title": "Compare to last week", "sub": ["additions and removals"], "icon": "filter"}],
    "note": "Several services only expose user lists to a full admin credential. Note which."}),
   "How one service's list is collected. The credential scope is worth recording per service, "
   "because an access review tool holding several admin credentials is itself an access concern.",
   "How a service's user list is collected weekly",
   "A vertical chain of five steps entered by a box labelled A service with an API that lists "
   "users. Step one asks whether a read-only scope exists for user listing; if not it exits to "
   "Admin credential needed and records that fact. Step two uses the system's own credential "
   "rather than a person's login, stored as one secret each in Secrets Manager. Step three "
   "fetches the list weekly. Step four stores a dated snapshot that is never overwritten. Step "
   "five compares against last week for additions and removals. A note says several services only "
   "expose user lists to a full admin credential, and it is worth noting which."),
  ("p", "The irony is worth naming: a system built to review access frequently needs elevated "
        "access to several services in order to do it. That is unavoidable for the services that "
        "offer no read-only scope, and the honest response is to record which services those are "
        "and to keep each credential in its own secret with its own rotation, rather than one "
        "credential that can read everything."),
  ("p", "It is also a reason the system has no write path anywhere. A tool holding admin "
        "credentials to eleven services and able to modify access would be a genuinely attractive "
        "target; one that can only list is much less so."),
  ("h2", "Coverage, honestly"),
  ("fig", ("strip", {
    "stages": [
      {"title": "14 services", "sub": ["that people log into"], "icon": "external"},
      {"title": "9 by API", "sub": ["weekly, verified"], "icon": "check"},
      {"title": "2 by export", "sub": ["monthly, verified"], "icon": "bucket"},
      {"title": "3 manual", "sub": ["unverified"], "icon": "form"},
      {"title": "Coverage", "sub": ["94% of spend, 79% of services"], "icon": "chart"}],
    "title": "COVERAGE, REPORTED TWO WAYS",
    "note": "Percentage of spend is the honest number. Percentage of services flatters."}),
   "How coverage is reported. Both percentages are true and they differ substantially, which is "
   "why the report carries the less flattering one first.",
   "How access review coverage is reported across fourteen services",
   "A horizontal row of five boxes. Fourteen services that people log into. Nine by API: weekly "
   "and verified. Two by export: monthly and verified. Three manual: unverified. Coverage: "
   "ninety-four per cent of spend and seventy-nine per cent of services. A note says percentage "
   "of spend is the honest number and percentage of services flatters."),
  ("p", "Those two numbers usually differ a lot, because the services with good APIs tend to be "
        "the larger, more expensive ones and the manual ones tend to be small tools. Reporting "
        "only the spend figure would flatter; reporting only the service count would understate "
        "how much of the important estate is covered."),
  ("p", "Reporting both, with the service count first, is the version that keeps somebody honest "
        "about the three services nobody can verify."),
  ("p", "Next: matching accounts to people."),
 ],
},
{
 "slug": "how-an-account-gets-matched-to-a-person",
 "title": "How an account gets matched to a person",
 "nav": "How matching works",
 "read": 5, "words": 750,
 "desc": ("Matching on more than an email address, the four kinds of account that match nobody, "
          "and why a shared account is a finding rather than a problem to solve."),
 "og": ("Email matching alone misses the person who changed their name and finds a false "
        "positive in every shared mailbox. Four kinds of unmatched account, and only two are "
        "problems."),
 "abstract": ("Why email matching alone is not enough, the four kinds of account that match "
              "nobody, and why a shared account is a finding to record rather than a problem to "
              "resolve."),
 "lede": ("Matching an account to a person looks like a join on email address and is not, for "
          "reasons that are individually small and collectively cover about ten per cent of "
          "accounts in any real business."),
 "tags": ["access review", "identity matching", "shared accounts", "offboarding", "data quality",
          "serverless"],
 "takeaways": [
  "Match on email, then on alias, then on name, and record which matched.",
  "Four kinds of unmatched account: leaver, contractor, shared, and service.",
  "Only the first two are problems. The other two are findings to record and watch.",
  "A shared account is never matched to a person, however obvious it seems.",
  "A person with two accounts on one service is worth reporting as its own case.",
 ],
 "blocks": [
  ("h2", "Three ways to match"),
  ("fig", ("chain", {
    "entry": {"title": "An account", "sub": ["email and display name"], "icon": "person"},
    "steps": [
      {"title": "Email on the staff list?", "sub": ["exact"], "icon": "branch",
       "side": {"title": "Staff list", "sub": ["current and past"], "icon": "team"},
       "exit": {"title": "Matched", "sub": ["the usual case"], "icon": "check", "label": "yes"}},
      {"title": "A known alias?", "sub": ["former address, or a second"], "icon": "branch",
       "exit": {"title": "Matched", "sub": ["record the alias"], "icon": "link", "label": "yes"}},
      {"title": "Name matches one person?", "sub": ["exactly one"], "icon": "branch",
       "exit": {"title": "Probably matched", "sub": ["flag for confirmation"], "icon": "search",
                "label": "one"}},
      {"title": "Looks shared or service?", "sub": ["by pattern"], "icon": "branch",
       "exit": {"title": "Record as shared", "sub": ["never as a person"], "icon": "lock",
                "label": "yes"}},
      {"title": "Matches nobody", "sub": ["the finding"], "icon": "alarm"}],
    "note": "A name match is provisional. Two people called J Smith is not a match at all."}),
   "How an account finds its person. The name-match tier is deliberately provisional, because "
   "confidently matching the wrong person is worse than reporting an unmatched account.",
   "How a service account is matched to a person on the staff list",
   "A vertical chain of five steps entered by a box labelled An account, carrying an email and a "
   "display name. Step one asks whether the email is on the staff list, exactly, checking both "
   "current and past staff; a hit exits to Matched, the usual case. Step two asks whether it is a "
   "known alias such as a former or second address; a hit exits to Matched and records the alias. "
   "Step three asks whether the name matches exactly one person; one match exits to Probably "
   "matched, flagged for confirmation. Step four asks whether it looks like a shared or service "
   "account by pattern; if so it exits to Record as shared, never as a person. Step five is "
   "Matches nobody, which is the finding. A note says a name match is provisional and two people "
   "called J Smith is not a match at all."),
  ("h3", "Aliases"),
  ("p", "People change email addresses more often than systems expect: a name change, a domain "
        "migration, a move from a personal address used during a trial to a work one. The account "
        "created under the old address frequently survives, and matching on the current address "
        "alone reports it as unmatched every week forever."),
  ("p", "So the staff list carries known former addresses, and a match against one records the "
        "alias on the account. That both silences the false finding and produces something "
        "genuinely useful: a list of accounts still using an address that no longer routes, which "
        "is a password-reset problem waiting to happen."),
  ("h2", "Four kinds of unmatched"),
  ("table", ["Kind", "Looks like", "What it means"], [
   ["Leaver", "Matches somebody on the past-staff list", "Remove it; this is the finding"],
   ["Contractor", "A domain that is not yours, still active", "Check whether the engagement ended"],
   ["Shared", "info@, accounts@, a team name", "Record it; a different conversation"],
   ["Service", "An API key, a bot, an integration", "Record it and attach an owner"],
  ]),
  ("p", "Only the first two are problems in the ordinary sense. The other two are legitimate, "
        "common, and worth having written down &mdash; a shared mailbox nobody owns and a service "
        "account nobody remembers creating are both real risks, and both need a conversation "
        "rather than a removal."),
  ("h3", "Shared accounts are never matched"),
  ("p", "The temptation with <code>accounts@</code> is to match it to whoever mostly uses it, "
        "which makes the report tidier and destroys the finding. A shared account by definition "
        "has no individual accountable for it, and that is the thing worth recording."),
  ("p", "So shared accounts get their own category, an owner is attached to the category rather "
        "than to the login, and the twice-yearly review asks a specific question about each: is "
        "this still needed, and could it be individual accounts instead. That question produces a "
        "genuine improvement about a third of the time and never gets asked without something "
        "prompting it."),
  ("h2", "Two accounts, one person"),
  ("fig", ("strip", {
    "stages": [
      {"title": "j.reed@", "sub": ["active, current"], "icon": "person"},
      {"title": "jreed@", "sub": ["also active"], "icon": "search"},
      {"title": "Same person", "sub": ["by alias"], "icon": "link"},
      {"title": "Two logins", "sub": ["one is unused"], "icon": "counter"},
      {"title": "Reported", "sub": ["as duplication, not a leaver"], "icon": "report"}],
    "title": "ONE PERSON, TWO ACCOUNTS",
    "note": "Common after a migration, and each unused login is a credential nobody rotates."}),
   "The duplication case. It is not a leaver and not shared, and it produces a live credential "
   "attached to nobody's attention.",
   "How a person holding two accounts on one service is reported",
   "A horizontal row of five boxes. The address j dot reed at: active and current. The address "
   "jreed at: also active. Same person: matched by alias. Two logins: one of which is unused. "
   "Reported: as duplication rather than as a leaver. A note says this is common after a "
   "migration, and each unused login is a credential nobody rotates."),
  ("p", "This case is worth its own reporting line because it is invisible to both the leaver "
        "check and the entitlement review: the person works here and legitimately needs access, "
        "so nothing is wrong except that there are two credentials where there should be one, and "
        "one of them has not been used in eight months."),
  ("p", "Next: the twice-yearly review."),
 ],
},
{
 "slug": "how-a-review-round-runs",
 "title": "How a review round runs",
 "nav": "How a round runs",
 "read": 5, "words": 740,
 "desc": ("One owner, one service, one short list, and the design choices that stop a review "
          "becoming a rubber stamp."),
 "og": ("A review that asks one person to approve four hundred rows produces four hundred "
        "approvals in six minutes. One owner, one service, twelve rows is a different exercise."),
 "abstract": ("Why the review is per service rather than per person, what an owner actually sees, "
              "the defaults that stop it becoming a rubber stamp, and what happens to no reply."),
 "lede": ("Access reviews fail in a completely predictable way: somebody is shown a long list, "
          "approves all of it, and a control is recorded as having happened. Everything in this "
          "post is about the difference between that and a review that changes something."),
 "tags": ["access review", "governance", "compliance", "reviews", "operations", "serverless"],
 "takeaways": [
  "One owner reviews one service, not one manager reviewing one person's everything.",
  "The default is keep, and removing is one tap. The reverse produces panicked mass-approval.",
  "Last-used dates are shown, because they are what actually informs the decision.",
  "No reply is recorded as no reply, not as approval.",
  "Twice a year. Quarterly produces the rubber stamp and annual is too slow for a leaver.",
 ],
 "blocks": [
  ("h2", "Per service, not per person"),
  ("p", "The two ways to slice a review are by person &mdash; here is everything Jo can access "
        "&mdash; and by service &mdash; here is everyone who can access the file storage. Both "
        "are defensible and the second works much better in a small business."),
  ("p", "Per person requires a manager to have an opinion about eleven services they may not use "
        "themselves. Per service asks one person who genuinely understands that service about a "
        "list of names they recognise, which is a question somebody can answer well in two "
        "minutes."),
  ("fig", ("chain", {
    "entry": {"title": "Review round opens", "sub": ["twice a year"], "icon": "calendar"},
    "steps": [
      {"title": "One message per service", "sub": ["to its owner only"], "icon": "email",
       "side": {"title": "Service owners", "sub": ["one each, named"], "icon": "team"}},
      {"title": "The list", "sub": ["names, roles, last used"], "icon": "doc"},
      {"title": "Default is keep", "sub": ["removing is the action"], "icon": "check"},
      {"title": "Any removals?", "icon": "branch",
       "exit": {"title": "A task, to them", "sub": ["with a link to the admin page"],
                "icon": "person", "label": "yes"}},
      {"title": "Recorded", "sub": ["who answered, when, what"], "icon": "log"}],
    "note": "Default-keep is deliberate. Default-remove produces mass approval out of fear."}),
   "How a review round is delivered. The default matters more than anything else in the design: "
   "it determines whether somebody reads the list or protects themselves from it.",
   "How a twice-yearly access review round is run",
   "A vertical chain of five steps entered by a box labelled Review round opens, twice a year. "
   "Step one sends one message per service, to its named owner only. Step two shows the list of "
   "names, roles and last-used dates. Step three sets the default to keep, so removing is the "
   "action. Step four asks whether there are any removals; if so it exits to A task assigned to "
   "them, with a link to the service's admin page. Step five records who answered, when and what. "
   "A note says default-keep is deliberate, because default-remove produces mass approval out of "
   "fear."),
  ("h3", "Why default-keep"),
  ("p", "A review where inaction removes access sounds more rigorous and produces worse outcomes. "
        "Owners who are busy will approve everything rather than risk breaking somebody's access, "
        "and the review becomes a formality with higher stakes."),
  ("p", "With default-keep, doing nothing is honest &mdash; it is recorded as no reply rather "
        "than as approval &mdash; and the only action available is the one that requires a "
        "positive decision. In practice that produces more removals, not fewer, because the "
        "owner is looking for candidates rather than defending a list."),
  ("h3", "Last-used dates"),
  ("p", "The single most useful column and the one many services do not expose. Where it is "
        "available, an account that has not been used in five months answers the review question "
        "on its own; where it is not, the owner is deciding from memory."),
  ("p", "So the collector captures it wherever the API offers it, and the review sorts by it "
        "descending so the least-used accounts are at the top of the list. That ordering alone "
        "changes the outcome of a review measurably."),
  ("h2", "What no reply means"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Sent", "sub": ["to the owner"], "icon": "email"},
      {"title": "Reminder", "sub": ["at 7 days"], "icon": "bell"},
      {"title": "Their manager", "sub": ["at 14 days"], "icon": "team"},
      {"title": "Recorded as no reply", "sub": ["never as approved"], "icon": "log"},
      {"title": "In the summary", "sub": ["'3 of 14 not reviewed'"], "icon": "report"}],
    "title": "SILENCE IS NOT APPROVAL",
    "note": "A review record that counts silence as approval is worse than no record."}),
   "How an unanswered review is handled. Recording silence honestly is what keeps the review "
   "record worth anything.",
   "How an unanswered access review is escalated and recorded",
   "A horizontal row of five boxes. Sent: to the owner. Reminder: at seven days. Their manager: "
   "at fourteen days. Recorded as no reply: never as approved. In the summary: three of fourteen "
   "not reviewed. A note says a review record that counts silence as approval is worse than no "
   "record."),
  ("p", "This is the one place where an access review system can quietly become dishonest, and it "
        "happens by accident: a schema with an <code>approved</code> boolean defaulting to false "
        "gets reported as \"11 approved, 3 pending\" and then, next quarter, as \"14 reviewed\". "
        "A three-state field &mdash; reviewed, removals requested, no reply &mdash; makes that "
        "impossible."),
  ("h3", "Twice a year"),
  ("p", "Quarterly is the common recommendation and it produces the rubber stamp: four rounds a "
        "year of the same list generates fatigue quickly, and the second round is already being "
        "approved without reading. Annual is too slow to be the only control, but it is not the "
        "only control here &mdash; the leaver check runs weekly and catches the urgent case."),
  ("p", "Twice a year is short enough to remember what the service is for and long enough that "
        "the list has genuinely changed since last time, which is what makes reading it worth "
        "doing."),
  ("p", "Next: the weekly leaver check, which is where most of the value is."),
 ],
},
{
 "slug": "how-leavers-get-caught",
 "title": "How leavers get caught",
 "nav": "How leavers are caught",
 "read": 5, "words": 730,
 "desc": ("The weekly check that finds the account nobody removed, the offboarding list it "
          "produces, and the one number worth watching."),
 "og": ("The leaver check is a join between two lists and it is worth more than the entire "
        "twice-yearly review. It runs weekly and takes nobody's time."),
 "abstract": ("The weekly join that finds accounts belonging to people who have left, the "
              "offboarding checklist it produces on day one, and the single number worth "
              "watching over time."),
 "lede": ("Everything in the previous three posts is groundwork for a query that takes about "
          "eleven lines: which accounts belong to people who are not on the staff list any more. "
          "It is worth more than the entire twice-yearly review and it costs nobody any time at "
          "all."),
 "tags": ["access review", "offboarding", "leavers", "security", "reporting", "serverless"],
 "takeaways": [
  "The check is a weekly join between the account snapshots and the staff list.",
  "A leaver produces one message listing every service they still have access to.",
  "The same list is produced proactively on somebody's last day, as a checklist.",
  "Days-to-removal is the number worth watching, and it should trend towards zero.",
  "A service that never appears on a leaver list is probably not being collected at all.",
 ],
 "blocks": [
  ("h2", "The weekly join"),
  ("fig", ("chain", {
    "entry": {"title": "This week's snapshots", "sub": ["every service"], "icon": "database"},
    "steps": [
      {"title": "Match each account", "sub": ["against current staff"], "icon": "filter",
       "side": {"title": "Staff list", "sub": ["current, and leavers", "with dates"], "icon": "team"}},
      {"title": "On the leaver list?", "sub": ["with a leaving date"], "icon": "branch",
       "exit": {"title": "Still has access", "sub": ["the finding"], "icon": "alarm",
                "label": "yes"}},
      {"title": "Matches nobody at all?", "sub": ["not even a leaver"], "icon": "branch",
       "exit": {"title": "Unknown account", "sub": ["ask the owner"], "icon": "search",
                "label": "yes"}},
      {"title": "Group by person", "sub": ["one message, all services"], "icon": "counter"},
      {"title": "Send with the dates", "sub": ["left when, still in what"], "icon": "email"}],
    "note": "Grouping by person is what makes it one task rather than six separate ones."}),
   "The weekly leaver check. Grouping by person rather than by service is what turns six findings "
   "into one afternoon's task with a clear owner.",
   "How the weekly leaver check finds accounts that should have been removed",
   "A vertical chain of five steps entered by a box labelled This week's snapshots, from every "
   "service. Step one matches each account against current staff, using a staff list that holds "
   "both current people and leavers with their dates. Step two asks whether the person is on the "
   "leaver list with a leaving date; if so it exits to Still has access, which is the finding. "
   "Step three asks whether the account matches nobody at all, not even a leaver; if so it exits "
   "to Unknown account and asks the owner. Step four groups by person so one message covers all "
   "services. Step five sends it with the dates: when they left and what they are still in. A "
   "note says grouping by person is what makes it one task rather than six separate ones."),
  ("h3", "One message per person"),
  ("p", "A leaver with access to six services is one problem, not six. Six separate findings "
        "routed to six service owners produces six small tasks with no coordination and a good "
        "chance that two of them are done and four are not."),
  ("p", "So the message goes to whoever handles offboarding, lists every service the person still "
        "has access to, and includes a link to each service's user administration page. That is a "
        "single ten-minute task with an obvious completion condition, which is a far better shape "
        "than six two-minute ones."),
  ("h2", "The proactive checklist"),
  ("p", "The same query, run in the other direction, produces something more useful than any "
        "detection: a list of everything a specific person has access to, generated on the day "
        "they hand in their notice."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Notice given", "sub": ["a leaving date"], "icon": "calendar"},
      {"title": "Query their access", "sub": ["from this week's snapshots"], "icon": "search"},
      {"title": "A checklist", "sub": ["9 services, with links"], "icon": "doc"},
      {"title": "Last day", "sub": ["worked through"], "icon": "check"},
      {"title": "Verified next week", "sub": ["the collector confirms"], "icon": "retry"}],
    "title": "THE SAME QUERY, USED FORWARDS",
    "note": "Detection is the backstop. The checklist is what stops there being anything to detect."}),
   "The same data used proactively. The checklist prevents the finding; the weekly check exists "
   "to catch what the checklist missed.",
   "How the access data produces an offboarding checklist",
   "A horizontal row of five boxes. Notice given: with a leaving date. Query their access: from "
   "this week's snapshots. A checklist: nine services, each with a link. Last day: worked "
   "through. Verified next week: the collector confirms. A note says detection is the backstop "
   "and the checklist is what stops there being anything to detect."),
  ("p", "The verification step is what makes the checklist trustworthy. Somebody ticking nine "
        "boxes on a Friday afternoon is not evidence that nine accounts were removed; next "
        "Monday's collection is. A checklist item ticked but still showing in the following "
        "week's snapshot is reported specifically, and it is usually a service where removal "
        "requires a step somebody did not realise."),
  ("h2", "The number to watch"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Leavers", "sub": ["4 this quarter"], "icon": "team"},
      {"title": "Accounts", "sub": ["31 between them"], "icon": "counter"},
      {"title": "Removed on the day", "sub": ["26"], "icon": "check"},
      {"title": "Median days", "sub": ["0"], "icon": "clock"},
      {"title": "Worst case", "sub": ["11 days, one service"], "icon": "alarm"}],
    "title": "ONE QUARTER OF OFFBOARDING",
    "note": "The last two numbers matter. A median of zero with a worst case of 11 names a service."}),
   "A quarter of offboarding in five numbers. The gap between the median and the worst case is "
   "what identifies the specific service that keeps being missed.",
   "One quarter of offboarding summarised in five numbers",
   "A horizontal row of five boxes. Leavers: four this quarter. Accounts: thirty-one between "
   "them. Removed on the day: twenty-six. Median days to removal: zero. Worst case: eleven days, "
   "on one service. A note says the last two numbers matter, and a median of zero with a worst "
   "case of eleven names a service."),
  ("p", "Median days to removal is the headline and it should be zero in a business with a working "
        "checklist. The worst case is the more useful number, because it is almost always the same "
        "service every quarter &mdash; the one whose admin panel is awkward, or whose owner is "
        "part-time, or which nobody remembers is a service at all."),
  ("h3", "The service that never appears"),
  ("p", "One quiet finding worth mentioning: a service that has never once appeared on a leaver "
        "list, across several quarters, in a business with turnover. That usually means its "
        "collection is broken rather than that its offboarding is perfect, and it is worth "
        "checking specifically because a silently broken collector is indistinguishable from a "
        "well-run service."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="collection",
 volumes=[(40, "40 collections"), (120, "12 services weekly"), (400, "40 services weekly")],
 read_each=0.0,
 msgs_each=0.6,
 lede=("This polls a handful of APIs once a week and does a join. Forty collections is about ten "
       "services checked weekly. It is one of the cheapest systems in the series and one of the "
       "few whose value is measured in things that did not happen. Here is where each cent goes."),
 takeaway_extra=("No model, and the APIs are free. Storage grows with retained snapshots, which "
                 "is the only line that moves."),
 risks=[
  "<strong>Storing a full snapshot per service per week forever.</strong> Small, but it "
  "compounds, and snapshots older than about two years answer no question anybody asks. Expire "
  "them deliberately.",
  "<strong>Polling on a schedule that hits rate limits.</strong> Several SaaS user APIs are "
  "aggressively rate limited. Collect services sequentially with a delay rather than in parallel; "
  "there is no hurry.",
  "<strong>Log retention left at never.</strong> With a bill this small, unbounded logs will be "
  "the whole of it within months.",
 ],
 per_unit_note=("There is no read line: nothing here calls a model. The variable cost is a "
                "handful of API calls and the storage of weekly snapshots."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="ar",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the credential handling, and the write permissions it deliberately lacks."),
 outside=[
  {"title": "Service APIs", "sub": ["user lists, read-only"], "icon": "external"},
  {"title": "Staff list", "sub": ["Sheets API, read-only"], "icon": "team"},
  {"title": "SES outbound", "sub": ["leavers, review rounds"], "icon": "email"}],
 inside=[
  {"title": "EventBridge", "sub": ["weekly collect,", "twice-yearly review"], "icon": "clock"},
  {"title": "Lambda x3", "sub": ["collect, match, review"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["accounts, reviews"], "icon": "database"}],
 note="us-east-1. One account. No write permission to any reviewed service, ever.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Service APIs, providing user lists "
  "read-only. The Staff list, read through the Google Sheets API read-only. And SES outbound, "
  "carrying leaver findings and review rounds. Inside the account, three groups. EventBridge "
  "carrying a weekly collection schedule and a twice-yearly review schedule. Three Lambda "
  "functions named collect, match and review. And two DynamoDB tables named accounts and reviews. "
  "A note gives the region as us-east-1, one account, and states there is no write permission to "
  "any reviewed service, ever."),
 functions=[
  ["<code>ar-collect</code>", "EventBridge weekly",
   "One service at a time, with a delay; stores a dated snapshot", "300s / 512&nbsp;MB"],
  ["<code>ar-match</code>", "SQS snapshot queue",
   "Email, alias and name matching; classifies unmatched accounts", "30s / 512&nbsp;MB"],
  ["<code>ar-review</code>", "EventBridge weekly + twice-yearly + Function URL",
   "Leaver report, review rounds, and the signed response links", "30s / 512&nbsp;MB"]],
 roles=[
  ["<code>ar-collect-role</code>",
   "<code>secretsmanager:GetSecretValue</code>, <code>dynamodb:PutItem</code>",
   "One secret per service, named individually; the accounts table"],
  ["<code>ar-match-role</code>",
   "<code>dynamodb:UpdateItem</code>, <code>secretsmanager:GetSecretValue</code>",
   "Accounts; the staff-list credential only"],
  ["<code>ar-review-role</code>", "<code>dynamodb:Query</code>, <code>ses:SendEmail</code>",
   "Accounts and reviews; one verified identity"]],
 tables=[
  ("Table: accounts",
   "PK   service           S   filestore\n"
   "SK   account_id        S   the service's own identifier\n"
   "     email             S   as the service holds it\n"
   "     display_name      S   as the service holds it\n"
   "     last_used         S   where the API exposes it -- the useful column\n"
   "     matched_person    S   or null\n"
   "     match_method      S   email | alias | name | none\n"
   "     unmatched_kind    S   leaver | contractor | shared | service | unknown\n"
   "     first_seen        S   2026-02-14\n"
   "     last_seen         S   2026-08-04   -- absence is how removal is confirmed\n"
   "     tier              S   api | export | manual\n\n"
   "`last_seen` not updating is how a removal is verified. A checklist tick is\n"
   "a claim; a missing account in next week's snapshot is evidence."),
  ("Table: reviews",
   "PK   round             S   2026-H2\n"
   "SK   service           S   filestore\n"
   "     owner             S   the person asked\n"
   "     sent_at           S   2026-08-04\n"
   "     state             S   reviewed | removals_requested | no_reply\n"
   "     answered_at       S   or null\n"
   "     removals          L   [{account_id, requested_by, done_at}]\n\n"
   "Three states, never a boolean. An `approved` boolean defaulting to false is\n"
   "how a review record starts counting silence as approval.")],
 inbound=[
  "<strong>One secret per service</strong>, named individually in the IAM policy. A single "
  "credential that can read every service's user list would make this system a more attractive "
  "target than any service it reviews.",
  "<strong>Read-only scopes wherever offered</strong>, and a recorded note where a service only "
  "exposes user listing to a full admin credential.",
  "<strong>Sequential collection with a delay.</strong> Several SaaS user APIs rate limit "
  "aggressively, and there is no reason to hurry a weekly job.",
  "<strong>No write permission to any reviewed service.</strong> Not disabled, not commented out "
  "&mdash; absent from the credential scope, so it cannot be added by changing code."],
 model_notes=[
  "<strong>There is no model in this system.</strong> Matching is exact comparison, alias lookup "
  "and an exact-name check.",
  "<strong>Fuzzy name matching is deliberately avoided.</strong> A close-but-wrong match attaches "
  "an account to the wrong person, which is worse than reporting it unmatched.",
  "<strong>Classifying an unmatched account</strong> as shared or service uses a pattern list you "
  "maintain, not a judgement, so the classification is stable between runs.",
  "<strong>If a model were used anywhere</strong> it would be to suggest a classification for a "
  "new unmatched account, and a person confirming it is faster than reading a model's reasoning.",
  "<strong>The cost page assumes none</strong>, which is why there is no read band."],
 gotchas=[
  "Split leavers from entitlements. They are different questions on different cadences, and "
  "conflating them produces a quarterly rubber stamp that catches nothing.",
  "Default to keep in the review. Default-remove makes busy owners approve everything to avoid "
  "breaking somebody's access.",
  "Use three states, never an approved boolean. Silence must never be recordable as approval.",
  "Verify removals from the next snapshot. A ticked checklist is a claim; an absent account is "
  "evidence.",
  "Watch for a service that never appears on a leaver list. That is usually a broken collector "
  "rather than perfect offboarding."],
))
