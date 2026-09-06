-- Mirror statistics: the same trade, reported twice, by the two countries doing it.
--
-- The checks guard three things: that the two sides are only ever compared like
-- with like, that the FOB comparison is never quietly run on the CIF column, and
-- that a gap is arithmetic from two published figures rather than an assertion.

-- check: every flow row carries a source
-- level: error
select reporter_code, partner_code, flow from tm_flow
where source is null or trim(source) = '';

-- check: every pair carries a source
-- level: error
select exporter_iso, importer_iso from tm_pair
where source is null or trim(source) = '';

-- check: flows are one of two directions
-- level: error
select distinct flow from tm_flow where flow not in ('X', 'M');

-- check: values are positive
-- level: error
select reporter_code, partner_code, flow, primary_value_usd from tm_flow
where primary_value_usd is not null and primary_value_usd <= 0;

-- check: a country is never its own trading partner
-- level: error
select exporter_iso, importer_iso from tm_pair where exporter_iso = importer_iso;

-- check: every pair appears once
-- level: error
select exporter_iso, importer_iso, count(*) from tm_pair
group by 1, 2 having count(*) > 1;

-- check: FOB never exceeds CIF for the same import
-- level: error
-- CIF is FOB plus freight and insurance, so it cannot be the smaller of the two.
-- If it ever is, the two columns have been swapped somewhere upstream and the
-- whole valuation argument on the page inverts.
select exporter_iso, importer_iso, importer_reported_fob_usd, importer_reported_cif_usd
from tm_pair
where importer_reported_fob_usd is not null
  and importer_reported_fob_usd > importer_reported_cif_usd * 1.0001;

-- check: the CIF gap is arithmetic
-- level: error
select exporter_iso, importer_iso, exporter_reported_usd, importer_reported_cif_usd,
       gap_cif_usd
from tm_pair
where abs(gap_cif_usd - (importer_reported_cif_usd - exporter_reported_usd)) > 1;

-- check: the CIF gap percentage is arithmetic
-- level: error
select exporter_iso, importer_iso, gap_cif_usd, exporter_reported_usd, gap_cif_pct
from tm_pair
where abs(gap_cif_pct - 100.0 * gap_cif_usd / exporter_reported_usd) > 0.02;

-- check: the FOB gap is arithmetic where it exists
-- level: error
select exporter_iso, importer_iso, gap_fob_usd, importer_reported_fob_usd,
       exporter_reported_usd
from tm_pair
where gap_fob_usd is not null
  and abs(gap_fob_usd - (importer_reported_fob_usd - exporter_reported_usd)) > 1;

-- check: an FOB gap exists only where an FOB value does
-- level: error
-- The comparison that removes the freight margin runs on a subset, and the page
-- says so. A row with a FOB gap and no FOB value would mean the subset had been
-- silently backfilled from the CIF column.
select exporter_iso, importer_iso from tm_pair
where (gap_fob_usd is null) <> (importer_reported_fob_usd is null);

-- check: the coverage totals match the pair rows
-- level: error
select (select value from tm_coverage where property = 'matched pairs') stated,
       (select count(*) from tm_pair) actual
having stated <> actual;

-- check: the stated exporter-side total is the sum of the pairs
-- level: error
select (select value from tm_coverage
        where property = 'matched pairs, exporter side') stated,
       (select sum(exporter_reported_usd) from tm_pair) actual
having abs(stated - actual) > 1;

-- check: the stated median gap is the median of the pairs
-- level: error
select (select value from tm_coverage
        where property = 'median absolute gap, CIF') stated,
       round((select median(abs(gap_cif_pct)) from tm_pair), 2) actual
having abs(stated - actual) > 0.02;

-- check: every reporter in the pair table is in the reporter table
-- level: error
select distinct exporter_iso from tm_pair
where exporter_iso not in (select iso3 from tm_reporter);

-- check: ISO codes resolved
-- level: error
-- An empty ISO column does not raise anything; it just makes every per-country
-- filter match every row, which is how the first version reported an identical
-- median for all fifty-two reporters.
select count(*) from tm_reporter where iso3 is null or trim(iso3) = ''
having count(*) > 0;

-- check: the world does not balance with itself (known)
-- level: warn
-- The page's headline. Every export is an import, so these two totals describe
-- the same trade and cannot honestly differ.
select property, value, unit from tm_coverage
where property in ('reported exports, these reporters',
                   'reported imports, these reporters',
                   'import minus export, these reporters');

-- check: freight does not explain the gap (known)
-- level: warn
select property, value from tm_coverage
where property in ('median absolute gap, CIF', 'median absolute gap, FOB');

-- check: some reporters disagree with everybody (known)
-- level: warn
select reporter, median_abs_gap_cif_pct, pairs_as_exporter from tm_reporter
where pairs_as_exporter >= 25 order by median_abs_gap_cif_pct desc limit 8;

-- check: a country whose own totals disagree with its own detail (known)
-- level: warn
select reporter, flow, stated_world_total_usd, partner_rows_sum_usd, diff_pct
from tm_selfmismatch;
