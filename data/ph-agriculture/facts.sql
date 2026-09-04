-- Facts published on projects/agriculture-analysis.html
--
-- Tonnage comes from FAOSTAT, shares of GDP and employment from the World Bank.
-- They are never combined into a peso figure: converting FAO tonnage to value
-- would need farmgate prices this repository does not have, which is why no
-- "agricultural output in pesos" number appears anywhere on the page.

-- fact: agri.rice.2024
select round(value / 1e6, 2) from ph_agri_production where item = 'Rice' and year = 2024;

-- fact: agri.rice.1961
select round(value / 1e6, 2) from ph_agri_production where item = 'Rice' and year = 1961;

-- fact: agri.rice.multiple
select round((select value from ph_agri_production where item = 'Rice' and year = 2024)
           / (select value from ph_agri_production where item = 'Rice' and year = 1961), 1);

-- fact: agri.corn.2024
select round(value / 1e6, 2) from ph_agri_production where item = 'Maize (corn)' and year = 2024;

-- fact: agri.coconut.2024
select round(value / 1e6, 2) from ph_agri_production where item = 'Coconuts, in shell' and year = 2024;

-- fact: agri.sugar.2024
select round(value / 1e6, 2) from ph_agri_production where item = 'Sugar cane' and year = 2024;

-- fact: agri.banana.2024
select round(value / 1e6, 2) from ph_agri_production where item = 'Bananas' and year = 2024;

-- fact: agri.riceyield.ph
select round(value, 0) from ph_agri_yield where item = 'Rice' and year = 2024;

-- fact: agri.riceyield.vn
select round("yield", 0) from ph_agri_rice_yield_asia where country = 'Viet Nam' and year = 2024;

-- fact: agri.riceyield.gap
-- How far behind Vietnam, in percent. The single most useful number here: the
-- Philippines is not short of rice land, it is short of yield.
select round((1 - (select "yield" from ph_agri_rice_yield_asia
                   where country = 'Philippines' and year = 2024)
                / (select "yield" from ph_agri_rice_yield_asia
                   where country = 'Viet Nam' and year = 2024)) * 100, 0);

-- fact: agri.riceyield.rank
select count(*) from ph_agri_rice_yield_asia a
where a.year = 2024
  and a."yield" >= (select "yield" from ph_agri_rice_yield_asia
                    where country = 'Philippines' and year = 2024);

-- fact: agri.riceyield.countries
select count(*) from ph_agri_rice_yield_asia where year = 2024;

-- fact: agri.riceyield.ph.1961
select round("yield", 0) from ph_agri_rice_yield_asia where country = 'Philippines' and year = 1961;

-- fact: agri.ricearea.2024
select round(value / 1e6, 2) from ph_agri_area where item = 'Rice' and year = 2024;

-- fact: agri.ricearea.1961
select round(value / 1e6, 2) from ph_agri_area where item = 'Rice' and year = 1961;

-- fact: agri.gdp.share
select agri_value_added_pct_gdp from ph_agri_economy
where agri_value_added_pct_gdp is not null order by year desc limit 1;

-- fact: agri.gdp.share.year
select year from ph_agri_economy
where agri_value_added_pct_gdp is not null order by year desc limit 1;

-- fact: agri.gdp.share.1961
select agri_value_added_pct_gdp from ph_agri_economy
where agri_value_added_pct_gdp is not null order by year limit 1;

-- fact: agri.employment.share
select agri_employment_pct from ph_agri_economy
where agri_employment_pct is not null order by year desc limit 1;

-- fact: agri.productivity.gap
-- Employment share divided by value-added share. One means agriculture pays
-- like everything else; this is the number that says it does not.
select round((select agri_employment_pct from ph_agri_economy
              where agri_employment_pct is not null order by year desc limit 1)
           / (select agri_value_added_pct_gdp from ph_agri_economy
              where agri_value_added_pct_gdp is not null order by year desc limit 1), 1);

-- fact: agri.asean.year
select distinct year from ph_agri_asean;

-- fact: agri.asean.vn.employment
select agri_employment_pct from ph_agri_asean where country = 'Vietnam';

-- fact: agri.asean.my.employment
select agri_employment_pct from ph_agri_asean where country = 'Malaysia';

-- fact: agri.arable
select arable_ha_per_person from ph_agri_economy
where arable_ha_per_person is not null order by year desc limit 1;

-- fact: agri.crops
select count(distinct item) from ph_agri_production;

-- fact: agri.years
select count(distinct year) from ph_agri_production;

-- fact: agri.ricearea.multiple
select round((select value from ph_agri_area where item = 'Rice' and year = 2024)
           / (select value from ph_agri_area where item = 'Rice' and year = 1961), 2);

-- fact: agri.riceyield.multiple
select round((select value from ph_agri_yield where item = 'Rice' and year = 2024)
           / (select value from ph_agri_yield where item = 'Rice' and year = 1961), 1);
