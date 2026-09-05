#!/usr/bin/env python3
"""Regenerate projects/transit-analysis.html from data/ph-transit CSVs.

    .venv/bin/python tools/pages/build_transit.py

The page this replaces claimed 12,500+ jeepney routes and 1,200+ bus routes.
OpenStreetMap has 26 and 803. Eight of its sixteen chart arrays were perfectly
monotone.

Neither the old numbers nor these are a count of Metro Manila's transport
system. The old ones were invented; these are a count of what volunteers have
mapped, which is a different and knowable thing. The page is built around that
distinction rather than around it.
"""
import csv
import json
import os
import re

D = "data/ph-transit"
PAGE = "projects/transit-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def js(x):
    return json.dumps(x)


def main():
    rt = rows("ph_transit_routes")
    st = rows("ph_transit_stops")
    city = rows("ph_transit_by_city")
    rail = rows("ph_transit_rail_routes")
    cov = {r["metric"]: int(r["value"]) for r in rows("ph_transit_coverage")}

    g = lambda t, k, v: [r for r in t if r[k] == v][0]
    csorted = sorted(city, key=lambda r: -int(r["road_stops"]))
    lines = sorted({re.sub(r":.*$", "", r["name"]) for r in rail})

    F = dict(
        routes=sum(int(r["routes"]) for r in rt),
        bus=int(g(rt, "route_type", "bus")["routes"]),
        jeep=int(g(rt, "route_type", "share_taxi")["routes"]),
        stops=cov["stop_nodes_total"],
        busstops=int(g(st, "stop_type", "bus stop")["count"]),
        named=float(g(st, "stop_type", "bus stop")["pct_named"]),
        stations=int(g(st, "stop_type", "rail station")["count"]),
        terminals=int(g(st, "stop_type", "bus terminal")["count"]),
        ncity=len(city), lines=len(lines),
        top=csorted[0]["city"], tops=int(csorted[0]["road_stops"]),
        bot=csorted[-1]["city"], bots=int(csorted[-1]["road_stops"]),
        total=sum(int(r["road_stops"]) for r in city),
        norail=sum(1 for r in city if int(r["rail_stations"]) == 0),
        qc=int(g(city, "city", "Quezon City")["rail_stations"]),
        busop=float(g(rt, "route_type", "bus")["with_operator"])
        / int(g(rt, "route_type", "bus")["routes"]) * 100,
        jeepop=float(g(rt, "route_type", "share_taxi")["with_operator"])
        / int(g(rt, "route_type", "share_taxi")["routes"]) * 100,
    )
    F["ratio"] = round(F["bus"] / F["jeep"])
    F["cityratio"] = round(F["tops"] / F["bots"])
    F["top2"] = round(100.0 * (int(csorted[0]["road_stops"])
                               + int(csorted[1]["road_stops"])) / F["total"], 1)
    F["busop"] = round(F["busop"], 1)
    F["jeepop"] = round(F["jeepop"], 1)

    hero = '''                <h1>What Metro Manila&rsquo;s Transit Map Leaves Out</h1>
                <p class="hero-description">
                    OpenStreetMap has {bus} bus routes for Metro Manila and
                    {jeep} jeepney routes. The city runs jeepneys in the thousands.
                    This page is about that gap &mdash; what a volunteer map records,
                    what it misses, and why the pattern is not random.
                </p>

                <div class="header-actions">
                    <a href="https://overpass-turbo.eu/" target="_blank" class="btn btn-primary">
                        Overpass API
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="tr.bus.routes">{bus}</div>
                        <div class="stat-label">Bus routes mapped</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="tr.jeep.routes">{jeep}</div>
                        <div class="stat-label">Jeepney routes mapped</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="tr.stops">{stops:,}</div>
                        <div class="stat-label">Stop and station nodes</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="tr.stations">{stations}</div>
                        <div class="stat-label">Rail stations</div>
                    </div>
                </div>
'''.format(**F)

    tldr = '''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Every number here counts what has been <em>mapped</em>, not what exists. That sounds like a disclaimer. It is the finding: the formal network is mapped almost completely, and the informal one that moves most people is barely mapped at all.</p>
                    <ul class="tldr-list">
                        <li><span data-fact="tr.bus.routes">{bus}</span> bus routes against <span data-fact="tr.jeep.routes">{jeep}</span> jeepney routes &mdash; a ratio of <span data-fact="tr.bus.vs.jeep">{ratio}</span> to one, in a city where jeepneys outnumber buses many times over.</li>
                        <li>The rail network, by contrast, looks complete: <span data-fact="tr.rail.lines">{lines}</span> lines and <span data-fact="tr.stations">{stations}</span> stations, all of them named.</li>
                        <li>Mapping is concentrated. <span data-fact="tr.top.city">{top}</span> and Manila hold <span data-fact="tr.top2.share">{top2}%</span> of all mapped road stops between them, and <span data-fact="tr.top.city">{top}</span> alone has <span data-fact="tr.city.ratio">{cityratio}</span> times as many as <span data-fact="tr.bottom.city">{bot}</span>.</li>
                        <li>Even the tagging splits along the same line: <span data-fact="tr.operator.pct">{busop}%</span> of bus routes record an operator against <span data-fact="tr.jeep.operator.pct">{jeepop}%</span> of jeepney routes.</li>
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

    sec(1, "What Got Mapped",
        "Route relations in OpenStreetMap inside the Metro Manila bounding box, by "
        "mode. Read this as a picture of mapping effort, not of service.",
        "Mapped route relations by mode", "routeChart",
        [("Bus routes", "{bus}".format(**F), "tr.bus.routes",
          "Nearly all named, most with an operator recorded."),
         ("Jeepney routes", "{jeep}".format(**F), "tr.jeep.routes",
          "Tagged <code>share_taxi</code>. Metro Manila runs thousands of jeepney "
          "routes; twenty-six are in the map."),
         ("Ratio", "{ratio}&times;".format(**F), "tr.bus.vs.jeep",
          "Bus routes per jeepney route in OSM. On the road the ratio runs the other "
          "way.")])

    sec(2, "The Part That Is Complete",
        "Rail is the exception, and the contrast is what makes the rest legible. Fixed "
        "infrastructure with a published timetable and a corporate owner gets mapped; a "
        "route that exists because drivers agree it does, does not.",
        "Rail stations by city", "railChart",
        [("Rail lines", "{lines}".format(**F), "tr.rail.lines",
          "Counted as distinct lines. OSM models each direction as its own relation, "
          "so the raw relation count doubles the network."),
         ("Stations", "{stations}".format(**F), "tr.stations",
          "Every one carries a name &mdash; 100% named, against {n}% of bus "
          "stops.".format(n=F["named"])),
         ("Cities with no station", "{norail} of {ncity}".format(**F), "tr.norail.cities",
          "Including Marikina, Navotas and Las Pi&ntilde;as. Rail coverage is genuinely "
          "uneven, and here the map and the world agree.")])

    sec(3, "Where The Stops Are",
        "Mapped road stops by local government unit, all {n} of them. The spread is "
        "wider than population or land area explains.".format(n=F["ncity"]),
        "Mapped road stops by city", "cityChart",
        [("{top}".format(**F), "{tops:,}".format(**F), "tr.top.city.stops",
          "The most mapped city in the metro."),
         ("{bot}".format(**F), "{bots}".format(**F), "tr.bottom.city.stops",
          "The least. A {r}-fold spread.".format(r=F["cityratio"])),
         ("Top two combined", "{top2}%".format(**F), "tr.top2.share",
          "Of all mapped road stops in the metro, in two of {n} "
          "cities.".format(n=F["ncity"]))])

    sec(4, "Even The Tags Split",
        "An operator tag says who runs the route. It is the kind of detail added by "
        "someone with access to official information, and it divides the same way "
        "everything else does.",
        "Share of routes carrying an operator tag", "tagChart",
        [("Bus routes", "{busop}%".format(**F), "tr.operator.pct",
          "Record an operator."),
         ("Jeepney routes", "{jeepop}%".format(**F), "tr.jeep.operator.pct",
          "Fewer than half. Jeepney routes are run by cooperatives and individual "
          "franchises, and that is harder to look up than a bus company."),
         ("Bus stops named", "{named}%".format(**F), "tr.busstops.named",
          "Of {b:,} mapped bus stops. Naming is the easy part; knowing who operates "
          "the service is not.".format(b=F["busstops"]))])

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">05</div>
                    <h2>A Bug Worth Showing You</h2>
                    <p class="section-description">
                        The first version of the city table credited San Juan &mdash;
                        Metro Manila's smallest city, about 6 km&sup2; &mdash; with 948
                        bus stops. That is more than Manila. It sat in a chart looking
                        entirely ordinary.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>What happened</h4>
                        <p>Each city was queried by name:
                        <code>area["name"="San Juan"]</code>. Six administrative
                        boundaries worldwide carry that name &mdash; Metro Manila, Negros
                        Oriental, Batangas, Puerto Rico, Honduras, El Salvador. Overpass
                        unioned them and returned one total. San Juan, Puerto Rico has a
                        real bus network.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Why it was invisible</h4>
                        <p>It returned a plausible number. Nothing errored, nothing was
                        empty, the totals still summed. The only tell was domain
                        knowledge: San Juan is small, and 948 stops is not.</p>
                    </div>
                    <div class="insight-card">
                        <h4>The fix</h4>
                        <p>Boundaries are now fetched once inside the metro box, matched
                        by name <em>there</em>, and each city queried by its own relation
                        id &mdash; recorded in the CSV. A name resolving to zero or more
                        than one relation is a hard error. San Juan now reads
                        <span data-fact="tr.sanjuan.stops">{sj}</span> mapped stops
                        instead of 948, and the metro's genuine floor turns out to be
                        {bot} with <span data-fact="tr.bottom.city.stops">{bots}</span>.</p>
                    </div>
                </div>
            </div>
        </section>
'''.format(sj=int(g(city, "city", "San Juan")["road_stops"]),
           bot=F["bot"], bots=F["bots"]))

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">06</div>
                    <h2>What This Page Does Not Cover</h2>
                    <p class="section-description">
                        The version this replaces charted ridership, busiest corridors,
                        stop spacing, transfer hubs, service hours, route overlap and
                        population per stop. None of those can be built from what is
                        actually available here.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Ridership and service hours</h4>
                        <p>LRTA and the MRT-3 operator publish ridership, and DOTr
                        aggregates it &mdash; in press releases and PDFs.
                        <code>dotr.gov.ph</code> returns 403 to scripts. OSM has
                        geometry, never passengers.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Corridors, transfers, overlap</h4>
                        <p>All of these need complete route geometry to mean anything.
                        With jeepney routes at 26 of several thousand, a "busiest
                        corridor" computed from this data would describe the mapping,
                        not the traffic.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Population per stop</h4>
                        <p>Needs population on the same boundaries. Doable with
                        WorldPop, and worth doing &mdash; but it would inherit the
                        coverage gap above and produce a confident number about a network
                        that is mostly missing.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">07</div>
                    <h2>Method</h2>
                    <p class="section-description">One fetcher, five CSVs, Overpass only.</p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Extent is a bounding box</h4>
                        <p>14.35&ndash;14.80&deg;N, 120.90&ndash;121.15&deg;E. The
                        <code>Metro Manila</code> admin relation does not resolve by name
                        in Overpass, so the box is the definition &mdash; and it is
                        carried on every row, because it moves every number.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Cities by relation id</h4>
                        <p>Never by name. See section 05. The seventeen NCR local
                        government units are named explicitly rather than taken from the
                        box, because the box also contains Bacoor, Antipolo and half of
                        Bulacan.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Directions are deduplicated</h4>
                        <p>OSM models each direction of a rail line as its own relation,
                        so the raw count is fourteen for
                        <span data-fact="tr.rail.lines">{lines}</span> lines. Counting
                        relations would double the network.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Queries are cached</h4>
                        <p>Overpass is a free community endpoint under real load. It
                        answered with 429s, 504s and bare connection drops during this
                        build &mdash; a dropped connection is not a
                        <code>URLError</code>, which killed one run after thirteen of
                        seventeen cities. Responses are cached so a re-run resumes rather
                        than repeating the work.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Counts are floors</h4>
                        <p>Nothing here is a count of Metro Manila's transport system.
                        Everything is a count of what has been mapped. The two are not
                        close for road-based transport, and a standing warning in
                        <code>checks.sql</code> fires while jeepney coverage stays under
                        500 routes.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Verification</h4>
                        <p>Eleven assertions in <code>checks.sql</code>, including one
                        that fails if any single city holds more than half the metro's
                        stops &mdash; the exact signature of the boundary bug in section
                        05.</p>
                    </div>
                </div>
            </div>
        </section>
'''.format(lines=F["lines"]))

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">08</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>OpenStreetMap holds
                        <span data-fact="tr.bus.routes">{bus}</span> bus routes and
                        <span data-fact="tr.jeep.routes">{jeep}</span> jeepney routes for
                        Metro Manila &mdash;
                        <span data-fact="tr.bus.vs.jeep">{ratio}</span> to one, in a city
                        where the real ratio runs the other way.</li>
                        <li>Rail is essentially complete:
                        <span data-fact="tr.rail.lines">{lines}</span> lines,
                        <span data-fact="tr.stations">{stations}</span> stations, all
                        named. Formal infrastructure with an owner and a timetable gets
                        recorded; a route that exists because drivers agree it does does
                        not.</li>
                        <li>Mapping is concentrated:
                        <span data-fact="tr.top.city">{top}</span> and Manila hold
                        <span data-fact="tr.top2.share">{top2}%</span> of all
                        <span data-fact="tr.city.total">{total:,}</span> mapped road stops
                        between them.</li>
                        <li><span data-fact="tr.norail.cities">{norail}</span> of
                        <span data-fact="tr.cities">{ncity}</span> NCR cities have no
                        mapped rail station at all &mdash; and here the map and the world
                        agree.</li>
                        <li>The formal/informal split reaches into the tags:
                        <span data-fact="tr.operator.pct">{busop}%</span> of bus routes
                        record an operator against
                        <span data-fact="tr.jeep.operator.pct">{jeepop}%</span> of jeepney
                        routes.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**F))

    # ---------------------------------------------------------------- charts
    charts = []
    charts.append('''        // 01 mapped routes by mode. Log scale: 803 against 2 renders every mode
        //    but bus as an invisible sliver otherwise.
        new Chart(document.getElementById('routeChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Mapped route relations', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { type: 'logarithmic',
                               title: { display: true, text: 'Route relations (log scale)' } } }
            }
        });''' % (js([r["route_type"] for r in rt]),
                  js([int(r["routes"]) for r in rt]),
                  js(["#ef4444" if r["route_type"] == "share_taxi" else "#3b82f6"
                      for r in rt])))

    rc = sorted(city, key=lambda r: -int(r["rail_stations"]))
    charts.append('''        // 02 rail stations by city
        new Chart(document.getElementById('railChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Rail stations', data: %s, backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { title: { display: true, text: 'Stations' } } }
            }
        });''' % (js([r["city"] for r in rc]),
                  js([int(r["rail_stations"]) for r in rc]),
                  js(["#64748b" if int(r["rail_stations"]) == 0 else "#8b5cf6"
                      for r in rc])))

    charts.append('''        // 03 mapped road stops by city
        new Chart(document.getElementById('cityChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Mapped road stops', data: %s, backgroundColor: '#3b82f6' }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'Mapped stops' } } }
            }
        });''' % (js([r["city"] for r in csorted]),
                  js([int(r["road_stops"]) for r in csorted])))

    charts.append('''        // 04 operator tagging by mode
        new Chart(document.getElementById('tagChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: '%% of routes with an operator tag', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { max: 100, title: { display: true, text: '%% tagged' } } }
            }
        });''' % (js([r["route_type"] for r in rt]),
                  js([round(100.0 * int(r["with_operator"]) / int(r["routes"]), 1)
                      for r in rt]),
                  js(["#ef4444" if r["route_type"] == "share_taxi" else "#3b82f6"
                      for r in rt])))

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

    desc = ("OpenStreetMap has {b} bus routes and {j} jeepney routes for Metro Manila. "
            "What a volunteer map records, what it misses, and why the pattern is not "
            "random.").format(b=F["bus"], j=F["jeep"])
    short = ("{b} bus routes mapped, {j} jeepney routes. The gap is the "
             "finding.").format(b=F["bus"], j=F["jeep"])

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, rep, src, count=1)
        if not n:
            raise SystemExit("head patch failed (%s)" % why)

    swap(r"<title>[^<]*</title>",
         "<title>What Metro Manila's Transit Map Leaves Out | Allan Niñal - Data Analyst Portfolio</title>",
         "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % desc, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="What Metro Manila\'s Transit Map Leaves Out | Allan Niñal">',
         "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % short, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="What Metro Manila\'s Transit Map Leaves Out">',
         "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % short, "tw:desc")
    swap(r'"headline": "[^"]*"',
         '"headline": "What Metro Manila\'s Transit Map Leaves Out"', "headline")
    swap(r'"description": "[^"]*"', '"description": %s' % json.dumps(desc), "ld desc")

    faq = {
        "How many jeepney routes are there in Metro Manila?":
            "This analysis cannot tell you, and says so. OpenStreetMap holds {j} jeepney "
            "route relations for the metro; the real network runs to several thousand. "
            "That figure is a measure of mapping coverage, not of the transport system, "
            "and the gap between it and the {b} mapped bus routes is the point of the "
            "page.".format(j=F["jeep"], b=F["bus"]),
        "How many rail stations does Metro Manila have?":
            "{s} stations across {l} lines are mapped, all of them named. Rail is the "
            "part of the network OpenStreetMap has essentially complete, which is what "
            "makes the road-based gap legible: fixed infrastructure with an owner and a "
            "timetable gets recorded, informal routes do not. {n} of the {c} NCR cities "
            "have no rail station at all.".format(
                s=F["stations"], l=F["lines"], n=F["norail"], c=F["ncity"]),
        "Which Metro Manila city has the most transit stops?":
            "{t} with {ts:,} mapped road stops, against {b} with {bs} -- a {r}-fold "
            "spread. {t} and Manila together hold {p}% of all {tot:,} mapped road stops. "
            "Again, this measures where mapping has happened as much as where service "
            "runs.".format(t=F["top"], ts=F["tops"], b=F["bot"], bs=F["bots"],
                           r=F["cityratio"], p=F["top2"], tot=F["total"]),
        "Can you use OpenStreetMap to analyse Philippine public transport?":
            "For rail, yes. For road-based transport, only with the coverage stated up "
            "front. Anything needing complete route geometry -- busiest corridors, "
            "transfer hubs, route overlap, population per stop -- would describe the "
            "mapping rather than the traffic, so this page does not compute them.",
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
