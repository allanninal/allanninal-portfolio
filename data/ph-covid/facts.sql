-- Facts published on projects/covid-analysis.html
--
-- Everything below is read at one as_of date. The page this replaces took its
-- case count from May 2023, its death count from January 2024 and its
-- vaccination count from December 2022, and presented the three as a single
-- snapshot. Each was close to a real number; the set was mutually impossible.

-- fact: cov.cases
select value from ph_covid_headline where metric = 'total_cases';

-- fact: cov.deaths
select value from ph_covid_headline where metric = 'total_deaths';

-- fact: cov.cfr
select value from ph_covid_headline where metric = 'case_fatality_pct';

-- fact: cov.fullyvax
select round(value / 1e6, 1) from ph_covid_headline where metric = 'people_fully_vaccinated';

-- fact: cov.vaccinated
select round(value / 1e6, 1) from ph_covid_headline where metric = 'people_vaccinated';

-- fact: cov.boosters
select round(value / 1e6, 1) from ph_covid_headline where metric = 'total_boosters';

-- fact: cov.excess
select value from ph_covid_excess where metric = 'excess_deaths';

-- fact: cov.excess.multiple
select value from ph_covid_excess where metric = 'undercount_multiple';

-- fact: cov.excess.unattributed
select value from ph_covid_excess where metric = 'unattributed_deaths';

-- fact: cov.peak.daily
select max(new_cases) from ph_covid_daily;

-- fact: cov.peak.date
select date::varchar from ph_covid_daily order by new_cases desc limit 1;

-- fact: cov.peak.smoothed
select round(max(new_cases_smoothed), 0) from ph_covid_daily;

-- fact: cov.waves
select count(*) from ph_covid_waves;

-- fact: cov.wave3.cases
select cases_in_wave from ph_covid_waves where wave = 3;

-- fact: cov.wave3.peak
select peak_smoothed_cases from ph_covid_waves where wave = 3;

-- fact: cov.wave2.deaths
select deaths_in_wave from ph_covid_waves where wave = 2;

-- fact: cov.wave2.cases
select cases_in_wave from ph_covid_waves where wave = 2;

-- fact: cov.cases.2021
select cases from ph_covid_annual where year = 2021;

-- fact: cov.deaths.2021
select deaths from ph_covid_annual where year = 2021;

-- fact: cov.cases.2020
select cases from ph_covid_annual where year = 2020;

-- fact: cov.stringency.max
select value from ph_covid_stringency where metric = 'max_stringency';

-- fact: cov.stringency.mean
select value from ph_covid_stringency where metric = 'mean_stringency';

-- fact: cov.stringency.r
-- Same-day correlation between the Oxford stringency index and smoothed cases.
-- Positive, which reads backwards until you remember governments tighten
-- BECAUSE cases are rising. It is not evidence that lockdowns spread the virus,
-- and the page says so rather than leaving the sign to be misread.
select value from ph_covid_stringency where metric = 'pearson_r_same_day';

-- fact: cov.stringency.days
select value from ph_covid_stringency where metric = 'paired_days';

-- fact: cov.asean.rank.deaths
select count(*) from ph_covid_asean
where deaths_per_million >= (select deaths_per_million from ph_covid_asean
                             where country = 'Philippines');

-- fact: cov.asean.deaths.pm
select round(deaths_per_million, 0) from ph_covid_asean where country = 'Philippines';

-- fact: cov.asean.cases.pm
select round(cases_per_million, 0) from ph_covid_asean where country = 'Philippines';

-- fact: cov.asean.vax
select round(fully_vaccinated_per_hundred, 1) from ph_covid_asean where country = 'Philippines';

-- fact: cov.asean.sg.cases.pm
select round(cases_per_million, 0) from ph_covid_asean where country = 'Singapore';

-- fact: cov.revision
-- The single day the cumulative count fell, and by how much.
select abs(delta) from (
    select date, total_cases - lag(total_cases) over (order by date) delta
    from ph_covid_daily) where delta < 0;

-- fact: cov.stringency.last
select last_date::varchar from ph_covid_coverage where metric = 'stringency_index';

-- fact: cov.positivity.last
select last_date::varchar from ph_covid_coverage where metric = 'positive_rate';

-- fact: cov.positivity.peak
select round(max(positive_rate), 1) from ph_covid_daily;

-- fact: cov.lastreport
select value from ph_covid_reporting where metric = 'last_report_date';

-- fact: cov.trailingzeros
select value from ph_covid_reporting where metric = 'trailing_zero_days';

-- fact: cov.wave3.deaths
select deaths_in_wave from ph_covid_waves where wave = 3;
