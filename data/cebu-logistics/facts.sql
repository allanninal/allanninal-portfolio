-- Facts published on projects/cebu-logistics-analysis.html
--
-- The CPA volume columns arrive as quoted strings with thousands separators
-- and a literal '-' for "no movement", so every aggregate below cleans them
-- inline: nullif(trim(x),'-') then strip commas then cast. Summing the raw
-- column is a type error, which is the good failure mode -- a silent
-- lexicographic sum would be the bad one.

-- fact: cebu.cargo.2024
select round(sum(try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double)) / 1e6, 1)
from cpa_cargo where year = '2024';

-- fact: cebu.teu.2024
select round(sum(try_cast(replace(nullif(trim(volume_teus), '-'), ',', '') as double)) / 1e3, 0)
from cpa_container where year = '2024';

-- fact: cebu.pax.2024
select round(sum(try_cast(replace(nullif(trim(number_passengers), '-'), ',', '') as double)) / 1e6, 1)
from cpa_passenger where year = '2024';

-- fact: cebu.calls.2024
select round(sum(try_cast(replace(nullif(trim("count"), '-'), ',', '') as double)) / 1e3, 0)
from cpa_shipcall where year = '2024';

-- fact: cebu.cargo.growth.2022_2024
select round((sum(case when year = '2024' then try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double) end)
            / sum(case when year = '2022' then try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double) end) - 1) * 100, 1)
from cpa_cargo;

-- fact: cebu.cargo.peakmonth.2024
-- lower() is load-bearing: CPA ships 'January' and 'january' as separate
-- literals, and grouping on the raw column splits four of the twelve months.
-- May beats July by only 12,000 mt, so the peak claim is decided on full
-- tonnage and rounded for display only.
select round(sum(try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double)) / 1e6, 1)
from cpa_cargo where year = '2024' and lower(trim(month)) = 'may';

-- fact: cebu.cargo.perday.2024
select round(sum(try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double)) / 366 / 1e3, 0)
from cpa_cargo where year = '2024';

-- fact: cebu.roads.total
select sum(count) from cebu_roads_summary;

-- fact: cebu.roads.trunk_primary
select sum(count) from cebu_roads_summary where highway_class in ('trunk', 'primary');

-- fact: cebu.roads.secondary_tertiary
select sum(count) from cebu_roads_summary where highway_class in ('secondary', 'tertiary');

-- fact: cebu.roads.freight_share
select round(100.0 * sum(case when highway_class in ('trunk', 'primary', 'secondary', 'tertiary')
                              then count else 0 end) / sum(count), 1)
from cebu_roads_summary;

-- Prose figures.

-- fact: cebu.mix.rolling
select round(100.0 * sum(case when cargo_type = 'Rolling'
             then try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double) else 0 end)
           / sum(try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double)), 1)
from cpa_cargo where year = '2024';

-- fact: cebu.mix.bulk
select round(100.0 * sum(case when cargo_type = 'Bulk'
             then try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double) else 0 end)
           / sum(try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double)), 1)
from cpa_cargo where year = '2024';

-- fact: cebu.mix.containerized
select round(100.0 * sum(case when cargo_type = 'Containerized'
             then try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double) else 0 end)
           / sum(try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double)), 1)
from cpa_cargo where year = '2024';

-- fact: cebu.mix.breakbulk
select round(100.0 * sum(case when cargo_type = 'Breakbulk'
             then try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double) else 0 end)
           / sum(try_cast(replace(nullif(trim(volume_metrictons), '-'), ',', '') as double)), 1)
from cpa_cargo where year = '2024';

-- fact: cebu.pax.growth.2022_2024
select round(((select sum(try_cast(replace(nullif(trim(number_passengers), '-'), ',', '') as double)) from cpa_passenger where year = '2024')
            / (select sum(try_cast(replace(nullif(trim(number_passengers), '-'), ',', '') as double)) from cpa_passenger where year = '2022') - 1) * 100, 0);

-- fact: cebu.cip.teu.share
select round(100.0 * sum(case when lower(trim(pmo)) = 'pmo cip'
             then try_cast(replace(nullif(trim(volume_teus), '-'), ',', '') as double) else 0 end)
           / sum(try_cast(replace(nullif(trim(volume_teus), '-'), ',', '') as double)), 0)
from cpa_container where year = '2024';
