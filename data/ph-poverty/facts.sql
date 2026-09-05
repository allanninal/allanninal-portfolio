-- Facts published on projects/poverty-analysis.html
--
-- PSA's Family Income and Expenditure Survey is the source for regional
-- Philippine poverty figures and is unreachable by script. These are the
-- national series the World Bank republishes from the same surveys.

-- fact: pov.national
select round(poverty_national_pct, 1) from ph_poverty_annual
where poverty_national_pct is not null order by year desc limit 1;

-- fact: pov.year
select max(year) from ph_poverty_annual where poverty_national_pct is not null;

-- fact: pov.national.first
select round(poverty_national_pct, 1) from ph_poverty_annual
where poverty_national_pct is not null order by year limit 1;

-- fact: pov.365
select round(poverty_365usd_pct, 1) from ph_poverty_annual
where poverty_365usd_pct is not null order by year desc limit 1;

-- fact: pov.215
select round(poverty_215usd_pct, 1) from ph_poverty_annual
where poverty_215usd_pct is not null order by year desc limit 1;

-- fact: pov.gini
select round(gini, 1) from ph_poverty_annual
where gini is not null order by year desc limit 1;

-- fact: pov.gini.first
select round(gini, 1) from ph_poverty_annual where gini is not null order by year limit 1;

-- fact: pov.gini.change
select round((select gini from ph_poverty_annual where gini is not null
              order by year desc limit 1)
           - (select gini from ph_poverty_annual where gini is not null
              order by year limit 1), 1);

-- fact: pov.bottom20
select round(income_share_bottom_20, 1) from ph_poverty_annual
where income_share_bottom_20 is not null order by year desc limit 1;

-- fact: pov.top10
select round(income_share_top_10, 1) from ph_poverty_annual
where income_share_top_10 is not null order by year desc limit 1;

-- fact: pov.ratio
-- The top tenth against the bottom fifth: two and a half times as many people
-- sharing a much smaller slice.
select round((select income_share_top_10 from ph_poverty_annual
              where income_share_top_10 is not null order by year desc limit 1)
           / (select income_share_bottom_20 from ph_poverty_annual
              where income_share_bottom_20 is not null order by year desc limit 1), 1);

-- fact: pov.vulnerable
select round(vulnerable_employment_pct, 1) from ph_poverty_annual
where vulnerable_employment_pct is not null order by year desc limit 1;

-- fact: pov.unemployment
select round(unemployment_pct, 2) from ph_poverty_annual
where unemployment_pct is not null order by year desc limit 1;

-- fact: pov.gni
select gni_per_capita_usd from ph_poverty_annual
where gni_per_capita_usd is not null order by year desc limit 1;

-- fact: pov.surveys
select count(*) from ph_poverty_surveys;

-- fact: pov.span
select max(survey_year) - min(survey_year) from ph_poverty_surveys;

-- fact: pov.asean.year
select distinct year from ph_poverty_asean;

-- fact: pov.asean.gini.rank
select count(*) from ph_poverty_asean
where gini >= (select gini from ph_poverty_asean where country = 'Philippines');

-- fact: pov.asean.n
select count(*) from ph_poverty_asean;

-- fact: pov.asean.gini
select gini from ph_poverty_asean where country = 'Philippines';
