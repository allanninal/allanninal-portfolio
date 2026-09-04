-- Facts published on projects/dengue-analysis.html

-- fact: dengue.peak.2019
select cases from ph_dengue_annual where year = 2019;

-- fact: dengue.deaths.2016_2021
select sum(deaths) from ph_dengue_annual where deaths is not null;

-- fact: dengue.cases.2024
select cases from ph_dengue_annual where year = 2024;

-- fact: dengue.cases.2026ytd
select cases from ph_dengue_annual where year = 2026;

-- fact: dengue.drop.2020
select round((( select cases from ph_dengue_annual where year = 2020)
            / (select cases from ph_dengue_annual where year = 2019)::double - 1) * 100, 0);

-- fact: dengue.cases.2023
select cases from ph_dengue_annual where year = 2023;

-- fact: dengue.cases.2022
select cases from ph_dengue_annual where year = 2022;

-- fact: dengue.seq.2023
select denv1 + denv2 + denv3 + denv4 + unspecified from ph_dengue_ena_serotype_by_year where year = 2023;

-- fact: dengue.seq.2019
select denv1 + denv2 + denv3 + denv4 + unspecified from ph_dengue_ena_serotype_by_year where year = 2019;

-- fact: dengue.runs.total
select sum(runs) from ph_dengue_ena_studies;

-- fact: dengue.studies.total
select count(*) from ph_dengue_ena_studies;

-- fact: dengue.runs.largest_study
select runs from ph_dengue_ena_studies where study_accession = 'PRJNA1009983';

-- fact: dengue.top_province.cases
select cases from ph_dengue_top_provinces_2016_2021 order by cases desc limit 1;

-- fact: dengue.cebu.cases
select cases from ph_dengue_top_provinces_2016_2021 where province = 'CEBU';

-- fact: dengue.cebu.deaths
select deaths from ph_dengue_top_provinces_2016_2021 where province = 'CEBU';

-- The insight cards round to thousands. Separate keys rather than a looser
-- comparison: '442K' and 441,902 are both correct, and the verifier should not
-- have to guess which rounding a page meant.

-- fact: dengue.peak.2019.k
select round(cases / 1000.0, 0) from ph_dengue_annual where year = 2019;

-- fact: dengue.cases.2024.k
select round(cases / 1000.0, 0) from ph_dengue_annual where year = 2024;

-- Prose figures. These are the ones that drift: every number below was typed
-- by hand from a CSV, and four of them were wrong when this file was written
-- (a 82% year-on-year that was really 37.8%, a 30% regional share that was
-- really 35.9%, a 6x seasonal ratio that was really 5.6x, and a CFR off by
-- 0.01). Bound here so the next edit has to survive `make facts`.

-- fact: dengue.avg.cases.2016_2020
select round(avg(cases) / 1000.0, 0) from ph_dengue_annual where year between 2016 and 2020;

-- fact: dengue.avg.deaths.2016_2020
select round(avg(deaths), 0) from ph_dengue_annual where year between 2016 and 2020;

-- fact: dengue.cfr.2016_2020
select round(100.0 * sum(deaths) / sum(cases), 2) from ph_dengue_annual where year between 2016 and 2020;

-- fact: dengue.cfr.2017
select cfr_pct from ph_dengue_annual where year = 2017;

-- fact: dengue.season.ratio
-- Aug+Sep over Apr+May, pooled 2016-2021.
select round((select sum(cases_2016_2021_total) from ph_dengue_monthly_seasonality where month in (8, 9))
           / (select sum(cases_2016_2021_total) from ph_dengue_monthly_seasonality where month in (4, 5))::double, 1);

-- fact: dengue.region3.share
select round(100.0 * sum(case when region in ('REGION IV-A-CALABARZON', 'REGION III-CENTRAL LUZON',
                                              'REGION VI-WESTERN VISAYAS') then cases else 0 end)
             / sum(cases), 1)
from ph_dengue_by_region_2016_2021;

-- fact: dengue.yoy.2024
-- 2024 is Jan-Oct against a full 2023, so this understates the real gap. Said
-- plainly on the page rather than annualised into a cleaner-looking number.
select round((( select cases from ph_dengue_annual where year = 2024)
            / (select cases from ph_dengue_annual where year = 2023)::double - 1) * 100, 1);
