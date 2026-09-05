-- ERA5 daily reanalysis for nine Philippine grid cells, 1940-2024, from two
-- models that disagree. Most of these checks exist to stop the disagreement
-- being averaged away or presented as precision.

-- check: every row carries a source
-- level: error
select city from ph_weather_annual where source is null or trim(source) = '';

-- check: all nine cities are present in every table
-- level: error
select 'annual' t, count(distinct city) n from ph_weather_annual
having count(distinct city) <> 9
union all
select 'monthly', count(distinct city) from ph_weather_monthly
having count(distinct city) <> 9
union all
select 'decades', count(distinct city) from ph_weather_decades
having count(distinct city) <> 9;

-- check: every city has the same number of complete years
-- level: error
-- A city short of the others would quietly shift its own decadal means.
select city, count(*) n from ph_weather_annual group by 1
having count(*) <> (select max(c) from (select count(*) c from ph_weather_annual
                                        group by city));

-- check: no annual row is built from a partial year
-- level: error
-- 360 days is the threshold in the fetcher. A year below it would let a missing
-- January drag a mean down and read as a cold year.
select city, year, days from ph_weather_annual where days < 360;

-- check: temperatures are physically plausible for the Philippines
-- level: error
select city, year, mean_c, hottest_day_c, coolest_night_c from ph_weather_annual
where mean_c not between 10 and 35
   or hottest_day_c not between 15 and 45
   or coolest_night_c not between 0 and 30;

-- check: the mean sits between the mean minimum and the mean maximum
-- level: error
select city, year, mean_min_c, mean_c, mean_max_c from ph_weather_annual
where mean_c < mean_min_c or mean_c > mean_max_c;

-- check: the hottest day is at least the mean maximum
-- level: error
select city, year, mean_max_c, hottest_day_c from ph_weather_annual
where hottest_day_c < mean_max_c;

-- check: rainfall is non-negative and not absurd
-- level: error
select city, year, rainfall_mm from ph_weather_annual
where rainfall_mm < 0 or rainfall_mm > 12000;

-- check: hot-day counts never exceed the days measured
-- level: error
select city, year, days, days_over_35c from ph_weather_annual
where days_over_35c > days;

-- check: partial decades are labelled
-- level: error
-- The 2020s hold five years. Plotted beside ten-year decades without a label,
-- they read as a decade.
select city, decade, years, completeness from ph_weather_decades
where years <> 10 and completeness <> 'partial';

-- check: complete decades really have ten years
-- level: error
select city, decade, years from ph_weather_decades
where completeness = 'complete' and years <> 10;

-- check: decadal means agree with the annual table
-- level: error
select d.city, d.decade, d.mean_c, round(avg(a.mean_c), 2) from_annual
from ph_weather_decades d
join ph_weather_annual a on a.city = d.city
  and a.year - a.year % 10 = cast(replace(d.decade, 's', '') as int)
group by 1, 2, 3
having abs(d.mean_c - avg(a.mean_c)) > 0.06;

-- check: monthly rainfall is a per-year figure, not an 85-year total
-- level: error
-- Summing the monthly means should land near the annual mean rainfall. A factor
-- of eighty-five apart would mean the division by years was dropped.
select city, round(sum(mean_rainfall_mm)) monthly_sum,
       round((select avg(rainfall_mm) from ph_weather_annual a
              where a.city = m.city)) annual_mean
from ph_weather_monthly m group by 1
having abs(sum(mean_rainfall_mm)
           - (select avg(rainfall_mm) from ph_weather_annual a
              where a.city = m.city)) > 200;

-- check: every city has twelve months
-- level: error
select city, count(*) n from ph_weather_monthly group by 1 having count(*) <> 12;

-- check: both models are compared over the same years
-- level: error
-- ERA5 begins in 1940 and ERA5-Land in 1950. Comparing a 1940-2024 slope with a
-- 1950-2024 one is partly a comparison of periods, and the early decades are
-- exactly the ones whose inclusion changes the answer.
select city, model, first_year, last_year from ph_weather_trends
where basis = 'shared period'
  and (first_year <> (select min(first_year) from ph_weather_trends
                      where basis = 'shared period')
       or last_year <> (select max(last_year) from ph_weather_trends
                        where basis = 'shared period'));

-- check: a full-span row states that it is one
-- level: error
select city, model, basis from ph_weather_trends
where model like '%own span%' and basis <> 'full model span';

-- check: both models warm in every city
-- level: error
-- The page's central claim is that the two disagree on how much and agree on
-- whether. If a model ever showed cooling somewhere, that claim would need
-- rewriting rather than re-rendering.
select city, model, trend_c_per_decade from ph_weather_trends
where basis = 'shared period' and model <> 'model spread'
  and trend_c_per_decade <= 0;

-- check: the model spread row is the difference of the two model rows
-- level: error
select s.city, s.trend_c_per_decade stated,
       round(abs(a.trend_c_per_decade - b.trend_c_per_decade), 3) actual
from ph_weather_trends s
join ph_weather_trends a on a.city = s.city and a.model = 'era5'
  and a.basis = 'shared period'
join ph_weather_trends b on b.city = s.city and b.model = 'era5_land'
  and b.basis = 'shared period'
where s.model = 'model spread'
  and abs(s.trend_c_per_decade
          - abs(a.trend_c_per_decade - b.trend_c_per_decade)) > 0.002;

-- check: the two models disagree enough to matter
-- level: error
-- Asserted so the page cannot start quoting a single trend as though the choice
-- of reanalysis were a detail. If they ever converged this section would change.
select city, trend_c_per_decade from ph_weather_trends
where model = 'model spread' and trend_c_per_decade < 0.02;

-- check: every record has a date inside the span
-- level: error
select city, record, date from ph_weather_records
where date < '1940-01-01' or date > '2024-12-31';

-- check: coverage records what reanalysis is not
-- level: error
select property, value from ph_weather_coverage
where property in ('station observations', 'typhoon tracks', 'urban heat island')
  and value <> 0;

-- check: most heat records are recent (known)
-- level: warn
-- Eight of the nine cities set their hottest day in 2020-2024. Recorded rather
-- than asserted, because it is the kind of finding that should be visible in the
-- check output and not only in the prose.
select city, date, value from ph_weather_records
where record = 'hottest day' and date >= '2020-01-01';

-- check: hot-day counts are sensitive to the model, not just to the weather (known)
-- level: warn
-- A count of days above 35 C depends on absolute temperature, and the two
-- reanalyses differ by more than a degree. The direction of the change is robust;
-- the magnitude is not, and the page says so.
select property, value, note from ph_weather_coverage
where property = 'absolute disagreement between models, Manila';
