-- Facts published on projects/philippine-names-analysis.html
--
-- One snapshot of the 1,000 commonest forenames. Nothing here is a trend, a
-- region or a birth record; every key describes this list.

-- fact: names.n
select value from ph_names_coverage where property = 'names in the file';

-- fact: names.people
select value from ph_names_coverage where property = 'people covered';

-- fact: names.base
-- Incidence times frequency, medianed across all thousand rows.
select value from ph_names_coverage where property = 'implied population base';

-- fact: names.base.low
select value from ph_names_coverage where property = 'implied base, lowest';

-- fact: names.base.high
select value from ph_names_coverage where property = 'implied base, highest';

-- fact: names.base.spread
-- How far apart the two ends of that agreement are, as a percentage.
select round(100.0 * ((select value from ph_names_coverage
                       where property = 'implied base, highest')::double
                    / (select value from ph_names_coverage
                       where property = 'implied base, lowest')::double - 1), 2);

-- fact: names.covered.pct
select value from ph_names_coverage
where property = 'share of the population covered';

-- fact: names.uncovered.pct
select round(100 - (select value from ph_names_coverage
                    where property = 'share of the population covered')::double, 2);

-- fact: names.uncovered.people
select round((select value from ph_names_coverage
              where property = 'implied population base')::double
           - (select value from ph_names_coverage
              where property = 'people covered')::double);

-- ---- the commonest ----------------------------------------------------------

-- fact: name.top
select forename from ph_names_top order by rank limit 1;

-- fact: name.top.n
select incidence from ph_names_top order by rank limit 1;

-- fact: name.top.freq
select one_in_n from ph_names_top order by rank limit 1;

-- fact: name.top.pct
select round(100.0 * (select incidence from ph_names_top order by rank limit 1)
           / (select value from ph_names_coverage
              where property = 'implied population base')::double, 2);

-- fact: name.second
select forename from ph_names_top where rank = 2;

-- fact: name.second.n
select incidence from ph_names_top where rank = 2;

-- fact: name.top.male
select forename from ph_names_top where gender = 'Male' order by rank limit 1;

-- fact: name.top.male.n
select incidence from ph_names_top where gender = 'Male' order by rank limit 1;

-- fact: name.top.over.second
select round((select incidence from ph_names_top order by rank limit 1)
           / (select incidence from ph_names_top where rank = 2)::double, 2);

-- fact: name.last.n
-- The thousandth name. The floor of the list.
select incidence from ph_names_top where rank = 1000;

-- fact: name.last
select forename from ph_names_top where rank = 1000;

-- ---- concentration -----------------------------------------------------------

-- fact: conc.10
select pct_of_covered from ph_names_concentration where top_n_names = 10;

-- fact: conc.100
select pct_of_covered from ph_names_concentration where top_n_names = 100;

-- fact: conc.100.people
select people from ph_names_concentration where top_n_names = 100;

-- fact: conc.100.of.pop
select pct_of_population from ph_names_concentration where top_n_names = 100;

-- fact: conc.500
select pct_of_covered from ph_names_concentration where top_n_names = 500;

-- ---- initials -----------------------------------------------------------------

-- fact: initial.top
select initial from ph_names_initials order by people desc limit 1;

-- fact: initial.top.pct
select pct_of_covered from ph_names_initials order by people desc limit 1;

-- fact: initial.top.people
select people from ph_names_initials order by people desc limit 1;

-- fact: initial.second
select initial from ph_names_initials order by people desc limit 1 offset 1;

-- fact: initial.second.pct
select pct_of_covered from ph_names_initials order by people desc limit 1 offset 1;

-- fact: initial.third
select initial from ph_names_initials order by people desc limit 1 offset 2;

-- fact: initial.fourth
-- The published page named R and A as the commonest initials. A is fourth.
select initial from ph_names_initials order by people desc limit 1 offset 3;

-- fact: initial.a.rank
select count(*) from ph_names_initials
where people >= (select people from ph_names_initials where initial = 'A');

-- fact: initial.top4.pct
select round(sum(pct_of_covered), 2) from (
  select pct_of_covered from ph_names_initials order by people desc limit 4);

-- fact: initial.n
select count(*) from ph_names_initials;

-- ---- gender -------------------------------------------------------------------

-- fact: gender.female.names
select names from ph_names_gender where gender = 'Female';

-- fact: gender.male.names
select names from ph_names_gender where gender = 'Male';

-- fact: gender.female.people
select people from ph_names_gender where gender = 'Female';

-- fact: gender.male.people
select people from ph_names_gender where gender = 'Male';

-- fact: gender.female.per.name
select people_per_name from ph_names_gender where gender = 'Female';

-- fact: gender.male.per.name
select people_per_name from ph_names_gender where gender = 'Male';

-- fact: gender.crowding
-- How much more crowded a male name is than a female one, on this list.
select round((select people_per_name from ph_names_gender where gender = 'Male')
           / (select people_per_name from ph_names_gender
              where gender = 'Female')::double, 2);

-- fact: gender.ambiguous
select count(*) from ph_names_ambiguous;

-- fact: gender.ambiguous.most
-- The name the file is least sure about.
select forename from ph_names_ambiguous order by gender_pct limit 1;

-- fact: gender.ambiguous.most.pct
select gender_pct from ph_names_ambiguous order by gender_pct limit 1;

-- fact: gender.ambiguous.most.minority
select minority_pct from ph_names_ambiguous order by gender_pct limit 1;

-- fact: names.single.letter
-- Entries of one or two characters. "H" carries 25,745 people, which is either a
-- real forename, an initial recorded as one, or an artefact of how the source
-- extracted names. The page says so rather than charting it.
select count(*) from ph_names_top where length(forename) < 2;

-- fact: names.single.letter.n
select incidence from ph_names_top where length(forename) < 2
order by incidence desc limit 1;

-- fact: names.missing.initials
-- Letters of the alphabet that begin no name in the top thousand.
select 26 - (select count(*) from ph_names_initials
             where initial between 'A' and 'Z');
