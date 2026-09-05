-- Facts published on projects/global-reading-analysis.html
--
-- Two universes, kept apart because their counts mean different things. Anything
-- named country.* comes from the per-country endpoint, whose view counts are
-- deliberately ROUNDED by Wikimedia so per-country reading cannot re-identify
-- anyone. Anything named lang.* comes from the per-project endpoint, whose counts
-- are exact. No country view count is ever presented as a measurement.

-- ---- the shape of the dataset ------------------------------------------------

-- fact: gw.countries
select value from gw_coverage where property = 'countries';

-- fact: gw.projects
select value from gw_coverage where property = 'language projects';

-- fact: gw.days
select value from gw_coverage where property = 'days';

-- fact: gw.topn
select value from gw_coverage where property = 'articles read per list';

-- fact: gw.country.entries
select count(*) from gw_country_top;

-- fact: gw.project.entries
select count(*) from gw_project_top;

-- fact: gw.dropped.ns
select value from gw_coverage where property = 'namespace entries dropped';

-- fact: gw.dropped.nonwp
select value from gw_coverage where property = 'non-Wikipedia entries dropped';

-- fact: gw.first
select min(date) from gw_country_top;

-- fact: gw.last
select max(date) from gw_country_top;

-- ---- what cannot be measured at all -----------------------------------------

-- fact: gw.missing.countries
-- Countries the API will not answer for. Not a fetch failure: it returns 404 with
-- "the country you asked for is not loaded yet".
select value from gw_coverage where property = 'countries with no data at all';

-- fact: gw.missing.pct
select round(100.0 * (select value from gw_coverage
                      where property = 'countries with no data at all')::int
           / (select value from gw_coverage where property = 'countries')::int, 1);

-- fact: gw.answered
select count(*) from gw_availability where entries > 0;

-- fact: gw.truncated
-- Countries that answer but with fewer articles clearing the privacy floor.
select value from gw_coverage where property = 'countries with a truncated list';

-- fact: gw.smallest.list
select entries from gw_availability where entries > 0 order by entries limit 1;

-- fact: gw.smallest.list.country
select country from gw_availability where entries > 0 order by entries limit 1;

-- ---- who reads in English ----------------------------------------------------

-- fact: en.top.country
select country from gw_country_share order by en_wikipedia_pct desc, country limit 1;

-- fact: en.top.pct
select en_wikipedia_pct from gw_country_share
order by en_wikipedia_pct desc, country limit 1;

-- fact: en.india
select en_wikipedia_pct from gw_country_share where country = 'India';

-- fact: en.india.entries
select entries from gw_country_share where country = 'India';

-- fact: en.india.hindi
-- Entries in India's most-read list that sit on Hindi Wikipedia. It is zero.
select count(*) from gw_country_top
where country = 'India' and project = 'hi.wikipedia';

-- fact: en.philippines
select en_wikipedia_pct from gw_country_share where country = 'Philippines';

-- fact: en.nigeria
select en_wikipedia_pct from gw_country_share where country = 'Nigeria';

-- fact: en.japan
-- The other end of the same measure.
select en_wikipedia_pct from gw_country_share where country = 'Japan';

-- fact: en.japan.own
select top_project_pct from gw_country_share where country = 'Japan';

-- fact: en.france
select en_wikipedia_pct from gw_country_share where country = 'France';

-- fact: en.over80
-- Countries reading English Wikipedia for more than four fifths of their top list.
select count(*) from gw_country_share where en_wikipedia_pct > 80;

-- fact: en.under10
select count(*) from gw_country_share where en_wikipedia_pct < 10;

-- fact: en.between
-- The middle of the distribution is nearly empty, which is what makes it a split
-- rather than a spectrum.
select count(*) from gw_country_share
where en_wikipedia_pct between 10 and 80;

-- fact: en.indonesia
select en_wikipedia_pct from gw_country_share where country = 'Indonesia';

-- ---- how little the world shares --------------------------------------------

-- fact: ov.median
select round(median(jaccard_pct), 2) from gw_overlap;

-- fact: ov.pairs
select count(*) from gw_overlap;

-- fact: ov.zero
select count(*) from gw_overlap where jaccard_pct = 0;

-- fact: ov.max
select jaccard_pct from gw_overlap order by jaccard_pct desc limit 1;

-- fact: ov.max.a
select a_country from gw_overlap order by jaccard_pct desc limit 1;

-- fact: ov.max.b
select b_country from gw_overlap order by jaccard_pct desc limit 1;

-- fact: ov.max.shared
select shared_articles from gw_overlap order by jaccard_pct desc limit 1;

-- ---- and how little the languages share -------------------------------------

-- fact: lov.median
select round(median(jaccard_pct), 2) from gw_project_overlap;

-- fact: lov.pairs
select count(*) from gw_project_overlap;

-- fact: lov.zero
-- Pairs of language Wikipedias whose most-read articles do not intersect at all,
-- over a whole week.
select count(*) from gw_project_overlap where jaccard_pct = 0;

-- fact: lov.zero.pct
select round(100.0 * (select count(*) from gw_project_overlap where jaccard_pct = 0)
           / (select count(*) from gw_project_overlap), 1);

-- fact: lov.max
select jaccard_pct from gw_project_overlap order by jaccard_pct desc limit 1;

-- fact: lov.max.a
select a_language from gw_project_overlap order by jaccard_pct desc limit 1;

-- fact: lov.max.b
select b_language from gw_project_overlap order by jaccard_pct desc limit 1;

-- ---- one day, two national holidays -----------------------------------------

-- fact: hol.date
select distinct date from gw_holiday;

-- fact: hol.projects
select count(*) from gw_holiday;

-- fact: hol.distinct
-- Distinct top articles across those projects. If the world read one thing this
-- would be 1.
select count(distinct top_article) from gw_holiday;

-- fact: hol.hindi
select top_article from gw_holiday where language = 'Hindi';

-- fact: hol.hindi.views
select views from gw_holiday where language = 'Hindi';

-- fact: hol.italian
-- Ferragosto: 15 August is also a public holiday in Italy.
select top_article from gw_holiday where language = 'Italian';

-- fact: hol.italian.views
select views from gw_holiday where language = 'Italian';

-- fact: hol.english
select top_article from gw_holiday where language = 'English';

-- fact: hol.english.views
select views from gw_holiday where language = 'English';

-- fact: hol.english.over.hindi
-- The English top article outdrew the Hindi one by this factor on India's own
-- national holiday.
select round((select views from gw_holiday where language = 'English')::double
           / (select views from gw_holiday where language = 'Hindi')::double, 1);

-- ---- what a pageview is not --------------------------------------------------

-- fact: gw.country.exact
select value from gw_coverage where property = 'per-country counts are exact';

-- fact: gw.bots
select value from gw_coverage where property = 'bot traffic excluded';

-- fact: gw.engagement
select value from gw_coverage where property = 'reading time or engagement';
