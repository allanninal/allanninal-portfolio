#!/usr/bin/env python3
"""Western Pacific storm tracks from IBTrACS, restricted to Philippine waters.

The published page reported 23 major typhoons, 43.9 million people affected, 4.2
million houses damaged and 65,870 barangays hit, sourced to NDRRMC/DROMIC. Those
are impact figures from disaster response reports, not track data, and none of
them traced to anything in this repo.

IBTrACS is the authoritative track archive: every agency's best-track estimates
merged into one file, 248,308 observations of 4,245 western Pacific storms from
1884. It carries position, intensity and distance to land -- not damage. So this
page is about where storms go and how strong they get, and it says plainly that
it has nothing to say about what they cost.

The single most important thing in the file is that it should not be read from
1884. Intensity is missing for 100% of observations before 1945 and 44.1% of
1945-69, because nobody was measuring. A chart of storms per year from 1884 does
not show storms becoming more frequent; it shows aircraft reconnaissance starting
in the 1940s and satellites in the 1960s. Every rate and trend here is therefore
restricted to 1980 onward, the threshold is a stated constant, and the earlier
data is written out with its own gaps recorded so the reason is visible.

"Philippine waters" here is the box 5-25N, 115-135E. The official PAR is a
polygon and this is its bounding rectangle, so the counts are a slight
over-estimate of PAR entries; the coverage file says so rather than implying
precision the geometry does not have.

Writes:
  ph_typhoon_storms.csv      one row per storm reaching the box, with its peak
  ph_typhoon_seasons.csv     storms per season, with a data-quality flag
  ph_typhoon_monthly.csv     the season within the year
  ph_typhoon_intensity.csv   peak Saffir-Simpson category distribution
  ph_typhoon_strongest.csv   the most intense storms on record here
  ph_typhoon_landfall.csv    storms recording a Philippine landfall
  ph_typhoon_coverage.csv    what the archive does and does not carry
"""
import csv
import io
import os
import sys
import urllib.request

try:
    import duckdb
except ImportError:
    sys.exit("fetch_typhoon.py needs duckdb:  make venv")

OUT = os.path.join(os.path.dirname(__file__), "..")
CACHE = os.path.join(os.path.dirname(__file__), ".cache")
URL = ("https://www.ncei.noaa.gov/data/"
       "international-best-track-archive-for-climate-stewardship-ibtracs/"
       "v04r01/access/csv/ibtracs.WP.list.v04r01.csv")
SRC = "NOAA NCEI IBTrACS v04r01, western Pacific basin"

# The satellite era. Before this the archive undercounts storms and barely
# records intensity, so no rate, trend or ranking on the page starts earlier.
ERA = 1980
# Bounding box of the Philippine Area of Responsibility. The official PAR is a
# polygon; this rectangle contains it.
S, N, W, E = 5.0, 25.0, 115.0, 135.0
# The last usable season is derived from the archive rather than written here.
# Filtering TRACK_TYPE to 'main' already excludes the current season, whose tracks
# are still PROVISIONAL, so the maximum season present is by construction a
# finalised one. Hardcoding a year would silently start excluding real data as the
# archive advances, or include a partial season as it is being written.
LAST_FULL = None      # set in main() from the data

SSHS = {-5: "disturbance", -4: "post-tropical", -3: "tropical depression",
        -2: "subtropical", -1: "tropical depression", 0: "tropical storm",
        1: "category 1", 2: "category 2", 3: "category 3", 4: "category 4",
        5: "category 5"}


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("  wrote %-30s %5d rows" % (name, len(rows)))


def download():
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "ibtracs_wp.csv")
    if not os.path.exists(path) or os.path.getsize(path) < 10_000_000:
        # 109 MB. Cached because it is the same file every run and the page is
        # rebuilt far more often than NOAA revises the archive.
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=900) as r, open(path, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
    if os.path.getsize(path) < 10_000_000:
        raise SystemExit("IBTrACS download is too small to be the real file")
    return path


def main():
    global LAST_FULL
    path = download()
    con = duckdb.connect()
    # header=true names the columns from row 1; row 2 is a units row ("Year",
    # "kts", "km") and is dropped by requiring SEASON to parse as an integer.
    # TRACK_TYPE is filtered to 'main' so spur and provisional duplicates of the
    # same storm are not counted twice.
    con.execute("""
        create view obs as select
          SID, try_cast(SEASON as int) season, trim(NAME) storm_name,
          try_cast(ISO_TIME as timestamp) ts,
          try_cast(LAT as double) lat, try_cast(LON as double) lon,
          try_cast(USA_WIND as double) wind, try_cast(USA_SSHS as int) sshs,
          try_cast(DIST2LAND as double) d2l, try_cast(LANDFALL as double) landfall
        from read_csv('%s', header=true, all_varchar=true)
        where try_cast(SEASON as int) is not null and TRACK_TYPE = 'main'
    """ % path.replace("'", "''"))
    con.execute("""
        create view par as select * from obs
        where lat between %f and %f and lon between %f and %f
    """ % (S, N, W, E))

    def rows(sql):
        return con.execute(sql).fetchall()

    n_obs, n_storm, y0, y1 = rows(
        "select count(*), count(distinct SID), min(season), max(season) "
        "from obs")[0]
    LAST_FULL = y1
    print("  %d observation(s), %d storm(s), %d-%d (last finalised season: %d)"
          % (n_obs, n_storm, y0, y1, LAST_FULL))

    # ---- one row per storm that entered the box ----------------------------
    storms = rows("""
        select p.SID, p.season, max(nullif(p.storm_name, 'UNNAMED')) nm,
               min(p.ts) first_in_box, max(p.ts) last_in_box,
               max(p.wind) peak_wind_kt, max(p.sshs) peak_sshs,
               min(p.d2l) closest_land_km,
               count(*) obs_in_box,
               count(*) filter (where p.landfall = 0) landfall_obs
        from par p group by 1, 2 order by 2, 1""")
    write("ph_typhoon_storms.csv",
          ["sid", "season", "name", "first_in_box", "last_in_box",
           "peak_wind_kt", "peak_sshs", "peak_category", "closest_land_km",
           "obs_in_box", "landfall_obs", "era", "source"],
          [[a, b, c or "UNNAMED", str(d), str(e), f, g,
            SSHS.get(g, "") if g is not None else "", h, i, j,
            "satellite" if b >= ERA else "pre-satellite", SRC]
           for a, b, c, d, e, f, g, h, i, j in storms])

    # ---- per season, with the quality flag that governs the page ----------
    seasons = rows("""
        select o.season,
               count(distinct o.SID) storms_in_basin,
               (select count(distinct p.SID) from par p where p.season = o.season)
                 storms_in_box,
               round(100.0 * count(*) filter (where o.wind is null) / count(*), 1)
                 pct_obs_without_wind
        from obs o group by 1 order by 1""")
    write("ph_typhoon_seasons.csv",
          ["season", "storms_in_basin", "storms_in_box",
           "pct_obs_without_wind", "era", "complete", "source"],
          [[a, b, c, d,
            "satellite" if a >= ERA else "pre-satellite",
            "yes" if a <= LAST_FULL else "no", SRC]
           for a, b, c, d in seasons])

    # ---- the season within the year ----------------------------------------
    write("ph_typhoon_monthly.csv",
          ["month", "storms", "pct_of_storms", "source"],
          [[m, n, round(100.0 * n / tot, 2), SRC] for m, n, tot in rows("""
            with s as (select month(ts) m, count(distinct SID) n from par
                       where season between %d and %d group by 1)
            select m, n, (select sum(n) from s) from s order by m"""
            % (ERA, LAST_FULL))])

    # ---- peak intensity, one category per storm ----------------------------
    # Each storm counted once at its own maximum. Counting every observation
    # would weight a slow storm more heavily than a fast one.
    write("ph_typhoon_intensity.csv",
          ["peak_sshs", "peak_category", "storms", "pct_of_storms", "source"],
          [[a, SSHS.get(a, "unclassified"), b, round(100.0 * b / t, 2), SRC]
           for a, b, t in rows("""
            with s as (
              select max(sshs) mx, SID from par
              where season between %d and %d group by SID),
                 c as (select mx, count(*) n from s where mx is not null group by 1)
            select mx, n, (select sum(n) from c) from c order by mx"""
            % (ERA, LAST_FULL))])

    # ---- the strongest -----------------------------------------------------
    write("ph_typhoon_strongest.csv",
          ["rank", "name", "season", "peak_wind_kt", "peak_wind_kmh",
           "peak_sshs", "closest_land_km", "source"],
          [[k, (nm or "UNNAMED"), se, w, round(w * 1.852), sh, round(d2l or 0), SRC]
           for k, (nm, se, w, sh, d2l) in enumerate(rows("""
            select max(nullif(storm_name,'UNNAMED')), season, max(wind), max(sshs),
                   min(d2l)
            from par where season between %d and %d group by SID, season
            having max(wind) is not null
            order by max(wind) desc, season limit 25"""
            % (ERA, LAST_FULL)), 1)])

    # ---- landfalls ----------------------------------------------------------
    write("ph_typhoon_landfall.csv",
          ["season", "storms_in_box", "storms_with_landfall_obs",
           "pct_with_landfall", "source"],
          [[a, b, c, round(100.0 * c / b, 1) if b else "", SRC]
           for a, b, c in rows("""
            select season, count(distinct SID),
                   count(distinct SID) filter (where landfall = 0)
            from par where season between %d and %d group by 1 order by 1"""
            % (ERA, LAST_FULL))])

    # ---- coverage ------------------------------------------------------------
    pre = rows("""select count(distinct SID),
                  round(100.0*count(*) filter (where wind is null)/count(*),1)
                  from obs where season < 1945""")[0]
    mid = rows("""select count(distinct SID),
                  round(100.0*count(*) filter (where wind is null)/count(*),1)
                  from obs where season between 1945 and 1969""")[0]
    sat = rows("""select count(distinct SID),
                  round(100.0*count(*) filter (where wind is null)/count(*),1)
                  from obs where season >= %d""" % ERA)[0]
    box = rows("select count(distinct SID) from par")[0][0]
    box_era = rows("select count(distinct SID) from par where season between %d and %d"
                   % (ERA, LAST_FULL))[0][0]
    cov = [
        ["observations in the archive", n_obs, "western Pacific basin", SRC],
        ["storms in the archive", n_storm, "%d to %d" % (y0, y1), SRC],
        ["storms entering the box", box, "all years", SRC],
        ["storms entering the box, %d-%d" % (ERA, LAST_FULL), box_era,
         "everything on this page that is a rate or a trend uses only these", SRC],
        ["storms before 1945", pre[0], "", SRC],
        ["observations before 1945 with no wind speed", pre[1],
         "%, so no intensity of any kind can be computed for them", SRC],
        ["observations 1945-1969 with no wind speed", mid[1],
         "%, aircraft reconnaissance era", SRC],
        ["observations since %d with no wind speed" % ERA, sat[1],
         "%, satellite era", SRC],
        ["first season used for rates and trends", ERA,
         "chosen because earlier storm counts measure observing capability rather "
         "than storm activity", SRC],
        ["last finalised season", LAST_FULL,
         "derived from the archive, not fixed in the script: only TRACK_TYPE=main "
         "tracks are read, and the current season's are still PROVISIONAL, so the "
         "maximum season present is finalised by construction", SRC],
        ["deaths, damage or people affected", 0,
         "IBTrACS is a track archive. It carries no impact data at all, and this "
         "page makes no claim about what any storm cost", SRC],
        ["Philippine landfall points", 0,
         "the landfall column gives distance to the nearest land, not which "
         "country. Storms recording a landfall inside the box may have made it on "
         "Taiwan or Vietnam", SRC],
        ["official PAR polygon", 0,
         "the box %g-%gN, %g-%gE is the bounding rectangle of the Philippine Area "
         "of Responsibility, so counts here slightly exceed true PAR entries"
         % (S, N, W, E), SRC],
        ["PAGASA local storm names", 0,
         "IBTrACS carries international names. Haiyan is Yolanda locally, and this "
         "page uses the international name throughout", SRC],
    ]
    write("ph_typhoon_coverage.csv",
          ["property", "value", "note", "source"], cov)


if __name__ == "__main__":
    main()
