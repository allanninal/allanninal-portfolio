-- World Bank health indicators for the Philippines.

-- check: every row carries a source
-- level: error
select year from ph_health_annual where source is null or trim(source) = '';

-- check: life expectancy is plausible and internally ordered
-- level: error
-- Female life expectancy exceeds male everywhere on earth. If that inverts, the
-- two columns have been swapped.
select year, life_expectancy_female, life_expectancy_male from ph_health_annual
where life_expectancy_female is not null and life_expectancy_male is not null
  and (life_expectancy_female <= life_expectancy_male
       or life_expectancy_female > 100 or life_expectancy_male < 20);

-- check: combined life expectancy sits between the sexes
-- level: error
select year, life_expectancy, life_expectancy_male, life_expectancy_female
from ph_health_annual
where life_expectancy is not null and life_expectancy_male is not null
  and (life_expectancy < life_expectancy_male - 0.5
       or life_expectancy > life_expectancy_female + 0.5);

-- check: under-5 mortality is at least infant mortality
-- level: error
-- Under-5 deaths include infant deaths by definition, so the first can never be
-- smaller. A violation means the two indicators were transposed.
select year, infant_mortality_per_1000, under5_mortality_per_1000
from ph_health_annual
where infant_mortality_per_1000 is not null and under5_mortality_per_1000 is not null
  and under5_mortality_per_1000 < infant_mortality_per_1000;

-- check: percentages stay inside 0-100
-- level: error
select year from ph_health_annual
where (measles_immunisation_pct is not null
       and (measles_immunisation_pct < 0 or measles_immunisation_pct > 100))
   or (out_of_pocket_pct_of_health_spend is not null
       and (out_of_pocket_pct_of_health_spend < 0 or out_of_pocket_pct_of_health_spend > 100))
   or (stunting_under5_pct is not null
       and (stunting_under5_pct < 0 or stunting_under5_pct > 100));

-- check: rates are non-negative
-- level: error
select year from ph_health_annual
where tb_incidence_per_100k < 0 or maternal_mortality_per_100k < 0
   or fertility_rate < 0 or health_spend_pct_gdp < 0;

-- check: annual coverage is unbroken for the core series
-- level: error
select y from (select unnest(range(1960, 2025)) y) g
where y not in (select year from ph_health_annual where life_expectancy is not null);

-- check: the ASEAN comparison uses one year for every country
-- level: error
select count(distinct year) from ph_health_asean having count(distinct year) > 1;

-- check: the Philippines is in the comparison
-- level: error
select 1 where 'Philippines' not in (select country from ph_health_asean);

-- check: TB incidence has risen since 2000 (known)
-- level: warn
-- Nearly every other indicator here improved. TB did not, and the page is built
-- on that contrast. Kept as a check so that if it ever reverses, the framing gets
-- revisited rather than quietly outliving the data.
select (select tb_incidence_per_100k from ph_health_annual where year = 2000) as y2000,
       (select tb_incidence_per_100k from ph_health_annual
        where tb_incidence_per_100k is not null order by year desc limit 1) as latest
where (select tb_incidence_per_100k from ph_health_annual
       where tb_incidence_per_100k is not null order by year desc limit 1)
    > (select tb_incidence_per_100k from ph_health_annual where year = 2000);
