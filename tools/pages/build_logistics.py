#!/usr/bin/env python3
"""Regenerate projects/competitiveness-analysis.html from data/ph-logistics.

    .venv/bin/python tools/pages/build_logistics.py

The page was specified as a ranking of 149 Philippine cities on DTI's Cities and
Municipalities Competitiveness Index, with pillar scores, radars and
year-over-year movement. cmci.dti.gov.ph returns 403 to anything that is not a
browser and publishes no open feed, so none of that is reachable. Fifteen of its
twenty chart arrays were perfectly monotone.

Rather than approximate a ranking that cannot be fetched, the page now covers the
competitiveness measure that IS open and comparable: the World Bank's Logistics
Performance Index. It is narrower -- one country, one dimension of
competitiveness -- and it is real. Section 05 states plainly what was dropped and
why.
"""
import csv
import json
import os
import re

D = "data/ph-logistics"
PAGE = "projects/competitiveness-analysis.html"
DIMS = ["customs", "infrastructure", "international shipments",
        "logistics competence", "tracking and tracing", "timeliness"]


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def js(x):
    return json.dumps(x)


def main():
    sc = rows("ph_lpi_scores")
    rk = rows("ph_lpi_ranks")
    rounds = rows("ph_lpi_rounds")

    years = sorted({int(r["year"]) for r in sc})
    last, first = years[-1], years[0]
    countries = sorted({r["country"] for r in sc})

    def s(country, dim, year):
        m = [r for r in sc if r["country"] == country and r["dimension"] == dim
             and int(r["year"]) == year]
        return float(m[0]["score"]) if m else None

    ph_last = {d: s("Philippines", d, last) for d in DIMS}
    worst = min(ph_last, key=ph_last.get)
    best = max(ph_last, key=ph_last.get)

    F = dict(
        overall=s("Philippines", "overall", last), year=last, first=first,
        rank=int([r for r in rk if r["country"] == "Philippines"
                  and int(r["year"]) == last][0]["rank_in_asean6"]),
        n=int([r for r in rk if r["country"] == "Philippines"
               and int(r["year"]) == last][0]["countries_ranked"]),
        customs=ph_last["customs"], timeliness=ph_last["timeliness"],
        infra=ph_last["infrastructure"],
        worst=worst, best=best,
        sgp=s("Singapore", "overall", last),
        firstscore=s("Philippines", "overall", first),
        rounds=len(years), obs=len(sc),
        maxgap=max(int(r["gap_years"]) for r in rounds),
        bestrank=min(int(r["rank_in_asean6"]) for r in rk if r["country"] == "Philippines"),
        worstrank=max(int(r["rank_in_asean6"]) for r in rk if r["country"] == "Philippines"),
    )
    F["spread"] = round(max(ph_last.values()) - min(ph_last.values()), 2)
    F["leadergap"] = round(F["sgp"] - F["overall"], 2)
    F["customsgap"] = round(s("Singapore", "customs", last) - F["customs"], 2)
    F["change"] = round(F["overall"] - F["firstscore"], 2)

    hero = '''                <h1>How Well Do Goods Actually Move?</h1>
                <p class="hero-description">
                    The Philippines scores <span>{overall}</span> out of 5 on the World
                    Bank&rsquo;s Logistics Performance Index &mdash; {rank}th of
                    {n} ASEAN economies. But the gap between its own best and worst
                    dimension is wider than the gap between it and the regional leader,
                    and that is the more useful number.
                </p>

                <div class="header-actions">
                    <a href="https://lpi.worldbank.org/" target="_blank" class="btn btn-primary">
                        World Bank LPI
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="lpi.overall">{overall}</div>
                        <div class="stat-label">Overall LPI score, {year} (1&ndash;5)</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="lpi.rank">{rank} of {n}</div>
                        <div class="stat-label">Rank among ASEAN-6</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="lpi.customs">{customs}</div>
                        <div class="stat-label">Customs &mdash; the weakest link</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="lpi.spread">{spread}</div>
                        <div class="stat-label">Internal spread, best to worst</div>
                    </div>
                </div>
'''.format(**F)

    tldr = '''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">The Philippines is not uniformly behind on logistics. It is <em>lopsided</em>: goods arrive on time and then wait at the border.</p>
                    <ul class="tldr-list">
                        <li>Timeliness scores <span data-fact="lpi.timeliness">{timeliness}</span> and customs <span data-fact="lpi.customs">{customs}</span> &mdash; an internal spread of <span data-fact="lpi.spread">{spread}</span> points, wider than the <span data-fact="lpi.leader.gap">{leadergap}</span>-point gap to Singapore on the overall score.</li>
                        <li>On customs alone the gap to Singapore is <span data-fact="lpi.customs.gap">{customsgap}</span> points &mdash; the widest single-dimension gap in the comparison. One bottleneck, not a general weakness.</li>
                        <li>The overall score has risen from <span data-fact="lpi.first">{firstscore}</span> in {first} to <span data-fact="lpi.overall">{overall}</span> in {year}, a gain of <span data-fact="lpi.change">{change}</span>. The rank has moved between <span data-fact="lpi.best.rank">{bestrank}</span>th and <span data-fact="lpi.worst.rank">{worstrank}</span>th over the same period.</li>
                        <li>This is a survey of freight forwarders, not a measurement of ports. A single round&rsquo;s movement can reflect who answered as easily as what changed &mdash; the World Bank says so itself.</li>
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

    sec(1, "One Country, Six Dimensions",
        "The LPI scores six things separately, each 1 to 5. Reading only the overall "
        "score hides the shape, and here the shape is the whole story.",
        "Philippine LPI by dimension, {y}".format(y=last), "dimChart",
        [("Best: {b}".format(b=best), "{timeliness}".format(**F), "lpi.timeliness",
          "Shipments reach their destination within the expected time. This is the part "
          "that works."),
         ("Worst: {w}".format(w=worst), "{customs}".format(**F), "lpi.customs",
          "Border clearance. Every other dimension sits above it."),
         ("Spread", "{spread} pts".format(**F), "lpi.spread",
          "Best minus worst. A country that were uniformly mediocre would have a small "
          "spread; this one has a specific problem.")])

    sec(2, "Against The Region",
        "The same six dimensions for the ASEAN-6 in {y}. Note where the Philippine line "
        "tracks its neighbours and where it drops away.".format(y=last),
        "LPI by dimension, ASEAN-6", "compareChart",
        [("Overall rank", "{rank} of {n}".format(**F), "lpi.rank",
          "At {o} against Singapore's {s}.".format(o=F["overall"], s=F["sgp"])),
         ("Gap to the leader", "{leadergap} pts".format(**F), "lpi.leader.gap",
          "On the overall score &mdash; smaller than the country's own internal spread."),
         ("Gap on customs", "{customsgap} pts".format(**F), "lpi.customs.gap",
          "The widest single-dimension gap here. If one number were worth fixing, this "
          "is it.")])

    sec(3, "Seventeen Years Of Rounds",
        "The overall score across all {r} survey rounds. The rounds are irregular "
        "&mdash; two to {g} years apart, with the pandemic gap the longest &mdash; so "
        "the axis is real time rather than evenly spaced categories.".format(
            r=F["rounds"], g=F["maxgap"]),
        "Overall LPI score by round, ASEAN-6", "trendChart",
        [("{first} score".format(**F), "{firstscore}".format(**F), "lpi.first",
          "The first round the index was published."),
         ("{year} score".format(**F), "{overall}".format(**F), "lpi.overall",
          "A gain of {c} points over seventeen years.".format(c=F["change"])),
         ("Rank range", "{bestrank}th&ndash;{worstrank}th".format(**F), "lpi.best.rank",
          "Where the Philippines has sat among these six. The score improved while the "
          "rank moved little, because everyone improved.")])

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">04</div>
                    <h2>What A Survey Score Is Not</h2>
                    <p class="section-description">
                        The LPI is built from questionnaires sent to freight forwarders,
                        who rate the countries they ship to. That makes it useful and it
                        makes it fragile in specific ways.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Respondents change between rounds</h4>
                        <p>A movement of a tenth of a point can reflect a different pool
                        of forwarders answering rather than anything that happened at a
                        port. The World Bank warns against reading single-round
                        movements as trend, and this page does not.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Rank is steadier than score</h4>
                        <p>The whole scale drifts between rounds. Rank within a fixed
                        peer group absorbs some of that, which is why both are published
                        here and why the rank range is quoted alongside the score
                        gain.</p>
                    </div>
                    <div class="insight-card">
                        <h4>The overall is not an average</h4>
                        <p>It is a weighted aggregate computed by the World Bank, and it
                        does not equal the mean of the six published sub-scores. A check
                        in <code>checks.sql</code> asserts the difference persists, so
                        nobody later "simplifies" the page by recomputing it from the
                        parts.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">05</div>
                    <h2>The Page This Was Supposed To Be</h2>
                    <p class="section-description">
                        This project was specified as a ranking of 149 Philippine cities
                        on DTI&rsquo;s Cities and Municipalities Competitiveness Index,
                        with five pillar scores, radar comparisons and year-over-year
                        movement. That page could not be built.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>CMCI is closed to scripts</h4>
                        <p><code>cmci.dti.gov.ph</code> returns HTTP 403 to anything that
                        is not a browser, and DTI publishes no open feed or bulk
                        download of the index. The rankings exist; they are just not
                        fetchable.</p>
                    </div>
                    <div class="insight-card">
                        <h4>So the subject changed</h4>
                        <p>Rather than approximate 149 city scores from nothing &mdash;
                        which is exactly what the previous version of this page did
                        &mdash; the page now covers a narrower question that can be
                        answered: how well goods move through the country as a
                        whole.</p>
                    </div>
                    <div class="insight-card">
                        <h4>What that costs</h4>
                        <p>Everything sub-national. No city rankings, no pillar radars,
                        no income-class comparison, no population-versus-score
                        scatter. Those need CMCI, and CMCI needs a browser and a person.
                        Stated here so the absence is a decision rather than an
                        oversight.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">06</div>
                    <h2>Method</h2>
                    <p class="section-description">One fetcher, three CSVs, {o} observations.</p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Source</h4>
                        <p>World Bank LPI via the WDI API, keyless. Six dimensions plus
                        the overall score, for six ASEAN economies, across {r} survey
                        rounds from {f} &mdash; {o} observations in total.</p>
                    </div>
                    <div class="insight-card">
                        <h4>The scale rides on every row</h4>
                        <p>LPI is a 1&ndash;5 survey scale. Read as a rank, a percentage
                        or an index out of 100 it is wrong by a factor, so the scale is
                        carried in the CSV rather than assumed.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Completeness is asserted</h4>
                        <p>A check cross-joins every country, dimension and round and
                        fails on any missing cell &mdash; a gap would silently drop a
                        country from a chart or shift a rank.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Ranks are derived and cross-checked</h4>
                        <p>Rank is computed from the scores, then a second check asserts
                        rank order agrees with score order. Two derivations of the same
                        fact catch a flipped sort or an inconsistent tie-break.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Irregular rounds, real axis</h4>
                        <p>2007, 2010, 2012, 2014, 2016, 2018, {y}. Gaps run from two to
                        {g} years. The trend chart uses a linear time axis; evenly spaced
                        categories would imply a regularity the survey does not have.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Verification</h4>
                        <p>Eight assertions in <code>checks.sql</code>, plus every figure
                        on this page bound to a query in <code>facts.sql</code> and
                        re-checked on each build.</p>
                    </div>
                </div>
            </div>
        </section>
'''.format(o=F["obs"], r=F["rounds"], f=F["first"], y=F["year"], g=F["maxgap"]))

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">07</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>The Philippines scores
                        <span data-fact="lpi.overall">{overall}</span> of 5 overall,
                        <span data-fact="lpi.rank">{rank}</span>th of
                        <span data-fact="lpi.countries">{n}</span> ASEAN economies.</li>
                        <li>The weakness is specific, not general. Customs at
                        <span data-fact="lpi.customs">{customs}</span> against timeliness
                        at <span data-fact="lpi.timeliness">{timeliness}</span> is an
                        internal spread of
                        <span data-fact="lpi.spread">{spread}</span> points &mdash; wider
                        than the <span data-fact="lpi.leader.gap">{leadergap}</span>-point
                        overall gap to Singapore.</li>
                        <li>On customs alone that gap is
                        <span data-fact="lpi.customs.gap">{customsgap}</span> points, the
                        widest single-dimension gap in this comparison. Goods arrive on
                        time and then wait at the border.</li>
                        <li>The score has improved by
                        <span data-fact="lpi.change">{change}</span> points since
                        {first}, while the rank has moved only between
                        <span data-fact="lpi.best.rank">{bestrank}</span>th and
                        <span data-fact="lpi.worst.rank">{worstrank}</span>th &mdash;
                        improvement that the neighbours matched.</li>
                        <li>The city-level competitiveness ranking this page was meant to
                        carry is not here. DTI's CMCI returns 403 to scripts, and
                        inventing 149 city scores is what the previous version did.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**F))

    # ---------------------------------------------------------------- charts
    charts = []
    charts.append('''        // 01 Philippine dimensions, latest round, sorted worst to best so the
        //    bottleneck reads first
        new Chart(document.getElementById('dimChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Score (1-5)', data: %s, backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { min: 1, max: 5,
                               title: { display: true, text: 'LPI score (1-5)' } } }
            }
        });''' % (js(sorted(DIMS, key=lambda d: ph_last[d])),
                  js([ph_last[d] for d in sorted(DIMS, key=lambda d: ph_last[d])]),
                  js(["#ef4444" if d == worst else "#3b82f6"
                      for d in sorted(DIMS, key=lambda d: ph_last[d])])))

    palette = {"Philippines": "#ef4444", "Singapore": "#22c55e",
               "Malaysia": "#8b5cf6", "Thailand": "#f59e0b",
               "Vietnam": "#3b82f6", "Indonesia": "#64748b"}
    ds = ", ".join(
        '{ label: %s, data: %s, borderColor: %s, backgroundColor: %s, '
        'borderWidth: %d, pointRadius: 3 }'
        % (js(c), js([s(c, d, last) for d in DIMS]), js(palette[c]),
           js("rgba(239,68,68,0.15)" if c == "Philippines" else "transparent"),
           3 if c == "Philippines" else 1)
        for c in sorted(countries, key=lambda c: -(s(c, "overall", last) or 0)))
    charts.append('''        // 02 radar across dimensions. The Philippines is drawn heavier and
        //    filled; the rest are outlines, so the shape comparison is readable
        //    rather than a tangle of six filled polygons.
        new Chart(document.getElementById('compareChart'), {
            type: 'radar',
            data: { labels: %s, datasets: [%s] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { r: { min: 1.5, max: 4.5, ticks: { stepSize: 0.5 } } }
            }
        });''' % (js(DIMS), ds))

    tds = ", ".join(
        '{ label: %s, data: %s, borderColor: %s, backgroundColor: "transparent", '
        'borderWidth: %d, pointRadius: 3, tension: 0.2 }'
        % (js(c), js([{"x": y, "y": s(c, "overall", y)} for y in years]),
           js(palette[c]), 3 if c == "Philippines" else 1)
        for c in sorted(countries, key=lambda c: -(s(c, "overall", last) or 0)))
    charts.append('''        // 03 overall score by round. A LINEAR x axis, not categories: rounds sit
        //    2 to 4 years apart and even spacing would invent a regular series.
        new Chart(document.getElementById('trendChart'), {
            type: 'line',
            data: { datasets: [%s] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: {
                    x: { type: 'linear', title: { display: true, text: 'Survey round' },
                         ticks: { stepSize: 1, callback: function (v) { return v; } } },
                    y: { min: 2, max: 4.5, title: { display: true, text: 'Overall LPI (1-5)' } }
                }
            }
        });''' % tds)

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

    desc = ("Philippine logistics competitiveness on the World Bank LPI: {o} of 5, "
            "{r}th of {n} in ASEAN, with customs at {c} the clear bottleneck.").format(
                o=F["overall"], r=F["rank"], n=F["n"], c=F["customs"])
    short = ("Goods arrive on time and then wait at the border: customs {c} against "
             "timeliness {t}.").format(c=F["customs"], t=F["timeliness"])

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, rep, src, count=1)
        if not n:
            raise SystemExit("head patch failed (%s)" % why)

    swap(r"<title>[^<]*</title>",
         "<title>How Well Do Goods Actually Move? | Allan Niñal - Data Analyst Portfolio</title>",
         "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % desc, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="How Well Do Goods Actually Move? | Allan Niñal">',
         "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % short, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="How Well Do Goods Actually Move?">',
         "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % short, "tw:desc")
    swap(r'"headline": "[^"]*"',
         '"headline": "Philippine Logistics: Goods Arrive On Time, Then Wait At The Border"',
         "headline")
    swap(r'"description": "[^"]*"', '"description": %s' % json.dumps(desc), "ld desc")

    faq = {
        "How does the Philippines rank on logistics performance?":
            "{o} out of 5 on the World Bank's Logistics Performance Index in {y}, "
            "{r}th of {n} ASEAN economies. Singapore leads the group at {s}. The LPI is "
            "a survey of freight forwarders rather than a measurement of ports, so "
            "single-round movements should not be read as trend.".format(
                o=F["overall"], y=F["year"], r=F["rank"], n=F["n"], s=F["sgp"]),
        "What is the biggest weakness in Philippine logistics?":
            "Customs, at {c} out of 5 -- the lowest of the six dimensions and {g} points "
            "behind Singapore, the widest single-dimension gap in the comparison. "
            "Timeliness by contrast scores {t}. Goods reach the country on schedule and "
            "then wait at the border.".format(
                c=F["customs"], g=F["customsgap"], t=F["timeliness"]),
        "Has Philippine logistics performance improved?":
            "The overall score rose from {f} in {fy} to {o} in {y}, a gain of {ch} "
            "points. The rank among these six ASEAN economies moved only between {b}th "
            "and {w}th over the same period, because the neighbours improved too.".format(
                f=F["firstscore"], fy=F["first"], o=F["overall"], y=F["year"],
                ch=F["change"], b=F["bestrank"], w=F["worstrank"]),
        "Where can I find Philippine city competitiveness rankings?":
            "DTI's Cities and Municipalities Competitiveness Index at cmci.dti.gov.ph, "
            "which covers 149 cities and over a thousand municipalities. It is not "
            "analysed here: the site returns HTTP 403 to anything that is not a browser "
            "and DTI publishes no open feed or bulk download, so the rankings cannot be "
            "fetched or verified programmatically.",
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
