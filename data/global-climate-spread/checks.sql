-- Model spread in CMIP6 projections at city scale.
--
-- This page can be misread in one specific and damaging way, so the checks are
-- built to make that reading impossible: the direction is agreed and only the
-- amount is disputed. A check asserts every model warms every city, and it is an
-- ERROR rather than a warning, because if it ever failed the page's framing would
-- be wrong and it should not build.

-- check: every model row carries a source
-- level: error
select city, model from cs_model where source is null or trim(source) = '';

-- check: every city row carries a source
-- level: error
select city from cs_city where source is null or trim(source) = '';

-- check: every model warms every city
-- level: error
-- The claim the whole page rests on. Disagreement about magnitude is the finding;
-- disagreement about sign would be a different and much larger story, and this
-- data does not contain one.
select city, model, warming_c from cs_model where warming_c <= 0;

-- check: the city-level flag agrees with the model rows
-- level: error
select c.city, c.all_models_warm, min(m.warming_c) coldest
from cs_city c join cs_model m on m.city = c.city
group by 1, 2 having (min(m.warming_c) > 0) <> (c.all_models_warm = 1);

-- check: warming is arithmetic
-- level: error
select city, model, baseline_mean_c, future_mean_c, warming_c from cs_model
where abs(warming_c - (future_mean_c - baseline_mean_c)) > 0.01;

-- check: the city spread is the range of its own model rows
-- level: error
select c.city, c.spread_c stated, round(max(m.warming_c) - min(m.warming_c), 2) actual
from cs_city c join cs_model m on m.city = c.city
group by 1, 2 having abs(c.spread_c - (max(m.warming_c) - min(m.warming_c))) > 0.02;

-- check: the city min and max bracket every model
-- level: error
select c.city, c.min_warming_c, c.max_warming_c, min(m.warming_c), max(m.warming_c)
from cs_city c join cs_model m on m.city = c.city
group by 1, 2, 3
having min(m.warming_c) < c.min_warming_c - 0.01
    or max(m.warming_c) > c.max_warming_c + 0.01;

-- check: the mean warming sits inside the spread
-- level: error
select city, min_warming_c, mean_warming_c, max_warming_c from cs_city
where mean_warming_c < min_warming_c - 0.01 or mean_warming_c > max_warming_c + 0.01;

-- check: the model count matches the rows kept
-- level: error
select c.city, c.models stated, count(m.model) actual
from cs_city c join cs_model m on m.city = c.city
group by 1, 2 having c.models <> count(m.model);

-- check: no city is reported on too small an ensemble
-- level: error
-- A range across two models is not a spread. Cities below the minimum are dropped
-- from cs_city entirely rather than reported with a narrow-looking range.
select city, models from cs_city where models < 4;

-- check: every city-model pair has an availability verdict
-- level: error
select m.city, m.model from cs_model m
where not exists (select 1 from cs_availability a
                  where a.city = m.city and a.model = m.model and a.status = 'ok');

-- check: temperatures are physically plausible
-- level: error
select city, model, baseline_mean_c, future_mean_c from cs_model
where baseline_mean_c < -40 or baseline_mean_c > 45
   or future_mean_c < -40 or future_mean_c > 45;

-- check: hot-day counts are within a year
-- level: error
select city, model, baseline_days_over_35_per_year, future_days_over_35_per_year
from cs_model
where baseline_days_over_35_per_year < 0 or baseline_days_over_35_per_year > 366
   or future_days_over_35_per_year < 0 or future_days_over_35_per_year > 366;

-- check: the coverage city count matches the rows
-- level: error
-- cs_coverage.value is text, because the same column carries "1991-2010" as a
-- window alongside the numbers. Every comparison against it has to cast.
select (select cast(value as integer) from cs_coverage
        where property = 'cities') stated,
       (select count(*) from cs_city) actual
having stated <> actual;

-- check: the stated median spread is the median of the rows
-- level: error
select (select cast(value as double) from cs_coverage
        where property = 'median spread between models') stated,
       round((select median(spread_c) from cs_city), 2) actual
having abs(stated - actual) > 0.02;

-- check: the spread is a large share of the warming (known)
-- level: warn
-- The page's finding, kept in the check output rather than only in prose.
select round(median(mean_warming_c), 2) median_warming,
       round(median(spread_c), 2) median_spread,
       round(median(spread_over_warming), 2) ratio
from cs_city;

-- check: some cities disagree more than they warm (known)
-- level: warn
select city, mean_warming_c, spread_c, spread_over_warming from cs_city
where spread_c > mean_warming_c order by spread_over_warming desc;

-- check: models are not equally available everywhere (known)
-- level: warn
select model, status, count(*) from cs_availability group by 1, 2 order by 1, 2;

-- check: hot days move more than the mean does (known)
-- level: warn
select city, baseline_days_over_35, future_days_over_35,
       round(future_days_over_35 - baseline_days_over_35, 1) added
from cs_city where future_days_over_35 > 0
order by future_days_over_35 - baseline_days_over_35 desc limit 10;
