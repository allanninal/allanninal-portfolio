-- 2015 FIES public microdata aggregates. Unweighted household records.

-- check: every row carries a source
-- level: error
select decile from ph_fies_deciles where source is null or trim(source) = '';

-- check: the sample size is intact
-- level: error
-- 41,544 households. A smaller number means the mirror changed or a filter
-- silently dropped rows, and every median on the page would shift with it.
select value from ph_fies_headline where metric = 'households' and value <> 41544;

-- check: deciles are complete and evenly sized
-- level: error
-- ntile splits as evenly as the row count allows, so no decile may differ from
-- another by more than one household.
select count(*) n, max(households) - min(households) spread from ph_fies_deciles
having count(*) <> 10 or max(households) - min(households) > 1;

-- check: decile income shares sum to 100
-- level: error
select round(sum(income_share_pct), 2) from ph_fies_deciles
having abs(sum(income_share_pct) - 100) > 0.05;

-- check: deciles are ordered by income
-- level: error
select a.decile from ph_fies_deciles a join ph_fies_deciles b on b.decile = a.decile + 1
where a.median_income > b.median_income or a.max_income > b.min_income;

-- check: mean income exceeds median
-- level: error
-- Income is strongly right-skewed, so the mean must sit above the median. If it
-- ever does not, the two were transposed -- and the page uses medians precisely
-- because the gap between them is large.
select (select value from ph_fies_headline where metric = 'mean_income') mean_v,
       (select value from ph_fies_headline where metric = 'median_income') median_v
where (select value from ph_fies_headline where metric = 'mean_income')
   <= (select value from ph_fies_headline where metric = 'median_income');

-- check: percentiles nest correctly
-- level: error
select 1 where (select value from ph_fies_headline where metric = 'p10_income')
             >= (select value from ph_fies_headline where metric = 'p90_income')
   or (select value from ph_fies_headline where metric = 'min_income')
    > (select value from ph_fies_headline where metric = 'p10_income')
   or (select value from ph_fies_headline where metric = 'max_income')
    < (select value from ph_fies_headline where metric = 'p90_income');

-- check: the Gini is in range
-- level: error
select value from ph_fies_inequality where metric = 'gini' and (value <= 0 or value >= 1);

-- check: food share falls monotonically across deciles (Engel's law)
-- level: error
-- The clearest result in this dataset and the page's central chart. A break
-- would mean the decile assignment or the ratio is wrong, since Engel's law
-- holds essentially without exception in household budget data.
select a.decile, a.median_food_share_pct, b.median_food_share_pct
from ph_fies_food_share a join ph_fies_food_share b on b.decile = a.decile + 1
where b.median_food_share_pct > a.median_food_share_pct;

-- check: food shares are plausible proportions
-- level: error
select decile, median_food_share_pct from ph_fies_food_share
where median_food_share_pct <= 0 or median_food_share_pct >= 100;

-- check: every region has enough households to report
-- level: error
select region, households from ph_fies_regions where households < 200;

-- check: spending categories are non-negative
-- level: error
select category from ph_fies_spending
where median_poorest_decile < 0 or median_richest_decile < 0;

-- check: the sample is unweighted (known)
-- level: warn
-- FIES ships sampling weights so results can be grossed up to the population.
-- This public extract does not include them, so every figure describes the
-- 41,544 sampled households and not the country. Recorded as a standing warning
-- because it is the single largest caveat on the page and is invisible in the
-- numbers themselves.
select 'unweighted' as basis, value households from ph_fies_headline
where metric = 'households';
