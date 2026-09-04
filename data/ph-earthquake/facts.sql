-- Facts published on projects/earthquake-analysis.html
--
-- Every rate figure is at M4.5+. The catalogue is not complete below that (see
-- checks.sql), so an M2.5+ count measures how good the seismometers were, not
-- how much the ground moved. The page says this in the open rather than quoting
-- the bigger, more impressive, meaningless number.

-- fact: eq.events.m45
select sum(m45plus) from ph_earthquakes_annual;

-- fact: eq.events.total
select sum(m25plus) from ph_earthquakes_annual;

-- fact: eq.years
select count(*) from ph_earthquakes_annual;

-- fact: eq.strongest
select max(mag) from ph_earthquakes;

-- fact: eq.strongest.year
select year(time_utc::timestamp) from ph_earthquakes order by mag desc limit 1;

-- fact: eq.m70plus
select sum(m70plus) from ph_earthquakes_annual;

-- fact: eq.m60plus
select sum(m60plus) from ph_earthquakes_annual;

-- fact: eq.peak.year
select year from ph_earthquakes_annual order by m45plus desc limit 1;

-- fact: eq.peak.count
select max(m45plus) from ph_earthquakes_annual;

-- fact: eq.rate.mean
select round(avg(m45plus), 0) from ph_earthquakes_annual where year < 2026;

-- fact: eq.band.m45
select share_pct from ph_earthquakes_magnitude_bands where band = 'M4.5-4.9';

-- fact: eq.band.m50
select share_pct from ph_earthquakes_magnitude_bands where band = 'M5.0-5.9';

-- fact: eq.band.m60
select share_pct from ph_earthquakes_magnitude_bands where band = 'M6.0-6.9';

-- fact: eq.depth.shallow
select share_pct from ph_earthquakes_depth_bands where band = 'shallow (<70 km)';

-- fact: eq.depth.intermediate
select share_pct from ph_earthquakes_depth_bands where band = 'intermediate (70-300 km)';

-- fact: eq.depth.deep
select share_pct from ph_earthquakes_depth_bands where band = 'deep (300+ km)';

-- fact: eq.depth.fixed10
-- USGS pins depth to exactly 10.0 km when it cannot resolve it. Nearly a
-- quarter of events carry that placeholder, so the shallow share is softer
-- than it looks and the page says so.
select share_pct from ph_earthquakes_depth_bands
where band = 'of which depth fixed at exactly 10.0 km';

-- fact: eq.lat.south
select share_pct from ph_earthquakes_latitude_bands where band = 'south (<10N)';

-- fact: eq.lat.central
select share_pct from ph_earthquakes_latitude_bands where band = 'central (10-13N)';

-- fact: eq.lat.north
select share_pct from ph_earthquakes_latitude_bands where band = 'north (13N+)';

-- fact: eq.magdepth.r
select distinct pearson_r_all_bands from ph_earthquakes_mag_depth;

-- fact: eq.dec.2000s.rate
select per_year from ph_earthquakes_decades where period = '2000-2009';

-- fact: eq.dec.2010s.rate
select per_year from ph_earthquakes_decades where period = '2010-2019';

-- fact: eq.dec.2020s.rate
select per_year from ph_earthquakes_decades where period = '2020-2026 (partial)';

-- fact: eq.dec.2000s.m60rate
select round(m60plus / years::double, 1) from ph_earthquakes_decades where period = '2000-2009';

-- fact: eq.dec.2020s.m60rate
select round(m60plus / years::double, 1) from ph_earthquakes_decades where period = '2020-2026 (partial)';

-- fact: eq.month.dec.raw
select share_pct from ph_earthquakes_monthly where month = 12;

-- fact: eq.month.dec.ex
select share_ex_aftershocks_pct from ph_earthquakes_monthly where month = 12;

-- fact: eq.month.expected
select distinct expected_pct from ph_earthquakes_monthly;

-- fact: eq.month.spread.ex
-- Largest minus smallest monthly share once aftershocks are removed. Under
-- 2.4 points across twelve months is what "no season" looks like numerically.
select round(max(share_ex_aftershocks_pct) - min(share_ex_aftershocks_pct), 2)
from ph_earthquakes_monthly;

-- fact: eq.aftershock.2023.count
select m45_next_30d from ph_earthquakes_aftershocks
where mainshock_utc = '2023-12-02T14:37:04';

-- fact: eq.aftershock.2023.ratio
select ratio from ph_earthquakes_aftershocks
where mainshock_utc = '2023-12-02T14:37:04';

-- fact: eq.aftershock.max.ratio
select max(ratio) from ph_earthquakes_aftershocks;

-- fact: eq.complete.m30
select events from ph_earthquakes_completeness where mag_bin = '3.0';

-- fact: eq.complete.m45
select events from ph_earthquakes_completeness where mag_bin = '4.5';
