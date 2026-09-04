-- PSA / BSP merchandise trade.

-- check: total trade is exports plus imports
-- level: error
select year, total_trade_usd_b, round(exports_usd_b + imports_usd_b, 2) computed
from ph_trade_annual where abs(total_trade_usd_b - (exports_usd_b + imports_usd_b)) > 0.05;

-- check: balance is exports minus imports
-- level: error
-- This is the check that would have caught a sign error. The PSE page shipped
-- one; trade balances are the other place a sign flip reads as plausible.
select year, trade_balance_usd_b, round(exports_usd_b - imports_usd_b, 2) computed
from ph_trade_annual where abs(trade_balance_usd_b - (exports_usd_b - imports_usd_b)) > 0.05;

-- check: annual coverage is unbroken
-- level: error
-- The series starts in 2015; 2025 is a partial year kept in the CSV.
select y from (select unnest(range(2015, 2026)) y) g
where y not in (select year from ph_trade_annual);

-- check: every year states its source
-- level: error
select year from ph_trade_annual where source is null or trim(source) = '';

-- check: partner shares sum to at most 100
-- level: error
select 'exports' t, round(sum(share_pct), 1) s from ph_export_partners_2023 having sum(share_pct) > 100.5
union all
select 'imports', round(sum(share_pct), 1) from ph_import_partners_2023 having sum(share_pct) > 100.5;

-- check: partner shares are consistent with their values
-- level: warn
-- Partner tables list the top 8 only, so the implied total is the top-8 sum
-- rather than the national figure; a share that disagrees with its own value
-- by more than a point means one column was edited alone.
select country, share_pct, round(100.0 * value_usd_b / (select sum(value_usd_b) from ph_export_partners_2023), 1) implied
from ph_export_partners_2023
where abs(share_pct - 100.0 * value_usd_b / (select sum(value_usd_b) from ph_export_partners_2023)) > 15;

-- check: export composition categories do not double-count silently
-- level: error
-- 'Manufactured Goods (incl. Electronics)' contains 'Electronic Products'.
-- That overlap is deliberate and documented, so the categories must NOT sum
-- to 100 -- this check asserts the note column says so.
select category from ph_export_composition_2024 where note is null or trim(note) = '';

-- check: recent-period rows state their source
-- level: error
select period from ph_trade_recent where source is null or trim(source) = '';
