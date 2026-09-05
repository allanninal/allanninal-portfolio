-- Facts published on projects/electricity-analysis.html
-- Each query must return exactly one value.

-- fact: el.coal.2005
select share_pct from ph_generation_mix where year = 2005 and fuel = 'Coal';

-- fact: el.coal.2015
select share_pct from ph_generation_mix where year = 2015 and fuel = 'Coal';

-- fact: el.coal.2024
select share_pct from ph_generation_mix where year = 2024 and fuel = 'Coal';

-- fact: el.coal.2025
select share_pct from ph_generation_mix where year = 2025 and fuel = 'Coal';

-- fact: el.solar.2025
select share_pct from ph_generation_mix where year = 2025 and fuel = 'Solar';

-- fact: el.coal.thailand
select coal_share_pct from sea_coal_share where area = 'Thailand' and year = 2025;

-- fact: el.coal.singapore
select coal_share_pct from sea_coal_share where area = 'Singapore' and year = 2025;

-- fact: el.coal.vietnam
select coal_share_pct from sea_coal_share where area = 'Viet Nam' and year = 2025;

-- fact: el.coal.malaysia
select coal_share_pct from sea_coal_share where area = 'Malaysia' and year = 2025;

-- fact: el.coal.vs.thailand
select round((select coal_share_pct from sea_coal_share where area = 'Philippines' and year = 2025)
           / (select coal_share_pct from sea_coal_share where area = 'Thailand' and year = 2025), 1);

-- fact: el.meralco.first
select rate_php_per_kwh from ph_meralco_monthly order by year, month limit 1;

-- fact: el.meralco.latest
select rate_php_per_kwh from ph_meralco_monthly order by year desc, month desc limit 1;

-- fact: el.meralco.rise.pct
select round((( select rate_php_per_kwh from ph_meralco_monthly order by year desc, month desc limit 1)
            / (select rate_php_per_kwh from ph_meralco_monthly order by year, month limit 1) - 1) * 100, 1);

-- fact: el.meralco.months
select count(*) from ph_meralco_monthly;

-- fact: el.ph.rows
select count(*) from ph_generation_mix;

-- fact: el.coal.rows
select count(*) from sea_coal_share;

-- Added when the page was deepened: the original version charted only coal and
-- omitted the finding below entirely.

-- fact: el.renew.2000
select renewable_pct from ph_generation_rollup where year = 2000;

-- fact: el.renew.latest
select renewable_pct from ph_generation_rollup order by year desc limit 1;

-- fact: el.renew.change
select round((select renewable_pct from ph_generation_rollup order by year desc limit 1)
           - (select renewable_pct from ph_generation_rollup where year = 2000), 1);

-- fact: el.fossil.latest
select fossil_pct from ph_generation_rollup order by year desc limit 1;

-- fact: el.total.2000
select total_twh from ph_generation_rollup where year = 2000;

-- fact: el.total.latest
select total_twh from ph_generation_rollup order by year desc limit 1;

-- fact: el.total.mult
select round((select total_twh from ph_generation_rollup order by year desc limit 1)
           / (select total_twh from ph_generation_rollup where year = 2000), 1);

-- fact: el.renew.twh.2000
select renewable_twh from ph_generation_rollup where year = 2000;

-- fact: el.renew.twh.latest
-- Renewable generation nearly doubled in absolute terms while its SHARE fell by
-- twenty points. Both are true; quoting either alone misleads.
select renewable_twh from ph_generation_rollup order by year desc limit 1;

-- fact: el.geothermal
-- Ember files Philippine geothermal under "Other renewables", which is why that
-- bucket is unusually large here.
select share_pct from ph_generation_mix
where fuel = 'Other renewables' and year = (select max(year) from ph_generation_mix);

-- fact: el.solar
select share_pct from ph_generation_mix
where fuel = 'Solar' and year = (select max(year) from ph_generation_mix);

-- fact: el.wind
select share_pct from ph_generation_mix
where fuel = 'Wind' and year = (select max(year) from ph_generation_mix);

-- fact: el.gas
select share_pct from ph_generation_mix
where fuel = 'Gas' and year = (select max(year) from ph_generation_mix);

-- fact: el.hydro
select share_pct from ph_generation_mix
where fuel = 'Hydro' and year = (select max(year) from ph_generation_mix);

-- fact: el.fuels
select count(distinct fuel) from ph_generation_mix;

-- fact: el.meralco.found
select months from ph_meralco_status where status = 'found';

-- fact: el.meralco.missing
select months from ph_meralco_status where status = 'not found';

-- fact: el.meralco.total
select sum(months) from ph_meralco_status;

-- fact: el.meralco.coverage.pct
select round(100.0 * (select months from ph_meralco_status where status = 'found')
           / (select sum(months) from ph_meralco_status), 0);
