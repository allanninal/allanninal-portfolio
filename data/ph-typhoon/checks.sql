-- IBTrACS western Pacific tracks, restricted to a box around the Philippines.
-- Most of these checks guard the boundary between what the archive measures
-- (position and intensity) and what it does not (impact), and the boundary
-- between the satellite era and everything before it.

-- check: every row carries a source
-- level: error
select sid from ph_typhoon_storms where source is null or trim(source) = '';

-- check: every storm in the table actually reached the box
-- level: error
select sid, obs_in_box from ph_typhoon_storms where obs_in_box < 1;

-- check: storm ids are unique
-- level: error
select count(*) n, count(distinct sid) d from ph_typhoon_storms
having count(*) <> count(distinct sid);

-- check: seasons are within the archive's span
-- level: error
select sid, season from ph_typhoon_storms
where season < 1884 or season > 2024;

-- check: wind speeds are physically plausible
-- level: error
-- 200 kt has never been observed anywhere. A value above it means a unit error.
select sid, name, peak_wind_kt from ph_typhoon_storms
where peak_wind_kt is not null and (peak_wind_kt <= 0 or peak_wind_kt > 200);

-- check: Saffir-Simpson agrees with wind speed at the top of the scale
-- level: error
-- Category 5 begins at 137 kt. A storm flagged 5 with a lower peak wind, or one
-- above 137 kt not flagged 5, means the two columns have come apart.
select sid, name, peak_wind_kt, peak_sshs from ph_typhoon_storms
where peak_wind_kt is not null and peak_sshs is not null
  and ((peak_sshs = 5 and peak_wind_kt < 137)
       or (peak_wind_kt >= 137 and peak_sshs <> 5));

-- check: every pre-1945 storm is flagged pre-satellite
-- level: error
-- The era flag is what stops a chart being drawn across the point where the
-- observing system changed.
select sid, season, era from ph_typhoon_storms
where (season < 1980 and era <> 'pre-satellite')
   or (season >= 1980 and era <> 'satellite');

-- check: no intensity is claimed for storms that have none
-- level: error
-- 100% of pre-1945 observations carry no wind speed. A peak intensity appearing
-- for one would mean it had been imputed somewhere.
select sid, season, peak_wind_kt from ph_typhoon_storms
where season < 1945 and peak_wind_kt is not null;

-- check: seasonal box counts match the storm table
-- level: error
select s.season, s.storms_in_box, count(t.sid) actual
from ph_typhoon_seasons s
left join ph_typhoon_storms t on t.season = s.season
group by 1, 2 having s.storms_in_box <> count(t.sid);

-- check: storms in the box never exceed storms in the basin
-- level: error
select season, storms_in_basin, storms_in_box from ph_typhoon_seasons
where storms_in_box > storms_in_basin;

-- check: the archive's earliest seasons record no intensity at all
-- level: error
-- Asserted rather than assumed, because it is the whole reason the page starts
-- at 1980. If this ever stopped being true the era threshold should be revisited.
select season, pct_obs_without_wind from ph_typhoon_seasons
where season < 1940 and pct_obs_without_wind < 99.9;

-- check: monthly shares sum to 100
-- level: error
select round(sum(pct_of_storms), 2) from ph_typhoon_monthly
having abs(sum(pct_of_storms) - 100) > 0.05;

-- check: all twelve months are present
-- level: error
-- Including the quiet ones. A February with three storms is a finding; a missing
-- February is a chart with a hole in it.
select count(*) from ph_typhoon_monthly having count(*) <> 12;

-- check: intensity shares sum to 100
-- level: error
select round(sum(pct_of_storms), 2) from ph_typhoon_intensity
having abs(sum(pct_of_storms) - 100) > 0.05;

-- check: each storm is counted once in the intensity distribution
-- level: error
-- Counted at its own peak, not once per observation, which would weight a slow
-- storm more heavily than a fast one.
select sum(storms) from ph_typhoon_intensity
having sum(storms) <> (select count(*) from ph_typhoon_storms
                       where era = 'satellite' and peak_sshs is not null);

-- check: the strongest list is ordered and consistent
-- level: error
select rank, name, peak_wind_kt, prev from (
  select rank, name, peak_wind_kt, lag(peak_wind_kt) over (order by rank) prev
  from ph_typhoon_strongest)
where prev is not null and peak_wind_kt > prev;

-- check: kilometres per hour is converted, not typed
-- level: error
select name, peak_wind_kt, peak_wind_kmh from ph_typhoon_strongest
where abs(peak_wind_kmh - peak_wind_kt * 1.852) > 1;

-- check: every storm in the strongest list is category 5
-- level: warn
-- Recorded rather than asserted: the top of a 45-season list should be, and if it
-- ever is not that is worth seeing.
select rank, name, peak_sshs from ph_typhoon_strongest
where rank <= 10 and peak_sshs <> 5;

-- check: landfall counts never exceed storms in the box
-- level: error
select season, storms_in_box, storms_with_landfall_obs from ph_typhoon_landfall
where storms_with_landfall_obs > storms_in_box;

-- check: the landfall share is arithmetic
-- level: error
select season, storms_in_box, storms_with_landfall_obs, pct_with_landfall
from ph_typhoon_landfall
where storms_in_box > 0
  and abs(pct_with_landfall
          - 100.0 * storms_with_landfall_obs / storms_in_box) > 0.06;

-- check: coverage records that this archive carries no impact data
-- level: error
-- The page this replaced led with people affected and houses damaged. IBTrACS
-- has neither, and asserting the zero stops that returning.
select property, value from ph_typhoon_coverage
where property in ('deaths, damage or people affected',
                   'Philippine landfall points', 'official PAR polygon',
                   'PAGASA local storm names')
  and value <> 0;

-- check: most of the archive predates usable intensity data
-- level: warn
-- Why the page uses 957 storms rather than 2,905.
select property, value from ph_typhoon_coverage
where property = 'storms before 1945';
