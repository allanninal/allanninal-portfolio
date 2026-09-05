-- Facts published on projects/traffic-analysis.html
--
-- Everything named mmda.* comes from 17,312 MMDA incident tweets covering
-- 20 August 2018 to 27 December 2020, and describes what MMDA reported. Anything
-- named road.* is a national WHO estimate with a year attached.

-- ---- what the file is -------------------------------------------------------

-- fact: mmda.n
select count(*) from ph_traffic_incidents;

-- fact: mmda.first
select min(date) from ph_traffic_incidents;

-- fact: mmda.last
select max(date) from ph_traffic_incidents;

-- fact: mmda.days
select count(distinct date) from ph_traffic_incidents;

-- fact: mmda.span
select value from ph_traffic_coverage where property = 'calendar days in span';

-- fact: mmda.silent.days
-- Days inside the span with no report at all. Metro Manila did not have an
-- incident-free day; MMDA had a quiet one.
select (select value from ph_traffic_coverage
        where property = 'calendar days in span')::int
     - count(distinct date) from ph_traffic_incidents;

-- fact: mmda.cities
-- Distinct cities after the encoding repair. NCR has 17 local government units.
select count(*) from ph_traffic_by_city where city <> '(no city given)';

-- fact: mmda.missing.lgus
select 17 - (select count(*) from ph_traffic_by_city
             where city <> '(no city given)');

-- fact: mmda.locations
select count(distinct location) from ph_traffic_incidents where location <> '';

-- ---- the coverage problem ---------------------------------------------------

-- fact: mmda.top.city
select city from ph_traffic_by_city where city <> '(no city given)'
order by incidents desc limit 1;

-- fact: mmda.top.city.n
select incidents from ph_traffic_by_city where city <> '(no city given)'
order by incidents desc limit 1;

-- fact: mmda.top.city.pct
select pct_of_all from ph_traffic_by_city where city <> '(no city given)'
order by incidents desc limit 1;

-- fact: mmda.top4.pct
-- Four cities out of a possible seventeen carry most of the file.
select round(sum(pct_of_all), 2) from (
  select pct_of_all from ph_traffic_by_city where city <> '(no city given)'
  order by incidents desc limit 4);

-- fact: mmda.bottom.city
select city from ph_traffic_by_city where city <> '(no city given)'
order by incidents limit 1;

-- fact: mmda.bottom.city.n
select incidents from ph_traffic_by_city where city <> '(no city given)'
order by incidents limit 1;

-- ---- the faults, all counted ------------------------------------------------

-- fact: bad.mojibake
-- Rows whose city name arrived as UTF-8 bytes decoded as Latin-1.
select value from ph_traffic_coverage where property = 'city name double-encoded';

-- fact: bad.nullisland
select value from ph_traffic_coverage
where property = 'coordinates at exactly 0,0';

-- fact: bad.city
select value from ph_traffic_coverage where property = 'city missing';

-- fact: bad.type
select value from ph_traffic_coverage where property = 'incident type missing';

-- fact: bad.time.missing
select value from ph_traffic_coverage where property = 'time missing';

-- fact: bad.time.unparseable
select value from ph_traffic_coverage where property = 'time unparseable';

-- fact: bad.time.total
select (select value from ph_traffic_coverage where property = 'time missing')::int
     + (select value from ph_traffic_coverage
        where property = 'time unparseable')::int;

-- fact: mmda.mappable
select value from ph_traffic_coverage
where property = 'incidents usable on a map';

-- fact: mmda.timed
select value from ph_traffic_coverage
where property = 'incidents with a usable time';

-- fact: mmda.blank.months
select count(*) from ph_traffic_monthly where incidents = 0;

-- ---- when ------------------------------------------------------------------

-- fact: hour.peak
select hour from ph_traffic_hourly order by incidents desc limit 1;

-- fact: hour.peak.n
select incidents from ph_traffic_hourly order by incidents desc limit 1;

-- fact: hour.peak.pct
select pct_of_timed from ph_traffic_hourly order by incidents desc limit 1;

-- fact: hour.lunch
-- The 1pm trough. Sharper than any hour either side of it.
select incidents from ph_traffic_hourly where hour = 13;

-- fact: hour.lunch.vs.peak
select round(100.0 * (select incidents from ph_traffic_hourly where hour = 13)
           / (select max(incidents) from ph_traffic_hourly), 1);

-- fact: hour.quiet
select hour from ph_traffic_hourly order by incidents limit 1;

-- fact: hour.quiet.n
select incidents from ph_traffic_hourly order by incidents limit 1;

-- fact: band.morning
-- 06:00-09:59 as a share of timed incidents.
select round(sum(pct_of_timed), 2) from ph_traffic_hourly
where hour between 6 and 9;

-- fact: band.evening
select round(sum(pct_of_timed), 2) from ph_traffic_hourly
where hour between 16 and 19;

-- fact: band.diff
select round((select sum(pct_of_timed) from ph_traffic_hourly
              where hour between 6 and 9)
           - (select sum(pct_of_timed) from ph_traffic_hourly
              where hour between 16 and 19), 2);

-- fact: dow.busiest
select day_of_week from ph_traffic_dow
order by incidents_per_reporting_day desc limit 1;

-- fact: dow.busiest.rate
select incidents_per_reporting_day from ph_traffic_dow
order by incidents_per_reporting_day desc limit 1;

-- fact: dow.quietest
select day_of_week from ph_traffic_dow
order by incidents_per_reporting_day limit 1;

-- fact: dow.quietest.rate
select incidents_per_reporting_day from ph_traffic_dow
order by incidents_per_reporting_day limit 1;

-- fact: dow.ratio
select round((select incidents_per_reporting_day from ph_traffic_dow
              order by incidents_per_reporting_day limit 1)
           / (select incidents_per_reporting_day from ph_traffic_dow
              order by incidents_per_reporting_day desc limit 1) * 100, 1);

-- ---- the lockdown -----------------------------------------------------------

-- fact: ecq.before
select incidents_per_reporting_day from ph_traffic_ecq where period = 'before ECQ';

-- fact: ecq.during
select incidents_per_reporting_day from ph_traffic_ecq
where period = 'ECQ and MECQ';

-- fact: ecq.after
select incidents_per_reporting_day from ph_traffic_ecq
where period = 'after MECQ';

-- fact: ecq.drop
select round(100.0 * (1 - (select incidents_per_reporting_day from ph_traffic_ecq
                          where period = 'ECQ and MECQ')
                       / (select incidents_per_reporting_day from ph_traffic_ecq
                          where period = 'before ECQ')), 1);

-- fact: ecq.recovery
-- Still this far below the pre-lockdown rate at the end of the file.
select round(100.0 * (1 - (select incidents_per_reporting_day from ph_traffic_ecq
                          where period = 'after MECQ')
                       / (select incidents_per_reporting_day from ph_traffic_ecq
                          where period = 'before ECQ')), 1);

-- fact: ecq.n
select incidents from ph_traffic_ecq where period = 'ECQ and MECQ';

-- fact: month.feb2020
select incidents from ph_traffic_monthly where month = '2020-02';

-- fact: month.apr2020
select incidents from ph_traffic_monthly where month = '2020-04';

-- fact: month.busiest
select month from ph_traffic_monthly order by incidents desc limit 1;

-- fact: month.busiest.n
select incidents from ph_traffic_monthly order by incidents desc limit 1;

-- ---- what kind of incident --------------------------------------------------

-- fact: type.top
select type_family from ph_traffic_by_type order by incidents desc limit 1;

-- fact: type.top.n
select incidents from ph_traffic_by_type order by incidents desc limit 1;

-- fact: type.top.pct
select pct_of_all from ph_traffic_by_type order by incidents desc limit 1;

-- fact: type.top.strings
-- How many distinct free-text spellings that one family covers. The published
-- figure of 11,781 accidents matched no exact-string count, which is what
-- happens when free text is counted as though it were a code list.
select distinct_raw_strings from ph_traffic_by_type
order by incidents desc limit 1;

-- fact: type.stalled
select incidents from ph_traffic_by_type where type_family = 'stalled vehicle';

-- fact: type.stalled.pct
select pct_of_all from ph_traffic_by_type where type_family = 'stalled vehicle';

-- fact: type.stalled.strings
select distinct_raw_strings from ph_traffic_by_type
where type_family = 'stalled vehicle';

-- fact: type.families
select count(*) from ph_traffic_by_type;

-- fact: type.strings
select count(distinct incident_type) from ph_traffic_incidents
where incident_type <> '';

-- ---- where -----------------------------------------------------------------

-- fact: loc.top
select location from ph_traffic_locations order by incidents desc limit 1;

-- fact: loc.top.n
select incidents from ph_traffic_locations order by incidents desc limit 1;

-- fact: loc.top.city
select city from ph_traffic_locations order by incidents desc limit 1;

-- fact: loc.edsa.pct
-- EDSA is one road. This is its share of every located incident in the file.
select round(100.0 * count(*) / (select count(*) from ph_traffic_incidents
                                 where location <> ''), 2)
from ph_traffic_incidents where location like 'EDSA%';

-- fact: loc.edsa.n
select count(*) from ph_traffic_incidents where location like 'EDSA%';

-- ---- the national counterweight ---------------------------------------------

-- fact: road.ph
select deaths_per_100k from ph_traffic_deaths
where country = 'Philippines' order by year desc limit 1;

-- fact: road.year
select max(year) from ph_traffic_deaths where country = 'Philippines';

-- fact: road.ph.2000
select deaths_per_100k from ph_traffic_deaths
where country = 'Philippines' and year = 2000;

-- fact: road.ph.change
select round(100.0 * ((select deaths_per_100k from ph_traffic_deaths
                       where country = 'Philippines' order by year desc limit 1)
                    / (select deaths_per_100k from ph_traffic_deaths
                       where country = 'Philippines' and year = 2000) - 1), 1);

-- fact: road.rank
-- Rank among the six compared countries, lowest death rate first.
select count(*) from ph_traffic_deaths a
where a.year = (select max(year) from ph_traffic_deaths where country = 'Philippines')
  and a.deaths_per_100k <= (select deaths_per_100k from ph_traffic_deaths
                            where country = 'Philippines'
                            order by year desc limit 1);

-- fact: road.n
select count(distinct country) from ph_traffic_deaths;

-- fact: road.worst
select country from ph_traffic_deaths
where year = (select max(year) from ph_traffic_deaths where country = 'Philippines')
order by deaths_per_100k desc limit 1;

-- fact: road.worst.rate
select deaths_per_100k from ph_traffic_deaths
where year = (select max(year) from ph_traffic_deaths where country = 'Philippines')
order by deaths_per_100k desc limit 1;

-- fact: road.rising
-- How many of the six had a higher rate in the last year than in 2000.
select count(*) from (
  select country from ph_traffic_deaths
  group by country
  having max(case when year = (select max(year) from ph_traffic_deaths) then deaths_per_100k end)
       > max(case when year = 2000 then deaths_per_100k end));
