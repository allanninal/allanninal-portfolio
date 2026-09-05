-- Facts published on projects/global-water-analysis.html
--
-- Two rungs of the WHO/UNICEF service ladder. "At least basic" is an improved
-- source within a 30-minute round trip. "Safely managed" is the same source, on
-- the premises, available when needed, and free from contamination -- and it is
-- SDG indicator 6.1.1. Every fact below keeps them apart, because the argument
-- of the page is the distance between them and the places the strict one is
-- simply absent.

-- ---- the dataset -------------------------------------------------------------

-- fact: gw.countries
select count(*) from gw_country;

-- fact: gw.firstyear
select value from gw_coverage where property = 'first year';

-- fact: gw.lastyear
select value from gw_coverage where property = 'last year';

-- fact: gw.rows
select count(*) from gw_series;

-- fact: gw.crosschecked
select value from gw_coverage
where property = 'cross-checked country-year-indicator pairs';

-- fact: gw.worstdiff
select value from gw_coverage where property = 'worst cross-check disagreement';

-- fact: gw.onlygho
select value from gw_coverage where property = 'pairs only in WHO GHO';

-- fact: gw.onlywb
select value from gw_coverage where property = 'pairs only in the World Bank';

-- ---- the number that does not exist ------------------------------------------

-- fact: miss.countries
-- Countries with a basic drinking water figure and no safely-managed one.
select count(*) from gw_country
where water_basic_pct is not null and water_safely_managed_pct is null;

-- fact: miss.people
select round(sum(population) / 1e6) from gw_country
where water_basic_pct is not null and water_safely_managed_pct is null;

-- fact: miss.billion
select round(sum(population) / 1e9, 2) from gw_country
where water_basic_pct is not null and water_safely_managed_pct is null;

-- fact: miss.pct
select value from gw_coverage
where property = 'share of that population with no safely managed figure';

-- fact: have.basic
select count(*) from gw_country where water_basic_pct is not null;

-- fact: have.safely
select count(*) from gw_country where water_safely_managed_pct is not null;

-- fact: miss.top.country
select country from gw_country
where water_basic_pct is not null and water_safely_managed_pct is null
order by population desc limit 1;

-- fact: miss.top.people
select round(population / 1e6) from gw_country
where water_basic_pct is not null and water_safely_managed_pct is null
order by population desc limit 1;

-- fact: miss.top.basic
select water_basic_pct from gw_country
where water_basic_pct is not null and water_safely_managed_pct is null
order by population desc limit 1;

-- fact: miss.rich
-- High-income countries in the same position, which is what stops this being a
-- story about poor countries lacking survey capacity.
select count(*) from gw_country
where water_basic_pct is not null and water_safely_managed_pct is null
  and income_group = 'High income';

-- fact: miss.sanitation
select count(*) from gw_country
where sanitation_basic_pct is not null and sanitation_safely_managed_pct is null;

-- fact: miss.sanitation.people
select round(sum(population) / 1e6) from gw_country
where sanitation_basic_pct is not null and sanitation_safely_managed_pct is null;

-- ---- where both exist, the two rungs are far apart ---------------------------

-- fact: gap.top.country
select country from gw_country
where basic_minus_safely_pts is not null and population > 20000000
order by basic_minus_safely_pts desc limit 1;

-- fact: gap.top.basic
select water_basic_pct from gw_country
where basic_minus_safely_pts is not null and population > 20000000
order by basic_minus_safely_pts desc limit 1;

-- fact: gap.top.safely
select water_safely_managed_pct from gw_country
where basic_minus_safely_pts is not null and population > 20000000
order by basic_minus_safely_pts desc limit 1;

-- fact: gap.top.pts
select basic_minus_safely_pts from gw_country
where basic_minus_safely_pts is not null and population > 20000000
order by basic_minus_safely_pts desc limit 1;

-- fact: gap.median
-- The typical distance between the two rungs, among countries reporting both.
select round(median(basic_minus_safely_pts), 1) from gw_country
where basic_minus_safely_pts is not null;

-- fact: gap.over40
select count(*) from gw_country where basic_minus_safely_pts >= 40;

-- fact: gap.reporting
select count(*) from gw_country where basic_minus_safely_pts is not null;

-- fact: id.basic
select water_basic_pct from gw_country where iso3 = 'IDN';

-- fact: id.safely
select water_safely_managed_pct from gw_country where iso3 = 'IDN';

-- fact: id.people
select round(population / 1e6) from gw_country where iso3 = 'IDN';

-- fact: ph.basic
select water_basic_pct from gw_country where iso3 = 'PHL';

-- fact: ph.safely
select water_safely_managed_pct from gw_country where iso3 = 'PHL';

-- fact: ph.gap
select basic_minus_safely_pts from gw_country where iso3 = 'PHL';

-- ---- the world, and the target it is not going to meet -----------------------

-- fact: world.first
select round(pct, 2) from gw_world
where scope = 'GLOBAL' and residence = 'total'
  and indicator = 'water_safely_managed' and year = 2000;

-- fact: world.last
select round(pct, 2) from gw_world
where scope = 'GLOBAL' and residence = 'total'
  and indicator = 'water_safely_managed'
  and year = (select max(year) from gw_world
              where scope = 'GLOBAL' and indicator = 'water_safely_managed');

-- fact: world.rate
-- Percentage points a year, over the whole published series.
select round((( select pct from gw_world where scope = 'GLOBAL' and residence = 'total'
                and indicator = 'water_safely_managed'
                and year = (select max(year) from gw_world where scope = 'GLOBAL'
                            and indicator = 'water_safely_managed'))
            - ( select pct from gw_world where scope = 'GLOBAL' and residence = 'total'
                and indicator = 'water_safely_managed' and year = 2000))
           / (( select max(year) from gw_world where scope = 'GLOBAL'
                and indicator = 'water_safely_managed') - 2000), 2);

-- fact: world.arrival
-- The year universal safely-managed drinking water arrives if the last quarter
-- century's rate simply continues. SDG target 6.1 is 2030.
select round(( select max(year) from gw_world where scope = 'GLOBAL'
               and indicator = 'water_safely_managed')
           + (100 - ( select pct from gw_world where scope = 'GLOBAL' and residence = 'total'
                      and indicator = 'water_safely_managed'
                      and year = (select max(year) from gw_world where scope = 'GLOBAL'
                                  and indicator = 'water_safely_managed')))
           / ((( select pct from gw_world where scope = 'GLOBAL' and residence = 'total'
                 and indicator = 'water_safely_managed'
                 and year = (select max(year) from gw_world where scope = 'GLOBAL'
                             and indicator = 'water_safely_managed'))
             - ( select pct from gw_world where scope = 'GLOBAL' and residence = 'total'
                 and indicator = 'water_safely_managed' and year = 2000))
            / (( select max(year) from gw_world where scope = 'GLOBAL'
                 and indicator = 'water_safely_managed') - 2000)));

-- fact: world.late
select round(( select max(year) from gw_world where scope = 'GLOBAL'
               and indicator = 'water_safely_managed')
           + (100 - ( select pct from gw_world where scope = 'GLOBAL' and residence = 'total'
                      and indicator = 'water_safely_managed'
                      and year = (select max(year) from gw_world where scope = 'GLOBAL'
                                  and indicator = 'water_safely_managed')))
           / ((( select pct from gw_world where scope = 'GLOBAL' and residence = 'total'
                 and indicator = 'water_safely_managed'
                 and year = (select max(year) from gw_world where scope = 'GLOBAL'
                             and indicator = 'water_safely_managed'))
             - ( select pct from gw_world where scope = 'GLOBAL' and residence = 'total'
                 and indicator = 'water_safely_managed' and year = 2000))
            / (( select max(year) from gw_world where scope = 'GLOBAL'
                 and indicator = 'water_safely_managed') - 2000))) - 2030;

-- fact: back.count
-- Countries whose safely-managed share was lower in 2022 than in 2015, the year
-- the Sustainable Development Goals were adopted.
select count(*) from gw_series a join gw_series b using (iso3, indicator, residence)
where a.indicator = 'water_safely_managed' and a.residence = 'total'
  and a.year = 2015 and b.year = 2022 and b.pct < a.pct;

-- fact: back.of
select count(*) from gw_series a join gw_series b using (iso3, indicator, residence)
where a.indicator = 'water_safely_managed' and a.residence = 'total'
  and a.year = 2015 and b.year = 2022;

-- ---- urban and rural ---------------------------------------------------------

-- fact: world.urban
select round(pct, 2) from gw_world
where scope = 'GLOBAL' and residence = 'urban'
  and indicator = 'water_safely_managed' and year = 2022;

-- fact: world.rural
select round(pct, 2) from gw_world
where scope = 'GLOBAL' and residence = 'rural'
  and indicator = 'water_safely_managed' and year = 2022;

-- fact: world.rr.gap
select round(( select pct from gw_world where scope = 'GLOBAL' and residence = 'urban'
               and indicator = 'water_safely_managed' and year = 2022)
           - ( select pct from gw_world where scope = 'GLOBAL' and residence = 'rural'
               and indicator = 'water_safely_managed' and year = 2022), 2);

-- fact: rr.countries
select count(*) from gw_country
where water_safely_managed_rural_pct is not null
  and water_safely_managed_urban_pct is not null;

-- fact: rr.ruralahead
-- Countries where rural beats urban. Small, but not zero, and the page says so
-- rather than claiming a rule without exceptions.
select count(*) from gw_country
where water_safely_managed_rural_pct > water_safely_managed_urban_pct;

-- fact: rr.top.country
select country from gw_country
where water_safely_managed_rural_pct is not null
  and water_safely_managed_urban_pct is not null and population > 20000000
order by water_safely_managed_urban_pct - water_safely_managed_rural_pct desc limit 1;

-- fact: rr.top.urban
select water_safely_managed_urban_pct from gw_country
where water_safely_managed_rural_pct is not null
  and water_safely_managed_urban_pct is not null and population > 20000000
order by water_safely_managed_urban_pct - water_safely_managed_rural_pct desc limit 1;

-- fact: rr.top.rural
select water_safely_managed_rural_pct from gw_country
where water_safely_managed_rural_pct is not null
  and water_safely_managed_urban_pct is not null and population > 20000000
order by water_safely_managed_urban_pct - water_safely_managed_rural_pct desc limit 1;

-- ---- the bottom of the ladder ------------------------------------------------

-- fact: od.world
select round(pct, 2) from gw_world
where scope = 'GLOBAL' and residence = 'total' and indicator = 'open_defecation'
  and year = (select max(year) from gw_world
              where scope = 'GLOBAL' and indicator = 'open_defecation');

-- fact: od.world.2000
select round(pct, 2) from gw_world
where scope = 'GLOBAL' and residence = 'total' and indicator = 'open_defecation'
  and year = 2000;

-- fact: hw.missing
-- Basic handwashing is the thinnest series of the six, and the page says so
-- rather than drawing a world map out of a third of it.
select count(*) from gw_country where handwashing_basic_pct is null;

-- fact: hw.have
select count(*) from gw_country where handwashing_basic_pct is not null;
