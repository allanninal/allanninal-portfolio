#!/usr/bin/env python3
"""Regenerate projects/ofw-analysis.html from data/ph-ofw CSVs.

    .venv/bin/python tools/pages/build_ofw.py

The page claimed 2.19M OFWs, 57.2% female, P262B remitted and P129K per worker.
None of it is fetchable: DMW publishes deployment statistics as annual PDF
compendiums and PSA's Survey on Overseas Filipinos sits behind the same managed
challenge as the rest of psa.gov.ph. Nothing had been opened.

So the page answers a narrower question it can actually answer -- what migration
sends home, rather than who migrates -- and section 05 says what that costs.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, section, prose_section          # noqa: E402

D = "data/ph-ofw"
PAGE = "projects/ofw-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    ann = rows("ph_ofw_annual")
    peers = rows("ph_ofw_peers")
    have = [r for r in ann if f(r["remittances_usd"]) is not None]
    last, first = have[-1], have[0]
    ph = [r for r in peers if r["country"] == "Philippines"][0]
    pk = max(ann, key=lambda r: f(r["remittances_pct_gdp"]) or -1)

    F = dict(
        remit=round(f(last["remittances_usd"]) / 1e9, 2), year=last["year"],
        pct=round(f(last["remittances_pct_gdp"]), 2),
        pctpk=round(f(pk["remittances_pct_gdp"]), 2), pkyear=pk["year"],
        remit77=round(f(first["remittances_usd"]) / 1e6, 1), firstyear=first["year"],
        fdi=round(f(last["remittances_over_fdi"]), 2),
        exp=round(100.0 * f(last["remittances_usd"])
                  / f(last["exports_goods_services_usd"]), 1),
        netmig=abs(int(f(last["net_migration"]))),
        pyear=peers[0]["year"], pn=len(peers),
        prank=sum(1 for r in peers
                  if f(r["remittances_pct_gdp"]) >= f(ph["remittances_pct_gdp"])),
        india=round(f([r for r in peers if r["country"] == "India"][0]["remittances_usd"])
                    / 1e9, 1),
        indiapct=f([r for r in peers if r["country"] == "India"][0]["remittances_pct_gdp"]),
        nyears=len(have),
    )
    decade = [r for r in ann if f(r["net_migration"]) is not None
              and int(r["year"]) > int(last["year"]) - 10]
    F["decade"] = abs(int(sum(f(r["net_migration"]) for r in decade)))
    F["mult"] = round(f(last["remittances_usd"]) / f(first["remittances_usd"]))

    p = Page(PAGE)
    p.hero('''                <h1>What Migration Sends Home</h1>
                <p class="hero-description">
                    Overseas Filipinos sent back ${remit} billion in {year} &mdash;
                    {fdi} times what the country received in net foreign direct
                    investment, and equal to {exp}% of everything it exported. This page
                    is about the money, because the money is what is publicly countable.
                </p>

                <div class="header-actions">
                    <a href="https://data.worldbank.org/indicator/BX.TRF.PWKR.CD.DT?locations=PH" target="_blank" class="btn btn-primary">
                        World Bank remittance data
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="ofw.remit">${remit}B</div>
                        <div class="stat-label">Remittances received, {year}</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="ofw.pct">{pct}%</div>
                        <div class="stat-label">Of GDP</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="ofw.vs.fdi">{fdi}&times;</div>
                        <div class="stat-label">Net foreign direct investment</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="ofw.netmig">{netmig:,}</div>
                        <div class="stat-label">Net migration, {year}</div>
                    </div>
                </div>
'''.format(**F))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Remittances are not a supplement to the Philippine economy. At <span data-fact="ofw.vs.fdi">{fdi}</span> times net foreign direct investment, they are one of its main external inflows &mdash; and they have been shrinking as a share of it for twenty years.</p>
                    <ul class="tldr-list">
                        <li>${remit} billion arrived in {year}, worth <span data-fact="ofw.pct">{pct}%</span> of GDP. That share peaked at <span data-fact="ofw.pct.peak">{pctpk}%</span> in <span data-fact="ofw.pct.peak.year">{pkyear}</span> and has fallen since &mdash; not because remittances shrank, but because the economy grew faster.</li>
                        <li>They are equal to <span data-fact="ofw.vs.exports">{exp}%</span> of all goods and services the country exports. Nearly a third as much again on top of everything sold abroad.</li>
                        <li>The flow has grown <span data-fact="ofw.remit.1977">{remit77}</span> million dollars in {firstyear} to ${remit} billion now, across <span data-fact="ofw.years">{nyears}</span> years without a single sustained reversal &mdash; including through 2008 and 2020.</li>
                        <li>Against five other large remittance economies the Philippines ranks <span data-fact="ofw.peers.rank">{prank}</span> of <span data-fact="ofw.peers.n">{pn}</span> by share of GDP. India receives ${india} billion &mdash; four times as much money, worth <span data-fact="ofw.india.pct">{indiapct}%</span> of its economy.</li>
                    </ul>
'''.format(**F))

    S = [
        section(1, "Forty-Nine Years Of Growth",
                "Remittance inflows since {fy}. The striking property is not the level "
                "but the shape: it goes up through every crisis in the "
                "period.".format(fy=F["firstyear"]),
                [("{year} inflow".format(**F), "${remit}B".format(**F), "ofw.remit",
                  "Up from ${r}M in {fy}.".format(r=F["remit77"], fy=F["firstyear"])),
                 ("Growth multiple", "{mult}&times;".format(**F), None,
                  "In nominal dollars over {n} years. Not inflation-adjusted, and the "
                  "page does not claim it is.".format(n=F["nyears"])),
                 ("Through the crises", "no reversal", None,
                  "2008 and 2020 both dented FDI and exports. Neither produced a "
                  "sustained fall here &mdash; migrants send more when home needs more, "
                  "which is the opposite of how investment behaves.")],
                "Remittances received, US$ billions", "flowChart"),
        section(2, "Bigger Than Investment",
                "The comparison that says what remittances actually are in this economy. "
                "Foreign direct investment gets the policy attention; this gets the "
                "money.",
                [("Against net FDI", "{fdi}&times;".format(**F), "ofw.vs.fdi",
                  "In {year}. Remittances have exceeded net FDI in every year on "
                  "record.".format(year=F["year"])),
                 ("Against exports", "{exp}%".format(**F), "ofw.vs.exports",
                  "Of all goods and services exported. Almost a third as much again on "
                  "top of everything the country sells abroad."),
                 ("Share of GDP", "{pct}%".format(**F), "ofw.pct",
                  "Down from {p}% at the {py} peak &mdash; the economy grew faster than "
                  "the remittances did.".format(p=F["pctpk"], py=F["pkyear"]))],
                "Remittances, net FDI and exports, US$ billions", "compareChart"),
        section(3, "Against Other Remittance Economies",
                "Six large receivers at {y}, by share of GDP rather than by dollars. "
                "Dollars would just rank by country size and tell you "
                "nothing.".format(y=F["pyear"]),
                [("Rank by share", "{prank} of {pn}".format(**F), "ofw.peers.rank",
                  "At {p}% of GDP.".format(p=F["pct"])),
                 ("India, by dollars", "${india}B".format(**F), "ofw.india.usd",
                  "Four times the Philippine inflow in absolute terms."),
                 ("India, by share", "{indiapct}%".format(**F), "ofw.india.pct",
                  "And less than half the Philippine share of GDP. The same money means "
                  "very different things to different economies.")],
                "Remittances as a share of GDP, %", "peerChart"),
        prose_section(4, "The Number Nobody Publishes Openly",
                      "Every figure above is money. None is people, and that is not an "
                      "editorial choice.",
                      [("Net migration is an estimate",
                        "The World Bank derives it from five-year interpolations "
                        "between census rounds. Three years in the series come back "
                        "positive &mdash; 1998, 2010 and 2012 &mdash; not because "
                        "migration reversed but because the residual can flip. Those are "
                        "recorded rather than clipped to zero, because clipping would "
                        "hide how coarse the series is."),
                       ("The direction is not in doubt",
                        "Net outflow over the last decade of data comes to about "
                        "{d:,} people. The level is soft; the sign is "
                        "not.".format(d=F["decade"])),
                       ("But not who, or where, or doing what",
                        "Sex, age, occupation, destination and region of origin are all "
                        "published by DMW &mdash; in annual PDF compendiums, not as a "
                        "series. Nothing here can speak to them.")]),
        prose_section(5, "What This Page Does Not Cover",
                      "The version this replaces claimed 2.19M OFWs, 57.2% female, "
                      "P262B remitted and P129K per worker, plus charts of age, "
                      "occupation, destination country and region of origin.",
                      [("The headcount",
                        "PSA's Survey on Overseas Filipinos is the source, and "
                        "psa.gov.ph sits behind a managed challenge that scripts do not "
                        "pass. Without a headcount, 'average remittance per worker' "
                        "cannot be computed either &mdash; so neither appears."),
                       ("Destination and occupation",
                        "DMW's deployment statistics carry both, as PDF tables per year. "
                        "Extracting them is a real project; approximating them is what "
                        "produced the page this replaces."),
                       ("Peso figures",
                        "The old page reported remittances in pesos. The World Bank "
                        "publishes them in US dollars, and converting needs a rate "
                        "choice this analysis does not want to bury in a headline. "
                        "Everything here is in dollars and says so.")]),
        prose_section(6, "Method",
                      "One fetcher, three CSVs, via the shared helper in "
                      "<code>data/_lib/worldbank.py</code>.",
                      [("Share and dollars are cross-checked",
                        "The World Bank publishes remittances in dollars and as a share "
                        "of GDP separately. A check divides the first by GDP and fails "
                        "if it disagrees with the second &mdash; if one is revised "
                        "without the other, that is where it shows."),
                       ("Vietnam is deliberately absent",
                        "It has only five points of remittances-as-%-of-GDP, 2000 to "
                        "2004. Including it pinned the like-for-like peer comparison to "
                        "2004 and would have presented a twenty-year-old snapshot as "
                        "current. A check now fails if any peer does the same."),
                       ("Sign convention is asserted",
                        "Net migration must stay overwhelmingly negative. A flipped "
                        "sign is easy to miss because the magnitudes stay plausible "
                        "either way."),
                       ("Nominal, not real",
                        "Dollar figures are nominal. The growth multiple over {n} years "
                        "is therefore not a real-terms claim, and the page says so where "
                        "it appears.".format(n=F["nyears"])),
                       ("Like-for-like comparison",
                        "The peer table uses the latest year every country has, not "
                        "each country's own latest print."),
                       ("Verification",
                        "Nine assertions in <code>checks.sql</code>, and every figure "
                        "bound to a query in <code>facts.sql</code>.")]),
    ]

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">07</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>Overseas Filipinos sent home
                        <span data-fact="ofw.remit">${remit}</span> billion in {year},
                        worth <span data-fact="ofw.pct">{pct}%</span> of GDP.</li>
                        <li>That is <span data-fact="ofw.vs.fdi">{fdi}</span> times net
                        foreign direct investment and
                        <span data-fact="ofw.vs.exports">{exp}%</span> of all exports.
                        Remittances are a primary external inflow, not a
                        supplement.</li>
                        <li>The share of GDP peaked at
                        <span data-fact="ofw.pct.peak">{pctpk}%</span> in
                        <span data-fact="ofw.pct.peak.year">{pkyear}</span> and has
                        fallen since &mdash; the economy grew faster, not the
                        remittances smaller.</li>
                        <li>Among six large remittance economies the Philippines is
                        <span data-fact="ofw.peers.rank">{prank}</span> of
                        <span data-fact="ofw.peers.n">{pn}</span> by share of GDP, while
                        India receives
                        <span data-fact="ofw.india.usd">${india}</span> billion &mdash;
                        four times the money, at
                        <span data-fact="ofw.india.pct">{indiapct}%</span> of its
                        economy.</li>
                        <li>No figure here is a headcount. How many Filipinos work
                        abroad, what they do and where they go all sit in DMW and PSA
                        publications that no script can reach.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**F))

    yrs = [r["year"] for r in ann]
    charts = ['''        // 01 remittance inflows. Linear, not log: the point is the smoothness of
        //    the climb through 2008 and 2020, which a log axis flattens away.
        new Chart(document.getElementById('flowChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [{ label: 'Remittances received (US$ bn)', data: %s,
                             borderColor: '#22c55e',
                             backgroundColor: 'rgba(34,197,94,0.15)',
                             borderWidth: 2, pointRadius: 0, fill: true, spanGaps: false }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { ticks: { maxTicksLimit: 14 } },
                          y: { title: { display: true, text: 'US$ billions' } } }
            }
        });''' % (js(yrs),
                  js([round(f(r["remittances_usd"]) / 1e9, 2)
                      if f(r["remittances_usd"]) else None for r in ann])),
              '''        // 02 remittances against FDI and exports, all in US$ bn on one axis
        new Chart(document.getElementById('compareChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Remittances', data: %s, borderColor: '#22c55e',
                      backgroundColor: 'rgba(34,197,94,0.15)', borderWidth: 2,
                      pointRadius: 0, fill: true, spanGaps: false },
                    { label: 'Net FDI inflows', data: %s, borderColor: '#f59e0b',
                      borderWidth: 2, pointRadius: 0, fill: false, spanGaps: false },
                    { label: 'Exports of goods and services', data: %s,
                      borderColor: '#3b82f6', borderWidth: 2, borderDash: [5, 3],
                      pointRadius: 0, fill: false, spanGaps: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { ticks: { maxTicksLimit: 14 } },
                          y: { title: { display: true, text: 'US$ billions' } } }
            }
        });''' % (js(yrs),
                  js([round(f(r["remittances_usd"]) / 1e9, 2)
                      if f(r["remittances_usd"]) else None for r in ann]),
                  js([round(f(r["fdi_net_inflows_usd"]) / 1e9, 2)
                      if f(r["fdi_net_inflows_usd"]) else None for r in ann]),
                  js([round(f(r["exports_goods_services_usd"]) / 1e9, 2)
                      if f(r["exports_goods_services_usd"]) else None for r in ann])),
              '''        // 03 peers by share of GDP, Philippines highlighted
        new Chart(document.getElementById('peerChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Remittances, %% of GDP', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { title: { display: true, text: '%% of GDP' } } }
            }
        });''' % (js([r["country"] for r in peers]),
                  js([f(r["remittances_pct_gdp"]) for r in peers]),
                  js(["#22c55e" if r["country"] == "Philippines" else "#3b82f6"
                      for r in peers]))]

    p.sections(S)
    p.charts(charts)
    p.head("What Migration Sends Home",
           "Overseas Filipinos sent home $%s billion in %s -- %s%% of GDP and %s times "
           "net foreign direct investment. What migration remits, from World Bank data."
           % (F["remit"], F["year"], F["pct"], F["fdi"]),
           "$%s billion sent home in %s — %s times net foreign direct investment."
           % (F["remit"], F["year"], F["fdi"]),
           "What Migration Sends Home: Philippine Remittances, 1977-%s" % F["year"])
    p.faq({
        "How much money do overseas Filipinos send home?":
            "$%s billion in %s, equal to %s%% of GDP. In dollar terms the flow has grown "
            "from $%s million in %s across %s years without a sustained reversal -- "
            "including through the 2008 financial crisis and 2020."
            % (F["remit"], F["year"], F["pct"], F["remit77"], F["firstyear"], F["nyears"]),
        "Are remittances bigger than foreign investment in the Philippines?":
            "Yes, and by a wide margin: %s times net foreign direct investment in %s, and "
            "remittances have exceeded net FDI in every year on record. They also equal "
            "%s%% of all goods and services the country exports."
            % (F["fdi"], F["year"], F["exp"]),
        "Are Philippine remittances declining?":
            "Not in dollars. As a share of GDP they have fallen from a peak of %s%% in %s "
            "to %s%% now -- but that is the economy growing faster than the remittances, "
            "not the remittances shrinking."
            % (F["pctpk"], F["pkyear"], F["pct"]),
        "How many Filipinos work overseas?":
            "Not stated here. The headcount comes from PSA's Survey on Overseas Filipinos "
            "and DMW's deployment statistics; psa.gov.ph is behind a managed challenge "
            "and DMW publishes PDF compendiums rather than a series, so neither is "
            "fetchable. Without a headcount, average remittance per worker cannot be "
            "computed either, and this page reports neither figure.",
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
