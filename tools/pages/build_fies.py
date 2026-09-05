#!/usr/bin/env python3
"""Regenerate projects/fies-analysis.html from data/ph-fies CSVs.

    .venv/bin/python tools/pages/build_fies.py

This page is the exception in the rebuild. Its four headline figures -- 41,544
households, P247,556 mean income, P164,080 median, a 0.444 Gini -- all turn out
to be correct: recomputing them from the microdata gives 41,544, 247,556,
164,080 and 0.4438. Somebody had read them off the dataset description. The
charts were still invented, and nothing had ever opened the file.

The file opens fine. PSA is unreachable, but the public FIES extract is mirrored
on Kaggle and served without authentication -- the page already cited that
mirror. Sixty columns and 41,544 rows, which is enough for the analysis the page
had been claiming to do.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-fies"
PAGE = "projects/fies-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def peso(v):
    return "P{:,.0f}".format(v)


def main():
    head = {x["metric"]: f(x["value"]) for x in rows("ph_fies_headline")}
    ineq = {x["metric"]: f(x["value"]) for x in rows("ph_fies_inequality")}
    dec = rows("ph_fies_deciles")
    food = rows("ph_fies_food_share")
    spend = rows("ph_fies_spending")
    reg = rows("ph_fies_regions")
    sex = rows("ph_fies_head_sex")

    d1 = [x for x in dec if x["decile"] == "1"][0]
    d10 = [x for x in dec if x["decile"] == "10"][0]
    f1 = [x for x in food if x["decile"] == "1"][0]
    f10 = [x for x in food if x["decile"] == "10"][0]
    regs = sorted(reg, key=lambda x: -f(x["median_income"]))
    fem = [x for x in sex if x["head_sex"] == "Female"][0]
    male = [x for x in sex if x["head_sex"] == "Male"][0]

    F = dict(
        n=int(head["households"]),
        median=head["median_income"], mean=head["mean_income"],
        p10=head["p10_income"], p90=head["p90_income"], mx=head["max_income"],
        members=head["median_household_size"], foodmed=head["median_food_spend"],
        gini=ineq["gini"], top1=ineq["top_1pct_income_share"],
        agri=ineq["median_income_agricultural"],
        nonagri=ineq["median_income_non_agricultural"],
        d1s=f(d1["income_share_pct"]), d10s=f(d10["income_share_pct"]),
        d1m=f(d1["median_income"]), d10m=f(d10["median_income"]),
        fd1=f(f1["median_food_share_pct"]), fd10=f(f10["median_food_share_pct"]),
        rtop=regs[0]["region"].strip(), rtopv=f(regs[0]["median_income"]),
        rbot=regs[-1]["region"].strip(), rbotv=f(regs[-1]["median_income"]),
        nreg=len(reg),
        femv=f(fem["median_income"]), malev=f(male["median_income"]),
        femn=int(fem["households"]),
    )
    F["skew"] = r(F["mean"] / F["median"], 2)
    F["ratio9010"] = r(F["p90"] / F["p10"], 1)
    F["decratio"] = r(F["d10m"] / F["d1m"], 1)
    F["foodspread"] = r(F["fd1"] - F["fd10"], 2)
    F["agriratio"] = r(F["nonagri"] / F["agri"], 2)
    F["regratio"] = r(F["rtopv"] / F["rbotv"], 2)

    p = Page(PAGE)
    p.hero('''                <h1>What 41,544 Households Actually Spend</h1>
                <p class="hero-description">
                    The 2015 Family Income and Expenditure Survey, opened. The median
                    household earned {medianp} that year and the mean earned
                    {meanp} &mdash; and the poorest tenth spent
                    {fd1}% of income on food against {fd10}% for the richest.
                </p>

                <div class="header-actions">
                    <a href="https://www.kaggle.com/datasets/grosvenpaul/family-income-and-expenditure" target="_blank" class="btn btn-primary">
                        FIES 2015 public microdata
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="fies.households">{n:,}</div>
                        <div class="stat-label">Households in the sample</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="fies.median">{medianp}</div>
                        <div class="stat-label">Median annual income</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="fies.gini">{gini}</div>
                        <div class="stat-label">Gini, from these records</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="fies.food.spread">{foodspread}</div>
                        <div class="stat-label">Point spread in food share, poorest to richest</div>
                    </div>
                </div>
'''.format(wrapcls=p.t["wrap"], medianp=peso(F["median"]), meanp=peso(F["mean"]), **F))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Engel&rsquo;s law says the share of income spent on food falls as income rises. It holds here across all ten deciles without a single break &mdash; from <span data-fact="fies.food.d1">{fd1}%</span> down to <span data-fact="fies.food.d10">{fd10}%</span>.</p>
                    <ul class="tldr-list">
                        <li>Median household income was <span data-fact="fies.median">{medianp}</span> against a mean of <span data-fact="fies.mean">{meanp}</span> &mdash; the mean is <span data-fact="fies.skew">{skew}</span> times the median, which is what a long right tail does to an average.</li>
                        <li>The richest tenth took <span data-fact="fies.d10.share">{d10s}%</span> of all income in the sample against <span data-fact="fies.d1.share">{d1s}%</span> for the poorest tenth. The top 1% alone took <span data-fact="fies.top1">{top1}%</span>.</li>
                        <li>Agricultural households had a median income of <span data-fact="fies.agri.median">{agrip}</span> against <span data-fact="fies.nonagri.median">{nonagrip}</span> for the rest &mdash; a factor of <span data-fact="fies.agri.ratio">{agriratio}</span>.</li>
                        <li>These are <span data-fact="fies.households">{n:,}</span> unweighted household records. FIES ships sampling weights so results can be grossed up to the population; this public extract does not include them, so every figure describes the sample and not the country.</li>
                    </ul>
'''.format(wrapcls=p.t["wrap"], medianp=peso(F["median"]), meanp=peso(F["mean"]),
           agrip=peso(F["agri"]), nonagrip=peso(F["nonagri"]), **F))

    S = [
        p.section(1, "The Shape Of Household Income",
                  "Median, mean and the tails. The gap between the first two is the "
                  "reason every other figure on this page is a median.",
                  [("Median", peso(F["median"]), "fies.median",
                    "Annual household income, 2015 pesos."),
                   ("Mean", peso(F["mean"]), "fies.mean",
                    "{s} times the median. The highest single household in the sample "
                    "reported {m}.".format(s=F["skew"], m=peso(F["mx"]))),
                   ("90th over 10th", "{r}&times;".format(r=F["ratio9010"]),
                    "fies.p90p10",
                    "{a} against {b}. A household at the 90th percentile earned seven "
                    "times one at the 10th.".format(a=peso(F["p90"]), b=peso(F["p10"])))],
                  "Median income by income decile, PHP", "decileChart"),
        p.section(2, "Engel's Law, Without Exception",
                  "The oldest empirical regularity in economics: as income rises, the "
                  "share spent on food falls. Across all ten deciles here it falls "
                  "monotonically &mdash; a check asserts it, because a break would mean "
                  "the decile assignment or the ratio is wrong.",
                  [("Poorest tenth", "{v}%".format(v=F["fd1"]), "fies.food.d1",
                    "Of income spent on food, at the median of that decile."),
                   ("Richest tenth", "{v}%".format(v=F["fd10"]), "fies.food.d10",
                    "The same measure, at the other end."),
                   ("Spread", "{v} pts".format(v=F["foodspread"]), "fies.food.spread",
                    "Median food spending across the whole sample was "
                    "{f}.".format(f=peso(F["foodmed"])))],
                  "Median food share of income by decile, %", "engelChart"),
        p.section(3, "Who Holds The Income",
                  "Share of all income in the sample, by decile. The bars are the same "
                  "ten groups as the chart above, counted a different way.",
                  [("Richest tenth", "{v}%".format(v=F["d10s"]), "fies.d10.share",
                    "Of all income in the sample."),
                   ("Poorest tenth", "{v}%".format(v=F["d1s"]), "fies.d1.share",
                    "A ratio of {r} to one on median income.".format(r=F["decratio"])),
                   ("Gini", "{v}".format(v=F["gini"]), "fies.gini",
                    "Computed from these {n:,} records rather than quoted, so it and "
                    "the decile table come from the same rows.".format(n=F["n"]))],
                  "Share of total sample income by decile, %", "shareChart"),
        p.section(4, "What The Money Buys",
                  "Median spending by category for the poorest and richest deciles. The "
                  "categories are named individually because the file also carries "
                  "subtotals, and summing those alongside their components "
                  "double-counts.",
                  [("Median food spend", peso(F["foodmed"]), "fies.food.median",
                    "Across the whole sample."),
                   ("Agricultural households", peso(F["agri"]), "fies.agri.median",
                    "Median income, against {v} for non-agricultural &mdash; a factor "
                    "of {r}.".format(v=peso(F["nonagri"]), r=F["agriratio"])),
                   ("Top 1% share", "{v}%".format(v=F["top1"]), "fies.top1",
                    "Of all income in the sample, held by 415 households.")],
                  "Median spending by category, poorest and richest decile, PHP",
                  "spendChart"),
        p.section(5, "Where They Live",
                  "Median household income by region, all {n} of them. The spread is "
                  "wider than any single spending category on this "
                  "page.".format(n=F["nreg"]),
                  [(F["rtop"], peso(F["rtopv"]), "fies.region.top.income",
                    "Highest median household income."),
                   (F["rbot"], peso(F["rbotv"]), "fies.region.bottom.income",
                    "Lowest. A factor of {r} between the two.".format(r=F["regratio"])),
                   ("Female-headed households", peso(F["femv"]), "fies.female.median",
                    "Median income, against {m} for male-headed. Stated as an "
                    "observation rather than explained: the survey records who is named "
                    "as head, and the two groups differ in composition in ways this "
                    "data cannot separate.".format(m=peso(F["malev"])))],
                  "Median household income by region, PHP", "regionChart"),
        p.prose(6, "What This Page Does Not Cover",
                "The microdata is rich, and this page uses a fraction of its sixty "
                "columns. Three limits are worth stating rather than leaving to be "
                "discovered.",
                [("The sample is unweighted",
                  "FIES ships sampling weights so results can be grossed up to the "
                  "population. This public extract does not include them, so every "
                  "figure here describes the {n:,} sampled households and not the "
                  "Philippines. National totals are not computed and would be wrong if "
                  "they were.".format(n=F["n"])),
                 ("It is 2015",
                  "A decade old. Nominal peso figures from 2015 are not comparable with "
                  "today's, and nothing here is inflation-adjusted. Later FIES rounds "
                  "exist and sit behind PSA's managed challenge."),
                 ("Housing and assets are in the file, not on the page",
                  "Type of roof, walls, building, toilet facility and water source are "
                  "all columns here. They deserve their own treatment against the "
                  "national JMP series rather than a chart each, and are left for that "
                  "rather than added thinly.")]),
        p.prose(7, "Method",
                "One fetcher, seven CSVs, from the public mirror the page already cited.",
                [("PSA is unreachable; the mirror is not",
                  "psa.gov.ph sits behind a managed challenge that scripts do not pass. "
                  "The public FIES extract is mirrored on Kaggle and served without "
                  "authentication. The previous version of this page linked to that "
                  "mirror and never opened it."),
                 ("The microdata is not committed",
                  "22 MB, redistributable but not ours, and a checked-in copy would go "
                  "stale against the mirror without anyone noticing. The fetcher "
                  "downloads, aggregates and writes only the summaries."),
                 ("Medians, not means",
                  "Income is strongly right-skewed -- the mean is {s} times the median "
                  "and the largest single household reported {m}. Medians are used "
                  "throughout and the mean appears only where the gap is the "
                  "point.".format(s=F["skew"], m=peso(F["mx"]))),
                 ("Subtotals are excluded by name",
                  "The file carries Total Food Expenditure alongside its components. "
                  "Every spending category is named explicitly so a subtotal cannot be "
                  "summed with the parts it contains."),
                 ("Engel's law is asserted",
                  "A check fails if the food share stops falling monotonically across "
                  "deciles. It holds essentially without exception in household budget "
                  "data, so a break would indicate a fault here rather than a finding."),
                 ("Four figures that were already right",
                  "41,544 households, {mean} mean, {med} median and a 0.444 Gini were "
                  "all on the previous version of this page and all check out against "
                  "the microdata. The charts did not.".format(
                      mean=peso(F["mean"]), med=peso(F["median"])))]),
    ]

    S.append('''        <section class="{wrapcls}">
            <div class="container">
                <div class="section-header fade-up">
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>Engel's law holds across all ten deciles without a break:
                        food takes <span data-fact="fies.food.d1">{fd1}%</span> of income
                        at the bottom and
                        <span data-fact="fies.food.d10">{fd10}%</span> at the top, a
                        <span data-fact="fies.food.spread">{foodspread}</span>-point
                        spread.</li>
                        <li>Median household income was
                        <span data-fact="fies.median">{medianp}</span> against a mean of
                        <span data-fact="fies.mean">{meanp}</span> &mdash;
                        <span data-fact="fies.skew">{skew}</span> times higher, the
                        signature of a long right tail.</li>
                        <li>The richest tenth held
                        <span data-fact="fies.d10.share">{d10s}%</span> of sample income
                        against <span data-fact="fies.d1.share">{d1s}%</span> for the
                        poorest, giving a Gini of
                        <span data-fact="fies.gini">{gini}</span> computed from these
                        records.</li>
                        <li>Agricultural households earned
                        <span data-fact="fies.agri.median">{agrip}</span> at the median
                        against <span data-fact="fies.nonagri.median">{nonagrip}</span>
                        for everyone else, and
                        <span data-fact="fies.region.top">{rtop}</span> earned
                        <span data-fact="fies.region.ratio">{regratio}</span> times
                        <span data-fact="fies.region.bottom">{rbot}</span>.</li>
                        <li>All of it describes
                        <span data-fact="fies.households">{n:,}</span> unweighted
                        sampled households in 2015, not the country and not today.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(wrapcls=p.t["wrap"], medianp=peso(F["median"]), meanp=peso(F["mean"]),
           agrip=peso(F["agri"]), nonagrip=peso(F["nonagri"]), **F))

    charts = ['''        // 01 median income by decile. Log y: the tenth decile's median is twelve
        //    times the first, and a linear axis flattens the bottom half.
        new Chart(document.getElementById('decileChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Median income (PHP)', data: %s, backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'Income decile' } },
                          y: { type: 'logarithmic',
                               title: { display: true, text: 'PHP per year (log)' } } }
            }
        });''' % (js(["D%s" % x["decile"] for x in dec]),
                  js([f(x["median_income"]) for x in dec]),
                  js(["#22c55e" if x["decile"] == "1" else "#ef4444"
                      if x["decile"] == "10" else "#3b82f6" for x in dec])),
              '''        // 02 Engel curve. Falls at every step; the check asserts it.
        new Chart(document.getElementById('engelChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [{ label: 'Median food share of income (%%)', data: %s,
                             borderColor: '#f59e0b',
                             backgroundColor: 'rgba(245,158,11,0.18)',
                             borderWidth: 3, pointRadius: 4, fill: true }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'Income decile' } },
                          y: { min: 0, max: 70,
                               title: { display: true, text: '%% of income spent on food' } } }
            }
        });''' % (js(["D%s" % x["decile"] for x in food]),
                  js([f(x["median_food_share_pct"]) for x in food])),
              '''        // 03 income share by decile. The flat line is what perfect equality
        //    would look like -- 10%% each -- and the gap to it is the Gini.
        new Chart(document.getElementById('shareChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Share of total income (%%)', data: %s, backgroundColor: '#8b5cf6' },
                    { label: 'Equal shares (10%%)', data: %s, type: 'line',
                      borderColor: '#22c55e', borderDash: [6, 4], pointRadius: 0, fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { title: { display: true, text: 'Income decile' } },
                          y: { title: { display: true, text: '%% of all sample income' } } }
            }
        });''' % (js(["D%s" % x["decile"] for x in dec]),
                  js([f(x["income_share_pct"]) for x in dec]), js([10] * len(dec))),
              '''        // 04 spending mix. Log x again: restaurant spending in the top decile is
        //    two orders of magnitude above tobacco in the bottom one.
        new Chart(document.getElementById('spendChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Poorest decile (PHP)', data: %s, backgroundColor: '#22c55e' },
                    { label: 'Richest decile (PHP)', data: %s, backgroundColor: '#ef4444' }
                ]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { type: 'logarithmic',
                               title: { display: true, text: 'Median PHP per year (log)' } } }
            }
        });''' % (js([x["category"] for x in spend]),
                  js([max(f(x["median_poorest_decile"]), 1) for x in spend]),
                  js([max(f(x["median_richest_decile"]), 1) for x in spend])),
              '''        // 05 by region
        new Chart(document.getElementById('regionChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Median household income (PHP)', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: 'PHP per year' } } }
            }
        });''' % (js([x["region"].strip() for x in regs]),
                  js([f(x["median_income"]) for x in regs]),
                  js(["#ef4444" if i == 0 else "#22c55e" if i == len(regs) - 1
                      else "#3b82f6" for i in range(len(regs))]))]

    p.sections(S)
    p.charts(charts)
    p.head("What 41,544 Households Actually Spend",
           "The 2015 Philippine FIES microdata, opened: median income %s against a %s "
           "mean, a %s Gini computed from the records, and Engel's law holding across "
           "all ten deciles." % (peso(F["median"]), peso(F["mean"]), F["gini"]),
           "Food takes %s%% of income at the bottom and %s%% at the top."
           % (F["fd1"], F["fd10"]),
           "Philippine FIES 2015: What 41,544 Households Actually Spend")
    p.faq({
        "What is the average Philippine household income?":
            "In the 2015 FIES sample the median household earned %s a year and the mean "
            "earned %s -- the mean is %s times the median because income is strongly "
            "right-skewed, with the largest single household reporting %s. The median is "
            "the more useful figure and is what this page uses throughout. These are "
            "unweighted sample records, not national estimates."
            % (peso(F["median"]), peso(F["mean"]), F["skew"], peso(F["mx"])),
        "How much of their income do Filipino families spend on food?":
            "It depends sharply on income. The poorest tenth of households spent %s%% of "
            "income on food; the richest tenth spent %s%%. The share falls at every one "
            "of the ten steps between -- Engel's law, holding without a single exception "
            "in this data." % (F["fd1"], F["fd10"]),
        "How unequal is Philippine household income?":
            "The Gini computed from these %s records is %s. The richest tenth held %s%% "
            "of all income in the sample and the poorest tenth %s%%, while the top 1%% "
            "alone held %s%%. A household at the 90th percentile earned %s times one at "
            "the 10th." % (format(F["n"], ","), F["gini"], F["d10s"], F["d1s"],
                           F["top1"], F["ratio9010"]),
        "Where does Philippine FIES data come from?":
            "PSA runs the Family Income and Expenditure Survey. psa.gov.ph sits behind a "
            "managed challenge that automated requests do not pass, but the public "
            "microdata extract is mirrored on Kaggle and served without authentication. "
            "This analysis uses that mirror: 41,544 household records with 60 columns, "
            "for 2015. The records are unweighted, so they describe the sample rather "
            "than the country.",
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
