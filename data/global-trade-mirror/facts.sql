-- Facts published on projects/global-trade-mirror-analysis.html
--
-- Every export is somebody's import. The two countries doing the same trade both
-- report it, and the numbers do not match. Some of the gap is definitional --
-- exports are valued FOB and imports CIF, so freight and insurance sit inside the
-- import figure -- and the FOB facts below are the comparison that removes it.

-- ---- the dataset -------------------------------------------------------------

-- fact: tm.year
select value from tm_coverage where property = 'year';

-- fact: tm.reporters
select value from tm_coverage where property = 'reporters read';

-- fact: tm.pairs
select value from tm_coverage where property = 'matched pairs';

-- fact: tm.flows
select value from tm_coverage where property = 'flow rows';

-- fact: tm.fobpairs
select value from tm_coverage where property = 'pairs with an importer FOB value';

-- ---- the world does not balance with itself ----------------------------------

-- fact: world.exports
select round(value / 1e12, 2) from tm_coverage
where property = 'reported exports, these reporters';

-- fact: world.imports
select round(value / 1e12, 2) from tm_coverage
where property = 'reported imports, these reporters';

-- fact: world.gap.bn
select round(value / 1e9) from tm_coverage
where property = 'import minus export, these reporters' and unit = 'usd';

-- fact: world.gap.pct
select value from tm_coverage
where property = 'import minus export, these reporters' and unit = 'percent';

-- ---- how far apart the two sides are -----------------------------------------

-- fact: median.cif
select value from tm_coverage where property = 'median absolute gap, CIF';

-- fact: median.fob
-- The same comparison with both sides on the same valuation. What is left is the
-- part shipping cannot explain.
select value from tm_coverage where property = 'median absolute gap, FOB';

-- fact: over10
select value from tm_coverage where property = 'pairs disagreeing by more than a tenth';

-- fact: over10.pct
select round(100.0 * (select value from tm_coverage
                      where property = 'pairs disagreeing by more than a tenth')
           / (select value from tm_coverage where property = 'matched pairs'), 1);

-- fact: over50
select value from tm_coverage where property = 'pairs disagreeing by more than a half';

-- fact: over100
-- Pairs where one side reports more than twice what the other does.
select count(*) from tm_pair where abs(gap_cif_pct) > 100;

-- ---- the pairs themselves ----------------------------------------------------
--
-- These are published on the page in billions, so they are returned in billions.
-- A query answering in dollars beside a page printing "$116.23B" would be a
-- mismatch the verifier reports on every rebuild, and the fix belongs here rather
-- than in a looser comparison.

-- fact: ph.us.exports
select round(exporter_reported_usd / 1e9, 2) from tm_pair
where exporter_iso = 'PHL' and importer_iso = 'USA';

-- fact: ph.us.imports
select round(importer_reported_cif_usd / 1e9, 2) from tm_pair
where exporter_iso = 'PHL' and importer_iso = 'USA';

-- fact: ph.us.fob
select round(importer_reported_fob_usd / 1e9, 2) from tm_pair
where exporter_iso = 'PHL' and importer_iso = 'USA';

-- fact: ph.us.pct
select gap_cif_pct from tm_pair where exporter_iso = 'PHL' and importer_iso = 'USA';

-- fact: ph.us.fobpct
select gap_fob_pct from tm_pair where exporter_iso = 'PHL' and importer_iso = 'USA';

-- fact: biggest.gap.exporter
-- The largest disagreement in dollars on any pair over five billion, between two
-- actual countries. Comtrade carries special reporting areas whose codes are not
-- real ISO3 -- "Other Asia, nes" is S19 -- and the shape of the code is what
-- excludes them. Matching on the name would have dropped IndoNESia and
-- PhilippiNES along with it.
select exporter from tm_pair where exporter_reported_usd > 5e9
  and regexp_matches(exporter_iso, '^[A-Z]{3}$')
  and regexp_matches(importer_iso, '^[A-Z]{3}$')
order by abs(gap_cif_usd) desc limit 1;

-- fact: biggest.gap.importer
select importer from tm_pair where exporter_reported_usd > 5e9
  and regexp_matches(exporter_iso, '^[A-Z]{3}$')
  and regexp_matches(importer_iso, '^[A-Z]{3}$')
order by abs(gap_cif_usd) desc limit 1;

-- fact: biggest.gap.said
select round(exporter_reported_usd / 1e9, 2) from tm_pair where exporter_reported_usd > 5e9
  and regexp_matches(exporter_iso, '^[A-Z]{3}$')
  and regexp_matches(importer_iso, '^[A-Z]{3}$')
order by abs(gap_cif_usd) desc limit 1;

-- fact: biggest.gap.heard
select round(importer_reported_cif_usd / 1e9, 2) from tm_pair where exporter_reported_usd > 5e9
  and regexp_matches(exporter_iso, '^[A-Z]{3}$')
  and regexp_matches(importer_iso, '^[A-Z]{3}$')
order by abs(gap_cif_usd) desc limit 1;

-- fact: biggest.gap.bn
select round(abs(gap_cif_usd) / 1e9, 1) from tm_pair where exporter_reported_usd > 5e9
  and regexp_matches(exporter_iso, '^[A-Z]{3}$')
  and regexp_matches(importer_iso, '^[A-Z]{3}$')
order by abs(gap_cif_usd) desc limit 1;

-- fact: sa.cn.said
select round(exporter_reported_usd / 1e9, 2) from tm_pair
where exporter_iso = 'SAU' and importer_iso = 'CHN';

-- fact: sa.cn.heard
select round(importer_reported_cif_usd / 1e9, 2) from tm_pair
where exporter_iso = 'SAU' and importer_iso = 'CHN';

-- fact: sa.cn.pct
select gap_cif_pct from tm_pair where exporter_iso = 'SAU' and importer_iso = 'CHN';

-- fact: nl.de.said
-- The opposite sign, and the reason a gap is not simply under-reporting: goods
-- landing at Rotterdam and moving on are Dutch exports and never German imports.
select round(exporter_reported_usd / 1e9, 2) from tm_pair
where exporter_iso = 'NLD' and importer_iso = 'DEU';

-- fact: nl.de.heard
select round(importer_reported_cif_usd / 1e9, 2) from tm_pair
where exporter_iso = 'NLD' and importer_iso = 'DEU';

-- fact: nl.de.pct
select gap_cif_pct from tm_pair where exporter_iso = 'NLD' and importer_iso = 'DEU';

-- ---- who disagrees with everybody --------------------------------------------

-- fact: worst.reporter
select reporter from tm_reporter where pairs_as_exporter >= 25
order by median_abs_gap_cif_pct desc limit 1;

-- fact: worst.reporter.pct
select median_abs_gap_cif_pct from tm_reporter where pairs_as_exporter >= 25
order by median_abs_gap_cif_pct desc limit 1;

-- fact: best.reporter
select reporter from tm_reporter where pairs_as_exporter >= 25
order by median_abs_gap_cif_pct limit 1;

-- fact: best.reporter.pct
select median_abs_gap_cif_pct from tm_reporter where pairs_as_exporter >= 25
order by median_abs_gap_cif_pct limit 1;

-- fact: worst.over.best
select round((select median_abs_gap_cif_pct from tm_reporter
              where pairs_as_exporter >= 25
              order by median_abs_gap_cif_pct desc limit 1)
           / (select median_abs_gap_cif_pct from tm_reporter
              where pairs_as_exporter >= 25
              order by median_abs_gap_cif_pct limit 1), 1);

-- ---- one country disagreeing with itself -------------------------------------

-- fact: self.reporter
select reporter from tm_selfmismatch order by abs(diff_pct) desc limit 1;

-- fact: self.stated
select round(stated_world_total_usd / 1e9, 2) from tm_selfmismatch
order by abs(diff_pct) desc limit 1;

-- fact: self.summed
select round(partner_rows_sum_usd / 1e9, 2) from tm_selfmismatch
order by abs(diff_pct) desc limit 1;

-- fact: self.pct
select diff_pct from tm_selfmismatch order by abs(diff_pct) desc limit 1;

-- fact: self.consistent
-- Reporter-flows whose partner detail does sum to their own published total.
select 104 - (select count(*) from tm_selfmismatch);
