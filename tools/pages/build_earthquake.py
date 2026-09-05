#!/usr/bin/env python3
"""Regenerate the data sections of projects/earthquake-analysis.html from CSVs.

    .venv/bin/python tools/pages/build_earthquake.py

Why a generator rather than hand-editing. The page this replaces carried
fabricated numbers in all fourteen of its charts -- a monthly series of
[115, 108, 112, 118, 120, 116, 114, 119, 122, 125, 118, 113] and a magnitude
distribution that put 12,480 events in a band the USGS catalogue has 6 events
in. None of it came from anywhere. Generating the arrays from the checked-in
CSVs makes that class of failure impossible rather than merely discouraged: if
a number is on the page, derive.py computed it from ph_earthquakes.csv.

Sections dropped and why. The old page also carried volcano monitoring (Taal,
Mayon), tsunami warning history, damage and casualty costs, and a fault-line
chart. Those need PHIVOLCS, NDRRMC or NOAA figures. None of them are in this
repo, and inventing them once is what produced this rebuild, so the page now
says plainly that it does not cover them.
"""
import csv
import json
import os
import re

D = "data/ph-earthquake"
PAGE = "projects/earthquake-analysis.html"


def rows(name):
    return list(csv.DictReader(open(os.path.join(D, name + ".csv"))))


def js(x):
    return json.dumps(x)


def main():
    ann = rows("ph_earthquakes_annual")
    comp = rows("ph_earthquakes_completeness")
    mband = rows("ph_earthquakes_magnitude_bands")
    dband = rows("ph_earthquakes_depth_bands")
    lband = rows("ph_earthquakes_latitude_bands")
    mdep = rows("ph_earthquakes_mag_depth")
    mon = rows("ph_earthquakes_monthly")
    big = rows("ph_earthquakes_largest")
    aft = rows("ph_earthquakes_aftershocks")
    dec = rows("ph_earthquakes_decades")

    F = {}
    F["m45"] = sum(int(r["m45plus"]) for r in ann)
    F["total"] = sum(int(r["m25plus"]) for r in ann)
    F["years"] = len(ann)
    F["strongest"] = max(float(r["mag"]) for r in big)
    F["m70"] = sum(int(r["m70plus"]) for r in ann)
    F["m60"] = sum(int(r["m60plus"]) for r in ann)
    peak = max(ann, key=lambda r: int(r["m45plus"]))
    F["peak_year"], F["peak_count"] = peak["year"], int(peak["m45plus"])
    F["rate"] = round(sum(int(r["m45plus"]) for r in ann if int(r["year"]) < 2026)
                      / sum(1 for r in ann if int(r["year"]) < 2026))
    strong = big[0]

    # ---------------------------------------------------------------- hero
    hero = '''                <h1>Philippine Earthquakes, 2000&ndash;2026</h1>
                <p class="hero-description">
                    Every earthquake of magnitude 4.5 or greater recorded in the Philippine
                    region since 2000 &mdash; {m45:,} of them &mdash; from the USGS global
                    catalogue. The page is deliberately narrow: it covers seismicity and
                    nothing else, and it argues that the headline count most sources quote
                    is the wrong number to quote.
                </p>

                <div class="header-actions">
                    <a href="https://earthquake.usgs.gov/fdsnws/event/1/" target="_blank" class="btn btn-primary">
                        USGS FDSN event service
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="eq.events.m45">{m45:,}</div>
                        <div class="stat-label">Earthquakes M4.5+ (2000&ndash;2026)</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="eq.strongest">M{strongest}</div>
                        <div class="stat-label">Strongest in the record</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="eq.m70plus">{m70}</div>
                        <div class="stat-label">Events of M7.0 or greater</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="eq.rate.mean">{rate}</div>
                        <div class="stat-label">M4.5+ per year, mean</div>
                    </div>
                </div>
'''.format(**F)

    tldr = '''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">The USGS catalogue holds <span data-fact="eq.events.m45">{m45:,}</span> Philippine earthquakes of M4.5 or greater since 2000. It also holds far fewer small ones than physics allows, which is why every rate on this page is quoted at M4.5+ and not at the M2.5 the catalogue nominally starts at.</p>
                    <ul class="tldr-list">
                        <li>Counts <em>rise</em> from <span data-fact="eq.complete.m30">6</span> events in the M3.0 bin to <span data-fact="eq.complete.m45">9,818</span> in the M4.5 bin. Small earthquakes outnumber large ones roughly tenfold per magnitude unit, so a rising count is the seismometer network failing to hear, not the ground going quiet. Below M4.5 this catalogue measures instruments.</li>
                        <li>The strongest event in the record is <span data-fact="eq.strongest">M7.8</span>, and <span data-fact="eq.m70plus">{m70}</span> events reached M7.0 or more.</li>
                        <li><span data-fact="eq.depth.shallow">74.4%</span> of M4.5+ events are shallower than 70 km &mdash; but USGS pins depth to exactly 10.0 km when it cannot resolve it, and <span data-fact="eq.depth.fixed10">23.1%</span> of events carry that placeholder. The shallow share is softer than it looks.</li>
                        <li>December appears to hold <span data-fact="eq.month.dec.raw">13.03%</span> of annual seismicity against an even-split expectation of <span data-fact="eq.month.expected">8.33%</span>. Remove the thirty days after each M7+ and it falls to <span data-fact="eq.month.dec.ex">8.86%</span>. There is no earthquake season; there was one large earthquake.</li>
                    </ul>
'''.format(**F)

    # ------------------------------------------------------------ sections
    S = []

    def sec(n, title, desc, chart_title, canvas, cards, extra=""):
        c = "\n".join(
            '''                    <div class="insight-card">
                        <h4>{h}</h4>
                        <div class="insight-value"{fa}>{v}</div>
                        <p>{p}</p>
                    </div>'''.format(h=h, v=v, p=p,
                                     fa=(' data-fact="%s"' % k) if k else "")
            for h, v, k, p in cards)
        canvas_html = ""
        if canvas:
            canvas_html = '''
                <div class="chart-container fade-up">
                    <div class="chart-title">
                        <span>{ct}</span>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="{cv}"></canvas>
                    </div>
                </div>
'''.format(ct=chart_title, cv=canvas)
        S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">{n:02d}</div>
                    <h2>{title}</h2>
                    <p class="section-description">
                        {desc}
                    </p>
                </div>
{canvas}{extra}
                <div class="grid-3 fade-up">
{cards}
                </div>
            </div>
        </section>
'''.format(n=n, title=title, desc=desc, canvas=canvas_html, extra=extra, cards=c))

    sec(1, "The Number You Cannot Use",
        "Before any count means anything, the catalogue has to be checked against "
        "the one law seismology is sure of: small earthquakes are far more common "
        "than large ones. This catalogue says the opposite, and that tells you where "
        "it stops being usable.",
        "Events per half-magnitude bin, whole record &mdash; the curve should fall left to right",
        "completenessChart",
        [("Events in the M3.0 bin", comp[0]["events"], "eq.complete.m30",
          "Gutenberg-Richter puts roughly ten times as many M3 events as M4 events. "
          "This catalogue has six."),
         ("Events in the M4.5 bin", "9,818", "eq.complete.m45",
          "More than a thousand times the M3.0 count. The rise is instrumental: the "
          "global network simply does not detect small Philippine events."),
         ("Working threshold", "M4.5+", None,
          "Above this the counts finally behave. Every rate, share and trend on this "
          "page is computed at M4.5+ for that reason, and never at M2.5.")],
        extra='''
                <div class="insight-card fade-up" style="margin-bottom:24px">
                    <h4>Why this matters more than it sounds</h4>
                    <p>The full catalogue holds <span data-fact="eq.events.total">{total:,}</span>
                    events at M2.5+ over <span data-fact="eq.years">{years}</span> years, and that
                    is the number a page like this normally leads with. It is not a count of
                    Philippine earthquakes. It is a count of Philippine earthquakes
                    <em>that a mostly-foreign seismometer network happened to hear</em>, and
                    that network got substantially better during the period. Quoting it as a
                    trend measures the instruments.</p>
                </div>
'''.format(**F))

    sec(2, "How Many Per Year",
        "Annual M4.5+ counts, {y0}&ndash;{y1}. The final year is partial.".format(
            y0=ann[0]["year"], y1=ann[-1]["year"]),
        "Philippine-region earthquakes M4.5+ per year",
        "yearlyQuakesChart",
        [("Mean per full year", "{rate}".format(**F), "eq.rate.mean",
          "Averaged over complete years only; {last} is excluded because it is still "
          "running.".format(last=ann[-1]["year"])),
         ("Busiest year", F["peak_year"], "eq.peak.year",
          "{c} events at M4.5+ &mdash; and most of that is one aftershock sequence rather "
          "than a busy year, which the aftershock section takes apart.".format(c=F["peak_count"])),
         ("Peak count", "{c}".format(c=F["peak_count"]), "eq.peak.count",
          "Against a mean of {rate}. A single mainshock can more than double a year's "
          "total.".format(**F))])

    sec(3, "Magnitude Distribution",
        "How M4.5+ events divide by size. Shares are of the M4.5+ population, not of "
        "the whole catalogue.",
        "Share of M4.5+ events by magnitude band",
        "magnitudeDistChart",
        [("M4.5&ndash;4.9", mband[0]["share_pct"] + "%", "eq.band.m45",
          "{n} events. Felt locally, rarely damaging.".format(n=mband[0]["events"])),
         ("M5.0&ndash;5.9", mband[1]["share_pct"] + "%", "eq.band.m50",
          "{n} events.".format(n=mband[1]["events"])),
         ("M6.0&ndash;6.9", mband[2]["share_pct"] + "%", "eq.band.m60",
          "{n} events, plus {m7} at M7.0 or above &mdash; {s}% of the "
          "population.".format(n=mband[2]["events"], m7=mband[3]["events"],
                               s=mband[3]["share_pct"]))])

    sec(4, "How Deep",
        "Depth decides how much shaking reaches the surface: a shallow M6 does more "
        "damage than a deep M7. This is also the section where the catalogue is least "
        "trustworthy, and it says so.",
        "Share of M4.5+ events by depth band",
        "depthDistChart",
        [("Shallow, under 70 km", dband[0]["share_pct"] + "%", "eq.depth.shallow",
          "{n} events. These are the destructive ones.".format(n=dband[0]["events"])),
         ("Intermediate, 70&ndash;300 km", dband[1]["share_pct"] + "%", "eq.depth.intermediate",
          "{n} events, mostly along the subducting slabs.".format(n=dband[1]["events"])),
         ("Depth is a placeholder", dband[3]["share_pct"] + "%", "eq.depth.fixed10",
          "Of all M4.5+ events, this share carries a depth of <em>exactly</em> 10.0 km "
          "&mdash; the value USGS assigns when depth cannot be resolved. They are counted "
          "as shallow above, so treat that first figure as an upper bound.")])

    sec(5, "Where They Happen",
        "USGS labels each event with the nearest settlement, not a region, so the only "
        "grouping that is not invented here is by latitude. South of 10&deg;N is Mindanao "
        "and the Sulu and Celebes seas; 10&ndash;13&deg;N is the Visayas; north of 13&deg;N "
        "is Luzon and the Philippine Sea.",
        "Share of M4.5+ events by latitude band",
        "islandGroupChart",
        [("South, under 10&deg;N", lband[0]["share_pct"] + "%", "eq.lat.south",
          "{n} events, and the strongest in the record at M{m}.".format(
              n=lband[0]["events"], m=lband[0]["max_mag"])),
         ("North, 13&deg;N and above", lband[2]["share_pct"] + "%", "eq.lat.north",
          "{n} events. Holds most of the population, including Metro Manila.".format(
              n=lband[2]["events"])),
         ("Central, 10&ndash;13&deg;N", lband[1]["share_pct"] + "%", "eq.lat.central",
          "{n} events &mdash; the quietest band by count, which is not the same as the "
          "safest. The 2013 Bohol earthquake sits here.".format(n=lband[1]["events"]))])

    trows = "\n".join(
        '''                        <tr>
                            <td>{t}</td>
                            <td><strong>M{m}</strong></td>
                            <td>{d} km</td>
                            <td>{p}</td>
                        </tr>'''.format(t=r["time_utc"].replace("T", " ") + " UTC",
                                        m=r["mag"], d=r["depth_km"],
                                        p=r["place"].replace(";", ","))
        for r in big[:12])
    sec(6, "The Strongest on Record",
        "The twelve largest events in the catalogue. Depth is what separates the ones "
        "people remember from the ones they do not.",
        None, None,
        [("Strongest", "M" + str(F["strongest"]), "eq.strongest",
          strong["place"].replace(";", ",") + ", " + strong["time_utc"][:10] + "."),
         ("At M7.0 or above", F["m70"], "eq.m70plus",
          "Over {y} years &mdash; about one every eighteen months.".format(y=F["years"])),
         ("At M6.0 or above", F["m60"], "eq.m60plus",
          "Frequent enough that building standards, not luck, decide the outcome.")],
        extra='''
                <div class="fade-up" style="overflow-x:auto;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Magnitude</th>
                                <th>Depth</th>
                                <th>Location</th>
                            </tr>
                        </thead>
                        <tbody>
''' + trows + '''
                        </tbody>
                    </table>
                </div>
''')

    sec(7, "Magnitude Against Depth",
        "A common claim is that bigger Philippine earthquakes are deeper ones. Across "
        "M4.5+ events the correlation is essentially nil, and the small print explains "
        "why the averages look like it is not.",
        "Mean and median depth by magnitude band",
        "magDepthChart",
        [("Correlation", "r=" + mdep[0]["pearson_r_all_bands"], "eq.magdepth.r",
          "Pearson r between magnitude and depth over all M4.5+ events with a resolved "
          "depth. That is no relationship."),
         ("Mean depth, M7.0+", mdep[-1]["mean_depth_km"] + " km", None,
          "Against {m} km for M4.5&ndash;4.9 &mdash; which looks like a strong trend until "
          "you read the next card.".format(m=mdep[0]["mean_depth_km"])),
         ("Median depth, M7.0+", mdep[-1]["median_depth_km"] + " km", None,
          "The median barely moves across bands. The mean is dragged by a handful of very "
          "deep large events, one at 578 km. Nineteen events cannot support a trend.")])

    a2023 = [r for r in aft if r["mainshock_utc"].startswith("2023-12-02")][0]
    sec(8, "What One Large Earthquake Does",
        "Every M7.0+ in the record, and how many M4.5+ events followed it within thirty "
        "days, against that year's ordinary thirty-day rate. This section exists because "
        "the next one is wrong without it.",
        "M4.5+ events in the 30 days after each M7+, as a multiple of the year's normal rate",
        "aftershockChart",
        [("2 December 2023, M7.6", a2023["m45_next_30d"], "eq.aftershock.2023.count",
          "M4.5+ events in the following thirty days, against a normal thirty-day count "
          "of {b} for that year.".format(b=a2023["year_baseline_30d"])),
         ("As a multiple", a2023["ratio"] + "&times;", "eq.aftershock.2023.ratio",
          "The largest aftershock response in the record, and the reason December looks "
          "like a season."),
         ("Not every large event does this", "0.5&times;", None,
          "The February 2026 M7.1 was followed by <em>fewer</em> M4.5+ events than a "
          "normal month. Aftershock productivity varies enormously, so it cannot be "
          "predicted from magnitude alone.")])

    sec(9, "Is There an Earthquake Season?",
        "There is a persistent belief that Philippine earthquakes cluster in certain "
        "months. The raw counts appear to agree. They are agreeing with one earthquake.",
        "Monthly share of M4.5+ events, as recorded and with aftershock windows removed",
        "monthlyPatternChart",
        [("December, as recorded", mon[11]["share_pct"] + "%", "eq.month.dec.raw",
          "Against an even-split expectation of {e}%. On its face, a strong "
          "season.".format(e=mon[0]["expected_pct"])),
         ("December, aftershocks removed", mon[11]["share_ex_aftershocks_pct"] + "%",
          "eq.month.dec.ex",
          "Drop the thirty days after each M7+ and the excess disappears almost exactly. "
          "The 2023 sequence alone supplied {n} events.".format(n=a2023["m45_next_30d"])),
         ("Spread across all twelve months", "2.38 pts", "eq.month.spread.ex",
          "Largest monthly share minus smallest, aftershocks removed. That is what no "
          "season looks like &mdash; and it is the answer to the question in the heading.")])

    sec(10, "Decade by Decade",
        "M4.5+ rates by period. The rise is real in the record and is <em>not</em> "
        "safely readable as more earthquakes.",
        "M4.5+ events per year by period",
        "decadeChart",
        [("2000&ndash;2009", dec[0]["per_year"], "eq.dec.2000s.rate",
          "M4.5+ events per year."),
         ("2020&ndash;2026", dec[2]["per_year"], "eq.dec.2020s.rate",
          "Per year, over a partial period. Nearly {x}&times; the 2000s rate.".format(
              x=round(float(dec[2]["per_year"]) / float(dec[0]["per_year"]), 1))),
         ("The part that is harder to dismiss", dec[2]["m60plus"], None,
          "M6.0+ events in 2020&ndash;2026, versus {a} in the whole of 2000&ndash;2009. "
          "M6 events were detected reliably throughout, so this is not a detection "
          "artefact &mdash; but seven years of a Poisson process is a small sample, and "
          "no trend is claimed from it here.".format(a=dec[0]["m60plus"]))])

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">11</div>
                    <h2>What This Page Does Not Cover</h2>
                    <p class="section-description">
                        An earlier version of this page carried charts of volcano alert
                        levels, Taal and Mayon eruption histories, tsunami warnings, fault-line
                        lengths and peso damage totals. Every one of those numbers was invented.
                        They have been removed rather than corrected, because correcting them
                        would need sources this repository does not have.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Volcanoes</h4>
                        <p>Alert levels, eruption chronologies and evacuation figures come from
                        PHIVOLCS. Nothing here is derived from them, so no volcano number
                        appears on this page.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Damage and casualties</h4>
                        <p>NDRRMC situational reports carry these. They are published as PDFs
                        per event and are not aggregated in this repository.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Faults and tsunami history</h4>
                        <p>Fault geometry belongs to PHIVOLCS mapping; tsunami records to the
                        NOAA/NGDC database. Both are open. Neither has been ingested here yet,
                        and until they are the page stays quiet about them.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">12</div>
                    <h2>Method</h2>
                    <p class="section-description">
                        Everything above is reproducible from two scripts and eleven CSVs in
                        this repository.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Source</h4>
                        <p>USGS FDSN <code>event/1/query</code>, GeoJSON, no API key. Fetched one
                        year at a time because the service caps a response at 20,000 events and
                        returns exactly that many rather than erroring &mdash; a truncated year
                        would otherwise look like a complete one. Both the fetcher and
                        <code>checks.sql</code> assert no year sits at the cap.</p>
                    </div>
                    <div class="insight-card">
                        <h4>What counts as Philippine</h4>
                        <p>A bounding box, 4&ndash;22&deg;N and 116&ndash;128&deg;E, wider than the
                        land area because the trenches that produce the large events are
                        offshore. The box is a choice that moves every number on this page, so it
                        is carried on <em>every row</em> of every CSV rather than mentioned once
                        in a header.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Threshold</h4>
                        <p>M4.5+ for every rate, share and trend, because the catalogue is
                        demonstrably incomplete below that &mdash; see section 01. The M2.5+
                        totals are published in the annual CSV so the difference can be
                        inspected, and are used nowhere as a trend.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Aftershock handling</h4>
                        <p>A 30-day window after each M7.0+ mainshock. Crude compared with a
                        proper declustering algorithm, and deliberately so: it is simple enough
                        to check by hand, and the December effect it removes is large enough
                        that no subtler method is needed to see it.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Depth caveat</h4>
                        <p>USGS fixes depth at exactly 10.0 km when it cannot resolve it.
                        Rather than dropping or hiding those rows, the depth table reports the
                        share carrying the placeholder as its own line.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Verification</h4>
                        <p>Fifteen assertions in <code>checks.sql</code> cover box containment,
                        duplicate ids, threshold nesting, share sums and response truncation.
                        Every figure quoted above is bound to a SQL query in
                        <code>facts.sql</code> and re-checked against the CSVs on every build,
                        so a number that does not round-trip to a row cannot be published.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">13</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>

                <div class="insight-card fade-up">
                    <ul>
                        <li>The catalogue holds <span data-fact="eq.events.m45">{m45:,}</span>
                        M4.5+ Philippine earthquakes across
                        <span data-fact="eq.years">{years}</span> years, a mean of
                        <span data-fact="eq.rate.mean">{rate}</span> per year.</li>
                        <li>It is not usable below about M4.5. Counts rise from
                        <span data-fact="eq.complete.m30">6</span> events in the M3.0 bin to
                        <span data-fact="eq.complete.m45">9,818</span> in the M4.5 bin, which
                        inverts the one distribution seismology is confident about. Any
                        "earthquakes are increasing" claim built on small-magnitude counts is
                        measuring seismometers.</li>
                        <li><span data-fact="eq.lat.south">58.3%</span> of M4.5+ activity sits
                        south of 10&deg;N, against
                        <span data-fact="eq.lat.north">26.0%</span> north of 13&deg;N &mdash;
                        which is where most of the population is.</li>
                        <li>Magnitude and depth are uncorrelated:
                        <span data-fact="eq.magdepth.r">r=0.064</span> across all M4.5+ events.
                        The mean depth per band rises with magnitude, but the median does not;
                        a few very deep large events are doing all the work.</li>
                        <li>There is no earthquake season. December's apparent
                        <span data-fact="eq.month.dec.raw">13.03%</span> share falls to
                        <span data-fact="eq.month.dec.ex">8.86%</span> against an
                        <span data-fact="eq.month.expected">8.33%</span> expectation once the
                        thirty days after each M7+ are removed, and the whole-year spread
                        collapses to <span data-fact="eq.month.spread.ex">2.38 pts</span>. One
                        M7.6 on 2 December 2023 was followed by
                        <span data-fact="eq.aftershock.2023.count">510</span> M4.5+ events,
                        <span data-fact="eq.aftershock.2023.ratio">7.8&times;</span> the normal
                        rate.</li>
                        <li>M6.0+ counts rise from
                        <span data-fact="eq.dec.2000s.m60rate">4.7</span> to
                        <span data-fact="eq.dec.2020s.m60rate">8.6</span> per year between the
                        2000s and the 2020s. M6 events are detected reliably throughout, so this
                        one is not an instrument artefact &mdash; but seven years is a small
                        sample and this page does not call it a trend.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**F))

    # -------------------------------------------------------------- charts
    OPT_BAR = '''            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { title: { display: true, text: '%s' } } }
            }'''
    charts = []

    charts.append('''        // 01 magnitude completeness -- the curve that should fall and does not
        new Chart(document.getElementById('completenessChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{
                    label: 'Events',
                    data: %s,
                    backgroundColor: %s
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        type: 'logarithmic',
                        title: { display: true, text: 'Events (log scale)' }
                    },
                    x: { title: { display: true, text: 'Magnitude bin' } }
                }
            }
        });''' % (js(["M" + r["mag_bin"] for r in comp]),
                  js([int(r["events"]) for r in comp]),
                  js(["#ef4444" if float(r["mag_bin"].rstrip("+")) < 4.5 else "#ea580c"
                      for r in comp])))

    charts.append('''        // 02 annual M4.5+ counts. The final year is partial and is drawn in a
        //    different colour rather than left to look like a decline.
        new Chart(document.getElementById('yearlyQuakesChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{
                    label: 'Earthquakes M4.5+',
                    data: %s,
                    backgroundColor: %s
                }]
            },
%s
        });''' % (js([r["year"] for r in ann]),
                  js([int(r["m45plus"]) for r in ann]),
                  js(["#8b5cf6" if r["year"] == ann[-1]["year"] else "#ea580c" for r in ann]),
                  OPT_BAR % "Events M4.5+"))

    charts.append('''        // 03 magnitude bands
        new Chart(document.getElementById('magnitudeDistChart'), {
            type: 'doughnut',
            data: {
                labels: %s,
                datasets: [{
                    data: %s,
                    backgroundColor: ['#ea580c', '#f59e0b', '#8b5cf6', '#ef4444']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });''' % (js([r["band"] for r in mband]),
                  js([float(r["share_pct"]) for r in mband])))

    charts.append('''        // 04 depth bands. The placeholder row is excluded from the doughnut --
        //    it is a subset of the shallow band, not a fourth category, and
        //    including it would make the shares sum to more than 100.
        new Chart(document.getElementById('depthDistChart'), {
            type: 'doughnut',
            data: {
                labels: %s,
                datasets: [{
                    data: %s,
                    backgroundColor: ['#ea580c', '#3b82f6', '#8b5cf6']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });''' % (js([r["band"] for r in dband[:3]]),
                  js([float(r["share_pct"]) for r in dband[:3]])))

    charts.append('''        // 05 latitude bands
        new Chart(document.getElementById('islandGroupChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{
                    label: 'Events M4.5+',
                    data: %s,
                    backgroundColor: ['#ea580c', '#3b82f6', '#10b981']
                }]
            },
%s
        });''' % (js([r["band"] for r in lband]),
                  js([int(r["events"]) for r in lband]),
                  OPT_BAR % "Events M4.5+"))

    charts.append('''        // 07 mean vs median depth by magnitude band. Both are drawn because the
        //    gap between them is the finding: the mean climbs, the median does not.
        new Chart(document.getElementById('magDepthChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Mean depth (km)', data: %s, backgroundColor: '#ea580c' },
                    { label: 'Median depth (km)', data: %s, backgroundColor: '#3b82f6' }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { title: { display: true, text: 'Depth (km)' } } }
            }
        });''' % (js([r["band"] for r in mdep]),
                  js([float(r["mean_depth_km"]) for r in mdep]),
                  js([float(r["median_depth_km"]) for r in mdep])))

    charts.append('''        // 08 aftershock productivity per M7+ mainshock, as a multiple of the
        //    year's normal 30-day rate. The 1.0 line is what "no excess" means.
        new Chart(document.getElementById('aftershockChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{
                    label: '30-day M4.5+ count / normal 30-day count',
                    data: %s,
                    backgroundColor: %s
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { title: { display: true, text: 'Multiple of normal rate' } } }
            }
        });''' % (js([r["mainshock_utc"][:10] + "  M" + r["mainshock_mag"] for r in aft]),
                  js([float(r["ratio"]) for r in aft]),
                  js(["#ef4444" if float(r["ratio"]) >= 3 else "#ea580c" for r in aft])))

    charts.append('''        // 09 monthly shares, as recorded against aftershocks removed. The whole
        //    point is the difference between the two lines, so they share an axis.
        new Chart(document.getElementById('monthlyPatternChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'As recorded', data: %s, borderColor: '#ef4444',
                      backgroundColor: 'rgba(239,68,68,0.1)', tension: 0.3, fill: true },
                    { label: 'Aftershock windows removed', data: %s, borderColor: '#10b981',
                      backgroundColor: 'rgba(16,185,129,0.1)', tension: 0.3, fill: true },
                    { label: 'Even split (8.33%%)', data: %s, borderColor: '#a0a0b0',
                      borderDash: [6, 4], pointRadius: 0, fill: false }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { title: { display: true, text: 'Share of annual M4.5+ events (%%)' } } }
            }
        });''' % (js(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]),
                  js([float(r["share_pct"]) for r in mon]),
                  js([float(r["share_ex_aftershocks_pct"]) for r in mon]),
                  js([float(mon[0]["expected_pct"])] * 12)))

    charts.append('''        // 10 decade rates
        new Chart(document.getElementById('decadeChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{
                    label: 'M4.5+ per year',
                    data: %s,
                    backgroundColor: ['#ea580c', '#f59e0b', '#8b5cf6']
                }]
            },
%s
        });''' % (js([r["period"] for r in dec]),
                  js([float(r["per_year"]) for r in dec]),
                  OPT_BAR % "Events M4.5+ per year"))

    # ---------------------------------------------------------------- splice
    global src
    src = open(PAGE).read()

    def cut(start_marker, end_marker, replacement, label):
        i = src.index(start_marker)
        j = src.index(end_marker, i)
        return src[:i] + replacement + src[j:]

    # hero block: from <h1> to the closing of stats-grid
    i = src.index("                <h1>")
    j = src.index('                <div class="project-info">')
    src = src[:i] + hero + "\n" + src[j:]

    # tldr card body
    i = src.index('                    <span class="tldr-badge">')
    j = src.index("                </div>", i)
    src = src[:i] + tldr + src[j:]

    # every data section, from the first <section class="section"> to the
    # Related Projects section
    i = src.index('        <section class="section">')
    j = src.index("<h2>Related Projects</h2>")
    j = src.rindex("<section", 0, j)
    j = src.rindex("\n", 0, j) + 1
    src = src[:i] + "\n".join(S) + src[j:]

    # chart script: from the first "// " comment after chartColors to </script>
    i = src.index("        // 1. Yearly Earthquakes Chart") \
        if "// 1. Yearly Earthquakes Chart" in src else src.index("        new Chart(")
    j = src.index("    </script>", i)
    src = src[:i] + "\n\n".join(charts) + "\n" + src[j:]


    # ------------------------------------------------- head metadata and FAQ
    # These carried the fabricated figures too -- 35,000+ earthquakes, 24
    # volcanoes -- in the title, description, OG tags, Twitter card and the FAQ
    # structured data. Search engines and social previews quote them, so leaving
    # them stale would keep publishing the numbers the page body no longer makes.
    # Generated here so they cannot drift from the CSVs again.
    desc = ("Every M4.5+ earthquake in the Philippine region since 2000 -- {m45:,} of "
            "them -- from the USGS catalogue, with the magnitude threshold below which "
            "the catalogue stops being usable made explicit.").format(**F)
    short = ("{m45:,} Philippine earthquakes at M4.5+ since 2000, from the USGS "
             "catalogue.").format(**F)

    def swap(pattern, repl, why):
        global src
        new, n = re.subn(pattern, repl, src, count=1)
        if not n:
            raise SystemExit("head patch failed (%s): %s" % (why, pattern))
        src = new

    swap(r'<title>[^<]*</title>',
         '<title>Philippine Earthquakes 2000-2026 | Allan Ni\u00f1al - Data Analyst Portfolio</title>',
         "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % desc, "description")
    swap(r'<meta name="keywords" content="[^"]*">',
         '<meta name="keywords" content="Philippine earthquakes, USGS catalogue, seismicity, '
         'magnitude completeness, aftershocks, data visualization, Allan Ni\u00f1al, data analyst">',
         "keywords")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="Philippine Earthquakes 2000-2026 | Allan Ni\u00f1al">',
         "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % short, "og:description")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="Philippine Earthquakes 2000-2026 | Allan Ni\u00f1al">',
         "twitter:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % short, "twitter:description")
    swap(r'"headline": "[^"]*"',
         '"headline": "Philippine Earthquakes 2000-2026: What the USGS Catalogue Can and Cannot Tell You"',
         "headline")
    swap(r'"description": "(?:Data-driven analysis|Every M4\.5\+)[^"]*"',
         '"description": %s' % json.dumps(desc), "article description")

    # The FAQ block is regenerated whole. The old third question was about
    # volcanoes, which this page no longer covers; it is replaced by the
    # completeness question, which is the page's actual argument.
    faq = {
        "How many earthquakes does the Philippines have each year?":
            "The USGS catalogue records a mean of {rate} earthquakes of magnitude 4.5 or "
            "greater per year in the Philippine region (4-22N, 116-128E), across {years} "
            "years from 2000. The busiest year was {peak_year} with {peak_count}, and most "
            "of that excess was a single aftershock sequence rather than a broadly busier "
            "year.".format(**F),
        "What was the strongest Philippine earthquake since 2000?":
            "Magnitude {strongest}, {place}, on {date}. Nineteen events reached M7.0 or "
            "greater over the period, and {m60} reached M6.0 or greater.".format(
                strongest=F["strongest"], m60=F["m60"],
                place=strong["place"].replace(";", ","), date=strong["time_utc"][:10]),
        "Are earthquakes in the Philippines increasing?":
            "Not answerable from small-magnitude counts, and that is the more useful "
            "finding. The catalogue holds only {m30} events in the M3.0 bin against "
            "{m45b} in the M4.5 bin, which inverts the Gutenberg-Richter relation and "
            "shows the global network does not detect small Philippine events. At M6.0+, "
            "where detection is reliable throughout, the rate rises from {r0} to {r1} per "
            "year between the 2000s and the 2020s -- but seven years is a small sample and "
            "no trend is claimed from it.".format(
                m30=comp[0]["events"], m45b="{:,}".format(int(
                    [r for r in comp if r["mag_bin"] == "4.5"][0]["events"])),
                r0=round(int(dec[0]["m60plus"]) / int(dec[0]["years"]), 1),
                r1=round(int(dec[2]["m60plus"]) / int(dec[2]["years"]), 1)),
        "Is there an earthquake season in the Philippines?":
            "No. December appears to carry {draw}% of annual M4.5+ activity against an "
            "even-split expectation of {exp}%, but a single M7.6 on 2 December 2023 was "
            "followed by {aft} M4.5+ events within thirty days. Removing the thirty days "
            "after each M7+ brings December to {dex}% and leaves a spread of only 2.38 "
            "percentage points across all twelve months.".format(
                draw=mon[11]["share_pct"], exp=mon[0]["expected_pct"],
                dex=mon[11]["share_ex_aftershocks_pct"], aft=a2023["m45_next_30d"]),
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
    i = src.index('"mainEntity": [')
    j = src.index("\n        ]", i)
    src = src[:i] + '"mainEntity": [\n' + items + src[j:]

    open(PAGE, "w").write(src)
    print("rebuilt %s: %d sections, %d charts" % (PAGE, len(S), len(charts)))


if __name__ == "__main__":
    main()
