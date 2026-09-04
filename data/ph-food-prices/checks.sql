-- check: vocabulary closure on rice variety
-- level: error
-- Any commodity name not on the committed list is a parse artifact until a
-- human says otherwise. This is what catches 'sGlutinous'.
select distinct commodity, count(*) as rows
from ph_rice_prices_daily
where commodity not in (
  'Basmati','Fancy','Glutinous','Japonica/Jasponica','Other Special','Premium',
  'Regular Milled','Special','Special/Fancy','Well Milled',
  'NFA (Regular milled)','NFA (Well milled)',
  'Premium (Yellow tag)','Regular milled (White tag)','Special (Blue tag)',
  'Well milled (White tag)',
  'P20 Benteng Bigas Meron Na','Premium (RFA5)','Regular Milled (RFA100)','Well Milled (RFA25)'
)
group by 1;

-- check: coverage continuity by year
-- level: warn
-- A year with source PDFs but no output rows means the parser stopped working
-- on that layout. Warn, not error, while the infographic era is a known gap.
select c.yr, c.n_files, coalesce(d.n_rows, 0) as n_rows
from (select strftime(date, '%Y') as yr, count(*) as n_files
      from ph_rice_prices_coverage group by 1) c
left join (select strftime(date, '%Y') as yr, count(*) as n_rows
           from ph_rice_prices_daily group by 1) d using (yr)
where coalesce(d.n_rows, 0) = 0 and c.n_files > 0;

-- check: per-series price envelope
-- level: warn
-- Deliberately per-commodity, not a global band. Basmati legitimately trades
-- at 215-250 PHP/kg; a global 10-200 check flags 173 good rows and teaches
-- everyone to ignore it.
-- Known standing exception: Basmati at 60.00 on 2025-11-14. Verified against
-- Daily-Price-Index-November-14-2025.pdf, which really does print 60.00 where
-- Basmati normally sits near 200. A source anomaly, not a parse error, so the
-- row stays and this check warns rather than blocks.
with band as (
  select commodity,
         quantile_cont(price_php_per_kg, 0.01) lo,
         quantile_cont(price_php_per_kg, 0.99) hi
  from ph_rice_prices_daily group by 1)
select r.date, r.commodity, r.price_php_per_kg
from ph_rice_prices_daily r join band b using (commodity)
where r.price_php_per_kg < b.lo * 0.5 or r.price_php_per_kg > b.hi * 2;

-- check: every row carries a source
-- level: error
select count(*) from ph_rice_prices_daily
where source_pdf is null or trim(source_pdf) = ''
having count(*) > 0;
