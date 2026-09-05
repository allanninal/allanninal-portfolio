-- European grid generation and day-ahead prices, one year, eight countries.
-- The checks guard three things: that shares are ratios of things actually
-- generated, that storage and trade never leak into a generation total, and that
-- the mixed native resolutions were reconciled rather than compared raw.

-- check: every row carries a source
-- level: error
select country_code from gg_hourly
where source is null or trim(source) = '';

-- check: every country has a year of hours
-- level: error
-- 8760 in a normal year. A country short by more than a day of hours has a gap
-- that would bias its distribution, which is the whole point of the page.
select country, hours from gg_country where hours < 8712 or hours > 8790;

-- check: the year is the one the page states
-- level: error
-- The API takes start and end in the market's LOCAL time, so a request for
-- 2025-01-01 to 2025-12-31 comes back labelled 2024-12-31 23:00 UTC to
-- 2025-12-31 22:00 UTC -- central European time is UTC+1 in winter. That is a full
-- local calendar year and correct; the first version of this check assumed UTC
-- boundaries and failed on it. Two hours of slack each side covers CET and CEST.
select min(hour_utc) mn, max(hour_utc) mx from gg_hourly
having min(hour_utc) < '2024-12-31 21:00' or min(hour_utc) > '2025-01-01 02:00'
    or max(hour_utc) < '2025-12-31 20:00' or max(hour_utc) >= '2026-01-01 02:00';

-- check: generation is positive
-- level: error
select country, hour_utc, generation_mw from gg_hourly where generation_mw <= 0;

-- check: no component exceeds the total it is part of
-- level: error
select country, hour_utc, generation_mw, renewable_mw, fossil_mw, nuclear_mw
from gg_hourly
where renewable_mw > generation_mw + 0.6
   or fossil_mw > generation_mw + 0.6
   or nuclear_mw > generation_mw + 0.6;

-- check: the three categories never exceed the total together
-- level: error
-- They can be less than it -- "other" exists -- but never more, which is what
-- would happen if a production type were counted in two categories.
select country, hour_utc, generation_mw,
       renewable_mw + fossil_mw + nuclear_mw parts
from gg_hourly
where renewable_mw + fossil_mw + nuclear_mw > generation_mw + 0.6;

-- check: the renewable share is arithmetic, not asserted
-- level: error
select country, hour_utc, renewable_mw, generation_mw, renewable_pct
from gg_hourly
where abs(renewable_pct - 100.0 * renewable_mw / generation_mw) > 0.02;

-- check: shares are percentages of generation
-- level: error
-- Above 100% would mean renewables exceeded total generation, which is
-- arithmetically impossible and would mean a category leaked.
select country, hour_utc, renewable_pct from gg_hourly
where renewable_pct < 0 or renewable_pct > 100.01;

-- check: storage and trade never appear as a production type
-- level: error
-- Pumped-storage output counted as renewable would double-count the electricity
-- used to fill it, and imports counted as generation would let a country look
-- greener than it generates.
select distinct production_type from gg_sources
where production_type in ('Hydro pumped storage',
                          'Hydro pumped storage consumption',
                          'Cross border electricity trading', 'Load',
                          'Residual load');

-- check: every production type is categorised
-- level: error
select distinct production_type, category from gg_sources
where category is null or trim(category) = '';

-- check: no fossil type was filed as renewable
-- level: error
-- "Fossil coal-derived gas" contains the word gas and is not renewable; matching
-- categories on a substring rather than a named set is how that happens.
select production_type, category from gg_sources
where category = 'renewable' and lower(production_type) like 'fossil%';

-- check: the annual share agrees with the hourly rows it comes from
-- level: error
select c.country, c.annual_renewable_pct,
       round(100.0 * sum(h.renewable_mw) / sum(h.generation_mw), 2) recomputed
from gg_country c join gg_hourly h on h.country_code = c.country_code
group by 1, 2
having abs(c.annual_renewable_pct
           - 100.0 * sum(h.renewable_mw) / sum(h.generation_mw)) > 0.02;

-- check: the energy-weighted share and the mean of hourly shares differ
-- level: error
-- They are different statistics and the page treats them as such. If they were
-- ever equal to two decimal places, one of them is being computed wrongly.
select country, annual_renewable_pct, mean_hourly_pct from gg_country
where annual_renewable_pct = mean_hourly_pct;

-- check: the quantiles are ordered
-- level: error
select country, min_pct, p5_pct, median_pct, p95_pct, max_pct from gg_country
where not (min_pct <= p5_pct and p5_pct <= median_pct
           and median_pct <= p95_pct and p95_pct <= max_pct);

-- check: the annual share sits between the extremes
-- level: error
select country, min_pct, annual_renewable_pct, max_pct from gg_country
where annual_renewable_pct < min_pct or annual_renewable_pct > max_pct;

-- check: the histogram accounts for every hour
-- level: error
select h.country, sum(h.hours) banded, max(c.hours) total
from gg_share_hist h join gg_country c on c.country_code = h.country_code
group by 1 having sum(h.hours) <> max(c.hours);

-- check: histogram bands are contiguous and do not overlap
-- level: error
select country, band_from, band_to from gg_share_hist a
where band_to < 999
  and band_to <> (select min(band_from) from gg_share_hist b
                  where b.country_code = a.country_code
                    and b.band_from > a.band_from);

-- check: histogram shares sum to 100 per country
-- level: error
select country, round(sum(pct_of_hours), 2) from gg_share_hist
group by 1 having abs(sum(pct_of_hours) - 100) > 0.06;

-- check: the worst week is a full week and worse than the year
-- level: error
-- If the worst 168-hour window were not below the annual figure the search is
-- broken, because the annual figure is an average over windows including it.
select country, week_renewable_pct, annual_renewable_pct from gg_dunkelflaute
where week_renewable_pct > annual_renewable_pct;

-- check: the worst hour in that week is at or below the week's own share
-- level: error
select country, worst_hour_pct, week_renewable_pct from gg_dunkelflaute
where worst_hour_pct > week_renewable_pct;

-- check: prices are recorded in one unit
-- level: error
select distinct unit from gg_price where unit <> 'EUR / MWh';

-- check: negative price counts are arithmetic
-- level: error
select country, intervals, negative_intervals, negative_pct
from gg_price_country
where abs(negative_pct - 100.0 * negative_intervals / intervals) > 0.02;

-- check: the mean of negative prices really is negative
-- level: error
select country, negative_intervals, mean_when_negative from gg_price_country
where negative_intervals > 0 and mean_when_negative >= 0;

-- check: min and max bracket the mean
-- level: error
select country, min_price, mean_price, max_price from gg_price_country
where mean_price < min_price or mean_price > max_price;

-- check: every country has a price series
-- level: error
select country from gg_country
where country not in (select country from gg_price_country);

-- check: coverage records what is excluded from a generation total
-- level: error
select property, value from gg_coverage
where property in ('storage counted as generation', 'imports counted as generation',
                   'distribution-level solar included', 'curtailment')
  and value <> 0;

-- check: negative prices happen in more than one country (known)
-- level: warn
-- The page's second claim. Day-ahead markets are coupled, so a negative price in
-- Germany is usually a negative price in France and Belgium at the same instant.
select country, negative_intervals, negative_pct from gg_price_country
where negative_intervals > 0;

-- check: the annual share hides both tails (known)
-- level: warn
-- The page's first claim, recorded so the spread is visible in the check output
-- rather than only in prose.
select country, annual_renewable_pct, min_pct, max_pct,
       hours_at_or_above_80, hours_at_or_below_20
from gg_country order by annual_renewable_pct desc;

-- check: native resolution is not uniform (known)
-- level: warn
-- Half these countries report quarter-hourly and half hourly. Everything is
-- aggregated to hourly for comparability, and this is why.
select property, value from gg_coverage
where property like 'native resolution:%';
