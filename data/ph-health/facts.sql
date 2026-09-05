-- Facts published on projects/health-analysis.html
--
-- DOH's Field Health Services Information System is the proper source for
-- Philippine disease numbers; doh.gov.ph sits behind a managed challenge that
-- scripts do not pass. These are the internationally comparable subset the World
-- Bank republishes from WHO and UN IGME.

-- fact: hl.life
select round(life_expectancy, 1) from ph_health_annual
where life_expectancy is not null order by year desc limit 1;

-- fact: hl.year
select max(year) from ph_health_annual where life_expectancy is not null;

-- fact: hl.life.1960
select round(life_expectancy, 1) from ph_health_annual
where life_expectancy is not null order by year limit 1;

-- fact: hl.life.gain
select round((select life_expectancy from ph_health_annual
              where life_expectancy is not null order by year desc limit 1)
           - (select life_expectancy from ph_health_annual
              where life_expectancy is not null order by year limit 1), 1);

-- fact: hl.life.female
select round(life_expectancy_female, 1) from ph_health_annual
where life_expectancy_female is not null order by year desc limit 1;

-- fact: hl.life.male
select round(life_expectancy_male, 1) from ph_health_annual
where life_expectancy_male is not null order by year desc limit 1;

-- fact: hl.infant
select round(infant_mortality_per_1000, 1) from ph_health_annual
where infant_mortality_per_1000 is not null order by year desc limit 1;

-- fact: hl.infant.1960
select round(infant_mortality_per_1000, 1) from ph_health_annual
where infant_mortality_per_1000 is not null order by year limit 1;

-- fact: hl.under5
select round(under5_mortality_per_1000, 1) from ph_health_annual
where under5_mortality_per_1000 is not null order by year desc limit 1;

-- fact: hl.maternal
select round(maternal_mortality_per_100k, 0) from ph_health_annual
where maternal_mortality_per_100k is not null order by year desc limit 1;

-- fact: hl.tb
-- The indicator that went the wrong way while everything else improved.
select round(tb_incidence_per_100k, 0) from ph_health_annual
where tb_incidence_per_100k is not null order by year desc limit 1;

-- fact: hl.tb.2000
select round(tb_incidence_per_100k, 0) from ph_health_annual where year = 2000;

-- fact: hl.tb.change
select round((select tb_incidence_per_100k from ph_health_annual
              where tb_incidence_per_100k is not null order by year desc limit 1)
           - (select tb_incidence_per_100k from ph_health_annual where year = 2000), 0);

-- fact: hl.oop
-- Share of all health spending paid directly by households at the point of care.
select round(out_of_pocket_pct_of_health_spend, 1) from ph_health_annual
where out_of_pocket_pct_of_health_spend is not null order by year desc limit 1;

-- fact: hl.spend
select round(health_spend_pct_gdp, 1) from ph_health_annual
where health_spend_pct_gdp is not null order by year desc limit 1;

-- fact: hl.measles
select round(measles_immunisation_pct, 0) from ph_health_annual
where measles_immunisation_pct is not null order by year desc limit 1;

-- fact: hl.measles.peak
select round(max(measles_immunisation_pct), 0) from ph_health_annual;

-- fact: hl.dpt
select round(dpt_immunisation_pct, 0) from ph_health_annual
where dpt_immunisation_pct is not null order by year desc limit 1;

-- fact: hl.stunting
select round(stunting_under5_pct, 1) from ph_health_annual
where stunting_under5_pct is not null order by year desc limit 1;

-- fact: hl.fertility
select round(fertility_rate, 2) from ph_health_annual
where fertility_rate is not null order by year desc limit 1;

-- fact: hl.asean.year
select distinct year from ph_health_asean;

-- fact: hl.asean.tb.rank
select count(*) from ph_health_asean
where tb_incidence_per_100k >= (select tb_incidence_per_100k from ph_health_asean
                                where country = 'Philippines');

-- fact: hl.asean.n
select count(*) from ph_health_asean;

-- fact: hl.asean.oop.rank
select count(*) from ph_health_asean
where out_of_pocket_pct_of_health_spend
   >= (select out_of_pocket_pct_of_health_spend from ph_health_asean
       where country = 'Philippines');

-- fact: hl.asean.tb.best
select round(min(tb_incidence_per_100k), 0) from ph_health_asean;

-- fact: hl.asean.tb.mult
-- Philippine TB incidence as a multiple of the lowest in the comparison group.
select round((select tb_incidence_per_100k from ph_health_asean where country = 'Philippines')
           / (select min(tb_incidence_per_100k) from ph_health_asean), 1);

-- fact: hl.asean.tb.ph
-- Philippine TB incidence in the ASEAN comparison year, which is one year behind
-- the latest national figure -- the comparison uses the latest year EVERY country
-- has, so the two differ and must not be used interchangeably.
select tb_incidence_per_100k from ph_health_asean where country = 'Philippines';
