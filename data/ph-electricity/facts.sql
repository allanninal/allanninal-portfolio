-- Facts published on projects/electricity-analysis.html
-- Each query must return exactly one value.

-- fact: el.coal.2005
select share_pct from ph_generation_mix where year = 2005 and source = 'Coal';

-- fact: el.coal.2015
select share_pct from ph_generation_mix where year = 2015 and source = 'Coal';

-- fact: el.coal.2024
select share_pct from ph_generation_mix where year = 2024 and source = 'Coal';

-- fact: el.coal.2025
select share_pct from ph_generation_mix where year = 2025 and source = 'Coal';

-- fact: el.solar.2025
select share_pct from ph_generation_mix where year = 2025 and source = 'Solar';

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
