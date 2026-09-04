-- FAOSTAT production/yield/area + World Bank agriculture indicators.

-- check: every production row carries a unit and a source
-- level: error
-- Units differ by element and item: tonnes for crops, 1000 head for some
-- livestock, kg/ha against kg/animal for yield. A row without its unit is a
-- number that cannot be charted safely.
select item, year from ph_agri_production
where unit is null or trim(unit) = '' or source is null or trim(source) = '';

-- check: no FAO aggregate items leaked into the crop tables
-- level: error
-- "Cereals, primary" contains "Rice"; "Fruit Primary" contains "Bananas".
-- Summing the item column with an aggregate present roughly doubles the
-- harvest, and the total still looks plausible.
select distinct item from ph_agri_production
where item ilike '%primary%' or item ilike '%, total%' or item = 'Meat, Total';

-- check: every named crop resolved to FAOSTAT rows
-- level: error
-- FAO renames items between releases -- "Garlic" is "Green garlic" here, and
-- the original name matched nothing at all. An unmatched crop vanishes from
-- every chart without erroring anywhere.
select item, status from ph_agri_coverage where status <> 'matched';

-- check: production values are positive
-- level: error
select item, year, value from ph_agri_production where value <= 0;

-- check: yields are positive and physically plausible
-- level: error
-- Crop yields are kg/ha. Above about 250,000 kg/ha is not a crop, it is a
-- unit error.
select item, year, value, unit from ph_agri_yield
where value <= 0 or (unit = 'kg/ha' and value > 250000);

-- check: production, area and yield are mutually consistent
-- level: warn
-- FAO computes yield as production over area, so the three should reconcile.
-- They are published independently and rounded separately, so small drift is
-- expected; more than 2% means one of the three was revised without the others.
select p.item, p.year, round(p.value, 0) production,
       round(a.value * y.value / 1000.0, 0) implied
from ph_agri_production p
join ph_agri_area a on a.item = p.item and a.year = p.year
join ph_agri_yield y on y.item = p.item and y.year = p.year
where a.value > 0 and p.value > 0
  and abs(p.value - a.value * y.value / 1000.0) / p.value > 0.02;

-- check: rice is present for every year of the modern series
-- level: error
select y from (select unnest(range(2000, 2025)) y) g
where y not in (select year from ph_agri_production where item = 'Rice');

-- check: the Philippines is in the regional yield comparison
-- level: error
select 1 where 'Philippines' not in (select country from ph_agri_rice_yield_asia);

-- check: economy shares stay within range
-- level: error
select year, agri_value_added_pct_gdp, agri_employment_pct from ph_agri_economy
where (agri_value_added_pct_gdp is not null
       and (agri_value_added_pct_gdp < 0 or agri_value_added_pct_gdp > 100))
   or (agri_employment_pct is not null
       and (agri_employment_pct < 0 or agri_employment_pct > 100));

-- check: the ASEAN comparison uses one year for every country
-- level: error
select count(distinct year) from ph_agri_asean having count(distinct year) > 1;

-- check: agriculture employs a far larger share than it produces (known)
-- level: warn
-- Not a data fault -- it is the finding. Agriculture is about a fifth of
-- employment and under a tenth of value added, and the gap is the productivity
-- story the page is built on. Kept as a check so that if it ever closes, the
-- page's argument gets revisited rather than silently outliving the data.
select year, agri_employment_pct, agri_value_added_pct_gdp
from ph_agri_economy
where agri_employment_pct is not null and agri_value_added_pct_gdp is not null
  and year = (select max(year) from ph_agri_economy where agri_employment_pct is not null)
  and agri_employment_pct > agri_value_added_pct_gdp * 1.5;

-- check: the unit column reads as text, not boolean
-- level: error
-- FAO writes tonnes as a bare "t". A column whose only value is "t" is inferred
-- as BOOLEAN by DuckDB, at which point `unit = 'tonnes'` matches nothing and
-- trim(unit) raises. The fetcher spells it out for that reason; this asserts it
-- stayed spelled out.
select distinct typeof(unit) from ph_agri_production where typeof(unit) <> 'VARCHAR';
