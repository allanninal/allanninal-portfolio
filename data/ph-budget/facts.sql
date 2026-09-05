-- Facts published on projects/budget-analysis.html
--
-- Two perimeters, never mixed. World Bank figures are CENTRAL government; IMF
-- figures are GENERAL government, which adds local government and social
-- security. They disagree by four to five points of GDP and are supposed to.
-- Every fact below is named for the perimeter it belongs to.
--
-- No figure here is a DBM budget number. DBM publishes the enacted General
-- Appropriations Act but not as a series any script can read, so peso amounts on
-- this page are derived -- a share of GDP times GDP in current pesos -- and the
-- page says so wherever one appears.

-- fact: bud.expense.pct
select expense_pct_gdp from ph_budget_annual
where expense_pct_gdp is not null order by year desc limit 1;

-- fact: bud.expense.year
select year from ph_budget_annual where expense_pct_gdp is not null order by year desc limit 1;

-- fact: bud.revenue.pct
select revenue_ex_grants_pct_gdp from ph_budget_annual
where revenue_ex_grants_pct_gdp is not null order by year desc limit 1;

-- fact: bud.revenue.year
select year from ph_budget_annual
where revenue_ex_grants_pct_gdp is not null order by year desc limit 1;

-- fact: bud.tax.pct
select tax_revenue_pct_gdp from ph_budget_annual
where tax_revenue_pct_gdp is not null order by year desc limit 1;

-- fact: bud.balance.pct
select net_lending_pct_gdp from ph_budget_annual
where net_lending_pct_gdp is not null order by year desc limit 1;

-- fact: bud.interest.pct
-- Interest as a share of central government EXPENSE, not of GDP. Close to one
-- peso in six of what the central government spends goes to servicing debt
-- before anything is delivered.
select interest_pct_of_expense from ph_budget_annual
where interest_pct_of_expense is not null order by year desc limit 1;

-- fact: bud.interest.year
select year from ph_budget_annual
where interest_pct_of_expense is not null order by year desc limit 1;

-- fact: bud.interest.pct.2022
select interest_pct_of_expense from ph_budget_annual where year = 2022;

-- fact: bud.interest.min
select min(interest_pct_of_expense) from ph_budget_annual;

-- fact: bud.expense.php
-- Derived: expense share of GDP times GDP in current pesos.
select round(expense_php_derived / 1e12, 2) from ph_budget_annual
where expense_php_derived is not null order by year desc limit 1;

-- fact: bud.revenue.php
select round(revenue_php_derived / 1e12, 2) from ph_budget_annual
where revenue_php_derived is not null order by year desc limit 1;

-- fact: bud.gdp.php
select round(gdp_current_php / 1e12, 2) from ph_budget_annual
where gdp_current_php is not null order by year desc limit 1;

-- fact: bud.debt.pct
select value_pct_gdp from ph_budget_imf
where metric = 'gross_debt_pct_gdp' and basis = 'actual' order by year desc limit 1;

-- fact: bud.debt.year
select year from ph_budget_imf
where metric = 'gross_debt_pct_gdp' and basis = 'actual' order by year desc limit 1;

-- fact: bud.debt.2019
select value_pct_gdp from ph_budget_imf
where metric = 'gross_debt_pct_gdp' and year = 2019;

-- fact: bud.debt.rise
select round((select value_pct_gdp from ph_budget_imf
              where metric = 'gross_debt_pct_gdp' and basis = 'actual'
              order by year desc limit 1)
           - (select value_pct_gdp from ph_budget_imf
              where metric = 'gross_debt_pct_gdp' and year = 2019), 1);

-- fact: bud.debt.php
-- Derived: general government gross debt share times GDP in current pesos, at
-- the latest year both exist.
select round((select value_pct_gdp from ph_budget_imf
              where metric = 'gross_debt_pct_gdp' and basis = 'actual'
              order by year desc limit 1)
           * (select gdp_current_php from ph_budget_annual
              where year = (select max(year) from ph_budget_imf
                            where metric = 'gross_debt_pct_gdp' and basis = 'actual'))
           / 100 / 1e12, 2);

-- fact: bud.debt.proj
select value_pct_gdp from ph_budget_imf
where metric = 'gross_debt_pct_gdp' and basis = 'projection' order by year limit 1;

-- fact: bud.debt.proj.year
select year from ph_budget_imf
where metric = 'gross_debt_pct_gdp' and basis = 'projection' order by year limit 1;

-- fact: bud.debt.peak
select max(value_pct_gdp) from ph_budget_imf
where metric = 'gross_debt_pct_gdp' and basis = 'actual';

-- fact: bud.asean.year
select distinct year from ph_budget_asean;

-- fact: bud.asean.rev.rank
select count(*) from ph_budget_asean
where revenue_pct_gdp >= (select revenue_pct_gdp from ph_budget_asean
                          where country = 'Philippines');

-- fact: bud.asean.rev
select revenue_pct_gdp from ph_budget_asean where country = 'Philippines';

-- fact: bud.asean.debt
select gross_debt_pct_gdp from ph_budget_asean where country = 'Philippines';

-- fact: bud.asean.idn.rev
select revenue_pct_gdp from ph_budget_asean where country = 'Indonesia';

-- fact: bud.asean.countries
select count(*) from ph_budget_asean;

-- fact: bud.interest.max
-- The real high, and it is at the START of the series. An earlier draft of this
-- page called the 2023 figure a record; the chart said otherwise the moment it
-- was rendered. The interest burden has fallen enormously since 1990 and has
-- recently turned back up, which is a different claim entirely.
select max(interest_pct_of_expense) from ph_budget_annual;

-- fact: bud.interest.max.year
select year from ph_budget_annual
order by interest_pct_of_expense desc nulls last limit 1;

-- fact: bud.interest.min.year
select year from ph_budget_annual
where interest_pct_of_expense is not null order by interest_pct_of_expense limit 1;

-- fact: bud.interest.rank
-- How many years had an interest share at least as high as the latest. 21 of 28
-- did: the current figure sits in the lower half of the series, not the top.
select count(*) from ph_budget_annual
where interest_pct_of_expense >= (select interest_pct_of_expense from ph_budget_annual
                                  where interest_pct_of_expense is not null
                                  order by year desc limit 1);

-- fact: bud.interest.years
select count(*) from ph_budget_annual where interest_pct_of_expense is not null;

-- fact: bud.debt.peak.year
select year from ph_budget_imf
where metric = 'gross_debt_pct_gdp' and basis = 'actual'
order by value_pct_gdp desc limit 1;
