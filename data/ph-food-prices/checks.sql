-- check: vocabulary closure on rice variety
-- level: error
-- Any commodity name not on the committed list is a parse artifact until a
-- human says otherwise. This is what catches 'sGlutinous'.
select distinct commodity, count(*) as rows
from ph_rice_prices_daily
where commodity not in (
  'Basmati','Fancy','Glutinous','Japonica/Jasponica','Other Special','Premium',
  'Regular Milled','Special','Special/Fancy','Well Milled',
  'NFA (Regular milled)','NFA (Well milled)',
  'Premium (Yellow tag)','Regular milled (White tag)','Special (Blue tag)',
  'Well milled (White tag)',
  'P20 Benteng Bigas Meron Na','Premium (RFA5)','Regular Milled (RFA100)','Well Milled (RFA25)'
)
group by 1;

-- check: coverage continuity by year (known)
-- level: warn
-- A year with source PDFs but no output rows means the parser stopped working
-- on that layout. Warn, not error, while the infographic era is a known gap.
select c.yr, c.n_files, coalesce(d.n_rows, 0) as n_rows
from (select strftime(date, '%Y') as yr, count(*) as n_files
      from ph_rice_prices_coverage group by 1) c
left join (select strftime(date, '%Y') as yr, count(*) as n_rows
           from ph_rice_prices_daily group by 1) d using (yr)
where coalesce(d.n_rows, 0) = 0 and c.n_files > 0;

-- check: per-series price envelope (known)
-- level: warn
-- Deliberately per-commodity, not a global band. Basmati legitimately trades
-- at 215-250 PHP/kg; a global 10-200 check flags 173 good rows and teaches
-- everyone to ignore it.
-- Known standing exception: Basmati at 60.00 on 2025-11-14. Verified against
-- Daily-Price-Index-November-14-2025.pdf, which really does print 60.00 where
-- Basmati normally sits near 200. A source anomaly, not a parse error, so the
-- row stays and this check warns rather than blocks.
with band as (
  select commodity,
         quantile_cont(price_php_per_kg, 0.01) lo,
         quantile_cont(price_php_per_kg, 0.99) hi
  from ph_rice_prices_daily group by 1)
select r.date, r.commodity, r.price_php_per_kg
from ph_rice_prices_daily r join band b using (commodity)
where r.price_php_per_kg < b.lo * 0.5 or r.price_php_per_kg > b.hi * 2;

-- check: every row carries a source
-- level: error
select count(*) from ph_rice_prices_daily
where source_pdf is null or trim(source_pdf) = ''
having count(*) > 0;

-- ---- the basket, for projects/food-prices-analysis.html ---------------------

-- check: every basket row carries a source
-- level: error
select commodity from ph_food_commodities
where source is null or trim(source) = '';

-- check: no change figure uses a partial year
-- level: error
-- The file reaches June 2026. A 2026 endpoint would compare six months against
-- twelve and report the seasonal cycle as inflation.
select commodity, last_year from ph_food_commodities where last_year > 2025;

-- check: every commodity's change matches its own endpoints
-- level: error
select commodity, first_php_per_kg, last_php_per_kg, change_php_pct
from ph_food_commodities
where abs(change_php_pct - 100.0 * (last_php_per_kg / first_php_per_kg - 1)) > 0.06;

-- check: the CAGR is consistent with the change and the span
-- level: error
-- Derived from the endpoint prices, not from change_php_pct: that column is
-- rounded to one decimal, and over a short span the rounding is amplified enough
-- to fail a tight tolerance on its own. Maize (white), 2020-2022, missed by 0.024
-- for exactly that reason.
select commodity, first_php_per_kg, last_php_per_kg, years, cagr_php_pct
from ph_food_commodities
where last_year > first_year
  and abs(cagr_php_pct
          - 100.0 * (power(last_php_per_kg / first_php_per_kg,
                           1.0 / (last_year - first_year)) - 1))
      > 0.02;

-- check: peso change never falls below dollar change
-- level: error
-- The peso lost value against the dollar across this whole period, so a
-- commodity's rise in pesos must exceed its rise in dollars. A crossing means
-- the two currency columns have been swapped.
select commodity, change_php_pct, change_usd_pct from ph_food_commodities
where change_usd_pct > change_php_pct + 0.05;

-- check: cohort counts sum to the commodities analysed
-- level: error
select sum(commodities) from ph_food_cohorts
having sum(commodities) <> (select count(distinct commodity) from ph_food_annual);

-- check: prices are positive
-- level: error
select commodity, year, median_php_per_kg from ph_food_annual
where median_php_per_kg <= 0 or median_usd_per_kg <= 0;

-- check: the onion series covers the crisis and its shoulders
-- level: error
select count(*) n, min(month) mn, max(month) mx from ph_food_onions
having min(month) > '2021-06' or max(month) < '2023-12';

-- check: the onion peak really is the peak
-- level: error
-- The page names January 2023 explicitly, so the data must agree that it is the
-- maximum rather than merely a large value.
select month, median_php_per_kg from ph_food_onions
where median_php_per_kg = (select max(median_php_per_kg) from ph_food_onions)
  and month <> '2023-01';

-- check: market extremes bracket the median
-- level: error
select month, lowest_market_php, median_php_per_kg, highest_market_php
from ph_food_onions
where lowest_market_php > median_php_per_kg
   or highest_market_php < median_php_per_kg;

-- check: regional medians are backed by enough observations
-- level: error
select commodity, region, observations from ph_food_by_region
where observations < 12;

-- check: coverage records what the basket cannot support
-- level: error
select property, value from ph_food_coverage
where property in ('household spending weights', 'quality or grade adjustment',
                   '2026 in change figures')
  and value <> 0;

-- check: most commodities do not span the record (known)
-- level: warn
-- Recorded rather than fixed. The date range describes the file; it does not
-- describe most of the commodities in it, and every rate on the page is scoped
-- to its own commodity's span for that reason.
select value, note from ph_food_coverage
where property = 'commodities spanning the whole record';

-- check: the 2020 cohort's growth rates cover the inflation spike (known)
-- level: warn
-- A five-year rate beginning in 2020 includes 2022-23 and is not comparable
-- with a twenty-five-year rate. The page groups by cohort instead of ranking
-- them together.
select count(*) n from ph_food_commodities where first_year >= 2020
having count(*) > 20;
