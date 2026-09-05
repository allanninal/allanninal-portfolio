-- Facts published on projects/fies-analysis.html
--
-- All from the 41,544 unweighted household records of the 2015 FIES public
-- microdata. Unweighted: these describe the sample, not the country.

-- fact: fies.households
select value from ph_fies_headline where metric = 'households';

-- fact: fies.median
select value from ph_fies_headline where metric = 'median_income';

-- fact: fies.mean
-- The mean sits far above the median because income is strongly right-skewed.
-- The page uses medians throughout and shows the mean only where the gap is
-- itself the point.
select value from ph_fies_headline where metric = 'mean_income';

-- fact: fies.skew
select round((select value from ph_fies_headline where metric = 'mean_income')
           / (select value from ph_fies_headline where metric = 'median_income'), 2);

-- fact: fies.p10
select value from ph_fies_headline where metric = 'p10_income';

-- fact: fies.p90
select value from ph_fies_headline where metric = 'p90_income';

-- fact: fies.p90p10
select round((select value from ph_fies_headline where metric = 'p90_income')
           / (select value from ph_fies_headline where metric = 'p10_income'), 1);

-- fact: fies.max
select value from ph_fies_headline where metric = 'max_income';

-- fact: fies.members
select value from ph_fies_headline where metric = 'median_household_size';

-- fact: fies.gini
select value from ph_fies_inequality where metric = 'gini';

-- fact: fies.top1
select value from ph_fies_inequality where metric = 'top_1pct_income_share';

-- fact: fies.d10.share
select income_share_pct from ph_fies_deciles where decile = 10;

-- fact: fies.d1.share
select income_share_pct from ph_fies_deciles where decile = 1;

-- fact: fies.decile.ratio
select round((select median_income from ph_fies_deciles where decile = 10)
           / (select median_income from ph_fies_deciles where decile = 1), 1);

-- fact: fies.d10.median
select median_income from ph_fies_deciles where decile = 10;

-- fact: fies.d1.median
select median_income from ph_fies_deciles where decile = 1;

-- fact: fies.food.d1
-- Engel's law: the share of income spent on food falls as income rises. It
-- holds monotonically across all ten deciles here, which checks.sql asserts.
select median_food_share_pct from ph_fies_food_share where decile = 1;

-- fact: fies.food.d10
select median_food_share_pct from ph_fies_food_share where decile = 10;

-- fact: fies.food.spread
select round((select median_food_share_pct from ph_fies_food_share where decile = 1)
           - (select median_food_share_pct from ph_fies_food_share where decile = 10), 2);

-- fact: fies.food.median
select value from ph_fies_headline where metric = 'median_food_spend';

-- fact: fies.agri.median
select value from ph_fies_inequality where metric = 'median_income_agricultural';

-- fact: fies.nonagri.median
select value from ph_fies_inequality where metric = 'median_income_non_agricultural';

-- fact: fies.agri.ratio
select round((select value from ph_fies_inequality where metric = 'median_income_non_agricultural')
           / (select value from ph_fies_inequality where metric = 'median_income_agricultural'), 2);

-- fact: fies.region.top
select region from ph_fies_regions order by median_income desc limit 1;

-- fact: fies.region.top.income
select median_income from ph_fies_regions order by median_income desc limit 1;

-- fact: fies.region.bottom
select trim(region) from ph_fies_regions order by median_income limit 1;

-- fact: fies.region.bottom.income
select median_income from ph_fies_regions order by median_income limit 1;

-- fact: fies.region.ratio
select round((select median_income from ph_fies_regions order by median_income desc limit 1)
           / (select median_income from ph_fies_regions order by median_income limit 1), 2);

-- fact: fies.regions
select count(*) from ph_fies_regions;

-- fact: fies.female.median
-- Female-headed households report a higher median income than male-headed ones.
-- Stated as an observation, not explained: the survey records who is named as
-- head, and the composition of the two groups differs in ways this data cannot
-- separate.
select median_income from ph_fies_head_sex where head_sex = 'Female';

-- fact: fies.male.median
select median_income from ph_fies_head_sex where head_sex = 'Male';

-- fact: fies.female.count
select households from ph_fies_head_sex where head_sex = 'Female';
