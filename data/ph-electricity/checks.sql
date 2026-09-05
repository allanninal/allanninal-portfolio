-- check: Meralco rate plausibility
-- level: error
-- An all-in residential rate sits near P12-15/kWh. The generation charge is
-- written in the same "to P.. from P.. per kWh" shape and is about P7-8, so an
-- unanchored parser captures the wrong series. This band catches that.
select year, month, rate_php_per_kwh
from ph_meralco_monthly
where rate_php_per_kwh < 8 or rate_php_per_kwh > 20;

-- check: no duplicate months in the Meralco series
-- level: error
select year, month, count(*) as n
from ph_meralco_monthly group by 1,2 having count(*) > 1;

-- check: Ember area name still present
-- level: error
-- Ember calls the country "The Philippines". If that string ever changes the
-- upstream filter yields zero rows and every chart silently empties.
select 'no philippine rows in generation mix' as problem
from (select count(*) as n from ph_generation_mix) t
where t.n = 0;

-- check: generation shares are percentages
-- level: error
select year, fuel, share_pct from ph_generation_mix
where share_pct < 0 or share_pct > 100;

-- check: coal share covers the peer set
-- level: warn
select 'missing peer' as problem, a.area
from (select distinct area from sea_coal_share) a
where a.area not in ('Philippines','Thailand','Viet Nam','Indonesia','Malaysia','Singapore','ASEAN');
