#!/usr/bin/env python3
"""Group F — conditional formatting by formula, harder lookups, and getting a file back.

Three small clusters that share a property: each is the point where somebody stops being a
beginner. A conditional format driven by a formula, a lookup that returns the LAST match,
knowing that an unsaved file is usually recoverable — none of these are hard, and none of
them are obvious.

Demand is highest in the conditional formatting group: "format based on another cell's
value" is the single highest-voted Google Sheets question in the whole sample at 781,040
views, with "highlight duplicates" close behind at 950,994. That is where advanced
actually begins for most people.
"""
from build_guide import fx, symptom_table

CF = "Conditional formatting"
LK = "Lookups"
RC = "Files and recovery"
G_CF = "Formatting that follows a rule"
G_LK = "Lookups past the basics"
G_RC = "When the file goes wrong"

GUIDES_F = [

dict(
 slug="excel-conditional-format-another-cell",
 title="Conditional Formatting Based on Another Cell's Value",
 description="Colour a cell by what a different cell says. The trick is the dollar signs — the rule is written for the top-left cell and Excel walks it across the rest.",
 h1="Colour this cell based on what that cell says",
 lead="Highlight the row when the status column says Overdue. Colour the amount when it is over budget. The built-in rules cannot do it &mdash; you need a formula rule, and one detail decides whether it works.",
 category=CF, group=G_CF,
 card_title="Format based on another cell",
 card_blurb="The formula rule, and the dollar signs that decide whether it works.",
 chips=["Any version", "Excel + Google Sheets", "Formula rule"],
 keywords=["excel conditional formatting another cell", "excel highlight row based on cell",
           "excel conditional format formula", "excel format if другой cell",
           "google sheets conditional formatting custom formula", "excel highlight overdue"],
 short_answer="""<p><strong>Use <em>Home &rarr; Conditional Formatting &rarr; New Rule &rarr; Use a
formula</em>, and write the formula as if for the <em>top-left cell of your selection only</em>.</strong>
Excel applies it to every other cell by shifting the references, exactly as it would if you dragged a
formula. So lock the column with a dollar sign &mdash; <code>=$C2="Overdue"</code> &mdash; and the
whole row follows column C.</p>""",
 problem_h="The rule is written once and walked across everything",
 problem="""<p>This is the whole idea, and nothing in the dialog explains it.</p>
<p>You select a range and write one formula. Excel applies that formula to the <em>top-left</em> cell
of the selection, then moves it to every other cell in exactly the way dragging a formula would:
relative references shift, and anything with a dollar sign in front of it does not.</p>
<p>So if you select <code>A2:F100</code> and write <code>=C2="Overdue"</code>, cell <code>B2</code>
tests <code>D2</code>, and <code>C2</code> tests <code>E2</code>. Every cell tests a different column,
and the colours look random.</p>
<p>Writing <code>=$C2="Overdue"</code> pins the column and lets the row move. Now every cell in row 2
tests <code>C2</code>, every cell in row 3 tests <code>C3</code>, and the whole row lights up
together.</p>""",
 symptoms=symptom_table([
   ["Only the first column colours",
    "The reference is fully absolute &mdash; <code>$C$2</code>",
    "Free the row: <code>$C2</code>"],
   ["Colours look scattered at random",
    "Nothing is pinned, so every cell tests a different column",
    "Pin the column: <code>$C2</code>"],
   ["Nothing highlights at all",
    "The formula was written for the wrong row",
    "Write it for the FIRST row of the selection"],
   ["Correct at first, wrong after inserting rows",
    "The Applies To range shifted",
    "Fix it in Manage Rules"],
   ["The rule split into dozens of rules",
    "Copy and paste fragmented the range",
    "Delete them all and reapply once"],
 ]),
 howto_name="How to format a row based on another cell",
 howto_desc="Select the whole range first, write the rule for its top-left cell, and pin the column.",
 steps=[
  dict(h="Select the whole range you want coloured, starting at the top left",
       plain="Select every cell that should change colour — the whole data range, not just the column you are testing. Note which cell is top-left.",
       body="""<p>To colour whole rows, select <code>A2:F100</code>, not column C. Start the selection
at <code>A2</code>, because that is the cell your formula will describe.</p>
<p>Do not include the header row unless you want it coloured too.</p>"""),
  dict(h="Add a formula rule",
       plain="Home > Conditional Formatting > New Rule > Use a formula to determine which cells to format.",
       body="""<p><em>Home &rarr; Conditional Formatting &rarr; New Rule &rarr; Use a formula to
determine which cells to format</em>. It is the last option in the list and the only one that can look
at a different cell.</p>"""),
  dict(h="Write the formula for the top-left cell, pinning the column",
       plain="Write the test as it applies to the first cell of your selection, with a dollar sign before the column letter but not the row number.",
       body="""<p>For a selection starting at <code>A2</code>, testing column C:</p>""" +
       fx("Pin the column, free the row", '=$C2="Overdue"',
          """<p>The <code>$</code> before <code>C</code> stops the column moving as the rule walks
sideways. No <code>$</code> before <code>2</code> lets the row move as it walks down. That is the
entire trick.</p>""")),
  dict(h="Check the Applies To range afterwards",
       plain="Open Manage Rules and check the Applies To box still covers your whole range — it drifts when rows are inserted or cells are copied.",
       body="""<p><em>Conditional Formatting &rarr; Manage Rules</em>, and look at <em>Applies to</em>.
It should be your whole range. Copying and pasting cells inside the range tends to shatter one rule
into several with odd fragments &mdash; when that happens, delete them all and apply once, cleanly.</p>"""),
 ],
 body="""<h2>Useful rules to keep</h2>
<ul>
<li><strong>Overdue:</strong> <code>=AND($D2&lt;TODAY(),$E2="")</code> &mdash; due date passed and
nothing in the completed column.</li>
<li><strong>Over budget:</strong> <code>=$C2&gt;$B2</code> &mdash; actual above planned.</li>
<li><strong>Blank required field:</strong> <code>=$B2=""</code>.</li>
<li><strong>Top ten percent:</strong> <code>=$D2&gt;=PERCENTILE($D$2:$D$100,0.9)</code> &mdash; note
the range is fully pinned, because it is the same range for every row.</li>
<li><strong>Weekend:</strong> <code>=WEEKDAY($A2,2)&gt;5</code>.</li>
</ul>
<h2>Banding a table by group</h2>
<p>To shade alternate <em>groups</em> rather than alternate rows, count the distinct values above and
test whether that count is even. It is a rule that reads badly and looks excellent on a sorted
report.</p>
<h2>Rules run in order, and can stop</h2>
<p>In Manage Rules, rules are applied top to bottom and later ones can overwrite earlier ones. The
<em>Stop If True</em> checkbox halts processing for a cell when a rule matches &mdash; useful for
&ldquo;if it is cancelled, grey it out and ignore every other rule&rdquo;.</p>
<h2>Google Sheets</h2>
<p>Same idea, called <em>Custom formula is</em> under <em>Format &rarr; Conditional formatting</em>.
The dollar-sign behaviour is identical. Sheets applies the rule relative to the top-left of the
range you gave it, exactly as Excel does.</p>""",
 faq=[
  ("How do I highlight a whole row based on one cell?",
   "Select the whole range, add a formula rule, and write it for the top-left cell with the column pinned — for example =$C2=\"Overdue\". Pinning the column is what makes the whole row follow column C."),
  ("Why do only some cells change colour?",
   "The references are wrong for how the rule walks. Fully absolute ($C$2) colours only where that one cell matches; nothing pinned makes every cell test a different column."),
  ("Which cell should the formula be written for?",
   "The top-left cell of the range you selected. Excel applies it there and shifts the references for every other cell, exactly like dragging a formula."),
  ("Why did my rule stop working after I inserted rows?",
   "The Applies To range shifted. Open Manage Rules and check it still covers the whole range."),
  ("Why has one rule turned into twenty?",
   "Copying and pasting cells inside the range fragments the rule. Delete all the fragments and apply the rule once over the whole range."),
  ("Does this work the same in Google Sheets?",
   "Yes. It is called Custom formula is, and the dollar-sign behaviour is identical."),
 ],
 related=[("excel-highlight-duplicates", "Highlighting duplicates"),
          ("excel-conditional-format-ranges-changing", "Stopping rules fragmenting"),
          ("excel-absolute-relative-references", "The $ sign explained")],
),

dict(
 slug="excel-highlight-duplicates",
 title="Highlight Duplicates in Excel — Including Across Columns",
 description="The built-in duplicate rule covers one column. For duplicates across two columns, second-and-later only, or a whole row, you need a formula rule.",
 h1="Show me which of these appear more than once",
 lead="The built-in rule handles a single column and colours every copy, including the first. Most of the time what you actually want is subtler than that.",
 category=CF, group=G_CF,
 card_title="Highlighting duplicates",
 card_blurb="The built-in rule, and the formula versions it cannot do.",
 chips=["Any version", "COUNTIF", "Excel + Google Sheets"],
 keywords=["excel highlight duplicates", "excel duplicate rows conditional formatting",
           "excel find duplicates two columns", "excel highlight second occurrence",
           "google sheets highlight duplicates", "excel duplicate values"],
 short_answer="""<p><strong>For one column, <em>Home &rarr; Conditional Formatting &rarr; Highlight
Cells Rules &rarr; Duplicate Values</em> is enough.</strong> For anything else, use a formula rule
with <code>COUNTIF</code>: <code>=COUNTIF($A$2:$A$500,$A2)&gt;1</code> flags every copy, and
<code>=COUNTIF($A$2:$A2,$A2)&gt;1</code> flags only the second and later &mdash; note the range that
grows as the rule walks down.</p>""",
 problem_h="What the built-in rule cannot do",
 problem="""<p>It is a good rule with three real limits, and each of them matters in practice.</p>
<ul>
<li><strong>It colours every copy, including the first.</strong> When you are deciding what to delete,
that is unhelpful &mdash; you want the extras marked, not the original.</li>
<li><strong>It works on one column at a time.</strong> A duplicate defined by name <em>and</em> date
together is beyond it.</li>
<li><strong>It ignores capitals.</strong> <code>ACME</code> and <code>acme</code> are duplicates to
it. Sometimes right, sometimes very wrong.</li>
</ul>
<p>All three are solved by a formula rule, and all three use <code>COUNTIF</code> in slightly
different ways.</p>""",
 symptoms=symptom_table([
   ["Every copy is highlighted",
    "The built-in rule colours all of them",
    "Use a growing range to flag the extras only"],
   ["Duplicates not detected",
    "Trailing or non-breaking spaces",
    "Clean the column first"],
   ["Numbers not matching text versions",
    "Different types are never equal",
    "Make both the same type"],
   ["Long codes wrongly flagged",
    "<code>COUNTIF</code> compares only the first 15 digits",
    'Compare with <code>&amp;""</code> appended'],
   ["Very slow on a large sheet",
    "<code>COUNTIF</code> over a whole column, per cell",
    "Bound the range to the rows in use"],
 ]),
 howto_name="How to highlight duplicates",
 howto_desc="The built-in rule, then the formula versions for the cases it cannot handle.",
 steps=[
  dict(h="One column, every copy: use the built-in rule",
       plain="Select the column, then Home > Conditional Formatting > Highlight Cells Rules > Duplicate Values.",
       body="""<p>Select the column, then <em>Home &rarr; Conditional Formatting &rarr; Highlight
Cells Rules &rarr; Duplicate Values</em>. Two clicks, and for a quick look it is the right tool.</p>"""),
  dict(h="Flag only the second and later copies",
       plain="Use COUNTIF with a range that starts fixed and ends at the current row, so it only counts what came before.",
       body="""<p>The range grows as the rule walks down, which is what makes this work:</p>""" +
       fx("Extras only", '=COUNTIF($A$2:$A2,$A2)>1',
          """<p><code>$A$2</code> is pinned and <code>$A2</code> is not, so on row 5 the range is
<code>$A$2:$A5</code>. The first occurrence sees a count of 1 and stays uncoloured; every later one
sees 2 or more. This is the rule to use before deleting anything.</p>""")),
  dict(h="Duplicates across two columns",
       plain="Use COUNTIFS with a condition for each column, so a row counts as a duplicate only when both match.",
       body="""<p>When identity depends on two fields:</p>""" +
       fx("Same name AND same date",
          '=COUNTIFS($A$2:$A$500,$A2,$B$2:$B$500,$B2)>1',
          """<p>Select both columns before applying it. Use <code>COUNTIFS</code> rather than joining
the two values into one string &mdash; joining creates false matches where one value ends and the
next begins.</p>""")),
  dict(h="Case-sensitive duplicates",
       plain="COUNTIF ignores capitals. Use SUMPRODUCT with EXACT when ABC123 and abc123 are genuinely different.",
       body="""<p>Where case carries meaning:</p>""" +
       fx("Case-sensitive", '=SUMPRODUCT(--EXACT($A$2:$A$500,$A2))>1',
          """<p><code>EXACT</code> compares capitals as well as characters. Slower than
<code>COUNTIF</code>, so bound the range.</p>""")),
 ],
 body="""<h2>Highlighting the whole duplicate row</h2>
<p>Select the full width of the data and pin the column being tested:</p>
""" + fx("Whole row", '=COUNTIF($A$2:$A$500,$A2)>1',
"""<p>Applied to <code>A2:F500</code>, this colours the entire row for each duplicate, because the
<code>$</code> before <code>A</code> keeps every cell in the row looking at column A.</p>""") + """
<h2>The 15-digit trap</h2>
<p><code>COUNTIF</code> compares numbers with about 15 digits of precision. Two different 16-digit
card numbers or long barcodes can therefore be reported as duplicates when they are not. Force a text
comparison:</p>
""" + fx("Long numbers", '=COUNTIF($A$2:$A$500,$A2&"")>1',
"""<p>The <code>&amp;""</code> makes the criterion text, so the full value is compared rather than a
rounded number.</p>""") + """
<h2>Clean before you trust it</h2>
<p>Every method here compares values exactly as stored. <code>Acme Ltd</code> and <code>Acme
Ltd&nbsp;</code> with a trailing space are not duplicates to any of them, which is precisely how a
duplicate survives a deduplication that reported none.</p>
<h2>Finding duplicates without colouring</h2>
<p>For a count rather than a picture, put <code>=COUNTIF($A$2:$A$500,A2)</code> in a helper column and
filter on it. Easier to act on than colour, and it can be sorted.</p>""",
 faq=[
  ("How do I highlight only the second and later duplicates?",
   "Use a formula rule with a growing range: =COUNTIF($A$2:$A2,$A2)>1. The first occurrence counts 1 and stays uncoloured."),
  ("How do I find duplicates across two columns?",
   "Use COUNTIFS with a condition per column, so a row is a duplicate only when both match. Do not join the values into one string — that creates false matches."),
  ("Is the built-in duplicate rule case-sensitive?",
   "No. ACME and acme are duplicates to it. Use SUMPRODUCT with EXACT if capitals matter."),
  ("Why are two different long numbers flagged as duplicates?",
   "COUNTIF compares numbers at about 15 digits of precision, so longer values look identical. Append &\"\" to the criterion to force a text comparison."),
  ("Why does it miss duplicates I can see?",
   "The values differ by a trailing or non-breaking space. Every method compares values exactly as stored, so clean the column first."),
  ("Why is my sheet slow after adding this?",
   "COUNTIF runs once per cell over the whole range. Bound the range to the rows actually in use rather than using a whole column."),
 ],
 related=[("excel-conditional-format-another-cell", "Format based on another cell"),
          ("excel-unique-values-list", "Getting a list of unique values"),
          ("clean-crm-contact-export-excel", "Cleaning a contact export")],
),

dict(
 slug="excel-conditional-format-ranges-changing",
 title="Stop Excel Conditional Formatting Rules Fragmenting",
 description="One rule becomes forty with odd ranges after copying and pasting. Why it happens, how to repair it, and how to stop it recurring.",
 h1="My one rule has turned into forty",
 lead="Open Manage Rules and there are dozens of near-identical entries with ranges like <code>$A$2:$A$7,$A$14,$A$22:$A$36</code>. Nobody did it on purpose. Copying and pasting inside the range did it.",
 category=CF, group=G_CF,
 card_title="Rules that fragment on their own",
 card_blurb="Why one rule becomes forty, and how to stop it happening again.",
 chips=["Any version", "Manage Rules", "Excel"],
 keywords=["excel conditional formatting rules multiply", "excel conditional format range changing",
           "excel manage rules cleanup", "excel conditional formatting slow",
           "excel duplicate formatting rules", "excel applies to range"],
 short_answer="""<p><strong>Copying and pasting cells inside a formatted range splits the rule, because
the pasted cells bring their own copy of it.</strong> Repair it by deleting every fragment in
<em>Manage Rules</em> and applying the rule once over the whole range. Prevent it by pasting with
<em>Paste Special &rarr; Values</em>, which carries no formatting and therefore no rules.</p>""",
 problem_h="Why the rules multiply",
 problem="""<p>Conditional formatting travels with a cell, exactly like a fill colour or a border.
Copy a formatted cell and paste it three rows down, and the pasted cell arrives carrying its own copy
of the rule.</p>
<p>Excel tries to merge that copy back into the existing rule. When the ranges are adjacent it
succeeds. When they are not, it cannot, so it keeps both &mdash; and the <em>Applies to</em> ranges
start looking like <code>$A$2:$A$7,$A$14,$A$22:$A$36</code>.</p>
<p>Do that for a few weeks and there are forty rules. The sheet slows down, because every rule is
evaluated for every cell it covers, and worse, they begin to disagree: some fragments get edited and
others do not, so identical-looking rows are coloured differently.</p>""",
 symptoms=symptom_table([
   ["Dozens of near-identical rules",
    "Pasting split the original repeatedly",
    "Delete all, apply once"],
   ["Ranges full of commas",
    "Merged fragments that could not be joined",
    "Same fix"],
   ["Identical rows coloured differently",
    "Fragments have drifted apart",
    "Delete all, apply once"],
   ["Scrolling has become slow",
    "Every rule is evaluated per cell",
    "Fewer rules, bounded ranges"],
   ["Formatting appears where there is no data",
    "The range was extended by a paste",
    "Reset Applies To"],
 ]),
 howto_name="How to clean up fragmented rules",
 howto_desc="Delete every fragment, apply once, then change how you paste.",
 steps=[
  dict(h="Look at the damage first",
       plain="Home > Conditional Formatting > Manage Rules, and set the dropdown to This Worksheet to see every rule rather than only those for the selection.",
       body="""<p><em>Home &rarr; Conditional Formatting &rarr; Manage Rules</em>, then set
<em>Show formatting rules for</em> to <strong>This Worksheet</strong>. It defaults to the current
selection, which is why the mess usually goes unnoticed.</p>
<p>Widen the <em>Applies to</em> column. Commas in there are the symptom.</p>"""),
  dict(h="Delete every fragment",
       plain="Select the whole sheet and use Conditional Formatting > Clear Rules > Clear Rules from Entire Sheet.",
       body="""<p>Do not try to repair them individually &mdash; on forty fragments it is slower and
you will miss one. Select all, then <em>Conditional Formatting &rarr; Clear Rules &rarr; Clear Rules
from Entire Sheet</em>.</p>
<p>Write your rules down first. This removes all of them.</p>"""),
  dict(h="Apply the rule once, over the whole range",
       plain="Select the full range in one go and add the rule a single time. Do not apply it column by column.",
       body="""<p>Select <code>A2:F500</code> in one action and add the rule once. One rule with one
clean range is faster and cannot drift out of step with itself.</p>"""),
  dict(h="Paste values from now on",
       plain="Use Paste Special > Values, or Ctrl+Alt+V then V, when moving data inside a formatted range.",
       body="""<p><em>Paste Special &rarr; Values</em> (<strong>Ctrl+Alt+V</strong> then
<strong>V</strong>) carries no formatting, so it cannot carry a rule. This one habit prevents the
whole problem.</p>
<p>It also stops you dragging fill colours and borders around, which is the other way a tidy sheet
slowly stops looking tidy.</p>"""),
 ],
 body="""<h2>Why it slows the sheet down</h2>
<p>Every conditional formatting rule is re-evaluated for every cell in its range whenever anything on
the sheet changes. One rule over 3,000 cells is 3,000 evaluations. Forty fragments covering the same
cells is 120,000, for exactly the same visual result.</p>
<p>Rules that use <code>COUNTIF</code> or <code>INDIRECT</code> are much heavier again, and
<code>INDIRECT</code> is volatile, meaning it recalculates on <em>every</em> change anywhere.</p>
<h2>Use a table where you can</h2>
<p>A range formatted as a table (<strong>Ctrl+T</strong>) extends its formatting to new rows on its
own, which removes one of the reasons people copy formatted cells around in the first place.</p>
<h2>Keep rules to whole columns of a bounded range</h2>
<p>Applying a rule to <code>A:A</code> covers 1,048,576 cells. Applying it to <code>A2:A5000</code>
covers what you have. On a workbook with several rules this is the difference between instant and
sluggish.</p>
<h2>Check it periodically</h2>
<p>On any workbook that several people edit, open Manage Rules with the worksheet view once a month.
It takes ten seconds and it catches the drift long before anyone notices the colours have stopped
making sense.</p>""",
 faq=[
  ("Why do my conditional formatting rules keep multiplying?",
   "Conditional formatting travels with a cell. Copying and pasting inside a formatted range brings a copy of the rule, and where Excel cannot merge it back it keeps both."),
  ("How do I fix dozens of fragmented rules?",
   "Note the rules, clear all rules from the entire sheet, then apply each one once over the whole range. Repairing fragments individually is slower and you will miss some."),
  ("How do I stop it happening again?",
   "Paste with Paste Special > Values when moving data inside a formatted range. Values carry no formatting, so they cannot carry a rule."),
  ("Do conditional formatting rules slow Excel down?",
   "Yes. Each rule is re-evaluated for every cell it covers whenever anything changes, so fragments multiply the work for no visual difference. Rules using INDIRECT are worse, because it is volatile."),
  ("Should I apply rules to whole columns?",
   "No. A whole-column rule covers over a million cells. Bound it to the rows you actually use."),
  ("How do I see all the rules on a sheet?",
   "In Manage Rules, change the dropdown from the current selection to This Worksheet. It defaults to the selection, which is why the mess goes unnoticed."),
 ],
 related=[("excel-conditional-format-another-cell", "Format based on another cell"),
          ("excel-highlight-duplicates", "Highlighting duplicates"),
          ("excel-formulas-not-updating", "My formulas stopped recalculating")],
),

dict(
 slug="excel-last-match-lookup",
 title="Get the LAST Match in Excel, Not the First",
 description="VLOOKUP returns the first match. To get the most recent price, status or reading, use XLOOKUP's search mode or the classic LOOKUP trick.",
 h1="I need the most recent one, not the first one",
 lead="The price list has three rows for the same product because the price changed twice. <code>VLOOKUP</code> hands you the oldest one, because the first match is the only match it knows how to find.",
 category=LK, group=G_LK,
 card_title="The last match, not the first",
 card_blurb="The most recent price, status or reading — three ways, by version.",
 chips=["XLOOKUP or LOOKUP", "Any version", "Excel + Google Sheets"],
 keywords=["excel last match lookup", "excel vlookup last value", "excel xlookup search mode",
           "excel lookup most recent", "excel find last occurrence", "excel latest price lookup"],
 short_answer="""<p><strong>On Excel 365 or 2021, add <code>-1</code> as <code>XLOOKUP</code>'s fifth
argument to search from the bottom up.</strong> On any version,
<code>=LOOKUP(2,1/(A:A=key),B:B)</code> returns the last match &mdash; an old trick that works
everywhere and reads like nonsense until you know why. Both beat sorting your data backwards, which
solves it once and breaks the next time someone sorts it.</p>""",
 problem_h="Why first-match is the default, and when that hurts",
 problem="""<p>Most lookups are against a reference table where each key appears once, so first and
last are the same thing and the question never arises.</p>
<p>It arises the moment your table is a <em>log</em> rather than a reference: a price history, a
status trail, a series of meter readings. There the newest row is the one that matters, and it is at
the bottom.</p>
<p><code>VLOOKUP</code> and <code>MATCH</code> both scan from the top and stop at the first hit. There
is no argument to change that. The fix is either a function that can search backwards, or a
calculation that finds the largest matching position rather than the first.</p>""",
 symptoms=symptom_table([
   ["Getting an old price",
    "First match, and the table is a history",
    "Search from the bottom"],
   ["Status is out of date",
    "Same cause",
    "<code>XLOOKUP</code> with <code>-1</code>"],
   ["Right until a row was added",
    "The new row is below the one being found",
    "Search from the bottom"],
   ["<code>#N/A</code> from the <code>LOOKUP</code> trick",
    "No match at all, or the key type differs",
    "Wrap in <code>IFERROR</code>; check types"],
   ["Correct only while sorted",
    "The workaround was sorting",
    "Use a formula that does not depend on order"],
 ]),
 howto_name="How to find the last matching value",
 howto_desc="Use the version-appropriate method, then handle rows with no match.",
 steps=[
  dict(h="Excel 365 or 2021: XLOOKUP with search mode -1",
       plain="XLOOKUP's fifth argument controls direction. -1 searches from the last item backwards.",
       body="""<p>The fifth argument is the one nobody reads about:</p>""" +
       fx("Search from the bottom",
          '=XLOOKUP(G1,A2:A500,B2:B500,"not found",0,-1)',
          """<p>Arguments in order: what to find, where to look, what to return, what if missing,
match mode (0 = exact), search mode (<code>-1</code> = last to first). The two zeros before it must be
there as placeholders.</p>""")),
  dict(h="Any version: the LOOKUP trick",
       plain="LOOKUP(2, 1/(range=key), result) returns the last match. It works in every version of Excel and in Sheets.",
       body="""<p>This appears in workbooks everywhere and almost nobody can explain it:</p>""" +
       fx("The classic", '=IFERROR(LOOKUP(2,1/($A$2:$A$500=G1),$B$2:$B$500),"not found")',
          """<p><code>$A$2:$A$500=G1</code> gives TRUE and FALSE per row. Dividing 1 by those gives
1 for TRUE and a divide-by-zero error for FALSE. <code>LOOKUP</code> then searches for 2 in a list
whose largest value is 1, never finds it, and by design settles on the <em>last</em> value that was
not an error. That last 1 is the last match.</p>""")),
  dict(h="Add conditions with a second test",
       plain="Multiply another condition into the same expression to get the last match that also satisfies it.",
       body="""<p>The last price for a product <em>from a particular supplier</em>:</p>""" +
       fx("Two conditions",
          '=LOOKUP(2,1/(($A$2:$A$500=G1)*($C$2:$C$500=G2)),$B$2:$B$500)',
          """<p>Multiplying the two TRUE/FALSE lists gives 1 only where both hold. The rest of the
trick is unchanged.</p>""")),
  dict(h="Or find the position, then fetch it",
       plain="MAX with IF finds the largest matching row number, and INDEX fetches from it. Clearer to read than the LOOKUP trick.",
       body="""<p>More readable, if longer:</p>""" +
       fx("Largest matching row",
          '=INDEX($B$2:$B$500,MAX(IF($A$2:$A$500=G1,ROW($A$2:$A$500)-1)))',
          """<p>On Excel 2019 and earlier this needs <strong>Ctrl+Shift+Enter</strong>. The
<code>-1</code> converts a sheet row number into a position within the range, and getting it wrong by
one is the usual bug here.</p>""")),
 ],
 howto_extra="",
 body="""<h2>Getting the whole row</h2>
<p>Wrap the position in <code>INDEX</code> over the full width:</p>
""" + fx("Every column of the last matching row",
'=INDEX($A$2:$F$500,MATCH(2,1/($A$2:$A$500=G1)),0)',
"""<p>The <code>0</code> as the column argument means &ldquo;all columns&rdquo;, so on a modern Excel
the whole row spills.</p>""") + """
<h2>Sort by date, not by row order</h2>
<p>&ldquo;Last&rdquo; here means last <em>in the sheet</em>, which is only the most recent if rows were
added in date order. If they were not, sort by date first, or find the largest date that matches and
look that up instead. This is a real source of quietly wrong answers in workbooks that several people
append to.</p>
<h2>A dedicated date column beats row position</h2>
<p>If &ldquo;most recent&rdquo; is the question you keep asking, do not rely on position at all:</p>
""" + fx("Most recent by date",
'=MAXIFS($D$2:$D$500,$A$2:$A$500,G1)',
"""<p>That gives the latest date for the key; use it as a second criterion in a
<code>XLOOKUP</code> or <code>SUMIFS</code> to fetch the value. Slower, and it cannot be broken by
somebody sorting the sheet.</p>""") + """
<h2>Google Sheets</h2>
<p>Sheets has no <code>XLOOKUP</code> search mode, but the <code>LOOKUP</code> trick works exactly as
written. <code>QUERY</code> is often clearer there:
<code>=QUERY(A:B,"select B where A='"&amp;G1&amp;"' order by A desc limit 1")</code>.</p>""",
 faq=[
  ("How do I make VLOOKUP return the last match?",
   "You cannot — VLOOKUP always scans from the top. Use XLOOKUP with search mode -1, or the LOOKUP(2,1/(range=key),result) trick, which works in every version."),
  ("How does the LOOKUP(2,1/...) trick work?",
   "Dividing 1 by a TRUE/FALSE list gives 1 for matches and errors for the rest. LOOKUP searches for 2, never finds it, and settles on the last non-error value — which is the last match."),
  ("What is XLOOKUP's fifth argument?",
   "Search mode. 1 searches first to last, -1 searches last to first. The match mode argument before it must be supplied as a placeholder."),
  ("Does 'last' mean most recent?",
   "Only if rows were added in date order. If they were not, sort by date first, or find the largest matching date with MAXIFS and look that up instead."),
  ("Can I get the last match on two conditions?",
   "Yes. Multiply the conditions inside the trick: LOOKUP(2,1/((A=x)*(C=y)),B)."),
  ("What is the equivalent in Google Sheets?",
   "The LOOKUP trick works unchanged. QUERY is often clearer: select the column, order by descending, limit 1."),
 ],
 related=[("excel-join-two-sheets-lookup", "Joining two sheets with a lookup"),
          ("excel-last-non-empty-cell", "The last non-empty cell in a column"),
          ("excel-compare-two-lists", "Find what is in list A but not list B")],
),

dict(
 slug="excel-last-non-empty-cell",
 title="Find the Last Non-Empty Cell in an Excel Column",
 description="Get the latest value in a growing column without a fixed range. LOOKUP works everywhere; XLOOKUP and TAKE are clearer if you have them.",
 h1="I want the latest reading, wherever the column ends",
 lead="A column that grows every week, and a summary that should always show the newest value. A fixed reference goes stale the moment somebody adds a row, and a range that is &ldquo;big enough&rdquo; finds a blank.",
 category=LK, group=G_LK,
 card_title="The last non-empty cell",
 card_blurb="The newest value in a growing column, without a range that goes stale.",
 chips=["Any version", "Growing data", "Excel + Google Sheets"],
 keywords=["excel last non empty cell", "excel last value in column", "excel latest value formula",
           "excel lookup last row", "excel dynamic last cell", "excel find end of column"],
 short_answer="""<p><strong><code>=LOOKUP(2,1/(A:A&lt;&gt;""),A:A)</code> returns the last non-empty
cell in column A, in every version of Excel and in Google Sheets.</strong> On Microsoft 365
<code>=TAKE(FILTER(A:A,A:A&lt;&gt;""),-1)</code> reads far more clearly. Both skip gaps, which is why
they beat counting rows &mdash; <code>COUNT</code> based approaches break the moment there is a blank
in the middle.</p>""",
 problem_h="Why counting rows is not enough",
 problem="""<p>The obvious approach is to count how many values there are and go to that row.
<code>=INDEX(A:A,COUNTA(A:A))</code> works perfectly until there is a gap.</p>
<p>With a blank in the middle, <code>COUNTA</code> returns one less than the row you want, so you get
the second-to-last value. Nothing errors. The number is simply wrong, and it stays wrong until
somebody notices the summary disagrees with the sheet.</p>
<p>Gaps are normal in real data: a week nobody recorded, a row deleted, a section separated by a blank
line for readability. So the method has to find the last <em>value</em>, not the last
<em>position</em>.</p>""",
 symptoms=symptom_table([
   ["Getting the second-to-last value",
    "A gap, and a <code>COUNTA</code>-based formula",
    "Use a method that searches for the value"],
   ["Reference goes stale",
    "A fixed cell reference",
    "One of the formulas below"],
   ["Returns 0",
    "Landed on a genuinely empty cell",
    'Test with <code>&lt;&gt;""</code>, not <code>&lt;&gt;0</code>'],
   ["Returns a blank-looking value",
    'A formula returned <code>""</code>',
    'Filter with <code>&lt;&gt;""</code>, which excludes it'],
   ["Slow on a whole column",
    "Over a million cells scanned",
    "Bound the range"],
 ]),
 howto_name="How to find the last non-empty cell",
 howto_desc="Pick by version, then adapt it for the last row rather than the last value.",
 steps=[
  dict(h="Any version: the LOOKUP form",
       plain="LOOKUP(2,1/(range<>\"\"),range) returns the last cell that is not empty, skipping gaps.",
       body="""<p>The same trick as finding a last match, with the test changed:</p>""" +
       fx("Works everywhere", '=LOOKUP(2,1/($A$2:$A$5000<>""),$A$2:$A$5000)',
          """<p>Gaps are skipped because a blank produces an error, and <code>LOOKUP</code> settles on
the last value that was not one.</p>""")),
  dict(h="Microsoft 365: TAKE and FILTER",
       plain="FILTER removes the blanks and TAKE with -1 returns the last remaining item.",
       body="""<p>Far easier to read, and to explain to whoever inherits the file:</p>""" +
       fx("The modern form", '=TAKE(FILTER(A2:A5000,A2:A5000<>""),-1)',
          """<p><code>-1</code> means &ldquo;from the end&rdquo;. Anyone can work out what this does
at a glance, which the <code>LOOKUP</code> form cannot claim.</p>""")),
  dict(h="Get the value from a different column",
       plain="Use the same test on the key column but return from another column, to get the value that sits beside the last entry.",
       body="""<p>The date of the last reading, say, rather than the reading itself:</p>""" +
       fx("Return from a neighbour", '=LOOKUP(2,1/($B$2:$B$5000<>""),$A$2:$A$5000)',
          """<p>Test column B, return from column A. Both ranges must be the same height or the
answers come from the wrong rows.</p>""")),
  dict(h="Get the row number instead of the value",
       plain="Swap the return range for ROW to find where the data ends, which is useful for building other ranges.",
       body="""<p>When you need the position rather than the value:</p>""" +
       fx("Where does the data end?",
          '=LOOKUP(2,1/($A$2:$A$5000<>""),ROW($A$2:$A$5000))',
          """<p>Handy for a named range that resizes itself, though a table
(<strong>Ctrl+T</strong>) does that better and with no formula at all.</p>""")),
 ],
 body="""<h2>A table is usually the better answer</h2>
<p>If the column grows because rows are appended, format the range as a table with
<strong>Ctrl+T</strong>. A table's own reference grows with it, so charts, formulas and pivot tables
all follow automatically and no last-cell formula is needed.</p>
<p>Reach for these formulas when a table is not possible &mdash; a fixed layout, a protected sheet, or
data with deliberate gaps in it.</p>
<h2>Last non-empty in a row</h2>
<p>Same shape, sideways: <code>=LOOKUP(2,1/(A2:Z2&lt;&gt;""),A2:Z2)</code>. Useful for a report with a
column per month, to show the most recent month that has data.</p>
<h2>Beware formula blanks</h2>
<p>A cell holding <code>=IF(x,"",y)</code> looks empty and is not. The <code>&lt;&gt;""</code> test
used here correctly excludes it. A test of <code>&lt;&gt;0</code> would not, and would return an
empty-looking answer.</p>
<h2>Whole columns are slow</h2>
<p><code>A:A</code> scans over a million cells every recalculation. One is unnoticeable; twenty in a
workbook is not. Bound them to a realistic maximum.</p>""",
 faq=[
  ("How do I get the last value in a column?",
   "Use =LOOKUP(2,1/(range<>\"\"),range) in any version, or =TAKE(FILTER(range,range<>\"\"),-1) on Microsoft 365, which is much easier to read."),
  ("Why does INDEX with COUNTA give the wrong answer?",
   "COUNTA counts values, not positions. With a gap in the column, the count is smaller than the row you want, so you get an earlier value."),
  ("Does this skip blank cells in the middle?",
   "Yes. Both methods search for the last cell that is not empty rather than counting rows, so gaps do not matter."),
  ("How do I get the value from another column?",
   "Test the key column and return from the other one: =LOOKUP(2,1/(B:B<>\"\"),A:A). Both ranges must be the same height."),
  ("Should I use a table instead?",
   "Usually yes, if the column simply grows by appending. A table's reference grows with it, so nothing needs a last-cell formula at all."),
  ("Why is my workbook slow after adding these?",
   "Whole-column references scan over a million cells on every recalculation. Bound them to a realistic maximum row."),
 ],
 related=[("excel-last-match-lookup", "The last match, not the first"),
          ("excel-apply-formula-entire-column", "Applying a formula to a whole column"),
          ("excel-return-blank-not-zero", "Returning a real blank instead of zero")],
),

dict(
 slug="excel-sheet-name-in-cell",
 title="Put the Sheet Name in a Cell in Excel",
 description="CELL with MID extracts the sheet name, and it needs a saved file plus a reference argument. Also the file name, the path, and why it can show the wrong sheet.",
 h1="I want the tab's name to appear in a heading",
 lead="Twelve monthly sheets, each with a title that should say which month it is. Typing it into each one guarantees that one of them will say the wrong month by March.",
 category=LK, group=G_LK,
 card_title="The sheet name in a cell",
 card_blurb="One formula, two conditions nobody mentions, and why it sometimes shows the wrong tab.",
 chips=["Any version", "Needs a saved file", "Excel"],
 keywords=["excel sheet name in cell", "excel tab name formula", "excel cell filename",
           "excel get worksheet name", "excel file name in cell", "excel dynamic sheet title"],
 short_answer="""<p><strong><code>=MID(CELL("filename",A1),FIND("]",CELL("filename",A1))+1,255)</code>
returns the name of the sheet the formula is on.</strong> Two conditions that catch everyone out: the
workbook must have been <strong>saved at least once</strong>, and the <code>A1</code> argument is not
optional &mdash; without it, <code>CELL</code> reports whichever sheet was last active, so every tab
can show the same name.</p>""",
 problem_h="Why there is no SHEETNAME function",
 problem="""<p>There simply is not one, in any version. <code>CELL("filename")</code> is the only
route, and it returns the whole thing:</p>
<p><code>C:\\Users\\you\\Documents\\[Budget.xlsx]January</code></p>
<p>The sheet name is everything after the closing square bracket, so the formula finds that bracket
and takes the rest. That is all the <code>MID</code> and <code>FIND</code> are doing.</p>
<p>The two traps are both about <code>CELL</code> rather than the string handling. It returns an empty
string on a workbook that has never been saved, because there is no path yet. And without a cell
reference it reports the <em>last active</em> sheet, not the sheet the formula lives on &mdash; so all
twelve tabs show whichever one you clicked last.</p>""",
 symptoms=symptom_table([
   ["Returns nothing",
    "The workbook has never been saved",
    "Save it once"],
   ["Every tab shows the same name",
    "The <code>A1</code> argument was left out",
    'Use <code>CELL("filename",A1)</code>'],
   ["Shows the wrong sheet until you click",
    "Same cause &mdash; last active sheet",
    "Add the reference argument"],
   ["Stale after renaming the tab",
    "<code>CELL</code> does not always recalculate",
    "Press F9"],
   ["Returns the whole path",
    "The <code>MID</code> is taking from the wrong position",
    'Find <code>"]"</code> and take from one past it'],
 ]),
 howto_name="How to show a sheet name in a cell",
 howto_desc="Save the file, use the reference argument, then extract the part you want.",
 steps=[
  dict(h="Save the workbook first",
       plain="CELL(\"filename\") returns an empty string until the file has been saved once, because there is no path to report.",
       body="""<p>A brand-new workbook has no path, so there is nothing for <code>CELL</code> to
return. Save it once and the formula starts working. This is the most common reason it appears
broken.</p>"""),
  dict(h="Include the cell reference — it is not optional",
       plain="Always write CELL(\"filename\",A1). Without the second argument it reports the last active sheet, so every tab can show the same name.",
       body="""<p>The second argument tells <code>CELL</code> which cell to describe, and therefore
which sheet:</p>""" +
       fx("The sheet name", '=MID(CELL("filename",A1),FIND("]",CELL("filename",A1))+1,255)',
          """<p>Leave out <code>A1</code> and every one of your twelve tabs shows whichever sheet was
last selected. It looks right while you build it and wrong to everyone else.</p>""")),
  dict(h="Use it in a heading",
       plain="Join it to text with & to build a title that follows the tab name.",
       body="""<p>Join it to whatever the heading needs:</p>""" +
       fx("A self-updating title",
          '="Sales report - "&MID(CELL("filename",A1),FIND("]",CELL("filename",A1))+1,255)',
          """<p>Rename the tab to <em>February</em> and the heading follows. Nobody has to remember to
change it, which is the point.</p>""")),
  dict(h="Get the file name or the folder instead",
       plain="The same string holds the path and the file name — take different parts of it.",
       body="""<p>All three come from the same call:</p>""" +
       fx("File name and folder",
          '=MID(CELL("filename",A1),FIND("[",CELL("filename",A1))+1,\n'
          '   FIND("]",CELL("filename",A1))-FIND("[",CELL("filename",A1))-1)\n'
          '=LEFT(CELL("filename",A1),FIND("[",CELL("filename",A1))-1)',
          """<p>The first returns <code>Budget.xlsx</code>; the second returns the folder. Useful in a
printed footer, where knowing which file a page came from saves real time later.</p>""")),
 ],
 body="""<h2>It does not always update</h2>
<p><code>CELL</code> recalculates when the sheet does, and renaming a tab does not always count as a
change. If the name looks stale, press <strong>F9</strong>. On a workbook where this matters, say so
in a note next to it rather than leaving the next person to distrust the number.</p>
<h2>Referring to a sheet whose name is in a cell</h2>
<p>The reverse problem &mdash; building a reference from a name in a cell &mdash; needs
<code>INDIRECT</code>:</p>
""" + fx("A reference built from text", '=INDIRECT("\'"&A1&"\'!B5")',
"""<p>The single quotes handle sheet names with spaces in them. Two warnings: <code>INDIRECT</code> is
volatile, so it recalculates constantly and slows large workbooks; and it cannot see a closed
workbook, so it breaks on external references.</p>""") + """
<h2>Listing every sheet name</h2>
<p>There is no formula for it without VBA or a defined name using the old <code>GET.WORKBOOK</code>
macro function, which forces the file to <code>.xlsm</code>. Power Query can do it cleanly by pointing
at the workbook itself, which is the better answer on a modern Excel.</p>
<h2>Google Sheets</h2>
<p>Sheets has no <code>CELL("filename")</code> equivalent for the sheet name. It needs a short Apps
Script custom function, which is the closest thing to VBA there.</p>""",
 faq=[
  ("How do I display the sheet name in a cell?",
   "Use =MID(CELL(\"filename\",A1),FIND(\"]\",CELL(\"filename\",A1))+1,255). The workbook must have been saved at least once."),
  ("Why does the formula return nothing?",
   "The workbook has never been saved, so there is no path for CELL to report. Save it once."),
  ("Why does every tab show the same sheet name?",
   "The A1 argument was omitted. Without a cell reference, CELL reports the last active sheet rather than the sheet the formula is on."),
  ("Why does it not update when I rename the tab?",
   "CELL does not always treat a rename as a change worth recalculating for. Press F9 to force it."),
  ("How do I get the file name rather than the sheet name?",
   "Take the part between the square brackets instead of the part after the closing one."),
  ("Is there a way to list every sheet name?",
   "Not with a plain formula. It needs VBA, a defined name using the old GET.WORKBOOK macro, or Power Query pointed at the workbook itself."),
 ],
 related=[("excel-last-non-empty-cell", "The last non-empty cell in a column"),
          ("excel-formulas-not-updating", "My formulas stopped recalculating"),
          ("excel-column-number-to-letter", "Turning a column number into a letter")],
),

dict(
 slug="excel-column-number-to-letter",
 title="Convert a Column Number to a Letter in Excel",
 description="Turn 27 into AA and back again. ADDRESS with SUBSTITUTE does it one way, COLUMN does the other — for when a position has to become a reference.",
 h1="I have column 27 and I need to know it is AA",
 lead="A formula gave you a position and you need the letter, or you have a letter and need the number. Both are one formula, and neither is remotely obvious.",
 category=LK, group=G_LK,
 card_title="Column number to letter",
 card_blurb="27 becomes AA, and back again. One formula each way.",
 chips=["Any version", "ADDRESS + COLUMN", "Excel + Google Sheets"],
 keywords=["excel column number to letter", "excel column letter to number", "excel address function",
           "excel convert column index", "excel column name formula", "excel get column letter"],
 short_answer="""<p><strong><code>=SUBSTITUTE(ADDRESS(1,27,4),"1","")</code> returns
<code>AA</code>.</strong> <code>ADDRESS</code> builds the reference <code>AA1</code> and
<code>SUBSTITUTE</code> removes the row number. Going the other way,
<code>=COLUMN(AA1)</code> returns <code>27</code>. The <code>4</code> is what makes
<code>ADDRESS</code> give a relative reference rather than <code>$AA$1</code>.</p>""",
 problem_h="Why the letters are not a simple pattern",
 problem="""<p>Column letters look like counting until you reach the end of the alphabet. Then column
27 is <code>AA</code>, 28 is <code>AB</code>, 703 is <code>AAA</code>, and the last column, 16,384, is
<code>XFD</code>.</p>
<p>It resembles base 26 but is not quite, because there is no zero digit &mdash; <code>Z</code> is
followed by <code>AA</code>, not by <code>A0</code>. Writing the conversion yourself is a small,
fiddly piece of arithmetic that is easy to get wrong at exactly the boundaries.</p>
<p><code>ADDRESS</code> already knows all of it. Let it build a reference and take the letters off the
front.</p>""",
 symptoms=symptom_table([
   ["Getting <code>$AA$1</code>",
    "Default absolute reference",
    "Pass <code>4</code> as the third argument"],
   ["Row digits left in the answer",
    "The row number is still attached",
    'Substitute <code>"1"</code> away'],
   ["Wrong for column 10 with row 10",
    'The <code>SUBSTITUTE</code> removed a <code>"1"</code> from the letters',
    "Always build with row 1"],
   ["<code>#VALUE!</code>",
    "The column number is 0 or negative",
    "Columns start at 1"],
   ["Need it inside another formula",
    "The letter is text, not a reference",
    "Use <code>INDEX</code>, not <code>INDIRECT</code>"],
 ]),
 howto_name="How to convert between column numbers and letters",
 howto_desc="Build a reference and strip the row, or read a reference's column number.",
 steps=[
  dict(h="Number to letter",
       plain="ADDRESS(1, number, 4) builds a relative reference like AA1; SUBSTITUTE removes the 1.",
       body="""<p>Always build with row <code>1</code>, so there is exactly one digit to remove:</p>""" +
       fx("27 to AA", '=SUBSTITUTE(ADDRESS(1,27,4),"1","")',
          """<p>The <code>4</code> means a relative reference. Leave it out and you get
<code>$AA$1</code>, and the dollar signs come along for the ride.</p>""")),
  dict(h="Letter to number",
       plain="COLUMN with a reference returns its number. INDIRECT turns a letter held in a cell into a reference first.",
       body="""<p>Directly, or from a cell:</p>""" +
       fx("AA to 27", '=COLUMN(AA1)\n=COLUMN(INDIRECT(A1&"1"))',
          """<p>The second reads the letter from <code>A1</code>. <code>INDIRECT</code> is volatile, so
avoid it in a column of thousands of formulas.</p>""")),
  dict(h="Get the letter of the current cell",
       plain="Combine the two: ADDRESS with COLUMN() returns the letter of the cell the formula is in.",
       body="""<p>Useful in a header row that labels itself:</p>""" +
       fx("This cell's own column", '=SUBSTITUTE(ADDRESS(1,COLUMN(),4),"1","")',
          """<p>Fill it across and each cell reports its own letter.</p>""")),
  dict(h="Prefer INDEX over building a reference",
       plain="If the goal is to fetch a value from column N, INDEX takes the number directly and needs no letter at all.",
       body="""<p>Most of the time the letter is a means to an end, and the end does not need it:</p>""" +
       fx("Skip the letter entirely", '=INDEX($A$1:$Z$100,5,27)',
          """<p>Row 5, column 27, no letter and no <code>INDIRECT</code>. Faster, not volatile, and it
survives inserted columns. Reach for the letter only when a human has to read it.</p>""")),
 ],
 body="""<h2>Why row 1 matters in the trick</h2>
<p><code>SUBSTITUTE</code> removes <em>every</em> occurrence of what you give it. Build
<code>ADDRESS(10,10,4)</code> and you get <code>J10</code>; substituting <code>"10"</code> away leaves
<code>J</code>, which is right by luck. Build <code>ADDRESS(1,1,4)</code> for column 1 and you get
<code>A1</code>, and removing <code>"1"</code> leaves <code>A</code>, which is right by design.</p>
<p>Always build with row 1 and remove <code>"1"</code>. It is correct for every column, including the
ones with a 1 in the row that would otherwise bite.</p>
<h2>Turning off letters altogether</h2>
<p>Excel can label columns with numbers instead: <em>File &rarr; Options &rarr; Formulas &rarr; R1C1
reference style</em>. Then column 27 is simply 27. It changes how every formula is written, so it is a
whole-workbook decision rather than a convenience, but for anyone working with column positions
constantly it removes the problem at the source.</p>
<h2>Where this actually comes up</h2>
<ul>
<li><code>MATCH</code> returned a position and you need to tell somebody the column.</li>
<li>Building a range for <code>INDIRECT</code> &mdash; though <code>INDEX</code> is nearly always
better.</li>
<li>Writing an error message that names a column a person can find.</li>
<li>Generating documentation for a wide sheet.</li>
</ul>""",
 faq=[
  ("How do I convert a column number to a letter?",
   "Use =SUBSTITUTE(ADDRESS(1,27,4),\"1\",\"\"). ADDRESS builds the reference AA1 and SUBSTITUTE removes the row number."),
  ("What does the 4 in ADDRESS do?",
   "It asks for a relative reference. Without it you get $AA$1 and the dollar signs end up in your answer."),
  ("How do I convert a letter back to a number?",
   "=COLUMN(AA1) returns 27. If the letter is in a cell, use =COLUMN(INDIRECT(A1&\"1\")), though INDIRECT is volatile."),
  ("Why must I build with row 1?",
   "SUBSTITUTE removes every occurrence of the text you give it. Building with row 1 means there is exactly one digit to remove, which is correct for every column."),
  ("Do I need the letter at all?",
   "Often not. INDEX takes a column number directly, so if you are fetching a value there is no need to build a reference from a letter."),
  ("Can I make Excel show numbers instead of letters?",
   "Yes — File > Options > Formulas > R1C1 reference style. It changes how every formula is written, so treat it as a whole-workbook decision."),
 ],
 related=[("excel-sheet-name-in-cell", "The sheet name in a cell"),
          ("excel-last-non-empty-cell", "The last non-empty cell in a column"),
          ("excel-join-two-sheets-lookup", "Joining two sheets with a lookup")],
),

dict(
 slug="excel-recover-unsaved-file",
 title="Recover an Excel File You Closed Without Saving",
 description="Excel keeps autorecover copies of unsaved work. Where to find them, how long they last, and the settings that decide whether there is anything to find.",
 h1="I closed it without saving and it was three hours of work",
 lead="It is recoverable far more often than people think. Excel keeps periodic copies of unsaved work, including files that were never saved at all &mdash; but only for a while, and only if the settings allowed it.",
 category=RC, group=G_RC,
 card_title="Recovering unsaved work",
 card_blurb="Where the autorecover copies are, how long they last, and what to check first.",
 chips=["Act quickly", "Any version", "Excel"],
 keywords=["excel recover unsaved file", "excel autorecover", "excel recover closed without saving",
           "excel temporary files", "excel unsaved workbook", "excel version history"],
 short_answer="""<p><strong>Open Excel and go to <em>File &rarr; Open &rarr; Recover Unsaved
Workbooks</em>, at the bottom of the recent files list.</strong> That folder holds autorecover copies
of files never saved. For a file that <em>was</em> saved but has lost recent changes, open it and check
<em>File &rarr; Info &rarr; Manage Workbook</em> for earlier versions. Do this before doing anything
else &mdash; the copies are deleted on a timer.</p>""",
 problem_h="What Excel keeps, and for how long",
 problem="""<p>Two different safety nets, and knowing which applies decides where you look.</p>
<p><strong>Autorecover</strong> saves a snapshot every ten minutes by default, into a hidden folder.
It covers a crash, and it covers closing without saving. For a workbook that was <em>never</em> saved,
the copy is kept for four days. For one that was saved at least once, the last autorecover copy is
kept when you close without saving &mdash; but only if <em>Keep the last autorecovered version if I
close without saving</em> is switched on.</p>
<p><strong>Version history</strong> applies to files stored on OneDrive or SharePoint. It is far
better: proper versions, kept for much longer, restorable in a click. If your file was on OneDrive,
start there.</p>
<p>Neither survives a file that was never opened long enough for a snapshot. If you worked for four
minutes with a ten-minute interval, there may be nothing.</p>""",
 symptoms=symptom_table([
   ["Closed without saving",
    "Autorecover may hold a copy",
    "File &rarr; Open &rarr; Recover Unsaved Workbooks"],
   ["Excel crashed",
    "Document Recovery normally appears on restart",
    "Reopen Excel before anything else"],
   ["Saved, but recent changes lost",
    "An earlier version may exist",
    "File &rarr; Info &rarr; Manage Workbook"],
   ["File is on OneDrive",
    "Full version history is available",
    "Right-click the file &rarr; Version history"],
   ["Nothing in the recovery folder",
    "Autorecover was off, or too little time passed",
    "Check the interval setting for next time"],
 ]),
 howto_name="How to recover an unsaved Excel file",
 howto_desc="Check each place in order, starting with the one most likely to have it.",
 steps=[
  dict(h="Do not create new files first",
       plain="Autorecover copies are cleaned up on a timer and as new ones are made. Look for the file before doing more work in Excel.",
       body="""<p>Every hour that passes and every new file worked on makes recovery less likely. Do
this first, before carrying on with anything else.</p>"""),
  dict(h="Recover Unsaved Workbooks",
       plain="File > Open, scroll to the bottom of the recent files list, and click Recover Unsaved Workbooks.",
       body="""<p><em>File &rarr; Open</em>, then scroll to the very bottom of the recent list and
click <strong>Recover Unsaved Workbooks</strong>. It opens the folder holding autorecover copies of
files that were never saved.</p>
<p>They have unhelpful names and are ordered by time. Open the most recent and check it. Save it
somewhere sensible immediately.</p>"""),
  dict(h="Check earlier versions of a saved file",
       plain="Open the file and look at File > Info > Manage Workbook for autorecover versions from the current session.",
       body="""<p>For a file that exists but has lost changes, open it and go to <em>File &rarr; Info
&rarr; Manage Workbook</em>. Any autorecover versions are listed there.</p>
<p>The same menu has <strong>Recover Unsaved Workbooks</strong> as an option, which is the same folder
by another route.</p>"""),
  dict(h="Use version history if it is on OneDrive or SharePoint",
       plain="Right-click the file in OneDrive or the web interface and choose Version history for a proper list of earlier versions.",
       body="""<p>Far more reliable than autorecover: real versions, kept much longer, restorable in
a click. Right-click the file in OneDrive, or open <em>File &rarr; Info &rarr; Version History</em> in
Excel.</p>
<p>This alone is a strong argument for keeping working files in OneDrive or SharePoint rather than on
a desktop.</p>"""),
  dict(h="Then fix the settings",
       plain="File > Options > Save. Reduce the autorecover interval and make sure the keep-last-version box is ticked.",
       body="""<p><em>File &rarr; Options &rarr; Save</em>:</p>
<ul>
<li>Set <strong>Save AutoRecover information every</strong> to 5 minutes or less. Ten is the default
and it is too long.</li>
<li>Tick <strong>Keep the last autorecovered version if I close without saving</strong>. Without it,
closing without saving leaves nothing at all.</li>
</ul>"""),
 ],
 body="""<h2>Where the folder actually is</h2>
<p>If the menu route fails, the folder can be opened directly. On Windows it is usually under
<code>%AppData%\\Microsoft\\Excel\\</code>; on a Mac, inside the Library folder under Application
Support. The exact path is shown in <em>File &rarr; Options &rarr; Save</em> as
<em>AutoRecover file location</em> &mdash; copy it from there rather than guessing.</p>
<h2>Autorecover is not a backup</h2>
<p>It is a crash net. It does not protect against a file being overwritten, deleted, corrupted, or
saved over with wrong data. For that you need real versioning &mdash; OneDrive, SharePoint, or a
backup that runs on its own.</p>
<h2>Before doing anything risky</h2>
<p>Press <strong>Ctrl+S</strong>, then <em>Save As</em> with a new name. Ten seconds, and it removes
the entire class of problem. Anyone about to run a large delete, a big paste, or a find-and-replace
across a workbook should do this by reflex.</p>
<h2>Google Sheets does not have this problem</h2>
<p>Sheets saves continuously and keeps a full version history under <em>File &rarr; Version
history</em>, going back months, with named versions if you want them. It is the single biggest
practical advantage it has over desktop Excel.</p>""",
 faq=[
  ("Can I recover an Excel file I closed without saving?",
   "Often yes. Go to File > Open and click Recover Unsaved Workbooks at the bottom of the recent files list. Do it before doing more work, because the copies are cleaned up on a timer."),
  ("How long does Excel keep unsaved files?",
   "Autorecover copies of a workbook that was never saved are kept for four days. For a saved file, the last autorecover version is kept only if the keep-on-close option is enabled."),
  ("Where is the autorecover folder?",
   "The exact path is shown in File > Options > Save as AutoRecover file location. Copy it from there rather than guessing, as it differs by version and platform."),
  ("What if the file is on OneDrive?",
   "Use version history — right-click the file in OneDrive, or File > Info > Version History. It is far more reliable than autorecover and goes back much further."),
  ("How do I make this less likely next time?",
   "In File > Options > Save, reduce the autorecover interval to five minutes and tick 'Keep the last autorecovered version if I close without saving'."),
  ("Is autorecover a backup?",
   "No. It is a crash net. It does not protect against a file being overwritten, deleted or saved over with wrong data — that needs real versioning or a separate backup."),
 ],
 related=[("excel-broken-external-links", "Links that will not break"),
          ("excel-formulas-not-updating", "My formulas stopped recalculating"),
          ("excel-conditional-format-ranges-changing", "Rules that fragment on their own")],
),

dict(
 slug="excel-broken-external-links",
 title="Remove Broken External Links in Excel That Will Not Break",
 description="Excel asks to update links to a file you deleted years ago, and Break Links does nothing. The four hiding places: names, validation, formatting and charts.",
 h1="Excel keeps asking about a file I deleted years ago",
 lead="Every time the workbook opens: &ldquo;This workbook contains links to one or more external sources.&rdquo; You have run <em>Break Links</em>. The prompt comes back anyway, because the link is not in a cell.",
 category=RC, group=G_RC,
 card_title="Links that will not break",
 card_blurb="Four places a link hides where Break Links cannot reach it.",
 chips=["Any version", "Four hiding places", "Excel"],
 keywords=["excel broken links", "excel phantom links", "excel break links not working",
           "excel external links remove", "excel link prompt on open", "excel find external links"],
 short_answer="""<p><strong><em>Break Links</em> only handles links in cell formulas. When the prompt
survives, the link is in one of four other places: a <strong>defined name</strong>, a <strong>data
validation</strong> rule, a <strong>conditional formatting</strong> rule, or a <strong>chart</strong>
series.</strong> Defined names are the usual culprit &mdash; open Name Manager, sort by
<em>Refers To</em>, and delete anything pointing at another file.</p>""",
 problem_h="Four places Break Links cannot see",
 problem="""<p>An external link is any reference to another workbook. <em>Data &rarr; Edit Links
&rarr; Break Links</em> converts those to values &mdash; but only where the reference is in a cell
formula. Four other places can hold one, and none of them are touched.</p>
<ul>
<li><strong>Defined names.</strong> The most common by a distance. A name copied in with a sheet from
another workbook still points at that workbook, invisibly, forever.</li>
<li><strong>Data validation.</strong> A dropdown whose source list lives in another file.</li>
<li><strong>Conditional formatting.</strong> A rule whose formula references another workbook.</li>
<li><strong>Charts.</strong> A series pointing at a range in another file.</li>
</ul>
<p>None of these show up in <em>Edit Links</em>'s list in a way that lets you clear them, which is why
the prompt appears to be unkillable.</p>""",
 symptoms=symptom_table([
   ["Prompt returns after Break Links",
    "The link is not in a cell formula",
    "Check names, validation, formatting, charts"],
   ["<em>Edit Links</em> lists a file you cannot find",
    "A reference survives in a name or a rule",
    "Name Manager first"],
   ["A name shows <code>#REF!</code>",
    "It pointed at a deleted file or range",
    "Delete the name"],
   ["Prompt only on one sheet",
    "A chart or a validation rule on that sheet",
    "Check both there"],
   ["Slow to open",
    "Excel is trying to reach the missing file",
    "Remove the link entirely"],
 ]),
 howto_name="How to find and remove a stubborn external link",
 howto_desc="Work through the four hiding places, most likely first.",
 steps=[
  dict(h="Try Break Links first",
       plain="Data > Edit Links > Break Links clears the ordinary case, and it is worth ruling out before hunting.",
       body="""<p><em>Data &rarr; Edit Links &rarr; Break Links</em>. It converts formulas referencing
other files into their current values. If the prompt is gone next time you open the file, you are
finished.</p>
<p>It cannot be undone, so save a copy first.</p>"""),
  dict(h="Check defined names — the usual culprit",
       plain="Formulas > Name Manager, widen the Refers To column, and delete any name pointing at another workbook or showing #REF!.",
       body="""<p><em>Formulas &rarr; Name Manager</em>. Widen <em>Refers To</em> and sort by it.
Anything containing <code>[</code> and a file name, or showing <code>#REF!</code>, is a broken link.</p>
<p>Select and delete them. Names copied in with a sheet from another workbook are the single most
common cause of a link that will not die.</p>"""),
  dict(h="Search the sheet for the bracket",
       plain="Press Ctrl+F, search for [ , and set Look in to Formulas with Within set to Workbook.",
       body="""<p>External references always contain a square bracket:</p>
<ul>
<li><strong>Ctrl+F</strong>, search for <code>[</code></li>
<li>Options &rarr; <em>Within: Workbook</em>, <em>Look in: Formulas</em></li>
<li>Find All</li>
</ul>
<p>This catches cell formulas anywhere in the file, including sheets you had forgotten about.</p>"""),
  dict(h="Check data validation and conditional formatting",
       plain="Use Go To Special to find every cell with validation, and Manage Rules with This Worksheet to review formatting rules on each sheet.",
       body="""<p><strong>Validation:</strong> <em>Home &rarr; Find &amp; Select &rarr; Go To Special
&rarr; Data validation &rarr; All</em>. Check the Source box of each for another file name.</p>
<p><strong>Formatting:</strong> <em>Conditional Formatting &rarr; Manage Rules</em>, set the dropdown
to <em>This Worksheet</em>, and read each rule's formula. Repeat per sheet &mdash; there is no
workbook-wide view.</p>"""),
  dict(h="Check every chart's series",
       plain="Click each series in a chart and read the SERIES formula in the formula bar for another file name.",
       body="""<p>Click a chart, click a series, and read the <code>SERIES</code> formula in the
formula bar. An external reference appears there in full. Repoint or delete it.</p>
<p>Charts are last because they are the rarest cause, and the most tedious to check.</p>"""),
 ],
 body="""<h2>If you still cannot find it</h2>
<p>An <code>.xlsx</code> is a zip archive. Copy the file, rename it to <code>.zip</code>, extract it,
and search the extracted files for the missing workbook's name. The folder that contains it tells you
where the link lives &mdash; <code>xl/charts/</code>, <code>xl/worksheets/</code>,
<code>xl/workbook.xml</code> for names &mdash; and you can then go back to Excel and look in the right
place.</p>
<p>It sounds drastic and it is often faster than hunting through twenty sheets.</p>
<h2>Suppressing the prompt is not fixing it</h2>
<p><em>Data &rarr; Edit Links &rarr; Startup Prompt</em> can hide the message. The link is still
there, still reaching for a missing file, and still slowing the workbook down on open. Worse, the next
person has no idea it exists. Remove the link rather than the message.</p>
<h2>Avoiding it</h2>
<ul>
<li>Copying a sheet from another workbook brings its defined names. Check Name Manager afterwards,
every time.</li>
<li>Prefer Power Query to formula links across files &mdash; it is visible, listed, and manageable in
one place.</li>
<li>Where a link is genuinely wanted, keep both files in the same folder and use relative paths, so
moving the pair does not break it.</li>
</ul>""",
 faq=[
  ("Why does Break Links not remove my external link?",
   "It only handles links in cell formulas. The link is likely in a defined name, a data validation rule, a conditional formatting rule or a chart series."),
  ("Where do external links usually hide?",
   "Defined names, by a wide margin. A name copied in with a sheet from another workbook keeps pointing at that workbook invisibly."),
  ("How do I search for external links?",
   "Press Ctrl+F and search for a square bracket, with Within set to Workbook and Look in set to Formulas. External references always contain one."),
  ("Can I just turn off the prompt?",
   "You can, under Edit Links > Startup Prompt, but the link remains — still reaching for a missing file, still slowing the open, and now invisible to the next person."),
  ("What if I cannot find it anywhere?",
   "Rename a copy of the file to .zip, extract it, and search the extracted files for the missing workbook's name. The folder it appears in tells you where the link lives."),
  ("How do I stop this happening?",
   "Check Name Manager after copying any sheet in from another workbook, and prefer Power Query over cross-file formula links, since it is visible and managed in one place."),
 ],
 related=[("excel-recover-unsaved-file", "Recovering unsaved work"),
          ("excel-conditional-format-ranges-changing", "Rules that fragment on their own"),
          ("excel-power-query-refresh-load-settings", "What Enable Load and Refresh actually do")],
),
]
