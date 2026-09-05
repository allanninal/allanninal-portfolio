-- Wikimedia pageviews for 24 countries and 14 language projects over one week.
-- Most of these checks guard two things: that a rounded count is never treated as
-- an exact one, and that the countries the API will not answer for stay visible.

-- check: every row carries a source
-- level: error
select country_iso from gw_country_top
where source is null or trim(source) = '';

-- check: the window is the one the page states
-- level: error
select min(date) mn, max(date) mx, count(distinct date) n from gw_country_top
having min(date) <> '2026-08-24' or max(date) <> '2026-08-30'
    or count(distinct date) <> 7;

-- check: no main page or navigation page survived the filter
-- level: error
-- The main page is the largest single entry in almost every country. If one came
-- back, every country would look similar for a reason unrelated to what anyone was
-- reading, and every overlap figure would rise together.
--
-- Deliberately NOT written as "article like '%:%'". That was the first version and
-- it failed on both sides: it flagged real titles that contain a colon
-- (Spider-Man: Brand New Day, Fear Factor: Khatron Ke Khiladi 15) while still
-- missing the Vietnamese and Thai spellings of Special:Search. Namespaces now come
-- from each project's own MediaWiki API, so this check only has to catch the
-- canonical names that must never appear.
select distinct article from gw_country_top
where article in ('Main_Page', '-', 'Hauptseite', 'Portada', 'Beranda')
   or article like 'Special:%' or article like 'Wikipedia:%'
   or article like 'File:%' or article like 'Category:%' or article like 'Help:%';

-- check: the same filter held on the per-project table
-- level: error
select distinct article from gw_project_top
where article in ('Main_Page', '-')
   or article like 'Special:%' or article like 'Wikipedia:%'
   or article like 'File:%' or article like 'Category:%' or article like 'Help:%';

-- check: only Wikipedia projects are counted
-- level: error
-- The per-country endpoint spans every Wikimedia project. The wiktionary,
-- wikibooks and commons entries in it are almost entirely Special:RecentChanges
-- bot traffic on tiny projects, which is not somebody reading an encyclopaedia.
select distinct project from gw_country_top where project not like '%.wikipedia';

-- check: ranks are 1..20 with no gaps inside a country-day
-- level: error
select country_iso, date, count(*) n, max(rank) mx from gw_country_top
group by 1, 2 having max(rank) <> count(*) or max(rank) > 20;

-- check: country counts are labelled as rounded, never as exact
-- level: error
-- The API field is views_ceil: Wikimedia rounds per-country figures so they cannot
-- re-identify a reader. Presenting one as a measurement would be wrong, so the
-- basis travels with every row.
select distinct count_basis from gw_country_top where count_basis <> 'rounded';

-- check: project counts are labelled exact
-- level: error
select distinct count_basis from gw_project_top where count_basis <> 'exact';

-- check: the coverage file says country counts are not exact
-- level: error
select property, value from gw_coverage
where property = 'per-country counts are exact' and value <> 0;

-- check: view counts are positive
-- level: error
select country_iso, article, views_ceil from gw_country_top
where views_ceil is not null and views_ceil <= 0;

-- check: English share is arithmetic, not asserted
-- level: error
select country, entries, en_wikipedia_entries, en_wikipedia_pct
from gw_country_share
where abs(en_wikipedia_pct - 100.0 * en_wikipedia_entries / entries) > 0.011;

-- check: the top project's share is arithmetic too
-- level: error
select country, top_project_entries, entries, top_project_pct
from gw_country_share
where abs(top_project_pct - 100.0 * top_project_entries / entries) > 0.011;

-- check: the top project is never smaller than the English count
-- level: error
-- If English is the largest project for a country then top_project must be
-- en.wikipedia. A country where the two disagree means the max was taken wrongly.
select country, top_project, top_project_entries, en_wikipedia_entries
from gw_country_share
where top_project_entries < en_wikipedia_entries;

-- check: every country in the share table has entries
-- level: error
select country from gw_country_share where entries = 0;

-- check: overlap is a Jaccard, computed from the two set sizes
-- level: error
select a_country, b_country, a_articles, b_articles, shared_articles, jaccard_pct
from gw_overlap
where abs(jaccard_pct - 100.0 * shared_articles
          / (a_articles + b_articles - shared_articles)) > 0.011;

-- check: a pair never shares more articles than the smaller set holds
-- level: error
select a_country, b_country, a_articles, b_articles, shared_articles
from gw_overlap
where shared_articles > least(a_articles, b_articles);

-- check: the same two rules on the language-project overlap
-- level: error
select a_language, b_language, jaccard_pct from gw_project_overlap
where abs(jaccard_pct - 100.0 * shared_articles
          / (a_articles + b_articles - shared_articles)) > 0.011
   or shared_articles > least(a_articles, b_articles);

-- check: no country is paired with itself
-- level: error
select a_iso, b_iso from gw_overlap where a_iso = b_iso
union all
select a_project, b_project from gw_project_overlap where a_project = b_project;

-- check: availability is recorded for every country asked for
-- level: error
-- Including the ones with nothing, which is the point of the table.
select count(*) from gw_availability
having count(*) <> (select value from gw_coverage where property = 'countries');

-- check: a country with no entries says so
-- level: error
select country, entries, availability from gw_availability
where entries = 0 and availability not like 'none%';

-- check: the holiday table covers the projects that answered
-- level: error
select count(*) from gw_holiday having count(*) < 10;

-- check: the holiday date is the one the page names
-- level: error
select distinct date from gw_holiday where date <> '2026-08-15';

-- check: reading is nowhere near universal across countries
-- level: warn
-- The page's central claim. Recorded as a warning so the number is visible in the
-- check output rather than only in prose: if the median overlap ever rose towards
-- 50% the argument would need rewriting, not re-rendering.
select round(median(jaccard_pct), 2) median_overlap_pct,
       count(*) filter (where jaccard_pct = 0) zero_overlap_pairs,
       count(*) pairs
from gw_overlap;

-- check: language projects overlap even less than countries
-- level: warn
select round(median(jaccard_pct), 2) median_overlap_pct,
       count(*) filter (where jaccard_pct = 0) zero_overlap_pairs,
       count(*) pairs
from gw_project_overlap;

-- check: several large countries are simply not published
-- level: warn
-- Russia, Egypt, Vietnam, Turkey, Pakistan and Bangladesh. Recorded because it is
-- the strongest limitation on the page and it is not a fetch failure -- the API
-- answers 404 saying the country is not loaded.
select country, entries from gw_availability where entries = 0;

-- check: smaller countries get shorter lists as well as rounder ones
-- level: warn
select country, entries from gw_availability
where entries > 0 and entries < 140;
