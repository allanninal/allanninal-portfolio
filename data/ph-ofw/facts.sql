-- Facts published on projects/ofw-analysis.html
--
-- DMW deployment statistics and PSA's Survey on Overseas Filipinos are the
-- proper sources for who migrates. Both are unreachable by script. These cover
-- what migration sends home, which is a narrower question the page states up
-- front.

-- fact: ofw.remit
select round(remittances_usd / 1e9, 2) from ph_ofw_annual
where remittances_usd is not null order by year desc limit 1;

-- fact: ofw.year
select max(year) from ph_ofw_annual where remittances_usd is not null;

-- fact: ofw.pct
select round(remittances_pct_gdp, 2) from ph_ofw_annual
where remittances_pct_gdp is not null order by year desc limit 1;

-- fact: ofw.pct.peak
select round(max(remittances_pct_gdp), 2) from ph_ofw_annual;

-- fact: ofw.pct.peak.year
select year from ph_ofw_annual order by remittances_pct_gdp desc nulls last limit 1;

-- fact: ofw.remit.1977
select round(remittances_usd / 1e6, 1) from ph_ofw_annual
where remittances_usd is not null order by year limit 1;

-- fact: ofw.first.year
select min(year) from ph_ofw_annual where remittances_usd is not null;

-- fact: ofw.vs.fdi
-- Remittances as a multiple of net foreign direct investment.
select round(remittances_over_fdi, 2) from ph_ofw_annual
where remittances_over_fdi is not null order by year desc limit 1;

-- fact: ofw.vs.exports
select round(100.0 * remittances_usd / exports_goods_services_usd, 1)
from ph_ofw_annual
where remittances_usd is not null and exports_goods_services_usd is not null
order by year desc limit 1;

-- fact: ofw.netmig
select abs(net_migration) from ph_ofw_annual
where net_migration is not null order by year desc limit 1;

-- fact: ofw.netmig.decade
-- Net outflow over the last ten years of data.
select abs(sum(net_migration)) from ph_ofw_annual
where net_migration is not null
  and year > (select max(year) - 10 from ph_ofw_annual where net_migration is not null);

-- fact: ofw.peers.year
select distinct year from ph_ofw_peers;

-- fact: ofw.peers.rank
select count(*) from ph_ofw_peers
where remittances_pct_gdp >= (select remittances_pct_gdp from ph_ofw_peers
                              where country = 'Philippines');

-- fact: ofw.peers.n
select count(*) from ph_ofw_peers;

-- fact: ofw.india.usd
select round(remittances_usd / 1e9, 1) from ph_ofw_peers where country = 'India';

-- fact: ofw.india.pct
select remittances_pct_gdp from ph_ofw_peers where country = 'India';

-- fact: ofw.years
select count(*) from ph_ofw_annual where remittances_usd is not null;
