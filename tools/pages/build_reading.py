#!/usr/bin/env python3
"""Regenerate projects/global-reading-analysis.html from data/global-wikipedia CSVs.

    .venv/bin/python tools/pages/build_reading.py

The first page on this site that is not about the Philippines. It asks what the
world reads on Wikipedia, and the answer is that the question does not have one:
over a single week the 24 countries' most-read lists share a median 2.81% of their
articles, and 60 of 91 pairs of language Wikipedias share nothing at all.

The finding that carries it is about language rather than volume. India's 140
most-read entries over the week are 100% on English Wikipedia and 0% on Hindi
Wikipedia -- and the distribution is a split rather than a spectrum: 6 countries
read English for more than four fifths of their list, 9 for less than a tenth, and
only 3 sit anywhere in between. The line does not track wealth. It tracks which
countries had English imposed as an administrative language.

Two honest limits, both load-bearing and both on the page. Per-country view counts
come back as views_ceil -- Wikimedia rounds them so per-country reading cannot
re-identify anyone -- so no country count here is a measurement. And six of the 24
countries asked for return 404 with "the country you asked for is not loaded yet":
Russia, Egypt, Vietnam, Turkey, Pakistan and Bangladesh. A quarter of the sample
cannot be measured at all, and the missing quarter is not random.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/global-wikipedia"
PAGE = "projects/global-reading-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    share = rows("gw_country_share")
    ov = rows("gw_overlap")
    lov = rows("gw_project_overlap")
    hol = rows("gw_holiday")
    avail = rows("gw_availability")
    cov = {x["property"]: x["value"] for x in rows("gw_coverage")}

    share.sort(key=lambda x: -f(x["en_wikipedia_pct"]))
    ov.sort(key=lambda x: -f(x["jaccard_pct"]))
    lov.sort(key=lambda x: -f(x["jaccard_pct"]))
    S = {x["country"]: x for x in share}
    H = {x["language"]: x for x in hol}

    def med(vals):
        vals = sorted(vals)
        n = len(vals)
        return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0

    ovj = [f(x["jaccard_pct"]) for x in ov]
    lovj = [f(x["jaccard_pct"]) for x in lov]
    smallest = min((x for x in avail if int(x["entries"]) > 0),
                   key=lambda x: int(x["entries"]))

    F = dict(
        ncountry=int(cov["countries"]), nproj=int(cov["language projects"]),
        ndays=int(cov["days"]), topn=int(cov["articles read per list"]),
        centries=len(rows("gw_country_top")),
        pentries=len(rows("gw_project_top")),
        dropns=int(cov["namespace entries dropped"]),
        dropnonwp=int(cov["non-Wikipedia entries dropped"]),
        first=min(x["date"] for x in rows("gw_country_top")),
        last=max(x["date"] for x in rows("gw_country_top")),
        missing=int(cov["countries with no data at all"]),
        answered=sum(1 for x in avail if int(x["entries"]) > 0),
        truncated=int(cov["countries with a truncated list"]),
        smallest=int(smallest["entries"]), smallestc=smallest["country"],
        entop=share[0]["country"], entoppct=f(share[0]["en_wikipedia_pct"]),
        india=f(S["India"]["en_wikipedia_pct"]),
        indiaen=int(S["India"]["entries"]),
        indiahindi=sum(1 for x in rows("gw_country_top")
                       if x["country"] == "India" and x["project"] == "hi.wikipedia"),
        ph=f(S["Philippines"]["en_wikipedia_pct"]),
        ng=f(S["Nigeria"]["en_wikipedia_pct"]),
        jp=f(S["Japan"]["en_wikipedia_pct"]),
        jpown=f(S["Japan"]["top_project_pct"]),
        fr=f(S["France"]["en_wikipedia_pct"]),
        idn=f(S["Indonesia"]["en_wikipedia_pct"]),
        over80=sum(1 for x in share if f(x["en_wikipedia_pct"]) > 80),
        under10=sum(1 for x in share if f(x["en_wikipedia_pct"]) < 10),
        between=sum(1 for x in share if 10 <= f(x["en_wikipedia_pct"]) <= 80),
        ovmed=r(med(ovj), 2), ovpairs=len(ov),
        ovzero=sum(1 for x in ovj if x == 0),
        ovmax=f(ov[0]["jaccard_pct"]), ovmaxa=ov[0]["a_country"],
        ovmaxb=ov[0]["b_country"], ovmaxshared=int(ov[0]["shared_articles"]),
        lovmed=r(med(lovj), 2), lovpairs=len(lov),
        lovzero=sum(1 for x in lovj if x == 0),
        lovmax=f(lov[0]["jaccard_pct"]), lovmaxa=lov[0]["a_language"],
        lovmaxb=lov[0]["b_language"],
        holdate=hol[0]["date"], holn=len(hol),
        holdistinct=len({x["top_article"] for x in hol}),
        holhi=H["Hindi"]["top_article"], holhiv=int(H["Hindi"]["views"]),
        holit=H["Italian"]["top_article"], holitv=int(H["Italian"]["views"]),
        holen=H["English"]["top_article"], holenv=int(H["English"]["views"]),
    )
    F["missingpct"] = r(100.0 * F["missing"] / F["ncountry"], 1)
    F["lovzeropct"] = r(100.0 * F["lovzero"] / F["lovpairs"], 1)
    F["enoverhi"] = r(F["holenv"] / F["holhiv"], 1)
    # Devanagari and Latin side by side in a card label needs the readable gloss.
    F["holhi_en"] = "Independence Day (India)"

    p = Page(PAGE)
    # This page was created by copying the typhoon page as a scaffold, so every
    # self-referential field still names that page -- including the canonical URL,
    # which would tell search engines this is a duplicate and should not be indexed.
    p.relocate(
        "typhoon-analysis",
        og_image="og-reading.png",
        keywords=["Wikipedia pageviews", "global reading", "language access",
                  "English Wikipedia", "open data", "data analysis"],
        dataset_name="Wikimedia pageviews by country and language",
        dataset_desc=("Most-read Wikipedia articles for 18 reporting countries and "
                      "14 language editions, 24-30 August 2026, from the Wikimedia "
                      "Analytics API"),
        breadcrumb="What The World Reads")
    p.hero('''                <h1>There Is No Such Thing As What The World Is Reading</h1>
                <p class="{hero_desc}">
                    One week, {answered} countries, {nproj} language editions of
                    Wikipedia. The median pair of countries shares {ovmed}% of
                    its most-read articles, {lovzero} of {lovpairs} pairs of
                    language editions share none at all, and India's entire
                    top list sits on English Wikipedia.
                </p>

                <div class="header-actions">
                    <a href="https://wikimedia.org/api/rest_v1/" target="_blank" class="btn btn-primary">
                        Wikimedia pageviews API
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="ov.median">{ovmed}%</div>
                        <div class="{label}">Median overlap between two countries' top lists</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="lov.zero">{lovzero} of {lovpairs}</div>
                        <div class="{label}">Language pairs sharing no top article at all</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="en.india">{india}%</div>
                        <div class="{label}">Of India's most-read list is English Wikipedia</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="gw.missing.countries">{missing} of {ncountry}</div>
                        <div class="{label}">Countries the API will not report at all</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Across {first} to {last} the {answered} countries that Wikimedia will report on shared a median <span data-fact="ov.median">{ovmed}%</span> of their most-read articles, and <span data-fact="ov.zero">{ovzero}</span> of <span data-fact="ov.pairs">{ovpairs}</span> country pairs shared <em>nothing</em>. Between language editions it is starker: a median of <span data-fact="lov.median">{lovmed}%</span>, with <span data-fact="lov.zero">{lovzero}</span> of <span data-fact="lov.pairs">{lovpairs}</span> pairs sharing no article at all.</p>
                    <ul class="tldr-list">
                        <li>India's <span data-fact="en.india.entries">{indiaen}</span> most-read entries over the week were <span data-fact="en.india">{india}%</span> on English Wikipedia and <span data-fact="en.india.hindi">{indiahindi}</span> on Hindi Wikipedia. Nigeria is also <span data-fact="en.nigeria">{ng}%</span>, the Philippines <span data-fact="en.philippines">{ph}%</span>.</li>
                        <li>Japan is the opposite pole at <span data-fact="en.japan">{jp}%</span> English and <span data-fact="en.japan.own">{jpown}%</span> Japanese; France reads English for <span data-fact="en.france">{fr}%</span> of its list. This is a split, not a spectrum: <span data-fact="en.over80">{over80}</span> countries are above 80%, <span data-fact="en.under10">{under10}</span> below 10%, and only <span data-fact="en.between">{between}</span> anywhere between.</li>
                        <li>On {holdate}, <span data-fact="hol.projects">{holn}</span> language editions had <span data-fact="hol.distinct">{holdistinct}</span> different most-read articles. Hindi Wikipedia's was India's Independence Day; Italian Wikipedia's was <span data-fact="hol.italian">{holit}</span>, Italy's own public holiday on the same date. Neither shows any sign of the other.</li>
                        <li>Per-country view counts are <strong>rounded by Wikimedia on purpose</strong> so that reading cannot be traced to individuals. Every country figure here is approximate by design, and a check asserts none is ever labelled exact.</li>
                        <li><span data-fact="gw.missing.countries">{missing}</span> of the <span data-fact="gw.countries">{ncountry}</span> countries asked for return no data at all &mdash; Russia, Egypt, Vietnam, Turkey, Pakistan and Bangladesh. That is <span data-fact="gw.missing.pct">{missingpct}%</span> of the sample, and it is not a random quarter.</li>
                    </ul>
'''.format(**F))

    S_ = [
        p.section(1, "A Quarter Of The World Cannot Be Measured",
                  "Before any finding, the limit that shapes all of them. The "
                  "per-country endpoint answers 404 for six of the {n} countries "
                  "asked for, with the message that the country is not loaded. "
                  "This is not a fetch failure and no amount of retrying changes "
                  "it.".format(n=F["ncountry"]),
                  [("Countries with no data", "{v} of {n}".format(v=F["missing"],
                                                                 n=F["ncountry"]),
                    "gw.missing.countries",
                    "Russia, Egypt, Vietnam, Turkey, Pakistan and Bangladesh "
                    "&mdash; <span data-fact=\"gw.missing.pct\">{p}%</span> of the "
                    "sample, and between them roughly a billion people."
                    .format(p=F["missingpct"])),
                   ("Countries reporting", "{v}".format(v=F["answered"]),
                    "gw.answered",
                    "Everything else on this page describes these, and says so "
                    "rather than saying “the world”."),
                   ("Shortest list", "{v} of {t}".format(v=F["smallest"],
                                                         t=F["topn"] * F["ndays"]),
                    "gw.smallest.list",
                    "{c} answers, but only this many articles cleared the privacy "
                    "floor across the week. A smaller audience gets a shorter list "
                    "as well as a rounder one, so the data is thinnest exactly "
                    "where it would be most interesting."
                    .format(c=F["smallestc"]))],
                  "Entries returned per country, of a possible %d"
                  % (F["topn"] * F["ndays"]), "availChart"),
        p.section(2, "The Median Pair Of Countries Shares Almost Nothing",
                  "Overlap is the share of articles two countries both had in "
                  "their top {t} on any day of the week &mdash; a Jaccard index "
                  "over sets, not a comparison of rankings, because rank order is "
                  "noisy and the question is whether the same things are being "
                  "read at all.".format(t=F["topn"]),
                  [("Median overlap", "{v}%".format(v=F["ovmed"]), "ov.median",
                    "Across all <span data-fact=\"ov.pairs\">{p}</span> pairs of "
                    "reporting countries.".format(p=F["ovpairs"])),
                   ("Pairs sharing nothing", "{v}".format(v=F["ovzero"]),
                    "ov.zero",
                    "Not one article in common across seven days. Japan shares "
                    "nothing with Italy, Poland, Thailand or Argentina."),
                   ("The most similar pair", "{v}%".format(v=F["ovmax"]),
                    "ov.max",
                    "{a} and {b}, sharing "
                    "<span data-fact=\"ov.max.shared\">{n}</span> articles. That "
                    "is the ceiling: the two countries with a shared language, "
                    "shared media and shared celebrities still disagree about "
                    "four fifths of what they read."
                    .format(a=F["ovmaxa"], b=F["ovmaxb"], n=F["ovmaxshared"]))],
                  "Overlap between country pairs, most to least similar",
                  "overlapChart"),
        p.section(3, "Between Languages It Is Worse",
                  "The same measure on the {n} language editions directly, using "
                  "their exact view counts rather than the rounded per-country "
                  "ones. If there were a global conversation this is where it "
                  "would show up.".format(n=F["nproj"]),
                  [("Median overlap", "{v}%".format(v=F["lovmed"]), "lov.median",
                    "The median pair of language Wikipedias shares no most-read "
                    "article at all."),
                   ("Pairs sharing nothing", "{a} of {b}".format(a=F["lovzero"],
                                                                 b=F["lovpairs"]),
                    "lov.zero",
                    "<span data-fact=\"lov.zero.pct\">{p}%</span> of pairs, over a "
                    "full week and a top {t} each day."
                    .format(p=F["lovzeropct"], t=F["topn"])),
                   ("The most similar pair", "{v}%".format(v=F["lovmax"]),
                    "lov.max",
                    "{a} and {b}. Even the closest two editions overlap by less "
                    "than a thirteenth."
                    .format(a=F["lovmaxa"], b=F["lovmaxb"]))],
                  "Overlap between language editions, most to least similar",
                  "langOverlapChart"),
        p.section(4, "Who Reads In English",
                  "For each country, the share of its most-read entries that sit "
                  "on English Wikipedia rather than on any other edition. The "
                  "shape of this distribution is the most interesting thing in the "
                  "dataset.",
                  [("India", "{v}%".format(v=F["india"]), "en.india",
                    "All <span data-fact=\"en.india.entries\">{e}</span> entries "
                    "across the week, and "
                    "<span data-fact=\"en.india.hindi\">{h}</span> on Hindi "
                    "Wikipedia &mdash; which exists, and has hundreds of "
                    "thousands of articles."
                    .format(e=F["indiaen"], h=F["indiahindi"])),
                   ("Japan", "{v}%".format(v=F["jp"]), "en.japan",
                    "The other end. <span data-fact=\"en.japan.own\">{o}%</span> "
                    "Japanese, and France reads English for "
                    "<span data-fact=\"en.france\">{f}%</span> of its list."
                    .format(o=F["jpown"], f=F["fr"])),
                   ("A split, not a spectrum",
                    "{a} / {b} / {c}".format(a=F["over80"], b=F["between"],
                                             c=F["under10"]),
                    "en.over80",
                    "Countries above 80% English, between 10 and 80, and below 10. "
                    "Only <span data-fact=\"en.between\">{b}</span> sit in the "
                    "middle, and Indonesia at "
                    "<span data-fact=\"en.indonesia\">{i}%</span> is the clearest "
                    "of them.".format(b=F["between"], i=F["idn"]))],
                  "Share of each country's most-read list that is English Wikipedia",
                  "englishChart"),
        p.section(5, "One Date, Two National Holidays, No Shared Awareness",
                  "{d} is Independence Day in India. It is also Ferragosto, a "
                  "public holiday in Italy. Both show up clearly &mdash; each in "
                  "exactly one language edition and nowhere else."
                  .format(d=F["holdate"]),
                  [("Hindi Wikipedia", "{v:,}".format(v=F["holhiv"]),
                    "hol.hindi.views",
                    "Views on {g}, its most-read article that day."
                    .format(g=F["holhi_en"])),
                   ("Italian Wikipedia", "{v:,}".format(v=F["holitv"]),
                    "hol.italian.views",
                    "Views on <span data-fact=\"hol.italian\">{a}</span>, Italy's "
                    "own 15 August holiday, and the top article there."
                    .format(a=F["holit"])),
                   ("English Wikipedia", "{v:,}".format(v=F["holenv"]),
                    "hol.english.views",
                    "Views on an unrelated biography &mdash; "
                    "<span data-fact=\"hol.english.over.hindi\">{r}</span> times "
                    "the Hindi article, on India's own national holiday. "
                    "<span data-fact=\"hol.projects\">{n}</span> editions produced "
                    "<span data-fact=\"hol.distinct\">{k}</span> different top "
                    "articles."
                    .format(r=F["enoverhi"], n=F["holn"], k=F["holdistinct"]))],
                  "Most-read article per language edition, %s" % F["holdate"],
                  "holidayChart"),
        p.prose(6, "What This Data Cannot Tell You",
                "Five limits. Two of them are unusual enough to be the most "
                "interesting thing about the source.",
                [("The country counts are rounded on purpose",
                  "The API field is literally <code>views_ceil</code>. Wikimedia "
                  "rounds per-country figures so that reading behaviour cannot be "
                  "traced back to individuals, which is the right decision and "
                  "makes every country number here approximate by design. A check "
                  "asserts that no country row is ever labelled exact. The "
                  "per-language counts are unrounded, which is why the two tables "
                  "are kept apart rather than merged."),
                 ("A quarter of the sample is simply absent",
                  "Russia, Egypt, Vietnam, Turkey, Pakistan and Bangladesh return "
                  "404. Any claim about global reading built on this source is "
                  "really a claim about the countries Wikimedia publishes, and the "
                  "ones it does not publish are systematically not the wealthy "
                  "English-speaking ones."),
                 ("A pageview is a request, not a read",
                  "There is no dwell time, no scroll depth and no way to tell a "
                  "person who read an article from one who bounced off it. "
                  "<code>all-access</code> also includes automated traffic that "
                  "Wikimedia could not classify; a user-only filter exists per "
                  "project but not per country, so neither table uses it, because "
                  "comparability matters more here than precision."),
                 ("Wikipedia is not the internet",
                  "It is one encyclopaedia, unusually open about its numbers. "
                  "Countries where people get reference information from a search "
                  "summary, a messaging app or a walled platform will look quieter "
                  "here than they are, and that bias also is not random."),
                 ("One week is one week",
                  "Seven days from {f} to {l}, plus {d} as a separate named case "
                  "study that is not mixed into the weekly figures. A different "
                  "week with a World Cup final or an election in it would move "
                  "every overlap number up, and the direction of that bias is "
                  "knowable while its size is not."
                  .format(f=F["first"], l=F["last"], d=F["holdate"]))]),
        p.prose(7, "Method",
                "One fetcher, nine CSVs, and more work in the filtering than in "
                "the analysis.",
                [("Namespaces come from MediaWiki, not from a pattern",
                  "Main pages, searches and category listings are navigation, not "
                  "reading, and the main page alone is usually the largest single "
                  "entry in every country &mdash; keeping it would make every "
                  "country look alike for a reason unrelated to interest. Matching "
                  "them by pattern does not work: <code>Special:Search</code> and "
                  "<code>Spider-Man: Brand New Day</code> are the same shape, and "
                  "there are 288 distinct colon-prefixes across the 98 Wikipedia "
                  "editions that appear. The namespace names are fetched from each "
                  "edition's own API instead, which is exact."),
                 ("Two bugs that filter caught only in a browser's worth of detail",
                  "A regex over letters missed the Hindi, Vietnamese and Thai "
                  "spellings of Special:Search, because Python's <code>\\w</code> "
                  "excludes the combining marks those scripts use. And the first "
                  "namespace fetch kept only namespaces numbered above zero &mdash; "
                  "but Special is namespace <strong>-1</strong>, so the one that "
                  "mattered most was excluded. Both are recorded in the fetcher "
                  "rather than quietly fixed."),
                 ("Only Wikipedia, not all of Wikimedia",
                  "The per-country endpoint spans every Wikimedia project, and its "
                  "wiktionary, wikibooks and commons entries are almost entirely "
                  "<code>Special:RecentChanges</code> traffic on tiny editions. "
                  "{n} such entries were dropped, counted in the coverage file "
                  "rather than discarded silently.".format(n=F["dropnonwp"])),
                 ("Overlap is a set measure",
                  "Jaccard over the set of articles each country or edition read "
                  "during the week, not a rank correlation. Rank order moves "
                  "around day to day for reasons that are not interesting; whether "
                  "two populations read the same things at all is the question."),
                 ("The holiday is a case study, not a data point",
                  "{d} sits in its own table and is excluded from every weekly "
                  "figure. Picking a national holiday and then reporting it inside "
                  "an average would be choosing the result first."
                  .format(d=F["holdate"])),
                 ("Licensing",
                  "The pageview datasets are released CC0. Article titles are "
                  "content and carry the editions' own CC BY-SA terms; they appear "
                  "here as data points rather than as article text.")]),
    ]

    HCLS = ("%s fade-up" % p.t["sec_head"]) if p.t["sec_head"] else "fade-up"
    CWRAP = ("%s fade-up" % p.t["card_wrap"]) if p.t["card_wrap"] else "fade-up"
    S_.append('''        <section class="{wrap}">
            <div class="container">
                <div class="{hcls}">
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="{cwrap}">
                    <ul>
                        <li>The median pair of reporting countries shares
                        <span data-fact="ov.median">{ovmed}%</span> of its most-read
                        articles, and <span data-fact="ov.zero">{ovzero}</span> of
                        <span data-fact="ov.pairs">{ovpairs}</span> pairs share
                        none.</li>
                        <li>Between language editions the median is
                        <span data-fact="lov.median">{lovmed}%</span>, with
                        <span data-fact="lov.zero">{lovzero}</span> of
                        <span data-fact="lov.pairs">{lovpairs}</span> pairs
                        &mdash; <span data-fact="lov.zero.pct">{lovzeropct}%</span>
                        &mdash; sharing no article at all.</li>
                        <li>India reads English Wikipedia for
                        <span data-fact="en.india">{india}%</span> of its top list
                        and Hindi Wikipedia for
                        <span data-fact="en.india.hindi">{indiahindi}</span> of
                        <span data-fact="en.india.entries">{indiaen}</span>
                        entries. Japan reads English for
                        <span data-fact="en.japan">{jp}%</span>.</li>
                        <li>It is a split rather than a spectrum:
                        <span data-fact="en.over80">{over80}</span> countries above
                        80% English,
                        <span data-fact="en.under10">{under10}</span> below 10%, and
                        <span data-fact="en.between">{between}</span> in
                        between.</li>
                        <li>On {holdate},
                        <span data-fact="hol.projects">{holn}</span> editions had
                        <span data-fact="hol.distinct">{holdistinct}</span>
                        different top articles &mdash; India's Independence Day in
                        Hindi, <span data-fact="hol.italian">{holit}</span> in
                        Italian, and in English a biography that outdrew the Hindi
                        article
                        <span data-fact="hol.english.over.hindi">{enoverhi}</span>
                        times over.</li>
                        <li>Per-country counts are rounded by design, and
                        <span data-fact="gw.missing.countries">{missing}</span> of
                        <span data-fact="gw.countries">{ncountry}</span> countries
                        return no data at all.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    AV = sorted(avail, key=lambda x: -int(x["entries"]))
    OVT = ov[:18]
    LOVT = lov[:16]
    ENS = share
    HOLS = sorted(hol, key=lambda x: -int(x["views"]))
    MAXENT = F["topn"] * F["ndays"]

    charts = ['''        // 01 entries returned per country. The zeroes are the finding: they are what
        //    the API will not report, not what nobody read.
        new Chart(document.getElementById('availChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Entries returned', data: %s, backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex]; } } } },
                scales: { x: { beginAtZero: true, suggestedMax: %d,
                               title: { display: true, text: 'Entries of a possible %d' } } }
            }
        });''' % (js([x["country"] for x in AV]),
                  js([int(x["entries"]) for x in AV]),
                  js(["#ef4444" if int(x["entries"]) == 0
                      else "#f59e0b" if int(x["entries"]) < MAXENT else "#3b82f6"
                      for x in AV]),
                  js([x["availability"][:70] for x in AV]), MAXENT, MAXENT),

              '''        // 02 country overlap, most similar first. Even the top pair is a fifth.
        new Chart(document.getElementById('overlapChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Shared share of top articles (%%)', data: %s,
                             backgroundColor: '#3b82f6' }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + ' shared articles'; } } } },
                scales: { x: { beginAtZero: true, max: 100,
                               title: { display: true, text: '%% of the two countries\\' combined article set' } } }
            }
        });''' % (js(["%s / %s" % (x["a_iso"], x["b_iso"]) for x in OVT]),
                  js([f(x["jaccard_pct"]) for x in OVT]),
                  js([int(x["shared_articles"]) for x in OVT])),

              '''        // 03 language-edition overlap. Same axis as the chart above on purpose: the
        //    comparison between the two is the point.
        new Chart(document.getElementById('langOverlapChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Shared share of top articles (%%)', data: %s,
                             backgroundColor: '#8b5cf6' }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + ' shared articles'; } } } },
                scales: { x: { beginAtZero: true, max: 100,
                               title: { display: true, text: '%% of the two editions\\' combined article set' } } }
            }
        });''' % (js(["%s / %s" % (x["a_language"][:9], x["b_language"][:9])
                      for x in LOVT]),
                  js([f(x["jaccard_pct"]) for x in LOVT]),
                  js([int(x["shared_articles"]) for x in LOVT])),

              '''        // 04 English share per country. The empty middle is the finding, so the bars
        //    stay in rank order rather than being grouped by region.
        new Chart(document.getElementById('englishChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'English Wikipedia share of top list (%%)',
                             data: %s, backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return 'Largest edition: ' + %s[c.dataIndex]; } } } },
                scales: { x: { beginAtZero: true, max: 100,
                               title: { display: true, text: '%% of entries on en.wikipedia' } } }
            }
        });''' % (js([x["country"] for x in ENS]),
                  js([f(x["en_wikipedia_pct"]) for x in ENS]),
                  js(["#ef4444" if f(x["en_wikipedia_pct"]) > 80
                      else "#22c55e" if f(x["en_wikipedia_pct"]) < 10 else "#f59e0b"
                      for x in ENS]),
                  js([x["top_project"] for x in ENS])),

              '''        // 05 the holiday. Log x: English is thirty times the Hindi article and a
        //    linear axis renders every other edition as nothing.
        new Chart(document.getElementById('holidayChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Views on that edition\\'s top article', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex]; } } } },
                scales: { x: { type: 'logarithmic',
                               title: { display: true, text: 'Views, %s (log scale)' } } }
            }
        });''' % (js([x["language"] for x in HOLS]),
                  js([int(x["views"]) for x in HOLS]),
                  js(["#ef4444" if x["language"] in ("Hindi", "Italian") else "#3b82f6"
                      for x in HOLS]),
                  js([x["top_article"][:52] for x in HOLS]), F["holdate"]),
              ]

    p.sections(S_)
    p.charts(charts)
    p.head(
        "There Is No Such Thing As What The World Is Reading",
        "Wikipedia pageviews for %d countries and %d language editions over one "
        "week: the median country pair shares %s%% of its most-read articles, %d of "
        "%d language pairs share none, and India's entire top list is on English "
        "Wikipedia."
        % (F["answered"], F["nproj"], F["ovmed"], F["lovzero"], F["lovpairs"]),
        "The median pair of countries shares %s%% of what it reads. India reads "
        "English Wikipedia for %s%% of its top list." % (F["ovmed"], F["india"]),
        "There Is No Such Thing As What The World Is Reading")
    p.faq({
        "What does the world read on Wikipedia?":
            "There is no single answer, and the data says so plainly. Over one week "
            "the %d countries Wikimedia reports on shared a median of just %s%% of "
            "their most-read articles, and %d of %d country pairs shared none at "
            "all. Between language editions the median overlap is %s%%, with %d of "
            "%d pairs sharing no most-read article. The most similar pair anywhere "
            "is %s and %s at %s%%."
            % (F["answered"], F["ovmed"], F["ovzero"], F["ovpairs"], F["lovmed"],
               F["lovzero"], F["lovpairs"], F["ovmaxa"], F["ovmaxb"], F["ovmax"]),
        "Do people in India read Hindi Wikipedia?":
            "Not in the most-read lists. Across %d entries over one week, %s%% of "
            "India's most-read Wikipedia articles were on English Wikipedia and %d "
            "were on Hindi Wikipedia -- which exists and has hundreds of thousands "
            "of articles. Nigeria is also at %s%% English and the Philippines at "
            "%s%%, while Japan is at %s%% and France at %s%%. The dividing line "
            "tracks which countries had English imposed as an administrative "
            "language rather than tracking wealth."
            % (F["indiaen"], F["india"], F["indiahindi"], F["ng"], F["ph"],
               F["jp"], F["fr"]),
        "Is Wikipedia pageview data accurate per country?":
            "It is deliberately approximate. The per-country endpoint returns a "
            "field called views_ceil: Wikimedia rounds these figures so that "
            "reading behaviour in a country cannot be traced back to individuals. "
            "Smaller audiences also get shorter lists, because fewer articles clear "
            "the privacy floor -- one country here returned only %d entries where "
            "others returned %d. The per-language endpoint, by contrast, returns "
            "exact counts, which is why this analysis keeps the two apart instead "
            "of merging them."
            % (F["smallest"], MAXENT),
        "Which countries are missing from Wikimedia's per-country data?":
            "Of the %d countries requested, %d returned no data at all: Russia, "
            "Egypt, Vietnam, Turkey, Pakistan and Bangladesh. The API answers 404 "
            "with the message that the country is not loaded. That is %s%% of the "
            "sample and roughly a billion people, so any claim about &ldquo;global&rdquo; "
            "reading built on this source is really a claim about the countries "
            "Wikimedia publishes."
            % (F["ncountry"], F["missing"], F["missingpct"]),
        "What happened on 15 August 2026 on Wikipedia?":
            "Two different national holidays, each visible in exactly one language. "
            "15 August is Independence Day in India, and Hindi Wikipedia's most-read "
            "article that day was Independence Day (India) with %s views. It is "
            "also Ferragosto, a public holiday in Italy, and Ferragosto was Italian "
            "Wikipedia's top article with %s views. English Wikipedia's top article "
            "was an unrelated biography with %s views -- %s times the Hindi article, "
            "on India's own national day. Across %d editions there were %d "
            "different most-read articles."
            % (format(F["holhiv"], ","), format(F["holitv"], ","),
               format(F["holenv"], ","), F["enoverhi"], F["holn"], F["holdistinct"]),
    })
    p.save(len(S_), len(charts))


if __name__ == "__main__":
    main()
