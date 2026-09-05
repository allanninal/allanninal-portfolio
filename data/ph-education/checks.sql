-- DepEd public-school counts, plus UIS national outcomes. The checks mostly
-- guard against pairing one level's pupils with another level's teachers, and
-- against reading a reporting change as a policy change.

-- check: every row carries a source
-- level: error
select academic_year from ph_education_by_region
where source is null or trim(source) = '';

-- check: every year has all seventeen regions
-- level: error
select academic_year, regions from ph_education_national where regions <> 17;

-- check: the file is the shape it should be
-- level: error
select count(*) from ph_education_by_region having count(*) <> 187;

-- check: regional enrollment sums to the national total
-- level: error
select n.academic_year, n.enrollees, sum(r.enrollees) regional
from ph_education_national n
join ph_education_by_region r on r.academic_year = n.academic_year
group by 1, 2 having n.enrollees <> sum(r.enrollees);

-- check: regional teacher counts sum to the national total
-- level: error
select n.academic_year, n.teachers, sum(r.teachers) regional
from ph_education_national n
join ph_education_by_region r on r.academic_year = n.academic_year
group by 1, 2 having n.teachers <> sum(r.teachers);

-- check: the three levels partition national enrollment
-- level: error
-- Senior-high columns are matched by prefix because the source spells one of them
-- Enrollees_G122_SPORTs. If that match ever stops working, those pupils fall out
-- of the total and this is what notices.
select academic_year, enrollees,
       enrollees_elem + enrollees_jhs + enrollees_shs parts
from ph_education_national
where enrollees <> enrollees_elem + enrollees_jhs + enrollees_shs;

-- check: the three levels partition the teacher count
-- level: error
select academic_year, teachers,
       teachers_elem + teachers_jhs + teachers_shs parts
from ph_education_national
where teachers <> teachers_elem + teachers_jhs + teachers_shs;

-- check: each level's ratio uses its own enrollment and its own teachers
-- level: error
-- A blended ratio would hide that the three tiers are staffed differently, and
-- crossing them would be invisible on a chart.
select academic_year, level, enrollees, teachers, pupils_per_teacher
from ph_education_levels
where teachers > 0
  and abs(pupils_per_teacher - enrollees * 1.0 / teachers) > 0.011;

-- check: level enrollment matches the national table
-- level: error
select l.academic_year, l.level, l.enrollees
from ph_education_levels l join ph_education_national n
  on n.academic_year = l.academic_year
where (l.level = 'elementary' and l.enrollees <> n.enrollees_elem)
   or (l.level = 'junior high' and l.enrollees <> n.enrollees_jhs)
   or (l.level = 'senior high' and l.enrollees <> n.enrollees_shs);

-- check: senior high is empty before it existed, and not after
-- level: error
-- The K-12 rollout is the page's spine. If a stray value appeared before
-- SY 2016-2017 the grade-column matching has gone wrong.
select academic_year, enrollees, teachers from ph_education_shs
where (ay_start < 2016 and (enrollees <> 0 or teachers <> 0))
   or (ay_start >= 2016 and enrollees = 0);

-- check: a level with no pupils and no teachers says so
-- level: error
select academic_year, level, note from ph_education_levels
where enrollees = 0 and teachers = 0 and (note is null or trim(note) = '');

-- check: track shares sum to 100 in every year senior high exists
-- level: error
select academic_year, round(sum(pct_of_shs), 2) from ph_education_tracks
group by 1 having abs(sum(pct_of_shs) - 100) > 0.05;

-- check: track counts sum to the senior-high total
-- level: error
select academic_year, sum(enrollees) parts, max(shs_total) declared
from ph_education_tracks group by 1
having sum(enrollees) <> max(shs_total);

-- check: track totals match the national senior-high column
-- level: error
-- "national" is a reserved word in DuckDB, so the alias is nat.
select t.academic_year, max(t.shs_total) tracks, max(n.enrollees_shs) nat
from ph_education_tracks t join ph_education_national n
  on n.academic_year = t.academic_year
group by 1 having max(t.shs_total) <> max(n.enrollees_shs);

-- check: all eight senior-high tracks are present every year
-- level: error
select academic_year, count(*) n from ph_education_tracks
group by 1 having count(*) <> 8;

-- check: outcome percentages are percentages
-- level: error
select year, primary_completion_pct, secondary_net_enrolment_pct
from ph_education_outcomes
where (primary_completion_pct is not null
       and primary_completion_pct not between 0 and 130)
   or (secondary_net_enrolment_pct is not null
       and secondary_net_enrolment_pct not between 0 and 100)
   or (adult_literacy_pct is not null
       and adult_literacy_pct not between 0 and 100);

-- check: net enrolment never exceeds gross enrolment
-- level: error
-- Net counts only pupils of the official age for the level; gross counts all
-- enrolled pupils regardless of age, so gross is always the larger. A crossing
-- means the two indicator codes have been swapped.
select year, secondary_net_enrolment_pct, secondary_gross_enrolment_pct
from ph_education_outcomes
where secondary_net_enrolment_pct is not null
  and secondary_gross_enrolment_pct is not null
  and secondary_net_enrolment_pct > secondary_gross_enrolment_pct;

-- check: every ASEAN country appears in the spending comparison
-- level: error
select count(*) from ph_education_spend_asean having count(*) <> 6;

-- check: the spending comparison uses one year
-- level: error
select count(distinct year) from ph_education_spend_asean
having count(distinct year) <> 1;

-- check: a country marked not comparable states why
-- level: error
-- Indonesia's series falls from 3.58% of GDP in 2015 to about 1% after, which is
-- a change in what it reports to UIS rather than in what it spends. The row is
-- kept and labelled, because dropping a country makes a six-country chart look
-- like a five-country one.
select country, comparable, note from ph_education_spend_asean
where comparable = 'no' and (note is null or trim(note) = '');

-- check: coverage records what enrollment data cannot say
-- level: error
select property, value from ph_education_coverage
where property in ('private schools', 'learning outcomes',
                   'dropouts or repetition', 'school or class counts')
  and value <> 0;

-- check: senior high is more crowded than when it started (known)
-- level: warn
-- Recorded because it runs against the direction of every other ratio here: the
-- new tier opened at 19.9 pupils per teacher and was at 26.83 four years later.
select academic_year, pupils_per_teacher from ph_education_levels
where level = 'senior high' and pupils_per_teacher > 25;

-- check: at least one country is excluded from the spending ranking (known)
-- level: warn
select country, education_spend_pct_gdp, note from ph_education_spend_asean
where comparable = 'no';

-- check: the two secondary enrolment figures the page pairs share a year
-- level: error
-- Gross runs to 2024 and net stops at 2015. Pairing each with its own latest
-- year would put a gross, a net and a gap on the page that do not add up.
select year, secondary_gross_enrolment_pct, secondary_net_enrolment_pct
from ph_education_outcomes
where secondary_net_enrolment_pct is not null
  and secondary_gross_enrolment_pct is null;
