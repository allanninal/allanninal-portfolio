#!/usr/bin/env python3
"""Group A — the seven things Excel does to your data before you type anything.

These are ranked by measured demand, not by what is fun to write about. The source is
486 real questions on Super User and Stack Overflow with ~72M combined views: CSV and
encoding is the largest cluster on the whole site at 14.1M, and data-mangling-on-entry
adds another 4.3M. Together they beat every formula topic combined.

Each `short_answer` is written to be liftable verbatim by a search engine or an AI
answer — one direct sentence first, then the mechanism. Vague openers ("There are
several reasons this might happen...") are what stops a page being quoted.
"""
from build_guide import fx, symptom_table

GROUP = "When Excel changes your data"
CAT = "Data integrity"

GUIDES_A = [

# --------------------------------------------------------------------------- 1
dict(
 slug="excel-leading-zeros-disappear",
 title="Excel Deletes Leading Zeros — Why, and How to Keep Them",
 description="Excel drops the 0 from 01234 because it reads the cell as a number. Import the column as Text and the zeros survive. Full fix for CSV and paste.",
 h1="Excel keeps deleting the zero at the front of my numbers",
 lead="Postcodes, SKUs, employee IDs and sort codes all start with a zero, and Excel removes it the moment it decides the cell is a number. Nothing warns you, and formatting the column afterwards does not bring it back.",
 category=CAT, group=GROUP,
 card_title="Leading zeros disappear",
 card_blurb="Why 01234 becomes 1234, and the one import setting that keeps the zero.",
 chips=["CSV + paste", "Excel + Google Sheets", "No macros"],
 keywords=["excel leading zeros", "excel removes leading zero", "keep leading zeros excel",
           "excel postcode leading zero", "csv leading zeros excel", "excel sku leading zero"],
 short_answer="""<p><strong>Excel removes a leading zero because it has classified the cell as
a number, and 01234 and 1234 are the same number.</strong> The zero is not hidden by
formatting &mdash; it is not stored at all. The fix is to tell Excel the column is
<em>text</em> before the value arrives: import with <em>Data &rarr; From Text/CSV &rarr;
Transform Data</em> and set the column type to Text. Formatting the column as Text
afterwards does not restore the zero, because there is nothing left to restore.</p>""",
 problem_h="Why formatting the column afterwards never works",
 problem="""<p>This is the part that wastes the afternoon. You open the file, see 1234 where
01234 should be, select the column, set the format to Text &mdash; and nothing changes.
It looks like Excel is ignoring you.</p>
<p>It is not. Number formatting only controls how a stored value is <em>displayed</em>. When
Excel parsed <code>01234</code> it stored the number 1234, and the leading zero was discarded
at that moment. Changing the display format later asks Excel to re-render a value whose zero
no longer exists. The information is gone from the workbook, though it is still sitting
untouched in the original CSV.</p>
<p>That is why every real fix below happens <em>before or during</em> the import, not after it.</p>""",
 symptoms=symptom_table([
   ["<code>01234</code> shows as <code>1234</code>",
    "Parsed as a number on open; the zero was never stored",
    "Re-import the column as Text"],
   ["The column is right-aligned",
    "Excel right-aligns numbers and left-aligns text &mdash; this is the tell",
    "Alignment tells you which type you actually have"],
   ["Formatting as Text changes nothing",
    "Formatting affects display, not the stored value",
    "The value must be Text <em>as it arrives</em>"],
   ["A custom format like <code>00000</code> looks right",
    "It pads for display only; the underlying value is still 1234",
    "Fine for fixed-width codes, wrong if the length varies"],
 ]),
 howto_name="How to keep leading zeros in Excel",
 howto_desc="Four routes, depending on whether the data is arriving from a file, from a paste, or being typed.",
 steps=[
  dict(h="Importing a CSV: use Power Query and set the column to Text",
       plain="Open Excel first, then Data > From Text/CSV, choose the file, and in the preview click Transform Data rather than Load. Select the ID column, set its data type to Text, then Close & Load.",
       body="""<p>Open Excel <em>first</em> with a blank workbook &mdash; do not double-click the
CSV. Then <em>Data &rarr; From Text/CSV</em>, pick the file, and in the preview window click
<strong>Transform Data</strong>, not Load. In the Power Query editor, click the ID column, set
<em>Data Type &rarr; Text</em>, then <em>Close &amp; Load</em>. The zeros arrive intact because
Excel never got to guess.</p>"""),
  dict(h="No Power Query? Rename the file to .txt first",
       plain="Rename the file from .csv to .txt and open it. That forces the legacy Text Import Wizard, where step 3 lets you mark each column as Text.",
       body="""<p>A <code>.csv</code> opens silently using defaults. A <code>.txt</code> makes Excel
ask. Rename the file, open it, and at <strong>step 3</strong> of the wizard select the ID column
and choose <em>Text</em> under Column data format. This works in every version of Excel including
the ones with no Power Query.</p>"""),
  dict(h="Typing or pasting a few values: format the cells as Text before entering",
       plain="Select the empty column, set Format Cells to Text, and then type or paste. The format has to be applied before the value arrives, not after.",
       body="""<p>Select the still-empty column, <em>Format Cells &rarr; Text</em>, and only then
type or paste. Order is everything here: applied first it works, applied after it does nothing.
An apostrophe prefix (<code>'01234</code>) does the same thing for a single cell &mdash; the
apostrophe is not stored and not printed.</p>"""),
  dict(h="Rebuilding a zero that has a known fixed length",
       plain="If the code is always the same length, TEXT(A2,\"00000\") rebuilds the padded value as real text. Only do this when the length is genuinely fixed.",
       body="""<p>Sometimes the original file is gone and all you have is the damaged column. If
the code has a genuinely fixed length &mdash; a five-digit US ZIP, say &mdash; you can rebuild it:</p>""" +
       fx("Rebuild a fixed-length code", '=TEXT(A2,"00000")',
          """<p>This returns real text with the zeros restored. Use it <strong>only</strong> where
the length is fixed and known. If your SKUs vary between four and seven characters, this pads
everything to five and silently corrupts the rest &mdash; go back to the source file instead.</p>""")),
 ],
 body="""<h2>How to tell which type you actually have</h2>
<p>Excel gives you the answer without a formula: <strong>numbers align right, text aligns left</strong>,
unless someone has overridden the alignment. If your ID column is flush right, it is a number and
the zeros are gone.</p>
<p>To be certain, test it:</p>
""" + fx("Is this cell text or a number?", '=ISTEXT(A2)',
"""<p>TRUE means it is text and safe. FALSE means Excel is holding a number, and any leading zero
has already been discarded.</p>""") + """
<h2>Which columns to protect</h2>
<p>The rule is simple: <strong>if you would never do arithmetic on it, it is not a number.</strong>
Nobody adds two postcodes together. Treat all of these as text, every time:</p>
<ul>
<li>Postcodes and ZIP codes &mdash; the entire US Northeast starts with 0</li>
<li>SKUs, part numbers and batch codes</li>
<li>Employee, member, student and patient IDs</li>
<li>Phone numbers &mdash; and every international number written with a leading 0</li>
<li>Bank sort codes and account numbers</li>
<li>ISBNs, EANs and barcodes &mdash; these also hit the 15-digit limit</li>
</ul>
<h2>Google Sheets does the same thing</h2>
<p>Sheets strips leading zeros on import too. The equivalent fix is <em>Format &rarr; Number &rarr;
Plain text</em> applied to the column before the data lands, or on import choosing not to convert
text to numbers.</p>""",
 faq=[
  ("Why does Excel remove leading zeros?",
   "Because it classifies the cell as a number, and as a number 01234 and 1234 are identical. The zero is not hidden by formatting — it is never stored."),
  ("Can I get the zeros back after the file is saved?",
   "Not from the damaged workbook alone, unless the code has a fixed known length that you can rebuild with TEXT. The original CSV is unchanged, so re-importing it as Text is the reliable fix."),
  ("Does formatting the column as Text fix it?",
   "No, not afterwards. Number formatting changes how a stored value is displayed, and the zero is no longer part of the stored value. The format must be applied before the data arrives."),
  ("Is the apostrophe trick safe?",
   "Yes. A leading apostrophe forces the entry to be text, and the apostrophe itself is not stored in the value and does not print. It is practical for a handful of cells, not for a whole import."),
  ("Why do my zeros come back wrong after I share the file?",
   "A custom number format like 00000 pads for display only. Anyone who exports the column, or reads it with a script, gets the underlying number without the zeros. Store it as text instead."),
  ("Does this happen in Google Sheets too?",
   "Yes. Sheets applies the same numeric conversion on import. Set the column to Plain text before the data arrives."),
 ],
 related=[("excel-scientific-notation-barcodes", "Scientific notation is eating my barcodes"),
          ("excel-numbers-stored-as-text", "Numbers stored as text, and why SUM ignores them"),
          ("excel-csv-all-in-column-a", "The whole CSV landed in column A")],
),

# --------------------------------------------------------------------------- 2
dict(
 slug="excel-csv-utf8-mojibake",
 title="Fix Mojibake in Excel: the UTF-8 CSV Import Setting",
 description="Accented characters turn to mojibake because Excel guessed the wrong encoding. Set File Origin to 65001 (UTF-8) on import, and save as CSV UTF-8.",
 h1="Excel turned my accented characters into nonsense",
 lead="Niñal arrives as NiÃ±al, café as cafÃ©, and every name with an accent in it is now wrong. The file is not corrupt &mdash; Excel guessed the wrong character encoding on the way in, and there is a single setting that fixes it.",
 category=CAT, group=GROUP,
 card_title="Accents turn into mojibake",
 card_blurb="Ni&Atilde;&plusmn;al instead of Ni&ntilde;al. One import setting fixes it, and one export setting stops it.",
 chips=["CSV import + export", "UTF-8", "Excel + Google Sheets"],
 keywords=["excel utf-8 csv", "excel mojibake", "excel accented characters wrong",
           "csv encoding excel", "excel 65001 utf-8", "excel csv special characters"],
 short_answer="""<p><strong>Your file is fine; Excel opened it with the wrong character
encoding.</strong> A UTF-8 file read as Windows-1252 turns every accented character into two or
three wrong ones &mdash; <code>&ntilde;</code> becomes <code>&Atilde;&plusmn;</code>. Import with
<em>Data &rarr; From Text/CSV</em> and set <strong>File Origin to 65001: Unicode (UTF-8)</strong>.
When saving, choose <em>CSV UTF-8 (Comma delimited)</em>, because plain <em>CSV</em> writes your
system codepage and re-breaks the file on the way out.</p>""",
 problem_h="What mojibake actually is",
 problem="""<p>Text is stored as bytes, and an encoding is the agreement about which bytes mean
which characters. UTF-8 writes <code>&ntilde;</code> as two bytes. If a program reads those two
bytes as Windows-1252 &mdash; where every byte is its own character &mdash; it renders them as two
separate characters: <code>&Atilde;</code> and <code>&plusmn;</code>.</p>
<p>Nothing is damaged at this point. The bytes on disk are still correct and still say
<code>&ntilde;</code>. Only Excel's interpretation is wrong, which is why the fix is a setting
rather than a repair.</p>
<p>It becomes real damage the moment you <strong>save</strong>. Excel then writes out the wrong
characters it is showing you, and now the file on disk genuinely says
<code>Ni&Atilde;&plusmn;al</code>. Fix the import before saving anything.</p>""",
 symptoms=symptom_table([
   ["<code>Ni&Atilde;&plusmn;al</code> for <code>Ni&ntilde;al</code>",
    "UTF-8 file read as Windows-1252",
    "Re-import with File Origin 65001"],
   ["<code>caf&Atilde;&copy;</code> for <code>caf&eacute;</code>",
    "Same cause &mdash; one character became two",
    "Re-import with File Origin 65001"],
   ["A <code>&#65533;</code> where a character should be",
    "The byte had no valid mapping in the assumed encoding",
    "Re-import; if it persists the source was already damaged"],
   ["Accents were fine, then broke after you saved",
    "Saved as plain CSV, which writes your system codepage",
    "Save As &rarr; CSV UTF-8 (Comma delimited)"],
   ["<code>&#65279;</code> at the very start of the first cell",
    "A UTF-8 byte-order mark read as characters",
    "Import with 65001, which consumes the BOM properly"],
 ]),
 howto_name="How to open and save UTF-8 CSV files in Excel",
 howto_desc="Set the encoding on the way in, and choose the UTF-8 variant on the way out.",
 steps=[
  dict(h="Import with Data → From Text/CSV",
       plain="Open Excel with a blank workbook, then Data > From Text/CSV and select the file. Do not double-click the CSV.",
       body="""<p>Double-clicking gives Excel no chance to ask. Open Excel first, then
<em>Data &rarr; From Text/CSV</em> and choose the file. The preview dialog is where the encoding
setting lives.</p>"""),
  dict(h="Set File Origin to 65001: Unicode (UTF-8)",
       plain="In the preview dialog, change the File Origin dropdown to 65001: Unicode (UTF-8). The preview updates immediately and the accents appear correctly.",
       body="""<p>Change <strong>File Origin</strong> to <em>65001: Unicode (UTF-8)</em>. The
preview redraws straight away &mdash; if the accents look right there, they will be right in the
sheet. This is the whole fix. 65001 is just the Windows codepage number for UTF-8.</p>"""),
  dict(h="Click Transform Data and set your ID columns to Text",
       plain="While you are in the import dialog, click Transform Data and set any postcode, SKU or ID column to Text, so you fix the encoding and the leading zeros in one pass.",
       body="""<p>You are already in the right dialog, so deal with the other problem at the same
time: click <strong>Transform Data</strong> and set any code or ID column to Text. Encoding and
leading zeros are two separate failures that arrive through the same door.</p>"""),
  dict(h="Save with Save As → CSV UTF-8 (Comma delimited)",
       plain="When exporting, pick CSV UTF-8 (Comma delimited) rather than CSV (Comma delimited). Plain CSV writes your system codepage and corrupts non-ASCII characters.",
       body="""<p>Excel offers two CSV formats and the difference is not explained anywhere in the
dialog. <em>CSV (Comma delimited)</em> writes your system codepage. <em>CSV UTF-8 (Comma
delimited)</em> writes UTF-8 with a BOM. If anything downstream is a database, a website or
another person's computer, you want the UTF-8 one.</p>"""),
 ],
 body="""<h2>Why the BOM matters more than it should</h2>
<p>Excel will not reliably auto-detect UTF-8 from the content alone. It detects it from a
<strong>byte-order mark</strong> &mdash; three bytes at the very start of the file that announce the
encoding. A UTF-8 file written without a BOM, which is the normal and correct output of most
programming languages and databases, gives Excel nothing to detect, so it falls back to your
system codepage and the mojibake appears.</p>
<p>This is why a file that opens perfectly on a colleague's machine can be broken on yours: you have
different system codepages, and neither of you has a BOM to settle it.</p>
<h2>If you generate the CSV yourself</h2>
<p>Writing the BOM makes the file open correctly in Excel by double-click, with no import dialog at
all. In Python that is the <code>utf-8-sig</code> codec; in most other languages it means writing
the three bytes <code>EF BB BF</code> before anything else. Everything that reads UTF-8 properly
tolerates a BOM, so this costs you nothing elsewhere.</p>
<h2>Google Sheets is easier here</h2>
<p>Sheets assumes UTF-8 and is usually right. If you have an Excel-broken file, uploading it to
Google Drive and opening it with Sheets is a quick way to confirm the source file was fine all
along &mdash; and to recover the correct text.</p>""",
 faq=[
  ("Is my file corrupted?",
   "Almost certainly not. The bytes on disk are still correct; Excel is interpreting them with the wrong encoding. It only becomes real corruption if you save the file while it is displaying wrongly."),
  ("What does 65001 mean?",
   "It is the Windows codepage number for UTF-8. Choosing it in the File Origin dropdown tells Excel to read the bytes as UTF-8."),
  ("Why does the file open correctly for my colleague but not for me?",
   "Different system codepages. Without a byte-order mark, Excel falls back to each machine's regional default, so the same file can render differently on two computers."),
  ("What is the difference between CSV and CSV UTF-8 when saving?",
   "Plain CSV writes your system codepage and will corrupt non-ASCII characters. CSV UTF-8 writes UTF-8 with a byte-order mark, which is what any database, website or other person needs."),
  ("How do I stop this happening for files I generate?",
   "Write the UTF-8 byte-order mark at the start of the file. Then Excel detects the encoding on its own and even a double-click opens the file correctly."),
  ("Can I fix a file that was already saved with the wrong characters?",
   "Only by going back to the original. Once Excel has saved the mojibake, those wrong characters are genuinely what the file contains."),
 ],
 related=[("excel-csv-all-in-column-a", "The whole CSV landed in column A"),
          ("excel-leading-zeros-disappear", "Excel keeps deleting my leading zeros"),
          ("excel-vlookup-non-breaking-space", "Your VLOOKUP is fine, the data has an invisible space")],
),

# --------------------------------------------------------------------------- 3
dict(
 slug="excel-converts-text-to-dates",
 title="Stop Excel Turning Text Into Dates (SEP1, 1-2, 3/4)",
 description="Excel converts SEP1, 1-2 and 3/4 into dates the moment they arrive. Import the column as Text to stop it — and know which conversions cannot be undone.",
 h1="Excel keeps turning my part numbers into dates",
 lead="<code>SEP1</code> becomes 01-Sep. <code>1-2</code> becomes 2 January. <code>3/4</code> becomes a date instead of a ratio. Excel applies this the instant the value arrives, and the original text is not kept anywhere.",
 category=CAT, group=GROUP,
 card_title="Text silently becomes a date",
 card_blurb="SEP1, 1-2 and 3/4 all convert on entry. Why it is irreversible, and how to prevent it.",
 chips=["CSV + paste", "Irreversible", "Excel + Google Sheets"],
 keywords=["excel converts text to date", "stop excel changing to date", "excel autocorrect date",
           "excel gene names dates", "excel part number date", "excel date conversion csv"],
 short_answer="""<p><strong>Excel converts anything that looks like a date into a date serial
number the moment it is entered or imported, and the original text is discarded.</strong> The only
reliable prevention is to make the column Text before the value arrives &mdash; on import via
<em>Transform Data &rarr; Text</em>, or by formatting an empty column as Text before pasting. Once
converted, the value is a number like 45901 and the text it came from is not recoverable from the
workbook.</p>""",
 problem_h="Why this is worse than the other conversions",
 problem="""<p>A dropped leading zero is at least predictable: you know 1234 should have been 01234.
A date conversion destroys the shape of the value entirely.</p>
<p>When Excel decides <code>1-2</code> is a date, it stores the serial number for 2 January of the
current year &mdash; a five-digit integer with no visible relationship to what you typed. Displaying
it as text afterwards gives you <code>45659</code>, not <code>1-2</code>. There is no formatting
that returns the original, because the original was never stored.</p>
<p>This is well documented in science: a study of published genomics papers found gene names such as
<em>SEPT1</em> and <em>MARCH1</em> silently converted to dates in a large share of supplementary
spreadsheets. The problem was severe and persistent enough that in 2020 the naming body renamed the
affected genes rather than continue fighting the spreadsheet.</p>""",
 symptoms=symptom_table([
   ["<code>SEP1</code> shows as <code>01-Sep</code>",
    "Three-letter month prefix plus digits reads as a date",
    "Import the column as Text"],
   ["<code>1-2</code> shows as <code>02-Jan</code>",
    "Digits either side of a hyphen read as day-month",
    "Import the column as Text"],
   ["<code>3/4</code> shows as a date, not a ratio",
    "A slash between numbers reads as a date separator",
    "Format as Text first, or enter as <code>0 3/4</code> for a real fraction"],
   ["A five-digit number like <code>45659</code>",
    "That IS the date &mdash; a serial number, shown with a General format",
    "The original text is gone; re-import the source"],
   ["Values changed when a colleague opened the file",
    "Their regional settings read the same text as a different date",
    "Store as Text so no locale can reinterpret it"],
 ]),
 howto_name="How to stop Excel converting text to dates",
 howto_desc="Prevent the conversion on import or on paste; there is no reliable cure afterwards.",
 steps=[
  dict(h="On import, set the column type to Text",
       plain="Use Data > From Text/CSV, click Transform Data, select the affected column and set its data type to Text before loading.",
       body="""<p><em>Data &rarr; From Text/CSV &rarr; Transform Data</em>, select the column, set
<em>Data Type &rarr; Text</em>, then <em>Close &amp; Load</em>. This is the only method that
protects a whole file in one pass, and it is the one to learn.</p>"""),
  dict(h="Before pasting, format the destination as Text",
       plain="Select the empty destination column, set Format Cells to Text, and paste with Paste Special > Values. The format must exist before the values land.",
       body="""<p>Select the empty destination column, <em>Format Cells &rarr; Text</em>, then paste
using <em>Paste Special &rarr; Values</em>. Pasting into a General column converts on arrival, and
formatting afterwards will not undo it.</p>"""),
  dict(h="For a single typed value, lead with an apostrophe",
       plain="Type an apostrophe before the value, as in 'SEP1. The apostrophe forces text, is not stored in the value, and does not print.",
       body="""<p>Typing <code>'SEP1</code> forces the entry to be text. The apostrophe is not part
of the stored value and never prints. Practical for a few cells; not a strategy for an import.</p>"""),
  dict(h="Check a suspect column before you trust it",
       plain="Use ISNUMBER on the column. Any cell that returns TRUE where you expected a code has already been converted to a date serial.",
       body="""<p>A converted cell is a number, so this finds them all at once:</p>""" +
       fx("Has this been converted?", '=ISNUMBER(A2)',
          """<p>TRUE on a cell you expected to hold a code means it is now a date serial and the text
is gone. Sort or filter on this column to see the damage before you build anything on top of it.</p>""")),
 ],
 body="""<h2>Which shapes trigger it</h2>
<p>Excel converts a value when it matches a date pattern for your locale. In practice that means:</p>
<ul>
<li><strong>Digits around a separator</strong> &mdash; <code>1-2</code>, <code>3/4</code>, <code>12.5</code> in some locales</li>
<li><strong>A three-letter month prefix</strong> &mdash; <code>SEP1</code>, <code>MAR2</code>, <code>DEC10</code></li>
<li><strong>Digits with a month name</strong> &mdash; <code>1 Sep</code>, <code>Sep 1</code></li>
</ul>
<p>It is locale-dependent, which makes it worse: the same file can convert differently on two
machines. <code>3/4</code> is 3 April in the UK and 4 March in the US, and neither is a ratio.</p>
<h2>Why DATEVALUE is not a good detector</h2>
<p>The obvious test is <code>ISNUMBER(DATEVALUE(A2))</code>, but it inherits the same locale
dependence as the bug. Tested on one machine it flagged <code>3/4</code> but missed both
<code>SEP1</code> and <code>1-2</code> &mdash; values Excel does convert. Matching the
<em>shape</em> instead is deterministic:</p>
""" + fx("Would Excel read this as a date?",
'=OR(AND(OR(ISNUMBER(SEARCH("/",A2)),ISNUMBER(SEARCH("-",A2))),\n'
'   ISNUMBER(VALUE(SUBSTITUTE(SUBSTITUTE(A2,"/",""),"-","")))),\n'
'   ISNUMBER(MATCH(UPPER(LEFT(A2,3)),{"JAN";"FEB";"MAR";"APR";"MAY";"JUN";\n'
'   "JUL";"AUG";"SEP";"OCT";"NOV";"DEC"},0)))',
"""<p>TRUE means the value is at risk. This does not change with your regional settings, which is
the point &mdash; it is checking the shape, not asking Excel's opinion.</p>""") + """
<h2>The one case you can recover</h2>
<p>If the value became a date and you know the original format, the serial number still encodes the
day and month, so <code>TEXT(A2,"d-m")</code> can rebuild <code>1-2</code>. That works only when the
original really was a day and month. For a gene name or a part number, the mapping is not
reversible &mdash; go back to the source file.</p>""",
 faq=[
  ("Why does Excel change SEP1 to a date?",
   "SEP is a three-letter month prefix, so SEP1 matches Excel's pattern for the first of September. It converts on entry and stores a date serial number, discarding the text."),
  ("Can I undo a date conversion?",
   "Not in general. The stored value is a serial number and the original text was never kept. Where the original genuinely was a day and month you can rebuild it with TEXT; for a code or a gene name you must re-import the source."),
  ("Why did the values change when someone else opened my file?",
   "Date parsing is locale-dependent. 3/4 is 3 April in the UK and 4 March in the US. Storing the column as Text stops any locale from reinterpreting it."),
  ("Does turning off AutoCorrect stop this?",
   "No. This is type coercion during parsing, not AutoCorrect, and there is no setting that disables it. The column has to be Text before the value arrives."),
  ("How do I enter 3/4 as a fraction rather than a date?",
   "Type 0 3/4 — a zero, a space, then the fraction. Excel stores 0.75 and displays it as a fraction. Alternatively format the cell as Text if you want the literal characters."),
  ("Is this really why some genes were renamed?",
   "Yes. Repeated silent conversion of names like SEPT1 and MARCH1 in published supplementary data led the gene naming committee to rename the affected genes in 2020."),
 ],
 related=[("excel-leading-zeros-disappear", "Excel keeps deleting my leading zeros"),
          ("excel-numbers-stored-as-text", "Numbers stored as text, and why SUM ignores them"),
          ("clean-inventory-sku-export-excel", "Cleaning an inventory or SKU export")],
),

# --------------------------------------------------------------------------- 4
dict(
 slug="excel-vlookup-non-breaking-space",
 title="VLOOKUP Returns #N/A but the Value Is Right There",
 description="A trailing or non-breaking space makes an exact match fail. Why TRIM alone does not fix it, why CHAR(160) is not portable, and the chain that works.",
 h1="My VLOOKUP says #N/A but I can see the value in the list",
 lead="The value is sitting there in the lookup range. You have checked it three times. The match still fails &mdash; because the two strings are not actually identical, and the difference is a character you cannot see.",
 category=CAT, group=GROUP,
 card_title="#N/A when the value is clearly there",
 card_blurb="Invisible spaces break exact matches. Why TRIM alone is not enough.",
 chips=["VLOOKUP + XLOOKUP", "TRIM + CLEAN", "Excel + Google Sheets"],
 keywords=["vlookup na error", "vlookup not working value exists", "excel trailing space lookup",
           "excel non-breaking space", "excel trim not working", "excel char 160"],
 short_answer="""<p><strong>An exact-match lookup compares the strings byte for byte, so a
trailing space or a non-breaking space makes two values that look identical fail to match.</strong>
<code>TRIM</code> alone does not fix it: <code>TRIM</code> only removes ordinary spaces, and text
pasted from a web page usually contains a <em>non-breaking</em> space, which is a different
character. Substitute the invisible characters first, then <code>CLEAN</code>, then
<code>TRIM</code> &mdash; in that order.</p>""",
 problem_h="Three different invisible characters, three different fixes",
 problem="""<p>&ldquo;There is a space in it&rdquo; is usually right but rarely specific enough.
There are three distinct culprits and only one of them is what people mean by a space:</p>
<ul>
<li><strong>Ordinary space</strong> (character 32) at the start or end. <code>TRIM</code> removes
these, and this is the case everyone knows about.</li>
<li><strong>Non-breaking space</strong> (U+00A0). Arrives with anything pasted from a web page or a
PDF. <code>TRIM</code> does <em>not</em> touch it, because it is not an ordinary space. This is the
one that produces the &ldquo;I already trimmed it and it still fails&rdquo; afternoon.</li>
<li><strong>Zero-width space</strong> (U+200B) and control characters. Arrive from ERP and PDF
exports. Occupy no width at all, so the cell looks completely normal.</li>
</ul>
<p><code>CLEAN</code> removes control characters but not the non-breaking space either &mdash; a
non-breaking space is a <em>printing</em> character as far as Excel is concerned. So the standard
advice, <code>TRIM(CLEAN(A2))</code>, misses the most common cause.</p>""",
 symptoms=symptom_table([
   ["#N/A but the value is visibly present",
    "The two strings differ by a character you cannot see",
    "Clean both sides, then match"],
   ["<code>TRIM</code> made no difference",
    "A non-breaking space is not an ordinary space",
    "SUBSTITUTE the character out first"],
   ["<code>=A2=B2</code> returns FALSE for identical-looking text",
    "Confirms the strings genuinely differ",
    "Compare <code>LEN</code> to find the extra character"],
   ["It works after you retype the value by hand",
    "Retyping produced clean characters; the imported one was dirty",
    "Clean the column rather than retyping it"],
   ["Only some rows fail",
    "Only some values were pasted from the dirty source",
    "Clean the whole column, not the failing rows"],
 ]),
 howto_name="How to fix a lookup that fails on invisible characters",
 howto_desc="Confirm the cause, clean both sides with the chain in the right order, then match.",
 steps=[
  dict(h="Confirm the strings really do differ",
       plain="Put =A2=B2 next to the pair. FALSE proves they are not identical. Then compare LEN(A2) and LEN(B2) to see how many extra characters there are.",
       body="""<p>Before changing anything, prove the cause:</p>""" +
       fx("Are they actually the same?", '=A2=B2          =LEN(A2)          =LEN(B2)',
          """<p>FALSE with different lengths means there are extra characters. FALSE with the
<em>same</em> length means a character has been substituted &mdash; typically an ordinary space
replaced by a non-breaking one.</p>""")),
  dict(h="Identify the character",
       plain="Use CODE on the last character. 32 is an ordinary space, 160 is a non-breaking space, and anything under 32 is a control character.",
       body="""<p>To see exactly what you are dealing with:</p>""" +
       fx("What is that last character?", '=CODE(RIGHT(A2,1))',
          """<p><strong>32</strong> is an ordinary space, <strong>160</strong> is a non-breaking
space, and anything below 32 is a control character. Knowing which one tells you whether
<code>TRIM</code> can help at all.</p>""")),
  dict(h="Clean with the chain in the correct order",
       plain="Substitute the non-breaking and zero-width spaces first, then apply CLEAN, then TRIM. Doing it in any other order leaves the invisible characters in place.",
       body="""<p>Order matters and this is the whole trick. Replace the invisible characters first
&mdash; while they are still there to be replaced &mdash; then let <code>CLEAN</code> and
<code>TRIM</code> do their work:</p>""" +
       fx("The clean chain", '=TRIM(CLEAN(SUBSTITUTE(SUBSTITUTE(A2,"[nbsp]"," "),"[zwsp]","")))',
          """<p><code>[nbsp]</code> and <code>[zwsp]</code> stand for the literal invisible
characters. Copy one out of your own data to type them, or use the free workbook below, which
already has them in place.</p>""")),
  dict(h="Clean both sides, then match",
       plain="Apply the same cleaning to the lookup value and to the lookup column. Cleaning only one side leaves the mismatch in place.",
       body="""<p>This is the step people miss. Cleaning your lookup value while the lookup
<em>column</em> is still dirty changes nothing. Add a cleaned helper column beside the lookup range,
point the lookup at that, and clean the search value the same way.</p>"""),
 ],
 body="""<h2>Why CHAR(160) is the wrong advice</h2>
<p>Nearly every article recommends <code>SUBSTITUTE(A2,CHAR(160)," ")</code>. Inside Excel it works.
Outside Excel it does not, and it fails <em>silently</em> &mdash; the formula runs, reports success,
and leaves the character in place.</p>
<p>Tested in LibreOffice, <code>CODE(CHAR(160))</code> returns <strong>239</strong>, not 160. So
<code>CHAR(160)</code> is not producing a non-breaking space at all, and the substitution matches
nothing. <code>UNICHAR(160)</code> is not available there either. If your workbook is ever opened in
LibreOffice, Numbers, or by a colleague who does not use Excel, a <code>CHAR(160)</code>-based
cleanup will report their data clean when it is not.</p>
<p>Putting the <strong>literal character</strong> inside the quotes needs no character-set function
at all and behaves identically everywhere. That is what the workbook does.</p>
<h2>Fix the data, not the formula</h2>
<p>Wrapping every lookup in a cleaning chain works, but it hides the problem and slows large sheets
down. Clean the column once, paste the result back over itself with <em>Paste Special &rarr;
Values</em>, and every lookup that touches it afterwards is simple again.</p>
<h2>XLOOKUP does not rescue you</h2>
<p><code>XLOOKUP</code> is a better function in most respects, but its default match mode is exact,
so it fails on invisible characters exactly like <code>VLOOKUP</code>. The problem is the data, not
the function.</p>""",
 faq=[
  ("Why does my VLOOKUP fail when I can see the value?",
   "Exact match compares strings character by character. A trailing space, a non-breaking space or a zero-width character makes two identical-looking values different, so the match fails."),
  ("Why did TRIM not fix it?",
   "TRIM removes ordinary spaces (character 32). A non-breaking space is character 160 — a different character that TRIM leaves alone. Substitute it out before trimming."),
  ("Why is CHAR(160) not reliable?",
   "It works in Excel but not elsewhere. In LibreOffice, CODE(CHAR(160)) returns 239, so the substitution matches nothing and silently reports the data clean. Use the literal character instead."),
  ("How do I type a non-breaking space into a formula?",
   "Copy one out of your own data and paste it between the quotes. The free workbook already contains it, so you can lift the formula from there."),
  ("Does XLOOKUP handle this better than VLOOKUP?",
   "No. XLOOKUP defaults to exact match and fails the same way. The problem is in the data, not in the lookup function."),
  ("Should I clean inside every formula, or clean the column once?",
   "Clean the column once and paste the result back as values. Wrapping every lookup in a cleaning chain hides the problem and slows large workbooks down."),
 ],
 related=[("excel-compare-two-lists", "Find what is in list A but not list B"),
          ("excel-join-two-sheets-lookup", "Joining two sheets the way SQL would"),
          ("excel-numbers-stored-as-text", "Numbers stored as text, and why SUM ignores them")],
),

# --------------------------------------------------------------------------- 5
dict(
 slug="excel-csv-all-in-column-a",
 title="My Whole CSV Opened Into Column A — How to Split It",
 description="A CSV that lands entirely in column A was written with a different delimiter. Fix it on import instead of changing your Windows regional settings.",
 h1="The whole CSV opened into a single column",
 lead="Every row is sitting in column A with the commas or semicolons still in it. The file is not broken and it does not need repairing &mdash; Excel simply expected a different separator from the one the file uses.",
 category=CAT, group=GROUP,
 card_title="Everything landed in column A",
 card_blurb="Comma vs semicolon is a regional setting. Fix it on import, not in Windows.",
 chips=["CSV import", "Delimiters", "Excel + Google Sheets"],
 keywords=["csv opens in one column excel", "excel semicolon csv", "excel csv delimiter",
           "excel csv not splitting columns", "excel list separator", "text to columns csv"],
 short_answer="""<p><strong>Excel splits a CSV using your Windows <em>list separator</em>, and the
file was written with a different one.</strong> Most of the English-speaking world uses a comma;
much of Europe uses a semicolon, because the comma is the decimal separator there. Fix it per file
with <em>Data &rarr; From Text/CSV</em>, where you choose the delimiter in the import dialog &mdash;
rather than changing your regional settings, which would break every other file you own.</p>""",
 problem_h="Why the file is fine and your settings are the problem",
 problem="""<p>A CSV is a text file with a separator between fields. Which separator counts as
&ldquo;the&rdquo; separator is not stored in the file &mdash; there is no header saying so. Excel
decides using the <strong>list separator</strong> from your Windows regional settings.</p>
<p>In regions where the comma is the decimal separator, using a comma to separate fields would be
ambiguous, so the list separator is a semicolon. A file exported there is perfectly valid, and lands
in one column on a machine expecting commas. The reverse happens just as often.</p>
<p>This is why the internet's usual answer &mdash; change your Windows list separator &mdash; is bad
advice. It fixes this one file and changes how Excel reads and writes <em>every</em> CSV on the
machine from then on.</p>""",
 symptoms=symptom_table([
   ["Every row in column A, commas visible",
    "File is comma-separated, Excel expected semicolons",
    "Import and choose Comma"],
   ["Every row in column A, semicolons visible",
    "File is semicolon-separated, Excel expected commas",
    "Import and choose Semicolon"],
   ["Splits correctly but numbers are wrong",
    "Decimal comma read as a thousands separator, or the reverse",
    "Set the column locale in Power Query"],
   ["Some rows split, others do not",
    "Quoted fields containing the delimiter, handled inconsistently",
    "Import properly &mdash; the wizard respects quoting"],
   ["It splits on your machine, not a colleague's",
    "You have different regional list separators",
    "Agree on one format, or send .xlsx instead"],
 ]),
 howto_name="How to open a CSV with the right delimiter",
 howto_desc="Choose the separator per file on import, and use Text to Columns to rescue a file already open.",
 steps=[
  dict(h="Import with Data → From Text/CSV and pick the delimiter",
       plain="Open Excel with a blank workbook, use Data > From Text/CSV, select the file, and set the Delimiter dropdown to the character the file actually uses.",
       body="""<p><em>Data &rarr; From Text/CSV</em>, choose the file, and set the
<strong>Delimiter</strong> dropdown to what the file actually uses. The preview shows the result
immediately. This affects only this file, which is exactly what you want.</p>"""),
  dict(h="Already open? Use Text to Columns",
       plain="Select column A, then Data > Text to Columns, choose Delimited, tick the correct separator, and finish. Make sure there are empty columns to the right first.",
       body="""<p>If the file is already open in one column, you do not need to reopen it. Select
column A, then <em>Data &rarr; Text to Columns &rarr; Delimited</em>, tick the right separator, and
finish. Insert empty columns to the right first &mdash; the split overwrites whatever is beside
it.</p>
<p>While you are on step 3 of that wizard, set your ID columns to Text. It is the same dialog that
prevents the leading-zero problem.</p>"""),
  dict(h="Check the decimal separator too",
       plain="If the file came from a region that uses a decimal comma, set the column locale in Power Query so 1.234,56 is read correctly rather than becoming 1.23456 or text.",
       body="""<p>A file with semicolon separators very likely uses a <strong>decimal comma</strong>
as well. In Power Query, right-click the column, choose <em>Change Type &rarr; Using Locale</em>,
and pick the origin region. Without this the numbers import as text, or worse, as the wrong
numbers.</p>"""),
  dict(h="Do not change your Windows list separator",
       plain="Changing the regional list separator fixes this file but changes how Excel reads and writes every CSV on the machine afterwards. Handle it per file instead.",
       body="""<p>It is the top answer everywhere and it is a trap. It is a machine-wide setting: it
silently changes how every future CSV is read <em>and written</em>, so files you export start
arriving wrong for everyone else. Per-file import is a few more clicks and has no side effects.</p>"""),
 ],
 body="""<h2>The sep= line</h2>
<p>There is one thing a file can do to declare its delimiter. If the very first line is:</p>
""" + fx("Declaring the delimiter inside the file", 'sep=;',
"""<p>Excel reads it and uses that separator, even on a double-click. It is an Excel-specific
convention rather than part of any CSV standard, so other tools may show it as a stray first row
&mdash; but if your audience is Excel users, it removes the problem completely.</p>""") + """
<h2>If you are generating the file</h2>
<p>You cannot satisfy every region at once with CSV. If the recipient is known to be an Excel user
in a semicolon region, write semicolons and a <code>sep=;</code> line. If the file is going to a
database or a script, write commas and quote every field containing one.</p>
<p>Where the recipient is a person rather than a system, <strong>send an .xlsx instead</strong>. It
carries its own structure, so there is no delimiter to negotiate, no encoding to guess, and no
leading zeros to lose.</p>
<h2>Google Sheets detects this automatically</h2>
<p>Sheets inspects the content and usually picks the right separator regardless of your locale, and
its import dialog lets you override it. Uploading a stubborn file to Sheets is a quick way to
confirm the file itself is well-formed.</p>""",
 faq=[
  ("Why did my CSV open in one column?",
   "Excel split it using your Windows list separator, and the file uses a different one. Comma is common in English-speaking regions, semicolon where the comma is the decimal separator."),
  ("Should I change my Windows list separator?",
   "No. It is a machine-wide setting that changes how Excel reads and writes every CSV afterwards, so files you export start breaking for other people. Choose the delimiter per file on import."),
  ("Is the file broken?",
   "No. It is a valid CSV written with a different separator convention. Nothing needs repairing — only the way Excel opens it needs changing."),
  ("What is the sep= line?",
   "Putting sep=; on the very first line makes Excel use that delimiter even on a double-click. It is an Excel convention rather than a CSV standard, so other tools may display it as a stray row."),
  ("Why are my numbers wrong after the columns split correctly?",
   "The file probably uses a decimal comma. In Power Query use Change Type > Using Locale and pick the origin region so the numbers are parsed correctly."),
  ("What is the most reliable format to send someone?",
   "An .xlsx file. It carries its own structure and encoding, so there is no delimiter to guess, no encoding to get wrong and no leading zeros to lose."),
 ],
 related=[("excel-csv-utf8-mojibake", "Accents turned into mojibake"),
          ("excel-leading-zeros-disappear", "Excel keeps deleting my leading zeros"),
          ("excel-numbers-stored-as-text", "Numbers stored as text, and why SUM ignores them")],
),

# --------------------------------------------------------------------------- 6
dict(
 slug="excel-numbers-stored-as-text",
 title="SUM Returns 0: Numbers Stored as Text in Excel",
 description="If SUM ignores a column, the values are text that looks numeric. How to detect it, three ways to convert, and why the total looked right all along.",
 h1="SUM is ignoring half my column",
 lead="The total is far too low, or zero, and the column is plainly full of numbers. They are not numbers &mdash; they are text that looks like numbers, and every arithmetic function in Excel skips them without a word.",
 category=CAT, group=GROUP,
 card_title="SUM ignores numbers that look fine",
 card_blurb="Text that looks numeric is skipped by SUM, AVERAGE and every other calculation.",
 chips=["SUM + AVERAGE", "Detect + convert", "Excel + Google Sheets"],
 keywords=["excel sum not working", "excel numbers stored as text", "excel sum returns 0",
           "convert text to number excel", "excel value function", "excel green triangle number"],
 short_answer="""<p><strong><code>SUM</code> silently skips text, so a column of numbers stored
as text totals to zero or to only the part that is genuinely numeric.</strong> Detect it with
<code>=AND(ISTEXT(A2),ISNUMBER(VALUE(A2)))</code> &mdash; TRUE means the cell is being ignored.
Convert with Text to Columns, with Paste Special multiply-by-1, or by re-importing the column as a
number. The most dangerous case is a <em>partly</em> text column, because the total looks
plausible.</p>""",
 problem_h="Why the wrong total is more dangerous than no total",
 problem="""<p>A <code>SUM</code> that returns 0 is at least obvious. The costly case is the column
where most values are numeric and a handful are text &mdash; typically the rows that came from a
different export, or that had a stray space, or that a person typed by hand.</p>
<p><code>SUM</code> returns a number that is too small but entirely believable. It gets copied into a
report, and nothing about it looks wrong. Excel shows a small green triangle in the corner of the
affected cells, but that is easy to miss and often switched off in a shared workbook.</p>
<p>This is the standard state of anything exported from an accounting or ERP system, where numbers
frequently arrive with currency symbols, thousands separators or trailing spaces attached.</p>""",
 symptoms=symptom_table([
   ["<code>SUM</code> returns 0",
    "The entire column is text",
    "Convert the column to numbers"],
   ["The total is too low but plausible",
    "Only some rows are text &mdash; the dangerous case",
    "Test every row, not a sample"],
   ["Values are left-aligned",
    "Excel left-aligns text and right-aligns numbers",
    "Alignment is the fastest visual check"],
   ["A small green triangle in the corner",
    "Excel's own 'number stored as text' warning",
    "Select the range and use Convert to Number"],
   ["<code>COUNT</code> is lower than <code>COUNTA</code>",
    "COUNT counts numbers only; COUNTA counts anything non-empty",
    "The gap is the number of text cells"],
 ]),
 howto_name="How to find and convert numbers stored as text",
 howto_desc="Measure the size of the problem first, then convert with whichever method suits the column.",
 steps=[
  dict(h="Measure it with COUNT against COUNTA",
       plain="Compare COUNT of the range with COUNTA of the range. COUNT only counts numeric cells, so the difference is how many are text.",
       body="""<p>Before converting anything, find out how bad it is:</p>""" +
       fx("How many cells are being skipped?", '=COUNTA(A2:A500)-COUNT(A2:A500)',
          """<p><code>COUNTA</code> counts every non-empty cell; <code>COUNT</code> counts only
numeric ones. The difference is the number of cells <code>SUM</code> is ignoring. Zero means the
column is clean.</p>""")),
  dict(h="Flag the exact rows",
       plain="Use AND(ISTEXT(A2),ISNUMBER(VALUE(A2))) to flag cells that are text but would be valid numbers. Filter on it to see which rows are affected.",
       body="""<p>To see <em>which</em> rows:</p>""" +
       fx("Is this a number pretending to be text?", '=AND(ISTEXT(A2),ISNUMBER(VALUE(A2)))',
          """<p>TRUE means the cell holds text that would convert cleanly to a number &mdash; exactly
the cells <code>SUM</code> is skipping. Filter on TRUE to inspect them before you convert
anything.</p>""")),
  dict(h="Convert with Text to Columns — the fastest whole-column fix",
       plain="Select the column, choose Data > Text to Columns, and click Finish on the first screen. This forces Excel to re-parse every value, converting the numeric ones.",
       body="""<p>Select the column, <em>Data &rarr; Text to Columns</em>, and press
<strong>Finish</strong> immediately &mdash; you do not need any of the wizard's options. This forces
Excel to re-parse each value, and the numeric ones become real numbers. It is the fastest fix for a
whole column and needs no helper column.</p>"""),
  dict(h="Or multiply by 1 with Paste Special",
       plain="Type 1 into an empty cell and copy it. Select the text numbers, then Paste Special > Multiply. Arithmetic forces the conversion in place.",
       body="""<p>Type <code>1</code> in a spare cell and copy it. Select the affected range, then
<em>Paste Special &rarr; Multiply</em>. Multiplying by one forces a numeric conversion in place,
which is useful when Text to Columns would disturb the layout.</p>"""),
  dict(h="If the values carry symbols, strip them first",
       plain="Currency symbols, thousands separators and trailing spaces block conversion. Remove them with SUBSTITUTE and TRIM before applying VALUE.",
       body="""<p><code>VALUE</code> fails on anything with a currency symbol or a thousands
separator still attached:</p>""" +
       fx("Strip, then convert", '=VALUE(TRIM(SUBSTITUTE(SUBSTITUTE(A2,"$",""),",","")))',
          """<p>Extend the nested <code>SUBSTITUTE</code> calls for whichever symbols your export
carries. Wrap the whole thing in <code>IFERROR</code> if some rows are genuinely not numbers.</p>""")),
 ],
 body="""<h2>Why this happens so often to accounting exports</h2>
<p>Financial systems export numbers with their formatting attached: <code>$1,234.56</code>,
<code>1 234,56</code>, <code>(500)</code> for a negative, or a trailing space where a currency code
was stripped. Each of those makes the value text as far as Excel is concerned.</p>
<p>Negatives in parentheses are a particular trap. Accountants write <code>(500)</code> for minus
500; Excel usually reads that as text. Convert those explicitly rather than hoping:</p>
""" + fx("Accounting negatives", '=IF(LEFT(TRIM(A2),1)="(",-VALUE(SUBSTITUTE(SUBSTITUTE(A2,"(",""),")","")),VALUE(A2))',
"""<p>Detects the bracket form, strips the brackets and negates the result; anything else converts
normally.</p>""") + """
<h2>The opposite problem</h2>
<p>Sometimes text is what you want. An ID column of digits <em>should</em> be text &mdash; that is
what keeps the leading zeros. Do not convert a column to numbers just because it contains digits.
Ask whether you would ever do arithmetic on it. If not, leave it as text.</p>
<h2>Preventing it at the source</h2>
<p>On import, set genuinely numeric columns to a numeric type in Power Query, with the correct
locale if the file uses a decimal comma. Getting the type right on the way in avoids the whole
conversion exercise.</p>""",
 faq=[
  ("Why does SUM return 0 when the column is full of numbers?",
   "They are text that looks numeric. SUM only adds numeric cells and skips text without any warning or error."),
  ("How do I tell whether a cell is text or a number?",
   "Numbers align right and text aligns left by default. To be certain, use =ISTEXT(A2), or compare COUNT and COUNTA over the range."),
  ("What is the fastest way to convert a whole column?",
   "Select the column, Data > Text to Columns, and click Finish on the first screen. That re-parses every value and converts the numeric ones in place."),
  ("Why does VALUE return an error on my cells?",
   "Something non-numeric is still attached — a currency symbol, a thousands separator, a trailing space or accounting brackets. Strip those with SUBSTITUTE and TRIM before applying VALUE."),
  ("What is the green triangle in the corner of the cell?",
   "Excel's own warning that a number is stored as text. Selecting the range gives you a Convert to Number option, though it is often disabled in shared workbooks."),
  ("Should I convert every column of digits to numbers?",
   "No. IDs, SKUs and postcodes should stay as text — that is what preserves their leading zeros. Only convert columns you would actually do arithmetic on."),
 ],
 related=[("excel-leading-zeros-disappear", "Excel keeps deleting my leading zeros"),
          ("excel-sum-visible-rows-only", "Summing only the rows a filter left visible"),
          ("clean-bank-statement-export-excel", "Cleaning a bank statement export")],
),

# --------------------------------------------------------------------------- 7
dict(
 slug="excel-scientific-notation-barcodes",
 title="Excel Shows 1.23E+14 Instead of My Barcode — the Fix",
 description="Long numbers become scientific notation, and past 15 digits Excel replaces the rest with zeros permanently. How to import barcodes and card numbers safely.",
 h1="Excel turned my barcode into 1.23E+14",
 lead="Long reference numbers arrive as scientific notation, and formatting them back reveals a second problem: past the fifteenth digit, the rest have been replaced by zeros. That part is permanent.",
 category=CAT, group=GROUP,
 card_title="Barcodes become 1.23E+14",
 card_blurb="Scientific notation is cosmetic. The 15-digit limit behind it is not.",
 chips=["15-digit limit", "Irreversible", "Excel + Google Sheets"],
 keywords=["excel scientific notation", "excel barcode number", "excel 15 digit limit",
           "excel long number changes to 0", "excel credit card number", "excel imei number"],
 short_answer="""<p><strong>There are two separate problems here.</strong> Scientific notation is
only a display format and is reversible. The real damage is Excel's 15-significant-digit limit: any
digit past the fifteenth is replaced by a zero, permanently, and no formatting brings it back. A
16-digit card number or an 18-digit tracking reference is truncated the moment it is read as a
number. Import the column as <strong>Text</strong> and neither problem occurs.</p>""",
 problem_h="The cosmetic problem and the permanent one",
 problem="""<p><strong>Scientific notation</strong> is Excel shortening a long number to fit the
column. <code>123456789012345</code> becomes <code>1.23457E+14</code>. The value is intact; widening
the column or applying a Number format shows it again. Annoying, not harmful.</p>
<p><strong>The 15-digit limit</strong> is different. Excel stores numbers as IEEE 754 doubles, which
hold about 15 significant decimal digits. A 16-digit card number loses its sixteenth digit &mdash;
replaced with a zero. An 18-digit tracking reference loses three. This happens at the moment the text
is parsed into a number, and the discarded digits are not stored anywhere.</p>
<p>So <code>4532015112830366</code> becomes <code>4532015112830360</code>. It still looks like a card
number. It is simply the wrong one, and no formula recovers it &mdash; the information is not in the
workbook any more.</p>""",
 symptoms=symptom_table([
   ["<code>1.23E+14</code> in the cell",
    "Display format only &mdash; the value is intact",
    "Widen the column or apply a Number format"],
   ["Number ends in 0 where it should not",
    "Past 15 significant digits; the rest were replaced",
    "Re-import as Text &mdash; not recoverable in place"],
   ["<code>#####</code> across the cell",
    "Column too narrow for the formatted number",
    "Widen the column; nothing is damaged"],
   ["Last digits differ from the source file",
    "The 15-digit limit truncated them on import",
    "Re-import the original with the column as Text"],
   ["Barcode scans as a different product",
    "A digit was replaced, so the check digit no longer matches",
    "Re-import as Text and re-verify"],
 ]),
 howto_name="How to keep long numbers intact in Excel",
 howto_desc="Treat long reference numbers as text, because they are identifiers rather than quantities.",
 steps=[
  dict(h="Import the column as Text",
       plain="Use Data > From Text/CSV, click Transform Data, set the long-number column to Text, and load. Nothing is parsed as a number, so nothing is truncated.",
       body="""<p><em>Data &rarr; From Text/CSV &rarr; Transform Data</em>, select the column,
<em>Data Type &rarr; Text</em>, <em>Close &amp; Load</em>. The digits are never parsed as a number,
so the limit never applies. This is the only method that is safe for 16+ digits.</p>"""),
  dict(h="Format the destination as Text before pasting",
       plain="Select the empty column, set Format Cells to Text, and then paste. Applying the format afterwards does not restore truncated digits.",
       body="""<p>Select the empty column, <em>Format Cells &rarr; Text</em>, then paste. As with
leading zeros, the order decides the outcome: format first and the digits survive, format afterwards
and you are formatting a number that has already lost them.</p>"""),
  dict(h="Check whether truncation has already happened",
       plain="Compare the length of the value with the length it should be. If a 16-digit reference now has fewer significant digits or ends in an unexpected zero, it has been truncated.",
       body="""<p>Count what you actually have:</p>""" +
       fx("How long is this value really?", '=LEN(TRIM(A2))',
          """<p>Compare against the length the identifier should be. Anything at or above 16 digits
that was read as a number is suspect &mdash; check the last digits against the source file before
using it.</p>""")),
  dict(h="If it is already truncated, go back to the original",
       plain="Truncated digits are not stored anywhere in the workbook. Re-import the original file with the column set to Text; there is no formula that recovers them.",
       body="""<p>There is no repair. The digits were discarded during parsing and the workbook has
no record of them. The original CSV or export is still correct &mdash; re-import it with the column
as Text. If the original is gone, the data is gone.</p>"""),
 ],
 body="""<h2>Which identifiers are affected</h2>
<ul>
<li><strong>Payment card numbers</strong> &mdash; 16 digits. Always truncated.</li>
<li><strong>IMEI numbers</strong> &mdash; 15 digits. Right at the boundary.</li>
<li><strong>Tracking references</strong> &mdash; often 18 to 22 digits.</li>
<li><strong>EAN-13 and UPC barcodes</strong> &mdash; 12 to 13 digits, usually safe, but they also
lose leading zeros.</li>
<li><strong>Bank account numbers with IBAN</strong> &mdash; well past the limit.</li>
</ul>
<p>The pattern is the same as everywhere else on this site: <strong>these are identifiers, not
quantities</strong>. You will never add two barcodes together. Nothing that you would not do
arithmetic on should be stored as a number.</p>
<h2>Why the limit exists</h2>
<p>Excel stores numbers in the IEEE 754 double-precision format, which allocates 53 bits to the
significand &mdash; roughly 15 to 17 significant decimal digits. Excel rounds to 15 for consistency.
This is a deliberate engineering trade-off in a format designed for measurement and calculation, and
it is shared by Google Sheets, LibreOffice and most programming languages. It only becomes a bug
when a number is being used as a name.</p>
<h2>Displaying a long number that is genuinely a number</h2>
<p>If a value really is a quantity and you only want to stop the scientific notation, a custom
number format of <code>0</code> forces full digits without changing the stored value. That is purely
cosmetic and does nothing about the 15-digit limit.</p>""",
 faq=[
  ("Is scientific notation damaging my data?",
   "No. Scientific notation is a display format and the stored value is intact. The damage is the separate 15-significant-digit limit, which truncates longer numbers permanently."),
  ("Why does my 16-digit number end in 0?",
   "Excel stores numbers with about 15 significant digits. The sixteenth digit onward is replaced with a zero when the text is parsed as a number, and it is not stored anywhere."),
  ("Can I recover the truncated digits?",
   "Not from the workbook — they were never stored. The original file is still correct, so re-import it with the column set to Text."),
  ("Does formatting the cell as Number fix it?",
   "It removes the scientific notation display, but it cannot restore digits that were discarded during parsing. Formatting only changes how a stored value is shown."),
  ("Why does this happen in Google Sheets too?",
   "Sheets uses the same IEEE 754 double-precision storage and has the same practical limit. Setting the column to Plain text before import avoids it there as well."),
  ("What about #### across the cell?",
   "That is only the column being too narrow for the formatted value. Widen the column; nothing has been changed."),
 ],
 related=[("excel-leading-zeros-disappear", "Excel keeps deleting my leading zeros"),
          ("excel-converts-text-to-dates", "Excel keeps turning my part numbers into dates"),
          ("clean-inventory-sku-export-excel", "Cleaning an inventory or SKU export")],
),
]
