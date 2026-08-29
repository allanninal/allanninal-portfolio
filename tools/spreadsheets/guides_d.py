#!/usr/bin/env python3
"""Group D — Power Query: doing the cleaning once instead of every month.

This is the sequel to the whole data-cleanup line. Groups A to C teach you to repair a
file. Power Query records the repair as steps and replays them on next month's file, so
the work stops being manual. It is built into Excel, so it belongs here; Power BI is a
separate product and is out of scope.

Demand: 2,670,784 views across the top 100 `powerquery` questions, and the individual
figures are quoted in each article where they are load-bearing.

Writing standard (agreed 2026-08-29): short sentences, plain words, every term explained
the first time it appears. The technical names — Power Query, M, unpivot — are the things
themselves and stay as they are.
"""
from build_guide import fx, symptom_table

GROUP = "Power Query — clean it once, not every month"
CAT = "Power Query"

GUIDES_D = [

dict(
 slug="excel-power-query-unpivot",
 title="Unpivot in Excel: Turn a Wide Table Into Rows",
 description="A table with a column per month cannot be filtered or pivoted. Unpivot turns it into three tidy columns in two clicks, and it repeats on next month's file.",
 h1="My table has a column for every month and nothing works",
 lead="Twelve columns, one per month. It reads well on paper and it fights you in every other way: you cannot filter by month, you cannot pivot it, and each new month means editing every formula.",
 category=CAT, group=GROUP,
 card_title="Unpivot a wide table",
 card_blurb="A column per month becomes three tidy columns. Two clicks, and it repeats next month.",
 chips=["Power Query", "Two clicks", "Excel + Google Sheets"],
 keywords=["excel unpivot", "power query unpivot", "excel wide to long", "excel reverse pivot",
           "excel transpose columns to rows", "excel flatten table"],
 short_answer="""<p><strong>Select the columns you want to keep, right-click one of them and choose
<em>Unpivot Other Columns</em>.</strong> Your twelve month columns collapse into two: one holding the
month name and one holding the value. Get there with <em>Data &rarr; From Table/Range</em> to open
Power Query first. Because Power Query saves the step, next month's file is fixed by pressing
Refresh rather than doing it again.</p>""",
 problem_h="Why a column per month makes everything harder",
 problem="""<p>A wide table looks like a report. The trouble is that Excel's own tools &mdash; filters,
pivot tables, <code>SUMIFS</code> &mdash; all expect the opposite shape, where every row is one
observation and every column is one kind of thing.</p>
<p>With a column per month, the month is not <em>in</em> the data. It is in the column headings, and
a formula cannot read a heading as easily as it reads a cell. So you end up writing twelve formulas
instead of one, and adding a thirteenth by hand in January.</p>
<p>Unpivoting turns the headings into values. Three columns &mdash; who, which month, how much
&mdash; and every tool in Excel starts working again.</p>""",
 symptoms=symptom_table([
   ["You cannot filter by month",
    "The month is a heading, not a value",
    "Unpivot so the month becomes data"],
   ["A pivot table cannot use the months",
    "Same reason &mdash; there is no month field",
    "Unpivot first, then pivot"],
   ["Twelve nearly identical formulas",
    "One per column, because the column is the month",
    "One <code>SUMIFS</code> after unpivoting"],
   ["A new month means editing everything",
    "The shape has to grow sideways",
    "After unpivoting it grows downwards, which nothing breaks"],
   ["Charts need re-pointing every month",
    "The source range changed shape",
    "A tall table keeps the same columns forever"],
 ]),
 howto_name="How to unpivot a table in Excel",
 howto_desc="Open the table in Power Query, keep the identifying columns, and unpivot the rest.",
 steps=[
  dict(h="Open the table in Power Query",
       plain="Click any cell in your table, then Data > From Table/Range. If Excel asks, confirm the range and tick My table has headers.",
       body="""<p>Click any cell in the data, then <em>Data &rarr; From Table/Range</em>. If your
range is not already a table Excel offers to make it one &mdash; say yes, and check
<em>My table has headers</em>. The Power Query editor opens in its own window. Nothing has changed
in your workbook yet.</p>"""),
  dict(h="Select the columns you want to KEEP",
       plain="Click the heading of the columns that identify each row — product, region, name. Hold Ctrl to select more than one.",
       body="""<p>Click the heading of each column that <em>identifies</em> the row: product name,
region, customer. Hold <strong>Ctrl</strong> to pick several. These are the columns that will stay
as they are.</p>
<p>Do not select the month columns. That is the part people get backwards on the first try.</p>"""),
  dict(h="Right-click and choose Unpivot Other Columns",
       plain="Right-click one of the selected headings and choose Unpivot Other Columns. Everything you did not select collapses into two columns: Attribute and Value.",
       body="""<p>Right-click one of the highlighted headings and choose <strong>Unpivot Other
Columns</strong>. Everything you did <em>not</em> select folds into two new columns called
<em>Attribute</em> and <em>Value</em>.</p>
<p><em>Unpivot Other Columns</em> rather than plain <em>Unpivot Columns</em> is the important choice:
it means &ldquo;fold up everything except these&rdquo;, so a month column added next year is folded
too, automatically.</p>"""),
  dict(h="Rename the two new columns",
       plain="Double-click the Attribute heading and type Month. Double-click Value and type Amount. Then Close & Load.",
       body="""<p>Double-click <em>Attribute</em> and type <code>Month</code>. Double-click
<em>Value</em> and type <code>Amount</code>. Then <em>Close &amp; Load</em> to send the tidy table
back to a new sheet in your workbook.</p>"""),
  dict(h="Next month, just press Refresh",
       plain="Replace the source data and click Data > Refresh All. Every step you recorded runs again on the new file.",
       body="""<p>This is the part that matters. Power Query recorded what you did as a list of
steps. Put next month's file in place and press <em>Data &rarr; Refresh All</em>, and the same steps
run again in a second.</p>
<p>You did the work once. Everything after that is a button.</p>"""),
 ],
 body="""<h2>What "tidy" means, and why every tool wants it</h2>
<p>There is a shape that spreadsheets and databases both prefer, and it has three rules:</p>
<ul>
<li>Every column is one kind of thing.</li>
<li>Every row is one observation.</li>
<li>Nothing important is stored in a heading.</li>
</ul>
<p>A table with a column per month breaks the third rule, which is why it breaks the tools. Unpivoting
is simply putting it back.</p>
<h2>Going the other way</h2>
<p>If you need the wide shape back &mdash; for a printed report, say &mdash; that is what a pivot
table is for. Keep the tidy table as your data and let the pivot produce the layout. Never store the
report shape and try to calculate from it.</p>
<h2>Google Sheets does not have Power Query</h2>
<p>There is no direct equivalent. The nearest is a formula that rebuilds the tall shape, or the
<code>QUERY</code> function. For a one-off, Sheets users often paste into Excel, unpivot, and paste
back &mdash; which is a fair use of ten minutes.</p>
<h2>Two things that trip people up</h2>
<ul>
<li><strong>Blank cells become rows too.</strong> If a product had no sales in March you get a row
with a blank amount. Filter them out inside Power Query with the arrow on the Amount heading.</li>
<li><strong>Months come back as text.</strong> <code>Jan</code> sorts before <code>Feb</code>
alphabetically, which is luck rather than order. If you need real dates, add a column that converts
them while you are still in Power Query.</li>
</ul>""",
 faq=[
  ("What does unpivot mean?",
   "It turns columns into rows. A table with twelve month columns becomes a table with a month column and a value column, so the month is data you can filter and pivot rather than a heading."),
  ("What is the difference between Unpivot Columns and Unpivot Other Columns?",
   "Unpivot Columns folds up the ones you selected. Unpivot Other Columns folds up everything else. The second is safer, because a new column added later is included automatically."),
  ("Do I have to redo this every month?",
   "No. Power Query saves your steps. Put the new file in place and press Data > Refresh All, and the same steps run again."),
  ("Does this change my original data?",
   "No. Power Query reads your source and writes the result to a new sheet. The original is untouched."),
  ("Is Power Query available in my version of Excel?",
   "It is built into Excel 2016 and later on Windows, and into Excel for Mac from 2019 onwards with some limits. In Excel 2010 and 2013 it was a free add-in from Microsoft."),
  ("Is there an equivalent in Google Sheets?",
   "Not directly. Sheets has no Power Query. The nearest tools are the QUERY function or a formula that rebuilds the tall shape."),
 ],
 related=[("excel-power-query-merge-join", "Merging two tables like a SQL join"),
          ("excel-power-query-combine-files-folder", "Combining every file in a folder"),
          ("excel-sumifs-vs-pivot-table", "Group and sum by category")],
),

dict(
 slug="excel-power-query-parameter-cell",
 title="Use a Cell Value Inside a Power Query Query",
 description="Power Query cannot read a cell directly. Make the cell a named table, load it as a query, and drill to the value — the supported way to parameterise a query.",
 h1="I want my query to read a date from a cell",
 lead="You want the query to filter on whatever is typed in B1, so the person using the sheet never has to open Power Query. It is a completely reasonable thing to want, and the way to do it is not obvious at all.",
 category=CAT, group=GROUP,
 card_title="Reference a cell inside a query",
 card_blurb="The supported way to make a query read a value someone types in a cell.",
 chips=["Power Query", "Parameters", "Excel"],
 keywords=["power query reference cell", "power query parameter", "excel query dynamic filter",
           "power query cell value", "power query named range", "power query drillthrough"],
 short_answer="""<p><strong>Power Query cannot point at a cell the way a formula can. Turn the cell
into a small named table, load that table as its own query, and drill down to the single value.</strong>
Put the value in a one-cell table, name it <code>Parameter</code>, then <em>Data &rarr; From
Table/Range</em>, right-click the value and choose <strong>Drill Down</strong>. That query now
<em>is</em> the value, and your main query can use it in a filter.</p>""",
 problem_h="Why =B1 does not work here",
 problem="""<p>Power Query is not a formula engine. It is a small language, called M, that describes
where data comes from and what to do to it. It has no idea what cell <code>B1</code> is, because it
does not think in cells &mdash; it thinks in tables and steps.</p>
<p>So the answer is to give it something it does understand: a table. A one-cell table is still a
table, and once it is loaded as a query, <em>Drill Down</em> reduces it from a table containing one
value to just the value itself. That value can then be dropped into any step of another query.</p>
<p>It is three more clicks than <code>=B1</code> and it is the supported route. Everything else you
will find suggested online is a workaround that breaks on refresh.</p>""",
 symptoms=symptom_table([
   ["Nowhere to type a cell reference",
    "Power Query has no concept of a cell",
    "Load the cell as a one-row table"],
   ["The filter is hard-coded into the query",
    "You typed the value into the step",
    "Replace it with the drilled-down parameter"],
   ["Users have to open Power Query to change a date",
    "The value lives in the query, not the sheet",
    "Move it to a cell they can type in"],
   ["Refresh fails after moving the file",
    "A hard-coded file path in the query",
    "Parameterise the path the same way"],
   ["Value arrives as a table, not a value",
    "You loaded the table but did not drill down",
    "Right-click the cell &rarr; Drill Down"],
 ]),
 howto_name="How to use a cell value in Power Query",
 howto_desc="Turn the cell into a named table, load it, drill to the value, and use it in a step.",
 steps=[
  dict(h="Put the value in its own tiny table",
       plain="On a settings sheet, type a heading in one cell and the value below it. Select both, press Ctrl+T, and tick My table has headers.",
       body="""<p>On a sheet called <em>Settings</em>, type <code>StartDate</code> in A1 and the date
in A2. Select both cells, press <strong>Ctrl+T</strong>, and tick <em>My table has headers</em>.
Name the table <code>Parameter</code> in the Table Design tab.</p>
<p>A heading and one value. That is all a table needs to be.</p>"""),
  dict(h="Load it as a query and drill down to the value",
       plain="With a cell in that table selected, choose Data > From Table/Range. In Power Query, right-click the single value and choose Drill Down. Then Close & Load To > Only Create Connection.",
       body="""<p>Click inside the table, then <em>Data &rarr; From Table/Range</em>. In the editor,
right-click the one value and choose <strong>Drill Down</strong>. The query stops being a table and
becomes the value itself &mdash; you will see it on its own in the window.</p>
<p>Rename the query to <code>StartDate</code>, then <em>Close &amp; Load To &rarr; Only Create
Connection</em> so it does not write a pointless sheet into your workbook.</p>"""),
  dict(h="Use it in your main query",
       plain="In your main query, apply a filter as normal, then edit that step in the formula bar and replace the typed value with the name of your parameter query.",
       body="""<p>In your real query, filter the column the usual way &mdash; pick a date, click OK.
Then look at the formula bar and replace the hard-coded date with the query name:</p>""" +
       fx("Before and after",
          '= Table.SelectRows(Source, each [Date] >= #date(2026,1,1))\n'
          '= Table.SelectRows(Source, each [Date] >= StartDate)',
          """<p>Turn on <em>View &rarr; Formula Bar</em> if you cannot see it. The name is
case-sensitive and must match the query name exactly.</p>""")),
  dict(h="Test it by changing the cell and refreshing",
       plain="Type a different date in the settings cell and press Data > Refresh All. The result should change without opening Power Query.",
       body="""<p>Change the date on the Settings sheet and press <em>Data &rarr; Refresh All</em>.
The query result changes. Nobody has to open the editor again, which is the entire point.</p>"""),
 ],
 body="""<h2>The same trick for file paths</h2>
<p>A query that points at <code>C:\\Users\\you\\Desktop\\data.xlsx</code> breaks the moment the file
moves or somebody else opens it. Put the folder path in a settings cell, parameterise it exactly as
above, and the query travels.</p>
<h2>Why not the built-in Parameters feature</h2>
<p>Power Query has <em>Manage Parameters</em>, which looks like the obvious answer. It is fine, but
the value lives <em>inside</em> Power Query, so changing it still means opening the editor. If the
person changing it is not you, the cell approach is better, because a cell is something everyone
already knows how to use.</p>
<h2>Keep the settings on their own sheet</h2>
<p>One sheet called Settings, holding every parameter the workbook uses, each in its own small table.
It makes the workbook self-documenting, and it stops someone deleting a row and quietly breaking a
refresh.</p>
<h2>Privacy levels may interrupt you</h2>
<p>The first refresh after combining a cell value with an external source sometimes raises a privacy
warning. It is Excel checking that you are happy for the two to be mixed. Setting both sources to
<em>Organizational</em>, or turning the check off for this file, clears it.</p>""",
 faq=[
  ("Can Power Query read a cell like =B1?",
   "No. Power Query has no concept of a cell — it works with tables and steps. Turn the cell into a one-row named table, load it, and drill down to the value."),
  ("What does Drill Down do?",
   "It reduces a query from a table containing a single value to that value on its own, so it can be used directly inside another step rather than as a table."),
  ("Why not use Manage Parameters?",
   "It works, but the value lives inside Power Query, so changing it means opening the editor. A cell on a settings sheet can be changed by anyone."),
  ("How do I stop the parameter query creating a sheet?",
   "Use Close & Load To and choose Only Create Connection. The query exists and is usable but writes nothing to the workbook."),
  ("Can I parameterise a file path the same way?",
   "Yes, and you should. A hard-coded path breaks as soon as the file moves or someone else opens the workbook."),
  ("Why do I get a privacy level warning?",
   "Excel is checking whether it is safe to combine two sources. Setting both to Organizational, or disabling the check for that file, resolves it."),
 ],
 related=[("excel-power-query-refresh-load-settings", "What Enable Load and Refresh actually do"),
          ("excel-power-query-combine-files-folder", "Combining every file in a folder"),
          ("excel-power-query-unpivot", "Unpivot a wide table")],
),

dict(
 slug="excel-power-query-combine-files-folder",
 title="Combine Every File in a Folder With Power Query",
 description="Point Power Query at a folder and it stacks every file into one table, applying the same cleaning to each. Drop a new file in and press Refresh.",
 h1="I have forty files that all need the same treatment",
 lead="One file per branch, or per month, or per supplier, all the same shape. Opening each one and copying it into a master sheet is an afternoon that comes round again next month.",
 category=CAT, group=GROUP,
 card_title="Combine every file in a folder",
 card_blurb="Stack forty files into one table, cleaned the same way, refreshed with a button.",
 chips=["Power Query", "Folder source", "Excel"],
 keywords=["power query combine files", "excel merge multiple files", "power query folder",
           "excel combine workbooks", "power query append files", "excel consolidate files"],
 short_answer="""<p><strong>Use <em>Data &rarr; Get Data &rarr; From File &rarr; From Folder</em>,
point it at the folder, and choose <em>Combine &amp; Transform</em>.</strong> Power Query reads every
file, applies the same steps to each, and stacks them into one table. Add a file to the folder next
month and press Refresh &mdash; it is included with no further work. Add a column for the file name
so you can always tell which row came from where.</p>""",
 problem_h="Why copy and paste does not survive",
 problem="""<p>Copying forty files into one sheet works exactly once. It has three problems, and they
all arrive later:</p>
<ul>
<li><strong>It has to be redone</strong> every time a file changes or a new one appears.</li>
<li><strong>Nothing records where a row came from.</strong> When a number looks wrong, you cannot
trace it back to its file.</li>
<li><strong>A file with columns in a different order</strong> lands in the wrong columns, and pasting
does not notice.</li>
</ul>
<p>A folder query fixes all three. It matches columns by name rather than by position, it can add the
file name automatically, and it re-runs on a button.</p>""",
 symptoms=symptom_table([
   ["An afternoon of copy and paste, monthly",
    "The combining is manual",
    "Point a query at the folder instead"],
   ["Cannot tell which file a row came from",
    "The source is lost when you paste",
    "Keep the Source.Name column"],
   ["Columns landed in the wrong place",
    "One file had a different column order",
    "Power Query matches on name, not position"],
   ["One bad file breaks everything",
    "A different shape, or a stray heading row",
    "Fix it in the sample file query"],
   ["Refresh is very slow",
    "Every file is re-read each time",
    "Narrow the folder, or filter before combining"],
 ]),
 howto_name="How to combine a folder of files",
 howto_desc="Point at the folder, filter to the files you want, then combine and clean once.",
 steps=[
  dict(h="Point Power Query at the folder",
       plain="Data > Get Data > From File > From Folder, then browse to the folder and click Open.",
       body="""<p><em>Data &rarr; Get Data &rarr; From File &rarr; From Folder</em>. Browse to the
folder and click Open. A preview lists every file it found, with its name, extension and date &mdash;
not the contents yet, just the list.</p>"""),
  dict(h="Filter out anything you do not want",
       plain="Click Transform Data, then use the arrow on the Extension column to keep only .xlsx files, and filter out temporary files beginning with a tilde.",
       body="""<p>Click <strong>Transform Data</strong> rather than Combine, so you can tidy the list
first. Use the arrow on <em>Extension</em> to keep only <code>.xlsx</code>, and filter the
<em>Name</em> column to exclude files starting with <code>~$</code> &mdash; those are Excel's
temporary files for anything currently open, and they will break the refresh if included.</p>"""),
  dict(h="Combine, using the first file as the pattern",
       plain="Click the double-arrow icon on the Content column, choose the sheet or table to take from each file, and click OK.",
       body="""<p>Click the double-arrow icon at the top of the <strong>Content</strong> column.
Power Query opens one file as a sample and asks which sheet or table to take from each. Pick it and
click OK.</p>
<p>It then builds a small set of helper queries and applies the same extraction to every file.</p>"""),
  dict(h="Clean once, in the sample file query",
       plain="In the Queries pane find Transform Sample File. Any step you add there is applied to every file in the folder.",
       body="""<p>This is the part worth understanding. In the Queries pane there is a query called
<strong>Transform Sample File</strong>. Steps you add <em>there</em> &mdash; removing a heading row,
setting a column to Text, trimming spaces &mdash; run against <em>every</em> file.</p>
<p>Clean the sample once and all forty files are cleaned. That is the whole return on the exercise.</p>"""),
  dict(h="Keep the file name column",
       plain="Power Query adds a Source.Name column holding the file each row came from. Do not delete it — it is how you trace a wrong number back to its file.",
       body="""<p>The combined table includes <strong>Source.Name</strong>. Keep it. When a total
looks wrong, that column is the difference between finding the bad file in seconds and opening forty
files by hand.</p>"""),
 ],
 body="""<h2>Adding a file next month</h2>
<p>Save it into the folder and press <em>Data &rarr; Refresh All</em>. It is picked up because the
query points at the folder, not at a list of files. Nothing else to do.</p>
<h2>When one file breaks the refresh</h2>
<p>Usually a file with a different sheet name, a merged cell, or an extra heading row. The error
message names the file. Two options: fix the file, or add a step to the sample query that copes with
both shapes &mdash; for example, removing rows until the real heading appears rather than removing a
fixed number.</p>
<h2>CSV folders work the same way and are faster</h2>
<p>The same feature reads a folder of CSVs, and it is considerably quicker because there is no
workbook to open. If you control the export, CSV is the better choice for this &mdash; just set your
ID columns to Text in the sample query, or you will lose leading zeros across every file at once.</p>
<h2>Keep the folder clean</h2>
<p>The query reads everything you have not filtered out. A folder that also holds last year's
archive, a copy called <em>final v2</em> and somebody's notes will produce a total that is wrong in a
way nobody can see. One folder, one purpose.</p>""",
 faq=[
  ("How do I combine several Excel files into one?",
   "Use Data > Get Data > From File > From Folder, point it at the folder, and choose Combine & Transform. Power Query stacks every file into one table and can re-run on a button."),
  ("Will new files be included automatically?",
   "Yes. The query points at the folder rather than a list of files, so anything you save there is picked up on the next refresh."),
  ("How do I know which file a row came from?",
   "Power Query adds a Source.Name column. Keep it — it is how you trace an odd number back to the file that produced it."),
  ("What if the files have columns in a different order?",
   "Power Query matches columns by name, not position, so a different order is handled. A different column name is not, and shows up as a new column of nulls."),
  ("Why does my refresh fail with a strange file name?",
   "Usually a temporary file. Excel creates files beginning with ~$ for any workbook that is open. Filter them out in the Name column."),
  ("Is combining CSVs faster than Excel files?",
   "Yes, considerably — there is no workbook to open. Set your ID columns to Text in the sample query so you do not lose leading zeros across every file at once."),
 ],
 related=[("excel-power-query-unpivot", "Unpivot a wide table"),
          ("excel-power-query-merge-join", "Merging two tables like a SQL join"),
          ("excel-csv-utf8-mojibake", "Accents turned into mojibake")],
),

dict(
 slug="excel-power-query-merge-join",
 title="Merge Two Tables in Excel Like a SQL Join",
 description="Power Query's Merge gives you inner, left, right, full outer and anti joins by name — and it is far faster than fifty thousand lookup formulas.",
 h1="I need a proper join, not fifty thousand lookups",
 lead="A column of <code>XLOOKUP</code> works until the workbook takes ten seconds to recalculate. Power Query does the same job as a real join, computed once when you refresh, and it can answer questions a lookup cannot.",
 category=CAT, group=GROUP,
 card_title="Merge two tables like a join",
 card_blurb="Inner, left, right, full outer and anti joins by name — and much faster than lookups.",
 chips=["Power Query", "Six join types", "Excel"],
 keywords=["power query merge", "excel join two tables", "power query left join",
           "excel anti join", "power query merge queries", "excel sql join"],
 short_answer="""<p><strong>Load both tables as queries, then <em>Home &rarr; Merge Queries</em>,
pick the matching column in each, and choose a join kind.</strong> Power Query offers all six by
name: inner, left outer, right outer, full outer, left anti and right anti. The anti joins are the
ones no lookup formula can do &mdash; they return the rows that did <em>not</em> match, which is
exactly what a reconciliation needs.</p>""",
 problem_h="What a lookup cannot do",
 problem="""<p>A lookup answers one question: for this key, give me the matching value. That covers a
lot, and it misses three things people regularly need.</p>
<ul>
<li><strong>Rows that did not match.</strong> A lookup gives you <code>#N/A</code> and leaves you to
filter it. An anti join returns exactly those rows as a table.</li>
<li><strong>Every matching row, not the first.</strong> A lookup returns one value. A merge can
return all the matches.</li>
<li><strong>Speed at size.</strong> Fifty thousand lookup formulas are recalculated on every change.
A merge is computed once, on refresh.</li>
</ul>
<p>The vocabulary is the same as SQL, which is deliberate: if you have ever used a database, the
dialog will read like a familiar sentence.</p>""",
 symptoms=symptom_table([
   ["Workbook recalculates for seconds",
    "Thousands of lookups over whole columns",
    "Replace them with one merge"],
   ["Need the rows that did NOT match",
    "A lookup can only give you <code>#N/A</code>",
    "Use a left anti join"],
   ["Need every match, not the first",
    "A lookup returns a single value",
    "Merge, then expand"],
   ["More rows after merging than before",
    "Duplicate keys on the other side &mdash; correct behaviour",
    "Deduplicate the lookup table first"],
   ["The merge matches nothing",
    "Key types differ, or invisible characters",
    "Set both keys to Text and trim them"],
 ]),
 howto_name="How to merge two tables in Power Query",
 howto_desc="Load both as queries, merge on the key, choose the join kind, expand the columns you want.",
 steps=[
  dict(h="Load both tables as queries",
       plain="Click in each table and use Data > From Table/Range. Load them as Only Create Connection so they do not fill your workbook with sheets.",
       body="""<p>Click in the first table, <em>Data &rarr; From Table/Range</em>, then <em>Close
&amp; Load To &rarr; Only Create Connection</em>. Repeat for the second. Both now exist as queries
without writing anything to a sheet.</p>"""),
  dict(h="Merge them on the key column",
       plain="With one query open, choose Home > Merge Queries. Pick the other query, click the matching column heading in each table, and choose the join kind.",
       body="""<p>Open the first query and choose <em>Home &rarr; Merge Queries</em>. Pick the second
query underneath. Click the key column heading in the top table and the matching one in the bottom
&mdash; both highlight when they are selected.</p>
<p>The dialog tells you how many rows will match, at the bottom. Read it. If it says 0 of 50,000, stop
and fix the keys before going further.</p>"""),
  dict(h="Choose the right join kind",
       plain="Left outer keeps every row on the left. Inner keeps only matches. Left anti keeps only the rows that did not match.",
       body="""<p>The six options, in plain terms:</p>
<ul>
<li><strong>Left outer</strong> &mdash; every row from the first table, plus matches where they exist.
This is what a lookup does, and it is the default.</li>
<li><strong>Inner</strong> &mdash; only rows that matched on both sides.</li>
<li><strong>Right outer</strong> &mdash; every row from the second table instead.</li>
<li><strong>Full outer</strong> &mdash; everything from both, matched where possible.</li>
<li><strong>Left anti</strong> &mdash; only rows from the first table with <em>no</em> match. The
reconciliation answer.</li>
<li><strong>Right anti</strong> &mdash; only unmatched rows from the second table.</li>
</ul>"""),
  dict(h="Expand only the columns you need",
       plain="Click the double-arrow on the new column, untick Use original column name as prefix, and select just the columns you want.",
       body="""<p>The merge adds one column holding the whole matched table. Click the double-arrow
in its heading and tick only the columns you actually want &mdash; expanding all thirty when you need
two makes the query slow for no reason.</p>
<p>Untick <em>Use original column name as prefix</em> unless you like headings such as
<code>Customers.Customers.Name</code>.</p>"""),
  dict(h="Check the row count afterwards",
       plain="If the merged table has more rows than you started with, the other table has duplicate keys and each one multiplied a row.",
       body="""<p>A left outer join should return the same number of rows you started with. More
means the second table has duplicate keys, and each duplicate multiplied its row.</p>
<p>That is correct join behaviour, not a bug &mdash; but it is almost never what you wanted. Remove
duplicates from the lookup table first.</p>"""),
 ],
 body="""<h2>The anti join is the one to learn</h2>
<p>Almost nobody knows it exists, and it answers the question a reconciliation is actually made of:
<em>what is in my list that is not in theirs?</em></p>
<p>Two anti joins, run in both directions, give you a complete reconciliation in about a minute: the
invoices with no payment, and the payments with no invoice. Formulas can do it, but they cannot hand
you the two lists as tables.</p>
<h2>Clean the keys before you merge</h2>
<p>Merging matches values exactly, so everything from the basics applies here too: a trailing space,
a non-breaking space, or one side stored as text and the other as a number will all produce a merge
that matches nothing. Trim and set the type on both key columns first, inside Power Query, where it
is two clicks.</p>
<h2>Merge or append?</h2>
<p>They sound similar and do opposite things. <strong>Merge</strong> adds columns &mdash; the same
rows with more information. <strong>Append</strong> adds rows &mdash; two tables of the same shape
stacked on top of each other. If you are combining twelve monthly files, you want Append, or the
folder feature that does it for you.</p>""",
 faq=[
  ("What is the Power Query equivalent of a SQL join?",
   "Merge Queries. It offers inner, left outer, right outer, full outer, left anti and right anti joins, using the same names and meanings as SQL."),
  ("What is an anti join for?",
   "It returns only the rows that did NOT match. Run in both directions it gives you a complete reconciliation — what is in your list and not theirs, and the reverse."),
  ("Why does my merged table have more rows than I started with?",
   "The other table has duplicate keys, so each duplicate multiplied its row. That is correct join behaviour. Remove duplicates from the lookup table first."),
  ("Why does the merge match nothing?",
   "Usually the key is text on one side and a number on the other, or there are invisible characters. Set both key columns to Text and trim them inside Power Query."),
  ("Is a merge faster than thousands of lookups?",
   "Yes, substantially. Lookup formulas recalculate on every change; a merge is computed once when you refresh."),
  ("What is the difference between Merge and Append?",
   "Merge adds columns — the same rows with more information. Append adds rows — two tables of the same shape stacked together."),
 ],
 related=[("excel-join-two-sheets-lookup", "Joining two sheets with a lookup"),
          ("excel-compare-two-lists", "Find what is in list A but not list B"),
          ("excel-power-query-combine-files-folder", "Combining every file in a folder")],
),

dict(
 slug="excel-power-query-refresh-load-settings",
 title="Power Query: What Enable Load and Refresh Actually Do",
 description="Only Create Connection, Enable Load and Include In Report Refresh decide whether a query writes a sheet and whether it updates. What each one means.",
 h1="My workbook is full of sheets I did not ask for",
 lead="Every query you build writes its own sheet, staging tables included, and the file grows to forty megabytes. Two checkboxes control all of it, and nothing explains what they mean at the moment you have to choose.",
 category=CAT, group=GROUP,
 card_title="Enable Load and Refresh, explained",
 card_blurb="Which queries write a sheet, which ones update, and why the file got so big.",
 chips=["Power Query", "File size", "Excel"],
 keywords=["power query enable load", "power query only create connection",
           "power query include in report refresh", "excel query settings",
           "power query file size", "power query refresh all"],
 short_answer="""<p><strong><em>Enable Load</em> decides whether a query writes its result into the
workbook. <em>Include In Report Refresh</em> decides whether <em>Refresh All</em> updates it.</strong>
Staging queries &mdash; the ones that exist only to feed another query &mdash; should be
<em>Only Create Connection</em>, which is Enable Load turned off. They still work; they just do not
write a sheet or store a copy of the data, which is usually where a bloated file comes from.</p>""",
 problem_h="Why the file got so big",
 problem="""<p>When a query has Enable Load switched on, Excel keeps a full copy of its result inside
the workbook file, so it can show it without re-running the query. That is what makes the file large,
and it is doubly wasteful for a staging query whose result nobody ever looks at.</p>
<p>A typical build has one query per source file, a couple that reshape them, and one final query that
combines everything. Only the last needs to be loaded. If all six are, the workbook stores six copies
of overlapping data.</p>
<p>Turning Enable Load off on the staging queries does not break them. The final query still reads
them. They simply stop writing to the workbook.</p>""",
 symptoms=symptom_table([
   ["A sheet for every query",
    "Enable Load is on for all of them",
    "Set staging queries to Only Create Connection"],
   ["File is tens of megabytes",
    "Excel stores a copy of every loaded result",
    "Turn off Enable Load where the result is not read"],
   ["Refresh All takes minutes",
    "Every query refreshes, including staging ones",
    "Untick Include In Report Refresh where it is not needed"],
   ["A query does not update on Refresh All",
    "Include In Report Refresh is off",
    "Turn it back on for that query"],
   ["Deleting a sheet broke a query",
    "Another query used that sheet as its source",
    "Use Only Create Connection instead of deleting sheets"],
 ]),
 howto_name="How to control what a query loads and refreshes",
 howto_desc="Load only what someone reads, and refresh only what needs to be current.",
 steps=[
  dict(h="Choose Only Create Connection when you close a query",
       plain="Use Close & Load To rather than Close & Load, and pick Only Create Connection for any query that only feeds another query.",
       body="""<p>Use <em>Close &amp; Load To</em>, not <em>Close &amp; Load</em>. The dialog offers
<strong>Only Create Connection</strong> &mdash; take it for any query that exists to feed another one.
The query works exactly as before and writes nothing.</p>"""),
  dict(h="Change it later from the Queries pane",
       plain="Open Data > Queries & Connections, right-click a query and choose Load To, then switch it to Only Create Connection.",
       body="""<p><em>Data &rarr; Queries &amp; Connections</em>, right-click the query,
<em>Load To</em>, and switch it. Excel warns that the existing sheet will be deleted. That is what
you want &mdash; the data is still in the query.</p>"""),
  dict(h="Turn off refresh for queries that do not change",
       plain="In query Properties, untick Include In Report Refresh for anything reading a fixed reference file that never changes.",
       body="""<p>Right-click a query, <em>Properties</em>, and untick <strong>Include In Report
Refresh</strong> for anything reading a static reference file &mdash; a price list, a mapping table.
It stops being re-read every time, which on a slow network share is the difference between a refresh
of two seconds and one of two minutes.</p>
<p>You can still refresh it deliberately by right-clicking the query.</p>"""),
  dict(h="Switch on background refresh, or off, deliberately",
       plain="Background refresh lets you keep working while a query runs, but it makes a macro or a chain of dependent queries unpredictable. Turn it off where order matters.",
       body="""<p><em>Properties &rarr; Enable background refresh</em> lets you carry on working
while a query runs. Turn it <strong>off</strong> where one query depends on another finishing first,
or where a macro runs after the refresh &mdash; otherwise the next step starts on stale data.</p>"""),
 ],
 body="""<h2>A sensible layout for a real workbook</h2>
<ul>
<li><strong>Source queries</strong> &mdash; one per file or table, minimal steps.
<em>Only Create Connection.</em></li>
<li><strong>Transform queries</strong> &mdash; the cleaning and reshaping.
<em>Only Create Connection.</em></li>
<li><strong>Output queries</strong> &mdash; the one or two tables a person actually reads.
<em>Loaded to a sheet</em>, or straight to a pivot table.</li>
</ul>
<p>Group them into folders in the Queries pane. On a build with fifteen queries this is the
difference between something maintainable and something nobody dares touch.</p>
<h2>Load to the Data Model instead of a sheet</h2>
<p>The Load To dialog also offers <em>Add this data to the Data Model</em>. It stores the table in a
compressed in-memory engine rather than on a sheet, which handles far more rows than the roughly one
million a worksheet allows, and is what pivot tables read from on large builds.</p>
<h2>Refresh on open</h2>
<p><em>Properties &rarr; Refresh data when opening the file</em> is convenient and worth thinking
about twice: on a shared workbook it means everyone waits for the refresh before they can do
anything, and if the source is unavailable they get an error instead of a file.</p>""",
 faq=[
  ("What does Only Create Connection mean?",
   "The query exists and can be used by other queries, but it does not write its result to a sheet and Excel does not store a copy in the file. It is the right setting for staging queries."),
  ("Why is my Power Query workbook so large?",
   "Excel stores a full copy of the result of every query that has Enable Load switched on. Turning it off for staging queries usually shrinks the file dramatically."),
  ("What is Include In Report Refresh?",
   "It decides whether Refresh All updates that query. Turning it off for a static reference source stops it being re-read every time."),
  ("Will turning off Enable Load break my other queries?",
   "No. Other queries read the query itself, not the sheet it wrote. Nothing downstream changes."),
  ("Should I use background refresh?",
   "Turn it off where order matters — dependent queries or a macro that runs afterwards — because otherwise the next step can start before the refresh has finished."),
  ("What is the Data Model?",
   "A compressed in-memory store that holds far more rows than a worksheet's roughly one million limit. Large pivot tables read from it rather than from a sheet."),
 ],
 related=[("excel-power-query-parameter-cell", "Reference a cell inside a query"),
          ("excel-power-query-combine-files-folder", "Combining every file in a folder"),
          ("excel-formulas-not-updating", "My formulas stopped recalculating")],
),

dict(
 slug="excel-power-query-vs-power-pivot",
 title="Power Query or Power Pivot? Which One You Need",
 description="Power Query shapes data before it arrives. Power Pivot models and measures it after. Which to learn first, and when you need neither.",
 h1="Power Query, Power Pivot — which one do I actually need?",
 lead="Two features with similar names, both free inside Excel, both mentioned in the same breath. They do completely different jobs, and picking the wrong one to learn first wastes a fortnight.",
 category=CAT, group=GROUP,
 card_title="Power Query or Power Pivot?",
 card_blurb="One shapes data on the way in, the other models it once it is there. Which to learn first.",
 chips=["Both free in Excel", "Which first", "Excel"],
 keywords=["power query vs power pivot", "excel power pivot", "what is power query",
           "excel data model", "power pivot measures", "excel bi tools"],
 short_answer="""<p><strong>Power Query gets data in and cleans it. Power Pivot relates several
tables and calculates on them.</strong> If your problem is &ldquo;this file is messy and I do it every
month&rdquo;, you want Power Query. If it is &ldquo;I have four tables and need one number across all
of them&rdquo;, you want Power Pivot. <strong>Learn Power Query first</strong> &mdash; almost everyone
needs it, and many people never need Power Pivot at all.</p>""",
 problem_h="Two different jobs, one confusing pair of names",
 problem="""<p>The names suggest a matched pair. They are better understood as two stages of the same
pipeline.</p>
<p><strong>Power Query</strong> is the loading dock. It connects to files, folders, databases and web
pages, and applies the same cleaning steps every time you refresh. Everything it does happens
<em>before</em> the data reaches your workbook.</p>
<p><strong>Power Pivot</strong> is the warehouse. It holds several tables at once, lets you define
relationships between them &mdash; this order belongs to that customer &mdash; and calculates
measures across them. Everything it does happens <em>after</em> the data has arrived.</p>
<p>Data flows one way: Power Query, then Power Pivot, then a pivot table. That order is why learning
them in that order makes sense.</p>""",
 symptoms=symptom_table([
   ["Cleaning the same file every month",
    "A repeatable import problem",
    "Power Query"],
   ["Combining forty files",
    "An import problem",
    "Power Query"],
   ["Four tables, one number across all",
    "A modelling problem",
    "Power Pivot"],
   ["A pivot table cannot see two tables",
    "No relationship defined between them",
    "Power Pivot"],
   ["More rows than a worksheet holds",
    "Past the ~1 million row limit",
    "Power Pivot's Data Model"],
   ["One tidy table, ordinary size",
    "Neither &mdash; a pivot table is enough",
    "Do not over-tool it"],
 ]),
 howto_name="How to choose between them",
 howto_desc="Decide by which problem you actually have, and learn them in the order the data flows.",
 steps=[
  dict(h="Ask where the pain is",
       plain="If the work is getting the data usable, that is Power Query. If the data is already clean but you cannot calculate across tables, that is Power Pivot.",
       body="""<p>One question sorts it: <strong>is the painful part getting the data usable, or
calculating once it is?</strong></p>
<p>Getting it usable &mdash; opening files, deleting heading rows, fixing types, combining sources
&mdash; is Power Query. Calculating across several related tables is Power Pivot.</p>"""),
  dict(h="Learn Power Query first",
       plain="Almost everyone has an import problem. Far fewer have a modelling problem, and Power Pivot is easier once your data is already clean.",
       body="""<p>Nearly everyone who uses Excel has a repeated import to deal with. Far fewer have
four related tables to model. Power Query also has a much gentler start: it is mostly clicking, and it
shows you the result at every step.</p>
<p>Power Pivot needs DAX, a formula language of its own, and it is much easier to learn against clean
data &mdash; which Power Query gives you.</p>"""),
  dict(h="Use Power Pivot when relationships appear",
       plain="The signal is a pivot table that needs fields from two tables at once, or a lookup column you added only so a pivot could see it.",
       body="""<p>The clearest signal: you find yourself adding a lookup column to a table
<em>purely so a pivot table can group by it</em>. That column is standing in for a relationship, and
a relationship is what Power Pivot provides.</p>
<p>Switch on <em>File &rarr; Options &rarr; Add-ins &rarr; COM Add-ins &rarr; Microsoft Power
Pivot</em>, then load your queries to the Data Model instead of to sheets.</p>"""),
  dict(h="Know when you need neither",
       plain="One tidy table under a hundred thousand rows, refreshed by hand occasionally, needs only a pivot table and some formulas.",
       body="""<p>Plenty of real work needs neither. One tidy table, well under a million rows,
updated by hand now and then, is served perfectly by a pivot table and a few formulas. Reaching for
the heavier tools makes the workbook harder for the next person without making it better.</p>"""),
 ],
 body="""<h2>Where Power BI fits</h2>
<p>Power BI is a separate product that contains both of these, plus its own visuals and a publishing
service. The skills carry over almost exactly &mdash; the same Power Query editor, the same DAX. If
you learn them in Excel and later move to Power BI, very little is wasted.</p>
<p>You do not need Power BI to use either of them. Both are built into Excel at no extra cost.</p>
<h2>Availability</h2>
<ul>
<li><strong>Power Query</strong> &mdash; built into Excel 2016 and later on Windows, and Excel for Mac
from 2019 with some limits. A free add-in for 2010 and 2013.</li>
<li><strong>Power Pivot</strong> &mdash; Windows only, and not in every Excel edition. Home &amp;
Student in particular does not have it.</li>
</ul>
<h2>A short vocabulary</h2>
<ul>
<li><strong>M</strong> &mdash; the language behind Power Query. You rarely write it; the clicks
generate it.</li>
<li><strong>DAX</strong> &mdash; the formula language of Power Pivot. You do write this.</li>
<li><strong>Data Model</strong> &mdash; the in-memory store Power Pivot uses. Holds far more than a
worksheet.</li>
<li><strong>Measure</strong> &mdash; a calculation defined once in the model and reusable in any pivot
table, rather than a formula sitting in a cell.</li>
</ul>""",
 faq=[
  ("What is the difference between Power Query and Power Pivot?",
   "Power Query gets data in and cleans it, before it reaches your workbook. Power Pivot relates several tables and calculates across them, after the data has arrived."),
  ("Which should I learn first?",
   "Power Query. Almost everyone has a repeated import problem, it is mostly clicking rather than a formula language, and it gives Power Pivot the clean data that makes it easier."),
  ("Do I need Power BI to use them?",
   "No. Both are built into Excel at no extra cost. Power BI is a separate product that includes the same two engines plus its own visuals and publishing."),
  ("When do I actually need Power Pivot?",
   "When a pivot table needs fields from two tables at once, or when you find yourself adding a lookup column purely so a pivot can group by it. That column is standing in for a relationship."),
  ("Is Power Pivot available on a Mac?",
   "No. Power Pivot is Windows only, and is not included in every Excel edition. Power Query is available on Mac from Excel 2019, with some limitations."),
  ("What is a measure?",
   "A calculation defined once in the Data Model and reusable in any pivot table, rather than a formula written into a cell."),
 ],
 related=[("excel-power-query-unpivot", "Unpivot a wide table"),
          ("excel-power-query-refresh-load-settings", "What Enable Load and Refresh actually do"),
          ("excel-sumifs-vs-pivot-table", "Group and sum by category")],
),
]
