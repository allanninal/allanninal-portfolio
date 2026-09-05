-- Facts published on projects/rice-prices-analysis.html and on
-- projects/food-prices-analysis.html. Each query must return exactly one value.
--
-- Both pages read the same WFP file, so they share this project directory rather
-- than keeping two copies of a 31 MB CSV. Keys beginning rice.* belong to the
-- rice page; keys beginning food.* belong to the basket page.

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

-- ---- the basket, for projects/food-prices-analysis.html ---------------------
--
-- Every rate here is scoped to its own commodity's span. The file runs 2000 to
-- 2026 but only two commodities run the whole way, so a fixed baseline would
-- silently drop most of the basket or invent a starting price for it.

-- fact: food.obs
select value from ph_food_coverage
where property = 'retail per-kilo observations';

-- fact: food.commodities
select value from ph_food_coverage where property = 'commodities';

-- fact: food.markets
select value from ph_food_coverage where property = 'markets';

-- fact: food.regions
select value from ph_food_coverage where property = 'regions';

-- fact: food.spanning
-- Commodities priced continuously from 2000 to 2025. Out of 62.
select value from ph_food_coverage
where property = 'commodities spanning the whole record';

-- fact: food.excluded.aggregate
select value from ph_food_coverage where property = 'WFP aggregate rows excluded';

-- fact: food.excluded.unit
select value from ph_food_coverage where property = 'non-kilogramme rows excluded';

-- ---- how the depth is distributed -------------------------------------------

-- fact: food.cohort.2000
select commodities from ph_food_cohorts where first_month = '2000-01';

-- fact: food.cohort.2008
select commodities from ph_food_cohorts where first_month = '2008-01';

-- fact: food.cohort.2020
select commodities from ph_food_cohorts where first_month = '2020-05';

-- fact: food.cohort.2020.pct
select round(100.0 * (select commodities from ph_food_cohorts
                      where first_month = '2020-05')
           / (select sum(commodities) from ph_food_cohorts), 1);

-- ---- the two long series ----------------------------------------------------

-- fact: food.pork.change
select change_php_pct from ph_food_commodities where commodity = 'Meat (pork)';

-- fact: food.pork.usd
select change_usd_pct from ph_food_commodities where commodity = 'Meat (pork)';

-- fact: food.pork.cagr
select cagr_php_pct from ph_food_commodities where commodity = 'Meat (pork)';

-- fact: food.pork.2000
select first_php_per_kg from ph_food_commodities where commodity = 'Meat (pork)';

-- fact: food.pork.2025
select last_php_per_kg from ph_food_commodities where commodity = 'Meat (pork)';

-- fact: food.rice.change
select change_php_pct from ph_food_commodities
where commodity = 'Rice (regular, milled)';

-- fact: food.rice.usd
select change_usd_pct from ph_food_commodities
where commodity = 'Rice (regular, milled)';

-- fact: food.rice.cagr
select cagr_php_pct from ph_food_commodities
where commodity = 'Rice (regular, milled)';

-- fact: food.rice.2000
select first_php_per_kg from ph_food_commodities
where commodity = 'Rice (regular, milled)';

-- fact: food.rice.2025
select last_php_per_kg from ph_food_commodities
where commodity = 'Rice (regular, milled)';

-- fact: food.pork.over.rice
-- Pork rose this many times as much as rice, over the identical 25 years. The
-- comparison is only possible because these two share a span.
select round((select change_php_pct from ph_food_commodities
              where commodity = 'Meat (pork)')
           / (select change_php_pct from ph_food_commodities
              where commodity = 'Rice (regular, milled)'), 2);

-- ---- pesos against dollars --------------------------------------------------

-- fact: food.peso.gap.pork
-- The distance between a commodity's rise in pesos and its rise in dollars is
-- the peso's own decline. For pork over 25 years it is this many points.
select round((select change_php_pct from ph_food_commodities
              where commodity = 'Meat (pork)')
           - (select change_usd_pct from ph_food_commodities
              where commodity = 'Meat (pork)'), 1);

-- fact: food.usd.falling
-- Commodities whose dollar price fell even though their peso price did not.
select count(*) from ph_food_commodities
where change_usd_pct < 0 and change_php_pct >= 0;

-- fact: food.usd.falling.total
select count(*) from ph_food_commodities where change_usd_pct < 0;

-- ---- the fastest and slowest -------------------------------------------------

-- fact: food.top.commodity
-- Restricted to the 2008 cohort and older, so an 18-year rate is not ranked
-- against a 5-year one.
select commodity from ph_food_commodities where first_year <= 2008
order by change_php_pct desc limit 1;

-- fact: food.top.change
select change_php_pct from ph_food_commodities where first_year <= 2008
order by change_php_pct desc limit 1;

-- fact: food.top.cagr
select cagr_php_pct from ph_food_commodities where first_year <= 2008
order by change_php_pct desc limit 1;

-- fact: food.slow.commodity
select commodity from ph_food_commodities where first_year <= 2008
order by change_php_pct limit 1;

-- fact: food.slow.change
select change_php_pct from ph_food_commodities where first_year <= 2008
order by change_php_pct limit 1;

-- fact: food.long.n
select count(*) from ph_food_commodities where first_year <= 2008;

-- ---- by category -------------------------------------------------------------

-- fact: food.cat.top
select category from ph_food_categories order by median_change_php_pct desc limit 1;

-- fact: food.cat.top.pct
select median_change_php_pct from ph_food_categories
order by median_change_php_pct desc limit 1;

-- fact: food.cat.bottom
select category from ph_food_categories order by median_change_php_pct limit 1;

-- fact: food.cat.bottom.pct
select median_change_php_pct from ph_food_categories
order by median_change_php_pct limit 1;

-- ---- the onion crisis --------------------------------------------------------

-- fact: onion.peak
select median_php_per_kg from ph_food_onions
order by median_php_per_kg desc limit 1;

-- fact: onion.peak.month
select month from ph_food_onions order by median_php_per_kg desc limit 1;

-- fact: onion.peak.market
-- The single highest price recorded in any market that month.
select highest_market_php from ph_food_onions
order by median_php_per_kg desc limit 1;

-- fact: onion.peak.pork
-- Pork per kilo in the same month. Onions cost more.
select pork_median_php from ph_food_onions
order by median_php_per_kg desc limit 1;

-- fact: onion.over.pork
select round((select median_php_per_kg from ph_food_onions
              order by median_php_per_kg desc limit 1)
           / (select pork_median_php from ph_food_onions
              order by median_php_per_kg desc limit 1), 2);

-- fact: onion.before
select median_php_per_kg from ph_food_onions where month = '2022-06';

-- fact: onion.rise
select round((select median_php_per_kg from ph_food_onions
              order by median_php_per_kg desc limit 1)
           / (select median_php_per_kg from ph_food_onions
              where month = '2022-06'), 2);

-- fact: onion.after
select median_php_per_kg from ph_food_onions where month = '2023-04';

-- fact: onion.spread
-- Cheapest and dearest market in the peak month differed by this factor.
select round((select highest_market_php from ph_food_onions
              order by median_php_per_kg desc limit 1)
           / (select lowest_market_php from ph_food_onions
              order by median_php_per_kg desc limit 1), 2);

-- ---- geography ---------------------------------------------------------------

-- fact: food.rice.region.top
select region from ph_food_by_region where commodity = 'Rice (regular, milled)'
order by median_php_per_kg desc limit 1;

-- fact: food.rice.region.top.price
select median_php_per_kg from ph_food_by_region
where commodity = 'Rice (regular, milled)'
order by median_php_per_kg desc limit 1;

-- fact: food.rice.region.bottom
select region from ph_food_by_region where commodity = 'Rice (regular, milled)'
order by median_php_per_kg limit 1;

-- fact: food.rice.region.bottom.price
select median_php_per_kg from ph_food_by_region
where commodity = 'Rice (regular, milled)'
order by median_php_per_kg limit 1;

-- fact: food.rice.region.spread
select round(100.0 * ((select median_php_per_kg from ph_food_by_region
                       where commodity = 'Rice (regular, milled)'
                       order by median_php_per_kg desc limit 1)
                    / (select median_php_per_kg from ph_food_by_region
                       where commodity = 'Rice (regular, milled)'
                       order by median_php_per_kg limit 1) - 1), 1);

-- fact: food.rice.ncr.rank
-- Where Metro Manila sits among the 17 regions on rice, cheapest first. Not
-- where a reader would guess.
select count(*) from ph_food_by_region
where commodity = 'Rice (regular, milled)'
  and median_php_per_kg <= (select median_php_per_kg from ph_food_by_region
                            where commodity = 'Rice (regular, milled)'
                              and region = 'National Capital region');

-- fact: food.rice.ncr.price
select median_php_per_kg from ph_food_by_region
where commodity = 'Rice (regular, milled)'
  and region = 'National Capital region';
