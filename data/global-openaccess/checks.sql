-- Does "diamond" mean the journal charges nothing? The audit says often not.
--
-- The checks guard three things: that the six open-access states are treated as
-- six and not as "open" and "closed", that the audit is a two-way comparison with
-- a control group rather than a hunt for confirming cases, and that the sample the
-- headline rate is computed on is large enough to report.

-- check: every year row carries a source
-- level: error
select year, oa_status from oa_year where source is null or trim(source) = '';

-- check: every audited journal carries a source
-- level: error
select issn from oa_label_audit where source is null or trim(source) = '';

-- check: the six states are the six states
-- level: error
select distinct oa_status from oa_year
where oa_status not in ('diamond','gold','hybrid','bronze','green','closed');

-- check: each year's shares sum to a hundred
-- level: error
select year, round(sum(pct_of_year), 2) from oa_year
group by 1 having abs(sum(pct_of_year) - 100) > 0.05;

-- check: shares are percentages
-- level: error
select year, oa_status, pct_of_year from oa_year
where pct_of_year < 0 or pct_of_year > 100.01;

-- check: works are never negative
-- level: error
select year, oa_status, works from oa_year where works < 0;

-- check: the country parts sum to the country total
-- level: error
select iso2, works,
       diamond_works + gold_works + hybrid_works + bronze_works
     + green_works + closed_works parts
from oa_country
where abs(diamond_works + gold_works + hybrid_works + bronze_works
        + green_works + closed_works - works) > 1;

-- check: country percentages follow from country counts
-- level: error
select iso2, diamond_works, works, diamond_pct from oa_country
where abs(diamond_pct - 100.0 * diamond_works / works) > 0.02;

-- check: only the author-pays states carry article charges
-- level: error
-- The internal evidence that the six states are not interchangeable. gold and
-- hybrid are the ones that move money; if diamond, green, bronze or closed ever
-- carried a material share of paid charges, the classification would not mean
-- what the page says it means.
select oa_status, works, works_with_paid_apc, pct_with_paid_apc
from oa_status_apc
where oa_status in ('diamond', 'green', 'bronze', 'closed')
  and pct_with_paid_apc > 1.0;

-- check: gold and hybrid do carry them
-- level: error
select oa_status, pct_with_paid_apc from oa_status_apc
where oa_status in ('gold', 'hybrid') and pct_with_paid_apc < 20.0;

-- check: the audit is two-way
-- level: error
-- A sample of only fee-charging journals could show a high mislabel rate and mean
-- nothing, because there would be no control. Both arms have to be present.
select count(*) from oa_label_audit where doaj_charges_fee = 'no'
having count(*) < 20;

-- check: the audit is large enough to report a rate on
-- level: error
select count(*) from oa_label_audit having count(*) < 150;

-- check: every audited journal has a verdict that follows from its two fields
-- level: error
select issn, doaj_charges_fee, openalex_labels_diamond, verdict
from oa_label_audit
where verdict <> case when doaj_charges_fee = 'yes' and openalex_labels_diamond = 'yes'
                      then 'wrong' else 'consistent' end;

-- check: the diamond label follows from the share it was derived from
-- level: error
select issn, diamond_pct_of_works, openalex_labels_diamond from oa_label_audit
where (diamond_pct_of_works > 50) <> (openalex_labels_diamond = 'yes');

-- check: a hard-currency flag matches the currency
-- level: error
select issn, currency, hard_currency from oa_label_audit
where (currency in ('USD','EUR','GBP','CHF','AUD','CAD','JPY','SEK','NOK','DKK',
                    'NZD','SGD')) <> (hard_currency = 'yes');

-- check: the coverage rate matches the audited rows
-- level: error
select (select value from oa_coverage
        where property = 'fee-charging journals labelled diamond' and unit = 'count') stated,
       (select count(*) from oa_label_audit where verdict = 'wrong') actual
having stated <> actual;

-- check: the stated mislabel percentage is the one the rows give
-- level: error
select (select value from oa_coverage
        where property = 'fee-charging journals labelled diamond'
          and unit = 'percent') stated,
       round(100.0 * (select count(*) from oa_label_audit where verdict = 'wrong')
           / (select count(*) from oa_label_audit where doaj_charges_fee = 'yes'), 2) actual
having abs(stated - actual) > 0.02;

-- check: nearly half of what is labelled diamond charges a fee (known)
-- level: warn
-- The page's headline, kept in the check output.
select count(*) labelled_diamond,
       sum(case when doaj_charges_fee = 'yes' then 1 else 0 end) of_which_charge,
       round(100.0 * sum(case when doaj_charges_fee = 'yes' then 1 else 0 end)
             / count(*), 2) pct
from oa_label_audit where openalex_labels_diamond = 'yes';

-- check: the error tracks currency (known)
-- level: warn
select hard_currency,
       sum(case when doaj_charges_fee = 'yes' then 1 else 0 end) charging,
       sum(case when verdict = 'wrong' then 1 else 0 end) mislabelled
from oa_label_audit group by 1;

-- check: the label rarely misses a genuinely free journal (known)
-- level: warn
-- The other arm. The classification over-includes; it does not under-include, and
-- saying only the first half would be a different and less honest page.
select count(*) fee_free,
       sum(case when openalex_labels_diamond = 'yes' then 1 else 0 end) labelled_diamond
from oa_label_audit where doaj_charges_fee = 'no';

-- check: the audit stopped at the daily allowance (known)
-- level: warn
select property, value from oa_coverage
where property = 'audit stopped by the daily allowance';
