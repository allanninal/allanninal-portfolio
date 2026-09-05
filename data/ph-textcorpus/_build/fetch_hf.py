#!/usr/bin/env python3
"""Statistics for a Filipino/English hate-speech corpus from Hugging Face.

    .venv/bin/python data/ph-textcorpus/_build/fetch_hf.py

Dataset: mapsoriano/2016_2022_hate_speech_filipino -- election-related posts
from the 2016 and 2022 Philippine campaigns, labelled hate / non-hate. Published
openly with parquet conversions served by the datasets-server, so no key and no
scraping.

An editorial line that shapes the whole pipeline: NOTHING in the outputs
reproduces the text. This is a corpus of abuse aimed at real, named people. Every
CSV written here is an aggregate -- counts, lengths, distributions, and the
frequency of a fixed list of grammatical function words chosen in advance
precisely because they carry no content. No example posts, no top-content-words
table, no slur list. The interesting findings survive that constraint; a page
that quoted the corpus would be republishing the harassment.

The code-switching measure is a deliberately blunt instrument and the page says
so. Tagalog and English function words are counted per post from two fixed
lists. A post using both is "mixed". That misses loanwords, misspellings and
Taglish morphology entirely -- it is a floor on code-switching, not a
measurement of it.
"""
import csv
import io
import os
import re
import ssl
import urllib.parse
import urllib.request
from collections import Counter

try:
    import duckdb
except ImportError:
    raise SystemExit("needs duckdb:  make venv")

OUT = os.path.join(os.path.dirname(__file__), "..")
DATASET = "mapsoriano/2016_2022_hate_speech_filipino"
SRC = "Hugging Face: " + DATASET
UA = "allanninal.dev research (contact via github.com/allanninal)"
API = "https://datasets-server.huggingface.co/parquet?dataset="

# Fixed, content-free function words. Chosen before looking at the data so the
# lists cannot be tuned to produce a nicer answer.
TL = {"ang", "ng", "mga", "sa", "na", "ay", "at", "ako", "siya", "kami", "kayo",
      "sila", "ito", "iyon", "yung", "para", "kung", "pero", "hindi", "wala",
      "may", "meron", "naman", "lang", "din", "rin", "po", "ba", "daw", "raw",
      "kasi", "dahil", "pa", "nang", "ni", "kay", "isang", "yan", "ganun"}
EN = {"the", "of", "and", "to", "in", "is", "are", "was", "were", "for", "with",
      "that", "this", "it", "on", "as", "be", "have", "has", "not", "but", "you",
      "we", "they", "he", "she", "his", "her", "their", "our", "your", "from",
      "will", "would", "can", "could", "should", "there", "what", "which"}
TOKEN = re.compile(r"[a-z]+")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180,
                                context=ssl.create_default_context()) as r:
        return r.read()


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    import json
    meta = json.loads(get(API + urllib.parse.quote(DATASET, safe="")))
    files = meta.get("parquet_files", [])
    if not files:
        raise SystemExit("no parquet files listed for %s -- the dataset was "
                         "removed or made private" % DATASET)
    con = duckdb.connect()
    con.execute("install httpfs; load httpfs;")
    urls = {f["split"]: f["url"] for f in files}
    print("  splits: %s" % ", ".join(sorted(urls)))

    union = " union all ".join(
        "select '%s' as split, text, label from read_parquet('%s')" % (s, u)
        for s, u in sorted(urls.items()))
    con.execute("create view corpus as " + union)

    n = con.execute("select count(*) from corpus").fetchone()[0]
    print("  %d rows" % n)

    # -- split and label balance
    rows = con.execute("""
        select split, label, count(*) n,
               round(100.0 * count(*) / sum(count(*)) over (partition by split), 2) pct
        from corpus group by split, label order by split, label""").fetchall()
    write("ph_text_splits.csv",
          ["split", "label", "rows", "pct_of_split", "source"],
          [list(r) + [SRC] for r in rows])

    # -- duplicates. A benchmark that repeats the same post across train and
    #    test leaks the answer, and reported accuracy on it means less than it
    #    looks. Reported rather than removed.
    dup = con.execute("""
        select count(*) from (select text from corpus group by text having count(*) > 1)
    """).fetchone()[0]
    cross = con.execute("""
        select count(*) from (
            select text from corpus group by text
            having count(distinct split) > 1)""").fetchone()[0]
    exact = con.execute("select count(*) - count(distinct text) from corpus").fetchone()[0]
    write("ph_text_duplicates.csv",
          ["metric", "value", "note", "source"],
          [["distinct_texts_appearing_more_than_once", dup, "", SRC],
           ["texts_appearing_in_more_than_one_split", cross,
            "train/test leakage: the same post is both studied and graded", SRC],
           ["total_rows_beyond_first_occurrence", exact, "", SRC],
           ["total_rows", n, "", SRC]])
    print("  %d texts repeat; %d of those cross split boundaries" % (dup, cross))

    # -- length distribution by label
    rows = con.execute("""
        select label,
               count(*) n,
               round(avg(length(text)), 1) mean_chars,
               median(length(text)) median_chars,
               min(length(text)) min_chars,
               max(length(text)) max_chars,
               round(avg(array_length(string_split(trim(text), ' '))), 2) mean_words
        from corpus group by label order by label""").fetchall()
    write("ph_text_lengths.csv",
          ["label", "rows", "mean_chars", "median_chars", "min_chars",
           "max_chars", "mean_words", "source"],
          [list(r) + [SRC] for r in rows])

    # -- character-length histogram, 20-char buckets
    rows = con.execute("""
        -- Integer division. DuckDB's / is float division, so length/20*20
        -- returns the length unchanged and produces one bucket per distinct
        -- length -- 591 rows instead of 16.
        select least(length(text) // 20 * 20, 300) bucket, label, count(*) n
        from corpus group by bucket, label order by bucket, label""").fetchall()
    write("ph_text_length_hist.csv",
          ["char_bucket_start", "label", "rows", "source"],
          [list(r) + [SRC] for r in rows])

    # -- platform character limits. The length histogram has a hard cliff at
    #    140 characters and a second at 280 -- Twitter's limit before and after
    #    November 2017. This corpus spans the 2016 and 2022 campaigns, so both
    #    regimes are present, and the shape of the distribution is a property of
    #    the platform rather than of how Filipinos write.
    rows = con.execute("""
        select case when length(text) <= 140 then 'within the old 140-char limit'
                    when length(text) <= 280 then '141-280 (post-2017 limit)'
                    else 'over 280' end band,
               count(*) n, round(100.0 * count(*) / sum(count(*)) over (), 2) pct
        from corpus group by band order by 2 desc""").fetchall()
    write("ph_text_char_limits.csv",
          ["band", "rows", "pct_of_corpus", "source"],
          [list(r) + [SRC] for r in rows])

    # -- language mix, from the fixed function-word lists
    texts = con.execute("select split, label, lower(text) from corpus").fetchall()
    mix = Counter()
    per_label = Counter()
    for split, label, t in texts:
        toks = set(TOKEN.findall(t))
        has_tl, has_en = bool(toks & TL), bool(toks & EN)
        kind = ("mixed" if has_tl and has_en else
                "tagalog markers only" if has_tl else
                "english markers only" if has_en else "neither list matched")
        mix[kind] += 1
        per_label[(label, kind)] += 1
    write("ph_text_language_mix.csv",
          ["category", "rows", "pct_of_corpus", "method", "source"],
          [[k, v, round(100.0 * v / len(texts), 2),
            "fixed function-word lists; a floor on code-switching, not a measurement",
            SRC] for k, v in mix.most_common()])
    write("ph_text_language_by_label.csv",
          ["label", "category", "rows", "pct_of_label", "source"],
          [[lab, k, v,
            round(100.0 * v / sum(x for (l2, _), x in per_label.items() if l2 == lab), 2),
            SRC] for (lab, k), v in sorted(per_label.items())])

    # -- function-word frequency by label. Function words only, by design: see
    #    the module docstring. This is the only token-level table published.
    freq = Counter()
    for split, label, t in texts:
        for w in TOKEN.findall(t):
            if w in TL or w in EN:
                freq[(label, w)] += 1
    tot = {lab: sum(v for (l2, _), v in freq.items() if l2 == lab)
           for lab in {l for l, _ in freq}}
    rows = []
    for lab in sorted(tot):
        top = sorted(((w, v) for (l2, w), v in freq.items() if l2 == lab),
                     key=lambda x: -x[1])[:20]
        for w, v in top:
            rows.append([lab, w, v, round(100.0 * v / tot[lab], 3),
                         "tagalog" if w in TL else "english", SRC])
    # Share of matched function words that are Tagalog, per label. The top-20
    # tables hint that hate-labelled posts lean Tagalog; this puts a number on it
    # without quoting anything.
    lang = {}
    for lab in sorted(tot):
        tl = sum(v for (l2, w), v in freq.items() if l2 == lab and w in TL)
        lang[lab] = round(100.0 * tl / tot[lab], 2)
    write("ph_text_language_share.csv",
          ["label", "tagalog_share_of_function_words_pct", "method", "source"],
          [[lab, lang[lab],
            "fixed function-word lists; measures register, not topic", SRC]
           for lab in sorted(lang)])

    write("ph_text_function_words.csv",
          ["label", "word", "count", "pct_of_label_function_words", "language", "source"],
          rows)


if __name__ == "__main__":
    import urllib.parse
    main()
