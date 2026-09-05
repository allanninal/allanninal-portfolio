-- Facts published on projects/weather-analysis.html
--
-- ERA5 reanalysis for nine Philippine grid cells. Two things to hold on to. This
-- is a model constrained by observations, not a thermometer record. And the two
-- reanalyses disagree by more than a degree on absolute temperature and by a
-- factor of about two on the warming rate, so no single absolute value is
-- presented as "the temperature" and every trend is a range.

-- fact: wx.cities
select value from ph_weather_coverage where property = 'cities';

-- fact: wx.days
select value from ph_weather_coverage where property = 'days per city';

-- fact: wx.obs
select value from ph_weather_coverage where property = 'daily observations read';

-- fact: wx.years
select value from ph_weather_coverage where property = 'complete years per city';

-- fact: wx.first
select min(year) from ph_weather_annual;

-- fact: wx.last
select max(year) from ph_weather_annual;

-- ---- the disagreement, which governs the page --------------------------------

-- fact: wx.models
select value from ph_weather_coverage
where property = 'reanalysis models compared';

-- fact: wx.gap.abs
-- Mean absolute difference between the two reanalyses on Manila's annual mean.
select value from ph_weather_coverage
where property = 'absolute disagreement between models, Manila';

-- fact: wx.gap.trend
select value from ph_weather_coverage
where property = 'trend disagreement between models, Manila';

-- fact: trend.era5.min
-- Slowest and fastest warming across the six cross-checked cities, per model,
-- over the years both models cover.
select min(trend_c_per_decade) from ph_weather_trends
where model = 'era5' and basis = 'shared period';

-- fact: trend.era5.max
select max(trend_c_per_decade) from ph_weather_trends
where model = 'era5' and basis = 'shared period';

-- fact: trend.land.min
select min(trend_c_per_decade) from ph_weather_trends
where model = 'era5_land' and basis = 'shared period';

-- fact: trend.land.max
select max(trend_c_per_decade) from ph_weather_trends
where model = 'era5_land' and basis = 'shared period';

-- fact: trend.ratio
-- How many times faster ERA5 warms than ERA5-Land, averaged over the cities.
select round(avg(a.trend_c_per_decade / b.trend_c_per_decade), 2)
from ph_weather_trends a
join ph_weather_trends b on b.city = a.city and b.model = 'era5_land'
  and b.basis = 'shared period'
where a.model = 'era5' and a.basis = 'shared period';

-- fact: trend.cities
select count(distinct city) from ph_weather_trends where model = 'model spread';

-- fact: trend.shared.first
select min(first_year) from ph_weather_trends where basis = 'shared period';

-- fact: trend.warming.everywhere
-- Cities where both models agree the temperature rose. Should be all of them.
select count(*) from (
  select city from ph_weather_trends
  where basis = 'shared period' and model in ('era5', 'era5_land')
  group by city having min(trend_c_per_decade) > 0);

-- fact: manila.era5.trend
select trend_c_per_decade from ph_weather_trends
where city = 'Manila' and model = 'era5' and basis = 'shared period';

-- fact: manila.land.trend
select trend_c_per_decade from ph_weather_trends
where city = 'Manila' and model = 'era5_land' and basis = 'shared period';

-- fact: manila.era5.mean
select mean_c from ph_weather_trends
where city = 'Manila' and model = 'era5' and basis = 'shared period';

-- fact: manila.land.mean
select mean_c from ph_weather_trends
where city = 'Manila' and model = 'era5_land' and basis = 'shared period';

-- fact: manila.land.change
-- Last ten years against the first ten, on the more conservative model.
select change_c from ph_weather_trends
where city = 'Manila' and model = 'era5_land' and basis = 'shared period';

-- fact: manila.era5.change
select change_c from ph_weather_trends
where city = 'Manila' and model = 'era5' and basis = 'shared period';

-- ---- what the decades show ----------------------------------------------------

-- fact: dec.manila.1970s
select mean_c from ph_weather_decades
where city = 'Manila' and decade = '1970s';

-- fact: dec.manila.2010s
select mean_c from ph_weather_decades
where city = 'Manila' and decade = '2010s';

-- fact: dec.manila.warmest
select mean_c from ph_weather_decades
where city = 'Manila' and completeness = 'complete'
order by mean_c desc limit 1;

-- fact: dec.manila.warmest.name
select decade from ph_weather_decades
where city = 'Manila' and completeness = 'complete'
order by mean_c desc limit 1;

-- fact: dec.manila.coolest.name
select decade from ph_weather_decades
where city = 'Manila' and completeness = 'complete'
order by mean_c limit 1;

-- fact: dec.warmest.is.last
-- Cities whose warmest complete decade is the most recent complete one.
select count(*) from (
  select city from ph_weather_decades where completeness = 'complete'
  group by city
  having max(case when decade = '2010s' then mean_c end) = max(mean_c));

-- fact: dec.partial
-- The 2020s hold five years, and every chart says so.
select years from ph_weather_decades
where city = 'Manila' and decade = '2020s';

-- ---- heat ---------------------------------------------------------------------

-- fact: heat.recent.records
-- Cities whose hottest day on record falls in 2020 or later, of nine.
select count(*) from ph_weather_records
where record = 'hottest day' and date >= '2020-01-01';

-- fact: heat.hottest
select value from ph_weather_records
where record = 'hottest day' order by value desc limit 1;

-- fact: heat.hottest.city
select city from ph_weather_records
where record = 'hottest day' order by value desc limit 1;

-- fact: heat.hottest.date
select date from ph_weather_records
where record = 'hottest day' order by value desc limit 1;

-- fact: heat.only.old
-- The one city whose record predates 2020.
select city from ph_weather_records
where record = 'hottest day' and date < '2020-01-01';

-- fact: heat.only.old.year
select year(date) from ph_weather_records
where record = 'hottest day' and date < '2020-01-01';

-- fact: hot.laoag.1950s
select days_over_35c_per_year from ph_weather_hotdays
where city = 'Laoag' and decade = '1950s';

-- fact: hot.laoag.2020s
select days_over_35c_per_year from ph_weather_hotdays
where city = 'Laoag' and decade = '2020s';

-- fact: hot.manila.1950s
select days_over_35c_per_year from ph_weather_hotdays
where city = 'Manila' and decade = '1950s';

-- fact: hot.manila.2020s
select days_over_35c_per_year from ph_weather_hotdays
where city = 'Manila' and decade = '2020s';

-- fact: hot.manila.ratio
select round((select days_over_35c_per_year from ph_weather_hotdays
              where city = 'Manila' and decade = '2020s')
           / (select days_over_35c_per_year from ph_weather_hotdays
              where city = 'Manila' and decade = '1950s'), 1);

-- ---- rain and season -----------------------------------------------------------

-- fact: rain.wettest.city
select city from (select city, avg(rainfall_mm) r from ph_weather_annual group by 1)
order by r desc limit 1;

-- fact: rain.wettest.mm
select round(avg(rainfall_mm)) from ph_weather_annual
where city = (select city from (select city, avg(rainfall_mm) r
                                from ph_weather_annual group by 1)
              order by r desc limit 1);

-- fact: rain.driest.city
select city from (select city, avg(rainfall_mm) r from ph_weather_annual group by 1)
order by r limit 1;

-- fact: rain.driest.mm
select round(avg(rainfall_mm)) from ph_weather_annual
where city = (select city from (select city, avg(rainfall_mm) r
                                from ph_weather_annual group by 1)
              order by r limit 1);

-- fact: rain.ratio
select round((select avg(rainfall_mm) from ph_weather_annual
              where city = (select city from (select city, avg(rainfall_mm) r
                                              from ph_weather_annual group by 1)
                            order by r desc limit 1))
           / (select avg(rainfall_mm) from ph_weather_annual
              where city = (select city from (select city, avg(rainfall_mm) r
                                              from ph_weather_annual group by 1)
                            order by r limit 1)), 2);

-- fact: rain.laoag.wet
-- Laoag has the sharpest wet/dry split in the set: the wettest month against the
-- driest, in millimetres.
select round(max(mean_rainfall_mm)) from ph_weather_monthly where city = 'Laoag';

-- fact: rain.laoag.dry
select round(min(mean_rainfall_mm)) from ph_weather_monthly where city = 'Laoag';

-- fact: rain.laoag.ratio
select round((select max(mean_rainfall_mm) from ph_weather_monthly
              where city = 'Laoag')
           / (select min(mean_rainfall_mm) from ph_weather_monthly
              where city = 'Laoag'));

-- fact: baguio.mean
-- The one city in the set that is not tropical-hot, because it is at altitude.
select mean_c from ph_weather_trends
where city = 'Baguio' and model = 'era5_land' and basis = 'shared period';

-- fact: baguio.vs.manila
select round((select mean_c from ph_weather_trends
              where city = 'Manila' and model = 'era5_land'
                and basis = 'shared period')
           - (select mean_c from ph_weather_trends
              where city = 'Baguio' and model = 'era5_land'
                and basis = 'shared period'), 2);
