"""Day 82 -- 2026-07-15 -- Tax rate updater."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from awsbuild.common import cost_part, reference_part

SLUG = "tax-rate-updater"
NAME = "Tax rate updater"

SPEC = {
 "slug": SLUG, "date": "2026-07-15", "name": NAME,
 "tagline": ("Watches the official sources for the tax rates and thresholds your systems have "
             "hard-coded, and tells a person before the change lands rather than after the "
             "first wrong invoice."),
 "lede": ("A small system that keeps a register of every tax rate and threshold your business "
          "has written down somewhere -- in a price list, a spreadsheet, a config file -- "
          "watches the official publications for changes to them, and puts a dated change in "
          "front of a person with the list of places that need editing. It never edits "
          "anything. Seven posts on the same system -- one diagram at a time -- with a cost "
          "breakdown and an engineering reference at the end."),
 "keywords": ["tax rates", "VAT", "compliance", "change management", "human in the loop",
              "serverless"],
 "icons": ["doc", "search", "alarm"],
 "faq": [
  ("What is a tax rate updater?",
   "A small serverless system that keeps a register of the tax rates and thresholds your "
   "business relies on, watches the official sources that publish them, and tells a person "
   "when one changes -- with the effective date and the list of places in your business that "
   "hold that number. It never edits anything itself."),
  ("Why not just use a tax API?",
   "For calculating tax on a transaction, you should. This solves a different problem: the "
   "rates that are not in any API because they are typed into a price list, a quoting "
   "spreadsheet, a printed rate card and a config file. Those are the ones that go stale, and "
   "no API knows they exist."),
  ("Does it change any of my systems?",
   "No, deliberately. It produces a dated change notice and a checklist of the places the "
   "number appears. Editing a live price list is a business decision with pricing and contract "
   "consequences, and it belongs to a person."),
  ("How does it know where a rate is used?",
   "You tell it, once, in a register. Each entry is a rate, the official source that publishes "
   "it, and the list of places in your business that hold a copy. Building that register is "
   "the real work and it is worth doing even without any code."),
  ("What does it cost to run?",
   "A couple of dollars a month. It checks a handful of sources on a schedule and almost never "
   "finds anything. See part six."),
 ],
}

SPEC["parts"] = [
{
 "slug": "tax-rate-updater-on-aws",
 "title": "A tax rate updater on AWS for a few dollars a month",
 "nav": "The whole system",
 "read": 6, "words": 920,
 "desc": ("Keeps a register of the tax rates your business has hard-coded, watches the "
          "official sources, and tells a person before a change lands. AWS, about $2 a month."),
 "og": ("A register of every rate you have written down, a watcher on the official sources, "
        "and a dated change notice listing exactly which of your systems holds that number."),
 "abstract": ("The whole system on one page -- a register, a watcher and a notifier -- and the "
              "insight it is built on: the dangerous rates are the ones no API knows you have."),
 "lede": ("Every business has tax numbers written down in places nobody remembers. A VAT rate "
          "in a quoting spreadsheet. A mileage rate in a claim form. A registration threshold "
          "in somebody's head. A duty rate typed into a shipping template in 2021. None of "
          "them are in a system that gets updated, and all of them are wrong the moment the "
          "government changes something. The first anyone finds out is an invoice a customer "
          "queries, or worse, one they do not. This post walks through a small system that "
          "keeps the list and watches the sources."),
 "tags": ["tax rates", "VAT", "compliance", "change management", "human in the loop",
          "serverless"],
 "takeaways": [
  "The register is the product. Listing where every rate lives is most of the value.",
  "It watches official publications, not aggregator sites, and records what it read.",
  "A change produces a dated notice with a checklist, not an edit.",
  "It watches for the change being announced, not for it taking effect. Those are months apart.",
  "Designed on AWS for about $2 a month.",
 ],
 "blocks": [
  ("h2", "The whole system on one page"),
  ("p", "Before any code, here is the shape of what we are designing."),
  ("fig", ("system", {
    "outside": [
      {"title": "Official sources", "sub": ["publications, feeds"], "icon": "external"},
      {"title": "Rate register", "sub": ["what you use, where"], "icon": "doc"},
      {"title": "Whoever owns it", "sub": ["gets a dated checklist"], "icon": "person"}],
    "inside": [
      {"title": "Watcher", "sub": ["fetch, compare,", "record what was read"], "icon": "search"},
      {"title": "Differ", "sub": ["what changed, and", "when it takes effect"], "icon": "filter"},
      {"title": "Notifier", "sub": ["one notice per change,", "with the checklist"], "icon": "alarm"}],
    "edges": [{"from": 0, "to": 0, "label": "published pages"},
              {"from": 1, "to": 1, "label": "what to watch"},
              {"from": 2, "to": 2, "label": "change + checklist", "up": True}],
    "note": "It never edits a price list, a spreadsheet or a config file. It tells a person."}),
   "Three things outside the account, three pieces inside it. The register says what to watch "
   "and where each number lives; the watcher reads the official page; the notifier turns a "
   "difference into a dated checklist for a person.",
   "System: official sources watched against a register, notices out",
   "Three boxes across the top sit outside the AWS account. On the left, Official sources: the "
   "government publications and feeds that publish rates. In the middle, Rate register: your "
   "own list of which rates you use and where each one is written down. On the right, Whoever "
   "owns it: the person who receives a dated checklist. Each connects by an arrow to the AWS "
   "account container below. Published pages flow down into the account. The register feeds in "
   "to say what to watch. A change notice with a checklist goes back out. Inside the AWS "
   "account are three components in a row. On the left, the Watcher, which fetches each source, "
   "compares it with what was there last time, and records exactly what it read. In the middle, "
   "the Differ, which works out what changed and when it takes effect. On the right, the "
   "Notifier, which sends one notice per change with the checklist attached. A note at the "
   "bottom says it never edits a price list, a spreadsheet or a config file; it tells a person."),
  ("h3", "The register is the product"),
  ("p", "The code in this system is trivial. The register is not, and building it is a genuinely "
        "useful exercise that most businesses have never done. Each row is one rate, the source "
        "that publishes it, and every place in your business that holds a copy of it."),
  ("table", ["Column", "Example", "Why"], [
   ["Rate", "Standard VAT rate", "What it is, in plain words"],
   ["Current value", "20%", "What you believe it to be today"],
   ["Source", "The official VAT rates page", "Where the truth lives"],
   ["Effective from", "2011-01-04", "When the current value started"],
   ["Used in", "Quoting sheet, price list PDF, invoice template, Shopify tax setting",
    "The checklist. This column is the whole point."],
   ["Owner", "finance@", "Who gets the notice"],
  ]),
  ("p", "The <em>Used in</em> column is what makes this different from any tax API. An API can "
        "tell you the VAT rate. It cannot tell you that your printed rate card, your quoting "
        "spreadsheet and a hard-coded constant in your booking form all contain a copy of it "
        "and all need changing. Nobody knows that except you, and most businesses have never "
        "written it down."),
  ("h3", "What runs on every check (the inside)"),
  ("ul", [
   "<strong>The watcher.</strong> Fetches each source on a schedule, extracts the values it "
   "cares about, and stores exactly what it read along with a copy of the page. That last part "
   "matters more than it looks: when somebody asks in eighteen months why a rate was applied, "
   "the answer is a stored snapshot rather than a memory.",
   "<strong>The differ.</strong> Compares what was read against what the register says. The "
   "interesting output is not \"it changed\" &mdash; it is the effective date, because rates "
   "are almost always announced months before they apply, and the whole value of the system is "
   "in that gap.",
   "<strong>The notifier.</strong> Sends one notice per change to the owner, with the old "
   "value, the new value, the effective date, the source link, and the checklist of places from "
   "the register. Then it reminds them again shortly before the effective date, because a "
   "change announced in March for October will absolutely be forgotten by September.",
  ]),
  ("h2", "One change, end to end"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Published", "sub": ["on an official page"], "icon": "external"},
      {"title": "Noticed", "sub": ["next scheduled check"], "icon": "search"},
      {"title": "Dated", "sub": ["effective from when"], "icon": "calendar"},
      {"title": "Listed", "sub": ["the places to edit"], "icon": "log"},
      {"title": "Reminded", "sub": ["again, before it lands"], "icon": "bell"}],
    "title": "ONE RATE CHANGE, END TO END",
    "note": "The last stage is the one that actually saves you. Announcements are forgotten."}),
   "The same system as one line. The second reminder before the effective date is not a nicety "
   "&mdash; it is the step that converts an announcement into an action.",
   "One tax rate change from publication to reminder, in five stages",
   "A horizontal row of five boxes joined by arrows. Published: the change appears on an "
   "official page. Noticed: picked up by the next scheduled check. Dated: the effective date is "
   "extracted. Listed: the places in your business that hold the number are listed from the "
   "register. Reminded: a second notice goes out shortly before the change takes effect. A note "
   "says the last stage is the one that actually saves you, because announcements are "
   "forgotten."),
  ("h2", "In plain words"),
  ("p", "In March, the government publishes that a threshold you rely on will rise in the "
        "following April. The watcher's daily check picks it up within a day. The differ reads "
        "the effective date, notices it is thirteen months away, and files it. The notifier "
        "sends one message in March: what changed, from what to what, effective when, with the "
        "link, and the checklist &mdash; the quoting spreadsheet, the two paragraphs on the "
        "website, the accountant's standing instruction, and the config value in the booking "
        "form."),
  ("p", "Nobody does anything in March, which is fine and expected. In the following March, "
        "four weeks before it takes effect, the same message arrives again, marked as a "
        "reminder. Now somebody acts, because it is imminent and because the checklist means "
        "acting takes twenty minutes rather than being an open-ended research task. The "
        "alternative &mdash; and this is what actually happens without a system &mdash; is that "
        "three of the four places get updated by whoever remembered, and the fourth is "
        "discovered eight months later by a customer."),
  ("callout", "Design rules that shaped every decision", [
   "It never edits anything. A live price list carries pricing and contract consequences, and "
   "changing one is a business decision.",
   "Watch official sources only. Aggregators and news sites are faster and occasionally wrong, "
   "and being wrong about a tax rate is much worse than being late.",
   "Store what was read, not just what was extracted. A snapshot of the page is the audit "
   "trail.",
   "The effective date is the important field, not the value. Announcement and effect are "
   "usually months apart.",
   "Remind before the effective date. An announcement noticed and forgotten is the same as an "
   "announcement missed.",
   "A source that stops being readable is an alarm, not silence. The failure mode of a watcher "
   "is quietly watching nothing.",
  ]),
  ("h2", "Why this shape"),
  ("p", "Tax software solves the transaction problem: what rate applies to this sale, right now. "
        "It solves it well and this system does not try to compete with it. The problem here is "
        "different and almost entirely unaddressed &mdash; the rates that live outside any "
        "system, in documents and spreadsheets and templates, where nothing updates them and "
        "nothing knows they exist."),
  ("p", "That problem is not solvable by software alone, because the crucial information lives "
        "only in people's heads: where the numbers are. So the design puts almost all of its "
        "weight on the register, makes maintaining it cheap, and adds the only automatable "
        "part &mdash; watching the sources and remembering the dates &mdash; around it."),
  ("p", "The next four posts walk through each piece: how the register works, how a source gets "
        "read, how a change gets dated, and how the reminder works. One diagram per post, a cost "
        "breakdown, and an engineering reference at the end."),
 ],
},
{
 "slug": "how-the-rate-register-works",
 "title": "How the rate register works",
 "nav": "How the register works",
 "read": 5, "words": 830,
 "desc": ("Building the list of every rate your business has written down, why the \"used in\" "
          "column is the whole point, and how to find the rates nobody remembers."),
 "og": ("The register is the product. What is in a row, how to find the rates nobody remembers, "
        "and why the \"used in\" column is the only part software cannot supply."),
 "abstract": ("What is in a register row, the four ways to find rates nobody remembers, and "
              "why the \"used in\" column is the one thing no software can supply for you."),
 "lede": ("This post has almost no engineering in it, which is honest, because the register is "
          "the part of this system that no amount of code will build for you. It is an "
          "afternoon of asking people where numbers live, and it is worth an afternoon "
          "regardless of whether you build anything else in this series."),
 "tags": ["tax rates", "compliance", "register", "documentation", "small business", "serverless"],
 "takeaways": [
  "A register row is a rate, a source, an effective date, an owner, and a list of places.",
  "The list of places is the only part software cannot supply. Everything else is lookup.",
  "Four reliable ways to find rates nobody remembers, in rough order of yield.",
  "A rate you cannot find an official source for is still worth registering, marked as manual.",
  "The register lives in a sheet, so it survives the system being switched off.",
 ],
 "blocks": [
  ("h2", "One row"),
  ("pre", "rate            Standard VAT rate\n"
          "value           0.20\n"
          "format          percent | amount | threshold\n"
          "source_url      https://... the official publication\n"
          "source_kind     html | pdf | feed | manual\n"
          "selector        the part of the page the value lives in\n"
          "effective_from  2011-01-04\n"
          "used_in         quoting sheet (tab Prices, B4)\n"
          "                price list PDF (page 2)\n"
          "                invoice template (Xero, tax rate 'Standard')\n"
          "                booking form (config: VAT_RATE)\n"
          "owner           finance@example.com\n"
          "last_checked    2026-07-15T06:00:00Z\n"
          "last_seen_value 0.20"),
  ("p", "The <code>used_in</code> entries are deliberately specific &mdash; a tab and a cell, a "
        "page number, a named setting, a config key. \"The quoting spreadsheet\" is not "
        "actionable at eight in the morning eleven months from now; \"quoting sheet, tab "
        "Prices, cell B4\" is."),
  ("h2", "Finding the rates nobody remembers"),
  ("fig", ("chain", {
    "entry": {"title": "Start empty", "sub": ["nobody has this list"], "icon": "doc"},
    "steps": [
      {"title": "Search your own files", "sub": ["for % signs and rate words"], "icon": "search",
       "side": {"title": "Drive, S3, repos", "sub": ["everything you own"], "icon": "bucket"}},
      {"title": "Read last year's returns", "sub": ["every rate you filed"], "icon": "report"},
      {"title": "Ask the three people", "sub": ["who make quotes,", "invoices and prices"],
       "icon": "team"},
      {"title": "Check every template", "sub": ["invoice, quote, contract"], "icon": "form"},
      {"title": "A register", "sub": ["usually 8-20 rows"], "icon": "check"}],
    "note": "The third step finds the ones the first two cannot. Rates live in people."}),
   "Four ways to build the register, in rough order of yield. The third is the one that finds "
   "the rates that exist only as a habit.",
   "Four ways to find the tax rates a business has written down",
   "A vertical chain of five steps entered by a box labelled Start empty, because nobody has "
   "this list. Step one searches your own files across Drive, S3 and code repositories for "
   "percent signs and rate words. Step two reads last year's tax returns for every rate you "
   "filed. Step three asks the three people who make quotes, invoices and prices. Step four "
   "checks every template: invoice, quote and contract. Step five is A register, usually eight "
   "to twenty rows. A note says the third step finds the ones the first two cannot, because "
   "rates live in people."),
  ("ul", [
   "<strong>Search your own files.</strong> A grep across Drive, shared folders and any code "
   "for percent signs next to words like tax, VAT, duty, rate and threshold finds a surprising "
   "amount in twenty minutes. It finds the written-down ones.",
   "<strong>Read last year's returns.</strong> Every rate you actually filed against is on a "
   "form somewhere, and the accountant's working papers usually name the thresholds too. This "
   "finds the ones you use correctly but never wrote down.",
   "<strong>Ask three people.</strong> Whoever prices work, whoever raises invoices, and "
   "whoever deals with the accountant. The question is not \"what rates do we use\" &mdash; "
   "nobody can answer that &mdash; it is \"when you quote a job, where do you get the tax "
   "number from?\" The answers are frequently \"I know it\" and that is a register row.",
   "<strong>Check every template.</strong> Invoice, quote, contract, order form, rate card. "
   "Numbers get typed into templates once and inherited forever.",
  ]),
  ("h3", "Rates with no official source"),
  ("p", "Some numbers you rely on are not published anywhere machine-readable: a rate agreed "
        "with your accountant, a threshold in a trade body's guidance, a duty rate that only "
        "appears in a PDF schedule. Those still belong in the register, marked "
        "<code>manual</code>."),
  ("p", "A manual row is never watched, but it is reviewed &mdash; the system sends a reminder "
        "on a cadence you set, usually annually before the fiscal year, saying \"these six "
        "rates are not watched; please confirm they are still right\". That is a much weaker "
        "control than watching, and it is enormously better than the rate not being on any list "
        "at all."),
  ("h2", "Keeping the register in a sheet"),
  ("p", "The register lives in a spreadsheet, read by the system rather than owned by it. That "
        "is a deliberate constraint and it costs nothing: a sheet can be edited by a "
        "bookkeeper, survives the system being switched off, can be printed and handed to an "
        "accountant, and requires no permissions model."),
  ("callout", "What a good register row avoids", [
   "Vagueness in <code>used_in</code>. \"The website\" is not a place; \"the pricing page, "
   "second paragraph\" is.",
   "A source that is a summary rather than a publication. Aggregator sites are convenient, "
   "occasionally wrong, and unusable as an audit trail.",
   "One row for two rates. A reduced rate and a standard rate are separate rows with separate "
   "effective dates, even when they are published on the same page.",
   "An owner who is a team. \"Finance\" does not read email; a person does.",
  ]),
  ("p", "Next: how the watcher reads a source without producing a false alarm every time a "
        "website is redesigned."),
 ],
},
{
 "slug": "how-a-source-gets-read",
 "title": "How a source gets read",
 "nav": "How sources are read",
 "read": 5, "words": 840,
 "desc": ("Fetching a government page without breaking on every redesign, why the snapshot is "
          "kept, and why a source that stops being readable is an alarm rather than silence."),
 "og": ("Government pages get redesigned. Reading them robustly means anchoring on the label "
        "rather than the layout, keeping a snapshot, and treating unreadable as an alarm."),
 "abstract": ("Fetching a government page without breaking on every redesign: anchoring on the "
              "label rather than the markup, keeping the snapshot, and treating unreadable as "
              "an alarm rather than as silence."),
 "lede": ("The failure mode of every watcher ever built is that it quietly stops watching. The "
          "page moves, the selector breaks, the fetch starts returning a cookie banner, and the "
          "system reports no changes for eighteen months because it is reading nothing. This "
          "post is mostly about that."),
 "tags": ["tax rates", "web scraping", "AWS Bedrock", "monitoring", "compliance", "serverless"],
 "takeaways": [
  "Anchor on the label, not the markup. \"Standard rate\" survives a redesign; a CSS path does not.",
  "Every fetch stores a snapshot, so a change can be evidenced eighteen months later.",
  "A source that becomes unreadable raises an alarm. Silence is the dangerous outcome.",
  "PDFs are read the same way as pages, through Textract, and change less often.",
  "The model reads the page; the comparison is plain equality on a number.",
 ],
 "blocks": [
  ("h2", "How a page gets read"),
  ("fig", ("chain", {
    "entry": {"title": "Scheduled check", "sub": ["daily, per source"], "icon": "clock"},
    "steps": [
      {"title": "Fetch the source", "sub": ["with a real user agent"], "icon": "external",
       "exit": {"title": "Fetch failed", "sub": ["alarm after 3 days"], "icon": "alarm",
                "label": "error"}},
      {"title": "Store the snapshot", "sub": ["S3, content-addressed"], "icon": "bucket"},
      {"title": "Unchanged bytes?", "sub": ["digest vs last time"], "icon": "branch",
       "exit": {"title": "Nothing to do", "sub": ["the usual outcome"], "icon": "check",
                "label": "same"}},
      {"title": "Find the labelled value", "sub": ["one Bedrock call"], "icon": "model",
       "side": {"title": "Register row", "sub": ["the label to find"], "icon": "doc"},
       "exit": {"title": "Label not found", "sub": ["alarm, do not assume"], "icon": "alarm",
                "label": "missing"}},
      {"title": "Compare with the register", "sub": ["plain equality"], "icon": "counter"}],
    "note": "The byte digest short-circuits almost every check, so the model is rarely called."}),
   "How one source is read on a schedule. The digest check means the model is only involved on "
   "the rare days a page actually changes, and a missing label is an alarm rather than an "
   "assumption.",
   "How a tax rate source is fetched, snapshotted and read",
   "A vertical chain of five steps entered by a box labelled Scheduled check, running daily per "
   "source. Step one fetches the source with a real user agent; a fetch error exits to Fetch "
   "failed, which alarms after three consecutive days. Step two stores the snapshot in S3, "
   "content-addressed. Step three asks whether the bytes are unchanged by comparing the digest "
   "with last time; unchanged exits to Nothing to do, the usual outcome. Step four finds the "
   "labelled value with a single Bedrock call, grounded by the label named in the register row; "
   "if the label is not found it exits to Label not found, which alarms rather than assuming "
   "anything. Step five compares the found value with the register using plain equality. A note "
   "says the byte digest short-circuits almost every check, so the model is rarely called."),
  ("h3", "Anchoring on the label"),
  ("p", "The naive approach is a CSS selector or an XPath, and it breaks on the first redesign, "
        "which for a government site is roughly annual. The robust approach is to describe what "
        "you are looking for in words &mdash; \"the standard rate percentage\" &mdash; and ask "
        "the model to find it in the page text."),
  ("p", "That survives a redesign, a table becoming a list, and a value moving between "
        "paragraphs. What it does not survive is the label itself changing, which is exactly "
        "right: if a page stops describing something as the standard rate, that is a real event "
        "and a human should look at it. So a missing label is an alarm, not a silent zero."),
  ("h3", "Why the snapshot is kept"),
  ("p", "Two reasons, and the second is the one people do not anticipate. The first is audit: "
        "when somebody asks in eighteen months why a rate was applied from a particular date, "
        "the answer should be a stored copy of the page as it read on that date, not a memory "
        "and a link to a page that has since changed."),
  ("p", "The second is debugging the watcher itself. When a source starts producing a value "
        "that looks wrong, having the last thirty snapshots means you can see exactly when the "
        "page changed shape. Content-addressed storage means thirty daily snapshots of an "
        "unchanged page cost one object, not thirty."),
  ("h2", "The failure mode that matters"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Fetch fails", "sub": ["3 days -> alarm"], "icon": "alarm"},
      {"title": "Label missing", "sub": ["immediate alarm"], "icon": "search"},
      {"title": "Value unparseable", "sub": ["immediate alarm"], "icon": "stop"},
      {"title": "Source moved", "sub": ["redirect chain logged"], "icon": "link"},
      {"title": "No check at all", "sub": ["the worst one"], "icon": "clock"}],
    "title": "FIVE WAYS A WATCHER SILENTLY STOPS",
    "note": "The fifth needs its own heartbeat, because a watcher that is not running reports nothing."}),
   "The five ways a watcher stops working, and why the last one needs a separate mechanism. "
   "Nothing inside a system that is not running can report that it is not running.",
   "Five ways a rate watcher can silently stop working",
   "A horizontal row of five boxes. Fetch fails: alarms after three consecutive days. Label "
   "missing: alarms immediately. Value unparseable: alarms immediately. Source moved: the "
   "redirect chain is logged and followed once. No check at all: the worst one. A note says the "
   "fifth needs its own heartbeat, because a watcher that is not running reports nothing."),
  ("p", "The last one deserves the emphasis. Every other failure produces a message from inside "
        "the system; a system that is not running produces nothing, which is indistinguishable "
        "from a quiet month. So the register carries a <code>last_checked</code> timestamp per "
        "row, and a separate scheduled job &mdash; a different rule, in a different function "
        "&mdash; alarms if any row has not been checked in three days."),
  ("p", "That is a small amount of duplication and it is the difference between a watcher and "
        "the appearance of one."),
  ("h3", "PDFs"),
  ("p", "A good proportion of authoritative rate schedules are PDFs, often several hundred pages "
        "of them. They are handled the same way: fetch, digest, and only if the bytes changed do "
        "they go through Textract and the same label-anchored read. PDFs change less often than "
        "pages, which makes the digest short-circuit even more effective, and when they do "
        "change it is usually a whole new document with a new URL &mdash; which the redirect "
        "and link-following logic has to handle."),
  ("p", "Next: what the differ does with a change, and why the effective date matters more than "
        "the value."),
 ],
},
{
 "slug": "how-a-rate-change-gets-dated",
 "title": "How a rate change gets dated",
 "nav": "How it is dated",
 "read": 5, "words": 820,
 "desc": ("Announcement and effect are months apart, and the gap is the whole value. Reading "
          "the effective date, handling changes with no date, and the transitional cases."),
 "og": ("A rate change has two dates -- when it was announced and when it applies -- and the "
        "gap between them is the entire value of the system."),
 "abstract": ("Announcement and effect are months apart, and the gap is where the value is. "
              "Reading the effective date, what to do when there is not one, and the "
              "transitional cases that catch people out."),
 "lede": ("A tax rate change has two dates and almost every system that watches for changes "
          "only records one. The value is not in knowing that a rate changed; you would find "
          "that out eventually. The value is in the months between the announcement and the "
          "effect, which is the only window in which anything can be done calmly."),
 "tags": ["tax rates", "effective dates", "compliance", "change management", "scheduling",
          "serverless"],
 "takeaways": [
  "Two dates per change: when it was announced and when it applies.",
  "A change with no stated effective date is treated as immediate and flagged as uncertain.",
  "Transitional rules are read but never interpreted. They go to a person verbatim.",
  "A rate that changes twice before taking effect supersedes the first notice rather than adding one.",
  "The register keeps a history, so the value on any past date can be answered.",
 ],
 "blocks": [
  ("h2", "Two dates"),
  ("fig", ("chain", {
    "entry": {"title": "Value differs", "sub": ["from the register"], "icon": "counter"},
    "steps": [
      {"title": "Effective date stated?", "sub": ["on the same page"], "icon": "branch",
       "exit": {"title": "Treat as immediate", "sub": ["and say it is uncertain"],
                "icon": "alarm", "label": "no date"}},
      {"title": "Already notified?", "sub": ["same change, same date"], "icon": "branch",
       "side": {"title": "DynamoDB changes", "sub": ["what was sent"], "icon": "database"},
       "exit": {"title": "Supersede", "sub": ["one notice, not two"], "icon": "retry",
                "label": "revised"}},
      {"title": "Transitional text?", "sub": ["near the change"], "icon": "branch",
       "exit": {"title": "Attach it verbatim", "sub": ["never summarised"], "icon": "doc",
                "label": "found"}},
      {"title": "Notify now", "sub": ["with the checklist"], "icon": "email"},
      {"title": "Schedule the reminder", "sub": ["four weeks before effect"], "icon": "clock"}],
    "note": "The last step is the one that turns an announcement into an action."}),
   "How a detected difference becomes a dated, scheduled change. The supersede path matters "
   "because rates are frequently revised between announcement and effect.",
   "How a detected rate change is dated and scheduled",
   "A vertical chain of five steps entered by a box labelled Value differs from the register. "
   "Step one asks whether an effective date is stated on the same page; if not it exits to "
   "Treat as immediate while saying the date is uncertain. Step two asks whether this same "
   "change with this same date has already been notified, checking a DynamoDB changes table; a "
   "revision exits to Supersede, producing one notice rather than two. Step three asks whether "
   "there is transitional text near the change, exiting to Attach it verbatim, never "
   "summarised. Step four notifies now with the checklist. Step five schedules a reminder four "
   "weeks before the change takes effect. A note says the last step is the one that turns an "
   "announcement into an action."),
  ("h3", "When there is no effective date"),
  ("p", "It happens, particularly on pages that are updated in place rather than published as "
        "announcements. The system's response is to treat the change as effective now and to "
        "say clearly in the notice that no effective date could be found, with a link to the "
        "page and the snapshot."),
  ("p", "Treating it as immediate is the cautious choice and it is the right one. The failure "
        "mode of assuming a future date is applying an old rate after a new one took effect, "
        "which is a filing error. The failure mode of assuming immediate is somebody looking at "
        "a page and deciding it does not apply yet, which is a two-minute check."),
  ("h3", "Transitional rules"),
  ("p", "Rate changes frequently come with rules about work spanning the change: which rate "
        "applies to an invoice raised before but delivered after, how deposits taken earlier are "
        "treated, whether continuous supplies are apportioned. These are the parts that actually "
        "cause errors, and they are exactly the parts a system must not try to summarise."),
  ("p", "So transitional text near a changed value is extracted verbatim and attached to the "
        "notice under a plain heading, with the link. The system's contribution is finding it "
        "and putting it in front of somebody. Interpreting it is a conversation with an "
        "accountant, and any attempt to compress it into a rule is how a business ends up "
        "confidently doing the wrong thing at scale."),
  ("h2", "Superseding"),
  ("p", "A rate announced in one budget and revised in the next before it ever took effect is "
        "not two changes; it is one pending change that moved. Sending a second notice without "
        "connecting it to the first produces two contradictory checklists sitting in somebody's "
        "inbox, and the wrong one gets actioned about half the time."),
  ("p", "So a pending change carries an id, and a subsequent change to the same rate with an "
        "effective date in the future supersedes it: the notice says so explicitly, the old "
        "reminder is cancelled, and a new one is scheduled. The superseded notice is kept in "
        "the history because it explains why somebody may have already edited something."),
  ("h2", "The history"),
  ("fig", ("strip", {
    "stages": [
      {"title": "Value", "sub": ["what it was"], "icon": "counter"},
      {"title": "From", "sub": ["when it started"], "icon": "calendar"},
      {"title": "Source", "sub": ["the snapshot"], "icon": "bucket"},
      {"title": "Notified", "sub": ["who, when"], "icon": "email"},
      {"title": "Actioned", "sub": ["and by whom"], "icon": "check"}],
    "title": "WHAT THE HISTORY ANSWERS",
    "note": "\"What rate applied on 3 March 2024, and how did we know?\" -- in one query."}),
   "The five things a history row holds, which together answer the only question anybody ever "
   "asks about a past rate: what was it, and how did we know?",
   "The five fields of a rate history row",
   "A horizontal row of five boxes. Value: what the rate was. From: when it started applying. "
   "Source: the stored snapshot of the page it was read from. Notified: who was told and when. "
   "Actioned: whether it was actioned and by whom. A note says this answers, in one query, what "
   "rate applied on a given date and how you knew."),
  ("p", "Next: the reminder, and why acknowledging a notice is the only interaction the system "
        "asks for."),
 ],
},
{
 "slug": "how-the-rate-reminder-works",
 "title": "How the rate reminder works",
 "nav": "How it reminds",
 "read": 5, "words": 810,
 "desc": ("The second notice before the effective date, the per-place checklist, and why "
          "acknowledging is the only interaction the system ever asks for."),
 "og": ("Announcements get forgotten. The reminder four weeks before the effective date, with "
        "a per-place checklist, is what converts a notice into an edit."),
 "abstract": ("The second notice four weeks before the effective date, the per-place checklist "
              "with a tick per location, and why acknowledgement is the only interaction the "
              "system ever asks for."),
 "lede": ("A system that notices a rate change in March and says nothing again until it takes "
          "effect in October has done half a job. The half it did is the easy half. This post "
          "is about the other one."),
 "tags": ["tax rates", "reminders", "checklists", "Amazon SES", "compliance", "serverless"],
 "takeaways": [
  "Two notices per change: one on announcement, one four weeks before effect.",
  "The reminder carries a checklist with one tick per place from the register.",
  "Ticking a place is the only interaction the system asks for, and it is optional.",
  "An unticked place at the effective date is escalated once, then left visible.",
  "The annual review covers manual rates, which are never watched but must not be forgotten.",
 ],
 "blocks": [
  ("h2", "Two notices, deliberately"),
  ("fig", ("system", {
    "outside": [
      {"title": "Owner", "sub": ["gets both notices"], "icon": "person"},
      {"title": "Register", "sub": ["the places to edit"], "icon": "doc"},
      {"title": "Whoever files", "sub": ["escalation only"], "icon": "team"}],
    "inside": [
      {"title": "Announcer", "sub": ["on the day it", "is published"], "icon": "email"},
      {"title": "Reminder", "sub": ["four weeks before", "it takes effect"], "icon": "clock"},
      {"title": "Checklist", "sub": ["one tick per place"], "icon": "check"}],
    "edges": [{"from": 0, "to": 0, "label": "ticks, or nothing", "up": True},
              {"from": 1, "to": 1, "label": "the places"},
              {"from": 2, "to": 2, "label": "only if unticked at effect", "up": True}],
    "note": "The whole system asks for one interaction, and it is optional."}),
   "The two notices and the checklist between them. The system is deliberately undemanding: "
   "the only thing it ever asks anybody to do is tick a box, and not ticking it is allowed.",
   "How the announcement and the reminder reach the rate owner",
   "Three boxes across the top outside the AWS account. The Owner, who gets both notices. The "
   "Register, which supplies the list of places to edit. And Whoever files, who is involved "
   "only on escalation. Inside the account, three components. The Announcer, which sends on the "
   "day a change is published. The Reminder, which sends four weeks before it takes effect. And "
   "the Checklist, which carries one tick per place. Arrows show the owner returning ticks or "
   "nothing, the register supplying the places, and an escalation reaching whoever files only "
   "if places remain unticked at the effective date. A note says the whole system asks for one "
   "interaction and it is optional."),
  ("h3", "What the reminder says"),
  ("callout", "The reminder, in order", [
   "<strong>Line one.</strong> The change and the date. \"Standard rate goes from 20% to 22% on "
   "1 October &mdash; four weeks today.\"",
   "<strong>Line two.</strong> When you were first told. \"Announced 14 March; this is the "
   "reminder.\"",
   "<strong>The checklist.</strong> One line per place from the register, each with a tick box: "
   "quoting sheet tab Prices cell B4, price list PDF page 2, Xero tax rate 'Standard', booking "
   "form config VAT_RATE.",
   "<strong>The transitional text,</strong> verbatim, if there was any, under its own heading "
   "with the source link.",
   "<strong>The snapshot link.</strong> The page as it read when the change was detected.",
  ]),
  ("p", "The checklist is the working part. It is not a workflow, there is no approval, and "
        "nothing is blocked by leaving it unticked. It exists because \"update the VAT rate\" "
        "is a task somebody will do incompletely and \"update these four specific things\" is a "
        "task somebody will do completely, and the difference between those two outcomes is a "
        "customer finding an error in a price list eight months later."),
  ("h3", "Why ticking is optional"),
  ("p", "Because making it mandatory would make the system something people have to serve, and "
        "systems that people have to serve get worked around. If somebody updates all four "
        "places and never touches the checklist, the change still happened correctly and the "
        "system was still useful. The tick is a convenience for the person doing the work, not "
        "a control."),
  ("p", "The one place it has teeth is the escalation: if the effective date arrives and places "
        "remain unticked, one message goes to whoever files the returns saying which places were "
        "not confirmed. That is not an accusation &mdash; the work may well have been done "
        "&mdash; it is a prompt to check, from the person who carries the consequence of it "
        "not having been."),
  ("h2", "The annual review of manual rates"),
  ("p", "Rates with no watchable source get a different treatment: a single message on a "
        "cadence you set, usually shortly before the fiscal year, listing them and asking for "
        "confirmation."),
  ("fig", ("strip", {
    "stages": [
      {"title": "Watched", "sub": ["14 rates"], "icon": "search"},
      {"title": "Manual", "sub": ["6 rates"], "icon": "doc"},
      {"title": "Changed", "sub": ["2 this year"], "icon": "counter"},
      {"title": "Actioned", "sub": ["both, fully"], "icon": "check"},
      {"title": "Unconfirmed", "sub": ["1 manual rate"], "icon": "alarm"}],
    "title": "ONE YEAR OF THE REGISTER",
    "note": "The fifth number is the only one that needs anybody to do anything."}),
   "A year of the register in five numbers. Most of it is quiet, which is what a compliance "
   "control should look like when nothing is wrong.",
   "One year of the tax rate register summarised in five numbers",
   "A horizontal row of five boxes. Watched: fourteen rates have an official source. Manual: "
   "six do not. Changed: two changed this year. Actioned: both were fully actioned across every "
   "place in the register. Unconfirmed: one manual rate has not been confirmed. A note says the "
   "fifth number is the only one that needs anybody to do anything."),
  ("p", "That last number is the honest weakness of the system, stated plainly rather than "
        "hidden. Six rates that nothing watches is six rates that could be wrong right now, and "
        "the only control on them is somebody reading a list once a year and thinking about it. "
        "Naming that in the annual summary is better than a dashboard that shows fourteen green "
        "ticks and does not mention the other six."),
  ("p", "Next: what all of this costs to run."),
 ],
},
]

SPEC["parts"].append(cost_part(
 slug=SLUG, name=NAME, unit="source check",
 volumes=[(200, "200 checks"), (600, "600 checks"), (2000, "2,000 checks")],
 read_each=0.0003, msgs_each=0.05,
 lede=("This is the cheapest system in the series by a wide margin, for a structural reason: "
       "almost every check ends at the byte-digest comparison and never reaches a model at all. "
       "Twenty sources checked daily is six hundred checks a month, of which perhaps three "
       "involve any real work. Here is where each cent goes."),
 takeaway_extra=("Almost every check ends at the digest comparison, so the model runs a handful "
                 "of times a year rather than a handful of times a day."),
 risks=[
  "<strong>Reading the page on every check.</strong> If the byte digest short-circuit is "
  "skipped, twenty sources checked daily is six hundred model calls a month instead of three. "
  "The digest is the single most important cost decision in this design.",
  "<strong>Storing a snapshot per check rather than per change.</strong> Content-addressed "
  "storage means an unchanged page costs one object however many times it is fetched; keying "
  "snapshots by date instead multiplies storage by three hundred and sixty-five.",
  "<strong>Log retention left at never.</strong> This system produces almost nothing but logs. "
  "Without a retention setting the logs will be the entire bill within a year.",
 ],
 per_unit_note=("The unit here is a source check rather than a change, because checks are what "
                "you pay for. Twenty registered sources checked daily produce six hundred "
                "checks a month and perhaps two changes a year, which is exactly the ratio you "
                "want from a compliance watcher."),
))

SPEC["parts"].append(reference_part(
 slug=SLUG, name=NAME, prefix="tr",
 lede=("The first six posts are for the person deciding whether to build this. This one is for "
       "the person building it. Same system, no analogies: the services by name, the functions, "
       "the two tables, the fetch discipline, and the one model call."),
 outside=[
  {"title": "Official sources", "sub": ["HTTPS, some PDFs"], "icon": "external"},
  {"title": "Register sheet", "sub": ["Sheets API, read-only"], "icon": "doc"},
  {"title": "SES outbound", "sub": ["notices, reminders"], "icon": "email"}],
 inside=[
  {"title": "S3 + EventBridge", "sub": ["snapshots,", "two schedules"], "icon": "bucket"},
  {"title": "Lambda x3", "sub": ["check, notify,", "heartbeat"], "icon": "lambda"},
  {"title": "DynamoDB x2", "sub": ["rates, changes"], "icon": "database"}],
 note="us-east-1. One account. Outbound HTTPS only; nothing inbound except the answer links.",
 diagram_desc=(
  "Three boxes across the top outside the AWS account. Official sources, fetched over HTTPS, "
  "some of them PDFs. The Register sheet, read through the Google Sheets API read-only. And "
  "SES outbound, carrying the notices and reminders. Inside the account, three groups. S3 "
  "holding content-addressed snapshots, and EventBridge carrying two schedules. Three Lambda "
  "functions named check, notify and heartbeat. And two DynamoDB tables named rates and "
  "changes. A note gives the region as us-east-1, one account, with outbound HTTPS only and "
  "nothing inbound except the checklist answer links."),
 functions=[
  ["<code>tr-check</code>", "EventBridge daily",
   "Fetches each source, snapshots, digests, reads on change", "120s / 1024&nbsp;MB"],
  ["<code>tr-notify</code>", "SQS change queue + EventBridge daily",
   "Announcements, reminders, escalations and the annual review", "30s / 512&nbsp;MB"],
  ["<code>tr-heartbeat</code>", "EventBridge daily, separate rule",
   "Alarms if any register row has not been checked in three days", "10s / 256&nbsp;MB"]],
 roles=[
  ["<code>tr-check-role</code>",
   "<code>s3:PutObject</code>, <code>bedrock:InvokeModel</code>, "
   "<code>secretsmanager:GetSecretValue</code>",
   "The snapshots prefix; one model arn; the Sheets credential"],
  ["<code>tr-notify-role</code>", "<code>ses:SendEmail</code>, <code>dynamodb:UpdateItem</code>",
   "One verified identity; rates and changes"],
  ["<code>tr-heartbeat-role</code>", "<code>dynamodb:Scan</code>, <code>sns:Publish</code>",
   "The rates table; the operations topic only"]],
 tables=[
  ("Table: rates",
   "PK   rate_id           S   standard-vat\n"
   "     label             S   Standard VAT rate\n"
   "     value             N   0.20\n"
   "     format            S   percent | amount | threshold\n"
   "     source_url        S   https://...\n"
   "     source_kind       S   html | pdf | feed | manual\n"
   "     find_label        S   the standard rate percentage\n"
   "     effective_from    S   2011-01-04\n"
   "     used_in           L   [{place, locator}]\n"
   "     owner             S   finance@example.com\n"
   "     last_checked      S   2026-07-15T06:00:00Z\n"
   "     last_digest       S   sha256 of the last fetch\n\n"
   "`last_checked` is what the heartbeat scans. A row that has not moved in\n"
   "three days is an alarm regardless of what the rest of the system thinks."),
  ("Table: changes",
   "PK   change_id         S   chg_standard-vat_2026-10-01\n"
   "     rate_id           S   standard-vat\n"
   "     old_value         N   0.20\n"
   "     new_value         N   0.22\n"
   "     effective_from    S   2026-10-01\n"
   "     date_certainty    S   stated | assumed_immediate\n"
   "     announced_at      S   2026-03-14\n"
   "     snapshot_key      S   s3://snapshots/sha256...\n"
   "     transitional      S   verbatim text, or null\n"
   "     superseded_by     S   another change_id, or null\n"
   "     checklist         L   [{place, ticked_by, ticked_at}]\n"
   "     reminder_at       S   2026-09-03\n\n"
   "GSI  reminder-index      PK reminder_at   -- the daily notify sweep")],
 inbound=[
  "<strong>Outbound only</strong>, apart from the checklist links. There is no inbound mail "
  "path and no webhook, which removes an entire class of surface.",
  "<strong>Fetches identify themselves</strong> with a real user agent naming the business and "
  "a contact address. Government sites are generally tolerant of this and hostile to anything "
  "that looks like an anonymous scraper.",
  "<strong>Conditional requests</strong> are used where the source supports them: an ETag or "
  "Last-Modified turns most daily checks into a 304 that costs nothing and confirms the source "
  "is still reachable.",
  "<strong>Checklist links</strong> are signed, scoped to one change and one place, and expire "
  "sixty days after the effective date."],
 model_notes=[
  "<strong>Model:</strong> <code>anthropic.claude-haiku-4-5-20251001-v1:0</code> on Bedrock. "
  "The task is finding a labelled value in page text, which is extraction.",
  "<strong>Called only when the bytes changed.</strong> An unchanged digest short-circuits "
  "before any model call, which is why this system costs almost nothing.",
  "<strong>Output is a JSON schema</strong> with the value, an effective date and any "
  "transitional text, all nullable. A null value is a Label-not-found alarm and never a zero.",
  "<strong>Grounded</strong> with the label from the register row, so the model is looking for "
  "a specific described thing rather than summarising a page.",
  "<strong>Transitional text is returned verbatim</strong> and never summarised. Summarising a "
  "transitional rule is how a business confidently does the wrong thing at scale."],
 gotchas=[
  "Anchor on the label, not on markup. A CSS path breaks on the first redesign; \"the standard "
  "rate percentage\" survives one.",
  "Treat a missing label as an alarm, not as an unchanged value. A page that stops describing "
  "something is a real event.",
  "Give the heartbeat its own EventBridge rule and its own function. A watcher cannot report "
  "that it is not running.",
  "Store snapshots content-addressed. Three hundred and sixty-five daily fetches of an "
  "unchanged page should cost one object.",
  "Never summarise transitional rules, and never let the system apply one. Extract them "
  "verbatim, attach them, and let an accountant read them."],
))
