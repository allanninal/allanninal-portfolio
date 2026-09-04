-- World Bank connectivity indicators + Ookla Speedtest tiles.

-- check: every annual row carries a source
-- level: error
select year from ph_internet_annual where source is null or trim(source) = '';

-- check: annual coverage is unbroken
-- level: error
select y from (select unnest(range(2000, 2026)) y) g
where y not in (select year from ph_internet_annual);

-- check: percentages stay within range
-- level: error
-- internet_users_pct is a share and cannot exceed 100. Subscriptions per 100
-- legitimately can -- people hold more than one SIM -- so only the share is
-- bounded here.
select year, internet_users_pct from ph_internet_annual
where internet_users_pct is not null
  and (internet_users_pct < 0 or internet_users_pct > 100);

-- check: subscription rates are non-negative
-- level: error
select year from ph_internet_annual
where mobile_per_100 < 0 or fixed_broadband_per_100 < 0 or fixed_telephone_per_100 < 0;

-- check: the ASEAN comparison uses one year for every country
-- level: error
-- Comparing each country at its own latest year would put 2024 against 2019 and
-- read the difference as a gap in connectivity.
select count(distinct year) from ph_internet_asean having count(distinct year) > 1;

-- check: the Philippines is in the ASEAN comparison
-- level: error
select 1 where 'Philippines' not in (select country from ph_internet_asean);

-- check: every Ookla quarter carries its bounding box
-- level: error
-- The box defines what counts as Philippine here. Without it a row cannot be
-- re-derived or argued with.
select type, year, quarter from ph_internet_speeds
where box is null or trim(box) = '' or source is null or trim(source) = '';

-- check: speeds and latencies are physically plausible
-- level: error
select type, year, quarter, wmean_down_mbps, wmean_latency_ms from ph_internet_speeds
where wmean_down_mbps <= 0 or wmean_down_mbps > 2000
   or wmean_latency_ms <= 0 or wmean_latency_ms > 2000;

-- check: every quarter has tiles behind it
-- level: error
select type, year, quarter, tiles, tests from ph_internet_speeds
where tiles <= 0 or tests <= 0;

-- check: both connection types are present in every year fetched
-- level: error
-- A schema change silently dropped six quarters on the first run: the older
-- parquet files have no tile_x column and the query failed per-file rather than
-- overall. This asserts the recovery held.
select year from (
    select year, count(distinct type) t from ph_internet_speeds group by year)
where t < 2;

-- check: no Ookla quarter failed to parse
-- level: error
select type, year, quarter, status from ph_internet_speeds_coverage
where status <> 'parsed';

-- check: speed band shares are backed by tiles
-- level: error
select type, band, tiles from ph_internet_speed_bands where tiles <= 0 or tests <= 0;

-- check: the internet-use series breaks between 2023 and 2024 (known)
-- level: warn
-- Reported internet use falls from 77.87% to 67.26%, a drop of more than ten
-- points in one year. People did not lose access; the underlying survey changed.
-- The series is therefore not continuous across that break and the page says so
-- rather than drawing a smooth line through it.
select a.year, a.internet_users_pct as pct_earlier, b.internet_users_pct as pct_later
from ph_internet_annual a join ph_internet_annual b on b.year = a.year + 1
where a.internet_users_pct is not null and b.internet_users_pct is not null
  and b.internet_users_pct - a.internet_users_pct < -5;

-- check: mobile test coverage is shrinking (known)
-- level: warn
-- Ookla mobile tiles fall from about 70,000 in 2022 to under 50,000 in 2025
-- while fixed tiles rise. Fewer tiles means fewer places measured, so the rising
-- mobile speed line is partly a changing sample. Kept visible because the page
-- makes a trend claim about that line.
select type, min(tiles) first_tiles, max(tiles) peak_tiles,
       (select tiles from ph_internet_speeds s2
        where s2.type = s.type order by year desc, quarter desc limit 1) latest_tiles
from ph_internet_speeds s where type = 'mobile' group by type
having (select tiles from ph_internet_speeds s2
        where s2.type = s.type order by year desc, quarter desc limit 1) < max(tiles) * 0.8;
