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
