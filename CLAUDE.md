# allanninal.dev

Static portfolio site. Philippines-focused data analysis, plus product and
field-notes sections. No build step for the site itself: pages are committed
HTML with inline Chart.js.

## Layout

```
projects/<topic>-analysis.html   the rigorous version: charts, tables, methodology
blog/<topic>-analysis.html       the plain-language companion, one per project
data/<project>/                  the CSVs a project is built from
data/<project>/_build/           the scripts that produce those CSVs
tools/                           site generators (nav, field notes, /build, spreadsheets)
images/og-<topic>.png            1200x630 Open Graph card, one per project
```

Every `projects/` page has a `blog/` counterpart with the same filename, and
every page links to its twin in both directions.

## Data pipeline conventions

**One directory per project.** CSVs at `data/<project>/`, the scripts that
build them at `data/<project>/_build/`. Scripts are plain Python 3 + stdlib.
The only external binaries assumed are `pdftotext` (poppler) and `magick`.

**Every CSV carries a `source` column.** Not a header comment, a column — so a
row stays attributable after someone filters or joins it. Where a project mixes
vintages or sources, say which per row (`data/ph-dengue/ph_dengue_annual.csv`
is the model: HDX for 2016-2021, DOH press releases after).

**Write a coverage file when extraction is partial.** If a script parses 841 of
2,367 PDFs, emit a second CSV with one row per source document and its status
(`parsed` / `no rice table` / `error:...`). Coverage that lives only in a log is
coverage nobody can audit. See `data/ph-food-prices/ph_rice_prices_coverage.csv`.

**Cross-check against a second source and fail loudly.**
`data/ph-pse/_build/fetch_pse.py` pulls the same index from Yahoo and from the
exchange and aborts if any overlapping year disagrees by more than a centavo.
Two sources agreeing is worth more than either alone.

**The checked-in CSV is the system of record.** Several upstream feeds are
rolling windows — PSE's `compositeSector` only goes back about five years. A
pipeline that re-derives a whole series from a live feed on every run will
silently drop its own history. Append; never rebuild from scratch.

**State the universe on the page.** If a chart covers the 80 largest listed
companies rather than the whole exchange, the page says so. An unstated subset
reads as a total.

## Before publishing a number

The failure this repo is most prone to is a page that looks sourced and is not.
Published pages have carried a sector chart with two sign errors, an all-time
high stated three different ways, and a year duplicated from the row above it
with "0.0% change". All of it survived review because it looked plausible.

So, before a number ships:

1. It traces to a row in a CSV under `data/`, or to a cited URL on the page.
2. Round numbers and smooth series are suspect. Real market breadth oscillates;
   `[52,54,50,48,45,44,42,40,39,38,36,38]` is a hand-drawn line, not data.
3. Identical adjacent values in a time series are a placeholder until proven
   otherwise.
4. Check the page against itself. The PSE page called both 8,558 and 7,230 the
   all-time high, in different sections.
5. Prefer "not available" to a plausible guess. Section 11 of the PSE page says
   plainly that no market-level P/E is claimed, because the free sources do not
   carry one.

## Verifying a page before commit

- Tag balance and JSON-LD parse (both have broken silently before)
- Charts actually render: extract the Chart.js configs into a standalone page
  and screenshot with headless Chrome. A config can be valid JS and still draw
  nothing.
- `tools/research/eli5.py score blog/*.html` for reading level

## Writing

`/blog/` posts use very simple words, as if explaining to a five-year-old, with
technical terms kept precise and explained in plain language on first use.
Target Flesch reading ease >= 70 and grade <= 6; `tools/research/eli5.py`
measures it. `/projects/` pages carry the rigour; the blog is the on-ramp.

Never use hire-me or available-for-work framing. Open to collaboration, not
looking for a job.

## Known landmines

**Regex.** A monolithic row parser with nested quantifiers burned 65 minutes of
CPU before a stack sample found it spinning in `sre_ucs1_match`. Prefer
splitting fixed-layout rows on `\s{2,}` into columns over one clever pattern.
Where a pattern is unavoidable, Python 3.11+ supports atomic groups `(?>...)`
and possessive quantifiers `a++`, which make the blowup impossible.

**Government PDFs change layout without notice.** The DA price reports have at
least four generations; PSE infographics have two. Detect the layout from its
header rather than assuming one, and count what you could not parse.

**Filenames lie.** Several `Price-Monitoring-*.pdf` files are cigarette reports.
Classify by content after extraction, never by name.

**`urlretrieve` sends no User-Agent** and several government hosts return 403 to
it. Use `urlopen` with an explicit `Request`.

**Do not normalise whitespace before parsing a fixed-layout PDF.** Column
position is the only thing distinguishing two side-by-side tables, and
collapsing runs of spaces destroys it.

**PSA and DOH are behind a Cloudflare managed challenge.** No script reaches
`psa.gov.ph`, `openstat.psa.gov.ph`, `doh.gov.ph`, `coa.gov.ph` or
`lto.gov.ph`. Use HDX, World Bank or UN mirrors, or a browser.

**`data.gov.ph`'s old CKAN API returns the HTML shell with status 200** — old
code "succeeds" while receiving garbage.

## Working style

Long build tasks continue without asking, deploying in batches. Do not use
GitHub Actions; verify deploys by fetching the live URLs. Creating public repos
is pre-authorised. The plaintext PAT in the git remote is deliberate — leave it.
