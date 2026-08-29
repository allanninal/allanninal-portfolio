#!/usr/bin/env python3
"""Group B — formulas and references that behave differently from how they read.

Same sourcing rule as group A: every topic here is one people demonstrably get stuck on,
ranked by real question volume rather than by what makes a tidy curriculum. The single
most-viewed question in the set is "how do I keep one reference fixed while the other
moves" at 919k views — the dollar sign, which almost no beginner course explains as the
conceptual wall it actually is.

Where a modern function (UNIQUE, XLOOKUP, FILTER, TEXTSPLIT) solves the problem outright,
it is given first and the older formula second, because a reader on Excel 2019 or
LibreOffice still needs the older one and most ranking content pretends they do not exist.
"""
from build_guide import fx, symptom_table

GROUP = "Formulas that do not behave as they read"
CAT = "Formulas"

GUIDES_B = [

dict(
 slug="excel-absolute-relative-references",
 title="The $ in Excel: Absolute and Relative References Explained",
 description="A formula that breaks when you drag it down is a relative reference problem. What $ actually locks, when to use each of the four forms, and the F4 shortcut.",
 h1="My formula breaks the moment I drag it down",
 lead="It works perfectly in the first cell. Drag it down and every row below is wrong, or full of errors. Nothing is broken &mdash; the references moved with the formula, which is what they are designed to do.",
 category=CAT, group=GROUP,
 card_title="The $ sign, and why dragging breaks formulas",
 card_blurb="What $ actually locks, the four forms, and when each one is correct.",
 chips=["F4 shortcut", "Four forms", "Excel + Google Sheets"],
 keywords=["excel absolute reference", "excel dollar sign formula", "excel relative reference",
           "excel f4 key", "excel lock cell reference", "excel formula changes when dragged"],
 short_answer="""<p><strong>Excel references are <em>relative</em> by default: they describe a
direction and distance, not a fixed address, so they shift when the formula is copied.</strong> A
<code>$</code> pins the part that follows it. <code>$B$2</code> never moves; <code>B$2</code> keeps
the row but lets the column move; <code>$B2</code> keeps the column but lets the row move. Press
<strong>F4</strong> on a reference in the formula bar to cycle through all four forms.</p>""",
 problem_h="A reference is a direction, not an address",
 problem="""<p>This is the idea that makes everything else obvious, and it is almost never taught.</p>
<p>When you write <code>=A2*B2</code> in cell <code>C2</code>, Excel does not record
&ldquo;multiply A2 by B2&rdquo;. It records <em>&ldquo;multiply the cell two to my left by the cell
one to my left&rdquo;</em>. Copy that formula to <code>C3</code> and it faithfully does the same
thing one row down &mdash; which is exactly what you want.</p>
<p>The trouble starts when one of the values should <strong>not</strong> move. A single tax rate in
<code>F1</code>, a conversion factor, a total to calculate percentages against. Dragging a formula
that refers to <code>F1</code> makes row 2 look at <code>F2</code>, row 3 at <code>F3</code>, and so
on into empty cells &mdash; which is why you get zeros, or <code>#DIV/0!</code>.</p>""",
 symptoms=symptom_table([
   ["First row right, everything below wrong",
    "A reference that should be fixed moved with the formula",
    "Add <code>$</code> to the reference that should not move"],
   ["<code>#DIV/0!</code> down the column",
    "The moving reference now points at an empty cell",
    "Pin it: <code>$F$1</code>"],
   ["Zeros instead of percentages",
    "The total reference drifted off the total",
    "Pin the total"],
   ["Right dragging down, wrong dragging across",
    "The column moved when only the row should have",
    "Use a mixed reference &mdash; <code>$B2</code> or <code>B$2</code>"],
   ["Breaks after inserting a row",
    "Insertion shifted the target; the formula followed it",
    "This is correct behaviour &mdash; use a named range if it should not follow"],
 ]),
 howto_name="How to lock a cell reference in Excel",
 howto_desc="Decide what must stay still, add the dollar signs that pin it, and use F4 rather than typing them.",
 steps=[
  dict(h="Ask which part must not move",
       plain="Before adding any dollar signs, decide whether the fixed value stays in the same column, the same row, or the same single cell as the formula is copied.",
       body="""<p>Do this before touching the keyboard. Copying <em>down</em> a column changes row
numbers, so pin the row. Copying <em>across</em> changes column letters, so pin the column. Copying
in both directions means pinning both.</p>"""),
  dict(h="Use F4 instead of typing dollar signs",
       plain="Click the reference in the formula bar and press F4. Each press cycles through B2, $B$2, B$2 and $B2.",
       body="""<p>Click on the reference in the formula bar and press <strong>F4</strong>. Each press
cycles: <code>B2</code> &rarr; <code>$B$2</code> &rarr; <code>B$2</code> &rarr; <code>$B2</code> and
back. On a Mac it is <strong>&#8984;+T</strong>. Faster than typing and it never puts a dollar in the
wrong place.</p>"""),
  dict(h="Pin a single constant with a fully absolute reference",
       plain="Use $F$1 for a value like a tax rate that every row of the formula must refer to.",
       body="""<p>One rate, referenced by every row:</p>""" +
       fx("Fully absolute", '=B2*$F$1',
          """<p><code>B2</code> moves with each row; <code>$F$1</code> stays put. This is the form
you need nine times out of ten.</p>""")),
  dict(h="Use a mixed reference for a grid",
       plain="In a table that is copied both down and across, pin the column of the row labels and the row of the column headers, so each stays on its own axis.",
       body="""<p>A multiplication table or a rate grid is copied in both directions, and each input
should move on only one axis:</p>""" +
       fx("Mixed references in a grid", '=$A2*B$1',
          """<p><code>$A2</code> always reads column A but follows the row.
<code>B$1</code> always reads row 1 but follows the column. Written once in the top-left cell, this
fills an entire grid correctly.</p>""")),
 ],
 body="""<h2>The four forms, in one table</h2>
<p>Read the <code>$</code> as &ldquo;lock what comes next&rdquo;.</p>
<ul>
<li><code>B2</code> &mdash; nothing locked. Both move.</li>
<li><code>$B$2</code> &mdash; both locked. Never moves.</li>
<li><code>B$2</code> &mdash; row locked. Moves across, not down.</li>
<li><code>$B2</code> &mdash; column locked. Moves down, not across.</li>
</ul>
<h2>Named ranges are usually better than $</h2>
<p>If you find yourself typing <code>$F$1</code> in twenty formulas, name the cell instead. Select
it, type a name such as <code>TaxRate</code> into the Name Box, and then write:</p>
""" + fx("A named range", '=B2*TaxRate',
"""<p>A name is absolute by nature, so it never drifts. It also survives inserted rows, and anyone
reading the formula in six months can see what the number means &mdash; which
<code>$F$1</code> never tells them.</p>""") + """
<h2>Structured references in tables</h2>
<p>Format your range as a table (<em>Ctrl+T</em>) and columns get names of their own:
<code>=[@Quantity]*[@Price]</code>. These behave sensibly when copied and do not need dollar signs
at all. For anything that grows over time, a table is a better answer than careful pinning.</p>
<h2>Google Sheets is identical</h2>
<p>Same syntax, same four forms. The cycling shortcut is <strong>F4</strong> there too.</p>""",
 faq=[
  ("What does the dollar sign do in an Excel formula?",
   "It locks the part of the reference immediately after it, so that part does not change when the formula is copied. $B$2 is fully locked; B$2 locks only the row; $B2 locks only the column."),
  ("Why does my formula change when I drag it?",
   "Because references are relative by default — they record a direction and distance rather than a fixed address, so they shift with the formula. That is usually what you want, except for values that must stay fixed."),
  ("What is the keyboard shortcut for absolute references?",
   "F4 with the cursor on a reference in the formula bar cycles through all four forms. On a Mac it is Command+T."),
  ("When should I use a mixed reference?",
   "When a formula is copied in both directions and each input should move on only one axis — typically a grid with row labels down the side and column headers across the top."),
  ("Are named ranges better than dollar signs?",
   "Usually, for a constant you refer to repeatedly. A name is absolute by nature, survives inserted rows, and tells the next reader what the value means."),
  ("Does this work the same in Google Sheets?",
   "Yes — identical syntax, identical behaviour, and F4 cycles the forms there too."),
 ],
 related=[("excel-apply-formula-entire-column", "Applying a formula to a whole column"),
          ("excel-formulas-not-updating", "My formulas stopped recalculating"),
          ("excel-sumifs-vs-pivot-table", "SUMIFS or a pivot table?")],
),

dict(
 slug="excel-formulas-not-updating",
 title="Excel Formulas Not Updating? Check Calculation Mode First",
 description="If formulas show stale results until you save, calculation is set to Manual. How to fix it, why it switched, and the other four causes worth checking.",
 h1="My formulas have stopped recalculating",
 lead="You change an input and nothing downstream moves. Press save and suddenly everything updates. The formulas are correct &mdash; Excel has simply stopped recalculating automatically, and one workbook can switch the setting for the whole session.",
 category=CAT, group=GROUP,
 card_title="Formulas showing stale results",
 card_blurb="Calculation set to Manual is the usual cause. Five checks, in order.",
 chips=["Two-minute fix", "F9", "Excel + Google Sheets"],
 keywords=["excel formulas not updating", "excel calculation manual", "excel not calculating",
           "excel f9 recalculate", "excel formula shows old value", "excel automatic calculation"],
 short_answer="""<p><strong>In nine cases out of ten, calculation has been set to Manual.</strong>
Go to <em>Formulas &rarr; Calculation Options &rarr; Automatic</em>, or press <strong>F9</strong> to
force a single recalculation. The setting is saved <em>inside the workbook</em>, and the first
workbook opened in a session sets the mode for every workbook opened after it &mdash; which is why
this seems to happen at random.</p>""",
 problem_h="Why one workbook can break all the others",
 problem="""<p>Calculation mode is stored in the workbook file, not in your Excel preferences. When
Excel starts, the <strong>first workbook you open</strong> imposes its setting on the whole
application, and every workbook opened afterwards in that session inherits it.</p>
<p>So someone sends you a large model that was saved in Manual mode &mdash; a reasonable thing to do
with a slow workbook &mdash; you open it, and then open your own perfectly normal sheet. Yours is now
in Manual mode too, and nothing you did caused it.</p>
<p>That is also why saving appears to fix it: saving triggers a recalculation, so the numbers update
once and then go stale again.</p>""",
 symptoms=symptom_table([
   ["Values update only when you save",
    "Calculation is Manual; saving forces one pass",
    "Set Calculation Options to Automatic"],
   ["<code>Calculate</code> in the status bar",
    "Excel is telling you results are pending",
    "Press F9, then switch to Automatic"],
   ["The formula shows as text in the cell",
    "The cell is formatted as Text, or Show Formulas is on",
    "Format as General and re-enter, or press Ctrl+`"],
   ["Only some cells are stale",
    "Those cells were entered while the format was Text",
    "Reformat and re-enter them"],
   ["Recalculates but the number is unchanged",
    "A circular reference, or an input that did not really change",
    "Check the status bar for a circular reference warning"],
 ]),
 howto_name="How to fix formulas that will not update",
 howto_desc="Five checks in order of likelihood, starting with calculation mode.",
 steps=[
  dict(h="Set calculation back to Automatic",
       plain="Go to Formulas > Calculation Options and choose Automatic. Press F9 to force an immediate recalculation of the whole workbook.",
       body="""<p><em>Formulas &rarr; Calculation Options &rarr; Automatic</em>. To force a single
pass now, press <strong>F9</strong>. <strong>Shift+F9</strong> does the active sheet only, and
<strong>Ctrl+Alt+F9</strong> forces a full rebuild of every formula, which is the one to use when
you suspect Excel's dependency tree has gone stale.</p>
<p>Then re-save the workbook, so the Automatic setting is what it carries next time.</p>"""),
  dict(h="Check whether the cell is formatted as Text",
       plain="If the cell shows the formula itself rather than a result, it is probably formatted as Text. Set the format to General, then re-enter the formula.",
       body="""<p>A cell formatted as Text stores your formula as a string. Changing the format alone
does not fix it &mdash; the cell has to be re-entered. Set the format to <em>General</em>, click into
the cell and press Enter. For a column of them, use <em>Data &rarr; Text to Columns &rarr;
Finish</em>.</p>"""),
  dict(h="Check Show Formulas",
       plain="Press Ctrl+` to toggle Show Formulas. If every formula on the sheet is visible as text, this view is simply switched on.",
       body="""<p>If <em>every</em> formula on the sheet displays as text and the columns have gone
wide, someone has pressed <strong>Ctrl+`</strong> (the backtick, next to the 1 key). Press it again.
Nothing is wrong with the workbook.</p>"""),
  dict(h="Look for a circular reference",
       plain="Check the status bar for a circular reference warning, and use Formulas > Error Checking > Circular References to find it.",
       body="""<p>A circular reference stops Excel from resolving part of the sheet. The status bar
names the offending cell, and <em>Formulas &rarr; Error Checking &rarr; Circular References</em>
lists them. Until it is broken, results near it stay stale.</p>"""),
  dict(h="Force a full rebuild",
       plain="Press Ctrl+Alt+F9 to rebuild every formula in every open workbook, ignoring the cached dependency tree.",
       body="""<p>Excel keeps a dependency tree so it only recalculates what changed. That tree can
go wrong, especially in a workbook edited by several versions of Excel.
<strong>Ctrl+Alt+F9</strong> ignores it and rebuilds everything.</p>"""),
 ],
 body="""<h2>When Manual mode is the right choice</h2>
<p>Manual is not a mistake in every case. A workbook with hundreds of thousands of volatile formulas
can take minutes to recalculate, and Manual makes it usable &mdash; you edit freely and press F9 when
you want the numbers.</p>
<p>If you do that, say so in the workbook. A note on the first tab saying &ldquo;this file is set to
Manual calculation; press F9 to update&rdquo; takes a moment and saves the next person an hour of
believing wrong numbers.</p>
<h2>Which functions force constant recalculation</h2>
<p>These are <em>volatile</em>: they recalculate on every change anywhere in the workbook, whether or
not anything they depend on moved.</p>
<ul>
<li><code>NOW</code>, <code>TODAY</code></li>
<li><code>RAND</code>, <code>RANDBETWEEN</code></li>
<li><code>OFFSET</code>, <code>INDIRECT</code></li>
<li><code>CELL</code>, <code>INFO</code></li>
</ul>
<p>A few are harmless. Thousands of <code>OFFSET</code> calls are the usual reason a workbook became
slow enough that someone reached for Manual mode in the first place. Replacing <code>OFFSET</code>
with <code>INDEX</code>, which is not volatile, is often the real fix.</p>
<h2>Google Sheets</h2>
<p>Sheets always recalculates automatically and has no Manual mode. Its equivalent complaint is a
volatile-function recalculation setting under <em>File &rarr; Settings &rarr; Calculation</em>.</p>""",
 faq=[
  ("Why do my formulas only update when I save?",
   "Calculation is set to Manual. Saving triggers one recalculation pass, so the numbers refresh once and then go stale again. Set Calculation Options to Automatic."),
  ("Why did calculation mode change on its own?",
   "It is stored in the workbook, and the first workbook opened in an Excel session sets the mode for every workbook opened afterwards. Opening someone else's Manual-mode file switches yours too."),
  ("What does F9 do?",
   "F9 recalculates all open workbooks once. Shift+F9 does the active sheet only, and Ctrl+Alt+F9 forces a full rebuild ignoring the cached dependency tree."),
  ("My cell shows the formula instead of the answer. Why?",
   "Either the cell is formatted as Text, in which case set it to General and re-enter the formula, or Show Formulas is switched on for the whole sheet — press Ctrl+` to toggle it."),
  ("Is Manual calculation ever a good idea?",
   "Yes, for very large workbooks where every edit would otherwise trigger a long recalculation. If you use it, leave a visible note in the workbook so the next person knows to press F9."),
  ("Which functions make a workbook slow?",
   "Volatile ones — NOW, TODAY, RAND, OFFSET, INDIRECT, CELL and INFO — because they recalculate on every change anywhere. Replacing OFFSET with INDEX usually helps most."),
 ],
 related=[("excel-absolute-relative-references", "The $ sign and why dragging breaks formulas"),
          ("excel-return-blank-not-zero", "Returning a real blank instead of zero"),
          ("excel-apply-formula-entire-column", "Applying a formula to a whole column")],
),

dict(
 slug="excel-unique-values-list",
 title="Get a List of Unique Values in Excel (With and Without UNIQUE)",
 description="UNIQUE does it in one formula on Microsoft 365. On older Excel, use Remove Duplicates, Advanced Filter or a pivot table. All four methods compared.",
 h1="I need a list of the distinct values in this column",
 lead="Every method you find online assumes a different version of Excel, and half of them modify your data in place. Here is which one to use, and what each does to the original column.",
 category=CAT, group=GROUP,
 card_title="Getting unique values from a column",
 card_blurb="UNIQUE if you have it, and three methods that work on any version.",
 chips=["UNIQUE", "Works on old Excel", "Excel + Google Sheets"],
 keywords=["excel unique values", "excel distinct values column", "excel remove duplicates",
           "excel unique function", "excel advanced filter unique", "excel list distinct"],
 short_answer="""<p><strong>On Microsoft 365 or Excel 2021, use <code>=UNIQUE(A2:A500)</code>
&mdash; one formula, spills automatically, updates when the source changes.</strong> On any older
version, use <em>Data &rarr; Remove Duplicates</em> on a copy of the column, or <em>Advanced
Filter</em> with &ldquo;Unique records only&rdquo; to write the distinct list somewhere else without
touching the original. A pivot table also lists distinct values as row labels.</p>""",
 problem_h="Pick by two questions: which Excel, and may the original change?",
 problem="""<p>Everything else follows from those two answers.</p>
<p><strong>Remove Duplicates deletes rows in place.</strong> It is the top search result and the most
destructive option &mdash; it modifies your data and cannot be undone once the file is saved and
closed. Always run it on a copy.</p>
<p><strong>Advanced Filter</strong> can write the unique list to a different location, leaving the
source intact. It is the right non-destructive answer for older Excel and almost nobody knows it
exists.</p>
<p><strong><code>UNIQUE</code></strong> is a formula, so it never touches the source and updates on
its own. It needs Microsoft 365 or Excel 2021 &mdash; and it does not exist in LibreOffice, which
matters if you share the file.</p>""",
 symptoms=symptom_table([
   ["<code>#NAME?</code> from <code>UNIQUE</code>",
    "Your Excel version does not have the function",
    "Use Advanced Filter or Remove Duplicates"],
   ["<code>#SPILL!</code> from <code>UNIQUE</code>",
    "Something is blocking the range it needs to fill",
    "Clear the cells below and to the right"],
   ["Blanks appear in the unique list",
    "The source range includes empty cells",
    "Filter them out, or narrow the range"],
   ["Values that look identical listed twice",
    "They differ by a trailing or non-breaking space",
    "Clean the column first"],
   ["Remove Duplicates deleted data",
    "It works in place and deletes whole rows",
    "Undo now; work on a copy"],
 ]),
 howto_name="How to get a unique list of values",
 howto_desc="Four methods; choose by your Excel version and whether the source may be modified.",
 steps=[
  dict(h="Microsoft 365 or Excel 2021: use UNIQUE",
       plain="Type =UNIQUE(A2:A500) in an empty cell. The result spills down automatically and updates whenever the source changes.",
       body="""<p>One formula, and it stays live:</p>""" +
       fx("The modern answer", '=UNIQUE(A2:A500)',
          """<p>The result spills down as far as it needs to. Wrap it in <code>SORT</code> to order
the list: <code>=SORT(UNIQUE(A2:A500))</code>. Nothing is written to the source column.</p>""")),
  dict(h="Any version, non-destructive: Advanced Filter",
       plain="Select the column, choose Data > Advanced, select 'Copy to another location', tick 'Unique records only', and give it a destination cell.",
       body="""<p>Select the column, then <em>Data &rarr; Advanced</em>. Choose <strong>Copy to
another location</strong>, tick <strong>Unique records only</strong>, and set a destination. The
distinct values are written there and the source is untouched.</p>
<p>This is the method to use on Excel 2019 and earlier. It is a one-off snapshot, so re-run it when
the data changes.</p>"""),
  dict(h="Any version, destructive: Remove Duplicates",
       plain="Copy the column to a new sheet first, then use Data > Remove Duplicates. It deletes rows in place, so never run it on your only copy.",
       body="""<p><strong>Copy the column to a new sheet first.</strong> Then <em>Data &rarr; Remove
Duplicates</em>. It is fast and simple, and it permanently deletes rows from wherever you run it.
Excel reports how many were removed &mdash; read that number and check it is what you expected.</p>"""),
  dict(h="Count the distinct values without listing them",
       plain="Use SUMPRODUCT with COUNTIF to count distinct values in any Excel version, without producing a list.",
       body="""<p>When you only need the number:</p>""" +
       fx("Count distinct, any version",
          '=SUMPRODUCT((A2:A500<>"")/COUNTIF(A2:A500,A2:A500&""))',
          """<p>Each value contributes 1 divided by how many times it appears, so every distinct
value sums to exactly 1. The <code>&amp;""</code> and the <code>&lt;&gt;""</code> test are what stop
empty cells causing a <code>#DIV/0!</code>. On 365, <code>=COUNTA(UNIQUE(A2:A500))</code> is
clearer.</p>""")),
 ],
 body="""<h2>Clean before you dedupe</h2>
<p>Every one of these methods compares values exactly as stored. <code>Acme Ltd</code> and
<code>Acme Ltd&nbsp;</code> with a trailing space are two different values to all of them, so your
&ldquo;unique&rdquo; list quietly contains the same company twice.</p>
<p>Clean the column first &mdash; that is the whole reason the free workbook below exists. Dedupe
afterwards.</p>
<h2>Case sensitivity</h2>
<p>None of these methods is case-sensitive. <code>ACME</code>, <code>Acme</code> and
<code>acme</code> collapse into one entry, and which spelling survives depends on the method. If case
matters, add a helper column with <code>EXACT</code> comparisons before deduplicating.</p>
<h2>Unique across two columns</h2>
<p>To find distinct combinations rather than distinct single values, <code>UNIQUE</code> accepts a
multi-column range directly: <code>=UNIQUE(A2:B500)</code> returns the distinct <em>pairs</em>. On
older Excel, concatenate the columns into a helper first and deduplicate that.</p>
<h2>Google Sheets</h2>
<p>Sheets has <code>UNIQUE</code> and has had it far longer than Excel, so it is always available
there. It also has <code>COUNTUNIQUE</code>, which has no Excel equivalent.</p>""",
 faq=[
  ("How do I get unique values in Excel?",
   "On Microsoft 365 or Excel 2021 use =UNIQUE(A2:A500). On older versions use Advanced Filter with 'Unique records only', which writes the list elsewhere without changing your data."),
  ("Why does UNIQUE give me a #NAME? error?",
   "The function does not exist in your version of Excel. It requires Microsoft 365 or Excel 2021, and it is not available in LibreOffice."),
  ("Does Remove Duplicates change my data?",
   "Yes. It deletes rows in place and cannot be undone once the file has been saved and closed. Always run it on a copy of the column."),
  ("Why are values that look identical listed twice?",
   "They differ by a character you cannot see, usually a trailing or non-breaking space. Every deduplication method compares values exactly as stored, so clean the column first."),
  ("Is UNIQUE case-sensitive?",
   "No. ACME, Acme and acme are treated as the same value by all of these methods. If case matters, compare with EXACT in a helper column first."),
  ("How do I count distinct values without listing them?",
   "Use =SUMPRODUCT((A2:A500<>\"\")/COUNTIF(A2:A500,A2:A500&\"\")) on any version, or =COUNTA(UNIQUE(A2:A500)) on Microsoft 365."),
 ],
 related=[("excel-compare-two-lists", "Find what is in list A but not list B"),
          ("excel-vlookup-non-breaking-space", "#N/A when the value is clearly there"),
          ("excel-count-functions-explained", "COUNT, COUNTA, COUNTIF and COUNTBLANK")],
),

dict(
 slug="excel-compare-two-lists",
 title="Find What Is in One Excel List but Not the Other",
 description="Compare two columns and list what is missing from each. COUNTIF works on every version; XLOOKUP and FILTER are cleaner on Microsoft 365.",
 h1="Which of these names are missing from the other list?",
 lead="Two lists that should agree and do not: a stock count against the system, a bank statement against the ledger, this month's members against last month's. The comparison itself is one formula &mdash; the trap is what counts as a match.",
 category=CAT, group=GROUP,
 card_title="What is in list A but not list B",
 card_blurb="COUNTIF on any version, FILTER on 365, and why matches fail.",
 chips=["COUNTIF", "Any version", "Excel + Google Sheets"],
 keywords=["excel compare two lists", "excel find missing values", "excel countif compare columns",
           "excel two column comparison", "excel not in list", "excel reconcile two lists"],
 short_answer="""<p><strong><code>=COUNTIF(ListB,A2)=0</code> is TRUE when the value in
<code>A2</code> does not appear in list B.</strong> It works in every version of Excel, in Google
Sheets and in LibreOffice. On Microsoft 365,
<code>=FILTER(A2:A500,COUNTIF(B2:B500,A2:A500)=0)</code> returns the missing items as a list in one
step. Run it in both directions &mdash; A-not-in-B and B-not-in-A are different questions with
different answers.</p>""",
 problem_h="Both directions, and the reason matches fail",
 problem="""<p>Two mistakes account for nearly every wrong answer here.</p>
<p><strong>Only checking one direction.</strong> &ldquo;What is in A but not B&rdquo; does not tell
you what is in B but not A. A stock count that finds no missing items may still contain items that
should not exist at all. Always run both.</p>
<p><strong>Comparing dirty values.</strong> <code>COUNTIF</code> matches exactly as stored, so a
trailing space, a non-breaking space, or one side stored as text and the other as a number all
produce a confident MISSING for a row that is sitting right there. In a reconciliation, that is worse
than no answer &mdash; it sends someone hunting for a discrepancy that does not exist.</p>""",
 symptoms=symptom_table([
   ["Everything reports as missing",
    "One list is text, the other numbers",
    "Make both the same type"],
   ["A handful wrongly missing",
    "Invisible characters on one side",
    "Clean both columns first"],
   ["<code>#NAME?</code> from <code>FILTER</code>",
    "Not available in your Excel version",
    "Use the <code>COUNTIF</code> method"],
   ["Counts do not agree with the list",
    "Duplicates counted more than once",
    "Deduplicate before comparing"],
   ["Matches ignore capitalisation",
    "<code>COUNTIF</code> is not case-sensitive",
    "Use <code>SUMPRODUCT</code> with <code>EXACT</code>"],
 ]),
 howto_name="How to compare two lists in Excel",
 howto_desc="Flag the missing items in both directions, then list them.",
 steps=[
  dict(h="Flag what is missing, in both directions",
       plain="Put a COUNTIF formula beside each list that reports whether the value appears in the other list. Do it for both lists, not just one.",
       body="""<p>Beside list A:</p>""" +
       fx("Is this A value in B?", '=IF(COUNTIF($B$2:$B$500,A2)=0,"MISSING FROM B","ok")',
          """<p>And the mirror image beside list B, pointing at column A. Two columns, two questions,
two different answers.</p>""")),
  dict(h="On Microsoft 365, get the list directly",
       plain="Use FILTER with COUNTIF to return only the values that do not appear in the other list, with no helper column.",
       body="""<p>No helper column, and it stays live:</p>""" +
       fx("The missing items, as a list",
          '=FILTER(A2:A500,COUNTIF(B2:B500,A2:A500)=0,"none missing")',
          """<p>The third argument is what to show when nothing is missing &mdash; without it you get
<code>#CALC!</code>, which looks like a failure rather than a clean result.</p>""")),
  dict(h="Clean both sides before you trust the answer",
       plain="Apply the same trimming and cleaning to both lists before comparing, because COUNTIF matches values exactly as stored.",
       body="""<p>Add a cleaned helper column beside each list and compare <em>those</em>:</p>""" +
       fx("Compare cleaned values",
          '=IF(COUNTIF($D$2:$D$500,TRIM(A2))=0,"MISSING","ok")',
          """<p>Where column D holds the cleaned version of list B. If the two lists came from
different systems, assume they need cleaning &mdash; they almost always do.</p>""")),
  dict(h="Check the types match",
       plain="If one list holds numbers and the other holds text versions of the same numbers, every comparison fails. Test with ISTEXT on both sides.",
       body="""<p>An order number stored as text in one export and as a number in the other will never
match, however clean both are. Test with <code>=ISTEXT(A2)</code> on each side. Convert one, or
compare <code>TEXT(A2,"@")</code> against <code>TEXT(B2,"@")</code> so both are strings.</p>"""),
 ],
 body="""<h2>Highlighting the differences visually</h2>
<p>For a quick visual answer, conditional formatting takes the same formula. Select list A,
<em>Home &rarr; Conditional Formatting &rarr; New Rule &rarr; Use a formula</em>, and enter:</p>
""" + fx("Conditional formatting rule", '=COUNTIF($B$2:$B$500,A2)=0',
"""<p>Pick a fill colour and every unmatched value in A is highlighted. Note the mixed reference
&mdash; <code>$B$2:$B$500</code> pinned, <code>A2</code> relative &mdash; which is what lets the rule
walk down the column.</p>""") + """
<h2>Case-sensitive comparison</h2>
<p><code>COUNTIF</code> ignores capitalisation. Where <code>ABC123</code> and <code>abc123</code> are
genuinely different codes, use:</p>
""" + fx("Case-sensitive match", '=SUMPRODUCT(--EXACT($B$2:$B$500,A2))=0',
"""<p><code>EXACT</code> compares case as well as characters, and <code>SUMPRODUCT</code> counts how
many exact matches exist.</p>""") + """
<h2>Matching on more than one column</h2>
<p>When identity depends on two fields &mdash; a date <em>and</em> an amount, a first name
<em>and</em> a surname &mdash; use <code>COUNTIFS</code> with a criterion per column rather than
concatenating the fields into a key. Concatenation creates false matches whenever one value ends
where the next begins.</p>
<h2>When the lists are large</h2>
<p><code>COUNTIF</code> across two columns of 100,000 rows is slow, because it is comparing every
value against every value. Sort both lists first, or use <code>MATCH</code>, which stops at the first
hit and is noticeably faster on large ranges.</p>""",
 faq=[
  ("How do I find values in one column that are not in another?",
   "Use =COUNTIF(OtherList,A2)=0. TRUE means the value does not appear in the other list. On Microsoft 365, FILTER with the same COUNTIF test returns the missing items as a list."),
  ("Do I need to compare in both directions?",
   "Yes. What is in A but not B is a different question from what is in B but not A, and a reconciliation needs both answers."),
  ("Why does everything report as missing?",
   "Usually a type mismatch — one list holds numbers and the other holds text versions of the same values. They never match, however clean both are."),
  ("Why do a few rows wrongly report as missing?",
   "Invisible characters, typically a trailing or non-breaking space on one side. COUNTIF compares values exactly as stored, so clean both columns first."),
  ("Is COUNTIF case-sensitive?",
   "No. For a case-sensitive comparison use =SUMPRODUCT(--EXACT(Range,A2))=0, which compares capitalisation as well as characters."),
  ("How do I match on two columns at once?",
   "Use COUNTIFS with one criterion per column. Concatenating the columns into a single key creates false matches where one value ends and the next begins."),
 ],
 related=[("excel-unique-values-list", "Getting a list of unique values"),
          ("excel-join-two-sheets-lookup", "Joining two sheets the way SQL would"),
          ("excel-vlookup-non-breaking-space", "#N/A when the value is clearly there")],
),

dict(
 slug="excel-sumifs-vs-pivot-table",
 title="Group and Sum in Excel: SUMIFS or a Pivot Table?",
 description="Both answer 'total by category'. SUMIFS when you need a live figure in a report layout; a pivot table when you are exploring. How to choose, with both methods.",
 h1="I need a total for each category",
 lead="Sales by region, hours by project, spend by supplier. Excel has two good answers and they suit genuinely different jobs &mdash; one is a formula that lives in your layout, the other is a tool for looking around.",
 category=CAT, group=GROUP,
 card_title="Group by and sum",
 card_blurb="SUMIFS for a live figure in a fixed report; a pivot table for exploring.",
 chips=["SUMIFS", "Pivot tables", "Excel + Google Sheets"],
 keywords=["excel group by sum", "excel sumifs", "excel sum by category", "excel pivot table sum",
           "excel sumif multiple criteria", "excel total by group"],
 short_answer="""<p><strong>Use <code>SUMIFS</code> when the answer belongs in a report you control
and must update automatically; use a pivot table when you are exploring and do not yet know which
breakdown you want.</strong> <code>=SUMIFS(Amount,Region,"North")</code> totals one category and
recalculates on its own. A pivot table produces every category at once but must be refreshed by
hand.</p>""",
 problem_h="The real difference is who controls the layout",
 problem="""<p>Both give the same numbers. They differ in what happens next.</p>
<p><strong>A pivot table owns its own block of the sheet.</strong> You cannot put a column of your own
in the middle of it, and its shape changes as the data changes. That is exactly what you want when
exploring &mdash; drag a field, see a different cut &mdash; and exactly what you do not want inside a
monthly report with a fixed layout.</p>
<p><strong><code>SUMIFS</code> lives wherever you put it.</strong> The row labels are yours, the
formatting is yours, and the figure updates the moment the data changes. That is what a report needs,
and it is why finance models are full of <code>SUMIFS</code> and short of pivot tables.</p>
<p>The pivot table's real weakness is the refresh. It shows a cached result until someone right-clicks
and chooses Refresh, so a printed report can be silently out of date. <code>SUMIFS</code> cannot be
stale (unless calculation is set to Manual).</p>""",
 symptoms=symptom_table([
   ["<code>SUMIFS</code> returns 0",
    "The criterion does not match exactly, or the values are text",
    "Check for spaces and check the type"],
   ["Pivot total does not match the data",
    "The pivot is showing a cached result",
    "Right-click &rarr; Refresh"],
   ["New rows missing from the pivot",
    "They fell outside the source range",
    "Base the pivot on a table (Ctrl+T)"],
   ["<code>#VALUE!</code> from <code>SUMIFS</code>",
    "The sum range and criteria ranges are different sizes",
    "Make every range the same height"],
   ["Categories split that should be together",
    "Trailing spaces or inconsistent capitalisation",
    "Clean the category column"],
 ]),
 howto_name="How to total by category in Excel",
 howto_desc="SUMIFS for a fixed report, a pivot table for exploration.",
 steps=[
  dict(h="Build the category list first",
       plain="Get a unique list of the categories, either with UNIQUE or with Advanced Filter, and put it down the side of your report.",
       body="""<p>You need somewhere for the totals to sit. On 365,
<code>=SORT(UNIQUE(Data!C2:C5000))</code> gives you the row labels and keeps them current; on older
Excel use Advanced Filter.</p>"""),
  dict(h="Total each one with SUMIFS",
       plain="Use SUMIFS with the sum range first, then each criteria range and its criterion. Point the criterion at the label cell so the formula fills down.",
       body="""<p>Point the criterion at your label cell rather than typing the category into the
formula:</p>""" +
       fx("Total by one category", '=SUMIFS(Data!$D$2:$D$5000,Data!$C$2:$C$5000,$A2)',
          """<p>Sum range first, then pairs of range and criterion. <code>$A2</code> is a mixed
reference so it follows the row but not the column &mdash; that is what lets one formula fill the
whole report.</p>""")),
  dict(h="Add more conditions as more pairs",
       plain="SUMIFS accepts up to 127 criteria pairs. Add a date range with >= and <= criteria to total a category within a period.",
       body="""<p>Every extra condition is another range-and-criterion pair:</p>""" +
       fx("Category within a date range",
          '=SUMIFS(Data!$D$2:$D$5000,Data!$C$2:$C$5000,$A2,\n'
          '        Data!$B$2:$B$5000,">="&$B$1,Data!$B$2:$B$5000,"<="&$B$2)',
          """<p>Note <code>"&gt;="&amp;$B$1</code> &mdash; the operator is a string, joined to the
cell reference with <code>&amp;</code>. Typing <code>"&gt;=$B$1"</code> instead compares against the
literal text and silently returns zero.</p>""")),
  dict(h="For exploring, use a pivot table on a real table",
       plain="Format the data as a table with Ctrl+T first, then Insert > PivotTable. A table source grows automatically as rows are added.",
       body="""<p>Press <strong>Ctrl+T</strong> on your data first, then <em>Insert &rarr;
PivotTable</em>. A table source expands as rows are added, so new data appears on refresh. A fixed
range like <code>A1:D5000</code> silently ignores row 5001 forever &mdash; the most common reason a
pivot total is quietly wrong.</p>"""),
 ],
 body="""<h2>Why SUMIFS returns zero</h2>
<p>Nearly always one of three things:</p>
<ul>
<li><strong>The category has a trailing space</strong> in the data but not in your label, so nothing
matches.</li>
<li><strong>The sum column is text</strong>, not numbers &mdash; <code>SUMIFS</code> skips text
exactly as <code>SUM</code> does.</li>
<li><strong>The operator is inside the quotes</strong>: <code>"&gt;=$B$1"</code> instead of
<code>"&gt;="&amp;$B$1</code>. The first compares against a literal string and matches nothing.</li>
</ul>
<h2>SUMIF and SUMIFS put their arguments in different orders</h2>
<p>This catches everyone. <code>SUMIF(range, criterion, sum_range)</code> puts the sum range
<em>last</em>. <code>SUMIFS(sum_range, range1, criterion1, ...)</code> puts it <em>first</em>. Use
<code>SUMIFS</code> for everything, even with one condition, and the inconsistency stops mattering.</p>
<h2>Counting and averaging work the same way</h2>
<p><code>COUNTIFS</code> and <code>AVERAGEIFS</code> take the same argument shape. <code>AVERAGEIFS</code>
returns <code>#DIV/0!</code> when nothing matches, so wrap it in <code>IFERROR</code> if empty
categories are expected.</p>
<h2>Google Sheets has a third option</h2>
<p>Sheets has <code>SUMIFS</code> and pivot tables too, plus <code>QUERY</code>, which does
SQL-style grouping in a single formula:
<code>=QUERY(A:D,"select C, sum(D) group by C")</code>. Excel has no equivalent.</p>""",
 faq=[
  ("Should I use SUMIFS or a pivot table?",
   "SUMIFS when the number belongs in a report layout you control and must update automatically. A pivot table when you are exploring the data and do not yet know which breakdown you need."),
  ("Why does my SUMIFS return zero?",
   "Usually a trailing space on the category, a sum column stored as text, or an operator written inside the quotes as \">=$B$1\" instead of \">=\"&$B$1."),
  ("Why is my pivot table total wrong?",
   "It is showing a cached result and needs refreshing, or new rows fell outside a fixed source range. Base the pivot on a table created with Ctrl+T so it grows automatically."),
  ("What is the difference between SUMIF and SUMIFS?",
   "The argument order. SUMIF takes the sum range last; SUMIFS takes it first. Use SUMIFS for everything, even single conditions, and the inconsistency stops being a problem."),
  ("How many conditions can SUMIFS handle?",
   "Up to 127 criteria pairs. Every range must be the same height as the sum range or you get a #VALUE! error."),
  ("Is there a SQL-style GROUP BY in Excel?",
   "Not natively. Google Sheets has QUERY, which does it in one formula. In Excel the equivalent is SUMIFS, a pivot table, or Power Query's Group By step."),
 ],
 related=[("excel-sum-visible-rows-only", "Summing only the rows a filter left visible"),
          ("excel-count-functions-explained", "COUNT, COUNTA, COUNTIF and COUNTBLANK"),
          ("excel-numbers-stored-as-text", "SUM is ignoring half my column")],
),

dict(
 slug="excel-join-two-sheets-lookup",
 title="Join Two Excel Sheets the Way SQL Would",
 description="Pull columns from one sheet into another with XLOOKUP, INDEX/MATCH or VLOOKUP. Which to use, why VLOOKUP breaks, and how to handle unmatched rows.",
 h1="I need to pull data from one sheet into another",
 lead="You have orders in one sheet and customers in another, joined by an ID. In SQL this is a join. In Excel it is a lookup, and which function you pick decides how badly it breaks when someone inserts a column.",
 category=CAT, group=GROUP,
 card_title="Joining two sheets on a key",
 card_blurb="XLOOKUP, INDEX/MATCH and VLOOKUP compared, and why VLOOKUP breaks.",
 chips=["XLOOKUP", "INDEX + MATCH", "Excel + Google Sheets"],
 keywords=["excel join two sheets", "excel vlookup another sheet", "excel xlookup",
           "excel index match", "excel merge two tables", "excel lookup between sheets"],
 short_answer="""<p><strong>Use <code>XLOOKUP</code> if you have Microsoft 365 or Excel 2021, and
<code>INDEX</code>/<code>MATCH</code> otherwise.</strong>
<code>=XLOOKUP(A2,Customers!$A:$A,Customers!$C:$C,"not found")</code> pulls a value across, handles
the not-found case in the formula, and does not care where the columns sit. <code>VLOOKUP</code>
works but refers to the return column by <em>position</em>, so inserting a column silently changes
what it returns.</p>""",
 problem_h="Why VLOOKUP breaks and the others do not",
 problem="""<p><code>VLOOKUP</code>'s third argument is a column <em>number</em>. Written as
<code>VLOOKUP(A2,Customers!A:F,3,FALSE)</code>, it means &ldquo;the third column of that range&rdquo;.</p>
<p>Insert a new column anywhere inside that range &mdash; something a colleague may do for entirely
good reasons &mdash; and the third column is now a different field. The formula does not error. It
returns the wrong data, confidently, and there is nothing on screen to indicate it.</p>
<p><code>XLOOKUP</code> and <code>INDEX</code>/<code>MATCH</code> both refer to the return column by
<em>reference</em>, so an inserted column shifts the reference with it and the formula keeps
returning the same field. This is the whole reason to move off <code>VLOOKUP</code>.</p>
<p><code>VLOOKUP</code> also cannot look to its left: the key must be in the first column of the
range. <code>XLOOKUP</code> and <code>INDEX</code>/<code>MATCH</code> have no such restriction.</p>""",
 symptoms=symptom_table([
   ["#N/A on rows you can see exist",
    "Invisible characters, or a type mismatch",
    "Clean both key columns and check types"],
   ["Wrong data after someone edited the other sheet",
    "<code>VLOOKUP</code>'s column index now points elsewhere",
    "Switch to <code>XLOOKUP</code> or <code>INDEX</code>/<code>MATCH</code>"],
   ["#REF! in the formula",
    "The column index is beyond the range",
    "Check the range covers the return column"],
   ["Returns the first match only",
    "Lookups return one value by design",
    "Use <code>FILTER</code>, or aggregate with <code>SUMIFS</code>"],
   ["Workbook became very slow",
    "Thousands of lookups over whole-column ranges",
    "Limit ranges, or use Power Query to merge"],
 ]),
 howto_name="How to look up data from another sheet",
 howto_desc="Choose the function, handle the not-found case, and check the key columns match.",
 steps=[
  dict(h="Microsoft 365: use XLOOKUP",
       plain="XLOOKUP takes the lookup value, the column to search, the column to return, and what to show when nothing matches.",
       body="""<p>Four arguments, in a readable order:</p>""" +
       fx("XLOOKUP across sheets",
          '=XLOOKUP(A2,Customers!$A:$A,Customers!$C:$C,"not found")',
          """<p>Lookup value, where to search, what to return, and the not-found result. Exact match is
the default &mdash; unlike <code>VLOOKUP</code>, where forgetting <code>FALSE</code> gives you an
approximate match and quietly wrong answers.</p>""")),
  dict(h="Older Excel: use INDEX and MATCH",
       plain="INDEX returns a value from a column by position, and MATCH finds that position. Together they do what XLOOKUP does and work in every version.",
       body="""<p>Read it inside out: <code>MATCH</code> finds the row, <code>INDEX</code> fetches
from it.</p>""" +
       fx("INDEX and MATCH",
          '=IFERROR(INDEX(Customers!$C:$C,MATCH(A2,Customers!$A:$A,0)),"not found")',
          """<p>The <code>0</code> in <code>MATCH</code> means exact match and is not optional &mdash;
without it you get an approximate match against unsorted data, which returns nonsense. Works in every
version of Excel, in Sheets and in LibreOffice.</p>""")),
  dict(h="Always handle the not-found case",
       plain="Wrap the lookup so unmatched rows show a readable label instead of #N/A, and so a genuine failure is distinguishable from a missing record.",
       body="""<p>A column of <code>#N/A</code> makes every downstream <code>SUM</code> fail too.
<code>XLOOKUP</code> takes the fallback as its fourth argument; for
<code>INDEX</code>/<code>MATCH</code> use <code>IFERROR</code>.</p>
<p>Use a specific label such as <code>"no customer record"</code> rather than an empty string. A blank
tells you nothing about whether the lookup failed or the source was genuinely empty.</p>"""),
  dict(h="Check the key columns are the same type",
       plain="If the ID is text in one sheet and a number in the other, every lookup fails. Test with ISTEXT on both sides and convert one.",
       body="""<p>This is the most common cause of a lookup that fails on every row. Test both
sides:</p>""" +
       fx("Do the keys match in type?", '=ISTEXT(A2)      =ISTEXT(Customers!A2)',
          """<p>Different answers mean no row will ever match. Convert one side, or wrap both in
<code>TEXT(...,"@")</code> so the comparison is string to string.</p>""")),
 ],
 body="""<h2>When you need more than one match</h2>
<p>Lookups return a single value. To bring back <em>every</em> matching row &mdash; all orders for a
customer, say &mdash; use <code>FILTER</code> on Microsoft 365:</p>
""" + fx("Every matching row", '=FILTER(Orders!$A:$D,Orders!$B:$B=A2,"no orders")',
"""<p>On older Excel there is no clean formula for this. Use a pivot table, or aggregate instead of
listing: <code>SUMIFS</code> for a total, <code>COUNTIFS</code> for a count.</p>""") + """
<h2>Power Query is the real join</h2>
<p>For a genuine table-to-table join, Power Query is the right tool and almost nobody reaches for it.
<em>Data &rarr; Get Data &rarr; Combine Queries &rarr; Merge</em> gives you inner, left, right, full
outer and anti joins by name &mdash; the same vocabulary as SQL.</p>
<p>It is also dramatically faster. Fifty thousand <code>XLOOKUP</code> formulas recalculate on every
change; a merged query is computed once on refresh. If your workbook has slowed to a crawl from
lookups, this is the fix.</p>
<h2>Clean the keys first</h2>
<p>Everything here assumes the two key columns actually match. In practice they usually do not
&mdash; different systems, different exports, different amounts of whitespace. Clean both sides
before you conclude a record is missing.</p>""",
 faq=[
  ("Should I use VLOOKUP or XLOOKUP?",
   "XLOOKUP if you have it. It refers to the return column by reference rather than by position, so an inserted column cannot silently change what the formula returns, and it can look to the left."),
  ("What is the equivalent of a SQL join in Excel?",
   "For a single column, a lookup. For a genuine table-to-table join, Power Query's Merge, which offers inner, left, right, full outer and anti joins by name."),
  ("Why does my VLOOKUP return the wrong column?",
   "Its third argument is a column number, not a reference. Inserting a column inside the range changes which field that number points at, and the formula returns wrong data without erroring."),
  ("How do I return every matching row rather than the first?",
   "Use FILTER on Microsoft 365. On older Excel there is no clean formula — use a pivot table, or aggregate with SUMIFS or COUNTIFS instead of listing."),
  ("Why does every row return #N/A?",
   "Most often the key is text on one side and a number on the other, so nothing can match. Check with ISTEXT on both sides. Invisible characters are the other common cause."),
  ("My workbook is very slow with lookups. What should I do?",
   "Avoid whole-column ranges, and consider replacing the lookups with a Power Query merge, which computes once on refresh rather than on every recalculation."),
 ],
 related=[("excel-vlookup-non-breaking-space", "#N/A when the value is clearly there"),
          ("excel-compare-two-lists", "Find what is in list A but not list B"),
          ("excel-sumifs-vs-pivot-table", "Group and sum by category")],
),

dict(
 slug="excel-sum-visible-rows-only",
 title="Sum Only the Visible Rows After Filtering in Excel",
 description="SUM ignores filters and totals everything. SUBTOTAL sums what the filter left; AGGREGATE also skips manually hidden rows and errors. When to use each.",
 h1="My total does not change when I filter",
 lead="You filter to one region and the total at the bottom stays the same. <code>SUM</code> has no idea a filter exists &mdash; it adds every cell in the range, hidden or not.",
 category=CAT, group=GROUP,
 card_title="Totalling filtered rows",
 card_blurb="SUM ignores filters. SUBTOTAL and AGGREGATE do not — and they differ.",
 chips=["SUBTOTAL", "AGGREGATE", "Excel + Google Sheets"],
 keywords=["excel sum visible rows", "excel subtotal function", "excel sum filtered data",
           "excel aggregate function", "excel sum ignore hidden rows", "excel subtotal 109"],
 short_answer="""<p><strong><code>=SUBTOTAL(109,D2:D500)</code> sums only the rows a filter has left
visible.</strong> The <code>109</code> is what makes it ignore hidden rows &mdash; <code>9</code>
respects filters but still includes rows hidden by hand. <code>AGGREGATE</code> goes further and can
also skip error values: <code>=AGGREGATE(9,7,D2:D500)</code> ignores both hidden rows and errors,
which <code>SUBTOTAL</code> cannot do.</p>""",
 problem_h="Why this one is dangerous",
 problem="""<p>Most Excel errors announce themselves. This one does not.</p>
<p>You filter a 5,000-row sheet to a single supplier, look at the total, and use it. The total is for
all 5,000 rows. There is no error, no warning, and the number is entirely plausible &mdash; it is just
answering a different question from the one you asked.</p>
<p>It is a favourite in audit findings for exactly that reason: the filter changes what you see, and
<code>SUM</code> keeps reporting on what you cannot.</p>""",
 symptoms=symptom_table([
   ["Total unchanged when you filter",
    "<code>SUM</code> has no awareness of filters",
    "Use <code>SUBTOTAL(109,...)</code>"],
   ["Changes on filter, not on hiding rows",
    "You used function 9 rather than 109",
    "Use 109 to exclude manually hidden rows"],
   ["Nested subtotals double-counting",
    "<code>SUBTOTAL</code> ignores other <code>SUBTOTAL</code>s &mdash; this is correct",
    "No action needed"],
   ["<code>#DIV/0!</code> in a filtered average",
    "The filter left no visible rows",
    "Wrap in <code>IFERROR</code>"],
   ["Total wrong because of an error cell",
    "<code>SUBTOTAL</code> propagates errors",
    "Use <code>AGGREGATE(9,7,...)</code>"],
 ]),
 howto_name="How to total only what a filter has left visible",
 howto_desc="Pick the function code that matches which rows you want excluded.",
 steps=[
  dict(h="Use SUBTOTAL with 109 for a filtered sum",
       plain="Put =SUBTOTAL(109,D2:D500) at the bottom of the column. It totals only the rows the filter has left visible.",
       body="""<p>The first argument names the operation and how to treat hidden rows:</p>""" +
       fx("Sum the visible rows", '=SUBTOTAL(109,D2:D500)',
          """<p><strong>9</strong> means SUM respecting filters; <strong>109</strong> means SUM
respecting filters <em>and</em> manually hidden rows. Use 109 unless you have a specific reason not
to.</p>""")),
  dict(h="Use the same pattern for other operations",
       plain="SUBTOTAL supports count, average, min and max with the same 100-series codes for ignoring hidden rows.",
       body="""<p>Add 100 to the base code to make it ignore manually hidden rows:</p>
<ul>
<li><code>101</code> AVERAGE &nbsp;&middot;&nbsp; <code>102</code> COUNT &nbsp;&middot;&nbsp;
<code>103</code> COUNTA</li>
<li><code>104</code> MAX &nbsp;&middot;&nbsp; <code>105</code> MIN &nbsp;&middot;&nbsp;
<code>109</code> SUM</li>
</ul>"""),
  dict(h="Use AGGREGATE when the column contains errors",
       plain="AGGREGATE takes a function number and an options number, and option 7 ignores hidden rows and error values together.",
       body="""<p><code>SUBTOTAL</code> cannot survive an error in the range &mdash; one
<code>#N/A</code> and the total is <code>#N/A</code>. <code>AGGREGATE</code> can skip them:</p>""" +
       fx("Sum visible rows, ignoring errors", '=AGGREGATE(9,7,D2:D500)',
          """<p>First argument the operation (9 = SUM), second the options (7 = ignore hidden rows and
errors). This is the robust choice for a column fed by lookups, where a few <code>#N/A</code> values
are normal.</p>""")),
  dict(h="Let a table do it for you",
       plain="Format the range as a table with Ctrl+T and switch on the Total Row. Excel inserts a SUBTOTAL formula automatically.",
       body="""<p><strong>Ctrl+T</strong>, then tick <em>Total Row</em> on the Table Design tab. Excel
writes the <code>SUBTOTAL</code> for you and each column gets a dropdown to choose the operation. It
is also the version least likely to be broken by the next person.</p>"""),
 ],
 body="""<h2>SUBTOTAL ignores other SUBTOTALs, on purpose</h2>
<p>If a range contains its own <code>SUBTOTAL</code> formulas &mdash; per-group totals down the sheet
&mdash; a <code>SUBTOTAL</code> over all of them does <strong>not</strong> double-count. It skips
nested <code>SUBTOTAL</code> results by design, which is what makes grouped reports work.</p>
<p><code>SUM</code> has no such rule. A <code>SUM</code> over a range containing subtotal rows counts
everything twice, which is a classic source of a total that is exactly double what it should be.</p>
<h2>Counting the visible rows</h2>
<p>To see how many rows a filter has left:</p>
""" + fx("How many rows are visible?", '=SUBTOTAL(103,A2:A500)',
"""<p><code>103</code> is COUNTA ignoring hidden rows. Useful above a filtered list as a
&ldquo;showing N of M&rdquo; indicator.</p>""") + """
<h2>The 9 versus 109 distinction</h2>
<p>Both respect autofilters. Only the 100-series also excludes rows hidden manually with
<em>Hide Rows</em>. Since someone hiding a row almost always means &ldquo;ignore this&rdquo;, 109 is
the safer default and 9 is the one to justify.</p>
<h2>Google Sheets</h2>
<p>Sheets has <code>SUBTOTAL</code> with the same codes. It does not have <code>AGGREGATE</code>;
where you need to ignore errors, filter them out with <code>IFERROR</code> in a helper column or use
<code>QUERY</code>.</p>""",
 faq=[
  ("Why does my total not change when I filter?",
   "SUM has no awareness of filters and adds every cell in the range, visible or not. Use SUBTOTAL(109, range) to total only the visible rows."),
  ("What is the difference between SUBTOTAL 9 and 109?",
   "Both respect autofilters. 109 additionally excludes rows hidden manually with Hide Rows. 109 is the safer default."),
  ("What does AGGREGATE do that SUBTOTAL cannot?",
   "It can ignore error values. One #N/A in the range makes SUBTOTAL return #N/A, whereas =AGGREGATE(9,7,range) skips both hidden rows and errors."),
  ("Will SUBTOTAL double-count my group subtotals?",
   "No. SUBTOTAL deliberately ignores other SUBTOTAL results inside its range. A plain SUM over the same range would double-count them."),
  ("How do I count the rows a filter left visible?",
   "Use =SUBTOTAL(103,range), which is COUNTA ignoring hidden rows."),
  ("Does this work in Google Sheets?",
   "SUBTOTAL works with the same codes. AGGREGATE does not exist there, so handle errors with IFERROR in a helper column instead."),
 ],
 related=[("excel-sumifs-vs-pivot-table", "Group and sum by category"),
          ("excel-count-functions-explained", "COUNT, COUNTA, COUNTIF and COUNTBLANK"),
          ("excel-numbers-stored-as-text", "SUM is ignoring half my column")],
),

dict(
 slug="excel-return-blank-not-zero",
 title="Make an Excel Formula Return a Real Blank, Not Zero",
 description="An IF returning an empty string looks blank but is text, so ISBLANK is false and charts plot a gap as zero. What works instead.",
 h1="My formula returns a blank that is not really blank",
 lead="You wrote <code>IF(A2=\"\",\"\",A2*2)</code> to keep the sheet tidy. The cell looks empty, but <code>ISBLANK</code> says it is not, <code>COUNTA</code> counts it, and the chart plots it as zero.",
 category=CAT, group=GROUP,
 card_title="Empty-looking cells that are not empty",
 card_blurb='Why "" is not blank, what it breaks, and what to do instead.',
 chips=["IF + ISBLANK", "Charts", "Excel + Google Sheets"],
 keywords=["excel return blank not zero", "excel empty string vs blank", "excel isblank not working",
           "excel hide zero values", "excel na chart gap", "excel formula blank cell"],
 short_answer="""<p><strong>A formula cannot return a truly empty cell. <code>""</code> is an empty
<em>string</em> &mdash; text of zero length &mdash; which is why <code>ISBLANK</code> returns FALSE
and <code>COUNTA</code> counts it.</strong> If you want a chart to break the line, return
<code>NA()</code> instead. If you only want to hide zeros visually, do it with a number format or
with the worksheet option rather than in the formula.</p>""",
 problem_h="Three different kinds of nothing",
 problem="""<p>Excel has three states that all look like an empty cell, and they behave
differently:</p>
<ul>
<li><strong>A genuinely empty cell.</strong> Nothing has been entered. <code>ISBLANK</code> is TRUE,
<code>COUNTA</code> ignores it, and a chart breaks the line.</li>
<li><strong>An empty string</strong> from a formula returning <code>""</code>. Looks identical.
<code>ISBLANK</code> is FALSE, <code>COUNTA</code> counts it, and a chart plots it as
<strong>zero</strong>.</li>
<li><strong>A space.</strong> Genuinely a character. Breaks lookups as well.</li>
</ul>
<p>The chart behaviour is where this costs real money: a monthly series with <code>""</code> for
future months does not stop at today &mdash; it dives to zero and stays there, and the chart looks
like a catastrophe rather than an incomplete year.</p>""",
 symptoms=symptom_table([
   ["<code>ISBLANK</code> false on an empty-looking cell",
    "It holds an empty string, not nothing",
    'Test with <code>=A2=""</code> instead'],
   ["Chart line drops to zero",
    'The <code>""</code> is plotted as zero',
    "Return <code>NA()</code> for gaps"],
   ["<code>COUNTA</code> too high",
    "It counts empty strings",
    "Use <code>COUNTIF(range,\"&lt;&gt;\")</code>"],
   ["<code>SUM</code> unaffected but <code>AVERAGE</code> wrong",
    "<code>AVERAGE</code> is affected by what counts as present",
    "Return <code>NA()</code>, which <code>AVERAGE</code> skips"],
   ["<code>0</code> appearing where you wanted nothing",
    "A reference to an empty cell returns 0",
    'Use <code>IF(A2="","",A2)</code> or a number format'],
 ]),
 howto_name="How to handle blanks in Excel formulas",
 howto_desc="Decide whether you need a visual blank, a chart gap or a real empty cell.",
 steps=[
  dict(h="For a chart gap, return NA()",
       plain="Return NA() rather than an empty string, so the chart breaks the line instead of plotting zero.",
       body="""<p><code>NA()</code> is the only value a chart treats as &ldquo;no data here&rdquo;:</p>""" +
       fx("A gap a chart will respect", '=IF(A2="",NA(),A2*2)',
          """<p>The cell shows <code>#N/A</code>, which is ugly on the sheet but correct in the chart.
Hide it with conditional formatting that sets the font to the background colour where
<code>ISNA</code> is TRUE.</p>""")),
  dict(h="To test for either kind of empty, do not use ISBLANK",
       plain='Compare the cell to an empty string with =A2="" — that returns TRUE for both a genuinely empty cell and one holding an empty string.',
       body="""<p><code>ISBLANK</code> only catches genuinely empty cells. This catches both:</p>""" +
       fx("Is it empty, either way?", '=A2=""',
          """<p>TRUE for a truly empty cell and for one containing an empty string. This is what you
want almost every time.</p>""")),
  dict(h="To hide zeros, use a number format, not a formula",
       plain="Apply a custom number format with a third section, or switch off zero display for the sheet, rather than testing for zero in every formula.",
       body="""<p>Do not litter the sheet with <code>IF(x=0,"",x)</code>. A custom number format has
three sections &mdash; positive, negative, zero:</p>""" +
       fx("Custom format that hides zeros", '#,##0;-#,##0;""',
          """<p>The empty third section hides zeros while keeping the underlying value intact, so
every calculation downstream still works. For a whole sheet, <em>File &rarr; Options &rarr;
Advanced</em> and untick <em>Show a zero in cells that have a zero value</em>.</p>""")),
  dict(h="To count non-empty cells properly",
       plain='Use COUNTIF with the "<>" criterion, which counts cells that are not empty strings, rather than COUNTA.',
       body="""<p><code>COUNTA</code> counts empty strings as present. This does not:</p>""" +
       fx("Count what is genuinely there", '=COUNTIF(A2:A500,"<>")',
          """<p>Counts cells that are neither empty nor an empty string &mdash; usually the number you
actually wanted.</p>""")),
 ],
 body="""<h2>Why a formula cannot produce a truly empty cell</h2>
<p>A cell containing a formula contains something by definition, so it cannot be empty. The closest
available results are an empty string, which looks blank but is text, and <code>NA()</code>, which is
an error value that most aggregate functions skip.</p>
<p>The only way to get a genuinely empty cell is for no formula to be there: delete it, or use Power
Query, which produces values rather than formulas and can return real nulls.</p>
<h2>Empty strings break lookups too</h2>
<p>A lookup against a range whose keys are <code>""</code> from a formula behaves differently from one
against genuinely empty cells &mdash; the empty string is a value and can match another empty string.
If a lookup is matching rows you expected to be ignored, this is usually why.</p>
<h2>Which functions treat them differently</h2>
<ul>
<li><code>COUNTA</code> counts <code>""</code>; <code>COUNT</code> does not (it counts numbers only)</li>
<li><code>ISBLANK</code> is FALSE for <code>""</code>; <code>=A2=""</code> is TRUE for both</li>
<li><code>AVERAGE</code> skips text, so <code>""</code> is excluded &mdash; but a real zero is not</li>
<li>Charts plot <code>""</code> as zero and break the line on <code>NA()</code></li>
</ul>
<h2>Google Sheets</h2>
<p>Same distinction, same behaviour. Sheets adds <code>IFERROR</code>-style handling in more places
and its charts have an explicit setting for how to plot empty cells, under Chart editor &rarr;
Customise &rarr; Chart style.</p>""",
 faq=[
  ("Why does ISBLANK return FALSE on my empty cell?",
   "The cell holds an empty string returned by a formula, not nothing. ISBLANK only returns TRUE for genuinely empty cells. Use =A2=\"\" to test for both cases."),
  ("How do I make a chart skip a data point?",
   "Return NA() rather than an empty string. Charts plot an empty string as zero and only break the line on #N/A."),
  ("Can a formula produce a truly empty cell?",
   "No. A cell containing a formula contains something by definition. The nearest options are an empty string or NA(). Only Power Query, which produces values rather than formulas, can return real nulls."),
  ("How do I hide zeros without changing my formulas?",
   "Use a custom number format with an empty third section, such as #,##0;-#,##0;\"\", or switch off zero display for the sheet in File > Options > Advanced."),
  ("Why is my COUNTA too high?",
   "It counts cells containing empty strings as present. Use =COUNTIF(range,\"<>\") to count only cells that are genuinely not empty."),
  ("Does AVERAGE include empty strings?",
   "No — AVERAGE skips text, so empty strings are excluded. A real zero is included, which is usually the actual cause of an average that looks too low."),
 ],
 related=[("excel-count-functions-explained", "COUNT, COUNTA, COUNTIF and COUNTBLANK"),
          ("excel-formulas-not-updating", "My formulas stopped recalculating"),
          ("excel-sum-visible-rows-only", "Summing only the rows a filter left visible")],
),

dict(
 slug="excel-count-functions-explained",
 title="COUNT, COUNTA, COUNTIF and COUNTBLANK: Which to Use",
 description="COUNT only counts numbers, which is why it under-reports text columns. What each counting function includes, and the gaps that reveal data problems.",
 h1="My row count is wrong and I do not know which COUNT to use",
 lead="Excel has five counting functions and they disagree with each other on purpose. The disagreements are useful &mdash; the gap between two of them is often the fastest diagnostic you have.",
 category=CAT, group=GROUP,
 card_title="Which COUNT function to use",
 card_blurb="What each one includes, and why the gaps between them are diagnostic.",
 chips=["Five functions", "Diagnostics", "Excel + Google Sheets"],
 keywords=["excel count vs counta", "excel countif", "excel countblank", "excel count functions",
           "excel count not counting", "excel counta text"],
 short_answer="""<p><strong><code>COUNT</code> counts numbers only. <code>COUNTA</code> counts
anything non-empty, including text and empty strings. <code>COUNTBLANK</code> counts empty cells
<em>and</em> empty strings. <code>COUNTIF</code> and <code>COUNTIFS</code> count what matches your
conditions.</strong> If <code>COUNT</code> is lower than you expect on a numeric column, the missing
cells are numbers stored as text.</p>""",
 problem_h="The gaps are the useful part",
 problem="""<p>Most guides present these as five ways to do the same thing. They are more useful as
instruments: the <em>difference</em> between two of them tells you something about the data that
neither tells you alone.</p>
<ul>
<li><code>COUNTA</code> &minus; <code>COUNT</code> = <strong>how many numeric-looking cells are
actually text.</strong> On a column that should be all numbers, this should be zero.</li>
<li><code>COUNTBLANK</code> &minus; genuinely empty cells = <strong>how many empty strings</strong>
are sitting in the range from formulas returning <code>""</code>.</li>
<li><code>COUNTA</code> &minus; <code>COUNTIF(range,"&lt;&gt;")</code> = the same measure from the
other direction.</li>
</ul>
<p>Running the first of those on any imported column takes five seconds and finds the
&ldquo;<code>SUM</code> is wrong&rdquo; problem before it reaches a report.</p>""",
 symptoms=symptom_table([
   ["<code>COUNT</code> lower than expected",
    "Some cells are numbers stored as text",
    "Convert them, or count with <code>COUNTA</code>"],
   ["<code>COUNTA</code> higher than the visible rows",
    "Empty strings from formulas are being counted",
    'Use <code>COUNTIF(range,"&lt;&gt;")</code>'],
   ["<code>COUNTBLANK</code> higher than expected",
    "It counts empty strings as blank",
    "That is intended &mdash; the gap is diagnostic"],
   ["<code>COUNTIF</code> returns 0",
    "The criterion does not match exactly",
    "Check for spaces; try a wildcard"],
   ["Counts change when you filter",
    "They do not &mdash; use <code>SUBTOTAL</code> for that",
    "<code>SUBTOTAL(103,...)</code> counts visible rows"],
 ]),
 howto_name="How to choose the right counting function",
 howto_desc="Match the function to what you mean by 'present', and use the gaps as a check.",
 steps=[
  dict(h="Counting numbers: COUNT",
       plain="COUNT counts only cells containing numbers, and ignores text, blanks and errors.",
       body="""<p><code>=COUNT(A2:A500)</code> counts numeric cells and nothing else. Dates count,
because dates are numbers. Text does not, even if it looks numeric.</p>"""),
  dict(h="Counting anything present: COUNTA",
       plain="COUNTA counts every cell that is not genuinely empty, including text, numbers, errors and empty strings.",
       body="""<p><code>=COUNTA(A2:A500)</code> counts everything that is not empty &mdash; including
error values and including empty strings from formulas, which is the one to watch.</p>"""),
  dict(h="Diagnose a numeric column with the gap",
       plain="Subtract COUNT from COUNTA over the same range. Any non-zero result is the number of cells that look numeric but are stored as text.",
       body="""<p>The most useful five seconds you can spend on an imported column:</p>""" +
       fx("How many are secretly text?", '=COUNTA(A2:A500)-COUNT(A2:A500)',
          """<p>Zero means the column is genuinely all numbers. Anything else is the count of cells
<code>SUM</code> is silently ignoring.</p>""")),
  dict(h="Counting by condition: COUNTIF and COUNTIFS",
       plain="COUNTIF takes one range and one criterion; COUNTIFS takes as many range-and-criterion pairs as you need.",
       body="""<p>One condition or many:</p>""" +
       fx("Conditional counting",
          '=COUNTIF(C2:C500,"North")\n'
          '=COUNTIFS(C2:C500,"North",D2:D500,">1000")',
          """<p>Wildcards work in the criterion: <code>"*Ltd"</code> matches anything ending in Ltd,
<code>"?????"</code> matches any five characters. To match a literal asterisk or question mark,
prefix it with a tilde: <code>"~*"</code>.</p>""")),
 ],
 body="""<h2>The five, in one place</h2>
<ul>
<li><code>COUNT</code> &mdash; numbers only. Dates included, text excluded.</li>
<li><code>COUNTA</code> &mdash; anything not genuinely empty, including errors and empty strings.</li>
<li><code>COUNTBLANK</code> &mdash; empty cells <em>and</em> empty strings.</li>
<li><code>COUNTIF</code> &mdash; one range, one criterion.</li>
<li><code>COUNTIFS</code> &mdash; many ranges, many criteria, all of which must hold.</li>
</ul>
<p>Note that <code>COUNTA</code> and <code>COUNTBLANK</code> both count empty strings, so on a range
containing them the two will sum to <em>more</em> than the number of cells. That is not a bug; it is
the two functions disagreeing about what an empty string is.</p>
<h2>Counting unique values</h2>
<p>None of these does it. On Microsoft 365 use <code>=COUNTA(UNIQUE(A2:A500))</code>; on older
versions use the <code>SUMPRODUCT</code>/<code>COUNTIF</code> pattern. Google Sheets has
<code>COUNTUNIQUE</code>, which Excel does not.</p>
<h2>Counting visible rows only</h2>
<p>All five ignore filters. For a count that respects them, use <code>=SUBTOTAL(103,A2:A500)</code>,
which is <code>COUNTA</code> restricted to visible rows.</p>
<h2>Why COUNTIF returns zero when the value is there</h2>
<p>Same reason lookups fail: the criterion has to match the stored value exactly. Trailing spaces,
non-breaking spaces and a number-versus-text mismatch all produce a confident zero.</p>""",
 faq=[
  ("What is the difference between COUNT and COUNTA?",
   "COUNT counts only cells containing numbers. COUNTA counts every cell that is not genuinely empty, including text, errors and empty strings."),
  ("Why is my COUNT lower than the number of rows?",
   "Some of the cells are numbers stored as text, which COUNT does not count. The difference between COUNTA and COUNT tells you how many."),
  ("Does COUNTBLANK count formula blanks?",
   "Yes. COUNTBLANK counts both genuinely empty cells and cells containing an empty string returned by a formula."),
  ("How do I count unique values?",
   "None of the COUNT functions does it. Use =COUNTA(UNIQUE(range)) on Microsoft 365, or the SUMPRODUCT and COUNTIF pattern on older versions."),
  ("Why does COUNTIF return zero when I can see matching values?",
   "The criterion must match the stored value exactly. Trailing or non-breaking spaces, or a mismatch between text and numbers, all cause it to find nothing."),
  ("How do I count only the rows a filter left visible?",
   "Use =SUBTOTAL(103,range). The COUNT functions themselves have no awareness of filters."),
 ],
 related=[("excel-numbers-stored-as-text", "SUM is ignoring half my column"),
          ("excel-return-blank-not-zero", "Returning a real blank instead of zero"),
          ("excel-unique-values-list", "Getting a list of unique values")],
),

dict(
 slug="excel-negative-number-squared",
 title="Why =-3^2 Gives 9 in Excel Instead of -9",
 description="Excel applies the unary minus before the exponent, so -3^2 is (-3)^2 = 9. Where this silently corrupts real calculations, and how to write it safely.",
 h1="Excel says minus three squared is positive nine",
 lead="Type <code>=-3^2</code> and Excel returns 9. Every maths convention says it should be &minus;9. Excel is not wrong by accident &mdash; it applies the minus sign first, deliberately, and it is one of the very few places where Excel differs from standard notation.",
 category=CAT, group=GROUP,
 card_title="Why =-3^2 returns 9",
 card_blurb="Excel binds the unary minus before the exponent. Where that quietly breaks results.",
 chips=["Operator precedence", "Silent error", "Excel + Google Sheets"],
 keywords=["excel negative number squared", "excel operator precedence", "excel unary minus",
           "excel power operator", "excel -3^2", "excel exponent negative"],
 short_answer="""<p><strong>Excel binds the unary minus tighter than the exponent, so
<code>-3^2</code> is evaluated as <code>(-3)^2</code>, which is 9.</strong> Standard mathematical
notation binds the exponent first, giving <code>-(3^2)</code> = &minus;9. Both are internally
consistent; Excel simply chose the other convention. Write <code>=-(3^2)</code> when you want
&minus;9, and always use brackets when a negative value meets an exponent.</p>""",
 problem_h="Where this actually costs you",
 problem="""<p>As a curiosity it is harmless. It becomes expensive when the negative is in a cell
rather than typed literally, because then nothing on screen looks unusual.</p>
<p>A variance column holding &minus;3, squared to remove the sign &mdash; a standard step in computing
a standard deviation or a sum of squares by hand &mdash; behaves as you expect, since
<code>A2^2</code> where <code>A2</code> is &minus;3 correctly gives 9. The reference is evaluated
first and the minus is part of the <em>value</em>, not an operator.</p>
<p>The trap is a formula that writes the minus itself: <code>=-A2^2</code>. If <code>A2</code> is 3,
this is <code>(-3)^2 = 9</code>, not <code>-(3^2) = -9</code>. In a discounting or a
present-value calculation, the sign of the result silently flips, and the number that appears is
entirely plausible.</p>""",
 symptoms=symptom_table([
   ["<code>=-3^2</code> returns 9",
    "Unary minus binds before the exponent",
    "Write <code>=-(3^2)</code>"],
   ["<code>=-A2^2</code> is positive",
    "Same rule, hidden behind a reference",
    "Bracket the exponent explicitly"],
   ["Sign flipped against a textbook",
    "The textbook uses standard precedence",
    "Bracket every exponent on a negative"],
   ["<code>=0-3^2</code> returns &minus;9",
    "This is a binary minus, which binds after",
    "Different operator, different rule"],
   ["Result differs from the same formula in Python",
    "Most languages follow standard precedence",
    "Bracket, and the two agree"],
 ]),
 howto_name="How to write exponents safely in Excel",
 howto_desc="Bracket the exponent whenever a minus sign is anywhere near it.",
 steps=[
  dict(h="Bracket the exponent when you want the standard result",
       plain="Write =-(3^2) rather than =-3^2. The brackets make the exponent bind first, giving -9.",
       body="""<p>Explicit brackets remove all ambiguity:</p>""" +
       fx("The two readings", '=-3^2      returns  9\n=-(3^2)    returns  -9',
          """<p>The second is what standard notation means by &minus;3&sup2;. Write it that way even
when you are sure, because the next reader will not be.</p>""")),
  dict(h="Understand the binary minus behaves differently",
       plain="A minus between two values is a binary operator and binds after the exponent, so =0-3^2 correctly returns -9.",
       body="""<p><code>=0-3^2</code> returns &minus;9, because that minus is a <em>binary</em>
operator sitting between two operands and binds after the exponent. Only the <em>unary</em> minus
&mdash; the one that negates a single value &mdash; binds first. Two different operators that share a
symbol.</p>"""),
  dict(h="Watch for it in formulas that build their own sign",
       plain="Any formula of the form =-Reference^2 has this problem. Search your workbook for a minus immediately followed by a reference and a caret.",
       body="""<p>The dangerous shape is <code>=-A2^2</code>, and it hides well because nothing looks
odd. If your workbook computes sums of squares, variances or present values, search for
<code>-</code> immediately before a reference that is raised to a power, and bracket every one.</p>"""),
  dict(h="Prefer POWER when clarity matters",
       plain="POWER(base, exponent) has no precedence ambiguity because the arguments are separated by a comma.",
       body="""<p>Where a formula will be read by other people, the function form is unambiguous:</p>""" +
       fx("No ambiguity possible", '=-POWER(3,2)     returns  -9',
          """<p>The base and the exponent are separate arguments, so there is no precedence question
to get wrong.</p>""")),
 ],
 body="""<h2>Excel's full precedence order</h2>
<p>Highest to lowest:</p>
<ol>
<li>Reference operators &mdash; range <code>:</code>, union <code>,</code>, intersection (space)</li>
<li><strong>Unary minus</strong> &mdash; this is the unusual one</li>
<li>Percent <code>%</code></li>
<li>Exponent <code>^</code></li>
<li>Multiply and divide <code>*</code> <code>/</code></li>
<li>Add and subtract <code>+</code> <code>-</code></li>
<li>Concatenate <code>&amp;</code></li>
<li>Comparison <code>=</code> <code>&lt;</code> <code>&gt;</code> <code>&lt;=</code>
<code>&gt;=</code> <code>&lt;&gt;</code></li>
</ol>
<p>Standard mathematical notation places the unary minus <em>below</em> the exponent. That single
difference is the whole issue.</p>
<h2>Percent binds before the exponent too</h2>
<p>A related surprise: <code>=2^2%</code> is <code>2^(0.02)</code>, not <code>(2^2)%</code>, because
percent also binds tighter than the exponent. Bracket that as well.</p>
<h2>Google Sheets and LibreOffice match Excel</h2>
<p>Both follow Excel's precedence for compatibility, so <code>=-3^2</code> is 9 in all three. Most
programming languages do not: Python's <code>-3**2</code> is &minus;9. If you are porting a formula
between a spreadsheet and code, this is a real source of quiet disagreement.</p>""",
 faq=[
  ("Why does Excel say -3^2 is 9?",
   "Excel applies the unary minus before the exponent, so it evaluates (-3)^2. Standard mathematical notation applies the exponent first, giving -(3^2) = -9."),
  ("Is this a bug?",
   "No, it is a documented precedence choice. It is internally consistent — it simply differs from standard mathematical notation and from most programming languages."),
  ("How do I write minus three squared correctly?",
   "Use =-(3^2), or =-POWER(3,2). Both give -9 and neither depends on remembering the precedence rule."),
  ("Why does =0-3^2 give -9?",
   "That minus is a binary operator between two operands, and binary minus binds after the exponent. Only the unary minus binds before it."),
  ("Does Google Sheets behave the same way?",
   "Yes. Sheets and LibreOffice both follow Excel's precedence for compatibility, so -3^2 is 9 in all three."),
  ("Where does this cause real errors?",
   "In formulas that write their own minus sign, such as =-A2^2, typically in variance, sum-of-squares or present-value calculations. The sign of the result flips and the number still looks plausible."),
 ],
 related=[("excel-formulas-not-updating", "My formulas stopped recalculating"),
          ("excel-absolute-relative-references", "The $ sign and why dragging breaks formulas"),
          ("excel-return-blank-not-zero", "Returning a real blank instead of zero")],
),

dict(
 slug="excel-apply-formula-entire-column",
 title="Apply a Formula to a Whole Column Without Dragging",
 description="Double-click the fill handle, use Ctrl+D, or convert the range to a table so formulas fill themselves. Four methods and when each one fails.",
 h1="I need this formula in ten thousand rows",
 lead="Dragging the fill handle down ten thousand rows is not a plan. There are four faster ways, and one of them means the formula fills itself for every row added in future.",
 category=CAT, group=GROUP,
 card_title="Filling a formula down a whole column",
 card_blurb="Double-click, Ctrl+D, a table, or a spill formula. When each one fails.",
 chips=["Ctrl+D", "Tables", "Excel + Google Sheets"],
 keywords=["excel apply formula entire column", "excel fill down shortcut", "excel ctrl d",
           "excel fill handle double click", "excel copy formula down column", "excel table formula"],
 short_answer="""<p><strong>Double-click the fill handle &mdash; the small square at the
bottom-right of the selected cell &mdash; and the formula fills down to the end of the adjacent
data.</strong> Or select the range and press <strong>Ctrl+D</strong>. Best of all, format the range
as a table with <strong>Ctrl+T</strong>: a formula entered in one cell of a table column fills the
entire column automatically, including rows added later.</p>""",
 problem_h="Which method to use, and when each one fails",
 problem="""<p>All four work. They fail in different ways, and knowing which is which saves you
discovering it on a 50,000-row sheet.</p>
<p><strong>Double-clicking the fill handle</strong> stops at the first gap in the
<em>adjacent</em> column. If column A has a blank at row 400, your formula in column B fills to row
399 and stops. On a long sheet the gap is invisible and you will not notice.</p>
<p><strong>Ctrl+D</strong> fills exactly the range you selected, so it never stops early &mdash; but
you have to select the range, which on 10,000 rows means using the Name Box rather than scrolling.</p>
<p><strong>A table</strong> fills automatically and keeps filling for rows added later. This is the
only method that stays correct over time.</p>
<p><strong>A spill formula</strong> on Microsoft 365 produces the whole column from a single cell,
with no fill at all.</p>""",
 symptoms=symptom_table([
   ["Fill stopped part-way down",
    "A gap in the adjacent column ended the double-click fill",
    "Use Ctrl+D over an explicit range"],
   ["New rows have no formula",
    "The range is not a table",
    "Convert with Ctrl+T"],
   ["Every result identical",
    "The references were absolute when they should be relative",
    "Remove the unneeded <code>$</code> signs"],
   ["<code>#SPILL!</code>",
    "Something is blocking the spill range",
    "Clear the cells below"],
   ["Workbook slowed to a crawl",
    "A million formulas over whole-column references",
    "Limit ranges, or use a spill formula"],
 ]),
 howto_name="How to fill a formula down a column",
 howto_desc="Four methods, from quickest to most durable.",
 steps=[
  dict(h="Double-click the fill handle",
       plain="Select the cell with the formula and double-click the small square at its bottom-right corner. The formula fills down to the end of the adjacent data.",
       body="""<p>Select the cell, then double-click the small square at its bottom-right. Excel
fills down as far as the neighbouring column has data. Fastest method, and the one that silently
stops at a gap &mdash; check where it ended before moving on.</p>"""),
  dict(h="Select a precise range and press Ctrl+D",
       plain="Type the range into the Name Box, press Enter to select it, and press Ctrl+D to fill the formula from the top cell down through the selection.",
       body="""<p>For an exact range, use the <strong>Name Box</strong> to the left of the formula
bar. Type <code>B2:B10000</code>, press Enter to select it, then <strong>Ctrl+D</strong>. The
formula in the top cell fills the whole selection, and gaps in neighbouring columns are
irrelevant.</p>
<p><strong>Ctrl+R</strong> does the same thing rightwards.</p>"""),
  dict(h="Convert the range to a table",
       plain="Press Ctrl+T to make the range a table. A formula typed into one cell of a column fills the whole column, and new rows inherit it automatically.",
       body="""<p>Select any cell in the data and press <strong>Ctrl+T</strong>. Now type your formula
once in a cell of an empty column: Excel fills the entire column immediately, and <em>every row added
afterwards inherits it</em>.</p>
<p>This is the only method that stays correct as the data grows. It also gives you structured
references like <code>=[@Quantity]*[@Price]</code>, which need no dollar signs and read far better
than <code>=B2*C2</code>.</p>"""),
  dict(h="Microsoft 365: return the whole column from one formula",
       plain="Give the formula a range instead of a single cell and it spills the results down automatically, with only one formula in the workbook.",
       body="""<p>Modern Excel evaluates a range argument across the whole range:</p>""" +
       fx("One formula, whole column", '=B2:B10000*C2:C10000',
          """<p>The result spills down automatically. There is only one formula in the workbook, which
recalculates far faster than 10,000 copies and cannot be partly overwritten by someone editing a
single row. Wrap in <code>FILTER</code> or <code>IF</code> to skip blanks.</p>""")),
 ],
 body="""<h2>Do not use whole-column references</h2>
<p><code>=SUM(B:B)</code> and <code>=VLOOKUP(A2,Sheet2!A:Z,3,FALSE)</code> are convenient and they are
the main cause of slow workbooks. A whole-column reference asks Excel to consider 1,048,576 rows
whether or not they contain anything.</p>
<p>One is harmless. Ten thousand lookups over whole-column ranges is tens of billions of cell
evaluations on every recalculation. Use a table, whose references cover exactly the rows in use, or
state a realistic bound.</p>
<h2>Selecting a large range without scrolling</h2>
<ul>
<li><strong>Ctrl+Shift+&darr;</strong> selects to the last non-empty cell in the column</li>
<li><strong>Ctrl+Shift+End</strong> selects to the last used cell on the sheet</li>
<li>The <strong>Name Box</strong> selects any range you can name: type <code>B2:B10000</code></li>
</ul>
<h2>Copy and Paste Special is the other reliable route</h2>
<p>Copy the formula cell, select the destination range, and use <em>Paste Special &rarr;
Formulas</em>. This pastes the formula without the source's formatting &mdash; useful when the
target column is already styled and you do not want the fill to overwrite it.</p>
<h2>Google Sheets</h2>
<p>Sheets has the same fill handle and Ctrl+D. It also has <code>ARRAYFORMULA</code>, which does what
spill formulas do in Excel and has been available far longer:
<code>=ARRAYFORMULA(B2:B*C2:C)</code>.</p>""",
 faq=[
  ("How do I apply a formula to an entire column?",
   "Double-click the fill handle at the bottom-right of the cell, or select the range and press Ctrl+D. Converting the range to a table with Ctrl+T fills the column automatically, including future rows."),
  ("Why did my fill stop part-way down?",
   "Double-clicking the fill handle fills only as far as the adjacent column has data, so a gap there ends the fill early. Use Ctrl+D over an explicitly selected range instead."),
  ("How do I make new rows get the formula automatically?",
   "Format the range as a table with Ctrl+T. A formula in one cell of a table column applies to the whole column and is inherited by every row added afterwards."),
  ("Why is my workbook so slow?",
   "Usually whole-column references such as SUM(B:B) repeated thousands of times. Each one considers over a million rows. Use a table, or bound the range to the rows in use."),
  ("What does #SPILL! mean?",
   "A spill formula could not write its results because something is in the way. Clear the cells below and to the right of the formula."),
  ("Is there an equivalent in Google Sheets?",
   "Yes — ARRAYFORMULA does what Excel's spill formulas do, and it has been available in Sheets for much longer."),
 ],
 related=[("excel-absolute-relative-references", "The $ sign and why dragging breaks formulas"),
          ("excel-formulas-not-updating", "My formulas stopped recalculating"),
          ("excel-sumifs-vs-pivot-table", "Group and sum by category")],
),
]
