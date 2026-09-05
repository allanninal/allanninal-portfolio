#!/usr/bin/env python3
"""DepEd public-school enrollment and teacher counts, 2010-11 to 2020-21.

The published page carried fifty charts and no figures that traced to anything.
The dataset it cited downloads from Kaggle without authentication and is small
and clean: 187 rows, one per region per academic year, with enrollment split by
grade level and by senior-high track, and teacher counts split into elementary,
junior high and senior high.

Two things in it are worth a page.

The first is the K-12 rollout. Every G11 and G12 column is zero until SY
2016-2017, when senior high school appears with 731,981 students, and reaches
1,987,180 by 2020-21. That is a new tier of schooling built in four years, and
the file records the staffing that went with it: 36,788 senior-high teachers in
the first year, 74,056 by the last.

The second is quieter. National enrollment rose 14.6% over the eleven years while
teacher numbers rose 72.7%, so the pupil-teacher ratio fell from 38.9 to 25.8.
Whatever else was true of Philippine public schooling in that decade, class sizes
came down a long way.

And one finding that contradicts the usual assumption: the largest senior-high
track is not STEM. It is Technical-Vocational-Livelihood, at 37.84% against
STEM's 9.02%.

What this cannot say is anything about learning. There are no scores here, no
completion rates and no private schools -- roughly a tenth of Philippine basic
education is private and is simply absent. The coverage file records all three.

Writes:
  ph_education_national.csv    one row per academic year
  ph_education_by_region.csv   one row per region per year
  ph_education_levels.csv      enrollment and teachers by level, with ratios
  ph_education_tracks.csv      senior-high track choice, by year
  ph_education_shs.csv         the K-12 rollout year by year
  ph_education_coverage.csv    what the file is and is not
"""
import csv
import io
import os
import re
import sys
import zipfile
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_lib"))
import worldbank as wb  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..")
KAGGLE = ("https://www.kaggle.com/api/v1/datasets/download/"
          "johnjoemmelrodelas/philippine-public-education-data")
SRC = ("Kaggle johnjoemmelrodelas/philippine-public-education-data "
       "(DepEd enrollment and teacher counts, public schools)")
SRC_WB = "UNESCO Institute for Statistics, via World Bank WDI"

# The counterweight. DepEd counts the children who are enrolled; these count the
# ones who are not, which is the question enrollment data cannot answer about
# itself.
WB_IND = [("SE.PRM.CMPT.ZS", "primary_completion_pct"),
          ("SE.PRM.ENRR", "primary_gross_enrolment_pct"),
          ("SE.SEC.ENRR", "secondary_gross_enrolment_pct"),
          ("SE.SEC.NENR", "secondary_net_enrolment_pct"),
          ("SE.PRM.UNER", "primary_age_out_of_school"),
          ("SE.XPD.TOTL.GD.ZS", "education_spend_pct_gdp"),
          ("SE.ADT.LITR.ZS", "adult_literacy_pct"),
          ("SE.TER.ENRR", "tertiary_gross_enrolment_pct")]

ASEAN = {"PHL": "Philippines", "IDN": "Indonesia", "VNM": "Vietnam",
         "THA": "Thailand", "MYS": "Malaysia", "SGP": "Singapore"}

# Grade columns, grouped into the three levels the teacher counts use. Written
# out rather than pattern-matched so a ratio can never silently pair a level's
# enrollment with another level's staff.
ELEM = ["Enrollees_K"] + ["Enrollees_G%d" % g for g in range(1, 7)]
JHS = ["Enrollees_G%d" % g for g in range(7, 11)]
# The file spells one senior-high column "Enrollees_G122_SPORTs" -- a typo for
# G12 -- so senior-high columns are matched by prefix and the typo is recorded
# rather than corrected silently.
SHS_RE = re.compile(r"^Enrollees_G1(?:1|2|22)_(.+)$")

TRACK_NAME = {
    "ABM": "Accountancy, Business and Management",
    "HUMSS": "Humanities and Social Sciences",
    "STEM": "Science, Technology, Engineering and Mathematics",
    "GAS": "General Academic Strand",
    "MARITIME": "Maritime",
    "TVL": "Technical-Vocational-Livelihood",
    "SPORTs": "Sports",
    "A&D": "Arts and Design",
}


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  wrote %-32s %5d rows" % (name, len(rows)))


def num(v):
    """A count from a possibly blank cell.

    Named num rather than i: as "i" it was shadowed by a "for i in ASEAN" loop
    added later in the same module, and the enrol() closure above then failed with
    a free-variable error rather than anything that pointed at the cause.
    """
    return int(v) if v and str(v).strip() else 0


def load():
    req = urllib.request.Request(KAGGLE, headers={"User-Agent": "Mozilla/5.0"})
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=180).read()))
    names = [n for n in z.namelist() if n.lower().endswith(".csv")]
    if len(names) != 1:
        raise SystemExit("archive layout changed: %s" % z.namelist())
    return list(csv.DictReader(io.StringIO(z.read(names[0]).decode("utf-8-sig"))))


def track_of(col):
    m = SHS_RE.match(col)
    return m.group(1) if m else None


def main():
    raw = load()
    if not raw:
        raise SystemExit("no rows in the archive")
    cols = list(raw[0])
    shs_cols = [c for c in cols if SHS_RE.match(c)]
    tracks = sorted({track_of(c) for c in shs_cols})
    print("  %d row(s), %d column(s), %d senior-high column(s), %d track(s)"
          % (len(raw), len(cols), len(shs_cols), len(tracks)))

    years = sorted({r["Academic_Year"] for r in raw},
                   key=lambda s: int(re.search(r"(\d{4})", s).group(1)))
    regions = sorted({r["Region"] for r in raw})

    def enrol(r, group):
        return sum(num(r.get(c)) for c in group)

    def shs(r, track=None):
        return sum(num(r.get(c)) for c in shs_cols
                   if track is None or track_of(c) == track)

    # ---- per region per year ------------------------------------------------
    by_region = []
    for r in raw:
        e_el, e_jh, e_sh = enrol(r, ELEM), enrol(r, JHS), shs(r)
        t_el, t_jh, t_sh = (num(r["Teachers_Elementary"]), num(r["Teachers_JHS"]),
                            num(r["Teachers_SHS"]))
        tot_e, tot_t = e_el + e_jh + e_sh, t_el + t_jh + t_sh
        by_region.append([
            r["Academic_Year"], int(r["AY_Start"]), r["Region"],
            tot_e, e_el, e_jh, e_sh, tot_t, t_el, t_jh, t_sh,
            round(tot_e / tot_t, 2) if tot_t else "", SRC])
    write("ph_education_by_region.csv",
          ["academic_year", "ay_start", "region", "enrollees", "enrollees_elem",
           "enrollees_jhs", "enrollees_shs", "teachers", "teachers_elem",
           "teachers_jhs", "teachers_shs", "pupils_per_teacher", "source"],
          by_region)

    # ---- national ------------------------------------------------------------
    nat = []
    for y in years:
        rs = [x for x in by_region if x[0] == y]
        tot_e = sum(x[3] for x in rs)
        tot_t = sum(x[7] for x in rs)
        nat.append([y, rs[0][1], len(rs), tot_e, sum(x[4] for x in rs),
                    sum(x[5] for x in rs), sum(x[6] for x in rs),
                    tot_t, sum(x[8] for x in rs), sum(x[9] for x in rs),
                    sum(x[10] for x in rs),
                    round(tot_e / tot_t, 2) if tot_t else "", SRC])
    write("ph_education_national.csv",
          ["academic_year", "ay_start", "regions", "enrollees", "enrollees_elem",
           "enrollees_jhs", "enrollees_shs", "teachers", "teachers_elem",
           "teachers_jhs", "teachers_shs", "pupils_per_teacher", "source"], nat)

    # ---- by level, with each level's own ratio ------------------------------
    # A blended national ratio hides that the three tiers are staffed very
    # differently, so each level is paired only with its own teachers.
    lvl = []
    for row in nat:
        y = row[0]
        for name, e, t in (("elementary", row[4], row[8]),
                           ("junior high", row[5], row[9]),
                           ("senior high", row[6], row[10])):
            lvl.append([y, row[1], name, e, t,
                        round(e / t, 2) if t else "",
                        "not yet established" if e == 0 and t == 0 else "", SRC])
    write("ph_education_levels.csv",
          ["academic_year", "ay_start", "level", "enrollees", "teachers",
           "pupils_per_teacher", "note", "source"], lvl)

    # ---- senior-high tracks --------------------------------------------------
    trk = []
    for y in years:
        rs = [x for x in raw if x["Academic_Year"] == y]
        total = sum(shs(r) for r in rs)
        if not total:
            continue
        for t in tracks:
            n = sum(shs(r, t) for r in rs)
            trk.append([y, int(rs[0]["AY_Start"]), t, TRACK_NAME.get(t, t), n,
                        round(100.0 * n / total, 2), total, SRC])
    write("ph_education_tracks.csv",
          ["academic_year", "ay_start", "track", "track_name", "enrollees",
           "pct_of_shs", "shs_total", "source"], trk)

    # ---- the rollout ---------------------------------------------------------
    roll = []
    prev = None
    for row in nat:
        e, t = row[6], row[10]
        roll.append([row[0], row[1], e, t,
                     round(e / t, 2) if t else "",
                     "" if prev in (None, 0) else round(100.0 * (e / prev - 1), 2),
                     "before senior high school existed" if e == 0 else "", SRC])
        prev = e
    write("ph_education_shs.csv",
          ["academic_year", "ay_start", "enrollees", "teachers",
           "pupils_per_teacher", "growth_pct", "note", "source"], roll)

    first, last = nat[0], nat[-1]
    ratios = [x for x in lvl if x[5] != ""]
    cov = [
        ["academic years", len(years), "%s to %s" % (years[0], years[-1]), SRC],
        ["regions", len(regions), "the Philippines has 17", SRC],
        ["rows", len(raw), "one per region per year", SRC],
        ["first year senior high appears",
         next(r[0] for r in roll if r[2] > 0), "", SRC],
        ["column named G122 rather than G12", 1,
         "Enrollees_G122_SPORTs is a typo in the source; senior-high columns are "
         "matched by prefix so it is counted rather than dropped", SRC],
        ["private schools", 0,
         "DepEd counts public schools; roughly a tenth of Philippine basic "
         "education is private and is absent from every figure here", SRC],
        ["learning outcomes", 0,
         "no test scores, no completion rates. Enrollment counts who is on a roll, "
         "not who is learning", SRC],
        ["dropouts or repetition", 0,
         "the file is a snapshot per year, so no pupil is followed between years "
         "and no cohort survival can be computed", SRC],
        ["school or class counts", 0,
         "pupils per teacher is not class size: a teacher may take several "
         "classes and a class several teachers", SRC],
        ["enrollment change over the period",
         round(100.0 * (last[3] / first[3] - 1), 2), "%", SRC],
        ["teacher change over the period",
         round(100.0 * (last[7] / first[7] - 1), 2), "%", SRC],
    ]
    # ---- national outcomes, which the DepEd file cannot supply ------------
    got = {n: wb.series("PHL", c) for c, n in WB_IND}
    yrs = sorted(set().union(*(set(v) for v in got.values())))
    write("ph_education_outcomes.csv",
          ["year"] + [n for _, n in WB_IND] + ["source"],
          [[y] + [round(got[n][y], 2) if y in got[n] else "" for _, n in WB_IND]
           + [SRC_WB] for y in yrs])

    # Education spending as a share of GDP, across ASEAN. Two traps here.
    #
    # First, a chart that quietly drops a country reads as a chart that never had
    # it, so every country gets a row.
    #
    # Second, and worse: Indonesia's series falls from 3.58% in 2015 to 1.21% in
    # 2016 and stays near 1% after. Indonesia devolves most education spending to
    # its regions and constitutionally earmarks a fifth of the budget for it, so
    # ~1% of GDP is not a real figure -- it is a change in what gets reported to
    # UIS. Publishing it beside the others would state something false.
    #
    # So a break is detected rather than hardcoded: any country whose series
    # halves from one year to the next and stays down is marked not comparable,
    # with the break year recorded. The page keeps the row and excludes it from
    # the ranking, naming the exclusion.
    spend = {i: wb.series(i, "SE.XPD.TOTL.GD.ZS") for i in ASEAN}

    def break_year(series):
        ys = sorted(series)
        for a, b in zip(ys, ys[1:]):
            if b - a > 3 or series[a] <= 0:
                continue
            if series[b] < 0.5 * series[a]:
                after = [series[y] for y in ys if y >= b]
                if sum(after) / len(after) < 0.6 * series[a]:
                    return b
        return None

    breaks = {i: break_year(spend[i]) for i in ASEAN}
    common = [y for y in range(1990, 2026) if all(y in spend[i] for i in ASEAN)]
    if not common:
        raise SystemExit("no year carries education spending for all six countries")
    y = max(common)
    rows_sp = []
    for i in ASEAN:
        bk = breaks[i]
        broken = bk is not None and y >= bk
        rows_sp.append([
            ASEAN[i], y, round(spend[i][y], 2),
            "no" if broken else "yes",
            ("series drops from %.2f%% in %d to %.2f%% in %d and stays down -- a "
             "change in what is reported, not in what is spent"
             % (spend[i][bk - 1], bk - 1, spend[i][bk], bk)) if broken else "",
            SRC_WB])
    write("ph_education_spend_asean.csv",
          ["country", "year", "education_spend_pct_gdp", "comparable", "note",
           "source"], sorted(rows_sp, key=lambda r: r[2]))
    print("  ASEAN spending comparison year: %d" % y)
    for r in rows_sp:
        if r[3] == "no":
            print("    %s marked not comparable: %s" % (r[0], r[4]))

    def latest(name):
        s = got[name]
        y = max(s)
        return y, s[y]

    for name in ("primary_completion_pct", "secondary_net_enrolment_pct",
                 "primary_age_out_of_school", "education_spend_pct_gdp"):
        y, v = latest(name)
        cov.append([name.replace("_", " "), round(v, 2),
                    "national, %d, and outside the DepEd file" % y, SRC_WB])

    write("ph_education_coverage.csv",
          ["property", "value", "note", "source"], cov)
    print("  enrollment %s -> %s, teachers %s -> %s, ratio %s -> %s"
          % (format(first[3], ","), format(last[3], ","),
             format(first[7], ","), format(last[7], ","),
             first[11], last[11]))


if __name__ == "__main__":
    main()
