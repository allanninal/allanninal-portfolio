#!/usr/bin/env python3
"""Regenerate projects/election-analysis.html from data/ph-election CSVs.

    .venv/bin/python tools/pages/build_election.py

The page this replaces put turnout at 67.0% -- the real figure is 82.98% -- and
total votes at 55.5M against 56.03M. Its winner figures happened to be right,
which made the rest look trustworthy.

This is the weakest source chain in the repository and the page says so in its
own section rather than in a footnote. COMELEC and the Senate both return 403 to
scripts, so the numbers are Wikipedia's transcription of the Congress canvass,
pinned to a revision id and carrying the primary URLs through for manual
checking.
"""
import csv
import json
import os
import re

D = "data/ph-election"
PAGE = "projects/election-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def js(x):
    return json.dumps(x)


def main():
    cands = rows("ph_election_candidates")
    tot = rows("ph_election_totals")
    reg = rows("ph_election_regions")
    disc = rows("ph_election_source_discrepancies")

    T = {(r["race"], r["metric"]): r for r in tot}
    pres = sorted([c for c in cands if c["race"] == "president"],
                  key=lambda c: int(c["rank"]))
    vp = sorted([c for c in cands if c["race"] == "vice_president"],
                key=lambda c: int(c["rank"]))
    urls = T[("president", "primary_source_urls")]["note"].split(" ; ")
    revid = pres[0]["revid"]

    def val(race, metric):
        return float(T[(race, metric)]["value"])

    F = dict(
        # Rounded to the precision facts.sql publishes. The template carries
        # four decimals; printing those against a fact rounded to two is a real
        # mismatch, not a formatting nicety.
        w=int(pres[0]["votes"]), ws=round(float(pres[0]["share_of_valid_pct"]), 2),
        r=int(pres[1]["votes"]), rs=round(float(pres[1]["share_of_valid_pct"]), 2),
        valid=int(val("president", "valid")),
        invalid=int(val("president", "invalid")),
        electorate=int(val("president", "electorate")),
        turnout=round(val("president", "turnout_pct"), 2),
        vpw=int(vp[0]["votes"]), vpws=round(float(vp[0]["share_of_valid_pct"]), 2),
        vpinv=int(val("vice_president", "invalid")),
        ncand=len(pres), cover=val("president", "regional_coverage_pct"),
        revid=revid, ndisc=len(disc),
    )
    F["margin"] = round(F["ws"] - F["rs"], 1)
    F["mvotes"] = F["w"] - F["r"]
    F["ratio"] = round(F["w"] / F["r"], 2)
    F["invpct"] = round(100.0 * F["invalid"] / (F["valid"] + F["invalid"]), 2)
    F["vpexcess"] = F["vpinv"] - F["invalid"]
    F["bottom7"] = sum(int(c["votes"]) for c in pres if int(c["rank"]) >= 4)

    pr = [r for r in reg if r["race"] == "president" and r["candidate"] == "Marcos"]
    pr_sorted = sorted(pr, key=lambda r: -100.0 * int(r["votes"]) / int(r["region_total"]))
    F["best"] = pr_sorted[0]["region"]
    F["bests"] = round(100.0 * int(pr_sorted[0]["votes"]) / int(pr_sorted[0]["region_total"]), 1)
    F["worst"] = pr_sorted[-1]["region"]
    F["worsts"] = round(100.0 * int(pr_sorted[-1]["votes"]) / int(pr_sorted[-1]["region_total"]), 1)
    won = 0
    for r in pr:
        others = [x for x in reg if x["race"] == "president" and x["region"] == r["region"]
                  and x["candidate"] not in ("Others",)]
        if int(r["votes"]) == max(int(x["votes"]) for x in others):
            won += 1
    F["won"] = won
    F["nregions"] = len({r["region"] for r in pr})

    hero = '''                <h1>The 2022 Philippine Election</h1>
                <p class="hero-description">
                    {ncand} presidential candidates, {electorate:,} registered voters and
                    the most lopsided result since 1953. Also {invalid:,} ballots that
                    reached a precinct and produced no valid presidential vote &mdash;
                    more than the fourth-placed candidate received.
                </p>

                <div class="header-actions">
                    <a href="{url}" target="_blank" class="btn btn-primary">
                        Congress canvass (Senate PDF)
                    </a>
                </div>

                <div class="stats-grid">
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="elec.winner.votes">{w:,}</div>
                        <div class="stat-label">Votes for the winner</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="elec.winner.share">{ws}%</div>
                        <div class="stat-label">Share of valid votes</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="elec.turnout">{turnout}%</div>
                        <div class="stat-label">Turnout</div>
                    </div>
                    <div class="stat-card fade-up">
                        <div class="stat-value" data-fact="elec.invalid">{invalid:,}</div>
                        <div class="stat-label">Invalid presidential ballots</div>
                    </div>
                </div>
'''.format(url=urls[0], **F)

    tldr = '''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Turnout was <span data-fact="elec.turnout">{turnout}%</span>, not the 67% this page used to claim. On a near-record turnout, one candidate took <span data-fact="elec.winner.share">{ws}%</span> &mdash; a margin of <span data-fact="elec.margin.pts">{margin}</span> points.</p>
                    <ul class="tldr-list">
                        <li><span data-fact="elec.winner.votes">{w:,}</span> against <span data-fact="elec.runnerup.votes">{r:,}</span>: a gap of <span data-fact="elec.margin.votes">{mvotes:,}</span> votes and a ratio of <span data-fact="elec.ratio">{ratio}</span> to one.</li>
                        <li><span data-fact="elec.invalid">{invalid:,}</span> presidential ballots were invalid &mdash; <span data-fact="elec.invalid.pct">{invpct}%</span> of everything cast, and more than the fourth-placed candidate's entire vote.</li>
                        <li>The vice-presidential race drew <span data-fact="elec.vp.invalid">{vpinv:,}</span> invalid ballots, <span data-fact="elec.vp.invalid.excess">{vpexcess:,}</span> more than the presidential race. That many people filled in a ballot and skipped the second line.</li>
                        <li>Regional dominance was near-total: <span data-fact="elec.regions.won">{won}</span> of <span data-fact="elec.regions">{nregions}</span> regions, from <span data-fact="elec.best.region.share">{bests}%</span> in Region <span data-fact="elec.best.region">{best}</span> down to <span data-fact="elec.worst.region.share">{worsts}%</span> in Region <span data-fact="elec.worst.region">{worst}</span>.</li>
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

    trows = "\n".join(
        '''                        <tr>
                            <td>{r}</td><td>{n}</td><td>{p}</td>
                            <td style="text-align:right">{v:,}</td>
                            <td style="text-align:right">{s}%</td>
                        </tr>'''.format(r=c["rank"], n=c["candidate"], p=c["party"],
                                        v=int(c["votes"]),
                                        s=round(float(c["share_of_valid_pct"]), 2))
        for c in pres)
    sec(1, "The Presidential Result",
        "All {n} candidates as canvassed by Congress. Shares are of valid votes, which "
        "is what the official return reports and is not the same as a share of ballots "
        "cast.".format(n=F["ncand"]),
        "Presidential votes by candidate", "presChart",
        [("Winner", "{w:,}".format(**F), "elec.winner.votes",
          "{s}% of valid votes.".format(s=F["ws"])),
         ("Margin", "{margin} pts".format(**F), "elec.margin.pts",
          "{m:,} votes, a ratio of {ra} to one.".format(m=F["mvotes"], ra=F["ratio"])),
         ("Bottom seven combined", "{b:,}".format(b=F["bottom7"]), "elec.bottom7",
          "Candidates four through ten together, against {r:,} for second "
          "place.".format(r=F["r"]))],
        extra='''
                <div class="fade-up" style="overflow-x:auto;">
                    <table class="data-table">
                        <thead><tr><th>#</th><th>Candidate</th><th>Party</th>
                        <th style="text-align:right">Votes</th>
                        <th style="text-align:right">Share</th></tr></thead>
                        <tbody>
''' + trows + '''
                        </tbody>
                    </table>
                </div>
''')

    sec(2, "The Ballots That Chose Nobody",
        "Turnout figures count ballots that reached a precinct. They do not tell you "
        "whether a line on the ballot was filled in. The gap between the two is the most "
        "under-reported number in any Philippine election, and it is not small.",
        "Valid and invalid ballots, president against vice president", "invalidChart",
        [("Invalid, president", "{invalid:,}".format(**F), "elec.invalid",
          "{p}% of all presidential ballots.".format(p=F["invpct"])),
         ("Invalid, vice president", "{vpinv:,}".format(**F), "elec.vp.invalid",
          "The same voters, the very next line on the same sheet."),
         ("The difference", "{vpexcess:,}".format(**F), "elec.vp.invalid.excess",
          "More people declined to pick a vice president than a president. Whatever "
          "that is, it is a choice, and it is larger than most candidates' entire "
          "vote.")])

    order = sorted({r["region"] for r in pr},
                   key=lambda g: -100.0 * int([x for x in pr if x["region"] == g][0]["votes"])
                   / int([x for x in pr if x["region"] == g][0]["region_total"]))
    sec(3, "Region By Region",
        "Presidential share by region, from strongest to weakest. Regional figures come "
        "from a scraped table rather than the structured return, and that table accounts "
        "for {c}% of the national vote &mdash; so these are shares within regions, never "
        "a national total.".format(c=F["cover"]),
        "Winner's share of the valid vote by region, %", "regionChart",
        [("Best region", "{bests}%".format(**F), "elec.best.region.share",
          "Region {b}. Regional shares range across nearly seventy "
          "points.".format(b=F["best"])),
         ("Weakest region", "{worsts}%".format(**F), "elec.worst.region.share",
          "Region {w} &mdash; the runner-up's home region and the only place the "
          "national result reverses.".format(w=F["worst"])),
         ("Regions carried", "{won} of {nregions}".format(**F), "elec.regions.won",
          "Counting the overseas absentee return as one. A national margin of thirty "
          "points is built region by region, not in one place.")])

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">04</div>
                    <h2>Where These Numbers Come From, And Why That Matters</h2>
                    <p class="section-description">
                        This is the weakest source chain on the site. It is stated here
                        rather than in a footnote, because a reader deserves to weigh it
                        before believing anything above.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>The primary record is unreachable</h4>
                        <p>The official canvass is a Senate PDF and COMELEC's own
                        statistics pages. Both return HTTP 403 to anything that is not a
                        browser, and there is no open COMELEC API. The URLs are printed
                        below so they can be checked by hand.</p>
                    </div>
                    <div class="insight-card">
                        <h4>So this is a transcription</h4>
                        <p>National figures come from Wikipedia's structured results
                        templates, which transcribe that canvass and cite it. That is a
                        tertiary source. It is used because the alternative was leaving
                        invented figures on this page, not because it is as good as a
                        primary feed.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Pinned to a revision</h4>
                        <p>Wikipedia is editable, so every row records the revision id it
                        came from &mdash; <code>{revid}</code>. A number that cannot be
                        tied to a revision cannot be rechecked later.</p>
                    </div>
                    <div class="insight-card">
                        <h4>The source disagrees with itself</h4>
                        <p><span data-fact="elec.discrepancies">{ndisc}</span> cells in the
                        regional tables publish a vote count that does not match the
                        percentage printed beside it. Region IV-B states 7.44% where its
                        own numbers imply 12.94%. Those columns are recomputed as the
                        remainder and the disagreement is kept in a CSV rather than
                        quietly corrected.</p>
                    </div>
                    <div class="insight-card">
                        <h4>The regional table is short</h4>
                        <p>Its rows sum to
                        <span data-fact="elec.regional.coverage">{cover}%</span> of the
                        valid vote its own total row declares &mdash; about 1.18 million
                        votes appear in no region at all. The vice-presidential table sums
                        to exactly 100%. Regional figures are therefore never presented
                        here as adding up to the national result.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Primary sources, for checking</h4>
                        <p>{links}</p>
                    </div>
                </div>
            </div>
        </section>
'''.format(revid=F["revid"], ndisc=F["ndisc"], cover=F["cover"],
           links=" ".join('<a href="%s" target="_blank">%s</a>'
                          % (u, ["Congress canvass", "Election-day turnout",
                                 "Absentee turnout"][i] if i < 3 else "Source")
                          for i, u in enumerate(urls[:3]))))

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">05</div>
                    <h2>What This Page Does Not Cover</h2>
                    <p class="section-description">
                        The version this replaces charted senatorial results, party-list
                        results, winning margins by province, turnout by region,
                        historical turnout, overseas absentee detail, vote concentration,
                        the gender of elected officials and election technology. None of
                        those are in a source this analysis can reach.
                    </p>
                </div>

                <div class="grid-3 fade-up">
                    <div class="insight-card">
                        <h4>Senate, party-list, provincial</h4>
                        <p>These exist in the canvass, at a level of detail no open feed
                        publishes. Reconstructing them would mean scraping many more
                        tables of the same quality as the regional one &mdash; which, as
                        section 04 shows, does not fully add up.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Turnout by region</h4>
                        <p>Requires registered voters per region, which COMELEC publishes
                        on pages that return 403. National turnout is available because
                        the electorate figure is carried in the results template; the
                        regional split is not.</p>
                    </div>
                    <div class="insight-card">
                        <h4>Historical comparison</h4>
                        <p>Every previous election would need the same treatment, each
                        with its own transcription quality. Worth doing; not done here, so
                        no trend is claimed.</p>
                    </div>
                </div>
            </div>
        </section>
''')

    S.append('''        <section class="section">
            <div class="container">
                <div class="section-header fade-up">
                    <div class="section-number">06</div>
                    <h2>Key Findings &amp; Summary</h2>
                </div>
                <div class="insight-card fade-up">
                    <ul>
                        <li>Turnout was
                        <span data-fact="elec.turnout">{turnout}%</span> of
                        <span data-fact="elec.electorate">{electorate:,}</span> registered
                        voters. The figure this page previously carried, 67%, was wrong by
                        sixteen points.</li>
                        <li>The winner took
                        <span data-fact="elec.winner.share">{ws}%</span> against
                        <span data-fact="elec.runnerup.share">{rs}%</span> &mdash; a
                        <span data-fact="elec.margin.pts">{margin}</span>-point margin and
                        <span data-fact="elec.ratio">{ratio}</span> votes for every one of
                        the runner-up's.</li>
                        <li><span data-fact="elec.invalid">{invalid:,}</span> presidential
                        ballots were invalid,
                        <span data-fact="elec.invalid.pct">{invpct}%</span> of all ballots
                        cast &mdash; more than the fourth-placed candidate polled
                        nationally.</li>
                        <li>The vice-presidential line drew
                        <span data-fact="elec.vp.invalid">{vpinv:,}</span> invalid ballots,
                        <span data-fact="elec.vp.invalid.excess">{vpexcess:,}</span> more
                        than the presidential line on the same sheets. Deliberate
                        abstention on the second race is larger than most candidates'
                        national vote.</li>
                        <li>Every figure here is a transcription of a canvass this
                        analysis cannot fetch directly, pinned to one Wikipedia revision,
                        with <span data-fact="elec.discrepancies">{ndisc}</span> internal
                        contradictions in the source recorded rather than smoothed
                        over.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(**F))

    # ---------------------------------------------------------------- charts
    charts = []
    charts.append('''        // 01 presidential votes. Log scale: the tenth candidate polled 60,592
        //    against the winner's 31.6 million, and a linear axis renders seven
        //    of the ten as invisible slivers.
        new Chart(document.getElementById('presChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Votes', data: %s, backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { type: 'logarithmic',
                               title: { display: true, text: 'Votes (log scale)' } } }
            }
        });''' % (js([c["candidate"] for c in pres]),
                  js([int(c["votes"]) for c in pres]),
                  js(["#3b82f6" if i else "#8b5cf6" for i in range(len(pres))][::-1][::-1])))

    charts.append('''        // 02 valid against invalid, both races
        new Chart(document.getElementById('invalidChart'), {
            type: 'bar',
            data: {
                labels: ['President', 'Vice president'],
                datasets: [
                    { label: 'Valid', data: %s, backgroundColor: '#3b82f6' },
                    { label: 'Invalid', data: %s, backgroundColor: '#ef4444' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                scales: { x: { stacked: true }, y: { stacked: true,
                          title: { display: true, text: 'Ballots' } } }
            }
        });''' % (js([F["valid"], int(val("vice_president", "valid"))]),
                  js([F["invalid"], F["vpinv"]])))

    shares = [(g, round(100.0 * int([x for x in pr if x["region"] == g][0]["votes"])
                        / int([x for x in pr if x["region"] == g][0]["region_total"]), 1))
              for g in order]
    charts.append('''        // 03 regional share. The 50%% line is drawn because "won the region" and
        //    "took a majority of it" are different claims and the chart should
        //    let a reader tell them apart.
        new Chart(document.getElementById('regionChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: "Winner's share of valid votes (%%)",
                             data: %s, backgroundColor: %s }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { max: 100, title: { display: true, text: 'Share (%%)' } } }
            }
        });''' % (js([s[0] for s in shares]), js([s[1] for s in shares]),
                  js(["#8b5cf6" if s[1] >= 50 else "#ef4444" for s in shares])))

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

    desc = ("The 2022 Philippine election as canvassed: {t}% turnout, a {m}-point "
            "presidential margin, and {inv:,} ballots that produced no valid "
            "presidential vote.").format(t=F["turnout"], m=F["margin"], inv=F["invalid"])
    short = ("{t}% turnout, a {m}-point margin, and {inv:,} invalid presidential "
             "ballots.").format(t=F["turnout"], m=F["margin"], inv=F["invalid"])

    def swap(pat, rep, why):
        nonlocal src
        src, n = re.subn(pat, rep, src, count=1)
        if not n:
            raise SystemExit("head patch failed (%s)" % why)

    swap(r"<title>[^<]*</title>",
         "<title>The 2022 Philippine Election | Allan Niñal - Data Analyst Portfolio</title>",
         "title")
    swap(r'<meta name="description" content="[^"]*">',
         '<meta name="description" content="%s">' % desc, "description")
    swap(r'<meta property="og:title" content="[^"]*">',
         '<meta property="og:title" content="The 2022 Philippine Election | Allan Niñal">',
         "og:title")
    swap(r'<meta property="og:description" content="[^"]*">',
         '<meta property="og:description" content="%s">' % short, "og:desc")
    swap(r'<meta name="twitter:title" content="[^"]*">',
         '<meta name="twitter:title" content="The 2022 Philippine Election">', "tw:title")
    swap(r'<meta name="twitter:description" content="[^"]*">',
         '<meta name="twitter:description" content="%s">' % short, "tw:desc")
    swap(r'"headline": "[^"]*"',
         '"headline": "The 2022 Philippine Election: The Margin, and the Ballots That Chose Nobody"',
         "headline")
    swap(r'"description": "[^"]*"', '"description": %s' % json.dumps(desc), "ld desc")

    faq = {
        "What was the turnout in the 2022 Philippine election?":
            "{t}% of {e:,} registered voters. Valid and invalid presidential ballots "
            "together came to {c:,}. Turnout counts ballots that reached a precinct, "
            "which is not the same as ballots on which a president was actually "
            "chosen.".format(t=F["turnout"], e=F["electorate"],
                             c=F["valid"] + F["invalid"]),
        "How many votes did each 2022 presidential candidate get?":
            "The winner took {w:,} votes, {ws}% of valid votes; the runner-up {r:,}, "
            "{rs}%. The margin was {m} percentage points and {mv:,} votes, a ratio of "
            "{ra} to one. Ten candidates appeared on the ballot and the bottom seven "
            "polled {b:,} between them.".format(
                w=F["w"], ws=F["ws"], r=F["r"], rs=F["rs"], m=F["margin"],
                mv=F["mvotes"], ra=F["ratio"], b=F["bottom7"]),
        "How many ballots were invalid?":
            "{i:,} presidential ballots, {p}% of all ballots cast -- more than the "
            "fourth-placed candidate received nationally. The vice-presidential race drew "
            "{v:,}, which is {x:,} more: that many people filled in a ballot and left the "
            "second line blank or spoiled.".format(
                i=F["invalid"], p=F["invpct"], v=F["vpinv"], x=F["vpexcess"]),
        "Where do these election figures come from?":
            "Wikipedia's structured transcription of the Congress canvass, pinned to "
            "revision {rv}. The primary record -- a Senate PDF and COMELEC's statistics "
            "pages -- returns HTTP 403 to anything that is not a browser, so it cannot be "
            "fetched by script; the URLs are printed on the page for manual checking. "
            "The regional tables carry {d} cells where the published vote and the "
            "published percentage disagree, and account for {c}% of the national vote, "
            "both of which are recorded rather than corrected.".format(
                rv=F["revid"], d=F["ndisc"], c=F["cover"]),
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
