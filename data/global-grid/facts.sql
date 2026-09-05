-- Facts published on projects/global-grid-analysis.html
--
-- Eight European grids, one year, aggregated to hourly. Two distinct statistics
-- are kept separate throughout: the energy-weighted annual share (total renewable
-- MWh over total MWh) and the mean of the hourly shares. They are not the same
-- number and a check asserts they never come out equal.

-- ---- the dataset -------------------------------------------------------------

-- fact: gg.countries
select value from gg_coverage where property = 'countries';

-- fact: gg.year
select value from gg_coverage where property = 'year';

-- fact: gg.hours
select value from gg_coverage where property = 'country-hours';

-- fact: gg.price.intervals
select value from gg_coverage where property = 'price intervals';

-- fact: gg.quarterhourly
-- Countries whose native resolution is 15 minutes rather than an hour.
select count(*) from gg_coverage
where property like 'native resolution:%' and value = '15min';

-- fact: gg.hourly.native
select count(*) from gg_coverage
where property like 'native resolution:%' and value = '60min';

-- ---- the annual number, and the distribution it hides ------------------------

-- fact: top.country
select country from gg_country order by annual_renewable_pct desc limit 1;

-- fact: top.annual
select annual_renewable_pct from gg_country
order by annual_renewable_pct desc limit 1;

-- fact: top.min
-- The greenest grid's worst single hour of the year.
select min_pct from gg_country order by annual_renewable_pct desc limit 1;

-- fact: top.max
select max_pct from gg_country order by annual_renewable_pct desc limit 1;

-- fact: top.hours80
select hours_at_or_above_80 from gg_country
order by annual_renewable_pct desc limit 1;

-- fact: bottom.country
select country from gg_country order by annual_renewable_pct limit 1;

-- fact: bottom.annual
select annual_renewable_pct from gg_country order by annual_renewable_pct limit 1;

-- fact: bottom.min
select min_pct from gg_country order by annual_renewable_pct limit 1;

-- fact: bottom.max
select max_pct from gg_country order by annual_renewable_pct limit 1;

-- fact: bottom.hours20
-- Hours the least-renewable grid spent at or below a fifth renewable.
select hours_at_or_below_20 from gg_country order by annual_renewable_pct limit 1;

-- fact: bottom.hours20.pct
select round(100.0 * (select hours_at_or_below_20 from gg_country
                      order by annual_renewable_pct limit 1)
           / (select hours from gg_country order by annual_renewable_pct limit 1), 1);

-- fact: worst.hour.beats.annual
-- The greenest grid's worst hour against the least green grid's whole year. This is
-- the single clearest statement of how little an annual average tells you.
select round((select min_pct from gg_country
              order by annual_renewable_pct desc limit 1)
           / (select annual_renewable_pct from gg_country
              order by annual_renewable_pct limit 1), 2);

-- ---- Germany, the grid people mean when they say "the transition" ------------

-- fact: de.annual
select annual_renewable_pct from gg_country where country = 'Germany';

-- fact: de.mean.hourly
-- Not the same statistic as the annual share, and deliberately shown beside it.
select mean_hourly_pct from gg_country where country = 'Germany';

-- fact: de.min
select min_pct from gg_country where country = 'Germany';

-- fact: de.max
select max_pct from gg_country where country = 'Germany';

-- fact: de.p5
select p5_pct from gg_country where country = 'Germany';

-- fact: de.p95
select p95_pct from gg_country where country = 'Germany';

-- fact: de.spread
select round((select p95_pct from gg_country where country = 'Germany')
           - (select p5_pct from gg_country where country = 'Germany'), 2);

-- fact: de.hours80
select hours_at_or_above_80 from gg_country where country = 'Germany';

-- fact: de.hours80.pct
select round(100.0 * (select hours_at_or_above_80 from gg_country
                      where country = 'Germany')
           / (select hours from gg_country where country = 'Germany'), 1);

-- ---- the week the wind stopped -----------------------------------------------

-- fact: dunkel.worst.country
select country from gg_dunkelflaute order by week_renewable_pct limit 1;

-- fact: dunkel.worst.pct
select week_renewable_pct from gg_dunkelflaute order by week_renewable_pct limit 1;

-- fact: dunkel.worst.annual
select annual_renewable_pct from gg_dunkelflaute
order by week_renewable_pct limit 1;

-- fact: dunkel.worst.fossil
select week_fossil_pct from gg_dunkelflaute order by week_renewable_pct limit 1;

-- fact: dunkel.worst.from
-- Date only: the page names a week, not an hour.
select strftime(cast(week_from as timestamp), '%Y-%m-%d')
from gg_dunkelflaute order by week_renewable_pct limit 1;

-- fact: dunkel.january
-- Countries whose worst renewable week of the whole year began in January. The
-- point of the section: the worst week is a continental weather event, not eight
-- independent national ones, so interconnection cannot rescue anybody.
-- week_from parses as a TIMESTAMP, so it needs an explicit cast before a LIKE.
select count(*) from gg_dunkelflaute
where month(cast(week_from as timestamp)) = 1;

-- fact: dunkel.de.pct
select week_renewable_pct from gg_dunkelflaute where country = 'Germany';

-- fact: dunkel.de.fossil
select week_fossil_pct from gg_dunkelflaute where country = 'Germany';

-- fact: dunkel.fr.pct
select week_renewable_pct from gg_dunkelflaute where country = 'France';

-- fact: dunkel.fr.fossil
-- France's worst renewable week is filled by nuclear rather than by fossil fuel,
-- which is the whole argument about what a low-carbon grid needs behind it.
select week_fossil_pct from gg_dunkelflaute where country = 'France';

-- fact: dunkel.fr.nuclear
select week_nuclear_pct from gg_dunkelflaute where country = 'France';

-- ---- negative prices ---------------------------------------------------------

-- fact: neg.top.country
select country from gg_price_country order by negative_pct desc limit 1;

-- fact: neg.top.intervals
select negative_intervals from gg_price_country order by negative_pct desc limit 1;

-- fact: neg.top.pct
select negative_pct from gg_price_country order by negative_pct desc limit 1;

-- fact: neg.countries
-- Zones with at least one negative interval, of eight.
select count(*) from gg_price_country where negative_intervals > 0;

-- fact: neg.total
select sum(negative_intervals) from gg_price_country;

-- fact: neg.deepest
select min(min_price) from gg_price_country;

-- fact: neg.deepest.country
select country from gg_price_country order by min_price limit 1;

-- fact: neg.zero.country
-- The one market that never went negative all year, and did not because its floor
-- is zero rather than because its grid is different.
select country from gg_price_country where negative_intervals = 0;

-- fact: neg.zero.min
select min_price from gg_price_country where negative_intervals = 0;

-- fact: es.min
-- Spain's floor is a different number again, which is what makes these market
-- rules rather than physics.
select min_price from gg_price_country where country = 'Spain';

-- fact: es.negative
select negative_intervals from gg_price_country where country = 'Spain';

-- fact: neg.deepest.mean
-- Where a negative price bites hardest on average, which is not where it happens
-- most often.
select country from gg_price_country
where negative_intervals > 0 order by mean_when_negative limit 1;

-- fact: neg.deepest.mean.value
select mean_when_negative from gg_price_country
where negative_intervals > 0 order by mean_when_negative limit 1;

-- fact: price.highest.mean
select country from gg_price_country order by mean_price desc limit 1;

-- fact: price.highest.mean.value
select mean_price from gg_price_country order by mean_price desc limit 1;

-- fact: price.lowest.mean
select country from gg_price_country order by mean_price limit 1;

-- fact: price.lowest.mean.value
select mean_price from gg_price_country order by mean_price limit 1;

-- ---- what a share of generation is not ---------------------------------------

-- fact: gg.storage
select value from gg_coverage where property = 'storage counted as generation';

-- fact: gg.imports
select value from gg_coverage where property = 'imports counted as generation';

-- fact: gg.rooftop
select value from gg_coverage where property = 'distribution-level solar included';

-- fact: gg.curtailment
select value from gg_coverage where property = 'curtailment';
