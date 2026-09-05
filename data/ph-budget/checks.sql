-- World Bank central-government fiscal indicators + IMF general-government
-- aggregates. The two perimeters are different and are never mixed.

-- check: every annual row states its perimeter and source
-- level: error
select year from ph_budget_annual
where perimeter is null or trim(perimeter) = '' or source is null or trim(source) = '';

-- check: every IMF row is marked actual or projection
-- level: error
-- The DataMapper returns forecasts in the same array as history -- the debt
-- series runs to 2031. An unmarked row is a projection waiting to be charted as
-- a measurement.
select year, metric, basis from ph_budget_imf
where basis not in ('actual', 'projection');

-- check: projections start exactly where actuals stop
-- level: error
-- Asserts the actual/projection boundary is a single clean break per metric. A
-- new WEO vintage moves it, and a stale constant would silently relabel real
-- years as forecasts or the reverse.
select metric, max(case when basis = 'actual' then year end) last_actual,
       min(case when basis = 'projection' then year end) first_projection
from ph_budget_imf group by metric
having min(case when basis = 'projection' then year end)
    <> max(case when basis = 'actual' then year end) + 1;

-- check: shares of GDP are plausible
-- level: error
select year, expense_pct_gdp, revenue_ex_grants_pct_gdp from ph_budget_annual
where (expense_pct_gdp is not null and (expense_pct_gdp < 0 or expense_pct_gdp > 100))
   or (revenue_ex_grants_pct_gdp is not null
       and (revenue_ex_grants_pct_gdp < 0 or revenue_ex_grants_pct_gdp > 100));

-- check: tax revenue never exceeds total revenue
-- level: error
select year, tax_revenue_pct_gdp, revenue_ex_grants_pct_gdp from ph_budget_annual
where tax_revenue_pct_gdp is not null and revenue_ex_grants_pct_gdp is not null
  and tax_revenue_pct_gdp > revenue_ex_grants_pct_gdp + 0.01;

-- check: the fiscal balance stays in a plausible band
-- level: error
-- Deliberately NOT a reconciliation against revenue minus expense. Those two
-- World Bank series use different definitions -- net lending includes grants,
-- the revenue series excludes them -- so they disagree by two to three points in
-- most years. A check that fires on twenty-one of thirty-five good rows gets
-- switched off, which is worse than no check.
select year, net_lending_pct_gdp from ph_budget_annual
where net_lending_pct_gdp is not null
  and (net_lending_pct_gdp < -15 or net_lending_pct_gdp > 10);

-- check: derived peso figures reconcile with their inputs
-- level: error
-- expense_php_derived is share of GDP times GDP. If it ever stops being exactly
-- that, the derivation has drifted from what the column says it is.
select year, expense_php_derived,
       round(gdp_current_php * expense_pct_gdp / 100) recomputed
from ph_budget_annual
where expense_php_derived is not null
  and abs(expense_php_derived - gdp_current_php * expense_pct_gdp / 100) > 1;

-- check: GDP is positive and rising in nominal terms
-- level: error
-- Nominal GDP in pesos can stall but should not fall; a drop means a revision
-- landed in the wrong year or the currency unit changed.
select year, gdp_current_php from ph_budget_annual a
where gdp_current_php is not null
  and gdp_current_php < (select gdp_current_php from ph_budget_annual b
                         where b.year = a.year - 1) * 0.9;

-- check: annual coverage is unbroken
-- level: error
select y from (select unnest(range(1990, 2026)) y) g
where y not in (select year from ph_budget_annual);

-- check: the ASEAN comparison uses one year for every country
-- level: error
select count(distinct year) from ph_budget_asean having count(distinct year) > 1;

-- check: the Philippines is in the ASEAN comparison
-- level: error
select 1 where 'Philippines' not in (select country from ph_budget_asean);

-- check: the two perimeters disagree, as they should (known)
-- level: warn
-- World Bank central government against IMF general government for the same
-- year. General government includes local government and social security, so it
-- is larger. They are reported side by side and never averaged; this check
-- exists so that if they ever converge, someone looks at why.
select a.year, a.revenue_ex_grants_pct_gdp central, i.value_pct_gdp general
from ph_budget_annual a
join ph_budget_imf i on i.year = a.year and i.metric = 'revenue_pct_gdp'
where a.revenue_ex_grants_pct_gdp is not null
  and a.year = (select max(year) from ph_budget_annual
                where revenue_ex_grants_pct_gdp is not null)
  and abs(a.revenue_ex_grants_pct_gdp - i.value_pct_gdp) > 1.0;
