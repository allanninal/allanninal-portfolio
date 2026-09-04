-- Facts published on projects/stock-market-analysis.html
-- Each query must return exactly one value.

-- fact: pse.close.2025
select close from ph_psei_annual where year = 2025;

-- fact: pse.close.2024
select close from ph_psei_annual where year = 2024;

-- fact: pse.close.2021
select close from ph_psei_annual where year = 2021;

-- fact: pse.record.close
select round(max(close), 2) from ph_psei_daily;

-- fact: pse.decade.return
select round((( select close from ph_psei_annual where year = 2024)
            / (select close from ph_psei_annual where year = 2014) - 1) * 100, 2);

-- fact: pse.return.2014_2025
select return_2014_2025_pct from ph_asean_index_returns where index = 'PSEi';

-- fact: pse.sector.mining.2025
select change_pct from ph_psei_sector_annual where year = 2025 and code = 'M-O';

-- fact: pse.sector.holding.2025
select change_pct from ph_psei_sector_annual where year = 2025 and code = 'HDG';

-- fact: pse.sector.services.2025
select change_pct from ph_psei_sector_annual where year = 2025 and code = 'SVC';

-- fact: pse.sector.spread.2025
select round(max(change_pct) - min(change_pct), 0) from ph_psei_sector_annual
where year = 2025 and code not in ('PSEI','ALL');

-- fact: pse.vol.mining
select annualised_volatility_pct from ph_sector_volatility where index = 'Mining & Oil';

-- fact: pse.vol.industrial
select annualised_volatility_pct from ph_sector_volatility where index = 'Industrial';

-- fact: pse.ict.share
select share_of_domestic_pct from ph_pse_marketcap_top20 where ticker = 'ICT';

-- fact: pse.ict.cap.t
select round(market_cap_php / 1e12, 2) from ph_pse_marketcap_top20 where ticker = 'ICT';

-- fact: pse.turnover.2021
select round(avg_daily_value_php / 1e9, 2) from ph_pse_annual_indicators where year = 2021;

-- fact: pse.turnover.2025
select round(avg_daily_value_php / 1e9, 2) from ph_pse_annual_indicators where year = 2025;

-- fact: pse.foreign.5y
-- foreign_net_php is a MAGNITUDE; the sign lives in foreign_direction. Summing
-- the column raw returns +198.8 for five straight years of net selling, and the
-- verifier only caught it once it learned to read the minus in '-P198.8B'.
-- checks.sql now asserts the direction vocabulary so a 'net buying' year cannot
-- be added as a bare positive.
select round(sum(case when foreign_direction = 'net selling' then -foreign_net_php
                      else foreign_net_php end) / 1e9, 1)
from ph_pse_annual_indicators;

-- fact: pse.raised.2021
select round(capital_raised_php / 1e9, 2) from ph_pse_annual_indicators where year = 2021;

-- fact: pse.raised.2024
select round(capital_raised_php / 1e9, 2) from ph_pse_annual_indicators where year = 2024;

-- fact: pse.seasonality.dec
select avg_return_pct from ph_psei_seasonality where month = 'Dec';

-- fact: pse.seasonality.aug
select avg_return_pct from ph_psei_seasonality where month = 'Aug';

-- fact: pse.seasonality.aug.positive
select positive_share_pct from ph_psei_seasonality where month = 'Aug';

-- fact: pse.pe.low
select min(pe_ratio) from ph_psei30_fundamentals where pe_ratio > 0;

-- fact: pse.pe.high
select max(pe_ratio) from ph_psei30_fundamentals;

-- fact: pse.breadth.best
select advancing from ph_pse_breadth_monthly where year = 2024
order by advancing_share_pct desc limit 1;

-- fact: pse.breadth.worst
select advancing from ph_pse_breadth_monthly where year = 2024
order by advancing_share_pct limit 1;
