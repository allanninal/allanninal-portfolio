-- OpenStreetMap public-transport extract for Metro Manila.
-- Every count here is a floor on what is MAPPED, not a count of the system.

-- check: every row carries a source
-- level: error
select route_type from ph_transit_routes where source is null or trim(source) = ''
union all
select stop_type from ph_transit_stops where source is null or trim(source) = '';

-- check: routes and stops carry the bounding box
-- level: error
-- The box is the definition of "Metro Manila" here and changes every number.
select route_type from ph_transit_routes where box is null or trim(box) = '';

-- check: counts are positive
-- level: error
select route_type, routes from ph_transit_routes where routes <= 0
union all
select stop_type, count from ph_transit_stops where count <= 0;

-- check: named subsets never exceed their totals
-- level: error
select route_type, routes, named_routes from ph_transit_routes
where named_routes > routes or with_operator > routes;

-- check: stop types sum to the declared total
-- level: error
select (select sum(count) from ph_transit_stops) parts,
       (select value from ph_transit_coverage where metric = 'stop_nodes_total') total
where (select sum(count) from ph_transit_stops)
   <> (select value from ph_transit_coverage where metric = 'stop_nodes_total');

-- check: all seventeen NCR local government units are present
-- level: error
select 17 - count(*) from ph_transit_by_city having count(*) <> 17;

-- check: every city resolved to exactly one OSM relation
-- level: error
-- This is the check that matters most here. area["name"="San Juan"] matches six
-- admin_level=6 boundaries worldwide -- Metro Manila, Negros Oriental, Batangas,
-- Puerto Rico, Honduras, El Salvador -- and Overpass unions them into one total.
-- The first run credited Metro Manila's smallest city with 948 bus stops, more
-- than Manila, because it was counting San Juan, Puerto Rico too. Cities are now
-- resolved to a specific relation id, and a duplicate id would mean two cities
-- were charged to the same boundary.
select osm_relation_id, count(*) from ph_transit_by_city
group by osm_relation_id having count(*) > 1;

-- check: city relation ids are plausible OSM relations
-- level: error
select city, osm_relation_id from ph_transit_by_city
where osm_relation_id is null or osm_relation_id <= 0;

-- check: no single city dominates implausibly
-- level: error
-- A city holding more than half the metro's mapped stops is the signature of the
-- boundary bug above returning a union rather than one city.
select city, road_stops,
       round(100.0 * road_stops / (select sum(road_stops) from ph_transit_by_city), 1) pct
from ph_transit_by_city
where road_stops > (select sum(road_stops) from ph_transit_by_city) * 0.5;

-- check: city rail stations do not exceed the metro total
-- level: error
select sum(rail_stations) city_sum,
       (select count from ph_transit_stops where stop_type = 'rail station') metro
from ph_transit_by_city
having sum(rail_stations)
     > (select count from ph_transit_stops where stop_type = 'rail station');

-- check: jeepney routes are barely mapped (known)
-- level: warn
-- 26 share_taxi relations for a metro that runs jeepneys in the thousands. This
-- is the central caveat of the whole project and the page leads with it: OSM has
-- the formal network almost completely and the informal one hardly at all. Kept
-- as a standing warning so that if coverage ever improves, the page's framing
-- gets revisited rather than quietly outliving the data.
select value, note from ph_transit_coverage
where metric = 'share_taxi_routes' and value < 500;
