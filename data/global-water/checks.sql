-- Two rungs of the WHO/UNICEF service ladder, and the distance between them.
--
-- The checks guard three things: that the strict rung is never reported as
-- larger than the generous one it is a subset of, that a country missing from
-- the strict series is recorded as missing rather than as a zero, and that the
-- two publishers of these estimates are still saying the same thing.

-- check: every row carries a source
-- level: error
select iso3, year, indicator from gw_series
where source is null or trim(source) = '';

-- check: every country row carries a source
-- level: error
select iso3 from gw_country where source is null or trim(source) = '';

-- check: shares are percentages
-- level: error
select iso3, year, indicator, residence, pct from gw_series
where pct < 0 or pct > 100.01;

-- check: safely managed never exceeds at least basic
-- level: error
-- Safely managed is a strict subset of at least basic: the same improved source,
-- plus three further conditions. A country where the strict figure is larger has
-- had two different series joined together.
select s.iso3, s.year, s.residence, b.pct basic, s.pct safely
from gw_series s join gw_series b
  on b.iso3 = s.iso3 and b.year = s.year and b.residence = s.residence
 and b.indicator = 'water_basic'
where s.indicator = 'water_safely_managed' and s.pct > b.pct + 0.02;

-- check: safely managed sanitation never exceeds at least basic sanitation
-- level: error
select s.iso3, s.year, s.residence, b.pct basic, s.pct safely
from gw_series s join gw_series b
  on b.iso3 = s.iso3 and b.year = s.year and b.residence = s.residence
 and b.indicator = 'sanitation_basic'
where s.indicator = 'sanitation_safely_managed' and s.pct > b.pct + 0.02;

-- check: open defecation and basic sanitation cannot both be near-universal
-- level: error
-- Open defecation is the bottom rung and basic sanitation is above the middle;
-- they are mutually exclusive, so together they cannot exceed the population.
select b.iso3, b.year, b.pct basic, o.pct open_def
from gw_series b join gw_series o
  on o.iso3 = b.iso3 and o.year = b.year and o.residence = b.residence
 and o.indicator = 'open_defecation'
where b.indicator = 'sanitation_basic' and b.pct + o.pct > 100.02;

-- check: the gap column is arithmetic, not asserted
-- level: error
select iso3, water_basic_pct, water_safely_managed_pct, basic_minus_safely_pts
from gw_country
where basic_minus_safely_pts is not null
  and abs(basic_minus_safely_pts
          - (water_basic_pct - water_safely_managed_pct)) > 0.02;

-- check: a missing strict figure is recorded as missing, never as zero
-- level: error
-- This is the failure the whole page is about. A country with no safely-managed
-- estimate must be absent from the column, not present with a zero in it, or
-- every average computed over the column is wrong and quietly so.
select c.iso3, c.country, c.water_safely_managed_pct, v.status
from gw_country c join gw_coverage_country v using (iso3)
where v.has_water_safely_managed = 'no' and c.water_safely_managed_pct is not null;

-- check: the coverage file agrees with the country file
-- level: error
select c.iso3,
       c.water_safely_managed_pct is not null in_country,
       v.has_water_safely_managed in_coverage
from gw_country c join gw_coverage_country v using (iso3)
where (c.water_safely_managed_pct is not null)
   <> (v.has_water_safely_managed = 'yes');

-- check: the coverage file counts what the country file contains
-- level: error
select (select value from gw_coverage
        where property = 'countries with basic but no safely managed figure') stated,
       (select count(*) from gw_country
        where water_basic_pct is not null
          and water_safely_managed_pct is null) actual
having stated <> actual;

-- check: the stated missing population is the sum of the missing countries
-- level: error
select (select value from gw_coverage
        where property = 'population in those countries') stated,
       (select sum(population) from gw_country
        where water_basic_pct is not null
          and water_safely_managed_pct is null) actual
having abs(stated - actual) > 1;

-- check: every country appears once
-- level: error
select iso3, count(*) from gw_country group by 1 having count(*) > 1;

-- check: no aggregate leaked into the country table
-- level: error
-- WLD, SSF, LIC and the rest are World Bank aggregates. One of them counted as a
-- country would double-count the people in it and change every total on the page.
select iso3, country from gw_country
where iso3 in ('WLD','SSF','LIC','LMY','LMC','UMC','HIC','EAS','ECS','LCN','MEA',
               'NAC','SAS','ARB','EMU','EUU','OED','AFE','AFW','IBD','IBT','IDA',
               'IDB','IDX','LTE','MIC','PRE','PST','SST','TEA','TEC','TLA','TMN',
               'TSA','TSS','WLD');

-- check: the two publishers agree wherever they overlap
-- level: error
-- Same JMP estimates, two publications. Any disagreement means one of them has
-- shipped a different vintage, and the fetch script aborts rather than choosing.
select iso3, year, indicator, who_gho, world_bank, abs_diff
from gw_crosscheck
where indicator <> 'open_defecation' and abs_diff > 0.05;

-- check: open defecation agrees within what rounding can explain
-- level: error
-- GHO publishes this one at country level rounded to whole percent, so the two
-- copies can differ by up to half a point and no further.
select iso3, year, who_gho, world_bank, abs_diff from gw_crosscheck
where indicator = 'open_defecation' and abs_diff > 0.51;

-- check: the world series is monotonic in neither direction (known)
-- level: warn
-- Recorded because the page says progress is slow, not that it is uniform. Thirty
-- countries went backwards between 2015 and 2022 and the world total still rose.
select year, round(pct, 2) pct from gw_world
where scope = 'GLOBAL' and residence = 'total'
  and indicator = 'water_safely_managed'
order by year;

-- check: the strict rung is unreported for a large share of the world (known)
-- level: warn
-- The page's first claim, kept in the check output rather than only in prose.
select count(*) countries, round(sum(population) / 1e6) million_people
from gw_country
where water_basic_pct is not null and water_safely_managed_pct is null;

-- check: rural trails urban everywhere it is measured (known)
-- level: warn
select count(*) countries,
       sum(case when water_safely_managed_rural_pct
                   > water_safely_managed_urban_pct then 1 else 0 end) rural_ahead
from gw_country
where water_safely_managed_rural_pct is not null
  and water_safely_managed_urban_pct is not null;

-- check: neither publisher carries the whole series (known)
-- level: warn
select property, value from gw_coverage
where property in ('pairs only in WHO GHO', 'pairs only in the World Bank');
