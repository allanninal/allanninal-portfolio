-- Facts published on projects/competitiveness-analysis.html
--
-- The page was specified as a ranking of 149 Philippine cities on DTI's CMCI.
-- cmci.dti.gov.ph returns 403 to scripts and there is no open feed, so that
-- ranking is unreachable and the page says so. What is here instead is the World
-- Bank's Logistics Performance Index: a real, comparable, openly published slice
-- of competitiveness, on a 1-5 survey scale.

-- fact: lpi.overall
select score from ph_lpi_scores
where country = 'Philippines' and dimension = 'overall'
  and year = (select max(year) from ph_lpi_scores);

-- fact: lpi.year
select max(year) from ph_lpi_scores;

-- fact: lpi.rank
select rank_in_asean6 from ph_lpi_ranks
where country = 'Philippines' and year = (select max(year) from ph_lpi_ranks);

-- fact: lpi.countries
select countries_ranked from ph_lpi_ranks
where country = 'Philippines' and year = (select max(year) from ph_lpi_ranks);

-- fact: lpi.customs
select score from ph_lpi_scores
where country = 'Philippines' and dimension = 'customs'
  and year = (select max(year) from ph_lpi_scores);

-- fact: lpi.timeliness
select score from ph_lpi_scores
where country = 'Philippines' and dimension = 'timeliness'
  and year = (select max(year) from ph_lpi_scores);

-- fact: lpi.spread
-- Best dimension minus worst, latest round. The internal spread is wider than
-- the gap between the Philippines and its neighbours on the overall score.
select round((select max(score) from ph_lpi_scores
              where country = 'Philippines' and dimension <> 'overall'
                and year = (select max(year) from ph_lpi_scores))
           - (select min(score) from ph_lpi_scores
              where country = 'Philippines' and dimension <> 'overall'
                and year = (select max(year) from ph_lpi_scores)), 2);

-- fact: lpi.worst.dim
select dimension from ph_lpi_scores
where country = 'Philippines' and dimension <> 'overall'
  and year = (select max(year) from ph_lpi_scores)
order by score limit 1;

-- fact: lpi.best.dim
select dimension from ph_lpi_scores
where country = 'Philippines' and dimension <> 'overall'
  and year = (select max(year) from ph_lpi_scores)
order by score desc limit 1;

-- fact: lpi.infrastructure
select score from ph_lpi_scores
where country = 'Philippines' and dimension = 'infrastructure'
  and year = (select max(year) from ph_lpi_scores);

-- fact: lpi.sgp
select score from ph_lpi_scores
where country = 'Singapore' and dimension = 'overall'
  and year = (select max(year) from ph_lpi_scores);

-- fact: lpi.leader.gap
select round((select score from ph_lpi_scores where country = 'Singapore'
              and dimension = 'overall' and year = (select max(year) from ph_lpi_scores))
           - (select score from ph_lpi_scores where country = 'Philippines'
              and dimension = 'overall' and year = (select max(year) from ph_lpi_scores)), 2);

-- fact: lpi.customs.gap
-- The Philippines against Singapore on customs specifically -- the widest
-- country gap in any single dimension.
select round((select score from ph_lpi_scores where country = 'Singapore'
              and dimension = 'customs' and year = (select max(year) from ph_lpi_scores))
           - (select score from ph_lpi_scores where country = 'Philippines'
              and dimension = 'customs' and year = (select max(year) from ph_lpi_scores)), 2);

-- fact: lpi.first
select score from ph_lpi_scores
where country = 'Philippines' and dimension = 'overall'
  and year = (select min(year) from ph_lpi_scores);

-- fact: lpi.change
select round((select score from ph_lpi_scores where country = 'Philippines'
              and dimension = 'overall' and year = (select max(year) from ph_lpi_scores))
           - (select score from ph_lpi_scores where country = 'Philippines'
              and dimension = 'overall' and year = (select min(year) from ph_lpi_scores)), 2);

-- fact: lpi.rounds
select count(distinct year) from ph_lpi_scores;

-- fact: lpi.firstyear
select min(year) from ph_lpi_scores;

-- fact: lpi.gap.years
select max(gap_years) from ph_lpi_rounds;

-- fact: lpi.best.rank
select min(rank_in_asean6) from ph_lpi_ranks where country = 'Philippines';

-- fact: lpi.worst.rank
select max(rank_in_asean6) from ph_lpi_ranks where country = 'Philippines';

-- fact: lpi.obs
select count(*) from ph_lpi_scores;
