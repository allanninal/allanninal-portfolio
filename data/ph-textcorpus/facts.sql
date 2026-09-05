-- Facts published on projects/social-media-analysis.html
--
-- One corpus, analysed properly, in place of six that were never opened. Every
-- figure is an aggregate: no post text appears in any CSV or on the page.

-- fact: txt.rows
select value from ph_text_duplicates where metric = 'total_rows';

-- fact: txt.train
select rows from ph_text_splits where split = 'train' and label = 0;

-- fact: txt.splits
select count(distinct split) from ph_text_splits;

-- fact: txt.hate
select sum(rows) from ph_text_splits where label = 1;

-- fact: txt.nonhate
select sum(rows) from ph_text_splits where label = 0;

-- fact: txt.balance
select round(100.0 * sum(case when label = 1 then rows else 0 end) / sum(rows), 2)
from ph_text_splits;

-- fact: txt.leak
-- Posts appearing in more than one split. A model can be graded on text it was
-- trained on, which inflates any accuracy reported against this benchmark.
select value from ph_text_duplicates
where metric = 'texts_appearing_in_more_than_one_split';

-- fact: txt.leak.pct
select round(100.0 * (select value from ph_text_duplicates
                      where metric = 'texts_appearing_in_more_than_one_split')
           / (select value from ph_text_duplicates where metric = 'total_rows'), 2);

-- fact: txt.dupes
select value from ph_text_duplicates where metric = 'total_rows_beyond_first_occurrence';

-- fact: txt.mean.chars.hate
select mean_chars from ph_text_lengths where label = 1;

-- fact: txt.mean.chars.nonhate
select mean_chars from ph_text_lengths where label = 0;

-- fact: txt.median.chars.hate
select median_chars from ph_text_lengths where label = 1;

-- fact: txt.max.chars
select max(max_chars) from ph_text_lengths;

-- fact: txt.under140
-- The old Twitter character limit is visible as a cliff in the length
-- histogram: this corpus spans the 2016 and 2022 campaigns, and the platform
-- doubled its limit in between.
select pct_of_corpus from ph_text_char_limits
where band = 'within the old 140-char limit';

-- fact: txt.141to280
select pct_of_corpus from ph_text_char_limits where band = '141-280 (post-2017 limit)';

-- fact: txt.over280
select pct_of_corpus from ph_text_char_limits where band = 'over 280';

-- fact: txt.mixed
select pct_of_corpus from ph_text_language_mix where category = 'mixed';

-- fact: txt.tagalog.only
select pct_of_corpus from ph_text_language_mix where category = 'tagalog markers only';

-- fact: txt.english.only
select pct_of_corpus from ph_text_language_mix where category = 'english markers only';

-- fact: txt.nomatch
select pct_of_corpus from ph_text_language_mix where category = 'neither list matched';

-- fact: txt.tl.share.hate
select tagalog_share_of_function_words_pct from ph_text_language_share where label = 1;

-- fact: txt.tl.share.nonhate
select tagalog_share_of_function_words_pct from ph_text_language_share where label = 0;

-- fact: txt.tl.gap
select round((select tagalog_share_of_function_words_pct from ph_text_language_share where label = 1)
           - (select tagalog_share_of_function_words_pct from ph_text_language_share where label = 0), 2);

-- fact: txt.tlonly.hate
select pct_of_label from ph_text_language_by_label
where label = 1 and category = 'tagalog markers only';

-- fact: txt.tlonly.nonhate
select pct_of_label from ph_text_language_by_label
where label = 0 and category = 'tagalog markers only';

-- fact: txt.top.word.hate
select word from ph_text_function_words where label = 1 order by count desc limit 1;

-- fact: txt.top.word.nonhate
select word from ph_text_function_words where label = 0 order by count desc limit 1;
