#!/usr/bin/env python3
"""Two diagrams per guide: what goes wrong, and what to do instead.

Same engine as the product pages (tools/fieldnotes/diagrams.py via palette.py, which
re-skins it green), so the geometry lives in one place and a long label cannot silently
overflow its box on one page in twenty-three.

The pairing is fixed and deliberate:

  chain(..., fail_at=N)   the journey a value takes, with the step where it breaks
                          marked red. This is "the problem" — it shows that the damage
                          happens at a specific moment, usually before you touched
                          anything, which is the point most people miss.
  branch(...)             one decision sorted into outcomes, green for the good path
                          and red for the bad one. This is "what to do instead".

Words are kept short on purpose. A box label is read in about a second, so anything that
needs a comma belongs in the caption, not in the box.
"""
from palette import branch, chain

V = {}


def _v(slug, *, p_aria, p_cap, steps, fail_at, f_aria, f_cap, source, outcomes):
    V[slug] = {
        "problem": chain(f"{slug}-p", p_aria, p_cap, steps, fail_at=fail_at),
        "fix": branch(f"{slug}-f", f_aria, f_cap, source, outcomes),
    }


# ── A · when Excel changes your data ────────────────────────────────────────────
_v("excel-leading-zeros-disappear",
   p_aria="How a zero-padded code loses its zero when a file is opened",
   p_cap="The zero is gone before the file is on screen. Nothing warns you, because as far "
         "as Excel is concerned it did the ordinary thing.",
   steps=[("File on disk", "01234"), ("Excel opens it", "guesses the type"),
          ("Reads as number", "1234"), ("You format as text", "still 1234")],
   fail_at=1,
   f_aria="Choosing the column type before the value arrives, or after",
   f_cap="The same decision, made at two different moments. Only one of them can work.",
   source=("Set the column type", "before or after the data lands?"),
   outcomes=[("Set to Text on import", "the zero is never dropped", "good"),
             ("Formatted after opening", "nothing left to restore", "bad")])

_v("excel-csv-utf8-mojibake",
   p_aria="How a UTF-8 file becomes mojibake",
   p_cap="Two bytes meaning one letter get read as two letters. The file never changed — "
         "until you save, at which point the wrong letters become real.",
   steps=[("File is UTF-8", "ñ = two bytes"), ("Excel guesses", "Windows-1252"),
          ("Two letters shown", "Ã±"), ("You save", "now truly broken")],
   fail_at=1,
   f_aria="Setting the file origin on import",
   f_cap="One dropdown in the import dialog decides this.",
   source=("Opening the CSV", "how does Excel read the bytes?"),
   outcomes=[("File Origin 65001", "read as UTF-8, accents intact", "good"),
             ("Double-clicked", "guessed, and usually wrong", "bad")])

_v("excel-converts-text-to-dates",
   p_aria="How a part number becomes a date",
   p_cap="The code is replaced by a number counting days. Nothing keeps the text you typed.",
   steps=[("You have", "SEP1"), ("Excel sees", "a month and a day"),
          ("Stores", "45901"), ("Shows", "01-Sep")],
   fail_at=1,
   f_aria="Where the column type is decided",
   f_cap="There is no repair step on the bad path — that is what makes this one different.",
   source=("A code that looks like a date", "what is the column set to?"),
   outcomes=[("Column is Text", "stays the code you typed", "good"),
             ("Column is General", "becomes a date, permanently", "bad")])

_v("excel-vlookup-non-breaking-space",
   p_aria="How an invisible character breaks an exact match",
   p_cap="Both cells look identical on screen. One has a character you cannot see, so the "
         "match fails and the row is reported as missing.",
   steps=[("Copied from a web page", "Smith + hidden space"), ("Looks identical", "on screen"),
          ("Compared letter by letter", "not the same"), ("Lookup", "#N/A")],
   fail_at=2,
   f_aria="Cleaning in the right order",
   f_cap="TRIM removes ordinary spaces only. The hidden one has to be swapped out first.",
   source=("Cleaning the column", "which order?"),
   outcomes=[("Swap hidden spaces, then TRIM", "the match works", "good"),
             ("TRIM on its own", "hidden space stays, still fails", "bad")])

_v("excel-csv-all-in-column-a",
   p_aria="How a whole file lands in one column",
   p_cap="The file does not say which separator it uses, so Excel uses the one your region "
         "prefers. The file is fine; the guess is not.",
   steps=[("File uses", "semicolons"), ("Your Excel expects", "commas"),
          ("Nothing to split on", "one long line"), ("Result", "all in column A")],
   fail_at=1,
   f_aria="Choosing the separator per file or per machine",
   f_cap="One of these fixes today's file. The other changes every file you ever open or save.",
   source=("Wrong separator", "where do you fix it?"),
   outcomes=[("Pick it in the import dialog", "this file only", "good"),
             ("Change Windows settings", "breaks every other file", "bad")])

_v("excel-numbers-stored-as-text",
   p_aria="How SUM skips part of a column",
   p_cap="The skipped rows look exactly like the counted ones. That is why the wrong total "
         "is more dangerous than no total.",
   steps=[("Export adds", "$ and commas"), ("Cell becomes", "text"),
          ("SUM only adds numbers", "text ignored"), ("Total", "too low, looks fine")],
   fail_at=1,
   f_aria="Whether a column of digits should be a number at all",
   f_cap="The test is simple: would you ever add two of them together?",
   source=("A column of digits", "would you do arithmetic on it?"),
   outcomes=[("Yes — money, counts", "make it a number", "good"),
             ("No — IDs, codes", "keep it text", "good"),
             ("Convert everything", "IDs lose their zeros", "bad")])

_v("excel-scientific-notation-barcodes",
   p_aria="How a long barcode loses its last digits",
   p_cap="The short display is harmless. The missing digits underneath are not, and no "
         "formula brings them back.",
   steps=[("Barcode", "16 digits"), ("Read as a number", "15 digits kept"),
          ("Rest replaced", "with zeros"), ("Shown", "1.23E+14")],
   fail_at=1,
   f_aria="Two different problems with the same symptom",
   f_cap="Only one of these can be undone, which is why they need telling apart.",
   source=("A long number looks wrong", "which problem is it?"),
   outcomes=[("Scientific notation", "display only — widen the column", "good"),
             ("Past 15 digits", "digits gone — re-import as Text", "bad")])

# ── B · formulas that do not behave as they read ────────────────────────────────
_v("excel-absolute-relative-references",
   p_aria="How a copied formula changes what it points at",
   p_cap="The formula is doing what it was told. It was told to look one row down each time.",
   steps=[("Row 2", "=B2*F1"), ("Copy down", "everything shifts"),
          ("Row 3 reads", "=B3*F2"), ("F2 is empty", "wrong answer")],
   fail_at=1,
   f_aria="Which part of a reference is pinned",
   f_cap="The dollar sign locks whatever comes straight after it.",
   source=("Copying a formula", "what must stay still?"),
   outcomes=[("$F$1 — pinned", "always the same cell", "good"),
             ("F1 — not pinned", "moves with the formula", "bad")])

_v("excel-formulas-not-updating",
   p_aria="How one workbook stops every other one recalculating",
   p_cap="Nothing you did caused this. The setting travels inside the file you opened first.",
   steps=[("You open", "someone's big model"), ("It is set to", "Manual"),
          ("Excel applies it", "to the whole session"), ("Your sheet", "goes stale too")],
   fail_at=2,
   f_aria="Automatic against manual calculation",
   f_cap="Manual is a real choice for a slow workbook — it just needs saying out loud.",
   source=("Calculation mode", "who decides when to recalculate?"),
   outcomes=[("Automatic", "updates as you type", "good"),
             ("Manual", "only on F9 or save", "bad")])

_v("excel-unique-values-list",
   p_aria="How deduplicating can delete the wrong thing",
   p_cap="Remove Duplicates works in place. Run it on your only copy and there is nothing "
         "to go back to.",
   steps=[("Your only copy", "5,000 rows"), ("Remove Duplicates", "works in place"),
          ("Rows deleted", "permanently"), ("Saved and closed", "no undo")],
   fail_at=1,
   f_aria="Three ways to get a distinct list",
   f_cap="Two of these leave your data exactly where it was.",
   source=("You need distinct values", "which method?"),
   outcomes=[("UNIQUE formula", "live, never touches the source", "good"),
             ("Advanced Filter", "writes a copy elsewhere", "good"),
             ("Remove Duplicates", "deletes rows in place", "bad")])

_v("excel-compare-two-lists",
   p_aria="How a comparison reports a row as missing when it is not",
   p_cap="The row is sitting in the other list. The comparison cannot see it because the "
         "two values are not byte-for-byte identical.",
   steps=[("List A", "Acme Ltd"), ("List B", "Acme Ltd + space"),
          ("Compared exactly", "not equal"), ("Reported", "MISSING")],
   fail_at=2,
   f_aria="Comparing in one direction or both",
   f_cap="These are two different questions, and a reconciliation needs both answers.",
   source=("Two lists that disagree", "what are you asking?"),
   outcomes=[("In A, not in B", "things you are missing", "good"),
             ("In B, not in A", "things that should not exist", "good"),
             ("Only checking one way", "half the answer", "bad")])

_v("excel-sumifs-vs-pivot-table",
   p_aria="How a pivot table shows a number that is out of date",
   p_cap="A pivot holds the answer it worked out last time. It does not notice new rows on "
         "its own.",
   steps=[("Data changes", "new rows added"), ("Pivot still shows", "the old answer"),
          ("Nobody refreshes", "no warning shown"), ("Report", "quietly wrong")],
   fail_at=1,
   f_aria="Choosing between a formula and a pivot table",
   f_cap="Same numbers, different jobs. Pick by whether you control the layout.",
   source=("Totals by category", "what is the total for?"),
   outcomes=[("A fixed report", "SUMIFS — updates itself", "good"),
             ("Exploring the data", "pivot table — drag and look", "good")])

_v("excel-join-two-sheets-lookup",
   p_aria="How VLOOKUP starts returning the wrong column",
   p_cap="No error appears. The formula still works, it just answers with a different field.",
   steps=[("VLOOKUP asks for", "column 3"), ("Someone inserts", "a new column"),
          ("Column 3 is now", "a different field"), ("Result", "wrong, no error")],
   fail_at=1,
   f_aria="Naming the return column by position or by reference",
   f_cap="This is the whole reason to move off VLOOKUP.",
   source=("Pulling a column across", "how is it named?"),
   outcomes=[("XLOOKUP or INDEX/MATCH", "by reference — moves with the column", "good"),
             ("VLOOKUP", "by number — breaks silently", "bad")])

_v("excel-sum-visible-rows-only",
   p_aria="How a total ignores the filter you just applied",
   p_cap="The number is plausible and it is answering a different question from the one "
         "you asked.",
   steps=[("5,000 rows", "all suppliers"), ("You filter", "to one supplier"),
          ("SUM cannot see filters", "adds all 5,000"), ("You use", "the wrong total")],
   fail_at=2,
   f_aria="Which totalling function respects a filter",
   f_cap="Add 100 to the code and manually hidden rows are excluded too.",
   source=("Totalling a filtered list", "which function?"),
   outcomes=[("SUBTOTAL(109,…)", "visible rows only", "good"),
             ("AGGREGATE(9,7,…)", "visible rows, ignores errors", "good"),
             ("SUM", "everything, filter or not", "bad")])

_v("excel-return-blank-not-zero",
   p_aria="How an empty-looking cell becomes a zero on a chart",
   p_cap="The cell looks blank in the sheet and reads as zero in the chart, so an unfinished "
         "year looks like a collapse.",
   steps=[('Formula returns', '""'), ("Cell looks", "empty"),
          ("Chart reads it", "as a value"), ("Line", "drops to zero")],
   fail_at=2,
   f_aria="What to return when there is nothing to show",
   f_cap="Only one of these makes a chart break the line.",
   source=("Nothing to show", "what should the formula return?"),
   outcomes=[("NA()", "chart leaves a gap", "good"),
             ('""', "chart plots a zero", "bad")])

_v("excel-count-functions-explained",
   p_aria="How COUNT reports fewer rows than the column holds",
   p_cap="The gap between two counting functions is the fastest way to find text pretending "
         "to be numbers.",
   steps=[("500 rows", "all look numeric"), ("40 are text", "from the export"),
          ("COUNT counts numbers", "returns 460"), ("You assume", "40 rows are empty")],
   fail_at=2,
   f_aria="What each counting function includes",
   f_cap="Subtract one from the other and the difference is the problem.",
   source=("How many are there?", "what counts as present?"),
   outcomes=[("COUNT", "numbers only", "plain"),
             ("COUNTA", "anything not empty", "plain"),
             ("COUNTA minus COUNT", "how many are secretly text", "good")])

_v("excel-negative-number-squared",
   p_aria="How Excel reads a minus sign in front of a power",
   p_cap="Excel is consistent with itself. It just disagrees with the maths textbook, and "
         "with most programming languages.",
   steps=[("You write", "-3^2"), ("Excel applies", "the minus first"),
          ("Works out", "(-3)^2"), ("Answer", "9, not -9")],
   fail_at=1,
   f_aria="Bracketing an exponent",
   f_cap="Brackets cost nothing and remove the question entirely.",
   source=("A minus next to a power", "how do you write it?"),
   outcomes=[("-(3^2)", "-9, as intended", "good"),
             ("-3^2", "9, and no warning", "bad")])

_v("excel-apply-formula-entire-column",
   p_aria="How a fill stops part way down a column",
   p_cap="Double-clicking fills to the end of the column beside it, not to the end of your data.",
   steps=[("Double-click the handle", "fills down"), ("Column A has a gap", "at row 400"),
          ("Fill stops", "at row 399"), ("Rows 400+", "silently empty")],
   fail_at=1,
   f_aria="Which method keeps working as rows are added",
   f_cap="Only one of these covers the rows somebody adds next month.",
   source=("Filling a formula down", "which method?"),
   outcomes=[("Table (Ctrl+T)", "new rows inherit it", "good"),
             ("Ctrl+D on a range", "exactly what you selected", "good"),
             ("Double-click the handle", "stops at the first gap", "bad")])

# ── C · cleaning a real export ──────────────────────────────────────────────────
_v("clean-bank-statement-export-excel",
   p_aria="How bracketed negatives flip a bank balance",
   p_cap="Every debit is added instead of subtracted, so the balance is out by exactly twice "
         "the debits — an oddly round number that is hard to trace.",
   steps=[("Bank writes a debit", "(500)"), ("Excel reads", "text"),
          ("Converted without care", "+500"), ("Balance", "out by twice the debits")],
   fail_at=2,
   f_aria="The order to clean a bank export in",
   f_cap="Dates first: reconciling by month against wrong dates wastes the whole exercise.",
   source=("A bank export", "what do you fix first?"),
   outcomes=[("1 · Dates, with the right locale", "so months are right", "good"),
             ("2 · Amounts, brackets included", "so the total is right", "good"),
             ("3 · Descriptions", "so grouping works", "good")])

_v("clean-student-list-excel",
   p_aria="How lost leading zeros hide part of a class",
   p_cap="Students numbered under 1000 drop out and the rest match, so it looks like missing "
         "students rather than a formatting problem.",
   steps=[("Student number", "004512"), ("Read as a number", "4512"),
          ("Other system holds", "004512"), ("Merge", "student not found")],
   fail_at=1,
   f_aria="Which field to match two class lists on",
   f_cap="Names change. Numbers do not, which is why the ID column is worth protecting first.",
   source=("Matching this term to last", "match on what?"),
   outcomes=[("Student ID", "stable, unique", "good"),
             ("Name", "spellings change, and repeat", "bad")])

_v("clean-inventory-sku-export-excel",
   p_aria="How a routine price edit attaches the wrong barcode",
   p_cap="The file still looks like a product list, and the system accepts it, because the "
         "barcode is still thirteen digits.",
   steps=[("Export the catalogue", "to edit prices"), ("Excel reads barcodes", "as numbers"),
          ("Digits changed", "silently"), ("Re-import", "wrong barcode, real product")],
   fail_at=1,
   f_aria="Checking a barcode before sending it back",
   f_cap="The last digit is worked out from the others, so a damaged barcode can be caught "
         "by arithmetic rather than by eye.",
   source=("A barcode after editing", "how do you know it is intact?"),
   outcomes=[("Check digit still matches", "safe to re-import", "good"),
             ("Check digit fails", "Excel changed it — re-export", "bad")])

_v("clean-crm-contact-export-excel",
   p_aria="How deduplication reports no duplicates and sends twice",
   p_cap="The tool reported success. It compared two values that differ by a character "
         "nobody can see.",
   steps=[("Two rows", "same email"), ("One has a hidden space", "from a web paste"),
          ("Compared exactly", "not equal"), ("Result", "0 duplicates, sent twice")],
   fail_at=2,
   f_aria="Cleaning before deduplicating, or after",
   f_cap="The order decides whether the deduplication can see anything at all.",
   source=("A contact list", "clean first or dedupe first?"),
   outcomes=[("Clean, then dedupe", "duplicates are visible", "good"),
             ("Dedupe first", "reports none, keeps both", "bad")])

_v("clean-payroll-timesheet-export-excel",
   p_aria="How a weekly total rolls over at 24 hours",
   p_cap="Nothing is wrong with the arithmetic. The cell is showing a time of day instead of "
         "a length of time.",
   steps=[("Hours add to", "37.5"), ("Stored as", "1.56 days"),
          ("Format is h:mm", "rolls at 24"), ("Shows", "13:30")],
   fail_at=2,
   f_aria="Which unit to keep hours in",
   f_cap="Decimal hours are what payroll systems expect, and thresholds are far easier to check.",
   source=("Hours in a timesheet", "which unit?"),
   outcomes=[("Decimal hours (7.5)", "easy to total and compare", "good"),
             ("Time values (7:30)", "needs [h]:mm to total", "plain"),
             ("Both in one column", "cannot be added at all", "bad")])


# ── D · Power Query ─────────────────────────────────────────────────────────────
_v("excel-power-query-unpivot",
   p_aria="Why a column per month blocks every tool",
   p_cap="The month is written in the heading, and a formula cannot read a heading the way it reads a cell.",
   steps=[("A column per month", "12 of them"), ("Month is a heading", "not data"),
          ("Formulas cannot read it", "one per column"), ("January arrives", "edit all 12")],
   fail_at=1,
   f_aria="Where the month should live",
   f_cap="Unpivot turns headings into values. Three columns, and every tool starts working.",
   source=("Where is the month?", "heading or data?"),
   outcomes=[("A column of month values", "filter, pivot, one SUMIFS", "good"),
             ("A column per month", "twelve formulas, growing sideways", "bad")])

_v("excel-power-query-parameter-cell",
   p_aria="Why a query cannot point at a cell",
   p_cap="Power Query works in tables and steps. It has no idea what B1 is.",
   steps=[("You want", "filter on B1"), ("Power Query sees", "tables, not cells"),
          ("No reference to type", "nowhere to put it"), ("So the value", "gets hard-coded")],
   fail_at=2,
   f_aria="Giving the query something it understands",
   f_cap="A one-cell table is still a table. Drill down and it becomes the value itself.",
   source=("A value the query needs", "how do you hand it over?"),
   outcomes=[("One-row table, drilled down", "anyone can change the cell", "good"),
             ("Typed into the step", "means opening the editor to change", "bad")])

_v("excel-power-query-combine-files-folder",
   p_aria="Why copying files into one sheet does not last",
   p_cap="It works exactly once, and it loses the one thing you need when a number looks wrong.",
   steps=[("40 files", "same shape"), ("Open and copy each", "an afternoon"),
          ("Source is lost", "which file was that?"), ("Next month", "do it again")],
   fail_at=2,
   f_aria="Pointing at the folder instead of the files",
   f_cap="Clean the sample once and every file is cleaned, including next month's.",
   source=("Combining many files", "point at what?"),
   outcomes=[("The folder", "new files included on refresh", "good"),
             ("Each file by hand", "redone every month", "bad")])

_v("excel-power-query-merge-join",
   p_aria="What a lookup cannot answer",
   p_cap="A lookup gives you #N/A and leaves you to work out what it means.",
   steps=[("Two lists", "should agree"), ("Lookup each key", "one value back"),
          ("Unmatched rows", "just #N/A"), ("The question", "still unanswered")],
   fail_at=2,
   f_aria="Choosing the join that answers the question",
   f_cap="The anti join returns the rows that did not match, as a table. No formula does that.",
   source=("What are you asking?", "matches, or misses?"),
   outcomes=[("Left outer", "everything, plus matches where they exist", "good"),
             ("Left anti", "only the rows with no match", "good"),
             ("A column of lookups", "recalculated on every change", "bad")])

_v("excel-power-query-refresh-load-settings",
   p_aria="Why the workbook grew to forty megabytes",
   p_cap="Excel stores a full copy of every loaded query result, including the ones nobody reads.",
   steps=[("6 queries built", "one final output"), ("All set to load", "default"),
          ("6 copies stored", "in the file"), ("File size", "40 MB")],
   fail_at=1,
   f_aria="Which queries should write a sheet",
   f_cap="Only load what a person actually reads.",
   source=("Does anyone read this query?", "or does it just feed another?"),
   outcomes=[("Read by a person", "load it to a sheet", "good"),
             ("Feeds another query", "Only Create Connection", "good"),
             ("Everything loaded", "a copy of each stored in the file", "bad")])

_v("excel-power-query-vs-power-pivot",
   p_aria="Where each tool sits in the flow",
   p_cap="Data moves one way, which is why learning them in that order makes sense.",
   steps=[("Source files", "messy"), ("Power Query", "gets it in, cleans it"),
          ("Power Pivot", "relates tables, measures"), ("Pivot table", "the answer")],
   fail_at=None,
   f_aria="Choosing by the problem you have",
   f_cap="Most people have the first problem. Many never have the second.",
   source=("Where is the pain?", "getting it in, or calculating?"),
   outcomes=[("Getting it usable", "Power Query", "good"),
             ("Calculating across tables", "Power Pivot", "good"),
             ("One tidy table", "neither — a pivot table is enough", "plain")])

# ── E · dynamic arrays and text ─────────────────────────────────────────────────
_v("excel-spill-error",
   p_aria="Why a formula refuses to write its answer",
   p_cap="Excel will not overwrite your data to make room. The error is it protecting something.",
   steps=[("One formula", "many answers"), ("Needs empty cells", "to write into"),
          ("Something is there", "often invisible"), ("Result", "#SPILL!")],
   fail_at=2,
   f_aria="What is usually in the way",
   f_cap="The dashed border shows the area it needs. The obstruction is inside it.",
   source=("Something blocks the spill", "what is it?"),
   outcomes=[("A space or stray character", "select the range and delete", "good"),
             ("A merged cell", "unmerge it", "good"),
             ("Inside a table", "tables cannot spill — move it out", "bad")])

_v("excel-filter-function",
   p_aria="Why a filtered list shows zeros",
   p_cap="Nothing is wrong. It is Excel's ordinary treatment of empty cells, finally visible.",
   steps=[("Source has blanks", "no phone number"), ("FILTER reads values", "not cells"),
          ("An empty cell is", "zero"), ("Your list shows", "0")],
   fail_at=2,
   f_aria="Combining two conditions",
   f_cap="AND and OR collapse the whole range to one answer, so FILTER returns everything or nothing.",
   source=("Two conditions", "how do you join them?"),
   outcomes=[("* for AND, + for OR", "one test per row", "good"),
             ("The AND function", "one answer for the whole range", "bad")])

_v("excel-sort-sortby",
   p_aria="Why ribbon sorting keeps needing redoing",
   p_cap="It rearranges the actual rows, once, and the original order is gone with it.",
   steps=[("Sort from the ribbon", "rows rearranged"), ("A row is added", "sits at the bottom"),
          ("Sort again", "and again"), ("Original order", "unrecoverable")],
   fail_at=1,
   f_aria="Sorting as an action or as a formula",
   f_cap="One rearranges your data. The other makes a copy that keeps itself in order.",
   source=("You need it in order", "action or formula?"),
   outcomes=[("SORT formula", "a live copy, data untouched", "good"),
             ("Ribbon sort", "redone every time, order lost", "bad")])

_v("excel-lambda-named-functions",
   p_aria="What happens to a formula that gets copied around",
   p_cap="Six copies become six slightly different formulas, and the one you miss is the wrong one.",
   steps=[("One clever formula", "written once"), ("Copied to 6 places", "for reuse"),
          ("Each edited separately", "they drift"), ("Rule changes", "find all six")],
   fail_at=2,
   f_aria="Two ways to reuse a calculation",
   f_cap="Both reuse the logic. Only one keeps the file openable everywhere.",
   source=("Reusing a calculation", "how?"),
   outcomes=[("LAMBDA, named", "one definition, file stays .xlsx", "good"),
             ("A VBA function", "file becomes .xlsm, may be blocked", "bad")])

_v("excel-byrow-bycol",
   p_aria="How a helper column goes quietly wrong",
   p_cap="Nothing errors. The last rows are simply blank, and the total below them is too small.",
   steps=[("Helper column", "filled down to row 500"), ("Rows added", "to 640"),
          ("Nobody filled it", "no warning"), ("Total", "quietly short")],
   fail_at=2,
   f_aria="Helper column or one formula",
   f_cap="Neither is always right. Pick by whether a person needs to see the per-row number.",
   source=("One number per row", "where should it live?"),
   outcomes=[("BYROW, one formula", "resizes itself, nothing to fill", "good"),
             ("A helper column", "visible and easy to check", "plain"),
             ("A helper column nobody fills", "short totals, silently", "bad")])

_v("excel-regex-functions",
   p_aria="Why regex advice for Excel is mostly out of date",
   p_cap="The functions arrived in 2024. Almost everything written before that says you need a macro.",
   steps=[("You search online", "regex in Excel"), ("Advice says", "use VBA"),
          ("File becomes .xlsm", "may be blocked"), ("Meanwhile", "three functions exist")],
   fail_at=1,
   f_aria="Which tool for pulling a pattern out of text",
   f_cap="Describe the shape of the text rather than the text itself.",
   source=("A code buried in messy text", "how do you get it?"),
   outcomes=[("REGEXEXTRACT", "one formula, no macro", "good"),
             ("Power Query extract", "works on older Excel too", "good"),
             ("Forty nested SUBSTITUTEs", "unreadable and brittle", "bad")])

_v("excel-extract-numbers-from-text",
   p_aria="What stripping non-digits does to a real number",
   p_cap="The point and the minus sign are not digits either, so they go too.",
   steps=[("You have", "-12.50"), ("Strip non-digits", "[^0-9]"),
          ("Point and minus gone", "with them"), ("Result", "1250")],
   fail_at=1,
   f_aria="Deciding what you actually want",
   f_cap="Answer this before picking a method, or the method answers it for you.",
   source=("The number in the text", "which number?"),
   outcomes=[("The first run of digits", "usually what you meant", "good"),
             ("Keep the point and minus", "for real amounts", "good"),
             ("Every digit joined up", "4471 and 3 become 44713", "bad")])

_v("excel-textsplit-functions",
   p_aria="Why Text to Columns stops covering your data",
   p_cap="It ran once, on the rows that existed at the time. Nothing tells you it has stopped.",
   steps=[("Text to Columns", "splits 500 rows"), ("40 rows added", "later"),
          ("They are not split", "no warning"), ("Everything downstream", "misses them")],
   fail_at=2,
   f_aria="Splitting as an action or as a formula",
   f_cap="One is done to your data. The other keeps producing a copy.",
   source=("Splitting a column", "once, or every time?"),
   outcomes=[("TEXTSPLIT formula", "covers rows added later", "good"),
             ("Text to Columns", "a one-off, and it overwrites rightwards", "bad")])

# ── F · formatting, lookups, recovery ───────────────────────────────────────────
_v("excel-conditional-format-another-cell",
   p_aria="How one rule is applied to a whole range",
   p_cap="Excel writes your rule for the top-left cell and shifts it for every other one, exactly like dragging.",
   steps=[("You write", "=C2=\"Overdue\""), ("Applied to A2", "as written"),
          ("Shifted for B2", "now tests D2"), ("Colours", "look random")],
   fail_at=2,
   f_aria="What the dollar sign pins",
   f_cap="Pin the column, free the row, and the whole row follows column C.",
   source=("Which part must not move?", "column, row, or both?"),
   outcomes=[("$C2 — column pinned", "whole row follows column C", "good"),
             ("$C$2 — both pinned", "only colours where that one cell matches", "bad"),
             ("C2 — nothing pinned", "every cell tests a different column", "bad")])

_v("excel-highlight-duplicates",
   p_aria="What the built-in duplicate rule colours",
   p_cap="It marks the original as well, which is unhelpful when you are deciding what to delete.",
   steps=[("Three copies", "of one value"), ("Built-in rule", "colours duplicates"),
          ("All three coloured", "including the first"), ("Which to keep?", "no answer")],
   fail_at=2,
   f_aria="Counting all of them, or only what came before",
   f_cap="A range that grows as the rule walks down counts only the earlier rows.",
   source=("COUNTIF range", "fixed, or growing?"),
   outcomes=[("$A$2:$A2 — growing", "flags the extras only", "good"),
             ("$A$2:$A$500 — fixed", "flags every copy", "plain")])

_v("excel-conditional-format-ranges-changing",
   p_aria="How one formatting rule becomes forty",
   p_cap="Formatting travels with a cell. Excel keeps both copies whenever it cannot merge them.",
   steps=[("One rule", "over the range"), ("Cells copied and pasted", "inside it"),
          ("Pasted cells bring a copy", "of the rule"), ("Cannot merge", "so both are kept")],
   fail_at=2,
   f_aria="How to move data inside a formatted range",
   f_cap="Values carry no formatting, so they cannot carry a rule.",
   source=("Pasting inside a formatted range", "paste what?"),
   outcomes=[("Paste Special → Values", "no rule travels", "good"),
             ("An ordinary paste", "splits the rule again", "bad")])

_v("excel-last-match-lookup",
   p_aria="Why a lookup on a price history gives an old price",
   p_cap="First match is the right default for a reference table and the wrong one for a log.",
   steps=[("Three rows", "same product"), ("Price changed twice", "newest at the bottom"),
          ("VLOOKUP scans down", "stops at the first"), ("You get", "the oldest price")],
   fail_at=2,
   f_aria="Which end to search from",
   f_cap="On a log, the row you want is the last one, not the first.",
   source=("Which match do you want?", "first or last?"),
   outcomes=[("Search from the bottom", "the current price", "good"),
             ("Search from the top", "the price from two years ago", "bad")])

_v("excel-last-non-empty-cell",
   p_aria="Why counting rows finds the wrong value",
   p_cap="COUNTA counts values, not positions, so one gap puts the answer a row early.",
   steps=[("Column with a gap", "one week missed"), ("COUNTA counts values", "not rows"),
          ("Count is one short", "of the real last row"), ("You get", "the previous value")],
   fail_at=2,
   f_aria="Searching for a value or counting positions",
   f_cap="Look for the last value rather than the last position and gaps stop mattering.",
   source=("Finding the end of a column", "count, or search?"),
   outcomes=[("Search for the last value", "gaps are skipped", "good"),
             ("Count the values", "one gap and it is wrong", "bad")])

_v("excel-sheet-name-in-cell",
   p_aria="Why every tab shows the same name",
   p_cap="Without a cell reference, CELL describes whichever sheet was last clicked.",
   steps=[("CELL(\"filename\")", "no reference given"), ("Reports the ACTIVE sheet", "not this one"),
          ("You click a tab", "all twelve change"), ("Every heading", "says the same month")],
   fail_at=1,
   f_aria="The two conditions nobody mentions",
   f_cap="Both have to be true or the formula looks broken for reasons it never explains.",
   source=("The formula returns nothing useful", "why?"),
   outcomes=[("Saved, and CELL(...,A1)", "the tab's own name", "good"),
             ("Never saved", "returns an empty string", "bad"),
             ("No cell reference", "reports the last active tab", "bad")])

_v("excel-column-number-to-letter",
   p_aria="Why column letters are not simple counting",
   p_cap="It looks like base 26 and is not, because there is no zero digit.",
   steps=[("Column 26", "Z"), ("Column 27", "AA, not A0"),
          ("Column 703", "AAA"), ("Writing it yourself", "wrong at the boundaries")],
   fail_at=2,
   f_aria="Whether you need the letter at all",
   f_cap="Most of the time the letter is a means to an end that does not need it.",
   source=("You have a column number", "what for?"),
   outcomes=[("To fetch a value", "INDEX takes the number directly", "good"),
             ("For a person to read", "ADDRESS, then strip the row", "good"),
             ("To build a reference", "INDIRECT is volatile — avoid", "bad")])

_v("excel-recover-unsaved-file",
   p_aria="What Excel keeps, and for how long",
   p_cap="It is a crash net on a timer, not a backup. Every hour makes recovery less likely.",
   steps=[("You work", "3 hours"), ("Autorecover snapshots", "every 10 min by default"),
          ("Closed without saving", "last copy kept, if enabled"), ("Cleaned up", "on a timer")],
   fail_at=3,
   f_aria="Where to look, in order",
   f_cap="Look before doing anything else in Excel.",
   source=("Unsaved work", "where is the copy?"),
   outcomes=[("On OneDrive", "full version history — best case", "good"),
             ("Never saved", "Recover Unsaved Workbooks, kept 4 days", "good"),
             ("Autorecover was off", "nothing to find", "bad")])

_v("excel-broken-external-links",
   p_aria="Why Break Links does not stop the prompt",
   p_cap="It converts cell formulas only. Four other places can hold a link, and it sees none of them.",
   steps=[("Prompt on open", "every time"), ("You run Break Links", "cells converted"),
          ("Link was in a name", "not a cell"), ("Prompt", "returns tomorrow")],
   fail_at=2,
   f_aria="The four hiding places",
   f_cap="Defined names are the usual culprit, by a wide margin.",
   source=("A link that will not break", "where is it?"),
   outcomes=[("A defined name", "Name Manager — check here first", "good"),
             ("Validation, formatting, a chart", "the other three places", "good"),
             ("Suppressing the prompt", "hides it, does not remove it", "bad")])
