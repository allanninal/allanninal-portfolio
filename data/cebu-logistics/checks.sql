-- Cebu Port Authority monthly panels + OSM road extract.

-- check: cargo volumes parse as numbers
-- level: error
-- The volume columns are quoted strings with thousands separators. A value
-- that survives comma-stripping but still will not cast is a parse artifact,
-- not a number -- and try_cast would turn it silently into NULL.
select volume_metrictons, count(*) from cpa_cargo
where trim(volume_metrictons) not in ('', '-')
  and try_cast(replace(trim(volume_metrictons), ',', '') as double) is null
group by volume_metrictons;

-- check: container volumes parse as numbers
-- level: error
select volume_teus, count(*) from cpa_container
where trim(volume_teus) not in ('', '-')
  and try_cast(replace(trim(volume_teus), ',', '') as double) is null
group by volume_teus;

-- check: month vocabulary closure
-- level: error
-- Compared case-insensitively on purpose -- see the casing check below. A
-- stray 'Jan' or 'january ' would split the monthly series in two and quietly
-- halve a peak-month figure.
select distinct month from cpa_cargo
where lower(trim(month)) not in ('january', 'february', 'march', 'april', 'may', 'june',
                                 'july', 'august', 'september', 'october', 'november', 'december');

-- check: month casing is inconsistent in the source (known)
-- level: warn
-- CPA ships some months capitalised: 2024 alone carries 'January' alongside
-- 'january', and 'June', 'October', 'November' likewise. Grouping on the raw
-- column therefore splits those months in two -- which silently demoted June
-- from third-largest month to eighth before this was caught. Every query over
-- month must lower() it. Kept as a warning so the quirk stays on the record
-- instead of being normalised away in the CSV.
select lower(trim(month)) m, count(distinct month) variants from cpa_cargo
group by m having count(distinct month) > 1;

-- check: movement type vocabulary closure
-- level: error
-- Two vocabularies coexist by design: domestic movements are inbound/outbound,
-- foreign movements are import/export. Both appear in mixed case, so this is
-- normalised the same way the month check is.
select distinct movement_type from cpa_cargo
where lower(trim(movement_type)) not in ('inbound', 'outbound', 'import', 'export');

-- check: every full year has all twelve months of cargo
-- level: error
-- 2025 is partial by design and excluded. Any complete year missing a month
-- means the source workbook lost a sheet, which shows up as a dip in the
-- chart rather than an error.
select year, count(distinct lower(trim(month))) m from cpa_cargo
where year in ('2022', '2023', '2024') group by year having m <> 12;

-- check: passenger movements are balanced in kind
-- level: warn
-- Embarking and disembarking should both be present every month; a month with
-- only one direction is a partial extract.
select year, lower(trim(month)) m, count(distinct lower(trim(movement_type))) d from cpa_passenger
group by year, m having d < 2;

-- check: road class counts are positive
-- level: error
select * from cebu_roads_summary where count is null or count <= 0;

-- check: freight-grade classes are all present in the road extract
-- level: error
-- The freight-grade share on the page is (trunk+primary+secondary+tertiary)
-- over the total. If Overpass drops a class the share moves without erroring.
select c from (values ('trunk'), ('primary'), ('secondary'), ('tertiary')) v(c)
where c not in (select highway_class from cebu_roads_summary);
