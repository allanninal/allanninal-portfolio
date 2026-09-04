-- DOH/HDX case counts + ENA sequence metadata.

-- check: case counts are positive
-- level: error
select year, cases from ph_dengue_annual where cases is null or cases <= 0;

-- check: CFR is consistent with cases and deaths
-- level: error
-- Only 2016-2021 carry deaths. Where they do, the published CFR must be the
-- quotient -- a transcription slip here would put a plausible-looking but
-- wrong percentage on the page.
select year, cfr_pct, round(100.0 * deaths / cases, 2) computed
from ph_dengue_annual
where deaths is not null and abs(cfr_pct - 100.0 * deaths / cases) > 0.01;

-- check: every year states its coverage
-- level: error
-- Half these rows are partial years. A row without a coverage string is a row
-- that will be charted as if it were a full year.
select year from ph_dengue_annual where coverage is null or trim(coverage) = '';

-- check: every year states its source
-- level: error
select year from ph_dengue_annual where source is null or trim(source) = '';

-- check: annual coverage is unbroken
-- level: error
select y from (select unnest(range(2016, 2027)) y) g
where y not in (select year from ph_dengue_annual);

-- check: serotype rows add up to their stated total
-- level: error
select year, total, denv1 + denv2 + denv3 + denv4 + unspecified computed
from ph_dengue_ena_serotype_by_year
where total <> denv1 + denv2 + denv3 + denv4 + unspecified;

-- check: serotype shares match their own counts
-- level: error
-- The four shares are each over the year's TOTAL, which includes untyped
-- sequences -- so they sum to 100 only in years where nothing is untyped, and
-- asserting a flat 100 flagged 2011, 2012, 2015 and 2017 for being correct.
-- The real invariant is per-share: each share is its own count over the total.
select year, denv1_share_pct, round(100.0 * denv1 / total, 1) computed
from ph_dengue_ena_serotype_by_year
where total > 0 and abs(denv1_share_pct - 100.0 * denv1 / total) > 0.15
union all
select year, denv2_share_pct, round(100.0 * denv2 / total, 1)
from ph_dengue_ena_serotype_by_year
where total > 0 and abs(denv2_share_pct - 100.0 * denv2 / total) > 0.15
union all
select year, denv3_share_pct, round(100.0 * denv3 / total, 1)
from ph_dengue_ena_serotype_by_year
where total > 0 and abs(denv3_share_pct - 100.0 * denv3 / total) > 0.15
union all
select year, denv4_share_pct, round(100.0 * denv4 / total, 1)
from ph_dengue_ena_serotype_by_year
where total > 0 and abs(denv4_share_pct - 100.0 * denv4 / total) > 0.15;

-- check: sequence table and serotype table agree on the yearly count
-- level: error
-- Two independent aggregations of the same ENA pull. They must match; if the
-- serotype pivot is rebuilt without the sequence table they can drift.
select s.year, s.n seq_rows, t.total pivot_total
from (select year, count(*) n from ph_dengue_ena_sequences group by year) s
full join ph_dengue_ena_serotype_by_year t on s.year = t.year
where coalesce(s.n, -1) <> coalesce(t.total, -1);

-- check: study run counts sum to the run table
-- level: error
select (select sum(runs) from ph_dengue_ena_studies) declared,
       (select count(*) from ph_dengue_ena_runs) actual
where (select sum(runs) from ph_dengue_ena_studies) <> (select count(*) from ph_dengue_ena_runs);

-- check: serotype vocabulary closure
-- level: error
select distinct serotype from ph_dengue_ena_sequences
where serotype not in ('DENV-1', 'DENV-2', 'DENV-3', 'DENV-4', 'unspecified');

-- check: province names carry no leading or trailing whitespace
-- level: error
-- HDX ships several provinces as ' NEGROS ORIENTAL'. Unstripped, a province
-- appears twice and neither copy carries its real total.
select province from ph_dengue_top_provinces_2016_2021 where province <> trim(province)
union all
select region from ph_dengue_by_region_2016_2021 where region <> trim(region);

-- check: monthly seasonality covers all twelve months
-- level: error
select m from (select unnest(range(1, 13)) m) g
where m not in (select month from ph_dengue_monthly_seasonality);
