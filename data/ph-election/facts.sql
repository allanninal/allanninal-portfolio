-- Facts published on projects/election-analysis.html
--
-- National figures come from Wikipedia's structured results templates, which
-- transcribe the Congress canvass and cite the Senate PDF that holds it.
-- Regional figures are scraped from the article's tables and are weaker; the
-- page says which is which rather than presenting both as equally solid.

-- fact: elec.winner.votes
select votes from ph_election_candidates where race = 'president' and rank = 1;

-- fact: elec.winner.share
select round(share_of_valid_pct, 2) from ph_election_candidates
where race = 'president' and rank = 1;

-- fact: elec.runnerup.votes
select votes from ph_election_candidates where race = 'president' and rank = 2;

-- fact: elec.runnerup.share
select round(share_of_valid_pct, 2) from ph_election_candidates
where race = 'president' and rank = 2;

-- fact: elec.margin.pts
select round((select share_of_valid_pct from ph_election_candidates
              where race = 'president' and rank = 1)
           - (select share_of_valid_pct from ph_election_candidates
              where race = 'president' and rank = 2), 1);

-- fact: elec.margin.votes
select (select votes from ph_election_candidates where race = 'president' and rank = 1)
     - (select votes from ph_election_candidates where race = 'president' and rank = 2);

-- fact: elec.ratio
select round((select votes from ph_election_candidates where race = 'president' and rank = 1)
           / (select votes from ph_election_candidates where race = 'president' and rank = 2)::double, 2);

-- fact: elec.candidates
select count(*) from ph_election_candidates where race = 'president';

-- fact: elec.valid
select value from ph_election_totals where race = 'president' and metric = 'valid';

-- fact: elec.invalid
select value from ph_election_totals where race = 'president' and metric = 'invalid';

-- fact: elec.invalid.pct
-- Ballots that reached a precinct and produced no valid presidential vote.
-- 2.21 million of them -- more than the fourth-placed candidate received, and
-- close to two-thirds of what the bottom seven candidates polled between them.
select round(100.0 * (select value from ph_election_totals
                      where race = 'president' and metric = 'invalid')
           / ((select value from ph_election_totals where race = 'president' and metric = 'valid')
            + (select value from ph_election_totals where race = 'president' and metric = 'invalid')), 2);

-- fact: elec.electorate
select value from ph_election_totals where race = 'president' and metric = 'electorate';

-- fact: elec.turnout
select round(value, 2) from ph_election_totals
where race = 'president' and metric = 'turnout_pct';

-- fact: elec.bottom7
select sum(votes) from ph_election_candidates where race = 'president' and rank >= 4;

-- fact: elec.vp.winner.votes
select votes from ph_election_candidates where race = 'vice_president' and rank = 1;

-- fact: elec.vp.winner.share
select round(share_of_valid_pct, 2) from ph_election_candidates
where race = 'vice_president' and rank = 1;

-- fact: elec.vp.invalid
select value from ph_election_totals where race = 'vice_president' and metric = 'invalid';

-- fact: elec.vp.invalid.excess
-- More people skipped the vice-presidential line than the presidential one.
select (select value from ph_election_totals where race = 'vice_president' and metric = 'invalid')
     - (select value from ph_election_totals where race = 'president' and metric = 'invalid');

-- fact: elec.regions
select count(distinct region) from ph_election_regions where race = 'president';

-- fact: elec.best.region
select region from ph_election_regions
where race = 'president' and candidate = 'Marcos'
order by 100.0 * votes / region_total desc limit 1;

-- fact: elec.best.region.share
select round(100.0 * votes / region_total, 1) from ph_election_regions
where race = 'president' and candidate = 'Marcos'
order by 100.0 * votes / region_total desc limit 1;

-- fact: elec.worst.region
select region from ph_election_regions
where race = 'president' and candidate = 'Marcos'
order by 100.0 * votes / region_total limit 1;

-- fact: elec.worst.region.share
select round(100.0 * votes / region_total, 1) from ph_election_regions
where race = 'president' and candidate = 'Marcos'
order by 100.0 * votes / region_total limit 1;

-- fact: elec.regions.won
select count(*) from (
    select region from ph_election_regions r
    where race = 'president' and candidate = 'Marcos'
      and votes = (select max(votes) from ph_election_regions x
                   where x.race = 'president' and x.region = r.region
                     and x.candidate <> 'Others'));

-- fact: elec.regional.coverage
select value from ph_election_totals
where race = 'president' and metric = 'regional_coverage_pct';

-- fact: elec.discrepancies
select count(*) from ph_election_source_discrepancies;
