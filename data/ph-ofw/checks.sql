-- World Bank remittance and migration indicators.

-- check: every row carries a source
-- level: error
select year from ph_ofw_annual where source is null or trim(source) = '';

-- check: remittances are non-negative
-- level: error
select year, remittances_usd from ph_ofw_annual where remittances_usd < 0;

-- check: the remittance share of GDP reconciles with the dollar figures
-- level: error
-- Two independently published series. remittances_usd / gdp_usd must equal
-- remittances_pct_gdp; if it stops doing so, one was revised without the other.
select year, remittances_pct_gdp,
       round(100.0 * remittances_usd / gdp_usd, 3) implied
from ph_ofw_annual
where remittances_usd is not null and gdp_usd is not null and gdp_usd > 0
  and remittances_pct_gdp is not null
  and abs(remittances_pct_gdp - 100.0 * remittances_usd / gdp_usd) > 0.2;

-- check: the remittance share is plausible
-- level: error
select year, remittances_pct_gdp from ph_ofw_annual
where remittances_pct_gdp is not null
  and (remittances_pct_gdp < 0 or remittances_pct_gdp > 60);

-- check: net migration is overwhelmingly negative
-- level: error
-- The Philippines is a net sender, so a series that stopped being mostly
-- negative would mean the sign convention flipped -- easy to miss, because the
-- magnitudes stay plausible either way. Asserted on the balance of years rather
-- than on every year: see the warning below.
select count(*) positive, (select count(*) from ph_ofw_annual
                           where year >= 1990 and net_migration is not null) total
from ph_ofw_annual where year >= 1990 and net_migration > 0
having count(*) > (select count(*) * 0.25 from ph_ofw_annual
                   where year >= 1990 and net_migration is not null);

-- check: a few years of net migration are positive (known)
-- level: warn
-- 1998, 2010 and 2012 come back positive. These are not sign errors: the World
-- Bank estimates net migration from five-year interpolations between census
-- rounds, and the residual can flip in a single year without anything real
-- having reversed. Recorded rather than clipped to zero, because clipping would
-- hide how coarse this particular series is.
select year, net_migration from ph_ofw_annual
where year >= 1990 and net_migration > 0;

-- check: annual coverage is unbroken
-- level: error
select y from (select unnest(range(1977, 2026)) y) g
where y not in (select year from ph_ofw_annual);

-- check: the peer comparison uses one year for every country
-- level: error
select count(distinct year) from ph_ofw_peers having count(distinct year) > 1;

-- check: the peer comparison year is recent
-- level: error
-- Vietnam's remittance share series stops in 2004, and including it pinned the
-- whole comparison there -- a twenty-year-old snapshot presented as current.
-- This fails if any future peer does the same thing.
select max(year) from ph_ofw_peers
having max(year) < (select max(year) - 3 from ph_ofw_annual
                    where remittances_pct_gdp is not null);

-- check: remittances exceed net FDI (known)
-- level: warn
-- Every year on record, and by a widening margin. It is the central fact about
-- what migration is in this economy, so it is asserted rather than assumed.
select year, remittances_over_fdi from ph_ofw_annual
where remittances_over_fdi is not null
  and year = (select max(year) from ph_ofw_annual where remittances_over_fdi is not null)
  and remittances_over_fdi > 1;
