#!/usr/bin/env python3
"""Regenerate projects/global-openaccess-analysis.html from data/global-openaccess.

    .venv/bin/python tools/pages/build_openaccess.py

OpenAlex sorts every published work into six open-access states. One of them,
diamond, means the journal is fully open AND charges the author nothing. It is
the second largest of the six, the fastest growing, and the one people cite when
they say open access does not have to cost researchers money.

DOAJ asks journals that question directly and records the answer with a price and
a currency. Comparing the two, journal by journal, on 348 journals with a control
group: of the 167 that OpenAlex labels diamond, 79 -- 47.31% -- charge an author
fee according to DOAJ. Nearly half.

The mechanism is that OpenAlex has no apc_usd value for those journals and a null
there is being read as a zero. So the error is not random: 21.14% of fee-charging
journals priced in a hard currency carry the label, against 50.60% of those priced
in anything else.

Which makes the country map of diamond open access partly a map of which
currencies have been converted. Indonesia is first at 63.61%, Germany is at 5.03%,
and 21 of the 46 fee-charging Indonesian-rupiah journals in this sample are
labelled diamond.

The other arm of the audit matters as much: of 90 journals DOAJ says charge
nothing, 88 are labelled diamond. The classification over-includes; it does not
miss genuinely free journals. Saying only the first half would be a different and
less honest page.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/global-openaccess"
PAGE = "projects/global-openaccess-analysis.html"
STATES = ["diamond", "gold", "hybrid", "bronze", "green", "closed"]


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    yr = rows("oa_year")
    sa = rows("oa_status_apc")
    cty = rows("oa_country")
    aud = rows("oa_label_audit")
    cov = {x["property"] + "|" + x["unit"]: x["value"] for x in rows("oa_coverage")}

    def C(p_, u):
        return f(cov[p_ + "|" + u])

    Y = {(int(x["year"]), x["oa_status"]): x for x in yr}
    A = {x["oa_status"]: x for x in sa}
    K = {x["iso2"]: x for x in cty}
    years = sorted({int(x["year"]) for x in yr})
    YEAR = int(C("year analysed", "year"))

    charging = [x for x in aud if x["doaj_charges_fee"] == "yes"]
    free = [x for x in aud if x["doaj_charges_fee"] == "no"]
    wrong = [x for x in aud if x["verdict"] == "wrong"]
    labelled = [x for x in aud if x["openalex_labels_diamond"] == "yes"]
    hardc = [x for x in charging if x["hard_currency"] == "yes"]
    softc = [x for x in charging if x["hard_currency"] == "no"]
    hardw = [x for x in wrong if x["hard_currency"] == "yes"]
    softw = [x for x in wrong if x["hard_currency"] == "no"]

    F = dict(
        year=YEAR, works=int(C("works in the year analysed", "works")),
        freepct=C("open access, any kind", "percent"),
        diaw=int(Y[(YEAR, "diamond")]["works"]),
        diapct=f(Y[(YEAR, "diamond")]["pct_of_year"]),
        goldpct=f(Y[(YEAR, "gold")]["pct_of_year"]),
        hybpct=f(Y[(YEAR, "hybrid")]["pct_of_year"]),
        bronzepct=f(Y[(YEAR, "bronze")]["pct_of_year"]),
        closedpct=f(Y[(YEAR, "closed")]["pct_of_year"]),
        closed15=f(Y[(2015, "closed")]["pct_of_year"]),
        dia15=f(Y[(2015, "diamond")]["pct_of_year"]),
        goldapc=f(A["gold"]["pct_with_paid_apc"]),
        hybapc=f(A["hybrid"]["pct_with_paid_apc"]),
        diaapc=f(A["diamond"]["pct_with_paid_apc"]),
        closedapc=f(A["closed"]["pct_with_paid_apc"]),
        djn=int(C("DOAJ journals", "journals")),
        djfree=int(C("DOAJ journals charging no author fee", "journals")),
        djfreepct=C("DOAJ journals charging no author fee", "percent"),
        an=len(aud), ach=len(charging), afree=len(free),
        wn=len(wrong), wpct=r(100.0 * len(wrong) / len(charging), 2),
        lab=len(labelled),
        labpct=r(100.0 * sum(1 for x in labelled
                             if x["doaj_charges_fee"] == "yes") / len(labelled), 2),
        hardpct=r(100.0 * len(hardw) / len(hardc), 2),
        softpct=r(100.0 * len(softw) / len(softc), 2),
        ctrlok=sum(1 for x in free if x["openalex_labels_diamond"] == "yes"),
        iddia=f(K["ID"]["diamond_pct"]), idworks=int(K["ID"]["works"]),
        dedia=f(K["DE"]["diamond_pct"]), nldia=f(K["NL"]["diamond_pct"]),
        phdia=f(K["PH"]["diamond_pct"]),
        idrch=sum(1 for x in charging if x["currency"] == "IDR"),
        idrw=sum(1 for x in wrong if x["currency"] == "IDR"),
        absent=int(C("sampled journals absent from OpenAlex", "count")),
    )
    F["ratio"] = r(F["softpct"] / F["hardpct"], 1)
    F["idover"] = r(F["iddia"] / F["dedia"], 1)

    p = Page(PAGE)
    p.relocate(
        "global-trade-mirror-analysis",
        og_image="og-openaccess.png",
        keywords=["diamond open access", "article processing charge", "OpenAlex",
                  "DOAJ", "APC", "open data", "data analysis"],
        dataset_name="Open-access status and author charges, %d" % YEAR,
        dataset_desc=("Every indexed work in %d by open-access state, by year and "
                      "by country, audited journal by journal against DOAJ's direct "
                      "record of whether the journal charges an author fee" % YEAR),
        breadcrumb="The Free-To-Publish Label That Is Not",
        crumb_tail="Open Access",
        creator="OpenAlex / DOAJ",
        dataset_url="https://api.openalex.org/",
        tags=["\U0001f4d6 Research", "OpenAlex", "DOAJ",
              "%s works" % format(F["works"], ","),
              "<span class=\"dot\"></span> %d journals audited" % F["an"]],
        info=[("Data Sources",
               '<a href="https://api.openalex.org/" target="_blank" '
               'rel="noopener">OpenAlex</a> &middot; '
               '<a href="https://doaj.org/api/" target="_blank" '
               'rel="noopener">DOAJ</a> &middot; '
               '<a href="https://api.worldbank.org/v2/" target="_blank" '
               'rel="noopener">World Bank</a>'),
              ("Coverage",
               "%s works in %d &middot; %d-%d by state &middot; 60 countries"
               % (format(F["works"], ","), YEAR, years[0], years[-1])),
              ("Audit",
               "%d journals compared against DOAJ, %d fee-charging and %d "
               "fee-free as a control" % (F["an"], F["ach"], F["afree"])),
              ("Licence", "CC0 (OpenAlex) &middot; CC BY-SA (DOAJ)")])

    p.head(
        "Half The Journals Labelled Free-To-Publish Charge A Fee",
        "OpenAlex calls %s works in %d 'diamond' — fully open and free for the "
        "author. Audited against DOAJ, %s%% of the journals carrying that label "
        "charge an author fee, and the error is %s times more likely when the fee "
        "is not priced in a hard currency."
        % (format(F["diaw"], ","), YEAR, F["labpct"], F["ratio"]),
        "Of the journals OpenAlex labels free-to-publish, %s%% charge an author "
        "fee. The error tracks currency." % F["labpct"],
        "Half The Journals Labelled Free-To-Publish Charge A Fee")

    p.hero('''                <h1>Half The Journals Labelled Free-To-Publish Charge A Fee</h1>
                <p class="{hero_desc}">
                    OpenAlex sorts every paper into six open-access states. One,
                    &ldquo;diamond&rdquo;, means the journal is fully open
                    <em>and</em> charges the author nothing &mdash; {diaw:,}
                    works in {year}. DOAJ asks journals that question directly.
                    Of {lab} journals carrying the label in this audit, {wn}
                    charge a fee, and the disagreement is {ratio} times more
                    likely when the price is not in dollars or euros.
                </p>

                <div class="header-actions">
                    <a href="https://doaj.org/" target="_blank" class="btn btn-primary">
                        DOAJ
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="labelled.but.charges">{labpct}%</div>
                        <div class="{label}">Of journals labelled diamond that charge a fee</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="soft.pct">{softpct}%</div>
                        <div class="{label}">Mislabelled, when the fee is not in a hard currency</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="hard.pct">{hardpct}%</div>
                        <div class="{label}">Mislabelled, when it is</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="id.dia">{iddia}%</div>
                        <div class="{label}">Indonesia&rsquo;s diamond share; Germany&rsquo;s is {dedia}%</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Of the <span data-fact="labelled.diamond">{lab}</span> journals OpenAlex labels diamond in this audit &mdash; fully open and free for the author &mdash; <span data-fact="wrong.n">{wn}</span> charge an author fee according to DOAJ, which asks them directly. That is <span data-fact="labelled.but.charges">{labpct}%</span>.</p>
                    <ul class="tldr-list">
                        <li>The error is not random. <span data-fact="hard.pct">{hardpct}%</span> of fee-charging journals priced in a hard currency carry the label, against <span data-fact="soft.pct">{softpct}%</span> of those priced in anything else &mdash; <span data-fact="soft.over.hard">{ratio}</span> times more likely. OpenAlex has no dollar price on file for those journals and a missing price is being read as no price.</li>
                        <li>The other arm of the audit is reassuring and belongs here too: of <span data-fact="control.free">{afree}</span> journals DOAJ says charge nothing, <span data-fact="control.right">{ctrlok}</span> are labelled diamond. The classification over-includes; it does not miss genuinely free journals.</li>
                        <li>That makes the country map of diamond open access partly a map of which currencies have been converted. Indonesia leads at <span data-fact="id.dia">{iddia}%</span> against Germany&rsquo;s <span data-fact="de.dia">{dedia}%</span> &mdash; <span data-fact="id.over.de">{idover}</span> times &mdash; and <span data-fact="idr.wrong">{idrw}</span> of the <span data-fact="idr.charging">{idrch}</span> fee-charging rupiah-priced journals here carry the label.</li>
                        <li>The six states are genuinely different things, and the data says so: <span data-fact="gold.apc.pct">{goldapc}%</span> of gold works and <span data-fact="hybrid.apc.pct">{hybapc}%</span> of hybrid works carry a recorded charge, against <span data-fact="dia.apc.pct">{diaapc}%</span> of diamond and <span data-fact="closed.apc.pct">{closedapc}%</span> of closed. Only two of the six move money.</li>
                        <li>Asked directly rather than inferred, DOAJ's own answer is the cleaner one: <span data-fact="doaj.free">{djfree:,}</span> of <span data-fact="doaj.journals">{djn:,}</span> indexed journals &mdash; <span data-fact="doaj.free.pct">{djfreepct}%</span> &mdash; charge no author fee at all.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "Six States, Not Two",
                  "&ldquo;{freepct}% of research is open access&rdquo; sums five "
                  "different arrangements. Three of them can cost an author money, "
                  "one is revocable, and one means only that a manuscript sits in a "
                  "repository while the published version stays behind a "
                  "paywall.".format(**F),
                  [("Diamond", "{v}%".format(v=F["diapct"]), "dia.pct",
                    "Fully open, no author fee &mdash; supposedly. "
                    "<span data-fact=\"dia.works\">{n:,}</span> works, up from "
                    "<span data-fact=\"dia.2015\">{o}%</span> in 2015."
                    .format(n=F["diaw"], o=F["dia15"])),
                   ("Gold and hybrid",
                    "{a}% + {b}%".format(a=F["goldpct"], b=F["hybpct"]), "gold.pct",
                    "The author-pays kinds. "
                    "<span data-fact=\"gold.apc.pct\">{g}%</span> of gold works and "
                    "<span data-fact=\"hybrid.apc.pct\">{h}%</span> of hybrid ones "
                    "carry a recorded charge.".format(g=F["goldapc"], h=F["hybapc"])),
                   ("Bronze", "{v}%".format(v=F["bronzepct"]), "bronze.pct",
                    "Free to read on the publisher&rsquo;s site with no licence at "
                    "all. It can be closed again tomorrow and it cannot legally be "
                    "reused or mined.")],
                  "The six open-access states as shares of all indexed work, "
                  "{a} to {b}".format(a=years[0], b=years[-1]),
                  "stateChart"),

        p.section(2, "The Audit",
                  "One label claims to know something about money. DOAJ asks "
                  "journals that same question and writes down the answer, with a "
                  "price and a currency. {an} journals, compared both ways: {ach} "
                  "that say they charge and {afree} that say they do not."
                  .format(**F),
                  [("Labelled diamond, but charging",
                    "{v}%".format(v=F["labpct"]), "labelled.but.charges",
                    "<span data-fact=\"wrong.n\">{w}</span> of "
                    "<span data-fact=\"labelled.diamond\">{l}</span> journals "
                    "carrying the label charge an author fee."
                    .format(w=F["wn"], l=F["lab"])),
                   ("Of the ones that do charge",
                    "{v}%".format(v=F["wpct"]), "wrong.pct",
                    "Are labelled diamond anyway, out of "
                    "<span data-fact=\"audit.charging\">{n}</span> fee-charging "
                    "journals audited.".format(n=F["ach"])),
                   ("The control group",
                    "{a} of {b}".format(a=F["ctrlok"], b=F["afree"]), "control.right",
                    "Journals DOAJ says charge nothing that are correctly labelled "
                    "diamond. The label over-includes rather than under-includes, "
                    "and that distinction is the difference between a bug and a "
                    "smear.")],
                  "The audit as a two-by-two: what DOAJ says against what the label "
                  "says",
                  "auditChart"),

        p.section(3, "The Error Follows The Currency",
                  "OpenAlex records an article charge in US dollars. For a journal "
                  "that prices in rupiah, rial or hryvnia there is often no dollar "
                  "figure on file &mdash; and a missing price is being read as no "
                  "price.",
                  [("Priced in a hard currency",
                    "{v}%".format(v=F["hardpct"]), "hard.pct",
                    "Of fee-charging journals priced in dollars, euros and the like "
                    "that carry the diamond label anyway."),
                   ("Priced in anything else",
                    "{v}%".format(v=F["softpct"]), "soft.pct",
                    "The same measure for every other currency &mdash; "
                    "<span data-fact=\"soft.over.hard\">{r}</span> times as "
                    "likely.".format(r=F["ratio"])),
                   ("Indonesian rupiah",
                    "{a} of {b}".format(a=F["idrw"], b=F["idrch"]), "idr.wrong",
                    "Fee-charging rupiah-priced journals in this sample that are "
                    "labelled diamond. Indonesia is the country the diamond map "
                    "puts first.")],
                  "Mislabel rate among fee-charging journals, by whether the fee is "
                  "priced in a hard currency",
                  "currencyChart"),

        p.section(4, "Which Makes The Map Suspect",
                  "Read at face value, the country ranking says the places least "
                  "able to afford an article charge publish overwhelmingly in "
                  "journals that levy none. It is a good story and this data cannot "
                  "support it.",
                  [("Indonesia", "{v}%".format(v=F["iddia"]), "id.dia",
                    "Diamond share of <span data-fact=\"id.works\">{n:,}</span> "
                    "works &mdash; the highest of the sixty countries read here."
                    .format(n=F["idworks"])),
                   ("Germany", "{v}%".format(v=F["dedia"]), "de.dia",
                    "Against the Netherlands&rsquo; "
                    "<span data-fact=\"nl.dia\">{n}%</span>. Indonesia&rsquo;s share "
                    "is <span data-fact=\"id.over.de\">{r}</span> times "
                    "Germany&rsquo;s.".format(n=F["nldia"], r=F["idover"])),
                   ("The Philippines", "{v}%".format(v=F["phdia"]), "ph.dia",
                    "Also high, and subject to the same caveat. Nothing here says "
                    "the ranking is wrong &mdash; it says the ranking is not "
                    "measured well enough to read.")],
                  "Diamond share by country, ordered &mdash; and how much of the "
                  "ordering the currency effect could account for",
                  "countryChart"),

        p.prose(5, "What Would Settle It",
                "This page shows the label is unreliable. It does not show what the "
                "true country ranking is, and three specific things would.",
                [("A dollar price for every journal",
                  "The whole mechanism is a null in one field. If OpenAlex carried "
                  "a converted charge for the journals that price in rupiah and "
                  "rial, the classification would be right about them and the "
                  "country map could be read directly."),
                 ("The audit at full size",
                  "%d journals is enough to establish the rate and its currency "
                  "dependence. It is not enough to correct sixty countries one by "
                  "one. Doing that means auditing every journal each country "
                  "publishes in, which is a much larger job than a daily API "
                  "allowance permits." % F["an"]),
                 ("Asking DOAJ first",
                  "DOAJ already answers the question directly for %s journals, %s%% "
                  "of which charge nothing. Building the country map from that "
                  "answer rather than from an inferred label would avoid the problem "
                  "entirely, at the cost of covering only DOAJ-indexed journals."
                  % (format(F["djn"], ","), F["djfreepct"]))]),

        p.prose(6, "What These Numbers Are Not",
                "Four limits, and the first is the one that decides how far the "
                "headline travels.",
                [("A sample, and a budget-limited one",
                  "The audit covers %d journals: %d that DOAJ records as charging "
                  "and %d as not. OpenAlex allows about a thousand requests a day "
                  "without an account and each journal costs two, so the sample "
                  "stopped where the allowance did rather than at a planned size. "
                  "%d sampled journals were not in OpenAlex at all."
                  % (F["an"], F["ach"], F["afree"], F["absent"])),
                 ("DOAJ is not infallible either",
                  "It records what a journal told it, and journals change their "
                  "fees. Where the two sources disagree this page assumes DOAJ is "
                  "right because it asked; that assumption is doing real work and "
                  "is worth stating plainly."),
                 ("A journal-level label on work-level counts",
                  "The state is assigned per work but decided by the journal, so a "
                  "journal labelled wrongly mislabels everything it published. That "
                  "is why a modest share of journals can move a national percentage "
                  "a long way."),
                 ("Nothing here is about quality",
                  "Charging an author fee is not evidence of a bad journal and "
                  "charging none is not evidence of a good one. The only claim on "
                  "this page is that a field which says a journal charges nothing "
                  "frequently describes a journal that charges something.")]),
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
                        <li>Of <span data-fact="labelled.diamond">{lab}</span>
                        journals labelled diamond &mdash; free to read and free to
                        publish &mdash; <span data-fact="wrong.n">{wn}</span> charge
                        an author fee:
                        <span data-fact="labelled.but.charges">{labpct}%</span>.</li>
                        <li>The error tracks currency:
                        <span data-fact="hard.pct">{hardpct}%</span> of fee-charging
                        journals priced in a hard currency carry the label against
                        <span data-fact="soft.pct">{softpct}%</span> of the rest,
                        <span data-fact="soft.over.hard">{ratio}</span> times as
                        likely.</li>
                        <li>The label over-includes rather than misses: of
                        <span data-fact="control.free">{afree}</span> genuinely
                        fee-free journals,
                        <span data-fact="control.right">{ctrlok}</span> are labelled
                        correctly.</li>
                        <li>So the country ranking is partly a currency artefact.
                        Indonesia leads at <span data-fact="id.dia">{iddia}%</span>
                        against Germany&rsquo;s
                        <span data-fact="de.dia">{dedia}%</span>, and
                        <span data-fact="idr.wrong">{idrw}</span> of
                        <span data-fact="idr.charging">{idrch}</span> fee-charging
                        rupiah-priced journals here carry the label.</li>
                        <li>Only two of the six states move money:
                        <span data-fact="gold.apc.pct">{goldapc}%</span> of gold and
                        <span data-fact="hybrid.apc.pct">{hybapc}%</span> of hybrid
                        works carry a recorded charge, against
                        <span data-fact="dia.apc.pct">{diaapc}%</span> of
                        diamond.</li>
                        <li>Asked directly, DOAJ says
                        <span data-fact="doaj.free">{djfree:,}</span> of
                        <span data-fact="doaj.journals">{djn:,}</span> journals
                        &mdash;
                        <span data-fact="doaj.free.pct">{djfreepct}%</span> &mdash;
                        charge no author fee.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    # ---- chart data ---------------------------------------------------------
    COL = {"diamond": "#22d3ee", "gold": "#f59e0b", "hybrid": "#f97316",
           "bronze": "#a16207", "green": "#22c55e", "closed": "#64748b"}
    CN = sorted(cty, key=lambda c: -f(c["diamond_pct"]))[:20]

    charts = ['''        // 01 the six states over time. closed shrinking is the headline everybody
        //    quotes; the five ways of being open are not the same thing.
        new Chart(document.getElementById('stateChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: %s
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: '%% of all indexed work' } } }
            }
        });''' % (js(years),
                  "[" + ",".join(
                      """
                    { label: '%s', data: %s, borderColor: '%s',
                      backgroundColor: '%s', pointBackgroundColor: '%s',
                      borderWidth: %d, pointRadius: 2, fill: false }"""
                      % (st.title(), js([f(Y[(y, st)]["pct_of_year"]) for y in years]),
                         COL[st], COL[st], COL[st], 3 if st == "diamond" else 2)
                      for st in STATES) + "\n                ]"),

              '''        // 02 the audit as a two-by-two. The orange block is the finding and the
        //    tall green one is the control that stops it being a smear.
        new Chart(document.getElementById('auditChart'), {
            type: 'bar',
            data: {
                labels: ['DOAJ: charges a fee', 'DOAJ: charges nothing'],
                datasets: [
                    { label: 'OpenAlex says diamond', data: %s,
                      backgroundColor: '#f59e0b' },
                    { label: 'OpenAlex says not diamond', data: %s,
                      backgroundColor: 'rgba(100,116,139,0.8)' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { x: { stacked: true },
                          y: { stacked: true, beginAtZero: true,
                               title: { display: true, text: 'Journals audited' } } }
            }
        });''' % (js([sum(1 for x in charging if x["openalex_labels_diamond"] == "yes"),
                      sum(1 for x in free if x["openalex_labels_diamond"] == "yes")]),
                  js([sum(1 for x in charging if x["openalex_labels_diamond"] == "no"),
                      sum(1 for x in free if x["openalex_labels_diamond"] == "no")])),

              '''        // 03 the same mislabel rate split by whether the fee has a hard-currency
        //    price. The gap between the two bars is the mechanism.
        new Chart(document.getElementById('currencyChart'), {
            type: 'bar',
            data: {
                labels: ['Priced in a hard currency', 'Priced in anything else'],
                datasets: [{ label: 'Mislabelled as diamond (%%)', data: %s,
                             backgroundColor: ['#3b82f6', '#ef4444'] }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: (c) =>
                               %s[c.dataIndex] } } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: '%% of fee-charging journals' } } }
            }
        });''' % (js([F["hardpct"], F["softpct"]]),
                  js(["%d of %d journals" % (len(hardw), len(hardc)),
                      "%d of %d journals" % (len(softw), len(softc))])),

              '''        // 04 the country ranking the label produces. Presented as what the label
        //    says rather than as what is true, which is section 4's whole point.
        new Chart(document.getElementById('countryChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Share labelled diamond (%%)', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: '%% of works labelled diamond' } } }
            }
        });''' % (js([c["country"][:22] for c in CN]),
                  js([f(c["diamond_pct"]) for c in CN]),
                  js(["#22d3ee" if c["iso2"] in ("ID", "PH") else "#3b82f6"
                      for c in CN])),
    ]

    p.sections(S)
    p.charts(charts)
    p.faq({
        "What is diamond open access?":
            "A journal that is fully open access and charges the author nothing to "
            "publish. It is one of six states OpenAlex assigns, it covers %s works "
            "in %d -- %s%% of everything indexed -- and it is the one people cite "
            "when they say open access need not cost researchers money."
            % (format(F["diaw"], ","), YEAR, F["diapct"]),
        "Is the diamond label reliable?":
            "Often not. Audited against DOAJ, which asks journals directly whether "
            "they charge, %s%% of the journals carrying the diamond label do charge "
            "an author fee -- %d of %d in this sample. The error runs one way: of "
            "%d journals DOAJ says charge nothing, %d are labelled diamond, so the "
            "classification over-includes rather than missing genuinely free "
            "journals."
            % (F["labpct"], F["wn"], F["lab"], F["afree"], F["ctrlok"]),
        "Why does the currency matter?":
            "Because OpenAlex records an article charge in US dollars, and for a "
            "journal priced in rupiah, rial or hryvnia there is often no dollar "
            "figure on file. A missing price is being read as no price. %s%% of "
            "fee-charging journals priced in a hard currency carry the diamond label "
            "against %s%% of the rest, which is %s times as likely."
            % (F["hardpct"], F["softpct"], F["ratio"]),
        "Which countries publish the most diamond open access?":
            "By the label, Indonesia at %s%% of %s works, against Germany's %s%% and "
            "the Netherlands' %s%%. That ranking should not be read directly: %d of "
            "the %d fee-charging rupiah-priced journals in this audit carry the "
            "diamond label, so the map is partly a map of which currencies have been "
            "converted into dollars."
            % (F["iddia"], format(F["idworks"], ","), F["dedia"], F["nldia"],
               F["idrw"], F["idrch"]),
        "How many journals charge no author fee?":
            "Asked directly rather than inferred, DOAJ records %s of %s indexed "
            "journals -- %s%% -- as charging nothing. That is the cleaner answer to "
            "the question, and it covers only DOAJ-indexed journals."
            % (format(F["djfree"], ","), format(F["djn"], ","), F["djfreepct"]),
    })
    p.save(len(S), len(charts))
    blog(F)


BLOG = "blog/global-openaccess-analysis.html"
TITLE = "A Label Said These Journals Were Free. Half Of Them Charge."
DESC = ("One big database sorts science journals into free and not free. I "
        "checked 348 of them against the people who ask the journals directly.")
SUB = "I checked 348 journals. The label was wrong about half the ones it called free."


def fct(k, v):
    return '<span data-fact="%s">%s</span>' % (k, v)


def blog(F):
    import io, re
    src = io.open(BLOG, encoding="utf-8").read()

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, lambda _m: rep, src, count=1)
        if n != 1:
            raise SystemExit("blog: %s matched %d times" % (why, n))

    swap(r"<title>[^<]*</title>", "<title>%s | Allan Ni\u00f1al</title>" % TITLE, "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % DESC, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="%s | Allan Ni\u00f1al">' % TITLE, "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % DESC, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="%s">' % TITLE, "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % DESC, "tw:desc")
    swap(r'"headline": "[^"]*"', '"headline": "%s"' % TITLE, "headline")
    swap(r'"description": "[^"]*"', '"description": "%s"' % DESC, "ld desc")
    src = src.replace("global-trade-mirror-analysis", "global-openaccess-analysis")
    swap(r'<span class="current">[^<]*</span>',
         '<span class="current">Open Access</span>', "crumb")
    swap(r'<h1>[^<]*</h1>', "<h1>%s</h1>" % TITLE, "h1")
    swap(r'<p class="subtitle">[^<]*</p>', '<p class="subtitle">%s</p>' % SUB, "subtitle")

    a = src.index('<div class="article-content">')
    a = src.index("\n", a) + 1
    b = src.index('                <div class="project-link-box">')
    io.open(BLOG, "w", encoding="utf-8").write(src[:a] + body(F) + src[b:])
    print("rebuilt %s" % BLOG)


def body(F):
    g = fct
    return """                <p>When someone writes a science paper, a journal prints it.</p>

                <p>Some journals make the reader pay. Some make the writer pay. And a few charge nobody at all.</p>

                <p>That last kind has a name. People call it diamond.</p>

                <p>A big database called OpenAlex puts a diamond label on those journals. It labelled {diaw} papers that way in {year}.</p>

                <p>There is also a group called DOAJ. They just ask each journal: do you charge the writer? Then they write down the answer.</p>

                <p>So I took {an} journals and checked one list against the other.</p>

                <h2>The Label Was Wrong A Lot</h2>

                <p>Of the {lab} journals with the diamond label, {wn} of them do charge the writer.</p>

                <div class="stat-callout">
                    <div class="stat-number">{labpct_f}%</div>
                    <div class="stat-label">Of journals labelled free-to-publish that charge a fee</div>
                </div>

                <p>That is close to half.</p>

                <p>One of them charges three thousand five hundred and eighty pounds.</p>

                <h2>Why It Goes Wrong</h2>

                <p>OpenAlex keeps the price in dollars.</p>

                <p>Lots of journals do not price in dollars. They price in rupiah, or rial, or hryvnia.</p>

                <p>For those, OpenAlex often has no dollar price at all. The box is empty.</p>

                <p>And an empty box is being read as a zero.</p>

                <p>You can see it in the numbers. When the price is in dollars or euros, {hardpct} per cent of paying journals get the wrong label.</p>

                <p>When it is in anything else, {softpct} per cent do.</p>

                <p>That is {ratio} times as often.</p>

                <h2>The Good News First</h2>

                <p>I want to be fair to the label here.</p>

                <p>I also checked {afree} journals that DOAJ says are really free.</p>

                <p>{ctrlok} of them got the diamond label. So the label almost never misses a truly free journal.</p>

                <p>It just lets in a lot of journals that should not be there.</p>

                <h2>This Breaks A Nice Story</h2>

                <p>If you trust the label, it says something lovely. It says the countries with the least money publish the most in journals that charge nothing.</p>

                <p>Indonesia comes first, at {iddia} per cent. Germany is at {dedia} per cent. That is {idover} times as much.</p>

                <p>But look at what I found. Of the {idrch} paying journals in my sample that price in Indonesian rupiah, {idrw} carry the diamond label.</p>

                <p>So the map might be showing which countries use dollars. Not which countries charge.</p>

                <p>I am not saying the nice story is false. I am saying this data cannot tell you.</p>

                <h2>There Is A Better Question To Ask</h2>

                <p>DOAJ does not guess. It asks.</p>

                <p>It says {djfree} of {djn} journals charge the writer nothing. That is {djfreepct} per cent.</p>

                <p>That number came from asking. It is the one I would use.</p>

                <h2>Three Things I Cannot Tell You</h2>

                <p>This is {an2} journals, not all of them. OpenAlex only lets you ask about a thousand things a day without an account, and each journal costs two questions. I stopped when the day ran out.</p>

                <p>DOAJ can be wrong too. It writes down what a journal told it, and journals change their prices. When the two disagree I trusted DOAJ, because DOAJ asked.</p>

                <p>And none of this is about whether a journal is good. Charging money does not make a journal bad. I only checked whether a box that says "free" is telling the truth.</p>

""".format(
        diaw=g("dia.works", "{:,}".format(F["diaw"])), year=F["year"],
        an=g("audit.n", F["an"]), an2=F["an"],
        lab=g("labelled.diamond", F["lab"]), wn=g("wrong.n", F["wn"]),
        labpct_f=F["labpct"],
        hardpct=g("hard.pct", F["hardpct"]), softpct=g("soft.pct", F["softpct"]),
        ratio=g("soft.over.hard", F["ratio"]),
        afree=g("control.free", F["afree"]), ctrlok=g("control.right", F["ctrlok"]),
        iddia=g("id.dia", F["iddia"]), dedia=g("de.dia", F["dedia"]),
        idover=g("id.over.de", F["idover"]),
        idrch=g("idr.charging", F["idrch"]), idrw=g("idr.wrong", F["idrw"]),
        djfree=g("doaj.free", "{:,}".format(F["djfree"])),
        djn=g("doaj.journals", "{:,}".format(F["djn"])),
        djfreepct=g("doaj.free.pct", F["djfreepct"]),
    )


if __name__ == "__main__":
    main()
