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

-- Added when the page was deepened: the original charted three series from two
-- of six CSVs, and left the regional, varietal and margin structure unused.

-- fact: rice.region.high
select region from ph_rice_by_region order by mean_php_kg desc limit 1;

-- fact: rice.region.high.price
select mean_php_kg from ph_rice_by_region order by mean_php_kg desc limit 1;

-- fact: rice.region.low
select region from ph_rice_by_region order by mean_php_kg limit 1;

-- fact: rice.region.low.price
select mean_php_kg from ph_rice_by_region order by mean_php_kg limit 1;

-- fact: rice.region.spread
select round((select mean_php_kg from ph_rice_by_region order by mean_php_kg desc limit 1)
           - (select mean_php_kg from ph_rice_by_region order by mean_php_kg limit 1), 2);

-- fact: rice.region.spread.pct
select round(100.0 * ((select mean_php_kg from ph_rice_by_region order by mean_php_kg desc limit 1)
                    / (select mean_php_kg from ph_rice_by_region order by mean_php_kg limit 1) - 1), 1);

-- fact: rice.region.year
select distinct year from ph_rice_by_region;

-- fact: rice.regions
select count(*) from ph_rice_by_region;

-- fact: rice.markets
select markets from ph_rice_market_coverage order by year desc limit 1;

-- fact: rice.markets.regions
select regions from ph_rice_market_coverage order by year desc limit 1;

-- fact: rice.obs
select sum(observations) from ph_rice_market_coverage;

-- fact: rice.varieties
select count(distinct commodity) from ph_rice_by_variety;

-- fact: rice.variety.high
select commodity from ph_rice_by_variety
where year = (select max(year) from ph_rice_by_variety) order by mean_php_kg desc limit 1;

-- fact: rice.variety.high.price
select mean_php_kg from ph_rice_by_variety
where year = (select max(year) from ph_rice_by_variety) order by mean_php_kg desc limit 1;

-- fact: rice.variety.low
select commodity from ph_rice_by_variety
where year = (select max(year) from ph_rice_by_variety) order by mean_php_kg limit 1;

-- fact: rice.variety.low.price
select mean_php_kg from ph_rice_by_variety
where year = (select max(year) from ph_rice_by_variety) order by mean_php_kg limit 1;

-- fact: rice.variety.spread
select round((select mean_php_kg from ph_rice_by_variety
              where year = (select max(year) from ph_rice_by_variety)
              order by mean_php_kg desc limit 1)
           - (select mean_php_kg from ph_rice_by_variety
              where year = (select max(year) from ph_rice_by_variety)
              order by mean_php_kg limit 1), 2);

-- fact: rice.farmer.share
-- What share of the retail price reaches the farmer. The single most useful
-- number in this dataset, and it was not on the page.
select farmer_share_pct from ph_rice_margin_chain order by year desc limit 1;

-- fact: rice.farmer.share.year
select year from ph_rice_margin_chain order by year desc limit 1;

-- fact: rice.farmer.share.min
select min(farmer_share_pct) from ph_rice_margin_chain;

-- fact: rice.farmer.share.max
select max(farmer_share_pct) from ph_rice_margin_chain;

-- fact: rice.margin.years
select count(*) from ph_rice_margin_chain;

-- fact: rice.farmgate.latest
select farmgate_php_kg from ph_rice_margin_chain order by year desc limit 1;

-- fact: rice.retail.chain
select retail_php_kg from ph_rice_margin_chain order by year desc limit 1;

-- fact: rice.farm.to.retail
select farm_to_retail from ph_rice_margin_chain order by year desc limit 1;

-- fact: rice.pdfs.total
select count(*) from ph_rice_prices_coverage;

-- fact: rice.pdfs.parsed
select count(*) from ph_rice_prices_coverage where status = 'parsed';

-- fact: rice.pdfs.pct
select round(100.0 * (select count(*) from ph_rice_prices_coverage where status = 'parsed')
           / (select count(*) from ph_rice_prices_coverage), 0);
