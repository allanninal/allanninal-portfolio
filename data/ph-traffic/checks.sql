-- MMDA incident tweets, cleaned. Most of these checks assert a fault stays
-- visible rather than asserting the data is clean, because it is not.

-- check: every row carries a source
-- level: error
select incident_id from ph_traffic_incidents
where source is null or trim(source) = '';

-- check: the file is the size the page claims
-- level: error
select count(*) from ph_traffic_incidents having count(*) <> 17312;

-- check: every date is inside the stated span
-- level: error
select incident_id, date from ph_traffic_incidents
where date < '2018-08-20' or date > '2020-12-27';

-- check: hours are hours
-- level: error
-- One row reads "22:55 PM" -- a 24-hour clock wearing a 12-hour marker. Taking
-- the marker at face value produced hour 34, which is how it was found. It is
-- now rejected as unparseable rather than converted.
select incident_id, hour from ph_traffic_incidents
where hour is not null and hour not between 0 and 23;

-- check: every retained coordinate is inside Metro Manila
-- level: error
-- 55 rows carry latitude and longitude of exactly 0.0, which is in the Gulf of
-- Guinea. They are blanked rather than dropped, so the incident still counts and
-- the map does not show it.
select incident_id, latitude, longitude from ph_traffic_incidents
where latitude is not null
  and (latitude not between 14.30 and 14.85 or longitude not between 120.88 and 121.18);

-- check: the encoding repair left no double-encoded city names
-- level: error
-- "ParaÃ±aque" is "Parañaque" read as Latin-1. Counting distinct strings counted
-- the city twice, which is where the published "15 Cities/Areas" came from.
select distinct city from ph_traffic_incidents
where city like '%Ã%' or city like '%Â%';

-- check: Parañaque is one city, not two
-- level: error
-- The repair has to leave exactly one row. Written as a having clause so the
-- check returns rows only when it fails -- the first version selected the count
-- unconditionally and therefore always failed.
select count(*) n from ph_traffic_by_city where city like 'Para%aque'
having count(*) <> 1;

-- check: city shares sum to 100
-- level: error
select round(sum(pct_of_all), 2) from ph_traffic_by_city
having abs(sum(pct_of_all) - 100) > 0.05;

-- check: city counts sum to the whole file
-- level: error
select sum(incidents) from ph_traffic_by_city
having sum(incidents) <> (select count(*) from ph_traffic_incidents);

-- check: type families partition the file
-- level: error
select sum(incidents) from ph_traffic_by_type
having sum(incidents) <> (select count(*) from ph_traffic_incidents);

-- check: every incident has exactly one family
-- level: error
select type_family, count(*) from ph_traffic_incidents
where type_family is null or trim(type_family) = '' group by 1;

-- check: hourly counts sum to the timed incidents
-- level: error
select sum(incidents) from ph_traffic_hourly
having sum(incidents) <> (select count(*) from ph_traffic_incidents
                          where hour is not null);

-- check: day-of-week counts sum to the whole file
-- level: error
select sum(incidents) from ph_traffic_dow
having sum(incidents) <> (select count(*) from ph_traffic_incidents);

-- check: monthly counts sum to the whole file
-- level: error
-- The monthly table is built over the calendar span rather than over the months
-- that happen to have rows, so a missing month appears as a zero row with a note
-- instead of vanishing from the series.
select sum(incidents) from ph_traffic_monthly
having sum(incidents) <> (select count(*) from ph_traffic_incidents);

-- check: months with no data are labelled as such
-- level: error
-- A monthly chart that plots July 2020 as zero is asserting there were no
-- incidents in Metro Manila that month. There were; MMDA stopped tweeting.
select month, incidents, note from ph_traffic_monthly
where incidents = 0 and (note is null or trim(note) = '');

-- check: the lockdown windows are contiguous and cover the whole span
-- level: error
select sum(incidents) from ph_traffic_ecq
having sum(incidents) <> (select count(*) from ph_traffic_incidents);

-- check: the lockdown rate is computed per reporting day
-- level: error
-- Dividing by calendar days would blame the roads for a silent Twitter account.
select period, incidents, reporting_days, incidents_per_reporting_day
from ph_traffic_ecq
where reporting_days > 0
  and abs(incidents_per_reporting_day - incidents * 1.0 / reporting_days) > 0.011;

-- check: road death rates are plausible
-- level: error
select country, year, deaths_per_100k from ph_traffic_deaths
where deaths_per_100k <= 0 or deaths_per_100k > 100;

-- check: every ASEAN country has a full death series
-- level: error
select country, count(*) n from ph_traffic_deaths
group by 1 having count(*) <> (select max(c) from (
  select count(*) c from ph_traffic_deaths group by country));

-- check: coverage records the three things this data cannot say
-- level: error
-- Injury counts, fatality counts and traffic volume are all absent. Asserted as
-- zero so a later column addition cannot quietly turn an incident count into a
-- rate or a severity measure.
select property, value from ph_traffic_coverage
where property in ('injury or fatality counts', 'traffic volume') and value <> 0;

-- check: one city dominates the file (known)
-- level: warn
-- Recorded rather than fixed. It is a permanent property of the source and the
-- reason nothing here is called a ranking of dangerous cities.
select city, pct_of_all from ph_traffic_by_city where pct_of_all > 40;

-- check: not all of Metro Manila is present (known)
-- level: warn
-- NCR has 17 local government units. Anything short of that is a gap in MMDA's
-- reporting, and the page states the count rather than implying completeness.
select count(*) n from ph_traffic_by_city where city <> '(no city given)'
having count(*) < 17;

-- check: free-text incident types include misspellings (known)
-- level: warn
-- "VEHCICULAR ACCIDENT" appears eight times, so any exact-string count of
-- accidents is a floor. The families group by substring for this reason.
select incident_type, count(*) n from ph_traffic_incidents
where type_family = 'other' and incident_type like '%VEH%' group by 1;
