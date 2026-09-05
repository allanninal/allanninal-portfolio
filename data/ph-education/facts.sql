-- Facts published on projects/education-analysis.html
--
-- Keys named deped.* come from DepEd public-school administrative counts, 11
-- academic years, 17 regions. Keys named ph.* are national UIS estimates and
-- include private schools and children not enrolled at all. The two are not
-- interchangeable and the page keeps them apart.

-- ---- the DepEd file ---------------------------------------------------------

-- fact: deped.years
select value from ph_education_coverage where property = 'academic years';

-- fact: deped.rows
select value from ph_education_coverage where property = 'rows';

-- fact: deped.regions
select value from ph_education_coverage where property = 'regions';

-- fact: deped.first.year
select academic_year from ph_education_national order by ay_start limit 1;

-- fact: deped.last.year
select academic_year from ph_education_national order by ay_start desc limit 1;

-- ---- enrollment against staffing --------------------------------------------

-- fact: deped.enrol.first
select enrollees from ph_education_national order by ay_start limit 1;

-- fact: deped.enrol.last
select enrollees from ph_education_national order by ay_start desc limit 1;

-- fact: deped.enrol.change
select value from ph_education_coverage
where property = 'enrollment change over the period';

-- fact: deped.teachers.first
select teachers from ph_education_national order by ay_start limit 1;

-- fact: deped.teachers.last
select teachers from ph_education_national order by ay_start desc limit 1;

-- fact: deped.teachers.change
select value from ph_education_coverage
where property = 'teacher change over the period';

-- fact: deped.teachers.added
select (select teachers from ph_education_national order by ay_start desc limit 1)
     - (select teachers from ph_education_national order by ay_start limit 1);

-- fact: deped.ratio.first
select pupils_per_teacher from ph_education_national order by ay_start limit 1;

-- fact: deped.ratio.last
select pupils_per_teacher from ph_education_national order by ay_start desc limit 1;

-- fact: deped.ratio.drop
-- Per cent fall in the blended national pupil-teacher ratio.
select round(100.0 * (1 - (select pupils_per_teacher from ph_education_national
                           order by ay_start desc limit 1)
                        / (select pupils_per_teacher from ph_education_national
                           order by ay_start limit 1)), 1);

-- fact: deped.growth.ratio
-- Teachers grew this many times as fast as enrollment.
select round((select value from ph_education_coverage
              where property = 'teacher change over the period')::double
           / (select value from ph_education_coverage
              where property = 'enrollment change over the period')::double, 2);

-- ---- by level ---------------------------------------------------------------

-- fact: deped.elem.ratio.first
select pupils_per_teacher from ph_education_levels
where level = 'elementary' order by ay_start limit 1;

-- fact: deped.elem.ratio.last
select pupils_per_teacher from ph_education_levels
where level = 'elementary' order by ay_start desc limit 1;

-- fact: deped.jhs.ratio.first
select pupils_per_teacher from ph_education_levels
where level = 'junior high' order by ay_start limit 1;

-- fact: deped.jhs.ratio.last
select pupils_per_teacher from ph_education_levels
where level = 'junior high' order by ay_start desc limit 1;

-- fact: deped.elem.enrol.last
-- Elementary enrollment actually fell over the period, which is the one place
-- the pupil-teacher ratio improved for a reason other than hiring.
select enrollees from ph_education_levels
where level = 'elementary' order by ay_start desc limit 1;

-- fact: deped.elem.enrol.change
select round(100.0 * ((select enrollees from ph_education_levels
                       where level = 'elementary' order by ay_start desc limit 1)
                    / (select enrollees from ph_education_levels
                       where level = 'elementary' order by ay_start limit 1)::double
                     - 1), 2);

-- fact: deped.jhs.enrol.change
select round(100.0 * ((select enrollees from ph_education_levels
                       where level = 'junior high' order by ay_start desc limit 1)
                    / (select enrollees from ph_education_levels
                       where level = 'junior high' order by ay_start limit 1)::double
                     - 1), 2);

-- ---- the K-12 rollout -------------------------------------------------------

-- fact: shs.first.year
select academic_year from ph_education_shs where enrollees > 0
order by ay_start limit 1;

-- fact: shs.first.enrol
select enrollees from ph_education_shs where enrollees > 0
order by ay_start limit 1;

-- fact: shs.last.enrol
select enrollees from ph_education_shs order by ay_start desc limit 1;

-- fact: shs.growth
select round((select enrollees from ph_education_shs order by ay_start desc limit 1)
           / (select enrollees from ph_education_shs where enrollees > 0
              order by ay_start limit 1)::double, 2);

-- fact: shs.teachers.first
select teachers from ph_education_shs where enrollees > 0 order by ay_start limit 1;

-- fact: shs.teachers.last
select teachers from ph_education_shs order by ay_start desc limit 1;

-- fact: shs.ratio.first
-- The tier opened better staffed than either of the others.
select pupils_per_teacher from ph_education_shs where enrollees > 0
order by ay_start limit 1;

-- fact: shs.ratio.worst
select max(pupils_per_teacher) from ph_education_shs where enrollees > 0;

-- fact: shs.ratio.worst.year
select academic_year from ph_education_shs where enrollees > 0
order by pupils_per_teacher desc limit 1;

-- fact: shs.ratio.last
select pupils_per_teacher from ph_education_shs order by ay_start desc limit 1;

-- fact: shs.share.of.enrol
-- Senior high as a share of all public basic-education enrollment, latest year.
select round(100.0 * (select enrollees_shs from ph_education_national
                      order by ay_start desc limit 1)
           / (select enrollees from ph_education_national
              order by ay_start desc limit 1), 2);

-- ---- track choice -----------------------------------------------------------

-- fact: track.top
select track from ph_education_tracks
where ay_start = (select max(ay_start) from ph_education_tracks)
order by enrollees desc limit 1;

-- fact: track.top.pct
select pct_of_shs from ph_education_tracks
where ay_start = (select max(ay_start) from ph_education_tracks)
order by enrollees desc limit 1;

-- fact: track.top.n
select enrollees from ph_education_tracks
where ay_start = (select max(ay_start) from ph_education_tracks)
order by enrollees desc limit 1;

-- fact: track.stem.pct
select pct_of_shs from ph_education_tracks
where ay_start = (select max(ay_start) from ph_education_tracks)
  and track = 'STEM';

-- fact: track.stem.n
select enrollees from ph_education_tracks
where ay_start = (select max(ay_start) from ph_education_tracks)
  and track = 'STEM';

-- fact: track.tvl.over.stem
select round((select enrollees from ph_education_tracks
              where ay_start = (select max(ay_start) from ph_education_tracks)
                and track = 'TVL')
           / (select enrollees from ph_education_tracks
              where ay_start = (select max(ay_start) from ph_education_tracks)
                and track = 'STEM')::double, 2);

-- fact: track.stem.rank
-- Where STEM sits among the eight tracks, largest first.
select count(*) from ph_education_tracks a
where a.ay_start = (select max(ay_start) from ph_education_tracks)
  and a.enrollees >= (select enrollees from ph_education_tracks
                      where ay_start = (select max(ay_start) from ph_education_tracks)
                        and track = 'STEM');

-- fact: track.academic.pct
-- The four academic strands together: ABM, HUMSS, STEM, GAS.
select round(sum(pct_of_shs), 2) from ph_education_tracks
where ay_start = (select max(ay_start) from ph_education_tracks)
  and track in ('ABM', 'HUMSS', 'STEM', 'GAS');

-- fact: track.smallest
select track from ph_education_tracks
where ay_start = (select max(ay_start) from ph_education_tracks)
order by enrollees limit 1;

-- fact: track.smallest.n
select enrollees from ph_education_tracks
where ay_start = (select max(ay_start) from ph_education_tracks)
order by enrollees limit 1;

-- fact: track.n
select count(*) from ph_education_tracks
where ay_start = (select max(ay_start) from ph_education_tracks);

-- ---- geography ---------------------------------------------------------------

-- fact: region.worst
select region from ph_education_by_region
where ay_start = (select max(ay_start) from ph_education_by_region)
order by pupils_per_teacher desc limit 1;

-- fact: region.worst.ratio
select pupils_per_teacher from ph_education_by_region
where ay_start = (select max(ay_start) from ph_education_by_region)
order by pupils_per_teacher desc limit 1;

-- fact: region.best
select region from ph_education_by_region
where ay_start = (select max(ay_start) from ph_education_by_region)
order by pupils_per_teacher limit 1;

-- fact: region.best.ratio
select pupils_per_teacher from ph_education_by_region
where ay_start = (select max(ay_start) from ph_education_by_region)
order by pupils_per_teacher limit 1;

-- fact: region.spread
select round((select pupils_per_teacher from ph_education_by_region
              where ay_start = (select max(ay_start) from ph_education_by_region)
              order by pupils_per_teacher desc limit 1)
           - (select pupils_per_teacher from ph_education_by_region
              where ay_start = (select max(ay_start) from ph_education_by_region)
              order by pupils_per_teacher limit 1), 2);

-- fact: region.biggest
select region from ph_education_by_region
where ay_start = (select max(ay_start) from ph_education_by_region)
order by enrollees desc limit 1;

-- fact: region.biggest.n
select enrollees from ph_education_by_region
where ay_start = (select max(ay_start) from ph_education_by_region)
order by enrollees desc limit 1;

-- ---- what enrollment cannot say ---------------------------------------------

-- fact: ph.primary.completion
select primary_completion_pct from ph_education_outcomes
where primary_completion_pct is not null order by year desc limit 1;

-- fact: ph.primary.completion.year
select year from ph_education_outcomes
where primary_completion_pct is not null order by year desc limit 1;

-- fact: ph.primary.missing
-- The share of a primary cohort that does not complete it.
select round(100 - (select primary_completion_pct from ph_education_outcomes
                    where primary_completion_pct is not null
                    order by year desc limit 1), 2);

-- fact: ph.outofschool
select primary_age_out_of_school from ph_education_outcomes
where primary_age_out_of_school is not null order by year desc limit 1;

-- fact: ph.outofschool.year
select year from ph_education_outcomes
where primary_age_out_of_school is not null order by year desc limit 1;

-- fact: ph.secondary.net
-- Net enrolment counts only pupils of the official age for the level, so it is
-- the figure that shows who is missing.
select secondary_net_enrolment_pct from ph_education_outcomes
where secondary_net_enrolment_pct is not null order by year desc limit 1;

-- fact: ph.secondary.net.year
select year from ph_education_outcomes
where secondary_net_enrolment_pct is not null order by year desc limit 1;

-- fact: ph.secondary.gross
-- Taken from the same year as the net figure, not from the latest year gross is
-- available. Gross runs to 2024 and net stops at 2015, so pairing each with its
-- own latest year would put 85.29 and 65.56 on the page beside a gap of 16.45 --
-- three numbers that do not add up, which is exactly the kind of
-- self-contradiction this project has published before.
select secondary_gross_enrolment_pct from ph_education_outcomes
where secondary_net_enrolment_pct is not null order by year desc limit 1;

-- fact: ph.secondary.gross.latest
-- The most recent gross figure, stated with its own year wherever it is used.
select secondary_gross_enrolment_pct from ph_education_outcomes
where secondary_gross_enrolment_pct is not null order by year desc limit 1;

-- fact: ph.secondary.gross.latest.year
select year from ph_education_outcomes
where secondary_gross_enrolment_pct is not null order by year desc limit 1;

-- fact: ph.secondary.gap
select round((select secondary_gross_enrolment_pct from ph_education_outcomes
              where secondary_net_enrolment_pct is not null
              order by year desc limit 1)
           - (select secondary_net_enrolment_pct from ph_education_outcomes
              where secondary_net_enrolment_pct is not null
              order by year desc limit 1), 2);

-- fact: ph.literacy
select adult_literacy_pct from ph_education_outcomes
where adult_literacy_pct is not null order by year desc limit 1;

-- fact: ph.tertiary
select tertiary_gross_enrolment_pct from ph_education_outcomes
where tertiary_gross_enrolment_pct is not null order by year desc limit 1;

-- ---- money -------------------------------------------------------------------

-- fact: ph.spend
select education_spend_pct_gdp from ph_education_outcomes
where education_spend_pct_gdp is not null order by year desc limit 1;

-- fact: ph.spend.year
select year from ph_education_outcomes
where education_spend_pct_gdp is not null order by year desc limit 1;

-- fact: spend.asean.year
select distinct year from ph_education_spend_asean;

-- fact: spend.asean.rank
-- Rank among the countries whose series is comparable, highest spender first.
select count(*) from ph_education_spend_asean
where comparable = 'yes'
  and education_spend_pct_gdp >= (select education_spend_pct_gdp
                                  from ph_education_spend_asean
                                  where country = 'Philippines');

-- fact: spend.asean.n
select count(*) from ph_education_spend_asean where comparable = 'yes';

-- fact: spend.ph
select education_spend_pct_gdp from ph_education_spend_asean
where country = 'Philippines';

-- fact: spend.excluded
select count(*) from ph_education_spend_asean where comparable = 'no';
