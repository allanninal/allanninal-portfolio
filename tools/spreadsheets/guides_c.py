#!/usr/bin/env python3
"""Group C — cleaning a real export, by the job that produces it.

Groups A and B are organised by the fault. This group is organised by the person, because
that is how the problem is actually searched for: nobody types "non-breaking space in a
lookup key", they type "bank statement import excel messy". Each page takes one real
export, names the specific columns that go wrong in it, and works through them in order.

The overlap with groups A and B is deliberate and cross-linked rather than repeated. What
is genuinely new here is the sequence — which column to fix first, and which fault is
characteristic of that export. A bank CSV's problem is the amount column; a school export's
problem is the ID column; they need different first moves.

No profession-specific claim is made that is not a property of the file format. There is
no invented statistic about how much time this saves anyone.
"""
from build_guide import fx, symptom_table

GROUP = "Cleaning a real export"
CAT = "Worked examples"

GUIDES_C = [

dict(
 slug="clean-bank-statement-export-excel",
 title="Cleaning a Bank Statement Export in Excel",
 description="Bank CSVs arrive with amounts as text, accounting negatives in brackets, and dates in the wrong locale. The order to fix them so the balance reconciles.",
 h1="Cleaning a bank statement export so it actually reconciles",
 lead="The download opens, the columns look right, and the total is wrong. Bank exports break in three specific places, and fixing them in the wrong order means doing it twice.",
 category=CAT, group=GROUP,
 card_title="A bank statement export",
 card_blurb="Amounts as text, negatives in brackets, dates in the wrong locale.",
 chips=["Bookkeeping", "Reconciliation", "Excel + Google Sheets"],
 keywords=["clean bank statement excel", "bank csv excel import", "excel accounting negatives",
           "bank statement reconciliation excel", "excel bank export text numbers",
           "excel statement date format"],
 short_answer="""<p><strong>Fix it in this order: dates, then amounts, then the description
column.</strong> The amount column is almost always text, because it arrives with a currency symbol,
a thousands separator, or negatives written as <code>(500)</code> in brackets. Convert dates using
<em>Change Type &rarr; Using Locale</em> so a UK statement is not read as US, then strip the amount
column and convert it, then trim the description. Reconcile only after all three.</p>""",
 problem_h="Three faults, and why the order matters",
 problem="""<p><strong>The amount column is text.</strong> <code>SUM</code> returns zero or a
plausible-but-wrong figure. This is the fault that makes the balance disagree, and it is caused by
whatever the bank attached to the number: <code>&pound;</code>, <code>$</code>, a comma, a trailing
space where a currency code was stripped, or brackets for negatives.</p>
<p><strong>Accounting negatives.</strong> Banks and accounting systems write minus 500 as
<code>(500)</code>. Excel reads that as text, not as a negative number. If you convert the column
without handling the brackets first, every debit either fails to convert or converts as a
<em>positive</em> &mdash; and the balance is wrong by exactly twice the debits, which is a very
confusing number to chase.</p>
<p><strong>Dates in the wrong locale.</strong> A UK statement dated <code>03/04/2026</code> read on a
US-configured Excel becomes 4 March instead of 3 April. Transactions land in the wrong month, and
every date before the 13th is silently plausible. This is why dates come first: reconciling by month
against wrong dates wastes the whole exercise.</p>""",
 symptoms=symptom_table([
   ["<code>SUM</code> of amounts returns 0",
    "The whole column is text",
    "Strip symbols, then convert"],
   ["Balance out by twice the debits",
    "Bracketed negatives converted as positives",
    "Handle the brackets before converting"],
   ["Transactions in the wrong month",
    "Date read in the wrong locale",
    "Change Type &rarr; Using Locale on import"],
   ["Duplicate-looking payees not grouping",
    "Trailing spaces and inconsistent case",
    "Clean the description column"],
   ["Reference numbers lost leading zeros",
    "Read as numbers on import",
    "Import that column as Text"],
 ]),
 howto_name="How to clean a bank statement export",
 howto_desc="Dates first, then amounts, then descriptions — then reconcile.",
 steps=[
  dict(h="Import with Power Query and set the date locale",
       plain="Use Data > From Text/CSV, click Transform Data, right-click the date column and choose Change Type > Using Locale, then pick the country the statement came from.",
       body="""<p><em>Data &rarr; From Text/CSV &rarr; Transform Data</em>. Right-click the date
column, <em>Change Type &rarr; Using Locale</em>, and choose the country the <em>statement</em> came
from &mdash; not the country you are in. This is the only step that reliably fixes ambiguous dates,
because it tells Excel how to read them rather than letting it guess.</p>
<p>While you are here, set any reference or account-number column to <strong>Text</strong>.</p>"""),
  dict(h="Measure how bad the amount column is",
       plain="Compare COUNTA with COUNT over the amount column. Any difference is the number of rows SUM is silently skipping.",
       body="""<p>Before converting anything, find out how many rows are affected:</p>""" +
       fx("How many amounts are text?", '=COUNTA(D2:D2000)-COUNT(D2:D2000)',
          """<p>Zero means the column is already numeric and your problem is elsewhere. Anything else
is the count of transactions not being added.</p>""")),
  dict(h="Convert amounts, handling bracketed negatives",
       plain="Detect a leading bracket, strip the brackets and negate the result; strip currency symbols and thousands separators from everything else before converting.",
       body="""<p>One formula that covers both the bracket form and the ordinary one:</p>""" +
       fx("Amount, with accounting negatives",
          '=IFERROR(IF(LEFT(TRIM(A2),1)="(",\n'
          '   -VALUE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(A2,"(",""),")",""),",",""),"$","")),\n'
          '   VALUE(SUBSTITUTE(SUBSTITUTE(A2,",",""),"$",""))),"CHECK")',
          """<p>Extend the nested <code>SUBSTITUTE</code> calls for your currency symbol. Anything
that still will not convert returns <code>CHECK</code> rather than an error, so you can filter on it
and look at those rows rather than having one bad cell break the column.</p>""")),
  dict(h="Clean the description column before grouping",
       plain="Trim the payee column and remove invisible characters, so the same payee does not appear as several different ones when you group.",
       body="""<p>Bank descriptions are padded to a fixed width and frequently carry trailing spaces.
Grouping by payee without cleaning produces the same supplier three times:</p>""" +
       fx("Clean the payee", '=TRIM(CLEAN(SUBSTITUTE(B2,"[nbsp]"," ")))',
          """<p>Then group on the cleaned column. See the invisible-characters guide for why
<code>TRIM</code> on its own is not enough.</p>""")),
  dict(h="Reconcile against the ledger, in both directions",
       plain="Use COUNTIF to find statement lines missing from the ledger, and ledger lines missing from the statement. Run both directions.",
       body="""<p>Only now is it worth comparing. Match on the cleaned reference, and run the check
both ways &mdash; a statement line with no ledger entry and a ledger entry with no statement line are
different problems.</p>"""),
 ],
 body="""<h2>Why the balance is out by exactly twice the debits</h2>
<p>It is worth recognising this one on sight. If bracketed negatives converted as positives, every
debit is contributing <code>+x</code> where it should contribute <code>&minus;x</code> &mdash; an
error of <code>2x</code> per debit. A balance out by an even, suspiciously round multiple of your
debit total means the brackets were not handled.</p>
<h2>Matching on amount alone will mislead you</h2>
<p>Two transactions for the same amount on the same day are common &mdash; a standing order and a
card payment can easily coincide. Match on the reference where one exists, or on date <em>and</em>
amount together using <code>COUNTIFS</code>, rather than concatenating them into a single key.</p>
<h2>Keep the raw file</h2>
<p>Save the untouched download beside the cleaned copy. When a figure is queried in three months,
the raw file is the evidence, and it is the only thing that can prove whether a discrepancy came from
the bank or from the cleaning.</p>""",
 faq=[
  ("Why does SUM return zero on my bank statement amounts?",
   "The amount column is text, because the bank attached a currency symbol, a thousands separator or brackets for negatives. SUM skips text without warning."),
  ("What does (500) mean in a bank export?",
   "It is accounting notation for minus 500. Excel reads it as text, so it must be detected and negated explicitly before the column is converted."),
  ("Why is my balance out by exactly twice the debits?",
   "Bracketed negatives were converted as positives, so each debit contributes plus x instead of minus x — an error of 2x per debit."),
  ("Why did my transactions land in the wrong month?",
   "The dates were read in the wrong locale. 03/04/2026 is 3 April in the UK and 4 March in the US. Use Change Type > Using Locale on import and pick the statement's country."),
  ("Should I match transactions on the amount?",
   "Not on amount alone — two transactions for the same amount on the same day are common. Match on the reference, or on date and amount together with COUNTIFS."),
  ("Should I keep the original download?",
   "Yes. Save the untouched file beside the cleaned copy. It is the only evidence of what the bank actually sent if a figure is queried later."),
 ],
 related=[("excel-numbers-stored-as-text", "SUM is ignoring half my column"),
          ("excel-compare-two-lists", "Find what is in list A but not list B"),
          ("excel-csv-all-in-column-a", "The whole CSV landed in column A")],
),

dict(
 slug="clean-student-list-excel",
 title="Cleaning a Student List Export in Excel",
 description="School exports lose leading zeros from student IDs and split names inconsistently. How to fix the ID column first, then names, so merges and mail-merges work.",
 h1="Cleaning a class list so the IDs still match",
 lead="The register downloads, the student numbers have lost their leading zeros, and half the names are in one column while the rest are in two. Every merge against another system now fails.",
 category=CAT, group=GROUP,
 card_title="A student or class list export",
 card_blurb="Student IDs lose their zeros; names arrive in inconsistent shapes.",
 chips=["Schools", "Mail merge", "Excel + Google Sheets"],
 keywords=["clean student list excel", "student id leading zeros excel", "excel split names",
           "school export excel", "excel class list clean", "excel mail merge names"],
 short_answer="""<p><strong>Fix the student ID column before anything else, and fix it by
re-importing rather than by formatting.</strong> Student numbers such as <code>004512</code> lose
their leading zeros the moment Excel reads them as numbers, and every match against the timetable,
the library system or last term's file then fails. Import with the ID column set to <strong>Text</strong>,
then normalise the name columns.</p>""",
 problem_h="Why the ID column has to come first",
 problem="""<p>Everything else you do to this file depends on the ID still being the ID.</p>
<p>Student numbers are almost always zero-padded to a fixed width, because that is what makes them
sort correctly and print evenly. Excel sees digits, decides it is a number, and stores 4512. The
match against any other system &mdash; which still holds <code>004512</code> &mdash; now fails for
every student whose number begins with a zero, which is a large and arbitrary-looking subset of the
class.</p>
<p>It is arbitrary-looking that makes it expensive: students 1 to 999 fail and the rest work, so it
presents as &ldquo;some students are missing&rdquo; rather than as a formatting problem.</p>""",
 symptoms=symptom_table([
   ["Some students missing from a merge",
    "Their IDs lost leading zeros",
    "Re-import the ID column as Text"],
   ["IDs of differing lengths",
    "Zeros stripped from some, not others",
    "Same cause &mdash; re-import"],
   ["Names in one column for some rows, two for others",
    "The export changed format, or was hand-edited",
    "Normalise to one shape"],
   ["Mail merge greeting shows a surname",
    "The first-name column contains a full name",
    "Split before merging"],
   ["Duplicate students after combining files",
    "Trailing spaces on the name or ID",
    "Clean before deduplicating"],
 ]),
 howto_name="How to clean a class list export",
 howto_desc="Protect the ID column on import, then normalise names into a single consistent shape.",
 steps=[
  dict(h="Re-import with the student ID column set to Text",
       plain="Use Data > From Text/CSV, click Transform Data, set the student ID column to Text, then load. Do not try to fix the zeros after the fact.",
       body="""<p><em>Data &rarr; From Text/CSV &rarr; Transform Data</em>, select the student ID
column, <em>Data Type &rarr; Text</em>, <em>Close &amp; Load</em>. Formatting the column afterwards
cannot restore a zero that was never stored, so this must happen on import.</p>"""),
  dict(h="If the original is gone, rebuild a fixed-width ID",
       plain="Where student numbers are always the same length, use TEXT with the right number of zeros to rebuild them as text.",
       body="""<p>Only when the length is genuinely fixed and you know it:</p>""" +
       fx("Rebuild a six-digit student number", '=TEXT(A2,"000000")',
          """<p>Six zeros for a six-digit number. If your school's numbers vary in length, this pads
them all to the same width and silently creates wrong IDs &mdash; go back to the source export
instead.</p>""")),
  dict(h="Find the rows where the name shape is inconsistent",
       plain="Count the spaces in the name column. A row with no space is a single name; two or more spaces suggests a middle name or a double-barrelled surname.",
       body="""<p>Before splitting anything, find out what shapes you actually have:</p>""" +
       fx("How many spaces in this name?", '=LEN(TRIM(B2))-LEN(SUBSTITUTE(TRIM(B2)," ",""))',
          """<p>0 means one word, 1 means the ordinary first-and-last case, 2 or more means a middle
name or a double-barrelled surname. Sort on this column and deal with each group deliberately &mdash;
a blanket split will mangle the 2+ group.</p>""")),
  dict(h="Split a full name into first and last",
       plain="Take everything before the first space as the first name and everything after the last space as the surname, and review the rows with more than one space by hand.",
       body="""<p>For the ordinary case:</p>""" +
       fx("Split a full name",
          '=LEFT(TRIM(B2),FIND(" ",TRIM(B2)&" ")-1)\n'
          '=TRIM(RIGHT(SUBSTITUTE(TRIM(B2)," ",REPT(" ",99)),99))',
          """<p>The first takes everything up to the first space &mdash; the <code>&amp;" "</code>
stops it erroring on a single-word name. The second pads every space to 99 characters and takes the
last 99, which reliably returns the final word. Review anything with two or more spaces by hand;
&ldquo;van der Berg&rdquo; is not a middle name.</p>""")),
  dict(h="Standardise capitalisation carefully",
       plain="PROPER capitalises each word but breaks names like McDonald and O'Brien, so check the result rather than accepting it.",
       body="""<p><code>=PROPER(B2)</code> turns <code>SMITH</code> into <code>Smith</code>, which is
usually what you want for a mail merge. It also turns <code>McDonald</code> into
<code>Mcdonald</code> and <code>O'BRIEN</code> into <code>O'Brien</code> &mdash; one right, one
wrong. Sort the result and scan it; a class list is short enough to check by eye, and getting a
child's name wrong on a letter home is worth thirty seconds.</p>"""),
 ],
 body="""<h2>Do not convert the ID column to numbers, ever</h2>
<p>Someone will suggest it to make the column sort properly. It sorts fine as text as long as every
value is zero-padded to the same width &mdash; that is precisely why the padding exists. Converting
to numbers to fix sorting reintroduces the original problem.</p>
<h2>Dates of birth have the same locale trap</h2>
<p>A date of birth of <code>03/04/2012</code> is 3 April or 4 March depending on the locale, and both
are plausible for a child. Import date columns with <em>Change Type &rarr; Using Locale</em> set to
the country the export came from. An error here can put a student in the wrong school year.</p>
<h2>Before a mail merge, check for invisible characters</h2>
<p>Names pasted from a web-based school system frequently carry non-breaking spaces. They do not show
on screen, and they do show up in a printed letter as an odd gap. Clean the column before merging.</p>
<h2>Combining this term's list with last term's</h2>
<p>Match on the student ID, never on the name. Names change &mdash; spelling corrections, preferred
names, families changing surname &mdash; and two students in a year group sharing a name is common
enough to be a real risk. The ID is the only stable key, which is the whole reason to protect it in
step one.</p>""",
 faq=[
  ("Why did my student IDs lose their leading zeros?",
   "Excel read the column as numbers, and as a number 004512 is 4512. The zeros are not hidden by formatting — they were never stored. Re-import with the column set to Text."),
  ("Can I add the zeros back?",
   "Only where the ID length is genuinely fixed and known, using TEXT(A2,\"000000\"). If lengths vary, this pads everything to one width and creates wrong IDs. Re-import the original instead."),
  ("How do I split a full name into first and last?",
   "Take everything before the first space as the first name and everything after the last space as the surname. Review rows containing two or more spaces by hand, because middle names and double-barrelled surnames need judgement."),
  ("Should I use PROPER to fix capitalisation?",
   "With care. PROPER capitalises each word, which fixes SMITH but breaks McDonald and mishandles some apostrophes. Check the output rather than accepting it, especially for anything sent to families."),
  ("Should I match this term's list to last term's on name or ID?",
   "Always on ID. Names change through spelling corrections, preferred names and family changes, and two students sharing a name in one year group is entirely possible."),
  ("Why are dates of birth landing in the wrong month?",
   "The date column was read in the wrong locale. Use Change Type > Using Locale on import and select the country the export came from."),
 ],
 related=[("excel-leading-zeros-disappear", "Excel keeps deleting my leading zeros"),
          ("excel-vlookup-non-breaking-space", "#N/A when the value is clearly there"),
          ("excel-unique-values-list", "Getting a list of unique values")],
),

dict(
 slug="clean-inventory-sku-export-excel",
 title="Cleaning an Inventory or SKU Export in Excel",
 description="SKUs lose leading zeros, barcodes become scientific notation, and codes like SEP1 turn into dates. The import settings that protect a product catalogue.",
 h1="Cleaning a product export without corrupting the SKUs",
 lead="A product catalogue is almost entirely identifiers, and identifiers are exactly what Excel is worst at. A single import can damage the SKU column, the barcode column and any code that happens to look like a date.",
 category=CAT, group=GROUP,
 card_title="An inventory or SKU export",
 card_blurb="SKUs, barcodes and date-shaped codes — three failures in one file.",
 chips=["Retail + warehouse", "Barcodes", "Excel + Google Sheets"],
 keywords=["clean sku list excel", "excel barcode leading zeros", "excel product export",
           "excel inventory csv", "excel sku date conversion", "excel ean number"],
 short_answer="""<p><strong>Set every identifier column to Text on import &mdash; SKU, barcode,
supplier code, bin location &mdash; and never let Excel parse them as numbers.</strong> A product
export typically hits three failures at once: SKUs lose leading zeros, 13-digit barcodes become
scientific notation or lose digits past the fifteenth, and codes shaped like <code>SEP1</code> or
<code>1-2</code> convert to dates. All three are prevented by the same import step and none can be
repaired afterwards.</p>""",
 problem_h="Why a catalogue is the worst case",
 problem="""<p>Most files have one or two columns Excel can damage. A product catalogue is
<em>mostly</em> such columns, and the damage is silent in a particularly bad way: the file still
looks like a product list.</p>
<ul>
<li><strong>SKUs</strong> are frequently zero-padded, so they lose leading zeros.</li>
<li><strong>Barcodes</strong> are 12&ndash;13 digits, so they display as scientific notation, and
anything longer loses digits past the fifteenth permanently.</li>
<li><strong>Size and variant codes</strong> such as <code>1-2</code>, <code>3/4</code> or
<code>SEP1</code> convert to dates.</li>
<li><strong>Bin locations</strong> such as <code>A1-04</code> can also read as dates in some
locales.</li>
</ul>
<p>Then the file goes back into the system, or to a supplier, or onto a marketplace listing &mdash;
and the wrong barcode is now attached to a real product.</p>""",
 symptoms=symptom_table([
   ["SKUs shorter than they should be",
    "Leading zeros stripped on import",
    "Re-import the column as Text"],
   ["Barcode shows <code>1.23E+12</code>",
    "Displayed as scientific notation",
    "Re-import as Text"],
   ["Barcode ends in an unexpected 0",
    "Past 15 significant digits &mdash; truncated",
    "Re-import; not recoverable in place"],
   ["Size <code>1-2</code> shows as a date",
    "Converted on entry",
    "Import as Text; not reversible"],
   ["Product counts do not match the system",
    "Duplicate SKUs differing by whitespace",
    "Clean before deduplicating"],
 ]),
 howto_name="How to clean a product export safely",
 howto_desc="Set every identifier to Text on import, then verify before sending the file anywhere.",
 steps=[
  dict(h="Import with every identifier column set to Text",
       plain="Use Data > From Text/CSV and Transform Data, then set the SKU, barcode, supplier code and location columns to Text before loading.",
       body="""<p><em>Data &rarr; From Text/CSV &rarr; Transform Data</em>. Select each identifier
column in turn &mdash; SKU, barcode, supplier reference, bin location, variant code &mdash; and set
<em>Data Type &rarr; Text</em>. Leave only genuine quantities and prices as numbers.</p>
<p>The test for each column: would you ever add two of these together? If not, it is text.</p>"""),
  dict(h="Verify the barcode lengths",
       plain="Check that every barcode is the length it should be. An EAN-13 is 13 characters; anything shorter has lost leading zeros or digits.",
       body="""<p>A quick check across the whole column:</p>""" +
       fx("Is this barcode the right length?", '=IF(LEN(TRIM(A2))=13,"ok","CHECK")',
          """<p>Adjust 13 for your barcode standard &mdash; UPC-A is 12, EAN-13 is 13. Filter on
<code>CHECK</code> and compare those rows against the source file before doing anything else.</p>""")),
  dict(h="Validate the barcode check digit",
       plain="EAN and UPC barcodes end in a check digit computed from the others, so a corrupted barcode can be detected arithmetically rather than by eye.",
       body="""<p>This is the strongest check available, and almost nobody uses it. The last digit of
an EAN-13 is derived from the first twelve, so a truncated or altered barcode will fail it:</p>""" +
       fx("EAN-13 check digit",
          '=IF(MOD(10-MOD(SUMPRODUCT(--MID(A2,ROW(INDIRECT("1:12")),1),\n'
          '   {1;3;1;3;1;3;1;3;1;3;1;3}),10),10)=--RIGHT(A2,1),"valid","INVALID")',
          """<p>Weights alternate 1 and 3 across the first twelve digits; the check digit is what
brings the total to a multiple of ten. <code>INVALID</code> means the barcode has been altered
&mdash; almost always by Excel &mdash; and must come from the source file again.</p>""")),
  dict(h="Clean the description and supplier columns",
       plain="Trim and clean the text columns so that grouping by supplier or category does not split the same value into several.",
       body="""<p>Supplier names and category labels arrive with trailing spaces and inconsistent
capitalisation, which splits one supplier into three when you group. Clean them before any
summary:</p>""" +
       fx("Clean a text column", '=TRIM(CLEAN(SUBSTITUTE(B2,"[nbsp]"," ")))',
          """<p>Then group on the cleaned column, not the original.</p>""")),
  dict(h="Check for duplicate SKUs before re-importing",
       plain="Count occurrences of each SKU. A SKU appearing more than once will overwrite or reject on import to most systems.",
       body="""<p>Before the file goes back into any system:</p>""" +
       fx("Duplicate SKU check", '=IF(COUNTIF($A$2:$A$5000,A2)>1,"DUPLICATE","")',
          """<p>Run this on the <em>cleaned</em> column. Run it on the raw column and two SKUs
differing by a trailing space will not be reported as duplicates, which is how a duplicate reaches
the system in the first place.</p>""")),
 ],
 body="""<h2>Never send an Excel-touched catalogue back without checking</h2>
<p>The failure mode that costs real money is a round trip: export from the system, open in Excel to
edit prices, save, re-import. The prices are correct and a subset of the barcodes are now wrong. The
system accepts them, because they are still thirteen digits and still numeric.</p>
<p>If you must round-trip a catalogue, validate the check digits before re-importing. It takes one
column and catches exactly this.</p>
<h2>Prefer .xlsx over CSV for catalogue work</h2>
<p>An <code>.xlsx</code> stores the type of every cell, so a SKU saved as text stays text when it is
reopened. A CSV stores only characters, so every open is a fresh opportunity for Excel to guess
wrongly. Where a system offers both, take the <code>.xlsx</code>.</p>
<h2>Quantities and prices are genuinely numbers</h2>
<p>Do not over-apply the rule. Stock on hand, cost, retail price and weight are quantities you will
calculate with, and they should be numeric. It is only the identifiers that need protecting.</p>""",
 faq=[
  ("Why do my SKUs come back shorter than they should be?",
   "Excel read the column as numbers and discarded the leading zeros. Re-import the file with the SKU column set to Text; formatting afterwards cannot restore them."),
  ("Why does my barcode show as 1.23E+12?",
   "That is scientific notation, a display format only, and the value is intact. The serious problem is the separate 15-digit limit, which permanently truncates longer numbers."),
  ("How can I tell whether a barcode has been corrupted?",
   "Validate the check digit. The last digit of an EAN-13 is computed from the first twelve, so an altered barcode fails the arithmetic even when it still looks like a valid number."),
  ("Why did my size code 1-2 turn into a date?",
   "Excel converts anything shaped like a date on entry, and digits either side of a hyphen match that pattern. Import the column as Text; the conversion cannot be reversed."),
  ("Is it safe to edit a product export in Excel and re-import it?",
   "Only if every identifier column was imported as Text and you validate before sending it back. Otherwise a routine price edit can attach wrong barcodes to real products."),
  ("Should I use CSV or xlsx for catalogue work?",
   "xlsx, wherever the system offers it. It stores the type of every cell, so a SKU saved as text stays text. A CSV stores only characters, so every open is another chance to guess wrongly."),
 ],
 related=[("excel-scientific-notation-barcodes", "Excel turned my barcode into 1.23E+14"),
          ("excel-converts-text-to-dates", "Excel keeps turning my part numbers into dates"),
          ("excel-leading-zeros-disappear", "Excel keeps deleting my leading zeros")],
),

dict(
 slug="clean-crm-contact-export-excel",
 title="Cleaning a CRM Contact Export in Excel",
 description="Contact exports arrive with web-pasted non-breaking spaces, inconsistent phone formats and duplicate records. The order to clean them before any mail merge.",
 h1="Cleaning a contact export before you send anything",
 lead="A contact list assembled from a CRM, a web form and a conference badge scanner has three different ideas of what a phone number looks like, and enough invisible characters to break every deduplication you attempt.",
 category=CAT, group=GROUP,
 card_title="A CRM or contact export",
 card_blurb="Web-pasted invisible characters, phone formats, and duplicates that will not dedupe.",
 chips=["Sales + marketing", "Deduplication", "Excel + Google Sheets"],
 keywords=["clean crm export excel", "excel contact list clean", "excel phone number format",
           "excel duplicate contacts", "excel email list clean", "excel mail merge clean"],
 short_answer="""<p><strong>Clean before you deduplicate, in that order &mdash; deduplicating dirty
data leaves the duplicates in place and hides them.</strong> Contact exports are the single worst
source of non-breaking spaces, because so much of the data was pasted from web pages and email
signatures. <code>TRIM</code> alone will not remove those, so two identical-looking records survive
deduplication as separate contacts and both get the email.</p>""",
 problem_h="Why deduplication silently fails on contact data",
 problem="""<p>Every deduplication method in Excel &mdash; Remove Duplicates,
<code>COUNTIF</code>, <code>UNIQUE</code> &mdash; compares values exactly as stored. Two records for
<code>jane@example.com</code> where one has a trailing non-breaking space are two different values,
so both survive.</p>
<p>You then run Remove Duplicates, it reports &ldquo;0 duplicates found&rdquo;, and you reasonably
conclude the list is clean. It is not; the duplicates are simply invisible to the comparison. Jane
gets the email twice, which is the visible symptom of a problem that was reported as absent.</p>
<p>Contact data is unusually prone to this because of where it comes from: pasted from an email
signature, copied off a web page, typed into a form on a phone, scanned from a badge. Each of those
routes contributes its own whitespace.</p>""",
 symptoms=symptom_table([
   ["Remove Duplicates finds nothing, duplicates remain",
    "The values differ by invisible characters",
    "Clean first, then deduplicate"],
   ["Same person listed twice",
    "One record has trailing whitespace",
    "Clean the email column and re-check"],
   ["Mail merge greeting is blank",
    "The first-name field is empty or whitespace only",
    'Test with <code>=TRIM(A2)=""</code>'],
   ["Phone numbers in several formats",
    "Different capture routes, no normalisation",
    "Strip to digits and reformat"],
   ["Emails rejected by the sending tool",
    "Trailing spaces or a stray character",
    "Trim and validate before upload"],
 ]),
 howto_name="How to clean a contact export",
 howto_desc="Clean the key fields, then deduplicate, then validate before sending.",
 steps=[
  dict(h="Clean the email column first",
       plain="Trim, remove invisible characters and lower-case the email column, because it is the field you will deduplicate on.",
       body="""<p>Email is the deduplication key, so it gets cleaned first and most carefully. Email
addresses are case-insensitive in practice, so lower-casing prevents
<code>Jane@Example.com</code> and <code>jane@example.com</code> surviving as two contacts:</p>""" +
       fx("Clean an email address",
          '=LOWER(TRIM(CLEAN(SUBSTITUTE(SUBSTITUTE(A2,"[nbsp]"," "),"[zwsp]",""))))',
          """<p>Substitute the invisible characters first &mdash; <code>TRIM</code> cannot see them.
This single step is what makes the deduplication that follows actually work.</p>""")),
  dict(h="Now deduplicate on the cleaned column",
       plain="Flag duplicates using COUNTIF on the cleaned email column, not the original, and review them before deleting anything.",
       body="""<p>Flag rather than delete, so you can look before committing:</p>""" +
       fx("Flag duplicate contacts",
          '=IF(COUNTIF($D$2:$D$5000,D2)>1,"DUPLICATE","")',
          """<p>Where column D holds the cleaned email. Sort on the flag and check which record to
keep &mdash; usually the one with the most complete fields or the most recent activity date, not
simply the first.</p>""")),
  dict(h="Normalise phone numbers to digits, then reformat",
       plain="Strip every non-digit from the phone column so the numbers can be compared, then apply one consistent format.",
       body="""<p>Comparing phone numbers is impossible while one is
<code>(555) 123-4567</code> and another is <code>555.123.4567</code>. Reduce both to digits:</p>""" +
       fx("Phone number to digits only",
          '=SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(\n'
          '   TRIM(A2)," ",""),"(",""),")",""),"-",""),".","")',
          """<p>Keep the leading <code>+</code> if you have international numbers &mdash; it is the
only non-digit that carries meaning. Store the result as text, because a phone number with a leading
zero is exactly the case that loses it.</p>""")),
  dict(h="Check for empty-looking name fields",
       plain="Test the first-name column for values that are empty or contain only whitespace, so a mail merge does not send a greeting with a blank name.",
       body="""<p>A field containing only a space is not empty, and <code>ISBLANK</code> will not
catch it:</p>""" +
       fx("Is this name field really populated?", '=IF(TRIM(A2)="","MISSING","")',
          """<p>Catches genuinely empty cells, whitespace-only cells, and formula-returned empty
strings. Fix these before merging &mdash; &ldquo;Dear ,&rdquo; is worse than not sending.</p>""")),
  dict(h="Sanity-check the email addresses",
       plain="Check each address contains an @ and a dot after it, which catches the truncated and mistyped entries before an upload rejects the whole file.",
       body="""<p>Not full validation, but it catches the common damage:</p>""" +
       fx("Basic email sanity check",
          '=IF(AND(ISNUMBER(SEARCH("@",D2)),\n'
          '   ISNUMBER(SEARCH(".",MID(D2,SEARCH("@",D2),99)))),"ok","CHECK")',
          """<p>Requires an <code>@</code> and a dot somewhere after it. Filter on <code>CHECK</code>
and look at those rows &mdash; most sending platforms reject an entire upload for a handful of
malformed addresses.</p>""")),
 ],
 body="""<h2>Which duplicate to keep</h2>
<p>Remove Duplicates keeps the first occurrence and deletes the rest, which is rarely the right
choice. The first row is simply the one that happened to be highest in the file.</p>
<p>Sort by a meaningful column first &mdash; last activity date, or completeness &mdash; so that the
record you want to survive is the one at the top. Better still, flag duplicates as above and merge
the fields by hand where the count is small enough. A contact list is usually small enough.</p>
<h2>Do not lower-case anything except the email</h2>
<p>Lower-casing is safe for email because addresses are treated case-insensitively. Applying it to
names produces <code>jane mcdonald</code>, and <code>PROPER</code> then gives you
<code>Jane Mcdonald</code>. Leave name capitalisation alone unless it is clearly wrong, and fix those
rows individually.</p>
<h2>Keep the raw export</h2>
<p>Cleaning is lossy. Save the original export alongside the cleaned file so that a contact who says
their details are wrong can be traced back to what the system actually held.</p>""",
 faq=[
  ("Why does Remove Duplicates say there are no duplicates when I can see them?",
   "The values differ by characters you cannot see, usually a trailing or non-breaking space. Every deduplication method compares values exactly as stored, so clean the column first."),
  ("Why does TRIM not fix my contact data?",
   "TRIM removes ordinary spaces. Data pasted from web pages and email signatures usually contains non-breaking spaces, which are a different character that TRIM leaves in place."),
  ("Should I lower-case my contact data?",
   "Only the email column. Addresses are case-insensitive so lower-casing prevents false duplicates. Applying it to names destroys correct capitalisation that PROPER cannot reliably restore."),
  ("Which duplicate record should I keep?",
   "Not necessarily the first. Remove Duplicates keeps whichever row is highest in the file. Sort by last activity or completeness first, or flag duplicates and merge the fields by hand."),
  ("How should I store phone numbers?",
   "As text, reduced to digits with any leading + preserved. Stored as numbers they lose leading zeros, which affects most international formats."),
  ("How do I catch blank names before a mail merge?",
   "Test with =TRIM(A2)=\"\", which catches genuinely empty cells, whitespace-only cells and formula-returned empty strings. ISBLANK misses the last two."),
 ],
 related=[("excel-vlookup-non-breaking-space", "#N/A when the value is clearly there"),
          ("excel-unique-values-list", "Getting a list of unique values"),
          ("excel-return-blank-not-zero", "Returning a real blank instead of zero")],
),

dict(
 slug="clean-payroll-timesheet-export-excel",
 title="Cleaning a Payroll or Timesheet Export in Excel",
 description="Hours arrive as text, times over 24 hours display wrongly, and employee IDs lose their zeros. How to total hours correctly before they reach a payroll run.",
 h1="Cleaning a timesheet export so the hours add up",
 lead="Hours entered as <code>7:30</code>, <code>7.5</code> and <code>7h 30m</code> in the same column, a weekly total that resets past 24 hours, and employee numbers that have lost their leading zeros.",
 category=CAT, group=GROUP,
 card_title="A payroll or timesheet export",
 card_blurb="Mixed hour formats, totals resetting past 24 hours, and lost employee IDs.",
 chips=["HR + payroll", "Time formats", "Excel + Google Sheets"],
 keywords=["clean timesheet excel", "excel hours not adding up", "excel time over 24 hours",
           "excel payroll export", "excel sum hours format", "excel decimal hours"],
 short_answer="""<p><strong>If a weekly total shows 13:30 instead of 37:30, the cell format is
wrong, not the arithmetic.</strong> Excel stores time as a fraction of a day, so totals past 24 hours
roll over unless the format is <code>[h]:mm</code> &mdash; the square brackets are what let hours
accumulate. Fix the format first, then deal with mixed entry formats, then protect the employee ID
column.</p>""",
 problem_h="Three faults, and the one that is only a format",
 problem="""<p><strong>The total resets past 24 hours.</strong> Excel stores a time as a fraction of
a day: 12:00 is 0.5. Add up 37.5 hours and the underlying value is 1.5625 days, which a
<code>h:mm</code> format displays as 13:30 &mdash; correctly showing the time of day 1.5625 days in.
The value is right and only the format is wrong. <code>[h]:mm</code> tells Excel to keep counting
past 24.</p>
<p><strong>Mixed entry formats.</strong> One column containing <code>7:30</code>, <code>7.5</code>
and <code>7h 30m</code> is three different data types. <code>7:30</code> is a time value,
<code>7.5</code> is a number, <code>7h 30m</code> is text. <code>SUM</code> adds the first two
&mdash; wrongly, since 7:30 as a fraction of a day is 0.3125 while 7.5 is seven and a half
&mdash; and ignores the third.</p>
<p><strong>Employee IDs.</strong> Zero-padded, and stripped on import, exactly as everywhere else.</p>""",
 symptoms=symptom_table([
   ["Weekly total shows 13:30, not 37:30",
    "Format rolls over at 24 hours",
    "Use the <code>[h]:mm</code> format"],
   ["Total is a tiny decimal like 1.56",
    "Time is a fraction of a day; format is General",
    "Apply <code>[h]:mm</code>, or multiply by 24"],
   ["Some hours excluded from the total",
    "Those cells are text",
    "Convert them; check with <code>COUNT</code>"],
   ["7:30 and 7.5 give different results",
    "One is a time value, one is a number",
    "Standardise the column first"],
   ["Employee IDs shorter than expected",
    "Leading zeros stripped on import",
    "Re-import that column as Text"],
 ]),
 howto_name="How to clean a timesheet export",
 howto_desc="Fix the format, standardise the entries, then protect the identifiers.",
 steps=[
  dict(h="Apply the [h]:mm format to every total",
       plain="Select the total cells, open Format Cells, choose Custom, and enter [h]:mm. The square brackets let the hours accumulate past 24 instead of rolling over.",
       body="""<p><em>Format Cells &rarr; Custom</em>, and type <code>[h]:mm</code>. The square
brackets are the entire fix &mdash; they tell Excel not to roll the hours over at 24. Nothing about
the underlying values changes; they were correct all along.</p>"""),
  dict(h="Decide on one unit and convert everything to it",
       plain="Choose either decimal hours or time values for the whole column. Decimal hours are usually easier because payroll systems expect them.",
       body="""<p>Do not mix. Decimal hours are usually the better target, because that is what most
payroll systems expect and it removes the fraction-of-a-day confusion entirely:</p>""" +
       fx("Time value to decimal hours", '=A2*24',
          """<p>Format the result as a plain number with two decimals. 7:30 becomes 7.5. To go back
the other way, divide by 24 and format as <code>[h]:mm</code>.</p>""")),
  dict(h="Find the entries that are text",
       plain="Compare COUNT with COUNTA over the hours column. Any difference is entries stored as text that are being excluded from the total.",
       body="""<p>Text entries such as <code>7h 30m</code> are silently skipped:</p>""" +
       fx("How many hour entries are text?", '=COUNTA(C2:C500)-COUNT(C2:C500)',
          """<p>Anything above zero needs looking at. Filter to those rows &mdash; they usually share
a format, because they came from one person or one system, so they can be fixed as a group.</p>""")),
  dict(h="Convert a written duration to hours",
       plain="For entries like 7h 30m, extract the hours and minutes and combine them into decimal hours.",
       body="""<p>Where the text form is consistent, it can be parsed:</p>""" +
       fx("Parse 7h 30m into decimal hours",
          '=IFERROR(VALUE(LEFT(A2,SEARCH("h",A2)-1))\n'
          ' + VALUE(MID(A2,SEARCH("h",A2)+1,SEARCH("m",A2)-SEARCH("h",A2)-1))/60,"CHECK")',
          """<p>Takes what is before the <code>h</code> as hours and what is between <code>h</code>
and <code>m</code> as minutes. Anything not matching that shape returns <code>CHECK</code> for manual
review rather than erroring.</p>""")),
  dict(h="Protect the employee ID column on import",
       plain="Re-import the file with the employee number column set to Text, so zero-padded IDs survive and still match the HR system.",
       body="""<p>Same rule as every other identifier: <em>Transform Data &rarr; Data Type &rarr;
Text</em> on the employee number. A payroll file whose IDs no longer match the HR system is worse
than no file, because the mismatch is not obvious until someone is paid wrongly.</p>"""),
 ],
 body="""<h2>Why 7:30 plus 7.5 is not 15</h2>
<p>Worth understanding once, because it explains most timesheet confusion. <code>7:30</code> entered
as a time is stored as 0.3125 &mdash; seven and a half twenty-fourths of a day. <code>7.5</code>
entered as a number is stored as 7.5. Adding them gives 7.8125, which formatted as time is 18:45 and
formatted as a number is 7.8125. Neither is 15 hours.</p>
<p>This is why standardising the column is step two and not an optional tidy-up.</p>
<h2>Overtime thresholds need decimal hours</h2>
<p>Any calculation that compares hours against a threshold is far easier in decimal:</p>
""" + fx("Hours over 40", '=MAX(0,C2-40)',
"""<p>With <code>C2</code> in decimal hours. Attempting the same against time values means comparing
against <code>40/24</code>, which works but is a reliable source of mistakes in a file other people
will maintain.</p>""") + """
<h2>Rounding rules belong in the formula, visibly</h2>
<p>If your organisation rounds to the nearest quarter hour, write it explicitly rather than relying on
display formatting:</p>
""" + fx("Round to the nearest quarter hour", '=MROUND(C2,0.25)',
"""<p>Formatting alone would leave the underlying value unrounded, so the total would not match the
sum of the displayed rows &mdash; the kind of discrepancy that is very hard to explain to someone
querying their pay.</p>""") + """
<h2>Keep the raw export</h2>
<p>Payroll figures get queried, sometimes months later. Keep the untouched export beside the cleaned
version so that any figure can be traced back to what the time system actually recorded.</p>""",
 faq=[
  ("Why does my weekly total show 13:30 instead of 37:30?",
   "Excel stores time as a fraction of a day, so the display rolls over at 24 hours. The value is correct — apply the custom format [h]:mm, where the square brackets let hours accumulate past 24."),
  ("Why do 7:30 and 7.5 give different results?",
   "7:30 entered as a time is stored as 0.3125 of a day, while 7.5 is the number seven and a half. They are different data types and cannot be added meaningfully until the column is standardised."),
  ("Should I use decimal hours or time values?",
   "Decimal hours for anything that feeds payroll. Most payroll systems expect them, threshold comparisons are much simpler, and the fraction-of-a-day confusion disappears."),
  ("How do I convert a time value to decimal hours?",
   "Multiply by 24 and format the result as a plain number. To convert back, divide by 24 and format as [h]:mm."),
  ("Why are some hours missing from my total?",
   "Those entries are text — typically written forms like 7h 30m — and SUM skips them. Compare COUNTA with COUNT over the column to see how many."),
  ("Where should rounding rules live?",
   "In the formula, using MROUND, not in the cell format. Formatting alone leaves the underlying value unrounded, so the total will not match the sum of the displayed rows."),
 ],
 related=[("excel-numbers-stored-as-text", "SUM is ignoring half my column"),
          ("excel-leading-zeros-disappear", "Excel keeps deleting my leading zeros"),
          ("excel-sum-visible-rows-only", "Summing only the rows a filter left visible")],
),
]
