#!/usr/bin/env python3
"""Regenerate projects/internet-analysis.html from data/ph-internet CSVs.

    .venv/bin/python tools/pages/build_internet.py

The page this replaces claimed 85.2M users, 73.6% penetration and a 28.5 Mbps
average download speed for 2024. The World Bank puts internet use at 67.26% that
year, and Ookla's tiles put the test-weighted mean fixed download at 128 Mbps in
2024 Q1. Sixteen of its nineteen chart arrays were perfectly monotone.

Two sources, kept apart on purpose. The World Bank counts people with a
connection. Ookla measures how fast the connections that get tested are. Blending
them into one "digital quality" score would be inventing a statistic, so the page
keeps them in separate sections and says which question each answers.
"""
import csv
import json
import os
import re

D = "data/ph-internet"
PAGE = "projects/internet-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def js(x):
    return json.dumps(x)


def main():
    ann = rows("ph_internet_annual")
    asean = rows("ph_internet_asean")
    spd = rows("ph_internet_speeds")
    bands = rows("ph_internet_speed_bands")
    cov = rows("ph_internet_coverage")

    y24 = [r for r in ann if r["year"] == "2024"][0]
    y23 = [r for r in ann if r["year"] == "2023"][0]
    y00 = [r for r in ann if r["year"] == "2000"][0]
    fixed = [r for r in spd if r["type"] == "fixed"]
    mob = [r for r in spd if r["type"] == "mobile"]
    ph_a = [r for r in asean if r["country"] == "Philippines"][0]
    fb = [r for r in bands if r["type"] == "fixed"]

    F = dict(
        users=float(y24["internet_users_pct"]),
        users23=float(y23["internet_users_pct"]),
        users00=float(y00["internet_users_pct"]),
        mobile=float(y24["mobile_per_100"]),
        fixedbb=float(y24["fixed_broadband_per_100"]),
        ratio=round(float(y24["mobile_per_100"]) / float(y24["fixed_broadband_per_100"])),
        rank=sum(1 for r in asean
                 if float(r["internet_users_pct"]) >= float(ph_a["internet_users_pct"])),
        frank=sum(1 for r in asean
                  if float(r["fixed_broadband_per_100"]) >= float(ph_a["fixed_broadband_per_100"])),
        ayear=asean[0]["year"],
        fdown=float(fixed[-1]["wmean_down_mbps"]), fdown0=float(fixed[0]["wmean_down_mbps"]),
        mdown=float(mob[-1]["wmean_down_mbps"]), mdown0=float(mob[0]["wmean_down_mbps"]),
        flat=float(fixed[-1]["wmean_latency_ms"]), flat0=float(fixed[0]["wmean_latency_ms"]),
        mlat=float(mob[-1]["wmean_latency_ms"]), mlat0=float(mob[0]["wmean_latency_ms"]),
        mult=round(float(fixed[-1]["wmean_down_mbps"]) / float(fixed[0]["wmean_down_mbps"]), 1),
        mmult=round(float(mob[-1]["wmean_down_mbps"]) / float(mob[0]["wmean_down_mbps"]), 1),
        q=len(spd), tests=int(fixed[-1]["tests"]),
        latest="%s Q%s" % (fixed[-1]["year"], fixed[-1]["quarter"]),
        mtilespeak=max(int(r["tiles"]) for r in mob), mtiles=int(mob[-1]["tiles"]),
        ftiles=int(fixed[-1]["tiles"]),
    )

    hero = '''                <h1>Philippine Internet, 2000&ndash;2025</h1>
                <p class="hero-description">
                    Two questions that get answered as if they were one. How many
                    people have a connection &mdash; and how fast are the connections
                    that people test? The first comes from the World Bank, the second
                    from {q} quarters of Ookla Speedtest tiles, and this page keeps
                    them apart.
                </p>

                <div class="header-actions">
                    <a href="https://registry.opendata.aws/speedtest-global-performance/" target="_blank" class="btn btn-primary">
                        Ookla Open Data
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="net.users.pct">{users}%</div>
                        <div class="stat-label">Using the internet, 2024</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="net.mobile.vs.fixed">{ratio}&times;</div>
                        <div class="stat-label">Mobile subs per fixed line</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="net.fixed.down.latest">{fdown}</div>
                        <div class="stat-label">Mbps fixed, {latest}</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="net.asean.rank">{rank} of 6</div>
                        <div class="stat-label">ASEAN rank, internet use</div>
                    </div>
                </div>
'''.format(**F)

    tldr = '''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Speeds rose <span data-fact="net.fixed.multiple">{mult}</span>&times; in six years. Access did not keep up: the Philippines is <span data-fact="net.asean.rank">{rank}</span> of six ASEAN economies for the share of people online.</p>
                    <ul class="tldr-list">
                        <li>The country runs on mobile. <span data-fact="net.mobile.per100">{mobile}</span> mobile subscriptions per 100 people against <span data-fact="net.fixed.per100">{fixedbb}</span> fixed broadband lines &mdash; about <span data-fact="net.mobile.vs.fixed">{ratio}</span> mobile subscriptions for every fixed connection.</li>
                        <li>Test-weighted mean fixed download went from <span data-fact="net.fixed.down.2019">{fdown0}</span> Mbps in 2019 Q1 to <span data-fact="net.fixed.down.latest">{fdown}</span> Mbps in {latest}. Mobile went from <span data-fact="net.mobile.down.2019">{mdown0}</span> to <span data-fact="net.mobile.down.latest">{mdown}</span>.</li>
                        <li>Fixed latency fell from <span data-fact="net.fixed.lat.2019">{flat0}</span> ms to <span data-fact="net.fixed.lat.latest">{flat}</span> ms. Mobile latency stalled at about <span data-fact="net.mobile.lat.latest">{mlat}</span> ms and has barely moved since 2021 &mdash; the number that decides whether a call or a game feels right, on the connection most people actually use.</li>
                        <li>Reported internet use <em>falls</em> from <span data-fact="net.users.pct.2023">{users23}%</span> in 2023 to <span data-fact="net.users.pct">{users}%</span> in 2024. Nobody lost access; the survey changed. The series is not continuous across that break and this page does not draw a smooth line through it.</li>
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

    sec(1, "How Many People Are Online",
        "The World Bank's share of the population using the internet, back to 2000. "
        "The line is not continuous: the 2024 figure comes from a different survey "
        "basis than 2023 and is more than ten points lower, so the two ends of that "
        "step are not comparable.",
        "Share of the population using the internet, %",
        "penetrationChart",
        [("2024", "{users}%".format(**F), "net.users.pct",
          "On the current survey basis."),
         ("2023", "{users23}%".format(**F), "net.users.pct.2023",
          "On the previous basis. The drop between these two is a change in how the "
          "question was asked, not people going offline."),
         ("2000", "{users00}%".format(**F), "net.users.pct.2000",
          "Two people in a hundred. Whatever the exact level today, that part of the "
          "change is not in doubt.")])

    sec(2, "A Mobile Country, Not A Broadband One",
        "This is the fact that shapes everything else. Fixed broadband barely exists "
        "here by regional standards; mobile subscriptions exceed the population. That "
        "is not the same as everyone being connected &mdash; people hold multiple SIMs "
        "&mdash; but it does mean the typical connection is a phone on a cell network.",
        "Mobile subscriptions and fixed broadband lines per 100 people",
        "mobileFixedChart",
        [("Mobile per 100", "{mobile}".format(**F), "net.mobile.per100",
          "More subscriptions than people. Dual-SIM is common, so this overstates the "
          "share of people with a phone."),
         ("Fixed broadband per 100", "{fixedbb}".format(**F), "net.fixed.per100",
          "About one line for every fourteen people &mdash; and a line is usually a "
          "household, not a person."),
         ("Ratio", "{ratio}&times;".format(**F), "net.mobile.vs.fixed",
          "Mobile subscriptions per fixed broadband line. Any policy that assumes a "
          "wired connection at home is addressing a minority.")])

    sec(3, "Against The Region",
        "The six largest ASEAN economies at {y}, the most recent year every one of them "
        "has a figure. Comparing each country at its own latest year would put 2024 "
        "against 2019 and read the lag as a gap.".format(y=F["ayear"]),
        "Internet use and fixed broadband, ASEAN-6",
        "aseanChart",
        [("Rank, internet use", "{rank} of 6".format(**F), "net.asean.rank",
          "Last. Malaysia is at {t}%.".format(t=F and round(max(float(r["internet_users_pct"])
                                                                for r in asean), 1))),
         ("Rank, fixed broadband", "{frank} of 6".format(**F), "net.asean.fixed.rank",
          "Second from bottom, ahead only of Indonesia."),
         ("The gap is access, not speed", "&mdash;", None,
          "On measured speed the Philippines is competitive. On the share of people "
          "with a connection it is last of six. Those are different problems and they "
          "have different fixes.")])

    sec(4, "Speed, 2019 To Now",
        "Test-weighted mean download from Ookla's Speedtest tiles, two quarters a year. "
        "Fixed and mobile are drawn together because the gap between them is the point: "
        "they started level and did not stay that way.",
        "Test-weighted mean download speed, Mbps",
        "speedChart",
        [("Fixed, {latest}".format(**F), "{fdown} Mbps".format(**F), "net.fixed.down.latest",
          "Up from {f0} Mbps in 2019 Q1 &mdash; {m}&times;.".format(f0=F["fdown0"], m=F["mult"])),
         ("Mobile, {latest}".format(**F), "{mdown} Mbps".format(**F), "net.mobile.down.latest",
          "Up from {m0} Mbps &mdash; {m}&times;. Real improvement, and now far behind "
          "fixed.".format(m0=F["mdown0"], m=F["mmult"])),
         ("They started together", "{f0} vs {m0}".format(f0=F["fdown0"], m0=F["mdown0"]), None,
          "Mbps in 2019 Q1, fixed against mobile. The divergence since is the story of "
          "fibre reaching cities while everyone else stayed on a cell tower.")])

    sec(5, "Latency Is The Number That Stalled",
        "Download speed is what gets advertised. Latency &mdash; the delay before data "
        "starts moving &mdash; is what decides whether a video call, a game or a payment "
        "terminal feels broken. On fixed lines it improved fourfold. On mobile it has "
        "been flat since 2021.",
        "Test-weighted mean latency, milliseconds (lower is better)",
        "latencyChart",
        [("Fixed latency now", "{flat} ms".format(**F), "net.fixed.lat.latest",
          "Down from {f} ms in 2019 Q1.".format(f=F["flat0"])),
         ("Mobile latency now", "{mlat} ms".format(**F), "net.mobile.lat.latest",
          "Down from {m} ms &mdash; but essentially unchanged for four years.".format(
              m=F["mlat0"])),
         ("The gap", "{g:.1f}&times;".format(g=F["mlat"] / F["flat"]), None,
          "Mobile latency against fixed. Most people are on the slower side of that "
          "ratio, and it is the side that has stopped improving.")])

    sec(6, "North, Central, South",
        "The tiles carry no administrative labels, so grouping them by region would mean "
        "inventing one. Latitude bands are what the data actually supports: north of "
        "13&deg;N is Luzon, 10&ndash;13&deg;N the Visayas, below 10&deg;N Mindanao.",
        "Test-weighted mean fixed download by latitude band, Mbps",
        "bandChart",
        [("North (13&deg;N+)", "{v} Mbps".format(v=[r for r in fb if "north" in r["band"]][0]["wmean_down_mbps"]),
          "net.band.north",
          "Luzon, including Metro Manila. The fastest band and the most measured."),
         ("Central (10&ndash;13&deg;N)", "{v} Mbps".format(v=[r for r in fb if "central" in r["band"]][0]["wmean_down_mbps"]),
          "net.band.central", "The Visayas."),
         ("South (&lt;10&deg;N)", "{v} Mbps".format(v=[r for r in fb if "south" in r["band"]][0]["wmean_down_mbps"]),
          "net.band.south",
          "Mindanao. The spread across all three bands is smaller than the spread "
          "between fixed and mobile &mdash; what you connect with matters more than "
          "where you are.")])

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">07</div>
                    <h2>What The Speed Numbers Are Not</h2>
                    <p class="section-description">
                        Ookla's data is the best open measurement of Philippine internet
                        speed there is. It still is not a measurement of the average
                        Philippine connection, and three limits are worth stating before
                        anyone quotes a figure from this page.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>These are speeds of tests</h4>
                        <p>People run a speed test when something feels wrong, or right
                        after an upgrade. The sample is self-selected in both directions
                        and is not the population of connections.</p>
                    </div>
                    <div class="insight-card">
                        <h4>A weighted mean, not a median</h4>
                        <p>Every figure here is a test-weighted mean of tile means.
                        Ookla's own headline is a median across tests. The two are
                        different statistics and will not agree; nothing on this page is
                        called "the average speed in the Philippines".</p>
                    </div>
                    <div class="insight-card">
                        <h4>Coverage is where the testing is</h4>
                        <p>A tile exists because someone tested inside it. Mobile tiles
                        fell from <span data-fact="net.mobile.tiles.peak">{mp:,}</span>
                        at their peak to <span data-fact="net.mobile.tiles.latest">{ml:,}</span>
                        in the latest quarter while fixed tiles rose to
                        <span data-fact="net.fixed.tiles.latest">{fl:,}</span>. Fewer
                        places measured means the rising mobile line is partly a changing
                        sample, which is why it is reported and not celebrated.</p>
                    </div>
                </div>
            </div>
        </section>
'''.format(mp=F["mtilespeak"], ml=F["mtiles"], fl=F["ftiles"]))

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">08</div>
                    <h2>What This Page Does Not Cover</h2>
                    <p class="section-description">
                        The version this replaces charted internet access by region,
                        device ownership, social media platform shares, online activity
                        mix, adoption by age, e-commerce participation, telco market
                        share, 4G and 5G coverage and a digital literacy rate. None of
                        those came from an open source, and none are reproducible here.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Regional access, age, literacy</h4>
                        <p>PSA collects these in the National ICT Household Survey. Its
                        portal sits behind a managed challenge that scripts do not pass,
                        so nothing here is derived from it.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Social media, devices, online activity</h4>
                        <p>The widely-quoted figures come from DataReportal's annual
                        reports, which are PDF publications built on panel surveys rather
                        than an open dataset. Citable, not reproducible &mdash; so they
                        are not charted here.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Telco share and network coverage</h4>
                        <p>Subscriber shares come from operator financial filings and
                        coverage from GSMA, which is licensed. Neither is in this
                        repository.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">09</div>
                    <h2>Method</h2>
                    <p class="section-description">
                        Two fetchers, seven CSVs, both sources open and keyless.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>World Bank</h4>
                        <p>Four indicators from the WDI API: internet use, mobile
                        subscriptions, fixed broadband and fixed telephone. Gaps are left
                        as nulls rather than forward-filled &mdash; carrying the last known
                        value to the present asserts a measurement nobody made.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Ookla</h4>
                        <p>Quarterly Speedtest performance tiles on S3, read directly over
                        HTTP by DuckDB. Each tile is about 600 m across and carries the
                        mean speed of tests taken inside it. {q} quarters, filtered to a
                        stated bounding box carried on every row.</p>
                    </div>
                    <div class="insight-card">
                        <h4>A schema change that hid six quarters</h4>
                        <p>Ookla added <code>tile_x</code>/<code>tile_y</code> centroid
                        columns partway through the archive. Querying them fails on the
                        older files, so 2019 and 2021 Q3 first came back as
                        "unavailable" when the data was there. The fetcher now falls back
                        to parsing the polygon's first vertex, and
                        <code>checks.sql</code> asserts every year has both connection
                        types.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Why the two sources stay apart</h4>
                        <p>The World Bank counts people with a connection; Ookla measures
                        connections that were tested. Combining them into one score would
                        be inventing a statistic, so they get separate sections.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Latitude, not region</h4>
                        <p>Speedtest tiles carry no administrative boundary. Bands are
                        used because a region column would have to be made up, the same
                        reasoning the earthquake page uses.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Verification</h4>
                        <p>Fourteen assertions in <code>checks.sql</code>: bounding-box
                        containment, plausible speeds and latencies, one comparison year
                        across all six ASEAN countries, no failed quarter, and two
                        standing warnings for the 2023-24 survey break and the shrinking
                        mobile sample. Every figure above is bound to a query in
                        <code>facts.sql</code>.</p>
                    </div>
                </div>
            </div>
        </section>
'''.format(q=F["q"]))

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">10</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>Speed is not the constraint. Test-weighted mean fixed download
                        rose <span data-fact="net.fixed.multiple">{mult}</span>&times; in six
                        years, from <span data-fact="net.fixed.down.2019">{fdown0}</span> to
                        <span data-fact="net.fixed.down.latest">{fdown}</span> Mbps.</li>
                        <li>Access is. The Philippines is
                        <span data-fact="net.asean.rank">{rank}</span> of six ASEAN economies
                        for the share of people online and
                        <span data-fact="net.asean.fixed.rank">{frank}</span> of six for fixed
                        broadband lines per 100 people.</li>
                        <li>The typical connection is a phone.
                        <span data-fact="net.mobile.per100">{mobile}</span> mobile
                        subscriptions per 100 people against
                        <span data-fact="net.fixed.per100">{fixedbb}</span> fixed lines
                        &mdash; roughly <span data-fact="net.mobile.vs.fixed">{ratio}</span>
                        to one.</li>
                        <li>Mobile latency has been flat at about
                        <span data-fact="net.mobile.lat.latest">{mlat}</span> ms since 2021
                        while fixed fell to
                        <span data-fact="net.fixed.lat.latest">{flat}</span> ms. The measure
                        that decides whether a call works has stopped improving on the
                        connection most people use.</li>
                        <li>Geography matters less than connection type. The spread across
                        latitude bands runs from
                        <span data-fact="net.band.south">{bs}</span> to
                        <span data-fact="net.band.north">{bn}</span> Mbps on fixed lines
                        &mdash; narrower than the gap between fixed and mobile anywhere in
                        the country.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(mult=F["mult"], fdown0=F["fdown0"], fdown=F["fdown"], rank=F["rank"],
           frank=F["frank"], mobile=F["mobile"], fixedbb=F["fixedbb"], ratio=F["ratio"],
           mlat=F["mlat"], flat=F["flat"],
           bs=[r for r in fb if "south" in r["band"]][0]["wmean_down_mbps"],
           bn=[r for r in fb if "north" in r["band"]][0]["wmean_down_mbps"]))

    # ---------------------------------------------------------------- charts
    charts = []
    yrs = [r["year"] for r in ann]

    # The 2024 point is drawn as its own segment: the survey basis changed, so a
    # connecting line between 2023 and 2024 would assert a fall that did not
    # happen to any person.
    up = [float(r["internet_users_pct"]) if r["internet_users_pct"] else None for r in ann]
    charts.append('''        // 01 internet use. The 2023-24 break is drawn as a gap, not a slope --
        //    the survey basis changed and joining the points asserts a collapse
        //    in access that did not occur.
        new Chart(document.getElementById('penetrationChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Using the internet (%%), earlier basis', data: %s,
                      borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.15)',
                      borderWidth: 2, pointRadius: 2, fill: true, spanGaps: false },
                    { label: 'Using the internet (%%), current basis', data: %s,
                      borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.2)',
                      borderWidth: 2, pointRadius: 4, fill: true, spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { min: 0, max: 100,
                               title: { display: true, text: 'Share of population (%%)' } } }
            }
        });''' % (js(yrs),
                  js([v if r["year"] != "2024" else None for v, r in zip(up, ann)]),
                  js([v if r["year"] == "2024" else None for v, r in zip(up, ann)])))

    charts.append('''        // 02 mobile against fixed broadband
        new Chart(document.getElementById('mobileFixedChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Mobile subscriptions per 100', data: %s, borderColor: '#f59e0b',
                      backgroundColor: 'rgba(245,158,11,0.15)', borderWidth: 2,
                      pointRadius: 0, fill: true, spanGaps: false },
                    { label: 'Fixed broadband per 100', data: %s, borderColor: '#10b981',
                      backgroundColor: 'rgba(16,185,129,0.2)', borderWidth: 2,
                      pointRadius: 0, fill: true, spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { title: { display: true, text: 'Per 100 people' } } }
            }
        });''' % (js(yrs),
                  js([float(r["mobile_per_100"]) if r["mobile_per_100"] else None for r in ann]),
                  js([float(r["fixed_broadband_per_100"]) if r["fixed_broadband_per_100"]
                      else None for r in ann])))

    charts.append('''        // 03 ASEAN
        new Chart(document.getElementById('aseanChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Using the internet (%%)', data: %s, backgroundColor: '#3b82f6' },
                    { label: 'Fixed broadband per 100', data: %s, backgroundColor: '#10b981' }
                ]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });''' % (js([r["country"] for r in asean]),
                  js([float(r["internet_users_pct"]) for r in asean]),
                  js([float(r["fixed_broadband_per_100"]) if r["fixed_broadband_per_100"]
                      else None for r in asean])))

    qlab = ["%s Q%s" % (r["year"], r["quarter"]) for r in fixed]
    charts.append('''        // 04 speeds
        new Chart(document.getElementById('speedChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Fixed (Mbps)', data: %s, borderColor: '#3b82f6',
                      backgroundColor: 'rgba(59,130,246,0.15)', borderWidth: 2,
                      pointRadius: 2, fill: true },
                    { label: 'Mobile (Mbps)', data: %s, borderColor: '#f59e0b',
                      backgroundColor: 'rgba(245,158,11,0.15)', borderWidth: 2,
                      pointRadius: 2, fill: true }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { title: { display: true, text: 'Test-weighted mean Mbps' } } }
            }
        });''' % (js(qlab),
                  js([float(r["wmean_down_mbps"]) for r in fixed]),
                  js([float(r["wmean_down_mbps"]) for r in mob])))

    charts.append('''        // 05 latency. Lower is better, so the axis is not inverted but the
        //    caption says which direction is good.
        new Chart(document.getElementById('latencyChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Fixed latency (ms)', data: %s, borderColor: '#3b82f6',
                      borderWidth: 2, pointRadius: 2, fill: false },
                    { label: 'Mobile latency (ms)', data: %s, borderColor: '#ef4444',
                      backgroundColor: 'rgba(239,68,68,0.12)', borderWidth: 2,
                      pointRadius: 2, fill: true }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { title: { display: true, text: 'Milliseconds (lower is better)' } } }
            }
        });''' % (js(qlab),
                  js([float(r["wmean_latency_ms"]) for r in fixed]),
                  js([float(r["wmean_latency_ms"]) for r in mob])))

    mb = [r for r in bands if r["type"] == "mobile"]
    charts.append('''        // 06 latitude bands, both connection types
        new Chart(document.getElementById('bandChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Fixed (Mbps)', data: %s, backgroundColor: '#3b82f6' },
                    { label: 'Mobile (Mbps)', data: %s, backgroundColor: '#f59e0b' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { title: { display: true, text: 'Test-weighted mean Mbps' } } }
            }
        });''' % (js([r["band"] for r in fb]),
                  js([float(r["wmean_down_mbps"]) for r in fb]),
                  js([float(r["wmean_down_mbps"]) for r in mb])))

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

    desc = ("Philippine internet from two open sources: World Bank access figures and "
            "{q} quarters of Ookla Speedtest tiles. Speeds rose {m}x in six years; the "
            "country is still last of six ASEAN economies for the share of people "
            "online.").format(q=F["q"], m=F["mult"])
    short = ("Speeds up {m}x in six years, still last in ASEAN for the share of people "
             "online.").format(m=F["mult"])

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, rep, src, count=1)
        if not n:
            raise SystemExit("head patch failed (%s)" % why)

    swap(r"<title>[^<]*</title>",
         "<title>Philippine Internet 2000-2025 | Allan Niñal - Data Analyst Portfolio</title>",
         "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % desc, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="Philippine Internet 2000-2025 | Allan Niñal">',
         "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % short, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="Philippine Internet 2000-2025">', "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % short, "tw:desc")
    swap(r'"headline": "[^"]*"',
         '"headline": "Philippine Internet 2000-2025: Fast Connections, Few of Them"',
         "headline")
    swap(r'"description": "[^"]*"', '"description": %s' % json.dumps(desc), "ld desc")

    faq = {
        "How fast is internet in the Philippines?":
            "In {l}, Ookla's Speedtest tiles give a test-weighted mean download of {f} "
            "Mbps on fixed connections and {m} Mbps on mobile. Both are means of tile "
            "means weighted by test count, which is not the same statistic as Ookla's "
            "published median, and they measure connections people chose to test rather "
            "than a random sample.".format(l=F["latest"], f=F["fdown"], m=F["mdown"]),
        "What share of Filipinos use the internet?":
            "{u}% in 2024 on the World Bank's current survey basis, against {u23}% in "
            "2023 on the previous one. The fall between those two years is a change in "
            "measurement, not in access. Among the six largest ASEAN economies the "
            "Philippines ranks {r} on this measure.".format(
                u=F["users"], u23=F["users23"], r=F["rank"]),
        "Why does the Philippines rely on mobile internet?":
            "Fixed broadband reaches {fb} lines per 100 people while mobile "
            "subscriptions run at {mo} per 100 -- about {ra} mobile subscriptions for "
            "every fixed line. Laying fibre across an archipelago is expensive, so most "
            "connections are cellular.".format(
                fb=F["fixedbb"], mo=F["mobile"], ra=F["ratio"]),
        "Is Philippine internet getting better?":
            "On speed, clearly: fixed download rose {x}x between 2019 and {l} and fixed "
            "latency fell from {l0} ms to {l1} ms. On mobile latency, no -- it has sat "
            "near {ml} ms since 2021, and that is the measure that decides whether calls "
            "and games work, on the connection most people use.".format(
                x=F["mult"], l=F["latest"], l0=F["flat0"], l1=F["flat"], ml=F["mlat"]),
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
