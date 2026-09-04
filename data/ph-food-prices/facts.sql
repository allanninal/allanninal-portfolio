-- Facts published on projects/rice-prices-analysis.html
-- Each query must return exactly one value.

-- fact: rice.retail.2000
select retail_php_kg from ph_rice_annual where year = 2000;

-- fact: rice.retail.2026
select retail_php_kg from ph_rice_annual where year = 2026;

-- fact: rice.retail.multiple
select round((select retail_php_kg from ph_rice_annual where year = 2026)
           / (select retail_php_kg from ph_rice_annual where year = 2000), 1);

-- fact: rice.retail.2007
select retail_php_kg from ph_rice_annual where year = 2007;

-- fact: rice.retail.2008
select retail_php_kg from ph_rice_annual where year = 2008;

-- fact: rice.retail.2024
select retail_php_kg from ph_rice_annual where year = 2024;

-- fact: rice.retail.2025
select retail_php_kg from ph_rice_annual where year = 2025;

-- fact: rice.spread.mean.2000_2018
select round(avg(spread_pct), 1) from ph_rice_spread_annual
where year between 2000 and 2018;

-- fact: rice.spread.min.2000_2018
select round(min(spread_pct), 1) from ph_rice_spread_annual
where year between 2000 and 2018;

-- fact: rice.spread.max.2000_2018
select round(max(spread_pct), 1) from ph_rice_spread_annual
where year between 2000 and 2018;

-- fact: rice.spread.2019
select spread_pct from ph_rice_spread_annual where year = 2019;

-- fact: rice.spread.2020
select spread_pct from ph_rice_spread_annual where year = 2020;

-- fact: rice.wholesale.2018
select wholesale_php_kg from ph_rice_spread_annual where year = 2018;

-- fact: rice.wholesale.2020
select wholesale_php_kg from ph_rice_spread_annual where year = 2020;

-- fact: rice.retail.grade.2018
select retail_php_kg from ph_rice_spread_annual where year = 2018;

-- fact: rice.retail.grade.2020
select retail_php_kg from ph_rice_spread_annual where year = 2020;

-- fact: rice.daily.rows
select count(*) from ph_rice_prices_daily;

-- fact: rice.daily.days
select count(distinct date) from ph_rice_prices_daily;

-- fact: rice.pdfs.parsed
select count(*) from ph_rice_prices_coverage where status = 'parsed';

-- fact: rice.pdfs.total
select count(*) from ph_rice_prices_coverage;

-- fact: rice.premium.local.latest
select local_php_kg from ph_rice_imported_local
where grade = 'Premium' order by month desc limit 1;

-- fact: rice.premium.imported.latest
select imported_php_kg from ph_rice_imported_local
where grade = 'Premium' order by month desc limit 1;

-- fact: rice.premium.gap.latest
select local_premium_php_kg from ph_rice_imported_local
where grade = 'Premium' order by month desc limit 1;
