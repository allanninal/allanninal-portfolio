-- Facts published on projects/tourism-analysis.html

-- fact: tour.arrivals.2025
select round(total_arrivals / 1e6, 2) from ph_tourism_annual where year = 2025;

-- fact: tour.foreign.2025
select round(foreign_arrivals / 1e6, 2) from ph_tourism_annual where year = 2025;

-- fact: tour.arrivals.2019
select round(total_arrivals / 1e6, 2) from ph_tourism_annual where year = 2019;

-- fact: tour.arrivals.2021
select total_arrivals from ph_tourism_annual where year = 2021;

-- fact: tour.growth.2010_2025
select round((( select total_arrivals from ph_tourism_annual where year = 2025)
            / (select total_arrivals from ph_tourism_annual where year = 2010) - 1) * 100, 0);

-- fact: tour.vs.2019
select round((( select total_arrivals from ph_tourism_annual where year = 2025)
            / (select total_arrivals from ph_tourism_annual where year = 2019) - 1) * 100, 1);

-- fact: tour.korea.2024
select round(arrivals_2024 / 1e6, 2) from ph_tourism_top_markets_2024 where country = 'South Korea';

-- fact: tour.korea.share.2024
select share_pct from ph_tourism_top_markets_2024 where country = 'South Korea';

-- fact: tour.us.share.2024
select share_pct from ph_tourism_top_markets_2024 where country = 'United States';

-- fact: tour.japan.growth.2024
select growth_pct from ph_tourism_top_markets_2024 where country = 'Japan';

-- fact: tour.receipts.2024
select receipts_php_billion from ph_tourism_receipts where year = 2024;

-- fact: tour.drop.2021
select round((( select total_arrivals from ph_tourism_annual where year = 2021)
            / (select total_arrivals from ph_tourism_annual where year = 2019)::double - 1) * 100, 0);

-- fact: tour.arrivals.2010
select round(total_arrivals / 1e6, 2) from ph_tourism_annual where year = 2010;

-- fact: tour.vs.2024
-- Published as 0.76% before this was bound; the real gap is 9.0%.
select round((( select total_arrivals from ph_tourism_annual where year = 2025)
            / (select total_arrivals from ph_tourism_annual where year = 2024)::double - 1) * 100, 1);

-- fact: tour.receipts.growth.2024
select growth_pct from ph_tourism_receipts where year = 2024;

-- fact: tour.china.share.2024
select share_pct from ph_tourism_top_markets_2024 where country = 'China';
