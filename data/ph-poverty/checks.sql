-- World Bank poverty and income distribution indicators.

-- check: every row carries a source
-- level: error
select year from ph_poverty_annual where source is null or trim(source) = '';

-- check: shares and rates stay inside 0-100
-- level: error
select year from ph_poverty_annual
where (gini is not null and (gini < 0 or gini > 100))
   or (income_share_bottom_20 is not null
       and (income_share_bottom_20 < 0 or income_share_bottom_20 > 100))
   or (poverty_national_pct is not null
       and (poverty_national_pct < 0 or poverty_national_pct > 100));

-- check: poverty lines nest correctly
-- level: error
-- The $3.65 line must always catch at least as many people as the $2.15 line.
-- An inversion means the two indicators were swapped.
select year, poverty_215usd_pct, poverty_365usd_pct from ph_poverty_annual
where poverty_215usd_pct is not null and poverty_365usd_pct is not null
  and poverty_365usd_pct < poverty_215usd_pct;

-- check: the bottom fifth holds less than the top tenth
-- level: error
-- True of every unequal country and of the Philippines throughout. A violation
-- would mean the two share columns were transposed.
select year, income_share_bottom_20, income_share_top_10 from ph_poverty_annual
where income_share_bottom_20 is not null and income_share_top_10 is not null
  and income_share_bottom_20 > income_share_top_10;

-- check: every survey row has at least one measure
-- level: error
select survey_year from ph_poverty_surveys
where gini is null and poverty_national_pct is null and poverty_215usd_pct is null;

-- check: the ASEAN comparison uses one year for every country
-- level: error
select count(distinct year) from ph_poverty_asean having count(distinct year) > 1;

-- check: the Philippines is in the comparison
-- level: error
select 1 where 'Philippines' not in (select country from ph_poverty_asean);

-- check: distribution measures come from irregular surveys (known)
-- level: warn
-- Fourteen survey points across four decades, not an annual series. The page
-- must plot them as points on a real time axis; a smooth line would invent the
-- years nobody surveyed.
select count(*) survey_points,
       (select max(survey_year) - min(survey_year) from ph_poverty_surveys) span_years
from ph_poverty_surveys having count(*) < 25;
