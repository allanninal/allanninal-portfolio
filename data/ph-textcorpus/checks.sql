-- Aggregates over a Filipino/English hate-speech corpus. Nothing in these CSVs
-- reproduces the text; see the fetcher docstring for why.

-- check: no CSV carries raw post text
-- level: error
-- The single most important assertion here. This corpus is abuse aimed at real,
-- named people, and a table that leaked example rows would republish it. The
-- function-word table is the only token-level output, and every word in it must
-- come from the two fixed grammatical lists.
select word from ph_text_function_words
where length(word) > 12 or word !~ '^[a-z]+$';

-- check: every row carries its source
-- level: error
select split, label from ph_text_splits where source is null or trim(source) = '';

-- check: split percentages sum to 100 within each split
-- level: error
select split, round(sum(pct_of_split), 2) from ph_text_splits
group by split having abs(sum(pct_of_split) - 100) > 0.05;

-- check: the corpus is close to balanced
-- level: error
-- A benchmark whose classes are wildly unbalanced makes accuracy meaningless.
-- This one is near 50/50 by design; if that ever stops being true, every
-- accuracy figure quoted about it needs revisiting.
select split, label, pct_of_split from ph_text_splits
where pct_of_split < 40 or pct_of_split > 60;

-- check: split sizes sum to the total row count
-- level: error
select (select sum(rows) from ph_text_splits) split_sum,
       (select value from ph_text_duplicates where metric = 'total_rows') declared
where (select sum(rows) from ph_text_splits)
   <> (select value from ph_text_duplicates where metric = 'total_rows');

-- check: language categories partition the corpus
-- level: error
select round(sum(pct_of_corpus), 2) from ph_text_language_mix
having abs(sum(pct_of_corpus) - 100) > 0.05;

-- check: language categories partition each label
-- level: error
select label, round(sum(pct_of_label), 2) from ph_text_language_by_label
group by label having abs(sum(pct_of_label) - 100) > 0.05;

-- check: character-limit bands partition the corpus
-- level: error
select round(sum(pct_of_corpus), 2) from ph_text_char_limits
having abs(sum(pct_of_corpus) - 100) > 0.05;

-- check: lengths are physically possible
-- level: error
select label, min_chars, max_chars, mean_chars from ph_text_lengths
where min_chars < 1 or max_chars > 10000 or mean_chars <= 0
   or mean_chars < min_chars or mean_chars > max_chars;

-- check: the histogram accounts for every row
-- level: error
select (select sum(rows) from ph_text_length_hist) hist,
       (select value from ph_text_duplicates where metric = 'total_rows') total
where (select sum(rows) from ph_text_length_hist)
   <> (select value from ph_text_duplicates where metric = 'total_rows');

-- check: the benchmark leaks between splits (known)
-- level: warn
-- 273 posts appear in more than one split, so a model can be graded on text it
-- was trained on. That inflates any accuracy reported against this benchmark.
-- Recorded, not silently deduplicated: the leak is a property of the published
-- dataset and removing it here would hide it from anyone comparing to published
-- scores.
select metric, value from ph_text_duplicates
where metric = 'texts_appearing_in_more_than_one_split' and value > 0;
