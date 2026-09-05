#!/usr/bin/env python3
"""Regenerate projects/education-analysis.html from data/ph-education CSVs.

    .venv/bin/python tools/pages/build_education.py

The published page carried fifty charts and no figure that traced to anything.
The dataset it cited is 187 rows and downloads without authentication: DepEd
enrollment by grade and senior-high track, plus teacher counts by level, for all
17 regions across the eleven academic years to SY 2020-2021.

Three things in it carry the page.

The K-12 rollout. Every G11 and G12 column is zero until SY 2016-2017, when
senior high school appears with 731,981 pupils and 36,788 teachers, and reaches
1,987,180 pupils by 2020-21. A whole tier of schooling in four years.

The staffing. Enrollment rose 14.61% over the eleven years and teacher numbers
rose 72.66% -- 369,009 more teachers, growing 4.97 times as fast as enrollment.
The blended pupil-teacher ratio fell from 38.93 to 25.84. Senior high is the
exception and runs the other way: it opened at 19.9 pupils per teacher, hit 29.57
a year later as enrollment doubled, and was still at 26.83 in the last year.

And the tracks. The largest senior-high track is not STEM. It is
Technical-Vocational-Livelihood at 37.84%, which is 4.2 times STEM's 9.02%. STEM
is fourth of eight.

Against all of that the page sets the national UIS figures, because enrollment
data cannot be asked who is missing: 8.55% of a primary cohort does not complete
primary, 1,616,165 primary-age children are out of school, and net secondary
enrolment was 65.56% in 2015 against a gross 82.01% the same year.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import Page, js, r                               # noqa: E402

D = "data/ph-education"
PAGE = "projects/education-analysis.html"


def rows(n):
    return list(csv.DictReader(open(os.path.join(D, n + ".csv"))))


def f(v):
    return float(v) if v not in (None, "", "None") else None


def main():
    nat = sorted(rows("ph_education_national"), key=lambda x: int(x["ay_start"]))
    lvl = rows("ph_education_levels")
    trk = rows("ph_education_tracks")
    shs = sorted(rows("ph_education_shs"), key=lambda x: int(x["ay_start"]))
    reg = rows("ph_education_by_region")
    out = rows("ph_education_outcomes")
    spd = rows("ph_education_spend_asean")
    cov = {x["property"]: x["value"] for x in rows("ph_education_coverage")}

    first, last = nat[0], nat[-1]
    LY = max(int(x["ay_start"]) for x in reg)
    latest_reg = sorted((x for x in reg if int(x["ay_start"]) == LY),
                        key=lambda x: -f(x["pupils_per_teacher"]))
    TY = max(int(x["ay_start"]) for x in trk)
    tracks = sorted((x for x in trk if int(x["ay_start"]) == TY),
                    key=lambda x: -int(x["enrollees"]))
    stem = [x for x in tracks if x["track"] == "STEM"][0]

    def lv(level, idx):
        got = sorted((x for x in lvl if x["level"] == level),
                     key=lambda x: int(x["ay_start"]))
        return got[idx]

    def wb(col):
        got = [x for x in out if x[col]]
        return (int(got[-1]["year"]), f(got[-1][col])) if got else (None, None)

    net_row = [x for x in out if x["secondary_net_enrolment_pct"]][-1]
    pcy, pc = wb("primary_completion_pct")
    osy, oos = wb("primary_age_out_of_school")
    lity, lit = wb("adult_literacy_pct")
    tery, ter = wb("tertiary_gross_enrolment_pct")
    spy, sp = wb("education_spend_pct_gdp")
    gly, gl = wb("secondary_gross_enrolment_pct")

    comparable = [x for x in spd if x["comparable"] == "yes"]
    excluded = [x for x in spd if x["comparable"] == "no"]
    ph_sp = [x for x in spd if x["country"] == "Philippines"][0]
    shs_on = [x for x in shs if int(x["enrollees"]) > 0]

    F = dict(
        years=int(cov["academic years"]), nrows=int(cov["rows"]),
        nreg=int(cov["regions"]),
        y0=first["academic_year"], y1=last["academic_year"],
        e0=int(first["enrollees"]), e1=int(last["enrollees"]),
        echange=f(cov["enrollment change over the period"]),
        t0=int(first["teachers"]), t1=int(last["teachers"]),
        tchange=f(cov["teacher change over the period"]),
        r0=f(first["pupils_per_teacher"]), r1=f(last["pupils_per_teacher"]),
        elem0=f(lv("elementary", 0)["pupils_per_teacher"]),
        elem1=f(lv("elementary", -1)["pupils_per_teacher"]),
        jhs0=f(lv("junior high", 0)["pupils_per_teacher"]),
        jhs1=f(lv("junior high", -1)["pupils_per_teacher"]),
        elemE1=int(lv("elementary", -1)["enrollees"]),
        elemEch=r(100.0 * (int(lv("elementary", -1)["enrollees"])
                           / int(lv("elementary", 0)["enrollees"]) - 1), 2),
        jhsEch=r(100.0 * (int(lv("junior high", -1)["enrollees"])
                          / int(lv("junior high", 0)["enrollees"]) - 1), 2),
        sy0=shs_on[0]["academic_year"], se0=int(shs_on[0]["enrollees"]),
        se1=int(shs[-1]["enrollees"]),
        st0=int(shs_on[0]["teachers"]), st1=int(shs[-1]["teachers"]),
        sr0=f(shs_on[0]["pupils_per_teacher"]),
        srw=max(f(x["pupils_per_teacher"]) for x in shs_on),
        srwy=max(shs_on, key=lambda x: f(x["pupils_per_teacher"]))["academic_year"],
        sr1=f(shs[-1]["pupils_per_teacher"]),
        sshare=r(100.0 * int(last["enrollees_shs"]) / int(last["enrollees"]), 2),
        ttop=tracks[0]["track"], ttopname=tracks[0]["track_name"],
        ttoppct=f(tracks[0]["pct_of_shs"]), ttopn=int(tracks[0]["enrollees"]),
        stempct=f(stem["pct_of_shs"]), stemn=int(stem["enrollees"]),
        stemrank=1 + sum(1 for x in tracks
                         if int(x["enrollees"]) > int(stem["enrollees"])),
        acadpct=r(sum(f(x["pct_of_shs"]) for x in tracks
                      if x["track"] in ("ABM", "HUMSS", "STEM", "GAS")), 2),
        tsmall=tracks[-1]["track"], tsmalln=int(tracks[-1]["enrollees"]),
        ntrack=len(tracks),
        rworst=latest_reg[0]["region"],
        rworstv=f(latest_reg[0]["pupils_per_teacher"]),
        rbest=latest_reg[-1]["region"],
        rbestv=f(latest_reg[-1]["pupils_per_teacher"]),
        rbig=max(latest_reg, key=lambda x: int(x["enrollees"]))["region"],
        rbign=max(int(x["enrollees"]) for x in latest_reg),
        pc=pc, pcy=pcy, oos=oos, osy=osy, lit=lit, ter=ter, sp=sp, spy=spy,
        gl=gl, gly=gly,
        net=f(net_row["secondary_net_enrolment_pct"]),
        nety=int(net_row["year"]),
        gross=f(net_row["secondary_gross_enrolment_pct"]),
        spyear=int(ph_sp["year"]), spph=f(ph_sp["education_spend_pct_gdp"]),
        spn=len(comparable),
        sprank=1 + sum(1 for x in comparable
                       if f(x["education_spend_pct_gdp"])
                       > f(ph_sp["education_spend_pct_gdp"])),
        spexcl=len(excluded),
        spexclname=excluded[0]["country"] if excluded else "",
    )
    F["rdrop"] = r(100.0 * (1 - F["r1"] / F["r0"]), 1)
    F["gratio"] = r(F["tchange"] / F["echange"], 2)
    F["tadded"] = F["t1"] - F["t0"]
    F["sgrowth"] = r(F["se1"] / F["se0"], 2)
    F["tvlstem"] = r(F["ttopn"] / F["stemn"], 2)
    F["pcmiss"] = r(100 - F["pc"], 2)
    F["netgap"] = r(F["gross"] - F["net"], 2)
    F["rspread"] = r(F["rworstv"] - F["rbestv"], 2)

    # Short region labels: the source spells them "BARMM - Bangsamoro Autonomous
    # Region in Muslim Mindanao", which is unreadable on a card.
    def short(name):
        return name.split(" - ")[0].strip()
    F["rworsts"] = short(F["rworst"])
    F["rbests"] = short(F["rbest"])
    F["rbigs"] = short(F["rbig"])

    p = Page(PAGE)
    p.hero('''                <h1>A Whole New Tier Of School, Built In Four Years</h1>
                <p class="{hero_desc}">
                    DepEd public-school counts for {years} academic years and all
                    {nreg} regions. Senior high school did not exist until
                    {sy0}; by {y1} it held {se1:,} pupils. Over the same period
                    teachers grew {gratio} times as fast as enrollment.
                </p>

                <div class="header-actions">
                    <a href="https://www.kaggle.com/datasets/johnjoemmelrodelas/philippine-public-education-data" target="_blank" class="btn btn-primary">
                        DepEd enrollment data (Kaggle)
                    </a>
                </div>

                <div class="{grid}">
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="shs.last.enrol">{se1:,}</div>
                        <div class="{label}">Senior high pupils, {y1}, from zero in 2015</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="deped.ratio.last">{r1}</div>
                        <div class="{label}">Pupils per teacher, down from {r0}</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="track.top.pct">{ttoppct}%</div>
                        <div class="{label}">Of senior high in {ttop}, not STEM</div>
                    </div>
                    <div class="{card} fade-up">
                        <div class="{value}" data-fact="ph.outofschool">{oos:,.0f}</div>
                        <div class="{label}">Primary-age children out of school, {osy}</div>
                    </div>
                </div>
'''.format(**dict(F, **p.t)))

    p.tldr('''                    <span class="tldr-badge">Key Takeaways</span>
                    <p class="tldr-headline">Enrollment rose <span data-fact="deped.enrol.change">{echange}%</span> across the eleven years. Teacher numbers rose <span data-fact="deped.teachers.change">{tchange}%</span> &mdash; <span data-fact="deped.teachers.added">{tadded:,}</span> more teachers, growing <span data-fact="deped.growth.ratio">{gratio}</span> times as fast &mdash; and the pupil-teacher ratio fell from <span data-fact="deped.ratio.first">{r0}</span> to <span data-fact="deped.ratio.last">{r1}</span>.</p>
                    <ul class="tldr-list">
                        <li>Senior high school appears in {sy0} with <span data-fact="shs.first.enrol">{se0:,}</span> pupils and reaches <span data-fact="shs.last.enrol">{se1:,}</span> by {y1}, a factor of <span data-fact="shs.growth">{sgrowth}</span>. It is now <span data-fact="shs.share.of.enrol">{sshare}%</span> of all public basic-education enrollment.</li>
                        <li>It is also the one tier where crowding got worse. Senior high opened at <span data-fact="shs.ratio.first">{sr0}</span> pupils per teacher, hit <span data-fact="shs.ratio.worst">{srw}</span> the following year as enrollment doubled, and was still <span data-fact="shs.ratio.last">{sr1}</span> in the last year &mdash; while elementary fell from <span data-fact="deped.elem.ratio.first">{elem0}</span> to <span data-fact="deped.elem.ratio.last">{elem1}</span>.</li>
                        <li>The biggest senior-high track is <span data-fact="track.top.pct">{ttoppct}%</span> {ttop} &mdash; Technical-Vocational-Livelihood &mdash; against STEM's <span data-fact="track.stem.pct">{stempct}%</span>. That is <span data-fact="track.tvl.over.stem">{tvlstem}</span> times as many pupils, and it puts STEM <span data-fact="track.stem.rank">{stemrank}</span>th of <span data-fact="track.n">{ntrack}</span>.</li>
                        <li>None of that says anything about learning, and the national figures are less comfortable: <span data-fact="ph.primary.missing">{pcmiss}%</span> of a primary cohort does not complete primary, and <span data-fact="ph.outofschool">{oos:,.0f}</span> primary-age children were out of school in {osy}.</li>
                        <li>These are public schools only. Roughly a tenth of Philippine basic education is private and is absent from every DepEd figure here.</li>
                    </ul>
'''.format(**F))

    S = [
        p.section(1, "Teachers Grew Five Times Faster Than Pupils",
                  "National enrollment and teacher counts across the {years} "
                  "academic years. The two lines are on separate axes because the "
                  "point is the difference in slope, not the difference in "
                  "level.".format(**F),
                  [("Enrollment", "+{v}%".format(v=F["echange"]),
                    "deped.enrol.change",
                    "{a:,} to {b:,} pupils.".format(a=F["e0"], b=F["e1"])),
                   ("Teachers", "+{v}%".format(v=F["tchange"]),
                    "deped.teachers.change",
                    "{a:,} to {b:,} &mdash; "
                    "<span data-fact=\"deped.teachers.added\">{c:,}</span> more "
                    "posts.".format(a=F["t0"], b=F["t1"], c=F["tadded"])),
                   ("Pupils per teacher", "{v}".format(v=F["r1"]),
                    "deped.ratio.last",
                    "Down from <span data-fact=\"deped.ratio.first\">{a}</span>, a "
                    "fall of <span data-fact=\"deped.ratio.drop\">{d}%</span>. "
                    "Blended across all three levels; section 3 separates them."
                    .format(a=F["r0"], d=F["rdrop"]))],
                  "Enrollment and teacher counts, %s to %s"
                  % (F["y0"], F["y1"]), "growthChart"),
        p.section(2, "Senior High School, From Nothing",
                  "K-12 added two years to Philippine basic education. Every "
                  "senior-high column in the file is zero until {sy0}, which is "
                  "asserted by a check &mdash; a stray value before then would "
                  "mean the grade columns are being matched wrongly."
                  .format(**F),
                  [("First year", "{v:,}".format(v=F["se0"]), "shs.first.enrol",
                    "Pupils in {y}, with "
                    "<span data-fact=\"shs.teachers.first\">{t:,}</span> teachers."
                    .format(y=F["sy0"], t=F["st0"])),
                   ("Four years later", "{v:,}".format(v=F["se1"]),
                    "shs.last.enrol",
                    "A factor of <span data-fact=\"shs.growth\">{g}</span>, with "
                    "<span data-fact=\"shs.teachers.last\">{t:,}</span> teachers."
                    .format(g=F["sgrowth"], t=F["st1"])),
                   ("Share of all enrollment", "{v}%".format(v=F["sshare"]),
                    "shs.share.of.enrol",
                    "Of public basic education in {y}. Junior high enrollment rose "
                    "<span data-fact=\"deped.jhs.enrol.change\">{j}%</span> over "
                    "the period while elementary fell "
                    "<span data-fact=\"deped.elem.enrol.change\">{e}%</span> "
                    "&mdash; a cohort moving up, not a system shrinking."
                    .format(y=F["y1"], j=F["jhsEch"], e=F["elemEch"]))],
                  "Senior high enrollment and teachers, by academic year",
                  "shsChart"),
        p.section(3, "The One Tier That Got More Crowded",
                  "Pupils per teacher for each level, each paired only with its "
                  "own staff. A check asserts that pairing, because crossing two "
                  "levels' figures would produce a plausible number and would be "
                  "invisible on a chart.",
                  # A card value that prints two numbers can only bind to the
                  # first, so the value carries the starting ratio and the body
                  # carries the ending one in its own span.
                  [("Elementary", "{a}".format(a=F["elem0"]),
                    "deped.elem.ratio.first",
                    'Down to <span data-fact="deped.elem.ratio.last">{b}</span>, '
                    'helped by enrollment actually falling '
                    '<span data-fact="deped.elem.enrol.change">{c}%</span> to '
                    '<span data-fact="deped.elem.enrol.last">{n:,}</span> &mdash; '
                    'not only by hiring.'.format(b=F["elem1"], c=F["elemEch"],
                                                 n=F["elemE1"])),
                   ("Junior high", "{a}".format(a=F["jhs0"]),
                    "deped.jhs.ratio.first",
                    'Down to <span data-fact="deped.jhs.ratio.last">{b}</span>, the '
                    'largest fall of the three, and with enrollment up '
                    '<span data-fact="deped.jhs.enrol.change">{j}%</span> at the '
                    'same time.'.format(b=F["jhs1"], j=F["jhsEch"])),
                   ("Senior high", "{a}".format(a=F["sr0"]),
                    "shs.ratio.first",
                    'The wrong way. It opened here, peaked at '
                    '<span data-fact="shs.ratio.worst">{w}</span> in {wy} when '
                    'enrollment doubled in one year, and was still '
                    '<span data-fact="shs.ratio.last">{b}</span> at the end &mdash; '
                    'recovering, without reaching where it started.'
                    .format(w=F["srw"], wy=F["srwy"], b=F["sr1"]))],
                  "Pupils per teacher by level, each with its own staff",
                  "ratioChart"),
        p.section(4, "Vocational, Not STEM",
                  "Senior-high enrollment by track in {ty}. The academic strands "
                  "together are <span data-fact=\"track.academic.pct\">{a}%</span>, "
                  "so the split is not academic-versus-vocational so much as one "
                  "very large vocational track against four smaller academic ones."
                  .format(ty=trk and tracks[0]["academic_year"], a=F["acadpct"]),
                  [(F["ttopname"], "{v}%".format(v=F["ttoppct"]), "track.top.pct",
                    "<span data-fact=\"track.top.n\">{n:,}</span> pupils. The "
                    "largest single track by a wide margin."
                    .format(n=F["ttopn"])),
                   ("STEM", "{v}%".format(v=F["stempct"]), "track.stem.pct",
                    "<span data-fact=\"track.stem.n\">{n:,}</span> pupils &mdash; "
                    "<span data-fact=\"track.stem.rank\">{r}</span>th of "
                    "<span data-fact=\"track.n\">{t}</span>, and "
                    "<span data-fact=\"track.tvl.over.stem\">{x}</span> times "
                    "smaller than {top}.".format(n=F["stemn"], r=F["stemrank"],
                                                 t=F["ntrack"], x=F["tvlstem"],
                                                 top=F["ttop"])),
                   ("Smallest track", "{v:,}".format(v=F["tsmalln"]),
                    "track.smallest.n",
                    "{s}, nationwide. An entire strand smaller than a large "
                    "school.".format(s=F["tsmall"]))],
                  "Senior high enrollment by track", "trackChart"),
        p.section(5, "Where The Classrooms Are Fullest",
                  "Pupils per teacher by region in the last year. The spread is "
                  "<span data-fact=\"region.spread\">{s}</span> pupils between "
                  "the extremes, and the ordering is close to the ordering of "
                  "almost every other development measure in this project."
                  .format(s=F["rspread"]),
                  [(F["rworsts"], "{v}".format(v=F["rworstv"]),
                    "region.worst.ratio",
                    "The most crowded of the {n} regions."
                    .format(n=F["nreg"])),
                   (F["rbests"], "{v}".format(v=F["rbestv"]),
                    "region.best.ratio",
                    "The least crowded. A gap of "
                    "<span data-fact=\"region.spread\">{s}</span> pupils per "
                    "teacher.".format(s=F["rspread"])),
                   ("Largest system", "{v:,}".format(v=F["rbign"]),
                    "region.biggest.n",
                    "Pupils in {r} &mdash; more than the whole of "
                    "{w}.".format(r=F["rbigs"], w=F["rworsts"]))],
                  "Pupils per teacher by region, %s" % F["y1"], "regionChart"),
        p.section(6, "What Enrollment Data Cannot Be Asked",
                  "Everything above counts children who are enrolled. These are "
                  "national UIS estimates, which include private schools and "
                  "children in no school at all &mdash; the question the DepEd "
                  "file cannot answer about itself.",
                  [("Primary completion", "{v}%".format(v=F["pc"]),
                    "ph.primary.completion",
                    "In {y}, meaning "
                    "<span data-fact=\"ph.primary.missing\">{m}%</span> of a "
                    "cohort does not finish primary school."
                    .format(y=F["pcy"], m=F["pcmiss"])),
                   ("Out of school", "{v:,.0f}".format(v=F["oos"]),
                    "ph.outofschool",
                    "Primary-age children not enrolled anywhere, {y}."
                    .format(y=F["osy"])),
                   ("Secondary, net against gross",
                    "{a}% vs {b}%".format(a=F["net"], b=F["gross"]),
                    "ph.secondary.net",
                    "Both {y}, deliberately: net stops at {y} and gross runs to "
                    "{gy}, so pairing each with its own latest year would print "
                    "three numbers that do not add up. Net counts only pupils of "
                    "the official age, so the "
                    "<span data-fact=\"ph.secondary.gap\">{g}</span>-point gap is "
                    "over-age pupils.".format(y=F["nety"], gy=F["gly"],
                                              g=F["netgap"]))],
                  "Primary completion, secondary enrolment and out-of-school "
                  "children", "outcomeChart"),
        p.section(7, "And What It Costs",
                  "Education spending as a share of GDP across ASEAN in "
                  "{y}. Indonesia is shown but excluded from the ranking: its "
                  "series falls from 3.58% of GDP in 2015 to about 1% after, which "
                  "is a change in what it reports rather than in what it spends, "
                  "and a break like that is detected rather than assumed."
                  .format(y=F["spyear"]),
                  [("Philippines", "{v}%".format(v=F["spph"]), "spend.ph",
                    "Of GDP in {y}, the highest of the "
                    "<span data-fact=\"spend.asean.n\">{n}</span> comparable "
                    "countries.".format(y=F["spyear"], n=F["spn"])),
                   ("Latest available", "{v}%".format(v=F["sp"]), "ph.spend",
                    "The Philippine figure for {y}, its own most recent."
                    .format(y=F["spy"])),
                   ("Excluded from the ranking",
                    "{v}".format(v=F["spexcl"]), "spend.excluded",
                    "{n}, for the series break above. The row is kept rather than "
                    "dropped, because a five-country chart labelled ASEAN reads as "
                    "though the sixth was never there."
                    .format(n=F["spexclname"]))],
                  "Education spending as a share of GDP, ASEAN, %d" % F["spyear"],
                  "spendChart"),
        p.prose(8, "What This Page Does Not Claim",
                "Four limits, all recorded in the coverage file and asserted by "
                "checks.",
                [("Public schools only",
                  "DepEd counts the schools it runs. Roughly a tenth of Philippine "
                  "basic education is private, and it is absent from every DepEd "
                  "figure here &mdash; including the pupil-teacher ratios, which "
                  "would look different if private schools were in them."),
                 ("Enrollment is not learning",
                  "There are no test scores in this file, no completion rates and "
                  "no grades. It records who is on a roll. The national figures in "
                  "section 6 are the nearest this project gets to an outcome, and "
                  "they are enrolment and completion rather than attainment."),
                 ("Pupils per teacher is not class size",
                  "A teacher may take several classes and a class several teachers, "
                  "and the file carries neither class nor school counts. The ratio "
                  "is a staffing measure. It is a real one &mdash; it is what "
                  "changed most over the decade &mdash; but it is not the number "
                  "of children in a room."),
                 ("Nobody is followed between years",
                  "Each row is one region in one year, so no pupil cohort can be "
                  "tracked and no dropout or repetition rate can be computed from "
                  "this. The rise in junior-high enrollment alongside the fall in "
                  "elementary is consistent with a cohort moving up, but this data "
                  "cannot confirm that it is the same children.")]),
        p.prose(9, "Method",
                "One fetcher over a 187-row file, plus the World Bank for what the "
                "file cannot say.",
                [("Senior-high columns are matched by prefix",
                  "The source spells one of them Enrollees_G122_SPORTs &mdash; a "
                  "typo for G12. Matching by prefix counts it; a hand-kept list "
                  "would have dropped 3,809 pupils and the totals would still have "
                  "looked plausible. A check asserts the three levels sum to the "
                  "national total, which is what would catch it next time."),
                 ("Each level's ratio uses only its own staff",
                  "Elementary enrollment against elementary teachers, and so on. A "
                  "blended figure hides that senior high moved the opposite way "
                  "from the other two, which is the most interesting thing in the "
                  "file."),
                 ("A reporting break is detected, not hardcoded",
                  "Indonesia's education spending falls from 3.58% of GDP to 1.21% "
                  "in one year and stays down, because it devolves most spending to "
                  "its regions and changed what it reports to UIS. Any country "
                  "whose series halves and stays down is flagged automatically, "
                  "with the break year recorded, rather than a name being written "
                  "into the script."),
                 ("Two figures the page pairs share a year on purpose",
                  "Net secondary enrolment stops at {ny} and gross runs to {gy}. "
                  "Taking each at its own latest year would put {n}% and {g}% "
                  "beside a gap of {gap} points &mdash; three numbers that do not "
                  "add up. A check fails if the year the page pairs them on ever "
                  "loses one of them.".format(ny=F["nety"], gy=F["gly"],
                                              n=F["net"], g=F["gl"],
                                              gap=F["netgap"])),
                 ("Regions are shortened for display only",
                  "The source spells one “BARMM - Bangsamoro Autonomous Region "
                  "in Muslim Mindanao”. Cards use the acronym; the CSVs keep "
                  "the full string, so a figure still traces to a row that names "
                  "the region in full."),
                 ("The counterweight comes through the World Bank",
                  "UIS completion, enrolment, out-of-school and spending series, "
                  "fetched from the WDI API because it is reachable and returns a "
                  "clean error on a wrong indicator code rather than an empty "
                  "success.")]),
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
                        <li>Enrollment rose
                        <span data-fact="deped.enrol.change">{echange}%</span> while
                        teachers rose
                        <span data-fact="deped.teachers.change">{tchange}%</span>
                        &mdash;
                        <span data-fact="deped.teachers.added">{tadded:,}</span>
                        more posts, growing
                        <span data-fact="deped.growth.ratio">{gratio}</span> times
                        as fast &mdash; taking pupils per teacher from
                        <span data-fact="deped.ratio.first">{r0}</span> to
                        <span data-fact="deped.ratio.last">{r1}</span>.</li>
                        <li>Senior high school went from nothing to
                        <span data-fact="shs.last.enrol">{se1:,}</span> pupils in
                        four years, now
                        <span data-fact="shs.share.of.enrol">{sshare}%</span> of
                        public basic education.</li>
                        <li>It is the only tier that got more crowded:
                        <span data-fact="shs.ratio.first">{sr0}</span> pupils per
                        teacher at launch,
                        <span data-fact="shs.ratio.worst">{srw}</span> a year later,
                        <span data-fact="shs.ratio.last">{sr1}</span> at the end
                        &mdash; against elementary's
                        <span data-fact="deped.elem.ratio.last">{elem1}</span>.</li>
                        <li>{ttop} is
                        <span data-fact="track.top.pct">{ttoppct}%</span> of senior
                        high against STEM's
                        <span data-fact="track.stem.pct">{stempct}%</span> &mdash;
                        <span data-fact="track.tvl.over.stem">{tvlstem}</span> times
                        as many pupils, putting STEM
                        <span data-fact="track.stem.rank">{stemrank}</span>th of
                        <span data-fact="track.n">{ntrack}</span>.</li>
                        <li>{rworsts} runs
                        <span data-fact="region.worst.ratio">{rworstv}</span> pupils
                        per teacher against {rbests}'s
                        <span data-fact="region.best.ratio">{rbestv}</span>.</li>
                        <li>None of it measures learning. Nationally
                        <span data-fact="ph.primary.missing">{pcmiss}%</span> of a
                        primary cohort does not complete primary and
                        <span data-fact="ph.outofschool">{oos:,.0f}</span>
                        primary-age children were out of school in {osy}.</li>
                    </ul>
                </div>
            </div>
        </section>
'''.format(hcls=HCLS, cwrap=CWRAP, **dict(F, **p.t)))

    YR = [x["academic_year"].replace("SY ", "") for x in nat]
    EL = sorted((x for x in lvl if x["level"] == "elementary"),
                key=lambda x: int(x["ay_start"]))
    JH = sorted((x for x in lvl if x["level"] == "junior high"),
                key=lambda x: int(x["ay_start"]))
    SH = sorted((x for x in lvl if x["level"] == "senior high"),
                key=lambda x: int(x["ay_start"]))
    RG = list(reversed(latest_reg))
    OUTY = [x for x in out if int(x["year"]) >= 1990]

    charts = ['''        // 01 enrollment against teachers, two axes. The slopes are the finding.
        new Chart(document.getElementById('growthChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Enrollees', data: %s, borderColor: '#3b82f6', backgroundColor: '#3b82f6',
                      borderWidth: 3, pointRadius: 3, fill: false, yAxisID: 'y' },
                    { label: 'Teachers', data: %s, borderColor: '#22c55e', backgroundColor: '#22c55e',
                      borderWidth: 3, pointRadius: 3, fill: false, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { position: 'left',
                               title: { display: true, text: 'Enrollees' } },
                          y1: { position: 'right', grid: { drawOnChartArea: false },
                                title: { display: true, text: 'Teachers' } } }
            }
        });''' % (js(YR), js([int(x["enrollees"]) for x in nat]),
                  js([int(x["teachers"]) for x in nat])),

              '''        // 02 the rollout. Zero before SY 2016-2017 is drawn as a gap, not a zero
        //    line, because the tier did not exist rather than being empty.
        new Chart(document.getElementById('shsChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [
                    // order: the bar behind, the line in front. Chart.js sorts
                    // datasets by `order` and then draws that list backwards, so
                    // with both left at 0 the bar -- dataset 0 -- paints last and
                    // covers the line it is meant to sit under.
                    { label: 'Senior high enrollees', data: %s, order: 2,
                      backgroundColor: '#8b5cf6', yAxisID: 'y' },
                    { type: 'line', label: 'Senior high teachers', data: %s, order: 1,
                      borderColor: '#f59e0b', backgroundColor: '#f59e0b', borderWidth: 3, pointRadius: 4,
                      fill: false, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                // the legend follows draw order unless told otherwise, and the
                // order above would have put the bar at the end of it.
                plugins: { legend: { labels: {
                    sort: (a, b) => a.datasetIndex - b.datasetIndex } } },
                scales: { y: { position: 'left', beginAtZero: true,
                               title: { display: true, text: 'Pupils' } },
                          y1: { position: 'right', beginAtZero: true,
                                grid: { drawOnChartArea: false },
                                title: { display: true, text: 'Teachers' } } }
            }
        });''' % (js(YR),
                  js([int(x["enrollees"]) or None for x in shs]),
                  js([int(x["teachers"]) or None for x in shs])),

              '''        // 03 pupils per teacher by level. Senior high starts late and goes the
        //    other way, which is why the three are drawn together.
        new Chart(document.getElementById('ratioChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Elementary', data: %s, borderColor: '#3b82f6', backgroundColor: '#3b82f6',
                      borderWidth: 3, pointRadius: 3, fill: false },
                    { label: 'Junior high', data: %s, borderColor: '#22c55e', backgroundColor: '#22c55e',
                      borderWidth: 3, pointRadius: 3, fill: false },
                    { label: 'Senior high', data: %s, borderColor: '#ef4444', backgroundColor: '#ef4444',
                      borderWidth: 3, pointRadius: 4, fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: 'Pupils per teacher' } } }
            }
        });''' % (js(YR),
                  js([f(x["pupils_per_teacher"]) or None for x in EL]),
                  js([f(x["pupils_per_teacher"]) or None for x in JH]),
                  js([f(x["pupils_per_teacher"]) or None for x in SH])),

              '''        // 04 track choice. TVL highlighted because it is the finding; the four
        //    academic strands share a colour so the split is visible.
        new Chart(document.getElementById('trackChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Senior high enrollees', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex] + '%% of senior high'; } } } },
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: 'Pupils' } } }
            }
        });''' % (js([x["track"] for x in tracks]),
                  js([int(x["enrollees"]) for x in tracks]),
                  js(["#ef4444" if x["track"] == "TVL"
                      else "#3b82f6" if x["track"] in ("ABM", "HUMSS", "STEM", "GAS")
                      else "#94a3b8" for x in tracks]),
                  js([f(x["pct_of_shs"]) for x in tracks])),

              '''        // 05 by region, least crowded first.
        new Chart(document.getElementById('regionChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Pupils per teacher', data: %s,
                             backgroundColor: %s }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex].toLocaleString() + ' pupils'; } } } },
                scales: { x: { beginAtZero: true,
                               title: { display: true, text: 'Pupils per teacher' } } }
            }
        });''' % (js([x["region"].split(" - ")[0] for x in RG]),
                  js([f(x["pupils_per_teacher"]) for x in RG]),
                  js(["#ef4444" if f(x["pupils_per_teacher"]) > 30 else "#3b82f6"
                      for x in RG]),
                  js([int(x["enrollees"]) for x in RG])),

              '''        // 06 national outcomes. Net secondary stops in 2015, so the line stops
        //    there rather than being carried forward.
        new Chart(document.getElementById('outcomeChart'), {
            type: 'line',
            data: {
                labels: %s,
                datasets: [
                    { label: 'Primary completion (%%)', data: %s,
                      borderColor: '#22c55e', borderWidth: 3, pointRadius: 0,
                      fill: false, spanGaps: true },
                    { label: 'Secondary gross enrolment (%%)', data: %s,
                      borderColor: '#3b82f6', borderWidth: 3, pointRadius: 0,
                      fill: false, spanGaps: true },
                    { label: 'Secondary net enrolment (%%)', data: %s,
                      borderColor: '#ef4444', borderDash: [6, 4], borderWidth: 3,
                      pointRadius: 0, fill: false, spanGaps: true }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: { y: { min: 0, max: 110,
                               title: { display: true, text: '%% of the relevant cohort' } } }
            }
        });''' % (js([int(x["year"]) for x in OUTY]),
                  js([f(x["primary_completion_pct"]) for x in OUTY]),
                  js([f(x["secondary_gross_enrolment_pct"]) for x in OUTY]),
                  js([f(x["secondary_net_enrolment_pct"]) for x in OUTY])),

              '''        // 07 ASEAN spending. Indonesia is drawn in grey and labelled rather than
        //    dropped -- its series break makes it uncomparable, not absent.
        new Chart(document.getElementById('spendChart'), {
            type: 'bar',
            data: {
                labels: %s,
                datasets: [{ label: 'Education spending (%% of GDP)', data: %s,
                             backgroundColor: %s, borderRadius: 6 }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false },
                           tooltip: { callbacks: { afterLabel: function (c) {
                               return %s[c.dataIndex]; } } } },
                scales: { y: { beginAtZero: true,
                               title: { display: true, text: '%% of GDP' } } }
            }
        });''' % (js([x["country"] for x in spd]),
                  js([f(x["education_spend_pct_gdp"]) for x in spd]),
                  js(["#94a3b8" if x["comparable"] == "no"
                      else "#ef4444" if x["country"] == "Philippines"
                      else "#3b82f6" for x in spd]),
                  js([("not comparable: " + x["note"][:80]) if x["note"]
                      else "comparable" for x in spd])),
              ]

    p.sections(S)
    p.charts(charts)
    p.head(
        "A Whole New Tier Of School, Built In Four Years",
        "DepEd public-school counts for %d academic years: senior high school from "
        "zero to %s pupils, teachers growing %s times as fast as enrollment, and "
        "TVL at %s%% against STEM's %s%% -- set against %s primary-age children out "
        "of school."
        % (F["years"], format(F["se1"], ","), F["gratio"], F["ttoppct"],
           F["stempct"], format(int(F["oos"]), ",")),
        "Teachers grew %s times faster than pupils. And the biggest senior-high "
        "track is not STEM." % F["gratio"],
        "A Whole New Tier Of School, Built In Four Years")
    p.faq({
        "What is the pupil-teacher ratio in Philippine public schools?":
            "%s pupils per teacher in %s across all levels, down from %s in %s. "
            "Separated by level it is %s in elementary and %s in junior high, both "
            "much improved -- but %s in senior high, which opened at %s in its first "
            "year and got more crowded as enrollment tripled. Note this is a "
            "staffing ratio, not class size: a teacher may take several classes."
            % (F["r1"], F["y1"], F["r0"], F["y0"], F["elem1"], F["jhs1"], F["sr1"],
               F["sr0"]),
        "How many students are in senior high school in the Philippines?":
            "%s in %s, in public schools. Senior high school did not exist before "
            "%s -- K-12 added it -- and it began with %s pupils and %s teachers. It "
            "is now %s%% of all public basic-education enrollment."
            % (format(F["se1"], ","), F["y1"], F["sy0"], format(F["se0"], ","),
               format(F["st0"], ","), F["sshare"]),
        "Which senior high school track is most popular in the Philippines?":
            "Technical-Vocational-Livelihood, at %s%% of senior-high enrollment -- "
            "%s pupils. STEM is fourth of eight strands at %s%%, or %s pupils, "
            "making TVL %s times larger. The four academic strands together account "
            "for %s%%. The smallest is %s with %s pupils nationwide."
            % (F["ttoppct"], format(F["ttopn"], ","), F["stempct"],
               format(F["stemn"], ","), F["tvlstem"], F["acadpct"], F["tsmall"],
               format(F["tsmalln"], ",")),
        "Does this data show whether Filipino students are learning?":
            "No. The DepEd file counts who is enrolled and who teaches them. There "
            "are no test scores, no completion rates and no cohort tracking in it, "
            "and it covers public schools only -- roughly a tenth of Philippine "
            "basic education is private and absent entirely. The nearest measures "
            "here are national UIS estimates: primary completion of %s%% in %d, "
            "%s primary-age children out of school, and net secondary enrolment of "
            "%s%% in %d."
            % (F["pc"], F["pcy"], format(int(F["oos"]), ","), F["net"], F["nety"]),
        "How much does the Philippines spend on education compared with its neighbours?":
            "%s%% of GDP in %d, the highest of the %d ASEAN countries whose series "
            "is comparable. Indonesia is shown but excluded from that ranking: its "
            "reported figure falls from 3.58%% of GDP in 2015 to about 1%% after, "
            "which reflects a change in what it reports to UIS rather than in what "
            "it spends, since it devolves most education spending to its regions."
            % (F["spph"], F["spyear"], F["spn"]),
    })
    p.save(len(S), len(charts))


if __name__ == "__main__":
    main()
