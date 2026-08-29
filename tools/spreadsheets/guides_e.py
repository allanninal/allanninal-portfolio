#!/usr/bin/env python3
"""Group E — dynamic arrays, and the text work that used to need VBA.

Two clusters that belong together because they are the same shift: one formula now returns
many cells, and text problems that took a macro in 2015 take a function in 2026.

Demand: 2,915,688 views across the top 100 `array-formulas` questions. The regex article
is the single highest-view question found in either research pass at 1,363,150 — and
nearly all the content ranking for it was written before REGEXTEST, REGEXEXTRACT and
REGEXREPLACE existed, which is an unusually clean opening.

Every article says plainly which Excel versions have the function, because half the pain
here is following advice written for a version you do not have.
"""
from build_guide import fx, symptom_table

ARR = "Dynamic arrays"
TXT = "Text and regex"
G_ARR = "One formula, many answers"
G_TXT = "Text work that used to need a macro"

GUIDES_E = [

dict(
 slug="excel-spill-error",
 title="What #SPILL! Means in Excel, and How to Clear It",
 description="A formula that returns many cells needs empty room to write them. #SPILL! means something is in the way — usually a stray space or a merged cell.",
 h1="My formula returns #SPILL! and the cells below look empty",
 lead="Modern Excel formulas can return a whole column of answers from one cell. They need somewhere to put them, and <code>#SPILL!</code> means the room is not free &mdash; often because of something you cannot see.",
 category=ARR, group=G_ARR,
 card_title="#SPILL! explained",
 card_blurb="One formula, many cells — and what to do when there is no room to write them.",
 chips=["Excel 365 / 2021", "Two-minute fix", "Excel"],
 keywords=["excel spill error", "excel #spill", "excel dynamic array", "excel spill range",
           "excel formula returns multiple cells", "excel spill merged cell"],
 short_answer="""<p><strong><code>#SPILL!</code> means the formula wants to write into cells that are
not empty.</strong> Excel highlights the area it needs with a dashed border &mdash; clear everything
inside it. The usual culprits are a space someone typed years ago, a merged cell anywhere in the
range, or a formula sitting inside a table, where spilling is not allowed at all.</p>""",
 problem_h="One formula that fills many cells",
 problem="""<p>Excel used to work one cell at a time: one formula, one answer. Since 2019 a formula
can return a whole block, and Excel writes it into the cells below and to the right. That writing is
called <strong>spilling</strong>, and the block is the <strong>spill range</strong>.</p>
<p>You only type in the top-left cell. Everything else is produced by it, shown with a faint blue
border, and cannot be edited directly &mdash; change the one formula and the whole block redraws.</p>
<p>Spilling needs empty cells. If anything at all is in the way, Excel refuses rather than
overwriting your data, and shows <code>#SPILL!</code>. It is a polite error: it is protecting
something.</p>""",
 symptoms=symptom_table([
   ["<code>#SPILL!</code> and the cells look empty",
    "A space or an invisible character is in one of them",
    "Select the range and press Delete"],
   ["<code>#SPILL!</code> with nothing visible at all",
    "A merged cell inside the spill range",
    "Unmerge it"],
   ["<code>#SPILL!</code> inside a table",
    "Excel tables do not allow spilling",
    "Move the formula outside the table"],
   ["<code>#SPILL!</code> mentioning size",
    "The formula would need more rows than remain",
    "Move it up, or narrow the input range"],
   ["<code>#NAME?</code> rather than a spill",
    "Your Excel version does not have the function",
    "Use the older formula instead"],
 ]),
 howto_name="How to fix a #SPILL! error",
 howto_desc="Find what is in the way, clear it, and stop it happening again.",
 steps=[
  dict(h="Look at the dashed border",
       plain="Click the cell with the error. Excel draws a dashed outline around the area it is trying to fill — the obstruction is inside it.",
       body="""<p>Click the cell showing <code>#SPILL!</code>. Excel outlines the area it needs with
a dashed border. Whatever is blocking it is inside that outline, so you never have to guess where to
look.</p>
<p>The yellow warning triangle also names the reason &mdash; hover it and it will say whether the
range is not blank, is merged, or is too big.</p>"""),
  dict(h="Select the whole range and clear it",
       plain="Select every cell in the dashed area except the formula itself and press Delete. This removes spaces and invisible characters as well as visible content.",
       body="""<p>Select the dashed area, leave out the formula cell, and press <strong>Delete</strong>.
This is more reliable than looking for the offender, because the usual cause is a single space typed
into a cell years ago &mdash; it is not visible, and it is not blank.</p>"""),
  dict(h="Check for merged cells",
       plain="Select the range and look at the Merge & Center button. If it appears active, something inside is merged. Click it to unmerge.",
       body="""<p>A merged cell blocks a spill even when it is empty. Select the range and look at
<em>Merge &amp; Center</em> on the Home tab &mdash; if it looks pressed, something in there is
merged. Click it to unmerge.</p>
<p>Merged cells break sorting, filtering, tables and spilling. For anything holding data rather than
a title, <em>Center Across Selection</em> gives the same look with none of the damage.</p>"""),
  dict(h="Move the formula out of the table",
       plain="A spilling formula cannot live inside an Excel table created with Ctrl+T. Put it on the sheet outside the table.",
       body="""<p>Excel tables give each row its own copy of a formula, which is incompatible with
one formula filling many rows. There is no setting for this &mdash; move the formula outside the
table.</p>
<p>It can still <em>read</em> from the table. Only writing into one is the problem.</p>"""),
 ],
 body="""<h2>Pointing at a spill range</h2>
<p>You can refer to the whole result with a <code>#</code> after the top-left cell:</p>
""" + fx("The spill operator", '=SUM(D2#)',
"""<p><code>D2#</code> means &ldquo;everything <code>D2</code> spilled&rdquo;, however big that is
today. It grows and shrinks on its own, which is far better than guessing a range that is big enough
&mdash; a habit that leaves you summing a thousand empty rows.</p>""") + """
<h2>Which versions have this</h2>
<p>Dynamic arrays are in Microsoft 365 and Excel 2021 onwards. Excel 2019 and earlier do not have
them, and neither does LibreOffice in the same form. Google Sheets has had the behaviour for years
through <code>ARRAYFORMULA</code>.</p>
<p>If you send a workbook containing spilling formulas to someone on Excel 2019, they see
<code>#NAME?</code>. There is no compatibility mode for this, which is why the free workbooks on this
site avoid these functions in cells.</p>
<h2>Do not leave room by guessing</h2>
<p>The instinct is to keep a big empty area below a spilling formula. Better to put spilling formulas
in their own columns, with nothing to the right, and let them size themselves. The
<code>#</code> operator means nothing downstream needs to know how big they got.</p>""",
 faq=[
  ("What does #SPILL! mean?",
   "The formula returns more than one cell and something is in the way of where it needs to write. Excel refuses rather than overwriting your data."),
  ("The cells look empty. Why is it still blocked?",
   "Almost always a space or an invisible character in one of them, which is not the same as blank. Select the whole range and press Delete."),
  ("Why does it happen inside a table?",
   "Excel tables give each row its own copy of a formula, which is incompatible with one formula filling many rows. Move the formula outside the table."),
  ("What does the # after a cell reference do?",
   "It refers to the entire spilled result. D2# means everything D2 spilled, however large it is today, so the reference resizes itself."),
  ("Which versions support this?",
   "Microsoft 365 and Excel 2021 onwards. Excel 2019 and earlier show #NAME?, and there is no compatibility mode."),
  ("Does Google Sheets have spilling?",
   "Yes, and it has had it far longer, through ARRAYFORMULA and natively in many functions."),
 ],
 related=[("excel-filter-function", "FILTER, and the zero-for-blanks trap"),
          ("excel-apply-formula-entire-column", "Applying a formula to a whole column"),
          ("excel-sort-sortby", "Sorting with a formula")],
),

dict(
 slug="excel-filter-function",
 title="Excel FILTER Function: Rows That Match, in One Formula",
 description="FILTER returns every matching row as a live list. Why it shows 0 for blank cells, what #CALC! means, and how to filter on more than one condition.",
 h1="I want every row that matches, not just the first",
 lead="A lookup gives you one answer. <code>FILTER</code> gives you all of them, as a list that updates itself &mdash; and then shows a column of zeros where your data had blanks, which is where most people stop.",
 category=ARR, group=G_ARR,
 card_title="FILTER: every matching row",
 card_blurb="A live list of everything that matches, and the blank-becomes-zero trap.",
 chips=["Excel 365 / 2021", "AND / OR", "Excel + Google Sheets"],
 keywords=["excel filter function", "excel filter multiple criteria", "excel filter blank zero",
           "excel calc error", "excel filter formula", "excel return multiple matches"],
 short_answer="""<p><strong><code>=FILTER(range, condition, "none")</code> returns every row where
the condition is true.</strong> Combine conditions with <code>*</code> for AND and <code>+</code> for
OR &mdash; not the words. Always give the third argument, or an empty result shows
<code>#CALC!</code>. Blank cells in the source come back as <code>0</code>, because an empty cell is
zero to Excel; wrap the result in <code>IF(result="","",result)</code> if that matters.</p>""",
 problem_h="Two surprises, both worth knowing before you start",
 problem="""<p><strong>Blanks become zeros.</strong> <code>FILTER</code> returns cell values, and an
empty cell read as a value is <code>0</code>. So a filtered list of customers shows <code>0</code>
wherever the phone number was missing. Nothing is wrong; it is Excel's ordinary treatment of empty
cells, surfacing where you can finally see it.</p>
<p><strong><code>AND</code> and <code>OR</code> do not work here.</strong> Those functions collapse a
whole range into a single TRUE or FALSE, so <code>FILTER</code> receives one answer instead of one
per row and returns everything or nothing. You need <code>*</code> for AND and <code>+</code> for OR,
which multiply and add the TRUE/FALSE values row by row.</p>
<p>Neither is documented anywhere you will look at the moment you need it.</p>""",
 symptoms=symptom_table([
   ["Zeros where the source was blank",
    "An empty cell read as a value is 0",
    'Wrap in <code>IF(x="","",x)</code>'],
   ["<code>#CALC!</code>",
    "Nothing matched and there is no third argument",
    'Add <code>,"none found"</code>'],
   ["Every row returned",
    "<code>AND</code> collapsed the test to one TRUE",
    "Use <code>*</code> between conditions"],
   ["<code>#VALUE!</code>",
    "The condition is a different height from the range",
    "Make both the same number of rows"],
   ["<code>#NAME?</code>",
    "Your version does not have <code>FILTER</code>",
    "Use an advanced filter or a pivot table"],
 ]),
 howto_name="How to use FILTER",
 howto_desc="One condition, then several, then handle the empty result and the blanks.",
 steps=[
  dict(h="Start with one condition",
       plain="Give FILTER the range to return and a test that produces one TRUE or FALSE per row.",
       body="""<p>The range you want back, then the test:</p>""" +
       fx("Every order for one customer", '=FILTER(A2:D500,B2:B500="Acme Ltd","none found")',
          """<p>The third argument is what to show when nothing matches. Always include it. Without
it an empty result is <code>#CALC!</code>, which looks like a broken formula rather than a clean
answer of &ldquo;none&rdquo;.</p>""")),
  dict(h="Combine conditions with * and +",
       plain="Multiply conditions together for AND. Add them for OR. Do not use the AND and OR functions.",
       body="""<p>Multiplication is AND, addition is OR:</p>""" +
       fx("AND, then OR",
          '=FILTER(A2:D500,(B2:B500="Acme")*(C2:C500>1000),"none")\n'
          '=FILTER(A2:D500,(B2:B500="Acme")+(B2:B500="Northwind"),"none")',
          """<p>TRUE behaves as 1 and FALSE as 0, so multiplying gives 1 only when both hold, and
adding gives at least 1 when either does. Bracket each condition &mdash; without brackets the
operator precedence quietly changes what you asked for.</p>""")),
  dict(h="Turn the zeros back into blanks",
       plain="Wrap the whole FILTER in an IF that swaps empty strings back in, so missing values stay visibly missing.",
       body="""<p>If the zeros are misleading &mdash; a phone number of 0 is worse than no phone
number &mdash; swap them back:</p>""" +
       fx("Keep blanks blank", '=LET(r,FILTER(A2:D500,B2:B500="Acme","none"),IF(r="","",r))',
          """<p><code>LET</code> names the result so <code>FILTER</code> runs once rather than twice.
Without <code>LET</code> you would write the whole formula twice and it would do the work twice.</p>""")),
  dict(h="Sort the result while you are at it",
       plain="Wrap the FILTER in SORT to control the order, with a column number and 1 for ascending or -1 for descending.",
       body="""<p><code>FILTER</code> returns rows in their original order. Wrap it to change
that:</p>""" +
       fx("Filtered and sorted", '=SORT(FILTER(A2:D500,B2:B500="Acme","none"),3,-1)',
          """<p>Sort by the third column, descending. The two functions compose in either order but
this way round reads more naturally: filter first, then sort what is left.</p>""")),
 ],
 body="""<h2>Filtering by a cell instead of typed text</h2>
<p>Point the condition at a cell and the list becomes interactive &mdash; type a different customer
in <code>G1</code> and the results change:</p>
""" + fx("Driven by a cell", '=FILTER(A2:D500,B2:B500=G1,"no orders for that customer")',
"""<p>Add a dropdown on <code>G1</code> with <em>Data &rarr; Data Validation</em> and you have built
a small search tool with one formula and no code.</p>""") + """
<h2>Filtering on a partial match</h2>
<p><code>FILTER</code> tests for equality, so it will not do &ldquo;contains&rdquo; on its own. Pair
it with <code>SEARCH</code>:</p>
""" + fx("Rows containing a word",
'=FILTER(A2:D500,ISNUMBER(SEARCH("ltd",B2:B500)),"none")',
"""<p><code>SEARCH</code> returns a position or an error, and <code>ISNUMBER</code> turns that into
the TRUE/FALSE per row that <code>FILTER</code> needs. <code>SEARCH</code> ignores capitals;
<code>FIND</code> does not.</p>""") + """
<h2>What to do without FILTER</h2>
<p>On Excel 2019 or earlier, the honest answers are <em>Data &rarr; Advanced Filter</em>, which copies
matching rows somewhere else, or a pivot table. The array formulas that simulate
<code>FILTER</code> are long, slow and hard for the next person to maintain.</p>
<h2>Google Sheets</h2>
<p>Sheets has <code>FILTER</code> and has had it far longer. The differences are worth knowing: it
takes no third argument, so an empty result is <code>#N/A</code> and you wrap it in
<code>IFERROR</code>; and it accepts multiple conditions as extra arguments rather than needing
<code>*</code>.</p>""",
 faq=[
  ("Why does FILTER return 0 for blank cells?",
   "An empty cell read as a value is zero to Excel. Wrap the result in IF(result=\"\",\"\",result) to keep blanks looking blank."),
  ("What does #CALC! mean?",
   "Nothing matched and you did not supply the third argument. Add something like \"none found\" and an empty result becomes readable instead of an error."),
  ("Why does AND not work inside FILTER?",
   "AND collapses a whole range into a single TRUE or FALSE, so FILTER gets one answer rather than one per row. Multiply conditions with * for AND and add them with + for OR."),
  ("How do I filter on 'contains' rather than an exact match?",
   "Use ISNUMBER(SEARCH(\"word\",range)) as the condition. SEARCH ignores capitals; FIND does not."),
  ("What can I use instead on older Excel?",
   "Data > Advanced Filter, which copies matching rows elsewhere, or a pivot table. The array formulas that imitate FILTER are slow and hard to maintain."),
  ("Is Google Sheets FILTER the same?",
   "Close but not identical. Sheets takes no third argument, so wrap it in IFERROR, and it accepts several conditions as extra arguments rather than needing *."),
 ],
 related=[("excel-spill-error", "What #SPILL! means"),
          ("excel-sort-sortby", "Sorting with a formula"),
          ("excel-compare-two-lists", "Find what is in list A but not list B")],
),

dict(
 slug="excel-sort-sortby",
 title="Sort With a Formula in Excel: SORT and SORTBY",
 description="SORT and SORTBY produce a sorted copy that updates itself, without touching your data. When to use each, and how to sort by a column you do not show.",
 h1="I want a sorted list that stays sorted",
 lead="Sorting from the ribbon rearranges your actual data and has to be redone every time a row is added. A formula makes a sorted copy that re-sorts itself and leaves the original alone.",
 category=ARR, group=G_ARR,
 card_title="SORT and SORTBY",
 card_blurb="A sorted copy that updates itself, without rearranging your data.",
 chips=["Excel 365 / 2021", "Live results", "Excel + Google Sheets"],
 keywords=["excel sort function", "excel sortby", "excel sort formula", "excel dynamic sort",
           "excel sort without changing data", "excel top 10 formula"],
 short_answer="""<p><strong><code>=SORT(range, column, order)</code> returns a sorted copy;
<code>=SORTBY(range, by_range, order)</code> sorts by something that need not be in the
result.</strong> Order is <code>1</code> for ascending and <code>-1</code> for descending. Both leave
your data exactly where it is and re-sort on their own when it changes, which ribbon sorting cannot
do.</p>""",
 problem_h="Why sorting from the ribbon causes trouble",
 problem="""<p>Ribbon sorting physically rearranges rows. Three consequences follow, and all of them
bite eventually:</p>
<ul>
<li><strong>It has to be repeated.</strong> A row added tomorrow sits at the bottom until someone
sorts again.</li>
<li><strong>It can be done wrong.</strong> Selecting one column and sorting it alone, without
extending the selection, detaches that column from its rows. Excel warns, the warning gets dismissed,
and the data is now silently scrambled.</li>
<li><strong>The original order is gone.</strong> Unless there was a column recording it, entry order
cannot be recovered.</li>
</ul>
<p>A formula avoids all three. It produces a <em>copy</em>, in order, that keeps itself current.</p>""",
 symptoms=symptom_table([
   ["New rows sit at the bottom",
    "Ribbon sorting is a one-off action",
    "Use <code>SORT</code> for a live copy"],
   ["Columns no longer line up",
    "One column was sorted without the others",
    "Undo immediately; use a formula instead"],
   ["Cannot get the original order back",
    "Nothing recorded it",
    "Keep an entry-order column"],
   ["Want the top 10 only",
    "<code>SORT</code> returns everything",
    "Wrap it in <code>TAKE</code>, or use <code>LARGE</code>"],
   ["Sorted by text, not by value",
    "The column is numbers stored as text",
    "Convert it to numbers first"],
 ]),
 howto_name="How to sort with a formula",
 howto_desc="A sorted copy, then sorting by a hidden column, then a top-N list.",
 steps=[
  dict(h="Sort a range by one of its columns",
       plain="Give SORT the range, the column number to sort on, and 1 for ascending or -1 for descending.",
       body="""<p>Column number counts from the left of the range you gave it, not from column A of
the sheet:</p>""" +
       fx("Biggest first", '=SORT(A2:D500,4,-1)',
          """<p>Sort by the fourth column, descending. The result spills, so put it where there is
room.</p>""")),
  dict(h="Sort by something you do not want to show",
       plain="SORTBY takes the range to return and, separately, the range to sort on — so you can order by a date you are not displaying.",
       body="""<p>This is the difference between the two functions:</p>""" +
       fx("Order by a column you do not return",
          '=SORTBY(A2:B500,D2:D500,-1)',
          """<p>Return columns A and B, ordered by column D. <code>SORT</code> cannot do this because
its column number has to be inside the range it returns.</p>""")),
  dict(h="Sort by two things at once",
       plain="SORTBY accepts pairs: sort by region ascending, then by value descending.",
       body="""<p>Add more pairs of range and order:</p>""" +
       fx("Region, then value", '=SORTBY(A2:D500,B2:B500,1,D2:D500,-1)',
          """<p>Region A to Z, and inside each region the largest value first. Read left to right:
the first pair is the outer order.</p>""")),
  dict(h="Take just the top few",
       plain="Wrap a descending sort in TAKE to return only the first rows.",
       body="""<p>A live top-10 in one formula:</p>""" +
       fx("Top 10", '=TAKE(SORT(A2:D500,4,-1),10)',
          """<p><code>TAKE</code> needs Microsoft 365. On Excel 2021, <code>INDEX</code> with
<code>SEQUENCE</code> does the same: <code>=INDEX(SORT(A2:D500,4,-1),SEQUENCE(10),{1,2,3,4})</code>.</p>""")),
 ],
 body="""<h2>Blank rows sort to the bottom as zeros</h2>
<p>A range that includes empty rows below your data returns those rows too, as zeros and blanks. Bound
the range to the rows you actually have, or filter first:</p>
""" + fx("Drop the empties before sorting",
'=SORT(FILTER(A2:D500,A2:A500<>"","none"),4,-1)',
"""<p><code>FILTER</code> removes the empty rows, then <code>SORT</code> orders what is left.</p>""") + """
<h2>Keep an entry-order column</h2>
<p>Even with formula sorting, a plain incrementing number beside your data is worth having. It is the
only way back to the order things were entered, and it costs one column.</p>
<h2>Sorting text with numbers in it</h2>
<p><code>Item 10</code> sorts before <code>Item 9</code>, because text sorts character by character
and <code>1</code> comes before <code>9</code>. This is not a bug and there is no setting for it. The
fixes are to pad the numbers (<code>Item 09</code>) or to split the number into its own column and
sort on that.</p>
<h2>Google Sheets</h2>
<p>Sheets has both functions. <code>SORT</code> takes the same arguments; <code>SORTBY</code> is
spelled <code>SORTN</code> for the top-N case and behaves slightly differently, so check the arguments
rather than assuming.</p>""",
 faq=[
  ("What is the difference between SORT and SORTBY?",
   "SORT orders a range by one of its own columns. SORTBY orders it by a separate range, so you can sort by a column you are not displaying."),
  ("Does sorting with a formula change my data?",
   "No. It produces a sorted copy elsewhere and leaves the original untouched, which is the main reason to prefer it."),
  ("How do I sort by two columns?",
   "Use SORTBY with more pairs: =SORTBY(range, first, 1, second, -1). The first pair is the outer order."),
  ("How do I get just the top 10?",
   "Wrap a descending sort in TAKE. On Excel 2021 without TAKE, use INDEX with SEQUENCE."),
  ("Why does Item 10 sort before Item 9?",
   "Text sorts character by character, and 1 comes before 9. Pad the numbers, or split the number into its own column and sort on that."),
  ("Why do I get rows of zeros at the bottom?",
   "The range includes empty rows below your data. Bound the range, or wrap it in FILTER to drop the blanks before sorting."),
 ],
 related=[("excel-filter-function", "FILTER: every matching row"),
          ("excel-spill-error", "What #SPILL! means"),
          ("excel-unique-values-list", "Getting a list of unique values")],
),

dict(
 slug="excel-lambda-named-functions",
 title="Write Your Own Excel Function With LAMBDA — No VBA",
 description="LAMBDA turns a formula you keep repeating into a named function you can call like any built-in — no macros, and the file stays a plain .xlsx.",
 h1="I keep pasting the same monster formula everywhere",
 lead="The same forty-character formula, copied into six workbooks, each copy slightly different by now. <code>LAMBDA</code> lets you name it once and call it like <code>SUM</code> &mdash; and the file stays an ordinary .xlsx with no macros in it.",
 category=ARR, group=G_ARR,
 card_title="Your own function, no VBA",
 card_blurb="Name a formula once and call it like a built-in. No macros, still a plain .xlsx.",
 chips=["Excel 365", "No macros", "Excel + Google Sheets"],
 keywords=["excel lambda function", "excel custom function no vba", "excel named function",
           "excel lambda tutorial", "google sheets named function", "excel reusable formula"],
 short_answer="""<p><strong>Write <code>=LAMBDA(a, b, &lt;your formula&gt;)(test1, test2)</code> in a
cell to prove it works, then put the <code>LAMBDA</code> part in Name Manager under a name.</strong>
It becomes callable everywhere in that workbook. Because it is a formula rather than a macro, the file
stays <code>.xlsx</code> and nothing has to be enabled to open it &mdash; which is the main advantage
over VBA.</p>""",
 problem_h="Why this is better than the alternatives",
 problem="""<p>There have only ever been two ways to reuse a calculation, and both have real costs.</p>
<p><strong>Copy the formula.</strong> Free, and it drifts. Six copies become six slightly different
formulas, and when the rule changes you must find all of them. The one you miss is the one that is
wrong.</p>
<p><strong>Write a VBA function.</strong> Powerful, and it turns the file into <code>.xlsm</code>.
Now it triggers security warnings, may be blocked outright by an employer, and cannot be opened
properly in Google Sheets or on the web.</p>
<p><code>LAMBDA</code> has neither problem. The logic lives in one place, and the file is still an
ordinary spreadsheet.</p>""",
 symptoms=symptom_table([
   ["The same long formula in many places",
    "No way to name it, until now",
    "Make it a <code>LAMBDA</code>"],
   ["Copies have drifted apart",
    "Each was edited separately",
    "One definition, called everywhere"],
   ["Blocked because the file is .xlsm",
    "A VBA function forced the format",
    "<code>LAMBDA</code> keeps it .xlsx"],
   ["<code>#NAME?</code> when calling it",
    "The name is not defined in this workbook",
    "Names are per workbook &mdash; define it there too"],
   ["<code>#VALUE!</code> from the function",
    "Arguments given in the wrong order",
    "Order follows the <code>LAMBDA</code> definition"],
 ]),
 howto_name="How to make your own function with LAMBDA",
 howto_desc="Prove it in a cell, name it, then call it like anything built in.",
 steps=[
  dict(h="Get the formula working normally first",
       plain="Write the calculation with ordinary cell references until it gives the right answer. Do not start with LAMBDA.",
       body="""<p>Write it the usual way, pointing at real cells, and check the answer. Debugging a
formula and learning <code>LAMBDA</code> at the same time is twice as hard as doing them in
order.</p>""" +
       fx("An ordinary formula first", '=(B2-C2)/C2',
          """<p>A percentage change. Simple on purpose &mdash; the mechanics are the same whatever the
formula does.</p>""")),
  dict(h="Wrap it in LAMBDA and test it in place",
       plain="List the inputs as names, replace the cell references with those names, and add a second set of brackets holding test values.",
       body="""<p>The trailing brackets are a trick worth knowing: they call the function
immediately, so you can see the answer before naming anything.</p>""" +
       fx("Test before naming", '=LAMBDA(new,old,(new-old)/old)(120,100)',
          """<p>Returns 0.2. If that works, the definition is right. If it errors, fix it here
&mdash; a broken definition inside Name Manager gives you almost no feedback.</p>""")),
  dict(h="Give it a name",
       plain="Copy the LAMBDA part without the test brackets. Open Formulas > Name Manager > New, type a name, and paste it into Refers to.",
       body="""<p>Copy <code>=LAMBDA(new,old,(new-old)/old)</code> &mdash; without the test values
&mdash; then <em>Formulas &rarr; Name Manager &rarr; New</em>. Name it <code>PctChange</code> and
paste into <em>Refers to</em>.</p>
<p>Use the Comment box. It is what appears as a tooltip when someone types your function, and it is
the only documentation it will ever have.</p>"""),
  dict(h="Call it like any other function",
       plain="Type the name followed by its arguments in brackets. It autocompletes like a built-in.",
       body="""<p>It behaves exactly like a built-in from here:</p>""" +
       fx("Using it", '=PctChange(B2,C2)',
          """<p>Change the definition once in Name Manager and every use updates. That is the whole
point.</p>""")),
 ],
 body="""<h2>Names are per workbook</h2>
<p>A <code>LAMBDA</code> lives in the workbook that defines it. Send a sheet that uses it to someone
else without the definition and they get <code>#NAME?</code>.</p>
<p>Two ways round it: keep a template workbook holding your functions and start new files from it, or
copy a sheet from the source workbook into the target, which brings the names with it and can then be
deleted.</p>
<h2>LAMBDA plus BYROW is where it gets useful</h2>
<p>The helper functions take a <code>LAMBDA</code> as an argument, which is what makes them work:</p>
""" + fx("Apply a calculation to every row", '=BYROW(A2:C100,LAMBDA(row,MAX(row)-MIN(row)))',
"""<p>The spread of each row, in one formula. Without <code>LAMBDA</code> there would be no way to
tell <code>BYROW</code> what to do to each row.</p>""") + """
<h2>Keep them short</h2>
<p>A <code>LAMBDA</code> can be enormous. It should not be. Long ones are unreadable and undebuggable,
because there is no step-through and no error line. Build small named pieces and call one from
another &mdash; that composes, and each part can be tested on its own.</p>
<h2>Availability</h2>
<p><code>LAMBDA</code> needs Microsoft 365. It is not in Excel 2021 or 2019, and not in LibreOffice.
Google Sheets has the same idea as <em>Named Functions</em> under the Data menu, with a friendlier
dialog, and it can import them from another sheet &mdash; which Excel cannot.</p>""",
 faq=[
  ("What is LAMBDA in Excel?",
   "It lets you turn a formula into a named function you can call like SUM. The logic lives in one place instead of being copied, and the file stays a plain .xlsx."),
  ("Is this the same as a VBA function?",
   "No, and that is the advantage. LAMBDA is a formula, so the file stays .xlsx, opens without security warnings and is not blocked by employers who disable macros."),
  ("How do I test a LAMBDA before naming it?",
   "Add a second set of brackets with test values: =LAMBDA(a,b,a+b)(2,3). It calls itself immediately so you can see the answer."),
  ("Why do I get #NAME? when someone else opens my file?",
   "Names are stored per workbook. If the definition is not in their file, the function does not exist there. Keep a template workbook, or copy a sheet across to carry the names."),
  ("Which versions have LAMBDA?",
   "Microsoft 365 only. It is not in Excel 2021 or 2019, nor in LibreOffice. Google Sheets has the same idea as Named Functions."),
  ("Can a LAMBDA call another LAMBDA?",
   "Yes, and it is the right way to work. Build small named pieces and compose them rather than writing one enormous definition that cannot be debugged."),
 ],
 related=[("excel-byrow-bycol", "Doing something to every row"),
          ("excel-spill-error", "What #SPILL! means"),
          ("excel-absolute-relative-references", "The $ sign and why dragging breaks formulas")],
),

dict(
 slug="excel-byrow-bycol",
 title="BYROW and BYCOL: One Answer Per Row in Excel",
 description="BYROW runs a calculation across each row and returns one answer per row, replacing a helper column filled down — and it resizes itself.",
 h1="I want one number per row, without a helper column",
 lead="A helper column works. It also has to be filled down, kept in step with new rows, and explained to whoever inherits the file. <code>BYROW</code> does the same job from one cell.",
 category=ARR, group=G_ARR,
 card_title="BYROW and BYCOL",
 card_blurb="One answer per row from a single formula, instead of a helper column filled down.",
 chips=["Excel 365", "With LAMBDA", "Excel"],
 keywords=["excel byrow", "excel bycol", "excel lambda helper", "excel row calculation",
           "excel array per row", "excel replace helper column"],
 short_answer="""<p><strong><code>=BYROW(range, LAMBDA(row, calculation))</code> runs your
calculation on each row and returns a single column of answers.</strong> <code>BYCOL</code> does the
same across columns. The result spills and resizes itself, so rows added later are included without
anyone filling anything down. Both need Microsoft 365, because both take a <code>LAMBDA</code>.</p>""",
 problem_h="What is wrong with a helper column",
 problem="""<p>Usually nothing. It is clear, it is easy to debug, and everyone understands it. Reach
for <code>BYROW</code> when one of these bites:</p>
<ul>
<li><strong>It stops part way down.</strong> Somebody added rows and did not fill the formula, so the
last forty rows are blank and the total is quietly wrong.</li>
<li><strong>It has to be a single value.</strong> A formula that needs one number per row inside a
larger calculation cannot use a column that lives somewhere else.</li>
<li><strong>There is nowhere to put it.</strong> A protected sheet, or a layout that has no free
column.</li>
</ul>
<p>Where none of those apply, a helper column is still a perfectly good answer, and often the kinder
one for whoever maintains the file next.</p>""",
 symptoms=symptom_table([
   ["Helper column stops part way",
    "Nobody filled it down after adding rows",
    "<code>BYROW</code> resizes itself"],
   ["<code>MAX</code> across a row of a range fails",
    "Most functions take the whole range, not per row",
    "<code>BYROW</code> hands them one row at a time"],
   ["<code>#CALC!</code> from <code>BYROW</code>",
    "The <code>LAMBDA</code> returned more than one value",
    "It must return exactly one per row"],
   ["<code>#NAME?</code>",
    "Not available in your version",
    "Use a helper column"],
   ["Slow on a large range",
    "The <code>LAMBDA</code> runs once per row",
    "Keep the calculation simple, or bound the range"],
 ]),
 howto_name="How to use BYROW",
 howto_desc="Give it a range and a LAMBDA that turns one row into one answer.",
 steps=[
  dict(h="Write the calculation for a single row first",
       plain="Work out what you want using one row's cells, and check the answer before generalising it.",
       body="""<p>Prove the logic on row 2 with ordinary references. If you cannot get one row right,
wrapping it in <code>BYROW</code> will not help.</p>"""),
  dict(h="Wrap it in BYROW with a LAMBDA",
       plain="Pass the range, then a LAMBDA that names the row and does the calculation on it.",
       body="""<p>The <code>LAMBDA</code> receives one row at a time, as a small range:</p>""" +
       fx("Spread of each row", '=BYROW(A2:C100,LAMBDA(row,MAX(row)-MIN(row)))',
          """<p>You choose the name <code>row</code>; it stands for whichever row is being handled.
The result is one column, as tall as the range.</p>""")),
  dict(h="Make sure it returns exactly one value per row",
       plain="The LAMBDA must produce a single value. Returning a range gives #CALC!.",
       body="""<p><code>BYROW</code> builds a single column of answers, so each call must give it
exactly one value. A <code>LAMBDA</code> returning a range produces <code>#CALC!</code>.</p>
<p>Wrap anything that might return several in something that reduces it &mdash;
<code>SUM</code>, <code>MAX</code>, <code>TEXTJOIN</code>, <code>COUNT</code>.</p>"""),
  dict(h="Use BYCOL the same way, across columns",
       plain="BYCOL hands your LAMBDA one column at a time and returns a single row of answers.",
       body="""<p>Same shape, other axis:</p>""" +
       fx("Column totals", '=BYCOL(A2:C100,LAMBDA(col,SUM(col)))',
          """<p>Returns one row with a total per column. Useful under a block where the number of
columns changes.</p>""")),
 ],
 body="""<h2>Where it beats a helper column properly</h2>
<p>Counting how many cells in each row exceed a threshold is awkward as a helper column and clear
here:</p>
""" + fx("Cells above target, per row",
'=BYROW(B2:M100,LAMBDA(r,SUM(--(r>100))))',
"""<p>The double minus turns TRUE and FALSE into 1 and 0 so <code>SUM</code> can add them. It reads
oddly and it is the standard way to count conditions inside an array.</p>""") + """
<h2>The functions that take a LAMBDA</h2>
<ul>
<li><code>BYROW</code>, <code>BYCOL</code> &mdash; one answer per row or column</li>
<li><code>MAP</code> &mdash; one answer per <em>cell</em></li>
<li><code>SCAN</code> &mdash; a running total, keeping what came before</li>
<li><code>REDUCE</code> &mdash; the whole range down to one value</li>
<li><code>MAKEARRAY</code> &mdash; builds a block from scratch by position</li>
</ul>
<p><code>SCAN</code> is the one worth knowing after <code>BYROW</code>: a running balance without
filling a formula down.</p>
<h2>When not to use it</h2>
<p>If the per-row number is something people need to <em>see</em>, put it in a column where they can
see it. <code>BYROW</code> is best where the number is an intermediate step. A workbook that hides
every intermediate value inside one clever formula is harder to check, and being checkable is usually
worth more than being clever.</p>""",
 faq=[
  ("What does BYROW do?",
   "It runs a calculation on each row of a range and returns one answer per row, as a single spilled column, replacing a helper column filled down."),
  ("Why do I get #CALC! from BYROW?",
   "The LAMBDA returned more than one value for a row. Each call must produce exactly one — wrap it in SUM, MAX, COUNT or TEXTJOIN."),
  ("Is BYROW better than a helper column?",
   "Not always. Use it when the helper column keeps getting out of step with new rows, when the value must be a single expression, or when there is no free column. Otherwise a helper column is easier for the next person to check."),
  ("What is the difference between BYROW and MAP?",
   "BYROW hands your LAMBDA a whole row at a time. MAP hands it one cell at a time and returns an answer per cell."),
  ("Which versions have these?",
   "Microsoft 365 only. They take a LAMBDA, which does not exist in Excel 2021, 2019 or LibreOffice."),
  ("How do I do a running total?",
   "SCAN is the function for that — it keeps the value so far as it moves through the range, giving a running balance without filling a formula down."),
 ],
 related=[("excel-lambda-named-functions", "Write your own function with LAMBDA"),
          ("excel-spill-error", "What #SPILL! means"),
          ("excel-apply-formula-entire-column", "Applying a formula to a whole column")],
),

dict(
 slug="excel-regex-functions",
 title="Regex in Excel: REGEXTEST, REGEXEXTRACT and REGEXREPLACE",
 description="Excel finally has regular expressions built in. What the three functions do, the patterns worth knowing, and what to use if your version lacks them.",
 h1="Pulling a code out of messy text without a macro",
 lead="For twenty years the answer to &ldquo;can Excel do regular expressions?&rdquo; was &ldquo;only with VBA&rdquo;. That changed: Excel now has three regex functions built in, and most of the advice you will find online was written before they existed.",
 category=TXT, group=G_TXT,
 card_title="Regex, built into Excel at last",
 card_blurb="Three functions that replace the macro everyone used to need.",
 chips=["Excel 365", "Also in Sheets", "Excel + Google Sheets"],
 keywords=["excel regex", "excel regextest", "excel regexextract", "excel regexreplace",
           "excel regular expressions", "excel extract pattern from text"],
 short_answer="""<p><strong>Excel 365 has <code>REGEXTEST</code> (does it match?),
<code>REGEXEXTRACT</code> (give me the matching part) and <code>REGEXREPLACE</code> (swap it for
something else).</strong> They were added in 2024, so almost everything written about regex in Excel
predates them and tells you to use VBA. Google Sheets has had <code>REGEXMATCH</code>,
<code>REGEXEXTRACT</code> and <code>REGEXREPLACE</code> for years.</p>""",
 problem_h="What a regular expression is, in one paragraph",
 problem="""<p>A regular expression is a small pattern language for describing the <em>shape</em> of
text rather than the text itself. <code>\\d</code> means any digit; <code>\\d{5}</code> means five
digits in a row; <code>[A-Z]{2}</code> means two capital letters.</p>
<p>That is the whole idea. Instead of &ldquo;find the text ABC-1234&rdquo; you say &ldquo;find three
capitals, a hyphen, then four digits&rdquo;, and it finds every code shaped like that regardless of
what the letters and numbers are.</p>
<p>It is genuinely hard to read and enormously useful. The trick is to build patterns from a few
pieces you know rather than trying to understand somebody's forty-character expression from the
internet.</p>""",
 symptoms=symptom_table([
   ["Nested <code>SUBSTITUTE</code> forty deep",
    "Trying to describe a pattern with exact matches",
    "One <code>REGEXREPLACE</code>"],
   ["<code>#NAME?</code> from <code>REGEXEXTRACT</code>",
    "Your version does not have it",
    "Use Power Query or the older text functions"],
   ["<code>#N/A</code> from <code>REGEXEXTRACT</code>",
    "The pattern matched nothing",
    "Wrap in <code>IFERROR</code>; test with <code>REGEXTEST</code> first"],
   ["Matches the wrong part",
    "The pattern is greedy by default",
    "Add <code>?</code> to make it lazy"],
   ["Works on one row, not another",
    "The other row has a slightly different shape",
    "Loosen the pattern, or handle both"],
 ]),
 howto_name="How to use regex in Excel",
 howto_desc="Test the pattern first, then extract or replace, and handle the rows that do not match.",
 steps=[
  dict(h="Check the pattern matches, with REGEXTEST",
       plain="REGEXTEST returns TRUE or FALSE. Use it to check the pattern before you build anything on it.",
       body="""<p>Start here rather than with extraction, so a wrong answer is obviously a wrong
pattern:</p>""" +
       fx("Does this look like a product code?", '=REGEXTEST(A2,"[A-Z]{3}-\\d{4}")',
          """<p>TRUE where the cell contains three capitals, a hyphen and four digits. Add it as a
column and scan it before going further.</p>""")),
  dict(h="Pull the piece out with REGEXEXTRACT",
       plain="REGEXEXTRACT returns the part of the text that matched, and #N/A when nothing did.",
       body="""<p>Same pattern, now returning the match:</p>""" +
       fx("Get the code itself",
          '=IFERROR(REGEXEXTRACT(A2,"[A-Z]{3}-\\d{4}"),"no code found")',
          """<p>Always wrap it. Without <code>IFERROR</code> every non-matching row is
<code>#N/A</code>, and one <code>#N/A</code> breaks any total built on the column.</p>""")),
  dict(h="Clean text with REGEXREPLACE",
       plain="REGEXREPLACE swaps everything matching the pattern for something else — the fastest way to strip unwanted characters.",
       body="""<p>This replaces the tower of nested <code>SUBSTITUTE</code> calls:</p>""" +
       fx("Digits only", '=REGEXREPLACE(A2,"[^0-9]","")',
          """<p><code>[^0-9]</code> means &ldquo;any character that is not a digit&rdquo;. Replacing
them all with nothing leaves the digits. Turning a phone number into digits becomes one short
formula.</p>""")),
  dict(h="Learn six pieces and build from them",
       plain="Digits, letters, any character, one or more, exactly n, and start and end anchors will cover nearly everything you need.",
       body="""<p>These six carry most real work:</p>
<ul>
<li><code>\\d</code> a digit &nbsp;&middot;&nbsp; <code>[A-Z]</code> a capital letter</li>
<li><code>.</code> any character &nbsp;&middot;&nbsp; <code>+</code> one or more of the last thing</li>
<li><code>{3}</code> exactly three &nbsp;&middot;&nbsp; <code>{2,5}</code> between two and five</li>
<li><code>^</code> start of the text &nbsp;&middot;&nbsp; <code>$</code> end of it</li>
<li><code>[^…]</code> anything <em>except</em> these &nbsp;&middot;&nbsp; <code>|</code> either side</li>
</ul>
<p><code>^\\d{5}$</code> means the whole cell is exactly five digits &mdash; a postcode check in nine
characters.</p>"""),
 ],
 body="""<h2>Patterns worth keeping</h2>
<ul>
<li><strong>Digits only:</strong> <code>[^0-9]</code> replaced with nothing</li>
<li><strong>An email:</strong> <code>[\\w.+-]+@[\\w-]+\\.[\\w.]+</code></li>
<li><strong>Anything in brackets:</strong> <code>\\(([^)]+)\\)</code></li>
<li><strong>Trailing whitespace:</strong> <code>\\s+$</code> replaced with nothing</li>
<li><strong>Repeated spaces:</strong> <code>\\s{2,}</code> replaced with one space</li>
<li><strong>Last word:</strong> <code>\\S+$</code></li>
</ul>
<h2>Greedy and lazy</h2>
<p>A pattern takes as much as it can by default. On <code>(a) and (b)</code> the pattern
<code>\\(.+\\)</code> matches <code>(a) and (b)</code> in one go, because <code>.+</code> happily
swallows the middle. Adding <code>?</code> makes it stop at the first opportunity:
<code>\\(.+?\\)</code> gives you <code>(a)</code>.</p>
<p>This single character explains most &ldquo;why did it match too much&rdquo; confusion.</p>
<h2>If your Excel does not have these</h2>
<p>Three real options, in order of preference:</p>
<ol>
<li><strong>Power Query</strong> &mdash; the splitting and extracting tools cover most cases without
regex at all, and they run on any recent Excel.</li>
<li><strong>The older text functions</strong> &mdash; <code>LEFT</code>, <code>MID</code>,
<code>FIND</code>, <code>SUBSTITUTE</code>. Longer, but they work everywhere.</li>
<li><strong>VBA</strong> &mdash; what everyone used before 2024. It makes the file <code>.xlsm</code>,
which may be blocked where you work.</li>
</ol>
<h2>Google Sheets got there first</h2>
<p>Sheets has had <code>REGEXMATCH</code>, <code>REGEXEXTRACT</code> and <code>REGEXREPLACE</code>
for years. The names differ slightly &mdash; <code>REGEXMATCH</code> rather than
<code>REGEXTEST</code> &mdash; and the pattern syntax is the same in almost all everyday use.</p>""",
 faq=[
  ("Does Excel support regular expressions?",
   "Yes. Excel 365 added REGEXTEST, REGEXEXTRACT and REGEXREPLACE in 2024. Before that it needed VBA, which is why most advice online still says so."),
  ("What is the difference between the three functions?",
   "REGEXTEST returns TRUE or FALSE. REGEXEXTRACT returns the matching part of the text. REGEXREPLACE swaps everything matching for something else."),
  ("Why does REGEXEXTRACT return #N/A?",
   "The pattern matched nothing in that cell. Wrap it in IFERROR, and check the pattern with REGEXTEST first."),
  ("Why does my pattern match too much?",
   "Patterns are greedy — they take as much as they can. Add a question mark after the quantifier, as in .+? , to make it stop at the first opportunity."),
  ("What can I use if my Excel does not have them?",
   "Power Query's split and extract tools cover most cases and run on any recent Excel. Otherwise LEFT, MID, FIND and SUBSTITUTE, or VBA as a last resort."),
  ("Does Google Sheets have regex?",
   "Yes, and for much longer. The functions are REGEXMATCH, REGEXEXTRACT and REGEXREPLACE, with essentially the same pattern syntax."),
 ],
 related=[("excel-extract-numbers-from-text", "Getting the numbers out of messy text"),
          ("excel-textsplit-functions", "Splitting text without Text to Columns"),
          ("excel-vlookup-non-breaking-space", "#N/A when the value is clearly there")],
),

dict(
 slug="excel-extract-numbers-from-text",
 title="Extract Numbers From Text in Excel — Every Method",
 description="Get the digits out of a mixed cell with REGEXREPLACE, Power Query, Flash Fill or nested SUBSTITUTE — whichever your Excel version actually supports.",
 h1="I need the number out of &ldquo;Order 4471 &mdash; urgent&rdquo;",
 lead="One column, numbers buried inside text, in a slightly different place on every row. There are four ways to do it and which one is right depends entirely on which Excel you have.",
 category=TXT, group=G_TXT,
 card_title="Getting numbers out of text",
 card_blurb="Four methods, from one-line regex to something that works in every version.",
 chips=["Any version", "Four methods", "Excel + Google Sheets"],
 keywords=["excel extract numbers from text", "excel get digits from string",
           "excel remove letters from cell", "excel flash fill numbers",
           "excel extract number formula", "excel split text and number"],
 short_answer="""<p><strong>On Excel 365, <code>=REGEXREPLACE(A2,"[^0-9]","")</code> strips every
non-digit and leaves the number.</strong> On older versions use Power Query's <em>Extract</em> tools,
or Flash Fill (<strong>Ctrl+E</strong>) for a one-off, or nested <code>SUBSTITUTE</code> calls if the
unwanted characters are predictable. The result is <em>text</em> in every case &mdash; wrap it in
<code>VALUE</code> if you need to do arithmetic on it.</p>""",
 problem_h="Why there is no single answer",
 problem="""<p>Because &ldquo;the number&rdquo; means different things in different files, and the
methods differ in what they assume.</p>
<ul>
<li><strong>All digits joined together.</strong> <code>Order 4471 line 3</code> becomes
<code>44713</code>. Usually not what you meant.</li>
<li><strong>The first run of digits.</strong> Gives <code>4471</code>. Usually right.</li>
<li><strong>A number in a fixed position.</strong> Simple, until one row is different.</li>
<li><strong>A decimal or a negative.</strong> Stripping non-digits also removes the point and the
minus sign, silently turning <code>-12.50</code> into <code>1250</code>.</li>
</ul>
<p>Decide which you actually want before picking the method. That last one is the expensive
mistake.</p>""",
 symptoms=symptom_table([
   ["All the digits ran together",
    "You stripped everything that was not a digit",
    "Extract the first run instead"],
   ["A decimal turned into a whole number",
    "The decimal point was stripped too",
    "Keep it: <code>[^0-9.]</code>"],
   ["A negative lost its sign",
    "The minus was stripped",
    "Keep it: <code>[^0-9.-]</code>"],
   ["Result will not add up",
    "It is text, not a number",
    "Wrap in <code>VALUE</code>"],
   ["Flash Fill guessed wrongly",
    "Not enough examples, or an inconsistent pattern",
    "Give it three or four examples"],
 ]),
 howto_name="How to extract numbers from text",
 howto_desc="Four methods; use the first one your version of Excel supports.",
 steps=[
  dict(h="Excel 365: one regex",
       plain="REGEXREPLACE with the pattern [^0-9] removes every character that is not a digit.",
       body="""<p>Shortest and clearest, if you have it:</p>""" +
       fx("Strip everything but digits",
          '=REGEXREPLACE(A2,"[^0-9]","")\n'
          '=IFERROR(REGEXEXTRACT(A2,"\\d+"),"")',
          """<p>The first joins every digit together. The second returns only the <em>first run</em>
of digits, which is usually the one you meant. Keep the decimal point and minus with
<code>[^0-9.-]</code>.</p>""")),
  dict(h="Any recent Excel: Power Query",
       plain="Load the column into Power Query and use Transform > Extract, or add a column that keeps only digits.",
       body="""<p><em>Data &rarr; From Table/Range</em>, then <em>Transform &rarr; Extract</em> for
text before, after or between delimiters. For digits specifically, <em>Add Column &rarr; Custom
Column</em> with <code>Text.Select([Column1],{"0".."9"})</code>.</p>
<p>The advantage over a formula: it re-runs on next month's file.</p>"""),
  dict(h="A one-off: Flash Fill",
       plain="Type the answer for the first two or three rows, then press Ctrl+E. Excel works out the pattern and fills the rest.",
       body="""<p>In the column beside your data, type what you want for the first two or three rows,
then press <strong>Ctrl+E</strong>. Excel infers the pattern and fills down.</p>
<p>It is genuinely impressive and it is a <em>one-off</em>: the result is static values, and adding
rows later does nothing. Check the output &mdash; it guesses, and on inconsistent data it guesses
wrong quietly.</p>"""),
  dict(h="Every version: nested SUBSTITUTE",
       plain="If the unwanted characters are predictable, remove them one at a time with nested SUBSTITUTE calls.",
       body="""<p>Ugly, universal, and reliable when the junk is a known set:</p>""" +
       fx("Strip known characters",
          '=VALUE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(A2,"Order ",""),"$",""),",",""))',
          """<p>Works in every version of Excel, in Sheets and in LibreOffice, which is why the free
workbooks on this site use this form rather than regex.</p>""")),
 ],
 body="""<h2>The result is text</h2>
<p>Every method here returns text, even when it looks like a number. It will be left-aligned, and
<code>SUM</code> will ignore it. Wrap it in <code>VALUE</code>, or use
<em>Data &rarr; Text to Columns &rarr; Finish</em> on the finished column to convert the lot.</p>
<h2>Keep the leading zeros if it is a code</h2>
<p>If what you are pulling out is a reference rather than a quantity &mdash; a SKU, an order number
&mdash; do <strong>not</strong> convert it to a number. That is what strips the leading zeros. Leave
it as text.</p>
<h2>Getting the text out instead</h2>
<p>Invert the pattern: <code>=REGEXREPLACE(A2,"[0-9]","")</code> removes the digits and leaves
everything else. Usually worth a <code>TRIM</code> afterwards, since removing digits tends to leave
double spaces behind.</p>
<h2>When the position is fixed</h2>
<p>If the number is always in the same place, the old functions are clearer than any pattern:
<code>=MID(A2,7,4)</code> takes four characters from position seven. Simple and readable &mdash; and
it breaks the day one row is different, so add a check that the result is numeric.</p>""",
 faq=[
  ("How do I extract only the numbers from a cell?",
   "On Excel 365 use =REGEXREPLACE(A2,\"[^0-9]\",\"\"). On older versions use Power Query, Flash Fill for a one-off, or nested SUBSTITUTE calls."),
  ("Why did my decimal point disappear?",
   "Stripping everything that is not a digit removes the point and the minus sign too. Use [^0-9.-] to keep both."),
  ("Why does the result not add up?",
   "Every method returns text, even when it looks like a number. Wrap it in VALUE, or run Text to Columns on the finished column."),
  ("What is Flash Fill and when should I use it?",
   "Type the answer for a few rows and press Ctrl+E, and Excel infers the pattern. It is excellent for a one-off, but the result is static and it guesses silently on inconsistent data."),
  ("How do I get the first number rather than all the digits joined?",
   "Use REGEXEXTRACT with the pattern \\d+ , which returns the first run of digits rather than concatenating every digit in the cell."),
  ("Should I convert an extracted order number to a number?",
   "No. If it is a reference rather than a quantity, leave it as text — converting it is what strips any leading zeros."),
 ],
 related=[("excel-regex-functions", "Regex in Excel"),
          ("excel-textsplit-functions", "Splitting text without Text to Columns"),
          ("excel-numbers-stored-as-text", "SUM is ignoring half my column")],
),

dict(
 slug="excel-textsplit-functions",
 title="Split Text in Excel With TEXTSPLIT, TEXTBEFORE and TEXTAFTER",
 description="Split a column with a formula that updates itself instead of Text to Columns, which is a one-off. Plus what to use on older versions.",
 h1="Splitting a column without doing it again next month",
 lead="Text to Columns works, and it is a one-off action on static data. <code>TEXTSPLIT</code> does the same thing as a formula, so next month's rows split themselves.",
 category=TXT, group=G_TXT,
 card_title="Splitting text with a formula",
 card_blurb="TEXTSPLIT, TEXTBEFORE and TEXTAFTER — and what to use if you do not have them.",
 chips=["Excel 365", "Live results", "Excel + Google Sheets"],
 keywords=["excel textsplit", "excel textbefore", "excel textafter", "excel split cell formula",
           "excel split text to columns", "excel separate first last name"],
 short_answer="""<p><strong><code>=TEXTSPLIT(A2,", ")</code> splits a cell across columns at each
separator, and the result updates when the cell changes.</strong> <code>TEXTBEFORE</code> and
<code>TEXTAFTER</code> take just one side, which is usually what you want for a first and last name.
All three need Microsoft 365; on older versions use <em>Text to Columns</em>, Power Query, or
<code>LEFT</code> with <code>FIND</code>.</p>""",
 problem_h="Text to Columns is an action, not a formula",
 problem="""<p><em>Data &rarr; Text to Columns</em> is excellent and it has one property people
forget: it happens <em>once</em>, to the cells that existed at the time.</p>
<p>Rows added afterwards are not split. Nothing warns you &mdash; the new rows just sit there
unsplit at the bottom, and whatever you built on the split columns quietly stops covering them.</p>
<p>It also overwrites whatever is to the right, without much of a warning, which has destroyed more
than one column of notes.</p>
<p>A formula has neither problem: it produces a copy, it updates, and it cannot overwrite anything
because Excel refuses to spill onto occupied cells.</p>""",
 symptoms=symptom_table([
   ["New rows are not split",
    "Text to Columns ran once, before they existed",
    "Use a formula instead"],
   ["It overwrote the column beside it",
    "Text to Columns writes rightwards",
    "Undo, insert empty columns, redo"],
   ["<code>#SPILL!</code> from <code>TEXTSPLIT</code>",
    "Something is in the way of the result",
    "Clear the cells to the right"],
   ["Names with a middle name break",
    "More separators than expected",
    "Use <code>TEXTBEFORE</code> and <code>TEXTAFTER</code>"],
   ["<code>#NAME?</code>",
    "Not available in your version",
    "Power Query, or <code>LEFT</code> with <code>FIND</code>"],
 ]),
 howto_name="How to split text with a formula",
 howto_desc="Split across columns, or take one side, and handle the rows that do not fit the pattern.",
 steps=[
  dict(h="Split across columns with TEXTSPLIT",
       plain="Give it the cell and the separator. The result spills across as many columns as it needs.",
       body="""<p>The separator is text, so a comma and a space is <code>", "</code>:</p>""" +
       fx("Split on a separator", '=TEXTSPLIT(A2,", ")',
          """<p>The result spills rightwards. Pass a second separator to split down rows as well
&mdash; <code>=TEXTSPLIT(A2,",",";")</code> makes a grid.</p>""")),
  dict(h="Take one side with TEXTBEFORE or TEXTAFTER",
       plain="For a first and last name, TEXTBEFORE up to the first space and TEXTAFTER from the last space is more robust than splitting.",
       body="""<p>Better than splitting when the number of parts varies:</p>""" +
       fx("First and last name",
          '=TEXTBEFORE(A2," ")\n'
          '=TEXTAFTER(A2," ",-1)',
          """<p>The <code>-1</code> means &ldquo;the last one&rdquo;. So a middle name is simply
ignored, where <code>TEXTSPLIT</code> would have put it in a column of its own and pushed the surname
sideways.</p>""")),
  dict(h="Handle the rows that do not match",
       plain="Give TEXTBEFORE a fourth argument for what to return when the separator is not there, or wrap it in IFERROR.",
       body="""<p>A single-word name has no space in it, and by default that is an error:</p>""" +
       fx("Cope with a missing separator", '=TEXTBEFORE(A2," ",1,,,A2)',
          """<p>The last argument is what to return when the separator is not found &mdash; here, the
whole cell. <code>IFERROR</code> does the same job and reads more clearly.</p>""")),
  dict(h="Without these functions: LEFT and FIND",
       plain="LEFT with FIND takes everything up to the first separator, and works in every version.",
       body="""<p>The universal version:</p>""" +
       fx("Everything before the first space",
          '=LEFT(A2,FIND(" ",A2&" ")-1)',
          """<p>The <code>&amp;" "</code> is what stops it erroring on a cell with no space in it
&mdash; it guarantees there is always one to find. This works in every version of Excel, in Sheets
and in LibreOffice.</p>""")),
 ],
 body="""<h2>Getting the last word out</h2>
<p>Harder than the first, because you cannot search backwards. The standard trick is to pad every
separator until it is enormous, then take the tail:</p>
""" + fx("Last word, any version",
'=TRIM(RIGHT(SUBSTITUTE(TRIM(A2)," ",REPT(" ",99)),99))',
"""<p>Replace each space with 99 spaces, take the last 99 characters, trim. The last word is the only
one that can survive that. Ugly, and it works everywhere &mdash; which is why it has been copied into
so many workbooks.</p>""") + """
<h2>When Power Query is the better answer</h2>
<p>If the split is part of a monthly import, do it in Power Query rather than with formulas. Its
<em>Split Column</em> handles by delimiter, by position, and by the change from letters to digits
&mdash; and it runs on refresh.</p>
<h2>Names deserve care</h2>
<p>Splitting a full name is never fully solvable. <code>van der Berg</code>, <code>O'Brien</code>,
<code>Maria de los Angeles</code> and single-name people all break a simple rule. Take everything
after the last space as the surname, then <em>look at the result</em>. On a list of a few hundred it
takes a minute, and getting somebody's name wrong in a letter is worth more than a minute.</p>
<h2>Google Sheets</h2>
<p>Sheets has <code>SPLIT</code>, which is older and simpler than <code>TEXTSPLIT</code>. It has no
direct <code>TEXTBEFORE</code> or <code>TEXTAFTER</code>, but <code>INDEX(SPLIT(A2," "),1)</code>
gets the first piece.</p>""",
 faq=[
  ("What is the difference between TEXTSPLIT and Text to Columns?",
   "Text to Columns is a one-off action on the cells that exist at the time. TEXTSPLIT is a formula, so it updates and covers rows added later."),
  ("How do I get the last word of a cell?",
   "TEXTAFTER(A2,\" \",-1) on Excel 365, where -1 means the last occurrence. On older versions, substitute each space with 99 spaces and take the last 99 characters."),
  ("What happens when the separator is not there?",
   "TEXTBEFORE and TEXTAFTER return an error by default. Give them a fourth argument for what to return instead, or wrap them in IFERROR."),
  ("Why do I get #SPILL! from TEXTSPLIT?",
   "The result needs several columns and something is in the way. Clear the cells to the right of the formula."),
  ("What should I use on Excel 2019?",
   "Text to Columns for a one-off, Power Query for anything repeated, or LEFT with FIND for a formula that works in every version."),
  ("Is splitting names reliable?",
   "No rule handles every name. Take everything after the last space as the surname, then check the result by eye — double-barrelled surnames and name particles will break any simple rule."),
 ],
 related=[("excel-regex-functions", "Regex in Excel"),
          ("excel-extract-numbers-from-text", "Getting the numbers out of messy text"),
          ("clean-student-list-excel", "Cleaning a class list export")],
),
]
