-- One table of 1,000 forenames. Most of these checks exist because the file has
-- two columns that must agree, which is unusual and worth exploiting.

-- check: every row carries a source
-- level: error
select forename from ph_names_top where source is null or trim(source) = '';

-- check: the file is the size it claims
-- level: error
select count(*) from ph_names_top having count(*) <> 1000;

-- check: ranks are 1 to 1000 with no gaps or repeats
-- level: error
select count(*) n, min(rank) mn, max(rank) mx, count(distinct rank) d
from ph_names_top
having min(rank) <> 1 or max(rank) <> 1000 or count(distinct rank) <> 1000;

-- check: incidence falls as rank rises
-- level: error
-- The list is a ranking, so a name further down that has more bearers means the
-- rank or the incidence column has been misread.
select rank, forename, incidence, prev from (
  select rank, forename, incidence,
         lag(incidence) over (order by rank) prev
  from ph_names_top)
where prev is not null and incidence > prev;

-- check: incidence times frequency recovers the same population every time
-- level: error
-- This is the strongest thing the file offers. Incidence counts bearers and
-- frequency says one in N people, so their product is the population the data
-- was compiled against and must be near-constant. A 2% band allows for the
-- denominator being rounded to a whole number; anything wider would mean one of
-- the two columns does not mean what it says.
select forename, incidence, one_in_n, implied_population
from ph_names_top
where abs(implied_population
          - (select median(implied_population) from ph_names_top))
      > 0.02 * (select median(implied_population) from ph_names_top);

-- check: the implied base is a plausible Philippine population
-- level: error
select round(median(implied_population)) from ph_names_top
having median(implied_population) < 90000000
    or median(implied_population) > 120000000;

-- check: gender percentages are percentages
-- level: error
select forename, gender_pct from ph_names_top
where gender_pct is not null and gender_pct not between 50 and 100;

-- check: every name has a gender label
-- level: error
select forename from ph_names_top
where gender is null or trim(gender) = '';

-- check: initial counts sum to the whole file
-- level: error
select sum(names) from ph_names_initials
having sum(names) <> (select count(*) from ph_names_top);

-- check: initial people sum to the covered total
-- level: error
select sum(people) from ph_names_initials
having sum(people) <> (select sum(incidence) from ph_names_top);

-- check: initial shares sum to 100
-- level: error
select round(sum(pct_of_covered), 2) from ph_names_initials
having abs(sum(pct_of_covered) - 100) > 0.05;

-- check: the gender groups partition the file
-- level: error
select sum(names) n, sum(people) p from ph_names_gender
having sum(names) <> (select count(*) from ph_names_top)
    or sum(people) <> (select sum(incidence) from ph_names_top);

-- check: people per name is arithmetic, not asserted
-- level: error
select gender, people, names, people_per_name from ph_names_gender
where abs(people_per_name - people * 1.0 / names) > 1;

-- check: the ambiguous list matches its own threshold
-- level: error
-- The page quotes how many names the file is unsure about, so the flag and the
-- cutoff must not drift apart.
select count(*) from ph_names_ambiguous
having count(*) <> (select count(*) from ph_names_top where gender_pct < 90);

-- check: minority share is the complement of the stated share
-- level: error
select forename, gender_pct, minority_pct from ph_names_ambiguous
where gender_pct + minority_pct <> 100;

-- check: concentration is cumulative and ends at the whole file
-- level: error
select top_n_names, people, prev from (
  select top_n_names, people, lag(people) over (order by top_n_names) prev
  from ph_names_concentration)
where prev is not null and people < prev;

-- check: the last concentration row is the whole file
-- level: error
select people, pct_of_covered from ph_names_concentration
where top_n_names = 1000
  and (people <> (select sum(incidence) from ph_names_top)
       or abs(pct_of_covered - 100) > 0.01);

-- check: coverage records the six things this file cannot say
-- level: error
select property, value from ph_names_coverage
where property in ('collection date stated in the file', 'time dimension',
                   'regional or provincial split', 'surnames', 'age of bearers',
                   'methodology published by the source')
  and value <> 0;

-- check: the top thousand names do not cover everyone
-- level: warn
-- Recorded so the page cannot quietly present a partial list as a whole
-- population.
select value, note from ph_names_coverage
where property = 'share of the population covered';

-- check: single-character entries are recorded rather than silently kept
-- level: warn
-- "H" is in the list with 25,745 bearers. It may be a genuine recorded forename,
-- an initial standing in for one, or an extraction artefact in the source. The
-- page names it as a caveat rather than charting it as a name. The bound is one
-- character, not two: "Fe" and "Al" are also in the list and are ordinary
-- Filipino names.
select rank, forename, incidence from ph_names_top where length(forename) < 2;
