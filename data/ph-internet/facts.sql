-- Facts published on projects/internet-analysis.html
--
-- Two sources, deliberately kept apart. The World Bank measures how many people
-- have a connection; Ookla measures how fast the connections that get tested
-- are. They answer different questions and are never blended into a single
-- "internet quality" figure here.

-- fact: net.users.pct
select internet_users_pct from ph_internet_annual where year = 2024;

-- fact: net.users.pct.2023
select internet_users_pct from ph_internet_annual where year = 2023;

-- fact: net.users.pct.2000
select internet_users_pct from ph_internet_annual where year = 2000;

-- fact: net.mobile.per100
select mobile_per_100 from ph_internet_annual where year = 2024;

-- fact: net.fixed.per100
select fixed_broadband_per_100 from ph_internet_annual where year = 2024;

-- fact: net.mobile.vs.fixed
-- The number this page is really about: mobile subscriptions per fixed
-- broadband line.
select round(mobile_per_100 / fixed_broadband_per_100, 0) from ph_internet_annual where year = 2024;

-- fact: net.asean.rank
select count(*) from ph_internet_asean
where internet_users_pct >= (select internet_users_pct from ph_internet_asean
                             where country = 'Philippines');

-- fact: net.asean.year
select distinct year from ph_internet_asean;

-- fact: net.asean.top
select round(internet_users_pct, 1) from ph_internet_asean order by internet_users_pct desc limit 1;

-- fact: net.asean.fixed.rank
select count(*) from ph_internet_asean
where fixed_broadband_per_100 >= (select fixed_broadband_per_100 from ph_internet_asean
                                  where country = 'Philippines');

-- fact: net.fixed.down.latest
select wmean_down_mbps from ph_internet_speeds
where type = 'fixed' order by year desc, quarter desc limit 1;

-- fact: net.fixed.down.2019
select wmean_down_mbps from ph_internet_speeds
where type = 'fixed' order by year, quarter limit 1;

-- fact: net.fixed.multiple
select round((select wmean_down_mbps from ph_internet_speeds
              where type = 'fixed' order by year desc, quarter desc limit 1)
           / (select wmean_down_mbps from ph_internet_speeds
              where type = 'fixed' order by year, quarter limit 1), 1);

-- fact: net.mobile.down.latest
select wmean_down_mbps from ph_internet_speeds
where type = 'mobile' order by year desc, quarter desc limit 1;

-- fact: net.mobile.down.2019
select wmean_down_mbps from ph_internet_speeds
where type = 'mobile' order by year, quarter limit 1;

-- fact: net.fixed.lat.latest
select wmean_latency_ms from ph_internet_speeds
where type = 'fixed' order by year desc, quarter desc limit 1;

-- fact: net.fixed.lat.2019
select wmean_latency_ms from ph_internet_speeds
where type = 'fixed' order by year, quarter limit 1;

-- fact: net.mobile.lat.latest
select wmean_latency_ms from ph_internet_speeds
where type = 'mobile' order by year desc, quarter desc limit 1;

-- fact: net.mobile.lat.2019
select wmean_latency_ms from ph_internet_speeds
where type = 'mobile' order by year, quarter limit 1;

-- fact: net.band.north
select wmean_down_mbps from ph_internet_speed_bands where type = 'fixed' and band = 'north (13N+)';

-- fact: net.band.south
select wmean_down_mbps from ph_internet_speed_bands where type = 'fixed' and band = 'south (<10N)';

-- fact: net.band.central
select wmean_down_mbps from ph_internet_speed_bands where type = 'fixed' and band = 'central (10-13N)';

-- fact: net.mobile.tiles.peak
select max(tiles) from ph_internet_speeds where type = 'mobile';

-- fact: net.mobile.tiles.latest
select tiles from ph_internet_speeds where type = 'mobile' order by year desc, quarter desc limit 1;

-- fact: net.fixed.tiles.latest
select tiles from ph_internet_speeds where type = 'fixed' order by year desc, quarter desc limit 1;

-- fact: net.tests.latest
select tests from ph_internet_speeds where type = 'fixed' order by year desc, quarter desc limit 1;

-- fact: net.quarters
select count(*) from ph_internet_speeds;
