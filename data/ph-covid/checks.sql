-- OWID Philippine COVID-19 series and its aggregates.

-- check: every row carries as_of and source
-- level: error
-- as_of is the whole point of this project. The page it replaces mixed a May
-- 2023 case count with a January 2024 death count and a December 2022
-- vaccination count; carrying the date on every row makes that impossible.
select date from ph_covid_daily
where as_of is null or source is null or trim(source) = '';

-- check: one as_of across every table
-- level: error
select count(*) distinct_as_of_values from (
    select distinct as_of::varchar a from ph_covid_daily union
    select distinct as_of::varchar from ph_covid_headline union
    select distinct as_of::varchar from ph_covid_annual union
    select distinct as_of::varchar from ph_covid_waves union
    select distinct as_of::varchar from ph_covid_asean union
    select distinct as_of::varchar from ph_covid_excess union
    select distinct as_of::varchar from ph_covid_stringency)
having count(*) > 1;

-- check: the daily series has no gaps
-- level: error
select count(*) missing from (
    select unnest(generate_series((select min(date) from ph_covid_daily),
                                  (select max(date) from ph_covid_daily),
                                  interval 1 day))::date d)
where d not in (select date from ph_covid_daily)
having count(*) > 0;

-- check: no negative daily counts
-- level: error
select date, new_cases, new_deaths from ph_covid_daily
where new_cases < 0 or new_deaths < 0;

-- check: deaths never exceed cases
-- level: error
select date, total_cases, total_deaths from ph_covid_daily
where total_deaths > total_cases;

-- check: fully vaccinated never exceeds vaccinated
-- level: error
select date, people_vaccinated, people_fully_vaccinated from ph_covid_daily
where people_fully_vaccinated > people_vaccinated;

-- check: stringency stays in its 0-100 range
-- level: error
select date, stringency_index from ph_covid_daily
where stringency_index is not null and (stringency_index < 0 or stringency_index > 100);

-- check: waves partition the series with no overlap
-- level: error
-- Each wave is half-open on the left after the first, so consecutive waves must
-- meet exactly. An overlap silently inflates every per-wave total.
select a.wave, a."end", b.start from ph_covid_waves a
join ph_covid_waves b on b.wave = a.wave + 1
where a."end" <> b.start;

-- check: wave case totals match the daily series
-- level: error
select (select sum(cases_in_wave) from ph_covid_waves) waves,
       (select sum(new_cases) from ph_covid_daily) daily
where (select sum(cases_in_wave) from ph_covid_waves)
   <> (select sum(new_cases) from ph_covid_daily);

-- check: the Philippines appears in the ASEAN comparison
-- level: error
-- A country-name mismatch returns an empty comparison rather than an error --
-- the same failure that made an Ember query return nothing for "Philippines"
-- when the label was "The Philippines".
select 1 where 'Philippines' not in (select country from ph_covid_asean);

-- check: cumulative cases were revised downward mid-series (known)
-- level: warn
-- On 2023-08-14 the cumulative total FELL by 65,079 as DOH revised its count
-- down. OWID rebased the cumulative series without restating the daily one, so
-- sum(new_cases) exceeds max(total_cases) by about 32,000 and always will. Both
-- numbers are correct on their own terms. Kept visible so nobody "fixes" the
-- discrepancy by quietly scaling one series to the other.
select date, total_cases, total_cases - lag(total_cases) over (order by date) delta
from ph_covid_daily qualify delta < 0;

-- check: metrics that stopped reporting long before as_of (known)
-- level: warn
-- Stringency ends 2022-12-31, positivity 2022-06-07, vaccination 2023-03-19.
-- Charts of those series must stop where the data stops rather than run flat to
-- the present, which would read as "policy relaxed to zero" instead of
-- "reporting ended".
select metric, last_date from ph_covid_coverage
where last_date < (select max(date) from ph_covid_daily) - interval 180 day;
