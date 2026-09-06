-- Where networks actually meet: PeeringDB exchanges and facilities.
--
-- The checks guard three things: that a count of buildings is never mistaken for
-- a count of interconnection, that "empty" means empty in both of the two
-- independent counts rather than in one of them, and that the self-reported
-- nature of the registry stays visible instead of being rounded away.

-- check: every exchange carries a source
-- level: error
select ix_id from gi_exchange where source is null or trim(source) = '';

-- check: every facility carries a source
-- level: error
select fac_id from gi_facility where source is null or trim(source) = '';

-- check: ids are unique
-- level: error
select ix_id, count(*) from gi_exchange group by 1 having count(*) > 1;

-- check: facility ids are unique
-- level: error
select fac_id, count(*) from gi_facility group by 1 having count(*) > 1;

-- check: counts are never negative
-- level: error
select ix_id, net_count, ixf_net_count, fac_count from gi_exchange
where net_count < 0 or ixf_net_count < 0 or fac_count < 0;

-- check: facility counts are never negative
-- level: error
select fac_id, net_count, ix_count, carrier_count from gi_facility
where net_count < 0 or ix_count < 0 or carrier_count < 0;

-- check: the status column is derived, not asserted
-- level: error
-- Every row's status has to follow from its two counts. This is the field the
-- whole page turns on, so it is recomputed here rather than trusted.
select ix_id, net_count, ixf_net_count, status from gi_exchange
where status <> case
  when net_count = 0 and ixf_net_count = 0 then 'empty'
  when net_count = 0 then 'registry gap'
  when net_count = 1 then 'single member'
  else 'in use' end;

-- check: an exchange is only empty when BOTH counts say so
-- level: error
-- The distinction the page depends on. An exchange whose operator recorded zero
-- but whose own published member list shows members is a gap in the registry,
-- not an exchange nobody joined, and calling it empty would overstate the
-- finding in exactly the direction that makes it interesting.
select ix_id, name, net_count, ixf_net_count from gi_exchange
where status = 'empty' and ixf_net_count > 0;

-- check: the country rollup matches the exchange rows
-- level: error
select c.iso2, c.exchanges stated, count(x.ix_id) actual
from gi_country c left join gi_exchange x on x.country = c.iso2
group by 1, 2 having c.exchanges <> count(x.ix_id);

-- check: the country rollup matches the facility rows
-- level: error
select c.iso2, c.facilities stated, count(f.fac_id) actual
from gi_country c left join gi_facility f on f.country = c.iso2
group by 1, 2 having c.facilities <> count(f.fac_id);

-- check: country network totals are the sum of their rows
-- level: error
select c.iso2, c.networks_at_exchanges stated, sum(x.net_count) actual
from gi_country c join gi_exchange x on x.country = c.iso2
group by 1, 2 having c.networks_at_exchanges <> sum(x.net_count);

-- check: the empty tally per country matches the rows
-- level: error
select c.iso2, c.empty_exchanges stated,
       sum(case when x.status = 'empty' then 1 else 0 end) actual
from gi_country c join gi_exchange x on x.country = c.iso2
group by 1, 2 having c.empty_exchanges
                  <> sum(case when x.status = 'empty' then 1 else 0 end);

-- check: the largest exchange in a country is at least its mean
-- level: error
select iso2, largest_exchange_networks, networks_at_exchanges, exchanges
from gi_country
where exchanges > 0
  and largest_exchange_networks * exchanges < networks_at_exchanges;

-- check: coverage counts agree with the rows they summarise
-- level: error
select (select value from gi_coverage where property = 'exchanges' and unit = 'count') stated,
       (select count(*) from gi_exchange) actual
having stated <> actual;

-- check: the stated empty count is the number of empty rows
-- level: error
select (select value from gi_coverage
        where property = 'empty exchanges' and unit = 'count') stated,
       (select count(*) from gi_exchange where status = 'empty') actual
having stated <> actual;

-- check: landing points have coordinates
-- level: error
select landing_point_id, name from gi_landing_point
where longitude is null or latitude is null
   or longitude < -180 or longitude > 180 or latitude < -90 or latitude > 90;

-- check: facility coordinates are on the planet
-- level: error
-- Blank is allowed; a facility at longitude 400 is not.
select fac_id, latitude, longitude from gi_facility
where (latitude is not null and (latitude < -90 or latitude > 90))
   or (longitude is not null and (longitude < -180 or longitude > 180));

-- check: a facility count is not an interconnection count (known)
-- level: warn
-- The page's central point, kept in the check output. These two orderings are
-- different, and quoting the first as if it were the second is the error the
-- whole analysis exists to avoid.
select country, facilities, network_presences_in_facilities
from gi_country order by facilities desc limit 12;

-- check: most exchanges are small (known)
-- level: warn
select status, count(*) exchanges, sum(net_count) networks
from gi_exchange group by 1 order by 2 desc;

-- check: the registry is self-reported (known)
-- level: warn
-- Recorded so the caveat is in the data rather than only in the prose: PeeringDB
-- is maintained by operators about themselves, so a country with no rows may
-- have no exchange or may simply have nobody filling in the form.
select property, value from gi_coverage where property = 'self-reported registry';
