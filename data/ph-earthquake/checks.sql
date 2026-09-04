-- USGS FDSN event catalogue for the Philippine region, and its aggregates.

-- check: every event carries a magnitude and a position
-- level: error
select id from ph_earthquakes
where mag is null or latitude is null or longitude is null;

-- check: every event carries its bounding box and source
-- level: error
-- The box is the definition of "Philippine earthquake" here. A row without it
-- cannot be re-derived or contested, which is the whole point of the column.
select id from ph_earthquakes
where box is null or trim(box) = '' or source is null or trim(source) = '';

-- check: events fall inside the stated bounding box
-- level: error
-- Asserts the query filter actually applied. A widened box would raise every
-- count on the page without erroring anywhere.
select id, latitude, longitude from ph_earthquakes
where latitude not between 4 and 22 or longitude not between 116 and 128;

-- check: magnitudes are physically plausible
-- level: error
select id, mag from ph_earthquakes where mag < 2.5 or mag > 9.5;

-- check: depths are physically plausible
-- level: error
-- The deepest earthquakes anywhere reach about 700 km; a negative depth above
-- a few km means a sign or unit error.
select id, depth_km from ph_earthquakes
where depth_km is not null and (depth_km < -5 or depth_km > 750);

-- check: no duplicate event ids
-- level: error
select id, count(*) from ph_earthquakes group by id having count(*) > 1;

-- check: annual coverage is unbroken
-- level: error
select y from (select unnest(range(2000, 2027)) y) g
where y not in (select year from ph_earthquakes_annual);

-- check: no year sits at the USGS 20,000-event response cap
-- level: error
-- The service returns exactly 20,000 rather than erroring when a window is too
-- large, so a year at the cap is a silently truncated year. The fetcher raises
-- on this too; asserted again here because the CSV outlives the fetch.
select year, events from ph_earthquakes_coverage where events >= 20000;

-- check: every year of the catalogue parsed
-- level: error
select year, status from ph_earthquakes_coverage where status <> 'parsed';

-- check: annual counts match the event table
-- level: error
-- Two independent aggregations. If derive.py is run against a stale event
-- table these drift, and every figure on the page comes from the aggregates.
select a.year, a.m25plus declared, e.n actual
from ph_earthquakes_annual a
join (select year, count(*) n from ph_earthquakes group by year) e on a.year = e.year
where a.m25plus <> e.n;

-- check: magnitude thresholds nest correctly
-- level: error
select year from ph_earthquakes_annual
where m40plus > m25plus or m45plus > m40plus or m50plus > m45plus
   or m60plus > m50plus or m70plus > m60plus;

-- check: band shares sum to 100
-- level: error
select round(sum(share_pct), 1) from ph_earthquakes_magnitude_bands
having abs(sum(share_pct) - 100) > 0.2;

-- check: latitude band shares sum to 100
-- level: error
select round(sum(share_pct), 1) from ph_earthquakes_latitude_bands
having abs(sum(share_pct) - 100) > 0.2;

-- check: monthly shares sum to 100 on both columns
-- level: error
select round(sum(share_pct), 2) raw, round(sum(share_ex_aftershocks_pct), 2) ex
from ph_earthquakes_monthly
having abs(sum(share_pct) - 100) > 0.2 or abs(sum(share_ex_aftershocks_pct) - 100) > 0.2;

-- check: the catalogue is incomplete below M4.5 (known, and load-bearing)
-- level: warn
-- Gutenberg-Richter requires counts to FALL as magnitude rises. They rise from
-- M3.0 to M4.5 instead, by three orders of magnitude, because the global network
-- does not detect small Philippine events. This is why every rate claim on the
-- page is made at M4.5+ and none at the M2.5 the catalogue nominally starts at.
-- Kept as a warning so the reason stays attached to the data rather than living
-- only in a comment: if it ever stops firing, the threshold should be revisited.
select c.mag_bin, c.events, n.mag_bin, n.events from ph_earthquakes_completeness c
join ph_earthquakes_completeness n on n.mag_bin::double = c.mag_bin::double + 0.5
where c.mag_bin not in ('6.0+') and n.mag_bin not in ('6.0+') and n.events > c.events;
