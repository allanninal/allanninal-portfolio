-- Facts published on projects/trade-analysis.html

-- fact: trade.total.2024
select total_trade_usd_b from ph_trade_annual where year = 2024;

-- fact: trade.balance.2024
select trade_balance_usd_b from ph_trade_annual where year = 2024;

-- fact: trade.balance.2022
select trade_balance_usd_b from ph_trade_annual where year = 2022;

-- fact: trade.balance.2015
select trade_balance_usd_b from ph_trade_annual where year = 2015;

-- fact: trade.deficit.years
select count(*) from ph_trade_annual where trade_balance_usd_b < 0;

-- fact: trade.ratio.2024
select round(imports_usd_b / exports_usd_b, 2) from ph_trade_annual where year = 2024;

-- fact: trade.electronics.share
select share_pct from ph_export_composition_2024 where category = 'Electronic Products';

-- fact: trade.china.import.share
select share_pct from ph_import_partners_2023 where country = 'China';

-- fact: trade.china.import.value
select value_usd_b from ph_import_partners_2023 where country = 'China';

-- fact: trade.us.export.value
select value_usd_b from ph_export_partners_2023 where country = 'United States';

-- fact: trade.export.growth.2025
-- 2025 is exports-only in the source; imports for the year are not published
-- yet, which is why no 2025 balance or total appears anywhere on the page.
select round((( select exports_usd_b from ph_trade_annual where year = 2025)
            / (select exports_usd_b from ph_trade_annual where year = 2024) - 1) * 100, 1);

-- Prose figures.

-- fact: trade.manufactured.share
select share_pct from ph_export_composition_2024 where category = 'Manufactured Goods (incl. Electronics)';

-- fact: trade.us.export.share
select share_pct from ph_export_partners_2023 where country = 'United States';

-- fact: trade.indonesia.import.share
select share_pct from ph_import_partners_2023 where country = 'Indonesia';
