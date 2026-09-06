-- Facts published on projects/global-climate-spread-analysis.html
--
-- Seven downscaled CMIP6 models, one scenario, sixteen cities, two twenty-year
-- windows. Two statements are kept rigidly apart throughout: every model warms
-- every city, and the models do not agree on by how much. The first is why this
-- page is not a sceptical one; the second is what it is about.

-- ---- the dataset -------------------------------------------------------------

-- fact: cs.cities
select value from cs_coverage where property = 'cities';

-- fact: cs.models
select value from cs_coverage where property = 'models offered';

-- fact: cs.pairs
select value from cs_coverage where property = 'city-model pairs used';

-- fact: cs.unavailable
select value from cs_coverage where property = 'city-model pairs unavailable';

-- ---- the direction is not in dispute -----------------------------------------

-- fact: allwarm
-- Cities where every model in the ensemble projects warming. This is the check
-- that stops the page being read as an argument about whether warming happens.
select value from cs_coverage where property = 'cities where every model warms';

-- fact: coldest.model.warming
-- The single most conservative model-city combination anywhere in the set: even
-- the coolest projection is a warming one.
select round(min(warming_c), 2) from cs_model;

-- ---- the amount is --------------------------------------------------------

-- fact: median.warming
select value from cs_coverage where property = 'median warming';

-- fact: median.spread
select value from cs_coverage where property = 'median spread between models';

-- fact: median.ratio
select value from cs_coverage where property = 'median spread as a share of warming';

-- fact: median.ratio.pct
-- cs_coverage.value is text: the same column carries "1991-2010" as a window.
select cast(round(100.0 * (select cast(value as double) from cs_coverage
                           where property = 'median spread as a share of warming'))
            as integer);

-- fact: exceeds.n
-- Cities where the disagreement between models is larger than the warming they
-- are disagreeing about.
select value from cs_coverage
where property = 'cities where the spread exceeds the warming';

-- fact: biggest.spread
select value from cs_coverage where property = 'largest spread';

-- fact: smallest.spread
select value from cs_coverage where property = 'smallest spread';

-- fact: widest.city
select city from cs_city order by spread_c desc, city limit 1;

-- fact: widest.warming
select mean_warming_c from cs_city order by spread_c desc, city limit 1;

-- fact: widest.min
select min_warming_c from cs_city order by spread_c desc, city limit 1;

-- fact: widest.max
select max_warming_c from cs_city order by spread_c desc, city limit 1;

-- fact: tightest.city
select city from cs_city order by spread_c, city limit 1;

-- fact: tightest.spread
select spread_c from cs_city order by spread_c, city limit 1;

-- ---- Manila, and the page this one extends -----------------------------------

-- fact: mnl.warming
select mean_warming_c from cs_city where city = 'Manila';

-- fact: mnl.min
select min_warming_c from cs_city where city = 'Manila';

-- fact: mnl.max
select max_warming_c from cs_city where city = 'Manila';

-- fact: mnl.spread
select spread_c from cs_city where city = 'Manila';

-- fact: mnl.baseline
select baseline_mean_c from cs_city where city = 'Manila';

-- fact: mnl.future
select future_mean_c from cs_city where city = 'Manila';

-- fact: mnl.hot.base
select baseline_days_over_35 from cs_city where city = 'Manila';

-- fact: mnl.hot.future
select future_days_over_35 from cs_city where city = 'Manila';

-- fact: mnl.hot.min
select min_future_days_over_35 from cs_city where city = 'Manila';

-- fact: mnl.hot.max
-- The hot-day count is where the model disagreement stops being abstract: the
-- ensemble's range for one city is a different summer, not a different decimal.
select max_future_days_over_35 from cs_city where city = 'Manila';

-- ---- geography explains less than you would expect ---------------------------

-- fact: lat.corr
-- Correlation between latitude and projected warming across these cities. The
-- far north is expected to warm fastest and in this set it barely shows, because
-- the model disagreement is larger than the geographical signal.
select round(corr(latitude, mean_warming_c), 2) from cs_city;

-- fact: warmest.city
select city from cs_city order by mean_warming_c desc, city limit 1;

-- fact: warmest.warming
select mean_warming_c from cs_city order by mean_warming_c desc, city limit 1;

-- fact: warmest.lat
select round(latitude, 1) from cs_city order by mean_warming_c desc, city limit 1;

-- fact: coolest.city
-- Delhi and Dhaka both sit at the minimum, so the ordering carries an explicit
-- tiebreak. Without it this fact flips between rebuilds and the prose beside it
-- stops matching the number.
select city from cs_city order by mean_warming_c, city limit 1;

-- fact: coolest.warming
select mean_warming_c from cs_city order by mean_warming_c, city limit 1;

-- fact: northmost.city
select city from cs_city order by latitude desc limit 1;

-- fact: northmost.warming
select mean_warming_c from cs_city order by latitude desc limit 1;

-- fact: northmost.lat
select round(latitude, 1) from cs_city order by latitude desc limit 1;

-- ---- the city the ensemble cannot agree on -----------------------------------

-- fact: delhi.warming
select mean_warming_c from cs_city where city = 'Delhi';

-- fact: delhi.min
-- One model projects essentially nothing over twenty years. It is still positive.
select min_warming_c from cs_city where city = 'Delhi';

-- fact: delhi.max
select max_warming_c from cs_city where city = 'Delhi';

-- fact: delhi.spread
select spread_c from cs_city where city = 'Delhi';

-- fact: delhi.ratio
select round(spread_over_warming, 2) from cs_city where city = 'Delhi';

-- ---- hot days ----------------------------------------------------------------

-- fact: hot.city
select city from cs_city
order by future_days_over_35 - baseline_days_over_35 desc limit 1;

-- fact: hot.added
select round(future_days_over_35 - baseline_days_over_35, 1) from cs_city
order by future_days_over_35 - baseline_days_over_35 desc limit 1;

-- fact: hot.base
select baseline_days_over_35 from cs_city
order by future_days_over_35 - baseline_days_over_35 desc limit 1;

-- fact: hot.future
select future_days_over_35 from cs_city
order by future_days_over_35 - baseline_days_over_35 desc limit 1;

-- fact: hot.spread
-- The ensemble range on that same city's future hot-day count.
select round(max_future_days_over_35 - min_future_days_over_35, 1) from cs_city
order by future_days_over_35 - baseline_days_over_35 desc limit 1;
