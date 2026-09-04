-- 2022 Philippine national election, via Wikipedia's transcription of the
-- Congress canvass. This is the weakest source chain in the repository, so the
-- checks here are heavier than usual: they are what stands in for a primary
-- feed that returns 403 to every script.

-- check: every row carries a revision id
-- level: error
-- Wikipedia is editable. A figure that cannot be pinned to a revision cannot be
-- rechecked later, which is the whole reason revid is carried per row.
select race, candidate from ph_election_candidates where revid is null
union all
select race, candidate from ph_election_regions where revid is null;

-- check: one revision per source page
-- level: error
select count(distinct revid) from ph_election_candidates having count(distinct revid) > 2;

-- check: candidate votes are positive
-- level: error
select race, candidate, votes from ph_election_candidates where votes <= 0;

-- check: candidate votes sum to the stated valid total
-- level: error
-- The templates publish both the per-candidate votes and a valid-vote total.
-- They must agree exactly; a parse that drops or duplicates a candidate shows
-- up here and nowhere else.
select c.race, sum(c.votes) summed, any_value(t.value) declared
from ph_election_candidates c
join ph_election_totals t on t.race = c.race and t.metric = 'valid'
group by c.race having sum(c.votes) <> any_value(t.value);

-- check: shares sum to 100
-- level: error
select race, round(sum(share_of_valid_pct), 2) from ph_election_candidates
group by race having abs(sum(share_of_valid_pct) - 100) > 0.02;

-- check: turnout is plausible
-- level: error
select race, value from ph_election_totals
where metric = 'turnout_pct' and (value <= 0 or value > 100);

-- check: votes cast never exceed the electorate
-- level: error
select race from ph_election_totals t
where metric = 'valid'
  and value + (select value from ph_election_totals i
               where i.race = t.race and i.metric = 'invalid')
      > (select value from ph_election_totals e
         where e.race = t.race and e.metric = 'electorate');

-- check: every region reconciles to its own stated total
-- level: error
-- This is the check that earned its keep. Three separate parse faults were
-- caught here and nowhere else: a {{white|...}} wrapper being stripped along
-- with the vote count it contained, a bgcolor attribute whose hex digits were
-- glued onto the number beside it, and percentage cells losing their decimal
-- point. Each produced a page that looked entirely reasonable.
select race, region, sum(votes) summed, any_value(region_total) stated
from ph_election_regions
group by race, region having sum(votes) <> any_value(region_total);

-- check: every region has the same candidate set
-- level: error
select race, region, count(*) n from ph_election_regions
group by race, region
having count(*) <> (select max(c) from (
    select count(*) c from ph_election_regions group by race, region));

-- check: the Others column is derived, not published
-- level: error
-- The published Others disagrees with its own share in three regions, so it is
-- recomputed as the remainder. If a row ever claims to publish it, the
-- discrepancy is back inside the numbers.
select race, region, basis from ph_election_regions
where candidate = 'Others' and basis <> 'derived as total minus named';

-- check: primary source URLs are carried through
-- level: error
-- comelec.gov.ph and legacy.senate.gov.ph both return 403 to scripts, so the
-- page cannot fetch the primary record -- but it can and does print the exact
-- URLs so a reader with a browser can check them.
select race from ph_election_totals
where metric = 'primary_source_urls' and (note is null or note not like 'http%');

-- check: the source disagrees with itself in the Others column (known)
-- level: warn
-- Three regions publish an Others vote count that does not match the Others
-- share printed beside it: IV-B states 7.44% against 12.94% implied, and VI and
-- VII disagree by about a point in opposite directions. Recorded rather than
-- silently corrected, because it is a fact about the source.
select region, published_votes, published_share_pct, share_implied_by_votes_pct
from ph_election_source_discrepancies;

-- check: the presidential regional table is incomplete (known)
-- level: warn
-- Its eighteen rows sum to 97.8% of the valid vote its own total row declares --
-- about 1.18 million votes appear in no region. The vice-presidential table sums
-- to exactly 100%. Regional figures must therefore never be presented as adding
-- up to the national result, and the page says so.
select race, value from ph_election_totals
where metric = 'regional_coverage_pct' and value < 99.9;
