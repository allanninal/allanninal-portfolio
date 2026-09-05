#!/usr/bin/env python3
"""Regenerate projects/philippine-names-analysis.html from data/ph-names CSVs.

    .venv/bin/python tools/pages/build_names.py

The published page had five figures: Mary, 2.23M, 1:48, and "R & A" for the
commonest initials. The first three check out exactly. The fourth is half right
-- by number of bearers R is first and A is fourth, behind M and J.

The dataset is one table of a thousand forenames with no time dimension, no
regions and no stated collection date, so it cannot answer most questions about
Philippine names. The page is built around the three it can.

Concentration. The thousand names cover 74,581,757 people; the top hundred of
them account for 38.57% of that, and Mary alone for 2.1% of the whole country.

An accident of the file's own design. Incidence counts bearers and frequency says
one in N people, so their product recovers the population the data was compiled
against -- and it must be the same number in every row. It is, from 105,713,344
to 106,995,936 across all thousand names, a spread of 1.21% that is just the
denominator being rounded to a whole number. Two columns agreeing that closely is
worth more than either alone, and the median of 106,009,905 dates an undated
file to roughly 2019-2020. That is an inference, and the page labels it one.

Gender. 520 names are recorded female and 480 male, but the male names cover more
people, so a male name carries 1.18 times as many bearers on average. That is a
statement about how varied women's names are, not about how many women there are.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-names"
PAGE = "projects/philippine-names-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    top = sorted(rows("ph_names_top"), key=lambda x: int(x["rank"]))
    ini = rows("ph_names_initials")
    gen = rows("ph_names_gender")
    amb = rows("ph_names_ambiguous")
    con = rows("ph_names_concentration")
    cov = {x["property"]: x["value"] for x in rows("ph_names_coverage")}

    G = {x["gender"]: x for x in gen}
    fem, mal = G["Female"], G["Male"]
    a_rank = 1 + sum(1 for x in ini
                     if int(x["people"]) > int(
                         [y for y in ini if y["initial"] == "A"][0]["people"]))
    first_male = next(x for x in top if x["gender"] == "Male")

    def c(n):
        return [x for x in con if int(x["top_n_names"]) == n][0]

    F = dict(
        n=int(cov["names in the file"]),
        people=int(cov["people covered"]),
        base=int(cov["implied population base"]),
        lo=int(cov["implied base, lowest"]),
        hi=int(cov["implied base, highest"]),
        coveredpct=f(cov["share of the population covered"]),
        top=top[0]["forename"], topn=int(top[0]["incidence"]),
        topfreq=int(top[0]["one_in_n"]),
        second=top[1]["forename"], secondn=int(top[1]["incidence"]),
        maletop=first_male["forename"], maletopn=int(first_male["incidence"]),
        lastn=int(top[-1]["incidence"]), lastname=top[-1]["forename"],
        c10=f(c(10)["pct_of_covered"]), c100=f(c(100)["pct_of_covered"]),
        c100people=int(c(100)["people"]), c100pop=f(c(100)["pct_of_population"]),
        c500=f(c(500)["pct_of_covered"]),
        i1=ini[0]["initial"], i1pct=f(ini[0]["pct_of_covered"]),
        i1people=int(ini[0]["people"]),
        i2=ini[1]["initial"], i2pct=f(ini[1]["pct_of_covered"]),
        i3=ini[2]["initial"], i4=ini[3]["initial"],
        arank=a_rank, nini=len(ini),
        top4=r(sum(f(x["pct_of_covered"]) for x in ini[:4]), 2),
        femnames=int(fem["names"]), malnames=int(mal["names"]),
        fempeople=int(fem["people"]), malpeople=int(mal["people"]),
        femper=int(fem["people_per_name"]), malper=int(mal["people_per_name"]),
        namb=len(amb),
        ambtop=amb[0]["forename"], ambpct=int(amb[0]["gender_pct"]),
        ambmin=int(amb[0]["minority_pct"]),
        ambgender=amb[0]["gender"].lower(),
        hn=max((int(x["incidence"]) for x in top if len(x["forename"]) < 2),
               default=0),
    )
    F["uncoveredpct"] = r(100 - F["coveredpct"], 2)
    F["uncovered"] = F["base"] - F["people"]
    F["spread"] = r(100.0 * (F["hi"] / F["lo"] - 1), 2)
    F["toppct"] = r(100.0 * F["topn"] / F["base"], 2)
    F["topover"] = r(F["topn"] / F["secondn"], 2)
    F["crowding"] = r(F["malper"] / F["femper"], 2)
    F["missing"] = 26 - sum(1 for x in ini if x["initial"].isalpha())

    p = Page(PAGE)
    p.hero('''                <h1>One Filipino In {topfreq} Is Called {top}</h1>
                <p class="{hero_desc}">
                    The {n:,} commonest forenames in the Philippines, covering
                    {people:,} people. The file states no collection date &mdash;
                    but multiplying its two count columns together recovers a
                    population of {base:,}, which dates it itself.
                </p>

                <div class="header-actions">
                    <a href="https://www.kaggle.com/datasets/jorizivannvillanueva/most-popular-names-in-philippines-dataset" target="_blank" class="btn btn-primary">
                        Philippine forenames (Kaggle)
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="name.top.n">{topn:,}</div>
                        <div class="{label}">People called {top}, one in {topfreq}</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="conc.100">{c100}%</div>
                        <div class="{label}">Of the covered population in 100 names</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="names.base.spread">{spread}%</div>
                        <div class="{label}">Disagreement between the file's two count columns</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="names.uncovered.pct">{uncoveredpct}%</div>
                        <div class="{label}">Of Filipinos have a name outside this list</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">{top} is carried by <span data-fact="name.top.n">{topn:,}</span> people &mdash; one Filipino in <span data-fact="name.top.freq">{topfreq}</span>, and <span data-fact="name.top.pct">{toppct}%</span> of the whole country. The second commonest name, {second}, has <span data-fact="name.top.over.second">{topover}</span> times fewer.</p>
                    <ul class="tldr-list">
                        <li>The file states no collection date. Incidence counts bearers and frequency says one in N people, so their product recovers the population it was compiled against &mdash; and it agrees to within <span data-fact="names.base.spread">{spread}%</span> across all <span data-fact="names.n">{n:,}</span> rows. The median, <span data-fact="names.base">{base:,}</span>, puts the snapshot at roughly 2019-2020. That is an inference from the data, not a claim by the source.</li>
                        <li>Names are concentrated: <span data-fact="conc.10">{c10}%</span> of the covered population is in ten names and <span data-fact="conc.100">{c100}%</span> in a hundred. But the thousand names still leave <span data-fact="names.uncovered.pct">{uncoveredpct}%</span> of the country &mdash; <span data-fact="names.uncovered.people">{uncovered:,}</span> people &mdash; carrying something else.</li>
                        <li>The previously published claim that R and A are the commonest initials is half right. By bearers, <span data-fact="initial.top">{i1}</span> leads at <span data-fact="initial.top.pct">{i1pct}%</span>, then {i2} and {i3}; A is <span data-fact="initial.a.rank">{arank}</span>th. Those four cover <span data-fact="initial.top4.pct">{top4}%</span> between them, and <span data-fact="names.missing.initials">{missing}</span> letters begin no name here at all.</li>
                        <li><span data-fact="gender.female.names">{femnames}</span> names are recorded female against <span data-fact="gender.male.names">{malnames}</span> male, yet the male names cover more people &mdash; <span data-fact="gender.male.per.name">{malper:,}</span> bearers per name against <span data-fact="gender.female.per.name">{femper:,}</span>. Women's names are more varied, not fewer.</li>
                        <li>One snapshot, no regions, no ages, no surnames, no trend. Anything about how Filipino naming is changing is outside this data.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "A Fifth Of A Percent Of Names, A Third Of The People",
                  "Cumulative share of the covered population as the list "
                  "lengthens. The curve is steep at the start and long in the "
                  "tail: the thousandth name, {ln}, still has "
                  "{lnn:,} bearers.".format(ln=F["lastname"], lnn=F["lastn"]),
                  [("Top ten names", "{v}%".format(v=F["c10"]), "conc.10",
                    "Of the {p:,} people this list covers."
                    .format(p=F["people"])),
                   ("Top hundred", "{v}%".format(v=F["c100"]), "conc.100",
                    "<span data-fact=\"conc.100.people\">{n:,}</span> people "
                    "&mdash; <span data-fact=\"conc.100.of.pop\">{q}%</span> of "
                    "the whole country.".format(n=F["c100people"],
                                                q=F["c100pop"])),
                   ("Top five hundred", "{v}%".format(v=F["c500"]), "conc.500",
                    "Half the list carries four-fifths of its people. The other "
                    "half is the tail.")],
                  "Cumulative share of covered population by rank", "concChart"),
        p.section(2, "The File Dates Itself",
                  "This is the most useful thing in the dataset and it is not one "
                  "of its columns. Incidence is a count of bearers; frequency is "
                  "one in N people. Multiply them and you recover the population "
                  "the file was compiled against &mdash; which has to be the same "
                  "number in every row, and is.",
                  [("Implied population", "{v:,}".format(v=F["base"]),
                    "names.base",
                    "Median across all {n:,} rows.".format(n=F["n"])),
                   ("Spread across the file", "{v}%".format(v=F["spread"]),
                    "names.base.spread",
                    "<span data-fact=\"names.base.low\">{lo:,}</span> to "
                    "<span data-fact=\"names.base.high\">{hi:,}</span>, which is "
                    "the frequency denominator being rounded to a whole number "
                    "and nothing else.".format(lo=F["lo"], hi=F["hi"])),
                   ("What it implies", "≈2019-20", None,
                    "The Philippine population passed 106 million around then. "
                    "The file gives no date; this is inferred from it, and a "
                    "check fails if the two columns ever stop agreeing to within "
                    "2%.")],
                  "Population implied by each name's own two columns",
                  "baseChart"),
        p.section(3, "R, Then M, Then J",
                  "People per first letter, not names per first letter &mdash; "
                  "the two give different orders. {miss} letters of the alphabet "
                  "begin no name in this list."
                  .format(miss=F["missing"]),
                  [(F["i1"], "{v}%".format(v=F["i1pct"]), "initial.top.pct",
                    "<span data-fact=\"initial.top.people\">{n:,}</span> people. "
                    "Reynaldo, Ronaldo, Rosario, Roberto, Rowena and so on."
                    .format(n=F["i1people"])),
                   (F["i2"], "{v}%".format(v=F["i2pct"]), "initial.second.pct",
                    "Mary and Maria between them carry more than any other pair "
                    "on the list."),
                   ("A", "{v}th".format(v=F["arank"]), "initial.a.rank",
                    "Not second, as this page previously said. The top four "
                    "initials cover "
                    "<span data-fact=\"initial.top4.pct\">{t}%</span> of everyone "
                    "in the list.".format(t=F["top4"]))],
                  "People per first letter, top thousand names", "initialChart"),
        p.section(4, "More Women's Names, Fewer Women Per Name",
                  "The list holds more female names than male ones and fewer "
                  "female bearers, which means each male name is doing more work. "
                  "It says nothing about the sex ratio of the country &mdash; it "
                  "is about how widely names are shared.",
                  [("Female names", "{v}".format(v=F["femnames"]),
                    "gender.female.names",
                    "Carrying <span data-fact=\"gender.female.people\">{p:,}</span> "
                    "people, or "
                    "<span data-fact=\"gender.female.per.name\">{q:,}</span> each."
                    .format(p=F["fempeople"], q=F["femper"])),
                   ("Male names", "{v}".format(v=F["malnames"]),
                    "gender.male.names",
                    "Carrying <span data-fact=\"gender.male.people\">{p:,}</span> "
                    "people, or "
                    "<span data-fact=\"gender.male.per.name\">{q:,}</span> each."
                    .format(p=F["malpeople"], q=F["malper"])),
                   ("Crowding ratio", "{v}&times;".format(v=F["crowding"]),
                    "gender.crowding",
                    "A male name on this list is carried by {v} times as many "
                    "people as a female one.".format(v=F["crowding"]))],
                  "Names and bearers by recorded gender", "genderChart"),
        p.section(5, "The Names It Is Not Sure About",
                  "Each row carries the share of bearers of the stated gender. For "
                  "most names that is 99% or 100%. For {n} of them it is below "
                  "90%, and those are the interesting ones.".format(n=F["namb"]),
                  [("Ambiguous names", "{v}".format(v=F["namb"]),
                    "gender.ambiguous",
                    "Of {n:,}, where fewer than 90% of bearers share the recorded "
                    "gender.".format(n=F["n"])),
                   (F["ambtop"], "{a}/{b}".format(a=F["ambpct"], b=F["ambmin"]),
                    "gender.ambiguous.most.pct",
                    "The closest to even in the file: {p}% {g} and "
                    "<span data-fact=\"gender.ambiguous.most.minority\">{m}%</span> "
                    "not.".format(p=F["ambpct"], g=F["ambgender"],
                                  m=F["ambmin"])),
                   # The card value has to be the figure the fact returns, so the
                   # count of bearers goes in the value and the name itself in the
                   # heading. "H" carries no number to verify against.
                   ("The one-letter entry, H", "{n:,}".format(n=F["hn"]),
                    "names.single.letter.n",
                    "Bearers, at rank 707. It may be a real forename, an initial "
                    "recorded as one, or an artefact of how the source extracted "
                    "names. It is named here rather than charted as a name.")],
                  "Names whose gender split is not near-unanimous", "ambChart"),
        p.prose(6, "What This Data Cannot Say",
                "More is missing here than on most pages in this project, so it "
                "is worth being blunt about it.",
                [("There is no time dimension",
                  "One snapshot. No name can be shown rising or falling, and "
                  "nothing here supports a claim about naming fashions. A name "
                  "common among the living is not a name common among the newborn, "
                  "and this file cannot separate the two."),
                 ("There are no regions and no ages",
                  "National totals only. Nothing distinguishes Ilocos from "
                  "Mindanao, or a name popular in 1960 from one popular in 2015, "
                  "though the Spanish-derived names near the top &mdash; {s}, "
                  "Antonio, Reynaldo &mdash; are the kind that skew older."
                  .format(s=F["second"])),
                 ("It is forenames only",
                  "Philippine surnames are a much stranger subject: most were "
                  "assigned administratively from a catalogue in 1849, which is "
                  "why surnames cluster geographically in a way forenames do not. "
                  "None of that is in this file."),
                 ("The methodology is undocumented",
                  "The source does not say how incidence was counted or from "
                  "what. The internal agreement between its two columns is strong "
                  "evidence they were derived consistently, which is not the same "
                  "as evidence that they are right.")]),
        p.prose(7, "Method",
                "One small file, and one cross-check it makes possible.",
                [("The two count columns are checked against each other",
                  "Incidence times frequency must recover the same population in "
                  "every row. A check fails if any row falls more than 2% from the "
                  "median, which allows for the denominator being a rounded whole "
                  "number and nothing more. All {n:,} rows pass, from {lo:,} to "
                  "{hi:,}.".format(n=F["n"], lo=F["lo"], hi=F["hi"])),
                 ("The ranking is checked for monotonicity",
                  "A list ordered by rank must have incidence falling as rank "
                  "rises. A name further down with more bearers would mean one of "
                  "the two columns had been misread, and it is the kind of fault "
                  "that produces a chart which still looks reasonable."),
                 ("The ambiguity threshold is a stated constant",
                  "Ninety per cent, written once in the fetcher, used for the flag "
                  "and for the count the page quotes. A check asserts the flagged "
                  "list and the threshold have not drifted apart."),
                 ("The date is presented as an inference",
                  "The page says the file dates to roughly 2019-2020 because the "
                  "population it implies is {b:,}. It does not say the file is "
                  "from 2019, because the file does not say that."
                  .format(b=F["base"])),
                 ("Nothing is extrapolated to the country",
                  "The list covers {c}% of the implied population. Shares are "
                  "given either of the covered people or of the implied total, "
                  "and each is labelled, because those two denominators differ by "
                  "almost a third.".format(c=F["coveredpct"]))]),
    ]

    HCLS = ("%s fade-up" % p.t["sec_head"]) if p.t["sec_head"] else "fade-up"
    CWRAP = ("%s fade-up" % p.t["card_wrap"]) if p.t["card_wrap"] else "fade-up"
    S.append('''        <section class="{wrap}">
            <div class="container">
                <div class="{hcls}">
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="{cwrap}">
                    <ul>
                        <li>{top} is carried by
                        <span data-fact="name.top.n">{topn:,}</span> people, one
                        Filipino in <span data-fact="name.top.freq">{topfreq}</span>
                        and <span data-fact="name.top.pct">{toppct}%</span> of the
                        country &mdash;
                        <span data-fact="name.top.over.second">{topover}</span>
                        times the second name, {second}.</li>
                        <li>The file's two count columns agree to within
                        <span data-fact="names.base.spread">{spread}%</span> across
                        all <span data-fact="names.n">{n:,}</span> rows, implying a
                        population of
                        <span data-fact="names.base">{base:,}</span> and dating an
                        undated snapshot to about 2019-2020.</li>
                        <li><span data-fact="conc.100">{c100}%</span> of the covered
                        population is in a hundred names, yet
                        <span data-fact="names.uncovered.pct">{uncoveredpct}%</span>
                        of Filipinos &mdash;
                        <span data-fact="names.uncovered.people">{uncovered:,}</span>
                        people &mdash; carry a name outside the thousand.</li>
                        <li><span data-fact="initial.top">{i1}</span> is the
                        commonest initial at
                        <span data-fact="initial.top.pct">{i1pct}%</span>, not A,
                        which is <span data-fact="initial.a.rank">{arank}</span>th;
                        <span data-fact="names.missing.initials">{missing}</span>
                        letters begin no name at all.</li>
                        <li>There are more female names
                        (<span data-fact="gender.female.names">{femnames}</span>)
                        than male
                        (<span data-fact="gender.male.names">{malnames}</span>) but
                        each male name carries
                        <span data-fact="gender.crowding">{crowding}</span> times as
                        many people.</li>
                        <li><span data-fact="gender.ambiguous">{namb}</span> names
                        are not clearly one gender, {ambtop} most of all at
                        <span data-fact="gender.ambiguous.most.pct">{ambpct}</span>/{ambmin}.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    TOP = top[:20]
    RANKS = [int(x["rank"]) for x in top]
    CUM, run = [], 0
    for x in top:
        run += int(x["incidence"])
        CUM.append(round(100.0 * run / F["people"], 3))
    AMB = amb[:20]

    charts = ['''        // 01 the concentration curve over all thousand ranks, with the labelled
        //    cuts as points on it.
        new Chart(document.getElementById('concChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [{ label: 'Cumulative %% of covered population', data: %s,
                             borderColor: '#3b82f6',
                             backgroundColor: 'rgba(59,130,246,0.15)',
                             borderWidth: 3, pointRadius: 0, fill: true }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'Name rank' },
                               ticks: { maxTicksLimit: 12 } },
                          y: { min: 0, max: 100,
                               title: { display: true, text: '%% of covered population' } } }
            }
        });''' % (js(RANKS), js(CUM)),

              '''        // 02 the implied population from each row's own two columns. A flat line is
        //    the finding; the y range is deliberately tight so the 1.2%% spread is
        //    visible rather than hidden by a zero baseline.
        new Chart(document.getElementById('baseChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [{ label: 'Implied population', data: %s,
                             borderColor: '#22c55e', borderWidth: 2,
                             pointRadius: 0, fill: false }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'Name rank' },
                               ticks: { maxTicksLimit: 12 } },
                          y: { min: 105000000, max: 107500000,
                               title: { display: true, text: 'Incidence x frequency' } } }
            }
        });''' % (js(RANKS), js([int(x["implied_population"]) for x in top])),

              '''        // 03 people per initial, not names per initial.
        new Chart(document.getElementById('initialChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'People', data: %s, backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + ' name(s) in the top 1,000'; } } } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'People carrying a name with this initial' } } }
            }
        });''' % (js([x["initial"] for x in ini]),
                  js([int(x["people"]) for x in ini]),
                  js(["#ef4444" if i == 0 else "#3b82f6" for i in range(len(ini))]),
                  js([int(x["names"]) for x in ini])),

              '''        // 04 names against bearers by gender, two axes: the point is that the two
        //    bars disagree in direction.
        new Chart(document.getElementById('genderChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Names in the list', data: %s,
                      backgroundColor: '#8b5cf6', yAxisID: 'y' },
                    { label: 'People carrying them', data: %s,
                      backgroundColor: '#f59e0b', yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { position: 'left', beginAtZero: true,
                               title: { display: true, text: 'Names' } },
                          y1: { position: 'right', beginAtZero: true,
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: 'People' } } }
            }
        });''' % (js([x["gender"] for x in gen]),
                  js([int(x["names"]) for x in gen]),
                  js([int(x["people"]) for x in gen])),

              '''        // 05 the ambiguous names, majority share against minority share. Anything
        //    near the middle is a name the file cannot assign.
        new Chart(document.getElementById('ambChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Recorded gender (%%)', data: %s, backgroundColor: '#3b82f6' },
                    { label: 'The other (%%)', data: %s, backgroundColor: '#ef4444' }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                scales: { x: { stacked: true, min: 0, max: 100,
                               title: { display: true, text: '%% of bearers' } },
                          y: { stacked: true } }
            }
        });''' % (js(["%s (%s)" % (x["forename"], x["gender"][0]) for x in AMB]),
                  js([int(x["gender_pct"]) for x in AMB]),
                  js([int(x["minority_pct"]) for x in AMB])),
              ]

    p.sections(S)
    p.charts(charts)
    p.head(
        "One Filipino In %d Is Called %s" % (F["topfreq"], F["top"]),
        "The %s commonest Philippine forenames: %s alone covers %s%% of the "
        "country, a hundred names cover %s%% of those listed, and the file's two "
        "count columns agree closely enough to date an undated snapshot."
        % (format(F["n"], ","), F["top"], F["toppct"], F["c100"]),
        "%s is one Filipino in %d. And the file dates itself to within 1.2%%."
        % (F["top"], F["topfreq"]),
        "One Filipino In %d Is Called %s" % (F["topfreq"], F["top"]))
    p.faq({
        "What is the most common name in the Philippines?":
            "%s, carried by %s people -- one Filipino in %d, and %s%% of the "
            "country. The second commonest is %s with %s, which is %s times fewer. "
            "The commonest male name is %s with %s."
            % (F["top"], format(F["topn"], ","), F["topfreq"], F["toppct"],
               F["second"], format(F["secondn"], ","), F["topover"],
               F["maletop"], format(F["maletopn"], ",")),
        "What letter do most Filipino first names start with?":
            "By number of people carrying them, R -- %s%% of everyone in this list, "
            "or %s people. Then %s and %s, with A fourth. Those four initials "
            "account for %s%% between them, and %d letters of the alphabet begin no "
            "name in the top thousand at all."
            % (F["i1pct"], format(F["i1people"], ","), F["i2"], F["i3"], F["top4"],
               F["missing"]),
        "How many Filipinos share the same first name?":
            "Names are concentrated but not exhaustively so. Ten names cover %s%% of "
            "the %s people this list accounts for, and a hundred names cover %s%%. "
            "But the top thousand names still leave %s%% of the country -- about %s "
            "people -- carrying something outside the list."
            % (F["c10"], format(F["people"], ","), F["c100"], F["uncoveredpct"],
               format(F["uncovered"], ",")),
        "When was this Philippine names data collected?":
            "The file does not say, but it can be worked out from within. Incidence "
            "counts bearers and frequency gives one in N people, so multiplying them "
            "recovers the population the data was compiled against. Across all %s "
            "names that comes to between %s and %s -- a spread of %s%%, which is "
            "just the frequency denominator being rounded to a whole number. A "
            "median of %s puts the snapshot at roughly 2019-2020. That is an "
            "inference from the data rather than a statement by the source."
            % (format(F["n"], ","), format(F["lo"], ","), format(F["hi"], ","),
               F["spread"], format(F["base"], ",")),
        "Are there more male or female names in the Philippines?":
            "In this list, %d names are recorded female and %d male -- but the male "
            "names cover more people, %s against %s. So each male name is carried by "
            "%s bearers on average and each female name by %s, a ratio of %s. That "
            "is a statement about how varied women's names are, not about the sex "
            "ratio of the population. %d names are not clearly either, %s most of "
            "all at %d%% / %d%%."
            % (F["femnames"], F["malnames"], format(F["malpeople"], ","),
               format(F["fempeople"], ","), format(F["malper"], ","),
               format(F["femper"], ","), F["crowding"], F["namb"], F["ambtop"],
               F["ambpct"], F["ambmin"]),
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
