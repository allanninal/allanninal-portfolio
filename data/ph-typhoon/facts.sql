-- Facts published on projects/typhoon-analysis.html
--
-- All from IBTrACS track data. Nothing here describes damage, because the archive
-- carries none. Keys named par.* are restricted to 1980 onward; keys named
-- arch.* describe the whole archive including the era whose data cannot be used.

-- ---- the archive, and why most of it cannot be used -------------------------

-- fact: arch.obs
select value from ph_typhoon_coverage
where property = 'observations in the archive';

-- fact: arch.storms
select value from ph_typhoon_coverage where property = 'storms in the archive';

-- fact: arch.first
select min(season) from ph_typhoon_seasons;

-- fact: arch.last
select value from ph_typhoon_coverage where property = 'last finalised season';

-- fact: arch.box
select value from ph_typhoon_coverage where property = 'storms entering the box';

-- fact: arch.pre1945
select value from ph_typhoon_coverage where property = 'storms before 1945';

-- fact: arch.pre1945.nowind
-- Percentage of pre-1945 observations with no wind speed at all.
select value from ph_typhoon_coverage
where property = 'observations before 1945 with no wind speed';

-- fact: arch.mid.nowind
select value from ph_typhoon_coverage
where property = 'observations 1945-1969 with no wind speed';

-- fact: arch.sat.nowind
select value from ph_typhoon_coverage
where property = 'observations since 1980 with no wind speed';

-- fact: era.start
select value from ph_typhoon_coverage
where property = 'first season used for rates and trends';

-- ---- storms in Philippine waters, satellite era ------------------------------

-- fact: par.storms
select count(*) from ph_typhoon_storms where era = 'satellite';

-- fact: par.years
select count(*) from ph_typhoon_seasons
where era = 'satellite' and storms_in_box is not null;

-- fact: par.per.year
select round(avg(storms_in_box), 2) from ph_typhoon_seasons where era = 'satellite';

-- fact: par.max
select max(storms_in_box) from ph_typhoon_seasons where era = 'satellite';

-- fact: par.max.year
select season from ph_typhoon_seasons where era = 'satellite'
order by storms_in_box desc, season limit 1;

-- fact: par.min
select min(storms_in_box) from ph_typhoon_seasons where era = 'satellite';

-- fact: par.min.year
select season from ph_typhoon_seasons where era = 'satellite'
order by storms_in_box, season limit 1;

-- fact: par.share.of.basin
-- Share of all western Pacific storms that reach Philippine waters.
select round(100.0 * sum(storms_in_box) / sum(storms_in_basin), 1)
from ph_typhoon_seasons where era = 'satellite';

-- ---- how strong they get ------------------------------------------------------

-- fact: cat5
select storms from ph_typhoon_intensity where peak_sshs = 5;

-- fact: cat5.pct
select pct_of_storms from ph_typhoon_intensity where peak_sshs = 5;

-- fact: cat45
select sum(storms) from ph_typhoon_intensity where peak_sshs >= 4;

-- fact: cat45.pct
select round(sum(pct_of_storms), 2) from ph_typhoon_intensity where peak_sshs >= 4;

-- fact: cat5.per.year
select round((select storms from ph_typhoon_intensity where peak_sshs = 5)
           / (select count(*) from ph_typhoon_seasons
              where era = 'satellite')::double, 2);

-- fact: below.typhoon.pct
-- Storms reaching the box that never became a typhoon at all. Most of them.
select round(sum(pct_of_storms), 2) from ph_typhoon_intensity where peak_sshs < 1;

-- fact: classified
select sum(storms) from ph_typhoon_intensity;

-- ---- the strongest -----------------------------------------------------------

-- fact: peak.wind
select max(peak_wind_kt) from ph_typhoon_strongest;

-- fact: peak.wind.kmh
select max(peak_wind_kmh) from ph_typhoon_strongest;

-- fact: peak.tied
-- How many storms share the record. Four do.
select count(*) from ph_typhoon_strongest
where peak_wind_kt = (select max(peak_wind_kt) from ph_typhoon_strongest);

-- fact: peak.first
select name from ph_typhoon_strongest order by rank limit 1;

-- fact: peak.first.season
select season from ph_typhoon_strongest order by rank limit 1;

-- fact: peak.recent
-- Of the record-holders, the most recent season.
select max(season) from ph_typhoon_strongest
where peak_wind_kt = (select max(peak_wind_kt) from ph_typhoon_strongest);

-- fact: top25.since2000
-- How many of the twenty-five most intense storms are from this century.
select count(*) from ph_typhoon_strongest where season >= 2000;

-- fact: top25.n
select count(*) from ph_typhoon_strongest;

-- ---- the season within the year ------------------------------------------------

-- fact: month.peak
select month from ph_typhoon_monthly order by storms desc limit 1;

-- fact: month.peak.n
select storms from ph_typhoon_monthly order by storms desc limit 1;

-- fact: month.peak.pct
select pct_of_storms from ph_typhoon_monthly order by storms desc limit 1;

-- fact: month.quiet
select month from ph_typhoon_monthly order by storms limit 1;

-- fact: month.quiet.n
select storms from ph_typhoon_monthly order by storms limit 1;

-- fact: season.jul.oct.pct
-- Four months carry most of the year.
select round(sum(pct_of_storms), 2) from ph_typhoon_monthly
where month between 7 and 10;

-- fact: season.offseason.pct
-- And no month is empty, which is the point worth making about a country that
-- has no safe season.
select round(sum(pct_of_storms), 2) from ph_typhoon_monthly
where month in (1, 2, 3, 4);

-- ---- landfall ------------------------------------------------------------------

-- fact: landfall.pct
-- Share of storms in the box that record a landfall observation. Not necessarily
-- a Philippine landfall: the column gives distance to land, not to a country.
select round(100.0 * sum(storms_with_landfall_obs) / sum(storms_in_box), 1)
from ph_typhoon_landfall;

-- fact: landfall.total
select sum(storms_with_landfall_obs) from ph_typhoon_landfall;

-- fact: landfall.max.pct
select max(pct_with_landfall) from ph_typhoon_landfall;

-- fact: landfall.max.year
select season from ph_typhoon_landfall order by pct_with_landfall desc, season limit 1;

-- fact: landfall.min.pct
select min(pct_with_landfall) from ph_typhoon_landfall;

-- fact: landfall.min.year
select season from ph_typhoon_landfall order by pct_with_landfall, season limit 1;
