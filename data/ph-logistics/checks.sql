-- World Bank Logistics Performance Index, ASEAN-6.

-- check: every row carries its scale and source
-- level: error
-- The LPI is a 1-5 survey scale. A score read as a rank, a percentage or an
-- index out of 100 is wrong by a factor, so the scale rides on every row.
select country, dimension, year from ph_lpi_scores
where scale is null or trim(scale) = '' or source is null or trim(source) = '';

-- check: scores are inside the 1-5 survey scale
-- level: error
select country, dimension, year, score from ph_lpi_scores
where score < 1 or score > 5;

-- check: every country has every dimension in every round
-- level: error
-- A missing cell would silently drop a country from a chart or shift a rank.
select count(*) missing from (
    select c.country, d.dimension, y.year
    from (select distinct country from ph_lpi_scores) c
    cross join (select distinct dimension from ph_lpi_scores) d
    cross join (select distinct year from ph_lpi_scores) y
    left join ph_lpi_scores s
      on s.country = c.country and s.dimension = d.dimension and s.year = y.year
    where s.score is null)
having count(*) > 0;

-- check: the Philippines is present
-- level: error
select 1 where 'Philippines' not in (select country from ph_lpi_scores);

-- check: ranks are dense and complete within each round
-- level: error
select year, count(*) n, max(rank_in_asean6) mx, min(rank_in_asean6) mn
from ph_lpi_ranks group by year
having count(*) <> max(rank_in_asean6) or min(rank_in_asean6) <> 1;

-- check: rank order agrees with score order
-- level: error
-- Two independent derivations of the same thing. If a tie is broken
-- inconsistently, or the sort direction flips, this catches it.
select a.year, a.country, a.rank_in_asean6, b.country, b.rank_in_asean6
from ph_lpi_ranks a join ph_lpi_ranks b on a.year = b.year
where a.rank_in_asean6 < b.rank_in_asean6 and a.overall_score < b.overall_score;

-- check: the overall score is not a mean of the six dimensions
-- level: warn
-- The LPI overall is a weighted aggregate computed by the World Bank, not the
-- average of the published sub-scores. This check fires while the two differ,
-- which is the expected state; it exists so nobody "simplifies" the page by
-- recomputing overall from the parts.
select s.country, s.year, s.score published,
       round(avg(d.score), 3) mean_of_dimensions
from ph_lpi_scores s
join ph_lpi_scores d on d.country = s.country and d.year = s.year
                    and d.dimension <> 'overall'
where s.dimension = 'overall' and s.country = 'Philippines'
group by s.country, s.year, s.score
having abs(s.score - avg(d.score)) > 0.01;

-- check: survey rounds are irregular (known)
-- level: warn
-- 2007, 2010, 2012, 2014, 2016, 2018, 2022 -- gaps of two to four years, with
-- the pandemic gap the largest. Charts must use a real time axis; an evenly
-- spaced category axis would imply a regularity the survey does not have.
select round_year, next_round_year, gap_years from ph_lpi_rounds
where gap_years <> 2;
