-- check: foreign direction vocabulary closure
-- level: error
-- foreign_net_php holds an unsigned magnitude and this column carries the sign.
-- An unrecognised word means the sign is being guessed, which is how a
-- five-year net-selling total was published as a positive number internally.
select distinct foreign_direction from ph_pse_annual_indicators
where foreign_direction not in ('net selling', 'net buying');

-- check: foreign magnitudes are unsigned
-- level: error
-- If a negative ever appears here the convention has silently changed and every
-- query that applies foreign_direction will double-negate it.
select year, foreign_net_php from ph_pse_annual_indicators where foreign_net_php < 0;

-- check: the two foreign-flow sources agree on direction (known)
-- level: warn
-- ph_pse_annual_indicators comes from PSE's published annual infographics;
-- ph_pse_foreign_annual is reconstructed from 380 weekly report PDFs. They
-- disagree on 2021: the infographic says net selling P2.75B, the weekly
-- reconstruction says net buying P2.08B. The page cites the infographic and
-- says so. Kept as a warning because it is a real source conflict, not a bug --
-- but it must stay visible rather than be resolved by picking a favourite.
select i.year,
       case when i.foreign_direction = 'net selling' then -i.foreign_net_php else i.foreign_net_php end infographic,
       f.net_php weekly_reports
from ph_pse_annual_indicators i join ph_pse_foreign_annual f on i.year = f.year
where sign(case when i.foreign_direction = 'net selling' then -1 else 1 end) <> sign(f.net_php);
