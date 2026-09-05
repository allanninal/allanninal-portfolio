-- Facts published on projects/transit-analysis.html
--
-- Every count is what OpenStreetMap has MAPPED inside the stated bounding box.
-- OSM is a volunteer map and its Philippine transport coverage is partial, so
-- these are floors. The page says that before it says anything else.

-- fact: tr.routes
select sum(routes) from ph_transit_routes;

-- fact: tr.bus.routes
select routes from ph_transit_routes where route_type = 'bus';

-- fact: tr.jeep.routes
-- 26 relations for a network that runs in the thousands. The gap between this
-- and the bus count is the finding.
select routes from ph_transit_routes where route_type = 'share_taxi';

-- fact: tr.bus.vs.jeep
select round((select routes from ph_transit_routes where route_type = 'bus')
           / (select routes from ph_transit_routes where route_type = 'share_taxi')::double, 0);

-- fact: tr.rail.relations
select sum(routes) from ph_transit_routes
where route_type in ('light_rail', 'subway', 'train', 'monorail');

-- fact: tr.rail.lines
-- Distinct lines, not relations. OSM models each direction of a line as its own
-- relation, so counting relations doubles the network.
select count(distinct regexp_replace(name, ':.*$', '')) from ph_transit_rail_routes;

-- fact: tr.stops
select value from ph_transit_coverage where metric = 'stop_nodes_total';

-- fact: tr.busstops
select count from ph_transit_stops where stop_type = 'bus stop';

-- fact: tr.busstops.named
select pct_named from ph_transit_stops where stop_type = 'bus stop';

-- fact: tr.stations
select count from ph_transit_stops where stop_type = 'rail station';

-- fact: tr.terminals
select count from ph_transit_stops where stop_type = 'bus terminal';

-- fact: tr.cities
select count(*) from ph_transit_by_city;

-- fact: tr.top.city
select city from ph_transit_by_city order by road_stops desc limit 1;

-- fact: tr.top.city.stops
select road_stops from ph_transit_by_city order by road_stops desc limit 1;

-- fact: tr.bottom.city
select city from ph_transit_by_city order by road_stops limit 1;

-- fact: tr.bottom.city.stops
select road_stops from ph_transit_by_city order by road_stops limit 1;

-- fact: tr.city.ratio
select round((select road_stops from ph_transit_by_city order by road_stops desc limit 1)
           / (select road_stops from ph_transit_by_city order by road_stops limit 1)::double, 0);

-- fact: tr.city.total
select sum(road_stops) from ph_transit_by_city;

-- fact: tr.top2.share
-- Quezon City and Manila between them.
select round(100.0 * (select sum(road_stops) from (
                select road_stops from ph_transit_by_city order by road_stops desc limit 2))
           / (select sum(road_stops) from ph_transit_by_city), 1);

-- fact: tr.norail.cities
select count(*) from ph_transit_by_city where rail_stations = 0;

-- fact: tr.qc.stations
select rail_stations from ph_transit_by_city where city = 'Quezon City';

-- fact: tr.operator.pct
select round(100.0 * with_operator / routes, 1) from ph_transit_routes where route_type = 'bus';

-- fact: tr.jeep.operator.pct
select round(100.0 * with_operator / routes, 1) from ph_transit_routes where route_type = 'share_taxi';

-- fact: tr.sanjuan.stops
-- Metro Manila's San Juan alone, after the boundary fix. The first run reported
-- 948 for this city because Overpass had unioned six San Juans worldwide.
select road_stops from ph_transit_by_city where city = 'San Juan';
