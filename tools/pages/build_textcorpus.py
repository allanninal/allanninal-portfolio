#!/usr/bin/env python3
"""Regenerate projects/social-media-analysis.html from data/ph-textcorpus CSVs.

    .venv/bin/python tools/pages/build_textcorpus.py

The page this replaces claimed 42,000+ text samples across 6 datasets, 6 NLP
tasks and an 87.2% best model accuracy. No model was trained and no dataset was
opened; nine of its twelve chart arrays were perfectly monotone.

This version opens one dataset -- mapsoriano/2016_2022_hate_speech_filipino,
27,383 labelled posts -- and reports what is actually in it.

The editorial rule that shapes everything: no post text appears on this page or
in any CSV behind it. The corpus is abuse directed at real, named people.
Quoting it to illustrate a chart would republish the harassment, and a
"most frequent words" table would print slurs. The only token-level output is
the frequency of grammatical function words from two fixed lists chosen in
advance. Every finding below survives that constraint.
"""
import csv
import json
import os
import re

D = "data/ph-textcorpus"
PAGE = "projects/social-media-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def js(x):
    return json.dumps(x)


def main():
    sp = rows("ph_text_splits")
    dup = {r["metric"]: int(r["value"]) for r in rows("ph_text_duplicates")}
    ln = rows("ph_text_lengths")
    hist = rows("ph_text_length_hist")
    mix = rows("ph_text_language_mix")
    bylab = rows("ph_text_language_by_label")
    lim = rows("ph_text_char_limits")
    share = rows("ph_text_language_share")
    fw = rows("ph_text_function_words")

    g = lambda t, k, v: [r for r in t if r[k] == v][0]
    F = dict(
        rows=dup["total_rows"], leak=dup["texts_appearing_in_more_than_one_split"],
        dupes=dup["total_rows_beyond_first_occurrence"],
        hate=sum(int(r["rows"]) for r in sp if r["label"] == "1"),
        nonhate=sum(int(r["rows"]) for r in sp if r["label"] == "0"),
        splits=len({r["split"] for r in sp}),
        mch=float(g(ln, "label", "1")["mean_chars"]),
        mcn=float(g(ln, "label", "0")["mean_chars"]),
        maxc=max(int(r["max_chars"]) for r in ln),
        u140=float(g(lim, "band", "within the old 140-char limit")["pct_of_corpus"]),
        b280=float(g(lim, "band", "141-280 (post-2017 limit)")["pct_of_corpus"]),
        o280=float(g(lim, "band", "over 280")["pct_of_corpus"]),
        mixed=float(g(mix, "category", "mixed")["pct_of_corpus"]),
        tlonly=float(g(mix, "category", "tagalog markers only")["pct_of_corpus"]),
        enonly=float(g(mix, "category", "english markers only")["pct_of_corpus"]),
        nomatch=float(g(mix, "category", "neither list matched")["pct_of_corpus"]),
        tlh=float(g(share, "label", "1")["tagalog_share_of_function_words_pct"]),
        tln=float(g(share, "label", "0")["tagalog_share_of_function_words_pct"]),
        tloh=float([r for r in bylab if r["label"] == "1"
                    and r["category"] == "tagalog markers only"][0]["pct_of_label"]),
        tlon=float([r for r in bylab if r["label"] == "0"
                    and r["category"] == "tagalog markers only"][0]["pct_of_label"]),
    )
    F["balance"] = round(100.0 * F["hate"] / F["rows"], 2)
    F["leakpct"] = round(100.0 * F["leak"] / F["rows"], 2)
    F["tlgap"] = round(F["tlh"] - F["tln"], 2)

    hero = '''                <h1>What Is Actually In A Filipino Hate-Speech Corpus</h1>
                <p class="hero-description">
                    One openly published benchmark of {rows:,} labelled posts from the
                    2016 and 2022 election campaigns, opened and measured. No post text
                    appears anywhere on this page &mdash; the corpus is abuse aimed at
                    real people, and quoting it to decorate a chart would republish it.
                </p>

                <div class="header-actions">
                    <a href="https://huggingface.co/datasets/mapsoriano/2016_2022_hate_speech_filipino" target="_blank" class="btn btn-primary">
                        The dataset on Hugging Face
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="txt.rows">{rows:,}</div>
                        <div class="stat-label">Labelled posts</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="txt.leak">{leak}</div>
                        <div class="stat-label">Posts in more than one split</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="txt.under140">{u140}%</div>
                        <div class="stat-label">Fit the old 140-char limit</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="txt.tl.gap">{tlgap}</div>
                        <div class="stat-label">Point Tagalog gap between labels</div>
                    </div>
                </div>
'''.format(**F)

    tldr = '''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Opening one dataset properly beats listing six. This corpus is well balanced, quietly leaky, and shaped as much by a platform's character limit as by how anyone writes.</p>
                    <ul class="tldr-list">
                        <li><span data-fact="txt.leak">{leak}</span> posts appear in more than one split &mdash; <span data-fact="txt.leak.pct">{leakpct}%</span> of the corpus. A model can be graded on text it was trained on, so any accuracy reported against this benchmark is flattered by an unknown amount.</li>
                        <li><span data-fact="txt.under140">{u140}%</span> of posts fit inside 140 characters, with a hard cliff there in the length distribution. That is Twitter's pre-2017 limit, not a fact about Filipino writing: the corpus spans campaigns on either side of the change.</li>
                        <li>Hate-labelled posts are markedly more Tagalog. <span data-fact="txt.tl.share.hate">{tlh}%</span> of their function words are Tagalog against <span data-fact="txt.tl.share.nonhate">{tln}%</span> for the rest &mdash; and <span data-fact="txt.tlonly.hate">{tloh}%</span> of them show no English markers at all, against <span data-fact="txt.tlonly.nonhate">{tlon}%</span>.</li>
                        <li>That last one needs care. It may say what abuse sounds like, or it may say which language annotators were readier to call abusive. This data cannot separate the two, and the difference matters if anyone trains on it.</li>
                    </ul>
'''.format(**F)

    S = []

    def sec(n, title, desc, ct, canvas, cards, extra=""):
        c = "\n".join(
            '''                    <div class="insight-card">
                        <h4>{h}</h4>
                        <div class="insight-value"{fa}>{v}</div>
                        <p>{p}</p>
                    </div>'''.format(h=h, v=v, p=p, fa=(' data-fact="%s"' % k) if k else "")
            for h, v, k, p in cards)
        cv = ('''
                <div class="chart-container fade-up">
                    <div class="chart-title"><span>%s</span></div>
                    <div class="chart-wrapper"><canvas id="%s"></canvas></div>
                </div>
''' % (ct, canvas)) if canvas else ""
        S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">{n:02d}</div>
                    <h2>{t}</h2>
                    <p class="section-description">{d}</p>
                </div>
{cv}{ex}
                <div class="grid-3 fade-up">
{c}
                </div>
            </div>
        </section>
'''.format(n=n, t=title, d=desc, cv=cv, ex=extra, c=c))

    sec(1, "The Corpus",
        "{r:,} posts across {s} splits, each labelled hate or not. Class balance is the "
        "first thing to check on any benchmark: if one label dominates, a model that "
        "always guesses it scores well and accuracy stops meaning "
        "anything.".format(r=F["rows"], s=F["splits"]),
        "Rows by split and label", "splitChart",
        [("Total posts", "{rows:,}".format(**F), "txt.rows",
          "Across train, validation and test."),
         ("Hate-labelled", "{hate:,}".format(**F), "txt.hate",
          "{b}% of the corpus &mdash; close enough to even that accuracy is a fair "
          "measure here.".format(b=F["balance"])),
         ("Not hate", "{nonhate:,}".format(**F), "txt.nonhate",
          "The balance is deliberate and holds inside every split, not just overall.")])

    sec(2, "The Benchmark Leaks",
        "Splits exist so a model is graded on text it has never seen. That guarantee "
        "only holds if the splits are disjoint. Here they are not.",
        None, None,
        [("Posts in more than one split", "{leak}".format(**F), "txt.leak",
          "The same text is both trained on and graded on."),
         ("As a share", "{leakpct}%".format(**F), "txt.leak.pct",
          "Small, but it moves in one direction only: every published accuracy figure "
          "for this benchmark is flattered by some amount nobody has measured."),
         ("Rows beyond first occurrence", "{dupes}".format(**F), "txt.dupes",
          "Counting all repeats, not just cross-split ones. Reported rather than "
          "deduplicated here &mdash; removing it would hide the leak from anyone "
          "comparing against published scores.")])

    sec(3, "A Platform's Fingerprint",
        "Post length, in twenty-character buckets. The shape is not about how Filipinos "
        "write. It is about what the platform allowed: Twitter's limit was 140 "
        "characters until November 2017 and 280 after, and this corpus spans campaigns "
        "on both sides of that change.",
        "Posts by character length", "lengthChart",
        [("Within 140 characters", "{u140}%".format(**F), "txt.under140",
          "A hard cliff at exactly the old limit, visible in the histogram."),
         ("141&ndash;280 characters", "{b280}%".format(**F), "txt.141to280",
          "The post-2017 regime."),
         ("Longer than 280", "{o280}%".format(**F), "txt.over280",
          "Longest is {m} characters &mdash; threads and quote-tweets that the "
          "collection flattened into single rows.".format(m=F["maxc"]))])

    sec(4, "Which Language",
        "Every post is checked against two fixed lists of grammatical function words, "
        "one Tagalog and one English. A post matching both is counted as mixed. This is "
        "a blunt instrument by design, and it undercounts: it misses loanwords, "
        "misspellings and Taglish morphology entirely.",
        "Share of posts by language markers found", "mixChart",
        [("Mixed", "{mixed}%".format(**F), "txt.mixed",
          "Both lists matched. A floor on code-switching, not a measurement of it."),
         ("Tagalog markers only", "{tlonly}%".format(**F), "txt.tagalog.only",
          "Against {e}% showing English markers only.".format(e=F["enonly"])),
         ("Neither list matched", "{nomatch}%".format(**F), "txt.nomatch",
          "Short posts, hashtags, names and heavy slang. The honest residual of a "
          "word-list method, published rather than distributed away.")])

    sec(5, "The Register Difference, And Its Catch",
        "The clearest signal in the corpus, and the one most likely to be misread. "
        "Hate-labelled posts lean substantially more Tagalog than the rest.",
        "Tagalog share of matched function words, by label", "registerChart",
        [("Hate-labelled", "{tlh}%".format(**F), "txt.tl.share.hate",
          "Of matched function words. And {t}% of these posts show no English marker "
          "at all.".format(t=F["tloh"])),
         ("Not hate", "{tln}%".format(**F), "txt.tl.share.nonhate",
          "A {g}-point gap in register between the two classes.".format(g=F["tlgap"])),
         ("What it might not mean", "&mdash;", None,
          "Two readings fit equally well: abuse is more often written in Tagalog, or "
          "annotators more readily judged Tagalog posts abusive. Nothing in this data "
          "separates them &mdash; and a model trained here would learn the pattern "
          "either way, including if it is an artefact of labelling.")])

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">06</div>
                    <h2>Why There Are No Examples On This Page</h2>
                    <p class="section-description">
                        Every write-up of a hate-speech dataset quotes a few rows to
                        show the reader what it looks like. This one does not, and the
                        constraint was set before the analysis rather than after.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>These are real people</h4>
                        <p>The corpus is election-period abuse directed at named
                        candidates and named individuals. Reprinting it to illustrate a
                        chart republishes the harassment, with better formatting and a
                        wider audience.</p>
                    </div>
                    <div class="insight-card">
                        <h4>So no content words either</h4>
                        <p>A "most frequent words" table on this corpus is a slur list.
                        The only token-level output here is the frequency of grammatical
                        function words &mdash; <em>ang</em>, <em>the</em>, <em>sa</em>,
                        <em>of</em> &mdash; taken from two lists fixed in advance so they
                        could not be tuned to produce a tidier answer.</p>
                    </div>
                    <div class="insight-card">
                        <h4>The findings survived it</h4>
                        <p>The leak, the character-limit cliff and the register gap are
                        all aggregate properties. A check in
                        <code>checks.sql</code> asserts that no output CSV carries
                        anything but function words, so this cannot erode by accident
                        later.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">07</div>
                    <h2>What This Page Does Not Cover</h2>
                    <p class="section-description">
                        The version this replaced claimed six datasets, six NLP tasks and
                        an 87.2% best model accuracy, plus charts of emotion detection,
                        hashtag frequency, mention patterns, toxicity scores and posting
                        times. No model was trained and no dataset was opened.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>No model, so no accuracy</h4>
                        <p>Nothing here reports a classification score, because nothing
                        here trained a classifier. If one is ever trained, the leak in
                        section 02 has to be dealt with first or the number will be
                        wrong in a flattering direction.</p>
                    </div>
                    <div class="insight-card">
                        <h4>The other five datasets</h4>
                        <p>The Filipino fake-news and dengue-sentiment corpora exist and
                        are cited widely, but their Hugging Face entries no longer serve
                        a machine-readable conversion &mdash; the datasets-server returns
                        no info for them. One dataset opened beats six listed.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Hashtags, mentions, timestamps</h4>
                        <p>This corpus is text and a label. There are no timestamps, no
                        user handles and no engagement counts in it, so temporal and
                        network charts could not be built from it at all.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">08</div>
                    <h2>Method</h2>
                    <p class="section-description">One fetcher, eight CSVs, no key.</p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Source</h4>
                        <p>Hugging Face's datasets-server publishes parquet conversions
                        of public datasets. DuckDB reads them straight over HTTP &mdash;
                        about 2 MB for the whole corpus, so nothing is cached or
                        committed except the aggregates.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Language detection</h4>
                        <p>Two fixed function-word lists, written before looking at the
                        data. Deliberately crude: it cannot see loanwords or Taglish
                        morphology, so the mixed share is a lower bound. The
                        {n}% that matched neither list is published rather than
                        redistributed into the others.</p>
                    </div>
                    <div class="insight-card">
                        <h4>An integer-division bug</h4>
                        <p>The length histogram bucketed on
                        <code>length / 20 * 20</code>. DuckDB's <code>/</code> is float
                        division, so that returns the length unchanged and produced 591
                        buckets instead of 16 &mdash; a "histogram" with one bar per
                        distinct length. Fixed with <code>//</code>.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Leakage is measured, not fixed</h4>
                        <p>Deduplicating across splits here would produce a cleaner
                        corpus that no longer matches the published one, and would hide
                        the problem from anyone comparing against published scores. It
                        is counted and reported instead.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Balance is asserted</h4>
                        <p>A check fails if any split drifts outside 40&ndash;60% on
                        either label, because accuracy as a headline metric depends on
                        that balance holding.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Verification</h4>
                        <p>Eleven assertions in <code>checks.sql</code>, including the
                        one that matters most here: no output CSV may contain a token
                        outside the two function-word lists.</p>
                    </div>
                </div>
            </div>
        </section>
'''.format(n=F["nomatch"]))

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">09</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>The corpus holds <span data-fact="txt.rows">{rows:,}</span>
                        labelled posts and is well balanced at
                        <span data-fact="txt.hate">{hate:,}</span> hate against
                        <span data-fact="txt.nonhate">{nonhate:,}</span> not &mdash; so
                        accuracy is a meaningful metric on it, which is not true of every
                        benchmark.</li>
                        <li>It leaks. <span data-fact="txt.leak">{leak}</span> posts sit
                        in more than one split, so published accuracy figures are
                        flattered by an unmeasured amount. Reported here rather than
                        quietly deduplicated.</li>
                        <li><span data-fact="txt.under140">{u140}%</span> of posts fit
                        the pre-2017 140-character limit, against
                        <span data-fact="txt.141to280">{b280}%</span> in the 141&ndash;280
                        band. The length distribution is a fingerprint of platform policy,
                        not of writing style.</li>
                        <li>Code-switching is at least
                        <span data-fact="txt.mixed">{mixed}%</span> of posts by a
                        deliberately crude word-list test, with
                        <span data-fact="txt.nomatch">{nomatch}%</span> matching neither
                        list &mdash; a residual that a fancier method would hide rather
                        than remove.</li>
                        <li>Hate-labelled posts run
                        <span data-fact="txt.tl.gap">{tlgap}</span> points more Tagalog in
                        function-word register than the rest
                        (<span data-fact="txt.tl.share.hate">{tlh}%</span> against
                        <span data-fact="txt.tl.share.nonhate">{tln}%</span>). Whether
                        that is a fact about abuse or about annotation is not decidable
                        from this data, and a model trained on it would learn the pattern
                        either way.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**F))

    # ---------------------------------------------------------------- charts
    charts = []
    splits = sorted({r["split"] for r in sp})
    charts.append('''        // 01 split and label balance
        new Chart(document.getElementById('splitChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Not hate', data: %s, backgroundColor: '#3b82f6' },
                    { label: 'Hate', data: %s, backgroundColor: '#ef4444' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { stacked: true }, y: { stacked: true,
                          title: { display: true, text: 'Posts' } } }
            }
        });''' % (js(splits),
                  js([int([r for r in sp if r["split"] == s and r["label"] == "0"][0]["rows"])
                      for s in splits]),
                  js([int([r for r in sp if r["split"] == s and r["label"] == "1"][0]["rows"])
                      for s in splits])))

    buckets = sorted({int(float(r["char_bucket_start"])) for r in hist})
    charts.append('''        // 03 length histogram. The 140 line is drawn because the cliff there is
        //    the whole point: it is a platform limit, not a property of the
        //    language.
        new Chart(document.getElementById('lengthChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Not hate', data: %s, backgroundColor: '#3b82f6' },
                    { label: 'Hate', data: %s, backgroundColor: '#ef4444' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { stacked: true,
                               title: { display: true, text: 'Characters (20-char buckets; 300 = 300+)' } },
                          y: { stacked: true, title: { display: true, text: 'Posts' } } }
            }
        });''' % (js([str(b) for b in buckets]),
                  js([sum(int(r["rows"]) for r in hist
                          if int(float(r["char_bucket_start"])) == b and r["label"] == "0")
                      for b in buckets]),
                  js([sum(int(r["rows"]) for r in hist
                          if int(float(r["char_bucket_start"])) == b and r["label"] == "1")
                      for b in buckets])))

    charts.append('''        // 04 language markers
        new Chart(document.getElementById('mixChart'), {
            type: 'doughnut',
            data: {
                labels: %s,
                datasets: [{ data: %s,
                             backgroundColor: ['#f59e0b', '#8b5cf6', '#3b82f6', '#64748b'] }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });''' % (js([r["category"] for r in mix]),
                  js([float(r["pct_of_corpus"]) for r in mix])))

    cats = ["tagalog markers only", "mixed", "english markers only",
            "neither list matched"]
    charts.append('''        // 05 register by label
        new Chart(document.getElementById('registerChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Not hate (%% of label)', data: %s, backgroundColor: '#3b82f6' },
                    { label: 'Hate (%% of label)', data: %s, backgroundColor: '#ef4444' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { title: { display: true, text: '%% of posts with that label' } } }
            }
        });''' % (js(cats),
                  js([float([r for r in bylab if r["label"] == "0"
                             and r["category"] == c][0]["pct_of_label"]) for c in cats]),
                  js([float([r for r in bylab if r["label"] == "1"
                             and r["category"] == c][0]["pct_of_label"]) for c in cats])))

    # ---------------------------------------------------------------- splice
    src = open(PAGE).read()

    def at(marker, start=0):
        m = re.search(r"^[ \t]*" + re.escape(marker), src[start:], re.M)
        if not m:
            raise SystemExit("marker not found: %r" % marker)
        return start + m.start()

    i = at("<h1>")
    j = at('<div class="project-info">', i)
    src = src[:i] + hero + "\n" + src[j:]

    i = at('<span class="tldr-badge">')
    j = at("</div>", i + 1)
    src = src[:i] + tldr + src[j:]

    i = at('<section class="section">')
    j = src.index("<h2>Related Projects</h2>")
    j = src.rindex("<section", 0, j)
    j = src.rindex("\n", 0, j) + 1
    src = src[:i] + "\n".join(S) + src[j:]

    i = src.index("        new Chart(")
    j = src.index("    </script>", i)
    src = src[:i] + "\n\n".join(charts) + "\n" + src[j:]

    desc = ("An open Filipino hate-speech benchmark of {r:,} posts, measured: {l} posts "
            "leak across splits, {u}% fit the old 140-character limit, and hate-labelled "
            "posts run {g} points more Tagalog.").format(
                r=F["rows"], l=F["leak"], u=F["u140"], g=F["tlgap"])
    short = ("{r:,} labelled posts, {l} of them leaking across train and test.".format(
        r=F["rows"], l=F["leak"]))

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, rep, src, count=1)
        if not n:
            raise SystemExit("head patch failed (%s)" % why)

    swap(r"<title>[^<]*</title>",
         "<title>Inside a Filipino Hate-Speech Corpus | Allan Niñal - Data Analyst Portfolio</title>",
         "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % desc, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="Inside a Filipino Hate-Speech Corpus | Allan Niñal">',
         "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % short, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="Inside a Filipino Hate-Speech Corpus">',
         "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % short, "tw:desc")
    swap(r'"headline": "[^"]*"',
         '"headline": "Inside a Filipino Hate-Speech Corpus: What Opening One Dataset Shows"',
         "headline")
    swap(r'"description": "[^"]*"', '"description": %s' % json.dumps(desc), "ld desc")

    faq = {
        "What is in the Filipino hate speech dataset?":
            "{r:,} posts from the 2016 and 2022 Philippine election campaigns, each "
            "labelled hate or not hate, split into train, validation and test. It is "
            "close to evenly balanced -- {h:,} hate against {n:,} not -- which is what "
            "makes accuracy a fair headline metric on it.".format(
                r=F["rows"], h=F["hate"], n=F["nonhate"]),
        "Is the Filipino hate speech benchmark reliable?":
            "Mostly, with one caveat worth knowing: {l} posts appear in more than one "
            "split, so a model can be graded on text it was trained on. That is {p}% of "
            "the corpus and it pushes reported accuracy in one direction only. Anyone "
            "quoting a score against this benchmark should deduplicate first.".format(
                l=F["leak"], p=F["leakpct"]),
        "How much Taglish code-switching is in Philippine social media text?":
            "At least {m}% of posts in this corpus mix Tagalog and English grammatical "
            "markers, by a deliberately crude fixed-word-list test that cannot see "
            "loanwords or Taglish morphology. A further {x}% matched neither list. Treat "
            "{m}% as a floor, not a measurement.".format(m=F["mixed"], x=F["nomatch"]),
        "Are hate speech posts written in Tagalog or English?":
            "Hate-labelled posts lean Tagalog: {h}% of their matched function words are "
            "Tagalog against {n}% for the rest, and {t}% of them show no English marker "
            "at all. Whether that reflects how abuse is written or which language "
            "annotators were readier to label abusive cannot be decided from this data, "
            "and it matters because a model trained here learns the pattern "
            "regardless.".format(h=F["tlh"], n=F["tln"], t=F["tloh"]),
    }
    items = ",\n".join(
        '            {\n'
        '                "@type": "Question",\n'
        '                "name": %s,\n'
        '                "acceptedAnswer": {\n'
        '                    "@type": "Answer",\n'
        '                    "text": %s\n'
        '                }\n'
        '            }' % (json.dumps(q), json.dumps(a)) for q, a in faq.items())
    if '"mainEntity": [' in src:
        i = src.index('"mainEntity": [')
        j = src.index("\n        ]", i)
        src = src[:i] + '"mainEntity": [\n' + items + src[j:]

    open(PAGE, "w").write(src)
    print("rebuilt %s: %d sections, %d charts" % (PAGE, len(S), len(charts)))


if __name__ == "__main__":
    main()
