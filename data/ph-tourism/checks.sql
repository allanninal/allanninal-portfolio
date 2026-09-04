-- DOT arrivals + receipts.

-- check: arrivals split into foreign and overseas Filipinos
-- level: error
-- total_arrivals is the published headline; the two components are published
-- separately. If they stop adding up, one of the three was updated alone.
select year, total_arrivals, foreign_arrivals + overseas_filipinos computed
from ph_tourism_annual
where foreign_arrivals is not null and overseas_filipinos is not null
  and abs(total_arrivals - (foreign_arrivals + overseas_filipinos)) > 1;

-- check: arrivals are positive
-- level: error
select year, total_arrivals from ph_tourism_annual
where total_arrivals is null or total_arrivals <= 0;

-- check: annual coverage is unbroken
-- level: error
select y from (select unnest(range(2010, 2026)) y) g
where y not in (select year from ph_tourism_annual);

-- check: every year states its source
-- level: error
select year from ph_tourism_annual where source is null or trim(source) = '';

-- check: market shares are consistent with arrivals
-- level: error
-- The denominator is total_arrivals, not foreign_arrivals. Checking against
-- foreign_arrivals flagged all three top markets as wrong when the shares
-- were right -- worth stating, because 'share of arrivals' is ambiguous
-- exactly where it matters and the two bases differ by half a million.
select country, share_pct,
       round(100.0 * arrivals_2024 / (select total_arrivals from ph_tourism_annual where year = 2024), 2) computed
from ph_tourism_top_markets_2024
where abs(share_pct - 100.0 * arrivals_2024 / (select total_arrivals from ph_tourism_annual where year = 2024)) > 0.05;

-- check: market growth is consistent with the two years given
-- level: error
select country, growth_pct, round((arrivals_2024 / arrivals_2023::double - 1) * 100, 2) computed
from ph_tourism_top_markets_2024
where abs(growth_pct - (arrivals_2024 / arrivals_2023::double - 1) * 100) > 0.1;

-- check: top markets do not exceed the national total
-- level: error
select sum(arrivals_2024) top_markets,
       (select total_arrivals from ph_tourism_annual where year = 2024) country_total
from ph_tourism_top_markets_2024
having sum(arrivals_2024) > (select total_arrivals from ph_tourism_annual where year = 2024);

-- check: monthly 2026 rows do not exceed the year they belong to
-- level: warn
select month, foreign_arrivals from ph_tourism_monthly_2026
where foreign_arrivals > (select foreign_arrivals from ph_tourism_annual where year = 2025);
