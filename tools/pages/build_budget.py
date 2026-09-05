#!/usr/bin/env python3
"""Regenerate projects/budget-analysis.html from data/ph-budget CSVs.

    .venv/bin/python tools/pages/build_budget.py

The page this replaces led with a P5.768T national budget, a 22.1%
budget-to-GDP ratio and P14.62T of debt. Central government expense is 16.88% of
GDP, not 22.1%. Fourteen of its twenty-seven chart arrays were perfectly
monotone.

Nothing here is a DBM figure. DBM publishes the enacted appropriations act but
not as a readable series, and dof.gov.ph returns 403 to scripts. So the page is
built on the two open, internationally comparable sources -- World Bank central
government and IMF general government -- with the perimeter named every time,
because they differ by four to five points of GDP and averaging them would be
wrong at every point.
"""
import csv
import json
import os
import re

D = "data/ph-budget"
PAGE = "projects/budget-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def js(x):
    return json.dumps(x)


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    ann = rows("ph_budget_annual")
    imf = rows("ph_budget_imf")
    asean = rows("ph_budget_asean")

    debt = [r for r in imf if r["metric"] == "gross_debt_pct_gdp"]
    debt_act = [r for r in debt if r["basis"] == "actual"]
    debt_proj = [r for r in debt if r["basis"] == "projection"]
    last_exp = [r for r in ann if f(r["expense_pct_gdp"])][-1]
    last_rev = [r for r in ann if f(r["revenue_ex_grants_pct_gdp"])][-1]
    last_int = [r for r in ann if f(r["interest_pct_of_expense"])][-1]
    ph_a = [r for r in asean if r["country"] == "Philippines"][0]

    F = dict(
        exp=f(last_exp["expense_pct_gdp"]), expyear=last_exp["year"],
        rev=f(last_rev["revenue_ex_grants_pct_gdp"]), revyear=last_rev["year"],
        tax=f(last_rev["tax_revenue_pct_gdp"]),
        bal=f(last_rev["net_lending_pct_gdp"]),
        interest=f(last_int["interest_pct_of_expense"]), intyear=last_int["year"],
        int22=f([r for r in ann if r["year"] == "2022"][0]["interest_pct_of_expense"]),
        intmin=min(f(r["interest_pct_of_expense"]) for r in ann
                   if f(r["interest_pct_of_expense"])),
        intmax=max(f(r["interest_pct_of_expense"]) for r in ann
                   if f(r["interest_pct_of_expense"])),
        expphp=round(f(last_exp["expense_php_derived"]) / 1e12, 2),
        revphp=round(f(last_rev["revenue_php_derived"]) / 1e12, 2),
        gdpphp=round(f([r for r in ann if f(r["gdp_current_php"])][-1]["gdp_current_php"]) / 1e12, 2),
        debt=f(debt_act[-1]["value_pct_gdp"]), debtyear=debt_act[-1]["year"],
        debt19=f([r for r in debt if r["year"] == "2019"][0]["value_pct_gdp"]),
        proj=f(debt_proj[0]["value_pct_gdp"]), projyear=debt_proj[0]["year"],
        peak=max(f(r["value_pct_gdp"]) for r in debt_act),
        arev=f(ph_a["revenue_pct_gdp"]), adebt=f(ph_a["gross_debt_pct_gdp"]),
        ayear=ph_a["year"], nasean=len(asean),
        arank=sum(1 for r in asean
                  if f(r["revenue_pct_gdp"]) >= f(ph_a["revenue_pct_gdp"])),
        idn=f([r for r in asean if r["country"] == "Indonesia"][0]["revenue_pct_gdp"]),
    )
    F["rise"] = round(F["debt"] - F["debt19"], 1)
    F["debtphp"] = round(F["debt"] * f([r for r in ann if r["year"] == F["debtyear"]][0]
                                       ["gdp_current_php"]) / 100 / 1e12, 2)
    F["peakyear"] = [r["year"] for r in debt_act
                     if f(r["value_pct_gdp"]) == F["peak"]][0]
    F["intmaxyear"] = [r["year"] for r in ann
                       if f(r["interest_pct_of_expense"]) == F["intmax"]][0]
    F["intminyear"] = [r["year"] for r in ann
                       if f(r["interest_pct_of_expense"]) == F["intmin"]][0]
    F["intyears"] = sum(1 for r in ann if f(r["interest_pct_of_expense"]))
    F["intrank"] = sum(1 for r in ann if f(r["interest_pct_of_expense"])
                       and f(r["interest_pct_of_expense"]) >= F["interest"])

    hero = '''                <h1>Philippine Public Finances, 1990&ndash;2025</h1>
                <p class="hero-description">
                    What the state collects, what it spends, and what it owes &mdash;
                    from the two sources that publish it in a form anyone can check.
                    Both the debt and the cost of carrying it are far below where they
                    sat in the 1990s. Both have also turned back upward, and the second
                    one moved faster than the first.
                </p>

                <div class="header-actions">
                    <a href="https://www.imf.org/external/datamapper/GGXWDG_NGDP@WEO/PHL" target="_blank" class="btn btn-primary">
                        IMF fiscal indicators
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="bud.debt.pct">{debt}%</div>
                        <div class="stat-label">Gross debt, % of GDP ({debtyear})</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="bud.interest.pct">{interest}%</div>
                        <div class="stat-label">Of spending, on interest</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="bud.tax.pct">{tax}%</div>
                        <div class="stat-label">Tax revenue, % of GDP</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="bud.balance.pct">{bal}%</div>
                        <div class="stat-label">Fiscal balance, % of GDP</div>
                    </div>
                </div>
'''.format(**F)

    tldr = '''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Almost every alarming Philippine fiscal number is smaller than it was in the 1990s. Debt is <span data-fact="bud.debt.pct">{debt}%</span> of GDP against <span data-fact="bud.debt.peak">{peak}%</span> in {peakyear}; interest takes <span data-fact="bud.interest.pct">{interest}%</span> of spending against <span data-fact="bud.interest.max">{intmax}%</span> in {intmaxyear}. What is worth watching is the direction, not the level.</p>
                    <ul class="tldr-list">
                        <li>Debt rose <span data-fact="bud.debt.rise">{rise}</span> points of GDP between 2019 and {debtyear}, from <span data-fact="bud.debt.2019">{debt19}%</span> to <span data-fact="bud.debt.pct">{debt}%</span> &mdash; the cost of the pandemic, borrowed.</li>
                        <li>Interest took <span data-fact="bud.interest.pct">{interest}%</span> of central government spending in {intyear}, up from <span data-fact="bud.interest.pct.2022">{int22}%</span> a year earlier and from the series low of <span data-fact="bud.interest.min">{intmin}%</span> in {intminyear}. It is still lower than in <span data-fact="bud.interest.rank">{intrank}</span> of the <span data-fact="bud.interest.years">{intyears}</span> years measured &mdash; the burden fell for three decades and has only just started rising again.</li>
                        <li>Tax collection is <span data-fact="bud.tax.pct">{tax}%</span> of GDP. The state's problem is not that it spends unusually much &mdash; expense is <span data-fact="bud.expense.pct">{exp}%</span> of GDP &mdash; but the gap between the two, at <span data-fact="bud.balance.pct">{bal}%</span>.</li>
                        <li>Against four ASEAN neighbours the Philippines ranks <span data-fact="bud.asean.rev.rank">{arank}</span> of <span data-fact="bud.asean.countries">{nasean}</span> for general government revenue at <span data-fact="bud.asean.rev">{arev}%</span> of GDP &mdash; well above Indonesia's <span data-fact="bud.asean.idn.rev">{idn}%</span>.</li>
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

    sec(1, "Revenue Against Spending",
        "Central government, as a share of GDP. Shares rather than pesos, because pesos "
        "from 1990 and pesos from 2024 are not the same thing and putting them on one "
        "axis makes every early year look like nothing happened.",
        "Central government revenue and expense, % of GDP", "fiscalChart",
        [("Expense", "{exp}% of GDP".format(**F), "bud.expense.pct",
          "In {y}. Not a high number internationally; the Philippine state is "
          "comparatively small.".format(y=F["expyear"])),
         ("Revenue", "{rev}% of GDP".format(**F), "bud.revenue.pct",
          "In {y}, excluding grants.".format(y=F["revyear"])),
         ("The gap", "{bal}%".format(**F), "bud.balance.pct",
          "Net lending. The deficit is not driven by unusual spending, it is driven by "
          "what is not collected.")])

    sec(2, "Debt, And Why The Level Is The Wrong Alarm",
        "General government gross debt. The IMF publishes forecasts in the same series "
        "as history, so projections are drawn separately &mdash; a dashed line is a "
        "guess, and it should look like one.",
        "General government gross debt, % of GDP", "debtChart",
        [("Now", "{debt}%".format(**F), "bud.debt.pct",
          "In {y}, up {r} points from {d19}% in 2019.".format(
              y=F["debtyear"], r=F["rise"], d19=F["debt19"])),
         ("The actual peak", "{peak}%".format(**F), "bud.debt.peak",
          "Reached in {py}. Debt was substantially higher two decades ago than it is "
          "now, which is missing from most commentary.".format(py=F["peakyear"])),
         ("Projected {projyear}".format(**F), "{proj}%".format(**F), "bud.debt.proj",
          "An IMF forecast, not a measurement. It is on the chart as a dashed line for "
          "that reason.")])

    sec(3, "The Cost Of Carrying It",
        "Interest as a share of what the central government spends &mdash; not of GDP, "
        "of the budget. This is money committed before a peso reaches a classroom or a "
        "clinic. The shape of this chart is the opposite of what the headlines suggest, "
        "and an earlier draft of this page got it backwards until the chart was "
        "rendered and looked at.",
        "Interest payments as a share of central government expense, %", "interestChart",
        [("1990", "{intmax}%".format(**F), "bud.interest.max",
          "Two pesos in five went on interest. That is the real high in this series, "
          "and it is at the beginning of it."),
         ("Series low", "{intmin}%".format(**F), "bud.interest.min",
          "In {y}. Three decades of falling burden, helped by lower rates and a "
          "growing economy.".format(y=F["intminyear"])),
         ("Latest", "{interest}%".format(**F), "bud.interest.pct",
          "In {y}, up from {i22}% the year before. Still lower than in {rk} of the {n} "
          "years measured &mdash; so this is a reversal to watch, not a record to "
          "panic about.".format(y=F["intyear"], i22=F["int22"], rk=F["intrank"],
                                n=F["intyears"]))])

    sec(4, "Against The Neighbours",
        "Four ASEAN economies at {y}, on general government figures so the perimeter "
        "matches. Singapore is absent because the IMF publishes no revenue series for "
        "it, and a comparison that quietly drops a country reads as one that never "
        "included it.".format(y=F["ayear"]),
        "General government revenue and gross debt, % of GDP", "aseanChart",
        [("Revenue rank", "{arank} of {nasean}".format(**F), "bud.asean.rev.rank",
          "At {r}% of GDP. The Philippines collects more, relative to its economy, "
          "than most of this group.".format(r=F["arev"])),
         ("Debt", "{adebt}%".format(**F), "bud.asean.debt",
          "Mid-table. Malaysia and Thailand both carry more."),
         ("Indonesia", "{idn}%".format(**F), "bud.asean.idn.rev",
          "Revenue as a share of GDP &mdash; the lowest here, and a reminder that "
          "\"collects too little\" is relative to who you stand next to.")])

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">05</div>
                    <h2>Two Governments, Two Sets Of Numbers</h2>
                    <p class="section-description">
                        Fiscal figures for the same country routinely disagree, and it is
                        usually not an error. It is a question of what counts as
                        "government".
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Central government</h4>
                        <p>The World Bank series. National agencies only. Revenue of
                        <span data-fact="bud.revenue.pct">{rev}%</span> of GDP in
                        {revyear}.</p>
                    </div>
                    <div class="insight-card">
                        <h4>General government</h4>
                        <p>The IMF series. Adds local governments and social security.
                        Revenue of <span data-fact="bud.asean.rev">{arev}%</span> of GDP
                        for the same country in {ayear} &mdash; four and a half points
                        higher, because it is counting more things.</p>
                    </div>
                    <div class="insight-card">
                        <h4>So they are never mixed</h4>
                        <p>Both appear on this page, each labelled. Averaging them, or
                        quoting one and comparing it against the other, produces a number
                        that is wrong at every point. A check exists specifically to fire
                        if the two ever converge, so that someone looks at why.</p>
                    </div>
                </div>
            </div>
        </section>
'''.format(rev=F["rev"], revyear=F["revyear"], arev=F["arev"], ayear=F["ayear"]))

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-number" style="display:none"></div>
                <div class="section-header fade-up">
                    <div class="section-number">06</div>
                    <h2>What This Page Does Not Cover</h2>
                    <p class="section-description">
                        The version this replaces charted the budget by department, by
                        region, education and health allocations, infrastructure spending,
                        the unprogrammed appropriations, debt service by creditor, and
                        budget utilisation rates. All of those live in DBM and BTr
                        publications. None are in a form a script can read.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Anything by department or region</h4>
                        <p>The General Appropriations Act carries it, as a PDF per year
                        running to thousands of pages. Extracting it is a real project;
                        approximating it is what produced the page this replaces.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Debt by creditor and maturity</h4>
                        <p>The Bureau of the Treasury publishes this monthly in
                        spreadsheets that are not served through any stable endpoint.
                        dof.gov.ph returns 403 to scripts entirely.</p>
                    </div>
                    <div class="insight-card">
                        <h4>The enacted budget total</h4>
                        <p>The widely-quoted "P5.768 trillion budget" is an appropriation,
                        not an outturn &mdash; what was authorised, not what was spent.
                        This page reports outturns, so it does not carry that figure at
                        all. The peso amounts it does show are derived from shares of GDP
                        and labelled as derived.</p>
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
                    <p class="section-description">One fetcher, four CSVs, both APIs keyless.</p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Sources</h4>
                        <p>World Bank WDI for central government revenue, expense, tax and
                        interest; IMF DataMapper for general government debt, balance,
                        revenue and expenditure. Both open, both without a key.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Forecasts are separated</h4>
                        <p>The IMF returns projections in the same array as history &mdash;
                        the debt series runs to 2031. Every row is flagged actual or
                        projection, and a check asserts the boundary is a single clean
                        break, because a new forecast vintage moves it.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Peso figures are derived</h4>
                        <p>A share of GDP times GDP in current pesos, computed from the
                        rounded share this CSV publishes so the column can be recomputed
                        from the columns beside it. A check does exactly that
                        recomputation on every row.</p>
                    </div>
                    <div class="insight-card">
                        <h4>One request, not five</h4>
                        <p>The DataMapper ignores the country segments of its URL and
                        returns every country regardless. Asking per country is the same
                        payload five times and gets the client rate-limited with a 403
                        partway through &mdash; which looks exactly like a missing
                        indicator. It is fetched once and filtered locally.</p>
                    </div>
                    <div class="insight-card">
                        <h4>A check that was removed</h4>
                        <p>An earlier check reconciled the fiscal balance against revenue
                        minus expense. Those two World Bank series use different
                        definitions &mdash; net lending includes grants, the revenue
                        series excludes them &mdash; so it fired on twenty-one of
                        thirty-five perfectly good rows. A check that cries wolf gets
                        switched off, which is worse than no check, so it was replaced
                        with a plausibility band.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Verification</h4>
                        <p>Eleven assertions in <code>checks.sql</code>: perimeter and
                        source on every row, the actual/projection boundary, tax never
                        exceeding total revenue, nominal GDP never falling, one comparison
                        year across all five countries, and the derived peso columns
                        recomputed exactly.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">08</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>Gross debt is <span data-fact="bud.debt.pct">{debt}%</span> of
                        GDP in {debtyear}, up
                        <span data-fact="bud.debt.rise">{rise}</span> points from
                        <span data-fact="bud.debt.2019">{debt19}%</span> in 2019 &mdash;
                        but below the <span data-fact="bud.debt.peak">{peak}%</span> of
                        {peakyear}. The level is not unprecedented.</li>
                        <li>Neither is the cost of carrying it. Interest took
                        <span data-fact="bud.interest.pct">{interest}%</span> of central
                        government spending in {intyear} against
                        <span data-fact="bud.interest.max">{intmax}%</span> in
                        {intmaxyear} &mdash; lower than in
                        <span data-fact="bud.interest.rank">{intrank}</span> of
                        <span data-fact="bud.interest.years">{intyears}</span> years. It
                        has risen from the {intminyear} low of
                        <span data-fact="bud.interest.min">{intmin}%</span>, and the
                        direction is the story rather than the level.</li>
                        <li>The state is small, not extravagant: expense of
                        <span data-fact="bud.expense.pct">{exp}%</span> of GDP against
                        revenue of <span data-fact="bud.revenue.pct">{rev}%</span> and tax
                        of <span data-fact="bud.tax.pct">{tax}%</span>. The deficit at
                        <span data-fact="bud.balance.pct">{bal}%</span> is a collection
                        story more than a spending one.</li>
                        <li>Regionally the Philippines is
                        <span data-fact="bud.asean.rev.rank">{arank}</span> of
                        <span data-fact="bud.asean.countries">{nasean}</span> for general
                        government revenue at
                        <span data-fact="bud.asean.rev">{arev}%</span>, ahead of
                        Indonesia's <span data-fact="bud.asean.idn.rev">{idn}%</span>.</li>
                        <li>Derived peso figures &mdash; expense of
                        <span data-fact="bud.expense.php">{expphp}</span> trillion and debt
                        of <span data-fact="bud.debt.php">{debtphp}</span> trillion &mdash;
                        are shares of GDP multiplied by GDP, not DBM or BTr publications.
                        The page never presents them as the enacted budget.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**F))

    # ---------------------------------------------------------------- charts
    charts = []
    yrs = [r["year"] for r in ann]
    charts.append('''        // 01 revenue and expense, central government
        new Chart(document.getElementById('fiscalChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Expense (%% of GDP)', data: %s, borderColor: '#ef4444',
                      backgroundColor: 'rgba(239,68,68,0.12)', borderWidth: 2,
                      pointRadius: 0, fill: true, spanGaps: false },
                    { label: 'Revenue excl. grants (%% of GDP)', data: %s,
                      borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,0.12)',
                      borderWidth: 2, pointRadius: 0, fill: true, spanGaps: false },
                    { label: 'Tax revenue (%% of GDP)', data: %s, borderColor: '#3b82f6',
                      borderWidth: 2, borderDash: [4, 3], pointRadius: 0, fill: false,
                      spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { ticks: { maxTicksLimit: 12 } },
                          y: { title: { display: true, text: '%% of GDP' } } }
            }
        });''' % (js(yrs),
                  js([f(r["expense_pct_gdp"]) for r in ann]),
                  js([f(r["revenue_ex_grants_pct_gdp"]) for r in ann]),
                  js([f(r["tax_revenue_pct_gdp"]) for r in ann])))

    dyrs = [r["year"] for r in debt]
    charts.append('''        // 02 debt. Actuals solid, projections dashed and in their own series --
        //    the IMF ships both in one array and a single line would present a
        //    forecast as a measurement.
        new Chart(document.getElementById('debtChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Gross debt, actual (%% of GDP)', data: %s,
                      borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.15)',
                      borderWidth: 2, pointRadius: 0, fill: true, spanGaps: false },
                    { label: 'IMF projection', data: %s, borderColor: '#a0a0b0',
                      borderDash: [6, 4], borderWidth: 2, pointRadius: 0, fill: false,
                      spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { ticks: { maxTicksLimit: 12 } },
                          y: { title: { display: true, text: '%% of GDP' } } }
            }
        });''' % (js(dyrs),
                  js([f(r["value_pct_gdp"]) if r["basis"] == "actual" else None
                      for r in debt]),
                  # the last actual is repeated so the dashed line joins the solid
                  # one instead of starting in mid-air
                  js([f(r["value_pct_gdp"]) if (r["basis"] == "projection"
                                                or r["year"] == debt_act[-1]["year"])
                      else None for r in debt])))

    iyrs = [r["year"] for r in ann if f(r["interest_pct_of_expense"])]
    charts.append('''        // 03 interest as a share of expense
        new Chart(document.getElementById('interestChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Interest, %% of expense', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { ticks: { maxTicksLimit: 12 } },
                          y: { title: { display: true, text: '%% of central govt expense' } } }
            }
        });''' % (js(iyrs),
                  js([f(r["interest_pct_of_expense"]) for r in ann
                      if f(r["interest_pct_of_expense"])]),
                  js(["#ef4444" if r["year"] == last_int["year"] else "#f59e0b"
                      for r in ann if f(r["interest_pct_of_expense"])])))

    charts.append('''        // 04 ASEAN, revenue against debt
        new Chart(document.getElementById('aseanChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Revenue (%% of GDP)', data: %s, backgroundColor: '#22c55e' },
                    { label: 'Gross debt (%% of GDP)', data: %s, backgroundColor: '#8b5cf6' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { y: { title: { display: true, text: '%% of GDP' } } }
            }
        });''' % (js([r["country"] for r in asean]),
                  js([f(r["revenue_pct_gdp"]) for r in asean]),
                  js([f(r["gross_debt_pct_gdp"]) for r in asean])))

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

    desc = ("Philippine public finances from the World Bank and IMF: debt at {d}% of "
            "GDP against {p}% in {py}, and interest taking {i}% of central government "
            "spending against {im}% in {imy}.").format(
                d=F["debt"], p=F["peak"], py=F["peakyear"], i=F["interest"],
                im=F["intmax"], imy=F["intmaxyear"])
    short = ("Debt and its cost are both far below their 1990s levels -- and both have "
             "turned back up.")

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, rep, src, count=1)
        if not n:
            raise SystemExit("head patch failed (%s)" % why)

    swap(r"<title>[^<]*</title>",
         "<title>Philippine Public Finances 1990-2025 | Allan Niñal - Data Analyst Portfolio</title>",
         "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % desc, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="Philippine Public Finances 1990-2025 | Allan Niñal">',
         "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % short, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="Philippine Public Finances 1990-2025">',
         "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % short, "tw:desc")
    swap(r'"headline": "[^"]*"',
         '"headline": "Philippine Public Finances: Smaller Than The 1990s, And Turning Back Up"',
         "headline")
    swap(r'"description": "[^"]*"', '"description": %s' % json.dumps(desc), "ld desc")

    faq = {
        "How much debt does the Philippines have?":
            "General government gross debt was {d}% of GDP in {y}, up {r} points from "
            "{d19}% in 2019. That is high but not unprecedented -- it reached {pk}% in "
            "{pky}. Multiplied by GDP in current pesos it works out to about P{php} "
            "trillion, a derived figure rather than a Treasury publication.".format(
                d=F["debt"], y=F["debtyear"], r=F["rise"], d19=F["debt19"],
                pk=F["peak"], pky=F["peakyear"], php=F["debtphp"]),
        "How much of the Philippine budget goes to interest payments?":
            "{i}% of central government expense in {y}, up from {i22}% the year before "
            "and from a series low of {lo}% in {ly}. It is not a record: interest took "
            "{hi}% in {hy}, and the current figure is lower than in {rk} of the {n} years "
            "measured. The burden fell for three decades and has recently turned back "
            "up.".format(i=F["interest"], y=F["intyear"], i22=F["int22"], lo=F["intmin"],
                         ly=F["intminyear"], hi=F["intmax"], hy=F["intmaxyear"],
                         rk=F["intrank"], n=F["intyears"]),
        "Does the Philippine government spend too much or collect too little?":
            "Collect too little, on these numbers. Central government expense is {e}% of "
            "GDP -- not high internationally -- against revenue of {r}% and tax of {t}%. "
            "The deficit of {b}% of GDP is the gap between them.".format(
                e=F["exp"], r=F["rev"], t=F["tax"], b=F["bal"]),
        "Why do Philippine fiscal figures differ between sources?":
            "Because 'government' means different things. The World Bank series here "
            "covers central government; the IMF series covers general government, which "
            "adds local governments and social security. For {y} they report {c}% and "
            "{g}% of GDP in revenue for the same country. Both are correct. This page "
            "labels the perimeter every time and never averages them.".format(
                y=F["ayear"], c=F["rev"], g=F["arev"]),
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
