-- Facts published on projects/global-interconnect-analysis.html
--
-- PeeringDB is a registry network operators keep about themselves: every internet
-- exchange, every colocation facility, and how many networks are present at each.
-- The page's argument is that the number people quote -- how many data centres a
-- country has -- is not the number that matters, and that the distribution of the
-- one that does matter has a very long and very empty tail.

-- ---- the dataset -------------------------------------------------------------

-- fact: gi.exchanges
select value from gi_coverage where property = 'exchanges' and unit = 'count';

-- fact: gi.facilities
select value from gi_coverage where property = 'facilities' and unit = 'count';

-- fact: gi.presences
select value from gi_coverage where property = 'network presences in facilities';

-- fact: gi.atexchanges
select value from gi_coverage where property = 'networks at exchanges';

-- fact: gi.countries
select count(*) from gi_country;

-- fact: gi.cables
select value from gi_coverage where property = 'submarine cables';

-- fact: gi.landings
select value from gi_coverage where property = 'submarine cable landing points';

-- fact: gi.memberlists
-- Exchanges publishing a machine-readable member list, which is the second count
-- the empty finding is checked against.
select value from gi_coverage where property = 'exchanges publishing a member list';

-- fact: gi.gap
select value from gi_coverage where property = 'median gap between the two counts';

-- fact: gi.registrygaps
select value from gi_coverage
where property = 'registry gaps excluded from the empty count';

-- ---- the empty tail ----------------------------------------------------------

-- fact: empty.n
select count(*) from gi_exchange where status = 'empty';

-- fact: empty.pct
select round(100.0 * (select count(*) from gi_exchange where status = 'empty')
           / (select count(*) from gi_exchange), 2);

-- fact: single.n
select count(*) from gi_exchange where status = 'single member';

-- fact: emptyorsingle.n
select count(*) from gi_exchange where status in ('empty', 'single member');

-- fact: emptyorsingle.pct
select round(100.0 * (select count(*) from gi_exchange
                      where status in ('empty', 'single member'))
           / (select count(*) from gi_exchange), 2);

-- fact: inuse.n
select count(*) from gi_exchange where status = 'in use';

-- fact: under10.n
-- Exchanges with fewer than ten networks on them, which is small enough that the
-- traffic saved by peering there is unlikely to pay for the switch.
select count(*) from gi_exchange where net_count < 10;

-- fact: under10.pct
select round(100.0 * (select count(*) from gi_exchange where net_count < 10)
           / (select count(*) from gi_exchange), 1);

-- fact: allempty.countries
-- Countries whose every registered exchange is empty or has a single member.
select count(*) from gi_country
where exchanges > 0 and empty_exchanges + single_member_exchanges = exchanges;

-- fact: noexchange.countries
select count(*) from gi_country where exchanges = 0;

-- ---- the shape of the distribution -------------------------------------------

-- fact: median.networks
select cast(median(net_count) as integer) from gi_exchange;

-- fact: mean.networks
select round(avg(net_count), 1) from gi_exchange;

-- fact: top10.pct
select round(100.0 * (select sum(net_count) from
                      (select net_count from gi_exchange
                       order by net_count desc limit 10))
           / (select sum(net_count) from gi_exchange), 2);

-- fact: top20.pct
select round(100.0 * (select sum(net_count) from
                      (select net_count from gi_exchange
                       order by net_count desc limit 20))
           / (select sum(net_count) from gi_exchange), 2);

-- fact: bottomhalf.pct
-- The smaller half of all exchanges, by the share of the world's registered
-- presences they hold between them.
select round(100.0 * (select sum(net_count) from
                      (select net_count from gi_exchange
                       order by net_count limit 661))
           / (select sum(net_count) from gi_exchange), 2);

-- ---- the largest exchange is not where the story says it is ------------------

-- fact: biggest.name
select name from gi_exchange order by net_count desc limit 1;

-- fact: biggest.city
select city from gi_exchange order by net_count desc limit 1;

-- fact: biggest.country
select country from gi_exchange order by net_count desc limit 1;

-- fact: biggest.networks
select max(net_count) from gi_exchange;

-- fact: frankfurt.networks
select net_count from gi_exchange where name = 'DE-CIX Frankfurt';

-- fact: amsterdam.networks
select net_count from gi_exchange where name = 'AMS-IX';

-- fact: london.networks
select net_count from gi_exchange where name = 'LINX LON1';

-- fact: biggest.over.frankfurt
select round(1.0 * (select max(net_count) from gi_exchange)
           / (select net_count from gi_exchange where name = 'DE-CIX Frankfurt'), 2);

-- fact: id.intop10
-- Indonesian exchanges among the ten largest in the world, which is not where the
-- usual account of internet geography puts them.
select count(*) from (select country from gi_exchange
                      order by net_count desc limit 10) where country = 'ID';

-- ---- buildings are not interconnection ---------------------------------------

-- fact: us.facilities
select facilities from gi_country where iso2 = 'US';

-- fact: us.facilities.pct
select round(100.0 * (select facilities from gi_country where iso2 = 'US')
           / (select sum(facilities) from gi_country), 2);

-- fact: us.presences.pct
select round(100.0 * (select network_presences_in_facilities from gi_country
                      where iso2 = 'US')
           / (select sum(network_presences_in_facilities) from gi_country), 2);

-- fact: us.perbuilding
select round(1.0 * network_presences_in_facilities / facilities, 1)
from gi_country where iso2 = 'US';

-- fact: nl.perbuilding
select round(1.0 * network_presences_in_facilities / facilities, 1)
from gi_country where iso2 = 'NL';

-- fact: id.perbuilding
select round(1.0 * network_presences_in_facilities / facilities, 1)
from gi_country where iso2 = 'ID';

-- fact: nl.over.us
select round((select 1.0 * network_presences_in_facilities / facilities
              from gi_country where iso2 = 'NL')
           / (select 1.0 * network_presences_in_facilities / facilities
              from gi_country where iso2 = 'US'), 2);

-- fact: id.facilities
select facilities from gi_country where iso2 = 'ID';

-- fact: id.presences
select network_presences_in_facilities from gi_country where iso2 = 'ID';

-- ---- the Philippines ---------------------------------------------------------

-- fact: ph.exchanges
select exchanges from gi_country where iso2 = 'PH';

-- fact: ph.networks
select networks_at_exchanges from gi_country where iso2 = 'PH';

-- fact: ph.largest
select largest_exchange_networks from gi_country where iso2 = 'PH';

-- fact: ph.facilities
select facilities from gi_country where iso2 = 'PH';

-- fact: ph.perbuilding
select round(1.0 * network_presences_in_facilities / facilities, 1)
from gi_country where iso2 = 'PH';
