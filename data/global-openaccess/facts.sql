-- Facts published on projects/global-openaccess-analysis.html
--
-- OpenAlex sorts every published work into six open-access states. One of them,
-- diamond, is supposed to mean the journal charges the author nothing, and it is
-- the one people cite when they say open access need not cost researchers money.
-- DOAJ asks journals that question directly. The audit facts below compare the
-- two, in both directions, on a sample with a control group.

-- ---- the six states ----------------------------------------------------------

-- fact: oa.year
select value from oa_coverage where property = 'year analysed';

-- fact: oa.works
select value from oa_coverage where property = 'works in the year analysed';

-- fact: oa.free.pct
select value from oa_coverage
where property = 'open access, any kind' and unit = 'percent';

-- fact: dia.works
select works from oa_year where year = 2023 and oa_status = 'diamond';

-- fact: dia.pct
select pct_of_year from oa_year where year = 2023 and oa_status = 'diamond';

-- fact: gold.pct
select pct_of_year from oa_year where year = 2023 and oa_status = 'gold';

-- fact: hybrid.pct
select pct_of_year from oa_year where year = 2023 and oa_status = 'hybrid';

-- fact: bronze.pct
select pct_of_year from oa_year where year = 2023 and oa_status = 'bronze';

-- fact: closed.pct
select pct_of_year from oa_year where year = 2023 and oa_status = 'closed';

-- fact: closed.2015
select pct_of_year from oa_year where year = 2015 and oa_status = 'closed';

-- fact: dia.2015
select pct_of_year from oa_year where year = 2015 and oa_status = 'diamond';

-- ---- only two of the six move money ------------------------------------------

-- fact: gold.apc.pct
select pct_with_paid_apc from oa_status_apc where oa_status = 'gold';

-- fact: hybrid.apc.pct
select pct_with_paid_apc from oa_status_apc where oa_status = 'hybrid';

-- fact: dia.apc.pct
-- Diamond works almost never carry a recorded charge, which is the internal
-- evidence that the label is meant to mean what it says.
select pct_with_paid_apc from oa_status_apc where oa_status = 'diamond';

-- fact: closed.apc.pct
select pct_with_paid_apc from oa_status_apc where oa_status = 'closed';

-- ---- what DOAJ says when asked directly --------------------------------------

-- fact: doaj.journals
select value from oa_coverage where property = 'DOAJ journals';

-- fact: doaj.free
select value from oa_coverage
where property = 'DOAJ journals charging no author fee' and unit = 'journals';

-- fact: doaj.free.pct
select value from oa_coverage
where property = 'DOAJ journals charging no author fee' and unit = 'percent';

-- ---- the audit ---------------------------------------------------------------

-- fact: audit.n
select count(*) from oa_label_audit;

-- fact: audit.charging
select count(*) from oa_label_audit where doaj_charges_fee = 'yes';

-- fact: audit.free
select count(*) from oa_label_audit where doaj_charges_fee = 'no';

-- fact: wrong.n
select count(*) from oa_label_audit where verdict = 'wrong';

-- fact: wrong.pct
select round(100.0 * (select count(*) from oa_label_audit where verdict = 'wrong')
           / (select count(*) from oa_label_audit where doaj_charges_fee = 'yes'), 2);

-- fact: labelled.diamond
select count(*) from oa_label_audit where openalex_labels_diamond = 'yes';

-- fact: labelled.but.charges
-- The headline: of the journals the label calls free to publish in, how many
-- charge. This is the direction that matters, because it is the direction a
-- reader of the label is misled in.
select round(100.0 * (select count(*) from oa_label_audit
                      where openalex_labels_diamond = 'yes' and doaj_charges_fee = 'yes')
           / (select count(*) from oa_label_audit
              where openalex_labels_diamond = 'yes'), 2);

-- fact: hard.pct
select round(100.0 * (select count(*) from oa_label_audit
                      where verdict = 'wrong' and hard_currency = 'yes')
           / (select count(*) from oa_label_audit
              where doaj_charges_fee = 'yes' and hard_currency = 'yes'), 2);

-- fact: soft.pct
select round(100.0 * (select count(*) from oa_label_audit
                      where verdict = 'wrong' and hard_currency = 'no')
           / (select count(*) from oa_label_audit
              where doaj_charges_fee = 'yes' and hard_currency = 'no'), 2);

-- fact: soft.over.hard
select round((select 1.0 * count(*) from oa_label_audit
              where verdict = 'wrong' and hard_currency = 'no')
           / nullif((select count(*) from oa_label_audit
                     where doaj_charges_fee = 'yes' and hard_currency = 'no'), 0)
           / ((select 1.0 * count(*) from oa_label_audit
               where verdict = 'wrong' and hard_currency = 'yes')
            / nullif((select count(*) from oa_label_audit
                      where doaj_charges_fee = 'yes' and hard_currency = 'yes'), 0)), 1);

-- fact: control.free
select count(*) from oa_label_audit where doaj_charges_fee = 'no';

-- fact: control.right
-- The other arm: the label rarely misses a genuinely free journal. It
-- over-includes rather than under-includes, and the page says both.
select count(*) from oa_label_audit
where doaj_charges_fee = 'no' and openalex_labels_diamond = 'yes';

-- ---- what the label does to the country map ----------------------------------

-- fact: id.dia
select diamond_pct from oa_country where iso2 = 'ID';

-- fact: id.works
select works from oa_country where iso2 = 'ID';

-- fact: de.dia
select diamond_pct from oa_country where iso2 = 'DE';

-- fact: nl.dia
select diamond_pct from oa_country where iso2 = 'NL';

-- fact: ph.dia
select diamond_pct from oa_country where iso2 = 'PH';

-- fact: id.over.de
select round((select diamond_pct from oa_country where iso2 = 'ID')
           / (select diamond_pct from oa_country where iso2 = 'DE'), 1);

-- fact: idr.charging
-- Indonesian-rupiah journals in the audit that charge a fee, and how many carry
-- the label anyway. Indonesia is the country the diamond map puts first.
select count(*) from oa_label_audit
where doaj_charges_fee = 'yes' and currency = 'IDR';

-- fact: idr.wrong
select count(*) from oa_label_audit where verdict = 'wrong' and currency = 'IDR';

-- ---- what this is not --------------------------------------------------------

-- fact: audit.budgetlimited
select value from oa_coverage where property = 'audit stopped by the daily allowance';

-- fact: audit.absent
select value from oa_coverage where property = 'sampled journals absent from OpenAlex';
